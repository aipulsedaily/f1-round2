# STAGING R2-2041 .. R2-2100

## R2-2041 — two proven fixes that could not reach a frame, applied and verified IN THE ARTEFACT

Both were diagnosed, measured and signed off by earlier blocks. Neither was in
the ship path. **This is the fourth time on this project that a complete,
correct change has been structurally unable to reach a frame** — `film18`
shipped without four modules, `build_nearband.py` sat wired into nothing, and
these two were the same shape for the same reason: the change was in a file
nobody was going to run, or in a file somebody else held.

**The first thing this block did was ask the shipped artefact whether the
defects were still there**, because "already fixed" has been the right answer
six times today. `render/film21.blend` (10,007,785,627 bytes, built 02:42),
opened with `bpy.data.libraries.load(link=True)` — the 10 GB file interrogates
in about two minutes on this 11 GB box, no scene instantiated, no GPU:

| material in `film21.blend` | nodes | `R2CP_*` | `R2CS_*` | `Mapping.Scale` |
|---|---|---|---|---|
| **`CarbonFibre`** | 68 | **0** | **0** | **190.0, 190.0, 190.0** |
| **`CarbonFibre.001`** (the twin) | 68 | **0** | **0** | **190.0, 190.0, 190.0** |
| `CarbonMatte` | 59 | 0 | 0 | 62.8319 ✓ |
| `LiveryPaint` | 239 | **94** | 0 | — ✓ |
| `SuedeGrip` | 72 | 0 | **43** | — ✓ |

`TDP_*` node groups in `film21.blend`: **NONE**. Sockets named
`Traffic Passes`: **0**.

**Both defects were live in the delivered blend.** Neither fix was present.

---

### Fix 1 — `CarbonFibre`, the largest carbon area on the car

`CarbonFibre` covers the front wing, rear wing, barge boards, nose, engine
cover, sidepod and halo, and it was **the only car material in the delivered
blend carrying no round-2 fix at all**. Blender's Wave node multiplies its
coordinate by 20, so a `Mapping` Scale of S in front of a Wave at Scale 1.0
emits a period of `(2*pi/20)/S` metres. 190 was authored as "190 repeats per
metre" and delivers 604.8/m — a **1.6535 mm twill, 0.87 px** at the beat-1
payoff. Sub-pixel: it averages to nothing and the panel behaves as a dead-flat
mirror under a 0.045-roughness coat.

**Round 1 predicted the symptom verbatim while mis-fixing it.** Its own
docstring condemned 1.3 mm as *"far below a pixel at any sane render scale, so
it averaged to nothing … flat endplates caught the cove and rendered as white
plastic"*, then shipped **1.6535 mm — a 27 % improvement on a defect that
needed 4×**. Thirteen months later the client wrote *"the front wing is a plain
white bent sheet"*.

**Why nobody fixed it:** `world/car_paint.py` fixed the identical bug on
`LiveryPaint` and `tools/cockpit_surface.py` fixed it on
`CarbonMatte`/`SuedeGrip`. Each targets materials **by name**. Two agents fixed
the same bug on either side of the biggest instance of it.

#### Where it landed, and why there

`tools/cockpit_surface.py`, new `fix_carbon_fibre()`, with `CarbonFibre` added
to `TARGET_MATERIALS`. **That file was chosen because it is the only carbon
fixer PROVEN to be in the ship path** — `v126/build_car_cs.sh` runs it on
`world/R2829_car_anim_driver.blend`, and its output is what
`tools/build_film_scene.py --car` consumed to make `film21`. Putting the fix
anywhere else would have repeated the defect this block exists to close. It
also already owns the constant: `MAPPING_SCALE = WAVE_FACTOR / WEAVE_PITCH_M`
= **62.832**.

#### It is ONE constant, and that is a decision, not laziness

`fix_carbon_matte` makes three edits, because re-pitching a weave divides its
radiance modulation by the pitch ratio. Here the arithmetic says not to:

