"""Original CortexState memory engine. No model calls or implicit extraction."""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import math
import re
import sqlite3
import time
import uuid


class Conflict(Exception):
    """A stale revision or reused idempotency key conflicts with current state."""


class NotFound(Exception):
    """No visible memory exists in this exact scope."""


def string(value, name, maximum=256):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{name} must be a nonempty string of at most {maximum} characters")
    return value


def integer(value, name, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer between {minimum} and {maximum}")
    return value


@dataclass(frozen=True)
class Scope:
    tenant: str
    user: str
    agent: str = "default"
    session: str = "persistent"

    def __post_init__(self):
        for name in ("tenant", "user", "agent", "session"):
            string(getattr(self, name), name)

    def key(self):
        return json.dumps([self.tenant, self.user, self.agent, self.session], separators=(",", ":"))


def tokens(text):
    return re.findall(r"\w+", text.casefold(), flags=re.UNICODE)


class Memory:
    """SQLite-backed facts. Each call must supply an exact Scope.

    embedder is an optional callable str -> sequence[float]; embedding_id must
    identify its model/version. It is invoked locally by this library, never
    inferred from an API key. Changing embedding_id on a populated store fails.
    """

    def __init__(self, path="cortexstate.db", *, embedder=None, embedding_id=None, clock=time.time):
        if (embedder is None) != (embedding_id is None):
            raise ValueError("embedder and embedding_id must be supplied together")
        self.path, self.embedder, self.clock = str(path), embedder, clock
        if self.path == ":memory:":
            raise ValueError("Use a file path; each operation uses its own connection")
        self.embedding_id = string(embedding_id, "embedding_id") if embedder else "none"
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY, scope TEXT NOT NULL, text TEXT NOT NULL,
                    metadata TEXT NOT NULL, vector TEXT, revision INTEGER NOT NULL,
                    created REAL NOT NULL, updated REAL NOT NULL, expires REAL);
                CREATE INDEX IF NOT EXISTS by_scope ON memories(scope);
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL,
                    scope TEXT NOT NULL, revision INTEGER NOT NULL, action TEXT NOT NULL,
                    at REAL NOT NULL, snapshot TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS by_memory ON events(scope,id);
                CREATE TABLE IF NOT EXISTS requests (
                    scope TEXT NOT NULL, key TEXT NOT NULL, fingerprint TEXT NOT NULL,
                    response TEXT NOT NULL, memory_id TEXT NOT NULL,
                    PRIMARY KEY(scope,key));
            ''')
            db.execute("INSERT OR IGNORE INTO config VALUES ('embedding_id', ?)", (self.embedding_id,))
            configured = db.execute("SELECT value FROM config WHERE key='embedding_id'").fetchone()[0]
            if configured != self.embedding_id:
                raise ValueError("Store embedding_id differs; use the original embedder or a new database")

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def _vector(self, text):
        if self.embedder is None:
            return None
        raw = self.embedder(text)
        if not isinstance(raw, (list, tuple)) or not 1 <= len(raw) <= 8192:
            raise ValueError("embedder must return a nonempty list or tuple, max 8192 dimensions")
        if any(type(x) not in (int, float) for x in raw):
            raise ValueError("embedding values must be numbers")
        vector = [float(x) for x in raw]
        norm = math.hypot(*vector)
        if not math.isfinite(norm) or norm == 0:
            raise ValueError("embedding must have a finite nonzero norm")
        return [x / norm for x in vector]

    @staticmethod
    def _metadata(value):
        value = {} if value is None else value
        if not isinstance(value, dict):
            raise ValueError("metadata must be a JSON object")
        try:
            encoded = json.dumps(value, sort_keys=True, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("metadata must contain finite JSON values") from exc
        if len(encoded.encode()) > 16384:
            raise ValueError("metadata exceeds 16 KiB")
        return encoded

    def _dimensions(self, db, vector):
        if vector is not None:
            dim = str(len(vector))
            db.execute("INSERT OR IGNORE INTO config VALUES ('dimensions', ?)", (dim,))
            if db.execute("SELECT value FROM config WHERE key='dimensions'").fetchone()[0] != dim:
                raise ValueError("embedding dimension mismatch")

    @staticmethod
    def _record(row):
        return {"id": row["id"], "text": row["text"], "metadata": json.loads(row["metadata"]),
                "revision": row["revision"], "created_at": row["created"],
                "updated_at": row["updated"], "expires_at": row["expires"]}

    def _event(self, db, scope, record, action):
        db.execute("INSERT INTO events(id,scope,revision,action,at,snapshot) VALUES(?,?,?,?,?,?)",
                   (record["id"], scope.key(), record["revision"], action, self.clock(), json.dumps(record)))

    def add(self, text, *, scope, metadata=None, ttl_seconds=None, idempotency_key=None):
        text = string(text, "text", 32768)
        meta = self._metadata(metadata)
        if ttl_seconds is not None:
            integer(ttl_seconds, "ttl_seconds", 1, 315360000)
        if idempotency_key is not None:
            string(idempotency_key, "idempotency_key")
        fingerprint = hashlib.sha256(json.dumps([text, meta, ttl_seconds]).encode()).hexdigest()
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            if idempotency_key is not None:
                old = db.execute("SELECT * FROM requests WHERE scope=? AND key=?",
                                 (scope.key(), idempotency_key)).fetchone()
                if old:
                    if old["fingerprint"] != fingerprint:
                        raise Conflict("idempotency key was used with a different payload")
                    response = json.loads(old["response"])
                    if response["expires_at"] is not None and response["expires_at"] <= self.clock():
                        raise Conflict("idempotency result expired; purge it before retrying")
                    return response
            vector = self._vector(text)
            self._dimensions(db, vector)
            now = self.clock()
            identifier = str(uuid.uuid4())
            db.execute("INSERT INTO memories VALUES(?,?,?,?,?,?,?,?,?)",
                       (identifier, scope.key(), text, meta, json.dumps(vector) if vector else None,
                        1, now, now, now + ttl_seconds if ttl_seconds else None))
            record = self._record(db.execute("SELECT * FROM memories WHERE id=?", (identifier,)).fetchone())
            self._event(db, scope, record, "add")
            if idempotency_key is not None:
                db.execute("INSERT INTO requests VALUES(?,?,?,?,?)",
                           (scope.key(), idempotency_key, fingerprint, json.dumps(record), identifier))
            return record

    def _visible(self, db, identifier, scope):
        row = db.execute("SELECT * FROM memories WHERE id=? AND scope=? AND (expires IS NULL OR expires>?)",
                         (identifier, scope.key(), self.clock())).fetchone()
        if row is None:
            raise NotFound("memory not found")
        return row

    def get(self, identifier, *, scope):
        with self._db() as db:
            return self._record(self._visible(db, identifier, scope))

    def list(self, *, scope, limit=100, offset=0):
        integer(limit, "limit", 1, 1000)
        integer(offset, "offset", 0, 100000000)
        with self._db() as db:
            rows = db.execute("SELECT * FROM memories WHERE scope=? AND (expires IS NULL OR expires>?) ORDER BY created,id LIMIT ? OFFSET ?",
                              (scope.key(), self.clock(), limit, offset)).fetchall()
            return [self._record(row) for row in rows]

    def update(self, identifier, text, *, scope, expected_revision, metadata=None):
        string(text, "text", 32768)
        integer(expected_revision, "expected_revision", 1, 2147483647)
        meta = self._metadata(metadata) if metadata is not None else None
        vector = self._vector(text)
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            old = self._visible(db, identifier, scope)
            if old["revision"] != expected_revision:
                raise Conflict("stale revision; fetch the latest memory before editing")
            self._dimensions(db, vector)
            db.execute("UPDATE memories SET text=?,metadata=?,vector=?,revision=revision+1,updated=? WHERE id=?",
                       (text, meta if meta is not None else old["metadata"], json.dumps(vector) if vector else None,
                        self.clock(), identifier))
            record = self._record(self._visible(db, identifier, scope))
            self._event(db, scope, record, "update")
            return record

    def history(self, identifier, *, scope):
        with self._db() as db:
            rows = db.execute("SELECT action,at,snapshot FROM events WHERE scope=? AND id=? ORDER BY seq",
                              (scope.key(), identifier)).fetchall()
            if not rows:
                raise NotFound("memory not found")
            return [{"action": r["action"], "at": r["at"], "memory": json.loads(r["snapshot"])} for r in rows]

    def delete(self, identifier, *, scope, expected_revision):
        """Hard-delete current row, revisions, and replay payloads in one transaction.

        Database pages/backups are not securely erased by this operation.
        """
        integer(expected_revision, "expected_revision", 1, 2147483647)
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM memories WHERE id=? AND scope=?", (identifier, scope.key())).fetchone()
            if row is None:
                raise NotFound("memory not found")
            if row["revision"] != expected_revision:
                raise Conflict("stale revision")
            self._erase(db, identifier, scope.key())

    @staticmethod
    def _erase(db, identifier, scope_key):
        db.execute("DELETE FROM memories WHERE id=? AND scope=?", (identifier, scope_key))
        db.execute("DELETE FROM events WHERE id=? AND scope=?", (identifier, scope_key))
        db.execute("DELETE FROM requests WHERE memory_id=? AND scope=?", (identifier, scope_key))

    def purge_expired(self, *, scope):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute("SELECT id FROM memories WHERE scope=? AND expires<=?", (scope.key(), self.clock())).fetchall()
            for row in rows:
                self._erase(db, row["id"], scope.key())
            return len(rows)

    def search(self, query, *, scope, limit=10, metadata=None, semantic_weight=0.5):
        string(query, "query", 8192)
        integer(limit, "limit", 1, 100)
        if type(semantic_weight) not in (int, float) or not 0 <= semantic_weight <= 1:
            raise ValueError("semantic_weight must be between 0 and 1")
        filters = json.loads(self._metadata(metadata))
        query_tokens = set(tokens(query))
        vector = self._vector(query)
        with self._db() as db:
            rows = db.execute("SELECT * FROM memories WHERE scope=? AND (expires IS NULL OR expires>?)",
                              (scope.key(), self.clock())).fetchall()
        scored = []
        for row in rows:
            record = self._record(row)
            if any(k not in record["metadata"] or record["metadata"][k] != v for k, v in filters.items()):
                continue
            words = set(tokens(row["text"]))
            lexical = len(query_tokens & words) / max(1, len(query_tokens))
            semantic = 0.0
            if vector is not None:
                stored = json.loads(row["vector"])
                if len(stored) != len(vector):
                    raise ValueError("query embedding dimension mismatch")
                semantic = max(0.0, sum(a*b for a, b in zip(stored, vector)))
            score = ((1-semantic_weight)*lexical + semantic_weight*semantic) if vector else lexical
            if score > 0:
                scored.append({**record, "score": score, "signals": {"lexical": lexical, "semantic": semantic}})
        return sorted(scored, key=lambda r: (-r["score"], -r["updated_at"], r["id"]))[:limit]

    def context(self, query, *, scope, max_chars=4000, limit=20, metadata=None):
        """Return budgeted JSON data, never instructions. Character budget is exact."""
        integer(max_chars, "max_chars", 2, 1000000)
        selected = []
        for record in self.search(query, scope=scope, limit=limit, metadata=metadata):
            item = {"id": record["id"], "revision": record["revision"], "text": record["text"]}
            candidate = json.dumps(selected + [item], ensure_ascii=False)
            if len(candidate) <= max_chars:
                selected.append(item)
        content = json.dumps(selected, ensure_ascii=False)
        return {"data": content, "characters": len(content), "memory_ids": [r["id"] for r in selected],
                "trust": "untrusted_memory_data"}
