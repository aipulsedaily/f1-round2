"""THE EAST WALL'S ALUMINIUM, CUT INTO THE PIECES THE BAKE ALREADY MOVES.

`apply_breach.py` supplies the east wall's GLASS because round 1's panes are
zero-thickness planes 33.5 mm out of position (R3).  This module does the same
job for the east wall's FRAME, and for the same reason: round 1's mullions and
transoms are single unbroken solids, so there is no piece of them that can
leave when the car goes through.  R6 has always said that somebody must bind
geometry to the `MUL*` / `TRN*` names in `sim/out/breach_film.npz`.  Nobody
ever did, so `apply_breach.build()` counted 152 frame bodies and wrote none of
them, and the film has been rendering a static grid across a 2.15 x 6.00 m hole
since the breach first shipped.

    f9_1920_f0880.png: the car is already outside, the wall is a spiderweb,
    and the frame the car went through has not moved by one vertex.

WHY THE REPLACEMENT IS CUT FROM ROUND 1'S SECTION AND NOT FROM THE SIM'S
=======================================================================
The two disagree, and the disagreement is measured, not assumed:

    round 1 GW_Right_Mull_*      x 14.920 .. 15.080   (cap face 80 mm EAST of
                                                       the breach plane)
    the sim / wall_iface         x 14.840 .. 15.000   (cap face ON it)

    round 1 GW_Right_Transom_*   z 1.350 / 2.850 / 4.350
    wall_iface transom_landings  z 1.600 / 3.100 / 4.600   (250 mm apart)

`mullion_intact.section()` says x = 15.000 is the outermost surface and that
nothing in the assembly may sit east of it, so on the declared interface it is
ROUND 1 that is wrong, twice.  Supplying the frame at the interface position
would be the consistent thing to do — and it would move every mullion 80 mm and
every transom 250 mm across the WHOLE east elevation, which beat 1 looks at for
33 seconds from 1.6 m, where 250 mm is 583 px.  That is a large, deliberate,
separately-judged change to a shipped beat, and it is not what this module was
asked to fix.

So the replacement is cut from ROUND 1'S OWN BOX, at round 1's coordinates, and
merely PARTITIONED the way the bake partitions it.  Consequences, all intended:

  * every east-wall frame member the bake did not break keeps its round 1
    vertices exactly, so six of the ten bays are a PIXEL-IDENTICAL negative
    control on the whole change — same fix, same two builds, no geometry moved,
    so they must not move.  (R2-150's lesson, applied to a region that is not
    occluded but is simply untouched.)
  * beat 1 is bit-identical up to the release frame, because a piece that has
    not been released yet renders at its home pose, which is where round 1's
    solid was.  There is no swap, no hide, no pop: the members are present on
    all 2,978 frames and the ones that break simply start moving.
  * the trajectory a flying piece follows is the bake's, rigidly, about the
    SIM body's own centre — so a round 1 piece lands within the 80 mm the two
    sections differ by.  For a 0.775 m bar thrown 4.7 m onto an apron that is
    the last significant figure.

WHAT THE BAKE ACTUALLY SAYS, WHICH IS LESS THAN THE HEADLINE
============================================================
Measured over `sim/out/breach_film.npz`, maximum travel of any body:

    mullion 5   4.742 m   segments S00 and S01 (z 0.000 .. 1.550) leave
    mullion 4   0.024 m   released, did not go anywhere
    mullion 6   0.026 m   released, did not go anywhere
    transoms    0.089 m   worst of all 12 released transom bodies

So faithfully applying the bake removes the bottom 1.55 m of the centre mullion
and nothing else.  This module is what puts that on screen; it is NOT by itself
a claim that the aperture then reads.  See `sim/out/eastframe_prediction.json`.

THE RULE FOR WHAT GETS REPLACED
===============================
A member is replaced iff the bake gives at least one of its bodies a RELEASE
FRAME >= 0 — the solver's own statement that a constraint on that member broke.
Not a displacement threshold, which would be a number chosen by whoever is
looking.  On the shipped table that is mullions 4, 5, 6 and transom bays 3, 4,
5, 6 at all three levels; everything else is left as round 1 built it.

Standard library + numpy only, no `bpy`, so `--selftest` runs in a second.
"""

