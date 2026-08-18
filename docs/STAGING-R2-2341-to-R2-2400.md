# STAGING R2-2341 .. R2-2400

Working notes. `docs/DEFECT-LOG-R2.md` is merged by hand and is NOT edited here.

---

## R2-2341 — #97 (REOPENED): THE REPORT IS REPRODUCIBLE, THE NUMBER IS NOT A PROPERTY OF THE WORLD, AND THE SHIPPING WORLD HAS 1,202 PLACEMENT VIOLATIONS NOBODY HAS EVER SEEN

Agent `r2-2341-placement-determinism`. Blender 5.2.0 LTS
(`/opt/blender-5.2.0-linux-x64/blender`), CPU, 11 GB box shared with four other
agents' Blender processes.

### The premise had to be split before any verdict was available

#97 says a closest-approach figure moved between two runs with no world change.
R2-1761 already closed half of it (provenance stamps: `tools/provenance.py`,
`tools/report_repro.py`) and recorded, against itself, that
**the determinism result did not cover `closest_approach`** — `--selftest`
writes `controls` and `failures` and has no such block. That is the gap this
item works.

Three separate questions were tangled inside "it varies", and they have three
different answers:

| question | answer |
|---|---|
| Does the gate scatter run-to-run on a fixed world with frozen inputs? | **No. Byte-identical.** |
| Can the reported number change without the world changing? | **Yes — two mechanisms, both live, both now closed.** |
| Is the world actually passing? | **NO. `assembly14` is `PLACEMENT_FAIL`, 1,202 violations. The verdict of record is `PLACEMENT_CLEAN` from a world seven assemblies old, and the gate was adjudicating on 3 % of the shipping world.** |

---

### 1. THE DISTRIBUTION, MEASURED

Fixed world `world/verify_world.blend` (4.17 GB, 28,458 meshes, 28,392 tested,
291 measured per-vertex). All four keep-out inputs FROZEN into
`work/r2-2341/frozen/` first, because the last time this was attempted a peer
rebuilt `docs/beat_sheet.json` underneath the runs. The world's size+mtime is
recorded either side of every run.

**Six runs, pinned instrument (`tools/_r2341_gate_HEAD.py`, sha
`aa9f0712d0690ba7` = `git show HEAD:tools/placement_gate.py`):**

```
run 1 gate=aa9f0712d0690ba7 rc=1 248s pre=[4166294563 1785630450] post=[4166294563 1785630450] >> STAGE RESULT: PLACEMENT_FAIL
run 2 gate=aa9f0712d0690ba7 rc=1 246s pre=[4166294563 1785630450] post=[4166294563 1785630450] >> STAGE RESULT: PLACEMENT_FAIL
run 3 gate=aa9f0712d0690ba7 rc=1 208s pre=[4166294563 1785630450] post=[4166294563 1785630450] >> STAGE RESULT: PLACEMENT_FAIL
run 4 gate=aa9f0712d0690ba7 rc=1 195s pre=[4166294563 1785630450] post=[4166294563 1785630450] >> STAGE RESULT: PLACEMENT_FAIL
run 5 gate=aa9f0712d0690ba7 rc=1 228s pre=[4166294563 1785630450] post=[4166294563 1785630450] >> STAGE RESULT: PLACEMENT_FAIL
run 6 gate=aa9f0712d0690ba7 rc=1 259s pre=[4166294563 1785630450] post=[4166294563 1785630450] >> STAGE RESULT: PLACEMENT_FAIL
```

```
run      body_sha           total  closest_approach_m
r1.json  861dc1eb1b042921   13     camera_path=0.648@BR_Verge_R  car_path=-1.4344@BR_FenceStruct_L03  road_corridor=-7.714@BR_Armco_L03
r2.json  861dc1eb1b042921   13     (identical)
r3.json  861dc1eb1b042921   13     (identical)
r4.json  861dc1eb1b042921   13     (identical)
r5.json  861dc1eb1b042921   13     (identical)
r6.json  861dc1eb1b042921   13     (identical)

-- distribution over 6 runs --
body sha: {'861dc1eb1b042921': 6}
  camera_path    1 distinct value(s)
  car_path       1 distinct value(s)
  road_corridor  1 distinct value(s)
```

`tools/report_repro.py` on any pair:

```
   REPRODUCED
   every declared input, the tool, the contract and itemkit hash identically, and the report bodies are identical.
>> STAGE RESULT: OK (REPRODUCED)
```

**THE DISTRIBUTION IS A DELTA FUNCTION.** Not a two-valued flip, not continuous
jitter — zero spread, byte-identical report bodies, six for six. So the honest
answer to "reproduce it first" is: **on this world, with these inputs, at this
`HEAD`, it does not reproduce.** No defect was manufactured to match the
ticket.

