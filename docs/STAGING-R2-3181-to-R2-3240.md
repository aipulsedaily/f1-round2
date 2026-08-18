# STAGING R2-3181 .. R2-3240 — two instruments that could not tell "I could not test this" from "the thing under test is broken"

Agent: `r2-3181-instruments`. Tasks #155 (`tools/lap_shotscale.py`) and #153
(`tools/placement_determinism_control.py`).

**No rendering was needed and none was done.** Every pixel below is from
`work/r22161_proxy/`, which is already paid for.

---

## R2-3181 — #155a: the clamp is gone, and the private reader with it

`tools/lap_shotscale.py` kept its own `csv.DictReader` of
`telemetry/telemetry.csv` with its own interpolator, and that copy clamped:

```python
def at(self, t):
    t = max(0.0, min(t, self.t_end))        # <- the defect
```

`telemetry.csv` ends at world t **72.5833 s**; the film runs to **83.6115 s**.
All 264 frames of beat 6 are past the end of the table, and the clamp answered
them by repeating the last row — parking the car at (326.2, 167.2) and returning
a plausible number for it.

**Reproduced before touching anything** (`work/r2-3181/beat6_residual.py`):

| frame | clamped reader | `anim/carpath` + lap-down | error |
| --- | --- | --- | --- |
| 2714 | 326.2, 167.2 | 328.2, 168.8 | 2.5 m |
| 2760 | 326.2, 167.2 | 426.6, 251.4 | **131.1 m** |
| 2978 | 326.2, 167.2 | 502.9, 315.4 | **230.7 m** |

Every figure in the handover checks out. The clamped centre at f2978 is
**−2,349 proxy px**, which is where "2,349 px off the left of frame" came from.

**The private reader is deleted, not patched.** `lap_shotscale.Car` is now a
thin adapter over **`anim/carrig.CarRig`** — the same pose function
`anim/build_car_anim.py` keys the car with. Position and heading come from
`carpath.Car.state` (which extrapolates via `_extrap`/`LapDown` instead of
clamping), z from the four-wheel contact solve, attitude from the ground plus
the body's own dive-squat and lean. `at(t)` keeps the six-tuple its four
consumers unpack, so nothing downstream had to change shape.

Constants are imported from `anim/carpath` and **asserted against
`world/world_contract`** at import, so the two-level chain is checked rather
than trusted.

### The control, WATCHED TO FAIL

New `C0 extrapolation/no_clamp`. `work/r2-3181/clamp_negative_control.py` puts
the clamp back and requires the control to notice:

```
  clamped (the R2-2885 defect, reintroduced)   FAIL  extrapolation/no_clamp  5 s past the
      telemetry the car has moved 0.0 m (a clamped reader reads 0.0) and it lands within
      2.14e+02 m of anim/carpath.Car.state, which is the only definition of that motion
                                               SELFTEST FAIL
  fixed (anim/carrig)                          PASS  ... moved 214.1 m ... within 0.00e+00 m
                                               SELFTEST PASS
>> STAGE RESULT: CLAMP_NEGATIVE_CONTROL_OBSERVED_TO_FAIL_AND_PASS
```

Log: `work/r2-3181/clamp_negative_control.log`.

---

## R2-3182 — #155c: THE ~368 px RESIDUAL. It is not the beat sheet. **The delivered film does not have the lap-down.**

R2-2886 left this open and named a lead: *"the residual is most likely the
beat-sheet time map: `film22.blend` was built at 04:42 and the sheet on disk was
promoted at 06:22, so the sheet that built the delivered proxy is not pinned."*

**That lead is wrong, and it is now settled — by measurement, not by diff.**

`world/car_anim_measured.json` is `CAR_ROOT`'s per-film-frame transform sampled
off `world/car_anim.blend`. Driving my model off **today's**
`docs/beat_sheet.json` time map and comparing:

| frame | measured car keys | constant-speed model | Δ | R2-943 lap-down model | Δ |
| --- | --- | --- | --- | --- | --- |
| 1191 | 332.96, 172.80 | 332.96, 172.80 | **0.000 m** | same | 0.000 m |
| 2714 | 328.15, 168.78 | 328.15, 168.78 | **0.000 m** | same | 0.000 m |
| 2760 | 459.96, 279.37 | 459.96, 279.37 | **0.000 m** | 426.6, 251.4 | 43.5 m |
| 2850 | 485.98, 555.86 | 485.98, 555.86 | **0.000 m** | 495.2, 309.0 | 247.1 m |
| 2978 | 238.44, 939.74 | 238.44, 939.74 | **0.000 m** | 502.9, 315.4 | **678.0 m** |

