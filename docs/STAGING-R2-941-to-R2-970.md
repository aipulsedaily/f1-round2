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

### The 0.08 deg pitch step at `t_end` is PRE-EXISTING and is deliberately not fixed

Raised by the audio rebuild (R2-953) and checked here. `carrig.body_pitch`
returns the telemetry's own `pitch_c` up to `t_end` — where `ax = +1.5073`, i.e.
0.080 deg nose-UP under power — and 0 immediately after. The step lands between
frames 2713 and 2714, inside the 46.2 ms flat-out segment.

**It is not mine.** The shipped `body_pitch` returned a flat `0.0` for the entire
extrapolation, so the identical step is in the shipped film. R2-943 only changes
behaviour past `t_brake`; between `t_end` and `t_brake` it still returns 0.

**And I am declining to fix it, which is the part worth writing down.** Carrying
the telemetry's last acceleration across those 4.15 m would cost **f2714's car
pose its bit-identity with the shipped film** — the single strongest claim in
R2-944 and R2-947, and the one that makes the f2714/2715 seam safe without
re-measuring it. The gain is 0.080 deg of body pitch, which at a 3.600 m
wheelbase is **5 mm of nose height**, on one frame, at 85 m, through a 24 mm
lens: about 0.02 px. **Trading a proof for 0.02 px is a bad trade** and the
tidiness of not leaving a known step is not worth it. Recorded so the next agent
does not "fix" it and quietly spend the guarantee.

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

### R2-944b — the one path by which a beat-6 key can still reach frame 2714, closed

Prompted by the audio rebuild, which found **three** whole-film reductions that
turned a change to the last 11 s into a change from sample 42 onward. The picture
has one structural analogue and it is worth naming rather than assuming away:
**Cycles reads the F-curves at SUB-FRAME times for motion blur**, so frame
2714's shutter samples into the LINEAR segment 2714 → 2715, whose far endpoint
this change moves. Frame 2714 being bit-identical *at its own key* does not by
itself settle what its blur integrates.

    >> STAGE RESULT: SEAM_MOTION_BLUR_CLEAN

| | |
|---|---:|
| car delta at f2713 and f2714 | 0.000000e+00 m |
| car delta at f2715 | **3.540e-05 m** |
| car delta at f2716 | 1.843e-03 m |
| worst displacement inside f2714's shutter, CENTER (Blender default) | 8.850e-06 m = **2.666e-04 px** at 4K |
| worst, if the shutter were END-aligned | 1.770e-05 m = 5.331e-04 px at 4K |

The reason it is this small is the same reason R2-941 matters: at f2715 the brake
has been on for **23.6 ms** and the onset smoothstep is only 1.8 % applied, so
the car has lost 35 microns against the constant-speed arm. The camera is
bit-identical at f2715 in both position and rotation, so its own blur is
untouched. **Half a thousandth of a pixel** is not a tolerance, it is an absence.

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

> **CORRECTION, and it changes the decision.** I first wrote here: *"There is no
> version of this beat where the car is close AND still moving at f2978. It is
> arithmetic, not taste."* **That was wrong, and it was wrong because my search
> was too coarse, not because the arithmetic says so.** I had swept `v_end` over
> 8–18 m/s, which is a cool-down cruise, and every such profile does land 390–430
> m out at 185–200 px. Sweeping 4–12 m/s instead — a car at *walking-to-jogging*
> pace, still visibly rolling but covering almost no ground — changes the answer
> completely.

**The fallback, now measured rather than estimated.** `A_ROLL 0.0, A_BRAKE 6.0,
K_AERO 0.0046, V_RELEASE 22.0`:

| | shipped lap-down (R2-943) | fallback: never stops |
|---|---:|---:|
| peak deceleration | 3.60 g | 3.91 g |
| distance travelled | 226.5 m | 256.7 m |
| where it ends | pit straight, 23.5 m short of T1 | 6.7 m into T1's entry |
| distance to camera | 342.9 m | 355.0 m |
| **car at f2978** | **230.7 px** | **222.6 px** |
| speed at f2978 | 0.00 m/s | **4.08 m/s = 14.7 km/h** |
| on-screen motion at f2978 | 0.00 px/frame | **6.63 px/frame** |

**It costs 8 px, not the 22 I claimed.** For that it buys back visible motion on
the last frame, the camera pan in the hold that R2-949 item 2 says the stop
spends, and it removes the "stopped on the racing line reads as a retirement"
risk entirely — a *moving* car in a corner entry is a cool-down lap and nothing
else. It arguably also lands a better moment: the film would end on the instant
*before* rest rather than after it.

