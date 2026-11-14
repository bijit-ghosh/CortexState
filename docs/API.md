# API contract

All memory endpoints use `POST /v1/memories/{operation}`, `Authorization: Bearer <key>`, `Content-Type: application/json`, and a single Content-Length header. Maximum body size is 65,536 bytes. Chunked request bodies are unsupported. The unauthenticated `GET /health` endpoint returns liveness only.

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
