# Changelog

## 0.4.0 — cross-stack continual improvement

- Added a provider-, harness-, and skill-neutral deployment outcome ledger with exact-scope evidence and idempotent event capture.
- Added evidence-linked lesson candidates, held-out scorecards, a non-regression/strict-gain promotion gate, reviewer approval, rollback, rejection, and source-experience deletion.
- Added matching authenticated HTTP operations and Python/TypeScript SDK methods, including candidate listing.
- Added a live dashboard panel for recording consented outcomes and reviewing staged candidates and scorecards.
- Added the continual-improvement guide and deployment-learning architecture flow; clarified that evaluation and model-weight training run outside CortexState.
- Added an optional offline actor–writer RL training design for trainable model weights; the repository does not include an RL trainer or weight-update path.
- Aligned Python, JavaScript, Rust, CI, and release artifact versions at 0.4.0. No performance or benchmark results are claimed.

## 0.3.0 — bounded service and optional Rust ranking core

- Release assets: Python wheel and source archive, JavaScript tarball, optional Rust wheels for Linux/Windows/macOS and Python 3.10/3.12, and GitHub source archives.
- Added an optional PyO3 Rust BM25 scorer with a deterministic Python fallback and score-parity coverage.
- Capped HTTP handler concurrency, bounded the connection queue, tightened Content-Length validation, and retained socket timeouts.
- Enabled SQLite WAL, explicit busy timeout and synchronous policy; indexed expiry and erasure lookups.
- Added an original GitHub README banner and native Rust build coverage to Linux/Windows CI and package builds.
- Kept memory API, persistence, provider integration, and dashboard in Python; Rust accelerates only BM25 scoring.
- Versioned as a developer preview; no performance improvement is claimed until measured on a representative workload.

## 0.2.0 — memory console and SDK packages

- Live operator dashboard with exact scopes, counts, memory editing, history, and retention actions.
- One-command disposable demo, BM25 ranking, and scoped statistics.
- Python named client methods and an installable JavaScript SDK with TypeScript declarations.
- Optional OpenAI embeddings, extraction proposals, and context-backed answers with server-side credentials.
- SDK package artifact workflow and expanded regression checks. Public registry publication remains pending account setup.

## Documentation and adoption update

- Expanded CortexState architecture with request sequence, storage, lifecycle, and deployment diagrams.
- Added guided installation, use cases, integration patterns, FAQ, and a documentation index.
- Added a runnable offline support workflow and included it in CI.

## 0.1.0 — initial developer preview

- Original SQLite memory engine with exact scopes, revision history, TTL, deletion, and idempotent writes.
- Explainable lexical retrieval and optional embedding callable; bounded JSON context.
- Reviewed extraction proposal boundary with validated source references.
- Authenticated local HTTP service, Python and JavaScript clients, and CLI.
- Unit/integration tests, synthetic evaluation runner, and Windows/Linux CI configuration.
- Setup, architecture, API, operations, ownership, and capability documentation.
