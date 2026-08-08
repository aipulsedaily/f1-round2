#!/usr/bin/env python3
"""WHAT THE CAMERA IS DOING, EVERY FRAME, IN THE THREE UNITS A VIEWER FEELS.

    .venv/bin/python tools/camera_tempo.py --path <rig>_path.json \
        --sheet docs/beat_sheet.json [--json out.json] [--flat-threshold 0.10]

WHY THIS FILE EXISTS SEPARATELY FROM tools/campath_pacing.py
------------------------------------------------------------------------
R2-1601 built `campath_pacing.py` and reported 96.8 % of the film flat in one
85 s run.  The brief that sent me here says, correctly, that a number is a claim
until it is re-derived by something that did not inherit its assumptions.  So
this instrument was written WITHOUT reading that one, from the per-frame rig
path, and the two are compared afterwards.  Agreement between two independent
derivations is evidence; agreement between a file and its own copy is not.

WHAT IT MEASURES, AND WHY THESE THREE
------------------------------------------------------------------------
In a ONE-SHOT WITH ZERO CUTS there are exactly three ways to put a beat into a
viewer's attention, because there is no edit to do it for you:

  1. ACCELERATION   -- the speed of the move CHANGING.  A camera at constant
                       speed is felt as a background condition, not an event.
  2. DIRECTION CHANGE -- where the lens is pointed CHANGING, measured in FRAME
                       WIDTHS PER SECOND, not degrees.  5 deg in a 90 deg lens
                       is nothing and 5 deg in a 10 deg lens is a whip; the
                       project's own beat-1 report already uses %-of-frame-width
                       per frame, so this is the house unit.
  3. ZOOM           -- focal length changing, likewise normalised by the fov it
                       is changing.

"New information entering frame" is the fourth lever the brief names and it is
NOT measured here: it needs scene content, not the camera curve alone.  It is
left out rather than faked -- the immediately preceding round of this project
had a subagent "find" a novelty instrument that was a file it had written five
minutes earlier, and the remedy for that is to say plainly what an instrument
does not do.

THE FLATNESS DEFINITION IS SELF-CALIBRATING, WHICH IS THE POINT
------------------------------------------------------------------------
There is no absolute physical constant for "a viewer notices this much
acceleration", and inventing one would make every number here an argument about
the constant instead of about the film.  So each channel is normalised by ITS
OWN 95th percentile ACROSS THIS FILM, and the per-frame gesture is the largest
of the normalised channels:

    G(f) = max( |a| / p95(|a|),  |dP/dt| / p95(|dP/dt|),  |dZ/dt| / p95(|dZ/dt|) )

G = 1.0 is "as much gesture as this film's own busiest moments".  A frame is
FLAT when G < threshold (default 0.10): less than a tenth of the gesture the
film itself demonstrates it can produce.  This cannot be gamed by choosing
units, it needs no external constant, and `--flat-threshold` sweeps it so the
census can be shown to be a property of the film rather than of the cut-off.

A run is a maximal stretch of consecutive flat frames.  Runs are reported with
their beats, because a run that crosses a beat boundary is a different kind of
problem from one inside a beat.
"""
import argparse
import json
import math
import os
import sys

FPS = 24.0
SENSOR_W_MM = 36.0
R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def hfov_deg(lens_mm):
    return math.degrees(2.0 * math.atan(SENSOR_W_MM / (2.0 * max(lens_mm, 1e-6))))


def view_dir(q):
    """Camera -Z in world.  Blender quaternions are [w, x, y, z]."""
    w, x, y, z = q
    # third column of R(q) is the local +Z axis in world coords
    zx = 2.0 * (x * z + w * y)
    zy = 2.0 * (y * z - w * x)
    zz = 1.0 - 2.0 * (x * x + y * y)
    return (-zx, -zy, -zz)


def ang_between(u, v):
    d = sum(a * b for a, b in zip(u, v))
    d = max(-1.0, min(1.0, d))
    return math.degrees(math.acos(d))


def percentile(xs, p):
    if not xs:
        return 0.0
    s = sorted(xs)
    k = (len(s) - 1) * p
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    if lo == hi:
        return s[lo]
    return s[lo] * (hi - k) + s[hi] * (k - lo)


def beat_of_frame(sheet, f):
    """Name of the beat containing film frame `f` (1-based)."""
    t = (f - 1) / FPS
    best = "-"
    for b in sheet["beats"]:
        if b["start_s"] <= t < b["start_s"] + b["duration_s"]:
            return b["name"]
        if t >= b["start_s"]:
            best = b["name"]
    return best


