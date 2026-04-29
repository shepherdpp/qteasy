# coding=utf-8
# ======================================
# File: test_ai_corpus_regression.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-20
# Desc:
# Unittest for qteasy ai corpus regression
# ======================================

import json
import unittest
from pathlib import Path

from qteasy.ai.app import QteasyAssistant


class TestAiCorpusRegression(unittest.TestCase):
    """测试 AI 语料回归。"""

    @staticmethod
    def _load_cases(file_name: str) -> list[dict]:
        corpus_path = Path(__file__).resolve().parent / "ai_corpus" / file_name
        with corpus_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload.get("cases", [])

    def test_current_capability_corpus(self) -> None:
        """验证已实现能力语料路由与 ask 语义。"""

        assistant = QteasyAssistant()
        cases = self._load_cases("current_capabilities.json")
        print("\n[TestAiCorpusRegression] current capability cases:", len(cases))
        for case in cases:
            query = case["query"]
            mode = case.get("mode", "plan")
            if mode == "ask":
                payload = assistant.ask(query, response_style="raw")
                steps = payload["plan"]["steps"]
                print(" ask case:", case["id"], "steps:", len(steps))
                self.assertEqual(steps, [])
            else:
                payload = assistant.plan(query, response_style="raw")
                steps = payload["plan"]["steps"]
                print(" plan case:", case["id"], "skill:", steps[0]["skill_name"] if steps else "")
                self.assertGreaterEqual(len(steps), 1)
                self.assertEqual(steps[0]["skill_name"], case["expected_skill"])

    def test_future_capability_fallback_corpus(self) -> None:
        """验证前瞻语料回退行为。"""

        assistant = QteasyAssistant()
        cases = self._load_cases("future_capabilities.json")
        print("\n[TestAiCorpusRegression] future capability cases:", len(cases))
        for case in cases:
            payload = assistant.run(case["query"], response_style="raw")
            result = payload["execution"]["steps"][0]["result"]
            action = result.get("payload", {}).get("fallback_action")
            error_code = (result.get("error") or {}).get("code", "")
            print(" future case:", case["id"], "action:", action, "error:", error_code)
            self.assertEqual(action, case["expected_fallback_action"])
            self.assertIn(error_code, ["PLAN_ONLY", "NOT_SUPPORTED_YET", "CLARIFY_REQUIRED"])

    def test_error_corpus_consistency(self) -> None:
        """验证错误语料结构化错误一致性。"""

        assistant = QteasyAssistant()
        cases = self._load_cases("error_corpus.json")
        print("\n[TestAiCorpusRegression] error cases:", len(cases))
        for case in cases:
            payload = assistant.run(case["query"], response_style="raw")
            status = payload["execution"]["status"]
            steps = payload["execution"]["steps"]
            print(" error case:", case["id"], "status:", status, "steps:", len(steps))
            self.assertGreaterEqual(len(steps), 1)
            error = (steps[0]["result"].get("error") or {})
            print("  error:", error)
            self.assertIn(error.get("code", ""), case["expected_error_codes"])
            self.assertIn("message", error)

    def test_user_friendly_output_has_required_fields(self) -> None:
        """验证 user_friendly 输出包含 narrative/code/preview。"""

        assistant = QteasyAssistant()
        output = assistant.plan("list built-in strategies", response_style="user_friendly")
        output_dict = output.to_dict()
        print("\n[TestAiCorpusRegression] user_friendly output:", output_dict)
        self.assertTrue(output_dict["narrative"])
        self.assertTrue(output_dict["python_code"])
        self.assertIn("result_preview", output_dict)
        self.assertIn("raw", output_dict)


if __name__ == "__main__":
    unittest.main()
