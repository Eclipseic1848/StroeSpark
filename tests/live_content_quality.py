"""显式运行的真实模型对比检查；不属于自动 CI，不使用商家资料或输出密钥。"""

import argparse
import asyncio
import copy
import hashlib
import json
import re
import subprocess
import sys
import time
import types
from pathlib import Path

from pydantic import ValidationError

from storespark.provider import ProviderError, ProviderService
from storespark.schema import ModelReply
from storespark.settings import ROOT, Settings
from storespark.store import Store
from storespark.workflow import build_messages

BASELINE_REF = "7f0d3fa"


def check_sample(case: dict, reply: ModelReply) -> dict:
    content = re.sub(r"【待确认[^】]*】", "", reply.content)
    checked = {"required_terms": all(term in (reply.reply if case["action"] == "clarify" else reply.content)
                                      for term in case["required_terms"])}
    if case["action"] != "clarify":
        # 这些有限反例只用于此测试资料，真实输出仍需逐项人工复核，不能充当生产禁词表。
        checked["no_observed_unsupported_attributes"] = not any(
            term in content for term in ("皮薄", "馅香", "不少顾客", "常点", "招牌", "家常做法"))
    if case["expectation"] == "unconfirmed":
        checked["no_unconfirmed_home_style_in_body"] = "家常" not in content
        checked["candidate_labelled"] = "家常" not in reply.direction or any(
            word in reply.direction for word in ("候选", "待确认", "建议", "假设"))
    if case["action"] == "clarify":
        checked["no_body_during_clarification"] = not reply.content
        questions = [line for line in reply.reply.splitlines() if re.match(r"\s*\d+[.、）)]", line)]
        checked["no_repeated_menu_authenticity_question"] = not any(
            "真实" in line and any(word in line for word in ("测试", "示例", "虚构", "演示"))
            for line in questions + reply.missing_facts)
    else:
        checked["complete_delivery"] = bool(reply.content and reply.usage and reply.validation)
    return checked


async def main():
    parser = argparse.ArgumentParser(description="会产生真实 DeepSeek 请求并保存每次结果；有限匹配仍需人工语义复核")
    parser.add_argument("variant", choices=["baseline", "candidate"])
    arguments = parser.parse_args()
    cases = json.loads((ROOT / "tests/fixtures/content_grounding.json").read_text(encoding="utf-8"))
    baseline = types.ModuleType("storespark_baseline_workflow")
    source = subprocess.run(["git", "show", BASELINE_REF + ":storespark/workflow.py"], cwd=ROOT,
                            check=True, capture_output=True, text=True, encoding="utf-8").stdout
    exec(compile(source, "baseline_workflow.py", "exec"), baseline.__dict__)
    settings = Settings.from_env()
    provider = ProviderService(settings, Store(settings.data_dir))
    config = provider.public_config()
    assert config["api_key_set"] and config["provider"] == "deepseek"
    assert config["base_url"] == "https://api.deepseek.com" and config["model"] == "deepseek-flash"
    output = ROOT / "test-results/quality-grounding-20261028"
    output.mkdir(parents=True, exist_ok=True)
    failed = False
    for case in cases:
        materials = [{"name": item["name"], "media_type": item["media_type"],
                      "content": (ROOT / item["path"]).read_bytes()} for item in case["materials"]]
        old = baseline.build_messages(case["task"], materials, case["action"])
        current = build_messages(case["task"], materials, case["action"])
        comparable = copy.deepcopy(current)
        comparable[0] = old[0]
        context = json.loads(comparable[1]["content"].removeprefix("任务资料："))
        for artifact in context["existing_artifacts"]:
            artifact.pop("source", None)
        comparable[1]["content"] = "任务资料：" + json.dumps(context, ensure_ascii=False)
        assert comparable == old, "对比输入除系统规则和草稿标识外发生变化"
        messages = old if arguments.variant == "baseline" else current
        digest = hashlib.sha256(json.dumps(messages, ensure_ascii=False).encode("utf-8")).hexdigest()
        path = output / (arguments.variant + "-" + case["id"] + "-" + digest[:12] + ".json")
        if path.exists():
            saved = json.loads(path.read_text(encoding="utf-8"))
            assert saved["input_sha256"] == digest, "已有结果对应不同输入，不覆盖历史记录"
            try:
                checks = check_sample(case, ModelReply.model_validate(saved.get("response", {})))
            except ValidationError:
                checks = {}
            print(json.dumps({"case": case["id"], "saved_result_reused": True, "checks": checks}, ensure_ascii=False), flush=True)
            failed |= not checks or not all(checks.values())
            continue
        record = {"variant": arguments.variant, "case": case["id"], "input_sha256": digest}
        start = time.monotonic()
        try:
            raw = await provider.complete(messages)
            record["response"] = raw
            reply = ModelReply.model_validate(raw)
            record["status"] = "valid_response"
            record["checks"] = check_sample(case, reply)
            failed |= not all(record["checks"].values())
        except ProviderError as error:
            record.update(status="provider_failure", error=str(error))
            failed = True
        except ValidationError as error:
            record.update(status="schema_failure", errors=[{"loc": list(item["loc"]), "type": item["type"]}
                                                          for item in error.errors()])
            failed = True
        record["elapsed_seconds"] = round(time.monotonic() - start, 2)
        with path.open("x", encoding="utf-8") as file:
            json.dump(record, file, ensure_ascii=False, indent=2)
            file.write("\n")
        print(json.dumps({key: value for key, value in record.items() if key != "response"}, ensure_ascii=False), flush=True)
    return int(failed)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(asyncio.run(main()))
