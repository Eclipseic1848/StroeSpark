"""验证模型地址与授权头在信任边界失败时不覆盖数据或泄漏凭据。"""

import json
import tempfile
import unittest
from pathlib import Path

import httpx

from storespark.app import create_app
from storespark.settings import Settings


class InputBoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.requests = []

        def model_response(request):
            self.requests.append(request)
            result = {
                "reply": "测试回复", "direction": "", "title": "测试文案", "content": "测试内容",
                "missing_facts": [], "usage": "测试使用建议", "validation": "测试验证建议",
            }
            return httpx.Response(200, json={"choices": [{
                "finish_reason": "stop", "message": {"content": json.dumps(result, ensure_ascii=False)},
            }]})

        self.transport = httpx.MockTransport(model_response)
        self.settings = Settings(data_dir=Path(self.temp.name), provider_api_key="fixture-existing-key")
        self.app = create_app(self.settings, transport=self.transport)
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app, raise_app_exceptions=False), base_url="http://testserver")

    async def asyncTearDown(self):
        await self.client.aclose()
        self.temp.cleanup()

    async def test_invalid_idna_cannot_replace_existing_configuration_or_key(self):
        values = {"provider": "deepseek", "base_url": "https://api.deepseek.com", "model": "deepseek-flash"}
        self.assertEqual((await self.client.put("/api/v1/provider", json=values)).status_code, 200)
        before = self.app.state.store.get_setting("provider")
        master = (self.settings.data_dir / "provider.key").read_bytes()
        response = await self.client.put("/api/v1/provider", json={
            "provider": "openai-compatible", "base_url": "https://☃.com", "model": "fixture-model",
            "api_key": "fixture-replacement-key",
        })
        self.assertEqual(response.status_code, 422, response.text)
        self.assertIn("接口地址", response.json()["detail"])
        self.assertNotIn("fixture-replacement-key", response.text)
        self.assertEqual(self.app.state.store.get_setting("provider"), before)
        self.assertEqual((self.settings.data_dir / "provider.key").read_bytes(), master)
        self.assertEqual(self.requests, [])

    async def test_invalid_environment_url_fails_readably_and_preserves_input(self):
        settings = Settings(data_dir=Path(self.temp.name) / "invalid-env",
                            provider_base_url="https://☃.com", provider_api_key="fixture-environment-key")
        app = create_app(settings, transport=self.transport)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://testserver",
        ) as client:
            task = (await client.post("/api/v1/tasks", json={"title": "地址错误时保留输入"})).json()
            path = f"/api/v1/tasks/{task['id']}"
            response = await client.post(path + "/messages", json={"content": "请保留这段描述"})
            self.assertEqual(response.status_code, 422, response.text)
            self.assertIn("接口地址", response.json()["detail"])
            self.assertNotIn("fixture-environment-key", response.text)
            restored = (await client.get(path)).json()
            self.assertEqual(restored["messages"][0]["content"], "请保留这段描述")
            self.assertEqual(restored["artifacts"], [])
            self.assertEqual(restored["status"], "draft")
            self.assertEqual(self.requests, [])

    async def test_valid_internationalized_domains_can_save_and_generate(self):
        for address, expected in [
            ("https://例子.测试/v1", "https://xn--fsqu00a.xn--0zwm56d/v1"),
            ("https://bücher.example/v1", "https://xn--bcher-kva.example/v1"),
        ]:
            with self.subTest(address=address):
                saved = await self.client.put("/api/v1/provider", json={
                    "provider": "openai-compatible", "base_url": address, "model": "fixture-model",
                    "api_key": "fixture-idna-key",
                })
                self.assertEqual(saved.status_code, 200, saved.text)
                self.assertEqual(saved.json()["base_url"], address)
                task = (await self.client.post("/api/v1/tasks", json={"title": "国际化域名"})).json()
                response = await self.client.post(f"/api/v1/tasks/{task['id']}/messages", json={
                    "action": "generate", "content": "请生成测试文案",
                })
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(str(self.requests[-1].url), expected + "/chat/completions")

    async def test_non_ascii_authorization_bytes_are_rejected_without_server_error(self):
        token = "fixture-access-token-at-least-24-characters"
        app = create_app(Settings(data_dir=Path(self.temp.name) / "auth", access_token=token))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://testserver",
        ) as client:
            for supplied in [b"Bearer \xff", b"Bearer \xe4\xb8\xad\xe6\x96\x87"]:
                with self.subTest(supplied=supplied):
                    response = await client.post("/api/v1/tasks", json={"title": "不得创建"},
                                                 headers={b"authorization": supplied})
                    self.assertEqual(response.status_code, 401, response.text)
                    self.assertIn("访问令牌无效", response.json()["detail"])
                    self.assertNotIn(token, response.text)
            accepted = await client.get("/api/v1/tasks", headers={"Authorization": "Bearer " + token})
            self.assertEqual(accepted.status_code, 200, accepted.text)
            self.assertEqual(accepted.json(), [])


if __name__ == "__main__":
    unittest.main()
