# WORLD_CONTRACT.md

**`world/world_contract.py` is the single source of truth for everything two or more
modules must agree on.** This file explains why each decision went the way it did, and
maps each of the assembly review's five findings to the contract element that prevents
it recurring.

Contract version **1.1.0**. Self-test: `python3 world/world_contract.py --selftest` —
**114 checks, ~15 s**, no Blender required. v1.1.0 closes four defects and adds the
**continuity gate** (§13) that the first of them got past. Read §13 before changing
anything in the corridor programme or the datum.

---

## 0. How to use it

```python
import sys, os
sys.path.insert(0, os.path.join(PROJECT_ROOT, "world"))
import world_contract as C

z          = C.ground_z(s, u)              # THE ground datum. signed u, + = left
z, owner   = C.world_ground_z(x, y)        # any world point, and whose mesh is there
hw         = C.half_width(s)               # spec §9, fixed
e          = C.verge_edge(s)               # hw + 1.50 kerb + 1.00 verge
off        = C.barrier_offset(s, side)     # barrier FACE
lim        = C.platform_edge(s, side)      # outboard limit of the road programme
cut        = C.road_corridor_mask(x, y)    # terrain: build no ground where this is True
poly       = C.access_ribbon_polygon()     # architecture: cut your paving to this
```

Three rules, and they are not stylistic:

1. **If two modules need the same number, it lives here.** You import it. You do not
   reimplement it, you do not re-derive it from `circuit_spec.json`, and you do not
   "match" it. Every one of the five findings below is a number that two modules each
   derived independently and got different answers for.
2. **`world_contract.py` imports nothing but the stdlib and numpy.** No `bpy`. It has to
   run in a bare shell so the assembly gate can check a build without opening Blender,
   and it has to import into every builder without dragging Blender state along.
3. **The contract is not advisory.** A module that disagrees with it is the thing that
   is wrong — including `build_surface`, which is merely where most of the datum came
   from.

---

## 1. Conventions

| | |
|---|---|
| **world frame** | +X east, +Y north, +Z up. Origin = round-1 showroom floor centre. `z = 0.000` is the showroom finished floor **and** the pit-straight racing surface at the line. All geometry ships in this frame. |
| **circuit frame** | a.k.a. design frame. Pit straight along +x, centreline on y = 0. `world = Rz(40°)·(circuit − (−350, 72)) + (15, 0)`. Use `C.circuit_to_world` / `C.world_to_circuit`. |
| **s** | lap station, metres, `0 ≤ s < 3675.0`, from the S/F line in the racing direction (counter-clockwise). Everything takes `s % LAP`. |
| **u** | **signed** lateral offset from the centreline, **positive to the LEFT of the direction of travel**. |
| **side** | `+1` = left of travel, `−1` = right. A corner with `turn_deg > 0` turns left, so its **outside** is `side = −1`. |

### The sign convention is the one that caused finding #1

`build_barriers` and `build_dressing` speak `(lat, side)` with `lat ≥ 0`. A datum
expressed in `|lat|` **cannot carry banking**, because banking is antisymmetric in `u`.
That is not an oversight in the old `build_barriers.ground_z`; it is a direct
consequence of its signature. At 4° of banking on T10/T11 the outboard road edge is
0.66 m below the inboard one, and a function that cannot tell them apart is 0.66 m out
before it has fallen a single metre.

So every lateral in the contract is signed. For the `(lat, side)` callers, every such
function also accepts an optional `side`:

```python
C.ground_z(s, lat, side)  ==  C.ground_z(s, side * abs(lat))
```

which is a drop-in replacement for the old `build_barriers.ground_z(s, lat, side=None)`
signature.

---

## 2. `ground_z(s, u)` — THE datum

`build_surface.surface_z` was the only existing implementation carrying crown, banking
**and** undulation, so it is the basis. The contract's version adds the two things
`surface_z` did not have to think about, because it only ever meshed the road:

```
 |u| ≤ verge_edge(s)     elevation_c(s)
                       + banking(s)·u + drainage crown
                       + undulation(s, u)
                       + negative-kerb troughs
                       − verge drain (12 mm, ramped over the painted verge)

 |u| > verge_edge(s)     the road-edge value above, FROZEN — banking, undulation and
                         all — plus a constant −1.6 % outward fall,
                         except inside the apron tie (§7).
```

### The cross-section, stated once

| band | extent from the centreline | who meshes it |
|---|---|---|
| racing surface | `0 … half_width(s)` | `build_surface` (`SURF_Track`) |
| kerb band | `+1.50 m` | `build_surface`; kerb objects sit **on** the datum |
| painted verge | `+1.00 m` → `verge_edge(s)` | `build_surface` |
| runoff platform | → `platform_edge(s, side)` | `build_barriers` (or `build_architecture` in the apron zone, §7) |
| terrain | beyond `platform_edge` | `build_terrain`, welded to `corridor_rim` |

`kerb_top_z(s, u)` gives the top of a serrated kerb (25 mm inner lip → 50 mm outer,
+25 mm serration = 75 mm peak, spec §9) for clearance checks, without meshing one.

### What is deliberately NOT in the datum

`build_surface._undulation` carries two racing-line-dependent micro terms: a −9 mm
compaction dip along the driven line and a +4.5 mm braking-zone washboard. Both are
gaussian-windowed on `u − racing_line(s)` with 2.8 m and 3.4 m sigmas, so they are
already under a millimetre by the time they reach the track edge. Computing them here
would drag `build_surface`'s 240-iteration racing-line drivability solve into a module
that five builders import at load time.

They are therefore excluded, **and bounded**. `build_surface` may add them on top of
`ground_z` inside the racing surface under two conditions:

* `|extra| ≤ MICRO_LAYER_MAX_M` = 0.018 m, and
* `extra == 0` for `|u| ≥ half_width(s)` — enforced by multiplying by
  `C.micro_window(s, u)`, so it is a multiplication, not a promise.

**Measured**, over 200 000 random `(s, u)` inside the racing surface:
`|surface_z − ground_z|` is **max 14.4 mm, p99 11.1 mm, p50 0.73 mm, rms 4.2 mm**. The
analytic worst case of the two excluded terms is `0.009 × 1.35 + 0.0045` = 16.6 mm. The
contract *is* build_surface's surface, to the width fix and the micro layer.

---

## 3. `half_width(s)` — the width bug, fixed

spec §9 declares five widths and one transition rule:

| section | racing surface |
|---|---:|
| pit straight (S15 + S0) | **16.0 m** |
| standard | **14.0 m** |
| T4 hairpin | **15.0 m** |
| esses T6–T9 | **13.0 m** |
| access road / pit exit | **12.0 m** |

> "Width transitions are linear over 60 m so no seam is visible from the air."

**THE RULE, stated once.** A named section carries its full declared width over
**exactly its element extent**. The 60 m linear transition lies entirely **outside** the
section, in the neighbour. Therefore:

| | |
|---|---:|
| `half_width(3115.000)` | **8.000** — S15 `s_start`, the pit straight opens |
| `half_width(3055.000)` | **7.000** — 60 m earlier, still standard |
| `half_width(250.000)` | **8.000** — T1 `s_start`, the pit straight closes |
| `half_width(310.000)` | **7.000** — 60 m later, standard again |
| `half_width(3085.000)` | **7.500** — the transition is linear, so its midpoint is the mean |

The hairpin and the esses follow the same rule against their own element stations
(T4 = 939.2693…1025.2791, esses = T6 `s_start` 1545.4708 … T9 end 1904.0411). None of
the four transition bands overlap; the shortest gap is 400 m.

### What each module actually had

| at `s` | contract | build_surface | build_barriers | build_terrain |
|---|---:|---:|---:|---:|
| **3115.0** | **16.000** | 14.044 | 16.000 | 15.000 |
| **250.0** | **16.000** | 14.044 | 16.000 | 15.033 |
| 3055.0 | 14.000 | 14.000 | 14.000 | 14.000 |
| 1000.0 | 15.000 | 15.000 | 15.000 | 14.938 |

Whole-lap, against the contract:

| module | max \|Δ half-width\| | rms | fraction of the lap > 10 mm out |
|---|---:|---:|---:|
| `build_surface` | **0.978 m** | 0.156 | **14.1 %** |
| `build_terrain` | **0.502 m** | 0.100 | **14.4 %** |
| `build_barriers` | 0.0039 m | 0.0006 | 0.0 % |

`build_surface._build_width` set the 16 m span to `[3115+30, 250−30]` and then applied a
±30 m raised cosine — **centring** the transition on the element boundary instead of
starting it there. `build_terrain._ramped` set the span to `[3115, 3675]` and box-filtered
it over 60 m, which is the same centring error. `build_barriers` had it right and
everyone else was up to 0.978 m out.

That is not a cosmetic disagreement, because `build_barriers` pins runoff, verge,
advertising boards and barrier offsets to `verge_edge = half_width + 2.5`. With
`build_surface` building a 14.04 m road where `build_barriers` started its runoff at
16.00 m + 2.5, there was a **0.63 m strip of unbuilt ground along both edges of the pit
straight** — the surface the onboard follow runs down at 330 km/h.

### Linear, not raised-cosine

The spec says linear. A 1.0 m width change over 60 m deflects the road edge by 0.95°,
and a real circuit has exactly that construction joint. A C1 rounding would have to be
adopted by all five consumers or none, and "none" is the only one of those that cannot
drift. `half_width` is `np.interp` over 14 keys; anyone can reproduce it exactly.

---

## 4. Derived widths — change one thing, everything moves

```
verge_edge(s)          = half_width(s) + 1.50 + 1.00
runoff_widths(s, side) = {asphalt, gravel, grass, apex}   measured OUTBOARD from verge_edge
runoff_edge(s, side)   = verge_edge + max(asphalt+gravel, grass, apex)
barrier_offset(s,side) = the barrier FACE  (spec §9 runoff table, the inside-corner
                         geometric clamp, and the spec's hard pins)
platform_edge(s, side) = max(barrier_offset, runoff_edge) + margin
```

The runoff programme is ported verbatim from `build_barriers`, so `barrier_offset` is
numerically identical to the barrier line already built — this is a fix, not a rebuild.
What changes is that it is now **derived from the contract's `half_width`**, so the
0.978 m width error propagates out of the runoff, the verge, the boards and the barrier
line in one edit instead of five.

Spec pins that must stay exact, and are checked in the self-test:

* pit-straight south barrier at circuit `y = −19` (spec §9) — holds to 0.000 m
* pit wall at circuit `y = +11.5`, circuit x −245…+130 (spec §10.7) — holds to 0.000 m
* doppler station barrier pinned 30 m out so the hovering camera has 4.00 m of clearance

`PLATFORM_MARGIN_M` = 6.0 m of ground beyond the barrier for the Armco foot, the fence
posts and a mown shoulder — **except** where the barrier is a solid concrete wall, where
it drops to `PLATFORM_MARGIN_WALL_M` = 0.6 m, because the ground behind a pit wall
belongs to the pit lane. Without that clamp the road corridor claimed 6 m of
`ARCH_Paving_PitLane`.

`BASE_EMBED_M` = 0.020: anything standing on the ground — post, wall, tyre stack, board,
bollard, tree — embeds at least 20 mm into the datum, so a 10 mm mesh tolerance can
never open a lit gap under it at a 12.5° sun.

---

## 5. The road corridor — terrain cuts a hole, it does not blend

`build_terrain`'s height field is a **CELL = 2.5 m** grid. A track edge is a 3675 m curve
held to a centimetre. A 2.5 m grid cannot represent it, so "blend the terrain into the
road" was never an available move: at best it gives a 2.5 m sawtooth down both edges of
the circuit, and at worst — which is what happened — it gives this.

**Measured, `TER_Ground` against the contract datum:**

| where | result |
|---|---|
| the racing surface itself (16 542 samples) | terrain **above the tarmac at 6.49 %**, worst **+0.387 m** at s = 2198, u = +7.0 — the T10/T11 banked sweeper, i.e. the 294 km/h helicopter dive |
| kerb + painted verge band | buried at **54.0 %** (left) / **43.6 %** (right), worst **+0.563 m** |
| mid-runoff (asphalt + gravel) | terrain above the platform at **93.4 %** / **83.1 %**, mean **+1.30 m** / +0.28 m, worst **+5.75 m** |
| the barrier foot | terrain > 150 mm above at **82.1 %** / **76.0 %**, mean **+0.57 m** / +0.47 m — against `ARMCO_TOP` = 1.012 m |
| dressing standoff, 45 m out | terrain sat **+0.58 m** (left) / +0.52 m (right) above the datum objects were placed on |

So: **it is a hole.**

```python
cut = C.road_corridor_mask(x, y)        # build no ground geometry where True
rim = C.corridor_rim_polyline(side)     # weld your first ring of vertices to this
```

* `platform_edge(s, side)` is the outboard limit of the road programme. Left 12.1…73.0 m,
  right 25.0…87.9 m. **309 180 m² (0.31 km²)** comes out of the height field.
* `corridor_rim(s, side)` gives the exact `(x, y, z)` terrain must weld to, z from
  `ground_z`. Terrain blends outward into natural ground over `CORRIDOR_BATTER_M` = 34 m
  (its own existing number) and puts its drainage swale outside the rim, not inside it.
* `build_terrain.PLATFORM_DROP` = 0.120 is **superseded**. There is no separate platform
  height any more; the platform *is* `ground_z`, which already falls at −1.6 % from the
  road edge — −0.10 m at 6 m out, −0.32 m at 20 m.

### The vegetation exception, and "not a grass gray line"

The user's actual complaint has a precise cause. Terrain deliberately left the runoff
zone bare — `ter_wear` 0.85, no grass inside `PLAT` — **because it assumed the paving
would be on top**. Barriers paved it. Terrain then covered the paving in dirt. Two
correct-in-isolation decisions producing a grey line.

The contract splits it the other way round:

* **Terrain builds no ground inside the corridor.** The runoff asphalt (50 555 m²), the
  gravel (42 419 m²) and its 240 000 individually generated stones become visible
  because nothing is on top of them.
