"""Framework-neutral reward helpers for optional offline memory-policy RL.

These helpers calculate reward signals; they do not run rollouts or update weights.
"""
from .rewards import actor_reward, group_relative_advantages, writer_improvement_reward

__all__ = ["actor_reward", "group_relative_advantages", "writer_improvement_reward"]
