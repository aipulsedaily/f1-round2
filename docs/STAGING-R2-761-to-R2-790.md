# STAGING R2-761 .. R2-790 — the breach fines (task #129)

Staged for merge into `docs/DEFECT-LOG-R2.md` by identity, never by position.
Nothing in this block edits the defect log, `sim/out/breach_film.npz`, or any
shipped blend.

New source: `sim/debris.py`, `sim/debrismesh.py`, `sim/debris_demo.py`;
`sim/apply_breach.py` gains `--debris` (OFF by default).

---

## R2-761 — THE DEBRIS IS ABSENT BY CONSTRUCTION, AND THE MASS THAT IS MISSING IS 14.398 kg, EXACTLY, AND THE PROJECT HAS BEEN PRINTING IT FOR WEEKS

R2-129 traced the absence correctly and stopped one step short of the number.
`sim/debris.ledger()` builds every shard twice — once as the pane's own cell,
once as `shardmesh.prism` actually meshes it — and differences the signed
volumes. Over all 3,796 non-intact shards:

```
the pane's own glass, cell area x 11.5 mm      2,255.308 kg
after shardmesh.KERF_M (0.4 mm inset)          2,240.909 kg
after the 0.6 mm arris chamfer as well         2,239.923 kg

    KERF     14.399 kg      CHAMFER  0.986 kg      TOTAL DELETED  15.385 kg
                                                   = 0.682 % of the wall
```

**`mass_after_kerf_kg` is 2,240.909 kg. The figure this project quotes for the
glass being driven through the wall is 2,240.9 kg.** They agree to four
figures, and nobody put it there on purpose: the headline mass has always been
the *post-kerf* mass. The pane's actual mass is 2,255.3 kg. The 14.4 kg
difference is not rounding, not an estimate anyone made, and not a modelling
approximation — it is `shardmesh.KERF_M`, and it is the glass that exists in the
wall and exists in no rendered object.

`shardmesh.py` already anticipated this in its own words, justifying the inset
as *"the crack takes material with it, which is also what a real crack does: the
fracture surface is not a plane of zero thickness, it sheds dust"*. **That
sentence was written and never kept.** The debris pass is it being kept.

**And the ceiling must not be spent as a budget.** 0.4 mm was chosen to stop
Bullet exploding (the first full-wall bake without it reached 120.7 m/s and lost
the wall before the car arrived). A real crack in soda-lime glass has a kerf of
*microns*. Using 14.4 kg as a dust mass would over-state the physical fines by
two to three orders of magnitude. It is a ceiling; the budget is derived
elsewhere (R2-763) and comes to 13.5 % of it.

---

## R2-762 — A DEBRIS **CLOUD** SHOULD NOT BE BUILT, AND THE REASON IS ARITHMETIC RATHER THAN TASTE

The brief invited a well-defended decline of part of the ask, and this is it:
**the "cloud" in "breach debris cloud" is the wrong object.** What should be
built — and has been — is a *field of fine glass* plus a *declared optical
burst*. Three independent arguments, none of them about taste:

**(a) Laminated glass does not shed a cloud. That is what the interlayer is
for.** A 5 / 1.5 PVB / 5 laminate struck at speed crazes, tears and hinges;
the fragments stay bonded to the PVB and travel as slabs. The shipped plan
already encodes this (`fracture._finish` laminates 15 % of shards) and the
delivered frames show it: R2-700's "continuous sheet" is not purely a defect,
it is partly what laminated glass *does*.

**(b) The mass is not there.** The total free-fines budget derivable from the
contact is **2.073 kg out of 2,255.3 kg — one part in 1,088**. Even the
physical maximum — `f_spall = 1.0`, every gram of the crushable outer ply inside
the contact footprint leaving as free debris — is 10.04 kg, and that is still
only 65 % of the kerf ceiling. A cloud a viewer can point at needs an order of
magnitude more mass than this wall contains in a form that can leave it.

**(c) The project's own calibration rule forbids it.** *"If a viewer can point
at the dirt effect, it is too strong."* A debris cloud at this beat would be
exactly a pointable effect, and R2-546's own complaint about the existing ground
debris — *"pepper, not glass"* — is the failure mode a badly-scaled particle
pass reproduces at ten times the cost.

**What replaces it.** Individually resolvable flakes, frosted on every face, at
the density and size distribution the physics gives, catching the 12.47 deg sun
and smearing into 100-200 px streaks at this beat's shutter. Nothing to point
at; a frame that is alive instead of one that is clean.

---

## R2-763 — THE BUDGET IS DERIVED FROM THE CONTACT, AND ONE NUMBER IN IT IS A JUDGEMENT, NAMED AND BRACKETED

`fracture.Impact.energy` is a stretched exponential whose exponent `q = 1.7` was
chosen, in `fracture.py`'s own words, so the crushed zone has *"a flat top the
width of the contact, which is what a comminuted zone is"*. `E_CRUSH = 0.90` is
the edge of that flat top — a **reading** of an existing parameter, not a new
one. Measured on the shipped plan:

```
crushed footprint (energy >= 0.90)        0.7246 m2   of 78.445 m2 fractured
outer ply (5 mm) inside that footprint    9.057 kg
f_spall = 0.12                            1.087 kg    crush spall
chamfer (the arris, deleted by the mesher)0.986 kg    arris spall
                                          --------
                            free fines    2.073 kg    = 13.5 % of the ceiling
```

**`F_SPALL = 0.12` is the only judgement in the module.** It is alone, named,
sweepable without a rebuild (`--f-spall`), and bracketed by two independent
estimates that do not depend on it:

* a **fracture-surface roughness model** — a 3 um layer detaching from both
  faces of 540 m of crack through 11.5 mm — gives **93 g**, all sub-50 um;
* a **contact-volume model** with every crushed grain going free gives
  **9.06 kg**.

0.12 sits between them. If it is wrong it is wrong by a factor, not a decade.

`sim/debris.py --selftest` gates the ceiling with a negative control that
fires (`f_spall = 2.0` → 19.10 kg > 15.38 kg ceiling → refused).

---

## R2-764 — R2-700'S SIZE-DISTRIBUTION HYPOTHESIS IS CONFIRMED FROM THE OTHER END, AND THE FIX IS THE SAME FIX

R2-700 saw glass read as a continuous sheet on ten times fewer shards
(249 vs 2,580) and concluded the variable is the **shard size distribution**,
which neither count nor mass captures. Measured on `sim/out/fracture_wall.npz`:

```
 size band        shards    mass kg    % of glass mass
   0- 10 mm           61       0.15      0.01 %
  10- 15 mm          637       3.01      0.13 %
  15- 25 mm        1,358      15.74      0.70 %
  25- 40 mm          391      10.55      0.47 %
  40- 80 mm          220      20.53      0.91 %
  80-160 mm          268     120.83      5.36 %
 160-400 mm          790   1,690.67     74.96 %
 400+   mm           71     393.85     17.46 %
```

**92.4 % of the mass is in pieces 160 mm and larger; 1.3 % is under 40 mm.**
That much is a *correct* model of laminated glass and should not be "fixed".

The part that is not correct is finer than that. **Inside the crushed zone the
pieces are near-monodisperse**: p10 11.8 mm, p90 28.7 mm — a 2.4x spread over
2,458 shards. A Schuhmann fit to that population gives **b = 3.68** against a
physical 0.8-1.2 for brittle comminution. b = 3.68 is not a statement about
glass; it is the signature of a recursive mosaic that splits until each cell is
under a local target area, which necessarily clusters cells just under the
target. **The generator has no lower tail to extrapolate**, which is why the
debris budget had to come from mass conservation and not from continuing the
model's own fit — an approach I tried first and abandoned when the fit said
0.9 % of the crushed mass lies below 8 mm, which is the algorithm talking.

