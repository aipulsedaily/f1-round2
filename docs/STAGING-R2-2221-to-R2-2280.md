# R2-2221 .. R2-2228 — the two beats the client actually heard

**Result in one line: the breach and the ending are not defective, the metric was
wrong for both, for two different reasons, and the gate that could not see them
now covers five beats of six and declares the sixth with the numbers that make it
undeclarable.**

The master is unchanged. `audio/out/master.wav` is still
`d5087fd021b5f748f176ecb2b6c1de67`, 124.0833 s, 2,978 frames, −14.00 LUFS,
−1.10 dBTP, and a fresh 96 kHz render of the current code reproduces it **byte for
byte** (R2-2228). All 8 gates pass: `AUDIO_VERIFY_OK`.

---

## The claim that was put to us, and what it turned out to be

> breach +0.09 dB, ending +0.16 dB, ungated; pure noise reads −1.70 to −1.75 dB;
> 63 % of the client's listening time was those two beats and 0 % was the flying
> lap.

Every number in that is correct. The conclusion drawn from it is not, and this
note is mostly the measurements that separate the two.

### R2-2223 — the breach fails BOTH applicability tests, each by two orders of magnitude

| | measured | limit |
|---|---:|---:|
| share of the beat's energy above 2.6 kHz | **0.0183 %** | 0.20 % |
| that band's absolute level | **−47.7 dBFS** | — |
| …below the flying lap's own RMS | **31.5 dB** | — |
| next darkest beat in the film (1_assembly) | 1.02 % | — |
| broadband power against an octave-matched hair dryer | **−0.044** | +0.20 |

The +0.09 dB is a ratio computed on one part in five thousand of the beat. And on
the broadband limb — where the breach's energy actually is — the metric scores
the film **below** a hair dryer, i.e. it has negative discrimination there. That
is not a bug: the breach is 995 shard contacts and a laminated pane, and a
median-filtered spectral floor cannot find a line spectrum in 995 randomly-timed
inharmonic rings because there is not one. Breaking glass is broadband on purpose.

The 0.20 % threshold sits inside a **fifty-fold gap** between the breach and every
other beat, so no choice of it inside that gap changes the answer.

### R2-2224 — the ending's top end is a crowd

Per-bus render (R2-2228), 113.1–124.083 s, share of energy **above 2.6 kHz**:

| bus | share of the band | vs engine |
|---|---:|---:|
| **crowd** | **86.12 %** | +19.6 dB |
| bed | 8.45 % | +9.6 dB |
| reflect_garage | 4.27 % | +6.6 dB |
| **engine** | **0.93 %** | 0.0 dB |
| wind | 0.72 % | −1.1 dB |

Over the deceleration alone (113.1–117.0 s) the crowd is **91.50 %** of that band.
The harmonic gate, scoring the ending above 2.6 kHz, was measuring a grandstand,
and it measured it correctly: crowds are noise.

The engine in the ending is not the problem and is not masked in the lap's sense.
**The engine bus alone reads +15.73 dB above 2.6 kHz there**, against +17.03 dB
over the flying lap — i.e. the ending's engine is as clean as the film's best.

Contrast with the flying lap, the same table, which is the answer everyone already
agrees on and is used here as a positive control: above 2.6 kHz the lap is
**91.33 % engine** and 0.96 % wind. In the beat the fix was for, the engine owns
the band. In the ending it owns 0.93 % of it — because the car is stopping, the
camera is rising away, and a 4,300 rpm idle's firing series is 215 Hz, whose
twelfth harmonic is 2.58 kHz. There is very little engine above 2.6 kHz in the
ending **by physics**, not by defect.

### The evidence that needs no stems at all: neither beat moved

Median dB above 2.6 kHz, four masters, two complete engine rebuilds between them:

