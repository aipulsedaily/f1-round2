#!/usr/bin/env python3
"""R2-2970 CONTROLS: damage the ground cover, watch each gate fire.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -noaudio \
        -P tools/r2970_groundcover_px_control.py -- --out work/r2970/control.json

WHY
---
`tools/r2970_groundcover_px.py` says the ground-cover tier clears the measured
2.35 mm band.  On its own that sentence is worth nothing.  This project has
caught over a dozen instruments passing vacuously, including a camera gate that
cleared its own bar on a crowd looking at nothing and `tools/instance_variety.py`
printing `*** SPAM` and exiting 0.  A gate that has only ever seen good geometry
has not been tested.

So each gate is put in front of geometry that is BROKEN IN THE ONE WAY THAT GATE
EXISTS TO CATCH, and is required to say FAIL.  It is also required NOT to fail on
the other four damages, because a gate that fails on everything is a gate that
measures nothing.

THE DAMAGES ARE OF THE MECHANISM, NOT OF THE DECLARATION
--------------------------------------------------------
`leaf_unlobed` does NOT empty `LOBED_WEEDS`.  Emptying the declaration would make
the gate disappear rather than fail, and a gate that vanishes when the feature
vanishes is the exact vacuous pass this file exists to prevent.  It neuters
`_ribbon`'s lobe handling instead, so the species still DECLARES itself
pinnatifid and the mesh is not -- which is `docs/WAVE1-PEEP-SYNTHESIS.md`
PATTERN 4 reproduced on purpose.

Judge on `>> STAGE RESULT:`.  Blender 5.2 exits 0 on an uncaught exception.
"""
import argparse
import copy
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (HERE, os.path.join(ROOT, "world"), ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy                                                          # noqa: E402
import gate_exit                                                    # noqa: E402
import build_terrain as BT                                          # noqa: E402
import r2970_groundcover_px as PX                                   # noqa: E402

gate_exit.install(tool="r2970_groundcover_px_control")


def wipe():
    """Between damages, or mesh names collide and libraries accumulate."""
    for c in (bpy.data.objects, bpy.data.meshes):
        for d in list(c):
            c.remove(d, do_unlink=True)


# --- the damages ------------------------------------------------------------
def d_none():
    return lambda: None


def d_blade_thin():
    """Halve every hero blade's half-width.  The blade goes sub-pixel while the
    blade count, the tiller structure and the triangle count are all untouched
    -- i.e. exactly the defect a code review misses."""
    old = copy.deepcopy(BT.GRASS_PROF)
    for k in BT.GRASS_PROF:
        w = BT.GRASS_PROF[k]["w"]
        BT.GRASS_PROF[k]["w"] = (w[0] * 0.5, w[1] * 0.5)

    def undo():
        for k in old:
            BT.GRASS_PROF[k].update(old[k])
    return undo


def d_grit_smooth():
    """Put `shade_smooth()` back on the grit.  The 80 facets stay in the file;
    only their normals change.  This is the shipping defect, reproduced."""
    orig = BT.gen_grit_piece

    def patched(rng, matname):
        me, h = BT.gen_stone("pebble", rng, matname=matname, facet=False)
        return me, h
    BT.gen_grit_piece = patched
    PX.BT.gen_grit_piece = patched

    def undo():
        BT.gen_grit_piece = orig
        PX.BT.gen_grit_piece = orig
    return undo


def d_leaf_unlobed():
    """`LOBED_WEEDS` still declares thistle and ragwort pinnatifid; `_ribbon`
    stops honouring it.  Declared and not built."""
    orig = BT._ribbon

    def patched(*a, **kw):
        kw.pop("lobe", None)
        return orig(*a, **kw)
    BT._ribbon = patched

    def undo():
        BT._ribbon = orig
    return undo


def d_no_panicle():
    """Seed fraction to zero on every kind: no head is emitted at all."""
    old = {k: BT.GRASS_PROF[k]["seed"] for k in BT.GRASS_PROF}
    for k in BT.GRASS_PROF:
        BT.GRASS_PROF[k]["seed"] = 0.0

    def undo():
        for k, v in old.items():
            BT.GRASS_PROF[k]["seed"] = v
    return undo


def d_square_stem():
    """Weed stems back to a 4-sided tube."""
    old = BT.WEED_STEM_SIDES
    BT.WEED_STEM_SIDES = 4

    def undo():
        BT.WEED_STEM_SIDES = old
    return undo


DAMAGES = [
    # name             fn              gate(s) that MUST fail
    ("healthy",        d_none,         set()),
    ("blade_thin",     d_blade_thin,   {"blade_width"}),
    ("grit_smooth",    d_grit_smooth,  {"grit_facet"}),
    ("leaf_unlobed",   d_leaf_unlobed, {"leaf_margin"}),
    ("no_panicle",     d_no_panicle,   {"seed_head"}),
    ("square_stem",    d_square_stem,  {"stem_round"}),
]


def failing_gates(gts):
    return {g["gate"] for g in gts.values() if not g["pass_"]}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)

    sharp, _ = PX.sharp_table()
    results = {}
    healthy_gate_names = None
    for name, mk, must_fail in DAMAGES:
        wipe()
        undo = mk()
        try:
            libs = PX.build_libs(n=3, seed=20260808)
            rows = PX.measure(libs, sharp)
            gts = PX.gates(rows)
        finally:
            undo()
        got = failing_gates(gts)
        if name == "healthy":
            healthy_gate_names = sorted(gts)
        # THE GATE SET MUST NOT SHRINK.  A damage that deletes a gate instead of
        # failing it is the vacuous pass this file exists to prevent, so the
        # comparison against the healthy run is itself checked.
        shrank = sorted(set(healthy_gate_names) - set(gts))
        ok = (got >= must_fail) and (not (got - must_fail)) and not shrank
        results[name] = dict(must_fail=sorted(must_fail), failed=sorted(got),
                             gates_lost=shrank, ok=ok,
                             detail={k: dict(px=g["px"], verdict=g["verdict"],
                                             pass_=g["pass_"])
                                     for k, g in sorted(gts.items())})
        print("\n=== DAMAGE %-14s must fail %-16s -> failed %-28s %s"
              % (name, ",".join(sorted(must_fail)) or "(nothing)",
                 ",".join(sorted(got)) or "(nothing)",
                 "OK" if ok else "*** CONTROL DID NOT BEHAVE ***"))
        if shrank:
            print("    GATES LOST (a damage must FAIL a gate, not delete it): %s"
                  % ",".join(shrank))
        for k, g in sorted(gts.items()):
            if not g["pass_"]:
                print("      FAIL %-46s %5.2f %5.2f %5.2f px  %s"
                      % (k, g["px"][0], g["px"][1], g["px"][2], g["verdict"]))

    # ---- the vacuity control -----------------------------------------------
    # NOT a hand-written `nmesh == 0`: that would be this file asserting its own
    # arithmetic.  `PX.run` is called for real with a library generator that
    # builds NOTHING, and what is checked is that the tool comes back with zero
    # meshes and ZERO GATES -- i.e. that its `if nmesh == 0` refusal branch is
    # the one that fires, rather than "no gate failed, therefore clean".
    wipe()
    orig_build = PX.build_libs
    PX.build_libs = lambda *a, **kw: {"grass": {}, "grass_blades": {},
                                      "grit": {}, "weed": {}}
    try:
        vrows, vgts, vmesh = PX.run("")
    finally:
        PX.build_libs = orig_build
    vac_ok = (vmesh == 0 and len(vgts) == 0)
    results["vacuous"] = dict(meshes=vmesh, gates=len(vgts),
                              rows_from_empty=len(vrows), ok=vac_ok)
    print("\n=== VACUITY: an empty library -> %d meshes, %d gates, %d rows.  The "
          "tool must REFUSE, not report clean.  %s"
          % (vmesh, len(vgts), len(vrows), "OK" if vac_ok else "BAD"))

    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        json.dump(results, open(a.out, "w"), indent=1)
        print("\nwrote %s" % a.out)

    bad = [k for k, v in results.items() if not v["ok"]]
    if not healthy_gate_names:
        print(">> REFUSING TO REPORT: the healthy run produced no gates at all, "
              "so no control was actually exercised.")
        gate_exit.done("GROUNDCOVER_CONTROL_VACUOUS")
    elif bad:
        print(">> %d control(s) did not behave: %s" % (len(bad), ",".join(bad)))
        gate_exit.done("GROUNDCOVER_CONTROL_BROKEN", "  [%s]" % ",".join(bad))
    else:
        print(">> all %d damages fired exactly the gate they were aimed at, and "
              "no other; %d gates exercised" % (len(DAMAGES) - 1,
                                                len(healthy_gate_names)))
        gate_exit.done("GROUNDCOVER_CONTROL_OK")


if __name__ == "__main__":
    main()
