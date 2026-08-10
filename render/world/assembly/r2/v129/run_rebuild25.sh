#!/bin/bash
# film25 -- THE FIRST FILM ON assembly15, i.e. THE FIRST WITH THE GROUND COVER.
# R2-3661.
#
# `render/film23_breach.blend` AND `render/film24_breach.blend` ARE NOT TOUCHED
# BY THIS SCRIPT AND MUST NOT BE.  Both carry verdicts (film24: FILM_BAR_PASS
# 40/40 with the film10 negative control still failing) that must stay
# measurable on the files they were measured on.  Every output name here is
# film25 and every work path is `work/r23661`, so `work/r22101` and
# `work/r23361` are immutable from here.  Both shas are taken before the run
# and re-taken at the end; a difference FAILS the build.
#
# WHAT IS DIFFERENT FROM film24, AND IT IS EXACTLY ONE THING
# -----------------------------------------------------------
#   THE WORLD.  film24 was built on `assembly14.blend`; this is built on
#   `assembly15.blend`.  assembly15 is assembly14's object graph TO THE OBJECT
#   -- 31,068 objects, 4,247 meshes, 181 materials, every prefix identical
#   (DR 247, ARCH 31, BR 131, CFP 676, CRF 120, SPECX 900, SURF 58, TER 1,
#   TS 10, VEG 28,894) -- PLUS the ground cover, at +17.16 % traced triangles.
#
#   The car is the SAME artefact film24 appended
#   (`world/R2_3361_car_anim_driver_CS.blend`, 408,590,498 bytes) and the sheet
#   is the SAME `docs/beat_sheet.json` at `1abee787a8044f35`.  So the camera
#   path should come out at film24's sha, and it is CHECKED rather than
#   assumed: an unexpected difference would mean the rig read something else.
#
# THE WORLD OVERRIDE, AND WHY IT IS NOT THE ONE film24 USED
# ---------------------------------------------------------
# film24's override said "assembly14 is STALE against its own source and I am
# building on it anyway".  That was a real, open debt.  THIS BUILD CLOSES IT:
# assembly15's recorded fingerprint matches the worktree over all 94 files
# (0 differ), so the world this film is built on IS what its source produces.
# The override here is only that `SHIPPING.md` still names assembly14 -- a
# declaration this script deliberately does NOT rewrite, because that file is
# leased by another agent.  Promoting the declaration is a separate landing.
#
# Five stages, each judged only on its printed `>> STAGE RESULT:` token --
# Blender 5.2 exits 0 on an uncaught exception, so `$?` is not evidence -- and
# every stage checked for the two-verdict trap.
set -u
cd /home/zany/f1-round2
W=work/r23661
V7=render/world/assembly/r2/v127
V9=render/world/assembly/r2/v129
CAR=world/R2_3361_car_anim_driver_CS.blend
ASM=render/world/assembly/r2/assembly15.blend
SHEET=docs/beat_sheet.json
B=/opt/blender-5.2.0-linux-x64/blender
mkdir -p $W
exec > >(tee -a $W/REBUILD25.log) 2>&1
echo "######################## R2-3661 film25 $(date -Is)"

[ -s "$ASM" ] || { echo ">> STAGE RESULT: REBUILD25_FAIL (no assembly15)"; exit 10; }
[ -s "$CAR" ] || { echo ">> STAGE RESULT: REBUILD25_FAIL (no $CAR)"; exit 10; }

# THE TWO SHIP CANDIDATES MUST NOT BE OVERWRITTEN, AND THAT IS MEASURED, NOT
# ASKED.  A promise not to write a file is not evidence.
BEFORE23=$(sha256sum render/film23_breach.blend 2>/dev/null | cut -c1-16)
BEFORE24=$(sha256sum render/film24_breach.blend 2>/dev/null | cut -c1-16)
echo ">> film23_breach.blend sha16 BEFORE: ${BEFORE23:-absent}"
echo ">> film24_breach.blend sha16 BEFORE: ${BEFORE24:-absent}"
[ -n "$BEFORE23" ] && [ -n "$BEFORE24" ] || {
  echo ">> STAGE RESULT: REBUILD25_FAIL (a baseline this build promises not to touch is absent)"
  exit 10; }

