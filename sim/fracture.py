"""PRE-FRACTURE — the crack pattern in the showroom's glass wall, from code.

    .venv/bin/python sim/fracture.py --preview          # pattern + PNGs to sim/out
    .venv/bin/python sim/fracture.py --selftest         # 0 = every check passed

Beat 3, frames 865-1056.  The car breaches the east curtain wall on Y = 0.  This
module owns the PATTERN only: a watertight 2-D partition of every pane into
shards, in the pane's own (y, z) world plane.  It builds no geometry and imports
no bpy, so it runs under the project venv and inside Blender unchanged, and its
output is a data file that can be diffed, measured and looked at before a single
vertex exists.

WHY NOT CELL FRACTURE
=====================
`item_manifest` asks for "cell-fracture with the seed density falling off from
the launch axis" and warns off "uniform Voronoi across the whole pane".  Density
falloff fixes the second complaint but not the first, because a Voronoi mosaic —
graded or not — has no CRACK in it.  Every edge is the same kind of edge.  Glass
that has been hit does not look like that, and the reason is that the failure is
SEQUENTIAL:

  1.  RADIAL cracks leave the contact first, driven by the bending tension on the
      far face, and run to the frame.  There are a dozen of them and they are the
      longest features in the pane.
  2.  HOOP (circumferential) cracks open behind the radials as the plate rebounds.
      They ARREST on the radials — a hoop crack does not cross a radial that is
      already open, because the radial is a free surface with no tension across
      it.  So hoops are ARCS BETWEEN TWO RADIALS, never closed rings.
  3.  Only then does the MOSAIC appear, and only where the strain energy density
      was high enough: a comminuted zone at the contact, coarsening outward.
  4.  The 16 mm of every edge that is clamped under the pressure plate is in
      compression and does not participate.  It holds SLABS.

That is a HIERARCHY, and the honest way to build a hierarchy is to build it in
order.  This module cuts the pane recursively: primary radials through the whole
pane, then hoops confined to the wedge they were born in, then a mosaic that
subdivides each remaining piece until it is smaller than the local target area.

RECURSIVE SPLITTING BUYS FOUR THINGS A VORONOI DOES NOT
-------------------------------------------------------
  * THE UNION IS EXACTLY THE PANE.  Every cut produces two pieces from one, so
    area is conserved to floating point and there is no gap, no overlap and no
    sliver at the boundary.  `--selftest` asserts it to 1e-9 m^2.
  * SHARED EDGES ARE THE SAME NUMBERS.  Both children receive the identical
    polyline, vertex for vertex.  A pre-fractured pane that has to read as INTACT
    for the 33 s of beat 1 before it breaks cannot afford two edges that are
    nearly the same.
  * THE ARREST RULE IS FREE.  A hoop crack is cut into the wedge piece it lives
    in, so it physically cannot cross a radial.  In a Voronoi you would have to
    fake it.
  * PIECES STAY NEAR-CONVEX, so a convex-hull collider is not a lie.  Measured:
    see `convexity_report()`; the sim uses the hull and the render uses the mesh,
    and the deviation between them is a number this module publishes rather than
    a hope.

THE CRACKS WANDER, AND BOTH SIDES WANDER IDENTICALLY
----------------------------------------------------
A straight cut reads as CG from any distance.  Every cut here is a line plus a
1-D fractal displacement h(t) along it, so the side test for a point q is the
scalar field

    s(q) = (q - p).n  -  h((q - p).d)

which is exactly zero ON the crack.  Clipping by s > 0 and s < 0 and inserting
the roots gives two pieces whose shared boundary is sampled at the SAME knots.

WHERE THE IMPACT IS, AND WHY IT IS NOT A POINT
==============================================
The car is 2.005 m wide and 0.992 m tall and the glass starts at z = 0.110.  The
strike is not a point and it is not on the launch axis alone: the front wing
crosses the plane first as a 1.9 m LINE at z ~ 0.13, the nose cone follows at
z ~ 0.42, the front tyres at z ~ 0.36 and +-0.72 m, and nothing above z ~ 1.0
touches glass at all.  The upper 5 m of every pane fails because the wall loses
its mullions, not because anything hit it.  So the energy field is built from
SEGMENTS with weights, and the vertical gradient it produces — a comminuted band
in the bottom metre under long radial slivers reaching six metres to the head —
is both what the physics says and a better picture than a bullseye on Y = 0.

Numbers taken from, and only from:
    world/items/mullion_intact.py   glazing_pockets(), section(), breach_state()
    world/car_anim_measured.json    the car's own animated transform per frame
    anim/carpath.py                 CAR_LEN 5.698, nose offset +3.020 from origin
"""

import argparse
import json
import math
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R2, "sim", "out")

# --------------------------------------------------------------------------- #
#  THE WALL.  Every number below is READ from mullion_intact's published
#  interface, never re-derived.  If that file moves a plane, this moves with it.
# --------------------------------------------------------------------------- #
IFACE = os.path.join(R2, "world", "items", "mullion_intact_interface.json")

# A piece smaller than this is not a shard, it is a numerical sliver, and it is
# DISCARDED.  Discarded area is accounted, never silent: `partition_report`
# asserts residual == -dropped exactly, so the difference between "we threw away
# 0.08 mm2 of slivers" and "the partition leaks" stays visible.
SLIVER_M2 = 1.0e-7          # 0.32 mm x 0.32 mm
# How far the convex-hull collider may stand proud of the real shard.
CONVEX_TOL_M = 0.003        # 3 mm

# THE ASPECT CAP.  The first pattern that came out of this module was, above the
# crushed zone, a fan of 40:1 needles six metres long, because the far-field rule
# ("cut across the tangent so the piece stays a radial sliver") had nothing
# stopping it.  Two reasons that is wrong and one that it matters:
#   * glass slivers DO run long beside a radial crack, but the aspect ratio
#     observed on struck laminate is single digits, not forty.  Above the crush
#     zone the plate is FOLDING, not comminuting, and a folding plate sheds
#     roughly equiaxed slabs.
#   * a 40:1 convex hull is the classic rigid-body tunnelling shape: thin in one
#     axis, so a substep can carry it clean through a 12 mm floor.
# The cap is looser close in, where the needles are real, and tight far out.
# It is BOUNDED BY AREA as well, because halving a needle across its long axis
# halves its area too: chasing a 40:1 sliver down to 3.5:1 costs twelve halvings
# and turns one shard into a thousand grains.  Measured, when it was unbounded:
# one pane went 1,820 -> 4,206 shards and the far-field median area fell 5.7x,
# which destroyed the very size gradient the module exists for.  So a piece
# stops being cut for aspect once it is below AR_FLOOR_FRAC of its local target
# area, and the cap is reported as a DISTRIBUTION rather than a maximum.
AR_NEAR = 8.0               # allowed aspect within AR_R_M of the strike
AR_FAR = 3.5                # allowed aspect beyond it
AR_R_M = 0.60
AR_FLOOR_FRAC = 0.30

# THE HAIR RULE.  The cap above bounds the aspect of pieces it is allowed to
# cut, but it cannot fix a hair that was born as a hair: a crack that passes
# 0.4 mm from an existing one shaves a 0.4 mm x 500 mm wafer, and no amount of
# later cutting makes that anything but a hair.  Measured before this rule: 1 %
# of far-field shards were above 119:1 and the worst was 1,386:1.
# So a cut is REFUSED IN THAT PIECE if it would isolate a ligament thinner than
# W_MIN or longer than AR_HARD, which is the physical statement that a crack
# approaching an open free surface does not complete — it turns and merges into
# it.  This is applied in all three passes, per piece, so refusing a radial in
# one piece does not delete the radial.
W_MIN_M = 0.004             # 4 mm; 19 px at the nearest camera distance
AR_HARD = 22.0

