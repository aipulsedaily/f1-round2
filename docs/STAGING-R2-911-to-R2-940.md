# STAGING R2-911 … R2-940 — THE DECK RIDE: THE CONTACT SURFACE DOES NOT EXIST

*Staged, not logged. `docs/DEFECT-LOG-R2.md` is not edited by this block.*

Everything below is measured off tables already on disk. **No bake was run and
nothing was rendered, so this block spent $0.00.** The one instrument it adds is
`sim/ridecontact.py`, standard library + numpy, no Blender.

---

## R2-911 — THE FOURTH HYPOTHESIS DIES, AND IT TAKES THE QUESTION WITH IT. NOTHING IS TOUCHING THE CAR — CLOSEST APPROACH **287 mm**, AGAINST A COLLISION MARGIN OF **0.15 mm**

R2-707's last words were *"let me find what it IS touching."* The answer is
**nothing**, and this is the measurement rather than an inference.

`sim/ridecontact.py` rebuilds all **152** structural colliders from the same file
`build_breach_sim.py` builds them from, puts them at the baked transform, and
solves the exact convex separation against all **18** parts of
`breachlib.car_proxy_parts()` — the same eighteen the sim collides, transformed
by the same six curves.

```
breach_film_R2387.npz   f967-f977 at 0.1-frame steps (101 samples), solid wing
   body              MIN GAP    median     at f   clz_lo      clx  nearest car part
   MUL05_S02_P        0.2870    0.3169    967.0    1.267    -2.19  wing_r
   MUL05_S02          0.2914    0.3102    967.0    1.270    -2.10  wing_r
   TRN_z0_b04         0.3753    0.4318    967.0    0.737    -2.37  rep_r
   TRN_z0_b05         0.3873    0.4120    967.0    0.188    -2.63  rep_l
   TRN_z0_b05_P       0.4132    0.4390    967.0    0.280    -2.69  rep_l
   TRN_z0_b04_P       0.5052    0.5608    967.0    0.846    -2.38  rep_r
   MUL05_S01_P        0.7614    0.7628    969.9    1.715    -1.94  rep_l
   MUL05_S01          0.7676    0.7702    973.3    1.718    -1.85  rep_l
   MUL05_S00_P        1.3348    1.3409    969.1    2.164    -1.69  rep_l
   MUL05_S00          1.3420    1.3457    970.0    2.163    -1.60  rep_l
   bodies in CONTACT with the car (gap <= margin 0.00015 m): 0
   CERTIFIED LOWER BOUND on that closest approach: 0.2870 m
>> STAGE RESULT: RIDECONTACT_R2387 NO_CONTACT (closest 0.2870 m)
```

**Every one of the eight bodies `ridepose` calls *aboard* is between 0.29 m and
1.34 m clear of the nearest piece of car**, at every one of 101 sub-frame
samples across the peak window. The lowest corner of the nearest body sits at
car-local **z = 1.267**, which is **275 mm above `CAR_TOP_Z` = 0.992**. There is
no contact surface because there is no contact.

**And the margin the refutations were argued against was the wrong one.**
R2-707 cleared the rear wing at "60 mm against a 40 mm collision margin".
40 mm is *Blender's default*. `build_breach_sim.MARGIN` is **0.00015 m** and the
scene sets `use_margin` on every body explicitly, with a comment saying why. So
R2-707's refutation of the tray is **266 times stronger than it claimed** — and
so is this one. Nothing in the argument turns on it; it is recorded because the
next person to reason about clearance in this sim will otherwise reach for 40 mm
again.

### The instrument, and the control that makes it a measurement

* **The collider rebuild is checked against the table, not trusted.** All 152
  rebuilt box centres are compared with the baked table's own rest pose:
  `0 disagree by > 1 mm`, and `max |rest quaternion − I| = 0.0e+00` exactly.
  A rebuild that reproduces 152 independent rest positions to the millimetre is
  not a re-derivation of the geometry, it *is* the geometry. The run **refuses**
  if any box misses.
* **Every separation carries a dual certificate.** `hull_distance` returns the
  minimum-norm point of the Minkowski difference AND the gap of the separating
  plane normal to it. Upper and lower bound agree at the reported minima.
* **It is sampled between film frames.** Contact is an event, not a pose. At
  0.1-frame steps the 287 mm is a statement about the *continuum* of the window,
  not about eleven instants in it.

---

### The demonstration

