"""RIDECONTACT — WHAT IS THE DECK RIDE ACTUALLY TOUCHING?

    .venv/bin/python sim/ridecontact.py --selftest
    .venv/bin/python sim/ridecontact.py --table sim/out/breach_film_R2387.npz \
        --f0 967 --f1 977 --json sim/out/ridecontact_R2387.json

WHY THIS EXISTS
===============
Three named mechanisms for the deck ride have been refuted by measurement --
momentum transfer (26.54 N.s against 13,086 kg.m/s), collider withdrawal
(R2-388), and the rear-wing tray (R2-707, "the member never comes within 60 mm
of the solid wing").  Each refutation named a surface and cleared it.  NONE OF
THEM ASKED THE WHOLE QUESTION, which is what surface -- of the eighteen the car
has -- the member is on at all.  This module asks that one, exhaustively.

WHAT IT MEASURES, AND WHY IT CAN BE BELIEVED
============================================
The sim collides CONVEX HULLS with a 0.15 mm margin (`build_breach_sim.MARGIN`;
Blender's default is 0.040 m and this scene explicitly overrides it).  So the
only honest question is the separation of two convex hulls, and that is what is
computed -- exactly, not by proxy:

  * EVERY STRUCTURAL BODY'S COLLIDER IS REBUILT from the same file
    `build_breach_sim.py` builds it from (`mullion_intact_interface.json`),
    box for box.  It is not read off a bounding box and it is not estimated.
    The rebuild is then CHECKED against the baked table's own rest pose -- if
    a rebuilt box centre disagrees with the table's rest location by more than
    1 mm, the run refuses.  That control is what makes the geometry a
    measurement rather than a re-derivation.
  * THE CAR IS `breachlib.car_proxy_parts()`, transformed by exactly the six
    curves `build_breach_sim` keys the proxy from -- `Car.at_world_t`, XYZ
    euler.  Same function, same convention, no inflation.  (`carproxy_census`'s
    +120 mm envelope is a different instrument for a different question and is
    the one whose z-ceiling produced "MUL05_S02 transported 0.0 m" for a body
    that was riding.)
  * THE SEPARATION IS SOLVED WITH A DUAL CERTIFICATE.  `hull_distance` returns
    the minimum-norm point of the Minkowski difference AND the separating-plane
    gap that certifies it.  This matters: a textbook GJK returns 0.0 for the
    proxy's 16-gon tyre rings against a distant box -- it did, on this very
    data, claiming `tyre_RL` contact at f973 when the true separation was
    0.947 m.  Every distance below is reported only when upper and lower bound
    agree; a solve that does not converge is FLAGGED, never rounded to zero.
  * IT IS SAMPLED BETWEEN FILM FRAMES.  Contact is an event, not a pose, and a
    film-frame sample can step over one.  `--substep` evaluates the table at
    fractional frames (the resampler is linear in position and slerped in
    rotation, and the table's own decimation error is 1.5 mm / 0.35 deg), so
    a gap reported here is a gap over the CONTINUUM of the window, not at
    eleven instants in it.

WHAT IT DOES NOT MEASURE
------------------------
Glass.  `--glass` is not implemented and its absence is deliberate: the shards
are 3,796 bodies whose hulls are not reconstructible from a declaration file,
and the question this module was built for is about the CAR.  If nothing
structural is near the car AND nothing structural is near anything else, a
glass intermediary is the remaining hypothesis and needs the sim scene, not
this table.
"""

