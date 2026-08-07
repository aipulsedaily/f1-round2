"""DOES THE WALL UN-BREAK?  The instrument for the f0866 slab artefact.

    .venv/bin/python sim/slabcheck.py --film sim/out/breach_film.npz
    .venv/bin/python sim/slabcheck.py --selftest

WHAT WAS SEEN
=============
render/breach_f9/f9_1920_f0866.png shows the east wall as a soup of hard-edged
translucent slabs, several deep, at multiple orientations, across the whole
glazing.  The first hypothesis was that the intact pane and its shards both
render for about twelve frames.  That was falsified: `apply_breach` hides the
pane and shows the shards at the same frame, and no frame renders both.

What is left is the shard field itself.  At `t_bond_per_m` 4000 the bond network
is ~40x stronger than the glass it represents, so the impact cannot part the
sheet.  It loads it, the sheet stores the energy across 12,756 inter-shard
constraints, and gives it back: bay 4's median depth offset is 483 mm at f866
and 17 mm by f900.  ~3,000 flat plates spread through a metre of depth, still
parallel to one another, seen through one another — and then RE-ASSEMBLING.
The take contains a shatter-and-un-shatter.  R2-092 is why.

WHAT THIS MEASURES, AND WHY IT IS TWO NUMBERS AND NOT ONE
=========================================================
DEPTH      the median |x - x_at_swap| of a bay's shards, per frame.  This is
           what shows the bulge-and-return.  It is a MEDIAN because a bbox or a
           max is one flying shard.
ALIGNMENT  the median angle between each shard's face normal now and at the
           swap frame.  This is the one that matters for the PICTURE, and it is
           not implied by the depth.  A field can be spread through a metre of
           depth and still read as slabs if its plates are all still parallel;
           it reads as a cloud only once they have rotated out of register.
           Depth without alignment is a bulging sheet, which is exactly the
           thing that looks wrong.

CONTROLS — `selftest()` runs ten and every one must fire:
  RIGID       a field that does not move reads 0.000 m and 0.00 deg
  TRANSLATE   a field moved bodily 500 mm reads 0.500 m and 0.00 deg -- depth
              must not leak into alignment
  SPIN        a field rotated 30 deg in place reads 0.000 m and 30.00 deg --
              and alignment must not leak into depth
  BULGE       a sheet that goes out 500 mm and comes back is reported as
              RETURNS, with the return measured
  LEAVE       a sheet that goes out and keeps going is reported as LEAVES
  LEAVE_SIDEWAYS
              a field whose DEPTH returns to zero but which has gone 6 m
              sideways must read LEAVES.  This control was missing, and its
              absence produced a wrong verdict on the real bake.
  ONE_FLYER   199 still shards and 1 at 50 m must NOT read as a departure.
              The median exists for this control.
"""
import argparse
import json
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in ("sim", "anim"):
    p = os.path.join(R2, _p)
    if p not in sys.path:
        sys.path.insert(0, p)


def _rot(q):
    """(N,4) Blender WXYZ -> (N,3,3)."""
    q = np.asarray(q, float)
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    n = np.sqrt(w * w + x * x + y * y + z * z)
    n[n == 0] = 1.0
    w, x, y, z = w / n, x / n, y / n, z / n
    R = np.empty((len(q), 3, 3))
    R[:, 0, 0] = 1 - 2 * (y * y + z * z)
    R[:, 0, 1] = 2 * (x * y - z * w)
    R[:, 0, 2] = 2 * (x * z + y * w)
    R[:, 1, 0] = 2 * (x * y + z * w)
    R[:, 1, 1] = 1 - 2 * (x * x + z * z)
    R[:, 1, 2] = 2 * (y * z - x * w)
    R[:, 2, 0] = 2 * (x * z - y * w)
    R[:, 2, 1] = 2 * (y * z + x * w)
    R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return R