Six runs bound the rate of a rare outlier; they do not exclude one. That is the
argument for §4's `--repeat`: a rare event does not have to be caught in a
campaign if every future run checks itself.

**But "deterministic today" is not the same claim as "the number is a property
of the world", and the two were being conflated.** §3 names two mechanisms that
change the reported figure with the world untouched, and one of them is
one exact tie away from firing.

### 2. I BROKE MY OWN BASELINE, AND PROVENANCE CAUGHT IT

The first campaign was started before I began editing `tools/placement_gate.py`,
and I then edited the gate while it was still running. Each Blender invocation
picks up the file as it is on disk at launch, so run 3 measured with a different
tool than runs 1 and 2. Nothing in the printed output said so. The stamp did:

```
run 1  tool_sha= aa9f0712d0690ba7   2026-08-08T06:33:40
run 2  tool_sha= aa9f0712d0690ba7   2026-08-08T06:36:45
run 3  tool_sha= 55e71e9b481702ed   2026-08-08T06:39:26   <- not the same instrument
```

That campaign was discarded and re-run against a pinned copy of the gate at
`HEAD` (`tools/_r2341_gate_HEAD.py`, sha `aa9f0712d069…`, byte-identical to
`git show HEAD:tools/placement_gate.py`). It is worth recording as the live
demonstration that R2-1761's stamp does the job it was built for — including
against the agent who is supposed to be careful with it.

---

### 3. THE ENTROPY SOURCES

Suspects were eliminated cheapest-first, and the ones that survived are named
with the line that causes them.

**`PYTHONHASHSEED` — ELIMINATED, one experiment, whole family.** The gate does
iterate sets (`split_subject_context` returns them) but every consumer either
takes `len()` or `sorted()`. Six runs of the real gate on
`v120/ctl_place_nearmiss_neg.blend` at seeds `0 / 1 / 12345 / 999 / random /
unset` gave the same three closest approaches to the fourth decimal:

```
seed=0       road_corridor 0.3892  car_path 6.7805  camera_path 2.5754  CTL_Obstacle
seed=1       (identical)
seed=12345   (identical)
seed=999     (identical)
seed=random  (identical)
seed=unset   (identical)
```

**`mathutils.kdtree` — ELIMINATED.** Every measurement in this gate resolves
through `vol["kd"].find(...)` (`intrusion()`), so a tree that balanced
differently per process, or broke equidistant ties per process, would move
every number. `work/r2-2341/kd_probe.py` builds a 4,000-station tree, queries
40,000 points, hashes the whole nearest-index map, and repeats it after
randomly-sized heap churn:

```
KDPROBE hashseed=None    nearest_sha=c91643fb609c6c40 after_churn_sha=c91643fb609c6c40 ties=[(10,10),(250,250),(1999,2000),(3777,3777)] junk=34168
KDPROBE hashseed=0       nearest_sha=c91643fb609c6c40 after_churn_sha=c91643fb609c6c40 ties=[(10,10),(250,250),(1999,2000),(3777,3777)] junk=191959
KDPROBE hashseed=1       nearest_sha=c91643fb609c6c40 after_churn_sha=c91643fb609c6c40 ties=[(10,10),(250,250),(1999,2000),(3777,3777)] junk=62050
KDPROBE hashseed=12345   nearest_sha=c91643fb609c6c40 after_churn_sha=c91643fb609c6c40 ties=[…] junk=29896
KDPROBE hashseed=random  nearest_sha=c91643fb609c6c40 after_churn_sha=c91643fb609c6c40 ties=[…] junk=50616
```

Identical map, identical tie resolution, across processes and allocation
histories. Not the source.

**THE SCENE-ORDER TIE-BREAK — CONFIRMED, and it is the one #97 is named for.**
`placement_gate.py` at HEAD, in `measure()`:

```python
if not is_ctx and d > closest.get(vname, (-1e9,))[0]:
    closest[vname] = (d, ob.name, at)
```

A strict `>` over `for ob in scene.objects`. On an **exact tie the winner is
whichever object the scene walk reached first**, and scene order is not a
property of the world — it moves when an object is added, removed, renamed,
relinked, or the file is re-saved by a different tool. This world is built from
repeated modules on a regular station grid and the adversarial review already
found *the Beat-4 corridor built twice, 0.5 m apart*, so exact ties are the
normal case here, not a curiosity. Demonstrated below with two identical cubes:
the shipped rule reports `SELFTEST_TieA` or `SELFTEST_TieB` purely according to
link order.

**THE SILENT `world_contract` FALLBACK — CONFIRMED as a mechanism.**
`half_width_fn()` at HEAD:

```python
    try:
        import world_contract as WC
        if hasattr(WC, "half_width"):
            return WC.half_width
    except Exception:
        pass
    ...
    return lambda s: w * 0.5          # a CONSTANT half-width
```

