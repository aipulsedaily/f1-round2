# STAGING — R2-1541 to R2-1600 — the car at hero scale (R2-1142 answered)

Numbers to be assigned by the log's owner. **`docs/DEFECT-LOG-R2.md` not edited.**

R2-1142 records the client's read of `r2beat1_v2_000599.png` and lists six
absences on the car, plus a seventh on the light. **Five of the six absences do
not exist.** Every one of the named features is authored, at real millimetre
sizes, and renders correctly when it is given enough pixels. What is wrong is
**how the car is delivered** — and after this pass measured the delivered blend
rather than the source that builds it, the remedy is **one constant and one
lamp**, not a rebuild:

* **`CarbonFibre`'s weave is 1.6535 mm, not the 5 mm its own docstring specifies**
  — 0.87 px at delivery, the only car material in `film17_breach.blend` carrying
  no round-2 fix. `Mapping.Scale 190.0 → 62.832`.
* **The light was optimised until nothing clipped**, and the specular that
  describes a curve went with it. Scale-free, so it survives every other fix.
* Two claims this pass first made about the paint are **WITHDRAWN** — car paint v5
  and the imperfection layer are both in the delivered blend. See the withdrawal
  below; the error is worth more than the claim was.

**The instrument the client asked for is the one that settles it**, and it
overturned my own first hypothesis as well as theirs.

---

## R2-15xx — THE JUDGED FRAME IS 1280×720 AT 64 SAMPLES. The spec is 3840×2160 at 512

`out2/seq/r2beat1_v2/` — all 793 frames, `magick identify` and the broker's own
job rows (`state2/broker.db`, jobs `5dcd5edad9b1` … `2744aa4b659e`):

```
"resolution": [1280, 720], "samples": 64
```

