# CIRCUIT D — "VITRINE"
## A circuit designed backwards from the camera move

**Design philosophy: CAMERA-FIRST.** The beat sheet's six camera moves were laid down first,
as positions and velocities in space. Tarmac was then poured wherever those moves needed
something to look at, and only afterwards was the result audited as a racing circuit. Every
corner below has a stated camera job. Section 12 shows the racing-plausibility work, and
section 13 is honest about where the philosophy cost me.

Everything numeric here was **computed**, not asserted. The closure solve, the elevation
spline, the speed profile, the lap time, the sight-line optics and the pixel budgets all
come from the solver scripts listed in section 14. Where a number is a design choice rather
than a solve, it says so.

---

## 1. HEADLINE NUMBERS

| | value |
|---|---:|
| **Total length** | **3 675.0 m** |
| **Corners** | **15** (T1–T15) |
| **Predicted lap (centreline)** | **62.54 s** |
| average lap speed | 211.5 km/h |
| **Top speed** | **331.8 km/h** (pit straight, x = +182) |
| speed crossing S/F, flying lap | 323.4 km/h |
| speed crossing S/F, out lap | 294.3 km/h |
| **Hairpin (T4) apex** | **79.6 km/h** |
| **Elevation range** | **11.00 m** (−2.50 m at T4 braking → +8.50 m at T8) |
| max / min gradient | +3.97 % / −1.22 % |
| plan bounding box | 1 292 × 683 m |
| min separation between non-adjacent centrelines | 59.0 m |
| sector times | 17.60 / 24.66 / 20.27 s |
| direction | **counter-clockwise** (net +360° of left turn) |
| datum | +X east, +Y north, +Z up. S/F line at the world origin (0, 0, 0). |

Closure is exact: integrating the element list from (0, 0, heading 0°) lands the end of T15
at (−560.0000, −0.0000) on heading 360.0000°, and the 560 m pit straight closes the loop.

---

## 2. THE SIX CAMERA MOVES, AND THE CORNER THAT EXISTS TO SERVE EACH

This is the design. Read this table and the rest of the document is bookkeeping.

| # | camera move (from the beat sheet) | geometry built to serve it | why nothing else works |
|---|---|---|---|
| 1 | **Swoop chase**, camera behind → outboard | **T1 + T2**, a linked left-left of 62° + 30°, R100/R110, taken at 197 / 218 km/h, falling 1.1 m | A single 90° corner would rotate the car through the camera's frame too fast to hold. Two linked lefts give **166 m of continuous arc** at constant-ish yaw rate, so the chase can slide from dead astern to outboard-alongside without the car ever changing apparent direction. The 1.1 m drop lets the camera *dive* as it slides. |
| 2 | **Low kerb-height pass at the hairpin** | **T4 "The Pin"** — R28, **176°**, apex 79.6 km/h, 86.0 m of arc, **3.9 s** below 85 km/h, sitting at the circuit's low point (−2.30 m) | 176° is the point. A camera parked on the inside kerb at **0.85 m** watches the car yaw through 176° in front of it — front three-quarter → profile → rear three-quarter → profile → front three-quarter. No other corner geometry delivers a full profile-to-profile reveal from a *static* camera. And 80 km/h is slow enough for a 21 mm lens 4 m from the tyre wall to stay legible at 180° shutter. |
| 3 | **Helicopter arc through the esses** | **T6–T9**, four alternating corners (L38 / R44 / L46 / R30) over **358 m**, taken 155–186 km/h in **7.0 s**, on the summit at z = +7.85 … +8.50 | The arc needs (a) time — 7.0 s — (b) a subject that keeps changing direction under it so the arc reads as *orbit* not *drift*, and (c) **altitude to orbit above**. T8 is the highest ground on the circuit; a camera arcing to 70 m above T8 is 78.5 m above the pit straight and can see the showroom, the finish gantry and the hairpin in one frame. |
| 4 | **Near-static trackside doppler pass, ≥ 3 s** | **S11 "doppler straight"** — 306.4 m, **descending −0.9 %**, car peaking at **293.5 km/h** 26 m from the camera, then braking to 114 km/h inside the next 100 m | The pass needs the car flat-out *and* a long clean sight-line both ways. S11 exists only for this: the car is within ±200 m of the hover station for **6.87 s**, so a ≥ 3 s near-hover is comfortable. It descends so the hovering camera looks slightly *down* the barrel of the approach. The braking zone immediately after puts glowing discs and a squatting rear axle in the departing frame. |
| 5 | **Whip after it, then catch it** | **T12 (R50, 114 km/h) + T13 + T14 + T15** | The camera must physically re-acquire a car it just let go. T12 dumps the car from 300 → 114 km/h in 101 m, and the T12–T15 complex makes the car travel **415 m in 8.8 s** while the camera flies a **279 m chord** — a mean of **38 m/s (137 km/h)**. The catch-up is won by cutting the corner, which is honest physics, not a cheat. |
| 6 | **Tight onboard-like follow at ~330 km/h, then the closing wide** | **810 m pit straight** (T15 exit x = −560 → T1 turn-in x = +250), **S/F line at x = 0**, showroom breach face at (−350, +72) | The straight gives **559 m / 7.1 s** from T15 exit to the line, 207 → 323 km/h — long enough for the onboard follow to build, short enough that it does not become a hold. And the line sits at x = 0 **because that is the only station from which a camera that peeled off the car 3 s earlier can reach (−40, −150, 55) and hold the line-crossing and the breached glass wall in one 21 mm frame.** See section 10. |

Two more elements exist purely as camera plumbing:

- **S4 + T5 (the ramp)** — 175 m at **+3.97 %** out of the hairpin, then an 88° right. This is
  the only real gradient on the circuit and it exists so the camera's rise into the
  helicopter arc is *motivated by terrain*: the camera climbs because the car climbs.
- **S9 (crest run)** — 224.9 m flat-out at 8.0 m elevation. The camera's diving runway: it
  falls off the summit alongside a car doing 300 km/h into the sweeper.

---

## 3. PLAN VIEW

```
   +Y north                                                     1 col ≈ 15 m · 1 row ≈ 22 m
      ^                    T10                                        (aspect ≈ true)
      |                #########                                                       T4
      |            ####        #####                                                 ###  ◄ HAIRPIN
      |         ####               ######           T8                              ## ##
 T11 ─┼──►    ##                       #####T9########                             ##   #
      |      ##                            ###      ### T7    T6                   #   ##
      |      #                                       ############                 ##  ##
      |     ##                                                ####               ##   #
      |     #                                                    ####           ##   ##
      |    ##                                                       ####       ##   ##
      |    #                                                          #########    #
      |    #                                                            ## T5      #
 [D] ─┼─  ##                                                                       #  T3
      |   #                                                                        #
      |   #                                                                        #
      |  ##                                                                        #
 T12 ─┼─ #                                                                         #
      |  ###                                                                       #
      |    ##                                                                      #
 T13 ─┼──  ####                                                                    #
      |       ###                                                                  #
 T14 ─┼───     ##          ┌────────┐                                              #   T2
      |         ###        │SHOWROOM│                                             ##
      |           ##       └──G─────┘                                            ##
      |            ##          ╲:::                                             ##
      |             ###          :::  ~~~~~~ pit lane ~~~~~~~~~~~~~~~          ## T1
      |               ####       ::: ~~~~~~~ pit garages ~~~~~~~~~~            ###
      |                  ##########################|##############################
      |                 T15                       S/F
      +──────────────────────────────────────────────────────────────────────────►  +X east

   #   racing surface (centreline)          G   breached glass wall (22.0 m, faces −40° az)
   :   breach exit route / access road      [D] doppler hover station (s = 2555)
   ~   pit lane, pit wall, garage row       |   start / finish line + gantry, x = 0
```

