# Round 2 defect log

Same discipline as round 1: every defect gets an entry, including mine, including
the ones caught before anything shipped. An entry that says "found before it could
do damage" is the point of the gates — it is not padding.

Numbering: `R2-nnn`. Audio defects share the numbering with visual ones, as the
brief requires ("log audio defects in the same defect log").

---

## R2-001 — the brief's explode axis is inverted for this car
**Found:** STEP ZERO inventory, before any animation existed.

The brief specifies exploded offsets with *"fore/aft elements along Y, lateral
outboard"*. Measured from the blend, this car's longitudinal axis is **X**
(`FW_` +2.679, `NOSE_` +2.450, `RW_` −2.350) and **Y is the mirror axis** — every
module's Y centroid is exactly 0.000.

Following the brief literally would have rotated all 15 cluster offsets by 90°,
putting the front wing out through the side wall of a 22 m-wide room.

*Resolution:* the plan adapts to the inventory, per the brief's own instruction.
Mapped as fore/aft → X, lateral → Y, vertical → Z, and recorded in
`round2_inventory.md` §3 so no downstream task re-derives it wrongly.

*Generalises to:* **a spec written before the measurement is a hypothesis.** The
brief was right about intent and wrong about axes; only the blend knows.

---

## R2-002 — D160 redux designed out: full-width parts exploding laterally
**Found:** reviewing the first computed explode offsets, before rendering.

`SP_` (Y extent 1.48 m) and `BB_` (1.51 m) are single meshes spanning **both**
sides of a 2.005 m car — mirrored geometry whose own centroid therefore sits at
Y = 0. The first offset pass picked a lateral direction from that centroid, always
resolved to +1, and pushed the whole two-sided sidepod +1.36 m sideways, i.e.
straight through the monocoque.

This is precisely round-1 defect **D160**, which shipped, and which the user found
by zooming into a delivered 4K frame ("this is overlaping nightmare").

*Resolution:* a **measured** guard, not a name-based one — any cluster whose
lateral extent exceeds 60% of car width is redirected to explode vertically. A
future full-width part cannot reintroduce it, which a hard-coded `if key == "SP"`
would have allowed.

*Generalises to:* **fix the class, not the instance.** Round 1 fixed the sidepod;
the bug was the sign convention.

---

## R2-003 — seven cross-cluster overlaps in the computed exploded layout
**Found:** by running the collision check *before* animating, not after rendering.

Initial layout had 7 overlapping cluster pairs, worst `CI`×`SP` interpenetrating
**398 mm**. Round 1 shipped 19 such pairs and only discovered them from a delivered
frame.

*Resolution:* a solver that separates clusters by extending each **along its own
mechanical direction** — never nudging sideways, because a part shoved off-axis to
win a clearance argument stops reading as a part that came off the car. 26 passes,
**0 residual overlaps**, 120 mm minimum clearance.

Note the clearance term is **added** to the required separation. Round 1's solver
used `raw − clearance` (D164), so it stopped while parts were still lapping and
then reported success.

---

## R2-004 — colinear explode directions inflated the field to 15.11 m
**Found:** checking the solved layout against the room it has to fit in.

`FW` and `NOSE` both explode along +X. Being colinear, the solver could only
separate them by pushing further along the same line, producing a **15.11 m** field
and a 91-pass solve. Parts ended further from the turntable than the camera could
usefully weave, in a room only 30 × 22 m.

*Resolution:* a splay term — each cluster also drifts in the axes it is *not*
exploding along, by where it actually sits on the car. The front wing (low) and the
nose (above it) now separate vertically exactly as they sit, which is more
mechanically honest than the original. Field **15.11 → 9.84 m**, solve **91 → 26
passes**, ceiling clearance 1.88 m.

*Generalises to:* **when a solver has to work hard, suspect the parameterisation,
not the solver.**

---

## R2-005 — `filter_width` removed in Blender 5.x
**Found:** first run of `build_beat1_audit.py`, which died after building all 15
cameras and before saving.

`scene.render.filter_width` → **`filter_size`** in Blender 5.x. Round-1 docs and
several round-1 scripts still say `filter_width`.

*Cost:* one wasted 4-minute blend load. *Resolution:* renamed in both round-2
tools; recorded in the Blender API gotchas memory so it is not rediscovered.

*Worth noting:* the failure was loud and immediate, which is the good kind. The
script printed 15 successful camera lines first, so a careless reading of the log
would have concluded it worked — the absence of the `saved` line was the tell.

---

## R2-006 — engine gear selection always chose 8th; shift code never executed
**Found:** reading the demo's own summary line, not by listening.

`speed_to_rpm_gear` picked the *highest* gear whose rpm stayed under the shift
point. Because the ratio table descends (2.94 → 0.84), eighth always produced the
lowest rpm and so always qualified. Result: the whole 14 s demo ran in 8th at a
maximum of 6,560 rpm with **zero upshifts** — meaning `shift_envelope`, the torque
dip and the ignition crack were all dead code that had never once run.

*Resolution:* select the **lowest** gear that does not over-rev, which is what a
driver does and what maximises revs. Now 1st → 7th across the range with 6 upshifts.

*Generalises to:* **a plausible-looking output can hide an entire dead code path.**
The audio "worked" and the waveform looked fine. The summary line — `gear min 7 max
7 upshifts 0` — is what exposed it, which is why the tool prints it.

---

## R2-007 — final drive too short: 331 km/h in 3rd gear
**Found:** sanity-checking gear/rpm against real F1 figures after fixing R2-006.

With `FINAL_DRIVE = 3.20` the car reached 331 km/h in **3rd**. A modern F1 unit is
in 8th at ~12,500 rpm there.

*Resolution:* solved rather than guessed —
`FD = 12500 / (40.55 × 0.84 × 60) = 6.12`. Verified at both ends: 1st gear now tops
out at ~113 km/h (where an F1 first gear actually runs out) and 331 km/h sits in
7th at 14,031 rpm.

---

## R2-008 — audio: turbo whine dominated as a pure 8 kHz line
**Found:** by generating a spectrogram and looking at it, exactly as the brief
requires ("inspect waveforms/spectrograms like you pixel-peep frames").

At amplitude 0.055 with two pure partials, the compressor whine rendered as the
single brightest feature in the spectrum — a solid laser line at ~8 kHz. Piercing,
and far too tonal for a compressor, which is a *band* of blade noise.

*Resolution:* level 0.055 → 0.020, partials detuned against each other so they beat
rather than sum to a tone, a subharmonic added for body, and a 2.5–9 kHz noise band
mixed in at the blade-passing frequency. Measured band balance afterwards:
exhaust −50.5 dB, mid −59.2 dB, turbo −68.9 dB — a sensible descending balance.

---

## R2-009 — audio: exhaust rasp was flat broadband haze
**Found:** same spectrogram.

A 2-pole 420–5200 Hz band rendered as uniform haze across the entire plot: it read
as white noise laid *over* an engine rather than as the engine's own combustion.

*Resolution:* 6-pole band narrowed to 300–2600 Hz, where exhaust energy actually
lives. The noise now sits **under** the harmonics instead of on top of them.

---

## R2-010 — audio: harmonics were laser-flat at constant rpm
**Found:** same spectrogram.

At constant speed the harmonic stack rendered as perfectly flat horizontal lines.
That is the clearest tell of a synthesised engine — no real crankshaft holds a
frequency that precisely, because every combustion event differs in pressure.

*Resolution:* `combustion_jitter()` — ±0.4% brown-ish rpm noise below 6 Hz. Small
enough to be inaudible as pitch drift, large enough to give the partials the faint
waver a real engine has. Visible in the v2 spectrogram as waviness on every partial.

---

## Sanctioned violations — deliberate, do not "fix"

**Launch wheelspin (Beat 2).** For ~10 frames the wheels rotate faster than road
speed implies. This is the *only* sanctioned violation of the rolling-contact rule
(`rotation = distance / wheel_radius`) and it is in the brief by name. Logged here
so a later reviewer running a rolling-contact check does not "correct" it.

---

## Open / carried forward

- **Broker is not usable for round 2 yet.** Two independent audits found, among
  others: a `frame: null` job inheriting the previous job's frame in the warm
  worker (silent wrong frame); `rq` always overriding camera DOF, which would
  override round 2's *animated* DOF every frame; mirrored assets and sim caches
  never re-hashed, so a re-baked sim silently renders with the old cache; and a
  90-second SSH flap destroying a possibly-rendering GPU. Fixes dispatched.
- **Macro audit not yet run.** `world/beat1_audit.blend` is baked with 15 macro
  cameras and is waiting on the broker.

---

## R2-011 — the macro audit presented the steering wheel FROM BEHIND
**Found:** by rendering the first macro close-up on the 5090 and looking at it —
which is the entire reason the gate exists.

The frame was technically excellent: sharp, correctly exposed, DOF presenting the
subject against soft neighbours, carbon weave resolving as actual weave at 4K. And
it showed the **back** of the steering wheel — the column stub, the quick-release
and the rear carbon shell — while the face, carrying the display, the LED strip
and every button, pointed away from the lens. `SW` is 65 parts and the densest
cluster in the car; essentially all of its interest is on one side.

*Cause:* `camera_station()` placed the lens on a generic azimuth spiral,
`i/n * 2pi * 1.35 + 0.6`. That distributes stations evenly through the exploded
field, which is what it was written for, and it has no idea which side of a part
is worth looking at.

**Two wrong fixes before the right one — both worth recording.**

*Wrong fix 1: area-weighted mean face normal.* Sounds principled. It is
mathematically guaranteed to fail here: **the area-weighted normal of any closed
watertight mesh is exactly zero** by the divergence theorem. All 15 clusters are
solids, so all 15 dutifully reported confidence < 0.02 and "symmetric". The metric
was not measuring the parts at all — it was measuring the fact that they are
closed. Had the numbers been less uniform it would have been easy to accept.

*Right fix: measure legibility instead of orientation.* The useful question is not
"which way does it face" but "from which direction do I see the most of it".
`tools/presentation_normals.py` samples 192 directions on a filtered sphere and
scores each by

    projected_area(d) = sum over faces of max(0, dot(normal, d)) * area

weighted by how many distinct **materials** exceed 2% of that projected area from
that direction. Projected area alone cannot separate a steering wheel's front from
its back — both project the same disc — but material richness can: the front shows
a display, an LED strip, buttons, grips and carbon; the back shows one shell.

Measured result for `SW`: **[-0.879, 0.110, 0.464] with 6 distinct materials** —
behind and above, i.e. the driver's viewpoint. The old spiral had the lens at +X,
in front of the wheel, looking at its back.

Directions below the floor are rejected (the camera cannot fly under the dais),
and each cluster reports its margin over the runner-up so a genuinely ambiguous
part is visible as ambiguous rather than silently decided.

*Cost of the fix to the flight plan:* path 52.71 -> 51.32 m, mean camera speed
2.00 -> 1.94 m/s. Slightly better, and every cluster is still presented before it
seats.

*Generalises to:* **when a measurement returns the same answer for everything,
suspect the measurement.** Fifteen different assemblies did not all happen to be
symmetric; the metric was blind by construction.

---

## R2-012 — a verification that could never fail
**Found:** re-reading my own Beat-1 animation script.

The seat check computed `(ob.matrix_world.translation - ob.matrix_world.translation).length > 1e9`
— a value minus itself, compared against a number nothing reaches. It printed a
reassuring `0 stragglers` while proving precisely nothing.

Both independent audits of this project's render broker had, that same night,
flagged "verification theatre" as a bug class in its own right — checks that pass
on stale, truncated or absent artefacts. I then wrote one.

*Fix:* capture every part's seated transform BEFORE any keyframe is written, and
compare the last frame against that ground truth. Now reports worst deviation in
millimetres over all 616 parts (currently 0.0000 mm) and emits
`BEAT1_ANIM_STRAGGLERS` if any part fails to seat.

*Generalises to:* **a check that cannot fail is worse than no check**, because it
converts an unknown into false confidence.

---

## R2-013 — the audit blend could not deploy: my missing HDRI, my 19 cameras
**Found:** first 5090 deploy of the audit blend failed with
`FleetUnavailable: deploy failed on freshly rented instance (0/3 rounds)`.

Looking at the broker log rather than escalating showed both causes were mine:

    WARNING Image file /home/zany/opus5-car-render/assets/city.exr does not exist.
    ERROR   Failed to load 1 image files
    [worker] prewarm: 19 cameras [...]
    worker not ready after 62s and 20 pings

1. The blend inherited round 1's world, which references `city.exr` by absolute
   path in a tree the farm does not mirror — so Cycles would have rendered with no
   environment light, the exact "looks plausible and is wrong" failure round 1
   logged. And `city.exr` is a **downloaded photographic HDRI**, which the round-2
   brief forbids outright. Replaced with a procedural Sky Texture at the circuit
   spec's sun angle: brief-compliant, travels with the blend, and means the audit
   judges materials under the light they will actually ship in.
2. 15 macro cameras plus round 1's 4 hero cameras = 19, and the worker prewarms
   every camera at load (~4 s each), which exceeded the readiness probe. Round 1's
   cameras are useless here and were removed.

*Worth noting:* the standing instruction is that broker problems go to a subagent.
This looked like one and was not. Reading the log first cost two minutes and saved
a subagent chasing a bug that lived in my own blend.

---

## R2-014 — macro audit, SW: display glass reads as a hard-edged CG highlight
**Found:** 1:1 pixel-peep of `macro_SW_v2.png` at the beat sheet's real camera
distance (1.39 m focus, 58 mm, f/2.2).

The LCD cover glass carries a single hard diagonal white streak. It is a specular
highlight on a perfectly flat surface with uniform roughness, so it terminates with
a knife edge instead of falling off. Real cover glass is very slightly non-planar
and has microscopically varying roughness, which breaks a highlight into a soft,
uneven smear.

*Status:* **CLOSED** by `tools/imperfections.py` (recipe class `glass`), verified
against `render/macro/after/p6_SW.png` at the identical camera, 3840x2160 / 512.
Before/after 1:1 strip: `render/macro/ab/p6_SW_display_glass.png`; 2x on the
streak: `work/p3_glass_2x.png`, `work/p4_glass_lower_2x.png`.

Two independent causes, so two fixes:

1. **The surface is perfectly planar.** A gentle ~18 mm-wavelength waviness is
   bumped into `Normal` at ~0.37 deg of tilt. That is enough to make the
   termination of a reflected window edge wander instead of being a straight
   line, and far too little to disturb the readout 2 mm behind the glass — a
   1.5 IOR surface bends the transmitted ray by ~0.5x the tilt, which over that
   gap is ~2 um of displacement.
2. **Roughness is uniform**, so the highlight ends exactly where the geometry
   does. Roughness now carries a +0.010 constant lift off 0.045, a +/-0.013
   break-up at ~2.6 mm, and a faint finger-smudge term gated on AO openness.
   Most of the softening comes from here: roughness spreads a highlight smoothly
   and, unlike a normal, cannot distort what is behind the glass at all.

*Two wrong magnitudes before the right one, and the arithmetic is the lesson.*
Pass 1 sized the bump from "amplitude over half a wavelength" and rendered the
cover glass as crumpled cellophane. A Bump node's tilt comes from the height
field's DERIVATIVE, and an fBm noise's derivative is dominated by its FINEST
octave: at Detail 5 / Roughness 0.55 the octave gradients go as (0.55*2)^i, so
the real slope is ~3.5x what the base wavelength predicts. Worse, the height was
0.7 waviness + 0.3 micro at one shared Distance, and micro's wavelength is 7x
shorter — so the seasoning term contributed ~7x the slope of the thing it was
seasoning. Intended 1.3 deg, delivered ~9 deg.

*Generalises to:* **a bump's strength is set by its gradient, not its
amplitude.** Any time two frequencies share one Distance, the high one wins.

---

## R2-015 — macro audit: no imperfection layer anywhere on the car
**Found:** same peep.

Every surface is pristine. The brief explicitly requires, for parts presented this
close:

    "imperfection layers (subtle dust, fingerprint-level surface variation on paint)"

A steering wheel is the one component a driver physically grips, and at 1.39 m on a
58 mm lens the absence of any fingerprint, skin oil, dust in the button recesses or
wear on the grip edges is a tell. The geometry and the weave are excellent, which
paradoxically makes the pristineness more obvious — everything else says "real
object", the cleanliness says "render".

*Status:* **CLOSED** by `tools/imperfections.py` — one shared node group
(`R2_Imperfection`) instanced into 13 of the car's 14 materials, 674 mesh slots,
driven entirely by geometry. Six tuning passes on the 5090, three clusters
(SW / MB / CORNER_FL) plus FW as an untuned regression check.

**Drivers** (all procedural, nothing downloaded): Geometry>Pointiness convex ->
edge wear; AO at 20 mm + Pointiness concave -> dust in recesses; world normal.z
-> dust settles on upward faces; ~2.6 mm noise -> micro variation; ~7 cm noise ->
patchiness, which multiplies everything else so no term is ever uniform;
anisotropic Voronoi edge network -> handling scratches.

**Not one layer at one strength.** Grip takes skin oil (roughness DOWN, sheen UP);
paint takes a long-wavelength clearcoat orange peel; gloss carbon takes dust and
coat micro-scratches; machined metal burnishes SMOOTHER on its edges rather than
rougher; anodising rubs through to bare aluminium; rubber takes a patch-driven
dulling bloom; cover glass takes R2-014's treatment.

**Three calibration findings worth keeping:**

1. *Pointiness is not comparable between parts.* Measured medians: SW 0.533,
   MB 0.503, CORNER_FL 0.503 — the steering wheel reads convex everywhere because
   it is 65 small parts, so a threshold tight enough to find edges on the
   monocoque paints the whole wheel. The ramp is deliberately wide and
   smoothstepped: SW's raised baseline becomes a faint general burnish (which is
   defensible — it is the most handled object on the car) while genuine edges,
   the 99th percentile everywhere, still reach 0.5+.
2. *The first calibration was measured through the grade.* The mask render went
   through `ShowroomComp` (a Glare node) and included the black showroom shell in
   its percentiles. Both errors say "the mask is everywhere", both are invisible
   unless you check. `render_local.py --standard --alpha --nocomp --isolate` and
   `tools/mask_stats.py` exist so that cannot recur.
3. *A clearcoat's roughness must be modulated in proportion, not by addition.*
   LiveryPaint's Coat Roughness is 0.022, so an absolute +/-0.006 was a +/-27%
   swing and rendered at grazing angles as crazed, flaking lacquer. The identical
   number on carbon's 0.16 coat was +/-4% and invisible. One constant could not
   serve both; the modulation is now a fraction of each material's own value.

**Cost:** 65.5 s mean per 3840x2160 / 512 frame on the 5090 with the layer, against
57.7-61.0 s without. +9%. The AO node's own `samples` is 2, not the default 16 —
at 512 path samples the integrator averages it 512 times over anyway, and 8 rays
multiplied the whole layer's cost for no converged gain (it also stretched the
farm's per-camera prewarm from 4.3 s to 20.6 s, which is why `--keep-cams` exists).

*Left alone on purpose:* `DisplayEmit` (dirt belongs on the glass in front of an
emitter, not on the light source), and everything in SHOWROOM / PROPS / LIGHTS —
this defect is about the car.

*Note on the audit itself:* this is the class of finding the gate exists for. It is
invisible in a wide shot and unmissable at the distance the camera actually flies.

---

## Macro audit — SW cluster verdict

| criterion | result |
|---|---|
| carbon weave resolves as weave (no blur, no tiling) | **PASS** |
| decals/markings crisp at pixel level | **PASS** — dot-matrix and 7-segment legible |
| metallic + rubber at grazing angles | **PASS** — anodised buttons, machined bezels hold |
| edge bevels present, no razor CG edges | **PASS** |
| DOF presenting subject against soft neighbours | **PASS** (crop 4 soft by design, 17.5 vs 36-42) |
| imperfection layer | **FAIL** — R2-015 → **PASS** after `imperfections.py` p6 |
| display glass highlight | **FAIL** — R2-014 → **PASS** after `imperfections.py` p6 |

Render cost: **57.7 s** for 3840x2160 @ 512 samples on the 5090, 16-bit.
That is the first real per-frame measurement for a round-2 scene and supersedes
the middleware agent's extrapolation for budgeting purposes.

---

## Macro audit — imperfection layer, tuning record

Every row is a 3840x2160 / 512 render on the 5090 from the same cameras as the
"before" frames, pixel-peeped at 1:1 (and 2:1 on the glass, the grip and the
anodised buttons). `dMean` / `px>2%` are over the fixed crops in
`tools/ab_crops.py`; the crops never move between passes, because a moving crop
makes "it looks better now" unfalsifiable.

| pass | what changed | verdict from the peep |
|---|---|---|
| p1 | first calibrated guess | **far too strong everywhere.** Carbon twill turned to sandpaper, anodised buttons crackled, paint clearcoat went mirror -> sandblasted, titanium read as corroded castings, cover glass as crumpled cellophane |
| p2 | bump-noise Detail 5 -> 1.5; all bump distances cut 3-8x; dust/wear/scratch roughly halved; AO samples 8 -> 2 | carbon weave recovered, buttons no longer crackle. Paint and glass still clearly over-treated |
| p3 | micro/scratch amplitudes down again; `wear_anod` 0.10 -> 0.04; paint given its own 7 mm orange-peel field; glass bump 2.7x down + constant roughness lift | **SW and CORNER_FL land.** Paint still crazes at grazing angles |
| p4 | clearcoat roughness modulation made proportional; paint scratch 0.40 -> 0.12 | crazing reduced, not gone — grazing-angle coat reflection is near a step function of the normal, so amplitude barely matters until it is very small |
| p5 | paint orange peel cut 6x to ~0.12 deg; `LiveryPaint` micro 0.75 -> 0.45 | **paint lands.** Reflection boundaries read as "not a perfect mirror" rather than as damaged lacquer |
| p6 | rubber dulling moved from the cavity term to the broad patch term | **tyre lands** (a slick is convex and unoccluded, so a cavity-driven layer did literally nothing to it). FW rendered as an untuned regression cluster: max dMean +0.0009, px>2% <= 1.4% — no overfit |

Final magnitudes at full-frame scale: the before and after of `MACRO_SW` are
indistinguishable side by side except for the display highlight
(`work/p6_SW_full_ab.png`). At 1:1 and 2:1 every surface has variation. That is
the intended result — felt, not seen.

**Still open / handed on:**

- The layer is proved on the audit blend. It has **not** yet been injected into
  `world/beat1_anim.blend` or into the unified world; whoever owns those should
  re-run `tools/imperfections.py` against them (it is idempotent and `--strip`
  restores exactly, verified byte-for-byte across all 51 materials).
- Dust on `MB` and the corners is very light by construction: at a 20 mm AO
  distance a big convex monocoque has almost no occlusion (p95 = 0.070 vs SW's
  0.52), so only genuine panel gaps collect anything. If a later frame wants
  visible dust on large bodywork it needs a second, longer AO scale gated high,
  not a lower `cavity_start` — that greys out whole panels.
- AO uses `only_local = False`, so parts that mate collect dust in the gap
  between them. Cluster clearance in the exploded field is >= 120 mm against a
  20 mm ray, so no cluster can dirty its neighbour, but during Beat 1's flight a
  contact crevice will gain its dust over the last ~20 mm of travel. Believed
  invisible at these magnitudes; worth a look in the assembled animation.
- Unrelated observation from these renders, not a material defect: the `FD` and
  `FW` clusters sit BELOW the showroom floor plane in the exploded field
  (`MACRO_FW` centre Z = -0.298 with radius 1.07). Flagged for whoever owns the
  explode plan.

---

## Placement policy — three keep-out volumes, gated automatically

Added after the user raised it directly:

> "you need to make sure theres no building no fences etc ont he road every thing
>  to be perfectionasistly placed onto the map etc."

This is about to matter enormously: the world is being rebuilt one agent per
object — hundreds of items placed in parallel by agents who cannot see each
other's work. "Is anything on the road?" must be answerable by a command, not by
rendering a frame and hoping someone notices.

It is not hypothetical. The adversarial review already found 59% of dressing
objects buried (worst 7.38 m under), the Beat-4 corridor built twice 0.5 m apart,
and terrain sitting on top of the racing surface over 5.3% of its area.

`tools/placement_gate.py` enforces **three** volumes, because the road alone is
not enough:

| volume | what it protects | clearance |
|---|---|---|
| **road corridor** | centreline ± half_width, up to 4.5 m headroom | +0.50 m |
| **the car's driven path** | the real swept box from telemetry.csv, every frame of transit AND lap — stricter than the corridor where the racing line runs wide over kerbs, and it leaves the circuit entirely to cross the paddock | +0.60 m |
| **the camera's flight path** | a 1.20 m sphere swept along every camera key | — |

The third is the one that is easy to forget and impossible to recover from. The
camera flies through this world for 124 seconds **without a cut**: if it clips a
grandstand roof or a catch fence there is no cutting around it, and the shot is
dead.

Tested against EVALUATED geometry, because a BEVEL or SOLIDIFY modifier is exactly
what turns "just clear" into "just touching".

Allow-list is deliberately narrow — only things whose job is to be there: the
surface, its markings, kerbs, and the ground the wheels roll on. Everything else
found inside a keep-out volume is reported by name, volume and intrusion depth.

Runs alongside the two gates already built: `collision_gate.py` (BVH
triangle-level, cluster × environment) and `depth_probe.py` (penetration depth,
which distinguishes legitimate contact from interpenetration — an assembled car's
floor and monocoque touch by design, and a gate that condemns that condemns a
correct car).

---

## R2-016 — grass reads as a fuzzy carpet, not blades. Whole frame washed out.
**Found:** the user, at 1:1 on `vast-render/out/aaa5e2ba7dbf.png` (3840x2160).

> "think it half asses on this the grass is blurry etc. we need max detail max
>  models detail on everything for fnal video"

He is right. Inspecting a 700x394 1:1 crop, six distinct problems, and "blurry"
is the symptom of the first:

1. **No individual blades.** At 1:1 from 4K a grass field should resolve as
   discrete blades — visible edges, tips, curvature, and the dark gaps BETWEEN
   them, which is where most of the read comes from. This is a soft continuous
   mat. Either the blades are sub-pixel, the instance density is far too low and
   a noise texture is doing the work, or blade geometry does not exist at all.
   A grass "material" on a flat plane can never look like grass at this distance;
   it needs geometry.
2. **The whole frame is washed out** — low contrast, heavy haze over everything
   including the near ground. Near-field haze is wrong by definition: aerial
   perspective is a function of DISTANCE, and this is a few metres away. Suspects
   are volumetric density set globally rather than by depth, or the known terrain
   lighting mismatch (terrain calibrated to 3.0:1 direct:diffuse, sun 120 W/m2,
   aerosol 1.45, ozone 1.8; sky ships 115.754 W/m2, aerosol 0.45, ozone 1.30).
   The manifest names this mismatch as the cause of the pink/green blotching seen
   earlier, and it is the prime suspect here too.
3. **White speckles everywhere** — either fireflies (sampling), or tiny
   mis-scaled instanced objects. Either way they read as dirt on the lens.
4. **Bare ground is a flat sandy plane.** No stones, no clods, no tyre-carried
   debris, no depth. It is a colour, not a surface.
5. **The barrier is a smooth tube** with a smeared decal. No bolts, no posts, no
   scuffs, no paint transfer.
6. **Tree shadows are mushy** — soft blobs rather than the sharp, complex,
   dappled shadow a real canopy throws. That is a statement about the trees, not
   the shadows: a canopy without leaf geometry cannot cast a leaf shadow.

**The standing requirement this sets, in his words: "max detail max models detail
on everything for final video."** Recorded here and carried into the per-item
campaign brief. Specifically:

  * `grass_clump_fescue` and every vegetation item are GEOMETRY items, not
    material items. Blades must exist as meshes at the distances the manifest
    records (the doppler hover is 2.4 m above grass).
  * A material with no geometry behind it is a placeholder, at any resolution.
  * Near-field atmospheric haze must be driven by real depth, not applied flat.
  * The terrain/sky lighting mismatch must be closed before any material is
    calibrated, or every material after it is calibrated against a fiction.

*Note on timing:* the user explicitly said to let the running workflow finish
rather than interrupt it. This is a mental-note defect, logged now so it cannot
be lost, actioned in the item campaign.

---

## R2-017 — the placement gate ranked the most-correct object first

**Found by:** me, triaging my own gate's output rather than trusting it.
**Severity:** the gate was actively misleading, which is worse than absent.

The gate reported **37 placement violations**, ranked by triangle-pair count:

    road_corridor  ARCH_PitWall           15165 tri pairs   <- ranked #1
    road_corridor  BR_Stones_apex_L_242    3238
    road_corridor  BR_FenceMesh_L03        2252
    ...
    road_corridor  BR_FenceStruct_L03      1177             <- ranked #7

Measuring actual lateral intrusion (`tools/placement_depth.py`) inverted it:

| object | tri-pair rank | true intrusion | half-width there | verdict |
|---|---|---|---|---|
| `ARCH_PitWall` | **#1** | **−3.279 m** | 8.00 | correctly placed |
| `BR_FenceStruct_L03` | #7 | **+7.106 m** | 7.39 | **spans the racing surface** |
| `BR_FenceMesh_L03` | #3 | **+7.105 m** | 7.39 | **spans the racing surface** |
| `BR_FenceStruct_L04` | #12 | +0.188 m | 7.27 | clips the surface |
| `BR_FenceMesh_L04` | #15 | +0.093 m | 7.27 | clips the surface |

**37 flagged → 4 real defects, 13 edge-family, 15 pure artefacts.**

At s=926 the half-width is 7.39 m and the L03 fence reaches 7.106 m inboard: it
crosses from one edge nearly to the other. A car meets it at racing speed. It was
ranked *seventh*, below a pit wall that is exactly where a pit wall belongs.

### Two independent causes, both mine

1. **`tri_pairs` is not a distance.** It answers "do these meshes touch" and
   nothing else. A dense mesh grazing the margin outranks a sparse one blocking
   the road. Ranking by it puts the most-correct object at the top of the defect
   list.

2. **The corridor was built from AXIS-ALIGNED boxes** while the track curves. A
   box of half-width 8.0 m reaches 8.0·√2 = 11.31 m corner-to-corner — a 3.31 m
   diagonal skirt sweeping the outside of every corner. Predicted false-positive
   range ≤3.31 m; observed −2.41 to −3.86 m. That single geometric error
   manufactured the pit wall, every gravel trap, the barrier sub-base and all
   13 kerbs as "on the road".

### Fix

`placement_gate.py` no longer approximates the corridor with polygons at all. The
corridor *is* an analytic shape — nearest centreline station, lateral offset,
height band — so it is tested directly:

    intrusion = half_width(s) + margin − |lateral offset|

Exact; no diagonal skirt; cannot miss an object floating in the interior the way
a hollow swept prism can; and it reports **metres**, so a finding reads "move this
1.4 m outboard" instead of "these meshes touch, good luck". Findings are ranked by
depth, so the worst physical error is the first line read. Cost is held down by
rejecting on the evaluated bounding box before any per-vertex scan.

Edge-defining families (`DR_Kerb`, `BR_Subbase`, `ARCH_PitWall`, …) are **not**
blanket-allowed — blanket-allowing is how a gate quietly stops protecting you.
They are held to the *true* half-width instead of the courtesy margin: an edge
object may sit at or outside the surface boundary, never inside it.

### The lesson, which is now four for four

Round 1 shipped 19 overlapping module pairs because the check compared bounding
boxes. R2-011's steering-wheel fix used an area-weighted mean normal, which is
mathematically zero for any closed mesh. R2-012's verification used a test that
could never fail. And now this.

**Four times the broken thing was the verification, not the work.** On this
project a gate earns no more trust than the geometry it inspects — and a bad gate
does not fail loudly, it quietly stops protecting you while still printing a
number. Every gate here now reports a physical quantity in real units, because a
count can be large and meaningless where a distance cannot.

### R2-017 resolution and cross-check

The corrected gate was validated two ways before being trusted.

**1. Against an independently-written measurement.** `placement_depth.py` was
written separately from the rewritten `placement_gate.py`. On the same scene they
agree to the millimetre, with the 0.50 m courtesy margin exactly accounting for
the difference:

| object | depth probe | gate (incl. +0.50 margin) |
|---|---|---|
| `BR_FenceStruct_L03` | 7.106 | 7.606 |
| `BR_FenceMesh_L03`   | 7.105 | 7.605 |
| `BR_FenceStruct_L04` | 0.188 | 0.688 |
| `BR_FenceMesh_L04`   | 0.093 | 0.593 |

Road-corridor findings went 37 → 4, and the 4 are exactly the 4 the probe called
real. Two tools written apart, agreeing to 1 mm, is evidence; one tool printing a
number is not.

**2. Against the possibility that the fix agent acted on the BAD output.** The
barrier agent ran the *old* gate at 00:43 and saw the gravel traps, stones and
sub-base as intrusions. Had it "fixed" them it would have pushed correctly-placed
geometry several metres outboard — and the new gate would still have read clean,
because it only reports INWARD intrusion. Silent damage of exactly the kind a
one-directional check cannot see.

Measured instead of assumed: every trap, stone and sub-base in `br_fix.blend`
sits at −2.41 to −2.50 m, **bit-identical to the values measured before the fix
pass**. Untouched. The agent fixed the L03 fence, deleted a stray default `Cube`
that had been left in the car's path, and correctly left the rest alone.

`br_fix.blend` now returns **1 violation** (`BR_Verge_L`, 1.023 m into the car
path at z −0.139, i.e. *below* the driving plane — under triage as a probable
artefact of the car volume's 0.30 m downward band).

**Note on propagation:** because the fix lives in `tools/placement_gate.py`, every
agent that re-runs the gate picks it up automatically. No agent needs to be told,
and no one has to remember — the same structural principle as `save_clean()`.

---

## R2-018 — two gates reported a PASS while measuring nothing

**Found by:** the world-fix verifier, running the gates on the world-only assembly.
**Severity:** the most dangerous shape this failure takes.

    collision_gate.py  ->  "0 clusters, 0 environment objects"
                       ->  "STAGE RESULT: COLLISION_CLEAN"

    depth_probe.py     ->  0 surfaces found, no CAR collection
                       ->  "STAGE RESULT: DEPTH_PROBE_OK"

Both statements are true and both are worthless. `collision_gate` tests
explode-plan clusters against the SHOWROOM / PROPS / LIGHTS collections; a
world-only assembly has neither, so it tested zero pairs and none of them
intersected. `depth_probe` looks for `Turntable_Deck` / `Platform_Dais` / `Floor`
and a `CAR` collection -- all showroom objects, none present.

Zero of zero passed. The gate printed a green verdict on an empty set, and a
reader scanning the run banks it as evidence the scene is sound.

### Fix

Both now refuse. If the subject is missing they name what they could not find,
say plainly that this is **not** a pass, write `"vacuous": true` into the report,
and exit `COLLISION_VACUOUS` / `DEPTH_PROBE_VACUOUS`.

    >> REFUSING TO REPORT: no clusters (needs --groups explode_plan.json, or a
       CAR collection); no environment objects (needs one of SHOWROOM/PROPS/LIGHTS)
    >> This scene contains nothing this gate can test. That is NOT a pass.

### The rule this settles

That is now **five** times on this project the verification was the broken thing
rather than the work -- round 1's bounding-box collision test, R2-011's mean
normal (zero for any closed mesh), R2-012's assertion that could never fail,
R2-017's triangle-count ranking, and this.

**No gate may emit a pass without naming what it tested.** An empty test set is a
failure to test, not a successful test. Enforced in code now rather than
remembered, the same way `save_clean()` enforces the no-external-assets rule.

### Also fixed in the same pass -- placement_gate car-path category error

The gate reported `BR_Verge_L` **1.023 m inside the car's driven path**. It is
ground, and the car drives on it. The car volume is a test for OBSTACLES, and a
racing car spends the whole lap running over verges, kerbs, runoff and gravel.

`GROUND_FAMILIES` is now exempt **from the car path only** -- still held to its
edge threshold in the road corridor, and exempt from nothing in the camera
volume, because the camera flies and ground in its path is a real collision.

**Assembly2 now reports 2 violations, and the road corridor is completely clean**
-- `ARCH_RetainEdge` 1.198 m and `ARCH_PitWall` 1.067 m into the transit path at
the pit-wall/ribbon merge, which architecture had already declared as a known
open conflict. Independently re-run by me, matching the verifier to the
millimetre.

---

## R2-019 — the item gate accepted the mannequin crowd, and I wrote the hole

**Found by:** the user, looking at a render. Again.
> "the people in stands honeslty fucking shit"

`tools/item_gate.py` had already passed that exact asset:

    spectator_seated  ->  ITEM_ACCEPTED, all four checks pass

### Why it passed

The report said, in its own output:

    "variation_measured_over": "geometry-nodes CHUNKS, not individual instances
                                -- CV below is NOT a per-instance figure and does
                                not prove per-instance variation"
    "per_instance_variation": true

**It stated it could not evaluate the check, then passed it.** That is R2-018 with
a different label, written by me into a tool built *in the same session* as the
rule forbidding it. Writing the rule down is not the same as obeying it.

### The fix, in two rounds -- because the first one was still wrong

**Round 1** measured the instances geometry nodes actually emits, via
`depsgraph.object_instances`, which exposes each realized instance's source
geometry and world matrix. `distinct_sources` is precisely the number that
catches *"one tree spammed 100 times"*: one mesh instanced 7,800 times scores 1
no matter how wildly the transforms are randomised. Required source count scales
with population, `max(8, min(40, sqrt(n)))`, so three variants cannot satisfy a
crowd; the commonest source may hold at most 25 % of the population.

**Round 1 still passed the mannequins.** When the walk found nothing, control
fell through to the chunk statistics -- cv_size 1.24, 188 topologies -- and
passed. The same vacuous pass, one layer down. I only caught it by re-running
the gate against the asset I already knew was bad.

**Round 2:** unproven fails. If the scene declares 7,800 instances, the gate can
see 262 objects, and the realized-instance walk finds nothing, then per-instance
variation was never measured and does not pass. The message says what would make
it measurable rather than leaving the agent stuck.

### The number that should have been there all along

Also now reported, deliberately ungated:

    triangles: 3,040,752 total,  390 / declared instance,  11,606 / object

**390 triangles per person.** That cannot carry a finger, a face, or a fold of
cloth. Every threshold in the gate was distance-relative -- at 14.7 m the 6 px
detail limit permits 29.5 mm features, so a body of 30 mm facets sails through.
No threshold is set on this one: a trash can and a human need different budgets
and inventing a single number for 435 item classes would be another guess
wearing a measurement's clothes. It is put in front of the reader instead.

### Six

Round 1's bounding-box collision test. R2-011's mean normal, zero for any closed
mesh. R2-012's assertion that could not fail. R2-017's triangle-count ranking.
R2-018's two gates passing on an empty set. Now this.

**The user has found four of the six by looking at a picture.** Every gate on
this project earns less trust than the geometry it inspects, and the only thing
that has reliably worked is running the check against an artefact already known
to be bad and confirming it fails.

---

## Measurement note — the world's real polygon budget, and two self-inflicted detours

Recorded because the number is needed by the LOD work (#28) and because both
mistakes on the way to it were in the INSTRUMENT, not the subject. Again.

    BASE         49,576,534 tris    1,158 mesh datablocks
    EVALUATED     1,214,026,334     28,470 objects, after modifiers
    INSTANCES    11,968,189,220     4,688,475 instances from 310 source meshes
    RENDERED     13,182,215,554     <- what Cycles traces
    reuse factor 24.5x at object level, ~15,000x at instance level

**98.1 % of it is vegetation** (1.19 B of the 1.21 B evaluated layer). Every
barrier, kerb, grandstand, marking and the whole road surface together come to
22.4 M — under 2 %.

**Why 13.2 billion triangles fits in 32 GB of VRAM:** 4.69 M instances resolve to
only 310 distinct source meshes. Cycles stores each source once. Measured VRAM on
the 5090 during renders: 5.5 GB. Any "optimisation" that made instances unique
would turn a scene that renders into one that cannot.

### Detour 1 — I reported the job as OOM-killed. It was running fine.

Two instrument faults stacked:
  * the command was piped through `grep` with no `--line-buffered`, so nothing
    reached the output file until the process exited 758 s later;
  * checking whether it was alive, `ps aux | grep blender | head -5` was topped by
    the UI Blender, its sudo wrapper and three MCP processes — the actual job sat
    below the cutoff.

A truncated listing was read as absence. The job completed normally.

### Detour 2 — the fast substitute answered a different question.

A cheap per-object count (sum each object's shared mesh) gave 1,212,268,294
against a measured 1,214,026,334 — **0.14 % off**, which is precisely what made it
convincing. It was not an approximation of the right number; it was an exact
measurement of the wrong layer, silently missing the 11.97 B that geometry-nodes
instancing adds. A near-perfect match to the wrong quantity is not corroboration.

`tools/poly_census.py` (all three layers, ~13 min) and `tools/poly_by_object.py`
(fast, per-object and per-module) are kept so nobody re-derives this by hand.

---

## Variety census — the "one tree spammed 100 times" rule, measured world-wide

The user's first and most-repeated quality rule:

> "i dont want repeat stuff aka one tree spammed 100 times everything has to be
>  thought out no matter what"

Asserting compliance is worthless; here it is measured on the assembled world,
at both levels where repetition can hide.

**Instance level** (`tools/instance_variety.py`, depsgraph.object_instances):

    family   instances   sources  inst/src  top share   gini
    VEG      4,688,475       310    15,124       2.0%   0.722

Every realized instance in the world is vegetation -- nothing else is instanced
at the depsgraph level at all.

**Object level** (`tools/mesh_reuse.py`, mesh datablock users):

    family   objects  meshes  obj/mesh  top share   gini
    VEG       28,002     379      73.9       1.2%   0.580
    DR           249     249       1.0       0.4%   0.000
    BR           129     129       1.0       0.8%   0.000
    SURF          58      58       1.0       1.7%   0.000
    ARCH          31      31       1.0       3.2%   0.000
    TER            1       1       1.0     100.0%   0.000

### Verdict: the rule holds

**Every non-vegetation object has its own unique mesh.** 467 objects, 467
distinct meshes, gini exactly 0.000 across dressing, barriers, surface and
architecture. Nothing is reused even twice.

**Vegetation's worst concentration is 2.0 %.** The single most-used asset,
`VEG_tree_birch_L2_09`, appears 329 times out of 28,002 objects -- 1.2 %. The
named failure would present as a top share above ~40 %.

The gini of 0.58-0.72 says the distribution is uneven: a minority of species
carry most of the population. That is what real vegetation does. A flat
distribution across 310 sources would be the artificial-looking result, so this
is not a defect and should not be "fixed".

### Correction to an earlier claim in this log

The 24.5x object-level mesh reuse quoted with the polygon census is **entirely
vegetation**. For every other family reuse is exactly 1.0. The whole
memory-efficiency story is 379 vegetation meshes serving 28,002 objects and
4.69 M instances -- which is also why replacing instances with unique per-instance
geometry during LOD work would turn a scene that renders into one that cannot.

---

## R2-020 — the harness rendered 1080p and the gate scored it as 4K. Mine.

**Found by:** the throughput planning agent, reading PNG headers. Confirmed by me.

    11 of 28 wave-1 hero macros are 1920x1080
    17 of 28 are 3840x2160
    tools/item_gate.py:155   RES_X_4K = 3840   <- every px figure derives from this
    workflow script line 107  ./rq render --cam <CAM> --res 1920 1080

The gate never opens the image. It computes `px_per_m` from the manifest's lens and
distance at a 3840 width, reports `p10_edge_px` against that, and passes or fails on
it. The delivered frame was half that wide for 11 items, so **every pixel judgement
on those items was out by exactly 2x** — a feature the gate called 6 px was 3 px in
the frame the reviewer actually looked at.

I wrote that `--res 1920 1080` into the campaign prompt.

### Compounding

This lands on top of R2-017's lesson from the other direction. The scope analysis
separately found that `nearest_camera_m` is measured ABEAM — 90 degrees off travel,
which at 35 mm is 63 degrees outside the frame — so the peeps were framed at a
distance the camera never reaches AND rendered at half the resolution the gate
assumed. `crew_fireproof_overall` was condemned for a 1.6 mm silhouette error at a
distance where it subtends 0.02 px.

Some wave-1 REWORK verdicts are therefore unsafe. The scale-invariant findings
stand — a head with no face, hands that are stumps, six poses across 600 figures,
zero zinc spangle in a 1436 px/m crop — because those are ABSENT FEATURES, not
sub-threshold amplitudes. The amplitude-based findings need re-judging once the
camera exists (#34) and screen presence is measured (#61).

### The fix, and it is the same fix as five other entries

**A gate that judges pixels must open the image.** Asserting the delivered frame's
dimensions against the resolution it scored is one line, and it would have caught
this the first time it ran. Every measurement in this file that went wrong went wrong
because the instrument reported on something other than the artefact: bounding boxes
instead of surfaces, a mean normal that is zero for any closed mesh, an assertion
that could not fail, triangle counts instead of distances, an empty test set reported
as a pass, chunk statistics standing in for instances, and now a resolution the
renderer was never asked for.

Seven for seven. **Measure the artefact, not the intent.**

---

## R2-021 — the relief check is SOUND. My control was the broken thing. Twice.

**Context:** 21 of the item gate's 28 verdicts rest on one check,
`relief_reads_as_lip_and_shade`. Its author flagged the single-point-of-failure
plainly and asked for an empirical positive control. I built one
(`tools/relief_positive_control.py`): a ladder of known relief — flat, 0.5, 2 and
8 mm ribs, 3 mm chamfered bolts, and the same rib pattern PAINTED ON with zero
geometry as a decoy.

### The answer, on a control I verified by eye before measuring

    panel            height      dip
    a_flat_0mm         0.0mm   0.1422
    b_rib_0p5mm        0.5mm   0.3609
    c_rib_2mm          2.0mm   0.6706
    d_rib_8mm          8.0mm   0.6982
    e_bolts_3mm        3.0mm   1.4002
    f_printed_0mm      0.0mm   0.1688     <- PAINT, scores like the flat plate

    8 mm ribs over flat plate      +0.5560   PASS
    printed decoy over flat plate  +0.0266   PASS  (inside the 0.030 margin)
    2 mm ribs over printed decoy   +0.5018   PASS
    monotonic 0 -> 0.5 -> 2 -> 8 mm          PASS
    3 mm chamfered bolts over flat +1.2580   PASS

**Monotonic in feature height** is the strongest available evidence: the
statistic tracks the physical quantity across four known heights, so it is
measuring what it claims to. The decoy is the other half — real contrast, zero
geometry, reads as nothing. **The check discriminates relief from paint.**

**The gate's 21 rejections stand.**

### What I got wrong, and it is worse than the original bug

My first run of this control reported the check "fails every single test",
"inversely monotonic", "scores PAINT as RELIEF", and I wrote that into the
conversation as a finding. Every word of it came from a broken control:

1. **Sun energy 3.2** — every panel rendered at 0.04 luminance, lit by a
   0.35-strength sky alone.
2. **Ribs running ALONG the light** instead of across it, so no rib could cast a
   lip-and-shadow pair and the check correctly measured nothing.
3. **The sun pointing UP.** I wrote `(-d).to_track_quat('Z','Y')`, giving emit
   direction z = +0.2164 — straight at the sky. This is the EXACT bug I had
   disproven for `spectator_seated` *earlier in the same session*, having
   measured that passing the toward-sun vector is the correct form.
4. Then, after fixing the sun, **exposure clipped the decoy to pure white** — its
   stripes clipped out of existence, unmeasurable in the opposite direction.

Four faults, four render rounds, one at a time. And between the first and second
I published a confident conclusion about a working instrument.

### The rule, restated because I broke it myself

**Look at the frame before measuring it.** The measurement cannot tell you its
input was black, or blown out, or lit from underneath. Every one of those faults
was obvious in one glance at the PNG and invisible in the number.

`relief_positive_control.py` now REFUSES TO SAVE if the sun emits upward, and
refuses if the predicted lit-plate radiance falls outside 0.15-0.85 — the
exposure is solved from `L = albedo * E * cos(i) / pi` rather than guessed. Both
failure modes are now unrepresentable rather than remembered, the same structural
fix as `save_clean()`.

That is eight instruments broken on this project, and this one was mine, inside
the tool built specifically to catch broken instruments.

---

## R2-029 — beat 1's camera flies through the assembled car and looks at the glass wall

Found by the AIM GATE added to `anim/build_camera_rig.py` while authoring beats
2-5 (#34), and confirmed by opening the picture.

**The measurement.** Beat 1's declared subject is the exploded parts field: the
nearest of the 15 cluster volumes in `docs/explode_plan.json`, measured to the
edge of its bounding sphere, and moved from its exploded position to its seated
one on the seat frames in `world/beat1_anim_anim.json`. Against that subject:

    median          0.00 deg
    p90             8.85 deg
    worst          48.88 deg at frame 669
    over 25 deg    51 frames of 792

**The picture.** Frame 648, rendered at 1920x1080 / 128 samples on the 5090
(`verify_showroom.blend`, camera ONER): the glass wall's mullion grid, sky
beyond it, dark floor below, and **not one part in frame**. The camera is at
[2.73, 0.89, 1.47] — inside the assembled car's own volume, just above the nose
— looking along (0.843, 0.262, -0.471), i.e. +X toward the breach wall at
x = +15.

**The cause.** Beat 1 has 16 camera keys. The last presentation key (CORNER_FL)
is at t = 24.64 s / frame 591; the next and last key is the push toward the
completed car at t = 31.4 s / frame 754. That is a **6.76 s, 163-frame move with
two keys**, deliberately — `tools/build_beatsheet.py` reserves the last 20 % of
the beat "for the final settle and the push toward the car". The straight line
between those two stations passes through the car, and the quaternion
interpolation between the two orientations is not constrained to stay on the
field.

**Why nothing caught it before.** The same reason beats 2-5 had no camera at
all: the continuity gate measured position jumps and rotation steps. A slow
straight move through a car has neither.

**Not fixed here.** Beat 1's keys are outside the scope of #34 and were left
exactly as they are. What it needs is intermediate keys in frames 591-754 that
route the camera around the assembled car rather than through it, keeping the
lens on the field — three or four should do it. The gate will confirm the fix:
`1_assembly` must come in under its stated 30 deg bound.

**A rejected model, recorded so nobody re-derives it.** The first subject model
tried for beat 1 was "the single cluster the nearest key nominates". It reported
118.95 deg worst and 273 frames off-screen. That model is wrong: beat 1 is a
weave THROUGH the field, and between two presentations the lens is legitimately
on the parts in between. Shipping it would have sent someone to fix a camera
that is working for 741 of its 792 frames. It is still printed by the build, as
a labelled DIAGNOSTIC that does not gate.


## R2-022 — the beat-3 time map integrated to 3.73 s of world time against a declared 1.6

`build_time_map()` eased from 1.0 to a 0.20 floor over the first third of the
beat, held, and eased back over the last third. Mean scale 0.4667 over 8.0 s of
screen time = **3.73 s of world time**. `docs/beat_sheet.json` declares
`speed_ramps[0].world_s = 1.6`.

2.13 s of surplus world time puts the car 2.13 s further round the lap than
every other artefact assumes. Three independent numbers say 1.6 is right and
they agree to about 30 ms — see the derivation in `anim/filmtime.py`, which now
owns the mapping and is imported by both the authoring tool and the rig build.

A mean of exactly 0.20 leaves no room for an ease at a 0.20 floor. The ramp now
solves its floor from the declared durations: 6-frame ease down, hold at
**0.15372**, 15-frame ease back, integrating to 1.6000 s. The floor is inside
the brief's stated 15-25 % band, and `min_world_time_scale` in the beat sheet
has been updated from the impossible 0.20 to the solved value.


## R2-023 — beat 6 was offset by +3.0 s and had no rotation at all

Two defects in four lines of `build_camera_rig.py`.

1. `"t": b6_start + float(k["t"]) + 3.0` put beat 6's 3 s closing hold at film
   124.1-127.1 s — **entirely past the end of a 2,978-frame, 124.1 s film** —
   and put the camera's peel-off 260 m from the car. With the offset removed,
   beat 6's peel-off position [129.84, 2.37, 2.8] is exactly the car's own
   telemetry position at world t = 69.631 lifted 2.8 m, its declared peel speed
   83.1 m/s is the car's 83.05 m/s there, and the hold lands exactly on the
   film's last 3 s.

2. Beat 6's keys carry `world`, `lens_mm` and `speed` and **no `look_at`**, so
   the `if k.get("look_at")` branch never fired for them. The frozen orientation
   the #34 report traced to frame 754 in fact ran to frame 2978. Rotation is now
   derived from a declared subject in `sheet["aim"]["6_ending"]` — the car until
   t = +4.0, the breached facade at [15, 0, 3.1] from t = +6.0 — without moving
   one of beat 6's keys.

Beat 6's 8 keys also span 14 s, one every 48 frames, straddling the hand-off
from beat 5's 2-to-8-frame keys; Blender's AUTO_CLAMPED handles surged the
camera to 125 m/s across the peel-off against its own declared 83.1. Its
declared trajectory ("minimum-energy cubic ... peak |a| 19.9 m/s^2") is
reconstructed as a Hermite whose tangent magnitudes are the per-key declared
speeds — chord/dt agrees with the mean of each pair of declared speeds to better
than 1.5 % on all seven segments — and sampled at 61 intermediate keys. All 8
declared keys are reproduced exactly at their own frames.


## R2-024 — a top-down camera barrel-rolled while the aim gate read 0.00 deg

`Vector.to_track_quat("-Z", "Y")` resolves roll by pulling the camera's +Y
toward world +Z, which is undefined when the view direction IS world -Z. Beat 5
ends 2.0 m directly above the car at 83 m/s. Measured: **36.9 deg of roll per
frame** across two frames, while the aim angle sat at 0.00 deg — the lens never
left the car and the picture spun.

This is the argument for keeping both gates. The aim gate cannot see a roll; the
continuity gate can, and did.

Two cheaper fixes were measured and both were worse than the problem: blending
the roll reference from world +Z toward the direction of travel from |view.z| =
0.70 gave **175 deg in one frame** (the blended vector passes near the view axis
on a camera looking down-and-backward, and the cross product's sign flips), and
narrowing that window to the 26 deg cone gave **90 deg**. The shipped fix is
parallel transport — each key takes the previous key's orientation and applies
the minimal rotation carrying the old view direction onto the new one, which is
continuous by construction and has no cross product whose sign can change — with
a roll correction toward world +Z (or the direction of travel where world +Z is
ill-conditioned) limited to 3 deg per frame of key gap. Worst rotation step over
the whole film is now **19.05 deg/frame** against a 45 deg limit.


## R2-025 — the placement gate swept the camera at its KEYS, not along its path

`tools/placement_gate.py` built its camera keep-out volume from
`sheet["beat1"]["camera_keys"] + sheet["beat6"]["keys"]` — 25 spheres for a
camera that is airborne for 2,978 frames, and named by hand in exactly the way
that lost four beats' worth of camera in the first place.

It now prefers the per-frame path `world/camera_rig_path.json` emitted by the
rig build (2,978 samples) and reads EVERY beat's keys from the sheet, announcing
loudly which of the two it used. It also reports the CLOSEST APPROACH per volume
even when nothing is violated, because "CLEAN with 0.02 m to spare" and "CLEAN
with 8 m to spare" are different answers.

The first per-frame run immediately found five camera-path intrusions the
key-only sweep could not see, all at the T4 hairpin, worst **1.181 m into
`BR_TyreWall_T4`**. The inside of the hairpin at u = +14.0 carries the tyre
wall, `BR_Armco_L03`, its catch fence and `DR_Ad_012`; the first draft of the
kerb-height vantage flew at u = +13. Moved to u = +10.5.


## R2-026 — telemetry: during the launch, `x` and `s_m` disagree by exactly 25 %

Found while deriving the film-time -> world-time map for #34. Not a camera
defect; logged because three other consumers read these columns.

For every row with `s_m` below ~12 m, `x / s_m = 1.25207` to five figures. That
is 15.0 / 11.98 — the ratio of the dais-to-glass distance in world X to the
declared `launch_run_m`. The builder appears to have stretched the launch run
onto the geometry by scaling the position while leaving the arc length,
`speed_ms` and `wheel_rot_rad` on the unscaled run. Past the glass the ratio
decays to 1.0 and `x = s_m + 3.02` for the rest of the film.

Measured over the launch:

    frame 24   s 2.206   x 2.762   dx/dt  6.323 m/s   speed_ms  6.411   ratio 0.99
    frame 42   s 9.481   x 11.871  dx/dt 15.055 m/s   speed_ms 13.295   ratio 1.13

so the car's actual world speed runs up to **13 % above the `speed_ms` column**
by the time it reaches the glass, and `wheel_rot_rad` — computed from `s_m` —
under-rotates the wheels against the distance the body actually covers over the
same span. Beat 2 sanctions wheelspin for ~10 frames and no longer; from
hook-up to the glass the rolling-contact rule applies and this breaks it.

It also feeds the audio: RPM comes from `speed_ms`, so the engine will be a
quarter-tone flat against a car that is visibly travelling faster, for the
1.9 s of the launch.

The camera work in #34 is unaffected: it aims at `x, y, z`, which is where the
car is, and derives nothing from `s_m` except the station lookups used to place
lap vantages (which are past the affected span).


## R2-027 — the exposure ramp was keyed absolute, 3.6 stops over the world's calibration

`build_camera_rig.py` keyed the interior-to-daylight ramp as **-0.85 -> 0.00**.
That is only correct if the scene it is built into happens to be calibrated at
0.00. `render/world/assembly/assembly_render_setup.json` records the assembled
circuit calibrated at **exposure -3.628** under AgX, so the daylight end of the
ramp was 3.6 stops hot for every frame from the glass onward.

Found by looking: the first frame rendered through the rig against the full
world (frame 1150, beat 4, 1920x1080 / 128 samples on the 5090) came back washed
out, mean luminance 0.725 with the p99 at 0.965.

The ramp is now a DELTA. The daylight end is whatever exposure the incoming
scene is already set to; the interior end is that minus `INTERIOR_STOPS = 0.85`,
the brief's ~1 stop. On `beat1_anim.blend` (calibrated at 0.000) the keyed
values are unchanged, so beat 1 and beat 2 are unaffected.


## R2-028 — beat 6's declared peel-off frames a 2.25 x 1.27 m patch of the car

Not fixed, because both numbers involved are beat 6's own declared values and
#34 must not move them. Recorded so whoever owns beat 6 decides deliberately.

Beat 6's first key is `world [129.84, 2.37, 2.8]`, `lens_mm 32.0`. That position
is the car's own telemetry position at world t = 69.631 lifted 2.8 m, i.e. the
camera is directly over the car, 2.0 m above its roof. A 32 mm lens on a 36 mm
sensor at 2.0 m sees a footprint of **2.25 m wide by 1.27 m tall**. The car is
5.698 x 2.005 m. So the shot is a macro of the engine cover, not the car.

Verified by rendering frame 2642 (1920x1080 / 64 samples, `verify_surface.blend`
with the telemetry-driven car proxy): the proxy fills the frame edge to edge
with a sliver of road at either side.

If a top-down of the whole car is the intent, the geometry demands either about
12 mm of lens or roughly 8 m of height. If a macro at 300 km/h before the
crane-out IS the intent, it is correct as declared and this note can be closed.


## R2-030 — the same frame rendered twice is NOT bit-identical, and the seam gate has to know that

Found while closing #34: the broker had two completed renders of frame 1150
against the same scene with byte-identical job specs (1920x1080, 128 samples,
CYCLES, OPENIMAGEDENOISE, `--dof scene`), produced either side of a worker
restart. Their sha256 differ.

Measured, pixel by pixel:

    bit-identical pixels      94.797 %
    max absolute delta        4 / 255
    mean absolute delta       0.0181 / 255
    pixels differing by >1    0.002 %
    pixels differing by >4    0.000 %
    mean luminance            0.716488 vs 0.716487

So the difference is real but it is **LSB dither** — adaptive sampling and OIDN
not landing on the same tile schedule across a session restart. Nothing at this
magnitude can produce a visible pop: 4/255 on two ten-thousandths of the frame
is far under any perceptual threshold, and the frame means agree to six decimal
places.

**Why it is logged anyway.** The brief makes temporal continuity a first-class
defect category and prescribes the test:

    "Render 5 frames of overlap at every batch boundary and diff them; any pop,
     flicker, or shift at a boundary is a defect."

Written as a byte compare — which is the obvious way to write it — that gate
would fail every boundary in the film, immediately, on noise. It has to be
written against a stated PERCEPTUAL threshold instead, and the numbers above are
the calibration: the floor for "same render, different session" on this pipeline
is about **4/255 peak and 0.02/255 mean**. A boundary that exceeds that by an
order of magnitude is a real seam; one that sits at it is the renderer breathing.

Not a camera defect and nothing to fix here. It belongs to whoever builds the
render ladder (MASTER-PLAN step 10) and it is much cheaper to know now than to
discover from a red gate at 4K.

---

## R2-031 — we rented a below-median CPU and concluded remote execution does not scale

**Found by the user**, who pointed out that every 5090 offer ships a different CPU
and there are 100+ configurations available at any time.

`vastctl.build_query()` filtered on GPU model, CUDA version, reliability,
bandwidth cost, port count and disk. **It never asked for CPU at all.** Measured
across 54 live offers:

    min 8.0    median 30.2    max 384.0 effective cores
    the instance we were on: 23.04   (cgroup cpu.max 2304000/100000)

So the fleet drew randomly from an 8-384 pool and landed below the median.

### What it cost

The remote-exec A/B (#60) measured build throughput plateauing near 160 items/h
whether given 12 slots or 20, and concluded *"the remote box does not scale with
slots"* — rejecting remote execution at 1.68x against a 2.0x bar.

**A 23-CPU cgroup asked for 20 concurrent Blender builds is full.** The plateau
was the box. Host `loadavg` was ~52 on top of that, so it was contended as well
as small. The measurement was sound; the population it sampled was not.

What was available at the same time, at or below what we were paying:

    128.0 eff cores   $0.499/hr    5.6x our cores for +$0.15/hr
     64.0             $0.455       free bandwidth
     48.0             $0.435       2.1x cores and CHEAPER than ours
     32.0             $0.308       cheaper than ours, +39 % cores

### Compounding: the advertised number is not the real one

`cpu_cores_effective` said **32.0** for a box whose cgroup allows **23.04** —
optimistic by 39 %. And `nproc` (96) and `MemTotal` (188 GB) report the HOST, not
the container. Inside a cgroup the only honest sources are:

    /sys/fs/cgroup/cpu.max        quota/period = real CPUs
    /sys/fs/cgroup/memory.max     real bytes

I had written "32 effective cores, 515 GB RAM" into `MASTER-PLAN.md` from the
listing fields. Both were wrong; the plan is corrected.

### Fix

`MIN_CPU_CORES_EFFECTIVE = 32.0`, and `cpu_cores_effective>=32.0` in the query.
Verified: 20 offers now pass every filter, cheapest $0.308/hr at 32 cores —
cheaper than the 23-core box it replaces.

### The lesson, which is a new shape

Every previous entry in this log is *the instrument was broken*. This one is
different: **the instrument was fine and the sample was unrepresentative.** The
A/B was careful — it even refuted its own projection by re-running at 20 slots.
It could not detect that the box it ran on was drawn from the bottom of a
14-to-1 distribution nobody had looked at.

**Before trusting a measurement, ask what population the subject was drawn from,
and whether anything is selecting it.** Here nothing was selecting it, which was
precisely the problem.


## R2-036 — `barrier_offset` stepped 51.99 m in one metre. TWO mechanisms, and the report named only one of them.

**Fixed.** `world_contract.py` 1.0.1 → 1.1.0.

This is the defect that put `BR_Armco_L03/L04` and `BR_FenceStruct_L03/L04`
wall-to-wall across the T4 braking zone. `build_barriers` §4b wrote a 200-line
cone-eroded taper to survive it and handed it back in a comment. Nobody had
fixed it.

### It was not one fault

The defect report attributed every step to the pit-straight boolean masks.
Measured on the shipped v1.0.1, on its own 1 m grid, it is **two independent
faults** and only two of the seven steps are the masks:

    s      side   step        mechanism
     904    +1    51.99 m     (a) the maxoff sentinel
     250    -1    46.31 m     (b) the pit-straight masks
    1060    +1    21.40 m     (a)
    3114    -1    15.69 m     (b)
    1743    -1    15.26 m     (a)
    1819    -1     9.38 m     (a)
    2665    +1     8.64 m     (a)

**(a) A MEAN IS NOT A SMOOTHER WHEN ONE OF ITS INPUTS IS A SENTINEL.**
`_Corridor.maxoff` wrote `1e6` for "this station has no geometric cap",
min-filtered it over ±55 m, and then box-filtered it over 41 samples. With one
`1e6` left in the window the mean is `1e6/41 = 24 390`; with none it is `14.0`.
The published `maxoff` at s = 904 was **24 403.902** and at s = 905 was
**14.000**, so `np.minimum(raw, maxoff)` went from *no cap at all* to *14.0 m*
in one sample. The code read as though it had been smoothed. It had not been
smoothed at all.

**(b) A boolean mask assignment is a step by construction.** The pit-straight
overrides wrote `grass[-1][pit] = …`, `asph[-1][pit] = 0.0`, `grav[-1][pit] = 0.0`
on a hard `(s >= 3115) | (s <= 250)` mask, so at s = 250 the T1 runoff zone —
already at full weight, 45 m of asphalt + 12 m of gravel — switched on in one
sample against a pit-wall grass width of 11 m.

### The fix

The sentinel is finite and modest (`MAXOFF_NONE_M` = 200.0, against a maximum
programme offset of 81.95 m); the box filter is deleted; the pit-straight
overrides are `_ramp`-weighted blends over `PIT_OVERRIDE_RAMP_M` = 45 m with the
transition placed **outside** the named section, exactly as the contract already
places the width transition outside its section; and the finished line is
**cone-eroded** at `BARRIER_MAX_LATERAL_RATE` = 1.95 m/m.

Cone erosion, not a filter, because `min_j(c(j) + rate·|s−j|)` is exactly
`rate`-Lipschitz **whatever c does, including if c steps** — a filter of a
stepped field is still a smoothed step, which is how (a) survived 41 samples of
box filter — and because it is never below `min(c)`, which is what
`build_barriers`' first attempt (a box-smoothed *deficit*, subtracted) got wrong
when it produced −18.80 m: a barrier face 18.8 m past the centreline.

    barrier_offset  max |d off / ds|, sampled at 0.25 m over the whole lap
                    side +1        side -1
      v1.0.1        51.9876        46.3060
      v1.1.0         1.9500         1.9500     (= the rate it is eroded at)

Measured downstream, with `build_barriers` imported against v1.1.0 under
Blender: `_STEP_BREAK` — the mask it uses to refuse to lay barrier across a jump
in the declared line — now fires on **0 stations on both sides**. It fired on
five places, 24 m of lap. `barrier_clamp_report()` gives `max_lateral_rate` 1.95
on both sides and `stations_inside_verge` 0.

### The instrument was the thing that was broken, again

`--selftest` had **74 checks and not one of them looked at whether anything was
continuous.** The step was 52 m and the contract printed PASS.

v1.1.0 adds `continuity_report()` — every quantity the contract exposes as a
function of `s`, sampled over the whole lap, against a bound published in
`CONTINUITY_BOUNDS` with its calibration written beside it. It is runnable
against **any** revision through the public API:

    python3 world/world_contract.py --gate-selftest <old world_contract.py>

**Tested against the artefact already known to be bad.** Against the shipped
v1.0.1 it fails **14 of 23 rows**, headed by `barrier_offset (side +1)` at
**51.9876 m/m at s = 904.00** and `ground_z LAP closure` at **6.746e-3 m** — the
two numbers the defect report opened with. It exits non-zero if an old revision
*passes*. Nine instruments on this project have turned out to be the broken
thing; this is the only test that finds that out.

**Sampling step matters more than the bound does**, and that is the part that is
easy to get wrong. A step of *e* mm sampled at *h* metres reads as *e*/1000*h*
m/m, so R2-032's 6.75 mm datum step is **invisible** at h = 0.25 m (0.027 m/m,
under a 0.10 bound) and obvious at h = 0.01 m (0.675 m/m). `ground_z` is
therefore gated at 0.01 m over the whole lap at 17 laterals, plus an exact
closure test. A gate sampled too coarsely to see the defect is R2-018 again.


## R2-032 — THE DATUM did not close on itself. 6.75 mm across the start/finish line.

**Fixed** in `world_contract.py` 1.1.0.

`_undulation` evaluated value noise on **raw `s`**. `s / 46.0` puts **79.891**
noise cells in a 3675 m lap, so lattice cell 0 and lattice cell 79.891 carry
unrelated hashes and the two sides of the start/finish line are two different
draws. Measured: **6.746 mm**, worst at u = −6.5 m, over ±60 m of lateral.

It is inside `TOL_SEAM_M` and it is hidden under the painted S/F line, which is
exactly why it lasted. It is also a **step in the datum**, on the pit straight,
in a film that drives down that straight at 300 km/h, and everything that sits
on the ground sits on it.

The noise now runs on a whole number of cells per lap — 80 / 237 / 766, which
moves the three published wavelengths by −0.136 %, +0.041 % and −0.049 % — and
`_vnoise` wraps its lattice index. `ground_z(0, u) == ground_z(LAP, u)` to
**1.4e-17 m** against a new `TOL_CLOSURE_M` = 1e-6.

**The pattern moves, so every baked mesh must rebuild.** The lattice cell
boundaries drift by up to 0.11 of a cell over the lap, so the undulation shifts
longitudinally by up to ~5 m in places. Measured over 200 000 random points on
the road cross-section: **−8.5 … +9.6 mm, rms 1.5 mm**. That is `TOL_SEAM_M`, so
it is a rebuild, not a tolerance. No module needs a code change — they all
import the datum.


## R2-033 — `access_z` disagreed with `ground_z` by 90.2 mm, and three modules were building to the wrong one

**Fixed** in `world_contract.py` 1.1.0. Root-caused and measured by
`build_surface` (build_surface.md §5.4), which routed around it and handed it
back; this closes it at the source.

v1.0.x `access_z` eased from the flat apron onto `ground_z` with a weight that
was a function of the **route station t alone**, completing at the merge point
t = 154.32. But the ribbon starts **sharing an edge with `SURF_Track` at
t = 95.33**. Along the 149.3 m of shared edge the two answers differ by up to
**80.2 mm**, and by up to **90.2 mm** somewhere on the ribbon — **9×
`TOL_SEAM_M`**, on a boundary two modules share, in the beat the camera flies at
rooftop height.

`build_surface` built the ribbon on `ground_z` and got a 0.000 mm join.
`build_terrain` (line 444), `build_architecture` (5410, 6171) and
`items/access_road_slab` (813, 821, 3591) all read `access_z` and were building
to the other one.

`access_z` **is** `ground_z` now, expressed in route coordinates, kept as a named
function only because nine call sites read it. Nothing is lost: spec §10.3(b)'s
"first 50 m outside the glass exactly 0 % and exactly level with the interior
floor" still holds **exactly** — max |z| = 0.000000 m over the whole 49.60 m
apron run at every lateral — because `ground_z` is already identically `APRON_Z`
there. The contract's own apron tie does it, `apron_zone` being 1.000 along the
whole approach.


## R2-034 — two shared constants lived in two places and agreed by coincidence

**Fixed** in `world_contract.py` 1.1.0.

`APRON_JOINT_LAP_M` (0.050) and `APRON_JOINT_DEPTH_M` (0.005) were read by
**both** `build_surface` (line 136) and `build_architecture` (line 121) as
`float(getattr(C, name, default))`. They agreed only because the two files
carried the same fallback literal — which is not agreement, it is a coincidence
with a version number. Change one fallback and the asphalt lap and the concrete
slab part company silently, over 241 m of pit straight, at a 5 mm sealant invert
nobody would see until it was rendered.

RULE 1 of the contract's own docstring already required them there. They are
there. Both modules keep their `getattr` form, so a builder pinned to a v1.0.x
contract still works; from v1.1.0 the `getattr` finds these.


## R2-035 — THE CIRCUIT STILL CROSSES ITS OWN CORRIDOR, and the contract still does not know

**NOT FIXED.** Measured, named, and left open deliberately: it is a different
problem from R2-036 and it needs a medial-axis solve the contract does not have.

`world_contract.barrier_offset` is `verge_edge + max(runoff, 4) + margin`,
capped only by the inside-of-a-corner radius rule. Nothing in it knows another
**leg of the same track** might be in the way, and on this layout one is: T3's
40 m + 15 m runoff on side +1 puts the declared barrier face 66.9 m out, and S4
and T5 run back past that side 51–67 m away and 5–7 m higher.

Measured against v1.1.0 by sweeping the declared face into world space and
re-projecting it onto the nearest centreline:

    side  declared barrier face inside SOME leg's road corridor   worst intrusion
     +1        406 of 14 700 stations   (2.76 %)                       7.493 m
     -1          0 of 14 700 stations   (0.00 %)                            —

    worst at s = 786.0, whose barrier face lands at |u| = 0.01 m on the leg at
    s = 1182.4 — i.e. ON THAT LEG'S CENTRELINE.

(v1.0.1 was 3.56 % and the same 7.493 m worst; R2-036's taper reduced the count,
not the worst case.)

`road_corridor_mask` resolves this correctly, because it asks `project`, which
returns the nearest centreline — so terrain cuts the union of the two branches.
`barrier_offset` does not.

**Therefore `build_barriers` §4b's ownership clamp is still load-bearing and its
warning still stands**: any module that needs the barrier line through
s ≈ 660–1215 on the left must read `build_barriers.barrier_offset`, **not**
`world_contract.barrier_offset`. §4b now clamps 9.71 % of the left corridor
(was 14.1 %) and is exact against the contract over 90.3 % of the lap.

The fix, when someone takes it: promote `build_barriers.owned_edge` — the medial
axis between two branches plus `CORRIDOR_BIAS` — into the contract, so
`barrier_offset` is capped by ownership as well as by radius, and the divergence
disappears rather than being documented.

---

## R2-037 — beat 3's shutter is right for the car and 6.5x too short for the world

Found by the screen-presence measurement (#61), which needed the real per-frame
shutter to compute motion smear and therefore had to read it rather than assume it.

`anim/build_camera_rig.py:635`

    scene.render.motion_blur_shutter = a.shutter * scales[f - 1]

`motion_blur_shutter` is **one global scene property**. The reasoning behind that
line is sound and is written into the file's own docstring:

> A 180-degree shutter at 24 fps exposes for 1/48 s of WORLD time. If world time
> runs at 15 % and the shutter is left alone, the blur is nearly 7x too long and
> the slow-motion reads as smeared rather than crisp.

That is correct **for the car**, which is moving in slowed world time. It is wrong
for everything the camera flies PAST, because **the camera flies in FILM time at
full speed** — the brief's whole point about beat 3 is that contrast. A single
shutter value cannot serve both.

### What it costs

Static geometry during beat 3 receives **6.5x less blur than the camera's own
motion warrants**, so it renders unnaturally crisp.

Measured consequence for the campaign: **81 of 91 HERO items earn their tier in
beat 3.** At a flat 180-degree shutter the HERO count falls **91 -> 75**. Sixteen
items are currently scoped for hero fidelity on the strength of a shutter setting
that flatters them.

This confirms `PLAN-scope-optimisation.md` section 11.7, which flagged a possible
double-correction in the beat-3 shutter and could not verify it.

### The fix is a choice, not a patch

A global shutter cannot be right for two clocks at once. The options, in the order
a colleague would consider them:

1. **Per-object motion blur / vector pass** — blur the car by world time and the
   world by film time. Correct, and the most work.
2. **Choose the camera's clock** and accept the car smearing more. The camera's
   motion is what the audience reads as speed through a slowed scene.
3. **Compromise value**, stated and justified, with the scoping measurement re-run
   against whatever is chosen.

Whichever is picked, **the HERO tiering must be re-derived against it**, because
the tier boundary is defined in resolvable pixels and resolvable pixels depend on
this number.

### The general lesson

The docstring is a careful, correct argument about one object, applied to a
setting that governs all of them. Nothing about the code looks wrong; the scope
of the reasoning is what is wrong. **When a global setting is justified by an
argument about one subject, check what else that setting governs.**
## R2-054 — the pit wall stood in the Beat-4 transit lane, and THIS FILE put it there (#46)

> **RENUMBERED 2026-08-02, was R2-037.** Four pairs of duplicate numbers had accumulated in this log from agents allocating concurrently. Each pair was resolved by keeping the number that EXTERNAL CODE already cites, and moving the other. `anim/build_camera_rig.py`, `tools/build_verify_scene.py` and `tools/item_presence.py` all cite R2-037 meaning the beat-3 shutter, so the shutter keeps it.


**Fixed.** `world_contract.py` 1.1.0 -> 1.1.1, plus `build_architecture`.

Measured on the reassembled world (`assembly3.blend`, contract 1.1.0) with the
per-frame placement gate:

    car_path   ARCH_RetainEdge   1.526 m in   at (142.555, 28.448, -0.161)
    car_path   ARCH_PitWall      1.067 m in   at (144.282,  29.425, +0.200)
    road corridor CLEAN, closest approach ARCH_Gantry +1.149 m
    camera path   CLEAN, closest approach BR_Verge_R  +0.648 m

Telemetry frame 138 puts the car at world (144.75, 29.17), lap station 3443.15,
u = +10.94, doing **207.0 km/h**. The car's body half-width is 1.0025 m, so both
objects are inside the BODY envelope, not merely inside the gate's 0.60 m margin.

### The wall was misplaced, and the contract misplaced it

`_Corridor._build` pinned `barrier_offset(s, +1)` to `PIT_WALL_Y` from
`_pit_straight_station(GARAGE_X0)` = **s 3430.0**, the declared garage frontage.
The pit-exit road — the access ribbon, which IS the pit lane for these 150 m —
is still OUTBOARD of that line there. Measured by sweeping `access_edges`'
outboard edge into world space and re-projecting it onto the lap:

    s      3430    3435    3440    3445   3447.71   3450    3455    3460
    u_out  14.09   13.16   12.35   11.75   11.500   11.34   11.09   11.02

so for **17.7 m** the contract asked for a solid concrete wall standing in the
middle of a road, and `build_architecture` built one.

### The brief's diagnosis was wrong, and the geometry says so

The defect report proposed that the wall "belongs BETWEEN" the transit lane and
the racing line, "around y ~= 22" in world coordinates. There is no such station.
At s = 3443 the transit centreline is u = +10.94 and `verge_edge` is 10.50, so
the whole gap between the two is racing surface; a wall at u ~= 5.5 would stand
inside the 8.000 m half-width of the pit straight. The transit route and the lap
**converge and cross** — that is what a pit exit does. The answer is not a
different `y`. It is that the wall BEGINS AT THE CROSSING, which is also what a
real circuit does: the pit wall starts after the pit exit has merged.

### The fix

`PIT_WALL_S0` is **derived** from `access_edges` — the last station at which the
ribbon's outboard edge is outboard of `PIT_WALL_Y`, s = **3447.71**, circuit
x = -227.29 — instead of from `GARAGE_X0`. The open pit-exit apron now runs up to
it, so the apron ENDS where the wall BEGINS: one boundary, stated once.

The contract also publishes the terminal, because the NOSE is the thing that has
to be clear and v1.0.x's `build_architecture` had already moved its own west end
by hand to a literal -228.0 with a 4.2 m nose that tapers in HEIGHT ONLY — so its
face was still on `PIT_WALL_Y` and it is what the gate caught.

    PIT_WALL_TERMINAL_M        5.0    nose at s = 3447.71 = circuit x -227.29
    PIT_WALL_TERMINAL_FLARE_M  0.60   nose face 12.10, running face 11.50

The flare is where the clearance comes from and it is a real object: a flared
barrier terminal is standard circuit furniture.

`ARCH_RetainEdge` — the deeper of the two violations — was a second object with
the same cause. `platform_edge(s, +1)` runs 30.92 m at s = 3400 and 12.28 m at
s = 3429 while the car crosses those stations at u = 26.0 and 15.9, so from
s ~= 3405 east the corridor RIM lies inboard of the driven route and the retaining
edge stands on it. `_fc_clearance` (the showroom forecourt) was the only keep-out
that loop applied. The contract states the transit one now:
`TRANSIT_KEEPOUT_M` = 1.20 m, `transit_keepout()` and `rim_buildable()`, for every
module that stands anything on a rim.

### What moved, and what did not

Diffed function-by-function against the same file with only `s_lp0` reverted:

    barrier_offset (side +1)  max  14.841 m   nonzero over s 3385.25..3447.75 only
    platform_edge  (side +1)  max  14.297 m   same span
    runoff_edge    (side +1)  max  11.275 m   same span
    apron_zone     (side +1)  max   0.560     s 3430.25..3492.75
    barrier_type   (side +1)  B_CONCRETE -> B_NONE over s 3429.5..3447.25
    ground_z                  max   0.371 m   s 3430.2..3492.8, at u = 45
    side -1                   IDENTICAL, every function, every station

108 m of a 3675 m lap. Everything else is bit-for-bit.

### The gate

`--selftest` [15] measures the minimum distance from the wall face to the
ribbon's outboard edge over the whole wall span, for **any** declared wall start,
and it is run against the artefact already known to be bad:

      ok   the pit wall never stands in the pit-exit road
           min face-to-ribbon 0.317 m over the whole 357.3 m wall
      ok   ... and the check FAILS the wall start v1.1.0 shipped
           s = 3430.00 gives -1.986 m — the face is 1.986 m INSIDE the ribbon

## R2-055 — 42 m² of unbuilt ground at the pit exit, and a 0.30 m stand-off nobody laid (#47)

> **RENUMBERED 2026-08-02, was R2-038.** Four pairs of duplicate numbers had accumulated in this log from agents allocating concurrently. Each pair was resolved by keeping the number that EXTERNAL CODE already cites, and moving the other. `world/itemkit.py` and `tools/relief_audit.py` cite R2-038 meaning the dead bump node, so the bump node keeps it. `docs/MASTER-PLAN.md` cited R2-038 meaning THIS entry and has been corrected to R2-055.


**Fixed in part.** `world_contract.py` 1.1.1 (`ribbon_edge_u`), `build_barriers`,
`build_architecture`.

The unbuilt-corridor defect had already gone 658.0 m² / 104 stations -> 52.0 m² / 26
on a coarse 2 m x 1 m grid, and a 0.5 m x 0.10 m map found a further 32.25 m² the
coarse grid could not see. Re-measured on the reassembled world (`assembly3.blend`,
contract 1.1.0) over s 3380-3600, u 10-16, 26 901 samples at 0.50 x 0.10 m, a
sample counting as a hole when no ground surface lies within 50 mm of the datum:

    840 hole samples = 42.00 m2 over 303 stations, widest 1.7 m, mean 0.251 m

    SURF_AccessRoad | BR_Verge_L                 22.95 m2  170 runs  dz p50 13.85 mm
    SURF_AccessRoad | None (past the scan)        6.70 m2   14 runs
    SURF_Track | BR_Verge_L                       4.70 m2   57 runs  dz p50 12.06 mm
    SURF_Track | SURF_AccessRoad                  3.25 m2   56 runs  dz p50  4.93 mm
    ARCH_PitWall | ARCH_Paving_PitLane            2.60 m2   14 runs
    ARCH_Paving_ApronPlatform | SURF_AccessRoad   0.95 m2   14 runs  dz p50 32.30 mm

### The 22.95 m² is one line of code, and it is RULE 1 again

`build_barriers.platform_inner` cut the runoff platform's inboard edge to the
ribbon's outboard edge **plus `ACCESS_RIBBON_SAW_M` = 0.30 m**, and found that
edge by sweeping `u` in 0.10 m steps and taking the last sample INSIDE. So the
band began 0.30-0.40 m outboard of a road that stops dead, and nothing laid the
strip between.

`ACCESS_RIBBON_SAW_M` is **paving's** joint. Its own contract docstring says it
exists so `build_architecture`'s precast slab and `build_surface`'s sawn edge meet
at a joint instead of interpenetrating. `build_barriers` lays hot asphalt on the
same `ground_z`; there is nothing to saw, so it butts, and a butt joint on a shared
datum is exact and not toleranced.

The contract publishes the edge now — `ribbon_edge_u(s, "out" | "in")`, the
ribbon's edges in LAP coordinates, binned per 0.25 m station at 1 mm and **NaN
where the ribbon does not reach**, so a consumer cannot extrapolate an edge across
the 240 m of pit straight the ribbon is nowhere near.

### And a frame mismatch worth 0.44 m

`access_edges` clips the ribbon's inboard edge to `verge_edge` **at the route's own
station**, but over the merge arc the route heading differs from the lap heading by
up to 3.3 deg, so that clipped edge lands up to **0.44 m outboard of `verge_edge`**
once it is re-projected onto the lap. `build_architecture` then subtracted a
further 0.30 m saw margin from it, putting its slab's inboard cut at u = 10.64
while `SURF_Track` ends at 10.50 and `SURF_AccessRoad` really begins at 10.94.
Measured by the new recess gate as a **13-100 mm wide, 300 mm deep** slot at
s = 3400-3420. `apron_clearance` measures the inboard side in lap coordinates now.

### The measurement lesson, applied to the measurement

Every `SURF_Track | BR_Verge_L` and `SURF_Track | SURF_AccessRoad` run in the map
was **exactly one 0.10 m sample at exactly u = 10.500** — `verge_edge` to the
millimetre, and the first line of a round grid. Two abutting meshes share an edge
geometrically, not topologically, and a ray aimed at that edge can miss both. The
probe therefore runs the whole map **twice, on two offset grids**, and reports the
hole area in runs wider than one sample separately from the raw total.


## R2-039 — every sawn joint in the pit-exit apron was a black line, not just one (#48)

**Fixed.** `world_contract.py` 1.1.1 (the model), `build_architecture` (the
geometry and the gate).

The review found **3,390 pixels below 0.02 luminance** in `CAM_APRON_EDGE.png`,
in a frame whose track surface reads 0.1729 and which has nothing else below 0.05.
Ray-cast, every one of them landed on `ARCH_Paving_ApronPlatform` at
**34.17-34.45 mm below datum**, u = 12.097-12.102, 4.9-11.4 m from a 0.55 m lens.

`build_architecture`'s own gates PASSED it: `DEPTH_LIM` is 66 mm and the recess is
34 mm; `SURFACE_LOW_FRAC` is 3 % and it was 0.66 % of columns. Its own log line
says so in as many words:

    the pit-exit apron edge is a joint, not a shaft   PASS  deepest 35.0 mm (limit 66)

### It was not a missing bay

Scanning u at **1 mm** on the assembled world found the same signature at
s = 3300 / 3340 / 3380, at u = 39.047-39.054 — **8 mm wide, 35.0 mm deep,
`ARCH_Paving_ApronPlatform`** — which is a bay line, one every 3.0 m, the whole
length of the apron. `APRON_SUB_CAP` is 35 mm and the bays are laid ON the datum,
so every sawn joint in the field looked 35 mm down at the sub-base. The code's own
comment claimed "an 8 mm saw joint is 8 mm wide and 10 mm deep". It was not.

### A DEPTH BOUND DOES NOT BOUND BLACKNESS

The sun is 12.47 deg up. `SUN_SHADOW_RATIO` = 4.5222, so a 34 mm step casts 155 mm
of shadow and **nothing narrower than 155 mm gets any direct sun on its floor at
all**, whatever the depth gate says. What is left is the sky the slot can see
through its own mouth: for an infinite slot of width w and depth d that is
`sqrt(1 + r^2) - r` with `r = d/w`, which is 7.25 % for the 5 x 34 mm slot that
rendered black and 41 % for an 8 x 8 mm one.

`world_contract` publishes the model — `recess_relative_radiance(w, d, bearing)`,
`recess_is_black`, `max_recess_depth`, `TOL_RECESS_RADIANCE` = 0.10 — driven by the
DECLARED SUN and the declared irradiances, so it moves when `build_sky` moves.
Calibrated on measured artefacts, not on taste:

    THE DEFECT           5.0 x 34.3 mm  ->  0.024   3,390 px below 0.02
    shallowest legitimate joint in the
    same frame           8.0 x  5.0 mm  ->  0.180   probeH: 7 of 1920 columns
                                                    on scanline py=1990 were
                                                    more than 5 mm low
    the declared sealant lap  50 x 5 mm ->  0.711   invisible

0.10 is 4.2x above the first and 1.8x below the second. `max_recess_depth(0.005)`
is **7.4 mm, not 66 mm**.

### The fix is the one a real slab uses

The joint is **sealed**. A second, shallow cap (`A_Sealant`, 0.055 albedo — a real
polymer-modified bitumen, dark but not black) runs under the whole bay field at the
contract's own declared `APRON_JOINT_DEPTH_M` = 5 mm invert, so what shows in a
joint is sealant 5 mm down and not sub-base 35 mm down. The deep bedding stays
exactly where it was, doing the job it was added for. `build_architecture`'s own
apron-edge gate went from **35.0 mm to 5.0 mm deepest**.

### The gate, and it fails the artefact already known to be bad

`build_architecture.verify_contract` now scans every declared boundary at **1 mm**
over 216 cross-sections, finds every CLOSED recess (a run that reaches the end of
the scan is a step, not a slot, and is excluded; a one-sample run is a hairline and
is counted separately, because a ray aimed at a shared mesh edge can miss both
sides), and evaluates `C.recess_relative_radiance` for each. It reports the darkest
recess it found whether or not it fails, and a companion row asserts that the model
still calls the 5.0 x 34.24 mm recess that SHIPPED black and the 8 x 5 mm joints
beside it not-black.


## R2-040 — TER_Ground was built UNDER build_architecture's concrete (#50)

**Fixed.** `world_contract.py` 1.1.1 (`platform_field`), `build_terrain`
(`cut_field`).

Measured on the reassembled world by casting the full ray stack in 7 585 columns
over the pit-exit apron and reporting every pair of DIFFERENTLY-OWNED surfaces
within `TOL_COPLANAR_M` = 30 mm:

    ARCH_Paving_Paddock x TER_Ground   859 columns   |dz| p50 15.59 mm
                                       s 3196-3406, u 41.0-45.0
    ARCH_Paving_PitLane x TER_Ground    60 columns   |dz| p50 16.59 mm
                                       s 3432-3440, u 16.0-23.0
    49 of 7 585 columns (0.65 %) within 2 mm

`build_terrain` cuts a hole for `road_corridor_mask` and nothing else. For the
declared z = 0.000 platform it only FLATTENED its height field — `built =
max(pad, r1)`, `z_nat = z_nat*(1-built) - 0.20*built` — so the mesh was still
there, under the concrete. The contract's §11 says terrain builds no ground inside
the declared platform; terrain simply had no signed field to cut it with, and
nobody had checked.

`C.platform_field(x, y)` is `apron_platform_mask(raw=True)` as an exact signed
distance (a union of box SDFs), so a cell that straddles the platform edge is
CLIPPED rather than dropped or kept whole — the same reason `corridor_field`
exists. `build_terrain.cut_field = min(corridor_field, platform_field)` and the
cutter, the bisection refinement, the rim infill and the full-quad test all use it.

Cross-check that this is the same region and not a second opinion about it: the
declared platform is 63 725 m² of which 76 % lies outside the corridor — 48 400 m²
— against `build_architecture`'s own reported `paving_m2` of 48 239, agreeing to
0.3 %. Measured on the rebuild, terrain's hole went from **308 312 m² to
360 869 m², +52 557 m²**, and the cut took 103.4 s against 111.3 s before.


## R2-056 — cutting terrain out of the declared platform exposed 21 m² the paving never laid

> **RENUMBERED 2026-08-02, was R2-041.** Four pairs of duplicate numbers had accumulated in this log from agents allocating concurrently. Each pair was resolved by keeping the number that EXTERNAL CODE already cites, and moving the other. `tools/wheel_rotation_gate.py` cites R2-041 meaning the wheel_rot_rad snap-back, so that keeps it.


**NOT FIXED. Newly measured, and it is the same defect R2-040 is about, seen from
the other side.**

R2-040 cut `TER_Ground` out of the declared z = 0.000 platform, because two owners
on one square metre flicker under a moving camera. Re-measuring the pit exit on the
rebuild found the seam total had dropped 42.00 -> 27.65 m² (round grid) and
33.65 -> 25.85 m² (offset grid) — but the composition had changed:

    BEFORE (assembly3, 1.1.0)          AFTER (assembly4, 1.1.1)
    SURF_AccessRoad | BR_Verge_L 22.95   ARCH_Paving_ApronPlatform | ARCH_Markings 10.80
    SURF_AccessRoad | None        6.70   ARCH_Markings | ARCH_Markings              9.95
    SURF_Track | BR_Verge_L       4.70   SURF_Track | BR_Verge_L                    1.85
    SURF_Track | SURF_AccessRoad  3.25   SURF_Track | SURF_AccessRoad               1.35
    ARCH_PitWall | ARCH_Paving_PitLane 2.60   ARCH_PitWall | ARCH_Paving_PitLane    0.20

The 22.95 m² stand-off is gone (R2-038). What replaced it is **~21 m² bounded by
`ARCH_Markings` on one or both lips**, in one patch: **s 3443.0-3447.5,
u 12.7-15.2** — 2.2-2.6 m wide, about 5 m long, immediately west of the pit wall's
new nose at s = 3447.71.

`C.apron_platform_mask(x, y)` returns **True** over that whole patch and
`C.world_ground_z` hands it to `build_architecture:paving`. The markings programme
agrees — its paint is there. `ARCH_Paving_Apron` simply does not lay a bay on it.
`TER_Ground` was underneath the whole time and nobody noticed, which is exactly the
argument for cutting it: **an accidental backstop is not an owner.**

The 1 mm recess scan shows the same thing at the apron's outer rim, where the
bedding's 150 mm overrun is now the top surface for 150 mm at s 3220-3380
(35.0 mm down, `recess_relative_radiance` 0.33 — dark but not black), and two
genuine 0.30-0.60 m wide, 300 mm deep holes at s 3410 and s 3440.

**The fix, when someone takes it**, is in `build_architecture.build_paving`: its
apron bay grid does not reach this patch. It is NOT a contract change — the
contract already says who owns it, in three separate places, and all three agree.

## v1.1.1 — the before/after, on two 4.0 GB assemblies of the same world

Everything below is `assembly3.blend` (contract 1.1.0, the baseline rebuild) against
`assembly4.blend` (contract 1.1.1), measured with the SAME instruments in the same
session. Neither is the stale `assembly2.blend`, which was built against 1.0.1.

    tools/placement_gate.py, per-frame camera path, 28 403 objects
                                    BEFORE                      AFTER
    road corridor                   CLEAN  ARCH_Gantry +1.149    CLEAN  +1.149 (unchanged)
    camera path                     CLEAN  BR_Verge_R  +0.648    CLEAN  +0.648 (unchanged)
    car path, closest approach      ARCH_RetainEdge  -1.526      ARCH_RetainEdge  -0.155
    violations                      2                            0
    verdict                         PLACEMENT_FAIL               PLACEMENT_CLEAN

    probe_pitexit, s 3380-3600 x u 10-16 at 0.50 x 0.10 m
    seam, round grid                42.00 m2 / 303 stations      27.65 m2 / 103 stations
      ... in runs > 1 sample        37.05 m2                     22.50 m2
    seam, offset grid (+37 mm)      33.65 m2 / 256 stations      25.85 m2 /  51 stations
      ... in runs > 1 sample        32.30 m2                     24.30 m2
    SURF_AccessRoad | BR_Verge_L    22.95 m2                     0.05 m2

    1 mm recess scan, the sawn bay joints at s 3300 / 3340 / 3380
    width x depth                   8 mm x 35.0 mm               8 mm x 5.0 mm
    recess_relative_radiance        0.037  (BLACK)               0.180  (grey line)

    full ray stack, 7 585 columns over the pit-exit apron
    columns with two owners <2 mm   49  (0.65 %)                 1  (0.01 %)
    ARCH_Paving_Paddock x TER_Ground  859 cols, dz p50 15.59 mm  gone
    ARCH_Paving_PitLane x TER_Ground   60 cols, dz p50 16.59 mm  gone

    build_terrain's hole            308 312 m2                   360 869 m2
    build_architecture, deepest recess at the apron edge
                                    35.0 mm                      5.0 mm

**What is NOT closed**, stated plainly:

  * `ARCH_RetainEdge` still reaches **0.155 m** into the gate's swept car volume at
    world (141.664, 29.51). That is 0.445 m clear of the car BODY and inside the
    gate's 0.50 m edge-family allowance, so the gate reports CLEAN — it is not a
    silent pass, the number is printed. Raising `TRANSIT_KEEPOUT_M` from 1.20 to
    ~1.95 m would remove it; it was left at 1.20 because that number is calibrated
    against the swept volume and not against this one object.
  * ~21 m2 of declared apron that `ARCH_Paving_Apron` never laid is now visible
    because `TER_Ground` no longer covers it. See R2-041.
  * `build_architecture.verify_contract` still reports **5 black recesses** (worst
    0.0592 against a 0.10 bound: 13 mm x 34.6 mm at s = 3418, 11 mm x 24.0 mm at
    s = 3208/3211) and **2 samples** of `ARCH_Paving_ApronPlatform` 18-23 mm below
    the ribbon on the Beat-4 scan line. Both are recorded in
    `assembly4_build.json:contract_fails`. The gate is left FAILING on them rather
    than loosened, because loosening a bound to make a build pass is the failure
    mode this log exists to record.

### A note on `--gate-selftest`, so nobody misreads it

`python3 world/world_contract.py --gate-selftest <old>` is the CONTINUITY gate from
R2-036, and it exits non-zero when the old revision PASSES. Pointed at a copy of
1.1.1 with only `s_lp0` reverted it reports **0 of 23 rows FAIL / "THE GATE IS
WRONG"** — and that is correct, not a failure: the v1.1.0 wall start is perfectly
Lipschitz, it is just in the wrong place, and continuity is not the property that
was violated. The gate for #46 is `--selftest` section **[15]**, which measures the
wall face against the ribbon's outboard edge for any declared wall start and
returns **-1.986 m** for the one v1.1.0 shipped.

---

## R2-038 — the shared kit's bump node was dead, silently, in the foundation

Found by the humankit agent while chasing a fabric scale error. Confirmed and
fixed by me.

`world/itemkit.py` is the shared foundation every wave-2 item is built on, and
`world/items/pit_wall_unit_itemkit.py` is the reference item every campaign agent
is told to read and copy. `NT.bump()` pinned its inputs BY INDEX:

    self.pin(nd, 0, strength)   # Strength      ok
    self.pin(nd, 1, distance)   # Distance      ok
    self.pin(nd, 2, height)     # -> FILTER WIDTH
    self.pin(nd, 3, normal)     # -> HEIGHT

Blender 5.2 inserted **`Filter Width` at index 2**. The live order is

    [0] Strength  [1] Distance  [2] Filter Width  [3] Height  [4] Normal

so `height` went into the filter, the normal chain went into Height, and the
**Height socket of the first bump in every chain stayed at its constant default
of 1.0**. A constant has zero gradient. That bump produced **no relief at all**.

### Why nothing caught it

It built. It rendered. It passed `item_gate`, because `material_depth` counts
nodes and a dead socket is still a node. The only check that could see it is
`relief_reads_as_lip_and_shade` — which is the check **21 of 28 wave-1 items
already fail**, so one more failure looked like the crowd, not the cause.

Measured on three spheres under the contract sun at 10 m / 35 mm, fine-band
contrast against a smooth control of identical colour and roughness (the control
moved 0.4 % between renders, so the three are comparable):

    shipped, miswired                     0.257x
    frequency-corrected, still miswired   0.972x
    wired by name                         2.438x     (gate bar 2.0)

Frequency was not the fault. Fixing the frequencies and raising amplitudes 5x
moved the rendered image by **nothing**, because the socket carrying the signal
was never connected.

### Fix

`NT.pin_named()` wires by socket name; `bump()` uses it. `NT.pin()` gained an
optional `expect=` that turns a silent miswire into a `RuntimeError`.

**And a standing guard**, which matters more than the fix: selftest step [0] now
checks **every index this file assumes against the live socket names** — 32
assumptions across 10 node types — and asserts Bump's four names exist and that
index 2 is no longer `Height`. Milliseconds, no render. All 18 index-pinned calls
were audited; Bump was the only real breakage. (`ValToRGB[0]` reported as `Fac` →
`Factor`, but it is that node's only input, so the index still holds. A rename is
not a move.)

### The lesson, and it is a new shape

Every prior entry here is *a check that measured the wrong thing*, or *a fix that
could never run*. This is a third kind: **a latent version trap.** The code was
correct when written, stayed syntactically valid, kept producing a plausible
material, and passed every structural test — while a version bump quietly
rewired it. Nothing asserted that a named socket sat where it was pinned.

**If you address a thing by position, assert its name.** That assertion now
exists and cost one selftest step.

Thirteen instruments on this project have now turned out to be the broken thing.

---

## R2-042 — the contract and the telemetry disagreed about where the car drives, by 9.044 m

**Fixed in part.** `world_contract.py` 1.1.1 -> **1.2.0**. The DIVERGENCE itself is
NOT fixed and is not this entry's to fix; what is fixed is that the contract now
knows about it and no longer publishes keep-outs that only cover one of the two
curves.

`world_contract.access_route_point` merges onto the pit straight on the declared
**R150 / 40 deg arc**. `tools/build_telemetry.py:281` builds the same merge out of
the same `SPEC["transit"]["legs"]` block by **linearly interpolating the four leg
endpoints**:

    tx = np.interp(tr_s, cum, [p[0] for p in pts])

A 104.72 m arc of radius 150 stands `150*(1 - cos 20 deg)` = **9.04 m** off its own
chord, and the chord is on the OUTBOARD side. Measured, telemetry.csv re-projected
onto `access_route_arrays`:

    route t      0..45     59.6    76.7    86.3   96.6..107.5   130.4   154.0
    car v        +0.00    +3.23   +7.02   +8.28    +8.95..9.04  +6.47   +0.13

    max |v| 9.0406 m at the CSV's own frames, 9.0442 m on the line sampled at 0.01 m
    the car's CENTRE runs up to 3.041 m OUTSIDE the ribbon's declared outboard edge
    its SWEPT BOX (body 1.0025 + the gate's 0.60 m) up to 4.643 m outside
    over 60.1 m of a 381.88 m transit

### This is the same shape as the `barrier_offset` defect

Two modules consuming the same offset and disagreeing about it. `build_barriers`
S21 found it independently and carries a private workaround that reads
telemetry.csv directly, ending *"Delete this the day the telemetry and
access_route_point agree."* Nothing propagated it back to the contract, so every
keep-out v1.1.1 published — `transit_keepout`, `rim_buildable`, `_pit_wall_start`
— was derived from the RIBBON while `tools/placement_gate.py` measures the
TELEMETRY. That is the whole causal chain behind

    car_path  ARCH_RetainEdge  1.198 m in  at (138.431, 27.140, -0.179)
    car_path  ARCH_PitWall     1.067 m in  at (144.282,  29.425, +0.200)

### The brief's diagnosis was wrong twice over, and so was R2-037's rebuttal

The report proposed that the wall "belongs BETWEEN" the transit lane and the
racing line, "around y ~= 22" in world coordinates. R2-037 answered that there is
no such station, and that arithmetic is right: at s = 3443 the transit centreline
is u = +10.94 and `verge_edge` is 10.50, so the whole gap is racing surface. But
**it answered using the ribbon**, and the reason the transit centreline is at
u = +10.94 there at all is that the car is 4.6 m off its own road at that frame.
Both readings were arguing about the position of a curve neither had checked
against the other.

### The fix

The DRIVEN line is derived **here**, from the same spec block `build_telemetry`
integrates — RULE 1 satisfied without breaking RULE 2, because the contract still
reads nothing but SPEC, numpy and the standard library and still never opens a
CSV. Verified against the artefact: `transit_drive_arrays` reproduces
telemetry.csv's own x, y to **1.02e-4 m** over all 219 transit frames, mean
3.18e-5 m (selftest [18]).

`transit_keepout()` is now the **UNION** of the declared ribbon (+1.20 m) and the
driven swept car box (+0.60 m). The union is the correct keep-out **whichever of
the two curves is eventually declared right**, so it does not have to wait for
that argument. `_pit_wall_start()` takes the later of the two crossings.

NEW: `transit_drive_point/arrays/project`, `transit_drive_keepout`,
`TRANSIT_DRIVE_NODES/CUM_M/LEN_M/CLEAR_M`, `CAR_BODY_*`, `CAR_CLEARANCE_M`,
`CAR_SWEPT_HALF_W_M`, `CAR_SWEPT_PAD_M`.

### What it moves

**`PIT_WALL_S0` does not move**: 3447.7092, the ribbon's crossing, because the
driven swept box crosses `PIT_WALL_Y` at 3446.007 — 1.70 m earlier. **v1.1.1
cleared the pit wall by luck, and this entry is the reason it was luck.** Nothing
on the pit straight rebuilds for R2-042.

`rim_buildable(s, +1)` loses **15 of 14 700** stations, s 3438.25..3441.75 — a
3.5 m gap in `ARCH_RetainEdge` at exactly the metres where that beam was measured
1.198 m inside the car body. Of the 2 440 rim stations whose outboard ground is
declared platform, buildable goes **2 289 -> 2 274**.

### Still open, and it is a decision, not a patch

Which curve is right. Making the telemetry follow the arc re-times Beat 4 and
re-keys a 479-key camera rig; making the ribbon follow the chord throws away a
declared R150 merge and moves `SURF_AccessRoad`. Until it is taken, the car
drives 3.0 m off its own road for 60 m of Beat 4 in shot, and
`build_barriers` S21's private telemetry read stays.

### The measurement lesson

The contract's own R2-037 entry closed #46 with a geometric argument that was
internally valid and rested on a curve the car is not on. **When two files
integrate the same declared quantity by different methods, the disagreement is
not visible in either file.** The only thing that found it was projecting one
file's artefact onto the other file's function.

---

## R2-043 — the circuit crossed its own corridor, and now it does not (R2-035 closed)

**Fixed.** `world_contract.py` 1.2.0, `build_barriers.py`.

R2-035 measured it and left it open deliberately. Reproduced here bit-for-bit
before touching anything, which is the only reason the fix can be trusted:

    side  declared barrier face inside SOME OTHER leg's road corridor   worst
     +1        406 of 14 700 stations   (2.76 %)                       7.493 m
     -1          0 of 14 700 stations   (0.00 %)                            —

    worst at s = 786.0, landing at |u| = 0.007 m on the leg at s = 1182.4

(v1.0.1 was 3.56 % with THE SAME 7.493 m worst case. The v1.1.0 rate cap moved
the COUNT, not the INTRUSION, and reading that as progress is the mistake this
entry exists to close.)

### The fix: `owned_edge` is the contract's now

`build_barriers` S4b's ownership solve is promoted into `world_contract` S9b
**unchanged** — same 2.0 m station step, same 65 laterals, same 2.0 m / 0.25 m
self tolerances, same 0.75 m medial-axis bias, same 0.30 m/m taper, same 60 m
blend — and `barrier_offset` is clamped by it.

**No exclusion window, and that is the design.** The obvious shape is a KD-tree
over dense centreline samples with an arc-length window so a station does not
read its own neighbours as a foreign leg. It was rejected because *a window is a
tuning parameter that can silently disable the check*: too narrow and a hairpin
reads as foreign, too wide and a real crossing is swallowed. (Measured while
building this: a naive "nearest station more than 2 m of arc away" pre-filter on
a 2 m grid excludes exactly one neighbour and returns 4.0 m — the grid step — for
every station on the circuit. It looks like a measurement and it is the grid.)

Asking `project` for the GLOBAL nearest inverts the question: nothing has to be
excluded, only RECOGNISED. And the own-station answer is not merely close, it is
EXACT, because every element on this circuit is a straight or a circular arc —
not one clothoid — so the foot of the perpendicular from a point on the normal at
`s` IS `s`. Measured over all 238 940 samples:

    SELF     max |ds| 0.0000 m   max |du| 8.2e-14 m   (231 987 samples)
    FOREIGN  min |ds| 43.381 m   max |ds|    555.0 m    (6 953 samples)

The two populations are **43.4 m apart** and any tolerance in (0, 43.381) gives a
bit-identical answer. `OWNED_SELF_WINDOW_M` = 2.0 m sits 2.0 m above one and
41.4 m below the other. Two controls run every selftest:

    the T4 HAIRPIN, R = 28 m, the tightest on the circuit: 43 solve stations,
        max self |ds| 0.0000 m  -> a hairpin is never read as a foreign leg
    the PIT STRAIGHT, the longest run: 406 solve stations, 0 foreign samples,
        while the same solve finds 6 953 elsewhere  -> not silently dead

### The result, and the two controls it is judged against

    POSITIVE CONTROL  barrier_offset_declared (v1.1.1)  406 / 14 700   7.493 m
    NEGATIVE CONTROL  verge_edge + 1.00 m                 0 / 14 700       —
    THE RESULT        barrier_offset       (v1.2.0)       0 / 14 700       —
                      owned_edge                          0 / 14 700       —

Both sides. Zero, not "improved".

### S4b's clamp survived, and here is the measurement that says it may

    barrier_clamp_report()  frac_of_lap 0.0000 both sides
                            exact_vs_contract_frac 1.0000 both sides
    |world_contract.barrier_offset - build_barriers.barrier_offset|  0.000e+00

It is a **measured no-op**: the contract's line already satisfies `line <= avail`
by construction, so `hit` is empty and `line == target == bo` at every station.
It is kept because it is also the ASSERTION that no barrier this module builds
can be inside `build_surface`'s own mesh, and an assertion that has become cheap
is not a reason to delete it — if a future contract revision reopens the defect,
`build_barriers` raises at import instead of building an Armco wall across the T4
braking zone again. Deleting it would remove the only thing that caught the
defect the first time. `barrier_clamp_report()` is what to read to know which of
the two it is doing.

### NO BARRIER MESH MOVES

Verified by re-running S4b's own `_build_barrier_line` against the pre-ownership
contract line — i.e. reproducing what that module produced under contract 1.1.1 —
and diffing:

    side +1  max |diff| 0.000e+00 m   0 of 14 700 stations differ by > 1e-9
    side -1  max |diff| 0.000e+00 m   0 of 14 700 stations differ by > 1e-9

`build_barriers` has been building the shipped world off this exact line since the
T4 Armco wall. What changes is that `build_dressing`, `build_terrain`,
`build_architecture` and 435 item modules — every one of which reads the CONTRACT,
not `build_barriers` — stop being handed a line that runs 7.5 m into another leg's
racing surface. The divergence warning in R2-035 ("any module that needs the
barrier line through s ~ 660-1215 on the left must read
`build_barriers.barrier_offset`") is **withdrawn**: the two are now the same array.

### `rim_buildable` was the live end of it

MEASURED against telemetry.csv on v1.1.1: `corridor_rim(s, +1)` lies inside the
car's swept volume at **62 of 14 700** stations, and `rim_buildable` said
**BUILDABLE at 30 of them** — s 764..917, worst **1.481 m** in, where T3's 72.8 m
rim reaches across onto the S4/T5 leg the car takes at speed. Deeper than the
1.067 m pit wall that started this thread. `build_architecture` happens not to
build there because its own `PLAT_RECTS` test excludes it; nothing in the
CONTRACT said so, and the item campaign reads this function. It now refuses the
rim beyond ownership as well as in the transit keep-out: **0 of 73** buildable.

---

## v1.2.0 — WHAT MOVED, for the rebuild

Every field, swept over the 14 700-station 0.25 m grid, v1.1.1 -> v1.2.0.

    field                        min        max        rms      stations moved
    barrier_offset  (side +1)  -44.5978   +0.0000    8.1097        9.76 %
    barrier_offset  (side -1)   -0.0000   +0.0000    0.0000        0.00 %
    platform_edge   (side +1)   -2.4602   +0.0000    0.6709        8.82 %
    platform_edge   (side -1)   -0.0000   +0.0000    0.0000        0.00 %
    corridor_rim    (side +1)   horizontal max 2.4602 m, rim z max 0.0394 m
    corridor_rim    (side -1)   0.0000 m
    runoff_edge     both sides   0.0000    0.0000    0.0000        0.00 %
    apron_zone      both sides   0.0000    0.0000    0.0000        0.00 %
    ground_z, half_width, verge_edge, kerb_top_z, access_*, ribbon_edge_u,
    apron_platform_mask, platform_field, every light, every tolerance
                                 UNTOUCHED — no code path reads barrier_offset

    PIT_WALL_S0                  3447.7092  ->  3447.7092   (unchanged)
    rim_buildable   (side +1)    98.97 % -> 85.14 % buildable
                                 (13.73 % ownership at s 703..1208, 0.10 % transit
                                  at s 3438.25..3441.75)
    rim_buildable   (side -1)    100 % -> 100 %

**So the rebuild is: the left-hand barrier line and the ground that follows it,
over s 661-884 and 1081-1213 — and it rebuilds to exactly what `build_barriers`
was already building there. The terrain hole (`platform_edge`) shrinks by up to
2.46 m over the same span, which is a real change to `TER_Ground`'s weld ring and
to `build_barriers` S4c's fill. Nothing else on the lap moves by a float ulp.**

Contract import cost 3.78 s -> 8.07 s (the ownership solve is 239 k projections,
eager on purpose — a lazy cap is a second answer waiting to happen).
`build_barriers` import 5.5 s -> 2.4 s: it no longer runs its own copy.

Selftest 126 checks -> **149**, all passing.

---

## R2-044 — the barrier break test was dead, and setting it right made it fire on round-off

**Fixed.** `world_contract.py` 1.2.0, `build_barriers.py`.

`build_barriers.BARRIER_BREAK_RATE = 2.00` was a private copy of what should have
been `WC.BARRIER_MAX_LATERAL_RATE` = 1.95, and it is used as a **strict `>`**. On
a line the contract guarantees is 1.95-Lipschitz **by construction**
(`_cone_erode` at exactly that rate), a `> 2.00` test can never fire whatever the
corridor does. It is R2-012 wearing a threshold: an assertion that cannot fail.

### And the two-line fix was wrong

Set to a flat 1.95, it fires on **float round-off**. MEASURED on the shipped line:

    max |d off / ds|   side +1   1.9499999999999993
                       side -1   1.9500000000000028   <- 2.9e-15 OVER

which fired at 11 stations and blanked **17 m of Armco** on the right-hand side of
the lap for nothing. `_cone_erode` builds the line as repeated `e[i-1] + rate*ds`,
so a station where the erosion binds lands on `rate` to within a few ULPs either
way and the sign of that error is not something a contract can promise.

Found by measuring the artefact after making the change, not by reading it.

### The fix

The contract publishes **both** numbers: `BARRIER_MAX_LATERAL_RATE` = 1.95, the
rate it GUARANTEES, and `BARRIER_BREAK_RATE` = 1.95 + `RATE_EPS`, the rate at
which a consumer may call the line broken. `RATE_EPS` = 1e-6 m/m — one micron of
lateral per metre of station, far below anything geometric, far above the
round-off — and it is the same epsilon the continuity gate in S14 had already
allowed itself privately. Selftest [17] now checks both failure modes on the real
line: it does not fire on the contract's own line, and it does fire on a
synthetic 3.0 m step.

### Other private copies of contract constants, found and fixed

    build_barriers  BARRIER_BREAK_RATE 2.00      -> WC.BARRIER_BREAK_RATE
    build_barriers  owned_edge + _build_owned    -> WC.owned_edge (solve deleted)
    build_barriers  CORRIDOR_BIAS 0.75, BARRIER_TAPER_MAX 0.30, CLAMP_BLEND_M 60,
                    BARRIER_MIN_CLEAR_M 1.00, _CAP_DS 2.0, _CAP_NT 65  -> WC
    build_barriers  CAR_HALF_W 1.0025, CAR_CLEAR_M 0.60, CAR_PAD_M     -> WC
    build_architecture  RIBBON_SAW_M 0.30        -> WC.ACCESS_RIBBON_SAW_M
    build_architecture  ROT_DEG 40.0, PIVOT_C, PIVOT_W -> WC.ROT_DEG / PIVOT_*
    build_surface   CAR_WIDTH 2.005              -> C.CAR_BODY_W_M

All seven were numerically identical to the contract's value, so **no geometry
moves for any of them** — which is the point: they agreed by coincidence, which
is DEFECT 4 exactly, and a coincidence is not agreement.

### Found and NOT fixed — reported so the next agent does not rediscover them

  * `tools/placement_gate.py` keeps `CAR_MARGIN = 0.60` and the literal
    `0.5 * 2.005`, and falls back to `spec["track_section"]["width_m"]` if the
    contract will not import. The gate is deliberately semi-independent of the
    thing it judges, so this is arguably right — but the car box is now
    `C.CAR_BODY_W_M` and the two must be diffed by hand if either moves.
  * `build_dressing.UNTRUSTED_PAD_M = 42.0` is documented as "build_barriers'
    deficit smoothing bleed". That smoothing was deleted in contract 1.1.0
    (R2-036). The constant now pads against a mechanism that no longer exists.
  * `build_surface` and `build_architecture` still read `APRON_JOINT_LAP_M`,
    `APRON_JOINT_DEPTH_M`, `ACCESS_RIBBON_SAW_M` and `ACCESS_RIBBON_T_MIN` as
    `getattr(C, name, <literal>)`. That is deliberate v1.1.0 back-compat, but it
    is the DEFECT-4 pattern still loaded: with the contract at 1.2.0 the
    fallbacks are unreachable and could be deleted.
  * `build_terrain`'s `UNION_BAND = 130.0` is justified by a comment reading "max
    platform_edge is 87.95 m". Still true (87.9479 m, on side -1, which did not
    move) but it is a measured number frozen in a comment, not a derived one.
  * `world_contract.runoff_edge` and `platform_edge` are still NOT ownership
    clamped, on purpose. They are a declared KEEP-OUT for terrain, not a build
    instruction — `build_barriers` lays ground to `platform_reach`, which is
    already bounded by `owned_edge` — and clamping them would move the terrain
    hole by up to 50 m of lateral over 355 m of lap and invalidate S4c's measured
    fill, which cannot be re-verified without the rebuild. `rim_buildable` now
    refuses the rim wherever `platform_edge > owned_edge`, which closes the part
    of that gap where objects get STOOD ON the ground.

---

## R2-041 — `wheel_rot_rad` snapped BACKWARDS 1.4455 revolutions at frame 10

**Fixed.** `tools/build_telemetry.py`, and `telemetry/telemetry.csv` regenerated.

    frame  9   wheel_rot_rad  9.65984
    frame 10   wheel_rot_rad  0.57774      step  -9.08210 rad = -1.4455 rev

**Root cause.** The launch wheelspin — the brief's one sanctioned departure from
rolling contact — was added as a WINDOW rather than as an accumulated angle:

    extra = np.zeros(nfr)
    extra[:spin_frames] = np.cumsum(taper * 2.4 / a.fps / a.wheel_radius * 8.0)
    wheel = wheel + extra

`extra` reached 9.1399 rad at frame 9 and 0.0 at frame 10, so the whole
accumulated slip was thrown away in one frame — during the launch, which is the
one moment in the film where the eye is on the wheels. A wheel that has spun
1.45 turns more than it travelled does not un-spin when it hooks up; it resumes
rolling contact from its new phase. `extra` is now HELD at `slip_accum[-1]` for
every subsequent frame.

**Nothing had ever differenced the column.** `tools/wheel_rotation_gate.py` now
does, with two independent measurements required to agree:

  A. `diff(wheel_rot_rad)` over the raw 1,743 telemetry rows AND over the film's
     2,978 frames walked through `anim/filmtime.py` — because beat 3's ramp means
     a telemetry row and a film frame are not the same thing.
  B. `wheel_rot_rad - s_m / r`, which must be non-decreasing, must RISE across
     the frames the `wheelspin` column flags, and must be FLAT everywhere else.
     B exists because A cannot see an error that happens to be monotonic.

**Measured, before -> after:**

| | before | after |
|---|---:|---:|
| worst backwards step, telemetry rows | **-9.08210 rad (-1.4455 rev)** at frame 10 | **+0.05777 rad** |
| worst backwards step, the film's 2,978 frames | **-6.55220 rad** at film frame 828, 2 frames | **+0.000000 rad**, 0 frames |
| slip (rotation - distance/radius) worst step | -9.13988 rad | -0.00028 rad (the CSV's own 4-dp/5-dp quantisation, bound 0.00029) |
| total revolutions | 1791.6999 | **1793.1546** |

Reconciliation, to 2.6e-13 rev against a stated 1e-4 tolerance:

    1793.1546 rev  =  1791.6999 rev of rolling contact (4052.73 m / 2.2619 m
                      circumference)  +  1.4547 rev of sanctioned launch slip

**The gate's controls.** `--selftest` runs it against four artefacts whose
verdicts are known in advance: the shipped column (PASS), a synthetic clean
series (PASS), the pre-fix windowed slip rebuilt from the shipped column (FAIL,
naming frame 10), and a series that is strictly monotonic but has the launch
slip deleted entirely (FAIL — measurement A passes it, and B is what catches it).
All four behave as declared.

**Regeneration is exact.** `build_telemetry.py` reproduced the shipped
`telemetry.csv` byte-for-byte before the fix was applied, and after it exactly
one column changed: `wheel_rot_rad`, on 1,733 of 1,743 rows. The other sixteen
columns are byte-identical.

**Found, not fixed.** R2-026 still stands and also lands on this column: through
the launch, `x / s_m` = 1.25207, so the body covers up to 13 % more ground than
`s_m` says and `wheel_rot_rad`, computed from `s_m`, under-rotates against it.
That is a different defect in a different column and is left where it is logged.


## R2-051 — beat 1's camera flew through the car AND was aimed at a stale explode plan

> **RENUMBERED 2026-08-02, was R2-042.** Two agents allocated 042/043/044 concurrently
> and neither could see the other. The *contract* triple at R2-042/043/044 above keeps
> those numbers — it is referenced by name from `world_contract.py`,
> `build_telemetry.py`, `build_barriers.py`, `transit_line_gate.py`, `placement_gate.py`,
> `MASTER-PLAN.md` and `R2-042-DECISION.md`. This camera triple moves to **R2-051 /
> R2-052 / R2-053**, which was referenced only from inside this file. If you meet
> "R2-042/043/044" in an older task or transcript, check which it means: the contract
> triple is the transit curve, the corridor crossing and the barrier break rate; this
> triple is the beat-1 camera, the exposure and the beat-3 shutter.

**Fixed.** `tools/build_beatsheet.py`; `docs/beat_sheet.json` and
`world/camera_rig.blend` rebuilt. This is R2-029, plus a second defect found on
the way that nobody had logged.

### Defect 1 — the 163-frame gap (this is R2-029)

Beat 1's last presentation key (CORNER_FL, frame 591) and its final push toward
the car (frame 754) were 163 frames apart with nothing in between. The straight
line between them passes through the assembled car and the quaternion slerp
between the two orientations swings the lens onto the glass wall. **Rendered
frame 669 on the pre-fix rig is a rope-barrier stanchion and empty floor with
not one part in it** (`render/beat1_fix/before_f669.png`).

What that gap actually contains, from `world/beat1_anim_anim.json`: NOSE seats
597-605, FW 630-638, RW 663-671, and **all four corners seat together 696-704**,
which is the beat's climax and the brief's "wheels LAST with a simultaneous
seat". Five landings, none of them shot.

Four CLOSE-OUT keys now swing the camera around the nose — outside the car —
rising and widening 58 -> 48 -> 40 -> 36 -> 38 mm so the whole 5.7 m car is held
as the last parts arrive. Each is placed against a landing. Two BRIDGE keys were
added at frames 434 and 446 for a separate 110-degree pan (RW behind the car to
the rear-left wheel) that crossed with the lens on bare floor.

### Defect 2 — the keys were solved against an older `docs/explode_plan.json`

Regenerating beat 1 from the CURRENT explode plan does not reproduce the shipped
keys: 9 of 15 `look_at` targets move, by up to **1.72 m**. Which file is right
was settled by opening the animation: `world/beat1_anim.blend` at frame 1 agrees
with the current plan to within **0.06 m on all 15 clusters**. The camera keys
were the stale artefact.

The cost, measured as the angle each cluster's bounding sphere sits OUTSIDE the
frame edge at its own presentation key:

    FD    34.45 deg edge vs a 16.13 deg half-frame  ->  OFF SCREEN by 18.32 deg
    NOSE  43.80 deg edge vs a  9.90 deg half-frame  ->  OFF SCREEN by 33.90 deg

Two of the fifteen parts were presented entirely outside the picture, against a
brief whose rule is "No part seats without having been seen". Regenerated, all
fifteen measure **0.00 deg** — dead centre.

### Measured, before -> after

| | before | after |
|---|---:|---:|
| beat-1 keys | 16 | **22** |
| worst aim off the parts field | **48.885 deg** (frame 669) | **7.24 deg** (frame 427) |
| p99 aim | 47.84 deg | **0.00 deg** |
| frames with the subject OFF SCREEN | **77** (runs 442-449, 492-498, **642-703**) | **0** |
| frames with ZERO clusters in frame | **60** (runs 445-447, 480-495, **652-692**) | **0** |
| mean clusters in frame, over 792 frames | 4.38 | **6.63** |
| clusters in frame at 648 / 669 / 686 | 1 / **0** / **0** | **15 / 15 / 15** |
| clusters off screen at their own presentation | 2 (FD, NOSE) | **0** |
| aim-gate verdict, all six beats | CAMERA_RIG_FAIL | **CAMERA_RIG_CONTINUOUS_AND_AIMED** |

**The seam with beat 2 was not touched.** Beat 1's last key stays at t = 31.400,
world [6.8, -4.4, 1.9], 40.0 mm; beat 2's first key is 2.089 m away 39 frames
later at 39.949 mm. Across the boundary: **1.273 m/s, 0.340 deg/frame of aim,
-0.051 mm of focal length.** Beats 2, 3, 4, 5 and 6 are byte-identical to the
pre-fix sheet.

**Verified by rendering, not by reasoning.** 14 frames spanning beat 1 plus two
before/after controls, 1280x720 / 96 samples on the 5090, in
`render/beat1_fix/`. Frame 669 goes from a stanchion and bare floor to the car
mid-assembly with all four corners flying in; frame 686 holds the whole car for
the simultaneous four-wheel seat; frame 704 has them landed.

**The gate that would have caught both.** `tools/build_beatsheet.py` now
measures, in real units, (a) the camera's chord speed and its clearance to the
assembled car body SAMPLED BETWEEN KEYS, because R2-029 lived entirely between
two keys and a jump/step gate cannot see it, and (b) each cluster's angle outside
the frame at its own presentation, against the plan as it stands. Run with
`--check <sheet.json>` it gates an existing sheet, and against the pre-fix sheet
it returns BEATSHEET_VIOLATION naming the 0.000 m fly-through and both
off-screen clusters.

**Found, not fixed.** `build_beatsheet.py` wrote `min_world_time_scale = 0.20`
and only `author_beats2_5.py` corrected it to the solved 0.153719 — so the
pipeline's output depended on how many times it had been run. It now solves the
floor through `filmtime.solve_floor` on the first pass.


## R2-052 — the film's exposure was three independent numbers, and the DERIVED one was wrong

> **RENUMBERED 2026-08-02, was R2-043.** See the note at R2-051.

**Fixed.** `world/film_exposure.py` is now the one expression;
`render/world/assembly/r2/render_setup2.py`, `render_setup3.py` and
`world/build_terrain.py` import it.

Three copies, maintained separately, with nothing that could notice they
disagreed by 0.580 stops:

    world_contract.REFERENCE_EXPOSURE_EXTERIOR  -3.048   derived
    render_setup2.py / render_setup3.py         -3.628   hardcoded, no comment
    build_terrain.py                            -3.628   hardcoded again

### Which one is right — MEASURED, and the answer is the opposite of the report

The defect was reported as "the film renders 0.58 stops UNDER" — i.e. that the
derived -3.048 is right. **It is not.** `tools/exposure_calibration.py` renders
an 18 % lambertian card under `build_sky`'s actual light beside a 32-rung
emissive ladder of known linear radiance and reads the card's value off the
ladder, so the tone curve never has to be known. Six variants, 900x900 / 768
samples on the 5090:

    an 18 % card renders at   2.2351 (AgX)   2.2133 (Standard)   2.2304 (closed-form sRGB)
    -> exposure for AgX mid grey   -3.6343      -3.6201            -3.6312
    -> two view transforms agree to 0.0141 stops

    the hardcoded -3.628 is off by  -0.006 stops
    the derived   -3.048 is off by  -0.586 stops, in the direction that OVER-EXPOSES

### Why the contract's derivation is wrong, decomposed

`REFERENCE_EXPOSURE_EXTERIOR` = log2(0.18 / mean(`C.lambert_radiance(0.18)`)) is
exact arithmetic on inputs that are not the light the film renders in. Measured
downwelling irradiance on a horizontal surface, channel mean, W/m2:

    sky alone, no atmosphere                    11.1818   (C.SKY_IRRADIANCE says 8.4593)
    sky + atmosphere, no sun                    12.9655
    sun + sky, no atmosphere                    28.3005   (the contract formula says 25.9851)
    sun + sky + atmosphere = THE FILM'S LIGHT   39.0106

    SKY_Atmosphere's in-scattering   +0.4630 stops   (C.SKY_IRRADIANCE omits it)
    C.SKY_IRRADIANCE's own shortfall +0.1231 stops   (a finding for build_sky)
    TOTAL                            +0.5862 stops

`build_terrain.md` sec 9.2 had already measured the total as 0.53-0.58 stops from
an albedo probe and was right; this splits it into its two named causes.

**The value is NOT moved to -3.6343, deliberately.** The measurement's own
resolution is 0.04 stops (derived in the calibration file from its leave-one-out
control) and -3.628 sits 0.006 stops away — six times inside the noise. Moving a
shipped constant by less than you can measure is churn and would break the pixel
comparability of the three render_setup cameras placed at bit-identical
positions for exactly that purpose. `world/film_exposure.py --selftest` holds it
to the measurement instead, and its POSITIVE CONTROL confirms the same test
REJECTS -3.048 at 0.586 stops.

### Is any beat over-exposed? Measured, per beat

`tools/exposure_histogram.py`, whose four synthetic controls (pure white, flat
18 % grey, one clipped pixel, a 40x40 clipped block) all return their known
answers. Clipping is counted as FLAT clipped area — a clipped neighbourhood is
lost detail, an isolated clipped pixel is a highlight.

| frame | mean | p99 | max | clipped % | **flat clipped %** | crushed % |
|---|---:|---:|---:|---:|---:|---:|
| B1 f400 @-3.628 | 0.0950 | 0.4287 | 0.4653 | 0.00000 | **0.00000** | 4.999 |
| B2 f828 @-3.628 | 0.0918 | 0.3754 | 0.7348 | 0.00000 | **0.00000** | 2.498 |
| B3 f960 @-3.628 | 0.1246 | 0.2356 | 0.2493 | 0.00000 | **0.00000** | 0.000 |
| B4 f1120 @-3.628 | 0.1014 | 0.1695 | 0.1773 | 0.00000 | **0.00000** | 0.000 |
| B5 f1950 @-3.628 | 0.0334 | 0.0616 | 0.0703 | 0.00000 | **0.00000** | 0.000 |
| B6 f2850 @-3.628 | 0.3752 | 0.9388 | 1.0000 | 0.09039 | **0.07899** | 0.000 |
| B4 assembled world, transit | 0.3899 | 0.7108 | 0.8534 | 0.00000 | **0.00000** | 0.015 |
| B5 assembled world, T4 kerb | 0.4773 | 0.7411 | 0.9061 | 0.00000 | **0.00000** | 0.000 |
| B6 assembled world, closing wide | 0.5239 | 0.7365 | 0.8352 | 0.00000 | **0.00000** | 0.000 |

**NO BEAT CLIPS.** The worst flat clipped area anywhere is 0.079 % of one frame
(beat 6's sky), against a 0.20 % bar; on the assembled world it is 0.00000 % on
all three, with p99 luminance 0.71-0.74 and maxima 0.84-0.91. **The film at
-3.628 is not over-exposed, and rendering it at the contract's derived -3.048
would have pushed those maxima 0.59 stops higher.**

### Found, NOT fixed — and it needs a decision

At the film's single grade, **beats 1 and 2 crush: 5.00 % and 2.50 % of the
frame at pure black.** That is not the grade being wrong; it is the showroom.
`beat1_anim.blend`'s practicals were authored against exposure 0.000, where the
same frame measures mean 0.373 with 0.03 % crushed and reads correctly. One
continuous grade at -3.628, which the brief requires, therefore needs either the
showroom practicals raised by ~3.6 stops or a much larger camera exposure ramp:
`INTERIOR_STOPS` is 0.85 and the gap is 3.6. `build_camera_rig.py` now reports
the disagreement in stops on every build and records it in the continuity JSON
instead of leaving it to be discovered in a washed-out frame.

Also found: `C.SKY_IRRADIANCE` = (4.228, 7.577, 13.573) is 0.123 stops low
against the sky it describes (11.1818 W/m2 measured, 8.4593 published). Not
fixed — `world_contract.py` is another agent's this week.


## R2-053 — beat 3's shutter was a DOUBLE correction, not a compromise

> **RENUMBERED 2026-08-02, was R2-044.** See the note at R2-051.

**Fixed.** `anim/build_camera_rig.py`. This is R2-037, and the diagnosis in
R2-037 was half right: it saw that static geometry got 6.5x less blur than the
camera's own motion warranted and concluded that a single shutter could not
serve two clocks. There is only one clock.

    scene.render.motion_blur_shutter = a.shutter * scales[f - 1]

Cycles integrates motion blur over `shutter` FILM frames by evaluating the
depsgraph at sub-frame FILM times, and everything in this film is keyed on film
frames sampled through `filmtime.world_time_table`. **The slowdown is already in
the animation.** During beat 3 one film frame spans 1/24 * 0.15372 = 1/156 s of
world time, so a 180-degree shutter is 1/312 s of world time — exactly what a
156 fps high-speed camera with a 180-degree shutter records, which is what real
slow motion is. Scaling the shutter by the same factor applies it twice. The
6.5x in R2-037 is 1 / 0.15372, the ramp's own floor, seen from the other side.
`PLAN-scope-optimisation.md` sec 11.7 suspected this and could not verify it.

**THE DECISION: a constant 180 degrees, first frame to last.** Not a compromise
between two clocks, and not animated:

  * it cannot read as a cut, a stutter or a pulse, because it does not change.
    The fix REMOVES the animation rather than smoothing it.
  * it does not move the exposure — Cycles normalises the motion-blur integral,
    so `motion_blur_shutter` sets blur LENGTH, not how much light lands. It does
    not interact with R2-052 (the exposure).

`--shutter-mode {flat,world}` exists so the two can be rendered against each
other. `flat` is the default and `world` is not a supported way to render.

**Measured, A/B on the 5090** (`render/shutter_ab/`, 1280x720 / 128 samples,
identical scenes but for the shutter). High-frequency energy = mean |Laplacian|;
higher means sharper:

| frame | world_time_scale | HF flat | HF ramped | ratio | mean abs diff |
|---|---:|---:|---:|---:|---:|
| 870 (beat 3) | 0.154 | 0.005486 | 0.010561 | **1.925** | 0.008311 |
| 890 (beat 3) | 0.154 | 0.005095 | 0.008671 | **1.702** | 0.007214 |
| 960 (beat 3) | 0.154 | 0.001690 | 0.001845 | 1.092 | 0.000510 |
| **1400 (beat 5)** | **1.000** | 0.001575 | 0.001576 | **1.0004** | **0.000090** |

Frame 1400 is the NEGATIVE CONTROL: outside the ramp the two builds are
identical to 9e-5 mean and 0.0039 max, so every difference above is the ramp and
nothing else. The picture agrees: at frame 870 the ramped build renders the
glass wall's mullions razor-sharp while the camera flies past them, and the flat
build streaks them; the car proxy is unchanged between the two, because the
camera is tracking it. **The world gets its blur back and the car does not
smear** — the trade-off R2-037 described does not exist.

**The HERO set, RE-DERIVED against the decision.** `tools/screen_presence.py`
re-run on the NEW camera path in both shutter modes, so the shutter effect and
the camera fix are separable:

| run | HERO | MID | BULK |
|---|---:|---:|---:|
| shipped baseline (old camera, ramped shutter) | 91 | 55 | 289 |
| new camera, ramped shutter | 90 | 57 | 288 |
| **new camera, flat 180 degrees — SHIPS** | **75** | **63** | **297** |

**Nothing entered HERO. Every move is a demotion.** 15 items left HERO on the
shutter — `access_road_gully`, `access_road_slab`, `apron_wall_panel`,
`big_screen_tower`, `cable_reel_drum`, `catering_counter`,
`grass_clump_tussock`, `pit_exit_portal_frame`, `planter_shrub`,
`power_distribution_board`, `puddle`, `spectator_standing_at_rail`,
`spectator_standing_ga`, `spectator_standing_in_row`, `wheelie_bin` — plus 9
MID->BULK. Exactly one item, `oil_stain`, moved on the CAMERA fix (26 -> 23
frames against a 24-frame threshold). Agents per round 178 -> **169**.

Controls on that re-derivation: the two runs are bit-identical on every array
that does not depend on the shutter; the sharp/unoccluded flags differ on **0**
frames outside 865-1055 and on 178 of the 191 frames inside it; and a
flat-vs-flat run across the camera change differs on 815 frames outside the
ramp, which proves the zero is a real result and not a broken comparison.

**Found, not fixed.** `tools/build_and_dump_points.py` — the tool the next world
rebuild will use — records all 34 vegetation scatter hosts (bbox diagonals
1,460-3,408 m) as single points at the world origin, 5.7 m from the beat-1 lens.
That is the "phantom bramble inside the showroom" failure `dump_world_points.py`
already warns about in its own docstring. The tiering above was run on
`dump_world_points.py`'s cloud instead, and still measures `assembly2.blend`, so
it must be re-run after #53's rebuild.


## R2-045 — the transit drove the CHORD of its own merge arc, 9.044 m off the road

Decided in `docs/R2-042-DECISION.md`, implemented here. The contract's
`access_route_point` merged onto the pit straight on the declared **R150 / 40 deg**
arc; `tools/build_telemetry.py` built the same merge out of the same
`SPEC["transit"]["legs"]` block by linearly interpolating the four leg endpoints —
the arc's **chord**. A 104.72 m arc of R150 stands `150*(1-cos 20 deg)` = **9.046 m**
off its own chord, and the chord is on the outboard side, so the car in
telemetry.csv drove up to **9.0407 m to the left of the road every other module
built**, its swept box **4.643 m outboard of the ribbon's own painted edge**, for
60.1 m of Beat 4, at 200+ km/h, on camera.

**The file forbade this in its own header.** Lines 30-34 already said geometry is
evaluated ANALYTICALLY from the spec's elements, and named the harm: *"integrating
speed along chords would accumulate that error into the lap time and hence into the
audio sync."* The lap obeyed it. The transit did not, for the whole project.

### What was wrong is not only where the car was

`cum` was built from `length_m` — ARC lengths — while `tx`/`ty` interpolated along
CHORDS, so the car advanced 104.700 m of arc-length `s` along a 102.607 m path.
That is not a position error with a speed error beside it; it is one error, and it
is measurable in the artefact:

| over the merge (leg 2), 52 frames | before | after |
|---|---:|---:|
| ground path actually driven | 101.011 m | **103.090 m** (+2.079) |
| true ground speed vs the `speed_ms` column | **-2.078 %** | -0.098 % |
| worst `|v_world - speed_ms|` | **1.2407 m/s** | 0.1426 m/s |

Read the middle row carefully, because the obvious reading of it is wrong.
`audio/scene.py` derives `v_world` from `x, y, z` (R2-026 forced that), so the
ENGINE was consistent with the PICTURE and 2.078 % under the declared column. What
was inconsistent with both is **`wheel_rot_rad`**: it is `s_m / 0.36`, so the
wheels rolled off 104.700 m of arc over 102.607 m of ground — **2.04 % of
un-sanctioned wheelspin for 52 consecutive frames**, in the file whose ROLLING
CONTACT section promises exactly one exception, ten frames long, at the launch.
`tools/wheel_rotation_gate.py` cannot see it: it reconciles the rotation against
`s_m`, which is the number that was lying. After the fix the declared speed, the
driven ground and the wheels agree to 0.098 %.

### The fix

`transit_path()` in `tools/build_telemetry.py` evaluates the four legs as the
elements they declare. **It imports `world_contract` and uses `access_route_arrays`
for the apron and the merge** rather than reimplementing the arc. The alternative
— duplicating the evaluation and asserting the copy agrees — was rejected: a true
shared helper is impossible under the contract's RULE 2 (it may not import from
`tools/`), and of the two remaining options only the import makes agreement
STRUCTURAL. `world_contract` reads nothing but json/math/os/sys/numpy and never
reads telemetry.csv at import, so there is no cycle, and RULE 2 constrains what the
contract imports, not what imports the contract. The import is deliberately
unguarded: a `try/except` fallback to the old chord is exactly the
silent-plausible-data failure `elevation()` was rewritten to refuse.

Each leg is parameterised by ITS OWN FRACTION, not by a global station. The spec
rounds the merge to 104.700 m where R150 x 40 deg is 104.7198, and a global-station
mapping would spend that 19.8 mm as a step at the leg node and hand it to every leg
after it. The cost is a 0.019 % scale on leg 2; the alternative was a 20 mm jump.

**Leg 3 is not the spec's chord either, and that is the second half of the fix.**
The arc exits 5.023 m LEFT of the pit-straight centreline (contract
`ACCESS_MERGE_LATERAL` = 5.02; measured here at lap u = +5.0219 against a
`half_width` of 8.0, i.e. the car is already on the racing surface and has 215.6 m
of it to converge across). The spec's leg-3 chord spends that 5.02 m linearly,
which meets the merge at an **18.67 deg kink** and the START/FINISH LINE at a
**1.33 deg** one. Leg 3 is now the pit straight entered tangent, with the offset
decaying on a quintic ease: zero slope AND zero curvature at both ends, so the car
leaves the arc tangent and crosses the line both tangent and straight, and it never
departs the spec's own chord by more than **0.7405 m**. Worst yaw step in the
transit: **16.209 deg/frame -> 0.9646**.

The cubic smoothstep was tried first and REJECTED on a measurement: its curvature
is non-zero at the ends, so the car was still turning as it crossed the line and
`accel_lat_ms2` stepped **4.034 -> 0.000 m/s^2** with 0.126 deg of roll, in one
frame, at a beat boundary — a discontinuity introduced BY the fix. The quintic
ends flat and its peak curvature is lower (5.774 against 6.000), so it cost
nothing: the seam now steps **0.590 -> 0.000 m/s^2** and 0.018 deg of roll.

### The heading column was zeros, and the curvature column with it

`fh = np.zeros_like(ts)` for every transit frame. The car pointed due EAST through
a 40 deg merge and then snapped **40.0000 deg in one frame** at the start/finish
line — at 288 km/h, in a film whose one law is that there are no discontinuities.
`audio/scene.py:183` places the exhaust and its directivity off that column;
`tools/author_beats2_5.py:760` builds the car's oriented box for camera clearance
off it. Both were reading a lie. `transit_path` returns the analytic heading and it
is written; the seam is now **0.00206 deg**, against the 0.09786 deg the 16 frames
either side already carry. `curvature`, `accel_lat_ms2`, `steer_norm` and
`roll_rad` were zero over the merge for the same reason and are now real: 1/150,
**24.33 m/s^2 (2.48 g)**, 0.0187, 0.757 deg of body roll.

### What did NOT change, measured rather than assumed

`t_s`, `s_m`, `speed_ms`, `speed_kph`, `accel_long_ms2`, `wheel_rot_rad`,
`pitch_rad`, `wheelspin` and `z` are **bit-identical**, all 1743 frames, and so is
every lap frame's x and y (max delta exactly 0.0 over 1524 frames). The transit's
speed profile is integrated from `length_m` alone and never touched the positions,
so nothing in the time domain moves: lap 63.527 s, transit 9.103 s, total
72.583333 s, 1743 frames, and the film's 2978 frames and 124.0833 s stand.
**R2-042-DECISION 5.1's "transit distance shortens by ~2.09 m ... speed and
per-frame timing change" is wrong in both halves**: the declared distance is held
and the DRIVEN path lengthens by 2.079 m to meet it, and no clock moves.
`anim/filmtime.py` needs no edit — `GLASS_WORLD_T` re-measures at 1.928154 against
its declared 1.92815, because legs 0 and 1 are bit-identical.

### The instrument

`tools/transit_line_gate.py`, 15 checks, and it is built on the assumption that
the check might be the broken thing:

* the agreement test is made TWICE, the second time against an arc reconstructed
  from `circuit_spec.json` ALONE — the unique circle leaving leg 1 tangentially
  through leg 2's far endpoint, **R = 150.0160 m over 39.9958 deg** against the
  contract's 150/40, agreeing with the driven line to **3.8 mm**. It is asserted to
  differ from the contract's R, because an exact match would mean it had cheated.
* POSITIVE CONTROL: the pre-fix file is kept at `telemetry/pre_R2042.csv` and must
  fail the test by the sagitta. It reads **9.0407 m against a predicted 9.0461**.
* a synthetic 0.20 m lateral push must fail (reads 0.200059 — the CSV's own 4-dp
  quantum is 5e-5 m, which is why the tolerance is 1.5e-4 and not float epsilon).
* NEGATIVE CONTROL: 400 m off must read 400 m, and the far field must stay
  buildable.

Contract selftest **[18] is INVERTED** in the same change — it asserted that the
chord polyline reproduced telemetry.csv to 1.0e-4 m, which was TRUE and is now
false by 9.0407 m. Re-run against `pre_R2042.csv` through a symlinked root, the
inverted check fails by 9.04 m and reports the chord at **0.0001 m** — the old
assertion's own number, reproduced from the other side. 149 checks, 0 failed.

### Blast radius, measured

* `world/build_barriers.py` S21's +8.95 m correction table is **now a no-op**:
  max wall push **+3.347 m over 32.4 m of the north corridor wall -> 0.000 m**,
  both sides. Its own note says "Delete this the day the telemetry and
  `access_route_point` agree." That day is today. NOT DELETED HERE — `world/build_*`
  belongs to the rebuild agent, which is mid-render off that file. **Until it is
  deleted and barriers rebuilt, the Beat-4 corridor's north wall stands up to
  3.35 m further out than the contract declares, in the shot the camera flies.**
* `transit_keepout` is left as the UNION of the ribbon and the old chord. It is
  conservative and costs nothing. It covers 93.0 % of the driven transit frames;
  the 12 it does not are s 132.4-158.4 m at lap u +5.23..+8.85, where the car is on
  the RACING SURFACE (verge edge 10.50 m) and `in_access_ribbon` excludes its own
  centreline by construction because the track already owns that ground.
* `PIT_WALL_S0` **does not move, and it is no longer luck.** The driven swept box's
  crossing of `PIT_WALL_Y`, measured on the CSV densified 40x the way
  `world/items/pit_wall_unit.py` does it, goes **3446.001 -> 3421.450**; the union
  still takes the ribbon's 3447.709, now by 26.3 m of margin instead of 1.70 m.
  DEFECT #46 stays closed by construction rather than by coincidence.
* **the contract's own PROSE is now stale and only its owner may fix it.** S10c
  lines 2155-2170 still say *"VERIFIED: this polyline reproduces telemetry.csv's
  own x, y to 1.0e-4 m over all 219 transit frames"* and *"It does NOT decide which
  curve is right"*, and the v1.2.0 D1 header block says the same. Both were true
  and are now false by 9.0407 m. `transit_drive_*` is still published and still
  correct as a NAME for the old chord — `transit_keepout` uses it — but a reader
  will take it for where the car is. This change was allowed to touch selftest [18]
  and nothing else in that file, so it is handed over rather than patched: the next
  contract revision should re-word S10c and bump the version.
* the camera: beats 2, 3 and 5 re-author **bit-identically**, beat 4 goes 29 -> 30
  keys and its keys move up to 30.768 m, and the aim gate barely notices — beat 4
  worst aim **10.2518 -> 10.2540 deg** (bound 14.0) — because the anchors are
  derived RELATIVE to the car. Worst position jump 4.2469 m and worst rotation step
  27.438 deg are unchanged to all printed digits. Beat 1 is untouched: aim
  **7.243538695256358 deg**, byte-identical `beat1` block, and the beat-1/beat-2
  seam still measures **2.0893 m, 1.2727 m/s, 13.2504 deg (0.3398 deg/frame),
  -0.051 mm**.


## R2-046 — the car crosses the start/finish line 42.6 km/h faster than it arrives at it

**Found while measuring R2-045's seams. NOT FIXED.** The transit's last frame is
288.16 km/h and the lap's first is 330.80 km/h: **+11.845 m/s in one frame**, which
`np.gradient` renders as 284 m/s^2 of longitudinal acceleration and hands to
`pitch_rad`. It is not the transit's fault — the leg model's declared exit is
`exit_kph` 288.6 (the spec's own "line speed outlap") while the lap solver starts
the flying lap at vmax — and it is not new, but it is a genuine discontinuity at a
beat boundary in a film with no cuts, and the audio's `v_world` sees it. The
position seam is clean (3.6013 m of travel at 86.43 m/s against 79.94 and 91.89
either side) and the heading seam is now clean; only the speed steps.

Fixing it means deciding whether the out-lap ends at the line or a lap-length
earlier, which moves the beat-5 clock, so it is logged rather than taken.


## R2-047 — leg 0's `length_m` is measured from the NOSE and its endpoints from the ORIGIN

`docs/R2-042-DECISION.md` S6 flagged leg 0 as geometrically impossible: `length_m`
**11.980** against endpoints **15.000 m** apart, and an arc can never be shorter
than its own chord. It is not an arc. **It is two datums, and the arithmetic is
exact**: `round2_inventory.md` S2 measures the car body at x **-2.678 .. +3.020**,
and

    15.000 (the glass plane, world x) - 3.020 (the nose, at rest) = 11.980

to three decimals. `length_m` is the distance the car's NOSE travels to reach the
glass; `from_world`/`to_world` are ORIGIN positions. The spec's own note — "the
launch run is 11.98 m from the car's nose at X=+3.02 to the glass at X=+15.00" —
says so, and `build_telemetry`'s transit comment quotes it. **So the field pair is
not describing one object, and neither field is wrong on its own.**

This is the mechanism behind **R2-026** (`x / s_m = 1.25207` through the launch),
which is now explained rather than merely measured: 15.000/11.980 = 1.2520868.
The car's ORIGIN covers 15.000 m while `s_m`, `speed_ms` and `wheel_rot_rad` count
11.980, so the body runs **up to 13 % faster than the declared speed** and the
wheels under-rotate against the ground they cover, for 47 frames.

**NOT FIXED, DELIBERATELY.** Correcting the geometry alone (driving 11.98 m of
world X) would leave the car 3.02 m short of the glass; correcting the length alone
(15.0 m at the declared 1.78 s) moves the breach frame and with it Beat 3's ramp,
`filmtime.GLASS_WORLD_T`, and the 124.0833 s master. The honest fix is to declare
which datum each field uses and re-derive both together, with the breach frame
pinned. R2-045 left leg 0 bit-identical for exactly that reason.


## R2-048 — the doppler gate's correlation was measuring the tracker's luck

**Found by rebuilding the audio master for R2-045.** Four of five gates passed;
`doppler` failed on one line: `corr_measured_ratio_vs_predicted_ratio`
**0.93149 -> 0.83669** against a `> 0.90` threshold. Everything else in that gate
moved the RIGHT way — median error 5.129 -> 5.117 cents, **p90 61.12 -> 30.27**.

### It is not the film, and that took a whole control master to prove

The pass is at film frame 2271, in beat 5, where the car's telemetry, the camera
path (measured: **0.000000 m** of movement over frames 2190-2310) and therefore
the entire predicted Doppler are bit-identical before and after R2-045 — the
retarded-solve figures in the report are identical to six digits. Two hypotheses
were tested and one survived:

* **a global gain change** (the master's program gain and limiter do move,
  because beat 4 got louder). REFUTED BY ITS OWN CONTROL: the gate was re-run on
  the master scaled by -1.0, -0.2, +0.05 and +0.2 dB and returned **the identical
  correlation to five decimals** every time. The comb search is gain-invariant.
* **engine phase.** The engine is synthesised as a phase integral of f0, and f0
  comes from `v_world`, which R2-045 legitimately raised by 2.078 % over the
  merge. Every tonal sample AFTER the transit is therefore phase-shifted. MEASURED
  against a control master built from the pre-fix inputs: beat 1 waveform
  correlation **0.999978** and beats 1-3 and 6 differing only by a <0.18 dB gain,
  while beat 5's half-second RMS envelopes still correlate at **0.9988** but its
  waveforms correlate at **0.626**. Same spectrum, same envelope, same Doppler,
  different phase.

That control master — pre-fix telemetry, pre-fix beat sheet, pre-fix camera path,
same code, built in a shadow root so nothing live was touched — reproduces the
shipped baseline **exactly** (0.9314903621211171 against the shipped 0.93149,
median 5.128955, p90 61.11643, 85 windows). It is a faithful A/B, and it says the
0.09 is mine.

### What the 0.09 actually is

Five of 83 windows are comb-search failures, and they are not near misses. Their
measured/predicted ratios are **0.4853** (the sub-octave) and **0.7536, 0.7575,
0.7593, 0.7595** (the 4th harmonic read as the 3rd) — 480 to 1252 cents out, on a
distribution whose 90th percentile is 30 cents. The control master has **four**
such windows. One extra tracker slip is the entire difference between 0.93149 and
0.83669. Excluding them, the correlation is **0.99800** on the new master and
**0.99610** on the old one.

### The fix is to the instrument, and it is gated harder than before

`audio/verify.py`: `TRACK_MAX_CENTS = 200` splits locked windows from comb
failures — a whole tone, 8x the worst genuine error either master shows and under
half the smallest possible comb slip, so it is not a borderline call. The raw
correlation is **still reported unchanged**; the PASS now needs the correlation on
tracked windows > 0.90, the failure FRACTION <= 0.15, p90 < 150 cents (new),
median < 100 cents (as before) and the sweep agreement (as before).

Controls, all run:

| case | robust corr | fail frac | median | p90 | verdict |
|---|---:|---:|---:|---:|---|
| the master as shipped | +0.99800 | 6.0 % | 5.12 c | 30.27 c | PASS |
| the pre-R2045 control master | +0.99610 | 4.7 % | 5.13 c | 61.12 c | PASS |
| POSITIVE: pass window time-reversed | +0.95324 | **79.8 %** | 519 c | 951 c | **FAIL** |
| POSITIVE: pass window lifted from 60 s | +0.97189 | **62.5 %** | 354 c | 831 c | **FAIL** |
| POSITIVE: windows randomly permuted (in-gate, seeded) | **-0.17** | — | — | — | **FAIL** |

**Read the third and fourth rows carefully: the robust correlation ALONE passes
both broken files.** The teeth are the failure fraction and the two error
percentiles, which is why all three are in the criterion and why the cap is stated
against measured numbers (2.5x the worst real run, 4x under the mildest broken
one) rather than chosen. The gate now passes both real masters and fails four
independently broken ones.

### The rest of the audio, for the record

`levels` -14.02 LUFS / -1.105 dBTP / 0 clipped / 0 silent windows, `pitch`
firing correlation and its chirp control unchanged, `external_assets` clean, and
**`seam` IMPROVED: worst beat-boundary d3 percentile 91.029 -> 88.487** — R2-045
took a 40 deg yaw snap and an 18.67 deg kink out of the picture, and the sound got
smoother at the boundaries with it. `master_report.telemetry_r2026`'s own
diagnostic of the x-vs-s_m disagreement past the launch also halves:
**p99 0.02122 -> 0.00946**. Its `global_ratio` gets WORSE (1.000321 -> 1.000856)
and that is honest: the leg-2 chord deficit was partly cancelling leg 0's nose-datum
excess (R2-047), and removing one exposes the other.

---

## R2-058 — the Wave wavelength factor was 3.18× wrong, and the right value was in a comment three lines away

`itemkit._tex_wavelength_m()` returned `1.0 / Scale` for `ShaderNodeTexWave`. The true
value is **`2π/20 = 0.3141593 / Scale`** — Wave is **3.183× finer** than itemkit assumed.

Measured by two probes that import neither itemkit nor any factor: an 8192 px orthographic
emission render read by sub-bin least-squares sinusoid fit, and a 2048² radially-averaged
2-D power spectrum. Over a 46× sweep (Scale 5…230) every point returns 0.31416 — **mean
0.3141596, sd 3.2e-09**. Both probes carry a calibration case built from Math nodes that
shares no assumption with the thing measured, recovered to 0.00–0.12 %.

**itemkit's own header already quoted 0.31416.** It used the closed-form Wave as the
*control* for its noise measurement. The correct number sat three lines from the wrong code.

**And the selftest could not see it, because it round-tripped against the same constant.**
That is how this survived the frequency API (R2-... the `wavelength_m` work), the relief
law, and a fourteen-module rebuild. Replaced with `emitted_wavelength_m()`, which renders
a texture through an ortho camera and **counts bands** — an independent measurement, not an
algebraic identity. Its positive control reverts the constant to 1.0 and the check fails,
exit 1, while the calibration row still passes: the constant broke, not the instrument.

**Also found: Blender's DIAGONAL sums components and multiplies by 10, not 20** — a second
factor (`2π/(10√3)` band-normal), affecting seven built modules. Its selftest discriminates
on a *relation* (the ratio must be √3; a BANDS reading gives exactly 2.0000) rather than on
another repeated constant.

**Blast radius:** 55 Wave-driven stages moved, ×1.002 to ×3.183 (median ×3.038), and **35 of
55 changed band**. Seven fell out of every band; one entered from none; nine now sit at
8.3–9.04, **pinned at the terminator** — `m` cannot exceed `2/tan(12.47°) = 9.043` at this
sun. **None of the nine declared wavelengths was compensating for the error; seven were
propagating it.** Corrected as itemkit plus call sites in one pass, pixel-neutral by
construction (`relief_amplitude_for(m_new, λ_new)` equals the old pair to 1e-16) — and that
arithmetic was checked against a third thing neither number came from: opening the shipped
blends and confirming the derived `Distance` **is the float already on the socket, 7 of 7**,
with a negative control where the naive fix lands on 0 of 7.

`build_dressing`, `armco_w_beam`, `crew_fireproof_overall` and `pit_wall_unit` had each
independently hardcoded `(2π/20)` as a private workaround — a 3rd, 4th and 5th copy. All
converged onto `K.WAVE_WAVELENGTH_FACTOR`.

**Noise 1.60 and Voronoi 2.17 were confirmed and left alone.** Three estimators bracket
Noise at 1.53–2.12 and Voronoi at 2.30–2.53, and the factor moves with `detail`. The
Voronoi *peak* estimator is **disqualified by its own control** — it drifts 5.1 → 47.2 with
Scale, so it is not measuring a factor. A fourth significant figure would be a guess.

## R2-059 — `contract_sun()` set the refuted exposure, and the one caller that checked was accidentally immune

`itemkit.contract_sun()` set `C.REFERENCE_EXPOSURE_EXTERIOR = −3.048` — the **derived and
refuted** value, 0.586 stops over. The measured value is `film_exposure.FILM_EXPOSURE =
−3.628`, correct to 0.006 stops against an 18 % card with two view transforms agreeing to
0.0141 stops.

**This is the shared helper.** It exists precisely so nobody quotes the light independently,
so every item agent that called it and trusted it judged **0.58 stops over** — consistent
with the separate finding that *every item test frame ever judged* is 0.580 stops over,
including the crew macro that passed 8/8 and the frames the human-figure brief was written
from.

It stayed invisible for a pointed reason: the one caller that verified its own exposure —
the breach sim's `witness.py` — **overwrites it after the call**, so the only agent
positioned to notice was accidentally immune.

Now imports `FILM_EXPOSURE` (never spells the number), **asserts** the readback, and refuses
if the measured and refuted constants ever become equal. Its selftest reads the **live
scene**, not the constant.

**Found while landing that positive control:** `blender -b -P world/itemkit.py -- --selftest`
**exited 0 on an uncaught exception** — the assertion fired, the selftest never reached its
verdict, and the shell saw success. Now wrapped in `gate_exit.guard`; verified pass → 0,
reverted-exposure → 2, reverted-wave-factor → 1.

Four live setters of −3.048 remain outside itemkit: `build_sky.py:1442, 1768` (plus its own
re-declaration at :149), `build_barriers.py:4567`, `build_surface.py:3682`, and
`world_contract.py:3463`.

## R2-060 — a flat quad outscores real 2 mm ribs, so the relief check cannot tell paint from geometry

Exposed while rebuilding the relief positive control after R2-058 (its decoy had been
emitting **9.42 mm stripes against 30 mm ribs**, 3.18× too fine — its own comment recorded
the symptom and misdiagnosed the cause).

**A four-vertex quad with z ≡ 0 — no modifiers, no displacement, no normal map, verified in
the blend — scores dip 0.6308 against real 2 mm trapezoidal ribs at 0.6082.**

The shipped decoy passed only by luck: its stripes run along object X while `plate()` lays
the ribs on the sun's ground direction, **32° apart**, and that misalignment splits the
band-passed response near-equally between the along- and across-light terms, which cancel.
Structure tensor confirms it — rotated decoy −39.15°, ribs −39.68°, shipped decoy −0.03°.
Device confound closed: the shipped decoy re-rendered on CPU gives the same 0.0231, so
0.0231 → 0.6308 is **orientation alone**.

**Mechanism:** after the DoG band-pass, a sharp albedo *step* and a lip-and-shadow leave the
same bipolar pair at the same ~2r spacing.

**The FAILs stand; the PASSES were at risk.** The error is over-detection, and passing
requires `subject_dip ≥ control_dip + 0.03`, so inflation can only manufacture false
**passes**. The in-frame controls are untextured plain-grey primitives with no painted
anisotropy to inflate, closing the false-FAIL route.

**All eight relief passes were then re-examined** with a five-arm staged experiment sharing
**one pixel mask computed from the shipped frame**, so no arm could move the goalposts
(silhouette IoU 0.9994; CPU vs GPU ±0.0003). **Six are REAL. Not one was manufactured by
paint.** `crew_figure` — the ITEM_ACCEPTED 8/8 pit crew — is the best-supported: with all
paint forced flat it keeps 2.3× its own bar, the mesh alone scores *higher* than the shipped
figure, and a render-free census finds one ≥20° crease every 5.1 px at a 2 px band radius.
Two were inconclusive. **Five of the six real passes are also inflated by paint** — verdicts
safe, numbers not clean. **`pit_wall_unit`'s relief is entirely shader bump, not mesh** (one
crease every 68 px), predicted in advance by the render-free census.

### The repair, and a correction to the proposed mechanism

The first proposal was to gate on the two-light **correlation**. **It does not survive its
own controls** — real 3 mm bolt heads read +0.1003 and a plain grey plate −0.8608, because
real relief carries a light-*invariant* component (a rib's flat top is bright from either
side). A statistic that puts a smooth cylinder (+0.9193) and a painted one (+0.8629) in the
same bin cannot decide. **`rho` is measured and reported, not gated.**

The lever is **amplitude, not correlation**. Check 6 is now a three-clause conjunction:
`dip` ∧ `fine_over_control ≥ 2.00` ∧ **`light_over_control ≥ 2.00`** — render both staged
sun sides, band-pass **log** luminance (paint on curvature leaks 40.9× more in linear),
split the fine band into the half that moved with the sun and the half that did not, and
compare the moved half to the same luminance-matched in-frame control.

**Truth table, 15 panels: dip alone 9/15, combined 14/15. Paint 7/7 rejected, smooth 3/3
rejected.** The decisive row is a painted sphere — dip 0.6252 defeats the old check,
`fine_over_control` **25.45× defeats check 5 twelvefold**, and only the light clause rejects
it. The single miss, `e_bolts_3mm`, **also fails `fine_over_control` at 1.34×**, so the new
clause is never the deciding vote: no relief panel is lost that check 5 was not already
losing.

**Two limits, printed on every run rather than tuned around.** At a true 180° sun reversal a
painted cylinder reaches **2.05 against the 2.00 bar** — a geometry the gate cannot stage,
since both its candidates are side-lights ±70° off the camera axis; raising the bar to 3.00
would reject real 8 mm ribs at 2.83. And `heras_fence_panel`'s in-frame control remains
degenerate, so it passes on the absolute floor alone.

**Consequence:** a missing flip frame now makes check 6 **NOT MEASURED** rather than a
silent pass, so **every existing `gate.json` is stale** until re-run. And
**`catch_fence_post` cannot be measured at all** — its witness frame is **66 % crushed to
black** and the analyser rejects it as unfit, confirmed identical at committed HEAD, so one
of the eight passes currently has no supporting measurement in either direction.

## R2-061 — the film camera shipped with Blender's 1 km factory far clip

`anim/build_camera_rig.py` created the camera datablock and never touched
`clip_start` / `clip_end`, so every rig carried the factory `0.1 m / 1000 m`.

Beat 6 is the closing wide. It sees terrain **past 1 km**, and everything beyond the
far plane is not drawn — **56 full-width rows of literal black across the top of the
frame**, which reads as a letterbox bar rather than as a clipped horizon, which is
exactly why it survived being looked at.

**The instructive part is not the defect, it is that it was fixed twice.** It was
found once and corrected *in a built blend*, and the built blend is a build artefact:
every subsequent rig rebuild reintroduced it, silently, because the source that
generates the camera still had no opinion about clipping. **A fix applied to an
artefact rather than to the thing that generates the artefact is not a fix, it is a
manual step nobody wrote down.**

Fixed at source:

```python
cam_data.clip_start = 0.05      # the camera passes within centimetres at the breach
cam_data.clip_end   = 200000.0  # beat 6 sees the far terrain ring
```

`0.05` is not cosmetic either — at the breach the lens passes within centimetres of
the glass, and the factory `0.1` would clip the wall the shot is about.

## R2-062 — beat 1's tour was ordered by ASSEMBLY, not by SPACE, so the camera had to sprint

`present_order()` in `tools/build_beatsheet.py` used the **seat order** as its spine,
on the stated argument that assembly order is "roughly centre-outward".

**Seat order is centre-outward in assembly. It is not centre-outward in space.** Its
9th, 10th and 11th entries are NOSE (x = +3.75), FW (x = +4.38), RW (x = −4.59) — and
every cluster was given the same 1.76 s slot regardless of how far apart they sat. The
camera was therefore *required* to cross **9.14 m in one slot**: the f387–416 dash, at
**7.817 m/s in a beat whose design speed is 1.994 m/s**, with 67 frames (8.5 %) over
twice that.

**Why every gate passed it, and this is the finding worth keeping:**

> **The rig's aim gate scored it 7.24°, a pass. A camera can be pointed exactly at its
> subject and still be moving far too fast to photograph it.** Aim error and
> photographability are independent, and only one of them was being measured.

**Fixed** by solving the visiting order (exact Held-Karp over 11 nodes) subject to each
cluster being presented before it starts *flying* — not merely before it lands, since a
station is solved against the cluster's **exploded** centre — and by allocating time to
whichever constraint binds: dwell, transit at the peak-speed limit, or the turn at the
pan limit. Solved times are quantised to frames because the rig quantises them anyway.

| beat 1, f1–792 | before | after |
|---|---|---|
| max speed | 7.817 m/s | **3.897 m/s** |
| frames over 2× design speed | 67 (8.5 %) | **0** |
| max rotation | 23.42 % width/frame | 16.40 % |
| rig aim gate, worst | 7.24° | **0.00°** |

Two new gates were added that **FAIL the shipped sheet** — predicting 7.06–7.89 m/s on
the dash against 7.82 measured, and 21.1–23.6 % / 18.9–21.1 % on the two pans against
22.8 % and 23.4 % — and pass the new one, with predictions stated as *ranges* so a gate
can never fail inside its own resolution.

**A second-order trap was closed in the same file.** The beat-to-beat carry-forward was
top-level only, so every run silently deleted
`speed_ramps[3_breach].min_world_time_scale_note` — the paragraph another tool wrote
recording that the 0.153719 floor is *solved*. The merge is now recursive, and lists are
walked **only** where their elements carry a unique identity key, so `camera_keys` (22
elements all tagged `1_assembly`) is never zipped by position.

**Still open, and deliberately not fixed here:** f487 remains a 16.4 % WARN — crossing
behind the rear axle, the bisector of the two corner view directions is within 5° of
straight down, so roll must spin through the vertical singularity, and more time barely
helps (49 frames gave 16.4 %, 35 gave 17.3 %). The real fix is a third bridge key at a
wider lens, which is hand-placed geometry and needs a frame to look at.

## R2-063 — beat 6 does not start on a frame, and the rig rounded its keys onto one

The f2643 smear (32 % of frame width, 19.1°/frame) and the f2642–2646 speed swing
(88.3 → 68.5 → 78.0 → 85.3 m/s) were logged as two defects. **They are one.**

**Beat 6 begins at 113.1 s. 113.1 × 24 = 2714.4.** Every declared key in the beat lands
at **.4 of a frame**. `build_camera_rig.py` forced each declared *position* onto
`round(t · FPS)` and called that "reproduced exactly".

At 83.1 m/s, four tenths of a frame is **1.385 m of position error, placed on f2642**.
The camera lurched onto it and then decelerated at **−473 m/s²** to catch up. Because the
camera is only metres from the car it is following, **1.4 m of position error *is* a 19°
per-frame aim swing** — the smear and the swing are the same event measured two ways.

Separately, beat 5's last key and beat 6's peel are **3.6775 m apart across 1.40 frames**
— 63.0 m/s, against a beat-5 arrival of 88.2 and a beat-6 declared 83.1. **About 1.5 m of
the two authored paths simply do not meet.**

**Fixed** by blending the hand-off over 36 frames with the same cubic-Hermite technique
`beat6_path()` already uses, suppressing the rounding inside the window:

```
f2641-2650  before   88.1, 88.3, 68.5, 63.7, 78.0, 85.3, ...   worst |accel| 474 m/s2
f2641-2650  after    88.1, 87.5, 86.4, 85.3, ...               worst |accel|  27 m/s2
max rotation f2636-2660   32.45 %  ->  13.03 %
```

**The blend length was swept, not picked** — 24 frames clears the FAIL but leaves a 14 %
WARN; 36 and 48 are both clean; 36 is the shortest that is clean.

**And the first draft of the fix created a new defect that names the mechanism.** Keying
every frame of the blend starved `look_quat`'s 3°-per-frame roll correction and produced a
**43° tilted horizon** — precisely the defect that function exists to prevent. The blend is
now sampled on a ramp (1, 2, 3, … 8 frames) so the correction always has headroom.
**A dense fix can defeat a corrector by leaving it no room to correct in.**

## R2-070 — R2-057's fix moved the helper's own call sites and missed its two importers

`world/items/gantry_truss.py:3387` and `world/items/pont_girder.py:3051` both did
`g._feed(b, 5, g.bump(...))` on a Principled BSDF. **On 5.2, index 5 is `Thin Wall`.**

Both reach the DSL through `marshal_post_column.NG`. **That class was repaired for R2-057
and its own call sites were moved to `_feed_named` — its two importers were not.**

> **The generalisable shape: fix a shared helper, miss its importers.** The helper's author
> can see every call site *inside* the helper's file. The call sites that matter are the ones
> in files that merely `import` it, and nothing in the fix's own diff points at them.

Verified in the artefacts rather than inferred — `gantry_truss_test.blend` `CTX_Track`, and
`pont_girder_test.blend` `CTX_Track` / `CTX_Deck` / `CTX_Abut`: `Normal` unlinked, the
`ShaderNodeBump` output landing on `Thin Wall`.

**Blast radius measured, not assumed.** All four are opaque (Transmission 0, Subsurface 0,
Alpha 1.0, Coat 0, every one unlinked), so it degenerates to flat rather than flipping the
shell model. That was then *proved* with a five-arm CPU render of the real `_simple_mat`
graph rather than left as an argument from the property values:

| arm | result |
|---|---|
| **NULL** — 7× bump strength on the *broken* wiring | **0 / 147,456 px move** |
| **POS** — 7× bump strength on the *fixed* wiring | 147,456 / 147,456 move |
| **FIX** — broken vs fixed | 147,448 / 147,456 move |
| **INERT** — fixed, plus the same bump *also* on Thin Wall | **0 / 147,456 px move** |

The NULL arm is the defect. The POS arm proves the instrument can see a bump change at all —
without it, NULL is indistinguishable from a blind test. **The INERT arm is what licenses the
word "flat" over "shell flip"**: driving Thin Wall on top of correct wiring moves nothing, so
the stray link is inert here and not merely invisible.

Both sites are in `test_scene()`, not `build()`, so **nothing in assembly6/7 moves**. What was
wrong is the ground lighting these two items in the frames they were *accepted* in — and both
are on the relief PASSING list, so those verdicts were read from frames lit by a flat context.

**The audit tool already existed and had never been run over anything.** Its detection was
fine; its scope was **49 of 142 files**, with `tools/`, `anim/` and `sim/` entirely unswept.
Now every source directory, with no flag able to turn one off, plus a second **artefact** arm
(`--blend`) — because AST cannot see the 997 computed indices, post-assembly mutation, or a
module nobody pointed it at.

**Every other index site in the tree was verdicted against a live 5.2 socket table and is
correct**: `build_barriers` ×45, the `Principled[14/15/16/20/21]` specular/coat family, 13
sites that moved (`TexNoise[8]`, `Clamp[1/2]`, `CollectionInfo[1/2]`), and the uninferred-type
hits. Five `pin(bs, 6, …)` sites are correct *today* but were converted to `pin_named` anyway
because `pit_wall_unit_itemkit` **is the reference item every campaign agent copies from** —
it was the house style for `Normal`. Six sites in the `humankit`/`itemkit` selftests must stay
by index because they **are** the R2-038 positive controls; waived with the reason printed.

**The guard's own controls include one that matters more than the pass/fail pair.** Alongside
a positive (bump → `inputs[5]`, fires on 'Thin Wall') and a negative (the same graph, one link
moved to the name), there is an **idiom control**: `armco_w_beam`'s real Bevel-dotted-with-
geometry-normal edge-wear mask. **The first version of the guard failed that idiom — which is
exactly how a guard gets switched off.** The sink now decides severity and the idiom is a NOTE.

## R2-071 — both film scenes were built from the broken world AFTER the fixed one existed

`assembly7` was built at **04:45**. `film9.blend` was built at **11:39** and `film10.blend` at
**17:15**. Both fail the socket audit with **exactly the nine `DR_*` materials** that
distinguish assembly6 from assembly7 — `Height` constant 1.0, the height texture in
`Filter Width`, the bump output on `Thin Wall`.

**`tools/build_film_scene.py` builds from `assembly6`.**

> **Promoting a world as a decision is not the same as the builder consuming it.** The decision
> was made, evidenced and correct — regenerated from source, 0 of 28,781 objects differing,
> the fix durable via `_feed_named`. None of that reaches a frame while the film builder still
> names the old assembly.

Found by a **third party reading the finished artefact**, by graph inspection rather than the
vertex/pixel A/B that established the assembly6-vs-7 difference in the first place. Two
independent instruments landing on the same nine material names is what makes this settled.

**Total: 20 broken material instances across 5 built artefacts** — 7 repaired by two source
lines, 4 needing only a rebuild, 9 needing the films rebuilt from assembly7.

`marshal_post_column_test.blend` is the same story one level down: its source was fixed by
R2-057 and **the blend was built nine hours before the fix** and never rebuilt.

**The rule this earns:** a source fix has a build artefact downstream of it, and the fix is not
landed until that artefact has been rebuilt *and re-read*. Keep a list of what a fix
invalidates, or a guard that reads artefacts will keep finding fixes that were made months ago
and never arrived.

## R2-064 — the beat 1→2 seam had 39 frames of nothing in it, and an anchor could never have fixed it

The seam is specified at **1.2727 m/s**, and beat 2's second key sits 0.78 m from its first
two frames later — **9.4 m/s**. Between them lay a 39-frame chord with no keys at all, so
Blender's `AUTO_CLAMPED` handle at f793 was computed from a 39-frame neighbour on one side and
a 2-frame neighbour on the other. Result: **11.3447 m/s at f795**, 14.3 % faster than the
fastest authored pair anywhere in the film.

**The recommended fix was an anchor at t≈32.6 in `tools/author_beats2_5.py`, and it cannot
work.** Beat 2's emission window starts at f793 (`f0 = round(33.0·24)+1`), so **an anchor
placed before that window emits no key and controls nothing.** The recommendation was carried
forward twice — by the agent that diagnosed the seam and by me when I relayed it — and neither
of us checked that the file it named could act at the time it named.

> **The fix has to put keys in the hole.** A curve with no keys across 39 frames is not
> under-specified by a little; it is being authored entirely by a handle solver.

Both seam keys are now transcribed anchors of the same spline, the hole is emitted from that
spline on a spacing ramping `1,2,3,4,5,7,5,4,3,2,1`, and the t=33.70 arrival station is deleted
— it sat 1.0 m from the ignition station 9 frames later and forced 5.67 m of descent into 16
frames.

| `tools/seam_gate.py`, f738–832 | before | after |
|---|---|---|
| peak speed | 11.3447 m/s @f795 | **8.9124 @f804** |
| vs fastest authored pair | +14.3 % | **+0.0 %** |
| worst BULGE | 2.247× (f812–820) | **1.407×** |
| worst \|accel\| | 98.49 m/s² @f794 | **39.66 @f817** |
| verdict | SEAM_DEFECT | **SEAM_OK** |

The four seam invariants are untouched: chord 2.0893 m, speed 1.2727 m/s, look 13.2504°, lens
−0.051 mm. Beat 1 f1–754 is **bit-identical across the bridge insertion** — 0.0000 nm, 0
quaternion, 0 lens — enforced by pinning every beat-1 handle and re-sampling both sides inside
the rig, which refuses to save otherwise.

`seam_gate --selftest` is **7/7**, with three must-fail arms — the shipped pre-fix path judged
against **its own** sheet, beat 3 with an injected overshoot, and a sheet with one key pair
collapsed into a hold the path does not hold — and a census assertion that re-derives
`TOL_BULGE` every run and refuses if 1.570× outside and 2.247× inside stop straddling 1.80.

## R2-065 — beat 2's keys reach backwards into beat 1 through Blender's handle solver

Re-profiling beat 2 moves **f740 by 34.35 mm**, on a segment whose own two keys never change.
`AUTO_CLAMPED` handles are solved from neighbours, so the f718→f754 segment always depends on
what follows f754 — there is no "beat 1 alone" handle value to pin to.

**FOUND, NOT FIXED.** The consequence is operational and must not be forgotten: **beat 1's
frames ~686–753 must be re-rendered whenever beat 2's keys move**, even though beat 1 was not
edited and its keys are provably identical.

Attributed three ways before being written down — and the first attribution was wrong. A source
comment blaming `FCurve.update()` was written *before* it was tested; running `update()` on the
pre-fix rig moves f1–754 by **0.000000 mm**. The comment was corrected. **Writing the cause into
a comment before measuring it is how a wrong explanation acquires a citation.**

## R2-066 — the lens passed 2 mm from a plaque and blew frame 808 white

**Frame 808 of the shipped beat 2 is a grey-white wash over ~60 % of the picture.** Mean
luminance **0.5743** against 0.4722 and 0.4637 either side — one frame, **21.6 % brighter than
both neighbours**.

The beat-2 arrival station put the lens **2 mm** from `Plaque_Surround`. The surface is *behind
the lens at the key*, which is why every geometric check passed it — but at a **180° shutter
the camera sweeps past it during the exposure**, and the plaque crosses the sensor. Clearance
is now 130 mm.

**Found by looking at a picture.** No gate on this project was measuring near-clearance across
the shutter interval, and a still at the key would have shown nothing wrong.

**Fixed as a side-effect of a pacing change — which is luck, not design.** The station was
deleted for its 5.67 m descent, and the clearance came with it. `tools/cam_clearance.py` now
exists so the next one is caught deliberately.

`continuity_gate` on 85 rendered frames: **BEFORE FAIL with 3 FAIL-class** (D1_pop f808,
D4_seam f809, D6_stepped f809–816, plus D5_kink at f794/795/799 — exactly where the geometry
gate put the spike). **AFTER PASS, 0 FAIL-class.**

## R2-067 — beat 2 measured clean, and the 2.04 % wheelspin figure belonged to another beat

Recorded as a result rather than a defect, because `tools/beat2_probe.py` and
`tools/dump_exposure.py` cite it in their docstrings — **and a docstring citing a defect number
that does not exist is its own defect on this project.**

- Wheelspin **f818–827, exactly 10 frames, 1.4547 rev** — sanctioned, and present.
- **Zero phantom slip in the other 2,967 frames.** The 2.04 % figure that has been circulating
  was **beat 4's leg 2**, fixed under R2-045; it was never beat 2's.
- Exposure span across the beat: **0.000e+00 stops.** With `INTERIOR_STOPS = 0.0` the iris does
  not move, which is what a cut-free take requires.

## R2-068 — the continuity gate's image-motion estimate is blind on a tracking shot

`continuity_gate`'s whole-frame phase correlation reports **0.29 px/frame** on a shot whose
background moves **−24 px** and whose car moves **+36 px**. A whole-frame estimate averages two
halves moving in opposite directions and returns approximately zero — the one situation a
tracking shot is *always* in.

**D5, D7 and the pacing "translation" figure are all downstream of it.**

The finding that makes this publishable rather than merely embarrassing is the author's own
limit on their result:

> **Its PASS on my sequence is not evidence about the camera kink.** The A/B is — because
> D1/D4/D6 do not use that estimate.

`tools/frame_motion.py` now **refuses** rather than returning a number it cannot support.
Two further instruments were caught the same way: a `2·acos(|q·q|)` metric reporting 0.069° of
rotation change on frames whose quaternion components are **bit-identical** (it was measuring
float32 normalisation error), and the `FCurve.update()` misattribution recorded under R2-065.

**Three instruments wrong, all three caught by their own author before publishing.** That is
the standard.

## R2-072 — the guard rotted the instant its target was repaired

`socket_index_audit.py --selftest-blend` carried a section headed **"REAL SHIPPED ARTEFACT"**,
pointed at `gantry_truss_test.blend` and `pont_girder_test.blend`, with the reasoning written
into the file: *"if the arm is real, it fails them without being told to."*

That reasoning was sound on the day it was written. **It stopped being true the moment those
two blends were rebuilt** — the same repair this log records under R2-070. The section then
printed `0 stray relief link(s)` under a heading that claims to be proving the arm works, while
**asserting nothing at all**.

> **A control that names a specific broken artefact expires when that artefact is fixed, and it
> expires silently — into a cheerful pass.** The stronger the fix, the deader the control.

**Fixed by generating the control instead of naming one.** Every run now builds
`pont_girder._simple_mat` twice into two saved blends, **differing only in whether the single
`Normal` link is made by integer index 5 or by name**, and hands both to the ordinary `--blend`
path by filename. The positive must fail; the negative must pass. It cannot expire, because its
broken input is manufactured from live source each time rather than found on disk.

Building it caught a second trap immediately: **the first version scanned an empty file**,
because Blender purges a material with no user on save.

**Corpus state after the four rebuilds:** all 32 item test blends **PASS**, with only
`armco_w_beam`'s legitimate edge-wear idiom appearing at NOTE level on two of them. All 21
tracked `*_interface.json` files are **byte-identical** — only the material graph moved.

## R2-073 — 147 setter call sites could silently drop a value, and the static count was wrong

`marshal_post_column._set` and the `_set`/`_link` helpers in `spectator_seated.py` and
`build_architecture.py` **silently discarded the value when the socket name did not resolve**
(`if nm is not None`, `except: pass`). Because they address by name, a socket *insertion* cannot
break them — but a *rename* would make them do nothing, forever, with no artefact signature.
Unlike a dead relief chain, a dropped **scalar** leaves nothing for the artefact arm to find.

**Counted before deciding, because "make it loud" is only safe if the optionality is fake:**

```
static   147 call sites   141 pass ONE name with no fallback
                            6 pass an alias list, every one ('Specular IOR Level', 'Specular')
runtime  342 calls observed across all 22 material entry points those modules own
                            0 dropped;  0 of the 6 alias lists fell through
```

The optionality was theoretical, so raising breaks nothing today. Missing sockets now raise
`SocketGone`. The alias mechanism is untouched — it raises only when **no** candidate resolves,
which is precisely "the value was dropped".

**The static arm alone would have got this wrong, and that is the finding worth keeping.**
Blender resolves a socket string against the socket's **identifier** as well as its display
name, so `'Fac'` finds `'Factor'`. Judged against a measured socket table, ten perfectly correct
`_link(..., 'Fac')` calls in `spectator_seated.py` are condemned. **Only the runtime arm shows
them working.** A census that reads source and never runs it will manufacture defects at the
same rate it finds them.

Three inline copies of the same idiom in `world/build_dressing.py` (lines 1553/1757/2024 —
`for nm in aliases: if nm in b.inputs: …; break`, no `else`) were folded into one `_set_named`
helper rather than left because nobody had named them. **Leaving a known identical hole because
it was out of scope is how R2-070 happened.**

`tools/socket_setter_census.py` runs both arms plus its own control every time: it plants a
socket name that is genuinely gone on a real Principled BSDF and requires all five helpers to
refuse it, then writes to a name that *is* there and requires all five to accept.

**And the premise I gave this work was wrong.** I stated that `gantry_truss` and `pont_girder`'s
relief PASS verdicts had been read from frames lit by a flat context ground. They had not:
`item_gate.stage_witness` deletes everything but the subject, and the witness blends carry **no
`CTX_` material of any kind** — 11 objects and 12 materials, all `GATE_REF_*` or the item's own.
Re-judged from the rebuilt blends anyway, both verdicts stand unchanged, with margins of 70–120×
against a threshold of 2.00 and differences in the fourth decimal.

## R2-078 — the blind estimator, and why a foreground/background split was the wrong fix

`continuity_gate`'s whole-frame phase correlation reported **0.29 px/frame** on a tracking shot
whose background moves −24 px and whose car moves +36 px (R2-068). The obvious repair — split
the frame into foreground and background — **was proposed by me and is wrong.**

Dumping the field block by block on seam f804→805 shows image motion running **continuously**
from −28 px at top-left, through 0, to +40 px at the right, because the camera dollies past a
room whose contents sit at 4–22 m. **It is a depth gradient, not two halves.** The largest
cluster holds 19 % of blocks and the second another 19 %.

> **A bimodal summary would have replaced one confident wrong number with another.**

`tools/image_motion.py` therefore reports a **distribution** — `speed_med`, `spread_dx`
(p90−p10), `dominant`/`secondary` *with the block fraction each holds*, `shear`, `coverage` —
and each consumer takes the statistic that answers its own question. D5 reads
`median over blocks of |vᵢ − vᵢ₋₁|`, because a camera kink moves every block at whatever depth
it sits, while an object kink moves only its own. D7 speed-matches on `speed_med`.
`translation_median_px` became `image_speed_median_px` — **renamed, not reused**, so no stored
report can be silently reinterpreted.

**The positive control is what condemns the old estimator, and it is worse than "it returns
zero".** With background −24 px over 86 % of frame and subject +36 px over 14 %, the old code
returns **+36.09** — the *subject*, not the average — and sweeping the subject's area from 10 %
to 12 % **flips its answer from −24.07 to +35.89. Sixty pixels from a two-point composition
change.** The new estimator returns −23.91 and +35.87 and is stable from 5 % to 90 %.

**Blast radius, measured: 4 stored reports plus 1 A/B run that was never saved.** 24 individual
D5/D7 findings, 4 control rows, 4 floor figures, 7 pacing figures — all unmeasured, all
re-measured, with the stored reports marked `gate_version_stale` in place and pointed at their
replacements. **The D1/D2/D3/D4/D6 split was verified by result rather than by reading**: across
all four sequences those findings are *identical strings* before and after. One correction to
R2-068's framing — **D8's verdict was never downstream**; only its reported column was.

**No PASS/FAIL verdict flipped in either direction.** R2-066's A/B conclusion survives a real
measurement, and its D5 corroboration strengthens: seam_before f794/795 went from z = 12.2/9.3
to **z = 77/94**. Withdrawn: **7 of 11 D7 advisories on seam_after**, every one matched against
a "speed" of 0.04–0.40 px — *against a fiction*.

**A method note worth more than the defect.** The first blast-radius sweep returned three files
and was wrong: the shell's `grep` here is a wrapper that **respects `.gitignore`**, which
silently hides `work/` and `render/` — where the stored reports live. The real sweep used
`/usr/bin/grep` over all 4,825 files. **A search tool that quietly excludes exactly the
directory your artefacts live in will make any audit look clean.**

## R2-079 — the seam fix moved the kink rather than removing it, 57× smaller

New, and only visible once the estimator could see: **D5 fires at seam_after f755** (1.67
px/frame², z = 30) and is **absent from seam_before**.

`campath_gate` — an instrument sharing no code with the image measurement — independently flags
`C2_path_kink` at **f755** on the post-fix path (0.0030 m/frame, z = 8.8) and not on the pre-fix
path. Two unrelated instruments landing on the same frame is what makes this a finding rather
than a noise excursion.

**R2-064 removed a 0.171 m/frame kink at f793 and introduced a 0.0030 m/frame one at f755.**
Fifty-seven times smaller, real, advisory — and it could not have been seen before, because the
instrument that would have seen it was blind. Recorded rather than chased: it sits well inside
the authored-acceleration band that D5's leading arm fires on by design.

**Three instruments were caught wrong in the course of this, two of them the author's own.**
`continuity_gate.phase_shift` returned the negative of what its docstring claimed — every
consumer took a magnitude, so **no downstream effect**, stated plainly rather than inflated. The
author's own `block_residual` failed twice: v1 rounded shifts to whole pixels and so refused
every slow pan, including the seam's own 45-frame approach; v2 shifted sub-pixel but divided by
the *unshifted* difference, and since bilinear smoothing lowers the difference against anything,
**pure noise scored 0.6 and the refusal control returned a confident (+10.3, +30.1) px.**

And the third was a commit message. The author claimed the controls improved "from
12/13-with-one-skipped" — **an intermediate state of their own working tree, not the baseline**,
which flattered the change. Corrected in a follow-up; the real gain is one row. **A baseline
taken from your own uncommitted work is not a baseline.**

**Stated as not-confirmed, which is the right call:** on heavily motion-blurred 720p
(`work/seq_b5_1900`, beat 5) roughly **25 % of blocks can lose a large motion to a competing
zero peak** — brute-force minimum-|diff| search on 8 blocks agrees on 6 and disagrees on 2,
where reported −0.19 and −0.33 px are truly +51 and +9. Not fixed; measured, published in the
module docstring, and the `spread_dx` figure is what tells a reader the frame has no single
motion. Separately, `work/cont_carlaunch.json` was **already stale before any of this work** —
`TILE_MIN_FRAMES = 48` was added after it was written and carlaunch has 33 frames, so 11 D1_pop
and 14 D2_flicker findings are **NOT MEASURED rather than absent**, and nothing on the file's
face said so.

## R2-085 — f1461: an ABSOLUTE station cannot say how far away the car is

The film's last remaining campath FAIL — 51 % of frame width, 27.4°/frame, in beat 5.

`cp(s, u, h)` is an **absolute station**: its `u` is an offset from the **centreline**, and says
nothing whatever about where the car is. Between t = 59.00 and t = 61.60 **no anchor governed
the miss distance at all.** The camera crossed the racing line +20 → −20 over s 773–848 while the
car — 13 m/s faster, because the camera was spending its speed budget on 40 m of lateral travel
— caught up and arrived at the crossing point at the same moment.

**Closest approach 3.263 m, against an authored note reading "20 m away".** The car subtended
82° of a 53.6° frame. The author's own Catmull-Rom produces 3.263 m *before any key exists*, so
this was **authored, not sampled** — the geometry was in the spline from the start.

**Fixed by one sign.** `cp(773, +20.0, 3.0)` → `cp(773, -20.0, 3.0)` — the inside of the kink,
the side the next four anchors already use. 72 variants were swept to get there.

| | before | after |
|---|---|---|
| worst sweep | 56.55 % | **7.01 %** |
| closest approach | 3.17 m | **20.00 m — the note is now true** |
| campath | **FAIL** | **PASS, 0 FAIL** |
| beat 5 horizon | **79.77° over 50 frames** | **0.90°, 0 frames** |

**Both frames were rendered and looked at.** Before: 93 % car pixels, an unreadable smear with no
horizon. After: a level side-on tracking shot, car sharp at 20 m, wall and kerbs streaking — the
"fastest pan of the lap" the note always claimed. Clearance re-verified at minimum 3.631 m, 0 of
148 frames inside the 1.20 m sphere, controlled against `BVHTree` 400/400 and against unpruned
brute force over 13.7 M triangles.

## R2-086 — a local-median detector can only ever see the FIRST TOOTH of a periodic defect

f2680 was assumed to be a boundary artefact of R2-063's blend. It is not.

**R2-063 suppressed the frame-rounding only *inside* the blend window and left the branch
standing for beat 6's other six declared keys.** Each is a sawtooth — f2689 76.3 → f2694
56.9 m/s at **−151 m/s²** — about an analytic curve whose own worst acceleration is 6.7 m/s².

**Why only one frame of six ever scored, and this is the finding:**

> **C2 is a robust-z against a ±12-frame median, and the sawtooth's period is 24 frames. The
> window fills with the defect and the median rises to meet it.** f2691 scores 3.15× against a
> bound of 8. **A local-median detector can only ever see the first tooth of a periodic defect.**

That is a general property of every local-median detector in this codebase, not a fact about
f2680. A defect that repeats at roughly the detector's window length becomes its own baseline.

Fixed by deleting the branch — isolated effect 1.1251 m → 0.0213 m, the last 4.5× being
bracketing. Film-wide: frames over the 6× bound **4 → 2**, p99.9 6.70 → 4.20×, beat 6 worst
|accel| **151 → 6.7 m/s²**.

**The same shape explains f463, which is NOT real.** Jerk over f457–463 is constant at
−56.9 m/s³ with 0.6 % spread — a constant third difference is a cubic ease. The detector's ±8
window straddles a stop, mixing 8 approach frames (median |a| 7.65) with 7 near-stationary ones
(1.85), giving a mixed median of 2.08 and a ratio of 8.82×. **Against the pre-stop side alone it
is 2.40×.** It is the same event as the already-confirmed f462 false positive, not a second one.
**The accel-ratio detector has no hold guard, unlike `seam_gate`'s BULGE** — that is the
remaining fix, and it belongs to `seam_gate`.

## R2-087 — the speed-based key criterion: measured, then declined

Tried globally. Keys 433 → 451; campath **identical**, seam 7/7, subject_sweep 7/7.

**One gain:** BULGE 1.570 → 1.520×, on a figure already 15 % inside its bound.
**One loss:** accel p99.9 4.20 → 4.25×.
**Cost: 324 frames move, 321 of them inside beat 5** — the beat that is **67 % of the entire
master's render cost** — worst 0.234 m, invalidating every rendered frame of it.

Declined. It is the remedy for a specific failure — speed changing while bearing does not — and
**beats 3–5 do not do that.** Recorded here rather than left as a standing recommendation,
because the measurement is the useful artefact: the next person to propose it can read why.

## R2-088 — nothing on this film measured whether the horizon was level

The aim gate is **blind to roll by construction**; C1 measures rotation *rate*, and 60° of roll
spread over 42 frames is 1.9 % of frame width per frame — comfortably inside every bound.

So `tools/horizon_gate.py` was written, and it immediately found the shipped path at **79.77° of
roll across 50 frames in beat 5** (closed by R2-085) and **59.88° across 32 frames in beat 6**,
the latter a regression from R2-063 which doubled it from film9's −27°.

**A quantity nobody measures is not a quantity nobody has a problem with.** Two of the film's
worst frames were rolled most of the way onto their side and every existing gate passed them.

## R2-089 — both principled fixes for beat 6's roll were costed and both failed

Blending the roll reference halves beat 6 and **doubles beat 1** — 20.83° → 38.59°. Raising
`look_quat`'s 3°/frame limit to 15° removes the horizon problem entirely and takes beat 5's smear
to **47.8 % of frame width**, which is the exact defect R2-085 was spent killing.

**The limit is buying rotation legibility with horizon level, and one number cannot do both.**
Recorded as a costed rejection rather than an untried idea, so the next person does not spend the
day rediscovering it. `look_quat` was left unchanged.

## R2-090 — the closing wide cannot show the circuit and the car at once

At f2978 the camera is 140 m up, 595 m out, on the film's widest lens, aimed to 0.08°, holding
for exactly 3 s (**0.00 m over 72 frames**). The circuit reads.

**The wound is 20 px of 1920. The car is 12 px — and the agent rendering it could not find it.**

Putting the car at 2 % of frame width requires either a **73.8 mm lens** — a telephoto, not a
wide — or **188 m**, a third of the circuit. The brief asks for both and the geometry does not
allow both.

**Decision: the car wins.** This film is 124 seconds of following one car; ending on a frame
where the audience cannot find it ends on a different subject. Two independent readers failing to
locate it is evidence, not taste. The chosen resolution is being selected **by rendering variants
and looking**, with a lens push on an unmoved camera path as the leading candidate — because its
cost is confined to one track and leaves every seam, the aim gate and the 3 s hold exactly as
measured.

## R2-091 — beat 6's roll is WAIVED, not tuned away

f2680 sits at −33.8° and **reads as a banked aerial** — pit wall diagonal, car sharp and centred,
pit lane legible — and f2694 levels into a clean aerial. Beat 6's first declared move *is* a
peel-off, and the roll is smooth throughout. The recommendation reversed on the strength of the
pictures, having been "fix it" on the strength of the number.

**It is recorded as an explicit waiver and `horizon_gate.py` still fires.** The reasoning is the
part that generalises:

> **A gate quietly re-tuned so it stops firing on something someone accepted is worse than a gate
> with a waiver beside it — and that is precisely how the 79.77° roll survived into the shipped
> film.**

A waiver is a decision with a name on it. A moved threshold is a decision nobody can find later.

**Outstanding against this waiver:** f2666, the −59.88° peak, **has still not been looked at.**
f2680 and f2694 bracket it and both read, but the peak itself is the frame the waiver is about.
**Waiving something nobody has looked at is not a waiver, it is an assumption** — so the waiver is
provisional until that frame exists.

## R2-108 — a harness flag mismatch, a manufactured null, and the doc that was still teaching it

`work/r2038/run_module.sh` passed `--test --save <path>` to all fourteen modules
in its campaign. **Twenty-one of the forty-one item modules take `--out`.** On a
hand-rolled `opt()` parser the wrong flag is silent: the module builds the whole
test scene, prints its full report, throws the result away and exits 0. On
`pont_deck_slab` the gate then measured the blend built on 29 July, rendered it
against itself, and returned mean |diff| 7.69e-06 against a 7.70e-06 noise
floor, 0.00 % of pixels, correlation 0.99994 — a flawless, convincing null. The
stored re-run says **57.499 %**.

**Reproduced on live source, both directions, 2026-08-03:**

    crew_fireproof_overall --test --n 1 --save A.blend
        exit 0 · 188,062 triangles built and reported · A.blend NOT WRITTEN
    crew_fireproof_overall --test --n 1 --out  B.blend
        exit 0 · same build · B.blend = 18,367,428 bytes

The two runs differ by one line of stdout.

**The mismatch was not r2038's.** `world/items/REFERENCE.md` documented
`--test --save <path>` as *the* build command every item agent follows: the
**wrong save flag on 23 of 41 modules and the wrong verb on 3 more**. Fixed
there, and `tools/item_build_cmd.py` now derives the command from the module's
own parser. Two arms, per R2-073: a static AST read, and a **runtime** arm that
runs each argparse module with an unknown flag and reads the live usage table —
**35 of 35 probed, 35 agreed**. The 5 hand-rolled modules are STATIC ONLY and
the census says so per row rather than pretending. `--build` requires the target
blend's sha256 to change.

`run_module.sh` and `run_module2.sh` now **refuse** (exit 3) rather than build
with the wrong flag; `run_module3.sh` was already correct.

**WHAT WAS CONCLUDED THROUGH IT, AND DOES IT SURVIVE — YES, ENTIRELY.**
Attributed per module from the pipe logs:

| module | takes | harness that ran it |
|---|---|---|
| crew_fireproof_overall, gantry_truss, marshal_post_column, pont_deck_slab, pont_girder | `--out` | **run_module3 (fixed)** |
| armco_w_beam, catch_fence_post, heras_fence_panel, pit_wall_unit, tyre_wall_tyre | `--save` | run_module3 (fixed) |
| armco_post, kerb_precast_unit, team_truck_trailer | `--save` | run_module / 2 (broken) |

**Every module the broken harness ran takes the flag it passed**, and each
`build.log` carries a `saved …` line, so those three builds landed *by
artefact*. **Every `--out` module was re-run on the fixed harness.** No
published r2038 number descends from the null; the stored
`render/relief_ab/pont_deck_slab/ab.json` (08-02 18:45) is the corrected run.

**One layer out, and newly measured:** `item_build_cmd --stale-census` finds
**15 of 32** item test blends older than the source that built them —
`spectator_seated` by 133.5 h, `tyre_blanket` by 112.3 h. Reported as SUSPECT,
not as defects: an mtime says the source moved, not that the geometry did.


## R2-109 — a verdict read from a 3.6-stop-over frame is not evidence

`tools/build_verify_scene.py` set no view exposure. The assembly blends carry
`+0.000`; the film's measured grade is `FILM_EXPOSURE = -3.628`. The repair
(import `world/film_exposure.py`, apply before the rig, then assert every place
exposure can enter) existed but **had never been watched fail**. It has now:

* `--control-break-exposure 0.0` → `VERIFY_GRADE_FAIL`, *"+3.6280 stops off …
  That is no exposure at all — the blend's default"*, and the mis-graded blend
  is **deleted** so nobody can inspect it.
* `--control-break-view-transform Standard` → the same.
* normal → `VERIFY_GRADE_MATCHES_FILM`, −3.6280 on the static value, both ramp
  ends and the last frame.

**7 of 9 `verify_*.blend` carry +0.000; ~70 frames came off them.** What that
costs, measured on the artefacts — frame 960 of the same take, same rig, two
grades:

| | mean lum | p99 | pixels with a saturated channel |
|---|---|---|---|
| `render/exposure_beats/cal_960.png` (−3.628) | 0.0166 | 0.0456 | **0.000 %** |
| `render/shutter_ab/*_f960.png` (+0.000) | 0.494 | 0.9901 | **23.6 %** |

f870 is **27.2 %** saturated, f890 13.5 %, f1400 7.3 %.

**R2-053's shutter decision was read from those frames** and moved real work
(HERO 91 → 75, agents/round 178 → 169). Re-measured — `mean |Laplacian|`,
world/flat, over all opaque pixels and then over only pixels whose 3×3
neighbourhood holds no saturated channel:

| frame | all px | unclipped | px kept |
|---|---|---|---|
| f870 | 1.901 | **1.951** | 72 % |
| f890 | 1.766 | **1.832** | 86 % |
| f960 | 1.181 | **0.995** | 76 % |
| f1400 | 1.000 | 1.000 | 93 % |

**The conclusion survives and strengthens slightly** — removing the blown pixels
moves the ratio the *right* way, and R2-053's published 1.925 / 1.702 sit inside
the band. **f960's contribution does not**: 1.181 → 0.995, no difference at all,
so that frame's apparent 18 % gap is an artefact of the exposure and is
withdrawn. **Every absolute figure from these frames is unmeasured** —
`mean |Laplacian|` itself falls 46–47 % when the blown pixels go, so a
"smear ≤ 6 px" threshold cannot be read off them.

`tools/item_presence.py`'s `4_by_eye` key claimed eight `verify_world` frames
*"confirm what the numbers say"* — *"the trackside hoardings smeared to
transparency"* — and was **re-emitted on every run**. Withdrawn as **UNMEASURED,
not refuted**: the numeric tiering was never read from those frames. Marked in
place in `docs/screen_presence.json`, five `work/tier2/item_presence_*.json`,
and `render/shutter_ab/EXPOSURE_NOTE.md`.

`tools/render_local.py` never set or reported exposure, and would reproduce the
defect on any of the seven blown blends. It prints the grade of every render now
and says loudly when it is not the film's — shown firing at +0.000 and silent at
−3.628. **Still open, not touched (other owners):** `anim/build_camera_rig.py`
sets no grade and its live `work/beats456/rigs/*.blend` all log
`exposure ramp +0.000 -> +0.000`; `sim/witness.py:55` hardcodes `-3.628` instead
of importing it, which is the drift `film_exposure.py` exists to prevent.


## R2-110 — the gate that guards every item placement had no control, in any battery

v120, v121 and v122 each `run` `placement_gate` twice against the world and
**never once** against a case that must fail or must pass.
`ctl_place_pos.blend` and `ctl_place_neg.blend` have existed since the file was
written and **no battery ever opened them**. This is the gate already caught
testing empty air over 28 % of the lap. Wired in, and measured:

    ctl_place_pos       PLACEMENT_FAIL  rc=1   road_corridor −7.8222 m
    ctl_place_neg       PLACEMENT_CLEAN rc=0

**And the far negative control measures nothing.** Its own log:
`tested 1 objects; 1 rejected on bounding box; 0 measured per-vertex`. It can
catch a gate that *invents* violations and nothing else — it cannot catch
**over-rejection**, which is the failure this project actually had.

`ctl_place_nearmiss_neg.blend` is the over-rejection detector: the same obstacle
just outside the corridor, offset derived from the **live contract** each run
(`half_width(s)` + the gate's own 0.50 m margin + the cube's half extent +
0.80 m), so it tracks the corridor instead of expiring against it. Measured at
s = 1000, contract 1.2.1:

    gap 0.30 m → road_corridor −0.110 m   PLACEMENT_FAIL
    gap 0.55 m → +0.139 m                 PLACEMENT_CLEAN
    gap 0.80 m → +0.389 m                 PLACEMENT_CLEAN   ← shipped
                 1 object measured per-vertex, not 0

`ctl_assert.py` holds it there, because `expect pass` alone would be satisfied
by a control that had drifted back out to 3 km. Both directions: the near-miss
report → `CTL_ASSERT_OK`, tightest clearance +0.3892 m on `road_corridor`; the
**far** report, which the gate *also* passes → `CTL_ASSERT_FAIL`, *"this control
passed WITHOUT the gate looking at its geometry"*.

**R2-072's shape, closed.** Nothing regenerated the ten control blends; three
batteries opened whatever a human last left in `v120/`, and `ctl_place_pos` is
*positioned from the contract*. `lib_battery.sh :: regenerate_controls` rebuilds
them from live source every run and halts if the files were not rewritten —
shown both ways (10 rebuilt → `ok`; a directory it cannot write → `BATTERY_
INSTRUMENT_FAIL`, exit 2). All ten regenerated and re-run against the live
gates: **5 must-fail all FAIL, 5 must-pass all PASS.**

**And the battery had no version control at all.** `.gitignore`'s own header
says git exists here because an agent destroyed 1,655 unrecoverable lines — and
`render/` was swallowing **52 files of hand-written source**: `assemble.py`,
`probeA`–`probeK`, `lib_battery.sh`, all three `battery.sh`, `make_controls.py`.
"Establish a baseline from committed state" (R2-079) was **structurally
impossible** for the battery. Artefacts stay ignored; the source is tracked now.
`work/` still is — `work/r2038/run_module*.sh` remains untracked.


## R2-111 — three tools that reported success on failure, and five docstrings citing guards that do not exist

**`v120/fp_diff.py`** computed `moved`, printed it, and **never consulted it**.
No `sys.exit`, no `STAGE RESULT`, no `gate_exit` — it fell off the end at rc 0
and `lib_battery.sh :: run()` recorded `ok`. `v122/battery.sh` states in capitals
that *"fp_diff must find ZERO moved objects … before anything else in this report
is believed"*; it could have printed **100.00 %** and the run would still have
ended `BATTERY_OK`. The no-common-names branch printed its own refusal and also
exited 0. Expectations are declared on the command line and checked now, with a
7-case selftest and validation against the pair **already known to be bad**:
assembly5→assembly6 `--expect-moved 0` **FAILS** on `BR_Transit_NorthWall`,
bbox shift **3.1885 m**; assembly6→assembly7 **PASSES**, 0 of 28,781. A bare run
with no declared expectation is now `VACUOUS` (3), not a pass.

**`tools/horizon_gate.py`** returned `"verdict": "PASS"` for **zero frames
measured** *and* for **zero frames judged** — a camera rolled 80° while pointed
at the floor passed, because nothing was eligible. Both are `HORIZON_VACUOUS`,
exit 3, shown firing on `--lo 9000 --hi 9100` and on beat 1 (60 frames, none
within 45° of horizontal). The real run still returns a real verdict:
`HORIZON_ROLLED`, 32 FAIL frames at 2657–2688.

**`tools/build_beat1_audit.py`** computed `missing` image files, printed them
with `!!`, and printed `BEAT1_AUDIT_BLEND_OK` two lines later — the exact
failure its own comment twenty lines above says cost Round 1 a render batch.
`--control-plant-missing-image` exists so the assertion can be watched to fail.

**Five phantom citations, all confirmed absent:**

| citing file | citation | reality |
|---|---|---|
| `world/itemkit.py:1370` | `itemkit.socket_audit()` | no `def socket_audit` anywhere — **and it was in the `RuntimeError` text a reader hits at the moment a socket index has moved** |
| `world/items/crew_fireproof_overall.py:484` | `socket_audit()` | same |
| `tools/item_presence.py:321` | `--shutter-mode {flat,world}` | no such flag in the project |
| `tools/beat2_probe.py:80` | `--dump-exposure` | no such flag; and line 286 treats a missing `--exposure` as FAIL, so the phantom blocked the only documented route to passing |
| `tools/black_row_count.py:36` | `--control` | the guard is real and on by default; the flag is `--no-control`, so the documented invocation is an argparse error |

Plus the **battery headers themselves**: v121 and v122 claimed *"every `-P`
entry point is wrapped so an uncaught exception is a status 2"*. Four of their
own steps are not — `vertex_fingerprint.py`, `variety_distribution.py`,
`mesh_reuse.py`, `probe_pitexit.py`, **zero occurrences of `gate_exit` in any of
them**. The headers now say which four and tell the reader not to trust their
status.

`tools/phantom_citations.py` sweeps 207 files for `module.function()` and
`dir/file.py` citations that do not resolve, with both controls (3 real
citations → 0 hits; 3 phantom → 3 hits) and a `PHANTOM-OK` marker for prose that
*documents* a phantom. Flags are held in an explicit hand-verified list rather
than guessed, because a checker that guesses which of forty tools a `--flag`
belongs to manufactures defects at the rate it finds them (R2-073). Sweep is
**clean**, with two cited-but-absent items **printed as NOTE on every run**
because their files are owned by other agents right now:
`tools/build_film_scene.py:473` (`world/assembly/r2/assemble.py` — the real path
is `render/world/assembly/r2/assemble.py`) and `tools/socket_index_audit.py:88`
(a placeholder).

**Measured but NOT fixed**, all confirmed, all in files that were either
lower-value or owned elsewhere: `tools/inventory.py:245` (warnings counted,
`INVENTORY_OK` regardless), `tools/seam_gate.py:624` (`SEAM_CENSUS_OK` printed
whatever the census found, no guard), `tools/subject_sweep.py:299` (vacuous
summary lacks `span`/`verdict` → `KeyError` → **exit 0 with no `STAGE RESULT`
at all**), `tools/cam_clearance.py:69` (prints `CAM_CLEARANCE_VACUOUS` and exits
**1**, so a battery's `expect vacuous` halts on a correct refusal; and `min()`
on an empty `rows` raises → exit 0), and the same
count-then-pass-anyway shape at `tools/macro_audit.py:198`,
`tools/presentation_normals.py:175`, `tools/build_telemetry.py:553`,
`tools/dump_exposure.py:33`, `world/build_sky.py:1872`,
`world/showroom_lighting.py:586`.

## R2-092 — the wall opens on TWO parameters, and only one was ever tuned

`t_bond_per_m` decides whether glass **leaves**. The **mullion thresholds** decide whether the
opening is **wider than the car**. Across a 40× bond sweep (4000/1000/400/200/100), mullions
3, 4, 6 and 7 never move more than **45 mm** — only mullion 5, the one the car hits head-on,
responds at all. Every previous attempt tuned the parameter that could not widen the hole.

`THRESH_MULLION_JOINT = 900` / `BASE = 1400`, in Bullet's units — impulse per substep, so at
240 Hz × 8 substeps a threshold T is T × 1920 N sustained — are **1.73 MN and 2.69 MN**. A
75 × 160 mm 6063-T6 extrusion fails in bending near **30 kN** and its base studs in shear near
200 kN, i.e. T ≈ 16 and 104. **The shipped numbers were 55× and 13× too strong.**

Shipped: `bond 100, mullion joint 40, base 120` — derived from the extrusion, not fitted to an
outcome.

| | shipped | now |
|---|---|---|
| connected hole | 0.65 × 1.65 m, 0.6 % vacated | **2.15 × 6.00 m** (3.80 × 6.00 bridged) |
| bay 4 vacated | 0.0 % | **96.7 %** |
| mullion 5 travel | 0.407 m | **1.215 m**, 2 segments detach |

## R2-093 — the null passed because the wall had been made unbreakable, and the trade was negative

Four 480-frame `--wake-all --no-car` bakes. **The null at mullion 40/120 is bit-identical to the
null at 900/1400** — same 3 shards gone, same 2.257 m max, same 8.48 mm median. The mullion
thresholds are never approached under dead load. 15/50 breaks it (bay 7 sags 510 mm), so the
bracket is clean and 900/1400 sat far above it buying nothing.

**And the trade did not buy what it cost.** Over the same 480 frames the shipped 4000 has a
*worse* median displacement — **15.21 vs 8.48 mm** — and **264 shards over 50 mm against 100's
5**. A stiffer network is harder for 24 sequential-impulse iterations to satisfy, not easier.
All it ever bought was the binary "nothing over 0.25 m", **by making the glass unbreakable**.

A `mobility` field was added to `null_verdict` so that **a null which passes because nothing can
move is visible in the verdict** rather than indistinguishable from a null that passes because
nothing *should* move.

## R2-094 — the declared 9.6 m aperture was a measurement of a different object

9.6 m is `|Y| ≤ 4.8`: **the span between the two bent mullions.** The glass is a different
object and can reach at most **8.77 m**, and only by taking bays 2 and 7 that the same plan
marks `retained`. The car is 2.005 m wide, so nothing loads mullions 4 and 6 at all.

Testing the obvious lever — edge clamp 2.5 → 25, so the pane keeps hold of its frame — made the
aperture **worse**: 18.4 % → 7.5 % vacated. **Every attempt to reach 9.6 m was chasing a number
that describes the frame, not the hole.** Decision: correct the spec, ship the achievable
aperture. A wider breach is an *authored* choice about releasing bays 2 and 7, made looking at a
frame — not a threshold.

## R2-095 — `camera_ranges()` was 6.5× wrong, so every pixel figure through it was too

It priced bay 2 at **3.52 m**. The honest closest in-shot range after release is **22.87 m**.
Every sag figure ever quoted through it — including the standing "7.1 px" description of this
defect — was **6.5× too big**. Fixed at source and verified inside Blender.

**And the target was wrong as well as the scale: the worst retained bay is 7, not 2** — 11.52 px
at the recommended config, **10.75 px at the shipped one**. The wake-all null **has never met its
1 px criterion at any threshold**; a broken instrument was hiding that. Nothing regressed; a
long-standing failure simply became visible.

## R2-096 — fragment energy was never coupled to aperture, and the headline speed was a downstream blow-up

Mass-weighted peak speed across the whole bond sweep: **5.91 / 6.29 / 6.23 / 6.30 m/s.** Field
kinetic energy is non-monotone — 100 is the *lowest*. Opening the wall does not make the debris
faster.

The 137 m/s peak **exists in the shipped bake too**. The fastest shard reaches 137.6 m/s at
impact +0.49 s, at x = 17.26 while the car nose is at 23.25 — **six metres past it, travelling
backwards**, with 66 shards peaking on the same frame. It is not the car proxy: probes at nose,
rear wing and airbox never exceed 19.90 m/s (controls: origin probe exact, rotation zeroed
agrees to 4e-13).

The honest number is **launch speed — 1.43× the impactor at the 99th percentile by mass**. The
circulating "2.4×" was a max over 3,948 bodies dominated by the blow-up. **Larger than first
recorded: 828 shards exceed 60 m/s, 661 of them on screen** — but the shipped threshold is the
*worst* case at 7.6× the bond-100 population, so the config change **reduces** it.

## R2-097 — the shatter-and-un-shatter: the wall visibly un-breaks on camera

The slab field at f0866 was hypothesised to be an intact-mesh/fractured-mesh swap with both
present for ~12 frames. **Falsified**: `apply_breach.py` hides the pane at `r = min(release)`
over its bay and shows every shard of that bay at the **same** `r`, read off `breach_film.npz`.
**No frame renders both.** The only anomaly is 9 shards appearing one frame late.

It is the shard field. Projecting the bay rectangles onto the render shows the slabs lie
**exactly inside destroyed bays 3/4/5 and stop at their boundaries**. Bay 4's shards are 559 mm
from home, spread through 1.4 m of depth, displaced 259 px median on screen; bay 7 shows 5.7 mm
and 1.3 px.

**At bond 4000 the pane bulges as a sheet and springs back.** Bay 4's depth offset is **483 mm at
f866 and 17 mm by f900**; its median normal rotation goes **80.7° at f866 and back to 9.9° at
f900**. *The field un-rotates.* **In a film with zero cuts, the wall visibly un-breaks.** This is
not a rendering artefact — it is the defect the config change fixes, seen from the camera.

## R2-098 — measuring departure by depth, and by count instead of area

Two figures were wrong before any control caught them, and both are the same mistake in
different clothes: **depth is not a departure measure for a field that has already left**, and
**"gone by count" is not "gone by area"** — bay 5 is 87 % gone by count and **13.2 %** by area.

Three of the successor's own controls also failed first, including one that called a shard
"never moved" **when it had left at 18 m/s and landed back within 2.5e-7 m of home.** Net
displacement cannot distinguish "stationary" from "returned".

`sim/aperture.py` carries the trap that motivated it: the **old** aperture measure reports a
**13.01 × 5.79 m opening from two shards.**

## R2-099 — the sweep is single-seeded, and says so

One bake per sweep point, one fracture plan, unknown run-to-run variance. Published as a limit of
the result rather than discovered later: a second seed's plan is identical to within 1 %, so any
variance that appears is **the solver's**, not the fracture's. Also open and undiagnosed: cluster
B of the blow-up — **348 shards to 106 m/s with no measurable contact.**

## R2-100 — `input_stamp.py` declared assembly6 and would have gone on declaring it

Line 44 carried its own copy of "which world ships". **Fixed by removing the fact, not by
updating it** — a second copy of a fact is the mechanism behind R2-071, R2-061 and this entry
alike. New stdlib-only `tools/shipping_world.py` parses the **one** declaration in `SHIPPING.md`;
`input_stamp` and `build_film_scene` both read it, the latter having had its own second parser
which now delegates. It must be `bpy`-free because one caller runs inside Blender and one does
not.

`--selftest` carries four controls, **including one the old inline parser would have failed**:
`text.split(TITLE, 1)[-1]` returns the *whole file* when the heading is absent. Verified live —
old literal → `assembly6.blend`, new code → `assembly8.blend`.

**And `SHIPPING.md` itself was untracked.** The blanket `render/` gitignore excluded it, so the
project's single world declaration **had no version control at all**. Force-added. This is the
same shape as the 52 untracked battery source files found the same day: *the file everyone
treats as the source of truth is the one nobody checked was in git.*

## R2-101 — the relief reports did NOT hold still, and the control had to be manufactured

The premise handed down was that the two stale `_relief/*.json` files would not move, because
their inputs had not changed. **Measured instead of accepted, and the premise was wrong:**

```
pont_girder    m_max 0.00272 -> 8.273     m_sum 0.00513 -> 20.141
               Height-unlinked stages 5 -> 0
gantry_truss   m_max 0.00586 -> 8.073
```

**Both sides had changed** — the witness blends were rebuilt on 08-03 and `relief_audit.py` /
`itemkit.py` were edited the same day — and **no pre-08-03 tool exists in git**, so the obvious
A/B was impossible. Rather than guess which side moved, the control was **manufactured**: put the
R2-038 wiring back onto the *repaired* witness, run *today's* tool, and see whether it reproduces
the shipped JSON's signature. It does, exactly — "no procedural texture found upstream of
Height". Confirmed from the other direction by reading both witness generations' bump wiring: 8
bumps, 8 Heights linked, 0 on `Thin Wall`.

> **The artefact moved, not the instrument.**

**Scope is 30 files, not 2.** Every witness blend under `render/gate_witness/` was rebuilt on
08-03 between 12:19 and 18:46, and **every one of the 30 `_relief/*.json` predates its own
witness.** Superseded reports kept as `*_SUPERSEDED_pre_R2038witness.json`.

## R2-102 — assembly8: exactly one object of 28,781 moved, and it was predicted in writing first

| | assembly7 | assembly8 |
|---|---|---|
| objects | 28,781 | 28,781 |
| total verts | 1,282,465,803 | 1,282,465,803 |
| **objects moved** | — | **1** |
| bit-identical | — | 28,780 |

`TER_Ground`: vertex count unchanged, bbox x / y / z-min **bit-identical**, **bbox z max
38.004730 → 364.460632 (+326.4559 m)**, sum of z equivalent to +4.3111 m mean over 599,872
vertices. Cause: `world/build_terrain.py` gained `far_horizon()` and the `HORIZON_*` block at
09:07 — **five hours after assembly7 was built at 04:45.** It raises the far field to a 300 m
crest beyond Dc 3600 m: z only, no x, no y, no count. Nothing inside 3600 m moved, so no barrier,
surface, architecture, dressing or vegetation object moved and the circuit is untouched.

**The prediction was written down at 19:16, while terrain was still building, and all four parts
of it were met.** Predicting the shape of a diff before running it is the difference between a
verification and a rationalisation.

**Materials: 0 of 132 moved** — established with a *new* per-material graph fingerprint (every
node, input default, link, node property), because the existing census only counts bump nodes and
would have been blind to, say, a roughness change from `build_architecture`. Its control: the
same script on assembly6→assembly7 returns **9 of 132, all `DR_*`**, and names the moves —
reproducing `SHIPPING.md`'s table **from a script that had never been run.**

**And the module build report showed 0 substantive differences** — only timings and the output
path. That proves nothing, and that is the point:

> **The build report was bit-identical while `TER_Ground` rose 326 metres.**

## R2-103 — a quaternion rounding floor that reads as 0.162° of rotation

`film11 → film12`: beats 1, 2, 3 and 4 are **positionally bit-identical (dp = 0.000000 m)**; beat
5's worst is 40.458 m at f1442 (R2-085's T3 fix landing, and the stale focus track gone); beat
6's worst is 1.050 m (R2-086).

But the *unchanged* beats read 0.16–0.20° of rotation difference. **That is the instrument's own
floor, not a movement.** The path JSON rounds quaternions to 6 dp, and `2·acos(|dot|)` amplifies
that by a square root — **1e-6 of rounding reads as 0.162°.**

An earlier agent chased exactly this artefact on frames whose quaternion components were
**bit-identical**, and reported it as 0.069° of real rotation change. It is now documented in the
tool so nobody re-derives it as a defect a third time.

**film12 readback: zero of 37 fields differ from film11**, and the levelling identity was
recomputed from film12's own `_sl_base` properties rather than quoted — base 3,737.113 × 2^3.628
= 46,203.306 against 46,203.313 measured, residual **0.007 W**, worst per-lamp ratio
12.363369363 vs 12.363368794 so no lamp hid inside the total. Both world guards fired correctly
and **no `--world-override` was used**.

## CORRECTION to R2-088 — the gate that finally measured roll shipped a metric that saturates, and its default input was a generation old

Two corrections, and the first is the one that matters.

**The metric was wrong.** `tools/horizon_gate.py` measured tilt as
`asin(right.z)` — the angle of the camera's right axis above the horizontal
plane. That saturates at ±90°: it cannot distinguish a camera rolled θ from one
rolled 180−θ, and **as a camera passes through fully inverted it returns to
zero.** The correct image rotation is `atan2(right.z, up.z)`, and the sign of
`up.z` settles it in one character. The old metric discarded that sign entirely.

| frame | shipped `asin(right.z)` | true `atan2(right.z, up.z)` | up.z |
|---|---|---|---|
| **f2651** | **+1.99°** | **+176.65°** | −0.594 **inverted** |
| f2661 | −52.92° | −101.23° | −0.158 **inverted** |
| f2666 | −59.88° | −81.71° | +0.126 |
| f2680 | −33.83° | −36.97° | +0.740 |

The camera is **fully inverted for 28 consecutive frames, f2636–f2663**, peaking
3.3° from perfectly upside-down at f2651 — where the shipped metric reported
1.99°, i.e. level. **It called the worst frame in the film the best.**

So the claim R2-088 makes about itself — that it is the instrument nobody had —
stands, and the number it published, 59.88° in beat 6, was wrong: the peak is
122.93°, and f2666 is −81.71°, not −59.88°.

**Found by looking.** A render agent rendered f2666, measured the dominant
straight-edge direction *in the pixels* at +83° from horizontal, and refused to
accept a geometry number that disagreed with the picture. The instrument had six
controls, a census and a published finding, and not one of them was a frame.

**Second correction, and it is the same failure one level out. The gate's own
negative control was failing, and not because the gate was wrong.** See R2-115
and R2-114 below: `--selftest` reported `HORIZON_GATE_SELFTEST_BROKEN` on a clean
tree because the gate defaulted to `render/film11_path.json` and film12 — built
twenty minutes later with R2-085's fix in it — was never wired in. Anyone
re-running the selftest to check R2-088's finding would have been told the
instrument was broken, while looking at the wrong path.

Both are fixed. Selftest is 7/7, with a new synthetic arm P4 — a camera rolled
exactly 170°, which reads 170.000000 on the corrected metric and 10.000000 on the
one this gate shipped with. **That arm exists because the broken metric survived
six controls.**


## CORRECTION to R2-091 — the waiver is WITHDRAWN, and the roll it waived has been fixed rather than accepted

R2-091 waived beat 6's roll as "a banked peel-off, not a defect", on the strength
of f2680 and f2694. **Both bracket the peak.** The peak was then rendered and it
does not read:

* **f2666** — the frame is on its **side**. The track runs top-to-bottom, the pit
  garages are a vertical stripe against the left edge, and there is **no sky and
  no horizon in it at all**. Confirmed by a second reader on the same render.
* **f2661** — the pit-lane lines run vertically down the left edge; the car is
  vertical. Also on its side.
* **f2680 reads as a bank, and the reason is visible: it has sky in one corner,**
  so the viewer can tell which way up is. f2666 has none.

So the waiver held from about f2673 onward and **did not hold across
f2658–f2670**. A waiver written from bracketing frames is an assumption, and the
peak refuted this one.

**The part of R2-091 that generalises still stands and was not touched:** the
gate was never re-tuned to stop firing. It kept failing beat 6 until the camera
was fixed.

**And most of the inversion was genuinely harmless — checked, not assumed.**
f2646 and f2651 were rendered: near-nadir shots in which the car fills the frame
with no world reference, so being upside down in them is invisible. The
`|pitch| ≤ 45°` scope was doing its job. The damage was confined to the frames
where the world re-entered shot while the roll was still past vertical.

**The waiver is now moot rather than merely withdrawn.** R2-112 removes the roll:
worst tilt with a horizon in shot over f2600–f2714 goes −122.93° → **1.71°**, 32
FAIL frames → **0**, 28 inverted frames → **0**. The shipped rolled path is kept
as `docs/horizon_pre_R2112_path.json` and is now this gate's positive control.


## R2-112 — the peel-off rolled the camera past vertical with the world in shot, and the roll reference had changed subject halfway through

Thirteen frames, f2658–f2670, on their side. The pictures are in
`work/r2112/`; f2666 before and after is the pair to look at.

**Root cause, and it is not the correction rate.** `look_quat` rejects world up
as a roll reference once it comes within 26.7° of the view axis — pitch 63.3° —
and beat 6's peel-off carries the view through **pitch 80.5°**. So for the whole
nadir pass the roll was corrected toward the **direction of travel**, which is a
good reference for a top-down follow and has nothing to do with level, while the
error against world up grew unwatched to **163° by f2638**. Everything after that
is the error being paid back at the 3°/frame limiter — **38 consecutive frames at
3.00–3.30°/frame, f2657 to f2694** — and the world comes back into shot at f2657
with 123° still owed.

**Fixed by holding world up as the reference through the pass** (`PEEL_REF_MIN`
0.15, i.e. to pitch 81.4°) so the error never accumulates, plus a raised
correction limit inside the same window. Both are scoped to a window derived from
the beat sheet — `PEEL_LEAD_FRAMES` before beat 6's declared peel key to the start
of beat 6 — and the build prints the window together with the near-vertical span
it actually caught, so a window that stops containing the thing it exists for
cannot do so silently. It caught 18 near-vertical keys, f2630–f2656; the film's
other 26 are untouched.

| cone | rate | worst tilt f2600-2714 | FAIL frames | inverted | beat 5 smear | campath |
|---|---|---|---|---|---|---|
| 0.45 | 3 | −122.93° | 32 | 28 | 16.18 % | PASS *(shipped)* |
| 0.15 | 8 | 31.61° | 13 | 0 | 18.92 % | PASS |
| **0.15** | **10** | **1.71°** | **0** | **0** | **22.07 %** | **PASS** ← shipped |
| 0.15 | 12 | 1.71° | 0 | 0 | 25.47 % | FAIL |
| 0.45 | 15 | 1.71° | 0 | 0 | 47.83 % | FAIL |

Ten is **bracketed**, not tuned: eight does not finish the job, twelve is the
first value campath refuses. The control — cone 0.45, rate 3 — rebuilds the
shipped path **bit-identically**, 0.000000e+00 on position, quaternion and lens
across all 2,978 frames. Beats 1, 2, 3, 4 and 6 are unchanged to the digit. The
four beat-1→2 invariants are exact: chord 2.0893 m, speed 1.2727 m/s, look
13.2504°, lens −0.051 mm, and every derived seam figure is identical.

**R2-089's two candidates were re-costed against the corrected metric and both
rejections stand.** The global limit reproduces to the digit — 47.83 % of frame
width at f1800, which is R2-085's own defect class.

**AND THE OBVIOUS THIRD CANDIDATE WAS BUILT, MEASURED AND THROWN AWAY, which is
the part worth keeping.** Raise the limit wherever the horizon is *out* of shot,
on the argument that such a frame has nothing for the roll to be level against —
and f2646 and f2651 were rendered and do support that argument *for those frames*.
Swept at 6/10/15/18/24/30/45 it cost **47.83 % at f1800 and 27.81 % at f75: the
same cost, to the digit, as the global fix it was supposed to improve on.**

> **The pitch test is not a scope. The correction limit only ever BINDS where the
> view is near-vertical — that is the only place transport outruns 3°/frame — so
> scoping it to near-vertical views selects every frame it was already acting on
> and excludes none of them.** f1800 sits at pitch 64.0° carrying 88.0° of roll
> and f75 at pitch 80.6° carrying 112.9°; in both, the roll is plainly visible
> because **the subject** is in frame even though the horizon is not. "No horizon"
> was verified to mean "no visible roll" on two frames of beat 6 and assumed to
> mean it everywhere else. It does not.

**C1 overstates a roll, and the bracket was still drawn on it rather than argued
with.** campath's C1 is `2·acos|q₀·q₁| / hFOV` — the total rotation angle between
two frames — so it cannot tell an axial roll from a pan. 22 % of frame width is
what the **corners** do; the centre, where the car is, does not move.

**WHAT R2-112 COSTS, RENDERED AND MEASURED.** The frames the fix spends its
budget in are the near-nadir ones, f2631-f2655, and the argument that roll is
free there is *weaker than it looks*: there is no horizon in them, but the CAR is
in them at hero scale. f2639 was rendered from both cameras out of the same
scene lineage:

    f2639   mean |gradient|   p99 |gradient|
    shipped        1.532            15.44     a crisp near-nadir hero frame --
                                              cockpit, halo, airbox, engine
                                              cover all readable
    fixed          1.442            11.28     the same shot with the bodywork
                                              smeared;  -5.9 % mean, -27 % p99

That is the trade, stated plainly: **about 25 near-nadir frames lose peripheral
detail so that 13 frames with the world in them stop being on their side.** In a
one-take film the second is not optional and the first is a softening, not a
break — but it is a real cost and it was paid, not avoided.

**AND THERE IS A GENTLER SETTING THAT NOBODY HAS LOOKED AT.** Cone 0.15 at rate
**8** does not level the peel-off; it lands it on a decaying BANK:

    f2658  32 deg   f2666  19 deg   f2673  2 deg   f2675 onward  level

which is the shot R2-091 described and liked, at a shallower angle than the
-36.97 deg of f2680 that was rendered and accepted — and it costs less smear,
18.92 % against 22.07 %. It is not shipped because it leaves **13 frames over
this gate's 10 deg bound**, and taking it would mean writing a waiver for them.
**Not one of those 13 frames has been rendered.** R2-091 is exactly what happens
when a waiver is written before the frames exist, so the setting is recorded with
its numbers and NOT adopted. If the banked peel-off is wanted, render ref8's
f2658 and f2666 first and let the pictures decide.


## R2-113 — the closing hold was a freeze, and no single lens can show the circuit and the wound

The last 3 s is **0.00 m of camera movement over 72 frames**, so at a fixed lens
f2906 and f2978 are the same picture: mean |difference| **0.8/255**, 56 pixels of
2.07 M differing by more than 16. It is not a held frame, it is a still.

R2-090 closed the car: it and the wound are **966 m apart** at f2978, and
requiring both in frame pushes the camera back at exactly the rate a longer lens
gains, so the car is pinned at `1920 × 5.698 / 966` = **11.3 px** from any
position at any focal length. The car's beat is real and lives at f2756–f2832.

The other two subjects are resolved **in sequence rather than in one frame**:

| lens | mullion pitch | sky in frame | the wound | the circuit |
|---|---|---|---|---|
| 18.75 mm | 3.7 px | 29.3 % | 20 px — no resolvable grid to be a hole *in*; reads as a specular hit | 1143 m |
| 40 mm | 7.9 px | 5.7 % | 37 px | 536 m, reads best |
| 74 mm | 14.6 px | 0.0 % | 65 px — grid crisp either side and **absent** across the middle, dais ring legible through it | 290 m, gone |

So the hold **opens at 40 mm and pushes to 74 mm**. Two lens keys move and
nothing else: no key moves in time or space, the hold's two keys keep their
identical positions, and the built path is **0.0022 m over the 72 frames** with
the aim gate at 0.06° and frame-offset 0.001.


## R2-114 — a gate's default input was a generation old, and its own negative control failed because of it

`horizon_gate.py --selftest` reported `HORIZON_GATE_SELFTEST_BROKEN` on a clean
tree. The N1 arm — *beats 2 to 5, 1,808 frames, must PASS* — came back FAIL with
**155.65° of roll at f1464** and 50 FAIL frames.

f1464 is fine. The gate defaulted to `render/film11_path.json`; film12 was built
twenty minutes later with R2-085's fix in it and the default was never moved. On
film12 the same frames read −0.00° and the arm passes.

> **A negative control that fails because its INPUT is stale is
> indistinguishable, on the printed line, from the gate being broken** — and this
> file had just been used to publish R2-088.

The default is now `world/camera_rig_path.json`: the camera rig's own output,
which `build_camera_rig.py` writes and `build_film_scene.py` consumes. A numbered
`film*_path.json` is a snapshot of it and there is a new one every time anybody
assembles a scene. **Deliberately not "the newest film\*_path.json"** — picking up
whatever a passing agent dropped in `render/` is how a gate ends up judging
something nobody chose. Instead a check refuses to let the named default rot: if
the newest assembled film scene holds a *different* camera from the rig, the gate
says so and names the file, because the rendered frames come from the scene.


## R2-115 — the positive control was anchored to a defect, and fixing the defect took the control away

`horizon_gate.py`'s P3 arm read *"the **live** `--path` over f2640–2700 must
FAIL"*. It was the arm proving the gate fires on a rolled camera. R2-112 levelled
that roll, so P3 began reporting *expected FAIL, got PASS* on a healthy film.

**The version that would have been worse is the one that looks better.** Had P3
been written as a bound — "at least N FAIL frames", "no better than X degrees" —
it would have gone **quietly green** the moment the roll was fixed, and the gate
would have had no positive control from that instant on with nothing on the
printed line saying so. That is R2-072, for the second time on this project.

**A positive control cannot be a defect in the artefact under test, because the
whole point of the work is to remove it.** So the rolled camera is kept:
`docs/horizon_pre_R2112_path.json` is the shipped pre-fix path — 28 inverted
frames, −122.93° at f2657 — and P3 asks the gate to fail it forever. If the file
is missing, the arm FAILS and says the gate has no positive control, rather than
being skipped. In `docs/` and not `work/`, for the reason `seam_gate` already
gives about its own `--pre` control: work/ is gitignored, and a control a tidy-up
can delete is not a control.


## Open, and deliberately not given a number without being asked

**The peel-off's BANK is gone, and it was not a design.** R2-091 waived f2680's
−36.97° because it "reads as a banked aerial — the shot a helicopter makes
peeling away from a subject". That bank was the tail of the 176° runaway bleeding
off at the limiter's rate, so removing the runaway removes it: the fixed f2680
measures −17.5° of dominant edge against the level reference of −28.5°, i.e.
level. Rendered, it is a clean legible aerial down the pit straight, and it is
flatter than the frame R2-091 liked. **The bank cannot be kept without keeping
the runaway that produced it** — every swept value either leaves the inversion
(rate ≤ 8) or removes the bank with it (rate ≥ 10). If a banked peel-off is
wanted it has to be AUTHORED as a declared roll on beat 6, which is R2-089's own
closing recommendation and is a change to the beat sheet, not to `look_quat`.

**Nothing in this film gates how fast the lens moves.** `campath_gate` computes
`dlens = np.abs(np.diff(L))` and then never uses it — a dead variable, no
detector, no bound. R2-113 introduces the film's largest single lens move, so it
was measured against the film instead: converting focal length to the motion it
puts on a frame-edge pixel, the push peaks at **0.659 % of frame width per frame
at f2935**, against **2.787 % at f2254** which beat 5 already ships. The push is
4.2× gentler than a lens move already in the film. That is a measurement, not a
gate, and the gap is real.

## R2-116 — `spectator_seated` is UNMEASURABLE, not failing, and `distinct_shapes` never had a case to answer

The standing suspicion was that this foundation item — **8 dependants** — passed `distinct_shapes`
on a technicality. **Refuted, with numbers**: 7,420 realized instances, 420 sources, **420
distinct shapes against a required 40**, commonest shape **0.4 %** against a 25 % limit.

That check exists specifically to catch *"420 datablocks holding 6 poses"*, so the agent did not
stop at the shape count. `build_library` stamps `ob["posture"]` on every source, making the
posture vocabulary **readable rather than inferable**: **14 distinct base postures, top posture
13.67 %**, against the manifest's own "8–12 base postures". Artefact arm and runtime arm agree at
14. The positive control — 420 specs with `force_posture` fixed — returns **1 and FAILS**, so the
instrument can see the defect it exists for. **The "~6 poses" charge belongs to the wave-1
*render* in `HUMAN-FIGURE-BRIEF.md`, not to this module.**

**Under the current 8-check gate the verdict is `ITEM_UNMEASURABLE`** — 7 PASS, **0 FAIL**, 2 NOT
MEASURED. The gate's own words: *"nothing FAILED, but 2 checks could not be measured at all. That
is not a rejection, it is a gate that could not look."*

So the 8 dependants are **not standing on a failing foundation** — the interface they read is
unchanged and the geometry is bit-identical to the build they were written against. **They are
also not standing on an accepted one.**

**Two things had to be unpicked to get there.** The first gate run returned `ITEM_REJECTED` **on
0 subject pixels**: the median-triangle subject picker chose one of the 420 library sources that
`build_library` sets `hide_render=True` on by design — confirmed by opening the witness blend,
not inferred. Re-run against the median-triangle *renderable* object (381 renderable, 420
excluded), `surface_microstructure` moved **NOT MEASURED → PASS** at ×352.22 against ×2.00.

## R2-117 — `item_gate`'s `result` field is two-valued and there are three outcomes

`item_gate.py:3317` writes `"result": "ITEM_REJECTED"` **before** `:3449` decides to refuse. The
stored JSON therefore says REJECTED while the run says UNMEASURABLE.

**`result` has no cell for the third outcome**, and R2-108 records that reports are read
canonically from exactly that field. A gate that cannot look and a gate that looked and rejected
are opposite findings — one is "fix the item", the other is "fix the gate" — and they are
indistinguishable on disk. Annotated in place with a `REPORT_STATUS` block; **the field itself is
unfixed and owned elsewhere.**

## R2-118 — `relief_sweep.sh` was structurally unable to refresh anything

It skipped any item that **already had a report**. Over a corpus where **28 of 30 reports
predated their own witness**, it printed `HAVE` thirty times and **exited 0** — a clean run that
could not have refreshed a single stale number under any circumstances. It also called bare
`blender`, i.e. the CUDA-less one.

Now it skips only a report **newer than its witness**, supersedes stale ones, and judges on the
file it wrote.

**Result of actually running it: 28 of 30 relief reports moved.** `bump_height_unlinked` cleared
to **0 on 14 items and is now 0 across all 31 current reports** — no item in the corpus has a
dead Bump Height. **Three moved *down*** — `heras_fence_panel` 8.996 → 3.181, `tyre_wall_tyre`
7.656 → 1.577, `paddock_personnel_figure` 3.586 → 3.014 — so those published numbers were
*inflated*, not merely stale. Two genuinely did not move, and one of those (`terrain_ground`) is
an item whose **geometry did move**, which makes it a real null rather than an untouched row.

Witnesses were restaged before auditing, because **re-auditing an old witness republishes a
number about an artefact that no longer exists.** The new `relief_audit_control.py` generates a
procedural Bump-on-noise and the same scene with that one Height link removed **live each run**,
so it cannot expire (R2-072).

## R2-119 — the staleness census under-counted by half: 30 of 32, not 15

`--stale-census` compares a blend against `world/items/<module>.py` **and nothing else**.
Measured against the whole import closure — two arms, static AST and a live `sys.modules` read —
**30 of 32 blends are stale, not 15.** Sixteen rows the own-mtime rule scores CLEAN are older
than `itemkit.py`, `world_contract.py`, `build_surface.py` or `humankit.py`.

> **This is R2-070's shape again, with the census standing in for the author who can only see
> call sites inside their own file.** A staleness rule that looks only at the module's own source
> is blind to exactly the dependency that made the last twenty defects.

**The runtime arm was wrong first, and its own census said so:** importing 32 modules into one
interpreter meant a `sys.modules` diff credited a shared helper only to whichever module loaded
it first — **"runtime 0" on 31 of 32 rows.** Fixed with a per-row purge and a second-import
control. The two arms now disagree on **8 of 32, in both directions**, so both earn their keep.

## R2-120 — 16 rebuilds, 6 moved, and not one verdict moved with them

10 of 16 rebuilt **bit-identical**; 6 moved. **Not one socket verdict changed** — 16 PASS before,
16 PASS after, with `--selftest-blend` passing all four arms on both sides, so it is a
discriminating pass rather than a blind one.

Build flags are **not uniform** and assuming they were is R2-108: **9 `--save`, 7 `--out`, 3 with
a verb other than `--test`, and `showroom_facade_panel` takes no build verb at all.** Two modules
are STATIC ONLY (hand-rolled parser) — `crew_fireproof_overall` and `marshal_post_column` — both
verified by sha256 *and* by reading the rebuilt file.

**A determinism arm was added because these modules are procedural**: *"the geometry moved" is not
evidence of a source change if the module reseeds.* Every mover was built twice and returned
identical. Where a rebuild was bit-identical to a days-old build the arm was skipped as
`DETERMINISM_ENTAILED_BY_BIT_IDENTITY` — **validated first on `spectator_seated` by running it
both ways**, where the arm agreed with the entailment.

Largest movers: `gravel_bed_surface` max bbox shift **19.39 m** (3 objects gone, 3 new);
`paddock_personnel_figure` figures **12 → 260**, triangles **971,807 → 15,150,788** — and **its
tracked `*_interface.json` was written 2.6 h *after* the blend beside it**, so the published
contract was never describing that artefact.

## R2-121 — the gate overwrote a witness pair that a previous defect had deliberately protected

`item_gate` derives the witness **blend** path from the item id, and `--witness-dir` does not move
it. So re-gating `spectator_seated` overwrote `spectator_crowd`'s witness — **the pair R2-061 was
written to protect.** Caught and restored; backup at
`render/gate_witness/_r2116_spectator_crowd_witness_backup/`, wave-1 pair preserved at
`render/gate_witness/spectator_seated_wave1/`.

**A flag that redirects some of a tool's outputs and not others is worse than one that redirects
none** — it reads as isolation while writing outside the sandbox.

## R2-132 — the pit-exit hole is 390.15 m², not 32.25, because the probe's window was the defect's edge

The seam was recorded at **32.25 m²** since contract 1.1.0. It is **390.15 m²** — twelve times
larger — and the reason it stayed small is the finding:

> **`probe_pitexit` samples u 10–16. The defect runs u 10.50–40.40.** Its own reported `u_range`
> maximum is **`15.999…`** — *its window edge.*

**365.75 m² had never been looked at by anything.** The 32.25 figure was additionally a
grid-resolution delta measured on `assembly3` at contract 1.1.0, so it was a small number about a
small window on an old world, carried forward as though it described the defect.

**A probe whose reported range maximum equals its own window boundary is clipping, and that
number should always be read as suspicious.** Nothing in the report said "truncated"; the only
evidence was that the maximum landed one part in ten thousand under the limit.

**Three defects that had never been written up, now measured:**

- **paint over void — 7.10 m²**, strokes laid where there is no substrate beneath them.
- **paint floating up to 367.9 mm above its substrate.** `ARCH_Markings` is **one flat plane** —
  all 7,166 vertices at z = 0.007 — so it cannot follow ground that rises or falls under it.
- **the glass mouth's 100 mm sink — REFUTED.** Exactly **4950 = 110 × 45** samples, precisely
  round-1 `Floor`'s footprint, and `build_film_scene` **hard-refuses** unless that Floor's top is
  z = 0.000. This is the one of the four already closed by work since 1.1.1.

**Fix proven on a test build**: 380.65 → **2.70 m²** unbuilt, 6.20 → **0.00 m²** paint-only, apron
5881.5 → 6421.2 m². **Both gate failures are pre-existing** — established by building HEAD as a
control *after* the agent had wrongly reported them as its own regression. The fix takes them
2 → 1.

**A world rebuild is owed.** No vertex has moved in `assembly8`, so `film12` and `film13` are both
built on the defective world.

## R2-133 — the line of sight to a region is not the camera's view-axis pitch

The geometry says 390 m² of void. **The render shows continuous asphalt** — mean RGB
(49.2, 48.1, 48.6), sd ~5, edge-energy 1.76, against known-good track at (51.3, 49.6, 48.8),
sd ~6, 2.18. **Statistically the same material.**

Two camera analyses disagreed by 21° on the same shot — one said −20.9° look-down, the other
−42°. **−20.9° is right**, read from `film12_path.json` where the view-axis pitch holds −20.85°
to −21.05° across the span; the −42° was wrong and was withdrawn by the agent that had relayed
it. So the crops examined the right ground.

**But the distinction that resolves the conflict is one neither analysis had made:**

| frame | line-of-sight to ROI | distance | off-axis |
|---|---|---|---|
| f1098 | −14.4° | 52.5 m | 25.4° |
| **f1104** — the frame all the pixel work was done on | **−18.7°** | 44.7 m | 17.8° |
| f1112 | −28.3° | 33.1 m | 9.7° |
| f1114 | −32.0° | 30.1 m | 11.4° |
| f1119 — **never rendered** | **−45.9°** | 22.9 m | 27.2° |

**The region sits below the view axis, so its line of sight is steeper than the camera's pitch —
and f1104 is the *shallowest* view of it in the entire span.** The hole map casts straight down.
*"No hole visible at 18.7°"* and *"383 m² of void measured at 90°"* are **not in conflict; they
are answers to different questions.**

**It was not turned into a waiver, and that is the right call** — *"a coherent explanation, not a
measurement."* Inferring "therefore invisible" from frames that bracket the question is precisely
the R2-091 failure, one entry of which was written earlier the same day.

**What remains genuinely open is the commercially important half:** whether the void ever presents
to a **beat** camera at all. The film shows this ground only from the ONER, at 14–46° line of
sight, partly occluded by the pit wall — and the steepest frame available has never been rendered.
**A 390 m² hole nobody can see from the only camera that exists is a different priority from one
that reads on screen, and nobody yet knows which this is.**

What *is* visible, at 8× on f1104: the pit-lane strokes **terminate with blunt, abrupt cut-off
ends in open ground** — they do not fade, do not run off-screen, do not continue onto anything.
That is defects 1 and 2 in pixels.

## R2-150 — the occluded half of the same region is the control, and it is internal

f1104, rendered from film13 (defective world) and film14 (apron laid), ONER, 4K, 256 samples,
same farm. The floor is a **repeat render of film13 against itself**.

| region | px | changed >8/255 | repeat floor | mean \|Δ\| |
|---|---|---|---|---|
| **VOID, unoccluded — the claim** | 5,669 | **74.40 %** | **0.00 %** | **36.27** |
| **VOID, hidden by the pit building in BOTH** | 6,821 | **1.47 %** | 0.00 % | 2.04 |
| VOID, all in-frustum (earlier lower bound) | 12,490 | 34.57 % | 0.00 % | 17.58 |
| CTL_PAVED / CTL_SKY | 5,066 / 660,480 | 0.00 % / 0.00 % | 0.00 % | 0.30 |

> **Row 2 is the strongest control in this entire log, and it costs nothing to obtain.** It is
> the *same void region*, in the *same two builds*, under the *same fix* — differing only in
> that a wall stands between it and the lens. It must not move. At **1.47 % against 74.40 %**
> it does not.

A repair that "showed up" behind the wall as well would have been light leaking in from
somewhere else, and no external control could have distinguished that. **Where a fix has a
region the camera cannot see, that region is a free negative control — use it.**

Unoccluded void mean RGB **(72.0, 64.8, 57.1) → (108.2, 96.0, 81.2)**, about half a stop
lighter, because a lit concrete apron is now there.

**It independently reproduces the diagnostic camera by a different route.** R2-132's
purpose-built camera cast straight down and got **78 % changed against a 1.33 % control**; this
is the film's own ONER at 16.7–34.4° line of sight, a different scene and a different
instrument, at **74.40 % against 1.47 %**. The geometry agrees too — **70.86 m² unoccluded of
156.12 in frustum**, against R2-140's separately measured 71.50 of 157.50.

**Two process notes, both paid for in wall clock.** The first raycast used `scene.ray_cast`,
walking a depsgraph BVH over **29,415 objects — 28,314 of them vegetation nowhere near the pit
exit**; it ran an hour without finishing and was killed. R2-140 had **already named every
occluder of this region**, so casting against those four objects' own BVHs answered the same
question in three minutes, and the blocker census returning `ARCH_PitBuilding_Shell` 6,821 and
nothing else is what confirms the narrow question was the right one.

And the rewritten script **died on `No module named 'PIL'` while Blender exited 0.** The printed
`STAGE RESULT` line caught it; `$?` would not have. That rule earned its place again.

## R2-171 — `build_sky` never reads `SKY_IRRADIANCE`, and the shortfall constant is a plug

The standing description — *"`C.SKY_IRRADIANCE` is 0.123 stops low"* — is **arithmetically the
wrong statement.** 0.123 stops is what the shortfall **costs the film**; the sky term itself is
out by **log2(11.1818 / 8.4593) = +0.402 stops**, ten times the instrument's floor rather than
three. It reads as 0.123 only because the sky is 8.459 of a predicted 25.985 W/m², diluting the
error 3.07×.

**Neither "the constant is wrong" nor "`build_sky` delivers more" is the right frame.**
`build_sky` never reads the constant at all — its Background Strength is a literal 1.0. The
constant is a **downstream description**, and `calibrate()` bakes it from a throwaway `CAL_world`
holding one bare Sky Texture, while `build_world()` — *the film's world* — is that node **plus
three alpha-composited cloud decks**. Measured on `calibrate()`'s own rig:

```
bare Sky Texture at the contract's parameters   8.4602   +0.0001 stops   <- positive control
build_sky.build_world(), untouched             11.1524   +0.3987 stops
the same world, three deck factors forced to 0  8.4602   +0.0001 stops
```

**The decks are 100 % of the gap**; the aerosol mottle is 0.000 of it. Two rigs agree to 0.0038
stops. **So the constant is an exact measurement of a sky the film does not build.**

**Decision: do not fix it.** Re-baking to the shipped sky moves `FILM_EXPOSURE` −3.628 → −3.653.
The shipped value sits **+0.0063 stops** from the 5090's measured −3.6343; the "corrected" chain
sits **−0.0187**, three times further out. **The present chain is wrong twice with opposite signs
and the errors cancel to 0.006 stops.** A re-bake would also fail the contract's own
`DIRECT_TO_DIFFUSE` assertion (2.072 vs 1.572), move `lambert_radiance` — the material
calibration law of the whole film — and is **circular**, since `CUMULUS_SHADE` is computed *from*
`sum(SKY_IRRADIANCE)/3`, making a re-bake a fixed-point iteration rather than an assignment.

**Two findings recorded rather than acted on.** The **tint is out by more than the level**: the
decks add +1.076 / +0.464 / +0.054 stops per channel, so against a published
`C.SKY_TINT` of (0.3115, 0.5582, 1.0000) the shipped sky measures **(0.6323, 0.7412, 1.0000)** —
the film's fill light is far less blue than the contract says, and at least one item's shading was
reasoned from the published tint. And **`SKY_SHORTFALL_STOPS = -0.117` is a plug, not a
measurement** — the measured value is **0.1231**, quoted three lines above it, and −0.117 was
chosen so that `round(-3.048 - 0.463 - 0.117, 3)` lands on the shipped −3.628.
`SKY_SHORTFALL_MEASURED_STOPS` now publishes the real number beside it.

## R2-172 — inverted glass: catastrophic for a solid, invisible for a sheet

`GW_Front_Glass_00..13`, the 30 × 6 m south glazing, is wound **inconsistently across one flat
wall**: panes 00–02 and 11–13 face **+Y, into the showroom**; panes 03–10 face out. Six of
fourteen. `Vitrine_Glass_2` is the same defect on a display case. Both are inherited **verbatim
from round 1's `f1_showroom.blend`**. The ten `GP_b*` breach panes are **clean**, verified two
independent ways (analytic face table +0.0805 m³; measured in the built blend, 0 inward pieces,
+0.150354 m³).

**The answer splits by geometry, and only one half was what anyone assumed:**

| invert every pane | |
|---|---|
| **closed solid**, 11.5 mm, east wall | **1,281,402 px, mean 34.244 — 89 % of frame** |
| **zero-thickness sheet**, south wall | **1,291 px, mean 0.00091** |

For a closed solid, inverting costs **196 % of deleting the glass entirely — an inside-out pane
is worse than no pane.** For a single interface there is no interior for Cycles to get the wrong
side of, so the Fresnel and the bend stay symmetric. **The panes that are wrong are all
zero-thickness; the panes with real thickness are all right.** Net cost as shipped: **568 px,
max 3/255**, and the pixels that move are exactly the six mis-wound panes (00/01/02 move
0.003–0.004 levels; 03/04/05 move 0.000).

**The control that made the verdict non-vacuous was "delete the glass entirely"** —
1,402,932 px, mean 12.515. Without it, the south result would have been indistinguishable from
*"this camera cannot see the glass at all"*.

**And the first rig was refuted by its own positive control.** Five variants in one blend at
2–8 km offsets, to save a scene push: inverting all fourteen panes moved the picture **1.583
levels against a null of 1.618**. At 8 km float32 spacing is ~1 mm and many-bounce interior paths
diverge chaotically. Rebuilt as one variant per blend at identical coordinates, the null drops to
**25 px of 1.44 M at one 8-bit level**.

## R2-173 — the metric went to zero while the defect got worse

`TS_Stand00_BOREAL`'s deck **walking surface** — 2.903 × 2.834 m at z = 0.6793 — has mean normal
exactly **(0, 0, −1)**, with the sheet below it at 0.6513 facing **+1**. The slab is built upside
down, along with three step treads and the console worktops: **9 inverted slab pairs, 22.953 m²,
18.33 % of the object's area facing straight down.** `marshal_post_deck` has the same defect at
1.267 m².

**It is on screen 493 of 2,978 frames**, peaking at f1126 in beat 4 — camera at z = 16.7 m
looking down on a deck at z = 0.68 from 25.4 m, so **the reversed side is the one presented to
the lens** — at **426 px across, 11.1 % of frame width.**

**Why the repair could not catch it:** signed volume is undefined for a zero-thickness sheet, so
`--fix` correctly abstains. The `timing_stand` repair flipped 1,310 pieces and drove
`inward_area_frac` **0.3436 → 0.0**, while `piece4721` **stayed the largest back-face contributor
and went from 26 to 28 of 500 rays.**

> **The headline metric reached zero while the actual defect got marginally worse.** A summary
> statistic that a fix can satisfy without touching the fault is not a verification.

`winding_audit --sheet-facing` now pairs coplanar sheets and names a pair inverted when the upper
one faces down, with both synthetic controls run every time and **`SHEET_FACING_UNMEASURED`
rather than `OK`** when nothing horizontal is found. Its own first version **wiped the scene
before `collect()` and printed `OK` on an empty blend.**

## R2-179 — `extrude()` reversed the wrong cap, and signed volume is structurally blind to it

Three sites, one class, and **none of them was in the deck code.**

**Site 1 — `extrude()`, both modules.** `_grid_quads` gives the side quads normal `t × e`, outward
for a CCW ring. For that same ring the **start** cap's outward normal is `−e` and the end cap's is
`+e`. Both files reversed the **end** cap. **Every solid in both modules was a correct tube with
both lids facing into itself.**

**Why `Acc.solid` could not catch it, which is the part worth keeping:**

> Every face of a box contributes `V/6`. Four right sides and two wrong lids integrate to
> **+V/3 — positive, no flip — on a solid a third of whose area is wrong.** On the 2.903 × 2.834 m
> deck slab the lids are **98.07 % of the area.**

Corroboration that the corrected convention is the project's own: `hospitality_deck.py` already
writes `reverse=True` on the *start* cap, and its slabs were always clean.

**Site 2 — `box()`, both modules.** The bottom quad walks +x then +y round the underside: CCW from
above, normal +z, into the box. **`Acc.solid` integrates about the world origin**, so that face
contributes `area · z0 / 3` and **vanishes for a box sitting on z = 0** — precisely the case it was
eyeballed against.

**Site 3 — `slab_grid()`, found only after the first two were fixed.** Top quads wound −z, and two
of four edge strips inward. **A mixed winding has no meaningful signed volume**, and `Acc.solid`
decides the whole slab's orientation from it — so **whether a hut floor came out the right way up
was a function of where it stood.** 24 of 25 decks were flipped back by luck; `MPD_Deck_05_hut` at
z = −1.03 was not, and shipped 1.513 m² of floor facing down.

| `timing_stand` | before | after |
|---|---|---|
| inverted slab pairs | **138** (175.442 m²) | **0** |
| `inside_out_fraction` | **0.48000** | **0.02400** |
| objects / facets / slab pairs / triangles | 14 / 1456 / 532 / 3,087,808 | *identical* |

All ten `TS_Stand*` appear before, none after. `marshal_post_deck` 72 → 1 → **0**.

**Note which number moved.** `inward_area_frac` barely shifted, **0.3733 → 0.3363**, because it
counts the volumeless sheets signed volume abstains on — *the exact figure the previous repair
drove to 0.0 while the defect got worse* (R2-173). A fix that leaves the headline nearly still and
moves the fault is the right shape; the reverse is the warning sign.

`slab_grid` is now checked **at five heights**, which is the control that would have caught site 3
on day one. Restoring the old wiring at runtime fails **9 of 9** primitive checks in one module and
**4 of 4** in the other.

## R2-180 — the item under test was chosen by "biggest collection wins"

`collect()`'s `cands = pick or cands` fell through to *"any item collection, take the biggest"*
whenever the `--item` name matched nothing. And the naming convention is not one convention:
`W_Item_TimingStand` / `ITEM_MARSHAL_POST_DECK` / `PDS_Deck` + `PGD_Girders`.

`hospitality_deck`'s own collection carries no `W_Item_` prefix, while its **context** ships 41
`W_Item_PaddockPavingBay*` collections whose 54 members are **instancer empties holding no
polygons**. So the detector measured another item's floor, found zero objects, and returned a clean
zero.

Now: `ITEM_` is in the convention, **a collection with no qualifying mesh can never be the
subject**, an unmatched `--item` falls back to the **scene** and never to a different item,
`>> SUBJECT:` is printed every run, and **`NO_SUBJECT` is a separate verdict from `UNMEASURED`.**
Reads 5 objects, 15,693,726 triangles, 504 slab pairs, 0 inverted.

## R2-181 — a welded slab's mean normal cancels, so the detector reported zero

`sheet_facing` grouped by **connected component** and took its mean normal. That works only where
the walking surface *is* its own component — true in `timing_stand` because `extrude` duplicates
cap vertices. **A welded manifold slab puts top, soffit and sides in one component whose mean
normal cancels**, so a bridge deck reported "0 flat pieces". Now grouped over connected runs of
near-horizontal triangles *of the same sign*, with every rejection counted: 13 objects,
30,943,406 triangles, 34 slab pairs, 0 inverted.

**The change costs a false-positive class and it was closed properly rather than tuned around.**
Facet grouping sees inside grooves, and a slot floor under a lip has the *same signature* as an
inverted slab — 15 such pairs from a T-slot profile whose opposing slots are cut deeper than half
its 18.6 mm height, so the cavities meet and the profile runs back along itself. Settled by two
independent arms: a winding-independent **vertical ray-parity** test and a **closure test on the
pair's own welded component**. The file records the two candidates that failed first —
`enclosure_q` measures chunkiness, so a 4.5 m purlin scores 0.0025 against a 0.005 bound; `tri_piece`
is split by the duplicate cap vertices. **Ten controls, built live, both directions each.**

## R2-182 — the item is not in the world, and a before/after render would have proved nothing

`timing_stand` **has never been placed into the shipping world.** `TS_` appears **0 times** in
assembly9's 28,781 objects, and `TS_Stand` / `W_Item_TimingStand` / `MPD_Deck` appear **0 times** in
the 4.53 GB `film14.blend` — with `ARCH_PitWall`, which does appear, as the positive control.
`docs/screen_presence.json` nonetheless scores the item against `hosts: ["ARCH_PitWall"]` and peaks
it at **631 px in beat 4**.

**Rendering f1126 from the film before and after the fix would have produced two identical images
— and been read as "the fix is invisible, close it".**

The camera was right; the world was not. Planting the film's own f1126 camera into the item test
blend instead, at 4K / 256 spp / denoiser off / seed 0 / grade −3.628:

```
null (AFTER rendered twice)        260 px of 8,294,400, max 1 level
whole frame                  1,378,182 px (16.62 %), max 87   -> 5,301x null
TS_Stand00_BOREAL's box         60,077 px (10.47 %), max 11   -> 5,462x null
```

**Why it survived every check: a reversed face does not render black.** Cycles flips a back-facing
normal for diffuse, so an upside-down deck shows as every chequer rib and tread nosing **lit from
the wrong side** — wrong, plausible, and invisible to any check looking for absence.

**The open question this leaves is larger than the defect:** an item can be gated, tiered, and
scored for screen presence while being **absent from the ship**. Wave 2's entire 113-module scope
was drawn from measured screen presence, so **how many others are in this position is now worth
knowing.**

## R2-148 — assembly9: one object of 28,781 moved, and for the first time it was a vertex COUNT

`world/build_architecture.py` was fixed at `54dd6b8` (22:06). `assembly8` was built
at **19:38**. R2-132's own closing line says it: *"A WORLD REBUILD IS OWED. Nothing
here has moved a vertex in assembly8."* `film12` and `film13` were both built on the
defective world. This is that rebuild, read back from the file.

| | assembly8 | assembly9 |
|---|---|---|
| objects | 28,781 | 28,781 |
| total verts | 1,282,465,803 | **1,282,477,674** (+11,871) |
| objects moved | — | **1** |
| bit-identical | — | 28,780 |
| different vertex COUNT | — | **1** |
| materials moved | — | **0 of 132** |

`ARCH_Paving_ApronPlatform`: **128,722 → 140,593 verts (+9.222 %)**. Five of its six
bbox extremes are **bit-identical**; the sixth, `bbox y max`, moved **46.8 mm**.
`apron_platform_m2` **5881.5 → 6421.2**, reproducing R2-132's test-build figure
exactly in the full assembly.

**a5→a6, a6→a7 and a7→a8 all held 1,282,465,803 vertices to the digit.** This is the
first assembly diff in this project where the count moves at all, because the fix
does not *shift* a slab — it *lays* one.

**The prediction was written at 22:48 while `build_architecture` was still building**
(`v124/PREDICTION.md`), and one part of it is wrong. It predicted the bbox would
extend outboard. **It does not**: the slab grew entirely inside its own envelope and
the one extreme that moved went *inward*. The apron sweep curves, so its bounding box
was already set by the stations where `platform_edge` is widest, and the released
ground fills in behind that line. **Direction of the finding right, stated shape of it
wrong, and it is recorded as wrong rather than quietly dropped.**

The half that was *not* obvious and had to be checked rather than assumed:
`build_terrain` and `build_dressing` run **after** `build_architecture`, so "they were
not edited" is not sufficient on its own. Every `ray_cast` in `build_terrain` is inside
`test_scene()`, `selftest()` or `bake_cameras()` and **none is reachable from
`build()`**; `build_dressing` has none; `embed_ground_contacts` and `cull_unowned` both
query `world_ground_z` (the model) and never the apron mesh; and every builder in
`build()` takes its own freshly seeded `random.Random(20NN)`, so a bigger grid
consuming more draws cannot perturb what follows it. All four held.

**`build_architecture`'s own contract gate goes 2 failures → 1.** BLACK recesses
5 → 1; *"no ARCH mesh coplanar with another module on the Beat-4 route"* **FAIL (2
samples, both `ARCH_Paving_ApronPlatform`) → PASS (0)**. And *"paving stays inside the
contract's declared rectangles"* goes 35,474 → **40,184** up-faces with **0 outside**,
which is the row that says the fix did not spill the way its first version did.

`fp_diff.py` was run with four controls in one batch: its own 7-arm `--selftest`, the
a5→a6 pair where `BR_Transit_NorthWall` is known to have moved 3.1885 m (reports 1,
3.1885 m), and a **negative arm that declares `--expect-moved 0` on this pair and must
exit 1** — it does. R2-111 repaired this file because it computed `moved`, printed it
and never consulted it; the expectation is now declared on the command line.

---

## R2-149 — film14 on assembly9: 37 of 37 readback fields identical, and the camera is byte-identical

The full chain was re-run in order — `author_beats2_5.py` → `build_camera_rig.py` →
`build_film_scene.py` — with **no `--world-override`**; `SHIPPING.md` was updated to
declare assembly9 first, so `refuse_unless_world_is_declared()` is satisfied honestly.
Both world guards printed clean: *"WORLD: assembly9.blend, the ship declared in
SHIPPING.md"* and *"WORLD STALENESS: none"*.

**Two nulls, and they are what make the pixel comparison below a world comparison:**

* `docs/beat_sheet.json` sha `2ee973b8` **before and after** the author pass — it is
  idempotent, as r2100 and r2127 both measured.
* `world/camera_rig_path.json` sha `f1c65c46` before and after the rig build, and
  `render/film14_path.json` is **the same sha as `render/film13_path.json`**. The
  camera is byte-identical across the two films. **The only thing that differs between
  film13 and film14 is the world.**

| readback, from the saved blend | film9 (broken) | film13 | **film14** |
|---|---|---|---|
| interior lamp load | 3,737.113 W | 46,203.313 W | **46,203.313 W** |
| `_sl_base` lamp stamps | 0 | 23 | **23** |
| `scene_mark` | null | 3.628 | **3.628** |
| `assert_levelled` | REFUSED | PASS | **PASS** |

`readback_diff.py`: **37 fields compared, 37 identical, 0 differ.**

The levelling identity **recomputed from film14's own `_sl_base` properties**, not
quoted: base 3,737.113 × 2^3.628 = 46,203.306 against **46,203.313** measured,
residual **0.007 W**, worst per-lamp ratio (`WallWash_BackUp`) 12.363369363 against
12.363368794 — nine decimals, so no lamp hid inside the total. Deck top 0.3400, floor
top 0.0000, frames 1–2978 @ 24, scale 1.0, 28 Vitrines / 0 parented to `CAR_ROOT`,
camera `ONER` clip 0.05 / 200000, exposure −3.628 AgX.

**Gates, each with both controls:**

| gate | artefact | control |
|---|---|---|
| `horizon_gate --selftest` | 7/7 | includes P4, the 170°-rolled synthetic |
| `horizon_gate` f2600–2714 | **1.71° worst, 0 FAIL, 0 WARN, 0 inverted** | pre-R2112 path **FAIL**, −122.93°, 28 inverted, 32 FAIL frames |
| `horizon_gate --census` | bounds lie strictly between 2.48° and 122.93° | — |
| `seam_gate --selftest` | **7/7** on the repaired default `world/camera_rig_path.json` | three must-fail arms |
| `seam_gate` artefact | chord **2.0893**, speed **1.2727**, look **13.2504**, lens **−0.051**, SEAM_OK | — |
| `socket_index_audit --blend` | film14 **PASS**, 226 trees | film10 **FAIL, 27 findings**; film13 PASS |
| `campath_gate` | **PASS, 0 FAIL, 5 advisory** | see R2-151 |

**R2-103's floor was paid attention to rather than re-derived.** `path_diff.py` run on
`film14_path.json` **against itself** reports **1,429 of 2,978 frames "MOVED"** and
0.2032° of rotation. The strict componentwise comparison on the same self-null reports
**0**. Only then was film13 → film14 compared: **0 / 2978 position, 0 / 2978 rotation,
0 / 2978 lens.**

---

## R2-151 — `campath_gate`'s positive control passes, because the gate has no roll term at all

Running the control is the only reason this is known. `docs/horizon_pre_R2112_path.json`
— the path with **28 fully inverted frames and −122.93° of roll**, which `horizon_gate`
fails with 32 FAIL frames — goes through `campath_gate` and returns:

    >> STAGE RESULT: PASS — 0 FAIL, 5 advisory

**the same verdict, and the same five advisories, as film14.** `campath_gate` measures
speed, rotation RATE as a fraction of frame width, and path kink. **It has no roll or
up-vector term**, so a camera that is upside-down for 28 frames is invisible to it.

That is consistent with R2-088 — `horizon_gate` exists *because* nothing measured roll
— but the consequence is specific and was being missed: **a `campath_gate` PASS
reported next to that path as its "positive control" asserts nothing.** Two paths that
DO discriminate, and either should be used instead:

    docs/seam_pre_R2064_path.json   FAIL — 1 FAIL, 6 advisory  (C1_rotation_smear
                                    51 % of frame width/frame at f1461)
    render/film9_path.json          FAIL — 2 FAIL, 12 advisory

---

## R2-152 — `54dd6b8`'s own commit message quotes grid numbers that do not reproduce in the assembly

Small, and exactly the shape this log keeps recording. The fix's comment and commit
message both say a `max(platform_edge) + 3` grid *"would silently truncate the slab at
u ~ 23.9 while the declared apron runs to u ~ 40.4"*. In the full assembly the module
prints:

    [apron] grid u 6.05 .. 47.55  (platform_edge max 40.56; the declared
                                   platform reaches 44.55)

so the two numbers are **43.56 and 44.55**, not 23.9 and 40.4. The fix is right and
its area figures reproduce to the decimal (5881.5 → 6421.2 m²); the *grid* figures
were measured on `work/r2132/arch_base.blend`, a module-standalone test build, and
carried into the source comment as though they described the assembly. **A number
measured on a test rig and written into a comment about the shipping build is the
same defect as a probe window that stops inside the thing it measures** — which is
R2-132 itself.

## R2-187 — the apply readback, and the one field that does not mean what it says

Read back from the saved `.blend` with `work/r2187/readback_breach.py`, not
quoted from `sim/out/apply_film14.json`. The prediction (`work/r2187/PREDICTION.md`,
written before the apply finished) was that all four fields hold, because the
bake table, the fracture plan and the camera polyline are none of them functions
of the world, and assembly9 − assembly8 is one paving object at the pit exit.

| readback | film13_breach | **film14_breach** | |
|---|---|---|---|
| objects | 3,806 | **3,806** | 3,796 shards + 10 panes |
| tris | 278,864 | **278,864** | shard triangles |
| keys | 5,798,701 | **5,798,701** | 2,475,381 loc + 3,300,508 quat + 11,406 + 11,406 hide |
| hero | 3,573 | **3,573** | two independent routes, below |
| curve proof | LINEAR 6783 / CONSTANT 240 / other 0 | **identical** | max linear eval err 4.768e−07 |

`ARCH_Paving_ApronPlatform` reads **140,593 verts** in the applied scene, which
is assembly9's number (R2-148) and not assembly8's 128,722 — the apply is on the
film it was meant to be on. Scene total 33,221 objects.

**`stats["tris"]` in the apply report is SHARD triangles only.** A readback that
counts every mesh in the BREACH collections gets **278,984**, and the 120 it adds
are the ten panes' six quads each. That is a 120-triangle discrepancy that looks
exactly like a real one until you go and read which loop the counter sits in. The
figure is correct; the field name is not, and anyone re-deriving it will lose the
same twenty minutes.

**`hero` was recounted two ways and they agree** (`work/r2187/hero_readback.py`).
It is the one stat in the report that is a function of THE CAMERA — a shard is
hero if it passes within 6 m of the camera polyline — so it is the field that
would move if the byte-identical-camera claim were false anywhere the path JSON
does not capture.

* **by the mesh**, rebuilding every cell at detail 1 and detail 2 from the same
  plan and the same seed and asking which of the two the file actually contains:
  **3,573 hero, 223 bulk, 0 unmatched.**
* **by the camera**, recomputing `dist_to_path(...) <= 6.0` from
  `breach_film.npz` and `docs/beat_sheet.json`: **3,573.**
* **disagreements between the two: 0.**

Classifying hero by "big meshes are the hero ones" was tried first and is a
guess: the vertex counts run 15..80 with no clean gap, and a largest-gap split
returned **2**.

---

## R2-188 — `matrix_world` is not evaluated for a HIDDEN object, and the breach's reference frame is the one frame where everything is hidden

The worst thing found tonight, and it was found by a control rather than by
noticing.

The claim that closed R2-097 — bay 4 goes 2,288 mm at f866 → 2,615 mm at f900
**without returning** — was measured on `sim/out/breach_film.npz`. That file is
byte-identical between the two applies, so re-running `slabcheck` on it asserts
**nothing about this apply**. So it was asked of the SCENE instead: evaluate the
applied f-curves on the objects that will render.

Done through `object.matrix_world`, that produces this table:

    bay 4   f866  3933.5 mm    f900  2621.7 mm    f1165     0.0 mm
    bay 5   f866  2434.0 mm    f900  2307.3 mm    f1165     0.0 mm

Every bay reads **exactly 0.0 mm from home at the last frame**, and f900 was
within 0.25 % of the true value, which is the part that makes it dangerous: one
column of the table is right by coincidence and the whole thing is plausible.

**The reference frame is f845, and at f845 every shard is `hide_viewport` — that
is the entire point of the swap, the glass has not broken yet.** A hidden object
is not evaluated by the depsgraph, so its `matrix_world` is never flushed and
still holds the pose the `.blend` was SAVED with, which for an applied breach
scene is the field's **resting pose at the table's last frame**. So "how far has
it travelled from home" silently becomes "how far is it from where it ends", and
the last frame reads zero because there it is comparing the resting pose with
itself.

    GS_b04_00000 at f845   location            (14.9607, -0.0243, 0.0973)   <- correct
                           matrix_world        (16.1952,  3.5810, 0.1268)   <- its f1165 value
                           evaluated_get(dg)   (16.1952,  3.5810, 0.1268)   <- also wrong

`object.location` reads the f-curve correctly at the same instant.
`evaluated_get(depsgraph).matrix_world` does not help. Worst disagreement over
the field, `GS_b05_00018`: **120.7 m**.

**A warm-up `frame_set` does not fix it** — that was the first guess, and the
control fired again at f845 after the warm-up, which is what identified the real
cause. Hiding is not a first-frame effect.

The fix is to read the location f-curves, and the thing that makes reading them
legitimate is a control rather than an assumption: at a frame where the shards
are VISIBLE the two must agree, and requirement R7 (the BREACH collection is not
parented and not offset) is what makes `location` the world position. Measured:
**1,178 objects at f900, worst |location − matrix_world| = 0 m.** R7 verified,
not assumed. The negative arm — the same comparison at f845, where it is vacuous
— is kept and reported, so the size of the lie is in the record.

With the f-curves, the scene reproduces the table **to 0.1 mm**:

| bay | f866 | f900 | f1165 | table |
|---|---|---|---|---|
| 4 | **2,288.5** | **2,615.1** | **4,987.0** | 2,288.5 / 2,615.1 / 4,987.0 |
| 5 | 578.7 | 566.6 | 2,808.2 | last 2,808 |
| 2 / 3 / 6 / 7 | 2.4 / 3.5 / 12.7 / 9.9 | | 27.0 / 14.8 / 25.0 / 26.0 | |

The prediction allowed ±2 mm for the decimation. It is exact.

---

## R2-189 — R5 refuses on TRANSOMS, and `build_breach_sim.py` builds transoms on purpose

`--force` was used on this apply, as it was on film13's. The instruction was to
make the judgement again rather than inherit the flag, and the judgement stands —
but for a reason that makes the refusal permanent rather than incidental.

**The finding is bit-identical to film13's**, which is the first thing that had
to be true: same nine names, same `(n_in, n_tri, n_clear)` triples, same 18
capture-band members, same 79 AABB candidates, same 29,381 meshes scanned. The
apron is 400 m from the pocket and does not touch it.

    GW_Front_Mull_14      0  4  4        GW_Right_Transom_0    0  8  4
    GW_Front_Transom_0    0  6  6        GW_Right_Transom_1    0  8  4
    GW_Front_Transom_1    0  6  6        GW_Right_Transom_2    0  8  4
    GW_Front_Transom_2    0  6  6        WallLine_SideFin_0    0  8  4
                                         WallLine_SideFin_1    0  8  4

**All nine have ZERO vertices in the pocket.** Every hit is a side face crossing
it, which is the case the triangle arm was correctly written for.

Three reasons `--force` is right, and the third is the one that matters:

1. **R5's stated harm is a BAKE-time harm** — *"starts every clamped shard inside
   metal, which is exactly what the null control caught."* The bake is finished
   and was built in its own scene from purpose-made `SIM_*` colliders
   (`build_breach_sim.py` lays `SIM_FloorIn`, `SIM_FloorOut`, its own sill, head,
   mullions and transoms). **`film14`'s meshes were never colliders in it.**
   Writing keyframes cannot retroactively put a shard inside metal the solver
   never saw.
2. Six of the nine are round 1's own east-wall frame (three transom rails, two
   side fins) and three are the SOUTH wall's members meeting the east wall at
   the y = −11 corner. None is glazing; R3 (no round-1 east glass) passes clear.
3. **`build_breach_sim.py` builds transoms that fill the pocket BY DESIGN**, and
   says so in its own comment: *"a transom that spans 14.840 .. 14.976 fills the
   glazing pocket and puts every shard it crosses inside it."* They are inset
   37.5 mm from the mullion centres — i.e. **across the clear opening**, which is
   what a transom is. R5's clear-opening arm therefore charges the correct
   geometry class, and **no correctly glazed curtain wall can ever pass it.**

The applier's own selftest proves this without meaning to. Its positive control
*"a bar across the middle of bay 4 is caught"* returns
`[['Bar_across_bay4', 0, 4, 4]]` — **the same triple as `GW_Front_Mull_14`.** The
gate cannot distinguish a bar laid deliberately across a bay from a curtain
wall's own rails. It already has the exemption for the case one step less
obvious (*"a mullion ON a bay boundary captures the edge, does not refuse, and IS
reported"*); the transom case is the same shape and has no exemption.

**So `--force` is not a one-off waiver, it is the permanent state of this gate
against a glazed wall, and it should be turned into a rule** — a transom-shaped
member spanning a clear opening at a `transom_landings` height belongs in the
capture-band report, not the refusal — or the refusal will be forced past
forever and will one day be forced past over something real.

**And there is a picture consequence, which is R6 open.** `apply_breach` writes
`MUL*`/`TRN*` transforms and nothing binds a mesh to them, so what renders is
round 1's **static** frame. In `work/r2187/f14_000890.png` the transom rail runs
straight across the aperture, unbroken, while the sim's own model of that rail is
an ACTIVE body that sheds segments. The wall's glass leaves and its rails do not.

---

## R2-190 — the east wall, MEASURED: 1,255 of 4,096 camera rays meet glass, against 0 in the unapplied film

`n_GW_Right_Glass` counts ROUND ONE's object names and reads **0 for a correct
scene exactly as it does for an empty one**. That is why the wall shipped bare
through film10, 11, 12 and 13. The fallback is to render f0858 and look — and it
was rendered and looked at, and it is glazed — but at that range, through motion
blur, clear glass and no glass are genuinely hard to separate by eye, which is
how the defect survived four films.

So the question was put to the scene. `work/r2187/glass_raycast.py` casts a
64 × 64 grid from the film's own camera at f858 against a BVH of the `GP_b*`
panes:

| | `film14_breach` | `film14` (the ship, unapplied) |
|---|---|---|
| `GP_b*` panes in scene | 10 | **0** |
| visible at the frame | 10 | 0 |
| rays meeting glass | **1,255 of 4,096 (30.64 %)** | **0 of 4,096** |
| distinct panes hit | 6 — bays 4,5,6,7,8,9 | 0 |
| range | 6.93 .. 16.66 m | — |
| glass x | 14.95500 .. 14.96650 (the pocket) | — |
| material | `BREACH_Glass` | — |
| raster region | x 0.398..0.992, y 0.008..0.602 | — |

Same camera, same frame, same 4,096 rays. **The control comes back zero, and
that zero is the defect itself** — it is what film10–13 would all return.

`scene.ray_cast` was tried first and abandoned after 25 minutes without a
result: the whole-scene BVH over 33,221 objects and 4.99 GB does not build in
any time worth spending. Ten panes are 120 triangles.

---

## R2-191 — the pit-exit apron reads at f0866 and f0890, not only at f1104

R2-150 established the apron repair on f1104, *"the ONER's best view of the
region"*. It is not the only frame it reads in.

f0866 and f0890 were re-rendered from `film14_breach` and compared with the
archived `film13_breach` frames. **The control is a repeat render of
`film13_breach` on the instance in use tonight**, because a floor measured on
another night on another GPU is not this render's floor:

| | changed at all | > 2/255 | > 8/255 | max |
|---|---|---|---|---|
| **floor** f0866, film13_breach vs itself | 4.66 % | 0.0000 % | 0.0000 % | **1** |
| **floor** f0890, film13_breach vs itself | 4.62 % | 0.0000 % | 0.0000 % | **1** |
| f0858, film13_breach → film14_breach | 5.57 % | 0.0000 % | 0.0000 % | 3 |
| **f0866**, film13_breach → film14_breach | 7.83 % | 0.0094 % | **0.0037 %** | **19** |
| **f0890**, film13_breach → film14_breach | 8.50 % | 0.0122 % | **0.0048 %** | **66** |

77 pixels at f0866 and 100 at f0890, against a floor of exactly zero.

**They are the apron.** Projecting `ARCH_Paving_ApronPlatform`'s own vertices
through the scene's own camera puts it in a thin raster band, and the differing
pixels are inside it at both frames — while the band itself MOVES between them,
which is what makes the containment mean something:

    f0866   apron band  x 1191 .. 1920   y 377.8 .. 418.4   (41 px tall)
            pixels >8   x 1575 .. 1607   y 400   .. 402
    f0890   apron band  x  855 .. 1920   y 358.5 .. 428.2   (70 px tall)
            pixels >8   x 1463 .. 1498   y 398   .. 401

**And they move in R2-150's direction, to R2-150's values.** Taken over just the
pixels that changed:

    f0890   film13 (86.3, 78.6, 67.2)  ->  film14 (118.0, 108.3, 93.7)   +31.7 / +29.8 / +26.5
    f0866   film13 (112.7, 101.3, 84.4) -> film14 (125.2, 113.5, 95.9)   +12.5 / +12.2 / +11.5
    R2-150 at f1104, the void region:  (99.1, 88.2, 74.9) -> (116.6, 103.3, 86.6)

They **lighten**, because a lit concrete apron is now there — the same sign, the
same magnitude class and very nearly the same destination RGB as the region
R2-150 measured at a completely different frame. That agreement was not
arranged and is the best independent check that this is the apron and not
something else that happens to be in the band.

Worth recording as a caution: reading the crops by eye, I first called the
direction backwards — the film13 strip looked like the brighter one. The
measurement is what settled it, on 100 pixels, and the eye was wrong about a
32/255 difference.

**This falsifies the quantitative half of my own P4**, which predicted the two
frames would differ only at the floor. It falsifies it in the direction the
prediction named as interesting: the apron is in frustum in beat 3, so beat 3 is
not apron-neutral. It is 0.005 % of the frame and it does not change the
breach reading at all — but "the repair only shows at f1104" is now false, and
R2-150's framing should carry this.

---

## R2-192 — the 627 under the floor is the instrument, confirmed from the applied scene; and "627, 1.9 % of the field" is two different measurements in one sentence

Another agent is fixing this in `sim/verify_breach.py` as I write (their number
is R2-196, file touched 01:48). **Nothing here touches their file.** This is an
independent route to the same quantity — off the applied scene, through the
applied f-curves and each shard's own applied quaternion — and it lands on their
figure:

| at f1165, 3,796 shards | below floor | worst | %|
|---|---|---|---|
| axis-aligned bound, `origin_z − max\|local v_z\|` | **626** | 154.599 m | 16.49 |
| **rotated, `min (R·v)_z + origin_z`** | **70** | 154.6 m | **1.84** |

556 bodies are dropped by the rotation, **0 are found only by it**, and of the
556 the highest true lowest-vertex is **z = +0.1056 m** and the lowest is
**z = +0.0001 m** — every one of them above the floor, not near it. A shard's
local z is the PANE's vertical, so a shard lying flat on the forecourt has that
axis horizontal and the old bound charges it half its height in the wall.

**And the standing sentence "627 bodies end below the floor … 1.9 % of the
field" is two instruments spliced together.** 627 / 3,948 is 15.9 %. The 1.9 % is
70 / 3,796 = 1.84 % — the corrected count's percentage carried next to the
uncorrected count. Both halves have been repeated as one fact.

**This apply neither improves nor worsens it**, and cannot: the sink figure is a
property of `breach_film.npz`, which is the same file. Recomputed on the table
restricted to the same population the scene contains (`work/r2187/inherited.py`):
GS shards only, 3,796 bodies, same numbers. The 152 `MUL*`/`TRN*` frame bodies
in the table contribute **0** below-floor bodies and are not instanced in the
scene at all, so 627-against-3,948 and 575-against-3,796 were never comparable.

**70 shards really are under the floor and the worst really is 154.6 m.** That
part is not an instrument. `GS_b04_00446` at −154.6 m, then two at −114.9 and
three at −105.9.

**And the 70 now have an owner and a cause.** `e2d7d85` (R2-197, another agent,
committed while this was being written) diagnoses them: the static ground stops
at x 46 / |y| 14 and the field travels 653 m, so **55 of the 70 are outside the
slab footprint at the frame they first cross z = 0**, crossing at a median
−0.34 m/s — walking off a ledge, not punching through one. 15 genuinely tunnel.
`SIM_Outfield` closes it and **takes effect on the next bake only**, so the 70
are still in `film14_breach` and will be until the wall is baked again. That is
the correct call — none of them is on camera — and it should be recorded on the
scene rather than assumed fixed.

---

## R2-193 — cluster B is not in the motion that renders — and my explanation of WHY was wrong; R2-199 has the real one

**Superseded within the hour, and corroborating it.** While I was measuring
this, another agent closed cluster B properly at `e2d7d85` (R2-199): clusters A
and B were measured on `sim/tmp/breach_bake.npz`, **the superseded bond-4000
bake**, and on the bake that is actually in the film they are **0 and 0**. They
proved the identity rather than inferring it — the shipped table's last frame is
bit-identical to `breach_full_m1.npz` and 626.781 m from `breach_bake.npz`.

**The two measurements agree where they overlap, and one of them is exact.** My
chord-speed measure on the film-frame reconstruction finds the fastest body at
**110.4 m/s**; their raw-bake measure on the same config finds the peak at
**110.41 m/s**. Same body, two different instruments, four significant figures.
Their count over 60 m/s is 7 and mine is 1; that residual factor of seven *is*
the film-frame sampling, and it is the only part of my explanation that
survives.

**What I got wrong, and it is worth recording as wrong rather than dropped:** I
wrote that cluster B "lives at sub-film-frame timescales and the delivered
animation samples over it". That is not why it is absent. It is absent because
**it was never in this bake at all** — it belongs to a configuration that was
replaced. Sampling explains 7 → 1. It does not explain 348 → 0, and I had no
evidence that it did. The observation was right and the mechanism I attached to
it was a guess dressed as a finding.

What stands from this entry on its own: the rendered motion is much slower than
either bake figure suggests, and that is worth knowing for motion blur and for
anyone quoting a speed at a frame.


### the measurement, as taken

R2-096 left cluster B open — *"348 shards to 106 m/s with no measurable
contact"* — and recorded *"828 shards exceed 60 m/s, 661 of them on screen."*

**Those are raw-bake figures.** On the decimated film-frame reconstruction —
the table the scene was built from, and therefore the only motion the render
has — the picture is completely different:

    shard speed, max chord between consecutive film frames x 24 fps
        median (not sunk)           11.4 m/s
        99th percentile             22.0 m/s
        bodies over 60 m/s          1        (110.4 m/s, and it is sunk)
        bodies over 106 m/s         1

A chord between film frames is a lower bound on instantaneous speed, and a body
that accelerates and reverses inside 1/24 s has most of its speed averaged away
— so this bounds what is ON SCREEN and nothing more. **Nothing in the delivered
animation is travelling at 106 m/s.**

The overlap with the sink was tested at the same time, with a random-subset
control at each threshold. The 70 sunk shards **are** the fast tail —
median max speed **38.9 m/s against 11.4** for the rest, above the 99th
percentile of everything else — but they are not a 106 m/s population, because
on the shipped config there is no such population (R2-199). So the hypothesis
that the two open items were one item is **not supported**: the sunk bodies are
fast relative to their neighbours and ordinary in absolute terms, and R2-197's
diagnosis — 55 of the 70 walked off the edge of a ground plane that stops at
x 46 / |y| 14 — is the actual cause and has nothing to do with speed at all.
`work/r2187/clusterb.py`.

---

## R2-194 — the wound is frozen, not settled, and on the reconstruction it is 1,599 bodies not 2,275

The bake is not at rest at its last key. This bears directly on beat 3 → beat 4:
the wounded showroom has to persist for the rest of the take, and the table ends
at f1165 with the film running to f2978. Everything after f1165 is **CONSTANT
extrapolation** — the field does not settle, it is frozen mid-flight.

Measured on the applied f-curves, between the last two keyed frames:

    over 1 mm per frame     1,599 of 3,796 shards   (42.1 %)
    worst                   3.0489 m per frame      (73 m/s)

The standing figure is **2,275** (recorded elsewhere as 2,375). I could not
reproduce either. Recomputing on the decimated reconstruction restricted to the
same population gives **1,599** for GS shards and **1,599** for all 3,948 bodies
— the frame bodies contribute none. The scene reads **1,600**, the one-body
difference being that 3,573 shards carry the detail-2 mesh and my table-side
radius used detail 1. I am recording that I could not reproduce 2,275 rather
than assuming it was wrong; it is most likely the raw bake, on the same
raw-versus-reconstruction split as R2-193.

**Either way the item stands and gets worse when stated properly**: 42 % of the
glass is still moving when the table runs out, one body at 73 m/s, and what
holds the picture together for the remaining 1,813 frames is an extrapolation
mode rather than a physical rest state. `verify_breach`'s own PERSIST arm cannot
see this — it reports `"table ends before 1200"` and returns no verdict at all.


## The gates, each with the control that discriminates

| gate | film14_breach | control |
|---|---|---|
| `socket_index_audit --blend` | **PASS** — no relief chain reaches a shading node on anything but a normal | `film10`, the assembly6 control, **FAIL, 27 findings**, in the same run |
| `verify_breach --swap-scene` | **PASS, 0 problems.** Bays 2,3,4,5,6,7 each hide their pane at **860** and show every shard at **860**; `shards_not_on_the_pane_frame = 0` in all six; bays 0,1,8,9 intact, pane never hides | the same script's `--swap` arm on the TABLE: **FAIL, worst gap 2,118 frames, 301 shards uncovered.** Table fails, scene passes — that pairing is what shows the applier is the fix |
| `apply_breach --selftest` | **PASS, 0 failed of 11 arms** | six of the eleven are must-fail arms, including "no east glazing at all", "a hidden pane", "a surviving round-1 plane" and "a solid box through the pocket with ZERO vertices inside it" |
| curve proof (in-applier) | LINEAR 6,783 / CONSTANT 240 / **other 0**, max linear eval err 4.768e−07, `control_fires: true` | the Bezier control arm, which must and does register 4.797e−04 |
| east wall | **1,255 of 4,096 rays meet `GP_b*`** | `film14` unapplied: **0 of 4,096** (R2-190) |
| f0866 / f0890 A/B | signal 0.0037 % / 0.0048 % over 8/255 | live repeat-render floor **0.0000 %**, max 1/255 (R2-191) |

## The nulls

Three things had to NOT move, and did not:

* **the camera track.** `sim/dump_camera_track.py` re-run on `film14_breach` and
  compared with the copy dumped from `film13_breach`: 2,978 rows x 9 columns,
  **max|diff| exactly 0.0**, and the two files have the same sha256
  (`4cafe712c405b43b…`). Every pixel figure on this defect goes through that
  track, including R2-095's corrected ranges, and it did not have to be
  re-derived — but it did have to be checked, because the track was dumped from
  a scene that no longer ships.
* **`sim/out/apply_requirements.json`**, republished by the preflight run:
  no diff.
* **the curve proof**, byte-for-byte identical to film13's including the
  Bezier control's 4.797e−04.

And the one thing that did move, `render/film14_breach.blend` is
**462,507 bytes larger** than `film13_breach.blend` — which is the apron, and
is the only difference either file should have.

## R2-226 — the census read the docs for placement data; the artefacts have it

The census's handover says *"there is no placement step between `world/items/`
and `assemble.py`"* and, separately, that no item module carries placement data.
**The first is true.  The second is true of the documents and false of the
blends**, and the difference decided the whole design of the stage.

Measured out of the built test blends, `work/r2226/inventory_item.py`:

| item | objects | distinct meshes | centroid extent, WORLD metres |
|---|---:|---:|---|
| `armco_post` | 3,236 | 3,236 | x [−716.9, 552.7]  y [−256.8, 926.9] |
| `catch_fence_post` | 676 | 676 | x [−716.9, 625.8]  y [−257.2, 983.9] |
| `crew_figure` | 120 | 120 | x [−58.8, −30.1]  y [−64.3, −37.3] |
| `heras_fence_panel` | 771 | 771 | x [−109.9, 377.8]  y [−105.5, 320.0] |
| `timing_stand` | 10 | 10 | x [161.9, 317.2]  y [47.3, 177.7] |
| `tyre_wall_tyre` | 338 | 338 | x [246.6, 267.3]  y [895.6, 928.1] |

Those are circuit coordinates.  The modules import `world_contract` and resolve
every unit through `C.su_to_world(s, u)` / `C.world_ground_z(x, y)` **at build
time**; projected back onto the centreline by the new stage's own check,
`crew_figure` lands at **s 3232.6 – 3262.0, u +53.8 – +85.9 m**, the paddock
behind the pit building.

**So the missing stage is a transfer, not a placement solver.**  Every item's
position was computed by its author, through the contract every class builder
reads, and dropped on the floor at the door.  A design that had believed the
docs would have written a solver and re-derived 41 authors' work.

`assemble.py`'s `--mods` default now ends in `items`.  **A world rebuild is
owed** before anything changes in the ship.

## R2-227 — 40 of 41 modules cannot be placed today, and the reasons are four

`world/items/PLACEMENT.json`, 41 rows, each blocker naming its measurement.
One row is in state `PLACE`.  The blockers, with multiplicity:

```
SUPERSEDE_WELDED   24    the world already builds this feature, welded inside a
                         class mesh; placing it double-builds
GATE_NOT_ACCEPTED  22    canonical gate.json is not ITEM_ACCEPTED
PARTIAL_BUILD      15    the blend holds fewer units than the item declares
NOT_AN_ITEM         6    probes; their absence is correct
LOCAL_FRAME         5    builds local and publishes place=(R, t); the registry
                         has no transform arm yet
NO_BUILT_BLEND      3
DUPLICATE_MODULE    2    pit_wall_unit_itemkit, showroom_facade_panel_v2
NO_WORLD_FRAME      2    the test blend lays the population on a grid
NO_GATE_REPORT      1    spectator_standing_ga
```

**`crew_figure` is the only clean one, and why it is clean is the census's own
headline.** It supersedes nothing, because §2.5 measured that 0 of `assembly9`'s
30,183 datablock names and 0 of `film14`'s 32,069 match
`figure|person|crowd|spectat|skin|hair|human|crew|driver`, and there is no skin,
flesh or hair material among the 130 / 191.  **The one item that can be placed
without first taking something out is a human being, because there are none.**

Two rows worth naming for whoever picks this up:

* **`tyre_blanket` is the nearest next candidate** — the only row whose ONLY
  blocker is the gate verdict.  56 of 56 declared units, world frame, nothing in
  `assembly9` it would double-build.  Re-gate it ACCEPTED and it is placeable as
  it stands.
* **`spectator_crowd`'s `GATE_NOT_ACCEPTED` is reading the wrong file.**
  `spectator_crowd.py` sets `ITEM = "spectator_seated"`, so the row's verdict
  came from `render/items/spectator_seated/gate.json` (REJECTED) and not from
  `render/items/spectator_crowd/gate.json` (ACCEPTED), which exists for a
  directory that is not a manifest id — census §1.3's off-by-one.  The row is
  HOLD either way on `NO_WORLD_FRAME`, which is decisive and independent of the
  gate, and the row now says so rather than being taken as true.

## R2-228 — `tools/placement_gate.py` has R2-180's fall-through, in the gate the campaign relies on

Run on a scene holding **two** item collections it prints

    collection 'W_Item_CrewFigure' (item-campaign convention); 2 item
    collections present, took the largest -- pass --subject to be explicit

and measures crew_figure's 120 meshes as the subject while filing the ten
`TS_Stand*` objects under `context_findings`.  That is exactly R2-180 —
*"`cands = pick or cands` fell through to 'any item collection, take the
biggest'"* — in a different file, and **a placement stage makes multi-item
scenes the normal case**, so it will now fire routinely rather than never.

Worked round by running the gate once per item with `--subject`.  Both clean,
and the second run produces numbers the fall-through never reached:

```
crew_figure   PLACEMENT_CLEAN  0 violations; no subject mesh came within
                               bounding-box reach of ANY of the three volumes
timing_stand  PLACEMENT_CLEAN  0 violations
              road_corridor  3.487 m clear  TS_Stand05_GRISAILLE
              car_path       5.370 m clear  TS_Stand00_BOREAL
              camera_path   10.509 m clear  TS_Stand03_ESTIVAL
```

**And R2-110's controls were run with them, because a gate run only against the
thing you hope is clean is not a measurement:**

```
ctl_place_pos           PLACEMENT_FAIL     (must fail)
ctl_place_neg           PLACEMENT_CLEAN    (must pass)
ctl_place_nearmiss_neg  PLACEMENT_CLEAN    (must pass — over-rejection)
```

The gate is not mine to change; it is named here.

## R2-229 — the supersede debt is physical, and a counter could not have shown it

`build_items` derives its `REBUILD_OWED` lines from `assembly9_build.json`'s own
counters — `pit_wall_stands = 5`, `armco_posts = 3561`, `fence_posts = 676`.
**A counter says what was built, not where it is**, and "the old version has to
come out" is a claim about space.

`work/r2226/supersede_overlap.py` links `ARCH_PitWall` **alone** out of the
4.21 GB ship — one object through `bpy.data.libraries.load`, not a scene open —
and counts wall vertices inside each placed unit's world bounding box:

```
10 of 10 TS_Stand* units contain host geometry
4,300 of ARCH_PitWall's 24,664 vertices
worst TS_Stand09_KESTREL 2,184, best TS_Stand06_HALCYON 18
```

**A bounding box is generous.**  A stand's box runs from the ground to its
canopy and the wall passes beneath it, so this is an upper bound on
interpenetration rather than proof of it.  What it does establish is that the
hero stands and the welded ones occupy the same volume of the pit straight,
which is what makes them one feature built twice — and it is why
`timing_stand`'s state is HOLD despite being `ITEM_ACCEPTED`, complete at 10 of
10, in world frame and keep-out clean.

`catch_fence_post` is the starkest case and needs no measurement: the item
builds **676** posts and `build_barriers` reports `fence_posts = 676`.

## R2-230 — `build_items.purge()` leaked mesh datablocks, and the idempotence test is what caught it

`build()` twice in one session, on an identical 120-object scene:

```
run 1   123 objects   122 meshes   3,137,756 verts
run 2   123 objects   243 meshes   6,275,504 verts      <- before the fix
run 2   123 objects   121 meshes   3,105,356 verts      <- after
```

`purge()` removed the objects and left their meshes, and **Blender reused the
object names**, so the scene looked right — first and last object names
identical across both runs.  A second leak was in the rig-drop path: a standin
ground plane's mesh outlives its object the same way.

Blender drops zero-user datablocks on save, so this could never have reached a
shipped blend.  It matters anyway, because **the mesh counts are how the
no-repeats rule is enforced in this file** — `distinct meshes == objects`,
`users == 1`, `top_share` — and an in-session mesh count that doubles is a count
nobody can use.

Removal is scoped to what this stage placed.  It never sweeps `bpy.data` for
orphans: an orphan somebody else made is not this stage's to delete, and
*"`purge(prefix)` has no default prefix"* is a rule this project already paid
for.

## R2-231 — the placement check that did not exist, shown failing before it was trusted passing

`tools/item_placement_gate.py`.  R2-182 paid a full render cycle for the
question *is the item in the blend you are about to render?*, and the answer for
all 41 items was no.

**`--selftest`, seven families built live in-process.**  The four must-fail cases
are the point:

| case | verdict | arm |
|---|---|---|
| 40 objects / 40 meshes / stamped | `PLACED` | — |
| no collection at all | `ABSENT` | — |
| 39 of a declared 40 | `PLACED_BUT_WRONG` | `COUNT` |
| **40 objects wearing ONE mesh** | `PLACED_BUT_WRONG` | `NO_REPEATS` ×3 |
| 40 objects, 8 meshes (top 12.5 %) | `PLACED_BUT_WRONG` | `NO_REPEATS` ×3 |
| 40 objects, no provenance stamp | `PLACED_BUT_WRONG` | `PROVENANCE` |
| 4 objects, 1 mesh | `PLACED_BUT_WRONG` | `NO_REPEATS` (share not gated below 10 units; the datablock arm still fires) |

**And the strongest control cost nothing, because it was already on disk.**  The
same gate, same registry, run against the two artefacts the census measured:

```
render/film14.blend        --expect absent   crew_figure ABSENT, 1 of 1
                           >> PLACEMENT_ITEMS_ABSENT_AS_EXPECTED_OK
render/r2226_items.blend                     crew_figure  PLACED 120 objects,
                                                          120 meshes, 0 unstamped
                                             timing_stand PLACED  10 objects,
                                                           10 meshes, 0 unstamped
                           >> PLACEMENT_ITEMS_OK
```

A gate that cannot tell the shipping world from a placed one is not measuring
placement.  `tools/item_ab_measure.py` **refuses to interpret an A/B at all**
unless it is handed this gate's verdict for the AFTER blend.

## R2-232 — the pixels, and R2-182's own frame is no longer identical

Both A/Bs are `film14` against `render/r2226_items.blend`, 4K, 256 samples,
`--denoiser NONE`, camera `ONER`, same farm.  NULL is `film14` rendered a
**second** time.  `tools/item_ab_measure.py` refuses to interpret either until
handed `tools/item_placement_gate.py`'s verdict for the AFTER blend.

**f654 — `crew_figure`, 88 of 120 figures in frustum, 75 visible, 13 occluded:**

| region | px | AB >8/255 | AB mean \|Δ\| | NULL >8/255 | NULL mean \|Δ\| |
|---|---:|---:|---:|---:|---:|
| whole frame | 8,294,400 | 1.02 % | 0.38 | 0.00 % | 0.00 |
| **visible units** | 153,413 | **51.05 %** | **18.83** | 0.00 % | 0.00 |
| **occluded units — CONTROL** | 2,941 | **7.07 %** | 2.52 | 0.00 % | 0.00 |
| **rest of frame — CONTROL** | 8,138,046 | **0.08 %** | 0.03 | 0.00 % | 0.01 |

**f1126 — `timing_stand`, R2-182's own frame, 9 of 10 stands in frustum:**

| region | px | AB >8/255 | AB mean \|Δ\| | NULL >8/255 |
|---|---:|---:|---:|---:|
| whole frame | 8,294,400 | 7.69 % | 2.60 | 0.00 % |
| **visible units** | 1,046,575 | **49.47 %** | **14.47** | 0.00 % |
| rest of frame | 7,247,825 | 1.66 % | 0.89 | 0.00 % |

R2-182: *"Rendering f1126 from the film before and after the fix would have
produced two identical images — and been read as 'the fix is invisible, close
it'."*  **It does not, once the item is in the world.**  49.47 % of the pixels
in the nine stands' boxes move, against a repeat-render floor that rounds to
0.00 % at the same threshold.  There is no occluded stand at this frame, so the
internal control is unavailable and the tool says so rather than inventing one.

**Three controls, saying three different things.**  The NULL says the floor is
clean at the 8-level threshold (with the denoiser off, sampling noise reaches 26
levels on isolated pixels; nothing survives the threshold).  REST OF FRAME says
the change is confined to where the figures project — 0.08 % against 51.05 %,
**659×**, and 574× on mean |Δ|.  THE OCCLUDED HALF is R2-150's control, and at
7.07 % against 51.05 % it is **7.2×**, weaker than R2-150's 50×.  The reason is
measurable rather than mysterious: occlusion is classified by ONE ray to each
figure's centroid and the region is that figure's screen BOUNDING BOX, so a
figure whose chest is behind a wall and whose head clears it is scored occluded
and contributes a box full of visible head.  7.07 % is the size of that leak,
not of a light leak.  A per-pixel depth split would separate them.

**And the instrument failed first, loudly.**  The initial f654 run reported
visible **0.00 %** / occluded 0.00 % / rest-of-frame 1.04 % — the frame had
plainly changed and the boxes were empty, because the projection puts v = 0 at
the frame's bottom while numpy rows run top-down, so every box was vertically
mirrored.  It printed *"either the item is not where the projection says, or the
frame does not see it"* and returned `ITEM_AB_FAIL` rather than a tidy null.
Both logs are kept: `work/r2226/ab_654.log` mirrored, `ab_654_flip.log`
corrected.

**Looked at, not only measured.**  `work/r2226/peep_*.png`.  At f654 the BEFORE
is empty tarmac behind the paddock fence and the AFTER is a row of team-coloured
crew, motion-blurred by a fast camera.  At f1126 the BEFORE pit wall is bare and
the AFTER carries a run of decks, fascias and canopies — and the clutter along
that wall **is** the R2-229 debt made visible: ten hero stands standing among
five welded ones.

## R2-233 — two A/B tools in `tools/` cannot run on this box at all

`tools/r2179_ab_measure.py` and `tools/glass_winding_ab_measure.py` both do
`from PIL import Image` at module scope.  **Neither `/usr/bin/python3` nor
Blender 5.2's bundled interpreter has PIL** — checked again today, both raise —
which is exactly why `world/items/human_png.py` exists and says so in its own
header.  `tools/item_ab_measure.py` reads through that instead.

This is R2-150's shape a third time: *"the rewritten script died on
`No module named 'PIL'` while Blender exited 0.  The printed `STAGE RESULT` line
caught it; `$?` would not have."*  Noted, not fixed — those two files are
somebody else's.

## R2-234 — I clobbered another agent's commit message with `git commit --amend`

**My mistake, recorded because it is the git-hygiene rule's twin and the rule as
written does not cover it.**

The standing rule on this project is *path-scope every `git add`* — a broad add
has swept up other agents' in-flight work five times.  I obeyed it on every
`add`.  Then I ran `git commit --amend` to correct one number in **my own**
commit message.  Between my commit (`491cef7`) and the amend, another agent's
commit landed and became `HEAD`, so the amend rewrote **theirs**:

```
e4d1d90  R2-274: the repeat floor is not zero on a glass wall ...   <- clobbered
4d9e49a  R2-226: 120 human figures arrive in a film that had none   <- my message,
                                                                       their files
```

**Only the message moved.**  `sim/wallstats.py` and
`sim/out/wallstats_f2978_floor.json` are R2-274's own and are untouched, and
`491cef7` still carries my commit with the correct files.

**Repaired with `git notes`, not a rebase.**  `git notes add` on `4d9e49a`
records what happened and restores R2-274's message verbatim; the original
commit object survives at `e4d1d90` and `git show e4d1d90` still works.  A
rebase would have been the "proper" fix and would have rewritten eight commits
belonging to three live agents to repair one message — a far worse trade.

**`--amend` is `add`'s blind spot.**  `git add` takes a path; `--amend` takes
whatever `HEAD` happens to be at the moment it runs, and in a tree with
concurrent agents that is not necessarily yours.  The rule should read *never
`--amend` in this repository* — write a correcting commit instead.


## What is owed

1. **A world rebuild** to put `crew_figure` in the ship.  `assemble.py`'s
   default `--mods` now ends in `items`; nothing moves until an assembly runs.
2. **`build_architecture` and `build_barriers`** own every `REBUILD_OWED` line.
   Until a class module stops welding a feature, the hero module for that
   feature cannot be placed.  This is the honest, physical form of the census's
   *32 + 42 = 74 reworks*.
3. **A `frame: "local"` arm in the registry** for the five modules that build
   local and publish `place=(R, t)` / a `*_to_world()`: `pont_girder`,
   `pont_deck_slab`, `gantry_truss`, `driver_figure`, `crew_fireproof_overall`.
   Named and stopped.
4. **Per-face provenance in the class builders** — see the note below.  It is
   what would close the census's 168 `UNDET`, and the mechanism is already in
   those files.

### The provenance note, because the census asked whether it is worth it

**Object-level stamping is done and it is cheap**: every object this stage
places, and its mesh, carries `r2_item`, `r2_manifest_item`,
`r2_item_collection`, `r2_src_blend`, `r2_src_sha8`, `r2_gate`, `r2_stage`,
`r2_placed_utc`, and the gate fails an unstamped object inside a placed
collection so the stamp cannot rot into decoration.

**It does not close the 168, and it cannot.**  Those items are welded inside
`ARCH_PitWall`, `ARCH_Gantry`, `ARCH_PaddockBuildings` — *one mesh*, so no
object-level property can distinguish a coping from an advert from a timing
stand inside it.  The census asks for "a provenance attribute written at build
time"; for welded geometry that has to be a **face-domain attribute**, not a
custom property.

**It is worth building, and the reason is that the mechanism already exists in
those files.**  `build_architecture`'s `MB` accumulator already carries per-face
parallel arrays — `self.fm` material index, `self.fs` smooth flag, `self.fc`
colour — and `MB.build()` already writes them with `me.polygons.foreach_set(...)`
and `me.color_attributes.new(...)`.  `build_barriers` and `build_dressing` use
the identical `foreach_set` idiom.  A face-domain `INT` attribute keyed to an
item-id table is **`fc`'s twin**: one array beside the three that exist, one
`me.attributes.new(name="r2_item", type='INT', domain='FACE')` beside the colour
layer, and a current-item context set per *section* of the builder rather than
at each of the ~230 append sites.

That would make all 435 items decidable from the artefact for ever, and it
should be done at the next class-module change, because it needs a rebuild
anyway and one is already owed.

## R2-241 — the cockpit was empty for all 2,978 frames, and nobody had measured
what it was worth

`docs/ITEM-PRESENCE-CENSUS.md` scores `driver_figure` **MID / 220.7 px** and
lists it `ABSENT`. Both halves were understated.

Measured with `render/film14_path.json` (the film's own camera) against
`world/car_anim_car.json` (the car's own per-frame transform), with occlusion by
a BVH of all **9,629,183 car triangles built once in CAR_ROOT-LOCAL space** — so
the camera is transformed into the car each frame rather than the car into the
world, which makes an exact 2,978-frame occlusion sweep cheap:

| probe | peak px | peak SHARP px | frames visible | frames sharp | ≥200 px | closest |
|---|---:|---:|---:|---:|---:|---:|
| helmet (0.26 m) | 1312.4 | **366.0** | 2164 | 1838 | 151 | **1.226 m** |
| cockpit opening (0.40 m) | 1934.3 | 323.8 | 2278 | 1922 | 391 | 1.279 m |
| shoulders / arms | 667.3 | 347.4 | 1905 | 1575 | 224 | 2.093 m |

Per beat, helmet, sharp: beat 1 **209.7**, beat 2 **190.2**, beat 3 119.0,
beat 4 46.2, beat 5 **366.0**, beat 6 7.7. The peak is frame **2632** — 2.42 m
away, 78 % of the helmet unoccluded, car dead straight at 81.5 m/s.

**Both controls held.** POSITIVE: the same instrument on the rear wing reports
1738 visible frames. NEGATIVE: a probe **buried inside the monocoque** reports
**0 visible frames of 2978** while its raw projected size peaks at 25,611 px —
so the occlusion term is live and the metric does not read the same
present-or-absent.

**366 px sharp is 17 % of frame height, held above 200 px for 151 frames, on
screen and unoccluded for 2164 of 2978 frames (73 % of the film).** That is HERO
presence. `driver_figure.py`'s 1,608,502-triangle build is the right tier and is
kept unchanged; its tessellation is set by explicit section counts, not by the
`NEAR_M = 3.0 / LENS_MM = 21.0` header assumption, so nothing was owed there.

## R2-242 — the fit, and the part of it that cannot be fixed

Round 1's cockpit tub offers **0.249 m** of hip-to-headrest rise where a 1.78 m
man needs **0.552 m**, and `/home/zany/opus5-car-render` is READ-ONLY.
`driver_figure.PACKAGE['round1_note']` had already recorded this and recommended
moving the CAR. The car cannot move, so the DRIVER is re-solved onto it:

* `WHEEL_C` overridden from `(0.300, 0, 0.393)` to the measured
  `(0.300, 0, 0.3147)` — **78.3 mm** — and `WHEEL_TILT_DEG` from 25.00 to the
  measured **22.01**. The gloves then land **0.1 mm and 0.0 mm** from the car's
  own `SW_GripL/R` bars.
* helmet crown **0.147 m above the cockpit rim**, **5.5 mm under the halo apex**;
* ankles inside `CI_pedals` in both x and z;
* hip **0.229 m below the seat pan** — i.e. the pelvis and legs are inside the
  monocoque. Invisible, and `tools/driver_containment.py` measures that rather
  than asserting it.

**The fit frame matters.** Frame 1 is mid-explode: the cockpit interior sits
2.443 m above home until about frame 500. `measure_car` refuses any frame where
`CI_seat` is more than 20 mm off home.

## R2-243 — `driver_figure.build(place=)` took the figure apart, limb by limb

`Acc.emit` recentres every mesh on its bounding box and stores the offset in
`ob.location`. `build()` then applied the placement with

    o.matrix_world = Mw @ o.matrix_world

`matrix_world` is a DERIVED value the depsgraph writes; on an object created
moments earlier it can still read IDENTITY. For the objects emitted late in
`build()` the right-hand side was `Mw @ IDENTITY` and the assignment **discarded
the recentre offset**.

MEASURED: `DRV_Helmet` — emitted second — landed on its predicted crown height.
`DRV_Glove_L` — emitted sixth — landed **209 mm from its own grip anchor**, with
`matrix_basis.translation` equal to the placement translation alone and a raw
mesh centroid of `(0.151, 0.0015, 0.1454)` against an anchor at
`(0.2986, 0.1081, 0.3182)`. The module printed `>> driver_figure: 10 objects,
1608502 triangles` and reported success.

Fixed to go through `matrix_basis`, which is composed from stored loc/rot/scale
and is never stale, so the result is order-independent. A four-way unit test
(`WHEEL_C`, tilt and grip-offset overrides, crossed) confirmed the module's own
solve was correct all along: the bug was purely in how the answer was written
back.

## R2-244 — the install empty rode 408 m behind the car

`e.matrix_parent_inverse = root.matrix_world.inverted()` was sampled while the
scene sat on the fit frame, where `CAR_ROOT` is 400 m down the circuit. That
inverse was baked in permanently. `verify_install` caught it at **408.890 m**.
The empty now copies `CI_seat`'s own parent inverse and the `DRV_*` objects hang
off it with an identity inverse.

## R2-245 — keying the driver's appearance rewrote the CAR's seat animation

The empty was given `CI_seat`'s **own** action datablock so it would ride the
assembly. `key_appearance` then inserted `hide_render` keys through it and
forced every keyframe in the action to `CONSTANT` — into the car's action, on
the car's seat, in a blend the car is supposed to pass through untouched. The
explode-offset control went **2.518 m → 104.398 m**.

Two fixes: the empty gets a **copy** of the action, and it is excluded from the
appearance keying. And a **car witness** now brackets the entire run — seven car
objects (`CI_seat`, `CI_seatpad`, `CI_headrest`, `SW_Shell`, `CI_liner`,
`MB_chassis_cockpit`, `halo_assembly_HoopTube`) sampled for translation, rotation
and `hide_render` at ten frames, 70 samples, compared before and after and
refusing to save if any changed. **0 of 70 changed.**

## R2-246 to R2-249 — the driver does not fit, and where that reaches the film

`tools/driver_containment.py` renders the driver's coverage as an **alpha
mask**: every car mesh is set `is_holdout`, so it punches a transparent hole
while still occluding, and with `film_transparent` the alpha channel is 1
exactly where an unoccluded driver surface is frontmost. One sample, 0.01 px
filter, opaque `material_override` — binary, no denoiser, nothing to threshold.

(The first cut used the `IndexOB` pass through the compositor and died on
`Scene.node_tree`, which **Blender 5.2 removed**. Blender still exited 0.)

**R2-246.** Frame 2632: 132,426 driver pixels, **0 in the driver-absent
control**, and **82 outside the cockpit aperture** in a 10 × 14 px blob 198 px
from the hull. Frame 700: 222 px. Raycasting those exact pixels named
**`DRV_Boot_L` at 3.075 m with `MB_chassis_fwd` 5 mm behind it**. Setting the
boots back 31 mm and 70 mm by hand left 113 px: `MB_chassis_fwd`'s skin cuts
diagonally into the footwell and no axis-aligned plane follows it.

**R2-247.** The real cause is that the lower body is outside the survival cell
altogether — the hip is 0.229 m below the seat pan and the thighs hang below
`MB_cell_floor`, among the backing panels. Where a panel covers them they are
hidden; where one does not, they reach the film (`DRV_Suit` against
`Turntable_Deck` at frame 828). The driver is now **trimmed against the car's
own datums**: every face whose centroid is below `MB_cell_floor`'s underside
(z 0.3860) or ahead of `CI_footwell`'s bulkhead (x 1.0695) is deleted —
**188,167 of 810,592 faces, 23.21 %**. Nothing visible is near it: the aperture
bottoms out at z 0.5849 and the seat pan at 0.4085, 0.20 m above the cut. The
cut edge is left open on purpose; it is inside the cell floor, it is never
seen, and capping it would add faces whose winding nobody would ever check.

**R2-248.** The boots are excluded from the render. After the trim they lie
wholly below z 0.45 and no camera in this film can see them; every pixel they
ever reached was a protrusion. They stay in the blend, trimmed, so an interior
shot can switch them back on.

**R2-249 — and then the gate hid the fix from itself.** `driver_containment`
forced every `DRV_*` object `hide_render = False` for its "driver present"
pass, which switched the boots straight back on — the objects `place_driver`
had just excluded. It reported the identical 12 px / 211 px leak before and
after the fix, so the fix looked like a no-op and I nearly went hunting for a
third cause. **A gate that overrides the thing it measures is measuring
itself.** It now restores the AUTHORED visibility — keyed objects render,
unkeyed ones keep their stored flag — and prints which. With that one line the
same build read 0 outside on every frame.

Also fixed: `present` was a per-frame gate, so frame 1200 — where the camera is
not pointed at the car and 0 driver pixels is the *correct* answer — failed the
run. Presence is now reported per frame and gated once over the run.

### The final containment result

| frame | beat | driver px | driver px, absent | outside aperture |
|---|---|---:|---:|---:|
| 2632 | 5 lap | 132,155 | 0 | **0** |
| 2625 | 5 lap | 23,441 | 0 | **0** |
| 828 | 2 launch | 17,004 | 0 | **0** |
| 700 | 1 showroom | 15,978 | 0 | **0** |
| 1200 | 4 transit | 0 | 0 | **0** |
| 2100 | 5 lap | 116 | 0 | **0** |

**POSITIVE control:** `--control-displace 0.45` shoves the driver through the
side of the tub and **294,539 of 294,637 px escape**. The gate can fail, so its
pass means something.

## R2-250 — the film append, preflighted rather than assumed

`build_film_scene.py` carries four hard refusals on the CAR collection and is
out of bounds to edit. `tools/driver_film_preflight.py` replays them in an
empty scene in about a minute:

    636 direct objects, CAR_ROOT animated, 8 CARRIG_* hubs, 0 orphan parents
    11 DRV_* across the append, 14 procedural materials on their slots
    DRV_Install on 'DRV_Install_CI_seatAction' -- its own COPY, not the car's
    appearance keys survive: 8 hidden at frames 1/300/579, 0 at 580 and 2632
    NO EXTERNAL ASSETS: 0 images with a filepath, 0 image-texture nodes

Two of its own checks were wrong first time and are worth recording: the
material check matched `bpy.data` by name prefix and reported the CAR's
`CarbonFibre` as the driver's; and the no-external-assets check flagged
`Render Result` and `Viewer Node`, Blender's own internal images, as external
assets.


## When the driver appears, and why it is not a pop

The opening shot is the problem: at frames 1–3 a driver riding the seat's
explode path would float **2.44 m above the car, 452 px tall, dead in frame**;
pinned at the home position he would sit in mid-air at 209 px. Neither is
acceptable and neither was noticed until the explode offset was projected.

Measured off-screen runs for a 12-point hull of the whole figure, after the
interior lands: **448–530** and **540–623**. He is keyed hidden until frame
**580** — 40 frames inside the second run — and the gate re-projects the hull
over frames 572–588 and refuses if any is on screen. **0 of 17 were.**

## Pose

`straight`, not the manifest's `hairpin_apex`. At the peak frame the car is dead
straight at 81.5 m/s, and **the car's own `SW_Shell` euler is constant across
every frame sampled — this steering wheel never turns.** A driver holding 62° of
lock on a straight is the first thing an eye catches.

## The placement path — not R2-182's

The driver goes into the CAR, and the car is **appended** into the film from
`world/car_anim.blend` by `tools/build_film_scene.py --car`. So
`tools/place_driver.py` writes `world/car_anim_driver.blend` = `car_anim.blend`
+ `DRV_*`, and the film is built with `--car` pointed at it.
`tools/build_film_scene.py` is untouched (hard constraint 7), and so is the car.
A world-side placement stage would have left the driver at a fixed world point
while the car drove away from him.

## R2-266 — R6 was a requirement addressed to nobody, and 152 bodies were counted and thrown away

`apply_breach.REQUIREMENTS` has carried **R6 `frame_transform_binding`** since the
module was written: *"whoever meshes mullion_intact / mullion_bent_stub /
curtain_wall_transom binds to the MUL\*/TRN\* names in `sim/out/breach_film.npz`."*
Nobody was whoever. The corresponding code in `build()` was:

```python
n_frame = 0
for j, nm in enumerate(names):
    if not (nm.startswith("MUL") or nm.startswith("TRN")):
        continue
    n_frame += 1
log("frame bodies in the table: %d ..." % n_frame)
```

It counts 152 bodies, **prints the count, and writes nothing.** So every film
built since the breach first shipped renders round 1's static, undeformed
aluminium grid straight across a 2.15 × 6.00 m hole — including the closing
wide, which is the only place in the film where the wound is legibly on screen
at all, and the biggest look in the picture.

`render/breach_f9/f9_1920_f0880.png` is the evidence and always was: the car is
already outside, the wall is a spiderweb, and **the frame it went through has
not moved by one vertex.**

**A printed count looks exactly like a used count.** The log line was truthful,
was read by everyone who ran the applier, and said `152` every time — the same
number a correct build would print.

**Fixed** by `sim/eastframe.py` + `apply_breach.build_frame()`. Round 1's
`GW_Right_Mull_04/05/06` and `GW_Right_Transom_0/1/2` are deleted at apply time
and rebuilt as the 39 pieces the bake partitions them into, keyed off the baked
transforms. Read back from the saved 4.99 GB blend: at frames 1 and 844 every
replaced member's world AABB equals round 1's to **0.0000 mm**, and the eight
mullions the fix does not touch move **0.0 m** at every frame tested.

---

## R2-267 — the bake breaks 1.55 m of one mullion and nothing else, and the headline says otherwise

The standing description is *"mullion 5 travelling 4.43 m and shedding two
segments."* Both halves are true and together they read as a frame that came
apart. Measured over every frame body in `sim/out/breach_film.npz`:

| body | max travel |
|---|---|
| `MUL05_S01` | **4.742 m** |
| `MUL05_S00` | **3.932 m** |
| `MUL05_S02` … `S07` (z 1.55 → 6.22) | 0.145, 0.112, 0.083, 0.057, 0.034, 0.017 m |
| every segment of mullion **4** (released) | ≤ **0.024 m** |
| every segment of mullion **6** (released) | ≤ **0.026 m** |
| **every one of the twelve released transom bodies** | ≤ **0.089 m** |

Mullion 5 has **eight** segments. Two leave. **Six stay, and so do all three
transoms, at every level, in every bay.** "Shedding two segments" is a
statement about 2 of 8 and it was being read as a statement about the member.

At the closing frame the wound is 57.7 × 77.8 px for the bridged aperture and
the scale is **12.96 px/m**, so 89 mm of transom travel is **1.2 px**. Applying
the bake faithfully changes about **20 px of roughly 4,500**. This was
predicted in `sim/out/eastframe_prediction.json` before the after-render was
queued, and the render agrees.

**So the sim and the film do disagree about the transoms, and the disagreement
is the opposite way round from the one in the brief:** `build_breach_sim.py`
does model them as active bodies that can shed, and the solver's answer is that
they do not.

---

## R2-268 — the head restraint is 97× the load it carries, across a joint the interface records as an expansion gap

Why six segments of mullion 5 stay up with nothing under them:

```python
add_constraint("CON_MUL%02d_HEAD" % uid, segs[-1], head, C_con,
               thresh=args.t_mullion_joint * 0.5, loc=(xf1, y, z1))
```

`t_mullion_joint` is 40, so the threshold is **20**. In Bullet's units at
240 Hz × 8 substeps that is **20 × 1920 = 38.4 kN** sustained (R2-092's own
conversion). What it is holding:

| | |
|---|---|
| mullion 5 above z 1.55 — 4.650 m × 4.7 kg/m | 21.9 kg → **215 N** |
| half of the six transom stubs in bays 4 and 5 — 6 × 6.16 kg | 18.5 kg → **181 N** |
| **total** | **396 N** |
| **ratio** | **97×** — and **179×** against the mullion alone |

And the joint it is applied to is one the wall interface itself says carries
nothing: `world/items/…_interface.json` records `head_expansion_gap_m` for
**every** station, **0.0172 m at mullion 5**. A stick curtain wall is
**bottom-anchored**; the head is a movement joint whose whole purpose is to let
the mullion grow and shrink without loading it. The sim bolts 38.4 kN across
it.

**This is the one parameter that decides whether the aperture reads**, and it is
not a threshold anybody tuned — it is `mullion_joint × 0.5`, inherited from the
segment-to-segment joint, applied to a joint of a completely different kind.

**Recipe for the re-bake** (`sim/build_breach_sim.py`, one call site): make the
head a `GENERIC` constraint with the vertical axis free — `add_constraint`
already takes `kind=` and a `post=` hook onto the `rigid_body_constraint` — or,
if a FIXED joint is kept, set its threshold from the dead load rather than from
the joint threshold. Predicted outcome: mullion 5's remaining 4.67 m falls, and
the six transom stubs bolted into it in bays 4 and 5 go with it.

---

## R2-275 — two M6 self-tappers are modelled as stronger than the mullion's anchor studs into the slab

The second reason nothing in the frame comes apart, and it needs no external
engineering data at all — the inconsistency is visible inside four consecutive
lines of `sim/build_breach_sim.py`:

```python
THRESH_MULLION_JOINT = 40.0      # segment-to-segment, 6063-T6, 0.075 x 0.160
                                 # = 76.8 kN sustained.  Was 900 = 1.73 MN.
THRESH_MULLION_BASE  = 120.0     # the anchor studs into the slab
                                 # = 230 kN sustained.  Was 1400 = 2.69 MN.
THRESH_TRANSOM       = 260.0     # M6 self-tappers into the front screw port
```

**260 is 499 kN.** The comment names the fastener: `wall_iface`'s screw port
`SP1` *"takes M6 self-tapper, 6.0 mm nominal, cuts its own thread; 40 mm
minimum engagement."* Two of those per transom end carry on the order of
**15 kN** before the screws shear or the 6063-T6 port strips — call it **T ≈ 8**,
so the shipped value is roughly **33× too strong**.

> **You do not need that estimate to see it.** The same block prices the
> mullion's cast-in anchor studs at 120 and two self-tapping screws into an
> aluminium extrusion at 260. **The screws are more than twice the anchors.**

R2-092 found exactly this failure for `THRESH_MULLION_JOINT` and
`THRESH_MULLION_BASE` — *"not a tuned value, a value that had never been
converted into units"* — corrected those two by 55× and 13×, and **left the
other two alone.** `THRESH_TRANSOM` and the head constraint (R2-268) are the
survivors of that sweep, and between them they are why the frame across the
aperture is welded to itself:

| joint | modelled | can carry | ratio |
|---|---|---|---|
| transom end → mullion | **499 kN** | ~15 kN (2 × M6) | **33×** |
| mullion head → head beam | **38.4 kN** | ~0 (it is a **17.2 mm expansion gap**) | ∞ |

Neither was ever swept, and `land_breach.sh`'s threshold assertion pins
`transom == 260.0` as part of "the configuration that was decided", so a bake
that changed it would be refused by the pipeline's own gate.

---

## R2-269 — the film's transoms are 250 mm from the ones that were simulated, and the 250 mm is the whole answer

| | z of the three transoms |
|---|---|
| round 1 `GW_Right_Transom_0/1/2` — **what renders** | **1.350 / 2.850 / 4.350** |
| `wall_iface transom_landings` — **what was simulated** | **1.600 / 3.100 / 4.600** |

Now put that beside R2-267's segment boundaries. Mullion 5 is cut into eighths
of 0.7757 m, and the segments that leave are `S00` (z 0.000 – 0.775) and `S01`
(**0.775 – 1.551**).

> **Round 1's transom 0 sits at z 1.3125 – 1.3875 — entirely inside `S01`, the
> segment the bake threw 4.74 m. The sim put its transom at 1.600, inside `S02`,
> which stayed. The transom that survives in the bake is bolted to a piece of
> mullion that is still there; the transom that renders is bolted to a piece of
> mullion that is four metres away on the apron.**

**And it is the constraint, not just the overlap.** `build_breach_sim._seg_at`
bolts each transom end to the mullion segment whose centre is nearest, and the
eight centres are at z 0.406, 1.182, 1.957, 2.731, 3.507, 4.282, 5.057, 5.832:

| transom | z | bolted to | that segment |
|---|---|---|---|
| **sim** transom 0 | 1.600 | **S02** | stays (0.145 m) |
| **round 1** transom 0 | **1.350** | **S01** | **left, 4.742 m** |
| sim / round 1 transom 1 | 3.100 / 2.850 | S03 | stays, both |
| sim / round 1 transom 2 | 4.600 / 4.350 | S05 | stays, both |

**The lowest transom — the one at 1.35 m, directly over where the car went
through — is the only one the 250 mm changes, and it changes it from supported
to unsupported.** Transoms 1 and 2 land on the same segments either way and are
genuinely held; they only come down if mullion 5 does, which is R2-268.

That is not a rounding difference, it is the difference between a supported
member and an unsupported one, and it has never been simulated either way. The
two geometries must be made to agree before the frame's behaviour means
anything — either the sim is rebuilt at round 1's landings, or the frame is
supplied at the interface's (see R2-270, which is the same choice).

---

## R2-270 — round 1's east frame stands 80 mm east of the plane the section calls outermost

| | x |
|---|---|
| round 1 `GW_Right_Mull_*`, `GW_Right_Transom_*`, `Sill`, `Head` | **14.920 … 15.080** |
| `wall_iface` / `mullion_intact.section()` | **14.840 … 15.000** |

`fracture_wall.json`'s own section note: *"x = 15.000 is the OUTERMOST surface
of the wall (the cover cap face). **Nothing in this assembly is east of it.**"*
Round 1's cap face is at **15.080**, and the applier has been supplying glass at
14.955/14.9665 into a frame 80 mm out of position ever since R3 moved it.

**Not fixed, deliberately, and this is the one judgement call in the job.**
Supplying the frame at the interface position would move **every** mullion 80 mm
and **every** transom 250 mm across the whole east elevation — the elevation
beat 1 looks at for 33 s from 1.6 m, where 250 mm is **583 px**. That is a large
change to a shipped beat, it is not what R6 was asked to fix, and it would
destroy the negative control that makes the rest of this work checkable.

So `sim/eastframe.py` cuts the replacement from **round 1's own box, at round
1's coordinates**, and merely partitions it. Consequences, all measured:

* six of the ten bays keep round 1's vertices exactly and must be
  **pixel-identical** between the two builds — R2-150's free negative control,
  obtained here from the fix's own blast radius rather than from an occluder;
* the flying pieces follow the bake's rigid motion about the **sim** body's
  centre, so a round 1 piece lands within the 80 mm the two sections differ by:
  for a 0.775 m bar thrown 4.7 m onto an apron, the last significant figure.

**Somebody has to choose**, and the choice is between beat 1's composition and
the section's own declared rule. It should be made looking at a beat-1 frame.

---

## R2-271 — R5's refusal was true, was specific, was overridden on every apply, and named the three objects

`sim/out/apply_film9.json`, `apply_film13.json`, `apply_film14.json` all carry:

```
glazing_pocket_clear  FAIL
pocket_intruders_in_the_clear_opening: [... GW_Right_Transom_0, _1, _2 ...]
```

and `sim/land_breach.sh` said, in as many words:

> *"NOTE: R5 will refuse. The refusal is TRUE and it is about ROUND ONE's frame
> — three transoms across the bays at z 1.35/2.85/4.35 — not about the glass
> being restored. **That is R6 and the geometry is not ours.**"*

**The check had already found the defect, written down the exact object names,
and been correctly explained — and then routed to a requirement that nobody
owned.** Every apply since has passed `--force` over it. R2-125 built the
triangle-vs-box test *specifically* because a vertex test could not see these
three bars, and the thing it was built to see was then classified as somebody
else's problem.

`apply_breach` now runs R5 **again on the scene it is about to write** and
reports the intruders classified by whether they cross the wound. Over the
wound: **3 → 0**. What is left is the south wall's frame, two light fins, and
this module's own transom remainder over the six bays that keep their glass —
all deliberate, none of them across the hole. `land_breach.sh`'s note is
rewritten.

---

## R2-272 — my own first classifier would have reported "0 intruders" while three of my objects lay in the pocket

Self-caught before it shipped, and recorded because it is R2-124's shape in a
fresh coat of paint. The first version of the post-build R5 report filtered on
the name:

```python
east_intr = [x for x in intruders if str(x[0]).startswith("GW_Right")]
```

`BF_TRN0_STATIC` is the same aluminium in the same pocket and does not start
with `GW_Right`, so the line would have printed **"0 east-wall intruders"** with
three of this module's own objects standing in the glazing pocket.

**And the obvious repair is also wrong.** Classifying by world AABB fails in
*both* directions here: `BF_TRN*_STATIC` is one mesh holding **two** boxes
(y −10.919…−4.3625 and 4.3625…11.0), so its bounding box spans the gap between
them and would report it standing in a hole it is nowhere near; round 1's single
21.9 m transom really does cross the wound and its eight vertices are eleven
metres away at the ends. The classifier now asks the same question R5 asks —
triangles against the box by the separating-axis theorem — restricted to bays 4
and 5's clear openings.

---

## R2-273 — the demonstrator: what 2h25m of re-bake buys, and the answer is that it buys the shot

**`render/film14_breach_r6_DEMO.blend` IS NOT A DELIVERY** and cannot become one:
it *deletes* `BF_MUL05_S02..S07` and the six transom stubs in bays 4 and 5, so
those members are absent on all 2,978 frames including beat 1's 33 seconds, and
a member that was never there does not break on camera. It carries a
`DEMO_DO_NOT_SHIP` marker object and its own docstring says so.

Its only job was to answer, with a picture instead of an argument, whether
2h25m of re-bake is worth scheduling. `sim/out/eastframe_prediction_demo.json`
was committed **before** its frames were queued and predicted that it *would*
read, that `grid_contrast` over the bridged wound would collapse while every
neighbour held, and that the **mean would barely move**.

f2978, 4K, 256 samples, measured against the R6 build:

| region | changed >8/255 | `grid_contrast` R6 → DEMO |
|---|---|---|
| **WOUND_bridged** | **11.17 %** | **0.03675 → 0.00777** (4.7× down) |
| NB_left_bay3 | 0.0442 % | 0.03697 → 0.03704 |
| NB_right_bay6 | 0.3095 % | 0.06954 → 0.06773 |
| CTL_UNTOUCHED_bays789 | 0.0288 % | 0.05310 → 0.05327 |
| CTL_UNTOUCHED_bays012 | **0.0000 %** | 0.04329 → 0.04350 |
| sky | 0.0000 % | — |

And the mean moved 0.5107 → 0.5142, **0.7 %** — so a reader who judged this on
mean radiance would report that nothing happened, on a frame where the wall
plainly opened. That is R2-274 stated as a number rather than an argument.

`render/r6_demo/COMPARE_f2978_before_R6_DEMO.png` is the three-way at 1:1 × 7.
Panels 1 and 2 are the same picture. **Panel 3 is a hole**: two bays of an
otherwise perfectly regular lattice with no lattice in them.

**So the frame is the thing, the re-bake is worth its 2h25m, and R2-268 and
R2-275 are what it has to change.** The demonstrator is an *upper bound* — a
real bake would have those members fall, and some would come to rest in the
lower aperture or on the sill rather than vanish.

---

## R2-277 — the one-take law, checked in pixels rather than argued from the mechanism

The continuity claim is that the supplied frame is invisible until it breaks,
because every piece exists on all 2,978 frames and its F-curve extrapolates
CONSTANT backwards to the home pose, which is where round 1's solid stood. That
is an argument about a mechanism. **Beat 1, f0400, rendered from both builds:**

| | |
|---|---|
| pixels bit-identical | **78.52 %** |
| changed > 1/255 | 0.1729 % (3,586 px) |
| **changed > 8/255** | **0.0000 % (0 px)** |
| **max &#124;Δ&#124;** | **3/255** |
| mean &#124;Δ&#124; | 0.2165/255 |

Against a measured repeat floor of **max 41/255** on the same camera at f2978,
3/255 is not a change, it is the renderer. **The east wall of beat 1 is the
wall it has always been**, and it stays that way until f860, where the AABB
readback also puts every replaced member on round 1's coordinates to
**0.0000 mm** at f844.

---

## R2-276 — the fix's real payoff is in beat 3, not in the frame it was asked to fix

The job was the closing wide. The closing wide is where R6 does the LEAST, and
that is a consequence of scale, not of the fix:

| | wound on screen | what the fix removes | reads? |
|---|---|---|---|
| **f2978**, ONER 74.0 mm, 595.4 m | 57.7 × 77.8 px | 216 px, mostly 20 px of a 1 px line | **no** |
| **f0866**, ONER 23.9 mm, ~3 m | the wall fills the frame | **2.54 %** of the whole 1920 × 1080 frame changed at 8/255, **0.532 %** at 32/255 | **yes, plainly** |

`render/r6_beat13/COMPARE_f0866_before_top_after_bottom.png`, same build pair,
same camera, same samples. Before: mullion 5 runs straight and unbroken from
head to sill with the car already through it. After: **its foot is torn out, the
remaining column is displaced and tilted, and a shed segment is tumbling in
frame beside the car.** At f0880 the two shed segments project to **426 × 428 px
and 461 × 292 px** at 4K — two aluminium bars, the size of the car's rear wing,
turning over in the aperture as the car leaves it.

That is 152 rigid bodies' worth of baked motion that the film has never once
rendered, and beat 3 is where it was always going to show. **The wound reads at
595 m as a texture and at 3 m as a wound**, and the fix is scaled the same way.

**The uncomfortable half:** none of that helps the last image of the film, and
the last image was the brief. It should not be allowed to.

---

## R2-278 — `grid_contrast` stops working below one pixel per member, and the picture caught it

Found by running my own metric on a frame I had not planned to measure, and it
fails there. The demonstrator against R6 at **f2940** (55.3 mm, wound
43.1 × 58.1 px):

| | f2978 (74.0 mm) | **f2940 (55.3 mm)** |
|---|---|---|
| changed >8/255, WOUND_bridged | 11.17 % | **12.44 %** |
| CTL_UNTOUCHED ×2 | 0.0288 / 0.0000 % | **0.0000 / 0.0000 %** |
| **`grid_contrast`, WOUND_bridged** | **0.03675 → 0.00777** | **0.02572 → 0.02672** |

**More pixels changed at f2940 than at f2978, the controls are cleaner, and
`COMPARE_f2940_R6_vs_DEMO.png` plainly shows two bays of lattice replaced by
two bays of nothing — and the metric does not move.**

The cause is scale and it is arithmetic. At f2978 the wall is 12.96 px/m, so a
75 mm transom is **1.00 px**. At f2940 it is 9.69 px/m and the same transom is
**0.58 px** — sub-pixel, spread by antialiasing across the very rows the local
baseline is taken from (±3–5 px = 0.31–0.52 m of wall at this range). The
"line" and the "baseline" are sampling the same thing, so their difference is
noise whether or not the member is there.

**So `grid_contrast` is valid only where the members it measures are at least
about one pixel**, and that is the closing frame and nothing shallower. It is
reported here rather than quietly used on the one frame where it worked. The
pixel-change fraction against a measured repeat floor has no such limit and
agreed with the picture at both frames; **where the two disagree, the picture
and the change fraction win.**

---

## R2-274 — "the wound is not darker" was right, and the mean is the wrong statistic for it

The standing measurement of the closing frame is that the wound is **not** darker
than adjacent glass — **+0.066** against the left neighbour, **−0.124** against
the right — *"because the wall is transmissive on both sides, so 'hole' versus
'glass' is not a radiance difference at all."* Reproduced independently here on
the delivered f2978 at 4K: wound 0.4142 mean luminance, left neighbour 0.4018,
right neighbour 0.5643.

That diagnosis is correct and it is also the reason the mean can never settle
the question. **What tells a viewer there is a wall is not the glass, it is the
lattice** — at 595 m the only thing rendering the east elevation is a grid of
1 px aluminium lines, and a bay whose glass has gone still has all of them.

So `sim/wallstats.py` measures `grid_contrast`: the amplitude of the transom
lines against a **local** baseline three to five pixels above and below, over
each region's own y span, at the three heights the camera track puts the
transoms at. Two details that are not decoration:

* **local** baseline, because the closing shot has a strong vertical brightness
  gradient across the wall (the lit floor and the plinth are behind its lower
  half) and a baseline half a metre away measures that instead;
* **absolute** value, because round 1's transoms read ~0.2 *darker* than the
  interior seen through the wound and *lighter* than the crazed glass in some
  retained bays. A signed contrast cancels across the wall and reports a lattice
  that is plainly there as nearly zero — R2-181's mistake, where a welded slab's
  mean normal cancelled and the detector reported nothing.

Measured on the delivered f2978: the wound's lattice is **as loud as everybody
else's** (0.037 against 0.037 / 0.068 for its two neighbours and 0.053 / 0.044
for the two untouched groups of three bays). **That equality is the defect,
stated as a number.**

## R2-351 — the defect

A scene that links datablocks out of another `.blend` renders **empty** on a
rented instance and the job is reported `done`.

Probe job `82ebdd064292` (agent `crowd-r2296`, 2026-08-04 04:41:59, scene
`f1-round2/render/r2296_before.blend`) returned a strip of sky over pure black
in **0.829 s**, recorded `blank: OK`, `lum_mean 0.0899`, `lum_sd 0.2322`,
`state: done`. Its grandstands are linked from
`f1-round2/render/world/assembly/r2/assembly9.blend` by **absolute path**.

The broker uploads the `.blend` (`remote.push_scene`) and a name-matched list of
sibling directories (`scenes.sibling_dirs_for` → `remote.push_scene_siblings`).
It has never uploaded a linked library and nothing in it ever read one. Blender
does not fail on an unresolved library: it substitutes placeholders, drops the
geometry, and renders the empty world fast.

## R2-352 — why every existing gate passed it

* **The blank gate.** Sky over black is not uniform, so `blank` read `OK` for a
  frame containing none of its subject. A metric that reads the same whether
  the thing is present or absent is not a measurement.
* **`remote.missing_assets`.** Its own docstring named the failure — *"the
  broker returns a subtly wrong frame and logs nothing"* — and then grepped for
  **one string**, `Image file <path> does not exist`. That is what a missing
  *image* prints. A missing *library* prints `Cannot find lib '<path>'`. The
  check named the right class of failure and tested for one instance of it.
* **Render time.** 0.83 s looked wrong to a human who knew the scene. It is not
  an anomaly in any corpus-relative sense: see R2-357.

## R2-353 — blast radius: one render, and it is the known one

Swept `jobs.scene` for every job in `state/broker.db` (2004 jobs, 1792 `done`,
344 distinct scenes) and every `.blend` in both project trees plus
`vast-render/scenes` (464 files, 226 GB), reading each file's `Library`
datablocks directly (`broker.blendlibs`).

| | scenes | delivered renders |
|---|---|---|
| link nothing | 291 | 1713 |
| link libraries | 3 | 5 |
| `.blend` no longer on disk | 50 | 74 |

The three that link:

* `f1-round2/render/r2296_before.blend` → `assembly9.blend`, absolute. **1
  render: job `82ebdd064292`, the black frame that started this.** Already
  discarded.
* `opus5-car-render/work/f1_exploded_posed_hq.blend` (3 renders) and
  `f1_ghost_posed_hq.blend` (1 render), both round 1, 2026-07-26. Both link
  Blender's **own bundled** `geometry_nodes_essentials.blend` — the "Smooth by
  Angle" modifier, applied to `Platform_Dais`, `Turntable_Deck` and six
  `SpotCan_*`. **Not affected**: see R2-355.

Across the whole corpus only 15 files link at all: those 13 round-1 car scenes
(all bundled essentials) and `r2296_before.blend` / `r2296_after.blend`.

**No delivered result other than the already-known black frame came through an
unresolved library. No wrong conclusion is left standing.**

## R2-354 — what the sweep cannot answer

Stated because the answer above is only as good as its coverage.

* **74 renders from 27 scenes whose `.blend` no longer exists.** Unanswerable
  from the file.
* **600 renders from 64 scenes whose `.blend` was modified after their last
  job.** Today's verdict describes today's file, not the revision that
  rendered.
* No `.blend1` backup sweep was run; 163 exist and might narrow the second
  group.

## R2-355 — Blender remaps its own bundled assets; the round-1 scenes are clean

`work/f1_exploded_posed_hq.blend` stores
`//../../../../usr/share/blender/5.2/datafiles/assets/nodes/geometry_nodes_essentials.blend`.
The instance has no `/usr/share/blender` (verified on 46712525) and the scene
is uploaded to `/workspace/scenes/<digest>/`, from which that relative path
resolves to nothing. It still renders correctly.

Measured, because three earlier attempts to simulate the instance were wrong:

1. Copying the scene elsewhere did not reproduce the failure — Blender falls
   back to the path **recorded in the file at save time**, which pointed at the
   real `/usr/share`.
2. Deleting that path's directory did not reproduce it either.
3. Running `/opt/blender-5.2.0-linux-x64/blender` in a mount namespace with
   `/usr/share/blender` bind-mounted empty — no component of the stored
   reference existing anywhere — gave `is_missing: False`, and Blender
   **rewrote** the sibling brushes library to
   `/opt/blender-5.2.0-linux-x64/5.2/datafiles/assets/...`. It remaps bundled
   assets onto the running installation.

Pixel confirmation: `mean|Δ|` between the two 640×360 renders is **0.000000**.
The metric is not blind — its positive control (a genuinely dropped linked
collection) reads `mean|Δ| 0.0178`, `max 0.52`, 3.8 % of pixels changed, and
its null (an image against itself) reads 0.

`scenes.is_bundled_essentials` therefore exempts these. A gate that refused
them would reject thirteen scenes that render correctly, and a gate with false
refusals gets switched off.

## R2-356 — `blendlibs`: reading the library table without opening Blender

`scenes.sibling_dirs_for` chose name-pattern matching over reading the blend's
path table, on the stated grounds that "reading the blend's path table means
loading a 288 MB file in Blender for every dispatch". True of
`bpy.data.libraries`; **not true of the file format**. `broker/blendlibs.py`
walks the block chain and reads only `LI` and `DNA1`:

* 4.99 GB `film14_breach.blend` — 5.5 s
* 4.21 GB `assembly9.blend` — 2.9 s
* 3 MB `r2296_before.blend` — instant

Memoised on `(path, mtime, size, inode)` in `scenes._library_closure_cached`,
so a 500-frame sequence submit pays it once.

The `Library.filepath` offset is **computed from the file's own `DNA1` block**,
not hardcoded, so it survives the field being renamed (`name` → `filepath` at
3.0) or moved. The block header layout covers all three encodings including the
Blender 4.4+ `file_format_version 1` header, whose field order is
`code, sdna, old, len, count` — *not* the legacy order with wider fields.

## R2-357 — the screen that does not work, recorded so nobody rebuilds it

"An empty render comes back suspiciously fast" is not a usable detector.
Modelling every done job's throughput as `pixels × samples ÷ render_sec`, the
known-bad job `82ebdd064292` ranks **1645th of 1788** — among the *slowest*,
because it was a 1280×720×4-sample probe. It was caught because a human knew
what that scene should cost, not because 0.83 s is anomalous.

## R2-358 — an unreadable file must never be reported as a clean one

The first sweep returned 207 of 344 files "unparseable": Blender has saved
zstd-compressed by default since 3.0 and `zstandard` is installed in neither
the system nor the broker's Python. `blendlibs` now falls back to the `zstd`
binary, which `remote.push_scene` already requires.

The second sweep returned 22 more: the `zstd` CLI **silently refuses any input
that is not a regular file** and exits 0 having written nothing, so a `.blend`
reached through a symlink decoded to zero bytes. All 22 were symlinks under
`f1-round2/work/dr_relief/before_root/`, every one a real 47 MB scene. Fixed
with `-f`.

Both were found only because an unreadable file is an **error** here, never
"no libraries". Had this module guessed "clean" on a read failure, 229 of 464
files would have been cleared by a sweep that never opened them.

## R2-359 — the gate, at submit

`scenes.require_resolvable_libraries` raises `UnresolvedLibraries` (a
`SceneError`, so it becomes a 400) from `POST /jobs` and `POST /sequences`,
before a GPU exists. A library counts as **carried** only if it will genuinely
be readable *on the instance*:

* a bundled Blender essentials asset (R2-355), or
* a resolved path under a directory `asset_dirs_for` mirrors — `push_assets`
  recreates those at identical absolute paths, or
* a `//`-relative reference that stays inside the scene's own directory and
  whose first component is a directory `sibling_dirs_for` uploads.

Everything else is refused, naming each path. An absolute `/home/zany/...`
library can never resolve: nothing creates that tree on a rented box.

## R2-360 — the gate, at load

`worker/server.py` refuses terminally when any `bpy.data.libraries` entry has
`is_missing` — Blender's own verdict, on the machine that actually loaded the
file, rather than a log parse. Unconditional: unlike a physics cache there is
no reading under which a render missing its linked geometry is the render that
was asked for.

It also logs at load **in both directions** — `LIBRARIES: none`, `LIBRARIES: N
linked, all resolved`, or `MISSING LIBRARY: <path>` — so "no libraries" and
"the check did not run" cannot look identical from outside. That is the hole
the blank gate fell into.

Blender's own bundled libraries are not special-cased in the worker and do not
need to be: they resolve against the running installation, and 46712525 carries
`/workspace/blender/5.2/datafiles/assets/`.

## R2-361 — `missing_assets` now matches every way Blender says "not found"

`ASSET_MISS_PATTERNS` is a list, and it is a list *because* the version that
shipped was one string. Captured verbatim from Blender 5.2 on 2026-08-04:

    Warning: Unable to open '<path>': No such file or directory
    Info: Cannot find lib '<path>'
    Info: LIB: Collection: 'X' missing from '<path>', parent '<direct>'
    Warning: N libraries and M linked data-blocks are missing (...)
    Warning: Image file <path> does not exist

`missing_libraries` splits out the subset that means geometry is absent, and
the two are reported at different severities: a missing image is a warning,
a missing library is an error.

`missing_assets` now returns the matched **text** rather than a bare path. The
old version stripped its one pattern down to a path, which read well in a log
line and discarded the only thing distinguishing a missing HDRI from a missing
`.blend`.

## R2-362 — why the broker warns and the worker refuses

`fleet._report_missing` logs; it does not raise. Raising from a scene switch
lands in `except Exception` and is read as "this instance failed to switch
scenes", which starts a redeploy — and every farm outage on this project has
been a healthy 5090 thrown away over something that was not the hardware's
fault. A scene that links libraries is wrong wherever it runs. The box is fine.

## R2-363 — worker code now refreshes on a scene switch

`_deploy` and the resume path pushed `worker/server.py`; `_switch_scene` did
not, so a worker-side fix took effect only at the next **full redeploy** —
which, on an instance deliberately held warm for hours, may be never. The push
is guarded: a failure logs and continues with the worker already on the box,
because "could not copy a file" must never become "this instance cannot switch
scenes".

## R2-364 — controls

`broker/test_broker.py`, 35 checks, all offline:

* **Positive** — a linked scene is refused, and the refusal names the path.
* **Negative** — `appended.blend`: the *same collection* from the *same source
  `.blend`*, appended instead of linked. Identical geometry, and its datablock
  names still carry the source's name. A detector keyed on "mentions another
  `.blend`" passes the positive and fails here.
* **Compressed positive** — the same scene saved zstd. The instance object in
  the fixture is load-bearing: a linked collection nothing references is orphan
  data, Blender drops it on save, and the fixture silently becomes a second
  copy of the clean one. That happened on the first attempt.
* **Carried positive** — a `//cache/` library is accepted, so the gate is not
  "refuse everything that links" wearing a policy's clothes.
* **Pattern controls** — the four library lines match, the old single pattern
  is asserted **blind** to all four, and lines from a *successful* load of a
  linking scene (`Info: Read library: '<same path>'`) must not match.
* Fixtures are written by Blender, never by the test. A `.blend` synthesised by
  the test would be a file shaped like whatever the reader expects, which is
  the round-trip-against-its-own-constant this project has shipped before. If
  Blender is unavailable the test **fails**; it does not skip.

## R2-365 — open

* The 74 + 600 renders in R2-354 remain unattributable.
* `POST /exec` is not gated. Exec jobs run arbitrary Blender scripts and may
  open scenes the broker never validated.
* The submit gate models what the upload *will* do. If `push_*` changes,
  `scenes.library_status` must change with it; the worker-side refusal is the
  backstop that does not depend on that model being right.
* **Recommendation on linked-scene support: refuse them.** See below.


## Recommendation: refuse linked scenes; do not pack, do not resolve at push

Three options were on the table.

**Refuse (chosen).** A linked scene is rejected at submit with a message naming
the paths and the fix. Cost: an artist who works with linked assemblies must
run *File > External Data > Make Local: All* and save a self-contained copy
under a `SCENE_ROOT` before rendering. For `r2296_before.blend` that is 62
datablocks and 769 k faces — a few hundred MB, not the 4.5 GB the linked
assembly implies. The step is manual and has to be redone whenever the
assembly changes.

**Pack at submit** (broker makes the scene local and uploads the result).
Cost: the broker would write `.blend` files, which it currently never does; it
would need somewhere to put them that is inside a scene root and outside the
project trees; every submit of a large linked scene pays a make-local pass;
and the content-addressed scene cache keys on the *source* file's hash, so a
packed copy needs a second identity or the cache silently serves a stale pack.
That last one is the same shape as the defect being fixed.

**Resolve libraries at push** (upload each library to the absolute path the
`.blend` asks for, the way `push_assets` already does for asset dirs).
Cost: it works, and it is the most transparent option — but it uploads the
*whole* library file. `assembly9.blend` is 4.2 GB against a 23 GB scene-cache
budget on a 32 GB disk, and five 4.2 GB assemblies sit in that one directory.
It also has to handle nested libraries, eviction of libraries independently of
scenes, and the case where two scenes want different revisions of the same
absolute path. That is a scene-cache redesign, not a fix.

Refusing is the only one of the three that cannot itself fail silently: the
scene either has no unresolved libraries or the job does not exist. If linked
workflows become common, revisit **resolve at push** — but only with the
per-library cache accounting the current one does not have.

## R2-381 — a 180-second ceiling on every scene push, and it condemned healthy GPUs

`push_scene` and `push_scene_siblings` rode the **multiplexed SSH master**, whose `ssh_base`
sets `ServerAliveInterval=30 × CountMax=6` — **180 s**. A bulk stream starves the master's own
keepalive replies until ssh tears the whole master down. Two 5.2 GB pushes died at **181.4 s**
and **168.7 s** with `ssh exit 255, no stderr | zstd exit -13`.

> **This is not a flaky link. Any scene needing more than 180 s to push would fail FOREVER** —
> and the broker reads a failed push as a bad host, so it condemns the GPU, rents a replacement,
> and fails identically on the same scene.

**That is the mechanism behind every "the 5090 died" incident on this project** — six false
alarms, two healthy boxes destroyed by the broker's own error classification, and a near
24-hour machine ban. The instances were fine. The push was hitting a wall the clock put there.

Moved to `ssh_nomux`. **Proved in production: a 4.68 GB push ran 590 s and completed.**

**A second, separate fault in the same area:** `host_at_fault` correctly declined to blame a
host stuck pulling its image — but it **condemned only the OFFER**, so machine 73811 was
re-rented on a *second offer of the same machine* and burned another 900 s. Fixed with
`stalled_machines`, deliberately kept **in memory** rather than added to the 24-hour-persisted
`bad_machines`, because that would have re-broken the DNS-outage protection. **A guard acting at
the wrong granularity is a guard that fires and changes nothing.**

## R2-382 — VRAM exhaustion returns a structurally perfect PNG with no picture

**Proven by controlled experiment, not inferred.** `film14_breach_R2281_DIAGNOSTIC.blend`,
content hash `20245107f4ef7a79`, **byte-identical both times**:

```
instance 46712525   BLACK   mean 0.000323
instance 46780377   OK      mean 0.3932, 189 levels
```

Corroborated by `film14_breach_r6b.blend`, unchanged on disk, rendering **4 good frames then 4
black** on that same box amid CUDA OOM and `OPTIX_ERROR_UNKNOWN`.

**The cause was measured independently by a second agent:** a fixed **17,737 MiB, constant to
the megabyte across 40+ minutes**, while our own Blender swung 518 → 13,432 MiB. One Blender in
the container, no defunct processes, block never moves. **A co-tenant, leaving us 14,870 of
32,607 MiB — 46 % of a card billed at $0.3444/hr.** It also explains why small `pvg_*` scenes
kept rendering correctly in between: only the 5 GB scenes reached the exhausted region.

The same fault seen from the other direction produced **six consecutive OOMs on one 4K frame,
then success on the seventh with nothing changed.**

> **Cycles under VRAM exhaustion returns a zero-filled buffer that becomes a structurally
> perfect PNG — correct dimensions, correct sha256, no picture. Every check upstream of the
> blank gate passes it.**

**The blank gate was right every time, and `--allow-blank` would have been exactly the wrong
response.** That is worth stating plainly because the pressure next time will be to silence the
alarm rather than read it.

Instance replaced. **46780377 verified genuinely ours** — three samples 4 s apart, identical:
12,928 MiB used / 19,184 free, exactly one compute process at 12,918 MiB, our Blender accounting
for all but 10 MiB of driver context. Total cost of the diagnosis: **$0.33** across four dud
instances.

**A method note worth more than the fault.** An early diagnostic query counted only
`blank IS NULL` as success and missed every `blank='OK'` row, which made it look as though **no
scene had ever rendered both black and fine — the exact opposite of the truth.** Correcting the
query is what exposed the good→black transitions that led to the root cause.

## R2-283 — `build_breach_sim.py` has refused to bake since R2-197 added the outfield, and the first thing anybody re-baking hits is the gate

Before any of the intended work could start:

```
REFUSING TO BAKE: 3 bodies start inside other geometry, worst 0.2990 m
(SIM_Threshold into SIM_Outfield).
```

R2-197 added `SIM_Outfield`, a 2 km catch slab spanning z −0.60 … −0.001, and
its own comment says it *"sits 1 mm below the floor slabs' top so it can never
win a contact against them"*. The floor slabs run z −0.30 … 0.0. **So by
construction the outfield contains 299 mm of `SIM_FloorIn`, `SIM_FloorOut` and
`SIM_Threshold`**, and the penetration gate — which R2-197 had itself widened
from "shards only" to "every body" — raises `SystemExit` before every bake.

It went in **without a bake behind it**: the shipped table `breach_full_m1.npz`
registers **233** box colliders and this build registers **234**, and the extra
one is the outfield.

**And R2-197 was itself a fix.** It was the repair for the 70 bodies that ran
off the end of the static ground and hung motionless 154 m underground for the
last 1,813 frames of the take. So **the repair for one defect silently
disabled the entire pipeline it was repairing**, and nothing noticed, because
the only thing that would have noticed is a bake and nobody ran one. **A fix
that has never once been exercised is not a fix, it is a claim** — and this one
sat in the tree for hours reading as done. The two commits either side of it
touched the same file and neither could have baked either.

Whether the outfield actually *does* catch the 70 is still unmeasured here and
is not this block's to certify: what can be said is that `motion_report` now
reports `caught_by_the_outfield`, it read **0** in the null (nothing should
reach it with no car in the scene), and the production bake is the first run
that will exercise it at all.

The rule the gate is for is *"nothing may be ejected by its own initial
condition"*, and a PASSIVE body cannot be ejected — Bullet never integrates it.
Every defect this gate has ever caught was an ACTIVE body: 582 clamped shards
inside the sill, a mullion foot 88 mm inside it, a head 110 mm inside the head
beam. All of those are still refused. Static-into-static overlap is now
**reported with its worst offenders** and does not stop the bake, because a
catch slab that silently overlaps something else is exactly what R2-197 said it
did not want to be.

---

## R2-281 — the transom threshold, derived from the fastener: 260 → 8.8, and the shipped value was 29.5× the joint

`sim/frame_thresholds.py`. The unit conversion is R2-092's and is the whole
reason this is arithmetic rather than taste: Bullet compares
`breaking_threshold` against the impulse applied in **one substep**, and at
240 Hz × 8 substeps a threshold T is a sustained **T × 1920 N**.

**Declared by `wall_iface`**, and read out of the file rather than retyped —
the module refuses if the sentence changes:

| | |
|---|---|
| screw port SP1 takes | *"M6 self-tapper, 6.0 mm nominal, cuts its own thread; **40 mm minimum engagement**"* |
| port | 8.5 mm bore with a **5.0 mm open mouth** — a race, not a tapped hole |
| extrusion / fasteners | **6063-T6** / **A2-70 stainless** |
| screws | **2 per transom end**, counted at all 3 × 11 stations, 90 mm apart |

**Three failure modes, smallest governs:**

| mode | | |
|---|---|---|
| **screw shear** | 0.60 × 700 MPa × 20.12 mm² = 8 450 N × 2 | **16 901 N** |
| thread strip | 659.9 mm² (FED-STD-H28), × **80.0 %** because the race is open (5.0 mm mouth on an 8.5 mm bore = 72.1° of circumference missing), × 152 MPa × 2 | 160 463 N |
| bearing | 6.0 × 40.0 mm × 0.80 × 1.5 × 241 MPa × 2 | 138 785 N |

**Screw shear governs at 16.90 kN. T = 16 901 / 1920 = 8.80.**

The shipped **260 is 499 kN — 29.5×** — and more than twice
`THRESH_MULLION_BASE`, i.e. two self-tapping screws priced stronger than the
cast-in anchor studs in the slab.

The previous estimate of this joint was *"~15 kN, call it T ≈ 8"*, stated as
engineering judgement. **It was right to within 13 %.** What is new is that the
number now comes from the declared grade and the declared engagement, and that
the two modes which do **not** govern were computed rather than dismissed — the
open-race reduction in particular is the one that could have made the aluminium
govern instead, and it does not: 160 kN against 17 kN.

### What is judgement, stated so it can be argued with

* **The biggest single uncertainty is a factor of two, and it is in the
  declaration.** `transom_landings` gives one *pair* of screw heights per
  (line, mullion), and at an interior mullion **two** transoms land there. Per
  end, or shared? Taken as **per end**, and the interface argues for it: its own
  note requires a shear block to clear the isolator feet at |y| = 10.0–12.2 and
  32.2–34.4 mm, which describes a block twenty millimetres out to *one* side of
  the centreline, mirrored — a block per side, not one straddling the centre.
  **The other reading is T = 4.4, and that is the low point of the bracket this
  block bakes.** The bracket is not half-and-double for its own sake.
* **Ultimate, not design.** No partial factor. A sim must break a joint at the
  load that breaks it, not at the load a code lets an engineer rely on. With
  EN 1993-1-8's γ_M2 = 1.25 the same arithmetic gives T = 7.04.
* The shear plane passes through the **thread**, not a plain shank (a
  thread-cutting screw is threaded to the head). A plain shank would give
  23.75 kN, T = 12.4.
* No flute reduction: a thread-**cutting** screw's flutes are at the lead, not
  at the joint face. A 15 % allowance would give 14.37 kN, T = 7.5.
* The 160 kN strip mode is **higher than the two screws could deliver in
  tension** (28 kN). That is not a contradiction — it is the declared 40 mm
  minimum engagement doing what a minimum engagement is specified for, making
  the joint fastener-governed. It is quoted as a computed mode, not as a
  capacity anybody could reach.

So the derived value sits in a defensible band of **T = 7.0 … 12.4**, and **8.8
is what the declared numbers give with no allowance either way.**

---

## R2-282 — the head is a movement joint, and the one number I refused to derive

`CON_MUL*_HEAD` shipped as a FIXED constraint at `t_mullion_joint × 0.5` = 20 =
**38.4 kN**, across a joint `wall_iface` records as
`head_expansion_gap_m` — **0.0172 m at mullion 5, and a gap at every one of the
eleven stations, 10.2 … 20.5 mm.** What it holds up once the car has taken the
bottom quarter of mullion 5 is 4.7 m of extrusion plus half of six transom
stubs: **41.0 kg, 402 N. Ninety-six times.**

It is now a `GENERIC` constraint with **x and y locked and z and all three
rotations free** — a slider, which is what an expansion gap is — and it is the
**default**, so the pipeline's own gate now refuses a bake at the *old*
configuration rather than at the new one.

**Its breaking threshold is deliberately unchanged at 20.** The lateral
capacity of the head anchor is not declared anywhere in `wall_iface` — unlike
SP1, which declares its fastener, its grade and its engagement — so it cannot
be derived and will not be invented. Keeping it means **nothing that falls in
this bake can have been bought by weakening the head**: the only thing changed
about this joint is its *kind*, and that follows from a declared geometric fact.

`land_breach.sh`'s stage-0 gate pinned `transom == 260.0` as "the configuration
that was decided", so it would have **refused any bake that corrected this**.
It has been moved onto the derived set, and it now also checks the head model,
which is recorded in the report's `thresholds` block for the first time — a
bake whose head model is not recorded is a bake whose frame behaviour cannot be
attributed afterwards.

### The third survivor, found and NOT changed

R2-092's own comment derives the segment-to-segment joint at **T = 16** (a
75 × 160 6063-T6 extrusion failing in bending near 30 kN) and the file ships
**40 = 76.8 kN, 2.5× its own derivation.** That is the same class of error as
R2-281, an order of magnitude smaller. It is left alone on purpose: it is not
what holds the frame across the aperture — that joint *already breaks* in the
shipped bake, twice — and moving it in the same bake would put two independent
variables in one controlled experiment. **Logged, not fixed.**

---

## R2-284 — "did it move" is the wrong question; the right one is "did it come apart"

R2-267 is what happens when the frame's behaviour is read out of a statistic
that is 96 % glass. `sim/framemotion.py` measures **joint separation** —

```
    || (a(t) − b(t)) − (a(0) − b(0)) ||
```

— which is zero for a rigid pair however far the pair travels together, and is
therefore the measurement that does not care whether the wall fell over or was
pushed. Each transom end is matched to the mullion segment
`build_breach_sim._seg_at` actually bolted it to, by the same nearest-centre
rule.

**My first threshold was wrong and the shipped bake caught it.** At 20 mm —
reasoned from the collision margin — it reported **18 of 95 joints broken and
all six of mullion 5's transom ends broken**, in a bake whose transom
constraints are at 499 kN and cannot have broken. A Bullet FIXED constraint is
*soft*: 24 sequential-impulse iterations hold to tens of millimetres, not to
zero. The shipped table brackets it instead, and the bracket is wide open:

| | |
|---|---|
| largest separation on a joint that did **not** break | **0.0725 m** |
| smallest separation on a joint that **did** (`MUL05_S00→S01`) | **1.3605 m** |

a factor of nineteen with nothing in it. **0.25 m**, and every run prints the
whole distribution so the gap cannot close silently.

**Baseline on the shipped table: 2 joints broken of 95**, both inside mullion
5's lower column; **0 of 6 transom ends**; max transom body travel 96.9 mm.

---

## R2-285 — beat 3's payoff, priced before the job could cost it

`sim/shedpx.py` projects every replaced east-frame piece at a film frame from
the film table and `eastframe.plan()` alone — no render, no Blender — so
no-regression can be answered the moment a bake lands rather than after the
farm comes back. It reads the table through `resample.read_film` and poses it
through that module's own `expand()`, so it measures the **same reconstruction
the applier keys**, not a second implementation of it.

Baseline, shipped R6 table, **f0880**: `BF_MUL05_S00` **391.4 × 358.5 px** at
4.65 m, `BF_MUL05_S01` **396.4 × 269.3 px** at 4.70 m. The standing description
of the same two segments is 426 × 428 and 461 × 292; mine is an axis-aligned box
of the eight projected corners and reads about 9 % smaller, so it is a
*comparable* measure rather than the same one — and the comparison it exists for
is before-versus-after through one instrument.

---

## R2-286 — the measuring instrument was checked against the work it has to extend

Before measuring anything new, `sim/wallstats.py` was re-run on the **existing**
R6 pair. It reproduces the previous block's published numbers exactly:

| region | grid_contrast before → after | changed > 8/255 |
|---|---|---|
| WOUND_bridged | **0.03722 → 0.03675** | 1.8114 % |
| NB_left_bay3 | 0.03660 → 0.03697 | 1.5915 % |
| NB_right_bay6 | 0.06775 → 0.06954 | 0.8400 % |
| CTL_UNTOUCHED_bays789 | 0.05324 → 0.05310 | **0.0432 %** |
| CTL_UNTOUCHED_bays012 | 0.04369 → 0.04329 | **0.0000 %** |
| sky | — | 0.0000 % |

and the measured repeat floor at 1/255 runs **2.0 – 13.6 %** across these
regions, which is why the verdict is taken at 8/255. The two untouched
bay-groups are inherited unchanged as the negative control.


*(results sections follow once the bake lands)*

## R2-287 — the null holds, and its headline number is a maximum over 378 shards decided by one of them

**P1 of the committed prediction, and the first result in.** 480 frames,
`--wake-all --no-car`: every body awake at frame 1, no car in the scene, the
wall must stand on its own. Run at the derived thresholds and with the head as
a slider, against `sim/tmp/n1.npz` — **the same 480 frames at transom 260 with
the head FIXED**, which is the exact before-half — and against `n2`, the
mullion 15/50 config R2-093 identified as the one that *breaks* the null.

**The frame stands, and that is the claim P1 made:**

| | n1 — transom 260, head FIXED | n2 — mullion 15/50 | **new — transom 8.8, head slider** |
|---|---|---|---|
| max mullion-body sag | 0.175 mm | 0.273 mm | **0.341 mm** |
| max transom-body sag | 0.078 mm | 0.139 mm | **0.148 mm** |
| frame joints broken (of 95) | 0 | 0 | **0** |
| mullion 5 column travel | 0.001 m | 0.001 m | **0.001 m** |

A third of a millimetre, on a wall filmed at 12.96 px/m. The joint got 29.5×
softer and the frame's dead-load response roughly doubled, from 0.175 mm to
0.341 mm. **P1 predicted sub-millimetre and it is sub-millimetre.**

**And the glass did not move either — but the verdict line says it did.**
`NULL VERDICT` reports `worst_px_on_a_pane_that_stays`: **11.52 px** for n1 and
**360.31 px** for this bake, which reads like a large regression. It is one
shard.

| retained bays 2 and 7, 378 shards | n1 | n2 | **new** |
|---|---|---|---|
| median | 15.0 mm | 19.5 mm | 21.3 mm |
| **p95** | **27.7 mm** | **27.6 mm** | **27.6 mm** |
| p99 | 30.2 mm | 37.3 mm | 52.1 mm |
| over 100 mm | 0 | 2 | **1** |
| over 1 m | 0 | 0 | **0** |
| worst shard | 33 mm | **`GS_b07_00010` 510 mm** | **`GS_b07_00010` 918 mm** |

**The p95 is identical to three significant figures across all three
configurations.** The bulk of the retained glass is unchanged. The whole
difference in the headline is `GS_b07_00010` — **the same shard n2 lost at a
completely different threshold**, and the third-worst shard in n1 at 32 mm. It
is one marginal shard in bay 7 that this solver intermittently loses hold of,
it was doing it before the transom threshold was touched, and a **maximum over
378 shards is decided by whichever one of them it is.**

That is R2-274's lesson wearing different clothes — there the *mean* was the
wrong statistic for the wound, here the *max* is the wrong statistic for the
null — and R2-098's, which is the same mistake twice already. The null verdict
should carry a percentile beside its maximum, the way `null_verdict` already
carries `mobility` so that a null passing because nothing can move is visible.
**Logged, not fixed: it is not this block's file to change mid-bake.**

The seven shards R2-199 left open at bond 100 as "a different mechanism,
off camera, logged rather than chased" are almost certainly this population.

## R2-288 — the low bracket point is the alternative reading of the declaration, and it takes the frame apart past the demonstrator

`p_t4`: **T = 4.4**, head slider, 400 frames — impact (sim frame 145) plus
1.06 s. This is not "half, for the sake of it". **4.4 is what the derivation
gives if `transom_landings`' one pair of screws per (line, mullion) is shared
between the two transoms landing there rather than being two per end.** The
bracket's low end is the other reading of the declaration, so this run is the
answer to a question about the source data, not about a knob.

Measured with `framemotion`, against the shipped table **truncated to the same
400 frames**:

| | shipped, 260 / fixed | **p_t4, 4.4 / slider** |
|---|---|---|
| frame joints broken (of 95) | 2 | **23** |
| mullion 5's transom ends broken (of 6) | 0 | **6** |
| max transom-body travel | **0.097 m** | **12.222 m** |
| mullion 5 column (S02…S07) max travel | 0.16 m | **13.603 m** |
| lattice line z0 / z1 / z2 max travel | 0.097 / 0.073 / 0.043 m | **12.22 / 6.77 / 5.62 m** |

**Every one of mullion 5's eight segments leaves, all three transom lines leave
across both bays, and this goes past the demonstrator** — which only removed
mullion 5 above 1.55 m and six stubs.

**And it does not stop at the wound.** `TRN_z0_b02→MUL02_S00`,
`TRN_z0_b02→MUL03_S02` and `TRN_z0_b06→MUL07_S02` break too: transoms coming
off **bay 2 and bay 6**, and bay 2 is a *retained* bay whose glass stays put
(max shard travel 0.283 m, 0 of 195 over 1 m). At 4.4 the film would render an
undamaged bay of glass with its transom hanging off it.

**The glass tells the same story from the other side, and the retained bays
hold in both:**

| bay | role | shipped med / max @400f | p_t4 med / max @400f |
|---|---|---|---|
| 2 | **retained** | 0.005 / 0.048 m | 0.005 / **0.283** m — 0 of 195 over 1 m |
| 3 | destroyed | 0.012 / 0.028 m | 0.007 / 0.046 m |
| **4** | destroyed | 3.663 / **113.601** m | **14.717 / 18.534** m |
| **5** | destroyed | 1.876 / 19.093 m | **15.109 / 19.213** m |
| 6 | destroyed | 0.027 / 6.969 m | 0.013 / 3.849 m |
| 7 | **retained** | 0.025 / 0.196 m | 0.010 / **0.528** m — 0 of 183 over 1 m |

The cascade is confined to the two bays the car goes through. Note what else
changed: bay 4's **113.6 m outlier is gone** — p_t4's whole field maxes at
18.5 m and its distribution *tightens* (p95 15.16 against a median of 14.72).
A frame that lets go releases its glass as a coherent field instead of holding
some of it while the solver squeezes a few shards out at 110 m/s. That is the
opposite of what a "weaker means wilder" intuition predicts and it is
consistent with R2-199's finding that the blow-up is an over-determined
network shedding residual as velocity.

**So the bracket's low end is not obviously wrong physically — it is wrong
compositionally**, and that is a judgement about a picture, which is where the
brief says such calls belong.

## R2-289 — the frame comes apart across the WHOLE bracket, and it took a 29.5× error to stop it

`p_t17`: **T = 17.6, twice the derived value**, head slider, same 400 frames.
The point of a high bracket is to find where the result stops holding. **It
does not stop.**

| 400 frames, same seed, same everything else | shipped **260** | **4.4** (other reading) | **17.6** (2× derived) |
|---|---|---|---|
| frame joints broken (of 95) | **2** | 23 | **19** |
| mullion 5's transom ends broken (of 6) | **0** | 6 | **6** |
| max transom-body travel | **0.097 m** | 12.222 m | **15.639 m** |
| mullion 5 column max travel | 0.157 m | 13.603 m | **6.642 m** |
| lattice z0 / z1 / z2 max travel | 0.10 / 0.07 / 0.04 m | 12.2 / 6.8 / 5.6 m | **15.6 / 5.5 / 5.4 m** |
| damage outside bays 4–5 | — | **transoms off bays 2 and 6** | **none** |

**All six of mullion 5's transom ends break at 4.4 and at 17.6 alike.** The
derived 8.8 sits between two points that both take the frame apart, so the
answer does not depend on resolving the factor-of-two in the declaration, and
it does not depend on the derivation being right to better than a factor of two
in either direction.

**What was actually holding the frame together was the 29.5×.** The band this
job could defend on the arithmetic is T = 4.4 … 17.6 — a factor of four, from
the shared-screw reading at one end to double the derived value at the other —
and the whole of it breaks the frame. 260 is 15× above the top of that band.

**17.6 is also the better-behaved end**, which is not what a bracket usually
does: its damage is confined to bays 4 and 5, where 4.4 sheds transoms off two
bays that keep their glass. So the two ends of the bracket fail in *opposite*
directions — 4.4 by spreading, 17.6 not at all — and the derived value sits
between them.

**One thing this cannot yet attribute.** Both bracket points carry the head
slider as well as the corrected transom threshold, so "the ends broke" and "the
column fell" are not yet separable. The hypothesis the numbers suggest is that
they are two different mechanisms doing two different jobs — the transom
threshold decides whether the six ends let go (0 of 6 at 260, 6 of 6 at both
4.4 and 17.6), and the head model decides whether the column then has anywhere
to hang. `p_hfix` (8.8, head **fixed**) and `p_hsld` (260, head **slider**) are
baked to settle it; they are the two off-diagonal cells of the 2×2 and they are
queued behind the production bake.

## R2-290 — the corrected frame unmasks a kinematic bulldozer: 2,647 shards freeze mid-slide, 88 m downrange, across two-thirds of the closing frame

**The production re-bake at the derived thresholds landed clean and its
headline numbers are right.** 1,657 frames, `EXIT=0`, `land_breach` stage 0
and stage 4 both PASS:

| | shipped | **re-bake** |
|---|---|---|
| connected aperture | 2.15 × 6.00 m | **2.15 × 6.00 m** |
| bay 4 / bay 5 vacated | 96.7 / 95.4 % | **96.7 / 95.4 %** |
| shards gone | 2,962 | **2,923** |
| glass mass gone | 772.4 kg | **765.9 kg** |
| mullion 5 max displacement | 4.43 m, **2** of 8 segments gone | **89.79 m, ALL 8 gone** |
| transom max displacement | **0.089 m** | **69.83 m** |
| mullions 0–4, 6–10 displacement | 0.0000 m | **0.0000 m** — controls hold |

**P8 confirmed, P2 confirmed, and P3 — which I wrote as 50/50 and declined to
predict — resolves in favour of the column falling.** I was too conservative
and the reason is instructive: I reasoned statically, and the six transom ends
that would have held the column up are broken by the same transient that
breaks everything else.

**And the bake is not shippable, for a reason that is not the thresholds.**

The car proxy is `kinematic=True` — it is driven by the film's own authored
animation and *must* be, so it cannot be slowed by anything it hits. In the
shipped bake that never showed, because the frame was 29.5× too strong and
held the glass back from it. With the frame correctly weak, the car ploughs
the unrestrained field down the forecourt at its own speed:

| median destroyed-bay shard | shipped | re-bake |
|---|---|---|
| speed at sim f200 / f400 / f1000 / f1650 | 5.56 / 1.78 / 0.25 / **0.05** m/s | 12.95 / **18.88** / 14.15 / **7.33** m/s |
| final position | x = 16.5, **at rest by t = 2.9 s** | **x = 103.0, still sliding** |
| median travel | **3.77 m** | **88.17 m** |

It *accelerates* between f200 and f400 while lying on the ground at z = 0.02,
up to 18.88 m/s — and the car proxy's own parts never exceed 19.90 m/s
(R2-096). It is being pushed, and an infinitely massive bulldozer does not
stop pushing.

**The consequence is R2-197's defect at thirty-eight times the scale.** At the
table's last key **2,647 of 3,796 shards are still moving faster than 1 m/s
(median 6.995 m/s)**, and `apply_breach` extrapolates CONSTANT, so they hang
motionless for the remaining ~1,300 film frames of a take with zero cuts. The
camera is east of the wall, so 88 m of eastward travel moves the debris
*toward* it: the frozen field projects across **u 884…3465, v 1041…2067** of
the 4K closing frame — 2,581 × 1,026 px, two-thirds of the frame width — where
the shipped field occupies 476 × 1,040 px at the base of the wall and is at
rest (median 0.033 m/s, 77 shards over 1 m/s).

**This is not a threshold defect and correcting the thresholds did not create
it.** Both bakes are wrong about the debris; the shipped one is wrong in a way
that happens to look plausible, because an over-strong frame was doing the job
the car proxy's mass should have been doing. Fixing one exposed the other, and
that is the second time in this block (R2-283 is the first).

**It also sits between the camera and the wound**, so the closing frame from
this bake cannot be used to measure whether the aperture reads. That is what
R2-291 is for.

> **A diagnosis I got wrong, corrected here rather than quietly dropped.** The
> first 4K render of this scene died with `Out of memory in CUDA queue enqueue
> (integrator_shade_volume)` and I attributed it to the enlarged debris field
> blowing up the volume integrator's bounds. **That is refuted.** The
> atmosphere is built by `world/build_sky.py` as two fixed boxes at
> `SLAB_HALF = 40000.0` — ±40 km — independent of anything the sim does, so
> debris going from 20 m to 250 m is nothing against it; `sim/` creates no
> volume object at all; the identical OOM hit a different agent's unrelated
> scene in the same 21-minute window; and the same scene rendered fine at 256
> samples minutes later. The instance was failing, not the scene (R2-292). The
> geometry barely moved either: 3,845 → 3,856 objects, 278,864 → 278,910 tris.
> I state it because the wrong diagnosis was plausible, self-serving — it made
> my own defect look bigger — and would have been believed.

### What is NOT wrong with it

* the `--wake-all --no-car` null holds (R2-287);
* the two untouched bay-groups are untouched — mullions 0–4 and 6–10 at
  **0.0000 m**;
* `swap-scene`, the R2-098 check asked of the scene that actually renders,
  **PASSES** with 0 problems;
* the table-level `--swap` check FAILs at 375 uncovered shards — **and it fails
  on the shipped table too, at 301**, same 2,118-frame worst gap. Pre-existing,
  24 % larger, not introduced here.

## R2-291 — beat 3 does not regress, it gets substantially stronger, and my own numeric check said the opposite

The one thing this job was told not to trade away. **f0866, 1920 × 1080, 256
samples, all three builds at identical settings**, so the comparison needs no
caveat:

| | changed > 1/255 | **> 8/255** | > 32/255 | mean &#124;Δ&#124; | max |
|---|---|---|---|---|---|
| pre-R6 → R6 (the previous block's result) | 17.929 % | **2.548 %** | 0.535 % | 1.208/255 | 150/255 |
| **R6 → R2-281 re-bake** | 65.834 % | **27.950 %** | **9.186 %** | **10.398/255** | 201/255 |

The 2.548 % reproduces the previous block's published 2.54 % exactly — the
third time this session an inherited number has been reproduced before being
extended. **The re-bake moves eleven times as many pixels at 8/255 as R6 did**,
and seventeen times as many at 32/255.

`render/r2281/COMPARE_f0866_preR6_R6_REBAKE.png`, three panels:

* **pre-R6**: the car is through and the mullion runs straight and unbroken
  behind it. Round 1's static grid.
* **R6**: mullion 5's foot is torn out. Real, and subtle.
* **re-bake**: **a full-height aluminium member is torn out and tumbling
  diagonally across the upper frame**, the structure above the car is broken
  and displaced, and the wall is visibly *open* over the car rather than
  cracked. It is a different and much stronger image, and every member is still
  present — nothing was deleted to get it.

**And my own numeric no-regression check called this a regression.**
`sim/shedpx.py` reported `BF_MUL05_S00` shrinking 140,310 → 7,800 px and
`BF_MUL05_S01` 106,754 → 10,394 px at f0880, an 18× and 10× loss on precisely
the two segments R2-276 celebrated. That reading is *correct and irrelevant*:
those two segments are the ones the car sweeps downrange (R2-290), so they get
smaller because they leave, while `BF_MUL05_S07` grows 375,069 → 582,492 px and
twelve pieces exist that did not exist before, because the upper column the
shipped bake left hanging now comes down.

**A per-piece metric cannot see that the event got bigger when the pieces are
not the same pieces.** It flagged `regression=CHECK`, which is what it should
do, and then the picture had to decide — exactly the order the brief sets out.
**P7 holds**, but not for the reason I wrote: I predicted the same two segments
would be at least as large, and they are not.

## R2-293 — the head restraint is not what was holding the frame up, and the control I built by construction is what proves it

Two things changed together, so neither could be credited. The off-diagonal
cells, all 400 frames, same seed, same everything else:

| transom / head | joints broken (of 95) | mullion 5's transom ends | max transom travel | mullion 5 column |
|---|---|---|---|---|
| **260 / FIXED** — shipped | 2 | 0 of 6 | 0.187 m | 0.303 m |
| **8.8 / FIXED** — transom alone | **19** | **6 of 6** | **15.448 m** | **15.907 m** |
| **260 / SLIDER** — head alone | 2 | 0 of 6 | **0.189 m** | **0.296 m** |
| **8.8 / SLIDER** — production | 21 | 6 of 6 | 15.223 m | 14.457 m |

**The derived transom threshold does all of it. The head model does nothing
measurable.** 260/SLIDER is indistinguishable from the shipped bake to three
decimals — 0.189 against 0.187 m, 0.296 against 0.303 m — and 8.8/FIXED already
produces the entire collapse, **with the head still bolted on at 38.4 kN**.

**This refutes the standing analysis and my own prediction with it.** R2-268's
headline is that the head restraint is 97× the load it carries and that six
segments of mullion 5 "hang in the air with nothing under them" because of it;
my P3 reasoned the same way and made the column's fall conditional on releasing
the head. **The 97× is a correct piece of arithmetic about a static load, and
the event is not static.** Once the six transom ends let go, the transient that
broke a 76.8 kN segment joint has no trouble with a 38.4 kN head joint. The
head was never the lever.

**And the only reason this is knowable is the decision to leave the head's
breaking threshold alone.** Had I derived a new lateral capacity for it — which
was tempting, and would have looked like more work done — the head cell would
have carried two changes and this table could not have been read. The control
was built by construction rather than measured afterwards, and it is what turns
"the frame came apart" into "the frame came apart *because of the number I
derived*".

**The slider stays**, because a 17.2 mm declared expansion gap is a movement
joint whatever the impulse does, and because R2-268's reasoning about what a
stick curtain wall is remains right. It just must not be credited with the
result.

## R2-294 — THE APERTURE READS, my committed prediction said it would not, and the controls say I cannot yet call it clean

`sim/out/rebake_prediction.json`, **P5**, written before the bake was launched:

> *"THE APERTURE WILL STILL NOT READ AS A HOLE AT 595 m. It will read as a
> DAMAGED lattice — a grid with one line interrupted — and not as an opening…
> I am predicting my own job does not achieve the thing it was pointed at."*
> Confidence 60–65 %.

**That is wrong.** f2978, R6 build against the re-bake, **both at 96 samples**,
same camera, same crop, same everything — a matched pair, because the first
attempt at this measurement compared 96 samples against 256 and failed its own
sky control at 1.49 % with max |Δ| 36/255, which is what the sky control is for:

| region | grid_contrast R6 → re-bake | changed > 8/255 | repeat floor |
|---|---|---|---|
| **WOUND_bridged** | **0.03963 → 0.00908** | **51.55 %** | 0.0 % |
| WOUND_connected | 0.03812 → 0.03917 | 44.92 % | 0.0 % |
| NB_left_bay3 | 0.03678 → 0.04311 | 14.77 % | 0.0 % |
| NB_right_bay6 | 0.06676 → 0.06971 | 14.72 % | 0.0 % |
| CTL_UNTOUCHED_bays789 | 0.05569 → 0.05467 | **5.21 %** | 0.0 % |
| CTL_UNTOUCHED_bays012 | 0.04262 → 0.03594 | **4.20 %** | 0.0 % |
| sky | — | **0.0004 %**, max 9/255 | — |

**And the demonstrator, rendered at 96 samples for the first time so it can be
compared on the same footing: 0.03963 → 0.00912.**

> **The re-bake's 0.00908 and the demonstrator's 0.00912 are the same number.**
> The thing R2-273 faked by deleting six segments and six stubs, the corrected
> threshold produces by breaking them — and it moves **51.55 %** of the wound
> region's pixels at 8/255 where the demonstrator moves 12.75 %, because the
> demonstrator only removed members while this also empties the bays.

`render/r2281/COMPARE_f2978_MATCHED96.png`, 1:1 × 7, three panels all at 96
samples. Panel 1 is a regular lattice across the full width. **Panel 2 has no
lattice in the middle two bays at all** — no vertical member, no transom lines,
the plinth and the lit interior reading clean through an opening. Panel 3, the
demonstrator, is *less* open than panel 2. It is a hole, and it is a bigger
hole than the thing that was built to prove a hole would be worth having.

### Why this is not yet the verdict

**Both untouched bay-groups fail: 5.21 % and 4.20 % at 8/255 against a measured
0.0 % repeat floor.** The fix touches no vertex in either. The sky is clean
(0.0004 %, max 9/255), so this is not exposure or tone-map — it is real content.

It is R2-290. The frozen debris field projects across **u 884…3465, v
1041…2399**, and both control rectangles (88 × 79 px, at u 1774–1862 and
1978–2066) sit inside that span; 772 kg of glass relocated 88 m also moves
every bounce and reflection in the shot. **So this pair shows that the aperture
reads, and cannot show that the frame is why.**

That separation is what `render/film14_breach_R2281_FRAMEONLY_DIAGNOSTIC_DO_NOT_SHIP.blend`
exists for — the corrected frame on the shipped glass, so the controls have
nothing moving over them. Its 256-sample render is outstanding: the farm's GPU
failed under it (R2-292).

**I am recording P5 as wrong now, before that render lands, because the matched
pair and the picture already settle the question it asked.** What the
diagnostic can still change is the *attribution*, not the answer.

## R2-292 — the render farm's GPU failed progressively for three hours and two agents lost frames to it, and the first person to blame it was blaming their own scene

Recorded because of how it was nearly misdiagnosed — by me — and because the
broker's own gate is what stopped a bad frame becoming a result.

Instance `46712525` degraded through three stages:

1. **`Out of memory in CUDA queue enqueue (integrator_shade_volume)`** — three
   occurrences in the broker's entire history, all inside one 21-minute
   window, across **two different agents and two unrelated scenes**.
2. **Byte-identical black frames.** Five or more jobs returning exactly
   `mean 0.00032, sd 0.00108, 2 distinct luminance levels` — uniform 1/255
   noise with no structure. It hit **agent r2281 and agent r2372 (roof), on
   different scenes**. One of them was my original spec re-run *unchanged*: it
   rendered all four tiles over 3m18s without erroring, then emitted black.
3. **Total OptiX failure** — `OPTIX_ERROR_UNKNOWN in optixDeviceContextCreate`.
   The box could no longer start a Cycles GPU render at all.

**The failures cluster in TIME, not by scene, agent, sample count or
persistent-data setting.**

**And I had a ready explanation that was wrong.** My re-baked scene's debris
field had just grown from 20 m to 250 m, so when it OOM'd in
`integrator_shade_volume` I concluded the enlarged bounds had blown up the
volume integrator. It is refuted four ways: `world/build_sky.py` builds the
atmosphere as two fixed boxes at `SLAB_HALF = 40000.0` — ±40 km, independent of
anything the sim does; `sim/` creates no volume object at all; the identical
error hit another agent's unrelated scene in the same window; and my scene
rendered fine at 256 samples minutes later. Object and triangle counts barely
move: 3,845 → 3,856 and 278,864 → 278,910.

**A defect I had just found made a coincidental failure look like its
consequence.** That is the most dangerous shape a wrong diagnosis can have, and
the only reason it did not stand is that the question was handed to somebody
with no stake in the answer.

**What worked:** the broker's `allow_blank=False` gate. A structurally perfect,
correctly sized, sha256-matching black PNG was delivered five times and refused
five times. Without it those frames would have been measured, and a black frame
differences against anything as a very large change.

**Not fixed here and not this block's to fix:** the instance was replaced, not
repaired, and nothing detects "this GPU has started returning noise" other than
the blank gate catching the extreme case. A frame that came back *subtly* wrong
would not have been caught.

## R2-295 — the nine predictions against the outcome, including the three I got wrong

`sim/out/rebake_prediction.json` was committed **before the bake was launched**,
so it could be wrong about the mechanism and not only about the pixels. It was.

| | claim | outcome |
|---|---|---|
| **P1** | the wake-all null still holds, frame sub-millimetre | **RIGHT** — 0.341 mm mullion, 0.148 mm transom, 0 of 95 joints broken |
| **P2** | the z = 1.600 transoms tear off mullion 5; max transom travel > 1 m | **RIGHT** — 0.089 m → 69.83 m |
| **P3** | mullion 5's column is 50/50; *cannot fall from statics* | **WRONG, and wrong in the interesting direction.** All eight segments leave, and they leave **with the head still FIXED** (R2-293). I reasoned about a static load path in a problem whose answer is a transient |
| **P4** | grid_contrast lands 0.015–0.032, central estimate 0.024; will not reach the demonstrator's 0.00777 | **WRONG** — 0.00908, which *is* the demonstrator (0.00912 on the same footing). My reasoning — "the fallen members do not vanish, they land in the lower aperture" — was right about the mechanism (they land at v 1293–1446) and wrong about the consequence |
| **P5** | **the aperture will still not read at 595 m**, 60–65 % | **WRONG.** It reads, and it reads bigger than the demonstrator |
| **P6** | 3–12 % changed at 8/255 in the wound | **WRONG, 4×** — 51.55 %. I flagged this as my least confident number and cited the previous agent under-counting by 4.5×; I under-counted by 4.3× |
| **P7** | beat 3 does not regress; more material moves | **RIGHT in outcome, WRONG in reasoning** — I said the same two segments would be at least as large; they are 18× and 10× *smaller*, and beat 3 is stronger anyway (R2-291) |
| **P8** | glass essentially unchanged, 2,900–3,020 gone, aperture within 1.95–2.35 × 5.80–6.10 m | **RIGHT** — 2,923 gone, 2.15 × 6.00 m exactly |
| **P9** | the one-take law is not at risk | **RIGHT on the mechanism, but see R2-290** — nothing pops out of existence and `swap-scene` passes, yet 2,647 shards freeze mid-slide, which is a different way to break a continuous take |

**Five right, three wrong, one right for the wrong reason.** The three wrong
ones are P3, P4 and P5, and they are all the same error: **I reasoned statically
about an event whose whole content is a transient.** P3 counted six transom
ends at 16.9 kN against 400 N of dead load and concluded they would hold — they
break, because the thing that loads them is the impulse that just threw a
775 mm bar 4.7 m, not the weight of the column.

**The one I most wanted to be right about was P5, and being wrong about it is
the result.** A derived threshold, bracketed on both sides, with the head model
held fixed as a control, makes the closing wide read as an opening. The frame
*was* the lever. The scale argument that made "it cannot read at 595 m" so
persuasive — 1 px transoms, a 57.7 × 77.8 px wound — was an argument about how
much *contrast* is available, and it turns out that removing a 1 px line from a
regular grid is exactly the kind of change a viewer's eye is built to see.


## The recommendation

**Do not ship `render/film14_breach_r6b.blend`.** The thresholds in it are
right and demonstrably so; the debris field in it is not (R2-290), and 2,647
shards frozen at 7 m/s across two-thirds of the closing frame for ~1,300 frames
is not a thing to put in a take with no cuts.

**Do not revert the thresholds.** They are derived, bracketed over a factor of
four, attributed to a single parameter by a 2×2, and they produce the picture
the demonstrator was built to argue for.

**The next job is the car proxy, not the frame.** It is kinematic because it
carries the film's authored animation and it must stay that way, so the
question is how an unrestrained field escapes an infinitely massive bulldozer —
and it is a question that only became askable once the frame stopped holding
the glass out of its way. `post_s` is also too short: the field is still doing
7 m/s at the last key and needs roughly two more seconds to come to rest.

### The attribution, as far as the frames in hand can carry it

The frame-only diagnostic render is still outstanding (R2-292 cost roughly
three hours of farm availability and four instances). What the matched-96 pair
can already say, without it:

**The debris field crosses every region. The lattice only collapses where the
frame left.**

| region | grid_contrast R6 → re-bake | change | frame in this region |
|---|---|---|---|
| **WOUND_bridged** | 0.03963 → 0.00908 | **−77 %** | **gone** |
| CTL_UNTOUCHED_bays012 | 0.04262 → 0.03594 | −16 % | intact, 0.0000 m |
| NB_left_bay3 | 0.03678 → 0.04311 | +17 % | intact |
| NB_right_bay6 | 0.06676 → 0.06971 | +4 % | intact |
| CTL_UNTOUCHED_bays789 | 0.05569 → 0.05467 | −2 % | intact, 0.0000 m |

The wound's collapse is **five times larger than the largest movement in any
region whose frame did not move**, and two of those regions move *upward*. A
debris field lying in front of everything cannot selectively erase the lattice
in the two bays whose members are the ones that left; it adds structure rather
than removing it. The projected positions agree: `BF_TRN0_b04` and `_b05` have
left row v 1102 for v 1293–1371 and `BF_MUL05_S02/S03` are off the wound
entirely, which is exactly the rows `grid_contrast` samples.

**This is an argument, not the control.** The control is the diagnostic, and it
is listed under "not confirmed".

## R2-296 — the negative control's PREMISE expired, and the control correctly reported it

`CTL_UNTOUCHED_bays012` failed at **1.482 % against a 0.000 % floor** on the
frame-only diagnostic, where nothing but the east frame differs. It is not a
false alarm. This module's own docstring states the premise: *"the R6 fix cuts
up mullions 4/5/6 and the transoms between y ±4.3625 and does not touch a
single vertex outside that band"*. True of R6. **False of the re-bake:**

| | mullions replaced | transoms partitioned (level, bay) |
|---|---|---|
| R6 | 4, 5, 6 | levels 0–2 over bays 3–6 |
| **re-bake** | **4, 5, 6, 7** | **also (0,7), (1,2), (1,7), (2,7)** |

`GW_Right_Mull_07` is now deleted and rebuilt as well, and the transom over
**bay 2** is partitioned — and bay 2 (y −6.6 … −4.4) lies **inside** that
control rectangle. The control was doing exactly its job: reporting that
geometry inside it changed, because geometry inside it did.

**The repair is to state the premise that still holds, not to widen the limit.**
`CTL_UNTOUCHED_bays01` (y −10.9625 … −6.6375) is untouched by *both* bakes:

> **0.0435 % changed at 8/255 against a 0.0000 % floor.**

The old rectangle is kept rather than replaced, so every number already
published through it stays reproducible.

---

## R2-297 — THE VERDICT: the corrected frame reproduces the demonstrator, in both statistics and in the picture

`render/film14_breach_R2281_FRAMEONLY_DIAGNOSTIC_DO_NOT_SHIP.blend` — the
derived frame on the shipped glass, so nothing but the east frame differs —
against the R6 build, **both 256 samples**:

| region | grid_contrast R6 → corrected frame | changed > 8/255 | repeat floor |
|---|---|---|---|
| **WOUND_bridged** | **0.03675 → 0.00785** | **11.33 %** | 1.77 % |
| WOUND_connected | 0.03078 → 0.04871 | 11.67 % | 1.59 % |
| NB_left_bay3 | 0.03697 → 0.03571 | 0.221 % | 1.50 % |
| NB_right_bay6 | 0.06954 → 0.06977 | 0.663 % | 0.93 % |
| CTL_UNTOUCHED_bays789 | 0.05310 → 0.05190 | 0.144 % | 0.043 % |
| **CTL_UNTOUCHED_bays01** | 0.03788 → 0.03798 | **0.0435 %** | **0.0 %** |
| sky | — | **0.0004 %**, max 8/255 | — |

**Against the demonstrator's 0.00777 and 11.17 %.**

| | `grid_contrast` | changed > 8/255 |
|---|---|---|
| R2-273 demonstrator — *members deleted* | **0.00777** | **11.17 %** |
| **R2-281 corrected frame — *members broken*** | **0.00785** | **11.33 %** |
| difference | **1.0 %** | **1.4 %** |

**The thing the demonstrator faked by deleting six segments and six transom
stubs, a threshold derived from two M6 self-tappers produces by breaking them —
and it lands within one percent on both statistics.** Both neighbours hold,
both valid controls hold, the sky is 0.0004 %.

`render/r2281/COMPARE_f2978_R6_vs_FRAMEONLY_vs_DEMO_256.png`, 1:1 × 7. Panel 1
is a regular lattice across the full width. **Panels 2 and 3 are the same
picture: two bays with no lattice in them, the plinth and the lit interior
reading clean through an opening.** The difference between them is that panel 3
achieved it by deleting members that then do not exist for 2,978 frames, and
panel 2 achieved it by breaking them — so in panel 2 they are *visible on the
apron below*, which is the honest version the demonstrator could not give.

**R2-273 asked whether 2h25m of re-bake would buy the shot. It bought the
shot.** The bake cost 3h06m, the frame comes apart across a fourfold threshold
band, and the whole effect is attributable to one derived number.

## R2-298 — the crowd's 894-source library would have shipped as 894 people standing in a field

`spectator_crowd.build_library()` has two branches. `yard=None` sets
`hide_render = True`; a yard puts the sources on a contact sheet and leaves them
**visible** — deliberately, and the docstring says why: `item_gate` picks the
median-triangle object out of the collection, and a hidden one renders an empty
sky. `world/items/spectator_crowd_test.blend`, the blend `PLACEMENT.json` points
at, is built through the yard branch:

```
894 library sources, hide_render True: 0, False: 894
yard bbox  world x[216.8, 247.0]  y[-4.3, 44.0]  z[0.95, 1.46]
           circuit  s 3476.8 .. 3531.0,  u -80.4 .. -24.0 m off the centreline
```

Projected through `film14_path.json`: **that yard is inside the 4K frustum on 545
of the 2,978 frames, closest at 60.6 m on f1134, where a 1.7 m figure is 105 px
tall** — roughly twice the height of the largest spectator anywhere in the film
(R2-297). Placing that blend as it stands puts 894 unaccounted human figures in a
field beside the circuit, each bigger on screen than anybody in the stands.

**The flag that makes the gate work is the flag that breaks the ship**, and neither
the gate nor `build_items` can see it: the gate wants them visible, and
`build_items`' checks are all about counts, datablock sharing and where the
population lands — none of which a visible library violates. `hide_render` is
re-read off the saved artefact rather than trusted.

---

## R2-299 — `NO_WORLD_FRAME` on `spectator_crowd` is false, and it was the decisive blocker

`world/items/PLACEMENT.json` holds `spectator_crowd` at HOLD on three blockers and
R2-227 records that **`NO_WORLD_FRAME` is the decisive one**: *"the test blend lays
the population out on a grid for the macro camera; the module never resolves world
positions, so there is nothing to place."*

Measured off the blend's own depsgraph:

```
realized instances                3,803
distinct source objects             577
REALIZED origins   world x[263.34, 395.69] y[51.65, 168.34] z[2.56, 10.05]
                   3,722 distinct x, 3,351 distinct y, 103 distinct z
TRIBUNE PRINCIPALE seats
                   world x[262.96, 397.02] y[51.65, 168.34] z[3.00, 10.06]
```

**The population was already standing on the real stand, at real circuit
coordinates, 400 m from the world origin.** 103 distinct z is the riser stack.
The grid is real but it is the *library contact sheet* (R2-298), a different
collection, and the row read the grid as the population.

The other two blockers are also wrong for this row: `PARTIAL_BUILD` quotes
"801 units against a declared 7800", which is `spectator_seated`'s object count and
not this row's own `expect_objects: 895`; and `GATE_NOT_ACCEPTED` is R2-227's own
flagged off-by-one — the row's `item` is `spectator_seated`, so `build_items`
derives the gate path from the manifest id and reads the **wave-1** module's
`ITEM_REJECTED` about geometry that is not in this blend.
`render/items/spectator_crowd/gate.json` is `ITEM_ACCEPTED`, 8 of 8, 0 FAIL,
`unmeasurable: []`, and it names the right blend, the right collection and a
`SPECX_` subject.

**`build_items.check_row` now honours an explicit `gate_json` on a row** and reports
the path the verdict came out of. Two modules deliberately serve one manifest
record; deriving the gate path from that record reads the sibling's verdict about a
different artefact. It happened here in the safe direction — a rejection standing in
for an acceptance — but the failure is symmetric and the other direction ships
un-gated geometry.

---

## R2-300 — the census's own human pattern matches `Screws`

`docs/ITEM-PRESENCE-CENSUS.md` §2.5 greps
`figur|person|crowd|spectat|skin|hair|human|crew|driver` over the ship's datablock
names. Re-run over `film14.blend`'s 32,069 object / mesh / material / collection /
node-group names, it returns **40 hits and every one of them is a screw** —
`SW_PanelScrews`, `RW_PodScrews`, `NOSE_CamScrews_L`, `wheel_tyre_RR_CoverScrews` —
because **`crew` is a substring of `Screws`**. Positive control on the same pass:
`/Grandstand|Seat/` returns 22.

The census's conclusion is unaffected and if anything strengthened — there is no
human geometry — but the count it published is 40 false positives, and a reader
checking it by eye would have found "crew" in the film and stopped.

---

## R2-301 — the crowd is placed: 11,129 people, `ITEMS_PLACED_OK`, `PLACEMENT_ITEMS_OK`

`world/items/spectator_crowd_world.py` — the seating plan for the whole circuit.
It builds no figure and composes no stand: `spectator_crowd.py` + `humankit.py`
do both and are `ITEM_ACCEPTED` 8/8. It supplies the three things they were never
given — the real seat register, the fold filter, and a per-block focus frame —
and takes the `yard=None` library branch so nothing ships visible.

**Built**, 451 s, `world/items/spectator_crowd_world.blend`, 1,952 MB:

```
library      894 sources, 16,222,085 tris, ALL hide_render
TRIBUNE OUEST       1,843 / 3,071 seats  60.0 % physical  76.7 % of open  focus f1434
TRIBUNE T15         2,510 / 4,077        61.6 %           78.2 %          focus f1098
VIRAGE OUEST        1,414 / 2,143        66.0 %           66.0 %          focus f1119
TRIBUNE PRINCIPALE  3,345 / 5,542        60.4 %           77.6 %          focus f1150
TRIBUNE EST         1,559 / 2,522        61.8 %           78.8 %          focus f1193
TRIBUNE TEMPORAIRE    458 /   995        46.0 %           46.0 %          focus f1214
                   11,129 / 18,350       60.6 %
```

**Read back off the artefact**, not off the build report:

```
900 objects, 900 distinct meshes, 0 shared, 0 instancers, 894 hide_render True / 0 False
11,129 realised instances from 746 distinct sources
commonest source SPECX_Lib0370_sit_b5 used 70 times = 0.629 % of the crowd
copies per source  min 1  median 8  max 70
world bbox x[32.39, 495.58] y[-138.70, 256.11] z[2.56, 10.71]
```

**CONTACT, WITH ITS CONTROL.** Every person's world position against the seat
register: **11,129 of 11,129 within 0.70 m of an UNFOLDED pan centre (100.00 %)**,
worst 0.62 m — which is the 0.62 m sideways step `build_field` gives the aisle and
steps roles, by design. **Control: 0 of 11,129 within 0.05 m of a FOLDED pan
centre.** Nobody is sitting on a seat that is folded up.

**PLACED, through the stage that exists for it.**

```
build_items --place spectator_crowd_world
  900 objects, 900 distinct meshes, 31,142,407 tris, top_share 0.1111 %
  gate ITEM_ACCEPTED, read from render/items/spectator_crowd/gate.json
  0 refused, 0 superseded removed, 0 REBUILD OWED
  on_circuit: s 89.3 .. 3637.4, u -45.37 .. +82.00, 0 units beyond u 900 m,
              max radius from origin 534.6 m, collapsed_at_origin False
  >> STAGE RESULT: ITEMS_PLACED_OK

tools/item_placement_gate.py --rows spectator_crowd_world
  PLACED  900 objects, 900 meshes, top 0.111 %, 0 unstamped
  >> STAGE RESULT: PLACEMENT_ITEMS_OK
```

**`rebuild_owed` is 0 and that is the finding, not a formality.** 24 of the 41
registry rows are blocked on `SUPERSEDE_WELDED` because the world already builds
the thing welded into a class mesh. The crowd is the one class that carries none:
`build_architecture._seat()` casts the chairs and leaves them empty, so spectators
go **on** them rather than **instead of** them. Verified rather than assumed —
R2-300's grep plus its positive control.

**Honest note on the run:** it reports
`STALE_CLOSURE: blend predates spectator_crowd_world.py`, correctly. The module
was edited after the build, and the edits are the R2-302 reporting change and
comments only — no geometry moved. The staleness arm is doing its job and the
line is left in rather than rebuilt away.

---

## R2-302 — the occupancy dial did nothing on four of six stands, and nothing said so

`plan_block(n_want=)` only **thins**, by group. A target ABOVE what
`compose_stand` produced therefore does nothing at all, and the block lands
wherever the occupancy field put it — with no line anywhere saying the dial was
inert. Four of six blocks are in that state:

```
block                asked   got   of open   dial
TRIBUNE PRINCIPALE   3,990  3,345   77.6 %   INERT, short by 645
TRIBUNE T15          2,691  2,510   78.2 %   INERT, short by 181
TRIBUNE EST          1,564  1,559   78.8 %   INERT, short by 5
TRIBUNE OUEST        1,843  1,843   76.7 %   thinned to target
VIRAGE OUEST         1,414  1,414   66.0 %   thinned to target
TRIBUNE TEMPORAIRE     458    458   46.0 %   thinned to target
```

`compose_stand`'s field is
`occ * (1 + 0.10(1-r01) - 0.45(2|c01-0.5|)^2.4 - 0.22 r01^2.2)`, which at
`occ = 0.98` averages **~0.78** of the seats offered: 0.995 at the front centre,
~0.76 at the back, ~0.64 at the ends. That shape IS the brief's *"denser at the
centre and front"*, so raising the mean means flattening it — the wrong trade.

**The consequence is a crowd with no ranking between stands.** Five of the six
land within 1.8 points of each other at ~61 % of their physical seats; only
TRIBUNE TEMPORAIRE separates. The intended reading — the main tribune on the pit
straight is the ticket everyone wants, the temporary scaffold at the far end is
where the unsold seats are — is not in the artefact.

**The fix is to bring the LESSER stands down, not the main one up**: 0.55 / 0.50 /
0.45 / 0.30 for VIRAGE OUEST / EST / OUEST / TEMPORAIRE, leaving the two the
camera reads biggest at the ceiling. That is a ~10,000-person build and one 451 s
rebuild. It is not done in this pass because the frames already on the farm are of
this artefact, and it is written down rather than quietly left.

`build_world` now reports `target_unreachable` and `shortfall` per block and
prints `TARGET UNREACHABLE: asked N, the occupancy field produced M`. A dial that
does nothing must not look like a dial that worked.

---

## R2-303 — the twin rate beats its control where heads are readable and loses where they are not

The red line is *"one tree spammed 100 times"*, and the instruments that carry
its name cannot see it: the world spam check cannot fire (one mesh at half a
million copies scores 7.01 % of 40 %), and `top_share` cannot either — the
crowd's commonest source is **0.629 %** of 11,129 people against a per-family
bound of 10 %. What a viewer actually reads is two identical people CLOSE
TOGETHER, so that is what is counted: **on-screen neighbour pairs within four
head-widths that share a source mesh**, at the film's own camera, against a
control that reassigns every person a source by a uniform hash over the same
894 slots.

```
frame  on screen  head px   pairs    same    rate     CONTROL same    rate
 2607      9,252      2.5  231,894    981   0.423 %           264   0.114 %
 1156      4,376      4.6   39,352     88   0.224 %            50   0.127 %
 1098        683      9.5    2,099      0   0.000 %             2   0.095 %
 1119        946      8.9    4,134      1   0.024 %             3   0.073 %
```

**Where a head is 9 px the separation beats a uniform draw outright — 0 pairs and
1 pair against a control's 2 and 3. Where a head is 2.5 px it is 3.7x WORSE than
the control, and that is a real cost of a real design decision.**

`spectator_crowd` says so itself: *"The defect is measured on screen ... but it is
FIXED in the world, because the plan does not know the camera and must not."*
`_separate_twins` guarantees no shared source within **2.6 m in the world**. At
f2607 the stands are seen at a shallow raking angle, so two people fifteen metres
apart in the world — different rows, different heights — project a few pixels
apart. The world-space radius cannot reach them, and the structured library makes
it worse than a flat draw would, because `library_index` confines a seated person
to one `(role, head-yaw bin)` cell of 64 sources rather than the full 894, and the
bearing spread across one block puts most of the crowd in one or two bins.

**It does not need fixing at f2607 and it would be wrong to fix it there.** The
head is 2.5 px. Two identical people eleven pixels apart at two and a half pixels
of head are not identifiable as identical by any viewer — and the frames where
they would be, f1098 and f1119, are the frames where the rate is zero. The number
is recorded because a variety claim quoted without the frame it was measured on is
the kind of number this project has had to withdraw before.

**148 of the 894 library sources are never instanced** (746 distinct used). Those
are `(role, bin)` cells the plan never reaches — the same effect from the other
end.

---

## R2-304 — occupancy is clumped 2.0x its own Bernoulli control, and the control is not zero

`humankit.occupancy_clumpiness` join-count on the realised field, per block,
against a Bernoulli draw at the same mean over the same open seats:

```
block                people   occ     clumped   bernoulli   ratio
TRIBUNE OUEST         1,843  60.0 %   +0.1583    +0.0916     1.7x
TRIBUNE T15           2,510  61.6 %   +0.1857    +0.1061     1.7x
VIRAGE OUEST          1,414  66.0 %   +0.2357    +0.1180     2.0x
TRIBUNE PRINCIPALE    3,345  60.4 %   +0.2025    +0.1126     1.8x
TRIBUNE EST           1,559  61.8 %   +0.1778    +0.0952     1.9x
TRIBUNE TEMPORAIRE      458  46.0 %   +0.2454    +0.0709     3.5x
MEAN                                  +0.2009    +0.0990     2.0x
```

**Every block is clumped above its own control and the emptiest is clumped
hardest** — which is the right direction: a half-full stand is where grouping
shows.

**The control does not sit at 0 and the reason has to be said rather than the
ratio quoted bare.** `occupancy_clumpiness`'s docstring promises 0 "for a uniform
Bernoulli field by construction", and the module's own selftest gets +0.0174. It
is +0.0990 here because the grid is `(row, col)` over the block's full extent and
this world's rows are cut by aisles, vomitories and 3,311 folded seats — every one
of those is a permanently-absent cell, and a permanently-absent cell makes its
neighbours look correlated. Both arms are computed on the same grid with the same
holes, so the **ratio** is like-for-like; the **absolute** clumpiness is inflated
for both and should not be compared with the module's own +0.1527.

---

## R2-305 — `hide_render` on an instanced library: the check that was worth doing before a farm job

The world build takes `build_library(yard=None)`, which sets `hide_render = True`
on all 894 sources so the contact sheet cannot ship visible (R2-298). **If that
flag also suppressed the geometry-nodes INSTANCES, the entire crowd would render
as nothing and every number in this pass would be about an empty stand** — and a
4K farm job would have been the thing that found out.

`spectator_seated`'s docstring asserts it does not (*"Measured, not assumed:
library objects carry `hide_render = True` and geometry nodes still instances
them"*), but that is a different module's library, a different node group, and an
assertion in a docstring is not a measurement of this artefact.

480×270, 24 samples, denoiser off, CPU, both arms, `CAM_f1098`:

```
render/r2296_after.blend    11,129 realised instances, 14 objects hide_render False
render/r2296_before.blend        0 realised instances,  8 objects hide_render False

pixels differing > 8/255   5,284 of 129,600  (4.08 %)
max |delta| 101            mean |delta| 1.291
changed region             x 66..479, y 0..35 -- the stand's own band, not the frame
```

**The instances render.** The mean frame brightness moves only 21.07 -> 20.72, which
is why the check is a *spatial diff* and not a mean: a crowd occupying 4 % of a
frame and roughly the albedo of the concrete behind it moves the mean by less than
half a level. **A metric that reads the same whether the thing is present or
absent is not a measurement**, and frame mean is exactly that here.

---

## R2-306 — the placement gate cannot be fooled by this row: ABSENT from the ship, PLACED in the placed blend

R2-231's strongest control, re-run for this row, because a gate only ever run
against the thing you hope is clean is not a measurement:

```
render/film14.blend        --expect absent
  spectator_crowd_world  ABSENT  0 objects, no collection named
                         'ITEM_spectator_crowd' in this blend
  >> STAGE RESULT: PLACEMENT_ITEMS_ABSENT_AS_EXPECTED_OK

render/r2296_items.blend
  spectator_crowd_world  PLACED  900 objects, 900 meshes, top 0.111 %,
                         0 unstamped
  >> STAGE RESULT: PLACEMENT_ITEMS_OK
```

Same gate, same registry, same row, opposite verdicts on the two artefacts.

---

## R2-307 — A WORLD REBUILD IS OWED, and the one number to watch is RAM

`render/world/assembly/r2/assemble.py`'s default `--mods` already ends in `items`
and `build_items` places every row whose state is `PLACE`. `spectator_crowd_world`
is now `PLACE`, so **the next assembly carries the crowd and nothing else has to
change**. Rows at `PLACE`: 2 of 42 (`crew_figure`, `spectator_crowd_world`).

Nothing in this pass has moved a vertex in `assembly9`, so `film14` and everything
built on it still has empty stands.

**The risk is memory, not time.** `build_items` adds 900 objects / 31,142,407
triangles / ~1.95 GB to a 4.21 GB assembly. This box has **11 GB of RAM total and
about 5 GB free with other agents running**, which is why the A/B in R2-305 is
built as a light scene rather than by appending the crowd into `film14.blend` —
that append was tried and is not possible here. The rented box has **10.5 GB of
disk free of 32.2 GB with a 23 GB scene-cache budget already 20.2 GB full**, so it
cannot hold a 6.5 GB assembly either without eviction.

Mitigation, and it is structural rather than hopeful: **`items` runs LAST**, after
surface, barriers, architecture, terrain and dressing. A rebuild that dies at the
items stage has already done the five class modules, and the failure is at the one
stage that can be re-run standalone against the saved scene.

---

## R2-308 — posture variety, read off the placed instances: 22 archetypes, commonest 12.59 %

`top_share` over source MESHES cannot answer the brief's question. 894 distinct
meshes could hold six poses, and `HUMAN-FIGURE-BRIEF.md` defect 2 is exactly
that charge: *"roughly six poses across ~600 figures ... this is one tree spammed
100 times wearing a shirt."* The library stamps `hk_arche` and `hk_role` on every
source, so the archetype a realised person is in is **readable rather than
inferable** — the same argument R2-116 made for `ob["posture"]`.

Read off `render/r2296_items.blend`'s depsgraph, all 11,129 realised people:

```
ROLE MIX                        POSTURE ARCHETYPES: 22 distinct
  sit         9,584  86.12 %      sit_forward        1,401  12.59 %
  stand         785   7.05 %      sit_upright        1,377  12.37 %
  turned        365   3.28 %      sit_back_folded    1,192  10.71 %
  aisle         180   1.62 %      sit_arms_spread    1,009   9.07 %
  steps         125   1.12 %      sit_phone            992   8.91 %
  lean_rail      90   0.81 %      sit_legs_crossed     872   7.84 %
                                  sit_slouch           748   6.72 %
                                  sit_hands_lap        744   6.69 %
                                  sit_elbow_knee       694   6.24 %
                                  sit_cheer            555   4.99 %
                                  sit_turn_neighbour   365   3.28 %
                                  + 11 on-their-feet archetypes, 785 people
```

**22 archetypes, commonest 12.59 %**, against `item_gate`'s 25 % ceiling and the
brief's "8-12 base postures". **1,545 people — 13.9 % — are not seated**: on
their feet in the rows, turned round to the row behind, in an aisle, on the
steps, or leaning on the front rail. `HUMAN-FIGURE-BRIEF.md` defect 7 was
*"nobody is standing, walking, or moving. Every figure is seated."*

**And every one of those 22 is a base archetype, not the final pose.** The pose is
re-solved per person from a body sampled per person, so two `sit_forward` figures
of different stature do not share a vertex. The number that says so is the
mesh count: 746 distinct source meshes realised, commonest 0.629 %.

---

## R2-309 — I claimed the light ate the wardrobe colour. REFUTED at 4K, by my own render.

**Recorded as wrong rather than quietly replaced.**

Off a local 1280x720 / 48-sample render of `CAM_f2607` (`work/r2296/qab2_after.png`,
magnified `qab2_zoom.png`) I wrote that the crowd "reads almost monochrome
blue-grey", that the polychrome wardrobe visible in
`render/items/spectator_crowd/p6/` was largely gone in the film's own light, and
I gave a mechanism for it: the sun is at 12.47 deg, the deck sits in its own
roof's shadow, and sky-dominant shadow light on cloth is blue whatever colour the
cloth is.

**The mechanism is real and the conclusion was wrong.** At 3840x2160 with proper
sampling — `work/r2296/cmp_f2607_before_after.png` and the native-resolution crop
`work/r2296/crop_f1098_A.png` — the wardrobe is plainly polychrome: oranges,
reds, greens, yellows, whites, tans and purples are all separable through the
blue, in numbers.

**What I actually measured was my own render, not the crowd.** 48 samples at a
third of delivery resolution on a shadowed subject leaves so much noise that the
denoiser-free frame regresses toward its local mean, and the local mean of a
crowd under a blue sky is blue. Chroma is the first thing a low-sample render
loses and the last thing an eye trusts.

**The general form of it is the one worth keeping:** *a colour judgement made
below the delivery resolution and sample count is a judgement about the
sampler.* Every appearance conclusion on this project has to name the resolution
and the sample count it was made at, and this one now does — the original claim
came off 720p/48, the refutation off 4K/256 with the denoiser on.

WHAT THE 4K FRAMES DO SHOW, looked at rather than measured:

* **It reads as a crowd, unambiguously.** Individual people separate into heads,
  shoulders and arms; postures visibly differ; raised arms and held props break
  the row line. It is not confetti and it is not wallpaper.
* **The before/after is not subtle.** `cmp_f2607_before_after.png` puts them one
  above the other: the BEFORE is a clean geometric field of empty blue seats that
  reads as a stadium before the gates open. It is not "a bit emptier" — it is a
  different and obviously unfinished picture.
* **The patchiness reads as patchiness, not as unfinished.** Light-blue empty
  seats show through the crowd in irregular clumps, and they read as seats nobody
  bought rather than as figures that failed to build. That is the 3,311 folded
  chairs (R2-296) plus the clump field (R2-304) doing exactly the job they were
  put there for.
* **The colour survives the shadow but is desaturated by it**, which is what a
  real grandstand under its own roof does.

---

## R2-310 — 97 % face the track, and the 0.34 % that face the back wall are supposed to

`HUMAN-FIGURE-BRIEF.md` defect 1, and `spectator_seated`'s own docstring, is the
one that cost a whole macro render: *"every figure sat FACING THE BACK WALL — the
placement applied a second `Rz(180)` on top of the local frame's own facing
convention."* It is invisible to every count in this pass and it is one number.

The seat's own facing in WORLD is **130.000 deg** — circuit +y through the
contract's 40 deg rotation. `build_field` bakes body yaw as
`hk_rot.z = radians(body_yaw_deg - 90)`, so a figure's world bearing is
`degrees(hk_rot.z) + 90`. Read off the built blend's own point attributes, all
11,129 people:

```
                      n     mean      sd    |d|>90   |d|>135 (BACK WALL)
TRIBUNE EST        1,559   +11.79   24.45      14         6
TRIBUNE OUEST      1,843   +17.93   25.08      24         7
VIRAGE OUEST       1,414    +4.47   17.87       0         0
TRIBUNE PRINCIPALE 3,345   +10.81   23.33      34        13
TRIBUNE T15        2,510    +3.97   22.69      23        12
TRIBUNE TEMPORAIRE   458   +12.70   20.88       0         0

WHOLE CROWD  n = 11,129   mean +9.86 deg   sd 23.44   p5 -35.4   p95 +38.2
  within  45 deg of the seat's facing   96.99 %
  beyond  90 deg                         0.85 %
  beyond 135 deg (facing the back)       0.34 %
```

**The mean is +9.86 deg, not 0 and not 180** — a small consistent turn toward the
car, which is the whole point of the per-block focus frame. **The 38 people beyond
135 deg are the `turned` and `aisle` roles doing their jobs**: somebody talking to
the row behind, and an aisle walker whose `aisle_side < 0` puts their stance at
`seat_face + 180`. **Control:** the defect this checks for is a 180 deg error, and
it would put 100 % of the crowd in that bucket rather than 0.34 %.

---

## R2-311 — two grandstands are both called OUEST and the second field silently became `.001`

Found by the facing check printing per-object rows: `SPECX_Crowd_Ouest` and
**`SPECX_Crowd_Ouest.001`**. `GS_BLOCKS` holds both **TRIBUNE OUEST** and
**VIRAGE OUEST**, and the field was named on `name.split()[-1].title()`, so the
two collide and Blender suffixes the second.

**Nothing is broken by it** — 900 objects, 900 distinct meshes, prefix intact,
`build_items` and `item_placement_gate` both pass — and that is why it needed
finding by reading a per-object table rather than a total. **A `.001` in a shipped
blend is the signature of an accidental duplicate**, which is precisely what
`build_items` reports `materials_name_collided` for, and a reader cannot tell
which of the two stands `Ouest.001` is.

Named on the block index now (`SPECX_Crowd_02_Viragouest`). **The fix is in the
module and not in the artefact**: the shipped `spectator_crowd_world.blend` still
carries the collided name until the next build, and `build_items` already reports
that blend as `STALE_CLOSURE` against the module. No geometry moves when it is
rebuilt — the field's points, sources and rotations are unchanged.

---

## R2-312 — `rq render` without `--scene` renders the broker's DEFAULT scene, not yours

Submitted four hours ago, to make a BEFORE frame of the film's empty stands:

    ./rq render --cam ONER --res 3840 2160 --samples 128 --frame 2610 \
                --agent crowd-r2296 -o work/r2296/before_f2610.png

No `--scene`. `./rq status` reports

    scene    default=/home/zany/f1-round2/world/beat1_anim.blend

and my own submission's stdout, read back at the end:

    ce1e3b29eb81  canceled: None
    ce1e3b29eb81  queued (depth 2)  scene=beat1_anim.blend
    50b10205d8bc  canceled: None
    50b10205d8bc  queued (depth 11) scene=beat1_anim.blend

**Both jobs were requeued against `beat1_anim.blend`** -- a scene that has nothing
to do with the film and need not contain a camera called `ONER` at all. The
client had shown `loaded film14.blend` at submit time, so the first submission
looked correct; the scene is re-resolved from the CURRENT default on requeue
after a cancel, and a job that sits in a queue long enough to be requeued
silently changes which blend it is about.

**This is R2-182's exact shape at the transport layer** -- *"the item is not in
the blend you are about to render"* -- and it is worse than R2-182's version,
because there the blend was wrong from the start and here it was right when it
was submitted. **A frame that comes back is not evidence about the scene you
named.** Both jobs cancelled; nothing else on the farm was touched.

Rule: pass `--scene` explicitly on every submission, and confirm from
`./rq status` that the job is waiting against the scene you named. The two frames
this cost were a convenience arm, not the A/B -- the A/B pair
(`render/r2296_before.blend` / `render/r2296_after.blend`) differs in exactly one
thing by construction and is immune to it -- but had it hit the A/B, the
before/after would have been two different worlds and nothing would have said so.

---

## R2-313 — the local GPU is GONE, and a local render falls back to CPU without saying so

Surfaced while rendering the crowd crops locally after the farm blocked, and
confirmed on two independent instruments:

```
nvidia-smi
  Unable to determine the device handle for GPU0: 0000:07:00.0: Unknown Error
  No devices were found

blender --factory-startup, cycles preferences, all four backends:
  CUDA   -> [('Intel Core i7-7700K CPU @ 4.20GHz', 'CPU', False)]
  OPTIX  -> [('Intel Core i7-7700K CPU @ 4.20GHz', 'CPU', False)]
  HIP    -> [('Intel Core i7-7700K CPU @ 4.20GHz', 'CPU', False)]
  ONEAPI -> [('Intel Core i7-7700K CPU @ 4.20GHz', 'CPU', False)]
```

**Cycles enumerates NO GPU under any backend.** The GTX 1070 is in an Unknown
Error state at the driver level, not merely busy.

**The failure mode is that nothing fails.** `scene.cycles.device = 'GPU'` on a
box with no GPU device does not raise; Cycles renders on the CPU and the frame
comes back correct, just one to two orders of magnitude later. An agent that
falls back to "render it locally" when the farm is congested will therefore see
a job that appears hung, time it out, and report a *scene* problem — a 2 GB
scene at 4K on a 4-core i7-7700K took this box past 7 GB of RSS and into 15 GB
of swap, alongside another agent's hour-long breach bake.

This does not change the standing rule (everything renders on the rented 5090);
it removes the fallback that rule implicitly assumed was there. **A local render
is not a slow option on this box, it is a CPU option**, and any script that
selects a device should print which device actually got selected rather than
which one it asked for.

---

## R2-314 — a point-in-frustum test is not a figure-in-frame test, and it picked the render frame

My own instrument, found by a second pair of eyes looking at the frame it
nominated. `occ_full.py` tested whether a seat's CHEST POINT lay inside the 4K
frame. A seated figure is not a point: it runs from the pan 0.45 m below that
point to a crown 0.40 m above it.

**At f2614 — the frame I nominated for rendering as "the largest seated figure in
the film, 54.4 px" — all 541 seats in frustum project to screen rows 0..36 of
2,160.** The stand is a 36-pixel sliver clipped by the top edge, and the seat
publishing 54.4 px has roughly 85 % of its figure above the frame. The agent
rendering it reported the frame as "effectively crowdless"; it was right, and the
crop cost a CPU render that could never have shown anything.

Re-run requiring the WHOLE figure inside the frame — `v_pan > 0` and
`v_pan + height < RES_Y` — over the same 5.77 M rays and the same control
(rays 200 m behind each seat: 0 of 400 unoccluded against 277 of 400):

```
                              point-in-frustum   whole-figure-in-frame
overall peak                    54.4 px  f2614      53.3 px  f2613
median per-seat peak            36.1 px               35.9 px
95th percentile                 44.9 px               44.9 px
seats >= 40 px                   5,384 (29.34 %)      5,234 (28.52 %)
seats >= 50 px                      23 ( 0.13 %)         16 ( 0.09 %)
seats >= 60 px                       0                    0
frames with an unoccluded seat     655                  650
```

**Two separate conclusions and they must not be merged.** The SIZE conclusion is
robust — 53.3 px against the manifest's 254 is 4.8x, and every distributional
number moves by under 3 %. The FRAME NOMINATION was wrong, and that is the half
that cost something: the defect does not perturb an aggregate over 18,350 seats,
it concentrates entirely in the extreme, which is exactly what you use to choose
what to render.

**A statistic can be right and the frame it points at useless**, and nothing in
the aggregate would ever have said so. It took rendering the frame and looking.

---

## R2-315 — the render farm cannot see linked libraries, and reports the result as `done`

**Six 4K jobs would have come back looking finished and containing no
grandstands.** `render/r2296_after.blend` and `render/r2296_before.blend` LINK
the eight `ARCH_Grandstand_*` objects out of
`/home/zany/f1-round2/render/world/assembly/r2/assembly9.blend` by absolute
path. `~/vast-render` uploads the `.blend` plus sibling directories matching
`blendcache_*|cache|caches|sim|sims|textures|tex|anim`, plus dirs named
`assets`. `render/world/assembly/r2/` is none of those, and **the broker has no
linked-library handling at all** — `grep -rniE 'libpath|bpy\.data\.libraries|
make_local|pack_libraries' broker/ worker/ scripts/` returns nothing outside
tests.

Proved rather than inferred. Probe job `82ebdd064292`, `r2296_before` at
640x360: **`work/r2296/probe_before.png` is a strip of sky over pure black.
Zero grandstands. 0.83 s.** The broker recorded `blank: OK` and `state: done`.

**And the guard that exists says the right thing and implements half of it.**
`broker/remote.py:1863 missing_assets()`:

> *"The worker reports these as `WARNING Image file <path> does not exist` and
> then renders anyway, so without this the broker returns a subtly wrong frame
> and logs nothing. Reading them back turns a silent wrong render into a visible
> warning naming the exact path."*

It greps for exactly one string: `Image file ... does not exist`. **A missing
linked .blend produces a different warning and is invisible to it.** The
docstring's own reasoning covers the case; the regex does not. The blank-frame
guard does not catch it either, because a frame with a sky in it is not blank.

**This is R2-182 one layer deeper.** R2-182 was *"the item is not in the blend
you are about to render"*. This is *"the blend you are about to render is not the
blend that arrives on the GPU"*, and it is worse in one specific way: the frame
comes back, renders fast, passes every automatic check, and looks like a result.

Disk was never the binding constraint, and the congestion was a coincidence.

**Fix, for whoever owns a scene root:** make the linked data local and re-save —
only 62 datablocks / 769,716 faces are linked out of that 4.21 GB assembly, so a
self-contained scene is a few hundred MB rather than the 4.5 GB the cache
arithmetic assumed. Not done here: that file must sit under a SCENE_ROOT and
`~/vast-render` is not mine to change. **Named, not fixed.**


## WHAT IS OWED, AND WHAT WAS NOT DONE

**Owed**

1. **A WORLD REBUILD** (R2-307). `assemble.py --mods ...,items` now places
   `spectator_crowd_world` because its registry row is `PLACE`. Until it runs,
   `film14` and everything on it has empty stands. Watch RAM, not wall clock.
2. **The occupancy gradient** (R2-302). One 451 s rebuild with
   0.55 / 0.50 / 0.45 / 0.30 on VIRAGE OUEST / EST / OUEST / TEMPORAIRE, leaving
   PRINCIPALE and T15 at the composer's ceiling. ~10,000 people instead of
   11,129, and the stands stop being interchangeable.
3. **The field name fix** (R2-311) lands in the same rebuild. No geometry moves.
4. **A person has to make the colour call** (R2-309).

**Not done, and named rather than implied**

* **The A/B is not against `film14` itself.** Appending 1.95 GB of crowd into a
  4.5 GB film needs ~6.5 GB and this box has ~5 GB free; the rented box has
  10.5 GB of disk against a 23 GB cache budget already 20.2 GB full. The shot is
  built as a light scene — the real crowd, the real stands linked out of
  `assembly9`, the film's own camera / lens / sun / exposure, and nothing else.
  Everything below the stands is black because there is no terrain in it.
  **The number that would make the A/B decisive — the fraction of a film frame
  the crowd changes — is therefore predicted (15.58 % at f2607, projected and
  ray-cast) and not rendered.**
* **`spectator_seated` (wave 1) is untouched and unplaced.** Its 8 declared
  dependants — `crowd_flag_handheld`, `crowd_idle_motion`,
  `spectator_bag_and_coat`, `spectator_child`, `spectator_seated_leaning`,
  `spectator_standing_in_row`, `spectator_umbrella`, `spectator_with_phone` —
  **do not exist**: 0 of 8 have a `.py`, a `_test.blend`, an
  `_interface.json` or a `render/items/<name>/` anywhere in the repo. Placing
  wave 2 instead of wave 1 therefore breaks a plan, not code. But it is a real
  cost: `sample_spec`, `POSTURES` and especially `anchors()` — the attachment
  frames a flag, an umbrella or a phone would hang off — exist **only** in
  wave 1, and `humankit` publishes no equivalent. Whoever builds those eight has
  to write an attachment-frame API that does not currently exist.
* **The 58-seat difference between `grandstand_riser_unit.seat_grid()` (18,408)
  and `build_architecture` (18,350) is measured but not explained.**
  `seat_grid()` drops any seat whose column falls outside a host riser unit,
  which is the likeliest cause, and it is not chased because the crowd is seated
  on the 18,350.
* **`spectator_standing_ga` — the general-admission banking at six corners — is
  still not placed and still stands on a synthetic bank.** Its host
  `ga_viewing_bank` has no module. That is a terrain item and not a human one.
* **No animation.** The crowd is static geometry in a 124 s continuous take.
  `crowd_idle_motion` is one of the eight that do not exist. A still crowd
  photographs as a still crowd, and at 36 px of figure and a moving camera that
  is a bet rather than a fact — it has not been checked in motion.

## R2-316 — `presentation_framing` reported `edge_angle_deg = 0.000` fifteen times, and could not have reported anything else

`tools/build_beatsheet.py` graded every beat-1 presentation with

```
edge = max(0.0, ang - degrees(asin(rad / nd)))
```

`ang` is the angle from the optical axis to the cluster's **centre**, and
`camera_station()` places the lens on the ray through that centre. **`ang` is
therefore identically zero at every presentation by construction.** Subtracting
the cluster's own angular radius from zero and clamping at zero measures the
angle to the **near** edge of a body the axis passes through — which is inside
the frame always, for every cluster, at every distance, on every lens.

The sign in front of `asin` is the whole defect. The edge that overflows is the
**far** one.

> **This is R2-062's lesson a second time in the same beat.** There, the rig's aim
> gate scored a 9.14 m dash at 7.24 degrees and passed it, because a camera can be
> pointed exactly at its subject and still be moving far too fast to photograph
> it. Here the same gate scores a cluster that is two and a half times too big for
> the frame at 0.00 degrees, because a camera can be pointed exactly at its
> subject and still be far too close to contain it. **Aim was measured twice.
> Photographability has never been measured at all.**

**Fixed.** The block now projects the eight bounding-box corners and reports what
the audience gets: `extent_frac_frame_h` / `extent_frac_frame_w`, the cluster's
depth span, the f-number that would hold that depth inside 2 px at 4K, and the
standoff at which it would fit on the lens it already has. The near-edge test is
**kept unchanged for the bridges and the close-out** — see R2-318.

Gate behaviour, `--check` against the shipped sheet, which writes nothing:

```
before   15 presentations, edge 0.00 deg each        STAGE RESULT: BEATSHEET_OK
after    15 presentations, all 15 FAIL on fit        STAGE RESULT: BEATSHEET_VIOLATION
```

and against the corrected candidate sheet: **0 framing failures, 15/15 fit.** A
gate that has never failed has not been shown to work; this one now fails on the
artefact known to be bad and passes on the artefact built to be good.

---

## R2-317 — every one of the fifteen presentations overflows its own frame, 1.06x to 2.59x

`standoff = max(radius * 1.55 + 0.42, 0.75)`, with `radius` the bbox
half-diagonal, fixes the subtended **solid angle** and knows nothing about the
lens. Measured, on the shipped stations (`tools/beat1_present_gate.py`, and
independently by the corrected gate inside `build_beatsheet.py` — two
implementations, same numbers):

| cluster | f | lens | f-stop | fills H | fills W | depth | blur at near face |
|---|---|---|---|---|---|---|---|
| MB | 1 | 35 | 2.8 | **2.14** | 0.34 | 1.44 m | 1.7 px |
| FW | 62 | 35 | 2.8 | **1.77** | 0.90 | 0.84 m | 5.8 px |
| NOSE | 85 | 58 | 2.2 | **2.59** | 0.63 | 0.44 m | 23.7 px |
| CI | 124 | 58 | 2.2 | **1.91** | **1.61** | 0.78 m | 40.8 px |
| halo_assembly | 155 | 35 | 2.8 | 0.75 | **1.11** | 1.07 m | 10.0 px |
| SP | 191 | 35 | 2.8 | **1.68** | 0.69 | 0.79 m | 3.6 px |
| FD | 236 | 35 | 2.8 | **1.85** | 0.52 | 0.70 m | 1.4 px |
| RW | 276 | 58 | 2.2 | **2.46** | **1.14** | 1.34 m | 86.4 px |
| EC | 305 | 35 | 2.8 | 0.75 | **1.21** | 1.10 m | 5.3 px |
| BB | 339 | 35 | 2.8 | **1.72** | 0.76 | 1.02 m | 10.3 px |
| SW | 386 | 58 | 2.2 | **1.06** | 0.70 | 0.25 m | 46.0 px |
| CORNER_RR | 463 | 58 | 2.2 | **2.54** | **1.44** | 1.34 m | 86.1 px |
| CORNER_RL | 512 | 58 | 2.2 | **2.44** | **1.33** | 1.25 m | 76.3 px |
| CORNER_FR | 551 | 58 | 2.2 | **2.29** | **1.44** | 1.28 m | 83.9 px |
| CORNER_FL | 591 | 58 | 2.2 | **2.32** | **1.45** | 1.30 m | 85.6 px |

**Fifteen of fifteen do not fit. Seven overflow in BOTH axes**, so there is no
crop of the frame that contains them. The audience is shown a fragment.

Confirmed in the picture and not only in the projection. `tools/beat1_bbox_overlay.py`
projects the cluster's evaluated world bbox through the film's own camera and
draws it on the rendered pixels, so the arithmetic and the photograph are the same
object:

```
f460  CORNER_RR   box spans x -962..5032   y -1540..4334   in 3840x2160   1.56 x 2.72
f591  CORNER_FL   box spans x -849..5101   y -1050..4216   in 3840x2160   1.55 x 2.44
```

On both, the centre marker lands exactly on the assembly and **all twelve box
edges leave the frame.** f120 is one defocused tube across the picture with no
identifiable part in it; f460 is a rear corner with its suspension links drawn
into ribbons.

**And f591 is the frame that says the geometry is not the problem.** It is
CORNER_FL's own presentation station, and the right-hand third of it genuinely
resolves — individual fasteners, the wishbone pickups, the upright, the weave on
the duct. What the audience gets is a tyre wall filling the left half and running
off the top and bottom of frame, with the assembly it is attached to cut off on
every side. **The parts are good enough to survive this beat. The camera is not
showing them whole, and it is not holding them still.** At 100 % zoom the centre
of that same frame is soft — 1.8 px of defocus and 49.8 px of smear, and the
smear is what you see.

---

## R2-318 — the corrected gate must not be pointed at the close-out, and why that is not special pleading

Re-graded on the far edge, the two hand-authored close-out keys fail too: the
front wing at t = 25.90 reaches 30.46 deg against an 11.91 deg half-frame.

**That is the shot.** Those keys are composed wides in which a wing running off
the edge of frame is the composition, and a review has already accepted them. The
fit test is a claim about a **presentation** — a station built to make one cluster
large enough to read has failed if the cluster does not fit. Applied to a composed
wide it says nothing.

So the fit test is gated on `presentation_dir_measured`, and the bridges and the
close-out keep the **old near-edge test unchanged**, still reporting RW at t=27.30
as 7.31 deg inside a 14.21 deg half-frame. A corrected metric that fails two
frames a review already accepted is a corrected metric nobody will believe.

---

## R2-319 — THE FOCUS TRACK IS NOT BROKEN. The confounded `CAR_ROOT` comparison is withdrawn

The suspicion was that beat 1's `focus_distance` does not track its subject,
based on samples against the distance to `CAR_ROOT`. **In beat 1 the car is
exploded across 616 parts and `CAR_ROOT` is the assembled body's origin.** The
mean gap between "distance to CAR_ROOT" and "distance to the cluster actually
being presented" is **1.904 m** — that is the confound, measured, and it is now a
standing negative control inside `tools/beat1_focus_track.py --selftest`.

Against the right reference, from the blend, at the fifteen stations:

```
worst |focus_distance - range to the presented cluster's CENTRE|   0.053 m
typical                                                            0.000-0.028 m
```

**The focus lands on the presented cluster's centre to within a few centimetres
at every station.** `camera_station()` returns the standoff and
`build_beatsheet.py` writes that same number into `focus_distance_m`, so it is
correct by construction and the construction holds. Beat 1's focus track is
correct in the sense it was accused of being wrong.

**What is wrong is that the cluster is far deeper than the depth of field.** At
58 mm, f/2.2, focused at 1.503 m, the range that stays inside 2 px at 4K is
**53 mm**. The corner cluster it is presenting is **1300 mm deep**. The centre is
sharp to 0.2 px and the near face is blurred by **86 px**:

```
CORNER_FL f591   focus 1.503 m   depth 0.87 -> 2.17 m   DOF 1.477 -> 1.530 m
                 blur: centre 0.2 px   far face 36 px   NEAR FACE 89 px
```

13 of the 15 presentations are not fully in focus; only MB and FD are, and only
because they are the two furthest stations.

---

## R2-320 — framing is a PRECONDITION of focus, not a parallel defect, and the law says so in closed form

The exact thin-lens blur, `C = (f/N) f |s - s_f| / ((s_f - f) s)`, inverted for
the f-number that holds a body of depth `D` and widest extent `E` sharp to a
circle `c` while it fills a fraction `fill` of a frame of sensor height `h`:

```
    N_required  =  D * (fill * h)^2 / (2 c E^2)
```

**Independent of focal length and of standoff.** Both cancel, because the
standoff that achieves a given fill is itself proportional to the focal length.
Two consequences decide the order of the fixes:

1. **At the shipped standoff there is no aperture that works.** The corner
   clusters fill 2.3-2.5x the frame, and holding their depth inside 2 px there
   needs **f/35 to f/37**. That is not a photographable aperture, it destroys the
   background separation the brief asks for, and it is deep into diffraction.
2. **At a standoff that makes them FIT, f/5.2 to f/9.0 suffices** — a normal
   aperture, and not an unfamiliar one in this film: **beats 4 and 5 run at f/5.6
   for all 346 of their keys**, and beat 3 ramps 4.0 -> 5.6 across its 43. Beat 1
   is the outlier at f/2.2-3.2, and it is the beat that has to hold a 1.3 m body
   1.5 m from the lens.

> **Fix the framing first. Not as a preference — as a precondition.** The focus
> cannot be fixed at today's standoff by any means. Once the fill target is
> chosen the required aperture follows in closed form and is invariant to *how*
> the fill was achieved, so the aperture is a one-line consequence of the framing
> decision and never needs its own iteration.

---

## R2-321 — the largest reason beat 1's middle third does not read is neither of them. It is the 180-degree shutter

`use_motion_blur = True`, `motion_blur_position = CENTER`, shutter 0.5 frames
(`anim/build_camera_rig.py`:772). A 180-degree shutter smears a static point by
half its per-frame image displacement. Measured at the fifteen stations, in 4K
pixels, holding the cluster box fixed between f and f+1 so this isolates the
**camera's** contribution:

```
median smear at the presented cluster's CENTRE      42.3 px
worst at a station                                 189.4 px   NOSE, f85
worst anywhere in the tour, at a cluster's CENTRE  628.1 px   f532
worst anywhere in the tour, at its NEAR FACE       808.0 px   f532
best frames of the close-out                    1.6-28 px    f648-792
```

**The beat sheet's own pan limit permits this and nobody converted it into
pixels.** `weave_spec.pan_limit_widths_per_frame = 0.12`; the sheet reports the
tour peaking at 0.0939. **0.0939 of 3840 px is 361 px per frame, and half of that
is 180 px of smear.** The limit is expressed in a unit that is resolution-free,
and the picture is not.

This is why f460's suspension links are ribbons and why the 100 % crop of f200
has no edge in it anywhere: at those frames the depth-of-field blur is 2-8 px and
the motion blur is 40-120 px. **A DOF fix alone would not have made the middle
third read.**

**It also explains the protected region without one word about taste.** Across all
791 measurable frames of beat 1 (`tools/beat1_smear_profile.py`, the smear of
whichever cluster is nearest the optical axis at each frame):

(all four columns are the smear at the cluster's CENTRE, which is the smallest
value on that cluster; the near face runs higher — 808 px at f532)

```
                          n    median      p90       max   frames over 20 px
beat 1, all             791    42.1 px  149.4 px  628.1 px   580  (73 %)
  the presentation tour 590    54.7 px  184.5 px  628.1 px   519  (88 %)
  CORNER_FL + close-out  57    30.1 px   49.8 px   62.8 px    55  (96 %)
  PROTECTED f648-792    144     1.5 px    6.7 px   28.3 px     6  ( 4 %)
```

**The region a review called the best material in the film is the region where the
camera stops moving: 1.5 px of median smear against 54.7 px over the tour, a
factor of 36.** 88 % of the tour is over 20 px and 4 % of the protected region is.
No aesthetic judgement is needed to separate them.

**And the frames agree with the arithmetic without being asked to.** f648 and f700
are the protected region and they are the first frames of beat 1 in which the
picture is a picture: at f648 the monocoque, halo, floor, front wing, suspension
and all four wheels are present, whole and readable in one composed frame; at
f700 the car is finished and head-on, with the showroom's own signage legible
behind it. Every frame rendered from the presentation tour — f120, f400, f434,
f460, f500, f591 — is a fragment of one cluster, larger than the frame, and
smeared.

**The two populations separate on an absolute measure too, not only on
composition.** RMS image gradient per pixel — how much detail actually survives to
the delivered frame — across the ten frames rendered:

```
the presentation tour                      protected
  f400  0.00270      f300  0.01101           f648  0.01610
  f120  0.00305      f434  0.01109           f700  0.02399
  f591  0.00583      f200  0.01285
  f500  0.00615
  f460  0.00625
  median 0.00625                             median 0.02005
```

**The protected region carries 3.2x the surviving detail per pixel of the median
tour frame, and 8.9x that of f400.** Nothing about the geometry or the materials
changed between them. The camera slowed down.

Put beside the defocus at the same point in the same frame
(`tools/beat1_blur_budget.py`) — the two blurs, per frame, at the centre of
whichever cluster is nearest the optical axis:

```
                          n   motion > defocus   both under 2 px   med motion   med defocus
beat 1, all             791    752   (95 %)        95  (12 %)        42.1 px       3.6 px
  the presentation tour 590    555   (94 %)         2  ( 0 %)        54.7 px       6.1 px
  CORNER_FL + close-out  57     57  (100 %)         0  ( 0 %)        30.1 px       1.8 px
  PROTECTED f648-792    144    140   (97 %)        93  (65 %)         1.5 px       0.3 px
```

**Camera motion is the larger of the two blurs in 95 % of beat 1, by a factor of
12 in the median. Two frames out of 590 in the presentation tour have both blurs
inside 2 px. Sixty-five per cent of the protected region does.**

Read the defocus column as the BEST case and not the typical one: it is measured
at the cluster's centre, which is the one point the focus is pinned to. At the
corner stations the same cluster's near face is 76-89 px out (R2-317), so defocus
is a real defect too — it is simply not the biggest one, and it is not the one
that would have been found by looking only at where the focus plane sits.

The three defects share one lever. Pulling a station back to make its cluster fit
also cuts the parallax smear and lowers the angular rate needed to hold the
subject, so the framing fix is the only one of the three that pays into all
three.

---

## R2-322 — a presentation WINDOW is not "on screen", and 127 frames prove it

`beat1.schedule` runs each cluster's window from **its own station's arrival to
the NEXT station's arrival**, so the last frames of a window are spent flying
away from the thing the window names. At f500, the cluster its window nominates
(`CORNER_RR`) is **95.68 deg off axis** — beside the camera, not in the picture.
`continuity_gate` already prints the same fact from the other side: 127 beat-1
frames have the nominated cluster more than 25 deg off axis, worst 76.94 deg.

Any focus verdict taken at "the frames where the sheet says X is presented" is
therefore grading the camera on frames where X is not in shot — **the same class
of confound as measuring against `CAR_ROOT`, one level up.** Both are now
negative controls, and `tools/beat1_focus_track.py --best` asks the question the
brief actually asks instead: does every cluster get **some** frame where it is on
screen, whole, and sharp?

Its answer needs reading with care and is logged here so it is not misquoted:
15 of 15 clusters do have such a frame, **but for twelve of them that frame is in
the close-out (f625-792), where the car is assembled and the part is 12-31 % of
frame height as one detail of a whole car.** That is not a presentation. The three
exceptions are RW at f233, BB at f13 and CORNER_FR at f33, and none of those is
the cluster's own station either. **Not one of the fifteen clusters has its clean
readable moment at the station that was built to present it**, because at that
station every one of them is too big for the frame.

---

## R2-323 — the candidate fix clears all fifteen, and breaks the speed solve in five places

`tools/beat1_restand_candidate.py` pulls each station back along its own **measured**
presentation direction until the cluster fills 0.85 of the limiting frame
dimension, sets `focus_distance_m` to the new standoff and `fstop` to the
f-number the law above requires. Direction, `look_at` and lens are untouched, so
`presentation_normals` still chooses which face the audience sees.

```
framing         15/15 FAIL  ->  0/15 FAIL          all fit at 0.85 or under
apertures       f/2.2-2.8   ->  f/1.4-8.9 (SW f/23.7, see R2-324)
mean standoff   2.033 m     ->  4.436 m   (2.18x)
key-to-key path 54.958 m    ->  67.228 m  (1.22x)
```

**And it fails the R2-062 speed gate in five places**, worst 5.28-5.90 m/s
between f551 and f591 against a 4.00 m/s limit, because the tour was timed for
the closer stations and the moves are now longer inside the same 33 s.

> **The framing fix is not a standoff edit. It is a re-solve.** Held-Karp has to
> re-run over the new station positions and the time allocation with it. At the
> same speed limit the candidate needs **+7.4 s (33.0 -> 40.4 s)** — which the
> brief explicitly permits ("total runtime may grow toward ~2 minutes and that is
> fine"), but which moves every beat boundary after it and is a bigger unit of
> work than this block.

The alternative that costs no time is a **wider lens at the same station** — the
extent is linear in focal length, so 58 mm -> 19-27 mm and 35 mm -> 14-18 mm makes
every cluster fit without moving one camera, and divides the smear of R2-321 by
the same ratio. It is rejected here as a recommendation because a 14 mm lens
1.4 m from a monocoque is a different film, but it is the lever if the runtime
cannot move.

## R2-324 — the steering wheel cannot be fixed by standoff, and needs its own call

`SW` is 0.128 x 0.280 x 0.230 m. Its standoff is clamped by `max(..., 0.75)` and
it fits the frame at **0.935 m**, so the candidate barely moves it. But at 0.935 m
on a 58 mm lens its 0.245 m of depth needs **f/23.7** to stay inside 2 px — an
aperture where diffraction on a 9.375 um pixel is itself the limit.

SW is the one cluster where the closed-form law has no comfortable answer, because
its depth-to-width ratio is the worst in the field. The choices are a shorter lens
at the same distance, a much longer lens much further back, or accepting that the
rim is sharp and the column stub is not. **Open. Not decided here.**

---

## R2-325 — R2-103's quaternion floor, reproduced on this block's own comparator, before any verdict was read off it

The stored path quaternions are rounded to six decimals, so `|q|` is off unit by
about 8e-7 and `2*acos(|dot|)` amplifies that by a square root. Run as the
self-null, a path file against a **bit-identical copy of itself**:

```
raw stored q      2978 frames   dp 0 m   dq 0.203165 deg   dlens 0 mm
re-normalised q   2978 frames   dp 0 m   dq 0.000003 deg   dlens 0 mm
```

**0.203 deg is the floor, on a file compared against itself.** Every rotation
figure in R2-326 is taken on re-normalised, sign-normalised quaternions, and the
self-null is printed above every comparison `tools/campath_diff.py` makes.

Separately, rebuilding the rig from the **shipped** sheet reproduces
`render/film14_path.json` exactly — 0 m of position, 0 mm of lens, and every
quaternion component byte-identical across all 2978 frames. That is the null the
candidate is measured against.

---

## R2-326 — what the candidate does to the protected f648-792 region: 104 px at its first frame, nothing after f720

The question that blocked this work was whether moving `CORNER_FL` at f591 reaches
into f648-792, which a review called the best material in the film. Measured on
the built path, candidate against shipped:

```
                             worst |dp|        worst rotation
beat 1        f1-792           6.6156 m @f1        26.119 deg @f236
  f1-590 (the presentations)   6.6156 m @f1        26.119 deg @f236
  f591-647 (CORNER_FL + close) 1.8868 m @f591       0.003 deg @f593
  PROTECTED f648-792           0.1151 m @f648       0.000 deg @f650
beats 2-6     f793-2978        0.0000 m             0.000 deg
```

In screen pixels, using the range the film's own focus is holding at each frame:

```
f648  118 mm -> 104 px      f665   68 mm ->  47 px      f700  15 mm ->  8 px
f655    0 mm ->   0 px      f720  0.3 mm ->   0 px      f754   0 mm ->  0 px
```

**Beats 2 to 6 are bit-identical. The seam does not move at all** (R2-327). The
protected region is perturbed only at its first ~70 frames, by at most 104 px,
with zero rotation change, and is exactly unchanged from f720 on.

**That is not zero, and it is not being reported as zero.** 104 px at 4K is
visible. The existing machinery to remove it is already in `build_beatsheet.py` —
CORNER_FL's slot is pinned and there is a handle pin at f754 for exactly this
class of bleed — and a re-solve that keeps CORNER_FL's *time* fixed while moving
its *position* should be able to hold the close-out. **Not attempted here**, because
`render/film*.blend` is off limits to this block and a station change that cannot
be rendered cannot be judged in the only currency this project accepts.

---

## R2-327 — the four seam invariants, before and after, from the same script

`tools/seam_gate.py`, same invocation, `render/film14_path.json` and
`docs/beat_sheet.json`:

| | before | after (shipped, unchanged) | candidate (`work/b1rig/after_path.json`) |
|---|---|---|---|
| `chord_m` | 2.0893 | 2.0893 | 2.0893 |
| `speed_ms` | 1.2727 | 1.2727 | 1.2727 |
| `look_angle_deg` | 13.2504 | 13.2504 | 13.2504 |
| `lens_delta_mm` | -0.051 | -0.051 | -0.051 |
| built path vs declared keys | f754 0.0000 mm, f793 0.0000 mm | identical | identical |
| peak speed | 8.9124 m/s @f804 | identical | identical |
| worst BULGE | 1.407x f815-817 | identical | identical |
| worst LOCAL accel | 3.59x @f796 | identical | identical |
| verdict | SEAM_OK | SEAM_OK | SEAM_OK |

The shipped column cannot have moved: **this block changed no camera data at
all.** The one edit to `tools/build_beatsheet.py` is inside the report block, and
`--check` mode writes nothing. The candidate column is identical because the seam
lives at t = 31.4 and t = 33.041667, both outside beat 1's presentations, and the
candidate's perturbation is exactly zero from f720.

---

## R2-328 — what was NOT confirmed

* ~~**The motion-blur decomposition has not been closed by a rendered A/B.**~~
  **CLOSED by R2-331.** All three `--dof off` controls delivered and the
  prediction, committed before they landed, held on every one. The magnitude split
  is now measured and not inferred.
* **No frame of the candidate has been rendered**, because `render/film*.blend`
  is off limits to this block. Every candidate number above is geometry. In
  particular **the 104 px the candidate moves f648 by has not been looked at**,
  and 104 px at 4K is a shift a review would see.
* ~~**f532 did not render.**~~ **CLOSED — f532 delivered, and it is the most
  damning frame in the beat.** It carries the largest predicted smear anywhere in
  the take (475 px at the on-axis cluster centre, 808 px at its near face) and is
  the frame `continuity_gate` independently flags as the worst nominated-cluster
  aim in beat 1 (76.94 deg). The picture is not a picture of anything: every
  feature is drawn into a long horizontal streak. Its measured surviving-gradient
  axis is **91.6 deg against a predicted 97.6 deg — 6.0 deg**, the seventh
  agreement and the one on the most extreme frame in the set. The stall was a dead
  container behind a frozen status line and had nothing to do with the frame's
  content: it rendered normally on the retry.
* **The re-solve is not attempted**, so "+7.4 s" is the cost at the same speed
  limit on the same tour order, not the cost of the tour Held-Karp would choose
  for the new stations. It could be less.
* **SW is open** (R2-324).
* **Whether f/5.2-9.0 is the right LOOK** is a judgement nobody has made from a
  frame. The arithmetic says it is the aperture that makes the presented part
  read; it also flattens the separation the brief asks for. The background at
  10 m still blurs by 8-12 px at f/6.5 focused at 4 m, which is separation, but
  it is not the f/2.2 look.

---

## R2-329 — the motion-blur finding, confirmed in the PIXELS and not only in the geometry

R2-321's smear figures are geometry off the built path. `tools/blur_anisotropy.py`
settles them from the rendered frames alone, with no second render, because
**defocus and motion blur do not have the same shape**: the circle of confusion is
a circle and suppresses gradients equally in every direction, while a 180-degree
shutter is a line integral along one direction and leaves the gradients ACROSS it
almost intact.

The structure tensor of the frame gives the axis gradients survive in. The camera
path independently predicts the smear direction. **They are computed from
disjoint inputs and must agree.**

| frame | predicted surviving axis, from the path | measured, from the pixels | delta | predicted smear | anisotropy |
|---|---|---|---|---|---|
| f460 | 52.4 deg | 51.5 deg | **0.9** | 117 px | 0.832 |
| f591 | 59.3 deg | 58.5 deg | **0.8** | 50 px | 0.685 |
| f434 | 136.6 deg | 137.7 deg | **1.1** | 27 px | 0.838 |
| f200 | 162.4 deg | 160.2 deg | **2.2** | 40 px | 0.845 |
| f300 | 88.6 deg | 92.9 deg | **4.3** | 85 px | 0.896 |
| f120 | 17.8 deg | 11.4 deg | **6.4** | 107 px | 0.585 |
| f500 | 114.9 deg | 130.3 deg | 15.4 | 116 px | 0.728 |
| f648 | 53.3 deg | 66.1 deg | 12.8 | 26 px | 0.744 |
| f400 | 169.1 deg | 90.2 deg | **79** | **11 px** | **0.401** |

Six of the nine agree to within 6.4 degrees and four of them to within 2.2, on a
quantity nothing in the image pipeline was told about. **The middle third is
smeared by the camera, and the direction proves it.** The two loose ones are the
two frames where something else is organising the picture — f648 is the one
legible frame (see below) and f500 has two clusters at different depths smearing
by different amounts.

**And the last row is the point, not the exception.** f400 is the one frame
where the predicted smear is small — 11 px against 26-117 — and it is also
the only one whose anisotropy collapses, to 0.40 against 0.59-0.90. With no
smear to align to, the surviving axis reverts to the scene's own structure (the
turntable rim that fills its lower half). **So the instrument separates the two
causes rather than merely confirming one:** f120, f200, f300, f434, f460, f500
and f591 are motion-blurred frames; f400 — the frame the earlier agent flagged as "a bright
smear, no subject in focus" — is a genuine depth-of-field frame, and its subject
is 0.328 m behind the focus plane with 29.5 px of defocus and its centre outside
the vertical frame.

Limit, stated with the finding: a sharp picture of parallel edges is anisotropic
before anything blurs it, and the selftest carries that case explicitly (sharp
horizontal stripes read 1.0000). The verdict above rests on the AGREEMENT of two
independent estimates of a direction, never on the magnitude alone.

**f648 shows that limit doing its job.** Predicted surviving axis 53.3 deg,
measured 66.1 deg — 12.8 deg apart, one of only three disagreements over 6.4 deg in nine frames.
It is also the one frame of the seven that is legible, and a legible frame of a
Formula 1 car is dominated by the car's own long axis, so the gradients have
somewhere else to point. **The agreement is tight exactly where the smear is large
enough to be the only thing organising the picture, and it loosens where it is
not** — which is the behaviour the instrument should have, and the reason its
magnitude is never quoted as a verdict on its own.


---

## R2-330 — the cheapest fix that satisfies all three, and it is a HYBRID

Three levers, one target. The extent is linear in focal length and inversely
linear in distance, so the required shrink `over = max(ext_h, ext_w) / fill` can
be paid in either currency, and the smear divides by **the product** of the two
ratios while the required f-number is fixed by the fill target alone. Spending as
much of `over` as possible on the lens, with a 28 mm floor so the look stays a
lens and not a fisheye, and the remainder on distance:

| | shipped | pure dolly, lens fixed | **hybrid, 28 mm floor** |
|---|---|---|---|
| mean standoff | 2.033 m | 4.436 m (2.18x) | **3.072 m (1.51x)** |
| corner clusters move | — | 2.62-2.96x | **1.30-1.44x** |
| beat-1 key-to-key path | 54.958 m | 67.228 m | **60.175 m** |
| beat 1 at the same 4.00 m/s peak | 33.00 s | 40.37 s (+7.4 s) | **36.13 s (+3.1 s)** |
| corner apertures | f/2.2 (needs f/37) | f/5.2-9.0 | **f/5.3-8.4** |
| smear divided by | — | ~2.2x (range only) | **1.25-3.04x (lens x range)** |

**The hybrid costs less than half the runtime of the pure dolly, moves the corner
stations by 0.45-0.68 m instead of 2.4-3.0 m, and cuts the motion blur harder**,
because a wider lens shrinks the smear and the extra distance shrinks it again.
It is the recommendation.

**The order, and it is forced, not chosen:**

1. **Framing.** Nothing else can be fixed first. At today's standoff the aperture
   that holds a corner cluster sharp is f/37, so there is no focus fix available
   until the cluster fits (R2-320). Re-solve Held-Karp over the new stations and
   re-allocate the time; beat 1 grows by about 3 s and the brief permits it.
2. **Aperture.** A one-line consequence. `N = D (fill h)^2 / (2 c E^2)` is
   computable the instant the fill target is chosen and is invariant to *how* the
   fill was achieved, so it never needs its own iteration and can never be
   invalidated by a later change to the standoff or the lens.
3. **Re-measure the smear, then decide whether the pan limit still needs work.**
   The framing fix pays into it — 1.25x to 3.04x — but the median is 54.7 px over
   the tour and dividing by 2.2 leaves 25 px, which is still not sharp at 4K.
   `weave_spec.pan_limit_widths_per_frame` should be restated in **pixels of
   smear at the delivery resolution**, because that is the unit the defect is in
   and 0.12 frame-widths is 230 px at 4K and 58 px at 1080p — *the same camera
   passes or fails depending on what it is delivered at.*

None of the three is attempted here. `render/film*.blend` is off limits to this
block, and a station change that cannot be rendered cannot be judged.


---

## R2-331 — the `--dof off` A/B, PREDICTED BEFORE THE FRAMES ARRIVED

Committed while the three control frames were still queued, so it is a prediction
and not a postdiction. Each is the same frame, same camera, same 512 samples, same
4K, with Blender's depth of field disabled and nothing else changed — so the
difference between the pair is defocus and only defocus, and whatever survives in
the `--dof off` version is motion blur.

The measure is RMS image gradient per pixel, the same absolute one used above.

| frame | predicted smear | defocus at the on-axis centre | prediction for `--dof off` |
|---|---|---|---|
| f200 | 39.7 px | 2.1 px | **little change.** Motion dominates by ~19x; killing the defocus should barely move the gradient energy. |
| f400 | 11.4 px | 29.5 px | **large change.** This is the one defocus-dominated frame of the three; it should sharpen substantially and its anisotropy should stay low. |
| f591 | 49.8 px | 1.8 px at centre, **177 px at the tyre** | **split.** The tyre wall filling the left half should sharpen a lot; the centre of frame should stay smeared, because 1.8 px of defocus is not what is softening it. |

If f200 sharpens as much as f400 does, the motion-blur finding is wrong and R2-321
and R2-329 both have to be withdrawn. That is the outcome this pair is being
rendered to permit.

### RESULT — all three delivered, and the prediction held on every one

`tools/dof_ab.py`, per block, with the null taken from inside the same pair: DOF
cannot sharpen what was already at the focus plane, so those blocks differ only by
Monte Carlo noise between two independent renders and their change fraction IS the
noise floor. It measures **-0.004 to +0.003** on all three pairs, so everything
below is far outside it.

```
                     p10 (the null)   p50 (typical)   p90 (what the lens blurred)   whole frame
f200   predicted:                     little change
f200   measured:        +0.003          +0.138             +0.580                     +0.312
f400   predicted:                     LARGE change
f400   measured:        -0.004          +0.689             +7.430                     +2.158
f591   predicted:                     split: tyre sharpens, centre stays smeared
f591   measured:        -0.003          +0.028             +0.469                     +0.264
```

**THE FALSIFIER IS SURVIVED, AND NOT NARROWLY.** f400's typical block gains 69 %
and its worst decile gains **743 %** — 8.4x the gradient energy — when the lens is
opened up. f200's typical block gains 13.8 %. That is **5x less at the median,
12.8x less at p90, and 6.9x less on the whole frame.** R2-321 and R2-329 stand.

f591 split exactly as predicted: **+2.8 % at the median and +46.9 % at p90** — the
lens was blurring the tyre wall in the near foreground and leaving the rest of the
frame alone, because the rest of the frame is smeared, not defocused.

**The anisotropy moves the way the theory requires and nothing else would.**
Removing an ISOTROPIC blur from a picture that also carries a DIRECTIONAL one must
leave the anisotropy the same or higher; if defocus had been the dominant term it
would have fallen.

```
f200  0.845 -> 0.882      surviving axis 160.2 -> 158.5 deg   (smear axis, unmoved)
f591  0.685 -> 0.753      surviving axis  58.5 ->  54.8 deg   (smear axis, unmoved)
f400  0.401 -> 0.642      surviving axis  90.2 ->  94.1 deg   (SCENE axis, unmoved;
                                                    its predicted smear axis is 169)
```

**And the pictures say it more plainly than the numbers do.** f400 with the lens
opened up stops being a bright smear and becomes a crisp architectural frame — the
glass-wall mullions, the floor tiling, the suspension arm, the turntable rim, all
sharp. f200 with the lens opened up is **visually indistinguishable** from f200
with it closed: the same vertical streaks through the floor panels and sidepods,
the same illegibility, with only the far ceiling a touch crisper.

### What this settles, and it is worth more than the finding it was testing

**The standing complaint about f400 — "a bright smear, no subject in focus" — is
correct, and it is ISOLATED.** Beat 1 is not uniformly soft. It has two different
defects that look alike in a single frame and have different fixes:

* **f400 is a focus-placement failure.** The focus plane sits at 1.173 m, the
  nominated cluster (SW) is at 1.501 m, and SW's centre is outside the vertical
  frame anyway. The content is fine — the DOF-off frame proves the geometry and
  materials there are sharp and legible. **Fixing the standoff and the aim fixes
  f400.**
* **f200, f591 and the rest of the tour are a camera-speed failure.** No aperture,
  no focus pull and no standoff change will touch them. **Only slowing the camera
  or shortening the lens will.**

Nobody could tell these apart before this pair existed, and the whole-frame number
would not have separated them either: f200's whole frame moves +0.312 and f591's
+0.264, which look like the same frame until you see that f200's p50 is five times
f591's.

## R2-332 — the item was measured against its own copy of the host, and it read 3.3× too high

`marshal_post_deck`'s declared collection `ITEM_MARSHAL_POST_DECK` delivers **75
mesh objects** for an `expect_objects` of 25. The extra 50 are **`CTX_Column_01
… CTX_Column_50`** — the item's own *context* copies of the very thing it claims
to supersede. `hospitality_deck` is the same shape: 11 objects for a declared 5,
the extra six `CTX_Apron` and `CTX_Unit_1..5`.

The first pass counted them as item units:

```
                              units   host verts in boxes   core
CONTAMINATED (all 75)            75        67,628  40.06%   17,625  10.44%
declared prefix only (MPD_)      25        20,681  12.25%    3,257   1.93%
```

**3.3× on the headline.** The measure was scoring the item against its own copy
of `DR_Post_*`, and `CTX_Column_19` — a context object — was the single
"unit" with the highest overlap in the whole run at 4,414 host vertices. That
is R2-180's fall-through one level down: not "any item collection, take the
biggest", but "any object in the item's collection, count it as the item".

The probe now splits on the declared prefix exactly as `place_one` does and
reports both figures. **`build_items` already refuses these rows** — the
foreign-prefix arm fires on `CTX_*` against a declared `MPD_` — but the registry
records no blocker for it, so a reader would have expected them to place. Their
`rig_subcollections` names only `/Cameras` and `/Standins`; the context
sub-collection is not declared.

---

## R2-333 — a whole-object supersede that would have deleted about 1,530 tyres to place 338

`tyre_wall_tyre` is the one row whose supersede was already a whole object —
`{"object": "BR_TyreWall_T4"}` — and therefore the one the placement stage could
have executed today. It is `ITEM_ACCEPTED`. Its blend holds 338 units and its
`expect_objects` is 338, so **every check in `place_one` passes**: prefix,
population, no instancers, one mesh per object, `top_share` 0.296 %.

`BR_TyreWall_T4` is `rows=3 × courses=3` at 0.62 m pitch over the T4 hairpin's
inside arc — **about 1,530 of the world's 2,255 tyres**, read out of
`build_barriers`' own path arithmetic rather than off the global counter, which
does not split. The item's manifest declares 2,255; `gate.json`'s
`triangles / triangles_per_declared_instance` gives 11,555,486 / 5,124.4 =
**2,255 declared against 338 found**.

**So the stage as written would have placed 338 tyres and deleted 1,530.**
Nothing in the file would have said so, because `expect_objects` measures the
item against *its own blend* and can never see the size of the thing being
removed.

A supersede record now declares `replaces_units`, and `_refuse_partial_supersede`
is shown failing the world it must fail and passing the two it must pass:

```
MUST FAIL   the shipping row (338 in, ~1530 out)   PlacementRefusal, 22.1 % < 90 %
MUST PASS   the same row at its full 2255          no refusal
MUST PASS   a supersede with no replaces_units     no refusal (unaffected)
```

---

## R2-334 — the whole-feature skip removed a stand that nothing replaces, and the vertex count called it clean

The first cut of the pit-wall switch emptied `picks` and removed all five welded
stands. `ARCH_PitWall` fell from 24,664 vertices to 15,216, 30 of 31 `ARCH_*`
objects were bit-identical, and every summary said the removal was clean.

It was not. `work/r2331/verify_removal.py` clusters the removed vertices back
into the stands they came from and asks how far each is from the nearest hero
stand:

```
removed stand 0   744 v  (173.1,  55.3)  ->  TS_Stand01_CORVUS     6.9 m
removed stand 1  1088 v  (225.2,  99.8)  ->  TS_Stand04_FULGOR     8.2 m
removed stand 2   948 v  (271.1, 138.4)  ->  TS_Stand06_HALCYON    8.6 m
removed stand 3  1682 v  (319.1, 178.2)  ->  TS_Stand09_KESTREL    1.9 m
removed stand 4  1298 v  (367.3, 218.6)  ->  TS_Stand09_KESTREL   64.6 m   <--
```

The item's ten stands span world x 158–321; the class's fifth stand is at
x 367. **A whole-feature switch takes out a stand the item never reaches** — one
full 62 m stand pitch of pit wall left bare — and a vertex count reports that as
a clean 9,448-vertex removal.

Fixed by declaring the **sites** the item occupies, measured off the item's own
artefact (`class_switch_sites_world_xy`, ten centroids, `class_switch_radius_m`
31.0 — half the class feature's own 62 m pitch). `build_architecture` now asks
per stand:

```
architecture.pit_wall_stands at (173.0,  55.4): SUPERSEDED
                             at (225.6,  99.5): SUPERSEDED
                             at (271.6, 138.1): SUPERSEDED
                             at (319.4, 178.3): SUPERSEDED
                             at (367.3, 218.5): KEPT (no item within 31 m)
```

`pit_wall_stands` 5 → **1**, and `pit_wall_stands_superseded` = 4. The class
module is not guessing where the item is; it is being told by the same registry
that decides the placement, and it keeps everything it is not told about.

---

## R2-335 — `transporters = 20` are not in `ARCH_Ground_Compound`, and two independent readings say so

The registry's `team_truck_trailer` row declares
`welded_in: "ARCH_Ground_Compound", counter: "transporters", n: 20`.

**From the artefact:** zero of `ARCH_Ground_Compound`'s 9,692 vertices fall
inside any of the ten unit boxes, the bounding boxes are disjoint (IoU 0.0000 —
the item runs world x 23.6–73.7, the compound x −103.0 to −31.9), and the median
trailer stands **102.78 m** from it. The control read louder than the subject:
`ARCH_PaddockBuildings`, which the row does not claim, holds **9,153 vertices
(10.43 %)** inside the unit boxes, 2,638 in cores, 5 of 10 units, median 4.71 m.

**From the source, read independently:** `_transporter()` writes into
`MB("ARCH_PaddockBuildings")` — 14 at circuit y 93.5 and 6 at y 62.6 —
and `summary['transporters'] = 20` is a hard literal beside it.
`ARCH_Ground_Compound` is a crushed-hardcore yard with site cabins, silos, 260
loose stones and three Heras runs, and it is the one `ARCH_Ground_*` object that
emits no counter of its own.

Two readings, one artefact and one source, agree. The row's supersede is
retired. **Note the second finding inside the first:** the item's ten trailers
*do* interpenetrate `ARCH_PaddockBuildings` at 10.43 % / 5 of 10 units / 4.71 m
— an undeclared collision that nobody had looked for, because everybody was
looking at the compound.

---

## R2-336 — the class switch, shown failing the un-superseded world before it was trusted passing the superseded one

`build_items` runs LAST so that an item can supersede class geometry, and it can
unlink a whole object. A feature welded inside a shared class mesh is not a
whole object: `ARCH_PitWall` is one mesh carrying a terminal nose, a 357 m wall
run, two return walls, ~40 branded advertising panels **and** five timing
stands. **So the removal has to happen at the only moment it is possible —
before the class builder welds it in.**

`build_items.class_feature_owned(feature)` / `class_feature_owned_at(feature, x,
y)` answer that from the same registry that decides the placement, so the two
can never disagree. Both controls, run on the same code path:

```
registry with the rows on HOLD (work/r2331/PLACEMENT.before.json)
   architecture.pit_wall_stands   False
   barriers.fence_posts           False
   owned map                      {}

registry with the rows on PLACE (world/items/PLACEMENT.json)
   architecture.pit_wall_stands   True  (sited: 4 of 5 stations)
   barriers.fence_posts           True  (whole feature)
   barriers.armco_posts           False  <- declared, but its row is HOLD
   architecture.ground_decks      False  <- declared, but its row is HOLD
   architecture.nonsense_QQZZ     False
```

The two `False` rows in the second block are the arm that matters: a
`class_switch` is declared on `armco_post` and `hospitality_deck` too, and it
does **not** fire, because those rows are not going into the world. **An item
that is not being placed must not take the class version out with it.**

**Which way it fails.** If the registry cannot be read the resolver returns the
empty set and every class feature is built. The two failure directions are not
symmetric: *built twice* is visible in any frame that sees it and contradicts
the placement report; *built zero* is a hole nobody finds until somebody renders
that corner months later.

### The removals, at the source

**`build_architecture` — `ARCH_PitWall`, sited, 4 of 5 stands**

```
                    un-superseded   superseded
pit_wall_stands                 5            1
ARCH_PitWall verts         24,664       17,396   (-7,268)
ARCH_PitWall tris          25,422       18,162   (-7,260)
other ARCH_* objects       30 of 31 IDENTICAL — verts, bbox AND coordinate checksum
surviving verts present in the un-superseded wall     15,216 / 15,216
removed vertices, clustered                4 clusters, gaps 1.9 / 8.2 / 8.6 / 1.9 m
control: removed verts inside gantry_truss's boxes    0 (0.00 %)
>> STAGE RESULT: REMOVAL_VERIFIED_OK
```

**`build_barriers` — `BR_FenceStruct_*`, whole feature, 676 posts**

```
                    un-superseded   superseded
fence_posts                   676            0
objects                       131          131
verts                   6,774,019    6,752,083   (-21,936)
BR_* objects changed                  27, all BR_FenceStruct_*
BR_* objects identical                104 of 131
SIBLING CONTROL BR_FenceMesh_*/BR_FenceWire_*   28 of 28 IDENTICAL
fence_spans 655.0 -> 655.0   gates 28 -> 28   hero_wires 2080 -> 2080
```

The sibling control is the one that had to be run: the spans, the weave and the
hero verticals are built from the **same `posts` list** in a second pass, so if
skipping the post pass had perturbed them the swap would not be clean. It did
not.

**And the un-superseded standalone build reproduces the ship.** Run alone,
`build_architecture` gives `ARCH_PitWall` at 24,664 vertices and
`pit_wall_stands = 5`; `build_barriers` gives `fence_posts = 676`,
`objects = 131`, `verts = 6,774,019`. All five figures are `assembly9_build.json`'s
own. That is what makes the superseded mesh a legitimate drop-in for the film's
— and the transplant checks it again per object before it swaps anything.

---

## R2-337 — the pixels: 79.72 % of the removed geometry moves, against a 0.01 % repeat floor and a 0.82 % control on the same object

**f1126, the frame R2-182 named**, 3840 × 2160, Cycles, **256 samples, denoiser
OFF**, camera `ONER`, all three renders from the same 5090 session.

* **BEFORE** `render/r2226_items.blend` — `film14` + `crew_figure` +
  `timing_stand`. The **double-built** world: ten hero stands standing among
  five welded ones, which is what R2-232 saw and called "the R2-229 debt made
  visible".
* **AFTER** `render/r2331_ts_after.blend` — the same file with `ARCH_PitWall`'s
  mesh replaced by the one the superseded `build_architecture` produced.
* **NULL** `render/r2226_items.blend` rendered a **second** time.

**The transplant is checked, not asserted.** The film's own `ARCH_PitWall` is
compared to the un-superseded standalone build before anything is swapped, and
it matches on all four: 24,664 verts, 25,422 tris, the bounding box, and the
coordinate checksum `[6921343.5895, 3569451.289, 24514.7728]` to four decimals.
A transplant onto a *different* wall would have made every figure below
meaningless. After the swap: 17,396 verts, 18,162 tris. Nine material slots
came in suffixed (`A_ConcPrecast.001` …) and all nine were remapped back onto
the film's own materials; **zero suffixed materials remain**, which matters
because a wall wearing `.001` shades differently from the wall beside it for
reasons no pixel diff would explain.

```
region                             px   AB >8/255  AB mean|d| | NULL >8/255 NULL mean|d|
whole_frame                   8294400       4.02%        1.59 |       0.00%        0.01
REMOVED_point                   43608      79.72%       42.44 |       0.01%        0.03
REMOVED_box                   1835352      15.91%        5.47 |       0.00%        0.01
SURVIVING_HOST_CONTROL          37065       8.69%        3.87 |       0.01%        0.01
SURVIVING_FAR_CONTROL           12172       0.82%        0.89 |       0.01%        0.00
rest_of_frame_CONTROL         8213727       3.59%        1.36 |       0.00%        0.01
```

**The controls, and what each one is worth.**

* **NULL.** The repeat-render floor is 0.00–0.01 % at the 8/255 threshold on
  every region including the changed one. With the denoiser off this is the
  number that says 79.72 % is not sampling noise.
* **`SURVIVING_FAR_CONTROL` — 0.82 % against 79.72 %, a factor of 97.** This is
  R2-150's control — *"the occluded half of a changed region, in the same two
  builds under the same fix, must not move", 1.47 % against 74.40 %, 50×* —
  taken off geometry instead of off occlusion, and with the leak removed. It is
  the **same mesh datablock**, in the same two renders, restricted to vertices
  more than 15 m from anything that was removed, so nothing about the removal
  can light it, occlude it or reveal it. 97× is stronger than R2-150's 50×.
* **`SURVIVING_HOST_CONTROL` — 8.69 %, and it is NOT clean, deliberately.**
  This is the whole surviving wall, which includes the stretch directly behind
  and beneath each removed stand. That stretch *must* change: it is now seen
  and lit. 8.69 % is the size of that leak, exactly as R2-232 said of its own
  7.07 % — *"the size of that leak, not of a light leak"*. Both numbers are
  printed because reporting only the clean one would hide how the region was
  chosen.
* **`rest_of_frame` — 3.59 %, and this is a limitation, not a result.** The
  point mask is built from the removed **vertices**, dilated 4 px. A stand 30 m
  from the camera covers far more pixels than its vertices project to, so most
  of each removed silhouette falls *outside* `REMOVED_point` and lands in
  "rest of frame", along with the bounce light four fewer stands no longer
  throw. **So this A/B does not claim confinement**, and the number that would
  have claimed it is reported as what it is. `REMOVED_box`, the generous
  version at 1,835,352 px and 15.91 %, is given for comparison with every
  earlier A/B on this project, which used boxes.

**The instrument refuses two ways and both were live.** It refuses if nothing
of the removed geometry is in frame — R2-182's *"an item absent from the world
produces two identical images"*, which for a *removal* is the same trap wearing
the other mask. And it refuses if the removed region changed **less** than the
frame as a whole, which is the signature of the vertically-mirrored mask that
R2-232's own instrument produced and reported as a clean 0.00 %.

---

## R2-338 — the pixels: `catch_fence_post`, and the control that had to fail first

**f1580**, chosen by projecting the item's 676 unit centroids through all 2,978
camera poses: **446 posts in frustum, nearest 22.8 m**, where a 2 m object is
263 px. (The frame with the most posts in frustum, f2833 at 476, has them at
213 m and 19 px — more posts, no pixels.)

* **BEFORE** `render/r2331_cfp_before.blend` — `film14` + `catch_fence_post`
  placed. **676 objects, 676 distinct mesh datablocks, 0 shared, 0 instancers,
  `top_share` 0.1479 %.** The double-built world: 676 hero posts standing among
  676 welded ones.
* **AFTER** `render/r2331_cfp_after.blend` — the same file with all 27
  `BR_FenceStruct_*` meshes replaced by the superseded `build_barriers`
  output. `153,060 → 131,124` verts, **−21,936**, matching the standalone diff
  exactly. 27 material slots remapped, zero left suffixed.
* **NULL** `render/r2331_cfp_before.blend` rendered a **second** time.

**BEFORE and NULL are rendered and measured; the AFTER render is still
outstanding at the time of writing, so the A/B row is not filled in here.**
What is on record is the frame's own repeat floor and both controls of the
instrument.

**The f1580 null floor is not f1126's, and using the wrong one would be the
error this project keeps logging:**

```
f1126   mean |d| 0.006 levels   0.0031 % of pixels differ by more than 8
f1580   mean |d| 0.0373 levels  0.0349 % of pixels differ by more than 8   ~6x looser
```

Expected, with 446 fence posts of high-frequency geometry in frustum at 256
samples with the denoiser off. **The AFTER must be judged against 0.0349 %.**

### The control that had to fail, and did

`supersede_ab.py` was handed **two renders of the same scene** — BEFORE against
NULL, with no removal applied — and its first refusal arm did **not** fire:

```
region                    px      AB >8/255   |  the arm that should have caught it
whole_frame          8294400          0.03%   |  removed(0.29%) > whole(0.03%): PASSES
REMOVED_point          93729          0.29%   |  ... on NOISE ALONE
SURVIVING_HOST        171378          0.26%
```

The removed region is high-frequency geometry, so **its** repeat-render noise is
genuinely ten times the frame's, and "the removed region changed more than the
frame" is satisfied by nothing at all. What separates the two cases is the ratio
against the **same object's surviving geometry, in the same pair of images**:

```
real removal (f1126)   79.72 % / 0.82 %  =  97x     SUPERSEDE_AB_OK
no removal   (f1580)    0.29 % / 0.26 %  =  1.1x    SUPERSEDE_AB_FAIL
```

That arm is now in the instrument at a floor of 5×, and both records are kept:
`work/r2331/ab_1126_supersede.json` and `ab_1580_nullcontrol.json`.

### R2-344 — the AFTER OOM'd at 4K on a scene that got *smaller*, and the correctness question that raised

Six 4K submissions of `render/r2331_cfp_after.blend` died with
`Out of memory in CUDA queue enqueue (integrator_shade_volume)` on a 32 GB 5090
— **on a scene 21,936 vertices smaller than the BEFORE, which renders at full
4K on the same instance in 179.3 s.** A scene that shrank should not need more
memory, so the memory was treated as a symptom.

The leading hypothesis was a **correctness** problem, not a capacity one:
`bpy.data.libraries.load(link=False)` appends the *closure* — each object drags
its mesh, its materials and those materials' images — and remapping the 27
material **slots** back onto the film's materials fixes shading while leaving
the appended datablocks in the file. If the append had pulled in images, the
AFTER would differ from the BEFORE **by the fence swap plus the contamination**,
and the A/B would be measuring both.

Measured in the build run, both states in one pass:

```
datablocks   before: {'images': 0, 'materials': 194, 'meshes': 2717, 'objects': 30402}
datablocks after swap: {'images': 0, 'materials': 195, 'meshes': 2717, 'objects': 30402}
datablocks after purge: {'images': 0, 'materials': 194, 'meshes': 2717, 'objects': 30402}
  images +0   materials +0   meshes +0   objects +0        (AFTER minus BEFORE)
saved 4460.3 MB, previous build 4460.3 MB, +0.0 MB
```

**`images: 0`, in both — and that is decisive rather than lucky.** The append
could not have dragged in a texture because there is no texture anywhere in this
project to drag: everything is procedural, which is the brief's defining rule.
The one transient material the swap created was taken back by an explicit
zero-user sweep plus `orphans_purge(do_recursive=True)`, and **the purge changed
the file size by +0.0 MB**, so nothing had been orphaned in the first place.

Tiling was checked in the same pass because two causes can be true:
`use_auto_tile=True, tile_size=2048` — and the BEFORE carries the same values,
being the same file lineage, so it is not a difference either.

**So the A/B is measuring the fence swap and nothing else, and the OOM has no
cause on the content side.** Six agents were pushing ~5 GB scenes through one
warm worker with 76 % of instance time going to scene loading; it reads as
contention. Recorded here because the *diagnosis order* is the lesson: the
memory failure was worth treating as a content signal even though it turned out
not to be one, and the check that closed it is now in the build script rather
than in somebody's memory.

**Two further honest limits of this frame, recorded rather than worked around:**

* **`REMOVED_box` is the whole frame** — 8,294,400 px. A bounding box around 676
  posts distributed along 27 fence runs *is* the frame. Every earlier A/B on
  this project used box masks; for a distributed feature they carry no
  information at all, and the point mask is the only usable one.
* **`SURVIVING_FAR_CONTROL` is empty**, even at 8 m. Every surviving
  fence-struct vertex — cables, top rail, gate frames — is within 8 m of a post
  that was removed, because the posts *are* distributed along it. R2-150's
  control is **unavailable at this frame**, and the instrument prints
  `(empty)` rather than inventing one, as R2-232 did when f1126 had no occluded
  stand.

---

## R2-341 — I overwrote two live interface contracts, and `git status` caught it, not me

**My mistake, recorded because the naming collision is the reusable part.**

`WAVE2-SCOPE.md` §3.3 says the floor items *"should ship an `<id>_interface.json`
and nothing else"*, so I generated six of them. **Two of those names were already
taken by something else entirely.**

`world/items/access_road_slab_interface.json` and
`world/items/forecourt_paving_bay_interface.json` already existed and are the
**modules' own published contracts** — real, substantive, and depended upon:

```
access_road_slab_interface.json      route_total_m, glass_plane_x, flat_run_m,
                                     lane_edges_v, slab_thickness_m, bed_z,
                                     slab_top_min_m/max_m, friction_mu, kerb_seat_m
forecourt_paving_bay_interface.json  "surface_z: the flag top a thing RESTS on;
                                     use it, never APRON_Z", plus the socket
                                     list `forecourt_bollard` is told to use
```

I wrote over both. **Nothing failed** — the files parsed, the generator printed
six successes, and the campaign's decision was recorded exactly as intended. It
surfaced only because `git status` showed **`M`** against those two rows and
`??` against the other four, and `M` on a file I believed I had created is the
only signal there was.

Restored with `git checkout --` on the two paths; `git diff --stat` is now empty
for both, so the restore is byte-exact and the originals never reached a commit.

**The fix is the name.** The campaign's ownership decision is not the module's
contract and must not share its filename. The six are now
`world/items/<id>_ownership.json`, each carrying a
`not_to_be_confused_with` field pointing at the other file, and the generator
**refuses rather than overwrites** any path that already exists.

*"Path-scope every `git add`"* (R2-234) protects other agents' files at commit
time. It does nothing about a `open(path, "w")` that guesses a filename, and
`<id>_interface.json` is exactly the kind of name two independent pieces of work
guess the same way.

---

## R2-342 — `libraries.load` rewrites the list you hand it, and the crash is the only reason the result was not silently wrong

`bpy.data.libraries.load` mutates the list assigned to `data_to.objects` **in
place**, replacing the names with the loaded datablocks. So:

```python
have = [n for n in names if n in df.objects]     # strings
dt.objects = have
loaded = dt.objects                              # ... is the SAME list object
```

After the block, `have` and `loaded` are one list, both holding Objects.
`zip(have, loaded)` pairs every object **with itself**.

In `work/r2331/make_ab_blend.py` this was going to swap all 27
`BR_FenceStruct_*` meshes onto themselves — producing an AFTER blend **identical
to the BEFORE**, which would have rendered a perfect null and read as *"removing
676 posts is invisible, close it"*. That is R2-182's trap wearing the other
mask: there, the item was absent; here, the removal never happened.

It did not happen only because `bpy.data.objects[<Object>]` raises a
`TypeError`. **And Blender 5.2 exited 0 over it**, so `cfp_after.log` carried
neither `AB_BLEND_OK` nor `AB_BLEND_REFUSED` — the file simply was not there.
A peer agent, asked to render the AFTER, found the missing file and read the
traceback rather than assuming a slow build.

The pairing must be a **snapshot taken before the block exits**:

```python
have = [n for n in names if n in df.objects]
requested = list(have)                # copy BEFORE Blender mutates it
dt.objects = have
loaded = dt.objects
for wname, new_ob in zip(requested, loaded):
    ob = bpy.data.objects[wname]
```

**The uncomfortable part:** the same aliasing is written up, at length, in
`work/r2331/ownership_probe.py`'s `link_hosts()`, where it cost this same block
a run three hours earlier — *"`libraries.load` REPLACES the list you hand it …
`bpy.data.objects.get(<Object>)` raises inside a SystemError that Blender 5.2
would otherwise carry to exit code 0"*. Having written that comment did not stop
me writing the same bug in the next file. Documenting a trap is not the same as
being protected from it.

---

## R2-343 — a coordinate set-difference cannot tell removed geometry from a moved origin

Extracting *which* vertices the class builder stopped welding in, by
differencing the ship's `BR_FenceStruct_*` against the superseded build's:

```
rounded to 10 um    removed 132,594   "added by the superseded build" 110,681
rounded to  1 mm    removed  24,196   "added"                          2,252
expected from the object counts:      removed  21,936   added 0
```

Neither is right, and the reason is not precision alone. `MB.emit` **recentres
every mesh on its own centroid** and puts the offset on the object — so removing
676 posts moves all 27 origins, and every **surviving** vertex makes a different
round trip through `local = world − origin`. Blender stores vertices as
`float32`; at ~500 m from the world origin one ulp is ≈ 30 µm. The set
difference was measuring the recentring.

Replaced with a nearest-neighbour test at 5 mm — two orders above the float32
noise, two orders below the 152 mm width of the post being removed:

```
ship verts 153,060   superseded verts 131,124
removed (no superseded vertex within 5 mm)  21,936
expected from the object counts             21,936
>> STAGE RESULT: FAMILY_VERTS_OK
```

**Exact.** And note this never bit `ARCH_PitWall`, where the identical set
difference was clean at 1 µm — because that object's mesh is in circuit
coordinates near the origin with the placement on the object matrix, so the
magnitudes stay small. The same code, on the same kind of data, was correct in
one module and wrong in the other.

---

## R2-339 — the variety arithmetic does not move when class geometry comes out, and it *cannot*

The instruction was to measure it after rather than assume it improves. Measured,
`tools/instance_variety.py` on `render/r2331_cfp_after.blend` — the world with
676 welded posts **removed** and 676 hero posts **added**:

```
TOTAL 4,689,798 realized instances
family       instances  sources  inst/src  top share    gini   verdict
VEG          4,689,798      311    15,080       2.0%   0.722   concentrated
>> STAGE RESULT: INSTANCE_VARIETY_CLEAN
```

**Every figure is the on-record baseline to the digit** —
`variety_distribution_v122.json`: 4,689,798 realized instances, 311 distinct
source meshes, top share 1.99 %, gini 0.7222. The removal moved **nothing**.

That is not a null result, it is a confirmation of `WAVE2-SCOPE.md` §4.1 by
experiment. The instrument counts **realized instances from instancers**, and
`by_first_token` has exactly one family, `VEG`. The class geometry that came
out was **welded mesh**, not instanced, and the item geometry that went in is
**one object per one mesh datablock**, which is not an instance either. So a
change that removes 21,936 vertices from 27 class meshes and adds 676 hero
objects is, to this instrument, invisible by construction. *"The celebrated
311 / 89.1 / 1.99 % says nothing whatever about the item campaign. It is a
statement about grass."*

**The arm that does move is the per-family bound inside `build_items`, and it
is the one that means anything:**

```
item                objects  distinct meshes  shared  instancers  top_share  bound
catch_fence_post        676              676       0           0    0.1479 %   10 %
timing_stand             10               10       0           0   10.0000 %   10 %
```

`timing_stand` sits **exactly on** the bound, which is the honest floor of a
ten-unit population — a share bound cannot mean anything below 1/bound units —
and it is admitted by `MIN_UNITS_FOR_SHARE`, not by loosening the bound. The
world's distinct mesh count rises by **686**, every one with exactly one user.

**And the removal cannot make variety worse in the direction the red line
cares about.** What came out was one mesh's worth of welded, repeated,
seed-identical class furniture; what went in is 686 individually built units.
The instrument that carries the "no repeated assets" name still cannot see
either, which is the standing defect `WAVE2-SCOPE` §4.2 records and this block
does not fix.

---

## R2-340 — what a rebuild is owed, and what is still blocked

**A world rebuild IS owed.** `world/build_architecture.py` and
`world/build_barriers.py` now both read `world/items/PLACEMENT.json` through
`build_items.class_feature_owned*`, and two rows are `PLACE`, so the next
assembly will differ from `assembly9` in exactly these ways:

```
architecture   pit_wall_stands            5 -> 1     (4 superseded, 1 kept: no item within 31 m)
               pit_wall_stands_superseded new key, = 4
               ARCH_PitWall              24,664 -> 17,396 verts
               every other ARCH_* object  IDENTICAL (30 of 31, verified)
barriers       fence_posts              676 -> 0
               BR_FenceStruct_*     153,060 -> 131,124 verts, 27 objects
               fence_spans / gates / hero_wires   UNCHANGED
               every other BR_* object    IDENTICAL (104 of 131, verified)
items          places crew_figure, spectator_crowd_world, timing_stand,
               catch_fence_post           4 rows, was 2
```

**Nothing here needs the rebuild to be believed** — both class changes are
proved on 60–70 s scoped builds against the ship's own numbers, and both pixel
A/Bs are on film-derived blends whose host meshes were checked against the
un-superseded build before anything was swapped.

### Still blocked, and by what

| rows | blocker | note |
|---|---|---|
| 22 | `GATE_NOT_ACCEPTED` | not mine; the gate is `tools/item_gate.py`'s |
| 15 → 14 | `PARTIAL_BUILD` | one retired on measurement — `catch_fence_post`; `timing_stand` never had one |
| 24 → 19 | `SUPERSEDE_WELDED` | 2 cleared by the class switch and gone to `PLACE`, 3 measured FALSE and retired; 2 `pont_*` unproven on `LOCAL_FRAME` and kept |
| 6 | `NOT_AN_ITEM` | correct; probes |
| 5 | `LOCAL_FRAME` | needs a transform arm in the registry |
| 3 | `NO_BUILT_BLEND` | |
| 2 | `DUPLICATE_MODULE` | |
| **new** | `FOREIGN_PREFIX_IN_COLLECTION` | `marshal_post_deck` (50 `CTX_Column_*`), `hospitality_deck` (6 `CTX_*`) — `build_items` already refuses these and the registry did not record it (R2-332) |

**Two `PARTIAL_BUILD` blockers are retired on measurement, not waived.**
`catch_fence_post`'s blend holds 676 against an item-declared 690 — but the
**world builds 676**, and all 676 units sit within 2 m of the class geometry
they replace at a median of 0.68 m. There is no 690-post population anywhere in
this world to fall short of; the 690 is the item's own pre-filter site count.
`timing_stand` is 10 of 10 and never had one.

**The nearest next candidates, in order:**

1. **`tyre_blanket`** — still the only row whose *only* blocker is the gate
   verdict. 56 of 56, world frame, supersedes nothing. Re-gate it and it places.
2. **`hospitality_deck`** — `ARCH_Ground_Decks` is exactly this feature and the
   item builds 5 for `ground_decks = 5` at 57.93 % containment. Its
   `class_switch` (`architecture.ground_decks`) is **already declared and
   already wired to fire** the moment the row goes `PLACE`. It needs a gate
   pass and its `CTX_*` objects declared as a rig sub-collection.
3. **`armco_post`** — `class_switch` declared (`barriers.armco_posts`) and the
   removal site identified at a clean function boundary. Blocked on population:
   3,236 built against a world that builds 3,561, so placing it today is a
   325-post hole and the W-beam rails lose their only support.
4. **`pit_wall_unit` + `timing_stand` together** could retire `ARCH_PitWall`
   entirely — the two cover 57.33 % and 17.43 % of it and 119 of 119 / 10 of 10
   units land on it — but somebody has to own the terminal nose, the coping and
   the ~40-panel advertising band first.

## R2-366 — the apron's only relief octave is sub-pixel, so the closing frame sees a painted grid and nothing else

**The complaint** was that the paddock apron and forecourt paving — the largest
surface in the film's closing 4K frame — read as a grid of subtly different flat
grey rectangles with no aggregate, no joints that read as joints, no wear, no
camber. An untextured placeholder with a per-tile albedo jitter standing in for
material.

**Three measurements, in this order, and the second one reversed the first.**

**1. Which surface is it.** `tools/r2366_crop_owner.py` raycasts the delivered
frame's own pixels — the ONER pose and lens for frame 2978 out of
`camera_rig_path.json`, one ray per sampled pixel of the brief's crop
`900x420+900+780`, resolved against a real `build_architecture` build. 9,761
hits of 10,500 rays:

| object | material | share of crop |
|---|---|---:|
| `ARCH_Paving_Paddock` | `A_ConcSlab` | **32.5 %** |
| `ARCH_Paving_ApronPlatform` | `A_ConcApron` | **21.5 %** |
| `ARCH_Paving_Forecourt` | `A_ForecourtSlab` | **5.8 %** |

**59.8 % of the crop is paving, across THREE materials, and the biggest of them
is the one the brief did not name.** See R2-367.

**2. What relief it actually has — and the first audit of it was wrong in the
alarming direction.** `itemkit.bump_relief_report` reported the shipped stages at
m 1.889 / 2.966 / 2.090 against `isotropic_macro`'s 0.35–0.95 ceiling: all three
HIGH, apparently over-driven into the range where 1.66 was rejected as felt.

That reading is an artefact of the function's own conservative default. It
computes `amp = Distance * Strength * height_pp` with `height_pp = 1.0`, and its
docstring says plainly that a raw Noise swings about 0.6 of that. So
`tools/r2366_swing.py` renders each height chain alone — its own scene, 1 sample,
denoiser off, Standard view transform, 32-bit EXR — and measures the swing:
**0.2443 / 0.2443 / 0.2365** over the 1st–99th percentile. With the measured
swing the same law gives:

| material | λ | amplitude | m | verdict |
|---|---:|---:|---:|---|
| `A_ForecourtSlab` | 18.82 mm | 0.313 mm | **0.471** | ok |
| `A_ConcApron` | 18.82 mm | 0.508 mm | **0.764** | ok |
| `A_ConcSlab` | 29.09 mm | 0.520 mm | **0.507** | ok |

**The relief that exists is correctly banded. Nothing was over-driven.** Acting
on the first audit would have reduced relief that was already right. See R2-368.

**3. The actual defect, which is octaves and not amplitude.**
`tools/r2366_surface_visibility.py` projects the paving rectangle through all
2,978 camera poses and reports the surface scale per delivered pixel. The paving
runs from **5.3 mm/px at the beat-3 breach (f945, 5.9 m)** to **339 mm/px at the
closing wide (f2978, 611 m)** — a **64× span**, and at the closing frame an
18.8 mm feature is **0.055 px**.

> **So the frame the film ENDS on sees no relief at all.** The only structure
> left at a scale it can resolve is the per-cell white-noise albedo hash — a
> flat tone per cell with a hard step at the boundary and no normal change
> across it. `A_ConcSlab`'s cell is 5 m, which is **15 px** in that frame, and
> its ramp spans ±20 % of luminance. That is the rectangular patchwork,
> precisely: the surface is not under-textured, it is textured at one wavelength
> that the shot cannot see, and painted at one the shot can.

**Why it cannot be answered with more albedo.** R2-060: a flat quad with z ≡ 0,
painted with stripes aligned to the light, scores dip 0.6308 against real 2 mm
ribs at 0.6082, because after a band-pass a sharp albedo step and a lip-and-shadow
leave the same signature. The shipped defect is that failure shape already.

### The repair — four octaves, every amplitude derived

`build_architecture.PAVING_RELIEF` and `_paving_relief()`. Four chained bump
stages spanning 25.8 mm to 5.33 m, so something is resolved at every distance
the take visits:

| stage | λ | at 5.3 mm/px (beat 3) | at 339 mm/px (closing, along) | at 80 mm/px (closing, across) |
|---|---:|---:|---:|---:|
| aggregate | 25.8 mm | 5 px/cyc | 0.1 | 0.3 |
| float | 228.6 mm | 43 | 0.7 | 2.9 |
| screed | 1.39 m | 263 | 4.1 | 17.4 |
| settle | 5.33 m | 1006 | 15.7 | 66.7 |

`m_target` is chosen inside `RELIEF_BANDS['isotropic_macro']`, rolling off with
wavelength because fine texture is genuinely sharper than large form, and the
millimetres come from `itemkit.relief_amplitude_for(m, λ)`. Measured back through
`bump_relief_report`, all three materials land at **m 0.560 / 0.450 / 0.380 /
0.360** on their own wavelengths.

**BOUND BOTH WAYS, AND BOUND THE SURFACE RATHER THAN THE STAGE.** Four
independent random fields perturb the normal independently, so their slopes add
in quadrature. Every stage can be in band while what they add up to is not.
Quadrature **m = 0.889**, inside the same 0.95 ceiling.

**The height signal is normalised so the audit reads true.** Each stage puts a
Map Range on its own measured p1..p99 before the bump, so `Distance` IS the
peak-to-peak metres and `bump_relief_report`'s 1.0 default becomes exact rather
than conservative — the next person to audit these materials gets the right
number without needing the swing table. The clamp flattens 2 % of the area by
construction; sizing to the full range instead would under-drive everything that
has area.

**The per-cell hash is demoted, not deleted** (`_batch_tone`, `BATCH_TONE_KEEP =
0.30`). Adjacent bays really are poured from different batches and really do
differ — the per-cell step is a true thing about the subject. What was wrong was
its size relative to everything else: ±15 % (apron) and ±20 % (paddock) of
luminance at a 5 m cell, competing against relief at 0.055 px. A real
batch-to-batch difference in cast concrete is a few per cent.

---

## R2-367 — the brief named two paving surfaces and the biggest one in its own crop was a third

The brief called the region "the paddock apron and forecourt paving". Raycasting
it (R2-366, measurement 1) puts `ARCH_Paving_Paddock` / `A_ConcSlab` at **32.5 %
of the crop** — larger than the apron at 21.5 % and the forecourt at 5.8 %
combined-and-then-some.

`A_ConcSlab` is a different factory (`mat_paving`, 5.0 m uniform hash cell) from
the other two (`mat_slab`, 1.5×1.0 m and 5.0×5.0 m cells). Repairing only the
two named materials would have left **a third of the complained-about area
untouched**, and the frame would have come back still patchworked, with a fix
that measured well on everything it had been pointed at.

`docs/screen_presence.json` could not have answered this: it is stamped against
`assembly6` and the superseded camera. **The delivered frame's own pixels were
the only current source, so they were the source used.**

---

## R2-368 — a conservative default is not a measurement, and it pointed the wrong way

`itemkit.bump_relief_report(node_tree, height_pp=1.0)`. The default is honest and
the docstring is explicit: a raw Noise swings about 0.6 of full scale, so "a
stage this reports at m = 2.3 is therefore at least 1.4, never less."

**Used as an audit that is right. Used as a verdict it is a 4× over-read, and it
over-reads in the direction that manufactures work.** The first audit of this
task called all three shipped paving stages HIGH — m up to 2.966 against a 0.95
ceiling — and the obvious response would have been to cut relief. Measured, the
swing is 0.2365–0.2443 and every one of those stages is **in band**.

The general shape, and it is one this log already carries in other forms: **a
bound presented in the place where a value belongs.** The fix is not to change
the default — it is correct as a floor — but to measure the swing when
authoring, which `tools/r2366_swing.py` now does, and to normalise the height
signal in the graph so the default stops being approximate for these materials.

---

## R2-369 — the showroom roof is not near-field in beat 1; it is a beat-6-only surface

The brief states that "the showroom roof is near-field in beat 1". Measured, it
is not.

`tools/r2366_surface_visibility.py` projects the `Ceiling` slab's top face
(x ±15.25, y ±11.25, z 6.500, appended at identity by `build_film_scene`) through
every one of the 2,978 poses:

- visible on **151 frames, all of them in beat 6**
- every one at **594–610 m**, at an essentially constant **352 mm per delivered
  pixel**
- **26,078 px** of an 8.3 Mpx frame, roughly 300 × 90 px

Beat 1's camera stands **inside** the building at z 2–4.5 m with the slab soffit
at z 6.200 above it, aimed at car parts on the dais — the ceiling is above frame,
exactly as round-1's own module docstring predicted ("No camera sees the ceiling…
Anything built up there is invisible"). That claim was true for round 1's four
interior cameras and was never revisited when round 2 flew a camera out through
the glass and up.

**Consequence for the repair, and it is the whole design:** at 352 mm/px a
feature needs to be **≥ ~0.7 m** to occupy 2 px. Fine texture is not merely
wasted there, it aliases across a 151-frame move. The read has to come from form
and objects at the 0.7–10 m scale. Detail is owned by R2-372..376.

---

## R2-370 — every paving bay carries a per-bay vertex colour that no paving material reads

`build_architecture._stain()` (and the forecourt's inlined copy) draws a random
per-bay tone — fresh pour, old polished, a bluer batch of cement — and
`MB.build()` writes it into a `FLOAT_COLOR` CORNER attribute named `"Col"` on
every paving object.

**`mat_slab()` and `mat_paving()` contain no `ShaderNodeVertexColor`.** Only
`mat_generic()` has one, gated on `vcol=True`, and paving does not use it. So the
attribute is written for every bay of `A_ConcApron`, `A_ForecourtSlab` and
`A_ConcSlab` and **read by nothing**. The comment beside it says the amount was
halved "to break the shader's regularity"; it breaks nothing.

**Deliberately NOT wired up here.** Wiring it would restore exactly the thing
R2-366 is removing — a per-bay constant albedo step — and this defect is that
there is too much of that signal, not too little. Logged because it is a live
trap: it looks like a working variation layer in the source and would be cited
as one.

---

## R2-371 — decorrelating a shared procedural field silently re-banded it, and the audit caught it

The three paving materials share one relief ladder. Handing all three the same
field would tile a single continuous texture straight across the real joints
between them — the no-repeated-assets law in its procedural form, which the
world-level mesh-spam check cannot see because it counts meshes. So each material
gets its own `relief_mul` and `relief_shift`.

**`relief_mul` divides the wavelength. `relief_amplitude_for` is linear in
wavelength. Holding the amplitude fixed therefore multiplies m by exactly
`relief_mul`.** First build of the ladder:

| material | mul | quadrature m | |
|---|---:|---:|---|
| `A_ForecourtSlab` | 1.37 | **1.225** | HIGH |
| `A_ConcApron` | 0.79 | 0.708 | ok, but two stages LOW |
| `A_ConcSlab` | 1.00 | 0.885 | ok |

A change whose only purpose was to stop three surfaces sharing one field had
moved one of them 38 % out of band. Fixed by dividing `Distance` by `scale_mul`,
after which all three sit at identical modulation on different wavelengths —
same surface character, decorrelated fields.

**The instructive part is that nothing about the intent was wrong and the
artefact was still wrong.** It was found because `tools/r2366_relief_audit.py`
reports the quadrature sum and not only the per-stage numbers, i.e. because the
check bounded the surface rather than the stage.

---

## R2-377 — the A/B, both distances, against a null and a negative control

Four scenes off one `build_architecture`, differing only in `PAVING_RELIEF_LEGACY`
(R2-371). Same camera, lens, samples (400 / adaptive 0.01), denoiser, exposure
(`film_exposure.FILM_EXPOSURE`, −3.628 — not the refuted contract value). NULL is
the AFTER blend copied byte-for-byte (md5 verified equal) and rendered a second
time, so the pair distance has a floor.

**The measurement window is raycast, not eyeballed.** The brief's crop is only
59.8 % paving and the rest — barriers, fences, containers, the pit wall — carries
far more contrast than concrete does. Measured over the whole crop the first run
reported a spectral `peakiness` of 39,966 in BOTH arms: that number is the
diagonal barrier line, and **it would have read the same whether the defect was
present or absent**. `tools/r2366_paving_window.py` finds the largest rectangle
clearing a purity threshold, computed once from the BEFORE build and reused
unchanged for every arm so no arm can move the goalposts.

### Closing wide, f2978 — window 440×150+1760+1310, 95.0 % paving, 80 mm/px across

| | peakiness | peak period |
|---|---:|---:|
| BEFORE | **232,236** | 75.0 px = **6.00 m** |
| AFTER | **10,997** | 75.9 px = 6.07 m |
| NULL | 10,983 | 75.9 px |

**A 21× reduction, and the metric found the defect's own wavelength unprompted** —
6.00 m is `A_ConcSlab`'s 5 m hash cell beating against its 6 m bay. The residual
peak at the same period is the REAL bay joints, which should survive; what went
is the painted grid on top of them.

| | rms | p99.9 | max | > 0.02 |
|---|---:|---:|---:|---:|
| BEFORE vs AFTER | 0.01110 | 0.04219 | 0.05624 | **7.945 %** |
| AFTER vs NULL | 0.00041 | 0.00246 | 0.00394 | 0.000 % |

**Signal / null = 27.2×.**

### Near, f945 (beat-3 breach) — window 528×512+3152+208, 95.4 % paving, 7.3 mm/px

Chosen by `tools/r2366_surface_visibility.py`, not by eye, and then confirmed by
raycast: 71.2 % `A_ConcSlab` at 17.6 m, 24.2 % `A_ConcApron` at 38.7 m. **11×
finer than the closing wide.** The first guess at where the near paving was
returned 0.0 % paving — the region was scanned rather than assumed.

| | peakiness | rms | > 0.02 |
|---|---:|---:|---:|
| BEFORE | 424,177 | — | — |
| AFTER | **93,971** | — | — |
| NULL | 94,274 | — | — |
| BEFORE vs AFTER | | 0.02397 | **33.127 %** |
| AFTER vs NULL | | 0.00061 | 0.000 % |

**Signal / null = 39.5×**, and the near view moved FOUR TIMES MORE of its pixels
than the wide (33.1 % against 7.9 %) — the fine octaves are doing real work at
7.3 mm/px, which is the half of the trade that a wide-only tuning would have lost.

### The negative control (R2-150)

A window of the same frames that is ≥ 98 % NOT paving, found by the same tool
with the mask inverted. **Deliberately not the sky:** the sky region reads a mean
of 0.00002, and a control that is identically black proves only that black does
not move.

| frame | control window | BEFORE vs AFTER rms | > 0.02 | paving > 0.02 |
|---|---|---:|---:|---:|
| 2978 | 695×240+700+1260 | 0.00147 | **0.094 %** | 7.945 % |
| 945 | 3328×1408+512+752 | 0.00048 | **0.015 %** | 33.127 % |

The control is **not** at the null, and that is reported rather than hidden: it
sits at 4.2× the null at f2978. Two real causes, both expected — the window is
98 % non-paving, not 100 %, and the paving bounces light onto everything beside
it. What matters is the ratio: the change is **85×** more concentrated in the
paving than in the control by pixel fraction at f2978, and **2,200×** at f945.

### What did NOT discriminate, reported because it did not

The per-octave band-power table moves by less than 1 % between arms at both
frames. Even inside a 95 %-pure window the large-scale scene shading — the cast
shadows, the light falloff, the camber of the whole apron — dominates every
octave. It is kept in the output as a null result, not deleted: the periodicity
statistic is what carries this verdict, and pretending the octave table
contributed would be inventing support.

---

## R2-378 — the relief survives its own paint being taken away

R2-060's lesson is that scoring better is not enough; it has to be better FOR THE
RIGHT REASON, because a painted albedo step and a lip-and-shadow leave the same
band-passed signature. `tools/r2366_paint_vs_geometry.py` separates the scene
rather than looking for a cleverer statistic: four arms per material, same scene,
same camera, same sun, same sampler, one window layout computed from the geometry
that placed the planes.

| material | orig | **geo** | paint | flat (floor) | geo − floor | relief share |
|---|---:|---:|---:|---:|---:|---:|
| `A_ConcSlab` | 0.6236 | **0.3257** | 0.2319 | 0.0047 | **69×** | 58.4 % |
| `A_ConcApron` | 0.3637 | **0.3506** | 0.0785 | 0.0046 | **75×** | 81.7 % |
| `A_ForecourtSlab` | 0.3227 | **0.3145** | 0.0985 | 0.0047 | **66×** | 76.2 % |

Band-passed peak-to-peak of LOG luminance (linear leaks paint-on-curvature 40.9×
harder, R2-060). `geo` = every paint input forced constant, Normal untouched.
`paint` = the surface replaced by an emission of its own base colour. `flat` =
`geo` with Normal unlinked as well.

**For the apron and the forecourt slabs, taking the paint away barely moves the
number** — 0.3506 against 0.3637, and 0.3145 against 0.3227. The structure is
carried by the relief, not by the paint. `A_ConcSlab` keeps the largest paint
contribution because its rubber pick-up is a genuine dark albedo feature of a pit
lane, and even there relief carries 58 %.

**THIS TOOL WAS WRONG THREE TIMES BEFORE IT WAS RIGHT, and each way is worth
keeping:**

1. **The panel windows were assumed rather than computed.** Four columns and
   three rows do not tile a square render, so every row window straddled black
   background; log(1e-8) dominated and all four arms read p-p ≈ 8.1 with
   `geo/flat` = 1.00. The rects are now written out by the builder from the same
   numbers that placed the planes.
2. **The verdict was a ratio against a quantity that is identically zero.** A
   uniform plane under one sun has a band-passed p-p of exactly 0, so
   `geo / flat >= 2.0` passed for any `geo` whatsoever — **a check that cannot
   fail is not a check.** The bar is now an absolute margin in p-p.
3. **The render was CLIPPED AND QUANTISED and the numbers were stable, plausible
   and meaningless.** The contract sun on 0.5-albedo concrete gives a radiance
   near 4.0; the farm returned the frame clamped to 1.0 at 255 levels, every lit
   arm saturated, `flat` reading exactly 1.00002 with sd 0.000000. **Two
   genuinely different renders produced band powers identical to four decimal
   places, and that impossibility is what exposed it** — a null was checked
   rather than accepted. The probe now scales the sun by 0.04, which is an
   additive offset in log luminance and so cancels in the band-pass, and it
   REFUSES a render with more than 2 % of pixels at the clip.

Note the farm writes 8-bit regardless of the requested EXR, so `flat` at 0.0046
is a real quantisation-plus-sampling floor rather than zero. That makes it a
better control than it was, and every `geo` clears it by 66–75×.

---

## R2-379 — the variety measurement, for a field rather than a mesh

The no-repeated-assets law is enforced by mesh-instance counting, and **it cannot
see this class of repeat at all**: three procedural surfaces sharing one field
add no instances, and the world-level spam check would score them 0 %. The three
paving families meet each other along real joints in the closing frame —
forecourt to apron at the pavilion, apron to paddock at the pit exit — and one
shared field would run straight through those joints as a single continuous
texture.

Cross-correlation of the three `geo` arms, sampled at the object-space points the
delivered frame actually reads (R2-378's probe points):

| pair | r |
|---|---:|
| `A_ConcSlab` × `A_ConcApron` | **+0.0095** |
| `A_ConcSlab` × `A_ForecourtSlab` | **+0.0006** |
| `A_ConcApron` × `A_ForecourtSlab` | **−0.0197** |

**Worst \|r\| = 0.0197**, against 1.000 for a shared field. The decorrelation is
`relief_mul` (1.00 / 0.79 / 1.37, mutually non-integer) and `relief_shift`
(displacements far larger than the longest 5.33 m octave).

**And the surfaces themselves add no repeats:** the change moves no vertex and
adds no object. `tools/r2366_geometry_unchanged.py` fingerprints every
world-space vertex coordinate of all 32 mesh objects — 2,548,890 vertices —
sha256 **b236c411…IDENTICAL** between the arms, with exactly **3 of 39** material
graphs differing and those three being exactly the paving. Counts were not the
evidence: `assembly6` once had every module summary bit-identical to `assembly5`
with one object moved 3.19 m.

---

## R2-380 — what is owed, and what is not

**A WORLD REBUILD IS OWED.** This is a source change in
`world/build_architecture.py` and it moves nothing until the assembly is rebuilt.
The shipping world `assembly9.blend` and the film scenes `render/film14*.blend`
still carry the old paving.

**What the rebuild will change, predicted before it runs:** 3 of 39 materials,
0 of 28,781 objects, 0 vertices. Every geometric gate — placement, collision,
depth, seam, levelling, the transit line — reads geometry that is provably
bit-identical, so none of them can change verdict. `tools/r2366_relief_audit.py`
and `tools/r2366_geometry_unchanged.py` are the two checks to re-run against the
rebuilt world, and both are seconds rather than minutes.

**It batches cleanly with the queue.** The user's note says several fixes are
already waiting for the next assembly; this one adds no build time (material
construction is milliseconds) and no memory.

**Not owed:** no contract revision — `world_contract.py` and `itemkit.py` are
untouched, as required. No re-gate of any item. No camera or telemetry work.

**The showroom roof is a different answer entirely** — its source is round-1, in
the read-only tree, so it is a post-append tool on the film scene and needs no
world rebuild. See R2-372..376.

### One hazard for whoever schedules the rebuild

**`world/build_architecture.py` had uncommitted work from another live agent in
it while this change was being made** (R2-331/R2-334, welding five objects into
`ARCH_PitWall`, +7,268 verts). Nothing here touches those lines and no `git add`
in this task went outside its own paths, but the rebuild will pick up BOTH
changes, and the pit-wall weld has not been gated by this task. Attribute
anything unexpected in `ARCH_PitWall` to R2-331 before attributing it here — the
free control for that is `PAVING_RELIEF_LEGACY`, which isolates this change from
everything else in the file.


---

# THE SHOWROOM ROOF — R2-372 to R2-376

Appended by the roof agent. `render/r2372_roof_after.blend`, built by
`tools/r2366_roof_build.py` out of `render/film14_breach_r6.blend`.

---

## R2-372 — the showroom roof is round-1 geometry: ONE QUAD OF 686 m², and the fix has to be a post-append build

**The complaint** was that in the closing 4K frame `render/r6_after/full_f2978.png`
the showroom's roof is a single flat brown-grey plane with zero detail — no panel
seams, no plant, no gutter, no edge trim, no soiling — on the hero building.

**It is not round-2 geometry.** The object is `Ceiling`, emitted by
`/home/zany/opus5-car-render/build/s02_showroom.py:490` `build_shell()` as a
literal `C.box(...)`: **8 vertices, 6 quads, flat shaded, no bevel, no
subdivision**, x −15.25…+15.25, y −11.25…+11.25, soffit z 6.200, **top z 6.500**.
Its material is `CeilingMat` from `build/s03_materials.py:207` — a two-node
Principled, Base Color (0.075, 0.076, 0.080), Roughness 0.78, **no bump, no
normal, no displacement**. It reaches the film through `tools/build_film_scene.py`'s
append of `world/car_anim.blend`'s SHOWROOM collection, at identity. The top
face is **one quad of 686 m²**.

`opus5-car-render` is read-only (law 1), so it cannot be corrected at source.
`tools/add_dais_ramp.py` established the answer for exactly this shape of
problem and `tools/r2366_roof_build.py` follows it: open the film blend that
already exists, ASSERT the datum, build, save somewhere new.

**`CeilingMat` IS NOT TOUCHED, and that is a deliberate refusal.** It is also on
`Cove_Coffer_0/1` and `WallLine_BackFin_0/1` / `WallLine_SideFin_0/1` — the
**interior**. The same cuboid's *underside* at z 6.200 is the showroom's ceiling,
which `r2366_surface_visibility.py` shows is separately visible in beat 5 at
~200 m. Restyling `CeilingMat` would have fixed the roof by breaking the room.
Everything built here is a separate warm-roof buildup **entirely above z = 6.500**,
in its own collection `R2_ShowroomRoof`, with its own ten materials. No round-1
datablock is edited.

### The viewing regime — and the anisotropy the single number "352 mm/px" hides

`tools/r2366_surface_visibility.py` (the lead's) establishes: the roof top is
visible on **151 of 2,978 frames, all in beat 6, all at 594–610 m**, never
near-field, occupying ~26,000 px of the 8.3 Mpx frame at **352 mm per delivered
pixel**. Projecting the four corners through the f2978 ONER pose gives the quad
**(1788, 949) (2073, 951) (2069, 1038) (1771, 1036)** — 302 × 89 px. And that
means the scale is **strongly anisotropic**:

| direction | extent | screen | scale |
|---|---:|---:|---:|
| along **y** (across the frame) | 22.5 m | 285 px | **79 mm/px** |
| along **x** (into the frame) | 30.5 m | 88 px | **347 mm/px** |

352 mm/px is the *foreshortened* axis. A feature varying along **x** needs
≥ 0.7 m for 2 px; a feature varying along **y** is resolved to **0.16 m**, 4.4×
finer. Both numbers were used: the read is carried by form and objects at
0.7–10 m, and the finer periodic stages run in **y** where they are resolved.

### What was built

126 objects, 143,776 triangles, 72,818 vertices, ten new materials, extent
x/y ±15.295 / ±11.295, **z 6.500 … 9.654** (nothing below the round-1 slab top).

* **A 1.100 m parapet with an oversailing coping.** Not styling: below 1.100 m a
  roof carrying plant needs a guardrail, and a 48 mm guardrail tube is **0.14 px**
  at this range — thin geometry that would shimmer across 151 frames for no read.
  The parapet does the same job as form the camera can resolve, and does it three
  ways at once: the −y run throws a **4.12 m shadow band across the roof** (52 px
  of the 285), the coping catches a highlight the membrane cannot, and the near
  run **occludes 4.94 m of deck** (14 px). Coping falls inward at 1:12, oversails
  45 mm each side over a 30 mm drip.
* **Falls.** Four valley gutters at y = −10.20 / −3.55 / +3.55 / +10.20, 1:40
  cross-falls to the ridges between them, 1:100 along the valleys to eight
  outlets. Six alternating tonal bands ~45 px wide.
* **Roof plant**, which is where most of the read is: two air handling units, a
  five-machine condenser bank behind two acoustic louvre screens, a ducted run on
  sleepers, four flues, an access hatch with the lid propped, two rooflights, a
  90 m-long walkway, eight outlets, three penetrations, a comms dish, three
  fall-arrest anchors and a stack of spare pads. A 1.4 m unit is 18 px of screen
  and throws a **6.3 m shadow** — up to 80 px of unmistakable, correctly-directed
  dark.
* **Membrane bays at 2.00 m**, laps running in y so the pitch lands at 5.8 px —
  above the ~4 px where a repeating pattern starts to alias across a 151-frame
  move — and **built as real vertices, not as a bump**.

### No repeated assets — measured

`tools/mesh_reuse.py` on the built roof:

| family | objects | meshes | obj/mesh | top share | gini |
|---|---:|---:|---:|---:|---:|
| `RRF` | **126** | **126** | **1.00** | **0.8 %** | **0.000** |

Every object has its own mesh datablock. The spam threshold the tool fails on is
top_share ≥ 40 %; this is 0.8 %, which is 1/126 — the floor. `tools/instance_variety.py`
returns **`INSTANCE_VARIETY_VACUOUS`** and it is right to: the roof realises
**zero** instances, because nothing here is instanced at all. The two places
repetition is intrinsic — a run of walkway pads, a rank of louvre blades — are
built as **one datablock each** with the per-item variation (height, gap, width,
offset) baked in, so the repetition cannot become N copies of one asset.

`tools/r2366_roof_build.py` refuses a build whose `objects / meshes` exceeds 1.0
(`ROOF_REPEATED_ASSET_VIOLATION`), so this is a gate and not an observation.

### Two refusals the tool makes, and a third it learned to stop making

* `ROOF_NO_DATUM_REFUSED` — the `Ceiling` cuboid must be 8 verts / 6 polys with
  top z 6.500, soffit 6.200 and extents ±15.25 / ±11.25, to 1e-4. The 8/6 test is
  what stops a second run doubling the roof up.
* `ROOF_RECESS_BLACK_VIOLATION` — every groove is declared with its width, depth
  and the bearing it runs along and checked against `world_contract.
  recess_relative_radiance`. Defect #48 was 3,390 pure-black pixels from 35 mm
  joints; the worst here is the coping drip at **0.174** against a 0.10 floor.
* `ROOF_VOLUME_OCCUPIED_VIOLATION` **as first written was useless**, and this is
  worth recording. It asked bounding boxes, and on the film blend it refused the
  build with *"47 objects already reach into z > 6.500 inside the parapet line"* —
  the list being `TER_Ground` (z −12.8…364.5, x −10907…10827), `SURF_Track`,
  `ARCH_Ground_Fences` and forty-four other world-scale meshes whose AABB of
  course contains a 30 × 22 m box at the origin. Not one of them has a vertex up
  there. An AABB is a **filter**, so it is now used as one: AABB to shortlist,
  then the **evaluated mesh's vertices in world space**. On the film blend that
  is 47 shortlisted, **1,855,096 vertices tested, 0 objects with real geometry in
  the roof volume**.

---

## R2-373 — the relief law has no AZIMUTH term, and a stage laid the wrong way delivers 0.53 of what it was cut for

`itemkit.relief_amplitude_for(m, wavelength_m)` inverts `m = 2 sin(θ) / tan(e)`.
That derivation tilts the surface normal **in the vertical plane through the
sun**. A stage whose gradient runs along a fixed world axis does not: it only
tilts that far toward the sun **in azimuth**, and delivers

```
m_real  =  m_law * |axis · sun_horizontal|
```

At this film's bearing of −57.97° that is **0.530** for a gradient in x and
**0.848** for one in y — **a factor of 1.6 between two stages of identical
amplitude and wavelength, purely from which way they were laid.**

**Measured the hard way first.** The 2.00 m membrane bay camber was cut to the
law's 35.3 mm for m = 0.50. The bay laps run in y, so the camber's gradient is in
x. Differentiating the built height field and evaluating Lambert against
`world_contract.SUN_DIR` returned **m_pp = 0.322** — below `isotropic_macro`'s
0.35 floor, for a stage the law said was mid-band. The law was not wrong; it was
being asked the wrong question.

**The instrument is `stage_slope_audit()` in `tools/r2366_roof_build.py`**, and
it is the reason both faults below were caught before a single pixel was
rendered. It differentiates **the same height field the deck mesh is cut from**
— `buildup(x, y, only={stage})`, one stage at a time, on a 20 mm grid — builds
the true surface normal and evaluates

```
rel = max(0, n · L) / (n_flat · L)
```

reporting the peak-to-peak spread of `rel`, which **is** the radiance modulation
the relief law is a shortcut for. It does not translate; `relief_budget` does,
and the two are printed side by side so the shortcut can be checked rather than
trusted:

| stage | layer | λ (m) | amp p-p (mm) | `relief_budget` m | **measured m_pp** | band |
|---|---|---:|---:|---:|---:|---|
| `valley_1in100` | GEOM | 15.00 | 47.7 | 0.090 | **0.048** | form |
| `falls_1in40` | GEOM | 6.65 | 52.9 | 0.226 | **0.192** | form |
| `bay_camber` | GEOM | 2.00 | 45.0 | 0.638 | **0.410** | isotropic_macro ✓ |
| `crosslap_welt` | GEOM | 0.72 | 12.7 | 0.500 | **0.579** | isotropic_macro ✓ |
| `deck_settlement` | GEOM | 5.00 | 21.1 | 0.120 | **0.035** | form |
| `ponding` | GEOM | ~5.2 | 26 | — | **0.120** | form |
| `crickets` | GEOM | ~2.5 | 48 | — | **0.266** | form |
| **ALL together** | GEOM | — | — | — | **0.887** | |
| `membrane_ripple` | BUMP | 0.300 | 5.288 | 0.500 | (sub-pixel) | isotropic_macro ✓ |
| `membrane_grain` | BUMP | 0.025 | 0.247 | 0.280 | (sub-pixel) | isotropic_micro ✓ |

Amplitudes are **derived** — `K.relief_amplitude_for(M / axis_gain("x"), λ)` —
never chosen in millimetres, and then **capped by physics**: asking the law for
m = 0.50 through a gain of 0.530 wants **66.8 mm** of ballooning over a 2.00 m
bay, which is 3.3 % and is not a membrane. The cap is 45 mm (2.2 %), the top of
what a mechanically fastened single-ply actually does between fastener rows, and
the audit then reports what that really delivers: **0.410, in band**.

**Three stages are deliberately OUTSIDE every band and the tool prints `(form)`
rather than `LOW`.** A roof fall is limited to 1:40 by what water and a squeegee
will do; forcing `falls_1in40` into `geometry_fold` (0.60–1.40) would mean a 1:9
roof, which is not a flat roof. "Too little relief is as wrong as too much"
governs a stage claiming a texture band. It does not license inventing a
building that cannot exist.

### The two faults the audit caught, neither of which any other check could see

1. **A 16 mm vertical cliff every 2.00 m.** The cross-lap welt's stagger was
   `hash01(bay_index)` — a per-bay constant, i.e. a **step function** — so the
   welt jumped up to 1.6 m at every lap and the membrane acquired a vertical
   discontinuity. `relief_budget` reported the stage at a serene m = 0.500. The
   slope audit returned **slope_max 22.334°** against a design maximum of 3.17°.
   A roll laid by hand wanders; it does not teleport. Now `fbm1(x / 6.0)`, and
   slope_max is **4.638°**.
2. **A stage that was silently doing nothing.** `crickets` returned m_pp 0.000
   because its loop sat below an early `return` in the ponding gate. Zero, from a
   stage with six declared crickets in it, is only visible if something asks each
   stage separately.

**Check both layers.** `bump_relief_report` on all ten new materials, plus
`geometry_relief_report` on every roof mesh with bands widened to
(0.05, 0.16, 0.45, 1.40, 4.50, 40.0) m — the defaults top out at 0.15 m and
would have reported **zero edges in every band** for a roof whose finest edge is
0.10 m:

| mesh | band (m) | edges | rms dihedral | m |
|---|---|---:|---:|---:|
| `RRF_Deck` | 0.05–0.16 | 131,480 | 0.938° | 0.148 |
| `RRF_Parapet_S` | 0.05–0.16 | 189 | 6.883° | 1.084 |
| `RRF_Parapet_S` | 0.16–0.45 | 1,038 | **73.536°** | **8.673** (an arris — `hard_feature`) |
| `RRF_Parapet_S` | 0.45–1.40 | 249 | 13.519° | 2.114 |
| `Ceiling` (before) | every band | **0** | — | — |

`RRF_Deck`'s 0.148 is the **per-edge** dihedral on a 0.10 m grid, and
`geometry_relief_report`'s own docstring gives the conversion: for a sinusoid
resolved by n samples per wavelength the per-edge dihedral is about 2π/n of the
full swing. At 20 samples per 2.00 m bay that is 0.148 × 20 / 2π = **0.47**,
which reproduces the slope audit's 0.410 for the same stage from a completely
different direction. And `Ceiling`, the shipped roof, returns **zero interior
edges in every band from 50 mm to 40 m**: its top face is one quad, so there is
no wavelength at which it has any relief at all.

`bump_relief_report` on `CeilingMat` prints **"NO ShaderNodeBump AT ALL — zero
shader relief"**. Both layers, before and after, on the same instrument.

### An addendum, same family, found while auditing this file against law 4

`itemkit.NT.principled_out` maps a keyword to a socket with
`k.replace("_", " ").title()`. That turns `specular_ior_level` into
**`"Specular Ior Level"`**, and the live socket on a Blender 5.2 Principled BSDF
is **`"Specular IOR Level"`** — `IOR` is an initialism and `.title()` lower-cases
its last two letters. None of the three candidates the loop tries
(`specular_ior_level`, `Specular Ior Level`, `SpecularIorLevel`) matches, so the
loop **falls through silently** and the socket keeps its default of 0.5.

**Ten materials in this roof asked for a specular level and ten got 0.5.**
Verified against a live BSDF, not inferred: `[c for c in candidates if c in
n.inputs]` returns `[]`. Fixed by a local `_pout()` wrapper that sets it through
`pin_named`, which **raises** rather than falling through, and the built file now
reads back 0.420 / 0.520 / 0.620 / 0.400 / 0.450 where they were asked for.
`render/r2372_roof_after.blend` and its null were rebuilt after the fix.

This is R2-038's family — a socket addressed by a name one transformation away
from the real one, with no error — and it is in the shared kit, so **every module
that has ever passed `specular_ior_level=` to `principled_out` has been silently
ignored**. `itemkit.py` is frozen for this block and was not edited; the wrapper
is local. It is worth a look by whoever owns the kit.


---

## R2-374 — the shared A/B image reader byte-swaps every 16-bit pixel, and a FLAT PLANE reads back at sd = 0.30

`tools/r2256_ab_measure.py` is the established A/B pattern this block was told
to follow. Its `gray()` does

```python
raw = subprocess.run(["/usr/bin/magick", path, "-colorspace", "RGB",
                      "-depth", "16", "gray:-"], capture_output=True).stdout
a = np.frombuffer(raw, dtype=">u2") ...
```

**with no `-endian` on the command line.** On this box — ImageMagick 7.1.2-27
Q16-HDRI — that stream is **little**-endian. Reading it as `>u2` swaps every
pixel's two bytes.

Measured on the paint-vs-geometry BEFORE arm, over the same 25,298-pixel roof
mask, on the same file:

| read | mean | **sd** |
|---|---:|---:|
| `">u2"`, no `-endian` | 0.64337 | **0.300907** |
| `">u2"`, `-endian MSB` | 0.29559 | **0.001567** |
| independent 8-bit read | 0.29646 | 0.003150 |

The second and third agree and describe **a flat plane**, which is exactly what
that arm's picture is: the shipped 8-vertex `Ceiling` slab. The first describes
noise with a plausible-looking mean — which is what a byte-swapped 16-bit image
always looks like, because the low byte becomes the high byte and a smooth ramp
becomes a sawtooth. **A perfectly flat surface acquires sd = 0.30, and every
band-pass statistic taken through it is measuring the byte order.**

It was caught because the first paint-vs-geometry run returned a
`band_rms` of **0.0583** for the flat slab against **0.0662** for the built
roof — i.e. "the roof with 126 objects on it has 14 % more fine structure than
the empty slab", which is not a possible answer. The corrected read gives
**0.00055 against 0.02527: 46×.** Both runs were self-consistent; only one of
them was about the picture.

Both roof tools now **state** the byte order on the command line and then
**check** it against an independent 8-bit read of the same file, refusing if the
two disagree by more than 0.01 mean-absolute (quantisation alone is bounded by
1/512 = 0.00195). A stated assumption that is never tested is the same class of
thing as an unstated one.

**This is not scoped to the roof, and the blast radius was checked rather than
guessed.** `grep -l '">u2"' tools/*.py` returns exactly three files:
`tools/r2256_ab_measure.py`, `tools/r2258_mottle_verdict.py`, and the two roof
tools (now fixed). **Every number either of the first two has ever produced on
this machine should be re-derived before it is believed.**

`tools/r2366_ab_measure.py` — this block's own paving A/B — is **not affected**:
it reads through PIL at 8 bits and undoes the sRGB EOTF in numpy, with no raw
stream and no byte order to get wrong. Its numbers stand.

---

## R2-375 — the roof's relief is GEOMETRY, and it is shown by taking the paint away, not by scoring well

Defect R2-060 is the trap this has to clear: a flat 4-vertex quad with z
identically 0, painted with 30 mm stripes aligned to the light, scored dip
**0.6308** against **0.6082** for real 2 mm trapezoidal ribs. **Albedo variation
is not relief**, and passing a relief check is not the same as passing it for the
right reason.

`tools/r2366_roof_pvg.py` + `tools/r2366_roof_pvg_measure.py` run
`relief_paint_vs_geometry.py`'s method unchanged — not a better statistic, but
**the same statistic re-run on the same camera, the same sun and the same pixel
mask with the scene taken apart**. Eleven arms, each a separate blend, all built
from `r2366_roof_build`'s **own builder** (one definition of the geometry, not a
second description of it) on the round-1 datum, under `itemkit.contract_sun`, at
the film's exact f2978 ONER pose, with `film_exposure.apply` — and **all eleven
on the same AgX transform and the same FILM_EXPOSURE**, so nothing but the
subject differs.

All eleven arm blends and all eleven renders were regenerated after the
`Specular IOR Level` fix in R2-373, so the table below is measured on the build
that ships. The pre-fix run agreed with it to three significant figures.

**The mask is pure geometry**: the round-1 slab rectangle projected through the
f2978 pose and eroded, 25,298 px. Nothing about it is read out of any arm's
pixels, so no arm can move the goalposts by changing which pixels are lit.

| arm | dip | **band r2** | band r4 | band r8 |
|---|---:|---:|---:|---:|
| `before` — the shipped 8-vertex slab | −0.4555 | **0.00055** | 0.00114 | 0.00184 |
| `before_geo` — its paint forced constant | −0.1171 | 0.00059 | 0.00103 | 0.00147 |
| `before_geonb` — and its Normal unlinked | −0.1109 | 0.00059 | 0.00103 | 0.00147 |
| `before_truegeo` — Lambert off its true normal | −0.1677 | 0.00130 | 0.00300 | 0.00515 |
| `before_paint` — emission of its base colour | −0.2504 | 0.00101 | 0.00238 | 0.00405 |
| **`after`** — the built roof | +0.0838 | **0.02536** | 0.04217 | 0.04511 |
| **`after_geo`** — every paint socket forced constant | +0.0499 | **0.02267** | 0.03884 | 0.04128 |
| `after_geonb` — and the Normal unlinked | +0.0492 | 0.02265 | 0.03882 | 0.04127 |
| **`after_truegeo`** — Lambert off the TRUE NORMAL | +0.0091 | **0.01772** | 0.02518 | 0.02199 |
| `after_paint` — emission of base colour, no sun | −0.0162 | 0.01499 | 0.02291 | 0.02211 |
| `after_null` — `after` rendered a second time | +0.0837 | 0.02536 | 0.04216 | 0.04511 |

**The three numbers that decide it:**

| ratio | r2 | r4 | r8 |
|---|---:|---:|---:|
| `after / before` | **46.3×** | 37.1× | 24.5× |
| `after_geo / before_geo` — **both** with paint forced constant | **38.5×** | 37.7× | 28.1× |
| `after_geonb / before_geonb` — and the Normal unlinked too | **38.6×** | 37.6× | 28.1× |
| `after_truegeo / before_truegeo` — mesh only, no bump, no paint | **13.7×** | 8.4× | 4.3× |
| `after_paint / before_paint` — shape without light (see limit 2) | 18.8× | 12.8× | 7.3× |
| **`after_geo / after` — the fraction that SURVIVES the paint being taken away** | **0.89** | **0.92** | **0.92** |

**89–92 % of the built roof's band energy at every scale survives every paint
input on all ten materials being set to a constant 0.18 grey.** And the
`truegeo` arm — Lambert off the evaluated mesh's true normal, where no bump node
and no normal map can reach at all — still stands **13.7×** clear of the same arm
on the flat slab. The relief is carried by triangles.

`after_geonb` differs from `after_geo` by **0.00002** at r2, which says the two
bump stages contribute essentially nothing at this range. That is not a failure;
it is the design working. They are declared sub-pixel at 347 mm/px and are there
so the surface is a material rather than a plane, not to carry the frame.

**The null.** `after_null` reproduces `after`'s dip to **0.00012** and its band energy to
four decimal places, so none of the above is repeat-render noise.

**Two honest limits, stated because the numbers look better than they are
entitled to:**

1. **`relief_anisotropy`'s dip is the wrong shape of statistic for this
   subject** and is reported only because it is the project's own. It is tuned
   for 1–2 px isotropic lip-and-shadow dipoles; this roof's read is 10–80 px
   shadows lying **along** the light, which `item_gate`'s own docstring says
   correctly scores near zero — *"the correct answer for a direction the light
   cannot rake across"*. The verdict rests on **band energy**, which is the
   amplitude clause `item_gate` itself says closes the correlation's blind spot.
2. **The `paint` arm is not "paint only" for a subject made of objects.**
   Replacing every surface with an emission of its own base colour removes the
   light but keeps the **silhouettes** — the edge between an AHU and the deck is
   still there — so `after_paint`'s 18.8× over `before_paint` is *shape without
   light*, not paint. It is reported, not leaned on.

**The sun flip** (`item_gate.two_light_bands`' separator: mirror the sun's
azimuth through 180°, keep elevation, energy, colour and disc size, and move the
Sky Texture with it) gives `corr(dog A, dog B) = **+0.439**` on the built roof —
far from the **+1** a painted surface would give, and with the same explanation
as limit 2: an object's outline sits at the same pixels under both suns. On the
flat slab the same measurement returns **−0.430**, which is `item_gate`'s own
documented behaviour for a featureless plate — *"with no structure the only
thing in the band is the plate's own directional shading, which inverts with the
sun like anything else... rho is a correlation, so it is blind to the fact that
it is correlating almost nothing"*. Both readings are consistent with geometry,
and neither is the load-bearing evidence; the band-energy ratios are.

---

## R2-376 — the roof deck's whole 686 m² lives inside 0.9 % of the tonal range; the fix opens it to 33 %

**The defect, as a number.** The delivered BEFORE frame's roof deck — the
projected slab quad, inset 3 px, 20,250 px of `work/r2372/ab_before.png`
(`render/film14_breach_r6.blend`, ONER, f2978, 3840×2160, 400 samples, adaptive
0.01, OIDN):

| | mean | **sd** | p5 | p50 | p95 | **p95 − p5** |
|---|---:|---:|---:|---:|---:|---:|
| **film BEFORE, roof deck** | 0.4069 | **0.00259** | 0.4041 | 0.4075 | 0.4120 | **0.0078** |

**Ninety per cent of the largest surface on the hero building sits inside a
0.8 %-wide band of the tonal range.** That is not "under-detailed"; it is a
constant. There is no statistic that can be applied to it because there is
nothing in it to measure.

The same slab in the paint-vs-geometry reduced set — same camera, same frame,
same sun, same grade — reproduces it (**sd 0.00157, spread 0.0050**), which is
what makes the reduced set's AFTER comparable:

| arm | mean | **sd** | p5 | p95 | **spread** |
|---|---:|---:|---:|---:|---:|
| reduced BEFORE (the shipped slab) | 0.2956 | **0.00157** | 0.2921 | 0.2972 | **0.0050** |
| reduced AFTER (the built roof) | 0.3470 | **0.14263** | 0.1366 | 0.5662 | **0.4297** |
| | | **×90.8** | | | **×86.0** |

### The A/B on the delivered 4K frame, with its null and its controls

Every arm: the film's own ONER camera, frame 2978, 3840×2160, the same lens,
the same DOF, 400 samples, adaptive 0.01, OIDN on GPU, **no border**. The NULL
is the AFTER rendered a **second time from a byte-identical `cp`** of the same
scene, verified with `cmp` before submission and asserted again by the tool,
which refuses if the three sha256s show the null is a copy of the *picture*
rather than a second render.

| region | pair | rms | p99.9 | max | >0.02 | |
|---|---|---:|---:|---:|---:|---|
| **roof** x 1767–2076, y 908–1040 (40,788 px) | NULL after vs after-again | 0.00058 | 0.00392 | 0.01204 | **0.00 %** | |
| | **A/B before vs after** | **0.09934** | 0.45423 | 0.55940 | **68.08 %** | **170.6×** |
| **roof deck only** (24,272 px) | NULL | 0.00056 | 0.00392 | 0.01176 | **0.00 %** | |
| | **A/B** | **0.11751** | 0.47680 | 0.55940 | **93.68 %** | **208.3×** |
| `foreground_apron` y 1900–2160 (998,400 px) | NULL | 0.00050 | 0.00363 | 0.02518 | 0.00 % | |
| | A/B | 0.00086 | 0.00475 | 0.04421 | **0.00 %** | 1.72× |
| `sky_top_band` y 0–300 (1,152,000 px) | NULL | 0.00089 | 0.00755 | 0.04089 | 0.01 % | |
| | A/B | 0.00198 | 0.01680 | 0.08011 | 0.06 % | 2.23× |

**93.68 % of the roof deck's pixels move by more than 0.02 against a null in
which NOT ONE PIXEL does.**

And the tonal distribution, which is the defect stated as a number and then
un-stated:

| arm | mean | **sd** | p5 | p50 | p95 | **p95 − p5** |
|---|---:|---:|---:|---:|---:|---:|
| **before** | 0.4057 | **0.0110** | 0.4033 | 0.4072 | 0.4120 | **0.0087** |
| **after** | 0.4478 | **0.1099** | 0.2829 | 0.4702 | 0.6172 | **0.3343** |
| null | 0.4478 | 0.1099 | 0.2829 | 0.4702 | 0.6172 | 0.3343 |
| | | **×10.0** | | | | **×38.4** |

The **frame mean is unchanged, 0.3913 → 0.3912**. The fix does not move the
frame's exposure balance; it moves the roof's structure.

### The negative control failed, and the control was wrong, not the change

`sky_top_band` came back at **2.23×** the null against a bar of 2.0×, and the
tool printed `ROOF_AB_CONTROL_MOVED_FAIL`. Two things were wrong with it, and
both are worth the record.

**1. It is not sky.** The camera is at z = 140 m looking DOWN at a building
600 m away; rows 0–300 of this frame contain circuit, kerbs, grass, tree line
and a distant building. Its own local sd is 0.023 — the same magnitude as the
0.02 threshold — so it is the most sampling-sensitive content in the frame. It
was chosen from "the top of a frame is sky", which is an assumption about a
camera, not a measurement of one.

**2. The bar was the wrong reference, and no pixel in the frame passes it.**
`tile_map()` now measures every one of 576 120-px tiles:

* **11 tiles carry the change**, x 1680–2520, y 840–1080 — the roof and its
  shadow, which runs to +y (screen right) at this sun. Ratios **27.8× to
  178.8×**, up to 62.6 % of pixels over 0.02.
* **473 tiles carry none of it** (≤ 0.05 % of pixels over 0.02), and across
  those the BEFORE/AFTER rms is a **median of 2.00× the same-scene null**,
  p95 3.18×, max 5.28×.

That floor is real physics of the renderer, not of the roof: Cycles' adaptive
sampler allocates against a **whole-frame** noise threshold and OIDN is a
convolutional network with a large receptive field, so two renders of
**different** scenes differ slightly everywhere, including 40 km away. The NULL
measures the **same**-scene floor and is the wrong reference for a
before-versus-after distance. The right one is the **different-scene floor**,
and it is measured from the frame itself rather than assumed.

Against that reference: the roof moves **85.1× the floor**; `foreground_apron`
at 1.72× and `sky_top_band` at 2.23× both sit **under the floor's own p95 of
3.18×**. Verdict `ROOF_AB_CLEARS_NULL`.

The bar was not moved to make a number pass — the failing control caused the
instrument to be rebuilt, the new instrument reports the ratio map in full, and
the original failing reading is printed above unchanged.

Crops at 3.5× of the brief's own crop box (`560x380+1680+880`) are at
`work/r2372/briefcrop_{before,after}_35x.png`.

### The farm fault, recorded because three agents hit it

The AFTER and NULL each failed **three times** with

```
rendered BLACK: mean 0.00032, sd 0.00108, 2 distinct luminance level(s)
across 8,294,400 pixels
```

**and it was not this scene.** The identical failure, with the identical
statistics and a ~1,634,337-byte output, is on record in the same window for
agent `r2281oom` on `film14_breach_r6b.blend` and agent `r2171-glass` on
`glass_ab/g_{LIVE,NEG,CTL}.blend`, alongside
`OPTIX_ERROR_UNKNOWN in optixDeviceContextCreate` and
`Out of memory in CUDA queue enqueue (integrator_shade_volume)`. The broker then
cycled through four vast.ai instances that would not boot, over about 75 minutes.

`work/r2372/scenecheck.py` diffs the render-relevant state of
`render/film14_breach_r6.blend` against `render/r2372_roof_after.blend`:
**22 of 25 keys identical** — same world `SKY_World`, same 24 lights, same
camera `ONER`, same lens, same AgX / look None / exposure −3.628, same engine,
same resolution, same frame range, same collection exclusions. The only
differences are the filename, `objects 33254 → 33380`, and the added
`R2_ShowroomRoof` collection. Both frames rendered correctly on the next healthy
instance and are measured above.

### What this owes

**No world rebuild.** Nothing in `build_architecture`, `world_contract`,
`itemkit` or any round-1 module changed; the roof is additive geometry above an
existing slab, built into an existing film blend.

What is owed is **a new film scene**, and it exists:
`render/r2372_roof_after.blend` (4.66 GB), built by
`tools/r2366_roof_build.py` from `render/film14_breach_r6.blend`. If the merge
lands on a later lineage the tool re-runs on it unchanged — it is idempotent,
asserts the datum, and refuses a double build. **The ship declaration has to
move** off `render/film14.blend` onto whatever blend carries this and the other
blocks' fixes. `render/film14.blend` was not touched.

## R2-383 — nine predictions about the 89.79 m event, committed before the data

Written and committed **before** any trajectory was read out of
`sim/out/breach_film_R2281_REBAKE.npz` and before any ablation was run. The
only things known at the time of writing are:

* the table's format and its span (film frames 845…1165);
* the car's authored world-time trajectory over the sim window, which I read
  from `breachlib.Car` because it is the *input* to the sim, not a result of
  it — **the car travels 262.76 m in the 6.9 s sim window and accelerates
  from 9.6 m/s to 58.2 m/s**, crossing the glass plane (nose at x = 15.000)
  at sim frame 145;
* the construction of a mullion segment in `build_breach_sim.py`: 4.7 kg/m of
  6063-T6 over a segment of (head_z − foot_z)/8, split 0.72/0.28 between the
  extrusion body and its pressure plate.

That last one already prices the headline mechanism, so I will say the
uncomfortable thing first.

### P1 — the first frame

`MUL05_S02` first exceeds 0.05 m of displacement within **6 sim frames of sim
f145**, the frame the car's nose crosses x = 15.000. Film frame ≈ 860.

### P2 — the speed ceiling a single impulse allows

The car is doing **16.398 m/s** when its nose reaches the glass. A body struck
once by an infinitely massive plane moving at v, with restitution e, leaves at
at most (1 + e)·v; the car proxy declares `rest=0.05` and the aluminium
`REST_ALU = 0.10`, so a **single** contact cannot send `MUL05_S02` above about
**18 m/s**.

**I predict its measured peak speed exceeds 25 m/s.** If it does, the 89.79 m
cannot be a launch: energy is being added after the impact.

### P3 — the signature that decides between the two mechanisms

Two mechanisms are on the table and they are not the same defect:

* **H_A, the one the brief hands me** — the proxy is `kinematic=True`, so it
  has infinite mass, loses no momentum, and pumps into the field every joule
  the collision should have taken out of the car.
* **H_B, mine** — the proxy is a collider for **262 m** of downrange travel,
  and anything that ends up in front of it or on top of it is *carried*. On
  this hypothesis the mass of the proxy is close to irrelevant.

They separate cleanly on the speed profile. Under H_A the travel is one
launch: peak speed at contact, monotone decay afterwards. Under H_B the
segment's speed *tracks the car's* — repeated re-acceleration, and net
positive dv/dt long after the impact.

**I predict H_B.** Concretely: `MUL05_S02` shows net acceleration over an
interval of ≥ 100 sim frames beginning ≥ 100 sim frames after first contact,
and spends ≥ 300 consecutive sim frames inside the car's local envelope
(|x_local| ≤ 6 m, |y_local| ≤ 2 m, −1 ≤ z_local ≤ 3 m).

### P4 — the number that makes the brief's mechanism the wrong one

A mullion segment in this file is **4.7 kg/m × segment height × 0.72**. On an
approximately 6 m mullion in 8 segments that is about **2.5 kg**. The car is
798 kg. **The mass ratio at this contact is of order 300:1.**

**I predict that giving the car proxy its real dynamic mass changes
`MUL05_S02`'s travel by less than 20 %**, and that the fix named first in my
brief — "a dynamic proxy with the car's real mass and inertia" — therefore
does not fix the defect it is proposed for. An 798 kg body does not notice
2.5 kg. The 45 % momentum figure in the docstring is an *aggregate* over
2,240.9 kg of glass; it is not the impedance any single member sees, and I
think that aggregate has been read as if it were.

I am predicting that my own brief's prime suspect is not guilty of *this*
event. It may still be guilty of others — see P5.

### P5 — where the kinematic proxy IS the cause

The 2,240.9 kg aggregate is real. **I predict the kinematic proxy does show up
in the field statistic** — the median destroyed-bay shard's 88.17 m and the
2,647 shards still over 1 m/s — because the field as a whole *is* comparable
to the car's mass, and because those shards are small enough to be swept
rather than knocked clear. But I predict it shows up as *carrying*, not as
launching: same H_B mechanism, aggregated.

### P6 — the fix

**I predict the effective fix is to withdraw the boundary condition when it
stops representing anything**, not to re-mass it. Specifically: removing the
car proxy's collision after its tail has cleared the wall plane by a stated
margin brings `MUL05_S02` below **10 m** of travel.

### P7 — what the fix costs the car

**Nothing measurable.** The car's transform is read from
`world/car_anim_measured.json` and keyed onto the proxy; if I do not make the
proxy dynamic, the authored trajectory is untouched, and the beat 2 / beat 4
seams must come back **bit-identical**, not merely close.

### P8 — the ending

**I predict the aperture survives.** The aperture is decided in the first ~50
sim frames, while the debris travel is decided over the following 1,500. I
predict f2978 stays within 1 percentage point of the 11.33 % changed > 8/255
and f2940's result holds.

### P9 — the one I expect to be wrong about

I expect at least one of P1–P8 to fail, and if I had to name it I would name
**P6's 10 m**: withdrawing the collider still leaves the segment whatever
speed it had when the collider went away, and a 2.5 kg aluminium box sliding
on concrete at μ = 0.45 from 16 m/s runs **29 m** before it stops. So 10 m may
be unreachable without a second mechanism, and if it is, I will say so and
name the second mechanism rather than move the number.

---

## R2-384 — the 89.79 m is a RIDE, not a launch: `MUL05_S02` spends 161 film frames on the car's airbox, dead centre of a camera locked 6 m off it

`sim/carproxy_probe.py` puts every body of a breach table into the CAR'S OWN
frame at every key. The car's pose is known independently of the solver — it is
read from `world/car_anim_measured.json`, the same file the sim keys the proxy
from — so "is this body being carried?" is answerable without a contact
manifold, which is just as well, because `bpy` exposes none.

**The event, with its first frame.** `MUL05_S02` in
`sim/out/breach_film_R2281_REBAKE.npz`:

| | |
|---|---|
| first movement > 0.05 m | **film f860.0** |
| the car's nose crosses x = 15.000 | **film f859.876** (`Car.impact_frame()`) |
| travel | **89.79 m**, d = (+89.63, −4.95, −1.90) |
| peak speed | **23.06 m/s at f1050** |
| keys inside the car's envelope | **125 of 260, one unbroken run f859 → f1017** |

**P1 lands to within 0.13 of a film frame.** The segment starts moving the
frame the nose arrives, which is what a member struck head-on does.

**And then it does not leave.** The trace, in the car's own coordinates:

| film | world x | z | speed | car-local x | car-local z | what |
|---|---|---|---|---|---|---|
| f862 | 15.77 | 1.98 | 10.34 | +2.29 | 1.96 | ahead of the nose |
| f890 | 19.18 | 1.22 | 12.71 | **+0.05** | 1.22 | arriving on the deck |
| f905 | 20.33 | 1.06 | 15.47 | −0.54 | 1.07 | **on the airbox** (`CAR_TOP_Z` = 0.992) |
| f1000 | 30.61 | 1.17 | 21.79 | −3.43 | 1.20 | sliding aft, still aboard |
| f1047 | 37.99 | 0.63 | 22.58 | −5.25 | 0.68 | past the tail (`TAIL_DX` = −2.678) |
| f1051 | 40.44 | **0.11** | 22.83 | −6.03 | 0.17 | on the ground |
| f1165 | 104.53 | 0.05 | **4.79** | −205.34 | 1.25 | still sliding |

**So the 89.79 m is two numbers, and only one of them is a defect:**

* **25.6 m of RIDE**, f890 → f1051, lying on the car's airbox and engine cover
  while the authored animation takes the car from 19.1 to 41.6 m and from 12.7
  to 22.8 m/s;
* **64.1 m of ordinary slide**, f1051 → f1165, at 3.33 m/s² — which is
  µ = 0.34 against `FRICTION_ALU` × concrete = 0.45 × 0.62 = 0.279 combined,
  i.e. plain sliding friction doing exactly what it should.

The slide is honest physics applied to a speed the segment should never have
had. **The ride is the defect**, and P2 is confirmed with room to spare: a
single contact with a plane moving at 16.398 m/s and `rest` 0.05 / 0.10 cannot
send a body above ≈18 m/s, and this one reaches 23.06.

**It is not a small defect and it is not off camera.** `sim/sagpx.py` through
the ONER track: at f905 the car projects at u = 1792, at f1000 at u = 1913, at
f1050 at u = 2136 — the camera is **locked on the car** at **6.0 to 12.9 m**
for the whole ride. A 2.5 kg aluminium mullion segment lies on the airbox of an
F1 car, in the middle of a 4K frame, six metres from the lens, for 161 film
frames of beat 3.

### The other two capture modes, and the worst travellers in the file

`sim/carproxy_census.py`, same method over all 3,948 bodies, envelope = the
convex union of `breachlib.car_proxy_parts()` inflated by 120 mm:

| | R6 SHIPPED | **R2281 RE-BAKE** |
|---|---|---|
| distance TRANSPORTED inside the car's envelope | 5,802 m | **40,587 m** |
| distance travelled free | 26,722 m | 199,427 m |
| transport share of all travel | 17.8 % | **16.9 %** |
| bodies carried > 1 m | 2,395 | **2,629** |
| — at the nose | 1,475 (19.4 kg) | 1,771 (29.4 kg) |
| — on the deck | 870 (26.2 kg) | **795 (151.3 kg)** |
| — under the floor | 37 (0.3 kg) | 46 (1.2 kg) |

**The transport SHARE is the same in both bakes.** The capture mechanism is not
something the corrected thresholds introduced — it is pre-existing, it is in
the shipped table too, and correcting the frame only gave it seven times as
much to carry. That is R2-290's "both bakes are wrong about the debris",
measured.

**The worst travellers are not on the deck, they are underneath it.** The
fifteen furthest-travelled bodies in the re-bake are all `GS_b05_004xx`, at
**204.96 – 205.01 m**, and their car-local position is **x = −1.72 m ± 0.01 m,
z ≈ 0.01 m, held for 236 consecutive keys (f859 → f1094)**. Ten millimetres of
scatter over 226 film frames is not sliding contact — it is a clamp. They are
wedged between the proxy's `floor` part and the slab and dragged at the car's
own speed to **43.58 m/s**.

**And the geometry says they had no way out.** `breachlib.car_proxy_parts()`
puts `floor` at **z 0.008 … 0.055** — an 8 mm ground clearance — while the
curtain wall's glass is **11.5 mm laminate**. Nothing lying on the slab in the
car's track can pass under that floor. It is a squeegee, and it is 1.52 m wide.


---

## R2-385 — the kinematic proxy is NOT what makes the debris travel, and no re-massing of it — dynamic, hybrid or otherwise — would have helped

My brief names the prime suspect and quotes `build_breach_sim.py`'s own
docstring for it: the proxy is `kinematic=True`, so it has infinite mass, "cannot
lose momentum", and "every joule the collision should have taken out of the car
is instead pumped into the field". The docstring's supporting figure is that the
shard field takes **up to 45 %** of the car's momentum.

**The 45 % is real as an aggregate and it is the wrong quantity for this
defect.** Here is the impedance the actual bodies see.

### The masses at the three contacts that produce the travel

| body | mass | mass ratio to the car's 798 kg |
|---|---|---|
| `MUL05_S02`, the 89.79 m mullion segment | 4.7 kg/m × 0.775 m × 0.72 = **2.623 kg** | **304 : 1** |
| `GS_b05_00434`, the 205.01 m underfloor shard | **0.0025 kg** | **319,000 : 1** |
| the whole deck-carried population | 151.3 kg | 5.3 : 1 |

### What the ride actually costs the car

`MUL05_S02` gains 12.707 → 22.829 m/s over the 1.149 s it lies on the deck.
That is an impulse of **26.54 N·s**, a mean force of **23.10 N**, and
**0.203 % of the car's 13,086 kg·m/s at the glass plane**. A dynamic 798 kg car
would have been slowed by **0.033 m/s** by the entire event and would have
carried the segment to within a third of a percent of the same place.

The underfloor case is worse for the hypothesis, not better. Dragging a 2.5 g
shard against µ = 0.32 × 0.62 needs **0.005 N**. The car's static weight alone
is **7,828 N**. The surplus is a factor of a million and a half. Whether the
thing pressing down has infinite mass or 798 kg is not a question the shard can
tell the difference between.

**And the deck ride is not even a mass phenomenon.** A body lying on a surface
is carried by friction, and the carrying force is µ·m_body·g — it contains the
carrier's mass nowhere at all. `FRICTION_ALU` × the proxy's 0.55 gives
2.428 m/s²; the segment is actually accelerating at **8.81 m/s²**, so the rest
comes from normal impacts on the airbox's and rear wing's vertical faces — and
those are bounded by the car's *momentum*, of which this costs 0.2 %.

**P4 is confirmed, and it was a prediction against my own brief.** A dynamic
proxy at the car's real mass and inertia would not have moved this defect. Nor
would a hybrid with a finite effective mass at the contact, unless that
effective mass were of the order of the *shard's* — 2.6 kg for the mullion
segment, 2.5 g for the glass — which is not "the car's real mass and inertia",
it is a car made of polystyrene.

**I therefore decline the fix my brief names first, and I am declining it on
the numbers rather than on cost.** It is also the fix that would have been
expensive: it puts a solver inside a keyed animation the rest of the film's
continuity is built on, and it would have bought nothing.

### Where the 45 % IS true, and what it is true about

`sim/carproxy_census.py` runs the momentum budget the docstring argues from,
Σm|v| over all 3,948 bodies against 798·v_car, in world time:

| film frame | field | car | field / car |
|---|---|---|---|
| f860 | 1,732 | 13,283 | 13.0 % |
| f880 | 3,290 | 13,392 | **24.6 %** |
| f950 | 3,851 | 17,308 | 22.2 % |
| **f1049 (peak)** | **6,510** | 23,392 | **27.8 %** |
| f1165 | 1,191 | 58,748 | 2.0 % |

So the field really does hold a quarter of the car's momentum during the
breach, and a car that were dynamic really would decelerate hard. **That is a
statement about the car, not about the debris** — and it is already recorded as
a DECISION rather than a consequence (R2-099): the film's car does not slow
down because its animation says so, and changing that is a change to
`anim/carrig.py`. What it is *not* is an explanation of why one mullion segment
went 89.79 m, because that segment is 0.2 % of the budget.

### Two predictions half-right, said plainly

* **P3** predicted the carrying signature and got the mechanism right — the
  acceleration runs for 276 sim frames beginning 130 sim frames after first
  contact, exactly the "not a launch" shape. Its second clause asked for **≥
  300 consecutive sim frames** inside the envelope and the measurement is
  **288**. Narrowly wrong, and I am not moving the number.
* **P5** predicted the kinematic proxy would still show up in the *field*
  statistic through the same carrying mechanism. It does — 40,587 m of
  transport — but the census also shows the transport SHARE is **17.8 % in the
  shipped table against 16.9 % in the re-bake**, i.e. the mechanism is
  unchanged and only the amount of loose debris grew. P5 is right about the
  mechanism and understated how old it is.


---

## R2-386 — two of Blender 5.2's three ways to switch a collider off do nothing, and the test that found it is four lines of scene

The fix I am going to argue for needs the car proxy to stop colliding partway
through a bake without its transform changing. Blender exposes three plausible
switches and the manual distinguishes none of them for a PASSIVE KINEMATIC
body, so `sim/tmp/test_rb_enabled.py` builds the smallest scene that can answer
it — an active cube resting on a passive kinematic plate — keys each switch to
turn off at frame 30, bakes 60 frames, and asks the only question that settles
it: **does the cube fall through?**

| keyed property | cube z at f5 / f25 / f31 / f59 | fell through |
|---|---|---|
| `rigid_body.enabled` | 2.26 / 2.20 / 2.20 / **2.20** | **no** |
| `rigid_body.kinematic` | 2.26 / 2.20 / 2.20 / **2.20** | **no** |
| `rigid_body.collision_collections` | 2.26 / 2.20 / 2.19 / **−4.87** | **YES** |

Only the collision collections are re-read per frame. So the withdrawal is a
move from collision collection 0 — which every other body in this scene is in,
by `objects_add`'s default — to collection 1, which nothing is in.

**And it costs two F-curves, not thirty-six.** The eighteen proxy parts already
share one action and one slot (that is the whole reason the car costs 6 curves
instead of 108), so the two boolean curves go on the same channelbag and every
part switches on the same frame *by construction* rather than by eighteen
correct writes.

**It also broke the gate that proves the car's curve is linear, and that is
worth recording.** `prove_linear()` walked every fcurve in the action and did
`ref = loc[:, fc.array_index] if fc.data_path == "location" else rot[:, ...]`,
so the two new CONSTANT boolean curves would have been read as *rotation*
curves, failed the LINEAR flag test, and refused the bake — with a message
about the car's curve that would have been true and completely misleading.
`_act_fcurves()` now filters to `location` / `rotation_euler` and **counts what
it excluded** into `linearity.non_motion_curves`, so the exclusion is in the
report rather than in the code's memory.

**A note on the smoke test that failed first.** The first version of the switch
test had the plate scaled after creation and the rigid body added before the
depsgraph had seen the scale, so Bullet built a 4 m box where the picture
showed a 0.2 m one, the cube started 2 m inside it, and all three switches
"failed" identically — by launching the cube upward at 72 m/s. Three identical
results is not three measurements; it is one bug. The fix was one
`view_layer.update()`.


---

## R2-387 — what the ending can and cannot cost, committed before the fix exists

The 11.33 % was measured on
`render/film14_breach_R2281_FRAMEONLY_DIAGNOSTIC_DO_NOT_SHIP.blend` — the
corrected FRAME on the SHIPPED glass — so the statistic that says the aperture
reads is a statistic about **where the frame's thirty released bodies end up**.
Three of them end up 89 m downrange. It is therefore a fair question whether
the ending was bought by the very bulldozer I am about to remove, and it has to
be answered *before* the answer is available.

`sim/sagpx.py`, projecting each released frame body's RESTING position through
the ONER track, against `wallstats.py`'s own `WOUND_bridged` rectangle
(u 1891–1949, v 1041–1120):

| body | travel | rests at x | u, v at f2978 | in the wound box |
|---|---|---|---|---|
| `MUL05_S00 / S01 / S02` (+plates) | 88.3 / 89.0 / 89.8 m | 103–105 | 1800–1805, **1436–1445** | no |
| `MUL05_S03 / S04` | 13.3 / 12.7 m | 27–28 | 1902–1904, 1157–1160 | no |
| `MUL05_S05 / S06 / S07` | 7.6 / 7.6 / 7.6 m | 19.7–21.3 | 1922–1924, 1134–1139 | no |
| `TRN_z0_b04 / b05` | 53.1 / 69.8 m | 68 / 85 | 1914 / 1941, 1300 / 1364 | no |
| `TRN_z1_b04 / b05`, `TRN_z2_b04 / b05` | 5.5–8.6 m | 18.0–22.8 | 1894–1950, 1128–1145 | no |

**At f2978, zero of the thirty released frame bodies rest inside the wound
box.** The ground plane at the wall itself projects to v 1119 at f2978 — one
pixel above the box's lower edge — so *anything* that comes to rest on the
apron beyond x ≈ 15.5 m is below the measured region. **The 11.33 % was not
bought by the 89 m.** Had those three segments stopped at 30 m they would have
projected at v ≈ 1167, still forty-seven pixels clear.

**f2940 is the tighter frame and that is where the risk is.** Its box bottom
corresponds to ground at x ≈ 19.6 m, and **two bodies already rest inside it**
— `TRN_z2_b04` and its pressure plate, at x = 18.05, u 1909, v 1116. So the
f2940 result is already tolerant of released members lying in the lower
aperture, which is what R2-294 predicted and got right.

### The prediction

**P10.** The fix moves `MUL05_S00/S01/S02` from x ≈ 104 to somewhere in
x 25–50, and moves nothing else in the frame by more than 3 m. **f2978's
11.33 % holds to within 1.5 percentage points and `grid_contrast` stays under
0.012.** f2940's result holds.

**P11.** The number at risk is **f2940, not f2978**, and the mechanism if it
fails is *more* frame bodies coming to rest inside x < 19.6 m with |y| < 2.9 m
— i.e. the fix stopping them too early rather than too late. If f2940 moves and
f2978 does not, that is the reason, and I will report the resting x of every
released member rather than argue about the pixels.

## R2-401 — the driver is 92 % helmet, and that is the whole of the finding

`tools/r2401_part_mask.py` runs `driver_containment`'s instrument once per
GROUP: every car mesh `is_holdout`, `film_transparent`, one sample, 0.01 px
filter, opaque `material_override`, so alpha is 1 exactly where an unoccluded
DRIVER surface is frontmost. R2-241 measured how BIG the driver is. It did not
measure WHAT is on screen, and the whole question turns on that.

At **frame 2635**, the largest cockpit in the film with the driver present
(2.34 m, 80.4° above the aperture plane, 1,459 px/m):

| group | own pass | contribution to the rendered mask |
|---|---:|---:|
| all `DRV_*` that render | 172,468 px | — |
| helmet + balaclava | 157,999 | **157,999  (91.6 %)** |
| gloves | 11,157 | **11,157  (6.5 %)** |
| suit + HANS + harness + extras | 40,392 | **3,312  (1.9 %)** |

The torso's own pass is 40,392 px and only 3,312 of them survive into the
combined mask, because the helmet is in front of the rest of him. At frame
2632 it is **1,539 px of 132,155 — 1.2 %**.

Controls held. NEGATIVE: an all-hidden group returns **0 px** at both frames.
POSITIVE: the groups sum to MORE than the whole (209,548 vs 172,468 at f2635),
and the excess is exactly the mutual occlusion, so the groups do cover the
driver rather than silently missing part of him. The `all` figure at f2632 is
**132,155 px**, identical to R2-246's independently-run number.

**So the observation that started this is real.** The volume between the wheel
and the helmet is not a driver reading dark; it is the car's own seat, liner
and harness, with 1.9 % of a driver in front of it. `render/r2401/hollow_ab.png`
is the driver-present and driver-absent crops of that volume side by side and
the two are nearly identical.

## R2-402 — but "0.20 m below the cockpit rim" measures a joint centre against a rim 0.63 m in front of it

The number that opened this investigation is **0.207 m**, and it is
`docs/driver_placement.json`'s `anchors_local['shoulder_l']` z against
`CI_seal`'s **global maximum** z. Both halves are the wrong thing.

* `anchors_local` is `driver_figure`'s SKELETON, and it is also the module's
  PREDICTION — written to the report before `place_driver`'s −16.405 mm crown
  correction translated every emitted object. The glenohumeral joint centre is
  inside the body.
* `CI_seal`'s max z (0.7298) occurs at **x = +0.626**, at the scuttle. The rim
  directly outboard of the shoulder is lower and falls away forward — measured
  by `tools/r2401_cockpit_fit.py` in 50 mm slices: 0.6689 at x −0.15, 0.6645 at
  −0.10, **0.6310 at −0.05**, 0.6052 at +0.50.

Measured on the EMITTED MESH instead — the highest `DRV_Suit` vertex over each
deltoid, |y| 0.13..0.26, x −0.15..0.10:

| | z | vs CI_seal max 0.7298 | vs the rail beside it, 0.6310 |
|---|---:|---:|---:|
| suit shoulder, as built | **0.6003** | **0.1294 below** | 0.0307 below |
| the joint anchor it was read from | 0.5225 | 0.2073 below | 0.1085 below |

The gap between the two rows is **0.078 m**, which is the flesh over the joint —
a deltoid radius, and anatomically what it should be.

**On the surface datum the shoulder is 0.129 m below the rim, i.e. inside the
0.10–0.15 the reference is quoted as showing.** The defect is a datum mismatch
of 78 mm between a skeleton anchor and a surface reference.

This does not make R2-401 go away — 1.9 % is 1.9 % — but it does mean the
shoulder line is not the thing that is wrong, and moving it is moving something
that is already where it should be.

## R2-403 — there is no halo over the driver's head, and no engine cover either

`solve_hpoint`'s fourth fit check is `crown > halo_top + 0.01` → "the head is
outside the survival cell", against `halo_assembly_HoopTube`'s global max z of
0.8825. `tools/r2401_headroom.py` slices that tube along x:

| x | z range | nearest \|y\| | verts on the centreline |
|---:|---|---:|---:|
| −0.05 (the crown's x) | 0.6411 .. 0.7698 | **0.2892** | **0** |
| +0.00 | 0.7188 .. 0.7882 | 0.3252 | 0 |
| +0.85 | 0.8329 .. 0.8816 | 0.0026 | 1117 |
| +0.90 | 0.8366 .. 0.8825 | 0.0028 | 1097 |

The halo apex is the **front pillar junction at x +0.90**, 0.95 m ahead of the
crown. Over the head the halo is 0.29 m outboard and BELOW the crown. So the
check compares the helmet's height against a bar that is nowhere near it.

And `tools/r2401_cockpit_fit.py` fires 4,000 rays straight up off the helmet's
upper cap into a BVH of 176 car objects, 4,078,475 triangles: **0 of 4,000 hit
anything within 3 m.** There is nothing above the helmet at all. The stated
"0.054 m of headroom to the engine cover" is not a clearance; it is the gap up
to the bodywork's own silhouette line behind the head — `EC_shell` 0.9335,
`MB_chassis_cockpit` 0.9262 — and the true ceiling is the roll hoop
**`EC_hoop`, top 0.9529, i.e. 0.076 m** above the crown, not 0.054.

Not fixed here, because it changes a shipping gate's semantics: the fourth fit
check should read against `EC_hoop`, which is the object that is actually over
the driver.

## R2-404 — the window in which any of this can be seen is 25 frames

`tools/r2401_cockpit_sweep.py` projects the eight corners of the `CI_seal`
aperture box plus the driver landmarks through `render/film14_path.json` at
`world/car_anim_car.json`'s own per-frame car transform, for all 2,978 frames.
Frames counted only if ≥ 6 of 8 aperture corners land on the 3840 × 2160 frame
AND f ≥ 580, `place_driver --appear`, before which he is keyed hidden.

**2,201 frames (91.7 s) qualify.** Of those:

| helmet size | frames | seconds |
|---|---:|---:|
| ≥ 100 px | 356 | 14.8 |
| ≥ 200 px | 46 | 1.9 |
| ≥ 300 px | 15 | 0.6 |

and what a candidate correction is worth in pixels, over those 2,201 frames:

| move | median | p90 | max |
|---|---:|---:|---:|
| +54 mm | **6.9 px** | 28.9 | **78.8** |
| +77 mm (the datum gap of R2-402) | 9.9 | 41.2 | 112.3 |
| +135 mm (chest to the aperture's lower edge) | 17.3 | 72.2 | 197.0 |
| +229 mm (hip onto round 1's seat pan) | 29.3 | 122.5 | 334.1 |

The maxima all fall in one run, **f2628–f2652 — 25 frames, 1.04 second** — which
carries 6.5 % of the driver's total projected-size-time. Everywhere else the
whole argument is worth single-digit pixels.

## R2-405 — the first cut of that sweep nominated four frames where the cockpit is off screen

It asked whether the CROWN projected inside the frame plus a 200 px margin, and
returned f530–533 as the four largest cockpits in the film at **4,940 px/m**.
They are not. At f530 the camera is 1.27 m off the car and the aperture's eight
corners project to x 2,548..7,304: **one of eight** lands on a 3,840 px frame
and the crown is at x 3,591, off the right edge.

It was caught because `place_driver.figure_offscreen` had already measured
frames 448–530 as an OFF-SCREEN run, and the two disagreed. A single landmark
plus a generous margin is not an in-frame test; the aperture box is. Fixed, and
the fix is why R2-404's table is the real one.

## R2-406 — the +54 mm raise, built and rendered: it buys 6× the torso and fails containment

`tools/place_driver.py` gains `--hip-raise` (default 0.0, no behaviour change).
It lifts the H-point only; `wheel_rel = wheel_centre − H` is computed AFTER, so
the module **re-solves the arms down to the car's own grips** rather than the
gloves floating off them, which a rigid translation of the built figure would
do. Measured on the artefact: gloves **0.1 mm and 0.0 mm** from `SW_GripL/R`,
car witness **0 of 70** samples changed, install tracking 0.00000 m with the
2.518 m explode offset still seen.

`world/car_anim_driver_R2401_EXPERIMENT_raise54.blend`, against the shipping
build, at 4K/256 samples on the 5090:

| | base | +54 mm | |
|---|---:|---:|---|
| f2635 all driver px | 172,468 | 202,500 | +17.4 % |
| f2635 **torso visible** | 3,312 | 21,171 | **× 6.39** |
| f2632 torso visible | 1,539 | 9,417 | × 6.12 |
| suit shoulder z | 0.6003 | 0.6567 | |
| … below `CI_seal` max | **0.1294** | **0.0731** | **out of the 0.10–0.15 band** |
| helmet crown z | 0.8770 | 0.9310 | 0.022 under `EC_hoop` |

So it more than answers "how much of the gap does it close": on the joint datum
it takes 0.207 → 0.153, right onto the band's edge; on the SURFACE datum, which
R2-402 shows is the right one, it takes 0.129 → 0.073 and **overshoots the band
in the other direction.**

And then it fails the gate. `tools/driver_containment.py`, unmodified, on the
raised blend:

| frame | base: px / outside | +54 mm: px / outside | |
|---|---:|---:|---|
| 2635 | 172,468 / **0** | 202,500 / **208** | FAIL |
| 2632 | 132,155 / **0** | 155,204 / **13** | FAIL |
| 2625 | 23,441 / 0 | 32,068 / 0 | OK |
| 828 | 17,004 / 0 | 24,871 / 0 | OK |
| 700 | 15,978 / 0 | 22,297 / **6** | FAIL |

Both columns are the same unmodified instrument, run in the same session shape,
with the driver-absent control reading 0 px on all ten passes. The shipping
build reads **0 outside on all five frames including f2635**, which R2-249 had
never tested. The 208 px are
visible without the mask: in `render/r2401/raise54_f2635_crop.png` the shoulder
and HANS come through the monocoque skin as **gold wedges lying on the bodywork
outboard of the rim**, one above the cockpit on the engine-cover shoulder and
one below it on the tub flank. `render/r2401/overlay_ab_f2635.png` outlines
them.

That is the trade in one line: **+17,859 px of torso inside the cockpit, bought
with 208 px of driver on the outside of the car.**

## R2-407 — and it does not fix the thing it was supposed to fix

The complaint is the volume between the wheel and the helmet. The chest is at
z 0.450. The cockpit aperture's LOWER edge — `CI_seal` min z — is **0.5849**.
The chest is 0.135 m below the hole it would have to be seen through, so at
+54 mm it is at 0.504 and still 0.081 m below it. Compare
`render/r2401/base_f2635_crop.png` with `raise54_f2635_crop.png`: that volume is
the same dark tub in both. What the raise moved was the helmet and the shoulder
tips, not the chest.

To put the chest in the aperture takes **+135 mm**, at which the crown reaches
1.012 — **0.059 m above the roll hoop `EC_hoop`**, i.e. the driver's head
standing proud of the car. There is no height at which this figure's torso is
visible through this car's cockpit opening and his head is still inside the car.

A smaller raise was not built. It is not motivated: on the surface datum every
millimetre of raise moves the shoulder further out of the reference band, and
the leak is caused by the shoulders reaching the tub sides, which begins as soon
as they rise.

## R2-408 — what supplying corrected cockpit geometry at apply time would actually cost

`sim/apply_breach.py`'s R3 is the precedent and it is worth reading precisely:
it deletes **ten `GW_Right_Glass_*` objects of four vertices each** — zero
thickness planes on x = 15.000, which cannot be glass at any distance — and
supplies ten laminated panes. Un-animated, one material, no fasteners, no
seams, and the module that supplies them owns the breach anyway.

The cockpit is not that. Measured on `world/car_anim.blend`:

* the `CI_*`/`MB_*` cluster is **32 objects, 1,120,084 polygons, 24.4 % of the
  car's 4,598,601**, across 8 procedural materials;
* **all 32 are animated** — every one carries beat 1's explode path, and
  `place_driver` exists in its current form because a single action datablock
  shared with `CI_seat` rewrote the car's own assembly flight (R2-245);
* `MB_chassis_cockpit` alone is 182,225 polygons and is the surface the halo
  mounts, the seal, the fasteners and the imperfection pass all land on.

And there is no room underneath. To put the hip on the seat pan the pan and the
cell floor drop **0.229 m**. `MB_cell_floor`'s underside is at 0.3860 and
`MB_chassis_cockpit`'s lowest surface at 0.3704; the plank is at 0.0400, the
skids at 0.0389, `MB_underpan` spans **0.042 .. 0.160**. The corrected floor
would land at 0.157 — inside the underpan — so the underpan, plank, skids and
plank bolts move too, and the tub sides and the sidepods that meet them follow.
Raising the opening 0.13 m instead redraws the car's silhouette and the halo
mounts with it.

All of that lands on the object beat 1 is a 33-second close pass over.
Measured from the camera path: **189 frames (7.9 s) with the camera inside 2.0 m
of the cockpit, 323 frames (13.5 s) inside 3.0 m**, and a peak scale of
**70 px per millimetre** at f556, 0.09 m off the skin. New geometry would have
to match round 1's weave, rivet pitch and seam lines at that scale, hand-built,
with no repeated assets — for a defect worth 6.9 px at the median frame.

## R2-409 — RECOMMENDATION: accept it

**Accept.** Ship `world/car_anim_driver.blend` as it stands.

Why the others lose:

* **Raise into the headroom — loses on the pictures and on the gate.** It does
  not fill the hollow (R2-407): the chest cannot reach the aperture. It moves
  the shoulder OUT of the reference band on the datum that measures a surface
  against the rim above it (R2-402/R2-406). It puts 208 px of driver through the
  monocoque at the film's largest cockpit frame and fails
  `tools/driver_containment.py` at 3 of 5 frames. And 208 px of gold on the
  bodywork is a defect a viewer can point at, where 1.9 % vs 10.5 % of torso
  inside a dark cockpit is not.
* **Supply corrected geometry at apply time — loses on cost and on risk.** It is
  1.12 M polygons and 32 animated objects across 24.4 % of the car, it has to
  displace the underpan and the plank to find the 0.229 m, and it lands on the
  hero object of a 33-second close pass that peaks at 70 px/mm. `apply_breach`'s
  precedent replaced forty vertices that could not be right at any distance;
  this would replace a quarter of the car to move something by 6.9 px at the
  median frame. In a one-take film with zero cuts, every seam of it has to hold
  for 2,978 frames.
* **Accept — costs nothing and is defensible from the frames.**
  `render/r2401/base_f2635_crop.png` is the worst case: 2.34 m, 80° above the
  aperture, the largest the cockpit ever gets with a driver in it. The helmet is
  seated, the hands are on the wheel (`overlay_base_f2635.png` outlines both
  gloves in blue at the rim), the shoulder line sits 0.129 m under the rim
  which is where reference puts it, and the cockpit reads as a cockpit. The
  volume forward of the helmet is dark because it is the seat and the liner of
  a car whose cockpit sides are above its driver's shoulders — which is what a
  modern F1 cockpit looks like from above.

What IS worth doing, and is cheap: **R2-403's fit check**. `solve_hpoint`'s
halo test is comparing the crown against a bar 0.95 m forward with no geometry
over the head. It happens to pass on the shipping build, so it is not urgent,
but it is a gate that is not measuring what it says it measures, and the next
person to move the driver will be stopped or waved through by the wrong number.
Point it at `EC_hoop`.

## R2-410 — what I could not confirm

* **The reference band itself.** "Reference shows 0.10–0.15" was given to me,
  not measured here, and no external reference may be fetched. Everything above
  is conditional on it. If the band is meant against the rim rail directly
  outboard of the shoulder rather than the cockpit's highest line, the shipping
  build reads 0.031 and is too HIGH, and the raise makes that worse, not better
  — the recommendation is unchanged either way, which is why I have not chased
  it further.
* **A raise smaller than 54 mm was not built** (R2-407 gives the reason).
* **`--fit-warn-only`** is new and refuses unless `--out` contains
  `EXPERIMENT`. It has been exercised once, on the one blend it was written for.
* **The look scene is not the film.** `tools/build_driver_look.py` ships the
  car, the driver, the contract sun and sky — no track, no grandstands, no
  showroom — so the visor mirrors a cleaner sky than the film will. That is the
  same scene the R2-241..250 evidence was shot in, so the A/B is like-for-like,
  but neither is the shipping frame.
* **f2635 was never in `driver_containment`'s frame list** before this block.
  R2-249's 0-outside result was measured at 2632/2625/828/700/1200/2100. The
  base build has now been run at 2635 and reads 0 outside there too —
  `docs/r2401_containment_base.json`. Nothing else in the shipping build was
  re-verified; this block changed no shipping artefact.


## Artefacts

    tools/r2401_cockpit_fit.py       geometry off the emitted mesh + the ceiling BVH
    tools/r2401_headroom.py          what is above and behind the head; the halo profile
    tools/r2401_cockpit_sweep.py     px/m and camera elevation, all 2,978 frames
    tools/r2401_part_mask.py         the helmet / arms / torso pixel split
    tools/place_driver.py            + --hip-raise, + --fit-warn-only  (defaults unchanged)

    docs/r2401_cockpit_fit.json      docs/r2401_cockpit_fit_raise54.json
    docs/r2401_headroom.json         docs/r2401_cockpit_sweep.json
    docs/r2401_part_mask_base.json   docs/r2401_part_mask_raise54.json
    docs/r2401_placement_raise54.json
    docs/r2401_containment_base.json docs/r2401_containment_raise54.json

    render/r2401/base_f2635_crop.png     render/r2401/raise54_f2635_crop.png
    render/r2401/ab_f2635_full.png       render/r2401/ab_f2632_full.png
    render/r2401/overlay_ab_f2635.png    render/r2401/overlay_ab_f2632.png
    render/r2401/silhouette_ab_f2635.png render/r2401/hollow_ab.png

    world/car_anim_driver_R2401_EXPERIMENT_raise54.blend   NOT FOR SHIPPING
