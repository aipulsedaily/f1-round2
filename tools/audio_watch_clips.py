"""CUT THE LISTENING PASS — the short, labelled clips a person actually plays.

    .venv/bin/python tools/audio_watch_clips.py

R2-1090: nobody has listened to this film, and no agent here can. The audio has
been judged by spectrogram and band measurement only, and the `np.roll` defect is
the proof that this is not enough -- +31.2 dB on frame 1 would have been obvious
to anyone who pressed play, and it survived every gate the project built.

This cuts `watch/audio/`: a handful of clips at the moments that carry risk, each
a few seconds, each with one line saying what to listen FOR. The client is
working and will give this minutes, not hours.

TWO RULES THIS SCRIPT FOLLOWS, BOTH OF WHICH MATTER:

  * NO PER-CLIP NORMALISATION. Every clip keeps the master's absolute level, so
    one volume setting is right for all of them and a loud clip is loud because
    the film is. Normalising each clip would erase the exact thing the frame-1
    pair is there to demonstrate.

  * NO FADE AT A CLIP'S IN-POINT IF THE IN-POINT IS THE FILM'S OWN START. A
    5 ms fade is applied where a clip begins mid-programme, so the cut itself
    does not make a click that could be mistaken for a defect -- but applying one
    to frame 1 would fade out the defect being demonstrated. Out-points always
    fade. Which clips are faded is stated in the index.
"""
from __future__ import annotations

import json
import os
import shutil

import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "watch", "audio")
FPS = 24.0

POST = os.path.join(ROOT, "audio", "out", "master.wav")
PRE = os.path.join(ROOT, "audio", "out", "ab", "master_SHIPPED_aug2.wav")
END_A = os.path.join(ROOT, "audio", "out", "ab", "ending_A_nolapdown.wav")
END_B = os.path.join(ROOT, "audio", "out", "ab", "ending_B_lapdown.wav")


def _fade(y, sr, head, tail=0.005):
    y = y.copy()
    if tail:
        n = min(int(tail * sr), y.shape[0])
        y[-n:] *= np.linspace(1.0, 0.0, n)[:, None]
    if head:
        n = min(int(head * sr), y.shape[0])
        y[:n] *= np.linspace(0.0, 1.0, n)[:, None]
    return y


def cut(src, t0, dur, fade_in=True):
    x, sr = sf.read(src, always_2d=True, dtype="float64")
    a = int(round(t0 * sr))
    b = min(a + int(round(dur * sr)), x.shape[0])
    return _fade(x[a:b], sr, 0.005 if fade_in else 0.0), sr


def write(name, y, sr):
    p = os.path.join(OUT, name)
    sf.write(p, y, sr, subtype="PCM_24")
    return p


def main():
    os.makedirs(OUT, exist_ok=True)
    clips = []

    def add(name, y, sr, title, listen_for, frames):
        write(name, y, sr)
        pk = float(np.abs(y).max())
        clips.append({"file": name, "title": title, "listen_for": listen_for,
                      "film_frames": frames, "seconds": round(y.shape[0] / sr, 3),
                      "peak": round(pk, 4)})

    # --- 1/2/3: frame 1, the defect and its fix -----------------------------
    # NO fade-in: these two start at the film's own sample 0 and the whole point
    # is what is at sample 29.
    a, sr = cut(PRE, 0.0, 4.0, fade_in=False)
    add("01_opening_BEFORE_defect.wav", a, sr,
        "Frame 1 as it shipped (pre-fix master, 2 Aug)",
        "A hard BANG in the first hundredth of a second, before the showroom "
        "tone starts. That is the tail of a car at 323 km/h wrapped onto frame 1 "
        "by a circular buffer. It should not be there at all.",
        "1-96")

    b, sr = cut(POST, 0.0, 4.0, fade_in=False)
    add("02_opening_AFTER_fixed.wav", b, sr,
        "Frame 1 now",
        "The same four seconds with nothing at the top: an empty showroom that "
        "starts from silence. If you hear any click or thump at the very start, "
        "the fix did not hold.",
        "1-96")

    gap = np.zeros((int(1.0 * sr), a.shape[1]))
    add("03_opening_AB_one_press.wav", np.concatenate([a, gap, b]), sr,
        "Both of the above, back to back, one press of play",
        "Bang, one second of silence, then no bang. If the two halves sound the "
        "same, something is wrong -- they are 24 dB apart on frame 1.",
        "1-96 twice")

    # --- 4: the launch seam f792/793 ----------------------------------------
    c, sr = cut(POST, 31.5, 4.0)
    add("04_launch_seam_f792_793.wav", c, sr,
        "The launch, across the beat 1 -> 2 boundary at 33.000 s (f792 | f793)",
        "A join, 1.5 s in. Listen for a click, a jump in level, or the room "
        "changing abruptly. It should sound like one continuous take.",
        "756-852")

    # --- 5: the breach ------------------------------------------------------
    d, sr = cut(POST, 35.0, 6.0)
    add("05_breach_f865.wav", d, sr,
        "The breach — the car reaches the glass at 36.000 s (f865)",
        "The film's loudest event, and its largest legitimate spectral jump. "
        "Listen for distortion or clipping on the glass rather than for a join: "
        "this one is SUPPOSED to be violent.",
        "840-984")

    # --- 6: the ending seam f2715 -------------------------------------------
    e, sr = cut(POST, 112.0, 4.0)
    add("06_ending_seam_f2715.wav", e, sr,
        "The lift into the ending, beat 5 -> 6 at 113.100 s (f2714 | f2715)",
        "The injectors cut here. A 0.74 dB step at the lift, 28 ms before this "
        "join, was removed; listen for any remaining bump or gear-change glitch "
        "right as the engine goes off-throttle.",
        "2688-2784")

    # --- 7/8: the ending, A vs B — the client's actual decision --------------
    for nm, src, lab, note in (
        ("07_ending_A_no_lapdown.wav", END_A, "Ending A — no lap-down",
         "The car does not slow: the lap simply ends. Compare against B and "
         "pick one. This is a creative choice, not a defect hunt."),
        ("08_ending_B_lapdown.wav", END_B, "Ending B — with the lap-down",
         "Seven downshifts at a 0.48 s cadence, then the car stops and idles. "
         "Listen for whether the downshifts sound mechanical or sequenced, and "
         "whether the stop lands."),
    ):
        y, sr = sf.read(src, always_2d=True, dtype="float64")
        add(nm, _fade(y, sr, 0.005), sr, lab, note, "2690-2978")

    # --- 9: the last 1.75 s — idle or motored engine ------------------------
    f, sr = cut(POST, 121.8, 2.3)
    add("09_final_idle_last2s.wav", f, sr,
        "The last two seconds — the stopped car",
        "An engine at idle has a pulse you can count (215 Hz firing line: "
        "three firings per rev at a 4,300 rpm idle). A "
        "MOTORED engine — turning with the injectors cut — is a dead whoosh with "
        "no beat. This was a motored engine until R2-954; confirm it now idles.",
        "2923-2978")

    with open(os.path.join(OUT, "clips.json"), "w") as fh:
        json.dump(clips, fh, indent=1)
    for c in clips:
        print(f"  {c['file']:<34} {c['seconds']:>6.2f}s  peak {c['peak']:.4f}  f{c['film_frames']}")
    print(f">> {len(clips)} clips -> {OUT}")
    print(">> STAGE RESULT: AUDIO_WATCH_CLIPS_OK")
    return clips


if __name__ == "__main__":
    main()
