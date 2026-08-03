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

CONTROLS — `selftest()` runs six and every one must fire:
  RIGID       a field that does not move reads 0.000 m and 0.00 deg
  TRANSLATE   a field moved bodily 500 mm reads 0.500 m and 0.00 deg -- depth
              must not leak into alignment
  SPIN        a field rotated 30 deg in place reads 0.000 m and 30.00 deg --
              and alignment must not leak into depth
  BULGE       a sheet that goes out 500 mm and comes back is reported as
              RETURNS, with the return measured
  LEAVE       a sheet that goes out and keeps going is reported as LEAVES
  ONE_FLYER   999 still shards and 1 at 50 m must NOT read as a departure.
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


def profile(frames, L, Q, sel, swap_frame, at=(866, 880, 900, 920)):
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
            depth_median_mm=round(float(1000 * np.median(dep[i])), 1),
            depth_p90_mm=round(float(1000 * np.percentile(dep[i], 90)), 1),
            depth_spread_p10_p90_m=round(
                float(np.percentile(P[i, :, 0], 90)
                      - np.percentile(P[i, :, 0], 10)), 3),
            align_median_deg=round(float(np.median(ang[i])), 2),
            align_p90_deg=round(float(np.percentile(ang[i], 90)), 2))
    out["at"] = per
    med = np.median(dep, axis=1)
    j = int(np.argmax(med))
    out["peak_depth_median_mm"] = round(float(1000 * med[j]), 1)
    out["peak_at_frame"] = int(frames[j])
    out["last_frame"] = int(frames[-1])
    out["last_depth_median_mm"] = round(float(1000 * med[-1]), 1)
    # RETURNS if the median depth falls back appreciably from its peak.  The
    # test is a RATIO, because "17 mm after a 483 mm peak" and "17 mm after a
    # 20 mm peak" are not the same event.
    ret = float(med[-1] / med[j]) if med[j] > 1e-9 else 1.0
    out["return_ratio_last_over_peak"] = round(ret, 4)
    out["verdict"] = ("RETURNS" if (ret < 0.5 and med[j] > 0.05) else "LEAVES")
    out["monotone_after_swap"] = bool(
        np.all(np.diff(med[i0:]) > -1e-4))
    out["ref_is_home"] = True
    return out


def run(film_path, bays=(3, 4, 5, 7), shards=None):
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
    out = dict(film=film_path, frames=[int(frames[0]), int(frames[-1])],
               bays={})
    for bay in bays:
        ii = [idx["GS_b%02d_%05d" % (bay, s["id"])]
              for s in plan["panes"].get(bay, [])
              if "GS_b%02d_%05d" % (bay, s["id"]) in idx]
        if not ii:
            continue
        rr = rel[ii]
        sw = int(rr[rr > 0].min()) if (rr > 0).any() else int(frames[0])
        out["bays"][str(bay)] = profile(frames, L, Q, np.array(ii), sw)
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
          % (r["peak_depth_median_mm"], r["peak_at_frame"],
             r["last_depth_median_mm"], r["return_ratio_last_over_peak"]))

    # LEAVE: out and keeps going.
    L, Q = field(np.linspace(0, 3.0, nf), np.linspace(0, 90.0, nf))
    r = profile(frames, L, Q, sel, 860)
    check("LEAVE: a sheet that keeps going is LEAVES, and monotone",
          r["verdict"] == "LEAVES" and r["monotone_after_swap"],
          "last %.0f mm, %.1f deg"
          % (r["last_depth_median_mm"], r["at"]["880"]["align_median_deg"]))

    # ONE_FLYER: 199 still, 1 at 50 m.  A max would call this a departure.
    L, Q = field(z, z)
    L[:, 0, 0] += np.linspace(0, 50.0, nf)
    r = profile(frames, L, Q, sel, 860)
    check("ONE_FLYER: 1 shard of 200 at 50 m does not move the median",
          r["last_depth_median_mm"] == 0.0,
          "%.1f mm" % r["last_depth_median_mm"])

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
    print(json.dumps(rep, indent=1, default=float))
    if a.out:
        with open(a.out, "w") as fh:
            json.dump(rep, fh, indent=1, default=float)
    v = {b: rep["bays"][b]["verdict"] for b in rep["bays"]}
    print("STAGE RESULT: slabcheck %s" % json.dumps(v))


if __name__ == "__main__":
    main()
