# coding=utf-8
"""以 OpenCC s2t + 台湾术语表填充 zh_TW .po 的空条目 / fuzzy（默认不覆盖已有译文）。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import polib
from opencc import OpenCC

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from zh_tw_taiwan_terms import apply_taiwan_terms

ZH_TW_ROOT = _SCRIPTS.parent / 'source' / 'locale' / 'zh_TW' / 'LC_MESSAGES'

RTD_ZHCN = re.compile(r'https://qteasy\.readthedocs\.io/(?:zh-cn|zh)/latest/', re.I)
CHINESE = re.compile(r'[\u4e00-\u9fff]')


def is_copy_as_is(msgid: str) -> bool:
    """英文/代码类 msgid 直接复制。"""
    if not msgid.strip():
        return False
    if not CHINESE.search(msgid):
        return True
    if msgid.count('`') >= 2 and len(CHINESE.findall(msgid)) <= 2:
        return True
    return False


def convert_text(converter: OpenCC, msgid: str) -> str:
    """将 msgid 转为台湾繁中 msgstr。"""
    if is_copy_as_is(msgid):
        return msgid
    # 先对简体套台湾词，再 OpenCC，再对残留大陆繁体套台湾词
    out = apply_taiwan_terms(msgid)
    out = converter.convert(out)
    out = apply_taiwan_terms(out)
    out = RTD_ZHCN.sub('https://qteasy.readthedocs.io/zh-tw/latest/', out)
    return out


def needs_fill(entry: polib.POEntry, new_only: bool) -> bool:
    """是否需要填充。

    Parameters
    ----------
    entry : polib.POEntry
        词条。
    new_only : bool
        True 时仅空 msgstr 或 fuzzy（不覆盖已有完整译文）。
    """
    if entry.obsolete or not entry.msgid:
        return False
    if not new_only:
        return True
    if not entry.msgstr:
        return True
    if 'fuzzy' in entry.flags:
        return True
    return False


def process_po(po_path: Path, converter: OpenCC, new_only: bool) -> int:
    """填充单个 po 文件。"""
    po = polib.pofile(str(po_path))
    filled = 0
    for entry in po:
        if not needs_fill(entry, new_only):
            continue
        new = convert_text(converter, entry.msgid)
        if entry.msgstr != new:
            entry.msgstr = new
            filled += 1
        if 'fuzzy' in entry.flags:
            entry.flags.remove('fuzzy')
    if filled:
        po.metadata['PO-Revision-Date'] = '2026-08-21 22:00+0800'
        po.metadata['Last-Translator'] = 'Jackie PENG (zh_tw_fill_opencc)'
        po.save(str(po_path))
    return filled


def clear_header_fuzzy() -> int:
    """清除文件头 #, fuzzy。"""
    count = 0
    for path in ZH_TW_ROOT.rglob('*.po'):
        if path.name.endswith('~'):
            continue
        text = path.read_text(encoding='utf-8')
        if '\n#, fuzzy\n' in text:
            path.write_text(text.replace('\n#, fuzzy\n', '\n', 1), encoding='utf-8')
            count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    """遍历 zh_TW po；默认仅补新缺口。"""
    parser = argparse.ArgumentParser(description='Fill zh_TW .po with OpenCC + Taiwan terms')
    parser.add_argument(
        '--all',
        action='store_true',
        help='Also rewrite existing msgstr (full terminology pass; default: new-only)',
    )
    args = parser.parse_args(argv)
    new_only = not args.all

    converter = OpenCC('s2t')
    total = 0
    files = sorted(p for p in ZH_TW_ROOT.rglob('*.po') if not p.name.endswith('~'))
    print(f'[zh_tw] files={len(files)} new_only={new_only}')
    for i, po_path in enumerate(files, 1):
        n = process_po(po_path, converter, new_only=new_only)
        if n:
            print(f'  [{i}/{len(files)}] {po_path.relative_to(ZH_TW_ROOT)}: +{n}')
            total += n
    hdr = clear_header_fuzzy()
    print(f'zh_tw_fill_opencc: filled={total} header_fuzzy_cleared={hdr}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
