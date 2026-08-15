# STAGING R2-3241 .. R2-3300 — the shutter sweep

Agent `r2-3241-shutter-sweep`. Leases: `docs/STAGING-R2-3241-to-R2-3300.md`,
`tools/r2_3241_exposure.py`, `tools/r2_3241_motion_pose.py`.

Task: R2-3063 named a defect class — **A TEST BED THAT DOES NOT RESEMBLE THE
DELIVERY** — after the asphalt shipped visibly blank while every instrument
pointed at it passed. The cause was one line of selection logic:
`build_surface.FILM_POSE_FRAMES` picks test frames **by sharpness**. This task
asks how far that reaches. No render was commissioned and none is proposed;
**$[redacted] of credit is untouched.**

---

## R2-3241 — THE ANSWER, IN ONE LINE

> **The exposure is real, it is large, and only the asphalt was actually
> affected.**

Everything below is the evidence for that sentence and the boundary of what it
does not cover.

Two structural facts do most of the work, and neither was known when the brief
was written:

1. **Three of the six beats never reach the delivered shutter at all.** Two
   instruments measured independently — `track_scale.json`'s road-weighted `mb`
   column, and a fresh per-frame median streak over every visible world point,
   read off the **delivered** camera so the showroom frames `track_scale` has no
   rows for are covered. They agree (rho 0.85 on 2,165 shared frames, median
   ratio 1.00):

   ```
                    track_scale mb (road-weighted)     all visible points
                    p50    p99    max    %>=160     p50    p99    max   %>=160
     1_assembly    19.9  114.6  116.2      0.0%    22.8  122.0  126.9    0.0%
     2_launch      51.9  130.4  131.0      0.0%    47.9  130.0  130.6    0.0%
     3_breach      11.8   36.6   46.9      0.0%    11.9  163.6  201.9    1.2%
     4_transit     28.0  113.3  121.0      0.0%    31.7  199.7  231.3    1.6%
     5_lap         31.9 1070.3 2391.0     11.0%    32.0  188.2  306.2    2.4%
     6_ending       6.0   79.9   82.3      0.0%     3.2    9.7    9.8    0.0%
   ```

   **Beats 1, 2 and 6 contain no frame above 131 px by either instrument**; the
   ending peaks at **9.8 px**, i.e. it is a still. The worst of the four
   `FILM_POSE_FRAMES` is 69.7 px, so for those three beats **the existing sharp
   bed is within a factor of two of the worst frame the audience ever receives**
   and the defect class cannot bite. Beats 3 and 4 graze the floor on 1–2 % of
   frames, but only away from the road — their road-weighted `mb` never exceeds
   121 px. **The surface exposure is beat 5's alone.**
2. **Within the one exposed beat, the collapse is a property of the road
   surface and not of the shutter.** The kerb sits in the identical frames at
   the identical smear and does not move.

---

## R2-3242 — THE RANKED EXPOSURE LIST

`tools/r2_3241_exposure.py`. It ranks **by screen presence**, as the brief asks,
and carries exposure as a property of each row rather than as the sort order —
ranking on exposure was tried and puts a 70x ratio on a distant marker post
above the road surface that fills the frame.

For a **surface** verdict the right unit of screen presence is the sampling
rate, so world objects are ranked on `peak_px_per_m` — how finely the delivered
film ever samples that surface. The exposure term is

```
   exposure_ratio = peak_px_per_m / peak_sharp_px_per_m
```

taken from `screen_presence.py`'s own `SMEAR_SHARP_PX = 6.0` budget, imported
rather than retyped. It is **how much finer the film delivers a surface than any
frame a still bed could ever pose it on**, it is 1.0 for anything whose finest
moment is already sharp, and a row is flagged `*` at 2.0x — one octave, the unit
every relief budget in this project is written in.

**311 of 560 world objects and 269 of 434 manifest items are exposed.** The
class is not rare. That is exactly why it needed measuring rather than listing.

