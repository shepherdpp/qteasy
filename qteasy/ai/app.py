# coding=utf-8
# ======================================
# File: app.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# qteasy AI 外壳应用层入口，统一编排
# Notebook / CLI 调用链路。
# ======================================

"""阶段A统一入口（Notebook/CLI 共用）。

这个模块定位为“装配层（assembly layer）”，负责把分散模块按固定拓扑连接：

1. `SkillRegistry`：技能注册中心；
2. `Planner`：自然语言到 ToolPlan；
3. `PlanExecutor`：计划执行与 run 落盘；
4. `MemoryStore`：profile/env_facts/runs 存储。

设计目标
--------
- 对 Notebook 用户暴露简单 API（ask/plan/run）；
- 对 CLI 和未来 Web/TUI 保持一致的应用层语义；
- 避免前端直接感知技能细节与执行细节。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .config import ConfigCenter
from .executor import PlanExecutor
from .memory_store import MemoryStore
from .output import AssistantOutput
from .planner import Planner
from .provider import BaseLLMProvider
from .renderer import OutputRenderer
from .registry import SkillRegistry
from .run_policy import RunStorePolicy
from .skills import (
    build_data_summary_skill,
    build_strategy_meta_get_skill,
    build_strategy_meta_list_skill,
    build_system_fallback_skill,
    build_visual_export_skill,
)


def build_default_registry() -> SkillRegistry:
    """构建阶段A默认 Registry。

    Returns
    -------
    SkillRegistry
        已注册阶段A默认只读技能的注册中心实例。

    Notes
    -----
    这里按固定顺序注册技能，便于：
    - 测试时得到稳定输出；
    - 阅读时清楚看到阶段A能力边界。
    """

    registry = SkillRegistry()
    for builder in [
        build_strategy_meta_list_skill,
        build_strategy_meta_get_skill,
        build_data_summary_skill,
        build_visual_export_skill,
        build_system_fallback_skill,
    ]:
        metadata, handler = builder()
        registry.register(metadata, handler)
    return registry


@dataclass
class AssistantResponse:
    """统一返回对象（预留类型）。

    Notes
    -----
    当前阶段A主要以 `dict` 返回，保留该 dataclass 是为了后续在
    类型系统中逐步收敛响应对象结构。
    """

    plan: Dict[str, Any]
    execution: Dict[str, Any]
    run_id: str
    run_file: str


class QteasyAssistant:
    """Notebook/CLI 共用助手对象。

    这是用户最直接接触的 AI 外壳对象，面向“用户意图”而不是“内部模块”。
    用户只需要选择调用模式：

    - `ask()`：只问不执行；
    - `plan()`：生成 dry-run 计划；
    - `run()`：确认执行计划。
    """

    def __init__(
        self,
        *,
        provider: Optional[BaseLLMProvider] = None,
        memory_store: Optional[MemoryStore] = None,
        registry: Optional[SkillRegistry] = None,
        run_policy: Optional[RunStorePolicy] = None,
    ) -> None:
        # MemoryStore：负责持久化执行记录与轻量记忆。
        self.memory_store = memory_store or MemoryStore()
        # Registry：聚合本阶段可用技能及其元数据。
        self.registry = registry or build_default_registry()
        # Planner：根据用户请求生成计划对象。
        self.planner = Planner(self.registry, provider=provider)
        # Executor：负责按计划执行。
        self.executor = PlanExecutor(self.registry, self.memory_store)
        self.renderer = OutputRenderer()
        self.run_policy = run_policy or RunStorePolicy()
        self._last_run_id = ""

    def ask(
        self,
        query: str,
        *,
        response_style: str = "user_friendly",
        persist: str | None = None,
        keep: bool = False,
    ) -> Dict[str, Any] | AssistantOutput:
        """Ask 模式：仅返回 plan，不执行技能。

        Parameters
        ----------
        query : str
            用户自然语言请求。

        Returns
        -------
        Dict[str, Any]
            dry-run 执行结果（无技能调用），用于解释和预览。
        """

        plan = self.planner.build_plan(query, mode="ask")
        return self._execute_and_format(
            plan=plan,
            confirm=False,
            response_style=response_style,
            persist=persist,
            keep=keep,
        )

    def plan(
        self,
        query: str,
        *,
        response_style: str = "user_friendly",
        persist: str | None = None,
        keep: bool = False,
    ) -> Dict[str, Any] | AssistantOutput:
        """Plan 模式：生成 dry_run 计划。

        与 `ask()` 的区别在于：
        - ask：通常无步骤，强调“问答解释”；
        - plan：通常会生成可执行步骤，强调“执行前审阅”。
        """

        plan = self.planner.build_plan(query, mode="plan")
        return self._execute_and_format(
            plan=plan,
            confirm=False,
            response_style=response_style,
            persist=persist,
            keep=keep,
        )

    def run(
        self,
        query: str,
        *,
        response_style: str = "user_friendly",
        persist: str | None = None,
        keep: bool = False,
    ) -> Dict[str, Any] | AssistantOutput:
        """Plan + 确认执行。

        工作流程：
        1) 先由 Planner 生成 ToolPlan；
        2) 将 execution_mode 切换为 execute；
        3) 交给 Executor 实际执行并写入 runs。
        """

        plan = self.planner.build_plan(query, mode="plan")
        plan.execution_mode = "execute"
        return self._execute_and_format(
            plan=plan,
            confirm=True,
            response_style=response_style,
            persist=persist,
            keep=keep,
        )

    def _execute_and_format(
        self,
        *,
        plan: Any,
        confirm: bool,
        response_style: str,
        persist: str | None,
        keep: bool,
    ) -> Dict[str, Any] | AssistantOutput:
        """执行并按策略处理落盘与渲染。"""

        persist_mode = persist or self.run_policy.persist_mode
        persist_run = persist_mode in {"bounded", "audit"}
        payload = self.executor.execute(plan, confirm=confirm, persist_run=False)

        if persist_run:
            run_id = str(payload.get("run_id", "")).strip()
            if run_id:
                run_file = self.memory_store.save_run(run_id, payload)
                payload["run_file"] = run_file
                self._last_run_id = run_id
                if persist_mode == "bounded":
                    cleanup_report = self.memory_store.cleanup_runs(
                        max_age_days=self.run_policy.max_age_days,
                        max_count=self.run_policy.max_count,
                        max_total_mb=self.run_policy.max_total_mb,
                    )
                else:
                    cleanup_report = {"deleted_count": 0, "deleted_files": [], "remaining_count": len(self.memory_store.list_runs())}
                payload["cleanup"] = cleanup_report
                if keep:
                    payload["pinned_file"] = self.memory_store.pin_run(run_id, tag="keep")
        else:
            payload["run_file"] = ""
            payload["cleanup"] = {"deleted_count": 0, "deleted_files": [], "remaining_count": len(self.memory_store.list_runs())}

        if response_style == "raw":
            return payload

        rendered = self.renderer.render(payload, style="user_friendly", context={"persist_mode": persist_mode})
        if self.run_policy.show_save_hint:
            run_file = payload.get("run_file", "")
            hint = f"\nRun file: {run_file}" if run_file else "\nRun file: not persisted."
            rendered.narrative = rendered.narrative + hint
        return rendered

    def debug_config(self) -> Dict[str, Any]:
        """返回当前 AI 配置诊断信息（不泄露密钥）。"""

        config_center = ConfigCenter()
        provider_cfg = config_center.resolve_provider_config()
        trace = config_center.get_trace()
        api_key = str(provider_cfg.get("api_key", "")).strip()
        return {
            "provider_enabled": self.planner.provider is not None,
            "model": str(provider_cfg.get("model", "")).strip(),
            "base_url": str(provider_cfg.get("base_url", "")).strip(),
            "timeout": int(provider_cfg.get("timeout", 30)),
            "api_key_present": bool(api_key),
            "config_sources": {key: item.get("source", "") for key, item in trace.items()},
        }

    def pin_last_run(self, tag: str = "") -> str:
        """将最近一次 run 记录钉住保存。"""

        if not self._last_run_id:
            raise ValueError("No run has been persisted yet.")
        return self.memory_store.pin_run(self._last_run_id, tag=tag)