The two branches build corridors of different radius (7.00–8.50 m per station
versus a flat `width_m/2`), so **every** number in the report moves across that
`except`. `world/world_contract.py` is a 4,200-line file that six agents share
and that imports numpy; a transient half-written state or a stale
`__pycache__` flips this branch for one run and back for the next, and no
report recorded which side it had been on.

**THE ORIGINAL-vs-EVALUATED MATRIX — CONFIRMED as a mechanism.** `measure()`
coarse-rejects on `bbox_world(oe)` — the **evaluated** object — and then
transforms the vertices by `ob.matrix_world`, the **original's** cached matrix:

```python
lo, hi = bbox_world(oe)     # evaluated
...
mw = ob.matrix_world        # original
```

For anything parented, constrained or driven the two differ, and `matrix_world`
on the original datablock is a value the depsgraph writes — so which one you got
depended on whether the depsgraph had been evaluated. `measure()` never called
`view_layer.update()`; `--selftest` did, which is why the controls never saw it.

**UNDECLARED INPUT DRIFT — already closed by R2-1761, and it is the documented
cause of the one flip on record.** `v120/placement_v120.json` →
`v120/placement_v120_recheck.json`, same `assembly5.blend`, 1.4 h apart, every
other field byte-identical:

```
car_path   ARCH_RetainEdge  +0.3592 m   ->   BR_Concrete_L12  +4.6084 m
```

`SHIPPING.md` records the cause in a parenthesis nobody could have checked at
the time — *"(was ARCH_RetainEdge +0.359 m against the chord-driven path)"* —
i.e. `telemetry.csv` was rebuilt underneath the two runs. `road_corridor` and
`camera_path` did not move, which is exactly the signature of the car volume's
input moving alone. Provenance now records it.

**MEMORY-PRESSURE SKIPS — a mechanism, not observed firing.** `bbox_world()`
and `to_mesh()` were both wrapped in a bare `except: continue`. On an 11 GB box
running four Blenders, an object that fails to convert leaves the survey with
no record, and `closest_approach` moves. Zero skips were observed in any run
here, so this is closed on the grounds that it is now *visible*, not on the
grounds that it never happened.

---

### 4. THE FIX

All in `tools/placement_gate.py` unless stated.

1. **A total order on the closest approach.** New `_better(d, tag, cur)` —
   depth first, then **name**. Applied to the per-object winner *and* to the
   per-vertex `at_world`, so neither the reported object nor the reported
   coordinate can depend on the walk.
2. **The runner-up and the margin are reported.** New
   `determinism.closest_approach_margin[volume]` carries `winner`,
   `runner_up`, `margin_m`, and says `EXACT TIE` in words when the margin is
   0.0 — because "ARCH_Gantry 1.1491 m" and "ARCH_Gantry 1.1491 m with another
   object tied to the last bit behind it" are different answers and only one of
   them is a property of the world.
3. **`--repeat N` (default 2): the report asserts its own reproducibility.**
   The unchanged scene is measured N times in one process and the results are
   fingerprinted; disagreement is `PLACEMENT_NONDETERMINISTIC_REFUSED`, which
   `gate_exit` maps to **VACUOUS (3)**, not FAIL — the world may be perfectly
   clean and sending somebody to move an object on the strength of an
   unrepeatable number is the second-worst outcome available. The refusal is
   checked **before** CLEAN/FAIL, so an irreproducible run cannot print either.
4. **The scene walk order is hashed into the report**
   (`determinism.scene_walk_order_sha256`), so two *processes* can be diffed on
   it by `tools/report_repro.py`, which the in-process repeat cannot cover.
5. **Silent skips are named.** `bbox_world` / `to_mesh` / empty-mesh exits are
   collected into `determinism.skipped` with the exception text and printed.
6. **`half_width_fn()` returns its source**, which goes into the report body
   (`road_corridor.half_width_source`, `_min_m`, `_max_m`) and is printed. A
   `world_contract.py` that exists but will not import is now a **REFUSAL**
   rather than a silent swap to a constant corridor.
7. **`view_layer.update()` before `evaluated_depsgraph_get()`**, and the
   per-vertex transform uses `oe.matrix_world` — the same object the coarse
   reject bounded.
8. **The car band is in the report body.** `clearances` gains `car_zlo`,
   `car_body_top`, `car_body_w`, `car_swept_half_w`, `car_band_top`. #78's
   340 mm band error moved `closest_approach` and left no trace in any report
   it moved; a body diff sees it now.
9. **The edge-family courtesy is scoped to the road corridor** — see §6.

---

### 5. THE CONTROLS, AND THEIR DELIBERATE FAILURES

`placement_gate.py --selftest` went from 26 controls to **39, all behaving**
(`work/r2-2341/runs/ctl/selftest_fixed2.log`). Four of the new ones are
controls-on-the-control, i.e. they assert that the thing being tested is
capable of failing.

