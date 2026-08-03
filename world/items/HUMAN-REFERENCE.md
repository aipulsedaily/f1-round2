# The human reference — read this before building any figure item

---

## !!! THIS FILE WAS TRUNCATED ON 2026-08-03 AND IS INCOMPLETE !!!

**I deleted roughly 1,120 lines of this file by accident and only part of it
could be restored.** Recording it here rather than quietly leaving a shorter
file, because a reference with a silent hole in it is worse than one that says
where the hole is.

**How.** A Python edit computed `old = s[s.index("### 00000.7 WHAT IS STILL NOT
GOOD ENOUGH"):]` — from that heading **to the end of the file** — and replaced
it with a rewritten section 00000.7. Everything after that heading went with
it, which was every previous pass. The file went from 1,655 lines to 538 and I
did not notice until a line count in an unrelated check came back wrong. There
is no git in this repository, no editor backup, and the session transcript does
not carry the file body, so nothing could be recovered from disk.

**What was restored, verbatim, from what I had already read this session:**

* **§0000** — the fourth pass (the crowd gated, the gate could not see it).
* **§00** — the second pass (garments stopped wearing the body, the helmet
  stopped being an egg).
* **§0** — the first pass (six defects found by looking, and the big one).

**WHAT IS GONE AND COULD NOT BE RESTORED.** I never read these lines this
session, so I do not have the text. Their headings, from the file's own index,
so that the next agent knows what existed and can rebuild it from the code and
the render record:

    ## 000. UPDATE 2026-08-02 (third pass) — THE CLOTH HANGS, AND THE CROWD HAS A SPINE
    ### 000.0 TWO PREMISES THAT TURNED OUT TO BE FALSE
    ### 000.1 WHAT ACTUALLY MADE THE OVERALLS READ AS PAINT — a control pair
    ### 000.2 THE FOLD LANGUAGE, REBUILT — sparse and oriented, not a field
    ### 000.3 THE LADDER, AND THE PICTURES
    ### 000.4 TWO INSTRUMENTS THAT BROKE, AND THE PATTERN
    ### 000.5 THE CROWD — `world/items/spectator_crowd.py`, and it is NOT
              `spectator_seated.py`
    ### 000.6 A LIVE BUG THE CROWD FOUND — `_skirt` had never run
    ### 000.7 WHAT IS NOT DONE, AND WHAT I WOULD DO NEXT

    ## 1.  Why this item is the reference and a marshal is not
    ## 2.  What the layers are, and where each one lives
    ## 3.  The LOD tiers, against the MEASURED screen presence
    ## 3a. THE AMPLITUDE TRAP — found, with a mechanism
    ###    Measured, in a rendered frame, against a smooth control
    ###    And with the wiring fixed — same scene, same camera, same sun
    ## 3b. THE FREQUENCY TRAP — the node response, measured
    ###    Consequence 1 — frequency, 1.60x coarse
    ###    Consequence 2 — amplitude, ~5x low, and it is the one that mattered
    ###    What to do instead
    ###    The same trap a second time, in the geometry
    ## 4.  The shape to copy
    ## 5.  The seven things `humankit` will not let you get wrong
    ## 6.  Then look at it
    ## 7.  WHERE THIS ACTUALLY STANDS — read before building on it
    ###    What the 767 px render shows, looked at rather than measured

**Sections 1 to 7 were the "how to build a figure" half of this document** —
the layer map, the LOD table, the amplitude and frequency traps with their
measurements, the shape to copy, and the guard rails. **That is the part a new
agent needed most and it is the part that is gone.** Sections 0 and 00 below
still reference §3a and §3b by number; those references now point at nothing.

**What survives the loss, because it is in the code rather than here:**
`humankit --selftest` is 25 checks with controls and its messages state the
numbers; `relief_budget()` prints every relief stage's wavelength, amplitude and
slope; `slope_for_modulation()` and `amp_mm_for_modulation()` carry the
amplitude trap's arithmetic with docstrings; `NODE_PP` carries the measured node
response that §3b was about; `LOD` and `LOD.for_px` carry the tier table.
**Rebuild §1-§7 by reading those and re-deriving, not by trusting memory.**

---

---

## 00000. UPDATE 2026-08-03 (fifth pass) — THE BLUR WAS NOT DEPTH OF FIELD, AND THE CROWD'S GAZE HAD A COMB IN IT

Sections 0000, 000, 00 and 0 below are the four previous passes. **Two things
they state as fact are wrong, and both were wrong in the same way: a cause was
inferred from a symptom and written down without being measured.** Read §00000.0
before you plan anything.

### 00000.0 THE ONE-LINE STATE

`spectator_crowd` now carries a **camera pre-flight** that projects the plan and
refuses to build a camera that cannot show what it is for — and it agrees with
Blender's own `world_to_camera_view` to **0.094 px worst case over seven
cameras**. It has **six repaired framings**, the primary one resolving **491
unoccluded faces at ≥ 40 px** where its predecessor resolved **zero**. Two
defects are fixed with the artefact measured either side: **the mitten hands**
(3 digit-length shells → 5, at +3.1 % of a figure rather than +166 %) and **a
comb through the realised gaze field** that nobody had found and no statistic in
this repository could see. The scene is **rebuilt** — 894 sources, 577 distinct
sources AND 577 distinct SHAPES over 3,803 instances, top share 0.9 % — and
**re-exposed at the film's own −3.628 EV instead of the refuted −3.048 every
item frame before it was judged at.** `spectator_crowd --selftest` **14 checks,
0 failed**; `humankit --selftest` **25, 0**; `human_sweep` **2,360 cases, 0
crashed, 0 zero-area triangles**.

**AND IT HAS BEEN LOOKED AT.** `render/items/spectator_crowd/p5/
CAM_CROWD_ALONG.png` and `CAM_ATTN_ONAXIS.png` (3840x2160, 1536 samples, dof
off, at the corrected −3.628 EV) and the four `render/faceab/face_*.png` are on
disk. **The camera works and defect 6 is closed in a picture; defect 1 is now
diagnosed, and it is neither of the two things sec 0000.5 named.** See
sec 00000.8.

### 00000.1 THE TWO WRONG CAUSES

**1. "`macro_rig`'s depth of field turns every figure into a blur" (§0000.5) is
FALSE. There is no depth of field anywhere in this item.** `itemkit.add_camera`
touches `cam.data.dof` only when it is passed an `fstop`; `_cam` never passed
one. Read back out of the delivered blend with
`bpy.data.libraries.load(link=True)` — which loads camera datablocks without
touching 34 M triangles, and is the cheap way to interrogate a 600 MB scene:

    Camera                      lens=50 use_dof=False fstop=2.8 focus=10.000
    SPECX_CAM_BLOCK_CROSS       lens=50 use_dof=False fstop=2.8 focus=10.000
    SPECX_CAM_BLOCK_ONAXIS      lens=50 use_dof=False fstop=2.8 focus=10.000
    ... all six identical. `focus_distance 10.0` is the Blender default,
    i.e. never written.

`fstop 2.8` is the datablock's own default and does nothing while `use_dof` is
False. A second, independent reading agrees: local gradient energy down the
middle of `BLOCK_CROSS.png` rises **monotonically** from 0.138 at the far top of
the block to 0.161 at the near bottom. A defocus focused at the aim point peaks
in the MIDDLE and falls away both ways; a scale effect does exactly what is
measured. **Had the aperture been "fixed", the re-shot frame would have come
back identical and been declared a success.**

What those two frames actually are is arithmetic, and it needs no render:

| | as shipped | median head | faces ≥ 40 px |
|---|---|---:|---:|
| `CAM_BLOCK_ONAXIS` | 152 m / 50 mm / −9.0° | **8.0 px** | **0** |
| `CAM_BLOCK_CROSS` | 112 m / 50 mm / −11.0° | **10.1 px** | **0** |

The softness on top of that is 192 samples of sub-pixel crowd going through the
denoiser. It is not the fault. **You cannot judge whether two neighbours are the
same person at 8 px of head, and no aperture setting was going to change that.**

**2. "The face is geometry at essentially zero contrast" (§0000.5 item 1) is
also not supported.** Measured on the head grid, `HEAD_LOBES` alone with the
grain noise excluded (an independently written estimator — the slope of the lobe
displacement along the surface, not `_grid_normals`, which mixes in the 0.4 mm
grain and returns a flattering 6.5°):

| | face displacement | slope RMS | **m = 2θ/tan(12.47°)** |
|---|---|---:|---:|
| L1 | −4.5 … +35.9 mm | 14.07° | **2.22** |
| L0 | −5.7 … +40.0 mm | 14.52° | **2.29** |

§0.5's own yardstick puts the fold field's target at 0.90 and the shader's at
0.28. **The face carries 2.2 — more relief than anything else on the figure.**
The attributes are not missing either: on a finished L1 mesh `hk_lip` reaches
0.953, `hk_brow` 0.972, `hk_dark` 0.998.

What IS small, and is the surviving hypothesis, is **how much of the face carries
them.** At L1 the face is 304 vertices on a 44 × 32 grid, **10.7 mm apart = 8.4
px at a 180 px head**, and after the shader's own `maprange` floors:

    hk_lip     6 vertices above 0.5   (1.97 % of the face)   <- the whole mouth
    hk_brow   14                       (4.61 %)
    hk_dark   26                       (8.55 %)

A mouth that is six vertices is two quads, and §00.3 already had to answer "a
colour edge inside a quad is a soft edge" with a geometry welt.

