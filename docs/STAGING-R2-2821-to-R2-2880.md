# R2-2821 .. R2-2880 — the bar itself had the disease

Agent `r2-2821-verification-bar`, 2026-08-08.

---

## R2-2821 — `rig_preflight` had never executed, and could not have

`render/world/assembly/r2/v127/verify_film23.sh` line 175:

```bash
python3 tools/rig_preflight.py 2>&1 | tail -12
echo "  rig_preflight exit=$?"
```

`rig_preflight.py` reads a live `.blend`; it needs `bpy`. Run under `python3`
it cannot get past `read_rig()`. Measured, verbatim:

```
$ python3 tools/rig_preflight.py
Traceback (most recent call last):
  File "tools/rig_preflight.py", line 252, in <module>
    main()
  File "tools/rig_preflight.py", line 230, in main
    rig = read_rig()
  File "tools/rig_preflight.py", line 130, in read_rig
    import bpy
ModuleNotFoundError: No module named 'bpy'
python3 rc=1
```

and through the pipe the bar actually uses — `set -o pipefail` is not set in
these scripts, so the shell reports **`tail`'s** status:

```
$ python3 tools/rig_preflight.py 2>&1 | tail -12
  ...same traceback...
  rig_preflight exit=0
```

**The tool exits 1. The bar prints 0. Nothing reads either number.** No
`>> STAGE RESULT:` line is produced at all, so a caller grepping for the
verdict sees silence — and silence and a pass were spelled the same way.

`rig_preflight.py` was written at R2-1078 against the exact failure of a
comparison rig used silently while disagreeing with the film, and its own
docstring says *"A detection that does not reach an exit code is a rumour."*
It has been a rumour since the day it was written.

### Its first real verdict, on the live comparison rig

```
$ /opt/blender-5.2.0-linux-x64/blender -b world/surface_test_filmpose.blend \
      --factory-startup -noaudio -P tools/rig_preflight.py -- --json rig_real.json
>> RIG   world/surface_test_filmpose.blend
>> SUN   rig (0.0, 0.976407, 0.215939)
>> SUN   film (0.517854, -0.827767, 0.215939)
>> GRADE rig -3.0480 / AgX / look None   film -3.628 / AgX / look None
   FAIL SUN_BEARING    sun is 139.61 deg from the film's (elevation -0.000 deg,
                       bearing +147.970 deg). Elevation alone is invariant
                       under exactly this error
   FAIL EXPOSURE       rig grades at -3.0480000972747803, the film at -3.628
   FAIL WORLD_SKY      world is a bare Sky Texture (3 node(s)); the film's sky
                       carries cloud decks and atmosphere geometry, and
                       into-sun frames are exactly where that matters
>> STAGE RESULT: RIG_PREFLIGHT FAIL

TRUE EXIT STATUS = 1
```

**FAIL, three findings, exit 1.** The rig is 139.61° out in bearing and 0.58
stops out in grade, exactly as R2-1078 described, and the bar has been
reporting that check as part of its verdict for four film generations without
it running once.

### And the positive control: it PASSES on a correct rig

A guard that refuses everything is not a control either. Run against
`render/film23_breach.blend`, whose lighting rig **is** the film's:

```
$ /opt/blender-5.2.0-linux-x64/blender -b render/film23_breach.blend \
      --factory-startup -noaudio -P tools/rig_preflight.py
>> RIG   render/film23_breach.blend
>> SUN   rig (0.517854, -0.827767, 0.215939)
>> SUN   film (0.517854, -0.827767, 0.215939)
>> GRADE rig -3.6280 / AgX / look None   film -3.628 / AgX / look None
>> STAGE RESULT: RIG_PREFLIGHT_OK

TRUE EXIT = 0
```

Zero findings, exit 0, sun agreeing to six decimal places — from the same
binary, the same tool and the same run of the script that returned three
findings and exit 1 on the rig one minute earlier. **Both verdicts watched.**

---

## R2-2822 — the guard also died on its own documented command line

Once it was invoked under Blender, the FIRST usage line of its own docstring —

```
blender -b world/surface_test_filmpose.blend -P tools/rig_preflight.py
```

— **exited 2 and printed no verdict at all**:

```
00:00.602  blend            | Read blend: ".../world/surface_test_filmpose.blend"
usage: blender [-h] [--selftest] [--json JSON]
blender: error: unrecognized arguments: -b world/surface_test_filmpose.blend --factory-startup -noaudio -P
```

