# STAGING R2-3361 .. R2-3420 — the ship path's car is rebuilt, and film24 is the first film whose ending has a car in it

R2-3301 rebuilt `world/car_anim.blend` and proved beat 6 goes from 31.0 px and
91 frames empty to 81.0 px and none. **The ship path does not append that file.**
`film22` and `film23` both override `build_film_scene`'s `--car` default with
`world/R22041_car_anim_driver_CS.blend`, and that car is 678.031 m adrift at the
film's last frame. This block rebuilds *that* car, on the corrected keys, with
its four content passes intact, and builds `render/film24_breach.blend` on it.

---

## R2-3361 — THE CHAIN IN R2-3308 IS WRONG ABOUT LINK 5, AND THE CORRECTION NAMES THE ACTUAL MISTAKE

R2-3308 records a five-link chain of in-place edits and says **"not one link
re-keys `CAR_ROOT`"**. The producing logs say otherwise. Read verbatim off the
`[cockpit] in` / `Read blend:` lines of the runs that made each file:

| artefact | its parent, from the producing log |
| --- | --- |
| `work/r2881/car_anim_driver_R2881.blend` | `world/car_anim.blend` (`work/r2881/place_driver.log:1`) |
| `work/r2881/car_anim_driver_R2881_BOTH.blend` | `work/r2881/car_anim_driver_R2881.blend` (`work/r2881/both.log:2`) |
| `world/R2829_car_anim_driver.blend` | `world/R2829_car_anim.blend` (`work/r2840/chain2.sh:54`) |
| `world/R21701_car_anim_driver_CS.blend` | `world/R21701_car_anim_driver.blend` (`work/r21701/cockpit_surface.log:2`) |
| **`world/R22041_car_anim_driver_CS.blend`** | **`world/R2829_car_anim_driver.blend`** (`work/r22041/car_cs.log:2`) |

It is not a chain. It is a **DAG that forks twice**, and the fork is the defect.

**`work/r21701/chain.sh` DID re-key.** It exists for exactly that reason — its
header says so — and `work/r21701/lapdown_evidence.txt` measures it landing:

```
[A2] largest separation      678.03 m at f2978
     first frame that moves  f2715   (t_brake is world 72.6296 s)
     PASS the tail separates by 678.0 m -- LapDown landed in the keys
```

**R2-2041 then ran `tools/cockpit_surface.py` on `world/R2829_car_anim_driver.blend`
— the pre-lap-down parent — and threw R2-1701's re-key away.** The 678.0 m
`car_staleness --keys` reports on the ship car today is numerically the same
678.03 m R2-1701 measured itself putting *in*, nineteen hours earlier.

So the ship car is stale because **one ad-hoc invocation took the wrong parent**,
not because five links drifted. `world/car_anim_driver_R2881_BOTH.blend` and
`world/R21701_car_anim_driver_CS.blend` are dead siblings that never fed the film.

This matters beyond bookkeeping: R2-3308's framing implies the fix is a
five-stage re-derivation nobody had ever run. It is not. **`work/r21701/chain.sh`
is a working, documented, five-stage recipe that produced a correct car**, and
the rebuild below is that script with the promoted beat 1, the live sheet's
camera, and one stage fewer.

### Two of the four passes have collapsed into one invocation

`tools/cockpit_surface.py:121` now reads
`TARGET_MATERIALS = ("CarbonMatte", "SuedeGrip", "CarbonFibre")`. **`CarbonFibre`
is what R2-2041 added.** So R2-1701's cockpit pass and R2-2041's carbon pass are
the same call today, and R2-3311's "four passes" is **three tools, one of which
does two of the jobs**. The rebuild is five stages, not six.

`cockpit_surface.py` refuses on an already-treated material
(`FAIL_ALREADY_APPLIED`, `REC_KEY = "r2cs"`), which is the guard against running
the chain twice — and against feeding it any `*_CS.blend` by mistake.

---

## R2-3362 — THE REBUILD. Five stages, and a bytes probe that refuses if a pass is missing

`work/r2-3361/rebuild_driver_car.sh`, one hold of the big lane, **zero frames
rendered**. Every stage judged on its own printed `>> STAGE RESULT:` line, with
a `need()` that refuses on any `_FAIL` / `_REFUSED` / `FAIL_ALREADY_APPLIED` /
`FAIL_WOULD_OVERWRITE_INPUT` anywhere in that stage's log — a FAIL followed by a
later PASS must not read as a pass.

```
0/7  sample the SHIPPED driver car on disk   -> driver_measured_BEFORE.json
1/7  anim/build_car_anim.py on beat1_anim    -> world/car_anim_R2_3361_base.blend
2/7  tools/place_driver.py --appear 400      -> world/car_anim_driver_R2_3361.blend
3/7  world/car_paint.py --save                                 R2521_CARPAINT_APPLY_OK
4/7  tools/imperfections.py --out                              IMPERFECTIONS_OK
5/7  tools/cockpit_surface.py                -> world/R2_3361_car_anim_driver_CS.blend
6/7  tools/car_staleness.py --keys                             CAR_KEYS_MATCH_SOURCE
7/7  sample the new blend                    -> driver_measured_AFTER.json
```

`F1_LAPDOWN` is **unset, never exported as 0** — `carpath.py:65` defaults it on,
and exporting 0 rebuilds the defect.

