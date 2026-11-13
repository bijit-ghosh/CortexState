"""Run with python -m evals.run --out work/eval.json; never invent model scores."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import statistics
import tempfile
import time
from cortexstate import Memory, Scope


def run():
    root = Path(__file__).resolve().parents[1]
    fixture_path = root / "evals/cases.json"
    fixture = json.loads(fixture_path.read_text())
    cases, latencies = [], []
    with tempfile.TemporaryDirectory() as directory:
        memory = Memory(Path(directory) / "eval.db")
        scope = Scope("eval", "alice")
        for fact in fixture["memories"]:
            memory.add(fact["text"], scope=scope, metadata={"fixture_key": fact["key"]})
        for case in fixture["queries"]:
            start = time.perf_counter()
            results = memory.search(case["query"], scope=scope, limit=1)
            latencies.append((time.perf_counter()-start)*1000)
            actual = results[0]["metadata"]["fixture_key"] if results else None
            cases.append({**case, "actual": actual, "passed": actual == case["expected"]})
        isolated = memory.search("coffee", scope=Scope("another-tenant", "alice")) == []
    source_files = sorted((root / "cortexstate").glob("*.py")) + [fixture_path, Path(__file__).resolve()]
    hashes = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    return {"status": "measured", "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(), "platform": platform.system(),
            "dataset": "public synthetic development fixture", "memory_count": len(fixture["memories"]),
            "cases": cases, "passed": sum(c["passed"] for c in cases), "total": len(cases),
            "tenant_isolation_passed": isolated, "retrieval_p50_ms": statistics.median(latencies),
            "retrieval_max_ms": max(latencies), "model_calls": 0, "model_tokens": 0,
            "limitations": "Single run, tiny lexical fixture, no held-out data or model comparison; timing is machine-specific.",
            "sha256": hashes}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print(json.dumps({"passed": result["passed"], "total": result["total"], "tenant_isolation_passed": result["tenant_isolation_passed"]}))
    raise SystemExit(0 if result["passed"] == result["total"] and result["tenant_isolation_passed"] else 1)