echo; echo "######## 0/5  the world: assembly15's own build verdict and fingerprint"
# assembly14's acceptance was a grep for ASSEMBLY14_FIXES_PRESENT in a stdout
# file.  assembly15's equivalent evidence is its OWN sidecar, which records a
# per-module ok flag -- and that is the flag that was FALSE for `dressing` in
# the build that silently lost 247 objects.  Assert all seven, not the summary.
python3 - <<'PY'
import json, hashlib, os, sys
R2 = "/home/zany/f1-round2"
d = json.load(open(os.path.join(
    R2, "render/world/assembly/r2/assembly15_build.json")))
ok = True
want = ["surface", "barriers", "architecture", "terrain", "nearband",
        "dressing", "items"]
for m in want:
    v = d["mods"].get(m)
    if v is None:
        print(">> REFUSE: assembly15 has no %r stage" % m); ok = False; continue
    print("   %-14s ok=%-5s %7.1fs  objects %d"
          % (m, v["ok"], v["s"], v["objects_total"]))
    if not v["ok"]:
        print(">> REFUSE: assembly15's %r stage FAILED -- the artefact exists "
              "but is missing what that stage builds" % m); ok = False
pref = d["object_prefixes"]
print("   totals: %d objects, %d meshes, %d materials"
      % (d["total_objects"], d["total_meshes"], d["total_materials"]))
print("   DR=%d ARCH=%d BR=%d CFP=%d CRF=%d SPECX=%d SURF=%d TER=%d TS=%d VEG=%d"
      % tuple(pref.get(k, 0) for k in
              ("DR", "ARCH", "BR", "CFP", "CRF", "SPECX", "SURF", "TER", "TS",
               "VEG")))
for k, n in (("DR", 247), ("ARCH", 31), ("BR", 131), ("CFP", 676), ("CRF", 120),
             ("SPECX", 900), ("SURF", 58), ("TER", 1), ("TS", 10),
             ("VEG", 28894)):
    if pref.get(k, 0) != n:
        print(">> REFUSE: prefix %s is %d, assembly14 had %d"
              % (k, pref.get(k, 0), n)); ok = False
if d["total_objects"] != 31068:
    print(">> REFUSE: %d objects, not 31,068" % d["total_objects"]); ok = False

# THE FINGERPRINT, AGAINST THE TREE AS IT STANDS NOW.
fp = d["source_sha256"]
diff = []
for rel, sha in sorted(fp.items()):
    p = os.path.join(R2, rel)
    cur = (hashlib.sha256(open(p, "rb").read()).hexdigest()
           if os.path.exists(p) else None)
    if cur != sha:
        diff.append(rel)
print("   fingerprint: %d file(s), %d differ from the worktree now"
      % (len(fp), len(diff)))
for r in diff[:10]:
    print("     DRIFTED  %s" % r)
if diff:
    print(">> REFUSE: the world is stale against its own source"); ok = False
print(">> STAGE RESULT: %s"
      % ("ASSEMBLY15_ACCEPTED" if ok else "ASSEMBLY15_REFUSED"))
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] || { echo ">> STAGE RESULT: REBUILD25_FAIL (assembly15 not accepted)"; exit 10; }

echo; echo "######## 0b/5  the car's keys, against anim/carrig"
# A date check cannot catch this defect -- R2-3308 proved it: `--check` on the
# shipped car fires and never names anim/carpath.py, because the blend is
# 19.4 h NEWER than the file whose motion it does not contain.  Read the KEYS.
$B -b "$CAR" --factory-startup -noaudio -P tools/car_staleness.py -- --keys \
   > $W/keys_film25_car.log 2>&1
grep -a "CAR KEYS\|STAGE RESULT" $W/keys_film25_car.log
grep -qa "STAGE RESULT: CAR_KEYS_MATCH_SOURCE" $W/keys_film25_car.log || {
  echo ">> STAGE RESULT: REBUILD25_FAIL (the car this film would append is STALE)"
  exit 11; }

SHA=$(python3 -c "import hashlib;print(hashlib.sha256(open('$SHEET','rb').read()).hexdigest()[:16])")
echo ">> $SHEET sha256[:16] = $SHA"
[ "$SHA" = "1abee787a8044f35" ] || {
  echo ">> STAGE RESULT: REBUILD25_FAIL (sheet is $SHA, not the live 1abee787a8044f35)"
  exit 11; }

