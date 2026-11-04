-- Sutra ERP reference schema for the product (PostgreSQL 16 + TimescaleDB + pgvector).
-- The proof of concept keeps the same event model in SQLite; this is the production layout.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 1. Tenancy, entities, compliance -------------------------------------------------------------
CREATE TABLE tenant        (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), name text NOT NULL,
                            home_region text NOT NULL CHECK (home_region IN ('in','eu','us','me','apac')),
                            created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE legal_entity  (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL REFERENCES tenant,
                            name text NOT NULL, country char(2) NOT NULL, currency char(3) NOT NULL,
                            tax_id text, pack_version text NOT NULL);
CREATE TABLE country_pack  (country char(2), version text, body jsonb NOT NULL, approved_by text NOT NULL,
                            approved_at timestamptz NOT NULL, PRIMARY KEY (country, version));

-- 2. Identity and access (RBAC + attributes for ABAC) -------------------------------------------
CREATE TABLE principal     (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL REFERENCES tenant,
                            kind text NOT NULL CHECK (kind IN ('human','agent','service','device')),
                            name text NOT NULL, attrs jsonb NOT NULL DEFAULT '{}', disabled boolean NOT NULL DEFAULT false);
CREATE TABLE role_grant    (principal_id uuid REFERENCES principal, role text NOT NULL, entity_id uuid REFERENCES legal_entity,
                            valid_to timestamptz, PRIMARY KEY (principal_id, role, entity_id));

-- 3. The event store: source of truth, append-only, hash-chained per tenant --------------------
CREATE TABLE event (seq bigserial, tenant_id uuid NOT NULL, stream text NOT NULL, type text NOT NULL,
                    actor_id uuid NOT NULL, actor_kind text NOT NULL, at timestamptz NOT NULL DEFAULT now(),
                    payload jsonb NOT NULL, prev_hash bytea NOT NULL, hash bytea NOT NULL,
                    PRIMARY KEY (tenant_id, seq)) PARTITION BY HASH (tenant_id);
CREATE TABLE event_p0 PARTITION OF event FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE event_p1 PARTITION OF event FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE event_p2 PARTITION OF event FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE event_p3 PARTITION OF event FOR VALUES WITH (MODULUS 4, REMAINDER 3);
CREATE INDEX ON event (tenant_id, stream, seq);
CREATE INDEX ON event (tenant_id, type, at);
REVOKE UPDATE, DELETE, TRUNCATE ON event FROM PUBLIC;          -- the app role can only INSERT and SELECT
CREATE TABLE chain_anchor  (tenant_id uuid, seq bigint, hash bytea, anchored_at timestamptz DEFAULT now(),
                            witness text NOT NULL,             -- e.g. RFC 3161 timestamp authority or WORM store
                            PRIMARY KEY (tenant_id, seq));

-- 4. Finance (projections rebuilt from events) --------------------------------------------------
CREATE TABLE account       (entity_id uuid REFERENCES legal_entity, code text, name text NOT NULL,
                            kind text NOT NULL CHECK (kind IN ('asset','liability','equity','income','expense')),
                            PRIMARY KEY (entity_id, code));
CREATE TABLE journal       (id uuid PRIMARY KEY, entity_id uuid NOT NULL, event_seq bigint NOT NULL, posted_at timestamptz NOT NULL,
                            source text NOT NULL, memo text, period char(7) NOT NULL, created_by uuid NOT NULL);
CREATE TABLE journal_line  (journal_id uuid REFERENCES journal, line int, account_code text NOT NULL,
                            dr numeric(18,2) NOT NULL DEFAULT 0, cr numeric(18,2) NOT NULL DEFAULT 0,
                            tax_code text, cost_centre text, PRIMARY KEY (journal_id, line),
                            CHECK (dr >= 0 AND cr >= 0 AND (dr = 0 OR cr = 0)));
CREATE TABLE period_lock   (entity_id uuid, period char(7), locked_by uuid NOT NULL, locked_at timestamptz NOT NULL,
                            PRIMARY KEY (entity_id, period));

-- 5. Supply chain and assets --------------------------------------------------------------------
CREATE TABLE item          (id uuid PRIMARY KEY, tenant_id uuid NOT NULL, sku text NOT NULL, item_group text NOT NULL,
                            uom text NOT NULL, attrs jsonb NOT NULL DEFAULT '{}', UNIQUE (tenant_id, sku));
CREATE TABLE stock_move    (id uuid PRIMARY KEY, item_id uuid REFERENCES item, site text, qty numeric(18,3) NOT NULL,
                            event_seq bigint NOT NULL, at timestamptz NOT NULL);
CREATE TABLE asset         (id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site text NOT NULL, kind text NOT NULL,
                            criticality smallint NOT NULL CHECK (criticality BETWEEN 1 AND 5), gateway_id text);
CREATE TABLE telemetry     (asset_id uuid NOT NULL, metric text NOT NULL, at timestamptz NOT NULL, value double precision NOT NULL,
                            quality smallint NOT NULL DEFAULT 192);   -- OPC UA style quality code