def measure(path_json, sheet):
    """Per-frame kinematics off the rig's own path.  Nothing is smoothed."""
    P = {int(e["f"]): e for e in path_json["path"]}
    frames = sorted(P)
    n = len(frames)

    pos = {f: P[f]["p"] for f in frames}
    vdir = {f: view_dir(P[f]["q"]) for f in frames}
    fov = {f: hfov_deg(P[f]["lens"]) for f in frames}

    # first derivatives (backward difference; f and f-1 must both exist)
    v, pan, zoom = {}, {}, {}
    for f in frames:
        g = f - 1
        if g not in P:
            continue
        v[f] = math.dist(pos[f], pos[g]) * FPS                      # m/s
        # direction change in FRAME WIDTHS per second
        pan[f] = (ang_between(vdir[f], vdir[g]) / fov[f]) * FPS     # widths/s
        zoom[f] = (abs(fov[f] - fov[g]) / fov[f]) * FPS             # 1/s

    # second derivatives
    acc, pacc, zacc = {}, {}, {}
    for f in frames:
        g = f - 1
        if f in v and g in v:
            acc[f] = (v[f] - v[g]) * FPS                            # m/s^2
        if f in pan and g in pan:
            pacc[f] = (pan[f] - pan[g]) * FPS                       # widths/s^2
        if f in zoom and g in zoom:
            zacc[f] = (zoom[f] - zoom[g]) * FPS                     # 1/s^2

    common = [f for f in frames if f in acc and f in pacc and f in zacc]

    # ---- self-calibrating normalisation --------------------------------
    ref = {
        "acc": percentile([abs(acc[f]) for f in common], 0.95),
        "pan_acc": percentile([abs(pacc[f]) for f in common], 0.95),
        "zoom_acc": percentile([abs(zacc[f]) for f in common], 0.95),
    }
    for k in ref:
        if ref[k] <= 0:
            ref[k] = 1e-9

    G = {}
    chan = {}
    for f in common:
        c = {
            "acc": abs(acc[f]) / ref["acc"],
            "pan_acc": abs(pacc[f]) / ref["pan_acc"],
            "zoom_acc": abs(zacc[f]) / ref["zoom_acc"],
        }
        chan[f] = c
        G[f] = max(c.values())

    return {
        "frames": frames, "n": n, "common": common,
        "v": v, "pan": pan, "zoom": zoom,
        "acc": acc, "pan_acc": pacc, "zoom_acc": zacc,
        "ref": ref, "G": G, "chan": chan,
    }


def flat_runs(m, sheet, thr):
    """Maximal runs of consecutive frames whose gesture is below `thr`."""
    common = m["common"]
    G = m["G"]
    runs, cur = [], None
    for f in common:
        if G[f] < thr:
            if cur is None:
                cur = [f, f]
            else:
                cur[1] = f
        else:
            if cur is not None:
                runs.append(tuple(cur))
                cur = None
    if cur is not None:
        runs.append(tuple(cur))

    out = []
    for a, b in runs:
        nf = b - a + 1
        beats = []
        for f in range(a, b + 1):
            nm = beat_of_frame(sheet, f)
            if not beats or beats[-1] != nm:
                beats.append(nm)
        out.append({
            "f0": a, "f1": b, "frames": nf, "seconds": nf / FPS,
            "t0": round((a - 1) / FPS, 2), "t1": round((b - 1) / FPS, 2),
            "beats": beats,
            "mean_G": round(sum(G[f] for f in range(a, b + 1)) / nf, 4),
        })
    out.sort(key=lambda r: -r["frames"])
    return out


def cam_basis(q):
    """(right, up, forward) unit vectors in world for a Blender camera quat."""
    w, x, y, z = q
    right = (1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y))
    up = (2 * (x * y - w * z), 1 - 2 * (x * x + z * z), 2 * (y * z + w * x))
    fwd = view_dir(q)
    return right, up, fwd


# THE CAR'S LENGTH IS IMPORTED, NOT TYPED.  R2-2177.
#
# This file shipped `CAR_LEN_M = 5.63` -- a hand-typed private copy, wrong by
# 68 mm against the contract's 5.698, and the EIGHTH copy of the car's
# dimensions found in this codebase.  I wrote it while measuring other people's
# divergent copies, which is the whole argument for importing: a constant you
# re-type is a constant that will drift, and being the person auditing the drift
# is no protection at all.
sys.path.insert(0, os.path.join(R2, "world"))
import world_contract as WC                                        # noqa: E402

