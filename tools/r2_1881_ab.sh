#!/usr/bin/env bash
# R2-1881: the NEAR-BAND before/after harness.  4K, AgX, look None, exposure -3.628,
# matched camera and grade between arms, on the rented 5090 — never the local 1070.
#
#   tools/r2_1881_ab.sh BEFORE_MODULE.py AFTER_MODULE.py BEFORE.blend AFTER.blend
#
# It runs in four phases and REFUSES at the end of phase 2 rather than buying a GPU
# for an A/B that cannot mean anything:
#
#   1  bake the film-frame cameras into both arms, from the DECLARED live camera
#   2  compare the two arms' camera manifests — identical or STOP        (R2-1151)
#   3  render 4 frames x 2 arms at 3840x2160 @512 on the broker
#   4  verify each job's `effective` grade line, then crop and measure
#
# PHASE 2 IS THE POINT.  R2-1151: an A/B went to the client as "the fix does not
# work" when arm B had rendered with a socket unlinked.  Prose does not stop that;
# a byte comparison of what each arm is about to render does.
#
# PHASE 4'S GRADE CHECK IS THE SECOND HALF OF IT.  The blend declares a grade and
# the BROKER declares what it actually rendered with, on its own `effective` line —
# `exposure=-3.628  camera=CAM_fNNNN  lens=...  resolution_percentage=100`.  Those
# are different claims by different processes and only the second one is evidence.
set -u
R2=$HOME/f1-round2
VR=$HOME/vast-render
B=/opt/blender-5.2.0-linux-x64/blender
OUT=$R2/render/r2_1881
W=$R2/work/r2_1881
# f2760 is the client's own frame.  The other three were chosen by measurement, not
# by eye — see work/r2_1881/scan.json and the staging note.
FRAMES=${FRAMES:-2760,2832,2933,2089}
RES_W=3840; RES_H=2160; SAMPLES=512
BROKER=${VASTRENDER_URL:-http://127.0.0.1:8761}

MOD_B=$1; MOD_A=$2; BLEND_B=$3; BLEND_A=$4
mkdir -p "$OUT" "$W"

# ---- 1. bake, from live_campath.  ONE command, twice, differing only in the arm.
for arm in before after; do
  [ "$arm" = before ] && { M=$MOD_B; S=$BLEND_B; } || { M=$MOD_A; S=$BLEND_A; }
  echo "=== 1. bake cameras into $arm"
  "$B" -b --factory-startup -noaudio -P "$R2/tools/r2_1881_bake_cams.py" -- \
      --module "$M" --load "$S" --save "$OUT/${arm}_cams.blend" \
      --frames "$FRAMES" --manifest "$W/cams_${arm}.json" \
      2>&1 | grep -E "^\[bake\]|^>> " || true
done

# ---- 2. THE REFUSAL.
echo "=== 2. arm parity"
"$B" -b --factory-startup -noaudio -P "$R2/tools/r2_1881_bake_cams.py" -- \
    --compare "$W/cams_before.json" "$W/cams_after.json" 2>&1 \
    | grep -E "^  |^>> STAGE" | tee "$W/parity.log"
grep -q "R2_1881_ARMS_MATCHED" "$W/parity.log" || {
  echo ">> STAGE RESULT: R2_1881_AB_REFUSED  arms differ; nothing rendered, \$0 spent"
  exit 1; }

# ---- 3. render.  Both arms, same camera names, same res, same samples.
cd "$VR" || exit 1
IFS=, read -ra FS <<< "$FRAMES"
: > "$W/jobs.txt"
for arm in before after; do
  for f in "${FS[@]}"; do
    dst="$OUT/${arm}_f${f}.png"
    [ -s "$dst" ] && { echo "have  $dst"; continue; }
    echo "=== 3. $arm f$f ${RES_W}x${RES_H} @${SAMPLES}"
    VASTRENDER_URL=$BROKER ./rq render \
        --scene "$OUT/${arm}_cams.blend" --cam "CAM_f$(printf %04d "$f")" \
        --res "$RES_W" "$RES_H" --samples "$SAMPLES" --wait -o "$dst" \
        2>&1 | tee -a "$W/render.log" | tail -3
    grep -oE "^[0-9a-f]{12}" "$W/render.log" | tail -1 \
        | sed "s|\$|  ${arm}  f${f}|" >> "$W/jobs.txt"
  done
done

# ---- 4a. THE GRADE, AS THE BROKER ACTUALLY RAN IT.
echo "=== 4a. effective grade per job"
bad=0
while read -r jid arm f; do
  line=$(grep -h "job $jid effective" "$VR"/state*/broker.log | tail -1)
  echo "  $arm f$f  $jid"
  echo "$line" | grep -qE "exposure=-3\.628" || { echo "    *** exposure is NOT -3.628"; bad=1; }
  echo "$line" | grep -qE "camera=CAM_f0*$f" || { echo "    *** wrong camera"; bad=1; }
  echo "$line" | grep -qE "resolution_percentage=100" || { echo "    *** not full res"; bad=1; }
  echo "    $(echo "$line" | grep -oE "camera=[^ ]+ .*use_denoising=[^ ]+")"
done < "$W/jobs.txt"
[ "$bad" = 0 ] || { echo ">> STAGE RESULT: R2_1881_AB_GRADE_MISMATCH"; exit 1; }

# ---- 4b. crops chosen by the measurement, and the two metrics.
echo "=== 4b. crops + metrics"
"$R2/.venv/bin/python" "$R2/tools/r2_1881_nearband_ref.py" \
    --crops "$FRAMES" --out "$W/regions_nearband.json" | tail -20
for f in "${FS[@]}"; do
  "$R2/.venv/bin/python" "$R2/tools/r2_1821_ground_detail.py" \
      "$OUT/before_f${f}.png" --vs "$OUT/after_f${f}.png" \
      --regions "$W/regions_nearband.json" --label "f$f" \
      --json "$W/detail_f${f}.json" | tail -20
  "$R2/.venv/bin/python" "$R2/tools/r2_1661_measure.py" \
      "$OUT/before_f${f}.png" "$OUT/after_f${f}.png" \
      --json "$W/ground_f${f}.json" --label "f$f" | tail -12
  # 1:1 A/B strips at the measured crop boxes — never resampled
  "$R2/.venv/bin/python" - "$f" <<'PY'
import json, os, subprocess, sys
f = sys.argv[1]
# <<'PY' expands nothing, so this cannot be $HOME; expand it in Python.
R2 = os.path.expanduser("~/f1-round2")
reg = json.load(open(f"{R2}/work/r2_1881/regions_nearband.json"))
for nm, (x, y, w, h) in reg.items():
    if not nm.startswith(f"f{int(f):04d}_"):
        continue
    subprocess.run([f"{R2}/.venv/bin/python", f"{R2}/tools/peep.py", "ab",
                    f"{R2}/render/r2_1881/before_f{f}.png",
                    f"{R2}/render/r2_1881/after_f{f}.png",
                    f"{R2}/render/r2_1881/AB_{nm}.png",
                    "--box", str(x), str(y), str(w), str(h)], check=True)
PY
done
echo ">> STAGE RESULT: R2_1881_AB_DONE"
ls -la "$OUT"/*.png