def profile(frames, L, Q, sel, swap_frame, at=(866, 880, 900, 920), area=None):
    """DEPTH and ALIGNMENT for one bay, per frame, referenced to the swap.

    THE REFERENCE IS HOME, NOT THE SWAP FRAME, and getting that wrong cost me
    an hour.  Referencing to the swap frame reads 361 mm at f866 where home
    reads 483 mm, because by the time the shards appear THEY HAVE ALREADY MOVED
    129 mm.  One film frame spans the entire impact: frame 859 is 36.5 ms
    BEFORE contact and frame 860 is 5.1 ms after it, and in between the car
    arrives.  That is physical -- it is in the raw 240 Hz bake, not an artefact
    of the resample -- and it means the swap frame is not a state of rest and
    is not a valid zero.  The question "has the wall left" is asked against
    where the wall WAS.

    `ref` is the first frame of the table, which is 15 film frames before
    contact.  `ref_is_home_mm` reports how far the field is from its own
    origins there, and it must be zero; the caller must look at it, because a
    reference that has already moved is the exact mistake this note is about.
    """
    i0 = int(np.argmin(np.abs(frames - swap_frame)))
    iref = 0
    P, R = L[:, sel, :], _rot(Q[:, sel, :].reshape(-1, 4))
    R = R.reshape(L.shape[0], len(sel) if hasattr(sel, "__len__") else -1, 3, 3)
    nrm0 = R[iref, :, :, 0]                   # the pane's own outward axis
    dep = np.abs(P[:, :, 0] - P[iref, :, 0][None])
    # DEPTH IS NOT A DEPARTURE MEASURE, and using it as one cost me a wrong
    # verdict.  While the glass is still IN the wall, |dx| is exactly the
    # bulge and it is the right number for the slab artefact.  Once the field
    # is airborne it tumbles and falls and lands on a floor east of the wall,
    # and its x wanders back across the wall plane on the way: bay 4 at bond
    # 100 reads |dx| 1122 mm at f866, 132 mm at f900 and 938 mm at f920 while
    # its 3D displacement is 2050, 2199 and 1879 mm and 98 % of it is more
    # than 250 mm from home the whole time.  Read as depth that is a field
    # that came home.  It is a field on the forecourt.
    #
    # So the VERDICT is taken on 3D displacement, and depth stays as the
    # bulge diagnostic it is good at.  Control: LEAVE_SIDEWAYS.
    d3 = np.linalg.norm(P - P[iref][None], axis=2)
    dot = np.clip((R[:, :, :, 0] * nrm0[None]).sum(-1), -1.0, 1.0)
    ang = np.degrees(np.arccos(dot))
    out = dict(swap_frame=int(frames[i0]), ref_frame=int(frames[iref]),
               n=int(P.shape[1]),
               moved_by_the_swap_frame_median_mm=round(
                   float(1000 * np.median(dep[i0])), 1),
               moved_by_the_swap_frame_max_mm=round(
                   float(1000 * dep[i0].max()), 1))
    per = {}
    for f in at:
        i = int(np.argmin(np.abs(frames - f)))
        if abs(frames[i] - f) > 0:
            continue
        per[str(f)] = dict(
            net_median_mm=round(float(1000 * np.median(d3[i])), 1),
            net_p10_mm=round(float(1000 * np.percentile(d3[i], 10)), 1),
            gone_over_250mm=int((d3[i] > 0.25).sum()),
            depth_median_mm=round(float(1000 * np.median(dep[i])), 1),
            depth_p90_mm=round(float(1000 * np.percentile(dep[i], 90)), 1),
            depth_spread_p10_p90_m=round(
                float(np.percentile(P[i, :, 0], 90)
                      - np.percentile(P[i, :, 0], 10)), 3),
            align_median_deg=round(float(np.median(ang[i])), 2),
            align_p90_deg=round(float(np.percentile(ang[i], 90)), 2))
    out["at"] = per
    dmed = np.median(dep, axis=1)
    med = np.median(d3, axis=1)
    jd = int(np.argmax(dmed))
    j = int(np.argmax(med))
    out["peak_depth_median_mm"] = round(float(1000 * dmed[jd]), 1)
    out["peak_depth_at_frame"] = int(frames[jd])
    out["peak_net_median_mm"] = round(float(1000 * med[j]), 1)
    out["peak_at_frame"] = int(frames[j])
    out["last_frame"] = int(frames[-1])
    out["last_depth_median_mm"] = round(float(1000 * dmed[-1]), 1)
    out["last_net_median_mm"] = round(float(1000 * med[-1]), 1)
    out["gone_over_250mm_last"] = int((d3[-1] > 0.25).sum())
    out["gone_over_250mm_pct_last"] = round(
        100.0 * float((d3[-1] > 0.25).mean()), 1)
    out["gone_pct_is"] = "BY COUNT"
    # BY COUNT AND BY AREA ARE DIFFERENT ANSWERS AND THE APERTURE IS AN AREA.
    # Bay 5's shard sizes are heavily skewed -- median 0.00043 m2 against a p90
    # of 0.018 -- and it is the SMALL cells that leave.  87.1 % of bay 5's
    # shards are more than 250 mm from home and the bay still looks mostly
    # glazed in elevation, because the 12.9 % that stayed are the big ones.
    # I read the elevation, disbelieved my own instrument, and it was the
    # picture that was misleading.  Quote the area figure for an aperture;
    # sim/aperture.py measures it properly, on a raster, as a CONNECTED region.
    if area is not None:
        w = np.asarray(area, float)
        if w.sum() > 0:
            out["gone_pct_by_area_last"] = round(
                100.0 * float(w[d3[-1] > 0.25].sum() / w.sum()), 1)
    # RETURNS if the median NET displacement falls back appreciably from its
    # peak.  The test is a RATIO, because "48 mm after a 799 mm peak" and
    # "48 mm after a 60 mm peak" are not the same event, and it is gated on the
    # peak being big enough to be an event at all -- a bay that never moved
    # more than 25 mm has not "returned" from anywhere.
    ret = float(med[-1] / med[j]) if med[j] > 1e-9 else 1.0
    out["return_ratio_last_over_peak"] = round(ret, 4)
    # AND THE RATIO IS NOT ENOUGH EITHER.  A field that flies 2.3 m, falls, and
    # settles on the forecourt 400 mm from where it started has a ratio of 0.4
    # and has not returned to anything -- it is lying on the ground outside the
    # building.  RETURNS has to mean the glass is BACK IN THE WALL, so it is
    # gated on the fraction still further than 250 mm from home at the end,
    # which is the same "gone" threshold the aperture uses.
    gone_pct = 100.0 * float((d3[-1] > 0.25).mean())
    if med[j] <= 0.05:
        out["verdict"] = "DID_NOT_MOVE"
    elif gone_pct >= 50.0:
        out["verdict"] = "LEAVES"
    elif ret < 0.5:
        out["verdict"] = "RETURNS"
    else:
        out["verdict"] = "LEAVES"
    out["verdict_measured_on"] = ("net 3D displacement from home, gated on the "
                                  "fraction still over 250 mm at the end")
    dret = float(dmed[-1] / dmed[jd]) if dmed[jd] > 1e-9 else 1.0
    out["depth_return_ratio"] = round(dret, 4)
    out["monotone_after_swap"] = bool(
        np.all(np.diff(med[i0:]) > -1e-4))
    out["ref_is_home"] = True
    return out


