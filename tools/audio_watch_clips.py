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

import hashlib
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
# the master the client rejected as a hair blower, kept for the R2-1401 A/B
HAIR = os.path.join(ROOT, "audio", "out", "ab",
                    "master_R2-1400_REJECTED_hairblower.wav")
# THESE MUST BE THE NAMES `tools/audio_ending_ab.py` ACTUALLY WRITES (R2-2010).
# They used to read `ending_A_nolapdown.wav` / `ending_B_lapdown.wav`, which that
# tool has not written for some time -- it emits `ending_A.wav` / `ending_B.wav`.
# So clips 07 and 08 were being cut from orphaned files that no pipeline step
# updates: dated 7 Aug 17:59 while the master they were supposed to represent had
# been rebuilt twice since. Exactly the R2-1981 defect, one directory deeper, and
# it is why "re-cut the clips" was not on its own enough to make the page honest.
END_A = os.path.join(ROOT, "audio", "out", "ab", "ending_A.wav")
END_B = os.path.join(ROOT, "audio", "out", "ab", "ending_B.wav")

# WHERE THE COMPLAINT IS LOUDEST, CHOSEN BY MEASUREMENT (R2-1401).
#
# Scored every 6 s window of the REJECTED master on "loud AND noise-dominated"
# -- short-term level minus three times the median harmonic-to-noise ratio above
# 2.6 kHz -- so the window is picked by the defect rather than by anyone's taste.
# The worst in the film is 83.0 s (HNR 2.96 dB, HNR>2.6 kHz -1.21 dB, at -13.2 dB
# short-term). The launch is the second place the client is most likely to have
# formed the impression, because it is the closest and driest the engine ever is.
AB_LAP_T0, AB_LAP_DUR = 83.0, 6.0
AB_LAUNCH_T0, AB_LAUNCH_DUR = 33.0, 6.0

# The master the client rejected as "a wind machine with someone banging on
# tubes", kept for the R2-2001 A/B.
#
# READ THIS BEFORE TRUSTING IT. The exact B-variant the client was played was
# `master_B_lapdown.wav`, and it was DESTROYED during this work -- overwritten by
# the new render, and `*.wav` is gitignored, so there is no other copy. What is
# archived here instead is `master_A_nolapdown.wav` from the same 17:59 render of
# the same code, renamed. A and B are the same film until 113.1 s and differ only
# in the ending, but they are NOT bit-identical even before then, because
# master.py's whole-film gain staging (per-bus LUFS trims, the -14 LUFS
# normalisation, the limiter) is a function of the ending.
#
# Measured over the 6 s A/B window at 73.5 s, against the clip that WAS cut from
# the true B before it was lost: best-fit broadband gain 0.99926553, i.e.
# -0.0064 dB, with a residual 68.9 dB below the signal. Inaudible, and nothing
# about the ringing this A/B demonstrates is carried in it. Honest, but a
# substitute -- do not describe it to the client as the exact file they played.
TUBES = os.path.join(ROOT, "audio", "out", "ab",
                     "master_R2-2001_REJECTED_tubes.wav")

# WHERE THE BANGING IS MOST EXPOSED, CHOSEN BY MEASUREMENT (R2-2001).
#
# The score here is not the R2-1401 one, because the defect is in the ENVELOPE
# rather than the spectrum. Every 6 s window was scored on how much of its energy
# sits in 2-6 kHz plus how deeply that band's envelope swings (p90/p10, in dB).
#
# READ THAT SCORE CORRECTLY -- it is a measure of EXPOSURE, not of the defect.
# A long ring FILLS the gaps between firings, so if anything it SMOOTHS the
# envelope; deep swings mean the individual events are cleanly separated and
# therefore clearly audible. So this picks the window where each firing and its
# tail can be heard as its own event, which is where a wrong tail is easiest to
# judge -- it does not, on its own, say the tail is wrong. What says that is the
# decay measurement in R2-2001 and the tail measurement quoted in the cue below.
#
# The worst window in the film is 42.5 s at a score of 12.6 (envelope swing
# 27.7 dB against a film-wide mean of 12.1). IT IS NOT USED: 42.5-48.5 s straddles
# the 3_breach/4_transit boundary at 44.0 s, so half of it is breaking glass and
# the comparison would be confounded. 73.5 s is the worst window lying wholly
# inside 5_lap -- score 8.8, envelope swing 19.8 dB, 2-6 kHz at -11.0 dB
# relative -- and it is pure engine.
AB_TUBES_T0, AB_TUBES_DUR = 73.5, 6.0


