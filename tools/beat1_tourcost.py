"""What a presentation-direction choice COSTS the camera, in seconds of tour.

    python3 tools/beat1_tourcost.py --normals docs/presentation_normals.json
    python3 tools/beat1_tourcost.py --sweep

R2-451's SECOND FINDING, and it was not anticipated
---------------------------------------------------
Pulling the stations out of the nadir makes beat 1's tour LONGER, and the reason
is geometric rather than incidental.  A station sits at `centre + d * standoff`.
When every `d` points nearly straight up, all fifteen stations sit nearly
directly ABOVE their clusters, so the camera hovers over a field 6 m across.
When `d` is shallow, the station swings out to a horizontal radius of
`standoff * cos(elev)` and the camera has to fly AROUND the field instead.

And there is a second term that is easy to miss.  `move_seconds` charges for the
PAN as well as the chord, and the pan is the bearing between consecutive view
directions.  Fifteen near-nadir view directions are all nearly parallel to each
other, so the shipped tour costs almost nothing in pans.  A photographic tour
points the lens in fifteen genuinely different directions and pays for all of
them.

So the nadir framing was not only cheap to look at.  It was buying the schedule.
This tool prices that, because "the fix does not fit in 33 s" is a claim that
needs a number rather than a failed solve.

It reports, for any normals file, the Held-Karp OPTIMUM with the flight
deadlines switched off -- so a configuration that cannot be scheduled still
returns a cost instead of a SystemExit -- plus the worst deadline slack at that
optimum, which is the quantity that actually decides feasibility.
"""

import argparse
import importlib.util
import json
import math
import os
import sys

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "tools"))


def load_bbs():
    spec = importlib.util.spec_from_file_location(
        "bbs", os.path.join(R2, "tools/build_beatsheet.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def cost_of(m, geo, normals, order):
    n = len(order)
    cum, rows = 0.0, []
    for i in range(1, n):
        c = m._hop_cost(geo, normals, order[i - 1], i - 1, order[i], i, n,
                        cost=m.order_seconds)
        cum += c
        rows.append((order[i], c, cum))
    return cum, rows


def best_tour(m, geo, normals, order):
    """Held-Karp over the same 11-node spine + 4-node corner problem, deadlines
    OFF.  Reuses the shipped cost function so this is the same objective the
    real solver minimises, only without the feasibility filter."""
    import itertools
    spine = [k for k in order if not k.startswith("CORNER_")]
    corners = [k for k in order if k.startswith("CORNER_")]
    n = len(order)
    start, rest = spine[0], spine[1:]
    mfree = len(rest)
    INF = float("inf")
    dp = {}
    par = {}
    for j, b in enumerate(rest):
        dp[(1 << j, j)] = m._hop_cost(geo, normals, start, 0, b, 1, n,
                                      cost=m.order_seconds)
        par[(1 << j, j)] = None
    for mask in range(1, 1 << mfree):
        for last in range(mfree):
            if not mask & (1 << last):
                continue
            cur = dp.get((mask, last))
            if cur is None:
                continue
            depth = bin(mask).count("1")
            for nxt in range(mfree):
                if mask & (1 << nxt):
                    continue
                c = cur + m._hop_cost(geo, normals, rest[last], depth,
                                      rest[nxt], depth + 1, n,
                                      cost=m.order_seconds)
                key = (mask | (1 << nxt), nxt)
                if c < dp.get(key, INF):
                    dp[key] = c
                    par[key] = last
    full = (1 << mfree) - 1
    best, blast = INF, None
    for last in range(mfree):
        v = dp.get((full, last))
        if v is not None and v < best:
            best, blast = v, last
    seq, mask, last = [], full, blast
    while last is not None:
        seq.append(rest[last])
        nl = par[(mask, last)]
        mask ^= (1 << last)
        last = nl
    seq.reverse()
    spine_seq = [start] + seq
    # corners: 3! with CORNER_FL pinned last, entered from the spine's exit
    free = [k for k in corners if k != "CORNER_FL"]
    bc, bseq = INF, None
    for perm in itertools.permutations(free):
        s = list(perm) + ["CORNER_FL"]
        tot, prev = 0.0, spine_seq[-1]
        for i, k in enumerate(s):
            tot += m._hop_cost(geo, normals, prev, len(spine_seq) + i - 1,
                               k, len(spine_seq) + i, n, cost=m.order_seconds)
            prev = k
        if tot < bc:
            bc, bseq = tot, s
    return best + bc, spine_seq + bseq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normals", default=os.path.join(R2, "docs/presentation_normals.json"))
    ap.add_argument("--sweep", action="store_true")
    a = ap.parse_args()

    os.environ["B1_MAX_DEPRESSION"] = "90"      # this tool prices files, not clamps
    m = load_bbs()
    plan = json.load(open(os.path.join(R2, "docs/explode_plan.json")))
    geo = m.cluster_geometry(plan)
    anim = json.load(open(os.path.join(R2, "world/beat1_anim_anim.json")))
    flight_f = float(anim.get("flight_s", 1.55)) * 24
    deadlines = {c: (v["seat_frame"] - flight_f) / 24.0 - 0.5
                 for c, v in anim.get("clusters", {}).items()}
    order0 = json.load(open(os.path.join(R2, "docs/beat_sheet.json"))
                       )["beat1"]["present_order"]
    SPAN = 33.0

    def price(path, label):
        N = json.load(open(path))
        cost, seq = best_tour(m, geo, N, order0)
        scale = SPAN / cost
        _c, rows = cost_of(m, geo, N, seq)
        slack = min(deadlines.get(k, 1e9) - t * scale for k, _c2, t in rows)
        late = [k for k, _c2, t in rows if t * scale > deadlines.get(k, 1e9)]
        elev = []
        for k in seq:
            d = N[k]["normal"]
            mm = math.sqrt(sum(x * x for x in d)) or 1.0
            elev.append(math.degrees(math.asin(max(-1, min(1, d[2] / mm)))))
        print(f"{label:28s} tour {cost:7.3f} s   scale {scale:6.4f}   "
              f"worst slack {slack:+8.3f} s   late {len(late):2d}   "
              f"elev {min(elev):6.1f}..{max(elev):5.1f}")
        return cost, slack, late

    print("Held-Karp optimum with the flight deadlines OFF, then the deadline")
    print("slack that optimum would have once scaled into beat 1's 33.0 s.")
    print("A NEGATIVE worst slack is why the real solver returns 'no visiting")
    print("order satisfies the flight deadlines'.")
    print()
    price(os.path.join(R2, "docs/presentation_normals.json"), "SHIPPED (nadir)")
    if a.sweep:
        for cap in (25, 30, 35, 40, 45, 50, 60, 70):
            for tol in (0.0, 0.03, 0.10):
                p = os.path.join(R2, f"work/b1nadir/sweep/n{cap}_t{int(tol*100)}.json")
                os.system(f"cd {R2} && python3 tools/beat1_reaim.py --quiet "
                          f"--max-depression {cap} --score-tol {tol} --out {p} "
                          f">/dev/null 2>&1")
                price(p, f"cap {cap:2d} deg, tol {tol:.2f}")
    else:
        price(a.normals, os.path.basename(a.normals))
    print()
    print("STAGE RESULT: TOURCOST_OK")


if __name__ == "__main__":
    main()
