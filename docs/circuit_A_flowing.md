# Circuit A — **Vallon** · the flowing / natural-terrain layout

**Philosophy:** a road laid *over* a landscape, not carved into one. Every corner is the
consequence of a piece of terrain: a hairpin at the lip of the plateau, a plunge into a
valley, a rhythmic climb up the far side, a blind crest, a long sweeper wrapped round the
shoulder of a hill, a dip through a hollow on the way home. Spa/Suzuka lineage: long
sightlines, big radii, elevation doing the dramatic work.

**Everything below is measured, not asserted.** The centreline is a closed
straight/arc chain solved to exact closure (residual **0.0000 m** in position and
**0.0000°** in heading); the speed profile is a forward/backward point-mass solve over the
real curvature and gradient; the Beat 6 sight-line is a projected-frustum test, not a
guess. Generating scripts and raw data are listed in §9.

---

## 0. Headline numbers

| | value |
|---|---:|
| circuit length | **4 003.3 m** |
| corners | **15** (12–16 required) |
| predicted lap | **61.9 s** (55–65 s required) |
| average speed | 232.9 km/h |
| top speed | **335.6 km/h** (main straight, 275 m past the line) |
| speed crossing the S/F line | **326.0 km/h** |
| slowest apex | **82.4 km/h** (T1, the hairpin) |
| elevation range | **10.76 m** (−6.07 … +4.69) |
| steepest gradient | +2.88 % climb / −2.56 % drop |
| main straight | 960 m (520 m before the line + 440 m after) |
| plan footprint | 1 126 m (E–W) × 1 205 m (N–S) |
| closure residual | 0.0000 m / 0.0000° |

**World frame.** +X east, +Y north, +Z up. **Z = 0 is the showroom floor**, which is also
the paddock apron and the datum for the whole world. The showroom shell is the existing
round-1 geometry, unmoved: interior 30.0 × 22.0 m centred on the world origin, solid walls
at X = −15 and Y = +11, **glass curtain walls at X = +15 (facing +X) and Y = −11 (facing
−Y)**, ceiling 6.2 m. The car's nose points **+X**, so it launches straight at the X = +15
glass with no re-orientation of the round-1 scene.

---

## 1. Plan view

```
  PLAN VIEW    1 char = 30 m     X -160..1220     Y -820..380     (+X east, +Y north)

       1oo                                        1  T1  Source-de-Vallon   HAIRPIN
       o ooo                                      2  T2  Le Contre-Saut
       o   ooo                                    3  T3  Fond-de-Vallon
       o     o2oooooooo3o                         4  T4  Les Ondes 1  ]
       o                oo                        5  T5  Les Ondes 2  ]  ESSES
       o                 oo                       6  T6  Les Ondes 3  ]
       o                  o                       7  T7  Les Ondes 4  ]
       o                  oo                      8  T8  La Crete     BLIND CREST
       o                   o4                     9  T9  Grande Courbe A ] DOUBLE
       o                    ooooo                 A  T10 Grande Courbe B ] APEX
       o                        5o                B  T11 Le Fil
     S F                         oo               C  T12 La Combe
       o                          o               D  T13 Le Rappel
       o                          oo              E  T14 Les Vignes
       o                           6oo            G  T15 Grande Parabole
       o                             ooo
       o                                7         S  showroom (world origin)
       o                                oo        F  START / FINISH  (62, 0, 0)
       o                                 o
       o                                 o        The main straight is the WEST edge,
       o                                 oo       X = 62, cars running NORTH (+Y).
       o                                  o       Lap direction: CLOCKWISE.
       o                                  o       Infield lies EAST of the straight.
       o                                  oo
       o                                   o
       o                                   8
       o                                   o
       o                                  oo
       o                                  o
       G                                  o
       oo                                oo
        oo                               o
         oEo oooD                       9o
           ooo  ooo                    oo
                  ooo  ooooBooooo    ooo
                    Cooo        oooAoo
```

**Reading the shape.** From the line the car runs 440 m north on the plateau, brakes ~160 m
and throws it into **T1**, a 26 m hairpin right on the plateau's northern lip. Out of T1 it
runs east–south-east, kinks left at **T2**, then **La Plongee** drops it 3.7 m into the
valley and it arrives at **T3** at the bottom, a long fast right on the valley floor.
**T4–T7 (Les Ondes)** are the esses — four alternating corners that climb the far hillside.
**La Montee** is a 273 m straight climbing at 2.9 % to **T8 (La Crete)**, the blind crest
and the highest point on the circuit. Off the crest the road falls away into the
**Grande Courbe (T9/T10)**, a downhill double-apex right wrapped round the hill's shoulder
with an off-camber second apex. **La Crete-Ouest** runs west along the ridge — this is the
doppler-pass straight. **T11–T14** flow back down through the hollow (**La Combe**, the
lowest point of the return) and out over the vineyard rise, and **T15 (Grande Parabole)**
opens onto the 960 m main straight.

---

## 2. Corner table

Direction is the driver's. Entry speed is the peak in the 120 m preceding turn-in; apex
speed is the minimum through the arc. `z` is the centreline elevation at the apex.

