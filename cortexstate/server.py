"""Small authenticated HTTP adapter for local/private deployments."""
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from urllib.parse import urlsplit

from .memory import Conflict, NotFound, Scope, string

log = logging.getLogger("cortexstate")


def make_server(memory, credentials, host="127.0.0.1", port=8787):
    """credentials maps secret -> tenant. Provision secrets outside this process.

    Keys confer access to every user in their tenant: this API is for trusted
    backend services, not browsers or untrusted end-user clients.
    """
    if not isinstance(credentials, dict) or not credentials:
        raise ValueError("at least one API key is required")
    for key, tenant in credentials.items():
        string(key, "API key", 512)
        if len(key) < 32 or not key.isascii():
            raise ValueError("API keys must be ASCII and at least 32 characters")
        string(tenant, "tenant")
    credentials = dict(credentials)

    class Handler(BaseHTTPRequestHandler):
        server_version = "CortexState/0.1"
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
            if self.path == "/health":
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
                          "/v1/memories/purge-expired": memory.purge_expired}
                if path.path not in routes:
                    return self.reply(404, {"error": "not_found"})
                result = routes[path.path](scope=scope, **payload)
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

    return ThreadingHTTPServer((host, port), Handler)