```
presence sweep: camera=render/film22_path.json  (DELIVERED — see R2-3243)
     object                                 mm/px     mm/px   ratio  blur%  mb@peak    vis
                                        delivered     sharp                   px@4K frames
  *  SURF_Track                               0.8       3.8    4.6x    68%     2391   2391
  *  SURF_AccessRoad                          0.9       1.9    2.0x    71%       11    698
     ARCH_Paving_Forecourt                    0.9       1.0    1.0x    75%        -   1246
  *  ARCH_PitBuilding_Shell                   1.0      31.6   31.7x    80%       41    715
  *  BR_Runoff_R                              1.1       3.5    3.1x    70%      170   1784
  *  BR_Verge_R                               1.2       2.8    2.3x    70%       73   2227
  *  SURF_Kerb_T1_out1                        1.3      23.8   18.8x    58%       35    684
  *  SURF_Kerb_T1_out2                        1.3      32.0   24.8x    62%      112    730
  *  BR_Trap_apex_R_1188                      1.4       7.5    5.5x    65%        8    571
  *  VEG_grass_meadow_H                       1.4       3.8    2.7x    63%       11   2274
  *  BR_Subbase_R                             1.5       4.8    3.2x    68%        7   1871
  *  VEG_grass_reed_H                         1.5       6.1    4.0x    63%       11   2278
  *  VEG_weed_dock                            1.5       4.3    2.8x    62%        8   2251
     VEG_grass_dry_H                          1.6       3.1    2.0x    64%       17   2276
     VEG_grass_fescue_H                       1.6       2.7    1.7x    63%       18   2275
  *  BR_Transit_NorthWall                     1.7       4.6    2.8x    86%      121    434
  *  BR_Stones_outer_R_854                    1.7       7.1    4.2x    58%       11    598
  *  VEG_weed_ragwort                         1.7       4.2    2.5x    61%      288   2246
  *  VEG_grit_chip                            1.7       4.8    2.8x    64%       18   2482
  *  BR_Trap_outer_R_854                      1.8       7.1    4.0x    57%       12    598
  *  SURF_Kerb_T5_in0                         1.8       7.9    4.4x    65%       12    606
  *  SURF_Kerb_T4_out1                        1.9     126.7   66.2x    55%       11    410
  *  SURF_Kerb_T2_out1                        2.2      37.4   17.2x    59%      226    707
  *  SURF_Kerb_T3_in0                         2.2     123.5   56.1x    53%       99    386
```

Full list, all 560 objects and 434 items: `work/r23241/exposure_rank.json`.

**The brief's 3 px floor barely bites: 1 item of 435 falls below it.** That is
not a broken gate, it is what an upper bound does — `screen_presence.py`'s own
docstring says an item inherits the best moment any of its host objects ever
has, deliberately generously. The 343→91 hero collapse the brief recalls came
from the frustum-and-distance correction, which is already inside these numbers.
The floor is reported because it was asked for; it is not what selects the head.

### The item head is the asphalt finding restated

Of the 434 items above the floor, **89 are both exposed and reach their peak on
a frame at or above the delivered-shutter floor** — and the top of that list is,
without exception, the road surface:

```
  rubber_line_deposit   asphalt_patch_repair   track_manhole_cover
  start_finish_line     lockup_skid_mark       marble_drift_bank
  track_drain_slot      track_gully_lid            ... all mb@peak = 2391 px
```

then `runoff_sponsor_paint` / `verge_green_paint` at 170 px, then the pit-lane
population at 480 px. **There is no third group.** The item campaign's relief
verdicts are exposed exactly where they sit on the road.

---

## R2-3243 — THE RANKING BASIS HAD THE SAME DEFECT AS THE THING IT RANKS

Control C4 was written to check that the camera `screen_presence.py` swept is
the camera the proxy was rendered from, because `docs/` already carries a set of
`*_SUPERSEDED_a6_oldcam.json` files and this project does not assume what it can
check. **It failed.**

```
C4  authoring camera (camera_rig_path.json) vs DELIVERED camera (film22_path.json):
    1142/2978 frames differ in position (max 21.40 m), 1065 in lens (max 56.00 mm),
    2516 in orientation
```

`world/camera_rig_path.json` was last written 2026-08-04 15:49 and swept into
`docs/screen_presence*.json` at 2026-08-04 01:49 — *before* its own source was
last edited. `render/film22_path.json` was extracted from the shipped 10 GB
blend at 2026-08-08 04:42. **The whole of beat 1 (f2–f753) is a different
camera**, as is f2084–f2260 of beat 5.

