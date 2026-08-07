# STAGING — R2-1001 to R2-1030 · beat 5, the eight seconds at one third size

Owner: beat 5's f2012-2256 shot-scale run and the Pont occlusion inside it.
Merge by identity, never by position. **Do not edit `docs/DEFECT-LOG-R2.md`
from this file.**

Beat 5 is f1191-2714. Nothing here touches beat 6, `anim/carpath.py`,
`audio/scene.py`, the beat-6 camera keys, or the f2714/2715 seam.

Everything marked **MEASURED ON FRAMES** is measured on rendered pixels at
3840x2160 at 1:1. Everything else is measured on the built camera path, the
telemetry, and the world's own geometry.

---

## R2-1001 — the 8.04 s "one third size" defect is real as a NUMBER and false as a PICTURE. At 4K the car is a fully resolved F1 car at the span's worst frame

**MEASURED ON FRAMES.** `out2/seq/b5verdict_4k`, 6 frames, 3840x2160, 512
samples, `film17_breach.blend`, camera `ONER`. **$0.173, measured** — 1,412
GPU-seconds at $0.4403/hr, 235 s/frame.

The brief handed to this task was that beat 5 very likely repeats the ending's
defect — *"visible and 'a subject' are different things"* — for 8.04 s. It does
not. **The premise is refuted for the size claim**, and the instrument that
raised it is measuring the one property that turned out not to discriminate.

The four frames that carry the verdict, viewed at 1:1 on the 4K frame:

| frame | shot scale | distance | car width | what is actually in the crop |
|---|---:|---:|---:|---|
| f2035 | 4.24 % | 110.5 m | 163 px | rear wing, halo, **the driver's gold visor**, front wing, four tyres, cast shadow |
| f2100 | **2.97 %** | 169.4 m | 114 px | rear wing with legible endplate band, airbox, helmet, blue livery break, sidepods |
| f2160 | 4.84 % | **187.1 m** (span maximum) | 186 px | side-on through a corner, **brake discs glowing**, wing, halo, driver |
| f2225 | 4.70 % | 135.3 m | 180 px | small but whole, under the bridge |

f2100 is within 0.01 points of the span's minimum (2.96 % at f2097) and f2160 is
within 0.1 m of its maximum distance (187.2 m at f2161). At the span's *smallest*
subject and at its *furthest* the car is unambiguously an F1 car. It is not "a
grey-blue smudge."

**Why it differs from the ending at the same pixel size, measured not asserted.**
The ending reads 4.15 % and this span reads 4.22 %; R2-582 already put those two
numbers side by side. Pixel size was never the discriminator. Contrast is:

