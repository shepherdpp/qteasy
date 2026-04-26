# coding=utf-8
# ======================================
# File: notebook_magic.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-26
# Desc:
# qteasy AI 在 Classic Notebook 下的
# 魔法命令入口，实现 prompt-only 交互。
# ======================================

"""Classic Notebook 魔法命令入口。

该模块把 Notebook 作为 UIFrontend 接入既有 AI 框架：

- 只负责交互输入、参数解析与展示；
- 复用 QteasyAssistant 的 ask/plan/run 能力；
- 通过 confirm token 实现无 widgets 的显式确认执行。
"""

from __future__ import annotations

import argparse
import json
import shlex
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .app import QteasyAssistant
from .output import AssistantOutput

try:
    from IPython.core.magic import Magics, line_cell_magic, magics_class
    from IPython.display import Markdown, display
except Exception:  # pragma: no cover - 无 IPython 时不影响模块导入
    Magics = object

    def magics_class(cls: Any) -> Any:  # type: ignore[misc]
        return cls

    def line_cell_magic(name: str) -> Any:  # type: ignore[misc]
        def _decorator(func: Any) -> Any:
            return func

        return _decorator

    Markdown = None
    display = None


_ASSISTANT_NS_KEY = "_qtai_assistant"
_PLAN_CACHE_NS_KEY = "_qtai_plan_cache"


@dataclass
class MagicCommand:
    """Notebook 魔法命令解析结果。"""

    mode: str
    response_style: str
    persist: Optional[str]
    keep: bool
    confirm_plan_id: str
    query: str


def parse_magic_command(line: str, cell: Optional[str] = None) -> MagicCommand:
    """解析 `%qtai/%%qtai` 命令参数。"""

    parser = argparse.ArgumentParser(prog="qtai", add_help=False)
    parser.add_argument("--mode", choices=["ask", "plan", "run"], default="plan")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--raw", action="store_true")
    parser.add_argument("--persist", choices=["bounded", "audit", "none"], default=None)
    parser.add_argument("--keep", action="store_true")
    parser.add_argument("--confirm", dest="confirm_plan_id", default="")
    parser.add_argument("query_parts", nargs="*")

    args = parser.parse_args(shlex.split(line))
    if args.raw:
        response_style = "raw"
    else:
        response_style = "user_friendly"
    query_text = (cell if cell is not None else " ".join(args.query_parts)).strip()
    return MagicCommand(
        mode=args.mode,
        response_style=response_style,
        persist=args.persist,
        keep=args.keep,
        confirm_plan_id=str(args.confirm_plan_id).strip(),
        query=query_text,
    )