**5a. The tie-break, watched to flip.** Two identical cubes at an identical
transform — an exact tie by construction, not by float luck — measured under
both link orders, through the gate's own `measure()`:

```
   walk order A,B -> ['SELFTEST_TieA', 'SELFTEST_TieB']   walk order B,A -> ['SELFTEST_TieB', 'SELFTEST_TieA']
   PASS  CONTROL: permuting the link order really does move the scene walk    fires=True  expected=True  cae15b13a0d1d99b vs 405db0d9469eebbb
   PASS  the two objects are an EXACT tie (margin 0.0 m)                      fires=True  expected=True  margin 0.0 m
   PASS  CONTROL: the SHIPPED first-wins rule FLIPS the reported object       fires=True  expected=True  SELFTEST_TieA -> SELFTEST_TieB
   PASS  the GATE's closest_approach is the same under both walk orders       fires=True  expected=True  SELFTEST_TieA vs SELFTEST_TieA
   PASS  the deterministic rule agrees with the gate on both orders           fires=True  expected=True  SELFTEST_TieA / SELFTEST_TieA / SELFTEST_TieA / SELFTEST_TieA
```

Line 3 is the deliberate failure. The shipped rule is reconstructed inline
(same pattern the file already uses for `old_absolute_hit`) and is **required**
to flip; if it ever stops flipping, the control declares itself broken rather
than passing. Line 1 is the control's own control — without it, everything
below would pass on a scene that never changed.

**5b. The repeat assertion, fed a non-deterministic input end to end.** New
`tools/placement_determinism_control.py`. It wraps `placement_gate.measure` so
the SECOND pass returns one changed object name — the smallest possible version
of exactly the defect #97 is named for — then runs the gate's own `main()` and
requires a refusal; then removes the perturbation and requires the same
`main()`, on the same scene, to reach a verdict. Both `>> STAGE RESULT:` lines
that `main()` prints are captured, so the two-verdict trap cannot bite; this
file prints exactly one verdict of its own.

```
>> DETERMINISM CONTROL: the assertion is fed a non-deterministic input FIRST, and must refuse.
      [gate said] >> THE SAME UNCHANGED SCENE MEASURED DIFFERENTLY ON REPEAT:
      [gate said] >> determinism: 2 pass(es), DIFFERED; scene walk 07796cdeb7857159; 0 object(s) unmeasurable
      [gate said] >> REFUSING TO REPORT: the same unchanged scene measured differently on repeat, in one process, with nothing touched between passes. Every number above is unciteable.
   PASS  a deliberately non-deterministic measure() is REFUSED      got=PLACEMENT_NONDETERMINISTIC_REFUSED expected=PLACEMENT_NONDETERMINISTIC_REFUSED  exit code 3
   PASS  ...and the refusal is NOT spelled as a pass                got=True    expected=True  code 3

>> DETERMINISM CONTROL: perturbation removed, same scene, same arguments -- the gate must now produce a verdict.
      [gate said] >> determinism: 2 pass(es), IDENTICAL; scene walk 07796cdeb7857159; 0 object(s) unmeasurable
   PASS  the unperturbed run is NOT refused as non-deterministic    got=True    expected=True  verdict PLACEMENT_FAIL (exit 1)
   PASS  the unperturbed run reaches a real placement verdict       got=True    expected=True  verdict PLACEMENT_FAIL

>> the determinism assertion has been observed to FAIL on a non-deterministic input and to PASS on the same scene without it
>> STAGE RESULT: PLACEMENT_DETERMINISM_CONTROL_OK
```

**5b-i. The fixed gate, three runs, same world, same frozen inputs.** The fix
changes no number — 13 violations before and after, identical closest
approaches — and the report bodies are again identical across runs:

```
run      body_sha           total  closest_approach_m
r1.json  056e7338228702b4   13     camera_path=0.648@BR_Verge_R  car_path=-1.4344@BR_FenceStruct_L03  road_corridor=-7.714@BR_Armco_L03
r2.json  056e7338228702b4   13     (identical)
r3.json  056e7338228702b4   13     (identical)

camera_path    HEAD BR_Verge_R 0.648            FIXED BR_Verge_R 0.648
car_path       HEAD BR_FenceStruct_L03 -1.4344  FIXED BR_FenceStruct_L03 -1.4344
road_corridor  HEAD BR_Armco_L03 -7.714         FIXED BR_Armco_L03 -7.714
```

Cost: `--repeat 2` roughly doubles the measure phase (230 s → 280-480 s on a
28,392-object world, load included).

**5b-ii. AND THE NEW REPORT IMMEDIATELY SAID TWO THINGS NO PREVIOUS REPORT COULD.**

