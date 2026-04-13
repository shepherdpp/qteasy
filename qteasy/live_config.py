# coding=utf-8
# ======================================
# File: live_config.py
# Author: Jackie PENG / qteasy
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-12
# Desc:
#   模拟实盘运行前配置快照：从全局配置或 dict 浅合并 overrides 后校验并冻结（S1.3 P2）。
# ======================================

from __future__ import annotations

import warnings
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple, Union

from qteasy.configure import ConfigDict
from qteasy.utilfuncs import str_to_list

# 与 _arg_validators 中 live_trade / live_price 相关校验语义对齐
_ALLOWED_LIVE_TRADE_BROKER_TYPES = frozenset({'simulator', 'simple', 'manual', 'random'})
_ALLOWED_LIVE_PRICE_CHANNELS = frozenset({'eastmoney', 'tushare', 'akshare'})
_ALLOWED_REFILL_CHANNELS = frozenset({'eastmoney', 'tushare', 'akshare'})
_ALLOWED_LIVE_PRICE_FREQ = frozenset({'H', '30MIN', '15MIN', '5MIN', '1MIN', 'TICK'})
_ALLOWED_LIVE_TRADE_UI = frozenset({'cli', 'tui'})


def _strict_hhmmss(value: str, field_name: str) -> str:
    """校验并返回规范化的 HH:MM:SS 时间字符串；拒绝依赖宽松解析的写法（如仅有 H:MM）。"""
    if not isinstance(value, str):
        raise TypeError(f'{field_name} must be str, got {type(value).__name__} instead.')
    parts = value.split(':')
    if len(parts) != 3:
        raise ValueError(
            f'Invalid {field_name}: expected time in HH:MM:SS format, got {value!r} instead.'
        )
    try:
        h, m, s = (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError as exc:
        raise ValueError(
            f'Invalid {field_name}: expected integer hour, minute, second in {value!r}.'
        ) from exc
    if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59):
        raise ValueError(
            f'Invalid {field_name}: time out of range in {value!r}.'
        )
    return f'{h:02d}:{m:02d}:{s:02d}'


def _norm_broker_params(
    raw: Any,
) -> Optional[Tuple[Tuple[str, Any], ...]]:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise TypeError(
            f'live_trade_broker_params must be dict or None, got {type(raw).__name__} instead.'
        )
    items = tuple(sorted(raw.items(), key=lambda kv: kv[0]))
    return items


def _norm_asset_pool(value: Any) -> Union[str, Tuple[str, ...]]:
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return tuple(str(x) for x in value)
    raise TypeError(
        f'asset_pool must be str, list, or tuple, got {type(value).__name__} instead.'
    )


def _norm_benchmark(value: Any) -> Union[str, Tuple[str, ...]]:
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return tuple(str(x) for x in value)
    raise TypeError(
        f'benchmark_asset must be str, list, or tuple, got {type(value).__name__} instead.'
    )


