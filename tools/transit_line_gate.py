"""THE CAR IS ON THE ROAD IT IS DRIVING ON.  R2-042's gate.

    .venv/bin/python tools/transit_line_gate.py [--telemetry telemetry/telemetry.csv]
                                                [--control telemetry/pre_R2042.csv]

`tools/build_telemetry.py` used to build the transit by linearly interpolating the
four `SPEC["transit"]["legs"]` endpoints — the CHORD of a declared R150 / 40 deg
merge arc — while `world_contract.access_route_point`, which every module that
BUILDS that road reads, used the arc.  The two curves stood 9.044 m apart and the
car's swept box ran 4.643 m outboard of its own road's edge for 60.1 m of Beat 4.
See docs/R2-042-DECISION.md.

build_telemetry now imports the contract, so the arc cannot drift again by
construction.  THAT IS EXACTLY WHY THIS FILE EXISTS: a check that reads the same
implementation it is checking proves only that numpy is deterministic.  So every
check here is made TWICE, the second time from an INDEPENDENT reconstruction that
knows nothing about `world_contract` — the unique circle that leaves leg 1
tangentially and passes through leg 2's declared far endpoint, solved from
docs/circuit_spec.json alone.  The two must agree.

AND EVERY CHECK CARRIES A CONTROL.  `--control` takes a pre-fix telemetry.csv;
it MUST fail the agreement test by ~9.04 m, or the test is not measuring anything.
A synthetic 0.20 m lateral push is used as a second, always-available positive
control, and the far field as the negative one.
"""

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))
import world_contract as WC                                      # noqa: E402

TOL_ARC_M = 1.5e-4          # telemetry vs the contract.  NOT float epsilon: the
                            # CSV writes x and y to 4 decimals, so 0.05 mm of
                            # quantisation per axis is in the artefact itself and
                            # any tighter tolerance would be measuring the
                            # printf, not the geometry.
TOL_INDEP_M = 0.030         # telemetry vs the spec-only reconstruction
TOL_SEAM_M = 1.0e-9         # transit -> lap position seam
TOL_SEAM_HEAD_DEG = 0.05    # transit -> lap heading seam
CONTROL_MIN_M = 5.0         # a pre-fix file must miss the arc by at least this


