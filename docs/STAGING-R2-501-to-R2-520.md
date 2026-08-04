# STAGING — R2-501 to R2-520

Block: THE BATCHED REBUILD. `assembly10` + `film16`, carrying the beat-1 camera
promotion and the six queued source fixes. Owner of R2-501..R2-520.
Nothing here is written into `docs/DEFECT-LOG-R2.md`; that file has one owner.

---

## R2-501 — every number in the establishing station's own comment block was from a superseded solve, and the constant beside it was right

The beat-1 promotion turns on three claims: **18 mm, 9.0 m standoff, depression
exactly 10.00 deg**. Verifying them against the source rather than against the
prose is what found this.

`tools/build_beatsheet.py` states the station twice — once as a constant and once
as the paragraph immediately above `_establish_on()` that explains it. They did
not agree, on any field:

| | the paragraph said | `BEAT1_ESTABLISH` said | measured from the constant |
|---|---|---|---|
| lens | 24 mm | 18 mm | **18 mm** |
| standoff | d = 8.70 m | `focus_distance_m` 9.0 | **8.999989 m** |
| depression | 12 deg | — | **9.998502 deg** |
| lens z | 4.00 | `world[2]` 3.7566 | **3.7566** |
| station y | -8.51 | `world[1]` -8.8633 | **-8.8633** |
| radius | — | — | **8.903 m** (rope ring 6.96) |

**The constant is the one that shipped and the constant is correct.** The
paragraph describes an earlier solve that was superseded and never re-read. The
promoted numbers reproduce R2-466's table exactly, so the *work* was right; only
the explanation of it was wrong.

> This is the project's own recurring failure in its cheapest form: **a second
> copy of a fact.** `tools/shipping_world.py` exists because a consumer kept its
> own copy of the shipping world's name (R2-071, R2-100). A comment is a
> consumer too. Nothing executes it, so nothing catches it, and every summary
> written about this station quoted it.

**Fixed both ways.** The paragraph is corrected, and
`establish_station_geometry()` now *computes* standoff, depression, lens z and
radius from `BEAT1_ESTABLISH` itself, with module-level assertions that
`build_beatsheet.py` refuses to import if any of them drift:

```
assert abs(_ES_D   - 9.0)  < 5e-4        # standoff
assert abs(_ES_DEP - 10.0) < 5e-3        # 9.99850, "exactly 10.00"
assert abs(BEAT1_ESTABLISH["lens_mm"] - 18.0) < 1e-9
assert abs(BEAT1_ESTABLISH["focus_distance_m"] - _ES_D) < 5e-4
assert _ES_Z <= 5.29 and _ES_Z >= 1.20   # R2-454's two measured bounds
assert _ES_R > 6.96                      # outside the rope ring
```

A comment cannot be wrong if the number is computed. The R2-454 bounds are
asserted in the same block because they were also only ever prose.

**Caveat on "exactly 10.00 deg" (R2-466).** It is **9.998502**, not 10.000000.
The difference is 0.0015 deg and is of no consequence to any frame, but the word
"exactly" is not earned and the tolerance above is written at 5e-3 to say so
rather than at 1e-9 to hide it.

---

## R2-502 — `build_film_scene.py` had a path that saves NOTHING, and printed `FILM_SCENE_BUILT` on it anyway

`refuse_unless_levelled`'s docstring makes a specific, checkable claim:

> *"There are three `save_as_mainfile` calls in this file and this must precede
> every one of them, so the only way to ship an un-levelled film scene is to
> delete this function."*

**The claim about the guard is TRUE — I checked it and it holds.** All three
saves are immediately preceded by `refuse_unless_levelled`. The guard has not
regressed into `if not a.no_rig:` the way it did for `film9`.

**What is not true is the sentence's premise.** The saves are distributed like
this:

```
if not a.no_rig:
    ...build the camera rig...
    if world_before is None:                 -> guard, save        (branch 1)
    elif world_after != world_before:        -> guard, save        (branch 2)
    # <-- no else.  NO SAVE ON THIS PATH.
else:                                        -> guard, save        (branch 3)
```

The uncovered path is: the rig was built, the incoming scene **had** a world, and
the rig **left it alone**. On that path nothing is written — and control falls
straight through to

```
print(">> STAGE RESULT: FILM_SCENE_BUILT")
```

**The project's own working rule is that `$?` is worthless and a stage is judged
ONLY on its `STAGE RESULT` line.** That rule turns an unconditional success token
sitting over a conditional save into a live trap: a run that produced no file is
byte-for-byte indistinguishable, to every downstream reader, from one that did.
The comment `# never inside a branch -- see the docstring` appears on the guard
at each site, which is exactly where the eye stops.

**Why nobody found it.** Every `assembly*.blend` carries no sky — the file says
so itself at the branch: *"assembly*.blend carry no sky"* — so `world_before` is
always `None` and branch 1 has always fired. The path has never been taken. It
would be taken the first time a film is built from any scene that already has a
world, which is a thing this project does routinely for A/B arms
(`render/r2451_b1ab.blend` and friends all carry `R2_ProceduralSky`).

**Two fixes, because they are two defects.**

1. The missing `else` now guards and saves like the other three.
2. `FILM_SCENE_BUILT` is no longer printed on the strength of reaching the end
   of the function. It is printed on the strength of a blend existing on disk
   whose mtime is later than `t_start`, taken at the top of `main()`. A leftover
   file from a previous build satisfies existence but not freshness, so the
   two failure tokens are distinct:

```
>> STAGE RESULT: FILM_SCENE_NOT_SAVED   -- no file at all
>> STAGE RESULT: FILM_SCENE_STALE       -- a previous build's output
```

---

## R2-503 — `assemble.py` swallowed every module exception and then printed no verdict at all

`render/world/assembly/r2/assemble.py` wraps each module's `build()` in

```
except Exception as e:
    traceback.print_exc()
    s, ok, err = {}, False, repr(e)
```

and carries on. That is the right behaviour and should stay: one broken module
should still leave a probeable blend rather than nothing.

