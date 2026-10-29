"""仅供测试的真实 TCP 服务，模型响应均为测试 fixture，不访问外部网络。"""

import argparse
import asyncio
import json
import os
import socket
import sys
import time
from pathlib import Path

import httpx
import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from storespark.app import create_app
from storespark.settings import Settings

WAIT_MESSAGE = "测试 fixture：等待并发检查"
FAIL_MESSAGE = "测试 fixture：模型服务失败"


def create_fixture_app(data_dir: Path):
    async def model_fixture(request: httpx.Request) -> httpx.Response:
        if request.url.host != "api.deepseek.com":
            raise AssertionError("测试 fixture 不接受其他模型地址")
        payload = json.loads(request.content)
        messages = payload["messages"]
        context = json.loads(messages[1]["content"].removeprefix("任务资料："))
        latest = next(
            message["content"] for message in reversed(messages)
            if message["role"] == "user" and isinstance(message["content"], str)
        )
        if latest == FAIL_MESSAGE:
            return httpx.Response(503, json={"error": "测试 fixture 上游失败"})
        if latest == WAIT_MESSAGE:
            (data_dir / "runtime-model-entered").write_text("测试 fixture 已进入", encoding="utf-8")
            deadline = time.monotonic() + 10
            while not (data_dir / "runtime-model-release").exists():
                if time.monotonic() >= deadline:
                    return httpx.Response(503, json={"error": "测试 fixture 等待释放超时"})
                await asyncio.sleep(0.02)
        result = {
            "reply": "测试 fixture 回复：" + latest,
            "direction": "测试 fixture 宣传方向，仅用于自动化检查，未经过商家验证。",
            "title": "测试 fixture 文案",
            "content": f"测试 fixture 内容：{context['title']}\n测试 fixture 本次输入：{latest}",
            "missing_facts": ["测试 fixture：门店真实信息待核实"],
            "usage": "测试 fixture 使用建议：不作为真实宣传物料。",
            "validation": "测试 fixture 验证建议：仅检查软件流程。",
        }
        return httpx.Response(200, json={
            "choices": [{
                "finish_reason": "stop",
                "message": {"content": json.dumps(result, ensure_ascii=False)},
            }]
        })

    settings = Settings(
        data_dir=data_dir,
        provider_api_key="runtime-fixture-api-key-only",
        provider_timeout=15,
    )
    return create_app(settings, transport=httpx.MockTransport(model_fixture))


def main():
    parser = argparse.ArgumentParser(description="仅测试使用的 StoreSpark fixture 服务")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    arguments = parser.parse_args()
    if not 0 <= arguments.port <= 65535:
        parser.error("端口必须在 0 到 65535 之间")
    arguments.data_dir.mkdir(parents=True, exist_ok=True)
    app = create_fixture_app(arguments.data_dir)
    config = uvicorn.Config(app, host="127.0.0.1", port=arguments.port, log_level="warning")
    ready_path = arguments.data_dir / "runtime-ready.json"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", arguments.port))
        listener.listen(128)
        ready_path.write_text(json.dumps({
            "pid": os.getpid(), "parent_pid": os.getppid(), "port": listener.getsockname()[1],
        }), encoding="utf-8")
        uvicorn.Server(config).run(sockets=[listener])


if __name__ == "__main__":
    main()
