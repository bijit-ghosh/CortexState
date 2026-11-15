# Operations

## Deployment boundary

The HTTP adapter uses Python's stdlib threaded server with a 32-handler concurrency cap, a 64-connection accept queue, a 10-second socket timeout, a request body limit, and configurable per-key process-local rate limiting. It has explicit per-key operation permissions and `/ready` checks database connectivity. Treat it as a private service behind a reviewed TLS gateway; it does not implement end-user identity, per-user authorization, distributed quotas, HA, or a production availability target. Do not expose the SQLite file or embed service keys in a public frontend.

The Docker recipe runs as a non-root user and Compose binds only to loopback. Use `docker compose config` to validate your resolved configuration without sharing its output: it contains credentials. Docker execution is not part of the Python test suite.

## Credentials

Generate random keys with at least 32 ASCII characters and map each key to a structured policy in `CORTEXSTATE_KEYS`:

```json
{"<secret>": {"tenant": "team-a", "principal": "memory-service", "permissions": ["memory:read", "memory:write"]}}
```

Use the smallest permission set needed. `principal` is only an operator-configured log label. A key still authorizes those operations across all user/agent/session scopes within its tenant; your trusted backend must enforce end-user access. The server rejects legacy key-to-tenant mappings by default. `--allow-legacy-tenant-keys` enables a temporary migration path with full permissions; remove it after all keys have explicit policies. Supply credentials through a secret manager or environment, never committed files. Rotation currently requires replacing the mapping and restarting. A deliberate overlap window can include old and new keys, then remove the old key.

The built-in limiter uses a token bucket per key and process: 600 requests/minute with a burst of 60 by default. Tune with `serve --requests-per-minute` and `--burst`. A 429 response includes `Retry-After`. Buckets reset on restart and are not coordinated between workers, replicas, or tenants sharing a key. Add gateway-level aggregate, tenant, and model-spend quotas for shared deployments.

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

The service logs method, normalized route, HTTP status, configured principal label, and duration; it omits request bodies, credentials, query strings, and user scope. Keep principal labels non-sensitive. `/health` is liveness; `/ready` confirms only that a simple database query succeeds. Add external metrics, alerting, request tracing with privacy controls, and a monitored readiness/liveness setup before relying on it operationally.

## Production deployment checklist

Before internet-facing or sensitive use, place the service behind a maintained TLS gateway; authenticate callers and enforce user-level authorization in a trusted backend; configure shared rate, request-size, and provider-spend quotas; restrict dashboard access; pin and scan dependencies and container images; define retention and backup encryption; establish tested restore and incident procedures; and complete a threat model and independent security review. Test migrations before upgrades because this version has no online migration framework. The included checks do not provide load, multi-process isolation, failover, or recovery certification.
