# WHICH ASSEMBLY IS THE SHIPPING WORLD

**`assembly8.blend` — built 2026-08-03 19:38, `world_contract` 1.2.1. PROMOTED
2026-08-03 by the rebuild agent; `assembly7.blend` is its immediate predecessor and
differs from it in ONE object and nothing else.**

`render/film12.blend`, the film scene the master renders from, is built on it.

## THIS IS THE DECLARATION, AND IT IS THE ONLY ONE

The bold run above is parsed — the first `` **`assemblyN.blend` `` after this
file's title — by `tools/shipping_world.py`, and by nothing else. Two consumers
read it:

* `tools/build_film_scene.py` REFUSES to build a film scene on any other world
  unless `--world-override REASON` is passed;
* `tools/input_stamp.py` stamps it as the `world` role, so every measurement
  records which world it was made against.

Both used to keep their own copy of the answer. `build_film_scene` named
`assembly6` for the whole of the day `assembly7` was the ship and two film
scenes went out on a superseded world (R2-071); `input_stamp:44` named
`assembly6` through the same promotion and nobody noticed, because a default
argument in a dict does not look like a decision (R2-100). **Do not add a
second copy. Change the line above.**

## why assembly8 is the ship, and exactly what moved

The rebuild was not a promotion between two candidates. `assembly7` was
**stale against three of its own five generators** — its own build tool said so:

    world/build_architecture.py    newer by 13.7 h
    world/build_dressing.py        newer by 13.9 h
    world/build_terrain.py         newer by  5.2 h

R2-071's rule is that a source fix is not landed until the artefact downstream
of it has been rebuilt *and re-read*, so it was rebuilt, from source, all five
modules, and re-read. **What was expected to move was written down before the
diff was run** (`v123/PREDICTION.md`), so what follows is a prediction met
rather than a story told afterwards.

### 1. ONE object moved, and it is the one the source predicts

Same instrument as the assembly6 → assembly7 comparison, unchanged:
`v120/vertex_fingerprint.py` + `v120/fp_diff.py`, per object, verts + coordinate
sums + sum of squares + bbox + a 0.1 µm order-independent hash.

    assembly7 -> assembly8            (v123/fp_assembly8.json)
      objects            28781 -> 28781    total verts 1282465803 -> 1282465803
      objects MOVED      1 of 28781 (0.00 %)
      objects BIT-IDENTICAL          28780
      objects with a different vertex COUNT   0
      name-set symmetric difference           0

    the one object     TER_Ground        vertex count UNCHANGED at 599 872
      bbox x            -10906.944336 .. 10826.944336   BIT-IDENTICAL
      bbox y            -10486.944336 .. 11216.944336   BIT-IDENTICAL
      bbox z min        -12.796212                      BIT-IDENTICAL
      bbox z MAX          38.004730  ->  364.460632     +326.4559 m
      sum of z         624947.720483 -> 3211062.660710  = +4.3111 m mean rise
                                                          over 599 872 verts

**Why, in one line of source.** `world/build_terrain.py` gained `far_horizon()`
and the `HORIZON_*` block in commit fe87552 at 09:07 — **five hours after
assembly7 was built at 04:45.** It raises the far field from `HORIZON_RISE_M`
3 600 m to a crest of `HORIZON_Z_M` 300 m at 9 500 m, plus three octaves of
relief (118 / 46 / 14 m). Its own note says it "changes z on vertices that
already exist — 599 872 verts and 600 209 polys either way", and that is exactly
what the fingerprint finds: **z only, no x, no y, no count.** Nothing inside
Dc < 3 600 m moves, so no barrier, surface, architecture, dressing or vegetation
object moves and the circuit itself is untouched — 28 780 objects bit-identical
says so directly.

That term is **not** credited with fixing beat 6's black band; R2-061's camera
clip was (`clip_end` 1 000 → 200 000 m). It is kept because without it the far
field is featureless haze with no horizon LINE.