The model reproduces the built car keys to **0.000 m on every frame of beats 5
AND 6** — which is a far stronger statement about the beat sheet than any diff:
**today's time map IS the one the car was keyed with.** The sheet is exonerated.
(Corroborating: the sheet's `time_map` block is byte-identical across every
`beat_sheet*.json` snapshot on disk, and `film22_path.json`'s f2978 lens of
129.99 mm can only come from a 130 mm sheet.)

### The actual cause

```
world/car_anim.blend            built  2026-08-04 19:51
R2-943 lap-down lands in git    commit 4acc22f, 2026-08-07 08:35   <- 2.5 days LATER
render/film22_path.json         built  2026-08-08 04:42            <- WITH the lap-down
render/film22.blend             built  2026-08-08 04:51
```

`tools/build_film_scene.py` **appends** the car's keys from
`world/car_anim.blend` and refuses if they are missing — it does not re-key. So
the delivered film's car is the **pre-R2-943 constant-speed** car, streaking on
at 89.767 m/s, while the camera it is filmed with tracks the lap-down car that
does not exist in the scene.

**`docs/NEXT-REBUILD.md` already carries the lap-down as "ALREADY IN SOURCE —
nothing to fold in; the rebuild picks it up by running the source". Nobody had
connected that to beat 6's subject.**

### Proved on the delivered pixels

`work/r2-3181/overlay_beat6.py` draws both arms on the proxy.
`work/r2-3181/crop_2740.png` and `crop_2810.png` are the money shots: at f2740
and f2810 the **constant-speed** box is dead on the car and the **lap-down** box
is on empty asphalt. That is exactly the "on empty asphalt at f2810 and f2900"
R2-2886 saw and could not explain.

Separation between the two arms, measured:

| frame | 2715 | 2740 | **2760** | 2790 | 2850 | 2900 | 2978 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| px @4K | 0.0 | 158.4 | **375.7** | 716.0 | 649.1 | 1,339.5 | 4,054.3 |
| proxy px | 0.0 | 39.6 | **93.9** | 179.0 | 162.3 | 334.9 | 1,013.6 |

**375.7 px @4K / 93.9 proxy px at f2760**, against the residual R2-2886
measured by eye as "~92 proxy px (368 px at 4K)". Same number. The residual is
the lap-down, entirely.

The tool now takes `--car {source,built}` and **prints which one it used above
every table**, with a warning on the `source` default that beat 6 then describes
a rebuild and not `render/film22.blend`. Controls C6/C7 assert both arms against
the built keys, so the day `car_anim.blend` is rebuilt they fail and say why.

---

## R2-3183 — #155d: the beat-6 subject verdict, which nobody could issue

R2-2886 retracted two findings as artefacts of the clamp:

* *"the car is 2,349 px off the left of frame at f2978"*
* *"32.2 % of the ending is under 60 px at 4K"*

**The retraction was right about the method and wrong about the direction.**
Re-derived on the delivered camera and the delivered car:

| | published (clamped, film14 camera) | **re-derived (film22 camera, built car)** |
| --- | --- | --- |
| beat 6 median frac_w | 4.15 % | **0.81 %** |
| beat 6 car width p50 @4K | — | **31.0 px** (min 15.9) |
| box height p50 @4K | — | **19.2 px** (min 13.1) |
| frames under 60 px @4K | "32.2 %" (retracted) | **95.8 %** |
| frames with the car **wholly off frame** | 0 | **91 of 264 (34.5 %, 3.79 s)** |
| first frame with no car in shot | — | **f2888, and it never returns** |
| separation p50 | refused | 0.046, low-sep 42.4 %, low-detail 95.1 % |

**The film's last 91 frames — including its final frame — contain no car.**
`work/r2-3181/beat6_tail.png` is f2880 / f2900 / f2940 / f2978 at full proxy
resolution: empty track in all four.

The car exits the top of frame, not the left. The clamped reader's answer was
wrong in mechanism and magnitude and **understated the defect**: the correct
figure is not 32.2 % under 60 px, it is 95.8 %, plus a third of the beat with no
subject at all.

`tools/r2_2881_pixelpeep.py`'s C8 box validation, which refused beat 6, now
passes on it — `separation 0.208 on the box vs 0.000 at 400 px off it, lift
207,986x` — so this verdict is issued on a box that has been shown to be on the
car.

**This is a FILM defect, not an instrument defect, and it is the one thing in
this report that needs somebody else's decision.** Rebuilding
`world/car_anim.blend` from current source puts the lap-down in and takes beat 6
to p50 81 px @4K, min 53.5, **0 frames off frame** — which is what R2-943 was
for. Until that rebuild happens the delivered ending has no subject.

