# Staged for the defect log's owner — R2-187 to R2-194

Kept out of `docs/DEFECT-LOG-R2.md` deliberately: that file has one owner. My
block is R2-187 to R2-194 and I have used eight of it. Paste or renumber as you
see fit.

All of it is one job: **landing the completed breach bake on `film14`**, the
assembly9 ship. This was an APPLY, not a bake. The 1,657-frame bake at
bond 100 / mullion 40/120 was not re-run and `sim/out/breach_film.npz` is
byte-identical to the one film13_breach was built from.

Artefact: `render/film14_breach.blend`, 4,992,299,735 bytes.
Working files: `work/r2187/`.

---

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

Crops confirm it by eye: a lit strip of apron at ground level, seen through the
gap in the barrier wall, that is brighter and longer in the defective world.

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

---

## R2-193 — cluster B is not in the motion that renders: exactly ONE shard exceeds 60 m/s on the film-frame table

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

**This does not diagnose cluster B and does not contradict R2-096.** A chord
between film frames is a lower bound on instantaneous speed, and a body that
accelerates and reverses inside 1/24 s has most of its speed averaged away. What
it does is **bound the visible consequence**: whatever cluster B is, it lives at
sub-film-frame timescales and the delivered animation samples over it. Nothing
on screen is travelling at 106 m/s.

The overlap with the sink was tested at the same time, with a random-subset
control at each threshold. The 70 sunk shards **are** the fast tail —
median max speed **38.9 m/s against 11.4** for the rest, above the 99th
percentile of everything else — but they are not the 106 m/s population, because
on this table that population is one body. So the two open items are related in
direction and are not the same set. `work/r2187/clusterb.py`.

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

---

## The gates, each with the control that discriminates

| gate | film14_breach | control |
|---|---|---|
| `socket_index_audit --blend` | **PASS** — no relief chain reaches a shading node on anything but a normal | `film10`, the assembly6 control, **FAIL, 27 findings**, in the same run |
| `verify_breach --swap-scene` | **PASS, 0 problems.** Bays 2,3,4,5,6,7 each hide their pane at **860** and show every shard at **860**; `shards_not_on_the_pane_frame = 0` in all six; bays 0,1,8,9 intact, pane never hides | the same script's `--swap` arm on the TABLE: **FAIL, worst gap 2,118 frames, 301 shards uncovered.** Table fails, scene passes — that pairing is what shows the applier is the fix |
| `apply_breach --selftest` | **PASS, 0 failed of 11 arms** | six of the eleven are must-fail arms, including "no east glazing at all", "a hidden pane", "a surviving round-1 plane" and "a solid box through the pocket with ZERO vertices inside it" |
| curve proof (in-applier) | LINEAR 6,783 / CONSTANT 240 / **other 0**, max linear eval err 4.768e−07, `control_fires: true` | the Bezier control arm, which must and does register 4.797e−04 |
| east wall | **1,255 of 4,096 rays meet `GP_b*`** | `film14` unapplied: **0 of 4,096** (R2-190) |
| f0866 / f0890 A/B | signal 0.0037 % / 0.0048 % over 8/255 | live repeat-render floor **0.0000 %**, max 1/255 (R2-191) |
