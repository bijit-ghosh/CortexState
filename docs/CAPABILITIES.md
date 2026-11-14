# Capabilities and roadmap

Mem0's public repository was reviewed as a product reference. This table describes CortexState itself; it is not a benchmark or an assertion that the projects are interchangeable.

| Capability | CortexState 0.3.0 |
| --- | --- |
| Persistent scoped memory | Implemented: SQLite and exact tenant/user/agent/session scope |
| Python integration | Implemented: local library and HTTP client |
| JavaScript integration | Implemented: packable ESM SDK with TypeScript declarations; registry publication pending |
| CLI and self-host HTTP | Implemented: local/private developer service |
| Memory revision history | Implemented with compare-and-update revisions |
| Retry deduplication | Implemented with scoped idempotency receipts |
| Expiry and forgetting | Implemented; purge must be invoked explicitly |
| Search explanations | Implemented: lexical and optional cosine contributions |
| Semantic retrieval | Extension implemented; requires your embedding callable |
| Conversation extraction | Validated review proposals, optional OpenAI adapter, and model-backed answer endpoint; external calls require credentials |
| Metadata filtering | Implemented: top-level equality |
| Context budgeting | Implemented: exact characters; model token budgeting not included |
| Authentication | Implemented: static tenant-scoped backend keys |
| Reproducible eval | Implemented: small public synthetic regression fixture |
| Dashboard | Implemented: live polling, scopes, statistics, CRUD, history, search, model questions, reviewed proposals |
| Browser extension | Not implemented |
| Managed cloud / signup / billing | Not implemented |
| Graph memory / entity linking | Not implemented |
| BM25 | Implemented as opt-in scoring over scoped records |
| Vector indexes / reranking | Not implemented |
| Automatic fact conflict resolution | Not implemented |
| MCP / framework-specific adapters | Not implemented |
| Distributed storage / HA / online migrations | Not implemented |
| SSO / per-user RBAC / key management UI | Not implemented |
| LoCoMo / LongMemEval / model benchmarks | Not executed; no comparative performance claims |

## Next milestones and evidence required

1. **Retrieval quality:** build a consented, labeled dataset with paraphrases, multilingual facts, temporal questions, and stale/contradictory records. Freeze a final holdout before tuning.
2. **Provider integrations:** implement explicit adapters, test failures/timeouts, measure extraction faithfulness and retrieval quality with actual model versions and usage logs.
3. **Scale:** profile realistic per-scope data sizes; add indexed retrieval and queueing only with latency, recall, and isolation evidence.
4. **Operations:** package a deployment-grade server, migrations, backups, quotas, observability, key rotation, and recovery drills.
5. **User experience:** add an authenticated memory console with provenance review and deliberate deletion controls, then framework and MCP adapters.

A release may promote a capability to “implemented” only when code, a runnable example, failure tests, and documentation are present. Production readiness additionally requires workload and security review; passing the included fixture is insufficient.