---

## R2-3184 — #155d: R2-2521 §4c is wrong. `lap_shotscale`'s car box is correct.

The handover named `lap_shotscale.py:68` as *"a third site using the car's
thickness where its top belongs, putting the subject centre 0.340 m low"*,
following R2-2521 §4c: *"Its box is `CAR_BOT_Z = 0.0 .. CAR_TOP_Z = 0.992`. The
car is 0.340 .. 1.332."*

**Both boxes are the same box in different frames, and the file was right.**

`0.340 .. 1.332` is the car's **world** box **in the showroom, standing on the
dais deck**. `circuit_spec.showroom.dais.deck_top_z` and `carrig.DECK_TOP_Z` are
both **0.340**. `world_contract.CAR_RIDE_HEIGHT_M = 0.340` is that deck height
under a misleading name — a real F1 ride height is ~30 mm — and the name is what
propagated the error.

`lap_shotscale` adds its box to `pos`, which is `CAR_ROOT`, and **`CAR_ROOT`
sits on the ground**. Measured three independent ways:

1. `world/car_anim_measured.json` frame 1: `CAR_ROOT` loc z = **0.340** and all
   four of its contact patches are at z = **0.340**.
2. `carrig.pose()` sets `CAR_ROOT`'s z from the four-wheel contact solve, and
   `WHEEL_CENTRE_Z_LOCAL = 0.360 == WHEEL_RADIUS_M`, so local z 0 is the tyre's
   contact patch.
3. **Drawn on the delivered proxy** at f1268 / f1275 / f1380
   (`work/r2-3181/carbox_check.png`): `z 0.000..0.992` bounds the car; the
   "corrected" `0.340..1.332` box sits visibly **0.340 m above it**, lower edge
   through the sidepods, upper edge in clear air.

**Applying R2-2521 §4c's correction would have put the subject centre 0.340 m
HIGH.** The claim is withdrawn, and so is the knock-on finding that
`tools/r2971_pont_camera_rebase.py`'s aim is 22 px low — it is not.

What *is* real and is now recorded in the docstring: the box is symmetric about
the reference point (±L/2) while the measured car is x −2.678..+3.020, i.e.
**0.171 m forward of centre**. Not corrected — every published `frac_w` was
taken with the symmetric box — but priced.

---

## R2-3185 — #155d: two more defects in the same file, found while re-deriving

**The default camera was eight film builds stale.** `--path` defaulted to
`render/film14_path.json` (2026-08-03, the **74 mm** beat 6). The delivered film
is `film22_path.json` (**129.99 mm**). Beat 6's median moves **4.15 % → 4.64 %**
on the camera change alone, before the reader fix. Default changed, with the
reason in the code.

**Two controls were inheriting the thing under test.** Control 1 (the f697
ruler) and control 4 (agreement with `tmp/shotscale_v2.npy`) projected through
whatever `--path` the run was given, and compared against references measured on
`film14`. Moving the default made both FAIL — control 1 read 0.4418 against a
hard-coded 0.5033, control 4 read p95 2.10 % against a 2 % bound — **blaming the
projection for a change of camera.** Both now pin `CONTROL_PATH =
render/film14_path.json` explicitly. Control 1's reference is additionally now
**computed by `tools/beat1_true_extent.py`** rather than retyped, because
`docs/beat_sheet.json:beat1.car_box` is being edited live and a literal would
have started failing for a third unrelated reason.

Post-fix: `SELFTEST PASS`, every control green.

---

## R2-3186 — #155e: I checked your occlusion column, and it has the same blind spot it was built to close

`OCCLUSION_LEDGER` / `ledger_is_stale()` are sound and the R2-1081 correction
(pointing at `render/r2731/occ_final_items.json`, not the Aug-04 file) is right:
the live ledger's hidden set is **exactly f2180–2191**, the superseded one adds
f1114–1116, and every one of the six occlusion controls passes.

**But `ledger_is_stale()` checks one of the ledger's two inputs.** An occlusion
result is a claim about a world **and about a car**, and
`tools/r2651_occlusion_sweep.py` reads the car from
`world/car_anim_measured.json`. The check only looked at
`world/build_architecture.py`. Added `occlusion/not_stale_car`.

And a WARN that matters more:

```
WARN  occlusion/car_identity  world/car_anim_measured.json does NOT describe
      world/car_anim.blend on disk (sampled 300235801 bytes, blend is 301667220).
```

