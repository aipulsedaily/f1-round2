# build_barriers.py — safety furniture AND the runoff platform

One module, one `build()`, one collection (`R2_Barriers`). Idempotent: it wipes every
datablock named `BR_*` and the whole collection tree before rebuilding, so running it
twice is identical to running it once.

```
/opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P build_barriers.py
... -P build_barriers.py -- --render doppler_fence hairpin --res 1600x900 --samples 128
... -P build_barriers.py -- --list-renders
```

**This module is subordinate to `world/world_contract.py`.** It imports the datum, the
section widths, the runoff programme, the lighting constants and the Beat-4 corridor
extents from there and re-derives none of them. Read `WORLD_CONTRACT.md` first; §"Conformance
to the contract" below is the measured proof that this build meets it, and it names the one
place where this module deliberately departs from the contract and why.

## What it owns

| element | source | where |
|---|---|---|
| W-beam (Armco) barrier: rails, posts, splice bolts | spec §9 "Steel Armco … instanced, dense" | both sides, whole lap |
| TecPro, three rows deep, blue + red cap course | spec §9 runoff table | T1, T4, T12 |
| precast concrete barrier | spec §10.7 pit wall `y = +11.5` | pit straight, north side |
| debris (catch) fence, 3.6 m mesh on 6 m posts at 8 m centres | spec §9 | see "where the fence is" |
| marshal access gates | design decision, 16 of them | listed in `GATE_STATIONS` |
| gravel traps + apex beds | spec §9 runoff table + "gravel bed on the apex side" | 21 beds |
| tarmac runoff | spec §9 runoff table | T1, T3, T8, T10/T11, T15, T4 infield apron |
| **THE RUNOFF PLATFORM — every square metre of ground from `verge_edge(s)` to `platform_edge(s, side)`** | `WORLD_CONTRACT.md` §5 | both sides, whole lap, **221 143 m²** |
| tyre wall, belt-faced | spec §11 Beat 5: "21 mm lens **4 m from the tyre wall**" | T4 infield, apron corridor |
| walled transit corridor + terminals | spec §10.5, contract §6.2 | route t 6 → 96 north, 6 → 90 south |

Explicitly **not** mine: racing surface, kerbs, verge paint, terrain outside the corridor,
vegetation (terrain still scatters it *inside* the corridor, placed on `C.ground_z`),
sun/sky, grandstands, pit building, ad boards, marshal posts, decorative tyre stacks, and
the pit-exit apron surface (contract §7 gives that to `build_architecture`).

---

## What changed at the contract, and why

The assembly review found six modules that each verified themselves in isolation and did
not compose. Three of its five findings landed here.

| the finding | what this module had | what it has now |
|---|---|---|
| **#1 three incompatible ground datums.** 90.1 % of the barrier line had ground > 0.15 m above its own foot, mean 0.72 m against an `ARMCO_TOP` of 1.012 m; 50 555 m² of runoff asphalt and 42 419 m² of gravel with 240 000 stones were entirely under dirt | `ground_z(s, lat) = elevation_c(s) − 0.016·max(0, lat − verge_edge)`. No crown, no banking, and **unsigned in `lat`** — a signature that *cannot* carry banking, because banking is antisymmetric in `u`. Measured against the truth at the verge edge: min −0.680 m, max +0.691 m, p95 \|0.49\| m | `ground_z = C.ground_z(s, u, side)`, **signed**, one function, shared by every builder. Every call site in this file passes `side` |
| **#1, continued.** Terrain paved over the runoff because it assumed the runoff was on top | this module built three disconnected ribbons — a runoff strip, a gravel bed, a 4.5 m shoulder — and left the rest to terrain | **one continuous platform surface per side**, `verge_edge` → `platform_edge`, in four material bands, welded to the datum at both ends. Terrain cuts a hole and welds to `corridor_rim` |
| **#3 the Beat-4 corridor built twice**, 0.5 m apart | `BR_Transit_*` at x 18 → 109.8, isolated "so they can be deleted wholesale if that module builds them too" | the contract gives the corridor to **this module** (`C.CORRIDOR_OWNER`), so `purge()` deletes `C.CORRIDOR_DELETE_NAMES` — object *and* collection — on every build, rather than trusting the assembly order. Rebuilt on `C.transit_wall_span` / `C.transit_wall_point`: asymmetric, north 90.0 m, south 84.0 m, both starting at world x = 21.0 |
| **#4 three modules disagreed on the main straight width** | `build_barriers.half_width` was the only correct one of the five | it is deleted anyway. `half_width = C.half_width`. Being right is not a reason to keep a private copy — the point is that a change moves everybody |
| **#5 terrain calibrated under a light that does not exist** | the test harness lit frames with its own sun (1.45 W, `dust_density` 2.2, an assumed 12.5°) | `setup_test_light` is `C.SUN_*` / `C.SKY_*` verbatim, exposure `C.REFERENCE_EXPOSURE_EXTERIOR` = −3.048 AgX. The verge material is calibrated against `C.lambert_radiance` |
| **`SEAM_DROP = 0.015`**, claimed to "absorb up to 15 mm of disagreement" against a measured 0.69 m — off by 46× | 15 mm drop + a 0.35 m `EDGE_PAD` tuck under the painted verge | **both retired.** See "The two welds" below for what replaces them and what it is actually absorbing |

And one finding the review did not reach, which this module's own probe found: **the
circuit crosses its own corridor**, and `C.barrier_offset` puts T3's outside barrier line
under the S4/T5 racing surface for 400 m. See §4b. It is the one place this build
deliberately departs from the contract, and it is named, measured and handed back.

---

## Round 2 — the three assembly defects this module owned, and what closed each

The integration round fixed the datum. The **assembly** round then found five new defects,
three of them here — and the first was **caused by the previous fix**.

| # | the defect, as measured on the assembled world | what closed it | verified |
|---|---|---|---|
| **1a** | `barrier_offset` reached **−18.80 m on side +1** — 18.8 m past the centreline — over 53 m of lap (s 905–937, 1041–1047), standing `BR_Armco_L03/L04` and `BR_FenceStruct_L03/L04` across the **T4 hairpin braking zone**: 982 of 4 147 sampled verts inside `verge_edge`, mean 1.41 m and **max 4.60 m** above the tarmac. `CAM_T4_INTRUSION.png`. **§4b's own deficit smoothing did this.** | §4b rewritten: slope-limit the **clamped target in clearance-above-the-verge**, blended in only where the ownership cap bites. `offset − verge_edge ≥ 1.000 m` is now a *proof*, asserted at import | `verify_fixes.py` D1: **0 structural vertices inside `verge_edge`**, 0 structural hits on the racing surface. `CAM_T4_INTRUSION_fixed.png` |
| **1b** | the review's other named object, `BR_FenceStruct_R07` at s 1546.1–1558.1, u −8.86…−5.24, **3.756 m inside the track edge and 2.772 m above the tarmac** — and *not* on the barrier line: 26–28 m from the nearest node | **`build_gate` emitted design-frame coordinates.** Every other primitive in this module wraps its vertices in `W3` (design → world); this one did not, so all **16 marshal gates** were built 40° and a 350 m pivot away from the barrier they hang on. Fifteen landed in open country; `GATE_STATIONS` 1590.0 on the right landed on the T6 esses | `verify_fixes.py` D1 after the fix |
| **4** | **658 m² of the road corridor with no ground at all** (probe `void`, 104 stations, worst 38 m² at T3 s 728) — terrain cuts to `C.platform_edge`, §4b clamped the platform to `owned_edge`, nobody built between | §4c: `platform_reach` extends to `C.platform_edge` exactly where the annulus is void **and** the extension is ≥ 0.10 m below whatever already covers it — measured with the same swept-segment test `build_terrain.union_field` cuts with | `verify_fixes.py` D4 on the review's own 2 m × 1 m grid |
| **5** | `BR_Concrete_L13` — the pit wall — standing **0.36–1.01 m above the Beat-4 pit-exit road**, world x 135.9–146.4 | §4c-veto: `barrier_blocked(s, side)` tests the barrier **body** against `C.in_access_ribbon`, applied inside `_CorridorView.sample` (see the note there: it does NOT reach `build_dressing`). The pit wall now starts at the merge point, s = 3465 | `verify_fixes.py` D5: **0 structural vertices inside the ribbon**; `placement_gate.py` **PLACEMENT_CLEAN** |

and one the gate found while verifying those, which is a **telemetry ↔ contract**
conflict, not a barrier one:

| # | the defect | what was done | verified |
|---|---|---|---|
| **6** | `placement_gate.py` reported `BR_Transit_NorthWall` inside the **car's driven path**, 156 triangle pairs, minimum separation **0.189 m** between a wall vertex at (95.50, 11.40) and a car centre at (95.44, 11.22). The contract's north wall face is at `TRANSIT_NORTH_OFFSET_M` = +8.00 and the ribbon is ±6.00 m wide, but `telemetry.csv` puts the car **+8.95 m** left of `access_route_point` at route t 96.6–107.5 — 3 m outside its own road for ~50 m of Beat 4. 24 telemetry samples put the wall inside the car body | ~~`transit_wall_offset(t, side)` pushes the wall **outboard only where the swept car box demands it**, tapering back to the contract's exact +8.000~~ — **THAT WORKAROUND IS DELETED (2026-08-02).** R2-042 made `tools/build_telemetry.py` evaluate the transit merge as the declared R150 / 40° arc, so the two curves now agree and the correction table was a no-op that still fired. MEASURED before deleting, this module's own `transit_wall_offset` over t 6→96: **pre-R2-042 CSV +3.347 m north push over 32.4 m; post-R2-042 CSV +0.000 m; table removed +0.000 m**, south 0.000 throughout. `transit_wall_offset` now returns the contract constant and reads nothing | vertex-level: the wall path is bit-identical (0.0 m over 3603 coords/side) to the pre-delete module on the corrected telemetry, and no longer responds to the old telemetry at all. `assembly5.blend` **carried the defect** — its `BR_Transit_NorthWall` inner face runs 7.840 m to route t 63 then climbs to 11.173 m at t 96. `assembly6.blend` is the fixed world |