The fingerprint diff was run against a **positive control** in the same batch:
v121's assembly5 → assembly6 pair, where exactly one object is known to have
moved 3.19 m. It reports 1 of 28 781 and a 3.1885 m shift. A "0 moved" from a
script that cannot report a move is not a result.

### 2. NO material moved — and this was measured over all 132, not 9

`work/lighting/dressing_bump_census.py` counts BUMP nodes, which is the right
instrument for the assembly6 → assembly7 question and the wrong one for this
one: `build_architecture` and `build_dressing` both changed here, and a census
pointed at bump chains is silent about a roughness that moved.

So `work/r2100/material_graph_census.py` fingerprints **every material, every
node, every input default, every link and every node property** (the three
censuses it produced are in `v123/`):

    assembly7 -> assembly8      materials 132 -> 132
                                graphs that MOVED     0 of 132
                                graphs BIT-IDENTICAL  132

**Positive control, same instrument:** assembly6 → assembly7 returns **9 of 132
moved, all `DR_*`**, and names the moves — `Bump.Normal -> Principled.Thin Wall`
removed, `-> Principled.Normal` added, `Noise Texture.Factor` off `Filter Width`
and onto `Height`. That reproduces this file's own R2-038/R2-057 table exactly,
from a script that had never been run before, so the 0 above is a measurement
and not a blind spot.

**This was predicted.** `build_architecture` and `build_dressing` were touched
only by 8c2f5dc (R2-072/R2-073), which turns a silently-dropped socket write
into a raise. R2-073 measured 342 runtime calls across all 22 material entry
points with **0 dropped**, so a guard that fires zero times writes the same
graph. It fired zero times.

### 3. Every module summary is identical, AND THAT PROVES NOTHING

    assembly7_build.json -> assembly8_build.json
      substantive differences   0
      differing fields          the five wall-clock timings and the output path

Read §"why assembly5 was wrong" below before quoting that line at anybody. The
counts were bit-identical while `TER_Ground` rose 326 m. **A summary that does
not change is not evidence that geometry did not move**, and this rebuild is the
second worked example of it in this file.

### 4. The socket audit passes, and it fails a blend that should fail

    tools/socket_index_audit.py --blend assembly8.blend   PASS   164 trees
    tools/socket_index_audit.py --blend assembly6.blend   FAIL   27 findings
    tools/socket_index_audit.py --blend assembly7.blend   PASS   164 trees

The middle line is what makes the other two mean something: the same arm, the
same run, on the artefact known to carry the nine miswired `DR_*` materials.

### 5. It was REGENERATED FROM SOURCE, and the determinism is the point

    surface       78.9 s      barriers   201.6 s     architecture  231.2 s
    terrain     1220.6 s      dressing   356.5 s
    total       2128.1 s in Blender, 2339 s wall, peak RSS ~4.7 GB

(Slower than assembly7's 1 443.6 s because four other agents' Blender jobs were
resident on the same 11 GB box; nothing in the build changed.)

**A 39-minute full regeneration of five modules landing on 1 282 465 803
vertices of which 1 282 465 803 minus one object's are BIT-IDENTICAL is what
makes the diff meaningful rather than vacuous.** `build_surface` and
`build_barriers` have not been touched since the baseline commit, and they came
back byte-for-byte. If they had not, every fingerprint comparison this project
has ever made would be void.

## assembly7, the immediate predecessor — kept for the record

`assembly7.blend` is not dangerous, only stale: it predates `build_terrain`'s
horizon. It is the control this promotion was measured against and it stays.
Everything below was written when it was the ship.

## why assembly7 superseded assembly6, and why that promotion cost nothing

This was not a choice between two worlds. It is the same world with nine dressing
materials repaired, and **that is measured three independent ways** rather than
argued.

