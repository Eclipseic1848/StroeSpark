"""验证模型返回字段在真实 API 路径上的条件约束，不调用外部模型。"""

import json
import tempfile
import unittest
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from storespark.app import create_app
from storespark.settings import Settings


class ModelReplyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.reply = {
            "reply": "测试 fixture：请确认本次宣传用途。",
            "direction": "测试 fixture：仅突出已经提供的信息。",
            "title": "测试 fixture 标题",
            "content": "测试 fixture 正文，真实信息仍待确认。",
            "missing_facts": ["测试 fixture：门店信息"],
            "usage": "测试 fixture：确认信息后使用。",
            "validation": "测试 fixture：只验证软件行为。",
        }

        def handler(request):
            return httpx.Response(200, json={"choices": [{
                "finish_reason": "stop",
                "message": {"content": json.dumps(self.reply, ensure_ascii=False)},
            }]})

        settings = Settings(data_dir=Path(self.directory.name), provider_api_key="test-model-reply-key")
        self.client = TestClient(create_app(settings, httpx.MockTransport(handler)))
        self.addCleanup(self.client.close)

    def task(self):
        response = self.client.post("/api/v1/tasks", json={"title": "测试 fixture：模型结构检查"})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["id"]

    def turn(self, task_id, action):
        return self.client.post(f"/api/v1/tasks/{task_id}/messages", json={
            "action": action, "content": "测试 fixture：保留这次输入",
        })

    def test_empty_title_without_body_allows_clarification_and_direction(self):
        self.reply.update(content="", usage="", validation="")
        for action in ("clarify", "direction"):
            for title in ("", "   "):
                with self.subTest(action=action, title=title):
                    self.reply["title"] = title
                    response = self.turn(self.task(), action)
                    self.assertEqual(response.status_code, 200, response.text)
                    detail = response.json()
                    self.assertEqual(detail["status"], "clarifying" if action == "clarify" else "direction")
                    self.assertEqual([message["role"] for message in detail["messages"]], ["user", "assistant"])
                    self.assertEqual(detail["artifacts"], [])

    def test_body_with_empty_title_fails_and_preserves_input(self):
        for action in ("generate", "revise"):
            for title in ("", "   "):
                with self.subTest(action=action, title=title):
                    task_id = self.task()
                    self.reply["title"] = "测试 fixture 标题"
                    if action == "revise":
                        self.assertEqual(self.turn(task_id, "generate").status_code, 200)
                    before = self.client.get(f"/api/v1/tasks/{task_id}").json()
                    self.reply["title"] = title
                    response = self.turn(task_id, action)
                    self.assertEqual(response.status_code, 502, response.text)
                    after = self.client.get(f"/api/v1/tasks/{task_id}").json()
                    self.assertEqual(after["artifacts"], before["artifacts"])
                    self.assertEqual(after["status"], before["status"])
                    self.assertEqual(len(after["messages"]), len(before["messages"]) + 1)
                    self.assertEqual(after["messages"][-1]["role"], "user")
                    self.assertEqual(after["messages"][-1]["content"], "测试 fixture：保留这次输入")

    def test_body_with_title_still_generates_artifact(self):
        response = self.turn(self.task(), "generate")
        self.assertEqual(response.status_code, 200, response.text)
        artifact = response.json()["artifacts"][0]
        self.assertEqual(artifact["title"], "测试 fixture 标题")
        self.assertIn("## 使用建议", artifact["content"])
        self.assertIn("## 验证建议", artifact["content"])

    def test_other_model_field_constraints_remain_enforced(self):
        valid = self.reply.copy()
        for invalid in (
            {"missing_facts": "测试 fixture：错误类型"},
            {"unexpected": "测试 fixture：未知字段"},
            {"reply": ""},
            {"title": 123},
            {"content": ["测试 fixture：错误类型"]},
        ):
            with self.subTest(invalid=invalid):
                self.reply = {**valid, **invalid}
                task_id = self.task()
                response = self.turn(task_id, "generate")
                self.assertEqual(response.status_code, 502, response.text)
                detail = self.client.get(f"/api/v1/tasks/{task_id}").json()
                self.assertEqual(detail["artifacts"], [])
                self.assertEqual(len(detail["messages"]), 1)
                self.assertEqual(detail["messages"][0]["role"], "user")


if __name__ == "__main__":
    unittest.main()
