#!/usr/bin/env python3
"""R2-2401: build the attention A/B pair -- the rendered control for §R2-2408.

NOT RUN. Written, started, and killed at 6 min 57 s because the machine had
528 MB available, 35.4 of 45 GB of swap gone and another agent's 27-minute
film-scene build sitting at 3.9 GB. Two more library builds into that would very
likely have fired the OOM killer at somebody else's afternoon. It is left here
finished so the next agent on a quiet machine can run it in about ninety minutes
rather than rediscover it.

WHAT IT IS FOR. `tools/r2_2401_attention_null.py` shows in the PROJECTION that
`CAM_CROWD_ALONG`'s face count moves 6.9 sd between the shipped crowd and an
`attention = 0` null (491 -> 287 of 613 resolved heads). That is a statistic
responding. It does not show that a person LOOKING through the camera can tell
the two apart, and a verification camera is an instrument for a person to look
through. This builds the two blends that settle it.

    blender -b --factory-startup -P tools/r2_2401_build_attention_ab.py -- \
            --attention 1.0 --out render/r2_2401_attn/attn_ON.blend
    blender -b --factory-startup -P tools/r2_2401_build_attention_ab.py -- \
            --attention 0.0 --out render/r2_2401_attn/attn_OFF.blend

    ./rq render --scene attn_ON.blend  --cam SPECX_CAM_CROWD_ALONG \
                --res 3840 2160 --samples 128 -o C1.png
    ... likewise C2 (attn_OFF), C3/C4 (SPECX_CAM_ATTN_ONAXIS).

RENDER THEM AT 3840, NOT 720p. `CAM_CROWD_ALONG`'s median head is 57.2 px at
3840 and 19.1 px at 1280 -- below the 40 px bar this whole item exists to
enforce. A cheap A/B of a resolvable-band claim, shot outside the resolvable
band, is the pixel-footprint law being broken by the instrument policing it.
This note is here because the agent who wrote the tool made exactly that mistake
and caught it in the nomination rather than in the frames.

TWO THINGS IT DELIBERATELY DOES NOT DO
--------------------------------------
* IT DOES NOT ADD AN `attention` ARGUMENT TO `spectator_crowd.build_scene`.
  Six passes stand on that module and four other agents are in this tree. The
  control wraps `plan_block` from outside, for the duration of one build, and
  the shipped module is untouched. (If the item's owner wants it first-class, a
  `**kw` pass-through is the right change -- see §R2-2409 item 4.)
* IT DOES NOT LET THE CONTROL RE-AIM ITS OWN CAMERAS. `camera_plan` is driven
  off the ATTENTION-ON plan in both blends, so C1/C2 and C3/C4 are the same
  optics pointed at two different crowds. A control that re-plans its camera
  compares two instruments, not two crowds -- which is the mistake that made
  `CAM_SHEET` stand 0.0 m from its aim.
"""

import os
import sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
if "--attention" not in argv or "--out" not in argv:
    sys.exit(__doc__)
ATT = float(argv[argv.index("--attention") + 1])
OUT = os.path.abspath(argv[argv.index("--out") + 1])

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "world"), os.path.join(_ROOT, "world", "items")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bpy                                                      # noqa: E402
import spectator_crowd as SC                                    # noqa: E402
import humankit as HK                                           # noqa: E402

_orig = SC.plan_block


def _patched(seed, seats, facings, focus, n_want=None, legacy_gaze=False, **kw):
    kw.setdefault("attention", ATT)
    return _orig(seed, seats, facings, focus, n_want=n_want,
                 legacy_gaze=legacy_gaze, **kw)


SC.plan_block = _patched
HK.log("R2-2401: building with attention = %.3f -> %s" % (ATT, OUT))
res = SC.build_scene(lod=HK.LOD_L1)

# THE CAMERAS COME FROM THE ATTENTION-ON PLAN IN BOTH BLENDS.
SC.plan_block = _orig
ref = dict(res)
ref["plan"] = _orig(SC.SEED, res["seats"], res["facings"], res["focus"])
SC.add_cameras(ref, draft=False)

a = HK.attention_spread(res["plan"], res["focus"])
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print(">> STAGE RESULT: BUILT_ATTENTION_AB attention=%.3f frac_on=%.4f "
      "circ_sd=%.2f out=%s" % (ATT, a["frac_on"], a["circ_sd_deg"], OUT))
