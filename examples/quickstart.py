"""Run from repository root: python -m examples.quickstart"""
from pathlib import Path
import json
import tempfile
from cortexstate import Memory, Scope

with tempfile.TemporaryDirectory() as directory:
    memory = Memory(Path(directory) / "demo.db")
    scope = Scope(tenant="demo", user="alice", agent="assistant")
    fact = memory.add("Alice prefers decaf coffee after noon", scope=scope,
                      metadata={"source": "user-confirmed", "kind": "preference"},
                      idempotency_key="conversation-42-fact-1")
    print(json.dumps(memory.context("coffee", scope=scope, max_chars=500), indent=2))
    memory.update(fact["id"], "Alice now prefers herbal tea after noon", scope=scope, expected_revision=1)
    print(json.dumps(memory.history(fact["id"], scope=scope), indent=2))
