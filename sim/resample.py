"""RESAMPLE — the world-time bake becomes film-frame keys, and gets smaller.

    .venv/bin/python sim/resample.py --selftest
    .venv/bin/python sim/resample.py --bake sim/out/breach_bake.npz \
        --out sim/out/breach_film.npz

THE ONE OPERATION THAT MAKES THE SPEED RAMP
===========================================
The sim ran on a uniform WORLD clock at 240 Hz.  The film samples that clock
through beat 3's ramp: film frame f sits at world time `Clock.world_t(f)`, and
during the hold that advances by 1/156 s per film frame instead of 1/24 s.  So
the slow motion is produced HERE, by sampling, and the physics never knew about
it.  That is the whole reason the sim is not baked on film frames.

Position is linear in world time and rotation is SLERP.  Not nlerp: a shard
tumbling at 30 rad/s turns 7.2 deg between world samples, and normalised-lerp on
that is a 0.06 deg error with the wrong sign at the midpoint of every interval —
which at 156 fps is a periodic 3-frame wobble, i.e. exactly the kind of defect
that is invisible in motion and obvious held.

AND THEN IT GETS SMALLER, HONESTLY
==================================
A raw table of 3,000 bodies x 2,120 film frames x 7 floats is 178 MB of
keyframes, and `push_scene` is not resumable: a multi-GB scene goes as one
stream and a drop at 90 % restarts from zero (#80).  So the keys are DECIMATED —
a key is kept only where dropping it would move the shard by more than `tol`.

Decimation is a lossy operation and is therefore MEASURED, not asserted: the
reduced curve is re-evaluated against the full table and the worst position and
angle error over every body and every frame is reported.  `--tol` trades size
against that error and the report carries both, so nobody has to take the
compression on faith.

Free flight is nearly straight and nearly constant-spin, so almost all the keys
are at contacts, which is where they belong.
"""

import argparse
import json
import math
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(R2, "sim") not in sys.path:
    sys.path.insert(0, os.path.join(R2, "sim"))

import breachlib as BL                                            # noqa: E402

POS_TOL_M = 0.0015          # 1.5 mm: 7 px at the nearest camera distance the
                            # manifest gives a shard (0.8 m, 35 mm lens)
ANG_TOL_DEG = 0.35


# --------------------------------------------------------------------------- #
#  quaternion helpers (w, x, y, z)
# --------------------------------------------------------------------------- #

def qnorm(q):
    n = np.linalg.norm(q, axis=-1, keepdims=True)
    n[n < 1e-12] = 1.0
    return q / n


def qfix(q):
    """Make a quaternion track continuous by flipping sign where the dot with
    the previous sample is negative.  Without this, slerp takes the long way
    round on every frame Bullet happened to emit -q, and a shard spins 350 deg
    backwards in one frame."""
    q = q.copy()
    for i in range(1, len(q)):
        if np.dot(q[i], q[i - 1]) < 0.0:
            q[i] = -q[i]
    return q


def slerp(a, b, t):
    """a, b: (n, 4); t: (n,) or scalar."""
    a, b = np.atleast_2d(a), np.atleast_2d(b)
    t = np.atleast_1d(np.asarray(t, float))[:, None]
    d = np.sum(a * b, axis=1, keepdims=True)
    b = np.where(d < 0, -b, b)
    d = np.abs(d).clip(-1.0, 1.0)
    th = np.arccos(d)
    s = np.sin(th)
    lin = s < 1e-6
    w0 = np.where(lin, 1.0 - t, np.sin((1.0 - t) * th) / np.where(lin, 1.0, s))
    w1 = np.where(lin, t, np.sin(t * th) / np.where(lin, 1.0, s))
    return qnorm(w0 * a + w1 * b)


def qangle_deg(a, b):
    d = np.abs(np.sum(qnorm(a) * qnorm(b), axis=-1)).clip(-1.0, 1.0)
    return np.degrees(2.0 * np.arccos(d))


# --------------------------------------------------------------------------- #
#  1.  world grid  ->  film frames
# --------------------------------------------------------------------------- #

