"""Synthetic, offline support lifecycle. Run: python -m examples.support_workflow"""
import json
from pathlib import Path
import tempfile

from cortexstate import Memory, Scope, NotFound


def main():
    with tempfile.TemporaryDirectory() as directory:
        memory = Memory(Path(directory) / "support.db")
        scope = Scope("demo-support", "customer-42", "support")
        payload = {"scope": scope, "metadata": {"source": "customer-confirmed", "ticket": "demo-17"},
                   "idempotency_key": "demo-17-preference"}
        fact = memory.add("Customer prefers email for support updates", **payload)
        replay = memory.add("Customer prefers email for support updates", **payload)
        assert replay["id"] == fact["id"], "Retry created an unexpected duplicate"

        context = memory.context("support updates", scope=scope, max_chars=500)
        assert fact["id"] in context["memory_ids"]
        other_customer = Scope("demo-support", "customer-99", "support")
        assert memory.search("support", scope=other_customer) == []

        updated = memory.update(fact["id"], "Customer now prefers phone calls for support updates",
                                scope=scope, expected_revision=fact["revision"])
        history = memory.history(updated["id"], scope=scope)
        assert len(history) == 2 and updated["revision"] == 2
        memory.delete(updated["id"], scope=scope, expected_revision=updated["revision"])
        assert memory.list(scope=scope) == []
        try:
            memory.history(updated["id"], scope=scope)
        except NotFound:
            pass
        else:
            raise AssertionError("History was retained after deletion")

        print(json.dumps({"example": "CortexState support workflow", "retry_deduplicated": True,
                          "context_before_correction": json.loads(context["data"]),
                          "customer_isolation": "passed", "revision_after_correction": 2,
                          "history_entries_before_delete": len(history), "forgetting": "passed",
                          "model_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
