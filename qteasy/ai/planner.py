# coding=utf-8
# ======================================
# File: planner.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# qteasy AI 外壳规划层，负责将用户
# 请求转换为结构化 ToolPlan。
# ======================================

"""自然语言到 ToolPlan 的 Hybrid 最小实现。

A0 目标是打通 Planner 三段式链路：

1. `build_candidate_plan()`：候选计划生成（当前以规则为主，Provider 可选）；
2. `validate_plan()`：规则校验、字段归一与风险门控；
3. `finalize_plan()`：生成可执行计划并附加 `planner_trace`。
"""

from __future__ import annotations

import datetime
import re
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from .contracts import SkillSideEffects, ToolPlan, ToolStep, new_plan_id
from .provider import BaseLLMProvider
from .registry import SkillRegistry


class RuleValidator:
    """Planner 规则校验器。"""

    def __init__(self, registry: SkillRegistry) -> None:
        self.registry = registry

    def validate(self, candidate_plan: ToolPlan) -> Tuple[ToolPlan, Dict[str, Any]]:
        """校验并返回修订后的计划。"""

        corrected = deepcopy(candidate_plan)
        available_skills = {item.name for item in self.registry.list_skills()}
        trace: Dict[str, Any] = {
            "validator": "rule_validator_v2",
            "corrections": [],
            "downgrade_reason": "",
        }
        corrected_steps: List[ToolStep] = []
        for step in corrected.steps:
            if step.skill_name not in available_skills:
                trace["downgrade_reason"] = f"Skill not found: {step.skill_name}"
                continue
            meta = self.registry.get_metadata(step.skill_name)
            if step.side_effects != meta.side_effects:
                step.side_effects = meta.side_effects
                trace["corrections"].append(
                    {
                        "step_id": step.step_id,
                        "field": "side_effects",
                        "reason": "sync_from_registry_metadata",
                    }
                )
            if step.on_fail not in {"stop", "continue", "retry"}:
                trace["corrections"].append(
                    {
                        "step_id": step.step_id,
                        "field": "on_fail",
                        "from": step.on_fail,
                        "to": "stop",
                    }
                )
                step.on_fail = "stop"
            if step.on_fail != "retry" and step.retry_limit > 0:
                trace["corrections"].append(
                    {
                        "step_id": step.step_id,
                        "field": "retry_limit",
                        "from": step.retry_limit,
                        "to": 0,
                    }
                )
                step.retry_limit = 0
            corrected_steps.append(step)
        if not corrected_steps and corrected.mode == "plan":
            trace["downgrade_reason"] = trace["downgrade_reason"] or "No valid step after validation."
        corrected.steps = corrected_steps
        return corrected, trace