`render/r2911/DEMO_f0972_chain_is_not_touching.png` — the delivered R2387 frame
at f0972 with the six-body chain (**red**) and all eighteen parts of the car's
collider (**cyan**) drawn over it, through the same camera track. The red boxes
land exactly on the pale bar the eye objects to, which is the identification;
the cyan cage shows where the car actually is; and the **yellow** stub is the
shortest link between them. *(The yellow is a vertex-to-vertex witness at
0.3104 m, drawn so it is visible; the certified face-to-face minimum over the
window is 0.2870 m. The picture is the demonstration, the number is R2-911's.)*

The bar crosses the entire car and touches none of it.

---

## R2-912 — A TEXTBOOK GJK RETURNS 0.000 FOR THE PROXY'S TYRE RINGS, AND IT DID, ON THIS DATA, BEFORE ANY CONCLUSION WAS DRAWN FROM IT

The first pass of this measurement reported `CAR:tyre_RL 0.000` at f973 — a
contact, on the frame after the one R2-700 judged. It was false. The true
separation is **0.9474 m**, and the failure is structural rather than unlucky:
`car_proxy_parts()` builds each tyre as two 16-gon rings, 32 near-coplanar
points, and the simplex sub-distance routine degenerates on them and terminates
claiming the origin is enclosed.

**What caught it was not a test.** It was asking the solver for a *certificate*:
any direction `d` gives `min_A d·a − max_B d·b` as a valid lower bound, and
0.947 > 0 refutes the 0.000 immediately. The solver was then replaced with a
pairwise Frank–Wolfe minimum-norm-point method that returns both bounds, and
`--selftest` carries the tyre case as a named control:

```
   TYRE       a 16-gon ring 4 m from a box reads 4.000  4.000000  OK
```

**Had the certificate not been asked for, this block would have reported that
the member rides the left rear tyre** — a fourth named mechanism, plausible,
publishable and wrong, on the frame next to the one the whole defect is
argued from. A gate that answers "is it touching?" cannot tell you the
answer never converged.

---

## R2-913 — IT IS NOT A MEMBER. IT IS **SIX BODIES**, 2.325 m OF MULLION, STILL BOLTED TOGETHER, AND THE JOINTS HOLD TO **1 mm** THROUGH THE WHOLE RIDE

`ridecontact --silhouette` finds the still-joined set by measurement rather than
by being told: a pair whose centre-to-centre distance stays within 20 mm of its
value in the intact wall for the whole window has a constraint that never broke.

```
the STILL-JOINED CHAIN containing MUL05_S02 is 6 bodies:
   MUL05_S00 MUL05_S00_P MUL05_S01 MUL05_S01_P MUL05_S02 MUL05_S02_P
```

Over **f900–f1051**, in every bake:

| pair | intact-wall distance | max deviation over the ride |
|---|---:|---:|
| `MUL05_S00 – MUL05_S01` | 0.7750 m | **0.0011 m** |
| `MUL05_S01 – MUL05_S02` | 0.7750 m | **0.0012 m** |
| `MUL05_S02 – MUL05_S02_P` | 0.0925 m | **0.0012 m** |
| `MUL05_S02 – MUL05_S03` | 0.7750 m | 20.88 m — **this** is where it broke |

So `CON_MUL05_J00`, `CON_MUL05_J01` and all three plate joints survive the
event; only `J02` fails. **The object in the picture is the bottom 2.325 m of
mullion 5 — three segments and three pressure plates, 10.9 kg — flying as one
articulated stick.** Projected at f972 it is a single unbroken diagonal:

```
   MUL05_S00 / _P   screen x  508- 894   car-local z 2.17..2.68   depth 2.49 m
   MUL05_S01 / _P   screen x  854-1156   car-local z 1.73..2.24   depth 2.92 m
   MUL05_S02 / _P   screen x 1110-1355   car-local z 1.29..1.80   depth 3.42 m
                    (screen coordinates at 1920x1080)
```

R2-384 called this "MUL05_S02", R2-700 called it "one pale structural member",
R2-707 called it "the member". **Every mechanism proposed for it was a mechanism
for a 0.775 m bar, and the thing on screen is three times that long and six
times that many bodies.** The chain is not a defect in itself — a curtain-wall
mullion *is* a continuous 6.2 m extrusion and cutting it into eight segments is
a modelling device, so segments that stay joined are more physical than segments
that do not. But it is what makes the object read as one large still thing, and
it is why every mechanism aimed at "the member" was aimed at the wrong body:
the thing that has to be moved is **10.9 kg and 2.325 m long**, six bodies
rigidly linked, not the 3.6 kg segment whose name the defect is filed under.
Whether that changes the arithmetic of the 26.54 N·s figure is not measured
here and is not claimed.

---

## R2-914 — WHAT THE EYE WAS ACTUALLY SEEING: THE CHAIN FLIES **BETWEEN THE LENS AND THE CAR**, FOR **16 FRAMES**, AND THE PEAK WINDOW R2-700 PICKED BY EYE IS EXACTLY THAT EVENT

This is the finding. Contact was never the question; **depth order** was.

Through the ONER track, over the peak window, for the chain of R2-913:

| bake | R2-700's verdict by eye | chain screen extent @4K | in front of the car's nearest surface by | chain car-local z | verdict |
|---|---|---:|---:|---|---|
| **R6 SHIPPED** | wrong, car emerges pristine | *148 bodies still joined — the wall never broke* | — | — | **VACUOUS** |
| **R2281 RE-BAKE** | reads as an accident — **accept** | 1,417 px | **−0.83 m** (behind) | 0.99 … 1.32 | `BEHIND_OR_ON` |
| **R2387 AIR** | reads as broken — **reject** | **1,893 px** | **+0.23 m** (in front) | 1.27 … 2.70 | **`FOREGROUND_BAR`** |
| **R2701S** solid control | — | **1,893 px** | **+0.23 m** | 1.27 … 2.70 | **`FOREGROUND_BAR`** |
| **R2701A** aerofoil | not yet judged by eye | 1,470 px | **−1.04 m** (behind) | 0.28 … 0.88 | `BEHIND_OR_ON` |

**Two independent statistics reproduce R2-700's ordering and neither of them is
a contact measurement.** The rejected bake's chain is 34 % longer on screen than
the accepted one's, and it is the only bake in which the chain is *nearer the
lens than any part of the car*. At f972 it sits at 2.96 m depth against the
car's nearest surface at 3.20 m — a foreground object drawn diagonally across
89 % of its own screen box's worth of car.

**And the event is 16 frames long, f969–f984.** Over the whole ride f900–f1051:

```
                frames with the chain BETWEEN LENS AND CAR      peak chain px
R2387                        16   (f969-f984)                        1,951
R2281 RE-BAKE                 0                                      1,581
R2701A aerofoil               0                                      1,501
```

**R2-700 chose f0967–f0977 as "the peak" from the pictures, before any of this
was measured. It lands on top of a 16-frame foreground crossing that exists in
one of the three bakes and in neither of the others.** That is the strongest
evidence in this block that the eye was reacting to depth order and not to
contact, and it is evidence nobody arranged.

The 1,893 px also identifies the brief's own headline: **the "1,879 px" that the
ride subtends is the screen extent of this six-body chain**, not of a member.

### Why it reads as *at rest*, which is a separate question and has a separate answer

Two numbers, both of which are about the beat's clock rather than about contact:

* the chain's own rotation is **269.6 deg/s of WORLD time** — at beat 3's ramp
  floor of 0.153719 that is **1.73 deg per FILM frame**;
* it separates from the car at **4.22 m/s** while the car does **23.25 m/s**, so
  **82 % of its screen motion is the car's**.

A 10.9 kg, 2.3 m stick tumbling at a perfectly ordinary 270 deg/s is *pinned* in
a beat photographed at 6.5× slow motion. `ridepose`'s own-motion ratio measures
that inertia, correctly, and then attributes it to a pose. Nothing in the
contact model can move either number.

---

## R2-915 — THE ACCEPTANCE CRITERION IS SATISFIED BY THE BAKE THE EYE REJECTS AND VIOLATED BY THE ONE IT ACCEPTS

R2-700, in words: *"nothing may come to rest on top of the car."* Measured
literally, at the margin the sim actually uses:

```
breach_film_R2281_REBAKE.npz  f967-f977   <- the bake the eye ACCEPTS
   MUL05_S00     0.0000 m from  airbox    at f975.8   car-local z 0.990
   TRN_z0_b05    0.0000 m from  tyre_RL   at f967.8   car-local z 0.099
   TRN_z0_b04    0.0065 m from  tyre_RR
   bodies in CONTACT with the car: 2
>> STAGE RESULT: RIDECONTACT_R2281_REBAKE CONTACT (closest 0.0000 m)

breach_film_R2387.npz         f967-f977   <- the bake the eye REJECTS
   bodies in CONTACT with the car: 0      closest 0.2870 m
>> STAGE RESULT: RIDECONTACT_R2387 NO_CONTACT (closest 0.2870 m)
```

**A mullion segment is lying on the airbox at zero separation in the bake R2-700
called "reads as an accident — accept", and nothing is within 287 mm of the car
in the bake it called "reads as broken — reject".** R2-384's headline — *"161
film frames on the car's airbox"* — is true of R2281 and false of the production
table it was written to condemn.

So the criterion, as a sentence about contact, does not order these bakes; it
orders them **backwards**. It has to be restated, and the restatement is the
only part of this that is a judgement rather than a measurement:

> **Debris may lie on the car. What it may not do is fly between the lens and
> the car, long and straight, at the car's own speed.** The defect is a
> depth-order and screen-extent property of the silhouette, not a contact
> property of the bodywork.

That is what `RIDESILHOUETTE_*` gates, and it reproduces every verdict R2-700
made by eye, including `VACUOUS` for R6 — where the chain search returns **148
bodies still joined at 20 mm**, which is not a chain but an intact wall, and is
the correct signature of a bake that nothing came off.

---

## R2-916 — `--rear-wing aerofoil` IS THE FIX, AND R2-707 WAS RIGHT THAT ITS STATED MECHANISM IS FALSE

Both are true at once and the combination is the interesting part.

R2-707 refuted the tray: at 240 Hz the member never comes within 60 mm of the
solid wing. R2-911 strengthens that — in the solid bake the closest any
structural body gets to `wing_r` is **287 mm**, and the collision margin is
0.15 mm rather than the 40 mm the refutation was argued against. **The
mainplane's 58.6 % thickness is not holding anything up, and never was.**

And the aerofoil cell fixes the defect anyway:

| | R2387 / R2701S (solid) | **R2701A (aerofoil)** |
|---|---:|---:|
| frames with the chain between lens and car, f900–1051 | **16** | **0** |
| chain screen extent, peak window | 1,893 px | **1,470 px** |
| depth relative to the car's nearest surface | **+0.23 m in front** | **−1.04 m behind** |
| chain car-local z | 1.27 … 2.70 | **0.28 … 0.88** (below `CAR_TOP_Z`) |
| closest approach to the car | 287 mm | **4.1 mm** — genuinely alongside |
| nearest parts | `wing_r`, `rep_l` (nothing near) | `tyre_RR`, `cover`, `rep_l` |
| `ridepose` "across" | 0.41 – 0.81 (transverse) | **0.28** (pointing where the car is going) |

The aerofoil cell lands on the accepted side of **both** silhouette statistics,
with a larger margin than R2281 has, and it puts the chain *below the deck line
and alongside the rear tyre* — which is R2-700's "travelling alongside, tumbling
or trailing is fine and wanted", arrived at from a different direction.

**R2-702's P30, P34 and P36 all resolve, and P31 does not.** The tray does
release (16 foreground frames → 0). The "across" statistic falls from 0.41–0.81
to 0.28, exactly as P34 predicted, "because what makes a bar lie transversely is
being stopped square-on by a full-width leading face". P36's slot does not open:
the chain ends up at z 0.28–0.88, under the mainplane band, not wedged in it.
P31 fails — `ridepose` still returns FAIL on the aerofoil cell at ratio 0.067 —
and R2-914 is the reason: the own-motion ratio is reading a 10.9 kg stick's
inertia at a 6.5× slow-motion clock, which no change to the collider can move.

**So the recommendation is to adopt `--rear-wing aerofoil`, on evidence that has
nothing to do with the argument that produced it.** A lever chosen for a reason
that turned out to be false still moved the thing it was aimed at, and that is
worth saying out loud rather than quietly re-justifying.

### What this recommendation does NOT rest on, said before anyone asks

* **One seed — and THERE IS NO SEED TO VARY.** R2-700 asks any A/B on this beat
  for more than one. `build_breach_sim.py` has **no `--seed` argument**: the only
  `seed` in the file is `1000*bay + s["id"]`, the deterministic Wallner ripple on
  a shard's mesh, which is geometry rather than a realisation. **The multi-seed
  requirement is not currently satisfiable, and nobody has said so.** The nearest
  honest substitute is `--substeps` (default 8) or `--solver-iter` (default 24):
  changing either re-integrates the same physics down a different numerical path,
  which is exactly the role a seed plays for a chaotic degree of freedom, and
  changes no declared parameter. **A pair of cells at `--substeps 12`, aerofoil
  and solid, is the check that closes this**, and if the 16-frame foreground
  count survives it the result is no longer one realisation's.
  **Cost: R2-704 prices this pair at ~2.5 instance-hours; the 5090 is currently
  torn down (`rq status`: `gpu down, instance=None, $0.4654/hr`), so it is a
  fresh rental at ≈ $1.20 plus spin-up. Not queued here** — the GPU being down
  makes it a rental decision rather than a slot on a running box, and nothing in
  this block was authorised to spend.
* **No pixels.** R2-700's three verdicts were made on renders. There is no
  render of the aerofoil cell. Every figure above is geometry through
  `sim/out/oner_camera_track.json`, which is verified current below — it is the
  right instrument for depth order and screen extent and it is *not* a
  substitute for seeing it.
* **A 1920 still at f0972 from the aerofoil table** needs `apply_breach.py`
  against `film16`/`film17` (7.5 GB) plus one frame — the apply is the expensive
  half and it is hours, not dollars. Worth doing on the next world rebuild,
  where the scene is open anyway (`docs/NEXT-REBUILD.md`), not on its own.

---

## R2-917 — THE CAMERA TRACK IS STILL CURRENT, RE-CHECKED AGAINST `film17` WHICH WAS BUILT TODAY

R2-706 verified `sim/out/oner_camera_track.json` against `film16` on 4 August.
`render/film17_path.json` was written **today at 05:20**, and
`render/film_path_R2581B_ramp_RETUNED_REBASED.json` at 05:00 — a beat-3 *ramp*
candidate, which is exactly the file that could have invalidated every pixel in
this block. It does not:

| | max Δposition | max Δquaternion | max Δlens |
|---|---:|---:|---:|
| `film16` vs `film17`, beats 1–2 f1–864 | 9.234 m | 1.654 | 23.00 mm |
| `film16` vs `film17`, **beat 3 f865–1056** | **0.000e+00** | 1.0e−06 | **0.000e+00** |
| **sim track** vs `film17`, **judged f940–1060** | **5.0e−06 m** | 8.8e−07 | 5.0e−05 mm |
| **sim track** vs `film17`, **peak f967–977** | **4.9e−06 m** | 8.8e−07 | 4.4e−05 mm |
| **sim track** vs the R2581B ramp candidate, **peak** | **4.9e−06 m** | 6.4e−07 | 4.4e−05 mm |

All of the movement is beats 1–2, which is the re-pacing work. **5 µm at 3 m is
0.006 px at 4K.** The 1,893 px, the +0.23 m and the 16-frame count are all
measured through a camera that is bit-identical to the film being built right
now, and the ramp candidate would not move them either.

---

## R2-918 — WHAT IS NOT SETTLED, LISTED SO IT IS NOT REDISCOVERED AS AN OVERSIGHT

* **Glass is not measured.** `ridecontact` covers the 152 structural bodies and
  refuses to guess at 3,796 shard hulls, whose geometry is not reconstructible
  from a declaration file. Nothing in R2-911 changes if a shard is between the
  chain and the car — the chain is still 287 mm off the bodywork and still in
  front of the lens — but "the chain is resting on a raft of glass" is a
  hypothesis this block cannot kill, and it would need the sim scene rather
  than the table.
* **The 16-frame count is one realisation's, and the harness cannot give a
  second one without a change.** See R2-916. This is a gap in the *tooling*, not
  in this block's diligence: R2-700 wrote the requirement, R2-703 quoted it,
  R2-777's `--seed` belongs to `sim/debris_demo.py` and not to the breach bake,
  and no entry has noticed that the bake has no seed to vary.
* **`ridepose`'s own-motion gate is not withdrawn**, but R2-914 shows what it is
  measuring. It should be read beside `RIDESILHOUETTE`, not instead of it, and
  a bake can now fail one and pass the other — R2701A does exactly that, and
  that disagreement is information rather than a bug.
* **`Car.identity_ok()` still watches the blend's SIZE** (R2-705). Untouched
  here; this block opened no blend.
* **~100 of the ~200,000 separations in a full run do not converge to 1e-6.**
  They are counted and printed, never rounded to zero, and none of them is at a
  reported minimum. The reported minima are all certified.

---

## FILES

```
sim/ridecontact.py                   NEW.  numpy only, no Blender.
                                     --selftest                8 controls
                                     --table ... --substep     exact separation
                                     --silhouette              the depth-order gate
docs/STAGING-R2-911-to-R2-940.md     this file
```

Nothing in `sim/out/` was written or overwritten. `sim/out/breach_film.npz`
md5 is untouched — no stage of `land_breach.sh` was run.