# How many random chords the mosaic pass may try before it gives up on a piece.
# ONE is not enough; see the note in the mosaic loop.
MOSAIC_TRIES = 6


def wall():
    """section(), stations(), breach_state(), glazing_pockets() as one dict."""
    with open(IFACE) as fh:
        d = json.load(fh)
    return d


# --------------------------------------------------------------------------- #
#  1.  THE CUT.  A wandering line, and the two pieces it makes.
# --------------------------------------------------------------------------- #

def fractal_h(rng, n, rough=0.62):
    """1-D midpoint displacement on [0, 1], h(0) = h(1) = 0, unit-ish amplitude.

    n is the number of subdivision levels; the returned array has 2**n + 1
    samples.  Deterministic in `rng`.
    """
    m = 2 ** n + 1
    h = np.zeros(m)
    step = m - 1
    amp = 1.0
    while step > 1:
        half = step // 2
        for i in range(half, m, step):
            h[i] = 0.5 * (h[i - half] + h[i + half]) + rng.normal(0.0, amp)
        amp *= rough
        step = half
    mx = np.max(np.abs(h))
    return h / mx if mx > 0 else h


class Cut(object):
    """A wandering straight cut across a polygon.

    p   a point on the nominal line, in pane (u, v) metres
    d   unit direction ALONG the line
    n   unit normal (d rotated +90 deg)
    h   displacement along n as a function of t = (q - p).d, in metres
    """

    __slots__ = ("p", "d", "n", "t0", "t1", "hs", "kind", "gen")

    def __init__(self, p, d, span, rng, amp, levels=5, kind="mosaic", gen=0):
        d = np.asarray(d, float)
        d = d / np.linalg.norm(d)
        self.p = np.asarray(p, float)
        self.d = d
        self.n = np.array([-d[1], d[0]])
        self.t0, self.t1 = -span, span
        self.hs = amp * fractal_h(rng, levels)
        self.kind = kind
        self.gen = gen

    def h(self, t):
        """Displacement at along-line coordinate t, linearly interpolated."""
        m = len(self.hs)
        f = (np.asarray(t, float) - self.t0) / (self.t1 - self.t0)
        f = np.clip(f, 0.0, 1.0) * (m - 1)
        i = np.floor(f).astype(int)
        i = np.clip(i, 0, m - 2)
        w = f - i
        return self.hs[i] * (1.0 - w) + self.hs[i + 1] * w

    def s(self, q):
        """Signed side.  Exactly zero on the crack."""
        q = np.atleast_2d(np.asarray(q, float))
        r = q - self.p
        return r @ self.n - self.h(r @ self.d)

    def knots(self, ta, tb):
        """The fractal's own sample points strictly between ta and tb."""
        m = len(self.hs)
        ts = self.t0 + (self.t1 - self.t0) * np.arange(m) / (m - 1.0)
        return ts[(ts > min(ta, tb) + 1e-12) & (ts < max(ta, tb) - 1e-12)]

    def point(self, t):
        return self.p + self.d * t + self.n * float(self.h(t))


def _root(cut, a, b):
    """The point on segment a->b where cut.s changes sign.  Bisection, because
    s is piecewise linear in t and a closed form would have to pick a piece."""
    sa = float(cut.s(a)[0])
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        q = a + (b - a) * mid
        if (float(cut.s(q)[0]) > 0.0) == (sa > 0.0):
            lo = mid
        else:
            hi = mid
    t = 0.5 * (lo + hi)
    return a + (b - a) * t


def split(poly, cut):
    """Split polygon `poly` (N x 2, CCW) by `cut`.

    Returns (pos, neg) — the pieces on the s > 0 and s < 0 sides — or
    (poly, None) / (None, poly) if the cut misses.  The shared boundary is
    generated ONCE and handed to both pieces reversed, so the two edges are the
    same floating-point numbers.
    """
    P = np.asarray(poly, float)
    s = cut.s(P)
    if np.all(s >= -1e-12):
        return P, None
    if np.all(s <= 1e-12):
        return None, P
    n = len(P)
    # walk the ring, inserting the two crossings
    ring, side = [], []
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        sa, sb = s[i], s[(i + 1) % n]
        ring.append(a)
        side.append(1 if sa > 0 else -1)
        if (sa > 0) != (sb > 0):
            ring.append(_root(cut, a, b))
            side.append(0)
    ring = np.array(ring)
    side = np.array(side)
    xs = np.where(side == 0)[0]
    if len(xs) != 2:
        # a wandering cut can clip a corner twice; refuse rather than guess
        return (P, None) if np.sum(s > 0) > np.sum(s < 0) else (None, P)
    i0, i1 = xs
    A, B = ring[i0], ring[i1]
    ta = float((A - cut.p) @ cut.d)
    tb = float((B - cut.p) @ cut.d)
    ks = cut.knots(ta, tb)
    if tb < ta:
        ks = ks[::-1]
    bridge = np.array([cut.point(t) for t in ks]) if len(ks) else np.zeros((0, 2))

    # piece 1: ring[i0..i1] then bridge reversed back to A
    p1 = np.vstack([ring[i0:i1 + 1], bridge[::-1]]) if len(bridge) \
        else ring[i0:i1 + 1]
    # piece 2: ring[i1..end] + ring[0..i0] then bridge forward back to B
    p2 = np.vstack([ring[i1:], ring[:i0 + 1], bridge]) if len(bridge) \
        else np.vstack([ring[i1:], ring[:i0 + 1]])
    # which is which
    if np.mean(cut.s(_interior(p1))) > 0:
        return _dedupe(p1), _dedupe(p2)
    return _dedupe(p2), _dedupe(p1)


def _interior(poly):
    """A few points guaranteed inside-ish: the centroid and vertex midpoints."""
    c = np.mean(poly, axis=0)
    return np.vstack([c[None, :], 0.5 * (poly + c)])


def _dedupe(poly, tol=1e-9):
    keep = [0]
    for i in range(1, len(poly)):
        if np.linalg.norm(poly[i] - poly[keep[-1]]) > tol:
            keep.append(i)
    if len(keep) > 2 and np.linalg.norm(poly[keep[0]] - poly[keep[-1]]) <= tol:
        keep.pop()
    return poly[keep]


def area(poly):
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def centroid(poly):
    x, y = poly[:, 0], poly[:, 1]
    cr = x * np.roll(y, -1) - np.roll(x, -1) * y
    a = 0.5 * np.sum(cr)
    if abs(a) < 1e-15:
        return np.mean(poly, axis=0)
    cx = np.sum((x + np.roll(x, -1)) * cr) / (6.0 * a)
    cy = np.sum((y + np.roll(y, -1)) * cr) / (6.0 * a)
    return np.array([cx, cy])


def hull_indices(P):
    """Monotone-chain convex hull, returned as indices into P, CCW."""
    P = np.asarray(P, float)
    order = np.lexsort((P[:, 1], P[:, 0]))

    def cross(o, a, b):
        return (P[a][0] - P[o][0]) * (P[b][1] - P[o][1]) - \
               (P[a][1] - P[o][1]) * (P[b][0] - P[o][0])

    lo = []
    for i in order:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], i) <= 0:
            lo.pop()
        lo.append(int(i))
    up = []
    for i in order[::-1]:
        while len(up) >= 2 and cross(up[-2], up[-1], i) <= 0:
            up.pop()
        up.append(int(i))
    return lo[:-1] + up[:-1]