against a delivery spec of 3840×2160 / 512. **Nine times fewer pixels and eight
times fewer samples.** This is not a defect in the sequence — `docs/RENDER-LADDER.md`
requires exactly this pass, and its own table says a 4K still and a sequence catch
**different** defect classes. The defect is that a question from the still column
("carbon weave, a bevel, a decal edge, a material that reads as plastic" — the
ladder's own words) was answered from the sequence column.

**The resolvable band, from the live camera** (`render/film17_path.json`, declared
in `docs/LIVE-CAMERA.md`), weighted by the car's own frame coverage so that frames
where the car is 2 % of frame width cannot drag the median:

| beat | frames | car, median | mm of car per 4K px | smallest readable |
|---|---|---|---|---|
| **1_assembly** | **792** | **4,213 px** | **1.36** | **2.7 mm** |
| **2_launch** | **72** | **3,859 px** | **1.48** | **3.0 mm** |
| 3_breach | 192 | 710 px | 8.06 | 16.1 mm |
| 4_transit | 134 | 216 px | 26.54 | 53.1 mm |
| 5_lap | **1,524** | **82 px** | **70.18** | 140.4 mm |
| 6_ending | 264 | **40 px** | 143.58 | 287.2 mm |

Two corrections to the brief's own scoping, both in the direction that raises the
value of beat 1: the car's weighted median coverage in beat 1 is **1.097 of frame
width, not 0.60** — it is *larger than the frame* more than half the time. And the
lap holds it at **2.1 %, not 3–5 %**, the ending at **40 px, not 230**.

**At f599 specifically** — range 7.38 m, lens 36.3 mm, car 0.782 of frame width:

| feature | size | 4K px | 720p px | |
|---|---|---|---|---|
| panel gap / shutline | 4 mm | **2.10** | 0.70 | invisible at 720p |
| carbon twill cell | 5 mm | **2.63** | 0.88 | invisible at 720p |
| rivet / Dzus head | 8 mm | **4.20** | 1.40 | invisible at 720p |
| panel-line groove depth cue | 3 mm | 1.58 | 0.53 | **below the band in both — do not build** |
| tyre sidewall lettering | 25 mm | 13.13 | 4.38 | readable in both |
| front wing flap gap | 120 mm | 63.00 | 21.00 | readable in both |
| diffuser vane / floor fence | 300 mm | 157.50 | 52.50 | readable in both |

**Three of the six named absences are physically unresolvable in the medium they
were judged in.** A 4 mm panel gap at 0.70 px is not a modelling failure.

### And the frame proves it

`f599` re-rendered at 3840×2160 (broker `b0a8ebd22821`, 74.7 s). At 1:1 the same
car carries: shutlines down the sidepod and engine cover, **rows of Dzus
quarter-turn fasteners along every panel edge**, the sidepod louvre bank resolved
blade by blade, brake caliper hardware with anodised detail, wheel-nut geometry,
suspension pickups, cockpit interior, harness, and the four front-wing elements
with endplate, strakes, cascades and red-anodised flap adjusters.

At **zoom 4.0** (`56f35a1977b4`, 0.48 mm/px) **the carbon weave is plainly there**
on the halo and the cockpit rim. It renders. It is simply three times too fine to
survive to delivery — which is R2-15xx below.

---

## R2-15xx — THE MODEL IS NOT THE CEILING. 616 meshes, 4.80 M evaluated polys, every named feature authored

Source audit of the 15 live modules (`build/s08_assemble.py:35–51,77–86` — note
`s04_car.py` is **dead code**, `include_monocoque` is False and `build_body()` is
never called):

| claim in R2-1142 | source | authored at |
|---|---|---|
| "no panel separation" | `monocoque_b.py:217`, `engine_cover.py:68` | **`GAP = 1.8 mm`** and **`3.2 mm`**, 8 panel groups, bonded backing strips 9 mm and 11.5 mm below the skin, 118 Dzus on the cover alone |
| " " | `nose_assembly.py:143` | recessed seam troughs **1.9 × 1.05 mm**, 2 longitudinal + 2 transverse runs a side |
| " " | `sidepod.py:205–222` | panel-joint grooves **2.6 / 2.4 / 2.0 mm** deep, 72 Dzus a side, 52 rivets |
| "front wing is a plain bent sheet" | `front_wing.py:48–70` | **4 lofted elements**, slot gaps **13–20 mm**, 120 objects, **331,756 polys**; 13 mm endplates, footplate, 4 strakes/side, 2 cascades/side, **flap adjusters** (27 mm boss, 11.6 mm socket), gurney, **2 mounting pylons** |
| "underfloor is a flat grey slab" | `floor_diffuser.py` | 10 objects, **242,772 polys**: 10.6 mm plank, **8 titanium skids** 1.1 mm proud, 86 countersunk fasteners, **4 fences/side**, **8 diffuser vanes** |
| "tyres have no sidewall" | `wheel_tyre.py:486–586` | a dedicated `Lettering` object per corner: "APEX" ×3 at 14 mm cap / **0.85 mm relief**, size mark, compound mark, 3 batch codes, plus **mould vent pips**, 0.40 mm parting flash, rim-protector rib, 0.90 mm compound-band relief |
| "no carbon weave" | `s03_materials.py:258` | authored — **and mis-pitched by 3.02×, see below** |

`wheel_tyre_*_Lettering` and `*_VentPips` are in `docs/explode_plan.json`, so the
objects are in the shipped `CAR` collection, not merely in the source.

**No unwired bump anywhere in the live car.** All eight `ShaderNodeBump` in
`s03_materials.py` terminate in a `C.wire(..., "Normal", b, "Normal")`, and
`common.wire()` resolves by name, so the 5.2 socket-index move cannot bite. The
14 dead stacks were world/item modules, not the car.

**I decline to model anything.** There is nothing in the client's list to build.

---

## R2-15xx — `CarbonFibre`'s weave is 1.6535 mm, not the 5 mm its own docstring specifies, and round 1 diagnosed this exact symptom before mis-fixing it

`s03_materials.py::_planar_weave` (line 233) puts a `Mapping` **Scale 190** in
front of a `ShaderNodeTexWave` at **Scale 1.0**. Blender's Wave node multiplies
its coordinate by 20 internally, so the emitted period is

```
2*pi / 20 / 190  =  1.6535 mm      (604.8 periods/m, not the intended 190)
```

The intent is stated in `carbon_fibre()`'s own docstring at line 387: *"Real 2×2
twill is about 5 mm, i.e. ~190 repeats per metre."* **The number is right and the
node does not deliver it.** The corrected `Mapping.Scale` is **62.832**.

**And round 1 already found this defect and mis-fixed it.** The same docstring,
lines 383–388:

> D081: the weave was mapped at 760 repeats per metre — a 1.3 mm twill. **That is
> far below a pixel at any sane render scale, so it averaged to nothing and every
> carbon panel behaved as a dead-flat mirror under a 0.045-roughness coat: flat
> endplates caught the cove and rendered as white plastic.**

The condemned value was 1.3 mm. The "fixed" value is **1.6535 mm** — a 27 %
improvement on a defect that needed 4×. **The predicted symptom is verbatim the
client's second complaint**, thirteen months later: *"the front wing is a plain
white bent sheet."* It is not a bent sheet; it is 331,756 polys of correct
aerofoil reading as white plastic for exactly the reason the docstring names.

Against the resolvable band, at 4K (the repo's own threshold is ~2.5 px — below
that a feature "is not a feature, it is a flat tone with noise on it",
`tools/cockpit_surface.py:15–17`):

| | 1.6535 mm (shipped) | 5.000 mm (fixed) |
|---|---|---|
| f599, the judged frame | **0.87 px** | **2.63 px** |
| beat 1 weighted median | **1.22 px** | **3.68 px** |
| beat 1 p90, closest 10 % | 2.85 px | 8.62 px |

**This is the resolvable-band law the client asked me to apply to the car, and it
is the finding.** A detail authored outside the band is invisible however correct
it is — and this one is correct, wired, triplanar, grazing-faded, and 3.02× outside
the band on **the front wing, rear wing, barge boards, nose, engine cover, sidepod
and halo.**

**Why it was missed twice:** `world/car_paint.py` fixed the identical bug on
`LiveryPaint` (`WEAVE_PITCH_M = 0.0050`, built analytically with Math nodes so the
pitch is exact) and `tools/cockpit_surface.py` fixed it on `CarbonMatte`/`SuedeGrip`.
Each targets one material by name. **`CarbonFibre` — the largest carbon area on the
car — is in neither target list.** Two agents fixed the same bug on either side of it.

---

## R2-15xx — WITHDRAWN: the paint IS fixed in the delivered blend, and I read a linked socket's dead default

**This section previously claimed the shipped bodywork runs `Metallic = 0.62`
over a 0.0121 base — "96 % room reflection" — and that `LIVERY_TIER = "B"` gates
its weave off. Both claims are WRONG and are withdrawn.** They were read from
`build/s03_materials.py` source and from `inputs["Metallic"].default_value`, and
**the socket is linked, so its default is dead data.**

Measured on `render/film17_breach.blend` itself, opened with
`bpy.data.libraries.load(link=True)` — the 7.98 GB file interrogates fine locally
in link mode, about 2 minutes, no OOM, **no GPU spent**:

| | shipped in film17 |
|---|---|
| `LiveryPaint` `Metallic` | default 0.62, **LINKED** through `R2CP_085_metallic -> paint`, a MULTIPLY by **0.16129031777381897** = `0.10/0.62` exactly. **Effective metallic 0.10.** |
| `Coat Roughness` | **0.055** (round 1 ships 0.022) |
| `Coat Tint` | **0.960 / 0.975 / 1.000** (round 1 ships 0.68 / 0.82 / 0.90) |
| `R2CP_VERSION` | **5** |
| nodes / `R2CP_*` / `R2IMP_*` | **239 / 94 / 25** |
| `ShaderNodeGroup` | **1**, `R2IMP_000` → `R2_Imperfection` |

`world/car_paint.py:826–833` applies the fix deliberately as a **scale on the
existing link**, not as a new constant, so the nose's carbon-dissolve region that
round 1 drives to metallic 0 still reaches 0. **Any check that reads
`default_value` on that socket concludes "round 1" and is wrong.** That is the trap
and it caught this pass.

**So R2-1142's "the paint work landed" is TRUE**, and `docs/NEXT-REBUILD.md` line 7
("Car paint v5 + imperfections — landed in SOURCE, in no film blend") is **stale**:
it describes `render/film14_breach_r6.blend` (Aug 4 02:54), built before
`world/car_anim_driver.blend` was repainted (Aug 4 19:51). The paint is baked into
`world/R2829_car_anim_driver.blend` and `chain5.sh` inherits it — **the absence of
a carpaint stage from that script is not evidence of absence**, which is what this
pass first read it as. 21 materials carry markers; 386 `R2IMP_*` and 94 `R2CP_*`.

**`LIVERY_TIER` is likewise not the live control** — car_paint.py v5 rebuilds the
weave into `LiveryPaint` analytically at `WEAVE_PITCH_M = 0.0050`
(`R2CP_081_weave through paint` is in the shipped chain), downstream of the tier.

### And this leaves exactly one unfixed material, which is the one above

`CarbonFibre` in `film17_breach.blend`, **measured, not inferred**: 68 nodes,
**0 `R2CP_*`**, no `R2CP_VERSION`, and all three `ShaderNodeMapping` nodes feeding
its six `TexWave` nodes at **`Scale = 190.0`**. The 62.832 / 5.0 mm correction is
**not in the delivered blend.** `car_paint.py` owns `LiveryPaint` only, by design.

**The prescription therefore collapses to two items: one constant and one lamp.**

### Two side findings from the same probe, outside this question

* **Ten car materials exist twice in film17 as `.001` twins** — CarbonFibre,
  CarbonCeramic, TyreRubber, WheelRim, Titanium, SteelFastener, MatteBlack,
  AnodisedRed — plus a second `R2_Imperfection` node group. `LiveryPaint` does
  **not** have a twin, and `R2829_car_anim_driver.blend` has exactly one of each.
  Something in the film assembly is bringing in a second copy of part of the car.
  The twins are value-identical so nothing above changes, but **this may mean
  duplicate geometry in the shot** and should be chased.
* `CarbonFibre`'s `Coat Roughness` base is **0.16** against `LiveryPaint`'s 0.055.
  Worth confirming that is intended rather than a leftover.

---

## R2-15xx — the instrument lesson, because this pass made the error twice in one direction

Both withdrawn claims came from **reading the source that builds a thing instead
of the artefact that shipped**, and both flattered the finding:

* `Metallic = 0.62` is in `s03_materials.py` and in the shipped socket's
  `default_value`, and is **not** what the shipped material evaluates to, because
  the socket is linked. **A default on a linked socket is dead data**, and nothing
  in a node dump distinguishes "this is the value" from "this is what the value
  would be if anything read it."
* `chain5.sh` has no carpaint stage, which reads as "the paint did not land" and
  means only that the paint landed **upstream of the script I was reading**.

This is the same shape as `carproxy_census.py` reporting a correct value about
the wrong volume (R2-4xx) and `grid_contrast` measuring rows that could not
contain a member (R2-400). **The number was right and the object it described was
not the one being asked about.** `docs/NEXT-REBUILD.md:7` should be corrected or
dated — it is a true statement about `film14_breach_r6.blend` presented as a
standing fact about the film.

**The method that settled it, and it is cheap enough to be routine:**
`bpy.data.libraries.load(link=True)` opens the 7.98 GB film blend on this 11 GB
box in about two minutes without instantiating the scene — materials and node
groups are fully readable at a fraction of the memory. **No GPU, no cost.** Probe
kept at the session scratchpad's `probe.py`. Every "is X in the shipped blend"
question on this project can be answered this way instead of argued from source.

---

## R2-15xx — the light was optimised to stop clipping and the specular went with it

Scale-free, so it survives every fix above, and the client is right about it.

`build/s05_lighting_v2.py::build_three_point` — the rig exists (Key, Fill, Rim,
Kick), so "no key, no rim" is wrong as a source claim. **But every source in it was
deliberately enlarged until nothing clipped**, and the file says so:

| lamp | size | area | note in source |
|---|---|---|---|
| Key | 4.6 × 3.4 m | **15.64 m²** | spread 100° |
| Fill | 5.0 × 3.4 m | **17.00 m²** | spread 140° |
| Rim | 4.8 × 0.62 m | 2.98 m² | widened from 1.26 m² — *"drops peak radiance to 30, below the ~60 at which a clearcoat highlight clips"* |
| Kick | 3.0 × 0.62 m | 1.86 m² | widened from 1.30 m² — *"radiance down to 22"* |

The Key subtends **30.2°** from the car at 8.73 m. Measured on the delivered frame,
on a patch that is pure bodywork (nose / front monocoque):

```
max 0.9238      pixels over 0.95 : 0.0000 %      pixels over 0.99 : 0.0000 %
```

**A clearcoated body panel under studio light that never once reaches full scale.**
The optimiser's success criterion was "no clipping"; it achieved it, and took the
highlight that describes a curve with it. Clipping is measurable and
form-description is not, so the bounded search drove one to zero and the other
with it — the same shape of error as the transport census that measured the wrong
volume (R2-4xx) and `grid_contrast` measuring rows that cannot contain a member.

**And this is the same defect as the "missing" sidewall.** The lettering is
authored at **0.85 mm of relief with no albedo difference** — it is a pure shading
feature. Under a 30°-wide source there is no direction to the light, so a 0.85 mm
step produces no shadow and no gradient. **The tyre lettering, the 1.8 mm panel
gaps and the 1.05 mm seam troughs are all sub-millimetre shading features being
lit by a 15.6 m² source.** One narrow source fixes all three at once.

**Confirmed in the picture, at 8× the delivery band.** `80de0452de84`, the front
wing and wheel at zoom 4.0 — **0.48 mm per pixel, four times finer than delivery**,
where a 14 mm glyph is 29 px tall and a 0.85 mm step spans 1.8 px. The sidewall
annulus measures **sd 0.0471, median |dL/dpx| 0.0020** — about 0.4 % contrast
across a letter edge, indistinguishable from noise. Auto-levelled, one or two
glyph fragments appear and nothing more. **The lettering is in the shipped car
(`wheel_tyre_FL_Lettering` is in `docs/explode_plan.json`), it renders, and the
light cannot show it.** Four times more resolution does not help, which is the
proof that resolution is not this one's problem.

**The prescription is additive, not a retune:** the rig has no source under
1.86 m². Add one narrow strip and leave the four tuned lamps untouched, so nothing
that was measured against clipping is disturbed. Judge it by whether the sidewall
lettering appears, which is a binary the frame can answer.

---

## R2-15xx — beat 1's first 590 frames are still smeared, and R2-321's numbers no longer describe the film

Checked because it was my own leading hypothesis, and **it was wrong at f599.**

`tools/beat1_blur_budget.py` and `beat1_smear_profile.py` read
`work/b1dof/dump.json`, whose `blend` field is **`render/film14.blend` (Aug 4)**.
The film is `film17` (Aug 7). At f599 the two cameras differ by **4.0 m of position
and 20.6 mm of focal length**. This is R2-1007's stale-path failure recurring in a
different file — the dump is not declared anywhere and nothing re-derives it.

Re-measured on the live path, same metric, 4K pixels:

| band | n | film14 median | **film17 median** | over 20 px |
|---|---|---|---|---|
| beat 1, all | 791 | 42.1 px | **14.0 px** | 377 (48 %) |
| presentation tour f1–590 | 590 | 54.7 px | **40.6 px** | **377 (64 %)** |
| CORNER_FL + close-out f591–647 | 57 | 30.1 px | **0.8 px** | 0 (0 %) |
| PROTECTED f648–792 | 144 | 1.5 px | **1.0 px** | 0 (0 %) |

**f599 carries 0.9 px of smear, not the 29.5 px film14 had.** The client picked a
genuinely sharp, well-composed frame and the smear excuse does not apply to it —
my first read was overturned by the measurement, which is the third time on this
project that a visual attribution has failed and the instrument has held.

**But the front 590 frames were not fixed**: 40.6 px median, 64 % over 20 px,
worst 204.7 px. **Car detail cannot pay there whatever is done to the car**, and
that is a camera job, not a car job. R2-321 should be re-scored against film17
rather than left standing on a camera that no longer exists.

---

## What this pass declines to build, with the number

* **Anything on the car.** 616 meshes, 4.80 M evaluated polys, every named feature
  present, and the paint already fixed in the delivered blend. **One constant and
  one lamp, not a rebuild.**
* **Anything finer than 2.7 mm.** That is beat 1's Nyquist floor at 4K. The 3 mm
  panel-line groove cue is already below it at 1.58 px and must not be authored.
* **Any car detail aimed at beats 4, 5 or 6.** 26.5 / **70.2** / **143.6 mm per
  pixel**. Beat 5 is 1,524 frames — 51 % of the film — and holds the whole car in
  **82 px**; beat 6 holds it in **40 px**. Nothing built for hero scale is visible
  in 1,922 of the film's 2,978 frames.
* **The presentation tour's first 590 frames**, until the smear above is resolved.

**Hero car detail pays in 864 frames — beats 1 and 2 — of which only the 201 in
f591–792 are currently both large and sharp.** That is the surface worth the
client's bar, and it is the only one.

## Order of work

**Step 1 of the first draft — "settle whether car_paint v5 is in the blend" — is
done and the answer is yes.** What is left is two changes and a re-render.

1. `s03_materials.py::_planar_weave` — **`Mapping.Scale 190.0 → 62.832`**.
   One constant. Confirmed still at 190.0 in `film17_breach.blend`. Takes the
   weave from 0.87 px to 2.63 px at f599 on the front wing, rear wing, barge
   boards, nose, engine cover, sidepod and halo. **`CarbonFibre` is the only car
   material in the delivered blend that carries no round-2 fix.**
2. One **narrow strip source** added to `build_three_point`, the existing four
   lamps untouched so nothing tuned against clipping is disturbed. Gate: does the
   tyre sidewall lettering appear — a binary the frame answers.
3. Re-render f599 **and** a protected-region frame (f700 or f750) at
   3840×2160 / 512, A/B at matched camera and exposure against this pass's frames.
   **Note the 4K full-frame job OOM'd once on the 5090** (`integrator_shade_volume`,
   job `beac486d6729`); the 64-sample pass and every border crop succeeded, so
   retry or crop rather than assuming a scene fault.
4. Chase the **ten `.001` material twins** in film17 that do not exist in
   `R2829_car_anim_driver.blend` — possible duplicate car geometry in the shot.
5. `front_wing.py:234` — `m.thickness_clamp = 1.0` collapses the declared 13 mm
   endplate to a measured 1.02–2.67 mm (`DEFECTS_ROUND2.json`, critical). It is
   knife-thin in the 4K frame and it is 63 px of flap gap away from being seen.
6. Re-score **R2-321** against film17 rather than leaving it standing on film14's
   camera, and either declare `work/b1dof/dump.json` or make the tools re-derive it.
7. Correct or date `docs/NEXT-REBUILD.md:7`.