`world/beat1_anim.blend` is byte-identical to `world/R2829_beat1_anim.blend`
(md5 `f4e836c650c8e1bd4970aba5d7dee90f`, checked, not assumed), so the promoted
beat 1 and the beat 1 R2-1701 built on are the same artefact and the
`--anim world/beat1_anim_anim.json` sidecar is the promoted copy of R2829's,
differing only in two provenance fields.

### Every link matches its historical counterpart's byte count exactly

| stage | this build | the equivalent artefact on the old path | bytes |
| --- | --- | --- | --- |
| after `build_car_anim` | `car_anim_R2_3361_base.blend` | `R21701_car_anim.blend` / `R2829_car_anim.blend` | **300,235,801** |
| after driver + paint + imperfections | `car_anim_driver_R2_3361.blend` | `R21701_car_anim_driver.blend` / `R2829_car_anim_driver.blend` | **408,417,476** |
| after the cockpit surface | **`R2_3361_car_anim_driver_CS.blend`** | **`R22041_car_anim_driver_CS.blend`** | **408,590,498** |

That is corroboration and not proof, but it is exactly the corroboration you
want from a chain whose whole risk was silently dropping a pass.

### The driver placement reproduces R2-1701's, number for number

```
[place_driver] SOLVED H-point (CAR_ROOT-local) [0.198, 0.0, 0.18]  (hip raise +0.0000 m)
[place_driver]   crown_above_rim_m  +0.1472   crown_below_halo_apex_m  +0.0055
>> driver_figure: 10 objects, 1621350 triangles, 38.1 s
[place_driver] MESH CHECK  helmet crown predicted 0.8770, measured 0.8954 (delta +18.4 mm)
[place_driver] CROWN CORRECTION: ... crown now 0.8770 (delta -0.00 mm)
[place_driver] TRIM ... 189780 of 817272 faces removed (23.22 %)
[place_driver] APPEARANCE frame 400; figure on screen at 0 of the 17 frames 392..408
[place_driver] CAR GUARD: 0 of 70 witness samples changed
[place_driver] CAR now carries 11 DRV_* objects
```

**`--appear 400`, gated against THIS build's camera and not a superseded one.**
Under the beat-1 re-pace the only surviving offscreen window is f396-427; the
shipped 580 pops the driver dead centre of a clean 6.7 m wide. The gate was
pre-checked against three camera paths before the 40-minute chain was started
(0 of 17 on screen under all three), so the run was not gambled.

### THE BYTES PROBE, AND IT IS DIFFERENTIAL RATHER THAN A LIST OF REMEMBERED CONSTANTS

`work/r2-3361/passprobe.py`. A rebuild that runs the builder alone is
geometrically perfect and **visually round 1**, and every gate stays green
because round 1's chromed shell is a legal material. So the probe is run on the
SHIPPED car and on the REBUILD and the two fingerprints are compared. A constant
copied out of a four-day-old log is the kind of evidence this project keeps
discovering was about a different file; the shipped artefact is definitionally
what shipped.

```
>> SHIPPED  R22041_car_anim_driver_CS.blend (408590498 bytes)
>> REBUILD  R2_3361_car_anim_driver_CS.blend (408590498 bytes)

DRV_objects                  shipped  11  rebuild  11   ok
r2imp_materials              shipped  13  rebuild  13   ok
r2cs_materials               shipped   3  rebuild   3   ok
materials                    shipped  65  rebuild  65   ok
CI_meshes                    shipped  15  rebuild  15   ok
LiveryPaint_R2CP_VERSION     shipped 5              rebuild 5               ok
R2_Imperfection_group        shipped True           rebuild True            ok
DRV_Install_type             shipped 'EMPTY'        rebuild 'EMPTY'         ok
DRV_triangles                shipped 1245877        rebuild 1245877         ok
LiveryPaint_R2CP_nodes       shipped 94             rebuild 94              ok
LiveryPaint_nodes            shipped 239            rebuild 239             ok
CI_sharp_edges               shipped 28261          rebuild 28261           ok
DRV_Helmet_crown_local_z     shipped 0.877          rebuild 0.877           ok
R2IMP_node_counts            13 material(s); per-item diffs: NONE
R2CS_node_counts             1 material(s);  per-item diffs: NONE
DRV_faces                    10 object(s);   per-item diffs: NONE

>> STAGE RESULT: R2_3361_PASSES_PRESENT
```

**All four passes present, on every axis, against the shipped car itself.**
`r2cs` on three materials is R2-1701's two plus R2-2041's `CarbonFibre`.
`CI_sharp_edges` at 28,261 is the cockpit pass's own published figure (unfixed
is 57,362, of which 29,101 sit in the 36-60° false band). `DRV_Helmet`'s crown
at 0.877 in CAR_ROOT-local is the R2-882 crown fix — round 1's helmet has a
30 mm hole in the top of it and no apex vertex at all.

---

## R2-3363 — BEATS 1-5 DID NOT MOVE, BY EQUALITY. And f2715 is not zero and is not rounded away

`work/r2-3361/confinement.py`, `matrix_world` to `matrix_world` between the
shipped driver car and this rebuild, **by equality and not by a tolerance**,
because a tolerance here would hide the one thing the file exists to detect.

