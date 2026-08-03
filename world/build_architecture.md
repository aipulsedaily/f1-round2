# build_architecture.py — the built environment

Pit building + garage row, start/finish gantry, pit wall + pit-wall stands,
grandstand blocks **and their terrace**, the paddock (concrete, buildings,
transporter park, service ground, furniture, fencing, lighting), the **pit-exit
apron platform**, La Passerelle and Le Pont de la Plongée.

```
/opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P world/build_architecture.py
   ... -- --render beat4_route,paddock_eye --res 1920x1080 --samples 96
   ... -- --save world/arch_probe.blend --cams beat4_route,beat4_low,paddock_eye
   ... -- --save ... --noproxy      (no contract proxies, geometry only)
```

`build()` is idempotent — it deletes the `ARCH` collection tree, its meshes and
its `A_*` materials before rebuilding — and returns a summary dict. It exits
non-zero if either gate fails. Nothing in `build()` creates a camera, a light, a
world or a ground plane.

---

## 0. THE CONTRACT

**`world/world_contract.py` is authoritative over this file** — built and
verified against **v1.0.1**. It is imported as `WC` at module load and its
version is asserted. Everything two or more modules must agree on is imported,
never re-derived:

| what | where it comes from now |
|---|---|
| ground height, anywhere | `WC.world_ground_z(x, y)` → `(z, owner)` |
| who owns a square metre | the same call's `owner` string |
| the declared z = 0.000 platform | `WC.APRON_REGIONS_CIRCUIT` + `WC.FORECOURT_WORLD` |
| the outboard limit of the road programme | `WC.platform_edge(s, side)` |
| the pit wall line | `WC.PIT_WALL_Y`, `WC.barrier_offset(s, +1)` |
| the access ribbon | `WC.access_edges` / `WC.access_z` / `WC.access_project` |
| **the ribbon's start cap** | **`WC.ACCESS_RIBBON_T_MIN` = 0.0** — the breach plane, world x = 15.000. The margin is lateral and only lateral |
| **the track / apron joint** | **`APRON_JOINT_LAP_M`** = 0.050, `getattr(C, …, 0.050)`, the same expression `build_surface` uses |
| the Beat-4 corridor | **not ours** — `WC.CORRIDOR_OWNER` = `build_barriers` |
| embedment of anything standing on the ground | `WC.BASE_EMBED_M` = 0.020 |
| tolerances | `WC.TOL_SEAM_M` 0.010, `WC.TOL_COPLANAR_M` 0.030 |
| the light every material is calibrated against | `WC.SUN_*`, `WC.SKY_*`, `WC.lambert_radiance` |

`build()` writes `WC.summary()` onto the `ARCH` collection with `WC.stamp()`, so
a finished `.blend` records which contract it was built against.

### The five module-level primitives everything else is built on

```python
clear_c(cx, cy)     # >0 where architecture may pave.  min(|u| - platform_edge,
                    # ribbon clearance).  ONE predicate, from contract calls only.
apron_clearance(s,u)# the same, for the pit-exit apron, in (s, u).  AT MODULE SCOPE
                    # so build_apron_platform and verify_contract cannot ask the
                    # question two different ways -- which is the failure mode
                    # this whole review round exists to close.
_r1_shell_clearance # >0 outside the round-1 pavilion shell, world frame
cut_bays(bays, f)   # saw a list of axis-aligned bays to the curve f == 0
sit_c / sit_w       # scalar ground height for standing one object on
_owned(pts)         # the same test, for markings and object placement
cull_unowned()      # the machine backstop: delete any up-face left on somebody
                    # else's ground.  Runs after every builder.
```

---

## 0b. ROUND 2 OF THE REVIEW — the two defects this module owned, closed

The integration round fixed the world. The **assembly verification** then rendered
it and found five more. Two were mine, and both were the same mistake in two
places: **a surface that stops where another surface stops, with nothing
underneath.** Everything below is measured against the shipped build, and every
number is reproduced by `verify_contract()` on every build.

### Defect #2 — the corridor mouth at the glass plane had no ground

> 1 276 of 7 467 samples over world x 4…17, y ±14 had **no usable ground** —
> ~64 m², a continuous 3.0 m band across the whole 12 m driving width, of which
> **x 14.700…15.000 was FULLY OPEN**, 0.300 m × 12.75 m. `CAM_GLASS_GAP.png`
> shows a black slot with this module's forecourt sub-base behind it as an open
> coffered eggcrate with no top faces. This is the Beat 3 → Beat 4 hinge.

Three separate faults, and only the first was the one named:

| # | fault | fix |
|---|---|---|
| a | `clear_c` carried a **longitudinal** `-RIBBON_SAW_M - t` term, so the paving was cut 0.30 m *behind* the breach plane while `build_surface`'s ribbon began *on* it | the cut is `RIBBON_T_MIN - t`, read from **`C.ACCESS_RIBBON_T_MIN` = 0.0** (world_contract 1.0.1, whose docstring names this module: *"a module that keeps its own `-saw - t` term reopens the slot on its own side"*). The paving cut line is now measured at **x = 15.0000** every build |
| b | the sub-base was `prism(..., top=False)` — an open box on a 6 m grid, which is literally what the frame shows | **closed, in two levels.** Outside the pavilion, bedding at **−0.012**; under it, a closed formation slab at **R1_FORMATION_Z = −0.100** |
| c | the pavilion footprint the bays were cut around was **invented** — `(-19.15, 15.05, -13.15, 13.15)` — 4.15 m too big to the west and 2.15 m too big in y, leaving an unpaved ring nobody built | **measured** from `opus5-car-render/f1_showroom.blend`: `Floor` x −15…15, y −11…11, z −0.060…**0.000**; `Wall_BackX` x −15.25…−15; `Wall_SideY` y 11.00…11.25; glass at x = **15.000**. `R1_SHELL` is that plan |

**Why the mouth is a formation slab and not paving.** Round 1's `Floor` has its
finished level at **z = 0.000 exactly** — the same plane as `C.APRON_Z`. Laying
forecourt bays under it would be a **30 × 22 m coplanar z-fight in the frame the
camera breaches the glass**, which is the defect this entire round exists to
close. So the mouth gets the slab that floor is cast on: 100 mm below its
finished level, **40 mm below its soffit**, closed on every side.
`build_surface` reached the same conclusion independently and reported it rather
than building it. This module builds it, because a closed slab 100 mm down is
ground and an open coffer is not.

