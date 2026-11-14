# AI Agents Need a Learning Loop: Why I’m Building CortexState

*A shared memory layer for carrying verified experience across models, harnesses, skills, and codebases.*

When I started building AI agents, I expected each new model and better prompt to make the next task easier. I kept hitting the same gap: an agent could reason, call tools, and read a repository, but useful context did not survive the task.

It searched for architecture rules the team had documented and missed coding conventions explained in earlier sessions. A correction fixed one answer, then disappeared when the conversation ended or I changed models or harnesses. Tokens and engineering time went into rediscovering what the project already knew.

I wanted a coding agent to remember how a codebase is organized, which architectural boundaries matter, which checks must pass, and what prior failures taught us. I also wanted it to prove a change before opening a pull request. That led me to build CortexState around a simple engineering requirement: **experience should persist across tasks, and a lesson should earn its way into future behavior.**

## Continuous learning needs durable state and a control loop

Conversation history alone does not improve an agent. The system must capture outcomes, preserve evidence, turn repeatable results into candidate lessons, evaluate those candidates against a fixed baseline, and control when a lesson enters future context.

CortexState keeps that loop outside any one model. A deployment can change models, harnesses, or skills while keeping its memory and outcome records. Hosted model APIs still benefit: the system improves the agent’s **external memory and procedures**. Owners of trainable weights can add a separate offline learning path. Both paths need reliable outcomes and protected evaluation.

Durable memory needs explicit scope, provenance, expiry, correction, and deletion. Improvement needs versioned tasks, measurements, fixed acceptance criteria, approval, and rollback. Those controls make experience reviewable across task and model changes.

## The architecture has three connected paths

![CortexState architecture for coding agents. The upper path prepares scoped context and gates code changes. The middle path turns deployment evidence into reviewed memory. The lower path shows optional offline policy training for weights the model owner controls.](../../assets/coding-agent-learning-loop.svg)

The **runtime path** prepares an agent for a task. The host identifies the repository, branch, model, harness, and skills, checks saved rules against their source, then retrieves task-specific context through the Python library, TypeScript SDK, or trusted HTTP API. The host keeps authorization, tools, and system policy in its own control plane.

The **verification path** runs after each change. The harness or CI executes tests, lint, security and permission checks, then reviews the diff. A failure returns a concrete finding to the agent. The host reruns the check and blocks pull-request creation until required gates pass.

The **learning path** records a short, consented outcome with repository, code, model, harness, and skill versions. A candidate lesson links to its evidence. An external evaluator compares it with the baseline on a protected suite. A reviewer approves promotion; monitoring and revision-checked rollback keep the change reversible.

The diagram also shows a separate **offline RL path**. It trains only models whose owners control the weights. RL does not run inside the live memory service, and the current CortexState release does not ship a rollout worker or trainer.

## What CortexState remembers

Save compact, actionable records rather than full transcripts by default. For a coding agent, useful memories include:

- repository architecture rules, such as which layer owns a business operation;
- coding conventions and required build, test, lint, and security commands;
- reviewed decisions, including why a dependency or service boundary exists;
- confirmed task outcomes, such as a test failure, user correction, blocked action, or verified success;
- evidence references, source paths, revisions, and versions needed to check freshness;
- measures such as input and output tokens, latency, check results, and resource cost.

Each memory belongs to an explicit tenant, user/project, agent, and session scope. A persistent project scope can hold approved architecture rules; a branch session can hold temporary task details. Metadata identifies the source path and commit. The host compares that provenance with the checkout, refreshes stale rules, and excludes facts it cannot verify.

Every retrieved memory remains untrusted reference data. It cannot grant tool permissions, override system instructions, or prove that a repository rule is still current. The host applies policy before the model sees the context.

## One task, from first recall to approved lesson

Consider an agent adding retry handling to a payment service. Before editing, the host resolves the repository and branch, checks the source revisions of relevant architecture and test rules, and retrieves a small context about payment authorization. It attaches that context within a prompt budget instead of replaying chat history or rescanning every project document.

After the agent proposes a patch, the host runs required checks. A security scanner might find that a generated configuration file has broader read permissions than policy allows. The agent adjusts the file mode or storage design and reruns the check. The host blocks the pull request until tests and security gates pass.

The application records which checks ran, whether they passed, the versions involved, and the task’s tokens and latency. It can preserve the lesson about file-permission policy without retaining the credential, full diff, or private transcript.

The coding harness must fetch repository facts, compare revisions, execute tools, return failures, and enforce the pre-PR gate. CortexState supplies scoped context and an outcome ledger; the host supplies code access and execution.

## How the improvement loop decides what to keep

One successful run does not prove a reusable rule. The application records consented experience with a concise summary, source metadata, and measurements. Repeated corrections or failures can support a candidate procedure, which stays staged outside ordinary recall.

An external evaluator runs baseline and candidate on the same versioned task suite: representative repository changes, expected tests, security cases, stale and irrelevant memories, and cross-scope isolation. Keep final holdouts outside agent write access. Freeze the model, harness, tools, skills, evaluator, and acceptance criteria for each comparison.

CortexState’s gate checks caller-submitted scorecards for no regression in task success, tokens, or latency, zero **reported** safety regressions, and a strict gain in at least one measure. A reviewer approves promotion. The application monitors live results and can roll back the active lesson with revision protection.

