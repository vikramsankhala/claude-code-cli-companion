# Educator guide: teaching with free hosted models

Book: Chapter 22.6. This guide assumes NVIDIA's API catalogue as the main service, with OpenRouter, Google AI Studio, Mistral and a local Ollama as fallbacks.

## Before the course

| When | Task |
| --- | --- |
| Two weeks before | Read the current terms on build.nvidia.com and the licences of the models you plan to use; adapt `ACCEPTABLE-USE.md` |
| One week before | Pick two or three chat models, one embedding model and the safety model; test each from a fresh student-type account; note alternative IDs |
| One week before | Record a cassette of model answers for every live demo (`ch26-detagent` shows how), so a demo never depends on the network |
| Day before | Run `nvidia/probe_models.py` from a student-type account and pin the working IDs in your lab handout |
| Day before | Start the LiteLLM gateway with at least two providers; run `scripts/test-keys.ps1`; run `python -m pytest -q` in `free-tier` |
| Session 1 | Every student creates their own account and key (`STUDENT-SETUP.md`); collect signed acceptable-use sheets |

**Rate limits in a classroom.** NVIDIA allows about 40 requests a minute per account. That is plenty for one student and far too little for one shared key in a class. Individual accounts are not optional.

## Six sessions

| # | Session | Length | Lab | Students produce |
| --- | --- | --- | --- | --- |
| 1 | Keys and the first call | 90 min | `hello.py`, `stream.py` | A first call showing token counts; a correctly stored key |
| 2 | Choosing a model | 90 min | `compare_models.py`; read two model cards | A comparison table and a justified recommendation |
| 3 | Retrieval | 2 h | `embed.py`, then Project P8 with the gateway | Correct top passage for five test questions |
| 4 | Tools and agents | 2 h | `tools.py`, then Project P7 (`p07-mini-coder`) | A trace of the model calling a tool; one failure explained |
| 5 | Safety and evaluation | 2 h | `guard.py`; a ten-case evaluation set (Chapter 27) | A pass rate and one analysed failure |
| 6 | Capstone | Half day | Team assistant behind the gateway, with fallback | Demo, evaluation results and a one-page design note |

## Discussion prompts

- Why does a 3-billion-parameter model answer faster than a 70-billion one, and when is it good enough?
- The same prompt gives different answers on two runs. Why, and how do the deterministic patterns in Chapter 26 deal with it?
- What would change if this assistant had to go into production? (Licence, data terms, service levels, cost, monitoring.)

## Assessment rubric (per lab)

| Criterion | Excellent | Adequate | Not yet |
| --- | --- | --- | --- |
| Reproducibility | Runs from a clean clone with documented steps | Runs with help | Does not run |
| Evidence | Evaluation set, pass rate, failures analysed | Some test cases | Screenshots only |
| Reasoning | Clear, justified model and design choices | Choices stated | No justification |
| Key handling | Keys only in environment variables; none in submission | — | Key found in submission (automatic fail) |
| Responsible use | Data, licence and limits respected and discussed | Respected | Breached |

## When things go wrong

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| HTTP 401 | Key missing, mistyped, or not loaded in this window | Reopen the terminal after `setx`; check with `scripts/test-keys.ps1` |
| HTTP 404 or "model not found" | Listed but not available to free keys | Run `probe_models.py`; set `NVIDIA_MODEL` to an OK model |
| HTTP 410 "Gone" | The model was retired | Same: probe, then pick a current model |
| Empty answer or "reasoning model" note | A reasoning model used its whole token allowance thinking | Raise `NVIDIA_MAX_TOKENS`, or use it to teach how reasoning models differ |
| HTTP 429 | Rate limit | Wait; the scripts back off; check no one is sharing a key |
| Whole class slow | Service load | Switch the gateway to the fallback provider, or use the recorded cassettes |

## NVIDIA programmes for educators

- **Deep Learning Institute** ([learn.nvidia.com](https://learn.nvidia.com/)): self-paced courses (some free) and instructor-led workshops with certificates.
- **Teaching Kits**: lecture materials, exercises and GPU cloud resources for qualified university educators.
- **University Ambassador Program**: invited educators can become certified DLI instructors and run DLI workshops.
- **Self-hosted NIM**: Developer Program members may run NIM microservices on up to 16 GPUs for research, development and testing. This suits a university GPU lab with no rate limits.