* **Terrain still scatters vegetation inside the corridor** — the verges want it and the
  user asked for it — but it places every clump with `C.ground_z`, never with its own
  height field, and it plants nothing inside the runoff asphalt or the gravel beds
  (`C.runoff_widths`). Grass on the verge, bare gravel in the trap, both correct.

---

## 6. Beat 4 — the ribbon and the corridor

### 6.1 The access ribbon

`SURF_AccessRoad`, `ARCH_Paving_Paddock`, `ARCH_Paving_Apron` and `ARCH_Markings` all
covered the same 116 m of ground at separations of 1.4–9.0 mm, and the winning surface
flipped six times along the route. At 4K with a flying camera that is stroboscopic depth
fighting through the beat the brief calls the world-design linchpin.

Three decisions:

**(a) `build_surface` owns the driving surface.** It is a road, it is continuous with the
racing surface it merges into, and it must share that surface's datum exactly or the
merge is a seam at 219.5 km/h. `build_architecture` **cuts its paving** to
`C.access_ribbon_polygon()` — a closed world-space polygon, 400 vertices by default, with
a 0.30 m margin for the sawn edge strip — and lays no slab, no marking and no drain
inside it. Markings on the ribbon are `build_surface`'s.

**(b) The ribbon is DEAD FLAT at z = 0.000 for the first 49.60 m.** Not crowned.
spec §10.3(b) requires the first 50 m outside the glass to be exactly 0 % and exactly
level with the interior floor so the breach debris "keeps travelling on the plane it
started on"; §10.5 says the apron, the road and the racing surface are one plane at
z = 0.000. `build_surface`'s `−0.0125·|u|^1.7` crown put the ribbon edge 75 mm below the
apron and violated both. Over the merge arc the ribbon eases from that plane onto
`ground_z`; **past the merge point it *is* `ground_z`**, verified identical to 0.0 m, so
the join to `SURF_Track` is exact by construction rather than by tolerance.

**(c) The ribbon is clipped to the outside of `verge_edge`.** The R150 arc converges on
the pit straight. Unclipped, the ribbon's inboard edge crosses the track centreline and
lies 74 mm under `SURF_Track` for the last 59 m of the merge — the clip first engages at
route station **t = 95.3 m of 154.3**. `C.access_edges(t)` returns the clipped edges. The
car still merges "inside the track edge" as spec §10.5 requires: it drives across the
painted verge, which on the pit straight is plain asphalt because no kerb is planned
there.

**Result**, scanning the review's own line (world y = 0, x −5…+111, at 0.25 m):

```
build_architecture:paving → build_surface:SURF_AccessRoad
                          → build_architecture:paving → build_surface:SURF_Track
3 ownership changes.  One surface at every point.  Zero coplanar pairs.
```

### 6.2 The walled corridor — who owns it, and how long it really is

**`build_barriers` owns it. `ARCH_ApronCorridor` is deleted**, by name, via
`C.CORRIDOR_DELETE_NAMES`.

Reasons, in order: it is safety furniture — a retaining wall, a belted tyre stack, a
debris fence and a portal, every one of which is a `build_barriers` primitive with a
per-unit variation model, against `build_architecture`'s loose tyres intersecting a
concrete plinth. And `build_barriers` already isolated its version into a `BR_Transit`
collection "so they can be deleted wholesale if that module builds them too". It does
not need to be.

**The extent, though, was wrong in both builds and in the spec.** Measured along the
route with `project` against `verge_edge`:

| route t | south wall face, circuit y | clearance to the painted verge edge |
|---:|---:|---:|
| 75 m | +19.47 | 8.967 m |
| 85 m | +14.49 | 3.992 m |
| **90 m** | **+12.24** | **1.737 m** |
| 93 m | +10.96 | 0.460 m ← old `BR_Transit` end |
| 95 m | +10.14 | **−0.359 m — on the verge** |

spec §10.5's "middle 90 m of the apron run" at a constant −7.0 m offset is not
buildable: the merge arc converges and the south wall runs out of road at t = 95.
(§10.5 is internally loose anyway — the apron run is 49.6 m long, so a 90 m wall on it
always had to extend into the arc.) `build_architecture` found the same wall — its own
arithmetic put the collision at its `s = 90`, which is this `t = 102` — and solved it by
shortening the **whole** corridor to 70 m and starting it 12 m later, throwing away 20 m
of the camera's walled run to fix a problem only the south wall has.

The corridor is therefore **asymmetric**, which is also what a real pit exit is:

| | route stations | length | at its worst |
|---|---|---:|---|
| north retaining wall, 2.40 m, offset +8.0 | `6.0 → 96.0` | **90.0 m** — the spec literal | 13.1 m clear of the racing surface; ends on open apron at circuit (−269, +23.6) |
| south tyre wall + fence, 2.00 m, offset −7.0 | `6.0 → 90.0` | **84.0 m** | 1.74 m of verge still in front of it; needs a proper barrier terminal |

Both start at `t = 6.0` (world x = 21.0) rather than the old 3.0: the forecourt bollard
line stands at world x = 19.5 with bollards at y = ±9.0, and a wall face at y = +8.0 /
−7.0 starting before x = 21 fouls them and crowds the facade at the frame where the
camera clears the glass. The pit-exit portal at world x = +58 (route t = 43.0) sits
inside the walled run on both sides.

The camera flies **90 m of corridor, walled on both sides for 84 m of it**, and the wall
that peels away first is the one on the side the road is about to merge into. That is a
motivated reveal, not a compromise.

---

## 7. The apron tie — a conflict the review did not reach

The spec asserts three things that are each true and that meet at the track edge:

* §2 — `z = 0.000` is the pit-straight surface;
* §10.5 — the pit-exit apron, the road and the racing surface are "one plane at z = 0.000";
* §9 — the racing surface is crowned, which puts its edge at **−0.10 m**.

And §10.7 declares the pit-exit apron as circuit x −480…−245, **y 0…+45** — where y = 0
is the pit-straight **centreline**. Taken literally, architecture paves 10.5 m of racing
surface and 241 m of its painted verge. `ARCH_Paving_Apron` already did: it starts at
circuit y = 9.5 against a verge edge at 10.5, which is a 1.0 m wide, 241 m long coplanar
overlap at a 55–70 mm offset — a lit ledge down the whole pit straight.

Resolved the way a real pit exit resolves it, inside `ground_z` so nobody has to think
about it again:

* `apron_platform_mask(x, y)` returns the declared regions **minus** the road corridor
  and **minus** the ribbon. (`raw=True` gives the literal spec rectangles.) In the
  sampled apron band, 90 % of the declared cells belong to the road and are now cut.
* Outboard of `verge_edge`, wherever the corridor programme carries **no barrier** —
  which is exactly and only the open pit-exit apron, circuit x −480…−245 on the left,
  s 3200…3420 — the platform gives up its −1.6 % fall over `APRON_TIE_M` = 8.0 m and
  lands on `APRON_Z` = 0.000, exactly.