def to_film(bake, clock=None, f_end=None):
    """(frames, loc, quat) on FILM frames, from the world-time bake.

    Before the window the bodies are at their first sample (the wall standing);
    after it they are at their last (the wound, for the rest of the take).
    """
    clock = clock or BL.Clock()
    wt = bake["world_t"]
    L, Q = bake["loc"], qfix_track(bake["quat"])
    f0 = int(math.floor(float(clock.frame_at_world_t(wt[0]))))
    # ONLY the film frames the sim window actually covers.  Everything after the
    # last one is the wound at rest, and CONSTANT extrapolation on the F-curves
    # carries it to frame 2,978 at zero cost — which is the whole mechanism by
    # which the breach persists into beats 4, 5 and 6.  Resampling to 2,978
    # would multiply the table by 7x to store 1,800 copies of the same row.
    f1 = f_end or int(math.ceil(float(clock.frame_at_world_t(wt[-1]))))
    frames = np.arange(max(1, f0), f1 + 1)
    t = clock.world_t(frames.astype(float))
    i = np.searchsorted(wt, t).clip(1, len(wt) - 1)
    w0, w1 = wt[i - 1], wt[i]
    a = np.clip((t - w0) / np.where(np.abs(w1 - w0) < 1e-12, 1.0, w1 - w0),
                0.0, 1.0)
    n = L.shape[1]
    loc = np.empty((len(frames), n, 3), np.float32)
    quat = np.empty((len(frames), n, 4), np.float32)
    for k in range(len(frames)):
        j, aa = i[k], a[k]
        loc[k] = L[j - 1] * (1.0 - aa) + L[j] * aa
        quat[k] = slerp(Q[j - 1], Q[j], np.full(n, aa))
    return frames, loc, quat


def qfix_track(Q):
    """Sign-continuity per body, over the whole track."""
    Q = np.array(Q, np.float64)
    for j in range(Q.shape[1]):
        Q[:, j] = qfix(Q[:, j])
    return Q


# --------------------------------------------------------------------------- #
#  2.  decimation
# --------------------------------------------------------------------------- #

def decimate_body(frames, loc, quat, pos_tol, ang_tol):
    """Indices of the keys to KEEP for one body.

    Douglas-Peucker on the (position, orientation) pair jointly, because
    dropping a key drops it from every channel at once and a per-channel
    decision would let a position key survive on a frame the rotation needs and
    vice versa.
    """
    n = len(frames)
    if n <= 2:
        return list(range(n))
    keep = np.zeros(n, bool)
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        if j - i < 2:
            continue
        seg = np.arange(i + 1, j)
        a = ((frames[seg] - frames[i]) /
             float(frames[j] - frames[i]))[:, None]
        pl = loc[i] * (1 - a) + loc[j] * a
        pe = np.linalg.norm(loc[seg] - pl, axis=1)
        ql = slerp(np.repeat(quat[i][None, :], len(seg), 0),
                   np.repeat(quat[j][None, :], len(seg), 0), a[:, 0])
        qe = qangle_deg(quat[seg], ql)
        score = np.maximum(pe / pos_tol, qe / ang_tol)
        k = int(np.argmax(score))
        if score[k] <= 1.0:
            continue
        m = seg[k]
        keep[m] = True
        stack.append((i, m))
        stack.append((m, j))
    return list(np.where(keep)[0])


def decimate(frames, loc, quat, pos_tol=POS_TOL_M, ang_tol=ANG_TOL_DEG,
             progress=None):
    out = []
    n = loc.shape[1]
    for j in range(n):
        out.append(decimate_body(frames, loc[:, j], quat[:, j],
                                 pos_tol, ang_tol))
        if progress and j % 250 == 0:
            progress(j, n)
    return out


def rebuild(frames, keys, loc_j, quat_j):
    """Re-evaluate one body's decimated curve on every frame — the measurement
    that says what the compression cost."""
    ki = np.array(keys)
    fk = frames[ki]
    i = np.searchsorted(fk, frames).clip(1, len(fk) - 1)
    a = ((frames - fk[i - 1]) /
         np.maximum(fk[i] - fk[i - 1], 1e-9)).clip(0.0, 1.0)
    L = loc_j[ki][i - 1] * (1 - a)[:, None] + loc_j[ki][i] * a[:, None]
    Q = slerp(quat_j[ki][i - 1], quat_j[ki][i], a)
    return L, Q


