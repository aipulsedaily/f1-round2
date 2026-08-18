"""Which part of the R2-451 re-aim survives EVERY beat-1 gate, not just the solve.

    python3 tools/beat1_reaim_gated.py --out work/b1nadir/presentation_normals_SHIP.json

WHY A SECOND SEARCH
-------------------
`beat1_reaim_feasible.py` searched against the part-flight deadlines and found 13
of 15 clusters re-aimable.  Built into an actual sheet, that candidate FAILS
three gates the shipped sheet passes:

    the camera passes 0.085 m from the assembled car body, f517-561   (limit 0.30)
    two moves peak at 4.41-4.95 m/s                                   (limit 4.00)
    the close-out entry sweeps 15.9-17.8 % of frame width per frame   (limit 12)

The deadline solve is one of five constraints and it was the only one being
consulted.  A station that is schedulable can still be a station the camera has
to crash through the car to reach.  So this search runs the WHOLE of
`build_beatsheet.py` for every candidate and reads its verdict, which is slower
by a large factor and is the only version of the question worth asking.

The clearance failure in particular is the one that matters and it is not a
tuning problem: pulling a corner station down to 5-23 deg of elevation puts it at
wheel height on the far side of the assembled car, and the straight run between
two such stations goes THROUGH the car.  That is the same class of defect
BEAT1_CLOSEOUT was hand-authored to fix (R2-029) and it is why the close-out is
hand-authored rather than solved.

WHAT THIS ACCEPTS
-----------------
A candidate ships only if its gate set is a SUBSET of the shipped sheet's.  The
shipped sheet already fails all fifteen framing-fit checks (R2-317) and this
block does not own that defect, so those are carried; anything else is a
regression this block would be introducing.
"""

import argparse
import json
import math
import os
import subprocess
import sys

R2 = os.path.expanduser("~/f1-round2")
CARRIED = "does not FIT its own presentation frame"   # R2-317, not this block's


def gates_of(normals_path, tag, cap=None, establish=None):
    env = dict(os.environ)
    if establish is not None:
        env["B1_ESTABLISH"] = establish
    env["B1_NORMALS"] = normals_path
    env["B1_SHEET_OUT"] = os.path.join(R2, f"work/b1nadir/gate_{tag}.json")
    env["TMPDIR"] = os.path.join(R2, "tmp")
    env["B1_MAX_DEPRESSION"] = cap or "25.0"
    r = subprocess.run([sys.executable, os.path.join(R2, "tools/build_beatsheet.py")],
                       capture_output=True, text=True, env=env, cwd=R2)
    out = r.stdout + r.stderr
    if "no visiting order satisfies" in out:
        return None, "UNSCHEDULABLE"
    fails = [ln.strip()[5:].strip() for ln in out.splitlines()
             if ln.strip().startswith("FAIL ")]
    hard = [f for f in fails if CARRIED not in f]
    order = None
    for ln in out.splitlines():
        if ln.startswith(">> beat 1 ORDER") or "presentation order" in ln:
            order = ln
    return hard, out


