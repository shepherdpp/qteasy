# coding=utf-8
# ======================================
# File: system_fallback.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-20
# Desc:
# qteasy AI 系统回退技能：为未实现能力、
# 需澄清请求或仅计划模式提供统一响应。
# ======================================

"""系统回退技能。"""

from __future__ import annotations

from typing import Callable

from ..contracts import SkillError, SkillMetadata, SkillResult, SkillSideEffects, new_run_id


def build_system_fallback_skill() -> tuple[SkillMetadata, Callable[..., dict]]:
    """构建统一回退技能。"""

    metadata = SkillMetadata(
        name="qt.ai.system.fallback",
        version="0.1.0",
        summary="Return structured fallback response for unsupported intents.",
        inputs_schema={
            "query": {"type": "string", "required": True},
            "fallback_action": {"type": "string", "required": True},
            "reason": {"type": "string", "required": True},
            "hint": {"type": "string", "required": False},
        },
        outputs_schema={"payload": "dict", "error": "dict"},
        side_effects=SkillSideEffects(description="readonly"),
        required_capabilities=[],
        qteasy_entrypoints=[],
    )

    def handler(
        query: str,
        fallback_action: str,
        reason: str,
        hint: str = "",
        **kwargs,
    ) -> dict:
        run_id = new_run_id()
        action_code_map = {
            "plan_only": "PLAN_ONLY",
            "not_supported_yet": "NOT_SUPPORTED_YET",
            "clarify_required": "CLARIFY_REQUIRED",
        }
        error_code = action_code_map.get(fallback_action, "NOT_SUPPORTED_YET")
        result = SkillResult(
            ok=False,
            skill_name=metadata.name,
            run_id=run_id,
            inputs_echo={
                "query": query,
                "fallback_action": fallback_action,
                "reason": reason,
                "hint": hint,
                **kwargs,
            },
            error=SkillError(
                code=error_code,
                message=hint or "Request cannot be executed in current stage.",
                details={
                    "fallback_action": fallback_action,
                    "reason": reason,
                },
            ),
            payload={
                "fallback_action": fallback_action,
                "reason": reason,
                "hint": hint,
            },
        )
        return {
            "ok": result.ok,
            "skill_name": result.skill_name,
            "run_id": result.run_id,
            "inputs_echo": result.inputs_echo,
            "metrics": result.metrics,
            "data_summary": result.data_summary,
            "payload": result.payload,
            "warnings": result.warnings,
            "error": None if result.error is None else result.error.__dict__,
            "artifacts": result.artifacts,
        }

    return metadata, handler

