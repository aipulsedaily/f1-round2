#!/usr/bin/env python
"""R2-4141 -- CUT THE LISTENING PASS, from the films and the two masters.

Two clips, at the two moments the client has actually commented on:

    beat1_showroom_34s   film t 0.000 - 34.000 s   the assembly cell
    breach_glass_14s     film t 34.000 - 48.000 s  the launch and the glass

The in-points are not guessed. They were recovered by cross-correlating the
2026-08-14 clips against `audio/out/master.wav` at 8 kHz: the breach clip
matches at t = 34.0000 s with r = 0.9996 and the beat-1 clip at t = 0.0000 s
with r = 0.9993, so the new pass is frame-aligned with the old one and an A/B
between the two dates is a comparison of audio only.

TWO RULES, BOTH INHERITED FROM `tools/audio_watch_clips.py` AND BOTH LOAD-BEARING:

  * NO PER-CLIP NORMALISATION. Every clip keeps its master's absolute level, so
    one volume setting is right for all four and a loud clip is loud because the
    film is. The two masters are both -23.0 LUFS integrated, so the A/B is a
    comparison of CONTENT and not of gain.
  * THE PICTURE IS THE SAME IN BOTH ARMS, and it is the delivered H.265 scaled
    to 720p. Nothing here re-renders a frame.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILM = os.path.join(ROOT, "watch", "PART2_THE_FILM_4K_h265.mp4")
CLIPS = (("beat1_showroom_34s", 0.0, 34.0,
          "the showroom assembly cell -- listen for a MACHINE: contacts, "
          "valves, moves that start and stop. Nothing should hold a pitch."),
         ("breach_glass_14s", 34.0, 14.0,
          "the launch and the glass wall."))


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def cut(out_dir, tag, wav, name, t0, dur, dry=False):
    out = os.path.join(out_dir, "%s_%s.mp4" % (tag, name))
    cmd = ["ffmpeg", "-v", "error", "-y",
           "-ss", "%.6f" % t0, "-i", FILM,
           "-ss", "%.6f" % t0, "-i", wav,
           "-t", "%.6f" % dur,
           "-map", "0:v:0", "-map", "1:a:0",
           "-vf", "scale=1280:720",
           "-c:v", "libx264", "-preset", "slow", "-b:v", "2000k",
           "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", out]
    print(" ".join(cmd), flush=True)
    if not dry:
        subprocess.run(cmd, check=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", required=True, help="the candidate master wav")
    ap.add_argument("--old", default=os.path.join(ROOT, "audio", "out",
                                                  "master.wav"),
                    help="the master the films currently carry")
    ap.add_argument("--out", default=os.path.join(ROOT, "watch",
                                                  "listen_2026-08-14"))
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    man = {"film": os.path.basename(FILM), "film_sha16": sha16(FILM),
           "NEW_wav": os.path.relpath(a.new, ROOT),
           "NEW_sha16": sha16(a.new),
           "OLD_wav": os.path.relpath(a.old, ROOT),
           "OLD_sha16": sha16(a.old),
           "clips": []}
    for name, t0, dur, note in CLIPS:
        for tag, wav in (("NEW", a.new), ("OLD", a.old)):
            p = cut(a.out, tag, wav, name, t0, dur, dry=a.dry)
            man["clips"].append({"file": os.path.basename(p), "t0_s": t0,
                                 "dur_s": dur, "arm": tag, "listen_for": note})
    mp = os.path.join(a.out, "CLIPS_OF.json")
    if not a.dry:
        json.dump(man, open(mp, "w"), indent=1)
    print(json.dumps(man, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
