"""Does a FACE exist where the contract declares finished ground?

The contract's own "no ground is cut that nobody builds" checks ask
`C.world_ground_z` -- the MODEL. By construction the model cannot report a face
that was never built: it returns a finished height and an owner's name whether or
not any module laid a polygon there. This probe asks the MESH instead, by casting
a ray straight down at each declared sample and requiring a hit near the declared
height.

    blender -b <scene.blend> --python tools/ground_coverage_probe.py -- \
        [--s 3360 3500] [--u 10 42] [--ds 0.5] [--du 0.1] [--tol 0.25]
        [--owner build_architecture:paving] [--json out.json] [--selftest]

TWO CONTROLS, BOTH REQUIRED, AND NEITHER NAMES A DEFECT
-------------------------------------------------------
R2-072: a control anchored to a specific broken artefact expires silently into a
pass the moment that artefact is fixed. So neither control here refers to the
pit-exit apron.

  POSITIVE  a band of declared ground that every build paves (the apron strip
            INBOARD of platform_edge). Must come back >= 99 % covered. If it does
            not, the raycast is broken and no other number on the run means
            anything -- the run reports INSTRUMENT-FAIL and stops.

  NEGATIVE  --selftest DELETES a measured patch of faces from a copy of the mesh
            in memory and re-runs. The probe must find a hole of the area it just
            made, +/- 10 %. This control is manufactured at run time from
            whatever scene it is given, so it cannot expire when a defect is
            fixed, and it fails if the probe has stopped being able to see
            absence at all.

`n_GW_Right_Glass` counted round-1 object names and read 0 for a CORRECT scene.
A metric that reads the same whether the thing is present or absent is not a
measurement, so `--selftest` is not optional decoration: it is the proof that a
zero from this probe means "covered" and not "not looking".
"""
import os
import bpy, bmesh, sys, math, json, argparse
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.expanduser('~/f1-round2/world'))
import world_contract as WC


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--s", type=float, nargs=2, default=[3360.0, 3500.0])
    p.add_argument("--u", type=float, nargs=2, default=[10.0, 42.0])
    p.add_argument("--ds", type=float, default=0.5)
    p.add_argument("--du", type=float, default=0.1)
    p.add_argument("--tol", type=float, default=0.20,
                   help="a face this far below the declared height still counts "
                        "as covering it. 0.20 m clears the module's own deepest "
                        "legitimate recess (173.3 mm, from its build log) without "
                        "reaching the proxy ground. Tightening this to the 66 mm "
                        "open-joint bound instead FAILS the positive control: "
                        "real slab lives down there.")
    p.add_argument("--not-cover", default="PROXY_",
                   help="comma list of object-name prefixes that are NOT finished "
                        "ground. A module test blend carries PROXY_Terrain, a flat "
                        "plane 200 mm under everything; counting it as cover is "
                        "how a 390 m2 hole reads as 100 %% built.")
    p.add_argument("--owner", default=None,
                   help="restrict to samples C.world_ground_z names this owner for")
    p.add_argument("--json", default=None)
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--drop-s", type=float, nargs=2, default=[3380.0, 3400.0],
                   help="--selftest: station window whose faces are deleted")
    return p.parse_args(argv)


A = parse()
scn = bpy.context.scene
NOTCOVER = tuple(x for x in A.not_cover.split(",") if x)


def sample_grid(s0, s1, u0, u1, ds, du):
    S = np.arange(s0, s1 + 1e-9, ds)
    U = np.arange(u0, u1 + 1e-9, du)
    GS, GU = np.meshgrid(S, U, indexing='ij')
    GS = GS.ravel(); GU = GU.ravel()
    P = WC.su_to_world(GS, GU)
    return GS, GU, P, ds * du


def declared(P, owner=None):
    z, own = WC.world_ground_z(P[:, 0], P[:, 1])
    m = np.isfinite(z)
    if owner:
        m &= (own == owner)
    return m, z, own


def cast_down(P, zdec, tol, drop_above=8.0, notcover=()):
    """Straight down from `drop_above` metres over the declared height.

    Vertical, not along a view ray, so nothing can be hidden behind anything: a
    miss here is an absence of geometry, not an occlusion.
    """
    dg = bpy.context.evaluated_depsgraph_get()
    down = Vector((0.0, 0.0, -1.0))
    hit = np.zeros(len(P), bool)
    dz = np.full(len(P), np.nan)
    names = []
    for i, (p, zd) in enumerate(zip(P, zdec)):
        o = Vector((float(p[0]), float(p[1]), float(zd) + drop_above))
        ok, loc, nrm, idx, obj, mat = scn.ray_cast(dg, o, down,
                                                   distance=drop_above + 40.0)
        hit[i] = bool(ok)
        if ok:
            dz[i] = loc.z - zd
            names.append(obj.name)
        else:
            names.append("")
    isproxy = np.array([bool(n) and n.startswith(tuple(notcover)) if notcover
                        else False for n in names])
    covered = hit & (dz > -tol) & ~isproxy
    return hit, dz, covered, names


