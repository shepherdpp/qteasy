# coding=utf-8
# ======================================
# File: test_ai_run_policy.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-20
# Desc:
# Unittest for qteasy ai run policy and
# bounded persistence cleanup
# ======================================

import tempfile
import unittest

from qteasy.ai.app import QteasyAssistant, build_default_registry
from qteasy.ai.memory_store import MemoryStore
from qteasy.ai.run_policy import RunStorePolicy


class TestAiRunPolicy(unittest.TestCase):
    """测试 run 留存策略。"""

    def test_bounded_cleanup_and_pin(self) -> None:
        """验证 bounded 自动清理与 pin。"""

        with tempfile.TemporaryDirectory() as temp_dir:
            store = MemoryStore(base_dir=temp_dir)
            policy = RunStorePolicy(persist_mode="bounded", max_age_days=999, max_count=2, max_total_mb=200)
            assistant = QteasyAssistant(registry=build_default_registry(), memory_store=store, run_policy=policy)

            r1 = assistant.plan("list built-in strategies", response_style="raw")
            r2 = assistant.plan("list built-in strategies", response_style="raw")
            r3 = assistant.plan("list built-in strategies", response_style="raw")
            runs = store.list_runs()
            print("\n[TestAiRunPolicy] runs after bounded cleanup:", runs)
            self.assertLessEqual(len(runs), 2)
            self.assertIn("cleanup", r3)

            run_payload = assistant.run("list built-in strategies", response_style="raw", keep=True)
            print(" pinned file:", run_payload.get("pinned_file", ""))
            pinned = store.list_pinned()
            print(" pinned list:", pinned)
            self.assertGreaterEqual(len(pinned), 1)

            pinned_path = assistant.pin_last_run(tag="manual")
            print(" pin last path:", pinned_path)
            self.assertTrue(pinned_path.endswith(".json"))

    def test_persist_none(self) -> None:
        """验证 persist=none 不落盘。"""

        with tempfile.TemporaryDirectory() as temp_dir:
            store = MemoryStore(base_dir=temp_dir)
            assistant = QteasyAssistant(memory_store=store)
            payload = assistant.plan("list built-in strategies", response_style="raw", persist="none")
            runs = store.list_runs()
            print("\n[TestAiRunPolicy] persist none payload:", payload)
            print(" runs:", runs)
            self.assertEqual(payload.get("run_file", ""), "")
            self.assertEqual(runs, [])


if __name__ == "__main__":
    unittest.main()
