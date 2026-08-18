# STAGING — R2-1701 to R2-1760 — the rebuild that carries the manifest

Working notes for the film rebuild `docs/NEXT-REBUILD.md` describes. Appended to
as the build runs. Other agents are writing to this file too — re-read before
editing.

## R2-1701 — film18 IS NOT THE REBUILD, AND TWO OF ITS GAPS ARE INVISIBLE FROM ITS OWN LOG

`render/film18_breach.blend` (2026-08-07 18:59) was built by the camera-pacing
workstream to carry R2-1601..1603. It is a good build and it is **not** the
rebuild the manifest asks for. Audited in the artefact with
`libraries.load(link=True)`, not inferred from source:

| manifest item | in film18_breach? | evidence |
|---|---|---|
| car paint v5 | **YES** | `LiveryPaint`, Metallic LINKED via `R2CP_085_metallic -> paint`, MULTIPLY 0.16129031777381897 x 0.62 = 0.10 |
| showroom ceiling | **YES** | `R2_SHOWROOM_CEILING`, 21 objects, all `R2C_*` |
| driver | **YES** | 11 `DRV_*` objects |
| breach shards + frame | **YES** | 3,796 `GS_b*`, 39 `BF_*`, `BF_MUL05_S02` present |
| **breach fines** | **NO** | `BREACH_Fines` collection exists and is **EMPTY**. Searched 35,304 object names for fines/chip/puff/FN_/debris/frag/spall: 0. The applier's own report says `"fines": {"skipped": true, "why": "neither --fines-lib nor --debris given"}` |
| **beat-4 pit annexe** | **NO** | see below |
| **asphalt relief re-budget** | **NO** | see below |
| **beat-6 ending re-key** | **NO** | live sheet had `hold_lens_mm 74.0`; the candidate says 130.0 |
| **beat-6 lap-down** | **NO** | see R2-1703 |

**The two world items are the instructive ones.** film18's own build log prints,
and then moves past:

```
>> WORLD STALENESS: assembly10.blend predates 4 of its own generator module(s).
   world/build_architecture.py  newer by 60.4 h
   world/build_dressing.py      newer by 59.8 h
   world/build_surface.py       newer by 65.9 h
   world/build_terrain.py       newer by 74.3 h
   NOT a refusal
```

`assembly10.blend` is 2026-08-04 15:46. `build_architecture.py` (beat-4 pit
annexe) is 08-07 04:11 and `build_surface.py` (asphalt relief) is 08-07 09:42.
So both changes were landed, correct, and **structurally unable to reach a
frame**, because the film build appends CAR/SHOWROOM/PROPS/LIGHTS/CEILING onto a
world it does not rebuild. Nothing failed. The staleness report is explicitly
"NOT a refusal", and it is the only thing standing between a landed change and a
silently stale film.

**The lesson is not "someone forgot".** A film build that consumes a prebuilt
world can only be as current as that world, and nothing in the film build's own
gates can see the difference — every gate film18 ran passed, because they all
measure the film against itself.

## R2-1702 — THE BEAT-6 RE-KEY IS FOLDED INTO THE GENERATORS, NOT THE SHEET

`docs/NEXT-REBUILD.md` says to fold `docs/R2851_beat_sheet_CANDIDATE.json`'s
`beat6` and `aim.6_ending` **into `docs/beat_sheet.json`**. Taken literally that
is wrong, and it is the same defect the manifest itself warns about elsewhere:
`docs/beat_sheet.json` is **generated**, by `tools/build_beatsheet.py` then
`tools/author_beats2_5.py`. A value hand-written into it survives exactly until
the next regeneration — which is how a beat-1 camera fix sat unpromoted for ten
hours.

Verified first, because a fold into a generator is only safe if the generator
still reproduces what is shipped: regenerating to a scratch path via the tool's
own `B1_SHEET_OUT` override and diffing against the live sheet gave **0 diffs**.
The sheet was exactly its source. So the fold went where the values are authored:

| value | was | now | authored in |
|---|---|---|---|
| `beat6.keys[t=4.0].lens_mm` | 19.5 | 22.0 | `docs/circuit_spec.json` |
| `beat6.keys[t=6.0].lens_mm` | 18.75 | 30.0 | `docs/circuit_spec.json` |
| `CLOSING_LENS_HOLD_START_MM` | 40.0 | 55.0 | `tools/build_beatsheet.py` |
| `CLOSING_LENS_HOLD_END_MM` | 74.0 | 130.0 | `tools/build_beatsheet.py` |
| `beat6.aim_keying` | absent | stride 2, bearing 5.0 deg | `docs/circuit_spec.json` |
| `aim.6_ending` | facade from t=+4.0, bound 32.0 | the car for the whole beat, bound 26.0 | `tools/author_beats2_5.py:beat6_aim` |

`aim_keying` is not decorative: `anim/build_camera_rig.py:917` reads
`sheet["beat6"]["aim_keying"]["max_stride_frames"]` and defaults it to 8. The
default never shortens on a smoothly-tracked beat 6, because the 5 deg bearing
test cannot fire when the whole beat moves the aim 2.9 deg.

**The old 40/74 mm rationale was not wrong, its premise expired.** It reasoned
about which lens makes the wound legible on a hold that was a *freeze*. With the
aim on the car the hold is no longer a freeze — the camera pans through it — so
the lens now lengthens onto the car (45.8 px -> 78.5 px over the last 3 s) and a
130 mm lens at 1,000 m crops the bare terrain out of frame. That is the client's
"patches in the land" answered by the lens rather than by a terrain rebuild. The
superseded values are recorded in `aim.6_ending.superseded` rather than deleted.

After the fold, regenerating produced **exactly** the intended diff and nothing
else: 15 changed leaves, all under `beat6` and `aim.6_ending`, and
`aim.6_ending` is byte-equal to the candidate's. The only remaining difference
against the candidate file is one sentence in `beat6.trajectory` describing the
candidate's own provenance ("this candidate moves lens and aim only"), which is
a note about a file and not a value of the film.

## R2-1703 — THE LAP-DOWN IS IN SOURCE, IN NO FILM, AND THE CAR BLEND IS WHY

`docs/NEXT-REBUILD.md` records the beat-6 lap-down as **"ALREADY IN SOURCE —
nothing to fold in; the rebuild picks it up by running the source."** That is
true and it is not sufficient, because the rebuild does **not** run that source
unless the car animation is rebuilt:

```
anim/carpath.py                     2026-08-07 08:40   LapDown, Car._extrap
anim/carrig.py                      2026-08-07 08:16   ground_distance, body_pitch/roll
world/R2829_car_anim.blend          2026-08-07 04:24   <- keyed BEFORE both
world/R2829_car_anim_driver.blend   2026-08-07 04:36   <- what film18 appended
```

The car's motion is **baked into keyframes** at `build_car_anim.py` time. A film
build that appends a pre-baked car cannot pick up a change to the path module,
however correct that module is. So film18 has no lap-down, and a rebuild that
reused the same car would not have one either — while every log line would read
clean, because nothing in the film build consults `carpath.py` at all.

"Already in source, picked up for free" is true **of the step that runs it**.
Naming that step is the difference between a change that lands and a change that
reads as landed. Same shape as R2-1701: an input that is a build product of an
earlier stage, and a later stage with no way to see that it is stale.

## R2-1704 — THE MANIFEST'S DRIVER LINE IS STALE, AND FOLLOWING IT WOULD REVERT THE RE-PACE

The manifest says to promote `work/r2881/car_anim_driver_R2881_BOTH.blend`,
"**NOT either half**". Measured on the candidates rather than read from the
change log:

| | paint v5 + imperfections, in order | helmet crown fix | cockpit surface (`r2cs`) | driver appears |
|---|---|---|---|---|
| `world/R2829_car_anim_driver.blend` | yes | yes | **no** | **f400 (re-paced)** |
| `work/r2881/car_anim_driver_R2881_BOTH.blend` | yes | yes | **yes** | **f580 (old schedule)** |

BOTH.blend was built off `world/car_anim.blend` (Aug 4), whose beat-1 assembly
predates the re-pace: all 15 clusters seat 60–180 frames later and its own
sidecar records `appear_frame: 580`. Promoting it would land the cockpit surface
and **silently revert the beat-1 re-pace**, violating "Order matters" items 3
and 4 — at f580 the driver pops in dead centre of a clean 6.7 m wide.