| | closing wide (per the ending's diagnosis) | f2035-2227 (measured here) |
|---|---|---|
| polarity | car **brighter** than surround | car **darker** than surround |
| luminance separation | a specular glint | **-46 % to -59 %** against the asphalt |
| colour break | 0.14 blue-minus-red | +0.020 to +0.064 blue-minus-red |
| range | ~1000 m | 110-187 m |
| aerial perspective | heavy; helmet sub-pixel | light |
| surround | featureless pale run-off | kerbs, white lines, cast shadow for scale |

A car at half the luminance of a pale asphalt background, with a cast shadow
roughly doubling its footprint, is a hard silhouette at 114 px. A car slightly
brighter than a pale run-off at 1000 m through haze is not, at 159 px. **The two
frames have the same subtense and opposite legibility.**

**The instrument's own corollary does not survive the pixels either.**
`tools/lap_shotscale.py --selftest` prints, unprompted:

> "COROLLARY, and it is uncomfortable: the control's 3.00 % is not far below the
>  4.22 % the f2035-f2227 stretch actually measures. At that size the car is
>  barely bigger on screen than if it had never left the showroom."

That is true as subtense and false as a claim about the picture. The control is
the car left parked on the dais ~1 km behind the camera, which at 3.00 % would be
a haze-flattened blob; the real car at 4.22 % is the f2100 crop above, with a
readable rear-wing endplate. **Equal subtense, opposite legibility** — the same
point the closing wide makes from the other direction. The instrument is sound
(all four of its controls pass, agreement p95 0.64 %); what is wrong is treating
its one number as a verdict.

Method note, offered so it can be re-run: the luminance and colour numbers above
are the darkest quartile of the projected car box against an annulus 4x its size,
per frame, on `out2/seq/r2full`. `f2185` and `f2190` are the two frames where
that measurement *inverts* (-3.0 % and +6.4 %, colour break negative) — which is
not a measurement artefact but R2-1002.

## R2-1002 — the "no subject" defect in beat 5 is real, lasts 0.50 s, and is not about size. f2180-2191 has no car in the frame at all

**MEASURED ON FRAMES**, and it confirms R2-664 at 4K rather than re-deriving it.

f2185 and f2190 at 3840x2160 are photographs of `ARCH_PontPlongee` — a wall of
motion-blurred concrete abutment and steel plate girder. **There is no car
anywhere in either frame.** f2190 is the cleaner example: the whole frame is
girder, parapet, kerb and grass.

*This* is the ending's defect, exactly: a handsome, correctly-hazed shot of
circuit architecture with no subject in it.

Read straight off `render/r2651/occlusion.json` (`occ_frac_front`, in frame):
**f2180-f2191 are 1.000 — twelve frames, 0.50 s, the car wholly hidden.** f2180's
occluder is the fence channel, f2181-2191 solid, occluder distance 26.4 -> 54.6 m,
and f2192 is still 58 % hidden.

`tools/r2731_pont_full_sightline.py` defaults to the solid channel and so
reproduces eleven of those, f2181-2191. Run with the fence bands included
(`solid_only=False`) it reproduces **all twelve, f2180-2191, and f2192's partial
at 0.52 against the raycast's 0.581**. Worth recording because it is a third
agreement the tool was not tuned for, and because the fence channel is not a
detail to drop: the twelfth frame is hidden behind the bridge's own mesh screen,
and a raycast cannot see through one of those any more than through concrete.

The correction this makes to the brief's framing: the defect inside those eight
seconds is **not** the 8.04 s of small car. It is half a second of no car. The
metric that found the eight seconds is blind to it — `tools/lap_shotscale.py`
declares in its own docstring that "occlusion is not modelled: a car behind a
barrier still measures full size" — and at f2185/f2190 it reports 4.66 % and
4.91 %, its most confident readings of the whole span, for two frames containing
no car.

## R2-1003 — four levers measured before one was chosen: aim, lens and "no event" refuted; distance available but not needed

The ending's lesson was that the obvious lever was wrong three times running, so
each candidate lever was measured before one was picked. Three did not survive
contact with a measurement. The fourth survived and turned out not to be needed,
which is a different thing and is recorded as such.

**Aim — refuted.** The car is at screen centre for the entire span:
|screen x| < 0.01, |screen y| < 0.02 in normalised frame units, every frame from
f2025 to f2240. There is nothing to gain by re-aiming; the camera is already
looking straight at it.

**Lens — refuted, and already refuted once.** The span already runs
**69.2-85.0 mm**, the longest glass in the film. Tripling the subject needs
~210-255 mm. R2-591 has already built and rebased the retune
(`render/film_path_R2581B_ramp_RETUNED_REBASED.json`, peak focal 142.5 mm,
median 4.41 % -> 6.11 %); R2-737 established it **cannot change which frames are
blocked**, because a sightline is focal-independent, and that it puts *more*
concrete on screen. A lens change cannot touch R2-1002 and R2-1001 says the size
did not need touching.

**"The shot has no event" — refuted by measurement.** The hypothesis was that
8 seconds of a centred, receding, long-lens subject is dead screen time. Mean
absolute frame-to-frame image change over the span is **0.97x the beat-5
median** — the **45th percentile**, dead average. The span is normally kinetic.
The quietest stretch of beat 5 is f1826-1876 at 2.60 %, half the span's rate, and
nobody has flagged it.

**Distance — a live lever, and the shipped 187 m is a CHOICE, not a constraint.**
This entry originally claimed the distance was forced. **That claim was wrong and
is retracted here rather than quietly deleted.** The arithmetic:

The camera runs 97 m -> 187 m ahead of the car between f2015 and f2160 because it
is travelling to the doppler station, and the beat sheet's anchors give the
reason: *"170 m of deceleration is what a hover costs"*, *"45, 33, 22, 8, 1.5 m/s,
five anchors, because arriving at a hover in one is a 6 g stop."* The obvious
inference is that a closer camera cannot make the station. **Measured, it can.**

From a +40 m lead at f2112, the run to the station is **428.2 m in 6.08 s**,
ending at rest. Cruise-then-brake, against `author_beats2_5.py`'s own envelope
(v <= 137.8 m/s, |a| <= 95.9 m/s^2 = 9.78 g):

| cruise speed | brake needed | |
|---:|---:|---|
| 88.3 m/s (the shipped path's own peak in this stretch) | 35.8 m/s^2 = **3.65 g** | within envelope, and *below* the shipped path's 5.01 g peak |
| 101.9 m/s (beat 5's peak camera speed anywhere) | ~27 m/s^2 = 2.8 g | within envelope |
| 137.8 m/s (the ceiling) | 23.2 m/s^2 = 2.36 g | within envelope |

At a 40 m lead cruising 88.3 m/s against a car doing ~78 m/s the lead grows to
roughly 86 m before the brake closes it — **peak distance ~86 m instead of
187 m**, which is about 9 % of frame width instead of 4.2 %. The lever is real
and it is affordable.

**So why is nothing here spending it?** Because R2-1001 says it does not need
spending. The picture at 187 m is a legible F1 car; buying 2.2x the subtense buys
nothing the frame was missing, and it would rewrite ~250 frames of authored
camera to do it. The correct statement is that the shipped 187 m lead is a
*defensible authorial choice* and R2-422's account of it as a hard cost of the
doppler station is **overstated**. Anyone who later decides beat 5 does want a
closer pass now has the budget for it in this table, and does not have to
re-derive that it is possible.

## R2-1004 — the fix: R2-738's bridge thread, rebased onto the live path and with wider ramps, closes the blackout for LESS camera acceleration than the shipped path

`tools/r2971_pont_camera_rebase.py` (new), output
`render/film_path_R2971_PONT_B5_REBASED.json`. **CANDIDATE — not merged.**

R2-738 had already found the answer and it had been sitting unlanded, blocked on
one thing: *"21 m of deviation over ~60 frames is a picture question needing eyes
on rendered frames."* R2-1001/1002 are those eyes. Two defects in the R2-738
package had to be fixed before it could ship.

**Defect 1 — stale base, the R2-737 trap again.**
`tools/r2731_pont_camera_apply.py --out` writes a whole-film path rebuilt from
the beat sheet. Measured against the live `render/film17_path.json`: **2,472 of
2,978 frames differ, worst 9.866 m at f545**, all of it in beat 1. Adopting that
file would revert beat 1's camera by 9.9 m to buy a 12-frame fix in beat 5 —
precisely what R2-737 caught in the lens retune. The cure is
`tools/r2731_lens_retune_rebase.py`'s: **carry the OFFSET across, never the
file.** The offset is a pure function of frame index and rebases exactly; the aim
is not, so it is re-derived, and the selftest's first control is that with the
offset forced to zero the re-derived aim reproduces the live quaternion.

That 9.866 m turns out not to be a rebuild artefact at all — see R2-1007, which
is the more serious half of this finding.

**Defect 2 — R2-738 as authored spends 95 % of the camera acceleration budget.**

| | blocked frames | peak abs a | vs the 95.9 m/s^2 craft limit |
|---|---:|---:|---|
| shipped | **11** (f2181-2191) | 49.1 m/s^2 (5.01 g) | 51 % |
| R2-738 as authored | **0** | **91.2 m/s^2 (9.29 g)** | **95 %** |
| **R2-1004 (this)** | **0** | **47.7 m/s^2 (4.86 g)** | **50 %** |
| R2-1004, wider still | 0 | 43.9 m/s^2 (4.48 g) | 46 % |

R2-738 noted "acceleration triples locally" and left it. Measured, it is 1.86x,
it peaks at **f2193**, and **the whole spike is in the lateral OUT ramp**, which
R2-738 runs over 22 frames. Widening it to 32 frames (f2178->2210) and starting
both in-ramps 12 frames earlier (f2133) leaves the displacement and therefore the
occlusion result untouched — the plateau of zero blocked frames is 6 m x 5 m wide
— and brings the peak **below the shipped path's own**. The fix now costs nothing
in the camera envelope instead of nearly exhausting it.

The displacement itself is unchanged from R2-738: **du +20.0 m inboard, dz -7.5 m**,
interior to the measured zero-blocked plateau (du 18..24 x dz -6..-11). The camera
goes from 5.1 m *above* the soffit and 29 m outboard — flying over a bridge it was
specified to go under — to threading the clear opening, which is what
`docs/circuit_spec.md` §10 said all along: *"threads under it at ~5 m altitude."*
Camera altitude at the pass drops 16.7 m -> 9.2 m (f2168), 13.4 m -> 5.9 m (f2192).

**Occlusion re-measured** with `tools/r2731_pont_full_sightline.py`, whose
`--selftest` reproduces two independent raycasts at two stations
(s=2410 -> f2181-2191, s=2460 -> f2196-2227) from the same code.

Run across **all four bands — girders, deck slab, parapet and mesh screen**, not
just the solid ones, so that f2180's fence-channel frame is included:

| | wholly hidden | partial |
|---|---|---|
| shipped | **f2180-2191, 12 frames** | f2192 at 0.52, f2193 at 0.02 |
| candidate | **none** | none |

The all-channel model reproduces the raycast's twelve-frame window and its f2192
partial (0.52 against the raycast's 0.581) without being tuned to, which is a
third independent agreement on top of the two its `--selftest` already carries.
**All twelve frames close, not eleven.** That the mesh screen stops mattering is
geometry, not luck: the screen sits at soffit + 2.72 m and the candidate passes
*under* the soffit, so no sightline from it to the car can reach the screen at
all.

Not a size fix, and not sold as one: shot scale over the edit window rises
4.75 % -> 5.29 % (+11 %) and the f2035-2227 median moves 4.24 % -> 4.27 %. The
subject was already legible (R2-1001); what changes is that for half a second it
now exists.

## R2-1005 — seams: both beat-5 boundaries are bit-identical, and the edit is smoother than what it replaces

**Before**, on `out2/seq/r2full` at 720p, mean absolute pixel difference across
the seam, against the interior frame-to-frame baseline on either side — a seam is
only a defect if it exceeds the motion that surrounds it:

| | mean | p99.9 | max |
|---|---:|---:|---:|
| f1189\|1190 (interior control, beat 4) | 4.669 % | 59.22 % | 81.57 % |
| **f1190\|1191 — BEAT 4/5 SEAM** | **4.983 %** | 59.61 % | 82.75 % |
| f1191\|1192 (interior control, beat 5) | 5.415 % | 58.43 % | 83.14 % |

The seam sits **inside** its own interior bracket. Clean, and it was clean before
this task touched anything.

**After.** The candidate's support is exactly **f2131-2224**, asserted frame by
frame, so:

| frame | dp | dq | |
|---|---:|---:|---|
| f1190, f1191 | 0.0e+00 m | 0.0e+00 | **bit-identical** |
| f2714, f2715 | 0.0e+00 m | 0.0e+00 | **bit-identical** |

The f2714/2715 seam and its 1.33 % interpolation measurement are untouched and
were never approached — the edit ends 490 frames short of it.

**The edit's own ends** are the only new seams, and they are C2 by smootherstep
construction. The test that matters is not the offset's derivatives but the
camera's actual per-frame translation, since that is what a seam would show up
in:

| | per-frame translation, f2120-2240 | worst frame-to-frame CHANGE |
|---|---|---:|
| shipped | 0.9564 - 3.6799 m | 85.28 mm |
| candidate | 0.9564 - 3.6707 m | **82.74 mm** |

The candidate's worst discontinuity is **smaller** than the shipped path's.

**Quaternion normalisation.** The base path's stored quaternions are 6-decimal
(R2-103), so they are unit only to **8.21e-07** — worst at f1550, and 7.10e-07
inside this window. The 94 quaternions this candidate writes are freshly computed
and unit to **1.11e-16**. The output is therefore *cleaner* than its input inside
the window and bit-identical to it outside; any downstream check must use
R2-103's rounding floor, not an exact-unit assert, or it will fail on frames
nobody touched.

**Quaternion continuity**, because Blender lerps quaternion F-curves
component-wise and past 2pi between keys the rotation runs backwards: over
f2127-2228 the candidate has **0 hemisphere flips against the live path's 0**,
and its largest single-frame rotation step is 1.19 deg (live 0.91 deg). The
selftest fails if the candidate introduces a flip the live path does not have.

## R2-1006 — the clearance gate: PASSED at 2.391 m against a 1.20 m sphere; what remains open, and what it costs

**Measured, and it is a real cost: the camera's margin against the car's own
corridor.** R2-738 flagged that its candidate halves the closest the car ever
comes to a camera *position*, 21.43 m -> 9.40 m. This variant, holding inboard
longer, takes it to **8.97 m** — camera at f2183 against where the car will be at
f2238, **55 frames (2.29 s) later**. It is not a proximity in time and not a
collision: the *simultaneous* camera-to-car distance over the window is unchanged
at a 137.3 m minimum. But 8.97 m of standoff from the racing line is the price of
threading the opening, and it should be seen before it is accepted, not after.
The camera's lowest point drops from z 10.02 m to **z 5.78 m** at f2195 — which
is the ~5 m altitude `circuit_spec.md` §10 specified for this pass in the first
place.

**CLOSED: the triangle-level clearance gate. `>> STAGE RESULT: CAM_CLEAR_OK`.**
`tools/r2731_camera_clearance.py --mods barriers,architecture` against the built
world (162 objects, 15.8 M triangles), selftest passing inline (a plane planted
at 3.000000 m reads back 3.000000 m, one behind the camera reads as distance not
projection):

| path | min clearance | frame | nearest object |
|---|---:|---|---|
| shipped | **3.881 m** | f2250 | `BR_FenceWire_R` |
| R2-738 as authored | 2.506 m | f2194 | `BR_Runoff_R` |
| **R2-1004 (this)** | **2.391 m** | f2194 | `BR_Runoff_R` |

**Zero frames inside `placement_gate.py`'s 1.20 m camera sphere; the worst point
is 1.99x the gate radius.** The wider ramps cost **0.115 m** against R2-738 — same
frame, same object, so they do not move the pinch point. The tool reproduced
R2-740's 2.506 m exactly on its unchanged defaults before the new path option was
used, which is what makes the 2.391 m comparable.

Two things this measurement corrected, both worth carrying:

* **The bridge is not the constraint.** `ARCH_PontPlongee` is the nearest object
  on only 4 of the 116 frames, closest 2.719 m at f2175. The real minimum is
  `BR_Runoff_R` — runoff and barrier furniture on the way back *out* — exactly
  where R2-740 said to look.
* **A shipped figure of 4.516 m measured over f2125-2240 is a window-boundary
  artefact**, not a comparable number: the shipped curve is still descending at
  f2240. Over R2-740's own f2120-2250 the shipped minimum is 3.881 m and the
  candidate's stays 2.391 m at f2194, an interior minimum either way. **The
  honest statement is 2.391 m against 3.881 m — tighter by 1.49 m, versus
  R2-738's 1.38 m.**

**Still not run: `tools/placement_gate.py` itself.** The clearance tool measures
distance to the world; the placement gate also tests the road corridor and the
car's swept path. Given 2.391 m against a 1.20 m sphere it is very unlikely to
fail, but "unlikely" is not the same as run.

**Not run: the rig rebuild and `world/camera_rig_continuity.json`.** R2-738 named
this and it is still true.

**Not done: the B-side render.** The picture proof of the *fix* (as opposed to
the defect) needs the candidate keyed onto `ONER` and 6 frames rendered.
**Cost: 6 frames x 3840x2160 x 512 samples ~= $0.17**, plus one `rq exec` to key
the camera and save a candidate blend.

**Not submitted, and the reason is contention rather than money.** `rq exec` has
been at **12/12 slots for over an hour**, held by `r2943` (rekeying f2715-2978)
and `r2851ab`; a third build that saves an 8 GB blend into that is a real risk of
`StaleBundle` and of disturbing two agents mid-flight, for $0.17 of insurance.

**This is now the only thing between this candidate and shippable.** Every
measurable axis has been checked and passes — occlusion 12 -> 0, acceleration
below the shipped path's, clearance 2.391 m against a 1.20 m sphere, both beat
boundaries bit-identical, no new quaternion flip. What is left is a **taste**
question that no gate can answer: the camera drops from 10.0 m to 5.8 m and swings
20 m inboard for ~90 frames, and whether that low thread under the bridge is
*better cinema* than the high outboard pass is for the director, not the
instruments. Six frames answers it. Recommend rendering them when a slot frees.

**Not merged into `docs/beat_sheet.json`, deliberately**, on R2-591's rule:
*"other agents have live candidate sheets in that file, and two agents writing
one sheet is how a one-shot film acquires a seam."* `r2943` is live in
`film17_breach.blend` right now. The merge is 12 beat-5 camera keys, or one
`--path` swap at rig-build time; it belongs to the main thread.

## R2-1007 — `world/camera_rig_path.json` is three days stale, and the beat-1 camera on disk is 9.866 m from the film's

Found while validating the base of the fix above; it is not a beat-5 defect and
it is the most consequential thing in this file for anyone else.

| | |
|---|---|
| `world/camera_rig_path.json` (Aug 04 15:49) | **byte-identical to `render/film16_path.json`** |
| vs the live `render/film17_path.json` (Aug 07 05:59) | **768 frames differ, worst 9.866 m at f545**, span f2-f780 |
| over beat 5 (f1191-2714) | **0.00e+00 m** |

So the 9.866 m in R2-1004's Defect 1 is **not** a rebuild artefact of
`r2731_pont_camera_apply.py`. That tool was reading `world/camera_rig_path.json`,
which is the rig file, and **the rig file is what is out of date**: beat 1's
camera moved when film17 was built and the rig path on disk was never rewritten.
The tool was faithfully reproducing a stale input.

**Why this matters beyond beat 1.** `tools/r2731_pont_full_sightline.py` reads
`world/camera_rig_path.json` as its camera source, and so do the occlusion
instruments built on the same convention. Every occlusion and sightline result in
beats 2-6 is unaffected — the two files are identical from f781 on — but **any
beat-1 result from those tools is measured against a camera the film no longer
has.** Nothing here re-runs them; this entry exists so nobody has to rediscover
why a beat-1 number will not reproduce.

Not fixed here on purpose: `world/camera_rig_path.json` is the rig build's
output, not a hand-edited file, and rewriting it belongs to whoever owns the rig
build. The one-line check is
`python3 -c "import json,math; L=lambda p:{k['f']:k for k in json.load(open(p))['path']}; a,b=L('world/camera_rig_path.json'),L('render/film17_path.json'); print(max((math.dist(a[f]['p'],b[f]['p']),f) for f in a))"`.

## R2-1008 — a per-frame cost datapoint for whoever is costing the 4K master

Incidental, but it is a real measurement at the shipping spec and the master's
affordability is live. These 6 frames averaged **235 s/frame** at 3840x2160 /
512 samples / `film17_breach.blend`, against `m4k_probe`'s **196 s/frame** on
`film16_breach.blend`. At 235 s the full 2,978-frame master is **194 GPU-h =
~$85.5** at $0.4403/hr, against the $71.40 currently assumed.

**Do not treat that as a re-forecast.** Two confounds, both plausible and neither
separated here: these frames were rendered on a card with 12/12 exec slots busy
serving two other agents, which inflates wall time; and beat-5 aerials are not a
representative sample of the film. What is solid is that 235 s/frame was observed
on the current blend under current farm conditions, and it is 20 % above the
figure the master estimate rests on. Worth one clean, unloaded frame to separate
the two before anyone budgets against either number.

## R2-1009 — two corrections to the brief this task was given

1. **"1,247 contiguous frames" is not what is on disk.** `out2/seq/r2full` holds
   1,247 frames covering f793-2978, but only **f793-1281 are contiguous** (489
   frames); from f1286 the sequence is **1-in-5**. Beat 5 f1191-2714 is covered
   at 39 frames over the f2035-2227 span, not 193. Adequate for composition,
   which is what it was used for; not adequate for anything per-frame.

2. **The run is longer than 8.04 s and this was already known.** R2-582 measured
   the true continuous sub-10 % run as **f2012-f2256, 245 frames, 10.21 s**,
   median 4.41 % — *"the longest continuous run under 10 % of frame width
   anywhere in beats 2-6, including beat 6 itself."* f2035-2227 is R2-581's
   narrower window. Both are now superseded as a *defect* by R2-1001 anyway; what
   survives is R2-1002, which is 0.50 s inside it.

---

### Files touched

| file | |
|---|---|
| `tools/r2971_pont_camera_rebase.py` | **new.** Rebases R2-738's offset onto the live path, widens the ramps, 8 controls incl. a null that must reproduce the base |
| `render/film_path_R2971_PONT_B5_REBASED.json` | **new, candidate.** Live path + the offset over f2131-2224. Not wired to anything |
| `work/r2971/cam_candidate_path.json` | scratch: `r2731_pont_camera_apply.py`'s own output, kept only to document the 9.866 m stale-base delta |
| `docs/STAGING-R2-1001-to-R2-1030.md` | this file |
| `out2/seq/b5verdict_4k` | 6 frames, 4K, **$0.173 measured** |
| `tools/r2731_camera_clearance.py` | **modified, additively** — gained a path-selection option so the gate can be pointed at a candidate other than R2-738's. Existing default behaviour unchanged |

This task modified **nothing** in `docs/beat_sheet.json`, `docs/DEFECT-LOG-R2.md`,
`anim/`, `audio/`, `world/`, `telemetry/`, or any `render/film*.blend`, and
committed nothing. Other agents' edits are live in the same working tree
(`audio/scene.py`, `world/camera_rig_path.json`, `world/build_*.py` and others
show as modified and are **not** this task's) — anyone staging these changes must
use path-scoped `git add`, never `-A`.

One consequence of that, worth stating rather than discovering at merge:
`world/camera_rig_path.json` is currently dirty in someone else's hands. This
candidate was rebased onto `render/film17_path.json`, which is clean and which
was verified **identical to `world/camera_rig_path.json` over the whole of beat 5
to 0.00e+00 m**. `tools/r2971_pont_camera_rebase.py` takes `--base`, so at merge
time it should simply be re-run against whatever path is live rather than the
output file being adopted as-is.