import json
import os

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --------------------------------------------------------------------------- #
#  ROUND 1'S EAST WALL, MEASURED — world/car_anim.blend, 2026-08-04.
#  Every one of these objects is an 8-vertex axis-aligned box.  The numbers are
#  world-space AABBs read off `matrix_world @ bound_box`, not read off a script
#  that claims to have built them: round 1 is READ-ONLY and its source is not
#  this project's to trust.
# --------------------------------------------------------------------------- #
R1_MEASURED_FROM = "world/car_anim.blend SHOWROOM collection, 2026-08-04"
R1_X = (14.920, 15.080)                 # every east frame member, back .. cap
R1_MULL_HALF_Y = 0.0375                 # 75 mm sightline
R1_MULL_Z = (0.000, 6.200)
R1_MULL_Y = [-11.0 + 2.2 * i for i in range(11)]     # 11 mullion centres
R1_TRANSOM_Z = (1.350, 2.850, 4.350)    # centres; 75 mm deep
R1_TRANSOM_HALF_Z = 0.0375
R1_TRANSOM_Y = (-10.919, 11.000)        # the bar's own extent
R1_MATERIAL = "MullionAlu"

MULL_NAME = "GW_Right_Mull_%02d"
TRANSOM_NAME = "GW_Right_Transom_%d"

# what this module supplies, so a census can look for it by the name it is
# actually given rather than by round 1's name (R2-124: a metric that counts
# round 1's names reads 0 for a correct scene and for an empty wall alike)
PIECE_PREFIX = "BF_"


def _box(x0, x1, y0, y1, z0, z1):
    return (float(x0), float(x1), float(y0), float(y1), float(z0), float(z1))


def _box_verts(b):
    x0, x1, y0, y1, z0, z1 = b
    return np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1)
                     for z in (z0, z1)], float)


# faces of a box in the vertex order _box_verts emits (x major, then y, then z)
_BOX_FACES = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1],
              [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]


def box_mesh(boxes, origin):
    """One mesh out of N disjoint boxes, expressed LOCAL to `origin`."""
    V, F = [], []
    for b in boxes:
        n = len(V)
        V.extend([tuple(v - np.asarray(origin, float)) for v in _box_verts(b)])
        F.extend([[n + i for i in f] for f in _BOX_FACES])
    return V, F


def mullion_y_span(uid):
    y = R1_MULL_Y[uid]
    return (y - R1_MULL_HALF_Y, y + R1_MULL_HALF_Y)


def bay_y_span(bay):
    """Bay `bay` runs between mullion `bay` and mullion `bay`+1, clear of both.

    This reproduces round 1's own glazing rectangles: bay 3 is
    -4.3625 .. -2.2375, which is GW_Right_Glass_03 exactly.  That agreement is
    the check that the two indexings are the same indexing.
    """
    return (R1_MULL_Y[bay] + R1_MULL_HALF_Y,
            R1_MULL_Y[bay + 1] - R1_MULL_HALF_Y)


def _subtract(span, cuts):
    """[a,b] minus a list of intervals -> list of intervals, in order."""
    a, b = span
    out = [(a, b)]
    for c0, c1 in sorted(cuts):
        nxt = []
        for s0, s1 in out:
            if c1 <= s0 or c0 >= s1:
                nxt.append((s0, s1))
                continue
            if s0 < c0:
                nxt.append((s0, c0))
            if c1 < s1:
                nxt.append((c1, s1))
        out = nxt
    return [(a, b) for a, b in out if b - a > 1e-9]


# --------------------------------------------------------------------------- #

def released_members(names, release):
    """Which mullions and which transom bays did the SOLVER break?

    `release` is the frame a body's constraint let go, or -1 for never.  A
    member is broken iff any of its bodies has one.  Returns
    (set of mullion uids, set of (level, bay)).
    """
    mull, trn = set(), set()
    for n, r in zip(names, release):
        if int(r) < 0:
            continue
        if n.startswith("MUL"):
            mull.add(int(n[3:5]))
        elif n.startswith("TRN_z"):
            trn.add((int(n[5]), int(n[8:10])))
    return mull, trn