| # | Name | Type | Dir | R (m) | Arc (m) | Turn (°) | Entry km/h | Apex km/h | Bank | z at apex (m) | Apex (x, y) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| **T1** | **Source-de-Vallon** | **hairpin** | R | **26** | 53.5 | 118 | 269 | **82.4** | +1.5 % | −0.91 | (74.6, 462.3) |
| T2 | Le Contre-Saut | kink | L | 105 | 55.0 | 30 | 236 | 203.0 | 0 % | −1.69 | (279.9, 371.3) |
| T3 | Fond-de-Vallon | fast sweeper | R | 130 | 118.0 | 52 | 281 | 246.3 | **+3.0 %** | −6.05 | (565.7, 364.4) |
| T4 | Les Ondes 1 | esse | L | 90 | 59.7 | 38 | 273 | 179.5 | +1.0 % | −5.51 | (725.0, 202.7) |
| T5 | Les Ondes 2 | esse | R | 80 | 69.8 | 50 | 213 | 164.6 | +1.5 % | −4.60 | (857.5, 161.8) |
| T6 | Les Ondes 3 | esse | L | 85 | 65.3 | 44 | 208 | 172.0 | +1.5 % | −3.60 | (935.3, 44.4) |
| T7 | Les Ondes 4 | esse | R | 110 | 107.5 | 56 | 224 | 211.1 | +1.0 % | −2.16 | (1080.5, −23.0) |
| **T8** | **La Crete** | **crest kink** | R | 135 | 80.1 | 34 | 295 | 255.9 | **−2.0 %** | **+4.63** | (1187.6, −371.2) |
| **T9** | **Grande Courbe A** | **sweeper, apex 1** | R | 145 | 111.4 | 44 | 300 | 276.3 | +4.0 % | +1.98 | (1094.7, −642.6) |
| **T10** | **Grande Courbe B** | **sweeper, apex 2** | R | 130 | 90.8 | 40 | 291 | 246.3 | **−1.5 %** | +0.90 | (922.4, −737.7) |
| T11 | Le Fil | fast kink | L | 125 | 56.7 | 26 | 287 | 237.1 | 0 % | −0.68 | (682.9, −698.1) |
| T12 | La Combe | medium | R | 110 | 96.0 | 50 | 274 | 211.1 | **+3.0 %** | −3.62 | (468.9, −737.4) |
| T13 | Le Rappel | medium | L | 115 | 84.3 | 42 | 237 | 219.5 | +1.0 % | −2.23 | (342.9, −668.0) |
| T14 | Les Vignes | fast | R | 120 | 113.1 | 54 | 251 | 228.2 | +1.5 % | −0.41 | (169.6, −665.6) |
| T15 | Grande Parabole | fast, opening | R | 120 | 88.0 | 42 | 245 | 228.2 | +2.5 % | +1.28 | (70.0, −563.0) |

Net turning: **−360.0°** exactly (clockwise). 7 rights, 4 lefts in the loop proper plus the
4-corner alternating esses. Corners occupy 1 249.4 m — **31 %** of the lap.

### The four required features, located

| requirement | delivered by | evidence |
|---|---|---|
| long main straight, ~330 km/h | S/F straight, 960 m (X = 62, Y −520 → +440) | peak **335.6 km/h**, 326.0 km/h at the line |
| heavy braking hairpin, ~80 km/h | **T1 Source-de-Vallon**, R = 26 m, 118° | apex **82.4 km/h**, entry 269 km/h, 160 m braking zone |
| esses complex | **T4–T7 Les Ondes**, L-R-L-R over 528 m | 164–211 km/h, links 75 / 75 / 75 m |
| fast double-apex sweeper | **T9/T10 Grande Courbe**, R 145 → 130 | 276 → 246 km/h, 98 m straightening between apexes |
| 8–12 m elevation | valley floor −6.07 to crest +4.69 | **range 10.76 m** |

---

## 3. Centreline geometry

### 3.1 Exact generative definition (this is the authoritative shape)

Start at **(62.000, 0.000, 0.000)** — the start/finish line — heading **+90.0°**
(due north; heading measured CCW from +X). Traverse in order. `L`/`R` is the turn
direction; a left turn adds to the heading, a right turn subtracts. Feed straight into a
Blender curve builder; it closes on itself exactly.