**I am not switching to it.** The render of the stopping version is already in
flight and an independent agent is judging it; changing the thing under
assessment while it is being assessed is how three passes of camera work in a row
came to report success. If R2-950 finds the stillness dead, this is a
four-constant edit to `anim/carpath.py` with the numbers already measured and no
other file touched. **What I am doing is correcting the record**, because I had
written the door shut with the word "arithmetic" and it is not shut.

---

## R2-949b — the A/B is across two film builds, and f2715 is a free control for it

**Recorded before the frames exist, because it is the kind of confound that is
invisible once a verdict has been formed.**

| arm | film build | when |
|---|---|---|
| `r2851b6`, `r2851_4k_B_candidate` | `film16_R2851.blend` | 2026-08-04 16:26 |
| `r2943b6`, `r2943_4k` (mine) | `film17_breach.blend` | 2026-08-07 06:09 |

So the difference between the arms is **the car's motion plus 62 hours of film
construction.** R2-917 checked the *camera* across the same two builds and found
the delta confined to beats 1-2 — but a camera check says nothing about what the
car is made of, and at least one item in the gap bears directly on the question
being asked. `NEXT-REBUILD.md` lists a car-paint change worth **albedo 0.0121 ->
0.0372** and three-quarter diffuse **7.32 % -> 19.96 %**. A car that reads better
at 343 m may be reading better because it returns three times the light.

**The control is free and exact: frame 2715.** The driver lifts BETWEEN f2714 and
f2715 (R2-941), so at f2715 the car has lost **35 microns** and the camera's
position, rotation and lens are all `0.000e+00` different between the arms.

> **Any pixel difference at f2715 is the film build. None of it is the ending.**

Both 720p sequences contain f2715. Diffing them measures the confound directly
instead of arguing about it, and whatever it shows must be discounted from every
later frame before any improvement is credited to the arrival.

That control was not designed. It falls out of where the start/finish line
happens to sit relative to a beat boundary, which is the same accident that makes
the whole change possible. **Noting it because the honest version of R2-950 needs
it and the flattering version does not.**

---

## R2-949c — exec starvation: an 8 GB open cannot run while any render queue is non-empty

**MEASURED** on broker 8761 by the render agent, and recorded here because it is
structural, it is currently costing two agents about seven hours each, and one of
them is not us.

```
ExecMemoryShort: opening film17_breach.blend (7.98 GB) needs about 43.9 GB
free and the box has 6.3 GB — the render worker is holding a scene of its own.
```

An 8 GB blend needs ~44 GB of the box's 48.9 GB, so **no `rq exec` job can be
admitted while the render worker holds a scene.** The re-key has been in an
admit-and-bounce cycle for ninety minutes without its child ever starting —
`exec_sec` is null and there is no `>> STAGE RESULT:` line to judge, which is
exactly why the rule is to judge only on that line.

**The broker has no starvation guard for this.** Any agent feeding the render
queue indefinitely blocks all 8 GB exec work indefinitely, regardless of
priority, because the block is a memory admission test rather than a queue
ordering. R2-860's object-ID raycast has been starved by the same mechanism
since 07:39 and sits *ahead* of us at prio 40.

**Nothing was done about it, deliberately.** Cancelling, re-prioritising or
raising our own priority would take the window from a job we were explicitly told
to let land. The queue's arrivals have stopped — 6 frames queued in the last two
hours against 167 drained — so it will clear on its own. **Flagged for whoever
owns the broker; the fix is not ours to deploy** (`~/vast-render` has ten
uncommitted files and two changes that have never run in production).

---

## R2-949d — the film re-key LANDED, and it confirms the confound as well as the change

`out/exec/bd0345da6cb3/rekey_R2943.log`, broker 8760, on
`render/film17_breach.blend` → `film17_R2943.blend` (7,610.0 MB).

    >> STAGE RESULT: FILM_SCENE_REKEYED_R2943

The car stage reproduced the local dry run on `world/car_anim.blend` **digit for
digit**, which is the check that the 8 GB scene is the same object the 302 MB one
was:

```
11,088 key value(s) rewritten on frames 2715-2978 across 9 object(s);
   4,980 of them actually moved;
113,988 key(s) at or before f2714 verified BIT-IDENTICAL.
lift at world t 72.62957 (between f2714 72.61153 and f2715 72.65320),
   peak 35.27 m/s^2 = 3.60 g, at rest 9.226 s later after 226.52 m.
f2978: car at (502.93, 315.43, -0.00), speed 0.000 m/s, wheel spin 9.1400 rad
worst float32 storage error 4.875e-04; worst disagreement with the SHIPPED keys
   on the 2,714 frames this stage did NOT write: 4.882e-04
```