**So defect 1 is NOT diagnosed yet, and the ladder to diagnose it is now built
rather than argued:** `humankit.FACE_RELIEF` and `humankit.FACE_TINT`, gained
into the lobe displacement and into the three face colour masks respectively,
with `human_bench --face-relief / --face-tint`. Four blends are in
`render/faceab/` (`face_base`, `face_norelief`, `face_notint`, `face_neither`),
3 spectators at a 340 px head, and the four frames are the answer. **If neither
frame changes, the answer is the light** — which is where this project's fifth
systemic error lives (§0.6).

### 00000.2 THE CAMERA PRE-FLIGHT — `spectator_crowd.preflight`, and it is arithmetic

Four cameras on this project have now been commissioned that could not show what
they were for: beat 1's, 48.885° off its own subject with zero parts in view;
`CAM_SPECSEAT_MACRO`, whose 767 px render is the artefact the human brief was
written from; and this module's own two. **All four were detectable before a
single triangle was built.**

`preflight(name, loc, aim, lens, plan)` takes the PLAN — the same object
`build_field` bakes into point attributes — projects every head through the
camera the arithmetic says will exist, and returns: figures in frame, figures
unoccluded, **figures with an unoccluded face at ≥ 40 px**, median/p10/p90 head
pixels, frame fill on a 24 × 14 grid, near/far depth, and the axis elevation. It
is pure numpy. **`python3 world/items/spectator_crowd.py --preflight` is ~25 s
and there is now no excuse for spending a render without it.**

Four selftest checks, each with a control that reproduces a real failure:

* `preflight_rejects_the_cameras_it_was_written_for` — `BLOCK_ONAXIS` and
  `BLOCK_CROSS` rebuilt by the arithmetic that produced them. Both rejected.
* `preflight_catches_a_camera_aimed_off_its_subject` — the same camera swung
  **48.885°**, beat 1's own error. 688 figures → 0.
* `preflight_pixel_size_agrees_with_itemkit` — the projection's own `k` at the
  aim distance must equal `itemkit.px_per_m × 0.23 m` **exactly**, and must
  halve when the lens halves. This is the `attention_spread` trap (a statistic
  measuring a quantity it had invented) closed in advance. It needed
  `head_px_at_aim` as a separate field: `head_px_median` is taken over whatever
  is in frame and therefore moves with the field of view, so comparing two
  lenses on it compares two different populations — the first version failed at
  2.0495 for that reason and the failure was correct.
* `shipped_cameras_clear_their_own_preflight` — the negative control.

**AND THE CONTROL BLOCK HAD TO BE THE RIGHT SHAPE.** The selftest's 22 × 96 grid
is 47 m long by 19 m deep — 2.6:1 — and "along the bank" degenerates on a block
that squat; the front row eclipses everything behind it. A real grandstand is
8.8:1 (TRIBUNE PRINCIPALE, 160 × 27 m). The camera checks now build their own
24 × 300 control block **with the car 665 m away and 13° off the stand's
normal**, because putting the car 60° off makes the whole crowd crane its neck
and quietly turns the control into a different problem.

### 00000.3 THE CAMERAS THAT REPLACE THEM — measured on the real block

`camera_plan(plan, focus)` is **pure arithmetic and is the same list
`--preflight` checks and `add_cameras` builds** — a camera checked in one place
and placed by different arithmetic in another is how `CAM_SHEET` ended up 0.0 m
from its aim. Every distance is a multiple of the block's own half-length and
every lens is derived from the distance it ends up at (`lens_for(...,head_px)`),
so the set survives being pointed at a block that is not this one.

    BLOCK  TRIBUNE PRINCIPALE: 5568 seats, 3803 people,
           159.6 m along bearing 40.34°, 27.5 m deep, z 3.00..10.05
    CAR at frame 1009: 664.4 m away on bearing 143.22°; the seats face 130.00
           (spread 0.2°), so the car is 13.2° off the stand's own normal

    camera                  lens   aim m    px/m   elev inframe  unocc  faces  fill  head px med/p10
    SPECX_CAM_CROWD_ALONG    276   104.3   282.6  +0.00    1295    638    495  0.87  57.2 / 42.5
    SPECX_CAM_ATTN_ONAXIS    276   135.7   217.4  +0.00     334    330    292  0.52  50.5 / 47.5
    SPECX_CAM_ATTN_PROFILE   271   102.1   282.6  +0.00    1450    621    302  0.82  54.0 / 40.8
    SPECX_CAM_ROW             28    14.7   203.2  -4.00     804    772    158  0.47  28.4 / 16.5
    SPECX_CAM_FEET            50     9.0   592.6  -3.00     113    112     99  0.27  86.5 / 61.6
    SPECX_CAM_HANDS           85     3.2  2833.3  +2.00      36     19     17  0.05 135.1 / 68.8

    0 camera(s) rejected.

**A LONG LENS FROM LOW DOWN, ALONG THE BANK.** A 0.23 m head at 40 px needs 174
px/m; a 300 mm lens reaches that at 184 m. So one frame can hold a whole
175 m grandstand AND resolvable faces, which a 50 mm from 200 m cannot. That is
the entire idea, and it is what broadcast does.

Three things about it that are decisions, not accidents:

* **The height is 6.0 m, not track level, and that was measured.** At 2.0 m the
  same camera resolves **313** unoccluded heads and fills 0.33 of the frame
  against **653** and 0.86 — the front rows eclipse the bank. Level ALONG a
  raked bank is what "along the stand" has to mean; looking up at it from the
  track puts sky behind the top rows and chins in front. Axis elevation is
  **+0.00°**.
* **`CAM_ATTN_ONAXIS` is the WEAK half of the attention pair and is kept
  anyway.** The car is only 13° off the stand's normal, so bodies point almost
  into that lens whatever the heads do. Its value is the **27 % who are not
  watching**, who are unmissable in it — and looking straight into a raked bank
  is the one geometry with almost no self-occlusion (334 in frame, **330**
  unoccluded).
* **`CAM_ATTN_PROFILE` picks its own flank.** "90° off the car" leaves the sign
  free and the two sides are not equivalent — one of them looks down the rows at
  the back of every head. Both are projected and the better wins. The
  constraint (90° off, level, a 65 px head at the aim) is fixed either way.

`add_cameras` now **raises** rather than building a camera whose preflight
fails, asserts `use_dof is False` on every camera it creates rather than
assuming it, and **defaults to 4K**. It defaulted to a 1920 draft, which is how
a scene whose saved `resolution_x` is 1920 came to have four 3840×2160 PNGs
beside it: the render harness overrode the resolution and nothing in the module
knew which of the two the frames had been judged at.

### 00000.3a WHAT THE BUILD ACTUALLY PRODUCED, AND THE FOUR THINGS THAT CHECKED IT

`world/items/spectator_crowd_test.blend` (675 MB, staged for the farm as
`render/spx5.blend`) — 894 sources, **11,954,566 library polygons**, 904
objects, 3,803 realised instances, **69,669,463 realised polygons**, seven
cameras, `dof=False` on every one of them, scene at 3840x2160.

**1. THE PREFLIGHT AGREES WITH BLENDER'S OWN PROJECTION.** `work/spx_camcheck.py`
runs `bpy_extras.object_utils.world_to_camera_view` — an implementation shipped
by somebody else — against the same head points through the same camera
objects, on all seven cameras:

    SPECX_CAM_ATTN_ONAXIS    max 0.0059 px   median 0.00157 px   depth 4.9e-5 m
    SPECX_CAM_ATTN_PROFILE   max 0.0265      median 0.00242      depth 2.5e-5
    SPECX_CAM_CROWD_ALONG    max 0.0073      median 0.00151      depth 3.9e-5
    SPECX_CAM_FEET           max 0.0435      median 0.00514      depth 3.6e-5
    SPECX_CAM_HANDS          max 0.0936      median 0.00301      depth 4.8e-5
    SPECX_CAM_ROW            max 0.0518      median 0.00104      depth 4.9e-5
    SPECX_CAM_SHEET          max 0.0025      median 0.00074      depth 2.7e-5
    WORST 0.0936 px over 7 cameras -> preflight agrees with Blender

**The first run of that script printed "PREFLIGHT IS WRONG — do not trust its
numbers", and the script was the broken thing.** It had no depth floor: a head
60 mm in front of a 50 mm lens projects to hundreds of thousands of pixels,
where the 5e-5 m the two arithmetics differ by is 165 px on screen. The medians
were already 0.001–0.007 px and the depths already agreed to 5e-5 m; only the
max was nonsense. Seventeenth time on this project, and it was mine.

**2. VARIETY, ON THE DEPSGRAPH.** `tools/instance_variety.py`:

    family       instances  sources  inst/src  top share    gini   verdict
    SPECX            3,803      577         7       0.9%   0.553   varied
    >> STAGE RESULT: INSTANCE_VARIETY_CLEAN

and `work/spx5_shapes.py`, which hashes the **evaluated, mean-centred vertex
positions** of every source actually instanced, because 894 datablocks that are
894 copies of one geometry would score perfectly on the count:

    distinct SHAPES 577   distinct datablocks 577
    datablock groups that are geometrically IDENTICAL: 0
    >> STAGE RESULT: SHAPES_MATCH_SOURCES

**577 sources and 577 shapes against a bar of 40.**