| # | element | type | length (m) | radius (m) | turn (°) | heading out (°) |
|---:|---|---|---:|---:|---:|---:|
| 1 | S/F straight, line → T1 braking | straight | 440.0 | — | — | +90.0 |
| 2 | T1 Source-de-Vallon | arc R | 53.5 | 26 | 118 | −28.0 |
| 3 | hairpin exit chute | straight | 175.0 | — | — | −28.0 |
| 4 | T2 Le Contre-Saut | arc L | 55.0 | 105 | 30 | +2.0 |
| 5 | La Plongee | straight | 200.8 | — | — | +2.0 |
| 6 | T3 Fond-de-Vallon | arc R | 118.0 | 130 | 52 | −50.0 |
| 7 | valley floor | straight | 140.0 | — | — | −50.0 |
| 8 | T4 Les Ondes 1 | arc L | 59.7 | 90 | 38 | −12.0 |
| 9 | esse link 1 | straight | 75.0 | — | — | −12.0 |
| 10 | T5 Les Ondes 2 | arc R | 69.8 | 80 | 50 | −62.0 |
| 11 | esse link 2 | straight | 75.0 | — | — | −62.0 |
| 12 | T6 Les Ondes 3 | arc L | 65.3 | 85 | 44 | −18.0 |
| 13 | esse link 3 | straight | 75.0 | — | — | −18.0 |
| 14 | T7 Les Ondes 4 | arc R | 107.5 | 110 | 56 | −74.0 |
| 15 | La Montee (climb to crest) | straight | 273.1 | — | — | −74.0 |
| 16 | T8 La Crete | arc R | 80.1 | 135 | 34 | −108.0 |
| 17 | crest run | straight | 193.5 | — | — | −108.0 |
| 18 | T9 Grande Courbe A | arc R | 111.4 | 145 | 44 | −152.0 |
| 19 | between apexes | straight | 98.0 | — | — | −152.0 |
| 20 | T10 Grande Courbe B | arc R | 90.8 | 130 | 40 | −192.0 |
| 21 | La Crete-Ouest (doppler pass) | straight | 170.0 | — | — | −192.0 |
| 22 | T11 Le Fil | arc L | 56.7 | 125 | 26 | −166.0 |
| 23 | descent | straight | 142.1 | — | — | −166.0 |
| 24 | T12 La Combe | arc R | 96.0 | 110 | 50 | −216.0 |
| 25 | combe link | straight | 55.0 | — | — | −216.0 |
| 26 | T13 Le Rappel | arc L | 84.3 | 115 | 42 | −174.0 |
| 27 | rappel link | straight | 76.8 | — | — | −174.0 |
| 28 | T14 Les Vignes | arc R | 113.1 | 120 | 54 | −228.0 |
| 29 | vignes link | straight | 45.0 | — | — | −228.0 |
| 30 | T15 Grande Parabole | arc R | 88.0 | 120 | 42 | −270.0 ≡ +90.0 |
| 31 | S/F straight, T15 exit → line | straight | 520.0 | — | — | +90.0 |

**Closes at (62.000, 0.000) heading +90.000°.** Total 4 003.3 m. (The column above sums to 4 003.5 m because each element is printed to 0.1 m; full-precision values are in `final.json` — use those, not the rounded table, when building the curve.)

Build note: joining arcs directly to straights gives a curvature step. Insert **clothoid
(Euler-spiral) transitions of 25–40 m** at every arc/straight junction, absorbed from the
adjoining straight so total length is preserved to within a metre. Without them the car's
steering and roll channels will step, and a 4K chase camera will read it.

### 3.2 Sampled control points (x, y, z) in metres

Sampled every 50 m plus every element boundary; `s` is distance along the centreline.
112 points. Feed directly to a Blender NURBS/poly curve.

