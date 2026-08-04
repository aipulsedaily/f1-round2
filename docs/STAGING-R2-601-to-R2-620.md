# STAGING — R2-601 to R2-620

Block: **BREACH CONTINUITY** — tasks #32 and #117. Does the wound the car opens
in beat 3 survive the remaining 1,813 frames of a take with zero cuts.
Nothing here is written into `docs/DEFECT-LOG-R2.md`; that file has one owner.

---

## R2-601 — the wall does un-break, but not the half everybody has been measuring, and not for the reason the log names

Three claims were handed to me. Two of them are false and the third is true of a
file that has not been in the ship path since 08-03.

### The glass does not spring back, and the reading that says it does belongs to a superseded bake

R2-097 records *"at bond 4000 the pane bulges as a sheet and springs back —
483 mm at f866 and 17 mm by f900"*. That is a true statement about
`sim/tmp/breach_bake.npz` and a false one about everything downstream of it.
Measured with one instrument across every bake on disk (`persistence`, below):

| bake | bond | glass median end/peak | shards home again |
|---|---|---|---|
| `breach_bake` (**superseded**, the file R2-097 measured) | 4000 | **0.159** | **1,261 of 3,796** |
| `breach_full_m1` (**the shipped table**) | 100 | **0.9994** | 57 of 3,789 |
| `breach_full_r2281` | 100 | **1.0000** | 99 of 3,656 |
| `p_base` / `p_hfix` / `p_hsld` / `p_t17` / `p_t4` | 100 | **1.0000** | 51–136 of ~3,400 |

The config change to bond 100 did what R2-097 said it would. **The glass
half of the defect is closed and has been for a day.** The 50–130 shards that
do come home at bond 100 are gravel settling — a shard whose peak clears 10 mm
and lands back near its origin — and they do not move the median by a
thousandth.

### The aperture already persists across the entire tail, measured on the blend that renders

`sim/tail_persist.py` (new) reads `render/film14_breach_r6.blend` and measures
the connected aperture off the **F-curves**, never through `matrix_world` —
R2-188, and 3,796 of these objects are hidden for the first 859 frames.

```
frame     visible     gone   WOUND m2      w x h    CONTROL m2
1               0        0      0.000   0.00x0.00      0.0000
859             0        0      0.000   0.00x0.00      0.0000
860          3796      391      0.145   0.30x0.75      0.0000
900          3796     2767     11.658   2.15x6.00      0.0000
1165         3796     2962     12.482   2.15x6.00      0.0000
1166         3796     2962     12.482   2.15x6.00      0.0000
2978         3796     2962     12.482   2.15x6.00      0.0000
```

**2.15 × 6.00 m, 12.482 m², identical at f1165 and at f2978.** And not by
sampling: the tail is covered by proof, not by probe. Every F-curve on all
3,845 BREACH objects has its last key at f1165, extrapolates CONSTANT, and
carries no F-curve modifier; no BREACH object has a parent, a constraint, a
driver, a modifier or a delta transform. Given that, the pose at **all 1,813**
frames in f1166..f2978 is identically the pose at f1165. The five probes past
f1165 are a spot-check of the proof, not the proof.

**The controls, and why the number is not vacuous:**

| control | reads | what it kills |
|---|---|---|
| **NEG-2, the free negative control** — the same instrument, same scene, same frames, on the bays the plan never breaks (0/1/8/9, `intact`) | **0.0000 m²** at every frame, f1 to f2978 | an instrument that reports a hole wherever there is glass. The wound half reads 12.482 m² against it |
| **POS** — the wound bays *before* the swap frame | **0.0000 m²** at f1, f400, f859 | an instrument measuring the mesh instead of the motion |
| **NEG-1** — "no keys after f1165", asked of objects that are *not* the breach | **10 of 626** animated non-breach objects key past f1165 | a tail-static test that passes because nothing in the scene is keyed that late. If this arm found zero, stage A would be measuring nothing |

### What actually un-breaks is the aluminium, and every report in the pipeline is blind to it by construction

