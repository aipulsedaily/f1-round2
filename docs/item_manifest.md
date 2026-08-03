# Item manifest - the per-item asset campaign

> One row per discrete physical object a human would name. Not `barriers` - `armco_post`,
> `armco_w_beam`, `armco_splice_bolt`. An agent that owns *dressing* builds a placement
> system; an agent that owns *one trash can* builds the dent in the lid, the liner sagging
> over the rim, the drag scuffs on the base and the half-peeled sticker. This document is
> the enumeration the second kind of agent is dispatched from.

**435 items · 343 hero · 2,439,890 instances · 16 zones · 6 build waves**

Machine-readable twin: `docs/item_manifest.json` (schema `f1-round2/item_manifest/1.0`).

---

## 1. How `nearest_camera_m` was derived

This is the field that sets required fidelity, so it is measured, not guessed.

A 4,507-sample camera corridor was reconstructed from:

* `beat_sheet.json` - the 16 measured Beat-1 keys and the 8 Beat-6 keys;
* `circuit_spec.json` - the four transit legs, the doppler hover station at world
  `(-578.82, -47.47, 4.802)`, and the Beat-6 trajectory;
* `circuit_spec.md`'s **explicit Beat-5 vantage table**, which fixes where the lens is for
  every station of the lap:

| phase | stations | duration | where the lens is |
|---|---|---:|---|
| chase T1-T3 | s 0-760 | 10.7 s | dead astern sliding to outboard-alongside |
| **kerb-height hairpin pass** | s 760-1160 | 10.6 s | **STATIC on the inside kerb of T4 at z = +0.85, 21 mm lens, 4 m from the tyre wall** |
| rise + helicopter arc | s 1160-1910 | 14.6 s | climbing into the infield bowl over the esses |
| dive to the sweeper | s 1910-2403 | 7.0 s | descending outside T10/T11 |
| threshold + doppler hover | s 2403-2700 | 4.4 s | **under Le Pont de la Plongee at ~5 m altitude and 300 km/h**, then the hover at s = 2555, 26 m outboard, 2.4 m up |
| whip and catch | s 2700-3115 | 7.0 s | a 485 m straight chord that cuts inside the T12-T15 loop |
| onboard follow | s 3115-3675 | 7.1 s | tucked to the car at ~1.9 m, under La Passerelle |

`nearest_camera_m` is the minimum distance from that corridor to the item. Two consequences
are worth stating up front because they redirect a lot of effort:

1. **T12, T13 and T14 are never approached.** The whip-and-catch cuts the chord the car has
   to drive around, so those corners are only ever seen at **60-115 m** from a camera doing
   40-70 m/s. That is a real budget saving, and it is honest - the geometry says so.
2. **The Beat-6 crane-out flies over the grandstand**, clearing the roof by 13.8 m and
   passing the front top edge at ~9 m. The grandstand is not background; it is a hero
   surface seen from directly above at the end of the film.

`onscreen_px_4k = dimension_m x lens_mm x 3840 / (36 x nearest_camera_m)` at 3840x2160 on a
36 mm sensor. For flat items (paint, joints, stains, paving bays) the dimension used is the
feature's size **in plane**, not its thickness - `px_measured_dimension_m` records which.
Values are clamped at 2160 with `overfills_frame` set when the object is larger than frame.

---

## 2. Standing decisions this manifest encodes

**This is a RACE WEEKEND. The stands are full and the paddock is working.** 18,350 seats at
82 % mean occupancy = **15,050 figures** in the grandstand band, plus ~5,000 more on
general-admission banking at six corners, a full posed pit crew, an occupied pit wall,
media, recovery vehicles, and a safety car parked at the pit exit that the Beat-4 merge
goes straight past at 7.0 m.

Two consequences follow, and they partly pay for each other:

* **`grandstand_seat` is downgraded from hero.** At 82 % occupancy roughly three quarters of
  every seat is behind an occupant. What still reads from the crane-out is the aisle-end
  units, the empty seats inside the density field's gaps, the top edge of the seat back
  between shoulders, and the folded seats in the near-empty blocks. That saving is real and
  it funds part of the crowd.
* **The crowd is a massing problem, not an anatomy problem - and every note in the `crowd`
  zone says so explicitly.** The nearest seated spectator is 14.7 m: 254 px tall with a
  47 px head. At 47 px a head is a hair shape, a skin value and a suggestion of features;
  modelling eyes and mouths is wasted work that will read *worse* than a clean silhouette.
  The budget goes on posture, silhouette, headwear and the colour distribution of clothing.
  **Do not model faces.**

The one place that rule is tested is `passerelle_crowd_at_parapet` at **7.1 m** - the closest
civilians in the film. The geometry is kind: the camera is 1.9 m off the deck passing
underneath at ~230 km/h, so they are seen from a steep low angle through the anti-throw mesh
and smear 1.33 m per frame at a 180-degree shutter. What reads is forearms on the rail, chins
and hat brims, and phones held out over the parapet. Build for that view.

**Crew and marshals stay fully covered** - overall, gloves, helmet, visor, balaclava, zero
exposed skin. That is precisely why `crew_wheel_gunner` resolves cleanly at 653 px when a
bare-headed paddock figure at the same distance would not. `paddock_personnel_figure` is the
hard case (forearms, neck, face): keep it at 10 m+, in caps and sunglasses, in groups, and
never as the focal subject of a frame.

**The stand must move.** `crowd_idle_motion` is a manifest item in its own right because a
static crowd is a photograph of statues, and the camera cranes out over it in the film's
final image. It does not need much: sub-frame settling, heads turning to follow the car with
a 0.2-0.5 s spread of reaction lag, and a standing wave travelling along the stand at the
car's speed. A crowd that turns in unison is a chorus line.

**No floodlights or lighting masts inside the Beat-6 sight cone.** `circuit_spec` carries a
raycast gate that exists, in its own words, 'to protect the last image of the film from a
late-added lighting mast'. Any mast added by a per-item agent must be re-gated.

**The driver is DECIDED: yes.** See `driver_figure`, `driver_helmet`, `driver_race_suit`,
`driver_gloves`. A cockpit passing 3-5 m from a 21 mm lens with nobody in it would be the
single most glaring hole in the film. Only the helmet, shoulders, upper arms and hands are
ever visible above the cockpit rim and every one of them is covered, so no skin and no face
are required. The Beat-1 'no part seats without having been seen' law is not in conflict:
that law governs the 15 CAR clusters from the inventory, and the driver is not one of them -
he is a person who gets in, not a part that seats. The beat-sheet owner handles it; no build
agent needs to solve it.

**Invented brands only.** 31 already exist in `build_dressing`'s brand book with 698
distinct board signatures and zero duplicates; 12 are shared verbatim with
`build_architecture`. Reuse them rather than inventing a 32nd.

---

## 3. The ten to get right first

**1. `kerb_hero_t4` - T4 apex kerb (hero)**  
*0.8 m · 210 px · 1 instances · zone `kerbs_markings`*  
The static camera sits ON this kerb at z=+0.85 with a 21 mm lens while the car yaws 176 degrees in front of it for 3.9 s. A 75 mm serration is 210 px tall. Nothing else in the world is under this much scrutiny.

**2. `driver_figure` - Driver figure**  
*3.0 m · 523 px · 1 instances · zone `people`*  
DECIDED: yes. The cockpit passes 3-5 m from a 21 mm lens for 3.9 s at the hairpin and the onboard follow runs 560 m beside it. Only helmet, shoulders, arms and hands show above the rim and every one is covered - no skin, no face. The head must stay level under lateral load while the car rolls; a bolted head is worse than no driver.

**3. `glass_shard` - Glass shard**  
*0.8 m · 1167 px · 6,000 instances · zone `showroom_breach`*  
Beat 3 is the money moment of the film and it is made of these. Real thickness, conchoidal edges catching a 12.5-degree sun, and a laminate interlayer that stretches instead of snapping.

**4. `crowd_density_field` - Crowd density & occupancy field**  
*14.7 m · 254 px · 1 instances · zone `crowd`*  
The item that decides whether 15,050 grandstand occupants read as a crowd or a grid of dolls. Real crowds are lumpy - groups of 2-6 with gaps between, clear gangways, expensive rows filling first. A uniform 82 % fill is as wrong as a uniform 100 %. Nothing else in the crowd zone can be placed until this exists.

**5. `spectator_seated` - Spectator - seated**  
*14.7 m · 254 px · 7,800 instances · zone `crowd`*  
7,800 of them plus 7,250 more across the posture variants, 254 px tall at 14.7 m under the Beat-6 crane-out. A head is 47 px, so this is a MASSING problem, not an anatomy one - no faces. The budget goes on posture and silhouette: torso angle, shoulder line, knee position, where the arms are.

**6. `pont_soffit_panel` - Le Pont de la Plongee - deck soffit**  
*1.8 m · 436 px · 1 instances · zone `bridges`*  
The lens threads under this bridge with 1.8 m of clearance at 300 km/h. It fills the frame. Currently the least-considered surface in the world.

**7. `crew_wheel_gunner` - Crew - wheel gunner**  
*10.0 m · 523 px · 4 instances · zone `pit_lane`*  
653 px at 10 m, and the representative of a full posed pit crew. Four gunners, two of them mirrored not copied. Fireproofs, helmet, visor, balaclava, gloves - zero exposed skin, which is exactly why a crew resolves at this distance when a bare-headed figure would not.

**8. `gantry_soffit_panel` - Gantry soffit panel & services**  
*3.0 m · 516 px · 1 instances · zone `pit_straight`*  
The camera passes 3.0 m under the S/F gantry at 323 km/h. You only ever see the underside - cable trays, conduit, node plates - and nobody has built it.

**9. `armco_w_beam` - Armco W-beam panel**  
*2.6 m · 445 px · 1,821 instances · zone `barriers`*  
1,821 panels plus 3,641 posts is the most-repeated object trackside, and the doppler hover sits 2.6 m off it. Per-post settlement, lean and incident history is the difference between a barrier and smeared plastic.

**10. `asphalt_wearing_course` - Asphalt wearing course**  
*1.1 m · 41 px · 1 instances · zone `track_surface`*  
3,675 m of it, 1.1 m from the lens at the hairpin and 1.9 m for 560 m of onboard follow. The paver-mat joints at 9.5 m centres are the single most convincing asphalt detail there is.

