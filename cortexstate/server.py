"""Small authenticated HTTP adapter for local/private deployments."""
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from pathlib import Path
from socketserver import ThreadingMixIn
import threading
from urllib.parse import urlsplit

from .memory import Conflict, NotFound, Scope, string

log = logging.getLogger("cortexstate")


def make_server(memory, credentials, host="127.0.0.1", port=8787, *, model=None):
    """credentials maps secret -> tenant. Provision secrets outside this process.

    Keys confer access to every user in their tenant: this API is for trusted
    backend services and the trusted operator console, not end-user clients.
    """
    if not isinstance(credentials, dict) or not credentials:
        raise ValueError("at least one API key is required")
    for key, tenant in credentials.items():
        string(key, "API key", 512)
        if len(key) < 32 or not key.isascii():
            raise ValueError("API keys must be ASCII and at least 32 characters")
        string(tenant, "tenant")
    credentials = dict(credentials)

    class BoundedThreadingHTTPServer(ThreadingMixIn, ThreadingHTTPServer):
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
        server_version = "CortexState/0.3"
        sys_version = ""

        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, *args):
            # URLs, memory content, and credentials are deliberately not logged.
            pass

        def reply(self, status, payload):
            body = json.dumps(payload, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
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
                self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/health":
                self.reply(200, {"service": "cortexstate", "status": "alive"})
            else:
                self.reply(404, {"error": "not_found"})

        def do_POST(self):
            try:
                authorization = self.headers.get("Authorization", "")
                candidate = authorization[7:] if authorization.startswith("Bearer ") else ""
                tenant = None
                for key, value in credentials.items():
                    if hmac.compare_digest(candidate.encode(), key.encode()):
                        tenant = value
                if tenant is None:
                    return self.reply(401, {"error": "unauthorized"})
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
                scope = Scope(tenant=tenant, **supplied_scope)
                path = urlsplit(self.path)
                if path.query or path.fragment:
                    raise ValueError("query strings are not supported")
                routes = {"/v1/memories/add": memory.add, "/v1/memories/get": memory.get,
                          "/v1/memories/list": memory.list, "/v1/memories/search": memory.search,
                          "/v1/memories/update": memory.update, "/v1/memories/delete": memory.delete,
                          "/v1/memories/history": memory.history, "/v1/memories/context": memory.context,
                          "/v1/memories/stats": memory.stats,
                          "/v1/memories/purge-expired": memory.purge_expired}
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