Reading the lap from the S/F line: east along the pit straight → **T1/T2** turn north →
**S2** north up the east chute → **T3** fast right kink → **T4 THE PIN** (the hairpin,
top-right of plan, reversing the car onto a WSW ramp) → **T5** hooks it onto the WNW climb →
**T6–T9 esses** across the summit → **S9 crest run** → **T10/T11 double-apex sweeper**
(top-left) → **S11 doppler straight**, descending SSW down the west side → **T12** heavy
braking at the bottom-left → **T13/T14/T15** hook east → back onto the pit straight.

---

## 4. CORNER TABLE

Speeds are km/h from the solved speed profile (section 8). "Brake@" is the peak speed in the
240 m before turn-in — i.e. the speed at which the driver hits the brakes; for corners inside
a linked complex it is the previous corner's exit and is marked *. `z` is the centreline
elevation at the apex. `t` is the lap time at the apex on a flying lap.

| # | name | type | dir | R (m) | arc° | arc (m) | brake@ | turn-in | **apex** | exit | lat g | banking | apex (x, y, z) | t (s) |
|---|---|---|:-:|---:|---:|---:|---:|---:|---:|---:|---:|:-:|---|---:|
| **T1** | Vitrine | fast left | L | 100 | +62.0 | 108.2 | **331.8** | 197.7 | **197.2** | 197.2 | 3.1 | 2° positive | (+301.6, +14.3, −0.40) | 3.93 |
| **T2** | Threshold | linked left | L | 110 | +30.0 | 57.6 | 197.2* | 218.5 | **218.0** | 218.0 | 3.4 | 2° positive | (+367.1, +115.3, −1.10) | 6.07 |
| **T3** | Long Kink | fast right kink | R | 140 | −28.0 | 68.4 | 296.7 | 295.6 | **295.1** | 295.1 | 4.9 | 3° positive | (+363.6, +443.8, −2.05) | 10.60 |
| **T4** | **THE PIN** | **HAIRPIN** | L | **28** | **+176.0** | 86.0 | **301.9** | 80.3 | **79.6** | 79.6 | 1.8 | flat | (+428.4, +647.9, −2.30) | 15.66 |
| **T5** | Ramp | medium right, uphill | R | 75 | −88.0 | 115.2 | 226.9 | 153.3 | **152.7** | 152.7 | 2.4 | 1° positive | (+259.1, +451.0, +3.85) | 22.79 |
| **T6** | Weave 1 | esse, left | L | 88 | +38.0 | 58.4 | 262.8 | 175.3 | **174.8** | 174.8 | 2.7 | flat | (−27.4, +574.1, +7.85) | 28.58 |
| **T7** | Weave 2 | esse, right | R | 82 | −44.0 | 63.0 | 174.8* | 164.9 | **164.4** | 164.4 | 2.6 | flat | (−129.0, +567.1, +8.30) | 30.68 |
| **T8** | Crest | esse, left — **summit** | L | 76 | +46.0 | 61.0 | 164.4* | 154.9 | **154.4** | 154.4 | 2.5 | 1° negative | (−218.9, +613.3, **+8.50**) | 32.91 |
| **T9** | Weave 4 | esse, right | R | 94 | −30.0 | 49.2 | 197.8 | 186.2 | **185.7** | 185.7 | 2.9 | flat | (−317.8, +601.7, +8.10) | 35.02 |
| **T10** | Panorama 1 | **double-apex sweeper A** | L | 150 | +44.0 | 115.2 | 281.6 | 281.6 | **281.6** | 301.6 | 4.2 | 4° positive | (−612.7, +682.7, +5.70) | 39.57 |
| — | *(release)* | easing arc, not a corner | L | 420 | +8.0 | 58.6 | — | — | *305.9 peak* | — | 1.7 | 4° positive | — | 40.3 |
| **T11** | Panorama 2 | **double-apex sweeper B** | L | 125 | +41.4 | 90.3 | 305.9 | 255.1 | **254.6** | 254.6 | 4.1 | 4° positive | (−750.8, +607.1, +3.85) | 41.63 |
| **T12** | Doppler | heavy-braking left | L | 50 | +52.0 | 45.4 | **301.7** | 114.5 | **113.8** | 113.8 | 2.0 | flat | (−847.6, +247.4, +0.80) | 47.41 |
| **T13** | Hook | slow left | L | 70 | +22.0 | 26.9 | 113.8* | 145.2 | **144.7** | 144.7 | 2.4 | flat | (−795.7, +173.4, +0.55) | 49.83 |
| **T14** | Flick | right kink | R | 90 | −19.4 | 30.5 | 245.1* | 178.9 | **178.4** | 178.4 | 2.8 | flat | (−712.2, +121.1, +0.30) | 51.89 |
| **T15** | Gate | fast final left | L | 105 | +50.0 | 91.6 | 233.7 | 207.8 | **207.3** | 207.3 | 3.2 | 3° positive | (−604.3, +9.8, +0.05) | 54.63 |

Net turn: +62 +30 −28 +176 −88 +38 −44 +46 −30 +44 +8 +41.4 +52 +22 −19.4 +50 = **+360.0°** exactly.
Left-handers: 10. Right-handers: 5. Longest single arc: T5 at 115.2 m. Shortest: T13 at 26.9 m.

**Banking** is a design choice, not a solve. Positive (toward the corner centre) banking is
applied only where the corner is fast enough for it to matter: 4° through the T10/T11 sweeper
so a 282 km/h apex does not look like it is riding on the edge, 3° at T3 and T15, 2° at T1/T2.
T8 gets **1° of negative (off-camber) banking** at the summit crest — the single meanest thing
on the circuit and the reason the car looks light there under the helicopter arc.

---

## 5. ELEVATION PROFILE

Total relief **11.00 m**, inside the brief's 8–12 m window. The profile is a monotone-cubic
(Fritsch–Carlson PCHIP) interpolation through these keyframes, evaluated at 0.25 m stations —
monotone so the road never overshoots into a phantom hump between control points.

| station s (m) | z (m) | where | note |
|---:|---:|---|---|
| 0.0 | 0.00 | S/F line | datum |
| 304.1 | −0.40 | T1 apex | |
| 427.0 | −1.10 | T2 apex | |
| 756.1 | −2.05 | T3 apex | |
| **915.4** | **−2.50** | T4 braking board | **LOW POINT** — braking downhill into the hairpin |
| 983.4 | −2.30 | T4 apex | |
| 1026.4 | −2.15 | T4 exit | |
| 1105.2 | +0.30 | hairpin exit ramp | **+3.97 % max gradient** |
| 1201.4 | +2.70 | T5 entry | |
| 1259.0 | +3.85 | T5 apex | |
| 1316.6 | +4.65 | T5 exit | |
| 1546.6 | +7.60 | T6 entry | end of the climb straight |
| 1575.7 | +7.85 | T6 apex | |
| 1678.4 | +8.30 | T7 apex | |
| **1780.4** | **+8.50** | **T8 apex** | **SUMMIT** |
| 1880.5 | +8.10 | T9 apex | |
| 2187.7 | +5.70 | T10 apex | |
| 2349.1 | +3.85 | T11 apex | |
| 2630.6 | +1.05 | doppler straight | |
| 2723.3 | +0.80 | T12 apex | |
| 2814.5 | +0.55 | T13 apex | |
| 2913.1 | +0.30 | T14 apex | |
| 3069.2 | +0.05 | T15 apex | |
| 3675.0 | 0.00 | S/F line | closes on the datum |

