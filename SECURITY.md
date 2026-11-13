# Security

This is a developer preview. Do not store sensitive production data until your deployment, providers, authorization, retention, and recovery procedures have been reviewed.

Tenant API keys are service credentials. Your backend must authorize user/agent/session access; CortexState's exact scopes do not authenticate end users. Database access bypasses HTTP authorization. Use storage encryption and restricted filesystem permissions.

Memory text and extraction output are untrusted data. They must not authorize tools, modify system instructions, or grant access to another scope. The context trust marker documents this boundary; it is not a prompt-injection defense by itself.

For a suspected vulnerability, avoid public issues containing credentials or private records. Use GitHub private vulnerability reporting if enabled, or contact the maintainer through their GitHub profile to establish a private channel. No response SLA is promised. Public issues are appropriate for non-sensitive defects with synthetic reproductions.