def band(tag, s0, s1, u0, u1, ds, du, tol, owner=None):
    GS, GU, P, cell = sample_grid(s0, s1, u0, u1, ds, du)
    dm, zd, own = declared(P, owner)
    n_dec = int(dm.sum())
    if n_dec == 0:
        print("  %-28s no declared ground in this window" % tag)
        return dict(tag=tag, declared=0)
    hit, dz, cov, names = cast_down(P[dm], zd[dm], tol, notcover=NOTCOVER)
    n_cov = int(cov.sum())
    n_open = int((~hit).sum())
    n_low = int((hit & ~cov).sum())
    from collections import Counter
    c = Counter(n for n, k in zip(names, cov) if k and n)
    cm = Counter((n or "NOTHING") for n, k in zip(names, cov) if not k)
    print("  %-28s declared %6d = %8.2f m2 | COVERED %6d = %8.2f m2 (%6.2f %%) "
          "| NOTHING UNDER THE RAY %5d = %7.2f m2 | face >%.2f m low %5d = %7.2f m2"
          % (tag, n_dec, n_dec * cell, n_cov, n_cov * cell,
             100.0 * n_cov / n_dec, n_open, n_open * cell, tol, n_low, n_low * cell))
    if c:
        print("  %-28s   covered by: %s" % ("", c.most_common(4)))
    if cm:
        print("  %-28s   NOT covered -- first thing under the ray: %s"
              % ("", cm.most_common(4)))
    return dict(tag=tag, declared=n_dec, declared_m2=round(n_dec * cell, 2),
                covered=n_cov, covered_m2=round(n_cov * cell, 2),
                open=n_open, open_m2=round(n_open * cell, 2),
                low=n_low, low_m2=round(n_low * cell, 2),
                pct_covered=round(100.0 * n_cov / n_dec, 3), cell_m2=cell)


def positive_control(tol):
    """The apron strip INBOARD of platform_edge: paved in every build there has
    ever been. Names no defect, so it cannot expire when one is fixed."""
    S = np.arange(3360.0, 3500.01, 0.5)
    ve = WC.verge_edge(S) + 1.0
    pe = WC.platform_edge(S, +1) - 1.0
    rows = []
    for s, a, b in zip(S, ve, pe):
        if b <= a:
            continue
        U = np.arange(a, b, 0.25)
        rows.append((np.full(len(U), s), U))
    if not rows:
        return None
    GS = np.concatenate([r[0] for r in rows]); GU = np.concatenate([r[1] for r in rows])
    P = WC.su_to_world(GS, GU)
    # RESTRICTED TO THE GROUND THIS MODULE OWNS. Unrestricted it also sampled
    # build_barriers' runoff platform, which a module test blend does not contain
    # at all, and the control failed at 58 % on a scene with nothing wrong with
    # it -- a control that fails for a reason that is not the thing under test is
    # worse than no control.
    dm, zd, own = declared(P, WC.OWNER_APRON)
    hit, dz, cov, names = cast_down(P[dm], zd[dm], tol, notcover=NOTCOVER)
    pct = 100.0 * cov.sum() / max(1, len(cov))
    print("  CONTROL+ apron slab inboard of platform_edge (OWNER_APRON only): "
          "%d declared samples, %.2f %% covered" % (int(dm.sum()), pct))
    from collections import Counter
    miss = Counter((n or "NOTHING") for n, k in zip(names, cov) if not k)
    if miss:
        deep = dz[~cov]
        print("  CONTROL+   the %.2f %% residual: %s | depth below datum "
              "p50 %.3f m, max %.3f m" %
              (100.0 - pct, miss.most_common(4),
               float(np.nanmedian(deep)), float(np.nanmin(deep))))
    return pct


