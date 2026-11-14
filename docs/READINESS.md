# Readiness scorecard

Scores are a maintainer assessment of the repository at CortexState 0.4.0,
not an external audit, benchmark, or certification. A 10 means independently
verified against the stated criterion, not merely that documentation exists.

| Area | Score | Evidence and remaining work |
| --- | ---: | --- |
| Core memory behavior | 6/10 | Scoped SQLite records, revision checks, expiry, deletion, and a measured synthetic fixture exist. Add migration guarantees, scale/fault evaluation, and broader independent use. |
| Deployment security | 3/10 | Bearer keys, bounded request bodies/concurrency, and scoped records exist. Keys grant tenant-wide access; TLS, per-user roles, quotas, rate limits, managed secret rotation, and external security review are missing. |
| Operational readiness | 3/10 | Backup guidance and a container recipe exist. No schema migration framework, HA store, readiness/metrics endpoint, restore automation, or supported availability target. |
| Cross-stack learning | 4/10 | Outcome ledger, held-out scorecard fields, approval, rollback, and deletion exist. Evaluator claims are caller-supplied and not independently verified; no autonomous promotion is provided. |
| RL capability | 2/10 | Experimental reward helpers/design only. No trainer, rollout pipeline, reward model, policy update, safety study, or RL evaluation result. |
| Open specification readiness | 3/10 | CAMI 0.1.0 draft, schemas, governance notes, and mapping guidance now exist. No importer/exporter, conformance runner, independent implementation, neutral governance, or adoption evidence. |

## What “production ready” still requires

Before serving sensitive or high-volume workloads, prioritize per-principal
authorization, transport security at a supported gateway, tenant quotas and
rate limits, migrations and restore drills, observability, data retention
controls, threat modeling, dependency review, and an external security review.
Then define workload targets and validate them with repeatable load, failure,
backup/restore, and isolation evaluations. The current server is documented
for local/private trusted-backend use. No score here certifies it for
internet-facing or regulated production deployment.

## What “open standard” requires

CAMI is an openly published proposal. Calling it an established open standard
requires evidence beyond an open repository: multiple independent
implementations, a stable conformance suite, transparent change control,
independent stewardship, compatibility policy, and adoption. Until these
exist, describe it as “CortexState's proposed open agent-memory interchange
specification.”
