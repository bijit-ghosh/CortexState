"""Safety-gated reward calculations for ACT/WRITE policy training.

The model owner supplies independently measured scores and controls reward scales.
An ineligible result must be excluded from policy updates; it is not a low score.
"""
import math


def _finite(name, value, *, minimum=None, maximum=None):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be at most {maximum}")
    return float(value)


def _scores(name, values):
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError(f"{name} must be a non-empty list or tuple")
    return [_finite(f"{name}[{index}]", value) for index, value in enumerate(values)]


def actor_reward(task_score, discovery_score, *, discovery_verified,
                 safety_pass, beta=0.1, extra_tokens=0, token_cost=0.0,
                 extra_latency_ms=0, latency_cost=0.0):
    """Score ACT task performance plus bounded verified discovery, less cost.

    `discovery_score` is ignored unless a trusted external verifier explicitly
    sets `discovery_verified=True`. Safety failures make the sample ineligible
    for a policy update; callers must not convert them into a numeric trade-off.
    """
    if type(discovery_verified) is not bool or type(safety_pass) is not bool:
        raise ValueError("discovery_verified and safety_pass must be booleans")
    task = _finite("task_score", task_score)
    discovery = _finite("discovery_score", discovery_score, minimum=0, maximum=1)
    weight = _finite("beta", beta, minimum=0)
    tokens = _finite("extra_tokens", extra_tokens, minimum=0)
    per_token = _finite("token_cost", token_cost, minimum=0)
    latency = _finite("extra_latency_ms", extra_latency_ms, minimum=0)
    per_ms = _finite("latency_cost", latency_cost, minimum=0)
    if not safety_pass:
        return {"eligible": False, "reward": None, "reason": "safety_constraint_failed"}
    accepted_discovery = discovery if discovery_verified else 0.0
    resource_cost = tokens * per_token + latency * per_ms
    return {"eligible": True,
            "reward": task + weight * accepted_discovery - resource_cost,
            "task_reward": task,
            "verified_discovery_reward": weight * accepted_discovery,
            "resource_cost": resource_cost}


def writer_improvement_reward(previous_task_scores, future_task_scores, *,
                              safety_pass, extra_tokens=0, token_cost=0.0,
                              extra_latency_ms=0, latency_cost=0.0,
                              memory_growth_bytes=0, memory_cost=0.0):
    """Credit a WRITE from measured later-task gain, less added resource cost.

    The caller selects comparable before/after windows from one task stream.
    This difference is an attribution proxy, not a causal estimate; use matched
    rollouts and held-out streams in the training system.
    """
    if type(safety_pass) is not bool:
        raise ValueError("safety_pass must be a boolean")
    before = _scores("previous_task_scores", previous_task_scores)
    after = _scores("future_task_scores", future_task_scores)
    tokens = _finite("extra_tokens", extra_tokens, minimum=0)
    per_token = _finite("token_cost", token_cost, minimum=0)
    latency = _finite("extra_latency_ms", extra_latency_ms, minimum=0)
    per_ms = _finite("latency_cost", latency_cost, minimum=0)
    growth = _finite("memory_growth_bytes", memory_growth_bytes, minimum=0)
    per_byte = _finite("memory_cost", memory_cost, minimum=0)
    if not safety_pass:
        return {"eligible": False, "reward": None, "reason": "safety_constraint_failed"}
    before_mean = sum(before) / len(before)
    after_mean = sum(after) / len(after)
    gain = after_mean - before_mean
    cost = tokens * per_token + latency * per_ms + growth * per_byte
    return {"eligible": True, "reward": gain - cost,
            "previous_mean": before_mean, "future_mean": after_mean,
            "measured_gain": gain, "resource_cost": cost}


def group_relative_advantages(rewards, *, epsilon=1e-8):
    """Return population-standardized advantages for one comparable rollout group.

    Group only rollouts for the same task stream position and role (ACT or
    WRITE). A zero-variance or single-item group receives zero advantages.
    """
    values = _scores("rewards", rewards)
    eps = _finite("epsilon", epsilon, minimum=0)
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    deviation = math.sqrt(variance)
    if deviation <= eps:
        return [0.0] * len(values)
    return [(value - mean) / deviation for value in values]