```
   #          x          y        z         s   element boundary
   0      62.00       0.00     0.01       0.0   S/F straight (line -> T1 braking)
   1      62.00      50.00    -0.09      50.0
   2      62.00     100.00    -0.18     100.0
   3      62.00     150.00    -0.27     150.0
   4      62.00     200.00    -0.36     200.0
   5      62.00     250.00    -0.46     250.0
   6      62.00     300.00    -0.56     300.0
   7      62.00     350.00    -0.66     350.0
   8      62.00     400.00    -0.76     400.0
   9      62.00     440.00    -0.85     440.0   T1  Source-de-Vallon
  10      63.87     449.68    -0.87     449.9
  11     100.21     462.96    -0.99     493.5   hairpin exit chute
  12     105.50     460.14    -1.01     499.5
  13     149.65     436.67    -1.19     549.5
  14     193.80     413.19    -1.36     599.5
  15     237.95     389.72    -1.53     649.5
  16     254.72     380.80    -1.60     668.5   T2  Le Contre-Saut
  17     283.82     370.47    -1.71     699.5
  18     307.68     368.57    -1.79     723.5   La Plongee
  19     333.64     369.48    -1.88     749.5
  20     383.55     371.22    -2.41     799.4
  21     433.46     372.96    -3.68     849.4
  22     483.37     374.71    -4.96     899.3
  23     508.33     375.58    -5.52     924.3   T3  Fond-de-Vallon
  24     533.24     374.05    -5.81     949.3
  25     579.92     357.03    -6.06     999.3
  26     612.45     329.22    -5.98    1042.3   valley floor
  27     616.95     323.86    -5.97    1049.3
  28     649.09     285.56    -5.87    1099.3
  29     681.23     247.25    -5.77    1149.3
  30     702.44     221.97    -5.68    1182.3   T4  Les Ondes 1
  31     714.46     210.11    -5.59    1199.2
  32     752.67     191.79    -5.31    1242.0   esse link 1
  33     759.52     190.34    -5.27    1249.0
  34     808.43     179.94    -4.94    1299.0
  35     826.03     176.20    -4.83    1317.0   T5  Les Ondes 2
  36     855.12     163.59    -4.62    1348.9
  37     880.04     135.50    -4.36    1386.8   esse link 2
  38     885.67     124.91    -4.27    1398.8
  39     909.14      80.76    -3.92    1448.8
  40     915.25      69.28    -3.83    1461.8   T6  Les Ondes 3
  41     939.20      41.26    -3.56    1498.9
  42     964.03      28.35    -3.32    1527.1   esse link 3
  43     984.95      21.55    -3.13    1549.1
  44    1032.51       6.10    -2.69    1599.1
  45    1035.36       5.17    -2.67    1602.1   T7  Les Ondes 4
  46    1075.50     -18.18    -2.24    1648.8
  47    1103.57     -58.76    -1.44    1698.6
  48    1107.11     -69.12    -1.25    1709.6   La Montee
  49    1117.86    -106.62    -0.55    1748.6
  50    1131.65    -154.70     0.33    1798.6
  51    1145.43    -202.78     1.22    1848.6
  52    1159.22    -250.86     2.11    1898.6
  53    1173.00    -298.93     3.00    1948.6
  54    1182.38    -331.63     3.65    1982.7   T8  La Crete
  55    1185.87    -347.25     4.08    1998.7
  56    1184.63    -397.02     4.61    2048.7
  57    1181.00    -410.56     4.51    2062.8   crest run
  58    1169.85    -444.88     4.25    2098.8
  59    1154.36    -492.55     3.88    2149.0
  60    1138.87    -540.21     3.52    2199.1
  61    1123.38    -587.88     3.13    2249.2
  62    1121.22    -594.55     3.04    2256.2   T9  Grande Courbe A
  63    1102.02    -633.01     2.18    2299.4
  64    1066.76    -668.33     1.71    2349.5
  65    1051.39    -677.77     1.62    2367.6   between apexes
  66    1023.14    -692.79     1.46    2399.6
  67     979.00    -716.26     1.21    2449.6
  68     964.88    -723.77     1.13    2465.6   T10 Grande Courbe B
  69     933.21    -735.63     0.96    2499.5
  70     883.68    -737.42     0.70    2549.3
  71     876.82    -736.15     0.67    2556.3   La Crete-Ouest
  72     834.76    -727.21     0.45    2599.3
  73     785.85    -716.81     0.19    2649.3
  74     736.94    -706.42    -0.06    2699.3
  75     710.53    -700.80    -0.26    2726.3   T11 Le Fil
  76     687.84    -698.11    -0.60    2749.2
  77     654.30    -701.78    -1.12    2783.0   descent
  78     638.77    -705.66    -1.35    2799.0
  79     590.23    -717.76    -2.08    2849.1
  80     541.69    -729.86    -2.82    2899.1
  81     516.45    -736.15    -3.18    2925.1   T12 La Combe
  82     492.72    -739.38    -3.45    2949.1
  83     444.15    -729.48    -3.50    2999.1
  84     425.19    -718.41    -3.33    3021.1   combe link
  85     402.53    -701.96    -3.11    3049.1
  86     380.69    -686.09    -2.86    3076.1   T13 Le Rappel
  87     360.79    -674.48    -2.52    3099.2
  88     312.09    -664.13    -1.88    3149.4
  89     301.07    -664.75    -1.77    3160.4   rappel link
  90     262.37    -668.82    -1.37    3199.3
  91     224.65    -672.78    -0.98    3237.2   T14 Les Vignes
  92     212.67    -673.44    -0.86    3249.3
  93     164.01    -663.38    -0.35    3299.3
  94     123.61    -634.48     0.15    3349.3
  95     122.93    -633.74     0.16    3350.3   vignes link
  96      92.82    -600.30     0.63    3395.3   T15 Grande Parabole
  97      90.20    -597.28     0.68    3399.3
  98      66.78    -553.53     1.41    3449.3
  99      62.00    -520.00     1.73    3483.3   S/F straight (T15 exit -> line)
 100      62.00    -504.00     1.74    3499.3
 101      62.00    -454.00     1.57    3549.3
 102      62.00    -404.00     1.40    3599.3
 103      62.00    -354.00     1.23    3649.3
 104      62.00    -304.00     1.05    3699.3
 105      62.00    -254.00     0.88    3749.3
 106      62.00    -204.00     0.71    3799.3
 107      62.00    -154.00     0.53    3849.3
 108      62.00    -104.00     0.36    3899.3
 109      62.00     -54.00     0.19    3949.3
 110      62.00      -4.00     0.02    3999.3
 111      62.00       0.00     0.01    4003.3   (closes on point 0)
```

### 3.3 Elevation design

Terrain first, road second. Three landforms:

* **the plateau** (Z ≈ 0 … +1.8) — showroom, paddock, pit complex, the whole main straight.
  The straight falls gently 1.73 m over its 520 m approach to the line (−0.33 %), which is
  why the car makes 326 km/h at the line.
* **the valley** (Z ≈ −6.1) — floor of the north-east basin, reached by **La Plongee**
  (−2.56 % over 201 m) and left by the climbing esses.
* **the ridge** (Z ≈ +4.7 at T8) — the far hill, gained by **La Montee** at **+2.88 %**
  over 273 m, and given away again through the Grande Courbe.

Secondary undulation inside the same budget: **La Combe** dips to −3.6 m on the return leg
and **Les Vignes** rises back over a low vineyard swell, so the last sector breathes instead
of running flat.

| feature | z (m) | gradient into it |
|---|---:|---:|
| start/finish line | 0.00 | — |
| T1 apex (plateau lip) | −0.91 | −0.19 % |
| end of La Plongee | −5.52 | **−2.56 %** |
| **T3, valley floor (LOW POINT)** | **−6.07** | — |
| T5 / T6 / T7 (climbing esses) | −4.60 / −3.60 / −2.16 | +0.8 … +1.4 % |
| end of La Montee | +3.63 | **+2.88 %** |
| **T8 La Crete (HIGH POINT)** | **+4.69** | +1.6 % |
| T9 / T10 (falling sweeper) | +1.98 / +0.90 | −1.2 % |
| T12 La Combe (return hollow) | −3.62 | −1.7 % |
| T15 exit | +1.73 | +1.1 % |