| beat | 2 Aug | R2-1400 | R2-2001 | now | **movement** |
|---|---:|---:|---:|---:|---:|
| 5_lap | −0.71 | −0.72 | +6.68 | +5.84 | **7.40** |
| 2_launch | +1.36 | +1.27 | +5.63 | +8.06 | **6.79** |
| 4_transit | −0.55 | −0.59 | +3.57 | +3.91 | **4.51** |
| **6_ending** | +0.40 | +0.40 | +0.35 | +0.13 | **0.27** |
| **3_breach** | +1.49 | +1.45 | +0.08 | +0.05 | **1.44** |
| 1_assembly | −1.40 | −1.35 | −1.38 | −1.42 | 0.07 |

**A number that does not respond to two rebuilds of the engine is not measuring
the engine.** Reproduced by `tools/audio_hnr_evidence.py`, section 5.

### And the ending did improve — in the band nobody was scoring

Octave-band change over the final idle, delivered minus rejected, overall level
removed:

| | 31 | 63 | 125 | 250 | 500 | 1k | 2k | 4k | 8k |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dB | +1.8 | +1.4 | +0.6 | **+3.7** | **+3.9** | **+3.7** | +0.5 | **−7.4** | **−8.1** |

The film gained ~3.9 dB of car across the octaves an idle actually lives in and
lost 7–8 dB of hiss above 4 kHz. The gate's above-2.6 kHz limb sits **entirely
inside the part that got quieter**, which is why it read 0.27 dB of movement.

---

## R2-2221 — the gate now covers the film

`audio/verify.py`. `driven = ["2_launch", "4_transit", "5_lap"]` is gone as a
coverage list; it survives only as `HNR_ENGINE_BEATS`, choosing which of two
thresholds a beat is held to.

* **Scored: 6 of 6. Gated: 5 of 6.** The sixth, `3_breach`, is in
  `HNR_DECLARED_UNMEASURABLE` and the report prints both numbers above as the
  reason. Any *other* beat that becomes unmeasurable on both limbs lands in
  `undeclared_unmeasurable` and **fails** the gate.
* The declaration cannot rot in the film's favour: the two numbers are recomputed
  every run, so if a future edit puts high frequency back into the breach its
  share rises past 0.20 %, the limb becomes applicable on its own, and the breach
  starts being gated **with no edit to `verify.py`**.
* Two thresholds, each with a stated meaning: **3.0 dB** (the engine test, already
  justified) and **−1.0 dB** = one dB above what this metric reads on something
  with no line spectrum at all, measured per beat at −1.95 to −2.10 on the
  octave-matched hair dryer and −1.98 to −2.01 on flat white noise.

## R2-2222 — the median is replaced by the fraction below, not by a percentile

The percentile floor was authorised. **Measured, a percentile of the value is not
estimable here**, and the fraction below a threshold — the same statement read
from the other end — is. Block bootstrap, 200 ms blocks, 3000 resamples:

| beat | windows | SE of p20 **of the value** | SE of the **fraction below 3.0 dB** |
|---|---:|---:|---:|
| 2_launch | 120 | **±1.53 dB** | ±0.062 |
| 4_transit | 224 | ±0.52 dB | ±0.072 |
| 5_lap | 2540 | ±0.40 dB | ±0.023 |

Beat 2 is 3.0 seconds. Its 5th percentile is six windows and carries a **±2.69 dB**
error bar, against 0.58 dB of available separation. Nothing below p40 reached even
3σ. The fraction separates instead because the hair dryer's failure is that
*almost every* window is noise-like, not that its median is low: over the lap,
**0.331 of windows below 3.0 dB against the rejected master's 0.911**; over the
transit, 0.379 against 0.964.

**Margins of the delivered master against its limits, in standard errors: worst
3.5σ (transit HF), best 30.2σ (lap broadband).** The value-percentile form could
not reach 3σ anywhere below its own median.

### What fraction is permitted, and why

One rule, every beat, every limb: **the limit is the midpoint between what this
master reads and what the adversary reads, rounded to 0.05.**

* **HF limb — the test.** Adversary = the tightest of the octave-matched hair
  dryer and the two masters the client rejected. That limb exists to catch a hair
  blower, so it is set against one.