Two more found while fixing those, both reported with numbers below: **§4b-steps** (five
places where the *contract's* barrier line jumps 8.6–46.3 m in one metre and builds a
transverse Armco run across the runoff) and **§4c-inner** (314 m² of the pit-straight
platform band coplanar with `SURF_AccessRoad`'s gore).

---

## THE VARIATION SYSTEM — the point of this module

A barrier line is the single highest repetition risk in the film. Measured from the build:

| | count |
|---|---:|
| platform area built (`verge_edge` → `owned_edge`) | 221 143 m² |
| W-beam panels | 1 821 |
| Armco posts | 3 641 |
| splice bolts | 6 862 |
| TecPro blocks | 5 611 |
| precast concrete blocks | 125 |
| catch-fence posts | 690 |
| catch-fence spans | 665 |
| marshal gates | 28 |
| tyres | 2 255 |
| real 3-D fence wires (doppler window) | 2 080 |
| scattered stones | 240 000 |
| **objects / vertices / triangles** | **129 / 6.88 M / 11.76 M** |
| gravel bed area | 37 639 m² |
| tarmac runoff area | 42 878 m² |
| build time, headless | 119 s |

The brief's red line is *"i dont want repeat stuff aka one tree spammed 100 times"*.

**Nothing in this module is an instance.** There is no master panel, no master post, no
master block, no master tyre, no master pebble that is duplicated and rotated. Every unit
is generated from its own parameter draw straight into its own vertex data. Object
instancing (`bpy` linked duplicates, particle systems, geometry-node point instances) is
used **zero** times. The cost is 6.88 M vertices / 11.76 M triangles, which is affordable
and is where the geometry budget was deliberately spent.

`build()` is verified idempotent: two consecutive calls in one session give identical
object, mesh and material counts and identical vertex and triangle totals.

Variation is not "random rotation". It comes from a **history model**: three deterministic
fields over station `s`, plus a discrete incident list. Everything downstream is a
function of those, so the wear on a rail, the lean of its post, the crush of the TecPro
block in front of it and the rust in the fence above it all agree with each other —
which is what makes it read as *history* rather than as noise.

### 1. AGE — maintenance runs (`History._runs`)

The lap is partitioned into **maintenance runs of 25–220 m**, each with one age value.
Ages correlate along a slow sector field, but 8.5 % of runs reset to near-zero ("replaced
last month") and a further 12 % to ~0.2. The result is the strongest anti-repetition cue
available on a barrier: a bright, unweathered galvanised stretch standing against a
twenty-year-old one, with a hard joint between them. Age drives galvanise brightness and
roughness, rust coverage, TecPro UV fade, bolt corrosion, concrete staining, fence-wire
colour and fence slackness.

### 2. ALIGNMENT — wander and settlement (`History.align`)

Two-octave smooth noise gives ±37 mm of lateral wander and up to −57 mm of vertical
settlement, plus a discrete ±27 mm step at every straightening-run joint. Nothing on the
circuit is a perfectly straight ribbon. The lateral term is clipped to the contract's
`BARRIER_JITTER_MAX_M = 0.25`, and **the ground under the barrier reads the same vertical
field**, so a settled run takes its own shoulder down with it instead of standing in a
trench — see "the runoff platform" below.

### 3. INCIDENTS — where cars actually hit (`History._incidents`, `crash_field`)

38 incident sites are inverse-CDF sampled from a **crash-probability field** built from the
corner table: a per-corner weight (T1 1.00, T4 0.95, T12 1.00, T8 0.85 — the braking zones
and the off-camber crest — down to 0.25 at T2/T13) convolved with an upstream braking lobe
and a shorter exit lobe. 72 % land on the outside. Each site has:

* a **kind** — `brush` (44 %), `hit` (34 %), `repaired` (15 %), `heavy` (7 %);
* an **extent** (5–30 m) and a **depth** (10–190 mm of real rail deformation);
* an **epoch** — how long ago, which fades the paint transfer and grows rust in the scar;
* a **fictional livery colour** for the paint transfer (`LIVERY`, 9 entries, no real teams).

`repaired` sites force the local age to ~0.05: fresh panels and fresh posts spliced into an
old run, with the residual kink still there. `heavy` sites bend the post 9–43° and crush
the W-beam profile up to 28 %.

### 4. Per-unit draws on top

Every unit additionally hashes its own index:

| unit | what differs per unit |
|---|---|
| W-beam panel | length 3.86–4.09 m, dent lobe shape/position, splice-lap step, sag between posts, vertical crush, rail count (2 or 3, piecewise-constant on 70 m blocks) |
| Armco post | section type (C-channel / I / RHS), width ±8 %, exposed height, lean in two axes ±3.4°/±2.2°, yaw ±6°, cap plate present or not, extra bend at incident sites |
| whole maintenance run | 30 % of runs are **painted** rather than bare galvanised, in one of five fictional maintenance colours, with the paint chipping back to rust as the run ages. Rails and posts read one shared `run_paint()` so they never disagree |
| splice bolt | radius ±10 %, 3.5 % simply missing |
| TecPro block | length ±3 %, depth ±3 %, compression 0–42 % (front row worst), yaw ±(1.6°+7° × compression), roll ±1.2°, seating height, UV fade, replaced-block reset, plus a slow along-the-wall *settling* field so the line creeps in depth and height; 7 % of cap blocks are simply missing |
| concrete block | per-pour tint, length, height ±1 %, yaw ±0.65°, roll ±0.55°, seating depth, up to 3 chipped corners |
| fence post | I-section width ±6 %, lean ±1.3°, yaw ±2°, height ±1.5 %, pad present or not, back-stay every 4th–7th |
| fence span | **tension state**: slack 0.25–1.0 → out-of-plane bow, vertical sag, top-edge droop, and a 13 % chance of a local impact dent; wire phase; 14 % chance of a broken-wire patch |
| tyre | radius ±4 %, width ±7 %, spin, tilt ±3°, flat-spotting that grows with the load above it, tread-groove wear, age/chalking |
| pebble | 12 vertices each with an independent radial jitter, plus non-uniform scale and two-axis rotation — literally no two identical |

### 5. Layout variation, not just surface variation

Repetition is also fought at the level of *what is there at all*:

* **rail count** flips between 3-beam (FIA height 1.012 m) and 2-beam on quieter infield
  stretches, in 70 m blocks;
* **the fence is not a uniform ribbon** — on the infield it only exists where the infield
  is accessible (5 declared ranges), so long unfenced infield runs alternate with fenced
  ones;
* **16 marshal gates** break the fence with a tube frame and a leaf standing 8–38° open;
* the barrier line itself is **straightened into real straight runs**: stretches whose
  heading changes by < 0.85° are replaced with a true chord up to 130 m long, so straights
  are dead straight and corners are polygonal at panel resolution, exactly as built
  guardrail behaves — and each run joint carries its own alignment step;
* the **verge** is 221 143 m² of one material, which is the biggest repetition risk in the
  module by area. It is fought with a dryness field along the lap rather than a per-square-
  metre average, so whole stretches read as different palettes — see "The verge" below.

---

## Geometry decisions worth knowing

### The barrier line

The cross-section programme (`asph` / `grav` / `apex` / `grass` / `btype` / `fence` /
`barrier_offset`) now lives in `world_contract._Corridor`, ported verbatim from the class
that used to be here, so `C.barrier_offset` is numerically identical to the line this
module already built — but is now **derived from the contract's `half_width`**, so a width
change moves the runoff, the verge, the boards, the barrier and the terrain hole together.

```
C.barrier_offset(s) = verge_edge(s) + max(asphalt + gravel, grass, 4.0) + margin(s)
                      clamped by  0.50 R   on the inside of a corner
                      blended to  a pin    where the spec gives an exact number
```

* **Pins hold exactly** — verified in this build: pit wall `11.5000`, pit-straight south
  barrier `19.0000`, doppler standoff `30.0000`.
* Lateral history jitter stays (it is what stops the line being a drawing-board curve) and
  is now clipped to the contract's `BARRIER_JITTER_MAX_M = 0.25`.

#### §4b — the one place this module departs from the contract, and why

**The circuit crosses its own corridor, and `C.barrier_offset` does not know it.**

spec §9 gives T3 — a 140 m-radius right-hander, so its *outside* is `side = +1` — "40 m
asphalt outside, 15 m gravel bed at the exit". The inside-corner radius clamp never bites
at 140 m, so `C.barrier_offset(s, +1)` comes out at **66.9 m** for the whole of T3 and S3.
But S4 (the hairpin exit ramp) and T5 run back past that side 51–67 m away and 5–7 m
higher. Measured with the contract's own `project` and `world_ground_z`:

| s | `C.barrier_offset` | nearest station at that point | world ground − barrier |
|---:|---:|---|---:|
| 700.0 | 66.88 | 700.0 — itself | 0.000 m |
| 753.0 | 66.83 | **1225.4**, u +15.34 | **+6.740 m** |
| 800.0 | 66.94 | **1166.9**, u −1.13 — *owner `SURF_Track`* | **+5.203 m** |
| 900.0 | 66.97 | **1067.2**, u −8.14 | +1.579 m |

So the declared barrier line for s ≈ 700–1100 on the left runs **under the S4/T5 racing
surface**, and the runoff platform that goes with it would be a second ground plane 5–7 m
below a piece of circuit that already has one. This was measured, not guessed: an early
build put `BR_Verge_L` at z = +5.08 where the datum said −0.68, and the raycast found it.

`C.road_corridor_mask` already resolves this correctly — it asks `project`, which returns
the **nearest** centreline, so the mask is the union of the two branches and terrain cuts
exactly that. `C.barrier_offset` does not. So this module resolves it **by the contract's
own rule** and publishes the result:

```python
build_barriers.owned_edge(s, side)       # medial axis between the two branches
build_barriers.barrier_offset(s, side)   # min(C.barrier_offset, owned_edge − margin)
build_barriers.barrier_clamp_report()    # exactly how much, and where
```

#### §4b, second cut — the assembly review's defect #1, which this section *caused*

The first version of §4b smoothed the **deficit** `max(0, bo − avail)` over ±13 m of
dilation and ±24 m of box filter and subtracted it from the contract's line:

```
line = min(bo − box(dilate(deficit)), avail)
```

That is only meaningful while `bo` is continuous, **and it is not.** Measured on the
contract's own 1 m grid, side +1:

| s | `C.barrier_offset(s, +1)` |
|---:|---:|
| 900 | 66.970 |
| 904 | 65.988 |
| **905** | **14.000** ← **51.99 m in one metre** |

`_Corridor.maxoff` box-filters an inside-corner cap that is `1e6` outside the corner and
`14.0` (= 0.50 R, R = 28 m at the T4 hairpin) inside it, so the filtered cap falls off a
cliff at the station where the last `1e6` leaves the 41-sample window. The deficit at
s ≤ 904 is ≈ 43 m; the ±37 m influence window carried it forward onto stations where `bo`
had **already** dropped to 14.0, and `14.0 − 32.8 = −18.80`.

A barrier face at `u = −18.80` on side `+1` is **18.8 m past the centreline**, on the far
side of the track. What got built was `BR_Armco_L03` / `L04` and `BR_FenceStruct_L03` /
`L04` lying **across the T4 braking zone** — 982 of 4 147 sampled vertices inside
`verge_edge`, s 904.4–937.2, u −9.79…+9.93, mean 1.41 m and max 4.60 m above the tarmac,
over 53 m of lap. `CAM_T4_INTRUSION.png` shows it wall-to-wall across the road. It did not
exist before the clamp; the clamp made it.

**The replacement, and the three properties it is built to have.**

```python
target(s) = min(C.barrier_offset, avail)                     # the hard answer
soft(s)   = verge_edge + cone_erode(target − verge_edge, 0.30)   # slope-limited
line(s)   = lerp(target, soft, w)      # w = 1 only where `avail` actually bites
```

1. **It cannot reach the track, and that is a proof, not a clamp.**
   `cone_erode(c, R)(s) = min_j (c(j) + R|s−j|) ≥ min_j c(j)`, and
   `min_j (target − verge_edge) ≥ 1.000 m` — the pit wall (spec §10.7, circuit y = +11.5
   against a verge edge at 10.5) is the tightest clearance the **contract** declares
   anywhere, and `avail ≥ verge_edge + 4.0` by construction. A convex combination of two
   fields that are both ≥ `verge_edge + 1.0` is ≥ `verge_edge + 1.0`. So
   `barrier_offset(s, side) − verge_edge(s) ≥ 1.000 m` for **every station on both sides**,
   whatever the contract does upstream — asserted at import, and re-measured against the
   built vertices by `verify_fixes.py`.
2. **It is buildable.** `|d(offset)/ds| ≤ 0.30` inside the blended stretch — a 1 : 3.3
   taper. T4's entry now runs 26.0 m out at s = 840 → 21.3 at 880 → 15.5 at 900 → **14.0
   at 905**, and back out 14.0 at 1060 → 25.4 at 1100, instead of falling off a 52 m cliff.
3. **It is a no-op everywhere the cap does not bite.** `deficit == 0` for every station on
   side −1 and for 89.2 % of side +1, so `w == 0` there and the line is
   `C.barrier_offset` **bit for bit**.

Global smoothing was measured and rejected: eroding the whole lap at 0.25 m/m moves the
**right-hand** barrier line in by a **mean of 4.49 m**, because the contract's runoff ramps
legitimately shed 45 m of lateral over 55 m of station and a global slope limit cannot tell
those from the cliffs. (Smoothing the *line* rather than the deficit — the first thing
tried, a round earlier — dragged the contract's ±1.2 m margin wander down by 1.8 m over
half the lap. Both were caught by measuring, not by reading.)

| | fraction of the lap clamped | max clamp | mean where clamped | ranges | min clearance over `verge_edge` | max lateral rate |
|---|---:|---:|---:|---|---:|---:|
| left | 10.8 % | 51.85 m | 24.19 m | s 661–904, 1061–1213 | **1.000 m** (the pit wall) | **8.64 m/m** (§4b-steps) |
| right | 0.0 % | 0.00 m | — | — | **8.500 m** | 46.31 m/m (§4b-steps) |

#### §4b-steps — a step is not a barrier line, it is two barrier lines

Slope-limiting fixed T4 because the cap was already holding the line there. It does
**not** fix the five places where the contract's *own* line is discontinuous, because
`_Corridor._build` applies the pit-straight overrides, the runoff table and the
inside-corner cap as hard boolean masks on a 1 m grid:

| side | s | offset before → after | Δ in one metre |
|---|---:|---|---:|
| right | 250 | 21.19 → 67.50 | **46.31 m** |
| right | 3114 | 36.09 → 20.40 | 15.69 m |
| right | 1743 | 41.00 → 56.25 | 15.25 m |
| right | 1819 | 56.38 → 47.00 | 9.38 m |
| left | 2665 | 33.64 → 25.00 | 8.64 m |

`barrier_nodes` walks the line by **arclength**, so a 46 m lateral jump is 46 m of
polyline; the straightening pass then finds eleven consecutive nodes on one heading, and
what gets built is **46 m of three-beam Armco and 3.6 m debris fence running across the
T1 runoff at 89°** — in front of `CAM_T1_RUNOFF`.

It is **not** smoothed. Slope-limiting a 46 m outward step at 0.30 m/m holds the barrier
20–45 m inboard of the declared line for 150 m, and `_build_programme` scales the runoff
to fit inside the barrier, so it would halve T1's declared 45 m asphalt + 12 m gravel *to
fix a barrier*. A step is not a barrier line: it is two barrier lines, one ending and one
beginning further out, which is what a circuit builds where a runoff opens. So **no
barrier is laid across the jump** — `BARRIER_BREAK_RATE = 2.0` m/m, five places, **20 m of
lap in total**, which reads as a marshal opening where the runoff widens. The line itself
is untouched, so no runoff loses a metre.

The real fix is in `_Corridor._build`: ramp the pit-straight override and the `maxoff` cap
instead of box-filtering a 1e6 sentinel. Handed back.

The runoff programme is scaled to the room that is actually there, keeping the declared
asphalt : gravel ratio — T3's 40 m + 15 m becomes 33.4 + 12.5 at s = 700 and 11.4 + 4.3 at
s = 800. That is what fits, and it is what a real circuit does when two legs run 51 m
apart.

**This is a contract-level defect, not a local one.** `build_dressing` reads the barrier
line too, and would otherwise stand marshal posts and ad boards under the S4/T5 racing
surface for 400 m. It reads it through `BR.COR.barrier_offset(s, side)`, so `COR` is kept
as a thin `_CorridorView` over `world_contract._Corridor` whose `barrier_offset`
**deliberately routes through the clamp** — every consumer gets the corrected line without
having to know the clamp exists. (Deleting the old `Corridor` class outright would have
broken `build_dressing` silently at import, which is exactly the class of failure this
migration exists to stop; `COR.get(...)` is kept working for the same reason.) The real
fix belongs in `world_contract.barrier_offset`, and it is the top item handed back.

`build_dressing`'s `ground_z(s, lat)` wrapper still takes no `side`, so its laterals are
read as **signed** and everything it places on the right of travel loses its banking. That
one is not fixable from here — it needs `build_dressing` to pass `side`, which is what its
own migration note tells it to do.

`btype` is `B_NONE` across the open pit-exit apron (design x −480…−245): spec §10.5 says
there is no gate to cut and no barrier to remove, so there is none — and contract §7 makes
that stretch's *surface* `build_architecture`'s, so this module builds no platform there
either (see "The pit-exit apron" below).

#### §4c-veto — the pit wall stood in the pit-exit road (assembly defect #5)

`BR_Concrete_L13` — the pit wall, spec §10.7's exact pin at circuit y = +11.5 — stood
**0.36–1.01 m above the Beat-4 pit-exit road** over route t = 126→140 (world x 135.9→146.4,
y 22.3→31.1). The wall is not wrong. It simply **cannot start before the pit exit has
merged**: the R150 merge arc converges on the pit straight, so between t ≈ 106 and t ≈ 146
the ribbon's outboard edge is *outboard* of y = 11.5 and the wall is inside the road.

Measured, ribbon outboard edge against the declared wall face:

| route t | s | ribbon outboard u | wall face | wall in the road |
|---:|---:|---:|---:|---|
| 98 | 3406.6 | 21.055 | 23.089 | no |
| 106 | 3413.8 | 18.430 | 17.965 | **yes** |
| 130 | 3436.2 | 12.912 | 11.500 | **yes** |
| 138 | 3443.8 | 11.875 | 11.500 | **yes** |
| 146 | 3451.4 | 11.245 | 11.500 | no |

`barrier_blocked(s, side)` tests the barrier **body**, not just the declared face — a
precast block straddles the face by 0.265 m inboard (`CB_T`/2 + batter) — at
`in_access_ribbon(margin = 0.15)`, plus 3 m of clearance either end. The pit wall now
begins at **s = 3465** instead of s = 3430, which is what a real pit wall does: it starts
at the merge point. 98 m of veto on the left in total (35 m of it concrete; the rest is
already `B_NONE` apron).

The veto is applied **inside `_CorridorView.sample`**, not at the four call sites, so
`build_armco`, `build_tecpro`, `build_concrete` and `build_fence` cannot each forget it
independently — which is the exact failure mode this whole round exists to stop.

**It does not reach `build_dressing`.** That module reads
`world_contract.COR.sample("btype"|"fence", …)` directly, not this view, so it will still
place marshal posts, tyre stacks and boards on the barrier line inside the pit-exit road
and across the contract's steps. It must call `build_barriers.barrier_blocked(s, side)` —
or read `BR.COR` instead of `C.COR` — before it stands anything on that line. Handed
back, with the exact stations in `ribbon_report()`.

### Empty zones

The three declared empty zones are read from `circuit_spec.json` and enforced literally:
every barrier-line station is tested against the boxes in the **circuit** frame, and where
it falls inside, the structure is capped at the zone's `max_height_m` — in practice the
6 m fence posts are suppressed and only the 1.012 m Armco survives. The west-outfield zone
is the one that actually bites, on the outside of T12.

### The verge — the surface the "grass gray line" complaint is actually about

`mat_verge` covers 221 143 m², which is most of every wide frame of the flying lap, so it
is built to be looked at rather than to be a fill colour. Three things stop it reading as
a ribbon:

1. **Dryness is a field along the lap, not a per-square-metre average.** UV.y is the
   station in metres, so a 95 m and a 31 m noise put whole stretches into drought and whole
   stretches into shade. Two colour ramps (green and straw) are mixed by that field, so a
   dry stretch and a green one are different *palettes*, not different brightnesses.
2. **The cross-section is a real one.** UV.x is metres outboard of the painted verge. The
   first 2.6 m is scalped and rubber-flecked because cars run over it — that is the band an
   onboard camera actually sees. The middle is mown turf with bare scrapes worn through to
   subsoil. The last few metres before the barrier are a compacted aggregate service strip
   with a mown edge line, keyed off `wear.B`, which the platform builder fills with the
   distance to the barrier line.
3. **Tussocks, not noise.** One voronoi at clump scale drives *both* the colour and the
   bump, so the relief and the colour belong to the same clumps. At a 12.47° sun that is
   what makes turf read as turf instead of as a green plane.

**Calibrated by measurement, not by eye.** `render/world/barriers/calibrate_materials.py`
renders five reference patches of known diffuse albedo beside flat patches of this module's
five ground materials, in one frame, under `setup_test_light` — which is the contract's
light verbatim — and interpolates the implied albedo of each from the references. Contract
§8's rule is that if a material does not land near its intended albedo, *the material is
wrong, not the light*; this is how that gets checked rather than asserted.

```
material   display R G B       implied a   intended    hue G/R   B/R
verge      0.441 0.410 0.287     0.125      0.135       0.931   0.652
runoff     0.418 0.372 0.349     0.125      0.115       0.890   0.835
gravel     0.613 0.564 0.511     0.294      0.260       0.919   0.833
concrete   0.634 0.605 0.582     0.369      0.350       0.956   0.919
stone      0.599 0.567 0.538     0.301      0.280       0.946   0.898
neutral 0.18 grey renders G/R 0.939, B/R 0.896                    PASS
```

The hue test is against **the neutral grey lit by the same sun**, not against `G > R`. The
illuminant is (1, 0.716, 0.387), so a green surface still renders R > G; asking for `G > R`
is a test grass can never pass under this light. The verge's B/R is 0.244 *below* neutral,
which is what "yellow-green" means numerically.

`build_terrain` still scatters vegetation *inside* the corridor — the contract says so and
the user asked for it — but it places every clump with `C.ground_z` and plants nothing
inside `C.runoff_widths`' asphalt or gravel. Grass on the verge, bare gravel in the trap.

### The debris fence — where the geometry stops and the shader starts

Posts, base plates, back-stays, top rail, three tension cables, gate frames and leaves are
**real geometry**. The woven mesh is **two real surfaces** — a vertical-wire sheet 4.5 mm
in front of a horizontal-wire sheet, which is physically what a woven mesh is — each
carrying an analytic weave shader at a 50 mm pitch with 5.2 mm wire (10.4 % coverage per
layer, 19.7 % combined — an FIA debris fence, not chain-link).

This was a measured decision, not a shortcut. Full 3-D wire geometry over 5.2 km of fence
is ~145 m of wire per running metre → ≈ 750 km of wire → >100 M triangles, which is not
survivable in a scene shared with five other builders. The arithmetic that says the card is
enough: at the closest the camera ever gets to a fence (4.0 m, the doppler hover), one
50 mm aperture subtends 43 arcmin ≈ 34 px at 4K, and one 5.2 mm wire subtends 4.5 arcmin
≈ 3.5 px. A 3-px-wide wire with a correct cylindrical normal and a correct alpha silhouette
is indistinguishable from a 3-px-wide tube; what geometry would add — the over/under crimp
— is sub-pixel at every distance the camera reaches. The two-layer construction supplies
the one thing a single card cannot: correct parallax and mutual occlusion between the two
wire sets at grazing angles.

**The one place it *is* geometry**: `WIRE_WINDOWS` puts real 3-D vertical wires (4-gon
tubes) across the doppler hover window, s 2495–2615 on the outside. They read the *same*
per-span seed as `build_fence_span`, so a real wire and the analytic horizontals it crosses
lie on one surface; and `build_fence_span` drops its vertical card inside the window, so the
two are never double-drawn.

**Analytic LOD instead of a geometry LOD.** A periodic alpha mask aliases viciously once
the aperture drops under a pixel. Rather than swap geometry (which would produce a visible
seam), the shader mixes the crisp mask toward its *exact mean coverage* — which is the
correct filtered answer for a uniform periodic pattern — over a distance band read from
`Camera Data → View Distance`. There is no seam because there is no switch. The band is
45–190 m **at 3840 px wide**; `set_fence_fade(scene)` rescales it from the actual render
width, so a 960-px preview and the 4K master resolve the same amount of weave. *Any
orchestrator that renders this scene at a non-4K size must call `set_fence_fade()` after
setting the resolution.*

### Gravel

Gravel has to survive the camera diving to kerb height at the hairpin, so it is built in
three layers, each sized against what a pixel is actually worth:

1. **Bed geometry** — a structured grid whose s- and u-spacing is set by hero tier
   (0.09 m / 0.045 m across at T4 and T1, down to 0.36 m / 0.30 m on far beds), carrying
   the *macro* truth: the graded entry lip, the 0.24 m depth, the retaining bank, settled
   undulation, and **raked furrows** (0.30 m pitch, 11 mm, phase drifting along the trap).
2. **Braking-zone disturbance** — 3–10 **gouges** per bed, bunched toward the entry, each
   a pair of wheel ruts 1.7 m apart at a shallow angle into the bed, 75–190 mm deep, with a
   thrown-up berm alongside and a decay length of 4–18 m. This is what "raked/disturbed
   near the braking zones" means physically: the rake is the default state and the ruts are
   where it has been destroyed.
3. **Proud stones** — 130 000 individually-generated pebbles (11–42 mm) scattered over the
   near band of every hero bed. They carry the silhouette at close range, which is the one
   thing a bump map cannot fake under a 12.5° sun.

Below 11 mm the shader takes over: two voronoi scales (11 mm stones, 38 mm clumps) driving
colour-per-stone and bump. At a 12.5° sun elevation, bump at that scale reads almost like
displacement, which is why the geometry budget stops there.

### THE RUNOFF PLATFORM — 221 143 m² of ground, and the whole of finding #1

Before the contract this module built three disconnected ribbons — a tarmac runoff strip,
a gravel bed and a 4.5 m shoulder under the barrier — and left the ground between them to
`build_terrain`, which covered the lot in dirt on a 2.5 m grid. Terrain then deliberately
left that zone *bare* (`ter_wear` 0.85, no grass inside `PLAT`) **because it assumed the
paving would be on top**. Two correct-in-isolation decisions producing "a grass gray line".

The contract reverses it: terrain cuts a **309 180 m²** hole and welds its first ring of
vertices to `corridor_rim(s, side)`; everything inside is ours. So the platform is now
**one continuous surface per side**, `verge_edge(s)` → `platform_edge(s, side)`, emitted as
four material bands that share their boundary rows exactly — same station array, same
lateral expression, same z function — so there is no internal seam to find:

| band | extent, from `verge_edge` | object | material |
|---|---|---|---|
| **A** runoff asphalt | `0 … prog("asph")` | `BR_Runoff_{L,R}` | `mat_runoff` |
| **X** apex gravel sub-base | `0 … prog("apex")` | `BR_Subbase_{L,R}` | `mat_gravel` |
| **G** outer gravel sub-base | `+asph … +asph+grav` | `BR_Subbase_{L,R}` | `mat_gravel` |
| **V** the verge | outboard of all of them … `platform_edge` | `BR_Verge_{L,R}` | `mat_verge` |

`platform_z(S, U, side)` is `C.ground_z` plus a cross-section that is *physically* a
runoff platform and never touches either weld: a 45 mm pavement-edge drop and a 4 m
drainage swale outboard of the asphalt, a 75 mm earth retaining berm outboard of a gravel
bed, a graded 4.8 m maintenance strip under the barrier line, and low mown-ground relief.
Every one of those terms is multiplied by `sin(π·t)^0.8`, which is identically zero at
`t = 0` and `t = 1`.

**The gravel beds are dug into it, not cut out of it.** The gravel bands are a sub-base
that dips to `min(0.62, 3.2 × trap_depth_profile)` — deliberately deeper than the worst
possible bed (0.24 m profile + 0.19 m braking rut + 0.037 noise + 0.031 ripple = 0.498 m),
so no part of the platform can ever poke through a rut. In exchange, the trap and the
platform share one lateral extent (`prog("grav")`), one longitudinal taper and one depth
profile, and there is no hole for a hole to appear in. `trap_depth_profile(DD, WW)` is
exactly 0 at both lateral edges *for any width*, and every disturbance in `bed()` — the
noise, the rake furrows, the micro-relief and the braking gouges — is windowed to zero
there too. Without that window a 190 mm rut could reach the lip and the sub-base would
show through it.

#### The two welds, and what "agrees" means at each

**Inner, `u = verge_edge(s)`** — `build_surface`'s outer edge. z is **exactly**
`C.ground_z`: no offset, no drop, nothing hidden. What `SEAM_DROP` used to claim to
absorb no longer exists to be absorbed; there is one datum function and both modules
evaluate it. What *does* still exist is tessellation chord error — two independently
meshed surfaces cannot follow a 3675 m curve with the same sagitta — so the platform
carries a hidden flange: **straight down** `PLATFORM_TUCK_Z = 50 mm` at `u = verge_edge`,
then **inward** `PLATFORM_TUCK = 0.14 m`. It has zero horizontal footprint at the shared
line and is 50 mm below the datum by the time it has any, so it is not a coplanar surface
under `TOL_COPLANAR_M`; it closes chord slivers and nothing else. Its magnitude is set by
the chord error it has to close, and that is measured, not assumed.

**Outer, `u = platform_edge(s, side)`** — `corridor_rim`, what terrain welds to. z is
exactly `C.ground_z`. Station spacing is chosen per chunk from the **local rim radius** so
the chord sagitta stays under 4 mm: `ds = clip(√(8·0.004·R_rim), 0.40, 1.9)`. That matters
because on the inside of the T4 hairpin the rim radius falls to about 8 m, where a 2 m
step would leave a 6 cm scallop for terrain to weld into.

Where §4b's ownership clamp bites, the platform's outer edge is *not* the rim — it is the
medial axis, with the S4/T5 leg's ground up to 6.7 m higher on the far side. Left as a
free edge that is a hole in the world seen from below, so it gets a battered retaining
face (1 : 2.6) dropping to whatever `C.world_ground_z` actually reports over there.

#### §4c — the void, and where the platform actually stops (assembly defect #4)

`build_terrain` cuts **the union of every station's quad out to `C.platform_edge`** —
deliberately a *superset* of `road_corridor_mask`, so terrain "can never build ground the
road programme also builds". §4b clamped this module to `owned_edge` — deliberately a
*subset*, so a runoff platform is never laid 5–7 m under another leg of the same circuit.
Two conservative decisions in opposite directions, and between them

> **658 m² of the road corridor had no ground at all** — assembly probe `void`, 2 m × 1 m,
> 104 stations, worst 38 m² per 2 m station at T3 s 728.

The resolution is **not** "build to `platform_edge` everywhere". Measured over the whole
clamped stretch (s 700–1212, side +1, 20 247 samples on 1 m × 0.5 m):

| | |
|---|---|
| **68.6 %** of the annulus `(owned_edge, platform_edge]` | is already covered by **another station of this same module's platform** |
| of those, for s ≤ 914 | the covering ground is a **median 1.75 m above** ours — buried, invisible |
| of those, for s ≥ 1050 | the covering ground is up to **5.44 m below** ours — an extension there would be a shelf hanging over open ground |
| **31.4 %** | is covered by nobody, and **every one of those samples lies in s 701–922** |

So the reach is extended to `C.platform_edge` exactly where the annulus is void **and** the
extension is provably buried:

```python
platform_reach(s, side) = C.platform_edge   where _fill else owned_edge

_fill = (the annulus contains ground no other station lays)
      AND (every covered sample in it is ≥ PLATFORM_FILL_CLEAR = 0.10 m below
           the station that covers it)
```

ramped over `PLATFORM_FILL_RAMP_M = 12 m` so the rim never steps. The coverage test is the
**exact swept-segment** one — a point is covered iff it lies inside some station's quad
`{|along| ≤ ds/2·(1 + |u|κ), verge_edge ≤ |u| ≤ owned_edge}` — the same formulation
`build_terrain.union_field` cuts with, so the two answers are about the same region and not
about two different approximations of it.

| | stations capped | stations filled | ranges | extra ground laid |
|---|---:|---:|---|---:|
| left | 513 | **211** | s 701–748, 755–917 | **7 531 m²**, of which ~658 m² is the void and the rest is buried under the S4/T5 leg |
| right | 0 | 0 | — | 0 |

#### §4c — the inner edge, and a coplanar overlap the review did not reach

The Beat-4 access ribbon's outboard **gore** runs *inside* the pit-straight platform band
for 119 m of lap. Measured on a 0.05 m lateral scan:

| s | band | ribbon covers | % of band |
|---:|---|---|---:|
| 3440 | 10.50 → 13.54 | u 10.52–12.32 | **61 %** |
| 3460 | 10.50 → 12.10 | u 10.52–10.97 | 31 % |
| 3500 | 10.50 → 12.10 | u 10.52–10.77 | 19 % |
| 3540 | 10.50 → 12.10 | u 10.52–10.52 | 3 % |

**314 m² of the declared band, 100.4 m² of it inside the stations this module actually
paves**, coplanar with `SURF_AccessRoad` on the same `C.ground_z` — a stroboscopic z-fight
in the merge Beat 4 is built around, and the exact defect class this round exists to close.
`C.world_ground_z` puts the ribbon *above* the runoff platform in its priority order, so
the platform is the one that moves: `platform_inner(s, side)` cuts the band's inboard edge
to the ribbon's outboard edge **plus the contract's own paving joint**
(`C.ACCESS_RIBBON_SAW_M` = 0.30 m), the hidden verge flange is not laid where there is no
painted verge to hide under, and the 20 stations where the ribbon has eaten the whole band
are dropped from `_platform_runs`. **Cut, do not offset.**

### The pit-exit apron

Contract §7: outboard of `verge_edge`, wherever the corridor programme carries **no
barrier** — which is exactly and only the open pit-exit apron, circuit x −480…−245 on the
left of the pit straight, s ≈ 3196…3429 — the surface is `build_architecture`'s
unrubbered concrete and `C.ground_z` ties it to `APRON_Z = 0.000`. So this module builds
**no platform there**, cutting at `C.apron_zone(s, +1) > 0.5`. That is **6 721 m²** this
module deliberately does not build, and it will be a hole unless `build_architecture`
paves outward from `C.verge_edge` as its migration note instructs. Flagged, not assumed.

### The centreline

Now `world_contract.centreline_arrays`, evaluated **analytically**. The old class here
sampled a 0.25 m turtle integration and snapped every query to the nearest sample, which
put up to 125 mm of longitudinal jitter into anything not landing on a 0.25 m station.
`Centre` survives only as a design-frame view of the contract's world-frame centreline
(the module authors its geometry in the circuit frame and pushes it to world in `W3` at
emit time), and its old per-corner banking term is gone: `C.ground_z` carries the
cross-slope now, and carries it out into the runoff, which is the entire point.

---

## Conformance to the contract — measured, by raycast

`render/world/barriers/verify_vs_contract.py` builds a BVH over **every emitted triangle**
and casts rays at it. It never re-evaluates the formulas that produced the geometry: a
module that checks itself with its own arithmetic is exactly how six modules each passed
and the assembled world was broken.

```
blender -b --factory-startup -P render/world/barriers/verify_vs_contract.py \
        -- --out render/world/barriers/contract_report.json
```

### The five obligations, and what the rays found

| obligation | measure | result |
|---|---|---|
| **the inner weld** — the platform's height at `verge_edge(s) + 20 mm` against `C.ground_z`, both sides, 1225 stations | `p50`, `p95`, fraction within `TOL_SEAM_M` = 10 mm | **p50 −0.1 mm, p95 2.0 mm, rms 2.3 mm, 99.66 % within tolerance, 0 misses.** All 8 samples outside it are `BR_Stones_*` — proud pebbles at a gravel lip, which are 18–72 mm across and are supposed to be proud |
| **the outer weld** — `corridor_rim`, what build_terrain welds to | same | **p50 −0.0 mm, p95 0.8 mm, 99.95 % within tolerance** (n = 2 191). The single sample outside is the §4b retaining bank at s = 1213, the medial axis, which is not a rim |
| **coverage** — 37 laterals × 613 stations × 2 sides across the whole corridor: is there a surface at every point | hole rate | **0 holes in 43 878 samples**, re-measured after §4c over the band this module actually lays (`platform_inner` → `platform_reach`). Top-surface owners: Verge 32 546, Trap 5 635, Runoff 4 389, TecPro 177, Armco 143, Stones 100, Fence 94, TyreWall 45, Subbase 41, Concrete 708 |
| **is the runoff visible** — inside the asphalt band the top surface must be `BR_Runoff_*`; inside a gravel bed, `BR_Trap_*` / `BR_Stones_*` | fraction correct | **asphalt 800/800, outer gravel 928/928, apex beds 704/704 — 100 %.** The review's "the ENTIRE runoff programme is invisible" is 0 % of it now. (It was 92.8 % / 94.0 % before the corridor-ownership clamp: the 6 % failing were the T3 asphalt with the S4/T5 branch's verge sitting 5.8 m over it) |
| **the barrier foot** — ground height at the barrier line against the barrier's own base, and separately whether any GROUND surface is on top of it | fraction with ground > 0.15 m above the foot | **0.0000 on both sides**, against the review's 90.1 %. `ground − foot` p95 ±40 mm; **1.020 m (left) / 1.014 m (right) of a 1.012 m Armco showing**, against the review's ~0.29 m |

### The three assembly defects, re-measured on the built vertices

`render/world/barriers/verify_fixes.py`, run against a freshly built `R2_Barriers`. It
does not ask the formulas anything: it takes the **world position of every vertex of every
structural object**, projects it with `C.project`, and asks which station owns it.

| | before (assembly review) | after |
|---|---|---|
| **D1** structural vertices inside `verge_edge(s)` | 982 of 4 147 sampled — `BR_Armco_L03/L04`, `BR_FenceStruct_L03/L04`, `BR_FenceStruct_R07`, `BR_FenceMesh_R07`; up to **4.601 m above the tarmac** | **0 of 2 745 818** |
| **D1** ray probe: structural object topmost on the racing surface (2 m × 0.5 m grid) | 51 samples, 6.4 m², s 904.5–1059.5, mean 1.41 m / max 4.60 m proud | **0** |
| **D5** structural vertices inside `C.in_access_ribbon` | `BR_Concrete_L13`, 15 blocked points, 0.36–1.01 m above the road | **0** |
| **D4** void on the review's own 2 m × 1 m grid, `verge_edge` → `platform_edge`, both sides | **658.0 m²**, 104 stations, worst 38 m² at s = 728 | **26.0 m²**, 6 stations, worst 10 m² at s = 918 — see "Known limits" |
| barrier foot against the platform it stands on | assembly: ground **above** the foot at 90.1 %, p50 −10.8 mm | **p50 +11.4 mm**, p05 −21.5, p95 +15.6 (design intent +14 mm) |
| verge seam, platform height at `verge_edge + 20 mm` | p95 **8.9 mm** | **p50 0.18 mm, p95 1.94 mm, max 7.62 mm** — all inside `TOL_SEAM_M` |

### Interpenetration — BVH, triangle level

| pair | overlapping triangles |
|---|---:|
| tyre walls × the corridor's concrete wall and portal | **0** (was 34) |
| tyre walls × the platform | **0** |
| corridor wall × the platform | **0** |
| Armco × TecPro | **0** (was 3763) |

### Beat 4

| | built | contract | clearance to the painted verge |
|---|---:|---:|---|
| north retaining wall | 90.0 m | `t 6 → 96` | 13.122 m |
| south tyre wall + fence | 84.0 m | `t 6 → 90` | **1.737 m**, matching contract §6.2's measured table exactly |

`ARCH_ApronCorridor` absent from the build (`C.CORRIDOR_DELETE_NAMES`); the built wall
geometry sits a median 0.007 m (south) from the contract's line, the north wall's 0.174 m
being its coping's deliberate 0.16 m oversail toward the road.

### Where this build differs from the contract, in numbers

| | |
|---|---|
| `owned_edge` vs `C.platform_edge` | 513 stations capped, all on the left (s 700–1212), max gap **43.8 m**; right **0** |
| `platform_reach` vs `C.platform_edge` | **identical over 99.5 % of the lap.** 211 stations restored to the contract's rim (s 701–748, 755–917) — the void — for **7 531 m² of extra ground**, of which ~658 m² *is* the void and the rest is buried a median 1.75 m under the S4/T5 leg. §4c |
| `barrier_offset` vs `C.barrier_offset` | left **10.8 %** of the lap clamped, max 51.85 m, mean 24.19 m where clamped, **89.2 % bit-identical**; right **100.0 % bit-identical** |
| `platform_inner` vs `C.verge_edge` | equal everywhere except the Beat-4 ribbon's gore, where it is the ribbon edge + `C.ACCESS_RIBBON_SAW_M` = 0.30. 20 stations dropped entirely; **100.4 m²** of coplanar overlap with `SURF_AccessRoad` removed. §4c |
| barrier / fence vetoes | 98 m of lap on the left (35 m of it the pit wall's new start at s = 3465), 16 m on the right — every metre of it either inside the access ribbon or across a contract step. §4c-veto, §4b-steps |
| spec pins | pit wall **11.5000**, pit-straight south **19.0000**, doppler standoff **30.0000** — exact, after the clamp *and* after the slope limit |
| **the invariant** | `barrier_offset(s, side) − C.verge_edge(s) ≥ 1.000 m`, **all 3 675 stations, both sides** — asserted at import, and re-measured on the built vertices by `verify_fixes.py` |

---

## LOD

There is no polygonal LOD switch anywhere in this module, because a one-shot camera would
find the seam. Detail is modulated **continuously** instead:

* rail sampling: 4 sub-segments per panel normally, 10 where there is a dent or a hero
  window (so a dent is never a faceted crease);
* every object is **recentred** on emit (local vertex coordinates + an object offset).
  Without it, a position-driven procedural at world |P| ≈ 1000 m and a ×90 gravel scale
  lands at 10⁵ and float32 turns the gravel into smeared mud — this was a real, rendered,
  diagnosed defect. **Every material in this module therefore reads `TexCoord > Object`,
  never `Geometry > Position`**; anything added later must do the same;
* splice bolts: hero tiers only (`tier >= 1`);
* fence mesh grid: 20 × 12 in hero windows, 8 × 5 beyond;
* gravel bed spacing and stone density: three tiers by hero window;
* platform station spacing: `_platform_ds` is `clip(√(8·0.004·R_rim), 0.40, base)` with
  `base` 0.9 m in a hero window and 1.9 m outside it, further capped to 0.65 m wherever
  `platform_edge` is shedding more than 0.40 m of lateral per metre of station. Both caps
  exist for the same reason and neither is a taste judgement: they hold the chord sagitta
  of `corridor_rim` — the polyline `build_terrain` welds to — under 4 mm;
* fence weave: analytic, resolution-aware, seamless by construction.

`HERO` declares the eight windows, derived from the beat sheet: the T1 braking zone, the
hairpin, the summit, Le Pont de la Plongée, the doppler station (tier 2, the closest the
camera ever gets to a barrier), the plunge, the gantry and the start/finish line.

---

## Test renders

In `render/world/barriers/`. Every one was rendered and looked at; the framings are taken
from the beat sheet, not chosen to flatter.

| file | what it is for |
|---|---|
| `doppler_fence.png` | the Beat-5 hover station, 4.0 m from the Armco and fence — the closest barrier inspection in the film |
| `doppler.png` | the same station, actual Beat-5 framing down the straight |
| `hairpin_trap.png` | into the T4 trap from 3.4 m: rake furrows, braking ruts, berms, lip |
| `tecpro_macro.png` | TecPro at 4 m: colour, UV fade, compression, missing cap blocks |
| `fence_lod.png` | 6 m to 300 m of fence in one frame — the analytic-fade seam check |
| `hairpin.png` | the kerb-height hairpin camera, z = 0.85, 21 mm |
| `hairpin_tyre.png` | the tyre wall at 4 m |
| `gravel_macro.png` | gravel at 1 m, 50 mm — the "does it read as gravel" gate |
| `armco_macro.png` | the worst incident site inside a hero window at 1.7 m, 85 mm |
| `t1_wide.png` | T1: 45 m asphalt + 12 m gravel + TecPro + fence in one frame |
| `repeat_hunt.png` | 400 m of pit-straight barrier — the deliberate hunt for a recognisable repeat |
| `transit.png` | the walled apron corridor at rooftop height |

and the four added for the contract migration, which exist to show the findings gone:

| file | what it is for |
|---|---|
| `banked_runoff.png` | T10/T11 from 34 m up and 78 m outside, looking back across the whole banked complex — the 294 km/h helicopter dive, and the exact place `TER_Ground` stood 0.387 m proud of the tarmac. The cross-fall reads against the horizon, so the banking is visibly **carried out past the verge** instead of stopping at it |
| `platform_section.png` | the whole T1 cross-section from 15.5 m over the centreline: painted verge → 45 m asphalt → 12 m gravel → verge → TecPro → fence. If any of it is under dirt this frame says so |
| `calib_materials.png` | the five ground materials beside five reference patches of known albedo, under the contract's light — the frame `calibrate_materials.py` measures |
| `verge_macro.png` | the verge itself at working distance, 1.35 m lens height — the surface the user called "a grass gray line" |
| `weld_grazing.png` | 85 mm at 0.42 m above the painted verge on the pit straight, looking straight down the inner weld into a 12.47° sun. A gap, a ledge or a z-fight at `verge_edge` is a lit line here and nowhere else |

and the round-2 evidence frames, built by `render/world/barriers/make_fix_scene.py`
(barriers + `build_surface`'s real racing surface + `build_sky`'s light, so the frame is
the assembled thing and not a proxy):

| file | what it is for |
|---|---|
| `CAM_T4_INTRUSION_fixed.png` | **the review's own camera**, replicated exactly — `P(872, −1.5, +1, +2.30)` → `P(918, +2.0, +1, +0.60)`, 40 mm. Put it beside `render/world/assembly/CAM_T4_INTRUSION.png`, where three-beam Armco and a debris fence run wall-to-wall across the road. The T4 braking zone is now clear road, with the TecPro and the tyre wall on the apron where they belong and the gravel and kerb on the outside |
| `CAM_T1_STEP.png` | s 250 on the right, where the contract's line jumps 46.31 m in one metre — the 46 m of transverse Armco that used to cross the T1 runoff, now a marshal opening (§4b-steps) |
| `CAM_PITEXIT_WALL.png` | down the Beat-4 pit-exit road at route t = 120, where `BR_Concrete_L13` stood 0.36–1.01 m above the tarmac. The wall now begins at the merge |

The test harness adds a **stand-in racing surface** (`BR_TESTPROXY_track`) so the frames
read as a circuit. It is no longer set dressing: it is built from `C.ground_z` out to
exactly `C.verge_edge(s)` on both sides, i.e. it is what `build_surface` is contractually
obliged to hand over, minus its kerbs and its racing-line micro layer. That makes every
one of these frames a test of the seam. There is no verge/grass proxy any more — the
ground from `verge_edge` to `platform_edge` is this module's own geometry now, and if it
is missing the frame should say so.

**The light is the contract's**, not the harness's: `C.SUN_ENERGY` 115.754 at
`C.SUN_COLOR` (1, 0.71632, 0.38712), `MULTIPLE_SCATTERING` sky at aerosol 0.45 / ozone
1.30, `sun_disc` off, AgX at `C.REFERENCE_EXPOSURE_EXTERIOR` = −3.048, Look = None. The
old rig here (1.45 W, `dust_density` 2.2, an assumed 12.5°) was exactly the class of
private lighting that put `build_terrain`'s turf 45 % out on key : fill.

---

## Defects found by rendering, and fixed

Logged because they are the kind of thing that silently survives into a master:

1. **Procedural textures turned to mud on every ground surface.** Materials were driven
   from `Geometry > Position`, i.e. *world* position, at |P| ≈ 1000 m; a ×90 gravel voronoi
   evaluates at 10⁵ where float32 has ~6 mm of precision, so the gravel rendered as smeared
   wet clay with rainbow speckle. Fixed by recentring every object in `MB.emit` and moving
   every material to `TexCoord > Object`.
2. **TecPro rendered brown-grey instead of blue.** Its grime gradient read object-space Z,
   which after recentring (and, before that, at T4's z = −3.2 m) is not "height above the
   block". Fixed by carrying height-above-base in UV.v for TecPro and concrete alike.
3. **Rust saturated to 100 % everywhere.** The rust mask multiplied out to ≥ 1.0 for any
   age above ~0.4, so 3.7 km of barrier was uniformly rust-brown and read as varnished
   timber. Retuned to a patchy 0–0.85 with a real threshold, and the galvanised base
   darkened; rust now appears in streaks, which is the point.
4. **Car-paint transfer 4 m up a fence post.** The wear field is a function of station
   only, so a livery smear landed on everything at that station. Gated by UV.v against
   car-contact height.
5. **Rail ends left a sawtooth silhouette** wherever a run terminated — the four swept
   strips of the W-beam were open. Capped.
6. **Dents scalloped the rail every 2 m** because the post-bay modulation went to zero at
   each post. Reduced to ±45 %, so a 20 m hit reads as one deformation, not corrugation.
7. **An 8 m fence gap at every 260 m chunk boundary** — the span crossing the boundary
   belonged to neither chunk. Fixed with a ghost post so the earlier chunk owns it.
8. **Armco was being built along the concrete pit wall and across the open pit-exit apron.**
   `build()` now walks contiguous groups of `B_ARMCO | B_TECPRO3` only.
9. **Splice bolts drifted off the panel joints** (they were laid at a nominal 4.00 m while
   panel length jitters ±3.5 %) and sat on the hump crests rather than the W-beam's bolt
   valley. Both fixed.
10. **Livery paint transfer washed 22 m of TecPro uniformly red.** The smear used the same
    Gaussian width as the damage extent. A real transfer is a couple of metres of streak on
    a twenty-metre scar; the lobe was tightened to 0.24 × extent and the shader multiplier
    cut from 2.0 to 1.25.
11. **Scattered gravel stones floated or sank** because they read the bed height out of the
    surface grid by integer index, and the grid is non-uniform across the trap. The bed
    profile is now a single closure `bed(s, d, w)` evaluated by the surface *and* by every
    stone, so a stone is seated on its own bed by construction.
12. **The pit wall, the south pit-straight barrier and the doppler standoff missed their
    spec offsets by 1.5–3 m** because a margin term was added after the "pinned" width.
    Offsets are now frozen once in the corridor programme with smoothly-blended pins, and
    read back exactly: 11.5000 / 19.0000 / 30.0000 m. Still exact after the contract
    migration and after §4b's clamp — checked, because a clamp that quietly moved a spec
    pin would be the same class of defect this whole exercise is about.

### Found by the contract probe, in this migration

All of these were found by `render/world/barriers/verify_vs_contract.py`, which **raycasts
the emitted triangles** rather than re-evaluating the formulas that produced them. That
distinction is the point: a module that checks itself with its own arithmetic learns
nothing, which is how six modules each passed and the assembly failed.

13. **`BR_Verge_L` was 5.76 m above the datum over the T3 runoff.** The raycast found a
    surface at z = +5.08 where `C.ground_z` said −0.68. It was not a bad quad: it was the
    S4/T5 leg's own platform, because `C.barrier_offset` puts T3's outside barrier 66.9 m
    out and the circuit passes itself at 51 m. See §4b — this is the contract defect, and
    the probe is what surfaced it.
14. **Smoothing the barrier line dragged half the lap.** The first version of §4b's clamp
    smoothed the barrier line itself; `barrier_clamp_report()` then showed 67 % of the left
    and 55 % of the right clamped by a mean of 1.8–4.2 m, because the running-min was
    eating the contract's own ±1.2 m margin wander. Smoothing the *deficit* instead leaves
    `C.barrier_offset` bit-for-bit intact wherever nothing bites: 13.6 % left, **0.0 %
    right**.
15. **Every TecPro back-row block passed 59 mm through the Armco it is bolted to** — 3763
    triangle intersections on the BVH gate. The 0.02 m standoff put the block's rear face
    at −0.020 against a W-beam track-side face at −0.079. `TP_STANDOFF = 0.10`.
16. **The corridor gate posts stood inside the terminal tyres** of each tyre-wall run, 34
    triangle intersections. Moved 0.75 m into the opening and 0.32 m back.
17. **The fence-post base pads floated.** The pad sat 2 mm above the *barrier line*, but
    the post stands 0.31 m outboard of it where the platform is ~20 mm lower, and at a
    12.47° sun a 20 mm float is a 90 mm lit gap. The pad is now 90 mm thick and seated
    65 mm into the platform.
18. **The graded strip under the barrier did not settle with the barrier.** `History.align`
    sinks a maintenance run up to 57 mm; the ground under it did not move, so the barrier
    stood in a trench in some runs and proud in others. `platform_z` now reads the same
    field, so the barrier stands exactly 14 mm above its own shoulder everywhere by
    construction — which is what took `ground − foot` to a p95 of ±40 mm.
19. **A ray cast exactly on a mesh's free edge misses on a coin flip.** The first weld
    measurement reported 41 % misses and ±7 m errors at `platform_edge` that were not
    there: the ray fell through the boundary triangle and hit the sub-base underneath.
    Sampled 20 mm inside instead. Logged because it is a *probe* defect, and a probe that
    lies in the pessimistic direction is only luckier than one that lies the other way.
20. **A 48 mm-wide gravel bed was a 0.24 m-deep slot** against the painted verge, measured
    at the verge weld at s = 2128.7 as a −0.240 m step. `trap_depth_profile` shortened its
    ramps for a narrow bed but kept the full amplitude, so a bed still reached 0.24 m in
    the middle however narrow the tip was. The amplitude now scales with the width too:
    below 2.6 m a bed is a scrape, which is what a tapering bed edge actually is.
21. **A 40 mm sliver between the platform edge and `corridor_rim`** where a runoff taper
    makes `platform_edge` shed 1.55 m of lateral per metre of station (the end of the T1
    ramp). The mesh's outer row is a chord across a curve; at 1.9 m spacing that is 40 mm
    of lateral error. Found by a dense 20 mm probe around the single coverage miss —
    which is why the probe re-tests every miss over a 1.2 m patch instead of counting it.
    `_platform_ds` now also caps on `d(platform_edge)/ds`.

### Found by rendering under the contract's light, which is the point of using it

22. **`banked_runoff` rendered as a featureless grey field.** The camera was built by
    adding world-axis offsets to a station point, which put it 21 m above the runoff
    looking straight down at it from 30 m — nothing of the banked section in frame at all.
    All four contract cameras are now placed in `(station, lateral, side)`, and the
    camera-vs-geometry probe reports what each one's first hit actually is, so a camera
    that frames the inside of a mesh cannot pass as a render again.
23. **The verge was covered in 3 m pink and mauve blotches.** A Voronoi's socket 1 is
    COLOUR — a random RGB per cell — and it was being mixed in as a colour at 30 %
    strength. Cell randomness is now only ever taken as a scalar (distance, or the colour
    run through a black-to-white ramp), so the palette is the one written in the ramps.
24. **The verge read as a hard-edged polygonal patchwork at 20 m**, because 55 % of the
    bump came straight from a Voronoi F1 distance, whose cell borders are discontinuous.
    Now 52 % fine blade grain, 30 % a `pow(d, 0.55)`-softened clump, 18 % patch noise, and
    the bump distance dropped from 20 mm to 14 mm.
25. **The drought field was gained ×1.55 and clamped**, which pinned most of the lap to
    full drought and made the whole verge one straw palette — it measured R > G for
    something that is supposed to be grass. Re-centred through a MapRange, no gain.
26. **Two materials were not the albedo they claimed**, measured against the reference
    patches: the verge at 0.094 against an intended 0.135, and the runoff asphalt at
    **0.167** — light-concrete bright — against a real unrubbered runoff asphalt's
    0.10–0.14. Both retuned; all five ground materials now pass. This is the defect class
    `build_terrain` §2.1 shipped, and it is only findable by measuring against a published
    light rather than by looking at a frame.
27. **The verge went saturated cyan at grazing incidence.** All four ground materials were
    left at the Principled default 0.5 specular level, and at a 12.47° sun *every* ground
    plane is seen at a grazing angle for most of every frame — Fresnel then throws the
    whole blue sky back at the lens. It showed as a cyan band behind the T1 gravel trap,
    which is not a colour grass has. `NG.spec()` sets the level **by name** (the Principled
    input indices move between Blender versions; it is 14 in 5.2): turf 0.10, runoff
    asphalt 0.22, gravel and stone 0.16.

---

### Found by the assembly review, and by re-measuring what the fix for it did

29. **The fix for the corridor-ownership clamp put a barrier across the racing surface.**
   §4b's deficit smoothing, subtracted from a `C.barrier_offset` that steps 51.99 m in one
   metre at s = 905, produced an offset of **−18.80 m** — 18.8 m past the centreline.
   Three-beam Armco and a 3.6 m debris fence stood wall-to-wall across the T4 hairpin
   braking zone for 53 m of lap. Replaced with a cone erosion of the *clamped* line in
   clearance-above-the-verge, blended in only where the clamp bites, with
   `offset − verge_edge ≥ 1.000 m` as an import-time assertion rather than a hope.
   **This is the one to remember: a local fix that is not measured against the assembled
   world is a defect with a good reason attached.**
30. **All 16 marshal gates were built at their design coordinates.** `build_gate` was the
   only emit path in the module that did not wrap its vertices in `W3`. A gate 26 m from
   its own barrier still renders as a gate, so nothing in isolation caught it; the assembly
   review caught the one that happened to land on the T6 racing surface
   (`BR_FenceStruct_R07`, 3.756 m inside the track edge). Found by asking, of the *world*
   position of every structural vertex, "which station owns you, and are you inside
   `verge_edge` there" — which is a question no per-object test can be fooled by.
31. **658 m² of the road corridor had no ground**, because terrain cut a superset of the
   corridor and this module built a subset of it. Both were individually right. Closed by
   deriving the platform's reach from the *same* swept-segment test terrain cuts with, and
   extending to `C.platform_edge` exactly where the annulus is void and the extra sheet is
   provably buried (§4c).
32. **The pit wall stood in the pit-exit road** for 18 m, because a spec pin at circuit
   y = +11.5 and a merge arc that converges on the pit straight are both correct and meet.
   The wall now starts at the merge (§4c-veto).
33. **314 m² of the pit-straight platform band was coplanar with `SURF_AccessRoad`'s
   gore** — nobody's probe had scanned that band, because the Beat-4 checks scan the ribbon
   and the lap checks scan the corridor, and this is the strip that is both. Found by
   scanning this module's own band against `C.in_access_ribbon` while fixing defect #5.

### The three gates, on this build

```
blender -b world/br_fix.blend --factory-startup -P tools/placement_gate.py -- \
    --out render/world/barriers/placement_report.json \
    --allow "SURF_,TER_Ground,BR_Runoff,BR_Gravel,BR_Verge,BR_Subbase,BR_Trap,BR_Stones,..."
```

| gate | result |
|---|---|
| `tools/placement_gate.py` | **PLACEMENT_CLEAN** — 99 objects, 3 keep-out volumes (road corridor 3 666 stations at half-width 7.00–8.50 m, car path 1 743 stations at 1.60 m, camera path 25 keys at r = 1.20 m). *Nothing is on the road, in the car's path, or in the camera's path.* The `--allow` list needs `BR_Subbase`, `BR_Trap` and `BR_Stones` adding to its default: those are the gravel beds, their stones and the platform sub-base, i.e. ground, and the default list only names `BR_Gravel`, which is a **collection** name and not an object prefix |
| `tools/collision_gate.py` | **COLLISION_CLEAN**, but *vacuously*: it tests object clusters against the environment and a barriers-only blend has no clusters. The real triangle-level test for this module is `verify_vs_contract.py`'s `interpenetration` block: tyre walls × corridor wall **0**, tyre walls × platform **0**, corridor wall × platform **0**, Armco × TecPro **0** — over 1.13 M × 2.86 K and 1.54 M × 1.20 M triangles |
| `tools/depth_probe.py` | not applicable to a barriers-only blend for the same reason — it measures the car's penetration depth per frame |
| `verify_vs_contract.py` coverage | **43 878 samples, 0 holes (0.0000 %)** across the whole corridor, both sides, 37 laterals × 613 stations, probing the band this module actually lays (`platform_inner` → `platform_reach`) and excluding the ribbon at the contract's own saw margin |

## Known limits, and what is handed on

* The weave crimp is analytic, not geometric, everywhere except the doppler window's
  vertical wires. See the arcminute argument above.
* Gravel below 11 mm is shader, not geometry. If a later beat puts the lens closer than
  ~0.6 m to a gravel bed, raise the hero tier for that bed and re-run — the bed grid
  spacing and stone density are single constants.
* **`world_contract.barrier_offset` needs §4b's ownership clamp.** Until it has one,
  `build_dressing` must read `build_barriers.barrier_offset` / `build_barriers.owned_edge`,
  or it will stand marshal posts and ad boards under the S4/T5 racing surface for 400 m of
  the lap. This is the top item handed back to the contract author.
* **`world_contract._Corridor` publishes a discontinuous barrier line.** Five stations
  where `C.barrier_offset` moves 8.6–46.3 m in one metre (§4b-steps). The cause is
  fixable in one place: `_build` applies the pit-straight override as a hard boolean on
  `pit = (s >= 3115) | (s <= 250)` and box-filters a `1e6` sentinel in `maxoff`. Ramp
  both, and the T4 cliff that produced the review's defect #1 (51.99 m at s = 905) goes
  with them. Until then this module builds no barrier across the jump and reports each one
  by name in `ribbon_report()['*']['step_break_ranges']`.
* **`build_architecture` must pave the pit-exit apron** outward from `C.verge_edge` where
  `C.apron_zone(s, +1) > 0.5`, per its own migration note. This module cuts 6 640 m² there
  because contract §7 says that surface is architecture's; if architecture does not build
  it, it is a hole at the exact place Beat 4 merges. Note that `C.world_ground_z` names
  `build_barriers` the owner of that ground (priority 3, `|u| <= platform_edge`) while
  `C.platform_owner` names `build_architecture` (contract §7) — **the two disagree**, and
  the review's `void` probe found 3372–3426 empty. This module follows §7 and
  `apron_zone`, because architecture demonstrably *does* build there
  (`ARCH_Paving_ApronPlatform`, 5 811 m², assembly defect #3). One of the two contract
  functions has to move; whichever it is, both modules must read the same one.
* **`build_terrain` must weld to `build_barriers.platform_reach`, not `C.platform_edge`,**
  through s 701–915 / 916–1213 on the left. `platform_reach` is `C.platform_edge` over
  99.5 % of the lap *and* over the whole of the stretch where the void was; where it is
  not, it is the medial axis, which is where the two branches of the corridor actually
  meet. Everywhere else the two are identical to 0.000 m.
* ~~**`telemetry.csv` and `world_contract.access_route_point` do not agree through the
  Beat-4 merge.**~~ **CLOSED 2026-08-02 by R2-042.** It was real: the car's driven line sat
  on the route centreline for the first 45 m, then swung out to **+8.95 m** at route
  t 96.6–107.5. The cause was `tools/build_telemetry.py` integrating the declared
  R150 / 40° merge as a **straight chord** between the four leg endpoints, against its own
  file header's analytic-geometry policy; a 104.7 m arc of R150 stands 9.04 m off its own
  chord. `docs/R2-042-DECISION.md` ruled for the arc and the telemetry moved, not the
  contract — `ACCESS_R` / `ACCESS_ARC_C` did not change. telemetry.csv now reproduces
  `access_route_arrays` to **8.83e-05 m**. The symptom fix here (`transit_wall_offset`'s
  correction table) has been deleted; see defect #6.
* **`build_dressing` does not get the barrier veto.** It reads
  `world_contract.COR.sample("btype"|"fence", …)`, not `build_barriers.COR`, so it will
  still place marshal posts, tyre stacks and boards on the barrier line inside the pit-exit
  road (s 3406–3464 left) and across the five contract steps. One call to
  `build_barriers.barrier_blocked(s, side)` fixes it.
* **26 m² of the corridor is still void**, down from 658 m². 20 m² of it is s 916–920,
  where the annulus is void *and* the covering branch's ground is within 0.10 m of ours, so
  filling it would trade a hole for a coplanar pair; 6 m² is three isolated single samples
  (s 678, 1262, 3114) at the exact lateral where two branches' rims meet. Both are
  `world_contract`'s corridor self-intersection showing through, and both go when
  `C.platform_edge` stops reaching 73 m across another leg of the circuit.
* **`placement_gate.py`'s `--allow` default is stale for this module**: it lists
  `BR_Gravel` (a collection) but not `BR_Subbase`, `BR_Trap` or `BR_Stones` (the objects).
  With the default list the gate reports 11 false positives, every one of them ground that
  is correctly placed — measured min |u| 9.43–10.50 m against a corridor limit of
  7.50–8.50 m.
* The `ARMCO_TOP` clearance under a 2-beam run is 31 mm at the worst settled node. That is
  a real gap under a real barrier and it is meant to be there; if a later beat puts a lens
  under an Armco, check it rather than assuming.
