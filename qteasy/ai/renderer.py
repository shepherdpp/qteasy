# coding=utf-8
# ======================================
# File: renderer.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-20
# Desc:
# qteasy AI 输出渲染层，将结构化 raw
# payload 转换为用户友好的多通道输出。
# ======================================

"""输出渲染层。"""

from __future__ import annotations

from typing import Any, Dict, List

from .output import AssistantOutput


class OutputRenderer:
    """将 raw payload 渲染为用户输出。"""

    def render(self, payload: Dict[str, Any], *, style: str = "user_friendly", context: Dict[str, Any] | None = None) -> AssistantOutput:
        """渲染输出。

        Parameters
        ----------
        payload : Dict[str, Any]
            执行层原始结果。
        style : str
            输出风格，目前支持 `user_friendly`。
        context : Dict[str, Any], optional
            额外上下文信息。
        """

        if style != "user_friendly":
            return AssistantOutput(
                narrative="Raw payload returned.",
                python_code="",
                result_preview="Use raw payload directly.",
                raw=payload,
            )

        plan = payload.get("plan", {})
        steps: List[Dict[str, Any]] = plan.get("steps", [])
        first_skill = steps[0].get("skill_name", "") if steps else ""
        execution = payload.get("execution", {})
        execution_steps = execution.get("steps", [])
        first_result = execution_steps[0].get("result", {}) if execution_steps else {}

        if first_skill == "qt.ai.strategy_meta.list":
            return self._render_strategy_meta_list(payload, first_result)
        if first_skill == "qt.ai.strategy_meta.get":
            return self._render_strategy_meta_get(payload, first_result)
        if first_skill == "qt.ai.data.summary_kline":
            return self._render_data_summary(payload, first_result)
        if first_skill == "qt.ai.visual.export_kline":
            return self._render_visual_export(payload, first_result)
        if first_skill == "qt.ai.system.fallback":
            return self._render_fallback(payload, first_result)
        return self._render_generic(payload, first_skill, first_result)

    @staticmethod
    def _render_strategy_meta_list(payload: Dict[str, Any], result: Dict[str, Any]) -> AssistantOutput:
        count = result.get("metrics", {}).get("count", 0)
        preview_items = result.get("payload", {}).get("strategies", [])[:15]
        narrative = f"Listed built-in strategies successfully. Total count: {count}."
        python_code = "import qteasy as qt\nstrategies = qt.built_in_list()\nprint(len(strategies), strategies[:15])"
        result_preview = f"First strategies: {preview_items}"
        return AssistantOutput(narrative=narrative, python_code=python_code, result_preview=result_preview, raw=payload)

    @staticmethod
    def _render_strategy_meta_get(payload: Dict[str, Any], result: Dict[str, Any]) -> AssistantOutput:
        strategy_id = result.get("payload", {}).get("strategy_id", "unknown")
        strategy_type = result.get("payload", {}).get("strategy_type", "unknown")
        narrative = f"Fetched built-in strategy details for {strategy_id} ({strategy_type})."
        python_code = (
            "import qteasy as qt\n"
            f"doc = qt.built_in_doc('{strategy_id}')\n"
            f"obj = qt.get_built_in_strategy('{strategy_id}')\n"
            "print(type(obj).__name__)\nprint(doc[:300])"
        )
        result_preview = f"strategy_id={strategy_id}, strategy_type={strategy_type}"
        return AssistantOutput(narrative=narrative, python_code=python_code, result_preview=result_preview, raw=payload)

    @staticmethod
    def _render_data_summary(payload: Dict[str, Any], result: Dict[str, Any]) -> AssistantOutput:
        metrics = result.get("metrics", {})
        n_rows = metrics.get("n_rows", 0)
        min_price = metrics.get("close_min", "N/A")
        max_price = metrics.get("close_max", "N/A")
        narrative = f"Kline summary completed. Rows={n_rows}, close range=[{min_price}, {max_price}]."
        python_code = (
            "import qteasy as qt\n"
            "k = qt.get_kline(shares='000300.SH', start='20240101', end='20241231', freq='D', as_panel=False)\n"
            "print(k.shape)\nprint(k[['close']].describe())"
        )
        result_preview = f"metrics={metrics}"
        return AssistantOutput(narrative=narrative, python_code=python_code, result_preview=result_preview, raw=payload)

    @staticmethod
    def _render_visual_export(payload: Dict[str, Any], result: Dict[str, Any]) -> AssistantOutput:
        artifacts = result.get("artifacts", [])
        output_path = artifacts[0].get("path", "") if artifacts else ""
        narrative = f"Kline chart export completed. Output saved to: {output_path}"
        python_code = (
            "from qteasy.ai.skills.visual_export import build_visual_export_skill\n"
            "meta, export = build_visual_export_skill()\n"
            "res = export(shares='000300.SH', freq='D')\n"
            "print(res['artifacts'])"
        )
        result_preview = f"artifacts={artifacts}"
        return AssistantOutput(narrative=narrative, python_code=python_code, result_preview=result_preview, raw=payload)

    @staticmethod
    def _render_fallback(payload: Dict[str, Any], result: Dict[str, Any]) -> AssistantOutput:
        action = result.get("payload", {}).get("fallback_action", "not_supported_yet")
        hint = result.get("payload", {}).get("hint", "")
        narrative = f"Request cannot be executed directly in current stage. Fallback action: {action}."
        python_code = "# Please refine your request into smaller executable steps."
        result_preview = hint
        return AssistantOutput(narrative=narrative, python_code=python_code, result_preview=result_preview, raw=payload)

    @staticmethod
    def _render_generic(payload: Dict[str, Any], skill_name: str, result: Dict[str, Any]) -> AssistantOutput:
        ok = result.get("ok", False)
        narrative = f"Execution finished for skill: {skill_name}. ok={ok}."
        python_code = "# Raw result available in output.raw"
        result_preview = str(result)[:500]
        return AssistantOutput(narrative=narrative, python_code=python_code, result_preview=result_preview, raw=payload)

