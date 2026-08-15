#!/usr/bin/env python
"""R2-4152 -- RE-CUT THE LISTENING PASS. NEW = R2-4152, OLD = R2-4147.

    .venv/bin/python -m tools.r2_4152_listen_clips --new WAV --old WAV

Same two in-points, same picture, same two rules as `tools/r2_4141_listen_clips`
-- which this imports rather than copies, so the cut command and the "no
per-clip normalisation" rule cannot drift:

  * NO PER-CLIP NORMALISATION. Both masters are -23.0 LUFS integrated, so the
    A/B is a comparison of CONTENT and not of gain.
  * THE PICTURE IS THE SAME IN BOTH ARMS and nothing here re-renders a frame.

WHAT IS DIFFERENT IS WHAT THE ARMS ARE AND WHAT TO LISTEN FOR. R2-4141's cut
pointed the A/B at the client's beat-1 complaint, which is closed. **This one is
pointed at the breach**, because that is the beat this pass changed and the only
beat it changed: the glass rebuilt on the laminate's own loss factor and the
picture's own fragment population, and the power unit no longer delivering 6.5
times the world's energy across eight seconds of screen.
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.r2_4141_listen_clips import FILM, cut, sha16              # noqa: E402

CLIPS = (
    ("beat1_showroom_34s", 0.0, 34.0,
     "BEAT 1, THE CONTROL ARM. This pass did not touch beat 1 and this clip is "
     "here to prove it: the two arms differ by a pure programme gain and "
     "nothing else, measured on the delivered masters. If you can hear a "
     "difference here, something is wrong. The assembly cell is R2-4147's, "
     "unchanged."),
    ("breach_glass_14s", 34.0, 14.0,
     "THE BREACH, WHICH IS WHAT THIS PASS IS. Three things changed and all "
     "three are in these fourteen seconds. (1) THE GLASS IS LAMINATED: the "
     "showroom's glazing is 5 mm / 1.5 mm PVB / 5 mm and the audio had been "
     "ringing every fragment of it at a loss factor BELOW monolithic float "
     "glass -- 995 contacts a second each ringing for 0.6 s, which is a wash "
     "and not a shatter. Listen for INDIVIDUAL PIECES: distinct arrivals, a "
     "top end, pieces you can count rather than a hiss. (2) THE FRAGMENTS ARE "
     "NOW THE PICTURE'S OWN: 3,216 shards read out of the same fracture the "
     "4K frames were rendered from, median 21 mm, against the 351 pieces of "
     "median 321 mm the audio had been inventing. (3) THE ENGINE STOPS "
     "OUTWEIGHING WHAT IT IS DESTROYING: the shot is 1.6 seconds of world over "
     "8 seconds of screen, and the power unit had been delivering all eight "
     "seconds' worth of energy while the glass delivered the world's 1.6. It "
     "was 45 % of this beat. Listen for the GLASS to be the event and the car "
     "to be behind it."),
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", required=True)
    ap.add_argument("--old", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "watch",
                                                  "listen_2026-08-14"))
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    man = {"film": os.path.basename(FILM), "film_sha16": sha16(FILM),
           "NEW_wav": os.path.relpath(a.new, ROOT), "NEW_sha16": sha16(a.new),
           "OLD_wav": os.path.relpath(a.old, ROOT), "OLD_sha16": sha16(a.old),
           "clips": []}
    for name, t0, dur, note in CLIPS:
        for tag, wav in (("NEW", a.new), ("OLD", a.old)):
            p = cut(a.out, tag, wav, name, t0, dur, dry=a.dry)
            man["clips"].append({"file": os.path.basename(p), "t0_s": t0,
                                 "dur_s": dur, "arm": tag, "listen_for": note})
    man["what_this_ab_is"] = (
        "NEW is R2-4152, the master the films now carry; OLD is R2-4147, the "
        "one they carried before. Both are -23.00 LUFS integrated and neither "
        "clip is normalised, so this is a comparison of CONTENT. Beat 1 is the "
        "control arm and is unchanged by construction; the breach is the pass.")
    if not a.dry:
        json.dump(man, open(os.path.join(a.out, "CLIPS_OF.json"), "w"), indent=1)
    print(json.dumps(man, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