**Measured, 5 mm ray profile across the mouth, ARCH + contract proxies:**

```
y = 0.0, 3.5   x 11.000→15.000  ARCH_Paving_Forecourt  z = −0.1000   (formation)
               x 15.000→        PROXY_AccessRibbon     z =  0.0000   (build_surface)
y = 6.5, 9.5   x 11.000→15.000  ARCH_Paving_Forecourt  z = −0.1000
               x 15.010→        ARCH_Paving_Forecourt  z = +0.0002   (bays)
y = 11.6,12.5  x 11.000→        ARCH_Paving_Forecourt  z = +0.0002   (bays, whole width)
```

No terrain anywhere in the mouth, no gap at any y, and the 10 mm at x 15.000…15.010
is the bay grid's own 12 mm saw joint, **12 mm deep** onto the bedding.

A fourth fault surfaced while fixing (c) and is worth recording because it was
25 mm wide and would have shipped: growing the shell by the 12 mm construction
joint on **all four** sides put the paving's east edge at x = 15.012 and opened a
**12–18 mm slot straight through to terrain** at 6.3 < |y| < 11.25. The +x face
is the breach plane; it carries **no allowance at all**.

### Defect #3 — a 12 mm open joint, 300 mm deep, down the whole pit-exit apron

> `SURF_Track` ends at u = 10.500. `ARCH_Paving_ApronPlatform`'s first bay starts
> at u = 10.512 because `build_apron_platform` insets every bay 12 mm from a grid
> beginning **exactly at `verge_edge`**. Between them the ray falls 0.300 m to the
> sub-base. Verified at s = 3247 / 3305 / 3361; 26 mm joints over the whole
> 5 811 m² bay grid. At a 12.47° sun that is a black line down 220 m.

Reproduced here before touching anything — at s = 3247, u = 10.500…10.510 the ray
landed at **−0.4172**, i.e. **300 mm** below a datum of −0.1172, and the first bay
appeared at u = 10.515. Four faults:

| # | fault | fix |
|---|---|---|
| a | the u grid origin was `verge_edge.min()`, and on the pit straight `half_width` is a **constant 8.000**, so that IS `verge_edge` at every station — the grid line and the cut line were the same line, and the 12 mm inset survived | `APRON_GRID_INSET` = 4.5 m: the origin is a bay and a half **inboard**, so the first column always straddles and is always sawn. That is exactly why `ARCH_Paving_Paddock` never had this defect — its rectangle edges are nowhere near its cut line |
| b | two meshes both stopped at `verge_edge` and hoped | `build_surface` laps: `SURF_ApronJoint` carries the asphalt edge outboard as a real recessed sealant joint. This slab now **begins on the outer end of that lap**, `APRON_JOINT_LAP_M` = 0.050, read from the same `getattr(C, "APRON_JOINT_LAP_M", 0.050)` expression the neighbour uses, so the two track each other |
| c | the sub-base was one down-facing quad 300 mm below the datum | **bedding**, closed, `APRON_SUB_CAP` = **0.035** under the datum, sawn with the bays' own predicate and running `APRON_BED_OVERRUN` = **0.150 m past it on every side** — deeper than `C.TOL_COPLANAR_M`, so it is buried under the neighbour rather than coplanar with it |
| d | the same 12 mm inset ran in **s**, opening the same joint at both ends where the apron meets `build_barriers`' runoff | the ends are sawn on **`C.apron_zone == 0.5`**, which is exactly where `C.platform_owner` hands the surface over |

and the bay joint itself went **24 mm → 8 mm** (`APRON_BAY_JOINT` = 0.004), which
is what a sawn joint in cast concrete is.

**Measured, 1 mm ray profile across the joint, three stations:**

```
u − verge_edge   what the ray lands on          depth below C.ground_z
  −0.150…0.000   PROXY_RoadCorridor (track)      0.5 … 1.1 mm
  +0.001…0.007   PROXY_ApronJoint  (ramp in)     0.6 … 4.4 mm
  +0.007…0.026   PROXY_ApronJoint  (sealant)     4.4 mm
  +0.026…0.032   PROXY_ApronJoint  (ramp out)    3.6 … 1.6 mm
  +0.032…0.050   PROXY_ApronJoint  (the lap)     1.6 mm
  +0.050…        ARCH_Paving_ApronPlatform       0.0 mm      ← the slab
```

Continuous, at every station, at 1 mm. **Deepest point anywhere across the joint:
4.4 mm, against 300 mm before.**

### Two things this round proved that a measurement alone would not have

**1. The cut primitive was blind to a ridge.** `cut_bays` dropped any cell whose
four corners were all outside — but a cell can hide a *positive strip through its
middle*. Past s = 3390 the R150 ribbon eats the apron from outboard while the
joint lap holds the inboard edge, and at s = 3398 the feasible strip is **0.75 m
wide inside a 3.0 m bay whose corners are all negative**. Three 293 mm holes,
found by the sweep. A cell is now only dropped when its best corner is further
outside than the cell is wide — a sound test for a signed distance — and split
otherwise.

**2. The render found what the sweep could not.** Splitting deeper to catch that
ridge made every leaf 0.093 × 0.075 m = 0.007 m², under the flat 0.03 m² minimum
fragment area, so **every clipped fragment near a boundary was thrown away**: a
**0.28 m wide strip of finished slab vanished down the entire apron edge** — and
the ray sweep still passed, because the bedding underneath is only 35 mm down.
The 4K frame showed it immediately as a 46 mm blue shadow trough. Two changes
came out of that: the minimum fragment is now **2 × 10⁻⁵ m²**, and the gate has a
second question — **"is the thing you land on the finished slab, or its
bedding?"** — bounded at 3 % of columns more than 20 mm low, against a joint area
of ~0.6 %.

### The project keep-out gate, and one thing it finds that is NOT mine

`tools/placement_gate.py` on the ARCH test blend, ground surfaces allowed
(`--allow SURF_,TER_,PROXY_,ARCH_Paving_,ARCH_Markings`):

```
tested 25 objects; 23 measured per-vertex
2 PLACEMENT VIOLATIONS
   car_path   ARCH_RetainEdge   1.198 m in   at (138.431, 27.140, -0.179)
   car_path   ARCH_PitWall      1.067 m in   at (144.282, 29.425, +0.200)
```

