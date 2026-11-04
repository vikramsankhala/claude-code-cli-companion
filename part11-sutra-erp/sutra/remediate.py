"""Remediation with a human in the loop. Confidence and risk decide the route; code, not the model."""
PLAYBOOKS = {
    "reduce_load": {"risk": "low", "action": "set_line_speed", "params": {"pct": 80}, "reversible": True},
    "schedule_maintenance": {"risk": "low", "action": "create_work_order", "params": {"priority": "P2"}, "reversible": True},
    "stop_machine": {"risk": "high", "action": "stop_asset", "params": {}, "reversible": True},
    "reorder_stock": {"risk": "medium", "action": "create_purchase_requisition", "params": {}, "reversible": True},
    "hold_payment": {"risk": "medium", "action": "block_payment", "params": {}, "reversible": True},
}
# minimum confidence for each route, by risk. High-risk actions never run without a person.
ROUTES = {"low": (0.90, 0.60), "medium": (0.97, 0.60), "high": (2.0, 0.50)}


def confidence(alert, evidence: dict) -> float:
    """Blend independent signals into one score in [0, 1]. Weights are configuration, evaluated in CI."""
    base = {"threshold": 0.50, "predictive": 0.40, "anomaly": 0.30}.get(alert["kind"], 0.0)
    s = base + (0.25 if alert["severity"] == "critical" else 0.0)
    s += 0.15 * min(evidence.get("corroborating", 0), 2) / 2      # other sensors agree
    s += 0.10 * evidence.get("past_success_rate", 0.0)            # this playbook worked before here
    return round(min(s, 1.0), 2)


def route(playbook, conf):
    auto, approve = ROUTES[PLAYBOOKS[playbook]["risk"]]
    if conf >= auto:
        return "auto"
    if conf >= approve:
        return "approve"
    return "escalate"


def propose(alert, evidence):
    if alert["severity"] == "critical":
        pb = "stop_machine" if alert["metric"] == "bearing_temp_c" else "reduce_load"
    else:
        pb = "schedule_maintenance"
    conf = confidence(alert, evidence)
    return {"playbook": pb, **PLAYBOOKS[pb], "confidence": conf, "route": route(pb, conf), "alert": alert}
