# STAGING R2-2881 to R2-2940 — per-beat pixel-peep defect gates

Agent `r2-2881-pixelpeep`. Task #38. All work on the delivered pixels of
`work/r22161_proxy/` — all 2,978 frames of the complete film, 960×540, rendered
from `render/film22.blend` on the camera `docs/LIVE-CAMERA.md` declares.

Tool: **`tools/r2_2881_pixelpeep.py`** (new).
Outputs: `work/r22881/` — `scan.npz`, `subject_boxes.json`, `subject_valid.json`,
`findings.json`, `selftest.log`, `gate.log`, `crops/`.

```
python3 tools/r2_2881_pixelpeep.py subject | scan | gate | selftest | crops
```

---

## R2-2881 — THE HEADLINE: THE CLIENT'S NOTE IS INVERTED. THE GRASS IS FINE; THE ASPHALT IS BLANK.

The client wrote *"anything 5 feet away from the road has blank grass, no
detail"* and *"tire marks not noticeable enough"*. Measured on the delivered
pixels, **those are one defect, and it is not the grass.**

The verges, banks and scrub carry detail. **The road surface does not.** Across
beat 5 the emptiest regions of the frame are, in order, the bottom three rows —
and the crops show them to be bare tarmac, not vegetation. `f1787` is the
cleanest example in the film: the camera is directly over the car, the car is
1,675 px tall at 4K and fully modelled, and **the road it is sitting on carries
0.00069 of coarse-band energy against 0.00853 for the verge in the same frame —
12× less, on the same frame, through the same lens, at the same grade.**

Evidence, 1:1 crops, `work/r22881/crops/`:

| sheet | what it shows |
| --- | --- |
| `finding_ASPHALT_f1787.png` | the road under the top-down car vs the verge, same frame |
| `finding_ASPHALT_f1350.png` | the near lane vs the kerb beside it, same frame |
| `finding_RUNOFF_f2500.png` | the right-hand apron vs the grass verge, same frame |
| `finding_LAP_subject.png` | the subject through beat 5 at its delivered size |
| `control_G3_empty.png` | the damage the emptiness gate is required to catch |
| `control_G1_dissolve.png` | the subject dissolved into its background |
| `control_G1_blur.png` | the subject blurred by 12 px at 4K |

The left-hand panel of each finding sheet is a featureless field. The right-hand
panel is **from the same delivered frame**, so it is proof the emptiness is not a
limit of the renderer, the grade, the denoiser or the proxy.

**This is actionable in a way the client's own note was not.** "Add detail to the
grass" would have been work spent on the part of the frame that already passes.

---

## R2-2882 — WHAT THE PROXY IS AND IS NOT ENTITLED TO DECIDE

960×540 is a quarter of delivery in each axis, so one proxy pixel is four 4K
pixels. A Laplacian pyramid on the proxy reads these bands:

| level | proxy px | **4K px** | what lives there |
| --- | --- | --- | --- |
| L0 | 1–2 | **4–8** | stipple, weave, fine noise |
| L1 | 2–4 | **8–16** | gravel, kerb teeth, panel lines |
| L2 | 4–8 | **16–32** | tufts, clumps, tyre marks, shadows |
| L3 | 8–16 | **32–64** | bushes, barrier posts, road furniture |
| L4 | 16–32 | **64–128** | buildings, banks, hills |
| — | <1 | **0–4** | **the proxy is blind here, and so is this instrument** |

The consequence, which is the whole epistemics of the tool:

* A region with **no energy at L2–L3** is empty at scales of 16–64 4K pixels.
  Rendering it at 4K cannot put structure there, because the structure is missing
  at scales the proxy resolves perfectly well. **The proxy may close that on its
  own.**
* A region with L2+ energy but no L0/L1 energy is **inconclusive** — the proxy's
  own Nyquist eats that band, and only a 4K render can say.

So the instrument never says "the detail is absent". It says **"the detail is
absent at or above N 4K pixels", and it prints N.** The asphalt finding above is
of the first kind and is therefore closed on proxy evidence.

**L4 is measured but deliberately excluded from the emptiness verdict.** A
feature 16–32 *proxy* px across is a third of a tile wide and cannot be
attributed to a tile whatever margin is used; L4 is composition, not surface.

---