**Both are byte-identical, to the vertex, in `arch_probe.blend` — the build from
before this round.** They are pre-existing, they are the pit wall / ribbon merge
conflict this note has flagged since §6, and neither object is touched by any
edit in §0b: `build_pit_wall` and `_retain_run` call neither `clear_c` nor
`cut_bays`. Both points sit at s ≈ 3437–3443, u ≈ 11.4–13.5 — the pit wall's
contract pin at circuit y = +11.5 against the R150 merge — so moving either is a
three-way negotiation with `build_surface` and `C.PIT_WALL_Y`, not a local fix.
**Recorded, measured, still open.**

A third violation in that list *was* mine and is gone: `--factory-startup`'s
default **`Cube`**, a 2 m box at the world origin, was being saved into every
test blend. `_test_env()` now deletes the startup Cube / Camera / Light.

### The joint, measured in the rendered frame

`arch_apron_macro.png` vs `arch_apron_macro_BEFORE.png`, identical camera, 4K,
640 samples, the contract's own 12.47° sun 97 % across the joint, 1:1 pixels:

| at 4K, four columns | BEFORE | AFTER |
|---|---|---|
| darkest pixel in the joint ÷ adjacent concrete | **0.000** – 0.092 | **0.239 – 0.258** |
| pixels below 15 % of the concrete | 2 – 4 | **0** |
| what it is | a 12 mm crack with 300 mm of nothing behind it | a 50 mm sealed construction joint |

**There is no black pixel in the joint any more.** It is wider, because a sealed
asphalt-to-concrete joint is 50 mm wide and a crack is 12 mm, and it is grey-blue
(sky-lit) rather than black.

---

## 1. What the assembly review found here, and what each fix actually is

### Finding #2 — Beat 4 was a coplanar z-fight for its whole length

`SURF_AccessRoad`, `ARCH_Paving_Paddock`, `ARCH_Paving_Apron` and `ARCH_Markings`
all covered the same 116 m at separations of **1.4–9.0 mm**, and the winning
surface flipped **six times**. The old `build_surface.md` named the fix — "the
paddock builder should cut around the ribbon rather than overlap it" — and this
module did not do it.

It does now, and not by an offset. Every paving bay, every sub-base panel, every
marking segment, every slot-drain unit, every cable-duct unit and every loose
object is tested against `clear_c()` and **sawn to the curve** where it straddles.
A bay that straddles is quartered recursively to ≤ 0.75 m before the crossing is
taken linearly; at the ribbon's R150 the sagitta of a 0.75 m chord is **0.47 mm**,
against a 10 mm seam tolerance.

Three separate things had to be cut that a first pass missed, each caught by the
gate rather than by inspection:

* the **sub-base** was one box across the whole rectangle with its top at −0.014,
  which put a lit ledge 120 mm above `C.ground_z` right across the road corridor
  for 375 m;
* the **forecourt sub-base** did the same at −0.010 across the ribbon — that is
  the pair the Beat-4 scan line caught at world x 15+;
* the **slot drains and cable ducts** ran as single boxes the length of each
  region, crossing the ribbon at −26 mm and −20 mm, which is inside
  `TOL_COPLANAR_M`.

Measured now, on the review's own scan line (world y = 0, x −5…+111, 0.25 m):

```
build_architecture:paving  ->  build_surface:SURF_AccessRoad
                           ->  build_architecture:paving  ->  build_surface:SURF_Track
3 ownership changes.  0 coplanar samples.  One surface at every point.
```

### Finding #3 — the Beat-4 corridor was built twice

`ARCH_ApronCorridor` is **deleted**, not shortened. `_assert_no_corridor()` raises
if anything named in `WC.CORRIDOR_DELETE_NAMES` exists after a build, and the
contract gate checks it again.

The arithmetic in the old comment here was not wrong — at its `s = 90` the south
wall really did land on the racing surface. The contract reached the same wall by
measurement and answered it better than this module did: north wall `t` 6→96
(90.0 m, the spec literal), south wall 6→90 (84.0 m, terminated with 1.74 m of
verge still in front of it), both starting at world x = 21.0 to clear **this
module's** bollard line at x = 19.5. Shortening the whole corridor to 70 m threw
away 20 m of the camera's walled run to fix a problem only the south wall had.

### Finding #1 — the ground datum

Nothing in this file computes a ground height any more. Everything that touches
the ground is placed with `WC.world_ground_z` and embedded by `WC.BASE_EMBED_M`.
What that changed, measured:

| element | was | is | error it removed |
|---|---|---|---|
| **pit wall**, 375 m | base z = 0.000, face at circuit y = +11.325 | base −0.171…−0.144, face **on the contract pin +11.500** | hung **130–171 mm clear of the ground** for its whole length; face 175 mm inboard of `barrier_offset` |
| **gantry legs** | pad −0.40…+0.45 about z = 0 | about `C.ground_z` = −0.138 | 138 mm |
| **La Passerelle south tower** | columns from z = 0.000 | from `C.world_ground_z` − embed, on a cast raft | **325 mm** — it stands on `build_barriers`' runoff platform, not on the paddock |
| **Le Pont de la Plongée** | `zr = 3.913` copied out of the PVI table, origin hard-coded (−617.56, 94.75) | `WC.elevation_c(2410)` = 3.9129, origin `WC.centreline(2410)`, abutment tops `WC.ground_z(2410, ±15)` = +3.984 / +3.548 | the two abutments differ by **436 mm** and were both drawn level |
| **pit-wall stands** | feet at circuit y = 11.9, z = 0 | y = 12.25 (= `platform_edge` + 0.15), z = `APRON_Z` | 135 mm, and they stood 0.2 m inside the road corridor |
| **grandstands** | fascia to −0.30 on ground nobody publishes | a **formed terrace**, §4 | undefined |

### Finding #5 — the light

`_test_env()` is now `WC.SUN_*` / `WC.SKY_*` / `WC.REFERENCE_EXPOSURE_EXTERIOR`
verbatim, and the first contract-lit frame immediately exposed a bug of ours: the
SUN lamp was aimed with `(-SUN_DIR).to_track_quat('Z','Y')`, which **buries the
sun below the horizon** — a Blender SUN emits along local −Z, so local +Z must be
the direction *to* the sun. The frame was shadowless and sky-lit. Fixed and
re-measured (§9).

