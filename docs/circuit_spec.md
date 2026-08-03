# CIRCUIT VITRINE — FINAL BUILDABLE SPECIFICATION

**Synthesis of three candidate layouts.** Base layout: **D_camera "Vitrine"** (aggregate
25.5/30, first on all three judging axes). Grafts taken from **A_flowing "Vallon"** and
**C_street "Quartier Vitrine"** are listed and justified in §12; grafts rejected are listed
there too, with the arithmetic that killed them.

**Every number in this document was recomputed from scratch**, not copied from the source
layouts. The closure solve, the vertical alignment, the speed profile, the lap time, the
launch dynamics, the doppler physics and the Beat-6 optics all come from the solver scripts
in §14. Where the source layouts were wrong, §13 says so and gives the corrected value.

---

## 1. HEADLINE

| | value | requirement | ✓ |
|---|---:|---|:-:|
| **Total length** | **3 675.00 m** | — | |
| **Corners** | **15** (T1–T15, plus one unnumbered release arc) | 12–16 | ✓ |
| **Predicted lap (centreline, steady state)** | **63.54 s** | 55–65 s | ✓ |
| on-screen lap, line to line (entered at 288.6 km/h) | **63.70 s** | | |
| average lap speed | 208.2 km/h | | |
| **Top speed** | **330.8 km/h** (pit straight, s = 156 m) | ~330 | ✓ |
| speed crossing S/F, flying lap | 323.4 km/h | | |
| speed crossing S/F, out lap | 288.6 km/h | | |
| **Hairpin (T4) apex** | **79.6 km/h**, R = 28 m, 176° | ~80 | ✓ |
| **esses complex** | T6–T9, L-R-L-R over 358 m, 154–186 km/h | required | ✓ |
| **double-apex sweeper** | T10/T11, R125 → R400 release → R150, 255 → 294 km/h | required | ✓ |
| **Elevation range** | **11.63 m** (−3.67 m at T12 → +7.96 m at T8) | 8–12 m | ✓ |
| max / min gradient | **+5.20 % / −4.45 %** | | |
| plan footprint (circuit frame) | 1 291.8 × 685.0 m | | |
| min separation, non-adjacent centrelines | 60.6 m (s 872 ↔ 1092) | | |
| sector times (s 0–1200 / 1200–2450 / 2450–3675) | 22.09 / 21.75 / 19.71 s | | |
| direction | **counter-clockwise**, net +360.000° | | |
| plan closure residual | **(0.0, 4.9 × 10⁻¹⁵) m**, heading 360.000000° | must close | ✓ |
| **elevation closure residual** | **0.00 m exactly**, grade 0.000 % both sides of the datum | must close | ✓ |

**Screen-time budget for the whole film**

| beat | screen time | world time | note |
|---|---:|---:|---|
| 1 assembly | 33.0 s | 33.0 s | inventory's 15 clusters |
| 2 ignition + launch | 3.0 s | 3.0 s | 1.2 s stillness + **1.78 s** solved launch |
| 3 breach | 8.0 s | ~1.6 s | speed ramp to 15–25 % |
| 4 transit | 5.6 s | 5.6 s | 30 m past the glass → S/F line |
| 5 the flying lap | **63.7 s** | 63.7 s | + 1.8 s if the optional T10/T11 ramp is taken |
| 6 the ending | **11.0 s** | 11.0 s | 8.0 s move + **3.0 s hold** |
| **total** | **124.3 s** (126.1 s with the ramp) | | inside 100–130 s ✓ |

---

## 2. TWO FRAMES, STATED ONCE

Everything below uses one of two frames. Confusing them is the single easiest way to build
this wrong, so they are defined here and never re-defined.

**WORLD frame `W`** — the Blender scene frame, and the frame of every coordinate in
`circuit_spec.json`.

* Origin = **the centre of the round-1 showroom floor**. `Floor` spans X −15…+15, Y −11…+11,
  top at Z = 0.000.
* **Z = 0.000 is simultaneously the showroom finished floor, the paddock apron, the access
  road and the pit-straight racing surface.** One plane, no lip, no step.
* **+X is the breach exit vector.** The car's nose points +X (measured: `FW_` centroid
  +2.679, `RW_` −2.350), the glazed bay `GW_Right` is the plane X = +15 with outward normal
  +X, so the launch, the breach and the first 50 m of the transit all run along +X.
* **The round-1 showroom is NOT moved, rotated or scaled.** Transform = identity.

**CIRCUIT frame `C`** — a presentation and layout frame in which the pit straight lies on
`y = 0` running +x, and the start/finish line is the origin. All *trackside furniture*
(pit wall, garages, paddock, grandstands, gantry) is dimensioned in `C`, because it should
be aligned to the pit straight rather than to the world axes.

```
    W = Rz(+40.000°) · ( C − (−350.000, +72.000) ) + (15.000, 0.000)
    C = Rz(−40.000°) · ( W − (  15.000,   0.000) ) + (−350.000, +72.000)
    z is identical in both frames.
```

Consequences, all exact:

| item | circuit frame C | world frame W |
|---|---|---|
| start/finish line | (0, 0, 0) | **(329.396, 169.820, 0.000)** |
| breach face centre | (−350, +72, 3.10) | **(15.000, 0.000, 3.100)** |
| racing direction on the pit straight | +x (0°) | bearing **40.000°** |
| T15 exit (start of the pit straight) | (−560.25, 0, −0.17) | (−99.59, −190.14, −0.17) |
| pit-exit merge onto the circuit | (−215.75, 0, 0.00) | (164.12, 31.14, 0.000) |

---

## 3. PLAN VIEW

Drawn in the **circuit frame** because that is legible; every coordinate table gives world.
`1 col ≈ 15.6 m`, `1 row ≈ 26.0 m` (rows are compressed ~1.7 : 1, characters are, the
geometry is not).

```
   +y                                                          x −919 … +513 · y −110 … +775
    ^
    |         T10  ┌──────── LE SOMMET (summit shelf, z +7.7 … +8.0) ───────┐
    |     #########                                                              ###
    |  ####       ######                                                        ## ##  ◄── T4
    |###               ######           T8      T7                             ##  ##      LE PIN
    ##                      ##############    ######                          ##  ##       R28 / 176°
    #                          T9        ####    ####                        ##   #        79.6 km/h
   ##                                       ####   ####                     ##   ##        z −3.21
   #   S9 summit run                            #####    ####              ##   ##
  ##   (crest, −2.00 %)                             ####    #######       ##   ##
  #                                                     T6      #######  ##   #    ▲
 D##  ◄── DOPPLER STATION  s = 2555                                  T5 ──┘    #    │ S3
  #      camera (−835.4, +417.3, +4.80)C                                       #    │ hairpin
  #      = (−578.8, −47.5, +4.80)W                                             #    │ approach
 ##      car at 313.2 km/h, 26.1 m slant                                       #    │
 #                                                                             #  T3
##   LA PLONGÉE  −4.45 % over 160 m                                            #  ◄── R140, 295 km/h
#    S11 doppler straight, 297.6 m                                             #      4.89 g
##                                                                             #
 ##  T12 ◄── R50, 313.8 → 113.8 km/h in 139.8 m, DOWNHILL, z −3.56             #  S2 east chute
  ##                                                                           #
   ####  T13                                                                   #
      ###   T14                                                                #  T2
         ##          ┌──────────┐                                              #  ◄── R110
          ##         │ SHOWROOM │ 34 × 26 m pavilion, floor z = 0.000          ## T1
            ##       │  S S S   │                                             ## ◄── R100
             ###     └────G:::  │  G = breached glazed bay, 22.0 m, normal −40°C / +X world
              T15      ####:::::::                                          ###
                ###########################:::################L###############
                          P I T   S T R A I G H T   810 m         ▲
                    ~~~ pit lane ~~~ garages ~~~                  │
                                                            S/F line, x = 0
                    ▓▓▓▓ grandstands, y −34 … −62, 14 m ▓▓▓▓            C = Beat-6 hold
                                                                        (104, −288, 140)C
```

Reading the lap from the line: **east along the 810 m pit straight** → **T1/T2** a linked
left-left that turns the car north → **S2 east chute** → **T3** a 295 km/h right kink →
downhill braking into **T4 LE PIN**, the 176° hairpin at the lip of the north-east
escarpment → **LA RAMPE**, 180 m at +5.20 % out of the hairpin → **T5** hooks onto the
WNW climb → **T6–T9**, the esses, on the summit shelf → **S9 summit run**, cresting and
falling at −2.00 % → **T10/T10b/T11**, the increasing-radius double-apex sweeper →
**LE BASCULEMENT**, the crest at the top of **LA PLONGÉE**, −4.45 % → downhill heavy braking
into **T12** at the circuit's low point → **T13/T14/T15** hook east → back onto the pit
straight.

---

## 4. CORNER TABLE

`brake@` is the peak speed in the 250 m before turn-in — the speed at which the driver hits
the brakes. Speeds are km/h from the solved profile (§7). `z` and `grade` are centreline
values at the apex. `t` is the elapsed lap time at the apex on a flying lap.

| # | name | type | dir | R (m) | arc° | arc (m) | brake@ | turn-in | **apex** | exit | lat g | bank | z (m) | grade | t (s) | apex (x, y) **world** |
|---|---|---|:-:|---:|---:|---:|---:|---:|---:|---:|---:|:-:|---:|---:|---:|---|
| **T1** | Vitrine | fast left | L | 100 | +62.0 | 108.2 | **330.8** | 197.2 | **197.2** | 197.4 | 3.06 | 2° | +0.00 | 0.00 % | 4.01 | (+551.1, +374.4) |
| **T2** | Threshold | linked left | L | 110 | +30.0 | 57.6 | 197.2* | 218.0 | **218.0** | 218.1 | 3.40 | 2° | +0.00 | 0.00 % | 6.16 | (+536.5, +494.1) |
| **T3** | Long Kink | fast right kink | R | 140 | −28.0 | 68.4 | 296.4 | 295.1 | **295.1** | 295.2 | 4.89 | 3° | −0.61 | −0.28 % | 10.67 | (+323.4, +742.7) |
| **T4** | **LE PIN** | **HAIRPIN** | L | **28** | **+176.0** | 86.0 | **296.4** | 79.6 | **79.6** | 80.0 | 1.78 | −1.5°→0 † | **−3.21** | −0.57 % | 16.12 | (+241.8, +940.7) |
| **T5** | La Rampe | medium right, uphill | R | 75 | −88.0 | 115.2 | 216.7 | 152.7 | **152.7** | 153.0 | 2.45 | 1° | +6.11 | +0.48 % | 23.45 | (+238.9, +681.3) |
| **T6** | Weave 1 | esse, left | L | 88 | +38.0 | 58.4 | 258.5 | 174.8 | **174.8** | 175.0 | 2.73 | flat | +7.24 | +0.35 % | 29.29 | (−59.9, +591.2) |
| **T7** | Weave 2 | esse, right | R | 82 | −44.0 | 63.0 | 174.8* | 164.4 | **164.4** | 164.6 | 2.59 | flat | +7.60 | +0.35 % | 31.41 | (−133.2, +520.5) |
| **T8** | Crest | esse, left — **SUMMIT** | L | 76 | +46.0 | 61.0 | 164.4* | 154.4 | **154.4** | 154.6 | 2.47 | **−1° off-camber** | **+7.95** | +0.18 % | 33.65 | (−231.8, +498.1) |
| **T9** | Weave 4 | esse, right | R | 94 | −30.0 | 49.2 | 194.3 | 185.7 | **185.7** | 185.9 | 2.89 | flat | +7.84 | −0.18 % | 35.76 | (−300.1, +425.7) |
| **T10** | Panorama 1 | **double-apex A** | L | **125** | +44.0 | 96.0 | 281.0 | 254.6 | **254.6** | 254.6 | 4.08 | 4° | +4.60 | −0.31 % | 40.45 | (−582.8, +298.2) |
| — | *release* | opening arc, not a corner | L | 400 | +8.0 | 55.9 | — | 254.6 | *254.6* | 271.3 | 1.28 | 4° | +4.36 | −0.31 % | 41.52 | (−620.7, +233.2) |
| **T11** | Panorama 2 | **double-apex B** | L | **150** | +41.4 | 108.4 | 281.0 | 271.3 | **271.3** | **293.7** | 3.86 | 4° | +4.10 | −0.31 % | 42.59 | (−634.5, +153.1) |
| **T12** | La Plongée | heavy-braking left | L | 50 | +52.0 | 45.4 | **313.8** | 113.8 | **113.8** | 114.2 | 2.04 | flat | **−3.56** | −1.03 % | 48.37 | (−478.9, −185.4) |
| **T13** | Hook | slow left | L | 70 | +22.0 | 26.9 | 113.8* | 144.7 | **144.7** | 145.0 | 2.35 | flat | −3.41 | +0.85 % | 50.82 | (−391.6, −208.8) |
| **T14** | Flick | right kink | R | 90 | −19.4 | 30.5 | 199.4 | 178.4 | **178.4** | 178.4 | 2.78 | flat | −2.31 | +1.14 % | 52.90 | (−294.0, −195.2) |
| **T15** | Gate | fast final left | L | 105 | +50.0 | 91.6 | 231.3 | 207.7 | **207.3** | 207.3 | 3.22 | 3° | −0.54 | +1.01 % | 55.63 | (−140.0, −211.2) |

