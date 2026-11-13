# Practical CortexState use cases

These are application patterns supported by the existing library and API. They are not prebuilt products, domain compliance claims, or framework integrations.

## Customer support continuity

Remember a customer's confirmed language preference, contact channel, or troubleshooting steps already completed. Use tenant for the support organization, user for the customer ID, and agent for the support application. Keep preferences in a persistent session and temporary case context in a ticket-specific session.

Store a source reference in metadata, retrieve relevant facts before drafting a response, and correct a fact using the revision from a fresh read. Your support backend still checks that the staff member may access that customer. Run [the support workflow](../examples/support_workflow.py) to see retries, revision history, context, isolation, and deletion together.

## Coding assistant project context

Store approved project conventions such as test commands, preferred runtime, or the reason for an architecture decision. One possible scope uses tenant for the engineering organization, user for a project identifier, agent for a coding assistant, and session for the active branch or `persistent`.

Use metadata such as `repository`, `commit`, and `kind` to identify where the fact came from. Recheck stale conventions against the repository before acting. Stored text must not become permission to execute commands or access secrets. CortexState has no repository synchronization or editor plugin in this release; the application is responsible for refreshing facts.

## Workflow handoff

A workflow can store concise, confirmed checkpoints such as “invoice validation completed” or “waiting for approval.” Use a workflow instance as the session and include the authoritative job ID in metadata. Retry a checkpoint write with an idempotency key derived from the event ID.

Keep the workflow engine or business database authoritative for execution state. CortexState supplies context; it does not implement task scheduling, exactly-once external actions, or durable job orchestration. Use a TTL for short-lived notes, and purge expired records explicitly.

## Personal assistant preferences

Remember preferences the user explicitly chooses to retain. Keep each user in a separate scope, allow correction through a revision-checked edit, and provide a deliberate forget action. A preference can guide a recommendation but should not authorize a purchase, message, or calendar change.

## Fit checklist

| Question | Practical choice |
| --- | --- |
| Is this an approved fact or an uncertain model inference? | Review uncertain extraction proposals before adding them |
| Who may retrieve it? | Select an exact scope and enforce authorization in the application |
| How long is it useful? | Set a TTL for temporary facts and schedule explicit purges |
| What proves its origin? | Store non-sensitive source references in metadata |
| Can another writer change it? | Read the latest revision before updating or deleting |
| Is the dataset too large for a scan? | Profile it; indexed retrieval is not included yet |

For credentials, large document archives, financial ledgers, or authoritative workflow state, use a purpose-built system and store only approved references or context in CortexState.