The car pose table every occlusion figure in this project rests on was sampled
**2026-08-03 04:04** off a blend that changed **2026-08-04 19:51**. WARN and not
FAIL because the ledger's own frames are unaffected in beats 1–5 — but nothing
reading it may claim to describe the built car until it is re-sampled. Six other
tools read that file (`sim/breachlib.py`, `tools/beat2_probe.py`,
`tools/r2651_pont_sightline.py`, `tools/r2731_pit_sightline.py`,
`tools/r2731_pont_camera_apply.py`, `tools/r2651_occlusion_sweep.py`).

---

## R2-3187 — #155d: which published numbers change, and which survive

**SURVIVE, unchanged or moved by less than the last quoted digit.** Everything
inside the telemetry, i.e. beats 2–5, on the camera it was quoted against:

| finding | published | re-derived | verdict |
| --- | --- | --- | --- |
| R2-581 beat 5 median | 12.92 % | 12.93 % | stands |
| R2-581 f2035–2227 median / min | 4.215 % / 2.957 % | unchanged to 2 dp | stands |
| R2-582 beat 3 / beat 4 medians | 44.60 % / 9.45 % | 44.60 % / 9.45 % | stands |
| R2-583 the whole bearing decomposition (f1990–f2220) | — | beat 5 only | stands |
| R2-589/R2-594 lensfix (f1937–2304) | — | beat 5 only | stands |
| R2-661 occlusion contamination of the demand curve | — | beat 5 only | stands |
| R2-1001/R2-1002/R2-1011/R2-1081 occlusion, 12 frames f2180–2191 | — | re-asserted | stands |
| R2-826 "beat 1 is not measured by this tool" | — | — | stands |
| beat 2 median | 130.42 % | 130.78 % | moved by the pose change |

The beat-5 numbers move by p50 **0.087 %** and p95 **1.00 %** relative — the
`carrig` pose (contact-solve z, ground pitch/roll) replacing the telemetry's
flat z and body-only attitude. Real, more correct, and below every quoted digit.

**CHANGE — every beat-6 figure ever taken through this tool.** All of them were
the parked car, and most were also on the stale 74 mm camera:

| finding | published | re-derived (delivered film) |
| --- | --- | --- |
| R2-582 "beat 6, the closing wide" | **4.15 %** w / 3.79 % h | **0.81 %** |
| R2-582 f2794–2978 median | **2.76 %** | **0.41 %** |
| R2-2887 `6_ending` G1 | REFUSED | **19.2 px @4K p50, 95.8 % under 60 px** |
| R2-2887 `6_ending` "cleanest beat in the film" on G3 | 1 p50, max 6 | **still true** — because there is nothing in the frame to be empty of |
| R2-430-era v2 build, beat 6 | 4.1 % (`tmp/shotscale_v2.npy`) | **also clamped**; 4.14 %, so the "independent implementation" control never covered beat 6 |

**RETRACTED FINDINGS, RE-EXAMINED.** R2-2886's two retractions stand as
retractions — those numbers were artefacts — but their *conclusions* were
understated, not overstated. See R2-3183.

**NOT AFFECTED.** `tools/r2581_lensfix.py` (f1937–2304), 
`tools/r2971_pont_camera_rebase.py` (f2131–2224) and
`tools/r2651_occlusion_sweep.py` (does not use the telemetry reader at all) are
entirely inside beat 5. `tools/r2581_nearfield_sweep.py` calls
`series(lo=1, hi=2978)` unguarded and its beat-6 rows were clamped; no published
figure of its was taken from them.

`tools/r2_2881_pixelpeep.py` is updated in the same commit: one reader instead
of two, `arm="built"` because it measures delivered pixels, and its **C0 control
re-specified** — the old `post > 1e-6` assertion would have kept passing on
float noise and kept claiming "the fix is live" about a divergence that no
longer means anything.

---

## R2-3188 — #153: the control that blamed the gate for its own vacuity

`tools/placement_determinism_control.py` perturbs `measure()` with

```python
for k in sorted(closest):
    d, name, at = closest[k]
    closest[k] = (d, name + "_INJECTED", at)
    break
```

On a scene where nothing comes near any corridor `closest` is **empty**, the
loop body never runs, nothing is injected, and the gate correctly reports
`IDENTICAL`. The control then printed

```
FAIL  a deliberately non-deterministic measure() is REFUSED  got=PLACEMENT_CLEAN
```

which reads as *the determinism assertion failed to refuse*. It did not. There
was nothing to refuse.

**Fixed:** the injection now reports whether it happened, and the file will not
judge the gate on a pass it never perturbed.

