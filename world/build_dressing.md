# build_dressing.py — trackside dressing for Circuit Vitrine

One module, one `build()`, one collection tree (`R2_Dressing`). Idempotent: every
datablock it owns is named `DR_*` and is purged before the rebuild, so running it
twice is identical to running it once.

```
/opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P world/build_dressing.py
   ... -- --render all --res 1600x900 --samples 96
   ... -- --list-renders
   ... -- --render doppler --context          (builds surface + barriers too)
   ... -- --save world/dressing_test.blend
```

There is no `--sun` and no `--bg`. The light is `world_contract` §13 and it is
not a knob (see defect 24). Render on the 5090 through
`rq render --dof off`, never through `tools/r5090` (defect 26).
```

## What it owns

| element | source of the placement rule | count |
|---|---|---:|
| marshal posts (4 archetypes, individually kitted) | corner exits + mutual sight lines + the barrier module's access gates, dropped or relocated where there is no ground behind the barrier | 24 |
| barrier-face advertising boards | TV-value field: corners sell, the pit straight sells, the infield does not | 494 |
| catch-fence banners (printed cloth, hemmed, grommeted, tied) | same field, only where a fence exists — and every TecPro run, because nothing is strapped to 1.75 m of energy absorber | 127 |
| free-standing hoardings | braking zones + six named sight lines, 55 m minimum separation, real ground behind the barrier | 9 |
| bridge fascia banners | the two overpasses' own geometry, read out of `build_architecture.py` | 4 |
| apex / low sponsor boards | insides of corners, on the sealed platform, never in a gravel bed | 15 |
| braking-distance boards | 300/250/200/150/100/50 m before the real turn-in of the real braking zones | 24 |
| corner number + name plates | corner entry, outside barrier | 15 |
| information + gate signage | sector splits, access gates, medical/rescue points | 15 |
| tyre stacks (4 tyre archetypes) | gates, post pads, four service laybys | 114 / 477 tyres |
| trackside TV camera masts | one per ~280 m, biased to corner outsides | 13 |
| PA horns / windsocks | spectator zones / high points | 13 / 3 |
| cable conduit + junction boxes | along the barrier foot, in segments — it stops where the barrier line does | 9 runs, 65 boxes |
| verge gullies | verge/runoff seam, never inside an apex gravel bed | 46 |
| painted sponsor names on the asphalt runoff | inside `runoff_widths(s, side)["asphalt"]`, measured | 5 |
| flagpoles with sponsor flags | S/F approach | 12 |

```
objects 242 · vertices 2 876 246 · triangles 4 190 819 · materials 12
brands 31 · board units 649 · distinct board signatures 649 · duplicates 0
marshal posts 24 · max gap 338.3 m · min sight-line clearance +0.35 m
ground anchors 974 · all on world_contract 1.0.0's ground · max dev 21.2 mm
headless build time 42 s (numbers from `build()`'s own summary dict)
```

The counts fell because the module now refuses to build furniture it cannot
stand up honestly: 33 placements had no ground behind the barrier (the pit wall
leaves 0.6 m of footing, and that ground is the pit lane), and 206 were inside
the 95 m of lap where `build_barriers.barrier_offset` is not on the barrier.
Both numbers are in `placement_gate`, printed on every build.

Explicitly **not** mine: Armco / TecPro / catch fence / gravel / runoff asphalt
(barriers), pit-wall advertising, grandstand fascia advertising, the S/F gantry
and its lettering (architecture), kerbs, verge paint and grid numerals (surface),
grass and trees (terrain), sun and sky (lighting).

---

## THE CONTRACT

`world_contract.py` v1.0.0 is authoritative over this file. It owns no datum, no
width and no ground height of its own.

```python
ground_z(s, lat, side)        -> world_contract.ground_z, SIGNED lateral
half_width / verge_edge       -> world_contract's, verbatim
runoff_widths(s, side)        -> world_contract's
anchor(name, s, lat, side...) -> the ONLY way anything here touches the ground
```

**`side` is a required argument of `ground_z`.** That is the whole of finding #1
in one line: the old signature was `ground_z(s, lat)` with an unsigned lateral,
delegating to the old `build_barriers.ground_z`, which was
`elevation_c(s) − 0.016·max(0, lat − verge_edge)` — no crown, no banking, no
undulation, and structurally *unable* to carry banking, because a function of
`|lat|` cannot be antisymmetric. Leaving `side` out is now a `TypeError` at build
time instead of a silent 0.69 m error at 4K.

### What that was worth, measured

`render/world/dressing/verify_dressing.py` builds this module and projects **every
DR_ vertex** to `(s, u)`, then compares it with `C.ground_z(s, u)`. Run against
the module as it stood, with `build_barriers` **already** migrated to the
contract (so this is the residual that was mine alone):

| | before | after |
|---|---:|---:|
| deepest vertex below the datum | **1.689 m** (`DR_Billboard_09`) | **0.455 m** — and it is a billboard *footing*, 1.4 % of that object's vertices, top 6.07 m above grade |
| objects with any vertex > 150 mm under | 77 / 260 | 41 / 242 |
| objects **mostly** buried (> 25 % of vertices under) | — | **0** |
| objects wholly below ground | — | **7**, all of them verge-gully-only batch chunks, which are recessed drainage by design |
| mean buried fraction | — | **2.0 %** |
| ground anchors off the contract's ground | — | **0 / 974** |
| anchor vs `world_ground_z` | — | max **21.2 mm**, p99 20.1 mm — and 20.0 mm of that is `C.BASE_EMBED_M`, applied deliberately |

The review's own headline (89 of 150 buried, median −0.34 m, `DR_Sign_006` 7.38 m
under) was measured against the *unmigrated* world, where `build_terrain` was
also on top of everything.

### And then against the neighbours' actual triangles

Stage 1 only proves this module agrees with the contract. The assembly review's
single lesson is that agreeing with yourself is not the test. So
`--assembled` builds `build_surface` and `build_barriers` into the same scene and
raycasts **every anchor onto their real triangles**, and BVH-overlaps every
`DR_` object against the barrier structure:

| | result |
|---|---|
| anchors that found ground | **972 / 974** (the two misses are gullies at s 3253 / 3335 on the pit-straight left, where the platform is 0.6 m of pit-wall footing) |
| anchor vs the neighbour's mesh | mean **+21.4 mm**, p50 +27.9, p95 61 mm, rms 49 mm |
| worst | **+268.9 mm** at `board@719.1/+1` |
| `DR_` objects intersecting the barrier structure | **28**, 12 345 triangle pairs — down from **77 / 207 583** |

The +28 mm median is not this module's: the anchors are on `C.ground_z` to 1 mm,
so it is `build_barriers`' runoff-platform and verge mesh sitting that far below
the datum, against a `TOL_SEAM_M` of 10 mm. Reported, not worked around.

**One `verify_dressing.py` bug is worth recording because it nearly produced a
false pass in the other direction**: the first assembled run reported 976 of 1071
anchors "missing the ground" and none of them were. Freshly created objects carry
a stale identity `matrix_world` until the depsgraph updates, so every neighbour
triangle was at the origin. `bpy.context.view_layer.update()` after each
neighbour's `build()`; the same run on a *saved* blend had been finding ground
everywhere all along.

---

## THE VARIATION SYSTEM

The brief's red line is *"i dont want repeat stuff aka one tree spammed 100 times
… not a grass gray line done"*. Trackside dressing is where that is hardest,
because a real circuit is genuinely repetitive — and the answer is not to
randomise, it is to build the thing that produces the repetition.

**Nothing in this module is an instance.** No linked duplicates, no particle
systems, no geometry-node point instancing. Every board, post, tyre, cone, sign
and bolt is generated from its own parameter draw straight into its own vertex
data. The module asserts it: every board's `(family, brand, W, H, age, damage,
layout)` signature is hashed at build time and the count of duplicated
signatures is reported in the summary. It is **0**.

`build()` is verified idempotent by calling it twice in one Blender session:
identical object / mesh / material counts (258 / 258 / 12) and identical vertex
and triangle totals (2 000 439 / 2 785 581) both times.

### 1. A brand book, not a colour randomiser

31 invented brands (`BRANDS`). The first 12 names and colours are shared
verbatim with `build_architecture.py` so the pit wall, the grandstand fascia and
the trackside boards advertise the **same companies** — a circuit sells one
sponsor package, not three. The other 19 are this module's.

Every brand carries a sector, a mark type (chevron / ring / bars / wave /
diamond / monogram / delta / arcs / shield / grid / hex / wing / bolt / drop /
mountain / arch / crest), a typographic tracking value, a strapline and a
**commercial tier**. Tier drives how much space the brand buys:

```
TIER_W = {1: 0.6, 2: 1.0, 3: 1.7, 4: 2.6, 5: 1.2}
```

so MERIDIAN (the fictional tyre supplier, tier 4) is on the boards four times as
often as LE BREUIL (the local vineyard, tier 1). That is what makes the
distribution read as a sales sheet rather than as uniform noise — and it is the
reason a brand *is* allowed to recur. A brand recurring is what a brand is.

**What is never allowed to recur is a board.** Within a run, a brand takes 1–2
consecutive slots and no more; the run then moves to another brand from its own
2–5 brand pool.

### 2. Artwork is composed, not textured

There are no image textures anywhere in this module. Board graphics are authored
as 2-D polygons in **board metres** by an `Art` class (rect / fan / disc / ring /
strip / mark / text) and then mapped through the board's own surface function
into 3-D. Ten layouts (`LAYOUTS`) plus a house layout, chosen by aspect ratio:
long boards get repeat or band layouts, tall boards get mark-led ones.

Type is baked from Blender's bundled font, one glyph at a time, cached, and
composed with a per-brand tracking value — so the same word is a different
logotype for a different brand. `bold` dilates the outline on a 12-point ring,
which is how the braking boards get numerals heavier than any weight the font
ships with.

Because the art is geometry, it goes **through** the surface deformation: the
print on a dented board is dented, the print on a sagging banner sags, and the
graphic on a bridge banner follows its bow. A decal projected onto a deformed
board would not do that.

Every art polygon is clipped to the board rectangle (Sutherland–Hodgman) before
it is mapped, so a deliberately over-scaled ghost mark bleeds off the edge and is
cut exactly at the edge, like real print.

### 3. Age is a story, not a slider

The first version aged everything uniformly and the circuit looked derelict. The
fix is a distinction a real race weekend has:

* **event advertising is new.** Boards and banners draw `age = 0.04 + 0.80·u³`,
  so most are freshly printed and a minority are the permanent local advertisers
  that have been up for years.
* **permanent furniture is old.** Corner plates, braking boards, marshal-post
  steelwork, cable boxes, gullies and tyre stacks draw age uniformly.
* **flags are the newest cloth on the circuit** (0.05–0.34) — they get replaced
  every season, and a bleached yellow flag reads as a mistake.

Age then drives print bleaching (saturation loss, not a mix toward grey), rain
streaking, dirt, roughness, rust coverage on steel and chalking on rubber.

### 4. Per-unit draws

| unit | what differs per unit |
|---|---|
| barrier board | brand, layout, 2.0–4.6 m length, 0.62–1.00 m height, seat height, thickness, panel bow, lean, 0–2 dents (real geometry, and the print follows them), 2–3 straps, bolt count, age, dirt |
| fence banner | as above plus sag depth, billow direction, wrinkle phase, cable-tie count and the back face's own grime |
| hoarding | 6.0–13.5 m × 2.4–4.0 m, top height 4.2–6.4 m, 2–4 physical panels each with its own bow and seating, joint shadow gaps, 2–3 legs, footing depth, brace angle, optional maintenance ladder, yaw toward the braking car |
| marshal post | one of four archetypes; shelter W/D/H, roof fall, roof material, painted or galvanised, skin material, pad type (slab / gravel / none), platform height, stair side; and an equipment manifest drawn per post from a 17-item library, each item placed in its own slot with its own yaw |
| tyre | archetype (slick / wet / road / truck), radius, width, rim ratio, groove count and depth, wear, chalking, out-of-round wobble, load squash from the stack above it, compound band colour |
| tyre stack | height 2–7, capped or open, belted or not, upright or toppled, through-bolt, per-tyre yaw and tilt |
| braking board | on its own posts or clamped to the Armco, black-on-white or white-on-black, panel bow, optional dent, angled 8–22° toward the oncoming car |
| TV camera mast | height 3.2–5.6 m, lattice taper, pan and tilt of the head, cable drop |
| cone / bin / crate / extinguisher / jerrycan | size, colour, age, dirt, yaw; extinguishers in three real sizes including a 50 kg trolley unit |

### 5. Layout variation, not just surface variation

* the ribbon of boards is **not continuous** — the TV-value field opens gaps, and
  gates, corner plates and braking boards reserve metres of barrier that
  advertising is not allowed to occupy;
* boards and cloth banners alternate on the same run, at different heights;
* four marshal-post archetypes (open canopy, box hut, equipment stand, raised
  platform) rather than one prefab;
* tyre stacks appear as neat capped stacks, belted stacks, and toppled ones.

---

## Placement logic

### Marshal posts

Real flag points sit at corner exits, on the outside, where a marshal sees the
corner he is covering and can see the next post. The plan is built in that order:

1. one post at every corner exit (`s_apex + arc/2 + 8…42 m`), on the outside;
2. an **inside** flag point at T4 — the hairpin is slow, the inside is where
   marshals actually stand, and it is the background of the beat sheet's
   kerb-height hero camera;
3. an extra post in the braking zones of T10 and T12;
4. infill so no gap exceeds 300 m;
5. every post within 55 m of one of the barrier module's 16 access gates is
   **pulled toward the gate** — a post without a way onto the circuit is
   decoration;
6. a **sight-line solve**: for every consecutive pair, the chord from eye height
   to eye height is tested against the road's own vertical profile. Where it
   fails, the upstream post is promoted to the raised-platform archetype (which
   is exactly what a real circuit does on a crest); only if that is still not
   enough is another post inserted, and the solve is re-run.

Result: **25 posts, maximum gap 253.9 m, minimum sight-line clearance +0.41 m**.
Both numbers are in the summary dict, recomputed on every build.

### Advertising

`tv_value_field()` computes a sellability value per metre per side from the
corner table (each corner weighted by how much television it gets — T1, T4, T12
at 1.00, the esses at 0.55), plus a hard override for the pit straight and the
doppler straight, times a slow noise so the density is never uniform. The pit
wall side of the pit straight is forced to zero because `build_architecture.py`
already advertises there.

Boards are then walked along the barrier line in runs of 9–46 m. `B_CONCRETE`
and `B_NONE` stretches are skipped, so nothing is ever stuck to a pit wall or
floating across the open pit-exit apron.

Hoardings stand behind the runoff at the braking zones (where a driver looks at
them for two seconds) and at six named sight lines, with 55 m of enforced
separation so one never stands in front of another.

### Braking boards

At the **real** braking zones from the spec's corner table, at the distances a
circuit actually paints: 300/250/200/150/100/50 before T1's turn-in (a 93.8 m
stop from 330.8 km/h), 200→50 at the hairpin, 250→50 at La Plongée, and shorter
sets at T5, T10 and T15. Distances are measured back along the centreline from
`s_apex − arc/2`, not eyeballed.

### The banner: what a hung sheet actually is

The review's verdict on this family was *"a flat colour fill with no fabric,
wrinkles, grommets, print texture or sun-fade"*. All five were true. What is
there now, outside in:

* a printed PVC-coated polyester sheet, **hemmed 35 mm** all round with the hem
  folded to the back and a stitch line showing on the face;
* **brass eyelets** punched through the hem on ~0.5 m centres along the top, on
  wider centres along the bottom, and one per side — flange, flange, barrel and
  a dark bore, all built by sampling the cloth surface so they follow it;
* **cable ties** through most of them, and **not all of them**: 14 % are left
  undone, and one banner in eight has **torn a grommet out** entirely, so that
  corner droops and the hole is a ragged crescent;
* the top edge **scallops between the ties**, creases fan down from each one, and
  the whole sheet carries the 1–3 **storage folds** it was creased with in its
  crate — the grommet list is shared by the surface function, the eyelets and
  the ties, so the wrinkles radiate from the holes the ties actually pass
  through;
* a **weave**, not a grid: warp and weft on a 1.15 mm pitch, half a pitch out of
  phase, combined with `MAXIMUM` so the yarns cross over and under, plus slub;
* **selective UV fade** — magenta and yellow die years before cyan, so a faded
  banner goes cold and light rather than grey — weighted to the top edge, which
  sees the most sky;
* **grime in the weave's valleys**, not on its crowns;
* **transmission**: a 12.47° sun behind a banner shows through it, and the mesh
  variant (45 % of them) passes three times as much light as the solid PVC one.

### The two hero windows

The beat sheet puts the camera 4.0 m from the barrier at the doppler hover
(s = 2555, right side) and at kerb height 4 m from the tyre wall at the hairpin.
`hero_tier()` marks eight windows from the beat sheet; tier ≥ 2 raises art
tessellation (0.12 m vs 0.30 m for rigid boards, 0.045 m vs 0.085 m for cloth),
panel grid density and banner mesh density. There is no polygonal LOD *switch* anywhere — a one-shot
camera would find the seam — only continuous density changes between neighbouring
objects that are never both in the same frame at the same scale.

---

## Contracts with the other builders

* **`world_contract` owns the ground, the widths and the light.** See THE
  CONTRACT above. `build_barriers` is still imported as a library (its `build()`
  is behind a `__main__` guard) but only for four things it alone knows: the
  **clamped** barrier line, `owned_edge`, `GATE_STATIONS` and `ARMCO_TOP`.
* **The barrier line is read off the barrier's own panel-node polyline, not off
  a declared offset.** `barrier_offset(s, side)` is a *nominal* face;
  `build_barriers` lays 4 m W-beam panels as straight chords on a jittered line,
  so through a corner the steel sits inboard of it by the panel sagitta.
  `barrier_face(s, side)` and `barrier_back(s, side)` sample
  `BR.barrier_nodes(side)` — the same construction the rails are swept along —
  and return the running min / max lateral over ±3 m, so a 4.6 m board clears
  every panel it spans. Measured against `barrier_face`, per 4 m station bin:

  | | inboard of `barrier_face` | outboard |
  |---|---:|---:|
  | `BR_Armco` | p50 **+0.027**, p05 −0.015 | p50 +0.227 |
  | `BR_TecPro` | p50 **−1.744**, p05 −1.774 | — |
  | `BR_FenceStruct` | p50 +0.297, p05 **+0.104** | p50 +0.547 |
  | `BR_FenceMesh` | p50 +0.345, p05 **+0.218** | — |
  | `BR_Concrete` | p50 −0.270 | +0.274 (a 0.6 m wall on its centre line) |

  Boards therefore hang at `barrier_face − 0.045` (strap + bolt-head depth), and
  banners at `barrier_face + 0.055`, which is the only lateral where the cloth
  clears both the fence post flange at +0.104 and its own 20 mm backward billow.
* **Nothing is strapped to TecPro.** The declared face is the *back* of three
  0.55 m rows plus a 0.10 m standoff, so a board bolted "to the face" was 1.75 m
  inside the energy absorber. Those runs now advertise on the debris fence above,
  or not at all.
* **Free-standing furniture asks for ground first.** `fit_behind` returns `None`
  where there is none, and the caller drops the object rather than being clamped
  somewhere it does not belong. That is how a TV mast ended up standing in the
  pit lane: at s = 26 the pit wall leaves 0.6 m of footing, the old clamp put the
  mast 12.7 m out, and `world_ground_z` returned `build_architecture:paving`
  171 mm below where the mast thought the ground was.
* **Tall furniture ducks the fence back stays.** `build_barriers` rakes a stay off
  every 4th–7th fence post — foot 2.45 m outboard at grade, head 3.00 m up at the
  post. The predicate is reproduced exactly (`_stay_stations`) so only the 5–7 %
  of stations that actually carry one are avoided. A first attempt applied it as
  a blanket 2.4 m lateral standoff and ate the whole 6 m platform: 13 billboards
  became 3.
* **`barrier_ok(s, side)` refuses to dress a barrier line that is not on the
  barrier.** Over 95 m of lap — s 905…938 and 1037…1060 on the left, T4 —
  `build_barriers.barrier_offset` comes out *inside* the painted verge, reaching
  **−18.80 m**, which is 18.8 m on the far side of the centreline. Its §4b deficit
  smoothing spans ±37 m, so the exclusion is padded to ±42 m. 206 placements were
  dropped there this build; it is in `placement_gate`, and it is a
  `build_barriers` number to fix.
* both bridge banners are placed from `build_architecture.py`'s own published
  numbers (La Passerelle: circuit x = −450, deck 4.0 m, soffit 7.50, truss depth
  3.05; Le Pont de la Plongée: world origin (−617.56, 94.75), heading 295.4°,
  deck 6.0 m, half-span 15.0, soffit 3.913 + 6.80, girders 1.35 m deep).
* the spec's three **declared empty zones** are enforced: `zone_cap(s, side)`
  suppresses hoardings, masts, speakers and windsocks that would break the
  helicopter arc, the doppler sight line or the Beat-6 crane-out volume, and
  demotes marshal posts to the low equipment-stand archetype inside them.
* every object is **recentred** on emit and every material reads
  `TexCoord → Object`, never `Geometry → Position`. At |P| ≈ 1000 m a
  position-driven procedural loses all its precision — this is the barrier
  module's defect #1 and it is not repeated here.

---

## Defects found by rendering, and fixed

Logged because each of them survived code review and only died in a frame.

1. **Every marshal post presented a blank wall to the camera.** The post's local
   frame had +y pointing *toward* the track, so the shelter's back wall faced the
   circuit and its open front faced the countryside. Flipped; the flag rack moved
   to the front with it.
2. **The raised-platform posts floated.** The deck was built at platform height
   and the shelter legs started at the deck underside — nothing carried it to the
   ground. Added the under-deck frame (four posts, two bearers, cross-bracing,
   pad footings) and a real stair with stringers, treads and a handrail instead
   of three disconnected floating slabs.
3. **Every black board rendered khaki.** The UV-fade mixed the print colour
   toward a fixed grey; on a near-black board that is a 40 % lift straight to
   tan. Replaced with a second saturation/value stage, so fading desaturates the
   colour it started from and black stays black.
4. **Board faces were dead flat plastic at 1.5 m.** The vinyl orange-peel and
   squeegee bump were running at ~480 cycles/m — pure sub-pixel noise that
   averages to nothing. Dropped to ~90 and ~33 cycles/m, and added the detail
   that actually identifies a trackside board: vertical rain streaks running down
   from the top edge, keyed to a 1-D noise across the board.
5. **Board rims were white-hot streaks.** The folded edge was fully metallic
   aluminium at roughness 0.2, so it mirrored the sky. Board backs and rims are
   now matte dark composite; the aluminium shader itself was dropped to
   metallic 0.82 / roughness 0.36.
6. **Tyre stacks read as coiled hose.** The first tyre added groove strips *on
   top of* a continuous crown, and cut 30 shallow notches into a 0.22 m crown.
   Rebuilt as a single revolved section with the grooves cut into the section
   itself, wider (13 % of the crown) and deeper (4–6 % of the radius).
7. **A run of seven identical-brand boards** in one frame. Runs now carry a 2–5
   brand pool with a 1–2 slot block size.
8. **Art escaped its board.** A deliberately over-scaled ghost mark hung 0.8 H
   above and below the panel. Added polygon clipping to the board rectangle.
9. **Two hoardings occupied the same 8 m of runoff.** Added 55 m minimum
   separation per side to the hoarding plan.
10. **`KESTREL LOGISTIQUE` ran off the end of its own board.** Two layouts had no
    width fit; all of them do now.
11. **The braking numerals were unreadable blobs.** The bold dilation ran at
    4.5 % of cap height on 8 offsets and merged the digits. Reduced to 1.6 % on
    12 offsets, with a 1.10 glyph-width stretch doing most of the weight.
12. **The test cameras were aimed at guessed stations and framed empty grass.**
    `build()` now records real landmark positions and the inspection framings are
    computed from them, so a macro camera is always looking at a real object.
13. **Camera pitch was inverted** in the test harness (`π/2 − atan2` instead of
    `π/2 + atan2`), so every "look down at the board" frame looked at the sky.
14. **The fence banners shredded into a z-fighting jigsaw.** The cloth carried
    12 mm wrinkles at ~20 cycles across the banner — far finer than the art
    tessellation could resolve — so the background layer and the mark layer
    interpolated to *different* surfaces between sample points and cut through
    each other. Wrinkle wavelengths lengthened to ~1 m, banner art tessellated
    to 0.14 m, and the print layer spacing raised from 1.6 mm to 2.9 mm.
15. **Every black board rendered tan (second cause).** After the colour fix they
    were still warm: a matte laminate was running at the Principled default
    specular, and the broad specular lobe of a 12.5° sun over a black diffuse
    is *all* you see. `Specular IOR Level` dropped to 0.24, and the "black" on
    the braking boards lifted from `#141416` to `#1c1f24` so it has something to
    be.
16. **Emboldened numerals turned to mush.** The 13 dilated outlines were pushed
    as one art item, so they were exactly coplanar and z-fought. Each dilation
    copy now gets its own micro-layer.

### Round 2 — found by measuring against the contract and the neighbours

17. **Every object in the module was placed by a datum that could not carry
    banking.** `ground_z(s, lat)`, unsigned. See THE CONTRACT. 77 of 260 objects
    had geometry more than 150 mm under the datum, worst 1.689 m.
18. **The print read as embossed plastic plates, and then as shredded paper.**
    Two faces of one defect. `emit_art` stacked the artwork 2.9 mm per layer,
    which at a 12.47° sun is a 13 mm cast shadow under every glyph. Dropping the
    step to 0.16 mm instead made the banner come back with **bites out of every
    letter**: each layer is tessellated independently, so each is a *different*
    piecewise-linear approximation of the same curved surface, and a chord across
    a triangle of edge L on radius R sags below it by L²/8R — which on 65 mm
    triangles over 0.15 m wrinkles is **3.5 mm**, twenty times the step. The
    original 2.9 mm was hiding it, which is also why the wrinkles had to stay at
    ~1 m wavelengths. Fixed three ways at once: the offset runs along the surface
    **normal** rather than a fixed local axis; the step is **derived**,
    `max(0.40 mm, 1.3·L²/8R)`; and the geometry is kept to curvatures a sane
    tessellation can carry (cloth R ≥ 1.2 m, board dents R ≥ 5 m) with the 5–20 mm
    creases that make cloth read as cloth moved into the **shader's** bump, where
    they cost nothing and resolve at any distance.
19. **A toppled tyre stack up to 0.45 m into the ground.** `build_tyre_stack`
    pitched it 74–106° about a fixed 0.34 m pivot, so anything past 90° drove the
    far end of a 2 m stack under grade. A stack on its side is a cylinder lying
    down: pitch 90° ± 2.5°, pivot at the real outer radius, lowest point within a
    millimetre of grade.
20. **77 objects and 207 583 triangle pairs inside the barrier.** Boards hung on
    the *declared* face rather than on the steel; tyre stacks and posts stood off
    the declared face rather than off the structure; nothing knew TecPro is 1.75 m
    thick or that fence stays exist. Measured, fixed and re-measured to
    **28 objects / 12 345 pairs**. The residual is banners against the fence they
    are cable-tied to (the tension cables occupy −0.157…+0.099 and the post
    flanges +0.104, so there is no gap between them to hang in) and boards inside
    `build_barriers`' T3/T5 clamp region.
21. **Apex boards floating 250 mm over gravel traps.** A gravel trap is a *dished
    bed*; `ground_z` describes the platform it is cut into, not its floor. Apex
    boards, gullies and painted logos are now placed against
    `C.runoff_widths(s, side)` and stay on sealed surface.
22. **The painted sponsor logos were on grass.** They were laid at
    `verge_edge + 6…14 m` with no reference to how wide the sealed runoff
    actually is. Now inside the measured asphalt band, and skipped where there is
    less than 9 m of it — which took 8 down to 5, all of them real.
23. **Marshal-post hardstandings ran through the Armco.** The pad reaches
    `padd·0.45` *inboard* of the post centre and the plan drew the post's lateral
    with no reference to it. The pad dimensions are drawn once, in `post_pad(k)`,
    and used by both the plan and the builder.
24. **The test harness was lighting these renders with a sun that does not
    exist.** 2.2 W at elevation 12.5° / rotation −58° and a 0.5 sky, graded at
    −0.35 stops: roughly 50× under key, wrong sun colour, wrong key:fill. Every
    "the boards look flat" judgement made before this was made under the wrong
    light. `_test_env` now writes `world_contract` §13 verbatim — sun 115.754 W/m²
    at (1, 0.71632, 0.38712), aerosol 0.45, ozone 1.30, AgX at −3.048 — and
    `render_tests` prints `lambert_radiance(0.18)` so the exposure can be checked
    against the contract's own published (1.6744, 1.4600, 1.3321).
25. **The board print really was a flat colour fill.** Not for want of terms:
    every one was keyed to a single scale-1.5 noise, so a 4 m board saw about one
    and a half cycles of everything and the variation read as a slow gradient.
    Printed vinyl on a race weekend is uneven at **three** scales at once — 0.6–2 m
    of uneven exposure and cleaning, 0.1–0.3 m of handling and wash, 5–20 mm of
    orange peel — plus edge grime, because the middle of a board is always its
    cleanest part. All three, and the roughness follows the colour so the
    specular breaks up with it.
26. **The 5090 was handing back blurred frames.** `tools/r5090` does not pass a
    `--dof` mode, and the worker's `restore_baseline_dof` keys on camera *names*
    from whichever scene was loaded when the baseline was captured — so a new
    blend inherits whatever the prewarm loop left. Every macro frame came back
    defocused. Rendering through `rq render --dof off` produces the same camera,
    sharp. **This is a `tools/r5090` defect, not a scene one.**

---

## Verification harness

Two scripts, both in `render/world/dressing/`, both reproducible.

```
blender -b --factory-startup -P verify_dressing.py -- \
        [--assembled] --out report.json --anchors anchors.json --blend out.blend
blender -b <assembled.blend> --factory-startup -P probe_assembled.py -- \
        --anchors anchors.json --out report.json
blender -b --factory-startup -P make_test_blend.py -- \
        --out dr_macro.blend --cams banner_macro,board_macro,... [--context]
```

`verify_dressing.py` is the gate: stage 1 against the contract, stage 2 against
the neighbours' triangles, plus the collision overlap. `probe_assembled.py` runs
stage 2 alone against a saved blend, so the placement can be iterated without
rebuilding surface and barriers each time (2.5 minutes a round). `make_test_blend.py`
writes a **few-camera** blend — the 5090 worker prewarms every camera it finds
and 19 of them once blew the readiness probe.

`render/world/dressing/verify_report.json` is the current run.

## Test renders

In `render/world/dressing/`, rendered **on the rented RTX 5090** at 2560×1440 /
768 samples through `rq render --dof off`, lit **only** by `world_contract` §13 —
which makes the frames a check on the lighting contract as well as on the
geometry. A stand-in ground ribbon stands in for the road; it is
`_test_proxy` and `build()` never emits it.

| file | what it is for |
|---|---|
| `ctx_barrier.png` | **r2, ASSEMBLED** — `build_surface` + `build_barriers` + `build_dressing` in one scene, from the runoff at s = 2530 looking down the barrier line. Boards, banners, braking boards, tyre stacks and a marshal post, all standing on the ground their neighbours actually built. This is the frame the review says nobody made. |
| `ctx_hairpin.png` | **r2, ASSEMBLED** — T4 exit at kerb height: kerb, painted verge, gravel bed, Armco and the tyre stacks behind it, showing the stacks on grade and clear of the steel |
| `repeat_hunt.png` | **the deliberate hunt for a recognisable repeat** — 90 m of the pit-straight ribbon, obliquely, at chase-camera height |
| `board_run.png` | three adjacent boards at 9 m: three brands, three layouts, three lengths |
| `board_layouts.png` | ten consecutive boards, one per layout family (CPU render, isolated) |
| `board_macro.png` | **re-rendered r2** — a barrier board at 1.55 m, 85 mm: print, fixings, rain streaks, the three-scale mottle and the edge grime |
| `banner_macro.png` | **re-rendered r2** — a fence banner at 2.1 m: hem, eyelet, cable tie, storage folds, wrinkle shading, and a print with no embossing and no tearing |
| `post_macro.png` | **re-rendered r2** — a marshal post at 6.5 m, standing on `world_contract.ground_z` with its footings in the ground |
| `tyre_macro.png` | **re-rendered r2** — a stack at 4.2 m |
| `post_platform.png` | a raised-platform post: under-deck frame, stair, handrail |
| `tyre_kinds.png` | all four tyre archetypes side by side (CPU render, isolated) |
| `marker_macro.png` | a 100 m braking board at 5 m — legibility |
| `cornersign.png` | a corner number + name plate |
| `billboard.png` | a hoarding with the barrier-board ribbon behind it |
| `bridge.png` | a bridge girder banner from the road |
| `doppler.png` | the Beat-5 hover station: the near boards are the closest the film's camera ever gets to trackside furniture, and Le Pont's banner closes the far end |
| `hairpin_out.png` | the outside of T4 from the kerb-height camera's eyeline |

Frames not marked **r2** are round-1 renders, made on the local GTX 1070 under
the old (wrong) test light and before the contract migration. They are kept only
as the before side of the comparison; nothing in this note is argued from them.

## Still open

* **28 `DR_` objects still share triangles with the barrier structure** (12 345
  pairs, down from 77 / 207 583). Most of it is banners against the fence they
  are cable-tied to: `BR_FenceWire` occupies −0.157…+0.099 relative to
  `barrier_face` and the post flanges start at +0.104, so there is no lateral
  where a banner both hangs on the fence and misses it. That is arguably contact
  rather than penetration — the distinction `tools/depth_probe.py` exists to make
  — but it has not been measured as depth, only as pairs.
* **The neighbours' ground mesh sits ~28 mm below `world_contract.ground_z`**
  (p50 over 972 anchors; p95 61 mm; worst +269 mm at s = 719 on the left). The
  anchors are on the datum to 1 mm, so this is `build_barriers`' platform and
  verge mesh against a `TOL_SEAM_M` of 10 mm.
* **`build_barriers.barrier_offset` reaches −18.80 m** over 95 m of lap at T4.
  206 placements are dropped there. Fixing it upstream gives back a marshal post
  and about 40 boards, and would close the `post_max_gap_m` regression
  (253.9 m → 338.3 m) that dropping those posts caused.
* The **flag cloth on the marshal-post flag racks** renders as plain white tubes
  — the rack builds the staves but the flags themselves are barely there. Next
  pass.
