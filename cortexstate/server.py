"""Small authenticated HTTP adapter for local/private deployments."""
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import math
from pathlib import Path
import threading
import time
from urllib.parse import urlsplit

from .memory import Conflict, NotFound, Scope, string
from .learning import LearningLedger

log = logging.getLogger("cortexstate")

PERMISSIONS = {
    "memory:read", "memory:write", "memory:delete", "memory:purge",
    "learning:read", "learning:record", "learning:propose",
    "learning:evaluate", "learning:approve", "learning:rollback",
    "learning:delete", "model:invoke",
}


def _credential_policy(value):
    """Normalize a legacy tenant key or a least-privilege service principal."""
    if isinstance(value, str):
        # Preserve an explicit migration path; it is rejected by default.
        string(value, "tenant")
        return {"tenant": value, "permissions": frozenset({"*"}), "legacy": True}
    if not isinstance(value, dict) or set(value) - {"tenant", "principal", "permissions"}:
        raise ValueError("credential values must be a tenant or a principal policy")
    tenant = string(value.get("tenant"), "tenant")
    principal = string(value.get("principal", "service"), "principal", 256)
    if not principal.isascii() or any(ord(character) < 32 or ord(character) == 127 for character in principal):
        raise ValueError("principal must contain printable ASCII characters only")
    permissions = value.get("permissions")
    if not isinstance(permissions, list) or not permissions:
        raise ValueError("principal credentials require a non-empty permissions list")
    if any(not isinstance(item, str) or item not in PERMISSIONS for item in permissions):
        raise ValueError("principal credentials contain an unknown permission")
    if len(set(permissions)) != len(permissions):
        raise ValueError("principal permissions must be unique")
    return {"tenant": tenant, "principal": principal,
            "permissions": frozenset(permissions), "legacy": False}