**The output file existing was never the evidence and it is worth saying why.**
`build_camera_rig.main()` saves to `--out` itself, part-way through, via
`save_clean` — the log shows two separate `Saved as "film17_R2943.blend"` lines.
A half-re-keyed blend lands at the identical path with an identical size. What
settles it is the LAST `>> STAGE RESULT:` line, and the four things it certifies:

| check | result |
|---|---|
| world datablock | `SKY_World` restored (the rig had swapped in `R2_ProceduralSky`) |
| atmosphere slab | both `SKY_AirColumn` and `SKY_AirBoundary` present |
| cloud-parallax drivers | 2 bound to `ONER`, **0 dangling** |
| object count before / after | **35,304 / 35,304** — nothing dropped |
| delivery | 3840×2160, AgX, look None, exposure **−3.628** |
| aim gate `6_ending` | **0.03 deg at f2758**, max subject range **342.5 m** |

Had the world restore failed, the frames would have been lit by a different sky
from the A-side. That is not an A/B, it is two different films, and it would have
looked entirely plausible.

### Two corrections to earlier entries in this file

**1. The beat-1 FAIL is NOT an artefact of building against `beat1_anim.blend`.**
R2-944 recorded the `1_assembly FAIL … 1.155 of the half-frame at frame 431`, and
I speculated it might be input-dependent because the previous agent's re-key of
`film16_R2851` reported `1_assembly PASS`. **It is not.** The identical FAIL, to
the same 1.155 and the same frame 431, appears here on a full film scene. The
difference from that earlier run is the *sheet*: it predated R2-861's re-base and
carried the old 23-key beat 1, where this carries the re-paced 19-key one.
R2-861's conclusion stands unqualified — **a film cannot be rebuilt from this
sheet until f431 is resolved**, and that is true on any input.

**2. The two film builds really are different, and now by a countable amount.**
`film16_R2851` reported **35,283** objects; `film17` reports **35,304** — 21 more,
which is exactly the object count `NEXT-REBUILD.md` gives for the showroom-ceiling
library. So `film17` demonstrably carries at least one item from the 62-hour gap,
and the presumption must be that it carries the car paint too. **R2-949b's
confound is confirmed rather than merely suspected**, and the f2715 control is
now required reading before any frame later than f2715 is credited to the
arrival.

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

### THE BUILDER'S OBSERVATION — 4K stills, looked at. NOT the verdict.

**I built this, so this is evidence, not adjudication.** An agent that did not
build it is judging the same frames independently and its verdict goes in
`docs/STAGING-R2-971-to-R2-990.md`. Where we disagree, prefer it — three passes
of camera work in a row reported success on this ending from evidence weaker than
what is below.

All four stills, 3840×2160, `blank=OK`, one `spec_hash c49ed585b3812fe5`,
233–304 s each.

**f2978, the last frame of the film, at 1:1.** The car is not a smudge. It is a
Formula 1 car with a **visible front and rear wing, airbox, halo, the driver's
helmet, four tyres with coloured rims, and its own shadow on the tarmac.** At
231 px it is past R2-862's top rung — that ladder described 265 px as *"a car
with a visible wing and airbox"* and this delivers it at 231. Against the
constant-speed arm's *"pale blue-grey horizontal smear the width of the gravel
rake marks"* at the same frame, it is not an improvement in degree.

**The wide frame is not empty, and R2-943b was wrong about that.** I predicted
*"no architecture and no start/finish line"*, having projected only the pit
building's declared box. The frame in fact contains the racing surface, red-and-
white kerbing, catch fencing carrying **advertising hoardings**, run-off, grass,
and **a grandstand corner with visible spectators at bottom-left**. The
prediction failed because I tested one object and concluded about a frame — the
same error shape as R2-946, one entry apart. **R2-943b's conclusion that the
resting station is physically determined still stands; its description of what
would therefore be in shot does not.**

**What R2-949 got right.** No sky, no horizon, at the predicted ~24 deg
depression. The frame is a high, plan-ish aerial. That was registered before the
render and it is exactly what arrived.