| | pitch | amplitude | modulation `m` |
|---|---|---|---|
| round 1 | 1.6535 mm | 0.0475 mm | **0.813 pp** — far above the band, and sub-pixel, so it only ever delivered noise |
| after, **bump untouched** | 5.000 mm | 0.0475 mm | **0.270 pp** — inside `isotropic_micro` (0.12, 0.45) |

`CarbonMatte` was lifted to 0.32 pp because a shaded cockpit interior lit by sky
and bounce under-delivers modulation for a given slope. `CarbonFibre` is
exterior bodywork under a rig carrying **61 % of the interior load**, so it does
not need the lift. **The in-band result is asserted in code, not assumed** — the
function raises if leaving the bump alone lands outside the band, which is what
makes "leave it alone" a decision somebody made rather than a step somebody
forgot.

Nothing else moved: not the triplanar projection, not the grazing fade, not the
coat, not the imperfection layer. Reversible by setting `Scale` back.

#### Verified in the built artefact

`world/R22041_car_anim_driver_CS.blend` (408.6 MB), built from the same round-1
parent `film21`'s car came from, read back in link mode — **16 checks, 0
failures**:

```
[PASS] CarbonFibre: Mapping.Scale     == 62.8319   reads 62.8319
[PASS] CarbonFibre: Mapping.001.Scale == 62.8319   reads 62.8319
[PASS] CarbonFibre: Mapping.002.Scale == 62.8319   reads 62.8319
[PASS] CarbonFibre: six TexWave, all still at Scale 1.0
[PASS] CarbonFibre: emitted twill pitch == 5.000 mm    5.0000 mm = 2.63 px at 526 px/m
[PASS] CarbonFibre: weave bump still round 1's 0.0475 mm
[PASS] CarbonMatte: still at 62.8319 (not regressed)
[PASS] LiveryPaint: carries 94 R2CP_* nodes
[PASS] LiveryPaint: Metallic is LINKED (its default is dead data)  default reads 0.6200
[PASS] LiveryPaint: effective Metallic == 0.10                     computed 0.1000
>> STAGE RESULT: OK (0 failures)
```

