# Runnable CortexState examples

Run from the repository root after `python -m pip install .`.

| Example | Command | Demonstrates |
| --- | --- | --- |
| [Quick start](quickstart.py) | `python -m examples.quickstart` | Add, budgeted context, correction, and history |
| [Support workflow](support_workflow.py) | `python -m examples.support_workflow` | Safe retries, customer isolation, correction, and forgetting |

Both use a temporary database and synthetic facts, clean up after themselves, and make no model or network calls. They can be run repeatedly without leaving a persistent demo database. To keep data across runs, create `Memory` with a persistent file path in your application.

For a client connected to a running service, follow [Getting started](../docs/GETTING-STARTED.md). For model and framework composition, see [Integration patterns](../docs/INTEGRATION-PATTERNS.md).