So the missing variable is **three decades of lower tail**, from the model's
8 mm floor down to the resolution limit, and the debris pass *is* that tail.
**One fix, both defects.**

---

## R2-765 — WHAT WAS BUILT, IN NUMBERS

`sim/debris.py --build` writes `sim/out/breach_debris.npz` (14.5 MB). It does
**not** touch `sim/out/breach_film.npz`, does not re-bake, and does not move one
vertex of the shard field: the fines ride on top of the shipped table.

```
emission sites (bonded cracks, from the plan's own adjacency)   12,756
sites drawn (55 % crush-weighted, 45 % crack-length-weighted)    4,200
puffs emitted                                                   16,753
chips emitted                                                  671,564    1.347 kg
   chip size p05 / p50 / p95                          2.15 / 2.81 / 5.16 mm
chips BUILT after the pixel grade                              260,000    0.884 kg
puffs BUILT                                                     11,246
f-curve keys                                                 ~2,88 M
   against the shards' 5,806,793 -- the fines add ~50 %, not a doubling
tris                                                          4,678,660
   against the breach's existing 278,864
verts                                                         2,859,330
```

**The triangle cost is the real one and it is not small: 4.68 M against the
breach's 278,864, a 17x increase in that collection.** A chip is a convex flake
with 4-7 plan sides, which is `4n - 4` = 12-24 triangles, and 260,000 of them is
what that comes to. The levers, in the order I would pull them, are
`--chips` (the grade budget, linear), `debrismesh.N_PLAN_MAX` (7 -> 5 saves a
third and costs facets, which is what the glint lives on), and `--px-min`.
Not pulled here: the number is reported so the trade is visible rather than
optimised behind the coordinator's back, which is the same discipline
`apply_breach`'s hero-shard count already follows.

**The one puff that flies past the lens.** Exactly **1 puff (14 chips) comes
within 0.10 m of the camera, 3 puffs (110 chips) within 0.30 m, and all of them
at f902-906** — the frames the camera is going through the wall. That is a real
and desirable shot element, not an artefact, and its scarcity is what makes it
one: 19 puffs inside 0.50 m, 125 inside 1.00 m. Worth having measured, because
a field that put hundreds of chips inside the near focus limit would render as
defocus mush and nothing in the mass ledger would have said so.

The 1.347 kg emitted is 65 % of the 2.073 kg budget; the remaining 35 % lies
below the per-site size floor and is **declared, not built** (R2-766).

**Every chip is its own solid.** `debrismesh.chip(seed, d)` is a generator, not
a library: the seed is `hash(puff, index)` and two of the 260,000 flakes share a
shape only if two 64-bit seeds collide. There is no chip asset, no chip
collection, and nothing instanced. The project's red line — *"one tree spammed
100 times"* — is met by construction rather than by assertion, and
`debrismesh.selftest()` carries the positive and negative controls for it.

**A chip is not a small shard**, and that is geometric rather than decorative.
A shard keeps both polished faces of the laminate and is 11.5 mm thick; a chip's
free surfaces are the two *crack* faces, millimetres apart, so it is a platy,
wedge-shaped flake (thickness 0.10-0.28 of its realised plan extent, measured
p50 0.186 / p95 0.289 by the selftest's rotation-invariant control) and every one
of its faces is a fracture surface.

---

## R2-766 — THE GRADE IS STATED IN PIXELS, AND AT RUNG 1 THIS FIELD IS BELOW THE RESOLUTION OF THE FRAMES

Grading uses `sim/out/oner_camera_track.json` — the per-frame camera, position,
lens and facing, which R2-706 confirms is current — and **not** the beat sheet's
coarse polyline that `apply_breach` grades hero shards with. A chip's score is
its plan size over its own distance to the camera *at its own frames*, with the
camera's focal length *at that frame* (beat 3 runs 28.4 mm → 21.0 mm across the
transit). A chip behind the camera scores zero.

```
                                            at 4K        at rung-1 720p
chip on-screen size  p50                    3.24 px          1.08 px
                     p95                    9.02 px          3.01 px
                     max                  265.67 px         88.6  px
```

(the 266 px maximum is one puff passing within ~50 mm of the lens as the camera
goes through the wall; the p50/p95 are the field.)

**SAID PLAINLY, AS THE BRIEF REQUIRED: THIS FIELD CANNOT BE ADJUDICATED AT
RUNG 1.** Half of it is under one pixel at 720p. Anyone who looks at a 720p
ladder frame and reports "the debris looks fine" or "I cannot see it" has
measured the resolution, not the field. This is the same wall R2-710 hit on the
slab un-break (483 mm ≈ 40 px at 720p) and it is the same answer: the question
belongs to a higher rung.

The camera's closest approach to the wound *centre* is **1.022 m at f903**,
giving 2,191 px/m at 4K — so one pixel is 0.457 mm there. The 5th percentile of
built chips' own closest approach is **1.41 m**.

**What the grade drops, and why that is right.** Below ~1.5 mm a chip cannot
read as a *shape* at any point in this beat; it can only read as extinction. So
it is not built, and `debris.powder_report()` weighs what that costs:

```
powder (50 um .. 1.5 mm) from the crush spall     0.272 kg   7.1e8 particles
total extinction cross-section                    6.05 m2
    tau at birth, over the crushed footprint      8.35     opaque, a few frames
    tau after 0.3 s, over the aperture            0.23     a veil
    tau after 1.0 s, over 25 m of apron           0.04     nothing
```

That is R2-546's *"no dust burst at the breach"* quantified: the burst is real,
it is briefly opaque, **and it is optical depth, not geometry** — as particles
it is 7 x 10^8 sub-pixel solids. Building it means a Cycles volume the camera
flies through at f899-908. **That is a render-cost decision for the coordinator
and it is deliberately not taken as a side effect of a geometry pass.** The
numbers to take it with are above.

---

## R2-767 — THE ONE APPROXIMATION, STATED BEFORE ANYBODY FINDS IT

A kilogram of millimetre glass is three quarters of a million flakes; they
cannot each be an animated Blender object. Chips are carried in **puffs**: one
spall site in one size bin, 8-40 chips inside a 50 mm ball, keyed as one rigid
body with its own ballistic-plus-quadratic-drag path and its own spin.

**Binning by size is not a convenience.** Drag on a flake goes as 1/d
(`debris.drag_k`, derived from the Cauchy projected area of a tumbling convex
body), so a 6 mm chip coasts 3.41 m and a 1 mm chip coasts 0.57 m. A puff of
mixed sizes would have to disperse and a rigid one could not. Binned, every chip
in a puff shares its trajectory to within a few per cent.

**The cost, said out loud:** chips inside a puff do not tumble independently.
At this beat's shutter — 0.0032 s of world time at the ramp's 15.4 % — a chip's
own spin is smeared out *within* the frame anyway, and the puff spin supplies the
between-frame change. A field where every chip tumbled on its own would twinkle
slightly more. That trade bought a 23x reduction in animated objects.

**A consequence worth having: fine glass stops.** With k ~ 1/d, the whole field
loses most of its relative velocity within one to three metres. The fines leave
with the shards, stall in the air at the wall, and fall — they do not travel to
the apron with the car. That is what a trailing burst looks like and it is a
prediction of the drag law, not a look that was arranged.

---

## R2-768 — THE MATERIAL IS THE HALF OF THIS THAT DECIDES WHETHER IT READS

`BREACH_Glass` — the material all 3,796 shards carry — is a Principled BSDF with
**roughness 0.02, transmission 1.0** and no texture nodes at all. That is a
polished float face. It is right for the pane and it is wrong for every square
millimetre of a chip, and re-using it for the fines would have produced 260,000
invisible lenses.

