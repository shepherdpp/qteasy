# coding=utf-8
# ======================================
# File: memory_store.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# qteasy AI 外壳本地记忆存储层，负责
# profile/env_facts/runs 的落盘与读取。
# ======================================

"""本地记忆与执行记录存储。

MemoryStore 是阶段A“可追溯”能力的核心支撑模块，解决三个问题：

1. 用户偏好如何保存（profile）；
2. 环境事实如何缓存（env_facts）；
3. 每次执行如何复盘（runs）。

目录约定
--------
默认目录：`./.qteasy/ai/`
可通过环境变量 `QTEASY_AI_HOME` 覆盖根目录。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import ConfigCenter


class MemoryStore:
    """管理 profile/env_facts/runs 的最小落盘。

    Parameters
    ----------
    base_dir : str, optional
        存储根目录。未提供时按环境变量或默认路径自动推断。
    """

    def __init__(self, base_dir: Optional[str] = None) -> None:
        config_center = ConfigCenter()
        base_dir = config_center.resolve(
            "ai_home",
            explicit=base_dir,
            env_key="QTEASY_AI_HOME",
            qt_key="ai_home",
            default=".qteasy/ai/",
        )
        self.base_dir = Path(base_dir)
        self.runs_dir = self.base_dir / "runs"
        # 初始化时确保目录存在，避免后续写入分支到处做 mkdir。
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    @property
    def profile_path(self) -> Path:
        """profile 文件路径。"""

        return self.base_dir / "profile.json"

    @property
    def env_facts_path(self) -> Path:
        """env facts 文件路径。"""

        return self.base_dir / "env_facts.json"

    def _read_json(self, path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
        """读取 JSON 文件，不存在时返回默认值。

        Notes
        -----
        阶段A采用“宽松读取”策略：不存在即返回默认值，
        以减少首次使用时的失败概率。
        """

        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, path: Path, data: Dict[str, Any]) -> None:
        """写入 JSON 文件。

        统一 UTF-8 + pretty JSON，方便用户直接查看和手工修复。
        """

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_profile(self) -> Dict[str, Any]:
        """读取 profile。"""

        return self._read_json(self.profile_path, default={})

    def save_profile(self, profile: Dict[str, Any]) -> None:
        """保存 profile。

        自动追加 `updated_at`，用于判断记忆新鲜度与变更时间。
        """

        payload = dict(profile)
        payload["updated_at"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        self._write_json(self.profile_path, payload)

    def load_env_facts(self) -> Dict[str, Any]:
        """读取环境事实。"""

        return self._read_json(self.env_facts_path, default={})

    def save_env_facts(self, env_facts: Dict[str, Any]) -> None:
        """保存环境事实。

        自动追加 `updated_at`，用于判断环境探测结果是否过期。
        """

        payload = dict(env_facts)
        payload["updated_at"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        self._write_json(self.env_facts_path, payload)

    def save_run(self, run_id: str, run_payload: Dict[str, Any]) -> str:
        """保存执行记录并返回路径。

        Parameters
        ----------
        run_id : str
            执行记录唯一 ID。
        run_payload : Dict[str, Any]
            执行结果内容。

        Returns
        -------
        str
            已保存 run 文件路径。
        """

        target = self.runs_dir / f"{run_id}.json"
        payload = dict(run_payload)
        payload["saved_at"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        self._write_json(target, payload)
        return str(target)

    def load_run(self, run_id: str) -> Dict[str, Any]:
        """按 run_id 读取执行记录。"""

        target = self.runs_dir / f"{run_id}.json"
        return self._read_json(target, default={})

    def list_runs(self) -> List[str]:
        """返回 run_id 列表。

        返回值按文件名排序，便于前端稳定展示与测试断言。
        """

        return sorted(path.stem for path in self.runs_dir.glob("*.json"))

    def clear_runs(self) -> None:
        """清空 runs 目录。

        该方法只删除 `runs/*.json`，不触及 profile/env_facts。
        """

        for path in self.runs_dir.glob("*.json"):
            path.unlink(missing_ok=True)
