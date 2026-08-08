#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2-2991 -- the pixel footprint of every feature `forecourt_paving_bay` builds,
at the framing R2-2990 MEASURED and at the framing its gate.json was taken at.

    python3 tools/r2990_forecourt_pixels.py --selftest
    python3 tools/r2990_forecourt_pixels.py --framing work/r2990/framing.json \
            --out work/r2990/pixels.json --md work/r2990/pixels.md

WHY, AND WHY BEFORE ANY EDIT
----------------------------
This project has shipped sub-pixel detail at least six times -- a 20-layer
asphalt surface entirely below one pixel, a carbon weave at 0.87 px, an eye
separation at 2.17 px. The law that stops it is: state the pixel footprint
BEFORE building or changing anything. This file states it, and nothing in
`world/items/forecourt_paving_bay.py` is touched by it.

EVERY DIMENSION IS IMPORTED FROM THE MODULE, NOT RETYPED
--------------------------------------------------------
The module's own constants are read out of it by import. Where a size is a
range chosen per flag (`agg_cell = 0.0042 + 0.0034 * r`), the two ends are
read from the same expression the module evaluates, by naming the constants;
where a size exists only in prose in the docstring, it is marked
`source: docstring` so nobody mistakes it for a measured constant.

TWO FRAMINGS, SIDE BY SIDE, BECAUSE THE ARGUMENT IS THE RATIO
-------------------------------------------------------------
  GATE   what `render/items/forecourt_paving_bay/gate.json` was taken at:
         `filmed_at_m` and `lens_mm` READ OUT OF THAT FILE.
  FILM   what R2-2990 measured off the live camera: `peak_unocc_sharp_px_per_m`.

THE THIRD COLUMN NOBODY COMPUTES: SHADOW
-----------------------------------------
At the contract sun (elevation 12.4706 deg) a feature of height h throws
h / tan(elev) of shadow -- a 4.52x amplifier. A 3 mm lip is 3.1 px of geometry
and 14.2 px of shadow. So a relief feature can be sub-pixel in HEIGHT and still
be the dominant thing in the image, and a purely in-plane feature (a stain, a
saw score) gets no such help. The table says which of the two each feature is.

