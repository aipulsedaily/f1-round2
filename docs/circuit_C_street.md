# CIRCUIT C — CIRCUIT DU QUARTIER VITRINE
## "Vitrine Quarter" — a semi-street circuit for one unbroken camera take

**Philosophy: STREET / URBAN-PADDOCK.** A harbour-and-old-town city circuit. Walls close,
buildings framing corners, a hairpin round a dock basin, four esses up a stepped street,
a gate arch you thread at 8.6 m, a market-square chicane. The paddock is not a field of
awnings — it is a **city terrace nine metres above the pit straight**, and the showroom is
a real glazed building fronting that terrace. Speed is made to feel violent by proximity to
solid geometry.

Every number below was produced by a geometry + vehicle-dynamics solver, not chosen by eye.
The loop closes to **0.1 mm**. Working scripts: `geo.py` (turtle + closure solve),
`sim.py` (sampling, elevation, forward/backward speed solve), `place.py` (showroom, transit,
sight-line), `out.py` (control points, plan raster).

---

## 1. HEADLINE NUMBERS

| | value | requirement | ✓ |
|---|---:|---|:-:|
| Total length | **3,572.3 m** | — | |
| Corners | **15** | 12–16 | ✓ |
| Predicted lap | **64.26 s** (avg 200.1 km/h) | ~55–65 s | ✓ |
| Top speed | **328.4 km/h** (main straight) | ~330 km/h | ✓ |
| Hairpin apex (T1) | **80.6 km/h**, R 30 m | ~80 km/h | ✓ |
| Esses complex | T3–T6, four corners, 147–175 km/h | required | ✓ |
| Double-apex sweeper | T7/T8, 228 → 259 km/h | required | ✓ |
| Elevation range | **11.36 m** (−0.19 → +11.17) | 8–12 m | ✓ |
| Steepest grades | **+5.27 %** climb / **−6.21 %** descent | — | |
| Main straight | 1,040 m + 152 m past the line into T1 braking | long | ✓ |
| Footprint | 1,345 × 757 m | — | |
| Loop closure residual | 0.0001 m position, 0.0000° heading | must close | ✓ |

**Sector split** — S1 (line → T6 exit) 1,003.9 m / 22.73 s · S2 (T6 → T9 exit) 801.7 m /
12.77 s · S3 (T9 → line) 1,766.7 m / 28.76 s.
**Speed distribution** — 8.7 s above 300 km/h, 17.7 s above 250, 11.6 s below 120.
Direction of travel: **anticlockwise** (turn budget sums to exactly +360°).

---

## 2. PLAN VIEW

True-scale raster of the solved centreline. `#` track · `S` showroom · `=` glass wall ·
`.` breach exit route · `L` start/finish line. World axes: **+X east, +Y north, +Z up**;
one character ≈ 14.5 m in X, 29 m in Y (so the plot is ~2:1 compressed vertically —
it is not distorted, characters are).

```
                                    CITADELLE  (highest ground, z +10.6 … +11.2)
                            8           7
                              #########                      <- Courbe de la Citadelle
                          #####       ####                      DOUBLE-APEX SWEEPER
                        ###              ##                     228 -> 259 km/h
                      ###                 ###
                9  ####                     ##
      PORTE       #                          ##
   SAINT-ELME    ##                          ###
   8.6 m gate    #                             ##            M O N T E E
   z +11.17      #                              ###          D E S
                 #                                ##         R E M P A R T S
                ##                                 ###       397 m climbing
               ##   10                               ##
             ###                                      ##
         11 ##                                          ##
   LA        #                                            ######   5
   DESCENTE  #                                           6      ####          LES ESCALIERS
   -6.21%    #                                      SSSS           ##         T3-T6 esses
             #                                       S==            ###       3    10.0 m wide
           ###  12                                     ..             ########
       13 ##                                            ...         4        ###
          #        MARCHE                                 ..                   ###   RAMPE DU FORT
          #        chicane                                 ...                   ##  +5.27%
          #        9.5 m                                     ..                   ####
          ##                                                  ..                     #########
           ##                                                  ...                 2         ##########
         14 ####                                                 ..                                   ###
               #####                                              ......                              ###  1
                   ########################################################################L###########
                 15        B O U L E V A R D   D U   Q U A I   (main straight, 1040 m)      ^        GRANDE
                                                                                            |        DARSE
                                       H A R B O U R   (open water, no geometry)         finish     hairpin
                                                                                          line      z -0.19

                                                                                                  [CAM6]
                                                                        Beat-6 closing camera (1105,-235,58)
```

Reading it: the car runs **east** along the harbour front, hairpins **left** 168° around the
Grande Darse dock at the far east, comes back west along the docks, turns right up the
**Rampe du Fort** (the 5.27 % climb out of the harbour), snakes north-west through the four
**Escaliers** esses, climbs the long **Montée des Remparts**, takes the **Citadelle**
double-apex sweeper across the top of the hill, threads the **Porte Saint-Elme** gate at the
circuit's highest point, plunges 5.8 m down **La Descente**, works through the **Marché**
chicane, and sweeps out of the **Virage du Phare** onto the main straight.

The showroom (`S`) sits inside the loop on a terrace, its glass wall (`=`) facing
south-east, with the breach route (`.`) running down to the main straight.

---

## 3. CORNER TABLE

Speeds from the forward/backward speed solve (§8). `dir` L = left, R = right.
Banking is given as engineered cross-slope; negative = adverse (falls away from the turn),
which is what a real public street does when it drains toward a harbour.

