# coding=utf-8
# ======================================
# File:     trader_cli.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-04-10
# Desc:
#   A command line interface (CLI) for
# qteasy live trade system, separated
# from original trader.py for better
# code organization.
# ======================================


import argparse
import rich
import shlex
import shutil
import sys
import time
import traceback
from threading import Thread

import numpy as np
import pandas as pd

from typing import Any, Dict, List, Optional
from cmd import Cmd
from rich.console import Console
from rich.text import Text

from qteasy.trader import (
    TraderMessage,
    TaskSpec,
    coerce_trader_message,
    drain_trader_message_queue,
    group_sys_log_physical_lines,
    _is_debug_sys_log_line,
)
from qteasy.trading_util import get_symbol_names, cancel_order
from qteasy.data_channels import list_builtin_channels

from qteasy.utilfuncs import (
    adjust_string_length,
    sec_to_duration,
    list_to_str_format,
)

# DEBUG 模式下 ``run --task`` 可手动触发的任务白名单（与 ``Trader._run_task`` 子集对齐）
DEBUG_RUN_TASK_CHOICES = (
    'process_result',
    'pre_open',
    'open_market',
    'close_market',
    'post_close',
    'refill',
    'diagnose_pending_orders',
)

# ``precmd`` 命令别名（``Cmd`` 不支持带连字符的 ``do_*`` 方法名）
CLI_COMMAND_ALIASES = {
    'ls-artifacts': 'artifacts',
    'live-config': 'liveconfig',
    'startup-gate': 'gate',
    'snapshot-reconcile': 'reconcile',
    'rotate-logs': 'rotatelogs',
    'rotatelog': 'rotatelogs',
    'pull-state': 'sync',
}

BROKER_SUBCOMMANDS = ('status', 'connect', 'disconnect')
SUPPORTED_DATA_CHANNELS = list_builtin_channels()


def _terminal_width(fallback: int = 80) -> int:
    """返回当前终端宽度，不可检测时返回 fallback。"""
    try:
        return int(shutil.get_terminal_size(fallback=(fallback, 24)).columns)
    except (ValueError, OSError):
        return fallback


def _is_tty_stream(stream) -> bool:
    """判断流是否连接到交互式终端。"""
    return hasattr(stream, 'isatty') and stream.isatty()


def _clear_current_line(stream=sys.stdout) -> None:
    """清除终端当前行内容（仅 TTY 生效）。"""
    if _is_tty_stream(stream):
        stream.write('\r\033[K')
        stream.flush()


def _truncate_text_to_cell_width(text: Text, max_width: int) -> Text:
    """按终端显示列宽截断 Rich Text（中文等宽字符占双列）。

    Parameters
    ----------
    text : rich.text.Text
        待截断文本。
    max_width : int
        最大显示列宽。

    Returns
    -------
    rich.text.Text
        截断后的副本。
    """
    line = text.copy()
    while line.cell_len > max_width and len(line.plain) > 0:
        line.truncate(len(line.plain) - 1, overflow='crop')
    return line


def _filter_sys_log_lines(lines: List[str], include_debug: bool = True) -> List[str]:
    """过滤系统日志行，可选排除 DEBUG 级别内容。

    Parameters
    ----------
    lines : list of str
        原始日志行列表。
    include_debug : bool, optional, default True
        为 False 时排除 ``DEBUG:`` 开头或含 ``<DEBUG>`` 的行。

    Returns
    -------
    list of str
        过滤后的日志行。
    """
    grouped = group_sys_log_physical_lines(lines)
    if include_debug:
        return grouped
    return [line for line in grouped if not _is_debug_sys_log_line(line)]


def _format_bool_markup(value: bool) -> str:
    """将布尔值格式化为带 Rich 颜色的字符串（用户可见英文 True/False）。"""
    if value:
        return '[bold green]True[/bold green]'
    return '[bold red]False[/bold red]'


def _format_scalar_for_display(value: Any, *, list_preview: int = 5) -> str:
    """将标量/简单容器格式化为 CLI 可读字符串。"""
    if value is None:
        return '--'
    if isinstance(value, bool):
        return _format_bool_markup(value)
    if isinstance(value, float):
        if np.isnan(value):
            return '--'
        return f'{value:,.4f}'.rstrip('0').rstrip('.')
    if isinstance(value, (list, tuple)):
        items = list(value)
        if not items:
            return '[]'
        preview = items[:list_preview]
        text = ', '.join(str(item) for item in preview)
        if len(items) > list_preview:
            text += f', ...({len(items)} total)'
        return text
    if isinstance(value, dict):
        if not value:
            return '{}'
        parts = [f'{k}={v}' for k, v in list(value.items())[:list_preview]]
        text = ', '.join(parts)
        if len(value) > list_preview:
            text += f', ...({len(value)} keys)'
        return text
    return str(value)


def _print_key_value_section(title: str, items: Dict[str, Any], *, width: Optional[int] = None) -> None:
    """以 overview 风格打印键值分段（支持 Rich 颜色 markup）。"""
    if width is None:
        width = _terminal_width()
    semi_width = int(width * 0.75)
    info_str = f'{{" {title} ":=^{width}}}\n'
    for key, value in items.items():
        formatted = _format_scalar_for_display(value)
        info_str += f'{key:<{semi_width - 20}}{formatted}\n'
    rich.print(info_str, end='')


def _normalize_task_status_filter(status: Optional[str]) -> Optional[str]:
    """归一化 task 列表命令的状态过滤参数。"""
    if status is None:
        return None
    normalized = str(status).strip().lower()
    if normalized in ('', 'all', 'a'):
        return None
    if normalized in ('queued', 'q', 'in-queue', 'in_queue', 'in queue'):
        return 'queued'
    return str(status).strip()


def format_trader_tasks_table(tasks: List[TaskSpec], *, rich_form: bool = True) -> str:
    """将 Trader 任务列表格式化为与 schedule 类似的表格字符串。

    Parameters
    ----------
    tasks : list of TaskSpec
        待展示任务列表。
    rich_form : bool, optional
        是否替换方括号以避免 Rich 误解析。

    Returns
    -------
    str
        表格字符串；无任务时返回提示语。
    """
    if not tasks:
        return 'No trader tasks found.'

    rows = []
    for task_spec in tasks:
        rows.append({
            'task_id': task_spec.task_id,
            'name': task_spec.name,
            'status': task_spec.status,
            'retry': f'{task_spec.retry_count}/{task_spec.max_retries}',
            'args': str(task_spec.args),
            'canceled': task_spec.canceled,
        })
    task_df = pd.DataFrame(rows).set_index('task_id')
    table_string = task_df.to_string()
    if rich_form:
        table_string = table_string.replace('[', '<')
        table_string = table_string.replace(']', '>')
    return table_string


def _drain_message_queue(trader) -> List[TraderMessage]:
    """排空 trader 消息队列并返回结构化消息列表。"""
    return drain_trader_message_queue(trader.message_queue)


class ModeMenuExitRequest(Exception):
    """用户在模式选单等待期间再次按下 Ctrl+C，请求立即正常退出 Shell。"""
    pass


MODE_MENU_TIMEOUT = 5.0


def _mode_menu_prompt() -> str:
    """返回 Ctrl+C 中断后模式选单的英文提示文本。"""
    return (
        '\nCurrent mode interrupted. Press 1, 2, or 3 within '
        f'{MODE_MENU_TIMEOUT:.0f} seconds (no Enter needed):\n'
        'Press Ctrl+C again to exit immediately.\n'
        '[1] Enter command mode\n'
        '[2] Enter dashboard mode\n'
        '[3] Exit and stop the trader\n'
        'Your choice: '
    )


def _parse_mode_menu_choice(line: Optional[str]) -> str:
    """解析模式选单输入，返回 ``command`` / ``dashboard`` / ``exit`` / ``resume``。"""
    if line is None:
        return 'resume'
    stripped = line.strip()
    if stripped == '1':
        return 'command'
    if stripped == '2':
        return 'dashboard'
    if stripped == '3':
        return 'exit'
    return 'resume'


ERROR_RECOVERY_TIMEOUT = 5.0


def _error_recovery_prompt() -> str:
    """返回运行时异常恢复选单的英文提示文本。"""
    return (
        '\nAn unexpected error occurred. Press 1 to return to dashboard, '
        f'3 to exit (default dashboard in {ERROR_RECOVERY_TIMEOUT:.0f}s, no Enter needed):\n'
        'Your choice: '
    )


def _parse_error_recovery_choice(line: Optional[str]) -> str:
    """解析运行时异常恢复选单输入，返回 ``dashboard`` 或 ``exit``。"""
    if line == '3':
        return 'exit'
    return 'dashboard'


def _accept_mode_menu_char(ch: str, line_parts: List[str]) -> Optional[str]:
    """解析模式选单单字节字符，立即接受 1/2/3；回车提交缓冲区中的合法选择。

    非 1/2/3 的可打印字符被忽略；缓冲区仅在回车时按合法选择提交或清空。

    Parameters
    ----------
    ch : str
        读取到的单个字符。
    line_parts : list of str
        跨多次读取累积的缓冲片段（不含已立即提交的 1/2/3）。

    Returns
    -------
    str or None
        已确定的选项 ``'1'`` / ``'2'`` / ``'3'``；否则 ``None`` 表示继续读取。
    """
    if ch in ('1', '2', '3'):
        line_parts.clear()
        return ch
    if ch in ('\n', '\r'):
        buf = ''.join(line_parts)
        line_parts.clear()
        if buf in ('1', '2', '3'):
            return buf
        return None
    return None


def _read_line_with_timeout_unix(timeout, input_stream, output_stream) -> Optional[str]:
    """在 Unix 上使用 ``termios`` 原始字符模式与 ``select`` 读取选单输入，超时返回 ``None``。"""
    import select
    import termios
    import tty

    fd = input_stream.fileno()
    old_settings = termios.tcgetattr(fd)
    line_parts: List[str] = []
    try:
        tty.setcbreak(fd)
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                output_stream.write('\n')
                output_stream.flush()
                return None
            ready, _, _ = select.select([input_stream], [], [], remaining)
            if not ready:
                output_stream.write('\n')
                output_stream.flush()
                return None
            ch = input_stream.read(1)
            if not ch:
                output_stream.write('\n')
                output_stream.flush()
                return None
            if ch == '\x03':
                raise ModeMenuExitRequest
            decision = _accept_mode_menu_char(ch, line_parts)
            if decision is not None:
                output_stream.write(decision + '\n')
                output_stream.flush()
                return decision
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _read_line_with_timeout_windows(timeout, input_stream, output_stream) -> Optional[str]:
    """在 Windows 上使用 ``msvcrt`` 轮询读取选单输入，1/2/3 立即生效，超时返回 ``None``。"""
    import msvcrt

    line_parts: List[str] = []
    deadline = time.monotonic() + timeout
    while True:
        if time.monotonic() >= deadline:
            output_stream.write('\n')
            output_stream.flush()
            return None
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch == '\x03':
                raise ModeMenuExitRequest
            decision = _accept_mode_menu_char(ch, line_parts)
            if decision is not None:
                output_stream.write(decision + '\n')
                output_stream.flush()
                return decision
        else:
            time.sleep(0.05)


def _read_line_with_timeout(
        prompt: str,
        timeout: float = MODE_MENU_TIMEOUT,
        input_stream=sys.stdin,
        output_stream=sys.stdout,
) -> Optional[str]:
    """在 TTY 上带超时读取一行；非 TTY 或超时返回 ``None``。"""
    if not _is_tty_stream(input_stream):
        return None
    output_stream.write(prompt)
    output_stream.flush()
    if sys.platform == 'win32':
        return _read_line_with_timeout_windows(timeout, input_stream, output_stream)
    return _read_line_with_timeout_unix(timeout, input_stream, output_stream)


def pack_system_info(trader_info, width=80):
    """ 打包账户信息字符串, 用于在shell中格式化显示trader_info中的系统信息

    Parameters
    ----------
    trader_info: dict
        包含账户信息的字典
    width: int
        字符串的宽度

    Returns
    -------
    str
        包含账户信息的字符串
    """
    semi_width = int(width * 0.75)

    info_str = ''

    # System Info
    info_str += f'{" System Info ":=^{width}}\n'
    info_str += f'{"python":<{semi_width - 20}}{trader_info["python"]}\n'
    info_str += f'{"qteasy":<{semi_width - 20}}{trader_info["qteasy"]}\n'
    info_str += f'{"tushare":<{semi_width - 20}}{trader_info["tushare"]}\n'
    info_str += f'{"ta-lib":<{semi_width - 20}}{trader_info["ta-lib"]}\n'
    info_str += f'{"Local DataSource":<{semi_width - 20}}{trader_info["Local DataSource"]}\n'
    info_str += f'{"System log file path":<{semi_width - 20}}{trader_info["System log file path"]}\n'
    info_str += f'{"Trade log file path":<{semi_width - 20}}{trader_info["Trade log file path"]}\n'

    return info_str


def pack_account_info(trader_info, width=80):
    """ 打包账户信息字符串，用于在shell中格式化显示trader_info中的账户信息

    Parameters
    ----------
    trader_info: dict
        包含账户信息的字典
    width: int
        字符串的宽度

    Returns
    -------
    str
        包含账户信息的字符串
    """

    semi_width = int(width * 0.75)

    info_str = ''

    # Account information
    info_str += f'{" Account Overview ":=^{width}}\n'
    info_str += f'{"Account ID":<{semi_width - 20}}{trader_info["Account ID"]}\n'
    info_str += f'{"User Name":<{semi_width - 20}}{trader_info["User Name"]}\n'
    info_str += f'{"Created on":<{semi_width - 20}}{trader_info["Created on"]}\n'
    info_str += f'{"Started on":<{semi_width - 20}}{trader_info["Started on"]}\n'
    info_str += f'{"Time zone":<{semi_width - 20}}{trader_info["Time zone"]}\n'

    return info_str


