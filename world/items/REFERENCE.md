# The reference item — read this before writing any item module

**`world/items/pit_wall_unit_itemkit.py`** is one item, built end to end, through
`world/itemkit.py`, and it **passes the current eight-check gate**. Read it, then
build yours the same shape.

It is not a toy. It is `pit_wall_unit` — 119 units, 12.31 M triangles, one of the
seven wave-1 items that survives the rewritten gate — with the scaffold deleted
and imported instead. The derivation was mechanical (delete these seventeen
top-level defs, substitute a shim), so the two modules can be diffed and the
claim checked rather than believed.

## What it measures out at

    original  world/items/pit_wall_unit.py            3,226 lines
    derived   world/items/pit_wall_unit_itemkit.py    2,900 lines
    scaffold deleted                                    380 lines
    shim added                                           54 lines
    net                                          326 lines, 10.1 % of the module

Deleted and imported from `itemkit`: `hash01`, `Rng`, `_h2`, `_sstep`,
`vnoise1`, `vnoise2`, `fbm1`, `fbm2`, `clamp01`, `smoothstep`, `_new_mesh`,
`_shade_by_angle`, `NT` (115 lines by itself), `_coll`, `purge`,
`contract_light`, `add_camera`.

10.1 % is the **conservative floor**, not the achievable saving. It counts only
the functions `itemkit` owns today. The same AST census over all 28 wave-1
modules puts **29.9 % of 102,554 lines** in functions whose name recurs in three
or more modules — `test_scene`, `selftest`, `interface_json`, `main`,
`build_ground`, `macro_rig`, `build_standins` are all in that band and are still
hand-written here because they are half item-specific. Trimming them is the next
pass; do not re-derive them from scratch either.

## The gate says it is the same object

`item_gate.py` was run on both. Both `ITEM_ACCEPTED`, all eight verdicts
identical:

    no_external_assets              PASS      witness_frame_valid            PASS
    material_depth                  PASS      surface_microstructure         PASS
    geometry_resolves_at_distance   PASS      relief_reads_as_lip_and_shade  PASS
    per_instance_variation          PASS      silhouette_departs_from_analytic  n/a

Of the 25 measured quantities in the two reports, **24 are bit-identical** —
119 objects, 12,312,868 triangles, 45 procedural texture nodes, p10 edge
3.00 mm = 1.80 px, size CV 0.06613, 22 distinct topologies. The 25th differs in
its sixth decimal (`p90_edge_m` 0.031399 → 0.031398), which is float ordering.

**The one deliberate behavioural change is R2-020.** The original's `test_scene`
set `resolution_x = 1920`, as 17 of the 28 wave-1 modules do, while the gate
scores every pixel figure against 3840. The derived module hands the render
settings to `itemkit.macro_rig()`, which renders 3840 × 2160 and asserts the
camera really stands at the manifest's 6.200 m.

## The shape to copy

```python
sys.path.insert(0, _WORLD)
import itemkit as K
import world_contract as C

ITEM, COLL, PFX = "pit_wall_unit", "W_Item_PitWallUnit", "PWU_"

FILMED_AT_M, LENS_MM = 6.2, 35.0            # from the manifest, not from taste
PX_PER_M = K.px_per_m(FILMED_AT_M, LENS_MM) # 602.2 px/m -> 1.661 mm per pixel

def build(...):
    root = K.coll(COLL)
    K.purge(PFX, COLL)                      # prefix-scoped; cannot touch another item
    me, off = K.new_mesh(PFX + "U000", V, quads=Q)   # recentres; Law 6
    ob = bpy.data.objects.new(PFX + "U000", me); ob.location = off
    ...

def test_scene(samples=256):
    root = build(...)
    cams  = K.coll(COLL + "/Cameras",  root)
    stand = K.coll(COLL + "/Standins", root)   # the gate skips this sub-collection
    K.contract_sun(PFX, scene=scene, coll_=root)   # refuses to point at the sky
    K.ground_plane(PFX, stand, span=150.0)
    K.macro_rig(PFX + "CAM_MACRO_4K", loc, aim, LENS_MM, cams,
                want_distance_m=FILMED_AT_M)       # 3840x2160, distance asserted
    K.assert_no_external_assets()                  # Law 1, before any GPU job
```

## The five things `itemkit` will not let you get wrong

Each of these is a defect somebody already shipped, made structurally
impossible instead of merely written down. `python3 world/itemkit.py --selftest`
proves all of them, and each proof includes a negative control — a broken input
that the check is shown to reject.