| # | name | type | dir | R (m) | turn | arc (m) | entry km/h | apex km/h | exit km/h | banking | z apex (m) | t (s) |
|---:|---|---|:-:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 1 | **Grande Darse** | hairpin | L | 30 | +168° | 88.0 | **328** | **80.6** | 82.5 | −1.5 % entry → 0 % apex | −0.19 | 4.6 |
| 2 | Rampe des Douanes | fast kink | R | 76 | −38° | 50.4 | 150 | 149.8 | 151.1 | −1.0 % | +1.02 | 12.0 |
| 3 | Escalier 1 | esse | L | 85 | +44° | 65.3 | 164 | 164.4 | 165.7 | −1.0 % | +7.29 | 15.4 |
| 4 | Escalier 2 | esse | R | 74 | −52° | 67.2 | 147 | 146.6 | 148.0 | −1.0 % | +7.75 | 17.6 |
| 5 | Escalier 3 | esse | L | 82 | +50° | 71.6 | 159 | 159.4 | 160.7 | −1.0 % | +8.15 | 19.8 |
| 6 | Escalier 4 | esse | R | 91 | −46° | 73.1 | 175 | 174.6 | 175.7 | −1.0 % | +8.55 | 22.0 |
| 7 | **Citadelle 1** | sweeper (apex 1) | L | 118 | +54° | 111.2 | 228 | **228.4** | 228.9 | **+3.0°** | +9.95 | 29.2 |
| 8 | **Citadelle 2** | sweeper (apex 2) | L | 132 | +40° | 92.2 | 243 | **259.4** | 264.8 | **+3.0°** | +10.60 | 31.2 |
| 9 | **Porte Saint-Elme** | tight gate | L | 39 | +46° | 31.3 | 94 | 94.4 | 96.2 | 0 % (flat threshold) | **+11.17** | 34.9 |
| 10 | La Descente | fast, downhill | R | 125 | −34° | 74.2 | 213 | 233.7 | 245.9 | **+2.0°** | +5.04 | 38.3 |
| 11 | Belvédère | medium | L | 88 | +44° | 67.6 | 169 | 169.4 | 170.6 | −1.0 % | +3.70 | 40.5 |
| 12 | Marché 1 | chicane in | R | 43 | −56° | 42.0 | 100 | 100.3 | 102.0 | −1.5 % | +2.81 | 43.4 |
| 13 | Marché 2 | chicane out | L | 46 | +58° | 46.6 | 105 | 104.8 | 106.4 | −1.5 % | +2.60 | 45.7 |
| 14 | Sous-le-Fort | medium-fast | L | 93 | +44° | 71.4 | 178 | 178.1 | 179.2 | −1.0 % | +2.35 | 49.0 |
| 15 | Virage du Phare | fast final | L | 107 | +38° | 71.0 | 205 | 204.6 | 205.3 | +1.5° | +2.10 | 51.1 |

**T7 + T8 are one corner with two apexes.** They are separated by a 30.0 m link straight and
turn a combined 94° over 233.4 m. Radius *increases* 118 → 132 m, so the car is accelerating
through it — the Pouhon pattern, not a dip-and-dip. It is the only place on the lap where the
car is above 250 km/h other than the main straight.

**T1 is the money braking event**: 328.4 → 80.6 km/h, 248 km/h shed in 91 m of braking, on
a −1.5 % adverse camber that falls toward the water, at the lowest point of the whole world
(z −0.19 m, i.e. below quay datum — the road dips into the dock basin).

---

## 4. TRACK WIDTHS, KERBS, BARRIERS — TO SCALE AGAINST THE CAR

The car is **5.698 m long, 2.005 m wide, 0.340 m ride height** (measured, per
`round2_inventory.md`). All of the following is dimensioned against those numbers, not
against a generic F1 car.

| section | width (m) | car widths | wall setback from track edge |
|---|---:|---:|---|
| Boulevard du Quai (main straight) | 14.0 | 7.0 | 2.5 m + quay wall (south), 2.5 m + pit wall (north) |
| T1 Grande Darse | 16.0 entry flare → 12.0 apex | 6.0 | 14 m of harbour apron runoff on the outside |
| Quai des Docks (T1→T2) | 11.5 | 5.7 | 1.0 m |
| Rampe du Fort (climb) | 10.5 | 5.2 | 0.8 m both sides — the tightest walled run |
| Les Escaliers T3–T6 | 10.0 (9.4 at T4) | 4.7 | 0.8 m |
| Montée des Remparts | 12.0 | 6.0 | rampart wall 1.0 m (inside), open parapet (outside) |
| Courbe de la Citadelle T7/T8 | **13.5** | 6.7 | **12 m of esplanade paving** — deliberate, see §10 |
| Esplanade (T8→T9) | 13.0 | 6.5 | 6 m |
| **T9 Porte Saint-Elme** | **8.6** | **4.3** | gate jambs at 0.4 m — narrowest point on the circuit |
| La Descente T10 | 11.5 | 5.7 | 1.2 m |
| T11 Belvédère | 11.0 | 5.5 | 1.0 m |
| Marché chicane T12/T13 | 9.5 | 4.7 | 0.6 m |
| Rue Sud / T14 | 11.5 | 5.7 | 1.0 m |
| T15 Virage du Phare | 12.5 → 14.0 onto the straight | 6.2 | 1.5 m, harbour wall outside |

**Kerbs.** 500 mm wide, 50 mm base with a 25 mm serration → **75 mm peak**. The car's plank
sits at 0.340 m, so peak-to-plank clearance is **265 mm**: the car can ride every kerb on the
circuit without the floor touching. Two-tone red/white at 1.0 m pitch. Negative kerbs
(−40 mm, 700 mm wide) on the exits of T4, T6 and T13 only.