def pack_status_info(trader_info, width=80):
    """ 打包账户状态信息字符串， 用于在Shell中格式化显示trader的状态信息

    Parameters
    ----------
    trader_info: dict
        包含账户信息的字典
    width: int
        字符串的宽度

    Returns
    -------
    str
        包含账户信息的字符串
    """
    semi_width = int(width * 0.75)

    info_str = ''

    # Status and Settings
    info_str += f'{" Status and Settings ":=^{width}}\n'
    info_str += f'{"Trader Stats":<{semi_width - 20}}{trader_info["Trader Stats"]}\n'
    info_str += f'{"Broker Status":<{semi_width - 20}}{trader_info["Broker Name"]} / {trader_info["Broker Status"]}\n'
    info_str += f'{"Live price update freq":<{semi_width - 20}}' \
                   f'{trader_info["Live price update freq"]}\n'
    info_str += f'{"Strategy":<{semi_width - 20}}{trader_info["Strategy"]}\n'
    info_str += f'{"Strategy run frequency":<{semi_width - 20}}{trader_info["Strategy run frequency"]}\n'
    info_str += f'{"Trade batch size(buy/sell)":<{semi_width - 20}}' \
                   f'{trader_info["trade batch size"]} ' \
                   f'/ {trader_info["sell_batch_size"]}\n'
    info_str += f'{"Delivery Rule (cash/asset)":<{semi_width - 20}}' \
                   f'{trader_info["trade delivery period"]} day / ' \
                   f'{trader_info["stock delivery period"]} day\n'

    buy_fix = trader_info["buy_fix"]
    sell_fix = trader_info["sell_fix"]
    buy_rate = trader_info["buy_rate"]
    sell_rate = trader_info["sell_rate"]

    if (buy_fix > 0) or (sell_fix > 0):
        trader_info += f'{"Trade cost - fixed (B/S)":<{semi_width - 20}}' \
                       f'¥ {buy_fix:.3f} / ¥ {sell_fix:.3f}\n'
    if (buy_rate > 0) or (sell_rate > 0):
        trader_info += f'{"Trade cost - rate (B/S)":<{semi_width - 20}}{buy_rate:.3%} / {sell_rate:.3%}\n'
    info_str += f'{"Market time (open/close)":<{semi_width - 20}}' \
                   f'{trader_info["market_open_am"]} / ' \
                   f'{trader_info["market_close_pm"]}\n'

    return info_str


def pack_investment_info(trader_info, width=80):
    """ 打包账户投资信息字符串, 用于在shell中格式化显示trader_info中的投资信息

    Parameters
    ----------
    trader_info: dict
        包含账户信息的字典
    width: int
        字符串的宽度

    Returns
    -------
    str
        包含账户信息的字符串
    """
    semi_width = int(width * 0.75)

    total_investment = trader_info['Total Investment']
    total_value = trader_info['Total Value']
    total_return_of_investment = trader_info['Total ROI']
    total_roi_rate = trader_info['Total ROI Rate']
    own_cash = trader_info['Total Cash']
    available_cash = trader_info['Available Cash']
    total_market_value = trader_info['Total Stock Value']
    position_level = trader_info['Stock Percent']
    total_profit = trader_info['Total Stock Profit']
    total_profit_ratio = trader_info['Stock Profit Ratio']

    info_str = ''

    # Investment Return
    info_str += f'{" Returns ":=^{semi_width}}\n'
    info_str += f'{"Benchmark":<{semi_width - 20}}¥ ' \
                   f'{trader_info["Benchmark"]}\n'
    info_str += f'{"Total Investment":<{semi_width - 20}}¥ {total_investment:,.2f}\n'
    if total_value >= total_investment:
        info_str += f'{"Total Value":<{semi_width - 20}}¥[bold red] {total_value:,.2f}[/bold red]\n'
        info_str += f'{"Total Return of Investment":<{semi_width - 20}}' \
                       f'¥[bold red] {total_return_of_investment:,.2f}[/bold red]\n' \
                       f'{"Total ROI Rate":<{semi_width - 20}}  [bold red]{total_roi_rate:.2%}[/bold red]\n'
    else:
        info_str += f'{"Total Value":<{semi_width - 20}}¥[bold green] {total_value:,.2f}[/bold green]\n'
        info_str += f'{"Total Return of Investment":<{semi_width - 20}}' \
                       f'¥[bold green] {total_return_of_investment:,.2f}[/bold green]\n' \
                       f'{"Total ROI Rate":<{semi_width - 20}}  [bold green]{total_roi_rate:.2%}[/bold green]\n'
    info_str += f'{" Cash ":=^{semi_width}}\n'
    info_str += f'{"Cash Percent":<{semi_width - 20}}  {own_cash / total_value:.2%} \n'
    info_str += f'{"Total Cash":<{semi_width - 20}}¥ {own_cash:,.2f} \n'
    info_str += f'{"Available Cash":<{semi_width - 20}}¥ {available_cash:,.2f}\n'
    info_str += f'{" Stock Value ":=^{semi_width}}\n'
    info_str += f'{"Stock Percent":<{semi_width - 20}}  {position_level:.2%}\n'
    if total_profit >= 0:
        info_str += f'{"Total Stock Value":<{semi_width - 20}}¥[bold red] {total_market_value:,.2f}[/bold red]\n'
        info_str += f'{"Total Stock Profit":<{semi_width - 20}}¥[bold red] {total_profit:,.2f}[/bold red]\n'
        info_str += f'{"Stock Profit Ratio":<{semi_width - 20}}  [bold red]{total_profit_ratio:.2%}[/bold red]\n'
    else:
        info_str += f'{"Total Stock Value":<{semi_width - 20}}¥[bold green] {total_market_value:,.2f}[/bold ' \
                       f'green]\n'
        info_str += f'{"Total Stock Profit":<{semi_width - 20}}¥[bold green] {total_profit:,.2f}[/bold green]\n'
        info_str += f'{"Total Profit Ratio":<{semi_width - 20}}  [bold green]{total_profit_ratio:.2%}[/bold ' \
                       f'green]\n'

    return info_str


def pack_pool_info(trader_info, width=80):
    """ 打包资产池信息字符串, 用于在shell中格式化显示trader_info中的投资信息

    Parameters
    ----------
    trader_info: dict
        包含账户信息的字典
    width: int
        字符串的宽度

    Returns
    -------
    str
        包含账户信息的字符串
    """

    asset_pool = trader_info['Asset Pool']
    asset_in_pool = trader_info['Asset in Pool']

    info_str = ''

    asset_pool_string = adjust_string_length(s=' '.join(asset_pool), n=width - 2)

    info_str += f'{" Investment ":=^{width}}\n'
    info_str += f'Current Investment Type:        {trader_info["Asset Type"]}\n'
    info_str += f'Current Investment Pool:        {asset_in_pool} stocks, ' \
                   f'Use "pool" command to view details.\n=={asset_pool_string}\n'

    return info_str


