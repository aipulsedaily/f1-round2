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