Gradients are applied as smooth vertical curves (Hann-filtered over a 61 m window), so the
profile is C1 — no kinks for the chassis rig or the camera to catch.

---

## 4. Track, kerbs and run-off — to scale against the car

The car is **5.698 m long, 2.005 m wide, tyre-contact plane 0.340 m below its floor datum**.
Everything below is quoted in car widths so the scale is checkable by eye in a render.

| element | dimension | = car widths |
|---|---|---:|
| main straight width | 15.0 m | 7.5 |
| esses / Les Ondes width | 13.0 m | 6.5 |
| Grande Courbe width | 14.5 m | 7.2 |
| T1 hairpin width | 12.0 m | 6.0 |
| white edge line | 0.10 m, inside face flush with the kerb | — |
| entry/apex kerb | 1.20 m wide, 50 mm proud, 250 mm serration pitch, 1.0 m red/white alternation | 0.6 |
| exit ("negative") kerb | 0.80 m wide, −40 mm, 300 mm pitch | 0.4 |
| kerb-to-barrier minimum | 8.0 m | 4.0 |
| debris fence | 3.5 m above barrier top, 1.0 m TecPro / triple tyre stack below | — |

**Run-off, budgeted by where the car actually leaves the road:**

| location | run-off |
|---|---|
| T1, end of the 960 m straight | 45 m asphalt, then 12 m gravel, then TecPro |
| T3 Fond-de-Vallon (valley floor, 246 km/h) | 30 m gravel outside |
| T8 La Crete (over the blind crest) | 25 m gravel + 20 m asphalt — a car that runs wide here is airborne-adjacent |
| T10 Grande Courbe B (off-camber exit) | 35 m asphalt |
| T12 La Combe | 22 m gravel |
| everywhere else | 15–20 m grass with a gravel bed at the apex side |

Racing line offsets the centreline by up to **±4.2 m** (track half-width minus a car width
minus 0.4 m), tightening through apexes; the rubbered-in band is 3.6 m wide and follows the
line, not the centreline.

---

## 5. Showroom, paddock and the breach route

### 5.1 Placement — exact

| item | value |
|---|---|
| showroom shell | round-1 geometry, **unmoved**: interior 30.0 × 22.0 m centred on (0, 0), floor Z = 0, ceiling 6.2 m |
| solid walls | X = −15 (back), Y = +11 (side) |
| **glass curtain wall (the one that gets breached)** | the plane **X = +15**, spanning Y −11 … +11, 0 … 6.2 m tall, **outward normal +X (due east)** |
| second glass run | Y = −11, facing −Y — daylight source, not breached |
| turntable | dais r = 3.70 m at the origin, deck top (tyre-contact plane) **Z = +0.340** |
| car at rest | centred on the origin, **nose at X = +3.02**, pointing +X |
| **breach exit vector** | **+X, i.e. (1, 0, 0)**, at Y = 0, sill Z = 0 |
| launch run, nose to glass | **11.98 m** |
| paddock apron | Z = 0, flat, X 15 → 52, Y −60 … +320 |
| pit garages | X 26 … 42, Y +40 … +300, 9.0 m eaves — **north of the Beat-6 sight corridor** |
| pit lane / service road | centreline X = 46, 9.0 m wide, running north |
| pit wall | X = 54, 1.1 m |
| **START / FINISH LINE** | **(62, 0)** — dead ahead of the breach, 47.0 m from the glass |

**The showroom is broadside to the pit straight and its glass wall stares straight down the
start/finish line.** That single decision is what makes Beat 6 work (§5.3) and it is the
reason the building sits where it sits.

```
  PADDOCK INSET     1 col = 4 m (X)     1 row = 8 m (Y)

              P P       #  <- main straight, X = 62, cars northbound
              P P       #                 P = pit garages (X 26..42, Y 40..300)
              P P       #                 > = the car's route out of the building
              P P      >#                 # = circuit centreline
              P P     >>#
              P P    >> #                 pit-exit blend rejoins the circuit
              P P   >>  #                 at (62, +200)
              P P  >>   #
              P P >>    #
              P P>>     #
              P P>      #
                >       #
               >>       #
      |--------G>>      #
      |        >>>>>>>>>F  <- START/FINISH (62, 0)
      |        *           * = breach hole, glass wall X = +15
      |--------G           | = solid back wall X = -15
                #
                #
```

### 5.2 Route from breach to circuit (Beat 4)

| leg | geometry | length | speed |
|---|---|---:|---|
| launch, inside | dais → glass, along +X at Y = 0 | 11.98 m | 0 → ~68 km/h |
| **breach** | glass plane X = +15 | — | ~68 km/h |
| apron | straight, +X, (15, 0) → (18, 0) | 3.0 m | 68 |
| **Le Crochet** | left arc **R = 28 m, 90°**, centre (18, 28), exits (46, 28) heading +Y | 44.0 m | ~78 (R=28 supports 82) |
| pit lane | straight north along X = 46, Y +28 → +100 | 72.0 m | 78 → 150 |
| **pit-exit blend** | S-curve, two arcs **R = 160 m × 18.2°**, +16 m lateral over +100 m longitudinal | 101.7 m | 150 → 195 |
| **merge** | joins the circuit at **(62, +200)**, heading +Y | — | ~195 km/h |
| clear straight before braking | (62, 200) → (62, 278) | 78 m | 195 → ~215 |
| T1 braking zone | (62, 278) → (62, 440) | 162 m | 215 → 82 |