---

## 2. The apron conflict the review did not reach

spec §10.7 declares the pit-exit apron as circuit **x −480…−245, y 0…+45**, and
y = 0 is the pit-straight **centreline**. Taken literally, architecture paves
10.5 m of racing surface. `ARCH_Paving_Apron` started at y = 9.5 against a verge
edge at 10.5: **a 1.0 m wide, 241 m long coplanar overlap at a 55–70 mm offset**,
a lit ledge down the whole main straight.

The contract resolves it inside `ground_z` as a real valley gutter, and assigns
the surface to this module via `platform_owner()`. So `ARCH_Paving_Apron` is gone
and **`ARCH_Paving_ApronPlatform`** replaces it: a sweep in `(s, u)` over the
stations where `WC.apron_zone(s, +1) > 0.5`, from
`WC.verge_edge(s) + APRON_JOINT_LAP_M` out to `WC.platform_edge(s, +1)`, sawn on
`apron_zone == 0.5` at both ends, with **every vertex placed by
`WC.su_to_world`** — so the concrete *is* `ground_z` and the datum cannot drift
by a micron. 5 894 m² of it on 6 019 m² of closed bedding (§0b, defect #3).
Measured across the tie at s = 3300:

```
verge edge  10.5 m : -0.122      (the crowned road edge)
            12.0 m : -0.132      (the gutter invert)
            16.0 m : -0.049
            18.5 m :  0.000      and 0.000 everywhere beyond
```

132 mm of rise over 8 m, 3.05 % maximum cross-grade. A gutter, not a step, and it
is where the drainage runs.

---

## 3. Where the platform stops, and the retaining edge

Paving is clipped to the **contract's** rectangles, not the spec's — the spec's
overlap the circuit. `ARCH_Paving_Paddock` used to run to circuit x −486…+104,
y 40.5…116; the declared paddock is x −480…+100, y 40.5…115, and the surplus was
ground `build_terrain` builds.

Where the platform meets the road corridor there is a real step: `C.ground_z` at
`platform_edge` is **up to 510 mm below `C.APRON_Z`**, and behind the pit wall it
is 138–150 mm below. The old build laid its slabs at 0.000 and simply stopped.

**`ARCH_RetainEdge`** builds what a paddock actually is: a cast edge beam, 439 m
of it, whose **top is exactly on `platform_edge`** — which is where the paving is
cut, so the beam and the slab share an edge instead of overlapping — with a face
battered 45 mm into the corridor, a heel deliberately **30 mm below the road
programme's own ground at its own lateral** so it is buried rather than laid on
top of somebody else's surface, weep pipes every fourth panel and a bollard
wherever the drop is over 280 mm. Where the drop is under 10 mm it emits nothing:
the sawn slab edge is the boundary.

Where the platform meets **terrain**, whose height this module is not allowed to
know, `_terrain_skirt()` runs a closed skirt 0.90 m below the deck with a kerb on
top, so `build_terrain` may weld anywhere in that band and the edge still reads as
a kerb rather than as a slab hanging in the air.

---

## 4. The grandstand terrace — a gap in the contract, handled and declared

The grandstand band is circuit y −34…−62, which is beyond
`WC.platform_edge(s, −1)` = 25.0 m, so `WC.world_ground_z` hands it to
`build_terrain` and returns **NaN**. This module is not allowed to know the height
there and must not guess it. But a grandstand does not sit on natural ground — it
sits on a formed terrace. So the terrace is built:

```
ARCH_Grandstand_Terrace   deck at C.APRON_Z, 816 sawn bays
extent (circuit)          x -426 .. +186,  y -69.0 .. -28.5
skirt                     1.85 m, CLOSED, battered 0.35 m, counterfort every 5th panel
concourse                 asphalt aprons front (y -34.35..-29.4) and rear (-74.6..-68.0)
```

**This is a required contract addendum.** `build_terrain` must treat that
rectangle the way it treats `apron_platform_mask`: build no ground inside it and
weld to its skirt. Until it does, the failure mode is bounded — terrain's own
`built` pad windows circuit y −70…+120 to z = −0.20, which the 1.85 m skirt
covers with 1.65 m to spare — but it is not *guaranteed* by anything, and it
should be.

---

## 5. Ground-level detail — the pass the aerial was missing

44 000 m² of concrete with nothing standing on it reads as a toy block from
240 m, and Beat 4 crosses it at rooftop height. Everything below is generated,
placed on `WC.world_ground_z`, rejected against the contract **and** against a
keep-out list of what this module has already committed to, and none of it is one
asset spammed: each family draws its dimensions, colour, wear, lean and contents
from its own seeded stream.

### 5.1 In the slab itself
* 5 601 individual bays, own 22 mm saw joint, own 0–2.5 mm level. **2 916 of
  them are sawn** to the corridor, the ribbon or the forecourt mitre.
* per-bay tone at **half** its first amplitude: the shader already hashes
  `floor(p / bay)` for ±13 %, and the first aerial frame showed the two layers
  compounding into a chessboard across 44 000 m² of 5 × 6 m bays.
* per-bay staining as five states — plain, fresh pour, old and polished, a bluer
  batch of cement, and (in the pit lane) a rubber-and-fuel shadow — plus 2.4 % of
  bays reinstated in asphalt over a service cut.
* recessed manholes, round or rectangular, with a modelled 14 mm rebate ring.
* **weeds and moss in the saw joints** on ~18 % of bays: the single cheapest thing
  that stops 44 000 m² of concrete reading as a shader test card.
* cast slot drains built unit by unit, one grating in seven sitting 16 mm low and
  one in eleven lifted and stacked beside the channel.
* cast-in cable ducts with bolted checker-plate covers, one in thirteen proud.

### 5.2 Standing on it
| family | count | what varies |
|---|---:|---|
| service road | 234 sawn segments | 1.6 % camber laid ON the platform (crown +70 mm, channel +6 mm), unit-by-unit kerbs with dropped crossings and gullies, reinstated trenches, 7 heavy rubber cable ramps |
| plant compound | 70 × 26 m | crushed hardcore with a modelled surface, 260 individually placed stones, Heras on three sides |
| furniture | 182 groups over 8 zones | skips (length, taper, colour, rubbing strips, wheels, heaped contents), wheelie bins (4 sizes, lid open/shut), flight cases (stacked 1–3, hardware, stencilled team panel), pallet stacks (2–9, each rotated, some shrink-wrapped), gas cages, cable reels (upright or laid flat), water tanks, gensets with cable tails on the ground, cone lines |
| fencing | perimeter + 3 internal runs | Heras panels, each with its own lean, 4.5 % missing, cast feet, banners on ~35 % |
| lighting | 11 masts | 4 heights, 3–6 heads on independent yaw, base enclosure on half |
| wayfinding | 8 finger posts, 4 fire points | 2–4 arms each at independent angles from an 8-destination table |
| hospitality decks | 5 | deck size, board width, board direction, board tone, 4–8 tables with 2–5 chairs each, parasols open / furled / absent, planters, drinks cabinets |
| planting | 48 paddock planters + 10 on the forecourt edge | every shrub generated: 3–6 stems, 2–4 twigs each, 9–18 **folded** leaves per twig on an ellipsoidal crown shell, own greens |
| jersey barriers | 3 runs | each unit placed with its own yaw and tone, 30 % carrying a brand panel |

### 5.3 New markings
The pit-wall edge line (with 13 % of segments scrubbed off), pedestrian crossings
from the wall stands to the garages, per-box equipment footprint outlines, the
service road's edge lines / centre dashes / direction arrows / 20 km/h roundels,
FIRE LANE KEEP CLEAR legends, and unit numbers on the hospitality frontage.

**Deleted, because they were `build_surface`'s:** the give-way triangles at
circuit y 8.4–9.6 (inside `verge_edge` = 10.5), and the transit route's chevrons
and PIT EXIT legend, which were painted straight onto `SURF_AccessRoad`.
`_owned()` is why they cannot come back: 100 marking segments are dropped per
build, by measurement rather than by intention.

---

## 6. The pit wall's west end — a second contract finding

`WC.access_edges` does not agree with `WC.barrier_offset`. Measured along the
route:

| route t | ribbon outboard edge, circuit | vs the pit wall face at y = +11.50 |
|---:|---|---|
| 120 m | (−248.2, +14.78) | — (west of the wall) |
| **124 m** | (−244.5, **+13.96**) | **2.46 m past the wall** |
| 132 m | (−236.9, +12.62) | 1.12 m past |
| 140 m | (−229.3, +11.68) | 0.18 m past |
| 144 m | (−225.5, +11.37) | clear |

and `WC.world_ground_z` hands circuit **x −245…−229 on the y = +11.5 line** to
`build_surface:SURF_AccessRoad`, not to the barrier line it also pins there.

A wall over those 16 m would stand in the middle of the pit-exit road, which is
also why a real circuit starts its pit wall **after** the exit merge. So the wall
starts at **circuit x = −228.0** with a modelled tapered terminal (7 stepped
lifts, a spread footing and a chevron board on the nose) instead of at the spec
literal −245. That is a deliberate 16 m departure from §10.7, measured, and it is
flagged here for the contract's author: either `access_edges` should clip its
**outboard** edge against `platform_edge` on the left of the pit straight the way
it already clips the inboard edge against `verge_edge`, or §10.7's wall extent
should be shortened in the contract.

---

## 7. The gates

Two, both run on **every build**, both fail the process with a non-zero exit.

### 7.1 `verify_contract()` — measured against the contract, not against myself

The review's single lesson is that six agents each verified their own work in
isolation. So this gate never asks whether the geometry is self-consistent; it
asks `WC.world_ground_z` **who owns the ground under every upward-facing face
this module puts near the platform**, and fails if the answer is anybody else.

| check | how it is measured | result |
|---|---|---|
| contract version | `WC.__version__` | 1.0.1 |
| the Beat-4 corridor is gone | `WC.CORRIDOR_DELETE_NAMES` in `bpy.data.objects` | none present |
| `ARCH_Paving` on nobody else's ground | 34 434 up-faces → `world_ground_z` owner | **0**, 1 577 legally buried |
| `ARCH_Ground` on nobody else's ground | 13 589 up-faces | **0** |
| `ARCH_Grandstands` on nobody else's ground | 1 938 up-faces | **0** |
| paving never proud of the datum | 24 469 paving-material faces, signed | **max +11.2 mm** (limit 17.5), deepest recess 335.7 mm, p50 −2.3 mm |
| **no open joint** — 7 fields, ray-cast down on ground `world_ground_z` gives us | **43 000 columns**: apron 9 000, paddock / pit lane / garages / terrace / forecourt 6 000 each, under-pavilion 4 000. Fails on anything deeper than `SUB_FORM_DZ + 4 mm` = **66 mm** | **0 everywhere.** apron p99 **7.8 mm**, max **42.8 mm**; paddock max 24.0; pit lane 24.0; terrace 16.0; forecourt 12.0; under the pavilion **0.0** |
| **the finished slab, not the bedding** | the same columns, fraction landing > 20 mm low, bound 3 % against a joint area of ~0.6 % | apron **0.66 %**, pit lane 0.95 %, paddock 0.47 %, the rest **0.00 %** |
| **the apron edge is a joint, not a shaft** | 1 393 columns at u = verge_edge + 1, 6, 12, 30, 51, 60, 250 mm, over 226 stations, skipping the stations the R150 ribbon owns | deepest **35.0 mm** (limit 66) — the bedding, once, at s = 3210 |
| **the ribbon start cap is the contract's** | `RIBBON_T_MIN` vs `C.ACCESS_RIBBON_T_MIN` | 0.000 == 0.000 |
| **the paving cut line IS the glass plane** | 60-step bisection of `clear_c` on the route centreline | **x = 15.0000**, `access_ribbon_polygon(0.30)` starts at 15.0000, `C.ACCESS_GLASS_X` 15.000, terrain's mask reaches 15.000 |
| Beat-4 has one owner at a time | 465 samples, world y = 0, x −5…+111 | 3 ownership changes |
| no ARCH mesh coplanar on the Beat-4 route | ray-cast down at each sample, compared to `world_ground_z` against `TOL_COPLANAR_M` | **0** |
| **no two DIFFERENT ARCH objects coplanar** | 9 000 columns, **cast against every ARCH object separately** so an exact coincidence is visible, pairs < 2.5 mm | **1 of 9 000 = 0.011 %** (bound 0.05 %), named in the gate output every build |
| intra-object coplanarity | the same sweep, same object either side | **0 of 9 000** |
| paving inside the declared rectangles | 24 175 flat-plane faces vs `WC.APRON_REGIONS_CIRCUIT` | **0** outside |
| the lighting reference | `WC.lambert_radiance(0.18)` | (1.6744, 1.4600, 1.3321) |

**The two open-joint checks are the ones this round added, and they are a pair on
purpose.** The first asks *is there anything under me* and the second asks *is it
the finished surface*. The first alone passed a build in which a 0.28 m strip of
slab had vanished down the whole apron edge, because the bedding 35 mm beneath it
answered "yes". Neither is a substitute for the render, which is what found that
one; both exist so it cannot come back silently.

**The self-coplanarity sweep is the one the renders forced into existence**, and
it had to be built twice. The contract's rule for finding #2 — *cut, do not
offset* — applies inside a module as well as between two, and the first
contract-lit frames showed a patch of apron rendering as shattered concrete.

The first sweep stepped one ray down through the scene, restarting 0.1 mm below
each hit. **That cannot see two surfaces at the same z** — the next ray starts
below both — which is exactly the case that renders as shattered concrete. It
reported 15 columns while the frame showed thousands of square metres of the
defect. The sweep now casts against **each object separately** and sorts the
answers, so an exact coincidence is a pair like any other. Cost: 31 casts a
sample instead of 6, and it finds what the renders find.

What the corrected sweep proved is worth recording precisely, because it is the
opposite of what it looked like: the shattered apron was
**`PROXY_RoadCorridor` against `ARCH_Paving_ApronPlatform`, exactly coplanar over
5 800 m²** — a bug in this module's own *test scaffolding*, which meshed
`C.ground_z` across the whole corridor including the band `C.platform_owner()`
awards to this module. The shipped geometry was correct the whole time. The proxy
now stops at `verge_edge` wherever `apron_zone > 0.5`.

The first (blind) sweep still found **370** real columns where two of this
module's own surfaces sat under 2.5 mm apart:

| what | how many | why |
|---|---:|---|
| building bases, fence feet, skips, crates with their underside at exactly z = 0.000 | 370 → 0 | fixed by `embed_ground_contacts()`, **22 946 vertices sunk 20 mm** |
| cable-duct covers 2.0 mm above the slab they overlapped | 71 → 0 | the bays are now cut around the duct and drain corridors (`_y_intervals`) |
| deck boards sharing a plane with their own sub-frame | 12 → 0 | frame top dropped to `dz − 0.082` |
| service-road markings at the platform's `MARK_Z`, 0.5 mm under their own road | 12 → 0 | split into `ARCH_RoadMarkings`, laid on the road's own camber |
| the forecourt's granite band 2 mm over the service yard | 6 → 0 | the yard now butts the band at x = −27.6 |
| a lifted drain grating resting exactly on the slab | 12 → 0 | raised 8 mm; it leans on the slab, it does not share its plane |
| a garages cable duct running under the pit building's plinth | 6 → 0 | removed — that slab **is** the building footprint |
| the service road's channel edge 2.5 mm over the concrete it is laid on | 2 → 0 | camber raised: crown +78 mm, channel +14 mm |
| a kerb gully grate laid flush, exactly on the concrete's bay plane | 2 → 0 | recessed 14 mm, which is what a gully is |

After both sweeps: **0 intra-object** and **1 of 9 000 cross-object columns**,
named in the gate output every build.

Two rules in that table are worth stating, because they are what make it a
measurement rather than a ritual:

* **buried is legal, visible is not.** A footing 30 mm under another module's
  ground is a footing; the same face 30 mm above it is the defect the review found
  six times. The test is signed.
* **nothing proud, recesses allowed.** A slot-drain channel is 55 mm down and a
  gully 50 mm down *by design*. A surface *above* the datum is a lip the 12.5° sun
  draws a 25 mm shadow under, and a coplanar risk. Only that side is bounded, and
  the datum check is filtered by **material** (`PAVE_MATS`) so that a duct-cover
  bolt head is not mistaken for the slab it is bolted to.

`cull_unowned()` is the backstop: after all builders run, any up-face still on
another module's ground is **deleted**, in bmesh, and the count is reported
(190 last build). That is the contract's rule for finding #2 applied as a machine
operation — cut, do not offset — so no individual generator has to be trusted.

### 7.2 `verify_sightlines()` — spec §10.6, unchanged in intent

| check | result |
|---|---|
| `hold->wound[0..4]` (aperture centre + four corners) | clear, 595 m |
| `key0->car[0..2]` | clear, 84–88 m |
| `hold->car@s601/701/815` | clear |
| beat-6 path clearance, 25 directions, 6 m sphere | no hit |
| **transit route** — now walked on `WC.access_route_point` and clipped to `WC.access_edges`, not to a private copy | clear |
| grandstand max z | **13.55 m** (cap 14.0) |

Rewriting the transit check against the contract is what surfaced §6: the old
check used this module's own 70 m corridor arithmetic and could not have seen it.

---

## 8. Frames, and the one matrix

```
W = Rz(+40°) · ( C − (−350, +72) ) + (15, 0)
```

Object *local* coordinates are circuit metres, which is what every procedural
material keys off — the concrete bay hash, the standing-seam pitch and the
board-mark pitch are all in real metres in a frame aligned to the pit straight.

Built at **identity** in world metres, because they belong to the round-1
pavilion: `ARCH_Paving_Forecourt` and `ARCH_ShowroomSurrounds`. Built at identity
because it is generated in `(s, u)` and mapped by `WC.su_to_world`:
`ARCH_Paving_ApronPlatform`.

**The forecourt mitre** survives the rewrite and is now cut by the same machinery
as everything else: `clearance = min(clear_c, _fc_clearance)`, so the paddock bays
are sawn against the forecourt's rotated rectangle *and* the road corridor *and*
the ribbon in one pass, and the granite edge band is pre-tiled to ~1.1 m before
cutting so it follows the ribbon rather than chording across it.

---

## 9. Lighting and material calibration

`_test_env()` is the contract's §8 verbatim: `SUN_ENERGY` 115.754,
`SUN_COLOR` (1, 0.71632, 0.38712), `sun_disc` off, `MULTIPLE_SCATTERING`,
air 1.00 / aerosol 0.45 / ozone 1.30, AgX at −3.048, Look = None.

**Measured** with an albedo-0.18 lambertian card, Standard view transform,
exposure 0:

| | red | green | blue |
|---|---:|---:|---:|
| `C.lambert_radiance(0.18)` | 1.6744 | 1.4600 | 1.3321 |
| rendered, first attempt | 1.7915 | 1.5759 | 1.4537 |
| ratio | ×1.070 | ×1.079 | ×1.091 |

Subtracting the sun's own `E_DIRECT_HORIZONTAL` leaves a **sky** of
(6.27, 9.60, 15.69) W/m² against the contract's (4.228, 7.577, 13.573): this
scaffolding has the sky *node* but not build_sky's explicit 1.1 km aerosol layer,
which is where the contract's low node aerosol is compensated. Scaling the
background by 8.459 / 10.52 = **0.804** lands it at

| | red | green | blue | mean |
|---|---:|---:|---:|---:|
| ratio after | ×1.040 | ×1.018 | ×0.970 | **×1.009** |

so the test frames are exposure-correct to **0.9 %** at
`C.REFERENCE_EXPOSURE_EXTERIOR` and the residual is ±4 % of *tint*, not level.
`ground_albedo` is set to 0.0 (the geometry provides the bounce) though the
MULTIPLE_SCATTERING model ignores it. **Final renders use `build_sky`'s world,
not this rig**; the rig exists so that a test frame can be judged at the same
exposure the film will be.

---

## 10. The contract proxies

`_contract_proxies()` meshes the **neighbours** from the contract so a test render
shows this module against the ground the other five have agreed to build, not
against a flat plane of its own invention:

* `PROXY_RoadCorridor` — `C.ground_z` on an `(s, u)` grid out to `platform_edge`,
  both sides, split at `half_width` / `verge_edge` so the kerb band reads;
* `PROXY_AccessRibbon` — `C.access_z` between `C.access_edges`;
* `PROXY_TransitWalls` — `C.transit_wall_span` / `transit_wall_point`, i.e. the
  corridor as `build_barriers` will build it;
* `PROXY_Terrain` — a plate at **−0.20**, deliberately *below* `APRON_Z`, so
  anywhere the platform is not properly retained shows as a black slot;
* `PROXY_Showroom` — the round-1 pavilion.

Pass `--noproxy` to switch them off.

---

## 11. The variation systems (unchanged, and still the red line)

"No one tree spammed 100 times." Nothing here is a duplicate loop with a random
rotation. §5.2 above covers the new families; the originals are unchanged:

* **14 garages** — door family (roller / sectional / concertina / overhead) is
  four different *meshes* whose open state changes what geometry exists; pier
  construction, header signage type, interior layout, balcony type and dressing,
  tidiness driving both the count and the *alignment* of the equipment in front
  of the box, and per-box marking wear.
* **6 grandstands** — six different typologies, each with its own tread, rise,
  aisle spacing, vomitory count, frame system and roof. 18 350 seats across four
  archetypes with a hue/value jitter, 22 % folded (a different mesh), 0.6 %
  missing; the seat-letter graphics are rasterised through an embedded 5×7 bitmap
  font at two seats per font pixel, so **the words are made of seats**.
* **Pit wall** — 3.0 m precast units with every fifth short, ±12 mm height and
  ±0.004 rad tilt per unit, advertising panels in three states including a corner
  peeled away as real geometry.
* **Transporters** — one per team, trailer length 12.6–14.6 m, two cab families,
  1–4 roof pods, awning deployed / half / stowed.
* **Paddock buildings** — one modular system parameterised into five hospitality
  units, the media centre and the medical centre; race control is deliberately
  *not* from that system.

---

## 12. Blender 5.2 notes

* `BevelModifier.clamp_overlap` → **`use_clamp_overlap`**.
* `ShaderNodeTexSky` has no `NISHITA` (use `MULTIPLE_SCATTERING`) and **no
  `dust_density`** — it is `air_density` / `aerosol_density` / `ozone_density`.
  Setting `dust_density` raises `AttributeError` and costs a build.
* A SUN lamp emits along local **−Z**, so `rotation_euler` must come from
  `Vector(SUN_DIR).to_track_quat('Z','Y')`. Negating it puts the sun underground
  and gives a shadowless render.
* Meshes are flat vertex/face lists realised with `from_pydata`, with
  `material_index` / `use_smooth` / a CORNER `Col` attribute written by
  `foreach_set`. Vertex colour is the per-instance variation channel.
* All text is baked from the bundled `Bfont` through `to_mesh()`. **No external
  assets**: no downloaded font, texture, model or HDRI, zero `TEX_IMAGE` nodes,
  every material a node graph.

---

## 13. Test renders

`render/world/architecture/` — 2560×1440, 384 samples, on the **RTX 5090**, lit
only by the contract's §8 constants. The racing surface, the runoff platform, the
access ribbon, the Beat-4 corridor walls and the terrain are `_contract_proxies()`;
they belong to other modules and are drawn from the contract.
`render/world/architecture/pre_contract/` holds the pre-migration frames for
comparison.

| file | what it is for |
|---|---|
| `arch_beat4_route.png` | **Beat 4 at rooftop height** — the ribbon, the corridor walls as `build_barriers` will build them, the paddock cut around both, and the sawn joint where the platform meets the road |
| `arch_beat4_low.png` | the same route at 1.35 m: the joint, the retaining edge and the ground furniture at car height |
| `arch_apron_rim.png` | the pit-exit apron platform, the gutter and `ARCH_RetainEdge` where the platform meets `platform_edge` |
| `arch_paddock_eye.png` | eye level in the paddock — the ground-detail pass |
| `arch_aerial_pad.png` | the paddock from 150 m — the "toy blocks" check |

**The assembly-defect probes**, 3840 × 2160, **640 samples**, DOF forced off, on
the 5090. These are the frames the two fixes are answerable to, and the `_BEFORE`
pair is the shipped defect rebuilt by reverting four constants and nothing else,
so the two frames differ by the defect alone:

| file | camera | what it settles |
|---|---|---|
| `arch_apron_macro_BEFORE.png` / `arch_apron_macro.png` | 0.90 m up, 2.7 m inboard, 8.4 m of the joint across frame, sun 97 % across it | **defect #3.** BEFORE: a pure-black hairline, min ÷ concrete **0.000**. AFTER: a 50 mm sealed joint, min ÷ concrete **0.239–0.258**, zero pixels below 15 % |
| `arch_apron_edge.png` | 1.10 m up, down 190 m of the joint | the same thing at film distance — a fine grey line, not a black one, the whole length of the pit straight |
| `arch_glass_gap.png` | 0.30 m up, 5 m behind the breach plane, looking out through it — `CAM_GLASS_GAP.png`'s framing | **defect #2, world build only.** Continuous ground: the formation slab, the ribbon, no slot, no eggcrate. The dark band is the shadow of the 100 mm formation step, which round 1's `Floor` covers |
| `arch_glass_gap_r1floor.png` | the same camera, `--r1floor` | **the film case.** Round 1's `Floor` composited: the mouth is one unbroken surface from the dais to the ribbon. No step, no line, nothing |
| `arch_glass_mouth.png` | 0.95 m, from inside the pavilion out along the corridor | the mouth at car height, with the walled run and the merge beyond |

Three defects the renders found that no gate would have:

1. **the sun was underground** — `(-SUN_DIR).to_track_quat` (§1, finding #5);
2. **the shrubs were green cards floating on sticks** — 5–11 leaves of up to
   0.26 m scattered through the crown volume. Rebuilt as a branching skeleton
   with 9–18 folded 45–95 mm leaves per twig on an ellipsoidal shell;
3. **the paddock read as a chessboard from 150 m** — the vertex-colour bay stain
   and the shader's own per-bay hash compounding on 5 × 6 m bays. The stain layer
   is now half its amplitude;
4. **the finger-post legend was mirrored on its far face** — `Rz(90 − 90·sy)`
   put the +Y text's normal into the plate. `Rz(180) @ Rx(90)` applies `Rx`
   first, taking the normal +Z → −Y → +Y and the reading direction +X → −X,
   which is the +Y face;
5. **the shattered apron was the test rig, not the model** — see §7.1.

And the one this round added to that list:

6. **the render found a hole the sweep called closed** — deeper cell splitting
   pushed every clipped fragment under a flat minimum-area threshold and 0.28 m
   of finished slab disappeared down the apron edge, while 9 000 ray columns
   reported "no open joint" because the bedding 35 mm below answered for it. See
   §0b.

**Build summary (last run).** 31 objects · **2 502 057 base triangles** ·
38 materials · 6 243 paving bays (**2 918 of them sawn** to the contract,
587 special) · 48 239 m² of platform · **5 894 m² of pit-exit apron platform on
6 019 m² of bedding** · 682 m² of formation under the round-1 pavilion ·
439 m of retaining edge · 918 terrace bays · 18 350 seats · 182 furniture groups ·
11 light masts · 8 finger posts · 5 hospitality decks with 38 seats ·
48 paddock + 10 forecourt planters · 279 marking segments dropped by `_owned()` ·
190 faces culled · 22 946 vertices embedded · build **39 s** ·
**contract gate ALL CLEAR (29 checks), sight-line gate ALL CLEAR (13 checks)**,
and `build()` exits non-zero if either is not.

---

## 14. Interfaces — what the other modules must know

1. **`build_barriers`** owns the Beat-4 corridor and the portal. It must also
   extend its runoff platform to `WC.platform_edge` on the **left of the pit
   straight** (12.10 m): `ARCH_RetainEdge`'s heel is buried under the ground at
   `platform_edge − 0.28`, and if that ground is not built the heel is exposed.
2. **`build_surface`** owns the access ribbon and every marking on it. This module
   lays nothing inside `WC.access_ribbon_polygon()` + 0.30 m **laterally**, and
   nothing at all past `WC.ACCESS_RIBBON_T_MIN` = 0.0 — the paving butts the
   ribbon **on the breach plane, x = 15.0000**, measured by bisection every build.
   It also owns `SURF_ApronJoint`, the 50 mm sealed joint at the pit-exit apron
   edge; this module's slab begins on the outer end of that lap
   (`APRON_JOINT_LAP_M`, same `getattr` expression in both files) and **overlaps
   none of it**. See §6 for the pit wall / ribbon conflict it should be told about.
2b. **The round-1 pavilion — a required assembly step, not a module.** The
   corridor mouth behind the glass plane is round 1's `Floor`
   (`opus5-car-render/f1_showroom.blend`: world x −15…15, y −11…11, **top
   z = 0.000**, soffit −0.060). This module builds the **formation slab it sits
   on**, closed, at **z = −0.100**, and deliberately lays no finished bay there:
   two surfaces at 0.000 over 30 × 22 m in the frame the car breaches the glass
   is the coplanar defect this round exists to close. `build()` publishes the
   whole interface as `summary['r1_floor_interface']`.
   **The assembly must composite that `Floor`.** Without it the mouth still has
   ground everywhere — the formation — but reads as a 100 mm step;
   `arch_glass_gap.png` and `arch_glass_gap_r1floor.png` are the two frames.
3. **`build_terrain`** must build no ground inside `WC.apron_platform_mask`, and
   **additionally** none inside `ARCH_Grandstand_Terrace`'s extent (§4), which the
   contract does not yet carry. It may weld to the terrace skirt anywhere between
   `APRON_Z` and `APRON_Z − 1.85`.
3b. **Two numbers still want a home in the contract.** `APRON_JOINT_LAP_M`
   (0.050) and `APRON_JOINT_DEPTH_M` (0.005) are read by **both**
   `build_surface` and this file as `getattr(C, name, default)`, so today they
   agree by having the same fallback rather than by having one owner. Publishing
   them in `world_contract.py` costs one line each and removes the last place at
   the track/apron joint where two modules hold the same number twice. The
   ribbon's start cap already went that way in **1.0.1**
   (`ACCESS_RIBBON_T_MIN`) and it is the reason defect #2 is closed rather than
   renegotiated.
4. **`build_dressing`** — trackside tyre stacks, marshal posts and ad boards are
   its own; everything inside the paddock rectangle listed in §5.2 is this
   module's, and `KEEPOUT` records where this module has already committed
   ground so a second scatter can avoid it.
5. **Lighting** — garage ceiling strips, canopy downlights, monitor faces, signal
   lenses, start lights and illuminated headers are all `A_Emit` with brightness
   carried in vertex colour (black = off). A relight only touches `A_Emit`.