`apply_breach.build_frame` reports `max_travel_m`. `breach_metrics` reports
`mullion_max_disp_m`, `transom_max_disp_m`, `bent_3_m`, `bent_7_m`. R2-267's
table is max travel. **All of them are maxima.** A member that deflects 303 mm
and springs back to 0 mm and a member that deflects 303 mm and stays there
print the *same number* in every one of them.

**A printed peak looks exactly like a persisted peak** — the same shape as
R2-266, where a printed count looked exactly like a used count.

Read off the shipping blend's own curves:

| piece | peak | end | end/peak |
|---|---|---|---|
| `BF_MUL05_S01` | 4.7421 | 4.4311 | 0.9344 |
| `BF_MUL05_S00` | 3.9318 | 3.9318 | 1.0000 |
| **`BF_MUL05_S02`** | **0.1449** | **0.0007** | **0.0048** |
| **`BF_MUL05_S03`** | **0.1119** | **0.0005** | **0.0042** |
| **`BF_TRN0_b05`** | **0.0892** | **0.0004** | **0.0048** |
| **`BF_TRN0_b04`** | **0.0859** | **0.0004** | **0.0052** |
| **`BF_MUL05_S04`** | **0.0826** | **0.0003** | **0.0034** |

**30 of the 32 deflected east-frame pieces in `film14_breach_r6.blend` return to
home.** Mullion 5's six surviving segments and all twelve released transom
pieces bend as the car goes through and are perfectly straight again by f1165 —
and then hold that repaired pose for the remaining 1,813 frames. R2-267 said
"mullion 5 travelling 4.43 m and shedding two segments" and it was true; what it
could not say, because it printed a max, is that everything else *came back*.

---

## R2-602 — the lever is the TRANSOM threshold, and it is not the head restraint the log named

R2-268 calls the head restraint *"the one parameter that decides whether the
aperture reads"* and R2-282 made `--head-restraint slider` the default on the
strength of it. **Measured against a single-variable control, the head
restraint barely moves the defect and the transom threshold decides it
outright.** Five pilot bakes already on disk in `sim/tmp`, all 4,048 bodies,
14,075 constraints, 8 substeps, 24 iterations, one variable apart:

| bake | head | transom | frame bodies deflected | **came home** | largest recovery | verdict |
|---|---|---|---|---|---|---|
| `p_base` | fixed | 260 | 68 | **64 (94.1 %)** | 0.3028 m | FAIL |
| `p_hsld` | **slider** | 260 | 70 | **60 (85.7 %)** | 0.2961 m | **FAIL** |
| `p_hfix` | fixed | **8.8** | 46 | **2 (4.3 %)** | 0.0192 m | **PASS** |
| `p_t17` | slider | 17.6 | 52 | 24 (46.2 %) | — | — |
| `p_t4` | slider | 4.4 | 45 | 8 (17.8 %) | — | — |

* **head fixed → slider, transom held at 260: 94.1 % → 85.7 %.** The named
  lever, moved on its own, leaves the defect standing.
* **transom 260 → 8.8, head held at fixed: 94.1 % → 4.3 %.** The unnamed one,
  moved on its own, closes it.
* and it is monotone in the transom threshold at fixed head restraint:
  260 → 17.6 → 4.4 gives 85.7 % → 46.2 % → 17.8 %.

Mullion 5's own column, same two bakes, head restraint identical in both:

```
                p_base (transom 260)          p_hfix (transom 8.8)
                peak     end   end/peak       peak      end   end/peak
MUL05_S00      8.102   8.102     1.000      15.468   15.468     1.000
MUL05_S01      7.697   7.697     1.000      15.616   15.616     1.000
MUL05_S02      0.303   0.000     0.001      15.907   15.907     1.000
MUL05_S03      0.254   0.000     0.001       7.607    7.607     1.000
MUL05_S04      0.205   0.000     0.002       7.173    7.173     1.000
MUL05_S05      0.151   0.000     0.002       6.856    6.856     1.000
MUL05_S06      0.096   0.000     0.003       6.671    6.671     1.000
MUL05_S07      0.066   0.000     0.003       6.629    6.629     1.000
```