The gradient never exceeds **+3.97 %** (hairpin exit ramp) or **−1.22 %** (crest run into the
sweeper). The pit straight is effectively flat (−0.29 m over its 810 m, a 0.04 % fall to the
east) which matters: a flat straight keeps the Beat-6 sight-line from the closing camera to
the showroom clean, and keeps the finish gantry from cutting the horizon.

---

## 6. CENTRELINE GEOMETRY — ELEMENT LIST (authoritative)

This is the generative definition. Feed it to a turtle integrator starting at
`(0, 0, 0)` heading `0°` (+X, east) and it reproduces the circuit exactly. `+ang` = left/CCW.

| element | type | R (m) | ang (°) | length (m) | s start | s end | start (x, y) | heading in |
|---|:-:|---:|---:|---:|---:|---:|---|---:|
| S0 pit straight, S/F → T1 | S | ∞ | — | 250.0 | 0.0 | 250.0 | (0.0, 0.0) | 0.0 |
| **T1** | A | 100 | +62.0 | 108.2 | 250.0 | 358.2 | (250.0, 0.0) | 0.0 |
| S1 T1–T2 link | S | ∞ | — | 40.0 | 358.2 | 398.2 | (338.3, 53.1) | 62.0 |
| **T2** | A | 110 | +30.0 | 57.6 | 398.2 | 455.8 | (357.1, 88.4) | 62.0 |
| S2 east chute | S | ∞ | — | **266.1** | 455.8 | 721.9 | (369.9, 143.9) | 92.0 |
| **T3** | A | 140 | −28.0 | 68.4 | 721.9 | 790.4 | (360.6, 409.8) | 92.0 |
| S3 hairpin approach | S | ∞ | — | 150.0 | 790.4 | 940.4 | (374.7, 476.1) | 64.0 |
| **T4 HAIRPIN** | A | 28 | +176.0 | 86.0 | 940.4 | 1026.4 | (440.4, 610.9) | 64.0 |
| S4 hairpin exit ramp | S | ∞ | — | 175.0 | 1026.4 | 1201.4 | (391.0, 637.2) | 240.0 |
| **T5** | A | 75 | −88.0 | 115.2 | 1201.4 | 1316.6 | (303.5, 485.6) | 240.0 |
| S5 climb straight | S | ∞ | — | 230.0 | 1316.6 | 1546.6 | (203.4, 456.9) | 152.0 |
| **T6** | A | 88 | +38.0 | 58.4 | 1546.6 | 1604.9 | (0.3, 565.0) | 152.0 |
| S6 esse link a | S | ∞ | — | 42.0 | 1604.9 | 1646.9 | (−56.3, 573.8) | 190.0 |
| **T7** | A | 82 | −44.0 | 63.0 | 1646.9 | 1709.9 | (−97.7, 566.5) | 190.0 |
| S7 esse link b | S | ∞ | — | 40.0 | 1709.9 | 1749.9 | (−158.0, 579.5) | 146.0 |
| **T8** | A | 76 | +46.0 | 61.0 | 1749.9 | 1810.9 | (−190.9, 601.7) | 146.0 |
| S8 esse link c | S | ∞ | — | 45.0 | 1810.9 | 1855.9 | (−249.2, 613.0) | 192.0 |
| **T9** | A | 94 | −30.0 | 49.2 | 1855.9 | 1905.1 | (−293.2, 603.7) | 192.0 |
| S9 crest run | S | ∞ | — | **224.9** | 1905.1 | 2130.1 | (−341.8, 606.2) | 162.0 |
| **T10** | A | 150 | +44.0 | 115.2 | 2130.1 | 2245.3 | (−555.8, 675.7) | 162.0 |
| T10b release | A | 420 | +8.0 | 58.6 | 2245.3 | 2303.9 | (−667.9, 667.9) | 206.0 |
| **T11** | A | 125 | +41.4 | 90.3 | 2303.9 | 2394.2 | (−718.6, 638.6) | 214.0 |
| S11 doppler straight | S | ∞ | — | **306.4** | 2394.2 | 2700.6 | (−769.7, 566.5) | 255.4 |
| **T12** | A | 50 | +52.0 | 45.4 | 2700.6 | 2746.0 | (−846.9, 269.9) | 255.4 |
| S12 T12–T13 link | S | ∞ | — | 55.0 | 2746.0 | 2801.0 | (−838.3, 227.0) | 307.4 |
| **T13** | A | 70 | +22.0 | 26.9 | 2801.0 | 2827.9 | (−804.9, 183.3) | 307.4 |
| S13 T13–T14 link | S | ∞ | — | 70.0 | 2827.9 | 2897.9 | (−784.9, 165.5) | 329.4 |
| **T14** | A | 90 | −19.4 | 30.5 | 2897.9 | 2928.4 | (−724.6, 129.9) | 329.4 |
| S14 T14–T15 link | S | ∞ | — | 95.0 | 2928.4 | 3023.4 | (−701.5, 110.3) | 310.0 |
| **T15** | A | 105 | +50.0 | 91.6 | 3023.4 | 3115.0 | (−640.4, 37.5) | 310.0 |
| S15 pit straight, T15 → S/F | S | ∞ | — | **560.0** | 3115.0 | 3675.0 | (−560.0, 0.0) | 360.0 |

Bold lengths are the three straights the closure solver was allowed to move (S2, S9, S11);
everything else is a design value held fixed. Three free lengths against three constraints
(end-x, end-y, total length) is a square system, so the solution is unique — there is no
hidden slack in this layout.

**Transitions.** The element list is straights and constant-radius arcs because that is the
language the geometry is *designed* in. When built, insert **clothoid transitions** at every
straight↔arc junction: A = √(R · L_c) with L_c = 0.55 · R for R ≤ 100 and 0.40 · R above,
absorbed by shortening the constant-radius portion so total length and closure are unchanged
to within 0.3 m. Without them the steering trace has a step at every turn-in and the chassis
roll animation will snap.

---

## 7. CENTRELINE CONTROL POINTS (x, y, z in metres)

148 points, ready for a Blender `POLY`/`NURBS` curve. Spacing is adaptive: ≤ 40 m on
straights, ≤ 12° of arc on corners (5.7 m minimum, inside the hairpin). Point 0 is the S/F
line; point 147 closes on it. Set the curve to **cyclic** and drop the duplicate last point,
or leave it and set the spline to non-cyclic for an open lap curve.

