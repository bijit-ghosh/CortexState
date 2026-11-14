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
        if operation not in ("add", "get", "list", "search", "update", "delete", "history", "context", "stats", "propose", "answer", "purge-expired"):
            raise ValueError("unknown operation")
        request = Request(f"{self.url}/v1/memories/{operation}",
                          json.dumps({**payload, "scope": scope}, allow_nan=False).encode(),
                          {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        with build_opener(NoRedirect).open(request, timeout=self.timeout) as response:
            return json.load(response)["result"]

    def add(self, text, *, scope, **options):
        return self.call("add", scope=scope, text=text, **options)

    def search(self, query, *, scope, **options):
        return self.call("search", scope=scope, query=query, **options)

    def get(self, identifier, *, scope):
        return self.call("get", scope=scope, identifier=identifier)

    def update(self, identifier, text, *, scope, expected_revision, **options):
        return self.call("update", scope=scope, identifier=identifier, text=text, expected_revision=expected_revision, **options)

    def delete(self, identifier, *, scope, expected_revision):
        return self.call("delete", scope=scope, identifier=identifier, expected_revision=expected_revision)

    def list(self, *, scope, **options):
        return self.call("list", scope=scope, **options)

    def history(self, identifier, *, scope):
        return self.call("history", scope=scope, identifier=identifier)

    def context(self, query, *, scope, **options):
        return self.call("context", scope=scope, query=query, **options)

    def stats(self, *, scope):
        return self.call("stats", scope=scope)

    def purge_expired(self, *, scope):
        return self.call("purge-expired", scope=scope)

    def propose(self, messages, *, scope):
        return self.call('propose', scope=scope, messages=messages)

    def answer(self, question, *, scope):
        return self.call('answer', scope=scope, question=question)
