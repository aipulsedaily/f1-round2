# STAGING R2-1091 to R2-1120

Owner: the rig-build audit. Staged here for `DEFECT-LOG-R2.md`, which I do not edit.

---

## R2-1091 — THE BLAST RADIUS OF THE STALE CAMERA IS SMALL, AND IT IS ALL IN BEAT 1

R2-1007 logged that `world/camera_rig_path.json` is byte-identical to
`render/film16_path.json` while `render/film17_path.json` is the film's camera.
This is the audit of what that broke.

**Headline: 43 readers, 4 affected. The exposure is real but narrow, and it is
concentrated in exactly the beat that is under active work right now.**

### The divergence, re-measured (do not reuse R2-1007's figures unqualified)

R2-1007's "768 frames differ, worst 9.866 m at f545, identical from f781" is
right about position and wrong by omission about everything else.

| quantity | frames differing | worst | p50 over the span | p90 |
| --- | --- | --- | --- | --- |
| position | 768 (f2–f780) | **9.866 m** @ f545 | 2.83 m | 8.20 m |
| **focal length** | **681 (f2–f753)** | **23.0 mm** @ f223 (58 → 35 mm) | **6.05 mm** | **22.7 mm** |
| orientation | — | **103.3 deg** @ f527 | 13.7 deg | 81.4 deg |

**The lens divergence was not in R2-1007 and is the more damaging of the two**
for anything that measures framing, projection, mm-per-pixel or depth of field.
A 58 mm-vs-35 mm disagreement is a different shot, not a nudge.

"Identical from f781 onward" is very nearly true and worth stating precisely:
from f781 position and lens are **bit-identical**; 1,048 frames carry a residual
orientation difference of at most **0.180 deg**, which is consistent with the
6-decimal quaternion rounding in the file format and is not a real difference.

**The two curves converge to exactly zero at f754**, which is beat 1's last
camera key. Beat 2 onward was never re-authored. That single fact is why the
blast radius is small: nothing measured at f≥793 can be touched by this.

### The ranking

**AFFECTED — 4 readers. Findings in doubt.**

| # | reader | what changes | severity |
| --- | --- | --- | --- |
| 1 | `tools/r2791_beat1_focus.py` | see R2-1092 | **critical, live** |
| 2 | `audio/scene.py` → `audio/master.py` | see R2-1093 | **high, ships** |
| 3 | `tools/r2366_surface_visibility.py` | **R2-369** in doubt | medium |
| 4 | `tools/r2731_lens_retune_rebase.py` | see R2-1095 | medium |