class TraderShell(Cmd):
    """ 基于Cmd的交互式shell，用于实盘交易模式与用户交互

    提供了基本操作命令，包括：
    - status: 查看交易系统状态
    - pause: 暂停交易系统
    - resume: 恢复交易系统
    - bye: 停止交易系统并退出shell
    - exit: 停止交易系统并退出shell
    - stop: 停止交易系统并退出shell
    - info: 查看交易系统信息
    - watch: 添加或删除股票到监视列表
    - buy: 手动创建买入订单
    - sell: 手动创建卖出订单
    - change: 手动修改交易系统的资金和持仓
    - positions: 查看账户持仓
    - orders: 查看账户订单
    - history: 查看账户历史交易记录
    - overview: 查看账户概览
    - config: 查看或修改qt_config配置信息
    - dashboard: 退出shell，进入dashboard模式
    - strategies: 查看策略信息，或者修改策略参数
    - schedule: 查看交易日程
    - help: 查看帮助信息
    - run: 手动运行交易策略，此功能仅在debug模式下可用
    - artifacts: 列出实盘账户磁盘产物路径（别名 ls-artifacts）
    - liveconfig: 只读展示 LiveTradeConfig 摘要（别名 live-config）
    - tasks / task: 查看或取消 Trader 任务队列（非 broker 订单）
    - gate: 手动触发启动门禁（别名 startup-gate）
    - reconcile: 打印 Broker 对账快照 JSON（别名 snapshot-reconcile）
    - rotatelogs: 手动轮换 trade/risk 日志（别名 rotate-logs）
    - broker: Broker 会话子命令 status/connect/disconnect
    - sync: 远端状态同步预留（stub，别名 pull-state，S2.1-b）

    qteasy Shell的命令支持参数解析，用户可以通过命令行参数来调整命令的行为，要查看所有命令的帮助，
    可以使用命令 "help" 或者 "?"，要查看某个命令的帮助，可以使用命令 "help <command>" 或者
    命令的-h参数，如<command -h>。

    在 Shell 运行过程中按下 Ctrl+C 进入模式选单：选项 1 进入 command 模式，选项 2 进入
    dashboard 模式，选项 3 停止 trader 并退出 Shell；5 秒内无有效输入则自动恢复中断前的模式。
    在模式选单等待期间再次按下 Ctrl+C 将立即按与选项 3 相同的正常关停路径退出 Shell，
    不会重新进入选单或异常中断。

    """
    intro = 'Welcome to the trader shell interactive mode. Type help or ? to list commands.\n' \
            'Type "bye" to stop trader and exit shell.\n' \
            'Type "dashboard" to leave interactive mode and enter dashboard.\n' \
            'Type "help <command>" to get help for more commands.\n'
    prompt = '(QTEASY) '

    argparser_properties = {
        'status':     dict(prog='status', description='Show trader status',
                           usage='status [-h]', ),
        'pause':      dict(prog='pause', description='Pause trader',
                           usage='pause [-h]',
                           epilog='When trader is paused, strategies will not be executed, '
                                  'orders will not be submitted, submitted orders will be '
                                  'suspended until trader is resumed'),
        'resume':     dict(prog='resume', description='Resume trader',
                           usage='resume [-h]', ),
        'debug':      dict(prog='debug', description='toggle or set debug mode',
                           usage='debug [-h] [--set]'),
        'bye':        dict(prog='bye', description='Stop trader and exit shell',
                           usage='bye [-h]',
                           epilog='You can also exit shell using command "exit" or "stop"'),
        'exit':       dict(prog='exit', description='Stop trader and exit shell',
                           usage='exit [-h]',
                           epilog='You can also exit shell using command "bye" or "stop"'),
        'stop':       dict(prog='stop', description='Stop trader and exit shell',
                           usage='stop [-h]',
                           epilog='You can also exit shell using command "exit" or "bye"'),
        'summary':    dict(prog='summary', description='Show human readable operation summary',
                           usage='summary [TIME] [-h]',
                           epilog='Display the summary of operation histories in human-readable format.'),
        'info':       dict(prog='info', description='Get trader info, same as overview',
                           usage='info [-h] [--detail] [--system]',
                           epilog='Get trader info, including basic information of current '
                                  'account, and current cash and positions'),
        'pool':       dict(prog='pool', description='Show details of asset pool',
                           usage='pool [-h]'),
        'watch':      dict(prog='watch', description='Add or remove stock symbols to watch list',
                           usage='watch [SYMBOL [SYMBOL ...]] [-h] [--position] [--remove '
                                 '[REMOVE [REMOVE ...]]] [--clear]'),
        'buy':        dict(prog='buy', description='Manually create buy-in order',
                           usage='buy AMOUNT SYMBOL [-h] [--price PRICE] [--side {long,short}] '
                                 '[--force]',
                           epilog='the order will be submitted to broker and will be executed'
                                  ' according to broker rules, Currently only market price '
                                  'orders can be submitted, and the orders might not be executed '
                                  'immediately if market is not open'),
        'sell':       dict(prog='sell', description='Manually create sell-out order',
                           usage='sell AMOUNT SYMBOL [-h] [--price PRICE] [--side {long,short}] '
                                 '[--force]',
                           epilog='the order will be submitted to broker and will be executed'
                                  ' according to broker rules, Currently only market price '
                                  'orders can be submitted, and the orders might not be executed '
                                  'immediately if market is not open'),
        'positions':  dict(prog='positions', description='Get account positions',
                           usage='positions [-h]',
                           epilog='Print out holding quantities and available quantities '
                                  'of all positions'),
        'overview':   dict(prog='overview', description='Get trader overview, same as info',
                           usage='overview [-h] [--detail] [--system]',
                           epilog='Get trader info, including basic information of current '
                                  'account, and current cash and positions'),
        'config':     dict(prog='config', description='Show or change qteasy configurations',
                           usage='config [KEYS [KEYS ...]] [-h] [--level LEVEL] [--detail] [--set SET]'),
        'history':    dict(prog='history', description='List trade history of a stock',
                           usage='history [SYMBOL] [-h]',
                           epilog='List all trade history of one particular stock, displaying '
                                  'every buy-in and sell-out in a table format. '
                                  'symbol like 000651 is accepted.'),
        'orders':     dict(prog='orders', description='Get account orders',
                           usage='usage: orders [SYMBOL [SYMBOL ...]] [-h] '
                                 '[--status {submitted,s,filled,f,canceled,c,partial-filled,p,rejected,r}] [--active] '
                                 '[--time {today,t,yesterday,y,3day,3,week,w,month,m,all,a}] '
                                 '[--type {buy,sell,b,s,all,a}] '
                                 '[--side {long,short,l,s,all,a}]'),
        'cancel':     dict(prog='cancel', description='Cancel an active order',
                           usage='cancel ORDER_ID [-h]',
                           epilog='Cancel one submitted/partial-filled order by order id.'),
        'change':     dict(prog='change', description='Change account cash and positions',
                           usage='change [SYMBOL] [-h] [--amount AMOUNT] [--price PRICE] '
                                 '[--side {l,long,s,short}] [--cash CASH]',
                           epilog='Change cash or positions or both. nothing will be changed '
                                  'if amount or cash is not given, price is used to calculate '
                                  'new cost, if not given, current price will be used'),
        'dashboard':  dict(prog='', description='Exit shell and enter dashboard',
                           usage='dashboard [-h] [--rewind REWIND]',
                           epilog='Exit shell and enter dashboard mode, where trading logs '
                                  'are displayed in real time; provide an integer to rewind '
                                  'previous rows of logs, default 50 rows'),
        'strategies': dict(prog='', description='Show or change strategy parameters',
                           usage='strategies [STRATEGY [STRATEGY ...]] [-h] [--detail] '
                                 '[--set-par [SET_VAL [SET_VAL ...]]] [--blender BLENDER] '
                                 '[--group GROUP]'),
        'schedule':   dict(prog='', description='Show trade agenda',
                           usage='schedule [-h]'),
        'refill':     dict(prog='', description='Refill data to datasource',
                           usage='usage: refill TABLE [TABLE ...] [-h] '
                                 '[--coverage -c COVERAGE] [--channel -ch CHANNEL]'),
        'run':        dict(prog='', description='Run strategies manually',
                           usage='run [STRATEGY [STRATEGY ...]] [-h] '
                                 f'[--task {{{",".join(DEBUG_RUN_TASK_CHOICES)}}}] '
                                 '[--args [ARGS [ARGS ...]]]'),
        'artifacts':  dict(prog='artifacts', description='List live-trade artifact paths (implemented)',
                           usage='artifacts [-h]'),
        'liveconfig': dict(prog='liveconfig', description='Show LiveTradeConfig summary (implemented)',
                           usage='liveconfig [-h] [--detail]'),
        'tasks':      dict(prog='tasks', description='List Trader task queue entries (implemented)',
                           usage='tasks [-h] [--status STATUS] [--name NAME]'),
        'task':       dict(prog='task', description='Show or cancel a Trader queue task (implemented)',
                           usage='task [TASK_ID] [-h] [--list] [--status STATUS] [--cancel]'),
        'gate':       dict(prog='gate', description='Run startup gate manually for smoke/debug (implemented)',
                           usage='gate [-h]'),
        'reconcile':  dict(prog='reconcile',
                           description='Print broker reconcile snapshot JSON (implemented)',
                           usage='reconcile [-h]'),
        'rotatelogs': dict(prog='rotatelogs',
                           description='Rotate trade/risk logs under QT_TRADE_LOG_PATH (implemented)',
                           usage='rotatelogs [-h] [--days DAYS] [--yes]'),
        'broker':     dict(prog='broker',
                           description='Run broker session subcommands (implemented)',
                           usage=f'broker {{{",".join(BROKER_SUBCOMMANDS)}}} [-h]'),
        'sync':       dict(prog='sync',
                           description='Pull broker remote state (stub, reserved for QMT S2.1-b)',
                           usage='sync [-h]'),
    }

    command_arguments = {
        'status':     [],
        'pause':      [],
        'resume':     [],
        'debug':      [('--set', '-s')],
        'bye':        [],
        'exit':       [],
        'stop':       [],
        'summary':    [('time',)],
        'info':       [('--detail', '-d'),
                       ('--system', '-s')],
        'pool':       [],
        'watch':      [('symbols',),
                       ('--position', '--positions', '-pos', '-p'),
                       ('--remove', '-r'),
                       ('--clear', '-c')],
        'buy':        [('amount',),
                       ('symbol',),
                       ('--price', '-p'),
                       ('--side', '-s'),
                       ('--force', '-f')],
        'sell':       [('amount',),
                       ('symbol',),
                       ('--price', '-p'),
                       ('--side', '-s'),
                       ('--force', '-f')],
        'positions':  [],
        'overview':   [('--detail', '-d'),
                       ('--system', '-s')],
        'config':     [('keys',),
                       ('--level', '-l'),
                       ('--detail', '-d'),
                       ('--set', '-s')],
        'history':    [('symbol',)],
        'orders':     [('symbols',),
                       ('--status', '-s'),
                       ('--active', '-a'),
                       ('--time', '-t'),
                       ('--type', '-y'),
                       ('--side', '-d')],
        'cancel':     [('order_id',)],
        'change':     [('symbol',),
                       ('--amount', '-a'),
                       ('--price', '-p'),
                       ('--side', '-s'),
                       ('--cash', '-c')],
        'dashboard':  [('--rewind', '-r'),
                       ],
        'strategies': [('strategy',),
                       ('--detail', '-d'),
                       ('--set-par', '--set', '-s'),
                       ('--blender', '-b'),
                       ('--group', '-g')],
        'schedule':   [],
        'refill':     [('tables',),
                       ('--coverage', '-c'),
                       ('--channel', '-ch')],
        'run':        [('strategy',),
                       ('--task', '-t'),
                       ('--args', '-a')],
        'artifacts':  [],
        'liveconfig': [('--detail', '-d')],
        'tasks':      [('--status', '-s'),
                       ('--name', '-n')],
        'task':       [('task_id',),
                       ('--list', '-l'),
                       ('--status', '-s'),
                       ('--cancel', '-c')],
        'gate':       [],
        'reconcile':  [],
        'rotatelogs': [('--days', '-d'),
                       ('--yes', '-y')],
        'broker':     [('action',)],
        'sync':       [],
    }

    command_arg_properties = {
        'status':     [],
        'pause':      [],
        'resume':     [],
        'debug':      [{'action':  'store',
                        'default': '',
                        'choices': ['on', 'off'],
                        'help':    'turn on or off debug mode with on/off'}],
        'bye':        [],
        'exit':       [],
        'stop':       [],
        'summary':    [{'action': 'store',
                        'nargs':  '?',  # nargs='?' will require at most one argument
                        'default': 'today',
                        'choices': ['today', 't', 'yesterday', 'y', '3day', '3', 'week', 'w',
                                    'month', 'm', 'all', 'a'],
                        'help':   'time period to show summary for'}],
        'info':       [{'action': 'store_true',
                        'help':   'show detailed account info'},
                       {'action': 'store_true',
                        'help':   'show system info'}],
        'pool':       [],
        'watch':      [{'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',  # nargs='+' will require at least one argument
                        'help':   'stock symbols to add to watch list'},
                       {'action': 'store_true',
                        'dest':   'position',
                        'help':   'add 5 stocks from position list to watch list'},
                       {'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',  # nargs='+' will require at least one argument
                        'help':   'remove stock symbols from watch list'},
                       {'action': 'store_true',
                        'help':   'clear watch list'}],
        'buy':        [{'action': 'store',
                        'type':   float,
                        'help':   'amount of shares to buy'},
                       {'action': 'store',
                        'help':   'stock symbol to buy'},
                       {'action':  'store',
                        'type':    float,
                        'default': 0.0,  # default to market price
                        'help':    'limit price to buy at; use 0 (default) for market order'},
                       {'action':  'store',
                        'default': 'long',
                        'choices': ['long', 'short'],
                        'help':    'order position side, default long'},
                       {'action': 'store_true',
                        'help':   'force buy regardless of current prices (NOT IMPLEMENTED YET)'}],
        'sell':       [{'action': 'store',
                        'type':   float,
                        'help':   'amount of shares to sell'},
                       {'action': 'store',
                        'help':   'stock symbol to sell'},
                       {'action':  'store',
                        'type':    float,
                        'default': 0.0,  # default to market price
                        'help':    'limit price to sell at; use 0 (default) for market order'},
                       {'action':  'store',
                        'default': 'long',
                        'choices': ['long', 'short'],
                        'help':    'order position side, default long'},
                       {'action': 'store_true',
                        'help':   'force sell regardless of current prices'}],
        'positions':  [],
        'overview':   [{'action': 'store_true',
                        'help':   'show detailed account info'},
                       {'action': 'store_true',
                        'help':   'show system info'}],
        'config':     [{'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',
                        'help':   'config keys to show or change'},
                       {'action':  'count',
                        'default': 2,
                        'help':    'config level to show or change'},
                       {'action': 'store_true',
                        'help':   'show detailed config info'},
                       {'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',
                        'help':   'config values to set or change for keys'}],
        'history':    [{'action':  'store',
                        'nargs':   '?',  # nargs='?' will require at most one argument
                        'default': 'all',
                        'type':    str,
                        'help':    'stock symbol to show history for, if not given, show history for all'}],
        'orders':     [{'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',  # nargs='*' allows 0 or any positive number of arguments.
                        # nargs='+' will require at least one argument
                        'help':   'stock symbol to show orders for'},
                       {'action':  'store',
                        'default': 'all',
                        'choices': ['submitted', 's', 'filled', 'f', 'canceled', 'c', 'partial-filled', 'p',
                                    'rejected', 'r'],
                        'help':    'order status to show'},
                       {'action': 'store_true',
                        'help':   'show active orders only (submitted + partial-filled)'},
                       {'action':  'store',
                        'default': 'today',
                        'choices': ['today', 't', 'yesterday', 'y', '3day', '3', 'week', 'w',
                                    'month', 'm', 'all', 'a'],
                        'help':    'order time to show'},
                       {'action':  'store',
                        'default': 'all',
                        'choices': ['buy', 'sell', 'b', 's', 'all', 'a'],
                        'help':    'order type to show'},
                       {'action':  'store',
                        'default': 'all',
                        'choices': ['long', 'short', 'l', 's', 'all', 'a'],
                        'help':    'order side to show'}],
        'cancel':     [{'action': 'store',
                        'type':   int,
                        'help':   'order id to cancel'}],
        'change':     [{'action':  'store',
                        'nargs':   '?',  # one or zero (default value) argument is allowed
                        'default': '',
                        'help':    'symbol to change position for'},
                       {'action':  'store',
                        'default': 0,
                        'type':    float,
                        'help':    'amount of shares to change'},
                       {'action':  'store',
                        'default': 0.0,  # default to market price
                        'type':    float,
                        'help':    'price to change position at'},
                       {'action':  'store',
                        'default': 'long',
                        'choices': ['l', 'long', 's', 'short'],
                        'help':    'side of the position to change'},
                       {'action':  'store',
                        'default': 0.0,  # default not to change cash
                        'type':    float,
                        'help':    'amount of cash to change for current account'}],
        'dashboard':  [{'action':  'store',
                        'type':    int,
                        'default': 50,
                        'help':    'rewind previous log entries (logical records), default 50'}],
        'strategies': [{'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',  # nargs='+' will require at least one argument
                        'help':   'strategy to show or change parameters for'},
                       {'action': 'store_true',
                        'help':   'show detailed strategy info'},
                       {'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',
                        'dest':   'set_val',
                        'help':   'set parameters for strategy'},
                       {'action':  'store',
                        'default': '',
                        'type':    str,
                        'help':    'set blender for strategies'},
                       {'action':  'store',
                        'default': '',
                        'help':    'The strategy group whose blender is set'}],
        'schedule':   [],
        'refill':     [{'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '+',  # nargs='+' will require at least one argument
                        'help':   'table to refill data for'},
                       {'action':  'store',
                        'default': 1,
                        'type':    int,
                        'help':    'days of data to cover'},
                       {'action':  'store',
                        'default': 'eastmoney',
                        'choices': SUPPORTED_DATA_CHANNELS,
                        'help':    'channel to fetch data from'}],
        'run':        [{'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',
                        'help':   'strategies to run'},
                       {'action':  'store',
                        'default': '',
                        'choices': list(DEBUG_RUN_TASK_CHOICES),
                        'help':    'task to run (DEBUG mode only)'},
                       {'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',
                        'help':   'arguments for the task to run'}],
        'artifacts':  [],
        'liveconfig': [{'action': 'store_true',
                        'help':   'include extended live-trade fields beyond summary dict'}],
        'tasks':      [{'action':  'store',
                        'default': '',
                        'help':    'filter by task status (e.g. queued, running, done)'},
                       {'action':  'store',
                        'default': '',
                        'help':    'filter by task name (e.g. refill, run_strategy)'}],
        'task':       [{'action':  'store',
                        'nargs':   '?',
                        'default': None,
                        'help':    'task id to show or cancel'},
                       {'action': 'store_true',
                        'help':   'list trader tasks (default status: queued)'},
                       {'action':  'store',
                        'default': 'queued',
                        'help':    'filter by task status when listing (e.g. queued, all, running)'},
                       {'action': 'store_true',
                        'help':   'cancel Trader queue task (not broker order; use cancel ORDER_ID for orders)'}],
        'gate':       [],
        'reconcile':  [],
        'rotatelogs': [{'action':  'store',
                        'type':    int,
                        'default': None,
                        'help':    'keep days override; default from trade_log_keep_days'},
                       {'action': 'store_true',
                        'help':   'confirm rotation without interactive prompt'}],
        'broker':     [{'action':  'store',
                        'choices': list(BROKER_SUBCOMMANDS),
                        'help':    'broker subcommand (Simulator connect is session flag only)'}],
        'sync':       [],
    }

    def __init__(self, trader):
        super().__init__(completekey='tab')
        self._trader = trader
        self._timezone = trader.time_zone
        self._status = None
        self._shutdown_requested = False
        self._watch_list = self.trader.watch_list  # set default watch list
        self._watched_price_string = ' == Realtime prices can be displayed here. ' \
                               'Use "watch" command to add stocks to watch list. =='  # watched prices string

        # dashboard 模式下上一行是否为 ``\\r`` 状态行（打印普通日志前需清除以免残留）
        self._dashboard_on_status_line: bool = False
        self._last_status_plain: Optional[str] = None
        self._watch_price_worker: Optional[Thread] = None

        self.argparsers = {}

        self.init_arg_parsers()

    def _print_log_line(self, text: str) -> None:
        """在 dashboard 中打印一行日志文本；若当前仍为状态行则先清除该行。

        Parameters
        ----------
        text : str
            已格式化的一行内容（不含末尾换行亦可）。

        Returns
        -------
        None
        """
        if self._dashboard_on_status_line:
            _clear_current_line()
        rich.print(text)
        self._dashboard_on_status_line = False
        self._last_status_plain = None

    def _print_status_line(self, text: Text) -> None:
        """在终端当前行输出状态 ``Text``，用空格填充至终端宽度并以 ``\\r`` 结尾。

        Parameters
        ----------
        text : rich.text.Text
            状态行内容（可含样式）。

        Returns
        -------
        None
        """
        status_plain = text.plain
        if status_plain == self._last_status_plain:
            return
        self._last_status_plain = status_plain

        width = _terminal_width()
        line = _truncate_text_to_cell_width(text, width)
        pad_len = max(0, width - line.cell_len)
        padded = line + (' ' * pad_len) if pad_len else line
        console = Console(file=sys.stdout, width=width, soft_wrap=False, force_terminal=True)
        console.print(padded, end='\r', highlight=False)
        self._dashboard_on_status_line = True

    def _replay_dashboard_logs(self, rewind: int) -> None:
        """排空消息队列并按当前 ``debug`` 设置回放系统日志尾部若干条逻辑记录。

        ``send_message`` 会先写入系统日志再放入队列；此处排空队列不做打印，
        仅回放日志尾部，避免与 ``read_sys_log`` 同一内容重复输出。

        Parameters
        ----------
        rewind : int
            逻辑日志条数上限，与 ``dashboard -r`` 一致（非文件物理行数）。

        Returns
        -------
        None
        """
        _drain_message_queue(self.trader)
        lines = self.trader.read_sys_log(row_count=rewind, include_debug=self.debug)
        for raw in lines:
            self._print_log_line(raw.rstrip('\n'))

    @property
    def trader(self):
        return self._trader

    @property
    def status(self):
        return self._status

    @property
    def watch_list(self):
        return self._watch_list

    @property
    def debug(self):
        return self.trader.debug

    def toggle_debug(self):
        """ toggle debug value"""
        self.trader.debug = not self.trader.debug

    def _maybe_refresh_watched_prices(self) -> None:
        """在 dashboard 模式下异步刷新监视价格，避免重叠 worker 线程。"""
        if not self.trader.is_market_open:
            self.format_watched_prices()
            return
        worker = self._watch_price_worker
        if worker is not None and worker.is_alive():
            return
        self._watch_price_worker = Thread(target=self.trader.update_watched_prices, daemon=True)
        self._watch_price_worker.start()
        self.format_watched_prices()

    def format_watched_prices(self):
        """ 根据watch list返回清单中股票的信息：代码、名称、当前价格、涨跌幅
        """
        watched_prices = self.trader.watched_prices
        symbols = self._watch_list
        watched_price_string = Text()

        if watched_prices is None:
            self._watched_price_string = ' == Live prices not available at the moment. =='
            return

        if watched_prices.empty:
            self._watched_price_string = ' == Live prices not available yet. =='
            return
        # remove duplicated symbols in watched_prices and symbols
        watched_prices = watched_prices[~watched_prices.index.duplicated(keep='first')]
        symbols = list(set(symbols))

        # start to build watched price strings
        for symbol in symbols:
            if symbol in watched_prices.index:
                change = watched_prices.loc[symbol, 'change']
                watched_prices_seg = f' ={symbol[:-3]}{watched_prices.loc[symbol, "name"]}/' \
                                     f'{watched_prices.loc[symbol, "close"]:.2f}/' \
                                     f'{watched_prices.loc[symbol, "change"]:+.2%}'
                if change > 0:
                    watched_price_string.append(watched_prices_seg, style='bold red')
                elif change < 0:
                    watched_price_string.append(watched_prices_seg, style='bold green')
                else:
                    watched_price_string.append(watched_prices_seg)

            else:
                watched_price_string += f' ={symbol[:-3]}/--/---'
        self._watched_price_string = watched_price_string

    def filter_order_details(self,
                             order_details: pd.DataFrame,
                             *,
                             symbols: list[str] = None,
                             status: str = None,
                             active_only: bool = False,
                             order_time: str = None,
                             order_type: str = None,
                             side: str = None,
                             ):
        """ Filter order details by arguments and return the filtered records

        Parameters:
        -----------
        order_details: pd.DataFrame
            订单详情数据框
        symbols: list of str
            股票代码列表
        status: str
            订单状态
        order_time: str
            订单时间
        order_type: str
            订单类型
        side: str
            订单方向

        Returns:
        --------
        order_details: pd.DataFrame
            筛选过后的订单详情
        """

        # select orders by time range arguments like 'last_hour', 'today', '3day', 'week', 'month'
        end = self.trader.get_current_tz_datetime()  # 产生本地时区时间
        if order_time in['all', 'a']:
            start = pd.to_datetime('1970-01-01 00:00:00')
        elif order_time in ['last_hour', 'l']:
            start = pd.to_datetime(end) - pd.Timedelta(hours=1)
        elif order_time in ['today', 't']:
            start = pd.to_datetime(end) - pd.Timedelta(days=1)
            start = start.strftime("%Y-%m-%d 23:59:59")
        elif order_time in ['yesterday', 'y']:
            yesterday = pd.to_datetime(end) - pd.Timedelta(days=1)
            start = yesterday.strftime("%Y-%m-%d 00:00:00")
            end = yesterday.strftime("%Y-%m-%d 23:59:59")
        elif order_time in ['3day', '3']:
            start = pd.to_datetime(end) - pd.Timedelta(days=3)
            start = start.strftime("%Y-%m-%d 23:59:59")
        elif order_time in ['week', 'w']:
            start = pd.to_datetime(end) - pd.Timedelta(days=7)
            start = start.strftime("%Y-%m-%d 23:59:59")
        elif order_time in ['month', 'm']:
            start = pd.to_datetime(end) - pd.Timedelta(days=30)
            start = start.strftime("%Y-%m-%d 23:59:59")
        else:
            start = pd.to_datetime(end) - pd.Timedelta(days=1)
            start = start.strftime("%Y-%m-%d 23:59:59")

        # select orders by time range
        order_details = order_details[(order_details['submitted_time'] >= start) &
                                      (order_details['submitted_time'] <= end)]

        # select orders by status arguments like 'submitted', 'filled', 'canceled', 'partial-filled'
        if active_only:
            order_details = order_details[order_details['status'].isin(['submitted', 'partial-filled'])]
        elif status in ['submitted', 's']:
            order_details = order_details[order_details['status'] == 'submitted']
        elif status in ['filled', 'f']:
            order_details = order_details[order_details['status'] == 'filled']
        elif status in ['canceled', 'c']:
            order_details = order_details[order_details['status'] == 'canceled']
        elif status in ['partial-filled', 'p']:
            order_details = order_details[order_details['status'] == 'partial-filled']
        elif status in ['rejected', 'r']:
            order_details = order_details[order_details['status'] == 'rejected']
        else:  # default to show all statuses
            pass

        # select orders by order side arguments like 'long', 'short'
        if side in ['long', 'l']:
            order_details = order_details[order_details['position'] == 'long']
        elif side in ['short', 's']:
            order_details = order_details[order_details['position'] == 'short']
        else:  # default to show all sides
            pass

        # select orders by order side arguments like 'buy', 'sell'
        if order_type in ['buy', 'b']:
            order_details = order_details[order_details['direction'] == 'buy']
        elif order_type in ['sell', 's']:
            order_details = order_details[order_details['direction'] == 'sell']
        else:  # default to show all directions
            pass

        # select orders by order symbol arguments like '000001.SZ'

        # normalize symbols to upper case and with suffix codes when symbols are given
        if symbols:
            symbols = [symbol.upper() for symbol in symbols]

            possible_symbols = []
            for symbol in symbols:
                from qteasy.utilfuncs import is_complete_cn_stock_symbol_like, is_cn_stock_symbol_like
                if is_complete_cn_stock_symbol_like(symbol):
                    possible_symbols.append(symbol)
                # select orders by order symbol arguments like '000001'
                elif is_cn_stock_symbol_like(symbol):
                    possible_symbols.extend([symbol + '.SH', symbol + '.SZ', symbol + '.BJ'])
                else:
                    continue

            order_details = order_details[order_details['symbol'].isin(possible_symbols)]

        return order_details

    # ----- command arg parsers -----
    def init_arg_parsers(self):
        """ 初始化命令参数解析器
        """
        if self.argparsers:
            return

        # create instances of argparsers for each command
        for command in self.argparser_properties:
            self.argparsers[command] = argparse.ArgumentParser(
                    **self.argparser_properties[command],
            )

        # add arguments to each argparser
        for command in self.argparsers:
            args = self.command_arguments[command]
            arg_properties = self.command_arg_properties[command]
            if not args:
                continue
            for arg, arg_property in zip(args, arg_properties):
                try:
                    self.argparsers[command].add_argument(*arg, **arg_property)
                except:
                    raise RuntimeError(f'Error: failed to add argument {arg} to parser for command {command}\n'
                                       f'pars: {arg_property}')

    def parse_args(self, command, args=None) -> Optional[argparse.Namespace]:
        """ 解析命令行参数

        Parameters
        ----------
        command: str
            需要解析参数的命令
        args: str
            需要被解析的参数

        Returns
        -------
        args: Namespace
            解析后的参数，一个Namespace对象
        """
        if command not in self.argparsers:
            raise ValueError(f'Command {command} not found in argparsers')
        arg_parser = self.argparsers[command]
        try:
            args = arg_parser.parse_args(shlex.split(args))
        except argparse.ArgumentError as e:  # wrong argument, this should work for python >= 3.11
            print(f'{e}')
            return None
        except SystemExit:  # wrong argument, this should work for python < 3.10
            return None

        return args

    def _print_json(self, payload: dict, *, indent: int = 2) -> None:
        """将字典以 JSON 格式打印到 stdout（用户可见英文键值）。"""
        import json
        print(json.dumps(payload, indent=indent, ensure_ascii=False, default=str))

    def _print_trader_tasks_list(self,
                                 *,
                                 status: Optional[str] = None,
                                 name: Optional[str] = None) -> None:
        """打印 Trader 任务列表表格（与 schedule 风格一致）。"""
        normalized_status = _normalize_task_status_filter(status)
        tasks = self.trader.list_tasks(status=normalized_status, name=name or None)
        print('Trader Tasks:')
        print(format_trader_tasks_table(tasks))

    def check_buy_sell_args(self, args, type) -> bool:
        """ 检查买卖参数是否合法

        Parameters
        ----------
        args: Namespace
            命令行参数对象
        type: str
            买卖类型，'buy' 或 'sell'

        Returns
        -------
        bool
            参数是否合法
        """

        import rich
        import math

        qty = args.amount
        symbol = args.symbol.upper()
        price = args.price

        # check if qty and price are legal
        if qty <= 0:
            rich.print("[bold red]Qty can not be less or equal to 0[/bold red]")
            return False
        if price < 0:
            rich.print("[bold red]Price can not be less than 0[/bold red]")
            return False

        # check if qty meets the moq
        if type == 'buy':
            moq = self.trader.get_config('trade_batch_size')['trade_batch_size']
        else:
            moq = self.trader.get_config('sell_batch_size')['sell_batch_size']

        if moq != 0:
            quotient = qty / moq
            if not np.isclose(quotient, round(quotient), atol=1e-9):
                rich.print(f'[bold red]Trade qty({qty}) should be a multiple of the minimum order quantity ({moq})[/bold red]')
                return False

        # check if symbol is legal
        from qteasy.utilfuncs import is_complete_cn_stock_symbol_like
        if not is_complete_cn_stock_symbol_like(symbol):
            print(f'Wrong symbol is given: {symbol}, please input full symbol code like "000651.SZ"')
            return False

        # if price == 0, use live price
        if price == 0:
            if self.trader.live_price is None:
                rich.print(f'[bold red]No live price data available, price should be given![/bold red')
                return False
            try:
                args.price = self.trader.live_price[symbol]
            except KeyError:
                rich.print(f'[bold red]No live price data for {symbol} available, price should be given![/bold red')
                return False

        # the symbol must be in the pool
        if symbol not in self.trader.asset_pool:
            rich.print(f'[bold red]{symbol} is not in the asset pool, can not be bought![/bold red')
            return False

        return True

    # ----- basic commands -----
    def do_status(self, arg):
        """usage: status [-h]

        Show trader status

        optional arguments:
          -h, --help  show this help message and exit

        Examples:
        ---------
        to show trader status:
        (QTEASY) status
        """

        import rich
        args = self.parse_args('status', arg)
        if not args:
            return False

        rich.print(f'current trader status: {self.trader.status} \n'
                   f'current broker name: {self.trader.broker.broker_name} \n'
                   f'current broker status: {self.trader.broker.status} \n'
                   f'current day is trade day: {self.trader.is_trade_day} \n')

    def do_pause(self, arg):
        """usage: pause [-h]

        Pause trader

        optional arguments:
          -h, --help  show this help message and exit

        When trader is paused, strategies will not be executed, orders will not be
        submitted, submitted orders will be suspended until trader is resumed

        Examples:
        ---------
        to pause trader:
        (QTEASY) pause
        """
        args = self.parse_args('pause', arg)
        if not args:
            return False
        self.trader.add_task('pause')
        sys.stdout.write(f'Pausing trader... use command status to check current status\n')

    def do_resume(self, arg):
        """usage: resume [-h]

        Resume trader

        optional arguments:
          -h, --help  show this help message and exit

        Examples:
        ---------
        to resume trader:
        (QTEASY) resume
        """
        args = self.parse_args('resume', arg)
        if not args:
            return False
        self.trader.add_task('resume')
        sys.stdout.write(f'Resuming trader...\n')

    def do_debug(self, arg):
        """usage: debug [-h] [--set]

        Toggle or set trader debug status

        optional arguments:
          --set, -s   set debug mode on or off with on/off
          -h, --help  show this help message and exit

        Examples:
        ---------
        to toggle debug:
        (QTEASY) debug
        to set debug status:
        (QTEASY) debug -s on
        """
        args = self.parse_args('debug', arg)
        if not args:
            return False

        if args.set == '':
            # Nothing is input, toggle debug
            self.toggle_debug()
        elif args.set == 'on':
            self.trader.debug = True
        elif args.set == 'off':
            self.trader.debug = False
        else:
            print('Wrong argument, use "on" or "off" to set debug mode')
            return False

        if self.debug:
            print('Debug mode is on')
        else:
            print('Debug mode is off')

    def do_bye(self, arg):
        """usage: bye [-h]

        Stop trader and exit shell

        optional arguments:
          -h, --help  show this help message and exit

        You can also exit shell using command "exit" or "stop"

        Examples:
        ---------
        to stop trader and exit shell:
        (QTEASY) bye
        """
        args = self.parse_args('bye', arg)
        if not args:
            return False
        self._request_shutdown()
        return True

    def _request_shutdown(self) -> None:
        """请求停止 Trader/Broker（幂等），供 CLI 退出路径复用。"""
        if not self._shutdown_requested:
            print('requesting trader runtime shutdown...')
            self.trader.stop(wait=False, include_post_close=True)
            self._shutdown_requested = True
        self._status = 'stopped'

    def _wait_for_shutdown(self, timeout: float = 60.0) -> None:
        """等待 Trader 停机并收敛 Broker 在途订单线程。"""
        self.trader.join(timeout=timeout)
        if self.trader.is_alive():
            print('Warning: trader runtime stop timeout reached, continuing shutdown.')

    def do_exit(self, arg):
        """usage: exit [-h]

        Stop trader and exit shell

        optional arguments:
          -h, --help  show this help message and exit

        You can also exit shell using command "bye" or "stop"

        Examples:
        ---------
        to stop trader and exit shell:
        (QTEASY) exit
        """
        return self.do_bye(arg)

    def do_stop(self, arg):
        """usage: stop [-h]

        Stop trader and exit shell

        optional arguments:
          -h, --help  show this help message and exit

        You can also exit shell using command "exit" or "bye"

        Examples:
        ---------
        to stop trader and exit shell:
        (QTEASY) stop
        """
        return self.do_bye(arg)

    def do_summary(self, arg):
        """ usage: summary [TIME] [-h]

        Display the summary of operation histories in human-readable format.

        positional arguments:
          TIME                  {today,t,yesterday,y,3day,3,week,w,month,m,all,a}, default today
                                time range to show summary

        optional arguments:
          -h, --help            show this help message and

        Examples:
        ---------
        to show summary of today's operation:
        (QTEASY) summary today
        to show summary of yesterday's operation:
        (QTEASY) summary yesterday
        """
        args = self.parse_args('summary', arg)
        if not args:
            return False

        time_period = args.time
        order_details = self._trader.history_orders()
        order_details = self.filter_order_details(
                order_details,
                symbols=None,
                order_time=time_period,
        )

        if order_details.empty:
            print(f'No order history found with given time period "{time_period}", please expand the time range')
            return

        # get the names of all symbols
        symbols = order_details['symbol'].tolist()
        names = get_symbol_names(datasource=self.trader.datasource, symbols=symbols)
        order_details['name'] = names

        # calculate total number of orders executed in the period and total transaction cost
        symbols = list(set(symbols))
        rich.print(f'({len(symbols)}) share(s) are operated in time period "{time_period}": \n{symbols}')

        # human-readable format of each order of each symbol:
        for symbol in symbols:
            order_detail_for_symbol = order_details[order_details['symbol'] == symbol]
            rich.print(f'\nFor symbol {symbol} {order_detail_for_symbol["name"].iloc[0]}:')
            rich.print('====================')
            net_qty = 0
            total_cost = 0
            for row, order in order_detail_for_symbol.iterrows():
                # messages like "On 2021-01-01 12:00:00, bought 1000 shares @ 10.00,"
                #               "800 shares filled at 2021-01-01 12:00:01 @ 10.01 with transaction cost 10.01"
                message = f'- {order["submitted_time"].strftime("%Y%m%d %H:%M")}, {order["direction"]} {order["qty"]} ' \
                          f'share(s) @ {order["price_quoted"]}, -- '
                if order["filled_qty"] > 0:
                    message += f'{order["filled_qty"]} share(s) filled at {order["execution_time"].strftime("%H:%M")}' \
                               f' @ {order["price_filled"]} with cost {order["transaction_fee"]}'
                elif order["canceled_qty"] > 0:
                    message += f'{order["canceled_qty"]} share(s) got canceled at ' \
                               f'{order["execution_time"].strftime("%H:%M")}'
                else:
                    message += f', order is still pending'
                net_qty += order["filled_qty"] if order["direction"] == 'buy' else -order["filled_qty"]
                total_cost += order["transaction_fee"]

                rich.print(message)

            rich.print(f'\nNet bought quantity for {symbol} is {net_qty}, total transaction cost is {total_cost:.2f}')

    def do_info(self, arg):
        """usage: info [-h] [--detail] [--system]

        Get trader info, same as overview

        optional arguments:
          -h, --help    show this help message and exit
          --detail, -d  show detailed account info
          --system, -s  show system info

        Get trader info, including basic information of current account, and
        current cash and positions.

        Examples:
        ---------
        to get trader info:
        (QTEASY) info
        to get detailed trader info:
        (QTEASY) info --detail
        """
        return self.do_overview(arg)

    def do_pool(self, arg):
        """print information of the asset pool

        Print detailed information of all stocks in the asset pool, including
        stock symbol, name, company name, industry, listed date, etc.

        """

        args = self.parse_args('pool', arg)
        if not args:
            return False

        pools = self.trader.asset_pool_detail()
        rich.print(pools)

        return

    def do_watch(self, arguments):
        """usage: watch [SYMBOL [SYMBOL ...]] [-h] [--position] [--remove [REMOVE [REMOVE ...]]] [--clear]

        Add or remove stock symbols to watch list

        positional arguments:
          symbols               stock symbols to add to watch list

        optional arguments:
          -h, --help            show this help message and exit
          --position, --positions, -pos, -p
                                add 5 stocks from position list to watch list
          --remove [REMOVE [REMOVE ...]], -r [REMOVE [REMOVE ...]]
                                remove stock symbols from watch list
          --clear, -c           clear watch list

        Examples:
        ---------
        to view current watch list
        (QTEASY) watch
        to add stock symbols to watch list:
        (QTEASY) watch 000651.SZ 600036.SH 000550.SZ
        to add 5 stocks from position list to watch list:
        (QTEASY) watch --position
        to remove stock symbols from watch list:
        (QTEASY) watch -r 000651.SZ 600036.SH
        to clear watch list:
        (QTEASY) watch -c
        """

        import rich
        args = self.parse_args('watch', arguments)
        if not args:
            return False

        # TODO: for python version >= 3.8, list args are extended then flatten nested list is not needed
        if args.symbols is None:
            args.symbols = []
        else:
            args.symbols = [symbol.upper() for symbol_list in args.symbols for symbol in symbol_list]

        if args.remove is None:
            args.remove = []
        else:
            args.remove = [symbol.upper() for symbol_list in args.remove for symbol in symbol_list]

        from .utilfuncs import is_complete_cn_stock_symbol_like

        illegal_symbols = []
        for symbol in args.symbols:
            if not is_complete_cn_stock_symbol_like(symbol):
                illegal_symbols.append(symbol)
                continue

            # 添加symbols到watch list，除非该代码已在watch list中
            if symbol not in self._watch_list:
                self._watch_list.append(symbol)
            # 检查watch_list中代码个数是否超过5个，如果超过，删除最早添加的代码
            if len(self._watch_list) > 5:
                self._watch_list.pop(0)

        # 如果arg.position == True，则将当前持仓量最大的股票代码添加到watch list
        if args.position:
            pos = self._trader.account_position_info
            if pos.empty:
                print('No holding position at the moment.')
            top_5_pos = pos.sort_values(by='market_value', ascending=False).head(5)
            top_5_pos = top_5_pos.index.tolist()
            self._watch_list = top_5_pos

        # 如果arg.remove不为空，则将remove中的股票代码从watch list中删除
        symbols_not_found = []
        if args.remove:
            for symbol in args.remove:
                print(f'is removing symbol {symbol} from watch list {self._watch_list}')
                if symbol in self._watch_list:
                    self._watch_list.remove(symbol)
                else:
                    symbols_not_found.append(symbol)

        # 如果arg.clear == True，则清空watch list
        if args.clear:
            self._watch_list = []

        rich.print(f'current watch list: {self._watch_list}')
        if illegal_symbols:
            rich.print(f'Illegal symbols in arguments: {illegal_symbols}, input symbols in the form like "000651.SZ"')
        if symbols_not_found:
            rich.print(f'Symbols can not be removed from watch list because they are not there: {symbols_not_found}')

    def do_buy(self, arg):
        """usage: buy AMOUNT SYMBOL [-h] [--price PRICE] [--side {long,short}] [--force]

        Manually create buy-in order

        positional arguments:
          amount                amount of shares to buy
          symbol                stock symbol to buy

        optional arguments:
          -h, --help            show this help message and exit
          --price PRICE, -p PRICE
                                price to buy at
          --side {long,short}, -s {long,short}
                                order position side, default long
          --force, -f           force buy regardless of current prices (NOT IMPLEMENTED YET)

        the order will be submitted to broker and will be executed according to broker
        rules. If --price/-p is provided with a positive value, a limit order is submitted.
        If --price is omitted or set to 0, a market order is submitted using latest price.

        Examples:
        ---------
        to buy 100 shares of 000651.SH at price 32.5
        (QTEASY) buy 100 000651.Sh -p 32.5
        to buy short 100 shares of 000651 at price 30.0
        (QTEASY) buy 100 000651.SH -p 30.0 -s short
        """

        args = self.parse_args('buy', arg)
        if not args:
            return False

        user_set_limit_price = args.price != 0.0
        if not self.check_buy_sell_args(args, 'buy'):
            return False

        qty = args.amount
        symbol = args.symbol.upper()
        price = args.price
        position = args.side

        trade_order = self.trader.submit_trade_order(
                symbol=symbol,
                qty=qty,
                price=price,
                position=position,
                direction='buy',
                order_type='limit' if user_set_limit_price else 'market',
        )
        if trade_order:
            order_id = trade_order['order_id']
            print(f'Order <{order_id}> has been submitted to broker: '
                  f'{trade_order["direction"]} {trade_order["qty"]:.1f} of {symbol} '
                  f'at price {trade_order["price"]:.2f}')
        else:
            decision = self.trader.last_risk_decision
            if decision is not None and not decision.allowed:
                print(
                        f'Order submission rejected by risk manager: '
                        f'rule_id={decision.rule_id!r}, reason={decision.reason!r}'
                )
            else:
                reason = self.trader.last_submit_reject_reason
                if reason:
                    print(f'Order submission failed: {reason}')
                else:
                    print('Order submission failed.')

        if not self.trader.is_market_open:
            print(f'Market is not open, order might not be executed immediately')

    def do_sell(self, arg):
        """usage: sell AMOUNT SYMBOL [-h] [--price PRICE] [--side {long,short}] [--force]

        Manually submit buy-in order

        positional arguments:
          amount                amount of shares to sell
          symbol                stock symbol to sell

        optional arguments:
          -h, --help            show this help message and exit
          --price PRICE, -p PRICE
                                price to sell at
          --side {long,short}, -s {long,short}
                                order position side, default long
          --force, -f           force sell regardless of current prices (NOT IMPLEMENTED YET)

        the order will be submitted to broker and will be executed according to broker
        rules. If --price/-p is provided with a positive value, a limit order is submitted.
        If --price is omitted or set to 0, a market order is submitted using latest price.

        Examples:
        ---------
        to sell 100 shares of 000651.SH at price 32.5
        (QTEASY) sell 100 000651.Sh -p 32.5
        to sell short 100 shares of 000651 at price 30.0
        (QTEASY) sell 100 000651.SH -p 30.0 -s short
        """

        args = self.parse_args('sell', arg)
        if not args:
            return False

        user_set_limit_price = args.price != 0.0
        if not self.check_buy_sell_args(args, 'sell'):
            return False

        qty = args.amount
        symbol = args.symbol.upper()
        price = args.price
        position = args.side

        trade_order = self.trader.submit_trade_order(
                symbol=symbol,
                qty=qty,
                price=price,
                position=position,
                direction='sell',
                order_type='limit' if user_set_limit_price else 'market',
        )

        if trade_order:
            order_id = trade_order['order_id']
            print(f'Order <{order_id}> has been submitted to broker: '
                  f'{trade_order["direction"]} {trade_order["qty"]:.1f} of {symbol} '
                  f'at price {trade_order["price"]:.2f}')

            if not self.trader.is_market_open:
                print(f'Market is not open, order might not be executed immediately')
        else:
            decision = self.trader.last_risk_decision
            if decision is not None and not decision.allowed:
                print(
                        f'Order submission rejected by risk manager: '
                        f'rule_id={decision.rule_id!r}, reason={decision.reason!r}'
                )
            else:
                reason = self.trader.last_submit_reject_reason
                if reason:
                    print(f'Order submission failed: {reason}')
                else:
                    print('Order submission failed.')

    def do_positions(self, arg):
        """usage: positions [-h]

        Get account positions

        optional arguments:
          -h, --help  show this help message and exit

        Print out holding quantities and available quantities of all positions

        Examples:
        ---------
        to get account positions:
        (QTEASY) positions
        """

        args = self.parse_args('positions', arg)
        if not args:
            return False

        print(f'current positions: \n')
        pos = self._trader.account_position_info
        if pos.empty:
            print('No holding position at the moment.')
        pos_string = pos.to_string(
                columns=['qty', 'available_qty', 'cost', 'current_price',
                         'market_value', 'profit', 'profit_ratio', 'name'],
                header=['qty', 'available', 'cost', 'price', 'market_value', 'profit', 'profit_ratio', 'name'],
                col_space={
                    'name':          8,
                    'qty':           10,
                    'available_qty': 10,
                    'cost':          12,
                    'current_price': 10,
                    'market_value':  14,
                    'profit':        14,
                    'profit_ratio':  14,
                },
                justify='right',
        )
        pos_header_string = pos_string.split('\n')[0]
        earning_pos = pos[pos['profit'] >= 0].sort_values(by='profit', ascending=False)
        losing_pos = pos[pos['profit'] < 0].sort_values(by='profit', ascending=False)
        nan_profit_pos = pos[pos['profit'].isna()]
        if not earning_pos.empty:
            earning_pos_string = earning_pos.to_string(
                    columns=['qty', 'available_qty', 'cost', 'current_price',
                             'market_value', 'profit', 'profit_ratio', 'name'],
                    header=None,
                    index_names=False,
                    formatters={'name':          '{:8s}'.format,
                                'qty':           '{:,.2f}'.format,
                                'available_qty': '{:,.2f}'.format,
                                'cost':          '¥{:,.2f}'.format,
                                'current_price': '[bold red]¥{:,.2f}'.format,
                                'market_value':  '¥{:,.2f}'.format,
                                'profit':        '¥{:,.2f}'.format,
                                'profit_ratio':  '{:.2%}[/bold red]'.format},
                    col_space={
                        'name':          8,
                        'qty':           10,
                        'available_qty': 10,
                        'cost':          12,
                        'current_price': 20,
                        'market_value':  14,
                        'profit':        14,
                        'profit_ratio':  14,
                    },
                    justify='right',
            )
        else:
            earning_pos_string = ''
        if not losing_pos.empty:
            losing_pos_string = losing_pos.to_string(
                    columns=['qty', 'available_qty', 'cost', 'current_price',
                             'market_value', 'profit', 'profit_ratio', 'name'],
                    header=None,
                    index_names=False,
                    formatters={'name':          '{:8s}'.format,
                                'qty':           '{:,.2f}'.format,
                                'available_qty': '{:,.2f}'.format,
                                'cost':          '¥{:,.2f}'.format,
                                'current_price': '[bold green]¥{:,.2f}'.format,
                                'market_value':  '¥{:,.2f}'.format,
                                'profit':        '¥{:,.2f}'.format,
                                'profit_ratio':  '{:.2%}[/bold green]'.format},
                    col_space={
                        'name':          8,
                        'qty':           10,
                        'available_qty': 10,
                        'cost':          12,
                        'current_price': 22,
                        'market_value':  14,
                        'profit':        14,
                        'profit_ratio':  12,
                    },
                    justify='right',
            )
        else:
            losing_pos_string = ''
        if not nan_profit_pos.empty:
            nan_profit_pos_string = nan_profit_pos.to_string(
                    columns=['qty', 'available_qty', 'cost', 'current_price',
                             'market_value', 'profit', 'profit_ratio', 'name'],
                    header=None,
                    index_names=False,
                    formatters={'name':          '{:8s}'.format,
                                'qty':           '{:,.2f}'.format,
                                'available_qty': '{:,.2f}'.format,
                                'cost':          '¥{:,.2f}'.format,
                                'current_price': '¥{:,.2f}'.format,
                                'market_value':  '¥{:,.2f}'.format,
                                'profit':        '¥{:,.2f}'.format,
                                'profit_ratio':  '{:.2%}'.format},
                    col_space={
                        'name':          8,
                        'qty':           10,
                        'available_qty': 10,
                        'cost':          12,
                        'current_price': 22,
                        'market_value':  14,
                        'profit':        14,
                        'profit_ratio':  14,
                    },
                    justify='right',
            )
        else:
            nan_profit_pos_string = ''
        rich.print(f'{pos_header_string}\n{earning_pos_string}\n{losing_pos_string}\n{nan_profit_pos_string}')

    def do_overview(self, arg):
        """usage: overview [-h] [--detail] [--system]

        Get trader overview, same as info

        optional arguments:
          -h, --help    show this help message and exit
          --detail, -d  show detailed account info
          --system, -s  show system info Get trader overview, same as info

        Get trader overview, including basic information of current account, and
        current cash and positions.

        Examples:
        ---------
        to get trader overview:
        (QTEASY) overview
        to get detailed trader overview:
        (QTEASY) overview --detail
        """
        args = self.parse_args('overview', arg)
        if not args:
            return False

        trader_info = self.trader.info(detail=args.detail, system=args.system)
        if not trader_info:
            return False

        screen_width = shutil.get_terminal_size().columns

        if args.system:
            rich.print(pack_system_info(trader_info, width=screen_width))
        if args.detail:
            rich.print(pack_account_info(trader_info, width=screen_width))
            rich.print(pack_account_info(trader_info, width=screen_width))
        rich.print(pack_investment_info(trader_info, width=screen_width))
        if args.detail:
            rich.print(pack_pool_info(trader_info, width=screen_width))

        if args.detail:
            return self.do_positions(arg='')

    def do_config(self, arg):
        """usage: config [KEYS [kEYS ...]] [-h] [--level] [--detail] [--set [SET [SET ...]]]

        Show or change qteasy configurations

        positional arguments:
          keys                  config keys to show or change

        optional arguments:
          -h, --help            show this help message and exit
          --level, -l           config level to show or change, default to level 2
          --detail, -d          show detailed config info
          --set [SET [SET ...]], -s [SET [SET ...]]
                                config values to set or change for key, a key must be given to set value

        Display current qt configurations to designated level, if level is not given, display
        until level 2.
        if configure key is given and value is not given, display current value, default value
        and explanation of the configure key.
        if configure key and a value is given, change the configure key to the given value.

        Examples:
        ---------
        to show all configures:
        (QTEASY) config
        to show configures until level 3:
        (QTEASY) config -lll
        to show value of configure key "key1":
        (QTEASY) config key1
        to change value of configure key "key1" to "value1":
        (QTEASY) config key1 -s value1
        """

        args = self.parse_args('config', arg)
        if not args:
            return False

        from qteasy._arg_validators import _vkwargs_to_text
        import rich
        import shutil

        # get terminal width and set print width to 75% of terminal width
        column_width, _ = shutil.get_terminal_size()
        column_width = int(column_width * 0.75) if column_width > 120 else column_width

        keys = [str(key) for key_list in args.keys for key in key_list] if args.keys else []
        set_values = [str(value) for value_list in args.set for value in value_list] if args.set else []
        level = args.level
        verbose = args.detail

        get_config = self.trader.get_config
        if not keys:  # no keys given, show all configures
            configs = get_config()
            rich.print(_vkwargs_to_text(configs,
                                        level=level,
                                        info=True,
                                        verbose=verbose,
                                        width=column_width)
                       )
        # if keys are given and set_values are not given, show configure values
        elif keys and not set_values:
            configs = {key: get_config(key)[key] for key in keys}
            rich.print(_vkwargs_to_text(configs,
                                        level='all',
                                        info=True,
                                        verbose=verbose,
                                        width=column_width)
                       )
        # if keys are given and set_values are also given, set configure values
        elif keys and set_values:
            if len(keys) != len(set_values):
                rich.print(f'[bold red]Number of keys and values do not match: {len(keys)} keys and '
                           f'{len(set_values)} values[/bold red]')
                return False

            # update configure values one by one
            for key, value in zip(keys, set_values):
                try:
                    self.trader.update_config(key, value)
                    rich.print(f'[bold green]configure key "{key}" has been changed to "{value}".[bold green]')
                except Exception as e:
                    rich.print(f'{e}, [bold red]configure key "{key}" can not be changed to "{value}".[/bold red]')
                    continue
        return None

    def do_history(self, arg):
        """usage: history [SYMBOL] [-h]

        List trade history of a stock

        positional arguments:
          symbol      stock symbol to show history for, if not given, show history for all

        optional arguments:
          -h, --help  show this help message and exit

        List all trade history of one particular stock, displaying every buy-in and
        sell-out in a table format. symbol like 000651 is accepted.

        Examples:
        ---------
        to show trade history of stock 000001:
        (QTEASY) history 000001
        to show trade history of all stocks:
        (QTEASY) history
        """

        args = self.parse_args('history', arg)
        if not args:
            return False

        history = self._trader.history_orders()

        if history.empty:
            print('No trade history found.')
            return

        symbol = args.symbol.upper()

        if symbol != 'ALL':
            from qteasy.utilfuncs import is_complete_cn_stock_symbol_like, is_cn_stock_symbol_like
            if is_complete_cn_stock_symbol_like(symbol):
                history = history[history['symbol'] == symbol]
                # select orders by order symbol arguments like '000001'
            elif is_cn_stock_symbol_like(symbol):
                possible_complete_symbols = [symbol + '.SH', symbol + '.SZ', symbol + '.BJ']
                history = history[history['symbol'].isin(possible_complete_symbols)]
            else:
                # if argument is not a symbol, use the first available symbol in order details
                print(f'Wrong symbol is given: {symbol}, please input full symbol code like "000651" or "000651.SZ"')
                return False

        # remove rows without actual fills; NaN filled_qty must not pass through
        filled_qty = history['filled_qty'].fillna(0)
        history = history[(filled_qty > 0) & history['execution_time'].notna()]
        history.sort_values(by='execution_time', inplace=True)
        # change the quantity to negative if it is a sell-out
        history['filled_qty'] = np.where(history['direction'] == 'sell',
                                         -history['filled_qty'],
                                         history['filled_qty'])
        # calculate rows: cum_qty, trade_cost, cum_cost, value, share_cost, earnings, and earning rate
        history['cum_qty'] = history.groupby('symbol')['filled_qty'].cumsum()
        history['trade_cost'] = history['filled_qty'] * history['price_filled'] + history['transaction_fee']
        history['cum_cost'] = history.groupby('symbol')['trade_cost'].cumsum()
        history['value'] = history['cum_qty'] * history['price_filled']
        history['share_cost'] = history['cum_cost'] / history['cum_qty']
        history['earnings'] = history['value'] - history['cum_cost']
        history['earning_rate'] = history['earnings'] / history['cum_cost']
        # add row: name
        all_names = get_symbol_names(datasource=self.trader.datasource, symbols=history['symbol'].tolist())
        history['name'] = [adjust_string_length(name, 8, hans_aware=True, padding='left') for name in all_names]

        # display history with to_string method with 2 digits precision for all numbers and 3 digits percentage
        #  for earning rate
        #  Error will be raised if execution_time is NaT. will print out normal format in this case
        if np.any(pd.isna(history.execution_time)):
            history.execution_time = history.execution_time.fillna(pd.to_datetime('1970-01-01'))

        rich.print(
                history.to_string(
                        columns=['execution_time', 'symbol', 'direction', 'filled_qty', 'price_filled',
                                 'transaction_fee', 'cum_qty', 'value', 'share_cost', 'earnings', 'earning_rate',
                                 'name'],
                        header=['time', 'symbol', 'oper', 'qty', 'price',
                                'trade_fee', 'holdings', 'holding value', 'cost', 'earnings', 'earning_rate',
                                'name'],
                        formatters={
                            'execution_time':  lambda x: "{:%b%d %H:%M:%S}".format(pd.to_datetime(x)),
                            'name':            '{:8s}'.format,
                            'operation':       '{:s}'.format,
                            'filled_qty':      '{:,.2f}'.format,
                            'price_filled':    '¥{:,.2f}'.format,
                            'transaction_fee': '¥{:,.2f}'.format,
                            'cum_qty':         '{:,.2f}'.format,
                            'value':           '¥{:,.2f}'.format,
                            'share_cost':      '¥{:,.2f}'.format,
                            'earnings':        '¥{:,.2f}'.format,
                            'earning_rate':    '{:.3%}'.format,
                        },
                        col_space={
                            'name':         8,
                            'price_filled': 10,
                            'value':        12,
                            'share_cost':   10,
                            'earnings':     12,
                        },
                        justify='right',
                        index=False,
                )
        )

    def do_orders(self, arg):
        """ usage: orders [SYMBOL [SYMBOL ...]] [-h] [--status {filled,f,canceled,c,partial-filled,p}]
                [--time {today,t,yesterday,y,3day,3,week,w,month,m,all,a}]
                [--type {buy,sell,b,s,all,a}] [--side {long,short,l,s,all,a}]

        Get account orders

        positional arguments:
          symbol                stock symbol to show orders for

        optional arguments:
          -h, --help            show this help message and exit
          --status {filled,f,canceled,c,partial-filled,p}, -s {filled,f,canceled,c,partial-filled,p}
                                order status to show
          --time {today,t,yesterday,y,3day,3,week,w,month,m,all,a}, -t {today,t,yesterday,y,3day,3,week,w,month,m,all,a}
                                order time to show
          --type {buy,sell,b,s,all,a}, -y {buy,sell,b,s,all,a}
                                order type to show
          --side {long,short,l,s,all,a}, -d {long,short,l,s,all,a}
                                order side to show

        Examples:
        ---------
        to get today's orders:
        (QTEASY) orders
        to get yesterday's orders:
        (QTEASY) orders -t yesterday
        to get orders of stock 000001:
        (QTEASY) orders 000001
        to get filled orders of stock 000001:
        (QTEASY) orders 000001 -s filled
        to get filled buy orders of stock 000001:
        (QTEASY) orders 000001 -s filled -y buy
        """

        args = self.parse_args('orders', arg)
        if not args:
            return False

        symbols = [symbol for symbol_list in args.symbols for symbol in symbol_list] if args.symbols else []
        status = args.status
        active_only = args.active
        order_time = args.time
        order_type = args.type
        side = args.side

        order_details = self._trader.history_orders()

        # filter orders by arguments

        order_details = self.filter_order_details(
                order_details=order_details,
                symbols=symbols,
                status=status,
                active_only=active_only,
                order_time=order_time,
                order_type=order_type,
                side=side,
        )

        if order_details.empty:
            rich.print(f'No orders found with criteria ({args}). try other ways to filter orders.')
        else:
            symbols = order_details['symbol'].tolist()
            names = get_symbol_names(datasource=self.trader.datasource, symbols=symbols)
            order_details['name'] = names
            display_df = order_details.copy()
            for col in ['broker_order_id', 'price_filled', 'filled_qty', 'canceled_qty', 'delivery_status']:
                display_df[col] = display_df[col].apply(
                        lambda x: '--' if (pd.isna(x) or x == '' or x is None) else x
                )
            rich.print(display_df.to_string(
                    index=False,
                    columns=['order_id', 'broker_order_id', 'execution_time', 'symbol', 'position', 'direction',
                             'qty', 'price_quoted',
                             'submitted_time', 'status', 'price_filled', 'filled_qty', 'canceled_qty',
                             'delivery_status', 'name'],
                    header=['id', 'broker_id', 'time', 'symbol', 'pos', 'buy/sell', 'qty', 'price',
                            'submitted', 'status', 'fill_price', 'fill_qty', 'canceled',
                            'delivery', 'name'],
                    formatters={'name':           '{:s}'.format,
                                'order_id':       '{:d}'.format,
                                'broker_order_id': lambda x: x if x == '--' else f'{x}',
                                'qty':            '{:,.2f}'.format,
                                'price_quoted':   '¥{:,.2f}'.format,
                                'price_filled':   lambda x: x if x == '--' else f'¥{float(x):,.2f}',
                                'filled_qty':     lambda x: x if x == '--' else f'{float(x):,.2f}',
                                'canceled_qty':   lambda x: x if x == '--' else f'{float(x):,.2f}',
                                'execution_time': lambda x: '--' if pd.isna(x) else "{:%b%d %H:%M:%S}".format(
                                        pd.to_datetime(x)),
                                'submitted_time': lambda x: '--' if pd.isna(x) else "{:%b%d %H:%M:%S}".format(
                                        pd.to_datetime(x))
                                },
                    col_space={
                        'price_quoted': 10,
                        'price_filled': 10,
                        'filled_qty':   10,
                        'canceled_qty': 10,
                    },
                    justify='right',
            ))

    def do_cancel(self, arg):
        """usage: cancel ORDER_ID [-h]

        Cancel one active order by order id.
        """

        args = self.parse_args('cancel', arg)
        if not args:
            return False

        order_id = int(args.order_id)
        try:
            cancel_order(
                    order_id=order_id,
                    data_source=self.trader.datasource,
                    account_id=self.trader.account_id,
            )
            print(f'Order {order_id} has been canceled.')
        except Exception as e:
            print(f'Order cancellation failed: {e}')
            return False

    def do_change(self, arg):
        """usage: change [SYMBOL] [-h] [--amount AMOUNT] [--price PRICE] [--side {l,long,s,short}]
                [--cash CASH]

        Change account cash and positions

        positional arguments:
          symbol                symbol to change position for

        optional arguments:
          -h, --help            show this help message and exit
          --amount AMOUNT, -a AMOUNT
                                amount of shares to change
          --price PRICE, -p PRICE
                                price to change position at
          --side {l,long,s,short}, -s {l,long,s,short}
                                side of the position to change
          --cash CASH, -c CASH  amount of cash to change for current account

           Change trader cash and positions

        Change cash or positions or both. nothing will be changed if amount or cash is not given,
        price is used to calculate new cost, if not given, current price will be used

        Usage:
        ------
        change symbol [--amount | -a AMOUNT] [--price | -p PRICE] [--side | -s l LONG | s SHORT] [--cash | -c amount]

        Examples:
        ---------
        to change cash to increase 1000:
        (QTEASY) change --cash 1000
        to change cash to decrease 1000:
        (QTEASY) change --cash -1000
        to change position of 000651.SH to increase 100 shares:
        (QTEASY) change 000651.SH --amount 100
        to change position of 000651.SH to increase 100 shares at price 32.5:
        (QTEASY) change 000651.SH --amount 100 --price 32.5
        to change short side of position of 000651.SH to increase 100 shares at price 32.5:
        (QTEASY) change 000651.SH --amount 100 --price 32.5 --side short
        """

        args = self.parse_args('change', arg)
        if not args:
            return False

        from qteasy.utilfuncs import is_complete_cn_stock_symbol_like, is_cn_stock_symbol_like

        symbol = args.symbol.upper()
        qty = args.amount
        price = args.price
        side = args.side
        cash_amount = args.cash

        # either qty or cash amount should be given
        if qty == 0 and cash_amount == 0:
            print('Please input one of position amount or cash to change.')
            return False

        # check the format of symbol
        if is_cn_stock_symbol_like(symbol):
            # check if input matches one of symbols in trader asset pool
            asset_pool = self.trader.asset_pool
            asset_pool_striped = [symbol.split('.')[0] for symbol in asset_pool]
            if symbol not in asset_pool_striped:
                print(f'symbol {symbol} not in trader asset pool, please check your input.')
                return False
            symbol = asset_pool[asset_pool_striped.index(symbol)]

        if symbol != '' and not is_complete_cn_stock_symbol_like(symbol):
            print(f'"{symbol}" invalid: Please input a valid symbol to change position holdings.')
            return False

        # get current price if price is not given
        if price == 0 and symbol != '':
            try:
                freq = self.trader.operator.op_data_freq
                last_available_data = self.trader.datasource.get_history_data(
                        shares=[symbol],
                        htypes='close',
                        asset_type=self.trader.asset_type,
                        freq=freq,
                        row_count=10,
                )
                current_price = last_available_data['close'][symbol][-1]
            except Exception as e:
                print(f'Error: {e}, latest price not available at the moment. 10.00 will be used as current price.')
                import traceback
                traceback.print_exc()
                current_price = 10.00
            price = current_price

        if qty != 0 and symbol != '':
            if side in ['s', 'short']:
                side = 'short'
            if side in ['l', 'long']:
                side = 'long'
            self._trader.manual_change_position(
                    symbol=symbol,
                    quantity=qty,
                    price=price,
                    side=side,
            )

        if cash_amount != 0:
            # change cash
            self.trader.manual_change_cash(amount=cash_amount)

    def do_dashboard(self, arg):
        """usage: dashboard [-h] [--rewind REWIND]

        Exit shell and enter dashboard

        optional arguments:
          -h, --help    show this help message and exit
          --rewind REWIND, -r REWIND
                        number of logical log entries to rewind (default: 50)

        Examples:
        ---------
        to enter dashboard mode:
        (QTEASY) dashboard
        to enter dashboard mode and rewind 100 log entries:
        (QTEASY) dashboard -r 100
        """

        args = self.parse_args('dashboard', arg)
        if not args:
            return False
        if args.rewind < 0 or args.rewind > 999:
            print('can not rewind more than 999 log entries or less than 0. please check your input.')
            return False

        import os
        # check os type of current system, and then clear screen
        os.system('cls' if os.name == 'nt' else 'clear')

        self._status = 'dashboard'
        self._dashboard_on_status_line = False
        self._last_status_plain = None
        print('\nWelcome to TraderShell! currently in dashboard mode, live status will be displayed here.\n'
              'You can not input commands in this mode, if you want to enter interactive mode, please '
              'press "Ctrl+C" to exit dashboard mode and select from prompted options.\n'
              'While the mode menu is waiting, press Ctrl+C again to exit immediately with normal shutdown.\n')
        self._replay_dashboard_logs(args.rewind)
        return True

    def do_strategies(self, arg: str):
        """usage: strategies [STRATEGY [STRATEGY ...]] [-h] [--detail] [--set-par [SET_VAL [SET_VAL ...]]]
                [--blender BLENDER] [--timing TIMING]

        Show or change strategy parameters

        positional arguments:
          strategy              strategy to show or change parameters for

        optional arguments:
          -h, --help            show this help message and exit
          --detail, -d          show detailed strategy info
          --set-par [SET_PAR [SET_PAR ...]], --set [SET_PAR [SET_PAR ...]], -s [SET_PAR [SET_PAR ...]]
                                set parameters for strategy
          --blender BLENDER, -b BLENDER
                                set blender for strategies, not implemented yet
          --timing TIMING, -t TIMING
                                The strategy run timing of the strategies whose
                                blender is set, not implemented yet

        Examples:
        ---------
        to display strategies information:
        (QTEASY): strategies
        to display strategies information in detail:
        (QTEASY): strategies --detail
        to set parameters (1, 2, 3) for strategy "stg":
        (QTEASY): strategies stg --set-par 1 2 3
        to set parameters (1, 2, 3) and (4, 5) for strategies "stg1" and "stg2" respectively:
        (QTEASY): strategies stg1 stg2 -s 1 2 3 -s 4 5
        to set blender of strategies:
        (QTEASY): strategies --blender <blender> (not implemented yet)
        """

        args = self.parse_args('strategies', arg)
        if not args:
            return False

        strategies = [stg for stg_list in args.strategy for stg in stg_list] if args.strategy else []
        detail = args.detail
        set_val = [tuple(val_list) for val_list in args.set_val] if args.set_val else []
        group = args.group
        blender = args.blender

        if not strategies and not blender:
            # if strategies are not given then display information of operator
            self.trader.operator.info(verbose=detail)
            return

        elif strategies and not set_val:
            # if strategies are given without set values

            strategy_ids = self.trader.operator.strategy_ids
            # check if strategies are all valid strategy ids
            if any(stg not in strategy_ids for stg in strategies):
                wrong_stg = [stg not in strategy_ids for stg in strategies]
                print(f'Strategies ({wrong_stg}) are not valid strategy ids, please check your input!')
                return False
            # show strategy info one by one
            for stg in strategies:
                self.trader.operator[stg].info(verbose=detail)
            return

        elif strategies and set_val:
            # update parameter values of each strategy

            # count of strategies should match that of set_val
            if len(strategies) != len(set_val):
                print(f'Number of strategies({len(strategies)}) must match set_val({len(set_val)})')
                return False

            for stg, val in zip(strategies, set_val):
                try:
                    # correct par type before setting
                    op = self.trader.operator
                    val = tuple(int(v) for v in val)
                    op.set_parameter(stg_id=stg, par_values=val)
                    print(f'Parameter {val} has been set to strategy {stg}.')
                except Exception as e:
                    print(f'Can not set {val} to {stg}, Error: {e}')
                    if self.trader.debug:
                        import traceback
                        traceback.print_exc()
                    return False

        elif group and blender:
            try:
                self.trader.operator.set_blender(blender=blender, group_id=group)
                print(f'Blender {blender} has been set to run timing {group}')
            except Exception as e:
                print(f'Can not set {blender} to {group}, Error: {e}')
                if self.trader.debug:
                    import traceback
                    traceback.print_exc()
                return False

    def do_schedule(self, arg):
        """ usage: schedule [-h]

        Show trade agenda

        optional arguments:
          -h, --help  show this help message and exit

        Examples:
        ---------
        to display current strategy task schedule:
        (QTEASY): schedule
        """

        args = self.parse_args('schedule', arg)
        if not args:
            return False

        print(f'Execution Schedule:')
        schedule_string = self.trader.get_schedule_string()
        print(f'{schedule_string}')

    def do_refill(self, arg):
        """ usage: refill TABLE [TABLE ...] [-h]
                 [--coverage -c COVERAGE] [--channel -ch CHANNEL]

        Manual refill data tables in the datasource, multiple tables can be refilled at the same time.

        positional arguments:
          table                 tables to refill

        optional arguments:
            -h, --help            show this help message and exit
            --coverage COVERAGE, -c COVERAGE
                                    coverage of days to refill, default to 1
            --channel CHANNEL, -ch CHANNEL{eastmoney, tushare, akshare}
                                    data source to refill, default to eastmoney

        Examples:
        ---------
        to refill table "stock_basic":
        (QTEASY): refill stock_basic
        to refill tables "stock_daily" and "stock_hourly" covering 3 days:
        (QTEASY): refill stock_daily stock_hourly -c 3
        to refill table "stock_daily" using tushare:
        (QTEASY): refill stock_daily -ch tushare
        """

        args = self.parse_args('refill', arg)
        if not args:
            return False

        tables = [table for table_list in args.tables for table in table_list] if args.tables else []
        coverage = args.coverage
        channel = args.channel

        if not tables:
            print('Please input a valid table name to refill.')
            return False

        if coverage < 0:
            print('Coverage must be a positive integer, please check your input.')
            return False

        if channel not in ['eastmoney', 'tushare', 'akshare']:
            print(f'Invalid data source: {channel}, please input a valid data source.')
            return False

        # make tables back to comma-separated string
        tables = list_to_str_format(tables)
        self.trader._run_task('refill', tables, coverage, channel)
        return False

    def do_run(self, arg):
        f"""usage: run [STRATEGY [STRATEGY ...]] [-h]
                [--task {{{",".join(DEBUG_RUN_TASK_CHOICES)}}}]
                [--args [ARGS [ARGS ...]]]

        Run strategies or tasks manually (DEBUG mode only).
        If run refill task, only one table can be refilled at a time.

        positional arguments:
          strategy              strategies to run

        optional arguments:
          -h, --help            show this help message and exit
          --task {{{",".join(DEBUG_RUN_TASK_CHOICES)}}},
          -t {{{",".join(DEBUG_RUN_TASK_CHOICES)}}}
                                task to run
          --args [ARGS [ARGS ...]], -a [ARGS [ARGS ...]]
                                arguments for the task to run

        Examples:
        ---------
        to run strategy "stg1":
        (QTEASY): run stg1
        to run strategy "stg1" and "stg2":
        (QTEASY): run stg1 stg2
        to run task pre_open:
        (QTEASY): run --task pre_open
        to run refill with table argument:
        (QTEASY): run --task refill --args stock_daily

        """

        if not self.trader.debug:
            print('Running strategy manually is only available in DEBUG mode')
            return False

        args = self.parse_args('run', arg)
        if not args:
            return False

        strategies = [stg for stg_list in args.strategy for stg in stg_list] if args.strategy else []
        task = args.task
        task_args = [t_arg for arg_list in args.args for t_arg in arg_list] if args.args else []

        if not strategies and not task:
            print('Please input a valid strategy id or task name.')
            return False

        elif strategies:  # run strategies
            all_strategy_ids = self.trader.operator.strategy_ids
            if not all([strategy in all_strategy_ids for strategy in strategies]):
                invalid_stg = [stg for stg in strategies if stg not in all_strategy_ids]
                print(f'Invalid strategy id: {invalid_stg}, use "strategies" to view all valid strategy ids.')
                return False

            current_trader_status = self.trader.status
            current_broker_status = self.trader.broker.status

            self.trader.status = 'running'
            self.trader.broker.status = 'running'

            try:
                self.trader._run_task('run_strategy', *strategies, run_in_main_thread=True)
            except Exception as e:
                import traceback
                print(f'Error in running strategy: {e}')
                print(traceback.format_exc())
                return

            self.trader.status = current_trader_status
            self.trader.broker.status = current_broker_status
        else:  # run tasks
            if task not in DEBUG_RUN_TASK_CHOICES:
                print(f'Invalid task name: {task}, please input a valid task name.')
                return False
            try:
                task_args = tuple(task_args)
                self.trader._run_task(task, *task_args, run_in_main_thread=True)
            except Exception as e:
                import traceback
                print(f'Error in running task: {e}')
                print(traceback.format_exc())
                return False

    def do_artifacts(self, arg):
        """usage: artifacts [-h]

        List live-trade artifact paths for the current account (implemented).
        Alias: ls-artifacts

        optional arguments:
          -h, --help            show this help message and exit
        """

        args = self.parse_args('artifacts', arg)
        if not args:
            return False

        import qteasy as qt

        try:
            arts = qt.list_live_trade_artifacts(self.trader.account_id, self.trader.datasource)
        except KeyError as exc:
            print(f'Account not found: {exc}')
            return False

        for key in ('sys_log', 'trade_log', 'break_point', 'risk_log'):
            print(f'{key}: {arts[key]}')
        return None

    def do_liveconfig(self, arg):
        """usage: liveconfig [-h] [--detail]

        Show read-only LiveTradeConfig summary derived from current trader config (implemented).
        Alias: live-config

        optional arguments:
          -h, --help            show this help message and exit
          --detail, -d          include extended live-trade fields
        """

        args = self.parse_args('liveconfig', arg)
        if not args:
            return False

        from qteasy.live_config import build_live_trade_config

        cfg = build_live_trade_config(self.trader.get_config())
        summary = dict(cfg.to_summary_dict())
        broker_items = {
            'Broker Type': summary.pop('broker_type'),
            'Broker Params': summary.pop('live_trade_broker_params'),
        }
        market_items = {
            'Live Price Channel': summary.pop('live_price_channel'),
            'Live Price Freq': summary.pop('live_price_freq'),
            'Asset Type': summary.pop('asset_type'),
            'Time Zone': summary.pop('time_zone'),
            'UI Type': summary.pop('live_trade_ui_type'),
        }
        account_items = {
            'Account ID': summary.pop('live_trade_account_id'),
            'Asset Pool': summary.pop('asset_pool'),
            'Benchmark Asset': summary.pop('benchmark_asset'),
        }
        _print_key_value_section('Live Trade Config - Broker', broker_items)
        _print_key_value_section('Live Trade Config - Market', market_items)
        _print_key_value_section('Live Trade Config - Account', account_items)
        if args.detail:
            detail_items = {
                'Startup Gate Mode': cfg.live_trade_startup_gate_mode,
                'Split Strategy Prepare': cfg.live_trade_split_strategy_prepare,
                'Strategy Snapshot Max Age (s)': cfg.live_trade_strategy_snapshot_max_age_seconds,
                'Prepare Lead Seconds': cfg.live_trade_prepare_lead_seconds,
                'Data Refill Channel': cfg.live_trade_data_refill_channel,
                'Data Refill Batch Size': cfg.live_trade_data_refill_batch_size,
                'Data Refill Batch Interval': cfg.live_trade_data_refill_batch_interval,
            }
            _print_key_value_section('Live Trade Config - Extended', detail_items)
        return None

    def do_tasks(self, arg):
        """usage: tasks [-h] [--status STATUS] [--name NAME]

        List Trader task queue entries (implemented). Does not list broker orders.
        For dead-letter details see TRACE events.

        optional arguments:
          -h, --help            show this help message and exit
          --status, -s STATUS   filter by task status
          --name, -n NAME       filter by task name
        """

        args = self.parse_args('tasks', arg)
        if not args:
            return False

        status = args.status or None
        name = args.name or None
        self._print_trader_tasks_list(status=status, name=name)
        return None

    def do_task(self, arg):
        """usage: task [TASK_ID] [-h] [--list] [--status STATUS] [--cancel]

        Show, list, or cancel Trader queue tasks (implemented). Use cancel ORDER_ID for broker orders.

        positional arguments:
          task_id               task id to show or cancel

        optional arguments:
          -h, --help            show this help message and exit
          --list, -l            list trader tasks (default status filter: queued)
          --status, -s STATUS   filter by task status when listing (e.g. queued, all, running)
          --cancel, -c          cancel the queue task instead of showing details
        """

        args = self.parse_args('task', arg)
        if not args:
            return False

        if args.list and args.cancel:
            print('Cannot use --list and --cancel together.')
            return False

        if args.list:
            if args.task_id:
                print('Cannot combine --list with a task id; use "task TASK_ID" to show one task.')
                return False
            self._print_trader_tasks_list(status=args.status)
            return None

        task_id = args.task_id
        if not task_id:
            print('Please provide a task id, or use --list to show queued tasks.')
            return False

        if args.cancel:
            if self.trader.cancel_task(task_id):
                print(f'Canceled Trader queue task: {task_id}')
            else:
                print(f'Task not found: {task_id}')
            return None

        task_spec = self.trader.get_task(task_id)
        if task_spec is None:
            print(f'Task not found: {task_id}')
            return False

        self._print_json({
            'task_id': task_spec.task_id,
            'name': task_spec.name,
            'status': task_spec.status,
            'args': list(task_spec.args),
            'retry_count': task_spec.retry_count,
            'max_retries': task_spec.max_retries,
            'canceled': task_spec.canceled,
            'reentry_policy': task_spec.reentry_policy,
            'last_error': task_spec.last_error,
        })
        return None

    def do_gate(self, arg):
        """usage: gate [-h]

        Manually run startup gate and print whether trading-side tasks are allowed (implemented).
        Alias: startup-gate

        optional arguments:
          -h, --help            show this help message and exit
        """

        args = self.parse_args('gate', arg)
        if not args:
            return False

        import qteasy as qt

        allowed = self.trader.run_startup_gate()
        mode = str(qt.QT_CONFIG.get('live_trade_startup_gate_mode', 'off'))
        _print_key_value_section('Startup Gate', {
            'Mode': mode,
            'Allowed': allowed,
        })
        return None

    def do_reconcile(self, arg):
        """usage: reconcile [-h]

        Print broker reconcile snapshot as JSON (implemented).
        On Simulator, remote_* fields may be empty placeholders until QMT (S2.1) is connected.
        Alias: snapshot-reconcile

        optional arguments:
          -h, --help            show this help message and exit
        """

        args = self.parse_args('reconcile', arg)
        if not args:
            return False

        snapshot = self.trader.collect_broker_reconcile_snapshot()
        tolerance = snapshot.get('tolerance')
        cash_diff = snapshot.get('cash_diff')
        position_qty_diff = snapshot.get('position_qty_diff')
        failures = snapshot.get('failures') or []
        cash_diff_text = _format_scalar_for_display(cash_diff)
        if cash_diff is not None and tolerance is not None and abs(float(cash_diff)) > float(tolerance):
            cash_diff_text = f'[bold red]{cash_diff_text}[/bold red]'
        position_diff_text = _format_scalar_for_display(position_qty_diff)
        if position_qty_diff is not None and tolerance is not None and abs(float(position_qty_diff)) > float(tolerance):
            position_diff_text = f'[bold red]{position_diff_text}[/bold red]'
        _print_key_value_section('Broker Reconcile', {
            'Overall OK': snapshot.get('is_ok'),
            'Tolerance': tolerance,
            'Remote Cash': snapshot.get('remote_cash'),
            'Local Cash Total': snapshot.get('local_cash_total'),
            'Cash Diff': cash_diff_text,
            'Remote Position Qty Total': snapshot.get('remote_position_qty_total'),
            'Local Position Qty Total': snapshot.get('local_position_qty_total'),
            'Position Qty Diff': position_diff_text,
            'Remote Orders Count': snapshot.get('remote_orders_count'),
            'Remote Positions Count': snapshot.get('remote_positions_count'),
            'Primary History Table': snapshot.get('primary_history_table'),
            'Failures': ', '.join(failures) if failures else '(none)',
        })
        return None

    def do_rotatelogs(self, arg):
        """usage: rotatelogs [-h] [--days DAYS]

        Rotate trade/risk logs under current QT_TRADE_LOG_PATH (implemented).
        Alias: rotate-logs

        optional arguments:
          -h, --help            show this help message and exit
          --days, -d DAYS       keep-days override; default from trade_log_keep_days
        """

        args = self.parse_args('rotatelogs', arg)
        if not args:
            return False

        import qteasy as qt
        from datetime import datetime, timedelta

        if args.days is None:
            keep_days = qt.QT_CONFIG.get('trade_log_keep_days', 3)
        else:
            keep_days = args.days

        if keep_days is None or (isinstance(keep_days, int) and keep_days <= 0):
            print('Rotation skipped (keep_days disabled)')
            return None

        log_path = qt.QT_TRADE_LOG_PATH
        candidates = qt._collect_expired_trade_log_files(log_path, int(keep_days))
        cutoff = datetime.now() - timedelta(days=int(keep_days))
        print(f'Trade log rotation preview (keep_days={keep_days}, path={log_path})')
        print(f'Cutoff time: {cutoff:%Y-%m-%d %H:%M:%S}')
        if not candidates:
            print('No expired trade/risk log files to remove.')
            return None

        print(f'Will remove {len(candidates)} file(s):')
        preview_limit = 20
        for full_path, created_time in candidates[:preview_limit]:
            print(f'  {full_path}  (created {created_time:%Y-%m-%d %H:%M:%S})')
        if len(candidates) > preview_limit:
            print(f'  ... and {len(candidates) - preview_limit} more')

        confirmed = bool(args.yes)
        if not confirmed:
            if not _is_tty_stream(sys.stdin):
                print('Rotation aborted (non-interactive). Use --yes to confirm.')
                return None
            answer = input('Continue? [y/N]: ').strip().lower()
            confirmed = answer in ('y', 'yes')

        if not confirmed:
            print('Rotation canceled.')
            return None

        removed = qt._rotate_trade_logs(log_path, int(keep_days))
        print(f'Trade log rotation completed (removed={len(removed)}, keep_days={keep_days}, path={log_path})')
        return None

    def do_broker(self, arg):
        """usage: broker {status,connect,disconnect} [-h]

        Run broker session subcommands (implemented).
        On Simulator, connect/disconnect only toggles adapter session state.

        positional arguments:
          {status,connect,disconnect}
                                broker subcommand

        optional arguments:
          -h, --help            show this help message and exit
        """

        args = self.parse_args('broker', arg)
        if not args:
            return False

        if not args.action:
            print('Please provide a broker subcommand: status, connect, or disconnect.')
            return False

        broker = self.trader.broker
        action = args.action
        if action == 'status':
            _print_key_value_section('Broker Status', {
                'Broker Name': broker.broker_name,
                'Status': broker.status,
                'Connected': broker.is_connected,
                'Registered': broker.is_registered,
            })
        elif action == 'connect':
            broker.connect()
            print('Broker connected.')
        elif action == 'disconnect':
            broker.disconnect()
            print('Broker disconnected.')
        return None

    def do_sync(self, arg):
        """usage: sync [-h]

        Pull broker remote state into local ledger (stub, reserved for QMT S2.1-b).
        Alias: pull-state

        optional arguments:
          -h, --help            show this help message and exit
        """

        args = self.parse_args('sync', arg)
        if not args:
            return False

        print('[NOT_IMPLEMENTED] sync_from_broker is reserved for QMT broker integration (S2.1-b).')
        return False

    # ----- overridden methods -----
    def precmd(self, line: str) -> str:
        """ Make all commands case-insensitive,
            remove trailing spaces,
            remove commas between arguments,
            and remove redundant spaces between words
        """
        line = line.lower()
        line = line.strip()
        line = line.replace(',', ' ')
        line = ' '.join(line.split())
        parts = line.split(' ', 1)
        if parts and parts[0] in CLI_COMMAND_ALIASES:
            alias_cmd = CLI_COMMAND_ALIASES[parts[0]]
            line = alias_cmd + (' ' + parts[1] if len(parts) > 1 else '')
        return line

    def _handle_mode_interrupt(self) -> bool:
        """处理 Ctrl+C 模式选单；返回 ``False`` 时主循环应退出。

        Returns
        -------
        bool
            为 ``False`` 表示用户选择退出 Shell。
        """
        previous_mode = self._status
        if self._dashboard_on_status_line:
            _clear_current_line()
            self._dashboard_on_status_line = False
        try:
            choice = _read_line_with_timeout(_mode_menu_prompt(), MODE_MENU_TIMEOUT)
        except ModeMenuExitRequest:
            print('Interrupted again; shutting down trader...\n')
            return False
        except KeyboardInterrupt:
            print('Interrupted again; shutting down trader...\n')
            return False
        action = _parse_mode_menu_choice(choice)
        if action == 'resume':
            if choice is None:
                print('No input received; resuming previous mode.\n')
            else:
                print('Invalid choice; resuming previous mode.\n')
            self._status = previous_mode
        elif action == 'command':
            self._status = 'command'
        elif action == 'dashboard':
            self.do_dashboard('')
        elif action == 'exit':
            return False
        return True

    def _handle_runtime_error(self, exc: Exception) -> bool:
        """处理主循环未捕获异常；返回 ``False`` 时 Shell 应退出。

        Parameters
        ----------
        exc : Exception
            主循环中捕获的异常。

        Returns
        -------
        bool
            为 ``False`` 表示用户选择退出 Shell。
        """
        if self._dashboard_on_status_line:
            _clear_current_line()
            self._dashboard_on_status_line = False
        self._print_log_line(f'Unexpected Error: {exc}')
        if self.trader.debug:
            traceback.print_exc()
        try:
            choice = _read_line_with_timeout(_error_recovery_prompt(), ERROR_RECOVERY_TIMEOUT)
        except ModeMenuExitRequest:
            print('Interrupted again; shutting down trader...\n')
            return False
        except KeyboardInterrupt:
            print('Interrupted again; shutting down trader...\n')
            return False
        if _parse_error_recovery_choice(choice) == 'exit':
            return False
        print('Returning to dashboard mode.\n')
        self._status = 'dashboard'
        self._dashboard_on_status_line = False
        self._last_status_plain = None
        return True

    def run(self):
        self.do_dashboard('')
        self.trader.start()

        live_price_refresh_interval = 0.05
        live_price_refresh_timer = 0
        watched_price_refresh_interval = self.trader.get_config(
                'watched_price_refresh_interval')['watched_price_refresh_interval']
        while True:
            # enter shell loop
            try:
                if self.status == 'stopped':
                    # if trader is stopped, shell will exit
                    break
                if self.status == 'dashboard':
                    # check trader message queue and display messages
                    text_width = _terminal_width()
                    if not self._trader.message_queue.empty():
                        msg = coerce_trader_message(self._trader.message_queue.get())

                        # adjust message length to terminal width
                        message = self.trader.add_message_prefix(msg.text, msg.debug)
                        message = adjust_string_length(
                                message,
                                text_width - 2,
                                format_tags=True,
                                hans_aware=True,
                        )
                        self._print_log_line(message)
                    else:
                        # 如果没有消息，原位显示倒计时/实时价格
                        next_task = self.trader.next_task
                        count_down = self.trader.count_down_to_next_task
                        count_down_string = sec_to_duration(count_down, estimation=True)
                        message = self.trader.add_message_prefix('', debug=False)
                        # print(f'next task: {next_task}')
                        next_task_string = next_task[1] if next_task else 'None'
                        message += f'{next_task_string}'
                        message = Text(message)
                        if count_down > 60:
                            message.append(f' in {count_down_string}', style='bold green')
                        else:
                            message.append(f' in {count_down_string}', style='bold red')
                        message = message + ' ' + self._watched_price_string
                        self._print_status_line(message)

                    # check if live price refresh timer is up, if yes, refresh live prices
                    live_price_refresh_timer += live_price_refresh_interval
                    if live_price_refresh_timer > watched_price_refresh_interval:
                        self._maybe_refresh_watched_prices()
                        live_price_refresh_timer = 0
                elif self.status == 'command':
                    # get user command input and do commands
                    sys.stdout.write('will enter interactive mode.\n')
                    if not self.trader.debug:
                        import os
                        # check os type of current system, and then clear screen
                        os.system('cls' if os.name == 'nt' else 'clear')
                    # check if data source is connected here, if not, reconnect before entering interactive mode
                    self.cmdloop()
                else:
                    sys.stdout.write('status error, shell will exit, trader and broker will be shut down\n')
                    # self.do_bye('')
                    break
                time.sleep(live_price_refresh_interval)
            except KeyboardInterrupt:
                if not self._handle_mode_interrupt():
                    break
                continue
            except Exception as e:
                if not self._handle_runtime_error(e):
                    break
                continue

        sys.stdout.write('Thank you for using qteasy!\n')
        self._request_shutdown()
        self._wait_for_shutdown()

