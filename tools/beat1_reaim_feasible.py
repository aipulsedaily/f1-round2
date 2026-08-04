"""How much of the R2-451 re-aim will beat 1's EXISTING schedule actually carry?

    python3 tools/beat1_reaim_feasible.py --out work/b1nadir/presentation_normals_R2451.json

WHY THIS EXISTS
---------------
Re-aiming all fifteen presentation directions out of the nadir makes beat 1's
tour unschedulable, and the reason is not the one I expected.

A station sits at `centre + d * standoff`.  With `d` near-vertical every station
sits nearly directly ABOVE its cluster and the camera hovers; with `d` shallow
the station swings out to a horizontal radius of `standoff * cos(elev)` and the
camera must fly AROUND the field.  MB is the worst case and it is also the film's
first frame: standoff 4.859 m, so its station moves from 0.49 m horizontally off
the monocoque to 4.69 m.  Separately, `move_seconds` charges for the PAN, and
fifteen near-nadir view directions are all nearly parallel to one another, so the
shipped tour pays almost nothing in pans while a photographic tour pays for all
fifteen.  **The nadir framing was buying the schedule.**

WHAT BINDS, AND IT IS NOT THE RUNTIME
-------------------------------------
The deadlines are when each cluster starts FLYING to its seat (R2-062) -- a
station solved against an exploded position is aimed at empty air after that.
Feasibility is `cum_cost(k) / total_cost <= deadline(k) / span`, and BOTH sides
are ratios: the absolute tour cost cancels.  So **lengthening beat 1 does not
help** -- it scales `span` up and makes every deadline harder, not easier.  That
kills the +3.1 s / +7.4 s escape route R2-323 and R2-330 costed for the standoff
fix.  It is also why this block does not move the beat-1/2 seam: there was never
a version of this fix that wanted to.

SO THE FIX IS SCOPED BY MEASUREMENT
-----------------------------------
Re-aim every cluster the schedule will carry, leave the ones that bind, and NAME
them.  This runs the real `solve_visit_order` -- the shipped solver, shipped cost
function, shipped deadlines -- over subsets, and reverts the smallest set of
clusters that restores feasibility.  The result is a normals file that is part
re-aimed and part shipped, with the per-cluster verdict written into it, and a
printed list of what could not be fixed inside the existing schedule.
"""

import argparse
import importlib.util
import json
import math
import os
import sys

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "tools"))
SPAN = 33.0