`BREACH_Fines` (built by `apply_breach.fines_material`, procedural, no image
texture) instead says:

* **Every face of a chip is a fracture surface.** Past the mirror radius — tens
  of microns at these stress levels — a glass crack goes through mist into
  hackle, rough at 1-20 um. A chip is frosted on all six faces. Roughness is
  driven 0.10-0.42 by two Object-space noises (a 3.8 mm one that varies *within*
  a puff and along a single chip, and a 3.5-scale one so the wound is not
  uniformly gritty).
* **A 0.4 mm flake frosted on both faces does not transmit an image, it
  scatters**, so transmission weight is 0.38-0.70 and *tied to* the roughness by
  one node rather than being an independent knob. This is why broken glass grit
  reads white in sunlight and a window pane does not.
* **A perfectly smooth chip has a delta-function highlight.** At any instant
  three chips in the field would be pointing at the sun and the other 259,997
  would be black. A frosted chip glints over a wide lobe, so the field sparkles
  continuously. The look follows from the physics rather than being arranged on
  top of it.

**STILL OPEN, AND NOT MINE TO CLOSE ON THIS TASK:** the *shards'* thickness band
is a fracture surface too, and it is currently polished at roughness 0.02.
`ledger()` weighs 12.66 kg of kerf on far-field cracks whose correct rendering is
exactly that — a frosted 11.5 mm band, no geometry, no cost. R2-546's
*"no thickness reads, no edge refraction — they look like intersecting quads"*
is that defect, and it is a bigger contributor to the sheet-reading of R2-700
than the fines are. Logged rather than done, because silently re-shading 3,796
shipped shards under a debris task is how a scene stops being comparable to its
own history.

---

## R2-769 — INTEGRATION: OFF BY DEFAULT, AND WHY

`apply_breach.py --debris sim/out/breach_debris.npz` adds a `BREACH_Fines`
collection. **Without the flag the applier is unchanged**, which is deliberate:
every apply this project has run produced 3,845 objects and 278,864 tris, and a
pass that silently multiplied both would make every historical comparison a lie
about a different scene. `stats["fines"]["skipped"]` is what a reader checks.

With the flag: +11,551 objects, +3.1 M tris, +~2.2 M keys. The fines are keyed
LINEAR and are put through the **same** `prove_curves` evaluation gate the
shards and the frame go through — the applier refuses if they are not linear by
evaluation — and they hide before their birth frame on the same discipline as
the R2-098 bay swap, with CONSTANT extrapolation after their last key so the
wound keeps its fallen glass through beats 4, 5 and 6 at no further cost.

Every module carries controls that fire:

```
sim/debrismesh.py --selftest   8 checks   (closed solid; centroid origin; two
                                          seeds are not one chip; the same seed
                                          IS; d^3 scale-freedom; the measured
                                          shape factor; platyness on 400 chips)
sim/debris.py     --selftest  13 checks   (size law vs its closed form; the
                                          b = 3 negative control; drag 1/d; the
                                          no-drag parabola; the closed-form
                                          quadratic-drag solution; landing; the
                                          ledger identity; the ceiling, with a
                                          negative control that fires)
```

`apply_breach.py --selftest` — the east-wall census and its 22 positive and
negative controls, which this block did not write and could have broken — still
**PASSES, 0 failed**, after the `--debris` edit. And `verify_breach.py
--swap-scene` is unaffected by construction: it looks up `GP_b*` and `GS_b*` by
name, so `DB_p*` is invisible to it. The fines add a collection; they do not
enter any existing invariant.

