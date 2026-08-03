# Wave 1 peep synthesis — what six independent reviews agree on

Six foundation items were adversarially pixel-peeped. **Every one returned
REWORK. Zero SHIP. The acceptance gate accepted zero.** The reviews are rigorous
and quantitative, and read together they show four faults that no single reviewer
could have seen — two of which are SYSTEMIC and must be fixed before any further
material work, because they corrupt the conditions every material is judged under.

---

## SYSTEMIC 1 — the item test scenes have no sun

`spectator_seated`, measured over the full 4K plate:

> "There is no sun in this frame. R minus B is NEGATIVE in every single luminance
>  band, and it gets more negative the brighter the band (−0.043 in the shadows,
>  −0.118 at 0.3–0.45, −0.176 in the top band)."

Blue exceeding red, and increasingly so toward the highlights, is the signature of
**sky-dominated illumination with no direct solar component**. A 12.5° sun is warm;
anything it lights should push red positive in the bright bands.

This is the SAME signature already measured on `CAM_CAL` (task #49): linear mean
0.0616 with the blue channel 8 % above red and green, on a card the camera can see
in full. Two unrelated scenes, same defect.

**Consequence: every material judged in a wave-1 test scene was judged under the
wrong light**, so every appearance-based conclusion in these six reviews — and any
calibration done against them — is suspect. Fix the light first, then re-judge.
Nothing about material tuning should be actioned until this is closed.

Suspects: the sun object missing from `procedural_world()`-derived test scenes
(it builds a Sky Texture background but a Sky Texture is not a sun lamp); a sun
whose visibility or strength is zero; or the sun occluded by the item's own
staging geometry.

## SYSTEMIC 2 — the hero macro is uniformly soft, and it is not depth of field

`armco_w_beam`, mean |Laplacian| (per-pixel detail energy):

    near steel face @2.6 m   1.775
    mid                      1.715
    far                      1.790
    ground                   1.580
    SKY                      1.543

**The sky carries 87 % of the detail energy of the in-focus steel.** A sky is a
smooth gradient with essentially no high-frequency content; if it measures nearly
as "detailed" as the focal subject, the number is not reporting subject detail —
the whole frame is uniformly soft. Depth of field cannot do this: DoF is a
function of distance, and near/mid/far here are identical within 4 %.

Prime suspects, in order: an over-aggressive denoiser eating detail at these
sample counts (OPENIMAGEDENOISE is on for every job), the film filter width, or
a render resolution/scale mismatch. **This would affect every render the project
has produced**, including the frames used to reject earlier work.

---

## PATTERN 3 — surfaces measure FLATTER than placeholder primitives

`crew_fireproof_overall`, band-passed contrast as % of mean:

    maroon back panel   r1 0.89  r2 0.34  r4 0.49  r8 0.96  r16 1.33
    maroon thigh        r1 1.01  r2 0.50  r4 0.70  r8 0.85  r16 0.90
    STANDIN head (a smooth featureless ovoid) 1.52 / 0.86 / 1.06 / 1.34 / 1.66
    flat ground plane                          0.34 / 0.20 / 0.47 / 1.10 / 1.95

**The fireproof fabric is flatter than the placeholder blob head.** And what
little energy exists is all at r8–r16 (2–4 cm) with none at r1–r4 (3–11 mm) —
the signature of a soft AO/dirt mask with no fabric beneath it.

The same fault, in each reviewer's own words:
- `armco_w_beam`: "no zinc spangle — zero crystal boundaries, zero polygonal
  facets, zero dendrite" in a 0.63 × 0.56 m crop of real steel at 1436 px/m.
- `marshal_post_deck`: "the timber has no grain at any scale the eye can use"
  in the 5–11 px band, exactly where latewood ridges and saw kerf live.
- `terrain_ground`: "stones are untextured low-poly blobs of a single colour" —
  six sampled stones cluster at one hue, one value, one material.
- `spectator_seated`: "the garments are inflated balloons wearing a moulded
  plastic bib."

**This is R2-016 restated with numbers.** The fix is not more procedural texture
nodes — `crew_fireproof_overall` already has 28 and `spectator_seated` 51, and
both pass the gate's material_depth check. Nodes are not structure. The gate's
`material_depth` check counts nodes and is therefore measuring the wrong thing;
band-passed contrast against a known-smooth reference is what actually discriminates,
and it should replace or supplement the node count.

## PATTERN 4 — nothing has a history, and claimed features are absent from frame

- `crew_fireproof_overall`: across ~30 legible figures, **zero** knee dirt, shin
  abrasion, rubber transfer, grease handprints, sweat darkening or repairs. Two
  of its six declared `variation_axes` produce literally no visible signal on 110
  instances. Its headline claim — the fold language — is measurably absent: the
  trouser silhouette fits a quadratic taper to **0.61 px RMS (1.6 mm)**, i.e. a
  machined cone, where real Nomex should perturb it 5–10 mm.
- `armco_w_beam`: across ~9 m of three-rail barrier, "not one rust bleed, not one
  white-rust bloom, not one chip, not one paint transfer, not one tyre smear."
- `marshal_post_deck`: "not one fixing is visible anywhere on the deck" against a
  claim of ~90 screws per ply floor and proud nail heads; a 25 mm nail head is
  15 px at 622 px/m, far above the resolve threshold.
- `terrain_ground`: ruts claimed at 46 mm deep with chevron tread printed in the
  floor render as "brown stripes with no depth anywhere in the frame."

**The recurring shape: the mechanism is in the code and its amplitude is 3–5×
too small to survive to pixels.** That is a different bug from "not built", and
it is invisible to any check that inspects the code rather than the image.

---

## Order of work

1. **Fix the sun** in item test scenes. Nothing else is trustworthy until then.
2. **Diagnose the uniform softness** — denoiser, filter width, or resolution.
   Re-render one known item and re-measure the sky-vs-subject Laplacian ratio.
3. Only then re-judge materials, and raise amplitudes against a band-pass
   measurement rather than against a claim.
4. Replace the gate's `material_depth` node count with band-passed contrast
   versus a known-smooth reference in the same frame. Both items that failed this
   pattern PASSED the node count.
