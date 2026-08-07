#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2731_lens_retune_rebase.py — REBASE R2-581's LENS RETUNE ONTO THE LIVE PATH.

    python3 tools/r2731_lens_retune_rebase.py --selftest
    python3 tools/r2731_lens_retune_rebase.py \
        --out render/film_path_R2581B_ramp_RETUNED_REBASED.json

WHY
---
R2-737.  `render/film14_path_R2581B_ramp_RETUNED_CANDIDATE.json` says of itself
"Lens only; p and q identical to film14_path.json".  Both halves are true and
the second is the trap: `film14_path.json` is NOT the path in the film.  It
differs from the live `world/camera_rig_path.json` by **8.863 m of position and
1.687 of quaternion, all of it in beat 1**, which another agent has just spent a
day rebuilding.

    candidate vs film14_path      max |dp| 0.000000 m   max |dq| 0.00000000
    film14_path vs the LIVE rig   max |dp| 8.863000 m   max |dq| 1.68747700
        beat 1  f1-792            max |dp| 8.863 m
        beat 5  f1191-2714        max |dp| 0.000 m   (|dq| 1e-6, rounding)
        beat 6  f2715-2978        max |dp| 0.000 m   (|dq| 1e-6, rounding)

**Adopting the file wholesale would silently revert beat 1's camera.**  Its lens
curve is fine and is the thing R2-581 actually produced.

WHAT THIS WRITES
----------------
The LIVE path, position and rotation untouched, carrying ONLY the candidate's
`lens` over the frames where the candidate's lens actually differs from its own
base — measured as f1998-2243, inside its declared support f1997-2244.  Every
other frame keeps the live lens exactly.

This is still a CANDIDATE.  R2-737 also measured what the retune does to the
bridge blackout: it cannot change which frames are blocked (a sightline does not
know the focal length) but it lands its peak magnification on them — f2190 goes
84.83 mm -> 142.11 mm, **1.68x** — so the two decisions belong together.
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = "render/film14_path_R2581B_ramp_RETUNED_CANDIDATE.json"
BASE = "render/film14_path.json"
LIVE = "world/camera_rig_path.json"


def load(p):
    return {int(e["f"]): e for e in
            json.load(open(os.path.join(ROOT, p)))["path"]}


def rebase():
    cand, base, live = load(CAND), load(BASE), load(LIVE)
    out, moved = [], []
    for f in sorted(live):
        e = dict(live[f])
        if f in cand and f in base and abs(cand[f]["lens"] - base[f]["lens"]) > 1e-9:
            e["lens"] = cand[f]["lens"]
            moved.append(f)
        out.append(e)
    return out, moved, cand, base, live


def selftest():
    ok = True

    def chk(nm, cond, detail=""):
        nonlocal ok
        print("   %-50s %s  %s" % (nm, "PASS" if cond else "FAIL", detail))
        ok = ok and bool(cond)

    out, moved, cand, base, live = rebase()
    o = {int(e["f"]): e for e in out}
    chk("position is the LIVE path on every frame",
        all(o[f]["p"] == live[f]["p"] for f in live))
    chk("rotation is the LIVE path on every frame",
        all(o[f]["q"] == live[f]["q"] for f in live))
    dp = max(max(abs(base[f]["p"][i] - live[f]["p"][i]) for i in range(3))
             for f in live if f in base)
    chk("the trap this avoids is real and large", dp > 8.0,
        "film14 vs live: max |dp| = %.3f m" % dp)
    chk("beat 1 is bit-identical to the live path",
        all(o[f]["p"] == live[f]["p"] and o[f]["lens"] == live[f]["lens"]
            for f in range(1, 793)))
    chk("lens changes only inside the declared support",
        moved and 1997 <= min(moved) and max(moved) <= 2244,
        "f%d-%d, declared f1997-2244" % (min(moved), max(moved)))
    chk("lens outside the support is the live lens",
        all(o[f]["lens"] == live[f]["lens"] for f in live if f not in moved))
    chk("the retuned lens is what the candidate asked for",
        all(o[f]["lens"] == cand[f]["lens"] for f in moved))
    print(">> STAGE RESULT: %s"
          % ("LENS_REBASE_SELFTEST_OK" if ok else "LENS_REBASE_SELFTEST_FAIL"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out",
                    default="render/film_path_R2581B_ramp_RETUNED_REBASED.json")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    out, moved, cand, base, live = rebase()
    peak = max(((o["lens"] - live[int(o["f"])]["lens"]), int(o["f"]))
               for o in out if int(o["f"]) in moved)
    doc = dict(
        frames=len(out), path=out,
        note="R2-737 REBASE of %s. The candidate is lens-only against %s, which "
             "is NOT the live path: they differ by 8.863 m of position and 1.687 "
             "of quaternion, ALL of it in beat 1. This file is the LIVE path "
             "(%s) with position and rotation untouched, carrying only the "
             "candidate's lens over f%d-%d. Adopting the original file wholesale "
             "would have reverted beat 1's camera. STILL A CANDIDATE: the retune "
             "lands its peak magnification on the bridge blackout (f2190 goes "
             "84.83 -> 142.11 mm, 1.68x), so it and the beat-5 camera decision "
             "belong together."
             % (CAND, BASE, LIVE, min(moved), max(moved)),
        lens_frames_changed=[min(moved), max(moved)],
        lens_frames_n=len(moved),
        peak_lens_increase_mm=round(peak[0], 3), peak_at_frame=peak[1])
    with open(os.path.join(ROOT, a.out), "w") as fh:
        json.dump(doc, fh)
    print(">> rebased lens over f%d-%d (%d frames); peak +%.2f mm at f%d"
          % (min(moved), max(moved), len(moved), peak[0], peak[1]))
    print(">> wrote %s" % a.out)
    print(">> STAGE RESULT: LENS_REBASE_WRITTEN")


if __name__ == "__main__":
    main()
