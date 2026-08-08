# THE NEXT REBUILD — everything it must carry

The 4K master cannot start until one rebuild carries all of this. Anything
rendered before it is superseded by construction. Written 2026-08-07.

## Landed in SOURCE, in no film blend

| what | where | evidence |
|---|---|---|
| **Car paint** v5 + imperfections — **ALREADY IN film17_breach.blend, verified in the artefact** (R2-1145); the evidence below was measured on `film14_breach_r6.blend`, built BEFORE the repaint. `Metallic` reads default 0.62 but is LINKED through a MULTIPLY of 0.16129031777381897 = 0.10/0.62, so any checker reading `default_value` reports round 1 forever. | `world/car_paint.py`, `tools/imperfections.py`, applied to BOTH car sources | albedo 0.0121 -> 0.0372; head-on diffuse 2.78 -> 7.87 %; three-quarter 7.32 -> 19.96 % |
| **Driver + seat** | promote `work/r2881/car_anim_driver_R2881_BOTH.blend` — **NOT either half**, they were built in parallel off the same shipping car | crown boundary 44 px -> 2 px; black pixels on the crown tile 1,910 -> 0; carbon fine-band 0.99/0.17 -> 2.63/1.73 |
| **Showroom ceiling** | `world/showroom_ceiling.blend` (6.99 MB library); the three-line append is already in `tools/build_film_scene.py` | 21 objects, 73,996 polys, lighting identical at 46,203.313 W |
| **Beat-4 pit building** | `world/build_architecture.py` — annexe loses one storey west of `PB_ANNEXE_X` | 6 frames occluded -> 0, nothing anywhere worse, worst clearance 0.94 m against 0.02 m in the draft it replaced |
| **Beat-1 re-pace + re-frame** | `tools/build_beatsheet.py`, `world/beat1_anim.blend` regenerated | payoff 4.01 s -> 11.29 s; beats 2-6 frame-identical over 2,186 frames |
| **Beat-1 focus** | post-pass, keyed to subject not frame numbers | subject inside the 2 px budget 0.9 -> 45.0 % median; frames with nothing sharp 174/292 -> 86/292 |
| **Beat-6 ending re-key** | fold `docs/R2851_beat_sheet_CANDIDATE.json`'s `beat6` and `aim.6_ending` into `docs/beat_sheet.json` — the rebuild reads the SHEET, and the candidate is still a separate file | aim worst 0.029 deg at f2758 against a 26.0 bound; lens f2978 73.997 -> 129.993 mm |
| **Beat-6 lap-down (R2-943)** | ALREADY IN SOURCE — `anim/carpath.py` (`LapDown`, `Car._extrap`), `anim/carrig.py` (`ground_distance`, `body_pitch`, `body_roll`), `audio/scene.py`, `tools/car_anim_gate.py`. **Nothing to fold in; the rebuild picks it up by running the source.** | car at the last frame 79.0 -> 230.7 px; beats 1-5 bit-identical at 0.000e+00 m and 0.00000 deg through f2715; rolling contact exact to 1.35e-12 m |
| **Breach frost** | `sim/apply_breach.py --fracture-faces`, **off by default** — a material edit on `BREACH_Glass`, no geometry, not appendable | pending probe |
| **Breach fines** | `world/breach_fines.blend` (101.9 MB library) landed by **`apply_breach.py --fines-lib`** — NOT a `build_film_scene` append | round-trip EXACT: 11,246 of 11,246 objects, 2,844,012 of 2,844,012 keys, worst world-position error **1.70e-06 m = 0.0037 px**, **0** visibility mismatches across f866/880/900/930/1200/2978 |
| ~~**Asphalt relief re-budget**~~ **THIS ROW IS WRONG — SEE THE CORRECTION BELOW THE TABLE (R2-3061)** | `world/build_surface.py` — 7 stages spanning 3.7 mm–1.03 m, all inside the camera's readable band, all from `relief_amplitude_for`; the 0.6 mm stage moved to roughness; six meso structures via `amp_field` | octave contrast **2.70× at f2000**, 1.90× on the wide; bit-identity survives (identical SHA256, 2,721,433 tris). Milled-repair feather **1.6 m → 0.13 m** with a sealed lip — the client's "patches in the land", second instance |
| **Audio beat-1 camera** | `audio/master.py:117` builds `CameraPath()` with **no argument** and gets the stale rig. Beat 1's assembly layer is positional. | level error p50 **2.19 dB**, max 11.69; binaural azimuth max **178.1°** — the source is panned to the **wrong ear on 318 of 792 frames**. Beats 2–6 untouched |
| **Beat-5 bridge blackout** | **IN SOURCE, R2-1701** — `tools/author_beats2_5.py` `pont_offset()`, applied inside `emit_keys`' sampler, and `docs/beat_sheet.json` is regenerated with it. **Nothing to fold in; the rebuild picks it up by running the source.** `render/film_path_R2971_PONT_B5_REBASED.json` is evidence, not an artefact — **do not merge it or any other `film_path_*.json`** | occlusion **12 → 0** across all four bridge bands; acceleration 47.7 m/s² *below* the shipped 49.1; clearance 2.391 m against a 1.20 m sphere; boundaries bit-identical. Re-measured from source: identical, and the film's worst authored camera acceleration drops 61.94 m/s² at f2194 → 53.75 at f2560 |
| **Beat-5 framing re-pace** (promoted 2026-08-08 06:15) | `docs/beat_sheet.json` sha256 `d8825d84…` (was `7be83550…`). Diff vs snapshot is **`['beat5']` and nothing else** — `total_frames` 2978, `total_s` 124.1, `fps` 24, `time_map` and `beat6` bit-identical. **One continuous take, runtime untouched.** Regeneration is deterministic: `promo.json` came out byte-identical to the gated candidate | Post-promotion aim gate: **1 `STAGE RESULT` line, 0 FAIL lines**, `CAMERA_RIG_CONTINUOUS_AND_AIMED`, all six beats PASS, worst 12.02° at f2273 vs a 22.0 bound. The promoted rig's `_path.json` is bit-identical to the gated candidate's (`7fc6d688…`) — **the gate that passed is the gate on what is on disk** |