`*` = inside a linked complex; the "brake@" column is the previous corner's exit.
`†` = T4 carries **−1.5 % adverse camber on entry easing to flat at the apex** (grafted from C):
it is what a real road that drains toward falling ground does, it costs nothing, and it makes
the 176° of yaw visibly harder work under the kerb-height camera.

Net turn = +62 +30 −28 +176 −88 +38 −44 +46 −30 +44 +8 +41.4 +52 +22 −19.4 +50 =
**+360.0° exactly**. Ten left-handers, five rights. Longest single arc T5 at 115.2 m,
shortest T13 at 26.9 m.

**The double-apex is now increasing-radius** (grafted from C): R125 → R400 release → R150,
with the car **accelerating through it, 254.6 → 271.3 → 293.7 km/h**. That is the
Pouhon/Copse pattern. D's original decreasing sequence (150 → 420 → 125) had the car
*decelerating* into its second apex, which is the wrong shape both for racing and for a
banking camera arc. The swap re-solved the closure in one pass and cost nothing: S9 grew
13.9 m, S11 shrank 8.8 m, total length and every downstream corner position unchanged.

**Banking** is a design choice, not a solve: 4° through the sweeper so a 294 km/h exit does
not look like it is riding on the edge, 3° at T3 and T15, 2° at T1/T2, 1° at T5. **T8 carries
1° of adverse camber at the summit** — the meanest thing on the circuit and the reason the
car looks light there under the helicopter arc.

**Braking events** — all four fall out of the published vehicle model (§7), which was the
whole point of grafting A's brake curve:

| zone | from | to | distance | time | mean decel | road grade |
|---|---:|---:|---:|---:|---:|---|
| into **T1** | 330.8 | 197.2 km/h | **93.8 m** | 1.31 s | **2.96 g** | 0.00 % (flat) |
| into **T4** (the hairpin) | 296.4 | 79.6 km/h | **143.8 m** | 3.01 s | **2.23 g** | −0.86 → −1.09 % (downhill) |
| brush into **T10** | 281.0 | 254.6 km/h | 18.8 m | 0.25 s | 2.97 g | −0.67 → −0.35 % |
| into **T12** | 313.8 | 113.8 km/h | **139.8 m** | 2.52 s | **2.41 g** | **−3.00 → −2.24 % (downhill)** |

Real F1 stopping distances from 300–330 km/h are 100–150 m. All three heavy zones land in
that band. The T12 stop is now a genuine **downhill** heavy braking event, which is what both
the authenticity judge and the cinematic judge asked for and which D did not have.

---

## 5. ELEVATION

**Method: tangent grades joined by parabolic vertical curves**, not an interpolating spline
through keyframes. This is how road vertical alignment is actually designed, and it means the
maximum gradient is a *stated design value* rather than an artefact of an interpolator —
which was exactly the defect the authenticity judge found in D (headline +3.97 %, real
+3.11 %).

Landform-first (grafted from A), with the budget **concentrated into three features and the
rest genuinely flat** (grafted from C). Total relief **11.63 m**, inside the 8–12 m window.

| PVI s (m) | z (m) | vertical curve L (m) | grade out | landform |
|---:|---:|---:|---:|---|
| 0.0 | **0.000** | — | 0.000 % | S/F line — the plateau, dead flat |
| 470.0 | 0.000 | 80 | −0.212 % | end of the flat plateau (T2 exit) |
| 800.0 | −0.700 | 100 | −1.633 % | east chute has drifted down |
| 950.0 | −3.150 | 110 | −0.294 % | foot of the fall — hairpin braking board |
| **1035.0** | **−3.400** | 60 | **+5.200 %** | T4 exit — bottom of **LA RAMPE** |
| **1215.0** | **+5.960** | 90 | +0.355 % | top of LA RAMPE (180 m at +5.20 %) |
| **1790.0** | **+8.000** | 60 | −0.182 % | **T8 apex — SUMMIT** |
| 1955.0 | +7.700 | 80 | −2.000 % | end of the summit shelf |
| 2095.0 | +4.900 | 100 | −0.313 % | foot of the summit rollover (140 m at −2.00 %) |
| 2430.0 | +3.850 | 70 | −0.300 % | the sweeper on its shelf |
| **2540.0** | **+3.520** | 140 | **−4.450 %** | **LE BASCULEMENT** — crest at the top of the plunge |
| **2700.0** | **−3.600** | 80 | −0.133 % | foot of **LA PLONGÉE** (160 m at −4.45 %) |
| 2790.0 | **−3.720** | 90 | +1.145 % | **T12 — LOW POINT** |
| 3115.0 | 0.000 | 120 | 0.000 % | T15 exit, back on the plateau |
| 3675.0 | 0.000 | — | — | closes on the datum |

**Verified:** `z(0) = 0.0000`, `z(3675) = 0.0000`, closure error **0.00 m exactly**; grade is
`0.000 %` on both sides of the wrap, so the profile is C¹ across the start/finish line as
well as everywhere else. Realised extremes: **z_min = −3.666 m at s = 2754** (T12 exit),
**z_max = +7.964 m at s = 1800** (just past T8). Realised grade extremes **+5.200 % / −4.450 %**
— identical to the design tangents, because they *are* the design tangents.

**Vertical curve comfort check** (vertical acceleration `a = v²·A / (100·L)`):

| curve | A (%) | L (m) | design speed | vertical a |
|---|---:|---:|---:|---:|
| sag, bottom of La Rampe (s 1035) | 5.49 | 60 | 88 km/h | 0.55 m/s² |
| crest, top of La Rampe (s 1215) | 4.85 | 90 | 150 km/h | 0.94 m/s² |
| crest, summit rollover (s 1955) | 1.82 | 80 | 290 km/h | 1.48 m/s² |
| **crest, Le Basculement (s 2540)** | **4.15** | **140** | **314 km/h** | **2.25 m/s² (0.23 g)** |
| sag, foot of La Plongée (s 2700) | 4.32 | 80 | 130 km/h | 0.70 m/s² |

Le Basculement is the one that reads: **0.23 g of vertical unloading at 314 km/h** as the
road drops away under the car at the top of the plunge, immediately before the doppler
station. The car goes visibly light, the camera dives with it, and 150 m later it is on the
brakes downhill for T12.

**The three features, and why each exists**

1. **LA RAMPE — +5.20 % over 180 m out of the hairpin.** The camera's rise into the
   helicopter arc has to be *motivated by terrain*, and 180 m of 1-in-19 climbing away from a
   79.6 km/h hairpin at full throttle is the strongest single grade the 12 m budget will pay
   for. Zandvoort's Turn-1 exit and Portimão's climb are the reference.
2. **LE BASCULEMENT + LA PLONGÉE — a 0.23 g crest into −4.45 % over 160 m.** Gives the
   descent that both judges asked for, makes the T12 stop downhill, tilts the doppler
   straight so the hovering camera looks slightly *down the barrel* of the approach, and
   drops the car 7.1 m in the 160 m before it brakes.
3. **THE FALL INTO THE HAIRPIN — −1.63 % over 150 m.** Small in gradient, large in meaning:
   the plateau *ends*, and the car falls off its edge into the hairpin bowl at 296 km/h.

Everything else is within 0.4 % of flat. **The pit straight is exactly z = 0.000 from
s = 3175 through s = 470** (the last 60 m of the climb out of T15 eases onto it), which is
what makes the showroom floor, the paddock apron, the access road and the racing surface a
single continuous plane.

