#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
grandstand_seats.py — THE SEATS THE WORLD ACTUALLY BUILT, read out of the
builder that casts them rather than modelled a second time.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/grandstand_seats.py -- --out world/items/grandstand_seats.json

WHY THIS FILE EXISTS
====================
Two seat registers existed before it and they disagree:

    build_architecture._grandstand_block()   18,350 seats   <- what is in the ship
    grandstand_riser_unit.seat_grid()        18,408 seats   <- the item's model of it

`render/world/assembly/r2/assembly9_build.json` records
`architecture.summary.grandstand_seats = 18350`, so 18,350 is the number the
shipped world put on the ground.  A crowd seated on the other register puts 58
people on chairs that are not there.

**AND ONE THING ONLY THIS REGISTER KNOWS.**  `build_architecture._seat()` folds
a tip-up seat at `rng.random() < 0.22` on seat kinds 0 and 2:

    TRIBUNE OUEST        3,071 seats   kind 0     669 folded  21.8 %
    TRIBUNE T15          4,077 seats   kind 2     868 folded  21.3 %
    VIRAGE OUEST         2,143 seats   kind 1       0 folded   0.0 %
    TRIBUNE PRINCIPALE   5,542 seats   kind 0   1,231 folded  22.2 %
    TRIBUNE EST          2,522 seats   kind 2     543 folded  21.5 %
    TRIBUNE TEMPORAIRE     995 seats   kind 3       0 folded   0.0 %
    ------------------------------------------------------------------
    TOTAL               18,350                  3,311 folded  18.0 %

**3,311 seats in this world are physically folded up.  A figure placed on one
is sitting on a vertical seat back.**  15,039 seats can hold a person, and that
is the real occupancy ceiling — not 18,350.  It is also, for free, the first
layer of the patchiness a grandstand needs: 18 % of the seating is unusable in
a pattern the architecture already chose, block by block.

HOW IT IS READ, AND WHY IT IS NOT A RE-DERIVATION
=================================================
`build_grandstands()` seeds one `random.Random(4200 + bi * 131)` per block and
hands it to `_grandstand_block()`, which consumes it for the advertising band,
the seat colours, the folds and the dropped seats, in that order.  This module
runs **that function**, with **that seed**, and swaps only `_seat()` for a
recorder and `MB` for a no-op.  `_seat_colour()` still runs for real, because it
draws from the same `rng` and skipping it would desynchronise the stream and
silently move every fold.

The assertion that makes it a measurement rather than a claim: the recorded
count per block must equal `_grandstand_block`'s own returned `seatn`, and the
total must equal `assembly9_build.json`'s `grandstand_seats`.  Both are checked
and a mismatch is a refusal.

FRAMES
======
`build_architecture` authors the rake in the CIRCUIT frame and puts `M_C2W` on
the object.  This file publishes both:

    x, y, z          circuit / design frame, as authored
    wx, wy, wz       world, through world_contract's 40 deg / (-350, 72) ->
                     (15, 0) datum, which is the same transform
                     `grandstand_riser_unit.seat_grid()` bakes in