Measured at s = 3300: road edge −0.122 → gutter invert −0.132 at 12 m → **0.0000 at 22 m
and everywhere beyond**. 132 mm of rise over 8 m, max cross-grade 3.05 %. That is a
valley gutter, not a step, and it is where the drainage runs. `platform_owner(s, side)`
says the surface there is `build_architecture`'s unrubbered concrete, not
`build_barriers`' runoff — which is what spec §10.5 declared it to be (μ 0.90).

The right-hand platform is untouched and still falls at exactly −1.6 %.

---

## 8. The lighting contract

**`build_sky` is the physical light of this film and it wins.** Every number below is
`build_sky`'s shipped, measured value, recorded here so material calibration, exposure
and any future relight have one reference.

| | value |
|---|---|
| `SUN_DIR` | (0.5178540, −0.8277670, 0.2159390), unit |
| elevation / bearing | **12.47061°** / **−57.96966°**, shadow ratio 4.5222 |
| `SUN_IRRADIANCE` | **(115.754, 82.917, 44.811)** W/m², normal to the sun |
| `SUN_ENERGY` / `SUN_COLOR` | **115.754** / **(1.00000, 0.71632, 0.38712)** |
| angular diameter | 0.545° (lamp and drawn disc use the same number) |
| sky model | `MULTIPLE_SCATTERING` — Blender 5.x has no `NISHITA` enum |
| air / aerosol / ozone / altitude | **1.00 / 0.45 / 1.30 / 0.0** |
| `sun_disc` | **off** — the SUN lamp is the light; leaving it on double-counts the key |
| `sun_rotation` | **147.96966°** = 90° − bearing (measured, not assumed) |
| `SKY_IRRADIANCE` | **(4.228, 7.577, 13.573)** W/m² on a horizontal surface |
| `SKY_TINT` | (0.3115, 0.5582, 1.0000) |
| `E_DIRECT_HORIZONTAL` | (24.996, 17.905, 9.676) = `SUN_IRRADIANCE · sin 12.47°` |
| `DIRECT_TO_DIFFUSE` | **2.072** = `sum(E_DIRECT_HORIZONTAL) / sum(SKY_IRRADIANCE)` |
| visual range | 23 km, `SIGMA_EXT_550` = 1.7009e−4 /m |
| `REFERENCE_EXPOSURE_EXTERIOR` | **−3.048** stops, AgX, Look = None |

**Exposure is a hand-off, not a setting.** `build_sky` never writes
`scene.view_settings` (its only `view_transform = 'Standard'` is inside its own
calibration probe render). The camera rig writes it, once, for the whole film — one lens,
one grade, no per-beat look changes, per the brief's law.

### Calibrating a material against this light

```python
C.lambert_radiance(0.18)   ->  (1.6744, 1.4600, 1.3321), mean 1.4888
```

An albedo-`a` horizontal lambertian surface renders at `a/π · (E_DIRECT_HORIZONTAL +
SKY_IRRADIANCE)` linear. `REFERENCE_EXPOSURE_EXTERIOR` was solved so that the mean of
that at `a = 0.18` lands on AgX mid-grey. If a material's rendered patch is not within a
few percent of `lambert_radiance` for its intended albedo, **the material is wrong, not
the light.**

### What `build_terrain.md` §2.1 got wrong, and how wrong

§2.1 published a lighting rig and told task #27 to "ADOPT S2.1 VERBATIM". Task #27 did
not, and was right not to: `build_sky` **measured** the sun against its own sky instead
of assuming it. The comparison:

| | terrain §2.1 assumed | actual | consequence |
|---|---|---|---|
| sun | 120 W/m² at (1.000, 0.735, 0.470) | 115.754 at (1.000, **0.71632**, **0.38712**) | the real sun is markedly redder and much less blue |
| aerosol / ozone | 1.45 / 1.80 | **0.45 / 1.30** | sky tint (0.3115, 0.5582, 1.0000) |
| direct : diffuse | 3.00 : 1 | **2.072 : 1** | **shadows are 45 % brighter relative to key** than turf albedo was tuned for |
| exposure | −2.70 AgX | **−3.048 AgX** | 0.348 stops |

The overall level is close **by luck**: §2.1's assumed total horizontal irradiance is
1.331× too high and its exposure 0.348 stops too dark, so the net lands within 0.07
stops. The **colour** and the **key:fill ratio** are not close. Every material calibrated
against §2.1 must be re-checked against `lambert_radiance`.

---

## 9. Tolerances — what "agrees" means, numerically

`build_barriers.md` claimed `SEAM_DROP = 0.015` "absorbs up to 15 mm of disagreement".
The measured disagreement at the verge edge was min −0.679 m, max +0.689 m,
p95 |0.49| m — **off by 46×**. A tolerance is only a tolerance if something measures it.

| | | |
|---|---:|---|
| `TOL_DATUM_M` | 0.001 | two modules asking `ground_z` the same question must agree within 1 mm. They will: it is one function. |
| `TOL_SEAM_M` | 0.010 | a module's own mesh may sit up to 10 mm off the datum at a shared boundary (row spacing, bevels, chamfers). Beyond that it is a defect, not a tolerance. |
| `TOL_COPLANAR_M` | 0.030 | two **separately-owned** surfaces closer than this in z over a shared footprint are a z-fight. The only legal fix is for one of them not to be there: **cut, do not offset.** |
| `SEAM_DROP_M` | 0.0 | **retired.** Nothing hides under anything any more. |
| `MICRO_LAYER_MAX_M` | 0.018 | measured, §2 |
| `BARRIER_JITTER_MAX_M` | 0.25 | `build_barriers` may add bounded lateral history jitter to the barrier line so it is not a drawing-board curve. Nobody else may. |
| `TOL_CLOSURE_M` | 1e-6 | **v1.1.0.** The datum must close on itself at the start/finish line: `ground_z(s)` and `ground_z(s + LAP)` are the same metre of road. 1 micron — 1000× below `TOL_DATUM_M`, 17× above the 5.7e-8 m the datum's own 5.2 % grade contributes over the 1e-6 m the test steps back from the seam. v1.0.1 failed it at **6.75 mm**. |
| `BARRIER_MAX_LATERAL_RATE` | 1.95 | **v1.1.0.** m of lateral per m of station. The steepest the barrier line, the runoff edge or the platform edge may move. Both a **declared bound** and the rate `barrier_offset` is cone-eroded at. §13. |
| `CORRIDOR_SMOOTH_K_M` | 0.60 | **v1.1.0.** Blend width of `_smax` / `_smin`, the C1 max/min the corridor cross-section is assembled with. Deviates from the hard operator by at most k/4 = **0.15 m**, inside `BARRIER_JITTER_MAX_M`. |
| `PIT_OVERRIDE_RAMP_M` | 45.0 | **v1.1.0.** The ramp the pit-straight overrides blend over, replacing the hard boolean masks that stepped the barrier line 46.31 m in one metre. |
| `APRON_JOINT_LAP_M` / `APRON_JOINT_DEPTH_M` | 0.050 / 0.005 | **v1.1.0.** The track↔apron joint. `build_surface` carries `SURF_Track`'s asphalt edge outboard past `verge_edge` by the lap, with the depth as a sealant invert; `build_architecture`'s slab begins on the outer end of it. Both used to read these as `getattr(C, …, default)` and agreed only because they shared a fallback literal. |