The scorecard cannot prove evaluator independence or holdout integrity; callers supply the claims and measurements. Production integrations must protect evaluator credentials and acceptance criteria, repeat noisy evaluations, report uncertainty, and keep agents from changing the final test set.

This is a controlled hill-climb. The system proposes one change and keeps it only when evidence supports the trade-off. Token savings cannot excuse a safety regression, and a test pass cannot excuse degraded task quality. The optimizer cannot change its acceptance tests.

## What production operation requires

For each task, the host should:

1. Authenticate the user and repository, then construct the exact memory scope.
2. Check each rule’s source path and revision against the current checkout.
3. Retrieve only relevant, reviewed context within a defined token budget.
4. Keep memory text separate from trusted instructions and tool permissions.
5. Run the same required checks after every agent revision.
6. Block pull-request creation until all required gates pass.
7. Record a consented, redacted outcome with model, harness, skill, and suite versions.
8. Stage, evaluate, and review candidate lessons before promotion.
9. Monitor outcomes and roll back a promoted lesson when evidence regresses.
10. Apply retention, backup, restore, access-control, and audit policies to the memory store.

CortexState 0.4 is a developer preview. It provides scoped SQLite memory, revisions, expiry and deletion, an authenticated HTTP adapter, Python and TypeScript clients, a review dashboard, and an evidence-linked learning ledger. API keys grant access across their mapped tenant; they do not provide per-user roles. The service is for local or private trusted-backend deployments. Production use needs a TLS gateway, principal-level authorization, quotas, observability, migrations, backup and restore drills, and security review.

The evaluator runs outside CortexState. The dashboard records outcomes and reviews candidates; it does not run agents or security scans. The application connects repository state, CI, evaluation, and approval to the API.

## Where RL fits

Memory hill-climbing can improve agents that call hosted models. RL addresses a separate problem: teaching a **trainable policy** when to investigate, what evidence to retain, and how to write memory for later tasks.

The proposed offline design coordinates two policies. **ACT** solves the current task and may identify useful evidence. **WRITE** proposes a concise memory addition, correction, or removal. A delayed reward compares later-task performance with a matched baseline, minus token, latency, and memory-growth costs. An independent verifier must confirm a reusable discovery before ACT receives an exploration bonus. Safety failures make a rollout ineligible; capability gains cannot offset them.

Training batches must preserve task order and compare equivalent rollouts. A GRPO-style objective can normalize advantages within groups that share a task position and role; a KL penalty can keep updated policies near a frozen reference. The sequence-level writer reward measures whether a memory change helped later tasks. These are trainer-side design choices; CortexState supplies experimental reward calculations, not a policy optimizer.

The training owner curates consented task streams, freezes a baseline, groups comparable ACT and WRITE rollouts, and trains offline. Evaluation uses entire held-out streams, checks capability and safety, then runs a canary with the prior policy available for rollback. The design draws on [CMU AIRe’s RIME work](https://cmu-aire.github.io/RIME/) on actor and memory-writer learning; CortexState’s reward helpers and integration boundary are original.

The repository includes experimental calculations for actor utility, delayed writer improvement, safety eligibility, and group-relative advantages. It has no rollout service, reward model, trainer, data exporter, or weight-update path. CortexState has no measured RL result. Closed model APIs use the shared-memory and evaluation path.

## Learning between coding sessions

A coding session should not become a permanent transcript. At task start, the host binds the tenant, project, agent, and branch scope; checks each rule’s source revision; and retrieves relevant architecture decisions, coding standards, and checks. Persistent scope holds approved project rules. Branch scope isolates temporary context, which the host expires and purges by policy.

During edits, the harness runs tests, lint, security, and permission checks. It returns failures to the agent, which revises and reruns the same gates. Pull-request creation stays blocked until they pass. CortexState provides context and outcome records; the host controls repository access and command execution.

At session end, the application records a consented, redacted outcome with code, model, and harness versions, check results, token use, and latency. It omits credentials and raw transcripts. Candidate lessons link to evidence and stay staged until evaluation and approval.

For promotion, compare baseline and candidate on the same frozen suite. Check task success, safety, tokens, and latency; protect the holdout and acceptance criteria from agent edits. After the gate passes and an authorized reviewer approves, promote the lesson to persistent project scope. Later sessions can retrieve it. Monitor outcomes and roll it back if it causes a regression.

## Outcomes this architecture is designed to support

The goal is to start each task with relevant, current project knowledge. That can reduce repeated searches and prompt context, help prevent known mistakes, and catch test or security failures before review. The host gives the agent a chance to fix failures and blocks the change until required checks pass. Scoped records carry approved project memory across models and harnesses.

These are intended benefits, not guaranteed results. They depend on source freshness, relevant retrieval, sound evaluation, and host-enforced gates. Measure context tokens, time to first edit, completion and check pass rates, security fixes before review, and post-deployment regressions against a baseline. Use the evidence to decide which lessons should carry into later sessions.

Each cycle follows the same path: **retrieve, act, verify, record, evaluate, approve, and observe**. CortexState carries memory and evidence between sessions; the host controls actions, and evaluation determines which lessons help the next task.

