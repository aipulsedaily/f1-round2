# STAGING — R2-581 … R2-600

Follow-up on **R2-422 as corrected by R2-430**: the mid-lap stretch where the car
collapses to roughly one third of its usual size. The brief was to characterise
it properly, decide whether it is actually a defect, and fix it with the smallest
possible change to the camera path.

**Method.** A corrected shot-scale instrument built independently of the one that
produced `tmp/shotscale_v2.npy`, validated against it and against a ruler on
seven delivered frames; then the frames themselves; then a path-level A/B, then
a rendered A/B off the shipping blend.

**Provenance.** `render/film14_path.json`, `telemetry/telemetry.csv`,
`anim/filmtime.py`'s time map. Pixels from `out/seq/r2b56_720` (film6 build) and
`out/seq/b456wit_f11` (film11 build) — **both carry a camera identical to
film14's in this region, verified key by key**, so their framing is film14's
framing even though their lighting is not.

---

## R2-581 — the corrected instrument, rebuilt from scratch, and the negative controls it has to fail

The script that produced `tmp/shotscale_v2.npy` no longer exists anywhere in the
tree. Its numbers are the ones R2-430's correction rests on, so before using them
to convict anything I rebuilt the measurement from the spec in R2-430 —
`tools/lap_shotscale.py` — and made the two implementations argue.

**They agree.** Over all 1,524 frames of beat 5 the p95 relative difference
between my series and `shotscale_v2.npy` is **0.64 %**, and the headline figures
reproduce to the decimal:

```
                       R2-430's correction    tools/lap_shotscale.py
beat 5 median                  12.91 %                12.92 %
f2035-f2227 median              4.22 %                 4.215 %
f2035-f2227 minimum             2.96 %                 2.957 %
```

**The controls, and they are the point.** Two of the size detectors written for
R2-422 returned 0.90 and 1.00 by latching onto the turntable and the rear wall.
`--selftest` therefore asserts four things, and two of them are things the
instrument must FAIL if the car is not there:

```
PASS  positive/pixels   f697 projects 0.5033; tools/beat1_true_extent.py, written
                        by someone else, gets 0.5033 on the same path, and the
                        ruler on r1full_000697.png reads 0.4630. A BOX bounds the
                        car, so it must sit slightly ABOVE the ruler (8.7 %) and
                        never below.
PASS  negative/absent   a zero-volume car reads max 0.000000 over beat 5
PASS  negative/absent-from-shot
                        the car left PARKED ON THE DAIS while the camera flies
                        the whole lap: median 3.00 % against the real 12.92 %,
                        only 993 of 1,524 frames even measurable, and it agrees
                        with the real reading to 10 % on 32 frames. A detector
                        latched onto scenery would agree on all 1,524.
PASS  agreement         vs tmp/shotscale_v2.npy over beat 5, p95 0.64 %
```

> **The third control's number is the uncomfortable one and it is left in the
> output on purpose.** With the car never leaving the showroom, the metric reads
> **3.00 %**. The stretch this document is about reads **4.2 %**. The car being
> present, on the circuit, at 300 km/h, makes a **1.4x** difference to how big it
> is on the screen. That is a fact about the stretch, not a fault in the ruler.

**The instrument was also wrong once and is fixed here.** Its first version let a
bounding box straddling the camera plane through the perspective divide, which
manufactured huge finite numbers from corners at z≈0; that is precisely how the
displaced-subject control passed when it should have failed. Straddling boxes now
report NaN.

**Correction to a figure in R2-430.** R2-430's appended correction states "true
value at f697 is 0.4746". On `render/film14_path.json` both this tool and
`tools/beat1_true_extent.py` get **0.5033** at f697; 0.4746 does not reproduce
from the shipping path. The *conclusion* is unaffected — 0.50 against a ruler
reading 0.4630 is still a full shot, still 1.57x smaller than the withdrawn
0.7890, and still confirms the retraction — but **0.4746 should not be quoted
again.**

---

## R2-582 — the stretch is real, it is longer than reported, and it is the longest small-subject run in the film outside the closing wide

R2-422 reported f2035-f2227, 193 frames, 8.04 s. Re-run on the corrected series
the run is **longer at every threshold**, and its identity does not depend on
which threshold is chosen:

| threshold | as a fraction of the beat-5 median | run | frames | seconds |
|---|---|---|---:|---:|
| 10.0 % | 0.77x | f2012-f2256 | 245 | **10.21 s** |
| 8.0 % | 0.62x | f2016-f2245 | 230 | 9.58 s |
| 6.46 % | 0.50x | f2021-f2236 | 216 | 9.00 s |
| 6.0 % | 0.46x | f2022-f2232 | 211 | 8.79 s |

**f2012-f2256 is the longest continuous run under 10 % of frame width anywhere in
beats 2-6**, including beat 6 itself:

```
f2012-f2256   245 fr  10.21 s   median 4.41 %   <- this, mid-lap
f2388-f2596   209 fr   8.71 s   median 7.36 %
f2794-f2978   185 fr   7.71 s   median 2.76 %   <- beat 6's closing wide
f1121-f1252   132 fr   5.50 s   median 5.25 %
```

It is **16.1 % of the flying lap** and 8.2 % of the film.

**And it is the same shot scale as the closing wide, in both axes.**

```
                     frac of frame WIDTH    frac of frame HEIGHT
beat 5 overall              12.92 %                 9.93 %
f2012-f2256                  4.41 %                 3.88 %
beat 6, the closing wide     4.15 %                 3.79 %
```

That comparison is the argument, and it needs no invented threshold: **the film's
fastest, most kinetic passage and its valedictory farewell wide are shot at the
same size.** One of them is authored to be a speck.

**Not chased here, but recorded so it is not lost:** the second entry in that
table, **f2388-f2596, 8.71 s at a 7.36 % median**, is the declared long-lens
follow into T12 Plongee (anchor t=98.6, 120 mm). It is milder — above half the
beat median throughout — and it is a *following* shot rather than a static hold,
so it is not the same defect. It is the obvious next thing to put a watch on if
the pacing verdict on this one comes back "too long".

---

## R2-583 — the cause is BEARING, not distance, and the author fought the wrong term

Between f2000 and f2100 the subject loses 4.65x. Decomposed exactly — apparent
width = presented metres x lens / (36 mm x distance) — it is not one loss but
three, and the largest is not the obvious one:

```
                 f2000     f2100     factor
distance         78.6 m   169.5 m    2.16x smaller
BEARING          61.7 deg   4.3 deg  2.47x smaller   <- the bigger term
lens             65.0 mm   74.6 mm   1.15x larger
                                     --------
                 13.82 %    2.97 %   4.65x smaller
```

"Bearing" is the angle between the car's heading and the camera's line of sight.
The presented width — what the frame actually contains — falls from **6.01 m to
2.43 m**:

```
     f     bearing   presented   frac_w
  1990     85.7 deg    5.87 m    13.41 %
  2000     61.7 deg    6.01 m    13.82 %
  2010     33.1 deg    4.82 m    10.75 %
  2020     11.9 deg    3.16 m     6.47 %
  2030      0.3 deg    2.06 m     3.79 %   <- dead nose-on, the car's 2.0 m track
  2100      4.3 deg    2.43 m     2.97 %
  2160     22.8 deg    4.07 m     4.84 %
  2220      1.2 deg    2.15 m     3.49 %
```

**The camera runs away down the centre of the road, so the car is exactly nose-on
at exactly the moment it is furthest away.** The distance loss and the aspect loss
multiply instead of trading off.

> This is the same blind spot that produced R2-429's 76.1 % and survived two
> tools before R2-430 caught it: **apparent size depends on which way the subject
> is facing.** There it was an error in an instrument. Here it is a fact about the
> shot, and it has been sitting in the film the whole time.

**The author saw the trough and fought it with the lens — the term that was less
to blame — and ran out of lens.** The focal climbs 65 → 85 mm through the stretch,
and then sits at **exactly 85.000 mm for eighteen consecutive frames, f2194-f2211**.
That flat is two adjacent anchors (t=91.4 and t=92.4) both declaring 85.0; it is a
ceiling, not a curve. 1.31x of compensation was applied against a 6.0x loss.

