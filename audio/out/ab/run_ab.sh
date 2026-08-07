#!/usr/bin/env bash
# Serial A/B render. NOT parallel: two 96 kHz renders peak at ~4.5 GB each on an
# 11 GB box and thrash; the parallel attempt ran the engine synthesis 12x slower
# than the serial one.
set -u
cd /home/zany/f1-round2
rm -f audio/out/ab/CHAINDONE
F1_LAPDOWN=0 .venv/bin/python -m audio.master \
  --out audio/out/ab/master_A_nolapdown.wav \
  --report audio/out/ab/report_A_nolapdown.json > audio/out/ab/render_A.log 2>&1
echo "A rc=$?" >> audio/out/ab/CHAIN.status
.venv/bin/python -m audio.master \
  --out audio/out/ab/master_B_lapdown.wav \
  --report audio/out/ab/report_B_lapdown.json > audio/out/ab/render_B.log 2>&1
echo "B rc=$?" >> audio/out/ab/CHAIN.status
date > audio/out/ab/CHAINDONE