def load(path):
    rows = list(csv.DictReader(open(path)))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def independent_merge(spec):
    """The merge arc, from docs/circuit_spec.json ALONE.  -> (centre, R, th0, sgn).

    Leg 1 arrives on heading 0 at leg 2's `from_world`, so the arc's centre lies on
    the normal there, at (x0, R).  Requiring it to pass through leg 2's `to_world`
    fixes R with no reference to the contract's ACCESS_* constants and no use of
    the declared 104.700 m:

        (x1-x0)^2 + (y1-R)^2 = R^2   ->   R = ((x1-x0)^2 + y1^2) / (2*y1)
    """
    legs = spec["transit"]["legs"]
    x0, y0 = legs[2]["from_world"][:2]
    x1, y1 = legs[2]["to_world"][:2]
    hdg_in = math.atan2(legs[1]["to_world"][1] - legs[1]["from_world"][1],
                        legs[1]["to_world"][0] - legs[1]["from_world"][0])
    if abs(hdg_in) > 1e-9:
        raise SystemExit("independent_merge: leg 1 is not on heading 0")
    dx, dy = x1 - x0, y1 - y0
    R = (dx * dx + dy * dy) / (2.0 * dy)
    return (x0, y0 + R), R, math.atan2(dx, R - dy)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--telemetry", default=os.path.join(ROOT, "telemetry",
                                                        "telemetry.csv"))
    ap.add_argument("--spec", default=os.path.join(ROOT, "docs",
                                                   "circuit_spec.json"))
    ap.add_argument("--control", default=None,
                    help="a PRE-FIX telemetry.csv, which must FAIL")
    a = ap.parse_args()

    spec = json.load(open(a.spec))
    legs = spec["transit"]["legs"]
    L = [float(l["length_m"]) for l in legs]
    cum = np.concatenate([[0.0], np.cumsum(L)])
    T = load(a.telemetry)
    fails, n = [], [0]

    def chk(name, ok, detail=""):
        n[0] += 1
        print("  %s  %s" % ("PASS" if ok else "FAIL", name))
        if detail:
            print("         %s" % detail)
        if not ok:
            fails.append(name)

    def route_t(s):
        """Transit station -> contract route station, BY LEG FRACTION.

        Not `s - 11.98`.  The spec rounds leg 2's arc length to 104.700 where
        R150 x 40 deg is 104.7198, so a global-station mapping arrives 19.8 mm
        short of the arc's own exit and every leg after it inherits the error.
        Each leg is mapped by its own fraction instead, which is what
        `build_telemetry.transit_path` does and why the leg nodes land where the
        spec says they do.  Check [1b] measures the 19.8 mm rather than hiding it.
        """
        f1 = np.clip((s - cum[1]) / L[1], 0.0, 1.0)
        f2 = np.clip((s - cum[2]) / L[2], 0.0, 1.0)
        return f1 * WC.ACCESS_L2 + f2 * WC.ACCESS_L3

    def arc_err(tel):
        """max |telemetry - contract route| over legs 1+2 (the apron and merge)."""
        s = tel["s_m"]
        m = (s >= cum[1]) & (s < cum[3])
        rx, ry, _ = WC.access_route_arrays(route_t(s[m]))
        return np.hypot(rx - tel["x"][m], ry - tel["y"][m]), m

    # ---------------------------------------------------------------- [1]
    print("\n[1] THE TELEMETRY IS ON THE CONTRACT'S ROAD")
    e, m = arc_err(T)
    chk("telemetry x,y == access_route_arrays over the apron and the merge",
        int(m.sum()) > 80 and float(e.max()) < TOL_ARC_M,
        "max %.3e m, mean %.3e m over %d frames (tol %g)"
        % (e.max(), e.mean(), int(m.sum()), TOL_ARC_M))
    s_all = T["s_m"]
    mm = (s_all >= cum[1]) & (s_all < cum[3])
    gx, gy, _ = WC.access_route_arrays(s_all[mm] - cum[1])
    ge = np.hypot(gx - T["x"][mm], gy - T["y"][mm])
    chk("[1b] the spec's rounded leg lengths cost less than 25 mm of station",
        float(ge.max()) < 0.025,
        "mapping by GLOBAL station instead of by leg fraction reads %.4f m — "
        "the spec declares the merge as 104.700 m and R150 x 40 deg is %.4f m"
        % (ge.max(), WC.ACCESS_L3))

    # ---------------------------------------------------------------- [2]
    print("\n[2] ... AND SO IS AN ARC THAT NEVER HEARD OF THE CONTRACT")
    (cx, cy), R, th0 = independent_merge(spec)
    s = T["s_m"]
    m2 = (s >= cum[2]) & (s < cum[3])
    f = (s[m2] - cum[2]) / L[2]
    th = f * th0
    ix = cx + R * np.sin(th)
    iy = cy - R * np.cos(th)
    ei = np.hypot(ix - T["x"][m2], iy - T["y"][m2])
    chk("a spec-only circle reproduces the driven merge",
        float(ei.max()) < TOL_INDEP_M,
        "R = %.4f m over %.4f deg (contract declares %.1f / %.1f), centre "
        "(%.3f, %.3f) vs (%.2f, %.2f); max %.4f m over %d frames"
        % (R, math.degrees(th0), WC.ACCESS_R, WC.ACCESS_ARC_DEG, cx, cy,
           WC.ACCESS_ARC_C[0], WC.ACCESS_ARC_C[1], ei.max(), int(m2.sum())))
    chk("... and it is a genuinely independent number, not a copy",
        abs(R - WC.ACCESS_R) > 1e-6,
        "R differs from the contract's by %.4f m — the spec's endpoints are "
        "rounded to 10 mm, so an exact match would mean the reconstruction had "
        "read the contract" % abs(R - WC.ACCESS_R))

    # ---------------------------------------------------------------- [3]
    print("\n[3] THE CONTROLS")
    push = dict(T)
    hdg = T["heading_rad"]
    push["x"] = T["x"] - np.sin(hdg) * 0.20
    push["y"] = T["y"] + np.cos(hdg) * 0.20
    ep, _ = arc_err(push)
    chk("POSITIVE CONTROL: a 0.20 m lateral push fails the agreement test",
        float(ep.max()) > TOL_ARC_M and abs(float(ep.max()) - 0.20) < 2.0 * TOL_ARC_M,
        "max %.6f m — the test can see 0.20 m, so it can see 9.04" % ep.max())
    far = dict(T)
    far["x"] = T["x"] + 400.0
    ef, _ = arc_err(far)
    chk("NEGATIVE CONTROL: the test is not vacuously true",
        float(ef.max()) > 100.0, "a 400 m offset reads %.1f m" % ef.max())
    if a.control:
        C = load(a.control)
        ec, mc = arc_err(C)
        chk("POSITIVE CONTROL: the PRE-FIX telemetry FAILS by the sagitta",
            float(ec.max()) > CONTROL_MIN_M
            and abs(float(ec.max())
                    - WC.ACCESS_R * (1.0 - math.cos(
                        math.radians(WC.ACCESS_ARC_DEG * 0.5)))) < 0.02,
            "max %.4f m over %d frames; R(1-cos(20 deg)) = %.4f m"
            % (ec.max(), int(mc.sum()),
               WC.ACCESS_R * (1.0 - math.cos(math.radians(
                   WC.ACCESS_ARC_DEG * 0.5)))))
    else:
        print("         (no --control given; the pre-fix file is the strongest "
              "positive control there is)")

    # ---------------------------------------------------------------- [4]
    print("\n[4] THE SEAMS — THE FILM IS ONE TAKE")
    i = int(np.searchsorted(s, cum[-1]))          # first lap frame
    x0, y0 = spec["elements"][0]["start_world"][:2]
    hdg_sf = math.radians(float(spec["datum"]["racing_direction_world_deg"]))
    # the transit's own last point, continued to the line
    tx = np.interp(cum[-1], s[i - 1:i + 1], T["x"][i - 1:i + 1])
    ty = np.interp(cum[-1], s[i - 1:i + 1], T["y"][i - 1:i + 1])
    chk("the transit arrives AT the start/finish line",
        math.hypot(tx - x0, ty - y0) < 1.0e-3,
        "extrapolated to s = %.2f: (%.4f, %.4f) vs the lap's own first point "
        "(%.4f, %.4f), %.2e m" % (cum[-1], tx, ty, x0, y0,
                                  math.hypot(tx - x0, ty - y0)))
    dxy = np.hypot(np.diff(T["x"]), np.diff(T["y"]))
    step = dxy / np.maximum(np.diff(T["t_s"]), 1e-9)
    jump = float(abs(step[i - 1] - 0.5 * (step[i - 2] + step[i])))
    chk("no position step at the transit -> lap frame",
        jump < 12.0, "frame %d -> %d moves %.4f m, %.2f m/s against %.2f and "
        "%.2f either side (the speed step at the line is R2-046, not this)"
        % (i - 1, i, dxy[i - 1], step[i - 1], step[i - 2], step[i]))
    yaw = np.degrees(np.unwrap(T["heading_rad"]))
    dyaw = np.abs(np.diff(yaw))
    mtr = s[1:] <= cum[-1]
    # A FIXED THRESHOLD WOULD BE THE WRONG INSTRUMENT.  The car yaws through the
    # merge, so "small" has to be measured against the yaw the film already has:
    # the seam step must not be an outlier among the steps around it.
    nb = np.concatenate([dyaw[i - 9:i - 1], dyaw[i + 1:i + 9]])
    chk("the heading is continuous into the lap",
        float(dyaw[i - 1]) <= float(nb.max()) + 1e-12,
        "%.5f deg across the seam against %.5f deg worst in the 16 frames "
        "either side — it was 40.0000 deg, the transit heading column having "
        "been ZERO for the whole of a 40 deg merge" % (dyaw[i - 1], nb.max()))
    chk("no yaw snap anywhere in the transit",
        float(dyaw[mtr].max()) < 1.5,
        "worst %.4f deg/frame at frame %d (the chord's leg nodes were 16.209 "
        "and 15.720)" % (dyaw[mtr].max(), int(np.argmax(dyaw[mtr])) + 1))

    # ---------------------------------------------------------------- [5]
    print("\n[5] THE CAR IS ON ITS OWN ROAD")
    t, v = WC.access_project(T["x"], T["y"])
    on = (t >= 0.0) & (t <= WC.ACCESS_TOTAL) & (np.abs(v) < 14.0) & (s <= cum[-1])
    vi, vo = WC.access_edges(np.clip(t[on], 0.0, WC.ACCESS_TOTAL))
    out = (v[on] + WC.CAR_SWEPT_HALF_W_M) - vo
    chk("the swept car box stays inboard of the ribbon's outboard edge",
        float(out.max()) < 0.0,
        "worst %+.4f m (it was +4.643 m, over 60.1 m of Beat 4)" % out.max())
    merge = on & (s < cum[3])
    chk("... and on the merge itself the offset is GONE, not reduced",
        float(np.abs(v[merge]).max()) < TOL_ARC_M,
        "max |offset from the declared route centreline| %.2e m over %d frames "
        "of apron and merge (it was 9.0406 m)"
        % (np.abs(v[merge]).max(), int(merge.sum())))

    # LEG 3 IS NOT ON THE ROUTE CENTRELINE AND MUST NOT BE.  The arc exits 5.023 m
    # left of the racing centreline and `access_route_point` keeps that offset for
    # ever, so a car that stayed on it would cross the start/finish line 5.02 m
    # wide of the lap's own first point.  It converges instead, on a smoothstep,
    # and the only thing that has to be true of that convergence is that it is
    # monotonic and stays on road.
    tr = s <= cum[-1]
    S3, U3 = WC.project(T["x"][tr & (s >= cum[3])], T["y"][tr & (s >= cum[3])])
    chk("leg 3 converges onto the racing centreline, monotonically",
        float(U3[0]) > 5.0 and abs(float(U3[-1])) < 0.01
        and float(np.diff(U3).max()) < 1e-9,
        "lap u %+.4f -> %+.4f over %d frames, never once increasing"
        % (U3[0], U3[-1], len(U3)))
    # LEG 0 IS INDOORS.  `project` returns nonsense for a car 300 m from the lap
    # and standing on the showroom floor, so the surface test starts at the glass.
    tr1 = tr & (s >= cum[1])
    Sa, Ua = WC.project(T["x"][tr1], T["y"][tr1])
    paved = np.abs(Ua) <= WC.verge_edge(Sa)
    rib = np.asarray(WC.in_access_ribbon(T["x"][tr1], T["y"][tr1]), bool)
    chk("every transit frame outside the glass is on built surface "
        "— ribbon or paved cross-section",
        bool(np.all(paved | rib)),
        "%d frames on the ribbon, %d inside the paved cross-section "
        "(worst |u| %.3f m against a verge edge of %.2f m)"
        % (int(rib.sum()), int(paved.sum()), np.abs(Ua[paved]).max(),
           float(WC.verge_edge(Sa[paved][np.argmax(np.abs(Ua[paved]))]))))
    # REPORTED, NOT GATED.  `transit_keepout` is the union of the ribbon and the
    # OLD chord line; the new curve is a third line and the union does not have to
    # contain it.  Where it does not, the car is on the racing surface, where the
    # keep-out is not the thing that protects it.
    ko = np.asarray(WC.transit_keepout(T["x"][tr1], T["y"][tr1]), bool)
    out_ko = ~ko
    print("  ---- transit_keepout covers %.1f %% of the driven transit frames"
          % (100.0 * ko.mean()))
    if out_ko.any():
        print("         the %d it does not are s %.1f-%.1f m, lap u %+.2f..%+.2f "
              "against a verge edge of %.2f — on the track, not beside it"
              % (int(out_ko.sum()), s[tr1][out_ko].min(), s[tr1][out_ko].max(),
                 Ua[out_ko].min(), Ua[out_ko].max(),
                 float(WC.verge_edge(Sa[out_ko])[0])))

    print("\n%s  (%d checks, %d failed)%s"
          % ("PASS" if not fails else "FAIL", n[0], len(fails),
             "" if not fails else "\n  " + "\n  ".join(fails)))
    print(">> STAGE RESULT: %s" % ("TRANSIT_LINE_OK" if not fails
                                   else "TRANSIT_LINE_FAIL"))
    return 0 if not fails else 1



# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised: `blender -b -P x.py`
    # prints the traceback and exits 0, MEASURED on this box. A gate that
    # crashed was indistinguishable from one that passed. guard() makes an
    # uncaught exception a status 2 and passes any real verdict through
    # unchanged. One shared helper, not N copies -- see tools/gate_exit.py.
    gate_exit.guard(main, tool="transit_line_gate")
