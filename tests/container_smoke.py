"""在真实 Linux 容器中验证入口、访问控制和无模型密钥时的诚实失败。"""

import argparse
import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    parser.add_argument("--restore", action="store_true")
    arguments = parser.parse_args()
    token = os.environ["STORESPARK_TEST_TOKEN"]

    def request(path, method="GET", data=None, auth=True):
        headers = {"Authorization": "Bearer " + token} if auth else {}
        if data is not None:
            headers["Content-Type"] = "application/json"
        value = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
        try:
            with urlopen(Request(arguments.base_url + path, data=value, headers=headers, method=method), timeout=3) as response:
                return response.status, response.read()
        except HTTPError as error:
            return error.code, error.read()

    deadline = time.monotonic() + 40
    while True:
        try:
            status, body = request("/api/health")
            if status == 200:
                break
        except (URLError, TimeoutError, ConnectionError):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError("容器服务未在限时内就绪")
        time.sleep(0.25)
    assert not json.loads(body)["provider_configured"]
    assert request("/api/v1/tasks", auth=False)[0] == 401
    status, html = request("/")
    assert status == 200 and b'<div id="root">' in html
    state = Path(os.environ.get("RUNNER_TEMP", ".")) / "storespark-container-task.txt"
    if arguments.restore:
        task_id = state.read_text(encoding="utf-8")
        status, body = request("/api/v1/tasks/" + task_id)
        assert status == 200
        task = json.loads(body)
        assert task["title"] == "容器持久化检查"
        assert task["messages"][0]["content"] == "请保留本次容器检查输入"
        print("PASS: 容器重启后任务与失败前输入仍可读取")
        return
    status, body = request("/api/v1/tasks", "POST", {"title": "容器持久化检查", "brief": "仅测试部署，不是实际商家数据"})
    assert status == 201
    task_id = json.loads(body)["id"]
    state.write_text(task_id, encoding="utf-8")
    status, body = request(f"/api/v1/tasks/{task_id}/messages", "POST", {"content": "请保留本次容器检查输入", "action": "clarify"})
    assert status == 503
    status, body = request(f"/api/v1/tasks/{task_id}")
    assert status == 200 and len(json.loads(body)["messages"]) == 1
    assert json.loads(body)["artifacts"] == []
    assert request(f"/api/v1/tasks/{task_id}/export")[0] == 200
    print("PASS: 容器页面、访问控制、任务保存、未配置模型失败与导出")


if __name__ == "__main__":
    main()