def execute_magic_command(
    command: MagicCommand,
    *,
    assistant: QteasyAssistant,
    plan_cache: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """执行魔法命令并返回可展示结果。"""

    if command.confirm_plan_id:
        cached = plan_cache.get(command.confirm_plan_id)
        if cached is None:
            return {
                "mode": "run",
                "result": AssistantOutput(
                    narrative=f"Plan id not found: {command.confirm_plan_id}",
                    python_code="",
                    result_preview="Please run `%%qtai --mode run` first to generate a plan.",
                    raw={"error": "plan_not_found", "plan_id": command.confirm_plan_id},
                ),
                "confirm_hint": "",
            }

        plan = deepcopy(cached["plan"])
        plan.execution_mode = "execute"
        persist = command.persist if command.persist is not None else cached.get("persist")
        keep = bool(command.keep or cached.get("keep", False))
        response_style = command.response_style or cached.get("response_style", "user_friendly")
        result = assistant._execute_and_format(
            plan=plan,
            confirm=True,
            response_style=response_style,
            persist=persist,
            keep=keep,
        )
        plan_cache.pop(command.confirm_plan_id, None)
        return {
            "mode": "run",
            "result": result,
            "confirm_hint": "",
            "confirmed_plan_id": command.confirm_plan_id,
        }

    if not command.query:
        return {
            "mode": command.mode,
            "result": AssistantOutput(
                narrative="Empty prompt. Please provide a query.",
                python_code="",
                result_preview="Example: %%qtai --mode plan\\nlist built-in strategies",
                raw={"error": "empty_prompt"},
            ),
            "confirm_hint": "",
        }

    if command.mode == "ask":
        result = assistant.ask(
            command.query,
            response_style=command.response_style,
            persist=command.persist,
            keep=command.keep,
        )
        return {"mode": "ask", "result": result, "confirm_hint": ""}

    if command.mode == "plan":
        result = assistant.plan(
            command.query,
            response_style=command.response_style,
            persist=command.persist,
            keep=command.keep,
        )
        return {"mode": "plan", "result": result, "confirm_hint": ""}

    # mode == run 且无 confirm：先产出 dry-run plan，再给确认 token。
    plan = assistant.planner.build_plan(command.query, mode="plan")
    plan.execution_mode = "execute"
    result = assistant._execute_and_format(
        plan=plan,
        confirm=False,
        response_style=command.response_style,
        persist=command.persist,
        keep=command.keep,
    )
    raw = result.raw if isinstance(result, AssistantOutput) else result
    plan_id = str(raw.get("plan", {}).get("plan_id", plan.plan_id))
    plan_cache[plan_id] = {
        "plan": deepcopy(plan),
        "persist": command.persist,
        "keep": command.keep,
        "response_style": command.response_style,
        "query": command.query,
    }
    confirm_hint = f"%%qtai --confirm {plan_id}\nExecute."
    return {"mode": "run", "result": result, "confirm_hint": confirm_hint, "plan_id": plan_id}


def _result_to_raw_dict(result: Any) -> Dict[str, Any]:
    """将结果统一转为 dict。"""

    if isinstance(result, AssistantOutput):
        return result.to_dict()
    if isinstance(result, dict):
        return result
    return {"output": str(result)}


def render_magic_result(mode: str, result: Any, *, confirm_hint: str = "") -> str:
    """将命令执行结果格式化为 Markdown 文本。"""

    mode_bar = f"[MODE: {mode.upper()}]"
    if isinstance(result, AssistantOutput):
        sections = [
            mode_bar,
            "",
            "### Narrative",
            result.narrative.strip(),
            "",
            "### Python Code",
            "```python",
            result.python_code.strip(),
            "```",
            "",
            "### Result Preview",
            result.result_preview.strip(),
        ]
        raw_plan = result.raw.get("plan", {})
        raw_steps = raw_plan.get("steps", [])
        if raw_steps:
            sections.extend(
                [
                    "",
                    "### Plan Steps",
                    "```json",
                    json.dumps(raw_steps, ensure_ascii=False, indent=2),
                    "```",
                ]
            )
    else:
        raw = _result_to_raw_dict(result)
        sections = [
            mode_bar,
            "",
            "### Raw Output",
            "```json",
            json.dumps(raw, ensure_ascii=False, indent=2),
            "```",
        ]

    if confirm_hint:
        sections.extend(["", "### Confirm To Execute", "```python", confirm_hint, "```"])
    return "\n".join(sections)


@magics_class
class QtAiMagics(Magics):  # type: ignore[misc]
    """qteasy AI notebook 魔法命令。"""

    @line_cell_magic
    def qtai(self, line: str, cell: Optional[str] = None) -> Any:
        """统一处理 `%qtai` 与 `%%qtai`。"""

        user_ns = getattr(self.shell, "user_ns", {})
        assistant = user_ns.get(_ASSISTANT_NS_KEY)
        if not isinstance(assistant, QteasyAssistant):
            assistant = QteasyAssistant()
            user_ns[_ASSISTANT_NS_KEY] = assistant
        plan_cache = user_ns.setdefault(_PLAN_CACHE_NS_KEY, {})
        if not isinstance(plan_cache, dict):
            plan_cache = {}
            user_ns[_PLAN_CACHE_NS_KEY] = plan_cache

        command = parse_magic_command(line=line, cell=cell)
        execution = execute_magic_command(command, assistant=assistant, plan_cache=plan_cache)
        markdown_text = render_magic_result(
            execution["mode"],
            execution["result"],
            confirm_hint=str(execution.get("confirm_hint", "")),
        )
        if display is not None and Markdown is not None:
            display(Markdown(markdown_text))
        else:  # pragma: no cover - 无 IPython 环境下的兜底
            print(markdown_text)
        return _result_to_raw_dict(execution["result"])


def load_ipython_extension(ipython: Any) -> None:
    """IPython 扩展入口。"""

    ipython.register_magics(QtAiMagics)

