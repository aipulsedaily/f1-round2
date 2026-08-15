# STAGING R2-2461 to R2-2520 — the aerofoil cell

Agent `r2-2461-aerofoil`. Task: *"REINSTATED — bake the aerofoil cell, for the
opposite reason to the one it was proposed for."*

**Outcome: REFUSED, and not on pixel-footprint grounds.** The cell is
resolvable — spectacularly so. It is refused because **the defect it fixes is
not in the film.** Working below.

---

## R2-2461 — THE REINSTATING ARGUMENT, IN ONE SENTENCE, QUOTED

> **R2-721** — *"`--rear-wing aerofoil` is the right cell — **not because the
> tray holds anything** (it holds nothing, at 287 mm) but because it moves the
> chain behind the car: **16 foreground frames → 0**, 1,893 → 1,470 px, +0.23 →
> −1.04 m, car-local z from 1.27–2.70 down to 0.28–0.88, below `CAR_TOP_Z`."*

The arc, so the "opposite reason" is unambiguous:

| | |
|---|---|
| **proposed** (R2-700) | the solid mainplane's 58.6 % thickness acts as a **tray** that holds a structural member up on the bodywork; thin the wing and the member falls through |
| **refuted** (R2-707, strengthened by R2-911) | at 240 Hz the member never comes within **287 mm** of `wing_r`, and the collision margin is **0.15 mm**, not the 40 mm the refutation was argued against. *"The mainplane's 58.6 % thickness is not holding anything up, and never was."* |
| **reinstated** (R2-721, restated R2-916) | the defect is **depth order and screen extent, not contact**. The chain flies *between the lens and the car*. The aerofoil cell puts it **1.04 m behind** the car and below the deck line, and the foreground crossing goes **16 frames → 0**. |

R2-916 says it out loud: *"the recommendation is to adopt `--rear-wing
aerofoil`, on evidence that has nothing to do with the argument that produced
it. A lever chosen for a reason that turned out to be false still moved the
thing it was aimed at."*

**`docs/NEXT-REBUILD.md` does not mention the aerofoil anywhere.** The 4 August
recommendation was never carried into the rebuild manifest. That is a real gap
and it is reported, not silently patched — see R2-2465.

---

## R2-2462 — THE PIXEL FOOTPRINT, AND THE CATEGORY ERROR THE QUESTION INVITES

**Asked literally, the answer is zero pixels, in every frame of the film.**

`wing_r` is one of eighteen convex boxes and wedges in
`sim/breachlib.py::car_proxy_parts()`. It exists only inside the rigid-body
solver. R2-701 already wrote this down, and wrote down the trap:

> *"It is not the rendered car, it is not in any film scene, and no shot
> contains it. … `--rear-wing aerofoil` cannot [touch render geometry]:
> `car_proxy_parts()` is imported by the sim and by nothing that builds a
> scene."*

The rendered rear wing is **already** a properly swept thin aerofoil and this
flag does not touch it. So the pixel-footprint law does not apply to the cell:
the law governs **authored detail intended to be seen**, and this is a solver
input. Applying the law here would refuse the right thing for the wrong reason
— which is the mirror image of the 20-layer asphalt mistake, not a repeat of it.

**The law's legitimate target is the flag's OUTPUT — the bodies it moves.**
Measured, not quoted: the eight corners of each body's real box from
`sim/eastframe.plan()`, rigidly posed from the bake, projected through the
**live** camera at 3840×2160.

```
LARGEST ON-SCREEN SUBTENSE OF A BODY THE FLAG MOVES  (aerofoil cell, 4K)
  f890   TRN_z1_b04    1775.2 px   (solid cell: 1234.6 px)   range  3.0 m
  f957   TRN_z0_b05    1507.7 px                             range  3.6 m
  f933   TRN_z0_b04    1416.0 px
  f889   MUL04_S02     1244.6 px
  f887   MUL04_S01     1047.8 px
  f968   MUL05_S02      552.8 px   <- the body the whole argument is about

  frames with a moved body over 100 px          198 of 207
  frames where the largest is sub-pixel           0 of 207
  peak single-body screen displacement A vs S  3251.4 px  at f916
  frames where >=1 structural body moves >1 px  191 of 207