SELECT create_hypertable('telemetry', 'at', chunk_time_interval => interval '1 day');

-- 6. Intelligence: alerts, proposals, people in the loop --------------------------------------
CREATE TABLE alert         (id uuid PRIMARY KEY, asset_id uuid, kind text CHECK (kind IN ('threshold','predictive','anomaly','business')),
                            severity text NOT NULL, why text NOT NULL, raised_at timestamptz NOT NULL, cleared_at timestamptz);
CREATE TABLE proposal      (id uuid PRIMARY KEY, alert_id uuid REFERENCES alert, playbook text NOT NULL, risk text NOT NULL,
                            confidence numeric(3,2) NOT NULL, route text CHECK (route IN ('auto','approve','escalate')),
                            model_version text, evidence jsonb NOT NULL, status text NOT NULL DEFAULT 'open');
CREATE TABLE hitl_decision (proposal_id uuid REFERENCES proposal, decided_by uuid NOT NULL, decision text NOT NULL
                            CHECK (decision IN ('approved','edited','rejected')), reason text, decided_at timestamptz NOT NULL);

-- 7. Agents and guardrails ----------------------------------------------------------------------
CREATE TABLE agent_policy  (agent text, version text, allow text[] NOT NULL, needs_approval text[] NOT NULL DEFAULT '{}',
                            max_per_min int NOT NULL, max_value numeric(18,2) NOT NULL, PRIMARY KEY (agent, version));
CREATE TABLE guard_decision(id bigserial PRIMARY KEY, tenant_id uuid NOT NULL, agent text NOT NULL, action text NOT NULL,
                            value numeric(18,2), allowed boolean NOT NULL, why text NOT NULL, approved_by uuid, at timestamptz NOT NULL);
CREATE TABLE agent_state   (agent text PRIMARY KEY, status text NOT NULL CHECK (status IN ('active','suspended','retired')),
                            reason text, changed_at timestamptz NOT NULL);

-- 8. Documents (P10 pattern: regional stores, content-addressed blobs, retention and legal hold) ---
CREATE TABLE document      (id uuid PRIMARY KEY, tenant_id uuid NOT NULL, region text NOT NULL, classification text NOT NULL
                            CHECK (classification IN ('public','internal','confidential','restricted')), doc_type text NOT NULL,
                            entity_id uuid, linked_stream text, retention_until date, legal_hold boolean NOT NULL DEFAULT false);
CREATE TABLE doc_version   (document_id uuid REFERENCES document, version int, sha256 bytea NOT NULL, size bigint NOT NULL,
                            status text NOT NULL, created_by uuid NOT NULL, created_at timestamptz NOT NULL,
                            PRIMARY KEY (document_id, version));
CREATE TABLE kb_chunk      (id bigserial PRIMARY KEY, tenant_id uuid NOT NULL, document_id uuid, access_group text NOT NULL,
                            lang text, text text NOT NULL, embedding vector(1024), tsv tsvector);
CREATE INDEX ON kb_chunk USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON kb_chunk USING gin (tsv);

-- 9. Audit --------------------------------------------------------------------------------------
CREATE TABLE audit_engagement (id uuid PRIMARY KEY, entity_id uuid NOT NULL, kind text CHECK (kind IN ('statutory','concurrent','internal')),
                               firm text, period_from date, period_to date, read_role text NOT NULL);
CREATE TABLE control       (id text PRIMARY KEY, name text NOT NULL, frequency text NOT NULL, rule jsonb NOT NULL, owner text NOT NULL);
CREATE TABLE finding       (id uuid PRIMARY KEY, engagement_id uuid REFERENCES audit_engagement, control_id text REFERENCES control,
                            event_seq bigint, severity text NOT NULL, status text NOT NULL DEFAULT 'open', response text);

-- 10. Service desk and evaluation ---------------------------------------------------------------
CREATE TABLE ticket        (id text PRIMARY KEY, tenant_id uuid NOT NULL, reporter uuid NOT NULL, text_redacted text NOT NULL,
                            status text NOT NULL, priority text NOT NULL, opened_at timestamptz NOT NULL, sla_due timestamptz);
CREATE TABLE ticket_rca    (ticket_id text REFERENCES ticket, rank int, cause text NOT NULL, confidence numeric(3,2) NOT NULL,
                            evidence jsonb NOT NULL, accepted boolean, PRIMARY KEY (ticket_id, rank));
CREATE TABLE eval_run      (id uuid PRIMARY KEY, suite text NOT NULL, git_sha text NOT NULL, model_versions jsonb NOT NULL,
                            metrics jsonb NOT NULL, passed boolean NOT NULL, ran_at timestamptz NOT NULL);

-- Row-level security: every query sees only its own tenant ---------------------------------------
ALTER TABLE event ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON event USING (tenant_id = current_setting('app.tenant_id')::uuid);