**3. AND THE RED LINE, MEASURED IN THE FRAME RATHER THAN IN THE BLOCK.** Whole-
block variety is the coarse half. What the user's red line is actually about is
whether two people you can SEE AT ONCE are the same person, so it is counted in
`CAM_CROWD_ALONG`'s own frame, over the 491 figures it resolves:

    201 distinct sources over 491 resolved faces; commonest appears 7 (1.43 %)
    402 distinct sources over the 1,296 in frame; commonest 12 (0.93 %)
    on-screen neighbour pairs within 4 head-widths:      3,849
      ... of which the SAME SOURCE MESH:                    16   (0.42 %)
      closest same-source visible pair:            31 px apart, on a 63 px head

**Sixteen visible pairs of identical twins in one frame, one of them
overlapping.** A source carries its own garment colour in `hk_col`, so two
instances of one source are identical down to the shirt. 0.42 % is small and it
is not zero, and the number to move is `ROLE_CELL["sit"]` (64 per bin, and the
block's 13.7 deg of bearing spread pushes 3,225 seated people into two or three
of the nine bins). Doubling it costs ~20 M library polygons.

**4. POSE REPETITION AT THE SCALE IT WILL BE SEEN** — defect 2, on the 613
figures `CAM_CROWD_ALONG` resolves: **22 distinct archetypes**, commonest
`sit_legs_crossed` at 12.2 %, and of 5,860 on-screen neighbour pairs **8.7 %
share an archetype against the 8.2 % a spatially-random draw from the same
realised distribution would give.** Poses are not clustered. `sit_cheer` — the
rigid-V repeat of sec 0000.5 item 6 — does not reach this frame's top ten.

**5. THE FULL-PARAMETER-SPACE SWEEP, re-run after the humankit changes:**
`human_sweep --jobs 2` — **2,360 cases, 0 CRASHED**, 0 non-finite vertices,
**0 zero-area triangles**, 0 out-of-range indices, 0 pieces left inside-out;
5,188 / 27,923 / 103,589 triangles per figure (min/median/max). The two seated
sole-above-pan and thirteen sole-below cases are the same known pose extremes
sec 0000.2 recorded, unchanged.

### 00000.3b EVERY ITEM TEST FRAME EVER JUDGED IS 0.580 STOPS OVER-EXPOSED

`itemkit.contract_sun` sets `scene.view_settings.exposure =
world_contract.REFERENCE_EXPOSURE_EXTERIOR = **-3.048**`. The film renders at
`film_exposure.FILM_EXPOSURE = **-3.628**`, and `tools/build_verify_scene.py`
says in terms that -3.048 is *"the refuted contract value"* and must never be
used. **The difference is 0.580 stops and it is in the over direction.**

Every frame in `render/items/` — all five `spectator_crowd` frames, the
`human_bench` A/B ladder that sections 0, 00 and 000 were written from, the
`crew_figure` macro that passed 8 of 8 — was judged under it. 0.58 stops is not
a rounding error on a face: it is most of the shading range a brow ridge and a
nasolabial fold have to work in, and defect 1 is *"the face is a featureless
oval"*. **This is not a claim that it is the cause** — the face ladder decides
that — but it is a fifth instance of §0.6's lesson and it had to stop.

`spectator_crowd.add_cameras` now reads `film_exposure.FILM_EXPOSURE` itself
and RAISES if it cannot. `contract_sun` is `itemkit`'s and another agent owns
it, so it is corrected loudly here rather than edited there. **Every other
figure item — `crew_figure`, `human_bench`, `paddock_personnel_figure`,
`driver_figure` — still shoots at -3.048.**

### 00000.3c A BAR THAT WAS WRITTEN BEFORE THE QUANTITY WAS UNDERSTOOD

`add_cameras` refused to build `CAM_ATTN_PROFILE` and killed an eleven-minute
build. It was right to fire and the bar was wrong. That camera stands 90 deg
off the car, so the seated bodies are **edge-on** to it and the
face-toward-lens test (`facing > 0.10`, ~84 deg) sits at its zero by
construction: it counted 175 where the frame holds **621 unoccluded heads**.
The 175 are the heads that have turned out of an edge-on shoulder line far
enough to show the face — which is the signal that frame exists to carry, not a
shortfall.

Fixed by measuring the right quantity rather than by lowering the number:
`preflight` now reports **`n_heads_resolved`** (unoccluded, at size, whichever
way they point) beside `n_faces_resolved`, `min_heads` is a bar of its own, and
the flank choice ranks on heads — ranking a profile camera on faces picks the
flank that is *least* in profile. `CAM_ATTN_PROFILE` carries `min_heads=300,
min_faces=120`: 300 so the shoulder lines are countable, 120 so a 10 %
subgroup still has ~12 members.

### 00000.4 THE COMB — a defect no statistic in this repository could see

**The realised head bearings of TRIBUNE PRINCIPALE occupied 10° out of every
18°, with a hole through the middle of the watching population.** Counted in 5°
bins relative to the block mean, before:

        -15..-10   368        +5..+10       1     <- one person, out of 3,803
        -10.. -5  1089       +10..+15     900
         -5.. +0    91       +15..+20     285
         +0.. +5    13       +20..+25      31

Mechanism, exactly: `plan_block` solved the **body** against the continuous head
turn and quantised the **head** afterwards. What a viewer sees is
`body + baked`, which is `stance + (1−share)·d + quantise(share·d)`. Inside one
bin that sweeps `(1−share) × bin_width` = 9.7°; at the bin edge it JUMPS the
remaining 8.3°. Period 18°, duty 54 %.

Every attention statistic in the file scores this identically — `crowd_watches_
the_car` counts everyone within 20° and returns 73 % either way — because the
comb is a property of the field's *fine structure*, not of its mean or its
spread. It would have been rendered at 57 px of head on the new camera.

**The fix costs nothing: re-solve the body AFTER the bin is known**, so the body
absorbs the quantisation residual and `body + baked` equals the attend bearing
wherever the neck (±72°) and the seat (±45°) can reach it. After:

         -5.. +0   594       +10..+15    272
         +0.. +5   699       +15..+20    105
         +5..+10   456       +20..+25     24

modal bin **29.5 % → 19.9 %**, top three **63.9 % → 49.7 %**, occupied 5° bins
**→ 40**, and **0 of 30 two-degree bins empty across the 2,823-person watching
core**. Attention is unchanged at **72.5 % within 20°, circular sd 43.9°**, and
`what_is_baked_is_what_was_planned` now measures the binning moving the realised
head by **0.0°** instead of up to 11.0°.

`realised_gaze_field_has_no_comb` checks it, and `plan_block(legacy_gaze=True)`
is the control — **the same function re-run**, not a reconstruction. The first
version of that control derived the old stance by subtracting the new residual
back off `body_yaw_deg` and returned **0 empty bins for both arms**, i.e. a
control that could not fail. Sixteenth time on this project. The same mistake
was live in `what_is_baked_is_what_was_planned`, whose "superseded scheme"
control was being fed the already-quantised `head_yaw_deg` and measured 28°
instead of 35.6°; `head_yaw_solved_deg` (the continuous neck angle the composer
wants, given the final body) is now carried separately from `head_yaw_deg` (what
is actually built) so the two can never be confused again.

### 00000.5 DEFECT 6 — the hands, fixed at 3.1 % instead of 166 %

`humankit.hand_finger_separation` counts connected shells on the emitted hand.
Run across the tiers on the same body, which is the A/B §0000.5 asked for:

| tier | digit-length shells | closest two tips |
|---|---:|---:|
| L2 | 2 | 84 mm |
| **L1, as shipped** | **3** | **51 mm** |
| **L1 + `fingers=5`** | **5** | **23 mm** |
| L0 | 9 (5 + nails) | 11 mm |

L1 as shipped is a hand with **three digits on it**, because `LOD_L1.fingers=3`
makes `_finger_groups` return two FUSED PAIRS at 1.9× radius. 85 % of a
grandstand is built at L1. The picture was telling the truth.

§0000.5 prescribes "build the seated library at L0". That works and costs
**79,088 tris a figure against 29,755 — +166 %** — and 0.92 s a figure against
0.32 s. **The hand is one body part.** `LOD.for_px` is right about the figure
and wrong about the hand: a 1.25 m seated body projects 254 px at the manifest
framing, but a hand raised above that body's head is nearer, unoccluded and
90–120 px across in the crop the defect was found in.

New: **`LOD.derive(**overrides)`**. The seated tier is built at L1 with L0
hands. Measured over six figures: **30,675 tris against 29,755 — +920, +3.1 %**
— and 0.34 s against 0.32 s. Same five fingers. `--lod L0` still does the
whole-tier bump if evidence ever demands it; `build_library(hands_l0=False)` is
the control.

### 00000.6 THE 767.2 px CITATION — wrong in three places, and 39 % high

`screen_presence.json` has **no `peak_sharp_px` field at all**, only
`peak_sharp_px_4k`. Regenerated 2026-08-03 03:58, the covered tier reads
**551.8 px sharp / 785.7 peak / 106 frames ≥ 300 px / min depth 7.602 m**.
767.2 was a pre-shutter-fix RAMPED number, superseded by R2-037, and it
**overstates the covered tier's macro resolve by 39.0 %**. Corrected in
`humankit`'s header, in §12c's prose and in the `lod_maps_the_measured_presence`
selftest (which asserted the stale numbers). The other two headline figures were
stale too: GA standing **363.4 → 278.7**, seated crowd **259.6 → 199.1**.