So the file the brief points at for ranking, and which the item campaign's
tiering rests on, describes a film that was not delivered. That is the same
defect class one level up: **a measurement bed that does not resemble the
delivery.** It is logged here, not acted on — `docs/screen_presence*.json` is
not my lease and beat 1 is another agent's ground.

**Scoped, before anybody over-reads it.** The four `FILM_POSE_FRAMES` and the
three motion frames selected below are all in the *agreeing* range — f1547,
f2000, f1226, f1350, f1787, f2622, f2632 are byte-identical between the two
cameras and f2225 differs by 5 mm and 0.1 mm of lens. **The R2-651 and R2-1036
surface work is not contaminated by this.** What is contaminated is beat 1's
presence numbers, and therefore any tiering decision taken on them.

The fix taken here: `resweep` recomputes presence against the **delivered**
camera and `rank` refuses the stale sweep. Median exposure ratio moves 2.16x →
2.19x (rho 0.83, |log2 diff| p50 = 0.02) so the aggregate is sound, but
individual objects move by up to 20x — `SURF_Kerb_T14_in0` 3.2x → 73.1x,
`DR_Ad_029` 12.7x → 1.4x. **Aggregates survived, rows did not.**

---

## R2-3244 — WHAT THE DELIVERED PIXELS SAY

No render. `work/r22881/scan.npz` already holds the 16–64 px @4K band energy of
every one of 48 tiles on every one of 2,978 delivered frames, and
`work/r23061/r23061_tile_geometry_join.json` already classifies ground tiles by
casting a ray through the tile centre. Both are read with
`r2_2881_pixelpeep`'s own `COARSE_FROM/TO`, `BAND_4K` and
`Gates.TILE_COARSE = 0.0020`, imported, so a number here and a number in
`work/r22881/findings.json` mean the same thing.

### The ground, by surface class and by shutter — the decisive table

```
                       smear @4K:  0-6      6-40    40-80  80-160  160-320   320+
  ASPHALT       median coarse    0.01214  0.00598 0.00381 0.00245 0.00118  0.00113
                % of tiles EMPTY    0.0%    19.6%   36.6%   44.6%   58.7%    57.7%
  KERB_BAND     median coarse         .   0.00958 0.01094 0.00958 0.01031  0.00927
                % of tiles EMPTY        .     0.0%    1.5%    3.3%    6.2%     7.1%
  PAINTED_VERGE median coarse    0.01074  0.01385 0.01046 0.00830 0.00660  0.00586
                % of tiles EMPTY    0.0%     0.0%    0.0%    3.4%   14.7%    16.7%
  BEYOND_VERGE  median coarse    0.00965  0.01102 0.00758 0.00649 0.00817  0.00280
                % of tiles EMPTY    4.1%     6.5%   10.1%    4.3%    8.9%    25.0%
```

**Read the second row and the fourth.** The asphalt falls by an order of
magnitude and goes from *nothing empty* to *three tiles in five empty*. The kerb
sits in the same frames, the same lens, the same grade, the same shutter, and is
**flat across a fifty-fold range of smear** — 0.00958 at the sharp end, 0.00927
at 320+ px. That is the control the whole question needed and it was already in
the data: a 180-degree shutter does not destroy contrast, it destroys contrast
**along one axis**, and the kerb's painted blocks survive being averaged over
245 px while the asphalt's aggregate does not.

The same collapse read against range instead of smear, which is the same
statement in the units a person can point at:

```
  ASPHALT      0-15 m   med smear 317 px   coarse 0.00104   63.9 % empty
              15-30 m             163 px           0.00286   43.5 %
              30-60 m              72 px           0.00333   39.1 %
             60-150 m              48 px           0.00526   27.5 %
              150 m+               11 px           0.00963    1.4 %
```

**At 150 m the road is fine. Under the camera it is gone.**

`PAINTED_VERGE` is the only other class that degrades at all — 0% → 16.7% empty.
That is a real gradient and it is worth one line in the next surface pass, but it
is a quarter of the asphalt's and it never crosses the point where the majority
of tiles read blank. **It is not a second casualty.**

