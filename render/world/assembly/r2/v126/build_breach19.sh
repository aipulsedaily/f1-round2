#!/bin/bash
# film19_breach = the breach applied to film19, WITH THE FINES.  R2-1701.
#
# ORDERING CONSTRAINT 5, and it is the expensive one to get wrong:
# DO NOT run sim/land_breach.sh end to end.  Its stage 1 regenerates
# `sim/out/breach_film.npz` from whatever raw bake happens to be sitting in
# sim/tmp/, which can silently swap in a table where BF_MUL05_S02 travels
# 55.35 m instead of 0.1449 m.  So the applier is invoked directly with an
# EXPLICIT --film, and the guard is checked in the output below.
#
# THE FINES LAND HERE, NOT IN build_film_scene.  `--fines-lib` appends
# world/breach_fines.blend (101.9 MB, 11,246 objects) inside the pass that is
# already opening the film, so there is no second film-sized open anywhere in
# the pipeline, and the fines end up INSIDE the BREACH collection rather than as
# a sibling a later tool would have to know about.  film18 shipped without them:
# its report reads `"fines": {"skipped": true, "why": "neither --fines-lib nor
# --debris given"}` and its BREACH_Fines collection is present and EMPTY.
#
# `--debris` is NOT passed: that flag is now only how the library is
# regenerated, and --debris with --fines-lib REFUSE together because doing both
# would put two copies of 260,000 chips in the wound.
#
# `--fracture-faces` is NOT passed: the frosted fracture faces are off by
# default and still a pending probe in docs/NEXT-REBUILD.md.  A material edit
# with no geometry, addable later without a rebuild.
#
# WHY --force, AND WHY IT IS NOT A SHRUG.  The `glazing_pocket_clear` preflight
# FAILS on every correctly-built film, including film18, and the reason is an
# ordering artefact in the check rather than a defect in the scene: it lists
# GW_Right_Transom_0/1/2 as intruders in the glazing pocket, and those are three
# of the SIX round-1 solids this same applier then deletes and replaces with its
# own east frame.  The preflight measures the scene before the applier has done
# the work that clears it, so it can never pass.  The remaining seven are on the
# SOUTH wall (GW_Front_*) and the side fins -- not the breach wall at all.
# The applier's own post-build census is the check that means something, and on
# film18 it read `R5_intruders_over_the_wound_after: []` with east_frame and
# east_wall both PASS.  That census is asserted below; if it ever reports an
# intruder over the wound this build must fail regardless of this flag.
set -u
cd /home/zany/f1-round2
W=work/r21701
B=/opt/blender-5.2.0-linux-x64/blender
IN=render/film19.blend
OUT=render/film19_breach.blend
NPZ=sim/out/breach_film.npz
mkdir -p $W

[ -s "$IN" ]  || { echo ">> STAGE RESULT: BREACH19_FAIL (no $IN)"; exit 2; }
[ -s "$NPZ" ] || { echo ">> STAGE RESULT: BREACH19_FAIL (no $NPZ)"; exit 2; }
[ -s world/breach_fines.blend ] || { echo ">> STAGE RESULT: BREACH19_FAIL (no fines lib)"; exit 2; }

{
  echo "=== INPUTS, hashed at $(date -Is) ==="
  sha256sum "$NPZ" world/breach_fines.blend sim/apply_breach.py sim/fracture.py
} > $W/inputs_breach19.txt 2>&1
cat $W/inputs_breach19.txt

waitmem () {
  for i in $(seq 1 960); do
    A=$(free -g | awk '/^Mem:/{print $7}')
    [ "$A" -ge 5 ] && { echo "[gate] ${A} GB available, starting $1"; return 0; }
    [ $((i % 10)) -eq 1 ] && echo "[gate] $1 waiting: ${A} GB available (need 5)"
    sleep 30
  done
  echo "[gate] TIMEOUT before $1"; return 1
}

waitmem apply_breach || exit 90
START=$(date +%s)
$B -b "$IN" --factory-startup -noaudio -P sim/apply_breach.py -- \
    --film "$NPZ" \
    --fines-lib world/breach_fines.blend \
    --force \
    --out "$OUT" \
    --report $W/apply_film19.json \
    > $W/breach19.log 2>&1
echo "exit=$?  seconds=$(( $(date +%s) - START ))   (exit status is NOT the evidence)"
grep -aE "east frame|fines|built [0-9]+ objects|census|Saved as|wrote render|preflight" $W/breach19.log | tail -30
ls -la "$OUT" 2>&1

# THE BAKE GUARD.  A wrong bake reads 55.35 m at MUL05_S02.  Note the namespace:
# the bake names them MUL05_S02 and apply_breach adds the BF_ prefix.
python3 - "$W/apply_film19.json" <<'PY'
import json, sys
try:
    r = json.load(open(sys.argv[1]))
except Exception as e:
    print(">> STAGE RESULT: BREACH19_FAIL (no report: %s)" % e); raise SystemExit(1)
tr = r["stats"]["frame"]["max_travel_m"]
s2 = tr.get("BF_MUL05_S02")
fines = r["stats"].get("fines", {})
print(">> BF_MUL05_S02 = %r  (want 0.1449)" % s2)
print(">> BF_MUL05_S00 = %r   BF_MUL05_S01 = %r  (want ~3.93 / ~4.74)"
      % (tr.get("BF_MUL05_S00"), tr.get("BF_MUL05_S01")))
print(">> fines: %s" % json.dumps(fines)[:300])
ok = True
if s2 is None or abs(s2 - 0.1449) > 5e-4:
    print(">> REFUSE: BF_MUL05_S02 is not 0.1449 m -- WRONG BAKE"); ok = False
if fines.get("skipped") or not fines.get("chips"):
    print(">> REFUSE: the fines did not land"); ok = False
# The census that --force does NOT excuse.  The preflight is coarse; this is the
# measurement of what the applier actually left over the wound.
ef = r.get("east_frame", {}); ew = r.get("east_wall", {})
over = ef.get("R5_intruders_over_the_wound_after")
print(">> east_frame PASS=%s  east_wall PASS=%s  intruders over the wound=%r"
      % (ef.get("PASS"), ew.get("PASS"), over))
if over:
    print(">> REFUSE: %d intruder(s) over the wound after the build" % len(over)); ok = False
if not ef.get("PASS") or not ew.get("PASS"):
    print(">> REFUSE: east frame/wall census did not pass"); ok = False
print(">> STAGE RESULT: %s" % ("BREACH19_BUILT" if ok else "BREACH19_FAIL"))
raise SystemExit(0 if ok else 1)
PY
