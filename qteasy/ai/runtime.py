# coding=utf-8
# ======================================
# File: runtime.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-16
# Desc:
# qteasy AI 外壳技能运行时，负责 precheck、
# side-effects 门控与统一错误封装。
# ======================================

"""SkillRuntime v2 最小实现。"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from .contracts import SkillMetadata


class SkillRuntime:
    """统一技能调用前后处理逻辑。"""

    def side_effect_level(self, metadata: SkillMetadata) -> str:
        """返回副作用等级。"""

        side_effects = metadata.side_effects
        if side_effects.local_state_change or side_effects.filesystem_write:
            return "high"
        if side_effects.network or side_effects.heavy_compute:
            return "medium"
        return "low"

    def precheck(self, metadata: SkillMetadata, kwargs: Dict[str, Any]) -> List[str]:
        """执行最小 precheck。"""

        missing_fields: List[str] = []
        for field_name, field_schema in metadata.inputs_schema.items():
            if not isinstance(field_schema, dict):
                continue
            if field_schema.get("required") and field_name not in kwargs:
                missing_fields.append(field_name)
        return missing_fields

    def execute(
        self,
        *,
        metadata: SkillMetadata,
        handler: Callable[..., Dict[str, Any]],
        kwargs: Dict[str, Any],
        confirmed: bool = True,
    ) -> Dict[str, Any]:
        """执行技能并返回统一结构。"""

        missing_fields = self.precheck(metadata, kwargs)
        if missing_fields:
            return {
                "ok": False,
                "skill_name": metadata.name,
                "warnings": [],
                "error": {
                    "code": "SKILL_PRECHECK_FAILED",
                    "message": "Missing required skill inputs.",
                    "details": {"missing_fields": missing_fields},
                },
                "rollback_hint": "Check inputs_schema and provide required fields.",
            }

        side_level = self.side_effect_level(metadata)
        if side_level == "high" and not confirmed:
            return {
                "ok": False,
                "skill_name": metadata.name,
                "warnings": [],
                "error": {
                    "code": "SKILL_CONFIRM_REQUIRED",
                    "message": "High side-effect skill requires explicit confirmation.",
                    "details": {"side_effect_level": side_level},
                },
                "rollback_hint": "Switch to plan mode for explicit user confirmation.",
            }

        try:
            result = handler(**kwargs)
        except Exception as exc:
            return {
                "ok": False,
                "skill_name": metadata.name,
                "warnings": [],
                "error": {
                    "code": "SKILL_HANDLER_FAILED",
                    "message": str(exc),
                    "details": {"side_effect_level": side_level},
                },
                "rollback_hint": "Review runtime logs and handler implementation.",
            }

        if not isinstance(result, dict):
            return {
                "ok": False,
                "skill_name": metadata.name,
                "warnings": [],
                "error": {
                    "code": "SKILL_INVALID_OUTPUT",
                    "message": "Skill handler must return dict payload.",
                    "details": {"actual_type": type(result).__name__},
                },
                "rollback_hint": "Update skill handler return contract.",
            }
        result.setdefault("skill_name", metadata.name)
        result.setdefault("rollback_hint", "")
        return result

