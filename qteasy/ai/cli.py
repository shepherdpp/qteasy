# coding=utf-8
# ======================================
# File: cli.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# qteasy AI 外壳命令行入口，支持
# ask/plan/run/provider-check 子命令。
# ======================================

"""qteasy AI 外壳 CLI 入口。"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from .app import QteasyAssistant
from .config import ConfigCenter
from .memory_store import MemoryStore
from .provider import OpenAICompatProvider


def _build_provider_from_config() -> OpenAICompatProvider | None:
    """从 ConfigCenter 构建 Provider。"""

    config_center = ConfigCenter()
    provider_cfg = config_center.resolve_provider_config()
    model = str(provider_cfg.get("model", "")).strip()
    if not model:
        return None
    return OpenAICompatProvider(
        model=model,
        api_key=str(provider_cfg.get("api_key", "")),
        base_url=str(provider_cfg.get("base_url", "https://api.openai.com/v1")),
        timeout=int(provider_cfg.get("timeout", 30)),
        config_center=config_center,
    )


def _provider_check_payload() -> Dict[str, Any]:
    """生成 provider-check 的可诊断信息。"""

    config_center = ConfigCenter()
    provider_cfg = config_center.resolve_provider_config()
    trace = config_center.get_trace()
    model = str(provider_cfg.get("model", "")).strip()
    api_key = str(provider_cfg.get("api_key", "")).strip()
    base_url = str(provider_cfg.get("base_url", "")).strip()
    timeout = int(provider_cfg.get("timeout", 30))

    mode = "rule"
    if model:
        if base_url.startswith("http://127.0.0.1") or base_url.startswith("http://localhost"):
            mode = "local_llm"
        else:
            mode = "cloud_llm"

    return {
        "ok": bool(model and api_key),
        "provider": "openai_compatible" if model else "none",
        "mode": mode,
        "model": model,
        "base_url": base_url,
        "timeout": timeout,
        "api_key_present": bool(api_key),
        "config_sources": {key: item.get("source", "") for key, item in trace.items()},
        "message": "Provider configured." if (model and api_key) else "Provider not configured.",
    }


def _print_json(payload: Dict[str, Any]) -> None:
    """打印 JSON。"""

    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""

    parser = argparse.ArgumentParser(
        prog="qteasy-ai",
        description="qteasy AI shell stage-A CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ask_parser = sub.add_parser("ask", help="Ask mode, no skill execution.")
    ask_parser.add_argument("query", type=str, help="Natural language query")

    plan_parser = sub.add_parser("plan", help="Plan mode dry run.")
    plan_parser.add_argument("query", type=str, help="Natural language query")

    run_parser = sub.add_parser("run", help="Plan and execute.")
    run_parser.add_argument("query", type=str, help="Natural language query")

    sub.add_parser("provider-check", help="Check provider settings.")
    return parser


def main() -> int:
    """CLI 主入口。"""

    parser = build_parser()
    args = parser.parse_args()

    memory_store = MemoryStore()
    provider = _build_provider_from_config()
    assistant = QteasyAssistant(provider=provider, memory_store=memory_store)

    if args.command == "ask":
        _print_json(assistant.ask(args.query))
        return 0
    if args.command == "plan":
        _print_json(assistant.plan(args.query))
        return 0
    if args.command == "run":
        _print_json(assistant.run(args.query))
        return 0
    if args.command == "provider-check":
        _print_json(_provider_check_payload())
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