### Everything off the ground

`tools/r2_3241_exposure.py tiles` decides which tiles are *looking at* an object
by voting with the world point cloud, and reads the delivered band there.

| checked | owned tile-frames | delivered coarse | % empty | verdict |
|---|---|---|---|---|
| `ARCH_PitBuilding_Shell` + `_Detail` | 56 | 0.032–0.037 | **0.0 %** | fine. Its 31.7x exposure is real and harmless: max streak it is ever delivered at is 76 px |
| 3 grandstands | 132 | 0.020–0.064 | **0.0 %** | fine, at 10–32x the threshold |
| 8 grass / weed species | 19 | 0.008–0.018 | **0.0 %** | fine, incl. 5 tile-frames at ≥160 px. **n is small — see the limits** |
| grit, stones, 3 gravel traps | 121 | 0.008–0.039 | 0.0 % (5.9 % inside 15 m) | fine |

**Not one of them is empty at any smear.** The client note *"blank grass with no
detail"* (R2-016) is not reproduced in the delivered pixels at 16–64 px @4K —
though with 19 owned tile-frames that is a weak refutation, and it is offered as
one.

---

## R2-3245 — EVERY CONTROL, INCLUDING THE TWO THAT FAILED AND STAYED FAILED

```
C1  independent smear vs track_scale mb: rho=0.9957  ratio 0.57-1.11        PASS
    control  frozen camera -> 0.0 px (must be 0)
C2  3 px floor: 434 kept, 1 dropped, 435 total                              PASS
C3  known casualty SURF_Track ranks #1 of 560 (top 5% = 28)                 PASS
    and is it EXPOSED by the ratio test? 4.6x vs threshold 2.0x
    control  14 objects have ratio < 1.05; 0 of them are flagged exposed
C4  THE CAMERAS DIFFER (see R2-3243). resweep is on the delivered camera    PASS
C5  ray join, ASPHALT: 0% empty at smear < 6 px, 58% at >= 160 px           PASS
```

Three of these were written, run, and came back wrong. That is the point of
them.

**C3 first said "top 20" and failed at #24** when the ranking was sorted on
exposure ratio. The failure was informative, not a bug: everything above the
asphalt was a kerb or a grid number with a *higher* exposure ratio. The ranking
was right and the sort order was wrong — presence, not exposure, is what the
brief asked to rank on, and on presence `SURF_Track` is **#1 of 560**.

**C5 is the one worth reading.** The first ownership rule called a tile owned
when an object put ≥40 points in it. Run on `SURF_Track` it returns 11,045
tile-frames at a median coarse band of 0.026 — **thirteen times the emptiness
threshold, i.e. it CLEARS the one surface in this film already proven blank.**
It was caught by running it on the known casualty before running it on anything
else. Tightened to a nearest-surface vote it still under-reports, because the
world point cloud is sampled at 1 m and a near-field tile at 8.5 mm/px covers
about 4 × 3 m of road — a dozen cloud points — so tiles below the vote size are
silently dropped. **Only 179 of 1,870 owned tiles are inside 25 m, which is
exactly where the asphalt defect lives.**

> **This file's own instrument had the defect this file is about**: a sampling
> bed that does not resemble the delivery, blind precisely in the near field.
> It is **declared, not repaired** — the ray-cast join supersedes it for ground,
> and every off-ground table above is stated with its `n`.

---

## R2-3246 — THE SELECTION-LOGIC FIX

`tools/r2_3241_motion_pose.py`. The durable repair the finder proposed: **the
motion case beside the stills, not instead of them.** A still remains the
correct bed for *"is it authored"* and nothing here argues otherwise.