def elev_of(n):
    d = n["normal"]
    mm = math.sqrt(sum(x * x for x in d)) or 1.0
    return math.degrees(math.asin(max(-1.0, min(1.0, d[2] / mm))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--pin", default=None,
                    help="CLUSTER=x,y,z[;CLUSTER=x,y,z] -- fix a direction "
                         "before the greedy runs. See the R2-464 seed note.")
    ap.add_argument("--band", default=os.path.join(
        R2, "work/b1nadir/view_surface.json"))
    a = ap.parse_args()

    ship = json.load(open(os.path.join(R2, "docs/presentation_normals.json")))
    surf = json.load(open(a.band))
    plan = json.load(open(os.path.join(R2, "docs/explode_plan.json")))
    names = sorted(ship)

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

    tmp = os.path.join(R2, "work/b1nadir/_probe.json")

    def write(mp):
        json.dump(mp, open(tmp, "w"), indent=1)
        return tmp

    # ---- the baseline the candidates must not be worse than -----------------
    # The baseline is the SHIPPED file, which predates the backstop and carries
    # no `r2451_reaimed` markers, so the clamp must be off for it or the
    # baseline is not the shipped sheet at all -- it is a clamped variant of it
    # that does not schedule, and every candidate would be compared against a
    # baseline that never shipped.
    # THE BASELINE IS THE SHIPPED FILM, WHICH HAS NO ESTABLISHING KEY.
    # Computing it with B1_ESTABLISH on was wrong and it silently widened the
    # acceptance test: the shipped MB direction puts its station 8.29 m from the
    # establishing station, which fails the weave-speed gate, so the baseline
    # came back with 1 hard failure and every candidate was then allowed one
    # too -- including the same one. A baseline must be the artefact being
    # improved on, not the artefact plus the defect under repair.
    base_hard, _ = gates_of(os.path.join(R2, "docs/presentation_normals.json"),
                            "base", cap="90", establish="0")
    print("SHIPPED SHEET, hard gate failures (framing-fit carried, R2-317):")
    for f in base_hard:
        print("   " + f[:110])
    if not base_hard:
        print("   none")
    print()

    cur = {k: dict(ship[k]) for k in names}
    for k in names:
        cur[k]["r2451_reaimed"] = False
    chosen = {k: False for k in names}

    # R2-464 SEED. The establishing station and MB's direction were solved as a
    # PAIR (build_beatsheet.BEAT1_ESTABLISH), so they have to be applied as one.
    # Greedy cannot discover the pair: with the establishing key present and MB
    # still shipped, the establish->MB move is 8.29 m in 2.0 s and fails the
    # weave-speed gate, so EVERY candidate carries that failure and nothing is
    # ever accepted -- the search reports 0/15 and looks like a refutation when
    # it is a seeding problem. Seeding MB clears the failure and the greedy then
    # works normally on the other fourteen.
    if a.pin:
        for spec in a.pin.split(";"):
            k, vec = spec.split("=")
            cur[k.strip()]["normal"] = [float(x) for x in vec.split(",")]
            cur[k.strip()]["r2451_reaimed"] = True
            chosen[k.strip()] = True
            print(f"SEEDED {k.strip()} = {cur[k.strip()]['normal']}  "
                  f"(solved jointly with the establishing station)")
        print()

    order_by_need = sorted(names, key=lambda k: -elev_of(ship[k]))
    print("GREEDY over the legal band, worst picture first, gated on the WHOLE")
    print("beat-1 gate set. A candidate is accepted only if it introduces no")
    print("hard failure the shipped sheet does not already have.")
    print()
    for sweep in range(1, 5):
        moved = 0
        for k in order_by_need:
            if chosen[k]:
                continue
            rows = band(k)
            got = None
            for j, (sc, e, d, pa, rich) in enumerate(rows):
                cand = {kk: dict(vv) for kk, vv in cur.items()}
                cand[k]["normal"] = [round(x, 5) for x in d]
                cand[k]["projected_area_m2"] = round(pa, 5)
                cand[k]["distinct_materials"] = int(rich)
                cand[k]["score"] = round(sc, 5)
                cand[k]["r2451_reaimed"] = True
                hard, _o = gates_of(write(cand), "probe")
                if hard is not None and len(hard) <= len(base_hard):
                    cur = cand
                    got = (j, sc, e, len(hard))
                    break
            if got:
                j, sc, e, nh = got
                kept = sc / max(surf["clusters"][k]["best_score"], 1e-9)
                chosen[k] = True
                moved += 1
                print(f"  pass {sweep}  + {k:16s} {elev_of(ship[k]):7.2f} -> "
                      f"{e:6.2f} deg   score {kept:5.1%}   tried {j:2d}/{len(rows)}"
                      f"   hard fails {nh}")
            elif sweep == 1:
                print(f"  pass {sweep}  . {k:16s} {elev_of(ship[k]):7.2f}    "
                      f"no legal direction survives the gates ({len(rows)} tried)")
        if not moved:
            print(f"  pass {sweep}: nothing moved -- fixed point")
            break
    print()

    out = {}
    for k in names:
        v = dict(cur[k])
        v["r2451_shipped_elev_deg"] = round(elev_of(ship[k]), 4)
        v["r2451_elev_deg"] = round(elev_of(cur[k]), 4)
        if not chosen[k]:
            v["r2451_note"] = (
                "NOT re-aimed: no direction inside the 25 deg / in-the-room band "
                "clears beat 1's clearance, speed and pan gates at the shipped "
                "standoff and the shipped 33.0 s span. See R2-455.")
        out[k] = v
    json.dump(out, open(a.out, "w"), indent=1)

    fixed = [k for k in names if chosen[k]]
    print(f"RE-AIMED  {len(fixed):2d}/15: " + (", ".join(fixed) or "none"))
    print(f"UNCHANGED {15 - len(fixed):2d}/15: "
          + (", ".join(k for k in names if not chosen[k]) or "none"))
    print()
    print(f"{'cluster':16s} {'shipped':>9s} {'now':>9s}")
    for k in sorted(names, key=lambda x: -elev_of(ship[x])):
        print(f"{k:16s} {elev_of(ship[k]):9.2f} {elev_of(out[k]):9.2f}"
              + ("" if chosen[k] else "   (unchanged)"))
    print(f"\n>> wrote {a.out}")
    print("STAGE RESULT: REAIM_GATED_OK")


if __name__ == "__main__":
    main()