def deepest_notch(poly):
    """(depth, v, a, b): the deepest concavity, the polygon index of its
    deepest vertex, and the two hull vertices whose chord it hangs from."""
    P = np.asarray(poly, float)
    if len(P) < 4:
        return 0.0, -1, -1, -1
    h = hull_indices(P)
    if len(h) < 3:
        return 0.0, -1, -1, -1
    hs = set(h)
    hull_pos = [i for i in range(len(P)) if i in hs]
    if len(hull_pos) < 2:
        return 0.0, -1, -1, -1
    best = (0.0, -1, -1, -1)
    for k in range(len(hull_pos)):
        i = hull_pos[k]
        j = hull_pos[(k + 1) % len(hull_pos)]
        skipped = []
        m = (i + 1) % len(P)
        while m != j:
            skipped.append(m)
            m = (m + 1) % len(P)
        if not skipped:
            continue
        a, b = P[i], P[j]
        e = b - a
        L = np.linalg.norm(e)
        if L < 1e-12:
            continue
        nn = np.array([-e[1], e[0]]) / L
        d = np.abs((P[skipped] - a) @ nn)
        k2 = int(np.argmax(d))
        if float(d[k2]) > best[0]:
            best = (float(d[k2]), skipped[k2], i, j)
    return best


def convexity_defect(poly):
    """DEPTH of the deepest concavity, in metres — the OpenCV definition.

    This is the number that says whether a CONVEX_HULL collider is honest: it is
    how far the hull stands proud of the real shard at the worst place, i.e. the
    thickness of the phantom material the solver would push against.

    NOT "distance from the polygon to the hull", which is identically zero for
    every simple polygon and is therefore an instrument that cannot fail.  It
    was, for one revision, and its positive control caught it.
    """
    P = np.asarray(poly, float)
    if len(P) < 4:
        return 0.0
    h = hull_indices(P)
    if len(h) < 3:
        return 0.0
    hs = set(h)
    # walk the polygon; between two consecutive hull vertices IN POLYGON ORDER
    # sit the skipped vertices, and their distance to the chord is the defect
    ring = [i for i in range(len(P))]
    hull_pos = [i for i in ring if i in hs]
    if len(hull_pos) < 2:
        return 0.0
    worst = 0.0
    for k in range(len(hull_pos)):
        i = hull_pos[k]
        j = hull_pos[(k + 1) % len(hull_pos)]
        skipped = []
        m = (i + 1) % len(P)
        while m != j:
            skipped.append(m)
            m = (m + 1) % len(P)
        if not skipped:
            continue
        a, b = P[i], P[j]
        e = b - a
        L = np.linalg.norm(e)
        if L < 1e-12:
            continue
        nn = np.array([-e[1], e[0]]) / L
        d = np.abs((P[skipped] - a) @ nn)
        worst = max(worst, float(np.max(d)))
    return worst


def principal(poly):
    """(aspect_ratio, long_axis_unit_vector) from the area second moment.

    Vertex covariance would be wrong: it weights a corner cluster as heavily as
    a long straight edge.  This integrates over the POLYGON by triangulating
    about the centroid, so a long thin shard reads as long and thin whatever its
    vertex count.
    """
    P = np.asarray(poly, float)
    c = centroid(P)
    Q = P - c
    n = len(Q)
    M = np.zeros((2, 2))
    tot = 0.0
    for i in range(n):
        a, b = Q[i], Q[(i + 1) % n]
        A = 0.5 * (a[0] * b[1] - a[1] * b[0])
        if abs(A) < 1e-18:
            continue
        # second moment of a triangle (0, a, b) about the origin
        for u, v in ((a, a), (b, b), (a, b)):
            M += (A / 12.0) * np.outer(u, v)
            M += (A / 12.0) * np.outer(v, u)
        tot += A
    if abs(tot) < 1e-15:
        return 1.0, np.array([1.0, 0.0])
    M = M / tot
    w, V = np.linalg.eigh(M)
    w = np.clip(w, 1e-18, None)
    ar = float(math.sqrt(w[1] / w[0]))
    return ar, V[:, 1]


def min_width(poly):
    """Area divided by the extent along the long principal axis, in metres —
    the mean width of the piece, and the number the hair rule is written in."""
    P = np.asarray(poly, float)
    A = abs(area(P))
    ar, ax = principal(P)
    t = P @ ax
    L = float(t.max() - t.min())
    return A / L if L > 1e-12 else 0.0


def is_hair(poly):
    if len(poly) < 3:
        return True
    if abs(area(poly)) < SLIVER_M2:
        return True
    if min_width(poly) < W_MIN_M:
        return True
    return principal(poly)[0] > AR_HARD


def reflex_vertices(P):
    """Indices of the polygon's re-entrant corners, deepest first."""
    P = np.asarray(P, float)
    n = len(P)
    if n < 4:
        return []
    out = []
    for i in range(n):
        a, b, c = P[(i - 1) % n], P[i], P[(i + 1) % n]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if cr < 0:                       # CCW polygon -> negative == reflex
            out.append((abs(cr), i))
    out.sort(reverse=True)
    return [i for _, i in out]


def convexify(poly, tol=0.003, max_cuts=6):
    """Split a shard until no concavity is deeper than `tol`.

    NOT a cosmetic step and not a solver workaround.  A re-entrant corner in
    glass is a stress raiser with a notch radius of a few microns; it is the
    single most likely place for a fragment to break again, and a fragment that
    kept one would be the unphysical object.  Cutting it is what the material
    does.

    It is ALSO what makes the CONVEX_HULL collider honest: after this pass the
    hull stands proud of the real shard by at most `tol`, and that number is
    published rather than assumed.  The cut extends an edge incident on the
    deepest reflex vertex, which is the classical convex-decomposition cut and
    is guaranteed to lie inside the polygon.
    """
    P0 = np.asarray(poly, float)
    if area(P0) < 0:                     # reflex_vertices assumes CCW
        P0 = P0[::-1]
    todo = [P0]
    done = []
    guard = 0
    while todo:
        guard += 1
        if guard > 4000:
            done.extend(todo)
            break
        P = todo.pop()
        if area(P) < 0:
            P = P[::-1]
        if convexity_defect(P) <= tol or len(P) < 4:
            done.append(P)
            continue
        rv = reflex_vertices(P)
        if not rv:
            done.append(P)
            continue
        d0 = convexity_defect(P)
        cut_ok = False
        n = len(P)
        # The cut EXTENDS an edge incident on the reflex vertex — the classical
        # convex-decomposition cut, guaranteed to enter the interior.  It is
        # offset off the vertex by EPS along its own normal, because a cut that
        # passes exactly THROUGH a vertex is tangential there: `split` sees one
        # sign change instead of two and hands back a pinched polygon with the
        # vertex in it twice.  That is what the first revision did, and the
        # +ve control caught it as "convexify changes nothing".
        EPS = 2.0e-4
        # CANDIDATE ZERO, and the one that almost always wins: cut through the
        # deepest notch vertex PERPENDICULAR TO THE HULL CHORD it hangs from.
        # That runs straight out of the notch into open interior and leaves two
        # chunky halves.  Extending an incident edge — the classical cut, kept
        # below as the fallback — shaves a wedge whenever the reflex vertex sits
        # on a short edge, and the hair rule then refuses it, which is how this
        # module spent a revision reporting a 26 mm hull defect it could not
        # cut out.
        dep, iv, ia, ib = deepest_notch(P)
        pre = []
        if iv >= 0 and dep > tol:
            e = P[ib] - P[ia]
            L = np.linalg.norm(e)
            if L > 1e-12:
                e = e / L
                nn = np.array([-e[1], e[0]])
                for sgn in (+1.0, -1.0):
                    pre.append((P[iv] + sgn * EPS * e, nn))
        for i in ([iv] if iv >= 0 else []) + rv[:max_cuts]:
            if i < 0:
                continue
            cands = list(pre)
            pre = []
            for d in (P[i] - P[(i - 1) % n], P[(i + 1) % n] - P[i]):
                L = np.linalg.norm(d)
                if L < 1e-12:
                    continue
                d = d / L
                nn = np.array([-d[1], d[0]])
                for sgn in (+1.0, -1.0):
                    cands.append((P[i] + sgn * EPS * nn, d))
            ext = float(np.max(np.linalg.norm(P - P[i], axis=1)))
            for p, d in cands:
                c = Cut(p, d, 3.0 * ext + 1e-3, np.random.default_rng(0),
                        0.0, levels=2, kind="notch")
                a, b = split(P, c)
                if a is None or b is None or len(a) < 3 or len(b) < 3:
                    continue
                if min(abs(area(a)), abs(area(b))) < 1e-9:
                    continue
                if _pinched(a) or _pinched(b):
                    continue
                if is_hair(a) or is_hair(b):
                    continue
                if max(convexity_defect(a), convexity_defect(b)) >= d0 - 1e-9:
                    continue                    # no progress: try another cut
                todo.extend([a, b])
                cut_ok = True
                break
            if cut_ok:
                break
        if not cut_ok:
            done.append(P)
    return done


