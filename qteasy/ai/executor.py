# coding=utf-8
# ======================================
# File: executor.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# qteasy AI 外壳执行层，负责计划执行、
# 异常标准化与 run 记录落盘。
# ======================================

"""ToolPlan 执行器。

执行器职责边界：
- 接收已经生成好的 ToolPlan；
- 按 dry_run / execute 模式处理；
- 把执行过程标准化落盘到 runs，保证可追溯。

注意：本模块不负责“如何规划”与“如何渲染结果”，只负责执行与记录。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Set

from .contracts import (
    PlanExecutionRecord,
    PlanStepRecord,
    ToolPlan,
    ToolStep,
    new_run_id,
)
from .memory_store import MemoryStore
from .registry import SkillRegistry


def _utc_now_iso() -> str:
    """返回 UTC 时间字符串。"""

    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class PlanExecutor:
    """执行 plan 并记录结果。

    Parameters
    ----------
    registry : SkillRegistry
        技能注册中心，负责实际调用技能实现。
    memory_store : MemoryStore
        本地记忆存储，负责 run 记录持久化。
    """

    def __init__(self, registry: SkillRegistry, memory_store: MemoryStore) -> None:
        self.registry = registry
        self.memory_store = memory_store

    def execute(self, plan: ToolPlan, *, confirm: bool = False) -> Dict[str, Any]:
        """执行计划，支持 dry_run 与 execute。

        Parameters
        ----------
        plan : ToolPlan
            待执行计划。
        confirm : bool, default False
            是否确认执行。即使 plan 为 execute，当 confirm=False 时也会按 dry_run 返回。

        Returns
        -------
        Dict[str, Any]
            包含 `plan`、`execution`、`run_id`、`run_file` 的统一结果。
        """

        run_id = new_run_id()
        created_at = _utc_now_iso()
        if plan.execution_mode == "dry_run" or not confirm:
            # 统一 dry_run 语义：只产出计划与占位执行记录，不真正触发技能调用。
            record = PlanExecutionRecord(
                run_id=run_id,
                plan_id=plan.plan_id,
                status="dry_run",
                mode=plan.mode,
                created_at=created_at,
                steps=[],
                summary={"message": "Plan generated; waiting for confirmation."},
            )
            payload = {
                "run_id": run_id,
                "plan": self._plan_to_dict(plan),
                "execution": self._execution_to_dict(record),
            }
            run_file = self.memory_store.save_run(run_id, payload)
            payload["run_file"] = run_file
            return payload

        # execute 分支：按最小 DAG 规则执行（depends_on/run_if/on_fail/retry_limit）。
        step_records: List[PlanStepRecord] = []
        all_ok = True
        completed_ids: Set[str] = set()
        step_results: Dict[str, Dict[str, Any]] = {}
        pending_steps = {step.step_id: step for step in plan.steps}
        ordered_steps = [step.step_id for step in plan.steps]
        abort_execution = False

        while pending_steps and not abort_execution:
            progressed = False
            for step_id in ordered_steps:
                step = pending_steps.get(step_id)
                if step is None:
                    continue
                if any(dep_id not in completed_ids for dep_id in step.depends_on):
                    continue
                progressed = True
                pending_steps.pop(step_id, None)
                started_at = _utc_now_iso()
                if not self._evaluate_run_if(step.run_if, step.depends_on, step_results):
                    result = {
                        "ok": True,
                        "skill_name": step.skill_name,
                        "warnings": [],
                        "error": None,
                        "skipped": True,
                        "skip_reason": "run_if condition not satisfied",
                    }
                    ended_at = _utc_now_iso()
                    step_records.append(
                        PlanStepRecord(
                            step_id=step.step_id,
                            skill_name=step.skill_name,
                            started_at=started_at,
                            ended_at=ended_at,
                            result=result,
                        )
                    )
                    completed_ids.add(step_id)
                    step_results[step_id] = result
                    continue

                result = self._execute_step_with_retry(step=step, confirm=confirm)
                ended_at = _utc_now_iso()
                step_records.append(
                    PlanStepRecord(
                        step_id=step.step_id,
                        skill_name=step.skill_name,
                        started_at=started_at,
                        ended_at=ended_at,
                        result=result,
                    )
                )
                completed_ids.add(step_id)
                step_results[step_id] = result

                if not result.get("ok", False):
                    all_ok = False
                    if step.on_fail == "stop":
                        abort_execution = True
                        break
            if not progressed and pending_steps:
                all_ok = False
                cycle_step_ids = list(pending_steps.keys())
                for cycle_step_id in cycle_step_ids:
                    step = pending_steps[cycle_step_id]
                    started_at = _utc_now_iso()
                    ended_at = _utc_now_iso()
                    result = {
                        "ok": False,
                        "skill_name": step.skill_name,
                        "warnings": [],
                        "error": {
                            "code": "EXECUTOR_DAG_BLOCKED",
                            "message": "Unresolved dependencies or cycle detected.",
                            "details": {
                                "step_id": step.step_id,
                                "depends_on": step.depends_on,
                            },
                        },
                    }
                    step_records.append(
                        PlanStepRecord(
                            step_id=step.step_id,
                            skill_name=step.skill_name,
                            started_at=started_at,
                            ended_at=ended_at,
                            result=result,
                        )
                    )
                    step_results[cycle_step_id] = result
                    completed_ids.add(cycle_step_id)
                pending_steps.clear()

        status = "success" if all_ok else "partial_failed"
        # summary 只放轻量汇总，详情在 steps 中按原样保留，便于上层按需展示。
        record = PlanExecutionRecord(
            run_id=run_id,
            plan_id=plan.plan_id,
            status=status,
            mode=plan.mode,
            created_at=created_at,
            steps=step_records,
            summary={
                "step_count": len(step_records),
                "ok_count": sum(1 for item in step_records if item.result.get("ok")),
            },
        )
        payload = {
            "run_id": run_id,
            "plan": self._plan_to_dict(plan),
            "execution": self._execution_to_dict(record),
        }
        run_file = self.memory_store.save_run(run_id, payload)
        payload["run_file"] = run_file
        return payload

    @staticmethod
    def _plan_to_dict(plan: ToolPlan) -> Dict[str, Any]:
        """将 plan 转换为字典。

        这里显式展开 side_effects，是为了让前端无需感知 dataclass
        也能直接读取风险标签并展示给用户。
        """

        return {
            "plan_id": plan.plan_id,
            "user_query": plan.user_query,
            "execution_mode": plan.execution_mode,
            "mode": plan.mode,
            "assumptions": plan.assumptions,
            "planner_trace": plan.planner_trace,
            "created_at": plan.created_at,
            "steps": [
                {
                    "step_id": step.step_id,
                    "skill_name": step.skill_name,
                    "inputs": step.inputs,
                    "depends_on": step.depends_on,
                    "run_if": step.run_if,
                    "on_fail": step.on_fail,
                    "retry_limit": step.retry_limit,
                    "estimated_cost": step.estimated_cost,
                    "side_effects": {
                        "network": step.side_effects.network,
                        "filesystem_write": step.side_effects.filesystem_write,
                        "local_state_change": step.side_effects.local_state_change,
                        "heavy_compute": step.side_effects.heavy_compute,
                        "description": step.side_effects.description,
                    },
                }
                for step in plan.steps
            ],
        }

    def _execute_step_with_retry(self, *, step: ToolStep, confirm: bool) -> Dict[str, Any]:
        """按 on_fail/retry_limit 执行单步。"""

        max_attempts = 1
        if step.on_fail == "retry":
            max_attempts = max(1, int(step.retry_limit) + 1)
        last_result: Dict[str, Any] = {}
        for attempt in range(1, max_attempts + 1):
            try:
                result = self.registry.call(step.skill_name, confirmed=confirm, **step.inputs)
            except Exception as exc:
                result = {
                    "ok": False,
                    "skill_name": step.skill_name,
                    "warnings": [],
                    "error": {
                        "code": "EXECUTOR_STEP_FAILED",
                        "message": str(exc),
                        "details": {"step_id": step.step_id, "attempt": attempt},
                    },
                }
            result["attempt"] = attempt
            last_result = result
            if result.get("ok", False):
                return result
        return last_result

    @staticmethod
    def _evaluate_run_if(run_if: str, depends_on: List[str], step_results: Dict[str, Dict[str, Any]]) -> bool:
        """评估最小 run_if 语义。"""

        if not run_if:
            return True
        if run_if == "all_dependencies_ok":
            return all(step_results.get(dep_id, {}).get("ok", False) for dep_id in depends_on)
        if run_if == "any_dependency_failed":
            return any(not step_results.get(dep_id, {}).get("ok", True) for dep_id in depends_on)
        if run_if == "always":
            return True
        # 未知表达式默认降级为不执行，避免潜在风险。
        return False

    @staticmethod
    def _execution_to_dict(record: PlanExecutionRecord) -> Dict[str, Any]:
        """将执行记录转换为字典。

        执行记录使用“扁平可读”结构，便于：
        - CLI 直接 JSON 输出；
        - runs 文件直接被外部脚本消费；
        - 后续接入 Web/TUI 时减少转换成本。
        """

        return {
            "run_id": record.run_id,
            "plan_id": record.plan_id,
            "status": record.status,
            "mode": record.mode,
            "created_at": record.created_at,
            "summary": record.summary,
            "steps": [
                {
                    "step_id": step.step_id,
                    "skill_name": step.skill_name,
                    "started_at": step.started_at,
                    "ended_at": step.ended_at,
                    "result": step.result,
                }
                for step in record.steps
            ],
        }
