#!/usr/bin/env bash
# THE DRESSING-RELIEF GATE BATTERY, run on assembly7 (build_dressing R2-038 +
# R2-057 repaired, world_contract 1.2.1).  This is v121/battery.sh re-pointed
# at assembly7 with assembly6 as the reference, and nothing in it is rewritten:
# the same gates, the same nine probes, the same controls, the same
# module-boundary sweep.
#
# THE FIRST THING IT RUNS IS THE PER-OBJECT VERTEX FINGERPRINT, for the reason
# v121 gives in capitals: assembly5 and assembly6 had BIT-IDENTICAL module
# summaries while one object had moved 3.19 m.  Counts do not move when
# vertices do.
#
# WHAT THIS BATTERY IS EXPECTED TO SHOW, stated before it runs so that a pass
# is a prediction met and not a shrug: the dressing repair touched only shader
# node trees.  fp_diff must find ZERO moved objects.  A moved object would mean
# a module other than mine changed under me between 2026-08-02 15:51 (when
# assembly6 was built) and now, and would have to be chased before anything
# else in this report is believed.
#
# EXIT CODES ARE VERDICTS NOW, AND THAT IS NEW           (R2, 2026-08-03)
# ------------------------------------------------------------------------------
# This file was written a few hours ago saying:
#
#     "EXIT CODES ARE NOT VERDICTS HERE. placement_gate.py, collision_gate.py
#      and instance_variety.py all exit 0 on FAIL, and Blender 5.2 exits 0 on
#      an uncaught script exception. Read the verdict text."
#
# All three of those are fixed. The gates return 0/1/2/3 from the same string
# they print (tools/gate_exit.py), and the runner below reads the status instead
# of printing and discarding it.
#
# THIS HEADER USED TO SAY "and every `-P` entry point is wrapped so an uncaught
# exception is a status 2 rather than Blender's 0". THAT WAS NOT TRUE OF THIS
# BATTERY'S OWN STEPS, and a header citing a safeguard that does not exist is
# worse than no header, because it stops the next person looking. Checked with
# /usr/bin/grep on 2026-08-03 -- zero occurrences of `gate_exit` in any of:
#     v120/vertex_fingerprint.py   (lines 69, 71)
#     v120/variety_distribution.py (line 129)
#     tools/mesh_reuse.py          (line 130)  -- no STAGE RESULT at all
#     probe_pitexit.py             (line 134)
# An uncaught exception in those four is exit 0 and `run ()` records `ok`. Read
# their output; do not trust their status. `fp_diff.py` was a fifth and is now
# repaired: it declares its expectation on the command line and checks it.
#
#   run    ...   a MEASUREMENT. Recorded, and the survey CARRIES ON; stopping
#                at the first finding on a multi-hour run hides the rest.
#   expect ...   a CONTROL, with the job it must do written beside it. A
#                positive control that does not FAIL halts the run.
#
# The runner is ../lib_battery.sh -- one copy, shared with v120 and v121,
# because a private copy of shared behaviour is what defeated the socket guard
# (R2-057) and this file's `run ()` was the third copy of it.
#
# THE PROBES NOW TAKE --out. probeA..probeK wrote hardcoded filenames into the
# assembly root, so this battery would have overwritten the probeD.json /
# probeG.json that v120/collect.py reads. Each is given a path under $V.
set -u
B=/opt/blender-5.2.0-linux-x64/blender
R2=/home/zany/f1-round2
D=$R2/render/world/assembly/r2
V0=$D/v120
V1=$D/v121
V=$D/v122
OLD=$D/assembly6.blend
S=$D/assembly7.blend

echo "########## BATTERY START $(date +%T)"
ls -l $OLD $S
echo "--- instrument versions ---"
md5sum $R2/tools/placement_gate.py $R2/tools/depth_probe.py \
       $R2/tools/collision_gate.py $R2/tools/instance_variety.py \
       $R2/world/build_dressing.py $R2/world/itemkit.py \
       $R2/world/world_contract.py

source "$D/lib_battery.sh"