Neither candidate is shippable. The staging doc that produced BOTH already said
so (`docs/STAGING-R2-881-to-R2-910.md:433`): *"build from this one, **or re-run
`cockpit_surface.py` on whatever driver-fixed car is current** — not promote
either half alone."* The rebuild takes the second path, on a freshly rebuilt car
so the lap-down comes with it.

The two blends are the same byte size (408,417,476), which is worth recording
because it is the kind of coincidence that ends an investigation early. Their
sha256 differ.

## R2-1705 — THE LISTENER WAS ON A CAMERA THE FILM DOES NOT HAVE, AND THE FIX BELONGS IN THE CLASS

`docs/NEXT-REBUILD.md` records this as "`audio/master.py:117` builds
`CameraPath()` with **no argument** and gets the stale rig". The line has since
moved to 167 and the diagnosis is right, but the defect is one level down:

```python
# audio/scene.py:325, before
def __init__(self, path_json=None, fps=24):
    path_json = path_json or os.path.join(ROOT, "world", "camera_rig_path.json")
```

The stale file is the **class default**, so fixing the one call site in
`master.py` would have left the trap armed for every other caller. Fixed in
`audio/scene.py` instead: with no explicit path it now calls
`live_campath.load()`, which takes no path argument — so the wrong file is
unreachable rather than merely detectable — and which verifies the sha256 that
`docs/LIVE-CAMERA.md` pins, so a rebuild that changes the camera without
announcing it raises here instead of being adopted silently. An explicit
`path_json` is still honoured, for A/Bs and controls.

**Measured, on the two files, after the fix:**

```
max position divergence   9.866 m at f545
max lens divergence       23.0 mm
frames differing >0.01 m  749
divergence after f800     0.000000 m
```

Which is the manifest's account exactly, and it explains the audio symptom
without needing to trust the audio: the listener was up to 9.9 m from where the
camera actually was, for 749 frames of beat 1, and nowhere else in the film. The
binaural azimuth error of 178.1 deg on 318 of 792 frames is that, heard.

`CameraPath()` now returns 2,978 frames of the declared live camera. **The audio
master has not been re-rendered against it** — that is a separate deliverable and
another workstream is mid-edit in `audio/master.py`, `dsp.py`, `engine.py` and
`verify.py`. This change is the root fix, not the re-master, and the re-master
must happen after the film's camera is re-declared or it will bake in the
previous film's path.

## R2-1706 — THE BEAT-5 BRIDGE BLACKOUT IS IN SOURCE. The offset was carried, the file was not

`tools/author_beats2_5.py` now carries `pont_offset()` and applies it inside
`emit_keys`' own sampler. `docs/beat_sheet.json` has been regenerated through the
declared chain (`tools/build_beatsheet.py` then `tools/author_beats2_5.py`) and
reproduces exactly from source. **Nothing needs folding in and nothing needs
merging.** The manifest line in `docs/NEXT-REBUILD.md` has been rewritten from
"staged, not merged" to the same form the beat-6 lap-down line already has: the
rebuild picks it up by running the source.

**`render/film_path_R2971_PONT_B5_REBASED.json` was NOT adopted, and must not
be.** It is a whole-film path; adopting one reverts beat 1 by up to 9.866 m over
2,472 frames to buy twelve frames in beat 5 (R2-737, and R2-1004's own
"Defect 1"). What was carried across is the OFFSET, which is a pure function of
the frame index and therefore rebases exactly. Both superseded tools now say so
in their first paragraph, because both of them will double-apply against the
current sheet — 40 m inboard and 15 m down, through the parapet — and neither
selftest can see it:

```
tools/r2731_pont_camera_candidate.py   SUPERSEDED banner (and it had the OLD 22-frame ramp)
tools/r2971_pont_camera_rebase.py      "in source" banner; its base must be a pre-R2-1701 path
```

### Where it went, and why there and not somewhere else

Not `world/build_architecture.py`: the bridge is not the defect. R2-731 already
established that moving `PONT_S` does not close this — 2460 measures *worse*
(25 blocked frames against 12) because the abutment, not the deck, is what a low
outboard sightline hits, and the best station anywhere in the sweep is 8.

