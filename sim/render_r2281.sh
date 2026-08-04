#!/bin/bash
# THE R2-281 RE-BAKE'S RENDER SET, AT EXACTLY THE R6 RUN'S SPECS.
#
#   bash sim/render_r2281.sh <new_applied.blend>
#
# Every job below is a byte-for-byte copy of the spec the R6 run used for the
# same frame, read out of the broker's own job table rather than retyped:
# same camera, same resolution, same samples, same depth of field, same crop
# rectangles and zoom factors.  That is the only reason the two sets can be
# differenced at all -- a 4K frame at 256 samples and a 4K frame at 400 differ
# on more pixels than this whole fix moves.
#
#   full   ONER 3840x2160 s256 dof-on            f2901 f2940 f2978
#   zoom   s400, the R6 run's own crop per frame f2901 (x15) f2940 (x11)
#                                                f2978 (x8)
#   beat3  ONER 1920x1080 s256                   f0866 f0880
#   beat1  ONER 1920x1080 s256                   f0400   (continuity control)
#
# AND TWO REPEATS, because the noise floor on a glass wall is not zero: the
# same build rendered twice differs on 2-14 % of these regions' pixels at
# 1/255, which is why the verdict is taken at 8/255.  One repeat of the R6
# build (the floor under the BEFORE image) and one of the new build (the floor
# under the AFTER image).
set -u
cd /home/zany/f1-round2
NEW="${1:-/home/zany/f1-round2/render/film14_breach_r6b.blend}"
OLD=/home/zany/f1-round2/render/film14_breach_r6.blend
RQ=/home/zany/vast-render/rq
A=r2281
D=render/r2281
mkdir -p $D

NEW=$(realpath "$NEW"); OLD=$(realpath "$OLD")   # the broker resolves a RELATIVE name against ITS scene roots, not your cwd
[ -f "$NEW" ] || { echo "STAGE RESULT: FAIL -- no $NEW"; exit 1; }
[ -f "$OLD" ] || { echo "STAGE RESULT: FAIL -- no $OLD"; exit 1; }

sub () {   # sub <scene> <out.png> <extra rq args...>
  scene="$1"; out="$2"; shift 2
  if [ -f "$out" ]; then echo "have $out"; return 0; fi
  echo "--- $out"
  $RQ render --agent $A --scene "$scene" --cam ONER --dof on \
      --adaptive-threshold 0.01 --prio 90 --timeout 0 "$@" -o "$out" \
      2>&1 | tail -3
}

# ---- the new build ------------------------------------------------------- #
for f in 2978 2940 2901; do
  sub "$NEW" $D/new_full_f0$f.png --res 3840 2160 --samples 256 --frame $f
done
sub "$NEW" $D/new_zoom_f2978.png --res 3840 2160 --samples 400 --frame 2978 \
    --zoom 8.0  --border 0.46804 0.53199 0.47659 0.52345
sub "$NEW" $D/new_zoom_f2940.png --res 3840 2160 --samples 400 --frame 2940 \
    --zoom 11.0 --border 0.47572 0.5243  0.4818  0.51823
sub "$NEW" $D/new_zoom_f2901.png --res 3840 2160 --samples 400 --frame 2901 \
    --zoom 15.0 --border 0.48231 0.51771 0.48627 0.51375
for f in 866 880 400; do
  sub "$NEW" $D/new_f0$f.png --res 1920 1080 --samples 256 --frame $f
done
# the floor under the AFTER image
sub "$NEW" $D/new_repeat_f2978.png --res 3840 2160 --samples 256 --frame 2978

# ---- the floor under the BEFORE image ------------------------------------ #
sub "$OLD" $D/r6_repeat_f2978.png --res 3840 2160 --samples 256 --frame 2978

echo
echo "STAGE RESULT: render set submitted/collected into $D"
ls -la $D