def plan(names, release, home_loc, n_seg=None):
    """The full replacement plan.  No bpy, no scene: pure arithmetic.

    names      : the bake's body names, in table order
    release    : release frame per body
    home_loc   : (n,3) each body's FIRST key location = its home centre
    n_seg      : segments per active mullion; inferred from the names if None

    Returns dict with
      delete   : round 1 objects that must go
      pieces   : [dict(name, boxes, driver, pivot, kind, member)]
                 `driver` is the bake body whose transform this piece follows,
                 or None for a piece that never moves.
      untouched: round 1 objects deliberately left alone — the negative control
    """
    idx = {n: i for i, n in enumerate(names)}
    home = {n: np.asarray(home_loc[i], float) for n, i in idx.items()}
    mull_broken, trn_broken = released_members(names, release)

    segs_of = {}
    for n in names:
        if n.startswith("MUL") and not n.endswith("_P"):
            segs_of.setdefault(int(n[3:5]), []).append(n)
    for k in segs_of:
        segs_of[k].sort()

    pieces, delete = [], []

    # ---- the mullions the solver broke -------------------------------------
    for uid in sorted(mull_broken):
        segs = segs_of[uid]
        n = n_seg or len(segs)
        if len(segs) != n:
            raise ValueError("mullion %d has %d segments, expected %d"
                             % (uid, len(segs), n))
        delete.append(MULL_NAME % uid)
        y0, y1 = mullion_y_span(uid)
        z0, z1 = R1_MULL_Z
        for k, nm in enumerate(segs):
            a = z0 + (z1 - z0) * k / n
            b = z0 + (z1 - z0) * (k + 1) / n
            pieces.append(dict(
                name="%sMUL%02d_S%02d" % (PIECE_PREFIX, uid, k),
                boxes=[_box(R1_X[0], R1_X[1], y0, y1, a, b)],
                driver=nm, pivot=home[nm].tolist(), kind="mullion",
                member="GW_Right_Mull_%02d" % uid))

    # ---- the transoms ------------------------------------------------------
    # Round 1's transom is ONE 21.9 m bar that passes THROUGH all eleven
    # mullions, so its own faces are coplanar with theirs over 75 mm at every
    # crossing.  Any crossing whose mullion is being replaced is dropped
    # entirely: it lies strictly inside that mullion's box (same x, y inside
    # +-37.5 mm, z inside 0..6.2), so nothing visible is lost, and leaving it
    # behind would hang three 75 mm blocks in mid-air once mullion 5 goes.
    # Crossings whose mullion is NOT replaced are kept VERBATIM, coplanar faces
    # and all, because the point of this module is that those bays do not move.
    for lvl, zc in enumerate(R1_TRANSOM_Z):
        broken_bays = sorted(b for (l, b) in trn_broken if l == lvl)
        if not broken_bays:
            continue
        delete.append(TRANSOM_NAME % lvl)
        za, zb = zc - R1_TRANSOM_HALF_Z, zc + R1_TRANSOM_HALF_Z
        cuts = [bay_y_span(b) for b in broken_bays]
        cuts += [mullion_y_span(u) for u in sorted(mull_broken)]
        for b in broken_bays:
            nm = "TRN_z%d_b%02d" % (lvl, b)
            by0, by1 = bay_y_span(b)
            pieces.append(dict(
                name="%sTRN%d_b%02d" % (PIECE_PREFIX, lvl, b),
                boxes=[_box(R1_X[0], R1_X[1], by0, by1, za, zb)],
                driver=nm, pivot=home[nm].tolist(), kind="transom",
                member=TRANSOM_NAME % lvl))
        rest = _subtract(R1_TRANSOM_Y, cuts)
        pieces.append(dict(
            name="%sTRN%d_STATIC" % (PIECE_PREFIX, lvl),
            boxes=[_box(R1_X[0], R1_X[1], a, b, za, zb) for a, b in rest],
            driver=None, pivot=[0.0, 0.0, 0.0], kind="transom_static",
            member=TRANSOM_NAME % lvl))

    untouched = ([MULL_NAME % u for u in range(11) if u not in mull_broken]
                 + ["GW_Right_Sill", "GW_Right_Head", "GW_Right_BaseReveal"])
    return dict(delete=sorted(delete), pieces=pieces,
                untouched=sorted(untouched),
                mullions_replaced=sorted(mull_broken),
                transoms_replaced=sorted(map(list, trn_broken)),
                rule="a member is replaced iff the bake gives one of its "
                     "bodies a release frame >= 0",
                measured_from=R1_MEASURED_FROM)


