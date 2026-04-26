# coding=utf-8
# ======================================
# File: test_ai_notebook_magic.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-26
# Desc:
# Unittest for qteasy ai notebook magic
# ======================================

import tempfile
import unittest

from qteasy.ai.app import QteasyAssistant, build_default_registry
from qteasy.ai.memory_store import MemoryStore
from qteasy.ai.notebook_magic import (
    execute_magic_command,
    parse_magic_command,
)


class TestAiNotebookMagic(unittest.TestCase):
    """测试 Notebook 魔法命令入口。"""

    def test_parse_magic_command(self) -> None:
        """验证魔法命令参数解析。"""

        command = parse_magic_command(
            line="--mode run --raw --persist none --keep --confirm plan_abc",
            cell="列出所有内置策略",
        )
        print("\n[TestAiNotebookMagic] parsed command:", command)
        self.assertEqual(command.mode, "run")
        self.assertEqual(command.response_style, "raw")
        self.assertEqual(command.persist, "none")
        self.assertTrue(command.keep)
        self.assertEqual(command.confirm_plan_id, "plan_abc")
        self.assertEqual(command.query, "列出所有内置策略")

    def test_ask_mode_is_readonly(self) -> None:
        """验证 Ask 模式为 dry_run 且无执行步骤。"""

        with tempfile.TemporaryDirectory() as temp_dir:
            assistant = QteasyAssistant(
                registry=build_default_registry(),
                memory_store=MemoryStore(base_dir=temp_dir),
            )
            plan_cache = {}
            command = parse_magic_command("--mode ask --raw 列出所有内置策略")
            outcome = execute_magic_command(command, assistant=assistant, plan_cache=plan_cache)
            payload = outcome["result"]

            print("\n[TestAiNotebookMagic] ask payload status:", payload["execution"]["status"])
            print(" ask plan steps:", len(payload["plan"]["steps"]))
            self.assertEqual(payload["execution"]["status"], "dry_run")
            self.assertEqual(len(payload["plan"]["steps"]), 0)

    def test_confirm_flow(self) -> None:
        """验证 run -> confirm 的两阶段流程。"""

        with tempfile.TemporaryDirectory() as temp_dir:
            assistant = QteasyAssistant(
                registry=build_default_registry(),
                memory_store=MemoryStore(base_dir=temp_dir),
            )
            plan_cache = {}

            run_command = parse_magic_command("--mode run --raw 列出所有内置策略")
            run_outcome = execute_magic_command(run_command, assistant=assistant, plan_cache=plan_cache)
            run_payload = run_outcome["result"]
            plan_id = run_outcome["plan_id"]

            print("\n[TestAiNotebookMagic] run dry status:", run_payload["execution"]["status"])
            print(" cached plan id:", plan_id)
            print(" cache size:", len(plan_cache))
            self.assertEqual(run_payload["execution"]["status"], "dry_run")
            self.assertIn(plan_id, plan_cache)

            confirm_command = parse_magic_command(f"--raw --confirm {plan_id}")
            confirm_outcome = execute_magic_command(confirm_command, assistant=assistant, plan_cache=plan_cache)
            confirm_payload = confirm_outcome["result"]

            print("[TestAiNotebookMagic] confirm status:", confirm_payload["execution"]["status"])
            print(" confirm steps:", len(confirm_payload["execution"]["steps"]))
            print(" cache size after confirm:", len(plan_cache))
            self.assertIn(confirm_payload["execution"]["status"], ["success", "partial_failed"])
            self.assertGreaterEqual(len(confirm_payload["execution"]["steps"]), 1)
            self.assertNotIn(plan_id, plan_cache)

    def test_fallback_not_approximate_substitution(self) -> None:
        """验证不支持请求走 system fallback，而非近似替代 skill。"""

        with tempfile.TemporaryDirectory() as temp_dir:
            assistant = QteasyAssistant(
                registry=build_default_registry(),
                memory_store=MemoryStore(base_dir=temp_dir),
            )
            plan_cache = {}
            command = parse_magic_command("--mode plan --raw 下载A股数据并回测")
            outcome = execute_magic_command(command, assistant=assistant, plan_cache=plan_cache)
            payload = outcome["result"]
            first_step = payload["plan"]["steps"][0]

            print("\n[TestAiNotebookMagic] fallback first skill:", first_step["skill_name"])
            print(" fallback action:", first_step["inputs"].get("fallback_action"))
            self.assertEqual(first_step["skill_name"], "qt.ai.system.fallback")
            self.assertIn(first_step["inputs"].get("fallback_action"), ["not_supported_yet", "clarify_required", "plan_only"])


if __name__ == "__main__":
    unittest.main()