* **BB limb — a floor, not the test.** Adversary = the hair dryer alone. The
  rejected masters are not broadband failures and were never claimed to be
  (3.49 vs 3.89 dB, per the note already in the file). Setting the floor against
  them produces a limit *tighter than the film*: measured, 0.05 at a 0.00σ margin.

| beat | limb | thr | film | adversary | **limit** | margin |
|---|---|---:|---:|---:|---:|---:|
| 1_assembly | hf | −1.0 | 0.707 | 0.952 | **0.85** | 6.4σ |
| 1_assembly | bb | −1.0 | 0.045 | 0.515 | **0.30** | 28.2σ |
| 2_launch | hf | +3.0 | 0.158 | 0.658 | **0.40** | 4.0σ |
| 2_launch | bb | +2.0 | 0.050 | 1.000 | **0.50** | 14.9σ |
| 4_transit | hf | +3.0 | 0.379 | 0.964 | **0.65** | 3.6σ |
| 4_transit | bb | +2.0 | 0.094 | 0.996 | **0.55** | 19.5σ |
| 5_lap | hf | +3.0 | 0.331 | 0.911 | **0.60** | 11.8σ |
| 5_lap | bb | +2.0 | 0.182 | 0.993 | **0.60** | 30.2σ |
| 6_ending | hf | −1.0 | 0.307 | 0.968 | **0.65** | 6.2σ |
| 6_ending | bb | −1.0 | 0.135 | 0.498 | **0.30** | 6.6σ |

**Why the lap is permitted 0.60 and not 0.05.** The bottom third of the flying lap
is the **quiet** third, and that was checked rather than assumed: correlation
between a window's above-2.6 kHz ratio and its own level over the lap is
**+0.252**, and restricting to windows within 6 dB of the lap's own 95th-percentile
level (63.0 % of them) moves the median from **5.84 to 8.03 dB**. A film whose
subject drives away from the camera for part of a lap is required to have quiet
windows; requiring 3 dB of harmonic-to-noise inside them is requiring the car to
be somewhere it is not.

### Verdicts

| case | |
|---|---|
| the delivered master | **PASS** |
| REJECTED R2-1400 (hair blower) | FAIL — launch .hf 0.67>0.40, transit 0.96>0.65, lap 0.91>0.60 |
| SHIPPED 2 Aug (same defect) | FAIL — launch .hf 0.66>0.40, transit 0.96>0.65, lap 0.91>0.60 |
| octave-matched hair dryer | FAIL on **10 limbs** |
| top four octaves → noise | FAIL on **5 limbs**, HF only, broadband intact — the two thresholds are still separate numbers |
| flat white noise | FAIL on **10 limbs** |
| REJECTED R2-2001 (tubular bells) | PASS — correct, and `waveguide_gate` fails it. HNR asks "is this tonal"; a struck tube is. |

The two newly-gated beats have teeth: the stated-negative control now fails
**1_assembly.hf at 0.989 > 0.85 and 6_ending.hf at 0.993 > 0.65**. Nothing would
have caught either before.

### A defect found in this work, in this work

The first build computed applicability from **the signal under test**. Both
applicability tests compare against a hair dryer — so when the signal *is* a hair
dryer, every limb read zero power, every limb went NOT APPLICABLE, and
`CONTROL: white noise wearing the master's own octave balance` **passed with no
failures**, while the master the client rejected failed one beat of three instead
of three of three. Applicability is a property of the film; `main()` computes it
once from the master and hands it down. Recorded because it is the exact shape of
the hole this whole task exists to close.

---

## The deliverables

### R2-2226 — the cutter proves provenance instead of asserting it

`tools/audio_watch_clips.py`. Every clip now records its source path, that
source's md5 and the exact sample range taken; the cutter then **reads each clip
back off disk and compares its un-faded interior against the source, sample for
sample**, before it will write `clips.json`. `SOURCE_MUST_BE_MASTER` names the
nine clips that are claims about the delivered film; any one of them not bit-exact
against the master **stops the run** (`AUDIO_WATCH_CLIPS_FAIL`).