With no `--` on the command line, the old argv fallback ("everything that is
not a `.py`") handed argparse **Blender's own flags**. argparse exited 2 before
`evaluate()` was reached. So even a caller that switched from `python3` to
`blender` — the obvious repair — would have got a CRASH with no verdict line,
and `2` is not `1`: a reader who tested `rc == 1` would have called it a pass.

Fixed in `_argv()`: inside Blender with no `--`, the tool takes **no**
arguments. An argparse usage error now `return`s `RIG_PREFLIGHT_CRASH` (a
`return`, not a `sys.exit` inside an `except` — that is R2-2108's trap) and the
final verdict comes from `gate_exit.verdict()`, so the printed string and the
exit code are produced by one expression and cannot disagree. The token gained
an underscore (`RIG_PREFLIGHT_OK`): `gate_exit.code_for` matches on `_OK`, and
the old space-separated `RIG_PREFLIGHT OK` classified as **CRASH**.

---

## R2-2823 — the five decorative lines, and why the fix belongs upstream

v124, v125 and v126 all did:

```python
for k,want in (('resolution_x',3840),('resolution_y',2160),('fps',24),
               ('frame_start',1),('frame_end',2978),
               ('view_transform','AgX'),('look','None'),('exposure',-3.628),
               ('clip_start',0.05),('clip_end',200000.0),('camera','ONER')):
    if k in m: chk(k, m.get(k), want, ...)
    else:      print('  %-34s NOT REPORTED by measure_film_scene' % k)
```

`measure_film_scene.py` emits `cameras` (a list) and `scene_camera` (a name),
and **no resolution and no clip at all**. So `resolution_x`, `resolution_y`,
`clip_start`, `clip_end` and `camera` fell into the `else` on every run.
**v126 printed 15 lines and counted 10.** The five it did not count include
every line that names the delivery format.

v127 (R2-2109) repaired them by re-reading the same numbers out of
`measure_film_extra.json` instead. That closes those five, but leaves the
mechanism intact: the `if k in m: ... else: print` shape is still there for the
remaining six keys, so if `measure_film_scene` ever fails, `m` is `{}` and
**six more checks vanish silently** while the bar can still print PASS.

Two fixes, not one:

1. **`work/lighting/measure_film_scene.py` now emits the keys it was asked
   for** — `resolution_x`, `resolution_y`, `resolution_percentage`, `camera`,
   `clip_start`, `clip_end`, `n_cameras_in_scene` — as flat scalars, so the bar
   does not have to index a list to find the scene camera.
2. **The `else` branch is gone.** In `tools/film_bar.py` an absent key is
   `UNMEASURABLE`, printed in the column where `OK` would go, and counted as a
   failure. The rule is one line long:

   > **A check that cannot be evaluated must never be indistinguishable from
   > one that passed.**

   That is `gate_exit`'s VACUOUS distinction (R2-1121) finally applied to the
   thing that judges everything else. The bar was the last gate in the project
   still spelling "could not measure" as `0`.

---

## R2-2824 — the whole-bar audit: 24 counted, 17 silent

Every assertion `v127/verify_film23.sh` makes, in its header or its body, and
whether the script can act on it:

| # | assertion | counted? |
|---|---|---|
| 1–4 | interior_lamp_watts, n_lamp_stamps, scene_mark, assert_levelled | yes |
| 5–8 | strip present / size_y / radiance_authored / visible_camera | yes |
| 9–14 | fps, frame_start, frame_end, view_transform, look, exposure | yes, **but only while `m` is non-empty** |
| 15–23 | resolution_x/_y/_pct, camera, clip_start, clip_end, n_cameras, scale_length, camera object_fcurves | yes (since R2-2109) |
| 24 | carbon + rubber materials | yes, via `grep -qa … \|\| BARRC=1` |
| 25–30 | lift_multiplier, identity_residual_w, identity_base_x_lift, levelled_watts_from_stamps, worst_per_lamp_ratio, lift_plus_exposure | **NO** — printed by the "levelling identity" block, judged by nobody |
| 31 | `measure_film_scene` produced a verdict | **NO** — `rc=$?` echoed with the comment "(exit status is NOT the evidence)", and its `STAGE RESULT` line is never grepped either |
| 32 | `measure_film_extra` produced a verdict | **NO** — same |
| 33 | `measure_strip` produced a verdict | **NO** — `grep … \|\| echo "(strip probe printed no verdict)"`, which cannot fail the bar |
| 34 | socket_index_audit PASSes on the film | **NO** — `\| tail -12`, no judgement of any kind |
| 35 | socket_index_audit still FAILs 27 on film10 — **the bar's only negative control** | **NO** — same |
| 36 | rig_preflight | **NO** — never executed (R2-2821) |
| 37 | slabcheck "MUST exit 0" | **NO** — `\| tail -3`, `$?` is `tail`'s, consumed by nobody |

**37 assertions. 24 counted. 13 silent.** Six of the 24 (rows 9–14) are
conditionally silent on top of that: they sit behind `if k in m`, so if
`measure_film_scene` ever fails, `m` is `{}` and they disappear without a
trace while the bar can still print PASS.

`tools/film_bar.py` expresses the same 37 as **40 rows** — `rig_preflight`
splits into an `rc` row and a printed-verdict row, because Blender exits 0 on
an uncaught exception and neither one alone is evidence, and two rows are new
cross-reads that make the two probes agree about the same open blend rather
than letting the bar pick a favourite silently.

Item 35 is the worst of them. The bar's own header says:

> If film10 ever comes back PASS the instrument is broken and every PASS above
> it is vacuous. **Keep it.**

It was kept, and it was never read. The one control that proves the socket
instrument still fires has been piped into `tail` for four generations.

### The repaired bar

`tools/film_bar.py` expresses all 41 as rows with three verdicts (`OK`, `FAIL`,
`UNMEASURABLE`), runs the four external stages as **list-argv subprocesses with
no shell and therefore no pipe**, and judges stages on their printed verdict
because Blender 5.2 exits 0 on an uncaught exception.

`--selftest` runs with no Blender and no artefacts, and **watches every check
fail**: 27 value checks perturbed one at a time (27/27 return exactly one
FAIL), the five historically-silent keys dropped one at a time (each moves a
row from OK to UNMEASURABLE, never to silence), and the four primitives:

```
  CLEAN: every value check passes on correct measurements        PASS 31 value checks OK, 6 external rows UNMEASURABLE (no logs, no blend)
  SILENT->UNMEASURABLE: dropping measured['resolution_x'] is not a pass PASS unmeasurable 6 -> 7
  SILENT->UNMEASURABLE: dropping measured['resolution_y'] is not a pass PASS unmeasurable 6 -> 7
  SILENT->UNMEASURABLE: dropping measured['clip_start'] is not a pass PASS unmeasurable 6 -> 7
  SILENT->UNMEASURABLE: dropping measured['clip_end'] is not a pass PASS unmeasurable 6 -> 7
  SILENT->UNMEASURABLE: dropping measured['camera'] is not a pass PASS unmeasurable 6 -> 7
  CAN-FAIL: every one of 27 value checks returns FAIL when perturbed PASS 27/27
  CAN-FAIL: a nested key (camera.clip_start) is reachable and fails PASS
  NESTED-ABSENT: camera=None makes its two checks UNMEASURABLE, not OK PASS
  CAN-FAIL: a list index (resolution.0) is reachable and fails   PASS
  STAGE: one correct verdict is OK                               PASS
  STAGE: one wrong verdict is FAIL                               PASS
  STAGE: TWO verdicts is FAIL even though one of them is right (R2-2108) PASS
  STAGE: a log with a traceback and NO verdict is UNMEASURABLE   PASS
  STAGE: a stage that never ran at all is UNMEASURABLE, not silence PASS
  RUN: a clean rc=0 is OK                                        PASS
  RUN: rc=1 is FAIL -- not filtered through `| tail`             PASS
  RUN: a tool that cannot be executed at all is UNMEASURABLE     PASS
  RUN: rc=0 with NO printed verdict is UNMEASURABLE (Blender exits 0 on an exception) PASS
  SUMMARY: all-OK yields the PASS code                           PASS
  SUMMARY: one UNMEASURABLE row REFUSES the bar                  PASS
  CONSTANTS: exposure/lift come from the film's own modules      PASS FILM_EXPOSURE -3.628  LIFT_STOPS 3.628
  CONSTANTS: frame_end comes from the beat sheet, not a literal  PASS total_frames 2978

>> STAGE RESULT: FILM_BAR_SELFTEST_PASS  (0 failed)
```

Exposure and the lift come from `world/film_exposure.py` and
`world/showroom_lighting.py`; `frame_end` comes from `docs/beat_sheet.json`,
the file `build_film_scene.py` itself reads. Nothing derivable is retyped.

---

## R2-2825 — THE SHIP CANDIDATE'S VERDICT CHANGES FROM PASS TO FAIL

`film23_breach` was recorded at `>> STAGE RESULT: VERIFY23_BAR_PASS`, "24
checks, 0 failures". Re-measured with the repaired `measure_film_scene.py` and
judged with the silent checks counting:

```
=== the delivery format, the oner, the clip ===
  resolution_x                 want 3840        got 3840        OK
  resolution_y                 want 2160        got 2160        OK
  resolution_pct               want 100         got 100         OK
  camera                       want ONER        got ONER        OK
  clip_start                   want 0.05        got 0.05        OK
  clip_end                     want 200000.0    got 200000.0    OK

=== the stages that produced those numbers ===
  measure_strip ran   want STRIP_MEASURED    got 2 verdicts: ['STRIP_MEASURED', 'STRIP_ABSENT (probe raised SystemExit(0))']   FAIL
  film materials      want FILM_MATERIALS_OK got 2 verdicts: ['FILM_MATERIALS_FAIL (1 failures)', 'FILM_MATERIALS_FAIL (instrument raised SystemExit(1))']  FAIL

=== the controls that have to actually execute ===
  rig_preflight rc        want rc=0             got rc=1                FAIL
  rig_preflight verdict   want RIG_PREFLIGHT_OK got RIG_PREFLIGHT_FAIL  FAIL
  slabcheck rc            want rc=0             got rc=0                OK
  socket audit (film)                    want rc=0  got <not run: pass --socket>  UNMEASURABLE
  socket audit (film10 must still FAIL)  want rc=1  got <not run: pass --socket>  UNMEASURABLE

  40 checks claimed | 34 OK | 4 FAIL | 2 UNMEASURABLE
>> STAGE RESULT: FILM_BAR_FAIL          (exit 1)
```

**The five keys that were decorative for four generations turn out to be
correct.** 3840×2160 at 100%, ONER, 0.05/200000 — every one of them passes now
that it is measured. The film's delivery format was never the problem; the
problem is that the bar could not have told you either way, and said PASS.

The four FAILs are not the delivery format. Two are `rig_preflight` finally
firing (§R2-2821), and two are about the artefacts the reported PASS was read
off:

**1. `measure_strip` printed TWO verdicts on the live film23 log.**

```
$ grep -a "STAGE RESULT" work/r22101/strip_film23_breach.log
>> STAGE RESULT: STRIP_MEASURED
>> STAGE RESULT: STRIP_ABSENT (probe raised SystemExit(0))
```

This is R2-2108's own defect, in R2-2108's own file. `measure_strip.py` was
fixed at 07:56:51; the log is from 07:55:56 and **the strip was never
re-measured after the fix**. The artefact backing four of the bar's rows still
carries an unread contradictory verdict. v127 greps that log with
`… || echo "(strip probe printed no verdict)"`, which cannot fail anything.

**2. The materials PASS lives in a file the bar does not read.**

```
$ grep -a "STAGE RESULT" work/r22101/materials_film23_breach.log
>> STAGE RESULT: FILM_MATERIALS_FAIL (1 failures)
>> STAGE RESULT: FILM_MATERIALS_FAIL (instrument raised SystemExit(1))

$ grep -a "STAGE RESULT" work/r22101/materials_rerun2.log
>> STAGE RESULT: FILM_MATERIALS_OK (0 failures)
```

`materials_${NAME}.log` is the filename v127 greps. It says FAIL, twice. The
`FILM_MATERIALS_OK` that was reported is in `materials_rerun2.log`, a name
nothing in the bar looks at. Run v127's own line against the tree as it sits:

```
$ grep -qa ">> STAGE RESULT: FILM_MATERIALS_OK" work/r22101/materials_film23_breach.log \
    && echo "  BARRC unchanged (PASS)" || echo "  ^^ carbon/rubber DID NOT PASS -> BARRC=1"
  ^^ carbon/rubber DID NOT PASS -> BARRC=1
```

**3. `rig_preflight` FAILs on the comparison rig** — §R2-2821. Two rows, `rc=1`
and `RIG_PREFLIGHT_FAIL`. This one is a judgement call for the coordinator:
`world/surface_test_filmpose.blend` is a *comparison* rig, not the film, and
the film's own lighting passes the same check cleanly. But the bar's own line
says a rig may not disagree with the film about the film's grade, the rig has
been wrong by 139.61° since R2-1078 said so, and it has produced two confident
wrong verdicts that were relayed to the client. **If that line is to stay in
the bar, the rig has to be rebuilt or retired.** What is not available any more
is the third option the bar has been taking: printing it and moving on.

**4. `measure_film_extra` prints a BARE `STAGE RESULT:` with no `>>`.**

So does `sim/slabcheck.py`. Every reader in this project — every verify script's
`grep -aE "^>> STAGE RESULT"`, and `gate_exit._VERDICT_RE` itself — requires the
`>>`. **Two stages' verdicts are invisible to the entire harness on
punctuation.** `film_bar.py` reads both spellings; the right permanent fix is to
make the convention single, and both files are named here for whoever owns them.

---

## R2-2826 — the exit-status trap, everywhere else in the harness

176 shell scripts scanned; 5 set `pipefail`. Findings where a verdict is
actually discarded, as opposed to a cosmetic pipe:

| file:line | shape |
|---|---|
| `render/world/assembly/r2/v127/verify_film23.sh:175` | `python3 tools/rig_preflight.py … \| tail -12` then `$?` — **the subject of R2-2821** |
| `render/world/assembly/r2/v127/verify_film23.sh:180` | `.venv/bin/python sim/slabcheck.py … \| tail -3` then `$?` — bar line reads "MUST exit 0" |
| `render/world/assembly/r2/v126/verify_film19.sh:114,119` | the same two, previous generation |
| `render/world/assembly/r2/v127/verify_film23.sh` socket loop | `python3 tools/socket_index_audit.py --blend "$f" \| tail -12` — status never captured at all, **both arms including the negative control** |
| `work/r2840/runstage.sh:22` | captures `RC=$?` correctly, then **ends on `grep … \| tail -40`**, so the script's own exit status is `tail`'s and every caller sees 0 regardless of `RC` |
| `work/r2296/place.sh:21` | last command is a pipeline; script status is the filter's |
| `work/r2038/isolate_run.sh:40`, `retune_split.sh:51`, `shipped_run.sh:48` | same shape, three scripts |
| `work/dr_relief/render_ab.sh:28` | same shape (`ls \| tail`), cosmetic |
| `render/world/assembly/r2/selftest_battery.sh:130` | `grep -q … && echo PASS \|\| echo FAIL` — the verdict becomes **text**, not status |

Python side, 4 findings, none load-bearing for a verdict:
`tools/beat1_tourcost.py:171` (`os.system` status discarded),
`render/world/assembly/r2/selftest_probe_isolation.py:275`,
`tools/r2256_ab_measure.py:120`, `tools/sheet_reproduces.py:72`
(`subprocess.run` whose `returncode` is never read).

`work/r2840/runstage.sh` is the notable one: it is the *"script that reported
`tail`'s status as its own"* pattern in a live harness file, and it even prints
`(exit status is NOT the evidence)` two lines above the place where it throws
its own away. It is another agent's scratch directory, so it is named here and
not edited.

---

## R2-2827 — both of the bar's instruments were untracked

`git check-ignore -v` on the two probes the bar reads every one of its numbers
from:

```
.gitignore:27:work/	work/lighting/measure_film_scene.py
.gitignore:27:work/	work/r2100/measure_film_extra.py
```

`git log` on either was empty. So the change that made five bar lines
decorative for four generations — `measure_film_scene.py` never emitting
`resolution_x` — was one nobody could bisect, review or revert. That is the
**same** failure `.gitignore`'s own header is about (1,655 lines destroyed with
no history and no backup), and the same one the `render/world/assembly/r2/`
re-inclusion block was written to close, one directory over.

Both are now tracked, with each directory level opened one at a time and
immediately re-closed. `git status --untracked-files=all work/` reports exactly
two files; the gigabytes of blends, logs and scratch under `work/` stay
invisible.

---

## Lease held, not taken

`render/world/assembly/r2/v127/verify_film23.sh` — the live bar — is held by
lease `r2-2101-breach-strip` (created 2026-08-08T05:25:47, ttl 24 h, **pid
1972067, which is dead**). I do not own it, I have not released or retired it,
and I have not edited the file. The repaired judge therefore lives in
`tools/film_bar.py`, which is runnable on its own today:

```bash
python3 tools/film_bar.py --work work/r22101 --name film23_breach \
        --rig world/surface_test_filmpose.blend --socket --film render/film23_breach.blend
```

The three edits v127 needs, for whoever owns that lease:

```bash
set -u
set -o pipefail                       # 1

# 2 — replace the inline `python3 -c "…"` judge and BARRC=$? with:
python3 tools/film_bar.py --work $W --name $NAME \
        --rig world/surface_test_filmpose.blend --socket --film "$FILM"
BARRC=$?

# 3 — delete the trailing `rig_preflight` / `slabcheck` / `socket_index_audit`
#     sections entirely.  film_bar.py runs all four as list-argv subprocesses
#     and counts them.
```

Placing it in `tools/` also removes the mechanism that let the five decorative
lines survive three generations: the bar was **copy-pasted per `vNNN`
directory**, so a defect in it had to be found and fixed four separate times,
and R2-2109 fixed it in exactly one of them.
