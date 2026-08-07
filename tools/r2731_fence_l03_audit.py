#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2731_fence_l03_audit.py — IS `BR_FenceMesh_L03` STILL ON THE RACING SURFACE?

    blender -b --factory-startup -P tools/r2731_fence_l03_audit.py -- --selftest
    blender -b --factory-startup -P tools/r2731_fence_l03_audit.py -- \
        --out render/r2731/fence_l03.json

WHY IT EXISTS
-------------
R2-017 measured `BR_FenceStruct_L03` / `BR_FenceMesh_L03` at **+7.106 / +7.105 m
of inward intrusion against a 7.392 m half-width at s = 926.3** — "spans the
racing surface".  R2-666 then noticed the same object is what the raycast finds
between the lens and the car on the film's last three frames, and asked whoever
closes the intrusion to check the closing frame against it.

R2-036 fixed the CAUSE — `world_contract.barrier_offset` stepped 51.99 m in one
metre because a `1e6` sentinel survived a box filter — and shipped it in
contract 1.1.0 (now 1.2.1).  `docs/placement_report_r2.json` and
`docs/placement_after_46.json` both come back with no L03 row.  But
`docs/placement_report_cam34.json`, which is NEWER than either, still carries
the 7.6054 m row with byte-identical `at_world` coordinates to the July 29
pre-fix run — i.e. it is a stale reading, not a fresh one.

Three files, two answers, and the newest one is the one that disagrees.  So the
question is re-measured from the current source instead of adjudicated from
JSON, by the same definition R2-017's corrected gate uses:

    intrusion = half_width(s) - |u|          for the object's inboard-most vertex

positive means inside the racing surface.  `build_barriers` alone is built —
this needs no architecture, no dressing and no farm.

CONTROLS (`--selftest`), because a gate that cannot fail is not a gate
------------------------------------------------------------------------
    on-road      a synthetic object planted at u = 0 on the centreline
                 -> intrusion == half_width(s), positive, FLAGGED
    off-road     the same object at |u| = half_width + 20 m
                 -> intrusion strongly negative, NOT flagged
    the projection agrees with the generator: for a set of (s, u) built through
    `world_contract.su_to_world`, `world_su` returns the same (s, u) to 1 mm

Blender 5.2 exits 0 on an uncaught script exception.  Judge on STAGE RESULT.
"""

import json
import os
import sys
import time

import bpy
import numpy as np

T0 = time.time()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, "world"), os.path.join(ROOT, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

WATCH = ("BR_FenceMesh_L03", "BR_FenceStruct_L03",
         "BR_FenceMesh_L04", "BR_FenceStruct_L04", "BR_Armco_L03")


def log(m):
    print("[l03 %7.1fs] %s" % (time.time() - T0, m))


def measure(ob, C, stride=1):
    """Worst inward intrusion of one object, in metres, and where."""
    me = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    M = np.array(ob.matrix_world)
    w = co @ M[:3, :3].T + M[:3, 3]
    ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    if stride > 1:
        w = w[::stride]
    s, u = C.world_su(w[:, 0], w[:, 1])
    hw = C.half_width(s)
    intr = hw - np.abs(u)
    i = int(np.argmax(intr))
    return dict(object=ob.name, n_verts=n, n_tested=int(len(w)),
                max_intrusion_m=round(float(intr[i]), 4),
                at_s=round(float(s[i]), 2),
                at_u=round(float(u[i]), 4),
                half_width_m=round(float(hw[i]), 4),
                at_world=[round(float(v), 3) for v in w[i]],
                on_racing_surface=bool(intr[i] > 0.0))


def selftest(C):
    ok = True

    def chk(nm, cond, detail=""):
        nonlocal ok
        print("  %-6s %-16s %s" % ("PASS" if cond else "FAIL", nm, detail))
        ok = ok and bool(cond)

    s0 = 926.3
    hw = float(C.half_width(s0))
    # projection round-trip
    ss = np.linspace(880.0, 980.0, 41)
    uu = np.linspace(-6.0, 6.0, 41)
    W = np.array(C.su_to_world(ss, uu))
    s1, u1 = C.world_su(W[:, 0], W[:, 1])
    err = float(max(np.max(np.abs(s1 - ss)), np.max(np.abs(u1 - uu))))
    chk("roundtrip", err < 1e-3, "max (s,u) error %.6f m" % err)

    def synth(name, u):
        p = np.array(C.su_to_world(np.array([s0]), np.array([u])))[0]
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(p), (p[0] + 0.1, p[1], p[2]),
                        (p[0], p[1] + 0.1, p[2])], [], [(0, 1, 2)])
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        return o

    a = measure(synth("CTRL_OnRoad", 0.0), C)
    chk("on-road", a["on_racing_surface"] and abs(a["max_intrusion_m"] - hw) < 0.05,
        "u=0 -> intrusion %.3f, half_width %.3f" % (a["max_intrusion_m"], hw))
    b = measure(synth("CTRL_OffRoad", -(hw + 20.0)), C)
    chk("off-road", not b["on_racing_surface"] and b["max_intrusion_m"] < -19.0,
        "u=-(hw+20) -> intrusion %.3f" % b["max_intrusion_m"])
    return ok


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = "render/r2731/fence_l03.json"
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import world_contract as C
    log("world_contract v%s" % C.__version__)

    if "--selftest" in argv:
        print(">> STAGE RESULT: %s"
              % ("L03_SELFTEST_OK" if selftest(C) else "L03_SELFTEST_FAIL"))
        return
    if not selftest(C):
        print(">> STAGE RESULT: L03_SELFTEST_FAIL")
        return
    bpy.ops.wm.read_factory_settings(use_empty=True)

    log("building barriers ...")
    import build_barriers as B
    B.build()
    log("built (%d objects)" % len(bpy.data.objects))
    bpy.context.view_layer.update()

    rows = []
    for nm in WATCH:
        ob = bpy.data.objects.get(nm)
        if ob is None:
            rows.append(dict(object=nm, missing=True))
            log("%-22s NOT IN THE BUILD" % nm)
            continue
        r = measure(ob, C)
        rows.append(r)
        log("%-22s worst intrusion %+8.4f m at s=%.1f u=%+.3f (half_width "
            "%.3f)  %s" % (nm, r["max_intrusion_m"], r["at_s"], r["at_u"],
                           r["half_width_m"],
                           "ON THE RACING SURFACE" if r["on_racing_surface"]
                           else "clear"))
    bad = [r for r in rows if r.get("on_racing_surface")]
    os.makedirs(os.path.dirname(os.path.join(ROOT, out)), exist_ok=True)
    with open(os.path.join(ROOT, out), "w") as fh:
        json.dump(dict(meta=dict(tool="tools/r2731_fence_l03_audit.py",
                                 world_contract=C.__version__,
                                 built="barriers",
                                 definition="intrusion = half_width(s) - |u|, "
                                            "per vertex, worst reported; "
                                            "positive = inside the racing "
                                            "surface (R2-017's corrected gate)"),
                       rows=rows, n_on_surface=len(bad)), fh, indent=1)
    print(">> STAGE RESULT: %s"
          % ("L03_ON_SURFACE" if bad else "L03_CLEAR"))


main()
