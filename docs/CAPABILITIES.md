# Capabilities and roadmap

This table describes CortexState's shipped surface and boundaries. It makes no comparative benchmark claim.

| Capability | CortexState 0.4.0 |
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
| Deployment learning ledger | Implemented: consent-asserted, scoped outcome records, evidence-linked lesson candidates, scorecards, approval, rejection, rollback, and deletion |
| Model/harness/skill neutrality | Implemented at the HTTP data/API boundary; no specific provider or agent framework is required, but integrations must call the API |
| Evaluation execution | Caller-operated: CortexState records caller-supplied scorecards and enforces numeric promotion gates; it does not run agents, benchmarks, or evaluators |
| Reinforcement learning for memory policy | Experimental reward primitives: framework-neutral actor reward, delayed writer-improvement reward, safety eligibility, and group-relative advantages; dedicated unit tests, trainer, reward model, rollout worker, and weight updates are not included |
| Dashboard | Implemented: live polling, scopes, statistics, CRUD, history, search, model questions, reviewed proposals, outcome capture, and lesson review/promotion |
| Browser extension | Not implemented |
| Managed cloud / signup / billing | Not implemented |
| Graph memory / entity linking | Not implemented |
| BM25 | Implemented as opt-in scoring over scoped records |
| Vector indexes / reranking | Not implemented |
| Automatic fact conflict resolution | Not implemented |
| MCP / framework-specific adapters | Not bundled; use the common HTTP API from any compatible runtime |
| Distributed storage / HA / online migrations | Not implemented |
| SSO / per-user RBAC / key management UI | Not implemented |
| LoCoMo / LongMemEval / model benchmarks | Not executed; no comparative performance claims |

## Next milestones and evidence required

1. **Retrieval quality:** build a consented, labeled dataset with paraphrases, multilingual facts, temporal questions, and stale/contradictory records. Freeze a final holdout before tuning.
2. **Provider integrations:** implement explicit adapters, test failures/timeouts, measure extraction faithfulness and retrieval quality with actual model versions and usage logs.
3. **Scale:** profile realistic per-scope data sizes; add indexed retrieval and queueing only with latency, recall, and isolation evidence.
4. **Operations:** package a deployment-grade server, migrations, backups, quotas, observability, key rotation, and recovery drills.
5. **Learning operations:** add an evaluator/rollout service with protected suites, statistical confidence, canary monitoring, durable audit events, and role-based approvals; prototype the separately packaged RL adapter only after sequence data and reward validity are established; then add optional MCP/framework adapters.

A release may promote a capability to “implemented” only when code, a runnable example, failure tests, and documentation are present. The RL reward helpers remain experimental until dedicated failure tests and a runnable trainer integration are added. Production readiness additionally requires workload and security review; passing the included fixture is insufficient.
