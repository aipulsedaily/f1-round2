#!/usr/bin/env bash
# R2-4152 -- render the master, verify it, adjudicate it, diff the adjudication.
#
#   bash tools/r2_4152_render.sh
#
# Everything lands in audio/out/r2_4152/. The shipped delivery is NOT touched by
# this script; landing it is a separate, explicit step.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=audio/out/r2_4152
mkdir -p "$OUT"

.venv/bin/python -m audio.master \
    --out "$OUT/master_R2-4152.wav" \
    --report "$OUT/master_R2-4152.json" \
    --stems "$OUT/stems" 2>&1 | tee "$OUT/render.log"

.venv/bin/python -m audio.verify --wav "$OUT/master_R2-4152.wav" \
    2>&1 | tee "$OUT/verify.log" || true

.venv/bin/python -m tools.percept_matrix --wav "$OUT/master_R2-4152.wav" \
    --adjudicate --out "$OUT/matrix_R2-4152.json" \
    2>&1 | tee "$OUT/matrix_R2-4152.log"

.venv/bin/python -m tools.r2_4150_matrix_diff \
    audio/out/r2_4147/matrix_R2-4147.json "$OUT/matrix_R2-4152.json" \
    2>&1 | tee "$OUT/diff_vs_R2-4147.log"
