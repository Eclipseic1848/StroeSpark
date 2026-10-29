"""独立 Uvicorn 进程的 TCP、重启持久化与并发回归检查。"""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
SERVER_SCRIPT = Path(__file__).with_name("runtime_server.py")
WAIT_MESSAGE = "测试 fixture：等待并发检查"


class RuntimeServer:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.process = None
        self.log = None
        self.base_url = ""

    def start(self):
        if self.process is not None:
            raise RuntimeError("测试服务已经启动")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.data_dir / "runtime-server.log"
        self.log = log_path.open("a", encoding="utf-8")
        environment = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}
        self.process = subprocess.Popen(
            [sys.executable, "-B", str(SERVER_SCRIPT), "--data-dir", str(self.data_dir), "--port", "0"],
            cwd=ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=self.log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            deadline = time.monotonic() + 15
            ready_path = self.data_dir / "runtime-ready.json"
            with httpx.Client(timeout=0.3, trust_env=False) as client:
                while time.monotonic() < deadline:
                    if self.process.poll() is not None:
                        break
                    try:
                        ready = json.loads(ready_path.read_text(encoding="utf-8"))
                        # Windows 虚拟环境可能先启动 Python 转发进程。
                        if self.process.pid in (ready["pid"], ready.get("parent_pid")):
                            self.base_url = f"http://127.0.0.1:{ready['port']}"
                            if client.get(self.base_url + "/api/health").status_code == 200:
                                return self
                    except (OSError, ValueError, KeyError, httpx.RequestError):
                        pass
                    time.sleep(0.04)
            raise RuntimeError("测试服务未就绪：" + log_path.read_text(encoding="utf-8")[-4000:])
        except BaseException:
            self.stop()
            raise

    def stop(self):
        try:
            if self.process is not None and self.process.poll() is None:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/PID", str(self.process.pid), "/T", "/F"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW, timeout=5,
                    )
                else:
                    self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
        finally:
            self.process = None
            if self.log is not None:
                self.log.close()
                self.log = None


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="storespark-runtime-")
        self.addCleanup(self.directory.cleanup)
        self.data_dir = Path(self.directory.name)
        self.server = RuntimeServer(self.data_dir)
        self.addCleanup(self.server.stop)
        self.server.start()
        self.connect()

    def connect(self):
        self.client = httpx.Client(base_url=self.server.base_url, timeout=15, trust_env=False)
        self.addCleanup(self.client.close)

    def create_task(self, title):
        response = self.client.post("/api/v1/tasks", json={
            "title": title,
            "brief": "测试 fixture 需求，不代表商家实际需求。",
            "channel": "测试 fixture 渠道",
            "format": "测试 fixture 文案",
        })
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["id"]

    def test_tcp_workflow_survives_process_restart(self):
        settings = self.client.put("/api/v1/provider", json={
            "provider": "deepseek",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-flash",
            "api_key": "runtime-fixture-saved-key-only",
        })
        self.assertEqual(settings.status_code, 200, settings.text)
        self.assertEqual(settings.json()["source"], "saved")
        self.assertTrue(settings.json()["api_key_set"])
        self.assertNotIn("runtime-fixture-saved-key-only", settings.text)
        task_id = self.create_task("测试 fixture：真实进程任务")
        path = f"/api/v1/tasks/{task_id}"
        upload = self.client.post(path + "/materials", files={
            "file": ("fixture.md", "测试 fixture 菜单：未提供真实菜品。".encode("utf-8"), "text/markdown")
        })
        self.assertEqual(upload.status_code, 201, upload.text)
        for action in ("direction", "generate"):
            response = self.client.post(path + "/messages", json={
                "content": "测试 fixture：" + action,
                "action": action,
            })
            self.assertEqual(response.status_code, 200, response.text)
        task = response.json()
        self.assertEqual(task["status"], "content")
        artifact_id = task["artifacts"][-1]["id"]
        manual_content = "测试 fixture：人工编辑的最终正文，仅用于软件流程检查。"
        edit = self.client.patch(path + "/artifacts/" + artifact_id, json={
            "title": "测试 fixture 人工标题",
            "content": manual_content,
        })
        self.assertEqual(edit.status_code, 200, edit.text)
        exported = self.client.get(path + "/export")
        self.assertEqual(exported.status_code, 200, exported.text)
        self.assertIn("text/markdown", exported.headers["content-type"])
        self.assertIn("attachment;", exported.headers["content-disposition"])
        self.assertIn(manual_content, exported.text)
        self.assertNotIn("runtime-fixture-saved-key-only", exported.text)
        before = self.client.get(path).json()
        old_pid = self.server.process.pid

        self.client.close()
        self.server.stop()
        self.server.start()
        self.connect()
        self.assertNotEqual(self.server.process.pid, old_pid)
        restored = self.client.get(path)
        self.assertEqual(restored.status_code, 200, restored.text)
        self.assertEqual(restored.json(), before)
        self.assertEqual(restored.json()["materials"][0]["name"], "fixture.md")
        self.assertEqual(restored.json()["artifacts"][-1]["content"], manual_content)
        self.assertEqual(self.client.get(path + "/export").text, exported.text)
        self.assertEqual(self.client.get("/api/v1/provider").json()["source"], "saved")
        generated = self.client.post(path + "/messages", json={
            "action": "generate", "content": "测试 fixture：重启后生成",
        })
        self.assertEqual(generated.status_code, 200, generated.text)

    def test_same_task_concurrency_returns_conflict_without_crossed_records(self):
        task_id = self.create_task("测试 fixture：并发任务 A")
        other_id = self.create_task("测试 fixture：并发任务 B")
        path = f"/api/v1/tasks/{task_id}"
        rejected_content = "测试 fixture：第二个同任务请求不得落库"
        with ThreadPoolExecutor(max_workers=1) as executor:
            first = executor.submit(self.client.post, path + "/messages", json={
                "action": "generate", "content": WAIT_MESSAGE,
            })
            try:
                deadline = time.monotonic() + 5
                while not (self.data_dir / "runtime-model-entered").exists():
                    if first.done():
                        self.fail("测试 fixture 首个请求提前结束：" + first.result().text)
                    if time.monotonic() >= deadline:
                        self.fail("测试 fixture 模型处理没有进入等待状态")
                    time.sleep(0.02)
                second = self.client.post(path + "/messages", json={
                    "action": "generate", "content": rejected_content,
                })
                self.assertEqual(second.status_code, 409, second.text)
                other = self.client.post(f"/api/v1/tasks/{other_id}/messages", json={
                    "action": "generate", "content": "测试 fixture：另一个任务独立生成",
                })
                self.assertEqual(other.status_code, 200, other.text)
            finally:
                (self.data_dir / "runtime-model-release").write_text("测试 fixture 释放", encoding="utf-8")
            completed = first.result(timeout=10)
        self.assertEqual(completed.status_code, 200, completed.text)
        task = self.client.get(path).json()
        self.assertEqual([item["role"] for item in task["messages"]], ["user", "assistant"])
        self.assertEqual(task["messages"][0]["content"], WAIT_MESSAGE)
        self.assertEqual(len(task["artifacts"]), 1)
        self.assertNotIn(rejected_content, json.dumps(task, ensure_ascii=False))
        self.assertIn("并发任务 A", task["artifacts"][0]["content"])
        self.assertNotIn("并发任务 B", task["artifacts"][0]["content"])
        other_task = self.client.get(f"/api/v1/tasks/{other_id}").json()
        self.assertEqual(len(other_task["messages"]), 2)
        self.assertEqual(len(other_task["artifacts"]), 1)
        self.assertIn("并发任务 B", other_task["artifacts"][0]["content"])
        self.assertNotIn("并发任务 A", other_task["artifacts"][0]["content"])


if __name__ == "__main__":
    unittest.main()
