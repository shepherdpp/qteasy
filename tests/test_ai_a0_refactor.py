# coding=utf-8
# ======================================
# File: test_ai_a0_refactor.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-16
# Desc:
# Unittest for qteasy ai A0 refactor
# ======================================

import tempfile
import unittest

from qteasy.ai.config import ConfigCenter
from qteasy.ai.contracts import SkillMetadata, SkillSideEffects, ToolPlan, ToolStep
from qteasy.ai.executor import PlanExecutor
from qteasy.ai.memory_store import MemoryStore
from qteasy.ai.planner import Planner
from qteasy.ai.registry import SkillRegistry
from qteasy.ai.runtime import SkillRuntime


class TestAiA0Refactor(unittest.TestCase):
    """测试 A0 局部重构核心契约。"""

    def test_config_center_priority(self) -> None:
        """验证 ConfigCenter 读取优先级。"""

        center = ConfigCenter(env={"QTEASY_AI_MODEL": "model_from_env"}, qt_config={"ai_model": "model_from_qt"})
        value_explicit = center.resolve(
            "model",
            explicit="model_from_explicit",
            env_key="QTEASY_AI_MODEL",
            qt_key="ai_model",
            default="model_default",
        )
        value_env = center.resolve(
            "model",
            explicit=None,
            env_key="QTEASY_AI_MODEL",
            qt_key="ai_model",
            default="model_default",
        )
        value_qt = ConfigCenter(env={}, qt_config={"ai_model": "model_from_qt"}).resolve(
            "model",
            explicit=None,
            env_key="QTEASY_AI_MODEL",
            qt_key="ai_model",
            default="model_default",
        )
        value_default = ConfigCenter(env={}, qt_config={}).resolve(
            "model",
            explicit=None,
            env_key="QTEASY_AI_MODEL",
            qt_key="ai_model",
            default="model_default",
        )

        print("\n[TestAiA0Refactor] config values:", value_explicit, value_env, value_qt, value_default)
        self.assertEqual(value_explicit, "model_from_explicit")
        self.assertEqual(value_env, "model_from_env")
        self.assertEqual(value_qt, "model_from_qt")
        self.assertEqual(value_default, "model_default")

    def test_planner_hybrid_trace(self) -> None:
        """验证 Planner 三段式输出包含 planner_trace。"""

        registry = SkillRegistry()
        metadata = SkillMetadata(
            name="qt.ai.data.summary_kline",
            version="0.1.0",
            summary="summary",
            inputs_schema={},
            outputs_schema={},
            side_effects=SkillSideEffects(),
        )
        registry.register(metadata, lambda **_: {"ok": True})
        planner = Planner(registry=registry)
        plan = planner.build_plan("show me 000001")

        print("\n[TestAiA0Refactor] planner trace:", plan.planner_trace)
        self.assertIn("candidate_plan_id", plan.planner_trace)
        self.assertIn("validator_trace", plan.planner_trace)
        self.assertEqual(plan.planner_trace["final_step_count"], len(plan.steps))

    def test_skill_runtime_gate(self) -> None:
        """验证 SkillRuntime precheck 与高副作用门控。"""

        runtime = SkillRuntime()
        metadata = SkillMetadata(
            name="qt.ai.data.refill",
            version="0.1.0",
            summary="refill",
            inputs_schema={"table": {"type": "string", "required": True}},
            outputs_schema={"ok": "bool"},
            side_effects=SkillSideEffects(filesystem_write=True),
        )
        result_missing = runtime.execute(metadata=metadata, handler=lambda **_: {"ok": True}, kwargs={}, confirmed=True)
        result_gate = runtime.execute(
            metadata=metadata,
            handler=lambda **_: {"ok": True},
            kwargs={"table": "stock_daily"},
            confirmed=False,
        )

        print("\n[TestAiA0Refactor] runtime missing:", result_missing)
        print(" runtime gate:", result_gate)
        self.assertFalse(result_missing["ok"])
        self.assertEqual(result_missing["error"]["code"], "SKILL_PRECHECK_FAILED")
        self.assertFalse(result_gate["ok"])
        self.assertEqual(result_gate["error"]["code"], "SKILL_CONFIRM_REQUIRED")

    def test_executor_min_dag(self) -> None:
        """验证最小 DAG 字段执行与失败策略。"""

        registry = SkillRegistry()
        metadata_ok = SkillMetadata(
            name="qt.ai.test.ok",
            version="0.1.0",
            summary="ok",
            inputs_schema={},
            outputs_schema={},
            side_effects=SkillSideEffects(),
        )
        metadata_fail = SkillMetadata(
            name="qt.ai.test.fail",
            version="0.1.0",
            summary="fail",
            inputs_schema={},
            outputs_schema={},
            side_effects=SkillSideEffects(),
        )
        registry.register(metadata_ok, lambda **_: {"ok": True, "value": 1})
        registry.register(metadata_fail, lambda **_: {"ok": False, "error": {"code": "FAIL"}})

        step1 = ToolStep(step_id="step_1", skill_name="qt.ai.test.fail", inputs={}, on_fail="continue")
        step2 = ToolStep(
            step_id="step_2",
            skill_name="qt.ai.test.ok",
            inputs={},
            depends_on=["step_1"],
            run_if="any_dependency_failed",
            on_fail="stop",
        )
        plan = ToolPlan(
            plan_id="plan_dag",
            user_query="dag",
            steps=[step1, step2],
            execution_mode="execute",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            store = MemoryStore(base_dir=temp_dir)
            executor = PlanExecutor(registry=registry, memory_store=store)
            payload = executor.execute(plan, confirm=True)

        steps = payload["execution"]["steps"]
        print("\n[TestAiA0Refactor] dag status:", payload["execution"]["status"])
        print(" steps:", steps)
        self.assertEqual(len(steps), 2)
        self.assertFalse(steps[0]["result"]["ok"])
        self.assertTrue(steps[1]["result"]["ok"])

    def test_executor_retry_policy(self) -> None:
        """验证 on_fail=retry 与 retry_limit 生效。"""

        registry = SkillRegistry()
        metadata_retry = SkillMetadata(
            name="qt.ai.test.retry",
            version="0.1.0",
            summary="retry",
            inputs_schema={},
            outputs_schema={},
            side_effects=SkillSideEffects(),
        )
        state = {"count": 0}

        def flaky_handler(**_) -> dict:
            state["count"] += 1
            if state["count"] < 3:
                return {"ok": False, "error": {"code": "TEMP_FAIL"}}
            return {"ok": True, "value": state["count"]}

        registry.register(metadata_retry, flaky_handler)
        step = ToolStep(
            step_id="step_retry",
            skill_name="qt.ai.test.retry",
            inputs={},
            on_fail="retry",
            retry_limit=3,
        )
        plan = ToolPlan(plan_id="plan_retry", user_query="retry", steps=[step], execution_mode="execute")

        with tempfile.TemporaryDirectory() as temp_dir:
            store = MemoryStore(base_dir=temp_dir)
            executor = PlanExecutor(registry=registry, memory_store=store)
            payload = executor.execute(plan, confirm=True)

        step_result = payload["execution"]["steps"][0]["result"]
        print("\n[TestAiA0Refactor] retry count:", state["count"])
        print(" retry result:", step_result)
        self.assertEqual(state["count"], 3)
        self.assertTrue(step_result["ok"])
        self.assertEqual(step_result["attempt"], 3)


if __name__ == "__main__":
    unittest.main()