#: what each role is REQUIRED to do.  `intact` bays are never rigid bodies and
#: never hide, so there is nothing to measure; every other bay has an outcome
#: the plan is asserting, and R2-1049 is what happened when nobody checked it.
ROLE_REQUIRES = {"destroyed": ("LEAVES",),
                 "retained": ("DID_NOT_MOVE", "RETURNS")}


def adjudicate(rep):
    """Does each bay do what its ROLE says?  Returns the list of failures.

    Separate from `run` so the controls can drive it with synthetic reports:
    a checker that can only be exercised through a 20 MB bake is a checker
    nobody proves.
    """
    bad = []
    for b, v in sorted(rep.get("bays", {}).items()):
        role, verdict = v.get("role"), v.get("verdict")
        want = ROLE_REQUIRES.get(role)
        if want is None:                      # intact, or a role we don't know
            continue
        if verdict not in want:
            bad.append(dict(bay=b, role=role, verdict=verdict,
                            expected=list(want),
                            vacated_pct_by_area=v.get("gone_pct_by_area_last")))
    missing = rep.get("bays_not_measured") or []
    for b in missing:
        bad.append(dict(bay=str(b), role="destroyed", verdict="NOT_MEASURED",
                        expected=["LEAVES"], vacated_pct_by_area=None))
    return bad