**Barriers.** 1.0 m concrete/steel barrier, top at track-z + 1.0 m, with 3.2 m debris fence
above it on spectator sides (total 4.2 m). Tecpro at T1 exit, T9, T12/T13 and T15.
The only sections with genuine runoff are T1 (harbour apron) and T7/T8 (esplanade) — see §10.

**Usable lateral offset for the racing line** (half-width − half-car − 0.30 m margin), for
whoever owns the telemetry CSV: main straight ±5.5 m, esses ±3.7 m, Porte Saint-Elme
**±3.0 m**, Marché chicane ±3.4 m, Citadelle ±5.4 m.

---

## 5. ELEVATION PROFILE

Range **11.36 m**, but deliberately **concentrated into two ramps** rather than smeared —
a circuit with 11 m spread evenly over 3.5 km has an average grade of nothing and gives the
camera nowhere to dive from.

| station | z (m) | note |
|---|---:|---|
| Start/finish line | +0.90 | |
| **T1 Grande Darse apex** | **−0.19** | **lowest point** — dips into the dock basin |
| T2 Rampe des Douanes | +1.02 | |
| **Rampe du Fort** (110 m straight) | +1.20 → +7.00 | **+5.27 %** — the climb out of the harbour |
| T3 → T6 (esses) | +7.29 → +8.55 | shelf, gentle |
| Montée des Remparts (397 m) | +8.64 → +9.60 | +0.24 %, long and nearly flat |
| T7 / T8 Citadelle | +9.95 / +10.60 | |
| **T9 Porte Saint-Elme apex** | **+11.17** | **highest point** |
| **La Descente** (95 m straight) | +11.10 → +5.20 | **−6.21 %** — the plunge off the citadel |
| T11 → T15 | +3.70 → +2.10 | stepping back down to the quay |
| Main straight crest (x ≈ 226, s = 2798) | +2.65 | |
| back to the line | +0.90 | main straight falls gently toward T1 |

The main straight is **not flat**: it crests early and falls 1.75 m over its last 774 m into
the T1 braking zone. That is a downhill braking event at 328 km/h.

---

## 6. CENTRELINE GEOMETRY — GENERATOR

This is the **exact, unambiguous definition**. It is a turtle walk: start at the start/finish
line, at world **(1000.000, 0.000)**, heading **0°** (due east, +X), and execute the list.
Angles are math convention (CCW positive). Corner turns sum to exactly **+360.000°**.

| # | segment | kind | length / radius | turn |
|---:|---|---|---:|---:|
| 0 | main_tail | straight | 152.000 | — |
| 1 | **T1** Grande Darse | arc | R 30.000 | +168.0° |
| 2 | quai_nord | straight | 240.451 | — |
| 3 | **T2** Rampe des Douanes | arc | R 76.000 | −38.0° |
| 4 | rampe_fort | straight | 110.000 | — |
| 5 | **T3** Escalier 1 | arc | R 85.000 | +44.0° |
| 6 | e1 | straight | 30.000 | — |
| 7 | **T4** Escalier 2 | arc | R 74.000 | −52.0° |
| 8 | e2 | straight | 26.000 | — |
| 9 | **T5** Escalier 3 | arc | R 82.000 | +50.0° |
| 10 | e3 | straight | 30.000 | — |
| 11 | **T6** Escalier 4 | arc | R 91.000 | −46.0° |
| 12 | montee | straight | 396.998 | — |
| 13 | **T7** Citadelle 1 | arc | R 118.000 | +54.0° |
| 14 | link | straight | 30.000 | — |
| 15 | **T8** Citadelle 2 | arc | R 132.000 | +40.0° |
| 16 | esplanade | straight | 140.000 | — |
| 17 | **T9** Porte Saint-Elme | arc | R 39.000 | +46.0° |
| 18 | desc1 | straight | 95.000 | — |
| 19 | **T10** La Descente | arc | R 125.000 | −34.0° |
| 20 | desc2 | straight | 55.000 | — |
| 21 | **T11** Belvédère | arc | R 88.000 | +44.0° |
| 22 | desc3 | straight | 60.000 | — |
| 23 | **T12** Marché 1 | arc | R 43.000 | −56.0° |
| 24 | chic | straight | 24.000 | — |
| 25 | **T13** Marché 2 | arc | R 46.000 | +58.0° |
| 26 | rue_sud | straight | 75.000 | — |
| 27 | **T14** Sous-le-Fort | arc | R 93.000 | +44.0° |
| 28 | link2 | straight | 45.000 | — |
| 29 | **T15** Virage du Phare | arc | R 107.000 | +38.0° |
| 30 | main_straight | straight | 1040.000 | — |

Ends at (1000.000, 0.000) heading 360.0°. **Closure residual: 0.0001 m, 0.0000°.**

**Elevation is applied as a function of arc length** (s = 0 at the line, increasing in the
direction of travel), linear between these keys then smoothed with 14 passes of a
[0.25, 0.5, 0.25] kernel at 1 m sampling:

```
s = 0.0      z = 0.90     s = 1588.2  z = 10.60    (T8 apex)
s = 196.0    z = -0.20    s = 1774.3  z = 11.10    (esplanade end)
s = 480.5    z = 0.85     s = 1789.9  z = 11.18    (T9 apex, high point)
s = 530.9    z = 1.20     s = 1805.6  z = 11.10    (top of La Descente)
s = 640.9    z = 7.00     s = 1900.6  z = 5.20     (foot of La Descente)
s = 673.5    z = 7.30     s = 1937.7  z = 5.05
s = 769.7    z = 7.75     s = 2063.6  z = 3.70
s = 865.1    z = 8.15     s = 2178.4  z = 2.80
s = 967.4    z = 8.55     s = 2246.7  z = 2.60
s = 1400.9   z = 9.60     s = 2380.7  z = 2.35
s = 1456.5   z = 9.95     s = 2496.8  z = 2.10
                          s = 2798.0  z = 2.65     (main straight crest)
                          s = 3572.3  z = 0.90     (back to the line)
```