# THE SOURCE FINGERPRINT for this film, v128's list unchanged.
{
  echo "=== SOURCE, hashed at $(date -Is) ==="
  sha256sum "$SHEET" telemetry/telemetry.csv docs/circuit_spec.json \
            anim/build_camera_rig.py anim/carpath.py anim/carrig.py \
            sim/apply_breach.py world/showroom_lighting.py world/showroom_strip.py \
            tools/build_film_scene.py tools/r2791_apply_focus.py \
            "$ASM" "$CAR" 2>&1
} > $W/inputs_film25.txt
cat $W/inputs_film25.txt

waitmem () {
  for i in $(seq 1 960); do
    A=$(free -g | awk '/^Mem:/{print $7}')
    [ "$A" -ge 5 ] && { echo "[gate] ${A} GB available, starting $1"; return 0; }
    [ $((i % 10)) -eq 1 ] && echo "[gate] $1 waiting: ${A} GB available (need 5)"
    sleep 30
  done
  echo "[gate] TIMEOUT before $1"; return 1
}

judge () {   # judge <log> <pass-token> <stage-name>
  local log="$1" tok="$2" name="$3"
  if ! grep -qa "$tok" "$log"; then
    echo ">> STAGE RESULT: REBUILD25_FAIL ($name: no '$tok' in $log)"; return 1
  fi
  local badline
  badline=$(grep -aE "STAGE RESULT: [A-Z0-9_]*(FAIL|UNSOUND|REFUS|STALE)" "$log" | head -3)
  if [ -n "$badline" ]; then
    echo ">> TWO-VERDICT TRAP: $name printed a failing verdict as well:"
    echo "$badline"
    echo ">> STAGE RESULT: REBUILD25_FAIL ($name: unread failing verdict)"; return 1
  fi
  return 0
}

OVERRIDE_REASON="R2-3661: film25 is film24's rig and film24's car on assembly15, which SUPERSEDES assembly14 (R2-3605..R2-3607: every prefix identical to the object, plus the ground cover at +17.16 % traced triangles, and every gate re-measured on both worlds). SHIPPING.md still names assembly14 and this script deliberately does NOT rewrite it, because render/world/assembly/r2/SHIPPING.md is held by another agent's lease and promoting the declaration is a separate landing. Unlike film24's override, this one does NOT carry a staleness debt: assembly15's recorded source fingerprint matches the worktree over all 94 files, 0 differ, asserted in stage 0/5 above."

echo; echo "######## 1/5  build_film_scene -> render/film25.blend"
waitmem film_scene || exit 90
bash tools/buildlock.sh r2-3661-film25-scene \
  $B -b "$ASM" --factory-startup -noaudio -P tools/build_film_scene.py -- \
    --out render/film25.blend --car "$CAR" --sheet "$SHEET" \
    --world-override "$OVERRIDE_REASON" > $W/build_film25.log 2>&1
echo "  rc=$?  (exit status is NOT the evidence)"
grep -aE "^>> |STAGE RESULT|REFUS|Traceback|WORLD STALENESS|showroom_strip" \
    $W/build_film25.log | tail -45
judge $W/build_film25.log ">> STAGE RESULT: FILM_SCENE_BUILT" "film25 scene" || exit 12
grep -qa "sky/camera bind CHECKED" $W/build_film25.log || {
  echo ">> STAGE RESULT: REBUILD25_FAIL (no sky rebind check)"; exit 13; }
grep -qa "showroom_strip: ADDED R2_Strip" $W/build_film25.log || {
  echo ">> STAGE RESULT: REBUILD25_FAIL (the strip source was not added)"
  grep -a "showroom_strip" $W/build_film25.log | tail -5; exit 13; }

# THE CAMERA PATH.  Same sheet + same car + same rig builder as film24, so this
# SHOULD come out at film24's sha.  It must NOT come out at film22/film23's
# 363e4e88b30207ad, which would mean the rig did not read the live sheet.
P25=$(sha256sum render/film25_path.json | cut -c1-16)
echo ">> render/film25_path.json sha16 = $P25"
echo ">>   film24's was 9d055d63da724993, film22/23's was 363e4e88b30207ad"
[ "$P25" = "363e4e88b30207ad" ] && {
  echo ">> STAGE RESULT: REBUILD25_FAIL (the camera path is film22/film23's -- the rig did not read the live sheet)"
  exit 13; }
if [ "$P25" = "9d055d63da724993" ]; then
  echo ">>   MATCHES film24 -- the rig is byte-identical, as it should be"
else
  echo ">>   DIFFERS from film24.  Not fatal, but it must be explained:"
  echo ">>   the sheet and the car are identical, so the only remaining input"
  echo ">>   is the world the rig samples.  Per-beat delta below."