def _fade(y, sr, head, tail=0.005):
    y = y.copy()
    if tail:
        n = min(int(tail * sr), y.shape[0])
        y[-n:] *= np.linspace(1.0, 0.0, n)[:, None]
    if head:
        n = min(int(head * sr), y.shape[0])
        y[:n] *= np.linspace(0.0, 1.0, n)[:, None]
    return y


# ================= PROVENANCE, PROVED BY THE CUTTER, NOT BY AN AUDIT ==========
# R2-2226. Clips 07 and 08 were cut for weeks from files no tool had written
# (R2-2010), and the reason that survived is that nothing here ever CHECKED where
# a clip came from -- the cutter wrote whatever the constant at the top of the
# file pointed at, and `clips.json` recorded a title and a peak. Re-running the
# cutter could not have fixed it and did not.
#
# So every clip now carries its source path, that source's md5, and the exact
# sample range taken from it; and before `clips.json` is written the cutter reads
# each clip back off disk and compares its un-faded interior against the source,
# sample for sample. `SOURCE_MUST_BE_MASTER` names the clips that are claims about
# the delivered film rather than about a kept artefact, and any one of those that
# is not bit-exact against `audio/out/master.wav` stops the run.
#
# 07 IS THE ONE HONEST EXCEPTION AND IT IS NAMED AS ONE. Ending A is a different
# render by construction -- that is the decision the client is being asked to make
# -- so it comes from `master_A_nolapdown.wav` and says so in the index. It was
# not saying so before.
def md5(path, _c={}):
    if path not in _c:
        h = hashlib.md5()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        _c[path] = h.hexdigest()
    return _c[path]


SOURCE_MUST_BE_MASTER = (
    "02_opening_AFTER_fixed.wav", "04_launch_seam_f792_793.wav",
    "05_breach_f865.wav", "06_ending_seam_f2715.wav",
    "08_ending_B_lapdown.wav", "09_final_idle_last2s.wav",
    "11_lap_AFTER_rebuilt.wav", "13_launch_AFTER_rebuilt.wav",
    "17_lap_AFTER_damped.wav",
)


def cut(src, t0, dur, fade_in=True):
    x, sr = sf.read(src, always_2d=True, dtype="float64")
    a = int(round(t0 * sr))
    b = min(a + int(round(dur * sr)), x.shape[0])
    y = _fade(x[a:b], sr, 0.005 if fade_in else 0.0)
    return y, sr, [{"path": src, "md5": md5(src), "from": a, "to": b,
                    "clip_offset": 0, "faded_in": bool(fade_in)}]


