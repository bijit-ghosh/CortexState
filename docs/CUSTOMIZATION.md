# Customization

## Scope and metadata

Use tenant for an organization or application boundary, user for the subject, agent for the application role, and session for a specific conversation or `persistent`. Scope values are identifiers, not authorization policies. The calling application must verify the user may access the supplied user/agent/session.

Metadata is your schema. Useful fields include `source`, `consent_reference`, `kind`, `conversation_id`, and `confirmed_by`. Avoid placing secrets in either text or metadata. Choose explicit TTLs for temporary state; absence of a TTL means no automatic expiry.

## Bring your own embeddings

```python
from cortexstate import Memory

def embed(text):
    # Call your approved embedding model or local model here.
    # Return its finite, nonzero numeric vector as a list.
    return approved_embedding_service(text)

memory = Memory("semantic.db", embedder=embed, embedding_id="my-provider/model/revision-1")
```

`approved_embedding_service` is deliberately an application-supplied integration, not an included provider. Set timeouts and retry budgets in that integration. Only the text passed to it leaves the library, and only if your callable sends it. The default mode sends nothing externally.

Keep the model/version identity fixed for a database. CortexState checks identity and dimensions but cannot detect a caller that changes model behavior while reusing the same identity. Create a new store and re-add approved facts when changing models. This preview has no online reindex/migration tool.

To serve this configured instance, pass it to `cortexstate.server.make_server(memory, credentials)` and call `serve_forever()`. The standard CLI service uses lexical retrieval only.

## Extract proposals, then approve facts

```python
from cortexstate.extraction import propose

messages = [{"role": "user", "content": "I prefer tea after lunch"}]

# A deterministic example adapter. Replace with your chosen model integration.
def extractor(conversation):
    return [{"text": conversation[0]["content"], "source_indices": [0]}]

proposals = propose(messages, extractor=extractor)
# Display proposals to an authorized reviewer or apply an explicit app policy.
# After approval: memory.add(proposals[0]["text"], scope=scope, metadata=...)
```

The boundary accepts only user/assistant messages, caps input size and fact count, validates source indices, and marks every proposal `needs_review`. It does not verify that a fact is entailed by its source: your evaluator or reviewer must do that. System prompts are rejected, and proposals are not persisted automatically. No live LLM extraction accuracy is claimed.

## Retrieval and context

Adjust `semantic_weight` in search only when an embedder is configured. Keep a development set of relevant, irrelevant, contradictory, stale, and cross-scope cases before changing weights. `context` uses the default retrieval weight and exact character budgeting. Applications needing provider token limits should apply their actual tokenizer and a second budget check before calling the model.

## Operational changes

For larger workloads, introduce an indexed storage backend behind a tested interface, rather than increasing the full-scan limit silently. For durable background work, add a queue with receipts, retry limits, and backpressure. For multi-user frontends, keep tenant credentials in the backend. Track these changes against the [capability matrix](CAPABILITIES.md), with measured regression results.