## R2-2883 — THE FOUR GATES, THE DAMAGE EACH WAS OBSERVED TO FAIL ON, AND ITS FALSE-POSITIVE RATE

`selftest` damages a real frame and requires the gate to fail on the damage
**and to leave the untouched neighbours alone**. Ten controls; full transcript in
`work/r22881/selftest.log`. `>> STAGE RESULT: SELFTEST_OK`.

| gate | what it measures | threshold | provenance of the threshold |
| --- | --- | --- | --- |
| **G1 subject** | size in 4K px; separation from surround; in-box detail vs surround | 60 px; sep 0.10; detail 0.85 | sep null is 0.040 by construction; detail from the C4 damage |
| **G2 footprint** | which 4K-pixel band the frame's detail actually sits in | arithmetic | reproduces 2.17 px already on the record |
| **G3 empty** | per-tile coarse band, L2–L3, ≥16 px at 4K | 0.0020 | 1.40× the C1 flatten control, 9.6× below that tile intact |
| **G4 seam** | local robust z of interframe MAD and histogram distance | z ≥ 8 | splice control fires at 38.83 |

| control | damage | intact → damaged | verdict |
| --- | --- | --- | --- |
| C0 agreement | — | box width vs `lap_shotscale.series`, 1,523 frames of beat 5 | **0.00e+00**, and non-zero past the telemetry as required |
| C1 empty | one tile flattened to its mean + the film's own grain | 0.01694 → **0.00087** | fires; **0 of the other 47 tiles change verdict** |
| C2 empty/FP | whole frame blurred by 8 px at 4K | 0 of 48 tiles newly empty | motion blur is not mistaken for emptiness |
| C2 bands | same blur | L0 share 0.113 → 0.036; L4 0.288 → 0.370 | the pyramid is scale-selective |
| C3 subject | car 90 % dissolved into its own surround | sep 0.387 → **0.000** | fires |
| C4 subject | car blurred by 12 px at 4K | detail 2.425 → **0.779** | fires |
| C5 vacuity | measurement pointed 400 px off the car | sep 0.387 → **0.045** | it is reading the car, not scenery |
| C6 seam | a frame from 209 frames away spliced at f1190→f1191 | z 0.86 → **38.83** | fires |
| C7 footprint | 0.062 m at 152.20 m on a 50 mm lens | **2.17 px** at 4K | reproduces the record; below the proxy's own floor, so refused |
| C8 box/beat | C5 run per beat, both boxes required in frame | see below | **refuses beat 6 outright** |

**False positives, on the 2,978 frames known to be good:**

```
G3 empty     15.00 % of 142,944 tiles; 50.94 % of frames over 6 tiles
             (sky excluded first: 15,956 tiles, 11.2 %)
G1           on the 2,714 frames whose box C8 validated:
             separation 10.80 % of frames, detail 1.14 %
G4 seam       0.10 % of 2,978 transitions — three frames, and they are f899-901,
              the breach transit, i.e. the largest real optical event in the film
```

G1's flags are not scattered; they fall in coherent runs (`f300-323`,
`f2156-2205`), which is what a finding looks like and what noise does not.

### Two threshold mistakes the controls caught, both of which had already passed

1. **`SUBJ_DETAIL` was 0.55 and the C4 damage went straight through it.** A 12 px
   blur on the car did not trip the gate. Moved to 0.85 — set by the damage, not
   by taste.
2. **A colour-based material classifier was written, then rejected.** `film22`'s
   grade is uniformly warm — R > G > B on *every* tile sampled; grass reads
   0.31/0.28/0.16, asphalt 0.27/0.25/0.14, overcast sky 0.71/0.69/0.67. Green
   dominance does not exist anywhere in the delivered pixels. The classifier
   scored 95 % "OTHER" on beat 5 and 100 % on beat 6. **Colour carries no
   material signal on this film.** Sky is excluded by position + brightness
   instead, which is testable and tested.

---

## R2-2884 — AN INSTRUMENT DEFECT THE GATE FOUND: THE TILE WAS READING ITS NEIGHBOURS

The first C1 control **failed, and it was right to.** A tile flattened to its own
mean still read 0.00480 against a 0.0022 threshold — it passed as "not empty"
while being, by construction, completely empty.