```
span                            frames     d loc (m)   d rot (deg)  d contact (m)  d spin (rad)  d steer (deg)
1_assembly                         792  0.000000e+00  0.000000e+00   0.000000e+00  0.000000e+00   0.000000e+00
2_launch                            72  0.000000e+00  0.000000e+00   0.000000e+00  0.000000e+00   0.000000e+00
3_breach                           192  0.000000e+00  0.000000e+00   0.000000e+00  0.000000e+00   0.000000e+00
4_transit                          134  0.000000e+00  0.000000e+00   0.000000e+00  0.000000e+00   0.000000e+00
5_lap                             1524  0.000000e+00  0.000000e+00   0.000000e+00  0.000000e+00   0.000000e+00
6_ending                           264  6.780306e+02  2.160537e+02   6.800166e+02  2.108988e+03   7.326407e+00
CONFINED 1-2714                   2714  0.000000e+00  0.000000e+00   0.000000e+00  0.000000e+00   0.000000e+00
TAIL 2715-2978                     264  6.780306e+02  2.160537e+02   6.800166e+02  2.108988e+03   7.326407e+00
```

**Frames differing on ANY of the five channels: 0 of 2714.** Not "below
tolerance" — bitwise equal on location, XYZ Euler, all four contact patches, all
four spin F-curves and all four steer F-curves.

The beat-1 witness block reads **0.000 m** here, unlike R2-3301's 2.902 m: both
cars descend from the same `beat1_anim.blend`, so there is no promoted-seat-
schedule term in this comparison at all.

### THE BOUNDARY IS f2714, AND THE RECORD HAS BEEN WRONG ABOUT IT TWICE

`work/r2-3301/confinement.py` sets `BOUNDARY = 2715` on the reasoning that beat 6
starts at f2715 so f2715 is the frame the two arms share. **It then printed
`CONFINEMENT_BROKEN` on a build everybody agrees is correct**, because f2715 is
not zero. This file sets `BOUNDARY = 2714` and reports f2715 separately.

```
    f2712   d loc 0.000000e+00 m   d rot 0.000000e+00 deg
    f2713   d loc 0.000000e+00 m   d rot 0.000000e+00 deg
    f2714   d loc 0.000000e+00 m   d rot 0.000000e+00 deg  <-- LAST BIT-IDENTICAL FRAME
    f2715   d loc 1.525879e-05 m   d rot 3.652131e-02 deg  <-- t_brake has bitten
    f2716   d loc 1.840442e-03 m   d rot 2.511602e-01 deg
```

```
f2715 IS NOT ZERO AND IS NOT ROUNDED AWAY
    dx +0.000e+00   dy -1.526e-05   dz -1.304e-08   (m)
    d roll +2.501e-09   d pitch +3.652e-02   d yaw +3.415e-06   (deg)
    one float32 ULP at y = 171.1836 is 1.5259e-05 m; |dy| = 1.5259e-05 m -> EXACTLY ONE ULP
    (float64 ulp at that magnitude, for contrast: 2.842e-14)
    PRICED: camera 87.3 m away on a 24.00 mm lens; 6.374e-04 rad about the box's 3.017 m worst arm
             = 1.9231 mm of on-car displacement = 0.0564 px at 4K
```

* **The position is not a difference.** `-1.526e-05 m` is *exactly* one float32
  ULP at `y = 171.1836`, computed by bit-incrementing the float32 rather than
  asserted. `dx` is exactly zero.
* **The pitch is a real difference with a named mechanism.** `carrig.body_pitch`
  returns the telemetry column while `t <= t_end` and the lap-down's closed form
  after it; `carpath._extrap` runs **flat out to the start/finish line and brakes
  only then**, so the onset is `t_brake`, which falls between f2714 and f2715.
  f2714 reads exactly zero not by luck but because it is already past `t_end` and
  before `t_brake`: the new build takes the lap-down branch and gets 0.0 out of
  it while the old build took its flat-0.0 past-telemetry branch. **Two different
  mechanisms returning the same number.**
* **0.0564 px at 4K.** Invisible, and still not zero — which is why it is
  reported as a difference rather than rounded into the claim it contradicts.

> **This is NOT `build_camera_rig.py`'s 0.203411 deg noise floor.** That floor
> belongs to the camera rig's rotation solve. `CAR_ROOT`'s keys come out of
> deterministic arithmetic on the telemetry — no solver anywhere on this path.
> A number being smaller than somebody else's noise does not make it noise.

---

## R2-3364 — `tools/car_anim_gate.py`: `CAR_ANIM_FAIL` -> `CAR_ANIM_OK`, and a contact patch 3.2 m under the road

Run on the two dumps taken off the two artefacts today, not quoted.

| | BEFORE — the shipped driver car | AFTER — this rebuild |
| --- | --- | --- |
| **A** wheel rotation | 14026.0 rad (2232.3 rev) | **11917.0 rad (1896.6 rev)** |
| **B** ground travelled | 5046.05 m | **4286.82 m** |
| **C** sanctioned launch wheelspin | 9.13984 rad (1.4547 rev) from f818 | **9.13984 rad (1.4547 rev)** — untouched |
| **E** worst contact patch vs the road | **-3.2062 m at f2977 FR**, rms 0.3051 m | **+0.0036 m at f850 RL**, rms 0.0001 m |
| **F** beat 1 vs its rest pose | 3.58e-09 m | 3.58e-09 m |
| verdict | **`CAR_ANIM_FAIL`** | **`CAR_ANIM_OK`** |

**E is the finding nobody had connected to the ending.** On the shipped car a
tyre sits **3.2 metres below the road** at f2977 — it is not braking, it is
streaking on at 89.767 m/s past the point where the road turns under it. The
rebuild brakes, and the wheels follow it: rolling contact and the sanctioned
launch slip window both survive a change that moved the car 678 m.

`tools/car_staleness.py` on the finished artefact:

```
>> CAR KEYS: none - the appended CAR_ROOT matches anim/carrig to 0.0000 m over 6
   probe frames spanning the confined span AND the lap-down
   (f1200 0.000, f2000 0.000, f2714 0.000, f2760 0.000, f2850 0.000, f2978 0.000)
>> STAGE RESULT: CAR_KEYS_MATCH_SOURCE
>> stamped world/R2_3361_car_anim_driver_CS_car.json over 10 source module(s)
     docs/beat_sheet.json         1abee787a8044f35
>> STAGE RESULT: CAR_FRESH
```

The three probes past `t_brake` are the ones that fail on the shipped file at
43.490 / 247.075 / 678.031 m. The three inside the confined span are what make a
PASS mean something: a check that only looks where the lap-down bites cannot tell
"this car is stale" from "this is not the film's car at all".

---

## R2-3365 — BEAT 6 ON THE DELIVERED PIXELS. 81.0 px, 0 frames off, and the last frame is in shot

`work/r2-3361/beat6_subject.py`. Box, camera basis, sensor and projection all
**imported** from `tools/lap_shotscale.py`; nothing retyped. Both arms measured
as the author's MODEL and as the ARTEFACT — `CAR_ROOT`'s `matrix_world` off the
saved blend.

**Measured on `render/film23_path.json`**, the camera the 31.0 px and 81.0 px
figures were established on, so the comparison is against the target and not
against a camera chosen after the fact:

| beat 6, f2715-f2978, ON THE ARTEFACT | SHIPPED `R22041_..._CS` | **REBUILT `R2_3361_..._CS`** |
| --- | --- | --- |
| **car WIDTH p50 @4K** | **31.0 px** | **81.0 px** |
| car width min / max | 15.9 / 153.5 | **53.5** / 244.1 |
| box HEIGHT p50 @4K | 19.2 px | **37.0 px** |
| **frames under 60 px — WIDTH** | **211/264 = 79.9 %** | **54/264 = 20.5 %** |
| **frames under 60 px — HEIGHT** | **253/264 = 95.8 %** | **207/264 = 78.4 %** |
| **frames WHOLLY OFF FRAME** | **91/264 = 34.5 %, 3.79 s** | **0/264 = 0.0 %** |
| first wholly-off frame | **f2888**, and it never returns | — none — |
| **the film's last frame f2978 in shot** | **NO** | **YES** |

**81.0 px on the nose, and 0 of 264 wholly off.** The two "under 60 px" rows are
printed separately and labelled, because R2-3181 reported *"frames under 60 px
95.8 %"* beside *"car size 31.0 px p50"* and those two numbers are about
different axes — the 95.8 % is the box HEIGHT and the 31.0 px is the WIDTH.

The four-way cross-check that says every figure is off the blends and not off
the models:

```
SHIPPED artefact vs MODEL --car built    worst 3.243e-05 m over 264 frames
SHIPPED artefact vs MODEL --car source   worst 6.780e+02 m
REBUILT artefact vs MODEL --car built    worst 6.780e+02 m
REBUILT artefact vs MODEL --car source   worst 2.108e-05 m
```

Each blend agrees with exactly one arm to ~2e-05 m and disagrees with the other
by 678 m. **The rebuild keyed the source. The shipped car did not.**

**Re-measured on the live-sheet rig** (`world/R2_3361_camera_rig_path.json`,
what film24 carries) the whole table is **identical to the last digit** — because
beat 6's camera is the one beat the two sheets agree on. That is stated rather
than assumed, per beat:

```
1_assembly   d camera position   0.0000 m   d lens 7.0270 mm
2_launch     d camera position   0.0000 m   d lens 0.0000 mm
3_breach     d camera position   0.0000 m   d lens 0.0000 mm
4_transit    d camera position   0.0000 m   d lens 0.0000 mm
5_lap        d camera position   0.2639 m   d lens 1.4069 mm   (at f2584)
6_ending     d camera position   0.0000 m   d lens 0.0000 mm
```

So the live sheet's two re-paces are beat 1's payoff orbit and beat 5's, exactly
as declared, and **beat 6's closing lens was already in film23's rig.** The
81.0 px is therefore a statement about the CAR and not about a camera change.

---

## R2-3366 — film24, and the one judgement call, which is not buried

`render/world/assembly/r2/v128/{run_rebuild24.sh, build_breach24.sh, verify_film24.sh}`
— a **new v128**, so `v127/verify_film23.sh` (leased by `r2-3121-bar-close`) is
run and never edited, and `work/r22101` — film23's only evidence that it passed
40/40 — is never written to. `W=work/r23361` throughout.

`render/film23_breach.blend` is **not touched, and that is measured rather than
promised**: its sha16 is taken before the run and re-taken at the end, and a
difference FAILS the build.

Two things differ from film23 and only two:

1. **The car** — `world/R2_3361_car_anim_driver_CS.blend`, asserted
   `CAR_KEYS_MATCH_SOURCE` at stage 0/4 before anything expensive runs.
2. **The camera** — `build_film_scene` rebuilds the rig in-process from
   `--sheet` on every build (`tools/build_film_scene.py:633`), so the live
   `docs/beat_sheet.json` at `1abee787a8044f35` is what carries the two
   re-paces. The build refuses if `render/film24_path.json` comes out at
   `363e4e88b30207ad`, which is the sha film22 and film23 share — if it did, the
   rig did not read the sheet.

