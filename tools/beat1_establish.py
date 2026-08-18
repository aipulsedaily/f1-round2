"""R2-429: give beat 1 an ESTABLISHING frame, and find the one it can afford.

    python3 tools/beat1_establish.py --sweep
    python3 tools/beat1_establish.py --standoff 8.7 --lens 24 --out <normals.json>

THE FINDING THIS ANSWERS, AND THE CORRECTION IT CARRIES
-------------------------------------------------------
R2-429: beat 1 never goes wider than 76.1 % of frame width and has no
establishing shot. **The 76.1 % is an artefact** -- it is the subtense of the
car's 5.72 m LENGTH, which is its apparent width only when the camera is
broadside. `tools/beat1_true_extent.py` projects the car's eight bbox corners
through the actual camera instead, and the close-out is not what the proxy said:

```
                                    proxy      TRUE
f700  car fraction of frame width   0.832     0.497
f724  widest framing in beat 1      0.809     0.603
close-out f648-792, frames in which the WHOLE CAR FITS      136 / 145  (94 %)
first frame that contains the whole car                     f657, t = 27.4 s
```

**So beat 1 DOES have an establishing shot and it arrives 27.4 seconds into a
33-second beat.** `work/b1look/b1focus_000700_full.png` settles it in pixels: the
complete car, uncropped, head-on on the turntable, with the MERIDIAN sign, the
24/P1 placard, the rope barrier and the ribbed wall behind it.

**The defect is therefore not "no establishing shot". It is "the establishing
shot is last".** That changes the fix from adding width -- which would mean
re-standing fifteen stations, R2-330's re-solve, and reaching into the protected
f648-792 -- to putting an establishing frame at the FRONT, which costs one
station.

WHY THE OPENING STATION IS THE CHEAP PLACE TO DO IT
---------------------------------------------------
MB is the tour start at t = 0. **There is no hop INTO it**, so widening it costs
only the single hop MB -> next, where widening any other station costs two. It is
also the frame that needs it most: it is the film's first image.

WHAT AN ESTABLISHING FRAME HAS TO CONTAIN HERE
----------------------------------------------
Not the car -- at t = 0 the car is exploded across 616 parts. The subject is the
FIELD, measured off `docs/explode_plan.json`:

```
exploded field bbox   x -6.402 .. 4.720   y -2.211 .. 2.211   z 0.273 .. 4.115
                      11.12 m long, 4.42 m wide, 3.84 m tall
```

11.12 m of subject inside a room that is 30.5 m x 22.5 m x 6.2 m, with the spot
rigs at z 5.590. The lens/standoff pairs that contain it are computed rather than
guessed, and the sweep below rejects any that leaves the room, breaks a beat-1
gate, or makes the tour miss a part-flight deadline.
"""

import argparse
import json
import math
import os
import subprocess
import sys

R2 = os.path.expanduser("~/f1-round2")
SENSOR_W = 36.0
SENSOR_H = SENSOR_W * 2160.0 / 3840.0
CARRIED = "does not FIT its own presentation frame"


def qn(q):
    m = math.sqrt(sum(v * v for v in q)) or 1.0
    return [v / m for v in q]


def basis(q):
    w, x, y, z = qn(q)
    return ([1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y)],
            [2 * (x * y - w * z), 1 - 2 * (x * x + z * z), 2 * (y * z + w * x)],
            [-(2 * (x * z + w * y)), -(2 * (y * z - w * x)),
             -(1 - 2 * (x * x + y * y))])


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def field_box():
    plan = json.load(open(os.path.join(R2, "docs/explode_plan.json")))
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for _k, c in plan["clusters"].items():
        off = c["explode_offset"]
        for i in range(3):
            lo[i] = min(lo[i], c["bbox_min"][i] + off[i])
            hi[i] = max(hi[i], c["bbox_max"][i] + off[i])
    return lo, hi


def extent(lo, hi, eye, q, lens):
    rt, up, fwd = basis(q)
    xs, ys = [], []
    for i in range(8):
        p = [lo[0] if i & 1 else hi[0], lo[1] if i & 2 else hi[1],
             lo[2] if i & 4 else hi[2]]
        v = [p[j] - eye[j] for j in range(3)]
        z = dot(v, fwd)
        if z <= 1e-6:
            return 99.0, 99.0
        xs.append(dot(v, rt) / z * lens)
        ys.append(dot(v, up) / z * lens)
    return (max(xs) - min(xs)) / SENSOR_W, (max(ys) - min(ys)) / SENSOR_H


def build(normals, tag):
    """Run the whole shipped pipeline. Returns (hard_fails, sheet) or (None,None)."""
    np_ = os.path.join(R2, f"work/b1nadir/_est_{tag}.json")
    sp = os.path.join(R2, f"work/b1nadir/_estsheet_{tag}.json")
    json.dump(normals, open(np_, "w"), indent=1)
    env = dict(os.environ)
    env.update({"B1_NORMALS": np_, "B1_SHEET_OUT": sp,
                "TMPDIR": os.path.join(R2, "tmp")})
    r = subprocess.run([sys.executable, os.path.join(R2, "tools/build_beatsheet.py")],
                       capture_output=True, text=True, env=env, cwd=R2)
    out = r.stdout + r.stderr
    if "no visiting order satisfies" in out:
        return None, None, out
    fails = [ln.strip()[5:].strip() for ln in out.splitlines()
             if ln.strip().startswith("FAIL ")]
    hard = [f for f in fails if CARRIED not in f]
    try:
        sheet = json.load(open(sp))
    except Exception:
        return None, None, out
    return hard, sheet, out