**And the thing I cannot settle, which is the whole reason R2-949b exists.** That
car is *bright* — saturated blue, high-contrast livery, orange rims, orange
helmet. Some unknown share of its legibility is `film17`'s car paint at ~3x the
albedo of the `film16` build both comparison arms come from, and **at f2760 the
car already reads clearly at 83 px, where R2-862's ladder called 79.5 px a
smudge.** That is either the haze difference (157 m against 1,000 m), or the
paint, or both, and this still cannot separate them. **The f2715 diff in the
720p sequences is the only clean instrument and it has not arrived yet.** Until
it does, "the arrival fixed the ending" is not a claim this file is entitled to
make — only "the ending now has a subject in it", which is a claim about the
film and not about the cause.

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
## R2-955 — the ending was changing the whole film, and it was not the ending's fault

Before comparing any master I ran the cheap version of the brief's own question at
the SOURCE: render every world-clock layer twice, once with `F1_LAPDOWN=0` and
once with `F1_LAPDOWN=1`, and compare with `==` for every world time up to
`t_end`. `tools/audio_prefix_identity.py`. The first run:

    speed accel_long accel_lat slip wheel_w heading s_m track_s pos rpm gear
                                                    all bit-identical, 0.000e+00
    eng   (the dry engine)                          NOT identical, worst 1.360e-01
    tyre  (the dry tyre bed)                        NOT identical, worst 1.192e-06

Every INPUT to the engine was bit-identical for the whole 72.58 s and its OUTPUT
was not. That is not a rounding story; it is a whole-film reduction somewhere
inside `synth`. Three were found, all of the same shape — a value read from the
future — and they are R2-956 and R2-957.

Recorded because of what it implies beyond this defect: **any** change to **any**
part of this film was silently re-deciding the engine everywhere else in it, and
no gate in `audio/verify.py` looks for that. It would have been invisible for as
long as nobody rebuilt one beat and checked another.

---

## R2-956 — `f_crank.mean()`: one scalar made every sample of the engine a function of every other

    ph_crank += 0.004 * np.cumsum(jit) * (2*pi/sr) * f_crank.mean()

`f_crank.mean()` is a reduction over the ENTIRE world grid. The lap-down drops
the last 11 s from ~13,000 rpm to a 4,300 rpm idle, which moves that mean, which
rescales the combustion jitter over all 124 s.

Measured on a 20 s bench where only the SECOND HALF of the speed track was
changed (60 m/s -> 20 m/s) and the first half was held identical:

    rpm over the first half              bit-identical
    engine signal over the first half    first difference at sample 42 of 960,000
    delta RMS over the first half        0.0287   against a signal RMS of 0.0489
                                         i.e. the "unchanged" half differed by -4.6 dB

**It is inaudible.** Same rpm, same gears, same pipes, same firing order — a
differently seeded 0.4 % wander. And it is still a defect, because it means the
film before a change cannot be shown to survive the change, and the whole point
of R2-943 is that beats 1-5 survive it.

**Fixed:** `ph_crank += 0.004 * np.cumsum(jit * f_crank) * (2*pi/sr)`. A prefix
sum, therefore causal, and the more physical of the two statements: cycle-to-cycle
variation is a fraction of the speed the crank is turning AT THAT MOMENT, so it
is small at a 4,300 rpm idle and large at 14,400 rpm. The old form applied the
film's average to both.

CHECKED AND NOT A LEAK, stated so it is not re-investigated: `synth` has one
other whole-film reduction, `np.nanmax(f)` selecting the turbo-whine branch. The
largest order-18 shaft line the model can produce is 125,000/60 * 18 * 0.9981 =
37,428.75 Hz, which is below 0.45*sr at 96 kHz (43,200) and above it at 48 kHz
(21,600), so the branch is decided by the SAMPLE RATE and not by the film at
either rate this project uses. Left alone.

---

## R2-957 — two block loops that read 512 and 2,048 samples into the future

With R2-956 closed, the bench's first differing sample moved from 42 to 479,235 —
765 samples BEFORE the change at 480,000. Two block-processing loops set a
coefficient from the MEAN of the block they are about to write:

| where | block | reads ahead | measured |
|---|---|---|---|
| `engine.synth`, turbo shaft `demand[a0:b0].mean()` | 2048 | 21.3 ms at 96 kHz | 0.0087 on a 0.049 RMS signal |
| `dsp.tv_onepole_lp`, `fc[a0:b0].mean()` | 512 | 5.3 ms at 96 kHz | 1.2e-06 on the tyre bed |

479,235 is three samples into the 2,048-block that straddles 480,000, which is
the turbo loop identified without ambiguity.