# --------------------------------------------------------------------------- #

def coverage(pl, tol=1e-6):
    """AT FRAME 1, IS THE FRAME STILL ALL THERE?

    This is the check R2-124 says every supplied-geometry module needs, and it
    is written so that it reads DIFFERENTLY for the present and the absent
    case, which `n_GW_Right_Glass` did not.  It measures LENGTH OF ALUMINIUM,
    per member, against what round 1 had:

        each replaced mullion  -> its slabs must tile z 0.000 .. 6.200
        each replaced transom  -> its bay pieces, its static remainder AND the
                                  mullion boxes that swallow the crossings must
                                  together tile y -10.919 .. 11.000

    A missing slab shortens a total.  A duplicated slab lengthens it.  Neither
    can pass by accident, and both are invisible to a name count.
    """
    out = {"members": [], "PASS": True}

    def union_len(ivs):
        ivs = sorted(ivs)
        tot, cur0, cur1 = 0.0, None, None
        for a, b in ivs:
            if cur1 is None or a > cur1 + tol:
                if cur1 is not None:
                    tot += cur1 - cur0
                cur0, cur1 = a, b
            else:
                cur1 = max(cur1, b)
        if cur1 is not None:
            tot += cur1 - cur0
        return tot

    def overlap_len(ivs):
        """total length counted more than once"""
        return sum(b - a for a, b in ivs) - union_len(ivs)

    for uid in pl["mullions_replaced"]:
        ivs = [(b[4], b[5]) for p in pl["pieces"] if p["kind"] == "mullion"
               and p["member"].endswith("%02d" % uid) for b in p["boxes"]]
        want = R1_MULL_Z[1] - R1_MULL_Z[0]
        got, dup = union_len(ivs), overlap_len(ivs)
        ok = abs(got - want) < 1e-6 and dup < 1e-6
        out["members"].append(dict(member=MULL_NAME % uid, axis="z",
                                   want_m=want, got_m=got, double_counted_m=dup,
                                   passed=ok))
        out["PASS"] &= ok

    levels = sorted({l for l, _b in pl["transoms_replaced"]})
    for lvl in levels:
        ivs = [(b[2], b[3]) for p in pl["pieces"]
               if p["member"] == TRANSOM_NAME % lvl for b in p["boxes"]]
        # the crossings that a replaced mullion now swallows are still there,
        # as part of THAT mullion's box; count them so the total is honest
        ivs += [mullion_y_span(u) for u in pl["mullions_replaced"]]
        want = R1_TRANSOM_Y[1] - R1_TRANSOM_Y[0]
        got, dup = union_len(ivs), overlap_len(ivs)
        ok = abs(got - want) < 1e-6 and dup < 1e-6
        out["members"].append(dict(member=TRANSOM_NAME % lvl, axis="y",
                                   want_m=want, got_m=got, double_counted_m=dup,
                                   passed=ok))
        out["PASS"] &= ok
    out["PASS"] = bool(out["PASS"])
    return out


# --------------------------------------------------------------------------- #

def _fake_table(n_seg=8, active=(4, 5, 6), bays=(3, 4, 5, 6)):
    """A synthetic bake table with the shipped table's shape."""
    names, rel, loc = [], [], []
    for uid in range(11):
        n = n_seg if uid in (3, 4, 5, 6, 7) else 1
        z0, z1 = 0.019, 6.219
        for k in range(n):
            for suf in ("", "_P"):
                names.append("MUL%02d_S%02d%s" % (uid, k, suf))
                rel.append(860 if uid in active else -1)
                loc.append([14.8925 if suf == "" else 14.985,
                            R1_MULL_Y[uid],
                            z0 + (z1 - z0) * (k + 0.5) / n])
    for lvl, z in enumerate((1.6, 3.1, 4.6)):
        for b in range(10):
            for suf in ("", "_P"):
                names.append("TRN_z%d_b%02d%s" % (lvl, b, suf))
                rel.append(860 if b in bays else -1)
                loc.append([14.8925 if suf == "" else 14.985,
                            0.5 * (R1_MULL_Y[b] + R1_MULL_Y[b + 1]), z])
    return names, np.array(rel), np.array(loc, float)


