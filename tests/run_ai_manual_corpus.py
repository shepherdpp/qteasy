# coding=utf-8
# ======================================
# File: run_ai_manual_corpus.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-20
# Desc:
# 运行 AI 语料并打印计划/执行摘要，
# 供人工测试记录使用。
# ======================================

"""运行 AI 语料并输出摘要。"""

from __future__ import annotations

import json
from pathlib import Path

from qteasy.ai.app import QteasyAssistant


def _load_cases(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("cases", [])


def run_corpus(corpus_name: str) -> None:
    corpus_path = Path(__file__).resolve().parent / "ai_corpus" / corpus_name
    cases = _load_cases(corpus_path)
    assistant = QteasyAssistant()
    print(f"\n[AI Corpus] running {corpus_name}, cases: {len(cases)}")
    for case in cases:
        query = case.get("query", "")
        mode = case.get("mode", "plan")
        if mode == "ask":
            payload = assistant.ask(query)
        else:
            payload = assistant.plan(query)
        plan_steps = payload.get("plan", {}).get("steps", [])
        execution = payload.get("execution", {})
        print(
            f" - {case.get('id', 'N/A')}: mode={mode}, "
            f"steps={len(plan_steps)}, status={execution.get('status', '')}, "
            f"first_skill={(plan_steps[0]['skill_name'] if plan_steps else '')}"
        )


if __name__ == "__main__":
    run_corpus("current_capabilities.json")
    run_corpus("future_capabilities.json")
    run_corpus("error_corpus.json")
