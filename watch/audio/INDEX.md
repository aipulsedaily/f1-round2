# The listening pass — 9 clips, about 4 minutes total

**Nobody has listened to this film.** Every judgement on its audio so far has been
made from spectrograms and band measurements. That is how a **+31 dB bang on the
very first frame** survived every automated gate this project built, and sat in
**every master this project ever shipped**. It is fixed. But the gap it exposed is
a gap in *capability*, not diligence — and it closes when a person presses play.

These are the moments that carry risk. Nothing else needs your ears.

---

## If you only have ten seconds

Play **`03_opening_AB_one_press.wav`**.

Bang → one second of silence → no bang. That is the defect and the fix, back to
back. If both halves sound the same, tell us — they are 24 dB apart on frame 1.

---

## Before you start

- **Do not change your volume between clips.** Nothing is normalised per clip;
  every clip keeps the master's own absolute level, so one setting is right for
  all nine. A loud clip is loud because the film is.
- **These are WAVs on purpose.** MP3/AAC encoders insert ~25 ms of silence at the
  start of a file, which would shift the exact thing clip 01 and 02 are asking you
  to judge. 16 MB total.
- Clips 04–09 have a 5 ms fade at the in-point so the *cut* does not make a click
  you might mistake for a defect. **Clips 01, 02 and 03 have no fade-in** — they
  begin at the film's own sample 0, and fading them would fade out the defect.

---

## The clips

| # | File | What it is | Listen **for** |
|---|------|-----------|----------------|
| 01 | `01_opening_BEFORE_defect.wav` | Frame 1 as it shipped, 2 Aug | A hard **bang in the first hundredth of a second**, before the showroom tone starts. It is the reverb tail of a car at 323 km/h, wrapped onto frame 1 by a circular buffer. It should not be there at all. |
| 02 | `02_opening_AFTER_fixed.wav` | Frame 1 now | The same four seconds with **nothing at the top** — an empty showroom starting from silence. Any click or thump at the very start means the fix did not hold. |
| 03 | `03_opening_AB_one_press.wav` | 01 and 02 back to back | The whole defect in nine seconds. **Start here.** |
| 04 | `04_launch_seam_f792_793.wav` | The launch, beat 1 → 2 at 33.000 s (**f792 \| f793**) | A join 1.5 s in. A click, a jump in level, or the room changing abruptly. It should sound like **one continuous take**. |
| 05 | `05_breach_f865.wav` | The breach — the car reaches the glass, 36.000 s (**f865**) | The film's loudest event. Listen for **distortion or clipping on the glass**, not for a join — this one is *supposed* to be violent. |
| 06 | `06_ending_seam_f2715.wav` | The lift into the ending, beat 5 → 6 at 113.100 s (**f2714 \| f2715**) | The injectors cut here. A 0.74 dB step at the lift, 28 ms before this join, was removed — listen for any **remaining bump or gear-change glitch** as the engine goes off-throttle. |
| 07 | `07_ending_A_no_lapdown.wav` | **Ending A** — no lap-down | The car does not slow; the lap simply ends. |
| 08 | `08_ending_B_lapdown.wav` | **Ending B** — with the lap-down | Seven downshifts at a 0.48 s cadence, then the car stops and idles. Do the downshifts sound **mechanical or sequenced**? Does the stop land? |
| 09 | `09_final_idle_last2s.wav` | The last two seconds — the stopped car | An engine at idle has **a pulse you can count** (215 Hz firing line — three firings per rev at a 4,300 rpm idle). A *motored* engine — turning with the injectors cut — is a dead whoosh with no beat. It was a motored engine until this pass; confirm it now **idles**. |

---

## The one decision only you can make

**Clips 07 and 08 are a creative choice, not a defect hunt.** A and B are the same
film until 113.1 s and differ only in whether the car winds down. Both are
correct; pick one. Everything else on this page is us asking you to check our
work — this is us asking you to decide.

---

## What a person can hear that a gate cannot

The gates now include an **edge gate** that looks at frame 1 and the last frame —
the two frames no other gate visited, because the seam gate walks beat
*boundaries* and the film's two ends are *edges*. It fails the old master (+31.62 dB)
and passes the current one (+8.53 dB).

But a gate only ever catches the defect it was told to look for. It cannot tell
you whether the downshifts sound like a gearbox, whether the glass sounds like
glass, or whether the ending lands. **That is what these four minutes are for.**