def selftest():
    """Eleven controls, including the two failure modes that have already cost
    this project a shipped film: geometry deleted and not put back, and a check
    that cannot tell the two apart.

        python3 sim/eastframe.py --selftest
    """
    fails = []

    def chk(name, cond, detail=""):
        print("  %-46s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            fails.append(name)

    names, rel, loc = _fake_table()
    pl = plan(names, rel, loc)

    # [1] the rule picks exactly the released members
    chk("[1] mullions replaced == released", pl["mullions_replaced"] == [4, 5, 6],
        str(pl["mullions_replaced"]))
    # [2] the bay indexing agrees with round 1's own glazing rectangles
    chk("[2] bay 3 span == GW_Right_Glass_03",
        max(abs(a - b) for a, b in zip(bay_y_span(3), (-4.3625, -2.2375))) < 1e-9,
        str(bay_y_span(3)))
    # [3] coverage passes on the correct plan
    cov = coverage(pl)
    chk("[3] coverage PASS on a correct plan", cov["PASS"], json.dumps(
        [m["member"] for m in cov["members"] if not m["passed"]]))
    # [4] THE DEFECT ITSELF: drop the static remainder and it must fail
    bad = dict(pl, pieces=[p for p in pl["pieces"]
                           if p["kind"] != "transom_static"])
    chk("[4] coverage FAILS when the remainder is dropped",
        not coverage(bad)["PASS"])
    # [5] drop ONE mullion slab and it must fail
    bad = dict(pl, pieces=[p for p in pl["pieces"]
                           if p["name"] != "BF_MUL05_S03"])
    chk("[5] coverage FAILS when one slab is missing",
        not coverage(bad)["PASS"])
    # [6] duplicate a slab and it must fail -- a length check that only tested
    #     the union would pass this, which is why overlap is measured too
    dup = [p for p in pl["pieces"] if p["name"] == "BF_MUL05_S03"][0]
    bad = dict(pl, pieces=pl["pieces"] + [dict(dup, name="BF_MUL05_S03_dup")])
    chk("[6] coverage FAILS on a duplicated slab", not coverage(bad)["PASS"])
    # [7] no piece may sit east of the breach plane... round 1's DOES, by
    #     80 mm, and this module keeps it there deliberately.  The control is
    #     that the number is the one we think it is.
    east = max(b[1] for p in pl["pieces"] for b in p["boxes"])
    chk("[7] cap face is round 1's 15.080, not the section's 15.000",
        abs(east - 15.080) < 1e-9, "%.4f" % east)
    # [8] the pieces tile without overlapping each other in 3-space
    #     (checked pairwise on AABBs, which for axis-aligned boxes is exact)
    ov = []
    allb = [(p["name"], b) for p in pl["pieces"] for b in p["boxes"]]
    for i in range(len(allb)):
        for j in range(i + 1, len(allb)):
            (na, a), (nb, b) = allb[i], allb[j]
            if all(a[2 * k] < b[2 * k + 1] - 1e-9 and b[2 * k] < a[2 * k + 1] - 1e-9
                   for k in range(3)):
                ov.append((na, nb))
    chk("[8] no two supplied pieces interpenetrate", not ov, str(ov[:3]))
    # [9] every driven piece names a body that is in the table
    idx = set(names)
    miss = [p["name"] for p in pl["pieces"]
            if p["driver"] is not None and p["driver"] not in idx]
    chk("[9] every driver exists in the bake table", not miss, str(miss))
    # [10] a table where NOTHING released must produce no plan at all -- the
    #      applier must not delete round 1's frame for a bake that never broke
    n2, r2, l2 = _fake_table(active=(), bays=())
    p2 = plan(n2, r2, l2)
    chk("[10] a bake with no releases deletes nothing",
        not p2["delete"] and not p2["pieces"], str(p2["delete"]))
    # [11] the untouched list is the negative control, and it must be the six
    #      bays and eight mullions we claim
    chk("[11] eight mullions + sill/head/reveal untouched",
        len(pl["untouched"]) == 11, str(len(pl["untouched"])))

    print("%d/%d checks passed" % (11 - len(fails), 11))
    return 1 if fails else 0


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    print(__doc__)