The build log's own line: `CarbonFibre: weave pitch 1.6535 -> 5.0000 mm (0.87
-> 2.63 px at 526 px/m, the bodywork at f599)`. **0.87 → 2.63 px is exactly the
number the diagnosis predicted**, and 2.63 px clears the repo's ~2.5 px
resolvable threshold that 0.87 px never could.

**The `LiveryPaint` rows are the trap, checked deliberately.** Its `Metallic`
reads default **0.62** and is LINKED through a MULTIPLY of
`0.16129031777381897` = 0.10/0.62 exactly. Any checker reading `default_value`
reports round 1 forever. This block's instrument **follows the link and computes
0.1000**, so it is known to be able to tell a fixed material from an unfixed one
— an audit that has never distinguished the two is not evidence.

#### The second half of the prescription is BLOCKED, and is not absorbed

R2-1146 prescribed **two** items: the constant, and *"one narrow strip source
added to the rig with the four clipping-tuned lamps untouched"*. **The constant
is done. The lamp is not, and it is reported rather than quietly dropped.**

Measured, not assumed. The rig **is** in `film21.blend` — 23 interior practicals
plus `SKY_Sun`, with Key/Fill/Rim/Kick at exactly the diagnosed **15.6400 /
17.0000 / 2.9760 / 1.8600 m²**. But:

* The lamps are **baked geometry and data inside the car blend**
  (`R21701_car_anim_driver_CS.blend` carries `SHOWROOM, PROPS, LIGHTS, CAR,
  CAMERAS`, appended whole by `tools/build_film_scene.py:387`). **Nothing in
  `f1-round2` ever executes round 1's lighting stage.**
  `/home/zany/opus5-car-render/build/s05_lighting_v2.py` has not been touched
  since Jul 26 and its own docstring says it is "not wired into
  `rebuild_scene.py`" — a file that does not exist. **Editing
  `build_three_point` has no path to a frame**, which is precisely the defect
  class this block was opened to close.
* **The artefact and that source already disagree**: the shipped spreads match
  v1 `s05_lighting.py` (Fill 120°, not v2's 140°) and every base energy is
  scaled off source by a *non-uniform* factor (Key ×1.09751, Fill ×1.23841, Rim
  ×1.07345, Kick ×1.09751) that appears nowhere in round-1 source.
* A round-2 implementation would have to insert the lamp in
  **`tools/build_film_scene.py`** — **held by another agent's live lease
  (`inflight-auto`)** — and reconcile a hard invariant that gates every single
  save: `build_film_scene.py:481` refuses on *"the interior load is 46,203.313 W
  over 23 lamps … **a 24th lamp breaks it**"*, restated in
  `docs/NEXT-REBUILD.md:102-103`.

**The lease is not released and the path is dropped instead.** The lamp needs
its owner, a decision about the 23-lamp invariant, and its own A/B; it is not
something to absorb into a materials fix. Recorded as OPEN.

---

### Fix 2 — the tyre marks: signed off at N = 1000, wired into nothing

The client: *"tire marks on the showroom and concreate is not noticable
enough."* R2-1222 handed over a precise patch spec, verified at N = 1000 with 13
checks and `>> STAGE RESULT: OK (0 failures)` against `build_surface`'s real
kit — and **`world/build_surface.py` contained no `Traffic Passes` and no
deposit**, because that file was held by another agent. It is free now.

Applied to `world/build_surface.py::_mat_concrete`, three edits, in the order the
handover fixes and calls non-negotiable — field → apply group → the substrate's
own bumps → BSDF, because the group *reduces* both substrate height stages
(rubber fills texture) and the reduction has to land before the bumps read them:

1. Round 1's five painted launch-streak lines deleted, plus the roughness line
   that consumed `launch`. Its only two consumers are now fed by the group.
2. `_apply_tyre_deposit()` instantiates `TDP_DepositField` and
   `TDP_Apply_Concrete` by hand — `_mat_concrete` uses `build_surface`'s own
   `_G` kit, which has no `.pin_named()` and no `.object_coords()`, so
   `TDP.field_node()` / `world_position()` / `mat_concrete()` cannot be called
   from it. World position is built fresh as `TexCoord→Object` through a POINT
   `OBJECT→WORLD` transform, **not** by reusing the function's existing `P`:
   that is object space, and the field is authored in world metres. They
   coincide today only because `_build_access` writes world-coordinate vertices
   into an untransformed object — a build coincidence, not a guarantee.
3. `Specular IOR Level` now comes from the group instead of a literal `0.32`.
   This is R2-1213's missing channel.

#### THE HANDOVER'S OWN CHANNEL LIST WAS MISSING `Interface`, AND ITS OWN VERIFIER SHIPPED THE BUG IT WARNS ABOUT

The prose spec in `docs/STAGING-R2-1211-to-R2-1240.md` wires nine channels into
`TDP_Apply_Concrete` and **omits `Interface`**. So does
`tools/r2_1222_verify_handover.py`, the 13-check verifier that returned
`OK (0 failures)` and was cited as the evidence the handover was applyable.
`Interface` defaults to `0.0`.

**`Interface` is the brightening term** (`ig = _wet_grain(t, ifc, grain)` inside
`build_concrete_group`) and it is the exact channel `itemkit.assert_wired`'s
docstring was written about:

> An A/B was rendered to decide whether a deposit material read better than the
> paint it replaced. Its treatment arm was grafted in with `Interface` … LEFT
> UNLINKED. Nothing failed. The socket fell back to its default, the render
> completed, the numbers looked ordinary, and the measured verdict was "the fix
> does not work". **It was reported to the client in those words.**

Applying the handover verbatim would have reproduced R2-1226 exactly. The
reference wiring — `tyre_deposit.mat_concrete()`, which the handover itself
names as authoritative over its prose — **does** pass `Interface`, and that is
what was followed. `K.assert_wired` is now asserted on both nodes at build time,
so the omission cannot recur silently. `Traffic Passes` is deliberately **not**
in either list: it is a typed constant on the way in, and an exemption you typed
is a decision.

#### `Traffic Passes = 1000`, and it is per-surface

R2-1226, signed off, and deliberately not derived. One tractive-slip pass moves
≈10.6 nm of rubber over 0.34 % coverage, changes no albedo, and measures
**+0.71 % with a p50 of −0.91 %** — it straddles zero. N = 1000 says this pit
exit has been run all season. Measured in the film at N = 1000: **−17.97 % /
−14.04 %, 3.2× the paint it replaces, one unbroken segment, 0.924-coherent,
98.3 % longitudinal**, crossing SNR 5 within **0.40 m**, adding **+0.00078 pp**
of pure black against a control already carrying 0.00216 % from the car's own
shadow.

N = 60 was the first answer and was **the worst available value**, not merely an
order of magnitude short: the interface term saturates at 99.7 % (all the
brightening) while coverage reaches 18.6 % (almost none of the darkening), so
the mark broke into 14 segments with 16 sign flips and its two tracks carried
opposite signs.

**`APRON_TRAFFIC_PASSES` is a module constant in `build_surface.py`, not a
global.** The apron is the only surface where N is an open question;
`tyre_deposit`'s deck and floor are N = 1 by construction and are not this
module's to set.

#### The time binding, which is the part that is easy to miss

The field masks **both** terms by `Front X`, keyed from the wheel's own
per-frame world x. **Without the binding the deposit exists on frame 1, under a
parked car.** It also fails *silently* if the material has no user in the scene:
an animated shader tree is only evaluated by the depsgraph when something in the
scene uses the material. `bind_time` is therefore called from `build()`, after
`_build_access` has put the material on an object, and **both preconditions are
asserted rather than assumed** — the material's user count, and a keyframe count
of at least 2.

#### Verified in the built artefact

A scoped `assemble.py --mods=surface` build (43 s) → 199 MB artefact, then read
back off the sockets. **37 checks, 0 failures:**

```
[PASS] Traffic Passes NOT linked (a typed constant)
[PASS] Traffic Passes == 1000.0000                      read 1000.0000
[PASS] Apply_Concrete.Interface is LINKED
[PASS] BSDF.Specular IOR Level is LINKED                (was a literal 0.32)
[PASS] Front X carries 248 keys                         read 248
[PASS] Front X @ f816    read -1.81200 want -1.81200
[PASS] Front X @ f818    read -1.79280 want -1.79280
[PASS] Front X @ f822    read -1.68860 want -1.68860
[PASS] Front X @ f827    read -1.55840 want -1.55840
[PASS] Front X @ f1064   read +62.03892 want +62.03892
[PASS] round 1's launch-streak MapRange is gone
[PASS] zero image-texture nodes
>> STAGE RESULT: OK (0 failures)
```

All five depsgraph-evaluated frames reproduce the handover's measured values to
better than 5e-4, which proves the animation is live in the scene and not merely
an action nobody evaluates. 248 keys is the handover's own figure exactly.

**It reaches the frame:** `M_Surf_Concrete` is on `SURF_AccessRoad`, **35,904
polys**, in the shipped `film21.blend` — checked before spending a world
rebuild, because an item module superseding the apron would have made all of
this invisible for the fifth time.

---

---

## R2-2042 — the rebuild, and BOTH FIXES READ BACK OFF THE SHIPPED 10 GB FILM

Neither fix is finished at "the source is correct" — that has been the trap four
times. The chain was run, in order, once.

| artefact | what it carries | verdict |
|---|---|---|
| `world/R22041_car_anim_driver_CS.blend` | 408.6 MB, `cockpit_surface.py` on the same round-1 parent `film21`'s car came from | `R2881_COCKPIT_SURFACE_OK`, static guarantee held (every `CI_*` vertex and fcurve byte-identical) |
| `render/world/assembly/r2/assembly14.blend` | 9.58 GB, `assemble.py` over all seven modules | `ASSEMBLY14_FIXES_PRESENT`, **7/7 acceptance** |
| `render/film22.blend` | 10.01 GB, `build_film_scene` + `r2791_apply_focus` | `REBUILD22_BUILT` |

**assembly14's acceptance asked the output, not the input** — it had to prove it
carried the new fix *and* did not regress the last one:

```
tyre_deposit_traffic_passes  want 1000.0     got 1000.0     OK
tyre_deposit_front_x_keys    want 248        got 248        OK
access_quads                 want 35904      got 35904      OK   (a material fix moves no quads)
triangles                    want 2721433    got 2721433    OK   (surface build bit-identical)
sward_C                      want 56063      got 56063      OK   (assembly13's number, not regressed)
grass_in_corridor            want 1386383    got 1386383    OK   (1,370,543 = R2-1821's holes are back)
```

`film22` came out at **32,045 objects — the same count as film21** — with
`exposure -3.628 AgX None` re-asserted after `build_sky`, the sky/camera bind
checked on 2 live driver targets, and focus keys **numerically identical to
film21's** (`keys=621 guard=clean maxstep=0.3059`). The camera is therefore
matched between the two arms by construction, not by assertion.

### Read back off the sockets of the 10 GB film, in link mode

**Carbon — 24 checks, 0 failures.** Including `CarbonFibre.001`, the twin: it is
value-identical, but if only one were fixed then whichever the wing actually
uses would decide the frame.

```
CarbonFibre     Mapping/.001/.002 .Scale == 62.8319   emitted pitch 5.0000 mm = 2.63 px
CarbonFibre.001 Mapping/.001/.002 .Scale == 62.8319   emitted pitch 5.0000 mm = 2.63 px
CarbonMatte     still 62.8319 (not regressed)
LiveryPaint     94 R2CP_*; Metallic LINKED, default reads 0.6200, EFFECTIVE 0.1000
```

**Rubber — 0 failures.** `Traffic Passes` reads **1000.0000** off the built
socket in the delivered film, `Interface` is LINKED, `Specular IOR Level` is
LINKED to the group, and `Front X` still carries its **248 keys** after two
further save passes rewrote the file.

**And the per-surface red line held, provably.** The film contains **exactly
two** `TDP_*` groups — `TDP_DepositField` and `TDP_Apply_Concrete`.
`TDP_Apply_BrushedMetal` and `TDP_Apply_PolishedFloor` finish with zero users
and are dropped on save, so the showroom deck and floor (N = 1 by construction)
**cannot** have received the apron's N = 1000: their apply groups are not in the
film at all. That was found by a check of mine that was wrong in the safe
direction — it expected four groups — and the artefact's answer was better than
the question.

---

## R2-2043 — THE FRAMES. 4K, 1:1, matched camera and exposure

Six frames, `film21` (BEFORE) against `film22` (AFTER), same camera `ONER`, same
3840×2160, same 512 samples, same `--dof scene`, same exposure. Rendered on a
rented RTX 5090 at $0.4538/hr; **total spend $0.30**, credit $54.36 → $54.04.

### Carbon, f599 — the client's "plain white bent sheet"

f599 was chosen over the ~60 %-frame-width frames (f661/f725) because it is the
frame the diagnosis measured 0.87 px on, the frame the client judged, and it
carries **0.9 px of smear** where f661 sits mid-orbit and is motion-blurred. The
car fills 89 % of frame width there.

**The BEFORE crop is the client's complaint, exactly**: the front-wing endplate,
the vanes and the nose render as flat grey-white plastic with no weave anywhere
— round 1's own docstring predicted this in the words *"flat endplates … rendered
as white plastic."* **The AFTER crop is woven carbon**, the twill legible across
the whole endplate at 1:1.

```
render/r22041/AB_f599_endplate.png     620x480 @ (300,1500)   1:1
render/r22041/AB_f599_frontwing.png    800x650 @ (197,1144)   1:1
```

Crops were chosen on the BEFORE frame and applied unchanged to the AFTER frame —
a moving crop makes "it looks better now" unfalsifiable.

### Rubber, f1030 — wide, sunlit, in focus

**Two unbroken longitudinal tyre tracks now run down the pit-exit apron where
the BEFORE frame has bare concrete.** Measured on the delivered 4K frames, not
on a rig:

```
mark pixels (delta < -1%)          87,381
mean luminance inside the mark     BEFORE 0.3647 -> AFTER 0.3207     -12.08 %
delta p50 -0.0392   p90 -0.0157   p99 -0.0105   worst pixel -0.1438
```

−12.08 % *in situ*, under real sun, shadow and the concrete's own ±14.5 % mottle,
against the −17.97 % / −14.04 % measured on the controlled rig at the same
N = 1000. The mark is where the derivation puts it — on the wheels' own tracks —
and not where round 1 painted it.

```
render/r22041/AB_f1030_apron.png       800x600 @ (2500,500)   1:1
```

### The pure-black guard, checked on every frame of both arms

```
beat 1  f599   BEFORE 0 px (0.0000 %)      AFTER 0 px (0.0000 %)     mean 0.4556 -> 0.4554
beat 1  f661   BEFORE 61 px (0.0007 %)     AFTER 68 px (0.0008 %)    mean 0.4412 -> 0.4412
        f1030  BEFORE 89 px (0.0011 %)     AFTER 88 px (0.0011 %)
```

**f599 is exactly 0.0000 % on both arms**, which is the constraint as written.
**f661 carries 61 crushed pixels BEFORE the change** — it is pre-existing in
`film21` and not caused by either fix; the change adds 7 pixels, +0.0001 pp.
Reported rather than rounded away. Frame means move by at most 0.0002, so
neither fix has disturbed the exposure.

---

### The instrument failed three times in this block, in the direction that flatters

Recorded because this project's own record is that its instruments were the
problem more often than its renders were.

1. **`verify_rubber.py` reported 5 failures on a correct artefact.** It compared
   node identity with `is`. Two reads of the same node return two different
   Python wrappers, so an identity test on `bpy_struct` is **always** False —
   it fails on a *correctly* wired material. `cockpit_surface.verify()`
   documents this exact trap in a comment, and the new instrument walked into it
   anyway. Fixed to compare by name; 0 failures.
2. **`verify_carbon.py` raised `ValueError` on a `Mapping.Scale` Vector** and
   **Blender exited 0**, printing six PASS lines and *no* `STAGE RESULT` line at
   all. A reader watching the PASS lines would have called it a pass. This is
   the whole reason the project judges on the printed token and never on `$?`.
3. **`verify_film_rubber.py` demanded four `TDP_*` groups** and reported FAIL on
   a correct film. Two is right, and the reason two is right is itself the
   evidence that N = 1000 did not leak to the deck and the floor.

None of the three was in the artefact. All three were in the thing measuring it.

---

### Files, leases, and what was deliberately not touched

Claimed under `r2-2041-carbon-rubber`:

```
world/build_surface.py                                 tools/cockpit_surface.py
docs/STAGING-R2-2041-to-R2-2100.md                     world/R22041_car_anim_driver_CS.blend
render/world/assembly/r2/v126/build_assembly14.sh      .../run_rebuild22.sh
```

**Not touched, held by others:** `tools/build_film_scene.py` and
`tools/r2791_apply_focus.py` are called, never edited.
`render/world/assembly/r2/SHIPPING.md` is held by `inflight-auto`; its
one-line world declaration must move for any build to run at all, so it is
edited on disk and **not staged or committed** — the declaration is its owner's
to make permanent. No lease was released.

`docs/DEFECT-LOG-R2.md` not edited.
