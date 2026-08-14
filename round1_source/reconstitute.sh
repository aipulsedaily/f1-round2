#!/bin/bash
# RECONSTITUTE ROUND 1'S SCENE FROM THE VENDORED SOURCE, WITHOUT ROUND 1.
#
#   bash round1_source/reconstitute.sh <out.blend> [workdir]
#
# This is the thing that makes `round1_source/` more than a backup: it proves,
# by running, that the vendored copy is SUFFICIENT.  Nothing it executes reads
# /home/zany/opus5-car-render -- the script asserts that, by grepping its own
# working tree for the string and refusing if it finds one.
#
# WHY A WORKING COPY AND NOT A DIRECT RUN.  `round1_source/build/` is a
# byte-faithful copy of round 1 (see PROVENANCE.md), and it stays that way so a
# future reader can diff it against the original while the original still
# exists.  Two absolute paths inside it point at round 1 and must be rewritten
# to run standalone, so the rewrite happens on a throwaway copy instead of on
# the vendored tree:
#
#   build/s01_base.py       PROJ = "/home/zany/opus5-car-render"
#   tools/rebuild_scene.py  sys.path.insert(0, ".../build")
#
# THE HDRI.  `s01_base.world_hdri()` calls `bpy.data.images.load()` on
# `$PROJ/assets/city.exr`, which RAISES if the file is absent -- so the build
# will not complete without something at that path.  Round 1's city.exr is a
# real photographic HDRI and the round-2 brief forbids downloaded stock, so it
# is NOT vendored.  An 8x4 px stub is GENERATED here instead, so no image file
# is committed to this repository at all.
#
# That is not a compromise, because the content never survives: every round-2
# build path saves through `tools/fix_audit_blend.save_clean()`, which replaces
# the world with a procedural Sky Texture and deletes every external FILE
# image, then refuses to save if one remains.  The HDRI has to EXIST for the
# round-1 build; it does not have to be anything.
set -eu

OUT="${1:?usage: reconstitute.sh <out.blend> [workdir]}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
R2="$(dirname "$HERE")"
WORK="${2:-$(mktemp -d "${TMPDIR:-/tmp}/r1recon.XXXXXX")}"
BLENDER=/opt/blender-5.2.0-linux-x64/blender
mkdir -p "$WORK"
WORK="$(cd "$WORK" && pwd)"

# THE WORK ROOT MUST BE OUTSIDE THE REPOSITORY, and the reason is a real one
# rather than tidiness.  `PROJ` becomes $WORK, so the HDRI stub is loaded from
# "$WORK/assets/city.exr" -- and `fix_audit_blend.save_clean()`, which every
# round-2 build path saves through, drops external images by asking whether
# they are outside f1-round2.  A work root INSIDE the repo makes the stub look
# like a project asset: it survives the drop, trips save_clean's refusal, and
# the whole car chain stops one line before it saves.  Measured, not reasoned:
# that is exactly what happened on the first run of this script (R2-4028).
case "$WORK/" in
  "$R2"/*) echo "REFUSING: workdir $WORK is inside $R2 -- see the comment above."; exit 2;;
esac

mkdir -p "$WORK/assets"
cp -a "$HERE/build" "$WORK/build"
mkdir -p "$WORK/tools"
cp -a "$HERE/tools/rebuild_scene.py" "$WORK/tools/rebuild_scene.py"

"$BLENDER" -b --factory-startup --python-expr "
import bpy
img = bpy.data.images.new('stub', 8, 4, float_buffer=True)
img.pixels[:] = [0.05, 0.06, 0.08, 1.0] * 32
img.file_format = 'OPEN_EXR'
img.filepath_raw = '$WORK/assets/city.exr'
img.save()
" >/dev/null 2>&1
[ -s "$WORK/assets/city.exr" ] || { echo "REFUSING: HDRI stub was not generated"; exit 1; }

sed -i "s#/home/zany/opus5-car-render#$WORK#g" \
    "$WORK/build/s01_base.py" "$WORK/tools/rebuild_scene.py"
# The scratch part modules (underscore-prefixed, never assembled) also carry the
# old root; rewrite them too so the assertion below can be absolute.
grep -rl "/home/zany/opus5-car-render" "$WORK" 2>/dev/null \
    | while read -r f; do sed -i "s#/home/zany/opus5-car-render#$WORK#g" "$f"; done

if grep -rq "opus5-car-render" "$WORK"; then
    echo "REFUSING: the working tree still references round 1:"
    grep -rn "opus5-car-render" "$WORK" | head
    exit 1
fi
echo ">> working tree at $WORK has ZERO references to round 1"

PYTHONDONTWRITEBYTECODE=1 "$BLENDER" -b --factory-startup \
    -P "$WORK/tools/rebuild_scene.py" -- --out "$OUT"

echo ">> reconstituted $OUT ($(stat -c%s "$OUT") bytes) from vendored source alone"
echo ">> STAGE RESULT: R1_RECONSTITUTED"
