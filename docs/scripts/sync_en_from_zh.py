# coding=utf-8
"""Phase B：将 en .po 空条目 / fuzzy 补齐为英文金标准（copy-as-is 或 zh→en 机翻）。"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import polib
from deep_translator import GoogleTranslator

_SCRIPTS = Path(__file__).resolve().parent
EN_ROOT = _SCRIPTS.parent / 'source' / 'locale' / 'en' / 'LC_MESSAGES'
CACHE_PATH = _SCRIPTS / 'en_from_zh_translation_cache.json'

CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')
RTD_WRONG = re.compile(
    r'https://qteasy\.readthedocs\.io/(?:zh-cn|zh)/latest/',
    re.IGNORECASE,
)

PROTECT_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    (re.compile(r'`[^`]+`'), 'CODE'),
    (re.compile(r'\b(?:qteasy|QTEASY|QtEasy)\b'), 'QTEASY'),
    (
        re.compile(
            r'\b(?:Operator|HistoryPanel|DataType|DataSource|BaseStrategy|'
            r'Backtester|Trader|RiskManager|BrokerFacade|SimulatorBroker)\b'
        ),
        'CLS',
    ),
    (re.compile(r'\b(?:PT|PS|VS)\b'), 'SIG'),
    (re.compile(r'https?://[^\s\])>]+'), 'URL'),
]


def is_copy_as_is(msgid: str) -> bool:
    """非中文或几乎全是代码的 msgid 可直接复制。"""
    if not msgid.strip():
        return False
    if not CHINESE_RE.search(msgid):
        return True
    if msgid.count('`') >= 2 and len(CHINESE_RE.findall(msgid)) <= 2:
        return True
    return False


def load_cache() -> Dict[str, str]:
    """加载 zh→en 翻译缓存。"""
    if CACHE_PATH.is_file():
        return json.loads(CACHE_PATH.read_text(encoding='utf-8'))
    return {}


def save_cache(cache: Dict[str, str]) -> None:
    """保存翻译缓存。"""
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=0),
        encoding='utf-8',
    )


def protect(text: str) -> Tuple[str, List[str]]:
    """将代码/术语替换为占位符。"""
    tokens: List[str] = []

    def repl_factory(tag: str):
        def _repl(m: re.Match[str]) -> str:
            tokens.append(m.group(0))
            return f'⟦{tag}{len(tokens) - 1}⟧'

        return _repl

    out = text
    for pat, tag in PROTECT_PATTERNS:
        out = pat.sub(repl_factory(tag), out)
    return out, tokens


def unprotect(text: str, tokens: List[str]) -> str:
    """还原占位符。"""
    for i, tok in enumerate(tokens):
        for tag in ('CODE', 'QTEASY', 'CLS', 'SIG', 'URL'):
            placeholder = f'⟦{tag}{i}⟧'
            if placeholder in text:
                text = text.replace(placeholder, tok, 1)
    return text


def postprocess_en(text: str) -> str:
    """RTD 内链改为 /en/latest/。"""
    return RTD_WRONG.sub('https://qteasy.readthedocs.io/en/latest/', text)


def translate_zh_to_en(
    text: str,
    translator: GoogleTranslator,
    cache: Dict[str, str],
    max_retries: int = 4,
) -> str:
    """翻译单段中文为英文（带缓存、保护与重试）。"""
    key = text.strip()
    if key in cache:
        return cache[key]
    protected, tokens = protect(key)

    def _call(chunk: str) -> str:
        last_err: Exception | None = None
        for attempt in range(max_retries):
            try:
                return translator.translate(chunk)
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                time.sleep(0.5 * (attempt + 1))
        raise last_err  # type: ignore[misc]

    if len(protected) > 4500:
        parts = []
        for i in range(0, len(protected), 4000):
            parts.append(_call(protected[i : i + 4000]))
            time.sleep(0.1)
        result = ''.join(parts)
    else:
        result = _call(protected)
        time.sleep(0.05)
    result = unprotect(result, tokens)
    result = postprocess_en(result)
    cache[key] = result
    return result


def needs_work(entry: polib.POEntry) -> bool:
    """空 msgstr 或 fuzzy 需要处理。"""
    if entry.obsolete or not entry.msgid:
        return False
    if not entry.msgstr:
        return True
    if 'fuzzy' in entry.flags:
        return True
    return False


def fill_entry(
    entry: polib.POEntry,
    translator: GoogleTranslator | None,
    cache: Dict[str, str],
    dry_run: bool,
) -> str:
    """填充单条；返回动作标签 copy|translate|skip。"""
    if is_copy_as_is(entry.msgid):
        if not dry_run:
            entry.msgstr = entry.msgid
            if 'fuzzy' in entry.flags:
                entry.flags.remove('fuzzy')
        return 'copy'
    if translator is None:
        return 'skip'
    if dry_run:
        return 'translate'
    entry.msgstr = translate_zh_to_en(entry.msgid, translator, cache)
    if 'fuzzy' in entry.flags:
        entry.flags.remove('fuzzy')
    return 'translate'


def clear_header_fuzzy() -> int:
    """清除文件头 #, fuzzy。"""
    count = 0
    for path in EN_ROOT.rglob('*.po'):
        if path.name.endswith('~'):
            continue
        text = path.read_text(encoding='utf-8')
        if '\n#, fuzzy\n' in text:
            path.write_text(text.replace('\n#, fuzzy\n', '\n', 1), encoding='utf-8')
            count += 1
    return count


