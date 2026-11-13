# CortexState FAQ

### Does it need an LLM API key?

No. The default library stores explicit facts and searches by word overlap. A key is needed only by a provider you choose to integrate. The HTTP service has its own tenant API keys, unrelated to model-provider keys.

### Does it learn automatically from every conversation?

No. You explicitly add facts. The optional extraction interface produces proposals for review; it does not persist them or silently call a model. This keeps retention policy in your application.

### Is semantic search included?

The engine supports cosine similarity through a supplied embedding callable. No pretrained embedding model or hosted embedding service is bundled. Default server/CLI retrieval is lexical. See [customization](CUSTOMIZATION.md) for a custom configured server.

### Why is a remembered fact missing from search?

Check the database path and all four scope fields, then expiry and metadata filters. In default mode, the query must share words with the fact. Context can also omit a result that does not fit the character budget.

### Can agents share memory?

Only through explicit application choices. Different agent fields are isolated. An authorized backend may read several scopes or deliberately use a shared agent identifier. CortexState does not infer collaboration permissions.

### Does `max_chars` guarantee a token limit?

No. It bounds the returned JSON string in Python characters. Token counts vary by model, language, and tokenizer. Apply the target model's tokenizer to the final request when enforcing a token budget.

### What happens when a fact expires?

It stops appearing in live get/list/search/context results. History remains until explicit deletion or `purge_expired`. No automatic cleanup job is installed.

### Does delete erase every copy?

It removes the current row, history, and stored retry responses in the active database. Backups, free disk pages, or downstream copies require separate retention controls. It is not secure disk erasure.

### Is this a drop-in replacement for another memory SDK?

No. CortexState defines its own scope model, operations, and retry semantics. Existing applications should adapt their integration explicitly and run their own acceptance tests. No compatibility shim or import utility is currently included.

### Can I use a browser directly with the service?

Tenant keys grant access across users in their tenant, so keep them in a trusted backend. Have the browser call that backend, which authenticates users and controls scope selection. A browser console and end-user authorization layer are not included.

### Where are the dashboard, cloud signup, and framework plugins?

They are not implemented in this developer preview. See [capabilities and roadmap](CAPABILITIES.md) for an explicit feature inventory. Documentation does not imply a feature exists.

### How do I report a problem?

Open a repository issue with your version, execution mode, synthetic reproduction, expected result, and actual result. Remove credentials and private memories. Follow the [security policy](../SECURITY.md) for sensitive reports.