**But it was the only signal.** Blender 5.2 exits 0 on an uncaught script
exception, so `$?` was never evidence; and because the exception was *caught*,
even that was not available. A build in which `items` raised and placed nothing
produced a saved blend, a written `_build.json`, and an exit status of 0 —
identical in every respect a caller checks to a build in which it worked.
Finding out required reading ~4,000 lines of log for a traceback.

This matters most for exactly the module this rebuild is about: `items` is the
sixth and last module, task #121 is *"nothing built in `world/items/` has ever
reached a frame"*, and a silent failure there would have reproduced task #121
while looking like the fix for it.

`assemble.py` now ends with a verdict line, and flags the quieter failure too —
a module that returned `ok=True` and an empty summary:

```
>> ASM MODULES FAILED: items
>>   items: RuntimeError(...)
>> STAGE RESULT: ASSEMBLE_FAIL        # or ASSEMBLE_OK
```

`v125/build_assembly10.sh` greps that token and nothing else.

---

## R2-504 — the showroom roof is NOT a source fix, and no world rebuild can deliver it

The batched rebuild was briefed as *"six queued source fixes — each a landed
source change waiting for a rebuild to reach a frame."* For five of the six that
is true. **For the roof it is false, and it is false for a structural reason
that no amount of rebuilding changes.**

`tools/r2366_roof_build.py` says so itself, in its own header:

> *"The roof is NOT round-2 geometry. `Ceiling` is a literal cuboid emitted by
> `/home/zany/opus5-car-render/build/s02_showroom.py:490` `build_shell()` — 8
> vertices, 6 quads, top face ONE QUAD OF 686 m². It reaches the film through
> `tools/build_film_scene.py`'s append of `world/car_anim.blend`'s SHOWROOM
> collection, at identity. `/home/zany/opus5-car-render` IS READ-ONLY (project
> law 1), so the source cannot be corrected."*

So the showroom shell enters the film **downstream of the assembly**, from the
shipped part-1 tree, and `assembly10` cannot contain it — `assembly*.blend` has
no showroom in it at all. The roof is a **post-append operation on a film
blend**, in the shape `tools/add_dais_ramp.py` established: open the film that
already exists, assert the datum it lands against, build into it, save elsewhere.

Three consequences worth stating plainly:

* **`assembly10` carries five of the six fixes, not six.** Any claim that "the
  rebuild landed all of them" is wrong at the world level by construction.
* **`tools/r2366_roof_build.py` is untracked** (`?? tools/r2366_roof_build.py`).
  It is not a *landed* change in any sense — it has never been committed.
* Its own visibility measurement says the roof top is visible on **151 frames,
  all in beat 6, all at 594–610 m**, never near-field. So it is real work with a
  real justification, but it is the last thing in the chain and not the first.

---

## R2-505 — the deck-slab normal fix reaches a frame only through `timing_stand`; the two modules it was actually written for are both `HOLD`

"Deck slabs — were upside down" is two commits:

```
d08eaa3  R2-182  slab_grid's walking surface faced down       world/items/marshal_post_deck.py
93921d8  R2-179  both end caps of every extrusion faced INWARD world/items/marshal_post_deck.py
                                                              world/items/timing_stand.py
```

`world/items/PLACEMENT.json` has **4 rows in state `PLACE` out of 42**:
`catch_fence_post`, `crew_figure`, `timing_stand`, `spectator_crowd_world`.

**`marshal_post_deck` is `HOLD`** (`GATE_NOT_ACCEPTED`, `SUPERSEDE_WELDED`), and
so is `pont_deck_slab` (`GATE_NOT_ACCEPTED`, `LOCAL_FRAME`, `SUPERSEDE_WELDED`).
Neither is placed, so **neither R2-182 nor R2-179's `marshal_post_deck` half
reaches a frame in `film16`.** What does reach a frame is R2-179's *other* half,
the inward-facing end caps in `timing_stand.py`, because `timing_stand` is one of
the four `PLACE` rows.

This is not a regression and nothing was done wrong — it is the sequencing rule
again, one level down. A fix to an item module reaches a frame only when that
item's row is `PLACE` **and** its built blend is newer than the module. Both
gates have to be checked, and only the second one is checked automatically.

**The blend-vs-module check, run over all four `PLACE` rows:**

```
world/items/catch_fence_post.py        2026-08-02_16:51   blend 2026-08-02_19:25   OK
world/items/crew_figure.py             2026-08-03_06:40   blend 2026-08-03_20:51   OK
world/items/timing_stand.py            2026-08-04_00:24   blend 2026-08-04_00:27   OK
world/items/spectator_crowd_world.py   2026-08-04_04:50   blend 2026-08-04_04:33   STALE by 17 min
```

**`spectator_crowd_world.blend` predates its own generator by 17 minutes.** The
crowd that goes into `assembly10` is the artefact built at 04:33 from a source
that was still being edited at 04:50. Whatever the 04:50 edit did, it is not in
this film. Flagged, not fixed: rebuilding a 2.0 GB crowd blend is its own pass
and the module's own note already says the next crowd pass costs a 451 s
rebuild.

---

## R2-506 — "70.5 % occupancy" is an average of six ratios, not a ratio; the crowd is 60.65 % of seats

The crowd was handed to this rebuild as **"70.5 % occupancy, 1.86× clustered."**
Neither number survives being looked up in the module that produces the crowd.

`world/items/spectator_crowd_world.py` states its own realised build:

```
TRIBUNE OUEST       1,843 / 3,071   60.0 % physical   76.7 % of open
TRIBUNE T15         2,510 / 4,077   61.6 %            78.2 %
VIRAGE OUEST        1,414 / 2,143   66.0 %            66.0 %
TRIBUNE PRINCIPALE  3,345 / 5,542   60.4 %            77.6 %
TRIBUNE EST         1,559 / 2,522   61.8 %            78.8 %
TRIBUNE TEMPORAIRE    458 /   995   46.0 %            46.0 %
-----------------------------------------------------------------
11,129 people over 18,350 chairs, 3,311 of them folded up
```

Three different numbers can be called "the occupancy" and they are far apart:

```
11,129 / 18,350                      = 60.65 %   of physical seats
11,129 / (18,350 - 3,311)            = 74.00 %   of seats that open
mean(76.7, 78.2, 66.0, 77.6, 78.8, 46.0) = 70.55 %   <-- THIS IS THE 70.5 %
```

**70.5 % is the unweighted mean of six per-block ratios.** It weights TRIBUNE
TEMPORAIRE's 995 chairs exactly as heavily as TRIBUNE PRINCIPALE's 5,542, so it
is not an occupancy of anything — it is an average of averages. The ratio of
totals over the same seats is **74.00 %**, and the number a viewer's eye actually
integrates, folded seats included because a folded seat is visibly empty, is
**60.65 %**.

> *A mean of ratios is not the ratio of the means, and this is the second
> "settled" figure in this rebuild that turned out to be a property of how it
> was reduced rather than of the film.* (The first is R2-501.)

**"1.86× clustered" has no source at all.** There is no clustering metric in
`spectator_crowd_world.py`, `spectator_seated.py` or `grandstand_seats.py` —
grep for `clust`, `clump`, `gregari` returns one prose line and no number. The
only `1.86` anywhere near the crowd is

```
world/items/spectator_seated.py:728
    stature = min(1.86, max(1.49, rng.gauss(1.633, 0.062)))
```

which is the **upper clamp on a seated adult's height in metres**, in the first
of two overlapping stature normals. It is not a multiplier and it is not about
clustering.

And the one place the word "clustering" does appear is a comment over code that
does not do it:

```
# occupancy, with real clustering: people arrive in twos and threes and
# leave gaps, they do not fill a stand like a checkerboard.
for (sx, sy, sz, r, c) in seats:
    f = occupancy
    if r < 2:
        f *= 0.88
    if rng.random() < f:            # <-- independent Bernoulli per seat
        taken.append(...)
```

That is an i.i.d. coin flip per seat, which is precisely the checkerboard the
comment says it is not. It is in `_test_rig`'s composer, not the world composer,
so it does not describe the shipped crowd — but it is where a reader looking for
"real clustering" lands, and it is another comment that is not performed.

---

## R2-507 — the `ranked` safeguard DOES exist now; the briefing on it is out of date, with one word still true

I was told: *"The documented safeguard ('walks down the ranking until a station
fits inside the room') was never implemented — nothing has ever read `ranked`.
If you touch that function, implement it or delete the comment."*

**That was true of the shipped code and is no longer true of the working tree.**
R2-451 implemented it, and moved it to where it belongs — into
`tools/presentation_normals.py`, where the ranking and the score live, rather
than in `build_beatsheet.camera_station()`, which had the comment but not the
data. It now walks three measured conditions:

```
the lens is under the light rig      cam_z <= spot_rig_z - clearance
the lens clears the rope barrier     cam_z >= min_cam_z
it is a photograph, not a plan       elev <= max_depression_deg
```

then takes the shallowest survivor within `--score-tol` of the best, and NAMES
the relaxation if no direction satisfies both envelope conditions rather than
silently widening. So `camera_station()` was correctly left alone: the fix
belonged upstream of it.

**The one word still literally true**: the `ranked` *field* is still never read.
`presentation_normals.py` performs the walk against its in-memory `scored` list
and then *writes* `ranked` as output. Nothing consumes it. It is a write-only
diagnostic — harmless, but if anyone documents it as the mechanism again, it
still is not.

---

## R2-508 — the beat-1 promotion put the showroom ceiling in the film's FIRST FRAME, and part-1's standing assumption that it is never in shot is now false

This is a defect the camera fix **created**, and it is worth more than the fix
was, because nothing would have looked for it.

`/home/zany/opus5-car-render/build/s05_lighting_v2.py` states an assumption twice
and builds on it:

```
line  17:  * The frame map also shows the ceiling is never in shot from any hero camera.
line 300:    light - the ceiling rig never appears in any hero frame.
```

**That was TRUE, and it is measurable why.** The shipped opening is a 35 mm lens
at 84.15 deg of depression. On a 36 x 20.25 mm frame a 35 mm lens has a 16.13 deg
vertical half-angle, so the top edge of the shipped first frame sits at

```
-84.15 + 16.13  =  -68.02 deg elevation
```

— 68 degrees below the horizon. The ceiling was not merely out of shot, it was
nowhere near it, and part 1 was entitled to build on that.

**The promotion makes it false.** The establishing station is 18 mm at 10.00 deg
of depression, and 18 mm has a **29.36 deg** vertical half-angle:

```
frame spans   -39.36 deg  ..  +19.36 deg elevation
camera z 3.7566, CEIL_Z 6.20
ceiling enters the frame at (6.20 - 3.7566) / tan(19.36 deg) = 6.95 m horizontal
the room is ROOM_Y 11.0 + WALL_T 0.25 = 11.25 m half-depth
```

**6.95 m is inside 11.25 m, so the ceiling is in frame 1 of the film.** It is in
frame 1 because of the fix landed in this same block, and the fix is still right:
an opening that shows the room is the whole point of R2-461, and a room has a
ceiling in it.

### what is up there

```
Ceiling            one cuboid, 8 vertices, 6 quads
                   top face: ONE QUAD of 686 m^2
                   CeilingMat: a two-node flat Principled
                   emitted by build/s02_showroom.py:490 build_shell()
23 interior practicals, 46,203.313 W, hanging in that volume
```

The beat runs 33 seconds — **a quarter of the film's runtime** — inside it. Its
lamps hang from nothing.

> **This is the R2-504 structure again and it is worth naming as a pattern.**
> Both the roof and the ceiling are part-1 geometry entering the film
> *downstream* of the assembly, through `build_film_scene.py`'s append of
> `world/car_anim.blend`'s SHOWROOM collection. `assembly10` has no showroom in
> it at all, so **no world rebuild can ever touch either of them.** Anything
> that fixes them is a post-append operation on a film blend, in the shape
> `tools/add_dais_ramp.py` established.

### the constraint any ceiling work has to respect

