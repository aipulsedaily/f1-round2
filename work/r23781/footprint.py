#!/usr/bin/env python3
"""R2-3781 -- THE PIXEL FOOTPRINT OF EVERY FEATURE, STATED BEFORE IT IS BUILT.

    python3 work/r23781/footprint.py --out work/r23781/footprint.json
    python3 work/r23781/footprint.py --control

This is `tools/r2970_groundcover_px.py`'s law applied to the four last items.
It is a separate file because that one is hard-wired to `build_terrain`'s
generators by design (`BT.GRASS_PROF`, `BT.WEEDS`, ...), and reaching into it
would make the ground cover's verdicts depend on this task's edits.

THE LAW, unchanged from R2-2970
===============================
    ABOVE    >= the line and built            -- fine
    MISSING  >= the line and NOT built        -- the defect being hunted
    BELOW    <  the line                      -- must not be built; waste

    line = 1 px   for an ISOLATED feature: a nail head, a chip, a lobe
    line = 2 px   for a PERIODIC feature -- a wave sampled under twice per
                  cycle does not come out small, it comes out ALIASED.  The
                  pitch is what is measured, never the amplitude.

TWO AMPLIFIERS THIS FILE ADDS, BOTH MEASURED NOT ASSUMED
========================================================
1.  SHADOW.  The contract sun sits at 12.47061 deg, so a relief feature throws
    1/tan(e) = 4.5217 x its own height in shadow.  A 5 mm lip is 0.7 px of
    geometry and 3.0 px of shade.  Rows typed `relief` are judged on the
    shadow; rows typed `inplane` get no such help.
2.  FORESHORTENING.  A ground plane seen at a grazing angle loses its in-plane
    sizes along the view.  Rows typed `inplane` on the apron are additionally
    scaled by |n.v| at the framing frame.

THE FRAMING IS READ, NOT DERIVED
================================
px/m comes from `work/r23721_item2/a9_film24_sp_objects.json`
(`peak_unocc_sharp_px_per_m`) -- the delivered camera, 2,978 frames, flat 180
deg shutter, occlusion applied -- for the object that IS the item, never for
the host it is ranked through.  `work/r23781/framing.json` is this task's own
independent arm and is printed beside it.  Deriving px/m from a lens and a
distance is the mistake R2-2990 named; both numbers here are measurements.
"""
import os
import sys
import json
import math
import argparse

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "world"))
import world_contract as C                                        # noqa: E402

SP_OBJECTS = os.path.join(R2, "work", "r23721_item2", "a9_film24_sp_objects.json")
FRAMING = os.path.join(R2, "work", "r23781", "framing.json")

PX_LINE = 1.0
NYQUIST_LINE = 2.0

SUN_ELEV = float(C.SUN_ELEV_DEG)
SHADOW_AMP = 1.0 / math.tan(math.radians(SUN_ELEV))               # 4.5217

# The object that IS each item, and the frame the film gives it.  The apron's
# subject is ARCH_Paving_ApronPlatform ALONE: ARCH_Paving_Forecourt also casts
# the formation slab under the round-1 pavilion floor, and that slab -- buried,
# seen from inside the showroom at f282 -- is what sets the 1049 px/m the
# ranking used (R2-2990 measured the same defect on forecourt_paving_bay).
SUBJECT = {
    "exterior_ground_apron":   ["ARCH_Paving_ApronPlatform"],
    "grandstand_debris_fence": ["ARCH_Grandstand_00_OUEST", "ARCH_Grandstand_01_T15",
                                "ARCH_Grandstand_02_OUEST", "ARCH_Grandstand_03_PRINCIPALE",
                                "ARCH_Grandstand_04_EST", "ARCH_Grandstand_05_TEMPORAIRE",
                                "ARCH_Grandstand_Towers", "ARCH_Grandstand_Terrace"],
    "podium_backdrop":         ["ARCH_Grandstand_Towers", "ARCH_Grandstand_Terrace"],
    "podium_structure":        ["ARCH_Grandstand_Towers", "ARCH_Grandstand_Terrace"],
}
RANKED_THROUGH = dict(SUBJECT)
RANKED_THROUGH["exterior_ground_apron"] = ["ARCH_Paving_Forecourt",
                                           "ARCH_Paving_ApronPlatform"]

# |n.v| at the item's framing frame.  The apron is a ground plane and the
# closing/lap frames look across it, not down it.  0.2071 is R2-2990's measured
# value for the forecourt bays at f910 (11.95 deg above the pavement) and is
# reused here because it is the same surface at a comparable grazing angle;
# it is a stated assumption, not a measurement of THIS object, and it is
# flagged as such in the report.
FORESHORTEN = {"exterior_ground_apron": 0.2071}