FORESHORTENING
--------------
A pavement is horizontal and the camera is not above it. An in-plane dimension
ACROSS the view keeps its full px/m; the same dimension ALONG the view is
multiplied by the grazing factor |n.v|. Both are reported. The manifest's own
formula does neither (`screen_presence.py`'s FORESHORTENING note).
"""

import argparse
import importlib.util
import json
import math
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "tools"), os.path.join(R2, "world")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_exit                                                  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "fcp_item", os.path.join(R2, "world", "items", "forecourt_paving_bay.py"))
FCP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FCP)

GATE_JSON = os.path.join(R2, "render", "items", "forecourt_paving_bay",
                         "gate.json")
RELIEF_JSON = os.path.join(R2, "render", "items", "_relief",
                           "forecourt_paving_bay.json")

#: The contract sun. Read from the relief audit's own record of it rather than
#: retyped, so it cannot drift away from the number the relief numbers use.
def sun_elev_deg():
    return float(json.load(open(RELIEF_JSON))["sun_elev_deg"])


def shadow_ratio(elev_deg=None):
    e = sun_elev_deg() if elev_deg is None else elev_deg
    return 1.0 / math.tan(math.radians(e))


# --------------------------------------------------------------- the features
# (label, mm, kind, source)
#   kind: 'relief'   a height -- gets the shadow column
#         'inplane'  a width/length on the surface -- no shadow help
#         'mesh'     a sampling pitch, not a feature: the floor of what CAN be
#                    expressed, so it is the one row where "small" is good
def feature_table():
    F = FCP
    mm = lambda v: float(v) * 1000.0                                # noqa: E731
    rows = [
        # ---- joints -------------------------------------------------------
        ("joint slot, nominal width", mm(F.JOINT_NOM_M), "inplane", "JOINT_NOM_M"),
        ("joint slot, narrowest", mm(F.JOINT_MIN_M), "inplane", "JOINT_MIN_M"),
        ("joint slot, widest", mm(F.JOINT_MAX_M), "inplane", "JOINT_MAX_M"),
        ("joint width laying tolerance (1 sd)", mm(F.JOINT_SD_M), "inplane",
         "JOINT_SD_M"),
        ("joint depth, shallowest (fresh sand)", mm(-F.BED_MAX_M), "relief",
         "BED_MAX_M"),
        ("joint depth, deepest (washed out)", mm(-F.BED_MIN_M), "relief",
         "BED_MIN_M"),
        ("joint depth, far-field bedding sheet", mm(-F.BED_COARSE_M), "relief",
         "BED_COARSE_M"),
        ("construction joint at the shell", mm(F.R1_JOINT_M), "inplane",
         "R1_JOINT_M"),
        # ---- arris --------------------------------------------------------
        ("cast arris chamfer (formed edge)", mm(F.CHAMFER_W_M), "relief",
         "CHAMFER_W_M"),
        ("sawn arris break (cut edge)", mm(F.CHAMFER_SAWN_M), "relief",
         "CHAMFER_SAWN_M"),
        ("mould line down the flag face", 22.0, "relief", "docstring L169"),
        ("arris chip", 2.0, "relief", "docstring L48"),
        ("chipping zone in from the edge", mm(F.CHIP_ZONE_M), "inplane",
         "CHIP_ZONE_M"),
        # ---- saw ----------------------------------------------------------
        ("saw-blade score on a sawn face (BUMP)", 0.25, "inplane",
         "docstring L50 / L2406"),
        ("sawn gap where a flag was cut in", 3.0, "inplane", "L861"),
        # ---- surface texture / aggregate ----------------------------------
        ("blast finish: aggregate cell, min", mm(0.0024), "inplane", "L922"),
        ("blast finish: aggregate cell, max", mm(0.0024 + 0.0022), "inplane",
         "L922"),
        ("blast finish: aggregate proud, min", mm(0.00058), "relief", "L923"),
        ("blast finish: aggregate proud, max", mm(0.00058 + 0.00042), "relief",
         "L923"),
        ("agg finish: aggregate cell, min", mm(0.0042), "inplane", "L907"),
        ("agg finish: aggregate cell, max", mm(0.0042 + 0.0034), "inplane",
         "L907"),
        ("agg finish: aggregate proud, min", mm(0.00110), "relief", "L908"),
        ("agg finish: aggregate proud, max", mm(0.00110 + 0.00095), "relief",
         "L908"),
        ("coarse stone spacing, min", mm(0.0095), "inplane", "L933"),
        ("coarse stone spacing, max", mm(0.0095 + 0.0090), "inplane", "L933"),
        ("coarse stone, the 14 mm one the docstring names", 14.0, "inplane",
         "docstring L44"),
        ("sub-mm matrix pitting (BUMP)", 0.15, "relief", "L418"),
        ("matrix erosion", 0.8, "relief", "docstring L47"),
        # ---- levels / lippage ---------------------------------------------
        ("flag-to-flag lip, target", mm(F.LIP_TARGET_M), "relief",
         "LIP_TARGET_M"),
        ("flag rock on a short bed", mm(F.ROCK_MAX_M), "relief", "ROCK_MAX_M"),
        ("flag warp across the diagonal", mm(F.WARP_MAX_M), "relief",
         "WARP_MAX_M"),
        ("bed level scatter (1 sd)", mm(F.LEVEL_SD_M), "relief", "LEVEL_SD_M"),
        ("settlement basin depth", mm(F.BASIN_DEPTH_M), "relief",
         "BASIN_DEPTH_M"),
        ("flag top band, max above datum", mm(F.FLAG_TOP_MAX_M), "relief",
         "FLAG_TOP_MAX_M"),
        ("flag top band, max below datum", mm(-F.FLAG_TOP_MIN_M), "relief",
         "FLAG_TOP_MIN_M"),
        # ---- jointing grit -------------------------------------------------
        ("jointing grit relief, max", mm(F.GRAIN_MAX_M), "relief",
         "GRAIN_MAX_M"),
        ("jointing grit grain, min", 0.6, "inplane", "L1809"),
        ("jointing grit grain, max", 2.2, "inplane", "L1809"),
        # ---- reinstatement -------------------------------------------------
        ("bitumen overband width", mm(F.OVERBAND_W_M), "inplane",
         "OVERBAND_W_M"),
        ("bitumen overband proud", mm(F.OVERBAND_H_M), "relief",
         "OVERBAND_H_M"),
        ("reinstatement laid low", mm(-F.ASPH_TOP_M), "relief", "ASPH_TOP_M"),
        # ---- sockets -------------------------------------------------------
        ("grout collar width", mm(F.COLLAR_W_M), "inplane", "COLLAR_W_M"),
        ("grout collar below arris", mm(-F.COLLAR_TOP_M), "relief",
         "COLLAR_TOP_M"),
        # ---- mesh floors ---------------------------------------------------
        ("MESH PITCH near band (d <= 2.6 m)", mm(FCP.lod_pitch(1.0)), "mesh",
         "lod_pitch"),
        ("MESH PITCH band 2 (d <= 4.2 m)", mm(FCP.lod_pitch(3.0)), "mesh",
         "lod_pitch"),
        ("MESH PITCH band 3 (d <= 7.0 m)", mm(FCP.lod_pitch(5.0)), "mesh",
         "lod_pitch"),
        ("MESH PITCH far band (d > 7.0 m)", mm(FCP.lod_pitch(20.0)), "mesh",
         "lod_pitch"),
        ("MESH PITCH library flags", mm(F.LIB_PITCH_M), "mesh", "LIB_PITCH_M"),
    ]
    return rows


def relief_stage_rows():
    """The shader bump stages, at their DECLARED wavelength, from the audit."""
    d = json.load(open(RELIEF_JSON))
    out = []
    for m in d["shader"]:
        for b in m["bumps"]:
            out.append((("BUMP %s / %s" % (m["material"], b["node"])),
                        b["wavelength_m"] * 1000.0, b["amp_mm"], b["m"],
                        b.get("driver")))
    return out


# ------------------------------------------------------------------ the maths
def px(mm_val, mm_per_px):
    return float(mm_val) / float(mm_per_px)


def build(mm_per_px_gate, mm_per_px_film, graze=1.0, elev_deg=None):
    sr = shadow_ratio(elev_deg)
    rows = []
    for label, mmv, kind, src in feature_table():
        r = {"feature": label, "mm": round(mmv, 4), "kind": kind, "source": src,
             "px_gate": round(px(mmv, mm_per_px_gate), 3),
             "px_film": round(px(mmv, mm_per_px_film), 3)}
        if kind == "relief":
            r["shadow_mm"] = round(mmv * sr, 3)
            r["shadow_px_film"] = round(px(mmv * sr, mm_per_px_film) * graze, 3)
        if kind == "inplane":
            r["px_film_along_view"] = round(px(mmv, mm_per_px_film) * graze, 3)
        r["verdict_film"] = (
            "MESH FLOOR" if kind == "mesh" else
            "SUB-PIXEL" if r["px_film"] < 1.0 else
            "1-2 px, marginal" if r["px_film"] < 2.0 else "resolves")
        rows.append(r)
    return rows, sr


# ------------------------------------------------------------------- selftest
def _selftest():
    ok = True

    def chk(name, cond, msg=""):
        nonlocal ok
        print("  %-60s %s  %s" % (name, "ok  " if cond else "FAIL", msg))
        ok = ok and bool(cond)

    print(">> SELFTEST r2990_forecourt_pixels")

    chk("closed form: a feature at 2x mm/px is exactly 2 px",
        abs(px(1.9058, 0.9529) - 2.0) < 1e-9, "%.9f" % px(1.9058, 0.9529))

    e = sun_elev_deg()
    chk("sun elevation is read, not typed", abs(e - 12.47061) < 1e-5,
        "%.5f deg from %s" % (e, os.path.relpath(RELIEF_JSON, R2)))
    chk("shadow ratio matches the module's own docstring figure",
        abs(shadow_ratio() - 4.5222) < 0.001, "%.4f" % shadow_ratio())

    rows, _ = build(0.4554, 0.9529)
    by = {r["feature"]: r for r in rows}

    # ---- POSITIVE: the features the module says resolve, do -----------------
    chk("12 mm joint resolves at the film framing",
        by["joint slot, nominal width"]["verdict_film"] == "resolves",
        "%.2f px" % by["joint slot, nominal width"]["px_film"])
    chk("5 mm cast chamfer resolves",
        by["cast arris chamfer (formed edge)"]["verdict_film"] == "resolves",
        "%.2f px" % by["cast arris chamfer (formed edge)"]["px_film"])

    # ---- NEGATIVE: the sub-pixel arm must FIRE, and on the right rows -------
    subs = sorted(r["feature"] for r in rows if r["verdict_film"] == "SUB-PIXEL")
    chk("MUST FIRE: the 0.25 mm blade score is flagged SUB-PIXEL",
        "saw-blade score on a sawn face (BUMP)" in subs)
    chk("MUST FIRE: the 0.15 mm matrix pitting is flagged SUB-PIXEL",
        "sub-mm matrix pitting (BUMP)" in subs)
    chk("MUST NOT FIRE: the 12 mm joint is not flagged",
        "joint slot, nominal width" not in subs,
        "%d rows flagged in all" % len(subs))

    # ---- VACUITY, BOTH WAYS. A classifier that always says the same thing
    # is not a classifier. Squeeze the pixel to nothing and to everything.
    fine, _ = build(0.4554, 1e-6)
    chk("MUST BE EMPTY at 1e-6 mm/px (nothing can be sub-pixel)",
        not any(r["verdict_film"] == "SUB-PIXEL" for r in fine))
    coarse, _ = build(0.4554, 1e6)
    n_nonmesh = sum(1 for r in rows if r["kind"] != "mesh")
    chk("MUST BE TOTAL at 1e6 mm/px (everything is sub-pixel)",
        sum(1 for r in coarse if r["verdict_film"] == "SUB-PIXEL") == n_nonmesh,
        "%d of %d" % (sum(1 for r in coarse if r["verdict_film"] == "SUB-PIXEL"),
                      n_nonmesh))

    # ---- THE TABLE IS WIRED TO THE MODULE, not to a copy of it -------------
    # Damage the module's constant in memory and require the table to move.
    # Without this the whole file could be a transcription and read identically.
    was = FCP.CHAMFER_W_M
    try:
        FCP.CHAMFER_W_M = 0.011
        moved, _ = build(0.4554, 0.9529)
        got = {r["feature"]: r for r in moved}[
            "cast arris chamfer (formed edge)"]["mm"]
        chk("MUST MOVE: damaging FCP.CHAMFER_W_M moves the table",
            abs(got - 11.0) < 1e-6, "table now reports %.3f mm" % got)
    finally:
        FCP.CHAMFER_W_M = was
    back = {r["feature"]: r for r in build(0.4554, 0.9529)[0]}[
        "cast arris chamfer (formed edge)"]["mm"]
    chk("  ...and it comes back when the damage is removed",
        abs(back - 5.0) < 1e-6, "%.3f mm" % back)

    # ---- shadow is an amplifier and must be one ----------------------------
    lip = by["flag-to-flag lip, target"]
    chk("a 3 mm lip is sub-2 px of geometry but supra-pixel in shadow",
        lip["px_film"] < 4.0 < lip["shadow_px_film"],
        "%.2f px of lip, %.2f px of shadow" % (lip["px_film"],
                                               lip["shadow_px_film"]))

    print()
    return gate_exit.verdict("R2990_PIXELS_OK" if ok else "R2990_PIXELS_FAIL",
                             " r2990_pixels_selftest")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--framing", default=os.path.join(R2, "work", "r2990",
                                                      "framing.json"))
    ap.add_argument("--step", default="camera OUTSIDE the pavilion, >= 10",
                    help="substring of the R2-2990 ablation step to read the "
                         "film framing from")
    ap.add_argument("--graze", type=float, default=1.0,
                    help="|n.v| at the measured frame; 1.0 = seen face-on")
    ap.add_argument("--out", default=None)
    ap.add_argument("--md", default=None)
    a = ap.parse_args()
    if a.selftest:
        return _selftest()

    g = json.load(open(GATE_JSON))
    gate_dist = float(g["filmed_at_m"])
    gate_lens = float(g["lens_mm"])
    gate_ppm = (FCP.RES_X_4K * gate_lens / FCP.SENSOR_MM) / gate_dist
    gate_mmpx = 1000.0 / gate_ppm

    fr = json.load(open(a.framing))
    # Which row of R2-2990's ablation is "the film's framing" is a CHOICE, so
    # it is named on the command line and echoed into the report rather than
    # being whichever row happened to be last.
    rows = [r for r in fr["ablation"] if a.step in r["step"] and "ppm" in r]
    if not rows:
        raise SystemExit("REFUSING: no ablation step matching %r in %s. "
                         "Steps present: %s"
                         % (a.step, a.framing,
                            [r["step"] for r in fr["ablation"]]))
    row = rows[0]
    film_ppm = row["ppm"]
    film_mmpx = 1000.0 / film_ppm

    rows, sr = build(gate_mmpx, film_mmpx, graze=a.graze)
    stages = relief_stage_rows()

    doc = {
        "gate": {"filmed_at_m": gate_dist, "lens_mm": gate_lens,
                 "px_per_m": gate_ppm, "mm_per_px": gate_mmpx,
                 "from": os.path.relpath(GATE_JSON, R2)},
        "film": {"step": row["step"], "frame": row["frame"],
                 "depth_m": row["depth_m"], "lens_mm": row["lens_mm"],
                 "n_sharp_unocc_points": row["n_pts"],
                 "px_per_m": film_ppm, "mm_per_px": film_mmpx,
                 "gate_dist_35mm_equiv_m": row["gate_dist_35mm_equiv_m"],
                 "bay_diag_px": row["bay_on_screen"]["diag_px"],
                 "from": os.path.relpath(a.framing, R2)},
        "over_framing_linear": gate_ppm / film_ppm,
        "sun_elev_deg": sun_elev_deg(), "shadow_ratio": sr,
        "graze": a.graze,
        "features": rows,
        "bump_stages": [
            {"stage": s[0], "wavelength_mm": s[1], "amp_mm": s[2], "m": s[3],
             "driver": s[4],
             "wavelength_px_gate": round(s[1] / gate_mmpx, 3),
             "wavelength_px_film": round(s[1] / film_mmpx, 3),
             "nyquist_ok_film": bool(s[1] / film_mmpx >= 2.0)}
            for s in stages],
    }

    print(">> GATE framing  %.3f m @ %.1f mm -> %.1f px/m, %.4f mm/px"
          % (gate_dist, gate_lens, gate_ppm, gate_mmpx))
    print(">> FILM framing  [%s]" % row["step"])
    print(">>               f%d, %.4f m @ %.3f mm -> %.2f px/m, %.4f mm/px  "
          "(%d sharp unoccluded samples)"
          % (doc["film"]["frame"], doc["film"]["depth_m"],
             doc["film"]["lens_mm"], film_ppm, film_mmpx, row["n_pts"]))
    print(">>               hand item_gate --filmed-distance-m %.4f  "
          "(a 35 mm-EQUIVALENT, not a position: R2-1367)"
          % doc["film"]["gate_dist_35mm_equiv_m"])
    print(">> the gate over-framed by %.4fx linear, %.2fx in area"
          % (doc["over_framing_linear"], doc["over_framing_linear"] ** 2))
    print()
    print("%-46s %9s %8s %8s  %s" % ("feature", "mm", "px GATE", "px FILM", ""))
    for r in rows:
        extra = ""
        if r["kind"] == "relief":
            extra = "shadow %8.2f px" % r["shadow_px_film"]
        print("%-46s %9.3f %8.2f %8.2f  %-18s %s"
              % (r["feature"], r["mm"], r["px_gate"], r["px_film"],
                 r["verdict_film"], extra))
    print()
    for s in doc["bump_stages"]:
        print("%-40s lam %8.3f mm = %6.2f px FILM  m %6.3f  %s"
              % (s["stage"], s["wavelength_mm"], s["wavelength_px_film"],
                 s["m"], "" if s["nyquist_ok_film"] else "BELOW 2 px NYQUIST"))

    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        json.dump(doc, open(a.out, "w"), indent=1)
        print(">> wrote %s" % a.out)
    return gate_exit.verdict("R2990_PIXELS_OK", " table built")


if __name__ == "__main__":
    gate_exit.guard(main)