Total transit **220.7 m**, ~6.2 s of screen time. The car merges onto the circuit and is
immediately in the heaviest braking zone on the lap — which is exactly the order the brief
asks the camera to fly (chase → hairpin). Beat 4's dressing is all inside a 220 m corridor:
apron concrete, the pit garage row on the left, pit wall and catch fence on the right,
gantry over the merge.

The lap proper then runs T1 → … → T15 → 520 m of main straight → **line at 326 km/h**.
The car crosses the start/finish line exactly **once**, at the end of Beat 5 / start of
Beat 6, which is the cleanest possible reading of "one flying lap".

**Build note (a real defect waiting to happen):** the turntable deck top is at Z = +0.340
but the showroom floor is Z = 0. Left alone, the car launches off a 340 mm plinth and the
tyres lose rolling contact for two frames. Add a **dais delivery ramp** — 0.340 m rise over
2.6 m (13 %), from the dais lip at X = +3.70 out to X = +6.30, full 3.0 m width, matching
floor material. It is showroom-plausible furniture and it keeps the rolling-contact rule
intact through the launch.

### 5.3 The Beat 6 sight-line — solved, not hand-waved

**The constraint:** one frame must contain the car crossing the line *and* the breached
showroom, with the wound readable.

**The solution:** the finish line sits on the breach axis. The glass wall's outward normal
is +X; the finish line is at (62, 0); the wall centre is at (15, 0, 3.1). They are
**collinear along Y = 0, 47.0 m apart.** Any camera east of the line and roughly on that
axis sees the line in the near field and the wall face-on behind it. There is nothing in
between: the paddock apron is flat, empty and at the same Z = 0 as both.

**Verified camera:** position **(168, −62, 34)**, aimed at **(48, 8, 6)**, **40 mm** lens on
a 36 × 20.25 mm sensor (half-FOV 24.2° h / 14.2° v). Projected:

| target | h° off axis | v° off axis | distance | in frame? |
|---|---:|---:|---:|---|
| finish line (62, 0, 0) | +0.06 | −4.08 | 127.4 m | **yes** |
| showroom facade centre (15, 0, 3.1) | −8.06 | +0.69 | 168.0 m | **yes** |
| facade north edge (15, +11, 3.1) | −4.67 | +1.03 | 172.3 m | **yes** |
| facade south edge (15, −11, 3.1) | −11.61 | +0.32 | 164.2 m | **yes** |
| facade top (15, 0, 6.2) | −8.09 | +1.74 | 167.4 m | **yes** |
| breach hole centre (15, 0, 1.6) | −8.04 | +0.18 | 168.2 m | **yes** |

**On-screen size at 3840 × 2160:** facade **567 px wide** (14.8 % of frame width), breach
hole **108 px**, car at the line **197 px long**. The wound is unmistakable.

**Occlusion cleared.** The sight-line from the camera to the facade crosses the pit-building
band (X 42 → 56) at **Y = −10.9 … −16.6** and **Z = 8.6 … 11.4 m**. The garages start at
Y = +40 (51 m clear to the north) and are 9.0 m tall (well below the ray). The pit wall
(1.1 m) and debris fence (4.6 m top) at X = 54 pass 6.8 m beneath the ray. **Nothing
occludes.**

**Camera clearance.** (168, −62) is **106 m** from the nearest centreline point — the
closing wide hovers over open infield grass, not over track or run-off.

**Screen direction.** Camera forward is (−0.864, +0.504) in plan; the car's velocity at the
line is (0, +1); their dot with the camera-right vector is +0.864, so **the car streaks
frame-right and away** while the breached building holds frame-left in the distance.

**Light.** Sun at **azimuth 252° (WSW), elevation 13°** — late afternoon, shadows 4.3× object
height running ENE across the straight. The showroom's east facade is therefore in its own
shadow, and the breach reads as a **warm-glowing hole** (the Beat-1 spot rigs are still
burning inside) punched through a cool shaded glass wall, with the spilled shard field on
the apron catching the low western sun as a glitter band. That contrast, not raw pixel size,
is what sells the wound at 168 m.

---

## 6. Camera note per beat — what *this* layout gives that another would not

**Beat 1 — assembly.** The layout contributes one thing and it matters: the breached wall is
the **east** glass, so the ~13° west sun rakes in through the **south** glass run (Y = −11)
across the turntable, while the east wall stays a dark mirror. The exploded field
(9.84 × 4.49 × 5.96 m, per the inventory) therefore sits against a dark east wall for the
whole beat — every part in the field gets edge separation from a *dark* background rather
than fighting a blown-out window, and the camera can weave the field on any heading without
flaring. It also means the wall the car is about to destroy is, for 35 seconds, the
least-interesting surface in frame. That is deliberate.

**Beat 2 — ignition and launch.** 11.98 m from nose to glass, dead straight along +X with
the turntable's 3.70 m dais lip 0.68 m ahead of the nose. That is a short, brutal run: the
camera tucked low beside the left-rear tyre gets wheelspin, the ramp step, and the wall
filling the lens inside a second, with no room for the shot to become a "drive". A longer
run would turn a launch into a commute.

