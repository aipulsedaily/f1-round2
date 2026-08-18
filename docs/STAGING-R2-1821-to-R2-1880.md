# STAGING — R2-1821 to R2-1880 — the client's f2760, re-measured where nobody looked

Numbers to be assigned by the log's owner. **`docs/DEFECT-LOG-R2.md` not edited.**

The brief: R2-1156 measured the client's *"anything 5 feet away from the main road
and buildings have blank grass no detail nothing"* on `watch/r2943_4k/r2943_4k_002760.png`
and found a 3.8× detail cliff. R2-1149/R2-1150 had just fixed the ending's ground —
`dist3` and 264,890 sward drifts, 4 % → 72 % screen cover — **but verified it at
f2811**, a high aerial over open infield. f2760 is a different vantage: large
near-field grass beside built structures, filling the lower half of frame.

**The question was whether the fix already covers f2760. It does not, and the reason
is a mask nobody had measured.**

---

## R2-1821 — the fix covers 53 % of the frame's ground and is SWITCHED OFF over the other 47 % by a rectangle drawn by hand

`habitat()`'s `built` is a district drawn in circuit space — x −490..140, y −70..120,
feathered 26 m, plus a 344 m box round the showroom. **16.50 ha.** Every ground-cover
tier multiplies itself down by it: the verge band deletes on it outright, the meadow
takes ×0.08, and **R2-1661's new sward drifts inherited it verbatim at ×0.10.**

The contract declares the paving itself, and `world_contract` §11 says in terms that
the two are meant to be *"the same region stated once so the extents cannot drift"*.

**Sampled over the drawn box:**

```
actually paved by build_architecture          31.9 %
inside the road corridor                      20.7 %
OPEN GROUND this module owns, and sterilises  47.7 %   = 7.98 ha
```

**And the southern half of it — circuit y −70..0, 4.83 ha — is 0.0 % paved.** Not one
square metre of architecture is in it. It is the field beside the pit building. It is
the region the client described.

**Measured on f2760's own frustum**, by ray-marching the camera through the module's
own height field and evaluating the module's own predicates at 17,871 ground samples:

```
                                        BEFORE (R2-1661 as landed)   AFTER (R2-1821)
ground in frame inside the mask                   46.7 %                    8.8 %
sward density, inside the mask                     0.049                    0.002
sward density, outside it                          0.472                    0.412
sward density, whole frame                         0.275                    0.376
```

**A 9.7× step in ground cover, and the mask is a rectangle**, so its feathered edge
lays that step across open farmland **as a straight line answering to nothing in the
picture**. R2-1661 caught tiers that would have laid density rings at 200 m and 520 m
and crossfaded them away; this is the same artefact drawn by the *mask* instead of by
the tiers, and it survived because no metric was pointed at it.

The transition across the client's field, screen row y = 1750, predicted ground cover:

```
before   0.00 0.00 0.00 0.01 0.02 0.06 0.07 0.08 0.09 0.10 0.18 0.36 0.59 0.94 1.06
after    0.00 0.00 0.00 0.06 0.25 0.58 0.72 0.84 0.95 1.09 1.02 0.98 0.97 1.13 1.08
f (m)      -0    3    7   12   17   22   26   31   36   40   45   50   54   59   64
```

### And the failure is a GRADIENT IN THE CLIENT'S OWN SENTENCE

The bottom-right field is the complaint. Cut it into bands by distance from the pit
wall and R2-1661's coverage falls off exactly the way the client described it —
**perfect at the far edge, nothing at all against the wall**:

```
band (4K pixels)                        n     R2-1661   R2-1821     gain
outer field    x2900-3840 y1500-2100  1410      0.998     1.023      +3 %
mid field      x2450-2900 y1400-2100   805      0.521     1.021     +96 %
NEAR the wall  x2050-2450 y1250-1750   500      0.058     0.593    +924 %
along the wall x1500-2100 y1450-2100   990      0.069     0.647    +838 %
whole BR quadrant                     5184      0.616     0.883     +43 %
```

**This is why f2811 passed and f2760 did not, in one table.** f2811 is a high aerial
over open infield — all of it "outer field", where R2-1661 scores 0.998 and is
genuinely finished. f2760 puts the wall in the frame, and against the wall the same
fix scores 0.058.

> **Two agents verified the same layer on two frames and got opposite answers, and
> NEITHER WAS WRONG. The verification frames were sampling different regimes of an
> unmapped gradient.** The client's sentence — *"anything 5 feet away from the main
> road and buildings"* — **is a gradient in distance from a rectangle nobody had drawn
> on the picture.**

That is the transferable part, and it is sharper than the rule it refines. *"A fix
verified at one frame is not verified at another"* was already this project's most
expensive lesson; what this pass adds is **why**. A verification frame is a *sample* of
a field whose shape nobody has drawn. **When two frames disagree, the useful question
is not which one is right — it is what quantity varies between them, because that
quantity is the defect.** Here it was neither distance from the lens nor distance from
the track: it was distance from an artefact of the source that has no counterpart
anywhere in the picture. That is exactly why no amount of looking at either frame would
have found it, and why evaluating the PREDICATE over the frustum found it in one pass.