def _merged_mapping(
    config: Union[Mapping[str, Any], ConfigDict],
    overrides: Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(config, ConfigDict) or isinstance(config, dict):
        base = dict(config)
    else:
        base = dict(config)
    base.update(dict(overrides))
    return base


@dataclass(frozen=True)
class LiveTradeConfig:
    """一次 live 运行的已校验配置快照（不可变）。

    由 ``build_live_trade_config`` 构造；字段与 ``Operator.run_live_trade`` 传入 ``Trader`` 的
    标量配置对齐；可选扩展键经 ``overrides`` 写入 ``extra``，便于后续接入柜台专用参数。
    """

    asset_pool: Union[str, Tuple[str, ...]]
    asset_type: str
    time_zone: str
    market_open_time_am: str
    market_close_time_am: str
    market_open_time_pm: str
    market_close_time_pm: str
    live_price_acquire_channel: str
    live_price_acquire_freq: str
    live_trade_data_refill_channel: str
    live_trade_data_refill_batch_size: int
    live_trade_data_refill_batch_interval: int
    watched_price_refresh_interval: int
    benchmark_asset: Union[str, Tuple[str, ...]]
    pt_buy_threshold: float
    pt_sell_threshold: float
    allow_sell_short: bool
    trade_batch_size: float
    sell_batch_size: float
    long_position_limit: float
    short_position_limit: float
    stock_delivery_period: int
    cash_delivery_period: int
    strategy_open_close_timing_offset: int
    live_trade_daily_refill_tables: str
    live_trade_weekly_refill_tables: str
    live_trade_monthly_refill_tables: str
    live_trade_broker_type: str
    live_trade_broker_params: Optional[Tuple[Tuple[str, Any], ...]]
    live_trade_ui_type: str
    live_trade_account_id: Optional[int]
    extra: Mapping[str, Any]

    def to_summary_dict(self) -> dict[str, Any]:
        """返回用于日志/断点的稳定子集摘要（JSON 友好）。

        Parameters
        ----------
        无

        Returns
        -------
        dict[str, Any]
            键名稳定的字典；值为 ``str`` / ``int`` / ``float`` / ``bool`` / ``None`` 或
            由 ``asset_pool``、``benchmark_asset`` 展开得到的普通 ``list``。
        """
        pool = self.asset_pool
        if isinstance(pool, tuple):
            pool_list = list(pool)
        else:
            pool_list = pool
        bench = self.benchmark_asset
        if isinstance(bench, tuple):
            bench_out: Union[str, list[str]] = list(bench)
        else:
            bench_out = bench
        params: Optional[dict[str, Any]]
        if self.live_trade_broker_params is None:
            params = None
        else:
            params = dict(self.live_trade_broker_params)
        return {
            'broker_type': self.live_trade_broker_type,
            'live_price_channel': self.live_price_acquire_channel,
            'live_price_freq': self.live_price_acquire_freq,
            'asset_type': self.asset_type,
            'time_zone': self.time_zone,
            'live_trade_ui_type': self.live_trade_ui_type,
            'live_trade_account_id': self.live_trade_account_id,
            'asset_pool': pool_list,
            'benchmark_asset': bench_out,
            'live_trade_broker_params': params,
        }


def build_live_trade_config(
    config: Union[Mapping[str, Any], ConfigDict],
    **overrides: Any,
) -> LiveTradeConfig:
    """从配置映射与 overrides 浅合并后校验，构造 ``LiveTradeConfig``。

    缺省键使用与全局配置一致的默认值；校验规则与 ``_arg_validators`` 中 live 相关项对齐。

    Parameters
    ----------
    config : Mapping[str, Any] or ConfigDict
        含实盘相关键的配置（通常为 ``QT_CONFIG`` 或子集 dict）。
    **overrides : Any
        覆盖 ``config`` 的同名字段（浅合并；嵌套 dict 整体替换）。

    Returns
    -------
    LiveTradeConfig
        冻结后的合法配置快照。

    Raises
    ------
    TypeError
        参数类型非法；异常消息为英文。
    ValueError
        取值非法；异常消息为英文。
    """
    merged = _merged_mapping(config, overrides)

    # 默认值与 _arg_validators 对齐（仅列出本模块校验用到的键）
    defaults: dict[str, Any] = {
        'time_zone': 'local',
        'market_open_time_am': '09:30:00',
        'market_close_time_am': '11:30:00',
        'market_open_time_pm': '13:00:00',
        'market_close_time_pm': '15:00:00',
        'live_price_acquire_channel': 'eastmoney',
        'live_price_acquire_freq': '15MIN',
        'live_trade_data_refill_channel': 'eastmoney',
        'live_trade_data_refill_batch_size': 0,
        'live_trade_data_refill_batch_interval': 0,
        'watched_price_refresh_interval': 5,
        'benchmark_asset': '000300.SH',
        'PT_buy_threshold': 0.0,
        'PT_sell_threshold': 0.0,
        'allow_sell_short': False,
        'trade_batch_size': 0.01,
        'sell_batch_size': 0.01,
        'long_position_limit': 1.0,
        'short_position_limit': -1.0,
        'stock_delivery_period': 1,
        'cash_delivery_period': 0,
        'strategy_open_close_timing_offset': 1,
        'live_trade_daily_refill_tables': '',
        'live_trade_weekly_refill_tables': '',
        'live_trade_monthly_refill_tables': '',
        'live_trade_broker_type': 'simulator',
        'live_trade_broker_params': None,
        'live_trade_ui_type': 'cli',
        'live_trade_account_id': None,
        'asset_pool': '000300.SH',
        'asset_type': 'E',
    }
    for k, v in defaults.items():
        if k not in merged:
            merged[k] = v

    asset_pool = _norm_asset_pool(merged['asset_pool'])
    asset_type = merged['asset_type']
    if not isinstance(asset_type, str):
        raise TypeError(f'asset_type must be str, got {type(asset_type).__name__} instead.')

    time_zone = merged['time_zone']
    if not isinstance(time_zone, str) or not time_zone:
        raise ValueError('Invalid time_zone: must be a non-empty string.')

    mo_am = _strict_hhmmss(merged['market_open_time_am'], 'market_open_time_am')
    mc_am = _strict_hhmmss(merged['market_close_time_am'], 'market_close_time_am')
    mo_pm = _strict_hhmmss(merged['market_open_time_pm'], 'market_open_time_pm')
    mc_pm = _strict_hhmmss(merged['market_close_time_pm'], 'market_close_time_pm')

    lpc = merged['live_price_acquire_channel']
    if not isinstance(lpc, str):
        raise TypeError(
            f'live_price_acquire_channel must be str, got {type(lpc).__name__} instead.'
        )
    lpc_norm = lpc.lower().strip()
    if lpc_norm not in _ALLOWED_LIVE_PRICE_CHANNELS:
        raise ValueError(
            f'Invalid live_price_acquire_channel: {lpc!r}. '
            f'Allowed values: {sorted(_ALLOWED_LIVE_PRICE_CHANNELS)}.'
        )

    freq_raw = merged['live_price_acquire_freq']
    if not isinstance(freq_raw, str):
        raise TypeError(
            f'live_price_acquire_freq must be str, got {type(freq_raw).__name__} instead.'
        )
    freq_norm = freq_raw.strip().upper()
    if freq_norm not in _ALLOWED_LIVE_PRICE_FREQ:
        raise ValueError(
            f'Invalid live_price_acquire_freq: {freq_raw!r}. '
            f'Allowed values: {sorted(_ALLOWED_LIVE_PRICE_FREQ)}.'
        )

    refill = merged['live_trade_data_refill_channel']
    if not isinstance(refill, str):
        raise TypeError(
            f'live_trade_data_refill_channel must be str, got {type(refill).__name__} instead.'
        )
    if refill not in _ALLOWED_REFILL_CHANNELS:
        raise ValueError(
            f'Invalid live_trade_data_refill_channel: {refill!r}. '
            f'Allowed values (case-sensitive): {sorted(_ALLOWED_REFILL_CHANNELS)}.'
        )

    batch_size = merged['live_trade_data_refill_batch_size']
    batch_interval = merged['live_trade_data_refill_batch_interval']
    if not isinstance(batch_size, int):
        raise TypeError(
            f'live_trade_data_refill_batch_size must be int, got {type(batch_size).__name__} instead.'
        )
    if not isinstance(batch_interval, int):
        raise TypeError(
            f'live_trade_data_refill_batch_interval must be int, got {type(batch_interval).__name__} instead.'
        )

    wpri = merged['watched_price_refresh_interval']
    if not isinstance(wpri, int):
        raise TypeError(
            f'watched_price_refresh_interval must be int, got {type(wpri).__name__} instead.'
        )
    if wpri < 5:
        raise ValueError(
            f'Invalid watched_price_refresh_interval: {wpri}, must be >= 5.'
        )

    benchmark_asset = _norm_benchmark(merged['benchmark_asset'])

    pt_buy = merged['PT_buy_threshold']
    pt_sell = merged['PT_sell_threshold']
    if not isinstance(pt_buy, (int, float)):
        raise TypeError(f'PT_buy_threshold must be a number, got {type(pt_buy).__name__} instead.')
    if not isinstance(pt_sell, (int, float)):
        raise TypeError(f'PT_sell_threshold must be a number, got {type(pt_sell).__name__} instead.')

    allow_short = merged['allow_sell_short']
    if not isinstance(allow_short, bool):
        raise TypeError(
            f'allow_sell_short must be bool, got {type(allow_short).__name__} instead.'
        )

    tbs = merged['trade_batch_size']
    sbs = merged['sell_batch_size']
    if not isinstance(tbs, (int, float)):
        raise TypeError(f'trade_batch_size must be a number, got {type(tbs).__name__} instead.')
    if not isinstance(sbs, (int, float)):
        raise TypeError(f'sell_batch_size must be a number, got {type(sbs).__name__} instead.')
    if float(tbs) < 0.01:
        raise ValueError(
            f'Invalid trade_batch_size: {tbs}, must be >= 0.01.'
        )
    if float(sbs) < 0.01:
        raise ValueError(
            f'Invalid sell_batch_size: {sbs}, must be >= 0.01.'
        )

    long_lim = merged['long_position_limit']
    short_lim = merged['short_position_limit']
    if not isinstance(long_lim, (int, float)) or float(long_lim) <= 0:
        raise ValueError(
            f'Invalid long_position_limit: {long_lim}, must be a number > 0.'
        )
    if not isinstance(short_lim, (int, float)) or float(short_lim) >= 0:
        raise ValueError(
            f'Invalid short_position_limit: {short_lim}, must be a number < 0.'
        )

    sdp = merged['stock_delivery_period']
    cdp = merged['cash_delivery_period']
    if not isinstance(sdp, int) or sdp not in range(0, 5):
        raise ValueError(
            f'Invalid stock_delivery_period: {sdp}, must be an integer in [0, 4].'
        )
    if not isinstance(cdp, int) or cdp not in range(0, 5):
        raise ValueError(
            f'Invalid cash_delivery_period: {cdp}, must be an integer in [0, 4].'
        )

    oc_offset = merged['strategy_open_close_timing_offset']
    if not isinstance(oc_offset, int) or oc_offset not in range(0, 5):
        raise ValueError(
            f'Invalid strategy_open_close_timing_offset: {oc_offset}, must be an integer in [0, 4].'
        )

    for tbl_key in (
        'live_trade_daily_refill_tables',
        'live_trade_weekly_refill_tables',
        'live_trade_monthly_refill_tables',
    ):
        v = merged[tbl_key]
        if not isinstance(v, str):
            raise TypeError(f'{tbl_key} must be str, got {type(v).__name__} instead.')

    broker_raw = merged['live_trade_broker_type']
    if not isinstance(broker_raw, str):
        raise TypeError(
            f'live_trade_broker_type must be str, got {type(broker_raw).__name__} instead.'
        )
    broker_norm = broker_raw.lower().strip()
    if broker_norm not in _ALLOWED_LIVE_TRADE_BROKER_TYPES:
        raise ValueError(
            f'Invalid live_trade_broker_type: {broker_raw!r}. '
            f'Allowed values: {sorted(_ALLOWED_LIVE_TRADE_BROKER_TYPES)}.'
        )
    if broker_norm == 'random':
        warnings.warn(
            'The broker name "random" is deprecated and will be removed in qteasy 2.0. '
            'Use "simulator" instead.',
            FutureWarning,
            stacklevel=2,
        )

    broker_params = _norm_broker_params(merged['live_trade_broker_params'])

    ui_raw = merged['live_trade_ui_type']
    if not isinstance(ui_raw, str):
        raise TypeError(
            f'live_trade_ui_type must be str, got {type(ui_raw).__name__} instead.'
        )
    ui_norm = ui_raw.lower().strip()
    if ui_norm not in _ALLOWED_LIVE_TRADE_UI:
        raise ValueError(
            f'Invalid live_trade_ui_type: {ui_raw!r}. Allowed values: {sorted(_ALLOWED_LIVE_TRADE_UI)}.'
        )

    account_id = merged['live_trade_account_id']
    if account_id is not None and not isinstance(account_id, int):
        raise TypeError(
            f'live_trade_account_id must be int or None, got {type(account_id).__name__} instead.'
        )

    # 仅将 overrides 中未消费的键纳入 extra，避免把整个 QT_CONFIG 快照进 frozen 对象
    reserved_keys = set(defaults) | {
        'live_trade_init_holdings',
        'cost_rate_buy',
        'cost_rate_sell',
        'cost_min_buy',
        'cost_min_sell',
        'cost_slippage',
        'mode',
    }
    extra_items: dict[str, Any] = {
        k: overrides[k] for k in overrides if k not in reserved_keys
    }
    extra_view: Mapping[str, Any] = MappingProxyType(dict(sorted(extra_items.items())))

    return LiveTradeConfig(
        asset_pool=asset_pool,
        asset_type=asset_type,
        time_zone=time_zone,
        market_open_time_am=mo_am,
        market_close_time_am=mc_am,
        market_open_time_pm=mo_pm,
        market_close_time_pm=mc_pm,
        live_price_acquire_channel=lpc_norm,
        live_price_acquire_freq=freq_norm,
        live_trade_data_refill_channel=refill,
        live_trade_data_refill_batch_size=batch_size,
        live_trade_data_refill_batch_interval=batch_interval,
        watched_price_refresh_interval=wpri,
        benchmark_asset=benchmark_asset,
        pt_buy_threshold=float(pt_buy),
        pt_sell_threshold=float(pt_sell),
        allow_sell_short=allow_short,
        trade_batch_size=float(tbs),
        sell_batch_size=float(sbs),
        long_position_limit=float(long_lim),
        short_position_limit=float(short_lim),
        stock_delivery_period=sdp,
        cash_delivery_period=cdp,
        strategy_open_close_timing_offset=oc_offset,
        live_trade_daily_refill_tables=merged['live_trade_daily_refill_tables'],
        live_trade_weekly_refill_tables=merged['live_trade_weekly_refill_tables'],
        live_trade_monthly_refill_tables=merged['live_trade_monthly_refill_tables'],
        live_trade_broker_type=broker_norm,
        live_trade_broker_params=broker_params,
        live_trade_ui_type=ui_norm,
        live_trade_account_id=account_id,
        extra=extra_view,
    )


def live_trade_config_to_trader_kwargs(cfg: LiveTradeConfig) -> dict[str, Any]:
    """将 ``LiveTradeConfig`` 映射为 ``Trader`` 构造函数使用的关键字子集（供内部复用）。

    Parameters
    ----------
    cfg : LiveTradeConfig
        已校验配置。

    Returns
    -------
    dict[str, Any]
        与 ``Trader`` 实例属性对应的关键字子集。
    """
    if isinstance(cfg.asset_pool, tuple):
        ap: Union[str, list] = list(cfg.asset_pool)
    else:
        ap = cfg.asset_pool
    if isinstance(cfg.benchmark_asset, tuple):
        bench_out_kw: Union[str, list] = list(cfg.benchmark_asset)
    else:
        bench_out_kw = cfg.benchmark_asset
    freq_for_trader = cfg.live_price_acquire_freq.lower()
    return {
        'asset_pool': ap,
        'asset_type': cfg.asset_type,
        'time_zone': cfg.time_zone,
        'market_open_time_am': cfg.market_open_time_am,
        'market_close_time_am': cfg.market_close_time_am,
        'market_open_time_pm': cfg.market_open_time_pm,
        'market_close_time_pm': cfg.market_close_time_pm,
        'live_price_channel': cfg.live_price_acquire_channel,
        'live_price_freq': freq_for_trader,
        'live_data_channel': cfg.live_trade_data_refill_channel,
        'live_data_batch_size': cfg.live_trade_data_refill_batch_size,
        'live_data_batch_interval': cfg.live_trade_data_refill_batch_interval,
        'watched_price_refresh_interval': cfg.watched_price_refresh_interval,
        'benchmark_asset': bench_out_kw,
        'pt_buy_threshold': cfg.pt_buy_threshold,
        'pt_sell_threshold': cfg.pt_sell_threshold,
        'allow_sell_short': cfg.allow_sell_short,
        'trade_batch_size': cfg.trade_batch_size,
        'sell_batch_size': cfg.sell_batch_size,
        'long_position_limit': cfg.long_position_limit,
        'short_position_limit': cfg.short_position_limit,
        'stock_delivery_period': cfg.stock_delivery_period,
        'cash_delivery_period': cfg.cash_delivery_period,
        'open_close_timing_offset': cfg.strategy_open_close_timing_offset,
        'daily_refill_tables': cfg.live_trade_daily_refill_tables,
        'weekly_refill_tables': cfg.live_trade_weekly_refill_tables,
        'monthly_refill_tables': cfg.live_trade_monthly_refill_tables,
    }


def apply_live_trade_config_to_trader(trader: Any, cfg: LiveTradeConfig) -> None:
    """用已校验的 ``LiveTradeConfig`` 覆盖 ``Trader`` 上与 live 相关的属性。

    Parameters
    ----------
    trader : Trader
        已按 kwargs 完成初始化的 ``Trader`` 实例。
    cfg : LiveTradeConfig
        由 ``build_live_trade_config`` 得到的快照。

    Returns
    -------
    None
    """
    kwargs = live_trade_config_to_trader_kwargs(cfg)
    if isinstance(kwargs['asset_pool'], list):
        trader._asset_pool = kwargs['asset_pool']
    elif isinstance(kwargs['asset_pool'], str):
        trader._asset_pool = str_to_list(kwargs['asset_pool'])
    else:
        trader._asset_pool = list(kwargs['asset_pool'])
    trader._asset_type = kwargs['asset_type']
    trader.time_zone = kwargs['time_zone']
    trader.market_open_time_am = kwargs['market_open_time_am']
    trader.market_close_time_am = kwargs['market_close_time_am']
    trader.market_open_time_pm = kwargs['market_open_time_pm']
    trader.market_close_time_pm = kwargs['market_close_time_pm']
    trader.live_price_channel = kwargs['live_price_channel']
    trader.live_price_freq = kwargs['live_price_freq']
    trader.live_data_channel = kwargs['live_data_channel']
    trader.live_data_batch_size = kwargs['live_data_batch_size']
    trader.live_data_batch_interval = kwargs['live_data_batch_interval']
    trader.watched_price_refresh_interval = kwargs['watched_price_refresh_interval']
    bench = kwargs['benchmark_asset']
    if isinstance(bench, str):
        benchmark_list = str_to_list(bench)
    elif isinstance(bench, list):
        benchmark_list = bench[:]
    else:
        benchmark_list = list(bench)
    trader.benchmark = bench
    trader.watch_list = benchmark_list + trader._asset_pool
    trader.pt_buy_threshold = kwargs['pt_buy_threshold']
    trader.pt_sell_threshold = kwargs['pt_sell_threshold']
    trader.allow_sell_short = kwargs['allow_sell_short']
    trader.trade_batch_size = kwargs['trade_batch_size']
    trader.sell_batch_size = kwargs['sell_batch_size']
    trader.long_position_limit = kwargs['long_position_limit']
    trader.short_position_limit = kwargs['short_position_limit']
    trader.stock_delivery_period = kwargs['stock_delivery_period']
    trader.cash_delivery_period = kwargs['cash_delivery_period']
    trader.open_close_timing_offset = kwargs['open_close_timing_offset']
    trader.daily_refill_tables = kwargs['daily_refill_tables']
    trader.weekly_refill_tables = kwargs['weekly_refill_tables']
    trader.monthly_refill_tables = kwargs['monthly_refill_tables']
