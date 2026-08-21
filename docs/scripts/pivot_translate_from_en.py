# coding=utf-8
"""Phase 2：以 en msgstr 为 pivot，将目标语言 .po 译为 de/fr/es 等。"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import polib
from deep_translator import GoogleTranslator

_SCRIPTS = Path(__file__).resolve().parent
LOCALE = _SCRIPTS.parent / 'source' / 'locale'
EN_ROOT = LOCALE / 'en' / 'LC_MESSAGES'

CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')

LANG_CONFIG: Dict[str, Dict[str, str]] = {
    'de': {'target': 'de', 'rtd': 'de'},
    'fr': {'target': 'fr', 'rtd': 'fr'},
    'es': {'target': 'es', 'rtd': 'es'},
    'ja': {'target': 'ja', 'rtd': 'ja'},
}

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
    """非中文 msgid 可直接复制 en（或 msgid 本身）。"""
    if not msgid.strip():
        return False
    if not CHINESE_RE.search(msgid):
        return True
    if msgid.count('`') >= 2 and len(CHINESE_RE.findall(msgid)) <= 2:
        return True
    return False


def locale_root(lang: str) -> Path:
    """目标语言 LC_MESSAGES 根目录。"""
    return LOCALE / lang / 'LC_MESSAGES'


def cache_path(lang: str) -> Path:
    """翻译缓存文件路径。"""
    return _SCRIPTS / f'{lang}_translation_cache.json'


def rtd_url_pattern() -> re.Pattern[str]:
    """匹配需替换的 RTD 英文/简体链接。"""
    return re.compile(
        r'https://qteasy\.readthedocs\.io/(?:en|zh-cn)/latest/',
        re.IGNORECASE,
    )


def load_cache(lang: str) -> Dict[str, str]:
    """加载翻译缓存。"""
    path = cache_path(lang)
    if path.is_file():
        return json.loads(path.read_text(encoding='utf-8'))
    return {}


def save_cache(lang: str, cache: Dict[str, str]) -> None:
    """保存翻译缓存。"""
    cache_path(lang).write_text(
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


def postprocess_locale(text: str, rtd_code: str) -> str:
    """RTD 内链与常见后处理。"""
    text = rtd_url_pattern().sub(f'https://qteasy.readthedocs.io/{rtd_code}/latest/', text)
    text = re.sub(r'``\s*``', '', text)
    return text


def needs_pivot_translation(
    msgid: str,
    msgstr_loc: str,
    msgstr_en: str,
    is_fuzzy: bool = False,
) -> bool:
    """判断是否需要从 en 机翻为目标语言。"""
    if not CHINESE_RE.search(msgid):
        return False
    if not msgstr_en.strip():
        return False
    if is_fuzzy:
        return True
    if not msgstr_loc.strip() or msgstr_loc.strip() == msgstr_en.strip():
        return True
    return False


def translate_text(
    text: str,
    translator: GoogleTranslator,
    cache: Dict[str, str],
    rtd_code: str,
    max_retries: int = 4,
) -> str:
    """翻译单段文本（带缓存、保护与重试）。"""
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
        time.sleep(0.08)
    result = unprotect(result, tokens)
    result = postprocess_locale(result, rtd_code)
    cache[key] = result
    return result


def fill_from_en(loc_path: Path, en_map: Dict[str, str]) -> int:
    """将非中文条目从 en 复制到目标语言（代码/API/英文原文）。"""
    po = polib.pofile(str(loc_path))
    filled = 0
    for entry in po:
        if entry.obsolete or not entry.msgid:
            continue
        if entry.msgstr and 'fuzzy' not in entry.flags:
            continue
        en_s = en_map.get(entry.msgid, '')
        if is_copy_as_is(entry.msgid):
            new = en_s if en_s else entry.msgid
            if entry.msgstr != new:
                entry.msgstr = new
                filled += 1
                if 'fuzzy' in entry.flags:
                    entry.flags.remove('fuzzy')
        elif not entry.msgstr and en_s and not CHINESE_RE.search(entry.msgid):
            entry.msgstr = en_s
            filled += 1
    if filled:
        po.metadata['PO-Revision-Date'] = '2026-05-24 10:00+0800'
        po.metadata['Last-Translator'] = 'Jackie PENG (pivot_translate_from_en)'
        po.save(str(loc_path))
    return filled


def process_file(
    loc_path: Path,
    lang: str,
    translator: GoogleTranslator,
    cache: Dict[str, str],
    rtd_code: str,
    dry_run: bool,
    save_every: int = 25,
) -> Tuple[int, int]:
    """机翻单个 po 文件中需 pivot 的条目。"""
    root = locale_root(lang)
    rel = loc_path.relative_to(root)
    en_path = EN_ROOT / rel
    if not en_path.is_file():
        return 0, 0

    loc_po = polib.pofile(str(loc_path))
    en_po = polib.pofile(str(en_path))
    en_map = {e.msgid: e.msgstr for e in en_po if e.msgid and not e.obsolete}

    translated = skipped = 0
    since_save = 0
    for entry in loc_po:
        if entry.obsolete or not entry.msgid:
            continue
        en_s = en_map.get(entry.msgid, '')
        fuzzy = 'fuzzy' in entry.flags
        if not needs_pivot_translation(entry.msgid, entry.msgstr, en_s, fuzzy):
            skipped += 1
            continue
        if dry_run:
            translated += 1
            continue
        try:
            entry.msgstr = translate_text(en_s, translator, cache, rtd_code)
            if 'fuzzy' in entry.flags:
                entry.flags.remove('fuzzy')
            translated += 1
            since_save += 1
        except Exception as exc:  # noqa: BLE001
            print(f'  WARN {rel}: {exc!s} :: {entry.msgid[:60]!r}', flush=True)
        if since_save >= save_every:
            loc_po.save(str(loc_path))
            save_cache(lang, cache)
            print(f'    checkpoint {rel.name}: +{translated}', flush=True)
            since_save = 0

    if not dry_run and translated:
        loc_po.save(str(loc_path))
        text = loc_path.read_text(encoding='utf-8')
        if '\n#, fuzzy\n' in text:
            loc_path.write_text(text.replace('\n#, fuzzy\n', '\n', 1), encoding='utf-8')

    return translated, skipped


def iter_po_files(lang: str, sections: Iterable[str] | None) -> List[Path]:
    """按章节过滤 po 文件列表。"""
    root = locale_root(lang)
    files = sorted(p for p in root.rglob('*.po') if not p.name.endswith('~'))
    if not sections:
        return files
    sec_set = set(sections)
    return [p for p in files if (p.relative_to(root).parts[0] if len(p.relative_to(root).parts) > 1 else '(root)') in sec_set]


def run_fill_pass(lang: str, sections: Iterable[str] | None) -> int:
    """全量 fill：非中文条目复制 en。"""
    total = 0
    for loc_path in iter_po_files(lang, sections):
        rel = loc_path.relative_to(locale_root(lang))
        en_path = EN_ROOT / rel
        if not en_path.is_file():
            continue
        en_po = polib.pofile(str(en_path))
        en_map = {e.msgid: e.msgstr for e in en_po if e.msgid and not e.obsolete}
        n = fill_from_en(loc_path, en_map)
        if n:
            print(f'  fill {rel}: +{n}')
            total += n
    return total


def clear_header_fuzzy(lang: str) -> int:
    """清除文件头 #, fuzzy。"""
    count = 0
    for path in locale_root(lang).rglob('*.po'):
        if path.name.endswith('~'):
            continue
        text = path.read_text(encoding='utf-8')
        if '\n#, fuzzy\n' in text:
            path.write_text(text.replace('\n#, fuzzy\n', '\n', 1), encoding='utf-8')
            count += 1
    return count


