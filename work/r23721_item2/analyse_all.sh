#!/bin/bash
# R2-3721 item 2: every arm through the SAME chain, and every comparison named.
set -u
R2=$HOME/f1-round2
OUT=$R2/work/r23721_item2
cd "$R2" || exit 1
BASE9=$OUT/a9_orphan14_item_presence.json

ip() {
  local arm="$1"
  [ -f "$OUT/${arm}_sp_points.npz" ] || { echo "!! $arm: no sweep"; return 1; }
  [ -f "$OUT/${arm}_item_presence.json" ] && return 0
  python3 tools/item_presence.py \
    --npz "$OUT/${arm}_sp_points.npz" --sheet docs/beat_sheet.json \
    --objects "$OUT/${arm}_sp_objects.json" \
    --out "$OUT/${arm}_item_presence.json" \
    --tiers "$OUT/${arm}_tiers_raw.json" 2>&1 | grep -E "proposed tiers|STAGE RESULT"
}

d() {  # base new label
  python3 work/w2_0/tier_delta.py "$1" "$2" --label "$3" \
    --out "$OUT/delta_$(basename "$2" _item_presence.json).json" \
    2>&1 | grep -vE "^      |^$"
}

for arm in "$@"; do ip "$arm"; done

for arm in "$@"; do
  [ -f "$OUT/${arm}_item_presence.json" ] || continue
  case "$arm" in
    a10_*) continue;;
  esac
  echo; echo "#################### $arm ####################"
  d "$BASE9" "$OUT/${arm}_item_presence.json" "assembly9 orphan(film14) -> $arm"
done

if [ -f "$OUT/a10_film14_item_presence.json" ] && \
   [ -f "$OUT/a10_film24_item_presence.json" ]; then
  echo; echo "#################### assembly10 robustness ####################"
  d "$OUT/a10_film14_item_presence.json" "$OUT/a10_film24_item_presence.json" \
    "assembly10 orphan(film14) -> film24"
fi