**Two of the fines' own controls caught real bugs in this block, both of which
would have shipped silently:** the position update in `fly()` was second-order and drifted
1.7 mm over 0.4 s (3.7 px at this beat's closest approach), and
`debrismesh.chip` scaled thickness by the *nominal* d rather than the realised
plan extent, producing chips that were not flakes. Two other control failures
were the *control's* fault and are noted in the source where they were fixed.

---

## R2-770 — THE DEMONSTRATION: RESULTS

*Harness and its honest scope: R2-776. Results filled in below as frames land;
the chain is `sim/debris_demo.py` -> `sim/debris_ab.py`, running on CPU because
the farm is down and the local card is in a fault state.*

**Render status at the time of writing.** The fines table and the demo blend
(shards + panes + 11,246 fines puffs, 15,222 objects, 4.96 M tris, 8.68 M keys)
build clean. Rendering is on **6 CPU threads at load average 15** — an
i7-7700K shared with other agents' Blender jobs — so a 4K border crop is
tens of minutes per image and the A/B is two.

**WHAT STILL NEEDS A CARD, and it is worth asking for one:** the frames that
actually settle this are the *film* scene at f870-905 at 4K, with the car, the
showroom and the grade in place. Nothing on this box can render those: the film
blends are 7-8 GB against 11 GB of host RAM. The demo answers "does a 3 mm
frosted flake read as a streak at 2,190 px/m under a 12.47 deg sun and a 180 deg
shutter"; it cannot answer "does the beat look right".

---

## R2-771 — A DEFECT THIS BLOCK CREATED AND CAUGHT: BLENDER LERPS QUATERNION F-CURVES COMPONENT-WISE, AND PAST 2*pi THAT RUNS THE ROTATION BACKWARDS

Logged because it is a trap any future keyed-rotation pass on this project walks
into, and because it would have been invisible in every check that exists.

Blender interpolates the four `rotation_quaternion` F-curves **independently**
and normalises on evaluation. Over a small angle that is indistinguishable from
slerp — measured here at **1.5e-4 rad across a 0.337 rad key gap**. Over a large
one it is not merely inaccurate: past 2*pi of rotation between two keys the
shortest quaternion arc reverses, and the object renders **spinning slowly the
wrong way**.

The first version of `debris.integrate()` put 26 log-spaced keys over a 1.10 s
flight. A puff spinning at 14 rad/s turns 5.6 rad in the last interval; one more
step and the sign flips. Tumble is most of what makes a field of flakes read as
glass rather than as grit, so this would have quietly cost the pass its point,
and **`apply_breach.prove_curves` would still have passed it** — that gate proves
the curves are LINEAR by evaluation, which they were. Linear was the problem.

Fixed three ways: key times are now the union of the translation schedule and a
rotation schedule bounded at 0.30 rad per interval; quaternions are carried into
one hemisphere; and **the spin stops when the puff lands**, which is physically
obvious and also removes the only regime where the bound cannot be met (after
the speed ramp exits, one film frame is 0.0417 world seconds and 14 rad/s turns
0.58 rad in a single frame — finer than which no keying can go).

**Two of the controls written for it were themselves wrong first, and that is
the part worth reading.**

* The lerp-vs-slerp check compared **absolute** angles extracted with
  `atan2(|v|, |w|)`, which folds into `[0, pi]`. A puff that turns 15 rad has
  keys well past that, so it reported a 0.128 rad error that was entirely its
  own wrapping. The quantity that matters is the **relative** rotation between
  two keys, which is always small.
* The negative control fired a 5.6 rad gap and expected a failure. 5.6 rad is
  **fine**; the cliff is at 2*pi. And it extracted an unsigned angle, which
  cannot express a reversal at all. It now uses 7.0 rad and a signed angle, and
  reads **-2.783 rad where the truth is +3.500**.
* A third control ran three test puffs from `z = 0`, so all three landed on
  frame one, never spun, and it passed with "worst gap 0.000 rad over three
  spin rates". **A control that cannot fail is not one.**

Same family as R2-708 ("an instrument validated on a sample is not validated
over a range"), and the same lesson: the control has to be checked against a
known failure before its PASS means anything.

---

## R2-772 — A LAZY `np.load` CLOSED OVER BY AN ACCESSOR IS A DECOMPRESSION PER CALL, AND `sim/resample.py` HAS THE SAME SHAPE

`np.load` on a `.npz` returns a lazy `NpzFile`: every `z["key_frame"]`
subscript decompresses that whole member again. `debris.load()`'s first
revision returned

```python
keys_of=lambda j: (z["key_frame"][off[j]:off[j+1]], ...)
```

which is a full decompression of a 14 MB array **per puff**, three times over,
for 11,551 puffs. Caught by reading rather than by timing, because the failure
mode is "the applier is slow", which on a box at load average 15 is
indistinguishable from the applier being slow.

**`sim/resample.py:read_film` already does it right** — it binds
`kf, kl, kq = z["key_frame"].astype(int), z["key_loc"], z["key_quat"]` as
locals before defining `keys_of`, so the accessor slices materialised arrays.
I wrote a near-copy of that function and dropped the one line that makes it
correct. Checked and corrected on my side only; `resample.py` is untouched and
needs nothing.

---

## R2-773 — OBJECT-SPACE TEXTURE COORDINATES ARE PER-OBJECT, SO A COARSE NOISE ON THEM IS A CONSTANT

Caught by reading, before a render. `BREACH_Fines` wanted two scales of
variation: a fine one that varies *within* a puff and along one chip, and a
coarse one so that some spall sites shed cleaner flakes than others.

The fine one is a Noise on `Texture Coordinate > Object` at scale 260 —
3.8 mm features across a 50 mm puff, which is correct and does what it says.
The coarse one was written the same way at scale 3.5. **That does nothing.**
Object space is per-object: every one of the 11,551 puffs' chips lives inside
the same 50 mm ball about *its own* origin, so a 0.29 m noise samples the same
patch of the same field for all of them and evaluates to very nearly one number.
Eleven thousand objects would have shared one roughness offset and the "not
uniformly gritty" claim would have been false while looking implemented.

Replaced with `Object Info > Random`, which is a genuine per-object draw. Worth
recording because the failure is invisible in a node graph screenshot, invisible
in a single-object test, and looks exactly like working code.

Note the same trap applies to the shards' material if anyone adds per-shard
variation to `BREACH_Glass`: 3,796 objects, same 22 mm scale, same Object space.

---

## R2-774 — WHAT IS **NOT** BUILT, LISTED SO IT IS NOT REDISCOVERED AS AN OVERSIGHT

1. **The powder burst as a volume.** 0.272 kg, sub-1.5 mm, `tau` 8.35 at birth
   falling to 0.04 within a second (R2-766). Real, briefly opaque, and the
   single most visible thing R2-546 asked for. It is optical depth, not
   geometry. Deliberately left to the coordinator with its numbers, because a
   Cycles volume the camera flies through at f899-908 is a render-cost decision
   and not a side effect of a geometry pass.
2. **The shards' frosted thickness band** (R2-768). Bigger contributor to the
   sheet-reading than the fines; zero geometry; not mine to change under this
   task.
3. **Secondary comminution.** A shard that hits the floor, a mullion or the car
   at 15-25 m/s sheds fines a second time. The baked table has those impacts and
   this pass ignores them: every chip in it is born at the crack, at release.
   The fines that should skitter off the apron behind the car are therefore
   missing, and R2-546's *"no secondary debris skittering"* is only half
   answered.
4. **Per-chip tumble.** Chips tumble with their puff (R2-767).
5. **Any interaction with the car.** The fines are ballistic; they do not know
   the car is there, are not deflected by it, and do not ride its wake. At
   0.9 kg over a 26 m2 aperture this is the right approximation and it is still
   an approximation.
6. **The other 35 % of the emitted budget** and everything below the per-site
   size floor: declared in `mass_emitted_frac_of_budget` and in the grade, not
   built.

---

## R2-775 — THE FINES WERE BUILT STANDING STILL WHILE THE GLASS LEFT AT 19 m/s, AND NOTHING IN THE MASS, SIZE OR PIXEL INSTRUMENTATION SAID A WORD

The worst defect in this block, found late, by asking the table a question none
of the three gates asks.

`debris.parent_state()` gives each puff the velocity of the two shards its crack
lies between. Its first revision took that velocity as the slope of the shard's
**first key interval**:

```python
dt = clock.world_t(fk[1]) - clock.world_t(fk[0])
return kl[0], (kl[1] - kl[0]) / dt
```

The resampled table keeps a key at the start of the sim span and then keys the
motion. `GS_b04_00000` has keys at **f845, f859, f860, f861, ...** and its
displacement over **f845 -> f859 is exactly zero**, because it has not released
yet. So that expression returned **0.00 m/s for every shard in the wall.**

Measured consequences, on the built field:

```
                                  first revision   corrected
shard launch speed  p50             (not used)      19.0 m/s
puff initial speed  p05/p50/p95   0.53/0.68/0.86   0.6/8.8/12.9 m/s (max 22.3)
puff total travel   p05/p50/p95   ----/0.45/3.51   1.24/3.00/4.58 m (max 5.63)
puff EASTWARD dx    p05/p50/p95        ~0          0.07/2.38/4.49 m
```

The corrected field is the drag law's own prediction made visible: the fines
leave with the glass at 9-22 m/s, and because `drag_k` goes as 1/d they shed
most of it inside three metres and stall in the air at the wall while the car
goes on. **A burst that leaves with the glass and is left behind by the car** —
which is what car-through-glass footage shows, and it was not arranged.

Every puff launched on the `EJECT_MIN_MS = 0.8` floor alone, 0.53-1.05 m/s
against a shard field doing 20. **A debris field that stays at the wall while
the glass leaves is worse than no debris field**: it reads as dirt on the lens,
which is precisely the pointable-effect failure this whole pass is scaled to
avoid.

**And every instrument in the module passed it.** The mass ledger balances — the
fines weigh what they should. The size law matches its closed form. The pixel
grade reports p50 3.2 px at 4K. Not one of them has an opinion about velocity.
The three gates measure *how much*, *how big* and *how visible*, and the defect
was *how fast*.

Now gated, with the bug itself as the negative control:

```
struck-bay shards launch at 5-40 m/s on the shipped table   PASS  p05 14.2
                                                                  p50 19.0
                                                                  p95 21.3 m/s
NEGATIVE: differencing the FIRST two keys reads ~zero        PASS  p50 0.0000 m/s
```

The general lesson, which is not new on this project but is newly earned:
**a set of gates that all measure the same noun cannot catch a defect in a
different noun.** R2-700 said the same thing about member count versus pose.

---

## R2-776 — THE DEMONSTRATION HARNESS, AND WHAT IT IS HONEST ABOUT

The deliverable asked for rendered frames at a resolution where the fines can
be seen. On 2026-08-07 neither route to a *film* frame exists: both vast.ai
brokers were torn down after the render ladder, and the local card reports
`Unable to determine the device handle for GPU0: 0000:07:00.0`. The film blends
are 7-8 GB against 11 GB of host RAM on a box running at load average 15.

So `sim/debris_demo.py` builds the **breach alone** — shards, panes and fines,
from the same tables, through the same `apply_breach.build()` — under

* the film's sun (`world/build_sky.py`'s `SUN_DIR`, `SUN_ENERGY`, `SUN_COLOR`,
  0.526 deg disc),
* the film's sky generator (`ShaderNodeTexSky`, `MULTIPLE_SCATTERING`, the same
  elevation and rotation — **no HDRI**, the prohibition holds),