21.3 ms of world time at `t_end` is 21.3 ms of film time (the ramp is long past,
scale = 1), and `t_end` lands at film t 113.055, i.e. INSIDE frame 2714. So the
turbo window reaches back to film t 113.034 — **frame 2713**. It is not a
rounding artefact that can be waved through; it would have made frames 2713 and
2714 differ.

**Fixed:** both take the coefficient at the block's FIRST sample instead of the
block mean. `tv_onepole_lp`'s own docstring already justifies this — the block is
far shorter than any audible change in the coefficient — and `demand` is a smooth
function of rpm through a 90 ms driveline lag and a 240/900 ms turbo inertia, so
its value at the block start and its mean over 21 ms differ by far less than the
quantisation the block structure already imposes. Neither loop now reads a sample
it has not yet reached.

**Verified on the same bench, after both fixes:**

    ENGINE  first differing sample = 480,000   (the change itself, not one earlier)
    TYRE    first differing sample = 480,000

---
## R2-958 — one shared RNG, and seven downshifts 61 seconds in the future

With R2-956 and R2-957 fixed, the SOURCE check still failed on one track:

    eng   bit-identical before t_end = False,  worst 1.102e-01
    first differing sample: index 2,198,824 -> WORLD t 10.809 s

61.8 s before the end of the telemetry, and nowhere near a block boundary. No
block-window argument can produce that; only a shared random stream can.

`engine.synth` opened ONE `default_rng(seed)` and walked it through three event
loops in order: upshift cracks, then downshift cracks, then overrun pops. The
lap-down adds seven downshifts in the last 11 s. Those seven `standard_normal`
draws are consumed BEFORE the pops loop starts, so every pop in the film was
drawn from a stream offset by them — and world t 10.809 is the first overrun of
the lap, i.e. the first pop in the film.

The upshift and downshift cracks themselves were fine by luck: `np.flatnonzero`
returns sorted indices, so the seven new events landed at the END of their own
loop. That is not a property worth relying on.

**Fixed:** every event draws from its own stream, keyed on its own sample index:

    def _ev_rng(kind, i):
        return np.random.default_rng([seed, kind, int(i)])

so neither the NUMBER of events nor their ORDER can perturb an existing one. The
film's cracks and pops are different random realisations than before; they are
the same process with the same statistics, and they are now local.

**RESULT — the claim the brief actually asks for, at the source:**

    tools/audio_prefix_identity.py --sr 48000

    speed accel_long accel_lat slip wheel_w heading s_m track_s pos
    rpm gear eng tyre                    ALL bit-identical before t_end, 0.000e+00
    >> ALL_BIT_IDENTICAL_BEFORE_T_END = True

Every world-clock source the render is built from is identical, sample for
sample, for all 72.583 s of world time up to the end of the telemetry, with the
lap-down on and off. The finished masters still differ by one broadband gain —
see R2-959 — and that is a mix-bus fact, not a rebuilt beat.

STILL LATENT, NOT TRIGGERED, recorded so the next agent does not have to find it
the hard way: `layers.tyres` has the same shape of hazard — one `rng` consumed
inside two branches that are gated on WHOLE-FILM maxima
(`surf["gravel"].max() > 1e-3`, `surf["glass_debris"].max() > 1e-3`). If a future
change ever puts a wheel on the gravel, the glass-debris crackle in beat 3
changes with it. It does not fire on this telemetry (max lateral offset on the
lap is 10 mm) and `tyre` measures bit-identical, so it is left alone.

---
## R2-959 — what R2-956..958 cost the film, measured on the gates rather than asserted

The three causality fixes change the engine everywhere in the film: a different
random realisation of every crack and pop, a jitter that scales with
instantaneous rather than mean crank speed, and two filter coefficients read at a
block's start instead of its middle. None of that is audible, but "not audible"
is a claim, so it was put through `audio/verify.py` against the same WAV the
stored report was written from:

| gate | stored report (2026-08-02) | after R2-956..958 |
|---|---|---|
| levels | PASS | PASS |
| seam | PASS | PASS |
| external_assets | PASS | PASS |
| pitch | PASS | PASS |
| doppler | PASS | PASS |
| pitch: corr(measured f0, rpm/60*3) | 0.99830 | 0.99754  (threshold > 0.97) |
| pitch: fraction within 50 cents | 0.99095 | 0.98643  (threshold > 0.85) |
| pitch: median abs error | 0.979 cents | 1.288 cents |
| seam: worst d3 local percentile | 88.49 | 88.49  (threshold < 99.9) |
| seam controls (splice, 3 dB step) | both correctly FAIL | both correctly FAIL |

