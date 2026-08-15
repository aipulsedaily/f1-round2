# round2_inventory.md — what round 1 actually produced

**Single source of truth for what the car is made of.** The round-2 brief opens with
*"Do NOT assume what it produced — inventory it"*, and this file is that inventory. Every
number here was **measured** from the blend by `tools/inventory.py`, not recalled from
round-1 documentation. Where the docs and the blend disagreed, the blend won and the drift
is recorded.

Generated 2026-07-28 from `~/opus5-car-render/work/iter.blend`
(288,254,978 bytes, Blender 5.2). Raw data: `docs/inventory_iter.json`,
`docs/explode_plan.json`.

---

## 1. Headline numbers

| | measured |
|---|---:|
| objects in scene | 947 |
| mesh objects | 919 |
| **car meshes** | **616** (+ `CAR_ROOT` empty = 617 objects in `CAR`) |
| car modules | 15 |
| base polygons | 4,598,601 |
| **evaluated triangles** | **10,122,867** |
| materials | 51 |
| cameras | 4 |
| lights | 23 lamps (+38 mesh emitters/fixtures in `LIGHTS`) |

### Doc drift found

- Round-1 docs state **~9.6 M** evaluated triangles. Measured: **10,122,867**. Use the
  measured figure; the difference is roughly half a million triangles of budget.
- Round-1 docs say "616 objects" for the car. That is 616 **meshes**; the `CAR` collection
  holds **617** objects because `CAR_ROOT` is an empty carrying the 0.340 m ride-height
  offset. Both statements are true, they count different things. Reconciled, not a defect.

---

## 2. Collection structure

```
Scene Collection              947
├── CAMERAS                     4
├── SHOWROOM                   76
├── LIGHTS                     61   (23 LIGHT + 38 MESH)
├── PROPS                     189
└── CAR                       617   (616 MESH + CAR_ROOT empty)
```

---

## 3. THE AXIS FINDING — the brief's convention is inverted for this car

**This is the most consequential thing in the inventory.** The brief says to compute
exploded offsets with *"fore/aft elements along Y, lateral outboard"*. Measured:

```
X  -2.678 ..  3.020    5.698 m   ← LONGITUDINAL.  +X = nose,  -X = tail
Y  -1.003 ..  1.003    2.005 m   ← LATERAL (mirror axis)
Z   0.340 ..  1.332    0.992 m   ← VERTICAL.  0.340 = ride height
```

Proof of orientation: `FW_` (front wing) centroid **+2.679**, `NOSE_` **+2.450**, against
`RW_` (rear wing) **−2.350**. And **every module's Y centroid is exactly 0.000**, which is
what a mirror axis looks like.

So the brief's *intent* maps onto this car as: **fore/aft along X, lateral outboard along
Y, underbody −Z, top structures +Z.** Following the brief's literal wording would have
rotated every exploded offset by 90° and put the front wing out the side of the building.

---

## 4. Car modules, measured

Ordered rear → front by X centroid. `centX`/`centZ` are world-space evaluated centroids.

| module | objs | eval tris | centX | centZ | extent (x,y,z) m |
|---|---:|---:|---:|---:|---|
| `RW_` rear wing | 97 | 535,588 | −2.350 | 0.930 | 0.65 × 1.05 × 0.72 |
| `suspension_rear_` | 16 | 557,996 | −1.997 | 0.671 | 0.51 × 1.53 × 0.32 |
| `EC_` engine cover | 13 | 394,122 | −1.091 | 0.918 | 2.49 × 0.65 × 0.80 |
| `FD_` floor/diffuser | 10 | 685,308 | −0.340 | 0.530 | 3.78 × 1.78 × 0.30 |
| `SP_` sidepods | 13 | 485,712 | −0.084 | 0.830 | 2.14 × 1.48 × 0.58 |
| `wheel_tyre_` | 56 | 1,030,528 | 0.000 | 0.701 | 4.32 × 2.01 × 0.72 |
| `brake_assembly_` | 88 | 826,248 | 0.008 | 0.700 | 4.04 × 1.82 × 0.42 |
| `halo_assembly_` | 53 | 329,722 | 0.130 | 1.125 | 1.67 × 0.76 × 0.41 |
| **`MB_` monocoque** | **17** | **1,844,927** | **0.265** | 0.827 | **5.47 × 1.45 × 0.89** |
| `CI_` cockpit interior | 15 | 459,202 | 0.459 | 0.871 | 1.24 × 0.42 × 0.40 |
| `SW_` steering wheel | 65 | 288,904 | 0.504 | 0.821 | 0.13 × 0.28 × 0.23 |
| `BB_` bargeboards | 10 | 534,848 | 1.300 | 0.623 | 0.86 × 1.51 × 0.45 |
| `suspension_front_` | 10 | 458,212 | 1.736 | 0.700 | 0.57 × 1.52 × 0.45 |
| `NOSE_` | 33 | 477,818 | 2.450 | 0.641 | 1.10 × 0.46 × 0.33 |
| `FW_` front wing | 120 | 720,048 | 2.679 | 0.525 | 0.68 × 2.00 × 0.33 |