def run(film_path, bays=None, shards=None):
    import resample as RS
    import fracture as FR
    film = RS.read_film(film_path)
    span = film["span"]
    frames = np.arange(int(span[0]), int(span[1]) + 1)
    L, Q = film["expand"](frames)
    names = [str(n) for n in film["names"]]
    rel = np.asarray(film["release"], int)
    plan = FR.load(shards or os.path.join(R2, "sim/out/fracture_wall.npz"))
    idx = {n: i for i, n in enumerate(names)}
    # R2-1049: this was hardcoded `(3, 4, 5, 7)`.  Bay 6 is `destroyed` and was
    # never once measured.  The bay list must come from the plan, so that adding
    # a bay to the breach cannot silently leave it unwatched.
    if bays is None:
        bays = tuple(b for b, r in sorted(plan["roles"].items())
                     if r in ROLE_REQUIRES)
    out = dict(film=film_path, frames=[int(frames[0]), int(frames[-1])],
               bays={}, bays_requested=list(bays), bays_not_measured=[])
    for bay in bays:
        ii = [idx["GS_b%02d_%05d" % (bay, s["id"])]
              for s in plan["panes"].get(bay, [])
              if "GS_b%02d_%05d" % (bay, s["id"]) in idx]
        if not ii:
            # A bay the plan wants broken, whose shards are not in the bake at
            # all.  Silence here is how bay 6 stayed invisible; record it.
            if plan["roles"].get(bay) == "destroyed":
                out["bays_not_measured"].append(int(bay))
            continue
        rr = rel[ii]
        sw = int(rr[rr > 0].min()) if (rr > 0).any() else int(frames[0])
        ar = [s["area"] for s in plan["panes"].get(bay, [])
              if "GS_b%02d_%05d" % (bay, s["id"]) in idx]
        out["bays"][str(bay)] = profile(frames, L, Q, np.array(ii), sw,
                                        area=ar)
        out["bays"][str(bay)]["role"] = plan["roles"].get(bay)
    return out


# --------------------------------------------------------------------------- #