```
>> closest approach, camera_path    BR_Verge_R           +0.648 m of clearance   (ARCH_Gantry 0.0311 m behind)
>> closest approach, car_path       BR_FenceStruct_L03   -1.434 m of clearance   (BR_FenceMesh_L03 0.0009 m behind)
>> closest approach, road_corridor  BR_Armco_L03         -7.714 m of clearance   (BR_FenceStruct_L03 0.1076 m behind)
>> determinism: 2 pass(es), IDENTICAL; scene walk df2f0909d45dace1; 26 object(s) unmeasurable
```

1. **The `car_path` winner beats its runner-up by 0.9 mm.** The gate's own
   declared resolution is `REPORT_TOL_M = 10 mm`, justified in its header by a
   centreline reconstruction that is up to 5.34 mm from the contract's. So the
   OBJECT NAME in `closest_approach_m.car_path` is separated from the next
   candidate by **less than a tenth of the instrument's own noise floor**. It
   is not a tie, so the tie-break does not fire — but "which object is closest"
   is, on this world, a question this instrument cannot answer, and until now no
   report said so. That is the same class of statement as #97's original
   complaint, arrived at from the other direction.
2. **26 objects were leaving the survey silently.** All of them `VEG_*`
   prototypes (`VEG_shrub_bramble_L0`, `VEG_grass_fescue`, `VEG_stone_boulder`,
   …) whose evaluated mesh has no polygons. Plausibly harmless — they read like
   instancing sources — but nobody could have known that, because nothing
   printed them. Flagged, not chased: if the vegetation reaches the world only
   as instances off these prototypes, whether the gate measures vegetation *at
   all* is a separate question and not this item's.

**5b-iii. The `matrix_world` mismatch is latent on this world, not firing.**
`tools/placement_entropy_probe.py` measured `|ob.matrix_world −
oe.matrix_world|` for every object that reached the per-vertex path:
`mw_mismatch 0` over 291 objects, both passes. The fix is correct and the
mechanism is real, but on `verify_world` it changes nothing today. Said plainly
rather than counted as a catch.

**5c. An object that cannot be measured is named, not dropped.**

```
   PASS  an object with no polygons is NAMED as unmeasurable, not dropped   fires=True  expected=True  skipped: ['SELFTEST_NoPolys']
   PASS  CONTROL: the measurable object beside it is still measured         fires=True  expected=True  closest: (6.58562085165003, 'SELFTEST_Solid', (-248.468, 485.557, 7.964))
```

---

### 6. DOES THE STABILISED NUMBER CHANGE A VERDICT?

**On the tie-break alone: no verdict on disk flips.** All seven placement
reports that carry a `closest_approach_m` block were re-read; none of their
recorded winners sits at a zero margin, and stabilising the tie-break moves
none of their `total` counts. That is worth saying plainly rather than
inflating: the tie-break was a live hole, and it had not yet fired on a report
anybody quoted.

**But two things came out of re-asking the question, and both change what
ships.**

#### 6a. A CLEAN VERDICT WHOSE OWN HEADLINE NUMBER SAYS 155 mm INSIDE THE CAR'S PATH

`docs/placement_after_46.json`, produced by `chain_v111.sh` on `assembly4`:

```json
"total": 0,  "violations": [],
"closest_approach_m": {
  "car_path": {"object": "ARCH_RetainEdge", "clearance_m": -0.1553, ...}
}
```

A **negative clearance is an intrusion**. That report says PLACEMENT_CLEAN and,
three lines down, says something reaches 155 mm into the volume the car sweeps.
The two halves contradict each other, and the cause is one line in `measure()`:

```python
limit = ROAD_MARGIN if ob.name.startswith(EDGE_FAMILIES) else 0.0
```

`limit` was computed **per object**, so an `EDGE_FAMILIES` name bought 0.50 m of
exemption in **all three** volumes. The justification for that exemption is
entirely about the road corridor — the corridor's radius is inflated by
`ROAD_MARGIN`, and a kerb whose inner lip sits on the white line is 0.50 m
inside *that inflated shape* while being exactly on the true boundary. Neither
of the other two volumes is inflated by `ROAD_MARGIN`: `car_path` is half the
car plus `CAR_MARGIN`, `camera_path` is a `CAM_CLEAR_R` sphere. The same 0.50 m
there is not a courtesy, it is half a metre of the car's swept volume and of
the camera's clearance sphere, handed over on a prefix match — to
`DR_Kerb`, `SURF_Kerb`, `KPU_`, `BR_Subbase`, `BR_Verge`, `ARCH_PitWall` and
`ARCH_RetainEdge`.

`limit` is now computed **per volume**, and the courtesy applies only to
`road_corridor`.