Cause: a coarse Laplacian coefficient near a tile edge is computed from a blur
that reaches across the border, so an empty tile inherits its neighbours' detail.

Fix: **every tile number is now taken on the middle 96 × 66 of a 120 × 90 tile.**
At margin 12 the same flattened tile reads 0.00143 and its intact self 0.01919 —
a 13× separation instead of a 4×.

This mattered in the direction that flatters the film: before the fix the
instrument was **under**-detecting emptiness.

---

## R2-2885 — A DEFECT IN A SHARED INSTRUMENT: `lap_shotscale.py` PARKS THE CAR FOR THE WHOLE OF BEAT 6

`telemetry/telemetry.csv` ends at world t **72.5833 s**. The film's world time
runs to **83.6115 s**. The last **11.03 s — all 264 frames of beat 6 — are
authored, not measured**: `anim/carpath.Car` continues the car along the circuit
centreline and applies the R2-943 lap-down, which is what the delivered pixels
show.

**`tools/lap_shotscale.py` keeps its own copy of the telemetry reader, and that
copy clamps** (`t = max(0, min(t, self.t_end))`). It therefore parks the car at
`(326.2, 167.2)` for the whole of beat 6 while the film drives it to
`(502.9, 315.4)` and stops it there:

| frame | film car (`anim/carpath`) | speed | clamped (`lap_shotscale`) | error |
| --- | --- | --- | --- | --- |
| 2714 | 328.2, 168.8 | 89.8 m/s | 326.2, 167.2 | 2.5 m |
| 2760 | 426.6, 251.4 | 46.4 m/s | 326.2, 167.2 | **131.1 m** |
| 2850 | 495.2, 309.0 | 7.4 m/s | 326.2, 167.2 | **220.6 m** |
| 2978 | 502.9, 315.4 | 0.0 m/s | 326.2, 167.2 | **230.7 m** |

Two copies of the same physics, one of them stale, failing silently with no
error — the R2-1007 shape again, in a different file. The divergence is already
**2.53 m inside beat 5**, at its end.

**Anything in this project that measured the beat-6 subject through
`lap_shotscale` is suspect and should be re-derived from `anim/carpath`.**
This tool now reads `anim/carpath.Car` and C0 asserts both halves: exact
agreement inside the telemetry, and a **non-zero** divergence outside it, so the
fix cannot silently revert.

---

## R2-2886 — RETRACTION: MY OWN BEAT-6 SUBJECT VERDICT, PUBLISHED AND THEN WITHDRAWN

Built on the clamped reader, this gate reported — and I nearly shipped — that in
beat 6 the car was **"2,349 px off the left of frame at f2978"** and that
**"32.2 % of the ending is under 60 px at 4K"**, with a crop strip showing six
black tiles as evidence the subject had vanished.

**Both are artefacts. Both are retracted.** The car is on the track and visible
throughout beat 6; `work/r22881/zoom_2760.png` shows it plainly.

And the correction was **not sufficient**. With `anim/carpath` the predicted
centre moves to frame centre — plausible, but still **~92 proxy px (368 px at 4K)
off the visibly rendered car at f2760**. `work/r22881/verify_boxes.png` puts the
predicted centre on the car at f1900 and f2500 and on **empty asphalt** at f2810
and f2900. The residual is most likely the beat-sheet time map: `film22.blend`
was built at 04:42 and the sheet on disk was promoted at 06:22, so the sheet that
built the delivered proxy is **not pinned** and may not be the sheet on disk.

**So there is no beat-6 subject verdict in this report.** The gate refuses to
print one:

```
REFUSE  C8 box/6_ending  separation 0.011 on the box vs 0.016 at 400 px off it,
                         lift 0.69x -- THE BOX IS NOT ON THE CAR HERE
```

**Open, and blocking any future claim about the ending's subject:** pin the beat
sheet `render/film22.blend` was actually built from, the way
`work/r22161/beat_sheet_PROMOTED.json` pins the other arm.

---

## R2-2887 — THE VERDICT ON THE FILM, BEAT BY BEAT

Full numbers in `work/r22881/findings.json` and `work/r22881/gate.log`.

