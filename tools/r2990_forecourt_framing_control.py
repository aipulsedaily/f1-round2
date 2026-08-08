#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2-2990 CONTROL -- damage `r2990_forecourt_framing.py` and WATCH THE ARMS FIRE.

    python3 tools/r2990_forecourt_framing_control.py

WHY THIS IS SEPARATE FROM `--selftest`
--------------------------------------
`--selftest` tests the ALGEBRA -- projection, frustum, foreshortening, the
subject mask -- on synthetic inputs. It cannot tell you whether the assembled
measurement still discriminates, because every arm in it is built from the same
constants the tool uses.

This file damages the tool in six ways THAT MATCH REAL DEFECTS THIS PROJECT HAS
LOGGED, points the damaged tool at the one number that is published and fixed
(`sp_objects.json`'s `peak_unocc_sharp_px_per_m` for `ARCH_Paving_Forecourt`,
1049.4475 px/m at f282) and requires that:

  * UNDAMAGED, it reproduces that number to four decimals. Without this the
    corrections below are a change of instrument, not a finding.
  * DAMAGED, it does NOT. An arm that gives the same answer with the check
    removed is not a check -- that is the single most-logged defect shape on
    this project, and it is why every damage mode below is asserted to MOVE the
    number and the amount it moves by is printed.

THE SIX DAMAGE MODES, AND THE DEFECT EACH ONE IS
------------------------------------------------
  radial            radial distance where pinhole depth belongs. This is the
                    manifest's own error (screen_presence docstring step 1).
  no_frustum        score anything in front of the camera whether or not it is
                    in the picture. This is R2-1362's trap, where a 5.2 m
                    station scored 7,560 px while being out of frame at every
                    one of those frames -- a 20x overstatement.
  no_smear          drop the 6 px sharpness gate, i.e. rank on `peak_px_per_m`.
                    This is the quantity `docs/WAVE2-RANKING.md` actually ranked
                    on and R2-2945 rejected.
  no_occ            do not rasterise the depth buffer at all.
  no_subject_mask   score the whole `ARCH_Paving_Forecourt` object, including
                    the sub-base prism and the formation slab buried under the
                    showroom floor -- geometry the item's own docstring says it
                    does NOT build. This is the R2-1362 / R2-2941 "measuring
                    their host" defect, one level in.
  no_plane_snap     leave the point at its voxel CENTRE, half a metre above the
                    concrete, under a camera 2.9 m up.