The median pitch error rises by 0.31 cents — three tenths of one hundredth of a
semitone — and that rise is the fix working: the jitter is now 0.4 % of the
INSTANTANEOUS crank speed, so it is larger at 14,400 rpm than the old film-mean
form made it, and the f0 tracker sees exactly that. Everything else is unchanged
to the digit.

---
## R2-960 — the shipped film opens with a click, and it is the END of the film wrapped onto the start

With every source proved bit-identical before `t_end` (R2-955..958), the two
finished masters still differed over frames 1-2714 by 8.02e-01 — and a best-fit
broadband gain of +0.0200 dB did not reduce it. A gain difference cannot do that,
so something structural was still crossing from the ending to the front.

Locating it by frame:

    worst frame over the whole film      FRAME 1,  |delta| 0.8021
    all other frames 1..2714             |delta| ~1e-3 .. 4e-3  (the 0.02 dB gain)

Frame 1. Not frame 2713, not the seam — the FIRST FRAME. And the cause is in the
shipped master too:

| master | peak inside frame 1 | at | programme RMS, frames 2-24 |
|---|---|---|---|
| shipped 2026-08-02 | **0.8505** (-1.4 dBFS) | sample 29, t = 0.60 ms | 0.0233 (-32.7 dBFS) |
| A, lap-down off | 0.8504 | sample 29 | 0.0217 |
| B, lap-down on | 0.1163 | sample 106 | 0.0222 |

**A 32 dB transient on the first frame of a film that opens on a silent
showroom.** It has been in every master this project has produced, no gate looks
at frame 1 (`seam_gate` only visits beat BOUNDARIES: frames 793, 865, 1057, 1191,
2715), and it is plainly visible as a bright vertical stripe at t = 0 in
`audio/out/master_spectrogram.png` once you know to look.

    audio/master.py:392
        interior = np.stack([tail * 0.75 + np.roll(tail, d1) * 0.35,
                             np.roll(tail, d2) * 0.75 + tail * 0.30], axis=1)

`np.roll` is CIRCULAR. Used as a stereo decorrelation delay on the showroom's
2.4 s FDN tail, it wraps the LAST d samples of the tail onto the FIRST d. The
burst is exactly `d2 = int(0.0113 * sr) = 1,085` samples long — 11.3 ms — which
is the tell: it is not a filter startup, it is a wrap, and its length is the
delay constant.

And that is why the ending reached frame 1. In A the film ends with a car at
323 km/h exciting the room; in B it ends with a car stopped 490 m outside it. The
tail's last 11.3 ms is 17 dB quieter in B, so B's frame 1 is 17 dB quieter — the
two renders disagreed about the FIRST FRAME because they disagreed about the
last.

**Fixed:** `dsp.delay(x, n)`, a shift with a silent head.
`np.roll(x, n)[i] == x[i-n]` for every `i >= n`, so the replacement is identical
everywhere except the first `n` samples, which is precisely the wrapped-in
material. Applied at all four sites that used a roll as a delay:
`master.py` (showroom tail x2, room tone), `layers.wind_at_camera`,
`layers.outdoor_bed`. `verify.py`'s two rolls are deliberate — they BUILD the
splice and jump-cut positive controls — and are left alone.

---
**Measured after the fix**, same window, same measurement:

| master | frame-1 peak | above the following second's RMS |
|---|---|---|
| shipped (np.roll) | 0.8505 | **+31.3 dB** |
| A, after `dsp.delay` | 0.0507 | +7.2 dB |

7.2 dB is an ordinary crest factor for a noise bed. The film no longer opens with
a transient.

## R2-961 — the brief's bit-identity, delivered: the residual is two mix-bus scalars, and both are named

With R2-956..960 fixed, A (lap-down off) and B (lap-down on) rendered from the
same tree:

    frames 1-2714   worst |A - B|   5.800e-03   (-44.7 dBFS)
                    median          1.641e-03
                    frame 1         3.234e-04
    frames 2715-2978 worst          3.384e-01   at frame 2732

That residual is not a leak. It is **exactly two whole-film gain-staging
scalars**, and `master_report.json` states both:

1. **One bus trim moved.** Thirteen of the fourteen buses are identical to
   1e-9 dB. The fourteenth is `crowd`: A -8.6427 dB, B -8.8000 dB, delta
   -0.1573 dB. `master.py` sets each trim from the bus's PEAK 3-SECOND
   short-term loudness, and in B the car crosses the line 50 m from the second
   grandstand (excitement 0.915) and then decelerates beside it instead of
   vanishing at 323 km/h, so the crowd bus's loudest three seconds now lie IN
   the ending. The bus is therefore 0.157 dB quieter across all 2,978 frames.
