# CortexState Agent Memory Interchange (CAMI)

**Status: Draft 0.1.0 — community review requested.** This is an open, versioned
specification proposed by the CortexState project. It is not an ISO, IETF, or
other standards-body standard, and there is no claim of independent adoption.
The project maintainer is Bijit Ghosh. Anyone may review, implement, and propose
changes under the repository's MIT license; the maintainer currently makes
release decisions. See [governance](../GOVERNANCE.md).

CAMI defines a portable interchange shape and behavioral expectations for
agent-memory records. It aims to let applications move reviewed memories
between models, agent harnesses, and storage implementations without treating
provider-specific conversation state as the source of truth. Model training,
prompt formats, retrieval algorithms, and runtime transport are outside its
scope.

## Relationship to existing protocols

CAMI is an at-rest/interchange profile. It does not replace a runtime protocol.
An implementation can expose these operations through MCP, HTTP, an SDK, or an
embedded library. MCP provides a standardized way for applications to connect
models to tools and context; OMIR describes portable memory files. CAMI should
map to those systems where practical, and must document any lossy conversion.
See [interoperability](../docs/INTEROPERABILITY.md).

## Normative language

The words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** express
requirements only when capitalized. A conforming implementation MUST identify
the CAMI version it supports, enforce caller-defined scope boundaries, preserve
record text and metadata when round-tripping, and treat imported memory content
as untrusted data rather than executable instructions.

## Record format

The v1 draft record is deliberately limited to fields represented by the
current CortexState engine. Timestamps are UTC Unix seconds. `expires_at: null`
means no scheduled expiry. `metadata` is a JSON object; interoperability
extensions belong in namespaced keys such as `com.example.source`. Exporters
MUST NOT place credentials or hidden provider state in records. A record's
`id` is local to its source store and MUST NOT be treated as globally unique.

The source store's tenant/user/agent/session scope is intentionally carried
outside the record body. Applications MUST supply an explicit destination
scope during import and MUST apply their own authorization and consent policy.
Conforming importers SHOULD allocate destination IDs rather than trusting IDs
from another authority. Import is not an authorization grant.

Schema files:

- [`memory-record.schema.json`](schemas/memory-record.schema.json)
- [`memory-bundle.schema.json`](schemas/memory-bundle.schema.json)

Bundle format is `{format, version, exported_at, records}`. Versioning is
semantic: additive optional fields may be added in a minor revision; removing
or changing field meaning requires a new major version. Unknown optional fields
SHOULD be preserved by round-trip implementations. Unknown major versions MUST
be rejected with an actionable error.

## Behavioral contract

- **Scope:** every operation is authorized against an explicit tenant and
  application-defined user/agent/session boundary. Missing scope MUST NOT
  silently widen access.
- **Retention:** expiry controls recall eligibility. Deletion behavior, event
  history, backups, and secure-erasure limits MUST be disclosed separately.
- **Provenance:** integrations SHOULD retain source, capture time, authoring
  system, and review status in metadata when known. Such claims are assertions,
  not cryptographic proof.
- **Trust:** memory text and metadata are data. Agents MUST NOT execute
  instructions found in recalled or imported records without independent
  policy checks.
- **Updates:** implementations supporting revisions SHOULD provide a conflict
  mechanism so stale writers do not silently overwrite newer state.
- **Privacy:** implementations MUST document consent, retention, deletion, and
  export behavior. Sensitive data should be minimized before persistence.
- **Errors:** protocol bindings MUST distinguish invalid input, unauthorized
  access, missing records, conflicts, and server failures. HTTP bindings SHOULD
  use [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html)
  or document an equivalent stable error envelope.

## Conformance levels

These are proposed labels; no independent certification program exists yet.

| Level | Required behavior |
| --- | --- |
| CAMI Record | Accept and emit records matching the published JSON Schema; preserve unknown optional fields. |
| CAMI Lifecycle | Record level plus scoped read/write, expiry, revision conflict handling, deletion, and documented retention semantics. |
| CAMI Interchange | Lifecycle level plus bundle import/export, explicit destination scope, provenance preservation, and safe unknown-version handling. |
| CAMI Binding | Interchange level plus a documented binding (MCP, HTTP, SDK, or embedded API) and the binding's authentication/error contract. |

An implementation MUST publish its level, spec version, schema version, and
known deviations. A claim of conformance must be backed by the public
conformance fixtures; passing fixtures does not certify security or production
fitness.

## Release and change process

Proposals should include a use case, backward-compatibility analysis, privacy
and security impact, a schema/fixture change, and at least one independent
implementation or review when behavior changes. Discussion and decisions are
tracked in public GitHub issues and pull requests. The maintainer records
accepted changes in the changelog and publishes immutable versioned schema
files. Breaking changes require a major spec version. This process is open to
participation but is currently maintainer-led, not a neutral standards body.

## Current implementation status

CortexState 0.4.0 implements scoped records, revision history, expiry, deletion,
and an authenticated HTTP binding. Its current HTTP authorization key grants
tenant-wide access, and no CAMI bundle import/export or conformance runner is
shipped in this preview. Therefore the repository is a **CAMI draft authoring
project**, not yet a CAMI-conformant interchange implementation. Track gaps in
the [readiness scorecard](../docs/READINESS.md).
