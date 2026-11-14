# Project and specification governance

CortexState is maintained by Bijit Ghosh and released under the MIT license.
The project is open source and accepts public issues and pull requests. The
maintainer currently controls merges, releases, and the proposed Agent Memory
Interchange (CAMI) specification; it is not governed by a standards body.

## How changes are reviewed

Proposals should state the user problem, expected behavior, compatibility
impact, data-handling implications, and evidence. Changes to the API, record
format, security boundary, or retention behavior need corresponding docs and
fixtures. A reviewer should be able to reproduce claims from the repository.
Evaluation results must identify the suite, version, environment, and limits.

## Specification changes

CAMI drafts and schemas live under `spec/`. Proposals are discussed in public
GitHub issues or pull requests. Accepted changes are recorded in the changelog;
published schema versions are immutable. The current process is maintainer-led.
Before describing CAMI as an adopted or community-governed standard, the project
needs independent implementations, public consensus rules, neutral stewardship,
and a maintained conformance program.

## Security and release decisions

Report vulnerabilities privately using the contact route documented in
`SECURITY.md`. Do not include real user memories or credentials in issues,
fixtures, or benchmark artifacts. Release notes must distinguish implemented
features from proposals and experimental components.
