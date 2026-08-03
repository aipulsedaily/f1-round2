"""SHARD GEOMETRY — one 2-D fracture cell becomes one solid of glass.

bpy only.  Imported by the sim scene builder AND by whatever builds the render
scene, so the two cannot disagree about where a shard's origin is — which they
must not, because the sim bakes transforms relative to that origin and the
render applies them.

THE ORIGIN IS THE RULE THAT MATTERS
-----------------------------------
A shard's object origin is the centroid of its 2-D cell, on the mid-plane of the
laminate.  Not the pane's origin, not the world origin, not the mesh's bounding
box centre.  Two reasons:

  * a rigid body rotates about its centre of mass, and Bullet takes the object
    origin as that centre unless told otherwise.  An origin at the pane corner
    would give every shard a 3 m lever arm it does not have, and the field would
    fly apart in a way no glass ever has.
  * the baked transform table is (location, quaternion) PER SHARD.  If the
    render scene rebuilds the same shard about a different origin, every shard
    lands in the wrong place by exactly the offset, and it does so smoothly and
    plausibly — the worst kind of wrong.

`ORIGIN_RULE` is a string written into both the sim's and the render's build
report so a mismatch is a diff, not a mystery.

DETAIL LEVELS
-------------
    0   the raw prism.  n-gon cap, n-gon cap, n quads.  This is the SIM mesh:
        Bullet only ever sees its convex hull, and the hull of the prism and the
        hull of the finished shard are the same to within the chamfer.
    1   + a 0.6 mm chamfer on both perimeter rings, so the edge is a real arris
        that catches the 12.47 deg sun instead of a zero-width line
    2   + conchoidal relief on the thickness band: the ripple a crack front
        leaves behind it.  0.30 mm peak-to-peak, which is 1.4 px at the 0.8 m
        the manifest films the nearest shard at, so it is MESH and not a bump
        map.  Also splits the laminate into its two 5 mm plies with the 1.5 mm
        PVB between, for the shards that keep it.

Only shards that come near the camera path need level 2, and `plan_detail()`
decides that from the camera keys rather than from a guess.
"""

import math

import numpy as np

ORIGIN_RULE = ("shard origin = (0.5*(x_in+x_out), centroid_u, centroid_v) "
               "in WORLD metres; mesh verts are stored relative to it")

CHAMFER_M = 0.0006

# THE KERF.  Neighbouring shards share their boundary EXACTLY — that is the
# whole point of a recursive-split partition — and two convex hulls that share a
# face are, to Bullet, two hulls overlapping by twice the collision margin.  The
# first bake of the full wall was 3,000 bodies resolving that overlap at once:
# median displacement 10.85 m in ONE SECOND of world time, peak 120.7 m/s, the
# entire wall gone before the car arrived.
#
# So the crack takes material with it, which is also what a real crack does: the
# fracture surface is not a plane of zero thickness, it sheds dust and the two
# faces never fit back together.  Each shard is inset by KERF_M, leaving a
# 2 x KERF_M gap between neighbours that the margin can live inside.
# 0.4 mm inset -> 0.8 mm gap; the shards are HIDDEN until they move, so the kerf
# is never on screen in the intact wall, and 0.8 mm at the closest a shard is
# ever filmed is under 2 px on a field of tumbling glass.
KERF_M = 0.0004
RIPPLE_M = 0.00030
RIPPLE_PERIOD_M = 0.012