`Ceiling`'s **underside at z 6.200 is the showroom's interior ceiling and is
visible in beat 5**, and `CeilingMat` is shared with `Cove_Coffer_0/1` and
`WallLine_*Fin_0/1`. `tools/r2366_roof_build.py` already worked this out for the
roof and its answer is the right one for the ceiling too: build **above** the
existing surface, in a new collection, with new materials, touching no round-1
datablock. And the lighting invariant is not negotiable —

```
interior lamp load   46,203.313 W   from showroom_lighting.measure()
_sl_base stamps      23
scene_mark           3.628          scene key `showroom_lighting_stops`
assert_levelled      PASS
```

— read with the module's own `measure()`, never a hand-rolled probe: a
hand-rolled one already returned 46,319 W once by counting a lamp that is not
interior.

**HANDED BACK, EXPLICITLY.** See the final report. The measurement above raises
the priority of this work (it is first-frame geometry now, not a beat-6 detail at
594 m) and that is exactly why it should not be rushed onto an 11 GB box while a
7.1 GB film blend is landing on it.

---

## R2-509 — the doubled text is a SCREEN-space collision, not a writer collision. Nothing writes those panels twice, and the gate built for this defect class cannot see it

I was told the doubling came from *"two modules writing the same panel 45 mm
apart"*, first on the gantry and then, corrected, on the **MERIDIAN facade sign**
and the **"24 P1" pit board**. I went looking for the second writer.

**There is no second writer. On any of them.** Four independent measurements:

```
1  duplicate objects       strings over world/car_anim_driver.blend,
                           render/film14.blend, render/film14_breach_r6.blend
                           -> WallSign_Word x1, WallSign_Strap x1, PitBoard_Num x1,
                              PitBoard_Pos x1, PitBoard_Gap x1, PitBoard_Lap x1
                           exactly one of each, in every blend.  No `.001`.

2  world-space overlap     every pair of text runs on both panels, world AABBs
                           -> STAGE RESULT: SIGN_TEXT_CLEAR
                              Word/Strap are 46.3 mm APART in z, cleanly.

3  neighbour sweep         every mesh object in world/beat1_anim.blend (919 of
                           them) within 0.35 m -- the gate's own SEP_M -- of any
                           sign text run
                           -> 22 hits, and every one is the sign's OWN hardware
                              (PitBoard_Face/Edge/Pole, WallSign_Rule) or the wall
                              it is mounted on (Wall_BackX, WallLine_Back,
                              WallLine_BackFin_0/1).  No second legend. None.

4  provenance              both panels are emitted ONCE each by part-1's
                           build/s07_props.py -- build_wall_wordmark() at :347 and
                           build_pit_board() at :951, each called once from :1458
                           and :1464.
```

### what it actually is

The doubling is **projective**. Measured through the film's own ONER camera at
4K, beat 1, with real glyph vertices rather than bounding boxes:

```
largest on-screen size, beat 1                 overlap at f1
  WallSign_Word    394.1 x 72.4 px @f9    WallSign_Strap x WallSign_Word
  WallSign_Strap   334.7 x 38.5 px @f9      305.9 x 16.8 px = 45.7% of the strapline
                                            (strapline is 306 x 37 px -- the overlap
                                             is its FULL WIDTH and 45% of its area)
  PitBoard_Num     119.6 x 77.9 px @f151  PitBoard_Gap x PitBoard_Pos
  PitBoard_Pos      97.1 x 71.8 px @f151    46.1 x 2.8 px = 7.2% of the smaller
```

These are legible-scale objects — 360 x 68 px at 4K — so the reading is not an
artefact of measuring specks.

### the root cause, and it is one number

```
WallSign_Word extrusion depth  = 2*extrude(0.022) + 2*bevel(0.004) = 52.0 mm
Word-to-Strap vertical gap     =                                     46.3 mm
                                                        DEPTH EXCEEDS GAP BY 5.7 mm
```

**A 52 mm-deep letterform stacked 46.3 mm above its neighbour will collide on
screen at any grazing view angle, and the wall is seen at a grazing angle.** The
runs are correctly separated in the plane of the wall; they are not separated in
the direction the camera actually integrates. The extruded body of MERIDIAN
sweeps down across the strapline.

> **And the "45 mm" I was handed is real but belongs to something else.** It is
> R2-256's La Passerelle figure — a genuine, already-fixed two-writer collision.
> Near this sign there are three unrelated 45-46 mm quantities: the 52 mm glyph
> depth, the 46 mm the wordmark stands proud of the fluting, and the 46.3 mm
> line gap. A number that appears everywhere is not a diagnosis.

### why the gate that exists for this passed it

`tools/text_overlap_gate.py` was written for exactly this defect class and is
correct about its own domain. It fails two panels together only when *"their
in-plane rectangles overlap by >= 15% of the smaller one"* — **in-plane**, in
world space. Word and Strap are *stacked*, not overlapping, in that plane, so
rule 3 never fires and the gate passes them honestly.

It also cannot reach them at all: it works by monkey-patching
`build_architecture.MB.text` and `build_dressing.emit_art` and re-running the
round-2 modules. **The showroom props are part-1 geometry from
`build/s07_props.py`** and are never in its universe. So the panels the defect
is actually on are outside both its test and its reach.

**The gate is not wrong. It is measuring world-space coplanarity, and this is
screen-space occlusion.** Those are different defects that produce the same
complaint, and only one of them has an instrument.

### the gantry: UNMEASURED, not clean

The track gantry's lettering is round-2 (`build_architecture.build_gantry`, and
`build_architecture.py:5703` concedes this module owns "the S/F gantry and its
lettering"). It appears in one delivered frame and carries no legible text there,
and at 720p a 45 mm offset is ~2 px and indistinguishable from an extruded
letterform's bevel. **I did not measure it and I am not calling it clean.** The
test that would settle it is now cheap and specific, and it is not "look for two
writers" — it is:

```
for every pair of stacked legend runs on one panel:
    does  glyph extrusion depth  exceed  the gap to the neighbouring run?
```

That is a one-number check, it is what actually failed here, and no existing
gate performs it.

### R2-509b — the gantry does NOT share the root cause, and here is the source that settles it