**Terrain, not road, carries the rest of the relief** (grafted from A's landform method, and
the fix for D's admitted weakness #3):

| landform | extent (circuit frame) | shape |
|---|---|---|
| **the plateau** | x −620…+300, y −120…+140 | flat at z 0; the pit straight, paddock, showroom and pit complex all sit on it |
| **the north-east escarpment** | beyond T4, x +300…+520, y +680…+1000 | ground **falls at −8 % from the edge of T4's gravel trap to −9.5 m at 120 m out**, so a camera on the inside kerb of the hairpin sees the car silhouetted against distant falling ground and sky, not against tarmac |
| **the ridge** | x −380…+260, y +400…+760 | rises with La Rampe and carries the esses; infield banked to +11 m behind T7/T8 so 8 m of road relief reads as 19 m of landscape |
| **the west hillside** | x −960…−560, y +80…+400 | falls away west of the sweeper and the doppler straight, dropping to −12 m at the world edge, so the camera diving off the summit has real ground falling under it |
| **the return hollow** | x −620…−240, y −260…−80 | T12/T13 sit 3.7 m below the plateau in a shallow bowl |

---

## 6. CENTRELINE — ELEMENT LIST (generative, authoritative)

Feed to a turtle integrator starting at circuit-frame `(0, 0)` heading `0°`. `+ang` = left.
`heading_w` is the world-frame bearing (circuit heading + 40°). Start points are given in
**world** metres.

| element | type | R (m) | ang (°) | length (m) | s start | world start (x, y) | heading_w (°) |
|---|:-:|---:|---:|---:|---:|---|---:|
| S0 pit straight, S/F → T1 | S | ∞ | — | 250.00 | 0.00 | (+329.40, +169.82) | 40.00 |
| **T1** | A | 100 | +62.0 | 108.21 | 250.00 | (+520.91, +330.52) | 40.00 |
| S1 T1–T2 link | S | ∞ | — | 40.00 | 358.21 | (+554.44, +427.91) | 102.00 |
| **T2** | A | 110 | +30.0 | 57.60 | 398.21 | (+546.13, +467.04) | 102.00 |
| S2 east chute | S | ∞ | — | **265.046** | 455.81 | (+520.28, +517.77) | 132.00 |
| **T3** | A | 140 | −28.0 | 68.42 | 720.85 | (+342.93, +714.74) | 132.00 |
| S3 hairpin approach | S | ∞ | — | 150.00 | 789.27 | (+311.13, +774.55) | 104.00 |
| **T4 LE PIN** | A | 28 | +176.0 | 86.01 | 939.27 | (+274.84, +920.09) | 104.00 |
| S4 La Rampe | S | ∞ | — | 175.00 | 1025.28 | (+220.09, +908.46) | 280.00 |
| **T5** | A | 75 | −88.0 | 115.19 | 1200.28 | (+250.48, +736.12) | 280.00 |
| S5 climb straight | S | ∞ | — | 230.00 | 1315.47 | (+192.22, +649.73) | 192.00 |
| **T6** | A | 88 | +38.0 | 58.36 | 1545.47 | (−32.76, +601.91) | 192.00 |
| S6 esse link a | S | ∞ | — | 42.00 | 1603.83 | (−81.87, +572.40) | 230.00 |
| **T7** | A | 82 | −44.0 | 62.97 | 1645.83 | (−108.87, +540.23) | 230.00 |
| S7 esse link b | S | ∞ | — | 40.00 | 1708.81 | (−163.12, +511.38) | 186.00 |
| **T8** | A | 76 | +46.0 | 61.02 | 1748.81 | (−202.90, +507.20) | 186.00 |
| S8 esse link c | S | ∞ | — | 45.00 | 1809.82 | (−254.84, +478.41) | 232.00 |
| **T9** | A | 94 | −30.0 | 49.22 | 1854.82 | (−282.55, +442.95) | 232.00 |
| S9 summit run | S | ∞ | — | **238.765** | 1904.04 | (−321.41, +413.67) | 202.00 |
| **T10** | A | 125 | +44.0 | 95.99 | 2142.81 | (−542.79, +324.22) | 202.00 |
| T10b release | A | 400 | +8.0 | 55.85 | 2238.80 | (−610.15, +259.17) | 246.00 |
| **T11** | A | 150 | +41.4 | 108.38 | 2294.65 | (−629.24, +206.73) | 254.00 |
| S11 doppler straight | S | ∞ | — | **297.605** | 2403.03 | (−620.55, +101.04) | 295.40 |
| **T12** | A | 50 | +52.0 | 45.38 | 2700.64 | (−492.90, −167.80) | 295.40 |
| S12 T12–T13 link | S | ∞ | — | 55.00 | 2746.02 | (−458.64, −195.14) | 347.40 |
| **T13** | A | 70 | +22.0 | 26.88 | 2801.02 | (−404.96, −207.14) | 347.40 |
| S13 T13–T14 link | S | ∞ | — | 70.00 | 2827.90 | (−378.26, −207.89) | 9.40 |
| **T14** | A | 90 | −19.4 | 30.47 | 2897.90 | (−309.20, −196.46) | 9.40 |
| S14 T14–T15 link | S | ∞ | — | 95.00 | 2928.37 | (−278.87, −196.61) | 350.00 |
| **T15** | A | 105 | +50.0 | 91.63 | 3023.37 | (−185.31, −213.11) | 350.00 |
| S15 pit straight, T15 → S/F | S | ∞ | — | 560.00 | 3115.00 | (−99.59, −190.14) | 40.00 |

**Bold lengths are the three free variables** in the closure solve (S2, S9, S11). Three
unknowns against three constraints (end-x, end-y, total length = 3 675.0 m) is a square
system, so the solution is unique — there is no hidden slack. Newton solve converges to a
residual of **(0.0, 4.9 × 10⁻¹⁵) m**.

### 6.1 Clothoid transitions

The element list is straights and constant-radius arcs because that is the language the
geometry is *designed* in. **Insert Euler-spiral transitions at every straight↔arc junction**
using `L_c = 0.55·R` for `R ≤ 100 m` and `0.40·R` above, `A = √(R·L_c)`, absorbed by
shortening the constant-radius portion so total length and closure are unchanged to within
0.3 m. Without them the steering trace steps at every turn-in and the chassis roll channel
will snap at 4K.

| R (m) | L_c (m) | A | R (m) | L_c (m) | A |
|---:|---:|---:|---:|---:|---:|
| 28 | 15.40 | 20.77 | 100 | 55.00 | 74.16 |
| 50 | 27.50 | 37.08 | 105 | 42.00 | 66.41 |
| 70 | 38.50 | 51.91 | 110 | 44.00 | 69.57 |
| 75 | 41.25 | 55.62 | 125 | 50.00 | 79.06 |
| 76 | 41.80 | 56.36 | 140 | 56.00 | 88.54 |
| 82 | 45.10 | 60.81 | 150 | 60.00 | 94.87 |
| 88 | 48.40 | 65.26 | 400 | 160.00 | 252.98 |
| 90 | 49.50 | 66.75 | 94 | 51.70 | 69.71 |

Where two arcs meet directly (T10 → T10b → T11), use an **egg-clothoid** between the two
radii rather than a spiral to infinity: `L_c = 0.40·(R₁·R₂)/(R₂−R₁)` clamped to 40 m.

### 6.2 Blender import

Drop §7's points into a **`POLY` spline, cyclic**, and delete the duplicate closing point
(index 201 is identical to index 0). Sweep the surface with geometry nodes from an
`s`-parameterised width curve per §8 — **do not** model the width by hand. Evaluate the
clothoids of §6.1 as a subdivision pass on the poly spline, **not** by moving control points:
the closure and the length are solved for the arc/straight definition, and hand-nudging a
control point breaks both silently.

---

## 7. LENGTH AND LAP TIME — HOW 63.54 s WAS DERIVED

Length was **constrained** to 3 675.0 m in the closure solve; the lap time then **fell out**
of a physics model. If the model had returned 70 s the circuit would have been shortened.

**Vehicle model.** `m = 830 kg` (measured car + driver + fuel).

| term | expression | source |
|---|---|---|
| lateral capacity | `a_lat(v) = min(15.0 + 0.0050·v², 48.0)` m/s² | D — independently verified by the authenticity judge to reproduce every published apex speed |
| traction limit | `a_trac(v) = min(11.0 + 0.0022·v², 20.0)` m/s² | **corrected** (D's flat 16.0 m/s² cap gave 0–100 in 2.05 s, ~20 % optimistic) |
| power | `a_pow(v) = 800/v` m/s² = 664 kW at the wheels | D |
| drag | `a_drag(v) = 0.00092·v²` m/s² | D |
| **braking** | `a_brk(v) = min(1.25 + 2.2·10⁻⁴·v², 5.0)·g` **plus drag** | **grafted from A** |
| gradient | `−g·dz/ds`, applied to accel and braking alike | both |
| surface μ | 1.00 circuit, 0.90 unrubbered access road, 0.85 showroom floor | grafted from C |

Corner speed solves `v² = a_lat(v)·R` iteratively. Sanity: R = 137 m returns 292 km/h, which
is Copse at Silverstone (R ≈ 150 m, ≈ 290 km/h). The corrected traction model gives
**0–100 km/h in 2.35 s** and terminal velocity 343 km/h, against a real car's ≈ 2.6 s.

**Solve.** Forward pass (traction/power limited) and backward pass (brake limited) over a
0.25 m station grid, clamped to the cornering ceiling, iterated cyclically to convergence.
`t = Σ ds / v̄`.

**Result: 63.545 s, 208.2 km/h average.** Sectors 22.09 / 21.75 / 19.71 s.

Adopting A's braking curve cost **+1.01 s** against D's published 62.54 s, and that second is
the price of a braking table that is consistent with its own solver. It is worth paying: D's
model needed **66 m** to go 331 → 197 km/h, which no F1 car has ever done.

**Speed distribution**

| | by distance | by time |
|---|---:|---:|
| above 200 km/h | 65.2 % | 51.8 % |
| above 250 km/h | 43.8 % | 31.8 % |
| above 300 km/h | 15.1 % | 10.0 % |

That is a medium-downforce permanent circuit — Austria or Baku, not Monaco. The 810 m pit
straight alone is 22 % of the lap length.

**Reasonableness.** Red Bull Ring is 4 318 m in ~64 s (243 km/h average) with far more
full throttle; Interlagos is 4 309 m at 222 km/h; Zandvoort is 4 259 m at 219 km/h. A
3 675 m circuit with one 810 m straight, a true 176° hairpin, four corners below 155 km/h
and a peak lateral load of 4.89 g landing at 208 km/h average sits sensibly among them.

**This is a centreline time.** A real racing line — cutting apexes, straightening the esses,
carrying a wider radius through T10/T11 — is worth roughly 1.5–2.5 % on a layout of this
character, so a driven lap would be **≈ 62.0–62.6 s**. The telemetry owner must use the
centreline number and add the racing-line offset **explicitly**, not silently.

**On-screen Beat 5 is 63.70 s**, not 63.54 s, because the car crosses the line the first time
at 288.6 km/h (out lap) rather than 323.4 km/h (flying lap) and spends the first ~120 m of the
straight catching up to the steady-state profile. Use 63.70 s in the beat sheet.

---

## 8. CENTRELINE — CONTROL POINTS (world metres, x y z)

**202 points, ready for a Blender `POLY` curve.** Spacing is driven by a **0.12 m sagitta
tolerance** on every arc (`θ_max = 2·acos(1 − 0.12/R)`, capped at 12°) and 40 m on straights.
Measured against the analytic centreline the worst chord deviation is **0.123 m** — 1.8 % of
a 7 m track half-width — and that worst case is **inside the 176° hairpin itself** (s = 1013),
which is the corner the film photographs from kerb height, so the tightest geometry on the
circuit is also the best-resolved. Point 0 is the S/F line; **point 201 is identical to point 0**
— set the spline cyclic and delete it.

```
  idx        x         y      z    idx        x         y      z    idx        x         y      z
  0    329.40    169.82   0.00   68    250.72    711.49   5.67  136   -623.72    224.42   4.33
  1    356.78    192.80   0.00   69    249.00    703.43   5.83  137   -629.31    206.49   4.27
  2    384.17    215.78   0.00   70    246.40    695.61   5.96  138   -631.88    196.06   4.24
  3    411.55    238.76   0.00   71    242.97    688.12   6.06  139   -633.73    185.24   4.21
  4    438.75    261.58   0.00   72    238.87    681.26   6.11  140   -634.77    174.55   4.17
  5    466.14    284.56   0.00   73    233.90    674.68   6.14  141   -635.04    163.82   4.14
  6    493.52    307.54   0.00   74    228.25    668.69   6.17  142   -634.55    153.09   4.10
  7    520.91    330.52   0.00   75    221.96    663.35   6.20  143   -633.24    142.18   4.07
  8    527.53    336.60   0.00   76    215.14    658.74   6.23  144   -631.21    131.64   4.04
  9    533.58    343.26   0.00   77    207.84    654.90   6.26  145   -628.42    121.27   4.00
 10    539.01    350.43   0.00   78    200.17    651.89   6.29  146   -624.81    110.90   3.97
 11    543.77    358.06   0.00   79    192.22    649.73   6.32  147   -620.55    101.04   3.93
 12    547.82    366.09   0.00   80    154.80    641.78   6.45  148   -604.57     67.38   3.82
 13    551.14    374.45   0.00   81    117.14    633.77   6.59  149   -588.58     33.72   3.70
 14    553.75    383.31   0.00   82     79.73    625.82   6.72  150   -572.60      0.06   3.30
 15    555.50    392.14   0.00   83     42.31    617.87   6.86  151   -556.62    -33.60   2.49
 16    556.45    401.08   0.00   84      4.66    609.87   7.00  152   -540.74    -67.04   1.27
 17    556.59    410.07   0.00   85    -32.76    601.91   7.13  153   -524.76   -100.70  -0.32
 18    555.92    419.04   0.00   86    -40.75    599.82   7.16  154   -508.77   -134.36  -1.98
 19    554.44    427.91   0.00   87    -48.74    596.88   7.19  155   -492.79   -168.02  -3.19
 20    546.13    467.04   0.00   88    -56.19    593.31   7.22  156   -489.61   -173.66  -3.32
 21    543.75    476.25   0.00   89    -63.28    589.06   7.25  157   -485.73   -178.85  -3.43
 22    540.49    485.45   0.00   90    -69.93    584.15   7.28  158   -481.21   -183.49  -3.52
 23    536.54    494.11   0.00   91    -76.27    578.47   7.31  159   -476.33   -187.36  -3.59
 24    531.86    502.39  -0.00   92    -81.87    572.40   7.34  160   -470.78   -190.72  -3.63
 25    526.33    510.43  -0.00   93    -95.37    556.31   7.41  161   -464.85   -193.32  -3.65
 26    520.28    517.77  -0.01   94   -108.87    540.23   7.49  162   -458.64   -195.14  -3.66
 27    495.01    545.83  -0.05   95   -114.30    534.36   7.52  163   -431.80   -201.14  -3.64
 28    469.58    574.08  -0.13   96   -120.08    529.21   7.54  164   -404.96   -207.14  -3.51
 29    444.32    602.13  -0.21   97   -126.32    524.63   7.57  165   -398.34   -208.29  -3.46
 30    418.89    630.38  -0.29   98   -133.19    520.53   7.60  166   -391.65   -208.80  -3.41
 31    393.62    658.44  -0.37   99   -140.42    517.13   7.63  167   -384.93   -208.67  -3.35
 32    368.19    686.68  -0.45  100   -147.71    514.52   7.66  168   -378.26   -207.89  -3.28
 33    342.93    714.74  -0.53  101   -155.22    512.61   7.68  169   -343.73   -202.17  -2.89
 34    335.60    723.58  -0.56  102   -163.12    511.38   7.71  170   -309.20   -196.46  -2.48
 35    329.16    732.78  -0.58  103   -202.90    507.20   7.85  171   -301.76   -195.54  -2.40
 36    323.35    742.69  -0.61  104   -210.31    506.05   7.88  172   -294.28   -195.25  -2.31
 37    318.38    753.04  -0.65  105   -217.81    504.10   7.91  173   -286.55   -195.60  -2.22
 38    314.36    763.53  -0.71  106   -225.07    501.40   7.93  174   -279.12   -196.57  -2.14
 39    311.13    774.55  -0.79  107   -231.80    498.09   7.95  175   -247.85   -202.08  -1.78
 40    302.05    810.94  -1.18  108   -238.17    494.14   7.96  176   -216.83   -207.55  -1.42
 41    292.98    847.32  -1.75  109   -244.31    489.41   7.96  177   -185.56   -213.07  -1.05
 42    283.91    883.71  -2.36  110   -249.94    484.08   7.96  178   -176.41   -214.29  -0.95
 43    274.84    920.09  -2.86  111   -254.84    478.41   7.96  179   -167.43   -214.71  -0.84
 44    273.20    924.81  -2.91  112   -268.69    460.68   7.92  180   -158.20   -214.33  -0.74
 45    270.75    929.17  -2.96  113   -282.55    442.95   7.88  181   -149.05   -213.15  -0.63
 46    267.40    933.19  -3.01  114   -287.90    436.68   7.87  182   -140.03   -211.16  -0.54
 47    263.55    936.38  -3.05  115   -293.78    430.91   7.85  183   -131.45   -208.48  -0.45
 48    259.20    938.83  -3.09  116   -299.95    425.83   7.84  184   -122.91   -204.96  -0.37
 49    254.49    940.48  -3.13  117   -306.74    421.15   7.82  185   -114.71   -200.71  -0.29
 50    249.30    941.27  -3.17  118   -313.91    417.09   7.81  186   -107.12   -195.90  -0.23
 51    244.31    941.12  -3.20  119   -321.41    413.67   7.79  187    -99.78   -190.30  -0.17
 52    239.43    940.08  -3.23  120   -358.26    398.78   7.63  188    -69.14   -164.59  -0.02
 53    234.81    938.19  -3.25  121   -395.12    383.88   7.11  189    -38.50   -138.88   0.00
 54    230.39    935.36  -3.28  122   -432.21    368.90   6.33  190     -7.85   -113.17   0.00
 55    226.75    931.94  -3.30  123   -469.07    354.01   5.56  191     22.79    -87.46   0.00
 56    223.78    927.93  -3.31  124   -505.93    339.12   5.02  192     53.43    -61.74   0.00
 57    221.57    923.45  -3.31  125   -542.79    324.22   4.75  193     84.07    -36.03   0.00
 58    220.13    918.41  -3.29  126   -552.57    319.77   4.72  194    114.71    -10.32   0.00
 59    219.67    913.43  -3.25  127   -561.72    314.63   4.68  195    145.35     15.39   0.00
 60    220.09    908.46  -3.18  128   -570.60    308.59   4.65  196    176.00     41.10   0.00
 61    226.17    873.99  -2.08  129   -578.94    301.81   4.62  197    206.64     66.81   0.00
 62    232.25    839.52  -0.27  130   -586.49    294.52   4.58  198    237.28     92.53   0.00
 63    238.33    805.05   1.55  131   -593.56    286.42   4.55  199    267.92    118.24   0.00
 64    244.40    770.59   3.37  132   -599.91    277.75   4.52  200    298.56    143.95   0.00
 65    250.48    736.12   4.95  133   -605.36    268.79   4.48  201    329.40    169.82   0.00
 66    251.47    727.93   5.22  134   -610.15    259.17   4.45
 67    251.54    719.69   5.46  135   -617.39    241.83   4.39
```

Index map (verified against the element stations):

| element | cp range | element | cp range |
|---|---|---|---|
| S0 pit straight | 0–7 | S9 summit run | 119–125 |
| **T1** | 7–19 | **T10** | 125–134 |
| S1 link | 19–20 | T10b release | 134–137 |
| **T2** | 20–26 | **T11** | 137–147 |
| S2 east chute | 26–33 | S11 doppler straight | 147–155 |
| **T3** | 33–39 | **T12** | 155–162 |
| S3 hairpin approach | 39–43 | S12 link | 162–164 |
| **T4 hairpin** | **43–60** | **T13** | 164–168 |
| S4 La Rampe | 60–65 | S13 link | 168–170 |
| **T5** | 65–79 | **T14** | 170–174 |
| S5 climb straight | 79–85 | S14 link | 174–177 |
| **T6** | 85–92 | **T15** | 177–187 |
| S6/T7/S7 | 92–103 | S15 pit straight | 187–201 |
| **T8** | 103–111 | | |
| S8/T9 | 111–119 | | |

**Tangent / handle guidance.** The list is for a `POLY` spline; no handles are needed. If a
`NURBS` or `BEZIER` spline is preferred instead:

* On the four straights longer than 200 m (S0, S2, S5, S15) set handles **collinear with the
  segment** — any curvature there is a defect, and a 330 km/h onboard follow will show it.
* Through the hairpin (cp 43–60) the tangent direction at cp *k* is the average of the
  incoming and outgoing chord directions; handle length **R·tan(θ/2)·(4/3)/2 = 1.63 m** for
  the 10.6° spacing at R = 28. Do not let an auto-handle solver run here: the 176° of arc
  will bulge.
* At the three arc→arc junctions (T10→T10b→T11, cp 134 and 137) the tangent must be
  **continuous** — these are tangent-continuous by construction and any handle discontinuity
  will appear as a steering-trace step at 271 km/h.
* Everything else: auto/smooth handles are fine at this spacing.

---

## 9. TRACK SECTION, KERBS, RUNOFF — TO SCALE AGAINST THE MEASURED CAR

The car is **5.698 m long, 2.005 m wide, ride height 0.340 m** (measured,
`round2_inventory.md` §3). Everything below is sized against those numbers.

| section | racing surface | = car widths | two abreast leaves |
|---|---:|---:|---:|
| pit straight (S15 + S0) | **16.0 m** (±8.0) | 7.98 | 12.0 m |
| standard | **14.0 m** (±7.0) | 6.98 | 10.0 m |
| T4 hairpin (widened) | **15.0 m** (±7.5) | 7.48 | 11.0 m |
| esses T6–T9 (narrowed) | **13.0 m** (±6.5) | 6.48 | 9.0 m |
| access road / pit exit | **12.0 m** | 5.99 | — |

Width transitions are linear over 60 m so no seam is visible from the air.

**Kerbs — FIA-standard serrated, 1.50 m wide, two-tone red/white at 1.00 m alternation.**
50 mm proud at the outer lip, 25 mm at the track-side lip, **25 mm serration amplitude on a
250 mm pitch → 75 mm peak**. Against 340 mm of ride height that leaves **265 mm of plank
clearance**, so the car can use every kerb on the circuit without the floor touching.
*(This corrects D, which specified a 60 mm serration on a 50 mm kerb — internally
inconsistent — and "negative sausage kerbs, 100 mm", which is a contradiction in terms.)*

**Negative kerbs: −60 mm deep, 0.80 m wide, at the T8 apex and the T12 exit only.** These are
the two places the beat sheet wants visible suspension travel; 60 mm against a 340 mm ride
height is an 18 % extension event, big enough to read at 4K and small enough not to launch the
car. 1.0 m of green/white painted asphalt verge outboard of every kerb, then runoff.

**Runoff, budgeted by where the car actually leaves the road** (method grafted from A):

| location | speed at the limit | runoff |
|---|---:|---|
| T1, end of the 810 m straight | 331 km/h at the braking board | 45 m asphalt, then 12 m gravel, then TecPro |
| T3 Long Kink (4.89 g, the highest load on the lap) | 295 km/h | 40 m asphalt outside, 15 m gravel bed at the exit |
| **T4 LE PIN** | 296 km/h entry | **30 m gravel + three-layer TecPro**; beyond it the escarpment falls at −8 % |
| T5 exit, onto La Rampe | 153 km/h | 20 m grass |
| T8, off-camber summit crest | 154 km/h, car light | 25 m gravel + 20 m asphalt |
| **T10/T11 sweeper** | **294 km/h exit** | **55 m asphalt outside the whole complex**, then 15 m gravel |
| **T12 La Plongée** | 314 km/h downhill entry | **30 m gravel + three-layer TecPro** |
| T15 Gate, onto the pit straight | 207 km/h | 30 m asphalt |
| everywhere else | | 18–25 m of grass with a gravel bed on the apex side |

The T10/T11 figure is deliberately larger than D's 40 m: with the radii swapped the car now
*exits* the complex at 293.7 km/h rather than entering at 281.6, and 40 m of asphalt behind a
294 km/h sweeper is not FIA-viable. This is C's "engineered open zone" doctrine applied —
the runoff is stated as a design decision with a reason, not defaulted.

**Barriers.** Steel Armco plus 3.6 m debris fence on 6 m posts at 8 m centres, instanced,
standing 18–25 m from the track edge; three-layer TecPro at T4 and T12. On the pit straight
the south barrier is at circuit-frame `y = −19` (11 m of asphalt verge outboard of the 8 m
half-width) and the pit wall at `y = +11.5` (3.5 m from the track edge, standard).

**Start/finish gantry** at circuit-frame `x = 0`, world (329.40, 169.82): legs at `y = ±11.0`,
crossbeam soffit at **z = 9.00 m**, 2.2 m deep.

**Two hard thresholds** (grafted from C's Porte Saint-Elme, which cannot be transplanted
literally onto a parkland circuit but whose *function* can):

1. **La Passerelle** — spectator footbridge over the pit straight at circuit-frame
   `x = −450`, deck soffit **7.5 m**, 4.0 m deep, spanning `y = −24 … +28`. The onboard
   follow passes under it 1.3 s in at ~230 km/h. It also solves D's weakness #9: the camera
   crosses this same tarmac twice 63 s apart, and the two passes are now visually
   distinguishable by construction — the out lap goes under it wide and outboard, the flying
   lap tight and low.
2. **Le Pont de la Plongée** — infield service bridge over the track at **s = 2410**, soffit
   **6.80 m**, 30 m span, 6 m deck. The camera, descending out of the helicopter arc, threads
   under it at ~5 m altitude and 300 km/h, **145 m before the doppler hover station**, so the
   car bursts out from under a bridge straight into the doppler pass. It also gives the arc a
   hard target altitude instead of an unmotivated drift down.

---

## 10. SHOWROOM, PADDOCK, BREACH EXIT — AND THE BEAT-6 SIGHT LINE

### 10.1 The showroom is not moved. Anything.

Verified object-by-object against `docs/inventory_iter.json`:

| object | measured | consequence |
|---|---|---|
| `Floor` | 30.0 × 22.0 × 0.06, centred (0,0), **top Z = 0.000** | world datum |
| `GW_Right` | plane **X = +15.00**, 21.919 m of head/sill, outward normal **+X** | **the wall that gets breached** |
| `GW_Right_Glass_00…09` | **10 panels**, each 2.125 m × 5.98 m | pre-fracture unit |
| `GW_Right_Mull_00…10` | **11 mullions**, 0.075 × 0.16 × 6.20 m, at 2.20 m centres | **one sits exactly on the launch axis Y = 0** |
| `GW_Right_Transom_0…2`, `_Head`, `_Sill`, `_BaseReveal` | full-width | framing, must fracture too |
| `GW_Front` | plane **Y = −11.00**, 14 panels of 2.068 m, 15 mullions | the daylight source, **not** breached |
| `Wall_BackX` / `Wall_SideY` | X = −15.25 / Y = +11.25, 6.20 m | solid |
| `Ceiling` | 30.5 × 22.5 × 0.3 | clear head 6.20 m, slab top 6.50 m |
| `Platform_Dais` | 7.4 m diameter (r = 3.70) at the origin | |
| `Turntable_Deck` | 6.9 m, **top Z = +0.340** | **the plinth defect, see 10.3** |
| `ExteriorGround` | 320 × 320 × 0.06, **top Z ≈ −0.08 … −0.14** | **the lip defect, see 10.3** |
| lights | 23 lamps, **no SUN** | round 1 was a pure interior rig; the exterior daylight is entirely round 2's choice |

Because the circuit is expressed in the world frame defined by this building, the transform
applied to 76 `SHOWROOM` + 61 `LIGHTS` + 173 `PROPS` root objects and 617 `CAR` objects is
**the identity**. `world/beat1_audit.blend` and its 15 macro cameras stay valid. This is the
single highest-value graft taken from layout A and it costs one rotation constant in the
curve builder.

### 10.2 Exact placement

| item | world | circuit frame |
|---|---|---|
| showroom floor centre | **(0, 0, 0)** | (−350.00, +72.00) offset by the wall |
| **breach face centre** | **(15.000, 0.000, 3.100)** | (−350.00, +72.00) |
| **breach exit vector** | **(+1, 0, 0)** — due +X | bearing −40° to the racing direction |
| glass wall end points | (15, −10.96) and (15, +10.96) | |
| exterior pavilion footprint | 34 × 26 m, x −19…+15, y −13…+13; parapet z = +10.40 | |
| interior | 30.0 × 22.0 × 6.50 m ceiling — the inventory's volume, unchanged | |
| min distance building → track centreline | **63.65 m** | |
| min distance breach face → track centreline | **72.00 m** | |
| showroom → S/F line | 376.9 m, bearing 24.3° off the breach axis | |

The building is a glass-and-anodised manufacturer hospitality pavilion standing in the
paddock, west of the pit garages, its glazed end facing south-east across the pit-exit apron
with the circuit beyond it. Nothing about that needs explaining to an audience.

**Why the paddock side and not the south side** — D tested and rejected three placements, and
re-deriving them confirms all three failures:

1. *South of the pit straight, upstream, glass facing down-track.* At the crossing instant the
   car and the wall are 155.6° apart in bearing. Dead.
2. *Downstream of the line, glass facing back up-track.* The frame stacks perfectly and the
   exit vector then points **against** the racing direction, so the merge needs a hairpin on an
   access road. Rejected on Beat 4.
3. *South, with the closing camera swung far south-west.* 73° off the wall normal; the wound
   stops reading.

The fourth works because the camera **crosses the track** during Beat 6's peel-off and ends up
on the *far* side of the circuit from the showroom — which is the side the glass wall is
looking at.

### 10.3 Two round-1 defects that must be fixed before Beat 2 (both grafted from A)

**(a) The 340 mm plinth.** `Turntable_Deck` top is Z = +0.340 and `Floor` top is Z = 0.000.
Left alone the car drives off a 340 mm step and loses rolling contact for ~2 frames at the
most-watched moment in the film. **Fix:** a dais delivery ramp — **0.340 m rise over 2.60 m
(13.1 %), full 3.0 m width, from the dais lip X = +3.70 out to X = +6.30**, matching the floor
material. It is showroom-plausible furniture and it keeps the rolling-contact rule intact.

**(b) The exterior lip.** `ExteriorGround` already spans ±160 m and sits **80–140 mm BELOW**
the floor. Shards that skitter out through the hole would hit an 8–14 cm ledge at the wall
line and the rigid-body sim would argue with it for days. **Fix:** re-level `ExteriorGround`
to **exactly Z = 0.000** over world X 10…90, Y −40…+40 (the breach wedge and the whole apron
run), then blend to its existing height over a further 20 m. The **first 50 m outside the
glass is then exactly 0 % and exactly level with the interior floor**, so debris keeps
travelling on the plane it started on.

**(c) The breach wall is framed, not frameless.** D described "frameless structural glazing".
It is not. Pre-fracture must respect the real panelisation:

* cell-fracture each of the **10 glass panels separately**, seeded densely (small shards) at
  the impact panel and coarsely at the wall edges;
* the **11 aluminium mullions are separate rigid bodies** failing at their head and sill
  fixings, not shattering;
* **the mullion at Y = 0 is the first thing the nose hits** — the car splits it. That is the
  hero detail of Beat 3 and it is free;
* the head, sill, three transoms and base reveal are their own bodies; the head beam should
  sag and stay attached at one end;
* expected aperture after the pass-through: **9.6 m wide × 5.6 m tall** (four panels and three
  mullions gone, the mullions at Y = ±4.4 surviving as bent stubs), centred on
  world **(15, 0, 2.85)**, Y −4.8…+4.8, Z 0.11…5.71. This is the aperture used in every
  Beat-6 pixel budget below; if the sim produces a materially different hole, re-run §10.6.

### 10.4 The launch — a correction to D

D stated a "26 m indoor launch run" reaching 85–100 km/h at the glass. **That is wrong for the
geometry that exists.** The car assembles on the turntable at the origin; its nose is at
X = +3.020 and the glass plane is X = +15.000, so the run is **11.98 m**.

Solved with the corrected traction model, μ 0.85 on a showroom floor:

| phase | duration | distance | exit speed |
|---|---:|---:|---:|
| sanctioned wheelspin (10 frames @ 24 fps, 55 % of traction) | 0.417 s | 0.46 m | 7.8 km/h |
| hook-up, traction-limited | 1.359 s | 11.52 m | — |
| **nose meets glass** | **1.776 s total** | **11.98 m** | **53.8 km/h (14.94 m/s)** |

**53.8 km/h, not 85–100.** A 830 kg car at 14.94 m/s carries 93 kJ, which destroys a 6.2 m
structural glazing bay and its aluminium mullions comfortably; and the lower speed is *better*
for the shot, because the shard field stays in frame for the whole of Beat 3's arc. Tune the
rigid-body sim to the **built** telemetry, but design the pre-fracture for an impact in the
50–60 km/h band, not 85–100.

A short, brutal 12 m launch is also the right dramatic shape: there is no room for the shot to
become a drive.

### 10.5 Breach exit route (transit table, format grafted from C)

Every leg with from/to in world metres, length, grade and exit speed. Nothing is left to
interpretation.

| leg | geometry | from (x, y, z) | to (x, y, z) | length | grade | exit speed | Δt |
|---|---|---|---|---:|---:|---:|---:|
| 1 launch | straight, +X, inside | (0.00, 0.00, 0.00) | (15.00, 0.00, 0.00) | 11.98 m | 0.00 % | 53.8 km/h | 1.78 s |
| 2 apron run | straight, +X, **unrubbered concrete, μ 0.90** | (15.00, 0.00, 0.00) | (64.60, 0.00, 0.00) | 49.60 m | **0.00 %** | 129.0 km/h | 1.97 s |
| 3 merge arc | **R = 150 m, 40.0° left**, centre (64.60, 150.00) | (64.60, 0.00, 0.00) | (161.02, 35.09, 0.00) | 104.70 m | 0.00 % | 219.5 km/h | 2.16 s |
| 4 blend + run to the line | pit straight, full grip | (161.02, 35.09, 0.00) | **(329.40, 169.82, 0.00)** | 215.60 m | 0.00 % | **288.6 km/h** | 3.00 s |
| — | **total glass → line** | | | **369.9 m** | | | **7.13 s** |

* The merge arc ends **5.02 m to the left of the centreline** — it joins the 16 m-wide pit
  straight inside the track edge and blends the last 5 m laterally over 90 m with a solid
  white blend line. That is what a pit exit is.
* R = 150 m supports 306 km/h; the car is doing 219.5 km/h at the blend point, so the curve is
  nowhere near limiting. No understeer, no camera-breaking scrub.
* The route crosses the pit-wall line (circuit `y = +13`) at circuit `x = −263.8`, so **the pit
  wall and the garage row start at circuit x = −245** and everything west of that is open
  pit-exit apron. There is no gate to cut and no barrier to remove.
* **Grade is zero on every leg**, by design (§2, §5). The apron, the road and the racing
  surface are one plane at z = 0.000.
* **Walls, not grade** (reduced graft from C's canyon): the middle 90 m of the apron run
  carries a **2.4 m cut-faced concrete retaining wall on the north side at 8.0 m offset** and
  a 2.0 m tyre-stack + debris-fence wall on the south at 7.0 m, with a pit-exit gate portal at
  world x = +58. The camera flies a walled corridor at rooftop height and then bursts into the
  open as the merge arc swings left and the whole circuit appears. That buys most of what C's
  −4.15 % canyon bought, without a 9 m escarpment and without moving the round-1 shell.

**Beat 4 is 5.6 s of world time**, not 7.13 s, because the first ~30 m past the glass is
consumed by Beat 3's speed ramp. That is longer than D's 6.5 s claim measured the same way,
and the extra second comes from the corrected (slower) launch.

### 10.6 THE BEAT-6 SIGHT LINE — SOLVED, AND ONE OF D's KEYS CORRECTED

**Requirement.** One frame must contain the circuit, the car streaking on, and the breached
showroom with its wound, held for ~3 s.

**The constraint that decides everything.** The camera arrives from the onboard follow at
**83.1 m/s heading down the pit straight**. Every candidate closing station is therefore
constrained not by taste but by dynamics. The minimum forward travel needed to stop from
83.1 m/s at 1.2 g is **292 m**. Any station requiring less forward advance than that is
unreachable at any acceleration a camera can plausibly carry. This is what kills the
"hold the frame closer / further west" graft (§12).

**Solution — a minimum-energy cubic from the peel-off to a full stop, verified frame by
frame.** Boundary conditions: at `t = −3.0 s` the camera is on the centreline behind the car
at circuit (−260.5, 0, 2.8) doing 83.1 m/s; at `t = +8.0 s` it is at rest at the hold station.
Peak acceleration **19.9 m/s² (2.03 g) at the peel-off**, easing monotonically thereafter.

| t (s) | camera, world (x, y, z) | lens | speed | what is in frame |
|---:|---|---:|---:|---|
| −3.0 | (129.84, +2.37, 2.8) | 32 mm | 83.1 m/s | onboard follow, car 29 m ahead at 299 km/h |
| −1.0 | (255.52, +75.07, 14.8) | 28 mm | 65.8 | camera crosses the south track edge, begins to rise |
| **0.0** | **(315.63, +89.61, 27.8)** | **24 mm** | 61.1 | **car crosses the line 86 m away at 323.4 km/h, 439 px long, under the gantry**; camera clears the 14 m grandstand roof by 13.8 m |
| +2.0 | (425.14, +87.77, 62.1) | 21 mm | 54.2 | pit straight sweeping through frame, camera yawing left |
| +4.0 | (513.55, +61.43, 98.8) | 19.5 mm | 44.3 | paddock and pit complex; **the wound enters frame ≈ here** |
| +6.0 | (572.69, +30.78, 128.0) | 18.75 mm | 27.0 | wide opening out, camera almost stopped |
| **+8.0** | **(594.19, +16.05, 140.0)** | **18.75 mm** | **0.0** | **HOLD BEGINS** |
| +9.5 | *hold* | 18.75 mm | 0 | |
| **+11.0** | *hold* | 18.75 mm | 0 | **HOLD ENDS. Beat 6 = 11.0 s from the line.** |

**The held frame, verified at three instants** (18.75 mm on a 36 mm sensor = 87.7° horizontal
FOV; pixel widths include rectilinear edge stretch, which is how the frame actually renders):

| | t = +8.0 | t = +9.5 | t = +11.0 |
|---|---:|---:|---:|
| car distance | 601 m | 701 m | 815 m |
| car speed | 257 km/h | 286 km/h | **295 km/h** |
| car on screen | 30 px | 25 px | 21 px |
| **showroom facade** | **119 px** | **113 px** | **109 px** |
| **breach aperture** | **52 px** | **49 px** | **48 px** |
| showroom distance | 595 m | 595 m | 595 m |
| angular separation car ↔ wound | 75.8° | 71.8° | 69.5° |
| worst subject position | 82 % of half-frame | 79 % | 77 % |
| grandstand ray clearance to the wound | **+29.4 m** | +29.4 m | +29.4 m |

**Against D's published hold** (26 mm at 617 m): facade 92 px naive / ~126 px with edge
stretch, aperture 40 px naive / ~55 px, subjects at 89 % of half-frame. This spec is
comparable on facade size, **20 % better on the wound**, and materially better on composition
— the hero subjects are no longer jammed into the last 11 % of the frame where rectilinear
stretch is worst.

**Occlusion, verified as ray crossings and not asserted.** Grandstands occupy circuit-frame
`y = −34 … −62`, `x = −420 … +180`, 14 m high. At the hold the camera→wound ray passes
**29.4 m above** the grandstand roofline; the camera→car ray passes 57–83 m above it. The
camera→wound ray crosses the pit wall (`y = +11.5`) and both garage bands (`y = +23.5`,
`y = +40.5`) at circuit `x ≈ −344 … −347`, i.e. **100 m west of the garage row**, which starts
at `x = −245`. Nothing occludes.

**A defect found in D and fixed here.** D's published `t = 0` key at circuit (−40, −150, 55)
is **occluded by D's own grandstands**: the ray from that station to the car at the line
crosses the grandstand front face (`y = −30`, 14 m tall) at **z = 11.5 m** — blocked by 2.5 m.
D never ran the check. The key above sits at circuit (−62.1, −52.6, **27.8**), which clears
the same roofline by 13.8 m.

**A dependency, flagged and not hidden.** At 595 m the wound is 48–52 px. That reads *only*
because the room behind it is lit and the aperture glows. **The showroom spot rigs must stay
on for the entire film** — write it into the lighting brief, not just the beat sheet.
Three things carry the wound at that distance and none of them is the hole itself:

1. **the shard fan** — 40+ m of glass debris on the apron in front of the wall, catching the
   low sun; at 595 m and 3.5 px/m that is a **140 px glitter band**, three times the size of
   the hole;
2. **the dust column** — a slowly-drifting 20–25 m haze above the building, still settling
   90 s after the breach;
3. **raking light on the facade** — with the sun at 58° incidence the mullions cast hard
   shadows across the glass and the breach reads as a dark, deep notch rather than a flat
   patch.

**A scripted gate, not a note** (process point grafted from C). Before Beat 6 renders, run a
raycast from the hold station to the wound and to the car against the full dressed scene, and
fail the build if either ray is obstructed or if the facade drops below 100 px. It is a
five-line check and it protects the last image of the film from a late-added lighting mast.

### 10.7 Paddock and pit complex (circuit frame; apply §2's transform to place)

| element | extent | height |
|---|---|---|
| pit wall | y = +11.5, x = −245 … +130 | 1.2 m |
| pit lane | y = +11.5 … +23.5 (12.0 m), x = −245 … +130 | — |
| pit garages | y = +23.5 … +40.5, x = −245 … +75, 14 bays at 22 m | roof z = +12.0 |
| paddock | y = +40.5 … +115, x = −480 … +100 | trucks, awnings, tyre stacks, fencing |
| **showroom** | x = −380.5 … −342.9, y = +63.6 … +100.1 | parapet z = +10.4 |
| **pit-exit apron** (declared surface, unrubbered concrete) | x = −480 … −245, y = 0 … +45 | z = 0 |
| grandstands | y = −34 … −62, x = −420 … +180 | 14.0 m |
| S/F gantry | x = 0, legs y = ±11.0 | soffit z = +9.0 |
| La Passerelle footbridge | x = −450, y = −24 … +28 | soffit z = +7.5 |

*(The apron is declared as a surface with extents because D's route crossed 32 m of its own
"paddock dressing zone" with no surface named — a real, if small, buildability gap.)*

**Three named empty zones** (doctrine grafted from C), so camera standoff is a design decision
rather than a late render-cost surprise:

| zone | extent (circuit frame) | rule |
|---|---|---|
| **the infield bowl** | x −340 … +160, y +180 … +420 | nothing above 4 m; this is the volume the helicopter arc orbits through above the esses |
| **the west outfield** | x −1010 … −860, y +150 … +560 | nothing above 3 m within 60 m of the doppler straight's outside edge; protects the doppler sight line both ways |
| **the south apron** | y −62 … −340, x −120 … +260 | nothing above 4 m; this is the volume the Beat-6 crane-out flies through and the ground under the held frame |

---

## 11. CAMERA NOTE PER BEAT — WHAT THIS LAYOUT GIVES THAT ANOTHER WOULD NOT

### Beat 1 — assembly, inside the showroom (33.0 s)

The layout's contribution is the **sun**, which is a free choice because round 1 has no SUN
lamp at all (23 lamps, all interior spots and areas). Specified here so that Beat 1 and the
circuit share one physical light:

> **Sun: direction-to-sun (+0.518, −0.828, +0.216) in world; horizontal bearing −58.0°;
> elevation 12.5°; shadows 4.51 × object height running toward (−0.518, +0.828).**

That angle does four jobs at once:

* it enters **`GW_Front`** (the 30 m south glazing, normal −Y) at **34° off normal** — a huge
  soft raking rectangle across the turntable, so the 9.84 × 4.49 × 5.96 m exploded field is
  lit by one motivated source and every one of the 15 clusters gets rim separation;
* it enters **`GW_Right`** (the breach wall, normal +X) at **58° off normal** — bright enough
  to be a luminous backdrop the camera can compose the field against, oblique enough not to be
  a blown-out rectangle that swallows edge detail;
* the mullion shadows rake 4.5 × across the floor, giving the drifting camera a moving graphic
  that reads the room's depth without any added practicals;
* and on the circuit it is **98° to the right of the racing direction** — near-perfect
  cross-light for long shadows across the tarmac on the pit straight.

*What another layout does not give:* the breach wall faces the pit-exit apron with the circuit
beyond it, so **the exploded field is backlit by the place the car is about to go**. A showroom
placed behind the pits, or facing away from the track, makes Beat 1 an interior with no
exterior — and then Beat 3's breach reveals nothing the audience has been anticipating for
33 seconds.

### Beat 2 — ignition and launch (3.0 s)

The launch axis is world +X, dead straight, 11.98 m nose-to-glass, with the dais delivery ramp
(§10.3a) taking the car off the 340 mm plinth without breaking rolling contact. The camera
settles low behind the left rear at z = 0.55, 6 m back, looking down the launch axis at the
glass — which frames the pit-exit apron and, 370 m beyond it, the pit straight.

*What this layout gives:* **the target of the launch is visible through the target of the
launch.** And 12 m is a short, violent run — 1.78 s from standstill to impact. A longer run
would turn a launch into a commute.

### Beat 3 — the breach (8.0 s screen, ~1.6 s world)

The wall normal is **40° oblique to the racing direction**. That is deliberate: the camera arcs
around the erupting shard field while world-time is at 15–25 %, and because the exit vector is
oblique to the track, the arc can carry the camera from *inside* the room to *outside* it while
continuously holding both the car and the hole. A wall facing straight down the straight would
force the arc to be a pull-back, which reads as retreat.

Three things this spec adds that D did not have:

* the **first 50 m outside the glass is exactly 0 % and exactly level with the interior floor**
  (§10.3b) — shards that skitter out keep travelling on the plane they started on, and the sim
  has no ledge to argue with;
* the wall is **framed, not frameless** (§10.3c) — the centre mullion at Y = 0 is what the nose
  splits, and eleven aluminium mullions failing at their fixings give the shatter cloud a
  structural spine that pure glass cannot;
* the breach is **63.6 m from the racing surface**, so the outbound shard field lands on
  dressed paddock concrete, not tarmac — a different skitter sound and a different specular
  response, and the same debris is still there in Beat 6, 90 s later, as a 140 px glitter band.

### Beat 4 — transit (5.6 s)

369.9 m of route with **four real thresholds in five and a half seconds**: the breach plane,
the walled apron corridor with its pit-exit portal at world x = +58, the pit-wall line, and the
blend line onto the racing surface. The camera pulls back and up into chase across all four
while the exposure animates from interior spill to full daylight.

*What another layout does not give:* a showroom that opened directly onto the racing surface
would have no thresholds at all and the transit would be a five-second nothing. And because
the merge is a genuine pit-exit blend at 219.5 km/h onto a 306 km/h-capable curve, the car
looks planted crossing the apron instead of negotiating a corner.

### Beat 5 — the lap (63.7 s)

| phase | stations | duration | what the geometry provides |
|---|---|---:|---|
| chase, T1–T3 | s 0 → 760 | **10.7 s** | **166 m of continuous linked-left arc** (T1 + T2, 62° + 30°) so the chase can slide from dead astern to outboard-alongside **without the car ever changing apparent direction**; then 265 m of straight to hold it; then T3 at 295 km/h and 4.89 g to hand the car away |
| kerb-height hairpin pass | s 760 → 1160 | **10.6 s** | 143.8 m of **downhill** braking, 296 → 80 km/h, then **176° of yaw at ≤ 85 km/h in 3.9 s** in front of a static camera on the inside kerb at z = 0.85 |
| rise + helicopter arc | s 1160 → 1910 | **14.6 s** | **180 m at +5.20 %** to climb with the car, then 358 m of alternating direction on the summit shelf, T8 off-camber at +7.95 m |
| dive to the sweeper | s 1910 → 2403 | **7.0 s** | 238.8 m of summit run cresting at −2.00 %, then 260 m of 93.4° left with the radius **opening** 125 → 400 → 150 and the car **accelerating** 255 → 294 km/h |
| threshold + doppler hover | s 2403 → 2700 | **4.4 s** | Le Pont de la Plongée at s = 2410, then Le Basculement (0.23 g of vertical unloading at 314 km/h), then the hover |
| whip and catch | s 2700 → 3115 | **7.0 s** | car covers 415 m through four corners while the camera cuts the chord |
| onboard follow | s 3115 → 3675 | **7.1 s** | 560 m, 207 → 323 km/h, dead straight, dead flat, under La Passerelle |

**The kerb-height hairpin pass.** 176° is the whole point. A camera parked on the inside kerb
at 0.85 m watches the car yaw through 176° in front of it: front three-quarter → profile →
rear three-quarter → profile → front three-quarter. No other corner geometry delivers a full
profile-to-profile reveal from a *static* camera, and 80 km/h is slow enough for a 21 mm lens
4 m from the tyre wall to stay legible at a 180° shutter. **And the background falls away** —
the escarpment beyond T4's gravel drops 9.5 m over 120 m (§5), so the car is silhouetted
against distant terrain and sky rather than against a tyre wall. That silhouette is grafted
from A; implementing it in the *terrain* rather than in the track's z is what let the downhill
braking survive alongside it.

**The doppler pass, specified.** Hover station **s = 2555**, camera at circuit
**(−835.4, +417.3, +4.80)** = world **(−578.82, −47.47, +4.80)** — 26.0 m outboard of the
centreline and 2.40 m above the local grade, on the outside of the descending doppler straight.
The camera pans; it does not translate.

| car relative to the station | speed | time | slant range | radial velocity | f′/f |
|---:|---:|---:|---:|---:|---:|
| −220 m (approaching) | 280.9 km/h | −2.65 s | 221.5 m | −75.3 m/s | **1.281** |
| −160 m | 292.3 | −1.90 | 162.2 | −80.7 | **1.308** |
| −100 m | 301.4 | −1.17 | 103.4 | −81.0 | **1.309** |
| −50 m | 307.7 | −0.58 | 56.4 | −75.8 | 1.284 |
| **0 m** | **313.2 km/h** | **0.00** | **26.1 m** | +0.2 | 0.999 |
| +50 m (braking) | 251.6 | +0.63 | 56.5 | +62.1 | **0.847** |
| +100 m | 182.7 | +1.47 | 103.5 | +49.2 | 0.875 |
| +160 m | 113.8 | +3.04 | 162.5 | +31.4 | 0.916 |

**Sweep 1.309 → 0.847 = 7.55 semitones**, and it falls out of the geometry with no
special-casing because the spatialisation maths is always on. The car is within ±220 m of the
station for **7.46 s**, so a ≥ 3 s near-hover has 2.5 × the margin the brief asks for. The
braking zone begins at **s = 2561**, i.e. **6 m past the station**, so picture and audio peak
on the same frame and the departing half of the pass has glowing discs, a squatting rear axle
and downshift blips. The road is falling at **−2.82 %** through the station and steepening to −4.45 % just beyond
it, so the hovering camera looks down the barrel of the approach: across the 140 m before the
station the road tips from −0.30 % to −4.45 % (Le Basculement), dropping 1.3 m, so the car
does not run level at the lens — it noses over and comes down at it.

**The catch-up, which is the hardest continuity problem in the film.** From the hover the
camera must re-acquire a car it just let go, and be tucked into the onboard follow by
s = 3115. The car covers **560 m in 11.36 s**; the camera flies a **485 m chord**, a
**chord/path ratio of 0.866** and a mean of **42.7 m/s (154 km/h)**, peaking near 68 m/s
(245 km/h) mid-flight before matching the car's 57.6 m/s at the pick-up. It is won by cutting
the corner the car has to drive around — honest physics, not a cheat.

**A named, costed fallback** (discipline grafted from C, and a decision rather than a
footnote): if the peak reads as too fast in previz, move the hover to **s = 2600**. Chord
drops to 454 m over 10.80 s (mean 42.1 m/s, peak ~66 m/s), the doppler sweep falls from 7.55
to about 6.6 semitones, and the slant range at closest approach grows to 31 m. **Primary is
s = 2555; the fallback is s = 2600; do not improvise a third.**

### Beat 6 — the ending (11.0 s)

Fully solved in §10.6. The three things to say here that are not in that table:

1. **The camera crosses the racing surface during the peel-off** — it is on the centreline
   behind the car at t = −3.0 and 55 m south of it by t = 0. That crossing is what makes the
   composition possible, and it is the last threshold the camera passes, bookending the glass
   wall it went through 90 seconds earlier.
2. **The wound is not in the frame at the crossing, and that is the design.** At t = 0 the
   separation between the car and the wall is 113° — no rectilinear lens holds both. So the
   crossing is a hero frame of the car alone (439 px, under the gantry, at 323.4 km/h), and
   then, as the camera rises and yaws left over the next six seconds, the pit straight, the
   paddock and finally the wounded building **arrive in frame**. The world unrolls between the
   two things that bracket the film.
3. **The held frame, left to right:** the showroom with its wound and its glitter fan at 35°
   frame-left, 595 m out; the whole 810 m pit straight receding; the finish gantry at 21° frame
   right; and beyond it, at 600–815 m, the car streaking north up the east chute at
   257 → 295 km/h. On the skyline behind everything, the esses at +8 m and the summit. The
   wound and the lap in one frame with the entire circuit between them.

---

## 12. WHAT WAS GRAFTED, WHAT WAS REJECTED, AND WHERE THE JUDGES DISAGREED

D_camera won on all three axes (8.5 / 8.5 / 8.5) and is the base. Fifteen grafts were taken;
six were rejected. Everything below is a decision, with the arithmetic that produced it.

### 12.1 Grafts ACCEPTED

| # | from | graft | why it survived |
|---|:-:|---|---|
| 1 | **A** | **Re-datum the world so the round-1 showroom lands unmoved at the origin** | Verified against `inventory_iter.json`: `Floor` top Z = 0.000, `GW_Right` at X = +15 with outward normal +X, nose points +X. D wanted the building at circuit (−350, +72) rotated −40°, which means transforming 310 unparented roots + 617 car objects and re-validating `world/beat1_audit.blend`'s 15 macro cameras. Rotating the *circuit* instead costs one constant in the curve builder (§2). Highest value-to-cost ratio of any graft. |
| 2 | **A** | **The dais delivery ramp** | Real defect, missed by C and D: `Turntable_Deck` top 0.340 vs `Floor` top 0.000. Fixed at §10.3a. |
| 3 | **A** | **Correct the breach-wall description before Beat 3 is scoped** | The wall is 10 glass panels of 2.125 m, 11 mullions at 2.20 m centres, 3 transoms, head, sill, base reveal — not "frameless structural glazing". Pre-fracture now follows the real panelisation, and the mullion at Y = 0 is what the nose splits (§10.3c). |
| 4 | **A** | **The Beat-3 flat-plane argument** | The whole breach corridor and the pit straight are at exactly z = 0.000 (§2, §5). Removes a class of sim iteration. Also surfaced a defect nobody flagged: round-1's `ExteriorGround` already sits 80–140 mm *below* the floor and must be re-levelled (§10.3b). |
| 5 | **A** | **Replace D's braking model** | D's curve gave 331 → 197 km/h in 66 m, ~30 % shorter than any real F1 car, and disagreed with D's own published table. A's `min(1.25 + 2.2e-4·v², 5.0)g + drag` returns 93.8 m for that stop and 143.8 m for 296 → 80. Cost: +1.01 s of lap time (62.54 → 63.55). All four braking zones now fall out of the published model (§4, §7). |
| 6 | **A** | **Landform-first, concentrated elevation, carried by terrain** | Three named grade features and five named landforms; the rest genuinely flat. Replaced D's PCHIP-through-keys with explicit tangent grades + parabolic vertical curves, so the max gradient is a design value (+5.20 %) rather than an artefact — which is the direct fix for the authenticity judge's finding that D's headline +3.97 % was really +3.11 % (§5). |
| 7 | **A** | **Per-corner runoff budgeted by where the car leaves the road** | §9, extended with C's "state the reason" doctrine, which is what forced the T10/T11 runoff from 40 m to 55 m. |
| 8 | **A** | **Site the hairpin so the background falls away** | Taken as **terrain**, not as track elevation: the ground beyond T4's gravel falls at −8 % to −9.5 m at 120 m out. This resolves the judges' disagreement (below) — D's downhill braking into the hairpin is kept *and* the kerb-height camera gets its silhouette. |
| 9 | **C** | **Increasing-radius double apex** | T10/T11 swapped to R125 → R400 → R150; the car now accelerates 254.6 → 271.3 → 293.7 km/h through it. Verified nearly free: S9 +13.9 m, S11 −8.8 m, total length and every downstream corner position unchanged (§4). |
| 10 | **C** | **Concentrate the elevation into short, punchy features** | +5.20 % over 180 m and −4.45 % over 160 m, versus D's 11 m smeared at ≤1.15 % over 90 % of the lap. Directly delivers the authenticity graft ("make the second heavy stop a downhill braking event") — T12 is now 313.8 → 113.8 km/h on a −3.0 % downgrade. |
| 11 | **C** | **The §9.3 transit-table format** | Every leg as from-(x,y,z) → to-(x,y,z) with length, grade and exit speed (§10.5). It is the only route format that leaves nothing to interpret. |
| 12 | **C** | **Derate grip by surface** | μ 1.00 circuit / 0.90 unrubbered access road / 0.85 showroom floor (§7). Makes the launch and transit speeds honest instead of assuming racing-line grip on fresh concrete. |
| 13 | **C** | **Name the deliberately empty zones in advance** | Three declared (§10.7), so camera standoff is a design decision rather than a late render-cost problem. |
| 14 | **C** | **One hard threshold mid-lap** (the Porte Saint-Elme idea) | Cannot be transplanted literally onto a parkland circuit, but its *function* can: **Le Pont de la Plongée** over the track at s = 2410 (6.80 m soffit) gives the helicopter arc a hard target altitude and puts the car bursting out from under a bridge into the doppler pass; **La Passerelle** over the pit straight differentiates the two passes of the same tarmac (§9). |
| 15 | **C** | **Publish a named, costed fallback for the doppler** | Primary s = 2555, fallback s = 2600, both costed in chord, mean speed and semitones. A decision in the beat sheet, not a footnote (§11 Beat 5). |

### 12.2 Grafts REJECTED, with the arithmetic

**R1 — "Graft A's blind crest at T8 onto D's summit run." (cinematic judge)**
Crest sight distance is `S = √( 100·(√(2h₁)+√(2h₂))²·L / A )`. With a chase lens at
h₁ = 0.75 m and a car reference at h₂ = 1.10 m, `(√1.5 + √2.2)² = 7.33`. Any vertical curve
gentle enough for the speeds involved (`L ≥ 55 m` at `A ≤ 5 %`) gives `S ≥ 91 m` — the car is
hidden only from a camera **more than 91 m astern**, which is not where D's chase camera is.
To hide the car from a 30 m chase you need `A ≈ 27 %`. Not achievable inside an 8–12 m budget
at any speed on this circuit. A's own T8 (+2.88 % into −1.3 %, `A = 4.18 %`) has the same
problem; its "~10 frames" claim silently assumes a camera ~75 m back.
**Taken instead:** the intent — motivated vertical drama — as **Le Basculement**, a 140 m
crest with `A = 4.15 %` giving **0.23 g of vertical unloading at 314 km/h** immediately before
the plunge. The car visibly goes light and the horizon drops; it is just not *blind*. Stated
honestly rather than claimed.

**R2 — "Put the finish line on the breach axis." (cinematic AND authenticity judges)**
Two separate failures. (a) *Literally*: the breach vector and the racing direction cannot be
collinear without the exit pointing against the racing direction — that is D's rejected
placement #2 and it needs a hairpin on the access road. (b) *As a partial slide*: the Beat-6
hold range is 595 m and is dominated by the camera's **southward standoff**, which is set by
the angular-separation constraint, not by the showroom's station along the straight. Moving
the showroom 65 m east buys ≈ 11 % of facade width, costs ≈ 0.9 s of Beat 4, and forces the
whole 14-bay garage row east because the breach route would otherwise cross the pit lane
*inside* the garage band (the route crosses `y = +13` at `x = −263.8`; garages start at
`x = −245`). Bad trade, rejected.
**Taken instead:** the underlying complaint — legibility — solved on the lens and the station
instead (18.75 mm at 595 m rather than 26 mm at 617 m), which improves the wound from ~55 px
to 52→48 px measured consistently and moves the hero subjects from 89 % to 77–82 % of
half-frame.

**R3 — "Hold the Beat-6 frame earlier / closer." (buildable judge)**
Tested exhaustively. The stations that give the biggest facade are 200–300 m *west* of the
line — e.g. circuit (−194, −254, 148) gives 162 px. But the camera arrives from the onboard
follow at **83.1 m/s heading down the pit straight**, and the minimum forward travel to stop
from 83.1 m/s at 1.2 g is **292 m**. That station needs only **66.5 m** of forward advance,
which requires **5.3 g** of braking. Every western candidate fails the same way. Verified by
solving the minimum-energy cubic boundary-value problem for each candidate: D's own published
station needs 3.6 g; the chosen station needs **2.03 g** and eases monotonically.
**Conclusion: D's eastward retreat was forced, not lazy**, and the graft does not survive
contact with the camera's momentum. What was kept is the *principle* — the hold is 22 m
closer, on a wider lens, with a verified 3 s frame and a verified occlusion clearance.

**R4 — "Adopt C's walled descending canyon and its 9 m paddock terrace."**
Re-derived D's own occlusion claim and it holds: the Beat-6 camera→wound ray crosses the
garage bands at circuit `x ≈ −345`, **100 m west of the garage row's western end at
`x = −245`**. The garages therefore do **not** occlude the showroom, so elevating it onto a
terrace buys **zero** Beat-6 pixels. Against that: a 4–9 m escarpment to model, a transformed
round-1 shell (which graft #1 exists to avoid), and the loss of the flat shard plane (graft
#4).
**Taken instead:** the confinement, without the terrain — **2.4 m cut retaining wall on the
north side of the apron run, 2.0 m tyre-stack wall on the south, and a pit-exit gate portal at
world x = +58** (§10.5). The camera flies a walled corridor at rooftop height and bursts into
the open, at almost no build cost.

**R5 — "Place the showroom so it looms over the main straight for the whole onboard follow."**
Geometrically impossible with a pit-exit merge. The showroom must be *upstream* of the merge
(otherwise the exit vector fights the racing direction), the merge is 215.6 m before the line,
and the onboard follow runs from T15 exit to the line. So the building is beside the first
40 % of the follow and behind the camera for the rest — and at circuit x = −350, y = +72 it
subtends a bearing of 55°+ off the track axis, outside a 24 mm frame.
**Taken instead:** the wound is pre-loaded by the *two* pit-straight passes (out lap at
288.6 km/h with the building wide in frame, flying lap tight and low 63 s later) and by
Beat 4's exposure ramp, not by a continuous sight line that the geometry cannot provide.

**R6 — "Drop D's T12 to about −2 m and steepen S11 from −0.9 % to ~−2.5 %." (cinematic judge)**
Superseded by a stronger version of the same idea: T12 sits at **−3.72 m** (the circuit's low
point) and S11 falls at **−4.45 %** over its last 160 m. Recording it as rejected only because
the specific numbers were replaced, not the intent.

### 12.3 Where the judges disagreed, and how it was resolved

**Disagreement 1 — the hairpin's setting.** The authenticity judge grafted C's *low-point
hairpin with adverse camber* onto D; the cinematic judge grafted A's *hairpin on the lip of
falling ground so the background drops*. These read as opposites: one wants the hairpin in a
bowl, the other on a lip.
**Resolved by separating road from land.** The *track* falls into T4 (−1.63 % through the
braking zone, apex at z = −3.21, adverse camber −1.5 % on entry easing to flat at the apex,
grafted from C) — so the heavy stop is downhill and the corner drains like a real road. The
*terrain* beyond T4 falls away at −8 % to −9.5 m (grafted from A) — so the kerb-height camera
gets its silhouette. Both judges get what they asked for; nothing is traded.

**Disagreement 2 — Beat-6 pixels versus Beat-6 reachability.** The cinematic and authenticity
judges both wanted the hero subjects bigger and less edge-jammed; the buildable judge wanted
the frame held closer. All three were arguing for the same thing and none of them checked
whether the camera could get there.
**Resolved by dynamics.** Section 10.6 solves it as a boundary-value problem with a stated
acceleration limit, which is the only way the question has an answer. The conclusion (D's
retreat direction was forced; the improvement available is in lens and margin, not station)
contradicts one graft from each of two judges and is stated with the numbers that killed it.

**Disagreement 3 — how much elevation D was actually wasting.** The authenticity judge said
D's real max grade was +3.11 %, not +3.97 %; the cinematic judge said the whole west half sat
at 0.5–1.2 %. Both were right, and both are consequences of interpolating a spline through
keyframes rather than designing a vertical alignment.
**Resolved by method, not by numbers.** Tangent grades + parabolic vertical curves (§5) make
the maximum gradient a *stated design value*. This spec's +5.20 % and −4.45 % are what the
road does, verified by evaluating the alignment at 0.25 m stations and taking the extremes.

**Disagreement 4 — D's lap time.** The authenticity judge reproduced D's 62.54 s to 0.01 s and
praised it; the same judge then demanded A's braking model, which necessarily changes it.
**Resolved in favour of physical honesty.** Reproducibility of a wrong model is not a virtue.
The lap is now **63.545 s**, still inside the 55–65 s window with 1.5 s of headroom, and
every braking row in §4 falls out of the model in §7.

---

## 13. CORRECTIONS MADE TO THE WINNING LAYOUT

Seven, all found by re-deriving rather than by reading.

1. **The launch run and impact speed.** D: "26 m indoor launch run", "≈ 85–100 km/h" at the
   glass. Measured: the car sits on the turntable at the origin, nose at X = +3.020, glass at
   X = +15.000 → **11.98 m**, and **53.8 km/h** at contact (§10.4). Beat 3's pre-fracture must
   be tuned for 50–60 km/h, not 85–100.
2. **D's Beat-6 `t = 0` key is occluded by D's own grandstands.** The ray from circuit
   (−40, −150, 55) to the car at the line crosses the grandstand front face (`y = −30`, 14 m)
   at **z = 11.5 m** — blocked by 2.5 m. Never checked in the source document. Fixed (§10.6).
3. **D's Beat-6 hold station is not dynamically reachable.** The minimum-energy trajectory
   from the peel-off to (−55, −460, 104) in 10 s peaks at **34.9 m/s² (3.6 g)**. The station
   published here peaks at **19.9 m/s² (2.03 g)** (§10.6).
4. **D's braking table disagreed with D's own solver** (found by the authenticity judge,
   fixed here by graft #5). Every zone in §4 now falls out of §7.
5. **D's headline max gradient of +3.97 % was unreachable from its own keyframes** (real
   +3.11 %). Replaced with an explicit vertical alignment whose stated max is what the road
   does (§5).
6. **Kerb geometry was internally inconsistent.** D specified a 60 mm serration amplitude on a
   50 mm kerb, and "negative sausage kerbs, 100 mm" — a contradiction in terms (a negative kerb
   is a depression). Corrected to a 50 mm kerb with a 25 mm serration (75 mm peak, 265 mm plank
   clearance) and true negative kerbs at −60 mm × 0.80 m (§9).
7. **The doppler ratio was reported with the sign inverted** in the source. Approaching is
   pitched **up**: `f′/f = c/(c + v_r)` with `v_r` positive when receding. The corrected
   sweep is **1.309 → 0.847** (§11).

Two further gaps closed rather than corrected: D's transit crossed 32 m of its own declared
"paddock dressing zone" with **no surface named** (the pit-exit apron is now a declared
surface with extents, §10.7), and D's runoff figures were defaults rather than arguments (now
budgeted per corner by exit speed, §9).

---

## 14. VERIFICATION, AND HOW TO REPRODUCE IT

Every assertion below was checked by the solvers listed at the end of this section, and each
must still hold after any edit to this spec.

| assertion | expected | measured |
|---|---|---|
| plan closure, integrating the §6 element list from (0,0,h=0°) | (0, 0), heading 360° | **(0.0, 4.9 × 10⁻¹⁵) m, 360.000000°** ✓ |
| net turn | +360.000° | **+360.0000°** ✓ |
| total length | 3 675.0 m | **3 675.0000 m** ✓ |
| **elevation closes in z** | z(0) = z(L) | **0.000 = 0.000, residual 0.00 m** ✓ |
| **elevation closes in grade** (it is a lap; a grade step at the line is a bump) | g(0) = g(L) | **0.000 % = 0.000 %** ✓ |
| elevation profile is C¹ everywhere | no grade step | max grade change per 0.25 m station **0.0229 %** (i.e. continuous, curvature-limited) ✓ |
| elevation range | 8–12 m | **11.630 m** (−3.666 … +7.964) ✓ |
| realised max/min grade equals the design tangents | +5.200 / −4.450 % | **+5.200 / −4.450 %** ✓ |
| lap time | 55–65 s | **63.545 s** ✓ |
| top speed | ~330 km/h | **330.8 km/h** ✓ |
| hairpin apex | ~80 km/h | **79.6 km/h** ✓ |
| corner count | 12–16 | **15** ✓ |
| min non-adjacent centreline separation | no self-intersection | **60.6 m** (s 872 ↔ 1092) ✓ |
| **§8 control points vs the analytic centreline** | ≤ 0.20 m | **0.123 m worst** (at s = 1013, in the hairpin exit); 0.108 m through the 176° hairpin itself ✓ |
| control points close cyclically | cp[201] = cp[0] | **(329.40, 169.82, 0.00) both** ✓ |
| Beat-6 held frame contains car + line + gantry + wound for 3.0 s | yes | **verified at t = +8.0 / +9.5 / +11.0**, max separation 75.8° in an 87.7° frame ✓ |
| Beat-6 sight line clears the grandstands | ≥ 6 m | **+29.4 m** to the wound, +57 … +83 m to the car ✓ |
| Beat-6 camera trajectory is realisable | ≤ 2.5 g | **2.03 g peak**, at the peel-off, easing monotonically ✓ |
| doppler near-static dwell | ≥ 3 s | **7.46 s** within ±220 m ✓ |
| every braking row falls out of the vehicle model | yes | **all four** ✓ |
| Beat 2 launch is rolling-contact-legal after the dais ramp | yes | 13.1 % ramp, no step ✓ |
| total film runtime | 100–130 s | **124.3 s** (126.1 s with the optional ramp) ✓ |

**Solvers.** Written and run for this synthesis. They live in **`tools/circuit/`** and
regenerate every number above, including `docs/circuit_spec.json`, from
`python3 tools/circuit/emit.py`.

```
geo.py     element list, Newton closure solve on S2/S9/S11
build.py   0.25 m sampling, vertical alignment (tangents + parabolic vertical curves),
           forward/backward speed solve, corner table, world transform
part2.py   launch/transit integration, on-screen lap time, control-point generation
           and chord-error measurement
part3.py   Beat-6 projection, angular separation, grandstand occlusion
part4.py   camera trajectory feasibility (minimum-energy cubic BVP)
final.py   doppler, catch-up chords, clothoid table, sagitta-driven control points
emit.py    all tables above + circuit_spec.json
```

They are self-contained (numpy only, no scipy) and take no arguments.

---

## 15. HONEST WEAKNESSES OF THIS DESIGN

1. **T14 is a kink dressed as a corner.** 19.4° at R = 90 m over 30.5 m, taken at 178 km/h —
   barely a lift. It exists because the closure solver needs its angle and because the camera
   needs one right-hand direction change while it re-acquires the car. Counting it gives 15
   corners; a driver would call this a 14-corner circuit. Both counts satisfy the brief, so
   nothing breaks, but this is the least honest line in the corner table. Inherited from D
   and not fixed.

2. **T3 is at the ceiling.** R = 140 m at 295 km/h is **4.89 g** — legal for a modern F1 car
   and the highest lateral load on the lap, but with only 68 m of arc it will read on camera
   as a full-throttle kink rather than a corner. Kept because the chase needs a hand-off
   moment before dropping to the hairpin.

3. **The car is 20–30 px in the held final frame.** At 601–815 m on an 18.75 mm lens the car
   is a streak, not a subject. That is literally what the brief asks for ("the car streaking
   on"), and with a 180° shutter at 257–295 km/h it will read as motion — but anyone hoping
   for a recognisable car in the last image will not get one. The alternative (a longer lens)
   costs the wound, and the wound is the story.

4. **The Beat-6 wound depends entirely on the interior lighting, the shard fan and the dust.**
   48–52 px of aperture at 595 m is small. Three mitigations are specified (§10.6) and one of
   them — the spot rigs staying lit for the whole film — is a hard cross-department dependency
   that is not visible from the layout. If the rigs are killed after the launch, the closing
   frame's most important story element becomes a grey smudge.

5. **The elevation is better than D's and still not Spa.** 11.63 m over 3 675 m concentrated
   into two punchy features means the camera gets exactly **two** genuine dive/climb
   opportunities (La Rampe, La Plongée) plus one crest. Between them the road is within 0.4 %
   of flat for over 1.5 km, and the "rise into the helicopter arc / dive off the summit" is
   carried substantially by the five specified landforms rather than by the racing surface. If
   the terrain build is skimped, Beat 5's altitude changes will look unmotivated. This is
   inherent to an 8–12 m ceiling and no arrangement of it fixes it.

6. **The catch-up after the doppler is still the film's most fragile move.** 485 m of chord in
   11.36 s at a 42.7 m/s mean is comfortable, but it starts from a near-hover and peaks near
   68 m/s (245 km/h), which is faster than any camera helicopter and at the top of what the
   quickest FPV drones do. It is motivated (the camera cuts the corner) and there is a costed
   fallback, but a viewer who flies drones will feel it.

7. **Beat 6 runs 11.0 s against the brief's "≈ last 8–10 s".** The extra second is the price of
   a 2.03 g camera deceleration instead of a 3.6 g one. It fits the 124.3 s total comfortably,
   but it is over the beat's own nominal and the beat-sheet owner should own that rather than
   discover it.

8. **As a racing circuit it has one and a half overtaking places.** T4 under braking from
   296 km/h is a real one; T12 from 314 km/h downhill is now a genuine second (better than D's,
   because the stop is longer and downhill), but the T12–T15 complex still exists so the camera
   can catch the car, not so cars can pass each other. Nothing overtakes in this film, so the
   cost is invisible on screen and real on paper.

9. **The two pit-straight passes could still read as a repeat.** La Passerelle and the 34 km/h
   speed difference help, but the beat sheet must make them different by construction — the
   out lap wide and outboard at 25 m lateral, the flying lap tight and onboard at 11 m astern.

10. **The world is diagonal.** Aligning the world frame to the showroom (graft #1) means the
    pit straight runs at 40° to the world axes. Circuit furniture is dimensioned in the circuit
    frame to compensate (§2, §10.7), and the JSON is world throughout, but anyone eyeballing
    coordinates in Blender will find nothing axis-aligned except the building. The alternative
    was transforming 927 validated round-1 objects. This is the right trade and it is still a
    real cost.

11. **The west lobe is expensive world.** The plan reaches to circuit x = −849, which is 289 m
    west of the pit straight's west end. Everything out there — T10 through T15, the doppler
    straight, the west hillside — is real geometry the camera flies at 5 m during the doppler
    beat and sees at 600–900 m during Beat 6's hold. There are no cheap far-side zones on this
    layout and the brief forbids them anyway. Budget for it or the held frame will show a soft,
    empty west.

12. **The lap-time model has a ±5 % band.** Point-mass, single-parameter downforce fit, no
    combined-slip, no tyre state, no gear steps, no banking contribution to grip. 63.545 s
    could honestly be 60.4–66.7 s, and the upper end breaks the brief's 65 s ceiling. If the
    built telemetry lands above 65 s, the cheapest fix is to shorten S9 by 60 m and re-solve
    closure on S2/S11 — that is why those three straights are the free variables.