* the film's exposure and view transform (AgX, -3.048),
* the film's camera transform, lens and sensor **at a named frame**, read from
  `sim/out/oner_camera_track.json`, and
* the film's 180 deg shutter, with motion blur on.

`sim/debris_ab.py` then renders the **same file twice** at the same frame, seed,
samples and crop, with the `BREACH_Fines` collection excluded in the control,
and reports the changed-pixel fraction at three thresholds. Nothing is rebuilt
between the two, so a difference is the fines and cannot be anything else.

**HONEST from these frames:** a chip's size in pixels; whether a flake reads as
a streak under this beat's blur; the density of the field; the A/B.
**NOT HONEST:** anything about occlusion by the car or the showroom, the fines
against a particular background, or the grade in context. Those need the film
scene and a card.

The crop is a 4K **border** render, so the pixel scale is the delivery format's
and not a downscale of it. That is the whole point: at 720p this field is
1.07 px at p50 (R2-766) and a 720p frame would show a smooth grey wall and prove
nothing.

---

## R2-777 — HOW TO TURN THIS ON, AND WHAT IT COSTS

```bash
# 1. the table (numpy only, ~8 min; writes sim/out/breach_debris.npz,
#    NOT breach_film.npz -- the shipping table is not touched)
.venv/bin/python sim/debris.py --selftest        # 19 controls
.venv/bin/python sim/debris.py --report          # ledger, budget, size law, powder
.venv/bin/python sim/debris.py --build

# 2. land it with the breach, on whatever film scene is current
bash sim/land_breach.sh <raw.npz> <report.json> <film.blend> <out.blend>
#    ...or apply directly, adding --debris to the apply stage:
blender -b <film>.blend -P sim/apply_breach.py -- \
    --out <out>.blend --report sim/out/apply_NEW.json --force \
    --debris sim/out/breach_debris.npz
```

`land_breach.sh` is NOT modified: its apply stage does not pass `--debris`, so
landing a bake today behaves exactly as it did yesterday. Turning the fines on
is a deliberate edit to one line of that script or a direct `apply_breach` call.
That is the same reason the flag defaults off (R2-769).

**Sweeps that need no rebuild of anything upstream:**

| flag | what it moves |
|---|---|
| `--f-spall` | the one judgement in the budget (R2-763). 0.12 shipped. |
| `--chips` | the grade budget. 260,000 shipped; linear in tris and keys. |
| `--px-min` | the visibility floor, in 4K pixels. 1.6 shipped. |
| `--sites` / `--site-cap` | spatial and per-site density of the emission |
| `--seed` | a different field at the same statistics — for the "more than one seed" R2-700 asks any A/B on this beat to use |

---

## R2-778 — THE SHIPPING TABLE IS UNTOUCHED, VERIFIED

```
sim/out/breach_film.npz              ce704629abdfaeb948831f4179080015
sim/out/breach_film_R6_SHIPPED.npz   ce704629abdfaeb948831f4179080015
```

Byte-identical to each other and to the md5 this task was handed. No bake was
run, `sim/tmp/` was not written, `land_breach.sh` was not invoked, and the fines
went to a **new** name, `sim/out/breach_debris.npz`. `sim/resample.py`,
`sim/fracture.py`, `sim/shardmesh.py` and `sim/build_breach_sim.py` are
unmodified; the only edit to an existing file in this block is
`sim/apply_breach.py`, which gains an opt-in `--debris` flag, a
`fines_material()` builder and a `build_debris()` pass, and whose own selftest
still reports **PASS, 0 failed**.

`~/opus5-car-render` was read only, and `docs/DEFECT-LOG-R2.md` was not
edited.

---

## R2-779 — THE f878 / f890 A/B: THE FINES READ, AND THE SAME PAIR CONVICTS THE SHARD MATERIAL

`render/debris/FRAMING_f{878,890}_{A_fines,B_control}.png` — the same demo blend,
same frame, same seed, same samples, `BREACH_Fines` excluded in B.

```
                       f878        f890
changed > 1/255      26.18 %     25.85 %
changed > 4/255       8.94 %      8.84 %
changed > 16/255      2.61 %      2.28 %
mean |delta|         0.00747     0.00708
max  |delta|         0.325       0.291
```

**The fines read, and they read as glass.** A quarter of the frame changes at
the 1/255 level and under 3 % at 16/255: present everywhere, strong almost
nowhere. That is the shape of a number that satisfies "if a viewer can point at
the dirt effect, it is too strong" while not being invisible. By eye, A shows a
pale granular burst at the contact and a fine sparkle through the field; B shows
neither.

**AND THE CONTROL FRAME IS R2-546, PHOTOGRAPHED AGAIN.** With the fines removed,
the shards are *thin bright lines*. No thickness, no body, no edge refraction —
"they look like intersecting quads", exactly as written. This is what convinced
me the frosting is the larger of the two fixes, and it is now evidence rather
than an argument. The coordinator extended scope to it on the strength of this.

**One caution on these two frames.** They are 960 px full-frame, so what is
visible is the field's AGGREGATE, not its chips (p50 3.24 px at 4K is 0.81 px
here). At this size the burst can read a little like a puff of smoke. That is
the sub-pixel population behaving as optical depth, which is correct, but it is
not proof that the field resolves into streaks — only a 4K frame shows that, and
the demo scene has no car, no showroom and no mullions behind it.

---

## R2-780 — I HAD THE POWDER WRONG, IN THE OPTIMISTIC DIRECTION, AND THE CORRECTED ANSWER CHANGES THE DECISION

`powder_report()`'s first revision reported optical depth falling
**8.35 -> 0.23 -> 0.04** over the first second and called it "dense for a few
frames at the contact and a thin veil thereafter". **Both of those numbers were
divided by an assumed volume, and the assumption was that the powder travels
with the car.** It does not.

`drag_k` goes as 1/d — the same law that makes the visible chips stall — so a
0.6 mm flake has a **drag length of 0.34 m**. The powder stops within a third of
a metre of the crack that made it. It never reaches the apron, and it does not
thin by spreading. What removes it is **settling**, and settling is slow:

```
terminal speed   1.5 mm 2.89 m/s   0.5 mm 1.67   0.1 mm 0.75   50 um 0.53 m/s

t_world   0.00  0.05  0.15  0.30  0.60  1.00  1.50  3.00  6.00 s
cloud r   0.05  0.35  0.63  0.83  1.06  1.22  1.36  1.59  1.83 m
tau       7.46  4.30  2.88  2.25  1.78  1.52  1.35  1.12  ~0
```

**Beat 3 is eight seconds of screen time at the ramp's 15.4 %, which is about
1.5 s of world time.** Over that entire span tau never falls below ~1.3. The
extinction is carried by the fine end of the distribution, whose fall time from
3 m is 4-6 seconds of world time — longer than the beat.

**So the powder is not a flash. It is a persistent, optically thick cloud
standing in the aperture, and the camera flies through it at f899-908.**

That makes it a **continuity question before it is a render-cost one.** The
brief requires the wound to persist and to be *framed again in beat 6*; a
τ ≈ 1.5 cloud hanging in the aperture would occlude it, and in a film with no
cuts there is nowhere to put the moment it clears.

**Recommendation: do not build it now**, and note that the reason has changed.
It was "too small to be geometry". It is now "too long-lived to add without
first deciding what it does to beats 4, 5 and 6". Pricing it in seconds per
frame answers the cheaper of the two questions.

I am recording this because the wrong numbers were in a report the coordinator
was asked to decide on, and they were wrong in the direction that made my own
recommendation look cheaper.

---

## R2-781 — THE FRACTURE-FACE MATERIAL: WHICH FACES, DECIDED BY GEOMETRY, NOT BY A MAP