def _pinched(poly, tol=1e-9):
    """True if two NON-ADJACENT vertices coincide — a polygon that touches
    itself.  `_dedupe` cannot see these because they are not neighbours."""
    P = np.asarray(poly, float)
    n = len(P)
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if np.linalg.norm(P[i] - P[j]) < tol:
                return True
    return False


# --------------------------------------------------------------------------- #
#  2.  THE ENERGY FIELD.  Impactors are SEGMENTS, not a point.
# --------------------------------------------------------------------------- #

class Impact(object):
    """Where the car touches this pane, in the pane's own (u = y, v = z) frame.

    Each impactor is a segment with a weight.  `energy` is a 0..1 field and
    `target_area` turns it into the local shard size.
    """

    # a_max is NOT a taste knob.  Away from the contact the pane is not being
    # comminuted, it is FOLDING about the mullion it just lost, and a folding
    # 11.5 mm laminate spanning 2.17 m sheds fragments of the order of a quarter
    # to a half of the span.  0.25 m2 is a 0.50 m fragment, which is the top of
    # that range and matches the manifest's "holds slabs at the frame" and its
    # 900 mm upper size (the biggest survive on the clamped edge, uncut).
    # It was 0.090 m2 for one revision and capped EVERY pane at a 300 mm slab,
    # including the two that the car never touches and that fail purely in
    # bending.
    # p was 2.0 when a_max was 0.090.  Raising a_max to 0.250 multiplied the
    # whole second term by 2.8x and the crushed zone lost its extent with it:
    # 72 mm off the wing line went from a 46 mm cell to a 69 mm one, and the
    # selftest caught it only because it was re-run.  p = 2.6 puts it back to
    # 49 mm and leaves the far field where the folding argument wants it.
    def __init__(self, segments, lam=0.42, a_min=6.25e-4, a_max=0.250,
                 p=2.6, q=1.7):
        self.seg = [(np.asarray(a, float), np.asarray(b, float), float(w))
                    for a, b, w in segments]
        self.lam = lam
        self.a_min = a_min
        self.a_max = a_max
        self.p = p
        self.q = q

    def dist(self, q):
        q = np.atleast_2d(np.asarray(q, float))
        best = np.full(len(q), 1e9)
        for a, b, w in self.seg:
            ab = b - a
            L2 = float(ab @ ab)
            t = np.zeros(len(q)) if L2 < 1e-12 else \
                np.clip(((q - a) @ ab) / L2, 0.0, 1.0)
            d = np.linalg.norm(q - (a + t[:, None] * ab), axis=1) / max(w, 1e-6)
            best = np.minimum(best, d)
        return best

    def energy(self, q):
        # A STRETCHED exponential, not a plain one.  exp(-d/lam) starts falling
        # at full rate from d = 0, so a plain exponential gives the comminuted
        # zone no EXTENT: 72 mm off the wing line it had already coarsened to a
        # 108 mm cell.  q = 1.7 gives the crushed zone a flat top the width of
        # the contact, which is what a comminuted zone is.
        return np.exp(-(self.dist(q) / self.lam) ** self.q)

    def target_area(self, q):
        e = self.energy(q)
        return self.a_min + (self.a_max - self.a_min) * (1.0 - e) ** self.p

    def origin(self):
        """The single point the radial cracks fan from: the weighted centroid
        of the impactor segments."""
        num = np.zeros(2)
        den = 0.0
        for a, b, w in self.seg:
            num += w * 0.5 * (a + b)
            den += w
        return num / max(den, 1e-9)


def car_impactors(pane_u0, pane_u1):
    """The car's own strike geometry, clipped to this pane's u span.

    z values are the car's, taken at the frame its nose reaches x = 15.000.
    Weights are RELATIVE STIFFNESS, not force: the nose cone and the front
    tyres carry the load, the wing endplates are the first thing to arrive and
    the least stiff.
    """
    segs = [
        # front wing, full width, first contact, low and compliant
        ((-0.950, 0.128), (0.950, 0.128), 0.55),
        # wing endplates: stiff vertical fins
        ((-0.950, 0.070), (-0.950, 0.290), 0.85),
        ((0.950, 0.070), (0.950, 0.290), 0.85),
        # nose cone tip, the stiffest single point on the car
        ((-0.075, 0.415), (0.075, 0.415), 1.60),
        # front tyres, 0.36 m radius, contact band
        ((-0.900, 0.180), (-0.560, 0.540), 1.20),
        ((0.560, 0.540), (0.900, 0.180), 1.20),
        # halo / airbox crown, arrives late, high
        ((-0.220, 0.960), (0.220, 0.960), 0.45),
    ]
    out = []
    for a, b, w in segs:
        if max(a[0], b[0]) < pane_u0 - 1.2 or min(a[0], b[0]) > pane_u1 + 1.2:
            continue
        out.append((a, b, w))
    if not out:                      # a pane the car never touches
        out = [((0.0, 0.128), (0.0, 0.415), 0.25)]
    return out


# --------------------------------------------------------------------------- #
#  3.  THE PANE.  Radials, then hoops, then mosaic.
# --------------------------------------------------------------------------- #

class Pane(object):
    def __init__(self, bay, u0, u1, v0, v1, hidden, seed,
                 impact, role="destroyed"):
        self.bay = bay
        self.rect = (u0, u1, v0, v1)
        self.hidden = hidden          # metres of every edge under the plate
        self.seed = seed
        self.impact = impact
        self.role = role              # destroyed | retained | intact
        self.shards = []

    def poly(self):
        u0, u1, v0, v1 = self.rect
        return np.array([[u0, v0], [u1, v0], [u1, v1], [u0, v1]])


