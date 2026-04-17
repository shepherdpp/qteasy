# coding=utf-8
# ======================================
# File: test_ai_cli_notebook_entry.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# Unittest for qteasy ai notebook and cli entry
# ======================================

import json
import subprocess
import sys
import tempfile
import unittest

from qteasy.ai.app import QteasyAssistant, build_default_registry
from qteasy.ai.memory_store import MemoryStore


class TestAiCliNotebookEntry(unittest.TestCase):
    """测试 Notebook/CLI 两入口可用。"""

    def test_notebook_assistant_plan_and_run(self) -> None:
        """验证 notebook 风格入口结构化输出。"""

        with tempfile.TemporaryDirectory() as temp_dir:
            store = MemoryStore(base_dir=temp_dir)
            assistant = QteasyAssistant(registry=build_default_registry(), memory_store=store)
            plan_payload = assistant.plan("list built-in strategies")
            run_payload = assistant.run("list built-in strategies")

            print("\n[TestAiCliNotebookEntry] plan status:", plan_payload["execution"]["status"])
            print(" run status:", run_payload["execution"]["status"])
            print(" run steps:", len(run_payload["execution"]["steps"]))

            self.assertEqual(plan_payload["execution"]["status"], "dry_run")
            self.assertIn(run_payload["execution"]["status"], ["success", "partial_failed"])
            self.assertGreaterEqual(len(run_payload["execution"]["steps"]), 1)

    def test_cli_plan_command(self) -> None:
        """验证 CLI plan 子命令可执行。"""

        cmd = [sys.executable, "-m", "qteasy.ai.cli", "plan", "list built-in strategies"]
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
        payload = json.loads(completed.stdout)

        print("\n[TestAiCliNotebookEntry] cli stdout:", completed.stdout[:240])
        print(" cli status:", payload["execution"]["status"])

        self.assertEqual(payload["execution"]["status"], "dry_run")
        self.assertIn("plan_id", payload["plan"])


if __name__ == "__main__":
    unittest.main()