# ------------------------------------------------- VERTEX-LEVEL COMPARISON --
run "vertex fingerprint assembly6 (the shipping world)" \
  $B -b -noaudio $OLD --factory-startup -P $V0/vertex_fingerprint.py -- $V/fp_assembly6.json
run "vertex fingerprint assembly7 (the dressing repair)" \
  $B -b -noaudio $S --factory-startup -P $V0/vertex_fingerprint.py -- $V/fp_assembly7.json
# The expectation is DECLARED to the tool, not just to the reader. Until
# 2026-08-03 fp_diff.py computed `moved`, printed it and never consulted it: it
# could print 100.00 % and this battery still ended BATTERY_OK.
expect pass "fp_diff  assembly6 -> assembly7   (EXPECT: 0 objects moved)" \
  python3 $V0/fp_diff.py $V/fp_assembly6.json $V/fp_assembly7.json --expect-moved 0

# ---------------------------------------------------------------- gates ---
regenerate_controls "$B" "$V0/make_controls.py" "$V0"

# THE PLACEMENT GATE HAD NO CONTROL IN THIS BATTERY UNTIL 2026-08-03, in any of
# the three versions -- only the two `run` lines below, against the world. It is
# the gate that guards every item placement and it is the one already caught
# testing empty air over 28 % of the lap (MASTER-PLAN §6.17). Its three controls
# now run BEFORE the measurements, so a bad instrument halts the battery instead
# of quietly colouring both surveys.
expect fail    "placement_gate POSITIVE control (obstacle ON the racing line)" \
  $B -b $V0/ctl_place_pos.blend --factory-startup -P $R2/tools/placement_gate.py -- \
     --out $V/ctl_place_pos.json
expect pass    "placement_gate FAR negative control (obstacle 3 km off)" \
  $B -b $V0/ctl_place_neg.blend --factory-startup -P $R2/tools/placement_gate.py -- \
     --out $V/ctl_place_neg.json
# The far control passes with 0 vertices measured -- it proves the gate does not
# INVENT violations and nothing more. Over-rejection needs a case the gate has
# to measure and still pass, and `ctl_assert` is what stops that case silently
# drifting back out to the 3 km one.
expect pass    "placement_gate NEAR-MISS negative control (just outside)" \
  $B -b $V0/ctl_place_nearmiss_neg.blend --factory-startup -P $R2/tools/placement_gate.py -- \
     --out $V/ctl_place_nearmiss_neg.json
expect pass    "  ... and it was MEASURED per-vertex, near the edge" \
  python3 $D/ctl_assert.py --json $V/ctl_place_nearmiss_neg.json \
     --label "placement near-miss" \
     --require measured-per-vertex clean clearance-between 0.05 1.50

run "placement_gate (shipped default allow)" \
  $B -b $S --factory-startup -P $R2/tools/placement_gate.py -- \
     --out $V/placement_v122.json
run "placement_gate (+ barrier ground objects)" \
  $B -b $S --factory-startup -P $R2/tools/placement_gate.py -- \
     --out $V/placement_v122_ground.json \
     --allow "SURF_,TER_Ground,BR_Runoff,BR_Gravel,BR_Subbase,BR_Trap,BR_Stone,BR_Verge,ARCH_Paving,ARCH_Markings,Floor,Turntable_,Platform_"

expect vacuous "collision_gate on the world (no CAR: must REFUSE)" \
  $B -b $S --factory-startup -P $R2/tools/collision_gate.py -- --out $V/collision_v122.json
expect fail    "collision_gate POSITIVE control (car through SHOW_Wall)" \
  $B -b $V0/ctl_collide_pos.blend --factory-startup -P $R2/tools/collision_gate.py -- --out $V/ctl_collide_pos.json
expect pass    "collision_gate NEGATIVE control (car clear of everything)" \
  $B -b $V0/ctl_collide_neg.blend --factory-startup -P $R2/tools/collision_gate.py -- --out $V/ctl_collide_neg.json