**Beat 3 — the breach.** Outside the glass there is **39 m of flat, empty, Z = 0 apron**
before the barrier line — the camera can complete a full ground-level arc around the erupting
shard field without ever finding a wall, a kerb or a slope. Because the apron is dead flat
and the same height as the floor, shards that skitter *out* through the hole keep travelling
on the same plane they started on: no ledge for the sim to argue with, and the debris field
stays in frame for the entire arc. The breach axis points at the finish line, so even during
the speed ramp the background of the arc is the circuit — the destination is visible from
inside the destruction.

**Beat 4 — transit.** 220 m, three distinct geometric events (a 28 m hook, a 72 m pit-lane
straight between garage doors and pit wall, a 100 m S-blend under a gantry) and a merge that
delivers the car straight into the braking zone. The camera pulls up and back through the
hook — the hook's 28 m radius means the car *rotates* under the lens rather than translating,
which is the cheapest way to sell speed while the car is actually still slow.

**Beat 5 — the lap.** The corner sequence was ordered to match the brief's camera list, in
order, with no cheating:

| brief's camera move | where the layout puts it | s (m) | screen time |
|---|---|---|---|
| swoop from chase to low kerb-height at the hairpin | **T1**, R = 26 m, 82 km/h apex, 118° of rotation | 440 – 494 | ~2.6 s |
| helicopter arc through the esses | **T4–T7**, 528 m of L-R-L-R at 165–211 km/h | 1 182 – 1 710 | ~10.6 s |
| (bonus) blind crest | **T8**, +2.88 % into a −1.3 % fall | 1 983 – 2 063 | ~1.1 s |
| (bonus) speed ramp at the fastest apex | **T9**, 276 km/h, +4 % banking, suspension loaded | 2 256 – 2 368 | ~1.5 s |
| near-static trackside doppler pass, ≥ 3 s | **T10 exit → La Crete-Ouest → T11**, 318 m of ridge at ~245 km/h with clean sightline both ways | 2 466 – 2 783 | **4.7 s** |
| tight onboard-like follow at ~330 km/h | **S/F straight**, 520 m, 228 → 326 km/h | 3 483 – 4 003 | ~6.9 s |

What the elevation buys the camera specifically:

* **T1 is on the lip of the plateau.** A camera at kerb height at the hairpin apex has the
  whole valley behind the car — the background falls away 5 m, so the car is silhouetted
  against distant terrain rather than against tarmac. On a flat circuit that shot has a
  guardrail behind it.
* **La Plongee gives the camera somewhere to dive from.** 201 m of −2.56 % with the road
  visible all the way to T3: a drone can drop 4 m while the car drops 3.7 m and the horizon
  line rotates through frame.
* **La Montee is the only place the camera can rise on the car's own energy.** Climbing at
  +2.88 % with the crest hiding the exit, a low chase camera loses the car over T8 for ~10
  frames — a free, physically-motivated "reveal" with no cut.
* **The Grande Courbe is downhill and off-camber at the second apex.** The camera arcing
  outside it looks *down* onto a car that is visibly unsettled (−1.5 % camber at 246 km/h).
  A flat sweeper gives a photogenic but inert image; this one has the car working.
* **La Crete-Ouest is on a ridge.** The doppler-pass camera at ground level there has 300 m
  of clean approach and 200 m of clean departure with sky behind the car in both directions,
  because the land falls away on both sides. That is what makes a *near-static* 4.7 s hold
  survivable — the car is legible for the whole pass.

**Beat 6 — the closing wide.** §5.3 in full. The one-sentence version: **the finish line was
placed on the breach axis**, so the closing camera does not have to compromise between the
car and the building — they are 47 m apart and collinear, and a 40 mm lens at (168, −62, 34)
holds both with the facade at 567 px and the wound at 108 px.

---

## 7. Speed profile and lap-time reasoning

Forward/backward point-mass solve over the actual curvature and gradient, iterated to
wrap-around convergence.

* mass 800 kg (car + driver + fuel), drivetrain 720 kW, drag coefficient tuned so
  terminal velocity ≈ 95 m/s
* lateral capacity `a_lat = min(1.85 + 3.889e-4·v², 5.2)·g` — 2.2 g at 108 km/h rising to
  the 5.2 g cap by ~300 km/h, matching real high-downforce cornering (Pouhon ≈ 4.3 g,
  130R ≈ 5.0 g)