---

## 10. The five findings → the contract element that prevents each

| # | finding | prevented by | how |
|---|---|---|---|
| **1** | **Three incompatible ground datums.** TER_Ground proud of the tarmac over 5.3 % of the racing surface, up to +0.381 m at T10/T11; 42.3 % of the kerb+verge band buried; the entire runoff programme invisible; 90.1 % of the barrier line with ground > 0.15 m above its own foot; 59 % of dressing objects buried, worst 7.38 m; surface-vs-barrier disagreement at the verge edge ±0.69 m against a claimed 15 mm tolerance. | **`ground_z(s, u)`** (§2) + **`road_corridor_mask` / `platform_edge` / `corridor_rim`** (§5) | There is exactly one datum function and it is signed in `u`, so it carries banking out into the runoff — the missing piece that made the old barriers datum 0.69 m wrong. Terrain no longer has a datum at all inside the corridor: it cuts a 309 180 m² hole and welds to `corridor_rim`. `build_dressing` already delegates to `build_barriers.ground_z`, so fixing that one function fixes all 150 dressing objects. `world_ground_z(x, y)` gives every module one call that returns both the height and the owner. |
| **2** | **Beat 4 is a coplanar z-fight for its whole length** — the winning surface flips 6 times over 116 m at 1.4–9.0 mm between `SURF_AccessRoad`, `ARCH_Paving_*` and `ARCH_Markings`. | **`access_ribbon_polygon()` + `in_access_ribbon()` + `access_z()` + `access_edges()`** (§6.1) and **`TOL_COPLANAR_M`'s rule: cut, do not offset** | The paddock builder cuts around the ribbon instead of overlapping it. Nothing is coplanar because nothing overlaps: on the review's own scan line the ownership changes 3 times, cleanly, with one surface at every point. The ribbon is flat z = 0.000 for 49.6 m (which §10.3(b) required all along) and **is** `ground_z` past the merge, so the ribbon↔track join is exact, not toleranced. |
| **3** | **The Beat-4 walled corridor is built twice**, 0.5 m apart, at x 18→109.8 (barriers) vs 27→98.4 (architecture) — half loose tyres sinking into concrete, half a proper belted stack, in the corridor the camera flies at rooftop height. | **`CORRIDOR_OWNER` = `build_barriers`, `CORRIDOR_DELETE_NAMES` = `("ARCH_ApronCorridor",)`, `TRANSIT_WALL_S0/S1`, `transit_wall_span()`, `transit_wall_point()`** (§6.2) | One owner, named. The loser is deletable by name. The extent is decided with the measured convergence table, not with either module's arithmetic: north wall 6→96 (90 m, the spec literal, 13.1 m of clearance), south wall 6→90 (84 m, terminated with 1.74 m of verge still in front of it). Both starts clear the forecourt bollard line at x = 19.5. |
| **4** | **Three modules disagree on the main straight width** by up to 0.978 m over 13 % of the lap, leaving a 0.63 m strip of unbuilt ground along both edges of the pit straight. | **`half_width(s)`** (§3), and **`verge_edge` / `runoff_edge` / `barrier_offset` / `platform_edge` derived from it** (§4) | One function, linear over 60 m, transition outside the section, verified at s = 3115 and s = 250 (both exactly 8.000) plus ten more stations and the transition midpoint. Because every downstream width is derived rather than re-derived, a change to the section table moves the runoff, the verge, the boards, the barrier line, the terrain hole and the dressing standoff together. |
| **5** | **Terrain's materials were calibrated under a light that does not exist** — `build_terrain.md` §2.1 vs what `build_sky` shipped. | **`SUN_*` / `SKY_*` / `REFERENCE_EXPOSURE_EXTERIOR` / `lambert_radiance()`** (§8) | The sky is the physical light and its real numbers are recorded here as the one calibration reference, with the delta from §2.1 quantified: direct:diffuse 2.072 not 3.0, sun colour blue channel 0.387 not 0.470, exposure −3.048 not −2.70. `lambert_radiance(albedo)` turns "is this material right" into an arithmetic check with a published answer. |

---

## 11. Migration — what each module changes

| module | change |
|---|---|
| **`build_surface`** | Delete `_build_width`; `track_half_width = C.half_width`. Base `surface_z` on `C.ground_z` and add the racing-line micro layer as `extra * C.micro_window(s, u)` with `|extra| ≤ C.MICRO_LAYER_MAX_M`. Build the road cross-section out to `C.verge_edge(s)` exactly. Rebuild `SURF_AccessRoad` on `C.access_route_arrays` / `C.access_edges` / `C.access_z` — flat z = 0 for the first 49.6 m, clipped inboard, no `−0.0125·|u|^1.7` crown. Keep the blend-line markings; they are yours. |
| **`build_barriers`** | Delete `half_width`, `verge_edge`, `ground_z`, `SEAM_DROP`, and the `Corridor` class; import all six from the contract. **Pass signed `u`.** Extend the runoff platform mesh out to `C.platform_edge(s, side)` so terrain has something to weld to. Keep `BR_Transit_*` and rebuild it to `C.transit_wall_span` / `C.transit_wall_point` (north 6→96, south 6→90, starts at world x = 21.0). Add a proper terminal at the south wall's end. Lateral history jitter stays, bounded by `C.BARRIER_JITTER_MAX_M`. |
| **`build_terrain`** | Delete `Circuit._half_width`, `Circuit._platform`, `PLATFORM_DROP` and the corridor blend in `Ground.height`. Cut the height field with `C.road_corridor_mask` and weld the boundary ring to `C.corridor_rim_polyline` — clip the cells, do not just drop them, or the 2.5 m grid shows. Move the drainage swale outside the rim. **Keep scattering vegetation inside the corridor**, placed with `C.ground_z` and excluded from `C.runoff_widths`' asphalt and gravel. Re-check every material against `C.lambert_radiance`. |
| **`build_architecture`** | Delete `ARCH_ApronCorridor` and `build_corridor` entirely. Cut `ARCH_Paving_*` and `ARCH_Markings` to `C.access_ribbon_polygon()` and to `C.apron_platform_mask(x, y)` — the exclusive one. Pave the pit-exit apron outward from `C.verge_edge` where `C.apron_zone(s, +1) > 0.5`, sitting it on `C.ground_z` so the gutter is real. Everything else you build stands on `C.world_ground_z`. |
| **`build_dressing`** | Replace its `BR` fallbacks with the contract (`ground_z`, `verge_edge`, `barrier_offset`); pass signed `u`. Re-place every object on `C.world_ground_z`, embedded by `C.BASE_EMBED_M`. |
| **`build_sky`** | No geometric change. Publish its constants **from** the contract, or assert against them at build time, so the two can never drift. |

---

## 12. Verification log

Everything above is measured, not asserted. Three artefacts, all reproducible.

### 12.1 `python3 world/world_contract.py`