Not `anim/build_camera_rig.py`: the rig consumes the sheet, so a term added
there would be invisible to every render-free instrument that reads the sheet,
and to `tools/r2731_pont_camera_candidate.py`, which would then double-apply.

`tools/author_beats2_5.py` is where beat 5's camera is *authored*, so it is the
one place that survives a regeneration of `docs/beat_sheet.json` — which is the
requirement, since that file is regenerated and never hand-edited.

**Inside `sample()`, not as a post-pass on `world`.** That distinction is
load-bearing and it is a real defect in the candidate-sheet route:
`r2731_pont_camera_candidate.py` rewrites `world` only, which leaves
`focus_distance_m` pointing at where the camera used to be — 21 m away — and
leaves the adaptive walk spacing keys on a bearing the camera does not have.
Putting the term in the sampler makes the offset part of *where the camera is*,
so bearing, key spacing and focus distance all fall out of it. Beat 5 gains
exactly one key doing so (316 -> 317).

### A new anchor was the obvious move and it is the wrong one

An anchor is a Catmull-Rom control point: it pulls the spline for hundreds of
frames either side of itself and cannot be held interior to a 94-frame window.
The property everything below rests on is that this term is **exactly zero**,
not nearly zero, outside f2131-2224. That is what makes both beat-5 boundaries
bit-identical without anyone having to assert it afterwards, and what makes
beats 2, 3, 4 and the seam bridge emit the keys they always did.

### Measured, not asserted

Every number below is from a run made after the edit, and it is rerunnable:
**`.venv/bin/python tools/r2_1706_pont_source_verify.py`**, which must print
`>> STAGE RESULT: R21706_PONT_SOURCE_OK`. `tools/r2731_pont_full_sightline.py`
was run with its own unmodified `--selftest` first — it reproduces two
independent depth-tested raycasts at two different stations — and then over
**all four bridge bands**, girders/deck/parapet/mesh, so f2180's fence-channel
frame is included:

| | wholly hidden | partial |
|---|---|---|
| shipped, all four bands | **f2180-2191, 12 frames** | f2192, f2193 |
| **source, all four bands** | **none** | **none** |
| shipped, solid bands only | f2181-2191, 11 | f2192, f2193 |
| **source, solid bands only** | **none** | **none** |

Camera acceleration, over R2-740's own f2120-2240 window, on the built path so
it is comparable to every figure R2-1004 quoted:

| | peak v | peak abs a | |
|---|---:|---:|---|
| shipped `film17_path.json` | 88.32 m/s | **49.12 m/s^2 = 5.01 g** | at f2188 |
| **source** | 88.10 m/s | **47.66 m/s^2 = 4.86 g** | at f2199 |

**50 % of `author_beats2_5.py`'s own 95.9 m/s^2 craft limit, and below the
shipped path's own peak** — which is what R2-1004 widened the ramps to buy, and
it reproduces to the decimal place from source.

And an extra that R2-1004 did not have, because it was measuring a path and not
the author: on this file's per-frame spline across all of beats 2-5, **the worst
camera acceleration anywhere in the film was 61.94 m/s^2 at f2194** — inside
this window, put there by the bridge pass itself. With the thread it is
53.75 m/s^2 at f2560. The fix removes the film's worst authored acceleration
frame. Global worst speed (101.69 m/s at f1209) and worst camera-to-car box
distance (1.808 m at f2642) are unchanged to the digit.

### The sheet diff, checked rather than hoped

`docs/beat_sheet.json` regenerated to a scratch path first and diffed against
the pre-change copy:

```
only top-level block that differs .......... beat5
beat1, beat2, beat3, beat4, beat6 .......... identical
beat1_2_seam, aim, time_map, speed_ramps ... identical
beat6.hold_lens_mm ......................... 130.0   (another agent's, intact)
beat6.aim_keying ........................... present (another agent's, intact)
aim.6_ending.bound_deg ..................... 26.0    (another agent's, intact)
beat5.anchors .............................. identical
beat5.camera_keys .......................... 316 -> 317, differ f2138-2250
beat5.first key f1191 / last key f2641 ..... identical
```

The differing range runs to f2250, twenty-six frames past the support, and that
is **key re-phasing, not camera movement**: the adaptive walk lands on 2249
instead of 2250 and re-syncs shortly after. Checked directly — every key outside
f2131-2224 reproduces the **unmodified** spline to 7.8e-05 m, and every key
inside it reproduces spline-plus-offset to 6.7e-05 m. Both residuals are the
sheet's own 4-decimal rounding.