```
  0      0.00      0.00   0.00     50    321.02    515.93   1.89    100   -750.81    607.08   3.85
  1     35.75      0.00  -0.04     51    303.52    485.61   2.70    101   -762.09    587.62   3.60
  2     71.50      0.00  -0.08     52    295.11    473.84   3.02    102   -769.69    566.46   3.34
  3    107.25      0.00  -0.12     53    284.59    463.90   3.32    103   -779.39    529.21   2.88
  4    143.00      0.00  -0.15     54    272.59    456.27   3.60    104   -789.03    492.21   2.43
  5    178.75      0.00  -0.19     55    259.12    450.99   3.85    105   -798.67    455.20   2.00
  6    214.50      0.00  -0.24     56    244.89    448.38   4.07    106   -808.37    417.95   1.61
  7    250.00      0.00  -0.29     57    230.67    448.53   4.27    107   -818.01    380.95   1.30
  8    268.14      1.66  -0.32     58    216.49    451.44   4.46    108   -827.65    343.94   1.08
  9    285.45      6.49  -0.36     59    203.36    456.89   4.65    109   -837.29    306.94   0.95
 10    301.61     14.35  -0.40     60    169.36    474.97   5.18    110   -846.93    269.93   0.86
 11    316.11     24.97  -0.46     61    135.59    492.93   5.71    111   -848.42    260.84   0.83
 12    328.47     38.01  -0.56     62    101.82    510.88   6.23    112   -848.25    251.88   0.81
 13    338.29     53.05  -0.67     63     67.82    528.96   6.73    113   -846.40    242.85   0.79
 14    357.07     88.37  -0.95     64     34.05    546.91   7.19    114   -843.05    234.54   0.76
 15    364.59    106.10  -1.06     65      0.28    564.87   7.60    115   -838.26    226.96   0.74
 16    368.90    124.87  -1.14     66    -13.29    570.68   7.74    116   -821.56    205.11   0.66
 17    369.88    143.85  -1.21     67    -27.39    574.11   7.85    117   -804.86    183.27   0.59
 18    368.55    182.06  -1.34     68    -41.87    575.17   7.94    118   -798.80    176.34   0.56
 19    367.22    220.02  -1.46     69    -56.32    573.84   8.01    119   -792.08    170.42   0.54
 20    365.90    257.98  -1.57     70    -77.00    570.19   8.11    120   -784.88    165.53   0.51
 21    364.57    295.94  -1.67     71    -97.68    566.54   8.20    121   -754.76    147.71   0.42
 22    363.25    333.90  -1.76     72   -113.60    565.31   8.25    122   -724.63    129.90   0.33
 23    361.92    371.86  -1.86     73   -129.21    567.14   8.30    123   -716.13    124.19   0.31
 24    360.59    409.82  -1.96     74   -144.19    571.91   8.34    124   -708.33    117.56   0.29
 25    361.68    432.74  -2.02     75   -157.77    579.32   8.39    125   -701.50    110.28   0.27
 26    366.41    454.94  -2.08     76   -190.93    601.68   8.47    126   -681.09     85.96   0.20
 27    374.68    476.08  -2.16     77   -204.35    608.89   8.49    127   -660.68     61.64   0.14
 28    391.12    509.78  -2.30     78   -218.93    613.28   8.50    128   -640.43     37.51   0.09
 29    407.56    543.48  -2.43     79   -234.09    614.67   8.48    129   -627.38     24.47   0.07
 30    423.99    577.19  -2.49     80   -249.23    613.02   8.44    130   -612.46     14.04   0.05
 31    440.43    610.89  -2.46     81   -271.24    608.34   8.35    131   -595.72      6.26   0.05
 32    442.41    616.28  -2.44     82   -293.25    603.66   8.23    132   -578.13      1.58   0.05
 33    443.24    621.96  -2.42     83   -309.60    601.66   8.14    133   -560.00      0.00   0.04
 34    442.90    627.69  -2.40     84   -326.04    602.54   8.06    134   -520.00      0.00   0.04
 35    441.40    633.23  -2.37     85   -341.84    606.21   7.97    135   -480.00      0.00   0.03
 36    438.79    638.35  -2.35     86   -377.73    617.87   7.74    136   -440.00      0.00   0.03
 37    435.20    642.83  -2.33     87   -413.39    629.45   7.48    137   -400.00      0.00   0.02
 38    430.77    646.48  -2.31     88   -449.04    641.04   7.20    138   -360.00      0.00   0.02
 39    425.69    649.16  -2.29     89   -484.70    652.62   6.90    139   -320.00      0.00   0.02
 40    420.17    650.74  -2.27     90   -520.35    664.21   6.57    140   -280.00      0.00   0.02
 41    414.45    651.16  -2.26     91   -555.77    675.72   6.24    141   -240.00      0.00   0.01
 42    408.76    650.40  -2.24     92   -584.03    681.96   5.97    142   -200.00      0.00   0.01
 43    403.34    648.50  -2.22     93   -612.71    682.68   5.70    143   -160.00      0.00   0.01
 44    398.43    645.54  -2.20     94   -641.01    677.93   5.40    144   -120.00      0.00   0.01
 45    394.22    641.63  -2.18     95   -667.88    667.88   5.08    145    -80.00      0.00   0.01
 46    391.02    637.17  -2.15     96   -685.39    658.82   4.84    146    -40.00      0.00   0.00
 47    373.52    606.86  -1.31     97   -702.24    649.09   4.60    147      0.00      0.00   0.00
 48    356.02    576.55   0.03     98   -718.62    638.58   4.37
 49    338.52    546.24   1.01     99   -736.24    624.20   4.10
```

Index map (verified against the element stations): **7–14** are T1, **31–46** are the hairpin
(note the 5.7 m spacing through 176° of arc), **65–85** are the esses T6–T9, **91–102** the
T10/T10b/T11 sweeper, **133–147** the pit straight running into the S/F line.

---

## 8. LENGTH AND LAP TIME — HOW THE 62.54 s WAS DERIVED

The lap time was **not** chosen and the length **not** guessed. Length was constrained to
3 675 m in the closure solve, then the lap time fell out of a physics model. If the model had
returned 70 s I would have shortened the circuit; it returned 62.54 s, inside the 55–65 s
window, so the length stands.

**Lateral limit** (downforce-dependent grip circle):
`a_lat(v) = min(15.0 + 0.0050·v², 48.0)` m/s²
→ 1.8 g at 80 km/h, 3.1 g at 200 km/h, 4.9 g at 300 km/h, capped at 4.9 g.
Corner speed solves `v² = a_lat(v)·R`. Sanity check against reality: this gives R = 137 m for
a 292 km/h apex, which is Copse-at-Silverstone territory (R ≈ 150 m, ≈ 290 km/h). Good.

**Longitudinal accel** (power + traction − drag), m = 830 kg:
`a(v) = min(16.0, 800/v) − 0.00092·v²` m/s²
→ 1.6 g traction-limited up to the 50 m/s power crossover, terminal velocity 344 km/h (a
DRS-open trim). 681 kW at the wheels. The model gives **0–100 km/h in 2.05 s and 0–200 km/h
in 4.02 s**, which is ~10 % optimistic against a real car (≈ 2.6 s / 4.5 s) because it has no
launch-traction or gear-step penalty. That bias makes the predicted lap ~1 % fast; see
weakness #10.

**Braking**: `a_brake(v) = min(17.0 + 0.0045·v², 55.0)` m/s²
→ 2.1 g at 100 km/h, 5.6 g at 330 km/h. The solved braking zones:

| zone | from | to | distance | time | mean decel |
|---|---:|---:|---:|---:|---:|
| into T1 | 331 km/h | 198 km/h | 100 m | 1.29 s | 2.8 g |
| **into T4 (the hairpin)** | 265 km/h | 80 km/h | **85 m** | 1.91 s | 2.9 g |
| into T12 | 300 km/h | 114 km/h | 101 m | 1.79 s | 3.0 g |

**Solve**: forward pass (traction-limited) and backward pass (brake-limited) over the 0.25 m
station grid, clamped to the cornering cap, with the road gradient added as `−g·dz/ds`,
iterated to convergence (8 passes), then `t = Σ ds/v`.

**Result: 62.54 s, average 211.5 km/h.** Sectors 17.60 / 24.66 / 20.27 s.

Reasonableness cross-check: Red Bull Ring is 4 318 m in ~64 s (243 km/h average) with a lot
more full-throttle; Monaco is 3 337 m in ~71 s (169 km/h). A 3 675 m circuit with one 810 m
straight, one true hairpin and four low-speed corners landing at 211 km/h average sits
sensibly between them.

**This is a centreline time.** A real racing line — cutting apexes, straightening the esses,
carrying a wider radius through T10/T11 — is worth roughly 1.5–2.5 % on a layout of this
character, so a driven lap would be **≈ 61.0–61.6 s**. The camera and telemetry should use the
centreline number and add the racing-line offset explicitly, not silently.

**Screen-time budget for the whole film:**

| beat | world time | note |
|---|---:|---|
| 1 assembly | 33.0 s | |
| 2 ignition + launch | 6.0 s | |
| 3 breach | 8.0 s screen | ~2.0 s of world time at 15–25 % |
| 4 transit | 6.5 s | see weakness #6 |
| 5 the lap | 62.5 s | + 1.8 s if the T10/T11 ramp is taken |
| 6 ending | 10.0 s | 7.0 s move + 3.0 s hold |
| **total** | **126.0 – 127.8 s** | inside the 100–130 s deliverable |

---

## 9. TRACK SECTION, KERBS AND SCALE AGAINST THE CAR

The car is **5.698 m long, 2.005 m wide, 0.340 m ride height** (measured, `round2_inventory.md`).
Everything below is sized against those numbers, not against a mental image of a track.

| section | racing surface | = car widths | two abreast leaves |
|---|---:|---:|---:|
| pit straight (S15 + S0) | **16.0 m** (±8.0) | 7.98 | 12.0 m |
| standard | **14.0 m** (±7.0) | 6.98 | 10.0 m |
| T4 hairpin (widened) | **15.0 m** (±7.5) | 7.48 | 11.0 m |
| esses T6–T9 (narrowed) | **13.0 m** (±6.5) | 6.48 | 9.0 m |

Width transitions are linear over 60 m so no seam is visible from the air.

**Kerbs** — FIA-standard serrated, 1.50 m wide, two-tone red/white in 1.00 m alternation:
- 50 mm proud at the outer lip, 25 mm at the track-side lip, 250 mm serration pitch,
  60 mm serration amplitude. With 340 mm of ride height the car can use all of it.
- **Negative "sausage" kerbs, 100 mm** at the T8 apex and the T12 exit only. These are the
  two places the beat sheet wants visible suspension travel; 100 mm against a 340 mm ride
  height is a 29 % compression event, big enough to read at 4K and small enough not to launch
  the car.
- 1.0 m of green/white painted asphalt verge outboard of every kerb, then runoff.

**Runoff and barriers:**
- Asphalt runoff at the fast exits: T1 (28 m), T3 (35 m), T10/T11 (40 m outside the sweeper),
  T15 (30 m).
- **Gravel traps** at the two heavy braking zones: 30 m deep outside T4, 25 m outside T12.
- Three-layer TecPro at T4 and T12; steel Armco plus debris fence elsewhere, standing 18–25 m
  from the track edge except on the pit straight, where the south barrier is at **y = −19**
  (11 m of asphalt verge outboard of the 8 m half-width) and the pit wall is at **y = +11.5**
  (3.5 m from the track edge, standard).
- Debris fence 3.6 m, on 6 m posts at 8 m centres. Instanced.

**Start/finish gantry** at x = 0: legs at y = ±11.0, crossbeam soffit at z = 9.0 m, 2.2 m deep.
Wide enough that the Beat-6 closing camera at 55 m altitude looks well over it.

---

## 10. SHOWROOM, PADDOCK, THE BREACH EXIT — AND THE BEAT-6 SIGHT-LINE SOLUTION

### 10.1 The geometric problem, stated honestly

Beat 6 has a constraint that looks trivial and is not. The camera arrives at the finish line
**trailing the car** — it has just spent 7 s in an onboard follow. The showroom must be
**upstream** of the camera at that moment (the car came from there). A camera looking forward
at the car therefore has the showroom *behind it*. Putting the showroom downstream of the line
fixes the frame but breaks the merge, because the breach exit vector then points against the
racing direction and the car would have to make a 180° turn on an access road.

Three placements were tested and rejected before the fourth worked:

1. **Showroom south of the pit straight, 300 m upstream, glass facing down-track.** The
   closing camera can only see the wall from down-track, i.e. from where the car is going —
   but by then the car is past the camera. At the crossing instant the car and the showroom
   are **155.6° apart** in bearing. Dead.
2. **Showroom downstream of the line, glass facing back up-track.** Frame stacks perfectly;
   the exit vector points the wrong way and the merge needs a hairpin on the access road.
   Rejected on Beat 4.
3. **Showroom south, closing camera swung far south-west.** The camera ends up almost
   edge-on to the glass — **73° off the wall normal** — and the wound stops reading at all.

### 10.2 The solution

Put the showroom on the **north (infield/paddock) side**, west of the pit garages, with its
glass wall facing **south-east across the pit-exit apron**. Then:

- the breach exit vector points *toward the track and down-track*, so the merge is a
  textbook pit exit;
- the closing camera goes **south of the pit straight**, i.e. on the *far* side of the track
  from the showroom — which is where the glass wall is looking. The camera sees straight into
  the hole.

The car crossing the line and the breached wall end up **on the same side of the camera**,
because the camera crossed the track.

### 10.3 Exact placement

| item | value |
|---|---|
| **Breach face centre (glass wall centre)** | **(−350.00, +72.00, +0.60)** — plan, at floor level |
| **Glass wall normal / breach exit vector** | **azimuth −40.0°**, unit **(+0.766, −0.643, 0)** |
| glass wall | 22.0 m wide × 6.5 m tall, single plane, frameless structural glazing |
| glass wall end points | (−342.93, +80.43) and (−357.07, +63.57) |
| showroom footprint (4 corners) | (−342.93, +80.43), (−357.07, +63.57), (−380.51, +83.24), (−366.37, +100.10) |
| footprint extent | x −380.5 … −342.9, y +63.6 … +100.1 |
| interior | 30.0 m (along the launch axis) × 22.0 m × 6.50 m ceiling — matches the inventory exactly |
| finished floor level | **z = +0.60** (0.58 m above track grade at that station) |
| min distance building → track centreline | **63.6 m** |
| min distance breach face → track centreline | **72.0 m** |
| orientation | long axis on the −40° / +140° bearing; the car's 26 m indoor launch run is along +140°→−40° |

The building's long axis is the launch axis, so Beat 2's run-up uses the full 30 m interior
depth. At the modelled launch the car meets the glass at **≈ 85–100 km/h** (the point-mass model
gives 100 km/h in 26 m; a realistic launch-traction limit puts it nearer 85). Tune the
rigid-body sim to the *built* telemetry, not to this estimate — but design the pre-fracture
for an impact in that band.