`crew_figure.PEEP_PX` is deliberately **left at 767.2** and documented: every
peep render and the ITEM_ACCEPTED 8/8 gate run were framed at 8.518 m when the
film never gets closer than 11.845 m sharp. That is a HARDER test than the
evidence requires, so the pass stands and does not have to be re-earned;
`crew_figure.PRESENCE_PX = 551.8` is the honest measurement beside it. Both tier
to L0, so no geometry moved. **`paddock_personnel_figure.py` still carries
767.2 / 7.537 in four places and is not owned by this pass — it needs the same
treatment.**

### 00000.8 THE FRAMES — what nine hundred and sixty pixels of head actually show

**THE CAMERA WORKS.** `CAM_CROWD_ALONG.png` is a stand of people, sharp, from
end to end: individual figures resolve at 60-90 px of head, there is no blur,
no banding, no repeated-figure moiré, the occupancy clumps and the aisle bays
read, and the colour speckle is even. Put it beside `BLOCK_CROSS.png` — same
block, same day, 8 px of head against 57 — and the difference is the whole
point of sec 00000.2.

**DEFECT 6 IS CLOSED AND IT READS.** Raised hands in the 1:1 crop have five
separate fingers. The flat paddle-with-a-thumb of `crops/feet_c.png` is gone,
at +3.1 % of a figure.

**DEFECT 1 IS DIAGNOSED, AND BOTH NAMED SUSPECTS WERE WRONG.** The four-corner
ladder, cropped to one head at ~400 px:

| | face in profile |
|---|---|
| `face_base` (relief 1, tint 1) | brow, nose, lip line, chin — a real profile |
| `face_notint` (relief 1, **tint 0**) | **unchanged** — every feature still there |
| `face_norelief` (**relief 0**, tint 1) | **GONE.** A smooth egg with a smudge |
| `face_neither` | egg |

Measured over the whole frame: turning the **tint** off changes **0.05 %** of
pixels; turning the **relief** off changes **0.68 %**. **The face is carried
almost entirely by `HEAD_LOBES`' geometry and the three colour masks contribute
essentially nothing** — which is the opposite of sec 0000.5's "suspect the skin
shader's zone channels", and it also means the relief is NOT at zero contrast.

So why is a crowd face a blank egg? The ladder answers that too, by showing
where the base frame's face DOES read: **in profile, as a silhouette.** Shading
carries almost none of it. A nose is ~20 mm on a 230 mm head — 5.5 px at the
crowd's 63 px head — and in the crowd frame most resolvable faces are frontal
or three-quarter, where there is no silhouette and 5 px of nose has to be
carried by shade alone. **The work is to make the orbital rim, the nasolabial
and the lip line read as SHADE from the front, not to add more of them.** The
levers, in the order I would try them: a geometry welt at the lip line and the
orbital rim (sec 00.3's answer to exactly this class of problem on a livery
panel); raising the three tint masks, which currently do 0.05 % of the work;
and re-checking under the corrected exposure, which no face frame before this
one had.

**AND TWO DEFECTS ARE WORSE THAN THE RECORD SAYS.** At 400 px and again at
63 px, the **hair is a granular crust** — a lumpy porridge-textured shell, not a
mass with an edge — and it is the single worst-looking thing in both frames.
sec 0000.5 item 3 calls it "a moulded shell, smooth and glossy"; it is not
smooth, it is chunky, and the chunk is at the wrong scale. The **caps still
read as hard hats**: a smooth dome, no six-panel seam, no button, and the white
ones are the brightest objects in the frame. Also visible at 400 px and not
previously recorded: **the head grid facets** — flat quad-shaped patches on the
neck and cheek at L0's 72 x 52.

**ATTENTION SURVIVES BEING SEEN.** In `CAM_ATTN_ONAXIS.png` most heads face the
lens and a clear minority are turned away, in profile, or down at a phone; in
`CAM_CROWD_ALONG.png` heads point across a range while the shoulder lines stay
square to the track. It is neither dead nor printed. The arithmetic behind that
is sec 00000.4, and the comb fix is what makes the range continuous rather than
stepped.

**AND THE BROKER WAS NOT BROKEN — I MISREAD IT, WHICH IS THE SAME MISTAKE THIS
SECTION IS ABOUT.** `rq status` showed `done` frozen at 1,344, `running: 1` with
no running detail line, and `idle` climbing, and I called it a stall and put an
agent on it. All three readings were the display, not the farm: a 50-frame
sequence is ONE row in `jobs` so the done counter cannot move while it runs;
`idle` is stamped per FRAME and sawtooths 0 -> 76 s; and the running row had
aged out of `rq status`'s `ORDER BY created DESC LIMIT 15` window precisely
because a long job is an old job. The GPU was busy the entire time and my jobs
were legitimately queued behind it. `broker/db.py recent()` has been fixed to
always include running rows (not live until the next broker restart).
**Eighteenth time, and the instrument was a status line.**

### 00000.7 WHAT IS STILL NOT GOOD ENOUGH

1. **All four crowd frames are in `render/items/spectator_crowd/p5/`** —
   `CAM_CROWD_ALONG`, `CAM_ATTN_ONAXIS`, `CAM_ATTN_PROFILE`, `CAM_ROW`, all
   3840x2160 / 1536 samples / dof off at -3.628 EV. `CAM_ROW.png` is the direct
   A/B against the old `ROW.png` (same framing, 0.580 stops apart) and I did
   not get to it. To re-render anything, copy
   `world/items/spectator_crowd_test.blend` (644 MB) into a permitted scene
   root -- `~/vast-render` will only accept `/home/zany/f1-round2/world`,
   `/home/zany/f1-round2/render`, `/home/zany/opus5-car-render/work` or
   `~/vast-render/scenes`, which is why the staged copy lived at
   `render/spx5.blend`.
2. **Defect 1 is diagnosed and NOT fixed** (sec 00000.8). The next agent has a
   working ladder (`FACE_RELIEF`, `FACE_TINT`, `human_bench --face-relief
   --face-tint`), a measurement that says the tint does 0.05 % of the work, and
   a named direction: make the face read as SHADE from the front. **Defects 3
   (hair) and 4 (caps) are worse than the record said and are the two ugliest
   things in the frame** — I would do the hair before anything else on this
   list. It is a granular crust at every distance and it is on every uncovered
   head.
3. **The GA tier still does not exist**, and the numbers sec 0000.6 quotes for
   it are stale. Measured 2026-08-03: `spectator_standing_ga` — 3,500 instances,
   1.75 m, **peak 448.6 px, peak SHARP 278.7 px, 0 frames >= 300 px, 82 frames
   >= 150 px, min depth 10.756 m**. **That is L1, not L0.** The manifest's own
   15.4 m / 35 mm arithmetic gives 424 px and the measured sharp presence gives
   279 — a whole tier apart, and somebody has to decide which governs before a
   line of it is written. Its host `ga_viewing_bank` — 6 instances, 6.0 m,
   **peak 1538.1, sharp 955.7, 86 frames >= 300 px**, *"the WEAR is the
   object"* — is a HERO with no module, and it must come first because the
   figures stand on it.
4. **16 visible pairs of identical twins** in `CAM_CROWD_ALONG`'s frame
   (sec 00000.3a item 3), one pair 31 px apart on a 63 px head. 0.42 % of
   on-screen neighbour pairs. The lever is `ROLE_CELL["sit"]`.
5. **Defects 2-5 on the UNCOVERED tier: 2 is now answered** (22 archetypes over
   613 resolved figures, no spatial clustering — sec 00000.3a item 4);
   **3, 4 and 5 are not.** They have only ever been re-checked behind helmets
   and gloves.
6. sec 0000.5's defects **3 (hair is a moulded shell), 4 (caps read as hard
   hats) and 5 (flat props: 43 % of the block holds a bright rectangle)** are
   untouched, and so are sec 00.6's five polish items.
7. **`paddock_personnel_figure.py` still carries the wrong 767.2 / 7.537 in
   four places**, and `crew_figure`, `human_bench`, `paddock_personnel_figure`
   and `driver_figure` all still shoot at the refuted **-3.048 EV**.
8. **The gate has not been re-run** on the new blend, and
   `render/items/spectator_crowd/gate.json` plus the five PNGs beside it
   describe a build three source revisions old (840 sources, mitten hands,
   pre-`ROLE_SPAN`, pre-comb-fix, and its two block cameras are the rejected
   ones). Do not quote them.
9. **Only one LOD is still built** for the seated tier, and `LOD.for_px` still
   decides a whole body from one number. `LOD.derive` makes per-part tiering
   possible; the hand is the only part that uses it.

---


---

## 0000. UPDATE 2026-08-02 (fourth pass) — THE CROWD WAS GATED, AND THE GATE COULD NOT SEE IT

