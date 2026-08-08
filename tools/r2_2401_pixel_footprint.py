#!/usr/bin/env python3
"""R2-2401: WHAT A CROWD CAMERA CAN RESOLVE OF A PERSON, AND WHAT ITS BLUR IS.

The pixel-footprint law has bitten this project at least four times: detail
authored outside the camera's resolvable band is invisible however correct it
is. The same law applies to the INSTRUMENT -- a verification camera has a
resolvable band too, and the two block cameras deleted on 2026-08-03 were
outside it. This is the arithmetic that says so, and it deliberately imports
NOTHING from `spectator_crowd.py`: if it agrees with `preflight` that is two
independently written arithmetics, and if it disagrees one of them is wrong and
we find out which. (It agrees: 8.06 / 10.90 px at the aim point against
preflight's 8.0 / 10.1 px median over the population in frame.)

    python3 tools/r2_2401_pixel_footprint.py
    python3 tools/r2_2401_pixel_footprint.py --size 0.23 --dist 112.5 --lens 50
    blender -b --factory-startup -P tools/r2_2401_pixel_footprint.py -- --datablocks BLEND

THE BLUR NUMBER NEEDS A STATED ASSUMPTION, and this is the whole trap
---------------------------------------------------------------------
HUMAN-REFERENCE sec 0000.5 recorded the block cameras as ruined by depth of
field. There is none: `use_dof = False` on every camera datablock, `fstop 2.8`
and `focus_distance 10.0` are Blender's untouched defaults. So "the blur circle"
has no single value -- it depends on what you imagine having been done:

  * flip `use_dof` on AS DELIVERED (focus left at its 10 m default) and the
    subject at 112.5 m blurs by 8.72 px at 4K -- LARGER THAN THE 10.9 px HEAD.
    Sec 0000.5's own prescribed remedy was "re-shoot with the aperture wide
    open", and on this datablock that is what it means. The fix would have made
    the frame strictly worse and the result would have read as confirmation.
  * ALSO focus at the subject and the lens is past hyperfocal (95.29 m on a 1 px
    4K budget), so the ceiling on defocus for an object at infinity is 0.847 px.

`--coc` reports both rows. Neither is "the" answer and quoting one without the
assumption is how a stale number outlives the record that corrected it.
"""

import argparse
import sys

SENSOR_MM = 36.0
RES_X_4K = 3840
HEAD_H_M = 0.23            # brow-to-chin; `spectator_crowd._HEAD_H_M`
EYE_SEP_M = 0.062          # interpupillary, adult
SHOULDER_W_M = 0.42        # biacromial, seated adult

# The two cameras deleted on 2026-08-03, at the distances R2-1991 recovered.
# 200 m / 148 m are the SUPERSEDED pair and are still quoted in places: a 0.23 m
# head at 200 m on a 50 mm lens is 6.1 px, not the 8.0 px recorded beside it,
# and only 152.20 / 112.50 reproduce the recorded figures.
REJECTED = (("CAM_BLOCK_ONAXIS", 152.20, 50.0, -9.0),
            ("CAM_BLOCK_CROSS", 112.50, 50.0, -11.0))
REPLACEMENTS = (("CAM_CROWD_ALONG", 104.3, 276.5),
                ("CAM_ATTN_ONAXIS", 135.7, 276.5),
                ("CAM_ATTN_PROFILE", 102.1, 270.6))


def px(size_m, dist_m, lens_mm, res_x=RES_X_4K):
    """Projected size in pixels. The whole law in one line."""
    return size_m / dist_m * (lens_mm / SENSOR_MM) * res_x


def coc_px(lens_mm, fstop, focus_m, subj_m, res_x=RES_X_4K):
    """Blur-circle diameter in pixels for a subject at `subj_m` with the lens
    focused at `focus_m`. Thin lens, standard geometric result."""
    A = lens_mm / fstop
    s, sf = subj_m * 1000.0, focus_m * 1000.0
    c_mm = A * abs(s - sf) / s * lens_mm / (sf - lens_mm)
    return c_mm / SENSOR_MM * res_x, c_mm


def hyperfocal_m(lens_mm, fstop, budget_px, res_x=RES_X_4K):
    c = budget_px * SENSOR_MM / res_x
    return (lens_mm ** 2 / (fstop * c) + lens_mm) / 1000.0


