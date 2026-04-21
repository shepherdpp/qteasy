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
import os
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

    def test_cli_provider_check_diagnostics(self) -> None:
        """验证 provider-check 返回配置诊断信息。"""

        env = dict(os.environ)
        env["QTEASY_AI_MODEL"] = "deepseek-chat"
        env["QTEASY_AI_API_KEY"] = "test_key"
        env["QTEASY_AI_BASE_URL"] = "https://api.deepseek.com/v1"
        env["QTEASY_AI_TIMEOUT"] = "42"

        cmd = [sys.executable, "-m", "qteasy.ai.cli", "provider-check"]
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
        payload = json.loads(completed.stdout)

        print("\n[TestAiCliNotebookEntry] provider-check:", payload)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["provider"], "openai_compatible")
        self.assertEqual(payload["mode"], "cloud_llm")
        self.assertEqual(payload["model"], "deepseek-chat")
        self.assertEqual(payload["base_url"], "https://api.deepseek.com/v1")
        self.assertEqual(payload["timeout"], 42)
        self.assertTrue(payload["api_key_present"])
        self.assertIn("config_sources", payload)

    def test_cli_provider_check_rule_mode(self) -> None:
        """验证 provider-check 在无模型配置时为规则模式。"""

        env = dict(os.environ)
        env.pop("QTEASY_AI_MODEL", None)
        env.pop("QTEASY_AI_API_KEY", None)
        env.pop("QTEASY_AI_BASE_URL", None)
        env.pop("QTEASY_AI_TIMEOUT", None)

        cmd = [sys.executable, "-m", "qteasy.ai.cli", "provider-check"]
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
        payload = json.loads(completed.stdout)

        print("\n[TestAiCliNotebookEntry] provider-check rule mode:", payload)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["mode"], "rule")

    def test_cli_provider_check_local_mode(self) -> None:
        """验证 provider-check 在本地地址时识别 local_llm。"""

        env = dict(os.environ)
        env["QTEASY_AI_MODEL"] = "llama3.1:8b"
        env["QTEASY_AI_API_KEY"] = "ollama"
        env["QTEASY_AI_BASE_URL"] = "http://127.0.0.1:11434/v1"
        env["QTEASY_AI_TIMEOUT"] = "30"

        cmd = [sys.executable, "-m", "qteasy.ai.cli", "provider-check"]
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
        payload = json.loads(completed.stdout)

        print("\n[TestAiCliNotebookEntry] provider-check local mode:", payload)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["mode"], "local_llm")


if __name__ == "__main__":
    unittest.main()
