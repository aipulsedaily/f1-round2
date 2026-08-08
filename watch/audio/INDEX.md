# The listening pass

You have told us the audio is bad twice. Both notes were right, both defects are
fixed, and both were in the **flying lap** — which is the beat you spent **none**
of your listening time on. **63 % of it went on the breach and the ending.**

So this round we went and measured those two, expecting to find a third defect.

**We did not find one, and this page is us showing our work rather than asking
you to take that on trust.**

---

## If you only have twenty-three seconds

Play **`21_ending_AB_one_press.wav`**.

The last eleven seconds of the film as you first heard it → three quarters of a
second of silence → the same eleven seconds as they stand now.

**Listen for the car underneath the crowd, not for the crowd.** Measured in
octave bands over the final idle, with the overall loudness taken out: the car's
own note is **+3.9 dB** across 250 Hz–1 kHz, where an idling V6's beat actually
lives, and the hiss above 4 kHz is **7 to 8 dB quieter**. If the second half does
not have more engine in it than the first, our measurement is wrong and we need
to know.

---

## Why we thought the ending was broken, and why it is not

Our own instrument scored the breach at **+0.09 dB** and the ending at
**+0.16 dB** on a tonal-versus-noise measure where **a literal noise generator
reads −2.0 dB**. Those were the two worst numbers in the film, they were the two
beats you actually listened to, and the instrument was not even checking them.

We checked them. Both numbers are real and neither is about the car.

**The ending.** We re-rendered the film one sound source at a time. Above
2.6 kHz — the band that measure scores — the ending is **86.1 % crowd** and
**0.93 % engine**. The measure was reading a grandstand, and it read it
correctly: crowds are noise. The engine on its own, in that same stretch, scores
**+15.7 dB** — as clean as it is anywhere in the film. If the top of the ending
sounds thin, that is distance and a rising camera, and it is meant to be.

**The breach.** Above 2.6 kHz the breach carries **0.02 % of its own energy** —
that is **31.5 dB below the flying lap**, one part in five thousand of what you
hear. The +0.09 dB is a ratio computed on almost nothing. Below that band the
measure scores the breach *worse than a hair dryer*, because a breach is 995
pieces of glass hitting things and there is no engine note in it to find. There
never was. **Breaking glass is broadband; that is what breaking glass is.**

**The cleanest evidence is that neither beat moved.** We have four masters
spanning two complete rebuilds of the engine. Above 2.6 kHz:

| beat | 2 Aug | after the hair-dryer fix | after the tubes fix | now | **total movement** |
|---|---:|---:|---:|---:|---:|
| the flying lap | −0.71 | −0.72 | +6.68 | +5.84 | **7.40 dB** |
| the launch | +1.36 | +1.27 | +5.63 | +8.06 | **6.79 dB** |
| the transit | −0.55 | −0.59 | +3.57 | +3.91 | **4.51 dB** |
| **the ending** | +0.40 | +0.40 | +0.35 | +0.13 | **0.27 dB** |
| **the breach** | +1.49 | +1.45 | +0.08 | +0.05 | **1.44 dB** |

Two complete engine rebuilds moved the ending by a quarter of a decibel. A number
that does not respond to the engine is not measuring the engine.

**What we changed instead of the sound: the instrument.** It scored three of the
six beats and it scored each one on a median, which says nothing about the other
half of a beat. It now scores all six, it gates five of them on *what fraction of
the beat* falls below the line rather than on the middle of it, and for the sixth
— the breach — it states in the report that it cannot measure it, and prints both
numbers proving why. It still fails both masters you rejected.

---


## What "banging on tubes" turned out to be

When you said *"hair blower"*, the exhaust was rebuilt from scratch as a physical
model of six pipes. That fixed the hiss. **It also gave the pipes almost no
damping**, and that is what you heard the second time.

We can put numbers on it. A V6 at 11,000 rpm fires every **1.82 ms**:

| | before | now |
|---|---:|---:|
| how long a pipe resonance rings | 37.7 ms | **12.5 ms** |
| in firing intervals — how many strikes overlap | **20.7** | **6.9** |
| the collector, the worst offender | 48.6 ms | **11.9 ms** |
| **the audible ringing tail, 2–6 kHz** | **26.1 ms** | **6.5 ms** |

That last row is the one to trust — it is measured by exciting the exhaust, then
cutting the excitation dead and timing how long the metal keeps sounding.
**Four times shorter.**

Honest caveat rather than a flattering one: at 11,000 rpm sound cannot even
travel up and back down one exhaust pipe (1.91 ms) before the next cylinder
fires, so **some** overlap is physically unavoidable and a real car has it too.
Twenty overlapping rings is a tubular bell. Three or four is an engine.

The second change: the model was hitting the pipes with a **71 microsecond**
edge at high rpm — sharper than any real exhaust valve can open, and sharpest
exactly where the engine also fires most often. That now has a floor.

**A note on what we did not do.** The obvious fix — damp the pipes harder — makes
it worse, and we can show that too: it detunes the upper resonances until they
are no longer in tune with each other, which is the actual definition of a bell.
We measured it at **323 cents** out, and threw it away. The fix is in the pipes'
losses, not their filtering.

---

## Before you start

- **Do not change your volume between clips.** Nothing is normalised per clip;
  every clip keeps the master's own absolute level, so one setting is right for
  all of them. A loud clip is loud because the film is.
- **These are WAVs on purpose.** MP3/AAC encoders insert ~25 ms of silence at the
  start of a file, which would shift the exact thing clips 01–03 ask you to
  judge.
