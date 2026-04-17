# coding=utf-8
# ======================================
# File: data_summary.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# qteasy AI 阶段A只读技能：K线数据摘要。
# ======================================

"""K线数据摘要只读技能。"""

from __future__ import annotations

from typing import Callable, Dict, Optional

import numpy as np
import pandas as pd

from ..contracts import SkillError, SkillMetadata, SkillResult, SkillSideEffects, new_run_id


def _normalize_freq(freq: Optional[str]) -> str:
    """规范化频率字符串。"""

    if not freq:
        return "D"
    return str(freq).upper()


def build_data_summary_skill(
    get_kline_func: Callable[..., pd.DataFrame] | None = None,
) -> tuple[SkillMetadata, Callable[..., dict]]:
    """构建 K 线摘要技能。"""

    if get_kline_func is None:
        import qteasy as qt

        get_kline_func = qt.get_kline

    metadata = SkillMetadata(
        name="qt.ai.data.summary_kline",
        version="0.1.0",
        summary="Summarize kline data.",
        inputs_schema={
            "shares": {"type": "string", "required": False},
            "start": {"type": "string", "required": False},
            "end": {"type": "string", "required": False},
            "freq": {"type": "string", "required": False},
        },
        outputs_schema={"metrics": "dict", "data_summary": "dict"},
        side_effects=SkillSideEffects(description="readonly"),
        required_capabilities=[],
        qteasy_entrypoints=["qteasy.get_kline"],
    )

    def handler(
        shares: str = "000300.SH",
        start: Optional[str] = None,
        end: Optional[str] = None,
        freq: str = "D",
        **kwargs,
    ) -> dict:
        run_id = new_run_id()
        freq_value = _normalize_freq(freq)
        inputs_echo = {
            "shares": shares,
            "start": start,
            "end": end,
            "freq": freq_value,
            **kwargs,
        }
        try:
            data = get_kline_func(
                shares=shares,
                start=start,
                end=end,
                freq=freq_value,
                as_panel=False,
            )
            if isinstance(data, dict):
                if not data:
                    raise ValueError("No data returned.")
                first_key = sorted(data.keys())[0]
                data = data[first_key]
            if data is None or data.empty:
                raise ValueError("No data returned.")
            close_col = "close" if "close" in data.columns else data.columns[0]
            close_values = data[close_col].astype(float)
            metrics = {
                "n_rows": int(len(data)),
                "n_cols": int(len(data.columns)),
                "close_min": float(np.nanmin(close_values.values)),
                "close_max": float(np.nanmax(close_values.values)),
                "nan_ratio_close": float(np.isnan(close_values.values).mean()),
            }
            data_summary: Dict[str, object] = {
                "columns": [str(col) for col in data.columns],
                "index_start": str(data.index.min()),
                "index_end": str(data.index.max()),
            }
            result = SkillResult(
                ok=True,
                skill_name=metadata.name,
                run_id=run_id,
                inputs_echo=inputs_echo,
                metrics=metrics,
                data_summary=data_summary,
                payload={"preview": data.head(5).to_dict(orient="records")},
            )
        except Exception as exc:
            result = SkillResult(
                ok=False,
                skill_name=metadata.name,
                run_id=run_id,
                inputs_echo=inputs_echo,
                error=SkillError(
                    code="KLINE_SUMMARY_FAILED",
                    message=f"Failed to summarize kline data: {exc}",
                ),
            )
        return {
            "ok": result.ok,
            "skill_name": result.skill_name,
            "run_id": result.run_id,
            "inputs_echo": result.inputs_echo,
            "metrics": result.metrics,
            "data_summary": result.data_summary,
            "payload": result.payload,
            "warnings": result.warnings,
            "error": None if result.error is None else result.error.__dict__,
            "artifacts": result.artifacts,
        }

    return metadata, handler