A `beat5.pont_thread` provenance block is written beside the keys, because a
reader holding only `beat5.anchors` cannot reproduce `beat5.camera_keys` any
more and should be told so rather than deriving the offset from the difference.

### Key density: checked, and deliberately left alone

The worry is real — a smootherstep ramp sampled too coarsely and then run
through Blender's AUTO_CLAMPED handles is exactly the failure this file's seam
bridge exists to fix. Measured instead of argued:

* the walk densifies on its own, because the offset is in the bearing it spaces
  on: through the ramps the gaps go 5-8 frames to 4-8;
* reconstructing the offset from the keys actually emitted is worst **0.259 m**
  against the exact curve;
* **the built path already differs from this file's own spline by 0.128 m over
  f2120-2240 before this term exists** — so the residual is inside the
  instrument that ships;
* the zero-blocked plateau is **6 m x 5 m** and the displacement sits in the
  middle of it, so 0.26 m cannot walk the fix off it;
* a displacement-per-key criterion was swept over seven settings: the best buys
  0.259 m -> 0.046 m for **21 extra keys** through the window and the milder
  ones buy almost nothing (0.16-0.23 m).

Not taken. Same verdict, same reasoning, as R2-087's rejection of a global speed
criterion in the same file — and unlike R2-087 the rejected option here does not
even relayout a beat, it just adds keys nobody needs.

### WHAT IS NOT VERIFIED, AND IT IS THE ONE THING A RIG BUILD WOULD ADD

**No rig was built.** Everything above is render-free: the offset, the sheet
diff, the key-level reproduction, the acceleration profile off the author's
spline, and the occlusion measured on `film17_path.json` plus the source's own
`pont_offset()` — which is bit-for-bit the candidate R2-1004 measured (worst
0.000e+00 m across all 2,978 frames, asserted).

What that does **not** close is the last hop: sheet keys -> Blender's
AUTO_CLAMPED bezier -> built path. The evidence that it is small is indirect but
it is measured and it is on this exact window: the shipped built path tracks the
author's spline to **0.128 m** over f2120-2240 with the same 5-8 frame spacing,
and it *smooths* the second derivative rather than sharpening it — 49.12 m/s^2
built against 61.94 on the spline. A term whose curvature scale is 32 frames is
not going to invert that. But it is inference, not a measurement, and the honest
statement is that the twelve frames are closed on the sheet and on the offset,
and confirmed on a built path only by construction.

The box has 11 GB of RAM with a world assembly and two probes already on it, so
no Blender was started. The check to run when a rebuild happens anyway — it
needs no world geometry, only the sheet, and it writes its own per-frame path:

```
blender -b -noaudio --factory-startup -P anim/build_camera_rig.py -- \
    --sheet docs/beat_sheet.json --telemetry telemetry/telemetry.csv \
    --out world/camera_rig.blend
# then, on world/camera_rig_path.json:
#   peak |a| over f2120-2240 should be <= 49.12 m/s^2
#   r2731_pont_full_sightline over all four bands should block 0 frames
```

Note that `world/camera_rig_path.json` is R2-1007's stale file and this is the
build that fixes it; read the live path through `tools/live_campath.py`, whose
`load()` takes no path argument, rather than by name.

## R2-1707 — assembly11, AND THE TWO WORLD ITEMS VERIFIED BY WHAT THE BUILD PRODUCED

`render/world/assembly/r2/assembly11.blend`, 7.12 GB, 2,118 s, all six modules
`ok=True`, `>> STAGE RESULT: ASSEMBLE_OK`. Promoted in `SHIPPING.md` under
R2-1701; `tools/shipping_world.py --selftest` passes with both its positive and
its three negative controls.

Rather than assert that the two stranded world changes landed, here is the
assembly10 -> assembly11 summary diff, which is free and is about the build's own
output rather than about its inputs:

| module | field | a10 | a11 | reading |
|---|---|---|---|---|
| surface | `procedural_texture_nodes_total` | 47 | **56** | the relief re-budget's stages |
| surface | `shader_nodes_total` | 1368 | **1462** | +94 |
| surface | `triangles` | 2,721,433 | **2,721,433** | **unchanged** |
| architecture | `base_tris` | 2,502,940 | **2,502,344** | **-596** |
| terrain | `sward_A/B/C`, `sward_drifts` | absent | 106,486 / 93,304 / 65,100 / 264,890 | R2-1661 |

**The asphalt relief re-budget is +94 shader nodes and ZERO triangles**, and
2,721,433 is the exact tri count `docs/NEXT-REBUILD.md` cites for it — the
manifest's "bit-identity survives (identical SHA256, 2,721,433 tris)" is
reproduced. Relief that moved geometry would have been the wrong fix.

**The beat-4 pit annexe is -596 triangles**, which is the right SIGN and the
right order for "the annexe loses one storey west of `PB_ANNEXE_X`". A storey
removed should subtract a small, structured amount from a 2.5 M-triangle
module, and it does.

Neither of these is a pixel measurement and neither is claimed as one. They are
enough to say the two changes are IN the world; whether the annexe closes the
six occluded frames is a frame question the manifest already answered on the
draft, and re-answering it is a render, not a build.

**One number moved that is not mine:** `items.stale_inputs` 3 -> 4, with
`items_refused: 0`. No item was refused and no registry row changed —
`world/build_items.py` and `world/items/PLACEMENT.json` both predate assembly10 and
were already in it. Recorded here because it belongs to the item campaign and
should not be discovered later as a surprise of this rebuild.

## R2-1822 — THE STALENESS GUARD COULD NOT SEE THE STALENESS THAT MATTERED, AND NOW REFUSES

assembly11 is stale against `world/build_terrain.py` (R2-1821's habitat/paving
fix), and its own summary proves it to the unit: `sward_drifts: 264890` is
R2-1661's figure exactly, so it read the pre-R2-1821 terrain.

**The mtime check cannot detect this, and nearly hid it:**

```
assembly11.blend  SAVED   22:40:16
world/build_terrain.py    22:25:31      <- OLDER than the save, so "fresh"
                                           but READ at ~22:06, 19 min before it changed
```

A save-time comparison is blind to a source edit that lands *during* a build.
The guard did fire on assembly11 — but only by luck, on an unrelated module
(`build_nearband.py`, 23:05). Had that module not appeared, film20 would have
been built on a stale world with the guard reporting "none".

Two changes, both in source:

1. **`assemble.py` records a CONTENT fingerprint at READ time** — sha256 of every
   `build_*.py`, `world_contract.py` and `itemkit.py`, written to
   `<blend>_build.json` **and stamped into the scene** as `world_source_sha256`,
   so the answer cannot be separated from the world it describes.
2. **`build_film_scene.py` REFUSES** instead of warning. The original docstring
   argued against refusing — *"a guard that must be routinely overridden teaches
   people to override guards"* — and that argument is right about **mtime**
   staleness, which fires when a file is merely re-saved. It is what made
   refusing unaffordable. Comparing CONTENT removes the false positives, so the
   refusal is rare enough to mean something. Assemblies predating this carry no
   fingerprint and fall back to mtime, which still refuses but says which arm
   spoke.

Tested against the shipped function: assembly10 REFUSE (5 modules), assembly11
REFUSE (1). `--world-override REASON` overrides deliberately and prints the
reason into the build log.

**A warning nobody can act on is not weaker than a refusal — it is a refusal
pre-overridden for everyone, permanently.** It printed on every film build for
days and film18 still shipped without four landed changes.

## R2-1824 — `build_nearband.py` EXISTS, TARGETS THE SAME CLIENT NOTE, AND IS IN NO ASSEMBLY

`world/build_nearband.py` (untracked, 23:05:40) is a complete module — 1,400+
lines, `build(ctx, quality, coll)`, its own `>> STAGE RESULT` lines — addressing
R2-1156: the band that `wood` evacuates, via `smoothstep(52.0, 150.0, D)`. That
is **the same client complaint** as R2-1821, one term further along.