**71 checks, 0.6 s, no Blender required.** Covers the centreline against the spec's own
202 published control points (max |u| = 6.5 mm) and the loop closure (1.4 mm); the
elevation PVIs; `half_width` at 13 stations plus the transition midpoint; `ground_z`
continuity across `verge_edge` (< 1e-5 m); the banking reaching the runoff; the runoff
pins; the whole transit route against spec §10.5's published coordinates; the corridor
clearances; the apron tie; the lighting identities; the scalar/array API contract; and
that the corridor mask, architecture's paving and terrain's ground form an **exhaustive,
disjoint** partition of the world.

### 12.2 The neighbour-comparison harness

`render/world/contract/verify_vs_neighbours.py`, run inside Blender against the three
live modules. It reproduces the review's own headline numbers **from the contract's
side** — same 0.978 m width error over 14.1 % of the lap, same ±0.69 m verge-edge
disagreement (min −0.679 / max +0.689 / p95 0.49), same +0.387 m of terrain over the
tarmac at s = 2198, same 42–54 % buried kerb band, same 82 % of the barrier line with
ground above its own foot. The contract is aimed at the target the review measured.

### 12.3 The rendered evidence

`render/world/contract/` — built by `build_contract_probe.py`, rendered at 512 samples,
2560 px, on the 5090, lit **only** from this contract's published lighting constants
(`SUN_ENERGY` 115.754, `SUN_COLOR` (1, 0.71632, 0.38712), aerosol 0.45, ozone 1.30,
AgX at −3.048), which is itself a check on §8.

| file | what it shows |
|---|---|
| `sec_track.png` | Cross-section at s = 2196 (T10 mid-arc), ×12 vertical exaggeration, reference lines every 0.25 m of **real** height. WHITE (contract) and AMBER (`build_surface`) are coincident across the racing surface and climb 5.3 reference lines — **1.32 m of banking across 21 m**, exactly the computed 1.321 m. GREEN (`build_terrain`) is dead flat and crosses the tarmac mid-frame. RED (`build_barriers`) is flat over the road and falls symmetrically at both ends, because a datum in \|lat\| cannot be antisymmetric. AMBER stops short of WHITE at both ends: that is the width error, in section. |
| `sec_wide.png` | The same section across 94 m. WHITE peaks at the outboard verge edge and falls at −1.6 % to the barrier line. GREEN, still dead flat, is above the tarmac on the inside of the corner and above the **runoff platform** again beyond 55 m — the 50 555 m² of runoff asphalt and 42 419 m² of gravel that were under dirt. |
| `pit_width.png` | True-scale plan of the width transition, s 3082…3128, with the s = 3115 element boundary marked in blue. The MAGENTA band is the defect itself: ground that `build_barriers` pinned its runoff, verge, boards and barrier line to, and that `build_surface` never paved. Pixel-measured against the render's own scale (55.65 px/m), the contract↔terrain edge separation is **0.512 m against 0.500 m predicted**. |

**Anything that changes a number in this file changes `world_contract.py` first, bumps
`__version__`, and re-runs all three.**

---

## 13. v1.1.0 — four defects, and the gate that lets none of them back

### 13.0 Why there is a gate at all

`--selftest` had **74 checks and not one of them looked at whether anything was
continuous.** `barrier_offset` stepped **51.99 m in one metre of station**; what got
built from it was `BR_Armco_L03/L04` and `BR_FenceStruct_L03/L04` lying **wall-to-wall
across the T4 braking zone**; `build_barriers` wrote a 200-line §4b to survive it and
handed the defect back in a comment; and the contract still printed `PASS`.

**A gate that cannot fail on the artefact you already know is bad is not an
instrument.** The gate below is therefore runnable against any revision of this module:

```
python3 world/world_contract.py --gate-selftest <path/to/old/world_contract.py>
```

It loads the other revision through the **public API only** and expects it to fail. Run
against the shipped v1.0.1 it fails **14 of 23 rows**, headed by
`barrier_offset (side +1)` measuring **51.9876 m/m at s = 904.00** and
`ground_z LAP closure` measuring **6.746e-3 m** — the two numbers the defect reports
opened with. If it ever passes an old revision, the gate is the broken thing.

### 13.1 Defect 1 — `barrier_offset` stepped 51.99 m in one metre. TWO mechanisms.

The defect report attributed all of it to the pit-straight masks. **Measured, it is two
independent faults**, and only one of them is the masks:

| s | side | step | mechanism |
|---:|---:|---:|---|
| 904 | +1 | **51.99 m** | (a) the `maxoff` sentinel |
| 250 | −1 | **46.31 m** | (b) the pit-straight masks |
| 1060 | +1 | 21.40 m | (a) |
| 3114 | −1 | 15.69 m | (b) |
| 1743 | −1 | 15.26 m | (a) |
| 1819 | −1 | 9.38 m | (a) |
| 2665 | +1 | 8.64 m | (a) |

**(a) A mean is not a smoother when one of its inputs is a sentinel.** `_Corridor.maxoff`
wrote `1e6` for "this station has no geometric cap", min-filtered it over ±55 m, and
then **box-filtered it over 41 samples**. With one `1e6` left in the window the mean is
`1e6/41 = 24 390`; with none it is `14.0`. So `np.minimum(raw, maxoff)` went from *no
cap at all* to *14.0 m* in a single sample. The published `maxoff` at s = 904 was
**24 403.902**, and at s = 905 it was **14.000**. That is the whole of the 51.99 m.

Fixed by making the sentinel finite and modest (`MAXOFF_NONE_M` = 200.0, against a
maximum programme offset of 81.95 m), deleting the box filter, and **cone-eroding the
finished line** instead.

**(b) A boolean mask assignment is a step by construction.** The pit-straight overrides
wrote `grass[-1][pit] = …`, `asph[-1][pit] = 0.0`, `grav[-1][pit] = 0.0` on a hard
`(s >= 3115) | (s <= 250)` mask, so at s = 250 the T1 runoff zone — already at full
weight, 45 m of asphalt + 12 m of gravel — switched on in one sample against a pit-wall
grass width of 11 m. They are `_ramp`-weighted blends now, over `PIT_OVERRIDE_RAMP_M`,
with the transition placed **outside** the named section exactly as §3 places the width
transition outside its section. The **discrete** labels (`btype`, `fence`) keep their
masks and are bit-identical to v1.0.1 — a barrier is Armco or it is concrete and there
is no half of one.

### 13.2 Why cone erosion, and not a filter

`_cone_erode(c, rate)(s) = min_j ( c(j) + rate·|s − j| )`. Three properties, none of
which a convolution has:

1. **The result is exactly `rate`-Lipschitz whatever `c` does, including if `c` steps.**
   A box or gaussian filter of a stepped field is still a smoothed step, whose slope
   goes as step/width — which is why (a) survived a 41-sample filter. This is what makes
   the bound in §13.4 a **property** and not an observation.
2. **The result is never below `min(c)`.** `build_barriers`' first attempt subtracted a
   *box-smoothed deficit* from an already-stepped line and produced **−18.80 m** on side
   +1 — a barrier face 18.8 m **past the centreline**. A cone cannot do that.
