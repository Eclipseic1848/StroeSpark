"""验证真实 API 路径；模型响应仅在测试中使用隔离传输。"""

import io
import json
import tempfile
import unittest
from pathlib import Path

import httpx
from fastapi.testclient import TestClient
from PIL import Image

from storespark.app import create_app
from storespark.settings import Settings


def model_response(**overrides):
    reply = {"reply": "已有信息已整理。", "direction": "突出用户提供的真实门店特色。",
             "title": "门店宣传草稿", "content": "来尝尝【待确认：招牌菜】。",
             "missing_facts": ["招牌菜名称"], "usage": "核实真实信息后使用。", "validation": "小范围收集消费者反馈。"}
    reply.update(overrides)
    return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {
        "content": json.dumps(reply, ensure_ascii=False)}}]})


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.requests = []
        self.response = lambda: model_response()

        def handler(request):
            self.requests.append(json.loads(request.content))
            return self.response()

        self.settings = Settings(data_dir=Path(self.temp.name), provider_api_key="test-provider-key")
        self.transport = httpx.MockTransport(handler)
        self.app = create_app(self.settings, self.transport)
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)

    def task(self, **values):
        response = self.client.post("/api/v1/tasks", json={"title": "蒸饺店宣传", **values})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["id"]

    def turn(self, task_id, action="generate", content="请生成一份宣传文案"):
        return self.client.post(f"/api/v1/tasks/{task_id}/messages", json={"action": action, "content": content})

    def test_complete_flow_and_restart_and_export(self):
        task_id = self.task(brief="江苏蒸饺店希望吸引附近消费者", channel="门店", format="文案")
        upload = self.client.post(f"/api/v1/tasks/{task_id}/materials", files={
            "file": ("menu.md", "菜品名称待核实".encode("utf-8"), "text/markdown")})
        self.assertEqual(upload.status_code, 201)
        self.assertEqual(self.turn(task_id, "direction").json()["status"], "direction")
        generated = self.turn(task_id).json()
        self.assertEqual(generated["status"], "content")
        self.assertEqual(len(generated["artifacts"]), 2)
        artifact_id = generated["artifacts"][-1]["id"]
        edited = self.client.patch(f"/api/v1/tasks/{task_id}/artifacts/{artifact_id}", json={
            "title": "人工核对稿", "content": "已手动修改；价格仍待确认。"})
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(self.turn(task_id, "revise", "请缩短正文").status_code, 200)
        exported = self.client.get(f"/api/v1/tasks/{task_id}/export")
        self.assertEqual(exported.status_code, 200)
        self.assertIn("人工核对稿", exported.text)
        self.assertIn("UTF-8".lower(), exported.headers["content-type"].lower())
        self.assertIn("attachment", exported.headers["content-disposition"])
        with TestClient(create_app(self.settings, self.transport)) as restarted:
            restored = restarted.get(f"/api/v1/tasks/{task_id}").json()
            self.assertEqual(len(restored["materials"]), 1)
            self.assertEqual(restored["messages"][-1]["role"], "assistant")

    def test_all_four_starting_cases(self):
        for explicit in (True, False):
            for has_material in (True, False):
                with self.subTest(explicit=explicit, material=has_material):
                    task_id = self.task(brief="制作门店文案" if explicit else "")
                    if has_material:
                        uploaded = self.client.post(f"/api/v1/tasks/{task_id}/materials", files={
                            "file": ("notes.txt", "门店素材".encode("utf-8"), "text/plain")})
                        self.assertEqual(uploaded.status_code, 201)
                    response = self.turn(task_id, "clarify", "先帮我理清任务")
                    self.assertEqual(response.status_code, 200)

    def test_model_failure_retains_user_input_without_success(self):
        task_id = self.task()
        self.response = lambda: httpx.Response(503, text="sensitive upstream content")
        response = self.turn(task_id, content="不要丢失这段描述")
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("sensitive", response.text)
        task = self.client.get(f"/api/v1/tasks/{task_id}").json()
        self.assertEqual(task["status"], "draft")
        self.assertEqual(task["artifacts"], [])
        self.assertEqual(task["messages"][0]["content"], "不要丢失这段描述")

    def test_invalid_model_schema_does_not_commit_assistant(self):
        task_id = self.task()
        self.response = lambda: model_response(missing_facts="invalid")
        self.assertEqual(self.turn(task_id).status_code, 502)
        task = self.app.state.store.get_task(task_id)
        self.assertEqual(len(task["messages"]), 1)
        self.assertEqual(task["artifacts"], [])

    def test_missing_delivery_sections_fails(self):
        task_id = self.task()
        self.response = lambda: model_response(usage="")
        self.assertEqual(self.turn(task_id).status_code, 502)
        self.assertEqual(self.app.state.store.get_task(task_id)["artifacts"], [])

    def test_no_provider_is_not_fake_success(self):
        settings = Settings(data_dir=Path(self.temp.name) / "unconfigured")
        with TestClient(create_app(settings)) as client:
            task_id = client.post("/api/v1/tasks", json={"title": "零准备"}).json()["id"]
            response = client.post(f"/api/v1/tasks/{task_id}/messages", json={"content": "帮我宣传"})
            self.assertEqual(response.status_code, 503)
            self.assertEqual(len(client.get(f"/api/v1/tasks/{task_id}").json()["messages"]), 1)

    def test_text_and_image_validation(self):
        task_id = self.task()
        url = f"/api/v1/tasks/{task_id}/materials"
        self.assertEqual(self.client.post(url, files={"file": ("x.txt", b"\xff\xfe", "text/plain")}).status_code, 400)
        self.assertEqual(self.client.post(url, files={"file": ("x.png", b"fake", "image/png")}).status_code, 400)
        self.assertEqual(self.client.post(url, files={"file": ("x.exe", b"executable", "text/plain")}).status_code, 400)
        self.assertEqual(self.client.post(url, files={"file": ("x.txt", b"x" * (5 * 1024 * 1024 + 1))}).status_code, 413)
        output = io.BytesIO()
        Image.new("RGB", (20, 20), "white").save(output, format="PNG")
        self.assertEqual(self.client.post(url, files={"file": ("x.png", output.getvalue())}).status_code, 201)
        self.assertEqual(self.turn(task_id, "clarify").status_code, 200)
        parts = self.requests[-1]["messages"][2]["content"]
        self.assertTrue(any(part["type"] == "image_url" for part in parts))

    def test_material_limit_and_task_ownership(self):
        task_id = self.task()
        for index in range(6):
            self.assertEqual(self.client.post(f"/api/v1/tasks/{task_id}/materials", files={
                "file": (f"{index}.txt", b"text")}).status_code, 201)
        self.assertEqual(self.client.post(f"/api/v1/tasks/{task_id}/materials", files={"file": ("7.txt", b"text")}).status_code, 400)
        artifact = self.turn(task_id).json()["artifacts"][0]
        other_id = self.task()
        response = self.client.patch(f"/api/v1/tasks/{other_id}/artifacts/{artifact['id']}", json={"title": "bad", "content": "bad"})
        self.assertEqual(response.status_code, 404)

    def test_provider_api_never_echoes_secret_even_in_validation_errors(self):
        secret = "sensitive-test-secret"
        saved = self.client.put("/api/v1/provider", json={"provider": "deepseek", "base_url": "https://api.deepseek.com",
                                                         "model": "deepseek-flash", "api_key": secret})
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertNotIn(secret, saved.text)
        invalid = self.client.put("/api/v1/provider", json={"provider": "bad", "api_key": secret})
        self.assertEqual(invalid.status_code, 422)
        self.assertNotIn(secret, invalid.text)
        self.assertNotIn(secret.encode("utf-8"), self.app.state.store.path.read_bytes())

    def test_access_control_and_cross_site_requests(self):
        settings = Settings(data_dir=Path(self.temp.name) / "auth", access_token="a" * 32)
        with TestClient(create_app(settings)) as client:
            self.assertEqual(client.get("/api/v1/tasks").status_code, 401)
            headers = {"Authorization": "Bearer " + "a" * 32}
            self.assertEqual(client.get("/api/v1/tasks", headers=headers).status_code, 200)
            headers["Origin"] = "https://evil.example"
            self.assertEqual(client.post("/api/v1/tasks", json={"title": "bad"}, headers=headers).status_code, 403)

    def test_unknown_task_invalid_fields_and_empty_revision(self):
        self.assertEqual(self.client.get("/api/v1/tasks/missing").status_code, 404)
        self.assertEqual(self.client.post("/api/v1/tasks", json={"title": "  "}).status_code, 422)
        self.assertEqual(self.turn(self.task(), "revise", "").status_code, 422)


if __name__ == "__main__":
    unittest.main()