Just behind them: `safety_car` (7.0 m, passed on the Beat-4 merge, a full hero road-car build), `passerelle_crowd_at_parapet` (7.1 m, the closest civilians in the film), `trash_can` (the user's own reference object), `tyre_wall_tyre` (behind the lens for the whole 176-degree yaw), `grass_clump_fescue` (directly under the doppler hover at 2.4 m) and `crowd_idle_motion` (without it the stand is a photograph of statues at the exact moment the camera cranes out).

---

## 4. Distribution

### By zone

| zone | items | hero | what it is |
|---|---:|---:|---|
| `showroom_breach` | 24 | 24 | Showroom envelope & the breach |
| `transit_corridor` | 20 | 20 | Transit corridor: glass to merge |
| `paddock` | 56 | 33 | Paddock & transporter park |
| `pit_building` | 18 | 7 | Pit building & garages |
| `pit_lane` | 58 | 49 | Pit lane & garage working furniture |
| `pit_straight` | 29 | 25 | Pit straight, S/F, gantry, footbridge |
| `grandstand` | 23 | 11 | Grandstand band |
| `track_surface` | 15 | 15 | Racing surface |
| `kerbs_markings` | 12 | 12 | Kerbs & painted markings |
| `runoff` | 11 | 11 | Runoff, gravel traps, verges |
| `barriers` | 26 | 26 | Barriers & catch fencing |
| `bridges` | 9 | 7 | Le Pont de la Plongee |
| `trackside` | 35 | 32 | Trackside dressing |
| `vegetation` | 35 | 22 | Terrain, treeline & ground cover |
| `people` | 15 | 12 | Figures |
| `crowd` | 33 | 21 | Crowd & spectator infrastructure |
| `ephemera` | 16 | 16 | The ephemeral |
| **total** | **435** | **343** | |

### By nearest-camera distance

| band | items | what that means for the builder |
|---|---:|---|
| < 2 m | 32 | macro. Bevels, micro-surface, real thickness on every edge. Nothing may be a decal. |
| 2-5 m | 103 | hero. Fasteners, seams, wear history individually readable. |
| 5-10 m | 69 | hero. Form and material must be exactly right; sub-centimetre detail can be shader. |
| 10-15 m | 115 | hero threshold. Silhouette, proportion and variation carry it. |
| 15-25 m | 83 | mid. Correct mass and correct variation; no micro-detail. |
| 25-45 m | 29 | mid-far. Silhouette and value only. |
| > 45 m | 4 | background. Mass, silhouette, aerial perspective. |

### By build wave

| wave | rule | items |
|---:|---|---:|
| 1 | Foundations and the closest heroes: <= 4 m from the lens, or depended on by >= 4 other items. | 139 |
| 2 | <= 10 m, or depended on by >= 2 other items. | 124 |
| 3 | <= 15 m - the hero threshold. | 74 |
| 4 | <= 25 m. | 81 |
| 5 | <= 45 m. | 14 |
| 6 | > 45 m - silhouette and mass only. | 3 |

Order inside a wave is by nearest-camera distance ascending, then by how many other items
depend on it. The `build_order` field in the JSON is the campaign's dispatch sequence.

---

## 5. The manifest, by zone

### `showroom_breach` - Showroom envelope & the breach

Beats 1-3 + the Beat-6 held frame. World origin, 34x26 m pavilion, glazed bay GW_Right on X=+15. The lens is inside this box for the first 44 s of the film and comes back to it as the last image.

*24 items, 24 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 1 | `showroom_floor_slab` | Showroom floor slab | 0.5 m | 448 | 1 | Y | 1 | - |
| 2 | `glass_shard` | Glass shard | 0.8 m | 1167 | 6,000 | Y | 1 | `glass_panel_prefractured` |
| 4 | `floor_shard_scatter` | Persistent floor shards inside the showroom | 1.0 m | 149 | 900 | Y | 1 | `glass_shard` |
| 11 | `curtain_wall_sill_extrusion` | Sill extrusion & base reveal | 1.3 m | 718 | 1 | Y | 1 | - |
| 12 | `dais_deck` | Turntable dais deck | 1.4 m | 907 | 1 | Y | 1 | - |
| 13 | `dais_delivery_ramp` | Dais delivery ramp | 1.4 m | 907 | 1 | Y | 1 | `dais_deck` |
| 21 | `glass_panel_prefractured` | Curtain-wall glass panel (pre-fractured) | 1.6 m | 2160+ | 10 | Y | 1 | `mullion_intact`, `curtain_wall_sill_extrusion` |
| 22 | `glazing_gasket_set` | Glazing gasket, setting blocks & silicone bead | 1.6 m | 77 | 220 | Y | 1 | `mullion_intact` |
| 20 | `mullion_intact` | Curtain-wall mullion | 1.6 m | 2160+ | 11 | Y | 1 | - |
| 26 | `exterior_ground_apron` | Exterior ground apron | 1.7 m | 2160+ | 1 | Y | 1 | - |
| 24 | `forecourt_paving_bay` | Forecourt paving bay | 1.7 m | 2160+ | 1,400 | Y | 1 | - |
| 33 | `breach_dust_ground_burst` | Ground dust burst at the breach | 2.0 m | 2160+ | 1 | Y | 1 | - |
| 35 | `concrete_spall_debris` | Concrete spall & secondary debris | 2.0 m | 149 | 400 | Y | 1 | `forecourt_paving_bay` |
| 47 | `curtain_wall_transom` | Curtain-wall transom rail | 2.5 m | 239 | 3 | Y | 1 | `mullion_intact` |
| 58 | `glass_shard_fan_settled` | Settled shard fan on the apron | 2.6 m | 431 | 1 | Y | 1 | `glass_shard`, `forecourt_paving_bay` |
| 73 | `breach_dust_column` | Breach dust column (volume) | 3.0 m | 2160+ | 1 | Y | 1 | `breach_dust_ground_burst` |
| 82 | `forecourt_bollard` | Forecourt bollard | 3.0 m | 1120 | 6 | Y | 1 | `forecourt_paving_bay` |
| 102 | `showroom_facade_panel` | Facade cladding panel (anodised) | 3.6 m | 1244 | 180 | Y | 1 | - |
| 108 | `mullion_bent_stub` | Bent mullion stub (survivor) | 3.8 m | 2160+ | 2 | Y | 1 | `mullion_intact` |
| 125 | `showroom_signage_lettering` | Facade signage (invented marque) | 4.0 m | 560 | 1 | Y | 1 | `showroom_facade_panel` |
| 128 | `wall_stud_framing` | Wall framing behind the glazing | 4.0 m | 2160+ | 1 | Y | 1 | - |
| 145 | `curtain_wall_head_extrusion` | Head extrusion | 4.7 m | 175 | 1 | Y | 2 | - |
| 150 | `showroom_rainwater_goods` | Downpipe, hopper & gutter | 5.0 m | 2160+ | 8 | Y | 2 | `showroom_facade_panel` |
| 205 | `showroom_parapet_coping` | Parapet coping | 9.0 m | 83 | 1 | Y | 2 | `showroom_facade_panel` |

**`showroom_floor_slab`**  
*varies by:* polish sheen; joint grid; reflection of the exploded field  
30.0 x 22.0 m, top z=0.000 exactly - same plane as the paddock apron and the pit straight. Round-1 geometry, transform IDENTITY. In Beat 1 it is the mirror every part is presented against.

**`glass_shard`**  
*varies by:* size 8 mm - 900 mm; tumble; edge chipping; laminate interlayer still bridging two plates on ~15 % of shards  
The money object of Beat 3. Must have real thickness, ground edges catching the low sun, and an interlayer that stretches rather than snaps on the laminated fraction. Wrong version: flat triangles with no thickness - they vanish edge-on and the field reads as confetti.

**`floor_shard_scatter`**  
*varies by:* size; slide distance from the wall; upturned vs flat  
Continuity requirement: if the camera ever sees the showroom again it is wounded. These stay for the rest of the film.

**`curtain_wall_sill_extrusion`**  
*varies by:* weathering at the drainage slots; scuffing at the threshold  
The camera passes over this at 1.3 m on the way out. Pressure-equalised sill with weep slots and setting blocks visible where glass is gone.

**`dais_deck`**  
*varies by:* brushed-finish direction; tyre scuff from the launch; ring joint wear  
7.4 m diameter platform, 6.9 m deck, top z=+0.340. Ride height is 0.340 m - the deck top and the car's floor are the same number, which is the scale key for the whole showroom.

**`dais_delivery_ramp`**  
*varies by:* surface grip texture; edge chamfer wear  
NEW BUILD, explicitly called out in circuit_spec: 0.340 m rise over 2.60 m (13.1 %), full 3.0 m width, X=+3.70 to +6.30. Without it the car steps off a 340 mm cliff at launch.

**`glass_panel_prefractured`**  
*varies by:* shard size gradient (fine at impact, coarse at edges); pane number; residual sealant on edges  
2.125 x 5.980 m, laminated. Cell-fracture with the seed density falling off from the launch axis Y=0. Wrong version: uniform Voronoi across the whole pane - real toughened glass dices near the strike and holds slabs at the frame. Edges must be conchoidal and thickness-visible (10-12 mm), not zero-thickness planes.

**`glazing_gasket_set`**  
*varies by:* compression set; torn tails where glass left; dust line  
EPDM wedge gasket + structural silicone. At 1.6 m on a 58 mm lens a 20 mm gasket is ~130 px - the seam between glass and metal must be a real detail, not a shared vertex.

**`mullion_intact`**  
*varies by:* anodising tone; fixing wear; dust in the channel  
0.075 x 0.160 x 6.200 m at 2.20 m centres; one sits exactly on the launch axis Y=0. Extruded aluminium: thermal break, screw ports, gasket races. Wrong version: a plain box.

**`exterior_ground_apron`**  
Round-1 ExteriorGround must be re-levelled from z -0.14..-0.08 to EXACTLY 0.000 over world X 10..90, Y -40..+40, blended over a further 20 m. A 140 mm step here is a visible kerb the car jumps.

**`forecourt_paving_bay`**  
*varies by:* saw-cut vs formed joint; weed colonisation ~18 %; 2.4 % reinstated in asphalt; stain  
The apron the car lands on. Bay module and joint pattern must survive a 1.7 m lens - a single unbroken slab reads as lino.

**`breach_dust_ground_burst`**  
*varies by:* burst radius; rebound roll  
Driven by the sim contact frame, not hand-timed.

**`concrete_spall_debris`**  
*varies by:* size; skitter distance; dust coating  
Skitters across the concrete outside. Reads as the wall having structure behind the glass.

**`curtain_wall_transom`**  
3 transoms full width. Must fracture with the assembly.

**`glass_shard_fan_settled`**  
*varies by:* density falls with distance from the wall; sweep lines where debris skittered; sun glitter  
40+ m fan in front of the wall; must still be there in Beat 6 where it reads as a ~140 px glitter band at 595 m. Continuity: the world is wounded for the rest of the film.

**`breach_dust_column`**  
*varies by:* density decay over 90 s; drift on the 65 deg wind  
20-25 m column, still settling 90 s later so it is present in the Beat-6 hold. Must be a LOCAL volume: the global haze slabs have visible_shadow=False and cast no god rays.

**`forecourt_bollard`**  
*varies by:* impact scuff; base grout; cap dent  
At world X=19.5, Y=+/-9.0. Cast or stainless sleeve over a core; the car threads between them.

**`showroom_facade_panel`**  
*varies by:* anodising batch drift between panels; oil-canning; fixing shadow gaps  
Reads as 33 px of facade at the Beat-6 hold (595 m) but at 3.6 m in Beat 4. The panel joint rhythm is the only thing that gives the building scale at both ends.

**`mullion_bent_stub`**  
*varies by:* bend angle; tear at the fixing; torn gasket tails; paint craze at the plastic hinge  
The two at Y=+/-4.4 survive the 9.6 m aperture as bent stubs. Plastic hinge with local buckling of the extrusion walls - not a smooth bend. This is the object that tells the audience how big the hole is.

**`showroom_signage_lettering`**  
*varies by:* halo-lit vs flat; grime shadow behind the letters  
Invented brand only. No real marque. Must read at 4 m in Beat 4 and survive being 2 px wide in Beat 6.

**`wall_stud_framing`**  
*varies by:* twist; fastener pull-through  
Must pre-fracture with the wall - the brief says 'plus wall framing'. Exposed studwork inside the wound in Beats 4 and 6.

**`curtain_wall_head_extrusion`**  
21.919 m of head. Carries the panels' top edge; tears out where the aperture forms.

**`showroom_rainwater_goods`**  
*varies by:* staining below the hopper; bracket rust  
Cheap to build, and the thing whose absence makes a building read as a box.

**`showroom_parapet_coping`**  
*varies by:* drip edge staining  
Parapet at z=+10.40 - the silhouette line in the Beat-6 held frame.

---

### `transit_corridor` - Transit corridor: glass to merge

The 244.3 m access ribbon, world X=+15 to the pit-exit merge at (161.02, 35.09). Four thresholds in 5.6 s: breach plane, walled corridor, portal at X=+58, pit-wall line, blend line. Camera crosses all of it.

*20 items, 20 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 5 | `pit_exit_portal_sign` | Portal signage & gate number | 1.0 m | 2160+ | 4 | Y | 1 | `pit_exit_portal_frame` |
| 14 | `pit_exit_portal_frame` | Pit-exit portal frame | 1.5 m | 2160+ | 1 | Y | 1 | `access_road_slab` |
| 25 | `access_road_saw_joint` | Saw-cut joint & sealant | 1.7 m | 73 | 240 | Y | 1 | `access_road_slab` |
| 23 | `access_road_slab` | Access-road concrete slab | 1.7 m | 2160+ | 1 | Y | 1 | - |
| 31 | `apron_wall_coping` | Apron wall coping & oversail | 1.8 m | 550 | 30 | Y | 1 | `apron_wall_panel` |
| 29 | `apron_wall_panel` | Apron retaining wall panel (north) | 1.8 m | 2160+ | 30 | Y | 1 | - |
| 34 | `apron_wall_weep_pipe` | Weep pipe & staining | 2.0 m | 186 | 24 | Y | 1 | `apron_wall_panel` |
| 37 | `portal_boom_gate` | Portal boom gate (raised) | 2.0 m | 224 | 1 | Y | 1 | `pit_exit_portal_frame` |
| 46 | `cone_connector_bar` | Cone connector bar | 2.5 m | 75 | 60 | Y | 1 | `traffic_cone` |
| 45 | `traffic_cone` | Traffic cone | 2.5 m | 1120 | 180 | Y | 1 | - |
| 67 | `access_road_kerb` | Access-road kerb unit | 3.0 m | 187 | 400 | Y | 1 | `access_road_slab` |
| 75 | `cable_ramp` | Heavy rubber cable ramp | 3.0 m | 112 | 26 | Y | 1 | - |
| 86 | `heras_banner_scrim` | Fence banner scrim | 3.0 m | 2160+ | 320 | Y | 1 | `heras_fence_panel` |
| 87 | `heras_fence_coupler` | Heras coupler clamp | 3.0 m | 186 | 900 | Y | 1 | `heras_fence_panel` |
| 88 | `heras_fence_foot` | Heras fence foot block | 3.0 m | 187 | 950 | Y | 1 | `heras_fence_panel` |
| 62 | `heras_fence_panel` | Temporary (Heras) fence panel | 3.0 m | 2160+ | 900 | Y | 1 | - |
| 101 | `transit_debris_fence` | Transit debris fence (over the tyre wall) | 3.5 m | 2160+ | 1 | Y | 1 | `catch_fence_mesh_panel`, `transit_tyre_wall_stack` |
| 96 | `transit_tyre_wall_stack` | Transit tyre wall (south) | 3.5 m | 2133 | 1 | Y | 1 | `tyre_wall_tyre`, `tyre_wall_belt_facing` |
| 113 | `access_road_gully` | Road gully & grating | 4.0 m | 560 | 14 | Y | 1 | `access_road_kerb` |
| 123 | `jersey_barrier` | Jersey barrier unit | 4.0 m | 840 | 120 | Y | 1 | - |

**`pit_exit_portal_sign`**  
*varies by:* invented brand; sun-fade; fixing rust  
Legible at 1.0 m. Invented names only.

**`pit_exit_portal_frame`**  
*varies by:* paint chipping at the jambs; height-restriction plate  
At world X=+58, clear width 2.6 m margin. THE CAMERA PASSES THROUGH IT - closest approach 0.0 m. Whatever this is made of will fill the frame for two frames at 4K.

**`access_road_saw_joint`**  
*varies by:* sealant age; spalled arris; weed  
The rhythm that tells you it is concrete and not tarmac at 1.7 m.

**`access_road_slab`**  
*varies by:* pour-bay joints; broom-finish direction; unrubbered (mu 0.90) so it stays pale  
12.0 m wide, 244.3 m long; the first 49.6 m is DEAD FLAT at z=0.000. Unrubbered concrete: it must not carry the track's rubber line. Wrong version: same asphalt shader as the circuit.

**`apron_wall_coping`**  
*varies by:* drip groove; chipped corners  
0.16 m coping oversail. Reads as a hard sunlit line the whole length of the corridor.

**`apron_wall_panel`**  
*varies by:* board-mark / cut-face texture; pour-lift lines; efflorescence; graffiti-free but stained  
2.40 m cut-faced concrete at +8.0 m offset over the middle 90 m. The camera passes 1.8 m from it at ~130 km/h - form-tie holes and lift lines are what stop it looking like grey plastic.

**`apron_wall_weep_pipe`**  
*varies by:* stain length; blockage  
Every 4th panel. Tiny, and it is the detail that dates the wall.

**`portal_boom_gate`**  
*varies by:* counterweight; reflective banding wear  
Parked up. Tells you the corridor is normally closed.

**`cone_connector_bar`**  
*varies by:* sag; missing bar leaving orphan cones  

**`traffic_cone`**  
*varies by:* lean; base grit; crushed/split top; reflective collar age; 3 sizes  
Nothing says placeholder like a perfect cone standing perfectly upright. At least 20 % must be leaning, scuffed or knocked flat.

**`access_road_kerb`**  
*varies by:* unit length; settlement step; scuffed arris  
Half-battered kerb, dropped at the crossings. Individual units, not an extruded ribbon.

**`cable_ramp`**  
*varies by:* lid open/closed; cable count inside; tyre-crush deformation; yellow wear  
The single most paddock-looking object there is. Must deform where vehicles cross it.

**`heras_banner_scrim`**  
*varies by:* invented brand; wind-torn eyelets; sag; sun bleach on the south face  
On ~35 % of panels. Must sag between ties and flap-crease, not stretch flat.

**`heras_fence_coupler`**  
*varies by:* missing on ~8 % of joints  

**`heras_fence_foot`**  
*varies by:* cracked concrete; mud  

**`heras_fence_panel`**  
*varies by:* 4.5 % missing; panel lean; mesh dent; galvanising bloom  
3.5 x 2.0 m. Perimeter plus 3 internal runs. The lean and the gaps are the whole read.

**`transit_debris_fence`**  
*varies by:* mesh tension; post lean  
Reaches 4.30 m total. Backlit by the low sun for the whole corridor run.

**`transit_tyre_wall_stack`**  
*varies by:* tyre age mix; belt tension; sag between bolts  
2.00 m stack at -7.0 m offset over 84 m. South clearance narrows to 1.737 m at route t=90 - the camera is close to this.

**`access_road_gully`**  
*varies by:* 1 in 7 sits ~16 mm low, 1 in 11 lifted; silt level  
Cast frame with a 14 mm rebate ring. The recess is the detail; a flush grating reads as a decal.

**`jersey_barrier`**  
*varies by:* 30 % carry a brand panel; lifting-eye rust; chipped nose  

---

### `paddock` - Paddock & transporter park

Circuit x -480..+100, y 40.5..115 (580 x 74.5 m). Only ~6 % of it is inside 15 m of the lens - the corridor along the Beat-4 route (circuit x -360..-280) plus the showroom surround. The rest is 40-90 m background.

*56 items, 33 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 129 | `paddock_paving_bay` | Paddock paving bay | 4.6 m | 812 | 5,560 | Y | 1 | - |
| 191 | `paddock_duct_cover` | Cable duct cover | 8.0 m | 187 | 140 | Y | 2 | `paddock_paving_bay` |
| 192 | `paddock_manhole_cover` | Manhole cover | 8.0 m | 280 | 120 | Y | 2 | `paddock_paving_bay` |
| 193 | `paddock_slot_drain` | Slot drain & grating | 8.0 m | 233 | 80 | Y | 2 | `paddock_paving_bay` |
| 186 | `team_truck_tractor` | Team truck tractor unit | 8.0 m | 1820 | 10 | Y | 2 | `truck_wheel_steer`, `truck_tyre` |
| 133 | `team_truck_trailer` | Team truck trailer | 8.0 m | 1867 | 10 | Y | 1 | `truck_wheel_trailer` |
| 198 | `truck_light_cluster` | Truck light cluster & marker lamps | 8.0 m | 155 | 140 | Y | 2 | `team_truck_trailer` |
| 199 | `truck_livery_decal` | Truck livery decal panel | 8.0 m | 933 | 20 | Y | 2 | `team_truck_trailer` |
| 200 | `truck_mirror_arm` | Mirror arm & head | 8.0 m | 387 | 20 | Y | 2 | `team_truck_tractor` |
| 201 | `truck_mud_flap` | Mud flap | 8.0 m | 257 | 60 | Y | 2 | `truck_wheel_trailer` |
| 202 | `truck_side_skirt` | Trailer side skirt panel | 8.0 m | 420 | 60 | Y | 2 | `team_truck_trailer` |
| 185 | `truck_tyre` | Truck tyre | 8.0 m | 490 | 220 | Y | 2 | - |
| 189 | `truck_wheel_steer` | Steer wheel & hub | 8.0 m | 490 | 40 | Y | 2 | `truck_tyre` |
| 187 | `truck_wheel_trailer` | Trailer wheel & twin set | 8.0 m | 490 | 120 | Y | 2 | `truck_tyre` |
| 188 | `water_bottle` | Water bottle | 8.0 m | 186 | 300 | Y | 2 | - |
| 206 | `truck_air_line_coil` | Suzie coil & electrical line | 9.0 m | 344 | 20 | Y | 2 | `team_truck_tractor` |
| 207 | `truck_landing_leg` | Trailer landing leg | 9.0 m | 456 | 20 | Y | 2 | `team_truck_trailer` |
| 212 | `bin_liner` | Bin liner | 10.0 m | 186 | 40 | Y | 2 | `trash_can`, `wheelie_bin` |
| 216 | `trash_can` | Trash can (paddock bin) | 10.0 m | 355 | 40 | Y | 2 | - |
| 241 | `truck_loading_ramp` | Trailer loading ramp | 10.0 m | 37 | 8 | Y | 2 | `truck_rear_door` |
| 217 | `truck_rear_door` | Trailer rear door leaf | 10.0 m | 1344 | 20 | Y | 2 | `team_truck_trailer` |
| 242 | `water_bottle_crate` | Water bottle crate | 10.0 m | 131 | 40 | Y | 2 | `water_bottle` |
| 218 | `wheelie_bin` | Wheelie bin | 10.0 m | 411 | 90 | Y | 2 | - |
| 286 | `flight_case` | Flight case | 12.0 m | 280 | 120 | Y | 3 | - |
| 289 | `jerry_can` | Jerry can | 12.0 m | 146 | 20 | Y | 3 | - |
| 290 | `pallet_stack` | Pallet stack | 12.0 m | 436 | 60 | Y | 3 | - |
| 302 | `cable_reel_drum` | Cable reel drum | 14.0 m | 267 | 24 | Y | 3 | - |
| 307 | `fuel_drum` | Fuel drum | 14.0 m | 235 | 24 | Y | 3 | - |
| 309 | `generator_unit` | Generator unit | 14.0 m | 427 | 16 | Y | 3 | `power_distribution_board` |
| 311 | `paddock_avenue_tree` | Paddock avenue tree | 14.0 m | 2160+ | 24 | Y | 3 | `tree_london_plane` |
| 303 | `paddock_planter` | Paddock planter box | 14.0 m | 240 | 34 | Y | 3 | - |
| 312 | `planter_shrub` | Planter shrub | 14.0 m | 213 | 34 | Y | 3 | `paddock_planter` |
| 304 | `power_distribution_board` | Power distribution board | 14.0 m | 293 | 30 | Y | 3 | `cable_reel_drum` |
| 346 | `finger_post_sign` | Wayfinding finger post | 16.0 m | 607 | 8 |   | 4 | - |
| 347 | `fire_point_station` | Fire point station | 16.0 m | 350 | 4 |   | 4 | `fire_extinguisher_handheld` |
| 349 | `gas_bottle` | Gas bottle | 16.0 m | 327 | 60 |   | 4 | `gas_bottle_cage` |
| 344 | `gas_bottle_cage` | Gas bottle cage | 16.0 m | 443 | 10 |   | 4 | - |
| 354 | `water_tank_ibc` | IBC water tank | 16.0 m | 280 | 12 |   | 4 | - |
| 364 | `pallet_truck` | Pallet truck | 18.0 m | 249 | 6 |   | 4 | - |
| 365 | `skip_container` | Skip container | 18.0 m | 270 | 8 |   | 4 | - |
| 368 | `awning_leg` | Awning leg, foot & guy line | 20.0 m | 560 | 60 |   | 4 | - |
| 373 | `forklift_truck` | Forklift truck | 20.0 m | 411 | 4 |   | 4 | - |
| 379 | `hospitality_awning` | Hospitality awning canopy | 20.0 m | 560 | 10 |   | 4 | `awning_leg` |
| 381 | `motorhome_unit` | Motorhome / hospitality unit | 20.0 m | 784 | 5 |   | 4 | `hospitality_deck` |
| 382 | `paddock_gate` | Paddock gate / turnstile | 20.0 m | 411 | 6 |   | 4 | `heras_fence_panel` |
| 392 | `folding_chair` | Folding chair | 22.0 m | 144 | 90 |   | 4 | `hospitality_deck` |
| 393 | `folding_table` | Folding table | 22.0 m | 127 | 30 |   | 4 | `hospitality_deck` |
| 139 | `hospitality_deck` | Hospitality deck platform | 22.0 m | 102 | 5 |   | 1 | - |
| 401 | `parasol` | Parasol | 22.0 m | 441 | 14 |   | 4 | `hospitality_deck` |
| 408 | `catering_counter` | Catering counter unit | 25.0 m | 164 | 4 |   | 4 | - |
| 406 | `lighting_mast` | Lighting mast column | 25.0 m | 1792 | 11 |   | 4 | - |
| 411 | `lighting_mast_head` | Lighting mast head | 25.0 m | 90 | 55 |   | 4 | `lighting_mast` |
| 426 | `hospitality_building` | Modular hospitality unit | 30.0 m | 809 | 5 |   | 5 | - |
| 432 | `race_control_building` | Race control building | 45.0 m | 747 | 1 |   | 5 | - |
| 433 | `media_centre_building` | Media centre | 55.0 m | 475 | 1 |   | 6 | - |
| 434 | `medical_centre_building` | Medical centre | 55.0 m | 373 | 1 |   | 6 | - |

**`paddock_paving_bay`**  
*varies by:* sawn vs formed; 18 % weed joints; 2.4 % asphalt reinstatement; oil staining; wheel-track polish  
5,560 bays over 49,645 m2. Bay-to-bay height variation must stay inside +/-15 mm - measured max is +14.8 mm today, and the tolerance is 15.5 mm.

**`paddock_duct_cover`**  
*varies by:* 1 in 13 proud; checker-plate wear  

**`paddock_manhole_cover`**  
*varies by:* round vs rectangular; 14 mm rebate ring; lifting keyholes; wear pattern  

**`paddock_slot_drain`**  
*varies by:* 1 in 7 sits 16 mm low, 1 in 11 lifted; silt  

**`team_truck_tractor`**  
*varies by:* cab family (2); roof pod count 1-4; livery; mirror set; grille bug strike; wash line on the lower panels  
The 'haul' the user named. Cab glazing must have real thickness and interior behind it - at 8 m an empty black cab reads as a toy.

**`team_truck_trailer`**  
*varies by:* 12.6-14.6 m length; livery; side-skirt scuffs; roof-edge grime streaks; door open/closed  
A 14 m flank at 8 m is 2/3 of the frame height. It cannot be a coloured box - it needs panel joints, rivet lines, kick plates, dirt gradient rising from the road.

**`truck_light_cluster`**  
*varies by:* lens crazing; one out  

**`truck_livery_decal`**  
*varies by:* invented brands only; edge lifting; wash marks; over-panel wrap seams  
NO real teams, NO real sponsors. Wrap seams over rivets are what make a wrap read as a wrap.

**`truck_mud_flap`**  
*varies by:* invented brand text; curl; road-spray staining; torn corner; hanging angle  
User-named. It must HANG - a flat rectangle at 90 degrees is the tell.

**`truck_side_skirt`**  
*varies by:* dent; missing panel; road-film gradient  

**`truck_tyre`**  
*varies by:* tread pattern (steer rib vs drive block); wear depth; sidewall lettering; kerb scrub; stone in the tread  
The user named this one explicitly. 315/70R22.5, ~1.05 m OD. Sidewall lettering must be RAISED geometry or a real displacement, and the tread must be modelled, not bumped - at 8 m a bumped tread reads as a sticker.

**`truck_wheel_steer`**  
*varies by:* alloy vs steel; polished vs painted; brake dust; missing nut indicator  
Wheel nut indicators (the little yellow arrows) are the detail people recognise without knowing why.

**`truck_wheel_trailer`**  
*varies by:* twin spacing; rust bloom on steel rims; hub-cap present/absent  

**`water_bottle`**  
*varies by:* fill level; label peel; crushed vs whole; cap on/off; condensation  
User-named. 112 px at 8 m on a 35 mm lens. Fill level and a slightly crushed body are the whole job - a rigid full cylinder is the placeholder.

**`truck_air_line_coil`**  
*varies by:* coil pitch; connected/hung  

**`truck_landing_leg`**  
*varies by:* extended/retracted; crank handle position; foot pad on a spreader  

**`bin_liner`**  
*varies by:* sag depth; knot; tuck under the rim; colour  
Cloth-sim or sculpted sag over the rim. A liner that ends flush with the rim is the placeholder tell.

**`trash_can`**  
*varies by:* dent in the lid; liner sagging over the rim; drag scuffs on the base; half-peeled sticker; fill level  
THE reference object for this whole campaign - the user named it by name. 296 px tall at 12 m. Every one of the four named details must be present and must differ between instances.

**`truck_loading_ramp`**  
*varies by:* deployed/stowed; checker-plate wear  

**`truck_rear_door`**  
*varies by:* open/closed; cam-lock hardware; interior visible when open  

**`water_bottle_crate`**  
*varies by:* full/part/empty; stacked 1-4; crate colour  

**`wheelie_bin`**  
*varies by:* 4 sizes; lid open/closed/missing; body scuffs and heat-warp; wheel grime; overfilled  
User-named class. The dent in the lid and the drag scuffs on the base are the brief.

**`flight_case`**  
*varies by:* stacked 1-3; ball-corner wear; latch state; stencilled team text; castor grime  
Butterfly latches, ball corners and extruded edging. The edging profile is the object.

**`jerry_can`**  
*varies by:* colour code; spout stowed; dent  

**`pallet_stack`**  
*varies by:* 2-9 high; block vs stringer; broken deck boards; nail heads proud; forklift damage  

**`cable_reel_drum`**  
*varies by:* wound/part-wound; timber vs steel; cable spill on the ground  

**`fuel_drum`**  
*varies by:* steel vs plastic; bung state; rust ring at the base; hazard label  

**`generator_unit`**  
*varies by:* size class; exhaust soot; door open; fuel line; running (heat shimmer)  
Acoustic canopy with louvres and a lifting frame. Exhaust staining above the outlet is the detail.

**`paddock_avenue_tree`**  
*varies by:* 11.8-19.6 m; 3 gaps in the row; 2 young replacements; +/-0.9 m spacing jitter  
Built at L0. The 2 young replacements in a row of mature trees is the detail that makes a planted avenue read as maintained rather than generated.

**`paddock_planter`**  
*varies by:* timber vs metal; soil level; watering stain  

**`planter_shrub`**  
*varies by:* species; 3-6 stems; leaf loss; pruning shape  
Known gap: the 5 shrub species all come from ONE generator with different parameters. This is the layer flagged for rebuild if the lens gets inside 15 m - it does, here.

**`power_distribution_board`**  
*varies by:* cable count; socket covers open; warning label  

**`finger_post_sign`**  
*varies by:* 2-4 arms from an 8-destination table; arm droop; post lean  

**`fire_point_station`**  
*varies by:* extinguisher count; signage fade; bracket rust  

**`gas_bottle`**  
*varies by:* colour code; valve cap present; scuff ring at the base  

**`gas_bottle_cage`**  
*varies by:* full/empty mix; chain; hazard placard  

**`water_tank_ibc`**  
*varies by:* fill level (translucent); cage rust; pallet base damage  

**`skip_container`**  
*varies by:* fill contents; rust runs; chain hooks; dented side  

**`forklift_truck`**  
*varies by:* mast height; fork position; hydraulic staining; seat wear  

**`hospitality_awning`**  
*varies by:* fabric sag; rain pooling; branded valance; tension wrinkles at the poles  
Fabric must sag and crease. A flat quad is the classic placeholder.

**`motorhome_unit`**  
*varies by:* deployed slide-outs; awning out/in; deck attached  

**`paddock_gate`**  
*varies by:* open/closed; accreditation signage  

**`folding_chair`**  
*varies by:* tucked/pushed out/tipped; fabric sling sag; stacked  
Chairs pushed in at identical angles is the single most common CG-crowd-furniture failure.

**`folding_table`**  
*varies by:* cloth on/off; leg splay; top scuff  

**`hospitality_deck`**  
*varies by:* board gaps; step nosing wear; edge trim  

**`parasol`**  
*varies by:* open / furled / absent; canopy sag; branded valance  

**`lighting_mast`**  
*varies by:* 4 heights; base enclosure on ~half; galvanising weathering  
CAUTION: circuit_spec's Beat-6 raycast gate exists specifically 'to protect the last image of the film from a late-added lighting mast'. Any mast within the south-apron or grandstand sight cone must be re-gated.

**`lighting_mast_head`**  
*varies by:* 3-6 heads on independent yaw; lens crazing  

**`hospitality_building`**  
*varies by:* module count; balcony; glazing tint; branded fascia  

**`race_control_building`**  
*varies by:* glazing reflection; roof plant; aerial array  
Deliberately separate from the modular system.

**`medical_centre_building`**  
*varies by:* ambulance bay; red-cross signage  

---

### `pit_building` - Pit building & garages

14 bays at 22 m, circuit x -245..+75, y 23.5..40.5, roof z +12.0. Seen from Beat 4 (west bays at 10-17 m) and across the pit lane on the onboard follow (20-25 m).

*18 items, 7 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 267 | `garage_door_roller` | Garage door - roller shutter | 10.7 m | 1570 | 4 | Y | 3 | `garage_door_guide_rail` |
| 275 | `garage_bay_number` | Garage bay number sign | 11.0 m | 136 | 14 | Y | 3 | `garage_facade_panel` |
| 244 | `garage_door_guide_rail` | Door guide rail & head gear | 11.0 m | 1629 | 14 | Y | 2 | - |
| 245 | `garage_facade_panel` | Garage facade panel | 11.0 m | 679 | 300 | Y | 2 | - |
| 276 | `garage_pier` | Garage pier / column between bays | 11.0 m | 1629 | 15 | Y | 3 | `garage_facade_panel` |
| 308 | `garage_door_sectional` | Garage door - sectional | 14.0 m | 1200 | 4 | Y | 3 | `garage_door_guide_rail` |
| 348 | `garage_door_concertina` | Garage door - concertina | 16.0 m | 1050 | 3 |   | 4 | - |
| 357 | `pit_building_west_gable` | Pit building west gable | 17.1 m | 2160+ | 1 | Y | 4 | - |
| 361 | `garage_door_overhead` | Garage door - overhead canopy | 18.0 m | 933 | 3 |   | 4 | - |
| 375 | `garage_awning` | Pit-lane garage awning | 20.0 m | 37 | 14 |   | 4 | - |
| 261 | `garage_interior_floor` | Garage interior floor | 22.0 m | 170 | 14 |   | 2 | - |
| 391 | `garage_light_batten` | Garage light batten | 22.0 m | 20 | 110 |   | 4 | `garage_interior_floor` |
| 402 | `pit_building_soffit` | Soffit & fascia | 22.0 m | 102 | 1 |   | 4 | - |
| 404 | `pit_building_window_band` | Upper window band | 24.0 m | 280 | 1 |   | 4 | - |
| 414 | `pit_building_stair_core` | External stair core | 25.0 m | 1792 | 2 |   | 4 | - |
| 419 | `garage_rear_door` | Garage rear door to the paddock | 26.0 m | 316 | 14 |   | 5 | - |
| 430 | `pit_building_balustrade` | Roof balustrade | 31.0 m | 132 | 1 |   | 5 | `pit_building_roof_deck` |
| 263 | `pit_building_roof_deck` | Pit building roof deck | 31.0 m | 36 | 1 |   | 2 | - |

**`garage_door_roller`**  
*varies by:* open height (0-100 %); slat dent; guide-rail grime; bottom-rail scuff  
One of four door FAMILIES - they are four different meshes, not four colours. Slat curvature and the curl at the head are the read.

**`garage_bay_number`**  
*varies by:* invented team name; mounting height drift; fade  

**`garage_door_guide_rail`**  
*varies by:* grease line; fixing rust  

**`garage_facade_panel`**  
*varies by:* panel joint; anodising drift; impact scuff at vehicle height  

**`garage_pier`**  
*varies by:* corner protector; scuff  

**`garage_door_sectional`**  
*varies by:* open height; panel joint shadow; vision-light row  

**`garage_door_concertina`**  
*varies by:* fold state; hinge wear  

**`pit_building_west_gable`**  
*varies by:* cladding; louvre bank; access door; downpipe  
The car threads past this on the merge. It is the biggest single object in the Beat-4 frame after the showroom.

**`garage_door_overhead`**  
*varies by:* canopy projection; counterbalance arm  

**`garage_awning`**  
*varies by:* deployed/retracted; fabric sag  

**`garage_interior_floor`**  
*varies by:* epoxy sheen; tyre marks; drain line; team floor graphic  
Seen at 20-25 m through open doors. Dark and empty is a defect; the floor graphic and the sheen carry it.

**`garage_light_batten`**  
*varies by:* on/off; diffuser yellowing  
Interior practicals must stay lit - the light spilling out of an open bay is what says 'occupied'.

**`pit_building_soffit`**  
*varies by:* staining; vent strip  

**`pit_building_window_band`**  
*varies by:* reflection; blind position varies per bay; one open  
Blinds at identical heights across 14 bays is the tell.

**`pit_building_stair_core`**  
*varies by:* open riser; handrail; landing  

**`garage_rear_door`**  
*varies by:* open/closed  

**`pit_building_balustrade`**  
*varies by:* post pitch; infill mesh vs glass  

**`pit_building_roof_deck`**  
*varies by:* plant units; walkway; edge upstand  
Roof at z=+12.0 - in frame for the whole Beat-6 climb.

---

### `pit_lane` - Pit lane & garage working furniture

12 m wide, circuit y 11.5..23.5, x -245..+130. Never closer than ~10 m; read at 10-25 m. Must be legible and correct, not micro-detailed.

*58 items, 49 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 182 | `safety_car` | Safety car | 7.0 m | 773 | 1 | Y | 2 | `safety_car_light_bar` |
| 179 | `safety_car_light_bar` | Safety car light bar | 7.0 m | 85 | 2 | Y | 2 | - |
| 134 | `crew_fireproof_overall` | Crew fireproof overall | 10.0 m | 653 | 110 | Y | 1 | - |
| 220 | `crew_gloves_and_boots` | Crew gloves & boots | 10.0 m | 112 | 110 | Y | 2 | `crew_fireproof_overall` |
| 221 | `crew_helmet_visor` | Crew helmet, visor & balaclava | 10.0 m | 105 | 60 | Y | 2 | `crew_fireproof_overall` |
| 222 | `crew_jack_operator_front` | Crew - front jack operator | 10.0 m | 597 | 1 | Y | 2 | `crew_fireproof_overall`, `pit_jack_front` |
| 223 | `crew_jack_operator_rear` | Crew - rear jack operator | 10.0 m | 597 | 1 | Y | 2 | `crew_fireproof_overall`, `pit_jack_rear` |
| 224 | `crew_release_operator` | Crew - release / stop-go operator | 10.0 m | 672 | 1 | Y | 2 | `crew_fireproof_overall`, `stop_go_board` |
| 225 | `crew_stabiliser` | Crew - side stabiliser | 10.0 m | 560 | 2 | Y | 2 | `crew_fireproof_overall` |
| 226 | `crew_tyre_carrier_off` | Crew - tyre carrier (off) | 10.0 m | 560 | 4 | Y | 2 | `crew_fireproof_overall`, `tyre_blanket` |
| 227 | `crew_tyre_carrier_on` | Crew - tyre carrier (on) | 10.0 m | 560 | 4 | Y | 2 | `crew_fireproof_overall`, `tyre_blanket` |
| 228 | `crew_wheel_gunner` | Crew - wheel gunner | 10.0 m | 523 | 4 | Y | 2 | `crew_fireproof_overall`, `wheel_gun` |
| 230 | `engineer_on_timing_stand` | Engineer on the timing stand | 10.0 m | 560 | 40 | Y | 2 | `timing_stand`, `timing_stand_monitor` |
| 211 | `fire_extinguisher_handheld` | Handheld fire extinguisher | 10.0 m | 224 | 90 | Y | 2 | - |
| 235 | `press_photographer_pitwall` | Press photographer at the pit wall | 10.0 m | 597 | 10 | Y | 2 | `photographer_rig` |
| 214 | `stop_go_board` | Stop / release board | 10.0 m | 187 | 2 | Y | 2 | - |
| 238 | `team_principal_figure` | Team principal on the timing stand | 10.0 m | 635 | 10 | Y | 2 | `timing_stand`, `crew_headset_full` |
| 243 | `pit_lane_surface` | Pit lane surface | 10.4 m | 359 | 1 | Y | 2 | - |
| 266 | `medical_car` | Medical car | 10.6 m | 528 | 1 | Y | 3 | `safety_car_light_bar` |
| 269 | `crew_front_wing_adjuster` | Crew - front wing adjuster | 11.0 m | 407 | 2 | Y | 3 | `crew_fireproof_overall` |
| 268 | `crew_kneeling_pad` | Crew kneeling pad | 11.0 m | 20 | 20 | Y | 3 | - |
| 270 | `crew_mechanic_kneeling` | Crew - mechanic, kneeling at the car | 11.0 m | 390 | 10 | Y | 3 | `crew_fireproof_overall`, `crew_kneeling_pad` |
| 271 | `crew_mechanic_standing` | Crew - mechanic, standing at the car | 11.0 m | 594 | 14 | Y | 3 | `crew_fireproof_overall` |
| 272 | `crew_pitlane_fire_marshal` | Crew - pit lane fire marshal | 11.0 m | 594 | 14 | Y | 3 | `crew_fireproof_overall`, `fire_extinguisher_handheld` |
| 273 | `crew_visor_cleaner` | Crew - visor cleaner | 11.0 m | 611 | 1 | Y | 3 | `crew_fireproof_overall` |
| 277 | `pit_box_marking` | Pit box marking | 11.0 m | 1018 | 14 | Y | 3 | `pit_lane_surface` |
| 278 | `pit_lane_speed_line` | Pit lane speed & lane lines | 11.0 m | 51 | 1 | Y | 3 | `pit_lane_surface` |
| 283 | `crew_engineer_at_monitor` | Crew - engineer at the monitor bank | 12.0 m | 529 | 10 | Y | 3 | `crew_headset`, `monitor_bank_trolley` |
| 280 | `crew_headset_full` | Crew headset & radio (garage) | 12.0 m | 68 | 40 | Y | 3 | `crew_fireproof_overall` |
| 284 | `crew_radio_beltpack` | Crew radio belt pack | 12.0 m | 44 | 80 | Y | 3 | `crew_fireproof_overall` |
| 285 | `crew_starter_operator` | Crew - starter operator | 12.0 m | 404 | 1 | Y | 3 | `crew_fireproof_overall`, `engine_starter_trolley` |
| 291 | `pit_lane_bollard` | Pit lane bollard | 12.0 m | 280 | 20 | Y | 3 | - |
| 292 | `pit_lane_light_panel` | Pit exit light panel | 12.0 m | 156 | 2 | Y | 3 | - |
| 136 | `tyre_blanket` | Tyre blanket | 13.0 m | 195 | 56 | Y | 1 | - |
| 300 | `tyre_blanket_controller` | Tyre blanket cable & controller | 13.0 m | 71 | 56 | Y | 3 | `tyre_blanket` |
| 299 | `tyre_trolley` | Tyre trolley | 13.0 m | 373 | 28 | Y | 3 | `tyre_blanket` |
| 301 | `air_hose_reel` | Air hose reel | 14.0 m | 160 | 14 | Y | 3 | - |
| 306 | `fire_extinguisher_wheeled` | Wheeled fire extinguisher | 14.0 m | 320 | 16 | Y | 3 | - |
| 310 | `media_camera_operator` | Media camera operator (pit lane) | 14.0 m | 467 | 8 | Y | 3 | `hi_vis_tabard` |
| 253 | `wheel_gun` | Wheel gun | 14.0 m | 147 | 12 | Y | 2 | - |
| 314 | `wheel_gun_hose` | Wheel gun hose & coupling | 14.0 m | 13 | 12 | Y | 3 | `wheel_gun` |
| 334 | `air_line_drop` | Overhead air line drop | 15.0 m | 747 | 28 | Y | 3 | `air_hose_reel` |
| 331 | `monitor_bank_trolley` | Monitor bank trolley | 15.0 m | 398 | 14 | Y | 3 | - |
| 332 | `pit_jack_front` | Front jack | 15.0 m | 87 | 10 | Y | 3 | - |
| 333 | `pit_jack_rear` | Rear jack | 15.0 m | 100 | 10 | Y | 3 | - |
| 337 | `tool_chest` | Tool chest / roller cabinet | 15.0 m | 261 | 20 | Y | 3 | - |
| 345 | `bodywork_trolley` | Bodywork trolley | 16.0 m | 303 | 10 |   | 4 | - |
| 343 | `engine_starter_trolley` | Engine starter trolley | 16.0 m | 187 | 8 |   | 4 | - |
| 355 | `wing_rack` | Spare wing rack | 16.0 m | 373 | 10 | Y | 4 | - |
| 371 | `crew_garage_technician` | Crew - garage technician | 20.0 m | 327 | 26 |   | 4 | `crew_fireproof_overall` |
| 380 | `media_pen_structure` | Media pen / interview position | 20.0 m | 448 | 3 |   | 4 | `pedestrian_crowd_barrier` |
| 394 | `garage_ceiling_gantry` | Garage ceiling gantry & services | 22.0 m | 68 | 14 |   | 4 | `garage_light_batten` |
| 395 | `garage_engineering_desk` | Garage engineering desk | 22.0 m | 127 | 14 |   | 4 | - |
| 396 | `garage_spare_car_covered` | Spare car under a cover | 22.0 m | 187 | 6 | Y | 4 | `garage_interior_floor` |
| 397 | `garage_team_signage` | Garage team signage | 22.0 m | 136 | 28 |   | 4 | - |
| 398 | `garage_toolboard` | Garage tool board | 22.0 m | 339 | 14 |   | 4 | - |
| 399 | `garage_tyre_allocation` | Garage tyre allocation stack | 22.0 m | 272 | 28 | Y | 4 | `tyre_blanket`, `tyre_trolley` |
| 403 | `garage_curtain_divider` | Garage curtain divider | 24.0 m | 622 | 13 |   | 4 | - |

**`safety_car`**  
*varies by:* invented marque; light bar; roof aerials; wheel design; brake dust; parked with the doors shut  
773 px at 7.0 m - the camera passes it on the Beat-4 merge. A race weekend parks it at the pit exit and this film's route goes straight past. It is a full road-car build at hero fidelity: glazing with real thickness, an interior behind the glass, panel gaps, and a light bar.

**`safety_car_light_bar`**  
*varies by:* lens segments; unlit; mounting feet; cable entry  

**`crew_fireproof_overall`**  
*varies by:* team colours (invented); collar up/down; sleeves pushed up; knee dirt; kneeling wear at the shins; fit by build  
THE garment that makes the whole crew work. Nomex hangs stiffer than cotton - fewer, larger folds, and it holds a crease at the elbow and the back of the knee. Get the fold LANGUAGE right once here and 110 figures inherit it.

**`crew_gloves_and_boots`**  
*varies by:* grip pattern; cuff over vs under the sleeve; boot scuffing; sole wear  
The cuff overlap is the detail that says the suit is worn rather than painted on.

**`crew_helmet_visor`**  
*varies by:* visor up/down; team livery (invented); scuffs; balaclava at the neck  
ZERO EXPOSED SKIN on the pit-stop crew - helmet, visor, balaclava, gloves. That is precisely why these figures are tractable at 653 px while a bare-headed paddock figure at the same distance would not be.

**`crew_jack_operator_front`**  
*varies by:* crouched with the jack presented / lifting / stepping clear  

**`crew_jack_operator_rear`**  
*varies by:* crouched behind / lifting; body angle to the car  

**`crew_release_operator`**  
*varies by:* board raised / lowered; arm extended; looking down the lane  

**`crew_stabiliser`**  
*varies by:* hand on the sidepod; braced stance  

**`crew_tyre_carrier_off`**  
*varies by:* braced to receive / arms out / tyre held at hip; lean angle  
The off-carrier's whole body is a diagonal brace. Standing upright is wrong.

**`crew_tyre_carrier_on`**  
*varies by:* tyre held ready at chest / stepping in; blanket just removed and dropped  

**`crew_wheel_gunner`**  
*varies by:* crouched ready / gun raised / gun down; which corner; left-vs-right handed stance  
653 px at 10 m. Four of them, one per corner, and the two on the far side are mirrored NOT copied - a mirrored figure with an identical fold pattern is visible. Crouched with the gun braced on the thigh is the canonical ready pose.

**`engineer_on_timing_stand`**  
*varies by:* seated at a monitor; leaning in; headset; hand raised  
Four to six per stand across ten stands. An occupied pit wall is the difference between a race weekend and a car park.

**`fire_extinguisher_handheld`**  
*varies by:* bracket vs floor-standing; label fade; pin & tag; dust film on the shoulder  
Everywhere: marshal posts, garages, paddock, fire points. 90+ instances and they must not all be identical.

**`press_photographer_pitwall`**  
*varies by:* crouched / standing / panning; two bodies on straps; tabard number  

**`stop_go_board`**  
*varies by:* raised/lowered; paint wear; team graphic  

**`team_principal_figure`**  
*varies by:* seated / standing / arms folded; team kit not fireproofs; headset  

**`pit_lane_surface`**  
*varies by:* concrete vs asphalt zones; tyre pickup outside each box; fuel staining  
12.0 m wide. The fast lane / working lane split has to be in the surface as well as the paint.

**`medical_car`**  
*varies by:* estate/SUV body; light bar; rear equipment visible through the glass; boot open  

**`crew_front_wing_adjuster`**  
*varies by:* crouched at the endplate with a driver; clicking the flap adjuster  

**`crew_kneeling_pad`**  
*varies by:* in use / dropped / stacked; compressed foam  

**`crew_mechanic_kneeling`**  
*varies by:* one knee / both knees / on a pad; reaching under the floor; tool in hand  
The garage's most common pose and the one that most obviously fails if it is a standing figure with bent legs.

**`crew_mechanic_standing`**  
*varies by:* arms folded / hands on the sidepod / reaching into the airbox / carrying a panel  

**`crew_pitlane_fire_marshal`**  
*varies by:* extinguisher held / on the ground beside; watching the box; full fire kit  
One per box. Fully fire-kitted including a hood - the most covered figure in the film and therefore the easiest.

**`crew_visor_cleaner`**  
*varies by:* reaching over the halo with a cloth on a stick  

**`pit_box_marking`**  
*varies by:* box number; paint wear at the gun positions; tape overlay  

**`pit_lane_speed_line`**  
*varies by:* wear; repaint ghosting  

**`crew_engineer_at_monitor`**  
*varies by:* seated / standing / leaning in; headset on; hand to the ear cup; laptop  

**`crew_headset_full`**  
*varies by:* boom mic position; cable to a belt pack; over-helmet vs over-cap  

**`crew_radio_beltpack`**  
*varies by:* aerial angle; cable route; clip  

**`crew_starter_operator`**  
*varies by:* crouched at the rear with the starter shaft in  

**`pit_lane_bollard`**  
*varies by:* impact lean; reflective band wear  

**`pit_lane_light_panel`**  
*varies by:* red/green state; housing weathering  

**`tyre_blanket`**  
*varies by:* wrapped/open; velcro flap; scorch marks; cable dangling; branded face  
User-named class. A blanket that is a smooth cylinder is wrong - it must bulge over the tyre and gape at the seam.

**`tyre_blanket_controller`**  
*varies by:* cable coil; LED state  

**`tyre_trolley`**  
*varies by:* loaded 0-4 tyres; castor angle; frame paint chips; team decal  

**`air_hose_reel`**  
*varies by:* wound/unwound; wall vs ceiling mount; guide arm angle  

**`fire_extinguisher_wheeled`**  
*varies by:* hose coil; pressure gauge; wheel grime  

**`media_camera_operator`**  
*varies by:* shoulder-mounted / on a monopod / walking backwards; tabard; cable wrangler behind  

**`wheel_gun`**  
*varies by:* socket fitted/off; hose direction; anodised body wear; team colour  
User-named. Nose-mounted socket, trigger cage, torque sleeve. It should be lying on the ground or in its cradle, not floating.

**`wheel_gun_hose`**  
*varies by:* coil; kink; connector state  

**`air_line_drop`**  
*varies by:* coil length; balancer position  

**`monitor_bank_trolley`**  
*varies by:* screen count 2-6; screens on/off; cable dressing  

**`pit_jack_front`**  
*varies by:* handle angle; pad wear; team colour  

**`tool_chest`**  
*varies by:* drawer open/closed; top clutter; castor brake; sticker layer; scuffed side  
Drawer front gaps and a slightly-open drawer are worth more than any amount of shader work.

**`engine_starter_trolley`**  
*varies by:* shaft stowed; cable state  

**`wing_rack`**  
*varies by:* loaded 0-3 wings; padding; castor  
A rack of spare front wings is the single most 'F1 garage' object after the tyre stack.

**`crew_garage_technician`**  
*varies by:* at a bench / carrying a case / at the toolboard / pushing a trolley  

**`media_pen_structure`**  
*varies by:* backdrop board with invented brands; barrier; lighting stand  

**`garage_ceiling_gantry`**  
*varies by:* air drops; power reels; cable trays; lighting rails  

**`garage_engineering_desk`**  
*varies by:* monitors; laptops; papers; chairs pushed out  

**`garage_spare_car_covered`**  
*varies by:* fitted cover draping over wings and wheels; team logo on the cover; wheels visible below the hem  
Solves the 'a race garage needs a second car and we only have one car model' problem honestly and authentically: a fitted cover is what a real garage does with a spare, and it is a cloth-sim job rather than a second 617-part build.

**`garage_team_signage`**  
*varies by:* invented team; backlit vs printed; fixing shadow  

**`garage_toolboard`**  
*varies by:* shadow-board outlines with tools missing from some; hooks; labels  
The shadow board with three tools missing is a better story than a full one.

**`garage_tyre_allocation`**  
*varies by:* blanketed vs bare; compound marking bands; stack height 3-6; trolley beside  

**`garage_curtain_divider`**  
*varies by:* drawn/open; team graphic; hem weights; sag  
Drawn curtains are how a real garage hides its business, and they are the cheapest way to make an interior read as deep without modelling it.

---

### `pit_straight` - Pit straight, S/F, gantry, footbridge

810 m at 16 m wide, dead flat z=0.000. The onboard follow runs it at 207-323 km/h with the lens 1.9 m off the deck; the camera passes UNDER the gantry (9.0 m soffit) and UNDER La Passerelle (7.5 m soffit).

*29 items, 25 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 84 | `gantry_soffit_panel` | Gantry soffit panel & services | 3.0 m | 516 | 1 | Y | 1 | `gantry_truss` |
| 64 | `gantry_truss` | S/F gantry truss beam | 3.0 m | 1493 | 1 | Y | 1 | `gantry_leg` |
| 121 | `gantry_walkway` | Gantry walkway grating & handrail | 4.0 m | 1027 | 1 | Y | 1 | `gantry_truss` |
| 148 | `gantry_fascia` | Gantry sponsor fascia | 5.0 m | 896 | 2 | Y | 2 | `gantry_truss` |
| 153 | `la_passerelle_deck` | La Passerelle deck | 5.6 m | 300 | 1 | Y | 2 | `la_passerelle_truss` |
| 152 | `la_passerelle_truss` | La Passerelle truss | 5.6 m | 2033 | 1 | Y | 2 | `la_passerelle_tower` |
| 162 | `la_passerelle_banner` | La Passerelle fascia banner | 6.0 m | 871 | 2 | Y | 2 | `la_passerelle_truss` |
| 156 | `la_passerelle_mesh` | La Passerelle mesh screen | 6.0 m | 1493 | 1 | Y | 2 | `la_passerelle_truss` |
| 177 | `pit_wall_terminal` | Pit wall tapered terminal & nose board | 6.1 m | 734 | 2 | Y | 2 | `pit_wall_unit` |
| 178 | `pit_wall_coping` | Pit wall coping | 6.2 m | 100 | 125 | Y | 2 | `pit_wall_unit` |
| 132 | `pit_wall_unit` | Pit wall precast unit | 6.2 m | 723 | 125 | Y | 1 | - |
| 180 | `pit_wall_advert` | Pit wall advertising panel | 7.0 m | 331 | 120 | Y | 2 | `pit_wall_unit` |
| 181 | `pit_wall_padding` | Pit wall padding block | 7.0 m | 427 | 60 | Y | 2 | `pit_wall_unit` |
| 204 | `gantry_tv_pod` | Gantry TV camera pod | 9.0 m | 207 | 3 | Y | 2 | `gantry_truss` |
| 234 | `pit_board` | Pit board | 10.0 m | 448 | 10 | Y | 2 | `pit_wall_unit` |
| 135 | `timing_stand` | Team timing stand | 10.0 m | 1195 | 10 | Y | 1 | - |
| 239 | `timing_stand_canopy` | Timing stand canopy | 10.0 m | 75 | 10 | Y | 2 | `timing_stand` |
| 215 | `timing_stand_monitor` | Timing stand monitor bank | 10.0 m | 217 | 60 | Y | 2 | `timing_stand` |
| 240 | `timing_stand_seat` | Timing stand seat | 10.0 m | 336 | 40 | Y | 2 | `timing_stand` |
| 264 | `start_light_backing` | Start light backing box & bracket | 10.1 m | 481 | 5 | Y | 3 | - |
| 265 | `start_light_panel` | Start light panel | 10.1 m | 407 | 5 | Y | 3 | `start_light_backing` |
| 274 | `gantry_ladder` | Gantry access ladder & safety cage | 11.0 m | 2160+ | 2 | Y | 3 | `gantry_leg` |
| 246 | `gantry_leg` | S/F gantry leg | 11.1 m | 2160+ | 2 | Y | 2 | - |
| 329 | `flagpole` | Flagpole | 15.0 m | 2160+ | 12 | Y | 3 | - |
| 336 | `sponsor_flag` | Sponsor flag | 15.0 m | 373 | 12 | Y | 3 | `flagpole` |
| 363 | `pa_horn_speaker` | PA horn speaker | 18.0 m | 93 | 14 |   | 4 | - |
| 260 | `la_passerelle_tower` | La Passerelle tower column | 20.0 m | 1680 | 2 |   | 2 | - |
| 418 | `windsock` | Windsock & pole | 25.0 m | 358 | 3 |   | 4 | - |
| 420 | `la_passerelle_stair` | La Passerelle stair flight & landing | 26.1 m | 1073 | 2 |   | 5 | `la_passerelle_tower` |

**`gantry_soffit_panel`**  
*varies by:* cable trays; conduit; junction boxes; bird spikes  
The single most-overlooked hero surface in the film: you only ever see the underside, at 3 m, at 4K.

**`gantry_truss`**  
*varies by:* node plates; bolt clusters; walkway edge  
Soffit at z=+9.00, 2.2 m deep. THE CAMERA PASSES UNDER IT AT 3.0 m. Every bolt cluster and node plate on the underside is on camera.

**`gantry_walkway`**  
*varies by:* grating pattern; toe board; kick plate  

**`gantry_fascia`**  
*varies by:* invented brand; both faces different; fixing shadow  

**`la_passerelle_deck`**  
*varies by:* deck plank/plate; drainage slot; wear path down the middle  
Circuit x=-450, soffit 7.50 m, 4.0 m deep, 52 m span. The onboard follow passes under it 1.3 s in at ~230 km/h - the soffit is 5.6 m from the lens.

**`la_passerelle_truss`**  
*varies by:* node plates; camber; paint system  

**`la_passerelle_banner`**  
*varies by:* invented brand; sag between fixings; sun bleach on the south face  

**`la_passerelle_mesh`**  
*varies by:* mesh aperture; tension sag; splice lines  
Anti-throw screening. At 6 m the aperture must be real geometry or an honest arcminute-argued shader - it is backlit.

**`pit_wall_terminal`**  
*varies by:* 7 stepped lifts; chevron board fade; spread footing exposed  
The west terminal is 6.1 m from the lens in Beat 4. A wall that just stops is the placeholder; a real one steps down over 7 lifts onto a spread footing with a chevron nose board.

**`pit_wall_coping`**  
*varies by:* chipped arris; paint wear where crew lean  

**`pit_wall_unit`**  
*varies by:* 3.0 m units, every 5th short; +/-12 mm height; +/-0.004 rad tilt; joint step; base staining  
375 m of wall, face pinned on circuit y=+11.500. The step and tilt between units IS the object - a continuous extrusion reads as a plastic kerb from the onboard follow.

**`pit_wall_advert`**  
*varies by:* invented brand; 50 mm proud of the face; edge lift; grime line at the bottom  

**`pit_wall_padding`**  
*varies by:* compression set; torn cover; strap  

**`gantry_tv_pod`**  
*varies by:* pan angle; housing weathering; cable drop  

**`pit_board`**  
*varies by:* digit set fitted; stored against the wall; handle wear  

**`timing_stand`**  
*varies by:* tier count; canopy up/down; occupied/empty; team livery  
NOT IN THE SPEC AND NOT BUILT - a genuine gap. A pit wall with no timing stands is the clearest sign nobody is home.

**`timing_stand_canopy`**  
*varies by:* deployed/stowed; fabric sag; branded valance  

**`timing_stand_monitor`**  
*varies by:* screen count; on/off; sun hood; cable loom  

**`timing_stand_seat`**  
*varies by:* headrest; occupied; swivel angle  

**`start_light_backing`**  
*varies by:* cable entry; mounting slop  

**`start_light_panel`**  
*varies by:* lens crazing; sun hood; off (unlit) state; column alignment drift  
NOT IN THE SPEC - the gantry is dimensioned with no signals on it. Five columns of five. Unlit for this film, which means the lens optics and hoods have to carry it, not emission.

**`gantry_ladder`**  
*varies by:* hoop pitch; rest platform  

**`gantry_leg`**  
*varies by:* lattice vs box section; base pad grout; ladder side; paint chalking  
Legs at circuit y=+/-11.0, 22 m clear span. The camera passes between them at 1.9 m altitude at 323 km/h.

**`flagpole`**  
*varies by:* halyard slap; cleat; base collar  

**`sponsor_flag`**  
*varies by:* invented brand; wind shape on bearing 65 deg; hem fray; age 0.05-0.34  
Flags must be shaped by the SAME wind bearing as the grass lean (65 deg) or the world contradicts itself.

**`pa_horn_speaker`**  
*varies by:* horn count 1-4; yaw; bracket rust  

**`la_passerelle_tower`**  
*varies by:* cast raft base (325 mm correction); bolt boxes  

**`windsock`**  
*varies by:* inflation on the 65 deg bearing; fabric bleach  
Must agree with the flag and grass wind direction.

**`la_passerelle_stair`**  
*varies by:* tread wear; half-landing; handrail  

---

### `grandstand` - Grandstand band

600 m x 28 m x 14 m, circuit y -34..-62, x -420..+180. The Beat-6 crane-out clears the roof by 13.8 m and passes the front top edge at ~9 m. Empty stands are a deliberate look - which makes every seat individually visible.

*23 items, 11 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 210 | `grandstand_nosing` | Tread nosing | 9.5 m | 16 | 3,400 | Y | 2 | `grandstand_riser_unit` |
| 208 | `grandstand_roof_sheet` | Roof sheet (profiled metal) | 9.5 m | 16 | 900 | Y | 2 | `grandstand_roof_truss` |
| 209 | `grandstand_roof_truss` | Roof truss | 9.5 m | 503 | 40 | Y | 2 | `grandstand_column` |
| 231 | `grandstand_gutter` | Gutter, outlet & downpipe | 10.0 m | 90 | 60 | Y | 2 | `grandstand_roof_sheet` |
| 138 | `grandstand_riser_unit` | Terrace riser unit (precast) | 14.7 m | 85 | 3,400 | Y | 1 | - |
| 321 | `grandstand_row_letter` | Row / seat number plate | 14.7 m | 12 | 18,350 |   | 3 | `grandstand_seat` |
| 315 | `grandstand_seat` | Grandstand seat | 14.7 m | 91 | 18,350 |   | 3 | `grandstand_seat_bracket` |
| 316 | `grandstand_seat_bracket` | Seat bracket & fixing | 14.7 m | 24 | 18,350 |   | 3 | - |
| 335 | `grandstand_handrail` | Handrail | 15.0 m | 249 | 60 | Y | 3 | `grandstand_stair` |
| 330 | `grandstand_stair` | Grandstand stair flight | 15.0 m | 224 | 26 | Y | 3 | `grandstand_riser_unit` |
| 258 | `grandstand_front_rail` | Front safety rail | 15.7 m | 262 | 1 | Y | 2 | - |
| 350 | `grandstand_banner` | Grandstand advertising banner | 16.0 m | 467 | 40 | Y | 4 | `grandstand_front_rail` |
| 351 | `grandstand_block_letter` | Block / gate letter sign | 16.0 m | 280 | 12 | Y | 4 | `grandstand_cladding` |
| 352 | `grandstand_litter_bin` | Grandstand litter bin | 16.0 m | 233 | 60 |   | 4 | `bin_liner` |
| 356 | `grandstand_bracing` | Bracing member | 17.0 m | 44 | 240 |   | 4 | `grandstand_column` |
| 259 | `grandstand_column` | Grandstand column | 17.0 m | 2160+ | 120 |   | 2 | - |
| 362 | `grandstand_camera_platform` | Camera / photo platform | 18.0 m | 207 | 6 |   | 4 | - |
| 376 | `grandstand_debris_fence` | Grandstand debris fence | 20.0 m | 672 | 1 |   | 4 | `catch_fence_post` |
| 377 | `grandstand_skirt` | Terrace skirt & counterfort | 20.0 m | 345 | 1 |   | 4 | - |
| 389 | `grandstand_cladding` | Rear cladding panel | 21.0 m | 178 | 700 |   | 4 | - |
| 390 | `grandstand_vomitory` | Vomitory / tunnel mouth | 21.0 m | 427 | 18 | Y | 4 | - |
| 400 | `grandstand_concourse` | Concourse apron | 22.0 m | 170 | 2 |   | 4 | - |
| 410 | `grandstand_tower` | Grandstand scaffold tower | 25.0 m | 2160+ | 6 |   | 4 | - |

**`grandstand_nosing`**  
*varies by:* anti-slip insert wear; chipped arris  

**`grandstand_roof_sheet`**  
*varies by:* profile pitch; end lap; fixing washer rows; algae streaks below the laps; one panel lifted  
The single largest surface in the Beat-6 frame at t=0. Streaking below the side laps is what stops a metal roof looking like grey plastic.

**`grandstand_roof_truss`**  
*varies by:* node plates; purlin cleats; camber; bracing  
Seen from ABOVE at 9.5 m in Beat 6 - the top chord and the purlins are the visible faces, which is the opposite of the usual assumption.

**`grandstand_gutter`**  
*varies by:* silt; leaf litter; overflow staining  

**`grandstand_riser_unit`**  
*varies by:* unit joint step; nosing wear; drainage channel; weathering streak  
816 sawn bays. Still hero: the riser fronts, the gangways and the tread strips are exactly the parts the crowd does NOT cover, and from directly above they are the grid the whole crowd is registered against.

**`grandstand_row_letter`**  
*varies by:* 5x7 bitmap glyph at 2 seats/font-pixel; wear  
Visible only on aisle-end units and in the empty blocks. Low priority.

**`grandstand_seat`**  
*varies by:* 4 archetypes; 22 % folded where unoccupied; 0.6 % missing; colour block pattern; sun bleach on the west face; chewing-gum grime  
DOWNGRADED BY THE CROWD DECISION, and that saving partly pays for the crowd. With the stands at 82 % occupancy roughly three quarters of every seat is hidden behind an occupant. What still reads from the Beat-6 crane-out is: the aisle-end units, the empty seats inside the density field's gaps, the top edge of the seat back between shoulders, and the folded seats in the near-empty blocks. Build the seat back edge and the aisle-end unit properly and let the rest be simple. It is no longer the hero it was when the stands were empty.

**`grandstand_seat_bracket`**  
*varies by:* riser vs tread mount; corrosion at the fixing  
Almost entirely occluded once the crowd is in. Low priority.

**`grandstand_handrail`**  
*varies by:* polish where gripped; joint sleeve; post base plate  

**`grandstand_stair`**  
*varies by:* contrasting nosing; centre handrail; wear path  

**`grandstand_front_rail`**  
*varies by:* infill mesh vs bar; sponsor kick panel; impact bends  
34 m from the racing line for the whole onboard follow, and 15.7 m under the Beat-6 crane-out. Now also the mounting line for draped crowd banners and the rail 600 standing spectators lean on, so its top rail takes hand polish and its kick panel takes scuffs.

**`grandstand_banner`**  
*varies by:* invented brand; sag; wind lift at a loose corner  

**`grandstand_block_letter`**  
*varies by:* invented naming; fixing shadow; fade  

**`grandstand_litter_bin`**  
*varies by:* open-top vs lidded; fill; dents  

**`grandstand_bracing`**  
*varies by:* turnbuckle; gusset  

**`grandstand_column`**  
*varies by:* section; base plate & grout; paint chalking on the sun face  

**`grandstand_camera_platform`**  
*varies by:* deck; rail; occupied  

**`grandstand_debris_fence`**  
*varies by:* mesh; post pitch  

**`grandstand_skirt`**  
*varies by:* board-mark texture; batter 0.35 m; counterfort every 5th panel  
CONTRACT GAP: the terrace is a declared addendum world_contract does not carry. Terrain must build no ground inside x -426..+186, y -69.0..-28.5 and must weld to this 1.85 m skirt.

**`grandstand_cladding`**  
*varies by:* panel joint; colour band; impact dent at ground level  

**`grandstand_vomitory`**  
*varies by:* dark interior with a real ceiling; signage; handrail; scuffed jamb  
A vomitory that is a black rectangle is a hole in the model. It needs depth, a lit far wall, and - now that this is a race weekend - people moving through it and a steward at the mouth.

**`grandstand_concourse`**  
*varies by:* bay pattern; wear path; drainage falls  

**`grandstand_tower`**  
*varies by:* tube & fitting; ply deck; safety mesh  

---

### `track_surface` - Racing surface

3675 m welded cyclic mesh. The lens gets to 0.8-1.1 m of it at the hairpin station and rides 1.9 m above it for 560 m of onboard follow.

*15 items, 15 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 9 | `asphalt_paver_mat_joint` | Paver mat longitudinal joint | 1.1 m | 61 | 80 | Y | 1 | `asphalt_wearing_course` |
| 6 | `asphalt_wearing_course` | Asphalt wearing course | 1.1 m | 41 | 1 | Y | 1 | - |
| 7 | `rubber_line_deposit` | Rubbered-in racing line | 1.1 m | 2160+ | 1 | Y | 1 | `asphalt_wearing_course` |
| 16 | `asphalt_crack_seal` | Crack sealing | 1.5 m | 60 | 300 | Y | 1 | `asphalt_wearing_course` |
| 17 | `asphalt_patch_repair` | Patch repair | 1.5 m | 2160+ | 25 | Y | 1 | `asphalt_wearing_course` |
| 18 | `asphalt_transverse_joint` | Transverse cold / day joint | 1.5 m | 30 | 40 | Y | 1 | `asphalt_wearing_course` |
| 15 | `tyre_marble` | Tyre marble | 1.5 m | 18 | 400,000 | Y | 1 | `rubber_line_deposit` |
| 36 | `lockup_skid_mark` | Lock-up / flat-spot mark | 2.0 m | 336 | 20 | Y | 1 | `asphalt_wearing_course` |
| 39 | `timing_loop_sawcut` | Timing loop saw cut & resin | 2.0 m | 22 | 3 | Y | 1 | `asphalt_wearing_course` |
| 51 | `marble_drift_bank` | Marble drift bank | 2.5 m | 597 | 60 | Y | 1 | `tyre_marble` |
| 74 | `bridge_expansion_joint` | Bridge deck expansion joint | 3.0 m | 75 | 2 | Y | 1 | `pont_deck_slab` |
| 70 | `track_drain_slot` | Track-edge slot drain & grating | 3.0 m | 498 | 120 | Y | 1 | - |
| 105 | `launch_rubber_stripe` | Grid launch rubber stripe | 3.6 m | 207 | 40 | Y | 1 | `grid_box_marking` |
| 126 | `track_gully_lid` | Gully pot lid | 4.0 m | 467 | 80 | Y | 1 | `track_drain_slot` |
| 127 | `track_manhole_cover` | Track-side manhole cover | 4.0 m | 560 | 60 | Y | 1 | - |

**`asphalt_paver_mat_joint`**  
*varies by:* joint tightness; raised vs depressed lip; sealed vs raw; mat width 9.5 m +/-13.5 %  
The single most convincing asphalt detail there is: real tracks are laid in 9.5 m mats and the joints run the length of the circuit. Wrong version: no joints at all, which is what 'flat grey paving' means.

**`asphalt_wearing_course`**  
*varies by:* 9 resurfacing zones; aggregate size mix; segregation patches; polish on the line  
11 detail scales already exist, 140 m down to 0.6 mm. The lens reaches 1.1 m at the hairpin, and rides 1.9 m for 560 m at 323 km/h. KNOWN LIMIT: displacement is bump-only (1-3 mm of relief). If the hairpin frames show flat aggregate at 1.1 m, this is the first thing to promote to true displacement - and then it must be re-checked for TEMPORAL flicker in motion, not just in a still.

**`rubber_line_deposit`**  
*varies by:* width by corner (heart 0.55 x spread, feather to 0.78 x half-width); tyre tracks at +/-0.82 m, 0.20 m wide  
Measured reflectance 0.0281-0.0288 rubbered vs 0.0626-0.0808 clean, ratio 2.23-2.87. THE OUT LAP IS NOT THE FLYING LAP: at s=0 the drawn rubber sits at u=-4.8 while the transit blend puts the car on the centreline. That is correct and must not be 'fixed'.

**`asphalt_crack_seal`**  
*varies by:* snake width; overband shine; age  

**`asphalt_patch_repair`**  
*varies by:* saw-cut rectangle vs ragged; age (colour); edge seal bead; settlement dish  
~25 per lap. A patch that is only a colour change is a decal; it needs a saw-cut edge, a sealant bead and a millimetre of settlement.

**`asphalt_transverse_joint`**  
*varies by:* step height; seal bead  

**`tyre_marble`**  
*varies by:* size 4-25 mm; drift bank depth; freshness; colour  
Individual pellets, not a texture. They bank OFF-line, which is exactly where the camera slides during the outboard-alongside chase at T1/T2.

**`lockup_skid_mark`**  
*varies by:* length; darkness; the double stripe of a locked front pair  

**`timing_loop_sawcut`**  
*varies by:* resin sheen; cut width  
At s=0, 1200 and 2450 (the sector splits). The camera crosses s=0 at 1.9 m.

**`marble_drift_bank`**  
*varies by:* bank height; sweep line at the edge; corner-exit weighting  

**`bridge_expansion_joint`**  
*varies by:* comb plate vs elastomeric; grit in the gap  

**`track_drain_slot`**  
*varies by:* silt level; one grating in 7 sits ~16 mm low; frame rebate  
The rebate ring is the object. A grating flush with the asphalt reads as a printed pattern.

**`launch_rubber_stripe`**  
*varies by:* decay over 13-18 m; pair spacing 2.005 m (car track)  
20 pairs. Already built; the pair spacing must match the measured 2.005 m car width.

**`track_gully_lid`**  
*varies by:* wear pattern; lifting keyholes; rust bloom  

**`track_manhole_cover`**  
*varies by:* round vs rect; rebate; settlement  

---

### `kerbs_markings` - Kerbs & painted markings

35 serrated kerbs, 1.50 m wide, 75 mm peak. The T4 inside kerb is the single closest piece of world geometry in the film.

*12 items, 12 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 3 | `kerb_hero_t4` | T4 apex kerb (hero) | 0.8 m | 210 | 1 | Y | 1 | `kerb_precast_unit` |
| 10 | `verge_green_paint` | Green painted verge strip | 1.1 m | 2036 | 1 | Y | 1 | `white_line_edge` |
| 8 | `white_line_edge` | Track-edge white line | 1.1 m | 204 | 1 | Y | 1 | - |
| 38 | `start_finish_line` | Start/finish line paint | 2.0 m | 448 | 1 | Y | 1 | - |
| 48 | `kerb_bedding_joint` | Kerb bedding & joint mortar | 2.5 m | 49 | 3,400 | Y | 1 | `kerb_precast_unit` |
| 49 | `kerb_end_ramp` | Kerb end ramp | 2.5 m | 112 | 70 | Y | 1 | `kerb_precast_unit` |
| 50 | `kerb_negative_trough` | Negative kerb trough | 2.5 m | 90 | 2 | Y | 1 | `kerb_precast_unit` |
| 43 | `kerb_precast_unit` | Serrated kerb unit | 2.5 m | 112 | 3,400 | Y | 1 | - |
| 69 | `pit_exit_blend_line` | Pit-exit blend line | 3.0 m | 124 | 1 | Y | 1 | - |
| 89 | `pit_exit_gore` | Pit-exit gore chevrons | 3.0 m | 373 | 1 | Y | 1 | `pit_exit_blend_line` |
| 103 | `grid_box_marking` | Grid box marking | 3.6 m | 2160+ | 20 | Y | 1 | - |
| 104 | `grid_numeral` | Grid numeral paint | 3.6 m | 519 | 20 | Y | 1 | `grid_box_marking` |

**`kerb_hero_t4`**  
*varies by:* serration knock-down groups; paint wear at 42 % inside / 72 % exit; bedding step; grit in the troughs  
THE closest piece of world geometry in the entire film: the static camera sits ON this kerb at z=+0.85 with a 21 mm lens. A 75 mm serration is 210 px tall. Every arris, every chip, every trapped stone is on camera for 3.9 s while the car yaws 176 degrees. Nothing else in the world is under this much scrutiny.

**`verge_green_paint`**  
*varies by:* 1.0 m wide with a 100 mm white line on the inboard lip; wear; algae in the low spots  
Outboard of every kerb. This is painted ASPHALT, not grass - do not plant it.

**`white_line_edge`**  
*varies by:* 100 mm wide; wear where the car crosses; repaint ghosting; thermoplastic edge bead  
Paint has THICKNESS (3.5 mm on the grid numerals). At 1.1 m a zero-thickness line is a decal.

**`start_finish_line`**  
*varies by:* 400 mm wide; wear at the racing line; the 6.75 mm datum step under it  
CONTRACT DEFECT to be aware of: the ground datum steps 6.75 mm across s=0 because the undulation noise is not cyclic. It hides under this 400 mm of paint, but the onboard follow crosses here at 323 km/h.

**`kerb_bedding_joint`**  
*varies by:* mortar squeeze-out; washed-out joints; weed  

**`kerb_end_ramp`**  
*varies by:* ramp length 1.1-2.8 m; impact damage at the leading arris  
The tapered terminal. Real kerbs never just stop.

**`kerb_negative_trough`**  
*varies by:* grit and rubber accumulation in the trough; ramp scuffing  
-60 mm deep, 0.80 m wide, 1.6 m end ramps. T8 apex and T12 exit ONLY. Causes an 18 % suspension extension event against 340 mm ride height - it must be geometrically exact or the car's motion lies.

**`kerb_precast_unit`**  
*varies by:* precast section 1.85-2.25 m; height step sigma 2.2 mm; roll sigma 3.5 mrad; 2-6 knocked-down serration groups; red/white block length 0.955-1.055 m  
1.50 m wide, 25 mm proud track-side, 50 mm outer, 25 mm serration on 250 mm pitch = 75 mm peak. Leaves 265 mm of plank clearance against 340 mm ride height. Wrong version: one extruded ribbon with a repeating stripe - the unit-to-unit step and roll is the whole read.

**`pit_exit_blend_line`**  
*varies by:* converges over 90 m from s=3459.4; wear  

**`pit_exit_gore`**  
*varies by:* 0.30 m paint on 1.20 m pitch at 45 deg; wear  

**`grid_box_marking`**  
*varies by:* 2.6 x 6.0 m staggered; 100 mm outline; pole on the left; wear  

**`grid_numeral`**  
*varies by:* 3.5 mm paint thickness; wear; repaint ghost  
Depends on Blender's bundled vector font; if it is unavailable the numerals are skipped and the boxes still build. Verify it renders.

---

### `runoff` - Runoff, gravel traps, verges

227,208 m2 of platform; 41,137 m2 of gravel; 50,072 m2 of tarmac runoff. The doppler hover stands ON the right-hand verge at 2.4 m.

*11 items, 11 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 60 | `gravel_bed_surface` | Gravel bed surface | 2.8 m | 67 | 21 | Y | 1 | - |
| 61 | `gravel_rake_furrow` | Rake furrow | 2.8 m | 267 | 900 | Y | 1 | `gravel_bed_surface` |
| 85 | `gravel_retaining_kerb` | Gravel retaining kerbstone | 3.0 m | 187 | 1,200 | Y | 1 | `gravel_bed_surface` |
| 94 | `grass_runoff_turf` | Grass runoff turf | 3.5 m | 32 | 1 | Y | 1 | `grass_clump_fescue` |
| 95 | `runoff_asphalt_mat` | Tarmac runoff mat | 3.5 m | 21 | 1 | Y | 1 | `asphalt_wearing_course` |
| 100 | `runoff_edge_lip` | Pavement edge lip | 3.5 m | 80 | 1 | Y | 1 | `runoff_asphalt_mat` |
| 115 | `bare_soil_scar` | Bare soil / erosion scar | 4.0 m | 560 | 120 | Y | 1 | `grass_runoff_turf` |
| 151 | `verge_gully_grate` | Verge gully & grate | 5.0 m | 373 | 46 | Y | 2 | `verge_swale` |
| 146 | `verge_swale` | Verge drainage swale | 5.0 m | 254 | 1 | Y | 2 | - |
| 175 | `runoff_sponsor_paint` | Painted sponsor name on runoff | 6.0 m | 933 | 8 | Y | 2 | `runoff_asphalt_mat` |
| 203 | `gravel_stone` | Gravel stone | 8.4 m | 13 | 240,000 | Y | 2 | `gravel_bed_surface` |

**`gravel_bed_surface`**  
*varies by:* rake furrows; depth profile (dips to 0.62 m); berm at the edge; disturbed patches  
41,137 m2 over 21 beds. A flat gravel plane is the placeholder; real beds are raked, mounded at the edges and scarred where something has been recovered.

**`gravel_rake_furrow`**  
*varies by:* direction; freshness; overlapping passes  
Explicitly called for. Cheap, and it makes a gravel trap read as maintained ground rather than a noise field.

**`gravel_retaining_kerb`**  
*varies by:* settlement; spalled arris; buried by displaced gravel  
The lip between the asphalt runoff and the gravel bed. Without it the two surfaces just abut, which is the giveaway.

**`grass_runoff_turf`**  
*varies by:* mown vs rough; 8 baked attributes (wet, wear, cover, mown, dry); scorch on the dry crowns  
18-25 m of it as the default runoff, and 20 m at T5. The rejected renders showed this as 'pink and green blotches' - the fix is that the ground shader and the clump geometry have to agree, not fight.

**`runoff_asphalt_mat`**  
*varies by:* different mix from the track (paler, coarser); no rubber line; paver joints at a different angle  
50,072 m2. It must NOT look like the racing surface - real runoff is a coarser, lighter mix laid in different mats, and the moment it matches the track the width of the circuit becomes unreadable.

**`runoff_edge_lip`**  
*varies by:* 45 mm drop; ravelled arris; grass encroachment  

**`bare_soil_scar`**  
*varies by:* wheel rut; water channelling; stone exposure  

**`verge_gully_grate`**  
*varies by:* silt; grass overgrowth; frame settlement  

**`verge_swale`**  
*varies by:* silt line; standing water in the low points; reed encroachment  
0.34 m swale 7 m beyond the platform edge. It is what makes the ground read as drained rather than extruded.

**`runoff_sponsor_paint`**  
*varies by:* invented brand; foreshortened letterforms; wear  

**`gravel_stone`**  
*varies by:* 11-42 mm; rounded pea vs angular; wet/dry; dust coat; embedded vs loose  
130,000 in the hero beds. KNOWN LIMIT: gravel below 11 mm is shader, not geometry - the documented rule is that if a lens gets inside ~0.6 m of a bed the hero tier must be raised and the bed re-run. Current closest is 2.8 m, so the rule holds, but check T1 at s=252.

---

### `barriers` - Barriers & catch fencing

1,821 W-beam panels, 3,641 posts, 5,611 TecPro blocks, 690 fence posts, 2,255 tyres. The doppler hover sits 4.2-4.4 m off the armco and fence it looks past.

*26 items, 26 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 54 | `armco_post` | Armco post | 2.6 m | 2154 | 3,641 | Y | 1 | - |
| 56 | `armco_reflector` | Armco reflector stud | 2.6 m | 143 | 1,800 | Y | 1 | `armco_w_beam` |
| 57 | `armco_spacer_block` | Armco spacer block | 2.6 m | 476 | 3,641 | Y | 1 | `armco_post`, `armco_w_beam` |
| 55 | `armco_splice_bolt` | Splice bolt set | 2.6 m | 119 | 6,862 | Y | 1 | `armco_w_beam` |
| 52 | `armco_w_beam` | Armco W-beam panel | 2.6 m | 445 | 1,821 | Y | 1 | `armco_post` |
| 53 | `catch_fence_post` | Catch fence post | 2.6 m | 2160+ | 690 | Y | 1 | - |
| 68 | `barrier_cable_conduit` | Barrier cable conduit run | 3.0 m | 100 | 9 | Y | 1 | `armco_post` |
| 71 | `barrier_foot_kerb` | Barrier foot kerb / edge beam | 3.0 m | 187 | 1 | Y | 1 | - |
| 72 | `barrier_junction_box` | Cable junction box | 3.0 m | 373 | 65 | Y | 1 | `barrier_cable_conduit` |
| 107 | `tyre_wall_belt_facing` | Conveyor belt facing | 3.8 m | 707 | 60 | Y | 1 | `tyre_wall_tyre` |
| 109 | `tyre_wall_bolt_plate` | Tyre wall bolt plate & washer | 3.8 m | 195 | 400 | Y | 1 | `tyre_wall_belt_facing` |
| 110 | `tyre_wall_through_rod` | Tyre wall through rod | 3.8 m | 33 | 600 | Y | 1 | `tyre_wall_tyre` |
| 106 | `tyre_wall_tyre` | Tyre wall tyre | 3.8 m | 389 | 2,255 | Y | 1 | - |
| 114 | `armco_terminal` | Armco terminal end | 4.0 m | 933 | 120 | Y | 1 | `armco_w_beam` |
| 142 | `catch_fence_base_collar` | Fence post base collar | 4.2 m | 295 | 690 | Y | 2 | `catch_fence_post` |
| 143 | `catch_fence_cranked_head` | Cranked fence head & top rail | 4.2 m | 800 | 690 | Y | 2 | `catch_fence_post` |
| 140 | `catch_fence_mesh_panel` | Catch fence mesh panel | 4.2 m | 2160+ | 665 | Y | 2 | `catch_fence_post` |
| 144 | `catch_fence_woven_wire` | Woven wire (real 3-D) | 4.2 m | 4 | 2,080 | Y | 2 | `catch_fence_mesh_panel` |
| 155 | `concrete_barrier_block` | Precast concrete barrier block | 6.0 m | 622 | 125 | Y | 2 | - |
| 161 | `concrete_lifting_eye` | Concrete block lifting eye | 6.0 m | 62 | 250 | Y | 2 | `concrete_barrier_block` |
| 195 | `tecpro_anchor` | TecPro anchor bracket & bolt | 8.0 m | 116 | 1,400 | Y | 2 | `tecpro_block_blue` |
| 184 | `tecpro_block_blue` | TecPro block (blue body) | 8.0 m | 420 | 4,200 | Y | 2 | - |
| 196 | `tecpro_block_red` | TecPro block (red cap course) | 8.0 m | 233 | 1,400 | Y | 2 | `tecpro_block_blue` |
| 197 | `tecpro_strap` | TecPro strap & buckle | 8.0 m | 62 | 2,800 | Y | 2 | `tecpro_block_blue` |
| 298 | `gate_latch_hardware` | Gate latch & hinge hardware | 12.7 m | 73 | 56 | Y | 3 | `marshal_access_gate` |
| 252 | `marshal_access_gate` | Marshal access gate | 12.7 m | 559 | 28 | Y | 2 | `armco_w_beam` |

**`armco_post`**  
*varies by:* settlement -57 mm; +/-37 mm lateral wander; +/-0.004 rad lean; galvanising age by maintenance run; impact bend  
The single most-repeated object trackside. Every post is driven, so every post has a slightly different height, lean and collar of disturbed ground. Identical posts on a perfect line is what made the round-1 barriers read as 'smeared plastic'.

**`armco_reflector`**  
*varies by:* missing ~10 %; dirt film; colour by side  

**`armco_spacer_block`**  
*varies by:* crush; rust at the bolt  

**`armco_splice_bolt`**  
*varies by:* 3.5 % missing BY DESIGN; nut orientation; rust bloom; thread protrusion  
6,862 of them and 3.5 % are missing. That deliberate absence is worth more than any shader.

**`armco_w_beam`**  
*varies by:* 3.86-4.09 m panels; 3-beam vs 2-beam in 70 m blocks; 38 incident scars (brush 44 %, hit 34 %, repaired 15 %, heavy 7 %); 9 fictional liveries on 30 % of runs  
ARMCO_TOP = 1.012 m (FIA 3-beam). The profile must be a true W with correct return lips - at 2.6 m from the doppler hover the section is fully readable. Incident scars are depth 10-190 mm over 5-30 m; 72 % of them on the outside.

**`catch_fence_post`**  
*varies by:* 6.00 m long, 1.20 m embed, 8.00 m centres; lean; galvanising age; base collar of disturbed ground  
The doppler hover sits 4.2 m from these. A post that is perfectly plumb every 8 m for 3.6 km is the tell.

**`barrier_cable_conduit`**  
*varies by:* clip pitch; sag; splice sleeve  

**`barrier_foot_kerb`**  
*varies by:* settlement; grass encroachment; buried sections  
439 m of ARCH_RetainEdge exists as a cast edge beam with weep pipes every 4th panel and a bollard where the drop exceeds 280 mm. Keep the rule: nothing where the drop is under 10 mm.

**`barrier_junction_box`**  
*varies by:* lid open; gland count; number label  

**`tyre_wall_belt_facing`**  
*varies by:* belt width; fixing washer rows; sag between fixings; fray at the cut edge; ply visible at the edge  
The rubber conveyor belt strapped across the face. Its sag between bolts is the difference between a tyre wall and a stack of doughnuts.

**`tyre_wall_bolt_plate`**  
*varies by:* rust; deformation; missing  

**`tyre_wall_through_rod`**  
*varies by:* protrusion; thread; nut orientation  

**`tyre_wall_tyre`**  
*varies by:* 4 archetypes (slick / wet / road / truck); age; sidewall lettering; UV chalking; compression flat at the bottom of a stack; water line inside  
370 px at 4 m from the T4 hairpin station. The tyres BEHIND the hairpin camera are in shot the whole time the car yaws. Compression flattening down a stack and the dark water line inside the bead are the two details that sell it.

**`armco_terminal`**  
*varies by:* flared vs ramped-to-ground; anchor cable; impact damage  
A barrier run that stops square is a placeholder. Terminals ramp, flare or turn away.

**`catch_fence_base_collar`**  
*varies by:* concrete vs driven; grass encroachment; heave  

**`catch_fence_cranked_head`**  
*varies by:* crank angle; barbed vs plain top  

**`catch_fence_mesh_panel`**  
*varies by:* tension sag; splice line; local dents; algae at the base  
KNOWN APPROXIMATION: the weave is ANALYTIC everywhere except the doppler window (s 2495-2615, side -1) where real 3-D wire is built. The arcminute argument is 4.5 arcmin (3.5 px) per wire at 4 m - so the analytic version is defensible, but set_fence_fade(scene) MUST be called by the render orchestrator or the weave resolves wrong at non-4K sizes.

**`catch_fence_woven_wire`**  
*varies by:* 5.2 mm wire, 0.050 pitch, 10.4 % coverage per layer, 19.7 % combined; kink at the knuckles  
Only in WIRE_WINDOWS (s 2495-2615, side -1) - the doppler hover looks THROUGH this at the car. It is 4.2 m from the lens and backlit by a 12.5 deg sun. This is the one place the analytic cheat would be caught.

**`concrete_barrier_block`**  
*varies by:* board-mark; chipped nose; joint step; brand panel on 30 %  

**`concrete_lifting_eye`**  
*varies by:* bent; rust; grouted over  

**`tecpro_anchor`**  
*varies by:* grout; rust streak down the block  

**`tecpro_block_blue`**  
*varies by:* 3 rows deep; UV chalking on the sun face; scuffs; deformation memory from impacts; strap tension  
T1, T4 and T12 (three-layer at T4 and T12). Real TecPro is a closed-cell foam core in a polyethylene shell with visible mould seams, lifting handles and bolt bosses. A smooth blue box is the placeholder.

**`tecpro_block_red`**  
*varies by:* as blue, plus faster UV fade on the red pigment  

**`tecpro_strap`**  
*varies by:* tension; fray; buckle orientation  

**`gate_latch_hardware`**  
*varies by:* sag; grease; padlock  

**`marshal_access_gate`**  
*varies by:* open/closed; hinge droop; latch; chevron panel; wear at the gate mouth  
28 gates from 16 GATE_STATIONS. Marshal posts within 55 m of a station are pulled to it, so gates and posts read as one facility.

---

### `bridges` - Le Pont de la Plongee

30 m span, 6 m deck, soffit +6.80 over s=2410. The camera threads UNDER it at ~5 m altitude and 300 km/h with 1.8 m of clearance - the soffit fills the frame.

*9 items, 7 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 32 | `pont_service_duct` | Soffit service duct & cable tray | 1.8 m | 187 | 1 | Y | 1 | `pont_soffit_panel` |
| 30 | `pont_soffit_panel` | Le Pont de la Plongee - deck soffit | 1.8 m | 436 | 1 | Y | 1 | `pont_girder` |
| 44 | `pont_girder` | Pont de la Plongee girder | 2.5 m | 1210 | 4 | Y | 1 | - |
| 90 | `pont_banner` | Pont de la Plongee fascia banner | 3.0 m | 1493 | 2 | Y | 1 | `pont_girder` |
| 65 | `pont_deck_slab` | Pont de la Plongee deck slab | 3.0 m | 1244 | 1 | Y | 1 | `pont_girder` |
| 91 | `pont_scupper` | Deck scupper & downpipe | 3.0 m | 373 | 4 | Y | 1 | `pont_deck_slab` |
| 124 | `pont_parapet` | Pont de la Plongee parapet | 4.0 m | 1027 | 2 | Y | 1 | `pont_deck_slab` |
| 366 | `pont_abutment` | Pont de la Plongee abutment | 18.1 m | 825 | 2 |   | 4 | - |
| 367 | `pont_bearing_pad` | Bearing pad & plinth | 18.1 m | 52 | 4 |   | 4 | `pont_abutment` |

**`pont_service_duct`**  
*varies by:* clip pitch; sag; junction box  
At 1.8 m this is what the audience actually sees of the bridge.

**`pont_soffit_panel`**  
*varies by:* girder shadow lines; efflorescence; drainage staining; bird mess; cable trays  
THE CAMERA THREADS UNDER THIS AT 1.8 m OF CLEARANCE AT 300 km/h. Soffit at +6.80 over s=2410, camera at ~5 m. It fills the frame for about 8 frames and it is the last thing before the doppler hover. A blank grey plane here is a hole in the film.

**`pont_girder`**  
*varies by:* web stiffeners; bolt clusters; paint system; camber  
1.35 m deep girders, 30 m span, 6.0 m deck. Origin world (-617.56, 94.75), heading 295.4 deg.

**`pont_banner`**  
*varies by:* invented brand; sag; both faces different  

**`pont_deck_slab`**  
*varies by:* wearing surface; kerb; joint  

**`pont_scupper`**  
*varies by:* staining plume below  
The stain below a scupper is the cheapest realism on any bridge.

**`pont_parapet`**  
*varies by:* mesh infill; post pitch; impact bend  

**`pont_abutment`**  
*varies by:* wing wall; board-mark; drainage  
Abutment tops at ground_z(2410, +/-15) = +3.984 and +3.548 - they differ by 436 mm, so the two ends of this bridge are NOT symmetric. Build to the numbers.

**`pont_bearing_pad`**  
*varies by:* elastomer bulge; dirt shelf  

---

### `trackside` - Trackside dressing

25 marshal posts, 584 barrier boards, 80 fence banners, 13 hoardings, 24 braking boards, 15 corner plates, 15 TV masts, 129 tyre stacks.

*35 items, 32 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 40 | `advertising_board` | Barrier-face advertising board | 2.1 m | 1422 | 584 | Y | 1 | `armco_w_beam` |
| 141 | `catch_fence_banner` | Catch fence banner | 4.2 m | 1244 | 80 | Y | 2 | `catch_fence_mesh_panel` |
| 147 | `apex_sponsor_board` | Apex low sponsor board | 5.0 m | 523 | 17 | Y | 2 | - |
| 157 | `marshal_absorbent_bin` | Absorbent granule bin | 6.0 m | 436 | 25 | Y | 2 | `marshal_post_deck` |
| 163 | `marshal_broom` | Broom, shovel & rake | 6.0 m | 871 | 75 | Y | 2 | `marshal_post_deck` |
| 158 | `marshal_chair` | Marshal folding chair | 6.0 m | 529 | 50 | Y | 2 | `marshal_post_deck` |
| 164 | `marshal_figure_flagging` | Marshal - flagging | 6.0 m | 1089 | 25 | Y | 2 | `marshal_overall`, `marshal_flag` |
| 159 | `marshal_flag` | Marshal flag (set) | 6.0 m | 467 | 175 | Y | 2 | `marshal_flag_rack` |
| 160 | `marshal_flag_rack` | Marshal flag rack | 6.0 m | 622 | 25 | Y | 2 | - |
| 167 | `marshal_light_panel` | Marshal light panel | 6.0 m | 311 | 25 | Y | 2 | `marshal_post_column` |
| 130 | `marshal_post_column` | Marshal post frame column | 6.0 m | 1742 | 120 | Y | 1 | - |
| 131 | `marshal_post_deck` | Marshal post platform deck | 6.0 m | 560 | 25 | Y | 1 | `marshal_post_column` |
| 168 | `marshal_post_handrail` | Marshal post handrail | 6.0 m | 622 | 25 | Y | 2 | `marshal_post_deck` |
| 169 | `marshal_post_roof` | Marshal post roof panel | 6.0 m | 62 | 25 | Y | 2 | `marshal_post_column` |
| 170 | `marshal_post_screen` | Marshal post debris screen | 6.0 m | 1120 | 25 | Y | 2 | `marshal_post_column` |
| 171 | `marshal_post_sign` | Marshal post number sign | 6.0 m | 218 | 25 | Y | 2 | `marshal_post_column` |
| 172 | `marshal_post_stair` | Marshal post stair | 6.0 m | 996 | 25 | Y | 2 | `marshal_post_deck` |
| 173 | `marshal_telephone` | Marshal post telephone box | 6.0 m | 249 | 25 | Y | 2 | `marshal_post_column` |
| 174 | `marshal_water_cooler` | Water cooler | 6.0 m | 684 | 25 | Y | 2 | `marshal_post_deck` |
| 176 | `tyre_stack_trackside` | Trackside tyre stack | 6.0 m | 1120 | 129 | Y | 2 | `tyre_wall_tyre` |
| 219 | `corner_name_plate` | Corner name plate | 10.0 m | 149 | 15 | Y | 2 | `corner_number_plate` |
| 213 | `corner_number_plate` | Corner number plate | 10.0 m | 299 | 15 | Y | 2 | - |
| 229 | `distance_marker_board` | Braking distance marker board | 10.0 m | 448 | 24 | Y | 2 | - |
| 287 | `free_standing_hoarding` | Free-standing hoarding | 12.0 m | 996 | 13 | Y | 3 | `hoarding_leg` |
| 282 | `hoarding_leg` | Hoarding leg frame & ballast | 12.0 m | 622 | 36 | Y | 3 | - |
| 288 | `info_gate_sign` | Information & gate sign | 12.0 m | 311 | 16 | Y | 3 | - |
| 296 | `tv_camera_body` | TV camera body & lens | 12.0 m | 155 | 15 | Y | 3 | `tv_camera_housing` |
| 297 | `tv_camera_cable` | TV camera cable loom | 12.0 m | 21 | 15 | Y | 3 | `tv_camera_mast` |
| 250 | `tv_camera_housing` | TV camera housing | 12.0 m | 140 | 15 | Y | 2 | - |
| 251 | `tv_camera_mast` | Trackside TV camera mast | 12.0 m | 1369 | 15 | Y | 2 | `tv_camera_housing` |
| 313 | `tv_camera_platform` | TV camera operator platform | 14.0 m | 267 | 8 | Y | 3 | `tv_camera_mast` |
| 383 | `recovery_tractor` | Recovery tractor | 20.0 m | 448 | 8 | Y | 4 | `marshal_access_gate` |
| 407 | `ambulance` | Ambulance | 25.0 m | 388 | 4 |   | 4 | - |
| 421 | `fire_tender` | Fire tender | 28.0 m | 400 | 2 |   | 5 | - |
| 427 | `recovery_crane_truck` | Recovery crane truck | 30.0 m | 398 | 3 |   | 5 | - |

**`advertising_board`**  
*varies by:* 31 invented brands, 698 distinct signatures, 0 duplicates; 2.0-4.6 m x 0.62-1.00 m; age = 0.04 + 0.80u^3; edge lift; grime line  
Mounted 50 mm PROUD of the barrier face - that standoff shadow is what makes it a board and not a painted stripe. Runs of 9-46 m, skipped over concrete.

**`catch_fence_banner`**  
*varies by:* invented brand; starts at Armco top 1.012 m; sag; wind lift at loose corners; sun bleach  

**`apex_sponsor_board`**  
*varies by:* invented brand; ground-level grime; leaning  

**`marshal_absorbent_bin`**  
*varies by:* lid; fill; scoop  

**`marshal_broom`**  
*varies by:* leaning vs lying; bristle wear; handle grime  
Leaning against the post. Cheap, and it is the single clearest sign a place is used.

**`marshal_chair`**  
*varies by:* occupied; angle; fabric fade  

**`marshal_figure_flagging`**  
*varies by:* flag furled and held / raised / waved; body turned up-track; one hand shielding the eyes  
One per post, and the pose must be turned UP-TRACK - a marshal facing the wrong way is a defect anybody notices.

**`marshal_flag`**  
*varies by:* yellow, double yellow, blue, red, white, green, chequered, oil; rolled vs furled vs held; fabric age; pole tape  
Seven distinct flags. A rolled flag is a soft cylinder with a taper and a loose tail, not a tube.

**`marshal_flag_rack`**  
*varies by:* flag count; rack lean; empty slots  

**`marshal_light_panel`**  
*varies by:* yellow/blue LED; sun hood; unlit for this film  

**`marshal_post_column`**  
*varies by:* scaffold tube vs box section; base plate & pins; paint  

**`marshal_post_deck`**  
*varies by:* 4 archetypes (open canopy, box hut, equipment stand, raised platform); deck board gaps; wear path; height above grade  
25 posts, max gap 253.9 m, min sight-line clearance +0.41 m. The rejected render showed this as flat cardboard - it needs board gaps, a wear path, and things stored under the deck.

**`marshal_post_roof`**  
*varies by:* corrugated vs flat; ponding; algae streak; one sheet lifted  

**`marshal_post_screen`**  
*varies by:* mesh; dents; sponsor panel  

**`marshal_post_sign`**  
*varies by:* post number; fade; fixing rust; slight lean  
'POSTE 7'. Small, and it is the thing that names the place.

**`marshal_post_stair`**  
*varies by:* tread wear; handrail polish  

**`marshal_telephone`**  
*varies by:* handset hung; cable coil; door open  

**`marshal_water_cooler`**  
*varies by:* bottle fill; cup stack  

**`tyre_stack_trackside`**  
*varies by:* height 2-7; capped/open; belted/not; upright/toppled; 4 tyre archetypes  
129 stacks / 543 tyres at gates, post pads and 4 service laybys. A toppled stack is worth ten upright ones.

**`corner_name_plate`**  
*varies by:* the spec's own names disagree - T12 is 'La Plongee' / 'T12 Doppler' / 'T12 Plongee'. NORMALISE before building.  
Naming inconsistencies to resolve: T12 (three names), S4/T5 (both called 'La Rampe').

**`corner_number_plate`**  
*varies by:* digit; frame; lean; fade  

**`distance_marker_board`**  
*varies by:* 300/250/200/150/100/50; post lean; board dish; fade; back face different  
24 boards. Full set before T1 (93.8 m stop from 330.8 km/h), 200-50 at T4, 250-50 at La Plongee, shorter sets at T5, T10, T15. Measured back from s_apex - arc/2.

**`free_standing_hoarding`**  
*varies by:* 6.0-13.5 m x 2.4-4.0 m; 2-4 panels; 2-3 legs; 55 m minimum separation; panel joint misalignment  

**`hoarding_leg`**  
*varies by:* ballast block; ground settlement  

**`info_gate_sign`**  
*varies by:* sector split / access gate / medical point; post lean; fade  

**`tv_camera_body`**  
*varies by:* lens hood; tally light; viewfinder  

**`tv_camera_cable`**  
*varies by:* drip loop; cable ties; ground pin  

**`tv_camera_housing`**  
*varies by:* pan/tilt angle - they should be TRACKING THE CAR at each moment; sun hood; weather cover  
The one variation axis that matters here is aim: a row of cameras pointing at nothing is worse than no cameras.

**`tv_camera_mast`**  
*varies by:* 3.2-5.6 m; guy wires; ladder; base ballast  
One per ~245 m, biased to corner outsides.

**`tv_camera_platform`**  
*varies by:* deck; rail; sandbags  

**`recovery_tractor`**  
*varies by:* crane arm stowed/raised; flashing beacon unlit; mud on the tyres; parked behind the barrier at a gate  
Parked at recovery gates. One of the most recognisable trackside objects there is and it is currently absent.

**`ambulance`**  
*varies by:* rear doors closed; light bar unlit; crew standing beside it  

**`fire_tender`**  
*varies by:* hose reels; ladder; crew kit on the ground  

**`recovery_crane_truck`**  
*varies by:* boom stowed; outriggers; strop set on the deck  

---

### `vegetation` - Terrain, treeline & ground cover

24,622 woodland trees, 38,738 shrubs, 1,432,086 grass clumps. Grass reaches 3.5 m of the lens at s=2502 and sits directly under the doppler hover at 2.4 m.

*35 items, 22 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 27 | `moss_patch` | Moss patch | 1.7 m | 546 | 3,000 | Y | 1 | `paddock_paving_bay` |
| 28 | `weed_joint_colonist` | Weed in a joint | 1.7 m | 546 | 40,000 | Y | 1 | `paddock_paving_bay` |
| 42 | `grass_clump_fescue` | Grass clump - fescue | 2.4 m | 436 | 500,000 | Y | 1 | `terrain_ground` |
| 41 | `terrain_ground` | Terrain ground surface | 2.4 m | 467 | 1 | Y | 1 | - |
| 97 | `grass_clump_dry` | Grass clump - dry / scorched | 3.5 m | 267 | 200,000 | Y | 1 | `terrain_ground` |
| 98 | `grass_clump_meadow` | Grass clump - meadow | 3.5 m | 373 | 350,000 | Y | 1 | `terrain_ground` |
| 99 | `grass_clump_tussock` | Grass clump - tussock | 3.5 m | 480 | 300,000 | Y | 1 | `terrain_ground` |
| 149 | `grass_clump_reed` | Grass clump - reed | 5.0 m | 672 | 80,000 | Y | 2 | `verge_swale` |
| 190 | `fern_clump` | Fern clump | 8.0 m | 327 | 7,162 | Y | 2 | `terrain_ground` |
| 194 | `shrub_bramble` | Shrub - bramble | 8.0 m | 560 | 10,000 | Y | 2 | `terrain_ground` |
| 232 | `leaf_litter` | Leaf litter patch | 10.0 m | 112 | 4,000 | Y | 2 | `tree_oak` |
| 236 | `rock_scree_stone` | Rock - scree stone | 10.0 m | 56 | 20,000 | Y | 2 | `terrain_ground` |
| 237 | `shrub_gorse` | Shrub - gorse | 10.0 m | 523 | 9,000 | Y | 2 | `terrain_ground` |
| 281 | `fallen_branch` | Fallen branch | 12.0 m | 62 | 1,200 | Y | 3 | `tree_oak` |
| 293 | `shrub_broom` | Shrub - broom | 12.0 m | 498 | 6,000 | Y | 3 | `terrain_ground` |
| 294 | `shrub_hazel` | Shrub - hazel | 12.0 m | 1089 | 8,000 | Y | 3 | `terrain_ground` |
| 295 | `shrub_juniper` | Shrub - juniper | 12.0 m | 342 | 5,700 | Y | 3 | `terrain_ground` |
| 305 | `tree_london_plane` | Tree - London plane | 14.0 m | 2160+ | 3,000 | Y | 3 | - |
| 353 | `tree_sapling` | Sapling | 16.0 m | 700 | 5,488 |   | 4 | - |
| 360 | `tree_hawthorn` | Tree - hawthorn | 18.0 m | 1244 | 3,400 | Y | 4 | - |
| 372 | `drainage_ditch` | Drainage ditch | 20.0 m | 149 | 40 |   | 4 | `verge_swale` |
| 378 | `hedgerow_section` | Hedgerow section | 20.0 m | 560 | 600 |   | 4 | `tree_hawthorn` |
| 384 | `rock_boulder` | Rock - boulder | 20.0 m | 224 | 800 |   | 4 | `terrain_ground` |
| 387 | `tree_italian_cypress` | Tree - Italian cypress | 20.0 m | 2160+ | 1,400 |   | 4 | - |
| 405 | `field_boundary_fence` | Field boundary fence post & wire | 25.0 m | 179 | 2,000 |   | 4 | - |
| 412 | `log_pile` | Log pile | 25.0 m | 179 | 30 |   | 4 | `fallen_branch` |
| 415 | `tree_dead_standing` | Tree - dead standing timber | 25.0 m | 1643 | 1,300 | Y | 4 | - |
| 416 | `tree_lombardy_poplar` | Tree - Lombardy poplar | 25.0 m | 2160+ | 4,000 |   | 4 | - |
| 417 | `tree_rowan` | Tree - rowan | 25.0 m | 1344 | 1,800 |   | 4 | - |
| 423 | `tree_crack_willow` | Tree - crack willow | 28.0 m | 1733 | 2,600 |   | 5 | - |
| 262 | `tree_oak` | Tree - pedunculate oak | 30.0 m | 2116 | 4,500 | Y | 2 | - |
| 428 | `tree_scots_pine` | Tree - Scots pine | 30.0 m | 2160+ | 4,200 |   | 5 | - |
| 429 | `tree_silver_birch` | Tree - silver birch | 30.0 m | 1742 | 3,200 |   | 5 | - |
| 431 | `farm_gate` | Farm gate | 35.0 m | 139 | 20 |   | 5 | `field_boundary_fence` |
| 435 | `escarpment_skyline` | T4 escarpment skyline | 60.0 m | 355 | 1 | Y | 6 | - |

**`moss_patch`**  
*varies by:* north-face bias; wet sheen  

**`weed_joint_colonist`**  
*varies by:* species; height; seed head; ~18 % of paving bays  
1.7 m from the lens on the forecourt. Weeds in saw joints are the single strongest 'this place is real' signal in the whole paddock.

**`grass_clump_fescue`**  
*varies by:* 54-98 blades per 0.21-0.33 m tuft; wind lean 15 deg x 0.55-1.55 on bearing 65 deg; scale drops 42 % where mown  
467 px tall directly under the doppler hover, and 3.5 m from the lens at s=2502. Blades must resolve individually there. 460 clumps per station-metre per side, ~9/m2 at the verge falling to ~2 at 46 m out.

**`terrain_ground`**  
*varies by:* 8 baked vertex attributes: wet, wear, cover, mown, hedge, dry, field (RGB crop), dist  
805 x 793 grid over 21.7 x 21.7 km. The doppler hover stands 2.4 m above it. KNOWN LIMIT: slope is not baked as a vertex attribute - it is read from the shading normal at render time. Also: every terrain material must be RE-CHECKED against the contract's lambert_radiance, because terrain's own lighting assumptions (direct:diffuse 3.00:1) are superseded by the measured 2.072:1 - shadows are 45 % brighter relative to key than the turf albedo was tuned for. That mismatch is the direct cause of the 'pink and green blotches'.

**`grass_clump_dry`**  
*varies by:* bleach; collapse  

**`grass_clump_meadow`**  
*varies by:* seed heads; colour by ter_dry  

**`grass_clump_tussock`**  
*varies by:* dead centre; flowering stems; lean  

**`grass_clump_reed`**  
*varies by:* in the swales only; seed plume  

**`fern_clump`**  
*varies by:* unfurl stage; brown fraction  

**`shrub_bramble`**  
*varies by:* arching canes; berry; dead cane fraction  
OPEN ITEM: all 5 shrub species come from ONE generator with different parameters, unlike the 10 independent tree structures. build_terrain's own note: 'if the camera ever gets within ~15 m of the undergrowth, that is the layer to rebuild next.' It does - the paddock planters are at 14 m and the verge shrubs at ~8 m.

**`leaf_litter`**  
*varies by:* species mix matching the tree above; wind drift into corners  

**`rock_scree_stone`**  
*varies by:* angularity; sorting by size down a slope  

**`shrub_gorse`**  
*varies by:* spine density; flower; dead core  

**`fallen_branch`**  
*varies by:* decay stage; bark loss; part-buried in leaf litter  

**`shrub_broom`**  
*varies by:* green stem; flower  

**`shrub_hazel`**  
*varies by:* multi-stem coppice; leaf size  

**`shrub_juniper`**  
*varies by:* prostrate vs upright; berry  

**`tree_london_plane`**  
*varies by:* bark plate mottling; pollard scars; avenue vs woodland form  
26 % of the plateau/paddock mix, and the species of the 24-tree paddock avenue at 14 m.

**`tree_sapling`**  
*varies by:* species; browse damage; stake & tie  

**`tree_hawthorn`**  
*varies by:* 45 % of hedgerows at 0.55-0.85 of species height; wind-shear form; berry load  

**`drainage_ditch`**  
*varies by:* water; reed; bank erosion  

**`hedgerow_section`**  
*varies by:* flail-cut top; gaps; standard trees in the line  

**`rock_boulder`**  
*varies by:* bedding orientation; lichen; partial burial  

**`tree_italian_cypress`**  
*varies by:* 14 % of the paddock mix; column form; splay at the top of older ones  

**`field_boundary_fence`**  
*varies by:* post lean; wire sag; staple rust; strainer post at corners  
Cheap, and the thing that makes farmland read as farmland rather than a green noise field.

**`log_pile`**  
*varies by:* stacked vs tipped; sawn end weathering  

**`tree_dead_standing`**  
*varies by:* 7.5 % of the mix; broken top; bark loss; woodpecker holes; lean  
The single best silhouette element in a treeline, and the one that stops a wood looking generated.

**`tree_lombardy_poplar`**  
*varies by:* fastigiate form; wind set; height variation in a row  

**`tree_rowan`**  
*varies by:* berry load; upright form  

**`tree_crack_willow`**  
*varies by:* 28 % of the damp low-ground mix; split trunk; low sweep  

**`tree_oak`**  
*varies by:* 3 LODs x 8/12/16 base meshes; age; lean; dead limbs; ivy  
L0 hero under 95 m has 6 branch orders and 30-57k leaves. OPEN ITEM from build_terrain: birch is 20 % of the base mix plus 7.5 % dead timber, so a quarter of every treeline is a pale stem and it reads as 'a birch wood' everywhere - the fix is to drop birch to ~0.13 and weight to oak and hawthorn.

**`tree_scots_pine`**  
*varies by:* 40 % of the exposed ridge mix; bare lower trunk; orange upper bark  

**`tree_silver_birch`**  
*varies by:* bark banding; weeping crown; REDUCE from 20 % to ~13 % of the base mix  

**`farm_gate`**  
*varies by:* open/closed; sag; baler-twine hinge  

**`escarpment_skyline`**  
*varies by:* ridge silhouette; suppressed woodland on the near lip  
OPEN DEFECT from build_terrain: 'the escarpment beyond T4 does not read from the kerb-height hairpin camera - the treeline sits on the near lip and occludes it.' The whole point of the hairpin station is that the car is silhouetted against distant terrain and sky. The fix is placement: suppress woodland inside the hairpin's outward fan. This is a hero item because it is the BACKGROUND of the film's best shot.

---

### `people` - Figures

A private shakedown, not a race meeting: empty grandstands, a manned marshal chain, a small crew presence in the paddock, two or three photographers. Everyone trackside is fully covered - overalls, helmet, gloves - which is what makes them tractable.

*15 items, 12 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 63 | `driver_figure` | Driver figure | 3.0 m | 523 | 1 | Y | 1 | `crew_headset` |
| 79 | `driver_gloves` | Driver gloves | 3.0 m | 179 | 2 | Y | 1 | `driver_figure` |
| 80 | `driver_helmet` | Driver helmet | 3.0 m | 209 | 1 | Y | 1 | `driver_figure` |
| 81 | `driver_race_suit` | Driver race suit & HANS | 3.0 m | 411 | 1 | Y | 1 | `driver_figure` |
| 118 | `driver_boots_and_feet` | Driver boots | 4.0 m | 112 | 2 | Y | 1 | `driver_figure` |
| 165 | `marshal_figure_seated` | Marshal - seated | 6.0 m | 809 | 45 | Y | 2 | `marshal_chair`, `marshal_overall` |
| 166 | `marshal_figure_standing` | Marshal - standing | 6.0 m | 1089 | 90 | Y | 2 | `marshal_overall` |
| 154 | `marshal_overall` | Marshal overall, gloves & helmet | 6.0 m | 1089 | 160 | Y | 2 | - |
| 233 | `paddock_personnel_figure` | Paddock personnel figure | 10.0 m | 653 | 260 | Y | 2 | - |
| 279 | `crew_figure` | Team crew figure (fireproofs) | 12.0 m | 544 | 120 | Y | 3 | - |
| 247 | `crew_headset` | Crew headset & radio | 12.0 m | 113 | 30 | Y | 2 | `crew_figure` |
| 248 | `hi_vis_tabard` | Hi-vis tabard | 12.0 m | 218 | 140 | Y | 2 | - |
| 369 | `photographer_figure` | Photographer | 20.0 m | 327 | 24 |   | 4 | - |
| 370 | `photographer_rig` | Photographer camera & long lens | 20.0 m | 108 | 24 |   | 4 | `photographer_figure` |
| 386 | `steward_figure` | Steward / security figure | 20.0 m | 327 | 60 |   | 4 | `hi_vis_tabard` |

**`driver_figure`**  
*varies by:* helmet livery (invented); visor tear-off stack; glove grip; HANS tether; harness tension; head and shoulder movement under lateral load; hands working the wheel  
DECIDED: YES. At the T4 hairpin station the cockpit passes within ~3-5 m of a 21 mm lens for 3.9 s while the car yaws 176 degrees, and the onboard follow runs 560 m beside it - an empty seat with a slack harness would be the single most glaring hole in the film. Only the helmet, shoulders, upper arms and hands are ever visible above the cockpit rim, and every one of them is covered, so no skin and no face are needed. The head must move: it stays level under lateral load while the car rolls, and it leads the steering into an apex. A rigidly bolted head is worse than no driver. The Beat-1 tension is resolved and is NOT a build-agent problem: the 'no part seats without having been seen' law governs the 15 CAR clusters from the inventory, and the driver is not one of them - he is a person who gets in, not a part that seats. The beat-sheet owner handles it.

**`driver_gloves`**  
*varies by:* grip pattern on the palm; cuff over the suit sleeve; knuckle folds; wrist strap  
Hands on the wheel at 3 m. The SW cluster already resolves to macro standard - gloves that do not match that standard will be the weak point of the frame.

**`driver_helmet`**  
*varies by:* invented livery; tear-off stack thickness; visor scratches and bug strikes; strap and D-ring; aero tab  
209 px at 3.0 m through a 21 mm lens at the hairpin station. The tear-off stack on the visor and the raking reflection across it are the two things that make a helmet look like it is being worn rather than displayed. Invented livery only.

**`driver_race_suit`**  
*varies by:* invented team colours; shoulder and collar folds under the belts; HANS tether routing; embroidered badges as geometry  
Only the shoulders, upper arms and the top of the chest are ever visible above the cockpit rim - build for that framing. The belt-over-shoulder compression is the detail.

**`driver_boots_and_feet`**  
*varies by:* thin sole; ankle fold  
Barely visible in the footwell, but the footwell is modelled (CI_footwell) and an empty one is worse than a cheap boot.

**`marshal_figure_seated`**  
*varies by:* slump; leg cross; leaning on the rail  

**`marshal_figure_standing`**  
*varies by:* posture (watching / turned / holding a flag / on the phone); overall age & fit; glove state; helmet vs cap; build  
261 px at 25 m, and 6.0 m at the T4 inside post. Fully covered - overall, gloves, helmet or balaclava - so no skin is needed, which is what makes this tractable. Two marshals in identical poses is worse than one.

**`marshal_overall`**  
*varies by:* orange fade by age; knee/elbow dirt; cuff & collar fit; reflective banding wear  
The garment is the character. Cloth fold at the elbow, knee and waist is 100 % of the read at 6 m.

**`paddock_personnel_figure`**  
*varies by:* polo & cap; lanyard; carrying something; walking vs standing  
A race-weekend paddock is busy. HARDER than the trackside figures: exposed forearms, neck and face. Keep them at 10 m+, in caps and sunglasses, in groups rather than evenly spread, and never let one be the focal subject of a frame.

**`crew_figure`**  
*varies by:* posture; kneeling/standing/carrying; helmet & visor state; headset; team colour  
The generic garage/paddock crew figure. The POSED pit-stop roles are separate rows (crew_wheel_gunner, crew_tyre_carrier_off/on, crew_jack_operator_front/rear, crew_stabiliser, crew_release_operator, crew_mechanic_kneeling/standing, crew_pitlane_fire_marshal) because a crew all standing identically is the same failure as one tree spammed a hundred times. Completely covered - helmet, visor, balaclava, fireproofs, gloves - zero exposed skin.

**`crew_headset`**  
*varies by:* boom mic position; cable route; belt pack  

**`hi_vis_tabard`**  
*varies by:* fade; ride-up; open/closed  

**`photographer_figure`**  
*varies by:* crouched / standing / panning; tabard; bag on the hip  

**`photographer_rig`**  
*varies by:* lens length; monopod; hood  

**`steward_figure`**  
*varies by:* hi-vis; radio; standing at a gate  

---

### `crowd` - Crowd & spectator infrastructure

A RACE WEEKEND, not a private test. 18,350 seats at 82 % occupancy = 15,050 figures in the 600 m grandstand band, plus general-admission banking at six corners. Nearest seated spectator is 14.7 m under the Beat-6 crane-out; the closest civilians in the entire film are the ones leaning over La Passerelle's parapet at 7.1 m, seen from directly underneath.

*33 items, 21 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 183 | `passerelle_crowd_at_parapet` | La Passerelle crowd at the parapet | 7.1 m | 920 | 60 | Y | 2 | `la_passerelle_mesh`, `la_passerelle_deck` |
| 249 | `pedestrian_crowd_barrier` | Pedestrian crowd barrier | 12.0 m | 342 | 900 | Y | 2 | - |
| 254 | `crowd_density_field` | Crowd density & occupancy field | 14.7 m | 254 | 1 | Y | 2 | `grandstand_riser_unit` |
| 318 | `crowd_flag_handheld` | Handheld crowd flag | 14.7 m | 122 | 900 | Y | 3 | `spectator_seated` |
| 319 | `crowd_idle_motion` | Crowd idle motion layer | 14.7 m | 254 | 1 | Y | 3 | `crowd_density_field`, `spectator_seated` |
| 320 | `crowd_litter_drift` | Crowd litter under the seats | 14.7 m | 20 | 4,000 | Y | 3 | `grandstand_riser_unit`, `litter_paper_scrap` |
| 322 | `spectator_bag_and_coat` | Bag, coat & belongings on seats | 14.7 m | 81 | 5,000 | Y | 3 | `spectator_seated` |
| 323 | `spectator_child` | Spectator - child | 14.7 m | 193 | 1,150 | Y | 3 | `spectator_seated` |
| 255 | `spectator_clothing` | Spectator clothing layer | 14.7 m | 142 | 19,000 | Y | 2 | - |
| 324 | `spectator_ear_defenders` | Ear defenders & headphones | 14.7 m | 41 | 7,000 | Y | 3 | `spectator_headwear` |
| 317 | `spectator_headwear` | Spectator headwear | 14.7 m | 33 | 11,400 | Y | 3 | `spectator_clothing` |
| 137 | `spectator_seated` | Spectator - seated | 14.7 m | 254 | 7,800 | Y | 1 | `crowd_density_field`, `spectator_clothing` |
| 325 | `spectator_seated_leaning` | Spectator - seated, leaning forward | 14.7 m | 234 | 3,000 | Y | 3 | `spectator_seated` |
| 326 | `spectator_standing_in_row` | Spectator - standing in the row | 14.7 m | 356 | 1,000 | Y | 3 | `spectator_seated` |
| 327 | `spectator_umbrella` | Spectator umbrella / parasol | 14.7 m | 183 | 300 | Y | 3 | `spectator_seated` |
| 328 | `spectator_with_phone` | Spectator - phone raised | 14.7 m | 295 | 1,500 | Y | 3 | `spectator_seated` |
| 338 | `ga_terrace_step` | GA terrace sleeper step | 15.4 m | 61 | 4,000 |   | 4 | `ga_viewing_bank` |
| 257 | `ga_viewing_bank` | General admission viewing bank | 15.4 m | 1455 | 6 | Y | 2 | `terrain_ground` |
| 339 | `spectator_backpack_coolbox` | Backpack & cool box | 15.4 m | 109 | 1,200 |   | 4 | `spectator_standing_ga` |
| 340 | `spectator_folding_stool` | Folding stool / camping chair | 15.4 m | 206 | 900 |   | 4 | `spectator_standing_ga` |
| 256 | `spectator_standing_ga` | Spectator - general admission, standing | 15.4 m | 424 | 3,500 | Y | 2 | `ga_viewing_bank` |
| 341 | `crowd_banner_draped` | Draped crowd banner | 15.5 m | 212 | 120 | Y | 4 | `grandstand_front_rail` |
| 342 | `spectator_standing_at_rail` | Spectator - standing at the front rail | 15.5 m | 337 | 600 | Y | 4 | `grandstand_front_rail` |
| 359 | `big_screen` | Big screen | 17.2 m | 1519 | 3 | Y | 4 | `big_screen_tower` |
| 358 | `big_screen_tower` | Big screen support tower | 17.2 m | 2160+ | 3 |   | 4 | - |
| 374 | `ga_picnic_group` | GA picnic / group cluster | 20.0 m | 112 | 400 |   | 4 | `spectator_standing_ga` |
| 385 | `spectator_entrance_gate` | Spectator entrance gate & turnstile | 20.0 m | 448 | 8 |   | 4 | `pedestrian_crowd_barrier` |
| 388 | `timing_tower` | Timing / scoring tower | 20.7 m | 2160+ | 1 |   | 4 | - |
| 409 | `food_concession_unit` | Food concession unit | 25.0 m | 448 | 14 |   | 4 | - |
| 413 | `merchandise_stall` | Merchandise stall | 25.0 m | 448 | 12 |   | 4 | - |
| 422 | `portable_toilet_block` | Portable toilet block | 28.0 m | 307 | 20 |   | 5 | - |
| 425 | `podium_backdrop` | Podium backdrop | 29.3 m | 510 | 1 |   | 5 | `podium_structure` |
| 424 | `podium_structure` | Podium structure | 29.3 m | 446 | 1 |   | 5 | `pit_building_roof_deck` |

**`passerelle_crowd_at_parapet`**  
*varies by:* leaning over / standing back / holding a phone or camera over the rail; hands and forearms on the rail; bags on the deck  
THE CLOSEST CIVILIAN FIGURES IN THE FILM at 7.1 m - but the geometry is kind: the camera is 1.9 m off the deck passing UNDERNEATH at ~230 km/h, so these are seen from a steep low angle THROUGH the anti-throw mesh, and at 64 m/s with a 180-degree shutter they smear 1.33 m per frame. What actually reads is: undersides of forearms on the rail, chins and hat brims, phones held out over the parapet, and legs behind the mesh. Build for that view - do not build faces for a view that never sees them.

**`pedestrian_crowd_barrier`**  
*varies by:* interlocking steel; lean; bent infill bars; a run pushed out of line where people have leaned on it  
The interlocking hook-and-eye barrier every event on earth uses. Runs of it must NOT be a straight line - people push them.

**`crowd_density_field`**  
*varies by:* 82 % mean occupancy; falloff to ~55 % at the far ends and the top rows; aisles and gangways left clear; friend-groups of 2-6 with gaps between; a few whole blocks nearly empty  
THE item that decides whether 15,050 grandstand occupants read as a crowd or as a grid of dolls. Real crowds are lumpy: people sit in groups with empty seats between groups, gangways stay clear, the expensive rows fill first, the corners of a block go last. A uniform 82 % fill is as wrong as a uniform 100 %. Build this before a single figure is placed - everything else in this zone reads off it.

**`crowd_flag_handheld`**  
*varies by:* invented team; waved / furled / resting on a shoulder; pole length; fabric age  
Must be shaped by the same 65-degree wind bearing as the grass and the sponsor flags.

**`crowd_idle_motion`**  
*varies by:* per-figure phase offset; breathing/settling amplitude 10-40 mm; head tracking the car with a 0.2-0.5 s spread of reaction lag; a travelling wave of standing as the car passes  
WITHOUT THIS THE STAND IS A PHOTOGRAPH OF STATUES and the one-shot illusion dies at the exact moment the camera cranes out. It does not need much: sub-frame settling, heads turning to follow the car with staggered lag, and a standing wave that travels along the stand at the car's speed. Motion blur at 24 fps hides everything else. The reaction lag spread is the detail - a crowd that turns in unison is a chorus line.

**`crowd_litter_drift`**  
*varies by:* programmes; cups; wrappers; drifted to the front of each riser  
Seen from directly above at the end of the film, this is what fills the gaps between people.

**`spectator_bag_and_coat`**  
*varies by:* coat over the seat back; rucksack in the footwell; cushion; folded programme wedged under a thigh  
The clutter of occupancy. A stand full of people and NO belongings is uncanny - this is the layer that says they have been sitting there for three hours.

**`spectator_child`**  
*varies by:* seated / standing on a seat / carried; ear defenders far more common than on adults  
8 % of the crowd. Stature variation is what stops a crowd looking machine-stamped, and children are the cheapest way to get it.

**`spectator_clothing`**  
*varies by:* hue distribution weighted to invented-team colours in blocks, white/grey/black/denim elsewhere; sleeve length; jacket tied round the waist; 3-4 fold sets per garment  
COLOUR DISTRIBUTION IS THE CROWD'S TEXTURE. Uniform random hue reads as television static; real crowds clump into team-colour blocks against a neutral field. Invented brands and invented team colours only. Fabric needs 3-4 real fold sets - at 254 px a flat-shaded torso is visible.

**`spectator_ear_defenders`**  
*varies by:* over-ear defenders; radio headsets with an aerial; around the neck vs worn  
Utterly characteristic of a motorsport crowd and almost never modelled. Widens the head silhouette, which is exactly the scale that reads at 14.7 m.

**`spectator_headwear`**  
*varies by:* cap forwards/backwards; bucket hat; hood up; sun visor; team cap; ~60 % of the crowd  
At 47 px of head, the HAT is a bigger silhouette contributor than the face. This is where the money goes.

**`spectator_seated`**  
*varies by:* 8-12 base postures; lean forward / back / turned to a neighbour / arms folded / arms up; build and stature spread including 8 % children; garment silhouette  
254 px tall, head 47 px, at the closest point of the Beat-6 crane-out. NO FACES: at 47 px a head is a hair shape, a skin value and a suggestion of features - modelling eyes and mouths is wasted work and will read worse than a clean silhouette. Spend the budget on POSTURE and SILHOUETTE instead. Torso angle, shoulder line, knee position and where the arms are is 100 % of the read. A stand where every figure has the same shoulder angle is the crowd equivalent of one tree spammed a hundred times.

**`spectator_seated_leaning`**  
*varies by:* elbows on knees; leaning on the row in front; head turned to follow the car  
The pose that makes a crowd look like it is WATCHING something. At the moment the car passes, the leaning fraction should rise along the stand in a wave - that is free storytelling and it costs one animated parameter.

**`spectator_standing_in_row`**  
*varies by:* cheering / filming / just stood up; arms position; 12-18 % of occupants  
Standing figures break the horizontal banding of a seated stand. Without them the crowd reads as corduroy.

**`spectator_umbrella`**  
*varies by:* open for shade against a 12.5-degree sun; colour; tilt toward the low sun  
A 12.5-degree sun means low raking light - umbrellas tilt toward it, and the shadows they throw across the seating deck are a gift.

**`spectator_with_phone`**  
*varies by:* one arm up / two hands / at chest height; screen unlit (daylight)  
The single most contemporary crowd signal there is. A modern grandstand at the moment a car passes is a field of raised arms; a crowd with none reads as period.

**`ga_terrace_step`**  
*varies by:* timber vs concrete; settlement; erosion behind the riser; missing sections  

**`ga_viewing_bank`**  
*varies by:* earth batter 1:2.5 to 1:3; worn desire lines up the face; bare mud at the crest; grass wear rings where groups stand  
The WEAR is the object. A grassed bank with no desire lines and no bald crest has never had anybody on it.

**`spectator_backpack_coolbox`**  
*varies by:* upright / fallen / open; strap slump  

**`spectator_folding_stool`**  
*varies by:* occupied vs empty; fabric fade; leg sink into soft ground  

**`spectator_standing_ga`**  
*varies by:* on the banking; standing / sitting on the grass / on a folding stool; coats and bags on the ground; clustered at the best sightlines and thin between  
GA banking at six corners. They cluster hard where the sightline is good and thin out to nothing 30 m either side - a uniform smear along the bank is the tell.

**`crowd_banner_draped`**  
*varies by:* invented team/driver; hand-painted vs printed; sag between ties; wind lift at a loose corner; hung over the front rail or a barrier  
Hand-lettered bedsheet banners are what tells you these are fans rather than an audience. Deliberately imperfect lettering.

**`spectator_standing_at_rail`**  
*varies by:* hands on rail; leaning over; holding a phone or a flag; children lifted up  
333 px. The front rail row is the most legible line of people in the film and it is silhouetted against the track.

**`big_screen`**  
*varies by:* louvre pitch; sun shade hood; content unlit or showing a flat colour field; support frame  
Race weekend only. Do NOT put live footage on it - a screen showing the film inside the film is a recursion trap and a continuity liability across one unbroken take. A dark louvred panel with a raking specular is correct and safer.

**`big_screen_tower`**  
*varies by:* lattice; ballast blocks; ladder & cage; cable loom  

**`ga_picnic_group`**  
*varies by:* blanket; cool box; bags; 2-6 people; scattered belongings  

**`spectator_entrance_gate`**  
*varies by:* open/closed; queue rail; signage; accreditation booth  

**`timing_tower`**  
*varies by:* panel grid; unlit; access ladder; sponsor cap  
CAUTION: 20 m tall near the line. Re-run circuit_spec's Beat-6 raycast gate after placing it - that gate exists to protect the last image of the film from exactly this kind of late addition.

**`food_concession_unit`**  
*varies by:* trailer vs container; serving hatch; extraction flue; menu board; bin beside it  

**`merchandise_stall`**  
*varies by:* awning out; hanging stock; invented brands; queue barrier; empty vs busy  

**`portable_toilet_block`**  
*varies by:* rows of 4-12; door open/closed/engaged; hand-wash unit; queue  
Twenty of them in a row is one of the most reliable signals that an event is happening here.

**`podium_backdrop`**  
*varies by:* invented brands in a repeating tile; fabric sag; frame  

**`podium_structure`**  
*varies by:* steps; three-level dais; rail; unoccupied  

---

### `ephemera` - The ephemeral

Litter, stains, marbles, tape, chalk. Individually trivial; collectively the difference between a render and a place.

*16 items, 16 hero.*

| # | id | name | near | px@4K | inst | H | wave | depends on |
|---:|---|---|---:|---:|---:|:-:|---:|---|
| 19 | `dust_drift` | Dust & grit drift at the kerb line | 1.5 m | 15 | 1 | Y | 1 | `kerb_precast_unit` |
| 59 | `scuff_mark_barrier` | Barrier scuff / paint transfer | 2.6 m | 72 | 150 | Y | 1 | `armco_w_beam` |
| 76 | `cable_tie_offcut` | Cable tie & offcut | 3.0 m | 62 | 900 | Y | 1 | `heras_fence_panel` |
| 77 | `chalk_mark` | Chalk / paint spot mark | 3.0 m | 165 | 300 | Y | 1 | - |
| 78 | `cigarette_end` | Cigarette end | 3.0 m | 41 | 600 | Y | 1 | - |
| 83 | `gaffer_tape_strip` | Gaffer tape on the ground | 3.0 m | 103 | 200 | Y | 1 | - |
| 66 | `oil_stain` | Oil stain | 3.0 m | 747 | 300 | Y | 1 | - |
| 92 | `puddle` | Puddle | 3.0 m | 1493 | 120 | Y | 1 | `terrain_ground` |
| 93 | `rust_streak` | Rust streak from a fixing | 3.0 m | 309 | 3,000 | Y | 1 | `armco_splice_bolt` |
| 112 | `absorbent_granule_residue` | Absorbent granule residue | 4.0 m | 619 | 80 | Y | 1 | `oil_stain`, `marshal_absorbent_bin` |
| 116 | `crushed_can` | Crushed drink can | 4.0 m | 155 | 80 | Y | 1 | - |
| 117 | `discarded_bottle` | Discarded bottle | 4.0 m | 224 | 60 | Y | 1 | `water_bottle` |
| 119 | `footprint_in_gravel` | Footprint & track in gravel | 4.0 m | 280 | 300 | Y | 1 | `gravel_bed_surface` |
| 120 | `fuel_spill_stain` | Fuel / coolant spill stain | 4.0 m | 467 | 80 | Y | 1 | `oil_stain` |
| 122 | `grass_clipping_drift` | Grass clipping drift | 4.0 m | 280 | 200 | Y | 1 | `grass_runoff_turf` |
| 111 | `litter_paper_scrap` | Paper / wrapper litter | 4.0 m | 112 | 400 | Y | 1 | - |

**`dust_drift`**  
*varies by:* accumulation in the lee of kerbs and posts; swept lines where a car has passed  
1.5 m from the lens at the hairpin. Nothing makes a kerb look bedded-in like the grit that has collected against it.

**`scuff_mark_barrier`**  
*varies by:* paint colour transferred; height above ground matching a real contact; smear direction  
Paint transfer at the right HEIGHT is the tell - it must line up with something that could have hit it.

**`cable_tie_offcut`**  
*varies by:* on fences and barriers; tail cut vs left long; UV yellowing  

**`chalk_mark`**  
*varies by:* survey spot vs pit-box reference; freshness; partial erasure  

**`cigarette_end`**  
*varies by:* burn depth; filter stain; ground into the joint  
User-named. Clusters near doorways, gates and the smoking side of every building - never uniform.

**`gaffer_tape_strip`**  
*varies by:* colour; lifted edge with grit under it; torn end; overlaid layers; ghost of a removed strip  
User-named. The lifted, gritty edge is the object; a flat rectangle is a decal.

**`oil_stain`**  
*varies by:* age (dark fresh to grey ghost); drip pattern under a parked vehicle; absorbent granule residue  
User-named. Concentrated where vehicles stand: garage floors, the transporter park, the compound.

**`puddle`**  
*varies by:* depth; silt ring; oil film iridescence; drying edge  
Sits in the low points the drainage model already defines - swales, gully surrounds, settled paving bays. A puddle placed anywhere else contradicts the ground.

**`rust_streak`**  
*varies by:* length; freshness; running down a vertical vs pooling on a horizontal  

**`absorbent_granule_residue`**  
*varies by:* swept vs raw; darkened where it worked  

**`crushed_can`**  
*varies by:* crush axis; tab state; fade  

**`discarded_bottle`**  
*varies by:* crushed vs whole; cap on/off; label peel; fill; lying vs standing  
The user named it. One discarded bottle, correctly weathered and correctly placed, does more than a thousand instanced clean ones.

**`footprint_in_gravel`**  
*varies by:* boot vs vehicle; freshness; overlapping  

**`fuel_spill_stain`**  
*varies by:* evaporation edge; colour  

**`grass_clipping_drift`**  
*varies by:* freshness; mower discharge direction  

**`litter_paper_scrap`**  
*varies by:* crumple state; drift into corners and against kerbs; wind-pinned against a fence  
Drifts where wind and geometry put it - against the windward face of barriers and in the lee of every post. Scattered uniformly is the placeholder.

---

## 6. Suggested build order

Dispatch in `build_order`. The first thirty rows, which is where the film is won or lost:

| # | id | zone | near | px@4K | why now |
|---:|---|---|---:|---:|---|
| 1 | `showroom_floor_slab` | `showroom_breach` | 0.5 m | 448 | foundation / closest |
| 2 | `glass_shard` | `showroom_breach` | 0.8 m | 1167 | foundation / closest |
| 3 | `kerb_hero_t4` | `kerbs_markings` | 0.8 m | 210 | foundation / closest |
| 4 | `floor_shard_scatter` | `showroom_breach` | 1.0 m | 149 | foundation / closest |
| 5 | `pit_exit_portal_sign` | `transit_corridor` | 1.0 m | 2160+ | foundation / closest |
| 6 | `asphalt_wearing_course` | `track_surface` | 1.1 m | 41 | many dependents |
| 7 | `rubber_line_deposit` | `track_surface` | 1.1 m | 2160+ | foundation / closest |
| 8 | `white_line_edge` | `kerbs_markings` | 1.1 m | 204 | foundation / closest |
| 9 | `asphalt_paver_mat_joint` | `track_surface` | 1.1 m | 61 | foundation / closest |
| 10 | `verge_green_paint` | `kerbs_markings` | 1.1 m | 2036 | foundation / closest |
| 11 | `curtain_wall_sill_extrusion` | `showroom_breach` | 1.3 m | 718 | foundation / closest |
| 12 | `dais_deck` | `showroom_breach` | 1.4 m | 907 | foundation / closest |
| 13 | `dais_delivery_ramp` | `showroom_breach` | 1.4 m | 907 | foundation / closest |
| 14 | `pit_exit_portal_frame` | `transit_corridor` | 1.5 m | 2160+ | foundation / closest |
| 15 | `tyre_marble` | `track_surface` | 1.5 m | 18 | foundation / closest |
| 16 | `asphalt_crack_seal` | `track_surface` | 1.5 m | 60 | foundation / closest |
| 17 | `asphalt_patch_repair` | `track_surface` | 1.5 m | 2160+ | foundation / closest |
| 18 | `asphalt_transverse_joint` | `track_surface` | 1.5 m | 30 | foundation / closest |
| 19 | `dust_drift` | `ephemera` | 1.5 m | 15 | foundation / closest |
| 20 | `mullion_intact` | `showroom_breach` | 1.6 m | 2160+ | many dependents |
| 21 | `glass_panel_prefractured` | `showroom_breach` | 1.6 m | 2160+ | foundation / closest |
| 22 | `glazing_gasket_set` | `showroom_breach` | 1.6 m | 77 | foundation / closest |
| 23 | `access_road_slab` | `transit_corridor` | 1.7 m | 2160+ | foundation / closest |
| 24 | `forecourt_paving_bay` | `showroom_breach` | 1.7 m | 2160+ | foundation / closest |
| 25 | `access_road_saw_joint` | `transit_corridor` | 1.7 m | 73 | foundation / closest |
| 26 | `exterior_ground_apron` | `showroom_breach` | 1.7 m | 2160+ | foundation / closest |
| 27 | `moss_patch` | `vegetation` | 1.7 m | 546 | foundation / closest |
| 28 | `weed_joint_colonist` | `vegetation` | 1.7 m | 546 | foundation / closest |
| 29 | `apron_wall_panel` | `transit_corridor` | 1.8 m | 2160+ | foundation / closest |
| 30 | `pont_soffit_panel` | `bridges` | 1.8 m | 436 | foundation / closest |

The remaining rows follow the same rule and are listed in full in the JSON. Two scheduling
notes:

* **Foundations gate everything above them.** `asphalt_wearing_course`, `kerb_precast_unit`,
  `armco_post`, `armco_w_beam`, `terrain_ground`, `paddock_paving_bay`,
  `catch_fence_post`, `tyre_wall_tyre` and `grass_clump_fescue` each have four or more
  dependents. Nothing that sits on them should be dispatched until they land.
* **The three closest single objects in the film are not on anybody's list today:**
  `pit_exit_portal_frame` (the camera passes through it), `kerb_hero_t4` (the lens sits on
  it), and `pont_soffit_panel` (1.8 m of clearance at 300 km/h). Dispatch those three first.

---

## 7. Known gaps and defects a per-item agent must not re-discover

These are already documented in the module docs and the contract; they are repeated here so
no agent wastes a cycle finding them again.

| # | gap | who must fix it |
|---:|---|---|
| 1 | `world_contract.barrier_offset` has no ownership clamp - the circuit crosses its own corridor at T3/S3. `build_dressing` does not read the clamp and will place marshal posts and ad boards *under* the S4/T5 racing surface for 400 m. | contract author, before any trackside dressing item is built |
| 2 | The ground datum steps 6.75 mm across the start/finish line (undulation noise evaluated on non-cyclic `S`). It hides under 400 mm of paint, but the onboard follow crosses at 323 km/h. | contract author |
| 3 | `C.access_z` disagrees with `C.ground_z` by up to 89.5 mm on the Beat-4 ribbon - 8x the seam tolerance. `build_surface` routes around it. | contract author: retire `access_z` or redefine it as `ground_z` |
| 4 | The grandstand terrace is a declared contract addendum `world_contract` does not carry. Terrain must build no ground inside circuit x -426..+186, y -69.0..-28.5 and must weld to the 1.85 m skirt. | `grandstand_skirt` + terrain |
| 5 | The escarpment beyond T4 does not read from the kerb-height hairpin camera - the treeline sits on the near lip and occludes it. That silhouette is the entire point of the film's best shot. | `escarpment_skyline`: suppress woodland inside the hairpin's outward fan |
| 6 | Every terrain material must be re-checked against the contract's `lambert_radiance`. Terrain was tuned for direct:diffuse 3.00:1; the measured value is 2.072:1, so shadows are 45 % brighter relative to key than the turf albedo assumed. This is the direct cause of the 'pink and green blotches'. | every `vegetation` item |
| 7 | All five shrub species come from ONE generator with different parameters, unlike the ten independent tree structures. `build_terrain`'s own note: rebuild if the lens gets inside ~15 m. It does - planters at 14 m, verge shrubs at ~8 m. | `shrub_*` items |
| 8 | Birch is 20 % of the tree mix plus 7.5 % dead timber, so a quarter of every treeline is a pale stem and it reads as 'a birch wood' everywhere. Drop birch to ~0.13 and weight to oak and hawthorn. | `tree_silver_birch`, `tree_oak`, `tree_hawthorn` |
| 9 | Asphalt displacement is bump-only (1-3 mm of relief). If the hairpin frames show flat aggregate at 1.1 m, promote to true displacement - and then re-check for TEMPORAL flicker in motion, not just in a still. | `asphalt_wearing_course` |
| 10 | Gravel below 11 mm is shader, not geometry. The documented rule is: if a lens gets inside ~0.6 m of a bed, raise the hero tier and re-run. Closest today is 2.8 m at s=252 - check it. | `gravel_stone` |
| 11 | The catch-fence weave is analytic everywhere except the doppler window (s 2495-2615, side -1). `set_fence_fade(scene)` MUST be called by the render orchestrator at any non-4K size or the weave resolves wrong. | render orchestrator |
| 12 | `build_dressing` is the one module whose materials were never re-calibrated against contract section 8 / `lambert_radiance` - its test renders used a stand-in sun. | every `trackside` item |
| 13 | Five of the six modules ship a test SUN lamp. `build_sky` warns on a second SUN - two suns break the one-light law. All `*_TEST*`, `*_PROXY*` and `TEST_*` scaffolding must be purged before assembly. | assembly owner |
| 14 | Start lights, timing stands, garage interiors, distance-marker boards as objects, marshal-post detail and grandstand structure are dimensioned nowhere in `circuit_spec`. They are in this manifest because the camera sees them, not because the spec asked for them. | the relevant per-item agents |

---

## 8. Contract compliance every item inherits

Any agent building any row must:

* Everything is BUILT BY HAND, procedurally, in Blender. No downloaded models, no photo textures, no HDRIs, no AI-generated anything. The project is currently clean - verified zero image-texture nodes. Keep it that way.
* No real sponsor names, no real team liveries. 31 invented brands already exist in build_dressing's brand book and 12 are shared with build_architecture - reuse them.
* Scale against the measured car: 5.698 m long, 2.005 m wide, 0.340 m ride height.
* z = 0.000 is simultaneously the showroom floor, the paddock apron, the access road and the pit-straight racing surface. One plane, no lip, no step.
* Everything standing on ground embeds >= 0.020 m (BASE_EMBED_M) and is placed with world_contract.world_ground_z, never on an assumed z.
* Every object is recentred on emit and every material reads TexCoord->Object, never Geometry->Position: at |P| ~ 1000 m a position-driven procedural loses all precision.
* Chunk along s so no object spans more than ~80-260 m of circuit.
* Place with `world_contract.world_ground_z(x, y)` and honour `platform_owner` - never
  assume a ground height.
* Prefix and collect per the existing registry: `ARCH_`/`A_` in `ARCH`, `BR_` in
  `R2_Barriers`, `DR_`/`DR_mat_` in `R2_Dressing`, `SURF_`/`M_Surf_` in `W_Surface`,
  `TER_`/`VEG_` in `WORLD_TERRAIN`, `SKY_` in `WORLD_SKY`. Purge by prefix so the build
  stays idempotent.
* Carry the per-vertex attribute set the modules already emit (UV, W wear, P, U, M, S) and
  a `Col` per-instance variation channel.
* Stamp `world_contract.summary()` / `stamp()` onto its collection so the .blend records
  which contract version it was built against.

---

*Generated 2026-07-28 from `docs/beat_sheet.json`, `docs/circuit_spec.json`, `docs/circuit_spec.md`, `world/WORLD_CONTRACT.md` and the six `world/build_*.md` module docs. The corridor derivation is reproducible from those five sources alone. `docs/item_manifest.json` is the authoritative copy - the campaign reads it, not this document.*
