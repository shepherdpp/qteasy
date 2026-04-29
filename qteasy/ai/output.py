# coding=utf-8
# ======================================
# File: output.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-20
# Desc:
# qteasy AI 用户向输出对象定义，统一自然
# 语言、代码、结果摘要与原始载荷。
# ======================================

"""用户向输出对象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AssistantOutput:
    """用户向输出对象。

    Notes
    -----
    该对象是“渲染层输出”，而不是执行层协议。
    执行层依旧返回 machine-readable 的 raw payload。
    """

    narrative: str
    python_code: str
    result_preview: str
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """将输出对象转换为字典。"""

        return {
            "narrative": self.narrative,
            "python_code": self.python_code,
            "result_preview": self.result_preview,
            "raw": self.raw,
        }

