#!/usr/bin/env bash
# THE §21-DELETION GATE BATTERY, run on assembly6 (build_barriers §21 deleted,
# world_contract 1.2.1 prose-only).  This is v120/battery.sh re-pointed, and
# nothing in it is rewritten: the same gates, the same nine probes, the same
# controls, the same module-boundary sweep.
#
# WHAT IS NEW HERE, AND IT IS THE POINT OF THE TASK:
#   the FIRST thing this runs is a per-object VERTEX FINGERPRINT of assembly5 and
#   assembly6 and a diff of the two.  #53's rebuild compared SUMMARIES, found them
#   bit-identical, and concluded no geometry moved.  Counts and totals do not move
#   when vertices do.  Compare the vertices.
#
# Serial on purpose: one 4 GB scene at a time on an 11 GB box.
#
# EXIT CODES AND CONTROLS                                          (R2, 2026-08-03)
# ------------------------------------------------------------------------------
# Until today every gate in this battery exited 0 whatever it found, so `run ()`
# printed `exit=0` for a report that said PLACEMENT_FAIL and the battery had no
# way to know. The gates now return 0/1/2/3 (see tools/gate_exit.py) and the
# runner lives in ../lib_battery.sh -- ONE copy, shared with the other version's
# battery, because a private copy of shared behaviour is what defeated the
# socket guard (R2-057).
#
# WHAT IS *NOT* GUARDED, STATED BECAUSE THIS HEADER USED TO CLAIM IT WAS.
# The four gates (placement, collision, depth, variety) and probeA..probeK do
# return real statuses. FOUR OF THIS BATTERY'S OWN `-P` STEPS DO NOT:
# v120/vertex_fingerprint.py, v120/variety_distribution.py, tools/mesh_reuse.py
# and probe_pitexit.py have no gate_exit wrapper, so an uncaught exception in
# any of them is Blender's exit 0 and `run ()` scores it `ok`. Checked with
# /usr/bin/grep on 2026-08-03: zero occurrences of gate_exit in all four.
# Read their output, do not trust their status. `fp_diff.py` WAS in that list
# and is not any more -- it now declares and checks its expectation.
#
#   run    ...   a MEASUREMENT. Records the verdict and CARRIES ON: this is a
#                survey over a 4 GB scene and stopping at the first finding
#                would hide the rest. The battery still exits non-zero at the
#                end if anything came back non-clean.
#   expect ...   a CONTROL, with what it must do written next to it. A positive
#                control that does not FAIL, or a negative control that does not
#                PASS, HALTS the run -- every measurement after a dead
#                instrument is worthless. `--keep-going` surveys on anyway.
#
# `expect` exists because of `ctl_depth_neg.blend`: it put the wheel 200 mm in
# the AIR, so this battery had two positive depth controls and none that had to
# pass, and nothing noticed for a day. Now each control declares its job.
#
# PROBE OUTPUTS ARE PER-VERSION. probeA..probeK wrote hardcoded filenames into
# the assembly root, so this battery overwrote the probeD.json / probeG.json
# that the other version's collect.py reads. Every probe is now given an
# explicit --out under this version's own directory.
set -u
B=/opt/blender-5.2.0-linux-x64/blender
R2=/home/zany/f1-round2
D=$R2/render/world/assembly/r2
V0=$D/v120
V=$D/v121
OLD=$D/assembly5.blend
S=$D/assembly6.blend

echo "########## BATTERY START $(date +%T)"
ls -l $OLD $S
echo "--- instrument versions ---"
md5sum $R2/tools/placement_gate.py $R2/tools/depth_probe.py \
       $R2/tools/collision_gate.py $R2/tools/instance_variety.py \
       $R2/world/build_barriers.py $R2/world/world_contract.py

source "$D/lib_battery.sh"

# ------------------------------------------------- VERTEX-LEVEL COMPARISON --
run "vertex fingerprint assembly5 (the shipping world)" \
  $B -b -noaudio $OLD --factory-startup -P $V0/vertex_fingerprint.py -- $V/fp_assembly5.json
run "vertex fingerprint assembly6 (the rebuild)" \
  $B -b -noaudio $S --factory-startup -P $V0/vertex_fingerprint.py -- $V/fp_assembly6.json
# assembly5 -> assembly6 is the rebuild whose module summaries were BIT-IDENTICAL
# while BR_Transit_NorthWall moved 3.19 m. Exactly one object moved, and saying so
# here turns this step from a printout into a check -- it is also the positive
# control fp_diff.py's own repair was validated against.
expect pass "fp_diff  assembly5 -> assembly6   (EXPECT: exactly 1 object moved)" \
  python3 $V0/fp_diff.py $V/fp_assembly5.json $V/fp_assembly6.json --expect-moved 1

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
     --out $V/placement_v121.json
run "placement_gate (+ barrier ground objects)" \
  $B -b $S --factory-startup -P $R2/tools/placement_gate.py -- \
     --out $V/placement_v121_ground.json \
     --allow "SURF_,TER_Ground,BR_Runoff,BR_Gravel,BR_Subbase,BR_Trap,BR_Stone,BR_Verge,ARCH_Paving,ARCH_Markings,Floor,Turntable_,Platform_"

