# STAGING — R2-941 to R2-970 · the ending: the car's arrival

Owner of R2-941..R2-950: the closing beat's CAR motion. Merge by identity, never
by position. R2-951..R2-965 belong to the audio rebuild and are appended by that
agent. **Do not edit `docs/DEFECT-LOG-R2.md` from this file.**

This picks up exactly where R2-862 left off:

> "The camera cannot fix this. The distance can. … The only free variable left is
>  how far away the car is, and that is `carpath.py`'s extrapolation at a constant
>  83.1 m/s, which carries it 913 m in the closing 11 s."

Everything below that is not marked **MEASURED ON FRAMES** is measured on the
built camera path and the car's own solve, not on pixels.

---

## R2-941 — the flying lap ends 4.15 m before the line, and the beat boundary is 0.018 s after it

**MEASURED** on `telemetry/telemetry.csv` and `anim/filmtime.py`.

Nobody had put these four numbers next to each other, and once they are, the
ending authors itself.

| | |
|---|---:|
| telemetry ends | world t **72.58333** s, track s **3670.850** m |
| lap length (`headline.length_m`) | **3675.0** m |
| so the car crosses the start/finish line at | world t **72.62957** s |
| last frame of beat 5, f2714 | world t **72.61153** s |
| first frame of beat 6, f2715 | world t **72.65320** s |

**The car crosses the start/finish line BETWEEN the two frames of the
f2714/2715 seam.** Beat 5 is the flying lap and it ends, to within 0.43 of a
frame, at the moment the lap ends. That is not a coincidence anyone has to
arrange — it falls out of the beat sheet as it already stands.

Two consequences, both load-bearing:

1. **The whole of the lap-down is inside beat 6.** A deceleration keyed off the
   line crossing cannot touch a single frame of beats 1-5, and f2714 — the seam
   frame whose 1.33 % interpolation measurement must survive — is still flat out
   at 89.767 m/s and **bit-identical**.
2. R2-862's phrase *"the film ends where the lap began"* is literally available.
   The car does not have to be brought back to the line; it is AT the line when
   beat 6 starts, at 323.2 km/h, and the beat is the 11 s after.

**A correction to the brief this task was given.** The authorised target was
*"336.7 m is where the car comes to rest near the start/finish line"* — the
distance from the camera's hold at `[594.19, 16.05, 140.0]` to the line itself.
The car cannot come to rest **at** the line: it arrives there at 323 km/h on the
first frame of the beat. It comes to rest **past** it, on the pit straight, and
that is *better* rather than a compromise — see R2-942.

---

## R2-942 — the pit straight is exactly 250.0 m long and the distance to the camera has a minimum inside it

**MEASURED** on `docs/circuit_spec.json`'s own element table and centreline.

```
elements[0]   S   s_start 0.0    length 250.0   "S0  pit straight S/F->T1"
elements[1]   A   s_start 250.0  length 108.21  R100 62 deg  "T1  Vitrine"
```

So there is a **declared 250 m box** the car may come to rest in. Past it the car
is stopped in the middle of a 100 m-radius corner, which does not read as a
lap-down — it reads as a retirement.

Distance from the camera's hold to the centreline, and the car's width at 4K
through the candidate's closing 130 mm lens:

| track s | dist to hold | car @4K | |
|---:|---:|---:|---|
| −50 | 355.3 m | 222 px | before the line |
| **0** | **336.7 m** | **235 px** | the line — the brief's figure |
| 50 | 324.7 m | 243 px | |
| **100** | **320.2 m** | **247 px** | **the minimum** |
| 150 | 323.5 m | 244 px | |
| 200 | 334.3 m | 236 px | |
| **226.5** | **342.9 m** | **231 px** | where it stops (R2-943) |
| 250 | 351.9 m | 224 px | T1 entry — the boundary |
| 300 | 383.9 m | 206 px | inside T1 |
| 500 | 562.2 m | 141 px | |

**The function is flat.** Anywhere on the pit straight is 320-352 m and 224-247
px. There is no fine tuning to do and no reason to chase the 320 m minimum: what
matters is landing inside the 250 m box at all, and every point in it clears
R2-862's *"a subject"* threshold of ~236 px or sits within 5 % of it.

---

## R2-943 — CANDIDATE: the lap-down. Grip-limited, aero-assisted, released at rest.

`anim/carpath.py`. Beats 1-5 are **bit-identical**, proved against a control
built from the same source with the model switched off.

    >> STAGE RESULT: LAPDOWN_OK

### The model, and why each term is there

```
a(v) = [ A_ROLL + (A_BRAKE + K_AERO v^2) * smoothstep(v / V_RELEASE) ]
       * smoothstep(dt / ONSET_S)

A_ROLL     1.2 m/s^2    rolling resistance + engine braking
A_BRAKE    7.0 m/s^2    the brake where only mechanical grip is available
K_AERO     0.0038 /m    the aero term: +30.6 m/s^2 at the speed it crosses at
V_RELEASE  15.0 m/s     the brake is progressively released below 54 km/h
ONSET_S    0.30 s       the driver's foot
```