---

## 7. CENTRELINE GEOMETRY — EXPLICIT CONTROL POINTS

115 ordered points, world metres, **(x, y, z)**, sampled at 18 m through corners and 55 m on
straights — dense enough that a Blender **POLY** curve through them is visually
indistinguishable from the analytic path, and a NURBS/Bezier fit converges cleanly. Point 0
is the start/finish line; the curve is **cyclic** (point 114 is 1 m short of point 0).

Read left-to-right in each row group: `idx  x  y  z`.

```
  0   1000.0      0.0   0.90   29    652.8    311.9   8.02   58     71.3    732.8  10.69   87   -171.3     91.3   2.38
  1   1055.0      0.0   0.59   30    640.4    326.0   8.10   59     57.2    721.5  10.74   88   -163.3     75.0   2.34
  2   1110.0      0.0   0.28   31    625.0    336.9   8.17   60     15.1    686.2  10.89   89   -152.4     60.6   2.31
  3   1140.0      0.0   0.11   32    607.6    344.1   8.25   61    -27.1    650.8  11.04   90   -139.0     48.5   2.27
  4   1158.9      0.8   0.01   33    588.9    347.4   8.32   62    -40.9    639.3  11.09   91   -115.3     30.1   2.20
  5   1174.9     10.6  -0.10   34    571.1    349.9   8.39   63    -53.2    626.1  11.16   92   -100.2     18.6   2.16
  6   1181.9     27.9  -0.19   35    553.5    353.5   8.46   64    -58.5    608.9  11.04   93    -83.7      9.3   2.12
  7   1177.4     46.0  -0.13   36    536.9    360.4   8.53   65    -62.4    554.0   7.68   94    -65.7      3.1   2.12
  8   1163.0     57.9  -0.06   37    521.9    370.4   8.58   66    -64.3    526.1   5.95   95    -47.0      0.2   2.15
  9   1108.5     69.9   0.15   38    509.3    383.1   8.63   67    -65.7    508.1   5.18   96      9.0     -0.0   2.25
 10   1053.8     81.5   0.36   39    476.8    427.6   8.76   68    -69.1    490.4   5.10   97     64.0     -0.0   2.35
 11    999.1     93.2   0.56   40    443.9    472.9   8.90   69    -75.0    473.4   5.00   98    119.0     -0.0   2.46
 12    944.5    104.8   0.77   41    411.0    518.2   9.03   70    -83.4    457.4   4.80   99    174.0     -0.0   2.56
 13    925.9    108.7   0.84   42    378.1    563.5   9.17   71    -93.8    442.7   4.61  100    229.0     -0.0   2.64
 14    908.6    113.9   0.96   43    345.2    608.8   9.30   72   -117.8    412.0   4.19  101    284.0     -0.0   2.52
 15    893.0    123.1   1.08   44    312.2    654.1   9.44   73   -129.3    396.9   3.99  102    339.0     -0.0   2.39
 16    879.9    135.6   1.28   45    279.9    698.6   9.57   74   -137.9    380.2   3.79  103    394.0     -0.0   2.27
 17    844.6    177.7   4.15   46    269.2    713.1   9.64   75   -142.8    362.0   3.61  104    449.0     -0.0   2.15
 18    817.6    209.9   6.37   47    256.8    726.2   9.75   76   -143.7    343.1   3.47  105    504.0     -0.0   2.02
 19    805.8    223.6   7.06   48    242.6    737.2   9.86   77   -138.4    291.4   3.06  106    559.0     -0.0   1.90
 20    792.0    235.1   7.22   49    226.9    746.0   9.97   78   -136.9    273.5   2.92  107    614.0     -0.0   1.77
 21    776.0    243.5   7.34   50    210.0    752.3  10.06   79   -141.2    256.2   2.79  108    669.0     -0.0   1.65
 22    758.6    248.3   7.43   51    192.4    756.0  10.15   80   -152.2    242.1   2.74  109    724.0     -0.0   1.52
 23    735.7    250.9   7.54   52    174.4    756.9  10.24   81   -166.0    230.5   2.69  110    779.0     -0.0   1.40
 24    717.8    253.0   7.62   53    156.4    756.9  10.33   82   -179.2    217.1   2.63  111    834.0     -0.0   1.28
 25    700.7    258.5   7.71   54    138.4    756.6  10.42   83   -186.3    199.8   2.58  112    889.0     -0.0   1.15
 26    685.4    267.9   7.79   55    120.5    754.2  10.51   84   -186.1    181.0   2.55  113    944.0     -0.0   1.03
 27    672.8    280.8   7.86   56    103.2    749.3  10.59   85   -178.4    126.6   2.45  114    999.0     -0.0   0.90
 28    662.9    295.8   7.94   57     86.7    742.1  10.65   86   -175.9    108.7   2.41
```

Key landmark coordinates, for cross-checking a build:

