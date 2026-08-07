# STAGING — R2-731 … R2-760

Findings staged here, not in `DEFECT-LOG-R2.md`. Everything below is a source
change already landed in `/home/zany/f1-round2`, or a declined defect with its
reason.

---

## R2-731 — the three occlusions: one closed in source, one is not a defect, and one is a rejected fix

**Scope.** The occlusion block handed over three items out of R2-651…R2-666:
the bridge blackout (f2180-2191), the beat-4 pit-building blackout (f1114-1116),
and `BR_FenceMesh_L03` over the film's last three frames. The previous agent's
raycast work was taken as given and not re-derived; `render/r2651/occlusion.json`
is its output and every number below is measured against that baseline.

**Outcome in one line each.**

| | verdict |
|---|---|
| bridge, f2180-2191 | **the specified fix is rejected** — `PONT_S = 2460` gives **25** blocked frames against 12, confirmed by raycast. No station clears it, and it is geometry rather than an unlucky search. Reverted; see R2-732. |
| bridge, the camera lever | **a verified candidate, not landed.** The camera crosses the bridge 5.1 m ABOVE the soffit and 29 m outboard; `circuit_spec.md` §10 says it "threads under it at ~5 m altitude". Putting it where the spec says takes the blackout to **zero**, on a 6 m x 5 m plateau. See R2-738. |
| beat 4, f1113-1118 | **closed.** 0 of 134 frames occluded at all analytically; the raycast confirms it with architecture, and again with dressing in the world. See R2-733. |
| last three frames | **not a defect.** The car is `in_frame: false`, 69° off the camera axis, for the last 145 frames. See R2-734. The L03 intrusion it cross-references is separately re-measured and clear in R2-735. |
| `DR_BridgeBanners` | **adds nothing.** Two frames, f2187-2188, both already blocked by the bridge behind them. R2-664's f2193-2196 tail is withdrawn — the proxy over-read by five frames. See R2-736 pass 3. |

### The baseline, restated from the raycast rather than from prose

`render/r2651/occlusion.json`, 1,922 frames over beats 4/5/6. Its
`modules_built` lists `surface, barriers, architecture, terrain`, but its
`passes` is `[["architecture", 220]]` — **the only cast it recorded was the one
after architecture**, so the baseline is blind to terrain and to dressing even
though terrain was built. That is stated here because it makes the comparison
below exact: pass 1 of the re-verification is the same cast against the same
module set. Rows with `occ_frac_front == 1.0`:

```
f1114-1116   ARCH_PitBuilding_Shell    9.3-12.4 m   solid    in_frame TRUE
f2180        ARCH_PontPlongee          26.4 m       fence    in_frame TRUE
f2181-2191   ARCH_PontPlongee          30-55 m      solid    in_frame TRUE
f2976-2978   BR_FenceMesh_L03          982-985 m    fence    in_frame FALSE   <--
```

That last column is the whole of finding 3 and it is dealt with below.

---

## R2-732 — THE BRIDGE MOVE IS REJECTED. `PONT_S = 2460` makes the blackout TWICE AS BAD, and no station closes it

**The brief's instruction was "`PONT_S = 2410 -> 2460` was tested against all of
beat 5 and closes it. Land it." It was landed, re-verified, and reverted.**

### What the raycast says, on the same instrument that found the defect

`tools/r2651_occlusion_sweep.py`, `--mods surface,barriers,architecture`,
beats 4/5/6, both runs built from source on this box:

```
PONT_S      fully-blocked frames (occ_frac_front = 1.0, in_frame)   occluder distance
2410        f2180 fence + f2181-2191 solid          12              26 - 55 m
2460        f2196, f2203-2230 solid                 25              32 - 66 m
```

`render/r2651/occlusion.json` (2410) and
`render/r2731/occ_STALE_s2460_firstannexe.json` (2460). f2180-2193 do clear
exactly as predicted. A new, longer, closer blackout opens 15 frames later.

### Why R2-660's sweep said zero, and it is a known shape

`tools/r2651_pont_sightline.py` reconstructs this bridge as **four horizontal
bands** — girders, deck slab, parapet, mesh screen — spanning u = −15…+15 from
the soffit up. Its own docstring says so. `build_architecture.build_bridges`
also emits, on **each** side:

```
abutment        x ±4.2   |u| 12.8 .. 18.0   z (zr − 6.0) .. soffit
precast pad     x ±5.0   |u| 12.0 .. 19.0   z (zr − 6.0) .. (ground + 0.10)
5 wing walls                out to |u| 26.6  z (zr − 4.0) .. soffit − 1.1k
```

The abutment alone is a **12.8 m tall, 5.2 m deep block of concrete**. A
sightline that passes outboard of the span and *below* the deck is stopped dead
by it, and the four-band model cannot see that at all. At 2410 the sweep crosses
|u| = 13…20 at z ≈ 9-10 m — over the abutment tops. At 2460 it crosses the same
lateral band lower, and goes through them.

