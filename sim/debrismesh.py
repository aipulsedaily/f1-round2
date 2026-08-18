"""ONE PIECE OF FINE GLASS DEBRIS, AS GEOMETRY.  numpy only, no bpy.

Imported by `sim/debris.py` (to weigh the field) and by `sim/apply_breach.py`
(to build it), so the two cannot disagree about what a chip is — which matters
here for the same reason it matters in `shardmesh.py`: the mass ledger in
`debris.ledger()` is computed from these volumes, and a mesher that built a
different solid would silently break the conservation argument the whole pass
rests on.

WHY A CHIP IS NOT A LITTLE SHARD
===============================
A shard is a cell of the pane: it keeps both polished faces of the laminate and
its thickness is the laminate's, 11.5 mm.  A chip is not.  Fine debris off a
fracturing plate comes from the crack's own process zone and from the crushed
contact, and it is PLATY — a flake — for a reason that is geometric rather than
aesthetic: the free surfaces available to it are the two crack faces, which are
millimetres apart, not the two ply faces, which are five apart.  So

    plan size   d   0.4 .. 8 mm      set by the fragmentation law (debris.py)
    thickness   t   0.10 .. 0.28 d   set by the crack opening it came out of

and the resulting flake is WEDGE-shaped, not a slab: a conchoidal fracture
surface is curved, so the two faces of a chip converge.  `taper` is that, and it
is what makes a chip catch the sun on one facet and go dark on the next as it
tumbles.  A parallel-faced slab does not do that; it glints twice per revolution
and reads as a sequin.

WHY THE FACES ARE FROSTED AND NOT POLISHED, AND WHY THAT IS GEOMETRY'S PROBLEM
=============================================================================
Every face of a chip is a fracture surface.  Beyond a mirror radius of order
`sqrt(K/sigma)` — tens of microns at these stress levels — a glass crack front
goes through mist into hackle and the surface is rough at 1-20 um.  A chip is
therefore FROSTED on every side, and that is not a detail: it is the difference
between a field of debris that sparkles continuously and one that fires a
delta-function highlight for three chips per frame and is otherwise invisible.

At 2-8 px per chip the roughness cannot be meshed, so it is carried by the
material (`BREACH_Fines`, built in apply_breach) as a real GGX roughness and not
as a bump map.  What the mesh must supply is the FACET COUNT: a chip with four
plan sides has six faces and six chances to be pointing at the sun.  `n_plan`
is drawn from 4..7 for that reason and not for variety's sake.

EVERY CHIP IS ITS OWN SOLID
===========================
`chip()` is a generator, not a library.  There is no chip asset, no chip
instanced 100,000 times, and no chip collection picked from by index: the seed
is `hash(group, index)` and two chips in the field are the same solid only by
the coincidence of two 64-bit seeds.  That is the project's red line
("one tree spammed 100 times") answered by construction rather than by a claim.
"""

import numpy as np

# The plan polygon is a convex hull of points on a jittered ellipse.  Convex is
# not a simplification for a chip the way it is for a shard: a flake this small
# that had a re-entrant corner would have broken there.
N_PLAN_MIN, N_PLAN_MAX = 4, 7

# thickness as a fraction of plan size.  The lower bound is the crack opening a
# flake can escape through; the upper is where it stops being a flake and starts
# being a small shard, which is the population `fracture.py` already owns.
T_OVER_D_MIN, T_OVER_D_MAX = 0.10, 0.28

# how far the two faces converge across the chip.  0 is a slab, 1 is a wedge
# that closes to an edge on one side.
TAPER_MIN, TAPER_MAX = 0.25, 0.85

# mean solid volume as a fraction of d**3, measured by `volume_factor()` over
# the generator's own output.  Used by debris.ledger() to turn a mass budget
# into a count without building the meshes first.
SHAPE_FACTOR = 0.02036        # asserted against the generator in selftest()