def load_bbs():
    os.environ["B1_MAX_DEPRESSION"] = "90"   # price the FILE, never a clamp
    spec = importlib.util.spec_from_file_location(
        "bbs", os.path.join(R2, "tools/build_beatsheet.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def elev_of(n):
    d = n["normal"]
    mm = math.sqrt(sum(x * x for x in d)) or 1.0
    return math.degrees(math.asin(max(-1.0, min(1.0, d[2] / mm))))


def feasible(m, geo, normals, deadlines, spine_exit, corner_entry):
    """Exactly the shipped solve. Returns the order, or None."""
    try:
        seat = json.load(open(os.path.join(R2, "docs/explode_plan.json")))["seat_order"]
        return m.present_order(geo, seat, normals, SPAN, deadlines,
                               spine_exit, corner_entry)
    except SystemExit:
        return None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reaim", default=os.path.join(
        R2, "work/b1nadir/presentation_normals_reaim.json"))
    ap.add_argument("--ship", default=os.path.join(
        R2, "docs/presentation_normals.json"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    m = load_bbs()
    plan = json.load(open(os.path.join(R2, "docs/explode_plan.json")))
    geo = m.cluster_geometry(plan)
    anim = json.load(open(os.path.join(R2, "world/beat1_anim_anim.json")))
    flight_f = float(anim.get("flight_s", 1.55)) * 24
    deadlines = {c: (v["seat_frame"] - flight_f) / 24.0 - 0.5
                 for c, v in anim.get("clusters", {}).items()}
    ship = json.load(open(a.ship))
    reaim = json.load(open(a.reaim))
    seat = plan["seat_order"]

    # EXACTLY build_beat1()'s own call: the spine is solved into the first
    # bridge at t = 18.10 and the corners into CORNER_FL's pinned 24.64, not
    # into the 33.0 s beat. Getting these two spans wrong makes every verdict
    # below meaningless, so they are taken from the shipped constants.
    dur = 33.0
    n_all = len(plan["seat_order"])
    slot = dur * 0.80 / n_all
    corner_last_t = round(dur * 0.80 - slot, 3)
    b1_t = m.BEAT1_BRIDGES[0]["t"]
    b2_t = m.BEAT1_BRIDGES[1]["t"]
    bridge1 = m._fixed_key_geom(m.BEAT1_BRIDGES[0])
    bridge2 = m._fixed_key_geom(m.BEAT1_BRIDGES[1])

    def try_set(keep_reaimed):
        N = {k: (reaim[k] if k in keep_reaimed else ship[k]) for k in ship}
        try:
            o = m.present_order(geo, seat, N, deadlines,
                                spine_span_s=b1_t,
                                corner_span_s=corner_last_t - b2_t,
                                spine_exit=bridge1, corner_entry=bridge2)
            return N, o
        except SystemExit:
            return None, None

    # ---- THE CANDIDATE BAND, not one candidate per cluster ------------------
    #
    # The first version of this file offered the solver ONE re-aimed direction
    # per cluster -- the tie-break's pick -- and concluded that eleven of the
    # fifteen were unschedulable.  That conclusion was an artefact of the
    # question.  Each cluster has ~54 directions inside the legal band and they
    # differ in AZIMUTH, which is exactly what the tour cost is made of: a
    # station swung out to the side the camera is already travelling toward
    # costs a fraction of one swung out the other way.  So the search is over
    # the band, best-scoring first, and a cluster is only declared unfixable
    # when EVERY legal direction it has breaks the schedule.
    surf = json.load(open(os.path.join(R2, "work/b1nadir/view_surface.json")))

    def band(k):
        cl = surf["clusters"][k]
        c = plan["clusters"][k]
        cz = c["centre"][2] + c["explode_offset"][2]
        radius = 0.5 * math.sqrt(sum(s * s for s in c["size"]))
        standoff = max(radius * 1.55 + 0.42, 0.75)
        rows = []
        for i, d in enumerate(cl["dirs"]):
            e = cl["elev_deg"][i]
            if e < -8.0 or e > 25.0:
                continue
            z = cz + standoff * math.sin(math.radians(e))
            if not (1.20 <= z <= 5.29):
                continue
            rows.append((cl["score"][i], e, d, cl["proj_m2"][i], cl["rich"][i]))
        rows.sort(key=lambda r: -r[0])
        return rows

    names = sorted(ship)
    print("BASELINES")
    _n, o = try_set(set())
    print(f"  all SHIPPED   -> {'schedulable' if o else 'NOT schedulable'}")
    _n, o = try_set(set(names))
    print(f"  all RE-AIMED  -> {'schedulable' if o else 'NOT schedulable'}")
    print()

    # ---- greedy over the band, worst picture first ---------------------------
    order_by_need = sorted(names, key=lambda k: -elev_of(ship[k]))
    cur = {k: ship[k] for k in names}

    def try_map(mp):
        try:
            return m.present_order(geo, seat, mp, deadlines,
                                   spine_span_s=b1_t,
                                   corner_span_s=corner_last_t - b2_t,
                                   spine_exit=bridge1, corner_entry=bridge2)
        except SystemExit:
            return None

    print("GREEDY over the legal band, worst picture first, ITERATED TO A FIXED")
    print("POINT.  A single pass is order-dependent and understates the answer:")
    print("FD is tried first, against a baseline where nothing else has moved,")
    print("and fails -- but once MB is out of the nadir the tour is a different")
    print("shape and FD may fit.  So the sweep repeats over the clusters still")
    print("unfixed until a whole pass changes nothing.")
    print()
    print("`tried` is how many legal directions were rejected by the SCHEDULE,")
    print("not by the picture; the search is in SCORE order, so the direction")
    print("taken is the most legible one that beat 1 can still be scheduled with.")
    print()
    chosen = {k: False for k in names}
    for sweep in range(1, 7):
        moved = 0
        for k in order_by_need:
            if chosen[k]:
                continue
            rows = band(k)
            got = None
            for j, (sc, e, d, pa, rich) in enumerate(rows):
                cand = dict(cur)
                cand[k] = dict(ship[k])
                cand[k]["normal"] = [round(x, 5) for x in d]
                cand[k]["projected_area_m2"] = round(pa, 5)
                cand[k]["distinct_materials"] = int(rich)
                cand[k]["score"] = round(sc, 5)
                if try_map(cand) is not None:
                    cur = cand
                    got = (j, sc, e)
                    break
            if got:
                j, sc, e = got
                kept = sc / max(surf["clusters"][k]["best_score"], 1e-9)
                chosen[k] = True
                moved += 1
                print(f"  pass {sweep}  + {k:16s} {elev_of(ship[k]):7.2f} -> "
                      f"{e:7.2f} deg   score {kept:5.1%} of the unconstrained "
                      f"max   tried {j:2d}/{len(rows)}")
            elif sweep == 1:
                print(f"  pass {sweep}  . {k:16s} {elev_of(ship[k]):7.2f}    "
                      f"no legal direction fits yet ({len(rows)} tried)")
        if not moved:
            print(f"  pass {sweep}: nothing moved -- fixed point reached")
            break
    print()

    o = try_map(cur)
    if o is None:
        print("STAGE RESULT: REAIM_FEASIBLE_FAIL")
        return 1

    out = {}
    for k in sorted(names):
        v = dict(cur[k])
        v["r2451_reaimed"] = bool(chosen[k])
        v["r2451_shipped_elev_deg"] = round(elev_of(ship[k]), 4)
        v["r2451_elev_deg"] = round(elev_of(cur[k]), 4)
        if not chosen[k]:
            v["r2451_note"] = ("UNFIXABLE inside the existing schedule: every "
                               "direction inside the 25 deg / in-the-room band "
                               "makes beat 1's tour miss a part-flight deadline")
        out[k] = v
    json.dump(out, open(a.out, "w"), indent=1)

    fixed = [k for k in names if chosen[k]]
    left = [k for k in names if not chosen[k]]
    print(f"RE-AIMED  {len(fixed):2d}/15: " + (", ".join(fixed) or "none"))
    print(f"UNFIXABLE {len(left):2d}/15: " + (", ".join(left) or "none"))
    print()
    print(f"{'cluster':16s} {'shipped':>9s} {'now':>9s}")
    for k in sorted(names, key=lambda x: -elev_of(ship[x])):
        e0, e1 = elev_of(ship[k]), elev_of(out[k])
        print(f"{k:16s} {e0:9.2f} {e1:9.2f}"
              + ("" if out[k]["r2451_reaimed"] else "   (UNFIXABLE)"))
    print()
    print(f">> presentation order: {o}")
    print(f">> wrote {a.out}")
    print("STAGE RESULT: REAIM_FEASIBLE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
