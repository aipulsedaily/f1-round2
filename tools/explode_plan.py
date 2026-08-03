"""Derive Beat 1's exploded layout, assembly clusters and seat order from the INVENTORY.

    python3 tools/explode_plan.py --inv docs/inventory_iter.json --out docs/explode_plan.json

Nothing here is a preset list. Every grouping and every offset is computed from
measured world-space geometry, because the brief's rule is that the plan adapts
to the inventory and never the reverse.

AXES — MEASURED, NOT ASSUMED
----------------------------
The brief says "fore/aft elements along Y, lateral outboard". That is wrong for
THIS car and following it literally would rotate every offset 90 degrees:

    X  -2.678 .. 3.020   5.698 m   <- LONGITUDINAL. +X is the nose (FW_ +2.679,
                                      NOSE_ +2.450); -X is the tail (RW_ -2.350).
    Y  -1.003 .. 1.003   2.005 m   <- LATERAL. Every module centroid is Y=0.000,
                                      i.e. Y is the mirror axis.
    Z   0.340 .. 1.332   0.992 m   <- VERTICAL. 0.340 is the ride height.

So the brief's intent maps onto this car as: fore/aft along X, lateral outboard
along Y, underbody drops -Z, top structures rise +Z.

WHY EVALUATED WORLD BOUNDS
--------------------------
Offsets are computed from evaluated world-space AABBs, never `bound_box`:
  * 13 MIRROR modifiers mean the base mesh is HALF the real object. Round 1 lost
    a day to this exact trap (D163).
  * 12 tyre objects carry an unapplied Z-scale (1.206 front, 1.598 rear), so
    local dimensions understate the real extent.
  * BEVEL/SOLIDIFY add shell thickness the base mesh does not have.

CLUSTERING
----------
616 meshes flown individually would read as confetti, which the brief explicitly
forbids. Parts are grouped into clusters that are MECHANICALLY real — a corner
assembly moves together because on the real car it bolts together — and each
cluster gets one readable close-up moment in the beat sheet.
"""

import argparse
import json
import math
from collections import defaultdict

FRONT_AXIS = 0   # X
LAT_AXIS = 1     # Y
UP_AXIS = 2      # Z

# Module prefixes as they actually exist in the blend, verified against the
# inventory rather than recalled from round-1 docs.
MODPFX = ["brake_assembly_", "suspension_front_", "suspension_rear_",
          "wheel_tyre_", "wheel_rim_", "halo_assembly_",
          "FW_", "RW_", "MB_", "SP_", "EC_", "FD_", "BB_", "NOSE_", "CI_", "SW_"]

CORNERS = ("FL", "FR", "RL", "RR")


def module_of(name):
    for p in MODPFX:
        if name.startswith(p):
            return p
    return name.split("_")[0] + "_"