def chip(seed, d, t=None):
    """(verts, faces) for one flake, centred on its own centroid, metres.

    `d` is the plan size (the diameter of the circle the plan is drawn in).
    `t` defaults to a fraction of the plan's REALISED long extent.
    """
    rng = np.random.default_rng(np.uint64(seed) % np.uint64(2 ** 63))
    n = int(rng.integers(N_PLAN_MIN, N_PLAN_MAX + 1))

    # --- plan: n points on a jittered, squashed ellipse --------------------- #
    a = np.sort(rng.uniform(0.0, 2.0 * np.pi, n))
    # a flake is rarely equiaxed; the crack that freed it had a direction
    ecc = rng.uniform(0.45, 1.0)
    r = 0.5 * d * rng.uniform(0.70, 1.0, n)
    P = np.c_[r * np.cos(a), ecc * r * np.sin(a)]
    P -= P.mean(axis=0)

    # THE THICKNESS IS A FRACTION OF THE PLAN THE CHIP ACTUALLY GOT, not of the
    # d it was asked for.  With n as low as 4 the drawn angles sometimes cluster
    # and the realised plan is half the nominal d; scaling t by d then produced
    # chips whose thinnest principal extent was 0.42 of their longest, which is
    # not a flake.  The platy control in selftest() is what caught it.
    if t is None:
        dp = float(np.ptp(P, axis=0).max())
        t = dp * rng.uniform(T_OVER_D_MIN, T_OVER_D_MAX)

    # --- the two faces converge: z = +-t/2 * (1 - taper * s) ---------------- #
    # s is a linear ramp across the plan in a random direction, so one edge of
    # the chip is thick and the opposite one is nearly closed.
    th = rng.uniform(0.0, 2.0 * np.pi)
    u = np.array([np.cos(th), np.sin(th)])
    s = P @ u
    sp = s.max() - s.min()
    s = (s - s.min()) / (sp if sp > 1e-12 else 1.0)
    taper = rng.uniform(TAPER_MIN, TAPER_MAX)
    half = 0.5 * t * (1.0 - taper * s)
    # the two faces are also independently tilted, because two conchoidal
    # surfaces are not parallel
    tilt = rng.normal(0.0, 0.12 * t, 2)
    dirn = rng.uniform(0.0, 2.0 * np.pi, 2)
    ramp = np.c_[P @ np.array([np.cos(dirn[0]), np.sin(dirn[0])]),
                 P @ np.array([np.cos(dirn[1]), np.sin(dirn[1])])]
    rsc = np.maximum(np.abs(ramp).max(axis=0), 1e-12)

    top = np.c_[P, +half + tilt[0] * ramp[:, 0] / rsc[0]]
    bot = np.c_[P, -half + tilt[1] * ramp[:, 1] / rsc[1]]
    V = np.vstack([bot, top])

    F = [list(range(n))[::-1], list(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        F.append([i, j, n + j, n + i])

    V = V - _centroid_of(V, F)
    # a tumbling flake has no preferred orientation; bake one in so the field
    # does not share an axis
    V = V @ _rand_rot(rng).T
    return V, F


_TRI_CACHE = {}


def _tris(F):
    """Fan-triangulate a face list, once, into an (m, 3) index array.

    Cached on the face list's identity-by-value because the chip topology is a
    function of `n` alone: 260,000 chips share at most four distinct topologies
    and re-deriving them per chip made the generator 2.4 ms instead of 0.3.
    """
    key = tuple(len(f) for f in F)
    if key not in _TRI_CACHE:
        t = []
        for f in F:
            for k in range(1, len(f) - 1):
                t.append((f[0], f[k], f[k + 1]))
        _TRI_CACHE[key] = np.array(t, np.int64)
    return _TRI_CACHE[key]


def _signed(V, F):
    """(per-triangle signed volumes, per-triangle centroids)."""
    T = _tris(F)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    dv = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0
    return dv, 0.25 * (a + b + c)


def volume(V, F):
    dv, _ = _signed(V, F)
    return abs(float(dv.sum()))


def _centroid_of(V, F):
    """Volume centroid.  The object origin must be the centre of mass for the
    same reason `shardmesh.ORIGIN_RULE` gives: a chip is keyed as a rigid body
    inside its puff and spins about this point."""
    dv, cen = _signed(V, F)
    den = float(dv.sum())
    if abs(den) < 1e-24:
        return V.mean(axis=0)
    return (dv[:, None] * cen).sum(axis=0) / den


def _rand_rot(rng):
    q = rng.normal(size=4)
    q /= np.linalg.norm(q)
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def volume_factor(n=4000, d=0.003, seed=1):
    """Mean solid volume / d**3.  This is the number the mass ledger uses; it is
    MEASURED off the generator, not assumed, so a change to the shape bands
    cannot silently move the field's mass."""
    v = [volume(*chip(seed * 1000003 + i, d)) for i in range(n)]
    return float(np.mean(v) / d ** 3)


def selftest():
    """Positive controls that must fire, negative controls that must not."""
    bad = []

    def check(name, cond, detail=""):
        print("   %-42s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            bad.append(name)

    V, F = chip(12345, 0.004)
    check("closed: every edge used exactly twice", _euler_ok(V, F))
    check("volume > 0", volume(V, F) > 0)
    check("origin is the volume centroid",
          float(np.linalg.norm(_centroid_of(V, F))) < 1e-12)

    # NEGATIVE CONTROL: two different seeds must not give the same solid.
    V2, _F2 = chip(12346, 0.004)
    same = (V.shape == V2.shape and np.allclose(V, V2))
    check("two seeds are not the same chip", not same)

    # POSITIVE CONTROL: the same seed must.
    V3, F3 = chip(12345, 0.004)
    check("the same seed IS the same chip",
          np.allclose(V, V3) and F == F3)

    # scale linearity: the generator must be scale-free, or the size law in
    # debris.py does not mean what it says.
    Va, Fa = chip(777, 0.001)
    Vb, Fb = chip(777, 0.010)
    check("volume scales as d^3 (scale-free generator)",
          abs(volume(Vb, Fb) / volume(Va, Fa) - 1000.0) < 1.0,
          "%.1f" % (volume(Vb, Fb) / volume(Va, Fa)))

    sf = volume_factor(2000)
    check("SHAPE_FACTOR matches the generator", abs(sf - SHAPE_FACTOR) < 0.0006,
          "measured %.4f, declared %.4f" % (sf, SHAPE_FACTOR))

    # A chip must be PLATY, measured on its OWN axes and not on the world's --
    # every chip carries a random baked rotation, so an axis-aligned extent
    # measures the rotation and not the shape.  This control failed for exactly
    # that reason on the first run and the failure was the check's, not the
    # generator's.
    rat = [_platy_ratio(*chip(9000 + i, 0.004)) for i in range(400)]
    check("platy: min principal extent < 0.35 x max, on 400 chips",
          float(np.percentile(rat, 95)) < 0.35,
          "p50 %.3f p95 %.3f" % (float(np.median(rat)),
                                 float(np.percentile(rat, 95))))

    print("   STAGE RESULT: debrismesh %s"
          % ("PASS" if not bad else "FAIL " + ",".join(bad)))
    return 1 if bad else 0


def _platy_ratio(V, F):
    """Smallest principal extent over largest.  Rotation-invariant."""
    Q = V - V.mean(axis=0)
    _u, _s, vt = np.linalg.svd(Q, full_matrices=False)
    e = (Q @ vt.T)
    ext = e.max(axis=0) - e.min(axis=0)
    return float(ext.min() / max(ext.max(), 1e-15))


def _euler_ok(V, F):
    from collections import Counter
    c = Counter()
    for f in F:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            c[(min(a, b), max(a, b))] += 1
    return all(v == 2 for v in c.values())


if __name__ == "__main__":
    import sys
    sys.exit(selftest())