CAR_LEN_M = WC.CAR_BODY_LEN_M          # 5.698, from the one authority


def measure_subject(path_json, sheet, telemetry, spec_path):
    """WHERE THE SUBJECT SITS IN FRAME, EVERY FRAME.

    THIS IS THE CHANNEL THAT SETTLES THE ARGUMENT, and it is worth saying why.
    A camera's own acceleration in m/s^2 is not a thing a viewer can see.  What
    a viewer sees is the PICTURE changing: the subject sliding across the frame,
    growing, shrinking.  A camera doing 60 m/s alongside a car doing 60 m/s has
    enormous kinetic numbers and a DEAD STILL picture, and that is exactly the
    shot a client falls asleep in.  So the subject's screen position and screen
    size are measured directly, in frame widths, off the real telemetry.
    """
    sys.path.insert(0, os.path.join(R2, "anim"))
    import carpath
    import filmtime as FT

    spec = json.load(open(spec_path))
    car = carpath.Car(telemetry, spec)
    P = {int(e["f"]): e for e in path_json["path"]}
    N = int(path_json["frames"])
    scales, _ramp = FT.build_time_map(sheet, N)
    W = FT.world_time_table(scales, N)

    out = {}
    for f in sorted(P):
        e = P[f]
        cam = e["p"]
        right, up, fwd = cam_basis(e["q"])
        hf = math.radians(hfov_deg(e["lens"]))
        wt = W[max(1, min(N, f))]
        cpos, _hd, _v = car.state(wt)
        w = [cpos[i] - cam[i] for i in range(3)]
        D = math.sqrt(sum(c * c for c in w)) or 1e-6
        fz = sum(w[i] * fwd[i] for i in range(3))
        fx = sum(w[i] * right[i] for i in range(3))
        fy = sum(w[i] * up[i] for i in range(3))
        # frame widths from centre; behind the camera is reported as None
        if fz > 1e-6:
            u = (fx / fz) / (2.0 * math.tan(hf / 2.0))
            v = (fy / fz) / (2.0 * math.tan(hf / 2.0))
            onscreen = abs(u) <= 0.5
        else:
            u = v = None
            onscreen = False
        size = (CAR_LEN_M / D) / hf          # subject width as a frame fraction
        out[f] = {"D": D, "u": u, "v": v, "size": size, "onscreen": onscreen}

    # derivatives of the picture
    for f in sorted(out):
        g = f - 1
        o = out[f]
        o["subj_speed"] = None
        o["loom"] = None
        if g in out:
            a, b = out[g], out[f]
            if None not in (a["u"], b["u"]):
                o["subj_speed"] = math.dist((a["u"], a["v"]),
                                            (b["u"], b["v"])) * FPS
            o["loom"] = ((b["size"] - a["size"]) / max(a["size"], 1e-9)) * FPS
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="a *_path.json from build_camera_rig")
    ap.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    ap.add_argument("--flat-threshold", type=float, default=0.10)
    ap.add_argument("--json", default=None)
    ap.add_argument("--per-beat", action="store_true")
    ap.add_argument("--telemetry", default=None,
                    help="telemetry/telemetry.csv — adds the subject-in-frame channels")
    ap.add_argument("--spec", default=os.path.join(R2, "docs/circuit_spec.json"))
    ap.add_argument("--window", type=float, default=1.0,
                    help="seconds, for the rolling report only")
    a = ap.parse_args()

    path_json = json.load(open(a.path))
    sheet = json.load(open(a.sheet))
    m = measure(path_json, sheet)

    print(f">> camera tempo — {m['n']} frames ({m['n'] / FPS:.2f} s) from "
          f"{os.path.relpath(a.path, R2) if a.path.startswith(R2) else a.path}")
    print(f">> normalisation (95th pct of |channel| across the whole film): "
          f"accel {m['ref']['acc']:.4f} m/s^2, "
          f"pan-accel {m['ref']['pan_acc']:.4f} widths/s^2, "
          f"zoom-accel {m['ref']['zoom_acc']:.4f} 1/s^2")

    # ---- the census, and its sensitivity to the cut-off ------------------
    print(">> FLAT CENSUS — a frame is flat when its gesture is under the "
          "threshold, as a fraction of this film's own 95th-percentile gesture")
    for thr in (0.05, a.flat_threshold, 0.20, 0.30):
        rs = flat_runs(m, sheet, thr)
        nflat = sum(r["frames"] for r in rs)
        pct = 100.0 * nflat / max(len(m["common"]), 1)
        big = rs[0] if rs else None
        print(f"   threshold {thr:.2f}: {pct:5.1f} % of frames flat in "
              f"{len(rs):4d} runs; largest {big['seconds']:6.2f} s "
              f"(f{big['f0']}-{big['f1']}, {'+'.join(big['beats'])})"
              if big else f"   threshold {thr:.2f}: no flat frames")

    rs = flat_runs(m, sheet, a.flat_threshold)
    print(f">> the ten longest runs at threshold {a.flat_threshold:.2f}")
    for r in rs[:10]:
        print(f"   {r['seconds']:7.2f} s  f{r['f0']:5d}-{r['f1']:<5d} "
              f"t {r['t0']:7.2f}-{r['t1']:<7.2f}  mean G {r['mean_G']:.4f}  "
              f"{'+'.join(r['beats'])}")

    # ---- per-beat summary -------------------------------------------------
    print(">> PER BEAT — median and 95th percentile of each channel")
    print("   %-12s %6s  %8s %8s  %8s %8s  %8s" %
          ("beat", "frames", "med|a|", "p95|a|", "med pan", "p95 pan", "med G"))
    by_beat = {}
    for f in m["common"]:
        by_beat.setdefault(beat_of_frame(sheet, f), []).append(f)
    order = [b["name"] for b in sheet["beats"]]
    for nm in order + [k for k in by_beat if k not in order]:
        fs = by_beat.get(nm)
        if not fs:
            continue
        aa = [abs(m["acc"][f]) for f in fs]
        pp = [abs(m["pan"][f]) for f in fs]
        gg = [m["G"][f] for f in fs]
        print("   %-12s %6d  %8.3f %8.3f  %8.4f %8.4f  %8.4f" %
              (nm, len(fs), percentile(aa, 0.5), percentile(aa, 0.95),
               percentile(pp, 0.5), percentile(pp, 0.95), percentile(gg, 0.5)))

    # ---- the picture, not the camera ------------------------------------
    subj = None
    if a.telemetry:
        subj = measure_subject(path_json, sheet, a.telemetry, a.spec)
        print(">> THE PICTURE — where the car actually sits in frame, per beat")
        print("   %-12s %6s %8s %8s %8s %9s %8s" %
              ("beat", "frames", "onscr%", "med|uv|", "med size",
               "med move", "med loom"))
        for nm in order:
            fs = [f for f in by_beat.get(nm, []) if f in subj]
            if not fs:
                continue
            on = [f for f in fs if subj[f]["onscreen"]]
            uv = [math.hypot(subj[f]["u"], subj[f]["v"])
                  for f in fs if subj[f]["u"] is not None]
            sz = [subj[f]["size"] for f in fs]
            mv = [subj[f]["subj_speed"] for f in fs
                  if subj[f]["subj_speed"] is not None]
            lm = [abs(subj[f]["loom"]) for f in fs
                  if subj[f]["loom"] is not None]
            print("   %-12s %6d %7.1f%% %8.3f %8.3f %9.4f %8.4f" %
                  (nm, len(fs), 100.0 * len(on) / len(fs),
                   percentile(uv, 0.5) if uv else float("nan"),
                   percentile(sz, 0.5), percentile(mv, 0.5) if mv else float("nan"),
                   percentile(lm, 0.5) if lm else float("nan")))

    if a.json:
        json.dump({
            "source": a.path,
            "ref": m["ref"],
            "flat_threshold": a.flat_threshold,
            "runs": rs,
            "per_frame": {
                str(f): {
                    "v": round(m["v"].get(f, 0.0), 5),
                    "a": round(m["acc"].get(f, 0.0), 5),
                    "pan": round(m["pan"].get(f, 0.0), 6),
                    "pan_acc": round(m["pan_acc"].get(f, 0.0), 6),
                    "zoom": round(m["zoom"].get(f, 0.0), 6),
                    "G": round(m["G"].get(f, 0.0), 5),
                } for f in m["common"]
            },
        }, open(a.json, "w"), indent=0)
        print(f">> wrote {a.json}")

    print(">> STAGE RESULT: CAMERA_TEMPO_MEASURED")


if __name__ == "__main__":
    main()