| landmark | world (x, y, z) |
|---|---|
| Start/finish line (centre) | (1000.00, 0.00, 0.90) |
| T1 Grande Darse apex | (1181.84, 26.86, −0.19) |
| T9 Porte Saint-Elme apex | (−54.38, 623.88, +11.17) |
| T7 / T8 Citadelle apexes | (230.97, 744.06, +9.95) / (102.25, 748.96, +10.60) |
| T15 exit = start of main straight | (−40.00, 0.00, +2.16) |
| Showroom glass wall centre | (463.60, 272.70, floor +9.00) |
| Breach route merge onto circuit | (722.22, 0.00, +1.53) |

---

## 8. LAP TIME — AND WHY IT IS THAT NUMBER

**Predicted lap: 64.26 s.** Not estimated — solved.

**Vehicle model** (a plausible current-generation F1 car; the round-1 car's measured
dimensions match one):

| parameter | value | how it was fixed |
|---|---:|---|
| mass (car + driver + fuel) | 800 kg | regulation ballpark |
| power at the wheels | 700 kW | — |
| drag area C_d·A | 1.48 m² | **back-solved** so that P/v = ½ρC_dAv² lands the terminal speed at exactly 330 km/h |
| lift area C_L·A | 4.45 m² | L/D = 3.0, typical F1 |
| μ lateral / braking | 1.45 | 1.55 slick baseline **derated for a street surface** (bumps, paint, manhole covers) |
| lateral accel cap | 52 m/s² (5.3 g) | tyre limit above which downforce stops helping |
| braking cap | 52 m/s² | |
| traction off the line | 11.0 m/s² | gives 0–100 km/h ≈ 2.6 s |

**Corner speeds are not chosen, they are consequences.** Solving
v²/R = μ(g + ½ρC_LAv²/m) for v gives R(v), and every radius in §3 was picked from that
curve to hit a target apex speed:

```
   80 km/h -> R  29.6 m      (T1  built at R 30  -> solver returns 80.6)
   95 km/h -> R  39.4 m      (T9  built at R 39  -> solver returns 94.4)
  105 km/h -> R  46.2 m      (T13 built at R 46  -> solver returns 104.8)
  175 km/h -> R  91.2 m      (T6  built at R 91  -> solver returns 174.6)
  205 km/h -> R 107.2 m      (T15 built at R 107 -> solver returns 204.6)
  228 km/h -> R 117.8 m      (T7  built at R 118 -> solver returns 228.4)
```

**Speed profile.** Curvature sampled at 1 m, corner-speed ceiling applied, then alternating
backward (braking-limited) and forward (traction/power-limited) passes to convergence, with
road grade entering both as ±g·sin θ. Braking capability is evaluated at the *upstream*
speed, where the car actually is and where it has the downforce — evaluating it at the
slower downstream speed (the easy mistake) understates high-speed braking by ~2.5×
and truncated top speed by 40 km/h before I fixed it. Lap time is ∫ds/v.

**Sanity checks against reality.** 3,572 m at 200.1 km/h average. Baku averages 216 km/h,
Singapore 180, Monaco 160. This circuit has Baku's long straight married to Monaco-grade
confinement, and lands between them — where it should. 8.7 s of the lap is above 300 km/h
and 11.6 s below 120 km/h: a genuinely bipolar street circuit, which is the point.

**Length is constrained by the lap-time window, not chosen.** At this speed profile,
55 s ⇒ ~3,060 m and 65 s ⇒ ~3,615 m. 3,572 m sits inside that band. I tried shortening it:
cutting the main straight by 95 m did **not** shorten the lap, because the loop's turn budget
(+360°) and fixed radii make its perimeter rigid — the solver simply poured the length back
into the Montée. Opening the Marché chicane from R 43/46 to R 58/62 gained only 0.15 s,
because the larger radii lengthened the loop by 37 m and cancelled the gain. Both experiments
are in the working scripts. **This layout wants to be ~3.57 km and ~64 s**, and I stopped
fighting it.

---

## 9. SHOWROOM + PADDOCK PLACEMENT, AND THE BEAT-6 SIGHT-LINE

### 9.1 The urban-paddock idea

There is no field of motorhomes. The paddock is **Place Vitrine**, a stone terrace
**9.00 m above the pit straight**, cut into the escarpment that separates the harbour front
from the old town. The pit garages sit at ground level along the main straight; the upper
paddock, the hospitality units and the **showroom** are on the terrace above them, connected
by the **Rampe Vitrine**, a walled service street that descends to the circuit and doubles as
the pit exit road. This is Monaco's and Macau's actual topology, and it is the only paddock
arrangement in which "the showroom is a real building trackside" is not a contrivance.

### 9.2 Exact placement

| property | value |
|---|---|
| Interior volume | **30.0 × 22.0 m, 6.50 m ceiling** — preserved *exactly* from round 1, so the measured exploded field (9.84 × 4.49 × 5.96 m, top at Z 4.62) keeps its 1.88 m ceiling clearance |
| Interior centre (plan) | **(455.00, 285.00)** |
| Floor / terrace level | **z = +9.00** (natural grade there is +7.35, so it sits on a 1.65 m retaining plinth) |
| Long axis bearing | **145°** (math angle −55°) — the 30 m axis is the launch run |
| Glass wall | the **22.0 m × 6.50 m** south-east end, centre at **(463.60, 272.70)** |
| Glass wall outward normal | **(0.5736, −0.8192, 0)** — faces SSE, down over the harbour |
| Exterior | 34 × 26 m footprint, 10.40 m above floor (6.50 interior + 3.90 clerestory/structure); parapet top **z = +19.40**; silhouette 12.05 m above natural grade |
| Clearance to track | **91.7 m** from the nearest building corner to the nearest centreline point (T6) |