**1. The geometry is identical — not "the summaries agree", which this file already
warns is worthless.** `v122/fp_assembly6.json` against `v122/fp_assembly7.json`, per
object, verts + coordinate sums + sum of squares + bbox + hash:

    assembly6 -> assembly7
      objects            28781 -> 28781    total verts 1282465803 -> 1282465803
      objects MOVED      0 of 28781 (0.00 %)
      name-set symmetric difference   0
      rows that differ in ANY field   0

**2. Exactly nine materials differ, all `DR_*`, and nothing else in the file does.**
Counted by loading only the material datablocks out of each blend
(`work/lighting/dressing_bump_census.py`, `bump_assembly{6,7}.json`) — 130 materials
in both, and the diff is:

| | assembly6 | assembly7 |
|---|---|---|
| `DR_*` bump nodes | 9 | 14 |
| with `Height` linked | **0** | **14** |
| with `Filter Width` linked | 9 | 0 |
| into Principled `[6] Normal` | **0** | **9** |
| into a chained `Bump.Normal` | 0 | 5 |
| into Principled `[5] Thin Wall` | **9** | **0** |

which reconciles this file's earlier "9 Normals linked" exactly: 14 bump outputs land
on a socket *named* `Normal`, of which 9 are Principled inputs and 5 are chained bump
stages. No non-`DR_` material differs in any field.

**3. It was REGENERATED FROM SOURCE, not patched into a built blend.** This is the
trap R2-061 fell into twice — a fix applied to an artefact is reverted by the next
rebuild. `assembly7_build.json` records all five modules actually running (surface
53.2 s, barriers 125.9 s, architecture 146.7 s, terrain 982.8 s, dressing 130.7 s,
1443.6 s total), and diffed against `assembly6_build.json` **every count, area and
total is identical** — the only differences are those five wall-clock timings, the
contract string 1.2.0 -> 1.2.1, and the output path.

That last point also makes point 1 mean something. A 24-minute full regeneration
landing on 1,282,465,803 *identical* vertices is what separates "nothing differs"
from "nothing was compared".

And the fix is durable at source. `build_dressing.py` no longer addresses the socket
by index at all:

    def _feed_named(self, node, name, v):
        """`_feed`, addressing the socket BY NAME.  USE THIS FOR `Normal`."""

Index addressing is what made this a recurring defect rather than a one-off: Blender
5.2 moved `Normal` from 5 to 6 and every index-addressed wire silently shifted onto
its neighbour. Addressing by name removes the whole class, not the current offset.

## what assembly6 was actually doing, stated accurately

The bump chain fed the height texture into `Filter Width`, so `Height` sat on a
constant with zero gradient (R2-038), and the output then went to Principled `[5]`,
which is `Thin Wall` in 5.2, not `Normal` (R2-057). Either defect alone produces the
same picture, which is why fixing one and measuring would have returned a perfect and
entirely convincing null.

**`Thin Wall` is not an inert socket** — it switches how the BSDF interprets the
shell — so the obvious escalation is that those nine materials were an *active wrong
result* and not merely an absent right one. **That escalation was tested and it does
not land.** All nine are opaque (`work/lighting/dr_trans_a6.json`):

    DR_Alu Concrete Fabric Plastic Print Rubber Steel Tarp Wood
        Transmission Weight 0.0, Alpha 1.0, Thin Wall LINKED<-BUMP
    DR_Glass
        Transmission Weight 1.0, Thin Wall 0.0 and UNLINKED  <- never miswired
    DR_Emit, DR_Paint
        Transmission 0.0, Thin Wall 0.0

With no transmission and no alpha, Cycles never reaches the thin-shell branch, so the
defect degenerates to plain flatness across 4.29 M triangles of trackside dressing.
**assembly6 got away with it** — by one material. The only dressing material that
does carry transmission, `DR_Glass`, has no bump chain at all. Had it had one, a
height texture would have been switching glass between thick and thin shell per pixel,
which nobody would ever have read as a bump defect.

## what promoting it did NOT change, measured in rendered pixels

