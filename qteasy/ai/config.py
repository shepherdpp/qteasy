# coding=utf-8
# ======================================
# File: config.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-16
# Desc:
# qteasy AI 外壳配置中心，统一配置读取
# 优先级与兼容策略。
# ======================================

"""AI 外壳配置中心。

本模块实现 A0 的 ConfigCenter 决策，统一读取优先级：

1. 显式参数；
2. 环境变量；
3. QT_CONFIG；
4. 默认值。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ConfigValueTrace:
    """配置读取追踪信息。"""

    key: str
    value: Any
    source: str


class ConfigCenter:
    """统一 AI 配置读取的最小实现。"""

    def __init__(
        self,
        *,
        env: Optional[Dict[str, str]] = None,
        qt_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.env = env if env is not None else os.environ
        self.qt_config = qt_config
        self._last_trace: Dict[str, ConfigValueTrace] = {}

    def _get_qt_config(self) -> Dict[str, Any]:
        """懒加载 QT_CONFIG。"""

        if self.qt_config is not None:
            return self.qt_config
        try:
            import qteasy as qt
        except Exception:
            return {}
        config = getattr(qt, "QT_CONFIG", None)
        if isinstance(config, dict):
            return config
        return {}

    def resolve(
        self,
        key: str,
        *,
        explicit: Any = None,
        env_key: Optional[str] = None,
        qt_key: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        """按优先级读取单个配置值。"""

        if explicit is not None:
            self._last_trace[key] = ConfigValueTrace(key=key, value=explicit, source="explicit")
            return explicit

        env_name = env_key or key.upper()
        env_val = self.env.get(env_name)
        if env_val not in (None, ""):
            self._last_trace[key] = ConfigValueTrace(key=key, value=env_val, source="env")
            return env_val

        qt_name = qt_key or key
        qt_val = self._get_qt_config().get(qt_name)
        if qt_val not in (None, ""):
            self._last_trace[key] = ConfigValueTrace(key=key, value=qt_val, source="qt_config")
            return qt_val

        self._last_trace[key] = ConfigValueTrace(key=key, value=default, source="default")
        return default

    def get_trace(self) -> Dict[str, Dict[str, Any]]:
        """返回最近一次读取追踪。"""

        return {
            key: {"value": item.value, "source": item.source}
            for key, item in self._last_trace.items()
        }

    def resolve_provider_config(
        self,
        *,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """读取 Provider 配置集合。"""

        timeout_val = self.resolve(
            "timeout",
            explicit=timeout,
            env_key="QTEASY_AI_TIMEOUT",
            qt_key="ai_timeout",
            default=30,
        )
        if isinstance(timeout_val, str) and timeout_val.isdigit():
            timeout_val = int(timeout_val)
        return {
            "model": self.resolve(
                "model",
                explicit=model,
                env_key="QTEASY_AI_MODEL",
                qt_key="ai_model",
                default="",
            ),
            "api_key": self.resolve(
                "api_key",
                explicit=api_key,
                env_key="QTEASY_AI_API_KEY",
                qt_key="ai_api_key",
                default="",
            ),
            "base_url": self.resolve(
                "base_url",
                explicit=base_url,
                env_key="QTEASY_AI_BASE_URL",
                qt_key="ai_base_url",
                default="https://api.openai.com/v1",
            ),
            "timeout": timeout_val,
        }