def decimation_report(frames, loc, quat, keys, sample=None):
    n = loc.shape[1]
    idx = range(n) if sample is None else \
        np.linspace(0, n - 1, min(sample, n)).astype(int)
    pe = qe = 0.0
    tot = 0
    for j in idx:
        L, Q = rebuild(frames, keys[j], loc[:, j], quat[:, j])
        pe = max(pe, float(np.linalg.norm(L - loc[:, j], axis=1).max()))
        qe = max(qe, float(qangle_deg(Q, quat[:, j]).max()))
    for j in range(n):
        tot += len(keys[j])
    return dict(bodies=n, film_frames=len(frames),
                keys_full=n * len(frames), keys_kept=tot,
                ratio=float(tot) / max(1, n * len(frames)),
                max_pos_err_m=pe, max_ang_err_deg=qe,
                pos_tol_m=POS_TOL_M, ang_tol_deg=ANG_TOL_DEG,
                measured_on=("all" if sample is None else int(len(list(idx)))))


# --------------------------------------------------------------------------- #
#  3.  when did each body break loose?
# --------------------------------------------------------------------------- #

def release_frames(frames, loc, eps=2.0e-4):
    """The first FILM frame at which each body has moved more than eps from its
    start.  This is what the intact-pane / shard visibility swap keys off: a
    pane renders as one solid until the frame its own glass moves."""
    d = np.linalg.norm(loc - loc[0][None, :, :], axis=2)     # (nf, n)
    out = np.full(loc.shape[1], -1, int)
    hit = d > eps
    any_ = hit.any(axis=0)
    out[any_] = frames[np.argmax(hit[:, any_], axis=0)]
    return out


RELEASE_EPS_M = 0.002


def release_for_film(frames, loc, car=None):
    """THE release rule, in ONE place, because it was in two and they differed.

    `main()` used to call `release_frames(frames, loc)` -- from the FIRST frame
    of the table, with the 0.2 mm default.  `sim/remote_bake.py` measured it
    from the state at IMPACT with a 2 mm threshold, and wrote down why:

        the bonded wall settles a fraction of a millimetre under its own
        weight before the car arrives, and a 0.2 mm trigger would fire the
        intact-pane swap on EVERY shard at frame 855 -- the wall would shatter
        five frames before the car touched it, and nothing in the transform
        table would look wrong.

    Both are entry points to the same pipeline and they disagreed about the
    frame the wall breaks.  Whichever ran, the other was wrong.  This is the
    rule; both call it now.
    """
    car = car or BL.Car()
    i0 = int(np.argmin(np.abs(frames - int(round(car.impact_frame())))))
    rel = release_frames(frames[i0:], loc[i0:], eps=RELEASE_EPS_M)
    return rel, int(frames[i0])


# --------------------------------------------------------------------------- #