* **`A_ROLL` never vanishes, and that is the whole reason it is a separate term.**
  Every profile that tapers the deceleration to zero as `v -> 0` — including the
  three I tried first — makes the car approach rest *asymptotically*: it is still
  creeping at 0.3-0.5 m/s on the last frame and never actually stops. A car that
  nearly stops is not an ending. With a floor of 1.2 m/s² the speed reaches
  **exactly** zero in finite time and stays there.
* **`K_AERO v²` is not decoration.** An F1 car's braking is grip-limited and its
  grip is aero-assisted, so deceleration falls with speed. A constant-g stop from
  89.767 m/s either takes 493 m (too far — 141 px) or needs 4.7 g (a limit stop,
  not a lap-down). The aero term is what buys a firm early brake AND a long, slow
  arrival inside the same 11 s.
* **`ONSET_S` exists for the seam.** Without it the deceleration steps from 0 to
  35 m/s² in one instant. It is not visible — 1.5 m/s of speed change in a frame
  moves the 180° motion blur by 27 mm — but the seam is the one place in this
  film where "not visible" is not the standard.

### The brake point is derived, not chosen

`t_brake = t_end + (lap_m − track_s_end) / v_end = 72.62957 s`, i.e. the line
crossing from R2-941. Not `t_end`. The 4.15 m between them is the difference
between a lap-down that starts at the line and one that starts 0.046 s early.

### What it does

| | |
|---|---:|
| speed at the line | 89.7671 m/s = **323.2 km/h** |
| peak deceleration | 35.27 m/s² = **3.60 g** at world t+0.9 s |
| comes to rest | **9.226 s** after the lift = **film frame 2936** |
| distance travelled | **226.52 m** |
| margin to T1 | **23.5 m** inside the 250 m pit straight |
| stationary for | frames 2936-2978, **42 frames = 1.75 s** |

An F1 car brakes at 5-6 g from 320 km/h. **3.60 g is roughly 65 % brake** — a
driver crossing the line and braking firmly, not a limit stop and not an
emergency. It is the one number in this model that is a taste judgement, and it
is stated so it can be argued with.

Per-frame, against the candidate camera:

```
    f   track_s    v m/s     kph    dist m   px @4K   px/frame   | SHIPPED dist    px
 2714      -1.6    89.77   323.2      85.0    171.6     112.65   |        85.0  171.6
 2715       2.1    89.76   323.1      87.3    167.1     109.70   |        87.3  167.1
 2760     106.1    53.75   193.5     156.8     83.3      32.75   |       175.8   74.3
 2820     203.4    15.83    57.0     272.8     51.6       5.98   |       431.0   32.7
 2880     223.2     3.27    11.8     335.0     76.5       1.83   |       664.9   38.6
 2906     225.6     1.58     5.7     342.5     97.6       1.13   |       751.7   44.5
 2936     226.5     0.00     0.0     342.9    146.4       0.00   |       860.5   58.3
 2978     226.5     0.00     0.0     342.9    230.4       0.00   |      1000.1   79.0
```

### Everything downstream of the car had a constant-speed assumption in it

The model is one function, `Car._extrap`, and **four** other places were reading
`v[-1] * (t - t_end)` or holding a constant. All four now walk the same table:

| file | what it was doing | what it would have shipped |
|---|---|---|
| `anim/carrig.ground_distance` | `dist_c[-1] + v[-1]*dt` | tyres spinning at 323 km/h under a car standing still for 42 frames |
| `anim/carrig.body_pitch` | `return 0.0` | a car braking at 3.60 g sitting dead level on its springs |
| `anim/carrig.body_roll` | `v[-1]**2 * curvature` | lateral lean computed at 323 km/h while stationary |
| `audio/scene.Telemetry.sample` | its own copy of the extrapolation | the engine at 323 km/h under a stopped car |
| `tools/car_anim_gate._ctrl_*` | `v[-1]*dt / r` | the control failing on beat 6 and no longer naming the launch |

`body_pitch` now uses **`tools/build_telemetry.py` line 533's own closed form** —
`clip(-ax/30, -1, 1) * 1.6 deg` — on the lap-down's deceleration, so the car dives
onto its nose under braking with the same law the telemetry itself was written
with. At 3.60 g the term clips, i.e. the full declared 1.6°.

### `F1_LAPDOWN=0` is an A/B fixture and nothing on the ship path may read it

It exists so a control arm can be built from the same source on the same box —
see R2-944 — and it is default-on. Named here because R2-723 is exactly the rule
it could violate: *a fixture that proves a checker works must never become a
default.*

---

## R2-943b — the car stops past the pits, and no braking rate can change that

**MEASURED** by taking `world/build_architecture.py`'s own declared pit-building
box through `WC.circuit_to_world` and projecting it into the built closing frame.

The circuit frame is aligned with the pit straight — track s **is** circuit x,
and the centreline sits at circuit y = 0 — which makes the architecture's
declared numbers directly comparable:

```
pit building   PB_X0, PB_X1 = -245.0, 75.0      i.e. from 235 m BEFORE the
               PB_Y0, PB_Y1 =   23.5, 40.5           line to 75 m AFTER it,
                                                      23.5-40.5 m to one side
car comes to rest                s = 226.5 m     i.e. 151 m past its east end
```

Projected into the 130 mm closing frame, with the camera aiming at the car:

| car rests at | dist | car px | start/finish line | pit building |
|---:|---:|---:|---|---|
| s=100 | 320.2 m | 246.7 | ndc x −2.25, out | **3 corners IN frame** |
| s=150 | 323.5 m | 244.2 | out | none |
| s=200 | 334.3 m | 236.3 | out | none |
| **s=226.5** | **342.7 m** | **230.6** | ndc x −5.73, out | none |
| s=250 | 351.9 m | 224.5 | out | none |

**Only s=100 puts any architecture in the closing frame, and s=100 is not
reachable.** Stopping in 100 m from 89.767 m/s is 4.03 g *mean*, which the aero
profile delivers at about 8 g peak. Even a genuine limit stop — 5.34 g peak, the
hardest profile in my grid search — covers 161.6 m and still finishes 87 m past
the building. **The car crosses the line at 323 km/h and physically cannot stop
inside the 75 m of pit building that remains in front of it.**

So the closing frame is *determined*: a 95 m-wide stretch of the pit straight
past the pit exit, with the car at its centre, and no architecture and no
start/finish line in it. That is not a choice I made and it is not one available
to be made differently.

**Whether that is good is a separate question and I am not going to pretend the
arithmetic answers it.** The case for it is R2-855's own statement of what the
ending is for — *"the car, alone, still running"* — and that the shipped ending's
failure was partly clutter: a 65 px wound in a truck park. A clean frame of the
car alone on the circuit is the opposite failure mode from the one we have. The
case against is that *"the film ends where the lap began"* is then true in the
world and invisible in the frame. **R2-950 has to settle it by looking.**

---

## R2-944 — the rig rebuilt: beats 1-5 bit-identical, and the seam step is the same object in all three arms

Built with `anim/build_camera_rig.py` from `docs/R2851_beat_sheet_CANDIDATE.json`
— **R2-853's sheet, unmodified.** The camera candidate ships as it stands; the
only new variable is where the car is.

    >> STAGE RESULT: CAMERA_RIG_FAIL     (1_assembly, PRE-EXISTING — see below)

Three arms, all measured with one instrument:

* **A** `work/r2941/camrig_R2943_path.json` — the lap-down.
* **B** `work/r2941/camrig_CTRL_constv_path.json` — the SAME build with
  `F1_LAPDOWN=0`. One variable, same box, same minute.
* **S** `render/film17_path.json` — the shipped film, for scale.

### A against its own control

| | position | rotation |
|---|---:|---:|
| f1 – f2713 | **0.000e+00 m** | **0.00000 deg** |
| **f2714, the seam frame** | **0.000e+00 m** | **0.00000 deg** |
| **f2715** | **0.000e+00 m** | **0.00000 deg** |
| f2716 – f2978 | 0.000e+00 m | 18.38 deg (f2795) |

**The lap-down changes nothing before frame 2716.** Not "nothing measurable" —
nothing. And the control is itself bit-identical to the previous agent's R2-853
build over all 2,978 frames, so the chain back to R2-853 is closed.

### The f2714/2715 seam

| arm | position step | rotation step | lens |
|---|---:|---:|---|
| A lap-down | 2.5454 m | 0.06240 deg | 24.003 → 23.999 |
| B const-v | 2.5454 m | 0.06240 deg | 24.003 → 23.999 |
| S shipped | 2.5454 m | 0.06239 deg | 24.003 → 23.999 |

**Every input to the 1.33 % seam measurement is identical to the shipped film's,
to 1e-5 deg.** The seam is not at risk and does not need re-measuring on pixels
to know that — nothing that feeds it moved.

### Pan rate, smear and the aim gate

| | peak pan | mean | worst smear @4K 180° |
|---|---:|---:|---:|
| S shipped | 91.47 deg/s (f2832) | 10.29 | 84.7 px |
| B const-v candidate | 10.50 deg/s (f2811) | 3.84 | 34.0 px |
| **A lap-down** | **6.12 deg/s** (f2761) | **2.56** | **6.0 px** |

The lap-down more than halves the candidate's own peak pan and cuts its worst
smear by 5.7x, for a reason that is obvious once stated: **a camera tracking a
decelerating car has less angle to cover than one tracking a car that keeps
going.** The whip R2-851 found is not merely gone, the beat is now the calmest in
the film.

Aim gate, `6_ending`: **0.029 deg worst at f2758** against a 26.0 bound, max
subject range **342.5 m**. The shipped rig's beat-6 entry read 1000.0 m.

`worst_position_jump_m 4.2469 at f1209` and `worst_rotation_step_deg 12.957 at
f2634` are **unchanged from the R2-853 build** — beat 6 does not become the
film's worst case in either.

### The 1_assembly FAIL is not mine and is not new

`1_assembly FAIL — subject reaches 1.155 of the half-frame at frame 431` appears
identically in A, in B, and in the previous agent's R2-853 build, and R2-861
already proved it reproduces with the **original, unmodified** `build_camera_rig`
on the shipped sheet. It belongs to whoever owns the beat-1 re-pace. **A film
cannot be rebuilt from this sheet until f431 is resolved**, and that is true with
or without this change.

---

## R2-945 — the car is in the picture on all 264 frames and never below 51 px

**MEASURED** by projecting `carpath.Car` through each built path with a
rectilinear projection (R2-858's correction: a perspective camera is
rectilinear, `ndc_x = (loc_x/fw)/tan(hfov/2)`, not equidistant).

