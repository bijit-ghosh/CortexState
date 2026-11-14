# CortexState live dashboard

Run `cortexstate demo` for a temporary sample workspace, or start your configured service and open `http://127.0.0.1:8787/dashboard`. Connect using a tenant service key. Never open the HTML file directly from disk: its API and assets are served by CortexState.

The dashboard refreshes live memory counts, expiry counts, revision counts, and the visible collection every three seconds while the tab is visible. This is near-real-time polling, not a WebSocket stream. Disable Live refresh to pause it.

Select the exact user, agent, and session. The memory list supports paging, overlap/BM25 search, and score details. The inspector shows metadata and history, and edits submit the displayed revision. A conflict requires reselecting the latest record. Forget and expiry purge require an explicit confirmation in the console.

The model workbench enables questions and extraction when the server has a generation model configured. Buttons clearly identify API calls. Extracted facts are proposals: review their content before choosing Approve and store. An answer displays the model, number of recalled facts, and token usage returned by the provider.

The deployment learning panel records concise outcomes only after an explicit operator consent check, lists recent experiences and scoped lesson candidates, and displays their held-out scorecards. The operator can reject a candidate or promote one whose recorded scorecard passed the gate. Evaluation itself runs in your trusted external evaluator; the console does not execute a benchmark or verify that a suite is truly held out. The service key authorizes tenant-wide access, so restrict dashboard access to trusted operators.

Console activity shows recent actions in this tab, not a durable audit trail. Provider credentials stay on the server. The service key is held only in JavaScript memory and cleared on disconnect/reload; browser storage is not used. Serve remotely only over HTTPS behind your reviewed gateway. This is a trusted operator tool with tenant-wide access, not a public customer portal.