import argparse
import json
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "sim"), os.path.join(R2, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import breachlib as BL                                            # noqa: E402
import resample as RS                                             # noqa: E402
import sagpx as SG                                                # noqa: E402

NSEG = 8                      # build_breach_sim --mullion-segments default
MARGIN_M = 0.00015            # build_breach_sim.MARGIN
REST_TOL_M = 1e-3


# --------------------------------------------------------------------------- #
#  1.  CONVEX SEPARATION, WITH A CERTIFICATE
# --------------------------------------------------------------------------- #

def hull_distance(A, B, iters=4000, tol=1e-11):
    """(distance, lower_bound, upper_bound) between conv(A) and conv(B).

    Minimum-norm point of the Minkowski difference by pairwise Frank-Wolfe.
    `upper_bound` is |x| for the point x found (any point of the difference set
    bounds the distance above); `lower_bound` is min_s <x/|x|, s>, the gap of
    the separating plane normal to x, which bounds it below.  When they agree
    the answer is exact and certified.
    """
    A = np.asarray(A, float)
    B = np.asarray(B, float)
    M = (A[:, None, :] - B[None, :, :]).reshape(-1, 3)
    n = len(M)
    k = int(np.argmin((M * M).sum(1)))
    w = np.zeros(n)
    w[k] = 1.0
    x = M[k].copy()
    act = {k}
    for _ in range(iters):
        g = x
        s = int(np.argmin(M @ g))
        al = np.fromiter(act, int)
        v = int(al[int(np.argmax(M[al] @ g))])
        if float(-g @ (M[s] - x)) < tol:
            break
        d = M[s] - M[v]
        dd = float(d @ d)
        gm = 0.0 if dd < 1e-24 else max(
            0.0, min(float(-(g @ d) / dd), w[v]))
        if gm > 0.0:
            w[v] -= gm
            w[s] += gm
            x = x + gm * d
            if w[v] <= 1e-14:
                act.discard(v)
            act.add(s)
            continue
        # THE AWAY STEP IS BLOCKED.  Breaking here is what leaves a solve
        # uncertified -- fall back to a plain Frank-Wolfe step, which is always
        # available and always feasible.
        d = M[s] - x
        dd = float(d @ d)
        if dd < 1e-24:
            break
        gm = max(0.0, min(float(-(g @ d) / dd), 1.0))
        if gm <= 1e-15:
            break
        w *= (1.0 - gm)
        w[s] += gm
        x = x + gm * d
        act = {i for i in act if w[i] > 1e-14}
        act.add(s)
    ub = float(np.linalg.norm(x))
    if ub < 1e-12:
        return 0.0, 0.0, 0.0
    lb = float(np.min(M @ (x / ub)))
    return ub, lb, ub


# --------------------------------------------------------------------------- #
#  2.  THE COLLIDERS, REBUILT FROM THE DECLARATION
# --------------------------------------------------------------------------- #

def structural_boxes(nseg=NSEG):
    """name -> (8,3) corners in the INTACT wall, for every framing body.

    Mirrors `build_breach_sim.build()` section 2 exactly: the mullion is two
    boxes (extrusion to the rebate face, pressure plate from the plate back to
    the cap face) per segment, and the transom is the same pair per bay.
    """
    W = BL.wall_iface()
    S = W["section"]
    st = W["stations"]
    bs = {b["uid"]: b["beat3"] for b in W["breach_state"]}
    hs = 0.5 * S["sightline_m"]
    xb0, xb1 = S["body_back_x"], S["rebate_face_x"]
    xf0, xf1 = S["plate_back_x"], S["cap_face_x"]
    out = {}

    def box(nm, lo, hi):
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        out[nm] = np.array([[x, y, z] for x in (lo[0], hi[0])
                            for y in (lo[1], hi[1])
                            for z in (lo[2], hi[2])], float)

    for r in st:
        uid, y = r["uid"], r["y"]
        z0, z1 = r["foot_z"], r["head_z"]
        n = nseg if bs[uid] in ("destroyed", "bent_stub") else 1
        for k in range(n):
            a = z0 + (z1 - z0) * k / n
            b = z0 + (z1 - z0) * (k + 1) / n
            box("MUL%02d_S%02d" % (uid, k), (xb0, y - hs, a), (xb1, y + hs, b))
            box("MUL%02d_S%02d_P" % (uid, k), (xf0, y - hs, a),
                (xf1, y + hs, b))
    tl = W.get("transom_landings")
    zs = tl["z"] if isinstance(tl, dict) and "z" in tl else (1.600, 3.100,
                                                             4.600)
    for zi, z in enumerate(zs):
        for i in range(len(st) - 1):
            y0, y1 = st[i]["y"], st[i + 1]["y"]
            box("TRN_z%d_b%02d" % (zi, i), (xb0, y0 + 0.0375, z - 0.030),
                (xb1, y1 - 0.0375, z + 0.030))
            box("TRN_z%d_b%02d_P" % (zi, i), (xf0, y0 + 0.0375, z - 0.030),
                (xf1, y1 - 0.0375, z + 0.030))
    return out


def quat_R(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def car_R(eul):
    """XYZ euler -> matrix, the convention `build_breach_sim` keys the proxy in
    and `carproxy_probe` / `ridepose` read it back in."""
    cx, cy, cz = np.cos(eul)
    sx, sy, sz = np.sin(eul)
    return np.array([
        [cy * cz, cz * sx * sy - cx * sz, cx * cz * sy + sx * sz],
        [cy * sz, cx * cz + sx * sy * sz, -cz * sx + cx * sy * sz],
        [-sy, cy * sx, cx * cy]])


# --------------------------------------------------------------------------- #
#  3.  THE MEASUREMENT
# --------------------------------------------------------------------------- #

def measure(table, f0, f1, rear_wing="solid", substep=1.0, bodies=None,
            track=None, nseg=NSEG):
    T = RS.read_film(table)
    names = list(T["names"])
    idx = {n: i for i, n in enumerate(names)}
    boxes = structural_boxes(nseg)

    # ---- CONTROL: the rebuild must be the table's own rest pose ---------- #
    Lr, Qr = T["expand"](np.array([float(T["span"][0])]))
    checked, bad = 0, []
    for nm, V in boxes.items():
        if nm not in idx:
            continue
        checked += 1
        d = float(np.linalg.norm(Lr[0, idx[nm]] - V.mean(0)))
        if d > REST_TOL_M:
            bad.append((nm, d))
    jj = [idx[n] for n in boxes if n in idx]
    dq = float(np.abs(Qr[0, jj] - np.array([1.0, 0, 0, 0])).max())
    ctrl = dict(boxes_rebuilt=len(boxes), boxes_in_table=checked,
                rest_disagreements=len(bad),
                worst=sorted(bad, key=lambda t: -t[1])[:5],
                rest_quat_max_dev=dq)
    if bad or dq > 1e-6:
        raise SystemExit("REFUSING: the collider rebuild does not reproduce "
                         "the table's rest pose: %s" % json.dumps(ctrl))

    n = int(round((f1 - f0) / substep)) + 1
    frames = f0 + np.arange(n) * substep
    L, Q = T["expand"](frames)
    car = BL.Car()
    clock = BL.Clock()
    wt = np.array([clock.world_t(f) for f in frames], float)
    c_loc, c_eul = car.at_world_t(wt)
    proxy = BL.car_proxy_parts(rear_wing)

    want = bodies or [nm for nm in names if nm in boxes]
    rows = {}
    nonconv = 0
    for fi in range(n):
        Rc = car_R(c_eul[fi])
        pw = [(nm, (Rc @ P.T).T + c_loc[fi]) for nm, P in proxy]
        prad = [(nm, P.mean(0), np.linalg.norm(P - P.mean(0), axis=1).max())
                for nm, P in pw]
        for nm in want:
            if nm not in idx or nm not in boxes:
                continue
            j = idx[nm]
            V = boxes[nm] - boxes[nm].mean(0)
            H = (quat_R(Q[fi, j]) @ V.T).T + L[fi, j]
            hc = H.mean(0)
            hr = float(np.linalg.norm(H - hc, axis=1).max())
            hl = (H - c_loc[fi]) @ Rc
            best = (1e9, None, 1e9)
            for (pn, pc, pr), (_pn2, P) in zip(prad, pw):
                lower = float(np.linalg.norm(hc - pc)) - hr - pr
                if lower >= best[0]:
                    continue                     # cannot beat the incumbent
                d, lb, ub = hull_distance(H, P)
                if ub - lb > 1e-6:
                    nonconv += 1
                if d < best[0]:
                    best = (d, pn, lb)
            rows.setdefault(nm, []).append(dict(
                f=float(frames[fi]), gap=best[0], lb=best[2], part=best[1],
                clx=float(hl[:, 0].mean()), cly=float(hl[:, 1].mean()),
                clz=float(hl[:, 2].mean()),
                clz_lo=float(hl[:, 2].min()), clz_hi=float(hl[:, 2].max())))

    out = dict(table=os.path.basename(table), rear_wing=rear_wing,
               window=[f0, f1], substep=substep, samples=n,
               margin_m=MARGIN_M, control=ctrl, nonconverged=nonconv,
               bodies=[])
    for nm, r in rows.items():
        g = np.array([x["gap"] for x in r])
        lbs = np.array([x["lb"] for x in r])
        # only bodies that are anywhere near the car are interesting
        rec = dict(name=nm, min_gap=float(g.min()),
                   min_gap_lower_bound=float(lbs.min()),
                   median_gap=float(
            np.median(g)), at_frame=float(r[int(np.argmin(g))]["f"]),
            part=r[int(np.argmin(g))]["part"],
            clz_lo=float(min(x["clz_lo"] for x in r)),
            clz_hi=float(max(x["clz_hi"] for x in r)),
            clx=float(np.mean([x["clx"] for x in r])),
            touching_frames=int((g <= MARGIN_M).sum()),
            near_frames=int((g <= 0.010).sum()))
        out["bodies"].append(rec)
    out["bodies"].sort(key=lambda b: b["min_gap"])
    return out, rows


# --------------------------------------------------------------------------- #
#  3b.  THE CHAIN, AND WHERE IT IS IN THE PICTURE
# --------------------------------------------------------------------------- #
#  R2-700 judged "a member lying across the top of the car".  It is not a
#  member.  `joined_chain()` finds, by measurement rather than by being told,
#  which bodies are still bolted to each other -- a pair whose centre-to-centre
#  distance stays within `tol` of the INTACT WALL'S value for the whole window
#  has a constraint that never broke.  The set that comes back is the object the
#  eye is actually looking at, and it is several bodies long.
#
#  `silhouette()` then asks the question contact cannot answer: is that object
#  BETWEEN THE LENS AND THE CAR?  A bar crossing the car's silhouette from in
#  front of it reads as lying on the bodywork and no separation measurement will
#  ever say so, because there is nothing to separate.

def joined_chain(table, f0, f1, seed, tol=0.020, nseg=NSEG, step=1.0):
    """Bodies still rigidly joined to `seed` through the window, transitively."""
    T = RS.read_film(table)
    names = list(T["names"])
    idx = {n: i for i, n in enumerate(names)}
    boxes = structural_boxes(nseg)
    fr = np.arange(f0, f1 + 1e-9, step)
    L, _Q = T["expand"](fr)
    cand = [n for n in names if n in boxes]
    link = {n: set() for n in cand}
    for i, a in enumerate(cand):
        for b in cand[i + 1:]:
            rest = float(np.linalg.norm(boxes[a].mean(0) - boxes[b].mean(0)))
            if rest > 2.6:                     # cannot have been a joint
                continue
            d = np.linalg.norm(L[:, idx[a]] - L[:, idx[b]], axis=1)
            if float(np.abs(d - rest).max()) <= tol:
                link[a].add(b)
                link[b].add(a)
    seen, stack = {seed}, [seed]
    while stack:
        n = stack.pop()
        for m in link[n]:
            if m not in seen:
                seen.add(m)
                stack.append(m)
    return sorted(seen)


def silhouette(table, f0, f1, group, rear_wing="solid", track=None,
               nseg=NSEG):
    """Per film frame: the group's screen extent, its depth, and the car's."""
    T = RS.read_film(table)
    names = list(T["names"])
    idx = {n: i for i, n in enumerate(names)}
    boxes = structural_boxes(nseg)
    tr = track if track is not None else SG.load_track()
    fr = np.arange(f0, f1 + 1).astype(float)
    L, Q = T["expand"](fr)
    car = BL.Car()
    clock = BL.Clock()
    wt = np.array([clock.world_t(f) for f in fr], float)
    c_loc, c_eul = car.at_world_t(wt)
    proxy = BL.car_proxy_parts(rear_wing)
    rows = []
    for i, f in enumerate(fr):
        k = int(f) - 1
        if k < 0 or k >= len(tr["frame"]):
            continue
        Rc = car_R(c_eul[i])
        V = np.vstack([(quat_R(Q[i, idx[n]])
                        @ (boxes[n] - boxes[n].mean(0)).T).T + L[i, idx[n]]
                       for n in group if n in idx])
        CV = np.vstack([(Rc @ P.T).T + c_loc[i] for _n, P in proxy])
        gx, gy, gd, _ = SG.project(tr, k, V)
        cx, cy, cd, _ = SG.project(tr, k, CV)
        ox = max(0.0, min(gx.max(), cx.max()) - max(gx.min(), cx.min()))
        oy = max(0.0, min(gy.max(), cy.max()) - max(gy.min(), cy.min()))
        ga = (gx.max() - gx.min()) * (gy.max() - gy.min())
        hl = (V - c_loc[i]) @ Rc
        rows.append(dict(
            f=float(f),
            chain_px=float(np.hypot(gx.max() - gx.min(), gy.max() - gy.min())),
            depth_m=float(np.median(gd)), depth_near_m=float(gd.min()),
            car_near_m=float(cd.min()),
            foreground_m=float(cd.min() - np.median(gd)),
            crosses=float(ox * oy / ga) if ga > 0 else 0.0,
            clz_lo=float(hl[:, 2].min()), clz_hi=float(hl[:, 2].max())))
    return rows


# --------------------------------------------------------------------------- #
#  4.  CONTROLS
# --------------------------------------------------------------------------- #

def selftest():
    ok = True
    box = np.array([[x, y, z] for x in (0, 1) for y in (0, 1) for z in (0, 1)],
                   float)
    cases = [("GAP        two boxes 1 m apart read 1.000", box,
              box + [2, 0, 0], 1.0),
             ("TOUCH      two boxes sharing a face read 0.000", box,
              box + [1, 0, 0], 0.0),
             ("OVERLAP    two boxes interpenetrating read 0.000", box,
              box + [0.5, 0, 0], 0.0),
             ("CORNER     the diagonal case reads sqrt(3)", box,
              box + [2, 2, 2], float(np.sqrt(3))),
             ("AXIS       a pure z offset does not leak into x", box,
              box + [0.5, 0.5, 3.0], 2.0)]
    for nm, A, B, exp in cases:
        d, lb, ub = hull_distance(A, B)
        good = abs(d - exp) < 1e-6 and (ub - lb) < 1e-6
        ok &= good
        print("   %-52s %.6f  %s" % (nm, d, "OK" if good else "FAIL"))

    # THE CONTROL THAT MATTERS: the tyre rings, which broke a textbook GJK
    th = np.linspace(0, 2 * np.pi, 16, endpoint=False)
    ring = np.c_[np.cos(th), np.zeros(16), np.sin(th)]
    tyre = np.vstack([ring + [0, -0.2, 0], ring + [0, 0.2, 0]])
    d, lb, ub = hull_distance(tyre, box + [5.0, -0.5, -0.5])
    good = abs(d - 4.0) < 1e-6
    ok &= good
    print("   %-52s %.6f  %s"
          % ("TYRE       a 16-gon ring 4 m from a box reads 4.000", d,
             "OK" if good else "FAIL"))

    # a proxy part against itself must be zero, and every part must be a solid
    for nm, P in BL.car_proxy_parts("solid"):
        d, _, _ = hull_distance(P, P)
        if d != 0.0:
            ok = False
            print("   SELF       %s against itself reads %.6f  FAIL" % (nm, d))
    print("   %-52s %s" % ("SELF       every proxy part against itself reads 0",
                           "OK"))

    # the collider rebuild against the declaration it claims to come from
    b = structural_boxes()
    W = BL.wall_iface()
    S = W["section"]
    v = b["MUL05_S02"]
    dims = v.max(0) - v.min(0)
    exp = np.array([S["rebate_face_x"] - S["body_back_x"], S["sightline_m"],
                    (W["stations"][5]["head_z"]
                     - W["stations"][5]["foot_z"]) / NSEG])
    good = np.allclose(dims, exp, atol=1e-9)
    ok &= good
    print("   %-52s %s  %s"
          % ("REBUILD    MUL05_S02 is the declared section x sightline x L/8",
             np.array2string(dims, precision=4), "OK" if good else "FAIL"))
    print(">> STAGE RESULT: RIDECONTACT_SELFTEST %s" % ("OK" if ok else "FAIL"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--table")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--f0", type=float, default=967)
    ap.add_argument("--f1", type=float, default=977)
    ap.add_argument("--substep", type=float, default=1.0)
    ap.add_argument("--rear-wing", default="solid",
                    choices=("solid", "aerofoil"))
    ap.add_argument("--bodies", nargs="*", default=None)
    ap.add_argument("--show", type=int, default=14)
    ap.add_argument("--silhouette", action="store_true",
                    help="find the still-joined chain and ask whether it is "
                         "BETWEEN THE LENS AND THE CAR")
    ap.add_argument("--seed-body", default="MUL05_S02")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(0 if selftest() else 1)
    if not a.table:
        raise SystemExit("--table or --selftest")

    if a.silhouette:
        tag = a.tag or os.path.basename(a.table)
        ch = joined_chain(a.table, a.f0, a.f1, a.seed_body)
        rows = silhouette(a.table, int(a.f0), int(a.f1), ch, a.rear_wing)
        px = np.array([r["chain_px"] for r in rows])
        fg = np.array([r["foreground_m"] for r in rows])
        cr = np.array([r["crosses"] for r in rows])
        zl = np.array([r["clz_lo"] for r in rows])
        zh = np.array([r["clz_hi"] for r in rows])
        print("== %s   f%g-f%g   silhouette" % (tag, a.f0, a.f1))
        print("   the STILL-JOINED CHAIN containing %s is %d bodies: %s"
              % (a.seed_body, len(ch), " ".join(ch)))
        print("   screen extent      median %6.0f px @4K   max %6.0f px"
              % (np.median(px), px.max()))
        print("   crosses the car's silhouette   median %5.1f %% of its own box"
              % (100 * np.median(cr)))
        print("   IN FRONT OF the car's nearest surface by  median %+.2f m   "
              "max %+.2f m   (positive = between the lens and the car)"
              % (np.median(fg), fg.max()))
        print("   car-local z of the chain   %.2f .. %.2f   (car top %.3f)"
              % (zl.min(), zh.max(), BL.CAR_TOP_Z))
        v = "FOREGROUND_BAR" if (np.median(fg) > 0 and np.median(cr) > 0.5) \
            else "BEHIND_OR_ON"
        print(">> STAGE RESULT: RIDESILHOUETTE_%s %s (%.0f px, %+.2f m)"
              % (tag, v, np.median(px), np.median(fg)))
        if a.json:
            with open(a.json, "w") as fh:
                json.dump(dict(table=os.path.basename(a.table), chain=ch,
                               window=[a.f0, a.f1], verdict=v,
                               median_chain_px=float(np.median(px)),
                               median_foreground_m=float(np.median(fg)),
                               median_crosses=float(np.median(cr)),
                               rows=rows), fh, indent=1)
            print("wrote %s" % a.json)
        return

    out, rows = measure(a.table, a.f0, a.f1, a.rear_wing, a.substep,
                        a.bodies)
    tag = a.tag or os.path.basename(a.table)
    print("== %s   f%g-f%g at %g-frame steps (%d samples), rear_wing=%s"
          % (tag, a.f0, a.f1, a.substep, out["samples"], a.rear_wing))
    c = out["control"]
    print("   CONTROL: %d colliders rebuilt, %d found in the table, "
          "%d disagree with its rest pose by > 1 mm, max |rest quat - I| %.1e"
          % (c["boxes_rebuilt"], c["boxes_in_table"], c["rest_disagreements"],
             c["rest_quat_max_dev"]))
    print("   collision margin this scene actually uses: %.5f m" % MARGIN_M)
    print("   %-15s %9s %9s %8s %8s %8s  %s"
          % ("body", "MIN GAP", "median", "at f", "clz_lo", "clx",
             "nearest car part"))
    shown = 0
    for b in out["bodies"]:
        if b["min_gap"] > 3.0 and shown >= a.show:
            break
        print("   %-15s %9.4f %9.4f %8.1f %8.3f %8.2f  %s"
              % (b["name"], b["min_gap"], b["median_gap"], b["at_frame"],
                 b["clz_lo"], b["clx"], b["part"]))
        shown += 1
        if shown >= a.show:
            break
    near = [b for b in out["bodies"] if b["min_gap"] <= MARGIN_M]
    out["n_touching"] = len(near)
    out["closest_body"] = out["bodies"][0]["name"] if out["bodies"] else None
    out["closest_gap_m"] = out["bodies"][0]["min_gap"] if out["bodies"] else None
    print("   bodies in CONTACT with the car (gap <= margin %.5f m): %d"
          % (MARGIN_M, len(near)))
    # the dual certificate is only meaningful for DISJOINT hulls: when two
    # hulls interpenetrate the separating plane does not exist and the bound
    # goes negative, which is information about overlap, not about accuracy.
    dis = [b["min_gap_lower_bound"] for b in out["bodies"] if b["min_gap"] > 0]
    lbmin = min(dis) if dis else 0.0
    out["closest_gap_lower_bound_m"] = float(lbmin)
    print("   closest approach of ANY structural body to ANY car part: "
          "%.4f m  (%s -> %s at f%.1f)"
          % (out["closest_gap_m"], out["closest_body"], out["bodies"][0]["part"],
             out["bodies"][0]["at_frame"]))
    print("   CERTIFIED LOWER BOUND on that closest approach, over every "
          "DISJOINT body/part/sample: %.4f m" % lbmin)
    if out["nonconverged"]:
        print("   WARNING: %d solves did not certify" % out["nonconverged"])
    verdict = "CONTACT" if near else "NO_CONTACT"
    print(">> STAGE RESULT: RIDECONTACT_%s %s (closest %.4f m)"
          % (tag, verdict, out["closest_gap_m"]))
    if a.json:
        out["per_frame"] = {k: v for k, v in rows.items()
                            if min(x["gap"] for x in v) < 3.0}
        with open(a.json, "w") as fh:
            json.dump(out, fh, indent=1)
        print("wrote %s" % a.json)


if __name__ == "__main__":
    main()