expect vacuous "depth_probe on the world (no CAR: must REFUSE)" \
  $B -b $S --factory-startup -P $R2/tools/depth_probe.py -- --frames 1 --out $V/depth_v122.json
expect fail    "depth_probe POSITIVE control (wheel 200 mm INTO the deck)" \
  $B -b $V0/ctl_depth_pos.blend --factory-startup -P $R2/tools/depth_probe.py -- --frames 1 --out $V/ctl_depth_pos.json
expect pass    "depth_probe NEGATIVE control (wheel in CONTACT, 0.0 mm)" \
  $B -b $V0/ctl_depth_neg.blend --factory-startup -P $R2/tools/depth_probe.py -- --frames 1 --out $V/ctl_depth_neg.json

# THE FLOAT BOUND NEEDS ITS OWN POSITIVE CONTROL. ctl_depth_neg.blend spent a
# day floating the wheel 200 mm in the AIR, which made it a SECOND positive
# control while three batteries counted it as the negative one -- two controls
# that must fail and none that must pass. It has since been repaired to a
# genuine CONTACT case, and the float case is promoted here to the positive
# control it always was.
expect fail    "depth_probe FLOAT positive control (wheel 200 mm ABOVE deck)" \
  $B -b $V0/ctl_depth_float_pos.blend --factory-startup -P $R2/tools/depth_probe.py -- --frames 1 --out $V/ctl_depth_float_pos.json

# ------------------------------------------- module-boundary triangle sweep -
run "probeD  module-boundary BVH" $B -b -noaudio $S --factory-startup -P $D/probeD.py -- --out $V/probeD_v122.json
run "probeG  the pairs D found, measured" $B -b -noaudio $S --factory-startup -P $D/probeG.py -- --out $V/probeG_v122.json

# ------------------------------------------------- ground-referenced road ---
run "probe_roadclear (ground-referenced corridor)" \
  $B -b -noaudio $S --factory-startup -P $V0/probe_roadclear.py -- $V/roadclear_v122.json

# --------------------------------------------------- the 9 original probes --
run "probeC  P1 P2 P3 P9" $B -b -noaudio $S --factory-startup -P $D/probeC.py -- --out $V/probeC_v122.json
run "probeB  P5 P6 P7 P8 + D2 D3" $B -b -noaudio $S --factory-startup -P $D/probeB.py -- --out $V/probeB_v122.json
run "probeE  P4 barrier feet" $B -b -noaudio $S --factory-startup -P $D/probeE.py -- --out $V/probeE_v122.json
run "probeA  D1 D4 D5 P4" $B -b -noaudio $S --factory-startup -P $D/probeA.py -- --out $V/probeA_v122.json

# ------------------------------------------------------------- variety -----
run "instance_variety (shipped)" \
  $B -b $S --factory-startup -P $R2/tools/instance_variety.py -- --out $V/instance_variety_v122.json
expect fail    "instance_variety POSITIVE control (1 mesh, 500 instances)" \
  $B -b $V0/ctl_variety_pos.blend --factory-startup -P $R2/tools/instance_variety.py -- --out $V/ctl_variety_pos.json
expect pass    "instance_variety NEGATIVE control (500 meshes, 500 inst)" \
  $B -b $V0/ctl_variety_neg.blend --factory-startup -P $R2/tools/instance_variety.py -- --out $V/ctl_variety_neg.json
run "variety_distribution (per-family sources)" \
  $B -b $S --factory-startup -P $V0/variety_distribution.py -- $V/variety_distribution_v122.json
run "mesh_reuse" $B -b $S --factory-startup -P $R2/tools/mesh_reuse.py

# ------------------------------------------------------- #47 / #48 / #50 ---
run "probe_pitexit on the rebuild" \
  $B -b $S --factory-startup -P $D/probe_pitexit.py -- $V/pitexit_v122.json

echo; echo "########## BATTERY DONE $(date +%T)"
# 0 all clean, 1 real findings, 2 an instrument misbehaved and
# nothing in this run is evidence.
battery_summary
exit $?