Frame-wide, ground predicted to read as a flat wash (cover < 0.15, the level the
metric's own empty-ground control sits at):

```
R2-1661 as landed                                        55.9 % of frame ground
with R2-1821                                             41.6 %
  ... of which is the ROAD CORRIDOR, not terrain's at all 17.6 %
  ... of which is architecture's DECLARED CONCRETE         8.8 %
```

**26.4 of those remaining 41.6 points are asphalt, runoff, gravel and concrete —
surfaces that are supposed to be flat.**

---

## R2-1822 — the client's "5 feet" is literal, and it is THREE tiers stopping for three different reasons on one strip of ground

The band from the corridor rim out to 12 m outboard — **9.5 % of the ground in frame**,
77 % of it inside the drawn district — carried:

* **no verge clump**, because `keep &= (built < 0.35) | inside` deleted everything
  outboard of the rim over the whole pit straight;
* **no sward drift**, because the tier gate is `f > 12.0`;
* **no meadow clump**, because that tier ramps from `f = 18`.

**An earlier author had already found this exact mask breaking the verge and patched
it with `| B["inside"]`** — which saved the strip *inside* the corridor and left
everything outboard of the rim deleted. The comment naming the bug is still in the
file. **This is the third time the same rectangle has produced the same defect**, and
the first two were patched at the call site rather than at the mask.

---

## R2-1823 — the fix: one predicate, and this module already trusted the contract for the same question

`cut_field` cuts the ground **mesh** against `C.platform_field`, whose outside-corridor
area agrees with build_architecture's own reported `paving_m2` **to 0.3 %**. Terrain
was cutting its ground to the footprint and then refusing to *plant* on the district.

```python
paved = smoothstep(BUILT_STANDOFF_M, 0.0, C.platform_field(x, y))
```

`paved` drives the **three ground-cover tiers only** — verge band, meadow, sward
drifts. Trees, shrubs, ferns, weeds, grit and the park species mix still read `built`,
because a tree keep-out around a paddock genuinely *is* a district and those tiers are
calibrated against that box. **Changing one predicate is a fix** (R2-1149).

`BUILT_STANDOFF_M = 3.0` is **sized, not chosen**: a tier-A sward drift is drawn over
1.45 × its 2.30 m pitch, so its half-extent is 1.67 m, and 3.0 m keeps every leaf off
architecture's concrete while letting the grass meet the pavement. A hard edge *at* a
kerb is correct; the defect was a soft edge 300 m away from one.

Because a plant standing where `platform_field > 0` always has ground under it — the
mesh is cut to the same field — this mask cannot float a drift, which the old box
could not promise.

**Not touched:** `Ground.height` keeps its own copy of the drawn box, so the landform,
the platform flattening and the ground shader's `built` attribute are byte-identical.

---

## The instruments

**`tools/r2_1821_ground_detail.py`** — the fine-detail sd R2-1156 measured with, made
reproducible: high-pass at 9 px, sd per 32 px tile, **median** over the region. It
publishes an **anisotropy** number beside every sd, because fine-detail sd cannot tell
*"no vegetation"* from *"vegetation smeared by a moving crane"*, and this frame smears.
Two run-time controls (R2-072): a synthetic sward at 55 % cover must exceed the
architecture reference; the same ground with the tufts removed must read near zero.

**`tools/r2_1821_paved_check.py`** — runs the module's own `verge_band`, meadow and
sward placement and asserts the shoulder comes back, the paddock does not, and
**nothing lands on `C.apron_platform_mask`**. The third is the one that matters: a
count of what came *back* cannot see grass growing through a garage.

---

## The measurement on the client's frame

**THERE ARE THREE STATES OF THIS FRAME AND THEY MUST NOT BE MIXED UP.**
`watch/r2943_4k/r2943_4k_002760.png` is state 1: it was rendered by R2-1129 and
**predates R2-1661 entirely** — no `dist3`, no sward drifts. It is what the client is
looking at, and it is the only *rendered* evidence that existed when this pass began.
State 2 is R2-1661 as landed, state 3 is R2-1821. **The measurement below is state 1;
the coverage tables above are predicted state 2 against predicted state 3; the A/B
below renders 2 against 3.** Nothing here claims R2-1661 leaves the client's box at
0.96 — R2-1661 was never rendered at this camera before today, which is the whole
reason this pass exists.

`tools/r2_1821_ground_detail.py watch/r2943_4k/r2943_4k_002760.png --selftest`

```
region                              fine-detail sd    anisotropy
grass beside the pit building              0.96          1.34
LEFT infield                               1.28          1.29
treeline / scrub band                      4.25          1.01
verge beside the track                     6.42          1.68
pit buildings (reference)                  6.17          1.90
--- controls ---
synthetic sward @ 55 % cover               9.04
the same ground, tufts REMOVED             0.63
```

**The client's grass reads 0.96 against a mathematically empty surface at 0.63.** It
is 15 % of the architecture and 15 % of the verge five metres away — harsher than
R2-1156's 19 % / 26 %, because the median-of-tiles reads the ground itself rather than
the boundaries crossing it.

**And it is not the motion blur.** The two blank ground regions read anisotropy
1.29–1.34; the regions scoring 5–6× higher read 1.68–1.90. **The blank ground is the
least smeared thing in the lower frame.** Reporting the sd without the anisotropy is
how a camera-speed problem gets fixed as a ground problem.

---

## R2-1824 — the tier crossfades HOLD at the new vantage, and the one hard edge left in the sward layer is its outermost

R2-1661 caught tiers that would have laid density rings at 200 m and 520 m and
crossfaded them away. **That work survives the change of vantage.** Measured on open
ground in f2760 only — outside the corridor, off the concrete, past the `f` ramp, so
the ramp cannot masquerade as a tier:

```
dcam3 (m)      n     sward    tier A   tier B   tier C
  30-  80    1397    0.705     0.705    0.000    0.000
  80- 130    3768    0.707     0.707    0.000    0.000
 130- 176     793    0.650     0.650    0.000    0.000
 176- 200     329    0.661     0.547    0.114    0.000
 200- 226     289    0.652     0.131    0.520    0.000     <- A hands to B
 226- 280     309    0.606     0.000    0.606    0.000
 496- 520      35    0.562     0.000    0.444    0.119
 520- 546      41    0.605     0.000    0.128    0.477     <- B hands to C
 546- 700     207    0.572     0.000    0.000    0.572
 900-1076     159    0.586     0.000    0.000    0.586
1076-1200      67    0.000     0.000    0.000    0.000     <- THE LAYER ENDS
```

```
A -> B at 200 m     inside 0.659   outside 0.644    step  -2.3 %
B -> C at 520 m     inside 0.535   outside 0.599    step +11.9 %
```

Both inside the ±10 % scatter the layer's own 38 m and 9 m patchiness terms produce.
**No rings.**

**But tier C has no outward fade.** The crossfade is written
`if T is not SWARD_TIERS[-1]: dens *= smoothstep(hi, d1 - 24, dcam3)` — correct for
handing one tier to the next, and the last tier has nobody to hand to, so the `band`
gate `dcam3 < d1 + 26` cuts it dead. **Cover goes 0.586 to 0.000 across zero metres at
1076 m.** It is the same hard edge R2-1661 removed at 200 m and 520 m, at the one
radius the crossfade could not reach.

**NOT CHANGED IN THIS PASS, DELIBERATELY.** At f2760 it is 0.5 % of the ground in
frame and it lands at 4K y = 340..380 — sixty pixels below the horizon, inside the
treeline band, where trees own the read. Folding a second change into this build would
confound the A/B for the change that matters. **It is one line, and it is strictly a
softening** — fading the last tier removes drifts near its edge and adds none, so it
cannot cost triangles and cannot put anything anywhere new. **It should be the next
item, on a frame where open ground runs past 1050 m of the camera path unobstructed.**

---

## R2-1825 — the in-flight assembly carries R2-1661 and NOT R2-1821, and that is checked rather than assumed

`render/world/assembly/r2/assemble.py` was building while this work was in progress,
and it imports `build_terrain` **lazily, inside its module loop** — so "did the edit
land inside the running build" is a real question and not a rhetorical one.

**It did not.** `work/r21701/build_assembly11.log` records the terrain module's own
report:

```
verge clumps   2,703,314   (1,386,383 inside the road corridor)
meadow clumps    281,404
sward drifts     264,890   (A 106,486 / B 93,304 / C 65,100)
grass clumps   2,984,718   (1,643,883 hero)
build            1,144.1 s
```

**264,890 is R2-1661's published figure to the unit**, so that build read the file
before the edit and `assembly11.blend` is the R2-1661 world exactly as intended.
**R2-1821 is not in it and the next assembly is the one that picks it up.**

Those counts are also the baseline the arm-B build is measured against: what the fix
restores is the difference in verge, meadow and sward counts, from the module's own
report rather than from a second opinion about it.

### assembly12 carries R2-1821 and NOT the edge fixes — checked the same way

The rebuild agent re-ran the assembly on top of R2-1821 while R2-1829/R2-1824 were
being written. `assemble.py` imports `build_terrain` **lazily**, so the question is
real: it imported at ~23:38:33, the edge fixes landed at 23:43:11. Rather than trust
that arithmetic, the artefact was read:

```
assembly12   verge 3,022,130 · meadow 293,533 · sward A 116,924 / B 93,538 / C 65,100
arm B        verge 3,022,130 · meadow 293,533 · sward A 116,924 / B 93,538 / C 65,100
```

**Identical in every field, and tier C is 65,100 UNCUT** — which is R2-1821's signature,
because R2-1824 takes tier C down (43,839 → 38,055 on the check's window). So
`assembly12.blend` (7.13 GB, `>> STAGE RESULT: ASSEMBLE_OK`, all 7 modules) is the
R2-1821 world exactly.

> **`assembly12` IS NOT FINAL. R2-1829 and R2-1824 need a thirteenth assembly.** Tier C
> at 65,100 is the one number to check it by: the next assembly must come back *lower*
> or it did not pick these up.

---

## R2-1826 — the placement, asserted: the shoulder comes back WHOLE, and the drawn district turns out to have been leaking grass ONTO the concrete

`tools/r2_1821_paved_check.py`, running the module's own `verge_band`, meadow grid and
sward grid. Confirmed independently by a second pass using the 14 m `Raster` the build
itself uses, which agrees to the sample.

```
1  pit-straight SOUTH shoulder, verge band COMPLETE
       27,051 -> 306,326 of 306,326 samples     8.8 % -> 100.0 % complete   (11.3x)
2  garages / paddock take no verge band
       0 samples kept on declared paving, of 226,282 in the paddock box
3  NEGATIVE CONTROL: nothing placed on declared paving
       verge 0, meadow 0 of 139,433, sward 0 / 0 / 0 of 94,907
3b instrument: the OLD mask DID leak onto the concrete
       old meadow 127,172 placed, 369 of them on declared paving -> new 0
```

**Assertion 1 failed on its first run and the assertion was wrong, not the fix.** It
demanded a 40× gain, which silently assumes the old count was ~0. The old count is
27,051 — the district's 26 m feather lets the two *ends* of the pit straight through —
so **the fix could not exceed 11.3× however perfect it was, and a correct fix reported
FAIL.** The property that matters is not a multiple of what survived but whether the
shoulder is now *whole*: **8.8 % → 100.0 %.** Restated as completeness, and the
mis-specification recorded rather than quietly retuned.

### The finding nobody was looking for

**The drawn district was doing both halves of the wrong thing at once.** A `× 0.92`
multiplier does not mean *"no grass on the buildings"*, it means *"8 % of the grass,
everywhere, including on the buildings"*. Measured over the paddock neighbourhood:

```
                     ON DECLARED PAVING     placed in the 1.8 km box
meadow    old                  377                     225,273
          new                    0                     237,379   (+5.4 %)
sward     old                  456                     164,249
          new                    0                     174,995   (+6.5 %)
```

**833 clumps and drifts were standing on `build_architecture`'s concrete** — the exact
class of defect `cut_field` was written to end for the ground *mesh* (defect #50, two
owners on one square metre, "a flicker with nowhere to hide" in a cut-free film), left
standing in the *plants* because they read a different mask.

**So this is not a trade.** The old mask gave less grass where grass belongs *and* more
grass where it does not. The contract's footprint gives 100 % of the shoulder and
**zero** on the concrete, and the global cost is +5–6 % of two tiers that between them
are a fraction of the layer.

> **A SINGLE MULTIPLIER FAILING IN BOTH DIRECTIONS AT ONCE**, and this is the thing to
> keep. `× 0.90` reads as *"no grass on the buildings"* and is not that statement at
> all — it is *"ten per cent of the grass, everywhere, including on the buildings."* A
> soft multiplier standing in for a hard fact is **simultaneously too strong where the
> fact is false and too weak where it is true**, and the two failures are invisible to
> each other: the sterilised field and the clumps on the concrete would never show up
> in the same metric, the same frame, or the same bug report.
>
> **Nobody asked for the second half.** The brief was to check whether vegetation
> stopped at a footprint or five metres out. It found the mask *also* leaking the other
> way, and only because the negative control was written to count what landed ON the
> concrete rather than what came back off it. **A count of what a fix restores cannot
> see what it was already breaking in the opposite direction.**

The north shoulder gains 32,088 of 325,667 samples (9.9 %) — the strips at the ends of
the paddock rectangles and the gaps between them, **none of which is on declared
paving**, which assertion 3 checks rather than assumes.

---

## Reproducing it

```bash
# the client's frame, measured, with both run-time controls
.venv/bin/python tools/r2_1821_ground_detail.py \
    watch/r2943_4k/r2943_4k_002760.png --selftest --map heat.png

# the placement assertions, including the negative control on the concrete
blender -b --factory-startup -noaudio -P tools/r2_1821_paved_check.py

# arm A = R2-1661's verified geometry + CAM_b6_2760;  arm B = a build with R2-1821
bash tools/r2_1821_ab.sh            # rebake | build | render

# the crops and the numbers, at 1:1, banded by distance from the pit wall
.venv/bin/python tools/r2_1821_crops.py \
    render/r2_1821/A_b6_2760.png render/r2_1821/B_b6_2760.png \
    --out render/r2_1821/crops --label "R2-1661|R2-1821"
```

**Arm A is the existing `ground_after_4cam.blend` with a camera added, not a rebuild.**
`b6_2760` was already in `_VIEWS_WORLD` — R2-1129 lifted all four beat-6 poses out of
the R2943 path when it made the stills — it had simply never been baked into a blend.
So the comparison is at the client's own camera, lens and exposure, and arm A is
literally the geometry that was signed off at f2811.

## R2-1827 — the blast radius, so the regression question is answered by arithmetic before it is answered by a render

Both masks are **identically zero** outside their own rectangles, so the set of ground
where anything can possibly change is `built XOR paved`. Sampled over the module's own
876 ha placement rectangle:

```
ground where `built` and `paved` differ at all      1.914 %   =  16.8 ha
  ... of which GAINS cover   (built > paved)                     16.8 ha
  ... of which LOSES cover   (paved > built)                       0.0 ha
```

**Nothing anywhere loses ground cover.** The mask only ever shrinks. The one place the
*multiplier* changes without the mask changing is on the declared paving itself, where
`0.90`/`0.92` became `1.00` — and that direction removes the 833 clumps that were
standing on architecture's concrete (R2-1826).

Evaluated at the module's own seven station views — the ones beats 1–5 are judged on:

```
t5_verge  esses_rim  t10_rim  t8_gravel  t4_apex  doppler_v      all IDENTICAL
pit_verge                                          built 1.000 -> paved 0.000
```

**Six of seven cannot change, by construction rather than by measurement.** The
seventh is `pit_verge` — **the view an earlier author added specifically to diagnose
this mask** (`before/pit_verge_nograss.png`, "the frame came back as bare olive
ground"). It is the only station view that flips, and it flips the way the comment
beside it says it should have flipped the first time.

`t5_verge` still renders in the A/B as the empirical check on that arithmetic.

## Cost

Everything up to the render is **CPU-only and free**: the frame measurement, the
frustum analysis (which runs `build_terrain`'s own `Circuit`, `Ground`, `CameraPath`
and `habitat` rather than a reimplementation of them), both placement checks, and the
arm-A camera rebake.

The render was **6 frames on the 5090** — 2 × 4K@512 at `b6_2760`, 2 × 4K@512 at
`b6_2811`, 2 × 1080p@256 at `t5_verge` — plus two 1.1 GB scene uploads and one cold
GPU start. Estimated **$0.80–1.10** against R2-1661's comparable **$1.06**.

**Actual: $0.1017** for the R2-1821 pass, **$0.374 cumulative** across both passes
(R2-1821 + R2-1829/R2-1824, 14 rendered frames, four 1.1 GB uploads, three cold starts). Frames were grouped by ARM so the worker swapped its resident
scene twice instead of six times, and arm A was submitted *while arm B was still
building*, so the 3–6 minute cold start and the first upload cost no wall clock at all.
4K@512 came back in 129 s a frame. The GPU stopped itself on the 5-minute idle timer;
budget stands at **$119.23 of $150**, vast.ai credit $[redacted].

**No broker was restarted, no job cancelled that this pass did not submit, and no
`pkill`.** The build was deliberately held until `render/world/assembly/r2/assemble.py`
— another workstream's, and the rebuild carrying R2-1661 into the film — had finished,
rather than competing with it for an 11 GB box.

## R2-1828 — THE RENDER, at f2760, 4K, matched camera and exposure: the client's strip goes +267 %

`render/r2_1821/{A,B}_b6_2760.png`, 3840×2160 @ 512, AgX / None / −3.628.

**Arm A is provably R2-1661.** Its `b6_2811` came back `mean 0.3737 sd 0.1098 range
0.106–0.776 171 levels` — **identical in every field to R2-1661's own published
`after_b6_2811`** — and its `t5_verge` likewise (`0.4647 / 0.1748 / 185 levels`). The
camera rebake changed the geometry by nothing.

```
region                          R2-1661   R2-1821    delta     aniso A -> B
grass, first 5 m off the road      1.40      5.12   +266.6 %    1.12 -> 0.99
pit buildings box (paddock ground) 1.82      4.91   +169.3 %    1.11 -> 0.98
grass beside the pit building      3.71      3.68     -0.7 %
LEFT infield                       1.52      1.47     -3.6 %
verge beside the track             5.46      5.35     -1.9 %
treeline / scrub band              4.29      4.31     +0.5 %
```

**The strip the client named goes from 1.40 — against an empty-surface control of
0.63 — to 5.12, which is within 5 % of the verge band's own 5.35.** The step between
the verge and the ground beside it is gone. Anisotropy falls 1.12 → 0.99: the new
detail is isotropic, i.e. geometry, not a residual smear.

**Everything outside the district moves by ≤ 3.6 %**, which is the Monte Carlo
difference between two independent 512-sample renders. The blast-radius arithmetic
(R2-1827) predicted exactly that, and the render confirms it.

1:1 crops, banded by distance from the pit wall — `render/r2_1821/crops/`:

```
01_against_the_wall      1.31 -> 4.56   +249 %
04_along_the_wall        1.57 -> 4.72   +200 %
06_the_verge_and_beyond  1.98 -> 2.89    +46 %
02_mid_field             3.05 -> 3.47    +14 %
03_outer_field           3.92 -> 3.78     -4 %
05_left_infield          1.56 -> 1.53     -2 %
```

**By eye at 1:1** the before crop is bare brown ground carrying a dozen isolated
sprigs; the after is tussock sward with individual crowns, seed heads and shadow.

### And b6_2811 — the frame R2-1661 WAS verified on — gets better too

```
texture     5.610 ->  6.120   +9.1 %
bare_frac   0.151 ->  0.082   -46.0 %
edge_p99  114.43  -> 110.99   -3.0 %
patch_cv   39.99  ->  40.15   +0.4 %     >> R2_1661_GROUND_BETTER
```

**The bare-ground fraction on the frame that signed R2-1661 off nearly halves.** The
district was costing that frame too; nobody had a metric pointed at it because f2811's
own numbers had already been declared good.

---

## R2-1829 — the residual step, found by looking: it is the VERGE BAND'S OUTER LIMIT, and it is a third the size of the one removed

The after frame carries a straight diagonal edge where the new cover stops. **It was
found by looking at the crop, not by any metric in this pass**, and then identified by
profiling across it on the rendered frame:

```
rendered fine-detail sd, 41 samples across the transition
A   2.6 2.4 2.2 2.1 1.6 1.3 1.2 1.0 1.0 1.0 1.1 1.3 1.0 1.0 1.8 1.2 1.4 1.6 2.0 1.9 2.0 2.2 3.0 2.2
B   4.7 4.4 4.6 4.5 4.1 4.8 5.5 5.6 5.4 5.2 5.1 5.1 5.5 6.3 4.9 4.5 2.6 2.8 3.2 3.3 3.5 3.7 3.1 3.0
                                                             ^ the step
```

At the step, `f = 44.4 → 45.1 m` and the drawn district reads **1.000 on both sides**
— so it is **not** the mask leaking through the tiers left on `built`. It is
`verge_band`'s `out_extra = 42.0`: the hero and far clumps stop dead at
`platform_edge + 42 m`, and beyond it the sward drifts alone carry the ground.

**It is a pre-existing edge that the fix made visible.** Before, both sides of it were
bare (1.0 vs 1.4) so there was nothing to see; now the near side is a real verge.

**And it is three times softer than the defect it replaces:**

```
the defect removed   verge 5.46 -> ground 1.40     the far side is  26 % of the near
what is there now    verge 4.5  -> sward  2.6      the far side is  58 % of the near
```

The far side is also **real cover, not absence** — 2.6–3.7 against the metric's own
empty-ground control of 0.63, and the drifts are individually visible in the crop.
**A managed verge giving way to rough pasture is what a circuit looks like**; the
defect is only that `out_extra` is a step where it should be a fade, which is the same
one-line shape as the tier-C cut in R2-1824. **Both belong to the next pass, together,
on a frame chosen for them.**

---

## R2-1830 — THE CAVEAT THAT NEEDS A DECISION: this change REDRAWS every grass clump in the film

`build_grass` draws species and size with `rng.random(n)` and `rng.uniform(..., n)`
where **`n` is the number of clumps that survived placement.** R2-1821 changes that
number, so from that call onward the shared random stream is displaced and every
later draw — grass kind, clump size, then weeds, stones and grit — lands differently.

**This is not a defect and it is not avoidable by being careful: any change that adds
a clump anywhere moves `n`.** R2-1661 escaped it only because it added the sward layer
*after* `build_grass` and left the counts alone.

**What it looks like, measured and then looked at.** `t5_verge` — beats 1–5's ground,
where `built` and `paved` are both identically zero so the mask *cannot* have acted:

```
texture   11.639 ->  9.657   -17.0 %      >> R2_1661_GROUND_NOT_BETTER
patch_cv  55.466 -> 56.484    +1.8 %
patch_p2p 84.90  -> 82.68     -2.6 %  (better)
edge_p99 152.40  -> 150.35    -1.3 %  (better)
texture_p95 19.88 -> 22.46   +13.0 %  (higher, while the mean fell)
```

**A 17 % move on ground the arithmetic says cannot change — so the metric had to be
wrong about what it was measuring, and it was.** At 1:1 the two frames are the same
verge, the same kerb, the same runoff, the same treeline, and **one different clump of
grass 0.6 m from a knee-height lens**, filling a large part of the frame. Mean texture
fell and p95 texture rose because a denser blade mass was replaced by a sparser one
with more seed heads. **It is a resample, not a regression** — but it *is* visible if
anyone A/Bs a beat-5 frame against a signed-off one.

> **This is the one thing in this pass that is a judgement rather than a measurement,
> and it is escalated rather than decided.** Beats 1–5 have been iterated on and
> approved. R2-1821 does not make them worse; it makes them *different in the
> foreground grass*. If that is not acceptable, the fix needs `build_grass` to draw
> kind and size from a generator whose consumption does not depend on the surviving
> count — which is a change to code this pass did not otherwise touch, and would want
> its own A/B.

---

## R2-1831 — the verge band's rim, crossfaded: the step goes −35.4 % → −1.1 % and nothing dips

`verge_band` now returns `tdraw`, the sample's own fraction of the way to its own outer
edge, and `build_grass` fades on it:

```python
dens *= smoothstep(1.0, 1.0 - VERGE_TAIL_T, B["tdraw"])      # VERGE_TAIL_T = 0.28
```

**It is `tdraw` and not `f` on purpose.** `outer` is capped to 0.75 R on the inside of a
bend, so the band's real rim is at f = 42 m on a straight and much less through T4. A
taper written against `f` would fade the wrong ground at every hairpin and leave the
step standing there. `tdraw` is the sample's position *within its own band*, so it is
exact wherever the cap bites — the same class of reasoning as `dist3` over `dist`.

`VERGE_TAIL_T = 0.28` is **sized, not chosen**: 0.28 of the pit straight's 50 m band is
f = 28..42 m, and the sward drifts are at full weight from f = 34, so the handoff
completes into a layer that is already carrying the ground.

```
f (m)        2     6    10    14    18    22    26    30    34    38    42    46    50
verge old 1.00  0.95  0.91  0.89  0.86  0.84  0.81  0.79  0.78  0.76  0.36  0.00  0.00
verge new 1.00  0.95  0.91  0.89  0.86  0.84  0.80  0.65  0.38  0.12  0.01  0.00  0.00
sward     0.00  0.00  0.00  0.02  0.13  0.29  0.47  0.62  0.67  0.67  0.67  0.67  0.67
TOTAL old 1.00  0.95  0.91  0.90  0.98  1.13  1.28  1.40  1.45  1.44  1.03  0.67  0.67
TOTAL new 1.00  0.95  0.91  0.90  0.98  1.13  1.27  1.26  1.05  0.80  0.68  0.67  0.67
```

**The old profile does not fall off a cliff — it BULGES to 1.45 and then crashes to
0.67.** The band's outer half was laying a second layer on top of a sward that was
already at full weight, and the "edge" was the far side of that bulge. The taper
removes the bulge; it does not open a hole.

```
step ACROSS the rim (f = 42 -> 50)      -35.4 %  ->  -1.1 %
minimum cover across f 20-46 m                       0.676
what the ground BEYOND the rim carries               0.662     never dipped below it
the verge itself, tdraw < 0.72          288,141  ->  288,141   identical
```

## R2-1832 — the sward layer's outer radius, dissolved instead of cut

```python
else:                                     # the LAST tier, which had no successor
    dens *= smoothstep(hi, T["d1"] - SWARD_TAIL_M, h["dcam3"])    # 190 m
```

The crossfade at the joins can be short because the next tier fills in behind it. This
one **fades into nothing**, so it is uncompensated and deliberately 190 m rather than
the 24 m used at the joins.

```
dcam3         700-800  800-860  860-920  920-980  980-1030  1030-1076  1076-1150
cover           0.686    0.686    0.643    0.436     0.182      0.028      0.000
```

**Invariants, and these are the point of the exercise:**

```
tier A            116,535 -> 116,535     identical to the unit
tier B             90,040 ->  90,040     identical to the unit
tier C             43,839 ->  38,055     86.8 %, and the fade can only multiply DOWN
A->B join at 200 m               +0.0 %  still sums to one
B->C join at 520 m               -0.2 %  still sums to one
on declared paving          A 0, B 0, C 0
```

**`>> STAGE RESULT: R2_1829_EDGES_OK (0 failures)`** — `tools/r2_1829_edges.py`.

### R2-1834 — the verge taper was WRONG TWICE, and both were holes, and both were caught by a number that should have been zero

The fix as first written faded on `tdraw` everywhere. Arm C's build reported
**in-corridor verge clumps 1,386,383 → 1,370,543, −1.1 %** — a count the taper has no
business touching at all. Chasing a 1.1 % that should have been 0.0 % found two
separate holes, neither of them on the pit straight where every assertion was looking.

**First: the fold cap.** `outer` is capped to 0.75 R on the inside of a bend, and at T4
that cap lands *inside the road corridor*. Measured over the whole lap: 26.6 % of the
band is in the taper zone, 3.8 % of those are in-corridor at a **median f of −14.3 m**,
clustered at s 919–1225 and s 2603–2756 — T4 and its neighbours. The sward's gate is
`f > 12`, so there is nothing out there to receive the handoff. **Fading a band that
was truncated by a numerical guard hands to nothing and opens a bare strip on the
inside of the hairpin** — the exact defect this workstream exists to remove.

**Second, and it was not anticipated: reprojection.** With the cap excluded, **23,354
of 2,130,639** in-corridor samples were *still* being tapered, median f −11.0 m. These
are samples drawn near their own rim on one branch that `C.project` lands inside
*another* branch's corridor — the case the file already warns about for gravel ("a
clump drawn 50 m off the esses can be 20 m off the doppler straight"), reaching a new
victim. The rule that covers both:

> **A crossfade is only legitimate where there is a layer on the other side to receive
> it.** The taper now applies only outboard of the rim (`inside` is exactly `f <= 0`)
> and only where the band reached its designed extent.

```
1c NOTHING inside the road corridor is tapered, WHOLE LAP
   first version    (no guard)   ~50,849 samples, f median -14.3 m     FAIL
   after the cap guard            23,354 samples, f median -11.0 m     FAIL
   after the reprojection guard        0 of 2,130,639                  OK
```

**The assertion that caught the second was written for the first.** It was added only
because the cap bug forced the question "what else is inside the corridor?", and it
then found a mechanism that had nothing to do with hairpins. **A one-straight sample
cannot answer a question about a lap with hairpins in it**, and the whole tool had been
looking at the pit straight because that is where the defect was.

### The instrument was wrong first, again, and in a new way

Assertion 2b reported **FAIL on a working fix.** It profiled the transition using the
*band's own samples* — and the band stops at its rim by construction, so there are no
samples beyond f = 42 at all. The "far field" it compared against was an empty slice
that averaged to 0.0, and the "step" it computed was between two bins **both inside the
taper**. It also printed an acceptance *fraction* (flat at ~0.37 across the whole band,
because the `t**1.8` bias is in the sampling, not the acceptance) while calling it
density.

> **An instrument that cannot see the far side of an edge cannot measure that edge.**

That is the second mis-specified assertion in this workstream — R2-1826's was a ratio
threshold that assumed the old count was zero. Both were caught the same way: **the
assertion disagreed with the profile printed beside it, and the profile was believed.**
Printing the evidence next to the verdict is what made both survivable; a bare
PASS/FAIL would have sent a working fix back twice.

## R2-1833 — no frame in this film can show R2-1824, and that is a finding

Before rendering the fade, ten delivered views were measured for how much of their
frame lands inside it:

```
esses 0.84 %   b6_2811 0.59 %   ridge 0.43 %   wide 0.17 %   plunge 0.17 %
b6_2760 0.15 %   repeat_n 0.01 %   repeat_s 0.00 %   b6_2937 0.00 %   b6_2978 0.00 %
```

**`dcam3` is distance to the nearest camera-path station, and the path wraps the whole
3675 m lap** — so its 1050 m radius is the far farmland *outside* the circuit, behind
the treeline, in every shot the film contains. **The fix is correct, cheap and
invisible.**

Rather than skip the check or dress a film frame up as evidence, `sward_rim` was sited
**on the band itself** — the densest 120 m cell of open, unwooded, near-level ground
inside it, at world (−1260, 1020) — and shot from 1418 m out, beyond the band's own
outer edge so the camera does not drag the radius with it. It is labelled a diagnostic
in the source and it is not a film frame. Adding a view cannot perturb placement:
`CameraPath` is built from the circuit and the beat keys, never from `VIEWS`.

## R2-1835 — THE RENDER: the 42 m step goes −42 % → −8 %, and nothing else moves

`render/r2_1829/{B,C}_b6_2760.png`, 4K @ 512, matched camera and exposure. Arm B is
R2-1821 as measured in R2-1828; arm C is the same build with both fades.

**The rendered profile across the rim** — fine-detail sd, 41 samples along the same
traverse R2-1829 was found on:

```
B   ... 5.1 5.1 5.5 6.3 4.9 4.9 4.5 | 2.6 2.8 2.8 3.2 3.2 3.3 3.5 ...
C   ... 4.4 4.9 4.3 4.6 4.4 4.4 3.7 | 3.4 3.0 3.0 3.9 3.9 3.9 3.0 ...
                                    ^ the rim
```

```
the single-tile step across the rim     -42.2 %   ->   -8.1 %
largest single-tile drop anywhere       -42.2 %   ->  -19.0 %   (and that one is noise
                                                                 at the far end)
```

**The plateau-then-cliff is now a decline.** And the approach is what changed: arm B
holds 4.5–6.3 right up to the rim, arm C glides 4.9 → 4.4 → 3.7 → 3.4 into it.

**No region got worse — every one is up or flat:**

```
grass beside the pit building   3.68 -> 3.84   +4.4 %
grass, first 5 m off the road   5.12 -> 5.30   +3.6 %
LEFT infield                    1.47 -> 1.50   +1.9 %
verge beside the track          5.35 -> 5.40   +1.0 %
pit buildings box               4.91 -> 4.92   +0.2 %
treeline / scrub band           4.31 -> 4.27   -1.0 %
```

**340,645 verge clumps were removed and the measured detail went UP everywhere.** That
is the bulge argument confirmed on pixels: what the taper deletes is a second layer
laid on ground the sward was already covering.

### The placement counts, and the invariant that proves the corridor bug is gone

```
                       arm B (R2-1821)   arm C (+1829/1824)
verge clumps               3,022,130         2,681,485    -11.3 %
  ... IN CORRIDOR          1,386,383         1,386,383    IDENTICAL  <- the bug, closed
meadow clumps                293,533           293,533    IDENTICAL
sward A                      116,924           116,924    IDENTICAL
sward B                       93,538            93,538    IDENTICAL
sward C                       65,100            56,063    -13.9 %
plants_on_runoff_or_gravel                           0
```

The buggy first build read **1,370,543** in-corridor. **1,386,383 exactly** is the proof
that the taper now stops at the rim, taken off the artefact rather than off the guard.

### b6_2811 and t5_verge

```
b6_2811    patch_cv 41.60 -> 40.85   bare_frac 0.0806 -> 0.0775   edge_p99 106.9 -> 106.6
t5_verge   patch_cv 56.48 -> 57.12   bare_frac 0.1846 -> 0.2052   texture 9.66 -> 9.27
```

`b6_2811` is flat-to-better on every axis. **`t5_verge`'s bare fraction is up 11.2 %,
and it is not the taper.** The band the taper touches was located in that frame's own
screen space by ray-marching its camera: **f = 24–46 m occupies 0.13 % of the frame —
a sixteen-row sliver at the far left, rows 544–560.** A change confined to 0.13 % of a
frame cannot move a whole-frame metric by 11 %. It is R2-1830's redraw again, and at
1:1 the verge is the same density with a different foreground clump.

> **The same metric, on the same frame, moved by 17 % for one reason last pass and 11 %
> for the same reason this pass — and both times the honest answer came from asking
> WHERE the change could physically be, not from arguing about the number.**

## R2-1836 — R2-1824 rendered on the only view that can see it: 0.3 %

`render/r2_1829/{B,C}_sward_rim.png` — the diagnostic sited in R2-1833.

```
whole-frame fine-detail sd     0.656 -> 0.654     -0.3 %
mean |dL| between the arms                       0.00041
the one row band that moves    1.33  -> 1.24      -6.7 %   (rows 512-640)
```

**Four ten-thousandths of a luminance unit, on a frame built specifically to show this
fix.** Between a hard cut and a 190 m dissolve there is nothing to see — the frame is
dominated by haze and treeline at that range, which is *why* the radius was invisible
in all ten delivered views and not merely absent from them.

**Keep it anyway.** It is strictly a softening, it costs 9,037 drifts and no triangles
of anyone else's, and the edge it removes is real and would surface the moment anything
changed — a longer lens, thinner atmosphere, or a camera path that ventures further out
than this one does. **A latent hard edge is cheaper to remove now than to find later**,
which is the entire argument of this project's defect log.

## What this pass does NOT prove

* **It is terrain-only**, like R2-1661 before it. The film-level confirmation is the
  next `assemble.py`, which will be the first to carry R2-1821 (R2-1825).
* **The tier-C outer cut at 1076 m is measured and left alone** (R2-1824), on purpose,
  so this A/B measures one change.
* **Trees, shrubs, ferns, weeds, grit and the park species mix still read the drawn
  district.** Weeds and grit are the two that also contribute ground texture, and if
  the rendered ground still reads thin against the wall they are the next candidates —
  as a separate, measured step, not folded into this one.
* **The RNG stream displacement (R2-1830) is ACCEPTED** — the coordinator's call, on
  the client's *"fill the WHOLE map with trees and detail no blank green spots period"*:
  a different blade of grass is not a cost against that. It moved `t5_verge`'s
  whole-frame metrics twice in this workstream and both times the cause was one
  foreground clump, not the ground.
* **R2-1824 is unobservable** (R2-1836) and kept on the argument that a latent hard edge
  is cheaper to remove now than to find later — not on any rendered evidence, because
  there is none and there cannot be.
* `BUILT_STANDOFF_M = 3.0` is argued from the drift's half-extent, not measured against
  a render of the pavement edge. If grass reads as growing onto concrete anywhere, that
  number is the dial, and it is the only one this change adds.