`build_architecture.build_gantry` writes exactly **two** legends, and they are on
opposite faces of the beam:

```
mb.text("CIRCUIT VITRINE", T(-1.20, 0.6, soffit+1.05) @ Rz(-90) @ Rx(90), 0.80, extrude=0.02)
mb.text("START / FINISH",  T( 1.20, 0.0, soffit+1.05) @ Rz( 90) @ Rx(90), 0.80, extrude=0.02)
```

* **one run per face** — so there is no stacked neighbour to collide with;
* the two runs are **2.40 m apart in x** and face opposite directions;
* extrusion is 0.02 -> **40 mm of depth against 2,400 mm of separation**, a
  ratio of 1:60 where the wall sign's is 52:46.3, i.e. worse than 1:1.

So the `depth > gap` failure that produces the MERIDIAN and pit-board doubling
**cannot occur on the gantry**. One fix does not buy three panels; it buys two,
and the gantry was never in the same family.

**The gantry is still UNMEASURED in pixels and is not being called clean.** This
is a statement about its construction, derived from source, not about its
appearance. At the 720p of the delivered ladder frames a 40 mm extrusion is ~2 px
and an extruded letterform's bevel is indistinguishable from a doubled glyph, so
only a frame at delivery resolution can retire the question.

---

## R2-510 — what the batch verified, and what was still running when it was handed over

### assembly10 — BUILT, `>> STAGE RESULT: ASSEMBLE_OK`, 1,372 s

```
                       assembly9   assembly10
objects                   28,781      30,488   (+1,707)
meshes                     1,493       3,200   (+1,707 -- one DISTINCT mesh per
                                                item object; nothing repeated)
materials                    137         180
barriers.fence_posts         676           0   superseded by catch_fence_post
architecture.pit_wall_stands   5           1   + 4 superseded by timing_stand
```

`>> STAGE RESULT: ITEMS_PLACED_OK` — 4 items, 1,706 objects, 1,706 distinct
meshes, 42,467,316 tris, 0 refused. **Task #121's stage ran and placed for the
first time.** The per-site supersede behaves exactly as R2-334 specified: four
pit-wall stands removed, the fifth KEPT because no item comes within 31 m of it.

### film16 — BUILT, `>> STAGE RESULT: FILM_SCENE_BUILT`, 7,159.4 MB

Built on assembly10 with `--car world/car_anim_driver.blend`, so the cockpit is
occupied. `>> WORLD STALENESS: none — assembly10.blend is newer than every
world/build_*.py`.

### THE BAR, read back from the saved blend with the module's own `measure()`

`work/lighting/measure_film_scene.py` calls `SL.measure(scene)` at line 36 and
`SL.assert_levelled(scene)` at line 122 — the module's own instruments, not a
hand-rolled probe.

```
                                    bar (film14)    film16       verdict
interior_lamp_watts                 46,203.313      46,203.313   MET
n_lamp_stamps__sl_base                      23              23   MET
scene_mark_showroom_lighting_stops       3.628           3.628   MET
assert_levelled                           PASS            PASS   MET
view_transform / look / exposure   AgX/None/-3.628  AgX/None/-3.628  MET
fps / frame_start / frame_end          24/1/2978       24/1/2978  MET
scene_camera                                ONER            ONER  MET
```

**And the same JSON reproduces the trap the bar was defined against.** Beside
`interior_lamp_watts = 46203.313` sits `lamp_watts_all_objects = 46319.067`,
with `n_interior_lamps = 23` and `n_lamps_all = 24`. The 116 W difference is the
one non-interior lamp, exactly as recorded. The two numbers being in one file,
labelled, is what stops the wrong one being quoted again.

### the camera, verified against the BUILT PATH rather than the sheet

Both instruments carry their own controls in the same run — `beat1_elevation`'s
self-null is 0 while it reports 2,546 genuinely moved frames, and `campath_diff`
prints the R2-103 raw-quaternion trap (0.203 deg of nothing) beside the
re-normalised 0.000003.

```
                         claimed          measured        verdict
frames >70 down          187 -> 0         187 -> 0        REPRODUCES
frames >80 down          120 -> 0         120 -> 0        REPRODUCES
beat 1 first frame       -84.15 -> -10.00 -84.15 -> -10.00 REPRODUCES
worst rotation %w/fr     16.41 -> 8.73    16.41 @f487 ->
                                          8.73 @f489      REPRODUCES
PROTECTED f648-792       0.0099 m @f648   0.0099 m @f648  REPRODUCES
beats 2-6                0.0000 m         0.0000 m        REPRODUCES
continuity_gate          PASS 0 FAIL      PASS 0 FAIL,
                         5 -> 6 advisory  6 advisory      REPRODUCES
```

The f478-495 rotation WARN present in the shipped path is **gone**, and beat 1's
lens range moves 35.0-58.0 mm -> **18.0**-58.0 mm, the establishing lens.

Promotion reproduces `docs/R2464_beat_sheet_CANDIDATE.json` **byte-identically**
(sha256 `7074ab3c466be818...`), and `tools/author_beats2_5.py` is an exact no-op
on the promoted sheet, so beats 2-5 provably did not move.

### STILL RUNNING at handover — NOT verified

The box is shared and was carrying three other agents' Blender jobs at the time
(peaks of 6.7 GB, 3.7 GB and 3.0 GB against 11.9 GB of RAM, 19 GB of swap in
use). A single 7.5 GB blend load was taking 10-25 minutes. These are launched
and will land on disk; **none of them had returned a verdict when this was
written and none should be quoted as passing:**

* `work/r2500/extra_film16.json` — the levelling identity recomputed from
  film16's own `_sl_base` stamps (the base x lift residual)
* the film14 arm of the readback diff, field by field
* the ONER check — camera count 1, clip 0.05/200000, 3840x2160, 24 fps, 2,978
* the in-blend presence check for `DRV_`, `CFP_`, `CRF_`, `TS_`, `SPECX_`
* `socket_index_audit --blend` on film16, with film10's standing 27-finding FAIL
  as the positive control