def fracture_pane(pane, n_radial=None, hoop_growth=1.62, max_shards=4000,
                  verbose=False):
    """Cut one pane.  Returns a list of shard dicts."""
    rng = np.random.default_rng(pane.seed)
    u0, u1, v0, v1 = pane.rect
    diag = math.hypot(u1 - u0, v1 - v0)
    o = pane.impact.origin()

    pieces = [dict(poly=pane.poly(), gen=0, wedge=0)]
    pane.dropped_area = 0.0

    if pane.role == "intact":
        return _finish(pane, pieces)

    # ---- 3a. RADIAL cracks ------------------------------------------------- #
    # A struck pane throws 8-16 radials.  They are NOT evenly spaced: the count
    # rises with impact energy and the spacing is jittered, because a radial
    # nucleates at whichever flaw is closest to the peak tensile hoop stress.
    if n_radial is None:
        e = float(pane.impact.energy(o[None, :])[0])
        n_radial = int(round(6 + 9 * e)) if pane.role == "destroyed" else \
            int(round(3 + 4 * e))
    base = rng.uniform(0, math.pi)
    angs = np.sort((base + np.arange(n_radial) * math.pi / n_radial
                    + rng.normal(0, 0.20, n_radial)) % math.pi)
    for k, a in enumerate(angs):
        d = np.array([math.cos(a), math.sin(a)])
        amp = 0.014 * diag
        cut = Cut(o, d, 1.2 * diag, rng, amp, levels=5, kind="radial", gen=1)
        nxt = []
        for pc in pieces:
            pos, neg = split(pc["poly"], cut)
            if pos is None or neg is None:
                nxt.append(pc)
                continue
            if is_hair(pos) or is_hair(neg):     # the crack merges instead
                nxt.append(pc)
                continue
            for q, sgn in ((pos, +1), (neg, -1)):
                nxt.append(dict(poly=q, gen=1,
                                wedge=pc["wedge"] * 2 + (1 if sgn > 0 else 0)))
        pieces = nxt

    # ---- 3b. HOOP cracks, which ARREST on the radials ---------------------- #
    # Confined to the wedge piece they are born in, which is the arrest rule
    # made structural rather than drawn.  Radii grow geometrically: the plate
    # rebounds with a decaying wavelength.
    r = 0.075 + 0.05 * rng.random()
    radii = []
    while r < 1.15 * diag:
        radii.append(r)
        r *= hoop_growth * (1.0 + rng.normal(0, 0.10))
    for r in radii:
        nxt = []
        for pc in pieces:
            c = centroid(pc["poly"])
            rc = float(np.linalg.norm(c - o))
            # only cut pieces the arc actually crosses
            rr = np.linalg.norm(pc["poly"] - o, axis=1)
            if rr.min() > r or rr.max() < r:
                nxt.append(pc)
                continue
            if rng.random() > 0.82:          # not every arc reaches every wedge
                nxt.append(pc)
                continue
            # the hoop's local tangent at this piece
            u = (c - o)
            nu = np.linalg.norm(u)
            if nu < 1e-9:
                nxt.append(pc)
                continue
            u = u / nu
            tang = np.array([-u[1], u[0]])
            p = o + u * r
            amp = 0.030 * r + 0.004
            cut = Cut(p, tang, 1.2 * diag, rng, amp, levels=4,
                      kind="hoop", gen=2)
            pos, neg = split(pc["poly"], cut)
            if pos is None or neg is None or is_hair(pos) or is_hair(neg):
                nxt.append(pc)
                continue
            for q in (pos, neg):
                nxt.append(dict(poly=q, gen=2, wedge=pc["wedge"]))
        pieces = nxt

    # ---- 3c. MOSAIC: split until the piece is below its local target ------- #
    # Anisotropic: the cut direction prefers RADIAL near the strike (long
    # slivers pointing at the impact) and is free further out.  Depth-limited so
    # a pathological piece cannot recurse forever.
    out = []
    stack = list(pieces)
    guard = 0
    while stack:
        guard += 1
        if guard > 400000 or len(out) + len(stack) > max_shards:
            out.extend(stack)
            break
        pc = stack.pop()
        A = abs(area(pc["poly"]))
        c = centroid(pc["poly"])
        tgt = float(pane.impact.target_area(c[None, :])[0])
        nu = float(np.linalg.norm(c - o))
        ar, ax = principal(pc["poly"])
        ar_max = AR_NEAR if nu < AR_R_M else AR_FAR
        too_long = ar > ar_max and A > AR_FLOOR_FRAC * tgt
        if (A <= tgt and not too_long) or pc["gen"] >= 16 \
                or len(pc["poly"]) > 64:
            out.append(pc)
            continue
        u = c - o
        if too_long:
            # a needle gets cut ACROSS its own long axis, wherever it is
            d = np.array([-ax[1], ax[0]])
            mix = rng.normal(0.0, 0.18)
            ca, sa = math.cos(mix), math.sin(mix)
            d = np.array([ca * d[0] - sa * d[1], sa * d[0] + ca * d[1]])
        elif nu < 1e-6:
            ang = rng.uniform(0, math.pi)
            d = np.array([math.cos(ang), math.sin(ang)])
        else:
            rad = u / nu
            tang = np.array([-rad[1], rad[0]])
            # THE SLIVER BAND.  Radial slivers are a MID-FIELD feature: right at
            # the contact the plate is comminuted and the mosaic is equiaxed;
            # out at the head of the pane the plate is FOLDING about the lost
            # mullion and sheds roughly equiaxed slabs.  Between the two — call
            # it half a metre to two metres — the radials are the dominant free
            # surfaces and the pieces beside them are long.  A monotone
            # "more radial the further out you go" rule (the first revision) put
            # six-metre needles at the head of every pane.
            w = math.exp(-((nu - 0.90) / 0.80) ** 2)      # radial preference
            d = (w * rad + (1.0 - w) * tang)
            d = d / np.linalg.norm(d)
            # ... and the far field is close to isotropic, which is what turns
            # the slab field at the head from a fan into rubble.
            mix = rng.normal(0.0, 0.22 + 0.95 * (1.0 - w))
            ca, sa = math.cos(mix), math.sin(mix)
            d = np.array([ca * d[0] - sa * d[1], sa * d[0] + ca * d[1]])
        # cut through a point near the centroid, offset so children differ.
        # SIX ATTEMPTS, not one.  With a single attempt an unlucky cut retires
        # the piece for good, and the failure mode is silent and spectacular:
        # one 0.827 m2 slab — a 0.91 m sheet of glass, nine times the local
        # target area — survived in the middle of bay 5 because the first
        # random chord it drew grazed a corner.  The picture is where that was
        # caught; no number in the report was outside its tolerance.
        ext = float(np.max(np.linalg.norm(pc["poly"] - c, axis=1)))
        pos = neg = None
        for _try in range(MOSAIC_TRIES):
            p = c + rng.normal(0, 0.16 * ext, 2)
            dd = d
            if _try:
                r_ = rng.normal(0.0, 0.5)
                ca, sa = math.cos(r_), math.sin(r_)
                dd = np.array([ca * d[0] - sa * d[1], sa * d[0] + ca * d[1]])
            cut = Cut(p, dd, 3.0 * ext + 1e-3, rng, 0.055 * ext, levels=4,
                      kind="mosaic", gen=pc["gen"] + 1)
            a_, b_ = split(pc["poly"], cut)
            if a_ is None or b_ is None or is_hair(a_) or is_hair(b_):
                continue
            if min(abs(area(a_)), abs(area(b_))) < 0.02 * A:
                continue
            pos, neg = a_, b_
            break
        if pos is None:
            pc["stuck"] = True
            out.append(pc)
            continue
        for q in (pos, neg):
            stack.append(dict(poly=q, gen=pc["gen"] + 1, wedge=pc["wedge"]))
    # ---- 3d. NO RE-ENTRANT CORNERS SURVIVE --------------------------------- #
    fin = []
    for pc in out:
        for q in convexify(pc["poly"], tol=CONVEX_TOL_M):
            fin.append(dict(poly=q, gen=pc["gen"], wedge=pc.get("wedge", 0)))
    if verbose:
        print("   bay %-2d %-10s %2d radials, %2d hoop radii -> %4d pieces "
              "-> %4d after convexify (dropped %.3e m2)"
              % (pane.bay, pane.role, n_radial, len(radii), len(out),
                 len(fin), pane.dropped_area))
    return _finish(pane, fin)


