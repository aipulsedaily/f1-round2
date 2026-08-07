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
| **Asphalt relief re-budget** | `world/build_surface.py` — 7 stages spanning 3.7 mm–1.03 m, all inside the camera's readable band, all from `relief_amplitude_for`; the 0.6 mm stage moved to roughness; six meso structures via `amp_field` | octave contrast **2.70× at f2000**, 1.90× on the wide; bit-identity survives (identical SHA256, 2,721,433 tris). Milled-repair feather **1.6 m → 0.13 m** with a sealed lip — the client's "patches in the land", second instance |
| **Audio beat-1 camera** | `audio/master.py:117` builds `CameraPath()` with **no argument** and gets the stale rig. Beat 1's assembly layer is positional. | level error p50 **2.19 dB**, max 11.69; binaural azimuth max **178.1°** — the source is panned to the **wrong ear on 318 of 792 frames**. Beats 2–6 untouched |
| **Beat-5 bridge blackout** | `render/film_path_R2971_PONT_B5_REBASED.json` — **staged, not merged**, and needs folding into the sheet like the beat-6 re-key | occlusion **12 → 0** across all four bridge bands; acceleration 47.7 m/s² *below* the shipped 49.1; clearance 2.391 m against a 1.20 m sphere; boundaries bit-identical |

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

6. **Rebuild the camera rig from the CURRENT sheet, and check the artefact it
   writes.** `build_camera_rig.py:1585` names its output
   `splitext(--out)[0] + "_path.json"` — **the artefact's name is a side effect
   of an argument, so no build step owns it.** `world/camera_rig_path.json` is
   therefore three days stale (byte-identical to `film16_path.json`), and **43
   files read it against 1 that reads the live path.** Worse, `same_gen` still
   SKIPs at 2.597 m when pointed at `film17_path.json`: **the sheet has been
   re-authored since film17 was built**, so the live path is itself behind the
   document that defines it. Use `tools/live_campath.py` — its `load()` takes
   no path argument, so the wrong file is unreachable rather than merely
   detectable.

## Verification bar the new film must meet

```
46,203.313 W interior      from showroom_lighting.measure(), NOT a hand probe
23 _sl_base stamps         scene key is showroom_lighting_stops
scene_mark 3.628           assert_levelled PASS, called UNCONDITIONALLY
ONER  clip 0.05/200000     3840x2160, 24 fps, 1..2978, AgX, look None, -3.628
BF_MUL05_S02 = 0.1449 m    the guard that proves the right bake landed
socket audit               film16 PASS, film10 FAIL 27 (the control that makes
                           every other PASS non-vacuous — keep film10)
slabcheck                  MUST exit 0.  It exits 1 today: bays 3 and 6 are
                           role `destroyed` and read DID_NOT_MOVE at 0.9 % and
                           9.0 % vacated.  See the blocker below.
rig_preflight              any comparison rig used to judge this film must exit
                           0 — sun bearing, exposure, view transform, world
```

## BLOCKER — decide bays 3 and 6 before building

`slabcheck` now joins each bay's `role` to its `verdict` and **fails**. Bays 3
and 6 are tagged `destroyed` and do not break; their shard counts (202, 200)
match the *retained* bays (195, 183), not the bays that go (1531, 1485).

**This is a look call, not a correctness one.** Fractured-but-standing laminated
glass flanking the hole is physically right and may be better than four bays
leaving. Either make them leave (re-bake) or re-label them `retained` (free) —
but **the plan and the outcome must agree before a 7-day render starts**, and
they have disagreed for the life of the project without anything noticing.

## Then the master

**155.0 h**, measured — not 180.0 and not the 172.2 that stood here earlier.
`adaptive_threshold 0.02` saves **7.3 %**, not the ~11 % once assumed.

```
current card 47039886   $0.4488/hr   186.7 s/f   $70.06   short $1.96
cheap card   42731684   $0.3999/hr   203.1 s/f   $67.95   clear  $0.15
```

**Credit is $68.10, so the master fits by fifteen cents and only on the cheaper
card** — and broker 2 still has queued jobs drawing on the same balance. **The
ask to the client is ~$25.** 256 samples fits at ~$47 and is **not** taken: it
is a look decision, not a budget one, and it was declined as one.

**This section has now been wrong four times, always the same way** — a rate
measured on a small sample extrapolated across 2,978 frames. 510.5 s/f was the
wrong scene entirely (2.6× high); 196.5 omitted overhead; 219.3 was a cold start
divided by nine (11 % high). **And the fifth error is already staged:** both the
anchor and the probe measure `film16_breach.blend`, while the farm has served
`film17_breach.blend` since 06:09 on 08-07.

**Do not quote a start figure from this table.** What settles it: **one
contiguous beat, 200–300 frames, delivery spec, on the shipping blend**, read
off `frames.render_sec` — 11–17 h, **$5–7**. Host-to-host variance across the
13–14 rentals a master needs is unmeasured and is now worth more than the $2.11
the card choice is.