* traction limit 1.55 g; braking `min(1.25 + 2.2e-4·v², 5.0)·g` plus drag, giving a 162 m
  braking zone from 335 → 82 km/h (Monza's T1 zone is ~130–150 m — this is the right order)
* gradient term `−g·dz/ds` applied throughout, so the downhill straight and the uphill
  La Montee are both in the numbers

**Result: 61.88 s over 4 003.3 m — 232.9 km/h average.**

**Sanity check against reality.** Spa averages 242 km/h, Silverstone 244, Interlagos 222,
Zandvoort 219. A 4.0 km circuit with one 26 m hairpin, four medium esses and five
200 km/h-plus corners averaging 233 km/h is squarely in that band. The number was *not*
chosen — length was solved from the corner geometry and the lap time fell out; had it landed
outside 55–65 s the corner set would have changed, not the target.

**Screen time.** 61.9 s of lap sits inside Beat 5's 55–65 s window with no time-remapping
needed. With Beats 1–4 at ~48 s and Beat 6 at ~9 s the total lands near **119 s**, inside the
100–130 s delivery. The two optional speed ramps (T9 apex, and the breach ramp in Beat 3)
*add* screen time, so the budget has headroom in the right direction.

Full per-element speeds are in the table of §2 and the segment dump in §9.

---

## 8. Honest weaknesses

1. **The gradients are modest and always will be.** 10.76 m of range spread over 4 003 m
   caps the steepest grade at **2.88 %**. Spa's Raidillon is 17 %. I concentrated the budget
   into three features (La Plongee, La Montee, the descent to La Combe) and kept the rest
   genuinely flat so those three read — but the "blind crest" at T8 hides the car only from a
   **low chase camera**; from any helicopter vantage the car is never hidden. Anyone reading
   "natural terrain" as "Eau Rouge" will be disappointed, and no arrangement of an 8–12 m
   budget over 4 km fixes that.

2. **The footprint is large and sparse.** 1 126 × 1 205 m for 4.0 km of track. A real circuit
   with that footprint would be 5.5–6 km. The infield east of the straight is largely empty,
   and the terrain between the esses and the Grande Courbe is a lot of hillside to model for
   very few frames. Dressing budgeted by distance-to-path helps, but the landmass itself is
   unavoidable and it is the single biggest build cost in this design.

3. **Beat 4 is short — 220 m, ~6.2 s — and that is a direct price paid for Beat 6.** Because
   the breach exit vector (+X) is *perpendicular* to the main straight, the car needs a 90°
   hook to join it, and a 90° hook fits in the 37 m paddock corridor only at R = 28 m, taken
   at ~78 km/h. So the car has to lift almost immediately after the launch. Yawing the
   showroom 90° so the breach fired *along* the straight would give a long, fast, elegant
   Beat 4 — and would push the building 300 m+ from the line, shrinking the facade in Beat 6
   from 567 px to ~160 px. I chose Beat 6 because the brief calls that sight-line a hard
   constraint and Beat 4's duration "approximate". It is a real trade and I lost something
   real on it.

4. **The main straight is 960 m — 24 % of the lap in one line.** That is a Monza proportion
   inside a circuit that claims Suzuka ancestry. It is what 330 km/h plus a pit-exit merge
   with usable room before T1 costs. The straight is the least "flowing" thing here.

5. **T11–T14 are four similar corners.** R = 125 / 110 / 115 / 120, apexes at 237 / 211 / 220
   / 228 km/h. A driver would fairly say three of them are the same corner. I gave T12 the
   La Combe hollow and T14 the vineyard rise so the *camera* can tell them apart by elevation,
   but the plan geometry of the return leg is the weakest quarter of the layout and it is the
   part most likely to feel like filler on screen.

6. **T9/T10 as a "double apex" is a judgement call.** 98 m of straightening between the two
   arcs is enough that a purist would call them two corners, not one double-apex. I kept the
   gap because at 276 km/h a shorter link makes the second apex un-takeable without lifting,
   which would have cost the sweeper its speed.

7. **The speed model is a 2D point mass.** No friction ellipse (lateral and longitudinal
   capacity are not traded against each other), no banking contribution to grip, no tyre
   thermal state, no aero balance shift under braking. Corner entry and exit speeds are
   therefore optimistic by a few km/h each, and the honest error bar on 61.9 s is about
   **±3 s**. It is good enough to prove the layout fits the 55–65 s window; it is not a
   lap-time simulation.

8. **The elevation profile is interpolated and smoothed, not designed as vertical curves.**
   Hann-filtering the keyframed z over a 61 m window means realised apex elevations differ
   from the design intent by up to ~0.3 m and the T8 crest is slightly gentler than the key
   values imply. A proper parabolic vertical-curve set should replace this before the terrain
   mesh is built.

9. **The clothoid transitions are specified but not solved.** §3.1 asks for 25–40 m Euler
   spirals at 30 arc/straight junctions; the control points in §3.2 are sampled from the pure
   arc/straight chain. Whoever builds the curve must insert them and re-derive the sample
   table, and the length will move by a metre or two.

10. **The showroom is only ever seen twice.** Nothing on the circuit comes back within 100 m
    of the building except the main straight. The "one world" promise is honoured
    geometrically, but experientially it is a corridor plus a large loop, and the wounded
    building is out of sight from ~0:42 to ~1:50. If that gap reads as two worlds stitched
    together, this layout is the reason.

---

## 9. Provenance

Everything numeric here was produced by, and can be regenerated from, the solver scripts in
the session scratchpad:

```
scratchpad/circA/final.py     centreline closure (projected least-squares over the straight
                              lengths), elevation keys, forward/backward speed profile
scratchpad/circA/extract.py   corner table, control points, Beat-6 frustum test,
                              occlusion and camera-clearance checks
scratchpad/circA/*.npy        sampled centreline P, arclength S, curvature K, elevation Z,
                              speed V, heading H  (1 m sampling, 4 004 points)
scratchpad/circA/final.json   segment list + spans + lap time + length
```

One bug is worth recording because it invalidated three earlier candidate layouts before it
was caught: the arc integrator placed the turn centre 90° to the **left** of the heading for
*both* turn directions, so every right-hand corner was drawn as its mirror image. The closure
algebra (which used the correct signed chord formula) reported a perfect closure while the
drawn path ended 480 m away from the start. Corner directions, footprint and self-intersection
results from before that fix are all void. The current path closes in both the algebra
**and** the integration, at (62.000, 0.000) heading +90.000°, and the minimum separation
between non-adjacent centreline points is 146.6 m — no self-intersection, no
uncomfortably-close parallel sections.
