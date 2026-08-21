#!/usr/bin/env bash
# Phase C：按序对 de fr es ja 做 en→lang 机翻（须在 docs/ 下或任意目录调用）
set -euo pipefail
DOCS="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DOCS"
PY=/opt/anaconda3/envs/py39/bin/python
LOGDIR=/tmp/qteasy_phase_c
mkdir -p "$LOGDIR"

for lang in de fr es ja; do
  echo "======== $(date '+%H:%M:%S') pivot $lang ========"
  PYTHONUNBUFFERED=1 "$PY" -u scripts/pivot_translate_from_en.py --lang "$lang" --skip-fill \
    2>&1 | tee "$LOGDIR/${lang}_pivot.log"
  "$PY" scripts/i18n_stats.py 2>&1 | grep "^${lang} " || true
done

# gaps + RTD
for lang in de fr es ja; do
  gaps="scripts/apply_${lang}_gaps.py"
  if [[ -f "$gaps" ]]; then
    echo "======== gaps $lang ========"
    "$PY" "$gaps" || true
  fi
done

"$PY" scripts/i18n_fix_rtd_residual.py || true
# zh_TW already done; re-run residual for all langs including en
echo "======== final stats ========"
"$PY" scripts/i18n_stats.py 2>&1 | head -20
echo "Phase C pivot wrapper done."
