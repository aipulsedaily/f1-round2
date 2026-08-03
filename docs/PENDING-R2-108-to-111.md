# PENDING DEFECT-LOG ENTRIES R2-108 … R2-111

Written 2026-08-03 by the four-lying-instruments repair. **Not merged into
`docs/DEFECT-LOG-R2.md` on purpose** — that file has one owner, to keep the
numbering collision-free. Paste these, or renumber them, as you see fit.
Commits: `7bc94d9` (R2-108, R2-111) and `b0490f9` (R2-109, R2-110).

---

## R2-108 — a harness flag mismatch, a manufactured null, and the doc that was still teaching it

`work/r2038/run_module.sh` passed `--test --save <path>` to all fourteen modules
in its campaign. **Twenty-one of the forty-one item modules take `--out`.** On a
hand-rolled `opt()` parser the wrong flag is silent: the module builds the whole
test scene, prints its full report, throws the result away and exits 0. On
`pont_deck_slab` the gate then measured the blend built on 29 July, rendered it
against itself, and returned mean |diff| 7.69e-06 against a 7.70e-06 noise
floor, 0.00 % of pixels, correlation 0.99994 — a flawless, convincing null. The
stored re-run says **57.499 %**.

**Reproduced on live source, both directions, 2026-08-03:**

    crew_fireproof_overall --test --n 1 --save A.blend
        exit 0 · 188,062 triangles built and reported · A.blend NOT WRITTEN
    crew_fireproof_overall --test --n 1 --out  B.blend
        exit 0 · same build · B.blend = 18,367,428 bytes

The two runs differ by one line of stdout.

**The mismatch was not r2038's.** `world/items/REFERENCE.md` documented
`--test --save <path>` as *the* build command every item agent follows: the
**wrong save flag on 23 of 41 modules and the wrong verb on 3 more**. Fixed
there, and `tools/item_build_cmd.py` now derives the command from the module's
own parser. Two arms, per R2-073: a static AST read, and a **runtime** arm that
runs each argparse module with an unknown flag and reads the live usage table —
**35 of 35 probed, 35 agreed**. The 5 hand-rolled modules are STATIC ONLY and
the census says so per row rather than pretending. `--build` requires the target
blend's sha256 to change.

`run_module.sh` and `run_module2.sh` now **refuse** (exit 3) rather than build
with the wrong flag; `run_module3.sh` was already correct.

**WHAT WAS CONCLUDED THROUGH IT, AND DOES IT SURVIVE — YES, ENTIRELY.**
Attributed per module from the pipe logs:

| module | takes | harness that ran it |
|---|---|---|
| crew_fireproof_overall, gantry_truss, marshal_post_column, pont_deck_slab, pont_girder | `--out` | **run_module3 (fixed)** |
| armco_w_beam, catch_fence_post, heras_fence_panel, pit_wall_unit, tyre_wall_tyre | `--save` | run_module3 (fixed) |
| armco_post, kerb_precast_unit, team_truck_trailer | `--save` | run_module / 2 (broken) |

**Every module the broken harness ran takes the flag it passed**, and each
`build.log` carries a `saved …` line, so those three builds landed *by
artefact*. **Every `--out` module was re-run on the fixed harness.** No
published r2038 number descends from the null; the stored
`render/relief_ab/pont_deck_slab/ab.json` (08-02 18:45) is the corrected run.

**One layer out, and newly measured:** `item_build_cmd --stale-census` finds
**15 of 32** item test blends older than the source that built them —
`spectator_seated` by 133.5 h, `tyre_blanket` by 112.3 h. Reported as SUSPECT,
not as defects: an mtime says the source moved, not that the geometry did.

---

## R2-109 — a verdict read from a 3.6-stop-over frame is not evidence

`tools/build_verify_scene.py` set no view exposure. The assembly blends carry
`+0.000`; the film's measured grade is `FILM_EXPOSURE = -3.628`. The repair
(import `world/film_exposure.py`, apply before the rig, then assert every place
exposure can enter) existed but **had never been watched fail**. It has now:

* `--control-break-exposure 0.0` → `VERIFY_GRADE_FAIL`, *"+3.6280 stops off …
  That is no exposure at all — the blend's default"*, and the mis-graded blend
  is **deleted** so nobody can inspect it.
* `--control-break-view-transform Standard` → the same.
* normal → `VERIFY_GRADE_MATCHES_FILM`, −3.6280 on the static value, both ramp
  ends and the last frame.

**7 of 9 `verify_*.blend` carry +0.000; ~70 frames came off them.** What that
costs, measured on the artefacts — frame 960 of the same take, same rig, two
grades:

| | mean lum | p99 | pixels with a saturated channel |
|---|---|---|---|
| `render/exposure_beats/cal_960.png` (−3.628) | 0.0166 | 0.0456 | **0.000 %** |
| `render/shutter_ab/*_f960.png` (+0.000) | 0.494 | 0.9901 | **23.6 %** |