### 10.4 The breach exit route

| leg | geometry | from | to |
|---|---|---|---|
| 1 — apron run | straight, **49.6 m**, heading −40° | (−350.00, +72.00) | (−312.00, +40.12) |
| 2 — merge curve | arc **left, R = 150 m, 40.0°**, 104.7 m, centre (−215.59, +155.02) | (−312.00, +40.12) | **(−215.59, +5.02)** heading 000° |
| — | **total access road 154.3 m** | | merges 215.6 m before the S/F line |

- The route crosses the pit-wall line (y = +13) at **x = −263.8**, so the pit wall and the
  garage row start at **x = −245** and everything west of that is open pit-exit apron. There
  is no gate to cut and no barrier to remove: the car exits into an apron that is already
  open to the circuit, which is exactly what a pit exit is.
- The merge curve is R = 150 m, whose grip-limited speed is 342 km/h. The car is doing
  **236 km/h** at the blend point, so the curve is nowhere near limiting — no camera-breaking
  understeer, and the car looks planted crossing the apron.
- Access road width 12.0 m, same asphalt shader family as the circuit but unrubbered and one
  shade lighter, with a solid white blend line for the last 90 m.
- Longitudinal fall along the route: +0.60 m → +0.02 m over 154 m = **−0.38 %**. No lip, no
  jump, no suspension event the sim has to survive.

**Speeds on the out lap** (from the same longitudinal model): 80 km/h at the glass →
**236.2 km/h at the blend point** → **294.3 km/h crossing the S/F line**. On the flying lap
62.5 s later the same station is crossed at **323.4 km/h**. Same tarmac, two speeds, one
unbroken shot — that contrast is free and should be used.

### 10.5 Paddock and pit complex (dressing that the camera crosses)

| element | extent |
|---|---|
| pit wall | y = +11.5, from x = −245 to x = +130, 1.2 m high |
| pit lane | y = +11.5 … +23.5 (12.0 m), from x = −245 to x = +130 |
| pit garages | y = +23.5 … +40.5, x = −245 … +75, roof at z = 12.0 m, 14 bays at 22 m |
| paddock | y = +40.5 … +115, x = −480 … +100 — trucks, awnings, tyre stacks, fencing |
| **showroom** | x −380.5 … −342.9, y +63.6 … +100.1 — sits *in* the paddock, west of the garages |
| pit-exit apron | x = −480 … −245, y = 0 … +45 — the surface the breach route crosses |
| grandstands | south of the pit straight, y = −30 … −58, x = −420 … +180, 14 m high |

The showroom is a glass-and-anodised pavilion in the paddock, which is exactly what a
manufacturer hospitality unit is at a real circuit — so nothing has to be explained.

### 10.6 THE BEAT-6 SIGHT-LINE SOLUTION (solved, not hand-waved)

**Requirement:** at the instant the car crosses the S/F line, one frame must contain the car
at the line *and* the breached glass wall.

**Solution:** camera at **(−40, −150, +55)** on a **21 mm** lens (81.2° horizontal FOV on a
36 mm sensor).

| quantity | value |
|---|---:|
| camera → car at the line | **165 m**, bearing 75.1°, car at 323.4 km/h |
| camera → breach aperture | **385 m**, bearing 144.4° |
| **angular separation** | **69.3°** — inside an 81.2° frame with 12° to spare ✅ |
| **angle off the glass-wall normal** | **4.4°** — the camera is essentially *on the breach axis* |
| glass wall in frame | **128 px** wide in a 3840 px frame |
| breach aperture (≈10 m) in frame | **58 px** |
| occlusion by pit garages | **clear** — sight-line crosses y = +25.0 at (x = −284.4, z = 14.3) and y = +40.5 at (x = −306.0, z = 10.7); the garage row is x = −245 … +75, so the ray passes 40–60 m west of it |
| occlusion by pit wall | **clear** — crosses y = +11.5 at (x = −265.5, **z = 17.5 m**), fourteen times the 1.2 m wall height |

Because the camera is only **4.4° off the wall normal**, it is not looking at a hole — it is
looking *through* it, down the breach axis, straight into the room the film started in. The
turntable, the ceiling coves and the spot rigs are visible through the aperture at 385 m.
That is the payoff of putting the finish line at x = 0 rather than anywhere else on the
straight.

**The full Beat-6 move.** The camera peels off the car 3 s before the line, then flies a
**314.2 m arc** from (−40, −150, 55) to (−55, −460, 104), decelerating from **83 m/s to
6 m/s** on an eased profile, with the focal length ramping 21 → 18.8 → 26 mm (opening as it
climbs, settling as it arrives). Every keyframe was checked; nothing leaves frame.

| t (s) | camera (x, y, z) | lens | car | showroom | separation | fits |
|---:|---|---:|---|---|---:|:-:|
| −3.0 | (−232, −2, 3.2) | 24 mm | 29 m astern, 299 km/h | 139 m, 401 px | 28.1° | ✅ |
| **0.0** | **(−40, −150, 55)** | **21 mm** | **165 m, at the line, 323 km/h** | **385 m, 128 px, 4.4° off-normal** | **69.3°** | ✅ |
| +1.0 | (−44.6, −244.9, 70.0) | 19.5 mm | 288 m, 328 km/h | 445 m, 102 px | 72.9° | ✅ |
| +2.0 | (−48.1, −318.2, 81.6) | 18.8 mm | 401 m, 332 km/h | 500 m, 86 px | 73.6° | ✅ |
| +3.0 | (−50.8, −372.6, 90.2) | 19.0 mm | 489 m, braking for T1 | 543 m, 79 px | 73.2° | ✅ |
| +4.0 | (−52.6, −410.9, 96.2) | 20.0 mm | 565 m, in T1 | 575 m, 78 px | 71.6° | ✅ |
| +5.0 | (−53.8, −435.9, 100.2) | 22.0 mm | 639 m, T1 exit | 596 m, 82 px | 68.9° | ✅ |
| **+7.0** | **(−55, −460, 104)** | **26 mm** | 768 m, through T2 | **617 m, 92 px, 21.0° off-normal** | 62.8° | ✅ |
| +8.5 | *hold* | 26 mm | 855 m, east chute, 270 km/h | 617 m, 92 px | 58.7° | ✅ |
| +10.0 | *hold* | 26 mm | 957 m, east chute, 295 km/h | 617 m, 92 px | 55.0° | ✅ |

**The final composed frame** (held 3 s, t = +7.0 → +10.0): camera 104 m up and 460 m south of
the pit straight, looking north. Left-of-centre, 617 m away, the showroom with its wound —
21° off the wall normal now, so the depth of the breach and the shard field on the apron rake
across the low sun. Centre, the finish gantry and the whole 810 m pit straight. Right, at
900+ m, the car streaking north up the east chute at 295 km/h. Between and behind them the
esses on the skyline at +8.5 m. The wound and the lap in one frame, with the entire circuit
between them.

**Dependency, flagged:** at 617 m the glass wall is 92 px and the aperture 41 px. That reads
*only* if the showroom interior is still lit and the breach glows. If the interior goes dark
after the launch, the wound vanishes at that distance. **The showroom spot rigs must stay on
for the whole film** — write it into the lighting brief, not just the beat sheet.

