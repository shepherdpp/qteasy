# coding=utf-8
# ======================================
# File: contracts.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# qteasy AI 外壳核心契约定义，统一
# 计划、执行、技能输出的数据结构。
# ======================================

"""qteasy AI 外壳核心契约定义。

本模块是阶段A的“统一数据语言”，用于约束：

1. 规划层（Planner）如何表达待执行计划；
2. 执行层（Executor）如何记录执行过程；
3. 技能层（Skills）如何返回结构化结果；
4. 前端层（Notebook/CLI）如何稳定解析输出。

设计原则：
- 结构化优先：避免自由文本导致解析歧义；
- 向前兼容：新增字段可扩展，已有字段语义尽量稳定；
- 可追溯：plan_id/run_id 和时间戳贯穿全链路。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


def _utc_now_iso() -> str:
    """返回当前 UTC 时间的 ISO 字符串。

    Notes
    -----
    统一采用 UTC + `Z` 的字符串形式，避免本地时区差异导致
    的日志排序与跨机器调试问题。
    """

    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


@dataclass
class SkillSideEffects:
    """技能副作用描述。

    该结构用于在 ToolPlan 阶段明确告知用户：
    当前技能是否会触发网络、写文件、修改本地状态或重计算。
    在阶段B接入高副作用技能后，该结构会成为“确认执行”的关键依据。
    """

    network: bool = False
    filesystem_write: bool = False
    local_state_change: bool = False
    heavy_compute: bool = False
    description: str = ""


@dataclass
class SkillMetadata:
    """技能元数据契约。

    一个技能最核心的“自描述信息”。
    Planner/Executor/前端都依赖该结构判断：
    - 技能能做什么（summary）；
    - 需要什么输入（inputs_schema）；
    - 返回什么输出（outputs_schema）；
    - 风险与依赖（side_effects / required_capabilities）；
    - 对应 qteasy 的确定性入口（qteasy_entrypoints）。
    """

    name: str
    version: str
    summary: str
    inputs_schema: Dict[str, Any]
    outputs_schema: Dict[str, Any]
    side_effects: SkillSideEffects = field(default_factory=SkillSideEffects)
    required_capabilities: List[str] = field(default_factory=list)
    qteasy_entrypoints: List[str] = field(default_factory=list)


@dataclass
class ToolStep:
    """计划中的单步调用。

    ToolPlan 可由一个或多个 ToolStep 组成。A0 起支持最小 DAG 字段：
    - `depends_on`：依赖前置步骤；
    - `run_if`：条件执行表达式（最小语义）；
    - `on_fail`：失败策略（stop/continue/retry）。
    """

    step_id: str
    skill_name: str
    inputs: Dict[str, Any]
    side_effects: SkillSideEffects = field(default_factory=SkillSideEffects)
    estimated_cost: str = "low"
    depends_on: List[str] = field(default_factory=list)
    run_if: str = ""
    on_fail: str = "stop"
    retry_limit: int = 0


@dataclass
class ToolPlan:
    """工具调用计划。

    ToolPlan 是用户可审阅的“执行合同”。
    任何高副作用动作都应先转成 ToolPlan，再交由用户确认后执行。
    """

    plan_id: str
    user_query: str
    steps: List[ToolStep]
    assumptions: Dict[str, Any] = field(default_factory=dict)
    planner_trace: Dict[str, Any] = field(default_factory=dict)
    execution_mode: str = "dry_run"
    mode: str = "plan"
    created_at: str = field(default_factory=_utc_now_iso)


@dataclass
class SkillError:
    """技能错误信息。

    统一错误格式可支持：
    - 前端稳定展示；
    - 自动化统计和告警；
    - 后续错误恢复策略（按 code 分流）。
    """

    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillResult:
    """技能统一输出结构。

    约定输出字段：
    - `metrics`：可直接用于统计/排序/评估；
    - `data_summary`：用于快速理解数据规模、区间和质量；
    - `artifacts`：图像、报表、文件路径等可复用产物；
    - `payload`：具体业务载荷（按技能扩展）。
    """

    ok: bool
    skill_name: str
    run_id: str
    inputs_echo: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    data_summary: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    error: Optional[SkillError] = None
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanStepRecord:
    """执行记录中的单步结果。

    一个 step 一条记录，保留开始/结束时间和结果快照，
    便于后续复盘“哪一步耗时、哪一步失败、失败时输入是什么”。
    """

    step_id: str
    skill_name: str
    started_at: str
    ended_at: str
    result: Dict[str, Any]


@dataclass
class PlanExecutionRecord:
    """计划执行记录。

    该结构是 runs 落盘的核心主体，代表一次完整执行会话。
    """

    run_id: str
    plan_id: str
    status: str
    mode: str
    created_at: str
    steps: List[PlanStepRecord] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


def new_plan_id() -> str:
    """生成 plan_id。

    Notes
    -----
    使用短 uuid 主要考虑可读性（日志、终端、文件名都更简洁）。
    """

    return f"plan_{uuid4().hex[:12]}"


def new_run_id() -> str:
    """生成 run_id。"""

    return f"run_{uuid4().hex[:12]}"


def to_dict(data: Any) -> Dict[str, Any]:
    """将 dataclass 契约对象转换为字典。

    Parameters
    ----------
    data : Any
        dataclass 实例或字典。

    Returns
    -------
    Dict[str, Any]
        序列化后的标准字典。

    Raises
    ------
    TypeError
        当传入对象既不是 dataclass 也不是 dict 时抛出。
    """

    if hasattr(data, "__dataclass_fields__"):
        return asdict(data)
    if isinstance(data, dict):
        return data
    raise TypeError(f"Unsupported data type for serialization: {type(data).__name__}")
