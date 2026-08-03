# People — the hardest asset class in the film

> "the people in stands honeslty fucking shit idc if there not noticable send out
>  a workflow and build us the best fucking people in the fucking world"
> "again no external assets we build everything in house"

Also standing, from earlier:

> "also im looking at this i want ultra realestic and inasne so lets add real
>  people pit crews add people in the stands fuck it lets go all out."

**No MakeHuman, no Mixamo, no scanned meshes, no photo textures, no downloaded
rigs, no AI-generated anything.** Every vertex procedural, generated in Blender by
code we wrote. This is not negotiable and it is checked, not trusted.

---

## What is wrong right now — measured off `CAM_SPECSEAT_MACRO`, 3840×2160

This is the honest defect list from pixel-peeping the current grandstand render.
It is the specification in negative: fix all of it.

1. **Heads are featureless ovoids.** No facial structure, no ears, no jaw, no
   brow, no neck transition. No hair geometry of any kind. At macro distance a
   head reads as an egg.
2. **The pose vocabulary is roughly six poses across ~600 figures.** The
   "arms crossed in an X on the lap" pose repeats dozens of times, visibly, all
   over the frame. This is *"one tree spammed 100 times"* wearing a shirt.
3. **Zero props.** No phones held up, no caps, no bags, no flags, no banners, no
   drinks, no cameras, no umbrellas, no scarves, no programmes. A real grandstand
   is dense with objects and half of them are held in hands.
4. **Clothing is flat colour fill.** No folds, no collars, no sleeve hems, no
   waistbands, no seams, no shoe geometry. Shirts are a solid RGB value.
5. **One body type.** Uniform adult proportions throughout. No children, no
   elderly, no larger builds, no height distribution, no sex dimorphism.
6. **Hands are stumps.** No fingers. Nothing reads as a mannequin faster.
7. **Nobody is standing, walking, or moving.** Every figure is seated. Real
   stands always have people on their feet, in aisles, climbing steps, turned
   around talking to the row behind.
8. **Occupancy is random-uniform.** Real crowds cluster into groups — families,
   friends, pairs — leaving irregular gaps, denser at the centre and front.
9. **No attention.** Nobody is looking at anything in particular. In a real
   grandstand almost every head is turned toward the same moving object.
10. **Figures do not interact with the seats** — some intersect the seat back,
    some float; contact is not solved.

---

## The standard

The bar is not "acceptable at distance". The user said explicitly:
**"idc if there not noticable"** — build them properly regardless of whether the
camera lingers. Wall-clock and render time are not constraints; he has said a
month is acceptable and that he tops up the render funds.

Where the camera actually goes (from `docs/item_manifest.json` — read your own
item's record, do not guess):
- **Pit crew** are the hard tier: fully-covered figures at **10–30 m**.
- **Spectators** are massed, at greater distance, but must survive a long lens
  and must be *alive* — a still crowd reads as a photograph of a car park.

---

## What "built by hand" means here, concretely

A believable human is not one mesh. It is a stack, and each layer must exist:

| layer | what it must actually be |
|---|---|
| **skeleton / proportions** | parametric, driven by an anthropometric distribution — stature, limb ratios, shoulder/hip width, mass. Different *bodies*, not one body scaled. |
| **pose** | joint angles within real anatomical limits. A pose library large enough that no pose repeats visibly in a 600-person stand. Weight must land on the seat or the feet. |
| **head** | skull structure, brow, nose, jaw, ears, neck. Hair as geometry — curves or cards with real silhouette, not a painted cap. |
| **hands** | fingers. Separated, posed, gripping what they hold. |
| **clothing** | geometry shells with folds, collars, cuffs, hems, waistbands, seams, and fit that varies with the body underneath. Garment *types*, not colour swaps. |
| **footwear** | actual shoes with soles. |
| **materials** | skin with subsurface scattering and real tone variation; fabric with sheen and fibre character; hair with its own shading. |
| **props** | held and worn objects, distributed by plausible frequency. |
| **crowd logic** | grouping, occupancy, standing fraction, gaze direction, density falloff. |

---

## Variation is the whole problem

A crowd is not one person 600 times. Every axis below must vary **per instance,
in the geometry**, not by tinting a shared mesh:

stature · build · sex · age · skin tone · hair colour, length and style · garment
type · garment colour · garment fit · pose · gaze · what they are holding · what
they are wearing on their head · posture (slouched, upright, leaning) · whether
they are seated at all

The gate measures this. `tools/item_gate.py` computes a coefficient of variation
across instances and counts distinct topologies; identical copies score exactly
0.0 and fail. Where a family is geometry-nodes instanced the gate can only see
chunk objects and **says so explicitly** — in that case the variation has to be
proven in a render, not asserted.

---

## Acceptance

Every figure item runs `tools/item_gate.py` (see `docs/ITEM-CAMPAIGN-BRIEF.md`
for the full contract) and must pass all four checks:

- `no_external_assets` — zero image-texture nodes, zero external image files
- `material_depth` — ≥ 6 procedural texture nodes reachable from the surface
- `geometry_resolves_at_distance` — 10th-percentile edge ≤ 6 px at the item's
  own filmed distance and lens
- `per_instance_variation` — CV ≥ 0.03 and ≥ 2 distinct topologies

**And then it is looked at.** The gate exists so that human attention is spent on
whether these read as people, not on catching placeholders. An item is done when
the gate passes *and* the render survives a hard look at the distance the film
actually uses.

---

## The rule that governs all of it

Do not report success because the code ran. On this project the **verification**
has been the broken thing five separate times (see R2-017 and R2-018 in
`docs/DEFECT-LOG-R2.md`) — a collision test that compared bounding boxes, a
surface normal that is mathematically zero for any closed mesh, an assertion that
could never fail, a gate that ranked the most-correct object first, and two gates
that printed a PASS while measuring nothing.

Measure the artefact, not the process. State plainly whatever you could not
verify.
