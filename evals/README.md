# Evaluation protocol

## Version 0.2 validation

The upgrade passed 33 Python tests and 2 JavaScript transport tests locally. Python wheel installation includes the dashboard assets and provider adapter; an installed npm tarball successfully called the local service. Browser checks exercised connection, live counts, add, revision editing, history, BM25 search, scope isolation, and disconnect with synthetic data. The [0.2 retrieval run](results/v0.2-local.json) passed the same 9 development cases and isolation check.

Provider tests use controlled SDK responses, not paid live calls. Model availability, extraction accuracy, production load, and comparative performance against another product remain unmeasured. The existing initial report below is historical evidence for version 0.1, not a claim that its source hashes match 0.2.

Run `python -m evals.run --out work/eval.json` from the repository root. The destination must not already exist. The runner creates an isolated temporary store, loads eight synthetic facts, executes nine retrieval/no-match cases and one tenant-isolation check, then removes the store.

The JSON report contains actual case outputs, pass counts, local retrieval timings, environment information, zero model-call usage, and SHA-256 hashes of the evaluated Python sources and fixture. [Recorded local run](results/local.json) is a measured development run, not a model benchmark.

## Recorded local validation — November 13, 2026

| Check | Measured result |
| --- | --- |
| Python unit and HTTP integration tests | 24 passed |
| JavaScript client tests | 2 passed |
| Synthetic retrieval/no-match cases | 9 / 9 passed |
| Synthetic tenant-isolation check | Passed |
| Retrieval latency, this tiny local fixture | p50 4.02 ms; maximum 6.84 ms |
| Model calls and model tokens | 0; no model was invoked |

Environment: Windows, Python 3.12.14. The initial socket tests were blocked by the execution sandbox; they were rerun successfully after loopback network access was granted. Docker is not installed in that environment, so the container recipe was not executed locally. CI reports are separate evidence for their own environments.

This fixture uses direct lexical overlap. It is deliberately small and public. A perfect score establishes only that these regressions pass. It does not measure paraphrase recall, large-scale performance, extraction accuracy, token savings, or comparison with Mem0. Embedding unit tests use deterministic synthetic vectors, not a real semantic model.

Before product claims, add consented domain data, negative and adversarial examples, temporal and contradictory facts, and an untouched test split. Fix acceptance criteria before tuning. Record provider/model/version, dataset version, repeated-run variance, failures, tokens, and cost. A lower token count is useful only if outcome quality and isolation remain acceptable.