3. **It is a no-op wherever `c` is already `rate`-Lipschitz**, so setting the rate at the
   runoff programme's own steepest declared motion leaves the line bit-for-bit unchanged
   where the cap never bites — measured, **98.8 %** of side +1 and **99.7 %** of side −1.

`np.maximum` of two smooth ramps is continuous but **kinks**, and the corridor
cross-section is assembled almost entirely out of maxima. `platform_edge` is the
polyline `build_terrain` welds its first ring of vertices to, under a 12.47° sun, so the
crossovers are now `_smax` / `_smin` — the quadratic smooth max/min, blend width
`CORRIDOR_SMOOTH_K_M` = 0.60 m, deviating from the hard operator by **at most 0.15 m**
and only within 0.6 m of a crossover. 0.15 m is inside `BARRIER_JITTER_MAX_M` = 0.25 m,
the lateral freedom `build_barriers` is already allowed on this line, so no consumer's
clearance analysis changes. `_smax` only ever moves an edge outboard and `_smin` only
inboard: the terrain hole can only grow, and the barrier can only move away from the
racing surface.

**What is NOT claimed:** `barrier_offset` is now C0 with a stated Lipschitz bound. It is
**not C1**. Rounding the metre-scale corners where a runoff bay opens into a curve you
could not see under a raking sun needs a value-space blend of tens of metres, which
moves the line by metres. Those corners are what a circuit actually builds — the run
ends and another begins further out — and turning them into arcs is a design change, not
a defect fix.

### 13.3 Defects 2, 3, 4

| # | was | now |
|---|---|---|
| **2** | `_undulation` evaluated value noise on **raw `s`**. `s/46.0` puts 79.891 noise cells in a 3675 m lap, so cell 0 and cell 79.891 carry unrelated hashes and **the datum did not close on itself**: a **6.75 mm step across the start/finish line**, inside `TOL_SEAM_M`, hidden under the painted S/F line, in a film that drives down that straight at 300 km/h. | The noise runs on a **whole number of cells per lap** (80 / 237 / 766, moving the three published wavelengths by < 0.15 %) and `_vnoise` wraps its lattice index. `ground_z(0, u) == ground_z(LAP, u)` to **1.4e-17 m**. |
| **3** | `access_z` eased from the flat apron onto `ground_z` with a weight that was a function of the **route station alone**, completing at t = 154.32 — but the ribbon starts **sharing an edge with `SURF_Track` at t = 95.33**. Disagreement with `ground_z`: **80.2 mm** along the 149.3 m shared edge, **90.2 mm** worst anywhere on the ribbon, **9× `TOL_SEAM_M`**. `build_surface` measured it and routed around it; `build_terrain`, `build_architecture` and `items/access_road_slab` did not. | `access_z` **IS** `ground_z`, expressed in route coordinates. Kept as a named function only for its nine callers. Nothing is lost: spec §10.3(b)'s flat 49.60 m still holds **exactly** (max \|z\| = 0.000000 m), because `ground_z` is already identically `APRON_Z` over the whole apron run — the contract's own apron tie does it. |
| **4** | `APRON_JOINT_LAP_M` (0.050) and `APRON_JOINT_DEPTH_M` (0.005) were read by **both** `build_surface` and `build_architecture` as `float(getattr(C, name, default))`, and agreed only because the two files carried the same fallback literal. | Declared here, beside `APRON_Z`. Both modules keep their `getattr` form, so a builder pinned to a v1.0.x contract still works; from v1.1.0 the `getattr` finds these. |

### 13.4 The gate — what it samples, and how each bound was calibrated

`CONTINUITY_BOUNDS` is a public dict of `(bound, sample step, calibration)`. Two rules
govern it, and the second matters more than the first:

1. **A bound is calibrated from a declared quantity** — a spec grade, a ramp length in
   `RUNOFF_ZONES`, a filter width in this file — never from what it happens to measure
   today. The measurement is printed beside the bound so the margin is visible.
2. **Sampling step matters more than the bound.** A step of *e* mm sampled at *h* metres
   reads as *e*/1000*h* m/m. The datum's 6.75 mm start/finish step is **invisible** at
   h = 0.25 m (0.027 m/m, under a 0.10 bound) and obvious at h = 0.01 m (0.675 m/m). So
   `ground_z` is gated at **0.01 m** over the whole lap at 17 laterals, and has a
   dedicated exact closure test on top.

| quantity | bound | step | calibration | measured |
|---|---:|---:|---|---:|
| `half_width`, `verge_edge` | 0.0170 | 0.25 | spec §9: 1.0 m of half-width over the 60 m **linear** transition = 0.016667 m/m exactly | 0.016667 |
| `elevation_c` | 0.0550 | 0.25 | spec §5: max \|PVI tangent grade\| = 5.200 %. Inside a symmetric parabolic vertical curve the gradient lies between its two tangent grades, so the tangent maximum **is** the maximum | 0.052000 |
| `barrier_offset` | **1.95** | 0.25 | steepest motion a single `RUNOFF_ZONES` entry declares is 1.5·W/ramp = **1.750** (T10T11, 70 m over 60 m); the assembled programme peaks at **1.9447** where the S11 doppler pin overlaps T10T11's ramp-out; every consumer's break test is a strict `> 2.00`. 1.95 is the tightest round number above the former and strictly below the latter. **Enforced** by `_cone_erode` at exactly this rate | 1.950000 |
| `runoff_{asphalt,gravel,grass,apex}` | 1.95 | 0.25 | no component of the cross-section may move faster than the line it drives | ≤ 1.500 |
| `runoff_edge` | 1.9700 | 0.25 | `verge_edge` (0.0170) + the widest component (1.950) | 1.883 |
| `platform_edge` | 2.1000 | 0.25 | `runoff_edge` (1.970) + the wall-margin ramp, a 45-sample box of a 0/1 indicator × (6.0 − 0.6) m = 0.120 m/m | 1.950 |
| `apron_zone` | 0.0340 | 0.25 | the declared pit-exit ramp: a smoothstep over 45 m, peak slope 1.5/45 = 0.033333 /m exactly | 0.022222 |
| `ground_z`, 17 laterals | 0.1000 | **0.01** | max PVI grade 5.200 % + the banking transition carried to the verge edge (max d(bank)/ds = 0.001839 /m over the 14 m `_csmooth`, × 10.5 m = 1.931 %) + the undulation (0.55 %) = 7.68 %, + 30 % for the negative-kerb ramps and the apron tie not being *proved* disjoint from the rest | 0.056908 |
| `corridor_rim_z` | 0.1500 | 0.25 | `ground_z` (0.100) + the platform's −1.6 % cross-fall dragged along by `platform_edge`'s 2.10 m/m = 3.4 % | 0.067578 |
| `ground_z` LAP closure | **1e-6** | exact | `TOL_CLOSURE_M`, §9 | 1.4e-17 |

Bounds that **are** a declared rate are stated as that rate + `_RATE_EPS` = 1e-6,
because the gate resamples a 1 m station field at 0.25 m and (0.25·r)/0.25 is not always
exactly *r* in float64. A micron of lateral per metre of station.

