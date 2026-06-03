#!/usr/bin/env bash
# download-images.sh
# Downloads all image attachments from the WordPress XML export.
# Safe to re-run — skips files that already exist.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
XML="$SCRIPT_DIR/Oroboro_Blog_Back_Up_All.xml"
OUT_DIR="$SCRIPT_DIR/wp-images"
FAILED_LOG="$OUT_DIR/failed.txt"

# ── Preflight ─────────────────────────────────────────────────────────────────

if [[ ! -f "$XML" ]]; then
  echo "Error: $XML not found."
  echo "Place Oroboro_Blog_Back_Up_All.xml in the same folder as this script."
  exit 1
fi

mkdir -p "$OUT_DIR"
> "$FAILED_LOG"

# ── Extract attachment URLs ───────────────────────────────────────────────────

echo "Scanning $XML for image attachments..."

URLS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && URLS+=("$line")
done < <(
  /usr/bin/python3 - "$XML" <<'PY'
import re, sys
for line in open(sys.argv[1], encoding='utf-8', errors='replace'):
    m = re.search(r'<wp:attachment_url><!\[CDATA\[(.*?)\]\]>', line)
    if m:
        url = m.group(1).strip()
        if re.search(r'\.(jpe?g|png|gif|webp|svg|tiff?|bmp)(\?.*)?$', url, re.IGNORECASE):
            print(url)
PY
)

TOTAL=${#URLS[@]}

if [[ $TOTAL -eq 0 ]]; then
  echo "No image attachments found in the XML."
  exit 1
fi

echo "Found $TOTAL images."
echo ""

# ── Download loop ─────────────────────────────────────────────────────────────

COUNT=0
DOWNLOADED=0
SKIPPED=0
FAILED=0

for url in "${URLS[@]}"; do
  COUNT=$(( COUNT + 1 ))
  filename="$(basename "${url%%\?*}")"
  dest="$OUT_DIR/$filename"

  if [[ -f "$dest" ]]; then
    echo "Skipping  $COUNT/$TOTAL: $filename"
    SKIPPED=$(( SKIPPED + 1 ))
    continue
  fi

  echo -n "Downloading $COUNT/$TOTAL: $filename ... "

  if curl -fsSL \
       --max-time 30 \
       --retry 2 \
       --retry-delay 3 \
       --output "$dest" \
       "$url" 2>/dev/null; then
    size=$(ls -lh "$dest" | awk '{print $5}')
    echo "$size"
    DOWNLOADED=$(( DOWNLOADED + 1 ))
  else
    echo "FAILED"
    echo "$url" >> "$FAILED_LOG"
    rm -f "$dest"
    FAILED=$(( FAILED + 1 ))
  fi
done

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "────────────────────────────────"
echo "  Downloaded : $DOWNLOADED"
echo "  Skipped    : $SKIPPED"
echo "  Failed     : $FAILED"
echo "────────────────────────────────"
[[ $FAILED -gt 0 ]] && echo "  Failed URLs → $FAILED_LOG"