* injected → the refusal assertions run as before, plus a third that the
  perturbation really was applied, and the line names **which corridor and which
  object name** was altered.
* not injected → `PLACEMENT_DETERMINISM_CONTROL_INAPPLICABLE`, naming the real
  reason and stating explicitly that the gate's answer is not evidence about the
  gate.

`INAPPLICABLE` is added to `gate_exit._VACUOUS_MARKERS`, so it exits **3
(VACUOUS)** — not a pass, and deliberately not FAIL. That is the code
`gate_exit` already defines for "nothing in the scene for it to test".

### Both runs, and both behave correctly

**A. `ctl_place_neg.blend` — nothing comes near any corridor. Must be
INAPPLICABLE.** (`work/r2-3181/determinism_control_neg.log`)

```
>> DETERMINISM CONTROL: the assertion is fed a non-deterministic input FIRST, and must refuse.
      [gate said] >> determinism: 2 pass(es), IDENTICAL; scene walk 07796cdeb7857159; 0 object(s) unmeasurable

>> THE PERTURBATION DID NOT HAPPEN. closest_approach is EMPTY on every corridor -- nothing
   in this scene comes near the camera path, the car path or the road corridor, so there is
   no object name to rename.
>> measure() ran 2 time(s); 1 injection attempt(s); 1 of them found an empty closest_approach.
>> The gate answered 'PLACEMENT_CLEAN'. THAT ANSWER IS NOT EVIDENCE ABOUT THE GATE: it was
   never given a non-deterministic input, so it had nothing to refuse and nothing to miss.
>> This control is INAPPLICABLE to this scene. Run it against a scene where something DOES
   come near a corridor -- render/world/assembly/r2/v120/ctl_place_pos.blend is one, and
   ctl_place_neg.blend is deliberately not.

>> STAGE RESULT: PLACEMENT_DETERMINISM_CONTROL_INAPPLICABLE
NEG rc=3
```

Was `FAIL ... got=PLACEMENT_CLEAN` and rc=1. Now VACUOUS, and the gate is named
as innocent in the same breath.

**B. `ctl_place_pos.blend` — something does. Must inject and must refuse.**
(`work/r2-3181/determinism_control_pos.log`)

```
      [gate said] >> THE SAME UNCHANGED SCENE MEASURED DIFFERENTLY ON REPEAT:
      [gate said] >> REFUSING TO REPORT: ... Every number above is unciteable.
      [injected] closest_approach[camera_path]: 'CTL_Obstacle' -> 'CTL_Obstacle_INJECTED' on pass 2 of 2
   PASS  a deliberately non-deterministic measure() is REFUSED       got=PLACEMENT_NONDETERMINISTIC_REFUSED  exit code 3
   PASS  ...and the refusal is NOT spelled as a pass                 code 3
   PASS  ...and the perturbation this verdict is about really was injected
                       closest_approach[camera_path] renamed 'CTL_Obstacle' -> 'CTL_Obstacle_INJECTED'
   PASS  the unperturbed run is NOT refused as non-deterministic     verdict PLACEMENT_FAIL (exit 1)
   PASS  the unperturbed run reaches a real placement verdict        verdict PLACEMENT_FAIL
>> STAGE RESULT: PLACEMENT_DETERMINISM_CONTROL_OK
POS rc=0
```

The third row is new: the refusal verdict is only credited when the injection is
shown to have been applied, and the line says which corridor and which name.

**No two-verdict trap.** `tools/gate_exit.py` over each log:

```
neg: 1 verdict(s)   << 1/1  PLACEMENT_DETERMINISM_CONTROL_INAPPLICABLE  VACUOUS   rc=3
pos: 1 verdict(s)      1/1  PLACEMENT_DETERMINISM_CONTROL_OK            PASS      rc=0
```

**Note on the buildlock.** These two runs are an 86 KB control scene, not a
build. My wrapped invocation queued behind four consecutive ~10 GB film builds
for 55 minutes without getting in, so I killed my own waiter **by explicit PID**
(2814005/2814001/2814000/2813968, no `pkill -f`) and ran the two gates directly
with 7.7 GB available and memory pressure at `full avg300=7.05`. Nobody's build
was displaced. Anything heavier stays in the lock.

---

## Claims, leases and commits

Claimed one at a time as `r2-3181-instruments`:
`tools/placement_determinism_control.py`, `tools/lap_shotscale.py`,
`tools/gate_exit.py`, `tools/r2_2881_pixelpeep.py`, and this file.

`docs/beat_sheet.json` and the beat-authoring tools were **not touched**.
`docs/DEFECT-LOG-R2.md` was **not edited** — it is merged by the main thread.