expect vacuous "collision_gate on the world (no CAR: must REFUSE)" \
  $B -b $S --factory-startup -P $R2/tools/collision_gate.py -- --out $V/collision_v121.json
expect fail    "collision_gate POSITIVE control (car through SHOW_Wall)" \
  $B -b $V0/ctl_collide_pos.blend --factory-startup -P $R2/tools/collision_gate.py -- --out $V/ctl_collide_pos.json
expect pass    "collision_gate NEGATIVE control (car clear of everything)" \
  $B -b $V0/ctl_collide_neg.blend --factory-startup -P $R2/tools/collision_gate.py -- --out $V/ctl_collide_neg.json

expect vacuous "depth_probe on the world (no CAR: must REFUSE)" \
  $B -b $S --factory-startup -P $R2/tools/depth_probe.py -- --frames 1 --out $V/depth_v121.json
expect fail    "depth_probe POSITIVE control (wheel 200 mm INTO the deck)" \
  $B -b $V0/ctl_depth_pos.blend --factory-startup -P $R2/tools/depth_probe.py -- --frames 1 --out $V/ctl_depth_pos.json
expect pass    "depth_probe NEGATIVE control (wheel in CONTACT, 0.0 mm)" \
  $B -b $V0/ctl_depth_neg.blend --factory-startup -P $R2/tools/depth_probe.py -- --frames 1 --out $V/ctl_depth_neg.json

# THE FLOAT BOUND NEEDS ITS OWN POSITIVE CONTROL.
#
# depth_probe fails BOTH ways -- PENETRATION (wheel in the deck) and FLOATING
# (wheel above it) -- and until 2026-08-03 only penetration had a control.
# ctl_depth_neg.blend was in fact floating the wheel 200 mm in the AIR, so this
# battery ran TWO positive controls and none that had to pass, and said nothing.
# ctl_depth_neg.blend has since been repaired to a genuine CONTACT case (0.0 mm,
# 8 vertices measured -- it passes because it measured something and it was
# clean, not because it measured nothing), and the float case is promoted here
# to the positive control it always was.
expect fail    "depth_probe FLOAT positive control (wheel 200 mm ABOVE deck)" \
  $B -b $V0/ctl_depth_float_pos.blend --factory-startup -P $R2/tools/depth_probe.py -- --frames 1 --out $V/ctl_depth_float_pos.json

# ------------------------------------------- module-boundary triangle sweep -
run "probeD  module-boundary BVH" $B -b -noaudio $S --factory-startup -P $D/probeD.py -- --out $V/probeD_v121.json
run "probeG  the pairs D found, measured" $B -b -noaudio $S --factory-startup -P $D/probeG.py -- --out $V/probeG_v121.json

# ------------------------------------------------- ground-referenced road ---
run "probe_roadclear (ground-referenced corridor)" \
  $B -b -noaudio $S --factory-startup -P $V0/probe_roadclear.py -- $V/roadclear_v121.json

# --------------------------------------------------- the 9 original probes --
run "probeC  P1 P2 P3 P9" $B -b -noaudio $S --factory-startup -P $D/probeC.py -- --out $V/probeC_v121.json
run "probeB  P5 P6 P7 P8 + D2 D3" $B -b -noaudio $S --factory-startup -P $D/probeB.py -- --out $V/probeB_v121.json
run "probeE  P4 barrier feet" $B -b -noaudio $S --factory-startup -P $D/probeE.py -- --out $V/probeE_v121.json
run "probeA  D1 D4 D5 P4" $B -b -noaudio $S --factory-startup -P $D/probeA.py -- --out $V/probeA_v121.json

# ------------------------------------------------------------- variety -----
run "instance_variety (shipped)" \
  $B -b $S --factory-startup -P $R2/tools/instance_variety.py -- --out $V/instance_variety_v121.json
expect fail    "instance_variety POSITIVE control (1 mesh, 500 instances)" \
  $B -b $V0/ctl_variety_pos.blend --factory-startup -P $R2/tools/instance_variety.py -- --out $V/ctl_variety_pos.json
expect pass    "instance_variety NEGATIVE control (500 meshes, 500 inst)" \
  $B -b $V0/ctl_variety_neg.blend --factory-startup -P $R2/tools/instance_variety.py -- --out $V/ctl_variety_neg.json
run "variety_distribution (per-family sources)" \
  $B -b $S --factory-startup -P $V0/variety_distribution.py -- $V/variety_distribution_v121.json
run "mesh_reuse" $B -b $S --factory-startup -P $R2/tools/mesh_reuse.py

# ------------------------------------------------------- #47 / #48 / #50 ---
run "probe_pitexit on the rebuild" \
  $B -b $S --factory-startup -P $D/probe_pitexit.py -- $V/pitexit_v121.json

echo; echo "########## BATTERY DONE $(date +%T)"
# The battery's own exit status: 0 all clean, 1 real findings,
# 2 an instrument misbehaved and nothing here is evidence.
battery_summary
exit $?
