#!/bin/bash
# film25_breach = the breach applied to film25, WITH THE FINES.  R2-3661.
#
# v128/build_breach24.sh with W -> work/r23661 and the film24 literals renamed.
# NOTHING ELSE CHANGES, and in particular:
#
# THE 10.9 GB BAKE IS NOT REDONE AND MUST NOT BE.  `sim/breachlib.py` reads the
# car only for beat 3 (f865-1056); the driver-car this film appends is the SAME
# artefact film24 appended (`world/R2_3361_car_anim_driver_CS.blend`), and
# R2-3363's confinement table measures its `3_breach` row at 0.000000e+00 on
# every channel across those 192 frames.  The world underneath changed --
# assembly14 -> assembly15 -- and the world is not an input to the bake either:
# `sim/out/breach_film.npz` is a table of per-segment rigid-body transforms for
# the east frame, baked once on 2026-08-04 and re-used by every film since.
# It is re-used unchanged here, and its sha is recorded before the run.
#
# ORDERING CONSTRAINT 5, restated because it is the one that bites:
#   DO NOT run sim/land_breach.sh end to end.  Its stage 1 REGENERATES
#   breach_film.npz from whatever raw bake sits in sim/tmp/, which can silently
#   swap in a table where MUL05_S02 travels 55.35 m instead of 0.1449 m.  The
#   applier is invoked directly, with an EXPLICIT --film.
#
# WHY --force, AND WHY IT IS NOT A SHRUG.  `glazing_pocket_clear` FAILS on every
# correctly-built film: it lists GW_Right_Transom_0/1/2 as intruders in the
# glazing pocket, and those are three of the round-1 solids THIS SAME APPLIER
# then deletes and replaces with its own east frame.  The preflight measures the
# scene before the applier has done the work that clears it, so it can never
# pass.  The check that means something is the applier's POST-BUILD CENSUS, and
# it is asserted below REGARDLESS of --force: if
# `R5_intruders_over_the_wound_after` is ever non-empty, or either census fails,
# this build fails and the flag excuses nothing else.
#
# `--debris` is NOT passed: it is now only how the library is regenerated, and
# --debris with --fines-lib REFUSE together because doing both puts two copies
# of 260,000 chips in the wound.
# `--fracture-faces` is NOT passed: off by default, still a pending probe.
set -u
cd /home/zany/f1-round2
W=work/r23661
B=/opt/blender-5.2.0-linux-x64/blender
IN=${1:-render/film25.blend}
OUT=${2:-render/film25_breach.blend}
NPZ=sim/out/breach_film.npz
mkdir -p $W

[ -s "$IN" ]  || { echo ">> STAGE RESULT: BREACH25_FAIL (no $IN)"; exit 2; }
[ -s "$NPZ" ] || { echo ">> STAGE RESULT: BREACH25_FAIL (no $NPZ)"; exit 2; }
[ -s world/breach_fines.blend ] || {
  echo ">> STAGE RESULT: BREACH25_FAIL (no fines lib)"; exit 2; }

# THE BAKE IS RE-USED, SO ITS IDENTITY IS RECORDED RATHER THAN ASSUMED.
# film24 hashed it at 3e312977987ac57a...; a difference here means somebody
# re-baked between the two films and the guard below is the only thing that
# would catch it.
{
  echo "=== INPUTS, hashed at $(date -Is) ==="
  sha256sum "$NPZ" world/breach_fines.blend sim/apply_breach.py sim/fracture.py
} > $W/inputs_breach25.txt 2>&1
cat $W/inputs_breach25.txt
NPZSHA=$(sha256sum "$NPZ" | cut -c1-16)
echo ">> bake sha16 = $NPZSHA   (film24 built on 3e312977987ac57a)"
[ "$NPZSHA" = "3e312977987ac57a" ] || {
  echo ">> WARNING: the bake is NOT the one film24 used.  Not fatal by itself"
  echo "   -- the BF_MUL05_S02 guard below is the decisive test -- but it is"
  echo "   recorded here so a silent re-bake cannot pass unremarked."; }

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
    --report $W/apply_film25.json \
    > $W/breach25.log 2>&1
echo "exit=$?  seconds=$(( $(date +%s) - START ))   (exit status is NOT the evidence)"
grep -aE "east frame|fines|built [0-9]+ objects|census|Saved as|wrote render|preflight|Traceback|Error" \
    $W/breach25.log | tail -30
ls -la "$OUT" 2>&1

python3 - "$W/apply_film25.json" <<'PY'
import json, sys
try:
    r = json.load(open(sys.argv[1]))
except Exception as e:
    print(">> STAGE RESULT: BREACH25_FAIL (no report: %s)" % e); raise SystemExit(1)
ok = True
st = r["stats"]

# --- THE BAKE GUARD.  A wrong bake reads 55.35 m at MUL05_S02.  Note the
# --- namespace: the bake names them MUL05_S02, apply_breach adds the BF_.
tr = st["frame"]["max_travel_m"]
s2 = tr.get("BF_MUL05_S02")
print(">> BF_MUL05_S02 = %r  (want 0.1449, as film24 read)" % s2)
print(">> BF_MUL05_S00 = %r   BF_MUL05_S01 = %r  (want ~3.93 / ~4.74)"
      % (tr.get("BF_MUL05_S00"), tr.get("BF_MUL05_S01")))
if s2 is None or abs(s2 - 0.1449) > 5e-4:
    print(">> REFUSE: BF_MUL05_S02 is not 0.1449 m -- WRONG BAKE"); ok = False
# S00 and S01 are the two segments that DO leave; if they were also ~0 the
# whole east frame stood up and the guard above would be vacuous.
for nm, want in (("BF_MUL05_S00", 3.93), ("BF_MUL05_S01", 4.74)):
    v = tr.get(nm)
    if v is None or abs(v - want) > 0.25:
        print(">> REFUSE: %s travels %r, not ~%.2f m -- the segments that are "
              "supposed to leave did not" % (nm, v, want)); ok = False

# --- THE FINES.  Measured off the appended datablocks, never quoted from the
# --- library's own report (R2-517).  `chips` is deliberately NOT asserted: it
# --- is not readable after the append.
f = st.get("fines", {})
print(">> fines: %s" % json.dumps(f)[:400])
if f.get("skipped"):
    print(">> REFUSE: the fines did not land (%s)" % f.get("why")); ok = False
else:
    for k, want in (("appended", True), ("puffs", 11246), ("animated", 11246),
                    ("tris", 4679872)):
        got = f.get(k)
        good = (got == want)
        print(">>   fines.%-9s want %-9s got %-9s %s"
              % (k, want, got, "OK" if good else "REFUSE"))
        if not good:
            ok = False

# --- THE CENSUS THAT --force DOES NOT EXCUSE.
ef = r.get("east_frame", {}); ew = r.get("east_wall", {})
over = ef.get("R5_intruders_over_the_wound_after")
print(">> east_frame PASS=%s  east_wall PASS=%s  intruders over the wound=%r"
      % (ef.get("PASS"), ew.get("PASS"), over))
if over:
    print(">> REFUSE: %d intruder(s) over the wound after the build" % len(over))
    ok = False
if not ef.get("PASS") or not ew.get("PASS"):
    print(">> REFUSE: east frame/wall census did not pass"); ok = False

print(">> STAGE RESULT: %s" % ("BREACH25_BUILT" if ok else "BREACH25_FAIL"))
raise SystemExit(0 if ok else 1)
PY
