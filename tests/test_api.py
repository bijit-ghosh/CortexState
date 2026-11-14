import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from cortexstate import Memory
from cortexstate.client import Client
from cortexstate.server import make_server

KEY_A = "a" * 40
KEY_B = "b" * 40


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.memory = Memory(Path(cls.tmp.name) / "api.db")
        cls.server = make_server(cls.memory, {KEY_A: "tenant-a", KEY_B: "tenant-b"}, port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.client = Client(cls.url, KEY_A)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.tmp.cleanup()

    def test_crud_over_http(self):
        scope = {"user": "crud"}
        record = self.client.call("add", scope=scope, text="Coffee preference", idempotency_key="one")
        same = self.client.call("add", scope=scope, text="Coffee preference", idempotency_key="one")
        self.assertEqual(record, same)
        hit = self.client.call("search", scope=scope, query="coffee")
        self.assertEqual(hit[0]["id"], record["id"])
        updated = self.client.call("update", scope=scope, identifier=record["id"], text="Tea preference", expected_revision=1)
        self.assertEqual(updated["revision"], 2)
        self.assertEqual(len(self.client.call("history", scope=scope, identifier=record["id"])), 2)
        self.client.call("delete", scope=scope, identifier=record["id"], expected_revision=2)
        self.assertEqual(self.client.call("list", scope=scope), [])

    def test_tenant_spoof_is_rejected(self):
        with self.assertRaises(HTTPError) as caught:
            self.client.call("list", scope={"user": "alice", "tenant": "tenant-b"})
        self.assertEqual(caught.exception.code, 400)

    def test_tenant_keys_isolate_data(self):
        scope = {"user": "isolation"}
        self.client.call("add", scope=scope, text="private")
        self.assertEqual(Client(self.url, KEY_B).call("list", scope=scope), [])

    def test_bad_key_is_unauthorized(self):
        with self.assertRaises(HTTPError) as caught:
            Client(self.url, "wrong").call("list", scope={"user": "x"})
        self.assertEqual(caught.exception.code, 401)

    def test_stale_revision_returns_conflict(self):
        scope = {"user": "conflict"}
        record = self.client.call("add", scope=scope, text="initial")
        with self.assertRaises(HTTPError) as caught:
            self.client.call("update", scope=scope, identifier=record["id"], text="stale", expected_revision=99)
        self.assertEqual(caught.exception.code, 409)

    def test_missing_body_and_invalid_json(self):
        for body in (b"[]", b"{broken", b'{"scope":{"user":null}}'):
            request = Request(self.url + "/v1/memories/list", body,
                              {"Authorization": "Bearer " + KEY_A, "Content-Type": "application/json"})
            with self.assertRaises(HTTPError) as caught:
                urlopen(request, timeout=5)
            self.assertEqual(caught.exception.code, 400)

    def test_server_requires_strong_key_format(self):
        for credentials in ({}, {"short": "tenant"}):
            with self.assertRaises(ValueError):
                make_server(self.memory, credentials, port=0)

    def test_remote_client_requires_tls(self):
        with self.assertRaises(ValueError):
            Client("http://example.com", KEY_A)

    def test_dashboard_assets_and_headers(self):
        for path in ('/dashboard', '/dashboard/app.js', '/dashboard/style.css'):
            with urlopen(self.url + path, timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy'])
                self.assertNotIn(KEY_A.encode(), response.read())

    def test_named_sdk_methods_and_stats(self):
        scope = {'user': 'sdk'}
        record = self.client.add('sdk supports memory', scope=scope)
        self.assertEqual(self.client.stats(scope=scope)['live'], 1)
        self.assertEqual(self.client.search('memory', scope=scope, ranking='bm25')[0]['id'], record['id'])
        self.assertEqual(self.client.get(record['id'], scope=scope)['revision'], 1)
        self.client.delete(record['id'], scope=scope, expected_revision=1)

    def test_unconfigured_model_fails_explicitly(self):
        with self.assertRaises(HTTPError) as caught:
            self.client.answer('hello', scope={'user':'alice'})
        self.assertEqual(caught.exception.code, 503)


if __name__ == "__main__":
    unittest.main()
