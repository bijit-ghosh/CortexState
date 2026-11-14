# CortexState documentation

## Learn and run

| Guide | What it answers |
| --- | --- |
| [Getting started](GETTING-STARTED.md) | How do I install, store a fact, query it, and run the service? |
| [Architecture](ARCHITECTURE.md) | Where does data go, how are writes protected, and how does forgetting work? |
| [Example catalog](../examples/README.md) | Which workflows can I run immediately without credentials? |
| [Use cases](USE-CASES.md) | How should I apply CortexState to an actual application? |
| [Integration patterns](INTEGRATION-PATTERNS.md) | Where does memory fit in a model or agent request? |
| [Continual improvement](CONTINUAL-IMPROVEMENT.md) | How do deployment outcomes become reviewed, evaluated lessons across model and agent stacks? |

## Configure and operate

- [Live dashboard](DASHBOARD.md)
- [SDK installation and packaging](SDK.md)
- [API-backed models](MODELS.md)

| Guide | What it answers |
| --- | --- |
| [API contract](API.md) | What fields, limits, operations, and errors are supported? |
| [Customization](CUSTOMIZATION.md) | How do I supply embeddings, extraction, and metadata policies? |
| [Operations](OPERATIONS.md) | How do I configure keys, back up data, and investigate failures? |
| [FAQ](FAQ.md) | Why is retrieval empty, what is portable, and what remains unimplemented? |
| [Security](../SECURITY.md) | Which trust boundaries must the application enforce? |

## Evaluate and contribute

- [Evaluation protocol and measured results](../evals/README.md)
- [Implemented capabilities and roadmap](CAPABILITIES.md)
- [Contribution guide](../CONTRIBUTING.md)
- [Change log](../CHANGELOG.md)
- [Ownership and provenance](../PROVENANCE.md)

Examples use synthetic data. A guide labeled as an integration pattern describes how to compose existing functions; it does not imply a bundled framework adapter or hosted service.
