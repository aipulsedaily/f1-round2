"""Diff two per-frame camera paths. Where did the camera actually move?

    python3 work/r2100/path_diff.py OLD_path.json NEW_path.json [beat_sheet.json]

`film11_path.json` and `film12_path.json` are written by the rig build itself,
one row per frame, so this compares the camera as BUILT rather than the sheet
as authored. Reports the per-frame position delta, the rotation delta as an
angle, and the lens delta, and locates the worst of each -- and bins them by
beat when the sheet is given, because "the camera moved" is not a finding
until it says WHICH BEAT moved.

THE ROTATION COLUMN HAS A FLOOR OF ABOUT 0.16 deg AND IT IS THIS SCRIPT'S, NOT
THE CAMERA'S.  The path JSON stores quaternion components rounded to 6 decimal
places, and `angle = 2*acos(|dot|)` AMPLIFIES that by a square root near
dot = 1: a 1e-6 error in the dot product reads as 0.162 deg.  Measured floors,
0.115 / 0.162 / 0.229 deg for dot errors of 5e-7 / 1e-6 / 2e-6.  So a beat
reporting `dp 0.000000 m, dq 0.18 deg` HAS NOT MOVED -- and the same 0.15-0.20
band shows up between film10 and film11 in beats the fix provably did not
touch, which is the empirical half of the same claim.  Read the position
column first; treat rotation under ~0.25 deg as silence.
"""
import json
import math
import sys

a = json.load(open(sys.argv[1]))
b = json.load(open(sys.argv[2]))
sheet = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else None

A = {r["f"]: r for r in a["path"]}
B = {r["f"]: r for r in b["path"]}
common = sorted(set(A) & set(B))
print("frames  old %d  new %d  common %d  only-old %d  only-new %d"
      % (len(A), len(B), len(common), len(set(A) - set(B)), len(set(B) - set(A))))

beats = {}
if sheet:
    fps = float(sheet.get("fps", 24))
    for bt in sheet.get("beats", []):
        lo = int(round(bt["start_s"] * fps)) + 1
        hi = int(round((bt["start_s"] + bt["duration_s"]) * fps))
        beats[bt["name"]] = (lo, hi)
    for k, v in sheet.items():
        if not isinstance(v, dict):
            continue
        fr = v.get("frames") or v.get("frame_range")
        if isinstance(fr, (list, tuple)) and len(fr) == 2:
            beats[k] = (int(fr[0]), int(fr[1]))


def beat_of(f):
    for k, (lo, hi) in beats.items():
        if lo <= f <= hi:
            return k
    return "?"


rows = []
for f in common:
    p, q = A[f]["p"], A[f]["q"]
    p2, q2 = B[f]["p"], B[f]["q"]
    dp = math.dist(p, p2)
    dot = abs(sum(x * y for x, y in zip(q, q2)))
    dot = max(-1.0, min(1.0, dot))
    dq = math.degrees(2.0 * math.acos(dot))
    dl = abs(A[f].get("lens", 0) - B[f].get("lens", 0))
    rows.append((f, dp, dq, dl))

moved = [r for r in rows if r[1] > 1e-6 or r[2] > 1e-4 or r[3] > 1e-6]
print("frames that MOVED at all: %d of %d (%.2f %%)"
      % (len(moved), len(rows), 100.0 * len(moved) / max(1, len(rows))))
for idx, name, unit in ((1, "position", "m"), (2, "rotation", "deg"),
                        (3, "lens", "mm")):
    w = max(rows, key=lambda r: r[idx])
    tot = sum(r[idx] for r in rows)
    print("  worst %-8s %12.6f %-4s at frame %5d (%s)   mean %.6f"
          % (name, w[idx], unit, w[0], beat_of(w[0]), tot / max(1, len(rows))))

if beats:
    print("  per beat (frames moved / frames, worst position):")
    for k, (lo, hi) in sorted(beats.items(), key=lambda kv: kv[1][0]):
        sub = [r for r in rows if lo <= r[0] <= hi]
        if not sub:
            continue
        mv = [r for r in sub if r[1] > 1e-6 or r[2] > 1e-4 or r[3] > 1e-6]
        print("    %-12s %5d-%5d  moved %5d/%5d  worst dp %10.6f m  dq %8.4f deg"
              % (k, lo, hi, len(mv), len(sub),
                 max(r[1] for r in sub), max(r[2] for r in sub)))
print("STAGE RESULT: %s"
      % ("CAMERA_PATH_IDENTICAL" if not moved else "CAMERA_PATH_MOVED"))