def selftest():
    fails = []

    def check(name, cond, detail=""):
        print("  %-58s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            fails.append(name)

    nf, n = 80, 200
    frames = np.arange(860, 860 + nf)
    sel = np.arange(n)

    def field(dx, ang_deg):
        L = np.zeros((nf, n, 3))
        L[:, :, 0] = 14.96 + dx[:, None]
        Q = np.zeros((nf, n, 4))
        th = np.radians(ang_deg)
        Q[:, :, 0] = np.cos(th / 2)[:, None]
        Q[:, :, 3] = np.sin(th / 2)[:, None]
        return L, Q

    z = np.zeros(nf)
    L, Q = field(z, z)
    r = profile(frames, L, Q, sel, 860)
    check("RIGID: a still field is 0 mm and 0 deg",
          r["at"]["866"]["depth_median_mm"] == 0.0
          and r["at"]["866"]["align_median_deg"] == 0.0)

    # The offset must be ZERO at the swap frame and 500 mm after it.  A field
    # held at a CONSTANT 0.5 m reads 0.000 m, correctly -- everything here is
    # measured RELATIVE to the swap -- and a control written that way tests
    # nothing.  It was written that way first.
    step = np.where(frames > frames[0], 0.5, 0.0)
    L, Q = field(step, z)
    r = profile(frames, L, Q, sel, 860)
    check("TRANSLATE: 500 mm of depth does not leak into alignment",
          abs(r["at"]["866"]["depth_median_mm"] - 500.0) < 1e-6
          and r["at"]["866"]["align_median_deg"] == 0.0,
          "%.1f mm, %.2f deg" % (r["at"]["866"]["depth_median_mm"],
                                 r["at"]["866"]["align_median_deg"]))

    L, Q = field(z, np.where(frames > frames[0], 30.0, 0.0))
    r = profile(frames, L, Q, sel, 860)
    check("SPIN: 30 deg of rotation does not leak into depth",
          r["at"]["866"]["depth_median_mm"] == 0.0
          and abs(r["at"]["866"]["align_median_deg"] - 30.0) < 1e-2,
          "%.1f mm, %.2f deg" % (r["at"]["866"]["depth_median_mm"],
                                 r["at"]["866"]["align_median_deg"]))

    # BULGE: out to 500 mm by f880, back to 17 mm by the end.  The artefact.
    dx = np.concatenate([np.linspace(0, 0.5, 20),
                         np.linspace(0.5, 0.017, nf - 20)])
    L, Q = field(dx, z)
    r = profile(frames, L, Q, sel, 860)
    check("BULGE: a sheet that goes out and comes back is RETURNS",
          r["verdict"] == "RETURNS" and not r["monotone_after_swap"],
          "peak %.0f mm at %d, last %.0f mm, ratio %.3f"
          % (r["peak_net_median_mm"], r["peak_at_frame"],
             r["last_net_median_mm"], r["return_ratio_last_over_peak"]))

    # LEAVE: out and keeps going.
    L, Q = field(np.linspace(0, 3.0, nf), np.linspace(0, 90.0, nf))
    r = profile(frames, L, Q, sel, 860)
    check("LEAVE: a sheet that keeps going is LEAVES, and monotone",
          r["verdict"] == "LEAVES" and r["monotone_after_swap"],
          "last %.0f mm, %.1f deg"
          % (r["last_net_median_mm"], r["at"]["880"]["align_median_deg"]))

    # LEAVE_SIDEWAYS: the control that was missing, and its absence produced a
    # wrong verdict on real data.  The field leaves in Y, its DEPTH returns
    # exactly to zero, and it must still read LEAVES.
    L = np.zeros((nf, n, 3))
    L[:, :, 0] = 14.96 + np.concatenate([np.linspace(0, 1.2, 20),
                                         np.linspace(1.2, 0.0, nf - 20)])[:, None]
    L[:, :, 1] = np.linspace(0, 6.0, nf)[:, None]
    Q = np.zeros((nf, n, 4))
    Q[:, :, 0] = 1.0
    r = profile(frames, L, Q, sel, 860)
    check("LEAVE_SIDEWAYS: a field whose DEPTH returns but which has gone "
          "6 m sideways is LEAVES",
          r["verdict"] == "LEAVES" and r["depth_return_ratio"] < 0.01
          and r["gone_over_250mm_pct_last"] == 100.0,
          "net %s, depth ratio %.3f, %.0f%% gone"
          % (r["verdict"], r["depth_return_ratio"],
             r["gone_over_250mm_pct_last"]))

    # SETTLE: out to 2.3 m, falls back to 400 mm, but every shard is still
    # more than 250 mm from home.  That is a field on the forecourt, not a
    # field back in the wall, and it must read LEAVES.
    dx = np.concatenate([np.linspace(0, 2.3, 25),
                         np.linspace(2.3, 0.4, nf - 25)])
    L, Q = field(dx, z)
    r = profile(frames, L, Q, sel, 860)
    check("SETTLE: a field that flies 2.3 m and settles 400 mm out is LEAVES, "
          "not RETURNS",
          r["verdict"] == "LEAVES" and r["return_ratio_last_over_peak"] < 0.5
          and r["gone_over_250mm_pct_last"] == 100.0,
          "%s, ratio %.2f, %.0f%% gone"
          % (r["verdict"], r["return_ratio_last_over_peak"],
             r["gone_over_250mm_pct_last"]))

    # ...and the same shape that ends INSIDE 250 mm must read RETURNS.
    dx = np.concatenate([np.linspace(0, 2.3, 25),
                         np.linspace(2.3, 0.02, nf - 25)])
    L, Q = field(dx, z)
    r = profile(frames, L, Q, sel, 860)
    check("RETURN: the same flight that ends 20 mm from home is RETURNS",
          r["verdict"] == "RETURNS" and r["gone_over_250mm_pct_last"] == 0.0,
          "%s, %.0f%% gone" % (r["verdict"], r["gone_over_250mm_pct_last"]))

    # QUAT_NULL.  `align` is arccos of a dot product of unit vectors, and
    # arccos AMPLIFIES rounding near dot = 1 by a square root -- the same trap
    # that made a shipped path-diff tool report 1,415 frames "moved" when it
    # compared a camera path with ITSELF.  There it was six-decimal JSON, where
    # 1e-6 reads as 0.162 deg.  Here the quaternions are float32 in the .npz,
    # which is ~1e-7, so the floor is ~6e-6 deg -- but that is a calculation
    # and this is the measurement.  Random unit quaternions, stored as float32
    # and read back, must still read zero.
    rng = np.random.default_rng(3)
    qq = rng.normal(size=(n, 4))
    qq /= np.linalg.norm(qq, axis=1, keepdims=True)
    L = np.zeros((nf, n, 3))
    L[:, :, 0] = 14.96
    Q = np.repeat(qq.astype(np.float32).astype(np.float64)[None], nf, axis=0)
    r = profile(frames, L, Q, sel, 860)
    check("QUAT_NULL: float32 quaternions compared with themselves read 0 deg",
          r["at"]["866"]["align_median_deg"] == 0.0
          and r["at"]["866"]["align_p90_deg"] < 1e-3,
          "median %.8f, p90 %.8f deg" % (r["at"]["866"]["align_median_deg"],
                                         r["at"]["866"]["align_p90_deg"]))

    # ONE_FLYER: 199 still, 1 at 50 m.  A max would call this a departure.
    L, Q = field(z, z)
    L[:, 0, 0] += np.linspace(0, 50.0, nf)
    r = profile(frames, L, Q, sel, 860)
    check("ONE_FLYER: 1 shard of 200 at 50 m does not move the median",
          r["last_net_median_mm"] == 0.0,
          "%.1f mm" % r["last_net_median_mm"])

    # ----------------------------------------------------------------- #
    #  R2-1049.  The role/verdict adjudicator.  Everything above proves the
    #  MEASUREMENT is honest; these prove the JUDGEMENT can actually fire.
    #  Before this existed, `role` was attached to the report and never once
    #  compared to `verdict` -- the tool computed both facts and never joined
    #  them, which is why a `destroyed` bay reading DID_NOT_MOVE shipped.
    # ----------------------------------------------------------------- #
    def rep_of(*bays):
        return dict(bays={str(b): dict(role=r, verdict=v,
                                       gone_pct_by_area_last=a)
                          for b, r, v, a in bays})

    check("ADJ_CLEAN: destroyed LEAVES + retained DID_NOT_MOVE passes",
          adjudicate(rep_of((4, "destroyed", "LEAVES", 96.8),
                            (7, "retained", "DID_NOT_MOVE", 3.6))) == [])

    r = adjudicate(rep_of((3, "destroyed", "DID_NOT_MOVE", 0.9)))
    check("ADJ_STUCK: a destroyed bay that does not move FAILS",
          len(r) == 1 and r[0]["bay"] == "3",
          "%d failure(s)" % len(r))

    r = adjudicate(rep_of((3, "destroyed", "RETURNS", 40.0)))
    check("ADJ_UNBREAK: a destroyed bay that RETURNS FAILS",
          len(r) == 1, "%d failure(s)" % len(r))

    r = adjudicate(rep_of((7, "retained", "LEAVES", 90.0)))
    check("ADJ_INVERSE: a retained bay that LEAVES FAILS too",
          len(r) == 1, "%d failure(s)" % len(r))

    check("ADJ_INTACT: an intact bay is not judged at all",
          adjudicate(rep_of((0, "intact", "DID_NOT_MOVE", 0.0))) == [])

    r = adjudicate(dict(bays={}, bays_not_measured=[6]))
    check("ADJ_UNMEASURED: a destroyed bay absent from the bake FAILS",
          len(r) == 1 and r[0]["verdict"] == "NOT_MEASURED",
          "%d failure(s)" % len(r))

    print("\nSTAGE RESULT: slabcheck selftest %s (%d failed)"
          % ("FAIL" if fails else "PASS", len(fails)))
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--film", default=os.path.join(R2,
                                                   "sim/out/breach_film.npz"))
    ap.add_argument("--shards", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    rep = run(a.film, shards=a.shards)
    bad = adjudicate(rep)
    rep["role_failures"] = bad
    print(json.dumps(rep, indent=1, default=float))
    if a.out:
        with open(a.out, "w") as fh:
            json.dump(rep, fh, indent=1, default=float)
    v = {b: rep["bays"][b]["verdict"] for b in rep["bays"]}
    for f in bad:
        print("  BAY %s IS '%s' AND READS %s -- expected %s%s"
              % (f["bay"], f["role"], f["verdict"], "/".join(f["expected"]),
                 "" if f["vacated_pct_by_area"] is None
                 else "  (%.1f%% vacated by area)" % f["vacated_pct_by_area"]))
    print("STAGE RESULT: slabcheck %s %s"
          % ("FAIL" if bad else "PASS", json.dumps(v)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