# ---------------------------------------------------------------------------
# The candidate features.  Every row is stated HERE, with its millimetres, its
# kind and why it is a candidate at all -- before anything is built.  A row
# that comes out BELOW must not be built, and the arithmetic that declined it
# has to be on the record or somebody will build it again.
#
# kind: "iso"     an isolated feature, judged at 1 px on its own size
#       "per"     a periodic feature, judged at 2 px on its PITCH
#       "relief"  an isolated feature whose read is its SHADOW (x4.5217)
#       "inplane" an isolated in-plane feature, foreshortened, no shadow help
FEATURES = {
    "exterior_ground_apron": [
        ("bay saw-cut joint PITCH",           "per",     3000.0, "the bay layout itself"),
        ("bay joint SHADOW (5 mm deep sinking)", "relief",   5.0, "what a joint actually reads as at 12.5 deg sun"),
        ("bay joint WIDTH",                   "inplane",    4.0, "the cut itself, seen in plane"),
        ("joint sealant bead WIDTH",          "inplane",   10.0, "grey mastic against grey concrete"),
        ("arris chamfer at bay edge",         "relief",     3.0, "the 3 mm break every precast edge carries"),
        ("broom / tine finish PITCH",         "per",        2.5, "the corduroy of a floated slab"),
        ("exposed aggregate diameter",        "iso",        8.0, "the coarse fraction standing proud"),
        ("float-texture stipple",             "iso",        1.2, "the fine skin"),
        ("hairline shrinkage crack WIDTH",    "inplane",    0.8, "the crack that makes concrete concrete"),
        ("surface undulation, lam 1.5 m",     "per",     1500.0, "the long waviness of a laid slab"),
        ("drainage channel slot PITCH",       "per",       25.0, "the grating over the edge channel"),
        ("edge upstand / drop to bedding",    "relief",   100.0, "the apron's own edge, already built"),
        ("tyre-rubber deposit band WIDTH",    "inplane",  600.0, "already built by build_surface"),
    ],
    "grandstand_debris_fence": [
        ("fence overall height",              "iso",     3600.0, "the thing itself"),
        ("post PITCH",                        "per",     2500.0, "the bay rhythm"),
        ("post section depth",                "iso",      150.0, "the member's own width"),
        ("top rail diameter",                 "iso",       48.0, "the cap rail"),
        ("bracket / cleat plate",             "iso",      100.0, "the fixing to the terrace"),
        ("debris MESH aperture PITCH",        "per",       50.0, "THE defining feature of a debris fence"),
        ("mesh wire diameter",                "iso",        3.15, "the wire itself"),
        ("tensioning cable diameter",         "iso",        8.0, "the horizontal cables"),
        ("galvanising spangle",               "iso",       15.0, "shading, not geometry"),
    ],
    "podium_structure": [
        ("podium overall height",             "iso",     3500.0, "the thing itself"),
        ("dais riser height",                 "iso",      180.0, "the three-level dais"),
        ("step nosing",                       "relief",    30.0, "the edge that separates a step from a stripe"),
        ("handrail tube diameter",            "iso",       42.0, "the rail"),
        ("balustrade infill PITCH",           "per",      100.0, "the vertical bars"),
        ("deck plank PITCH",                  "per",      150.0, "the boarded deck"),
        ("deck plank gap",                    "relief",     5.0, "the shadow line between boards"),
        ("panel joint reveal",                "relief",    10.0, "the joint between clad panels"),
        ("fixing bolt head",                  "iso",       19.0, "the fastener"),
    ],
    "podium_backdrop": [
        ("backdrop overall height",           "iso",     4000.0, "the thing itself"),
        ("sponsor lettering cap height",      "iso",      300.0, "the only thing a backdrop is FOR"),
        ("brand tile repeat PITCH",           "per",     1200.0, "the repeating tile"),
        ("fabric sag, lam 1.2 m",             "relief",    40.0, "the sag that makes it fabric and not board"),
        ("frame tube diameter",               "iso",       50.0, "the frame"),
        ("eyelet diameter",                   "iso",       25.0, "the fixings along the edge"),
        ("panel seam WIDTH",                  "inplane",   12.0, "the stitched seam"),
        ("fabric weave PITCH",                "per",        1.2, "the cloth itself"),
    ],
}


def load_px_per_m():
    d = json.load(open(SP_OBJECTS))
    objs = {o["object"]: o for o in d["objects"]}
    out = {}
    for item, subs in SUBJECT.items():
        best = None
        for name in subs:
            o = objs.get(name)
            if not o:
                continue
            v = float(o["peak_unocc_sharp_px_per_m"])
            if best is None or v > best[1]:
                best = (name, v, int(o["sharp_frame"]))
        rbest = None
        for name in RANKED_THROUGH[item]:
            o = objs.get(name)
            if not o:
                continue
            v = float(o["peak_unocc_sharp_px_per_m"])
            if rbest is None or v > rbest[1]:
                rbest = (name, v, int(o["sharp_frame"]))
        out[item] = dict(subject_object=best[0], px_per_m=best[1], frame=best[2],
                         ranked_object=rbest[0], ranked_px_per_m=rbest[1],
                         ranked_frame=rbest[2])
    return out