The sheet's sha is now **in the film's provenance**: `docs/beat_sheet.json` is
added to the `sha256sum` block (v127's list omitted it, so the one input the
film exists to pick up was the one input its record did not name), alongside the
telemetry, the spec, `build_camera_rig.py`, `carpath.py`, `carrig.py`, the
assembly and the car.

### THE WORLD IS STALE, AND film24 IS BUILT ON IT DELIBERATELY

`build_film_scene.report_world_staleness` (R2-1822) refuses to build on a world
that is not what its own source would produce. **film23 passed it clean at
06:10** — *"assembly14.blend matches its recorded source fingerprint over 10
module(s)"*. **It no longer does.** Measured today, 2 of those 10 differ:

| module | assembly14 read | now |
| --- | --- | --- |
| `world/build_surface.py` | `678fdb3f` | `9b5d6fb2` — a **landed, committed** change (R2-3061..R2-3066, the asphalt re-budget and its partial revert) |
| `world/build_terrain.py` | `991b15a0` | HEAD is `258048f7`, **worktree is `d09ac2a8`** — assembly14 was built from a state of that file that **never landed**, and it carries 1,101 uncommitted lines right now belonging to another agent |

This is a real, newly-opened finding. It is **not** an artefact of this rebuild:
it became true the moment those two modules moved, and it is as true of
`film23_breach.blend` as of film24.

Two ways to clear it, and only one is honest here:

* **Rebuild assembly14.** REJECTED, and not on cost. `build_terrain.py` carries
  1,101 lines of somebody else's in-flight work; rebuilding now would bake
  unlanded source into the ship candidate, which is a *worse* instance of exactly
  the defect the gate exists to prevent. It would also change the world under a
  film whose entire purpose is to isolate the car and the camera, so beat 6's
  before/after would stop being a comparison.
* **`--world-override`, with the reason on the record.** TAKEN. The reason string
  is in `run_rebuild24.sh` and is printed into `work/r23361/build_film24.log`.

> **THIS IS NOT A CLEARED WARNING.** The world's staleness is unfixed. It needs
> an **assembly15**, rebuilt from landed source, before the 4K master — and that
> is a prescription this block opens, not one it closes.

### The bar's prediction, printed BEFORE the build

`tools/film_bar.py`'s `FILM23` is **film23's** prediction. Judging film24 by it
would be moving the goalposts even though the two agree to the last digit — the
value of the number is that it was computed from arithmetic before the artefact
existed, and film23's was computed before a *different* artefact existed.

`work/r23361/PREDICTION_film24_20260808T185912Z.log`, timestamped **before**
stage 1 started at 19:03:39:

```
      50.0 W nominal / luma(COLD) 0.931576 = 53.6725 W
      radiance 47.4569   bound 60.0   margin 20.9 %
      levelled: 53.6725 W x 12.363369 = 663.5727 W added to the interior load
      PREDICTION for the built film: interior_lamp_watts 46203.313 -> 46866.886,
      n_lamp_stamps 23 -> 24
```

That is `FILM24` in `tools/film_bar.py`, selected by a new `--want film24`.
`FILM23` is untouched and `--want` defaults to `film23`, so no existing caller
changes meaning. **They agree because the prediction is a function of the
SHOWROOM, not of the car** — and that is checked, not assumed: both the shipped
and the rebuilt car carry the same 23 `LIGHT` objects with the same names, none
of them inside `showroom_lighting.SHELL` (`work/r23361/lampcheck.log`). If a
future film ever adds one, the `46203.313` baseline literal inside
`world/showroom_strip.py` is wrong and the dict must be re-derived, not copied.

### The 10.9 GB breach bake is NOT redone

`sim/breachlib.py` reads the car only for beat 3, f865-1056. The confinement
table's `3_breach` row is **`0.000000e+00` on every one of the five channels over
all 192 frames**, so `sim/out/breach_film.npz` describes this car exactly as well
as it described the last one. `build_breach24.sh` re-uses it unchanged, and says
so in its header.

---

## R2-3367 — film24 stage 1, and the campath identity that licenses the driver's appearance gate

```
>> WORLD STALENESS: assembly14.blend was built from a DIFFERENT source state.
   2 module(s) differ by content: world/build_surface.py, world/build_terrain.py.
   A rebuilt assembly would not be this file.
>> WORLD STALENESS OVERRIDDEN deliberately: R2-3361: film24 isolates the car and
   the camera and is built on the SAME assembly14 artefact as film23 ...
>> appended CAR (636 objects) from world/R2_3361_car_anim_driver_CS.blend in 62.8 s
>> showroom_strip: ADDED R2_Strip  3.60 x 0.10 m (0.3600 m2), 53.6725 W,
   radiance 47.46 (bound 60.0), spread 100 deg, in 'LIGHTS'
>> ONER camera: 637 keys over 2978 frames (124.1 s) at 3840x2160
>> STAGE RESULT: CAMERA_RIG_CONTINUOUS_AND_AIMED
```

`render/film24.blend` is 10,007,783,631 bytes. The refusal fired, was overridden
with the reason on the record, and **the reason is in the build log** — not only
in the script that passed it.

### `render/film24_path.json` sha16 = `9d055d63da724993`

Three things fall out of that one number, and the third is the one that matters:

1. **It is not `363e4e88b30207ad`**, the sha `render/film22_path.json` and
   `render/film23_path.json` share. The in-process rig read the live sheet.
2. It is **byte-identical to `world/R2_3361_camera_rig_path.json`**, the
   standalone rig built at 18:52 from the same sheet by the same module.
