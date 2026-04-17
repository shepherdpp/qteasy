# coding=utf-8
# ======================================
# File: test_ai_memory_store.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# Unittest for qteasy ai memory store
# ======================================

import tempfile
import unittest

from qteasy.ai.memory_store import MemoryStore


class TestAiMemoryStore(unittest.TestCase):
    """测试 profile/env_facts/runs 最小落盘。"""

    def test_memory_read_write_cycle(self) -> None:
        """验证记忆文件读写和 runs 列表。"""

        with tempfile.TemporaryDirectory() as temp_dir:
            store = MemoryStore(base_dir=temp_dir)
            store.save_profile({"favorite_symbol": "000300.SH"})
            store.save_env_facts({"python": "3.9"})
            run_path = store.save_run("run_demo", {"status": "ok"})
            profile = store.load_profile()
            env_facts = store.load_env_facts()
            run_data = store.load_run("run_demo")
            run_ids = store.list_runs()

            print("\n[TestAiMemoryStore] run path:", run_path)
            print(" profile:", profile)
            print(" env_facts:", env_facts)
            print(" run_ids:", run_ids)

            self.assertEqual(profile["favorite_symbol"], "000300.SH")
            self.assertEqual(env_facts["python"], "3.9")
            self.assertEqual(run_data["status"], "ok")
            self.assertIn("run_demo", run_ids)


if __name__ == "__main__":
    unittest.main()