---

## 11. CAMERA NOTE PER BEAT

### Beat 1 — assembly (inside the showroom)
Nothing here is circuit geometry, but the placement matters: the showroom's long axis runs
**−40° / +140°**, and the glass wall faces the pit-exit apron with the circuit beyond it.
That means the **exploded field is backlit by the track**. The 9.84 × 4.49 × 5.96 m parts
volume from the inventory sits in a 30 × 22 × 6.5 m room whose entire east-south-east wall is
a 22 × 6.5 m window onto a late-afternoon circuit. Every one of the 15 clusters gets rim
separation from a real, motivated source, and the camera weaving the field always has a bright
negative space to compose against. *What another layout does not give:* a showroom placed
behind the pits, or facing away from the track, makes Beat 1 an interior with no exterior —
and then Beat 3's breach reveals nothing the audience has been anticipating for 33 s.

### Beat 2 — ignition and launch
The 30 m interior depth is the launch run. Camera settles low behind the left rear at
z = 0.55, 6 m back, looking down the launch axis at the glass — which frames the pit-exit
apron and, 220 m beyond it, the pit straight. The car is aimed at the circuit from the first
frame of the launch. *What this layout gives:* the target of the launch is visible through the
target of the launch.

### Beat 3 — the breach
The wall normal is −40°, i.e. the car exits **across** the frame relative to the pit straight,
not along it. That is deliberate: the camera arcs around the erupting shard field while
world-time is at 15–25 %, and because the exit vector is oblique to the track, the arc can
carry the camera from *inside* the room to *outside* it while continuously holding both the
car and the hole. A wall facing straight down the straight would force the arc to be a
pull-back, which reads as retreat. And the breach is 63.6 m from the racing surface, so the
outbound shard field lands on the paddock apron — dressed concrete, not tarmac, and therefore
a different skitter sound and a different specular response.

### Beat 4 — transit
154.3 m of access road: a 49.6 m apron run and a 104.7 m R150 left onto the circuit, joining
216 m before the line. The camera pulls back and up into chase as the car crosses the apron.
Because the merge is a genuine pit-exit blend, the camera crosses the pit-wall line, the
garage row and the blend line in one continuous climb — three real thresholds in 6.5 s, which
is what sells "we went from inside a building onto a race track without a cut". *What another
layout does not give:* a showroom that opens directly onto the racing surface would have no
thresholds at all, and the transit would be an eight-second nothing.

### Beat 5 — the lap
Phase budget, from the solved telemetry:

| phase | stations | duration | what the geometry provides |
|---|---|---:|---|
| chase, T1–T3 | s 0 → 760 | **10.6 s** | 166 m of continuous linked-left arc (T1+T2) to slide from astern to outboard, then 266 m of straight to hold it, then T3 at 295 km/h to hand the car away |
| kerb-height hairpin pass | s 760 → 1160 | **10.0 s** | 85 m of braking from 265 to 80 km/h, then **176° of yaw at ≤ 80 km/h in 3.9 s** in front of a camera on the inside kerb at z = 0.85 |
| rise + helicopter arc, esses | s 1160 → 1910 | **14.9 s** | a +3.97 % ramp to climb with the car, then 358 m of alternating direction on the summit, T8 off-camber at +8.50 m |
| dive to the sweeper | s 1910 → 2400 | **6.8 s** | 224.9 m of flat-out crest run to dive down, then 264 m of 93.4° left with apexes at 282 and 255 km/h and a 306 km/h release between them — the optional speed ramp lives here |
| **doppler hover** | s 2400 → 2700 | **4.3 s** *(car within ±200 m of the station for **6.87 s**)* | see below |
| whip and catch | s 2700 → 3115 | **8.8 s** | car covers 415 m through four corners; camera flies a 279 m chord at 38 m/s mean |
| onboard follow | s 3115 → 3675 | **7.1 s** | 559 m, 207 → 323 km/h, dead straight, flat |

**The doppler pass, specified.** Hover station at **s = 2555**, camera at **(−810.3, +410.7,
+3.94)**, i.e. **26 m outboard of the centreline** and 2.4 m above the local grade, on the
outside of the descending doppler straight. The camera pans (does not translate) to hold the
car.

| car position relative to station | speed | time | slant range |
|---:|---:|---:|---:|
| −180 m (approaching) | 254.6 km/h | −2.37 s | 182 m |
| −90 m | 275.3 km/h | −1.14 s | 94 m |
| **0 m** | **293.5 km/h** | **0.00 s** | **26 m** |
| +90 m (braking) | 230.7 km/h | +1.14 s | 94 m |
| +180 m | 113.8 km/h | +3.42 s | 178 m |

Radial velocity at ±90 m is ±73.5 / ∓61.6 m/s, so the doppler ratio sweeps
**1.273 → 0.848 — a factor of 1.50, a clean perfect fifth (≈ 7.0 semitones) in about 2.3 s**,
with no special-casing: it falls out of the geometry. The camera is near-static (≤ 4 m/s) for
**6.9 s**, more than double the 3 s minimum. And the braking zone starts almost exactly at the
station, so the departing half of the pass has glowing discs, a squatting rear axle and the
downshift blips — the picture and the audio peak on the same frame.

### Beat 6 — the ending
Fully solved in section 10.6. The one thing to say here that is not in that table: the camera
**crosses the racing surface during the peel-off**. It is tucked behind the car on the
centreline at t = −3.0 s and is 150 m south of it by t = 0, so it leaves the tarmac roughly
2 s before the line while the car is still ~180 m short. That crossing is what makes the
composition possible, and it is the last threshold the camera passes — bookending the glass
wall it went through 90 s earlier.

---

## 12. RACING PLAUSIBILITY — SHOWING THE WORK

The risk of camera-first design is a track no driver would recognise. Audit:

**Corner-type distribution.** 1 hairpin, 4 esse corners, 2 sweeper apexes with a release,
3 fast corners above 250 km/h, 3 medium (150–220 km/h), 2 slow (< 150 km/h). That is a
conventional modern-F1 spread. Nothing is a constant-radius 180° "video-game" corner except
the hairpin, which is supposed to be.

**Lateral load.** Peak 4.9 g (T3), then 4.2 / 4.1 g (T10/T11), then 3.4 g and below. Modern F1
peaks at 5–6 g. Nothing here exceeds what the cars do at Copse, Blanchimont or Turn 8.

**Braking events.** Three real ones (T1, T4, T12) at 2.8–3.0 g mean over 85–101 m. Real F1
stopping distances from 300 km/h are 100–130 m. Consistent.

**Speed distribution.** 67.1 % of the lap *by distance* is above 200 km/h, 46.2 % above
250 km/h, 14.4 % above 300 km/h (53.9 / 34.0 / 9.6 % by *time*). The 810 m pit straight alone
is 22 % of the lap length. That is a medium-downforce circuit — Austria or Baku, not Monaco.

**Overtaking.** T4 is a genuine passing place: 302 km/h down to 80 km/h with 150 m of
approach straight and a 15 m-wide entry. T12 is a second, weaker one. A DRS zone on the pit
straight (detection at T14 exit, activation 90 m after T15) and a second on the crest run
would be conventional. This is the layout's weakest racing credential — see weakness #7.

**Direction of travel.** Counter-clockwise, 10 lefts to 5 rights, which is Interlagos/Baku
territory and puts the neck load on the right side. Fine.