*(RESTORED 2026-08-03 from the fifth pass's own reading of it. Verbatim.)*

Sections 000, 00 and 0 below are the three previous passes and are still
correct. This block is the fourth. **Read §0000.0 before you plan anything: the
two headline numbers you were handed both survive, and both were hiding a
defect underneath them that no statistic in this repository could see.**

### 0000.0 THE ONE-LINE STATE

`spectator_crowd` **has now been gated**, and the first run came back
**ITEM_REJECTED** on `witness_frame_valid` with the message *"only 0 subject
pixels (need 12000)"* — three further checks NOT MEASURED off that one
boolean. `render/gate_witness/spectator_seated/witness.png` (run 1) is the
proof and it is worth opening: the control sphere, the six-step wedge and the
plane are all there, correctly lit, and **there is no person in the frame.**

Cause, and it is entirely mine: `build_library` set `hide_render = True` on
every source. The gate picks the **median-triangle object in the collection**,
which for this item is necessarily one of those sources, deletes everything
else, stages its own scene around it — and **never clears `hide_render`.** So
the frame it measured was empty sky, and it said so honestly.

`hide_render` was only ever there to stop 402 people rendering on top of each
other at the origin, because `emit_mesh` recentres. `build_library(yard=...)`
now lays them out on a **contact sheet** — a grid, ordered by (role, bin, k),
well clear of the block — which fixes the gate AND produces the one picture
that answers the variety question by looking rather than by counting.

### 0000.1 BOTH LOAD-BEARING CLAIMS SURVIVE. BOTH WERE HIDING SOMETHING.

**ATTENTION — the number is right and the framing is not.** On the REAL block
(TRIBUNE PRINCIPALE, 3,803 people, frame 1009) the plan measures **72.5 %
within 20°, circular sd 44.2°**, against **20.7 % and 95.7°** at
`attention = 0`. So it reproduces. Three things the number does not say:

* **The car is 665 m away.** Every seat in the block faces 129.90°–130.11° —
  a spread of **0.2°** — and the bearing to the car varies **13.7°** across
  the whole 175 m block. A crowd all facing 130° with a 7° jitter would score
  ~70 % on this statistic without attending to anything. **The discriminator
  is not the watchers, it is the 27 % who are NOT watching** and are turned to
  their own group at 30–70°. Judge the picture on those.
* **The `attention = 0` control has a floor built into the geometry.** It
  measures 20.7 %, not the 11 % of a uniform field, because a non-watcher with
  no group faces *the way their seat does* — and the seat faces the track,
  which is where the car is. That is physically right and it means the contrast
  is 72 vs 21, not 72 vs 11.
* **`attention_spread` reads `yaw_deg`, which is the PLAN's intent, not the
  geometry.** What a viewer sees is `body_yaw_deg` (the instance rotation) plus
  the head turn **baked into whichever library cell the seat picked**. Measured
  on the realised geometry it is 72.3 % — the block-level claim holds — but the
  per-role error did not: the four roles with only 3 bins were off by a mean of
  **26.5° on `steps` and up to 53.9°**. 173 people on their feet with heads
  pointing somewhere the plan never asked for, invisible to every statistic in
  the file because every one of them reads the plan. Fixed (§0000.3) and now
  checked by `what_is_baked_is_what_was_planned`.

**VARIETY — 402 sources, `top_source_share` 0.0025, and 46 copies of one
person in one grandstand.** Every published number was true and every one of
them was measured on the wrong denominator:

| | as shipped | now |
|---|---:|---:|
| sources built | 402 | 894 |
| sources the real block actually instances | 247 | 562 |
| **worst copies of ONE source in the block** | **63** | **35** |
| `stand` — 304 people over | **12 sources** | 50 |
| `aisle` — 74 people over | **4 sources** | 23 |
| `steps` — 51 people over | **4 sources** | 23 |
| `lean_rail` — 48 people over | **4 sources** | 18 |
| sources built and NEVER instanced | **216 of 402** | — |

Two independent causes.

1. **`plan_block` set `head = 0` for anyone on their feet**, so `gaze_bin` was
   always the middle one and `library_index` could reach **one bin per role**
   however large the library was. 216 sources were built, saved into a 196 MB
   blend, and never instanced. The people on their feet are 15 % of a block,
   they are the only figures with a full-length silhouette, they are nearest
   the front — and there were **34 copies of one walking man**. That is the
   user's named red line wearing a high-vis vest.
   It was also wrong on its own terms: `body = yaw_deg` rotated an aisle walker
   bodily at the car, i.e. striding **sideways across the terracing into the
   seats**.
2. **`top_source_share` cannot see it, and neither can the gate.** 85 % of a
   block is seated, so a seated majority buries every other role in the
   denominator: `aisle` at 34 copies of 74 people is 45.9 % **of its own role**
   and 0.0089 of the crowd. **THE RED LINE IS PER ROLE.**
   `no_source_dominates_its_own_role` now measures each role against a uniform
   draw over *that role's own* library — an absolute bar fails a small role for
   being small, which is an instrument reporting its own denominator.

### 0000.2 THE FULL-PARAMETER-SPACE SWEEP — `world/items/human_sweep.py`

§000.6 predicted more bugs of the `_skirt` class in the uncovered tier. **There
are none.** `human_sweep` enumerates rather than samples — every (top × bottom
× sex) pair, every (headwear × shoe × sex × age), every one of the 31 pose
archetypes × sex × age, every prop in either hand at both grip extremes, every
role × LOD, the distribution's own tails reached by drawing 4,000 real bodies
per (sex, age) and taking the extremes, gaze at the ±95° clamp, and 1,200
fully random draws: **2,360 cases, 0 crashes.**

What it found instead is the class of defect that does not raise:

* **2,293 of 2,360 figures carried a median of 33 EXACTLY ZERO-AREA
  TRIANGLES**, all on the head, two independent causes, both a collapsed pole:
  * `build_hair` put the whole of ring 0 at `theta = 0`, so its 33 vertices sat
    on the polar axis — and because `grow` carries an azimuthal `lump` they do
    **not** coincide there. Measured: ring 0 spanned 2.2 mm in xy and **10.8 mm
    in z**. The crown of every uncovered head was a **needle**, ringed by
    55 mm² sliver quads against a typical 307, with `cap_lo` fanning 33
    zero-area triangles over the top.
  * `_peak`'s rim band was a closed strip of `(loop, loop-with-its-halves-
    swapped)` — the same two points in both rows at each join. Four zero-area
    triangles on the peak of **every capped figure**, and 29 % of this tier
    wears a cap.
  A zero-area face has no cross product, hence no normal, and Cycles shades it
  with whatever the interpolation gives. Both fixed; `no_face_has_zero_area`
  now checks it with **both** constructions reproduced verbatim as positive
  controls (they measure 15 and 4). `humankit --selftest` **25 checks, 0
  failed.**
* 2 of 2,360 seated figures put a sole above the seat pan and 10 put one below
  −0.62 m. Pose extremes, not crashes; listed here because nothing else looks.

**Run it before you trust a sample.** `python3 world/items/human_sweep.py
--jobs 6` is ~4 minutes on six cores.

### 0000.3 WHAT ELSE CHANGED IN THE MODULE

* **Two LOD tiers, and it was wrong in the expensive direction.** `LOD.for_px`
  takes the figure's projected HEIGHT: at 14.7 m on a 28 mm lens a **1.25 m
  seated** figure is 254 px → L1, and a **1.75 m standing** one is **356 px →
  L0**. The whole library was L1, so the 15 % on their feet were a tier short —
  3 grouped digits instead of 5 separate, 1 ear instead of 2, no nails, 190
  hair strands instead of 620. It costs nothing at render time: the library is
  instanced, so its size is a memory figure, ~33 M triangles against ~24 M on a
  32 GB card.
* **Each role has its OWN head-yaw span and bin count** (`ROLE_SPAN`,
  `ROLE_BINS`), and `role_bin` takes **degrees** rather than a global bin
  index. There is now one index space instead of two — which is the structural
  answer to the collision `library_index_is_a_bijection` caught last pass.
  Worst-case quantisation is `span / (bins - 1)`: 9° seated, 11° on their feet,
  against 72° before.
* **The body makes up whatever the neck cannot**, capped at 45° for a bolted
  seat and uncapped for someone on their feet. The superseded form gave the
  body a fixed fraction and let the neck absorb the rest.
* **`CTX_SeatStandin`** — bucket seats at the real anchors so contact can be
  *seen*. Read `build_seat_standins`'s docstring before you trust it: it shares
  the 0.445 pan constant with the placement and therefore **cannot** check it.
  What it can check is the **back and the wings** (`T(0, 0.22, 0.62) @ Rx(-9)`
  × (0.44, 0.045, 0.40) and two 0.04 × 0.30 × 0.16 wings) against a real body,
  because those come from `build_architecture._seat` and share nothing with the
  figure. Independently confirmed while writing it: `_seat`'s kind-0 pan is
  `xbox(T(0,0,0.42), (0.44,0.44,0.05))`, so its top face is at 0.445 exactly.
* **Six cameras** (`add_cameras`), each aimed at a claim rather than at the
  prettiest part of the block: the whole block **on the car's own bearing**
  (watching heads should point into the lens) and **at 78° to it** (they should
  be in profile with the bodies square to the track), the manifest's own
  14.7 m / 28 mm seated row, the people on their feet, hands-and-props at
  0.7 mm/px, and the library contact sheet.
  **[FIFTH PASS: two of those six could not answer the question they were
  built for and are replaced. See §00000.1 and §00000.3.]**
* `spectator_crowd --selftest` **9 checks, 0 failed**.

### 0000.4 THE GATE, SECOND RUN — 6 of 8, and the two it cannot measure

    no_external_assets              PASS      witness_frame_valid            PASS
    material_depth                  PASS      surface_microstructure         PASS
    geometry_resolves_at_distance   PASS      relief_reads_as_lip_and_shade  NOT MEASURED
    per_instance_variation          PASS      silhouette_departs_analytic    NOT MEASURED
    >> STAGE RESULT: ITEM_REJECTED

840 objects, **34,304,220 triangles**, 40,790 per source; realised **3,803
instances from 562 distinct source meshes and 562 distinct shapes**, commonest
source **0.9 %** (limit 25); edges p10 0.13 px at 14.7 m; subject 18,390 px
(was 0); band-pass fine contrast **10.74 %** of mean against the brightness-
matched wedge controls at 0.039.

The two NOT MEASURED are **the gate failing to measure a seated human**, not
(necessarily) the item failing:

* `relief_reads_as_lip_and_shade` — *"too few pixels after erosion"*. The
  subject's lit area is 14,816 px spread over a torso, two arms, two legs and a
  head; eroding it to exclude the outline leaves almost nothing. `crew_figure`
  passes this at 8/8 because a **standing** figure has a big contiguous trunk.
* `silhouette_departs_from_analytic` — *"no contiguous run of 100+ single-
  outline rows"*. A seated person has arms in front of a torso in front of a
  seat, so almost every scanline crosses the outline four or more times.

Both are properties of the subject's shape. **Do not "fix" them by choosing a
standing source with `--subject`** — the gate picks the median deliberately and
records an override. What is honest is to say the item is measured on 6 of the
8 and that the other two need a different instrument for a seated figure.

### 0000.5 AND THEN IT WAS LOOKED AT — five frames, and the head is the problem

`render/items/spectator_crowd/` — `ROW.png` (the manifest's own 14.7 m / 28 mm,
3840x2160), `HANDS.png` (3.2 m / 85 mm, 0.7 mm/px), `FEET.png` (9 m / 50 mm,
the people on their feet), `BLOCK_ONAXIS.png` / `BLOCK_CROSS.png`, plus 1:1
crops in `crops/`. **`crops/feet_c.png` and `crops/midrow.png` are the two to
open first.**

**WHAT SURVIVES BEING SEEN.** The block reads as a crowd. Occupancy clumps into
irregular patches with real gaps and the 16 aisle bays read; no repeated figure
is visible at block scale; skin tone, garment colour, garment type, stature and
build all have obvious range; poses differ figure to figure with no visible
"arms crossed in an X on the lap" repeat; cloth has collars, cuffs, ribbing and
real fold structure (the white knit in `feet_c.png` is genuinely good); shoes
have soles, midsole stripes and tread and read as shoes.

**WHAT DOES NOT, and it is defects 1 and 6 — the two the covered tier could
hide behind a helmet and a glove.**

1. **THE FACE IS A BLANK EGG.** At a **180 px head** in `HANDS.png` and a
   120 px head in `crops/feet_c.png`, every face is a smooth featureless oval:
   no eye sockets, no brow shadow, no mouth, a nose that is at most a faint
   smudge. `build_head` emits the features and `LOD_L1.eyes = 1`, so this is
   **not** missing geometry — it is geometry at **essentially zero contrast**,
   which is the same disease as §00.5's "a mark at 2 % contrast" one layer up.
   Suspect the skin shader's zone channels (`hk_lip`, `hk_brow`, `hk_dark`) and
   the relief amplitude on the orbital rim, and A/B it the way §000.1 A/B'd the
   cloth: build one figure with the face relief off and one with the skin
   tinting off, and see which frame changes.
   **[FIFTH PASS: done, and BOTH suspects are wrong. The relief carries the
   face and the tint does 0.05 % of the work. See §00000.1 and §00000.8.]**
2. **THE HANDS ARE MITTENS.** `crops/feet_c.png` has six `sit_cheer` figures
   with both arms up and **every raised hand is a flat paddle with a thumb**.
   Cause is exact and known: `LOD_L1.fingers = 3` (grouped), and the seated
   tier — 85 % of the block — is built at L1. The figures ON THEIR FEET are now
   L0 and their hands DO have five separated fingers (visible in `HANDS.png`),
   which is the A/B in one frame. **The fix is to build the seated library at
   L0 too.** It costs ~62 M triangles of library against 34 M and about 16
   minutes of build; it is instanced, so it costs nothing per person. It was
   NOT done because it could not be rebuilt, re-gated and re-looked at in the
   context that was left, and shipping an unrendered change is how this project
   got its nineteen broken instruments.
   **[FIFTH PASS: fixed, at +3.1 % of a figure rather than +166 %. §00000.5.]**
3. **HAIR IS A MOULDED SHELL.** Smooth, glossy, no strand break at the
   silhouette, no parting, no clumping — a swim cap. 190 strands at L1 (620 at
   L0) and none of them read. The pole fix in §0000.2 removed the needle; it
   did not give the mass an edge.
   **[FIFTH PASS: worse than this says — it is a granular CRUST, not smooth.
   It is the ugliest thing in the frame. §00000.8.]**
4. **CAPS READ AS HARD HATS.** The white ones especially: a smooth
   hemispherical crown with a peak that does not read from above, no six-panel
   seams, no button, no crown break. 29 % of this tier wears one. §00.4 fixed
   the cap being *inside the hair* and gave it a crown; the crown it gave it is
   a bowl.
5. **THE FLAT PROPS ARE CONSPICUOUS AND SAMEY.** `phone` (28 %) and
   `programme` (15 %) are both a pale flat slab, so 43 % of the block is
   holding a bright rectangle against dark clothing and they are the most
   repeated visual element in `ROW.png`. Give the programme a fold, a curl and
   a printed panel, and the phone a dark screen.
6. **`sit_cheer` repeats as a rigid V** — both arms straight up at nearly the
   same angle, six times in one crop. It is 5 % of the seated draw and it is
   the most conspicuous pose in the block, so it needs the most spread, not the
   least.

**AND THREE OF MY OWN CAMERAS WERE WRONG**, which is the §0.6 lesson
repeating: **both** block cameras sit far enough out (`CAM_BLOCK_ONAXIS` 200 m,
`CAM_BLOCK_CROSS` 148 m) that `macro_rig`'s depth of field turns every figure
into a blur, and both look *down* on the stand at 9–11° of elevation instead of
along it. **Neither can answer the question it was built for** — confirmed by
looking at both. What they do still show, and it is worth having: the occupancy
gradient and the 16 aisle bays read, the colour speckle is even, and there is
**no banding or repeated-figure moiré at block scale**. Re-shoot them from
eye level on the car's own bearing with the aperture wide open before drawing
any conclusion about attention. `CAM_SHEET` was placed at **0.0 m** because
`add_cameras` read `o.matrix_world.translation` before anything had evaluated
the depsgraph, so every library object reported the identity and `np.ptp` of
that is zero. Fixed in the source; both frames need re-shooting from eye level
with `fstop` wide.
**[FIFTH PASS: THE DEPTH-OF-FIELD DIAGNOSIS IS WRONG. `use_dof` is False on
all six cameras and always was. The fault is 8 px of head. §00000.1.]**

### 0000.6 WHAT IS STILL NOT DONE

1. **Defects 1 and 6 are OPEN on the uncovered tier**, with the evidence and
   the fix for each written down in §0000.5 items 1 and 2. Defects 3, 4 and 5
   are answered and were confirmed in the frames.
2. **The GA tier still does not exist.** `spectator_standing_ga` — 3,500
   figures, 15.4 m on a **35 mm** lens (242 px/m, a standing figure is **424
   px → L0**, a full tier above the seated crowd) — has no module, and its
   declared host `ga_viewing_bank` (6 instances, 1,455 px, *"the WEAR is the
   object"*) has no module either. That is two items, and the host must come
   first because the figures stand on it.
   **[FIFTH PASS: the MEASURED sharp presence is 278.7 px, i.e. L1, not the
   424 px / L0 the manifest arithmetic gives. §00000.7 item 3.]**
3. **The demographic half of defects 3–5, measured over the 894-source
   library and confirmed in the frames:** 4 age bands (74.5 % adult, 16.7 %
   elder, 4.5 % child, 4.3 % teen), 43.7 % female, stature **1.09–1.92 m**,
   sd 0.128 → defect 5. **78.7 % holding something** over 8 prop kinds →
   defect 3. 11 top types, 7 bottom types, 5 headwear, 8 hair styles →
   defect 4. The manifest's own note for this item says *"at 47 px a head is a
   hair shape, a skin value and a suggestion of features — modelling eyes and
   mouths is wasted work"*; the user overrode that with *"idc if there not
   noticable"*, and §0000.5 is what a 180 px head actually looks like.
4. **The blend that was gated is two source revisions old** (840 sources, L1
   seated / L0 on foot, before `ROLE_SPAN`). The current source builds 894 and
   has not been rebuilt or re-gated.
5. The five §00.6 polish items are **still open** and three of them are head
   defects on a tier that has no helmet to hide behind: the balaclava aperture
   (crew only), **ears invisible at a 400 px head**, **waxy skin and a straw
   fringe**, and the hip skin sliver.
6. **Swapping `spectator_seated` for this** still needs everything §000.7 item
   6 lists, and now also a re-gate, because the blend that was gated is two
   source revisions old (840 sources, before `ROLE_SPAN`).

---

## 00. UPDATE 2026-08-02 (later still) — THE GARMENT STOPPED WEARING THE BODY, AND THE HELMET STOPPED BEING AN EGG

*(RESTORED 2026-08-03 from the fifth pass's own reading of it. Verbatim.)*

Section 0 below is the previous agent's record and is still correct. This block
is what changed after it, in the order the render ladder found things.

**The renders are `render/items/human_bench/`.** B2 is where section 0 stopped;
B3, B4, B5 are this pass; A2 is the paddock bench re-rendered after the
inside-out fix; A3 and A4 are a new **face framing** (3 figures, `--aim head
--px 2600`, head ≈ 400 px) which is the only way any of the head defects below
were visible at all. Every fix here was found in one of those pictures.

### 00.1 GARMENTS INHERITED THE BODY'S MUSCLE RELIEF — fixed and measured

`garment_from_sweep` sliced the **body's** `Sweep` and offset it, so every
garment shell carried `build_arm`'s `noise_amp = 0.055 r` and `build_torso`'s
`surface_noise x 0.010 x chest_depth` one-for-one. `Sweep` now keeps the
**relief-free rings** alongside the noisy ones (`BX`, `BY`), and
`Sweep.relaxed(sigma_m)` returns a garment base that is those rings low-passed
at a physical **cloth-bridging length of 17 mm** — which attenuates a 50 mm
feature to 0.10 and passes a 250 mm one at 0.91, so the spinal groove and the
profile-table kinks go and the deltoid, belly, chest and buttocks stay.

The shipped path is kept as `relax="none"` and is the positive control:

| | arm | torso |
|---|---:|---:|
| gain of the garment's radial residual on the body's own noise field, **shipped** | **1.048** | **0.910** |
| same, **delivered** | 0.021 | −0.060 |
| shell-normal change, RMS | 2.74° | 2.08° |
| **m removed**, `2 tan(theta)/tan(12.47°)` | **0.433** | **0.329** |

against the fold field's own 0.90 target and the shader's 0.28. An
independently written estimator (finite-difference slope of the noise field on
the arm rings) returns 2.06° / m = 0.326 where the instrument returns 1.90° /
0.300 — two statistics, 8 % apart.

**Looked at:** `B2 -> B3` at 767 px, A/B on the light overall's thigh and
forearm. The soft blobs that followed the limb are gone; the cloth crumple is
not. That is the whole point.

Two consequences that had to be handled and are easy to miss:
* a relaxed base moves the shell INWARD wherever the body bulged, so
  `garment_from_sweep` measures the worst positive residual and loosens the
  whole shell by whatever it is short. Without it the limb pokes through the
  sleeve on one figure in fifty and only a render would ever find it.
* `Mesh.LOCK` — pieces added with an explicit `col=` are no longer repainted by
  `colour_by_material`. A livery panel and the overall under it are the same
  material in two colours, so colour cannot be derived from the material slot.

### 00.2 THE HELMET WAS AN EGG — rebuilt

`HELM_LOBES` was six Gaussians of 2.3–6.8 mm on an ellipsoid. At 438 px/m a
2.3 mm "crown spine" is **one pixel**. `_helm_P` is now a displaced direction
field — evaluable at an arbitrary direction, which is what lets vents sit on the
finished surface — with a **42 mm chin bar**, a **21 mm rear spoiler**, a 13 mm
brow band, a jaw taper and a nape roll; the eyeport is a 9 mm recess with a
4 mm **rim bead** and the visor plate sits 3.5 mm inside the shell line (or
25 mm proud, open). `_helm_pad` puts closed rounded-rect pads on it: two crown
intakes with dark recessed mouths, two rear exhausts, a chin vent with three
bars, and the **visor pivot bosses**. Shell 242 x 308 x 306 mm against a
161 x 203 x 237 mm head.

**B4 showed the next defect immediately:** one ellipsoid centred low on the head
has a vertical semi-axis 23 % longer than the horizontal one, so the helmet came
to a rounded POINT. The centre is now at `0.28 head_h` and the semi-axis is
split above and below it — crown sphericity `az_up/ax = 0.99`, minimum clearance
over the skull 26 mm. `B4 -> B5` is the picture.

### 00.3 TEAM LIVERY — 27 teams, all geometry

`livery_for_team(brand)` takes a brand from **itemkit's one book** (Law 2 — 31
invented brands, shared with the boards and the trucks) and returns base,
accent, trim, the brand's own `mark`, and one of six patterns. The patterns are
distributed 7/7/5/4/4/4 over the 31 brands — the first version hashed
`sum(ord(c))` of the name and put 11 of 31 on one pattern, which is this
project's "one tree spammed 100 times" in a new costume.

It is **panelled, not painted**:
* horizontal bands (yoke, shoulders, waist block, sleeve, leg) are emitted as
  their **own ring sections of the same sweep**, so the colour edge falls
  exactly on a ring and is **zero pixels wide**;
* vertical zones (side panels, chest chevron, sash) are per-vertex colour with a
  **2.2 mm welt** on the boundary, because one ring column is 40 mm on the chest
  — 17 px — and a colour edge inside a quad is a soft edge. The welt is the line
  the eye reads, and it is what a real panelled suit has anyway;
* sponsor patches are **closed pads 1.6 mm proud** carrying the team's mark as a
  stack of pads 1.3 mm above that. `MARK_PARTS` reproduces `build_dressing`'s
  mark vocabulary (chevron, ring, bars, delta, hex, wing, bolt, diamond, …) as
  geometry. No image, no font, no downloaded logo.
* the band bounds are in the sweep's **own parameter** — the trunk runs −0.24 to
  1.00 — and B4 was built with them read as a 0..1 fraction, which put the
  "shoulder" band across the lower ribs. Look at the picture.
* a mark drawn in the team accent on a near-white patch is yellow on white.
  `_contrasting()` picks whichever of the two team colours reads against it.

### 00.4 THE PADDOCK FACE — one hard bug closed, the rest still open

Re-rendered (A2) after the inside-out fix, then at a face framing (A3). A3 shows
a **cap with no crown**: a red band and a peak with a granular brown dome above
them. The cap was not missing — it was INSIDE the hair. `build_hair`'s mass is
`(8 + 30 x hair_vol) mm`, up to 39 mm, and `build_headwear`'s clearance was a
flat 6 mm. Now a hat squashes the hair (`squash=0.40`, and the strand count with
it) and the dome is given `1.06 x` the squashed thickness as clearance. A4 shows
three caps with crowns.

The collar was the same class of error: `neck_r * 1.03 + 0.55 * ease` stood it
32 mm off the neck and it read as a life-ring on every figure. `0.24 * ease`,
and the garment's own neck opening moved with it so the two still meet.

### 00.5 `item_gate` ON `crew_figure` — 8 of 8, ITEM_ACCEPTED

    no_external_assets              PASS      witness_frame_valid            PASS
    material_depth                  PASS      surface_microstructure         PASS
    geometry_resolves_at_distance   PASS      relief_reads_as_lip_and_shade  PASS
    per_instance_variation          PASS      silhouette_departs_analytic    PASS

* microstructure fine(r1–r2) **6.147 %** of mean against the strictest
  brightness-matched smooth control 0.042 — **x145.7**, bar x2.0
* **check 7, the one 21 of 28 wave-1 items fail: dip +0.2999 along the light
  against a control of +0.0646**, bar control + 0.030 and ≥ 0.050 absolute
* check 8 outline wander **7.1 mm** (2.19 px), bar 5 mm and 3x the sphere's
  0.29 px floor
* edges p10 **0.99 px** at 12.0 m, bar 6 px; 120 instances, 60 topologies, CV
  0.073
* `render/items/crew_figure/macro.png` is **3840 x 2160**, read back off disk.

`crew_figure`: 120 figures, 5,942,025 tris, **49,517 per person**, 27 teams,
51 groups, 0 pieces undecided, worst inside-out 2.4 %, nothing below the contact
plane. `humankit --selftest` 20 checks 0 failed in plain python, **23 checks 0
failed inside Blender**; `crew_figure --selftest` 8/0.

**[FIFTH PASS: that run was framed at 767.2 px, which is 39 % closer than the
film ever gets sharp (551.8). A harder test, so the pass stands. §00000.6.]**

### 00.5a A CONTROL THAT STOPPED BEING A CONTROL — worth the paragraph

`every_bump_drives_height_not_filter_width` went **RED** in the Blender half of
the selftest this pass, and the message read *"31 bump stages … all with Height
linked and nothing in Filter Width; the same graph built through
`itemkit.NT.bump` miswires **0 of 2**"*. The 31 real stages were all correct.
What had changed is that **`itemkit.NT.bump` was fixed upstream** (2026-08-02
11:01) — so the negative control stopped failing, and a check whose control
cannot fail is worth nothing, which is exactly what it reported.

A negative control that depends on ANOTHER MODULE STAYING BROKEN is not a
control. It now reproduces the index pinning verbatim inside the check, so it
fails on its own terms forever. Fifteenth time on this project that the
instrument was the thing that moved.

### 00.6 WHAT IS STILL NOT GOOD ENOUGH — found by looking, NOT fixed

1. **The overalls read as skin-tight bodysuits.** Stripping the noise fixed the
   *anatomy blobs*; it did not make the suit HANG. Ease is ~20 mm and the shell
   follows every anatomical radius. The lever I did not pull, because it is a
   second unverified change of the same class in the same pass: a **morphological
   dilation along v** in `Sweep.relaxed` — cloth spans between high points, so
   the garment radius over the thigh should be the widest radius within a
   bridging length, not the local one. Do it as its own A/B render.
2. **The sponsor patch reads as a rounded blob** at 767 px and the mark inside it
   is small. `expo=8.0, cols=20` made it rectangular in the parameterisation but
   it is conformed over the fold field, which rounds it.
3. **A balaclava head is a dark egg.** 55 of 120 crew are headset/cap_headset,
   and `build_balaclava` covers the face completely — which is what the manifest
   asks for ("zero exposed skin") and reads as a mask. A face aperture would
   break it and would move `skin_is_covered`; decide that deliberately.
4. **No ear is visible in the A4 profile** at a 400 px head. `build_ear` runs at
   L0 and I did not establish whether it is under the cap hem, too small, or too
   flat. Unresolved, and it is a profile view, which is where an ear is most of
   the read.
5. **The skin is waxy and uniform** at a 400 px head, and hair strands poke
   through the hat hem as a straw fringe (`squash` cuts the strand COUNT, not
   their length).
6. The sleeve silhouette is nearly a straight line from shoulder to wrist —
   there is ease and a fold field, but no elbow break.

**Do not start the crowd** — `garment_from_sweep` is now the foundation it will
be built on and item 1 above is still open on it.

---

## 0. UPDATE 2026-08-02 (late) — SIX DEFECTS FOUND BY LOOKING, AND THE BIG ONE

*(RESTORED 2026-08-03 from the fifth pass's own reading of it. Verbatim.)*

Section 7 below is still the honest record of where the *previous* build stood.
This block is what changed and, more importantly, **how it was found**: every
item here was found by rendering a five-figure bench at 767 px and cropping it,
not by any check in the file. Two of them had been wrong for the entire life of
the module and every number in this document passed while they were.

**[FIFTH PASS: "Section 7 below" NO LONGER EXISTS — see the truncation notice
at the top of this file. §1 to §7 were destroyed and could not be recovered.]**

### 0.1 The head, the hair, both shoes and every sole were INSIDE-OUT

An orientation audit of a finished L1 figure — signed volume **and**
mean(normal · radial) per emitted piece, two independently written statistics
that agreed on every piece — found **54 of 318 pieces facing inward**:

| piece | tris | normal · radial |
|---|---:|---:|
| head shell | 2,816 | **−0.966** |
| both ears | 99 each | −0.065 |
| hair mass + hanging fall | 15,972 | **−0.97** |
| both shoe uppers | 360 each | −0.717 |
| both soles | 360 each | −0.450 |
| all 22 sole tread bars | 12 each | −0.733 |

Cycles flips a back-facing normal for diffuse, so **none of this rendered
black** — it rendered with every bump *inverted*: a brow ridge lit as a groove,
a hair clump as a gutter, a leather crease as a welt. It is the mechanism behind
three of the six defects section 7 lists ("faces are not resolving", "hair reads
as a straw cone", "shoes read closer to slippers"), and no check in the module
could see it because every check measured the *model* and none measured which
**side** of the surface the renderer would get.

`Mesh.orient_outward()` now decides every piece by **exact signed volume** —
open pieces are closed first by capping their boundary loops — and
`humankit --selftest`'s `every_surface_faces_outward` runs it against a control
**pair** (an inward grid must be flipped, an outward one must be left alone).
Ray-cast inside-out surface fraction: **10.5 % → 1.1–3.3 %.**

### 0.2 Every capped figure had a peak across its mouth

`_peak` pinned the cap peak at `z = 0.075 × head_h` against eyes at
`0.140 × head_h`, and drooped it 47 mm — so the root crossed the brow and the
tip hung **80 mm below the pupils**, at chin height. The crown hem was one
latitude all the way round, which put a beanie's front edge 37 mm below the
eyes. Both now derive from the crown's own hem, which is azimuth-dependent
(higher at the face, lower over the occiput). `headwear_clearance_mm` measures
it and the old constants are kept as a positive control: **−33.9 mm → +2.8 mm
worst case.**

### 0.3 The sleeve heads were chimneys, not pauldrons

`extend_start(2, upper_arm × 0.30)` walked the sleeve's open end **90 mm
straight up the arm axis at 86–99 % of full radius** — clear of the trunk shell,
whose top ring is at the acromion — and stopped there, open. `sleeve_head()`
builds a real set-in dome that turns inboard and closes on a pole fan inside the
chest; the trouser legs get the same treatment aimed at the pelvis. Its winding
is decided against the tube it is stitched to, not assumed.

**The first two attempts to measure this were both the wrong layer** and are
worth recording: "height above the acromion" is confounded by pose (an arm
raised over the head legitimately puts sleeve above the shoulder), and "open
boundary loop area" returned **0.49 m² of hole on a figure with no visible
hole**, because this mesh is deliberately a stack of open interpenetrating
shells and a trunk's top ring is legitimately open under a shoulder cap. Only
`inside_out_fraction` — cast rays, take the first hit, count back-faces —
measures what a viewer sees.

### 0.4 Every seam welt was one column wide, i.e. a spike

`_ridge` was called with `width_u` 0.006–0.010 of a turn. A garment ring carries
`lod.ring` points — 26 at L0 — so **one column is 0.038 of a turn**. Every seam,
placket and zip therefore landed entirely inside a single column and displaced
one line of vertices by its full height: a hard 3 mm ledge running the whole
length of the garment. Clamped to 0.62 of a column spacing.

### 0.5 THE AMPLITUDE MODEL WAS MISSING THE SUN — this is the big one

Three amplitude sets have now been rendered and rejected, and all three were
reasoned about in **millimetres of cloth**. What the eye judges is the radiance
modulation, and for a Lambertian surface under a sun at elevation *e* that is

        m = 2 θ / tan(e)

The film's sun is at **12.47°**, where `tan(e) = 0.221` — a **4.5× amplifier**.
Worked through:

| amplitude set | slope | m | how it rendered |
|---|---:|---:|---|
| shipped | 5.0° | 0.79 | a machined cone |
| first fix | 22.6° | 3.76 | coarse stucco |
| second fix (the one section 7 describes) | 10.4° | **1.66** | **thick felt / towelling** |
| this | ~1.8° | **0.28** | isotropic; creases carry the rest |

A 157 % peak-to-peak swing on a 4 px feature over an entire garment is felt,
whatever it is called. Cloth genuinely crumples at 20–30° — but *locally, at
creases, over a fraction of the area*. So the isotropic stages are now derived
from `slope_for_modulation()` and a **sparse `crease` stage** carries the steep
part: a ridged noise (which concentrates its range into narrow valleys) gated by
a coarser noise, so it acts on about a quarter of the surface at m ≈ 1.0.

`relief_modulation_is_cloth_not_felt` asserts both halves.

**The same error was one layer down, in the GEOMETRY**, and after the shader was
corrected it became the dominant one: `fold_field`'s 8.2 mm of radial
displacement at a 100 mm flute is a **14.4° surface**, i.e. **m = 2.32**. Its
amplitudes now come from `amp_mm_for_modulation` too — 2.09–4.16 → **0.93–1.29**
(geometry folds should carry *more* than the shader, because they are the real
folds, but ~0.9, not 2.3). **Verified by looking**, B1 → B2 at 767 px: the tan
overall's granular crust is gone.

**[FIFTH PASS: `m = 2 theta / tan(12.47 deg)` is the yardstick §00000.1 uses on
the FACE, where the lobes measure m = 2.22 — higher than anything on the
garment. The face is not short of relief. It is short of relief that reads
FRONT-ON. §00000.8.]**

### 0.5a WHAT IS STILL FOAM, and it is not the cloth

B2 still shows large soft blobs on the light-coloured overall, and they are
**the body's own muscle-relief noise showing through the garment**.
`garment_from_sweep` slices the *body's* Sweep and offsets it, so the shell
inherits every ring the body has — including `build_torso`'s
`surface_noise × 0.010 × chest_depth` and `build_arm`'s `noise_amp = 0.055 × r`.
The tell is in the picture: the lumps follow the limb like anatomy rather than
hanging like cloth. A garment should be lofted from a *smoothed* copy of the
body rings, not the noisy ones. **Not fixed.** *(Fixed in §00.1.)*

### 0.6 The bench itself was lit wrong, and that is the lesson repeating

The first bench render came back with a 2 m **white cube** occluding the middle
figure and every figure lit by Blender's **default point lamp** — because
`--factory-startup` ships a Cube, a Camera and a Light and the script never
purged them. Every appearance judgement made on that frame would have been made
under the wrong light. Found in the first thirty seconds of looking at the
picture; invisible to everything else.

**[FIFTH PASS: and it happened AGAIN, quieter. Every item test frame ever
judged — including all of B1..B5, A2..A4 and the crew macro — was rendered at
`world_contract.REFERENCE_EXPOSURE_EXTERIOR = -3.048` while the film renders at
`film_exposure.FILM_EXPOSURE = -3.628`. 0.580 stops over. §00000.3b.]**

### 0.7 What is NEW, not just fixed

`world/items/crew_figure.py` — **120 pit crew, the COVERED tier**, at the
manifest's 12.0 m / 35 mm and looked at at the measured 767.2 px. New layers in
`humankit`: `build_overall` (one-piece suit: waist seam, full-length zip welt,
yoke, elbow and knee panels, gathered cuffs at wrist and ankle),
`build_helmet` (shell with a **recessed** visor aperture and a separate visor
plate in the recess), `build_balaclava`, `build_glove` (the hand inflated by a
real 2.4 mm with a gauntlet cuff), `build_headset`, and two new material slots —
`MAT_HELM` (clear-coated paint, gloss 0.085–0.185, coat 0.85) and `MAT_VISOR` —
because a helmet run through the fabric shader reads as a felt hat.

`world/items/human_bench.py` — the five-figure, one-camera, ~7-second bench that
found all of the above.

---

**`world/humankit.py`** is the shared procedural human foundation. Every person
in this film — 7,800 seated spectators, 3,500 on the GA banking, 260 paddock
personnel, 160 marshals, 120 crew, one driver — is built from it. It imports
`world/itemkit.py` rather than duplicating any of it, exactly as
`world/items/pit_wall_unit_itemkit.py` does.

**`world/items/paddock_personnel_figure.py`** is the worked item: 260 people,
one object each, gated at the manifest's own 10.0 m / 35 mm.

---