f870 is **27.2 %** saturated, f890 13.5 %, f1400 7.3 %.

**R2-053's shutter decision was read from those frames** and moved real work
(HERO 91 → 75, agents/round 178 → 169). Re-measured — `mean |Laplacian|`,
world/flat, over all opaque pixels and then over only pixels whose 3×3
neighbourhood holds no saturated channel:

| frame | all px | unclipped | px kept |
|---|---|---|---|
| f870 | 1.901 | **1.951** | 72 % |
| f890 | 1.766 | **1.832** | 86 % |
| f960 | 1.181 | **0.995** | 76 % |
| f1400 | 1.000 | 1.000 | 93 % |

**The conclusion survives and strengthens slightly** — removing the blown pixels
moves the ratio the *right* way, and R2-053's published 1.925 / 1.702 sit inside
the band. **f960's contribution does not**: 1.181 → 0.995, no difference at all,
so that frame's apparent 18 % gap is an artefact of the exposure and is
withdrawn. **Every absolute figure from these frames is unmeasured** —
`mean |Laplacian|` itself falls 46–47 % when the blown pixels go, so a
"smear ≤ 6 px" threshold cannot be read off them.

`tools/item_presence.py`'s `4_by_eye` key claimed eight `verify_world` frames
*"confirm what the numbers say"* — *"the trackside hoardings smeared to
transparency"* — and was **re-emitted on every run**. Withdrawn as **UNMEASURED,
not refuted**: the numeric tiering was never read from those frames. Marked in
place in `docs/screen_presence.json`, five `work/tier2/item_presence_*.json`,
and `render/shutter_ab/EXPOSURE_NOTE.md`.

`tools/render_local.py` never set or reported exposure, and would reproduce the
defect on any of the seven blown blends. It prints the grade of every render now
and says loudly when it is not the film's — shown firing at +0.000 and silent at
−3.628. **Still open, not touched (other owners):** `anim/build_camera_rig.py`
sets no grade and its live `work/beats456/rigs/*.blend` all log
`exposure ramp +0.000 -> +0.000`; `sim/witness.py:55` hardcodes `-3.628` instead
of importing it, which is the drift `film_exposure.py` exists to prevent.

---

## R2-110 — the gate that guards every item placement had no control, in any battery

v120, v121 and v122 each `run` `placement_gate` twice against the world and
**never once** against a case that must fail or must pass.
`ctl_place_pos.blend` and `ctl_place_neg.blend` have existed since the file was
written and **no battery ever opened them**. This is the gate already caught
testing empty air over 28 % of the lap. Wired in, and measured:

    ctl_place_pos       PLACEMENT_FAIL  rc=1   road_corridor −7.8222 m
    ctl_place_neg       PLACEMENT_CLEAN rc=0

**And the far negative control measures nothing.** Its own log:
`tested 1 objects; 1 rejected on bounding box; 0 measured per-vertex`. It can
catch a gate that *invents* violations and nothing else — it cannot catch
**over-rejection**, which is the failure this project actually had.

`ctl_place_nearmiss_neg.blend` is the over-rejection detector: the same obstacle
just outside the corridor, offset derived from the **live contract** each run
(`half_width(s)` + the gate's own 0.50 m margin + the cube's half extent +
0.80 m), so it tracks the corridor instead of expiring against it. Measured at
s = 1000, contract 1.2.1:

    gap 0.30 m → road_corridor −0.110 m   PLACEMENT_FAIL
    gap 0.55 m → +0.139 m                 PLACEMENT_CLEAN
    gap 0.80 m → +0.389 m                 PLACEMENT_CLEAN   ← shipped
                 1 object measured per-vertex, not 0

`ctl_assert.py` holds it there, because `expect pass` alone would be satisfied
by a control that had drifted back out to 3 km. Both directions: the near-miss
report → `CTL_ASSERT_OK`, tightest clearance +0.3892 m on `road_corridor`; the
**far** report, which the gate *also* passes → `CTL_ASSERT_FAIL`, *"this control
passed WITHOUT the gate looking at its geometry"*.

**R2-072's shape, closed.** Nothing regenerated the ten control blends; three
batteries opened whatever a human last left in `v120/`, and `ctl_place_pos` is
*positioned from the contract*. `lib_battery.sh :: regenerate_controls` rebuilds
them from live source every run and halts if the files were not rewritten —
shown both ways (10 rebuilt → `ok`; a directory it cannot write → `BATTERY_
INSTRUMENT_FAIL`, exit 2). All ten regenerated and re-run against the live
gates: **5 must-fail all FAIL, 5 must-pass all PASS.**

**And the battery had no version control at all.** `.gitignore`'s own header
says git exists here because an agent destroyed 1,655 unrecoverable lines — and
`render/` was swallowing **52 files of hand-written source**: `assemble.py`,
`probeA`–`probeK`, `lib_battery.sh`, all three `battery.sh`, `make_controls.py`.
"Establish a baseline from committed state" (R2-079) was **structurally
impossible** for the battery. Artefacts stay ignored; the source is tracked now.
`work/` still is — `work/r2038/run_module*.sh` remains untracked.

