"""VANTAGE REGIMES of the built camera rig -- the FRAME-peep count, derived.

    python3 tools/frame_peeps.py --path world/camera_rig_path.json \
        --sheet docs/beat_sheet.json --out work/tier2/frame_peeps.json

WHY THIS FILE EXISTS AT ALL
---------------------------
`docs/proposed_tiers.json` has, since 2026-08-02, asserted:

    "36 FRAME-peeps -- one per vantage regime MEASURED in the built rig
     (beat x speed-band x lens-band x altitude-band, >=24 frames each;
     36 of them covering 89% of the take)"

and **the script that produced it is not in the repository.**  It is not in
`tools/`, not in `work/`, not in `anim/`; the strings "FRAME-peep",
"frame_peep" and "agents_per_round" appear in exactly one file in the whole
project, which is the output itself.  So the 36 was, until this file, a
number nobody could re-derive, sitting in the plan that decides how many
adversarial reviewers a build round gets.

CAN THE ORIGINAL BE RECOVERED FROM ITS OWN SIGNATURE?  NO -- AND THAT WAS
TESTED RATHER THAN ASSUMED.  The old camera is recoverable (the `campos` and
`lens` arrays inside `docs/screen_presence_points.npz` are the exact per-frame
camera the 12:19 run used), so the binning could be searched for directly.
1,296 combinations of speed / lens / altitude band edges were swept against
that camera.  **Twelve of them land on exactly 36 regimes at 88-90 % coverage**
-- among them speed edges as unlike each other as [1, 10, 40, 80] m/s and
[2.78, 16.7, 55.6] m/s.  "36 regimes, 89 %" therefore does not identify a
binning.  Any band set reproducing it would be a coincidence dressed as a
recovery, so this file does NOT try to reproduce 36.  It states its own bands,
on stated grounds, and reports whatever they give.

THE ROUTE, WHICH IS THE POINT OF THIS FILE
------------------------------------------
A FRAME-peep judges one frame at the real camera, lens, distance and shutter.
Two frames need separate judging when what a reviewer would look at differs.
Four axes, each cut where the PERCEPTUAL class changes, not on round numbers:

  BEAT           the film's own six declared segments.  Different subject,
                 different intent, and the beat is what a reviewer is told
                 they are looking at.

  SPEED BAND     film-time speed of the camera body, m/s, cut at 1 / 10 / 30.
                 <1     the camera is effectively locked; the reviewer is
                        judging static detail and every flaw holds still.
                 1-10   walking to fast-jog; detail readable, edges softening.
                 10-30  road speed; silhouette and value survive, macro does not.
                 >=30   108 km/h and up -- beat 4 and 5's pace, where the
                        measured smear exceeds the 6 px sharp threshold for
                        anything close and only mass and tone are judgeable.
                 Speed is FILM time (position delta x 24 fps), because the
                 shutter is a flat 180 degrees of a FILM frame since R2-037 and
                 the smear a reviewer sees is a film-frame quantity.

  LENS BAND      cut at 28 / 50 / 85 mm, the photographic classes on this
                 rig's 36 mm horizontal sensor: wide, normal, short tele, tele.
                 These are the boundaries at which the relationship between
                 subject size and background compression visibly changes, and
                 they are not tuned to this film.

  ALTITUDE BAND  camera z, cut at 2 / 6 / 15 m.
                 <2     eye height -- the viewer reads it as standing there.
                 2-6    vehicle / low crane.
                 6-15   grandstand and gantry height.
                 >=15   aerial.
                 Absolute z, not height above terrain: the circuit's ground is
                 within about a metre of z=0 across the whole camera corridor,
                 and using absolute z keeps this tool free of any dependency on
                 the terrain build, which is owned by another agent and moves.

  MIN_FRAMES     24 (1.0 s).  A regime the camera passes through for under a
                 second is not a vantage anyone can review; its frames are
                 reported as UNCOVERED rather than silently folded into a
                 neighbour, so the coverage figure is honest.

The band edges are CLI arguments.  Changing them changes the answer and the
output records the edges used, so two runs can be compared.
"""
import os, sys, json, argparse

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 24.0

SPEED_EDGES = [1.0, 10.0, 30.0]
LENS_EDGES = [28.0, 50.0, 85.0]
ALT_EDGES = [2.0, 6.0, 15.0]
MIN_FRAMES = 24

SPEED_LAB = ["locked_lt1", "slow_1_10", "fast_10_30", "race_gte30"]
LENS_LAB = ["wide_lt28", "normal_28_50", "shorttele_50_85", "tele_gte85"]
ALT_LAB = ["eye_lt2", "low_2_6", "high_6_15", "aerial_gte15"]


def camera_from_path(path_json):
    d = json.load(open(path_json))
    p = d["path"]
    C = np.array([q["p"] for q in p], dtype=np.float64)
    lens = np.array([q["lens"] for q in p], dtype=np.float64)
    return C, lens


def camera_from_npz(npz):
    """The camera a PREVIOUS screen_presence run actually used.

    screen_presence.py stores `campos` and `lens` in its own output npz, which
    makes a historical run's camera recoverable even though no copy of the
    camera path from that date survives. That is the only reason the 36 could
    be tested at all.
    """
    z = np.load(npz, allow_pickle=True)
    return z["campos"].astype(np.float64), z["lens"].astype(np.float64)


