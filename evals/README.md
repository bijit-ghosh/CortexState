# Evaluation protocol

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