* **21 of 21 clips are bit-exact against their declared source.**
* **10 are the delivered master**, proved. Clip 08 is among them: it routes through
  `ending_B.wav`, and the cutter now *proves* that file is the master's own tail
  rather than assuming it — which is precisely the R2-2010 shape, an intermediate
  file that used to be the master and quietly stopped being one.
* **Clip 07 is the one honest exception and now says so.** Ending A is a different
  render by construction; it derives from `master_A_nolapdown.wav`, is bit-exact
  against it, and both `clips.json` and `INDEX.md` disclose it. It was not
  disclosing it before.
* Clips 07/08 were **double-faded** — `audio_ending_ab.py` writes a 5 ms linear
  ramp and the cutter added a second, making the first 240 samples quadratic, and
  putting 240 samples between the clip and the master for no reason. Removed.
* Four `film_frames` strings were hardcoded with a 0-based start against a 1-based
  end (04, 05, 06, 09 claimed 97/145/97/56 frames where the clip carried
  96/144/96/54). Derived from the samples now.

**Opening steps.** Worst across the 19 non-demo clips: **−12.47 dB** (clip 02,
which is deliberately unfaded because it *is* the film's sample 0). Every other
clip opens from a boundary sample of exactly 0.0 at ≤ −209 dB. Only clips 01 and
03 fail `edge_gate`, on the +23.45 dB frame-1 artefact they exist to demonstrate.
The +9.67 dB extract defect is not reintroduced.

> Correction to R2-1981..R2-2040: that note says the worst opening step is
> "**+0.00 dB** — every one of them starts from a boundary sample of exactly
> zero", and says clips 01/03 open at +19.58 dB. Neither reproduces. Clip 02's
> first sample is 0.005794 and its step is −12.47 dB; 01/03 open at +23.45 dB.
> The real figures are *better* than claimed, but they were not checkable.

### R2-2225 — a live docstring citing dead files

`edge_gate`'s docstring quoted `ending_A_nolapdown.wav` / `ending_B_lapdown.wav`
at "a hard cut at 0.542 with a +9.67 dB step". Those files are orphaned under
`audio/out/ab/brake/`, unwritten since 7 Aug 10:50, read by no code path, and
re-measure at 0.258 / **+5.08 dB** and 0.259 / **+5.13 dB**. The paragraph
immediately above it warns against exactly this. Rewritten to make the point
without citing a file nothing writes.

### R2-2227 — the habit is now a mechanism

`master_B_lapdown.wav` was lost to an unattended shell script, at which point
nobody was present to rename anything. `audio.master.build()` now writes beside
the target, compares, and **moves any differing existing master aside** as
`*_SUPERSEDED_<mtime>_<md5>.wav` before replacing it, logging the name into the
report. A render that reproduces its output byte for byte archives nothing and
says so. 35 MB against losing the only copy of an artefact a client has already
formed an opinion about.

(`master_B_lapdown.wav` on disk is currently md5-identical to `master.wav`: the
delivered master *is* the B variant.)

### R2-2228 — one render, sixteen buses

`audio.master --stems DIR` writes each bus at the exact point it enters the sum —
after the LUFS-S trim and the declared HF shelf, before the program gain and the
limiter. The wind diagnosis that fixed the lap cost sixteen separate 37-minute
renders; this costs one. **It provably cannot move the master:** the stem run's
output is `d5087fd021b5f748f176ecb2b6c1de67`, identical to the delivered file. Off
by default.

---

## What was NOT done, and why

**No change to the mix, the buses, or the master.** The wind lever was the right
answer for the lap and is the wrong answer here: above 2.6 kHz the ending's wind
is 0.72 % of the band and 1.1 dB *below* the engine. The masker in the ending is
a crowd at a rising wide shot of a circuit, which is a subject, not a texture
artefact — unlike the lap, where wind was 4.7 dB louder than the car and had
nothing in it to hear but air.

**`PIPE_LOOP_GAIN` 0.34, `COLLECTOR_LOOP_GAIN` 0.14, the rise-time floor and the
+2.69 dB exhaust compensation are untouched.** The dispersive 3rd-order control at
1200 Hz is still failing on purpose at 20.5 % / 323 cents.

---

## R2-2229 / R2-2230 — two defects in `tools/gitguard.py`, found by using it

Landing this change took three commands that should have taken one, and the
reason is worth writing down: **the guard misreported its own state.** Both
defects are in the guard, not in the leases.

### R2-2229 — a session-level seed outlives the session

`inflight-2026-08-07` is a `seed-inflight` bulk claim — 308 paths, "everything
dirty right now" — from a session that has ended. Its TTL is 24 h
(`R2_GUARD_TTL_H`), which is far longer than the session that created it, so it
kept refusing the authors of the files it held. A guard built to stop one agent
clobbering another spent the evening **blocking authors from committing their own
work**. The seed needs a TTL shorter than a session, or the auto-lease needs to
yield to a claim from the file's actual modifier.

### R2-2230 — `cmd_claim` is all-or-nothing, so it reports "no" when the truth is "four of seven"

**This is the sharper of the two, because the stale seed at least names the path
it holds.** `cmd_claim` collects clashes across its whole argument list and, on
any clash, returns `FAIL (…, nothing claimed)`. One seed-held path in a batch of
seven therefore claims *nothing* and reads as a hard refusal of all seven — when
in fact four were claimable and the override at line 350 would have taken them.

Measured, in the order it happened, because a code reading is exactly what got
this wrong the first time:

```
$ R2_AGENT=r2-2221-audio-hnr tools/gitguard.py claim <all seven>
CLASH  audio/verify.py is already leased by inflight-2026-08-07 (via audio/verify.py)
CLASH  audio/master.py is already leased by inflight-2026-08-07 (via audio/master.py)
CLASH  tools/audio_watch_clips.py is already leased by inflight-2026-08-07 (via tools/audio_watch_clips.py)
>> STAGE RESULT: FAIL (3 clashes, nothing claimed)

$ R2_AGENT=r2-2221-audio-hnr tools/gitguard.py claim <the four held by inflight-auto>
  (4 path(s) released from inflight-auto -- an explicit claim wins)
claimed 4 path(s) for r2-2221-audio-hnr; lease now holds 7
>> STAGE RESULT: OK (0 clashes)
```

A per-path claim with a summary line — *claimed 4, refused 3, here is who holds
them* — makes the real shape visible in one command.

### The rule that was quoted, and the branch it actually lives in

The override was read as "an explicit claim beats an automatic lease", from the
comment at line 370, and applied to the seed. **Line 350 scopes that override to
`AUTO_OWNER` alone** — `AUTO_OWNER = "inflight-auto"`, nothing else — and **line
378 refuses the manual seed deliberately, with its reason written down**: *"That
set is somebody's unfinished work from before the guard existed, and saying so
out loud once is the entire point of it."* Both statements are true; only one of
them is the enforcing branch. **A rule quoted from a docstring instead of from the
code that enforces it is the same defect this file's audio half is about**, and it
is the third time today.

### And the escape hatch is the worst part

**`R2_GITGUARD=off` is worse than having no guard, because the next agent reads a
clean `OK` and believes it.** A guard whose false-positive rate is high enough
teaches people to route around it, and this one is now demonstrably high enough
to have taught that lesson to two agents in one evening. That is the argument the
staleness check's own docstring makes against refusing, and it applies to the
guard itself.

### What was NOT done

**The seed was not released by this agent.** Three paths were released by the
coordinator, who owns that decision because a seed is a session-level artefact;
**the other 305 keep their lease**, because the rest of that set really is
somebody's unfinished work. The standing rule is unchanged: never release another
owner's lease — but a bulk seed with no live owner is not another owner, and the
fix is to claim, not to override.

---

## What to check next, if the client says the ending is still wrong

The measurement says the ending is fine and `21_ending_AB_one_press.wav` exists to
be proved wrong. If they hear a problem, the first number to look at is the crowd
bus at `TARGET_LUFS_S["crowd"] = -27.0`, which owns 86 % of the band, and **not**
the engine or the wind. That is a mix decision with a name, not a defect hunt.
