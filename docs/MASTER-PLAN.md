# CIRCUIT VITRINE — master plan and layout

**The one document to read first.** Written 2026-07-30 so the plan survives context
loss. If anything here contradicts an older doc, this wins.

The deliverable: **one continuous 4K camera take, 2,978 frames (124 s), zero cuts** —
showroom assembly, ignition, glass breach, transit, a flying lap, closing wide.
Everything procedural, built by hand. No downloaded models, HDRIs, photo textures or
AI-generated anything, ever.

---

## 1. THE SITUATION

### UPDATE — CONTRACT **1.2.0**. Read this before the rebuild (#53).

Three defects batched into one contract revision, because the assembly is a
4.19 GB remote job and a contract change moves no vertex until it is rebuilt.
Full detail in DEFECT-LOG-R2 **R2-042 / R2-043 / R2-044** and the
`v1.2.0 — WHAT MOVED` table beside them; selftest is **149 checks, all passing**.

- **R2-035 is CLOSED.** `owned_edge` is promoted into the contract and
  `barrier_offset` is clamped by it. The 14 700-station sweep goes **406 (2.76 %,
  worst 7.493 m) → 0**, both sides, against a positive and a negative control.
  `build_barriers` S4b's clamp now activates on **0.00 %** and the two lines are
  bit-identical, so **no barrier mesh moves**; its divergence warning is withdrawn.
- **`access_route_point` and `telemetry.csv` are two different curves, 9.044 m
  apart** (R150 arc vs its own chord). Every keep-out was derived from the ribbon
  while the placement gate measures the telemetry — that is the real cause of the
  `ARCH_PitWall` / `ARCH_RetainEdge` violations, and v1.1.1 cleared them by 1.70 m
  of luck. `transit_keepout` is the union of both curves now. ~~**Which curve is
  right is still open**~~ **CLOSED 2026-08-02 — see the next bullet.**
- **R2-045: THE ARC WON, AND telemetry.csv IS REBUILT.**
  `docs/R2-042-DECISION.md` decided it and `tools/build_telemetry.py` now
  evaluates the transit analytically off `world_contract.access_route_arrays`.
  Transit x/y move up to **9.0407 m**; `t_s`, `s_m`, `speed_ms`, `wheel_rot_rad`
  and every lap frame are **bit-identical**, so no clock and no beat boundary
  moves. Contract selftest **[18] is inverted** and still 149 checks / 0 failed;
  gate is `tools/transit_line_gate.py` with the pre-fix file kept as its positive
  control at `telemetry/pre_R2042.csv`. Camera re-authored (beats 2, 3, 5
  bit-identical; beat 4 29 → 30 keys; beat-1 aim and the beat-1/2 seam untouched).
  **FOR THE REBUILD:** `build_barriers` S21's car-envelope flare is now provably a
  **no-op (+3.347 m → 0.000 m)** and its own note says to delete it — until that
  happens the Beat-4 corridor's north wall is built up to **3.35 m outboard of the
  contract's declared +8.000** over 32.4 m of the shot the camera flies.
- **What the rebuild has to redo:** the LEFT barrier line and the ground that
  follows it over s 661–884 and 1081–1213 (`barrier_offset` −44.598 m … 0.000,
  rms 8.110), `platform_edge` −2.460 … 0.000 (rms 0.671) over the same span, and
  `corridor_rim` with it (2.460 m horizontal, 39 mm in z). `PIT_WALL_S0` does not
  move. `ground_z`, `half_width`, `access_*`, every light and every tolerance are
  bit-identical to 1.1.1. Side −1 is untouched, every function, every station.

### UPDATE 2026-08-02 (late) — FIVE BLOCKERS CLEARED. Read this first.

**#34 camera** — 24 keys became **479**, all six beats carrying location AND rotation.
An AIM GATE now measures, every frame, the angle from the camera's -Z to that beat's
declared subject, and asserts every beat has keys. Tested against the sheet with beats
2-5 removed: fails at 147 deg with the subject behind the camera on 683 frames.

**#57 softness** — NOT the denoiser. With it off at 8x samples the sky moved 5.617 ->
5.595 (0.4 %), which means that figure is the measurement's own NOISE FLOOR. The
subject genuinely lacks detail. No previously rejected work needs re-judging on
render-path grounds.

**#58 sun** — the lighting was never the defect. 100 % of 60 sampled spectators are
sun-blocked BY EACH OTHER; a packed grandstand at 12.5 deg self-shades. Two modules
still create no sun, and `procedural_world()` silently supplies none.

**#59 + #63 gate** — rewritten (468 -> 2,360 lines), renders its own witness frame with
a sphere, plane and six-step grey wedge as brightness-matched controls. **28/28 accepted
became 7/28.** The relief check that carries 21 of those verdicts was VALIDATED against
a physical ladder: monotonic across 0/0.5/2/8 mm ribs, and painted stripes with zero
geometry score inside the margin of a flat plate.