**Watched to fail, on one blend, through both gates.**
`work/r2-2341/ctl_edge_carpath.blend` holds a single object named
`ARCH_RetainEdge_CTL` placed by bisecting the gate's own `intrusion()` to
exactly 0.200 m inside the car path, at a transit station chosen because it is
74 m clear of the road corridor and 1.4 m clear of the camera sphere — so the
control isolates the car volume and nothing else can fire:

```
===== gate: tools/_r2341_gate_HEAD.py  (sha aa9f0712d0690ba7)
>> closest approach, car_path       ARCH_RetainEdge_CTL          -0.200 m of clearance   at (-0.0, 1.402, 0.5)
>> STAGE RESULT: PLACEMENT_CLEAN

===== gate: tools/placement_gate.py  (sha 93af5324216fe2e9, the final file)
>> closest approach, car_path       ARCH_RetainEdge_CTL          -0.200 m of clearance   at (-0.0, 1.402, 0.5)
>> 1 PLACEMENT VIOLATIONS (ranked by intrusion depth)
     car_path        ARCH_RetainEdge_CTL                   0.200 m in   at (-0.0, 1.402, 0.5)
>> STAGE RESULT: PLACEMENT_FAIL
```

Same world, same inputs, same second. `PLACEMENT_CLEAN` → `PLACEMENT_FAIL`.
And `--selftest` keeps the courtesy where it belongs, straddled:

```
   PASS  CONTROL: a PLAIN object 0.20 m into the car path is a violation                         fires=True  expected=True  [0.2001]
   PASS  an EDGE-FAMILY object 0.20 m into the CAR PATH is a violation too                       fires=True  expected=True  [0.2001]
   PASS  CONTROL: a PLAIN object 0.20 m into the corridor IS a violation                         fires=True  expected=True  [0.2001]
   PASS  an EDGE-FAMILY object 0.20 m into the CORRIDOR is still excused (courtesy kept …)       fires=False expected=False
```

#### 6b. THE PLACEMENT VERDICT ON RECORD IS SEVEN ASSEMBLIES OLD

The shipping world is `assembly14.blend` (`SHIPPING.md` line 3, promoted
2026-08-07 22:40). The newest placement report on disk that can say what it
measured is `v122/placement_v122.json`, and its own stamp says:

```
blend  render/world/assembly/r2/assembly7.blend  97d0a53094f67d8f
written 2026-08-03T04:59:59
```

`SHIPPING.md`'s "results" block quotes `PLACEMENT_CLEAN, 0 violations` under a
2026-08-02 heading, on `assembly5`/`assembly6`. **No placement report exists for
assembly8 through assembly14.** The gate that guards "nothing on the road" has
not been run on the world that is shipping, and no amount of determinism work
substitutes for running it.

So I ran it. **It does not pass, and the reason it was never going to be caught
is worse than the number.**

#### 6c. ON THE SHIPPING WORLD THE GATE WAS ADJUDICATING ON 3 % OF IT

First run of the (already determinism-fixed) gate on `assembly14.blend`:

```
>> subject: 900 meshes via collection 'ITEM_spectator_crowd' (item-campaign convention); 5 item collections present, took the largest -- pass --subject to be explicit
>> tested 30137 objects; 28844 rejected on bounding box; 1293 measured per-vertex
>> closest approach, camera_path    SPECX_Lib0664_stand_b7   -0.692 m of clearance   at (0.655, 0.109, 1.353)
>> closest approach, car_path       SPECX_Lib0853_turned_b0  -1.602 m of clearance   at (0.208, 0.0, 0.747)
>> closest approach, road_corridor  (nothing came near it)   measured, nothing close
>> 1202 PLACEMENT VIOLATIONS
>> STAGE RESULT: PLACEMENT_FAIL
```

`subject_meshes: 900, context_meshes: 29304`.

**Rule 2 of `split_subject_context` — "a `W_Item_*`/`ITEM_*` collection is the
thing under test, everything else is the test rig's furniture" — fired on the
assembled world**, because the item campaign's collections were merged into it.
Every barrier, fence, gantry and building the gate exists to guard was
reclassified as somebody's test furniture. Two consequences, and the second is
the serious one:

* `closest_approach_m` **excludes context by design**, so on the full circuit
  the gate reported `road_corridor: "measured, nothing close"`.
* findings from context go to `context_findings`, and the verdict is
  `PLACEMENT_CLEAN` whenever `violations` is empty. **A fence spanning the
  racing line would have been a context finding and a CLEAN verdict.** For 97 %
  of the shipping world this gate read the same whether the defect was present
  or not.

The file already names this danger — *"A gate that quietly narrows its subject
is R2-019 wearing a different hat"* — and then narrowed quietly, printing a
hint about `--subject` and carrying on.

**Fixed:** the item convention now applies only when the item collection's tree
is at least 50 % of the scene's meshes. A well-formed item scene scores ~100 %;
`assembly14` scores 3 % and falls through to rule 3 (every mesh, minus
stand-in-named collections) — which for a well-formed item scene gives the
identical answer anyway. Anything below the threshold is announced:

```
>> NOT an item test scene: the largest item collection 'ITEM_spectator_crowd'
   and its children hold 900 of 30204 meshes (3.0 %). The item convention would
   have made 29304 meshes 'context' and excused them from the verdict.
   Measuring the WHOLE scene instead; pass --subject if you really meant to
   narrow it.
```

Watched to fail — 2 item meshes among 18 world meshes:

```
>> SELFTEST: the item convention vs an assembled world
   PASS  an item collection holding 10 % of the scene does NOT narrow it      fires=0     expected=0     20 subject / 0 context
   PASS  CONTROL: and every world mesh is still in the subject                fires=True  expected=True  18 of 18 present
   PASS  CONTROL: the SHIPPED rule WOULD have excused the world as context    fires=True  expected=True  2 subject / 18 context under the shipped rule
```

#### 6d. 1,202 VIOLATIONS, AND THE TOP OF THE RANKING IS A 26-WAY PILE-UP

Even measuring only 3 % of the world, the shipping world is **not clean**:

```
violations by volume: {'car_path': 894, 'camera_path': 308}
name prefixes among violators: {'SPECX': 1202}
at_world of the worst: [0.052, -0.0, 0.119]
```

Every one is a `SPECX_Lib*` spectator-library prototype sitting **at the world
origin**, which is where the telemetry's station 0 is — so the car's swept
volume and the camera's clearance sphere both pass through the crowd library.
894 of them are in the car's path at up to 1.6025 m, which is the full swept
half-width, i.e. dead centre.

Whether those prototypes reach a frame is a question for whoever owns the crowd
build; whether the gate should have been saying so for seven assemblies is not.

**And this is where the tie-break lands.** The top of the `car_path` ranking is
not a measurement, it is a pile-up:

```
   car_path   1.6025 m  shared by  26 objects
   car_path   1.6024 m  shared by 143 objects
   car_path   1.6023 m  shared by 163 objects
   car_path   1.6022 m  shared by 140 objects
```

and the exact top-two margin the fixed report now prints is

```
 "car_path": {"winner": "SPECX_Lib0853_turned_b0",
              "runner_up": "SPECX_Lib0742_aisle_b0",
              "margin_m": 7.5e-07}
```

**0.75 micrometres**, against a declared instrument resolution of 10 mm — four
orders of magnitude inside the noise floor, with 26 objects sharing the value to
four decimal places. Being scrupulous: this is *not* an exact tie, so the
shipped first-wins rule happens to pick the same object as the fixed rule, and
no verdict on disk flips because of the tie-break. But "which object is closest
to the car" is, on the shipping world, a question this instrument cannot answer,
and the only reason anybody can see that now is that the report prints its own
margin.

#### 6e. THE SAME WORLD, BEFORE AND AFTER THE COVERAGE GUARD

Same blend, same frozen inputs, same hour:

```
BEFORE (item convention fired)
   subject/context: 900 / 29304
   total=1202 context_total=0 marginal=1
   camera_path    SPECX_Lib0664_stand_b7   -0.6919
   car_path       SPECX_Lib0853_turned_b0  -1.6025
   road_corridor  None -- "no subject mesh came within bounding-box reach of this volume -- measured, nothing close"
   determinism: IDENTICAL skipped 67

AFTER  (coverage guard)
   subject/context: 30204 / 0
   total=1202 context_total=0 marginal=1
   camera_path    SPECX_Lib0664_stand_b7   -0.6919
   car_path       SPECX_Lib0853_turned_b0  -1.6025
   road_corridor  ARCH_Gantry              +1.1491     (BR_Verge_R 0.7053 m behind)
   determinism: IDENTICAL skipped 67
```

**`road_corridor` went from blind to `ARCH_Gantry +1.1491 m`** — and that is the
same object and the same figure the last trustworthy report (`v122`, on
`assembly7`) recorded, so the corridor really has been clean all along and the
"nothing came near it" was purely the instrument. That is the good news. The
bad news is that "nothing came near it" and "1.15 m of clearance" are the two
readings this gate has been giving for the same world, and only one of them is
a measurement.

Violation count is unchanged at 1,202 because the other 29,304 meshes produce no
findings — the world minus the crowd library is clean. That is worth stating
positively: **the corridor, the barriers and the architecture pass. The crowd
library at the origin does not, and it is 894 objects deep in the car's path.**

### SUMMARY OF WHAT CHANGES WHAT SHIPS

1. **`assembly14.blend` — the shipping world — is `PLACEMENT_FAIL`, 1,202
   violations.** The verdict of record for the film is `PLACEMENT_CLEAN, 0
   violations`, from `assembly5`/`assembly6` on 2026-08-02, seven assemblies
   ago. No placement report existed for assembly8..14 before today.