**Pit lane.** Entry would be at T15 exit (a lane peeling off at x ≈ −620 inside the corner),
exit at the blend point (−215.6, +5.0). Pit lane length ≈ 400 m; at 80 km/h that is 18 s,
against a lap of 62.5 s — a pit-lane time loss around 20 s including the in/out delta, which
is normal.

**Where the layout is *not* plausible:** T14 is 19.4° of arc over 30.5 m. It is a kink, not a
corner. It is counted as one of the 15 because it is a genuine direction change (the only
right-hander in the final complex) and because the closure solve needed its angle — but a
driver would call this a 14-corner circuit. Both counts are inside the 12–16 requirement, so
nothing breaks; the honesty is the point.

---

## 13. HONEST WEAKNESSES OF THIS DESIGN

1. **T14 is a kink dressed as a corner.** 19.4° at R = 90 m, 30.5 m of arc, taken at
   178 km/h — barely a lift. Counting it gets me to 15 corners; without it the circuit has 14,
   which still satisfies the brief. It exists because the closure solver needed its angle and
   because the camera needs one right-hand direction change while it re-acquires the car in
   the final complex. It is the least honest line in the corner table.

2. **T3 is doing too much work.** R = 140 m at 295 km/h is **4.9 g** — legal for a modern F1
   car but right at the ceiling, and with only 68 m of arc it will read on camera as a
   full-throttle kink rather than a corner. I kept it because the chase needs a hand-off
   moment before dropping to the hairpin, but a purist would say the circuit really has 14
   corners and one very fast kink, not 15 corners.

3. **The elevation is spread too thin to photograph.** 11.00 m over 3 675 m is a mean absolute
   gradient under 1.5 %. Only the hairpin exit ramp (+3.97 % over ~180 m) will read as a hill
   inside a single frame. The 8.5 m summit at T8 gives the helicopter arc somewhere to be, but
   at 4K from 70 m up, 8.5 m of relief across 600 m of plan is close to invisible in the
   racing surface alone. **The relief has to be exaggerated by the surrounding terrain** —
   banked infield, a stepped treeline, grandstand plinths following the grade — or Beat 5's
   "rise and dive" will look like a crane move on a billiard table. The brief's 12 m ceiling
   makes this unfixable inside the racing surface.

4. **The camera's catch-up after the doppler hover is at the edge of credibility.** 279 m of
   chord in 7.35 s is 38 m/s mean, but because it starts from a near-hover the peak is around
   **62 m/s (223 km/h)** and the path crosses the racing surface. That is faster than any
   camera helicopter and at the top of what the fastest FPV drones do. It is flyable in the
   fiction and it is *motivated* (the camera cuts the corner the car has to drive round), but
   a viewer who flies drones will feel it. If it reads badly, the fix is to move the hover
   station 40 m later (s = 2600), which drops the chord to 254 m and the mean to 36.3 m/s at
   the cost of a slightly less clean approach sight-line.

5. **The west lobe is expensive world.** The plan reaches to x = −967, which is 407 m west of
   the pit straight's west end. Everything out there — T10 through T15, the doppler straight,
   the descending west hillside — is real geometry the camera flies at 100 m altitude in Beat
   6 while it is 600–900 m away. There are no cheap far-side zones on this layout (the brief
   forbids them anyway), so a large amount of world gets built at LOD-2 fidelity for a few
   seconds of background. Budget for it or the Beat-6 hold will show a soft, empty west.

6. **Beat 4 comes out short.** 154.3 m of access road plus 215.6 m of pit straight is
   **≈ 6.5 s** of world time from the glass to the line, against the brief's ~8 s. Options:
   extend Beat 3's ramp tail into the transit, add a gentle ramp on the merge, or accept a
   6.5 s Beat 4 and give the second back to Beat 1. I would accept 6.5 s — but the beat sheet
   owner must make that call deliberately, not discover it in the edit.

7. **As a racing circuit it has one and a half overtaking spots.** T4 under braking from
   302 km/h is a real one. T12 is a weak second. A modern F1 layout of this length would want
   two strong zones and a third opportunistic one. I traded that away for the camera:
   the T12–T15 complex exists so the camera can catch the car, not so cars can pass each
   other. Nothing overtakes in this film, so the cost is invisible on screen and real on paper.

8. **The Beat-6 wound depends entirely on the interior lighting.** At the held position the
   glass wall is 92 px and the breach aperture 41 px in a 3840 px frame. That reads as a wound
   *only* because the room behind it is lit and the aperture glows. If the showroom rigs are
   killed after the launch, the closing frame's most important story element becomes a grey
   smudge. This is a hard cross-department dependency and it is not obvious from the layout.

9. **The two pit-straight passes could read as a repeat.** The camera flies the same 350 m of
   tarmac in the same direction twice, 62 s apart (out lap at 294 km/h, flying lap at
   323 km/h). If both are framed low and behind the car, the audience will feel a loop even
   though there is no cut. The beat sheet must make them different by construction — the out
   lap wide and outboard at 25 m lateral, the flying lap tight and onboard at 11 m astern.

10. **The lap-time model has a ±5 % band.** It is a point-mass with a single-parameter
    downforce fit and no combined-slip, no tyre state, no gear steps. 62.54 s could honestly be
    59.5–65.7 s. The upper end touches the brief's 65 s ceiling. If the built telemetry lands
    above 64 s, the cheapest fix is to shorten S9 (crest run) by 60 m and re-solve closure on
    S2/S11 — that is why those three straights were the free variables.

---

## 14. REPRODUCTION

The solvers that produced every number above were written and run outside the project tree
(this design task was read-only except for this file). They live at:

```
<scratchpad>/cd/final.py       closure solve, elevation spline, speed profile,
                               corner table, control-point export
<scratchpad>/cd/showroom.py    showroom placement, breach exit route,
                               Beat-6 optics, occlusion and pixel budgets
<scratchpad>/cd/final.npz      P (centreline), S, Z, V, T, CP arrays
<scratchpad>/cd/final.json     corner table as structured data
```

Move them to `tools/circuit_D_final.py` and `tools/circuit_D_showroom.py` if this layout is
selected; they are self-contained (numpy only, no scipy) and take no arguments.

Verification assertions that must hold after any edit:

| assertion | expected |
|---|---|
| end of T15 | (−560.000, 0.000), heading 360.000° |
| total length | 3 675.0 m ± 0.1 |
| lap time | 62.54 s ± 0.05 |
| elevation range | 11.00 m |
| min non-adjacent centreline separation | ≥ 59.0 m (no self-intersection, no unbuildable pinch) |
| T4 apex | 79.6 km/h (the brief's ~80) |
| pit-straight peak | 331.8 km/h (the brief's ~330) |
| Beat-6 key A separation | 69.3° < 81.2° hFOV; off-normal 4.4°; garages and pit wall clear |

**Blender import.** Section 7's control points go straight into a `POLY` spline; set it cyclic,
give it a 16.0 m → 13.0 m animated bevel (or a geometry-nodes sweep driven by an
`s`-parameterised width curve per section 9), and evaluate the clothoid transitions of section
6 as a subdivision pass rather than by moving control points — the closure and the length are
solved for the arc/straight definition, and nudging control points by hand will break both.

The world datum is **the start/finish line at the origin**, chosen so that every camera
number in this document and in the beat sheet can be read without an offset.