def frames_str(t0, dur, sr, n):
    """1-based inclusive film frames, from the samples actually taken.

    Four of these were hardcoded and four of those started a frame early, so
    `clips.json` claimed 97 frames where the clip carried 96. Derived now.
    """
    return "%d-%d" % (int(round(t0 * sr)) // int(round(sr / FPS)) + 1,
                      (int(round(t0 * sr)) + n - 1) // int(round(sr / FPS)) + 1)


def write(name, y, sr):
    p = os.path.join(OUT, name)
    sf.write(p, y, sr, subtype="PCM_24")
    return p


def _is_master_tail(src_audio, a, b, skip, _m={}):
    """Is `src_audio[a:b]` bit-identical to the delivered master's own tail?

    The ending extracts run to the last sample of the film, so the alignment is
    determined -- the master's tail of the same length -- and no search or
    tolerance is involved: it matches sample for sample or it does not.

    `skip` drops `audio_ending_ab.py`'s OWN 5 ms in-ramp at each end, which is the
    only part of those files that is not the master. That ramp is also why the
    cutter no longer adds a second one (see clips 07/08 below).
    """
    if "x" not in _m:
        _m["x"], _m["sr"] = sf.read(POST, always_2d=True, dtype="float64")
    off = _m["x"].shape[0] - src_audio.shape[0] + a
    if off < 0 or off + (b - a) > _m["x"].shape[0]:
        return False
    return bool(np.array_equal(src_audio[a + skip:b - skip],
                               _m["x"][off + skip:off + (b - a) - skip]))


def main():
    os.makedirs(OUT, exist_ok=True)
    clips = []
    prov_fail = []

    def add(name, y, sr, title, listen_for, frames, src=None):
        p = write(name, y, sr)
        pk = float(np.abs(y).max())
        rec = {"file": name, "title": title, "listen_for": listen_for,
               "film_frames": frames, "seconds": round(y.shape[0] / sr, 3),
               "peak": round(pk, 4), "sources": src or []}
        # read back and compare the interior against the source, bit for bit
        if src:
            back, _ = sf.read(p, always_2d=True, dtype="float64")
            nf, ok = int(0.005 * sr), []
            for s in src:
                x, _ = sf.read(s["path"], always_2d=True, dtype="float64")
                seg = x[s["from"]:s["to"]]
                o = s["clip_offset"]
                got = back[o:o + seg.shape[0]]
                # skip the 5 ms ramps: the head ramp only where one was applied,
                # the tail ramp always -- `_fade` ramps the last 5 ms of every
                # segment, including the one before a gap
                h = nf if s["faded_in"] else 0
                d = (float(np.abs(got[h:seg.shape[0] - nf]
                                  - seg[h:seg.shape[0] - nf]).max())
                     if seg.shape[0] > h + nf else 0.0)
                ok.append(d == 0.0)
                s["interior_max_abs_diff"] = d
                if name in SOURCE_MUST_BE_MASTER and s["path"] != POST:
                    # A source that is not the master itself is allowed only if
                    # it IS the master over the samples taken -- clip 08 comes
                    # from `ending_B.wav`, which `audio_ending_ab.py` cuts from
                    # the B render, and B IS the delivered film. That has to be
                    # PROVED here rather than assumed, because this is exactly
                    # the shape of the R2-2010 defect: an intermediate file that
                    # used to be the master and quietly stopped being it.
                    s["equals_master"] = _is_master_tail(x, s["from"], s["to"], nf)
                    if not s["equals_master"]:
                        prov_fail.append(
                            "%s claims the delivered master, its source is %s, "
                            "and that file is NOT the master over the samples "
                            "taken" % (name, os.path.basename(s["path"])))
            rec["bit_exact_against_source"] = all(ok)
            rec["is_delivered_master"] = all(s["path"] == POST
                                             or s.get("equals_master")
                                             for s in src)
            if not all(ok):
                prov_fail.append(
                    "%s is not bit-exact against its source (worst %.3e)"
                    % (name, max(s["interior_max_abs_diff"] for s in src)))
        clips.append(rec)

    # --- 1/2/3: frame 1, the defect and its fix -----------------------------
    # NO fade-in: these two start at the film's own sample 0 and the whole point
    # is what is at sample 29.
    a, sr, pa = cut(PRE, 0.0, 4.0, fade_in=False)
    add("01_opening_BEFORE_defect.wav", a, sr,
        "Frame 1 as it shipped (pre-fix master, 2 Aug)",
        "A hard BANG in the first hundredth of a second, before the showroom "
        "tone starts. That is the tail of a car at 323 km/h wrapped onto frame 1 "
        "by a circular buffer. It should not be there at all.",
        frames_str(0.0, 4.0, sr, a.shape[0]), pa)

    b, sr, pb = cut(POST, 0.0, 4.0, fade_in=False)
    add("02_opening_AFTER_fixed.wav", b, sr,
        "Frame 1 now",
        "The same four seconds with nothing at the top: an empty showroom that "
        "starts from silence. If you hear any click or thump at the very start, "
        "the fix did not hold.",
        frames_str(0.0, 4.0, sr, b.shape[0]), pb)

    gap = np.zeros((int(1.0 * sr), a.shape[1]))
    add("03_opening_AB_one_press.wav", np.concatenate([a, gap, b]), sr,
        "Both of the above, back to back, one press of play",
        "Bang, one second of silence, then no bang. If the two halves sound the "
        "same, something is wrong -- they are 24 dB apart on frame 1.",
        frames_str(0.0, 4.0, sr, a.shape[0]) + " twice",
        pa + [dict(pb[0], clip_offset=a.shape[0] + gap.shape[0])])

    # --- 4: the launch seam f792/793 ----------------------------------------
    c, sr, pc = cut(POST, 31.5, 4.0)
    add("04_launch_seam_f792_793.wav", c, sr,
        "The launch, across the beat 1 -> 2 boundary at 33.000 s (f792 | f793)",
        "A join, 1.5 s in. Listen for a click, a jump in level, or the room "
        "changing abruptly. It should sound like one continuous take.",
        frames_str(31.5, 4.0, sr, c.shape[0]), pc)

    # --- 5: the breach ------------------------------------------------------
    d, sr, pd = cut(POST, 35.0, 6.0)
    add("05_breach_f865.wav", d, sr,
        "The breach — the car reaches the glass at 36.000 s (f865)",
        "The film's loudest event, and its largest legitimate spectral jump. "
        "Listen for distortion or clipping on the glass rather than for a join: "
        "this one is SUPPOSED to be violent.",
        frames_str(35.0, 6.0, sr, d.shape[0]), pd)

    # --- 6: the ending seam f2715 -------------------------------------------
    e, sr, pe = cut(POST, 112.0, 4.0)
    add("06_ending_seam_f2715.wav", e, sr,
        "The lift into the ending, beat 5 -> 6 at 113.100 s (f2714 | f2715)",
        "The injectors cut here. A 0.74 dB step at the lift, 28 ms before this "
        "join, was removed; listen for any remaining bump or gear-change glitch "
        "right as the engine goes off-throttle.",
        frames_str(112.0, 4.0, sr, e.shape[0]), pe)

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
        # NO SECOND FADE (R2-2226). `audio_ending_ab.py` already writes these
        # with a 5 ms linear in-ramp; fading again made the first 240 samples
        # QUADRATIC, which is not what this file's own docstring says it does,
        # and it put 240 samples between the clip and the master that had no
        # reason to be there. Copied through as written.
        y, sr = sf.read(src, always_2d=True, dtype="float64")
        add(nm, y, sr, lab, note, "2690-2978",
            [{"path": src, "md5": md5(src), "from": 0, "to": y.shape[0],
              "clip_offset": 0, "faded_in": True}])

    # --- 9: the last 1.75 s — idle or motored engine ------------------------
    f, sr, pf = cut(POST, 121.8, 2.3)
    add("09_final_idle_last2s.wav", f, sr,
        "The last two seconds — the stopped car",
        "An engine at idle has a pulse you can count (215 Hz firing line: "
        "three firings per rev at a 4,300 rpm idle). A "
        "MOTORED engine — turning with the injectors cut — is a dead whoosh with "
        "no beat. This was a motored engine until R2-954; confirm it now idles.",
        frames_str(121.8, 2.3, sr, f.shape[0]), pf)

    # --- 10-13: R2-1401, the hair blower ------------------------------------
    # THE ONLY CLIPS ON THIS PAGE THAT MATTER TODAY. Both windows are cut from
    # the same film times in both masters, at the same absolute level, so the
    # only difference between a BEFORE and its AFTER is the synthesis.
    for tag, t0, dur, n0, where, cue in (
        ("lap", AB_LAP_T0, AB_LAP_DUR, 10,
         "the flying lap at 83 s — the worst 6 seconds in the film, found by "
         "measurement",
         "In BEFORE the car has no note: there is a rising and falling WHOOSH "
         "with a pitch somewhere inside it. In AFTER there is a hard edged note "
         "with a countable beat, and it gets harsher as the throttle goes down "
         "rather than just louder. The top end is the tell — in BEFORE "
         "everything above about 2.6 kHz is hiss, because there was literally "
         "nothing else up there."),
        ("launch", AB_LAUNCH_T0, AB_LAUNCH_DUR, 12,
         "the launch at 33 s — the closest and driest the engine ever is",
         "Idle, then the car goes. BEFORE thins into air as the revs climb; "
         "AFTER hardens. Listen for the six cylinders being audibly different "
         "from each other at idle, and for the turbo sweeping UP through the "
         "band as it spools instead of sitting above hearing."),
    ):
        if not os.path.exists(HAIR):
            print(f"!! {HAIR} missing — skipping the R2-1401 A/B")
            break
        before, sr, pbef = cut(HAIR, t0, dur)
        after, sr, paft = cut(POST, t0, dur)
        add(f"{n0}_{tag}_BEFORE_hairblower.wav", before, sr,
            f"BEFORE (rejected master) — {where}", cue,
            f"{int(t0 * FPS) + 1}-{int((t0 + dur) * FPS)}", pbef)
        add(f"{n0 + 1}_{tag}_AFTER_rebuilt.wav", after, sr,
            f"AFTER (rebuilt exhaust + turbo) — {where}", cue,
            f"{int(t0 * FPS) + 1}-{int((t0 + dur) * FPS)}", paft)
        gap2 = np.zeros((int(0.7 * sr), before.shape[1]))
        add(f"{n0 + 2}_{tag}_AB_one_press.wav",
            np.concatenate([before, gap2, after]), sr,
            f"Both of the above back to back, one press of play — {where}",
            "Hair dryer, three quarters of a second of silence, then engine. "
            "If they sound like the same thing, the fix did not land and I need "
            "to know that.",
            f"{int(t0 * FPS) + 1}-{int((t0 + dur) * FPS)} twice",
            pbef + [dict(paft[0], clip_offset=before.shape[0] + gap2.shape[0])])

    # ------------------------------------------------ R2-2001: the tubes ------
    # ONE pair, at the measured worst moment, and nothing else. The client has
    # now been asked to listen twice; this is the only thing on the page that is
    # new since the second note.
    if os.path.exists(TUBES):
        t0, dur = AB_TUBES_T0, AB_TUBES_DUR
        frames = f"{int(t0 * FPS) + 1}-{int((t0 + dur) * FPS)}"
        cue = ("Same six seconds of the flying lap, same level. In BEFORE each "
               "firing sets the pipes ringing and the ring is still sounding "
               "when the next one arrives -- measured, every mode rang for 8 to "
               "21 firing intervals -- so the engine reads as something being "
               "struck rather than something running. In AFTER the ring stops "
               "between firings and what is left is the firing rate itself. "
               "Listen to the METAL above the note, not the note.")
        before, sr, pbef = cut(TUBES, t0, dur)
        after, _, paft = cut(POST, t0, dur)
        add("16_lap_BEFORE_tubes.wav", before, sr,
            "BEFORE (the master you heard) — the flying lap at 73.5 s", cue,
            frames, pbef)
        add("17_lap_AFTER_damped.wav", after, sr,
            "AFTER (damped waveguide) — the flying lap at 73.5 s", cue,
            frames, paft)
        gap3 = np.zeros((int(0.7 * sr), before.shape[1]))
        add("18_lap_AB_one_press.wav",
            np.concatenate([before, gap3, after]), sr,
            "Both of the above back to back, one press of play",
            "Banging, three quarters of a second of silence, then the same car "
            "without the banging. If they sound the same, tell me — the exhaust's "
            "audible ringing tail is measured 4x shorter (26.1 ms to 6.5 ms) and "
            "I need to know if that is not what you are hearing.",
            f"{frames} twice",
            pbef + [dict(paft[0], clip_offset=before.shape[0] + gap3.shape[0])])
    else:
        print(f"!! {TUBES} missing — skipping the R2-2001 A/B")

    # ------------------------------- R2-2221: THE ENDING, WHICH IS THE PAGE ---
    # WHY THIS PAIR IS AT THE BOTTOM AND IS THE ONE THAT MATTERS. 63 % of the
    # client's listening time went on the breach and the ending, 0 % on the
    # flying lap -- and the flying lap is the only beat the last two fixes
    # improved. Everything above this line answers a complaint about a beat they
    # did not listen to.
    #
    # THE MEASUREMENT SAYS THE ENDING IS FINE, SO THIS CLIP EXISTS TO BE PROVED
    # WRONG. The harmonic gate scores the ending +0.16 dB above 2.6 kHz, which is
    # two decibels off a literal noise generator, and that reading is not about
    # the car: above 2.6 kHz the ending is 86.1 % CROWD and 0.93 % engine (from
    # a per-bus render, R2-2221). The engine bus alone reads +15.7 dB there. So
    # the number that looks alarming is a correct measurement of a crowd.
    #
    # What DID change between the master they rejected and this one, measured in
    # octave bands over the final idle with the overall level removed: +3.7 to
    # +3.9 dB across 250 Hz - 1 kHz, where a 4,300 rpm idle's firing series
    # actually lives, and -7.4 / -8.1 dB at 4 and 8 kHz. The film got more car
    # and less hiss, and the gate's above-2.6 kHz limb sits entirely inside the
    # part that got quieter -- which is why it moved 0.27 dB while the flying lap
    # moved 7.40. The cue below describes exactly that, so it can be checked.
    if os.path.exists(HAIR):
        t0, dur = 113.1, 10.98
        cue = ("The last eleven seconds: the car slows, stops and idles while the "
               "camera rises away. BEFORE is the master you first rejected. The "
               "change is in the MIDDLE of the sound, not the top -- the idle's "
               "own beat around 250 Hz to 1 kHz is about 4 dB stronger, and the "
               "hiss above 4 kHz is 7 to 8 dB weaker. The top end here is a "
               "CROWD, not the car: above 2.6 kHz this beat is 86 % crowd and "
               "1 % engine, so if it sounds thin up there that is the grandstand "
               "and the distance, and it is meant to be. What I need to know is "
               "whether the car is present underneath it.")
        before, sr, pbef = cut(HAIR, t0, dur)
        after, _, paft = cut(POST, t0, dur)
        frames = f"{int(t0 * FPS) + 1}-{int((t0 + dur) * FPS)}"
        add("19_ending_BEFORE_rejected.wav", before, sr,
            "BEFORE (the first master you rejected) — the ending, 113.1 s to the "
            "end", cue, frames, pbef)
        add("20_ending_AFTER_delivered.wav", after, sr,
            "AFTER (the delivered master) — the ending, 113.1 s to the end",
            cue, frames, paft)
        gap4 = np.zeros((int(0.7 * sr), before.shape[1]))
        add("21_ending_AB_one_press.wav",
            np.concatenate([before, gap4, after]), sr,
            "THE ONE TO PLAY — both endings back to back, one press",
            "Before, three quarters of a second of silence, then after. Listen "
            "for the car UNDER the crowd, not for the crowd. If the second half "
            "does not have more engine in it than the first, my measurement is "
            "wrong and I need to know that — it says +3.9 dB across the octaves "
            "an idle lives in.",
            f"{frames} twice",
            pbef + [dict(paft[0], clip_offset=before.shape[0] + gap4.shape[0])])

    with open(os.path.join(OUT, "clips.json"), "w") as fh:
        json.dump(clips, fh, indent=1)
    print("  %-34s %6s %8s %-11s %-7s %s"
          % ("clip", "sec", "peak", "frames", "exact?", "source"))
    for c in clips:
        srcs = " + ".join(sorted({os.path.basename(s["path"])
                                  for s in c.get("sources", [])})) or "-"
        print("  %-34s %6.2f %8.4f f%-10s %-7s %s"
              % (c["file"], c["seconds"], c["peak"], c["film_frames"],
                 {True: "BIT-EXACT", False: "DIFFERS", None: "-"}
                 .get(c.get("bit_exact_against_source")), srcs))
    n_master = sum(1 for c in clips if c.get("is_delivered_master"))
    print(">> %d clips -> %s" % (len(clips), OUT))
    print(">> %d of them are cut from the delivered master (%s), bit-exact; the "
          "rest are\n   kept artefacts or the A-variant ending, and each says so "
          "in its own record." % (n_master, md5(POST)))
    for m in prov_fail:
        print("!! %s" % m)
    print(">> STAGE RESULT:",
          "AUDIO_WATCH_CLIPS_OK" if not prov_fail else "AUDIO_WATCH_CLIPS_FAIL")
    if prov_fail:
        raise SystemExit(1)
    return clips


if __name__ == "__main__":
    main()