2. **One master gain moved.** The -14 LUFS normalisation lands on a slightly
   different integrated loudness: A -14.033, B -14.019 LUFS, a +0.0255 dB
   best-fit difference over frames 1-2714.

0.157 dB on a bus targeted at -27 LUFS, plus 0.026 dB overall. Both are MIX
decisions that `TARGET_LUFS_S` exists to make, both are reported, and neither is
a rebuilt beat. **The claim that CAN be made exactly is made exactly, at the
source**, by `tools/audio_prefix_identity.py`: every world-clock track — speed,
accel_long, accel_lat, slip, wheel_w, heading, s_m, track_s, pos, rpm, gear, the
dry engine and the dry tyre bed — is bit-identical, `==`, for all 72.583 s of
world time before the lift.

FOR THE RECORD, because R2-951 makes the shipped file a red herring: the same
comparison of the SHIPPED 2026-08-02 master against a fresh A-side of this tree
gives worst |delta| 1.378 and a -2.83 dB best-fit gain, first differing frame 1.
It is a different film. Comparing against it would have measured R2-731..760's
camera move, not the ending.

---

## R2-962 — what the ending actually does, measured at the ear

Not the synthesiser's intent — the finished 48 kHz master, A against B.

**1. The tone stops.** The firing fundamental that has run for the whole flying
lap sits at ~550 Hz at the line (12,876 rpm in 8th, times a 0.861 recession
Doppler). In the control it runs unbroken to the last frame, drifting slowly
down: a held tone that only gets quieter. In B it **terminates at film t 113.6**,
half a second after the lift, and does not come back for six seconds. On the
brakes the throttle is shut, `fuel = clip(thr/0.06)` goes to zero and the
injectors cut, so there is no combustion and no firing tone — only pumping,
unburnt-charge pops and compressor surge, which are broadband. Measured across
frames 2715-2800: the 300-700 Hz band is **-2.37 dB** against the control while
every other band is within 0.6 dB. Visible in
`audio/out/ab/brake/ending_spectrograms.png` as the 550 Hz line simply ending.

Stopping a tone that has been running for seventy seconds is the loudest thing
that can happen to it. That is the deceleration, and it is the largest single
change in the closing beat.

**2. Seven downshifts.** `engine.synth` reports 24 downshifts in the control and
**31** in the lap-down: 8th -> 1st at world t 72.941, 73.390, 73.872, 74.373,
74.879, 75.373, 75.843, a 0.48 s cadence. Gear is chosen by the same rule as the
whole film (the lowest gear under the 14,400 rpm shift point), so this is the
gearbox solving the new speed track and not an ending-shaped special case.

**3. The idle comes back, and it is a real line.** Below 8.55 m/s the clutch
opens (R2-954), the throttle floors at idle and the injectors relight. Measured
on the last 1.75 s (frames 2937-2978), B minus A, 4 Hz smoothing:

        216.0 Hz   +9.06 dB      <- RPM_IDLE/60*3 = 215.0 Hz, the firing fundamental
        430   Hz   +2.95 dB         2nd harmonic
        645   Hz   +1.94 dB         3rd
        860   Hz   +3.07 dB         4th
        mean over 150-400 Hz  -0.62 dB   (i.e. the lift is a LINE, not a level change)

**4. The Doppler goes to zero, and it is not faded to zero — it arrives there.**
From the retarded-time solve on the shipped geometry, the received/emitted ratio
runs 0.861 at the line (the car receding from a climbing camera, 2.6 semitones
down) and reaches **|ratio - 1| < 4.2e-05 over the last 1.75 s** — 0.0007 of a
semitone. The 216.0 Hz line is measured at 216.0 Hz because both the car and the
camera have stopped, not because anything was switched off.

---

## R2-963 — the brake is acknowledged through the powertrain, and no brake layer was added

DECISION, with the reasons in the order they actually weighed.

**It is not a limit stop.** `carpath.py`'s own header says so: peak 3.60 g, and
"an F1 car can do 5-6 g there, so this is a firm lap-down brake and not a limit
stop". The lap the film has already shown pulls **4.89 g laterally** — more than
this brake pulls longitudinally. A sub-limit brake on slicks does not lock, does
not slide and does not squeal, so there is no stick-slip event to render. The
existing lateral scrub layer, which triggers above 1.6 g, is the model's own
statement of where tyre noise starts being a discrete sound, and a straight-line
brake at 3.60 g does not produce one.

