#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2366_relief_audit.py — what relief the SHIPPED paving and roof materials
actually deliver, in radiance, before anything is changed.

THE AUDIT DIRECTION. `itemkit.relief_budget` / `bump_relief_report` exist to be
pointed at what you already have, and it takes no render. Run this BEFORE and
AFTER so the two columns are directly comparable.

It builds ONLY the material factories out of `build_architecture` — no world, no
geometry, no contract sweep — so it costs seconds rather than 1,400 s.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/r2366_relief_audit.py -- [--json OUT]

Blender 5.2 exits 0 on an uncaught script exception; judge on `STAGE RESULT`.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))

import bpy                                                   # noqa: E402
import itemkit as K                                          # noqa: E402

# The three paving materials, which `tools/r2366_crop_owner.py` measured to be
# 59.8 % of the brief's crop by raycast: A_ConcSlab 32.5 %, A_ConcApron 21.5 %,
# A_ForecourtSlab 5.8 %. The brief named the apron and the forecourt; the
# largest of the three is the PADDOCK, and it was found by raycasting the
# delivered frame rather than by trusting the label.
SUBJECTS = [
    ("A_ConcSlab", "isotropic_macro"),
    ("A_ConcApron", "isotropic_macro"),
    ("A_ForecourtSlab", "isotropic_macro"),
]


# NOTE ON `height_pp = 1.0` BELOW, WHICH IS EXACT HERE AND WAS NOT BEFORE.
# `bump_relief_report` defaults to 1.0 as the CONSERVATIVE reading, because a
# raw Noise Fac does not swing the full range. Against the shipped materials
# that default over-read every stage by ~4x: it called A_ConcApron m 2.966 HIGH
# when `tools/r2366_swing.py` renders the actual height chain and measures a
# 0.2443 swing, putting it at m 0.764, comfortably in band. THE FIRST AUDIT OF
# THIS TASK WAS THEREFORE WRONG IN THE ALARMING DIRECTION and the repair would
# have been to reduce relief that was already correct.
# R2-366's own stages put a Map Range on their measured p1..p99 so the signal
# reaching each bump really does swing 0..1, which makes 1.0 exact rather than
# conservative — the audit now reads true without needing the swing table.
def audit(name, band, elev=None):
    m = bpy.data.materials.get(name)
    if m is None or not m.use_nodes:
        return {"material": name, "present": False}
    rows = K.bump_relief_report(m.node_tree, elev_deg=elev, height_pp=1.0)
    out = {"material": name, "present": True, "band": band,
           "band_range": list(K.RELIEF_BANDS[band]), "bumps": []}
    lo, hi = K.RELIEF_BANDS[band]
    for r in rows:
        v = None
        if r["m"] is not None:
            v = "LOW" if r["m"] < lo else "HIGH" if r["m"] > hi else "ok"
        r = dict(r)
        r["verdict"] = v
        out["bumps"].append(r)
    # displacement is the other half of "check both layers"
    outn = [n for n in m.node_tree.nodes
            if n.bl_idname == "ShaderNodeOutputMaterial"]
    out["displacement_linked"] = any(
        n.inputs["Displacement"].links for n in outn)
    out["n_bumps"] = len(rows)
    # BOUND IT BOTH WAYS, AND BOUND THE WHOLE SURFACE, NOT EACH OCTAVE.
    # Four independent random fields perturb the normal independently, so their
    # slopes add in quadrature. Every stage can sit inside the band while the
    # surface they add up to sits well outside it — checking only the stages
    # would be a summary statistic hiding the thing it summarises.
    ms = [r["m"] for r in rows if r["m"] is not None]
    out["m_quadrature"] = math.sqrt(sum(x * x for x in ms)) if ms else None
    if out["m_quadrature"] is not None:
        out["quadrature_verdict"] = (
            "LOW" if out["m_quadrature"] < lo else
            "HIGH" if out["m_quadrature"] > hi else "ok")
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    jout = argv[argv.index("--json") + 1] if "--json" in argv else None

    import build_architecture as BA
    # the two factories, nothing else. build_materials() first because
    # build_materials_extra() reuses helpers registered there.
    for fn in ("build_materials", "build_materials_extra"):
        f = getattr(BA, fn, None)
        if f is None:
            print("STAGE RESULT: r2366_relief_audit FAIL (no BA.%s)" % fn)
            sys.exit(1)
        f()
    print("[audit] materials registered: %d" % len(bpy.data.materials))

    elev = K.sun_elev_deg()
    print("[audit] sun elevation %.4f deg, amplifier %.3fx"
          % (elev, K.sun_amplifier()))
    print("")

    res = []
    for name, band in SUBJECTS:
        a = audit(name, band, elev)
        res.append(a)
        if not a["present"]:
            print("%-18s ABSENT from bpy.data.materials" % name)
            continue
        lo, hi = a["band_range"]
        print("%-18s band %-16s [%.2f .. %.2f]   displacement=%s"
              % (name, band, lo, hi, a["displacement_linked"]))
        if not a["bumps"]:
            print("    NO ShaderNodeBump AT ALL — zero shader relief")
        for r in a["bumps"]:
            if r["m"] is None:
                print("    %-14s amp %6.3f mm  lam    ?      %s"
                      % (r["node"], r["amp_mm"], r.get("why", "")))
            else:
                print("    %-14s amp %6.3f mm  lam %7.2f mm  slope %5.2f deg"
                      "  m %6.3f  %s"
                      % (r["node"], r["amp_mm"], r["wavelength_m"] * 1000.0,
                         r["slope_deg"], r["m"], r["verdict"]))
        if a.get("m_quadrature") is not None:
            print("    %-14s %41s m %6.3f  %s"
                  % ("ALL STAGES", "quadrature sum ->", a["m_quadrature"],
                     a["quadrature_verdict"]))
        print("")

    if jout:
        os.makedirs(os.path.dirname(jout) or ".", exist_ok=True)
        json.dump({"sun_elev_deg": elev, "amplifier": K.sun_amplifier(),
                   "bands": K.RELIEF_BANDS, "subjects": res},
                  open(jout, "w"), indent=1)
        print("[audit] wrote %s" % jout)

    print("STAGE RESULT: r2366_relief_audit PASS (%d materials audited)"
          % sum(1 for a in res if a["present"]))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        print("STAGE RESULT: r2366_relief_audit FAIL (uncaught exception)")
        sys.exit(1)
