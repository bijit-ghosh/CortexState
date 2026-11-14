# Optional reinforcement learning for memory writing

## Decision

RL belongs in an **optional offline policy-training lane**, not in CortexState's runtime memory service. The default product stays usable with closed APIs and any model, harness, or skill: those systems record outcomes and retrieve approved lessons through the shared API. RL is useful only when an operator has a trainable model, ordered related-task streams, and reliable outcome signals—and wants to teach the policy what to discover, retain, revise, and reuse.

This follows the problem framing in CMU AIRe's [RIME technical post and repository](https://github.com/cmu-aire/RIME): actor performance and memory-writing quality depend on each other. CortexState uses that as a research reference for an integration direction; it does not copy RIME code, figures, or benchmarks. The proposed integration below is CortexState's own boundary and safeguards.

## The RL we propose

Train a shared or coordinated **actor–writer policy** with grouped relative policy optimization (GRPO-style) over sequences of related tasks. Keep a KL/reference-policy constraint to limit drift:

1. **ACT:** the agent solves task `t` using the current scoped memory and emits a trajectory plus concise outcome evidence.
2. **WRITE:** a memory-writer policy proposes additions, corrections, or removals from that evidence. It never writes directly to production memory.
3. **Score delayed utility:** evaluate whether the revised memory improves the next `K` related tasks against a matched baseline. Reward the writer for downstream improvement, not length or amount of text changed.
4. **Reward useful discovery:** give the actor a small bounded bonus only when an independent verifier confirms a novel, reusable fact or procedure that the writer preserves. Cap this bonus and keep safety as a hard constraint.
5. **Optimize offline:** use the model owner's RL trainer on consented training streams. Normalize ACT and WRITE advantages among comparable rollouts at the same task position. Keep token, latency, and memory-size costs to limit drift and verbosity.
6. **Gate deployment:** compare the updated policy with the frozen baseline on protected, held-out task streams. Require no safety or capability regression and a measured gain in future-task performance, memory utility, or resource use. Deploy behind a canary; keep the prior model and memory policy available for rollback.

The writer reward can be expressed as a windowed change in verified task reward:

```text
writer_reward(t) = mean(task_score[t+1 : t+K])
                 - mean(task_score[t-K+1 : t])
                 - λ_tokens * extra_tokens
                 - λ_latency * extra_latency
                 - λ_memory * memory_growth
```

The actor reward combines current task quality with bounded, verifier-confirmed reusable discovery. Safety violations are constraints that fail the run; do not trade them for task reward. The windowed change is only an attribution proxy: other tasks and later writes also affect the result, so compare matched rollouts and report variance. Never reward “exploration” based only on activity, novelty of wording, or the model's own claim that a discovery is useful.

## Why add this lane

The current CortexState loop can collect evidence, compare a candidate with a baseline, reject regressions, and promote a reviewed lesson. That is enough for practical memory updates and deterministic hill-climbing. It does not train a model to seek information that will help later tasks, decide which experience is worth keeping, or improve its own memory-writing judgment. Sequential RL can train those actor and writer decisions together when the deployment exposes trainable weights and credible rewards.

RL is **not required** to make CortexState cross-model or cross-harness. A hosted model whose weights cannot be updated continues to use the same external memory API, evaluations, and approved lessons. No online policy update is made from an individual user's feedback.

## Data and evaluation contract

An RL adapter should consume versioned, consented streams of related tasks. The stream must give early experience a real chance to help later tasks; isolated tasks or streams that are too short do not train memory use effectively. A practical training curriculum can move from easier discovery tasks toward tasks that benefit from earlier lessons. Holdout streams should come from unseen environments and should include longer sequences to test whether gains persist beyond training length. Each stream should contain:

| Field | Purpose |
| --- | --- |
| `stream_id`, `position`, `task_family` | Preserve task order and group related work |
| `task_input_ref`, `actor_version`, `harness_version`, `skill_versions` | Reproduce what the actor saw and which policy stack ran |
| `memory_before`, `memory_candidate` | Compare the exact state used and proposed by WRITE |
| `task_score`, `safety_verdict`, `tokens`, `latency_ms` | Build reward and hard constraints from measured outcomes |
| `discovery_evidence`, `verifier_id`, `consent_ref` | Audit why an exploration bonus or training example was accepted |

Store sensitive task payloads outside the general memory ledger and reference them by access-controlled IDs. CortexState's current experience API is **not yet an RL trajectory format**; a future adapter must add these sequence and reward fields or export them from the host harness. Promotion still goes through the existing candidate, held-out evaluation, approval, and rollback boundary.

Evaluate on whole held-out streams, not randomly split individual tasks from the same repository or environment. Report total task capability and memory-attributable gain against a stateless baseline separately; a strong agent can solve tasks well while learning little from its own history. Also report safety regressions, tokens, latency, variance, memory growth, and forgetting on earlier skills. Keep evaluator and final-suite credentials outside agent access. Run multiple seeds and compare with a stateless baseline, a prompted ACT–WRITE baseline, and the frozen prior policy. Do not import external benchmark numbers as CortexState results.

## Implementation status

**Architecture and training contract only.** CortexState does not ship a trainer, reward model, rollout worker, RL dependency, automatic data exporter, or weight-update path. The existing API and dashboard continue to handle deployment outcomes and reviewed memory lessons. An RL adapter is a separate future package for a chosen trainable model stack; it must emit candidate lessons and scorecards that pass CortexState's existing deployment gate.

## Reference

- CMU AIRe, [RIME: How to Train Memory Writing for Continual Learning](https://cmu-aire.github.io/RIME/) and its [source repository](https://github.com/cmu-aire/RIME). Consulted for the actor/writer co-training, delayed improvement signal, useful-discovery reward, and sequential task-stream framing. CortexState's design, implementation, examples, and diagrams are original.
