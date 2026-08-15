# Broken instruments

### A catalogue of measurements that could not measure the thing they existed for

This is a collection of one failure, found twenty-six times, in subsystems that
share no code and were written weeks apart by people solving unrelated problems.
The failure is:

> **A guard, gate, metric or report returned the same answer whether the defect
> it existed to catch was present or absent.**

Each case below is a real one from a single project — a computer-generated short
film, its synthesised soundtrack, and the distributed GPU render farm that
produced it. Every case names the log entry it was verified against, and every
number in it was re-read from that entry rather than from any summary. The
project's own summaries were wrong more than once, which is part of what this
document is about.

**You do not need to know anything about films, audio or render farms to read
this.** The domain terms are explained where they appear, and the mechanism in
each case is arithmetic, ordering or plumbing — not craft.

**How to read it.** Cases are grouped by *mechanism*, because the mechanism is
the transferable part. The families are:

| | family | the shape |
|---|---|---|
| **I** | [The instrument never opened the artefact](#i--the-instrument-never-opened-the-artefact) | it measured a record, a source file, or an intent, and reported on the thing |
| **II** | [The instrument's best score was a degenerate case](#ii--the-instruments-best-score-was-a-degenerate-case) | the metric was maximised by the absence of the thing it rewarded |
| **III** | [The instrument was calibrated against the artefact it judges](#iii--the-instrument-was-calibrated-against-the-artefact-it-judges) | the pass mark was a function of the defect |
| **IV** | [The instrument's own arithmetic destroyed the reading](#iv--the-instruments-own-arithmetic-destroyed-the-reading) | the measurement was taken correctly and then overwritten, cancelled or averaged away |
| **V** | [The instrument had no case to answer](#v--the-instrument-had-no-case-to-answer) | it passed on an empty set, or it never executed at all |
| **VI** | [The verdict existed and nothing was wired to it](#vi--the-verdict-existed-and-nothing-was-wired-to-it) | the instrument was right and its output went in the bin |
| **VII** | [The instrument measured the wrong quantity](#vii--the-instrument-measured-the-wrong-quantity) | a real, careful measurement of something adjacent to the question |

Then a [synthesis](#synthesis), and finally
[what actually caught these](#what-actually-caught-these) — which is the only
section with any advice in it.

Two claims that circulated in this project as folklore turned out, on checking
the source entries, to be **wrong or overstated**. They are recorded in
[Corrections](#corrections) at the end rather than quietly dropped, because
"someone trusted a summary instead of the source" is the meta-failure this whole
document is about, and it would be absurd to commit it here.

---

## I — The instrument never opened the artefact

### I.1 — A quality gate suite in which three of eight gates never read the file

**Source:** `docs/audio-rebuild3/SPEC-ENGINE-AND-GATES.md` §2 and its audit
JSON; the replacement is logged at R2-4039 in
`docs/STAGING-R2-4021-to-R2-4080.md`.

The film's soundtrack was checked by eight automated gates before delivery. The
client rejected three successive versions of that soundtrack. All three had
passed all eight gates.

An audit did one experiment. It took the delivered master, replaced only the
first 33 seconds — the part the client complained about — with **a single 2.000
second block of audio tiled 16.5 times**, renormalised it to the same loudness,
and ran the suite unmodified:

```
{"levels": true, "edges": true, "seam": true, "external_assets": true,
 "pitch": true, "doppler": true, "harmonic": true, "waveguide": true}
ALL_PASS = True     >> STAGE RESULT: AUDIO_VERIFY_OK     exit 0
```

A two-second loop played over and over. Eight green lights.

It is worse than a miss. The `harmonic` gate — the one meant to judge tonal
quality — scored the looped version at **+34.454 dB** against the real film's
**−1.416 dB** on the same measurement. **It rated the tape loop 35.9 dB better
than the film it had just passed.**

**Why.** Of the eight gates, **three never opened the delivered audio file at
all**:

* `external_assets` was a static scan of the project's *source code*;
* `pitch` re-synthesised a clean engine tone from telemetry and measured *that*,
  not the mix;
* `waveguide` algebraically root-solved constants out of a *source file* at one
  hand-picked engine speed.

All three pass on 100% white noise, because none of them can see the audio.

Of the remaining five, the coverage was: `edges` judged 2 frames out of 2,978;
`seam` judged 20 samples out of 5,956,000; `doppler` judged 85 windows inside a
single 4.2-second span. Only two gates formed any opinion at all about the 33
seconds the client was complaining about.

**The general lesson.** *Count what fraction of the artefact your checks
actually touch, in the artefact's own units.* "Eight gates" sounds like
coverage. Twenty samples out of six million is not coverage. And a check that
reads the source tree is a **provenance** check — a statement about what you
built — not a **quality** check, which is a statement about what came out.
Conflating the two is how a suite reports eight passes while three of its
members are blind.

---

### I.2 — A resolution check that read a database row instead of the file

**Source:** R2-3927, `docs/STAGING-R2-3901-to-R2-3960.md`.

A 2,978-frame film was rendered on rented GPUs. The delivery verifier reported:

```
>> STAGE RESULT: FAIL — 2 distinct resolution(s) ...
   resolutions delivered: 3840x2160, NonexNone
```

Ten frames — 122, 123, 624, 625, 1080, 1462, 2073, 2074, 2489, 2606 — carried a
**NULL width and height** in the broker's SQLite database. The check that
declared the film's resolution non-uniform was reading that column.

A second pass decoded all 2,978 files from scratch. All ten suspect frames
decoded at 3840×2160, mode RGB, no error, with brightness values sitting
comfortably among their neighbours. Total cost of settling it: **8 minutes 25
seconds** to read every byte of 23.5 GiB.

The NULLs came from a recovery path: when the network connection carrying a job
dropped mid-render, the frame was recovered from the remote machine rather than
fetched normally, and that recovery code recorded the file's checksum, byte
count and blank-detection verdict — but never populated width and height. The
frames were perfect. Only the bookkeeping was short.

The decode tool existed because an earlier entry (R2-3856) had written down
exactly this: *"a resolution check sourced from the record cannot catch a record
that is wrong about the file."*

**The general lesson.** This one is cheap and it is nearly universal:
**a check on a record is a check on the record.** Here the record happened to be
wrong in the harmless direction — it under-reported a good film. The same gap
run the other way is a record that confidently reports the right dimensions for
a file that has none.

---

### I.3 — A gate that judged pixel sizes without ever opening the image

**Source:** R2-012's sibling R2-020, `docs/DEFECT-LOG-R2.md`.

A gate judged whether small props were modelled in enough detail to survive
close-up. It worked in pixels: given the lens, the distance and the frame width,
it computed how many pixels a feature would occupy, and passed or failed on that
number.

```
tools/item_gate.py:155   RES_X_4K = 3840   <- every px figure derives from this
workflow script line 107  ./rq render --cam <CAM> --res 1920 1080
```

The gate never opened the rendered image. It assumed 3840 pixels wide. **11 of
28 delivered frames were 1920 wide.** Every pixel judgement on those 11 items was
out by exactly a factor of two — a feature the gate called 6 px was 3 px in the
image a human then looked at.

The consequences had to be triaged rather than simply re-run. Findings about
*absent* features survived — "a head with no face", "six poses across 600
figures" — because absence is scale-invariant. Findings about *amplitudes*
did not: one item had been condemned for a 1.6 mm silhouette error at a distance
where it subtends **0.02 px**.

That entry closes with a running tally of the same failure in that log:
"bounding boxes instead of surfaces, a mean normal that is zero for any closed
mesh, an assertion that could not fail, triangle counts instead of distances, an
empty test set reported as a pass, chunk statistics standing in for instances,
and now a resolution the renderer was never asked for. **Seven for seven.
Measure the artefact, not the intent.**"

---

### I.4 — A blank-frame detector defeated by a strip of sky

**Source:** R2-352, `vast-render/docs/linked-libraries.md` (mirrored at
`docs/DEFECT-LOG-R2.md` R2-352).

A scene file can *link* geometry out of another file by absolute path. The render
farm uploaded the scene but had never uploaded a linked library, and the 3D
software does not fail on an unresolved link — it substitutes placeholders, drops
the geometry, and renders the empty world **fast**.

Job `82ebdd064292` returned a strip of sky over pure black in **0.829 seconds**,
recorded `blank: OK`, `lum_mean 0.0899`, `lum_sd 0.2322`, `state: done`. Its
grandstands — the entire subject — were linked, and absent.

Three separate checks let it through, each for its own reason:

* **The blank gate.** It tested for *uniformity*. Sky over black is not uniform.
  A frame containing none of its subject read `OK`.
* **The missing-asset check.** Its own docstring named the failure it existed to
  prevent — *"the broker returns a subtly wrong frame and logs nothing"* — and
  then grepped the render log for **one string**: `Image file <path> does not
  exist`. That is what a missing *image* prints. A missing *library* prints
  `Cannot find lib '<path>'`. **The check named the right class of failure and
  tested for one instance of it.**
* **Render time.** 0.83 s looked wrong to a human who knew the scene. It is not
  anomalous in any corpus-relative sense — see [VII.3](#vii3--suspiciously-fast-is-not-a-detector).

**The general lesson.** *A metric that reads the same whether the thing is
present or absent is not a measurement.* That sentence is from the entry itself
and it is the thesis of this whole document. Note also the second bullet: a check
written against a **class** of failure but implemented against one **instance**
of it is the most seductive form of this bug, because the docstring is correct.

---

### I.5 — A perfect PNG with no picture in it, delivered and counted

**Source:** `vast-render/docs/incidents.md`, 2026-07-28.

The same farm, earlier. Job `0908e534b1d3` reported `done` in 33.217 s. Its
output was:

* 8,734 bytes
* a valid PNG signature and terminating chunk
* 640×480 — exactly the dimensions requested
* a checksum matching the digest the remote worker computed when it wrote it
* **mean 0.00000, standard deviation 0.00000, maximum 0.0000**

An entirely black image. It passed every check the farm performed, **because
every check the farm performed verified that the FILE was intact.** Nothing
looked at the picture.

The cause was benign — a stray calibration camera in the caller's scene, parked
3.7 km from everything, pitched 53° below the horizon, aimed at ground that does
not exist out there. Sibling frames from the same file on the same machine
returned 27–38 MB images. **The farm was still wrong, because it reported
success.**

The broker's own log line even carried the evidence, and no rule could read it:

```
21:56:07 INFO broker  job 0908e534b1d3 done — render 33.2s, total 799.8s, 0.0 MB
```

`0.0 MB`, in a batch where every neighbouring frame logged 27–38 MB.

**The general lesson, in the entry's own words:** the farm had inherited a
rigorous *transport* discipline — checksums end to end, truncation detection,
refusing to delete the remote copy until the local one verifies — **and none of
the content rigour.** "Do the bytes I have match the bytes that were written" and
"is there anything in the picture" are different questions, and only the second
one decides whether a delivery is a delivery.

The fix is worth noting because it is unusually well-judged: the replacement
emits a **classification** (`BLACK`, `TRANSPARENT`, `UNIFORM`, `SUSPICIOUS`,
`OK`, `UNREADABLE`), not a threshold. `SUSPICIOUS` is reported loudly and never
fails a job, because *"a check that refuses legitimate work gets switched off,
and then it protects nothing."* Thresholds were placed in a measured gap: of 240
real frames, standard deviations ran 0.00000 (the defect), 0.00794 (a flat grey
that nobody had ever been shown the number for), then 0.03494 for the flattest
legitimate frame. The bar sits at 0.005, inside the empty gap — and not at zero,
because a deliberately blank test render measured 0.0011, not 0.

---

## II — The instrument's best score was a degenerate case

### II.1 — A quality gate whose maximum score was silence

**Source:** R2-4147 and R2-4147(1), `docs/STAGING-R2-4141-to-R2-4200.md`.

This is the single most instructive case in the collection, because the metric is
reasonable, the threshold was derived honestly, the gate caught real defects —
and it still drove four rebuilds toward an empty soundtrack.

The gate, `G-EVENT`, was meant to answer *"does this passage contain events, or
is it a stationary wash?"* — the difference between a machine shop and a hair
dryer. Its statistic, `local_dynamic_range`, is the span between the loud
moments and the quiet moments: the 95th percentile minus the 5th percentile of
the short-term level, inside two-second windows.

Read that definition again. **The 95th percentile is an impact. The 5th
percentile is whatever lies between the impacts.** So the cheapest way to
maximise the score is to put *nothing* between them.

Measured directly, with the film's own 777 percussive impacts held fixed and only
the material between them varied, all at matched level:

| the passage = impacts + | G-EVENT dB | AMI | audibility dB |
|---|---:|---:|---:|
| **NOTHING** (what shipped) | **27.17** | 0.8037 | **−140.71** |
| an audible machine-room ambience | **12.62 → FAIL** | 0.8179 | +14.56 |
| a hair dryer | 5.48 | 0.3309 | audible |
| a drone | 0.26 | 0.1807 | audible |

The bar was 13.7 dB. **Silence scored 27.17 — 13.5 dB clear of the bar and the
best score in the table — and a genuinely audible machine scored 12.62 and
FAILED.**

The consequence was not hypothetical. A tuning loop had been walking a gain
parameter downhill in search of a better G-EVENT score, and it arrived. The
delivered master's quiet passage measured **26.4 dB SPL** at domestic playback
level, with **0 of 29 third-octave bands above the threshold of hearing** in a
quiet room. A typical living room's own noise floor is about 15 dB louder than
the entire passage.

**It was caught by a listener.** The client wrote: *"now beat 1 i dont hear
anything until the tubes play."* Every gate in the suite said the passage was
fine.

**Why every gate said that** is the second half of the case, and it generalises
much further than audio: **every quality gate in the file was RELATIVE.** Each
one measured structure *within* whatever it was handed — ratios, spans,
correlations, fractions. Not one of them measured an absolute quantity. So
**digital silence scores perfectly on all of them**, because silence has
excellent ratios.

The fix was to add the first absolute measurement in the file, and to give it
**two limbs that cannot be traded against each other**: is the material above the
threshold of hearing, and is it articulated over time. The reason for two is
visible in the table above — silence has the second-best articulation score in
the corpus *and* is inaudible; the hair dryer is plainly audible *and* has nearly
the worst articulation. A single composite number could be gamed by trading one
against the other. Two independent limbs, both required, cannot.

**No threshold was moved.** G-EVENT was not retired and is not wrong about hair
dryers. It measures *trough depth*, and the honest finding is that **trough depth
is not eventfulness** — the metric was correct and the inference drawn from it
was not.

**The general lesson.** *For any metric you intend to optimise against, ask what
signal maximises it, and check that that signal is something you would ship.* If
the answer is "nothing", "silence", "an empty set" or "a constant", you have
built a gradient pointing at a degenerate case, and something will eventually
follow it.

---

### II.2 — A recurrence gate that pure randomness fails

**Source:** R2-4085, `docs/STAGING-R2-4081-to-R2-4140.md`.

A gate looked for spectral lines that *recur* across separate bursts of sound —
the signature of a fixed resonance being excited over and over, which is what
makes a synthetic room sound synthetic. Its bar: no more than 0.35 of observed
peaks may recur in three or more bursts.

Someone measured the chance level. On **independent** peaks drawn at random,
sharing nothing by construction:

| bursts | 8 | 12 | 20 | 40 | 60 |
|---|---:|---:|---:|---:|---:|
| recurrence | 0.031 | 0.162 | 0.277 | **0.638** | **0.835** |

**At forty bursts, pure independence fails a 0.35 gate.** It is a birthday
problem: with enough draws from a bounded set of resolvable frequency bins,
coincidences are compulsory. The film's own material read 0.600 and the
hand-built positive control read 0.666 — both for this reason, not because either
had a defect.

Two corrections were made and **the bar itself was not touched**: the number of
bursts examined was capped at 16, where chance is about 0.22; and a line now
counts as recurring only if it appears in more bursts than the most-recurring
line of an independent draw does 19 times out of 20 — a family-wise error rate
over all ~341 resolvable bins, not a per-bin test.

**The general lesson.** *A threshold on a count, a fraction or a coincidence rate
is meaningless until you have measured what it reads on pure noise.* If your gate
fails randomness, it is not measuring structure; it is measuring how many
observations you fed it.

The same entry records the sibling case: another limb of the same gate had a bar
of **1.5×** for an echo statistic whose measured value on material with **no room
and no delay of any kind** was **10.44×**. The statistic separates echo from
no-echo by an order of magnitude and works fine; the bar sits an order of
magnitude below the no-echo case, so it fails everything. It was recorded as open
and **deliberately not moved**, because *"moving three bars on evidence gathered
while doing something else is how bars get loose."*

---

## III — The instrument was calibrated against the artefact it judges

### III.1 — "The limit is the midpoint between what THIS master reads and what the adversary reads"

**Source:** the rule at R2-2222 in `docs/STAGING-R2-2221-to-R2-2280.md`; its
diagnosis in `docs/audio-rebuild3/SPEC-ENGINE-AND-GATES.md` §2; its ban at
R2-4041 in `docs/STAGING-R2-4021-to-R2-4080.md`.

Every threshold in the audio suite was set by one rule, stated in the code:

> the limit is the midpoint between what this master reads and what the adversary
> reads, rounded to 0.05

It is a tempting rule, and the version of it in R2-2222 is not lazy work. The
"adversary" was a synthesised hair dryer plus the two masters the client had
already rejected; the placements were bootstrapped with real standard errors; the
resulting gate correctly failed both rejected masters and failed synthetic
white noise on all ten limbs. It looks like a properly validated instrument.

It is still self-referential, and the consequence is exact:

> **the pass mark is a function of the artefact under test, so a film can only
> fail by being worse than the film that calibrated the limits.**

On the beat-1 scale, pure noise read 0.975, the drawn line 0.850, and the
delivered film 0.707. The film is guaranteed to be on the right side of a line
drawn from itself. What that gate could detect was *regression relative to the
calibrating artefact* — a genuinely useful thing — while what everyone believed
it detected was *quality*. Three rebuilds shipped and were rejected under it.

The fix is the most directly reusable thing in this document. Every threshold in
the replacement suite is a frozen record carrying a **provenance tag**:

```
Threshold(key, value, units, source, note)     source ∈ {physics, published, control-derived}
```

and an audit function **rejects `source=artefact` by name**, before any gate is
allowed to run:

```
X.midpoint_between_master_and_adversary  source=artefact
  -> BANNED: a threshold derived from the artefact under test. This is
     verify.py:816's rule and it is the reason three rebuilds shipped
     without anyone knowing they were bad.
```

A second rule fires alongside it: **a threshold with no derivation note is itself
a violation** — *a bare number is not a threshold*. The registry at the time of
writing held 25 thresholds and 0 violations: 8 from physics, 1 from published
literature, 16 derived from controls.

**The general lesson.** *Record where every threshold came from, mechanically,
and make "from the thing under test" an error rather than a habit.* Almost
everybody knows not to calibrate a test against its subject. Almost nobody has a
mechanism that notices when they have.

---

### III.2 — A hair dryer aimed into a rack of tubes, passing with more margin than the film

**Source:** R2-4040, `docs/STAGING-R2-4021-to-R2-4080.md`.

The direct consequence of III.1, and the reason 629 lines were deleted rather
than retuned.

The `harmonic` gate existed to detect exactly one complaint: that the soundtrack
sounded like a hair dryer. Measured against a literal adversary — broadband noise
blown into a rack of resonant tubes, synthesised for the purpose — **the hair
dryer passed the gate's own bar with more margin than the real film**: 0.481
against the film's 0.708, on a limit of 0.85 where lower is better.

The same gate scored a two-second block tiled repeatedly at **+43.814 dB**,
identically on every section of the film, against the delivered film's best
section at +8.059 dB. It rated a tape loop **5.4× better** than the best real
material in the project.

The entry's conclusion is the cleanest statement of this document's thesis:

> **An instrument that reads the same whether the defect is present or absent
> cannot be fixed by moving its threshold.**

**A note on the deletion.** 629 lines were removed and a block comment left in
their place **with the measured reason for each**, so that the next person finds
the reasoning and not a hole. That detail matters: a deleted gate with no record
gets re-added by the next well-meaning engineer.

---

### III.3 — A positive control anchored to the defect, which the fix then took away

**Source:** R2-115, `docs/DEFECT-LOG-R2.md`.

A gate that detects a rolled camera proved it could fire by pointing at a live
data file known to contain the roll. When the roll was fixed, **the arm proving
the gate works stopped working** — because its evidence was the defect.

A control anchored to a live artefact expires the moment the artefact is
repaired, and it expires **silently**, in the direction of everything passing.
The sibling entry R2-110 records the same class from the other side: the gate
guarding every prop placement in the project had control files that had existed
since the day it was written, and **no test battery had ever opened them**.
Wired in at last, they read `PLACEMENT_FAIL` and `PLACEMENT_CLEAN` respectively
— both correct, both never once consulted.

And R2-110's far-negative control, when finally run, logged its own uselessness:
`tested 1 objects; 1 rejected on bounding box; 0 measured per-vertex`. It could
catch a gate that *invents* violations and nothing else. The failure the project
actually had was **over-rejection**, which that control was structurally
incapable of seeing. The replacement is a *near-miss* control positioned from the
live contract on every run, so it tracks the corridor instead of drifting out of
relevance.

**The general lesson.** *Controls must be frozen artefacts or regenerated from
first principles — never live ones.* And a control that "passes" tells you
nothing unless you also assert that it passed **for the right reason**: the
project's control-assertion tool now fails a control that passed *without the
gate looking at its geometry at all*.

---

## IV — The instrument's own arithmetic destroyed the reading

### IV.1 — A limiter reporting 0.124 dB of gain reduction while removing about 22 dB

**Source:** `docs/audio-rebuild3/SPEC-CHAIN-AND-GLASS.md` §; witnessed in code at
R2-4031 and fixed at R2-4037, `docs/STAGING-R2-4021-to-R2-4080.md`.

A limiter is a device that turns the sound down when it gets too loud. The build
report said it had turned things down by at most **0.124 dB** — an inaudible
amount, the signature of a mix that needs no help.

Recovering the true gain curve — by dividing the delivered file by the sum of its
own 14 component tracks — showed a **32.2 dB swing** in total chain gain between
the quiet opening and the loud impact. At most 10 dB of that is attributable to
the slow program gain, which is hard-bounded. **The limiter was pulling about
−22 dB at the impact.**

**The report was wrong by 22 dB**, and the mechanism is four lines of code:

```
master.py:633-641   runs the limiter up to 8 times in a loop
                    and reassigns `gr` on every iteration
```

Each pass is gentler than the last, because each pass has less left to do. The
per-pass reductions on the delivered file were:

```
-19.93, -3.89, -2.20, -1.13, -0.63, -0.40, -0.22, -0.12 dB
```

**The report published the eighth.** A second, independent 8-pass loop ran at a
different sample rate with the same bug. Cumulative per-sample gain reached a
minimum of −28.27 dB; 20.65% of the film was pulled down more than 1 dB and
12.15% by more than 6 dB.

**The most expensive consequence was not the audio.** An earlier diagnosis in
this project read `max_gain_reduction_db = −0.124`, declared the limiter
**"REFUTED, clean"**, and moved on. That refutation was carried forward into
subsequent work. A later pass had to explicitly retract it and record that it
must not be inherited.

**The general lesson.** *A reported extremum computed inside a loop is a bug
waiting to happen, and the direction of the bug is always flattering.* The
variable holding "the worst we saw" must be reduced with `max`/`min`, never
assigned. Every iterative refinement loop has this shape: the last iteration is
by construction the one that had the least work to do, so reporting it reports
the algorithm's convergence rather than its effect.

The fix removed the loop entirely. The makeup gain is now **solved for** rather
than accumulated, so the delivered file goes through the limiter exactly once
however many attempts it took to find the right setting, and the reported figure
is the maximum over every attempt. If one pass cannot hit the target within 3 dB
of reduction, **the mix is wrong and the build says so** rather than iterating
until it stops complaining.

---

### IV.2 — A limiter whose gain path ran backwards in time

**Source:** R2-4032, `docs/STAGING-R2-4021-to-R2-4080.md`.

Same subsystem, a genuinely surprising bug, and one that will be familiar to
anyone who has ever reached for a convenient filtering function.

```python
g = minimum_filter1d(need, size=2*rel+1)          # rel = 120 ms, CENTRED
g = sosfiltfilt(butter(2, 1000/release_ms), g)    # ZERO-PHASE
```

Both operations are **symmetric in time**. A centred minimum filter looks 120 ms
into the future as well as the past. `filtfilt` — the standard "zero-phase"
filter, used precisely because it introduces no phase distortion — achieves that
by running the filter forwards and then backwards.

Measured on a single-sample impulse: **the gain began falling 161.4 ms before the
peak** and recovered 161.4 ms after it — a **322.9 ms hole with the transient
sitting in the middle**, reaching −14.10 dB deep.

That is not a limiter artefact. It is a limiter running in reverse, and it ducks
exactly the material the ear judges an impact against — carving a hole around
every single one. The film's impacts measured 6.90 ms of rise time against a
2 ms target, and this stage is where most of it went.

| | before | after |
|---|---:|---:|
| gain dip **before** the peak | **161.4 ms** | **1.74 ms** |
| total hole | 322.9 ms | 177.1 ms, **all of it after** |

**The general lesson.** *"Zero-phase" means acausal.* Any signal-processing
routine described as zero-phase, symmetric, centred, or two-pass runs backwards
over your data, and if the output is a *control* signal — a gain, a gate, a mask,
a decision — that is not a subtle phase artefact, it is the control acting before
its cause. The test that finds it takes one line: feed the system an impulse and
look at what happens *before* it.

---

### IV.3 — Two processes staging writes through the same temporary filename

**Source:** `vast-render/docs/incidents.md` #169, "One more defect, found by
writing that proof".

A shared list of condemned machines is written by several processes. Each writes
to a temporary file and then atomically renames it into place — the standard safe
pattern. The temporary file was named `bad_hosts.json.tmp` **for every writer**.

So two processes staged their writes through the *same* scratch path, and one
`replace()` moved the other's file out from under it. The loser's write died with
`FileNotFoundError`, logged as a warning, and otherwise invisible.

Two processes each condemning 60 hosts, on the unfixed code, run three times:

```
run 1   109/120 survived, 11 lost
run 2   120/120,           0 lost
run 3   117/120,           3 lost
```

**Run 2 is the point of this entry.** The race is timing-dependent, so a test
would have passed clean on the second attempt and the guard would have looked
fine. A single green run proves nothing about a race; it is a coin landing heads.

Fixed by `bad_hosts.json.<pid>.tmp` — which makes the collision impossible even
on the degraded path where the lock cannot be taken — plus a cross-process file
lock. Post-fix: 120/120, three runs out of three.

**The general lesson.** *A test that a race passes half the time is not evidence
it passes.* Run concurrency tests to a count, record the distribution, and treat
a clean run as one sample rather than as a verdict. And check every temporary
filename in a multi-writer system for the writer's identity — this is a
one-character-class fix that is trivially auditable across a codebase.

---

### IV.4 — A detector whose statistic cancels on the defect it detects

**Source:** R2-181, with R2-173, `docs/DEFECT-LOG-R2.md`.

A tool detected surfaces built upside down by grouping geometry into connected
pieces and taking each piece's mean normal — its average facing direction.

That works only where the walking surface is its own connected piece. **A welded
solid slab puts the top face, the underside and the edges in one piece, whose
mean normal cancels to approximately zero.** A bridge deck with the defect
reported "0 flat pieces". Regrouping over connected runs of near-horizontal
triangles *of the same sign* found the real answer across 13 objects and
30,943,406 triangles.

The companion entry, R2-173, is sharper still. A repair pass flipped 1,310
pieces and drove the headline metric `inward_area_frac` from **0.3436 to exactly
0.0**, while the single largest offending piece **stayed the largest offender and
got marginally worse** (26 → 28 of 500 test rays).

> **The headline metric reached zero while the actual defect got marginally
> worse. A summary statistic that a fix can satisfy without touching the fault is
> not a verification.**

**The general lesson.** *Any statistic formed by summing signed quantities can be
cancelled by the defect's own symmetry.* Means, net flows, signed volumes and
signed areas all have this property. When the fix drives your headline number to
a suspiciously round zero, go and look at the worst individual case; it is the
only thing that cannot be averaged away. (R2-173 also records that the
replacement tool's *own first version* wiped the scene before collecting data and
printed `OK` on an empty file — see family V.)

---

## V — The instrument had no case to answer

### V.1 — A verification that could never fail

**Source:** R2-012, `docs/DEFECT-LOG-R2.md`. The shortest entry in this
catalogue and the purest specimen in it.

```python
(ob.matrix_world.translation - ob.matrix_world.translation).length > 1e9
```

A value minus itself — identically zero — compared against a number nothing
reaches. It printed a reassuring `0 stragglers` and proved precisely nothing.

The author's own note: two independent audits of this project's render broker had,
*that same night*, flagged "verification theatre" as a bug class in its own right.
**"I then wrote one."**

> **A check that cannot fail is worse than no check, because it converts an
> unknown into false confidence.**

---

### V.2 — Two gates reporting PASS on an empty set

**Source:** R2-018, `docs/DEFECT-LOG-R2.md`.

```
collision_gate.py  ->  "0 clusters, 0 environment objects"
                   ->  "STAGE RESULT: COLLISION_CLEAN"

depth_probe.py     ->  0 surfaces found, no CAR collection
                   ->  "STAGE RESULT: DEPTH_PROBE_OK"
```

Both statements are true and both are worthless. The gates tested objects against
an environment; the scene being checked contained neither, so zero pairs were
tested and none of them intersected. **Zero of zero passed.** A reader scanning
the run banks a green verdict as evidence the scene is sound.

The fix is a rule that has since propagated through the whole project:

> **No gate may emit a pass without naming what it tested. An empty test set is a
> failure to test, not a successful test.**

Both tools now refuse: they name what they could not find, state plainly that
this is *not* a pass, write `"vacuous": true` into their report, and exit with a
distinct `_VACUOUS` status — a third outcome alongside pass and fail. That third
outcome is the load-bearing part. Two-valued reporting has nowhere to put "I
could not measure this", and it always ends up filed under "fine".

---

### V.3 — A tool that had never once executed, in a bar that reported it as passing

**Source:** R2-2821 and R2-2824, `docs/STAGING-R2-2821-to-R2-2880.md`; the
repaired verdict at R2-3120, `docs/STAGING-R2-3121-to-R2-3180.md`.

This is the case where the *verification harness itself* had the disease, and it
is the best single argument in the collection for auditing your test runner.

The film's ship-or-don't-ship gate was a shell script. One of its checks:

```bash
python3 tools/rig_preflight.py 2>&1 | tail -12
echo "  rig_preflight exit=$?"
```

Three independent failures stack in those two lines:

1. **`rig_preflight.py` needs the 3D application's Python module and cannot run
   under plain `python3` at all.** It dies with `ModuleNotFoundError: No module
   named 'bpy'` before reaching its first measurement.
2. **`set -o pipefail` is not set**, so `$?` is `tail`'s status, not the tool's.
   The tool exits 1; the bar prints `rig_preflight exit=0`.
3. **Nothing reads either number.** No verdict line is produced at all, and a
   caller grepping for the verdict sees silence — *and silence and a pass were
   spelled the same way.*

The tool's own docstring says *"A detection that does not reach an exit code is a
rumour."* It had been a rumour since the day it was written.

Run properly for the first time, it produced three findings and exit 1: the
comparison rig used to judge the film's lighting was **139.61° out in bearing**
and **0.58 stops out in exposure**. It had been reported as part of a passing
verdict for four generations of the film.

Then an audit counted every assertion the script makes:

> **37 assertions. 24 counted. 13 silent.**

The 13 included: every external tool's verdict, consumed by `| tail` and judged
by nobody; the levelling identity block, printed and judged by nobody; and item
35 — the suite's **only negative control**, whose own header reads:

> *If film10 ever comes back PASS the instrument is broken and every PASS above
> it is vacuous.* **Keep it.**

**It was kept. It was piped into `tail -12` for four film generations and its
verdict went in the bin.**

Six more of the 24 counted assertions were *conditionally* silent — they sat
behind `if key in measurements:` with an `else: print("NOT REPORTED")`, so a
missing measurement removed a check without removing a pass. One upstream tool
simply never emitted five of the keys it was asked for, including **every key
that names the delivery format**: resolution, clipping planes, camera. The script
printed 15 lines and counted 10.

The repaired harness expresses the same 37 assertions as 40 rows with three
verdicts (`OK`, `FAIL`, `UNMEASURABLE`), runs external tools as
list-argv subprocesses **with no shell and therefore no pipe**, and judges them
on their printed verdict because the 3D application exits 0 on an uncaught
exception. Its rule is one line:

> **A check that cannot be evaluated must never be indistinguishable from one
> that passed.**

The ship candidate's verdict on first honest run:

```
was:  VERIFY23_BAR_PASS   "24 checks, 0 failures"
now:  40 rows, 34 OK, 4 FAIL, 2 UNMEASURABLE, exit 1
```

And when the negative control was finally executed rather than discarded, it
failed with exactly its standing 27 findings, on the same run of the same
instrument that passed the ship candidate one minute earlier — which is what
makes the pass mean something.

**The general lessons**, and there are four distinct ones:

* *`| tail`, `| head` and `| grep` in a check discard the exit status.* Without
  `pipefail` you are reading the pager's opinion of the world.
* *Run your check tools as argv lists with no shell.* Every one of these
  failures needed a shell to happen.
* *Interpreters exit 0 on uncaught exceptions in some embedded contexts.* Judge
  on a printed verdict token as well as a status, and make the token and the
  status come from one expression so they cannot disagree.
* *Audit your harness by counting.* "How many assertions does this script claim
  to make, and how many can it act on?" is a question with a number for an
  answer, and here the number was 24 out of 37.

---

### V.4 — Bounds that had never executed

**Source:** `vast-render/docs/operations.md`, "The disk preflight".

A remote machine's scene cache was capped at 12 GB. The cap had **never fired**.
Measured live, nine hours into a campaign:

```
/workspace/scenes      8.8 G  across 41 cached scenes, none ever evicted
```

Nothing was broken in the sense of throwing an error. The cache had simply never
reached its ceiling, so the eviction code that existed had never run once — and,
in the entry's words:

> **A bound that has never executed is not a bound, it is an untested branch.**

Half an hour later the same cache was 11.5 GB across 48 scenes, because the
campaign was pushing a new ~882 MB scene every two minutes. The eviction path was
about to run for the first time ever, in production, at speed.

The replacement is three bounds of deliberately different kinds: a **policy**
budget (unmet → evict, then warn), a **measured** disk (unmet → lower the budget
silently), and a **physics** reserve (unmet → the job fails outright). The hard
one is free space, because running out of it is not a clean failure anywhere in
the pipeline: the renderer does not refuse, it writes a short file — the same
defect class as a truncated transfer, which this project had already lost a frame
to.

The same document records a sibling: a fleet retirement policy that *"has never
fired on any instance"* because the longest instance life was 10.7 h against a
12 h retirement. Both are the same observation — **an unfired branch is an
unwritten branch until proven otherwise**, and the way to prove otherwise is to
provoke it deliberately.

---

## VI — The verdict existed and nothing was wired to it

### VI.1 — A control that detected the problem and was overruled by its own summary line

**Source:** R2-1091 block, `docs/STAGING-R2-1091-to-R2-1120.md`.

A tool computed camera focus decisions. Its self-test printed:

```
solver AGREES at the stations   SKIP  path file and sheet are different
generations (mean station offset 4.612 m)
...
STAGE RESULT OK r2791_focus_selftest
```

The control **detected** that the tool was reading a camera path 4.6 metres out
of date, reported `SKIP`, and the stage summary printed `OK` anyway. The stale
data meant that on **369 of 792 frames — 46.6%** the shipped focus decision would
have put the subject outside its own depth of field.

The entry's own classification is precise: this is *"the 'guard that cannot fire'
shape with an extra step: it fired, and nothing was wired to it."*

The recommendation given to the tool's owners is worth quoting because it refuses
the comfortable middle option:

> Make the `SKIP` fail the stage, **or delete the control**. A control that skips
> into `OK` is worse than none.

**The general lesson.** *`SKIP`, `INAPPLICABLE`, `N/A` and `WARN` are the
dangerous verdicts,* because they are the ones with no defined consequence. Every
such outcome needs an explicit answer to "and then what?" — and the honest answer
is usually "fail the run", because an unmeasured check is an unknown, not a pass.

---

### VI.2 — A fix that was in the tree and not on the box

**Source:** `vast-render/docs/agents.md`, `rq drift`; and
`docs/MASTER-RUNBOOK.md` gate 7.

Twice, in two subsystems, the same thing:

* On 2026-08-07 an 8 GB file was pushed three times to a path nothing read, and
  the refusal written to make that terminal **never fired** — because the
  long-running service had started at 05:51 and the fix landed at 07:45.
  *"Everyone debugging it, including the agent who wrote the fix, was reading a
  file nothing was executing."*
* A minimum-RAM constant used to select rental hardware was read **at import
  time** and bound as a default argument. The value was raised on disk; every
  already-running service still held the old one. The runbook's own warning:
  *"the fix is real, the file is correct, and the process in memory is the old
  one"* — and it fails silently, with a confident log line.

The tool built in response reads `/proc`, comparing each running service's start
time and bytecode cache against the source tree file by file — **never the
service's own HTTP API**, on the explicit grounds that *"is that process running
the code I am reading?" is the one question a process running the wrong code can
answer wrongly.* Its three verdicts are `STALE`, `ok`, and `?` for what cannot be
determined, and **`?` is never rendered as `ok`**.

> **A fix in the tree and not on the box is a fix that does not exist.**

---

### VI.3 — A teardown command that failed before destroying anything

**Source:** R2-3927, `docs/STAGING-R2-3901-to-R2-3960.md`.

```
$ ./fleetctl down
usage: vastctl [-h] {offers,status,reap,destroy} ...
vastctl: error: argument cmd: invalid choice: 'down'
exit=2
```

The command that releases rented GPUs failed with an argument-parsing error,
because it reached into a sibling module that re-parses **the parent process's
`sys.argv`**. It failed *before* destroying anything — confirmed by querying the
provider's API directly, which still showed a live card.

The operator's note:

> **Had I trusted the command's own failure as "nothing to tear down", a card
> would have been left rented.**

**The general lesson.** *A non-zero exit from a destructive command is
ambiguous.* It can mean "I refused", "I failed before acting", "I failed
half-way", or "I acted and then failed to report". Only an independent query of
the thing itself distinguishes them — here, the provider's API rather than a
local state file. The teardown was completed with a different, supported command
and then *proved* against the API: `no instances on this account (checked the
vast.ai API, not a local state file)`.

---

## VII — The instrument measured the wrong quantity

### VII.1 — A memory guard that polled current usage and so could not see intent

**Source:** R2-4020, `docs/STAGING-R2-3961-to-R2-4020.md`, with the 0.5-second
timeline preserved at `docs/r2_4020_waitmem_timeline.tsv`.

Five heavy processing passes ran against a 10.9 GB scene file on a machine with
11.9 GB of RAM. The fifth was wrapped in a proper mutual-exclusion lock, with a
comment saying exactly why:

> Wrapped in the build lock because two ~10 GB opens on an 11 GB box do not run
> at half speed — one of them gets OOM-killed.

The four above it used a local helper instead:

```bash
waitmem () {
  for i in $(seq 1 960); do
    A=$(free -g | awk '/^Mem:/{print $7}')
    [ "$A" -ge 5 ] && { echo "[gate] ${A} GB available, starting $1"; return 0; }
    sleep 30
  done
}
```

One pass was then instrumented, polling resident memory every 0.5 seconds:

| | |
| --- | --- |
| **peak resident memory** | **7,847 MB = 7.66 GB** |
| available memory at start | 7,382 MB |
| **available memory at trough** | **264 MB** |

One pass takes the machine to 264 MB. Then the guard's verdict — which is a pure
function of the number it reads — was evaluated against the **recorded, real**
memory trace of that pass:

```
t=   0.0s  holder_rss=     0 MB  mem_avail= 7382 MB   waitmem: START
t=   2.5s  holder_rss=  1050 MB  mem_avail= 7155 MB   waitmem: START
t=  11.5s  holder_rss=  4312 MB  mem_avail= 6081 MB   waitmem: START
t=  16.5s  holder_rss=  6379 MB  mem_avail= 5495 MB   waitmem: START   <-- last
t=  17.0s  holder_rss=  6938 MB  mem_avail= 5079 MB   waitmem: wait
```

**For the first 16.5 seconds the guard says START** — while the process standing
next to it is already committed to 7.66 GB and has merely not touched it yet.
And the guard sleeps **30 seconds** between polls, so *its sampling interval is
nearly twice the width of the window in which it is wrong.* **It cannot even see
itself be wrong.**

The two guards were then asked the same question at the same instant, with a real
second pass launched against a real holder:

| wall clock | holder | `waitmem` says | the lock says |
| --- | --- | --- | --- |
| 17:18:53 | resident, 2.4 GB, lock held | `wait 3` | **QUEUED** |
| **17:18:58** | **resident, lock held** | **`START 5`** | **QUEUED (refused)** |
| **17:19:03** | **resident, lock held** | **`START 8`** | **QUEUED (refused)** |
| 17:19:08 | gone, lock released | `START 8` | RAN |

Same machine, same second, one guard green and one guard red — **and the red one
is right.**

> **A memory poll cannot see intent.** It samples what is *allocated now*; the
> quantity that decides whether the machine survives is what is *intended*. Only
> a lock carries intent, because the holder registers before it allocates.

**The general lesson.** This generalises past memory to every resource with a
ramp: disk, file handles, connection pools, GPU memory, rate-limit budget.
*Admission control on a sampled level always admits during the ramp.* If a
consumer's eventual demand is knowable, it must **declare** it before acquiring
it, and admission must be decided against declared demand. Sampling is for
observability, not for admission.

Two details of the fix are worth stealing. First, the naive way of wrapping the
passes in the lock — `bash -c "..."` to get the output redirect inside — would
have hidden the interpreter binary from the lock's own wrong-binary refusal,
**silently disarming a safety check while adding one**. Second, the lock printed
its own verdict line into logs that a downstream tool scans for verdicts, and
that tool fails any log containing two — so the naive wrap would have turned four
*passing* rows into failures, reporting a defect that did not exist. Both were
caught by regression tests written before the change shipped.

---

### VII.2 — An engine-quality metric that did not respond to two rebuilds of the engine

**Source:** R2-2223 and R2-2224, `docs/STAGING-R2-2221-to-R2-2280.md`.

Someone claimed two sections of the film were defective, citing a harmonic
quality metric reading +0.09 dB and +0.16 dB where clean sections read much
higher. **Every number in the claim was correct.** The conclusion was not, and
the measurement that settles it is one table — the same metric on four
successive masters, with two complete rebuilds of the engine synthesiser between
them:

| section | 2 Aug | rebuild 1 | rebuild 2 | now | **movement** |
|---|---:|---:|---:|---:|---:|
| flying lap | −0.71 | −0.72 | +6.68 | +5.84 | **7.40** |
| launch | +1.36 | +1.27 | +5.63 | +8.06 | **6.79** |
| transit | −0.55 | −0.59 | +3.57 | +3.91 | **4.51** |
| **the ending** | +0.40 | +0.40 | +0.35 | +0.13 | **0.27** |
| **the glass breach** | +1.49 | +1.45 | +0.08 | +0.05 | **1.44** |

> **A number that does not respond to two rebuilds of the engine is not measuring
> the engine.**

The reasons were then established independently for each. In the breach section,
the metric was computing a ratio on **0.0183%** of the section's energy — one
part in five thousand — because breaking glass is broadband on purpose and a
line-spectrum detector cannot find a line spectrum in 995 randomly-timed
inharmonic rings, because there is not one. In the ending, the band being scored
was **86.12% crowd noise** and only **0.93% engine**; the metric was measuring a
grandstand, and measuring it correctly.

**The general lesson.** *A time series of your metric across releases is a free
and extremely strong test of whether it measures what you think.* If a number
does not move when you rebuild the thing it names, it is measuring something
else, and you can establish that without knowing what.

---

### VII.3 — "Suspiciously fast" is not a detector

**Source:** R2-357, `vast-render/docs/linked-libraries.md`.

Recorded here as a **negative result**, because it is the intuition everybody
reaches for after case [I.4](#i4--a-blank-frame-detector-defeated-by-a-strip-of-sky), and it does not work.

The empty render came back in 0.83 s. So: flag renders that finish
suspiciously fast. Modelling every completed job's throughput as
`pixels × samples ÷ seconds`, the known-bad job ranked **1,645th of 1,788** —
among the *slowest*, because it was a low-resolution, low-quality preview.

> It was caught because a human knew what that scene should cost, not because
> 0.83 s is anomalous.

**The general lesson.** *An anomaly detector needs a population in which the
anomaly is anomalous.* Across a heterogeneous workload, "fast" is a property of
the request, not of the failure. Recording a negative result like this one is
what stops the next engineer spending a week rebuilding it.

---

### VII.4 — A relief check that cannot tell paint from geometry

**Source:** R2-060, `docs/DEFECT-LOG-R2.md`.

A check decided whether surface detail was real modelled geometry or merely
painted on. Measured directly:

> **A four-vertex flat quad with z ≡ 0 — no modifiers, no displacement, no normal
> map, verified in the file — scores 0.6308 against real 2 mm ribs at 0.6082.**

A flat plane outscored actual geometry. The mechanism: after the check's
band-pass filter, a sharp change in paint colour and a real lip-plus-shadow leave
**the same bipolar signature at the same spacing**. The statistic is genuinely
blind to the distinction.

The existing decoy control had been passing only by luck — its stripes ran 32°
away from the direction the real ribs are laid, and that misalignment split the
response between two terms that cancel. Rotating it to match moved its score from
0.0231 to 0.6308, **orientation alone**, with the graphics device ruled out as a
confound by re-rendering on CPU.

Two things about the repair are exemplary. First, the obvious fix — gate on the
correlation between two differently-lit renders — **did not survive its own
controls**: real 3 mm bolt heads read +0.1003 and a plain grey plate read
−0.8608, because real relief carries a light-*invariant* component (a rib's flat
top is bright from either side). A statistic that puts a smooth cylinder
(+0.9193) and a painted one (+0.8629) in the same bin cannot decide anything, so
that quantity is now **measured and reported but not gated**. Second, when the
working fix landed, all eight previously-passing items were **re-examined under
one shared pixel mask computed from the shipped image**, so that no arm of the
experiment could move its own goalposts. Six passes were real; two were
inconclusive; five of the six real ones were also inflated by paint — *verdicts
safe, numbers not clean*, which is a distinction most projects never bother to
draw.

---

### VII.5 — A gate with no term for the thing its positive control demonstrates

**Source:** R2-151, `docs/DEFECT-LOG-R2.md`.

A camera-path gate was reported as passing next to a known-bad path, as evidence
that the gate works. The known-bad path contains **28 fully inverted frames and
−122.93° of roll** — a camera upside down — and a different gate fails it with 32
bad frames.

The camera-path gate returned:

```
>> STAGE RESULT: PASS — 0 FAIL, 5 advisory
```

**The same verdict, and the same five advisories, as the good film.** The gate
measures speed, rotation rate and path kink. **It has no roll or up-vector term
at all**, so a camera that is upside down for 28 frames is invisible to it.

The gate is not broken. The *claim made about it* was: a pass reported next to
that path as its "positive control" asserts nothing. Two paths that do
discriminate were identified and either should be used instead.

**The general lesson.** *A positive control is only a control for properties your
instrument actually computes.* "We ran it against a known-bad input and it
behaved as expected" means nothing unless the known-bad input is bad **in a
dimension the instrument has a term for**. The way to check is embarrassingly
direct: read the instrument's variable list and ask which of the defect's
properties appear in it.

---

## Corrections

Two claims that circulated as project folklore did not survive contact with
their source entries. A third that was checked and *did* hold is noted at the
end, because "we verified it and it was fine" is also a result.

**1. "The host blacklist's TTL was shorter than the interval between its uses, so
every entry expired before the next lookup and it never once prevented
anything."** — *Substantially wrong, and the true version is more interesting.*

`vast-render/docs/incidents.md` #169 records two **independent** causes, and TTL
is the second one. The primary cause is **scope**: the list of condemned machines
lived in one process's memory and nothing published it. Across a seven-cycle
render, **4 of 10 condemnations were one process rediscovering another's
verdict.** The incident that cost a job has a 12-minute gap between one process
condemning machine 58073 and a sibling renting it — *far inside any TTL.*
**Scoping alone caused it.**

The list did prevent things: `state3/bad_hosts.json` contains an entry written
when a rental request returned HTTP 400, and that process never bought that offer
again. What made it look ineffective is that *two other processes* bought the
same offer within half an hour, each rediscovering a verdict sitting on disk in a
directory it never reads. **The 400 was recorded. Nobody could see it.**

The TTL claim is also mis-attributed. The constant the incident was filed
against, `Broker.BLACKLIST_TTL_SEC = 6 * 3600`, governed a **second, redundant
copy** of the list whose loader only ever *added* entries — it could not expire
anything. The TTL that actually decided re-renting was `fleet.BAD_HOST_TTL_SEC`
at **24 h**, against measured defect lifetimes of **24 h 02 m and 61 h 19 m**. So
the true statement is: *the TTL was shorter than the defect it records*, and
*two stores of one fact had drifted apart, one of them dead.*

That drift had its own silent bug, which is worth more than the headline: the
merge used `set.__ior__`, implemented in C, which does **not** call an overridden
`add`. Restored entries therefore entered the set with no timestamp, were never
persisted by their owner, and got re-stamped with `now` by the next unrelated
save — **silently restarting the ban clock on a host condemned hours earlier.**

The rest of the folklore holds: it did burn a job's last retry attempt. A process
rented a machine its sibling had condemned twelve minutes earlier, spent five
minutes rediscovering the same failure, and ended the pass having rendered zero
frames. Zero-progress passes spend an attempt; **it was the third of three**, and
the job failed with 101 frames of a 2,978-frame film unrendered.

**2. "The memory guard green-lit a fourth 7.66 GB process while three were still
ramping."** — *Overstated.* R2-4020 records **one** instrumented holder and
**one** contender, demonstrated live. Four passes were governed by that guard in
the script, but the measured demonstration is a pair. The corrected version is in
[VII.1](#vii1--a-memory-guard-that-polled-current-usage-and-so-could-not-see-intent) and loses nothing: one pass alone takes an 11.9 GB machine to 264 MB
of headroom, so admitting a second is already fatal.

**The specific phrasing matters**, which is why correction 1 is this long. "The
guard never once prevented anything" and "the guard's verdict never reached its
siblings" describe the same green dashboard and demand entirely different fixes:
the first says raise the TTL, the second says publish the store, lock it, and
re-read it before use. The incident's fix does all four, and the entry is explicit
that a shared file **nobody re-reads is still a private file** — one sibling had
been running for hours when the other condemned the machine, so a load that
happens only at construction misses the verdict by exactly as much as a separate
file did.

**Checked and upheld:** the claim that a limiter reported 0.124 dB while removing
about 22 dB. Two independent derivations agree — decomposing the recovered gain
curve bounds the limiter's contribution at about −22 dB at the impact, and the
per-pass list recovered from the shipped file starts at −19.93 dB and ends at
−0.12 dB, which is the number the report published. See
[IV.1](#iv1--a-limiter-reporting-0124-db-of-gain-reduction-while-removing-about-22-db).

---

## Synthesis

Twenty-six cases, seven mechanisms. What survives when you line them up?

### The threads that hold

**1. Instruments were validated against the artefact, and only against the
artefact.** This is the deepest thread and it has two forms. The explicit form is
[III.1](#iii1--the-limit-is-the-midpoint-between-what-this-master-reads-and-what-the-adversary-reads): a threshold *computed from* the thing under test. The implicit and far
more common form is a threshold *chosen so the current artefact passes*, which is
the same rule applied by hand. In both, the instrument can only detect
regression, never absence of quality — and the two are indistinguishable from
inside.

The tell is that **the instrument has never been shown anything but real work.**
Even a *deliberate* calibration can carry this defect if its calibration set is
one-dimensional: the audio suite's flatness calibrator ran on every invocation
and verified its own accuracy honestly — but every signal it had ever been shown
was a sustained tone with noise added. It confirmed monotonicity along that one
axis and said nothing whatever about impulsive material, which is precisely where
the statistic turned out to be **inverted** (see
[§2 of what worked](#2-positive-controls-that-must-pass--built-from-first-principles)).

**2. Guards were never watched failing.** Every case in family V and most of
family III reduces to: *nobody ever saw this thing say no.* The check that could
not fail ([V.1](#v1--a-verification-that-could-never-fail)), the gates that
passed on empty sets ([V.2](#v2--two-gates-reporting-pass-on-an-empty-set)), the
tool that had never executed ([V.3](#v3--a-tool-that-had-never-once-executed-in-a-bar-that-reported-it-as-passing)), the eviction that had never run
([V.4](#v4--bounds-that-had-never-executed)), the controls that had never been
opened ([III.3](#iii3--a-positive-control-anchored-to-the-defect-which-the-fix-then-took-away)) — all of them were *green for their entire lifetime*, which is
exactly what a working guard looks like from the outside.

This is why "the tests pass" is such weak evidence about a guard. A guard's
passing state is indistinguishable from its broken state **by construction**. The
only distinguishing observation is the refusal, and if you have never provoked
one you have never observed the guard at all.

**3. A report was trusted over the thing it reports on.** Family I is the whole
story, and family IV is the same story with the corruption happening inside the
instrument rather than beside it. The reported gain reduction
([IV.1](#iv1--a-limiter-reporting-0124-db-of-gain-reduction-while-removing-about-22-db)) was believed to the point of writing a formal
refutation on it. The database row ([I.2](#i2--a-resolution-check-that-read-a-database-row-instead-of-the-file)) was believed over ten files that decode in
eight minutes. The record ([VI.2](#vi2--a-fix-that-was-in-the-tree-and-not-on-the-box)) was believed over the running process.

Notice how cheap the settling observation was in every single instance: decode
the file, run the command by hand, read `/proc`, query the provider's API. In
this project the pattern recurs so often that it has a house rule — *"run the
failing command by hand before reading the code that wraps it"* — recorded after
an `ssh -v` outranked a full day of code reading.

**4. A metric's extremum was a degenerate case.** Family II, and the reason it
deserves separate billing from the others is that it is the only family where
**the instrument is correct** and the harm is done downstream. G-EVENT measures
trough depth accurately. The recurrence statistic counts coincidences accurately.
The damage happens when a human or a loop starts *optimising* against them, and
follows a gradient that terminates in silence or in an empty set.

This is the one family that scales with how good your automation is. A metric
whose maximum is degenerate is harmless if nobody optimises it, and it is a
guided missile aimed at your product if something does.

### The thread that does not hold

**"They were sloppy" does not survive the evidence.** The people who wrote these
instruments wrote the docstring naming the exact failure mode
([I.4](#i4--a-blank-frame-detector-defeated-by-a-strip-of-sky)), the comment
explaining exactly why the heavy step needed a lock
([VII.1](#vii1--a-memory-guard-that-polled-current-usage-and-so-could-not-see-intent)), the header stating that a passing negative control invalidates every
result above it ([V.3](#v3--a-tool-that-had-never-once-executed-in-a-bar-that-reported-it-as-passing)), and the note that *"a detection that does not reach an exit
code is a rumour"* on the tool that had never once reached an exit code.

The knowledge was **present and written down, adjacent to the defect, in the
defect's own words.** What was missing was a mechanism that could act on it.
That is the most uncomfortable finding here, and the one with the clearest
implication: **prose is not a mechanism.** The fixes that stuck in this project
all converted a written intention into something that executes — a provenance tag
that CI rejects, a third verdict value the aggregator counts as a failure, a
selftest that perturbs each check and requires exactly one failure.

### A ranking, since not all of these cost the same

Ordered by expected damage per unit of effort to prevent:

1. **The instrument does not open the artefact.** Cheapest to check, most common,
   most complete failure. One assertion — *the thing I measured is the thing that
   shipped* — closes most of family I.
2. **The guard has never been observed refusing.** Trivially detectable by asking
   the question, and every instance found in this project was real.
3. **The threshold came from the artefact.** Requires a convention and a check,
   but the convention is one field on a data structure.
4. **The metric's extremum is degenerate.** Requires actual thought about each
   metric, and the harm is proportional to how hard anything is optimising it.
5. **The metric measures something adjacent.** The hardest, because the
   instrument is honest and careful and the gap is conceptual. The version-series
   test in [VII.2](#vii2--an-engine-quality-metric-that-did-not-respond-to-two-rebuilds-of-the-engine) is the cheapest general-purpose detector for it.

---

## What actually caught these

None of these were caught by review. Three reviewers read the comment in
`vast-render/docs/incidents.md`'s "recurring shape" entry and all three agreed
with it, because the comment *was* a correct description of the intent — it was
just false about the ordering the code actually had. What caught them was a small
number of practices, all of which are cheap and none of which is clever.

### 1. Degenerate-signal controls that must FAIL

Build the stupidest possible input for your gate and require the gate to reject
it. In this project the corpus is: digital silence, white noise, a two-second
block tiled, a stationary hiss, and — decisively — **the artefact's own spectrum
re-synthesised as stationary noise**, which preserves every spectral statistic
and destroys every event. That last one, the `M-EVENT` mutation, is the sharpest
instrument in the suite: it reads 2.06 dB where the real control reads 21.36 dB.

The discipline that makes this work is **requiring the controls to run before the
gate is believed**. Two real bugs in one gate were found this way, in the gate's
own controls, on its first run:

* the event detector went blind on stationary material — with only a "within
  12 dB of the loudest" test, a signal with no dynamics has *every* frame near
  its own top, so the whole passage reads as one continuous event and there is no
  gap left to measure;
* a completely silent input returned `INAPPLICABLE` rather than `FAIL`, because
  a loudness function returned −infinity and −infinity was being read as "no
  calibration supplied" rather than as "measured, and there is nothing here".

Both were caught because the three signals the gate exists to reject were run
*first*, and all three came back `INAPPLICABLE`.

### 2. Positive controls that must PASS — built from first principles

A gate that refuses everything is not a gate. The turning point in the audio work
was building **one synthetic signal that is unambiguously good**, from physics,
with nothing recorded and nothing imported from the production code path: thin
ring flexural modes at ratios 1 : 2.83 : 5.42 : 8.73 (which are not small
integers, which is *why* a struck tube has no pitch), Hertzian contact for the
excitation, jet noise on Lighthill scaling, joint damping.

Two things immediately fell out of having it:

* **Two metrics were revealed as inverted rather than mis-thresholded.** Measured
  against every negative in the corpus, on both instruments at once:

  | passage | per-band flatness (× white) | harmonicity (dB) |
  |---|---:|---:|
  | **660 struck plates, no noise source at all** | **1.263** | **−3.78** |
  | **the physics-built positive control** | **1.032** | **−5.36** |
  | a literal hair dryer | 0.700 | — |
  | a blower into tubes | 0.639 | −0.63 |
  | the delivered master | 0.922 | +0.26 |
  | **a pure drone** | **0.338** | **+30.54** |

  **Every negative outscores every positive, on both instruments simultaneously.**
  That is not a threshold that needs moving; it is a statistic that is not
  monotone in the property being gated, and **no value of either bar passes what
  should pass and fails what should fail.** The reasons are physical and, once
  stated, obvious: an impulse's magnitude spectrum is smooth and deterministic,
  so its bin-to-bin variance is *lower* than white noise's chi-square
  fluctuation, and a shower of struck plates is literally flatter than white
  noise on that estimator. And a harmonicity measure asks whether the signal
  holds a note; a struck resonator does not. Both bars were **retired**, both
  recorded with their measurements so that re-adding either has to argue with a
  number rather than with a gap, and both instruments were **re-scoped** to the
  passages where their question is the right one.

* **The old bar's only validation was exposed as circular.** The retired
  harmonicity bar had been justified by one signal — which was 98.3% sustained
  tone by power, and *was the thing the client had rejected three times*. **The
  instrument that proved the bar reachable was itself the defect.** That signal
  was kept, unchanged, and its role inverted: it is now the anti-cheat control,
  the cheapest signal that clears the old bars, and it is **required to fail**.

The other thing positive controls buy you is knowing which failures are the
instrument's. When the new positive control failed a gate, the response was to
measure the gate's own null, discover the bar sat an order of magnitude below the
no-defect case ([II.2](#ii2--a-recurrence-gate-that-pure-randomness-fails)),
declare the gate **open for that control only** with the measurement attached —
and move nothing. The rule attached to that mechanism so it cannot become a
dumping ground: **an entry is admissible only with a measured null for the limb
it names**, never because a control "nearly" passes.

### 3. Mutation testing on the gates themselves

Perturb each check one at a time and require **exactly one** failure. The
repaired verification harness in [V.3](#v3--a-tool-that-had-never-once-executed-in-a-bar-that-reported-it-as-passing)
does this with no external dependencies at all: 27 value checks perturbed one at
a time, each producing exactly one FAIL; and — the part that closes the original
bug — the five historically-silent inputs **dropped** one at a time, each moving
a row from `OK` to `UNMEASURABLE`, **never to silence**.

The most recent audio suite reports this as a headline number: *"10 controls all
correct, 14 mutations all FIRED, no blind gates, 38 thresholds, 0 provenance
violations."* That single line answers "do my gates work" in a way that "all
tests pass" never can.

### 4. Predictions recorded before measurement

One staging document opens:

> **Four predictions in this pass were confidently made and wrong on
> measurement.** Three of them are recorded below in more detail than the fixes,
> because they are worth more.

That is the practice, and the discipline is writing the prediction down *first*,
where it can be wrong in public. It is what turns a surprising measurement from a
curiosity into a signal that your model of the system is broken — which is
exactly the state you are in whenever an instrument has been lying to you.

The corollary practice, equally valuable and rarer: **record the negative
results.** [VII.3](#vii3--suspiciously-fast-is-not-a-detector) — "suspiciously
fast is not a detector, here is the ranking that proves it" — costs one paragraph
and saves the next engineer a week. Three candidate metrics were built, measured,
found not to discriminate, and **written up as the more useful half of the pass**.

### 5. Watching the fix fail before it lands

The strongest single habit in this corpus. Before each fix ships, run the new
test against a copy of the **pre-fix** tree and record the score.

* The blacklist fix: **7/13 checks before, 13/13 after**, with the six failures
  listed by name.
* The same incident replayed with **two real processes**, because a
  single-process test cannot express the bug: pre-fix the sibling bought both bad
  offers, post-fix it bought neither. **1/5 → 5/5.**
* The lock migration in [VII.1](#vii1--a-memory-guard-that-polled-current-usage-and-so-could-not-see-intent): three regression tests, including one asserting that the
  *wrong-binary refusal is still armed* through the new wrapper — because the
  obvious implementation would have silently disarmed it.

A test written after a fix, and only ever seen passing, is in exactly the
position of every guard in family V.

### 6. Never moving a threshold to make an artefact pass

Stated most plainly in the entry titled *"BOTH BEAT-1 BARS ARE RETIRED, AND
NEITHER WAS MOVED TO MAKE A MASTER PASS."* The available responses to a failing
gate, in the order this project came to prefer them:

1. **Fix the artefact.**
2. **Retire the instrument**, with the measurement that retires it, so that
   re-adding it has to argue with a number.
3. **Re-scope the instrument** to the conditions where its question is the right
   one — as the two inverted statistics were, from "all material" to "sustained
   engine material only".
4. **Declare it open**, with a measured null attached and printed on every run.
5. **Move the bar** — and only with a derivation from physics, from published
   literature, or from a control, recorded in a field a machine checks.

The move that is never available is the one everybody reaches for first.

### 7. Three verdicts, not two

Threaded through everything above. `PASS` / `FAIL` has nowhere to put "I could
not measure this", and every project that lacks the third value discovers that
unmeasured silently means fine.

* `VACUOUS` — the gate ran and had nothing to test
  ([V.2](#v2--two-gates-reporting-pass-on-an-empty-set)).
* `UNMEASURABLE` — the input was missing, counted as a failure
  ([V.3](#v3--a-tool-that-had-never-once-executed-in-a-bar-that-reported-it-as-passing)).
* `unknown` — the probe did not answer, and only a positive `idle` licenses
  anything destructive (the render farm's three-state activity rule, written
  after "I could not ask" was read as "it is not happening" three times in one
  incident).
* `?` — this file's staleness cannot be determined, and **`?` is never rendered
  as `ok`** ([VI.2](#vi2--a-fix-that-was-in-the-tree-and-not-on-the-box)).

And its enforcement clause, which is the one line to take away if you take only
one:

> **A check that cannot be evaluated must never be indistinguishable from one
> that passed.**

---

## Sources

Every case above was verified against the entry cited with it. The entries live
in two repositories:

| document | contains |
|---|---|
| `f1-round2/docs/DEFECT-LOG-R2.md` | R2-012, R2-018, R2-020, R2-060, R2-110, R2-115, R2-151, R2-173, R2-181, R2-352, R2-357 |
| `f1-round2/docs/STAGING-R2-1091-to-R2-1120.md` | the focus selftest that skipped into OK |
| `f1-round2/docs/STAGING-R2-2221-to-R2-2280.md` | R2-2222 (the midpoint rule), R2-2223, R2-2224 |
| `f1-round2/docs/STAGING-R2-2821-to-R2-2880.md` | R2-2821, R2-2822, R2-2823, R2-2824 |
| `f1-round2/docs/STAGING-R2-3121-to-R2-3180.md` | R2-3120, the repaired bar's first honest verdict |
| `f1-round2/docs/STAGING-R2-3901-to-R2-3960.md` | R2-3927 |
| `f1-round2/docs/STAGING-R2-3961-to-R2-4020.md` | R2-4020 (also in `DEFECT-LOG-R2.md`) |
| `f1-round2/docs/STAGING-R2-4021-to-R2-4080.md` | R2-4030 – R2-4043 |
| `f1-round2/docs/STAGING-R2-4081-to-R2-4140.md` | R2-4082 – R2-4087 |
| `f1-round2/docs/STAGING-R2-4141-to-R2-4200.md` | R2-4141 – R2-4147(4) |
| `f1-round2/docs/audio-rebuild3/SPEC-ENGINE-AND-GATES.md` | the gate audit, the tiled-loop exhibit |
| `f1-round2/docs/audio-rebuild3/SPEC-CHAIN-AND-GLASS.md` | the limiter's true gain curve |
| `f1-round2/docs/MASTER-RUNBOOK.md` | the seven blocking gates and why each exists |
| `f1-round2/docs/r2_4020_waitmem_timeline.tsv` | the 0.5 s memory trace behind VII.1 |
| `vast-render/docs/incidents.md` | #169; the black PNG; the EEVEE prewarm; the nine "crashes" |
| `vast-render/docs/operations.md` | the disk preflight and the three bounds |
| `vast-render/docs/agents.md` | `rq drift`, the blank-frame classification |
| `vast-render/docs/linked-libraries.md` | R2-351 – R2-360 |

Two entries not written up above are worth reading in full for anyone collecting
this pattern: `incidents.md`'s *"A recurring shape: a comment describing a path
the code's own ordering makes unreachable"* — three instances of a correct
comment made false by a guard sitting in front of the call it describes, **every
one invisible in the passing case** — and its 2026-08-03 entry, in which every
guard against a stalled render was reading the wrong rendering engine's settings
and therefore no-op'd silently, *including the one whose comment called it "the
backstop for whatever the next scene invents."*