`r2366_surface_visibility.py` walks all 2,978 frames with `--step 1` and derives
`cover_px` and `mm_px` from pose *and* lens. **R2-369 ("the showroom roof is
visible on 151 frames, all in beat 6; never near-field in beat 1") is a positive
claim about beat 1 built entirely on the stale beat-1 poses**, and a 9.87 m /
23 mm swing can change whether that slab top enters frame at all. It must be
re-run on the live path before it stands. R2-366's frame-scale ladder is a
weaker case: its endpoints (f945, f2978) are outside the window and survive, but
the argument that selected them swept beat 1, so *"f945 is the finest view of
this paving anywhere in the take"* is unproven.

**PARTIAL — 3 readers. Stale rows on disk, published conclusions survive.**

`tools/r2581_nearfield_sweep.py`, `tools/r2651_band_sweep.py` and
`tools/r2651_track_scale.py` each write beat-1 rows from the stale camera —
26.2 % of emitted rows — but every figure any defect quotes from them is beat 4/5.
`render/r2581/nearfield.json`, `render/r2651/band_sweep.json` and
`render/r2651/track_scale.json` carry junk beat-1 rows and should be regenerated;
nothing rests on them.

**UNAFFECTED — the remaining 36.** They evaluate at single frames outside the
window (f2575, f2978, f2000, f945), or over hardcoded beat-4/5/6 ranges
(f1191–2714, f1057–2978), or explicitly exclude beat 1, or read only the frame
count. `tools/r2651_dof_dump.py` never opens the file at all — it only names it
in its docstring.

### Cost

**$0.** Every measurement in R2-1091 through R2-1096 is pure geometry on the
local CPU. No Blender, no GPU, nothing queued.

---

## R2-1092 — THE BEAT-1 FOCUS FIX IS BEING ADJUDICATED ON A CAMERA THE FILM DOES NOT HAVE

**This is the one that matters and it is live right now.**

`tools/r2791_beat1_focus.py` was reported to me as the one tool reading the live
path. **It is not.** It defaults to `render/film16_path.json` (line 621) and
hardcodes it again at line 574 for frames 1–792 — the stale lineage, over
exactly the divergent span. The only reader of `film17_path.json` in the tree is
`tools/r2971_pont_camera_rebase.py`.

Solved both ways over all 792 beat-1 frames:

| | stale (film16) vs live (film17) |
| --- | --- |
| frames focusing on a **different part of the car** | **482 of 792 — 60.9 %** |
| focus-distance error | p50 **1.171 m**, p90 5.302 m, max **5.752 m** |
| focus-distance error, relative | p50 **35.6 %**, max 93 % |
| lens error | p50 5.68 mm, max **23.0 mm** |
| frames where the stale focus falls **outside the live subject's near–far span** | **369 of 792 — 46.6 %** |

Worst frames are not marginal — they are a different shot:

```
f589  stale: CORNER_FL     focus 1.483 m  lens 58.0
      live:  halo_assembly focus 7.235 m  lens 36.1
f606  stale: CORNER_FL     focus 1.553 m  lens 54.7
      live:  CI            focus 7.304 m  lens 36.5
```

**On nearly half of beat 1 the shipped focus decision would put the subject
outside its own depth of field.** Any pacing or focus verdict taken from this
tool's current output is void.

### The tool's own guard fires, and the stage still says OK

`r2791_beat1_focus.py --selftest` prints:

```
solver AGREES at the stations   SKIP  path file and sheet are different
generations (mean station offset 4.612 m)
...
STAGE RESULT OK r2791_focus_selftest
```

The `same_gen` control **detected this staleness and was overruled by its own
stage line.** A SKIP on the single control that would have caught the wrong
camera, followed by `OK`, is the "guard that cannot fire" shape with an extra
step: it fired, and nothing was wired to it.

**And the live path does not fix it.** Re-pointed at `film17_path.json` the same
control reports **2.597 m** of mean station offset and still SKIPs. film17 is
closer to the current beat sheet than film16, but neither matches: **the sheet
has been re-authored since film17 was built.** The rig needs rebuilding from the
current sheet before this control can be read at all.

**FOR THE BEAT-1 OWNERS — REPORTED, NOT CHANGED** (I hold none of `anim/`,
`beat_sheet.json` or the beat-1 proxy):

1. Re-point `r2791_beat1_focus.py` off `film16_path.json` — both line 621 and
   the hardcoded line 574 — onto `live_campath.load()`.
2. Rebuild the rig from the current sheet, or the `same_gen` control stays dark.
3. Make `same_gen`'s SKIP fail the stage, or delete the control. A control that
   skips into `OK` is worse than none.

---

## R2-1093 — THE 9.866 m REACHES THE MIX

Yes. `audio/master.py:117` constructs `CameraPath()` with no argument, which
defaults to the stale file (`audio/scene.py:325`). The camera is the **listener**:
its position sets 1/r attenuation and propagation delay, its velocity sets
Doppler, and its orientation sets the binaural pan (`EAR_HALF` on the camera's
local +X, so roll is audible).

Beat 1's audible content is the **assembly layer**, rendered positionally at the
car through the propagator (`master.py:300`, `prop.source_track(car_ctrl["pos"])`).
Measured against the real telemetry source track over f1–792:

| | error, stale vs live listener |
| --- | --- |
| 1/r level | p50 **2.19 dB**, p90 6.68 dB, max **11.69 dB** |
| binaural azimuth | p50 **13.8 deg**, p90 89.7 deg, max **178.1 deg** |
| frames where the source is panned to the **wrong ear** | **318 of 792 — 40.2 %** |
| propagation delay | max **16.5 ms** |
| Doppler | max 17.3 cents (minor) |

Level and Doppler are defensible-to-marginal. **The pan is not: on 40 % of beat 1
the assembly is on the wrong side of the listener's head**, and a 178-degree
azimuth error is a fully reversed image.

Beats 2–6 are untouched — the glass pane, impact and shard sources are static and
all beat-2+, and the camera is bit-identical from f781.

**FOR THE AUDIO OWNER — REPORTED, NOT CHANGED** (another agent holds
`audio/scene.py`'s closing 11 s): the one-line fix is `scene.py:325` to
`live_campath.declared_campath()`. The closing 11 s is beat 6 and cannot be
affected by this; the fix is confined to the default path and does not touch it.
**The mix needs re-rendering for beat 1 after that.**

---

## R2-1094 — WHAT SURVIVES, MEASURED RATHER THAN ASSUMED

The expectation that the asphalt work survives was correct. It is now measured.

**`world/build_surface.py` — SURVIVES, exactly.** Two independent reasons:

1. `_film_pose_defs` (line 4387) reads the stale file, but `FILM_POSE_FRAMES =
   (1547, 2225, 2000, 1226)` — **all four are outside f2–780**, so the four film-pose
   cameras are bit-identical either way.
2. The readable band at `build_surface.py:1819` was re-derived end to end.
   `tools/r2651_track_scale.py` was re-run against `film17_path.json` (pure
   geometry, `STAGE RESULT: R2651_TRACK_SCALE_OK`) and the weighted percentiles
   recomputed:

   | camera | n frames ≥2 % cover | p25 | p50 | p75 |
   | --- | --- | --- | --- | --- |
   | stale (film16) | 1,888 | 10.8 | 20.8 | 108.1 |
   | **live (film17)** | **1,887** | **10.8** | **20.8** | **108.1** |

   Unchanged to every published digit. The reason is quantified, not lucky:
   of the 1,888 qualifying frames only **3 fall inside the divergent range,
   carrying 0.01 % of the cover weight**. On the live camera it is 2. The road
   genuinely does not feature in beat 1.

   **The 40 mm – 2 m readable band, the eleven-layer census and everything
   R2-1031 concluded from them stand.**

**`tools/seam_gate.py` — SURVIVES, exactly.** Its window is f738–832, which does
straddle the boundary, but the two curves have already converged there: **max
0.171 m of position and 0.313 mm of lens inside the whole window**, against
`TOL_ARTEFACT_M = 1e-3` on the two pinned keys, which sit at f754 and f793 where
the divergence is 0.000000 m. Run both ways the gate emits **identical output to
four decimals** — same 1.407× worst bulge at f815–817, same 39.66 m/s² at f817,
same 4.91 %/frame rotation at f806, `SEAM_OK` both times.

The f792/793 seam is safe **because f754 is where beat 1's last key is**, and
both files share it exactly.

---

## R2-1095 — A TOOL THAT NAMES THE STALE FILE `LIVE` AND CERTIFIES IT

`tools/r2731_lens_retune_rebase.py:49` — `LIVE = "world/camera_rig_path.json"`.

Its selftest then asserts, and passes:

```
chk("beat 1 is bit-identical to the live path",
    all(o[f]["p"] == live[f]["p"] and o[f]["lens"] == live[f]["lens"]
        for f in range(1, 793)))
```

This is **true of the variable and false of the film**. The rebased path it emits
carries the stale beat-1 camera, and its own control certifies that as correct
over exactly f1–792. Its header's *"differs from the live path by 8.863 m of
position"* is film14 measured against the stale file, not against the film's
camera.

If that rebased path is ever applied it would **re-inject the stale beat-1
camera into the film** with a green selftest attached. It has not been applied
as far as I can see; it should not be, until `LIVE` points at
`live_campath.declared_campath()`.

This is the same shape as the finding R2-1007 already made about
`r2731_pont_camera_apply.py`: a correct tool, a wrong input, a plausible wrong
conclusion. Expect it wherever a variable is named for a fact instead of reading
one.

---

## R2-1096 — THE DETECTION ALREADY EXISTED. NOTHING WAS WIRED TO IT.

`tools/horizon_gate.py` has `_stale_default_warning()`, and it works. Run today
on the default path it prints:

```
STALE DEFAULT: render/film17_path.json -- the newest assembled film scene --
holds a DIFFERENT camera from world/camera_rig_path.json, which is what was
just judged. Rendered frames come from the scene. Re-assemble it, or pass
--path render/film17_path.json to judge what will actually be rendered.
```

…and then:

```
-> PASS
>> STAGE RESULT: HORIZON_LEVEL
```

**The tree has been printing an accurate description of R2-1007 on every
horizon_gate run for three days.** It is a `print()` at line 698 that touches
neither the verdict nor the exit code. horizon_gate's own result is genuinely
unaffected (it excludes beat 1, and emits identical output both ways), so the
one tool that could see the problem was also the one tool with no stake in it.

This is the sharpest instance yet of the project's most-logged defect family,
and it inverts the usual diagnosis: **the instrument was not broken. It fired,
correctly, in prose, into a log nobody was gating on.**

`tools/input_stamp.py` is the companion failure, and it is worse because
preventing this is its stated purpose:

- `default_inputs()` hardcodes `"camera_path": "world/camera_rig_path.json"` —
  the literal-default pattern **its own docstring (lines 52–64) diagnoses for
  the `world` role and fixes there** via `shipping_world.declared_shipping_path()`,
  which raises rather than defaulting. The camera never got the same treatment.
- It is a **recorder, not a comparator**. It hashes what it is handed. It has no
  concept of which file is live, so a faithful sha256 of the wrong file is a
  clean stamp.
- `declared_version()` returns `frames=2978` for the stale file and `frames=2978`
  for the live one — and `None` for `film17_path.json`, because the check is
  `path.endswith("camera_rig_path.json")`. **The human-readable label reads the
  same stale or fresh, and is blank for the correct file.**

---

## R2-1097 — ROOT CAUSE: THE PATH FILE'S NAME IS A SIDE EFFECT OF AN ARGUMENT

Not a checked-in copy, and not a rename that left an orphan by accident. The
artefact has **no owner by construction**.

`anim/build_camera_rig.py:1585`:

```python
base = os.path.splitext(out)[0]
json.dump({"frames": total_frames, "path": path}, open(base + "_path.json", "w"))
```

The path file is named after `--out`. There is no canonical output name, so
`world/camera_rig_path.json` exists **only** when the rig is built standalone
with `--out world/camera_rig.blend`. That last happened in
`render/world/assembly/r2/v125/build_film16.sh:53`, **2026-08-04 15:49** — the
exact mtime of the stale file. There is no v126 script.

Since then the pipeline moved to `tools/build_film_scene.py`, which calls
`build_camera_rig.main()` with its own `--out render/filmNN.blend`
(**already documented as R2-840e**), producing `render/film17_path.json`.
Separately `work/r2840/chain2.sh` built `--out world/R2829_camera_rig.blend`,
producing `world/R2829_camera_rig_path.json` — **byte-identical to
`film17_path.json`**, so a correct copy has been sitting in `world/` since
Aug 7 04:49 under a defect-prefixed name while the canonical-looking file next
to it stayed three days stale.

So: **a build step that stopped running, because the rig's output name follows an
argument and the pipeline's argument moved.** Nothing rewrote
`world/camera_rig_path.json` because nothing was ever responsible for it.

**FOR THE RIG OWNER — REPORTED, NOT CHANGED** (`anim/` is held by another agent).
The fix is *not* to have `build_camera_rig.py` also write a canonical copy —
that manufactures a second copy of a fact, which is the defect
`shipping_world.py` exists to kill. The fix is:

1. **Delete `world/camera_rig_path.json`.** It is an orphan with no writer. It
   cannot be maintained; it can only go stale again. Do this *after* the readers
   are migrated, or 43 tools crash at once.
2. Have `build_camera_rig.py` **print the absolute path it wrote** as a
   `>> STAGE RESULT` line, so a build log records which artefact this run owns.
3. Route every reader through `tools/live_campath.load()` (R2-1098).

---

## R2-1098 — `tools/live_campath.py`: THE WRONG CAMERA IS UNAVAILABLE, NOT MERELY DETECTABLE

A stamp that 43 callers must remember to check will be forgotten by the 44th, so
this offers no stamp to check. It offers the camera, and **`load()` takes no path
argument.** There is no parameter through which the wrong file can be supplied.

- `docs/LIVE-CAMERA.md` is the single declaration, modelled exactly on
  `render/world/assembly/r2/SHIPPING.md` and parsed by exactly one module,
  modelled on `tools/shipping_world.py`.
- **Two keys, not one.** The declaration pins the filename *and* the sha256.
  Both are checked on every load, so **a rebuild that changes the bytes without
  updating the declaration raises in every reader** rather than being adopted
  silently. That is the failure mode that will actually recur.
- `KNOWN_STALE` recognises the R2-1007 file **by content**, so renaming it does
  not launder it, and the error names the defect and the divergence.
- A genuine A/B must call `load_explicit(path, why=...)` with non-empty prose.
  Every deliberate non-live read is then `grep`-able and prints itself at run time.
- stdlib only, no `bpy` — the same constraint `shipping_world` carries, so tools
  under the plain interpreter and tools inside Blender can share one parser
  instead of one of them keeping a copy.

### Proof that it fails — `python3 tools/live_campath.py --selftest`

```
>> SELFTEST live_campath
  resolves the declared live camera                        ok    render/film17_path.json
  loads it                                                 ok    2978 frames
  byframe keys by frame number                             ok    f1..f2978
  MUST FAIL: the real stale world/camera_rig_path.json     ok    raised, says 'KNOWN-STALE'
    ...and it is recognised by CONTENT, not by filename    ok    sha d9c8f5c54ccd1ad8
  MUST FAIL: the same bytes under an innocent filename     ok    raised, says 'KNOWN-STALE'
  MUST FAIL: declared sha256 disagrees with the file       ok    raised, says 'changed on disk'
  MUST FAIL: a declaration that pins no sha256             ok    raised, says 'pins no sha256'
  MUST FAIL: an undeclared camera                          ok    raised, says 'undeclared camera'
  MUST FAIL: no declaration file at all                    ok    raised, says 'does not exist'
  MUST FAIL: load_explicit with an empty why               ok    raised, says 'must state its reason'
  load_explicit with a reason returns the file             ok    2978 frames

STAGE RESULT: LIVE_CAMPATH_OK live_campath_selftest
```

**The first negative control feeds it `world/camera_rig_path.json` itself — the
actual file that caused R2-1007, on disk, as it is now** — not a synthetic
stand-in. The guard is not vacuous: it refuses the real offender, refuses it
under a disguised filename, and refuses an undeclared rebuild.

**Stated limit, so nobody over-trusts it:** `KNOWN_STALE` is a denylist and only
catches files already named in it. It is the belt. The braces — and the load-
bearing mechanism — are that `load()` has no path parameter and that the
declaration's sha256 is verified on every call.

### Migration owed

`live_campath.py` is in place and proven; **no reader has been migrated yet.**
43 call sites across files held by several agents is not a change to make while
a beat-1 proxy is in flight and 13 files are modified elsewhere. Priority order:

1. `tools/r2791_beat1_focus.py` (R2-1092) — beat-1 owner, live
2. `audio/scene.py:325` (R2-1093) — audio owner, ships
3. `tools/r2366_surface_visibility.py` — then re-run and re-judge **R2-369**
4. `tools/r2731_lens_retune_rebase.py:49` — before it is ever applied
5. `tools/input_stamp.py:66` — `default_inputs()`, and teach `declared_version()`
   to report a sha prefix instead of `frames=2978`
6. `tools/horizon_gate.py` — make `_stale_default_warning()` set the exit code
7. the remaining 36, which are unaffected and can migrate at leisure

Nothing was copied over `world/camera_rig_path.json`. That would fix today and
guarantee the repeat, and it would silently change the input of 43 tools while
other agents are mid-run.
