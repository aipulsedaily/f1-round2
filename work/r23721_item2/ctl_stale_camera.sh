#!/bin/bash
# R2-3721 item 2: NEGATIVE CONTROL on the camera guard added to
# tools/screen_presence.py. A guard that has only ever been run on a good input
# has not been tested, and a guard that cannot fire is the defect it was written
# to prevent wearing the fix's name.
#
#   ARM N1  --path world/camera_rig_path.json  (the ACTUAL R2-1007 orphan, on
#           disk, right now)                        -> MUST REFUSE, non-zero,
#                                                      BEFORE reading points
#   ARM N2  the same file with --why-stale ''       -> MUST REFUSE (an empty
#                                                      reason is not a reason)
#   ARM P1  the same file with a real --why-stale   -> MUST RUN, and must record
#                                                      camera_is_known_stale
#   ARM P2  no --path at all                        -> MUST resolve the LIVE
#                                                      camera from
#                                                      docs/LIVE-CAMERA.md
#   ARM D   DISCRIMINATION: the refusal must be about the BYTES, not the name.
#           The same orphan bytes copied to an innocent filename must still
#           refuse -- otherwise N1 proves only that a filename was blacklisted,
#           which is the check that already failed once (R2-1007's file was
#           sitting under the most innocent name in the tree).
#
# Nothing under $HOME/f1-round2 is written; --out and --npz go to scratch.
set -u
R2=$HOME/f1-round2
SCR=${SCR:-$R2/work/r23721_item2}
T=${T:-$(mktemp -d /tmp/sp_camera_ctl.XXXXXX)}
rm -rf "$T"; mkdir -p "$T"
cd "$R2" || exit 1
PTS=work/w2_0/retier_a9/world_points.npz
PASS=0; FAIL=0

run() {  # logfile args...
  local log="$1"; shift
  python3 tools/screen_presence.py --points "$PTS" --stride 4000 \
    --uniform-shutter --out "$T/out.json" --npz "$T/out.npz" "$@" \
    > "$log" 2>&1
  echo $?
}

chk() {  # name expect_rc expect_text log actual_rc
  local name="$1" erc="$2" etxt="$3" log="$4" arc="$5" ok=1
  [ "$arc" = "$erc" ] || ok=0
  grep -q -- "$etxt" "$log" || ok=0
  if [ $ok = 1 ]; then
    printf '  %-56s ok    rc=%s, says %s\n' "$name" "$arc" "$etxt"; PASS=$((PASS+1))
  else
    printf '  %-56s FAIL  rc=%s (wanted %s); %s %s\n' "$name" "$arc" "$erc" \
      "$(grep -q -- "$etxt" "$log" && echo says || echo 'did NOT mention')" "$etxt"
    sed -n '1,8p' "$log" | sed 's/^/        | /'
    FAIL=$((FAIL+1))
  fi
}

echo ">> SELFTEST screen_presence camera guard (R2-3721 item 2 / defect #159)"

rm -f "$T/out.json" "$T/out.npz"
RC=$(run "$T/n1.log" --path world/camera_rig_path.json)
chk "MUST FAIL: the real R2-1007 orphan, no reason given" 1 "KNOWN-STALE" "$T/n1.log" "$RC"
if [ -f "$T/out.json" ] || [ -f "$T/out.npz" ]; then
  printf '  %-56s FAIL  it refused but had already written output\n' \
    "  ...and it refused BEFORE reading points or measuring"; FAIL=$((FAIL+1))
else
  printf '  %-56s ok    no npz, no json\n' \
    "  ...and it refused BEFORE reading points or measuring"; PASS=$((PASS+1))
fi

RC=$(run "$T/n2.log" --path world/camera_rig_path.json --why-stale "   ")
chk "MUST FAIL: a whitespace-only --why-stale is not a reason" 1 "KNOWN-STALE" "$T/n2.log" "$RC"

# ARM N3: the OTHER generation of the same orphan -- the film13/film14 bytes,
# which are what docs/screen_presence*.json was actually swept from and what git
# HEAD still has in world/camera_rig_path.json. The film16 entry alone does not
# cover it, and a guard that catches only the generation somebody happened to
# write down is the R2-1007 filename check in a new costume.
RC=$(run "$T/n3.log" --path render/film14_path.json)
chk "MUST FAIL: the film13/film14 bytes the docs were swept from" 1 "defect #159" "$T/n3.log" "$RC"

# DISCRIMINATION: same bytes, innocent name.
cp world/camera_rig_path.json "$T/render_film99_path.json"
RC=$(run "$T/d.log" --path "$T/render_film99_path.json")
chk "MUST FAIL: the same bytes under an innocent filename" 1 "KNOWN-STALE" "$T/d.log" "$RC"

rm -f "$T/out.json" "$T/out.npz"
RC=$(run "$T/p1.log" --path world/camera_rig_path.json \
     --why-stale "R2-3721 item 2 control: the deliberate stale read must work")
chk "POSITIVE: a stated reason lets the stale sweep run" 0 "DELIBERATE stale-camera sweep" "$T/p1.log" "$RC"
python3 - "$T/out.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
ok = (d.get("camera_is_known_stale") is True
      and len(d.get("camera_path_sha256") or "") == 64
      and d.get("why_stale"))
print("  %-56s %s  sha=%s stale=%s"
      % ("  ...and the OUTPUT records that it was stale", "ok  " if ok else "FAIL",
         (d.get("camera_path_sha256") or "")[:16], d.get("camera_is_known_stale")))
sys.exit(0 if ok else 1)
PY
if [ $? = 0 ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

rm -f "$T/out.json" "$T/out.npz"
RC=$(run "$T/p2.log")
DECL=$(python3 -c "import sys;sys.path.insert(0,'tools');import live_campath as L;print(L.declared_campath())")
chk "POSITIVE: no --path resolves docs/LIVE-CAMERA.md" 0 "docs/LIVE-CAMERA.md declares" "$T/p2.log" "$RC"
if python3 -c "
import json,sys
d=json.load(open('$T/out.json'))
sys.exit(0 if d['camera_path']=='$DECL' and d['camera_is_known_stale'] is False else 1)"; then
  printf '  %-56s ok    %s\n' "  ...and it swept exactly that file" "$(basename "$DECL")"; PASS=$((PASS+1))
else
  printf '  %-56s FAIL\n' "  ...and it swept exactly that file"; FAIL=$((FAIL+1))
fi

echo
echo ">> STAGE RESULT: $([ $FAIL = 0 ] && echo SP_CAMERA_GUARD_OK || echo SP_CAMERA_GUARD_FAIL)  ${PASS} passed, ${FAIL} failed"
[ $FAIL = 0 ]