2. **894 `SPECX_Lib*` crowd prototypes sit in the car's swept path at up to
   1.6025 m** (the full swept half-width) and 308 in the camera's clearance
   sphere, all at the world origin. Owner of the crowd build needs to say
   whether that library is meant to be in the shipped blend at all.
3. **A CLEAN placement verdict has been reachable with a fence across the
   racing line**, because the item convention made 97 % of the world "context".
   Closed.
4. **A CLEAN placement verdict has been issued with a −0.155 m car-path
   clearance in the same file** (`docs/placement_after_46.json`), because the
   edge-family courtesy applied to all three volumes. Closed.
5. Neither of the two determinism mechanisms has yet flipped a verdict on disk.
   Both are closed, and every future report now states its own reproducibility
   and its own margin instead of leaving both to be inferred.

---

### 6f. THE EXISTING BATTERY IS UNCHANGED BY ALL OF THIS

The three controls `v121/battery.sh` already runs, against the final gate
(sha `93af5324216fe2e9`):

```
ctl_place_pos          rc=1 -> >> STAGE RESULT: PLACEMENT_FAIL
ctl_place_neg          rc=0 -> >> STAGE RESULT: PLACEMENT_CLEAN
ctl_place_nearmiss_neg rc=0 -> >> STAGE RESULT: PLACEMENT_CLEAN

>> ctl_assert placement near-miss
   volumes actually MEASURED 3  camera_path +2.575 m, car_path +6.780 m, road_corridor +0.389 m
   tightest clearance       +0.3892 m on road_corridor (must be in [0.050, 1.500])
>> STAGE RESULT: CTL_ASSERT_OK
```

Same verdicts, same exit codes, same clearances as before. The only cost is
`--repeat 2` roughly doubling the measure phase.

---

### 7. HELD — I CANNOT COMMIT `tools/placement_gate.py`

`tools/placement_gate.py` is under a live lease held by **`r2-1761-debt`**,
8.2 h old at the time of claiming, together with `provenance.py`,
`report_repro.py`, `gitguard.py` and eight other paths. That is the agent that
worked the first half of #97 and closed the provenance side of it.

```
$ R2_AGENT=r2-2341-placement-determinism python3 tools/gitguard.py claim tools/placement_gate.py
  claimed 0 of 1 requested for r2-2341-placement-determinism; lease now holds 3 path(s)
  The 1 clashing path(s) are NOT yours and nothing was taken.
    tools/placement_gate.py -- ask r2-1761-debt to release it.  Do NOT set R2_AGENT=r2-1761-debt.
>> STAGE RESULT: FAIL (0 claimed, 1 clashes)
```

I have **not** released it and have **not** set `R2_AGENT` to that owner. The
file at `HEAD` was clean when I started (`git status` empty for it, last commit
`cc993bc`), so nothing uncommitted was clobbered by editing it in the working
tree — but the commit is held pending the lease.

Claimed and mine: `tools/placement_determinism_control.py`,
`tools/placement_entropy_probe.py`, `docs/STAGING-R2-2341-to-R2-2400.md`.

`tools/_r2341_gate_HEAD.py` is the pinned experiment copy and is **not** for
committing — it is `git show cc993bc:tools/placement_gate.py` and is
regenerated with that command.

### 8. FILES

| path | state |
|---|---|
| `tools/placement_gate.py` | **modified, UNCOMMITTED — lease held by `r2-1761-debt`** (sha `93af5324216fe2e9`) |
| `tools/placement_determinism_control.py` | new, leased by me |
| `tools/placement_entropy_probe.py` | new, leased by me |
| `docs/STAGING-R2-2341-to-R2-2400.md` | this file, leased by me |
| `work/r2-2341/frozen/` | the four frozen keep-out inputs |
| `work/r2-2341/runs/head/` | 6 baseline runs, pinned `HEAD` gate |
| `work/r2-2341/runs/fixed/` | 3 runs, fixed gate |
| `work/r2-2341/runs/a14/` | the shipping world, before and after the coverage guard |
| `work/r2-2341/runs/ctl/` | selftests, hash-seed sweep, both deliberate-failure controls |
| `work/r2-2341/{repeat.sh,analyse.py,kd_probe.py,make_edge_ctl.py}` | the harness |
| `work/r2-2341/ctl_edge_carpath.blend` | the one-object blend that HEAD calls CLEAN and the fix calls FAIL |

When the lease clears:

```
R2_AGENT=r2-2341-placement-determinism python3 tools/gitguard.py claim tools/placement_gate.py
git add tools/placement_gate.py tools/placement_determinism_control.py \
        tools/placement_entropy_probe.py docs/STAGING-R2-2341-to-R2-2400.md
```

(path-scoped, never `-A`.)