---

## R2-111 — three tools that reported success on failure, and five docstrings citing guards that do not exist

**`v120/fp_diff.py`** computed `moved`, printed it, and **never consulted it**.
No `sys.exit`, no `STAGE RESULT`, no `gate_exit` — it fell off the end at rc 0
and `lib_battery.sh :: run()` recorded `ok`. `v122/battery.sh` states in capitals
that *"fp_diff must find ZERO moved objects … before anything else in this report
is believed"*; it could have printed **100.00 %** and the run would still have
ended `BATTERY_OK`. The no-common-names branch printed its own refusal and also
exited 0. Expectations are declared on the command line and checked now, with a
7-case selftest and validation against the pair **already known to be bad**:
assembly5→assembly6 `--expect-moved 0` **FAILS** on `BR_Transit_NorthWall`,
bbox shift **3.1885 m**; assembly6→assembly7 **PASSES**, 0 of 28,781. A bare run
with no declared expectation is now `VACUOUS` (3), not a pass.

**`tools/horizon_gate.py`** returned `"verdict": "PASS"` for **zero frames
measured** *and* for **zero frames judged** — a camera rolled 80° while pointed
at the floor passed, because nothing was eligible. Both are `HORIZON_VACUOUS`,
exit 3, shown firing on `--lo 9000 --hi 9100` and on beat 1 (60 frames, none
within 45° of horizontal). The real run still returns a real verdict:
`HORIZON_ROLLED`, 32 FAIL frames at 2657–2688.

**`tools/build_beat1_audit.py`** computed `missing` image files, printed them
with `!!`, and printed `BEAT1_AUDIT_BLEND_OK` two lines later — the exact
failure its own comment twenty lines above says cost Round 1 a render batch.
`--control-plant-missing-image` exists so the assertion can be watched to fail.

**Five phantom citations, all confirmed absent:**

| citing file | citation | reality |
|---|---|---|
| `world/itemkit.py:1370` | `itemkit.socket_audit()` | no `def socket_audit` anywhere — **and it was in the `RuntimeError` text a reader hits at the moment a socket index has moved** |
| `world/items/crew_fireproof_overall.py:484` | `socket_audit()` | same |
| `tools/item_presence.py:321` | `--shutter-mode {flat,world}` | no such flag in the project |
| `tools/beat2_probe.py:80` | `--dump-exposure` | no such flag; and line 286 treats a missing `--exposure` as FAIL, so the phantom blocked the only documented route to passing |
| `tools/black_row_count.py:36` | `--control` | the guard is real and on by default; the flag is `--no-control`, so the documented invocation is an argparse error |

Plus the **battery headers themselves**: v121 and v122 claimed *"every `-P`
entry point is wrapped so an uncaught exception is a status 2"*. Four of their
own steps are not — `vertex_fingerprint.py`, `variety_distribution.py`,
`mesh_reuse.py`, `probe_pitexit.py`, **zero occurrences of `gate_exit` in any of
them**. The headers now say which four and tell the reader not to trust their
status.

`tools/phantom_citations.py` sweeps 207 files for `module.function()` and
`dir/file.py` citations that do not resolve, with both controls (3 real
citations → 0 hits; 3 phantom → 3 hits) and a `PHANTOM-OK` marker for prose that
*documents* a phantom. Flags are held in an explicit hand-verified list rather
than guessed, because a checker that guesses which of forty tools a `--flag`
belongs to manufactures defects at the rate it finds them (R2-073). Sweep is
**clean**, with two cited-but-absent items **printed as NOTE on every run**
because their files are owned by other agents right now:
`tools/build_film_scene.py:473` (`world/assembly/r2/assemble.py` — the real path
is `render/world/assembly/r2/assemble.py`) and `tools/socket_index_audit.py:88`
(a placeholder).

**Measured but NOT fixed**, all confirmed, all in files that were either
lower-value or owned elsewhere: `tools/inventory.py:245` (warnings counted,
`INVENTORY_OK` regardless), `tools/seam_gate.py:624` (`SEAM_CENSUS_OK` printed
whatever the census found, no guard), `tools/subject_sweep.py:299` (vacuous
summary lacks `span`/`verdict` → `KeyError` → **exit 0 with no `STAGE RESULT`
at all**), `tools/cam_clearance.py:69` (prints `CAM_CLEARANCE_VACUOUS` and exits
**1**, so a battery's `expect vacuous` halts on a correct refusal; and `min()`
on an empty `rows` raises → exit 0), and the same
count-then-pass-anyway shape at `tools/macro_audit.py:198`,
`tools/presentation_normals.py:175`, `tools/build_telemetry.py:553`,
`tools/dump_exposure.py:33`, `world/build_sky.py:1872`,
`world/showroom_lighting.py:586`.