The long axis is the launch axis on purpose: the car gets **24.5 m of run** from the
turntable to the glass, and by the vehicle model (0.55 throttle for the first 0.42 s of
wheelspin, then full) it arrives at the glass at **85.9 km/h after 2.27 s** — fast enough to
destroy a structural glazing bay, slow enough that the shard field stays in frame.

### 9.3 Breach exit vector and route to the circuit

**Breach point (463.60, 272.70, +9.00). Exit vector (0.5736, −0.8192, 0.0000)** — level, no
drop, because the forecourt is flush with the showroom floor. The car does not become
airborne at the wall.

| leg | length | from → to | grade | speed out |
|---|---:|---|---:|---:|
| **Place Vitrine** forecourt (level plaza, 46 m wide) | 110.0 m | (463.6, 272.7, 9.00) → (526.7, 182.6, 9.00) | 0 % | 200 km/h |
| **Rampe Vitrine** (walled descending street, 13 m wide) | 155.2 m | (526.7, 182.6, 9.00) → (615.7, 55.4, 2.55) | **−4.15 %** | 206 km/h |
| **merge arc** (R 130 m, 55° left, = the pit-exit blend) | 124.8 m | (615.7, 55.4, 2.55) → (722.2, 0.0, 1.53) | −0.82 % | 224 km/h |
| **total breach → circuit** | **390.0 m** | drop 7.47 m | | **7.62 s** |
| then merge → start/finish line | 277.8 m | (722.2, 0, 1.53) → (1000, 0, 0.90) | | 298 km/h, **3.73 s** |

The merge radius of 130 m would physically permit 262 km/h, so at 224 km/h the car flows
onto the circuit rather than negotiating a corner — it is a merge, not a turn. The route
joins the main straight **277.8 m before the line**, so the car crosses the start/finish line
at 298 km/h and *that crossing is the start of the flying lap*. It crosses again 64.26 s
later at **328 km/h**. Two crossings, 30 km/h apart, bracketing the lap.

### 9.4 The Beat-6 sight-line — solved, not hand-waved

**The requirement:** one frame must contain the car crossing the finish line *and* the
breached showroom in the distance. The tension is that the breach exit wants the showroom
near where the car joins the circuit, while the closing wide wants it far away and visible.

**The solution: the Beat-6 sight-line and the Beat-3/4 breach corridor are the same
corridor, 16.6° apart.** The camera looks back up almost exactly the line the car drove out
along. Every metre that had to be kept clear for the car to drive through is the same metre
that has to be kept clear for the camera to see the wound. One constraint, satisfied twice.

Closing camera at **(1105, −235, 58)** — over open harbour water, 58 m up, looking
north-west (azimuth ≈ 128°, pitch −8°, **45 mm** full-frame equivalent):

| target | azimuth | distance | elevation |
|---|---:|---:|---:|
| car on the finish line (1000, 0, 0.9) | 114.1° | **257 m** | −12.5° |
| breach wound (463.6, 272.7, 12.5) | 141.6° | **818 m** | −3.2° |
| **separation** | **27.6°** | | 9.3° |

| lens | h-FOV | fits 27.6°? | showroom px/m | car px/m |
|---:|---:|:-:|---:|---:|
| 35 mm | ±27.2° | yes | 4.56 | 14.50 |
| **45 mm** | **±21.8°** | **yes** | **5.87** | **18.65** |
| 50 mm | ±19.8° | yes | 6.52 | 20.72 |

At 45 mm on a 3840 px frame: the **10 m breach hole is 59 px wide**, the 22 m glass facade
is 129 px, and the car is 106 px long. The wound reads as a black notch taking ~20 % out of a
lit glass box. The facade is seen **16.6° off-normal** — essentially face-on, which is why it
reads at all at 818 m. Both subjects sit at ~63 % of the half-frame width, so the car lands
low-left and the showroom upper-right with the main straight running between them.

**Occlusion is verified, not assumed.** Ray from camera to wound, against the infield
escarpment (which rises linearly from +1.6 m at the straight to +9.00 m at the terrace):

```
  at y =  45 m   ray z = 32.9 m   ground  2.8 m   ->  30.1 m clear   (over the pit garages)
  at y = 150 m   ray z = 23.5 m   ground  5.7 m   ->  17.8 m clear   (over the escarpment)
  at y = 250 m   ray z = 14.5 m   ground  8.4 m   ->   6.2 m clear   (over the forecourt)
```

Three hard design constraints fall out of that last line, and they are cheap to honour
because they are also what the car needs:

1. **The escarpment between the main straight and the terrace is landscaped, not built** —
   the *Jardins du Quai*, open terraced gardens with planting capped at 6 m. Monaco has
   exactly this above its harbour, so it costs nothing in plausibility.
2. **Nothing on Place Vitrine within 25 m of the glass wall may exceed 5.5 m** — no lighting
   masts, no gantries, no trees in the exit wedge. This is automatically satisfied: it is the
   corridor the car drives through at 200 km/h.
3. **Grandstands go on the north (escarpment) side of the main straight only.** The harbour
   side stays open water with just a quay wall — which is what a harbour front is, and which
   guarantees nothing at all sits between the closing camera and the finish line.

**Why the showroom is 9 m up.** Elevating it onto the terrace does three jobs at once: it
puts the facade above the pit-garage roofline so the closing wide can see it; it makes the
Rampe Vitrine a genuine descending ramp instead of a flat driveway; and it means the wounded
building **looms over the main straight for the whole of the lap's final 1,040 m run**, so
Beat 5's onboard follow keeps the wound in the upper-left of frame without any extra staging.
Continuity for free.

---

