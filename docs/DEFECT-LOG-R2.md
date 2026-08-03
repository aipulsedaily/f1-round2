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
