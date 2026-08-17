# coding=utf-8
# ======================================
# File:     generate_datatype_catalog.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-08-18
# Desc:
#   从 get_dtype_map() 生成 docs 用内置 DataType 分册清单（提交进仓）。
#   用法：/opt/anaconda3/envs/py39/bin/python docs/scripts/generate_datatype_catalog.py
# ======================================
"""根据 get_dtype_map() 生成 references/datatypes/_generated 下的 Markdown 分册。

改动内置 DATA_TYPE_MAP 或准备发文档前，请在本机 py39 环境重跑本脚本并提交生成物。
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

# acquisition_type 展示顺序（未列出的排在末尾按字母序）
ACQ_ORDER: List[str] = [
    'direct',
    'basics',
    'adjustment',
    'reference',
    'selection',
    'composition',
    'category',
    'event_signal',
    'event_status',
    'event_multi_stat',
    'selected_events',
]

ACQ_TITLES: Dict[str, str] = {
    'direct': '直读（direct）',
    'basics': '基本信息（basics）',
    'adjustment': '复权 / 修正（adjustment）',
    'reference': '引用型（reference）',
    'selection': '筛选型（selection）',
    'composition': '成份（composition）',
    'category': '分类（category）',
    'event_signal': '事件信号（event_signal）',
    'event_status': '事件状态（event_status）',
    'event_multi_stat': '多事件状态（event_multi_stat）',
    'selected_events': '选定事件（selected_events）',
}


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


def _safe_slug(acq: str) -> str:
    """将 acquisition_type 转为文件名安全 slug。"""
    return ''.join(ch if ch.isalnum() or ch in '-_' else '_' for ch in acq)


def _sort_acq_keys(keys: List[str]) -> List[str]:
    """按约定顺序排列 acquisition_type。"""
    rank = {name: i for i, name in enumerate(ACQ_ORDER)}

    def key_fn(name: str) -> Tuple[int, str]:
        return (rank.get(name, len(ACQ_ORDER)), name)

    return sorted(keys, key=key_fn)


def generate() -> int:
    """生成分册与 catalog_index，返回内置类型总行数。"""
    from qteasy.datatypes import get_dtype_map

    dtype_map = get_dtype_map(include_user_defined=False)
    total = int(len(dtype_map))
    generated_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # 清理旧分册，避免删类型后残留
    for old in OUT_DIR.glob('*.md'):
        old.unlink()

    grouped: Dict[str, List[Tuple[str, str, str, str, str]]] = {}
    for (name, freq, asset_type), row in dtype_map.iterrows():
        acq = str(row.get('acquisition_type', 'unknown'))
        desc = row.get('description', '')
        table = _table_name_from_kwargs(row.get('kwargs'))
        grouped.setdefault(acq, []).append(
            (
                _escape_cell(name),
                _escape_cell(freq),
                _escape_cell(asset_type),
                _escape_cell(desc),
                _escape_cell(table),
            )
        )

    index_rows: List[Tuple[str, str, int, str]] = []
    for acq in _sort_acq_keys(list(grouped.keys())):
        rows = grouped[acq]
        rows.sort(key=lambda r: (r[0].lower(), r[1], r[2]))
        slug = _safe_slug(acq)
        title = ACQ_TITLES.get(acq, acq)
        rel_name = f'{slug}.md'
        path = OUT_DIR / rel_name

        lines: List[str] = [
            '<!-- AUTO-GENERATED: do not edit -->',
            f'<!-- generated_at: {generated_at} -->',
            f'<!-- acquisition_type: {acq} -->',
            f'<!-- row_count: {len(rows)} -->',
            '',
            f'# {title}',
            '',
            f'本分册由 `docs/scripts/generate_datatype_catalog.py` 从 '
            f'`qteasy.datatypes.get_dtype_map()` 生成，共 **{len(rows)}** 条。',
            '',
            '请勿手改；更新内置类型后请重跑生成脚本。',
            '',
            '| name | freq | asset_type | description | table_name |',
            '| --- | --- | --- | --- | --- |',
        ]
        for name, freq, asset_type, desc, table in rows:
            lines.append(f'| {name} | {freq} | {asset_type} | {desc} | {table} |')
        lines.append('')
        path.write_text('\n'.join(lines), encoding='utf-8')
        index_rows.append((acq, title, len(rows), rel_name))

    # catalog_index：统计 + 链接
    index_path = OUT_DIR / 'catalog_index.md'
    index_lines: List[str] = [
        '<!-- AUTO-GENERATED: do not edit -->',
        f'<!-- generated_at: {generated_at} -->',
        f'<!-- total_rows: {total} -->',
        '',
        '# 内置 DataType 分册索引',
        '',
        f'生成时间：{generated_at}；合计 **{total}** 条内置数据类型。',
        '',
        '| acquisition_type | 说明 | 条数 | 分册 |',
        '| --- | --- | ---: | --- |',
    ]
    for acq, title, count, rel_name in index_rows:
        index_lines.append(f'| `{acq}` | {title} | {count} | [{rel_name}]({rel_name}) |')
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
    print(f'[generate_datatype_catalog] output: {OUT_DIR}')
    return total


def main() -> None:
    """命令行入口。"""
    generate()


if __name__ == '__main__':
    main()
