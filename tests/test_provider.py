import copy
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from storespark.provider import MAX_RESPONSE_BYTES, ProviderError, ProviderService


class FakeStore:
    def __init__(self):
        self.values = {}

    def get_setting(self, name):
        return copy.deepcopy(self.values.get(name))

    def set_setting(self, name, value):
        self.values[name] = copy.deepcopy(value)


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings = SimpleNamespace(
            data_dir=Path(self.directory.name),
            provider_name="deepseek",
            provider_base_url="https://api.deepseek.com",
            provider_model="deepseek-flash",
            provider_api_key="test-secret-never-display",
            provider_timeout=5,
        )
        self.store = FakeStore()
        self.service = ProviderService(self.settings, self.store)

    def configured(self, handler):
        return ProviderService(self.settings, self.store, httpx.MockTransport(handler))

    @staticmethod
    def response(content='{"answer":"测试结果"}', finish_reason="stop"):
        return httpx.Response(200, json={
            "choices": [{"finish_reason": finish_reason, "message": {"content": content}}]
        })

    def test_public_config_does_not_return_key(self):
        value = self.service.public_config()
        self.assertTrue(value["api_key_set"])
        self.assertEqual(value["source"], "environment")
        self.assertNotIn(self.settings.provider_api_key, json.dumps(value))
        self.assertNotIn("api_key", value)

    async def test_encrypted_save_survives_restart(self):
        self.service.save_config({})
        saved = self.store.get_setting("provider")
        self.assertNotIn(self.settings.provider_api_key, json.dumps(saved))
        self.assertTrue(saved["api_key_encrypted"])
        original_master = (self.settings.data_dir / "provider.key").read_bytes()
        self.settings.provider_api_key = "different-environment-value"

        def handler(request):
            self.assertEqual(request.headers["authorization"], "Bearer test-secret-never-display")
            return self.response()

        restarted = self.configured(handler)
        self.assertEqual(restarted.public_config()["source"], "saved")
        self.assertEqual(await restarted.complete([{"role": "user", "content": "需求"}]), {"answer": "测试结果"})
        self.assertEqual((self.settings.data_dir / "provider.key").read_bytes(), original_master)

    def test_blank_key_preserves_existing_ciphertext(self):
        self.service.save_config({"api_key": "saved-secret"})
        before = self.store.get_setting("provider")["api_key_encrypted"]
        self.service.save_config({"api_key": ""})
        self.assertEqual(self.store.get_setting("provider")["api_key_encrypted"], before)

    def test_missing_key_and_default_status(self):
        self.settings.provider_api_key = ""
        self.assertFalse(self.service.public_config()["api_key_set"])
        self.assertEqual(self.service.public_config()["source"], "default")

    async def test_missing_key_fails_before_network(self):
        self.settings.provider_api_key = ""
        with self.assertRaises(ProviderError) as raised:
            await self.service.complete([])
        self.assertEqual(raised.exception.status_code, 503)

    def test_invalid_save_preserves_configuration_and_keyfile(self):
        self.service.save_config({})
        before = copy.deepcopy(self.store.values)
        master = (self.settings.data_dir / "provider.key").read_bytes()
        for base_url in ["http://api.deepseek.com", "https://user:password@example.com", "https://example.com?token=secret", "https://example.com#secret", "https://example.com?", "https://example.com#", "https://example.com:bad", "https://example.com:0", "https://example.com\\other", "https://example.com\nother"]:
            with self.subTest(base_url=base_url), self.assertRaises(ProviderError):
                self.service.save_config({"base_url": base_url, "api_key": "new-secret"})
            self.assertEqual(self.store.values, before)
            self.assertEqual((self.settings.data_dir / "provider.key").read_bytes(), master)

    def test_masked_or_invalid_key_cannot_overwrite_saved_key(self):
        self.service.save_config({})
        before = copy.deepcopy(self.store.values)
        for value in ["********", "****last", "abc\r\nheader", "密钥", 123, None]:
            with self.subTest(value=value), self.assertRaises(ProviderError):
                self.service.save_config({"api_key": value})
            self.assertEqual(self.store.values, before)

    def test_configuration_switch_requires_explicit_key(self):
        self.service.save_config({})
        before = copy.deepcopy(self.store.values)
        for change in [{"base_url": "https://another.example/v1"}, {"provider": "openai-compatible"}, {"model": "another-model"}]:
            with self.subTest(change=change), self.assertRaises(ProviderError):
                self.service.save_config(change)
            self.assertEqual(self.store.values, before)
        self.service.save_config({"provider": "openai-compatible", "base_url": "https://another.example/v1", "model": "another-model", "api_key": "new-key"})
        self.assertEqual(self.service.public_config()["base_url"], "https://another.example/v1")

    async def test_missing_master_file_is_not_regenerated(self):
        self.service.save_config({})
        (self.settings.data_dir / "provider.key").unlink()
        before = copy.deepcopy(self.store.values)
        with self.assertRaises(ProviderError) as raised:
            await self.service.complete([])
        self.assertEqual(raised.exception.status_code, 503)
        with self.assertRaises(ProviderError):
            self.service.save_config({"api_key": "replacement-key"})
        self.assertFalse((self.settings.data_dir / "provider.key").exists())
        self.assertEqual(self.store.values, before)

    async def test_corrupted_master_file_is_preserved(self):
        self.service.save_config({})
        master_path = self.settings.data_dir / "provider.key"
        master_path.write_bytes(b"corrupted")
        with self.assertRaises(ProviderError):
            await self.service.complete([])
        self.assertEqual(master_path.read_bytes(), b"corrupted")

    async def test_unreadable_master_file_fails_safely(self):
        self.service.save_config({})
        before = copy.deepcopy(self.store.values)
        with patch.object(Path, "read_bytes", side_effect=PermissionError("sensitive system detail")):
            with self.assertRaises(ProviderError) as raised:
                await self.service.complete([])
        self.assertNotIn("sensitive system detail", str(raised.exception))
        self.assertEqual(self.store.values, before)

    def test_concurrent_first_save_keeps_one_valid_master(self):
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(lambda _: self.service.save_config({"api_key": "concurrent-key"}), range(8)))
        self.assertEqual(self.service._plain_key(self.service._current()), "concurrent-key")

    async def test_deepseek_request_format(self):
        def handler(request):
            self.assertEqual(str(request.url), "https://api.deepseek.com/chat/completions")
            body = json.loads(request.content)
            self.assertEqual(body["model"], "deepseek-flash")
            self.assertEqual(body["response_format"], {"type": "json_object"})
            self.assertEqual(body["thinking"], {"type": "disabled"})
            self.assertEqual(body["messages"], [{"role": "user", "content": "json"}])
            return self.response()
        result = await self.configured(handler).complete([{"role": "user", "content": "json"}])
        self.assertEqual(result, {"answer": "测试结果"})

    async def test_generic_provider_does_not_receive_deepseek_parameters(self):
        self.service.save_config({"provider": "openai-compatible", "base_url": "https://models.example/v1", "api_key": "other-key"})
        def handler(request):
            self.assertNotIn("thinking", json.loads(request.content))
            return self.response()
        await self.configured(handler).complete([])

    async def test_deepseek_parameters_not_sent_to_unknown_domain_or_model(self):
        for fields in [{"base_url": "https://models.example/v1"}, {"model": "custom-model"}]:
            with self.subTest(fields=fields):
                self.settings.provider_base_url = fields.get("base_url", "https://api.deepseek.com")
                self.settings.provider_model = fields.get("model", "deepseek-flash")
                def handler(request):
                    self.assertNotIn("thinking", json.loads(request.content))
                    return self.response()
                await self.configured(handler).complete([])

    async def test_redirect_is_not_followed(self):
        calls = []
        def handler(request):
            calls.append(str(request.url))
            return httpx.Response(307, headers={"location": "https://attacker.example"})
        with self.assertRaises(ProviderError):
            await self.configured(handler).complete([])
        self.assertEqual(calls, ["https://api.deepseek.com/chat/completions"])

    async def test_http_error_body_is_not_exposed(self):
        secret = self.settings.provider_api_key
        def handler(request):
            return httpx.Response(401, text=f"upstream-body {secret}")
        with self.assertRaises(ProviderError) as raised:
            await self.configured(handler).complete([])
        self.assertNotIn(secret, str(raised.exception))
        self.assertNotIn("upstream-body", str(raised.exception))

    async def test_timeout_and_connection_errors_are_safe(self):
        for error, status in [(httpx.ReadTimeout("sensitive detail"), 504), (httpx.ConnectError("sensitive detail"), 502)]:
            with self.subTest(error=type(error).__name__):
                def handler(request):
                    raise error
                with self.assertRaises(ProviderError) as raised:
                    await self.configured(handler).complete([])
                self.assertEqual(raised.exception.status_code, status)
                self.assertNotIn("sensitive detail", str(raised.exception))

    async def test_invalid_response_does_not_become_success(self):
        cases = [
            self.response(""), self.response("   "), self.response("not json"),
            self.response("[]"), self.response("null"), self.response('{"number":NaN}'),
            self.response('{"answer":"partial"}', "length"),
            self.response('{"answer":"tool"}', "tool_calls"),
            httpx.Response(200, json={"choices": []}),
            httpx.Response(200, json=[]),
            httpx.Response(200, text="not-json"),
        ]
        for response in cases:
            with self.subTest(response=response), self.assertRaises(ProviderError):
                await self.configured(lambda request: response).complete([])

    async def test_oversized_response_is_rejected(self):
        def handler(request):
            return httpx.Response(200, content=b"x" * (MAX_RESPONSE_BYTES + 1))
        with self.assertRaises(ProviderError) as raised:
            await self.configured(handler).complete([])
        self.assertIn("大小限制", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
