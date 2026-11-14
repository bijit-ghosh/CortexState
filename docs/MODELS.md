# API-backed memory and model calls

Install the optional adapter from the repository:

```bash
python -m pip install ".[openai]"
```

Configure these server environment variables through your secret-management workflow:

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Provider credential; never enter it into the dashboard service-key field |
| `CORTEXSTATE_EMBEDDING_MODEL` | Optional embedding model ID, for example `text-embedding-3-small` |
| `CORTEXSTATE_GENERATION_MODEL` | A Responses-compatible model ID available to your account; explicitly selected by you |
| `CORTEXSTATE_KEYS` | Separate JSON mapping of CortexState service keys to tenant IDs |

Then run `cortexstate --db semantic.db serve`. Use a new database when enabling/changing embeddings: each store locks its embedding identity and dimensions. The demo intentionally ignores model variables and makes no external calls.

Embedding calls occur on add, update, and query when enabled. `propose` calls the generation model to extract facts, validates source references, and returns proposals without storing them. `answer` retrieves context, calls the generation model, and returns text, memory IDs, and reported input/output token counts. It does not execute tools or write memory.

```python
import os
from cortexstate import Client
client = Client('http://127.0.0.1:8787', os.environ['CORTEXSTATE_API_KEY'], timeout=60)
scope = {'user': 'alice'}
proposals = client.propose([{'role':'user','content':'I prefer email for project updates'}], scope=scope)
print(proposals)  # Review before adding any fact.
print(client.answer('What do we know about project updates?', scope=scope))
```

The JavaScript SDK exposes the same `propose(messages, {scope})` and `answer(question, {scope})` methods; set `timeoutMs: 60000` for generation calls. The dashboard uses a longer timeout for these operations. The provider adapter bounds output to 2,048 tokens, requests no stored response, and uses a 20-second provider timeout with at most one SDK retry. Token limits and model availability remain provider-specific. Configure provider billing limits; CortexState does not enforce per-tenant spend quotas yet.

The adapter follows the official [embedding API](https://developers.openai.com/api/reference/python/resources/embeddings/methods/create) and [Responses API](https://developers.openai.com/api/reference/python/resources/responses/methods/create). Automated tests use controlled mock responses. No live model accuracy or provider-cost benchmark is claimed without a recorded credentialed run. Custom providers remain possible through the existing embedding and extraction callables.