| arm | frames OUT of frame | worst \|ndc\| | min car px | **car px at f2978** |
|---|---:|---:|---:|---:|
| S shipped | **146 / 264** | 11.457 (f2969) | 27.9 | 79.0 |
| B const-v candidate | 0 / 264 | 0.009 (f2977) | 31.5 (f2862) | 79.0 |
| **A lap-down** | **0 / 264** | **0.000** (f2719) | **51.3** (f2817) | **230.7** |

`|ndc| = 0.000` is not a rounding of something small: the car is on the frame's
centre line to better than a pixel for the entire beat, because the aim keys are
now dense enough (R2-859's `max_stride_frames: 2`) and the subject's bearing
changes smoothly.

**230.7 px against R2-862's own ladder** — 176.7 px "a car", 236 px "a subject",
265 px "a car with a visible wing and airbox". 230.7 px is 2.92x the shipped
arm and lands 2 % below the "a subject" mark. **That is a geometric claim and
not a claim about the picture**; only the 4K still can settle whether it reads.

---

## R2-946 — the closing frame stops containing bare ground at all

**MEASURED** by reproducing R2-856's method on all three arms: a 96×54 grid
through the frustum of the actual built path, cast onto z=0, with
`build_terrain.py`'s own two meadow-scatter gates evaluated at each hit —
`D < 430 m` from the centreline (line 3808) and `smoothstep(700, 260, dcam)`
against the camera path (line 3812). Percentages are **of the whole frame**.

| frame | arm | lens | sky | grass | **bare mesh** | ground range |
|---:|---|---:|---:|---:|---:|---|
| 2860 | shipped | 18.82 | 29.6 % | 58.4 % | 11.9 % | 198 – 12,095 m |
| 2860 | const-v | 30.08 | 16.7 % | 57.5 % | 25.8 % | 250 – 18,382 m |
| **2860** | **lap-down** | 30.08 | 0.0 % | 87.0 % | **13.0 %** | 192 – 1,556 m |
| 2906 | shipped | 40.00 | 3.7 % | 73.0 % | 23.3 % | 306 – 24,533 m |
| 2906 | const-v | 54.99 | 0.0 % | 54.4 % | 45.6 % | 391 – 17,862 m |
| **2906** | **lap-down** | 54.99 | 0.0 % | 100.0 % | **0.0 %** | 249 – 618 m |
| 2978 | shipped | 74.00 | 0.0 % | 94.4 % | 5.6 % | 392 – 1,463 m |
| 2978 | const-v | 129.99 | 0.0 % | 34.1 % | 65.9 % | 644 – 2,122 m |
| **2978** | **lap-down** | 129.99 | 0.0 % | **100.0 %** | **0.0 %** | 295 – 421 m |

**R2-856's cost is paid back.** That entry recorded, honestly, that the long lens
bought patch-boundary cropping and paid for it in bare ground — 45.6 % at f2978
against the shipped 37.7 %. The reason was arithmetic: a 130 mm lens on a camera
looking 1 km away reaches from 644 m to 2,122 m, and everything past 700 m is
outside the grass scatter radius. **A 130 mm lens looking 343 m away reaches from
295 m to 421 m, and all of it is inside.** The bare ground was never a property
of the lens. It was a property of how far away the camera was pointing, which is
the same variable R2-862 identified.

**Two caveats, stated rather than buried.**

1. **My absolute numbers do not reproduce R2-856's, AND THE PICTURE REFUTES
   MINE.** I first wrote that I had not reconciled the two and that anyone acting
   on the percentages should re-derive them. Then I opened the rendered frame,
   which settles it against me. My metric calls the constant-speed arm's f2978
   **65.9 % bare mesh**; the actual 4K render of that exact frame
   (`out2/seq/r2851_4k_B_candidate/..._002978.png`) is a corner enclosed by a
   dense treeline, grass banks, tarmac, gravel and tyre walls, and there is no
   part of it a reasonable person would call untextured ground.

   The cause is that `build_terrain.py`'s **meadow grass scatter is one of
   several vegetation systems**, and I gated on its two conditions alone. A hit
   that fails the meadow test can still be carrying woodland, verge clumps or
   hedge. **"Fails the meadow gate" is not "bare".** My percentages measure a
   thing that is not what the client is looking at, and they are withdrawn.

   What survives, and it is the entire mechanism, is the **ground range** column,
   which involves no scatter model at all: the last frame reaches 644–2,122 m in
   the constant-speed arm and **295–421 m** in the lap-down. That is arithmetic
   on the frustum. It is also the only column I would now quote.

   > A metric that disagrees with the picture is not a second opinion. This one
   > was built in twenty minutes to answer the client's literal complaint, agreed
   > with a staged measurement's *direction*, and was wrong. Looking at the frame
   > cost thirty seconds and was decisive.
2. **Finer sampling cuts both ways.** The closing frame's ground sampling goes
   from ~72 mm/px to **24.7 mm/px**, so `mat_ground`'s missing 0.4–19 m detail
   band (R2-854 item 2) now lands at 16–770 px instead of 5–260. The frame has
   less bad ground in it and resolves what is there three times better. **That is
   a question only the 4K still can answer**, and R2-854's terrain items are not
   discharged by this entry.

---

## R2-947 — the film re-key: the car stage, and the bug it caught before the farm did

`work/r2941/rekey_film_R2943.py`, derived from the proven
`work/r2851/rekey_film_R2851.py`. Two stages — the car, then the camera — and it
refuses to do one without the other, because camera-only tracks a car that is not
there and car-only brakes out of a frame still pointed at the facade.

Proved on `world/car_anim.blend` (302 MB, opens locally) before going near an
8 GB film scene:

    >> STAGE RESULT: TEST_REKEY_CAR_OK
    11,088 key values rewritten on frames 2715-2978 across 9 objects
    113,988 keys at or before f2714 verified BIT-IDENTICAL
    FL wheel angle at f2936 / f2950 / f2978: 11916.96777 (delta 0.000e+00 rad)
    car position f2936 vs f2978: 0.0000e+00 m

### `pose_series` accumulates from its first sample, and slicing it rolls the tyres back 1,796 revolutions

`carrig.pose_series` builds wheel rotation as a running chord sum starting at
**zero on its first sample** — deliberately, so rolling contact is exact against
the chords the LINEAR keys actually travel (its own docstring). Handing it frames
2715..2978 therefore restarted the wheels: the first version of this stage keyed
the front-left from **11,283.23 rad at f2714 to 9.14 rad at f2715**, an 1,796
revolution snap backwards inside one frame, in the last beat of the film.

The fix is to compute all 2,978 poses and write only the tail — which costs
seconds and **buys a check for nothing**: the same call also produces values for
frames 1..2714 that this stage does NOT write, so they can be compared against
what is already in the file. Worst disagreement **4.882e-04** on values up to
14,026 rad, i.e. float32 storage. A stage that only checked what it changed could
not have seen either problem.

> The general shape, and it is the third time this project has met it: **a
> function that is correct over a whole domain is not automatically correct over
> a slice of it.** `pose_series` is right; calling it on a window is wrong.

### The car_anim gate's central claim, checked directly on the new motion

    >> STAGE RESULT: ROLLING_CONTACT_OK

| over all 2,977 intervals | |
|---|---:|
| worst \|d(spin)·r − d(chord)\| | **1.350e-12 m** |
| worst backwards wheel step | **0.000e+00 rad** |
| beat-6 speed monotone non-increasing | **True** |
| beat-6 brake dive, peak | **1.6000 deg** nose-down — the telemetry's own declared ceiling, i.e. the term clips |
| brake dive at rest | 0.0000 deg |
| beat-6 steer, peak | 0.0000 deg — the pit straight is straight |

Rolling contact is exact by construction rather than to a tolerance, because the
wheels are built from the same chord series the positions are, which is what
`pose_series` exists to guarantee.

---

## R2-948 — my own instrument was wrong twice, in opposite directions, in one hour

Recorded because both errors produced plausible numbers and one of them
manufactured a defect that does not exist.

**First: `2*acos(dot)` on a path JSON stored to 6 decimal places.** Near zero
rotation, `acos` loses all precision — a 5e-7 rounding in each quaternion
component amplifies to a **0.19 deg floor between two BIT-IDENTICAL
quaternions**. I used it to report a "0.1961 deg beat-1 difference at f751"
between two builds whose quaternions print identically. There was no difference.

**Second: the replacement was off by a factor of two.** `2*atan2(|a−b|, |a+b|)`
is numerically stable and returns **half** the rotation angle: `|a−b| = 2
sin(Δ/4)`, so the atan2 gives Δ/4 and the factor is **4**, not 2. Every rotation
number in the first revision of R2-944 was halved, and they all still looked
reasonable — 45.74 deg/s for a whip pan is a perfectly plausible whip pan.

What caught it: the halved shipped-arm peak came out at **45.74 deg/s against
R2-851's independently staged 91.5**, an exact factor of two, which is the shape
of a units error rather than a disagreement. With `4*atan2` the same instrument
reproduces R2-851's figures — 91.47 vs 91.5 deg/s, 84.7 vs 84.8 px of smear,
34.0 vs 36.5 px for the candidate — on a metric it now also verifies against
known rotations of 0.001, 0.5, 5, 45 and 179 degrees, and whose noise floor on a
6-dp round trip is **0.000e+00**.

> **An agreement is only evidence if the two instruments could have disagreed.**
> R2-858 wrote that about an angle that was projection-independent. Here it is
> the reverse and better: a *disagreement* by exactly 2.000 was the only thing
> that could have found this, and it only existed because a previous agent had
> staged its numbers where I could collide with them.

`work/r2941/qmetric.py` is the corrected metric and carries both errors in its
docstring.

---

## R2-949 — what the arrival costs, stated before anyone watches it

Three things get worse or stay unresolved, and none of them are hidden in the
tables above.

1. **The last 1.75 s is a car at rest under a lens push on a static camera.**
   The camera holds from f2906 and the car stops at f2936, so frames 2936-2978
   contain no motion at all except the 55 → 130 mm push. R2-852 named exactly
   this gesture as the defect in the shipped ending — *"a lens push on a frozen
   camera … what a still photograph being zoomed looks like"*. The difference I
   am claiming is that there is now a subject in it and the stillness is the
   subject's, not the camera's: the last thing that happens in the film is the
   car stopping. **That is an assertion about a picture and it is the one thing
   in this entry that a metric cannot settle.**
2. **R2-853's "the hold breathes" is spent.** That entry earned 2.89 deg of pan
   across f2906-2978 because the camera was still tracking a moving car. Tracking
   a stopped car is 0 deg. The hold is a hold again.
3. **The closing frames contain no sky and no horizon at any lens.** Registered
   BEFORE watching, so it cannot be rationalised afterwards. The camera holds
   140 m up and 313 m out, so the car sits **24.10 deg below horizontal**, and
   the frame's half-vertical angle only reaches that at about **22.6 mm** — where
   the car is 40 px. Every lens that makes the car legible puts the horizon out
   of frame:

   | lens | car px | frame width at the car | horizon |
   |---:|---:|---:|---|
   | 45 mm | 79.8 | 274.3 m | 11.42 deg above frame |
   | 74 mm (shipped) | 131.2 | 166.8 m | 16.31 deg above frame |
   | 85 mm (R2-856's suggestion) | 150.7 | 145.2 m | 17.31 deg above frame |
   | **130 mm (candidate)** | **230.4** | **94.9 m** | 19.65 deg above frame |
   | 160 mm | 283.6 | 77.1 m | 20.48 deg above frame |

   R2-856 flagged that *"a closing frame with no horizon in it is part of why
   both read as a plan rather than a view"*, and its proposed remedy — ~85 mm
   with the car in the lower third — **is not available at this camera
   position**; it was costed against a car 1 km away at an 8.4 deg depression,
   and the depression is now 24.1 deg. This is a property of the declared hold,
   not of the lap-down: sky leaves the frame around f2830 in this arm and does
   not come back. It is the strongest argument for revisiting the hold's
   altitude, and it is not this task's to move.

4. **The wound is still gone.** R2-857 costed the loss of beat 3's callback
   honestly and this change does not recover it — it makes it further out of
   reach, because the camera now ends framed tight on a car 343 m away. If the
   ending is ever to have both, it is a different camera, not a different car.

There is no version of this beat where the car is close AND still moving at
f2978. It is arithmetic, not taste: covering only ~230 m in 11 s from 89.767 m/s
means a mean speed of 21 m/s, so the car must spend most of the beat slow or
stopped. Every profile I tried that kept it moving to the last frame put it 390 –
430 m out and 185 – 200 px. Three families were tried and the trade did not move.

---

## R2-950 — WATCHED

Pending. 264 frames at 720p (`watch/R2943_ending_LAPDOWN.mp4`) and 4K stills at
f2760, f2811, f2937, f2978, against the R2-853 constant-speed arm already
rendered at `out2/seq/r2851b6` and `out2/seq/r2851_4k_B_candidate`.

**Nothing in R2-941..R2-949 is a claim that the ending now works.** R2-862's
whole finding was that the geometry was right and the picture was not, and the
only thing that found it was watching all 264 frames and the stills at 1:1. A
rung-1 frame cannot tell you whether a car reads at 343 m; the 4K still can.

### The A side, looked at first, so the comparison is honest

Before rendering anything of my own I opened the two arms already on disk at 1:1.
**R2-862's verdict is correct and I am recording that I checked it rather than
inherited it.**

* **Constant-speed candidate, f2978, 130 mm.** A handsome, deep, correctly-hazed
  aerial of a circuit corner — treeline, banking, kerbs, gravel, tyre wall. At a
  300×169 crop of the exact frame centre the car is a **pale blue-grey horizontal
  smear about the width of the gravel trap's rake marks**, sitting in front of
  the tyre wall's shadow. You can find it once you know it is at frame centre.
  Nothing about the image asks you to look there. *"A handsome aerial of a
  circuit corner with no subject in it"* is not rhetoric; it is a description.
* **Shipped, f2978, 74 mm.** Pit building, grandstand, paddock, containers,
  crowd, and the breached showroom mid-frame — dense, detailed, and no car in it
  anywhere. R2-855's *"a 65 px wound in a truck park"* is also literally
  accurate. The client's *"patches in the land"* are visible in this frame as
  the flat olive-brown fields upper right, which is R2-854's Voronoi partition.

Worth stating because it cuts against a convenient story: **the world is not the
problem in either frame.** Both are well-built pictures. The ending failed for
the reason R2-862 gave and for no other.

### Pre-registered, so it cannot be rationalised after the fact

Written before a single frame of this arm exists. Five ways this can fail, and
what each looks like:

1. **The car reads as broken down, not as a lap-down.** A car stopped on the
   racing line is, in every other context, a retirement. The defence is that the
   audience watches it brake continuously for four seconds first, which a
   failure does not do — but that is an argument, not a measurement, and the only
   test is whether the last frame looks like an ending or an incident. **Watch
   f2820-2936 for whether the deceleration reads as a driver or as a failure.**
2. **The last 1.75 s is dead.** Nothing moves in frames 2936-2978 but the lens.
   If it reads as a zoom into a photograph, R2-852's criticism has been moved
   rather than answered, and the answer is R2-949's fallback: do not stop, end
   at ~208 px still rolling at ~10 m/s and keep the pan alive. That costs 22 px
   and is already costed.
3. **No horizon anywhere in the closing 5 s** (R2-949 item 3). If the frame
   reads as a plan rather than a view, the lens is not the lever — the hold's
   140 m altitude is, and that is somebody else's key.
4. **3.60 g looks violent at 24 fps.** 109.7 px of on-screen travel per frame at
   f2715 falling to 5.98 px by f2820 is a very fast collapse. If it snaps rather
   than eases, lower `K_AERO` — it costs distance, and R2-942's table says the
   whole pit straight is within 5 % of the target anyway.
5. **The car is occluded.** No ray-cast was run on the new resting position; the
   264 frames answer it directly and more cheaply than a sweep would. R2-651's
   `BR_FenceMesh_L03` finding was retracted in R2-852, and the fence re-measures
   6.76 m OUTSIDE the surface, so nothing is expected — but nothing was proved.

If two or more of these land, the arrival has not fixed the ending either, and
that is what this file will say.

### The grade was not touched, and the constraint that protected it still holds

Nothing in R2-941..R2-950 changes the view transform, the look or the exposure.
The re-key script asserts **3840×2160 / AgX / look None / exposure −3.628** and
refuses to save if any of them drifted; its own output line reports what it saw.

**The standing constraint — no crushing saturation, no lifting blacks — is not
discharged by this change and must not be treated as if it were.** R2-862
measured the car at 1 km as *brighter* than its surround with a **0.14
blue-minus-red** colour break doing the work, and warned that a routine grade
pass would destroy the only thing making it findable. At 231 px the car is
resolved rather than inferred, so it no longer *depends* on that break — but
every other distant read in the film still does, the lap is 63.5 s of distant
car, and a grade is one pass over the whole duration by the brief's own law.
**The constraint outlives this task, and this task is not evidence for relaxing
it.**

---

# R2-951 .. R2-965 — THE AUDIO REBUILD AGAINST THE LAP-DOWN

Appended by the audio agent. Owner of `audio/`, `tools/audio_ending_ab.py` and
these entries only.

---

## R2-951 — the shipped `audio/out/master.wav` is not reproducible from this tree, so it cannot be the A-side

The brief asks for the closing 11 s to be rebuilt while frames 1-2714 stay
bit-identical to "the current master". The current master is
`audio/out/master.wav`, written 2026-08-02 14:29. Three of its inputs have moved
since:

| input | what happened | when |
|---|---|---|
| `world/camera_rig_path.json` | 710 of 2,978 frames moved, worst 9.206 m at f1; the changed frames are f1-716 (beats 1-2), contiguous but for six single-frame gaps | uncommitted, mtime 2026-08-03 21:06 |
| `docs/beat_sheet.json` | rewritten | commit 2e13c12, 2026-08-07 04:57 |
| `docs/circuit_spec.json` | rewritten | same commit |

The camera rig IS the listener (`audio/scene.py:CameraPath`) and the beat sheet
IS the film clock (`audio/clock.py:Clock`). A re-render of this tree cannot
reproduce the shipped WAV anywhere in beats 1-2 no matter what the ending does,
so a bit-comparison against it would have measured R2-731..760's camera move and
reported it as an audio regression.

**The A-side is therefore a control rendered from THIS tree** with the lap-down
switched off at its own A/B switch:

    F1_LAPDOWN=0 .venv/bin/python -m audio.master --out audio/out/ab/master_A_nolapdown.wav

which is the pre-R2-943 constant-speed extrapolation and nothing else
(`anim/carpath.py:LAPDOWN_ENABLED`). The shipped file is kept at
`audio/out/ab/master_SHIPPED_aug2.wav` for reference only.

---

## R2-952 — the audio's car and the picture's car are now one object to 8.0e-14 m

R2-943's `audio/scene.py` edit built its own `LapDown` from
`vend = v_world[-1]` = 89.766125 m/s — the Savitzky-Golay derivative of the
position track — while `anim/carpath.Car` builds its from the CSV's
`speed_ms[-1]` = 89.767080. Two tables, two seeds 0.955 mm/s apart, `t_brake`
4.9e-07 s apart, and the audio's car 2.349 mm from the picture's at f2936.

**Changed: the audio now reads the picture's seed.** R2-026's rule is "follow the
car the AUDIENCE sees", and past `t_end` there is no independent position track
to differentiate — the car's position IS `LapDown`'s distance along the
centreline. So the same rule that makes the engine follow `v_world` ON the
telemetry makes it follow the lap-down's own v PAST it. Measured on the picture's
own frame convention (`world_of_frame[f]`, which is what
`anim/build_car_anim.py` keys), f2650-2978:

    worst |position| audio.sample vs carpath.Car.state    8.039e-14 m
    t_brake                                               identical to the last bit

Cost, stated: `speed` steps by 0.955 mm/s at `t_end` — 1.1e-5 relative, i.e.
1.8e-4 cents of engine pitch and 1.4e-4 dB of tyre level, under a 90 ms
driveline lag. The `F1_LAPDOWN=0` control keeps the pre-R2-943 `v[-1]` of the
chosen speed source, so the A-side is untouched.

A FRAME-CONVENTION TRAP, recorded because it has now caught one agent:
`CameraPath.frame_t` puts frame f at film t = (f-1)/24 (the START of its display
interval) while `build_car_anim` keys frame f at `world_of_frame[f]` (the END).
The two are one whole frame apart. A position check will not see it; a SPEED
check will, and it is the difference between reading 166.9 km/h and 193.5 km/h
at f2760.

---

## R2-953 — R2-943's edit put a step in `accel_long` at `t_end`, and my first fix for it was wrong

`out["accel_long"][past] = -aa` is a step, not a continuation. The CSV's last row
is `accel_long_ms2 = +1.5073` (the car is flat out) and the lap-down's flat-out
segment is a CONSTANT SPEED, so `-aa` is exactly 0.000 there:
`accel_long` went `+1.5073 -> 0.0000` between two adjacent samples at world
t = 72.583333.

That number is not decoration. `engine.throttle_from_spec` inverts it directly:

    v = 89.77:  a_drag = 0.00092 v^2 = 7.412   a_pow = min(800/v, ...) = 8.912
    accel_long = +1.5073 -> thr = 8.919/8.912 = 1.001 -> clipped to 1.00
    accel_long =  0.0000 -> thr = 7.412/8.912 = 0.832

so the combustion gate `(0.35 + 0.65*load)` stepped 1.000 -> 0.918 in one sample:
a 0.74 dB discontinuity 46 ms before the beat-5/beat-6 seam, and a claim that the
driver lifted BEFORE the line, which is the opposite of what R2-943 says the shot
is.

**FIX 1, WRONG.** I first blended the CSV's last acceleration out over
`LAPDOWN_ONSET_S` (0.30 s) from `t_brake`. It removed the step and it was wrong:
it left `accel_long` at **+0.796 m/s^2 at f2715**, 23 ms after the driver had
lifted, while the `speed` field returned by the SAME call was already falling.
Two fields of one sample disagreeing about which way the car is going is a worse
defect than the step it replaced. Caught by a peer measuring f2715 directly
rather than trusting the continuity scan I had run — the scan was true and
answered a different question.

**FIX 2, SHIPPED.** The handover runs over the FLAT-OUT SEGMENT itself — `t_end`
to `t_brake`, 46.2 ms, the 4.15 m the telemetry stops short of the line — so past
`t_brake` accel_long is exactly `-aa`, which is exactly `-carpath.Car.decel(t)`:

    frame   world      v (km/h)   accel_long   -car.decel(t)
    2714   72.61153     323.2       +0.509        -0.000     (flat out, 4.15 m short)
    2715   72.65320     323.1       -0.685        -0.685
    2716   72.69487     322.8       -4.708        -4.708
    2720   72.86153     311.6      -31.872       -31.872
    2760   74.52820     166.9      -16.374       -16.374
    2820   77.02820      59.8       -9.248        -9.248
    2880   79.52820      12.4       -2.142        -2.142
    2906   80.61153       5.7       -1.417        -1.417
    2936   81.86153       0.0       +0.000        -0.000

    largest change in accel_long per 0.1 ms sample, 72.40-73.30 s : 0.0185 m/s^2
    samples with accel_long > 0 past t_brake                      : none

The speed column reproduces the lead's brief digit for digit. Guarded by
`if self._lapdown is not None` so the control keeps the pre-R2-943 held value.

NOTE FOR THE PICTURE, not audio's to fix: `carrig.body_pitch` past `t_end`
returns `-car.decel(t)` = 0 through the same flat-out segment while the last
KEYED pitch comes from ax = +1.5073. A 0.08 deg step. Invisible; stated for
completeness.

---

## R2-954 — the car stops at f2936 and the engine's injectors were cut: a stall, not an idle

With the car stopped, `gear_and_rpm` correctly holds the crank at
`RPM_IDLE = 4300` (`rpm = max(rpm_wheel, hold)`), but `throttle_from_spec`
returned `thr = 2.1e-05`, so `fuel = clip(thr/0.06) = 3.5e-04` and the injectors
were shut. The last 1.75 s of the film — the last sound in it — was a V6 being
MOTORED at 12.8 % of its combustion gate.

A category error, not a tuning error. `throttle_from_spec` inverts a ROAD-LOAD
model: the throttle needed to produce a given road acceleration THROUGH A CLOSED
CLUTCH. Below the speed at which first gear pulls idle there is no closed clutch
and the model has nothing to say. That speed is derived, not chosen:

    v_clutch = RPM_IDLE / (r1 * FD * 60) * 2*pi*R
             = 4300 / (2.9400 * 6.4471 * 60) * 2.2619 = 8.55 m/s

and `gear_and_rpm` already computes exactly this, as `lock = rpm_wheel / rpm`.

**Fixed** in `audio/engine.py`: `thr = maximum(thr, IDLE_THROTTLE * (1 - lock))`,
`IDLE_THROTTLE = 0.08` — the figure the PRE-LAUNCH idle already used, now named
once instead of written twice.

**A bit-exact no-op before the ending, measured rather than assumed.** Scanned at
1 kHz over the whole world span (-35 .. +85 s), the floor raises `thr` at exactly
zero samples before `t_end`; the first sample it touches is world t = 78.061 s,
5.478 s past the end of the telemetry, which is the moment the decelerating car
drops through 8.55 m/s. It cannot bite on the lap: the lap's minimum speed is
7.80 m/s (the hairpin, where `lock` does fall to 0.0996), but the driver is on
the throttle there and the road-load model's own minimum `thr` wherever
`lock < 1` is 0.301 — 3.8x the largest possible floor. `np.maximum` returns its
first argument bit-for-bit when it wins, so those samples are untouched, not
merely unchanged to a tolerance.

---