def beats_of(sheet_json, n):
    sheet = json.load(open(sheet_json))
    lab = np.empty(n, dtype=object)
    lab[:] = "?"
    for b in sheet["beats"]:
        f0 = max(1, int(round(b["start_s"] * FPS)) + 1)
        f1 = min(n, int(round((b["start_s"] + b["duration_s"]) * FPS)))
        lab[f0 - 1:f1] = b["name"]
    return lab


def regimes(C, lens, beat, speed_edges, lens_edges, alt_edges, min_frames):
    n = len(C)
    spd = np.zeros(n)
    spd[:-1] = np.linalg.norm(np.diff(C, axis=0), axis=1) * FPS
    if n > 1:
        spd[-1] = spd[-2]
    alt = C[:, 2]
    sb = np.digitize(spd, speed_edges)
    lb = np.digitize(lens, lens_edges)
    ab = np.digitize(alt, alt_edges)

    cells = {}
    for i in range(n):
        k = (str(beat[i]), int(sb[i]), int(lb[i]), int(ab[i]))
        cells.setdefault(k, []).append(i + 1)
    rows = []
    for k, fr in cells.items():
        fr = np.array(fr)
        rows.append({
            "beat": k[0],
            "speed_band": SPEED_LAB[k[1]] if k[1] < len(SPEED_LAB) else str(k[1]),
            "lens_band": LENS_LAB[k[2]] if k[2] < len(LENS_LAB) else str(k[2]),
            "alt_band": ALT_LAB[k[3]] if k[3] < len(ALT_LAB) else str(k[3]),
            "frames": int(len(fr)),
            "frame_first": int(fr.min()), "frame_last": int(fr.max()),
            # the frame a reviewer should actually be handed: the MEDIAN frame
            # of the regime, so it is representative rather than a boundary
            # case that half belongs to the neighbouring regime.
            "representative_frame": int(np.median(fr)),
            "speed_ms": [round(float(spd[fr - 1].min()), 2), round(float(spd[fr - 1].max()), 2)],
            "lens_mm": [round(float(lens[fr - 1].min()), 2), round(float(lens[fr - 1].max()), 2)],
            "alt_m": [round(float(alt[fr - 1].min()), 2), round(float(alt[fr - 1].max()), 2)],
            "kept": bool(len(fr) >= min_frames),
        })
    rows.sort(key=lambda r: (-r["frames"], r["beat"]))
    kept = [r for r in rows if r["kept"]]
    cov = sum(r["frames"] for r in kept) / float(n)
    return rows, kept, cov, spd, alt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=os.path.join(R2, "world/camera_rig_path.json"))
    ap.add_argument("--from-npz", default="",
                    help="recover the camera from a previous screen_presence npz "
                         "(campos/lens) instead of a path json -- how a historical "
                         "run's camera is re-measured")
    ap.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--speed-edges", default=",".join(str(x) for x in SPEED_EDGES))
    ap.add_argument("--lens-edges", default=",".join(str(x) for x in LENS_EDGES))
    ap.add_argument("--alt-edges", default=",".join(str(x) for x in ALT_EDGES))
    ap.add_argument("--min-frames", type=int, default=MIN_FRAMES)
    a = ap.parse_args()

    if a.from_npz:
        C, lens = camera_from_npz(a.from_npz)
        src = os.path.abspath(a.from_npz) + " (campos/lens of a previous run)"
    else:
        C, lens = camera_from_path(a.path)
        src = os.path.abspath(a.path)
    beat = beats_of(a.sheet, len(C))
    se = [float(x) for x in a.speed_edges.split(",")]
    le = [float(x) for x in a.lens_edges.split(",")]
    ae = [float(x) for x in a.alt_edges.split(",")]
    rows, kept, cov, spd, alt = regimes(C, lens, beat, se, le, ae, a.min_frames)

    out = {
        "generated": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
        "camera_source": src,
        "beat_sheet": os.path.abspath(a.sheet),
        "frames": len(C),
        "bands": {"speed_ms_edges": se, "lens_mm_edges": le, "alt_m_edges": ae,
                  "min_frames": a.min_frames},
        "FRAME_PEEPS": len(kept),
        "regimes_total": len(rows),
        "coverage_pct": round(100.0 * cov, 1),
        "uncovered_frames": int(len(C) - sum(r["frames"] for r in kept)),
        "ROUTE": __doc__,
        "regimes": rows,
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print("[FP] camera %s" % src)
    print("[FP] %d regimes total, %d with >=%d frames -> FRAME_PEEPS = %d, "
          "covering %.1f %% of %d frames"
          % (len(rows), len(kept), a.min_frames, len(kept), 100 * cov, len(C)))
    for r in kept:
        print("   %-11s %-11s %-16s %-12s %5d fr  rep f%-5d"
              % (r["beat"], r["speed_band"], r["lens_band"], r["alt_band"],
                 r["frames"], r["representative_frame"]))
    print("[FP] wrote " + a.out)


if __name__ == "__main__":
    main()