`z` is the TREAD top.  The seat pan top is `z + 0.445` — `_seat()`'s own
constant, the one `spectator_seated.RAKE["pan_above_tread_m"]` mirrors.
"""

import json
import math
import os
import random
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
if _WORLD not in sys.path:
    sys.path.insert(0, _WORLD)

#: `_seat()` kind 0/1/2 all put the pan top 0.445 m above the tread it stands
#: on; kind 3 is a 0.045 m plank whose top is 0.4425.  The 2.5 mm difference is
#: half a millimetre of screen at the size this crowd is ever seen, and one
#: constant is what `spectator_seated.RAKE` and `spectator_crowd.seat_array`
#: both already assume, so it is kept as one and the exception is named here.
PAN_ABOVE_TREAD_M = 0.445

OUT_DEFAULT = os.path.join(_HERE, "grandstand_seats.json")
ASSEMBLY_BUILD = os.path.join(_ROOT, "render", "world", "assembly", "r2",
                              "assembly9_build.json")


class _NullMB(object):
    """Everything `_grandstand_block` draws except the seats, discarded.

    It must accept every method name the builder calls without changing the
    rng stream, which it cannot do because it never touches the rng.
    """

    def __init__(self, *a, **k):
        pass

    def __getattr__(self, _n):
        def f(*a, **k):
            return None
        return f


def census():
    """-> dict with every seat build_architecture cast, and its fold state."""
    import build_architecture as A          # needs bpy

    rec = []

    real_seat = A._seat

    def rec_seat(mb, m, kind, col, folded, rng, _r=[0], _c=[0]):
        # `m` = T(sx, yb - tread*0.42, z0 + 0.16) @ Rz(180): its translation is
        # the TREAD TOP at the pan centre in x/y.  Taken off the matrix rather
        # than recomputed, so this cannot drift from the builder's arithmetic.
        o = m.to_translation()
        rec.append([round(o.x, 4), round(o.y, 4), round(o.z, 4),
                    int(kind), 1 if folded else 0, _r[0], _c[0]])
        return None

    # row/col are not arguments to `_seat`, so they are carried in on the
    # enclosing loop by wrapping the colour call, which IS made once per seat,
    # immediately before it, with the loop indices in hand.
    real_col = A._seat_colour

    def rec_col(blk, ci, ri, ncol, nrow, rng):
        rec_seat.__defaults__[0][0] = ri
        rec_seat.__defaults__[1][0] = ci
        return real_col(blk, ci, ri, ncol, nrow, rng)

    A._seat = rec_seat
    A._seat_colour = rec_col
    try:
        blocks, seats = [], []
        for bi, blk in enumerate(A.GS_BLOCKS):
            rec[:] = []
            gr = random.Random(4200 + bi * 131)     # build_grandstands' own seed
            n, top = A._grandstand_block(_NullMB(), blk, gr, {})
            if n != len(rec):
                raise RuntimeError(
                    "block %r: the builder reports %d seats and the recorder "
                    "caught %d. The recorder is not seeing every seat and "
                    "nothing downstream of it can be trusted."
                    % (blk["name"], n, len(rec)))
            for r in rec:
                r.append(bi)
            seats.extend(rec)
            blocks.append(dict(i=bi, name=blk["name"], x0=blk["x0"],
                               x1=blk["x1"], rows=blk["rows"],
                               tread=blk["tread"], rise=blk["rise"],
                               seat_kind=blk["seat"], roof=blk["roof"],
                               aisle=blk["aisle"], voms=blk["voms"],
                               n_seats=n, n_folded=sum(r[4] for r in rec),
                               top_z=round(top, 3)))
    finally:
        A._seat = real_seat
        A._seat_colour = real_col

    total = len(seats)
    declared = None
    if os.path.exists(ASSEMBLY_BUILD):
        declared = (json.load(open(ASSEMBLY_BUILD))
                    .get("mods", {}).get("architecture", {})
                    .get("summary", {}).get("grandstand_seats"))
    if declared is not None and declared != total:
        raise RuntimeError(
            "recorded %d seats; assembly9_build.json's own counter says %d. "
            "This register does not describe the shipped world and placing a "
            "crowd on it would seat people on chairs nobody built."
            % (total, declared))

    import world_contract as WC
    cr = math.cos(math.radians(WC.ROT_DEG)); sr = math.sin(math.radians(WC.ROT_DEG))
    px, py = WC.PIVOT_DESIGN; wx0, wy0 = WC.PIVOT_WORLD
    out_seats = []
    for x, y, z, kind, folded, row, col, bi in seats:
        dx, dy = x - px, y - py
        out_seats.append(dict(
            b=bi, row=row, col=col, kind=kind, folded=bool(folded),
            x=x, y=y, z=z,
            wx=round(wx0 + dx * cr - dy * sr, 4),
            wy=round(wy0 + dx * sr + dy * cr, 4), wz=z))
    face_world = round(math.degrees(math.atan2(cr, -sr)), 4)
    return dict(
        schema="f1-round2/grandstand_seats/1.0",
        source="world/build_architecture.py _grandstand_block(), replayed with "
               "its own per-block random.Random(4200 + bi*131)",
        assembly_counter=declared, total=total,
        folded=sum(1 for s in out_seats if s["folded"]),
        seatable=sum(1 for s in out_seats if not s["folded"]),
        pan_above_tread_m=PAN_ABOVE_TREAD_M,
        facing_world_deg=face_world,
        datum=dict(rot_deg=WC.ROT_DEG, pivot_design=list(WC.PIVOT_DESIGN),
                   pivot_world=list(WC.PIVOT_WORLD)),
        blocks=blocks, seats=out_seats)


def load(path=OUT_DEFAULT):
    """The register, or a refusal. There is no fallback: a crowd seated on a
    guessed seat array is the whole defect this file exists to close."""
    if not os.path.exists(path):
        raise RuntimeError(
            "%s does not exist. Build it with\n"
            "    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup "
            "-P world/items/grandstand_seats.py -- --out %s\n"
            "This module does not fall back to grandstand_riser_unit."
            % (path, path))
    d = json.load(open(path))
    if d.get("schema") != "f1-round2/grandstand_seats/1.0":
        raise RuntimeError("%s: unknown schema %r" % (path, d.get("schema")))
    return d


def _main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out = argv[argv.index("--out") + 1] if "--out" in argv else OUT_DEFAULT
    d = census()
    print(" %-22s %6s %5s %8s %7s   %-28s"
          % ("block", "seats", "kind", "folded", "pct", "pan-top z (circuit)"))
    zs = {}
    for s in d["seats"]:
        zs.setdefault(s["b"], []).append(s["z"] + PAN_ABOVE_TREAD_M)
    for b in d["blocks"]:
        z = zs[b["i"]]
        print(" %-22s %6d %5d %8d %6.1f%%   %.2f .. %.2f"
              % (b["name"], b["n_seats"], b["seat_kind"], b["n_folded"],
                 100.0 * b["n_folded"] / b["n_seats"], min(z), max(z)))
    print(" %-22s %6d %5s %8d %6.1f%%"
          % ("TOTAL", d["total"], "", d["folded"], 100.0 * d["folded"] / d["total"]))
    print("assembly9_build.json grandstand_seats = %s  (agrees: %s)"
          % (d["assembly_counter"], d["assembly_counter"] == d["total"]))
    print("SEATS A PERSON CAN SIT ON: %d" % d["seatable"])
    print("seat facing in WORLD: %.3f deg" % d["facing_world_deg"])
    with open(out, "w") as f:
        json.dump(d, f)
    print("-> %s (%.1f MB)" % (out, os.path.getsize(out) / 1048576.0))
    print(">> STAGE RESULT: GRANDSTAND_SEATS_OK")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
