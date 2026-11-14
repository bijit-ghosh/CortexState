# Interoperability

CortexState is intended to work across model providers, agent harnesses, and
skills through an application-owned memory layer. Its proposed open format is
[CAMI](../spec/README.md), which describes record interchange. It does not
standardize a model API or claim universal adoption.

## Protocol layers

| Layer | Role | CortexState direction |
| --- | --- | --- |
| Memory interchange | Move durable memory records between stores | Draft CAMI records and bundles |
| Runtime connection | Let an agent discover and invoke tools/context | Keep the core provider-neutral; expose a future MCP adapter or use the current HTTP/SDK binding |
| Model inference | Generate, embed, or evaluate content | Caller-configured provider integration; model identity belongs in provenance |
| Agent harness | Orchestrate tools, prompts, and skills | Harness maps its own identity and authorization to explicit memory scope |

MCP is a standardized runtime protocol for connecting AI applications to tools
and context; CAMI should be transported through a documented MCP binding when
implemented. OMIR focuses on portable memory files and is a useful mapping
target for at-rest exchange. These projects solve adjacent problems and evolve
independently. CortexState currently has no MCP server or OMIR importer, so do
not claim compatibility until a mapping and conformance fixtures exist.

## Portability rules

- Map each source memory to one destination record; document dropped fields.
- Never infer tenant/user ownership from imported metadata. The receiving
  application selects the destination scope and authorizes the operation.
- Treat text, metadata, provenance labels, and evaluation summaries as
  untrusted. Imported content cannot grant tool access or approval.
- Do not move embeddings across providers unless the embedding model/version
  and dimensions are identical and the target explicitly accepts them.
- Preserve source identifiers only as provenance; use destination IDs for
  local addressing.
- Preserve timestamps only as source assertions. Do not use them as proof of
  identity or integrity.
- Publish compatibility claims against a specific CAMI version and fixtures.

## Current gaps

The current SDKs call CortexState's HTTP operations, but the repo does not yet
ship a standardized export/import API, a CAMI fixture runner, an MCP binding,
or an OMIR mapping. These are the highest-value interoperability milestones;
the [readiness scorecard](READINESS.md) tracks them separately from product
security and deployment maturity.