3. **Therefore the camera `tools/place_driver.py`'s appearance gate was run
   against IS the camera film24 carries.** That gate is the reason `--appear
   400` is safe — the driver must pop into existence while off screen — and
   `place_driver.py:782` warns in as many words that a PASS against a superseded
   camera *"is not evidence about the film being built"*. The film did not exist
   when the car was built, so the standalone rig was built first and the two
   were proved equal afterwards rather than assumed. `work/r2840/campath_identity.py`
   does the same job for the R2829 generation; this is that check, closed by
   sha rather than by tolerance.

---

## R2-3368 — the focus and the breach, and the bake that was correctly not redone

**Stage 2, focus** — `>> STAGE RESULT R2791_APPLY_OK keys=621 guard=clean maxstep=0.3059`.

**Stage 3, breach** — `render/film24_breach.blend`, 10,946,488,553 bytes, against
film23_breach's 10,946,487,113. Every guard reads exactly what it read on film23:

```
[apply   126.9s] east frame: deleted 6 round-1 solids, built 39 pieces, 8092 keys
                 worst travel BF_MUL05_S01 4.7421, BF_MUL05_S00 3.9318,
                              BF_MUL05_S02 0.1449
[apply  1441.8s] fines: appended 11246 puffs / 4679872 tris as 'BREACH_Fines.001'
>>   fines.appended  want True    got True    OK
>>   fines.puffs     want 11246   got 11246   OK
>>   fines.animated  want 11246   got 11246   OK
>>   fines.tris      want 4679872 got 4679872 OK
>> east_frame PASS=True  east_wall PASS=True  intruders over the wound=[]
>> STAGE RESULT: BREACH24_BUILT
```

**`BF_MUL05_S02 = 0.1449` is the bake guard**, and it reading the same value on a
film built from a different car is the direct evidence that **the 10.9 GB bake
did not need redoing**. `sim/breachlib.py` reads the car only for beat 3
(f865-1056), and R2-3363's `3_breach` row is `0.000000e+00` on all five channels
across all 192 of those frames. A wrong bake reads 55.35 m there. `sim/out/breach_film.npz`
was re-used unchanged, at the same sha it has carried since Aug 4.

---

## R2-3369 — THE FULL BAR ON film24. `FILM_BAR_PASS`, 40 of 40, judged against film24's own prediction

`render/world/assembly/r2/v128/verify_film24.sh render/film24_breach.blend`.
**All four measurement artefacts and both socket arms were re-run** — nothing is
carried over from film23:

```
  measure_film_scene ran   want MEASURE_FILM_SCENE_DONE  got MEASURE_FILM_SCENE_DONE  OK
  measure_film_extra ran   want FILM_EXTRA_MEASURED      got FILM_EXTRA_MEASURED      OK
  measure_strip ran        want STRIP_MEASURED           got STRIP_MEASURED           OK
  film materials           want FILM_MATERIALS_OK        got FILM_MATERIALS_OK (0 failures)  OK
  rig_preflight rc / verdict                             rc=0 / RIG_PREFLIGHT_OK      OK
  slabcheck rc                                           rc=0                         OK
  socket audit (film) rc                                 rc=0                         OK
  socket audit (film10 must still FAIL) rc               rc=1                         OK

  40 checks claimed | 40 OK | 0 FAIL | 0 UNMEASURABLE
>> STAGE RESULT: FILM_BAR_PASS
```

**The negative socket arm still fails.** `film10` returning `rc=1` is what makes
the film's `rc=0` mean something rather than meaning the audit is broken.

### It was judged against film24's prediction, and the log says so

```
>> judged against the film24 prediction: {'watts': 46866.886, 'stamps': 24,
   'strip_size_y': 0.1, 'strip_radiance': 47.4569}

  interior_lamp_watts        want 46866.886  got 46866.885   OK
  n_lamp_stamps              want 24         got 24          OK
  identity_residual_w        want 0.0        got 0.0         OK
  levelled_watts_from_stamps want 46866.886  got 46866.885   OK
  worst_per_lamp_ratio       want 12.363369  got 12.363369   OK
  lift_plus_exposure         want 0.0        got 0.0         OK
  strip narrow axis m        want 0.1        got 0.1         OK
  strip radiance (authored)  want 47.4569    got 47.4569     OK
```

That number was printed at **18:59:12Z**, into
`work/r23361/PREDICTION_film24_20260808T185912Z.log`, and stage 1 of the build
started at **19:04**. The ordering is on the filesystem, not on my word.

### The two content passes, read back out of the FILM rather than out of the car

`FILM_MATERIALS_OK` is the strongest single piece of evidence that the append
carried the passes, because it reads the 10.9 GB film:

```
[PASS] CarbonFibre: Mapping.Scale       want 62.8319  got 62.8319   (and .001, .002)
[PASS] CarbonFibre: TexWave count       want 6        got 6
[PASS] CarbonFibre: every TexWave still at Scale 1.0  want []  got []
[PASS] CarbonFibre.001: ... same, all six rows
[PASS] LiveryPaint: Metallic is LINKED  want True     got True
[PASS] LiveryPaint: metallic multiplier want 0.161290322581  got 0.161290317774
       (0.10/0.62 to float32; round 1 shipped no such node)
```

**R2-2041's carbon fix and R2-521's paint v5 are in the delivered scene**, on a
car that was rebuilt from scratch this evening. The `Metallic is LINKED` row is
the one that would catch a silent reversion: its `default_value` reads 0.62 and
is dead data, so a checker reading the default reports round 1 forever.

### film23_breach.blend was not touched, and that is measured

