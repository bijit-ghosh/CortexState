"""Outcome journal and gated lesson-promotion primitives.

This layer is intentionally model- and harness-neutral. Callers submit concise,
consented outcomes, generate candidate lessons with any model, then pass scores
from an independently managed evaluator before a human-gated promotion.
"""
import hashlib
import json
import math
import time
import uuid

from .memory import Conflict, NotFound, integer, string


OUTCOMES = {"success", "failure", "correction", "blocked", "unsafe"}
CATEGORIES = {"lesson", "procedure", "preference", "constraint", "tool_strategy"}


def _json_object(value, name, max_bytes=16384):
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    try:
        encoded = json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must contain finite JSON values") from exc
    if len(encoded.encode("utf-8")) > max_bytes:
        raise ValueError(f"{name} exceeds {max_bytes} bytes")
    return encoded


class LearningLedger:
    """Store deployment outcomes and promote lessons only after gated evaluation.

    The journal accepts summaries, not raw conversation or credential dumps.
    The caller is responsible for authorization, consent, redaction, and the
    trustworthiness of its evaluator and approver identity.
    """

    def __init__(self, memory):
        self.memory = memory
        self.clock = memory.clock
        with memory._db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS learning_experiences (
                    id TEXT PRIMARY KEY, scope TEXT NOT NULL, task TEXT NOT NULL,
                    outcome TEXT NOT NULL, summary TEXT NOT NULL, source TEXT NOT NULL,
                    measures TEXT NOT NULL, event_key TEXT, fingerprint TEXT NOT NULL,
                    created REAL NOT NULL);
                CREATE UNIQUE INDEX IF NOT EXISTS learning_event_key
                    ON learning_experiences(scope,event_key) WHERE event_key IS NOT NULL;
                CREATE INDEX IF NOT EXISTS learning_by_scope
                    ON learning_experiences(scope,created DESC);
                CREATE TABLE IF NOT EXISTS learning_candidates (
                    id TEXT PRIMARY KEY, scope TEXT NOT NULL, category TEXT NOT NULL,
                    content TEXT NOT NULL, status TEXT NOT NULL,
                    memory_id TEXT, approved_by TEXT, created REAL NOT NULL,
                    updated REAL NOT NULL);
                CREATE INDEX IF NOT EXISTS learning_candidates_by_scope
                    ON learning_candidates(scope,status,created DESC);
                CREATE TABLE IF NOT EXISTS learning_evidence (
                    candidate_id TEXT NOT NULL REFERENCES learning_candidates(id) ON DELETE CASCADE,
                    experience_id TEXT NOT NULL REFERENCES learning_experiences(id) ON DELETE CASCADE,
                    scope TEXT NOT NULL,
                    PRIMARY KEY(candidate_id,experience_id));
                CREATE TABLE IF NOT EXISTS learning_evaluations (
                    id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL
                        REFERENCES learning_candidates(id) ON DELETE CASCADE,
                    scope TEXT NOT NULL, suite TEXT NOT NULL, evaluator TEXT NOT NULL,
                    heldout INTEGER NOT NULL, total INTEGER NOT NULL,
                    baseline_passed INTEGER NOT NULL, candidate_passed INTEGER NOT NULL,
                    safety_regressions INTEGER NOT NULL, baseline_tokens INTEGER NOT NULL,
                    candidate_tokens INTEGER NOT NULL, baseline_latency_ms REAL NOT NULL,
                    candidate_latency_ms REAL NOT NULL, passed INTEGER NOT NULL,
                    created REAL NOT NULL);
                CREATE INDEX IF NOT EXISTS learning_evaluations_by_candidate
                    ON learning_evaluations(scope,candidate_id,created DESC);
            """)

    @staticmethod
    def _scope(scope):
        if not hasattr(scope, "key"):
            raise ValueError("scope must be a CortexState Scope")
        return scope.key()

    def record(self, *, scope, task, outcome, summary, source=None, measures=None,
               consent=False, event_key=None):
        """Append one consented deployment result; content must be redacted summary."""
        if consent is not True:
            raise ValueError("explicit consent is required to record an experience")
        task = string(task, "task", 256)
        summary = string(summary, "summary", 4096)
        if outcome not in OUTCOMES:
            raise ValueError(f"outcome must be one of: {', '.join(sorted(OUTCOMES))}")
        source_json = _json_object(source, "source", 4096)
        measures_json = _json_object(measures, "measures", 4096)
        if event_key is not None:
            string(event_key, "event_key", 256)
        scope_key = self._scope(scope)
        fingerprint = hashlib.sha256(json.dumps(
            [task, outcome, summary, source_json, measures_json], separators=(",", ":")
        ).encode()).hexdigest()
        with self.memory._db() as db:
            db.execute("BEGIN IMMEDIATE")
            if event_key is not None:
                old = db.execute("SELECT * FROM learning_experiences WHERE scope=? AND event_key=?",
                                  (scope_key, event_key)).fetchone()
                if old:
                    if old["fingerprint"] != fingerprint:
                        raise Conflict("experience event_key reused with different content")
                    return self._experience(old)
            identifier = str(uuid.uuid4())
            created = self.clock()
            db.execute("INSERT INTO learning_experiences VALUES(?,?,?,?,?,?,?,?,?,?)",
                       (identifier, scope_key, task, outcome, summary, source_json,
                        measures_json, event_key, fingerprint, created))
            return {"id": identifier, "task": task, "outcome": outcome,
                    "summary": summary, "source": json.loads(source_json),
                    "measures": json.loads(measures_json), "created_at": created,
                    "trust": "untrusted_experience_data"}

    @staticmethod
    def _experience(row):
        return {"id": row["id"], "task": row["task"], "outcome": row["outcome"],
                "summary": row["summary"], "source": json.loads(row["source"]),
                "measures": json.loads(row["measures"]), "created_at": row["created"],
                "trust": "untrusted_experience_data"}

    def list(self, *, scope, limit=100, before=None):
        integer(limit, "limit", 1, 100)
        scope_key = self._scope(scope)
        with self.memory._db() as db:
            if before is None:
                rows = db.execute("SELECT * FROM learning_experiences WHERE scope=? ORDER BY created DESC,id LIMIT ?",
                                  (scope_key, limit)).fetchall()
            else:
                if type(before) not in (int, float) or not math.isfinite(before):
                    raise ValueError("before must be a finite timestamp")
                rows = db.execute("SELECT * FROM learning_experiences WHERE scope=? AND created<? ORDER BY created DESC,id LIMIT ?",
                                  (scope_key, before, limit)).fetchall()
        return [self._experience(row) for row in rows]

    def propose(self, *, scope, evidence_ids, content, category="lesson"):
        """Stage a reusable candidate tied to same-scope deployment evidence."""
        content = string(content, "content", 4096)
        if category not in CATEGORIES:
            raise ValueError(f"category must be one of: {', '.join(sorted(CATEGORIES))}")
        if not isinstance(evidence_ids, list) or not 1 <= len(evidence_ids) <= 20:
            raise ValueError("evidence_ids must contain 1 to 20 experience IDs")
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("evidence_ids must be unique")
        for identifier in evidence_ids:
            string(identifier, "evidence_id", 64)
        scope_key = self._scope(scope)
        with self.memory._db() as db:
            db.execute("BEGIN IMMEDIATE")
            marks = ",".join("?" for _ in evidence_ids)
            rows = db.execute(f"SELECT id FROM learning_experiences WHERE scope=? AND id IN ({marks})",
                              [scope_key, *evidence_ids]).fetchall()
            if len(rows) != len(evidence_ids):
                raise NotFound("one or more evidence experiences are missing from this exact scope")
            identifier, now = str(uuid.uuid4()), self.clock()
            db.execute("INSERT INTO learning_candidates VALUES(?,?,?,?,?,?,?,?,?)",
                       (identifier, scope_key, category, content, "candidate", None, None, now, now))
            db.executemany("INSERT INTO learning_evidence VALUES(?,?,?)",
                           [(identifier, item, scope_key) for item in evidence_ids])
        return self.get_candidate(identifier, scope=scope)

    def get_candidate(self, identifier, *, scope):
        scope_key = self._scope(scope)
        with self.memory._db() as db:
            row = db.execute("SELECT * FROM learning_candidates WHERE scope=? AND id=?",
                             (scope_key, identifier)).fetchone()
            if row is None:
                raise NotFound("learning candidate not found")
            evidence = db.execute("SELECT experience_id FROM learning_evidence WHERE scope=? AND candidate_id=? ORDER BY experience_id",
                                  (scope_key, identifier)).fetchall()
            evaluation = db.execute("SELECT * FROM learning_evaluations WHERE scope=? AND candidate_id=? ORDER BY created DESC LIMIT 1",
                                    (scope_key, identifier)).fetchone()
        scorecard = None
        if evaluation:
            scorecard = {"id": evaluation["id"], "suite": evaluation["suite"],
                         "evaluator": evaluation["evaluator"], "heldout": bool(evaluation["heldout"]),
                         "total": evaluation["total"], "baseline_passed": evaluation["baseline_passed"],
                         "candidate_passed": evaluation["candidate_passed"],
                         "safety_regressions": evaluation["safety_regressions"],
                         "baseline_tokens": evaluation["baseline_tokens"],
                         "candidate_tokens": evaluation["candidate_tokens"],
                         "baseline_latency_ms": evaluation["baseline_latency_ms"],
                         "candidate_latency_ms": evaluation["candidate_latency_ms"],
                         "passed": bool(evaluation["passed"]), "created_at": evaluation["created"]}
        return {"id": row["id"], "category": row["category"], "content": row["content"],
                "status": row["status"], "evidence_ids": [item["experience_id"] for item in evidence],
                "evaluation": scorecard, "memory_id": row["memory_id"],
                "approved_by": row["approved_by"], "created_at": row["created"],
                "updated_at": row["updated"], "trust": "untrusted_candidate_data"}

    def list_candidates(self, *, scope, status=None, limit=100):
        """List staged and promoted lessons for an operator in the exact scope."""
        integer(limit, "limit", 1, 100)
        if status is not None and status not in {
            "candidate", "evaluated", "needs_revision", "promoting", "promoted", "rejected", "rolled_back"
        }:
            raise ValueError("invalid candidate status")
        scope_key = self._scope(scope)
        with self.memory._db() as db:
            if status is None:
                rows = db.execute(
                    "SELECT id FROM learning_candidates WHERE scope=? ORDER BY updated DESC,id LIMIT ?",
                    (scope_key, limit),
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT id FROM learning_candidates WHERE scope=? AND status=? ORDER BY updated DESC,id LIMIT ?",
                    (scope_key, status, limit),
                ).fetchall()
        return [self.get_candidate(row["id"], scope=scope) for row in rows]

    def evaluate(self, identifier, *, scope, suite, evaluator, total,
                 baseline_passed, candidate_passed, safety_regressions,
                 baseline_tokens, candidate_tokens, baseline_latency_ms,
                 candidate_latency_ms, heldout):
        """Record a scorecard; promotion needs a held-out, non-regressing gain."""
        scope_key = self._scope(scope)
        suite = string(suite, "suite", 128)
        evaluator = string(evaluator, "evaluator", 128)
        integer(total, "total", 1, 100000)
        integer(baseline_passed, "baseline_passed", 0, total)
        integer(candidate_passed, "candidate_passed", 0, total)
        integer(safety_regressions, "safety_regressions", 0, 100000)
        integer(baseline_tokens, "baseline_tokens", 0, 1000000000)
        integer(candidate_tokens, "candidate_tokens", 0, 1000000000)
        for name, value in (("baseline_latency_ms", baseline_latency_ms),
                            ("candidate_latency_ms", candidate_latency_ms)):
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be a finite non-negative number")
        if heldout is not True:
            raise ValueError("promotion evaluation must use a protected held-out suite")
        quality_non_regression = candidate_passed >= baseline_passed
        token_non_regression = candidate_tokens <= baseline_tokens
        latency_non_regression = candidate_latency_ms <= baseline_latency_ms
        safety_clean = safety_regressions == 0
        strict_gain = (candidate_passed > baseline_passed or
                       candidate_tokens < baseline_tokens or
                       candidate_latency_ms < baseline_latency_ms)
        passed = (quality_non_regression and token_non_regression and
                  latency_non_regression and safety_clean and strict_gain)
        now, evaluation_id = self.clock(), str(uuid.uuid4())
        with self.memory._db() as db:
            db.execute("BEGIN IMMEDIATE")
            candidate = db.execute("SELECT status FROM learning_candidates WHERE scope=? AND id=?",
                                   (scope_key, identifier)).fetchone()
            if candidate is None:
                raise NotFound("learning candidate not found")
            if candidate["status"] in ("promoting", "promoted", "rejected"):
                raise Conflict("candidate can no longer be evaluated")
            evidence_count = db.execute("SELECT COUNT(*) FROM learning_evidence WHERE scope=? AND candidate_id=?",
                                        (scope_key, identifier)).fetchone()[0]
            if evidence_count == 0:
                raise Conflict("candidate has no retained evidence")
            db.execute("INSERT INTO learning_evaluations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (evaluation_id, identifier, scope_key, suite, evaluator, 1, total,
                        baseline_passed, candidate_passed, safety_regressions,
                        baseline_tokens, candidate_tokens, float(baseline_latency_ms),
                        float(candidate_latency_ms), int(passed), now))
            db.execute("UPDATE learning_candidates SET status=?,updated=? WHERE scope=? AND id=?",
                       ("evaluated" if passed else "needs_revision", now, scope_key, identifier))
        return self.get_candidate(identifier, scope=scope)

    def promote(self, identifier, *, scope, approved_by):
        """Promote only after a passing held-out scorecard and explicit approval."""
        approved_by = string(approved_by, "approved_by", 256)
        scope_key = self._scope(scope)
        with self.memory._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM learning_candidates WHERE scope=? AND id=?",
                             (scope_key, identifier)).fetchone()
            if row is None:
                raise NotFound("learning candidate not found")
            if row["status"] == "promoted":
                return self.get_candidate(identifier, scope=scope)
            evaluation = db.execute("SELECT * FROM learning_evaluations WHERE scope=? AND candidate_id=? ORDER BY created DESC LIMIT 1",
                                    (scope_key, identifier)).fetchone()
            evidence = db.execute("SELECT experience_id FROM learning_evidence WHERE scope=? AND candidate_id=? ORDER BY experience_id",
                                  (scope_key, identifier)).fetchall()
            if evaluation is None or not evaluation["passed"] or not evaluation["heldout"]:
                raise Conflict("candidate needs a passing held-out evaluation before promotion")
            if not evidence:
                raise Conflict("candidate has no retained evidence")
            if row["status"] not in ("evaluated", "promoting"):
                raise Conflict("candidate is not eligible for promotion")
            if row["status"] != "promoting":
                db.execute("UPDATE learning_candidates SET status='promoting',approved_by=?,updated=? WHERE scope=? AND id=?",
                           (approved_by, self.clock(), scope_key, identifier))
        try:
            record = self.memory.add(
                row["content"], scope=scope,
                metadata={"kind": row["category"], "learning_candidate_id": identifier,
                          "experience_ids": [item["experience_id"] for item in evidence],
                          "evaluation_id": evaluation["id"], "evaluator": evaluation["evaluator"],
                          "source": "deployment_outcome_review"},
                idempotency_key=f"learning-candidate:{identifier}")
        except Exception:
            with self.memory._db() as db:
                db.execute("UPDATE learning_candidates SET status='evaluated',updated=? WHERE scope=? AND id=? AND status='promoting'",
                           (self.clock(), scope_key, identifier))
            raise
        with self.memory._db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE learning_candidates SET status='promoted',memory_id=?,approved_by=?,updated=? WHERE scope=? AND id=? AND status='promoting'",
                       (record["id"], approved_by, self.clock(), scope_key, identifier))
        return self.get_candidate(identifier, scope=scope)

    def reject(self, identifier, *, scope, reason):
        reason = string(reason, "reason", 512)
        scope_key = self._scope(scope)
        with self.memory._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status FROM learning_candidates WHERE scope=? AND id=?",
                             (scope_key, identifier)).fetchone()
            if row is None:
                raise NotFound("learning candidate not found")
            if row["status"] in ("promoting", "promoted"):
                raise Conflict("promoted candidate must be removed through memory deletion")
            db.execute("UPDATE learning_candidates SET status='rejected',approved_by=?,updated=? WHERE scope=? AND id=?",
                       (reason, self.clock(), scope_key, identifier))
        return self.get_candidate(identifier, scope=scope)

    def rollback(self, identifier, *, scope, expected_revision):
        """Remove a promoted lesson with revision protection; retain its scorecard."""
        scope_key = self._scope(scope)
        with self.memory._db() as db:
            row = db.execute("SELECT status,memory_id FROM learning_candidates WHERE scope=? AND id=?",
                             (scope_key, identifier)).fetchone()
        if row is None:
            raise NotFound("learning candidate not found")
        if row["status"] != "promoted" or not row["memory_id"]:
            raise Conflict("only a promoted lesson can be rolled back")
        self.memory.delete(row["memory_id"], scope=scope, expected_revision=expected_revision)
        with self.memory._db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE learning_candidates SET status='rolled_back',memory_id=NULL,updated=? WHERE scope=? AND id=? AND status='promoted'",
                       (self.clock(), scope_key, identifier))
        return self.get_candidate(identifier, scope=scope)

    def delete_experience(self, identifier, *, scope):
        """Erase one outcome and every lesson derived from it, including promoted memories."""
        scope_key = self._scope(scope)
        with self.memory._db() as db:
            row = db.execute("SELECT id FROM learning_experiences WHERE scope=? AND id=?",
                             (scope_key, identifier)).fetchone()
            if row is None:
                raise NotFound("experience not found")
            candidates = db.execute("SELECT c.id,c.memory_id FROM learning_candidates c JOIN learning_evidence e ON e.candidate_id=c.id WHERE e.scope=? AND e.experience_id=?",
                                    (scope_key, identifier)).fetchall()
        for candidate in candidates:
            if candidate["memory_id"]:
                try:
                    record = self.memory.get(candidate["memory_id"], scope=scope)
                    self.memory.delete(record["id"], scope=scope, expected_revision=record["revision"])
                except NotFound:
                    pass
        with self.memory._db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM learning_experiences WHERE scope=? AND id=?", (scope_key, identifier))
            for candidate in candidates:
                db.execute("DELETE FROM learning_candidates WHERE scope=? AND id=?", (scope_key, candidate["id"]))
        return {"deleted": True, "experience_id": identifier,
                "derived_lessons_removed": len(candidates)}