* `v125/prove_items_in_frame.py` — **the one that matters for task #121.** It
  renders frames 2000 / 2635 / 2900 through the ONER camera with an IndexOB
  pass and counts pixels per item family, with a nonexistent family as an
  in-run negative control that must score 0. Until it returns,
  **"the items are in the scene" is established and "the items reach a frame"
  is NOT.** Those are the two claims task #121 is about and only the second one
  is the task.

---

## R2-511 — **R2-509's HEADLINE IS REFUTED, BY MY OWN INSTRUMENT.** The wordmark eats 0.00 % of the strapline. The AABB artefact I named for the pit board was in my own finding

R2-509 claimed the doubled text was MERIDIAN's 52 mm extruded body occluding the
strapline, on the strength of a screen-space **axis-aligned bounding box**
overlap of 305.9 x 16.8 px, "45.7 % of the strapline". In the very same entry I
wrote that an AABB overlap is not glyph overlap, and used that to dismiss the pit
board's 7.2 %. **I did not apply it to my own headline.**

Measured properly — per pixel, with a holdout, through the film's own camera:

```
>> WallSign_Word depth 0.0520 m (52.0 mm), gap to strapline 0.0463 m (46.3 mm)
   f1     strapline    273 px alone ->    273 px seen   EATEN   0.00 %
   f9     strapline     84 px alone ->     84 px seen   EATEN   0.00 %
   f25    NO_SUBJECT -- the strapline renders 0 px; this frame says nothing
>> STAGE RESULT: SIGN_OCCL_ABSENT
```

**And the refutation carries the positive control the first measurement lacked**,
because "0 % eaten" and "the instrument does nothing" look identical:

```
POSITIVE CONTROL   WallSign_Word alone renders          1316 px   -> ON SCREEN
HOLDOUT CHECK      strap + word, word IS holdout         273 px
                   strap + word, word NOT holdout       1589 px
                   delta                                1316 px = exactly the word
```

1589 = 273 + 1316 exactly, so the holdout is functioning and the wordmark is on
screen. **Zero strapline pixels are occluded.** The two runs are 46.3 mm apart in
world z and they do not touch on screen either. The `depth > gap` mechanism is
wrong: 52 mm of depth does not reach across a 46.3 mm gap, because the depth is
projected along the VIEW direction and the gap is measured along the WALL, and
those are not the same axis. My arithmetic compared two lengths that never meet.

> **Two "settled" numbers in this block have now turned out to be artefacts of
> how they were reduced** — the crowd's 70.5 % (a mean of ratios, R2-506) and
> this one (a box overlap read as a glyph overlap). Both were mine to catch and
> I caught one of them late. The rule that keeps failing is not "measure" — both
> were measured. It is *name the quantity you compared*.

### what IS real, measured, and unexplained

The 52 mm depth produces a genuine artefact, but a different one: the wordmark
**doubles ITSELF.** An extruded letterform seen off-axis shows its near and far
outlines as two offset copies of the same word. Measured as the projected
separation of the front and back halves of the mesh, at 3840x2160:

```
frame  scale  depth_mm   front/back separation @4K
f1      1.00     52.0        6.77 px
f9      1.00     52.0        7.24 px
f60     1.00     52.0       15.95 px
f120    1.00     52.0       15.95 px
```

**Up to 15.95 px of double outline on a wordmark whose caps are ~68 px.** That is
a real, visible doubling of the word MERIDIAN and it is exactly what "doubled,
illegible" describes — but it is the letterform doubling itself, not two legends
colliding.

**I am not asserting this is what the user saw.** I asserted a mechanism once in
this block and it was wrong; this one is measured but it has NOT been tied to the
delivered frame, and I do not have that frame. It is a candidate with a number
on it, and that is all.

### the fix, validated but DELIBERATELY NOT LANDED

The remedy is the same either way and it is one line: scale `WallSign_Word`'s
local Z, which is the curve's extrusion axis, so glyph shapes, cap height,
letter-spacing, the fitted 2.60 m width and the mounting datum are all untouched.
The separation is exactly linear in depth:

```
scale 1.00 -> 52.0 mm -> 15.95 px worst
scale 0.50 -> 26.0 mm ->  7.97 px worst
scale 0.30 -> 15.6 mm ->  4.78 px worst
```

25-40 mm is the ordinary depth of applied wall letters at a 340 mm cap height, so
0.50 is a physically better sign as well as a less doubled one.

`tools/r2511_sign_occlusion.py --fix 0.5 --save <new.blend>` applies and
re-measures it in one pass.

**It is not applied to `film16.blend`, and that is a decision, not an omission:**

1. `film16` is the shipping candidate and its verification arms were still
   running against it. Mutating the artefact under a measurement in flight
   invalidates the measurement.
2. The ladder is being switched onto `film16`. Changing it now changes the thing
   being rendered halfway through.
3. **I have just refuted my own diagnosis of this defect once.** Landing a
   geometry change on the ship for a mechanism that is measured but not yet tied
   to the delivered frame is the move this project keeps punishing.

What would settle it is the delivered frame the user pointed at. With that, the
6.77-15.95 px double outline either matches what they saw or it does not, and the
fix follows in one command against a blend that is no longer under a running
pass.

### the gate

R2-509's two structural findings about `tools/text_overlap_gate.py` **stand and
are unaffected** by this refutation: it tests world-space coplanarity (so it
cannot see a screen-space effect of any kind) and it only walks round-2 modules
(so it cannot reach part-1 props at all). What has changed is what should replace
it. Not the `depth > gap` check R2-509 proposed — that check would have fired
here and it would have been wrong. The right instrument is the one that produced
this entry: **render the candidate legend alone, render it again behind its
neighbour as a holdout, and compare pixel counts** — with the neighbour's own
solo render as the positive control, because 0 % occlusion and a dead instrument
are indistinguishable without it.

---

## R2-512 — `film16` reached the ladder queue with NO BREACH IN IT, and nothing in the pipeline could have said so

**The defect.** `sim/apply_breach.py` was never run on `film16.blend`. Not
degraded — absent. The car drives through an **unbroken glass wall**, with round
1's undeformed aluminium grid still standing across it. That is R2-266's defect
in total form: the wall never breaks, so there is no wound to persist, and every
continuity result downstream of it is void.