```
film23_breach sha16 BEFORE this run: 642371aea6df60c1
film23_breach sha16 NOW            : 642371aea6df60c1     mtime 08-08 07:09
```

`work/r22101` — film23's only evidence that it passed 40/40 — is untouched, and
`render/film23_path.json` still reads `363e4e88b30207ad`. Both films' bars remain
independently measurable on the files they were measured on.

### One operational note that cost a stage and is worth recording

The run was launched as a background child of the agent shell, and **the harness
killed the parent between stage 3 and stage 4**, one line after
`[gate] 9 GB available, starting measure_film_scene`. No artefact was damaged —
`film24.blend` and `film24_breach.blend` were already complete and saved — but
the bar had to be relaunched, and `run_rebuild24.sh` never printed its closing
`REBUILD24_COMPLETE`, so **that token is absent from `work/r23361/REBUILD24.log`
and its absence is not a failure.** The bar was re-run standalone under
`setsid` (`work/r23361/VERIFY24_STANDALONE.log`), which is how a build on this
box should be started: a long build must not be a child of an agent's shell.

---

## R2-3370 — THE OCCLUSION LEDGER: re-run, and the twelve hidden frames DO NOT EXIST on the film's camera

`tools/r2651_occlusion_sweep.py` had to be re-run: 264 of `render/r2731/occ_final_items.json`'s
1,922 rows are at or after f2715 and every one described a car that had since
moved by up to 678 m. `occlusion/not_stale_car` was correctly red.

**But a straight re-run would have refreshed the car and left a worse defect
standing.** The tool read its camera from a HARDCODED LITERAL —
`world/camera_rig_path.json` — and that file is the R2-1007 orphan, byte-identical
to `render/film16_path.json` (`d9c8f5c54ccd1ad8`) while the live declaration is
`363e4e88b30207ad`. `docs/LIVE-CAMERA.md`'s claim that the two are *"bit-identical
in position and lens from f781 onward"* was true against film17 and **is false
now**, in exactly the two places this ledger is read:

* **beat 5, f2134-2253** — camera position up to **21.40 m** apart, mean 8.53 m.
  That run *contains* f2180-2191, the twelve frames that were this ledger's
  entire published finding. The orphan sits **7-8 m higher** through the bridge
  window, and whether a deck occludes a car is a function of eye height under a
  soffit.
* **beat 6** — 241 of 264 frames differ in focal length and 251 of 264 aim more
  than 1° apart; at f2978 the orphan is on 74.0 mm and the film on 130.0 mm,
  75.3° away.

So `--camera` and `--car` are new arguments. **They default to the old literals,
so no existing caller changes meaning**, the default carries a printed warning
naming the orphan, and the paths actually read are now stamped into the ledger's
meta with their shas — the meta block previously recorded two literals, i.e. the
tool's intentions rather than its inputs, which is how the orphan survived
unnoticed for four days. `--selftest` is **22/22** after the patch.

Re-run against `render/film24_path.json` and the rebuilt car, 596 s:

```
>> new meta camera   render/film24_path.json (9d055d63da724993)
>> new meta car_pose world/car_anim_measured.json (ce440239eca4bf72)
>> old meta camera   world/camera_rig_path.json
```