### The structural core, identified by geometry not by name

The brief requires the assembly to start from the structural core *"identified by geometry
and hierarchy, not by name"*. That is unambiguously **`MB_`**:

- it spans **5.47 m of the car's 5.698 m** — no other module comes close
- it carries the **most geometry by a factor of 1.8** (1,844,927 tris vs 1,030,528 next)
- its centroid sits nearest the car centre in X

It is pinned at zero offset: everything else assembles onto it.

---

## 5. Surprises resolved (35 warnings, zero defects)

Every warning was unapplied object scale. All are intentional, none are bugs, but **two
change how round 2 must compute geometry**:

| count | what | consequence for round 2 |
|---:|---|---|
| 16 | `Vitrine_*` scaled 0.366–0.919 | display-case clones placed by `s09_display.py`; they live in **PROPS** and **share mesh datablocks with real car parts**. They must NEVER be swept into the car's explode — animating by object is safe, but any code that iterates mesh *data* will hit them twice. |
| 12 | tyre objects, Z-scale **1.206** front / **1.598** rear | the tyre profile. Local `bound_box` therefore **understates real extent by up to 60%**. All exploded offsets must use evaluated world bounds. |
| 7 | `SW_` display/LED, scale 90–420× | tiny source geometry scaled up. Harmless, but do not "tidy" it. |

No zero-poly meshes, no orphaned objects, no `hide_render` objects, no leftover WIP.

---

## 6. Assembly order, and why

Derived from the brief's rule — structural core first, inboard-to-outboard, underbody
before topside, aero late, wheels last — applied to the measured module list. The rank
function in `tools/explode_plan.py` computes this, so a new module slots in without a
hand-edited list.

```
MB → FD → BB → EC → CI → SW → halo_assembly → SP → NOSE → FW → RW
   → CORNER_FL + CORNER_FR + CORNER_RL + CORNER_RR   (simultaneous)
```

| stage | clusters | justification |
|---|---|---|
| 1 | `MB` | structural core, pinned; everything mounts to it |
| 2 | `FD` | underbody before topside — the floor bolts to the tub's underside |
| 3 | `BB`, `EC` | inboard structure and powertrain enclosure |
| 4 | `CI`, `SW`, `halo_assembly` | cockpit furniture, inside-out |
| 5 | `SP` | bodywork closes over the inboard structure |
| 6 | `NOSE`, `FW`, `RW` | aero late, as the brief requires |
| 7 | four corners, **simultaneous** | wheels last, seating together |

**Clustering rationale.** 616 parts flown individually would read as confetti, which the
brief explicitly forbids. Parts are grouped where the grouping is *mechanically real*: a
corner assembly (upright, hub, brake, wheel, tyre and the suspension links that land on it)
bolts together on the real car, so it flies together. Corner membership is matched on
`_<CODE>_` rather than a loose substring — round 1 shipped a bug where `FW_Endplate_L`
was mistaken for a corner part by a regex that matched too loosely.

**15 clusters, 616 parts, every part accounted for.**

---

## 7. Exploded layout — computed, collision-solved, room-checked

| cluster | parts | tris | offset (x, y, z) m | dist |
|---|---:|---:|---|---:|
| `MB` | 17 | 1,844,927 | 0, 0, 0 *(pinned core)* | 0.00 |
| `FD` | 10 | 685,308 | −0.170, 0, −1.718 | 1.73 |
| `BB` | 10 | 534,848 | −1.554, 0, +1.006 | 1.85 |
| `EC` | 13 | 394,122 | −1.785, 0, +1.155 | 2.13 |
| `CI` | 15 | 459,202 | +0.611, 0, +2.443 | 2.52 |
| `SW` | 65 | 288,904 | +0.302, 0, +1.208 | 1.24 |
| `halo_assembly` | 53 | 329,722 | +0.823, 0, +3.291 | 3.39 |
| `SP` | 13 | 485,712 | −1.012, 0, +3.373 | 3.52 |
| `NOSE` | 33 | 477,818 | +2.216, 0, −0.479 | 2.27 |
| `FW` | 120 | 720,048 | +2.382, 0, −0.823 | 2.52 |
| `RW` | 97 | 535,588 | −1.756, 0, +0.183 | 1.77 |
| `CORNER_FL` | 41 | 690,930 | +0.435, +1.243, −0.186 | 1.33 |
| `CORNER_FR` | 41 | 690,930 | +0.435, −1.243, −0.186 | 1.33 |
| `CORNER_RL` | 44 | 745,562 | −0.434, +1.240, −0.186 | 1.33 |
| `CORNER_RR` | 44 | 745,562 | −0.434, −1.240, −0.186 | 1.33 |

