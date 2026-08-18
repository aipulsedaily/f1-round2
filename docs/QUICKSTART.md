# QUICKSTART — what actually runs in a fresh clone

This repository is 70 MB of tracked source describing 545 GB of artefacts that
are not here. So the first honest question is: **with nothing but a clone and
Blender, what can you make happen?**

Quite a lot, as it turns out — because the world is procedural, and a procedural
asset is a program. You do not need the film, the render farm, the 4K frames or
a GPU to build a crash barrier and measure it.

**Everything on this page was run on 2026-08-18 and its output is reported as it
came, including the failures.** Nothing was tidied.

---

## 0. What you need

| | |
|---|---|
| **Blender 5.2.0 LTS** | not "5.x". Pinned, because a scene must be rendered by the build that assembled it. |
| **Python 3.14** | for the handful of tools that run outside Blender. |
| **`numpy`** | needed by almost everything. Blender's bundled interpreter already has it. |
| **A clone at `~/f1-round2`** | there is no configuration layer; scripts resolve paths through `os.path.expanduser("~/f1-round2/…")`. |
| **No GPU** | required for everything on this page. A GPU is only needed to make pictures. |

### Dependencies, since there is no `requirements.txt`

There is no packaging here and nothing is installable. Measured by walking the
imports of all 493 tracked Python files, the third-party set is:

```
numpy   scipy   Pillow (PIL)   soundfile   matplotlib   OpenImageIO
pyloudnorm   praat-parselmouth
```

`numpy` and `OpenImageIO` are the only two you can assume. **The audio modules
need `scipy`, `soundfile`, `pyloudnorm` and `parselmouth`, and Blender's
interpreter does not have them** — the audio chain is designed to run under a
normal CPython with a virtualenv, not inside Blender. The item builds and their
selftests need `numpy` only, which is why they are the recommended starting
point.

---

## 1. Build one item and argue with it — about 20 seconds

```bash
blender -b -noaudio -P world/items/armco_post.py -- --selftest
```

This builds 3,236 crash-barrier posts along the circuit and then interrogates
them. An excerpt of the real output:

```
   3236 distinct post specifications over 3236 posts; 0 exact duplicates
   naive [tangent, normal, up]: 1685 of 3236 records are LEFT-handed (det = -1)
       -- every one of them is a post on the right of travel
   `_world_frame`:              det min 1.000000 max 1.000000; 0 left-handed
   LOD0:  69547 tris/post   edge p10  0.687 mm =  0.99 px   median 4.06 mm = 5.8 px
   3236 distinct post specifications over 3236 posts; 0 exact duplicates
SELFTEST PASSED
```

Three things in there are worth noticing, because they are the house style:

- **It reports what it measured, not that it passed.** "0 exact duplicates over
  3,236 posts" is a claim you can disbelieve and check. "OK" is not.
- **It keeps the wrong answer next to the right one.** The naive local frame is
  left-handed on 1,685 of 3,236 posts; the selftest prints both so the fix has
  something to be a fix *of*.
- **It measures in pixels as well as millimetres.** An edge is 0.687 mm *and*
  0.99 px at delivery. A detail smaller than a pixel is not detail, and several
  of the log's more expensive entries are about exactly that confusion.

Other items that run the same way and pass:

```bash
blender -b -noaudio -P world/items/kerb_precast_unit.py       -- --selftest
blender -b -noaudio -P world/items/grandstand_riser_unit.py   -- --selftest
blender -b -noaudio -P world/items/mullion_intact.py          -- --selftest
```

---

## 2. Two of them are not Blender scripts

```bash
python3 world/items/human_fabric_probe.py --selftest
python3 world/items/human_png.py --selftest
```

These run under plain CPython. **Running them through Blender does not work,
and the way it fails is instructive** — so it is recorded here rather than
smoothed over:

- `human_fabric_probe.py` through `blender -P` hands argparse Blender's own
  argv and dies with `unrecognized arguments: -b -noaudio -P …`. Loud, obvious,
  harmless.
- `human_png.py` through `blender -P` **runs and fails a real check**:
  `round trip FAIL: wrote (7, 11, 3), read (7, 11, 4)`. Under CPython the same
  check passes. Blender's image stack returns four channels where the module
  expects three. That is not a broken selftest — it is the selftest doing its
  job in an environment its author did not intend, and the finding survives:
  **this module's round-trip assumption does not hold inside Blender.**

---

## 3. The full sweep, measured

All 27 item modules that carry `--selftest`, run head-to-head on 2026-08-18.
Wall time on a workstation with no GPU involvement. **The verdict column is
taken from the log, never from the exit code** — for the reason in the next
section but one.

Reproduce it with:

```bash
for m in $(grep -l -- --selftest world/items/*.py); do
  blender -b -noaudio -P "$m" -- --selftest > "/tmp/$(basename $m .py).log" 2>&1
done
```