**The mechanism.** `t_transom = 260` is 499 kN across two M6 self-tappers — the
source's own note says so, and `sim/frame_thresholds.py` derives 8.8. At 260 the
three full-width transom rails never break their bolt to mullions 4/5/6, so bays
3–6 stay welded into one rigid ladder that terminates on members which do not
release. A Bullet `FIXED` rigid-body constraint is a *position* constraint: it
holds a rest relative transform, and any deflection is constraint error the
solver drives to zero. That is the restoring spring. It is the brief's
"pin/anchor group that was never released on fracture" — right in kind, wrong in
station.

**Ruled out, each with evidence rather than by elimination:**

* **solver stiffness / damping.** Identical in all five pilots (`substeps` 8,
  `solver_iterations` 24, `DAMP_LIN`/`DAMP_ANG` untouched) while the outcome
  swings 94 % → 4 %. And damping removes energy; it cannot define a pose to
  return to.
* **the PVB springs** (`_pvb_post`, the only literal springs in the bake:
  `spring_stiffness 55`, equilibrium at the intact rest offset). They join
  **glass to glass only**, and the glass median end/peak is 0.999–1.000 in every
  bond-100 bake. If the springs were driving anything home, the glass would be
  the first thing to go.
* **a shape key or modifier still driving toward the intact rest state.** None
  exists — not in the bake, and stage A of `tail_persist` finds zero modifiers,
  zero drivers and zero constraints on all 3,845 BREACH objects in the delivered
  scene.
* **the fracture never severing connectivity.** 2,962 shards are more than
  0.25 m from home at f1165 and 2,960 of them are still there at f2978.

---

## R2-603 — the fix, and the blocker it lands on

**In source:**

1. `sim/breach_metrics.py` — new `persistence()`. Peak, end and **end/peak** for
   every body, aluminium and glass reported separately, with its own three
   controls (`POS` a synthetic body out 1 m and back must be flagged; `NEG` one
   out 1 m that stays must not be; `ZERO` a bit-identical body is neither
   deflected nor recovered). Every future bake is now scored on whether
   anything came back.
2. `sim/land_breach.sh` — new **stage 3b**, which refuses. Stage 3 has never
   gated on anything: it pipes `slabcheck` through `tail -3` and the script
   carries on whatever it says, and slabcheck asks the question of the *glass*,
   which is the half that has not failed since bond went to 100. 3b asks it of
   the aluminium and calls `die` on a FAIL. Stage 4's duplicate
   `breach_metrics` run is removed — it was scoring a 152 MB table twice.
3. `sim/tail_persist.py` — new. The persistence question asked of the **blend
   that renders**, over the whole remaining take, with the three controls above.
   It imports its rule and its gate from `breach_metrics` rather than restating
   them; a second copy of a threshold is the mechanism behind R2-071, R2-061 and
   R2-100.

**The gate is on the size of the largest recovery, not on the count.** A count
of zero cannot be asked for and should not be — a mullion that is still bolted
in is *supposed* to flex a few millimetres and come back, and every bake on disk
has a handful of sub-20 mm ones on the neighbouring members. What is a defect is
a recovery you can see. **25 mm is 4.7 px at the beat-3 pass's own measured near
scale of 5.3 mm/px** (f945, 5.9 m). The glass arm gates on the field median
(0.90) for the same reason: 57 shards of 3,789 settling is not a pane
un-breaking.

Verdicts, one instrument, every artefact:

| artefact | head | transom | largest recovery | glass median | verdict |
|---|---|---|---|---|---|
| `breach_bake` (superseded) | fixed | 260 | 0.4892 m | **0.159** | **FAIL both arms** |
| `breach_full_m1` → **`film14_breach_r6.blend`, the ship candidate** | fixed | 260 | **0.1571 m** | 0.9994 | **FAIL** |
| `p_base` | fixed | 260 | 0.3028 m | 1.0000 | FAIL |
| `p_hsld` | slider | 260 | 0.2961 m | 1.0000 | FAIL |
| `p_hfix` | fixed | **8.8** | **0.0192 m** | 1.0000 | **PASS** |
| `breach_full_r2281` | slider | **8.8** | **0.0195 m** | 1.0000 | **PASS** |
| `film14_breach_R2387.blend` (applied) | slider | 8.8 | **0.0271 m** | — | **FAIL by 2.1 mm** |

Read off the two applied scenes rather than the tables, which is what actually
renders:

| | `film14_breach_r6` | `film14_breach_R2387` |
|---|---|---|
| aperture at f1165 = f2978 | **12.482 m², 2.15 × 6.00 m** | **12.895 m², 2.15 × 6.00 m** |
| intact-bay control | 0.0000 m² | 0.0000 m² |
| tail-static over f1166–2978 | PASS (1,813 frames) | PASS (1,813 frames) |
| deflected frame pieces that came home | **30 of 32 (93.8 %)** | **6 of 20 (30.0 %)** |
| largest recovery | **0.1449 m** | **0.0271 m** |

**The correction is real and it is 5.3×.** R2387 still misses the gate, by
2.1 mm, and the number is reported as it fell rather than the gate being moved
to meet it — the gate was fixed off the pixel scale before R2387 was measured.

**And here is the blocker.** Every configuration that stops the aluminium
springing back is a configuration in which mullion 5's column *leaves*, and in
every one of them it leaves at a speed nothing in this sim can take back:
`p_hfix` 15.9 m in 1.67 s, `breach_full_r2281` **89.79 m**, `film14_breach_R2387`
**55.35 m**. That is `MUL05_S02` in the brief, and it is the kinematic car
proxy — infinite mass, cannot lose momentum to 2,240.9 kg of glass. **The
transom fix and the car-proxy fix are not independent: the transom threshold is
what releases the ladder, and the car proxy is what decides where it goes.**
That fix has another owner and is not duplicated here. Until it lands there is
no bake that passes both arms, and `film14_breach_r6.blend` remains the ship
candidate with a known, now-measured, 145 mm un-bend on `MUL05_S02`.

`render/film14_breach_r6b.blend` is still not shippable for exactly that reason,
and `film9` / `film10` are untouched — film10's 27-finding audit FAIL is what
makes every other PASS non-vacuous.

**Cost of this block: $0.00.** Nothing was queued. The whole result is
geometric, read off tables and F-curves that already existed; the farm's ladder
pass was not interrupted.

---

## R2-604 — `apply_breach`'s R5 asks the pocket question at one frame and skips the only objects that could answer it

Not fixed here; recorded because it is the hole that a persistence bug would
fall through next time. `preflight()`'s R5 — the check that nothing stands in
the glazing pocket — runs `_world_aabb` / `_world_verts` at whatever frame the
applier happens to be on (f1, before the breach), and its very first filter is

```python
if o.name.startswith(("GP_b", "GS_b")):
    continue
```

so it skips every pane and every shard: the only objects in the scene whose
visibility and position change over the take. R5 is a *build-time foreign-object*
check and it is a good one — it is what caught eleven aluminium bars lying
through the glass — but it cannot see a wound that closes, and it has been read
as though it could. `tail_persist.py` is the arm that asks the question across
frames.

---

## R2-605 — a wrong result that matches the expected value is nearly undetectable, and the defence is a second path rather than a second reader

I reported the wound as **2.15 × 6.00 m, 12.482 m²**. It is **4.35 × 6.00 m,
24.800 m²**. The cause, in my own module:

```python
mi, sj = int(nm[3:5]), int(nm[nm.index("_S") + 2:][:2])
except (ValueError, IndexError):
    continue
```

The applied pieces are named `BF_MUL05_S02`, not `MUL05_S02`. `nm[3:5]` is
`"MU"`, `int()` raises, the bare `except` swallows it, and **`gone_mullions` was
empty on every frame** — so the mullion strips were treated as opaque and the
connected hole collapsed to a single bay. This is the `assemble.py` hazard the
brief warns about — a swallowed exception yielding a plausible result —
committed inside the module written to catch that class of defect.

**And it survived my own reading of it because it produced the number everybody
expected.** 2.15 × 6.00 m is what `part2.md`, this log and the task list all
say. The check a careful reader runs — *does this look right?* — returned yes.
That is the general result, and it is worth stating next to R2-433: **agreement
with a document is not verification, because a broken instrument that reproduces
the documented value is indistinguishable from a working one by inspection.**