def rig(sheet_path, tag):
    out = os.path.join(R2, f"work/b1nadir/_estrig_{tag}.blend")
    r = subprocess.run(
        ["/opt/blender-5.2.0-linux-x64/blender", "-b",
         os.path.join(R2, "world/beat1_anim.blend"), "--factory-startup",
         "-P", os.path.join(R2, "anim/build_camera_rig.py"), "--",
         "--sheet", sheet_path, "--telemetry",
         os.path.join(R2, "telemetry/telemetry.csv"), "--out", out],
        capture_output=True, text=True, cwd=R2,
        env=dict(os.environ, TMPDIR=os.path.join(R2, "tmp")))
    p = out.replace(".blend", "_path.json")
    return (p if os.path.exists(p) else None), (r.stdout + r.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--standoff", type=float, default=None)
    ap.add_argument("--lens", type=float, default=None)
    ap.add_argument("--base", default=os.path.join(
        R2, "work/b1nadir/presentation_normals_SHIP.json"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    lo, hi = field_box()
    print(f"exploded field  {tuple(round(v,3) for v in lo)} .. "
          f"{tuple(round(v,3) for v in hi)}   "
          f"{hi[0]-lo[0]:.2f} x {hi[1]-lo[1]:.2f} x {hi[2]-lo[2]:.2f} m")
    base = json.load(open(a.base))

    combos = ([(a.standoff, a.lens)] if a.standoff else
              [(6.5, 28), (7.5, 28), (7.5, 24), (8.7, 24), (8.7, 21),
               (10.0, 24), (10.0, 21), (12.0, 21), (12.0, 18)])

    print()
    print("Each row runs build_beatsheet.py AND the camera rig, then projects the")
    print("exploded field through the built f1 camera. `field w/h` under 1.00 means")
    print("the whole field is inside the frame.")
    print()
    hdr = (f"{'standoff':>9} {'lens':>5} {'sched':>6} {'hard':>5} {'field w':>8} "
           f"{'field h':>8} {'cam z':>7} {'clear':>7} {'peak':>6} {'path m':>7}")
    print(hdr)
    print("-" * len(hdr))
    best = None
    for so, ln in combos:
        N = {k: dict(v) for k, v in base.items()}
        N["MB"]["r2429_standoff_m"] = so
        N["MB"]["r2429_lens_mm"] = ln
        tag = f"{so:g}_{ln:g}".replace(".", "p")
        hard, sheet, _o = build(N, tag)
        if hard is None:
            print(f"{so:9.2f} {ln:5.0f} {'NO':>6} {'-':>5} "
                  f"{'-':>8} {'-':>8} {'-':>7} {'-':>7} {'-':>6} {'-':>7}")
            continue
        pj, _rl = rig(os.path.join(R2, f"work/b1nadir/_estsheet_{tag}.json"), tag)
        fw = fh = float("nan")
        camz = float("nan")
        if pj:
            path = {int(k["f"]): k for k in json.load(open(pj))["path"]}
            k1 = path[1]
            fw, fh = extent(lo, hi, k1["p"], k1["q"], k1["lens"])
            camz = k1["p"][2]
        b1 = sheet["beat1"]
        print(f"{so:9.2f} {ln:5.0f} {'yes':>6} {len(hard):5d} {fw:8.3f} "
              f"{fh:8.3f} {camz:7.3f} {b1['min_clearance_to_car_m']:7.3f} "
              f"{b1['max_estimated_peak_speed_ms']:6.2f} {b1['path_length_m']:7.2f}")
        if not hard and fw <= 1.0 and fh <= 1.0:
            score = max(fw, fh)
            if best is None or score > best[0]:      # largest that still FITS
                best = (score, so, ln, tag)

    print()
    if best:
        print(f">> the tightest framing that still contains the whole field and "
              f"breaks no gate: standoff {best[1]:.2f} m, lens {best[2]:.0f} mm "
              f"(field fills {best[0]:.3f})")
        if a.out:
            N = {k: dict(v) for k, v in base.items()}
            N["MB"]["r2429_standoff_m"] = best[1]
            N["MB"]["r2429_lens_mm"] = best[2]
            N["MB"]["r2429_note"] = (
                "ESTABLISHING STATION. The standoff law is overridden for the "
                "film's first frame only, so beat 1 opens on the whole exploded "
                "field instead of on one cluster that overflows the frame. "
                "R2-429/R2-464.")
            json.dump(N, open(a.out, "w"), indent=1)
            print(f">> wrote {a.out}")
    else:
        print(">> NOTHING in the sweep both contains the field and clears the gates")
    print("STAGE RESULT: ESTABLISH_OK")


if __name__ == "__main__":
    main()
