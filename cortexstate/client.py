"""Dependency-free Python HTTP client for trusted backend use."""
import json
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlsplit


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self, url, api_key, *, timeout=15):
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("provide an HTTP(S) service URL without credentials, query, or fragment")
        if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError("remote connections require HTTPS")
        self.url, self.api_key, self.timeout = url.rstrip("/"), api_key, timeout

    def call(self, operation, *, scope, **payload):
        if operation not in ("add", "get", "list", "search", "update", "delete", "history", "context", "purge-expired"):
            raise ValueError("unknown operation")
        request = Request(f"{self.url}/v1/memories/{operation}",
                          json.dumps({**payload, "scope": scope}, allow_nan=False).encode(),
                          {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        with build_opener(NoRedirect).open(request, timeout=self.timeout) as response:
            return json.load(response)["result"]