def _finish(pane, pieces):
    """Attach the per-shard facts the sim and the mesher need."""
    u0, u1, v0, v1 = pane.rect
    hid = pane.hidden
    o = pane.impact.origin()
    rng = np.random.default_rng(pane.seed ^ 0x5EED)
    out = []
    for i, pc in enumerate(pieces):
        P = pc["poly"]
        if area(P) < 0:
            P = P[::-1]
        c = centroid(P)
        A = abs(area(P))
        ar, _ax = principal(P)
        # touching the clamped bite?  those shards are held by the plate.
        near = (P[:, 0] < u0 + hid + 1e-6) | (P[:, 0] > u1 - hid - 1e-6) | \
               (P[:, 1] < v0 + hid + 1e-6) | (P[:, 1] > v1 - hid - 1e-6)
        out.append(dict(
            id=i, poly=P, area=A, centroid=c, gen=pc["gen"], aspect=ar,
            wedge=pc.get("wedge", 0),
            r_impact=float(np.linalg.norm(c - o)),
            clamped=bool(near.any()),
            energy=float(pane.impact.energy(c[None, :])[0]),
            # 15 % of shards keep a PVB bridge to a neighbour (manifest axis 4)
            laminated=bool(rng.random() < 0.15),
        ))
    pane.shards = out
    if not hasattr(pane, "dropped_area"):
        pane.dropped_area = 0.0
    return out


# --------------------------------------------------------------------------- #
#  4.  THE WALL'S TEN PANES
# --------------------------------------------------------------------------- #

def build_wall_plan(seed=20260803, verbose=False):
    """Fracture every pane of the east curtain wall.  Returns (panes, meta)."""
    W = wall()
    pockets = W["glazing_pockets"]
    bs = {b["uid"]: b["beat3"] for b in W["breach_state"]}
    panes = []
    for pk in pockets:
        bay = pk["bay"]
        m0, m1 = pk["between"]
        y0, y1 = pk["cut_rect_world"]["y"]
        z0, z1 = pk["cut_rect_world"]["z"]
        s0, s1 = bs[m0], bs[m1]
        # a pane whose BOTH mullions are gone falls; one gone = retained by the
        # surviving jamb and the PVB; neither = intact, but still pre-fractured
        # so the wall is one system and nothing has to be swapped in later.
        gone = sum(1 for s in (s0, s1) if s == "destroyed")
        bent = sum(1 for s in (s0, s1) if s == "bent_stub")
        if gone == 2 or (gone == 1 and bent == 1):
            role = "destroyed"
        elif gone or bent:
            role = "retained"
        else:
            role = "intact"
        imp = Impact(car_impactors(y0, y1))
        pane = Pane(bay, y0, y1, z0, z1, pk["hidden_each_edge_m"],
                    seed + 1013 * bay, imp, role)
        fracture_pane(pane, verbose=verbose)
        panes.append(pane)
    meta = dict(seed=seed, section=W["section"],
                breach_state=W["breach_state"],
                n_panes=len(panes),
                n_shards=sum(len(p.shards) for p in panes))
    return panes, meta


# --------------------------------------------------------------------------- #
#  7.  ADJACENCY — which shards were joined, and how strongly.
# --------------------------------------------------------------------------- #
#  A PRE-FRACTURED PANE IS STILL A PANE.  Nothing above this line says so, and
#  the first wake-all null control found out the hard way: with only the 582
#  clamped-edge constraints and the 444 PVB bridges holding it, a vertical wall
#  of 2,987 loose tiles has no load path at all — gravity is resisted only by
#  friction on near-vertical crack faces — so it slumps before the car arrives.
#
#  The physical object is a SOLID with cracks in it that have not opened.  Every
#  pair of shards that shares boundary is BONDED, and the bond's strength is the
#  glass's own tensile strength across the area of that shared boundary:
#
#      bond area = shared edge length x 11.5 mm laminate
#
#  so a shard joined to its neighbour along 300 mm holds twenty times what one
#  joined along 15 mm does.  The crack front then PROPAGATES: the impact breaks
#  the bonds it can reach, those shards load their neighbours, and the aperture
#  is the set of bonds that failed.  Nothing about which shards leave the wall is
#  authored.
#
#  Computed here rather than in Blender because it wants a KD-tree and the venv
#  has scipy; the result is a table in the .npz and the sim just reads it.