def iter_po_files(sections: List[str] | None) -> List[Path]:
    """按章节过滤 po 列表。"""
    files = sorted(p for p in EN_ROOT.rglob('*.po') if not p.name.endswith('~'))
    if not sections:
        return files
    sec_set = set(sections)
    out = []
    for p in files:
        rel = p.relative_to(EN_ROOT)
        top = rel.parts[0] if len(rel.parts) > 1 else '(root)'
        # references/datatypes 可用 datatypes 过滤
        if top in sec_set or str(rel).startswith(tuple(s + '/' for s in sec_set if '/' in s)):
            out.append(p)
            continue
        if 'datatypes' in sec_set and 'datatypes' in rel.parts:
            out.append(p)
    return out


def process_file(
    path: Path,
    translator: GoogleTranslator | None,
    cache: Dict[str, str],
    dry_run: bool,
    copy_only: bool,
    save_every: int = 25,
) -> Tuple[int, int, int]:
    """处理单个 po。返回 (copy, translated, skipped)。"""
    po = polib.pofile(str(path))
    n_copy = n_tr = n_skip = 0
    changed = False
    since_save = 0
    for entry in po:
        if not needs_work(entry):
            continue
        if copy_only and not is_copy_as_is(entry.msgid):
            n_skip += 1
            continue
        action = fill_entry(
            entry,
            None if copy_only else translator,
            cache,
            dry_run,
        )
        if action == 'copy':
            n_copy += 1
            changed = not dry_run
            since_save += 1
        elif action == 'translate':
            n_tr += 1
            changed = not dry_run
            since_save += 1
        else:
            n_skip += 1
        if changed and since_save >= save_every and not dry_run:
            po.metadata['PO-Revision-Date'] = '2026-08-21 18:00+0800'
            po.metadata['Last-Translator'] = 'Jackie PENG (sync_en_from_zh)'
            po.save(str(path))
            save_cache(cache)
            print(f'    checkpoint {path.name}: +{n_copy + n_tr}', flush=True)
            since_save = 0
    if changed:
        po.metadata['PO-Revision-Date'] = '2026-08-21 18:00+0800'
        po.metadata['Last-Translator'] = 'Jackie PENG (sync_en_from_zh)'
        po.save(str(path))
    return n_copy, n_tr, n_skip


def main(argv: List[str] | None = None) -> int:
    """CLI：补齐 en 空条目与 fuzzy。"""
    parser = argparse.ArgumentParser(description='Fill en .po from zh msgid')
    parser.add_argument('--sections', nargs='*', default=None)
    parser.add_argument('--copy-only', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit-files', type=int, default=0)
    args = parser.parse_args(argv)

    files = iter_po_files(args.sections)
    if args.limit_files:
        files = files[: args.limit_files]

    cache = load_cache()
    translator = None
    if not args.copy_only:
        translator = GoogleTranslator(source='zh-CN', target='en')

    total_c = total_t = total_s = 0
    mode = 'copy-only' if args.copy_only else 'copy+translate'
    print(f'[sync_en] files={len(files)} mode={mode} dry_run={args.dry_run}')
    for i, path in enumerate(files, 1):
        rel = path.relative_to(EN_ROOT)
        c, t, s = process_file(path, translator, cache, args.dry_run, args.copy_only)
        if c or t:
            print(f'  [{i}/{len(files)}] {rel}: copy={c} translate={t} skip={s}')
        total_c += c
        total_t += t
        total_s += s
        if not args.dry_run and (c or t):
            save_cache(cache)

    if not args.dry_run:
        save_cache(cache)
        hdr = clear_header_fuzzy()
        print(f'[sync_en] header_fuzzy_cleared={hdr}')
    print(
        f'[sync_en] done copy={total_c} translated={total_t} '
        f'skipped={total_s} cache_size={len(cache)}'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