## 10. CAMERA NOTE PER BEAT — WHAT THIS LAYOUT GIVES THAT ANOTHER WOULD NOT

**The stated risk of a street philosophy is that close walls kill the helicopter arc and the
closing wide.** I did not mitigate that with luck. The circuit contains **exactly two
engineered open zones**, placed precisely where the camera needs to breathe, and both are
justified by the fiction rather than bolted on:

- **The Citadelle esplanade** (T7/T8) — 13.5 m of track plus 12 m of open paving, on the
  highest ground, with the town roofs 10 m *below*. This is the helicopter-arc zone.
- **The harbour** — everything south of the main straight is open water. No geometry, no
  occluders, unlimited camera altitude and standoff. This is the closing-wide zone.

Everywhere else the walls are 0.6–1.2 m from the track edge and the camera can fly closer to
solid geometry than a parkland circuit would ever allow.

**Beat 1 — assembly, inside the showroom.** The interior is round 1's volume unchanged, so
the 15-cluster exploded field and its 1.88 m ceiling clearance are already validated. What
this *placement* adds: the glass wall faces SSE into a late-afternoon sun, so the darkened
showroom is lit by one enormous soft rectangle. Parts hanging in the exploded field get free
rim separation from that wall, and the camera can weave the 9.84 m field with the glazing as
a luminous backdrop — the wall we are about to destroy is the key light for the beat that
precedes its destruction.

**Beat 2 — ignition and launch.** 24.5 m of run along the 30 m axis, straight at the glass.
The car reaches 85.9 km/h in 2.27 s. The camera can sit low behind the diffuser with the
glass wall — and, beyond it, the harbour and the whole lit circuit — already in frame and in
focus. The audience sees where the car is going before it goes.

**Beat 3 — the breach.** Because the forecourt is level with the floor and 46 m wide, the
camera has a clean 360° of arc around the impact point with nothing to clip. The shard field
erupts *outward over a terrace with a 1.65 m drop at its edge*, so debris skitters and then
falls — two-stage debris behaviour the sim gets for free from the geometry. And the shards
land in the exact wedge the closing camera will later look up: the glitter on Place Vitrine
is still there in Beat 6.

**Beat 4 — transit.** This is where a street circuit annihilates a parkland one. The route is
a **155 m walled canyon at −4.15 %**, 13 m wide, dropping the camera and car 6.5 m between
buildings — and then it opens, hard, into the harbour as the merge arc swings left and the
whole waterfront appears at once. The camera flies the canyon at rooftop height with walls
1.5 m off each side, then bursts into open sky. There is no way to buy that transition on a
circuit surrounded by grass.

**Beat 5 — the lap.** In order, with what each gives:

- **T1 Grande Darse, low kerb-height.** 328 → 80.6 km/h, downhill, adverse camber, at the
  lowest point in the world (z −0.19). The 14 m harbour apron on the outside is the only
  place on the circuit with room for the camera to sit at kerb height *outside* the barrier
  line and be swallowed by the car as it turns in.
- **Rampe du Fort, +5.27 %.** The camera crests a real hill at 150 km/h with the harbour
  falling away behind — the first altitude the shot has gained since the showroom.
- **Les Escaliers (T3–T6), helicopter arc.** Four esses in a 10 m street, 147–175 km/h. The
  buildings on the *north* side of this street are 9–11 m two-storey, the south side is the
  escarpment, and there is a stepped-park gap on the inside of T4/T5. So the camera can climb
  continuously from street level to 45 m *through* a real gap in the massing and arc over the
  block while the car threads the esses below — a helicopter move performed inside a city,
  which is precisely the shot a parkland circuit cannot offer.
- **Montée des Remparts.** 397 m climbing along the rampart wall, walled on the inside, open
  parapet on the outside with the entire quarter 8 m below. The camera's natural vantage
  change: drop off the rampart and fly *outside* the circuit looking back in.
- **Courbe de la Citadelle (T7/T8), 228 → 259 km/h.** The open zone. Two apexes and rising
  speed means the camera can hold one long banking arc across 233 m without the car's
  attitude going static — it is loading up, unwinding, and loading again.
- **Porte Saint-Elme, 8.6 m.** The circuit's highest point and narrowest gate. The camera
  threads an arch alongside a car doing 94 km/h with 3.3 m of air each side. This is the
  single most claustrophobic frame available anywhere in the design.
- **La Descente, −6.21 %.** 5.8 m of drop in 95 m at 213–246 km/h. The camera dives, and it
  dives *because the road does*.
- **Marché chicane (T12/T13), 100/105 km/h, 9.5 m wide.** Market square, walls at 0.6 m.
  Alternative doppler position if the primary is rejected — see below.
- **Virage du Phare exit — the doppler beat.** The camera hovers over the harbour wall
  ~100 m up the main straight, 4 m high, near-static. The car unwinds T15 at 205 km/h and
  passes at **255 km/h** with 400 m of clean approach and departure sight-line, so the hold
  is comfortably ≥ 3 s. The physics gives a textbook sweep with no special-casing:
  f'/f = **1.260 approaching, 0.829 receding** — +4.0 semitones then −3.3.
- **Main straight, tight onboard follow.** 1,040 m, 328.4 km/h, the wounded showroom
  standing on its terrace in the upper left the whole way.

**Beat 6 — the closing wide.** Fully specified in §9.4. The camera decelerates, rises and
pulls back over open water to (1105, −235, 58); the car crosses the line at **328 km/h**
(the finish line sits 152 m clear of the T1 braking point precisely so the car is flat out
across it, not already braking) and streaks on toward the hairpin; and 818 m away, 16.6°
off-normal and lit from inside, the showroom shows its hole.