def verdict(kind, mm, ppm, fore, damage=""):
    """-> (px, line, verdict, note)."""
    amp = 1.0 if damage == "no_shadow" else SHADOW_AMP
    f = 1.0 if damage == "no_foreshorten" else fore
    line = PX_LINE if damage == "no_nyquist" else (
        NYQUIST_LINE if kind == "per" else PX_LINE)
    eff = mm
    note = ""
    if kind == "relief":
        eff = mm * amp
        note = "shadow x%.4f" % amp
    elif kind == "inplane":
        eff = mm * f
        note = "foreshortened x%.4f" % f
    px = eff * 1e-3 * ppm
    v = "ABOVE" if px >= line else "BELOW"
    if line <= px < line * 1.35:
        v = "MARGINAL"
    return px, line, v, note


def measure(damage=""):
    fr = load_px_per_m()
    out = {}
    for item, rows in FEATURES.items():
        ppm = fr[item]["px_per_m"]
        if damage == "ranked_px_per_m":
            ppm = fr[item]["ranked_px_per_m"]
        fore = FORESHORTEN.get(item, 1.0)
        res = []
        for name, kind, mm, why in rows:
            px, line, v, note = verdict(kind, mm, ppm, fore, damage)
            res.append(dict(feature=name, kind=kind, mm=mm, px=round(px, 3),
                            line=line, verdict=v, note=note, why=why))
        out[item] = dict(framing=fr[item], mm_per_px=round(1000.0 / ppm, 4),
                         features=res)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--control", action="store_true")
    a = ap.parse_args()

    base = measure()
    print("R2-3781  FEATURE FOOTPRINTS -- stated before anything is built")
    print("sun %.5f deg   shadow amplifier %.4f   lines: isolated %.1f px, "
          "periodic %.1f px (Nyquist)" % (SUN_ELEV, SHADOW_AMP, PX_LINE, NYQUIST_LINE))
    ind = {}
    if os.path.exists(FRAMING):
        ind = json.load(open(FRAMING))["items"]
    for item, d in base.items():
        f = d["framing"]
        mine = ind.get(item, {}).get("self", {}).get("peak_px_per_m")
        print("")
        print("%s" % item.upper())
        print("  measured on %-28s %8.2f px/m  @f%-5d  1 px = %.3f mm"
              % (f["subject_object"], f["px_per_m"], f["frame"], d["mm_per_px"]))
        if mine:
            print("  this task's independent arm            %8.2f px/m" % mine)
        if f["ranked_object"] != f["subject_object"]:
            print("  RANKED THROUGH %-28s %8.2f px/m  @f%-5d  -- %.2fx larger"
                  % (f["ranked_object"], f["ranked_px_per_m"], f["ranked_frame"],
                     f["ranked_px_per_m"] / f["px_per_m"]))
        if item in FORESHORTEN:
            print("  in-plane rows foreshortened by |n.v| = %.4f (stated, "
                  "not measured on this object)" % FORESHORTEN[item])
        print("  %-36s %-8s %9s %8s %5s  %s" %
              ("feature", "kind", "mm", "px", "line", "verdict"))
        for r in d["features"]:
            print("  %-36s %-8s %9.2f %8.2f %5.1f  %-8s %s" %
                  (r["feature"], r["kind"], r["mm"], r["px"], r["line"],
                   r["verdict"], r["note"]))
        nb = sum(1 for r in d["features"] if r["verdict"] == "BELOW")
        na = sum(1 for r in d["features"] if r["verdict"] == "ABOVE")
        nm = sum(1 for r in d["features"] if r["verdict"] == "MARGINAL")
        print("  -> %d ABOVE, %d MARGINAL, %d BELOW of %d"
              % (na, nm, nb, len(d["features"])))

    if a.out:
        json.dump(dict(sun_elev_deg=SUN_ELEV, shadow_amplifier=SHADOW_AMP,
                       px_line=PX_LINE, nyquist_line=NYQUIST_LINE,
                       foreshorten=FORESHORTEN, items=base),
                  open(a.out, "w"), indent=1)
        print("\nwrote %s" % a.out)

    if not a.control:
        print(">> STAGE RESULT: R2_3781_FOOTPRINT_OK")
        return 0

    print("")
    print("CONTROL -- each damage must move at least one verdict")
    dead = []
    for dmg in ("", "no_shadow", "no_foreshorten", "no_nyquist", "ranked_px_per_m"):
        got = measure(dmg)
        moved = tot = 0
        for item in base:
            for i, r in enumerate(base[item]["features"]):
                tot += 1
                if got[item]["features"][i]["verdict"] != r["verdict"]:
                    moved += 1
        if dmg == "":
            ok = moved == 0
            print("  %-16s NULL, must NOT move   %2d/%2d   %s"
                  % ("(none)", moved, tot, "ok" if ok else "BROKEN"))
            if not ok:
                dead.append("null")
        else:
            ok = moved > 0
            print("  %-16s must move             %2d/%2d   %s"
                  % (dmg, moved, tot, "ok" if ok else "VACUOUS"))
            if not ok:
                dead.append(dmg)
    if dead:
        print(">> STAGE RESULT: R2_3781_FOOTPRINT_CONTROL_BROKEN  [%s]" % ",".join(dead))
        return 1
    print(">> STAGE RESULT: R2_3781_FOOTPRINT_CONTROL_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