def make_server(memory, credentials, host="127.0.0.1", port=8787, *, model=None,
                requests_per_minute=600, burst=60, require_explicit_permissions=True):
    """Create the private HTTP adapter.

    ``credentials`` maps secrets to explicit
    ``{"tenant", "principal", "permissions"}`` policies. Legacy
    ``secret -> tenant`` values require ``require_explicit_permissions=False``
    during a controlled migration. Provision secrets outside this process.
    Rate limits are process-local and apply per API key.

    Keys confer access to every user in their tenant: this API is for trusted
    backend services and the trusted operator console, not end-user clients.
    Explicit permission lists limit operations but do not replace end-user
    authorization in the trusted backend.
    """
    if not isinstance(credentials, dict) or not credentials:
        raise ValueError("at least one API key is required")
    if type(requests_per_minute) is not int or not 1 <= requests_per_minute <= 100000:
        raise ValueError("requests_per_minute must be an integer from 1 to 100000")
    if type(burst) is not int or not 1 <= burst <= 10000:
        raise ValueError("burst must be an integer from 1 to 10000")
    if type(require_explicit_permissions) is not bool:
        raise ValueError("require_explicit_permissions must be a boolean")
    normalized = {}
    for key, policy in credentials.items():
        string(key, "API key", 512)
        if len(key) < 32 or not key.isascii():
            raise ValueError("API keys must be ASCII and at least 32 characters")
        normalized[key] = _credential_policy(policy)
    if require_explicit_permissions and any(policy["legacy"] for policy in normalized.values()):
        raise ValueError("explicit permission policies are required by this deployment")
    credentials = normalized
    learning = LearningLedger(memory)
    rate_lock = threading.Lock()
    rate_buckets = {}
    refill_per_second = requests_per_minute / 60.0

    route_permissions = {
        "/v1/memories/get": "memory:read",
        "/v1/memories/list": "memory:read",
        "/v1/memories/search": "memory:read",
        "/v1/memories/history": "memory:read",
        "/v1/memories/context": "memory:read",
        "/v1/memories/stats": "memory:read",
        "/v1/memories/add": "memory:write",
        "/v1/memories/update": "memory:write",
        "/v1/memories/delete": "memory:delete",
        "/v1/memories/purge-expired": "memory:purge",
        "/v1/memories/propose": "model:invoke",
        "/v1/memories/answer": "model:invoke",
        "/v1/learning/record": "learning:record",
        "/v1/learning/list": "learning:read",
        "/v1/learning/candidates": "learning:read",
        "/v1/learning/propose": "learning:propose",
        "/v1/learning/evaluate": "learning:evaluate",
        "/v1/learning/promote": "learning:approve",
        "/v1/learning/reject": "learning:approve",
        "/v1/learning/rollback": "learning:rollback",
        "/v1/learning/delete-experience": "learning:delete",
    }

    def allow_request(key, now):
        with rate_lock:
            tokens, updated = rate_buckets.get(key, (float(burst), now))
            tokens = min(float(burst), tokens + max(0.0, now - updated) * refill_per_second)
            if tokens < 1.0:
                rate_buckets[key] = (tokens, now)
                return False, max(1, math.ceil((1.0 - tokens) / refill_per_second))
            rate_buckets[key] = (tokens - 1.0, now)
            return True, 0

    class BoundedThreadingHTTPServer(ThreadingHTTPServer):
        # Bounded concurrency prevents untrusted connection floods exhausting threads.
        daemon_threads = True
        request_queue_size = 64
        max_workers = 32

        def __init__(self, *args, **kwargs):
            self._slots = threading.BoundedSemaphore(self.max_workers)
            super().__init__(*args, **kwargs)

        def process_request(self, request, client_address):
            if not self._slots.acquire(blocking=False):
                request.close()
                return
            try:
                super().process_request(request, client_address)
            except Exception:
                self._slots.release()
                raise

        def process_request_thread(self, request, client_address):
            try:
                super().process_request_thread(request, client_address)
            finally:
                self._slots.release()

    class Handler(BaseHTTPRequestHandler):
        server_version = "CortexState/0.4"
        sys_version = ""

        def setup(self):
            super().setup()
            self.connection.settimeout(10)
            self.request_started = time.monotonic()
            self.request_principal = "unauthenticated"

        def log_message(self, *args):
            # URLs, memory content, and credentials are deliberately not logged.
            pass

        def reply(self, status, payload, headers=None):
            body = json.dumps(payload, allow_nan=False).encode()
            requested_route = urlsplit(self.path).path
            route = requested_route if requested_route in route_permissions or requested_route in {"/health", "/ready", "/dashboard", "/dashboard/", "/", "/app.js", "/style.css"} else "other"
            log.info("method=%s route=%s status=%d principal=%r duration_ms=%d",
                     self.command, route, status, self.request_principal,
                     int((time.monotonic() - self.request_started) * 1000))
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            assets = {"/": ("index.html", "text/html; charset=utf-8"),
                      "/dashboard": ("index.html", "text/html; charset=utf-8"),
                      "/dashboard/app.js": ("app.js", "text/javascript; charset=utf-8"),
                      "/dashboard/style.css": ("style.css", "text/css; charset=utf-8")}
            if self.path in assets:
                filename, mime = assets[self.path]
                body = (Path(__file__).parent / "dashboard" / filename).read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("X-Frame-Options", "DENY")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
                self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/health":
                self.reply(200, {"service": "cortexstate", "status": "alive"})
            elif self.path == "/ready":
                try:
                    with memory._db() as db:
                        db.execute("SELECT 1").fetchone()
                    self.reply(200, {"service": "cortexstate", "status": "ready"})
                except Exception:
                    self.reply(503, {"service": "cortexstate", "status": "not_ready"})
            else:
                self.reply(404, {"error": "not_found"})

        def do_POST(self):
            try:
                authorization = self.headers.get("Authorization", "")
                candidate = authorization[7:] if authorization.startswith("Bearer ") else ""
                policy = None
                for key, value in credentials.items():
                    if hmac.compare_digest(candidate.encode(), key.encode()):
                        policy = value
                if policy is None:
                    return self.reply(401, {"error": "unauthorized"})
                self.request_principal = policy.get("principal", "legacy-tenant-key")
                allowed, retry_after = allow_request(candidate, time.monotonic())
                if not allowed:
                    self.reply(429, {"error": "rate_limited", "retry_after_seconds": retry_after},
                               {"Retry-After": str(retry_after)})
                    return
                path = urlsplit(self.path)
                if path.query or path.fragment:
                    raise ValueError("query strings are not supported")
                permission = route_permissions.get(path.path)
                if permission is None:
                    return self.reply(404, {"error": "not_found"})
                if "*" not in policy["permissions"] and permission not in policy["permissions"]:
                    return self.reply(403, {"error": "forbidden"})
                if self.headers.get("Transfer-Encoding"):
                    return self.reply(400, {"error": "chunked bodies are unsupported"})
                lengths = self.headers.get_all("Content-Length", [])
                if len(lengths) != 1:
                    return self.reply(411, {"error": "one Content-Length is required"})
                if not lengths[0].isascii() or not lengths[0].isdigit():
                    return self.reply(400, {"error": "invalid_content_length"})
                size = int(lengths[0])
                if not 0 < size <= 65536:
                    return self.reply(413, {"error": "body must be between 1 and 65536 bytes"})
                if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                    return self.reply(415, {"error": "application/json required"})
                raw = self.rfile.read(size)
                if len(raw) != size:
                    raise ValueError("incomplete body")
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise ValueError("body must be an object")
                supplied_scope = payload.pop("scope", None)
                if not isinstance(supplied_scope, dict) or "tenant" in supplied_scope:
                    raise ValueError("scope requires user; tenant is assigned by the API key")
                scope = Scope(tenant=policy["tenant"], **supplied_scope)
                routes = {"/v1/memories/add": memory.add, "/v1/memories/get": memory.get,
                          "/v1/memories/list": memory.list, "/v1/memories/search": memory.search,
                          "/v1/memories/update": memory.update, "/v1/memories/delete": memory.delete,
                          "/v1/memories/history": memory.history, "/v1/memories/context": memory.context,
                          "/v1/memories/stats": memory.stats,
                          "/v1/memories/purge-expired": memory.purge_expired}
                routes.update({
                    "/v1/learning/record": learning.record,
                    "/v1/learning/list": learning.list,
                    "/v1/learning/candidates": learning.list_candidates,
                    "/v1/learning/propose": learning.propose,
                    "/v1/learning/evaluate": learning.evaluate,
                    "/v1/learning/promote": learning.promote,
                    "/v1/learning/reject": learning.reject,
                    "/v1/learning/rollback": learning.rollback,
                    "/v1/learning/delete-experience": learning.delete_experience,
                })
                if path.path in ('/v1/memories/propose', '/v1/memories/answer'):
                    if model is None or not model.generation_model:
                        return self.reply(503, {'error': 'generation model is not configured'})
                    if path.path.endswith('/propose'):
                        from .extraction import propose
                        if set(payload) != {'messages'}:
                            raise ValueError('propose requires messages only')
                        result = propose(payload['messages'], extractor=model.extract)
                    else:
                        if set(payload) != {'question'}:
                            raise ValueError('answer requires question only')
                        context = memory.context(payload['question'], scope=scope, max_chars=4000)
                        result = model.answer(payload['question'], context)
                    return self.reply(200, {'result': result})
                if path.path not in routes:
                    return self.reply(404, {"error": "not_found"})
                result = routes[path.path](scope=scope, **payload)
                if path.path.endswith('/stats'):
                    result['generation_available'] = bool(model and model.generation_model)
                self.reply(200, {"result": result})
            except Conflict as exc:
                self.reply(409, {"error": str(exc)})
            except NotFound:
                self.reply(404, {"error": "memory not found"})
            except (ValueError, TypeError, OverflowError, RecursionError) as exc:
                self.reply(400, {"error": "invalid_request", "detail": str(exc)[:300]})
            except (TimeoutError, ConnectionError):
                self.close_connection = True
            except Exception:
                log.error("request failed; inspect service configuration (content not logged)")
                self.reply(500, {"error": "internal_error"})

    return BoundedThreadingHTTPServer((host, port), Handler)