**`assemble.py`'s MODS list is `surface,barriers,architecture,terrain,dressing,
items`. `nearband` is not in it, and nothing imports it.** So it is landed,
correct as far as anyone can tell, and structurally unable to reach a frame —
the film18 shape exactly, one day later.

**Not wired in by this rebuild, deliberately.** It is untracked and 30 minutes
old; adding an unreviewed module to the ship path on my own initiative is how a
world build breaks at 01:00. It needs one decision from its author: is it ready,
and does it run before or after `terrain`? assembly12 does **not** contain it.

## R2-1825 — THE BREACH PREFLIGHT CAN NEVER PASS ON A CORRECT FILM

`apply_breach` refused film19 on `glazing_pocket_clear`. The refusal is not new
and film18 did not hit it because film18's run passed `--force`.

The check lists ten intruders in the glazing pocket. **Three of them —
`GW_Right_Transom_0/1/2` — are round-1 solids that this same applier deletes and
replaces**, and its own report lists them under `deleted`. The preflight measures
the scene *before* the applier does the work that clears it, so it fails on every
correctly-built film. The other seven are on the SOUTH wall and the side fins,
not the breach wall.

`--force` is therefore correct here, and is passed with that reasoning written at
the call site rather than as a shrug. What replaces it as the real gate is the
applier's own post-build census, now asserted: `R5_intruders_over_the_wound_after`
must be empty and `east_frame`/`east_wall` must both PASS, **regardless of
`--force`**. On film18 that census read `[]`, PASS, PASS.

## R2-1826 — assembly12 WAS UNSOUND, AND THE INPUT GUARD SAID SO WITHOUT BEING TOLD

`assembly12` finished and my own build script refused it:

```
>> STAGE RESULT: ASSEMBLY12_UNSOUND (its own inputs changed under it;
   the artefact may carry a mixture of two source states -- rebuild)
```

The before/after input hash comparison (R2-1822) caught the two terrain fixes
landing mid-build **from the input side**, independently of and simultaneously
with the coordinator catching them **from the output side** (`sward_C 65,100`
unchanged). That is the same question asked at both ends, and it is worth noting
that neither alone is sufficient: the input guard cannot say whether a fix
reached the geometry, and the output check cannot say whether the build read one
source state or two.

assembly12 did carry R2-1821 — `sward_drifts` 264,890 -> 275,562 — and did not
carry the verge taper or tier C's fade. Both true at once, which is exactly what
"a mixture of two source states" means.

**assembly13's acceptance is now a NUMBER, not a timestamp**, and it is checked
in the build script itself:

```
sward_C            want 56063     (was 65,100; MUST fall)
grass_in_corridor  want 1386383   (MUST be identical; 1,370,543 = the holes are back)
```

The script exits `ASSEMBLY13_FIXES_PRESENT` or `ASSEMBLY13_FIXES_ABSENT`, and the
film chain behind it is gated on `FIXES_PRESENT` — **not on `BUILT`**. A world
that builds cleanly without the fixes must not become a film.

**Fewer clumps and more cover is not a contradiction** and is not chased here:
the verge band's outer half was laying a second layer on a sward already at full
weight, so deleting 340,645 clumps raises every measured region.

## R2-1827 — `build_nearband` IS WIRED IN, AND THE ORDER IS STRUCTURAL

`assemble.py`'s MODS is now
`surface,barriers,architecture,terrain,nearband,dressing,items`.

`nearband` cannot precede `terrain` and the reason is not preference: its
`capture_terrain` context manager wraps `Ground`, `GridZ`, `CameraPath`,
`Raster` and `build_library` **for the duration of terrain's own build** and
records the instances, so the near band is placed against THE SAME height field
the woodland was. A second `GridZ` on a coarser grid is a different height
field, and plants placed against it sit at a different z from the woodland they
are meant to blend into.

So the capture happens inside the `terrain` branch, not in a `nearband` branch
that runs later and re-derives anything. Two refusals guard it: the module order
is checked when MODS is parsed, and an incomplete capture raises rather than
building the tier against objects terrain did not make.

**A defect of my own, caught by its own log.** The first assembly13 attempt
printed `source fingerprint taken over 0 module(s)` — I had re-derived the world
directory from `__file__` and got the depth wrong, so the R2-1822 fingerprint
silently covered nothing. It is now the module-level `WORLD` constant that was
already resolved three lines away, and it reads 10 modules. An instrument that
reports emptiness as success is the shape this whole staging doc is about, and I
built one on the way to fixing one.