**A brake-disc layer would have been an invented number.** Everything in
`audio/` derives its level from something the project already declares: pipe
lengths, plate moduli, a vehicle model, an ISO 9613-1 curve. There is no
acoustic source term for carbon brakes anywhere in `circuit_spec.json`, so a disc
layer's level would have been chosen by me and then defended by ear. That is the
one thing this package has never done.

**And the geometry says it would not have survived the mix.** Through the heavy
braking the car is 96-241 m away and the camera is inside its own 40-60 m/s
airstream, with `wind` the second-loudest bus in the film at -18 LUFS. Measured
frame by frame over 2715-2800, the level difference between "braking" and "flat
out" is already under 0.5 dB in five of six octave bands. A synthesized disc
would have gone under a wind bed.

**WHAT WAS RULED OUT BY THE BRIEF, stated so it is not mistaken for a
preference.** A longitudinal tyre-slip layer is the one addition that could be
derived honestly, as the twin of the existing lateral `scrub`. It cannot be added
in this block: the telemetry's own braking zones reach **-36.76 m/s^2 = -3.75 g**,
which is HARDER than the lap-down's 3.60 g, so any threshold low enough to fire
on the ending fires on the lap and changes the film before f2714. It is left for
a block that is allowed to re-render beats 1-5.

---

## R2-964 — the last 1.75 s: a distant idle under open air, not silence and not a tail

The car is stationary from f2936. The camera is stationary too, 140 m up and
**342.9 m** away, `insideness` = 0.000. What is left:

    total programme, frames 2937-2978      -27.66 dBFS RMS
    silent 1 s windows below -80 dBFS      0        (level_gate requires 0)
    B minus A, 120-300 Hz                  +0.94 dB
    B minus A, every other octave          +0.05 .. +0.10 dB

So the last 1.75 s is the open-air bed and the distant grandstand babble, with an
idling V6 just showing through them as a 216.0 Hz line 9 dB over the bed. That is
what 342.9 m of air does to an idling engine, and the mix says so rather than
deciding it.

REJECTED: **silence.** A stopped F1 car is not silent, and 1.75 s of digital
silence at the end of a 124 s film reads as a dropout, not as an ending —
`level_gate` would fail it outright.

REJECTED: **a reverb tail.** There is no room. The showroom is 490 m behind the
car, the camera is 140 m up in the open, and `layers.insideness` returns 0.000 at
f2978. A tail would have been the one thing in this package invented for effect.

KEPT, and it was not designed — it fell out of the geometry: the car crosses the
line **50 m** from the second grandstand, whose excitement peaks at 0.915 and
then decays over the 0.8 s crowd lag as the car brakes away from it. The film's
last audible gesture other than the idle is a grandstand subsiding.

---

## R2-965 — gates, and what shipped

`.venv/bin/python -m audio.verify --wav audio/out/master.wav`

| gate | result |
|---|---|
| levels | PASS — -14.02 LUFS, -1.10 dBTP, 0 clipped, **0 silent 1 s windows**, short-term range 20.39 dB |
| seam | PASS — worst d3 local percentile **80.57** (threshold 99.9); the beat-6 boundary at f2715 is **76.10**, down from 87.70 in the shipped master, which is R2-953's continuous `accel_long` showing up on the one gate that looks at that frame |
| seam controls | both the 977-sample splice and the 3 dB step correctly FAIL |
| external_assets | PASS — 0 render-path hits, 0 package hits |
| pitch | PASS — corr 0.99754, 98.64 % within 50 cents |
| doppler | PASS — null control 2.5e-10 semitones |
| ffmpeg ebur128 (independent) | -14.0 LUFS, -1.1 dBTP true peak |

Shipped: `audio/out/master.wav` (= `audio/out/ab/master_B_lapdown.wav`),
`audio/out/master_report.json`, `audio/out/verify_report.json`.

**ONE DEFECT FOUND AND NOT FIXED, because fixing it changes beats 1-5.**
`engine.synth`'s downshift is documented as "a throttle blip that pulls the revs
UP to match the lower gear", and the implementation adds 900 rpm to `rpm_eff` but
never opens `thr`. So `fuel` stays at zero through the blip and the revs rise
with the injectors still cut: a rev-match with no combustion behind it. It
affects all 31 downshifts, 24 of which are before f2714. Left for the next block,
with the ending's seven as the reason it is worth doing.

---