| | superseded ledger (orphan camera, stale car) | **new ledger (film24's camera, rebuilt car)** |
| --- | --- | --- |
| rows | 1,922 | 1,922 |
| rows the control can read (`in_frame`) | 1,777 | **1,922** |
| frames with ANY front occlusion | 17 | **3** |
| **frames WHOLLY hidden (≥ 0.99)** | **12 — f2180-2191, all `ARCH_PontPlongee`** | **0** |

```
   frame | OLD front  owner              dist | NEW front  owner            dist
   f2180 |    1.000  ARCH_PontPlongee    26.4 |    0.000  None                 -
   f2185 |    1.000  ARCH_PontPlongee    36.5 |    0.000  None                 -
   f2190 |    1.000  ARCH_PontPlongee    51.9 |    0.000  None                 -
   f2191 |    1.000  ARCH_PontPlongee    54.5 |    0.000  None                 -
   f2192 |    0.581  ARCH_PontPlongee    57.1 |    0.000  None                 -
   f2717 |    0.032  ARCH_Gantry         76.1 |    0.032  ARCH_Gantry       75.9
   f2718 |    0.194  ARCH_Gantry         75.5 |    0.194  ARCH_Gantry       75.6
   f2719 |    0.065  ARCH_Gantry         75.3 |    0.065  ARCH_Gantry       74.8
```

**THE TWELVE HIDDEN FRAMES WERE AN ARTEFACT OF A CAMERA NO FILM HAS.** On the
camera film24 actually carries, the car is not behind the bridge at any frame of
beat 5.

**`ARCH_Gantry` at f2717-2719 is the negative control, and it is why this is a
correction and not a broken sweep.** Those three rows reproduce to three decimal
places on both cameras. The instrument still finds occlusion where occlusion is;
it stopped finding it where the camera was wrong. The 1,777 -> 1,922 jump in
readable rows is the same defect from the other side: the orphan's beat-6 aim was
75-79° off, so it had the car out of frame on 145 frames that are in frame in the
film.

### What this does to `tools/lap_shotscale.py`'s controls, measured

```
occlusion/not_stale       PASS  (unchanged; build_architecture.py is older than the ledger)
occlusion/not_stale_car   FAIL -> PASS      <-- the re-run's purpose, closed
occlusion/car_identity    PASS  (dump 301,667,220 == car_anim.blend on disk)
occlusion/supersession    PASS  (the Aug-04 file still lists f1114-1116)
occlusion/positive        PASS -> FAIL      hidden == [] , not list(range(2180, 2192))
```

> **`occlusion/positive` going red is a TRUE result about a corrected camera, not
> a regression, and the fix is not to relax it.** `tools/lap_shotscale.py` is
> leased by `r2-3181-instruments` and **has not been touched**. The control
> asserts a 12-frame hidden set that is now known to be an artefact; whoever
> holds that file should re-derive it from the new ledger, or re-point it at a
> claim that survives the camera correction. Any downstream text citing
> *"the car is 100 % hidden behind `ARCH_PontPlongee` at f2180-2191"* is now
> describing film16's camera and should say so or go.

The superseded ledger is kept at
`render/r2731/occ_final_items_SUPERSEDED_R2_3361_orphancam_stalecar.json`.

### A defect in my own harness, logged rather than quietly fixed

`work/r2-3361/rerun_occlusion.sh` guarded on `STAGE RESULT: SELFTEST_OK`, on the
belief — inherited from a summary rather than read off the source — that the 22
controls run unconditionally. **They run only under `--selftest`.** A real sweep
prints `OCC_OK`. So the script printed `OCC_ABORT` **after** the sweep had
succeeded and written the ledger: a FAIL standing over a PASS, which is the exact
two-verdict shape this project greps every log for. Nothing was lost, the guard
now reads `OCC_OK`, and the controls were run as their own job
(`work/r2-3361/occ_selftest.log`, 22/22) where they can actually be observed.

---

## R2-3371 — WHERE THE SHIP CANDIDATE STANDS, AND THE THREE THINGS THIS BLOCK DID NOT CLOSE

`render/film24_breach.blend` — 10,946,488,553 bytes — is the ship candidate.
`render/film23_breach.blend` is untouched at `642371aea6df60c1`, mtime 08-08 07:09,
and both films' bars remain independently measurable on the files they were
measured on.

| axis | film23_breach | **film24_breach** |
| --- | --- | --- |
| the car's motion | pre-R2-943; 91 frames of the ending with no subject | **`CAR_KEYS_MATCH_SOURCE`, 0.000 m at f2978** |
| beat 6 car width p50 @4K | 31.0 px | **81.0 px** |
| beat 6 frames wholly off frame | 91/264 | **0/264** |
| the film's last frame | **not in shot** | **in shot** |
| beat 5's camera | `363e4e88`, predates the re-pace | rebuilt from the live sheet |
| beat 1's camera | `363e4e88`, predates the re-pace | rebuilt from the live sheet |
| beat 1's assembly | the pre-R2829 seat schedule | the promoted `beat1_anim.blend` |
| the bar | `FILM_BAR_PASS` 40/40 | **`FILM_BAR_PASS` 40/40** |
| the world | assembly14, then clean | **assembly14, now STALE and overridden** |

### OPEN, and none of them is closed by this block

1. **`assembly15`.** `assembly14` no longer matches its own source fingerprint:
   `world/build_surface.py` moved by a landed commit, and `world/build_terrain.py`
   was read by assembly14 **in a state that never landed** and now carries 1,101
   uncommitted lines. film24 is built on it with `--world-override` and the reason
   on the record. **This must be closed before the 4K master, and closing it means
   landing `build_terrain.py` first** — a world rebuilt from the worktree today
   would bake another agent's unfinished work into the ship candidate.
2. **`tools/lap_shotscale.py`.** Leased by `r2-3181-instruments`, untouched.
   Three things are now wrong in it and one of them is newly wrong:
   * `occlusion/positive` asserts a 12-frame hidden set that R2-3370 shows was an
     artefact of the orphan camera. It is red and correctly so.
   * C6/C7 have inverted, as R2-3181 designed them to. The correction they need
     is subtler than "swap the arms": since R2-3301, `--car source` reproduces
     `world/car_anim_measured.json` everywhere and `--car built` is up to 655.3 m
     off — but **the ship car is now a third thing again**, and as of this block
     it is `world/R2_3361_car_anim_driver_CS.blend`, which the SOURCE arm also
     reproduces. So C6/C7 should now assert the source arm against the film, and
     the historical `built` arm is only about `work/r22161_proxy/`.
   * The module docstring, the `--car` help text and the `>> WARNING, beat 6 only:`
     banner all still say the delivered film has no lap-down. **That was true this
     morning and is false of film24.** The banner's advice — *"Use `--car built` to
     measure the pixels that exist"* — is now the exact inversion of the truth.
   * Its `--path` default is `render/film22_path.json`, two film generations stale.
3. **`docs/LIVE-CAMERA.md`** says `world/camera_rig_path.json` and the live path
   are *"bit-identical in position and lens from f781 onward"*. Measured in
   R2-3370, that is false by 21.40 m in beat 5 and by 56 mm of focal length in
   beat 6. The live declaration should also move to `render/film24_path.json`
   (`9d055d63da724993`) once film24 is accepted.

### Not open, and stated so nobody re-opens it

**The 10.9 GB breach bake does not need redoing** and was not redone. The car is
`0.000000e+00` on every channel across beat 3's f865-1056, and the rebuilt film's
bake guard reads `BF_MUL05_S02 = 0.1449` — the same value a correct bake has
always read. Every other consumer of `world/car_anim_measured.json` listed in
R2-3307 reads frames inside f1-f2714, where the two blends are bitwise equal.

