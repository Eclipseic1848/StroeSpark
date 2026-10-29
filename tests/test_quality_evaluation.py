"""验证有限样本判定器；通过这些检查不代表真实模型质量已经通过。"""

import json
import unittest
from pathlib import Path

from live_content_quality import check_sample
from storespark.schema import ModelReply


class QualityEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture_path = Path(__file__).parent / "fixtures" / "content_grounding.json"
        cls.cases = {case["id"]: case for case in json.loads(fixture_path.read_text(encoding="utf-8"))}

    @staticmethod
    def reply(**changes):
        values = {
            "reply": "测试样本：按已提供资料继续。",
            "direction": "仅使用已提供店名与菜名。",
            "title": "测试样本文案",
            "content": "测试店甲的白菜猪肉蒸饺，价格与地址待确认。",
            "missing_facts": ["价格", "地址"],
            "usage": "测试样本使用建议，事实确认后再使用。",
            "validation": "测试样本验证建议，不推断经营效果。",
        }
        return ModelReply.model_validate({**values, **changes})

    def test_historical_unconfirmed_positioning_in_body_is_detected(self):
        reply = self.reply(content="测试店甲推出白菜猪肉蒸饺，主打家常蒸饺品类，适合到店品尝。")
        for case_id in ("text_known_facts", "unconfirmed_old_draft"):
            with self.subTest(case=case_id):
                checks = check_sample(self.cases[case_id], reply)
                self.assertTrue(checks["required_terms"])
                self.assertFalse(checks["no_unconfirmed_home_style_in_body"])
                self.assertFalse(all(checks.values()))

    def test_unconfirmed_direction_requires_a_candidate_label(self):
        case = self.cases["unconfirmed_old_draft"]
        proposed = check_sample(case, self.reply(direction="候选方向：家常蒸饺定位，尚待商家确认。"))
        self.assertTrue(proposed["candidate_labelled"])
        self.assertTrue(proposed["no_unconfirmed_home_style_in_body"])
        self.assertTrue(all(proposed.values()))
        unlabelled = check_sample(case, self.reply(direction="品牌以家常蒸饺为定位。"))
        self.assertFalse(unlabelled["candidate_labelled"])
        self.assertFalse(all(unlabelled.values()))
        # 条件建议混入正文不符合本样本的字段分工，不把条件建议称为事实断言。
        mixed = check_sample(case, self.reply(content="测试店甲的白菜猪肉蒸饺。如果商家确认家常定位，可采用此候选方向。"))
        self.assertFalse(mixed["no_unconfirmed_home_style_in_body"])
        self.assertFalse(all(mixed.values()))

    def test_observed_candidate_attributes_are_rejected_for_fixed_materials(self):
        # 这些反例只对应固定测试资料，不是生产内容的关键词禁用规则。
        for content in (
            "测试店甲的白菜猪肉蒸饺，皮薄馅香，不少顾客常点。",
            "测试店甲的白菜猪肉蒸饺，采用家常做法。",
        ):
            with self.subTest(content=content):
                checks = check_sample(self.cases["text_known_facts"], self.reply(content=content))
                self.assertTrue(checks["required_terms"])
                self.assertTrue(checks["complete_delivery"])
                self.assertFalse(checks["no_observed_unsupported_attributes"])
                self.assertFalse(all(checks.values()))

    def test_confirmed_positioning_passes_without_craft_or_popularity_inferences(self):
        content = "测试店甲的白菜猪肉蒸饺，本次采用用户确认的家常蒸饺定位。价格与地址待确认。"
        checks = check_sample(self.cases["user_confirmed_positioning"], self.reply(content=content))
        self.assertTrue(checks["required_terms"])
        self.assertTrue(checks["no_observed_unsupported_attributes"])
        self.assertTrue(all(checks.values()))
        inferred = check_sample(self.cases["user_confirmed_positioning"], self.reply(
            content=content + "采用家常做法，皮薄馅香，不少顾客常点。"))
        self.assertTrue(inferred["required_terms"])
        self.assertFalse(inferred["no_observed_unsupported_attributes"])
        self.assertFalse(all(inferred.values()))

    def test_user_confirmed_positioning_must_remain_in_body(self):
        case = self.cases["user_confirmed_positioning"]
        kept = check_sample(case, self.reply(content="测试店甲的白菜猪肉蒸饺，本次采用用户确认的家常蒸饺定位。"))
        self.assertTrue(all(kept.values()))
        removed = check_sample(case, self.reply(direction="用户已确认家常蒸饺定位。"))
        self.assertFalse(removed["required_terms"])
        self.assertFalse(all(removed.values()))

    def test_historical_repeated_menu_authenticity_question_is_detected(self):
        reply = self.reply(
            title="", content="", usage="", validation="",
            reply="图片菜名：香菇青菜蒸饺、玉米鸡肉蒸饺。\n"
                  "1. 这份菜单卡对应的是真实门店菜单，还是仅作软件测试的虚构示例？\n"
                  "2. 本次宣传目标是什么？",
        )
        checks = check_sample(self.cases["image_known_answers"], reply)
        self.assertTrue(checks["required_terms"])
        self.assertFalse(checks["no_repeated_menu_authenticity_question"])
        self.assertFalse(all(checks.values()))

    def test_unknown_goal_and_channel_questions_are_not_mistaken_for_repetition(self):
        reply = self.reply(
            title="", content="", usage="", validation="",
            reply="图片是软件测试示例，不是真实菜单；菜名为香菇青菜蒸饺、玉米鸡肉蒸饺。\n"
                  "1. 本次希望告知菜品，还是介绍门店？\n"
                  "2. 打算用于哪个宣传渠道？",
        )
        checks = check_sample(self.cases["image_known_answers"], reply)
        self.assertTrue(checks["no_repeated_menu_authenticity_question"])
        self.assertTrue(all(checks.values()))

    def test_repeated_authenticity_request_in_missing_facts_is_detected(self):
        case = self.cases["image_known_answers"]
        values = {
            "title": "", "content": "", "usage": "", "validation": "",
            "reply": "这是软件测试，不是真实门店；图片菜名为香菇青菜蒸饺、玉米鸡肉蒸饺。",
            "missing_facts": ["门店名称", "宣传渠道"],
        }
        ordinary = check_sample(case, self.reply(**values))
        self.assertTrue(ordinary["no_repeated_menu_authenticity_question"])
        self.assertTrue(all(ordinary.values()))
        repeated = check_sample(case, self.reply(**{
            **values,
            "missing_facts": [*values["missing_facts"], "本次内容面向真实顾客，还是仅用于软件功能演示"],
        }))
        self.assertTrue(repeated["required_terms"])
        self.assertTrue(repeated["no_body_during_clarification"])
        self.assertFalse(repeated["no_repeated_menu_authenticity_question"])
        self.assertFalse(all(repeated.values()))

    def test_clarification_with_generated_body_is_rejected(self):
        reply = self.reply(reply="图中是香菇青菜蒸饺、玉米鸡肉蒸饺。", content="测试样本：不应在澄清时生成的正文。")
        checks = check_sample(self.cases["image_known_answers"], reply)
        self.assertTrue(checks["required_terms"])
        self.assertFalse(checks["no_body_during_clarification"])
        self.assertFalse(all(checks.values()))

    def test_generation_without_required_delivery_sections_is_rejected(self):
        for field in ("usage", "validation"):
            with self.subTest(missing=field):
                checks = check_sample(self.cases["text_known_facts"], self.reply(**{field: ""}))
                self.assertTrue(checks["required_terms"])
                self.assertFalse(checks["complete_delivery"])
                self.assertFalse(all(checks.values()))


if __name__ == "__main__":
    unittest.main()
