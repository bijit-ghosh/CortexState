# API contract

Memory endpoints use `POST /v1/memories/{operation}` and outcome-learning endpoints use `POST /v1/learning/{operation}`. Both require `Authorization: Bearer <key>`, `Content-Type: application/json`, and a single Content-Length header. Maximum body size is 65,536 bytes. Chunked request bodies are unsupported. The unauthenticated `GET /health` endpoint returns liveness only.

Every body includes `scope`. The API assigns `tenant` from the credential; callers send:

```json
{"scope": {"user": "alice", "agent": "assistant", "session": "persistent"}}
```

`user` is required. Defaults: `agent=default`, `session=persistent`. These fields match exactly: a session query does not automatically include persistent memories, and an agent cannot implicitly read another agent's scope. Your authorized backend can deliberately combine separate calls.

| Operation | Additional body fields | Result |
| --- | --- | --- |
| `add` | `text`; optional `metadata`, `ttl_seconds`, `idempotency_key` | Memory record |
| `get` | `identifier` | Current live record |
| `list` | Optional `limit` (1–1000), `offset` | Live records ordered by created time and ID |
| `search` | `query`; optional `limit` (1–100), `metadata`, `semantic_weight` (0–1) | Ranked records with `score` and `signals` |
| `stats` | None | Scoped live/expired counts, revision count, embedding identity, generation availability |
| `propose` | `messages` (user/assistant role/content objects) | Unpersisted review proposals; calls configured generation model |
| `answer` | `question` | Model answer, retrieved memory IDs and reported token usage |
| `context` | `query`; optional `max_chars` (2–1,000,000), `limit` (1–100), `metadata` | JSON string, exact character count, memory IDs, trust marker |
| `update` | `identifier`, `text`, `expected_revision`; optional `metadata` | Updated record |
| `history` | `identifier` | Ordered revision events; includes expired memories until purged |
| `delete` | `identifier`, `expected_revision` | `null`; current row, history, replay data removed |
| `purge-expired` | None | Number removed from this scope |

## Deployment learning endpoints

All learning endpoints also require the same exact `scope`; the server assigns the tenant from the API key. Outcomes and candidate text are returned as untrusted data and are never added to normal retrieval automatically.

| Endpoint | Required fields | Result |
| --- | --- | --- |
| `POST /v1/learning/record` | `task`, `outcome`, `summary`, `consent: true`; optional `source`, `measures`, `event_key` | Idempotent experience record for success, failure, correction, blocked, or unsafe outcome |
| `POST /v1/learning/list` | Optional `limit` (1–100), `before` | Recent same-scope experiences |
| `POST /v1/learning/candidates` | Optional `limit` (1–100), `status` | Same-scope candidate lessons and their most recent evaluation |
| `POST /v1/learning/propose` | `evidence_ids`, `content`; optional `category` | Staged candidate linked to retained same-scope evidence |
| `POST /v1/learning/evaluate` | `identifier`, `suite`, `evaluator`, `heldout: true`, `total`, baseline/candidate pass counts, safety regressions, baseline/candidate tokens and latency | Immutable scorecard; reports whether all non-regression and strict-gain gates pass |
| `POST /v1/learning/promote` | `identifier`, `approved_by` | Adds an evaluated lesson to ordinary memory after explicit trusted-backend approval |
| `POST /v1/learning/reject` | `identifier`, `reason` | Marks an unpromoted candidate rejected |
| `POST /v1/learning/rollback` | `identifier`, `expected_revision` | Revision-checked removal of a promoted lesson; scorecard remains |
| `POST /v1/learning/delete-experience` | `identifier` | Deletes the experience and derived candidates/promoted lessons |

The promotion gate requires the candidate to match or exceed baseline task success, tokens, and latency; have zero reported safety regressions; and strictly improve at least one of task success, tokens, or latency. Both versions must be scored against the same protected holdout suite. The caller supplies the evaluator label and `heldout` flag; CortexState cannot verify that the caller's evaluator is independent, that the suite was actually held out, or that scorecard values are truthful. The static tenant-key model has no fine-grained roles: every accepted key can call every operation for its tenant. Put evaluator and approval authorization in your trusted backend; `approved_by` is an audit label, not authentication.

Experience `summary` is limited to 4,096 characters. `source` and `measures` are finite JSON objects limited to 4 KiB each. Record only consented, redacted summaries; do not send raw transcripts, secrets, or credentials by default. `event_key` deduplicates a repeated event and returns HTTP 409 if reused with a different payload.

Successful responses use `{"result": ...}`. Errors use `{"error": ...}` with 400/401/404/409/411/413/415/500 statuses. Both clients reject remote plaintext URLs and do not follow HTTP redirects. Python exposes HTTP failures as `urllib.error.HTTPError`; JavaScript errors include `.status`.

Search also accepts `ranking="overlap"` (default) or `ranking="bm25"`. `context` retains the default overlap ranking. Generation endpoints return HTTP 503 when no generation model is configured. Propose never stores its output; review it and call add explicitly. Provider calls may incur costs. The static console assets are public; every data operation remains authenticated.

Memory records contain `id`, `text`, `metadata`, `revision`, `created_at`, `updated_at`, and `expires_at`. Timestamps are UTC Unix seconds; absent expiry is `null`. TTL is an integer from 1 to 315,360,000 seconds. Updating preserves the existing expiry; TTL extension is not implemented. Omitted update metadata preserves the previous object; `{}` clears it.

Text: nonblank, at most 32,768 characters. Query: at most 8,192 characters. Scope fields and idempotency keys: nonblank, at most 256 characters. Metadata must be a finite JSON object and fit in 16 KiB when serialized. Search metadata filters match top-level values by equality; no expression language is evaluated.

Example add:

```json
{
  "scope": {"user": "alice"},
  "text": "Alice prefers tea",
  "metadata": {"source": "confirmed"},
  "ttl_seconds": 86400,
  "idempotency_key": "conversation-17-fact-1"
}
```

The CLI supports local add, search, list, context, purge-expired, and serving. Use Python or HTTP for revision editing and history. `python -m cortexstate --help` lists arguments; `--db` precedes the subcommand.