### 13.5 What moved, and who has to rebuild

| quantity | change | where |
|---|---|---|
| `barrier_offset` | **−52.97 … +2.50 m** (side +1), **−47.32 … +0.06 m** (side −1); unchanged to < 10 mm over **93.9 % / 96.1 %** of the lap | the taper into T4 (s 860–904), out of it (1061–1089), and the four other capped stretches; the pit-straight ramps at s 251–291 and 3075–3114 |
| `runoff_edge` / `platform_edge` | −20.2 … +0.1 m / −22.8 … +2.3 m (side +1); −48.5 … +0.1 m / −47.3 … +0.2 m (side −1) | the same places. Terrain's hole and the barriers' platform both derive from these, so they move **together** and no void opens |
| `ground_z` | **−8.5 … +9.6 mm** on the road cross-section (rms 1.5 mm) from the cyclic-noise fix; up to **+0.36 m** on the pit-exit apron at s 3158–3214, \|u\| 14–41 m, from `apron_zone` now covering exactly the spec §10.7 rectangle (s 3195–3430) instead of the 23-m-short box-filtered version | everywhere / the pit-exit apron |
| `access_z` | up to **90.2 mm**, to agree with `ground_z` | the Beat-4 ribbon |
| `barrier_type`, `fence_allowed`, `half_width`, `verge_edge`, `elevation_c`, all lighting | **unchanged** | — |

**Every module that baked a mesh against a v1.0.x `ground_z` must rebuild** — the datum
moved by up to 9.6 mm on the racing surface, which is `TOL_SEAM_M`. `build_surface`,
`build_barriers`, `build_terrain`, `build_architecture`, `build_dressing` and every
`items/*.py` that meshes ground all import the datum, so a rebuild is sufficient; none
of them needs a code change.

**`build_barriers` §4b and its step-break workaround are now no-ops** and their owner
can retire them: measured against v1.1.0, `_STEP_BREAK` fires on **0 stations** on both
sides (it fired on five places, 24 m of lap), and `barrier_clamp_report()` gives
`max_lateral_rate` 1.95 on both sides with `stations_inside_verge` = 0. The §4b
ownership clamp still does real work — it solves corridor self-intersection, which is a
different problem — but it now clamps 9.71 % of the left corridor rather than 14.1 %,
and it is exact against the contract over 90.3 %.

`build_barriers.BARRIER_BREAK_RATE` = 2.00 is a private copy of a shared number and
should become `WC.BARRIER_MAX_LATERAL_RATE` (RULE 1).

## 14. v1.1.1 — the pit exit, and a gate that measures rendered blackness

Four defects, all of them at the pit exit, all of them shared quantities that a
module had inferred for itself. Full write-ups in `DEFECT-LOG-R2.md` R2-037..040.

### 14.1 `PIT_WALL_S0` — the wall's extent is a function of where the road runs

`barrier_offset(s, +1)` was pinned to `PIT_WALL_Y` from the declared garage
frontage, `_pit_straight_station(GARAGE_X0)` = s 3430.0. The access ribbon — the
pit-exit road — does not come inboard of that line until **s 3447.71**, so for
17.7 m the contract asked for a concrete wall standing in a road, and
`build_architecture` built one: measured **1.067 m inside the car's swept volume**
with the car at 207.0 km/h.

`PIT_WALL_S0` is derived from `access_edges` now, and the open pit-exit apron runs
up to it, so **the apron ends where the wall begins** — one boundary, stated once,
instead of two statements about `GARAGE_X0`. The declared `pit_lane` rectangle
starts there too, for the same reason.

The terminal is published (`PIT_WALL_TERMINAL_M` = 5.0,
`PIT_WALL_TERMINAL_FLARE_M` = 0.60) because the station the contract publishes is
where the NOSE stands. v1.0.x's `build_architecture` had already moved its own west
end by hand to a literal −228.0 with a nose that tapers in HEIGHT ONLY, so the
nose's face was still on `PIT_WALL_Y` and it is exactly what the gate caught. A
flared terminal is where the clearance comes from and it is a real object.

### 14.2 `TRANSIT_KEEPOUT_M` / `rim_buildable` — the rim crosses the transit lane

`platform_edge(s, +1)` runs 30.92 m at s = 3400 and 12.28 m at s = 3429 while the
car crosses those stations at u = 26.0 and 15.9, so from s ≈ 3405 east the corridor
RIM lies inboard of the driven route. `ARCH_RetainEdge` stood on it, **1.526 m**
into the car's path — deeper than the pit wall. The contract states the keep-out
once, for every module that stands anything on a rim.

### 14.3 `ribbon_edge_u` — one edge, in lap coordinates, to 1 mm

Three modules cut to the ribbon's outboard edge and all three found it for
themselves; `build_barriers` swept `u` in 0.10 m steps and then stood off the
result by `ACCESS_RIBBON_SAW_M` = 0.30 m, which is **paving's** joint and not
asphalt's. **22.95 m² of ground had no surface on it at all.** `ribbon_edge_u` is
NaN where the ribbon does not reach, so nobody can extrapolate an edge across the
240 m of pit straight the ribbon is nowhere near.

Note `access_edges` clips the ribbon's inboard edge to `verge_edge` *at the route's
own station*, and over the merge arc the two frames differ by up to 3.3°, so that
clipped edge lands up to **0.44 m outboard of `verge_edge`** once re-projected onto
the lap. Anything that needs the ribbon's edge in lap terms must use
`ribbon_edge_u`, not re-derive it from `access_edges`.

### 14.4 `recess_relative_radiance` — a depth bound is not a blackness bound

The sun is 12.47° up and `SUN_SHADOW_RATIO` = 4.5222, so a 34 mm step casts 155 mm
of shadow: **nothing narrower than 155 mm gets any direct sun on its floor**,
whatever a depth gate says. `build_architecture`'s `DEPTH_LIM` = 66 mm and its 3 %
low-column bound both PASSED a recess that rendered as 3,390 pure-black pixels.

The model is two closed-form terms — the lit fraction of an infinite slot's floor,
and the slot's sky view factor `sqrt(1+r²) − r` — weighted by the DECLARED
irradiances, so it moves when `build_sky` moves. `TOL_RECESS_RADIANCE` = 0.10 is
calibrated between two measured artefacts: the 5 × 34.3 mm recess that shipped
(0.024) and the shallowest legitimate joint in the same frame (8 × 5 mm, 0.180).
`max_recess_depth(0.005)` is 7.4 mm.

### 14.5 `platform_field` — terrain had no field to cut the platform with

`build_terrain` cut a hole for `road_corridor_mask` and, for the declared z = 0.000
platform, only FLATTENED its height field. `TER_Ground` was still there under
build_architecture's concrete: 859 columns of `ARCH_Paving_Paddock × TER_Ground` at
|dz| p50 15.59 mm, and 0.65 % of sampled columns carrying two owners within 2 mm.
`platform_field` is `apron_platform_mask(raw=True)` as an exact signed distance, so
a straddling cell is clipped rather than dropped — the same reason `corridor_field`
is a field and not a mask.
