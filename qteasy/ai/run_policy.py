# coding=utf-8
# ======================================
# File: run_policy.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-20
# Desc:
# qteasy AI runs 留存策略定义，控制
# 持久化模式与自动清理行为。
# ======================================

"""runs 留存策略。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal


@dataclass
class RunStorePolicy:
    """run 结果持久化策略。"""

    persist_mode: Literal["bounded", "none", "audit"] = "bounded"
    max_age_days: int = 7
    max_count: int = 200
    max_total_mb: int = 200
    show_save_hint: bool = True

    def to_dict(self) -> Dict[str, int | str | bool]:
        """返回策略字典。"""

        return {
            "persist_mode": self.persist_mode,
            "max_age_days": self.max_age_days,
            "max_count": self.max_count,
            "max_total_mb": self.max_total_mb,
            "show_save_hint": self.show_save_hint,
        }