| module | verdict | exit | wall | how it said so |
|---|---|---|---|---|
| `armco_post` | PASS | 0 | 19s | `SELFTEST PASSED` |
| `armco_w_beam` | PASS | 0 | 26s | `SELFTEST PASS` |
| `catch_fence_post` | **FAIL** | 0 | 54s | `SELFTEST FAIL` — the slot count reproduces the manifest's 690 exactly   [676 vs 690] |
| `crew_figure` | PASS | 0 | 121s | 8 checks, 0 failed |
| `crew_fireproof_overall` | **NO VERDICT** | 0 | 31s | ran to completion and printed nothing that states a verdict |
| `dais_delivery_ramp` | PASS | 0 | 69s | 20 checks, 0 failed |
| `grandstand_riser_unit` | PASS | 0 | 77s | `>> STAGE RESULT: SELFTEST_PASS` |
| `heras_fence_panel` | PASS | 0 | 43s | `SELFTEST PASS` |
| `hospitality_deck` | PASS | 0 | 28s | 26 `[PASS]`, 0 `[FAIL]`, **and no summary line at all** |
| `human_fabric_probe` | PASS | 2 | 4s | 4 checks, 0 FAILED — **run it with `python3`; through Blender it dies on argparse** |
| `human_png` | PASS | 1 | 4s | round-trip PASS under `python3`. **Through Blender it FAILS** — reads back 4 channels, not 3 |
| `kerb_precast_unit` | PASS | 0 | 78s | 21 checks, 0 failed |
| `marshal_post_deck` | **FAIL** | 1 | 22s | 25 `[PASS]`, 1 `[FAIL]`, **and no summary line at all** — site z == C.world_ground_z at the site                   max \|dz\| 0.0050… |
| `mullion_intact` | PASS | 0 | 20s | 22 checks, 0 failed |
| `paddock_personnel_figure` | PASS | 0 | 48s | 7 checks, 0 failed |
| `pit_wall_unit` | **FAIL** | 1 | 117s | 27 checks, 1 failed — ... and build_architecture's terminal nose did NOT (this is #46) 5.470 m at x=-232.6 |
| `pit_wall_unit_itemkit` | **FAIL** | 1 | 176s | 30 checks, 1 failed — ... and build_architecture's terminal nose did NOT (this is #46) 5.470 m at x=-232.6 |
| `showroom_facade_panel_v2` | PASS | 0 | 39s | >> selftest: 0 failures |
| `spectator_crowd` | PASS | 0 | 36s | 14 checks, 0 failed |
| `spectator_crowd_world` | **NOT SUPPORTED** | 2 | 32s | `--selftest` is not an argument this module accepts |
| `spectator_standing_ga` | **FAIL** | 1 | 36s | 8 checks, 1 failed |
| `team_truck_trailer` | PASS | 0 | 58s | 27 checks, 0 failed |
| `terrain_ground` | PASS | 0 | 232s | `>> STAGE RESULT: SELFTEST_PASS` |
| `timing_stand` | PASS | 0 | 23s | 42 checks, 0 failed |
| `tyre_blanket` | PASS | 0 | 63s | `>> STAGE RESULT: SELFTEST_PASS` |
| `tyre_deposit` | PASS | 0 | 32s | `>> STAGE RESULT: TYRE_DEPOSIT_SELFTEST_PASS` |
| `tyre_wall_tyre` | PASS | 0 | 117s | `SELFTEST PASS` |

**27 modules: 20 PASS, 5 FAIL, 2 neither.** Total wall time 1605 s (27 min).

Two of the 27 are CPython modules (§2) and are reported from their `python3`
run; the other 25 were run through Blender exactly as shown above.

### The two that are not a PASS or a FAIL are the interesting rows

- **`crew_fireproof_overall` printed nothing.** Its entire output under
  `--selftest` is four lines — a Blender banner, an audio-device warning, a
  blank line, and `Blender quit`. **No checks ran. It exited 0.** Any harness
  reading `$?` would have counted that as a pass, and this table nearly did:
  the first version of the sweep script classified by exit code and scored it
  green. It is `R2-018`'s "zero of zero passed" and `R2-4188`'s "a zero-length
  scan is the purest form of this project's commonest defect", found live,
  while writing the page that describes them.
- **`spectator_crowd_world` does not accept `--selftest` at all** and says so
  through argparse. That is the correct behaviour for a flag a module does not
  have, and it is the *only* one of the 27 whose non-result is unambiguous from
  the outside.

### How to read a failure here

**A failing selftest in this table is not rot, and it is not noise.** Look at
what one actually says:

```
[4] the west end and the Beat-4 car path (task #46)
  ok   wall face clears the placement gate's car volume (1.6025 m)  6.327 m
  ok   the published terminal budget also clears it                 6.018 m
  FAIL ... and build_architecture's terminal nose did NOT           5.470 m at x=-232.6
```

That is a cross-module disagreement about a real number, stated in metres, with
the position it occurs at. It is worth more than a green tick: it tells you that
`pit_wall_unit` and `build_architecture` disagree about where the west end of
the wall is, and by how much.

`catch_fence_post` fails the same way — `the slot count reproduces the
manifest's 690 exactly [676 vs 690]` — a fourteen-slot disagreement with a
manifest, which is the sort of thing that goes unnoticed for months when the
only check is that the build did not crash.