---

## 11. RUNTIME BUDGET — AN ARITHMETIC PROBLEM I AM HANDING OVER, NOT HIDING

| beat | duration | source |
|---|---:|---|
| 1 assembly | 35.0 s | brief's figure |
| 2 ignition + launch | 3.3 s | 1.0 s hold + **2.27 s** solved launch |
| 3 breach (speed-ramped) | ~8.0 s | brief's figure |
| 4 transit → line | **11.35 s** | **7.62 s** breach→merge + **3.73 s** merge→line |
| 5 the flying lap | **64.26 s** | solved |
| 6 closing wide | ~9.0 s | brief's figure |
| **total** | **~130.9 s** | deliverable spec is ~100–130 s |

That is **~1 s over the stated ceiling**. Real, small, and it needs a decision rather than a
shrug. The levers, cheapest first:

1. **Beat 1 at 32–33 s** instead of 35. The brief says the beat sheet, not its own numbers,
   is the source of truth. Buys 2–3 s. Recommended.
2. **Beat 3's ramp at 6.5 s** instead of 8. Buys 1.5 s.
3. **Move the showroom ~60 m closer to the merge.** Buys ~1.5 s off Beat 4 but costs Beat 6
   legibility (the breach would drop from 59 px to ~50 px wide). Not recommended.
4. **Do not** try to shorten the lap by shortening the circuit — §8 shows both obvious
   attempts fail.

---

## 12. HONEST WEAKNESSES OF THIS DESIGN

1. **The lap is 64.26 s — the top of the 55–65 s window**, and with the 11.35 s transit the
   total lands ~1 s over the 130 s ceiling (§11). I could not shorten the circuit without
   breaking it: the +360° turn budget with these radii makes the perimeter rigid, and both
   shortening experiments failed. Someone has to spend a couple of seconds from Beat 1 or
   Beat 3.

2. **The Montée des Remparts is 397 m and is the least "street" thing here.** It is a second
   high-speed zone in the middle of what is supposed to be a claustrophobic city lap, and it
   dilutes the theme. It exists because loop closure demands ~400 m of north-west-heading run
   between the harbour and the citadel; when I forced it shorter the solver either failed to
   close (25 m gap) or moved the same length into the Rampe du Fort and destroyed the 5.27 %
   climb grade. I have dressed it as a rampart road and given the camera a use for it, but it
   is a rationalisation of a constraint, not a choice.

3. **T1 eats 168° — 47 % of the entire turn budget.** That single decision is what forces
   item 2. A 120–130° T1 would give a tighter, more consistently urban layout with more turn
   budget for the final complex. I kept the full hairpin because 328 → 80.6 km/h at the
   lowest point of the world is the best single corner in the design, but it is a real
   trade and another designer would reasonably call it the wrong one.

4. **The doppler-to-onboard catch-up is not physically flyable.** For the camera to be
   alongside the car 290 m up the straight it must cover that distance in 3.7 s from a near
   hover — a mean of 286 km/h and a peak of 306 km/h, requiring ~23 m/s² of acceleration.
   Standard for a virtual camera, impossible for a drone, and a sharp viewer may read it as
   a cheat that betrays the one-take illusion. **Fallback:** run the doppler at the Marché
   chicane instead (T12/T13, 100–105 km/h, 9.5 m wide, walls at 0.6 m). The catch-up becomes
   trivial and the confinement is better, but the doppler sweep drops from ~4 semitones to
   ~1.5 and it is no longer immediately before the straight.

5. **T7/T8 at 228–259 km/h between walls is optimistic for a street circuit.** I gave the
   Citadelle 12 m of esplanade runoff to justify it, but a purist is right to say that a
   genuine street circuit does not contain a 259 km/h double-apex, and that the runoff exists
   because the camera needed it rather than because the city has it.

6. **The Beat-6 sight-line clears the escarpment by only 6.2 m at y = 250** — 23 m in front
   of the glass wall. Anything taller than ~5.5 m placed on Place Vitrine within 25 m of the
   facade kills the closing shot. That is a hard constraint on set dressing that is very easy
   to violate accidentally, and nothing in the geometry protects it. It should be a checked
   gate before Beat 6 renders, not a note in a document.

7. **The elevation is real but lumpy.** 11.36 m of range concentrated into two ramps means
   the camera gets exactly two genuine dive/climb opportunities (Rampe du Fort and La
   Descente). Between them the track is within 1 m of flat for over a kilometre. A circuit
   that spread the same 11 m across four or five grade changes would give the camera more
   reasons to change altitude, at the cost of the two ramps being far less dramatic.

8. **The car crosses the finish line twice** — at 298 km/h entering the lap and 328 km/h
   closing it. That is deliberate and only 30 km/h apart. If the edit and the camera vantage
   do not clearly distinguish the two crossings, it will read as a continuity error rather
   than as bracketing.

9. **The build cost is materially higher than a parkland circuit.** The footprint is
   1,345 × 757 m and, because it is a city, there is no cheap distant terrain — every metre
   within 50 m of the camera path is buildings with windows, balconies, shutters, signage
   and street furniture. The brief forbids cheap far-side zones, and a street circuit has
   the largest possible amount of expensive near-side.

10. **The showroom is small for the distance it must read at.** Round 1's interior is
    30 × 22 × 6.5 m and I preserved it exactly rather than inflating it, which is correct for
    inventory fidelity but means the Beat-6 wound is 59 px in a 3840 px frame. It works, but
    there is no margin: if the destruction sim produces a tidier hole than the ~10 m I have
    assumed, the closing frame loses its subject.
