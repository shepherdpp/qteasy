# coding=utf-8
# ======================================
# File: visual_export.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# qteasy AI 阶段A只读技能：K线图导出。
# ======================================

"""K线导出技能。"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Callable, Optional

import matplotlib.pyplot as plt
import pandas as pd

from ..contracts import SkillError, SkillMetadata, SkillResult, SkillSideEffects, new_run_id


def _default_output_path(output_path: Optional[str]) -> str:
    """计算默认输出路径。"""

    if output_path:
        return output_path
    folder = os.path.join(os.getcwd(), ".qteasy", "ai", "artifacts")
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(folder, f"kline_{timestamp}.png")


def build_visual_export_skill(
    get_kline_func: Callable[..., pd.DataFrame] | None = None,
) -> tuple[SkillMetadata, Callable[..., dict]]:
    """构建 K 线导出技能。"""

    if get_kline_func is None:
        import qteasy as qt

        get_kline_func = qt.get_kline

    metadata = SkillMetadata(
        name="qt.ai.visual.export_kline",
        version="0.1.0",
        summary="Export kline chart image.",
        inputs_schema={
            "shares": {"type": "string", "required": False},
            "start": {"type": "string", "required": False},
            "end": {"type": "string", "required": False},
            "freq": {"type": "string", "required": False},
            "output_path": {"type": "string", "required": False},
        },
        outputs_schema={"artifacts": "list"},
        side_effects=SkillSideEffects(filesystem_write=True, description="export image file"),
        required_capabilities=["matplotlib"],
        qteasy_entrypoints=["qteasy.get_kline"],
    )

    def handler(
        shares: str = "000300.SH",
        start: Optional[str] = None,
        end: Optional[str] = None,
        freq: str = "D",
        output_path: Optional[str] = None,
        **kwargs,
    ) -> dict:
        run_id = new_run_id()
        target_path = _default_output_path(output_path)
        inputs_echo = {
            "shares": shares,
            "start": start,
            "end": end,
            "freq": freq,
            "output_path": target_path,
            **kwargs,
        }
        try:
            data = get_kline_func(
                shares=shares,
                start=start,
                end=end,
                freq=freq,
                as_panel=False,
            )
            if isinstance(data, dict):
                if not data:
                    raise ValueError("No data returned.")
                data = data[sorted(data.keys())[0]]
            if data is None or data.empty:
                raise ValueError("No data returned.")
            close_col = "close" if "close" in data.columns else data.columns[0]
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(data.index, data[close_col], color="#1f77b4", linewidth=1.2)
            ax.set_title(f"{shares} {freq.upper()} close")
            ax.set_xlabel("time")
            ax.set_ylabel(str(close_col))
            ax.grid(alpha=0.25)
            fig.tight_layout()
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            fig.savefig(target_path, dpi=120)
            plt.close(fig)
            result = SkillResult(
                ok=True,
                skill_name=metadata.name,
                run_id=run_id,
                inputs_echo=inputs_echo,
                metrics={"n_rows": int(len(data))},
                data_summary={"index_start": str(data.index.min()), "index_end": str(data.index.max())},
                artifacts=[
                    {
                        "type": "image",
                        "path": target_path,
                        "description": "Exported kline chart.",
                    }
                ],
            )
        except Exception as exc:
            result = SkillResult(
                ok=False,
                skill_name=metadata.name,
                run_id=run_id,
                inputs_echo=inputs_echo,
                error=SkillError(
                    code="KLINE_EXPORT_FAILED",
                    message=f"Failed to export kline chart: {exc}",
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
