"""验证上下文来源与输入保留，不用固定模型回复代替语义质量验收。"""

import base64
import copy
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
from storespark.workflow import build_messages


class ContextGroundingTests(unittest.TestCase):
    def setUp(self):
        self.draft = {"title": "测试旧稿", "content": "测试店甲主打家常蒸饺。这是助手旧稿的未核实推测。"}
        self.task = {
            "title": "测试任务",
            "brief": "仅供软件测试，不是真实商家。目标为告知菜名，渠道为微信群。",
            "channel": "微信群",
            "format": "宣传文案",
            "artifacts": [self.draft.copy()],
            "messages": [
                {"role": "user", "content": "我已说明这是测试，目标是告知菜名，渠道是微信群。"},
                {"role": "assistant", "content": "旧助手回复推测：测试店甲主打家常蒸饺。"},
                {"role": "user", "content": "该定位未经我确认，请仅按已提供资料继续。"},
            ],
        }
        output = io.BytesIO()
        Image.new("RGB", (3, 2), (120, 150, 180)).save(output, format="PNG")
        self.image = output.getvalue()
        self.text = "仅供软件测试。店名：测试店甲；菜名：白菜猪肉蒸饺；价格、地址、优惠未提供。"
        self.materials = [
            {"name": "测试资料.txt", "media_type": "text/plain", "content": self.text.encode("utf-8")},
            {"name": "测试图片.png", "media_type": "image/png", "content": self.image},
        ]

    def test_existing_drafts_keep_text_and_are_marked_as_drafts(self):
        for action in ("generate", "revise"):
            with self.subTest(action=action):
                messages = build_messages(self.task, [], action)
                context = json.loads(messages[1]["content"].removeprefix("任务资料："))
                self.assertEqual(context["existing_artifacts"], [{**self.draft, "source": "draft"}])
                self.assertEqual(context["action"], action)

    def test_user_confirmed_positioning_keeps_original_role_and_text(self):
        confirmation = "我明确确认品牌定位就是家常蒸饺，请保留这个定位。"
        self.task["messages"].append({"role": "user", "content": confirmation})
        self.task["brief"] += "用户明确提供的品牌定位：家常蒸饺。"
        messages = build_messages(self.task, [], "generate")
        context = json.loads(messages[1]["content"].removeprefix("任务资料："))
        self.assertEqual(context["brief"], self.task["brief"])
        self.assertEqual(messages[2:], self.task["messages"])
        self.assertEqual(messages[-1], {"role": "user", "content": confirmation})

    def test_known_answers_materials_and_original_inputs_are_not_modified(self):
        original_task = copy.deepcopy(self.task)
        original_materials = copy.deepcopy(self.materials)
        for action in ("generate", "revise"):
            with self.subTest(action=action):
                messages = build_messages(self.task, self.materials, action)
                self.assertEqual([message["role"] for message in messages[:3]], ["system", "user", "user"])
                context = json.loads(messages[1]["content"].removeprefix("任务资料："))
                for name in ("title", "brief", "channel", "format"):
                    self.assertEqual(context[name], self.task[name])
                self.assertEqual(messages[3:], self.task["messages"])
                parts = messages[2]["content"]
                self.assertEqual(parts[0], {"type": "text", "text": "素材 测试资料.txt：\n" + self.text})
                self.assertEqual(parts[1], {"type": "text", "text": "用户提供的图片素材：测试图片.png"})
                image_url = parts[2]["image_url"]["url"]
                self.assertTrue(image_url.startswith("data:image/png;base64,"))
                self.assertEqual(base64.b64decode(image_url.split(",", 1)[1]), self.image)
                self.assertEqual(self.task, original_task)
                self.assertEqual(self.materials, original_materials)

    def test_api_caller_sends_draft_source_and_preserves_records_on_provider_failure(self):
        captured = []

        def handler(request):
            captured.append(json.loads(request.content))
            return httpx.Response(503, json={"error": "测试 fixture：仅用于检查实际请求上下文"})

        with tempfile.TemporaryDirectory() as directory:
            settings = Settings(data_dir=Path(directory), provider_api_key="test-context-key")
            app = create_app(settings, httpx.MockTransport(handler))
            with TestClient(app) as client:
                for action in ("generate", "revise"):
                    with self.subTest(action=action):
                        created = client.post("/api/v1/tasks", json={
                            name: self.task[name] for name in ("title", "brief", "channel", "format")
                        })
                        self.assertEqual(created.status_code, 201, created.text)
                        task_id = created.json()["id"]
                        path = f"/api/v1/tasks/{task_id}"
                        app.state.store.add_message(task_id, "user", self.task["messages"][0]["content"])
                        app.state.store.complete_turn(task_id, self.task["messages"][1]["content"], "content", self.draft)
                        for material in self.materials:
                            uploaded = client.post(path + "/materials", files={"file": (
                                material["name"], material["content"], material["media_type"],
                            )})
                            self.assertEqual(uploaded.status_code, 201, uploaded.text)
                        before = client.get(path).json()
                        current_input = self.task["messages"][2]["content"]
                        response = client.post(path + "/messages", json={"action": action, "content": current_input})
                        self.assertEqual(response.status_code, 502, response.text)
                        sent = captured[-1]["messages"]
                        context = json.loads(sent[1]["content"].removeprefix("任务资料："))
                        self.assertEqual(context["existing_artifacts"], [{**self.draft, "source": "draft"}])
                        self.assertEqual(sent[-1], {"role": "user", "content": current_input})
                        image_url = sent[2]["content"][2]["image_url"]["url"]
                        self.assertEqual(base64.b64decode(image_url.split(",", 1)[1]), self.image)
                        after = client.get(path).json()
                        self.assertEqual(after["artifacts"], before["artifacts"])
                        self.assertEqual(after["materials"], before["materials"])
                        self.assertEqual(after["messages"][:-1], before["messages"])
                        self.assertEqual(after["messages"][-1]["content"], current_input)
                        self.assertEqual(after["messages"][-1]["role"], "user")


if __name__ == "__main__":
    unittest.main()