`apply_breach.frost_glass_material()`, reachable two ways —
`apply_breach.py --fracture-faces` on a fresh apply, and
`sim/breach_dress.py --frost` on a blend that is already landed. One
implementation, two entry points, for the reason `shardmesh.py` is shared
between the sim and the render: a second implementation is a second answer.

**The classifier is exact and costs nothing.** `shardmesh.prism` writes a
shard's verts relative to its own origin on the laminate mid-plane, so in
OBJECT space the two ply faces are the only ones whose normal is parallel to
local X. `|N_object.x|` therefore separates them from every fracture face
without an attribute, a UV or a bake:

```
|n.x| ~ 1      float surface     -> roughness 0.02, unchanged
|n.x| ~ 0      crack face        -> hackle, 0.32 + comminution + noise
|n.x| ~ 0.7    the 0.6 mm arris  -> hackle, and rightly: that chamfer MODELS a
                                    chipped edge, the most damaged surface on
                                    the piece
```

`Geometry > Normal` is WORLD space and every shard is tumbling, so it goes
through `Vector Transform` (World -> Object) first. Reading it in world space
would have classified faces by which way the shard happened to be pointing —
a bug that would have looked like flickering roughness and been blamed on
sampling.

**The whitening is driven by the fracture model's own data, not painted on.**
`build()`/`breach_dress` stamp `fx_energy` (the impact field at the shard's
centroid — the same field that set its target area) and `fx_size` (its
equivalent side) as object properties; an `Attribute` node in OBJECT mode reads
them. So the energy that decided how BIG a shard is now decides how OPAQUE it
is, and the two cannot disagree. Transmission floors at 0.82, deliberately
shallow: the crushed shards are numerous but small (32 kg of 2,255), so the
contact region reads milky and the slabs stay clear, which is the picture
laminated glass actually makes.

Zero triangles, zero geometry, and it refuses if fewer than 3,000 shards take
the properties — because a shard that reads `fx_energy = 0` renders clear, and
a silently-clear third of the wall is the failure this would otherwise have.

---

## R2-782 — THE POWDER IS DECLINED ON CONTINUITY, NOT ON COST

Coordinator's ruling, recorded with its reason because the reason is the durable
part. The volume was priced and the price was not what decided it:

> "That is not an expensive effect, it is an effect that destroys the continuity
> the breach exists to establish. The wounded showroom persisting is a shipping
> requirement; a haze sitting in the hole would undo it for a third of the film."

A τ ≈ 1.5 cloud that hangs in the aperture for the whole of beat 3 (R2-780) is
still there in beats 4, 5 and 6, and the brief frames the wound again in beat 6.
In a film with no cuts there is nowhere to put the moment it clears.

**So the powder's status is now: physically real, correctly weighed, and
deliberately not rendered.** If anyone revisits it, the thing to solve first is
not render cost — it is what the cloud does to the wound between f905 and f2978.

---

## R2-783 — `rq exec` LOADS NO SCENE, AND A SCRIPT WRITTEN FOR `blender -b <blend> -P` WOULD HAVE SUCCEEDED AT DRESSING NOTHING

`sim/breach_dress.py` was written to be driven as
`blender -b render/film16_breach.blend -P sim/breach_dress.py`, where Blender
opens the scene and the script edits `bpy.data`. **`rq exec` does not work that
way.** It runs

```
blender -b --factory-startup -P <entry>
```

with **no scene loaded**, and stages the `--scene` blend *beside* the script in
the job directory as `scene.blend`. The script must open it itself.

**The failure this would have produced is the dangerous kind.** The unmodified
script would have run against the factory startup scene — a cube, a camera and
a lamp — found no `BREACH` collection, and... been caught, as it happens, by its
own preflight. But had that preflight not existed it would have added an empty
fines collection to an empty scene, saved **8 GB of nothing**, exited 0, and the
broker would have fetched and verified it by sha256. `--output` exists, the hash
matches, the job reports success.

Same family as an entry deriving its output path from `__file__` and writing
into a directory deleted at release: **a success that lands nowhere is
indistinguishable from a failure that never ran, except that it reports PASS.**

Fixed with `--src`, which is required under exec and optional when driving
Blender directly, and which refuses if the path is absent. The preflight that
would have caught it anyway is left in place — two guards, because the one that
saved it here was written for a different reason and might not have been.

---

## R2-784 — THE 4K RATE IS 196.5 s/frame ON THE FILM, AND `RENDER-LADDER.md` WAS QUOTING A DIFFERENT SCENE

Measured from `vast-render/state2/broker.db`, `frames` table, sequence
`m4k_probe`, scene **`film16_breach.blend`** at 3840x2160 / **512 spp**:

```
f30 151.0   f400 182.6   f760 151.7   f830 158.1   f950 216.0
f1120 230.5  f1500 270.9  f2300 210.5  f2850 197.1
                                   mean (n=9)  196.5 s   end-to-end 219.3 s
```

`RENDER-LADDER.md` carried **510.5 s/frame** at 4K — that is `render3.blend`
at n=2 — and **63.4 s** at 720p, which is `film6.blend`. **Neither is the film.**
The doc's 4K rate is 2.6x too high, so its "$108 / 13.4 days" master budget is
not a figure for `film16_breach`. The coordinator has corrected the doc; this
records where the replacement number came from.

**NO FRAME BETWEEN f860 AND f930 HAS EVER BEEN RENDERED AT 4K.** The nearest are
f830 = 158.1 s and f950 = 216.0 s, **n = 1 each, 37 % apart, straddling the
window** — and neither carries the 11,246 fines objects. That gap is the whole
reason this block probes before committing a range, and it is stated rather than
interpolated across.

**The beat-to-beat variance the ladder's budget assumes does not exist.** At
720p on the completed film pass, f860-930 measures **43.71 s/frame against a
42.3 s film mean — 1.03x**, n=71. The doc assumes 8.5x. Beat 3 is not
special at rung 1, and the transmissive glass this beat is made of does not show
up as a cost there.

Also corrected: **credit is $[redacted]**, from `vastctl status`, not the $[redacted] the
task carried; and the two $150 per-broker caps are blind to each other, so they
authorise $300 against $[redacted] and protect nothing. Credit is the only real limit.

---

## R2-785 — PRE-REGISTERED, BEFORE THE PROBE FRAMES LAND: WHAT THE FINES SHOULD DO TO PER-FRAME COST, AND HOW IT SHOULD MOVE WITH `adaptive_threshold`

Written and staged before any treatment frame exists, because the coordinator's
question — does the fines' cost scale differently at the master's planned
`adaptive_threshold 0.02` than at the current spec's 0.01 — has an answer that is
easy to rationalise after the fact and worth committing to first.

**The mechanism.** Cycles' adaptive sampler stops sampling a pixel once its own
noise estimate falls under the threshold. The fines are 260,000 **rough**
dielectrics: a rough transmissive hit spawns a refraction ray into a wide lobe,
so the radiance estimate for a pixel containing fines has high variance and
converges slowly. Pixels of sky, ground, or an unbroken wall converge fast.

**P1. The fines' added cost is NOT uniform across the frame.** It concentrates
in the pixels they occupy, and those pixels will run at or near the full 512
samples while the rest of the frame terminates early.

**P2. Raising the threshold 0.01 -> 0.02 makes the frame cheaper, but it
discounts the CLEAN pixels far more than the fines pixels.** A pixel already
failing to converge at 0.01 mostly still fails at 0.02.

**P3. Therefore the fines' cost as a FRACTION of the frame goes UP at 0.02, not
down**, even though the absolute added seconds should be roughly unchanged.
Concretely: if the fines add `D` seconds at 0.01 on a `T` second frame, at 0.02
I expect `D` to fall by much less than `T` does.

