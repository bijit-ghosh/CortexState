# CortexState JavaScript SDK

An ESM client for Node.js 20+, with TypeScript declarations and no runtime dependencies. It connects to a running CortexState service. Keep service keys in a trusted backend.

Build an installable archive from this directory with `npm pack`, then install the generated `.tgz` into your application using `npm install /path/to/cortexstate-client-0.2.0.tgz`. Registry publication and package-name availability are separate; this repository does not claim the package is already on npm.

```javascript
import {CortexState} from 'cortexstate-client';
const memory = new CortexState({url: 'http://127.0.0.1:8787', apiKey: process.env.CORTEXSTATE_API_KEY});
const scope = {user: 'alice', agent: 'assistant'};
const record = await memory.add('Alice prefers tea', {scope, idempotency_key: 'event-42'});
const results = await memory.search('tea', {scope, ranking: 'bm25'});
console.log(results);
await memory.update(record.id, 'Alice prefers coffee', {scope, expected_revision: record.revision});
```

Also available: `get`, `list`, `history`, `delete`, `context`, `stats`, `purgeExpired`, and the lower-level `call`. Errors from HTTP responses expose `.status`. Remote connections require HTTPS, redirects are rejected, and request timeouts default to 15 seconds. The package does not run a memory server or embedding model.