**#51 contract 1.1.0** — `barrier_offset` 51.99 -> **1.95 m/m**, datum closure
6.746 mm -> **0.000e+00**, selftest 74 -> 114 checks. My root cause was half right: only
two of seven steps were the pit masks; the rest came from `maxoff` writing a `1e6`
sentinel and then BOX-FILTERING it.

**#62 harness** — `world/itemkit.py`, `tools/campaign_preflight.py`, a worked reference
item, and section 4 of the campaign brief rewritten for the eight checks.

### THE SHIPPING WORLD IS `assembly6.blend`, contract 1.2.1

**`render/world/assembly/r2/assembly6.blend`** — contract **1.2.1**, 4018.9 MB, 28,781
objects. **`assembly5.blend` MUST NOT BE RENDERED FROM.** See `SHIPPING.md` in that
directory; the A/B copy is deliberately renamed
`verify_world_a5_SUPERSEDED_ab_reference.blend` so nobody picks it up by accident.
`assembly2.blend` (1.0.1) is a baseline, not a subject. **#91** (the HERO/MID/BULK
tiering) and `tools/build_and_dump_points.py` still measure it.

Evidence: `v120/` for the assembly5 battery, `v121/` for this one.

**WHY assembly5 WAS WRONG, AND WHY THE SUMMARY COMPARISON MISSED IT.**
`assembly5` was built at **12:43**. `telemetry.csv` was corrected at **13:54**. The
shipping world was built **71 minutes before the fix it was believed to be built
against.** `build_barriers` §21 read the telemetry to compute a correction; against the
old chord CSV it pushed the Beat-4 north wall **+3.347 m** outboard over 32.4 m.

§21 was **already inert** against the corrected CSV — it was never "still pushing". The
harm lived entirely in the **artefact**, not the code path. Deleting §21 was still right
(it removed a latent trap: `_car_envelope`'s route filter admitted lap rows near the
start/finish, giving a −11.83 m right-side envelope even under corrected telemetry, which
never bit only because the south wall stops at t 90). But the **rebuild** was the fix.

> **Every module summary in `assembly6` is bit-identical to `assembly5` — object counts,
> triangle counts, areas, all of it. And one object moved 3.19 m.** The per-object vertex
> fingerprint over 1,282,465,803 verts finds exactly **1 of 28,781** objects changed:
> `BR_Transit_NorthWall`, bbox_max `[106.858, 18.024, 2.56] → [107.877, 14.835, 2.56]`,
> vertex **count unchanged** at 1573.
>
> **A summary that does not change is not evidence that geometry did not move.** Name the
> quantity you compared. This is the second time this exact substitution has been made on
> this project and the first time it shipped.

Confirmed three independent ways: the module's own report, the vertex fingerprint, and a
**picture** — 18.3 % of beat-4 frame 1081 differs between the two worlds, and the
differing pixels are *exactly* the north wall and its cast shadow, everything else
pixel-identical. With the contract's declared lines projected into frame, `assembly6`'s
+8.000 wall-top lands on the built coping; in `assembly5` the same lines run over **empty
apron with no wall under them**.

**It built LOCALLY in 1004 s**, peak RSS 8.3 GB against 11 GB RAM. The long-standing note
that the rebuild "cannot run locally" was wrong and cost an agent an argument: that claim
is about **pushing** the finished 4.19 GB blend over the wire, not about **building** it.

What the rebuild proved:

- barrier verts and tris **bit-identical** to 1.1.1 — no barrier mesh moved, as the
  contract predicted analytically
- both car-path violations gone; `ARCH_RetainEdge` −0.155 → **+0.359 m**
- last vegetation instance on gravel **1 → 0**; unbuilt corridor void 52.0 → **4.0 m²**;
  apron sweep max 295.4 → **13.0 mm**
- **#48's 3,390 black pixels → 0** at delivery resolution
- ~~**R2-042 needs no second rebuild**~~ — **THIS WAS TOO STRONG. The barriers DO need
  rebuilding, and the shipping world is wrong until they are.** The rebuild agent measured
  *bit-identical summaries* from `build_surface` and `build_barriers` against the corrected
  telemetry. **Summaries are counts and totals; vertex positions can move while counts do
  not.** `build_barriers` §21 carries a correction table that existed only to compensate for
  the telemetry/ribbon disagreement. Now that they agree, applying it is not merely
  redundant — it **pushes the Beat-4 corridor's north wall up to 3.347 m outboard** of the
  contract's declared +8.000, over 32.4 m, **in the shot the camera flies at 200 km/h**.
  Delete §21, rebuild the barriers, re-gate. Tracked as its own task.
  *The lesson is the general one: a summary that does not change is not evidence that
  geometry did not move. Name the quantity you compared.*