The defence is an **independent path to the same number**. The table trace
(`np.interp` over `breach_film.npz`, no Blender) and the blend readback
(F-curves out of the 4.99 GB scene) now agree at 4.35 × 6.00 m and 24.800 m²,
computed from different data by different code. That agreement is evidence; the
earlier agreement with `part2.md` was not.

---

## R2-606 — the film's aperture has two correct values and the pipeline has always quoted the narrower one

Not a stale declaration, and **not an over-opening sim**. `sim/aperture.py`
returns both from one call, and its own docstring says quoting one without the
mullion state is a known error. On the shipped bake:

| measure | reading |
|---|---|
| `hole` — mullion strips **opaque** | **2.150 × 6.000 m, 12.895 m²** |
| `hole_bridged` — strips passable **only where that segment left** | **4.350 × 6.050 m, 25.380 m²** |

`sim/land_breach.sh:127` prints `a['hole_w_m']` — the strips-opaque one —
labelled `connected %.2f x %.2f m`. That is where 2.15 × 6.00 entered the
documents.

**The sim is at half its authored ceiling, not over it.** `aperture.CEILING`
records that the plan permits bays 3–6, which is **8.77 m** of glass. Delivered:

| bay | role | vacated |
|---|---|---|
| 2 | retained | 5.0 % |
| 3 | destroyed | **0.5 %** |
| 4 | destroyed | **96.8 %** |
| 5 | destroyed | **100.0 %** |
| 6 | destroyed | **2.2 %** |
| 7 | retained | 2.9 % |

`segments_gone: [5]` — one mullion, and only two of its eight segments.

**And the opening is not a doorway twice the car's width.** Mullion 5's segments
are 0.753 m each; only `S00` (z 0.086–0.840) and `S01` (0.840–1.593) leave. The
two bays are joined **through a 1.51 m-tall gap at the bottom**: 4.35 m wide at
car height, **2.15 m wide above z = 1.593**, where `S02`–`S07` still stand. The
aperture's shape and R2-601's un-bend are the same six objects — what keeps the
opening narrow at the top is exactly what springs back.

**Both numbers should be quoted with the mullion state.** No document was
edited; this is recorded for whoever owns them.

---

## R2-607 — every arm was asked whether it can pass on an empty set, and the free negative control could

R2-433's law applied to this block's own work: fixing the instance is not fixing
the defect. Stage E was found passing on `BREACH_Frame: 0` — "0 of 0 deflected
pieces came home". Asking the same question of the other arms found two more,
and **the worst of them is the one the whole deliverable rests on**:

* **`D`, the free negative control**, passes when a plan has no `intact` bays:
  `grid_i is None`, the control array stays zero, and D reports PASS **having
  measured nothing**. A negative control that can pass on an empty set is not a
  control; it is a decoration that reads like one.
* **`A`** passes on a scene whose BREACH collections exist but are empty — "no
  keys after `span_end`" is trivially true of nothing.
* **`POS`** carries no information when the wound never opens.
* `C` fails rather than passes on an empty set; `NEG-1` has no vacuous mode —
  it *is* the anti-vacuity arm.

A vacuity flag is **not** a pass/fail clause. Each arm still answers only its
own question — which is why `MAG` had to be split out of `D` and `POS` — and the
flag says separately whether that verdict carries information. **An arm that
passes while vacuous is listed and the run refused.**

This fired unprompted on `film9_breach`, flagging `E` VACUOUS and `POS` as an
empty-set pass.

---

## R2-608 — stage C sampled, which is the defect it exists to catch, and `film9_breach` is the proof

The first cut of `tail_persist` compared the tail against `span_end` and probed
five frames between. It **passed `film9_breach`**. Swept on every frame:

```
film9_breach   peak 7.863 m2 at f878   ->   0.000 m2 at f913   ->   0.432 m2 held
```

**The wound opens to 7.86 m², closes completely — 0.000 m² — and re-opens at a
twentieth of its size.** Neither the true peak (f878) nor the true minimum
(f913) was among any of the twelve probe frames: the old check had the wrong
numerator *and* the wrong denominator. This is the same shape as a local-median
detector seeing only the first tooth of a periodic defect — **a probe placed by
convenience rather than by the defect's own geometry.**

C now gates on *once open, never smaller*: peak over the take, then the minimum
from the peak frame to the last frame, and the frame it lands on.