Beats 4, 5 and 6 of the ten-frame ladder probe were rendered from a film scene built
on assembly6 and again from one built on assembly7, at identical settings. See
`work/lighting/L0relit_a6` vs `L0relit_a7` and the table in the relight agent's
report.

`assembly5.blend` is SUPERSEDED and **must not be rendered from** — see below.
`assembly6.blend` is not dangerous, only stale; it is kept as the immediate
predecessor and as the control the promotion was measured against.

`assembly5.blend` is SUPERSEDED and **must not be rendered from**. Its
`BR_Transit_NorthWall` stands up to **3.333 m outboard** of the contract's declared
`TRANSIT_NORTH_OFFSET_M` = +8.000 over the last 32 m of the Beat-4 corridor — the shot the
camera flies at 200 km/h. Measured on the blend itself: the wall's inner face runs 7.840 m
to route t 63 and then climbs to 11.173 m at t 96.

## why assembly5 was wrong, and why nobody caught it

`build_barriers` §21 carried a correction table that read `telemetry/telemetry.csv` and
pushed the corridor walls outboard to stay clear of a car that appeared to be driving
through them. It existed because `tools/build_telemetry.py` integrated the declared
R150 / 40° transit merge as a **straight chord**, putting the car up to 9.04 m off its own
road. R2-042 fixed the telemetry; §21 became a no-op that still fired against the *old*
CSV, and assembly5 was built at 12:43 — **71 minutes before the corrected CSV was written
at 13:54.**

**assembly5 and assembly6 have BIT-IDENTICAL module summaries.** Every count, area and
total that `assemble.py` reports is the same in both. That is why the rebuild that produced
assembly5 concluded, wrongly, that no geometry had moved.

    per-object vertex fingerprint, assembly5 -> assembly6
      objects            28781 -> 28781      total verts  1282465803 -> 1282465803
      objects MOVED      1 of 28781 (0.00 %)
      the one object     BR_Transit_NorthWall
      bbox_max           [106.858, 18.024, 2.56] -> [107.877, 14.835, 2.56]
      shift              3.1885 m in y, 1.019 m in x, 0 in z, SAME vertex count (1573)

**A summary that does not change is not evidence that geometry did not move.**

## what to run

    v123/verify_assembly8.sh the assembly7 -> assembly8 readback, with all three
                             positive controls, and v123/verify_assembly8.log as
                             it came out.  v123/PREDICTION.md is what was
                             expected, written before the diff was run.
    v123/fp_assembly8.json   the per-object vertex fingerprint, and
                             v123/matcensus_assembly{6,7,8}.json the material
                             graph censuses the material diff is taken over.
    v121/battery.sh          the gate battery on assembly6, with controls, and the
                             vertex-fingerprint diff that is the point of it
    v121/attribute.sh        today's probes against assembly5, so a probe difference can
                             be attributed to the instrument or to the world
    v121/*.png               the Beat-4 renders, the A/B against assembly5, and the
                             LABEL_* overlays that put the contract's declared wall line
                             into the picture's own pixels

## results, 2026-08-02

    placement_gate (#88-repaired, ground-referenced corridor)  PLACEMENT_CLEAN, 0 violations
      closest car_path  BR_Concrete_L12  +4.608 m   (was ARCH_RetainEdge +0.359 m
                                                     against the chord-driven path)
    probe_roadclear     ROADCLEAR_CLEAN, +ve control fires 6.98 m, -ve control silent
    probeA C D E G B    identical to assembly5 under the same instrument, except
                        probeA.P4_barrier_feet (the moved wall) and the contract string
    probe_pitexit       identical
    instance_variety / variety_distribution / mesh_reuse   identical
    collision_gate / depth_probe on the world               VACUOUS (as on assembly5)
    Beat-4 render f1081 / f1090, ONER camera, 5090          18.3 % / 20.1 % of the frame
                        differs from assembly5, and the differing pixels are exactly the
                        north wall and its cast shadow. Nothing else in the frame moved.
