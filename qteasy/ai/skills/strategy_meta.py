# coding=utf-8
# ======================================
# File: strategy_meta.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# qteasy AI 阶段A只读技能：内置策略元数据查询。
# ======================================

"""内置策略元数据只读技能。"""

from __future__ import annotations

from typing import Callable, Dict

from ..contracts import SkillError, SkillMetadata, SkillResult, SkillSideEffects, new_run_id


def build_strategy_meta_list_skill(
    list_func: Callable[[], list] | None = None,
) -> tuple[SkillMetadata, Callable[..., dict]]:
    """构建策略列表技能。"""

    if list_func is None:
        import qteasy as qt

        list_func = qt.built_in_list

    metadata = SkillMetadata(
        name="qt.ai.strategy_meta.list",
        version="0.1.0",
        summary="List built-in strategies.",
        inputs_schema={},
        outputs_schema={"strategies": "list[str]"},
        side_effects=SkillSideEffects(description="readonly"),
        required_capabilities=[],
        qteasy_entrypoints=["qteasy.built_in_list"],
    )

    def handler(**kwargs) -> dict:
        run_id = new_run_id()
        try:
            strategies = list_func()
            result = SkillResult(
                ok=True,
                skill_name=metadata.name,
                run_id=run_id,
                inputs_echo=kwargs,
                payload={"strategies": strategies},
                metrics={"count": len(strategies)},
                data_summary={"first_items": strategies[:10]},
            )
        except Exception as exc:
            result = SkillResult(
                ok=False,
                skill_name=metadata.name,
                run_id=run_id,
                inputs_echo=kwargs,
                error=SkillError(
                    code="STRATEGY_LIST_FAILED",
                    message=f"Failed to list built-in strategies: {exc}",
                ),
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


def build_strategy_meta_get_skill(
    doc_func: Callable[[str], str] | None = None,
    get_func: Callable[[str], object] | None = None,
) -> tuple[SkillMetadata, Callable[..., dict]]:
    """构建策略详情技能。"""

    if doc_func is None or get_func is None:
        import qteasy as qt

        doc_func = doc_func or qt.built_in_doc
        get_func = get_func or qt.get_built_in_strategy

    metadata = SkillMetadata(
        name="qt.ai.strategy_meta.get",
        version="0.1.0",
        summary="Get built-in strategy details.",
        inputs_schema={"strategy_id": {"type": "string", "required": True}},
        outputs_schema={"strategy_meta": "dict"},
        side_effects=SkillSideEffects(description="readonly"),
        required_capabilities=[],
        qteasy_entrypoints=["qteasy.built_in_doc", "qteasy.get_built_in_strategy"],
    )

    def handler(strategy_id: str, **kwargs) -> dict:
        run_id = new_run_id()
        sid = strategy_id.strip()
        try:
            strategy_obj = get_func(sid)
            strategy_doc = doc_func(sid)
            payload: Dict[str, object] = {
                "strategy_id": sid,
                "strategy_type": strategy_obj.__class__.__name__,
                "doc": strategy_doc,
            }
            result = SkillResult(
                ok=True,
                skill_name=metadata.name,
                run_id=run_id,
                inputs_echo={"strategy_id": sid, **kwargs},
                payload=payload,
                metrics={"doc_length": len(strategy_doc)},
                data_summary={"strategy_type": strategy_obj.__class__.__name__},
            )
        except Exception as exc:
            result = SkillResult(
                ok=False,
                skill_name=metadata.name,
                run_id=run_id,
                inputs_echo={"strategy_id": sid, **kwargs},
                error=SkillError(
                    code="STRATEGY_GET_FAILED",
                    message=f"Failed to get strategy details: {exc}",
                ),
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