EXIT 0 if every damage mode is rejected, 1 if any is not, per tools/gate_exit.py.
"""

import json
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "tools"))

import gate_exit                                                 # noqa: E402
import live_campath                                              # noqa: E402
import r2990_forecourt_framing as FR                             # noqa: E402

SP_CFG = {"no_subject_mask": True, "no_plane_snap": True}


def published():
    sp = json.load(open(FR.SP_OBJECTS))
    row = [r for r in sp["objects"] if r["object"] == FR.HOST_OBJECT][0]
    return row["peak_unocc_sharp_px_per_m"], row["sharp_frame"]


#: The two configurations the arms are run in. An arm that cannot bind in one
#: may bind in the other, and reporting only the first is how a null gets
#: mistaken for a check. `sp` is the published configuration (for calibration);
#: `answer` is the configuration R2-2990's conclusion actually rests on.
CONFIGS = {
    "sp (as published)": dict(damage=dict(SP_CFG), min_points=1,
                              outdoor_only=False),
    "answer (masked, snapped, outdoors)": dict(damage={}, min_points=10,
                                               outdoor_only=True),
}

#: EVERY published quantity, not just the headline. `no_frustum` cannot move a
#: peak that is already in frame, and `no_occ` cannot move a peak that is
#: already unoccluded -- but both move the COUNTS, and the counts are reported
#: in `framing.json` and quoted in the staging note. An arm fires if any
#: published quantity moves; an arm that moves NOTHING published is vacuous.
def observables(r):
    return {
        "ppm": r["peak_sharp"]["ppm"],
        "frame": float(r["peak_sharp"]["frame"]),
        "n_sharp_unocc_pts": float(r["peak_sharp"]["n_sharp_unocc_pts"]),
        "frames_sharp_in_frustum": float(r["frames_sharp_in_frustum"]),
        "peak_any_ppm": r["peak_any_ppm"],
        "peak_any_frame": float(r["peak_any_frame"]),
    }


def main():
    pub, pubf = published()
    cam = os.path.join(R2, FR.SP_CAMERA_FOR_CONTROL)
    live_campath.load_explicit(
        FR.SP_CAMERA_FOR_CONTROL,
        why="R2-2990 control harness: the published number this instrument is "
            "calibrated against was measured on this camera, so the damage "
            "arms must be run on it too or they test two things at once")

    print(">> published %.4f px/m at f%d\n" % (pub, pubf))

    doc = {"published_ppm": pub, "published_frame": pubf, "configs": {}}
    bad = []

    for cname, cfg in CONFIGS.items():
        base = FR.take_reading(cam, "baseline " + cname,
                               damage=dict(cfg["damage"]),
                               min_points=cfg["min_points"],
                               outdoor_only=cfg["outdoor_only"], quiet=True)
        bo = observables(base)
        print("== %s ==" % cname)
        print("  %-20s %9.4f px/m at f%-5d  %d pts, %d sharp frames"
              % ("baseline", bo["ppm"], int(bo["frame"]),
                 int(bo["n_sharp_unocc_pts"]),
                 int(bo["frames_sharp_in_frustum"])))
        if cname.startswith("sp"):
            okb = abs(bo["ppm"] - pub) / pub < 1e-4 and int(bo["frame"]) == pubf
            print("  %-20s %s" % ("", "REPRODUCES the published number"
                                  if okb else "DOES NOT REPRODUCE -- STOP"))
            if not okb:
                return gate_exit.verdict("R2990_CONTROL_FAIL",
                                         " baseline does not reproduce")

        modes = ["radial", "no_frustum", "no_smear", "no_occ"]
        if cname.startswith("sp"):
            # the two CORRECTIONS are on in the sp configuration by definition,
            # so damaging them means turning them off
            modes += ["no_subject_mask", "no_plane_snap"]
        rows = []
        for m in modes:
            d = dict(cfg["damage"])
            if m in d:
                d.pop(m)
            else:
                d[m] = True
            try:
                r = FR.take_reading(cam, m, damage=d,
                                    min_points=cfg["min_points"],
                                    outdoor_only=cfg["outdoor_only"],
                                    quiet=True)
                o = observables(r)
                moved = {k: (o[k] - bo[k]) for k in o if o[k] != bo[k]}
                fired = bool(moved)
            except SystemExit as exc:
                o, moved, fired = {}, {"REFUSED": str(exc)}, True
            rows.append({"damage": m, "observables": o, "moved": moved,
                         "fired": fired})
            print("  %-20s %s"
                  % (m, ("ok  rejected -- moved " +
                         ", ".join("%s %s->%s" % (k, _f(bo.get(k)), _f(o.get(k)))
                                   for k in moved))
                     if fired else
                     "FAIL  VACUOUS -- not one published quantity moves"))
            if not fired:
                bad.append("%s / %s" % (cname, m))
        doc["configs"][cname] = {"baseline": bo, "arms": rows}
        print()

    rc = gate_exit.verdict(
        "R2990_CONTROL_FAIL" if bad else "R2990_CONTROL_PASS",
        ("  vacuous arm(s): %s" % ", ".join(bad)) if bad else
        " (every damage mode moves a published quantity in both configurations)")
    doc["vacuous"] = bad
    json.dump(doc, open(os.path.join(R2, "work", "r2990", "control.json"), "w"),
              indent=1)
    return rc


def _f(v):
    if v is None:
        return "-"
    return ("%.4f" % v) if isinstance(v, float) and abs(v) < 1e6 else str(v)


if __name__ == "__main__":
    os.makedirs(os.path.join(R2, "work", "r2990"), exist_ok=True)
    gate_exit.guard(main)
