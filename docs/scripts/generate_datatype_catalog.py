# coding=utf-8
# ======================================
# File:     generate_datatype_catalog.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-08-18
# Desc:
#   从 get_dtype_map() 按业务类别生成 docs 用内置 DataType 分册清单（提交进仓）。
#   用法：/opt/anaconda3/envs/py39/bin/python docs/scripts/generate_datatype_catalog.py
# ======================================
"""根据 get_dtype_map() 生成 references/datatypes/_generated 下的 Markdown 分册。

用户主分册按业务类别，不再按 acquisition_type。改动内置 DATA_TYPE_MAP
或准备发文档前，请在本机 py39 环境重跑本脚本并提交生成物。
Sphinx / Read the Docs 构建时不应依赖本脚本（生成物已入库）。
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

# 仓库根目录
REPO_ROOT = Path(__file__).resolve().parents[2]  # docs/scripts -> 仓库根
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = REPO_ROOT / 'docs' / 'source' / 'references' / 'datatypes' / '_generated'

# 用户主分册（顺序即目录顺序）。id 同时用作文件名 slug。
BUSINESS_GROUPS: List[Tuple[str, str]] = [
    ('quotes', '行情与复权'),
    ('valuation', '估值与财务'),
    ('macro', '宏观、利率与资金'),
    ('events', '交易行为与事件'),
    ('composition', '指数成分与权重'),
    ('static', '静态证券信息'),
]
BUSINESS_TITLES: Dict[str, str] = dict(BUSINESS_GROUPS)

# 行情 K 线 / 净值表（含复权 adjustment 行）
_KLINE_TABLES = frozenset({
    'stock_daily', 'stock_weekly', 'stock_monthly',
    'stock_1min', 'stock_5min', 'stock_15min', 'stock_30min', 'stock_hourly',
    'index_daily', 'index_weekly', 'index_monthly',
    'index_1min', 'index_5min', 'index_15min', 'index_30min', 'index_hourly',
    'fund_daily', 'fund_weekly', 'fund_monthly',
    'fund_1min', 'fund_5min', 'fund_15min', 'fund_30min', 'fund_hourly',
    'fund_nav',
    'future_daily', 'future_weekly', 'future_monthly',
    'future_1min', 'future_5min', 'future_15min', 'future_30min', 'future_hourly',
    'options_daily', 'options_1min', 'options_5min', 'options_15min',
    'options_30min', 'options_hourly',
    'global_index_daily', 'ths_index_daily', 'sw_index_daily', 'ci_index_daily',
})
# 个股资金流、涨跌停、龙虎榜等交易行为（非 event_* 的 direct 行）
_ACTIVITY_TABLES = frozenset({
    'money_flow',
    'hk_top10_stock',
    'hs_top10_stock',
    'top_list',
    'top_inst',
    'stock_holder_trade',
    'margin_detail',
    'block_trade',
    'stock_limit',
    'stock_suspend',
    'stock_names',
    'dividend',
    'forecast',
})
_CALENDAR_TABLES = frozenset({'trade_calendar'})
_CALENDAR_NAME_PREFIXES = ('trade_cal', 'is_trade_day', 'pre_trade_day')
_COMPOSITION_TABLES = frozenset({'index_weight'})


def _escape_cell(value: Any) -> str:
    """将单元格内容转成适合 Markdown 表格的单行文本。"""
    text = '' if value is None else str(value)
    text = text.replace('\n', ' ').replace('\r', ' ').replace('|', '\\|')
    return text.strip()


def _table_name_from_kwargs(kwargs: Any) -> str:
    """从 kwargs 提取 table_name（若存在）。"""
    if not isinstance(kwargs, Mapping):
        return ''
    table = kwargs.get('table_name', '')
    return '' if table is None else str(table)


def _is_calendar_reference(name: str, table_name: str) -> bool:
    """Reference 里的交易日历，归入交易行为而不是宏观。"""
    if table_name in _CALENDAR_TABLES:
        return True
    return any(str(name).startswith(prefix) for prefix in _CALENDAR_NAME_PREFIXES)


def classify_business_group(
        name: str,
        kind: str,
        acquisition_type: str,
        table_name: str,
) -> str:
    """按消费形状与表名把一条 DataType 分到用户业务分册。

    判定顺序：静态 → 成分 → 宏观/日历 Reference → 事件 → 行情与复权 → 交易行为表 → 估值与财务。
    acquisition_type 只作辅助，不是用户主分类。

    Parameters
    ----------
    name : str
        宽名。
    kind : str
        ``history`` / ``reference`` / ``static``。
    acquisition_type : str
        内部提取方式。
    table_name : str
        kwargs 中的表名，可能为空。

    Returns
    -------
    str
        分册 id，如 ``quotes``、``static``。
    """
    acq = str(acquisition_type or '')
    kind_s = str(kind or '')
    table = str(table_name or '')
    wide = str(name or '')

    if kind_s == 'static':
        return 'static'
    if acq == 'composition' or wide.startswith('wt_idx') or table in _COMPOSITION_TABLES:
        return 'composition'
    if kind_s == 'reference':
        if _is_calendar_reference(wide, table):
            return 'events'
        return 'macro'
    if acq.startswith('event') or acq == 'selected_events':
        return 'events'
    if acq == 'adjustment' or table in _KLINE_TABLES:
        return 'quotes'
    if table in _ACTIVITY_TABLES:
        return 'events'
    return 'valuation'


def generate() -> int:
    """生成业务分册与 catalog_index，返回内置类型总行数。"""
    from qteasy.datatypes import get_dtype_map

    dtype_map = get_dtype_map(include_user_defined=False)
    total = int(len(dtype_map))
    generated_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # 清理旧分册（含已废弃的 acquisition_type 文件名），避免残留
    for old in OUT_DIR.glob('*.md'):
        old.unlink()

    grouped: Dict[str, List[Tuple[str, str, str, str, str, str, str, str]]] = {
        group_id: [] for group_id, _ in BUSINESS_GROUPS
    }
    unknown: List[str] = []
    for (name, freq, asset_type), row in dtype_map.iterrows():
        acq = str(row.get('acquisition_type', 'unknown'))
        desc = row.get('description', '')
        table = _table_name_from_kwargs(row.get('kwargs'))
        kind = str(row.get('kind', ''))
        usable_in = row.get('usable_in', '')
        group_id = classify_business_group(
            name=str(name),
            kind=kind,
            acquisition_type=acq,
            table_name=table,
        )
        if group_id not in grouped:
            unknown.append(group_id)
            grouped.setdefault(group_id, [])
        grouped[group_id].append(
            (
                _escape_cell(name),
                _escape_cell(freq),
                _escape_cell(asset_type),
                _escape_cell(desc),
                _escape_cell(kind),
                _escape_cell(usable_in),
                _escape_cell(acq),
                _escape_cell(table),
            )
        )

    if unknown:
        raise RuntimeError(f'classifier returned unknown group id(s): {sorted(set(unknown))}')

    assigned = sum(len(rows) for rows in grouped.values())
    if assigned != total:
        raise RuntimeError(
            f'business group row count {assigned} != get_dtype_map() {total}'
        )

    index_rows: List[Tuple[str, str, int, str]] = []
    for group_id, title in BUSINESS_GROUPS:
        rows = grouped[group_id]
        rows.sort(key=lambda r: (r[0].lower(), r[1], r[2]))
        rel_name = f'{group_id}.md'
        path = OUT_DIR / rel_name

        lines: List[str] = [
            '<!-- AUTO-GENERATED: do not edit -->',
            f'<!-- generated_at: {generated_at} -->',
            f'<!-- business_group: {group_id} -->',
            f'<!-- row_count: {len(rows)} -->',
            '',
            f'# {title}',
            '',
            f'本分册由 `docs/scripts/generate_datatype_catalog.py` 从 '
            f'`qteasy.datatypes.get_dtype_map()` 按**业务类别**生成，共 **{len(rows)}** 条。',
            '',
            '请勿手改；更新内置类型后请重跑生成脚本。列含义与推荐读法见 '
            '[清单入口](../index.md)。`acquisition_type` / `table_name` 仅供对照 refill。',
            '',
            '| name | freq | asset_type | description | kind | usable_in | acquisition_type | table_name |',
            '| --- | --- | --- | --- | --- | --- | --- | --- |',
        ]
        for name, freq, asset_type, desc, kind, usable_in, acq, table in rows:
            lines.append(
                f'| {name} | {freq} | {asset_type} | {desc} | {kind} | {usable_in} | {acq} | {table} |'
            )
        lines.append('')
        path.write_text('\n'.join(lines), encoding='utf-8')
        index_rows.append((group_id, title, len(rows), rel_name))

    index_path = OUT_DIR / 'catalog_index.md'
    index_lines: List[str] = [
        '<!-- AUTO-GENERATED: do not edit -->',
        f'<!-- generated_at: {generated_at} -->',
        f'<!-- total_rows: {total} -->',
        '',
        '# 内置 DataType 分册索引',
        '',
        f'生成时间：{generated_at}；合计 **{total}** 条内置数据类型，按业务类别分册。',
        '',
        '| 业务类别 | 条数 | 分册 |',
        '| --- | ---: | --- |',
    ]
    for group_id, title, count, rel_name in index_rows:
        index_lines.append(f'| {title} | {count} | [{rel_name}]({rel_name}) |')
    index_lines.extend(
        [
            '',
            '概念与用法见 [DataType 概念章](../../../manage_data/02.%20datatypes.md)；'
            '清单入口见 [datatypes 索引](../index.md)。',
            '',
        ]
    )
    index_path.write_text('\n'.join(index_lines), encoding='utf-8')

    print(f'[generate_datatype_catalog] wrote {len(index_rows)} booklets + catalog_index')
    print(f'[generate_datatype_catalog] total rows: {total}')
    for group_id, title, count, _ in index_rows:
        print(f'[generate_datatype_catalog]   {group_id}: {count} ({title})')
    print(f'[generate_datatype_catalog] output: {OUT_DIR}')
    return total


def main() -> None:
    """命令行入口。"""
    generate()


if __name__ == '__main__':
    main()
