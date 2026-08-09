#!/bin/bash
# R2-3721 item 2: the camera-only re-sweep, one arm at a time.
#
# WORLD HELD FIXED, CAMERA VARIED. Every arm reuses an ALREADY-DUMPED point
# cloud, so the only thing that differs between arms is the projection --
# tools/retier.sh's own header calls that out as the legitimate way to run a
# camera-only re-derive. Two worlds are used, and each world's arms are only
# ever compared with each other:
#
#   assembly9  work/w2_0/retier_a9/world_points.npz   -- the world the DELIVERED
#              docs/screen_presence*.json was swept from, so its arms answer
#              "what would the delivered tiering have said".
#   assembly10 work/w2_0/retier_a10/world_points.npz  -- the newest dump on
#              disk. NEITHER is the shipping world (SHIPPING.md says
#              assembly14); no assembly14 point dump exists and dumping one
#              opens a 7 GB+ blend on a box with 2 GB free. The a10 pair is the
#              robustness arm: if the camera answer is the same on two
#              different worlds it is not an artefact of one of them.
#
# --uniform-shutter on every arm: retier.sh's header and screen_presence.py's
# own --uniform-shutter help both say it is THE SHIPPING MODE since R2-037.
set -u
R2=/home/zany/f1-round2
SCR=${SCR:-$R2/work/r23721_item2}   # where make_ctl.py wrote the control camera paths
OUT=$R2/work/r23721_item2
mkdir -p "$OUT"
cd "$R2" || exit 1

# WHY SOME ARMS PASS --why-stale.  R2-3721 added film13/film14's bytes to
# live_campath.KNOWN_STALE, because they are the bytes docs/screen_presence*.json
# was actually swept from, and tools/screen_presence.py now refuses them.  The
# baseline arms sweep that camera ON PURPOSE -- that is the whole experiment --
# so they say so, and the refusal stays intact for everyone who does not.
WHYSTALE="R2-3721 item 2 / defect #159: the orphan is the BASELINE arm of this \
comparison. Sweeping it is the measurement, not the mistake."

sweep() {  # arm points campath [extra args...]
  local arm="$1" pts="$2" cam="$3"; shift 3
  if [ -f "$OUT/${arm}_sp_points.npz" ]; then
    echo "== $arm already done, skipping"; return 0
  fi
  echo "== $arm  points=$pts  camera=$cam  $(date -Is)"
  bash tools/buildlock.sh --small "sp_$arm" \
    python3 tools/screen_presence.py \
      --points "$pts" --path "$cam" --sheet docs/beat_sheet.json \
      --uniform-shutter "$@" \
      --out "$OUT/${arm}_sp_objects.json" \
      --npz "$OUT/${arm}_sp_points.npz" > "$OUT/${arm}_sweep.log" 2>&1
  echo "   rc=$? $(grep -c '^\[SP\] wrote' "$OUT/${arm}_sweep.log") wrote-lines  $(date -Is)"
  tail -2 "$OUT/${arm}_sweep.log"
}

A9=work/w2_0/retier_a9/world_points.npz
A10=work/w2_0/retier_a10/world_points.npz

# --- the answer, and the beat-1 isolation -------------------------------
sweep a9_film24   "$A9"  render/film24_path.json
sweep a9_k100     "$A9"  "$SCR/ctl_k100_path.json"
# --- the controls: a measured FRACTION of the same defect ---------------
sweep a9_k025     "$A9"  "$SCR/ctl_k025_path.json"
sweep a9_k010     "$A9"  "$SCR/ctl_k010_path.json"
# --- robustness on a different world ------------------------------------
sweep a10_film14  "$A10" render/film14_path.json --why-stale "$WHYSTALE"
sweep a10_film24  "$A10" render/film24_path.json
# --- the camera the only rendered pixels that exist actually came from -----
# work/r22161_proxy (the free 2,978-frame proxy) was rendered from film22
# (tools/r2_2881_pixelpeep.py:76 PROXY_PATH_JSON), and docs/LIVE-CAMERA.md still
# declares film19, whose bytes ARE film22's. So film22 separates the R2-1007
# orphan defect (film14 -> film22) from the newer film22 -> film24 re-pace.
sweep a9_film22   "$A9"  render/film22_path.json

echo ">> ALL SWEEPS DONE $(date -Is)"
