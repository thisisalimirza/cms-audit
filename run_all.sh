#!/usr/bin/env bash
# Run the full pipeline from raw CMS files to master results, tables, figures, manuscripts, and poster, then check every reported number.
# Usage: ROOT=/path/to/workdir bash repro/run_all.sh   (ROOT must contain data/ with the six Geo CSVs; see DATA.md)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-$(pwd)}"; export ROOT
cd "$ROOT"; mkdir -p data/provider_cache tables/exhibits figures writeup/poster
for s in "$HERE"/scripts/[0-9][0-9]_*.py; do echo "== $(basename "$s")"; python3 "$s"; done
echo "== 12_poster.js"; (cd writeup/poster && node "$HERE/scripts/12_poster.js" && soffice --headless --convert-to pdf poster_SGIM2027_48x36.pptx >/dev/null)
echo "== check_numbers.py"; python3 "$HERE/scripts/check_numbers.py" "$ROOT"
echo "done"
