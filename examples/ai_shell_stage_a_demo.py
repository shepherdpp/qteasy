# coding=utf-8
# ======================================
# File: ai_shell_stage_a_demo.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# Minimal demo for qteasy ai shell stage A
# ======================================

from qteasy.ai.app import QteasyAssistant


def main() -> None:
    """运行阶段A最小演示。"""

    assistant = QteasyAssistant()
    plan_payload = assistant.plan("list built-in strategies")
    print("\n[Demo] plan result:")
    print(plan_payload)

    run_payload = assistant.run("list built-in strategies")
    print("\n[Demo] run result:")
    print(run_payload)


if __name__ == "__main__":
    main()