- Every clip fades in over 5 ms at the cut, so the *edit* never makes a click you
  might mistake for a defect. **Clips 01, 02 and 03 are the exception** — they
  begin at the film's own sample 0, and fading them would fade out the defect
  they exist to show.

---

## The clips

### The new pair — the ending, which is what this round is about

| # | File | Listen **for** |
|---|---|---|
| 19 | `19_ending_BEFORE_rejected.wav` | The last eleven seconds as you first heard them. |
| 20 | `20_ending_AFTER_delivered.wav` | The same eleven seconds as delivered. |
| **21** | **`21_ending_AB_one_press.wav`** | **Both, one press. Start here.** The car under the crowd, not the crowd. |

### The previous pair — the exhaust ringing

| # | File | Listen **for** |
|---|---|---|
| 16 | `16_lap_BEFORE_tubes.wav` | The lap at 73.5 s, as you heard it. The ringing metal sitting on top of the engine. |
| 17 | `17_lap_AFTER_damped.wav` | The same six seconds, damped. |
| **18** | **`18_lap_AB_one_press.wav`** | **Both, one press. Start here.** |

73.5 s was chosen by measurement, not taste: it is the six-second window with the
most deeply modulated 2–6 kHz energy anywhere inside the flying lap. The very
worst window in the whole film is 42.5 s, and we did *not* use it — it straddles
the breach, so half of it is breaking glass and the comparison would be unfair.

### The wind

Your first complaint was the broadband noise, and that fix is in this master. Over
the flying lap the tonal-to-noise ratio above 2.6 kHz went from **−0.72 dB to
+6.69 dB** — the engine now leads the air by 7.4 dB where it used to lose to it.

**One correction to what we told you last time.** We said the breach and the
ending were "much worse than the lap" on this measure and that we would go and
fix them. We went, and the sentence was wrong: on the breach and the ending that
measure is not reading the car at all — 86 % of the ending's top end is crowd and
the breach has essentially no top end to read. The numbers were right; what we
concluded from them was not. See the section above.

A third of the lap does still sit below where we would like it. That third is the
**quiet** third — the car far away, pointing away, between passes; we checked, and
a window's score tracks its own loudness at +0.25 correlation. A film whose
subject drives away from the camera is required to have quiet windows. If the
wind is still wrong to you, say so; we know where to go next.

| # | File | Listen **for** |
|---|---|---|
| 10–12 | `10_lap_BEFORE_hairblower` / `11_lap_AFTER_rebuilt` / `12_lap_AB_one_press` | The lap at 83 s, before and after the first rebuild. |
| 12–14 | `12_launch_BEFORE_hairblower` / `13_launch_AFTER_rebuilt` / `14_launch_AB_one_press` | The launch at 33 s — the closest and driest the engine ever is. |

(Two files share the number `12` — a naming collision in our cutter, not a
missing clip — and there is no `15`. All 21 files are listed on this page.)

### The rest — unchanged since last time, still worth your ears

| # | File | Listen **for** |
|---|---|---|
| 01–03 | `0*_opening_*` | A hard **bang in the first hundredth of a second**, and its removal. Clip 03 is both, back to back. They are 24 dB apart on frame 1. |
| 04 | `04_launch_seam_f792_793.wav` | A join 1.5 s in. It should sound like **one continuous take**. |
| 05 | `05_breach_f865.wav` | The film's loudest event. Listen for **distortion**, not for a join — this one is *supposed* to be violent. |
| 06 | `06_ending_seam_f2715.wav` | The injectors cut. Any **bump or gear-change glitch** as the engine goes off-throttle. |
| 07 | `07_ending_A_no_lapdown.wav` | **Ending A** — the car does not slow; the lap simply ends. |
| 08 | `08_ending_B_lapdown.wav` | **Ending B** — seven downshifts, then the car stops and idles. |
| 09 | `09_final_idle_last2s.wav` | An idling engine has **a pulse you can count**. Confirm it idles rather than coasting. |

**Clips 07 and 08 were the worst offenders in the stale set** — they were being
cut from two orphaned files that no part of our pipeline had written in weeks, so
they were older than everything else on the page. If you made the A/B ending
decision last time, please make it again; what you were played was not current.

**We have stopped asking you to trust that.** The tool that cuts this page now
records, for every clip, which file it came from, that file's checksum, and the
exact samples taken — and then reads each clip back off disk and compares it
against its source sample for sample before it will write the page. Ten of the
twenty-one are the delivered master, proved bit-exact, clip 08 among them. Clip
07 is the one deliberate exception: **Ending A is a different render** — that is
the choice you are being asked to make — and it now says so in its own record
instead of quietly not being the film.

We also found and fixed a **click at the very end of the film** — the master was
being cut off mid-note on its final sample, the mirror of the frame-1 bang in
clips 01–03. It was in the version you were played.

---

## The one decision only you can make

**Clips 07 and 08 are a creative choice, not a defect hunt.** A and B are the same
film until 113.1 s and differ only in whether the car winds down. Both are
correct; pick one.

---

## What a gate cannot tell us

**Every automated check we own passed the master you called complete shit** — and
the one built to catch the hair dryer passed it most confidently of all. It was
asking "is this tonal rather than noisy", and a struck tube is extremely tonal.
It scores beautifully. Nothing we had asked whether the tone *stops*.

There is now a check that does, and it fails both masters you rejected. But that
is us catching up to you, not getting ahead of you. **You have been right twice.**