And `spectator_standing_ga`'s failing check is worth opening for a different
reason: it fails **one limb of a two-limb test**, against a control that was
built so the check could fail —

```
crowd_is_not_a_uniform_smear   FAILED
  gini 0.351 vs the uniform control's 0.144 = x2.43 (bar x1.7);
  density at the peak over density 30 m away 3.10x vs control 1.76x = x1.76
  (bars 3.0 absolute and x2.5).
  The control is the same 3,500 people, the same six banks and the same roles,
  spread EVENLY over the available banking -- built on purpose so the check
  can fail.
```

One limb clears its bar by 43 %, the other misses by 30 %, and the verdict is
FAIL because the limbs cannot be traded against each other. That design — two
required limbs rather than one composite score — is the fix that came out of
`BROKEN-INSTRUMENTS.md` §II.1, where a single number could be gamed by trading
audibility against articulation.

**These are left visible on purpose.** Making them pass by moving a number is
the failure mode this repository is a catalogue of; `R2-2172` is the entry about
a threshold and the quantity it judges being one instrument, and about what
happens when you change one without the other.

### And one thing to know before you trust any exit code

**Blender 5.2 exits 0 on an uncaught Python exception.** This was reproduced
while writing this page: `blender --python-expr "import scipy"` returned exit 0
on a machine with no `scipy`. The project's response is that every gate prints a
verdict line and callers grep for *that*:

```
>> STAGE RESULT: SELFTEST_PASS
```

**Except that only 4 of the 27 modules above actually print it.** Measured over
the sweep, the verdict is spelled seven different ways:

| spelling | modules |
|---|---|
| `N checks, N failed` (three capitalisations of "failed") | 11 |
| `SELFTEST PASS` / `PASSED` / `FAIL` | 5 |
| `>> STAGE RESULT: …` — the documented convention | 4 |
| `[PASS]` / `[FAIL]` lines with no summary at all | 2 |
| `>> selftest: N failures` | 1 |
| an argparse error (the flag does not exist) | 1 |
| **nothing whatsoever** | 1 |
| *(2 more are CPython modules, counted separately)* | 2 |

**And the exit code disagreed with the printed verdict on 4 of the 27.** Two
modules printed a clean result and exited non-zero; two failed a check and
exited 0.

`R2-2824` is the entry where the acceptance bar spent four film generations
reporting PASS because a gate was piped into `tail` with `pipefail` unset, so
the bar read `tail`'s exit status. The convention exists precisely because of
that — and the table above is the honest measure of how far it has actually
been adopted inside `world/items/`, which is: not far. **If you script anything
against these tools, grep the verdict, set `pipefail`, and never believe a
zero.** If you are adding a module, print `>> STAGE RESULT:` and make this
table shorter.

---

## 4. Read something instead of running it

Some of the most useful things here need no interpreter at all.

```bash
# the essay: 26 checks that passed while the thing was broken
less docs/BROKEN-INSTRUMENTS.md

# ~60 curated log entries with a ten-minute list at the top
less docs/READING-LIST.md

# find the entry for anything
grep -n '^## R2-1401 ' docs/DEFECT-LOG-R2.md

# check the reading list's links still land where they claim
python3 tools/docs_relink.py
```

`tools/docs_relink.py` needs no dependencies at all and is a small worked
example of the shape every check here is supposed to have: it can fail, it
refuses to write a result it has not verified, and it reports
`DOCS_RELINK_VACUOUS` rather than success when it examined nothing.

---

## 5. What you cannot do from a clone

Stated up front so it is not discovered three hours in.

| | |
|---|---|
| **Render the film** | ~97 h wall clock across three rented RTX 5090s, $132.57. It needs the companion `vast-render` repository and a funded vast.ai account. |
| **Render a 4K frame locally** | a local 8 GB card cannot hold one in a single pass. |
| **Rebuild the shipping world** | `render/world/assembly/r2/assemble.py` runs, but the assembly it produces is one of a numbered series, and `SHIPPING.md` records which one shipped and why. Expect hours and tens of gigabytes. |
| **Run the audio chain** | needs `scipy`, `soundfile`, `pyloudnorm` and `parselmouth` in a CPython, plus source material under `audio/out/` that is gitignored. |
| **Run the gate battery** | `python3 tools/gate_exit_selftest.py` runs, passes its 12 in-process checks, and then reports **5 controls misbehaved** — because the control `.blend` files it needs are gitignored. That is an honest `VACUOUS`, not a pass. |
| **Watch the film** | it is not in this repository and is not licensed for reuse. `LICENSE` §3. |

---

## 6. If something does not work

The most likely causes, in order:

1. **The clone is not at `~/f1-round2`.** There is no configuration layer.
2. **It is not Blender 5.2.0.** `blender --version`.
3. **A dependency is missing and Blender exited 0 anyway.** Read the output, not
   the exit code. See §3.
4. **It needs a gitignored artefact.** Anything reading from `render/`, `work/`,
   `watch/` or `audio/out/` is reading something that is not in the repository.

If none of those fit, open a `[question]` issue. "The documentation assumed
something I do not have" is a defect in the documentation.