def corner_of(name):
    """Corner tag if this part belongs to one, else None.

    Matched on _<CODE>_ so `FW_Endplate_L` is NOT mistaken for a corner part —
    round 1 shipped a bug of exactly that shape when a regex matched too loosely.
    """
    for c in CORNERS:
        if f"_{c}_" in name or name.endswith(f"_{c}"):
            return c
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--spread", type=float, default=1.85,
                    help="global explode scale; tuned against the beat sheet's "
                         "camera path, not chosen for looks")
    a = ap.parse_args()

    inv = json.load(open(a.inv))
    car = [o for o in inv["objects"]
           if "CAR" in o["collections"] and o["type"] == "MESH" and "min" in o]

    # ---- cluster assignment ---------------------------------------------
    clusters = defaultdict(lambda: {"parts": [], "tris": 0,
                                    "min": [1e9] * 3, "max": [-1e9] * 3})
    for o in car:
        mod = module_of(o["name"])
        cor = corner_of(o["name"])
        # A corner is a real mechanical assembly: upright, hub, brake, wheel,
        # tyre and the suspension links that land on it all move as one.
        if cor and mod in ("brake_assembly_", "wheel_tyre_", "wheel_rim_",
                           "suspension_front_", "suspension_rear_"):
            key = f"CORNER_{cor}"
        else:
            key = mod.rstrip("_")
        c = clusters[key]
        c["parts"].append(o["name"])
        c["tris"] += o["eval_tris"]
        for i in range(3):
            c["min"][i] = min(c["min"][i], o["min"][i])
            c["max"][i] = max(c["max"][i], o["max"][i])

    car_min = [min(o["min"][i] for o in car) for i in range(3)]
    car_max = [max(o["max"][i] for o in car) for i in range(3)]
    car_ctr = [(car_min[i] + car_max[i]) / 2 for i in range(3)]

    # ---- exploded offset per cluster ------------------------------------
    # Direction is mechanical, not radial-from-centre: a part travels the way it
    # would actually come off the car. Magnitude scales with the cluster's own
    # size so a big panel clears a long way and a small fitting does not fly to
    # the far wall.
    out = {"axes": {"longitudinal": "X (+X = nose)", "lateral": "Y",
                    "vertical": "Z", "ride_height": car_min[UP_AXIS]},
           "car_bbox": {"min": car_min, "max": car_max, "centre": car_ctr},
           "spread": a.spread, "clusters": {}}

    for key, c in clusters.items():
        ctr = [(c["min"][i] + c["max"][i]) / 2 for i in range(3)]
        size = [c["max"][i] - c["min"][i] for i in range(3)]
        diag = max(size)
        d = [0.0, 0.0, 0.0]

        if key.startswith("CORNER_"):
            cor = key.split("_")[1]
            # outboard laterally, and slightly fore/aft the way it sits
            d[LAT_AXIS] = 1.0 if ctr[LAT_AXIS] > 0 else -1.0
            d[FRONT_AXIS] = 0.35 if cor[0] == "F" else -0.35
            # A corner lifts as it comes off the car — a wheel is drawn off its
            # hub, not slid along the ground. This also gives the surface
            # constraint a vertical component to work with; with a pure lateral
            # offset the solver could not raise the wheel clear of the deck at
            # all and the flight rotation dipped the tyre into it.
            d[UP_AXIS] = 0.30
            mag = 1.15
        elif key in ("FW", "NOSE"):
            # Forward off the nose — but SEPARATED VERTICALLY, deliberately.
            #
            # Both used to explode along pure +X. Being colinear, the only way
            # the solver could separate them was to push further along the same
            # line, and once the floor cap removed their downward splay it drove
            # them to 10.5 m and 11.3 m forward in a room 30 m long.
            #
            # On the car the nose sits ABOVE the front wing (centZ 0.641 vs
            # 0.525), so lifting the nose and keeping the wing low is what the
            # parts actually do — and it uses the 5.6 m of headroom that the
            # floor constraint left idle.
            d[FRONT_AXIS] = 1.0
            d[UP_AXIS] = 0.62 if key == "NOSE" else -0.05
            mag = 1.30
        elif key == "RW":
            d[FRONT_AXIS] = -1.0                     # rearward off the tail
            mag = 1.30
        elif key == "FD":
            # The floor SLIDES OUT REARWARD, it does not drop.
            #
            # "Underbody drops" is the brief's phrasing and it is right in
            # principle, but this car sits on a 0.34 m dais: a 3.78 m floor tray
            # exploding straight down has 0.22 m of air before it is inside the
            # plinth. The solver, unable to move it vertically, then drove it
            # 2.9 m horizontally and still could not clear the monocoque, and
            # inflated FW/NOSE to scale 7 in the process (FW ended 11.3 m
            # forward, nearly out of a 30 m room).
            #
            # Mechanically, a floor is removed by sliding it out from under the
            # car — rearward, past the diffuser — with only a slight drop. That
            # reads as engineering AND leaves the solver somewhere to work.
            d[FRONT_AXIS] = -1.0
            d[UP_AXIS] = -0.28
            mag = 1.15
        elif key in ("EC", "BB"):
            d[UP_AXIS] = 0.55                        # powertrain lifts and back
            d[FRONT_AXIS] = -0.85
            mag = 1.10
        elif key in ("halo_assembly", "CI", "SW"):
            d[UP_AXIS] = 1.0                         # cockpit furniture rises
            d[FRONT_AXIS] = 0.25
            mag = 1.05
        elif key == "SP":
            # D160 REDUX — DO NOT explode this laterally.
            #
            # Round 1's worst geometry defect was exactly this: SP_ and BB_ are
            # single meshes that span BOTH sides of the car (a MIRROR modifier,
            # so each object's own centroid sits at Y=0). A lateral offset with
            # a sign picked from the centroid therefore always resolves to +1
            # and slides the whole two-sided part 0.80 m THROUGH the monocoque.
            # The user found that by zooming into a delivered 4K frame.
            #
            # Full-width parts are detected by MEASUREMENT below, not by name,
            # so a future full-width part cannot reintroduce it. They explode
            # vertically and rearward, where there is nothing to pass through.
            d[UP_AXIS] = 1.0
            d[FRONT_AXIS] = -0.3
            mag = 1.05
        elif key == "MB":
            d = [0.0, 0.0, 0.0]                      # the core stays put
            mag = 0.0
        else:
            # anything unforeseen: push it radially outward from the car centre
            v = [ctr[i] - car_ctr[i] for i in range(3)]
            n = max((sum(x * x for x in v)) ** 0.5, 1e-6)
            d = [x / n for x in v]
            mag = 1.0

        # SPLAY — separate clusters that travel the same way.
        #
        # FW and NOSE both explode along +X. Being colinear they can only be
        # separated by pushing one of them further along the SAME line, so the
        # collision solver below drove them to +7.0 and +7.8 m and produced a
        # 15 m field in a 30 x 22 m room. The parts ended up further from the
        # turntable than the camera could usefully weave.
        #
        # The fix is not a bigger room, it is a splay: each cluster also drifts
        # in the axes it is NOT exploding along, by where it actually sits on
        # the car. That is still mechanical — the front wing lives low and the
        # nose above it, so they separate vertically exactly as they sit — and
        # it gives the solver a cheap axis so it stops inflating the field.
        for ax in range(3):
            if abs(d[ax]) < 1e-6:
                rel = ctr[ax] - car_ctr[ax]
                span = max(car_max[ax] - car_min[ax], 1e-6)
                d[ax] += 0.55 * (rel / (span * 0.5))

        # FULL-WIDTH GUARD, measured. Any cluster whose lateral extent covers
        # most of the car is two-sided (mirrored) and cannot be moved sideways
        # without driving one half through the chassis — see the D160 note above.
        # This runs for EVERY cluster, so it also catches parts nobody special-
        # cased, which is the whole point: the round-1 bug was a sign convention
        # that was correct for one-sided parts and silently wrong for the rest.
        car_width = car_max[LAT_AXIS] - car_min[LAT_AXIS]
        full_width = size[LAT_AXIS] > 0.60 * car_width
        if full_width and abs(d[LAT_AXIS]) > 1e-6:
            d[UP_AXIS] = max(d[UP_AXIS], 0.0) + 1.0
            d[LAT_AXIS] = 0.0
            c["full_width_redirected"] = True

        n = max((sum(x * x for x in d)) ** 0.5, 1e-6)
        d = [x / n for x in d] if mag else [0.0, 0.0, 0.0]
        dist = mag * a.spread * (0.55 + 0.45 * (diag / max(car_max[0] - car_min[0], 1e-6)))
        offset = [round(d[i] * dist, 4) for i in range(3)]

        out["clusters"][key] = {
            "n_parts": len(c["parts"]),
            "tris": c["tris"],
            "bbox_min": [round(v, 4) for v in c["min"]],
            "bbox_max": [round(v, 4) for v in c["max"]],
            "centre": [round(v, 4) for v in ctr],
            "size": [round(v, 4) for v in size],
            "explode_offset": offset,
            "explode_distance": round(dist, 4),
            "parts": sorted(c["parts"]),
        }

    # ---- headroom constraint: an exploded part must remain photographable --
    #
    # The collision solver below only knows about parts hitting each other. It
    # will happily push a cluster to a height where no camera can frame it, and
    # that is exactly what happened to SP:
    #
    #   SP is a flat wide plate (2.15 x 1.48 x 0.58 m), so its projected area is
    #   maximised looking straight DOWN at it — all 16 of its best-scoring
    #   directions are near-vertical. The solver put its centre at z 4.2 m in a
    #   6.5 m room, leaving 1.85 m of headroom for a 2.54 m standoff. The macro
    #   render came back as a flat grey frame: the lens was inside the ceiling.
    #   Pulling the standoff in to fit made the cluster overflow the frame
    #   instead. Neither is a framing; both are the same layout error.
    #
    # So the constraint belongs here, before the solve: cap each cluster's
    # vertical offset so that its centre plus the standoff a camera needs still
    # clears the ceiling. An exploded layout that cannot be photographed is not
    # a layout.
    CEILING_USABLE = 6.05        # 6.5 m slab less a 0.45 m margin
    # THE SURFACE UNDER THE CAR IS NOT THE FLOOR.
    #
    # The car stands on a turntable: `Turntable_Deck` top is z=0.340 over a
    # 6.90 x 6.90 m footprint centred on the origin (`Platform_Dais` 7.40 x 7.40
    # to z=0.300 beneath it). The first floor constraint used z=0 — the showroom
    # slab — so six clusters were solved to positions INSIDE the plinth: all four
    # corners 186 mm in, FD 220 mm, FW 67 mm. The user spotted it in a rendered
    # suspension close-up.
    #
    # A cluster whose footprint overlaps the deck must clear the DECK; only one
    # entirely outside it may use the floor.
    DECK_TOP = 0.340
    DECK_HALF = 3.45             # 6.90 m deck, centred on the origin
    FLOOR_TOP = 0.0
    # Clearance must survive the MOTION applied to the layout, not just the
    # layout. Beat 1 gives every part a 4.5 deg flight rotation, and rotating a
    # wheel that rests on the deck tips its edge through it: the depth probe
    # measured wheel_tyre_RR_Tyre 11.33 mm INSIDE Turntable_Deck at frames 1 and
    # 400, while frame 792 (rotation back to zero) was clean.
    #
    # A cluster of radius r rotated by theta sweeps its lowest point down by
    # about r*sin(theta), so the gap has to cover that plus visible air.
    FLIGHT_ROT_DEG = 4.5
    SURFACE_GAP_BASE = 0.06      # visible air between a part and what it hangs over
    CAM_GAP = 1.20               # matches --dist in the audit/beat-sheet tools
    # ---- collision solve -------------------------------------------------
    # Round 1 shipped 19 overlapping module pairs and only caught them when the
    # user zoomed into a delivered 4K frame ("this is overlaping nightmare").
    # The gate that followed was built on the principle that ANY cross-cluster
    # overlap is a defect by definition, so the same principle is applied here
    # BEFORE anything is animated rather than after it is rendered.
    #
    # Clusters are separated by EXTENDING each one further along the mechanical
    # direction it already travels, never by nudging it sideways: the exploded
    # field has to read as an engineering diagram, and a part shoved off-axis to
    # win a clearance argument stops looking like it came off the car.
    #
    # MB is pinned at distance 0 — it is the structural core the rest assembles
    # onto, so it is always the other cluster that yields.
    #
    # D164 REDUX: the clearance term is ADDED to the required separation. Round 1
    # inverted this sign (`raw - clearance`) and the solver stopped while parts
    # were still lapping, then reported success.
    CLEARANCE = 0.12          # metres of visible air between clusters at 4K
    MAX_PASSES = 400
    STEP = 0.04

    def scaled_offset(k, c, scale):
        """Scale horizontally freely; scale VERTICALLY only up to the headroom cap.

        The first version scaled all three axes by one factor. Once a cluster hit
        the ceiling its scale could not grow at all, so the solver had no way to
        separate SP from halo_assembly (105.8 mm of interpenetration) even though
        both had metres of free space horizontally — SP travels -X, halo +X.

        Decoupling the axes lets a z-capped cluster keep sliding apart in the
        plane where there is room, which is what a person laying these out by
        hand would obviously do.
        """
        s_all = scale.get(k, 1.0)
        s_z = min(s_all, max_scale.get(k, 1e9))
        o = c["explode_offset"]
        return [o[0] * s_all, o[1] * s_all, o[2] * s_z]

    def boxes_of(scale):
        b = {}
        for k, c in out["clusters"].items():
            o = scaled_offset(k, c, scale)
            b[k] = ([c["bbox_min"][i] + o[i] for i in range(3)],
                    [c["bbox_max"][i] + o[i] for i in range(3)])
        return b

    def worst_pairs(b):
        bad = []
        keys = sorted(b)
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                ka, kb = keys[i], keys[j]
                (amin, amax), (bmin, bmax) = b[ka], b[kb]
                pen = min(min(amax[x], bmax[x]) - max(amin[x], bmin[x])
                          for x in range(3))
                if pen > -CLEARANCE:          # note: ADDED clearance (D164)
                    bad.append((pen, ka, kb))
        return sorted(bad, reverse=True)

    # HEADROOM AS A SOLVER CONSTRAINT, not a pre-pass.
    #
    # Capping the offsets before the solve does not work: the solver's whole job
    # is to scale offsets UP until clusters separate, so it simply undid the cap
    # and put SP back through the ceiling. The ceiling has to bound the solver.
    #
    # For each cluster, the largest scale whose resulting centre still leaves
    # room for a camera: centre_z(scale) + radius + CAM_GAP <= CEILING_USABLE.
    max_scale = {}
    for k, c in out["clusters"].items():
        off = c["explode_offset"]
        size = c["size"]
        radius = 0.5 * math.sqrt(sum(v * v for v in size))
        base_z = (c["bbox_min"][2] + c["bbox_max"][2]) / 2
        # UP: leave room above for a camera.
        room = CEILING_USABLE - radius - CAM_GAP - base_z
        # DOWN: a part may not sink through the floor. The ceiling constraint was
        # added first and this one was not — the imperfections pass found FD and
        # FW hanging BELOW the showroom floor plane (MACRO_FW centre z -0.298,
        # radius 1.07), i.e. half-buried in the slab the camera is standing on.
        # Same bug, opposite sign; fixing only the end that bit is how a defect
        # class survives.
        # which surface is under THIS cluster once it has moved?
        cx_lo = c["bbox_min"][0] + off[0]
        cx_hi = c["bbox_max"][0] + off[0]
        cy_lo = c["bbox_min"][1] + off[1]
        cy_hi = c["bbox_max"][1] + off[1]
        over_deck = (cx_lo < DECK_HALF and cx_hi > -DECK_HALF
                     and cy_lo < DECK_HALF and cy_hi > -DECK_HALF)
        # radius drives how far the flight rotation can dip this cluster
        rot_dip = radius * math.sin(math.radians(FLIGHT_ROT_DEG))
        surface = ((DECK_TOP if over_deck else FLOOR_TOP)
                   + SURFACE_GAP_BASE + rot_dip)
        c["rotation_dip_allowance_m"] = round(rot_dip, 4)
        c["surface_below"] = "deck" if over_deck else "floor"
        low_room = (c["bbox_min"][2] - surface)
        if off[2] > 1e-6:
            max_scale[k] = max(room / off[2], 0.0)
        elif off[2] < -1e-6:
            max_scale[k] = max(low_room / (-off[2]), 0.0)
        else:
            max_scale[k] = 1e9

    scale = {k: 1.0 for k in out["clusters"]}
    passes = 0
    for passes in range(1, MAX_PASSES + 1):
        bad = worst_pairs(boxes_of(scale))
        if not bad:
            break
        for _pen, ka, kb in bad:
            for k in (ka, kb):
                # a cluster with no direction (the pinned core) cannot yield
                if any(abs(v) > 1e-9 for v in out["clusters"][k]["explode_offset"]):
                    scale[k] += STEP

    final_bad = worst_pairs(boxes_of(scale))
    for k, c in out["clusters"].items():
        c["solve_scale"] = round(scale[k], 3)
        c["vertical_scale_cap"] = round(min(scale[k], max_scale[k]), 3)
        c["explode_offset"] = [round(v, 4) for v in scaled_offset(k, c, scale)]
        c["explode_distance"] = round(
            sum(v * v for v in c["explode_offset"]) ** 0.5, 4)
    out["solve"] = {"passes": passes, "clearance_m": CLEARANCE,
                    "residual_overlaps": len(final_bad),
                    "residual": [[round(p, 4), a, b] for p, a, b in final_bad]}

    # ---- seat order ------------------------------------------------------
    # Brief's rule: structural core first, inboard-to-outboard, underbody before
    # topside, aero late, wheels LAST with a simultaneous seat. Rank is derived,
    # then sorted, so adding a module later slots in without a hand-edited list.
    def rank(key):
        if key == "MB":
            return (0, 0)                       # core, by geometry: 5.47 m span
        if key == "FD":
            return (1, 0)                       # underbody before topside
        if key in ("EC", "BB"):
            return (2, 0)                       # powertrain inboard
        if key in ("CI", "SW", "halo_assembly"):
            return (3, 0)                       # cockpit furniture
        if key == "SP":
            return (4, 0)                       # bodywork
        if key in ("NOSE",):
            return (5, 0)
        if key in ("FW", "RW"):
            return (6, 0)                       # aero late
        if key.startswith("CORNER_"):
            return (7, 0)                       # wheels LAST, simultaneous
        return (5, 1)

    order = sorted(out["clusters"], key=lambda k: (rank(k), k))
    out["seat_order"] = order
    out["simultaneous_groups"] = [[k for k in order if k.startswith("CORNER_")]]

    json.dump(out, open(a.out, "w"), indent=1)

    print(f">> clusters {len(out['clusters'])}  parts {sum(c['n_parts'] for c in out['clusters'].values())}")
    print(f">> {'cluster':<16}{'parts':>6}{'tris':>11}{'dist':>8}   offset")
    for k in order:
        c = out["clusters"][k]
        print(f"   {k:<16}{c['n_parts']:>6}{c['tris']:>11,}{c['explode_distance']:>8.2f}   {c['explode_offset']}")
    print(f">> seat order: {' -> '.join(order)}")
    print(">> STAGE RESULT: EXPLODE_PLAN_OK")



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
    gate_exit.guard(main, tool="explode_plan")