def dump_datablocks(path):
    """Read camera datablocks WITHOUT loading 34 M triangles.

    `bpy.data.libraries.load(link=True)` pulls the camera datablocks out of a
    600 MB scene in seconds, which is the cheap way to interrogate one and is
    how the depth-of-field claim was settled by reading rather than by arguing.
    """
    import bpy
    with bpy.data.libraries.load(path, link=True) as (src, dst):
        dst.cameras = list(src.cameras)
        names = list(src.cameras)
    bad = 0
    for c in bpy.data.cameras:
        print("   %-28s lens=%-8.3f use_dof=%-6s fstop=%-5.2f focus=%.3f"
              % (c.name, c.lens, c.dof.use_dof, c.dof.aperture_fstop,
                 c.dof.focus_distance))
        bad += bool(c.dof.use_dof)
    print(">> STAGE RESULT: %s (%d camera(s) with use_dof True)"
          % ("DOF_OFF_ON_EVERY_CAMERA" if not bad else "DOF_IS_ON", bad))
    old = [n for n in names if "BLOCK_" in n]
    print(">> STAGE RESULT: %s (%s)"
          % ("REJECTED_CAMERAS_ABSENT" if not old
             else "REJECTED_CAMERAS_STILL_PRESENT",
             old or "no BLOCK_* datablock"))
    return 0


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser(prog="r2_2401_pixel_footprint")
    p.add_argument("--datablocks", metavar="BLEND",
                   help="read camera datablocks out of a .blend (needs Blender)")
    p.add_argument("--size", type=float, help="feature size in metres")
    p.add_argument("--dist", type=float, help="distance in metres")
    p.add_argument("--lens", type=float, help="focal length in mm")
    p.add_argument("--res", type=int, default=RES_X_4K)
    a = p.parse_args(argv)

    if a.datablocks:
        return dump_datablocks(a.datablocks)

    if a.size and a.dist and a.lens:
        print("%.4f m at %.2f m on %.1f mm, %d wide: %.3f px"
              % (a.size, a.dist, a.lens, a.res, px(a.size, a.dist, a.lens, a.res)))
        return 0

    print("REJECTED PAIR -- what they can resolve of a person")
    print("%-20s %8s %6s %9s %9s %9s %7s"
          % ("camera", "dist m", "lens", "head px", "eye sep", "shoulder", "elev"))
    for nm, d, lens, elev in REJECTED:
        print("%-20s %8.2f %6.0f %9.2f %9.3f %9.2f %7.1f"
              % (nm, d, lens, px(HEAD_H_M, d, lens), px(EYE_SEP_M, d, lens),
                 px(SHOULDER_W_M, d, lens), elev))
    print("\n  An interpupillary distance of 2.17 px is the sub-pixel finding of")
    print("  this defect: there is no gaze direction in those frames to read.")

    print("\nTHE BLUR CIRCLE, under both assumptions (50 mm, f/2.8)")
    for nm, d, lens, _e in REJECTED:
        x, xmm = coc_px(lens, 2.8, 10.0, d)
        y, ymm = coc_px(lens, 2.8, d, 1e9)
        print("  %-20s use_dof flipped on as delivered (focus 10 m): %7.2f px"
              % (nm, x))
        print("  %-20s ... and focused at its own subject (ceiling): %7.3f px"
              % ("", y))
    print("  hyperfocal 50 mm f/2.8, 1 px at 4K:  %.2f m" % hyperfocal_m(50.0, 2.8, 1.0))
    print("  ... the delivered blur EXCEEDS the head. The prescribed fix was worse.")

    print("\nREPLACEMENTS -- a long lens from low down, along the bank")
    print("%-20s %8s %6s %9s %9s"
          % ("camera", "aim m", "lens", "head px", "eye sep"))
    for nm, d, lens in REPLACEMENTS:
        print("%-20s %8.1f %6.0f %9.2f %9.3f"
              % (nm, d, lens, px(HEAD_H_M, d, lens), px(EYE_SEP_M, d, lens)))
    print("\n  The lens a 40 px head needs at the rejected distances:")
    for nm, d, _l, _e in REJECTED:
        print("    %-20s %6.1f mm" % (nm, 40.0 * SENSOR_MM * d / (HEAD_H_M * RES_X_4K)))
    print("\n  Distance and lens were the only real levers. The aperture never was.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