def main(argv: List[str] | None = None) -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description='Translate locale .po from en pivot')
    parser.add_argument('--lang', choices=sorted(LANG_CONFIG), default='fr')
    parser.add_argument('--sections', nargs='*', default=None)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--fill-only', action='store_true', help='Only copy non-Chinese from en')
    parser.add_argument('--skip-fill', action='store_true', help='Skip fill pass')
    parser.add_argument('--limit-files', type=int, default=0)
    args = parser.parse_args(argv)

    cfg = LANG_CONFIG[args.lang]
    rtd_code = cfg['rtd']

    if not args.skip_fill and not args.dry_run:
        print(f'[{args.lang}_pivot] fill pass...')
        filled = run_fill_pass(args.lang, args.sections)
        print(f'[{args.lang}_pivot] fill total={filled}')
        if args.fill_only:
            clear_header_fuzzy(args.lang)
            return 0

    files = iter_po_files(args.lang, args.sections)
    if args.limit_files:
        files = files[: args.limit_files]

    cache = load_cache(args.lang)
    translator = GoogleTranslator(source='en', target=cfg['target'])

    total_tr = 0
    print(f'[{args.lang}_pivot] translate files={len(files)} dry_run={args.dry_run}')
    for i, loc_path in enumerate(files, 1):
        tr, _ = process_file(loc_path, args.lang, translator, cache, rtd_code, args.dry_run)
        if tr:
            print(f'  [{i}/{len(files)}] {loc_path.relative_to(locale_root(args.lang))}: +{tr}')
        total_tr += tr
        if not args.dry_run:
            save_cache(args.lang, cache)

    if not args.dry_run:
        save_cache(args.lang, cache)
        clear_header_fuzzy(args.lang)
    print(f'[{args.lang}_pivot] done translated={total_tr} cache_size={len(cache)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