> **CORRECTION — THE ASPHALT RE-BUDGET IS NOT "IN NO FILM BLEND". IT IS IN BOTH
> OF THEM, AND HAS BEEN SINCE `assembly11`.** (R2-3061, 2026-08-08)
>
> ```
> tools/r2_3061_film_material.py --blend render/film22.blend
>   amp_field chip_hi offline ravel screed craze pluck h_hard   8/8 PRESENT
>   38-texture wavelength census identical to a fresh build of HEAD
>   >> STAGE RESULT: FILM_CARRIES_REBUDGET
>   ... and byte-for-byte the same on render/film23_breach.blend
> ```
>
> `assembly14_build.json` records `world/build_surface.py` at `678fdb3fa6a7…`,
> which is the blob at `244ff16`, and `git merge-base --is-ancestor cc38455
> 244ff16` confirms the re-budget commit is an ancestor of it. The only delta
> between that state and HEAD before R2-3061 was `76a685b`, which replaces four
> retyped car-box literals with `C.CAR_BODY_*` and is inert by its own
> measurement.
>
> **Why this row mattering is not bookkeeping:** it is the difference between
> "nothing to do, the rebuild carries the fix" and "this is unfixed and the
> rebuild reproduces it". `work/r22881` measured the delivered asphalt as the
> blankest large surface in the film *after* this change was already in it.
> **A rebuild off the source as it stood on 2026-08-08 06:00 would have shipped
> the same defect and looked like a fix.**
>
> R2-3065 authors the octave the re-budget did not reach — 45-160 mm, in albedo
> and roughness — in `world/build_surface.py`. **That IS a real "landed in
> source, in no film blend" item and the rebuild does need to pick it up.** See
> `docs/STAGING-R2-3061-to-R2-3120.md`.
>
> **AND IT IS UNPROVEN BY RENDER. SAY SO OUT LOUD RATHER THAN INHERITING IT.**
> The A/B rig (`world/r23061_nf_{before,after}.blend`, one camera, three film
> poses × shutter-open / camera-stopped) was built but never rendered: the shared
> build lock was held by a legitimately-working 9 GB assembly probe for the whole
> window. What exists instead of a measurement is a **prediction, written into
> the staging doc before any frame was rendered** — still arm 1.5-3×, live arm
> about half of that, f1787 tile (3,1) 0.00085 native → 0.0011-0.0018. That is a
> hypothesis on record, not a result, and the difference matters:
>
> * the change is **additive only** — 4 tags added, none removed, no existing
>   wavelength moved, 1129 → 1180 nodes — so it cannot break what it does not
>   touch, which is what makes shipping it unproven tolerable at all
> * **the first frames the rebuild renders settle it for free.** Run
>   `tools/r2_3061_judge.py` on any 4K frame in 1685-1688 / 1784-1787 / 2622 and
>   compare against the recorded before: 0.00069 proxy / 0.00085 native on tile
>   (3,1) at f1787, against a 0.0020 emptiness threshold and 0.00853 on the same
>   frame's verge
> * **if it lands below the predicted range the weights are too low, not the
>   approach wrong.** They were set from arithmetic (`sqrt(7.5² + 7.5² + 3.8²) /
>   7.5 = 1.5×` on albedo alone) and go up the same way. Do not re-derive the
>   design from a single disappointing number.