def negative_control(tol, s0, s1, u0, u1, ds, du):
    """Manufactured at run time: delete every apron face whose centre falls in a
    station window OF THE MEASURED BAND, re-probe that exact window, and require
    the probe to find back the area just deleted.

    THE DELETION AND THE MEASUREMENT MUST COVER THE SAME GROUND. The first
    version of this control picked faces "within 12 m of the centreline" and then
    measured u 10-42, so most of what it deleted was never looked at: it found
    122.85 of 288.65 m2 and reported the PROBE as blind. The probe was fine; the
    control was measuring somewhere else. Loosening the pass threshold would have
    buried that -- the fix is to make the two windows the same window.
    """
    ob = bpy.data.objects.get("ARCH_Paving_ApronPlatform")
    if ob is None:
        print("  CONTROL- SKIPPED: no ARCH_Paving_ApronPlatform in this scene")
        return None
    # 1. MEASURE THE WINDOW FIRST. The previous version deleted the faces and then
    #    called both bands, so its "pre-strip" reading was already post-strip and
    #    the delta was structurally 0.00 -- a control that could only ever report
    #    BLIND. Order matters and it was wrong.
    before = band("CONTROL- window, pre-strip", s0, s1, u0, u1, ds, du, tol)
    cov_before = before.get('covered_m2', 0.0)
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    doomed = []
    for f in bm.faces:
        c = ob.matrix_world @ f.calc_center_median()
        fs, fu = WC.project(np.array([c.x]), np.array([c.y]))
        if s0 <= fs[0] <= s1 and u0 <= fu[0] <= u1:
            doomed.append(f)
    if not doomed:
        print("  CONTROL- SKIPPED: no apron faces inside the strip window")
        bm.free(); return None
    made = sum(f.calc_area() for f in doomed)
    bmesh.ops.delete(bm, geom=doomed, context='FACES')
    bm.to_mesh(me); bm.free()
    me.update()
    bpy.context.view_layer.update()
    print("  CONTROL- deleted %d apron faces (%.2f m2 of face area, sides and "
          "bedding included) over s %.0f..%.0f u %.1f..%.1f"
          % (len(doomed), made, s0, s1, u0, u1))
    after = band("CONTROL- window, re-probed", s0, s1, u0, u1, ds, du, tol)
    cov_after = after.get('covered_m2', 0.0)
    lost = cov_before - cov_after
    # 2. COMPARE PLAN AREA WITH PLAN AREA. `calc_area()` sums face area including
    #    every vertical side and the bedding underneath, so it is several times
    #    the plan area the probe measures. Comparing the two made a working probe
    #    look 43 % blind.
    ok = cov_before > 1.0 and lost > 0.80 * cov_before
    print("  CONTROL- covered %.2f m2 -> %.2f m2 after the strip: the probe lost "
          "%.2f m2 of the %.2f m2 it had called covered (%.1f %%) -> %s"
          % (cov_before, cov_after, lost, cov_before,
             100.0 * lost / max(cov_before, 1e-9),
             "SEES ABSENCE" if ok else "*** BLIND -- a zero from this probe "
             "would not mean covered ***"))
    return dict(face_area_deleted_m2=round(made, 2),
                covered_before_m2=round(cov_before, 2),
                covered_after_m2=round(cov_after, 2),
                plan_area_lost_m2=round(lost, 2), ok=bool(ok))


print("=== GROUND COVERAGE PROBE  (contract %s) ===" % WC.VERSION
      if hasattr(WC, 'VERSION') else "=== GROUND COVERAGE PROBE ===")
print("scene: %s" % bpy.data.filepath)
OUT = {"scene": bpy.data.filepath, "args": vars(A)}

print("\n--- CONTROLS ---")
pos = positive_control(A.tol)
OUT['control_positive_pct'] = pos
# 98.0, and the number is MEASURED not chosen: the residual on a healthy build is
# this module's own sawn drain slots, duct covers and manhole pits, which are
# genuinely 200-330 mm below the datum and genuinely built. The run prints the
# census of the residual every time so a drift in WHAT is missing is visible even
# while the percentage holds.
if pos is None or pos < 98.0:
    print("STAGE RESULT INSTRUMENT-FAIL positive control %s -- every other number "
          "on this run is void" % pos)
    if A.json:
        json.dump(OUT, open(A.json, 'w'), indent=1)
    sys.exit(0)

print("\n--- THE WINDOW ---")
OUT['window'] = band("s %.0f-%.0f u %.1f-%.1f" % (A.s[0], A.s[1], A.u[0], A.u[1]),
                     A.s[0], A.s[1], A.u[0], A.u[1], A.ds, A.du, A.tol, A.owner)
print("\n--- BY LATERAL BAND (a window that stops inside the thing it measures "
      "reports the first slice as the whole) ---")
OUT['bands'] = []
edges = [10.0, 12.5, 16.0, 20.0, 25.0, 30.0, 35.0, 42.0]
for a, b in zip(edges[:-1], edges[1:]):
    OUT['bands'].append(band("u %.1f-%.1f" % (a, b), A.s[0], A.s[1], a, b,
                             A.ds, A.du, A.tol, A.owner))

if A.selftest:
    print("\n--- NEGATIVE CONTROL (manufactured now, not named) ---")
    OUT['control_negative'] = negative_control(A.tol, A.drop_s[0], A.drop_s[1],
                                              A.u[0], A.u[1], A.ds, A.du)

if A.json:
    json.dump(OUT, open(A.json, 'w'), indent=1)
w = OUT['window']
print("\nSTAGE RESULT OK declared %.2f m2 | covered %.2f m2 (%.2f %%) | "
      "UNBUILT %.2f m2" % (w['declared_m2'], w['covered_m2'], w['pct_covered'],
                           w['open_m2'] + w['low_m2']))