**A fourth observation, from the projection and not from taste.** Across the whole
stretch the car sits at screen x = **0.500** and y = 0.506-0.510, and the camera's
aim is a median **0.007 deg** off the car. For ten seconds the subject is nailed
to the exact centre of the frame with no lead room and no drift. Whatever else is
true, nothing in the composition is moving.

---

## R2-584 — the pixels: five frames measured with a ruler, three of them inside the stretch

Numbers found this; they do not convict it. These do. The camera in
`out/seq/r2b56_720` (film6) and `out/seq/b456wit_f11` (film11) is **identical to
film14's** at these frames — position, quaternion and focal all match key for key
— so the framing is the shipping framing.

| frame | source | projected | ruler on the picture | box overstates by |
|---|---|---:|---:|---:|
| f2000 | `r2b56_720_002000.png` 1280 px | 13.82 % | **13.83 %** (x 548-725) | 0 % |
| f2090 | `r2b56_720_002090.png` 1280 px | 3.02 % | **2.96 %** (x 620.7-658.6) | 2 % |
| f2100 | `b456wit_f11_002100.png` 1920 px | 2.97 % | **2.79 %** (x 932.9-986.4) | 6 % |
| f2180 | `r2b56_720_002180.png` 1280 px | 4.37 % | **4.06 %** (x 612.9-665.0) | 8 % |
| f697 | `r1full_000697.png` 1280 px | 50.33 % | 46.30 % (R2-430's ruler) | 9 % |

The corrected instrument is confirmed by a ruler at five frames, three of them
inside the stretch under investigation and one on its shoulder. **Every ruler
reading is at or BELOW the projection, by 0-9 %, which is the direction a
bounding box must err in.** An instrument that erred the other way would be
measuring something other than the car. The error is smallest at f2000, where the
car is broadside and the box fits it tightest, and largest at f697, where the car
is head-on and the box's front plane sits ahead of the front wing.

**What the frames look like, which is the part that decides it.**

* **f2000, the shoulder, 13.83 %** — and it is a genuinely fine frame: the car
  three-quarter and readable, low sun across the bodywork, its own shadow long on
  the asphalt, kerbs and a sweeping corner around it. **This is what the film
  loses four seconds later.** It is the honest before-picture, and it is not a
  straw man.
* **f2090** — a wide aerial of a sweeping right-hander at golden hour. It is a
  handsome frame. The car is a **38-pixel** blue chip in the middle of an empty
  road, roughly 116 px in the 4K delivery. It reads as *a car, somewhere down
  there*. It does not read as 300 km/h.
* **f2100** — the same shot 0.4 s later, 1920 px wide. The car is **54 px**.
  Everything else in the frame — run-off, catch fence, two grandstands, tree line —
  is larger and better lit than the subject.
* **f2180** — the worst of the three, and the one a number would never have
  found. The car is a **52-px dark silhouette in shadow**, at almost the same
  luminance as the road behind it, and the bottom-right **45 % of the frame is
  filled by a motion-smeared grandstand structure sweeping through the
  foreground**, its upper edge passing within a few pixels of the car. The
  subject is not merely small here; it is competing with, and nearly lost in,
  foreground architecture.

For contrast, `b456wit_f11_002270.png` — 3.7 s later, the doppler pass at
**24.92 %** — is the best frame in the beat: the whole car, side-on, sharp,
sunlit, the background smeared into pure speed. The payoff is not in doubt. The
ten seconds of approach to it are.

---

## R2-585 — the verdict: it is a defect of duration and floor, not of intent

**The wide is correct. The physics is real and is not in dispute:** the camera
cannot be stationary at the doppler station in time to be stationary for it
without leaving the car and running ~815 m, and it cannot stop from 68 m/s in
less than ~200 m. The beat sheet says so at t=91.4 and the path confirms it: peak
camera speed 97.6 m/s, peak deceleration 5.47 g at f2255.

**A film is allowed to go wide, and a flying lap in particular is allowed to show
its car small against a big circuit.** That is a real and good thing for a lap to
do; it is how a circuit reads as a place.

**So the case is not "the frame is too wide". The case is that the shot has no
event in it for ten seconds.** Stated from the shot's job rather than from the
number:

1. **It is a head-on approach in which nothing approaches.** Camera-to-car runs
   104 → 170 → 187 → 145 m across the stretch, and for the 5.0 seconds
   f2080-f2200 it sits between **160.4 and 187.2 m — a spread of 17 %**. The
   visual grammar of a head-on trackside shot is a car *growing*. Here it does
   not. Every twentieth frame, f2020 to f2220:

   ```
   6.47  3.79  3.82  4.48  3.32  2.97  3.88  5.51  4.84  4.37  4.88  3.49  %
   ```

   That is noise around a flat line, not a build.
2. **Nothing else is moving either.** Subject nailed to screen centre (R2-583),
   aim 0.007 deg off, lens crawling and then flat for 18 frames.
   **And the soundtrack does not carry it.** `audio/out/master.wav`, 0.5 s
   windows at 1 s spacing across t = 82-98 s: broadband RMS 10,922-11,387
   (a 4 % spread) and the 80-1200 Hz engine-band centroid 611-656 Hz (7 %, with
   no trend). Nothing in the mix rises or falls across the ten seconds either.
   *Limit:* 0.5 s windows cannot see an event shorter than half a second, and
   this says nothing about the doppler sweep at t=94.6, which is after the
   stretch and was not measured here.
3. **It is the longest such run in the film outside the closing wide, and it is
   at the closing wide's own scale in both axes** (R2-582).
4. **It sits in the beat whose declared job is speed.** `beat_sheet.json` calls
   beat 5 "one flying lap, vantage morphing continuously". For 16.1 % of that
   beat the vantage does not morph and the subject does not change size.
5. **And there is a floor under how much smaller it could get.** With the car
   left parked in the showroom for the entire lap — never on the circuit at all —
   the same metric reads **3.00 %**. The stretch reads **4.2 %**. Whatever the
   passage is doing, it is doing it with the subject only 1.4x larger than absent.

**Where the honest doubt lives, and it is real.** The wide is also the *setup*: a
ten-second withdrawal makes the 24.92 % doppler pass land harder than it would
after a close shot. Contrast is dramaturgy and this is a legitimate defence of
the shot as authored. What it does not defend is the *duration*, the *flatness*,
or f2180's foreground. My judgement — and it is a judgement, offered as one — is
that **the same setup at three to four seconds would cost the film nothing and
would not be a defect**; the other six or seven seconds are the transit cost of
the hover, showing.

**Verdict: a defect, of duration and floor, not of intent.** The fix must not
remove the wide. It must give the ten seconds something to do.

---

## R2-586 — the fix: lens only, position and rotation untouched, verified byte-for-byte

`tools/r2581_lensfix.py`. The authored focal is multiplied by a smooth bump
m(f) with **compact support on f1997-f2244**, exactly 1.0 outside it, C2 at both
ends by construction (smootherstep window over 46 frames at each end, on a curve
that is itself a double box-smooth of the per-frame demand).

**This is not a new idea; it is the author's own, finished.**
`tools/author_beats2_5.py`'s beat-5 docstring reads: *"the lens goes long while it
repositions and wide again as the car arrives, which is how you keep a subject
large while the camera is doing something else."* The move was declared and then
applied at 1.31x against a 6.0x loss.

### Variant A — the floor. `--target 0.0646`, half the beat-5 median

Candidate: `render/film14_path_R2581A_floor_CANDIDATE.json`. Before / after:

```
     f   lens0   lens1     x    size0    size1   gain   smear0  smear1
  2000    65.0    65.1  1.00   13.82%   13.82%  1.00x       67      67
  2010    65.8    68.1  1.03   10.75%   11.12%  1.03x       89      92
  2020    67.2    81.5  1.21    6.47%    7.86%  1.21x       81      98
  2030    68.6   105.7  1.54    3.79%    5.83%  1.54x       63      97
  2050    70.0   138.1  1.97    3.75%    7.41%  1.97x       30      60
  2080    72.5   154.2  2.13    3.32%    7.06%  2.13x       20      42
  2100    74.6   158.1  2.12    2.97%    6.31%  2.12x        9      20
  2120    75.4   152.4  2.02    3.88%    7.85%  2.02x       47      94
  2140    78.1   145.2  1.86    5.51%   10.25%  1.86x       66     124
  2160    80.0   138.5  1.73    4.84%    8.37%  1.73x       56      96
  2180    83.2   143.1  1.72    4.37%    7.52%  1.72x       67     115
  2200    85.0   142.6  1.68    4.88%    8.19%  1.68x       39      66
  2220    84.7   104.2  1.23    3.49%    4.29%  1.23x        3       4
  2240    74.7    74.7  1.00    6.87%    6.87%  1.00x       25      25
  2270    40.1    40.1  1.00   24.92%   24.92%  1.00x      293     293
```

```
the stretch f2012-f2256, 245 frames, 10.21 s
  median size   4.41 %  ->  7.58 %
  minimum size  2.96 %  ->  4.18 %
  frames under 6.46 %      216  ->  52
  peak focal     85.0 mm  ->  158.1 mm
  worst 4K smear   91 px  ->  124 px, over the 246 frames the change touches
```

### Variant B — the build. `--ramp 0.045 0.085`

A floor stops the passage being too small. It does **not** stop it being flat,
which R2-585 argues is the larger half of the defect. Variant B asks the subject
to *grow* from 4.5 % to 8.5 % across the support instead of holding a level, so
the ten seconds acquire the one thing a head-on approach is supposed to have.

Candidate: `render/film14_path_R2581B_ramp_CANDIDATE.json`.

```
     f   lens0   lens1     x    size0    size1
  2010    65.8    66.9  1.02   10.75%   10.92%
  2030    68.6    88.2  1.28    3.79%    4.87%
  2050    70.0   111.8  1.60    3.75%    5.99%
  2070    71.4   127.7  1.79    3.82%    6.83%
  2090    73.7   140.3  1.91    3.02%    5.76%
  2110    74.9   145.6  1.94    3.26%    6.32%
  2130    76.6   147.9  1.93    4.69%    9.06%
  2150    79.4   154.7  1.95    5.42%   10.57%
  2170    81.0   166.1  2.05    4.39%    9.00%
  2190    84.8   185.0  2.18    4.91%   10.71%
  2210    85.0   156.1  1.84    4.25%    7.80%
  2230    81.6    87.7  1.08    5.70%    6.13%
  2250    64.6    64.6  1.00    9.09%    9.09%
  2270    40.1    40.1  1.00   24.92%   24.92%
```

```
  median size   4.41 %  ->  7.30 %
  minimum size  2.96 %  ->  4.74 %
  frames under 4.50 %      133  ->  0
  peak focal     85.0 mm  ->  185.1 mm
  worst 4K smear   91 px  ->  143 px
```

**The shape is the point, not the median.** Before, the ten seconds read 3.8,
3.8, 3.8, 3.3, 3.0, 3.3, 4.7, 5.4, 4.4, 4.9, 4.3, 3.5 — noise around a flat line.
After, they read 4.9, 6.0, 6.8, 5.8, 6.3, 9.1, 10.6, 9.0, 10.7, 7.8 — a build
from 5 % to 10.7 % that then hands straight over to the natural rocket into the
24.92 % doppler pass. **Variant A raises the floor. Variant B gives the passage a
direction.** One residual dip survives in B, to 4.83 % at f2220, where the bearing
returns to 1.2 deg and the window is already easing out; that is one second of
"still far away" immediately before the payoff and is defensible as authored.

**Recommendation: B**, with A as the conservative fallback if the 185 mm peak is
judged too long. Both are the same tool, the same support, the same guarantees.

### How the "after" frames are rendered without touching a blend

For a fixed camera, a longer focal length is *exactly* a centred crop at higher
pixel density. `rq render --zoom Z --border (0.5-0.5/Z .. 0.5+0.5/Z)` therefore
produces the frame a lens `Z x` longer would produce — same position, same
rotation, same motion blur, same shutter — with no blend rebuilt. It is valid
here because the car sits at screen x = **0.500** in every frame of the stretch
(R2-583), so a centred crop cannot lose it.

**This is not my invention and it has a precedent in this project's own render
history.** `out/seq/b456wit_lens40` and `out/seq/b456wit_lens74` were rendered by
another agent from `film11.blend`, whose authored focal at f2978 is
**18.7500 mm**, at `zoom 2.1333334` and `zoom 3.9479167`. Those are 40/18.75 and
74/18.75, and the border in both jobs is exactly `0.5 +/- 0.5/Z`. Two sequences
named after the focal lengths they emulate, from a base focal that recovers both
to four decimals — and film14 now ships **73.9969 mm** at f2978, so the 74 mm
option is the one that won. The method is established and it decided a shot.

**The one exception, stated:** depth of field. A real 158 mm lens at the same
f-stop has roughly a quarter the depth of field of the 74.6 mm it replaces; a
crop does not. At 170 m subject distance nothing in these frames is near enough
for that to show, but the "after" frames are a faithful emulation of *framing*
and only an approximation of *focus*.

### The one-shot law, measured rather than asserted

`tools/campath_diff.py render/film14_path.json <candidate>`, with the R2-103
self-null printed first so the rounding floor is visible before any verdict:

```
SELF-NULL  film14_path.json vs itself
   raw stored q  (the R2-103 trap)   dq 0.203165 deg      <- the floor
   re-normalised q                   dq 0.000003 deg

A=film14_path.json  B=film14_path_R2581A_floor_CANDIDATE.json
   beat 1        f1-792      worst dp 0.0000 m   dq 0.000 deg   dlens 0 mm
     PROTECTED   f648-792    worst dp 0.0000 m   dq 0.000 deg   dlens 0 mm
   beats 2-6     f793-2978   worst dp 0.0000 m   dq 0.000 deg   dlens 83.8 mm

A=film14_path.json  B=film14_path_R2581B_ramp_CANDIDATE.json
   beat 1        f1-792      worst dp 0.0000 m   dq 0.000 deg   dlens 0 mm
     PROTECTED   f648-792    worst dp 0.0000 m   dq 0.000 deg   dlens 0 mm
   beats 2-6     f793-2978   worst dp 0.0000 m   dq 0.000 deg   dlens 100.2 mm
```

**Zero position change and zero rotation change over all 2,978 frames, in both
variants.** The only channel that moves is `lens`, and it moves only inside
f1997-f2244. The 0.203 deg in the self-null line is the R2-103 rounding floor —
six-decimal storage amplified by `2·acos(|dot|)` — and it is printed first
precisely so that the 0.000 deg below it is read against it and not against zero.

**The gate, shown FAILING before it is trusted passing.** `--selftest` asserts
five things; `--inject step|leak|smear` breaks the design on purpose:

```
                       clean    inject=step   inject=leak   inject=smear
compact support         PASS       FAIL          FAIL          PASS
C1 lens                 PASS       FAIL          FAIL          FAIL
position/rotation       PASS       PASS          PASS          PASS
negative/no-demand      PASS       PASS          PASS          PASS
smear ceiling           PASS       FAIL          PASS          FAIL
```

* **C1 lens uses no invented threshold.** The candidate's roughest frame is
  |dlens| **3.178** mm/frame and |d²lens| **0.842** mm/frame²; the *shipping*
  film's own worst over all 2,978 frames is **3.178** and **0.842**, both at the
  f2250-f2257 doppler zoom, which this change does not touch. The candidate is
  therefore exactly as smooth as what already ships and no smoother is claimed.
* **negative/no-demand** is the control that matters most: with the target set
  below every frame's actual size, the designer returns m = 1.0 everywhere. It
  responds to the measurement rather than reflexively lengthening the lens.
* **smear ceiling** counts only the frames the change touches. The film's own
  worst smears — 424 px at f2634, 293 px at the f2270 doppler pass — are outside
  the support and are untouched.

**The trade, so the choice is the main thread's and not mine:**

| target | median after | min after | peak focal | worst smear |
|---|---:|---:|---:|---:|
| floor 5.00 % | 6.09 % | 3.75 % | 122.4 mm | 96 px |
| **floor 6.46 % (A)** | **7.58 %** | **4.18 %** | **158.1 mm** | **124 px** |
| floor 8.00 % | 9.09 % | 4.63 % | 195.8 mm | 153 px |
| **ramp 4.5 → 8.5 % (B)** | **7.30 %** | **4.74 %** | **185.1 mm** | **143 px** |
| ramp 5.0 → 12.0 % | 8.68 % | 5.43 % | 258.2 mm | 199 px |

(nothing above was hand-tuned: each row is one run of the same tool with one
argument changed, and the 258 mm row is included because it is where the smear
ceiling starts to bind — 199 px against the 200 px flag — which is the honest
edge of what this fix can buy)

Beat 5's authored maximum focal elsewhere is **120.0 mm** at t=98.6 ("long-lens
follow into T12 Plongee's braking zone"), so the 5.00 % variant stays inside the
film's existing lens vocabulary and the 6.46 % variant exceeds it by 1.32x.

**What this fix costs, stated and not buried.**

1. **A longer lens is a narrower view, and here it costs the horizon.** At
   158 mm the horizontal half-angle is 6.50 deg against 13.57 deg at 74.6 mm:
   the circuit vista in these frames halves. Measured, as the geometric horizon's
   height in the frame (0 = top edge, negative = above it):

   ```
        f      before   variant A   variant B
     2080      -0.188      -0.963      -0.778
     2110      -0.008      -0.559      -0.487
     2140       0.130      -0.187      -0.214
     2170       0.262       0.092       0.011
     2200       0.322       0.201       0.123
   ```

   The horizon currently enters frame around f2110 and climbs to the upper third
   by f2200. **Both variants push it back out of frame until roughly f2160**, so
   about 2 more seconds of the passage become ground-only. The shot stops being
   an aerial wide and becomes a compressed long-lens head-on. That is a taste
   call. It is arguably the *right* shot for a flying lap — it is the language of
   the sport's own coverage — but it is a different shot and it should be chosen,
   not inherited.
2. **Depth of field.** The camera carries an f-stop and the candidate does not
   touch it; 2.1x the focal at the same f-stop is roughly a quarter of the depth
   of field. At 170 m subject distance the car stays inside it, but any merge
   must confirm against the blend's animated DOF rather than against this note.
3. **Variant A does not fix the flatness; variant B only partly does.** Raising a
   floor makes the ten seconds legible without making anything *happen* in them.
   B's build addresses that inside the lens channel — but a growing subject
   produced by a zoom is not the same event as a growing subject produced by an
   approach, and an audience can tell. **If the pacing verdict is that the
   passage is dead rather than small, neither variant is the fix**; the fix is
   then a shorter transit, which means moving the doppler station's arrival
   time, which is a beat-sheet change and not a path change.
4. **The 22 deg aim bound in `docs/beat_sheet.json` is stale at this focal.** At
   158 mm the frame's own half-width is 6.50 deg, so a 22 deg bound no longer
   bounds anything. Measured margin over f1997-f2244 is max **0.187 deg** off
   axis, so nothing leaves frame — but the gate's number would need re-deriving
   before it means anything again.

**What is NOT delivered here.** The candidates are per-frame paths. They have not
been folded back into anchor `lens_mm` values in `docs/beat_sheet.json`, and no
blend has been rebuilt — `docs/beat_sheet.json` already carries two other agents'
candidate sheets (`R2451_*`, `R2464_*`) and this one must not race them. The
anchor-level equivalent is four numbers: the `lens_mm` of the beat-5 anchors at
t=85.31, t=88.00, t=90.01 and t=91.40, currently 70 / 75 / 80 / 85 mm.

---

## R2-587 — the alternative fix, priced and rejected as not-smallest

Since R2-583 shows bearing is the larger term, the geometrically direct fix is to
stop the camera running down the *centre* of the road: bow its route laterally so
the car is never dead nose-on.

At f2100 the camera leads by 167 m. An **80 m lateral offset** would put the
bearing at 25.6 deg, raising presented width from 2.43 m to 4.27 m (1.76x) while
costing 1.11x in distance — a net **1.59x**, taking 2.97 % to 4.72 %.

**Rejected, for three reasons and one of them is fatal:**

* 1.59x does not reach what the lens reaches (2.12x), so it would need the lens
  anyway;
* an 80 m bow lengthens the camera's route, and the route already ends in a
  5.47 g stop — the deceleration budget has nothing in it;
* **it moves camera position, which is the channel the one-shot law is about.**
  The lens fix changes zero position and zero rotation on all 2,978 frames. Any
  positional change, however smooth, has to re-clear the placement gate against
  the assembled world, and at 15-50 m altitude over T10/T11 that is a real
  question and not a formality.

Recorded so nobody re-derives the bow and thinks it was overlooked. **If the
pacing verdict is that the passage should be shorter rather than bigger, the bow
is the wrong tool for that too — the right one is the arrival time at the doppler
station, and that is a beat-sheet change, not a path change.**

---

## R2-588 — the fix, in pixels: four matched pairs off the shipping blend

Rendered from **`render/film14_breach_r6.blend`** — the blend the ladder pass is
rendering, i.e. the shipping build — at 1280x720 / 64 samples / adaptive 0.01 /
camera `ONER`, the scene's own AgX and exposure. Eight frames, **$0.05 of GPU**,
slotted at prio 89 so they cost the r1ladder pass about seven minutes of its
seven hours. Archived in `docs/peep/r2581/`.

`before` is the film as it ships. `after` is variant A's focal at that frame,
rendered as `--zoom Z --border 0.5±0.5/Z`.

**First: the emulation is exact, and it has a control.** Downscale each `after`
by its own zoom factor and correlate it against the centre of its own `before`:

```
frame   zoom    corr vs its OWN before    corr vs a DIFFERENT frame's before
2050   1.9726          0.9935                        0.2069
2110   2.0839          0.9822                        0.1038
2170   1.7106          0.9785                       -0.0685
2200   1.6781          0.9977                        0.1356
```

0.98-1.00 against the right frame, 0.10-0.21 against the wrong one. **The `after`
frames are the same camera through a longer lens and nothing else.**

**Second: the ruler agrees with the projection on both sides of the A/B.** f2110,
measured off the delivered pixels:

```
             projected     ruler on the picture       box overstates
before          3.26 %     3.19 %  (x 618.7-659.5)         2 %
after           6.78 %     6.64 %  (x 596.2-681.2)         2 %
measured ratio           2.08x                 zoom requested 2.0839x
```

**Third, and this is the part that is not a number.** `zoom_before_2110.png` and
`zoom_after_2110.png` are the same 16 % x 22 % patch of frame at 6x. Before, the
car is a **blue smudge with two dark blobs for tyres**. After, at the same
sampling and the same grade, the rear wing endplates, the halo, the front-wing
elements, the tyre sidewalls and the livery's pattern are all separately legible.
**That is the difference between a car being present in a frame and a car reading
in a frame**, and it is what 3.2 % versus 6.6 % of frame width means in practice.

**Fourth, the honest cost, seen rather than argued.** The four pairs do not all
improve equally, and one of them is a warning:

* **f2050 — clear improvement.** Before: a chip on a wide corner with a sand
  trap. After: the car reads on the kerb line, and the kerb, verge and track
  edges are all still in frame. Nothing of value is lost.
* **f2110 — improved but bare.** This is the deepest point of the trough and the
  biggest zoom (2.08x). The car reads, but what surrounds it is now a strip of
  empty asphalt and two grass verges; the buildings and the horizon are gone.
  **The wide had more in it than the long lens does here.** If any frame argues
  for the gentler `--target 0.05` variant, it is this one.
* **f2170 — clear improvement, and the best frame of the eight.** The car reads
  on the kerb line of a sweeping corner with the barrier wall and the tree line
  still behind it. Both the subject and the place are in the frame at once.
* **f2200 — improvement, and it exposes a second defect.** The *before* frame is
  the camera passing a bridge: **two large concrete pylons occupy the left and
  right foreground and the car is a 62 px chip between them.** That is the same
  failure as f2180's grandstand — architecture in the near field competing with a
  distant subject — and it is now confirmed at two separate frames 20 frames
  apart. The longer lens crops most of the pylons out and the car reads under the
  `TELCOM` grandstand, so the lens fix *incidentally* improves it. **The
  foreground-architecture problem is real, it is separate from the shot-scale
  problem, and it is not fixed by a lens; it is a placement question and it is
  handed on rather than solved here.**

**Verdict on the fix.** Three of four pairs are unambiguously better pictures and
the fourth is better as a shot of a car and worse as a shot of a place. The
change is worth making; **f2110 is the argument for tuning the target down rather
than up**, and the trade table in R2-586 is where that choice lives.