**`MOTION_POSE_FRAMES` is computed, never typed.** It is the mirror image of the
comment block at `world/build_surface.py:4703` — the same table
(`render/r2651/track_scale.json`), the same coverage floor (`cover ≥ 0.40`,
which is R2-651's own: f1547 46 %, f2000 50 %, f1226 41 %) and the same sampling
ceiling (`mmpx ≤ 60`, f1226's 51.5 being the coarsest R2-651 picked), with the
`mb` column **maximised instead of minimised**. A hardcoded list would go stale
silently, which is R2-101 and R2-118 on this project.

```
  pool 638 frames pass cover>=0.40 and mmpx<=60; 143 reach the 160 px
  delivered-shutter floor, in 3 passes: f1336-f1361, f1779-f1846, f2621-f2669

  THE EXISTING BED (FILM_POSE_FRAMES, selected on SHARPNESS)
    f1547   mb=    7.03 px  mmpx=  11.77  cover=0.46
    f2225   mb=   10.29 px  mmpx=  20.96  cover=0.18
    f2000   mb=   69.71 px  mmpx=  11.46  cover=0.50
    f1226   mb=    5.44 px  mmpx=  51.52  cover=0.41
  THE MOTION CASE (same table, same filters, mb MAXIMISED)
    f1336   mb=  256.11 px  mmpx=   4.79  cover=0.69
    f1790   mb=  250.96 px  mmpx=   3.83  cover=0.90
    f2632   mb= 2391.03 px  mmpx=   0.99  cover=1.21
```

**One frame per PASS, and a pass is a contiguous run of qualifying frames.**
Taking the N highest-`mb` frames outright was tried and is wrong: the pool's top
33 are all inside f2621–f2669, i.e. one second of one corner rendered 33 times.
Grouping into runs is what makes the motion bed a *sample* of the delivered
defect rather than a close-up of its worst instant, and it sets the count from
the film instead of from the author — recut beat 5 into four passes and this
returns four frames with nobody editing the file.

> **An agreement nothing enforces.** The three runs come out at f1336–1361,
> f1779–1846, f2621–2669, and the picks land on **f1336 / f1790 / f2632**.
> R2-2881 independently named **f1350 / f1787 / f2622** from the delivered
> pixels, by a completely different route. Two instruments, two methods, three
> frames apart.

### The gate is the part that makes it non-repeatable

```python
from tools.r2_3241_motion_pose import assert_motion_case
assert_motion_case(frames, "the asphalt octave")   # raises MotionCaseMissing
```

`MOTION_CASE_MIN_MB = 160.0` px — where the ray join's ASPHALT emptiness crosses
50 %, so the floor is read off a measured delivery rather than chosen. It is an
**exception, not a printed warning**: R2-3063's entire finding is that every
instrument printed a pass and nobody was told the bed was wrong.

Selftest, and every control observed to fail first:

```
S1  gate refuses FILM_POSE_FRAMES                                      PASS
S2  gate accepts FILM_POSE_FRAMES + MOTION_POSE_FRAMES                 PASS
S3  gate refuses 100 sharp frames  (the failure is "all sharp", not
    "too few" — R2-1036 used four and a hundred must fail too)         PASS
S4  every motion frame is >=160 px streak AND >=40% road coverage      PASS
S5  drop-in reproduces the four original poses byte-for-byte, adds 3   PASS
S6  every motion frame agrees between authoring and DELIVERED camera   PASS
    control  beat-1 frames rejected by the same test: [100,300,500,700]
>> STAGE RESULT: MOTION_POSE_OK
```

**S1 is the only one that matters.** A gate that passed `FILM_POSE_FRAMES` would
have licensed the asphalt and is worth nothing.

### The one-line landing, for whoever holds `world/build_surface.py`

That file is another agent's lease all session, so the repair is written as a
drop-in rather than applied:

```python
from tools.r2_3241_motion_pose import film_pose_defs_with_motion
def _film_pose_defs(frames=None):
    return film_pose_defs_with_motion(frames)
```

S5 checks the reproduction against the real `_film_pose_defs`: identical
signature, identical return shape, identical `dof.json` lookup, the four
original poses byte-for-byte, three cameras appended. The motion cameras are
named `motionpose_f####` and the sharp ones keep `filmpose_f####`, **because the
whole defect was two beds being indistinguishable in the record.** Cost: three
extra cameras in the same blend, in the same broker job.

---

## R2-3247 — WHICH VERDICTS ACTUALLY CHANGE

**None, except the one already known.**

| verdict | exposed? | changes? |
|---|---|---|
| **R2-1031 / R2-1036 / R2-1038 asphalt octave & A/B** | yes, maximally | **already overturned by R2-3062.** This task adds that the collapse is confined to <30 m and that the kerb in the same frames does not move |
| R2-3065's new 45–160 mm octave | yes — authored after the class was named, not yet re-verified under 245 px | **unresolved by choice.** Its arms are in flight under another agent. `assert_motion_case` is what should gate its judgement |
| R2-1379 / R2-1293 / R2-633 item relief verdicts (`item_gate` witness still) | 89 of 434 items | **no change except on the road.** The exposed 89 are led without exception by road-surface items; everything else peaks below the floor |
| R2-016 "grass reads as a fuzzy carpet" | 2.7–4.0x | **not reproduced** — 0 % of grass tiles empty, incl. at ≥160 px. Weak (n=19), offered as weak |
| R2-1124 / R2-1342 cypress & tree tiering | 1.0–1.7x | **no change.** Several trees have ratio exactly 1.0 |
| R2-366 / R2-375 / R2-378 apron & roof paving at f2978 | **no** | **confirmed defensible.** Beat 6's whole camera peaks at 9.8 px. `ARCH_Paving_Forecourt` measures 1.0x — the one big surface in the film with no exposure at all |
| R2-242 / R2-406 driver containment at f2632 (2,391 px) | **immune** | containment is geometric. Its *legibility* half ("208 px of gold") is exposed and is **not checked** — see below |
| R2-014 / R2-015 / R2-011 `macro_audit` car surfaces | beat 1 ≤ 127 px | **no change.** Beat 1 never reaches the floor by either instrument |
| R2-1146 CarbonFibre weave at 0.87 px | n/a | untouched. 0.87 px is under the proxy's blind band and under everything else's |

---

## R2-3248 — WHAT I DID NOT CHECK, EXPLICITLY

1. **The 0–8 px @4K band.** The proxy is blind there and so is every number
   above. Nothing here claims absence from it.
2. **The car and the driver.** Not in the world point cloud — `screen_presence.py`
   says so in its own docstring — and not in the ground ray join. So R2-522/524/
   525/526/527 (paint albedo, twill weave), R2-1146 (carbon weave) and the
   legibility half of R2-406 are **unmeasured by me**. The car is the one subject
   with its own motion on top of the camera's, so its true smear is *higher* than
   any figure in this document. **If anything here justifies a targeted 4K frame,
   it is the car at f2632, and I have not asked for one because I have no proxy
   evidence to point at.**
3. **Barriers and the transit walls.** `BR_Armco_*`, `BR_FenceStruct_*`,
   `BR_TecPro_*` and `BR_Transit_NorthWall` returned `TILES_NO_OWNERSHIP` — too
   few cloud points to win a tile vote. Not checked, in either direction.
4. **Beats 1 and 2 on the ground.** The ray join samples f865–f2955 and has
   **zero** frames in beat 1 or 2, and only 6 and 4 in beats 3 and 4. Their
   immunity above rests on the streak distribution, not on tile pixels — it is
   an argument that the defect *cannot* reach them, not a measurement that it
   did not.
5. **`ARCH_PitBuilding_*` and the grandstands in the near field.** Their owned
   tiles are all beyond 30 m, so the C5 near-field blindness applies to them too.
6. **The 470 objects and 345 items below the reviewed head.** Ranked, in
   `work/r23241/exposure_rank.json`, not individually examined.
7. **`docs/screen_presence*.json` itself.** R2-3243 shows it is stale against the
   delivered camera for the whole of beat 1. I resweeped it for my own use and
   did **not** touch the shipped file or anything downstream of it. **Somebody
   who owns the item tiering needs to decide what that does to beat 1's tiers.**

---

## R2-3249 — SPEND

**Nothing.** No render, no rental, no 4K frame. Credit is $[redacted], unchanged. The
entire finding came off `work/r22161_proxy/`, `work/r22881/scan.npz` and
`work/r23061/`, all already paid for. **No targeted 4K frame is requested**: the
proxy resolved every candidate it could reach, and the one thing it cannot reach
(the car) has no proxy-level evidence to justify a spend against.