def selftest():
    fails = []

    def check(name, cond, detail=""):
        print("  %-52s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            fails.append(name)

    # slerp against a known rotation
    ax = np.array([0.0, 0.0, 1.0])
    for th in (0.3, 2.0, 3.0):
        a = np.array([[1.0, 0, 0, 0]])
        b = np.array([[math.cos(th / 2), 0, 0, math.sin(th / 2)]])
        m = slerp(a, b, [0.5])[0]
        want = np.array([math.cos(th / 4), 0, 0, math.sin(th / 4)])
        check("slerp halfway at %.1f rad" % th,
              np.allclose(m, want, atol=1e-9),
              "%.3e" % np.abs(m - want).max())

    # +ve control: NLERP must be measurably worse.  NOT at t = 0.5 — there the
    # two coincide for ANY pair, because both land on the bisector, and a
    # control evaluated at the midpoint reports 0.000 deg and proves nothing.
    # That is what this control said for one revision.
    th = 2.6                                   # 149 deg
    a = np.array([1.0, 0, 0, 0])
    b = np.array([math.cos(th / 2), 0, 0, math.sin(th / 2)])
    t = 0.25
    nl = qnorm(((1 - t) * a + t * b)[None, :])[0]
    sl = slerp(a[None, :], b[None, :], [t])[0]
    check("+ve control: nlerp differs from slerp by >1 deg at 149 deg, t=0.25",
          qangle_deg(nl, sl) > 1.0, "%.3f deg" % qangle_deg(nl, sl))

    # sign continuity
    q = np.array([[1.0, 0, 0, 0], [-0.999, 0, 0, -0.0447], [0.996, 0, 0, 0.0894]])
    f = qfix(q)
    check("qfix makes the track sign-continuous",
          all(np.dot(f[i], f[i - 1]) > 0 for i in range(1, len(f))))
    check("+ve control: the unfixed track is NOT continuous",
          any(np.dot(q[i], q[i - 1]) < 0 for i in range(1, len(q))))

    # decimation on a known ballistic arc + a bounce
    nf = 400
    fr = np.arange(1, nf + 1)
    t = fr / 240.0
    L = np.zeros((nf, 1, 3))
    L[:, 0, 0] = 3.0 * t
    L[:, 0, 2] = np.abs(2.0 * t - 0.5 * 9.81 * t * t)
    Q = np.zeros((nf, 1, 4))
    Q[:, 0, 0] = np.cos(6.0 * t / 2)
    Q[:, 0, 3] = np.sin(6.0 * t / 2)
    ks = decimate(fr, L, Q)
    rep = decimation_report(fr, L, Q, ks)
    check("decimation keeps < 40 %% of a ballistic arc's keys",
          rep["ratio"] < 0.40, "%.1f %% (%d of %d)"
          % (100 * rep["ratio"], rep["keys_kept"], rep["keys_full"]))
    check("... and stays inside its own tolerances",
          rep["max_pos_err_m"] <= POS_TOL_M * 1.001 and
          rep["max_ang_err_deg"] <= ANG_TOL_DEG * 1.001,
          "%.4f mm, %.4f deg" % (1000 * rep["max_pos_err_m"],
                                 rep["max_ang_err_deg"]))
    # +ve control: a 100x looser tolerance must lose accuracy AND keys
    ks2 = decimate(fr, L, Q, pos_tol=0.15, ang_tol=35.0)
    rep2 = decimation_report(fr, L, Q, ks2)
    check("+ve control: a 100x looser tol keeps fewer keys and errs more",
          rep2["keys_kept"] < rep["keys_kept"] and
          rep2["max_pos_err_m"] > rep["max_pos_err_m"],
          "%d keys / %.1f mm vs %d keys / %.1f mm"
          % (rep2["keys_kept"], 1000 * rep2["max_pos_err_m"],
             rep["keys_kept"], 1000 * rep["max_pos_err_m"]))

    # the ramp really is being walked
    c = BL.Clock()
    d1 = float(c.world_t(900.0) - c.world_t(899.0))
    d2 = float(c.world_t(1200.0) - c.world_t(1199.0))
    check("one beat-3 film frame is ~1/156 s of world time",
          abs(d1 - 1.0 / 156.2) < 2e-4, "%.6f s (1/%.1f)" % (d1, 1.0 / d1))
    check("one beat-5 film frame is 1/24 s of world time",
          abs(d2 - 1.0 / 24.0) < 1e-9, "%.6f s" % d2)
    check("the ramp integrates to the declared 1.600 s",
          abs(float(c.world_t(1056.0) - c.world_t(864.0)) - 1.6) < 1e-6,
          "%.6f s" % float(c.world_t(1056.0) - c.world_t(864.0)))

    # ---- THE RELEASE RULE, AND THE TWO ANSWERS IT USED TO HAVE ---------- #
    # A synthetic wall: 40 bodies, dead still except for a 0.4 mm settle that
    # creeps in before the impact, then a real departure afterwards.  This is
    # the shape of the actual bake and it is what separates the two rules.
    car = BL.Car()
    imp = int(round(car.impact_frame()))
    fr = np.arange(imp - 15, imp + 40)
    n = 40
    L = np.zeros((len(fr), n, 3))
    settle = np.linspace(0.0, 0.0004, 15)                 # 0.4 mm of creep
    L[:15, :, 2] = -settle[:, None]
    L[15:, :, 2] = -0.0004
    L[20:, :, 0] = np.linspace(0, 2.0, len(fr) - 20)[:, None]
    naive = release_frames(fr, L)                          # 0.2 mm from f[0]
    good, ref = release_for_film(fr, L, car)
    check("+ve control: the 0.2 mm rule from frame 1 fires BEFORE the impact",
          naive.min() < imp, "fires at %d, impact %d" % (naive.min(), imp))
    check("-ve control: the impact-referenced 2 mm rule does not",
          good.min() >= imp and ref == imp,
          "fires at %d, reference %d" % (good.min(), ref))
    check("and the two rules disagree, which is the point",
          int(naive.min()) != int(good.min()),
          "%d vs %d" % (naive.min(), good.min()))

    print("\n%d check(s) FAILED" % len(fails) if fails else "\nall checks passed")
    return 1 if fails else 0


def read_film(path):
    """The ragged table, plus a reconstructor.

    `expand(frames)` re-evaluates the decimated curves on any frame range, which
    is what BOTH the applier and the verifier must measure: the thing that gets
    rendered is the reconstruction, not the bake.
    """
    z = np.load(path, allow_pickle=False)
    cnt = z["key_count"].astype(int)
    off = np.concatenate([[0], np.cumsum(cnt)])
    kf, kl, kq = z["key_frame"].astype(int), z["key_loc"], z["key_quat"]
    names = [str(x) for x in z["names"]]
    rel = z["release"].astype(int)
    span = z["span"].astype(int)

    def keys_of(j):
        a, b = off[j], off[j + 1]
        return kf[a:b], kl[a:b], kq[a:b]

    def expand(frames):
        frames = np.asarray(frames, float)
        n = len(cnt)
        L = np.empty((len(frames), n, 3))
        Q = np.empty((len(frames), n, 4))
        for j in range(n):
            f, l, q = keys_of(j)
            if len(f) == 1:
                L[:, j] = l[0]
                Q[:, j] = q[0]
                continue
            i = np.searchsorted(f, frames).clip(1, len(f) - 1)
            a = ((frames - f[i - 1]) /
                 np.maximum(f[i] - f[i - 1], 1e-9)).clip(0.0, 1.0)
            L[:, j] = l[i - 1] * (1 - a)[:, None] + l[i] * a[:, None]
            Q[:, j] = slerp(q[i - 1], q[i], a)
        return L, Q

    return dict(names=names, release=rel, span=span, key_count=cnt,
                keys_of=keys_of, expand=expand, n=len(cnt))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--bake", default=os.path.join(R2, "sim/out/breach_bake.npz"))
    ap.add_argument("--out", default=os.path.join(R2, "sim/out/breach_film.npz"))
    ap.add_argument("--report",
                    default=os.path.join(R2, "sim/out/breach_film.json"))
    ap.add_argument("--pos-tol", type=float, default=POS_TOL_M)
    ap.add_argument("--ang-tol", type=float, default=ANG_TOL_DEG)
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    z = np.load(a.bake, allow_pickle=False)
    bake = {k: z[k] for k in z.files}
    clock = BL.Clock()
    frames, loc, quat = to_film(bake, clock)
    print("film frames %d..%d, %d bodies"
          % (frames[0], frames[-1], loc.shape[1]))
    keys = decimate(frames, loc, quat, a.pos_tol, a.ang_tol,
                    progress=lambda j, n: print("  decimate %d/%d" % (j, n)))
    rep = decimation_report(frames, loc, quat, keys, sample=400)
    rel, ref = release_for_film(frames, loc)
    rep["release_reference_frame"] = ref
    # RAGGED: only the keys that survived.  Storing the full per-frame table
    # alongside them would put back exactly the bytes the decimation removed,
    # and `push_scene` is not resumable (#80).
    cnt = np.array([len(k) for k in keys], np.int32)
    kf = np.concatenate([frames[np.array(k)] for k in keys]).astype(np.int32)
    kl = np.concatenate([loc[np.array(k), j] for j, k in enumerate(keys)])
    kq = np.concatenate([quat[np.array(k), j] for j, k in enumerate(keys)])
    np.savez_compressed(a.out,
                        key_count=cnt, key_frame=kf,
                        key_loc=kl.astype(np.float32),
                        key_quat=kq.astype(np.float32),
                        release=rel.astype(np.int32),
                        span=np.array([frames[0], frames[-1]], np.int32),
                        names=bake["names"])
    rep["out"] = a.out
    rep["bytes"] = os.path.getsize(a.out)
    rep["release_frame_min"] = int(rel[rel > 0].min()) if (rel > 0).any() else -1
    rep["never_released"] = int((rel < 0).sum())
    with open(a.report, "w") as fh:
        json.dump(rep, fh, indent=1, default=float)
    print(json.dumps(rep, indent=1, default=float))


if __name__ == "__main__":
    main()