**P4. The frost costs approximately nothing.** Zero triangles, zero objects, BVH
unchanged; it is a shading-only change, and it makes fracture faces ROUGHER,
which is the direction that costs variance — but it applies to 3,796 shards that
were already transmissive, not to new ones. If the combined delta is large, I
expect attribution to fall on the fines.

**P5. The 0.01 -> 0.02 saving on the CONTROL is 5-15 %.** The broker's own
projection for the two controls is 198 s at 0.01 against 188 s at 0.02, which is
5.1 % — but that 188 s basis is `n = 1` and is a projection, not a measurement,
so this prediction is against the measured pair, not against it.

**Why this matters to the budget and not just to me:** the master's plan assumes
0.02 because at 0.01 it does not fit $72.39. If P3 holds, the fines' share of
the master is larger than a measurement at 0.01 would suggest, and the `--chips`
budget should be set against the 0.02 number rather than the 0.01 one.

Four frames, all at f880, all $0.02 each:

```
        adaptive 0.01              adaptive 0.02
control  b129_ctrl      (queued)    b129_ctrl_at02   (queued)
fines    b129_fines     (pending    b129_fines_at02  (pending
         + frost         the build)  + frost          the build)
```

---

## R2-786 — THE 8 GB ROUND TRIP WAS WRONG UPSTREAM OF THE WALL IT HIT. THE FINES SHIP AS A LIBRARY, LIKE THE CEILING

The first architecture opened `film16_breach.blend` (7.97 GB) on the farm via
`rq exec`, added the fines, and saved an 8 GB result to be fetched and
re-uploaded as a new scene. **It never ran.** The broker refused it:

```
ExecMemoryShort: opening film16_breach.blend (7.97 GB) needs about 43.8 GB free
and the box has 11.7 GB -- the render worker is holding a scene of its own.
Waiting rather than being OOM-killed at `Read blend`, which would spend this
job's whole retry budget in ninety seconds and report it as a failed build.
[worker busy, attempt refunded]
```

**Two things to take from that message before the architecture.**

*The refusal is a fix working.* This is the third instance on this project of a
**resource condition wearing the costume of a verdict about the work**. Without
it, the job would have been OOM-killed at `Read blend`, burned its whole retry
budget in ninety seconds, and been reported as a failed build — a memory
shortage indistinguishable from "the fines are broken". It named itself, waited,
and **refunded the attempt**. Logged as a thing that behaved.

*And the scheduling fact it establishes:* **a big-blend `exec` build and a 4K
render cannot overlap on this box.** The warm worker holds a scene at ~12 GB;
opening a second 8 GB blend wants ~43.8 GB free of 57.8 GB total. They serialise
whether or not anybody planned for it.

**But the right response was not to wait for the box.** 43.8 GB is 5.5x the
blend size against ~50 GB on an idle box with a 20 GB floor underneath it. I knew
it did not fit busy; I did not know it fit idle. **Going around the constraint
beats measuring how close to it you are.**

`world/showroom_ceiling.blend` hit exactly this wall and already solved it: a
post-append tool that opened the 7.9 GB film, edited it and saved it was killed
three times locally for swap exhaustion and could not be moved to the farm
either. That agent stopped and re-architected into a **6.99 MB appendable
library** — 21 objects, 73,996 polys — that three lines in
`tools/build_film_scene.py` bring in beside the existing SHOWROOM / PROPS /
LIGHTS appends. **1,140x smaller than the artefact the round trip existed to
move.** Its conclusion is the one that applies here: *the round trip was wrong
upstream of the farm defect it would have hit.*

`sim/build_fines_lib.py` is that answer for the fines. **It opens no scene.** It
builds into factory startup, so its peak is the fines alone — about 2 GB against
43.8 — and **`ExecMemoryShort` cannot apply to it by construction**. No 8 GB
output, no fetch, no re-upload, no waiting for the render worker to idle. The
only thing that ever opens a film-sized blend is the render itself. The film
build gains a fourth append; a pipeline that already runs three pays nothing for
it.

**The frost does not go in the library and never could.** It is a material edit
to `BREACH_Glass`, a datablock the film already owns — no geometry, nothing to
append. It stays in `apply_breach.py` behind `--fracture-faces`. They were
always two changes and this keeps them two, which is also what makes them
separately revertible.

---

## R2-787 — THE ROUND TRIP IS NOT THE CEILING'S ROUND TRIP, SO IT IS MEASURED AND NOT ASSUMED

`showroom_ceiling.blend` is **21 static objects**. This is **11,246 animated
ones** carrying ~2.84 M keyframes on slotted actions whose transforms *are* the
breach sim's timing. A puff that appends half a frame late is a puff that
appears before the crack that freed it, and a puff that appends visible from
frame 1 is 260,000 chips hanging inside an intact wall through all of beat 1.

Appending is documented to carry actions. **Documented is not measured**, so
`build_fines_lib.py --verify` does the whole trip inside one process: build,
save, `read_factory_settings(use_empty=True)`, append the collection back out of
the file just written *using the same three lines the film build will use*, and
then

* object count and F-curve key count against the source,
* **world position** of 64 sampled puffs at f866/880/900/930/1200/2978,
  evaluated through the depsgraph, diffed against `debris.load()`'s own linear
  reconstruction — the same one `apply_breach` keys and the render shows, not
  the raw keys, because a key is only the truth *on* a key frame and most of
  those are not,
* visibility: hidden strictly before birth, shown at and after, because f2978 is
  also the test that CONSTANT extrapolation survived and the wound keeps its
  fallen glass through beats 4, 5 and 6.

It refuses on any of them. **A library that loses its animation silently is
worse than an 8 GB blend**, because the 8 GB blend fails loudly.

---

## R2-788 — `rq exec` RUNS THE CHILD WITH CWD AT THE JOB DIR AND THE BUNDLE UNDER `bundle/`, SO A RELATIVE INPUT PATH THAT WORKS LOCALLY FAILS THERE — AND BLENDER EXITED 0 ON IT

First library build, `2fa96151f7dd`:

```
FileNotFoundError: [Errno 2] No such file or directory: 'sim/out/breach_debris.npz'
  ... in DB.load(args.debris)
Blender 5.2.0 LTS ... Blender quit
```

The bundle **did** contain the file — `12 file(s) 23.8 MB`, the npz included.
The path was simply relative to the wrong root. `rq exec` runs the child with
its **CWD at the job directory** and unpacks the bundle into `<job>/bundle/`, so
`out/x` resolves and `sim/out/x` does not. I passed
`--arg=--debris --arg=sim/out/breach_debris.npz` because that is what works
locally, where CWD is the repo root.

**And Blender exited 0 on the exception**, exactly as `sim/land_breach.sh` warns
in its own header: *"Blender 5.2 exits 0 on an uncaught exception, so `$?` is
not evidence."*

**What converted that into a failure was `--output`.** The broker had two
declared outputs, found neither, refused the job, and attached the child's
traceback. **A job that declared no outputs would have reported PASS** — the
same shape as R2-783's empty-scene dress, and the second time in this block that
the thing standing between a silent success and a caught failure was a mechanism
aimed at something else.

Fixed by resolving INPUT paths against the bundle root (`__file__`'s parent's
parent) and leaving OUTPUT paths relative to the CWD, since `out/` is the only
directory the broker fetches and everything else is deleted when the child
exits. The resolver tries the path as given first, so local invocation is
unchanged, and it **refuses with the CWD and the bundle root in the message**
rather than letting `np.load` raise — because the traceback I got named the
missing file but not the two directories that would have explained it.

---

