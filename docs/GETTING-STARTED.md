# Getting started with CortexState

## One-command dashboard

After installation, run `cortexstate demo` (or `python -m cortexstate demo`). It starts a loopback service with three synthetic memories and prints a disposable key. Open the displayed `/dashboard` URL and paste that key to connect. No database configuration is needed for this demo; it uses temporary storage. Ctrl+C stops it and removes the temporary database.

For persistent data, use `serve` with a database path and tenant keys as described below. To enable actual provider calls, follow [model setup](MODELS.md).

## 1. Install from source

Use Python 3.10 or later. Node.js 20 or later is needed only for the JavaScript client. The Python core has no runtime dependencies and requires no model credentials.

```bash
git clone https://github.com/bijit-ghosh/CortexState.git
cd CortexState
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Then install and run the offline example:

```bash
python -m pip install .
python -m examples.support_workflow
```

If activation is unavailable, invoke the environment's Python executable directly. Installing may download build tooling; the installed default memory engine itself makes no network calls. Run examples from the cloned repository because examples are not included in the installed Python package.

## 2. Store and retrieve a fact from the terminal

```bash
python -m cortexstate --db demo.db add --tenant demo --user alice "Alice prefers tea"
python -m cortexstate --db demo.db search --tenant demo --user alice "tea"
python -m cortexstate --db demo.db context --tenant demo --user alice "tea"
```

The first command returns an ID and revision `1`. Search returns a matching record with `score` and `signals`. Context returns a JSON string in `data`, its character count, the selected IDs, and `trust: untrusted_memory_data`.

Reuse the same database and scope to retain memory across processes. Re-running an unkeyed CLI add creates another record. Use the Python/API idempotency key for retried writes.

## 3. Understand your scope

```python
from cortexstate import Scope
scope = Scope(tenant="demo", user="alice", agent="assistant", session="persistent")
```

Every field must match on later reads. The CLI defaults to agent `default`, while the example above uses `assistant`: changing that value selects a different scope. Persistent and conversation-specific sessions are separate; CortexState does not merge them automatically.

## 4. Run the HTTP service

Generate credentials in the server terminal, without pasting a secret into a source file.

PowerShell:

```powershell
$env:CORTEXSTATE_API_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"
$keyMap = @{}
$keyMap[$env:CORTEXSTATE_API_KEY] = 'demo'
$env:CORTEXSTATE_KEYS = $keyMap | ConvertTo-Json -Compress
python -m cortexstate --db service.db serve
```

Bash:

```bash
export CORTEXSTATE_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export CORTEXSTATE_KEYS="$(python -c 'import os,json; print(json.dumps({os.environ["CORTEXSTATE_API_KEY"]:"demo"}))')"
python -m cortexstate --db service.db serve
```

The server runs in the foreground on `127.0.0.1:8787`; Ctrl+C stops it. A separate client terminal must be provisioned with the same `CORTEXSTATE_API_KEY` through your local secret workflow. New terminals do not automatically inherit changes made in an existing shell. Never commit the key.

## 5. Call it from your backend

Save this as `client_demo.py` and run `python client_demo.py` in the client environment:

```python
import os
from cortexstate.client import Client

client = Client("http://127.0.0.1:8787", os.environ["CORTEXSTATE_API_KEY"])
scope = {"user": "alice"}
record = client.call("add", scope=scope, text="Alice prefers tea",
                     idempotency_key="getting-started-tea")
print(record["id"], record["revision"])
print(client.call("search", scope=scope, query="tea"))
```

HTTP scope omits tenant; the service derives it from the credential. Use the same server database and tenant mapping after a restart to retain access to the same facts.

## 6. Correct or forget

```python
current = client.call("get", scope=scope, identifier=record["id"])
updated = client.call("update", scope=scope, identifier=current["id"],
                      text="Alice now prefers coffee", expected_revision=current["revision"])
print(client.call("history", scope=scope, identifier=updated["id"]))
client.call("delete", scope=scope, identifier=updated["id"],
            expected_revision=updated["revision"])
```

An HTTP 409 means the stored revision or retry payload conflicts with your request. Read current state and resolve the difference; do not blindly retry a stale edit. Logical deletion removes the fact, history, and replay receipt. Disk pages and backups have their own retention requirements.

Continue with [integration patterns](INTEGRATION-PATTERNS.md), [API details](API.md), and [operations](OPERATIONS.md).