Two *apparent* regressions were attributed rather than reported, by re-running the probes
against the intermediate assembly: both came from contract **1.1.1**, not the rebuild.
**Do that attribution step before logging a regression.**

### THE SEQUENCING RULE, twice validated — FOUNDATION BEFORE MULTIPLICATION

This is the reasoning that has governed the last two decisions and should govern the next.

**A change to a shared foundation moves nothing until the thing built on it is rebuilt.**
So fix the foundation *first*, once, or pay for the rebuild twice.

It held for the contract: #46 and #68 both said, in their own text, that the fix belonged
in `world_contract.py`, and #68's verify step demanded a *rebuilt* assembly. Contract
1.2.0 landed first; the rebuild then ran once and clean.

It holds now for **wave 2 (#52), which is deliberately BLOCKED** on four items — because
each would otherwise be multiplied across ~407 items:

| | why it must land first |
|---|---|
| **#88** | `placement_gate`'s road corridor is an **absolute z band**; it tests empty air over **28 % of the lap**, and it guards every item placement |
| **#85** | humankit had **54 of 318 pieces inside-out**, rendering with every bump inverted while passing every check. Mirrored geometry has reversed winding *by construction*, and the same idioms run through itemkit |
| **#86** | the relief-amplitude law. **Three** amplitude sets were rendered and rejected before anyone reasoned in radiance rather than millimetres |
| **#91** | the tiering wave 2 is *scoped from* still measures the 1.0.1 world |

The same rule blocked the 7,800-spectator crowd (#41) behind the humankit garment fix:
build the crowd on a defective `garment_from_sweep` and 7,800 figures inherit it.

### The earlier 2026-08-02 note, kept for the record

Beats 2-5 are authored: **413 keys from 40 choreography anchors**, generated by
`tools/author_beats2_5.py`, in `docs/beat_sheet.json` as `beat2`..`beat5`.
`anim/build_camera_rig.py` now carries an **AIM GATE** (angle from the camera's
-Z to each beat's declared subject, every frame, plus where that subject lands
in the frame) and asserts every beat has both location AND rotation keys. The
gate was tested against the artefact already known to be bad — the sheet with
beats 2-5 removed — and fails it at 147 deg with the subject behind the camera
on 683 frames.

Measured on the rebuilt rig: worst position jump **4.247 m/frame** (limit 12),
worst rotation step **19.05 deg/frame** (limit 45), worst aim **2.52 deg**
(beat 5), **16.87 deg** (beat 2), **10.25 deg** (beat 4), **7.79 deg** (beat 3),
**0.08 deg** (beat 6) — all inside their stated bounds. Camera-to-car never
closer than 1.808 m. Peak camera speed 101.7 m/s, peak 6.31 g.

Eight defects were found on the way and are logged: **R2-029** (beat 1 flies
through the assembled car and looks at the glass wall — 48.9 deg, confirmed by
a rendered frame; the ONLY beat still failing the aim gate, and it is not #34's
to fix), **R2-022** (the beat-3 ramp integrated to 3.73 s of world time against
a declared 1.6), **R2-023** (beat 6 offset +3.0 s, and no rotation at all),
**R2-024** (a top-down camera barrel-rolling at 36.9 deg/frame while the aim
read 0.00), **R2-025** (the placement gate swept the camera at its keys, not
along its path), **R2-026** (telemetry x and s_m disagree by 25 % through the
launch), **R2-027** (the exposure ramp keyed absolute, 3.6 stops over the
assembled world's calibration, found by looking at a rendered frame) and
**R2-028** (beat 6's declared peel-off geometry frames a 2.25 x 1.27 m patch of
a 5.698 m car — declared values, not fixed here).

The film-time -> world-time mapping now lives in **`anim/filmtime.py`** and is
imported by both the authoring tool and the rig build. Anything that samples the
telemetry per frame must walk it: beat 3's ramp offsets the two clocks by 6.4 s
permanently.

---

### The situation as of 2026-07-30, kept for the record

The world is built and composes. **The film is not started.** Between those two facts
sits one discovery that reorders everything:

> **Beats 2, 3, 4 and 5 have no camera.**

`beat_sheet.json` holds camera keys for `beat1` (16) and `beat6` (8) only — 24 keys for
2,978 frames. `build_camera_rig.py:142-146` reads those two blocks and nothing else.
Over the 1,960-frame gap (754→2714) the camera drifts a 123 m near-straight chord at
1.5 m/s with its **orientation frozen**, while the car is a median **612 m** away.

The continuity gate passed it `CAMERA_RIG_CONTINUOUS` — correctly, because a slow
straight drift has no jumps. **Nothing ever checked whether the camera is pointed at
the film.**

**Why that blocks everything else:** `nearest_camera_m` in `item_manifest.json` sets the
fidelity target for all 435 items and flags 343 as hero. It was derived from a
reconstructed corridor that exists only as prose in `item_manifest.md` §1 — no script,
unreproducible — describing a camera that does not exist for two-thirds of the take.
**The entire asset campaign is scoped against a fiction.**

---

## 2. ORDER OF WORK — do not reorder without a reason

| # | step | task | state |
|---|---|---|---|
| 1 | Author beats 2–5 camera | **#34** | **DONE** — 479 keys, aim gate |
| 2 | Fix the render path | **#57**, **#58** | **DONE** — neither was the defect |
| 3 | Fix the gate | **#59**, **#63** | **DONE** — 28/28 → 7/28, relief validated |
| 4 | Fix the harness | **#62** | **DONE** — itemkit, preflight, 4K enforced |
| 5 | Fix the contract | **#51** | **DONE** — 1.1.0, 51.99 → 1.95 m/m |
| 6 | **REBUILD the world** | **#53** | **URGENT** — assembly is stale against 1.1.0 |
| 7 | Measure real screen presence | **#61** | running |
| 8 | World geometry defects | #46–#50 | running (#46–#48, #50) |
| 9 | Item campaign, re-tiered | #52 | ~316 agents; blocked on #53, #61, #69 |
| 10 | People | #45 → #41, #42 | ~25; #45 blocks the other two |
| 11 | Beats, breach sim, audio | #29–#33, #35 | ~30 — **the actual film** |
| 12 | Render ladder → 4K master | #36–#39 | ~10; 1080p/720p pixel-peeped FIRST |

**Remote CPU (#60) was measured and REJECTED at 1.68× against a 2.0× bar — but on a
below-median box (23.04 CPUs when offers run 8–384). See #67 to re-measure, and #66 for
running local and remote queues together, which clears the bar on #60's own numbers.**

---

## 3. AGENT BUDGET

Calibrated against wave 1's real timings: build ≈ 2.4 h, peep ≈ 0.3 h, which reproduces
the naive 24-day projection exactly.

| | agents | wall-clock |
|---|---:|---:|
| naive (1 agent/item × 435 × 2 rounds) | 1,740 | 24.5 d |
| after scope re-tiering (#61) | ~316 | — |
| after gate fix (#59), round-2 rate 100 %→20 % | 1,044 | 15.5 d |
| after batching (435 → ~240 units) | 372 | 11.1 d |
| after remote exec (#60) + 16-way | 372 | 2.4 d |
| after shared `itemkit` + worked example | 372 | **~2.0 d** |

**Two hard limits found in the runtime, worth knowing before planning a fan-out:**
- the **workflow runtime** caps concurrency at `min(16, max(2, cores-2))` — a module
  constant with **no env override**. This box has 6 cores → **4**.
- the **Agent tool** uses `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS ?? 20`.
- `MAX_SUBAGENTS_PER_SESSION` defaults to **200**; one workflow caps at **1,000**
  `agent()` calls. 1,740 was never runnable as a single workflow.

16-way only works *with* remote exec — 16 concurrent bpy builds on this box swap-dies.

---

## 4. LAYOUT — where everything lives

```
/home/zany/f1-round2/                  the round-2 project (part 1 is frozen, do not touch)
  part2.md                             the brief, verbatim
  docs/
    MASTER-PLAN.md                     <- this file
    THE-BRIEF-ROUND2.md                the brief, copy
    item_manifest.{json,md}            435 items; nearest_camera_m is SUSPECT (see §1)
    circuit_spec.{json,md}             the circuit: elements, elevation, sun
    beat_sheet.json                    beats + camera keys (ONLY beat1 + beat6 exist)
    WORLD_CONTRACT.md                  why each shared number went the way it did
    DEFECT-LOG-R2.md                   R2-001..R2-035 — read R2-017..R2-021 and R2-031..R2-035
    ITEM-CAMPAIGN-BRIEF.md             the contract every item agent follows
    HUMAN-FIGURE-BRIEF.md              people: the spec and the mannequin defect list
    WAVE1-PEEP-SYNTHESIS.md            what 15 adversarial reviews agree on
    PLAN-scope-optimisation.md         what work can be cut (agent 1)
    PLAN-throughput-optimisation.md    how to do the rest cheaper (agent 2)
    screen_presence.json               MEASURED per-item screen presence, 435 records.
                                       Carries METHOD (every assumption) and VALIDATION
                                       (four independent checks). SUPERSEDES the
                                       manifest's nearest_camera_m, which is CLOSER
                                       than reality on 220 of 435 items.
    screen_presence_objects.json       raw per-object and per-point measurement, so any
    screen_presence_points.npz         number can be re-derived without the 1.77 B sweep
    proposed_tiers.json                HERO 71 / MID 56 / BULK 308, 148 agents per round.
                                       Re-derived on assembly6 (contract 1.2.1) 2026-08-03.
                                       A PROPOSAL — the manifest is deliberately untouched.
                                       The previous 75/63/297 was measured on assembly2 and
                                       FOUR OF ITS HERO ITEMS WERE AN ARTEFACT: the old
                                       terrain sheet ran UNDER THE SHOWROOM, so a farm gate
                                       scored 1,604 sharp px because ground poked through the
                                       building floor 1.5 m from the lens.
                                       Superseded copies: docs/*_SUPERSEDED_a2_contract101.*
    frame_peeps.json                   28 peeps / 43 regimes / 94.5 % coverage, with the
                                       binning DECLARED in the output. The old "36 peeps"
                                       could not be reproduced — twelve different binnings
                                       give 36 at 88–90 %, so the figure never identified one.
    tiering_inputs.json                sha256 of every input the tiering read
  world/
    world_contract.py                  THE single source of truth. NOW 1.2.1.
                                       --selftest is 149 checks incl. continuity;
                                       --gate-selftest <old> proves it fails a bad revision
    film_exposure.py                   THE film's exposure, −3.628, MEASURED.
                                       C.REFERENCE_EXPOSURE_EXTERIOR (−3.048) is DERIVED and
                                       REFUTED — it over-exposes by 0.586 stops. Never use it.
    itemkit.py                         the shared item scaffold. contract_sun() and
                                       macro_rig() REFUSE the two bugs that bit wave 1.
                                       CAUTION: _tex_wavelength_m() is 3.18× wrong for
                                       ShaderNodeTexWave (returns 1.0/Scale, should be
                                       0.31416/Scale) — under repair. Its selftest cannot see
                                       it because it round-trips against the same constant.
    build_{surface,barriers,architecture,terrain,dressing,sky}.py
    items/<id>.py                      per-item modules (28 built)
    items/<id>_test.blend              per-item test scenes
  anim/
    build_beat1_anim.py                616 objects, 792 frames
    build_camera_rig.py                the ONE camera. 479 keys, all six beats.
                                       Carries the AIM GATE and a roll check.
    filmtime.py                        film-time -> world-time. Beat 3's ramp offsets
                                       the two clocks by 6.4 s PERMANENTLY — anything
                                       sampling telemetry per frame must WALK this.
  tools/
    placement_gate.py                  analytic intrusion depth in METRES, ranked;
                                       walks the PER-FRAME camera path, not its keys
    collision_gate.py                  BVH triangle-level; REFUSES on empty subject
    depth_probe.py                     penetration depth; REFUSES on empty subject
    item_gate.py                       per-item acceptance, 8 checks, renders its OWN
                                       witness frame with sphere/plane/grey-wedge controls
    campaign_preflight.py              resume checkpoint; SKIP 28 / BUILD 407 verified
    relief_positive_control.py         physical relief ladder; REFUSES to save a scene
    relief_control_measure.py          whose sun points up or whose exposure clips
    sharpness_probe.py                 sky-vs-subject detail energy; sky is its own control
    poly_census.py / poly_by_object.py polygon counts, three layers
    instance_variety.py / mesh_reuse.py the "one tree spammed" test
    sharpness_probe.py                 sky-vs-subject detail energy (#57)
    fix_audit_blend.py                 procedural_world() + save_clean()
  render/world/assembly/r2/            assembly2.blend, render2.blend, r2 renders
  render/items/<id>/                   gate.json, macro.png per item
  telemetry/telemetry.csv              1,743 rows: the ONE source for motion + audio

/home/zany/vast-render/                the render broker (NEVER touched by scene code)
  rq                                   agent CLI, stdlib only
  broker/  worker/  vastctl/  scripts/ panic.sh, brokerd.sh
  state/broker.db                      job queue

/opt/blender-5.2.0-linux-x64/blender   USE THIS for all Cycles GPU work
/usr/bin/blender                       UI/MCP only — cannot GPU-render
```

**Hardware — MEASURED FROM THE CGROUP, not from vast's listing.** Local: i7-7700K,
**6 cores, 11 GB RAM** — cannot load the 4.2 GB assembly for full evaluation.
Rented: **23.04 CPUs, 90.5 GiB** (`cpu.max` 2304000/100000, `memory.max`
97169440768). vast advertises `cpu_cores_effective` 32.0 and `cpu_ram` 515757 —
**optimistic by 39 %**. `nproc` 96 and `MemTotal` 188 GB are the HOST's, and host
`loadavg` runs ~52, so we are a tenant on a contended box. That contention is why
remote build throughput plateaus near 160 items/h regardless of slot count.

**Broker.** `./rq status` / `render` / `get` / `cancel` / `teardown`. Restart with
`scripts/brokerd.sh start /home/zany/f1-round2/world/beat1_anim.blend` — **the scene is
a positional argument; omitting it silently switches the default scene.** Bandwidth is
capped at **$4/TB both directions** (`MAX_INET_COST_PER_TB` in `vastctl.py`), enforced
as a query filter *and* re-checked client-side. Stop the broker **before** destroying an
instance or it re-provisions with stale in-memory code.

---

## 5. MEASURED FACTS worth not re-deriving

| quantity | value |
|---|---|
| traced triangles, whole world | **13,182,215,554** |
| — evaluated layer | 1,214,026,334 |
| — instanced layer | 11,968,189,220 from 310 source meshes |
| vegetation share | **98.1 %** of the evaluated layer |
| objects / unique meshes | 28,470 / 1,158 |
| VRAM in use while tracing 13.2 B | **5.5 GB of 32 GB** |
| worst asset repetition anywhere | **2.0 %** (`VEG_tree_birch_L2_09`, 329 of 28,002) |
| non-vegetation mesh reuse | **1.0** — every object unique, gini 0.000 |
| wave-1 triangles added | 323,028,492 across 28 items |
| car | 5.698 × 2.005 m, 0.340 m ride height |
| sun | elev 12.5°, bearing −58.0°, dir (0.518, −0.828, 0.216), 115.754 W/m² |
| road corridor | **clean** — nothing on the road (closest `ARCH_Gantry` +1.149 m) |
| remaining placement violations | **0** on contract 1.1.1 (`assembly4.blend`) — was 2 on 1.1.0: `ARCH_RetainEdge` 1.526 m, `ARCH_PitWall` 1.067 m. Closest car-path approach is now `ARCH_RetainEdge` -0.155 m, i.e. 0.445 m clear of the car BODY and inside the gate's 0.50 m edge-family allowance |

---

## 6. THE RECURRING FAILURE — read this before writing any check

**Seventeen times the verification was the broken thing, not the work.** The user found
four of them by looking at a picture. **This is the single most reliable failure mode on
this project.** If you are about to report a defect, first ask whether the instrument is
the defect.

The original seven:

1. Round 1 — collision test compared **bounding boxes**; shipped 19 overlapping pairs.
2. R2-011 — an area-weighted mean normal, **mathematically zero for any closed mesh**.
3. R2-012 — an assertion that **could never fail**.
4. R2-017 — ranked by triangle count; put the most-correct object **first**.
5. R2-018 — two gates printed **CLEAN on an empty test set**.
6. R2-019 — the item gate said "does not prove variation" and **passed the check**.
7. R2-020 — the harness rendered **1080p** and the gate scored it as **4K**.

Ten more, and the *shape* is what generalises — each is a distinct way to be wrong:

8. **A fix that could never execute.** `broker/remote.py`'s resume path called `log.info`
   in a module with no module-level logger. The `NameError` was swallowed and reported as
   the very failure it was meant to fix — `"resuming push of"` appeared **0 times** in a
   1.5 MB log.
9. **A latent version trap.** Index-based socket pinning stayed valid, produced plausible
   materials and passed every structural test while a Blender version bump rewired it.
   Every bump in every chain sat on a constant: **zero gradient, zero relief.**
10. **An unrepresentative sample.** The remote-exec A/B was measured on a 23.04-CPU box
    drawn from a pool running 8–384 cores, with no CPU filter in the query.
11. **An exact measurement of the wrong layer** — the most convincing kind of wrong. A
    polygon count landed **0.14 % from its own prediction** and was still a factor of
    **11** out, because it counted *evaluated* geometry rather than *traced*.
12. **A quoted number presented as a measurement.** The hash audit *printed* its controls
    as a hardcoded string. They are now computed every run, and it refuses to print
    results at all if the negative control fails to collapse.
13. **A control that stopped being a control.** A negative control went green because the
    miswiring it depended on was **fixed upstream**. A control that requires another
    module to stay broken is not a control.
14. **A check blind to which side the renderer gets** — *and then the diagnosis of what
    that costs was itself wrong.* 54 of 318 humankit pieces were inside-out, and it was
    believed they rendered with **every bump inverted**. **MEASURED AND REFUTED
    2026-08-02.** `tools/winding_probe.py`, one sphere with a 12 mm ridge at m = 2.2,
    rendered correct and reversed on the 5090: `Geometry > Backfacing` returns black vs
    white — so Cycles *knows* the surface is reversed, and the fault genuinely reached the
    renderer — but the lit render differs by **mean |diff| 0.00011, high-pass correlation
    +0.9997**. Cycles flips the shading normal for a back-facing hit **and the bump
    perturbation follows it consistently**. An inside-out, opaque, bump-shaded shell
    renders the same picture. Confirmed on a real module: repairing `timing_stand`
    (1,310 inward pieces, 22.5 % of surface area) changed **0.056 % of pixels** by more
    than 1/255.
    Winding still decides the picture for **true displacement** (mean |diff| 0.0117),
    refraction, subsurface, any shader reading `Backfacing`, and every non-Cycles
    consumer — so the repair is worth having and is now free on the way in. But it was
    **not** the cause of the soft figures, and it is not a candidate explanation for #57.
    *The lesson is the one this section keeps teaching: "the fault reached the renderer"
    and "the fault changed the image" are different claims, and only one of them was
    measured.*
15. **A bound on one side only.** `build_architecture` asserts paving is never *proud* of
    the datum, never that it is not far *below* it — and 100 mm of sunken forecourt went
    unseen across the glass mouth.
16. **A verdict decoupled from its measurement.** `depth_probe.py` prints
    `DEPTH_PROBE_OK` unconditionally — including on a wheel 200 mm inside the deck, the
    exact defect it was written for.
17. **A keep-out volume in the wrong frame.** `placement_gate`'s road corridor is an
    absolute world-z band while this circuit's ground runs −3.670…+7.964 m: it tests
    **empty air over 28 % of the lap**, and it guards every item placement.

Nine more from 2026-08-03 alone. By this point the count is not the point — **the
shapes are**, and they repeat:

18. **A selftest that round-trips against the constant it is testing.**
    `itemkit._tex_wavelength_m()` is **3.18× wrong** for Wave textures — and *the correct
    value is quoted in itemkit's own header, three lines from the wrong code*. The check
    used the wrong value on **both sides**, so it could never fail. This survived the
    frequency API, the relief law and a 14-module rebuild.
19. **A control artefact that was a second positive control.** `ctl_depth_neg.blend` put
    the wheel **200 mm in the air**. The battery ran with two cases that must fail and
    **none that must pass**.
20. **Measuring which pairs share a sampler seed.** A high-pass *correlation* against
    undenoised Cycles came back floor 0.146 / signal 0.883 — exactly backwards, because
    the sampler owns the high frequencies. Use a high-pass **energy ratio** (null = 1.0)
    with the floor rows seed-crossed like the signal rows.
21. **`--factory-startup` is not an empty scene.** The default Cube sat between an ortho
    camera and a measurement plane and returned **one identical number for all fourteen
    stages**.
22. **A summary statistic hiding a comb.** Realised head bearings occupied 10° of every
    18°, with −10..−5° holding **1,089 people** and +5..+10° holding **one** — while the
    gate scored 73 % either way. **Check the distribution, not the summary.**
23. **A checker with no depth floor** declared "PREFLIGHT IS WRONG" when *the checker* was
    wrong: one near-camera head produced 165 px of nonsense.
24. **A quantity that is identically zero for any valid input.** `convexity_defect`
    measured something mathematically zero for every simple polygon.
25. **A control evaluated where the two methods are equal.** An nlerp-vs-slerp control run
    at t = 0.5 — where they are identical — reported 0.000° and proved nothing.
26. **A global median hiding local behaviour.** A pop test reported **8,101 false pops** on
    smooth 16 m/s motion; 311 with a per-body local median.

And three failures of *reasoning* rather than of instruments, worth the same suspicion:

- **Publishing before looking.** "The check fails every single test" was written about the
  relief control before anyone opened the frames. The check was sound; the *scene* had four
  faults, including a sun pointing upward.
- **Extrapolating one sample across a varying subject.** The 4K master was costed at both
  $15 and $185 from two real measurements — of two *different scenes*, on a continuous take
  whose per-frame cost varies **8.5×** along its own length.
- **Repeating a stated cause without testing it.** The block cameras were said to be
  ruined by `macro_rig`'s depth of field. **There is no depth of field** — `use_dof=False`
  on all six, confirmed twice, and the gradient energy rises *monotonically* across the
  block, which a defocus cannot do. The real fault was arithmetic: **8.0 px median head**.
  Had the aperture been "fixed", the reshoot would have come back identical.
  The same shape produced `itemkit.socket_audit()` — a guard named by three docstrings that
  **does not exist** — and `v122/battery.sh`'s header citing "grep -c lines at the bottom"
  as a safeguard when the file contains none. **Grep for the guard before you cite it.**

**The rules that follow, and they are not optional:**
- A gate reports a **physical quantity in real units**. Counts are not measurements.
- **Unproven is a FAIL**, and the message must say what would make it measurable.
- **Check the fallback path.** R2-019's first fix printed "unproven" then fell through
  to a weaker statistic and passed.
- **Test every new gate against an artefact already known to be bad** and confirm it
  fails. This is the only technique that has reliably worked.
- **Measure the artefact, not the intent.** A gate that judges pixels opens the image.
- Confirm a suspicious gate with a **second, independently written measurement**.
- **Name the layer you measured.** Base, evaluated and traced geometry differ by 11×
  here. An exact number on the wrong layer is more dangerous than a rough one on the right.
- **A control must reproduce the fault itself**, never depend on a bug elsewhere surviving.
- **Bound both sides** when both sides are wrong — too proud *and* too sunken.
- **Check the frame.** Absolute world-z, film time vs world time, arc length vs chord: this
  project has been bitten by all three. Ask what coordinate the number lives in.
- **Before logging a regression, attribute it.** Re-run the probe against the intermediate
  artefact. Two "rebuild regressions" turned out to predate the rebuild by one version.
- **Distrust a conclusion that is also the convenient one.** R2-042's answer let a held
  multi-hour job start immediately, which is exactly why it was checked against the source
  rather than reasoned from plausibility.
- **A NULL RESULT MUST BE PROVEN, NOT ACCEPTED.** When a measurement returns "no change",
  the first hypothesis is that **the change never happened**. Check the artefact's mtime and
  identity before believing the number. Three separate nulls in one afternoon turned out to
  be measurement failures rather than real nulls:
  a harness passed `--save` to five modules that take `--out`, so they built the scene,
  printed a full report, **threw it away and exited 0** — and the gate measured a blend from
  four days earlier, returning mean |diff| 7.69e-06 against a 7.70e-06 noise floor, 0.00 % of
  pixels, correlation 0.99994. A flawless, entirely convincing null. The real answer was
  **57.50 %**;
  a module's bump chain was wired into `Thin Wall` instead of `Normal`, so 0.00 % changed
  because no relief reached the shader **on either side**;
  and four before/after pairs were not frames of the same object at all.
- **Confirm the two frames are of the same thing.** `pick_subject` frames the median-triangle
  instance, so a rebuild that renumbers the population silently re-aims the camera. One
  headline of "93.49 % of pixels changed" was measuring a *different post* at a different
  incidence; pinned to the same subject it is **43.39 %**.

---

## 7. OPEN DEFECTS, one line each

- ~~**#34** beats 2–5 have no camera~~ — **DONE 2026-08-02**, see §1
- **R2-029** beat 1's camera flies through the assembled car over frames ~640–700 and
  frames the glass wall; needs 3–4 intermediate keys between frames 591 and 754
- **#57** every render uniformly soft; sky carries 87 % of subject detail energy; suspect OIDN
- **#58** 2 of 28 modules build no sun; `procedural_world()` silently supplies none
- **#59** gate is orthogonal to the bar: 28/28 accepted, 15/15 reworked
- ~~**#46** pit wall 0.533 m from the transit centreline~~ — **DONE 2026-08-02**,
  contract 1.1.1: `PIT_WALL_S0` derived from `access_edges`, wall nose moved to
  s 3447.71 with a flared terminal; `ARCH_RetainEdge` (the deeper violation, 1.526 m)
  suppressed by the new `rim_buildable`. See DEFECT-LOG R2-037.
- ~~**#47** 32.25 m² of unwelded seam at the pit exit~~ — **DONE 2026-08-02** in the
  main part: 42.00 m² measured on the rebuild, of which 22.95 m² was one 0.30 m
  stand-off in `build_barriers`. `C.ribbon_edge_u` publishes the edge. R2-055
  (renumbered from R2-038, which now means the dead bump node).
- ~~**#48** 3,390 pure-black pixels~~ — **DONE 2026-08-02**. It was not one missing
  bay: EVERY 8 mm sawn joint in the pit-exit apron fell 35 mm to the bedding. The
  joints are sealed now, and `C.recess_relative_radiance` /
  `TOL_RECESS_RADIANCE` gates rendered blackness at the declared sun instead of
  bounding depth. R2-039.
- ~~**#50** TER_Ground × ARCH_Paving coplanar~~ — **DONE 2026-08-02**. `build_terrain`
  only FLATTENED the declared platform; it cuts it now, via `C.platform_field`.
  Terrain's hole 308 312 → 360 869 m². R2-040.
- **#51** `barrier_offset` steps up to 51.99 m/m from **unramped boolean masks**
- **#41/#42** crowd and pit crew are mannequins: 390 tris/person, no faces, stump hands
- one vegetation grit instance on gravel (1 of 4,716,477)

---

## 8. STANDING USER LAWS

- **Never touch the live site.** `f1-opus5.aipulsedaily.ai` is part 1 and frozen.
- **Always use the 5090.** Never the local 1070. Broker problems go to a subagent.
- **No external assets. Everything hand-built.** Verified by grepping for
  `ShaderNodeTexImage` / `images.load` / `bpy.ops.import_*`.
- **No repeated assets.** "One tree spammed 100 times" is the named failure.
- **Quality over speed.** Two passes have been rejected. "Okay" is a failing grade.
  A plan that saves time by lowering the bar is a failed plan.
- **Render time and money are not constraints. Wall-clock now is.**
- **Never go straight to 4K.** Hundreds of 1080p/720p passes, stripped to frames and
  pixel-peeped, before the master.
- Fable models: only ever for vast-middleware bug hunts. Nothing else.