| you cannot | because | it happened as |
|---|---|---|
| render the deliverable at 1080p | `macro_rig` refuses any resolution but 3840 × 2160 unless the keyword `i_know_this_is_not_the_gate_resolution` is named | R2-020 — 11 of 28 heroes scored at 2× |
| build a scene with no sun, or one pointing up | `contract_sun` always makes the lamp, and measures its emitted direction | 2 of 28 test scenes; R2-021 twice in one session |
| address a material in world space | `NT` has `object_coords()` and no `position()` | the first pass's blotching at \|P\| ≈ 1000 m |
| ship the non-avalanching `hash01` | one implementation, and the selftest measures the bit-flip rate (0.5032 vs 0.2458 for the naive form) | 14 of 15 modules still carry it |
| delete another item's sun | `purge(prefix)` has no default prefix | `armco_post`'s docstring — the render came back black |

## The relief stack states RADIANCE, not millimetres (added 2026-08-02)

Section 16 of the reference module used to read `t.bump(height, strength,
0.0020)`. It now reads

```python
LAM_AGG = K.VORONOI_WAVELENGTH_FACTOR / 105.0        # 20.67 mm
b = t.bump(height, strength, modulation_pp=2.6305, wavelength_m=LAM_AGG)
```

Copy that shape. **What the eye judges is not the height of a bump, it is the
radiance modulation it produces**, and under this film's 12.47° sun that
conversion carries a 4.52× amplifier — `m = 2 sin θ / tan e`. Three amplitude
sets were rendered and rejected on the human figures and every one had been
chosen in millimetres of cloth. See `ITEM-CAMPAIGN-BRIEF` §4a and `itemkit`
section 5b.

**The migration was a no-op on the pixels and the module proves it**: check
`[8b]` of `pit_wall_unit --selftest` reproduces all six shipped `Distance`
values from the modulations to a worst error of 4.4e-05, and shows that a
modulation 10 % wrong would miss by 11.7 %. State the target; do not re-tune
what has already been looked at.

**But `[8b]` ALONE CANNOT FAIL, and that is R2-058.** It states a wavelength and
then asks whether `relief_amplitude_for(m, lam)` reproduces a `Distance` that
was derived from the *same* `lam`. That is an algebraic identity: it passes for
any value of the wavelength constant, including a wrong one. The ply row read
`1.0 / 230.0` for three weeks — 3.183× too long, because a `ShaderNodeTexWave`
multiplies the coordinate by 20 before the sine and so emits `2π/20 = 0.31416`
of `1/Scale` — and `[8b]` passed every single time, because `itemkit`'s
`_tex_wavelength_m` carried the identical error and the two agreed with each
other. The correct value was sitting in a comment sixteen lines above the wrong
code, as the *control* for a different measurement.

So `[8c]` was added, and **copy that instead**. It renders the module's own wave
node alone through an orthographic camera and counts the bands:

```
[8c] the ply veneer's wavelength, MEASURED OFF A RENDER
  ok   the ply wave EMITS the wavelength this module declares
       declared 1.3659 mm, rendered and counted 1.3659 mm, 0.00 % apart
       (the 1/Scale reading would be 4.3478 mm, 3.18x out); the probe's own
       control, a 10.000 mm ask, comes back 10.0000 mm
```

`K.emitted_wavelength_m(build)` is the helper; it builds its own scene, refuses
if that scene is not exactly its plane and camera, and turns the denoiser off.
**A check that uses the constant under test on both sides is not a check.** If
your module declares a wavelength, render it and count.

**Ask for the pitch by name.** `K.wave_scale_for(lam)`, or
`nt.wave(vec, wavelength_m=lam)` — never `scale=1/lam`, which is the shape of
this defect. `noise()` and `vor()` have taken `wavelength_m=` all along; `wave()`
does now too.

**Check the geometry layer too.** Once the human figures' fabric *shader* was
corrected, the same misconception turned out to be one layer down in the
fold-field *geometry* at m = 2.32, and became the dominant defect.
`tools/relief_audit.py` reports both layers of a built blend in one run.

## Then prove it, and do not stop at "it ran"

```bash
# 1. build and save the test scene
blender -b --factory-startup -P world/items/<id>.py -- --test --save world/items/<id>_test.blend

# 2. gate it. --collection, not --prefix.
blender -b world/items/<id>_test.blend --factory-startup -P tools/item_gate.py -- \
        --item <id> --collection <YOUR_COLLECTION> --out render/items/<id>/gate.json

# 3. LOOK at the witness frame the gate rendered, and at your own macro
#    render/gate_witness/<id>/witness.png

# 4. confirm what actually landed on disk
python3 tools/campaign_preflight.py --items <id> --policy wave2
```

Step 3 is not optional and step 4 is not a formality. Nine instruments on this
project turned out to be the broken thing, and the two techniques that have
worked are *test the check against something already known to be bad* and *look
at the artefact, not the number*.
