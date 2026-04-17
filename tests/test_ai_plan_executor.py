# coding=utf-8
# ======================================
# File: test_ai_plan_executor.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# Unittest for qteasy ai plan executor
# ======================================

import tempfile
import unittest

from qteasy.ai.contracts import SkillMetadata, SkillSideEffects, ToolPlan, ToolStep
from qteasy.ai.executor import PlanExecutor
from qteasy.ai.memory_store import MemoryStore
from qteasy.ai.registry import SkillRegistry


class TestAiPlanExecutor(unittest.TestCase):
    """测试 PlanExecutor 的 dry_run 和执行流程。"""

    def test_dry_run_and_execute(self) -> None:
        """验证 dry_run 与 confirm 执行的记录落盘。"""

        registry = SkillRegistry()
        metadata = SkillMetadata(
            name="qt.ai.test.step",
            version="0.1.0",
            summary="Test step",
            inputs_schema={"x": {"type": "int"}},
            outputs_schema={"ok": "bool"},
            side_effects=SkillSideEffects(description="readonly"),
        )
        registry.register(metadata, lambda x=1: {"ok": True, "value": x})

        with tempfile.TemporaryDirectory() as temp_dir:
            store = MemoryStore(base_dir=temp_dir)
            executor = PlanExecutor(registry=registry, memory_store=store)
            step = ToolStep(step_id="step_1", skill_name=metadata.name, inputs={"x": 3})
            plan = ToolPlan(plan_id="plan_demo", user_query="demo", steps=[step], execution_mode="dry_run")

            dry_payload = executor.execute(plan, confirm=False)
            plan.execution_mode = "execute"
            run_payload = executor.execute(plan, confirm=True)

            print("\n[TestAiPlanExecutor] dry run status:", dry_payload["execution"]["status"])
            print(" run status:", run_payload["execution"]["status"])
            print(" run file:", run_payload["run_file"])

            self.assertEqual(dry_payload["execution"]["status"], "dry_run")
            self.assertEqual(run_payload["execution"]["status"], "success")
            self.assertTrue(run_payload["execution"]["steps"][0]["result"]["ok"])


if __name__ == "__main__":
    unittest.main()