**Affording it without restoring the defect.** `_largest_component` is a Python
flood fill and 2 × 2,978 of them do not finish. The fix is not to sample again:
`aperture.hole` is a pure function of `(gone_ids, gone_mullions)` — it never
sees the frame number — so memoising on exactly those arguments is **exact, not
approximate**, and the 1,813 tail frames collapse to one evaluation because the
set is *provably* constant there. Every frame is still evaluated. The report
carries `C_distinct_gone_sets_evaluated` (290 on `film9_breach`) so the cost of
the claim is visible.

**And `film9_breach` is the control that must fail.** It was applied from
`sim/tmp/breach_bake.npz` — bond 4000, 11:24 on 08-03, before `breach_full_m1`
at 22:28. R2-601 measured that table at glass median end/peak **0.159** with
1,261 of 3,796 shards home again; the blend built from it shows the wound
closing on camera. **The falsification and the confirmation are one
measurement:** the spring-back is real, is exactly where the table said, and is
preserved in a delivered scene while absent from the ship candidate. A gate
whose control must fail is worth more than one with two that pass — the whole
audit chain already rests on `film10` failing with 27 findings.

### The two verdicts, arm by arm

| arm | `film14_breach_r6` | `film9_breach` |
|---|---|---|
| **A** tail-static | PASS — 1,813 frames | PASS |
| **NEG-1** must-fire control | PASS — 10 of 626 | PASS — 10 of 626 |
| **C** once open, never smaller | **PASS — 100.0 %** (peak 24.800 m² f940) | **FAIL — 0.0 %** (7.863 m² f878 → **0.000 m² f913**) |
| **D** free negative control | PASS — 0.000000 m² | PASS — 0.000000 m² |
| **POS** motion not mesh | PASS | PASS but **VACUOUS** |
| **MAG** | PASS — 24.800 m² | **FAIL** — 0.433 m² |
| **E** aluminium | **FAIL** — 30 of 32, largest 0.1449 m | **VACUOUS** — `BREACH_Frame: 0` |

**Six arms pass on the ship candidate, none vacuously, and one fails.** The
glass wound is clean across the entire take; the aluminium is the whole of the
remaining defect.

---

## R2-609 — the un-bend cannot be measured by a temporal pair, and the numbers say so before any pixel is spent

`MUL05_S02` peaks at **145 mm at f861**, is under 10 % of that by **f866** and
home by **f870** — the un-bend is **nine film frames**, with a 28 mm secondary
bounce at f880. The obvious experiment is to diff f861 against f870. Projected
through the camera track's own pose and its 28.3 mm lens:

| | |
|---|---|
| camera-induced shift of a **static** point, f861 → f870 | **1,478.9 px** |
| the member's own 145 mm deflection at f861 | **41.1 px** |

**A temporal diff is 97 % camera.** The only design that isolates the member is
the same frame from two scenes with one variable between them, which is what
`sim/unbend_ab.py` builds: the 30 recovering pieces pinned to their f861 pose
for the whole take, with `BF_MUL05_S00` and `BF_MUL05_S01` — the two that
genuinely leave — **deliberately left alone**, so only one variable moves.

At **f870**, where A shows the wall repaired and B shows it still bent, the
pinned pieces that are actually in frame shift:

| piece | on-screen shift at f870 |
|---|---|
| `MUL05_S02` | **71.5 px** |
| `TRN_z0_b05` | 46.8 px |
| `TRN_z0_b04` | 38.8 px |

Larger than the 41.1 px at f861 because the camera is closer by then. The
subject is **opaque aluminium**, so this measurement does not inherit the
glass-against-glass readability degeneracy that weakens breach A/Bs taken off
the ladder pass.

---

### Files

* `sim/tail_persist.py` — new
* `sim/breach_metrics.py` — `persistence()`, `DEFLECT_M`, `RETURN_FRAC`,
  `RECOVERY_GATE_M`, `GLASS_MEDIAN_FLOOR`
* `sim/land_breach.sh` — stage 3b; stage 4's duplicate scoring run removed
* `sim/out/tail_persist_r6.json`, `sim/out/tail_persist_R2387.json` — the
  measurement records