fi
python3 - <<'PY'
import json, math, sys, os
sys.path.insert(0, "/home/zany/f1-round2/tools")
import lap_shotscale as LS
a = LS.load_path("/home/zany/f1-round2/render/film24_path.json")
b = LS.load_path("/home/zany/f1-round2/render/film25_path.json")
print(">> film25's camera vs film24's, per beat:")
moved = 0
for nm, lo, hi in LS.BEATS:
    w = max(math.dist(a[f]["p"], b[f]["p"]) for f in range(lo, hi + 1))
    l = max(abs(a[f]["lens"] - b[f]["lens"]) for f in range(lo, hi + 1))
    print("     %-12s d position %8.4f m   d lens %8.4f mm" % (nm, w, l))
    moved += (w > 0 or l > 0)
print(">> %d of 6 beats moved.  EXPECTED 0: film25 changes only the world, and "
      "the rig is built from the sheet." % moved)
PY

echo; echo "######## 1b/5  the car's keys, READ BACK OUT OF THE FILM"
# The stage-0b gate asked about the car ON DISK.  This asks about the CAR_ROOT
# that actually ended up INSIDE the artefact being shipped.  Those are different
# questions and only this one is about the film.  Never run before (R2-3301's
# wiring into build_film_scene was written up and never made).
$B -b render/film25.blend --factory-startup -noaudio -P $V9/film_car_keys.py \
   > $W/filmkeys_film25.log 2>&1
grep -a "CAR_ROOT\|CAR KEYS\|probe frames\|STAGE RESULT" $W/filmkeys_film25.log
grep -qa "STAGE RESULT: FILM_CAR_KEYS_MATCH_SOURCE" $W/filmkeys_film25.log || {
  echo ">> STAGE RESULT: REBUILD25_FAIL (the CAR_ROOT INSIDE film25 is not where anim/carrig puts it)"
  exit 13; }

echo; echo "######## 2/5  focus"
waitmem focus || exit 90
bash tools/buildlock.sh r2-3661-film25-focus \
  $B -b render/film25.blend --factory-startup -noaudio -P tools/r2791_apply_focus.py -- \
   --grid work/r2840/depthgrid_R2842.json --report $W/focus_report_film25.json \
   --out render/film25.blend > $W/apply_focus25.log 2>&1
grep -aE "^>> |STAGE RESULT" $W/apply_focus25.log | tail -14
judge $W/apply_focus25.log "STAGE RESULT R2791_APPLY_OK" "focus" || exit 14

echo; echo "######## 3/5  breach + fines"
# The bake is NOT redone: sim/breachlib.py reads the car only for beat 3
# (f865-1056), the car is film24's unchanged, and the world is not an input.
bash tools/buildlock.sh r2-3661-film25-breach \
  bash $V9/build_breach25.sh render/film25.blend render/film25_breach.blend
BRC=$?
[ $BRC -eq 0 ] || { echo ">> STAGE RESULT: REBUILD25_FAIL (breach rc=$BRC)"; exit 15; }

echo; echo "######## 4/5  verify"
bash $V9/verify_film25.sh render/film25_breach.blend
VRC=$?

echo
AFTER23=$(sha256sum render/film23_breach.blend 2>/dev/null | cut -c1-16)
AFTER24=$(sha256sum render/film24_breach.blend 2>/dev/null | cut -c1-16)
echo ">> film23_breach.blend sha16 AFTER: ${AFTER23:-absent}  (was ${BEFORE23:-absent})"
echo ">> film24_breach.blend sha16 AFTER: ${AFTER24:-absent}  (was ${BEFORE24:-absent})"
[ "$AFTER23" = "$BEFORE23" ] || { echo ">> STAGE RESULT: REBUILD25_FAIL (THIS RUN TOUCHED film23_breach.blend)"; exit 16; }
[ "$AFTER24" = "$BEFORE24" ] || { echo ">> STAGE RESULT: REBUILD25_FAIL (THIS RUN TOUCHED film24_breach.blend)"; exit 16; }
ls -la render/film25.blend render/film25_breach.blend \
       render/film24_breach.blend render/film23_breach.blend 2>&1
[ $VRC -eq 0 ] && echo ">> STAGE RESULT: REBUILD25_COMPLETE" \
               || echo ">> STAGE RESULT: REBUILD25_BUILT_BAR_NOT_MET"
