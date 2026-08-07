# THE NEXT REBUILD — everything it must carry

The 4K master cannot start until one rebuild carries all of this. Anything
rendered before it is superseded by construction. Written 2026-08-07.

## Landed in SOURCE, in no film blend

| what | where | evidence |
|---|---|---|
| **Car paint** v5 + imperfections | `world/car_paint.py`, `tools/imperfections.py`, applied to BOTH car sources | albedo 0.0121 -> 0.0372; head-on diffuse 2.78 -> 7.87 %; three-quarter 7.32 -> 19.96 % |
| **Driver + seat** | promote `work/r2881/car_anim_driver_R2881_BOTH.blend` — **NOT either half**, they were built in parallel off the same shipping car | crown boundary 44 px -> 2 px; black pixels on the crown tile 1,910 -> 0; carbon fine-band 0.99/0.17 -> 2.63/1.73 |
| **Showroom ceiling** | `world/showroom_ceiling.blend` (6.99 MB library); the three-line append is already in `tools/build_film_scene.py` | 21 objects, 73,996 polys, lighting identical at 46,203.313 W |
| **Beat-4 pit building** | `world/build_architecture.py` — annexe loses one storey west of `PB_ANNEXE_X` | 6 frames occluded -> 0, nothing anywhere worse, worst clearance 0.94 m against 0.02 m in the draft it replaced |
| **Beat-1 re-pace + re-frame** | `tools/build_beatsheet.py`, `world/beat1_anim.blend` regenerated | payoff 4.01 s -> 11.29 s; beats 2-6 frame-identical over 2,186 frames |
| **Beat-1 focus** | post-pass, keyed to subject not frame numbers | subject inside the 2 px budget 0.9 -> 45.0 % median; frames with nothing sharp 174/292 -> 86/292 |
| **Beat-6 ending re-key** | fold `docs/R2851_beat_sheet_CANDIDATE.json`'s `beat6` and `aim.6_ending` into `docs/beat_sheet.json` — the rebuild reads the SHEET, and the candidate is still a separate file | aim worst 0.029 deg at f2758 against a 26.0 bound; lens f2978 73.997 -> 129.993 mm |
| **Beat-6 lap-down (R2-943)** | ALREADY IN SOURCE — `anim/carpath.py` (`LapDown`, `Car._extrap`), `anim/carrig.py` (`ground_distance`, `body_pitch`, `body_roll`), `audio/scene.py`, `tools/car_anim_gate.py`. **Nothing to fold in; the rebuild picks it up by running the source.** | car at the last frame 79.0 -> 230.7 px; beats 1-5 bit-identical at 0.000e+00 m and 0.00000 deg through f2715; rolling contact exact to 1.35e-12 m |
| **Breach frost** | `sim/apply_breach.py --fracture-faces`, **off by default** — a material edit on `BREACH_Glass`, no geometry, not appendable | pending probe |
| **Breach fines** | `world/breach_fines.blend` (101.9 MB library) landed by **`apply_breach.py --fines-lib`** — NOT a `build_film_scene` append | round-trip EXACT: 11,246 of 11,246 objects, 2,844,012 of 2,844,012 keys, worst world-position error **1.70e-06 m = 0.0037 px**, **0** visibility mismatches across f866/880/900/930/1200/2978 |

**Why `apply_breach` and not `build_film_scene`:** the applier **already opens
the film once**, so the append lands inside a pass that was happening anyway -
no second film-sized open anywhere in the pipeline - and the fines end up
*inside* `BREACH` rather than as a sibling collection a later tool has to know
about. `--debris` is now **only** how the library is regenerated; `--debris` and
`--fines-lib` **refuse together**, because doing both would put two copies of
260,000 chips in the wound.

**f2978 is in the round-trip sample deliberately**: it proves CONSTANT
extrapolation survived the append, so the wound keeps its fallen glass through
beats 4-6 without a single extra key.

## THE PROBE BLENDS ARE THROWAWAY — DO NOT MERGE THEM

Two agents are independently producing 8 GB derivatives of the ship candidate:

```
film16_debris.blend   from film16_breach — fines + frosted fracture faces
film16_R2851.blend    from film16_breach — beat-6 re-key, lens and aim
```

**Neither is a merge candidate and neither should be promoted.** Both are
*probe artefacts* whose purpose is to measure one change in isolation. The
underlying changes are both expressed in SOURCE — `apply_breach.py --debris
--fracture-faces` and the beat-6 camera sheet — and **the rebuild runs the
source, in order, once.** There is no 8 GB three-way merge to do, and anyone
attempting one is reconciling two throwaways.

The rule generalises: **a derivative blend is evidence, not an artefact.**
Nothing on the ship path is ever produced by editing a film scene; it is
produced by running the build.

## Order matters

1. **Re-bind the sky after any camera rig rebuild.** `build_camera_rig` deletes
   every camera; `build_sky.bind_camera()` points two SCRIPTED drivers at the
   old one by ID; deleting it sets them to `None` and the decks silently
   "behave as a skybox" — build_sky's own docstring. **Assert zero dangling
   driver targets and fail loudly.** (R2-713)
2. **`imperfections.py` runs AFTER `car_paint.py`.** The reverse order orphans
   the upper layer and makes its own `--strip` a silent no-op.
3. **`beat1_anim.blend` MUST be regenerated** with any seat-schedule change, or
   parts silently desync from the camera.
3b. **`build_car_anim.py` must run AFTER the beat sheet carries the beat-6
   candidate, and it keys the lap-down for free** — `pose_series` reads
   `carpath.Car._extrap`, so no separate step and no re-key script is needed on
   the rebuild path. `work/r2941/rekey_film_R2943.py` exists only because the
   film is 8 GB and a candidate had to be judged without a rebuild; **it is
   evidence, not an artefact,** in exactly the sense this file's "THE PROBE
   BLENDS ARE THROWAWAY" section means. Do not promote anything it produces.
   The one thing to carry across is its check: `pose_series` accumulates wheel
   rotation from its FIRST sample, so it must be called over all 2,978 frames
   and never over a window (R2-947).
4. **`driver_figure`'s appearance frame moves to `--appear 400`** under the new
   pacing. At the shipped f580 the driver would pop in dead centre of a clean
   6.7 m wide. Exactly one window survives the re-pace: **f396-427, 1.33 s**,
   while the camera is tight on the rear wing. Re-gate against the NEW path,
   not `film14_path.json` — the existing gate cites a camera two generations old.
5. **Do not run `land_breach.sh` end to end.** Its stage 1 regenerates
   `breach_film.npz` from whatever raw bake sits in `sim/tmp/`, which can
   silently swap in a table where `BF_MUL05_S02` travels 55.35 m instead of
   0.1449 m. Invoke `apply_breach.py` directly with an explicit `--film`.

## Verification bar the new film must meet

```
46,203.313 W interior      from showroom_lighting.measure(), NOT a hand probe
23 _sl_base stamps         scene key is showroom_lighting_stops
scene_mark 3.628           assert_levelled PASS, called UNCONDITIONALLY
ONER  clip 0.05/200000     3840x2160, 24 fps, 1..2978, AgX, look None, -3.628
BF_MUL05_S02 = 0.1449 m    the guard that proves the right bake landed
socket audit               film16 PASS, film10 FAIL 27 (the control that makes
                           every other PASS non-vacuous — keep film10)
```

## Then the master

**180.0 h / $79.99** at 512 spp, or **160.7 h / ~$71.40** with
`adaptive_threshold 0.02` (measured visually free: mean delta 0.06, p99.9 of
1 level, 0.00 % of samples beyond 2). **Credit is $72.39.** 256 samples fits at
~$47 and is NOT taken — 17.5 % of samples move beyond 2 levels, which is a look
decision, not a budget one.

**Re-probe the changed beats before quoting a start figure.** Two of the six
per-beat rates were measured on beat 1 and beat 6, both of which this rebuild
changes. ~$0.44, 40 minutes.