> **CORRECTION — "alters ONLY the camera's aim, never its position" is WRONG, and it
> was my sentence.** Measured on the two gated rig paths, at the rendered-frame level
> the beat-5 promotion moves:
>
> ```
> position   0.264 m    at f2584
> lens       1.41 mm    at f2244
> aim       12.045 deg  at f2273      all confined to f1195-f2677
> ```
>
> **Cause, and it is not a bug:** `beat5.camera_keys` goes 317 → 319 and most keys' `t`
> values shift by up to ~1/24 s, so the *interpolated* position between keys moves while
> every aggregate — speed max, accel max, clearance min, seam pin — reads unchanged.
> **That is precisely why no aggregate could see it.** Another instrument that reads the
> same whether the thing is there or not; the family now has more than a dozen members.
>
> **Two consequences for whoever rebuilds:** (1) an A/B of this change shows a camera that
> *moves* slightly as well as aims differently — **do not report that 0.264 m as a
> regression**; (2) any confinement measurement that treats beat 5 as positionally frozen
> will flag it. Beats 1-3 were **bit-identical** and beat 6 moved **0.00015°**; those are
> the real baselines. This also falsifies **R2-853**'s "every camera position
> byte-identical" for the *promoted* sheet — that claim was true of an earlier candidate.

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
slabcheck                  MUST exit 0.  It DOES, as of R2-1121 — and its
                           selftest is now 22 controls, all of which must stay
                           green.  Nothing in the sim or the bake changed to
                           get there; see the closed blocker below.
rig_preflight              any comparison rig used to judge this film must exit
                           0 — sun bearing, exposure, view transform, world
```

## ~~BLOCKER — decide bays 3 and 6 before building~~ CLOSED, R2-1121

**Decided: bays 3 and 6 STAY.** Judged at 4K/1:1 on the shipping camera, with
ground truth from the bake projected over the frames. Full working in
`docs/STAGING-R2-1121-to-R2-1150.md`.

**Nothing in the sim changed. `fracture_wall.npz` and `breach_film.npz` are
untouched, and the `BF_MUL05_S02 = 0.1449 m` guard still holds.** The edit is
`sim/fracture.py` (new `outcome_of` / `bay_outcomes`) and `sim/slabcheck.py`
(join on outcome, not on role).

**Do not repeat the "relabelling is free" reasoning — it is false, and it was
measured.** `fracture_pane` reads `pane.role` to pick `n_radial` (15 for
`destroyed`, 7 for `retained`), so re-deriving the role re-fractures the bay:
bay 3 goes 202 shards → 198 and bay 6 200 → 178, every polygon different, new
`GS_bNN_NNNNN` names, and the 20 MB bake table no longer addresses them. That
is a re-bake — **the same bill as making them leave**. One word was doing two
jobs: `role` is a *fracture-density input*, and the gate was reading it as an
*outcome assertion*. Bays 3 and 6 are `destroyed` **and** stay, and both are
true — they are next to the strike so they are radialled hard, and they each
keep a jamb so they do not go.

Why they stay, physically: **only `MUL05_S00` and `MUL05_S01` ever leave** the
east frame (3.93 m and 4.43 m, the segments below z ≈ 1.59). Every other
mullion segment in the wall peaks at ≤ 26 mm and returns to 0.000 m — including
mullions 4 and 6, which are *declared* `destroyed`. So bays 3 and 6 have both
jambs standing and were never struck (the car's impactors span y −1.085…+1.085,
which is bays 4 and 5). Option (b) was never "make two panes leave"; it was
"destroy the frame the 4.35 m aperture is currently framed by".

**See R2-1122 in the staging doc: mullions 4 and 6 are the same defect one level
up, and are NOT fixed.** Changing a mullion's `beat3` state changes `active` and
the constraint thresholds in `build_breach_sim`, so it is a re-bake. It belongs
to whoever next has a reason to re-bake. The take is right; the label is not.

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
