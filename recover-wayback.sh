#!/usr/bin/env bash
# recover-wayback.sh
# Attempts to download missing images from the Wayback Machine.
# For each filename it first queries the CDX API to find the archived
# year/month URL, then downloads the raw file via the if_ endpoint.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MISSING_TXT="$SCRIPT_DIR/missing-images.txt"
OUT_DIR="$SCRIPT_DIR/wp-images"
FAILED_LOG="$SCRIPT_DIR/wayback-failed.txt"
R2_BASE="https://pub-7f7d07c430fd4c3eb11a4e6eae938ce3.r2.dev/"

if [[ ! -f "$MISSING_TXT" ]]; then
  echo "Error: missing-images.txt not found."
  exit 1
fi

mkdir -p "$OUT_DIR"
> "$FAILED_LOG"

# ── Extract filenames from the R2 URLs in missing-images.txt ─────────────────

FILENAMES=()
while IFS= read -r line; do
  [[ "$line" == "${R2_BASE}"* ]] && FILENAMES+=("${line#${R2_BASE}}")
done < "$MISSING_TXT"

TOTAL=${#FILENAMES[@]}
echo "Attempting to recover $TOTAL images from the Wayback Machine..."
echo ""

COUNT=0; RECOVERED=0; FAILED=0; SKIPPED=0

# ── CDX query helper ─────────────────────────────────────────────────────────
# Python builds the URL (regex-escape + percent-encode); curl does the fetch.
cdx_lookup() {
  local cdx_url
  cdx_url=$(/usr/bin/python3 -c "
import re, urllib.parse, sys
fname = sys.argv[1]
pattern = re.escape(fname)
parts = [
  'url='    + urllib.parse.quote('sailingoroboro.com/wp-content/uploads/', safe='/:'),
  'matchType=prefix',
  'output=text',
  'fl=original',
  'filter=' + urllib.parse.quote('statuscode:200'),
  'filter=' + urllib.parse.quote('original:.*/' + pattern + chr(36)),
  'limit=1',
]
print('https://web.archive.org/cdx/search/cdx?' + '&'.join(parts))
" "$1")
  curl -s --max-time 20 "$cdx_url" 2>/dev/null | head -1
}

# ── Main loop ─────────────────────────────────────────────────────────────────

for filename in "${FILENAMES[@]}"; do
  COUNT=$(( COUNT + 1 ))
  dest="$OUT_DIR/$filename"

  # Skip already recovered
  if [[ -f "$dest" ]]; then
    printf "[%d/%d] %-52s skipped\n" "$COUNT" "$TOTAL" "$filename"
    SKIPPED=$(( SKIPPED + 1 ))
    continue
  fi

  printf "[%d/%d] %-52s " "$COUNT" "$TOTAL" "$filename"

  # Step 1: find original archived URL via CDX API
  original_url=$(cdx_lookup "$filename")

  if [[ -z "$original_url" ]]; then
    printf "not in archive\n"
    echo "${R2_BASE}${filename}" >> "$FAILED_LOG"
    FAILED=$(( FAILED + 1 ))
    sleep 0.3
    continue
  fi

  # Step 2: download raw file (if_ = no Wayback toolbar injected)
  wb_url="https://web.archive.org/web/20200101000000if_/${original_url}"

  if curl -fsSL \
       --max-time 60 \
       --retry 2 \
       --retry-delay 3 \
       --output "$dest" \
       "$wb_url" 2>/dev/null; then
    size=$(ls -lh "$dest" | awk '{print $5}')
    printf "recovered (%s)\n" "$size"
    RECOVERED=$(( RECOVERED + 1 ))
  else
    printf "download failed\n"
    echo "${R2_BASE}${filename}" >> "$FAILED_LOG"
    rm -f "$dest"
    FAILED=$(( FAILED + 1 ))
  fi

  sleep 0.5   # be polite to archive.org

done

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "────────────────────────────────────"
printf "  Recovered : %d / %d\n" "$RECOVERED" "$TOTAL"
printf "  Skipped   : %d (already existed)\n" "$SKIPPED"
printf "  Failed    : %d\n" "$FAILED"
echo "────────────────────────────────────"
[[ $FAILED -gt 0 ]] && echo "  Failures logged to: $FAILED_LOG"