> This is R2-664's own v1 failure in a new costume: **a model that omits the
> thing that actually blocks returns a confident zero.** R2-664 recorded that
> lesson about the road being in the corridor and then the recommendation it
> carried forward was made on a model with no abutments.

### The replacement instrument, and why it may be trusted

`tools/r2731_pont_full_sightline.py` models every box `build_bridges` emits and
samples the car with `r2651_occlusion_sweep.py`'s own 58 points. `--selftest`
reproduces **both** raycasts exactly:

```
s = 2410   raycast f2181-2191 (11)   model f2181-2191 (11)   PASS
s = 2460   raycast f2196-2227 (25)   model f2196-2227 (25)   PASS
```

The second is the load-bearing one: it reproduces a defect it did not predict,
at a station someone else chose, from the same code.

*(Its first draft did not, and the reason is worth keeping: it sampled the car
on an 18-point grid lifted by the 0.34 m ride height that
`r2651_occlusion_sweep.py` **records and does not use** — `RIDE_H = 0.340 #
recorded, not used: the box is the hull`. A cheap prediction that samples the
subject differently from the authority it predicts is not comparable to it. With
the sweep's own 58 points it agrees to the frame at two stations.)*

### No station clears it, over the whole of beat 5

`--sweep`, frames 1191-2714, every station 2000-3200:

```
station  2000 2100 2200 2300 2400 2500 2600 2700 2800 2900 3000 3100 3200
blocked     4    5    5    8   10   20   62   14    8    4    0    0    0
```

and at 10 m resolution through the authored neighbourhood, 2300-2700, the
minimum is **8 frames at 2300** against 11 at 2410. The zeros at 3000+ are 600 m
away, on the pit approach where La Passerelle already stands; they are not a
station for *this* bridge.

### It is geometry, not an unlucky search

The sightline sweeps from **high and outboard** to **low and central**: it must
end at the car, on the road, at u ≈ 0 and z ≈ 1 m. Any slab spanning the track
therefore has its solid band crossed on every pass. To miss it a frame's ray
would have to be above the parapet at |u| = 12.8 *and* below the soffit for the
rest — but the abutment tops out at the soffit over |u| = 12.8…18, so the ray
must be *above* the soffit there and *below* it a moment later. That window is
~1.3 m of ray height, and the ray descends ~0.25 m per frame, so it can hold for
a handful of frames and never for the whole pass.

**Station is not a lever for this defect.** Neither, on its own, is height.

### The measured menu, for whoever owns the circuit's design

All at s = 2410 unless stated, fully-blocked frames, full-geometry model:

| change | blocked | note |
|---|---:|---|
| **shipped** | **11** solid + 1 fence | f2180-2191 |
| concrete parapet → kerb + full-height mesh screen | **8** | moves nothing; the 1.10 m upstand stops being concrete, the solid band goes 2.72 → 1.87 m, and the frames it gives back become *seen through mesh* rather than blacked out |
| soffit 6.80 → 9.80 | **4** | a 3 m raise; changes what the structure is |
| both | **4** | the raise dominates |
| s = 2650, soffit 8.80 | **1** | a 240 m move **and** a 2 m raise |
| s = 2700, soffit ≥ 9.80 | **0** | a 290 m move and a 3 m raise |

**Nothing on this list was landed.** The first row is what ships. The second is
cheap, moves no geometry, and is arguably the more standard detail for a circuit
overbridge — but it is a visible change to the circuit's signature structure and
it does not close the defect, so it is a proposal and not a change. The last two
close it and would delete the beat the bridge exists for: `circuit_spec.md` §10
puts it "**145 m before the doppler hover station**… so the car bursts out from
under a bridge straight into the doppler pass", and at 2700 there is no bridge
before the hover at all.

**The one lever not on this list is the camera**, and R2-660 already said so:
*"Only a change to the camera path could move it."* That is now the whole of the
remaining option space, and it is not this task's to spend.

### What WAS landed on the bridge, and it is worth keeping either way

`build_dressing.bridge_banner_sites()` read:

```python
hdg  = math.radians(295.4)
ox, oy = -617.56, 94.75
soff = 3.913 + 6.80
```

Those three are `WC.centreline(2410)` and `WC.elevation_c(2410)` to the
millimetre — verified, not assumed:

```
WC.centreline(2410)  -> (-617.563, 94.750), heading 295.400 deg
WC.elevation_c(2410) =  3.9129
```

a hand-taken snapshot of `PONT_S`, in a second module, with no link back.
R2-664 wrote the consequence down in advance: *"any placement move must carry
the banners with it; they are not part of build_architecture's bridge and will
not follow PONT_S on their own."* During the hour `PONT_S` was 2460 that was
demonstrated, not argued: with the literals in place the banners stayed at 2410,
and after the change they moved to `(-597.489, 52.474, 11.260)` and
`(-594.744, 46.693, 11.260)`, centred on `centreline(2460)`.

`PONT_S` is now module-level in `build_architecture.py` and
`bridge_banner_sites()` evaluates the contract at it. Measured back at 2410 in
Blender: the banners land at `(-618.936, 97.641, 11.413)` and
`(-616.191, 91.860, 11.413)` — **the shipped positions to 4 mm**, the residual
being the decimals the literal dropped. Nothing in the film moves; the copy is
gone.

The import is deliberately **not** guarded. A `try/except` fallback here would
mean the module silently keeps building at a station the bridge no longer
occupies, which is the failure this exists to prevent.

### Files touched and then reverted, listed so the revert can be audited

`world/build_architecture.py` (`PONT_S`), `docs/circuit_spec.json`
(`plunge_bridge_design.s` + an `s_note` recording the finding),
`tools/circuit/emit.py` (the generator that writes it), `docs/circuit_spec.md`
(four prose statements), `world/items/pont_girder.py` (`S_STATION` and its
derived figures), `world/items/pont_deck_slab.py` (a comment). All are back at
2410 with the reason recorded in place; the `s_note` and the `PONT_S` comment
block are the only net additions.

### One thing carried forward, not fixed here

`world/items/pont_girder.py` reads `SOFFIT_Z = 6.800` as an **absolute world z**
while `build_architecture` builds the soffit at `elevation_c(PONT_S) + 6.80`,
i.e. **relative to the road**. That predates this work; the item is on HOLD
(`LOCAL_FRAME` / `SUPERSEDE_WELDED` in `world/items/PLACEMENT.json`) so nothing
in the film is built from it, and the two conventions only diverge if the
station moves. **Whoever unblocks that row has to reconcile them.**
`world/items/pont_deck_slab.py` (gate `ITEM_REJECTED`, also on HOLD) still
carries `s = 2410` prose; its `S_STATION` re-exports `pont_girder`'s and follows.

---

## R2-733 — THE PIT BUILDING. Closed. The whole beat-4 blackout is the roof and what stands on it, at one corner of a 320 m frontage

**Landed.** R2-666 named `ARCH_PitBuilding_Shell`. That object is 320 m long and
some thousands of boxes, so the name was not yet something anyone could fix.

### The instrument: `tools/r2731_pit_sightline.py`

Reconstructs the shell from `build_architecture.py`'s own module constants and
intersects the camera-to-car segment box by box — the technique
`r2651_pont_sightline.py` used on the bridge, with the correction that broke that
one: it enumerates **every** box the builder emits, and it samples the car with
`r2651_occlusion_sweep.py`'s **own 58 points**, not a convenient grid.

Its controls are stated as such. With the pre-R2-731 geometry it must reproduce
f1114-1116 wholly blocked and f1113/1117/1118 partial — R2-666's own
`occ_frac_front` — and must clear f1100 and f1130. It does, plus four slab-test
controls including "a box beyond the far end of the segment does not occlude",
which is the depth test and the entire point. It also reads the annexe constants
**out of `build_architecture.py`** rather than restating them, because a tool
that carries its own copy of the change it is checking is checking itself.

### What the defect actually is

Over f1113-1118 the camera crosses the pit complex diagonally at z = 15.7 →
16.2 m and the sightline to a car 42 m away clips the **south-west corner of the
roof**. It never penetrates more than 8.8 m into a 320 m building and never
deeper than y = 25.13 into a 17 m-deep plan.

Per box — the box's top against the lowest the sightline gets over that box's own
footprint:

```
box               top     ceiling
parapet_front    12.00      9.70    BLOCKS by 2.30 m
core_W           12.70     11.42    BLOCKS by 1.28
roof_deck        10.96      9.70    BLOCKS by 1.26
roof_seam_0..7   11.02   9.71-10.84 BLOCKS
roof_lap_0       10.96     10.57    BLOCKS by 0.39
upper_wall       10.90     10.54    BLOCKS by 0.36
L1_spandrel      10.40     10.60    clear by 0.20
canopy_fascia     6.46     10.00    clear
ff_slab           6.40     10.10    clear
flank_W          10.90     13.42    clear
```

**Everything at or below the L1 glazing head at 10.40 is already clear and
everything above it is not.** The garage frontage, the pit-lane canopy, the
piers, the doors and the glazed band are innocent. The occluder is the roof and
what stands on it.

### The fix: the west end is an annexe

West of `PB_ANNEXE_X = -218.0` the building keeps its plan **exactly** and loses
a level. Its glazed band becomes a normal **3.00 m** storey over the first floor
where the main block is a **4.00 m** hospitality volume; its roof deck bears on
that head at 9.40; it stops **on** the façade line at y = 21.10 instead of
oversailing to 20.40; and it carries a 0.18 m eaves fascia in place of a 1.10 m
parapet. The W stair core, which marks the joint, rises 1.00 m above the annexe
roof (top 10.40) instead of 0.70 m above the main parapet (top 12.70). The rear
and west walls stop at 10.30 and are that roof's upstand.

**Nothing is stood back from the track.** Footprint, canopy, garage frontage,
piers, doors and pit lane are untouched, so the near-field geometry that sells
the speed still passes the lens at the same distance. What comes off is height,
at one corner, over 8 % of a 320 m frontage — and it reads as a subsidiary end
block rather than as a chopped-off main one.

### Why the step is at −218.0, and why the level and not just the station

The sweep over f1105-1135 is clean — **0 fully blocked and 0 partially
occluded** — for every step station from −235.0 eastward, and stays clean at
−234, −233, −232, −230, −228, −224 and −218. **A 17 m plateau, not a knife
edge** — the standard R2-660 set for the bridge and then did not meet. −218.0 is
the bay-1/bay-2 joint, the only structural line inside the plateau.

The station alone is not enough: with the annexe roof left at the main block's
10.90 the same sweep still leaves 3 partial frames at `frac 0.389` at every
station tested. **The level is doing the work.**

Over the whole of beat 4, f1057-1190: **0 of 134 frames occluded at all.**

### 9.40 and not 10.40, and the reason is an instrument correction

The first draft put the annexe deck on the main block's L1 head at 10.40. That
clears the blackout, and it was measured again after the tool was corrected to
sample the car exactly as the sweep does — 58 points at the box's own z, **not**
lifted by the 0.34 m ride height the sweep records and does not use
(`RIDE_H = 0.340 # recorded, not used: the box is the hull`). The un-lifted car
sits 0.34 m lower, the sightline with it, and the margins collapsed:

```
annexe eaves fascia   10.58   ceiling 10.54   -> BLOCKED
annexe roof deck      10.46   ceiling 10.54   ->  0.08 m
W core (top 11.40)            ceiling 11.42   ->  0.02 m
```

**0.02 m is not a clearance, it is a coin toss that landed.** At 9.40, measured
per box over f1110-1121 with the same 58 samples — the twelve tightest, worst
first, and there is nothing negative on the list:

```
box                     top    ceiling   margin
annexe_fascia          9.58     10.52    +0.94 m   <- the tightest thing there is
core_W                10.40     11.42    +1.02
roof_deck|annexe       9.46     10.52    +1.06
roof_lap_0|annexe      9.46     10.56    +1.10
L1_spandrel|annexe     9.40     10.61    +1.21
roof_seam_0|annexe     9.52     10.73    +1.22
roof_seam_1..6|annexe  9.52   10.83-11.58  +1.31 .. +2.07
```

`work/r2731/margins.txt`. **The worst margin in the whole annexe is 0.94 m,
against 0.02 m in the draft it replaced** — a factor of 47, for one storey of
height at one corner.

**The 10.40 draft was independently confirmed by the raycast before it was
replaced**, which is why the correction can be trusted rather than argued: the
run at those constants came back with f1114-1118 fully cleared and f1113 down
from `0.226` to `0.032` — 2 of 58 samples, against the analytic tool's predicted
3. Two instruments, one frame, one sample apart.

### Files changed — all in `world/build_architecture.py`

* `PB_ANNEXE_X`, `PB_Z_ANNEXE`, `PB_ANNEXE_EAVE_Y`, `PB_ANNEXE_FASCIA`,
  `PB_ANNEXE_CORE_UP` declared beside the other `PB_*` constants
* rear wall and west flank stop at the roof they enclose, 0.90 m proud of it
* the L1 spandrel band and the mullion/glass/spandrel loop take the annexe's own
  head west of the step
* the L1-head band (`PB_Z_L1` → `PB_Z_RF`) built only east of the step
* roof deck, standing seams and sheet laps split at the step
* a step face — the main block's west gable — standing on the annexe roof
* front parapet east of the step; an eaves fascia west of it
* `_core()` caps a core standing wholly on the annexe: **a core rises above its
  own roof**
* `_roof_plant()` takes the deck it stands on; the main-roof stretches now start
  at the step, and the annexe gets its own run **on its own seed** so the main
  roof's plant layout is bit-identical to before this change

---

## R2-734 — THE LAST THREE FRAMES ARE NOT A DEFECT. The car is not in the shot, and the raycast's own row says so

**Declined, with the measurement.**

R2-666 reported `BR_FenceMesh_L03` covering the car completely on f2976-2978.
The `occ_frac_front = 1.000` is real. **The same rows carry
`in_frame: false` and `in_frame_n: 0`, and `cx = 6.03, 5.98, 5.92`** — the car
projects six screen widths to the right of frame.

It is out of frame for the **whole tail of beat 6**, not just the last three
frames: `in_frame` is true through f2833 and false on **every frame from f2834
to f2978** — one unbroken run of 145 frames, 6.0 s. f2900 is already at
`cx = 3.588`.

**Checked independently of the tool, because a tool agreeing with itself is not
evidence.** Reprojecting from `world/camera_rig_path.json` and
`world/car_anim_measured.json` by hand — camera quaternion, 36 mm sensor, the
keyed focal:

```
frame   lens    dist      angle off the camera axis    half-HFOV
f2714   24.00     85.0 m           0.52 deg            36.87 deg   <- on axis
f2850   18.81    540.7 m          77.76 deg            43.74 deg
f2900   38.97    730.9 m          70.82 deg            24.79 deg
f2950   62.30    912.0 m          70.34 deg            16.11 deg
f2978   74.00   1000.1 m          69.26 deg            13.67 deg
```

At f2978 the car is **69.26° off axis inside a 13.67° half-angle**. The
hand-computed screen x is 5.917 against the sweep's 5.919 — two independent
projections, three decimals apart.

**So there is nothing between the lens and the subject, because the subject is
not in the picture.** The camera has come to rest on its 140 m hold
(`HOLD_W = (594.19, 16.05, 140.0)`) at 74 mm and the car has left frame. An
`occ_frac` computed along a ray fired 69° outside the frustum is a number about
a line, not about a shot.

**The sweep already knew.** `runs_of()`, which `summarise()` calls to build
every window it reports, opens a run only on
`hot = r["in_frame"] and r[key] >= thr` (`tools/r2651_occlusion_sweep.py:840`).
The tool's own summary would never have raised these frames. The finding came
from reading the per-frame array past the guard the tool puts there.

> The general shape, which is this project's most repeated failure and is worth
> restating: **a metric computed on a row whose precondition is false is not a
> weak result, it is not a result.** `in_frame` is on the same row as
> `occ_frac_front`, one field away.

**One thing this does NOT excuse.** R2-709 reasoned about the closing wide as if
the car were in it — *"the closing wide puts the car at ~1,000 m, where the whole
car subtends roughly 16 px at 4K and a helmet is comfortably sub-pixel — so zero
may be geometry rather than defect"* — and used that to keep `DRV_ = 0 px` open
rather than closing it. The car is not at 16 px in the closing wide; it is at 0
px, because it is not in the frame. **`DRV_` reading zero on f2978 is fully
explained without any statement about the driver**, and R2-709's instruction to
re-measure at a frame where the driver is known to read (e.g. f800) is the right
one and is now the *only* thing that can settle it.

---

## R2-735 — the L03 intrusion: three placement reports, two answers, and the newest one is the stale one

The other half of R2-666's cross-reference. Independent of R2-734, because
"is this fence on the racing surface" is a real question whatever the closing
frame does.

| file | mtime | L03 row |
|---|---|---|
| `docs/placement_report.json` | Jul 29 00:53 | 7.6054 m |
| `docs/placement_depth.json` | Jul 29 00:48 | 7.1054 m at s = 926.3 |
| `docs/placement_report_r2.json` | Jul 29 03:27 | **absent** — 2 violations, both `ARCH_*` edge-family |
| `docs/placement_report_cam34.json` | **Aug 2 01:01** | 7.6054 m |
| `docs/placement_after_46.json` | Aug 2 06:49 | **absent** — total 0 |

`placement_report_cam34.json` is the newest file that still reports it, and its
L03 rows are **byte-identical** to the July 29 pre-fix run, `at_world` included.
That is a stale reading carried forward, not a fresh measurement.

**The cause was fixed and it is possible to check that from source without
building anything.** R2-036 found `barrier_offset` stepping 51.99 m in one metre
— a `1e6` sentinel surviving a 41-sample box filter — and shipped the fix in
`world_contract` 1.1.0. On the shipped 1.2.1:

```
   s    half_width   barrier_offset(-1)
 900       7.173          41.642
 925       7.381          41.915
 926       7.385          41.921
 950       7.500          42.135
```

The barrier line on the L side through the whole L03 stretch is at ~42 m against
a 7.4 m half-width. There is no mechanism left by which the fence is on the road.

**Re-measured on built geometry** — `tools/r2731_fence_l03_audit.py`, which
builds `barriers` only (no architecture, no dressing, no farm) and applies
R2-017's corrected definition, `intrusion = half_width(s) − |u|` per vertex,
with an on-road and an off-road synthetic control and an `su_to_world` /
`world_su` round-trip check.

```
control  roundtrip   max (s,u) error 0.000000 m over 41 points, s 880-980
control  on-road     a facet planted at u = 0 reads +7.392 = half_width exactly
control  off-road    the same facet at |u| = hw + 20 reads -20.000 exactly

BR_FenceMesh_L03      worst intrusion  -6.7561 m   at s = 936.2, u = +14.231   (half_width 7.474)
BR_FenceStruct_L03    worst intrusion  -6.7481 m   at s = 936.2, u = +14.223   (half_width 7.474)
BR_FenceMesh_L04      worst intrusion -15.0904 m   at s = 1106.0, u = +22.090
BR_FenceStruct_L04    worst intrusion -15.0852 m   at s = 1106.0, u = +22.085
BR_Armco_L03          worst intrusion  -6.4490 m   at s = 1025.3, u = +13.949

>> STAGE RESULT: L03_CLEAR
```

**`BR_FenceMesh_L03` stands 6.76 m OUTSIDE the racing surface at its worst
vertex**, against +7.105 m inside when R2-017 measured it. So does L04, and so
does the Armco beside it. `render/r2731/fence_l03.json`.

**The intrusion is closed, and it was closed by R2-036, not by anything here.**
Nothing was changed in `build_barriers` for this. What this entry establishes is
that the newest report saying otherwise is stale, and that the closure survives
in the current source rather than only in a July blend — which is what R2-666
asked for when it said the closing frame is a witness for this defect.

> The closing frame is **not** a witness for it, for the reason in R2-734: the
> car is not in that frame. The two findings are independent, and the
> cross-reference R2-666 drew between them does not hold in either direction —
> the fence is not on the road, and the frame does not contain the car.

---

## R2-736 — re-verification against the assembled world

Everything below is `tools/r2651_occlusion_sweep.py` — the instrument that found
the defects — re-run from source on this box, after the changes. Its 22 controls
pass on every run, including the three that matter here: a plane BEHIND the car
does not occlude (the depth test), a ray through a bridge's opening hits nothing,
and a grazing ray is not occluded by the road it is aimed at.

The farm is down, so these are local builds. That is why they are split by
module set rather than run as one 7 GB scene.

### Pass 1 — `surface + barriers + architecture`, beats 4/5/6, 1,922 frames

`render/r2731/occ_final_sabt.json` against `render/r2651/occlusion.json`.

**Six frames changed out of 1,922. All six improved. Nothing anywhere got
worse.**

```
f1113   0.226  ARCH_PitBuilding_Shell  ->  0.000  -
f1114   1.000  ARCH_PitBuilding_Shell  ->  0.000  -
f1115   1.000  ARCH_PitBuilding_Shell  ->  0.000  -
f1116   1.000  ARCH_PitBuilding_Shell  ->  0.000  -
f1117   0.871  ARCH_PitBuilding_Shell  ->  0.000  -
f1118   0.323  ARCH_PitBuilding_Shell  ->  0.000  -
```

The three-frame blackout and the three partial frames around it are gone
together. The remaining fully-blocked frames in the whole of beats 4/5/6 are
`ARCH_PontPlongee` at f2180-2191 — **bit-identical to the baseline**, which is
the revert verifying itself.

> "A fix that clears one occluder and creates another is not a fix." Measured:
> the diff is six rows long and every row is a reduction. That is the check, and
> it is needed — the annexe is **not** purely subtractive. It adds two boxes: a
> step face (the main block's west gable, now standing on the annexe roof) and
> an eaves fascia. Both are inside the volume the removed parapet and roof
> overhang used to occupy, which is an argument; the diff is the evidence.

### Pass 2 — `+ terrain`, ABANDONED, and the reason is a cost the farm should carry

`build_terrain` completed in 1,035 s: **28,535 objects, 1,027 unique meshes,
33.3 M library triangles and 15.07 BILLION evaluated triangles** (2,984,718 grass
clumps, 24,646 woodland trees, 1.6 M grit pieces). The cast against that BVH did
not complete its first 250-frame progress line in fifteen minutes of wall clock,
against 13 s for the same 250 frames without terrain. It was stopped so the
dressing and items passes could run, and `occ_final_sabt.json` keeps the
architecture pass, which is complete and is the one comparable to the baseline.

**The R2-651 baseline never got this pass either** — its `passes` records only
`architecture` — so no occlusion measurement in this project has ever had
vegetation in the world. That is a real gap and it is the one thing here worth
spending farm money on: a single run with all six modules, one self-consistent
world, no splitting by module set to fit 11 GB. **Estimated ~1 h of one card,
about $0.60 of the $73.33** — under 1 %.

It cannot un-clear anything already cleared: the sweep min-combines passes and
only ever takes a NEARER hit, so a later module can add an occluder and never
remove one. Its only possible finding is a vegetation occluder nobody has
looked for.

### Pass 3 — `barriers + architecture + dressing`, DONE. The banners add nothing, and R2-664's proxy over-read by five frames

`render/r2731/occ_final_dressing.json`, log `work/r2731/runB2.log`,
`>> STAGE RESULT: OCC_OK`, all 22 controls passed.

This is the one the brief singled out: **`dressing` and `items` were absent from
the baseline, so `DR_BridgeBanners` was never tested**, and R2-664's 1 m
occupancy proxy put the banners in the corridor **out to f2196** — four frames
past the bridge's own window.

**Measured, with dressing in the world:**

```
=== RUNS, WHOLLY HIDDEN (>=95%) ===
  f2180-2186   7 fr  0.29 s   ARCH_PontPlongee  A_MeshDark    fence   31.8 m
  f2187-2188   2 fr  0.08 s   DR_BridgeBanners  DR_Print      solid   44.5 m
  f2189-2191   3 fr  0.12 s   ARCH_PontPlongee  A_SteelPaint  solid   51.8 m
```

**The banners own two frames, f2187 and f2188, and both were already blocked by
the bridge behind them.** The fully-blocked set with dressing is the same twelve
frames as without it, f2180-2191. Against the barriers+architecture pass:
**0 frames worse anywhere in beats 4/5/6.**

**Beat 4 with dressing in the world: no occlusion at all, any fraction.** The
annexe holds with the trackside dressing built.

> R2-664's f2193-2196 tail is **withdrawn**. The proxy over-read by five frames,
> which is exactly the failure it warned about in its own instrument caution —
> *"a systematic geometric over-read is contiguous too."* It was right about the
> mechanism and wrong about the extent, and the raycast is what decides.

The other thing this settles: **the banners did not need to move**, because the
bridge did not. `bridge_banner_sites()` now evaluates the contract at
`build_architecture.PONT_S` and returns the shipped positions to 4 mm, so
nothing about them changed in this rebuild — but the copy that would have
stranded them is gone.

### Pass 4 — `barriers + architecture + items`, IN FLIGHT

`work/r2731/runB3.log` -> `render/r2731/occ_final_items.json`. Closes the gap
named below.

### What is still not covered

`items` was not built in any of these passes. `world/items/PLACEMENT.json`
carries 42 rows and exactly **four** are at `state: PLACE` —
`catch_fence_post`, `crew_figure`, `spectator_seated`, `timing_stand`; the other
38 are on HOLD and build nothing. R2-709 measured all four as non-zero pixels in
a delivered 4K frame, `SPECX_` alone at 0.82 % of it.

**None of the four was in the corridor in this sweep, because none of them was
built.** Two could plausibly matter: `catch_fence_post` (which would land in the
fence channel, not the solid one) and `timing_stand`. That is a stated gap, not
a clean bill — and it is a cheap one to close, since `--mods
barriers,architecture,items` needs neither terrain nor dressing.

---

## R2-737 — THE LENS RETUNE CANDIDATE IS BUILT ON A SUPERSEDED PATH, and it makes the bridge blackout worse to look at without changing a single blocked frame

Checked before anything was moved, as instructed.

`render/film14_path_R2581B_ramp_RETUNED_CANDIDATE.json` says of itself: *"Lens
only; p and q identical to `film14_path.json`. Support f1997-f2244."* Both halves
of that are true, and the second half is the trap.

| comparison | max \|Δp\| | max \|Δq\| | max \|Δlens\| |
|---|---:|---:|---:|
| candidate vs `film14_path.json` | **0.000000 m** | **0.00000000** | 57.502 mm |
| `film14_path.json` vs the LIVE `world/camera_rig_path.json` | **8.863 m** | 1.687 | 23.0 mm |
| candidate vs the live rig | 8.863 m | 1.687 | 57.502 mm |

So the candidate is lens-only **relative to a path that is not the one in the
film**. Scoped by beat, the difference is entirely beat 1:

```
beat 1   f1-792       max |Δp| 8.863 m   max |Δq| 1.687      max |Δlens| 23.0
beat 5   f1191-2714   max |Δp| 0.000 m   max |Δq| 0.000001   max |Δlens| 0.0
beat 6   f2715-2978   max |Δp| 0.000 m   max |Δq| 0.000001   max |Δlens| 0.0
```

**Adopting the file wholesale would revert beat 1's camera by up to 8.9 m.**
Lifting only its lens curve over its declared support f1997-2244 is safe, because
over that range its base agrees with the live path to float noise.

### Does it interact with the bridge occlusion? Not by a frame, and badly by eye

A sightline does not know the focal length, so the retune cannot change **which**
frames are blocked — R2-660 said this and the raycast confirms it (the occlusion
tool uses the lens only for the in-frame test, and every bridge frame is in
frame at both focals). What it changes is how much of the screen the concrete
fills:

```
frame    shipped    retuned    magnification
f2180    83.18 mm   135.78 mm    1.63x
f2190    84.83 mm   142.11 mm    1.68x
f2195    85.00 mm   142.25 mm    1.67x
```

**The retune lands its peak magnification exactly on the blackout.** At f2190 the
delivered frame is already "a concrete parapet"; at 142 mm it is 1.68x more of
one. The retune does not cause the defect and does not deepen it by a frame, but
it is not neutral to it either, and the two should be decided together rather
than separately.

---

## R2-738 — THE CAMERA DOES NOT DO WHAT THE CIRCUIT SPEC SAYS IT DOES, and doing what the spec says clears the bridge to zero

**A finding and a verified candidate. Not landed — see the last section.**

### The spec

`docs/circuit_spec.md` §10, on Le Pont de la Plongée:

> The camera, descending out of the helicopter arc, **threads under it at ~5 m
> altitude** and 300 km/h, 145 m before the doppler hover station, so the car
> bursts out from under a bridge straight into the doppler pass.

### As built

The camera crosses the bridge's plane between f2174 and f2175. Measured in the
bridge's own frame:

```
f2173   along -4.98 m   u -29.26 m   z 15.95 world = 12.04 m over the road
f2174   along -1.53 m   u -29.27 m   z 15.81 world = 11.89 m over the road
f2175   along +1.93 m   u -29.24 m   z 15.66 world = 11.75 m over the road

the soffit is 6.80 m over the road; the clear opening is |u| < 12.80 m
```

**It passes 5.1 m ABOVE the deck soffit and 29.3 m outboard of the centreline.**
It is not under the bridge and it is not over the track. The film's camera and
the circuit's spec describe two different shots, and the raycast has been
measuring the one that is built.

### Putting it where the spec says clears the pass completely

`work/r2731/scratch/` — the camera offset scanned against
`tools/r2731_pont_full_sightline.py`, the model validated against both raycasts.
Occlusion does not depend on the camera's rotation, so these numbers stand
whatever the aim does; the aim is handled below.

**A rigid translation of the camera cannot fix it**, which is worth recording
because it is the obvious thing to try:

```
lateral  du = -16 .. +16 m    11 blocked frames at every value      no effect
along    ds = -16 .. +16 m    10-11 blocked at every value          no effect
vertical dz = +16 .. -1 m     6-11 blocked; raising only SLIDES the window later
         dz = -2.5 .. -3.5    4 blocked, the best a translation can do
```

The floor for a translation is **3 frames**, and the residual is the abutment:
the abutment's top **is** the soffit, so there is no gap between "must be above
6.80 at \|u\| = 12.8-18" and "must be below 6.80 at \|u\| < 12.8". A descending
ray cannot satisfy both, which is the same wall that closed the station search.

**Going through the opening does fix it, and on a plateau.** With the shipped
per-axis windows (`u` on f2145-2200, `z` on f2145-2222), fully-blocked frames:

```
                     lateral offset du (m)
   dz      +16   +18   +19   +20   +21   +22   +24
  -5.0       2     1     1     1     1     1     1
  -6.0       1     0     0     0     0     0     0
  -7.0       1     0     0     0     0     0     0
  -7.5       1     0     0     0     0     0     0
  -8.0       1     0     0     0     0     0     0
  -9.0       1     0     0     0     0     0     0
 -10.0       1     0     0     0     0     0     0
 -11.0       1     0     0     0     0     0     0
```

**A 6 m x 5 m rectangle of exactly zero** — du ∈ [18, 24], dz ∈ [−6, −11] — and
the edge in `du` is soft (a 1 at +16), the edge in `dz` hard only at −5. Not a
knife edge; the standard R2-660 set for the bridge and did not meet.

At the chosen point (du = +20, dz = −7.5) the camera flies the bridge like this:

```
frame   as built                       candidate
f2172   u -29.18   12.19 m over road   u  -9.18    4.69 m over road
f2174   u -29.27   11.89              u  -9.27    4.39     <- the crossing
f2176   u -29.15   11.61              u  -9.15    4.11
f2180   u -28.44   11.06              u  -8.57    3.56
f2186   u -26.91   10.27              u -12.04    2.77
f2192   u -26.09    9.51              u -20.95    2.03     <- swinging back out
```

**4.39 m over the road, 9.3 m off the centreline, 2.4 m under the soffit, inside
the 12.80 m clear opening.** That is `circuit_spec.md` §10's *"threads under it
at ~5 m altitude"*, to within the spec's own tilde — and it was arrived at from
the geometry, before the prose was re-read.

### The cost, stated rather than buried

A windowed offset with separate ramps per axis (u on f2145-2200, z on
f2145-2222, both smootherstep so the correction is C2 in frame):

```
                             as built     candidate
fully blocked frames            11             0
partially occluded              13             0
min height above ground       2.85 m        2.51 m
peak position step            3.680 m/f     3.680 m/f   (unchanged)
peak |acceleration|           0.140 m/f^2   0.358 m/f^2  (2.6x over this stretch)
max deviation from the authored path        21.4 m
```

The seam that matters is untouched: the window closes at f2222 and **f2714/2715
is 492 frames away**, so R2-711's 1.33 % stays exactly as measured.

### Why this is a candidate and not a commit

* **21 m of deviation over ~60 frames changes what the shot looks like**, not
  just what it can see. The `look_at` targets are untouched, so the rig will
  re-aim on the car automatically and the car stays centred — but the
  foreground, the horizon, the relationship to the runoff and the read of the
  bridge itself all change. That is a picture question and it wants eyes on
  frames, not a number.
* **The acceleration triples locally.** It is still an order of magnitude inside
  the rig's own gate (`worst position jump 4.001 m against a 12.0 limit`), and
  the step is unchanged, but it is a real added move.
* The authoritative check is a rig rebuild plus
  `world/camera_rig_continuity.json`, which has not been run — the box has been
  building worlds all session and a rig rebuild needs `beat1_anim.blend`.

**The edit itself is small and reversible.** Beat 5's camera is 316 explicit
keys in `docs/beat_sheet.json` with `world` and `look_at` per key; the change
touches the `world` of roughly eight keys (indices 222-234, f2148-2226) and
**no `look_at` at all**, which is why the aim looks after itself.

> The honest summary: **R2-660 said "only a change to the camera path could move
> it" and treated that as the end of the road. It is the road.** The camera path
> is the lever, the lever has a 4 m x 4 m plateau, and the position it moves to
> is the one the circuit spec already describes.