**How it happened, exactly.** `render/world/assembly/r2/v124/build_film14.sh`
documents "THE FULL CHAIN, IN ORDER, and none of it skipped" — and that chain is
**three steps**, ending at `tools/build_film_scene.py`. The breach is landed by a
*different* script, `sim/land_breach.sh`, which is not named in it. I copied the
film14 harness one generation forward, faithfully, and inherited its blind spot.
The chain that says it is complete is not complete.

> **My verification was thorough on lighting, camera, items and levelling, and
> the breach was not on the list.** Every arm I built compared `film16` against
> `film14` — the *pre-breach* scene — and on that comparison `film16` is
> correct. The ship is `film14_breach_r6`, and nothing I ran ever compared
> against it. **A bar copied from the wrong baseline passes for the wrong
> reason.**

### the instrument: complementary signatures, not a string

Checking for one created object is weak — a name can be missing because the
applier did not run, because it was renamed, or because a read failed. So
`tools/breach_gate.py` asserts **both directions of the same event** on the same
file:

```
                                    film14_breach_r6   film16
CREATED  BREACH_Shards (collection)          1            0
CREATED  GP_b04        (pane)                2            0
CREATED  GS_b04_00000  (shard)               3            0
CREATED  BF_MUL05_S02  (baked frame piece)   3            0
DELETED  GW_Right_Mull_04    round-1 mullion 0            2
DELETED  GW_Right_Transom_0  round-1 transom 0            2
CONTROL  ONER          (camera)              6            6
```

A blend that never saw the applier fails on **both** arms at once — its created
objects missing AND its deleted objects still standing. No rename, no read error
and no compression artefact can imitate that. And the **CONTROL being non-zero
on the same file** is what makes the zeros mean anything: without it, "no
shards" and "the reader is broken" are the same reading, which is the failure
mode this project keeps rediscovering. The gate refuses with
`BREACH_GATE_UNREADABLE` if the control is zero, and with
`BREACH_GATE_INVALID` if the positive control blend fails.

### WHICH BAKE — the trap next to the fix

There are two landed tables on disk and applying the wrong one would have been
worse than applying none:

```
apply_film14_r6.json  (THE SHIP)   BF_MUL05_S02 max travel   0.1449 m   mullions [4,5,6]
apply_NEW.json        (R2-387)     BF_MUL05_S02 max travel  55.3509 m   mullions [3,4,5,6]
```

`sim/land_breach.sh` **stage 1 regenerates `sim/out/breach_film.npz` from
whatever raw bake sits in `sim/tmp/`**, so running the script end to end could
have silently swapped R2-387's table in. It was pinned instead:

```
sha256 3e312977987ac57a...  sim/out/breach_film.npz
sha256 3e312977987ac57a...  sim/out/breach_film_R6_SHIPPED.npz   <- byte-identical
sha256 b7f6041d30560b44...  sim/out/breach_film_R2387.npz        <- NOT this one
```

and the applier invoked directly with `--film sim/out/breach_film_R6_SHIPPED.npz`,
skipping stages 0–5 entirely. Stage 5b (the camera track) was checked and is not
read by `apply_breach.py`, so skipping it costs nothing.

### the general lesson, which is bigger than the breach

This is R2-502 one level up. R2-502 was a *build* that printed success having
written no file. This is a *pipeline* that produced an entirely plausible 7.5 GB
film with a whole stage missing, and every gate on it passed, because every gate
asked about the stages that did run.

**The pattern to hunt is: any stage that mutates the film AFTER
`build_film_scene.py`.** Those are exactly the ones an assembly-focused rebuild
does not think to invoke, because they are not in the assembly's chain and not in
the film builder's chain — they are in a third script nobody's checklist names.
Grepping `save_as_mainfile` over `tools/`, `sim/` and `anim/` returns 32 files;
most are A/B probes, but the ship-path mutators are a short list and it should be
written down in one place, the way `SHIPPING.md` names the one shipping world.

**The durable check is not a list of appliers, though — it is a set difference.**
Once `film16_breach.blend` exists, diff its object-name census against
`film14_breach_r6.blend`'s. Any family present in the ship and absent in the new
scene is a missed stage, whether or not anybody remembered it existed. That
subsumes guessing, and it is the only version of this check that cannot go stale
as appliers are added.

---

## R2-513 — the breach is landed on `film16`, and it reproduces the ship's apply exactly

`render/film16_breach.blend`, 7,600 MB, built by `sim/apply_breach.py` against
the pinned R6 table. Its apply report is **identical to the ship's in every
statistic**:

```
                          film14_breach_r6 (SHIP)   film16_breach (NEW)
objects                            3,845                  3,845
tris                             278,864                278,864
keys                           5,806,793              5,806,793
hero                               3,573                  3,573
east frame objects                    39                     39
east frame keys                    8,092                  8,092
mullions_replaced                [4, 5, 6]              [4, 5, 6]
n_transom_pieces                      12                     12
BF_MUL05_S02 max travel         0.1449 m               0.1449 m
coverage PASS                       True                   True
east wall PASS / panes / missing  True / 10 / []     True / 10 / []
```

**`BF_MUL05_S02` at 0.1449 m is the number that proves the RIGHT bake landed.**
R2-387's table on the same disk gives that body **55.3509 m** and replaces four
mullions instead of three; had `land_breach.sh` been run end to end, its stage 1
would have regenerated `sim/out/breach_film.npz` from whatever raw bake sits in
`sim/tmp/` and could have swapped it in silently. The applier was invoked
directly with `--film sim/out/breach_film_R6_SHIPPED.npz` instead, and stages 0–5
skipped. Stage 5b was checked first and is not read by `apply_breach.py`.

The two documented mid-apply verdicts both came out right:

```
R5 after the build: 0 intruders in the clear opening OVER THE WOUND
                    (was 3 -- GW_Right_Transom_0/1/2), 9 elsewhere
```

