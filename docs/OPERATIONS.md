# Operations

## Deployment boundary

This preview uses Python's stdlib threaded HTTP server with a 32-handler concurrency cap, a 64-connection accept queue, and a 10-second socket timeout. Use it locally or on a private development network. An internet deployment still requires a reviewed gateway for TLS, rate limits, request quotas, and monitoring; the included server has no built-in per-tenant quotas or production availability claim. Do not expose the SQLite file or embed tenant keys in a public frontend.

The Docker recipe runs as a non-root user and Compose binds only to loopback. Use `docker compose config` to validate your resolved configuration without sharing its output: it contains credentials. Docker execution is not part of the Python test suite.

## Credentials

Generate random keys with at least 32 ASCII characters and map them to tenant IDs in `CORTEXSTATE_KEYS`. The server rejects a missing mapping. Supply credentials through your secret manager or environment, not committed files. Rotation requires replacing the mapping and restarting the process. Keep the old and new key together during a deliberate overlap window if needed, then remove the old one. Keys authorize every user in their tenant.

## Persistence, backup, restore

Use a dedicated database file on persistent local storage. Each operation opens and closes its connection; writes are serialized by SQLite with a bounded 10-second busy wait. Do not use `:memory:` or a shared network filesystem. Schema version migrations are not supplied in this release.

For a consistent backup, stop writers or use SQLite's online backup API. Example with writers stopped:

```python
import sqlite3
from contextlib import closing
with closing(sqlite3.connect("cortexstate.db")) as source:
    with closing(sqlite3.connect("backup.db")) as destination:
        source.backup(destination)
```

Protect backup permissions and retention like the primary database. Restore into a separate path, open with the original embedding configuration, and verify a known scoped read before switching traffic. No automatic backup job is installed.

## Expiry and deletion

Expiry hides live facts but does not immediately remove their history. Schedule `purge_expired` separately for each authorized scope. Deletion and purge remove logical rows, history, and idempotency responses. They are not secure disk erasure: free pages and existing backups can retain prior content. Apply storage encryption, filesystem controls, and backup deletion policies appropriate to your data.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| HTTP 401 | Exact key and Bearer header; the service has no anonymous mode |
| HTTP 400 for scope | Omit tenant in HTTP; supply a nonempty user |
| No search hits | Exact scope, expiry, word overlap, metadata filters, embedding configuration |
| HTTP 409 | Fetch latest revision or use the original payload for a retry |
| Embedding identity mismatch | Reuse original model/version or create a new database |
| Database locked | Slow embedder or concurrent writes; investigate before increasing timeouts |
| Empty context | Facts may exceed the character budget; increase budget deliberately |

No prompt/credential/access URL logging is enabled by default. The health endpoint is liveness only; a deployment should add a non-sensitive readiness probe and external metrics before relying on it operationally.