def adjacency(shards, step=0.006, tol=0.0045):
    """[(i, j, shared_len_m)] for every pair of shards that share boundary.

    Boundaries are SAMPLED rather than matched vertex-for-vertex, because a cut
    that lands on an already-shared edge inserts a crossing point into one child
    and not into its neighbour — a T-junction.  Exact vertex matching would miss
    every one of those, and they are the majority after ten generations.
    """
    from scipy.spatial import cKDTree

    pts, owner = [], []
    for k, s in enumerate(shards):
        P = np.asarray(s["poly"], float)
        n = len(P)
        for i in range(n):
            a, b = P[i], P[(i + 1) % n]
            L = float(np.linalg.norm(b - a))
            m = max(1, int(round(L / step)))
            t = np.arange(m) / float(m)
            pts.append(a + (b - a) * t[:, None])
            owner.extend([k] * m)
    pts = np.vstack(pts)
    owner = np.asarray(owner)
    tree = cKDTree(pts)
    prs = tree.query_pairs(r=tol, output_type="ndarray")
    if len(prs) == 0:
        return []
    oa, ob = owner[prs[:, 0]], owner[prs[:, 1]]
    m = oa != ob
    oa, ob = oa[m], ob[m]
    lo = np.minimum(oa, ob)
    hi = np.maximum(oa, ob)
    key = lo.astype(np.int64) * 1000003 + hi
    uk, cnt = np.unique(key, return_counts=True)
    out = []
    for k, c in zip(uk, cnt):
        i, j = int(k // 1000003), int(k % 1000003)
        # each coincidence is one sample from each side of a `step` interval
        out.append((i, j, float(c) * step * 0.5))
    return out


def adjacency_report(shards, adj):
    n = len(shards)
    deg = np.zeros(n, int)
    for i, j, _L in adj:
        deg[i] += 1
        deg[j] += 1
    ln = np.array([L for _i, _j, L in adj]) if adj else np.array([0.0])
    return dict(shards=n, bonds=len(adj),
                bonds_per_shard=float(len(adj) * 2.0 / max(n, 1)),
                isolated=int((deg == 0).sum()),
                degree_min=int(deg.min()), degree_median=float(np.median(deg)),
                degree_max=int(deg.max()),
                shared_len_m=dict(min=float(ln.min()),
                                  median=float(np.median(ln)),
                                  max=float(ln.max())))


def save(panes, meta, path=None, with_adjacency=True):
    path = path or os.path.join(OUT, "fracture_wall.npz")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    d = {}
    idx = []
    verts = []
    off = 0
    for p in panes:
        for s in p.shards:
            n = len(s["poly"])
            verts.append(s["poly"])
            idx.append((p.bay, s["id"], off, n, s["gen"], s["wedge"],
                        s["area"], s["r_impact"], s["energy"],
                        1 if s["clamped"] else 0, 1 if s["laminated"] else 0,
                        s["aspect"]))
            off += n
    d["verts"] = np.vstack(verts).astype(np.float64)
    d["index"] = np.array(idx, dtype=np.float64)
    d["rects"] = np.array([p.rect for p in panes], dtype=np.float64)
    if with_adjacency:
        rows = []
        for p in panes:
            if p.role == "intact" or len(p.shards) < 2:
                continue
            adj = adjacency(p.shards)
            meta.setdefault("adjacency", {})[str(p.bay)] = \
                adjacency_report(p.shards, adj)
            for i, j, L in adj:
                rows.append((p.bay, p.shards[i]["id"], p.shards[j]["id"], L))
        d["bonds"] = np.array(rows, dtype=np.float64) if rows \
            else np.zeros((0, 4))
    d["roles"] = np.array([p.role for p in panes])
    d["bays"] = np.array([p.bay for p in panes])
    np.savez_compressed(path, **d)
    with open(path.replace(".npz", ".json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    return path


def load(path=None):
    path = path or os.path.join(OUT, "fracture_wall.npz")
    z = np.load(path, allow_pickle=False)
    V, I = z["verts"], z["index"]
    panes = {}
    for row in I:
        bay = int(row[0])
        off, n = int(row[2]), int(row[3])
        panes.setdefault(bay, []).append(dict(
            id=int(row[1]), poly=V[off:off + n], gen=int(row[4]),
            wedge=int(row[5]), area=float(row[6]), r_impact=float(row[7]),
            energy=float(row[8]), clamped=bool(row[9]),
            laminated=bool(row[10]), aspect=float(row[11]),
            centroid=centroid(V[off:off + n])))
    bonds = {}
    if "bonds" in z.files:
        for row in z["bonds"]:
            bonds.setdefault(int(row[0]), []).append(
                (int(row[1]), int(row[2]), float(row[3])))
    return dict(panes=panes,
                rects={int(b): tuple(r) for b, r in zip(z["bays"], z["rects"])},
                roles={int(b): str(r) for b, r in zip(z["bays"], z["roles"])},
                bonds=bonds)


# --------------------------------------------------------------------------- #
#  5.  MEASUREMENT.  Every claim above, as a number.
# --------------------------------------------------------------------------- #

def convexity_report(panes):
    worst, tot, n = 0.0, 0.0, 0
    which = None
    for p in panes:
        for s in p.shards:
            d = convexity_defect(s["poly"])
            tot += d
            n += 1
            if d > worst:
                worst, which = d, (p.bay, s["id"])
    return dict(max_m=worst, mean_m=tot / max(n, 1), n=n, worst_shard=which)


def partition_report(panes):
    """Does the union of the shards equal the pane?  Area is the cheap test and
    it is also the sufficient one for a recursive split: overlap and gap both
    show up as a residual."""
    out = []
    for p in panes:
        u0, u1, v0, v1 = p.rect
        A = (u1 - u0) * (v1 - v0)
        a = sum(s["area"] for s in p.shards)
        out.append(dict(bay=p.bay, role=p.role, n=len(p.shards),
                        rect_area=A, shard_area=a, residual=a - A,
                        dropped=getattr(p, "dropped_area", 0.0),
                        unaccounted=a - A + getattr(p, "dropped_area", 0.0),
                        min_area=min(s["area"] for s in p.shards),
                        max_area=max(s["area"] for s in p.shards)))
    return out


def selftest():
    """Positive controls that FAIL and negative controls that pass."""
    fails = []

    def check(name, cond, detail=""):
        print("  %-46s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            fails.append(name)

    rng = np.random.default_rng(7)
    sq = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])

    # -- a single cut conserves area, exactly
    c = Cut([0.5, 0.5], [1.0, 0.3], 3.0, rng, 0.03)
    a, b = split(sq, c)
    check("one cut conserves area to 1e-12",
          a is not None and b is not None and
          abs(abs(area(a)) + abs(area(b)) - 1.0) < 1e-12,
          "residual %.3e" % (abs(area(a)) + abs(area(b)) - 1.0))

    # -- POSITIVE CONTROL: a cut that misses must not split
    c2 = Cut([5.0, 5.0], [1.0, 0.0], 3.0, rng, 0.0)
    a2, b2 = split(sq, c2)
    check("a cut that misses returns one piece",
          (a2 is None) != (b2 is None))

    # -- the shared boundary is the SAME numbers on both sides
    c3 = Cut([0.5, 0.5], [0.2, 1.0], 3.0, rng, 0.05)
    a3, b3 = split(sq, c3)
    sh = 0
    for q in a3:
        if np.min(np.linalg.norm(b3 - q, axis=1)) < 1e-15:
            sh += 1
    check("shared edge vertices are bit-identical", sh >= 2,
          "%d shared verts" % sh)

    # -- POSITIVE CONTROL: a deliberately mismatched pattern must be caught
    bad = a3.copy()
    bad[0] = bad[0] + np.array([1e-4, 0.0])
    sh2 = sum(1 for q in bad
              if np.min(np.linalg.norm(b3 - q, axis=1)) < 1e-15)
    check("+ve control: a 0.1 mm nudge loses a shared vert", sh2 < sh,
          "%d -> %d" % (sh, sh2))

    # -- the convexity metric is not identically zero
    tri = np.array([[0, 0], [1, 0], [0.5, 0.1], [1, 1], [0, 1]], float)
    check("+ve control: convexity_defect fires on a concave poly",
          convexity_defect(tri) > 0.05,
          "%.4f m" % convexity_defect(tri))
    check("-ve control: convexity_defect ~0 on a square",
          convexity_defect(sq) < 1e-12)

    # -- the energy field is not uniform (the whole point of it)
    imp = Impact(car_impactors(-1.085, 1.085))
    lo = float(imp.target_area(np.array([[0.0, 0.415]]))[0])   # the nose tip
    mid = float(imp.target_area(np.array([[0.0, 0.200]]))[0])  # 72 mm off it
    hi = float(imp.target_area(np.array([[0.0, 5.800]]))[0])   # pane head
    check("target area grows >40x from strike to head", hi / lo > 40.0,
          "%.2e -> %.2e m2 (%.0fx)" % (lo, hi, hi / lo))
    check("the crushed zone has EXTENT (72 mm out still < 4x a_min)",
          mid < 4.0 * imp.a_min,
          "%.2e m2 = %.0f mm cell" % (mid, 1000 * math.sqrt(mid)))

    # -- a whole pane
    pane = Pane(4, -1.085, 1.085, 0.0875, 6.1125, 0.0225, 4242,
                imp, "destroyed")
    fracture_pane(pane)
    A = 2.170 * 6.025
    a = sum(s["area"] for s in pane.shards)
    un = a - A + pane.dropped_area
    check("partition leaks NOTHING unaccounted (< 1e-9 m2)", abs(un) < 1e-9,
          "%d shards, residual %.3e, dropped %.3e, unaccounted %.3e m2"
          % (len(pane.shards), a - A, pane.dropped_area, un))
    check("discarded sliver area < 1 mm2", pane.dropped_area < 1e-6,
          "%.3e m2" % pane.dropped_area)
    cvs = [convexity_defect(s["poly"]) for s in pane.shards]
    check("no shard's hull stands >3 mm proud of it", max(cvs) <= CONVEX_TOL_M,
          "worst %.5f m over %d shards" % (max(cvs), len(cvs)))

    # -- NO SHARD IS FAR BIGGER THAN ITS OWN LOCAL TARGET.  This is the check
    #    that catches a piece the splitter silently gave up on, and it is here
    #    because the picture caught one that every other number let through.
    ov = np.array([s["area"] / float(imp.target_area(s["centroid"][None, :])[0])
                   for s in pane.shards])
    check("no shard exceeds 3x its own local target area",
          ov.max() <= 3.0, "worst %.2fx over %d shards" % (ov.max(), len(ov)))
    # +ve control: with ONE cut attempt instead of six the slab comes back
    _saved = globals()["MOSAIC_TRIES"]
    globals()["MOSAIC_TRIES"] = 1
    one = Pane(4, -1.085, 1.085, 0.0875, 6.1125, 0.0225, 4242, imp, "destroyed")
    fracture_pane(one)
    globals()["MOSAIC_TRIES"] = _saved
    ov1 = max(s["area"] / float(imp.target_area(s["centroid"][None, :])[0])
              for s in one.shards)
    check("+ve control: one attempt leaves a shard >3x its target",
          ov1 > 3.0, "%.2fx with 1 try vs %.2fx with %d"
          % (ov1, ov.max(), MOSAIC_TRIES))

    # -- the aspect cap held
    far = [s for s in pane.shards if s["r_impact"] >= AR_R_M]
    near = [s for s in pane.shards if s["r_impact"] < AR_R_M]
    af = np.array([s["aspect"] for s in far]) if far else np.array([1.0])
    # p99 rather than max, because the hair rule (not the aspect cap) is what
    # sets the tail: a piece the cap wants to cut but the hair rule refuses to
    # keeps its aspect, and AR_HARD is the designed ceiling on that.
    check("far-field aspect p50 < 4, p99 <= 10, max <= AR_HARD",
          np.median(af) < 4.0 and np.percentile(af, 99) <= 10.0
          and af.max() <= AR_HARD * 1.01,
          "p50 %.2f p99 %.2f max %.2f (AR_HARD %.0f)"
          % (np.median(af), np.percentile(af, 99), af.max(), AR_HARD))
    check("-ve control: the cap did not flatten everything to 1:1",
          np.median([s["aspect"] for s in pane.shards]) > 1.35,
          "median %.2f:1" % np.median([s["aspect"] for s in pane.shards]))

    # -- POSITIVE CONTROL: convexify must actually be doing something
    raw = Pane(4, -1.085, 1.085, 0.0875, 6.1125, 0.0225, 4242, imp,
               "destroyed")
    import types as _t
    saved = globals()["CONVEX_TOL_M"]
    globals()["CONVEX_TOL_M"] = 10.0        # effectively off
    fracture_pane(raw)
    globals()["CONVEX_TOL_M"] = saved
    rawcv = max(convexity_defect(s["poly"]) for s in raw.shards)
    check("+ve control: with convexify off the worst defect exceeds 3 mm",
          rawcv > CONVEX_TOL_M,
          "%.5f m off vs %.5f m on" % (rawcv, max(cvs)))

    # -- determinism
    p2 = Pane(4, -1.085, 1.085, 0.0875, 6.1125, 0.0225, 4242, imp, "destroyed")
    fracture_pane(p2)
    same = (len(p2.shards) == len(pane.shards) and
            all(np.array_equal(x["poly"], y["poly"])
                for x, y in zip(p2.shards, pane.shards)))
    check("same seed -> bit-identical pattern", same)
    p3 = Pane(4, -1.085, 1.085, 0.0875, 6.1125, 0.0225, 4243, imp, "destroyed")
    fracture_pane(p3)
    check("+ve control: a different seed changes it",
          len(p3.shards) != len(pane.shards) or
          not np.array_equal(p3.shards[0]["poly"], pane.shards[0]["poly"]))

    # -- the size gradient actually landed in the shards
    near = [s["area"] for s in pane.shards if s["r_impact"] < 0.5]
    far = [s["area"] for s in pane.shards if s["r_impact"] > 3.0]
    check("shards near the strike are >8x smaller than at the head",
          near and far and (np.median(far) / np.median(near)) > 8.0,
          "median %.4f vs %.4f m2 (%.1fx)"
          % (np.median(near), np.median(far),
             np.median(far) / np.median(near)) if near and far else "")

    print("\n%d check(s) FAILED" % len(fails) if fails else "\nall checks passed")
    return 1 if fails else 0


# --------------------------------------------------------------------------- #
#  6.  LOOK AT IT.  A pattern you have not seen is a pattern you do not have.
# --------------------------------------------------------------------------- #

def preview_png(panes, path, px_per_m=260, show_seams=True):
    from PIL import Image, ImageDraw
    u0 = min(p.rect[0] for p in panes)
    u1 = max(p.rect[1] for p in panes)
    v0 = min(p.rect[2] for p in panes)
    v1 = max(p.rect[3] for p in panes)
    W = int((u1 - u0) * px_per_m) + 40
    H = int((v1 - v0) * px_per_m) + 40

    def xy(q):
        return (20 + (q[0] - u0) * px_per_m, H - 20 - (q[1] - v0) * px_per_m)

    im = Image.new("RGB", (W, H), (12, 14, 17))
    dr = ImageDraw.Draw(im)
    for p in panes:
        for s in p.shards:
            e = s["energy"]
            g = int(40 + 150 * e)
            col = (g, int(g * 1.05) + 20, int(g * 1.15) + 30)
            if p.role == "intact":
                col = (34, 40, 46)
            elif p.role == "retained":
                col = (int(col[0] * 0.6), int(col[1] * 0.6), int(col[2] * 0.7))
            dr.polygon([xy(q) for q in s["poly"]], fill=col,
                       outline=(6, 7, 9) if show_seams else None)
    for p in panes:
        a, b, c, d = p.rect
        p0, p1 = xy((a, c)), xy((b, d))
        dr.rectangle([min(p0[0], p1[0]), min(p0[1], p1[1]),
                      max(p0[0], p1[0]), max(p0[1], p1[1])],
                     outline=(210, 120, 40))
    im.save(path)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--seed", type=int, default=20260803)
    ap.add_argument("--out", default=None,
                    help="where to write the plan.  DEFAULTS TO THE SHIPPING "
                         "PLAN, sim/out/fracture_wall.npz, which every baked "
                         "table, every applied scene and every instrument is "
                         "keyed to by shard id.  Give a different path for a "
                         "second seed: overwriting the shipping plan would "
                         "silently re-number 3,796 shards under a bake that "
                         "still refers to the old ones.")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    panes, meta = build_wall_plan(seed=a.seed, verbose=True)
    os.makedirs(OUT, exist_ok=True)
    p = save(panes, meta, path=a.out)
    print("\nwrote %s" % p)
    print(json.dumps(partition_report(panes), indent=1, default=float))
    print(json.dumps(convexity_report(panes), indent=1, default=float))
    if a.preview:
        stem = os.path.splitext(a.out)[0] if a.out else os.path.join(
            OUT, "fracture_wall")
        print(preview_png(panes, stem + ".png"))
        mid = [p_ for p_ in panes if p_.bay in (3, 4, 5, 6)]
        print(preview_png(mid, stem + "_aperture.png", px_per_m=420))
    print("STAGE RESULT: fracture plan seed=%d -> %s" % (a.seed, p))


if __name__ == "__main__":
    main()