The 9 elsewhere are the south wall's `GW_Front_*` frame and the light fins, which
`sim/land_breach.sh` names as deliberate and not this module's to move — the
preflight's headline `glazing_pocket_clear FAIL` is that same population and is
what `--force` exists for. Read `R5_intruders_over_the_wound_after`, not the
preflight count.

### the readback diff, which is the arm that should have caught this

With `film14` measured on the same instrument, every invariant is identical and
only three fields move:

```
bytes            4,530,665,076 -> 7,507,149,067
n_objects               29,415 -> 31,133      (+1,718: 4 item families + driver)
n_objects_data          29,726 -> 31,444
interior_lamp_watts  46,203.313 = 46,203.313
23 stamps / 3.628 / AgX / None / -3.628 / 24 fps / 1..2978 / ONER   all identical
```

**And that is exactly why the missing breach survived it.** Every arm compared
`film16` against `film14` — the *pre-breach* scene — and on that comparison
`film16` is perfect. The ship is `film14_breach_r6`. **A readback diff against
the wrong baseline is a clean bill of health for the wrong file.** The baseline,
not the instrument, was the defect.

---

## R2-514 — the user's frame is **La Passerelle's fascia, not the gantry**, it is two DIFFERENT words, and it was already fixed nine hours before this rebuild started

The frame is `2972abcb3fa1.png`. The broker's own job record says what it is:

```
job 2972abcb3fa1   frame 2575   scene render/film14_breach.blend
                   ONER, 3840x2160, 400 samples, DOF on, CYCLES
                   finished 2026-08-04 02:02
```

**That hash is quoted verbatim in `world/build_architecture.py`.** R2-256's own
comment names this exact file:

> *"the delivered 4K frame 2972abcb3fa1.png shows gold CADENCE and white
> PASSERELLE printed through each other and garbling into 'PASSERELICE'."*

So the frame the user pointed at is the frame R2-256 was written from. It is **La
Passerelle**, a pedestrian overpass — the crop shows its truss above and its
supports below — and not the start/finish gantry.

### it is two words, measured, not one word doubled

The proposed reading was a gold front face with a grey extruded side wall behind
it: one word, self-doubled, ~16 px. Measured over the crop region of the 4K
original, splitting by saturation:

```
GOLD  8,340 px   mean RGB (0.484, 0.394, 0.267)   x 1637..1999 (362 px)   centroid (1832, 340)
GREY  1,889 px   mean RGB (0.293, 0.280, 0.264)   x 1620..2018 (398 px)   centroid (1796, 355)
GOLD letter spans: 8 distinct runs
```

**Self-doubling cannot produce this.** The front and back faces of one extrusion
are the same glyph set: same letter count, same run width, rigidly offset. These
two populations have **different widths (362 vs 398 px), different centroids
offset (36, 15), and different letter counts** — 8 gold runs against a longer
grey word. They are two different strings. The composite reads `PASSERELICE`,
which is `PASSERELLE` and `CADENCE` printed through each other, exactly as
R2-256 recorded.

Of the coordinator's three outcomes this is **(2) — two objects after all** — but
it is not a new defect and it does not resurrect anything. It is the *known* one:

```
build_architecture   "PASSERELLE  2"  white  at (-452.100, 2.000, 9.650)
build_dressing       CADENCE banner   gold   at (-452.055, 2.000, 8.920)
                                             45 mm in front, concentric, containing it
```

**That is the "two modules writing the same panel 45 mm apart" my brief named in
the first place, and my brief called it the gantry sign.** It is not the gantry;
it is the bridge. The misnomer is the whole reason this took four entries.

### what this means for the rebuild — it is already fixed, and film16 has the fix

```
2026-08-04 02:02   frame 2972abcb3fa1.png rendered from film14_breach.blend
2026-08-04 03:10   f9eb94b R2-256 lands: the truss-face lettering is DELETED
2026-08-04 15:46   assembly10 built from that source
2026-08-04 16:26   film16 built on assembly10
```

**The delivered frame predates the fix by 68 minutes.** `assembly9` was built
2026-08-03 23:09 and `film14` 23:42, both before `f9eb94b`, which is why every
`film14*` scene still carries it. `assembly10` is the first world built after it,
and `film16`/`film16_breach` are the first films that cannot show it — the
lettering is not in the source any more, so there is nothing to collide with the
banner. This was one of the six queued fixes and it is the one the user reported.

### what I got wrong, and it cost four entries

R2-509 and R2-511 measured the **MERIDIAN facade sign and the pit board**, which
were nominated as the real panels after the gantry framing was withdrawn. Both
conclusions about those panels stand and both were correct:

* they have exactly one writer each and no collision (four measurements);
* the wordmark occludes 0.00 % of the strapline (R2-511's refutation of my own
  R2-509 headline, with a working positive control).

**They were the wrong panels.** Neither was ever the defect. The defect was on a
third object that the brief named wrongly, that I had explicitly left flagged as
*"unmeasured, not clean"*, and that had already been fixed before I was briefed.

> **The durable lesson is about the identifier, not the geometry.** Three
> different objects were called "the sign" in this block — a trackside gantry, a
> showroom facade wordmark, and a bridge fascia — and every re-aim of the
> investigation moved to a different one while the name stayed the same. The
> frame hash was in the source the entire time. **One `grep 2972abcb3fa1` over
> the tree would have answered it in the first minute**, and it is the first
> thing to do with a delivered-frame complaint: the artefact has a name, so ask
> the tree what already knows about it before measuring anything.

**The self-doubling measurement from R2-511 is unaffected and still true** — a
52 mm extrusion does project 6.77–15.95 px of double outline at 4K on the
MERIDIAN wordmark. It is simply not what the user saw, and there is now no
evidence anyone has ever complained about it. **The `--fix 0.5` depth reduction
is therefore withdrawn as a proposal**: it addresses a real but unreported
artefact on a panel nobody raised, and cutting geometry on the ship for that is
not justified.

### the gantry, finally

**Not implicated at all.** R2-509b's source reading stands — one legend per face,
2.40 m apart, 40 mm extrusion, so it cannot produce either mechanism. It is still
unmeasured in pixels and still not being called clean, but it is no longer
suspected of anything.