```

Subtense is computed over in-raster corners only, so a body crossing the frame
edge is **under**-counted. These are lower bounds.

**This is not a sub-pixel case. It is close to the largest picture event
available anywhere in the film** — bodies a metre and a half tall on screen, at
three metres from the lens, moved by up to most of the raster width. Had the
defect been real, this bake would have been worth almost any cost.

### the camera these figures are taken through is the live one, and the test is not vacuous

`sim/out/oner_camera_track.json` was dumped from `film14.blend`. The live camera
is `render/film19_path.json` (`docs/LIVE-CAMERA.md`, declared 23:21 on 08-07,
two generations past the `film17` that R2-917 checked against).

```
window f845-1051 live vs sim   dpos 5.0e-06 m   dquat 8.6e-07   dlens 5.0e-05 mm
NEGATIVE f1-844                dpos 9.132 m     dquat 9.4e-01   dlens 23.000 mm
NEGATIVE f2678-2978            dpos 7.2e-03 m   dquat 4.6e-01   dlens 56.000 mm
```

Over the frames that matter the two are **the same camera to float noise**, and
the same test over beat 1 and beat 6 **fails loudly**, so the PASS is not
vacuous. The beat-5 promotion (f1195–f2677) and the beat-1 re-author (f2–f780)
both miss this window entirely.

---

## R2-2463 — WHY IT IS REFUSED: THE DEFECT IS IN A BAKE THE FILM DOES NOT CARRY

This is the finding, and it holds the whole task.

**R2-721's own table names the bake each figure comes from:**

```
bake              R2-700 by eye   px @4K   vs car's nearest surface   frames in front
R2281 RE-BAKE        ACCEPT        1,417        -0.83 m BEHIND              0
R2387 AIR            REJECT        1,893        +0.23 m IN FRONT           16  (f969-984)
R2701A aerofoil        -           1,470        -1.04 m BEHIND              0
```

**The 16-frame foreground crossing exists in R2387 and in neither other bake.
The shipped bake is not in the table at all.**

The film does not carry R2387. It carries **R6**, and that is pinned in three
places:

```
sha256 3e312977987ac57a...  sim/out/breach_film.npz
sha256 3e312977987ac57a...  sim/out/breach_film_R6_SHIPPED.npz   <- byte-identical
sha256 b7f6041d30560b44...  sim/out/breach_film_R2387.npz        <- NOT this one
```

* **R2-513** applied the ship with `--film sim/out/breach_film_R6_SHIPPED.npz`
  explicitly, calling R2387 *"the trap next to the fix"*.
* **R2-778** re-verified the shipping table byte-identical and untouched.
* **R2-4097** (was R2-1097; renumbered 2026-08-14, #170) — the most recent
  audit, and **after** R2-916 — certifies
  *"the shipping bake is verifiably the right one"*, `MUL05_S02 0.1449 m`, and
  notes *"a wrong bake reads 55.35 m here"*. 55.35 m **is R2387**.
* `docs/NEXT-REBUILD.md`'s verification bar demands
  `BF_MUL05_S02 = 0.1449 m — the guard that proves the right bake landed`.

**And the shipped bake does not produce a chain at all.** Measured over all 152
structural bodies, net displacement home-to-rest:

```
bake                      >1 m   >5 m   max net      top movers
SHIPPED (R6) = the film      4      0     4.431 m    MUL05_S01 4.43, MUL05_S00 3.93
R2387 AIR (never shipped)   28     24    55.348 m    MUL05_S02 55.35, TRN_z0_b05 55.14
R2701S solid A/B            28     24    26.534 m    MUL05_S02 26.53, TRN_z0_b04 26.43
R2701A aerofoil A/B         20     14    29.660 m    MUL05_S00 29.66, MUL05_S01 28.94
```

In the film, **four** bodies leave the wall and none travels five metres — which
is exactly the shape NEXT-REBUILD and R2-092 declare correct: *"only `MUL05_S00`
and `MUL05_S01` ever leave the east frame (3.93 m and 4.43 m)."* `MUL05_S02` —
**the body the entire chain argument is about** — moves **0.1449 m** and stays on
the wall. `ridepose`'s verdict on the shipped table is **VACUOUS: aboard 0,
carried 0**, and R2-916 reads its chain search as *"148 bodies still joined at
20 mm, which is not a chain but an intact wall."*

**So there is no chain between the lens and the car in the film, because nothing
comes off the wall to make one.** The aerofoil cell is a variant of R2387's
simulation regime — R2-702 says so: *"one variable against the R2387 production
table: same bundle hash (`7db0e9db3f025c50`), same thresholds, same air model,
same friction, same substeps"* — and R2387 is a regime the ship path explicitly
refused.

### the two reasons therefore do not conflict; the reinstating one has no target

R2-721/R2-916 are **correct and remain correct**: given a re-bake in the R2387
regime, `--rear-wing aerofoil` is the right cell. That is a statement about
**which flag to set when you re-bake**. It was never a reason **to** re-bake, and
R2-1122 says where that reason must come from: *"it belongs to whoever next has
a reason to re-bake."* This task has not brought one.

### what baking it now would actually cost, beyond the money

1. **It would break the ship guard by design.** `BF_MUL05_S02 = 0.1449 m` is
   NEXT-REBUILD's proof that the right bake landed. Any aerofoil table moves
   `MUL05_S02` by 26–29 m. Adopting one silently converts the manifest's
   correctness guard into a failing gate, and the manifest is *"the gate to the
   master"*.
2. **The existing A/B table is not shippable and a full-span bake is genuinely
   missing.** `breach_film_R2701A.npz` spans **207 frames (f845–1051)** against
   production's **321 (f845–1165)**, and `apply_breach.py` extrapolates CONSTANT
   past the last key. At f1051 the aerofoil cell still has **3,047 of 3,948
   bodies moving faster than 1 mm/frame, the fastest at 14.12 m/s**, against the
   production table's **1 of 152 structural bodies** and 0.03 m/s. Applying it
   would freeze three thousand bodies in mid-air and hold them there for the
   remaining 1,927 frames of a one-shot film. So the task is *not* redundant —
   it is simply pointed at a defect that is not there.
3. **It would desynchronise other agents.** Brokers 3–11 are saturated with a
   whole-film proxy built on the shipped breach. A new production breach table
   invalidates it mid-flight.

**No GPU time was spent and no bake was submitted. Nothing was rendered.**

---

## R2-2464 — A CONTROL THAT HAS SILENTLY STOPPED CONTROLLING: `sim/sagpx.py`

Found by running it rather than trusting it, and **observed to fail**, which is
the only reason it is trusted now.

`sagpx.controls()` has four controls. Its only *aiming* control asserts the
breach centre projects to (1920, 1080) at f2901.

```
sim track  (film14)  f2901 breach centre -> (1920.0, 1079.9) px   in_raster True   FIRES
live       (film19)  f2901 breach centre -> (-14411.9, 2889.4)    in_raster False  DEAD
```

The beat-6 re-key moved the lens 39.254 → 54.122 mm and swung the aim; the
camera position at f2901 is unchanged to 0.1 mm, so **every position-based check
still passes** while the aiming control is four screen-widths off. Under the live
camera the breach is never centred — nearest approach is **f1444, 304.6 px off**.

**Consequence:** any pixel figure taken through `sagpx` against the live camera
is currently produced with 3 of 4 controls firing and the projector's only
aiming assertion dead — and `ALL_FIRE` reports `false` without saying which arm
died, so a caller that checks the boolean learns nothing about *what* is wrong.

My own measurements are unaffected: in **f845–1051** the live camera and the sim
track are identical to 5.0e-06 m, so the control calibrated on one applies
verbatim to the other, which is why R2-2462 validates on the sim track and then
proves the window identity separately with two negative controls.

**Not fixed here.** `sagpx` is shared breach instrumentation and re-deriving its
aim frame is not car/aero work; another agent may be mid-measurement on it.
Flagged for whoever owns it.

---

## R2-2465 — FRAME NOMINATION, PRE-REGISTERED AND UNRENDERED

Recorded **before** any frame was opened and while the recommendation is
*refuse*, so that a future re-bake cannot pick its own judges. If anyone ever
has an independent reason to re-bake the breach, these are the frames on which
`--rear-wing aerofoil` must be judged, and what each is for:

| frame | what it shows | measured |
|---|---|---|
| **f890** | `TRN_z1_b04` at its largest — the biggest single moved body anywhere in the window | 1,775.2 px aerofoil vs 1,234.6 px solid, range 3.0 m |
| **f916** | the largest A-vs-S disagreement in the film; if the cells look alike here they look alike nowhere | 3,251.4 px centroid separation |
| **f957** | `TRN_z0_b05`, the second-largest body, near peak | 1,507.7 px, range 3.6 m |
| **f968** | `MUL05_S02` at its largest — **the body the entire chain argument is about**, and the one the ship guard pins | 552.8 px |
| **f972** | R2-700's original judge frame, kept deliberately so the new read is comparable to the old one | R2-721 shows this window was itself the artefact |

**f969–f984** is the 16-frame foreground crossing in R2387 and must be inspected
as a block, not sampled — R2-721 records that picking f967–977 from the pictures
is what produced the original wrong verdict.

---

## Provenance

* Measured against `sim/out/breach_film{,_R6_SHIPPED,_R2387,_R2701A,_R2701S}.npz`
  and the live camera `render/film19_path.json` via `tools/live_campath.py`.
* **Nothing in the tree was modified.** No bake, no render, no GPU, no spend.
  `sim/`, `world/`, `render/` and `tools/` are untouched; the only file written
  is this one. `docs/DEFECT-LOG-R2.md` was **not** edited.
* `~/opus5-car-render` was not read from or written to.
* Lease `r2-2461-aerofoil` holds `docs/STAGING-R2-2461-to-R2-2520.md` only.