**Field extent 9.84 × 4.49 × 5.96 m**, top at Z 4.62. The showroom interior is
**30.0 × 22.0 m with a 6.50 m ceiling**, so it fits with **1.88 m of ceiling clearance**.

### Three round-1 defects designed out rather than rediscovered

**D160 redux — full-width parts must not explode laterally.** `SP_` (Y extent 1.48) and
`BB_` (1.51) are single meshes spanning *both* sides of a 2.005 m car, each with its own
centroid at Y = 0. Round 1 picked a lateral sign from that centroid, always got +1, and
slid the whole two-sided part 0.80 m **through the monocoque** — found by the user zooming
into a delivered 4K frame. The guard here is **measured, not name-based**: any cluster
whose lateral extent exceeds 60% of car width is redirected to explode vertically, so a
future full-width part cannot reintroduce it.

**D164 redux — the clearance sign.** Round 1's solver used `raw − clearance` and therefore
stopped while parts were still lapping, then reported success. Here clearance is **added**
to the required separation.

**The overlap gate runs before animation, not after render.** Round 1 shipped 19
overlapping module pairs. The initial computed layout here had **7** (worst: `CI`×`SP` at
398 mm). The solver resolves them by extending each cluster **along its own mechanical
direction** — never nudging it sideways, because a part shoved off-axis to win a clearance
argument stops looking like it came off the car. Result: **26 passes, 0 residual overlaps,
120 mm minimum clearance.**

A splay term was needed: `FW` and `NOSE` both explode along +X, and being colinear the
solver could only separate them by pushing further along the same line — producing a 15.11 m
field. Each cluster now also drifts in the axes it is *not* exploding along, by where it
sits on the car, so the front wing (low) and nose (above it) separate vertically exactly as
they sit. Field length dropped 15.11 m → 9.84 m and the solve halved to 26 passes.

---

## 8. What this constrains downstream

- **Beat 1 camera path** must weave a 9.84 × 4.49 × 5.96 m volume, floor to 4.62 m.
- **Every one of the 15 clusters needs a logged readable moment** in the beat sheet. No
  part seats without having been seen.
- **`CORNER_*` are 41–44 parts each** and seat simultaneously — four dense arrivals at once
  is the hardest moment to choreograph and to light.
- **`MB_` is 1.84 M triangles alone.** Sample tuning and LOD must budget around it.
- **`SW_` is 65 parts inside a 0.13 × 0.28 × 0.23 m box** — the densest cluster by far, and
  the one most likely to read as confetti. It gets a dedicated close pass, not a wide.
- **The macro audit (task #21) must test at the beat sheet's actual distances**, and the
  tyre Z-scale means tyre lettering is stretched 1.2–1.6× — check it resolves at 4K.

---

## 9. Provenance and reproduction

```
/opt/blender-5.2.0-linux-x64/blender -b ~/opus5-car-render/work/iter.blend \
    --factory-startup -P tools/inventory.py -- \
    --out docs/inventory_iter.json

python3 tools/explode_plan.py \
    --inv docs/inventory_iter.json --out docs/explode_plan.json
```

`work/iter.blend` is **read-only** to round 2. It is opened, never saved. Round 1's
deliverables in `finals/` and its blends are untouched.

Other blends present in round 1, not used as the round-2 source and recorded here so a
future reader does not wonder: `f1_complete.blend`, `f1_final_5090*.blend`, `f1_hq_v2.blend`,
`f1_exploded_posed*.blend`, `f1_ghost_posed*.blend`, `final_exploded.blend`,
`final_ghost.blend`, `final_claywire.blend`, `room_test.blend`,
`lightingagent_room_v3.blend`. `iter.blend` is the canonical scene — it is what
`tools/rebuild_scene.py` produces and what the website exported from.