def prism(poly_uv, x_in, x_out, detail=0, seed=0, kerf=None):
    """(verts, faces) for one shard, in WORLD axes, RELATIVE TO ITS ORIGIN.

    poly_uv is the 2-D cell as (u, v) = (world y, world z), CCW.
    x_in / x_out are the laminate's inner and outer faces in world x.
    """
    P = np.asarray(poly_uv, float)
    c = _centroid(P)
    xm = 0.5 * (x_in + x_out)
    k = KERF_M if kerf is None else float(kerf)
    if k > 0.0:
        P = _inset(P - c, k) + c
    n = len(P)
    Q = P - c                                    # 2-D, relative to the origin
    dx_in, dx_out = x_in - xm, x_out - xm

    if detail <= 0:
        V = np.zeros((2 * n, 3))
        V[:n, 0] = dx_in
        V[n:, 0] = dx_out
        V[:n, 1], V[:n, 2] = Q[:, 0], Q[:, 1]
        V[n:, 1], V[n:, 2] = Q[:, 0], Q[:, 1]
        F = [list(range(n))[::-1], list(range(n, 2 * n))]
        for i in range(n):
            j = (i + 1) % n
            F.append([i, j, n + j, n + i])
        return V, F

    # --- inset ring for the chamfer ---------------------------------------- #
    ins = _inset(Q, CHAMFER_M)
    rng = np.random.default_rng(seed)
    band = np.zeros(n)
    if detail >= 2:
        # Wallner ripple: the crack front's own arrest lines, running ACROSS the
        # thickness, so the modulation is along the perimeter arc length.
        s = np.concatenate([[0.0], np.cumsum(
            np.linalg.norm(np.diff(np.vstack([Q, Q[:1]]), axis=0), axis=1))])[:n]
        ph = rng.uniform(0, 2 * math.pi, 3)
        band = RIPPLE_M * (
            0.60 * np.sin(2 * math.pi * s / RIPPLE_PERIOD_M + ph[0])
            + 0.28 * np.sin(2 * math.pi * s / (0.41 * RIPPLE_PERIOD_M) + ph[1])
            + 0.12 * np.sin(2 * math.pi * s / (2.7 * RIPPLE_PERIOD_M) + ph[2]))

    rings = []                                   # (x offset, 2-D ring)
    rings.append((dx_in, ins))                   # inner cap ring
    rings.append((dx_in + CHAMFER_M, Q))         # inner arris
    if detail >= 2:
        nrm = _outward(Q)
        rings.append((0.0, Q + nrm * band[:, None]))
    rings.append((dx_out - CHAMFER_M, Q))        # outer arris
    rings.append((dx_out, ins))                  # outer cap ring

    V, F = [], []
    idx = []
    for dx, R in rings:
        base = len(V)
        for q in R:
            V.append([dx, q[0], q[1]])
        idx.append(base)
    V = np.array(V, float)
    F.append(list(range(idx[0], idx[0] + n))[::-1])
    F.append(list(range(idx[-1], idx[-1] + n)))
    for k in range(len(rings) - 1):
        a, b = idx[k], idx[k + 1]
        for i in range(n):
            j = (i + 1) % n
            F.append([a + i, a + j, b + j, b + i])
    return V, F


def origin_of(poly_uv, x_in, x_out):
    c = _centroid(np.asarray(poly_uv, float))
    return np.array([0.5 * (x_in + x_out), c[0], c[1]])


def _centroid(P):
    x, y = P[:, 0], P[:, 1]
    cr = x * np.roll(y, -1) - np.roll(x, -1) * y
    a = 0.5 * np.sum(cr)
    if abs(a) < 1e-15:
        return P.mean(axis=0)
    return np.array([np.sum((x + np.roll(x, -1)) * cr) / (6.0 * a),
                     np.sum((y + np.roll(y, -1)) * cr) / (6.0 * a)])


def _outward(P):
    """Unit outward normal at every vertex (angle bisector of its two edges)."""
    n = len(P)
    e = np.roll(P, -1, axis=0) - P
    L = np.linalg.norm(e, axis=1)[:, None]
    L[L < 1e-15] = 1.0
    e = e / L
    ne = np.c_[e[:, 1], -e[:, 0]]                # outward for CCW
    b = ne + np.roll(ne, 1, axis=0)
    Lb = np.linalg.norm(b, axis=1)[:, None]
    Lb[Lb < 1e-12] = 1.0
    return b / Lb


def _inset(P, d):
    """Move every vertex inward by d along its bisector, clamped so a small
    cell cannot turn inside out (which is what a fixed inset does to a 4 mm
    shard with a 0.6 mm chamfer)."""
    nrm = _outward(P)
    c = _centroid(P)
    r = np.linalg.norm(P - c, axis=1)
    dd = np.minimum(d, 0.35 * r)[:, None]
    return P - nrm * dd


def volume(V, F):
    """Signed volume of the closed mesh, m^3.  The mass comes from this and not
    from area x thickness, so a chamfered shard is lighter than a prism by
    exactly the material the chamfer removed."""
    tot = 0.0
    for f in F:
        for k in range(1, len(f) - 1):
            a, b, c = V[f[0]], V[f[k]], V[f[k + 1]]
            tot += float(np.dot(a, np.cross(b, c))) / 6.0
    return abs(tot)
