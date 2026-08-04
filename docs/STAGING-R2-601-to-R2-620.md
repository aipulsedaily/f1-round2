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

### Files

* `sim/tail_persist.py` — new
* `sim/breach_metrics.py` — `persistence()`, `DEFLECT_M`, `RETURN_FRAC`,
  `RECOVERY_GATE_M`, `GLASS_MEDIAN_FLOOR`
* `sim/land_breach.sh` — stage 3b; stage 4's duplicate scoring run removed
* `sim/out/tail_persist_r6.json`, `sim/out/tail_persist_R2387.json` — the
  measurement records