| beat | frames | G1 subject | G3 empty (of 48 tiles) | verdict |
| --- | --- | --- | --- | --- |
| 1_assembly | 1–792 | size only, p50 **1,620 px** @4K | 4 p50, max 19 | **no optical defect found** |
| 2_launch | 793–864 | size only, p50 **996 px** | 3 p50, max 9 | **clean** |
| 3_breach | 865–1056 | size only, p50 **1,164 px** | 6 p50, max 12 | **clean**; f899–901 is the breach, not a seam |
| 4_transit | 1057–1190 | p50 **270 px**, sep 0.381, **0 % low** | 6 p50, max 14 | **clean** |
| 5_lap | 1191–2714 | p50 **214 px**, sep 0.409, **0 % low** | **10 p50, max 31** | **THE DEFECT BEAT** |
| 6_ending | 2715–2978 | **REFUSED** (R2-2886) | 1 p50, max 6 | **cleanest beat in the film** on G3 |

### Beat 5 is the one to fix, and it is the road surface

* **10 of 48 tiles empty on the median frame**, 31 at worst; 70.1 % of the beat
  over the 6-tile mark.
* The empties are bottom-weighted — rows 5 and 6 carry **10,100 of 15,719**, i.e.
  **the near-field ground**, which is the largest, sharpest, most-looked-at part
  of every frame.
* Worst frames: **f1685–1688, f1784–1787, f2622**.
* The subject itself is healthy: separation p50 0.409, **zero** low-separation
  and **zero** low-detail frames in 1,524. One run, **f2156–2205** (50 frames,
  2.1 s), has the car under 60 px at 4K, minimum **51.6 px**.

### Beat 1 — the client said it "could be extraordinarily better"; the pixels do not say why

Beat 1 is the **densest** beat in the film by measured detail (L2+ share 80.1 %,
highest of the six) and its emptiness is mid-pack. Its worst tiles are the dais
floor. **G3, G2 and G4 find nothing wrong with beat 1.** Its G1 is size-only
because the car is exploded across 616 parts and the box is the assembled one.
Whatever the client is reacting to in beat 1, **it is not detail density, not
subject size, and not a seam** — so it is staging or pacing, and this instrument
is the wrong tool for it. That is a useful negative: it rules out the three
explanations that cost the most to act on.

### The one unbroken take holds

**All five beat boundaries are clean.** Worst z across the five is **1.50**
against a threshold of 8.0, on an instrument whose splice control fires at
**38.83**. The three film-wide outliers are **f899, f900, f901** — the car
transiting the glass, already on the record as the breach, and the correct
answer for the largest optical event in the film.

**The film is in better shape than the client's notes suggest.** Four of six
beats have no optical defect this instrument can find; the take has no seam; the
subject is legible wherever it can be validated. The whole recoverable defect is
one material, in one beat, in the bottom third of frame.

---

## R2-2888 — 4K CONFIRMATION (in flight)

Per the standard that nothing is declared absent on proxy evidence alone, four
targeted 4K frames were commissioned at the proxy's exact spec (ONER, 32 samples,
CYCLES + OIDN, adaptive 0.01) — **f1350, f1787** (the asphalt finding) and
**f2730, f2850** (beat 6). Landing in `work/r22881/4k/` with provenance.

The asphalt finding does **not** depend on them: it is a coarse-band absence at
16–64 px at 4K, which is above the proxy's floor. The 4K arm can only add whether
there is sub-8-px detail down there that a viewer would never see anyway.

---

## Files

```
tools/r2_2881_pixelpeep.py              the instrument
work/r22881/scan.npz                    2,978 frames x 48 tiles x 5 bands
work/r22881/subject_boxes.json          per-frame subject box, film22 camera
work/r22881/subject_valid.json          which beats' boxes C8 validated
work/r22881/findings.json               the verdict
work/r22881/selftest.log                the ten controls
work/r22881/gate.log                    the per-beat run
work/r22881/crops/                      before/after evidence, 1:1
work/r22881/verify_boxes.png            why beat 6 is refused
work/r22881/empty_overlay.png           the emptiness map on six frames
```

Not touched: `docs/DEFECT-LOG-R2.md`, `docs/beat_sheet.json`,
`tools/build_beatsheet.py`, `tools/author_beats2_5.py`,
`tools/placement_gate.py`, `tools/item_placement_gate.py`, the verification bar,
and everything under `/home/zany/opus5-car-render`.