## R2-789 — THREE SILENT FAILURES IN ONE BLOCK, ALL CAUGHT BY THE SAME MECHANISM, AND NONE OF THEM BY A TEST

Recorded together because the pattern is the finding, not any one instance.

| # | what would have happened | what caught it |
|---|---|---|
| R2-783 | `breach_dress.py` dresses the **factory startup cube**, saves 8 GB of nothing, exits 0, sha256 verifies | `breach_dress`'s own preflight — **aimed at a different failure** |
| R2-788 | `sim/out/breach_debris.npz` not found; Blender **exits 0**; job reports success with no artefact | `rq exec --output` |
| R2-789 | `sim/out/breach_debris.json` not found *after* the meshes were built; Blender **exits 0** | `rq exec --output` |

**Blender 5.2 exits 0 on an uncaught exception.** `sim/land_breach.sh` says so in
its own header — *"`$?` is not evidence and is not used as any stage's verdict
here"* — and this block hit it three times in forty minutes. In every case the
process returned success and the log contained a traceback nobody would have
read.

**The mechanism that caught two of the three is `--output`: declaring what a job
must produce and refusing when it does not appear.** That is the same shape as
this project's `>> STAGE RESULT:` discipline — judge on an artefact or on
printed text, never on an exit code — and it is worth noting that the broker's
version is *stronger*, because it also verifies the artefact's sha256 and cannot
be satisfied by a job that prints the right thing.

**The third-instance lesson is about the second failure specifically.** It
raised inside `build_debris` *after* all 260,000 chips had been meshed, over a
**3 KB provenance file** that no geometry depends on. A missing report is not a
reason to discard fifteen minutes of correct work, so that dependency is now
soft: absence is recorded in the build report and logged, not raised. The 23 MB
table it actually needs stays hard, and refuses early with the CWD and the
bundle root named — because the traceback I got told me which file was missing
and neither of the two directories that would have explained why.

**And the honest note:** none of these three was caught by a control I wrote.
The block has 27 controls across `debris.py` and `debrismesh.py` and every one of
them tests the physics. The failures were all in *delivery* — where the file is,
which scene is loaded, what the exit code means. **A test suite aimed entirely
at whether the answer is right will not tell you the answer never arrived.**

---

## R2-790 — THE LIBRARY ROUND-TRIPS EXACTLY. 11,246 ANIMATED OBJECTS AND 2,844,012 KEYS SURVIVE AN APPEND, MEASURED

`world/breach_fines.blend`, built by `sim/build_fines_lib.py` on the farm in
**175.7 s** (the same build took ~15 min on the loaded local box), and verified
inside the same process.

```
BUILT      11,246 puffs   260,000 chips   4,679,872 tris   2,859,936 verts
           2,844,012 keys   1.0023 kg
LIBRARY    101.9 MB   -- against the 7.97 GB the round trip existed to move, 78x
CURVES     LINEAR 9,814 / CONSTANT 240 / other 0
           max_linear_eval_err 9.54e-07,  bezier control fires at 3.83e-02

ROUND TRIP  (factory wipe -> append -> measure)
  objects                  11,246   of 11,246          exact
  animated                 11,246                      every one
  keys                  2,844,012   of 2,844,012       exact
  hide curves              22,492   = 11,246 x 2       exact
  worst world-position error   1.70e-06 m  at DB_p05600, f866
  visibility mismatches             0
  frames checked      866, 880, 900, 930, 1200, 2978
  PASS                           True
```

**1.7 micrometres.** At this beat's best pixel scale (2,191 px/m at 4K) that is
**0.0037 px** — float32 round-trip precision, not an animation error, and it
occurs at f866, adjacent to a key boundary, which is where it should if it is
precision.

**f2978 is in the sample on purpose** and it is the one that matters for
continuity: it proves CONSTANT extrapolation survived, so the wound keeps its
fallen glass through beats 4, 5 and 6 without a single extra key. Zero
visibility mismatches across all six frames means no puff appears before the
crack that freed it, and none hangs inside the intact wall through beat 1.

**So the coordinator's condition is met**: the animation survives, the round
trip does not come back on the table, and the 8 GB artefact is deleted rather
than merged.

**How the film consumes it.** `apply_breach.py --fines-lib world/breach_fines.blend`
appends `BREACH_Fines` **inside** the `BREACH` collection during the pass that
already opens the film — no second film-sized open anywhere in the pipeline.
`--debris` remains, and is now only how the library is regenerated. The two
refuse together, because doing both would put two copies of 260,000 chips in the
wound.

```
                      builds the field        appends it
regenerate library    build_fines_lib.py      --
land it on a film     apply_breach --debris   apply_breach --fines-lib
```

---

## HANDOVER — the one open item and the exact command that closes it

Everything in this block is landed and verified except **one picture**, and the
work to get it is two commands. Written here rather than carried in anybody's
head.

**What is open.** *"Do 3 mm frosted flakes resolve into streaks at 2,190 px/m?"*
That is close to scene-independent and does NOT need the film, which is why it
is the question being answered — the in-film cost measurement is deferred to the
next world rebuild, where the append happens anyway (R2-786, and
`docs/NEXT-REBUILD.md`).

**In flight when this was written**, all detached and all landing on disk:

```
48bfdeaa1f11   DONE in 70.8 s -> render/demo_fines_frost.blend (194.1 MB)
               the demo scene: 3,796 shards + 11,246 fines puffs, frosted
               fracture faces, film sun / sky / exposure / camera at f878

6a119c8a3e07   the 4K crop, QUEUED.  `rq render --cam CAM --res 3840 2160
               --samples 512 --dof scene --border 0.05 0.45 0.00 0.35
               --scene demo_fines_frost.blend`
               1,536 x 756 px AT THE 4K PIXEL SCALE, not a downscale.
               NOTE --cam CAM, not ONER: the demo scene builds its own camera
               from the film's track rather than carrying the film's rig.

b129_ctrl      f880 4K from film16_breach.blend, adaptive 0.01   } queued behind
b129_ctrl_at02 f880 4K from film16_breach.blend, adaptive 0.02   } another
                                                                   agent's job
```

**All three are submitted.** What remains is to LOOK at them:

```bash
cd ~/vast-render
VASTRENDER_URL=http://127.0.0.1:8761 ./rq status          # position in queue
ls out2/seq/b129_ctrl/ out2/seq/b129_ctrl_at02/           # the 2x2 controls
python3 -c "import sqlite3;c=sqlite3.connect('file:state2/broker.db?mode=ro',uri=True);\
print([r for r in c.execute(\"select id,state,render_sec,result_path from jobs \
where agent='breach129'\")])"                              # the crop lands here
```

`rq render` takes the scene's own current frame and the blend is saved at
**f878**, so no frame flag is needed and none exists. `--border` is on
`rq render` and NOT on `rq anim`, which is why the crop is a still and the
controls are one-frame anims.

**The crop is a 4K BORDER render, not a downscale.** That is the entire point:
the pixel scale must be the delivery format's. The two 960 px demo frames
already in `render/debris/` show the field's AGGREGATE and cannot answer this —
at 960 px a 3.24 px chip is 0.81 px (R2-779).

**What the answer means, and its caveat, fixed in advance so a good-looking
picture cannot quietly lose it:** the demo scene has **no car, no showroom and
no mullions** behind the glass. It can settle whether a frosted flake carries a
streak at this pixel scale under this sun and this shutter. It cannot settle how
the field reads against the real background, in the real grade, with the car in
shot. That is the rebuild's to answer.

**Expected, from R2-785's pre-registration:** p50 3.24 px per chip with 100-200
px of motion smear, so individual chips should read as faint streaks rather than
as points, and the frosted shards should stop reading as the thin bright lines
the f878 control caught them at (R2-779).