class Planner:
    """阶段A计划生成器。

    Parameters
    ----------
    registry : SkillRegistry
        技能注册中心，用于读取技能元数据（尤其是 side_effects）。
    provider : BaseLLMProvider, optional
        模型提供方抽象。阶段A中仅用于记录是否启用，不参与计划生成。
    """

    def __init__(self, registry: SkillRegistry, provider: Optional[BaseLLMProvider] = None) -> None:
        self.registry = registry
        self.provider = provider
        self.validator = RuleValidator(registry)

    def build_plan(self, user_query: str, *, mode: str = "plan") -> ToolPlan:
        """Hybrid 三段式入口，生成最终可执行计划。

        Returns
        -------
        ToolPlan
            已附带 `planner_trace` 的可执行计划对象。
        """

        candidate = self.build_candidate_plan(user_query, mode=mode)
        validated, trace = self.validate_plan(candidate)
        return self.finalize_plan(candidate, validated, trace)

    def build_candidate_plan(self, user_query: str, *, mode: str = "plan") -> ToolPlan:
        """生成候选计划。

        Parameters
        ----------
        user_query : str
            用户自然语言请求。
        mode : {'plan', 'ask'}
            Ask 模式下不执行技能，仅返回空步骤计划；
            Plan 模式下按规则推断技能与输入参数。

        Returns
        -------
        ToolPlan
            候选计划。
        """

        if mode == "ask":
            steps = []
            assumptions: Dict[str, Any] = {"mode": "ask", "no_skill_execution": True}
            return ToolPlan(
                plan_id=new_plan_id(),
                user_query=user_query,
                steps=steps,
                assumptions=assumptions,
                execution_mode="dry_run",
                mode="ask",
            )

        query = user_query.strip()
        q_lower = query.lower()
        step = self._infer_single_step(query=query, q_lower=q_lower)
        assumptions = {
            "planner": "hybrid_candidate_stage_a0",
            "provider_enabled": self.provider is not None,
        }
        return ToolPlan(
            plan_id=new_plan_id(),
            user_query=user_query,
            steps=[step],
            assumptions=assumptions,
            execution_mode="dry_run",
            mode="plan",
        )

    def validate_plan(self, candidate_plan: ToolPlan) -> Tuple[ToolPlan, Dict[str, Any]]:
        """校验候选计划并返回修订结果。"""

        return self.validator.validate(candidate_plan)

    @staticmethod
    def finalize_plan(candidate_plan: ToolPlan, validated_plan: ToolPlan, trace: Dict[str, Any]) -> ToolPlan:
        """合并候选与校验结果，形成最终计划。"""

        final_plan = deepcopy(validated_plan)
        final_plan.planner_trace = {
            "candidate_plan_id": candidate_plan.plan_id,
            "validator_trace": trace,
            "final_step_count": len(final_plan.steps),
        }
        return final_plan

    def _infer_single_step(self, *, query: str, q_lower: str) -> ToolStep:
        """根据 query 推断单步技能调用。

        阶段A采用“单步策略”：
        - 便于理解和调试；
        - 先把入口打通，再在后续阶段扩展多步DAG。
        """

        fallback_inputs = self._infer_fallback_inputs(query=query, q_lower=q_lower)
        if fallback_inputs is not None:
            skill_name = "qt.ai.system.fallback"
            inputs = fallback_inputs
        elif any(word in q_lower for word in ["strategy", "built-in", "built in", "策略"]):
            match_id = self._extract_strategy_id(query)
            if match_id:
                skill_name = "qt.ai.strategy_meta.get"
                inputs = {"strategy_id": match_id}
            else:
                skill_name = "qt.ai.strategy_meta.list"
                inputs = {}
        elif any(word in q_lower for word in ["kline", "candle", "k线", "绘图", "导出", "png"]):
            skill_name = "qt.ai.visual.export_kline"
            inputs = self._extract_market_inputs(query)
        else:
            skill_name = "qt.ai.data.summary_kline"
            inputs = self._extract_market_inputs(query)

        meta = self.registry.get_metadata(skill_name)
        return ToolStep(
            step_id="step_1",
            skill_name=skill_name,
            inputs=inputs,
            side_effects=meta.side_effects,
            estimated_cost="low",
            depends_on=[],
            run_if="",
            on_fail="stop",
            retry_limit=0,
        )

    @staticmethod
    def _infer_fallback_inputs(*, query: str, q_lower: str) -> Optional[Dict[str, str]]:
        """识别需要回退到统一响应的请求。"""

        contains_live = any(item in q_lower for item in ["实盘", "live trade", "live"])
        contains_download = any(item in q_lower for item in ["下载", "download", "refill"])
        contains_backtest = any(item in q_lower for item in ["回测", "backtest"])
        contains_optimize = any(item in q_lower for item in ["优化", "optimize"])
        contains_codegen = any(item in q_lower for item in ["生成策略", "strategybuilder", "codegen"])
        contains_dangerous = any(item in q_lower for item in ["rm -rf", "bash", "shell command", "cmd /c", "powershell"])
        contains_bypass_confirm = any(item in q_lower for item in ["跳过确认", "skip confirmation", "write files directly"])

        if contains_dangerous:
            return {
                "query": query,
                "fallback_action": "clarify_required",
                "reason": "unsafe_command_request",
                "hint": "Shell command execution is not supported by qteasy AI skills.",
            }

        if contains_bypass_confirm:
            return {
                "query": query,
                "fallback_action": "not_supported_yet",
                "reason": "bypass_confirmation_not_allowed",
                "hint": "High side-effect operations require explicit confirmation.",
            }

        high_risk_intents = [contains_live, contains_download, contains_backtest, contains_optimize, contains_codegen]
        if sum(1 for flag in high_risk_intents if flag) >= 2:
            return {
                "query": query,
                "fallback_action": "clarify_required",
                "reason": "multi_intent_not_supported_in_single_step_planner",
                "hint": "Please split request into smaller steps: download/backtest/optimize/live.",
            }

        if contains_live:
            return {
                "query": query,
                "fallback_action": "plan_only",
                "reason": "live_trade_requires_strong_confirmation",
                "hint": "Live trade is not auto-executed. Please use plan mode and confirm manually.",
            }

        if contains_download or contains_backtest or contains_optimize or contains_codegen:
            return {
                "query": query,
                "fallback_action": "not_supported_yet",
                "reason": "feature_not_implemented_in_stage_a",
                "hint": "This capability is planned for later stages. Use available read-only skills for now.",
            }

        date_match = re.findall(r"(20\d{2}[-/]?\d{2}[-/]?\d{2})", query)
        if len(date_match) > 1:
            start = date_match[0].replace("-", "").replace("/", "")
            end = date_match[1].replace("-", "").replace("/", "")
            try:
                start_dt = datetime.datetime.strptime(start, "%Y%m%d")
                end_dt = datetime.datetime.strptime(end, "%Y%m%d")
                if start_dt > end_dt:
                    return {
                        "query": query,
                        "fallback_action": "clarify_required",
                        "reason": "invalid_date_range",
                        "hint": "Start date must be earlier than or equal to end date.",
                    }
            except ValueError:
                return {
                    "query": query,
                    "fallback_action": "clarify_required",
                    "reason": "invalid_date_format",
                    "hint": "Date format should be YYYYMMDD or YYYY-MM-DD.",
                }

        if "freq=" in q_lower and not re.search(r"\b(1min|5min|15min|30min|60min|d|w|m)\b", query, flags=re.IGNORECASE):
            return {
                "query": query,
                "fallback_action": "clarify_required",
                "reason": "invalid_frequency_expression",
                "hint": "Supported freq: 1min/5min/15min/30min/60min/d/w/m.",
            }
        return None

    @staticmethod
    def _extract_strategy_id(query: str) -> Optional[str]:
        """提取策略 ID。

        Notes
        -----
        该函数是“宽松匹配”，会忽略常见功能词，尝试抓取第一个
        可能代表策略名的 token。若无法可靠判断则返回 None。
        """

        ignored = {
            "list",
            "built",
            "builtin",
            "builtin",
            "strategies",
            "strategy",
            "show",
            "get",
        }
        candidates = re.findall(r"\b([A-Za-z][A-Za-z0-9_]{2,})\b", query)
        for item in candidates:
            lower_item = item.lower()
            if lower_item not in ignored:
                return item
        return None

    @staticmethod
    def _extract_market_inputs(query: str) -> Dict[str, Any]:
        """提取标的与时间参数。

        当前支持抽取：
        - 标的：`000001.SH/000001.SZ/000001.BJ`，或 6 位数字（默认补 `.SH`）；
        - 日期：`YYYYMMDD` / `YYYY-MM-DD` / `YYYY/MM/DD`；
        - 频率：`1min/5min/15min/30min/60min/d/w/m`。

        返回值仅包含命中的字段，未命中的字段由技能内部使用默认值。
        """

        result: Dict[str, Any] = {}
        symbol_match = re.search(r"(\d{6}\.(?:SH|SZ|BJ))", query, flags=re.IGNORECASE)
        if symbol_match:
            result["shares"] = symbol_match.group(1).upper()
        else:
            short_symbol = re.search(r"\b(\d{6})\b", query)
            if short_symbol:
                # 阶段A的简化假设：纯6位代码优先按 SH 处理。
                result["shares"] = short_symbol.group(1) + ".SH"
        date_match = re.findall(r"(20\d{2}[-/]?\d{2}[-/]?\d{2})", query)
        if date_match:
            result["start"] = date_match[0].replace("-", "").replace("/", "")
            if len(date_match) > 1:
                result["end"] = date_match[1].replace("-", "").replace("/", "")
        freq_match = re.search(r"\b(1min|5min|15min|30min|60min|d|w|m)\b", query, flags=re.IGNORECASE)
        if freq_match:
            result["freq"] = freq_match.group(1)
        return result
