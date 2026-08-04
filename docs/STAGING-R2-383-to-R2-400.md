# STAGING — R2-383 to R2-400 (the car proxy)

Owner: the car-proxy block. `docs/DEFECT-LOG-R2.md` is not mine to edit.

---

## R2-383 — nine predictions about the 89.79 m event, committed before the data

Written and committed **before** any trajectory was read out of
`sim/out/breach_film_R2281_REBAKE.npz` and before any ablation was run. The
only things known at the time of writing are:

* the table's format and its span (film frames 845…1165);
* the car's authored world-time trajectory over the sim window, which I read
  from `breachlib.Car` because it is the *input* to the sim, not a result of
  it — **the car travels 262.76 m in the 6.9 s sim window and accelerates
  from 9.6 m/s to 58.2 m/s**, crossing the glass plane (nose at x = 15.000)
  at sim frame 145;
* the construction of a mullion segment in `build_breach_sim.py`: 4.7 kg/m of
  6063-T6 over a segment of (head_z − foot_z)/8, split 0.72/0.28 between the
  extrusion body and its pressure plate.

That last one already prices the headline mechanism, so I will say the
uncomfortable thing first.

### P1 — the first frame

`MUL05_S02` first exceeds 0.05 m of displacement within **6 sim frames of sim
f145**, the frame the car's nose crosses x = 15.000. Film frame ≈ 860.

### P2 — the speed ceiling a single impulse allows

The car is doing **16.398 m/s** when its nose reaches the glass. A body struck
once by an infinitely massive plane moving at v, with restitution e, leaves at
at most (1 + e)·v; the car proxy declares `rest=0.05` and the aluminium
`REST_ALU = 0.10`, so a **single** contact cannot send `MUL05_S02` above about
**18 m/s**.

**I predict its measured peak speed exceeds 25 m/s.** If it does, the 89.79 m
cannot be a launch: energy is being added after the impact.

### P3 — the signature that decides between the two mechanisms

Two mechanisms are on the table and they are not the same defect:

* **H_A, the one the brief hands me** — the proxy is `kinematic=True`, so it
  has infinite mass, loses no momentum, and pumps into the field every joule
  the collision should have taken out of the car.
* **H_B, mine** — the proxy is a collider for **262 m** of downrange travel,
  and anything that ends up in front of it or on top of it is *carried*. On
  this hypothesis the mass of the proxy is close to irrelevant.

They separate cleanly on the speed profile. Under H_A the travel is one
launch: peak speed at contact, monotone decay afterwards. Under H_B the
segment's speed *tracks the car's* — repeated re-acceleration, and net
positive dv/dt long after the impact.

**I predict H_B.** Concretely: `MUL05_S02` shows net acceleration over an
interval of ≥ 100 sim frames beginning ≥ 100 sim frames after first contact,
and spends ≥ 300 consecutive sim frames inside the car's local envelope
(|x_local| ≤ 6 m, |y_local| ≤ 2 m, −1 ≤ z_local ≤ 3 m).

### P4 — the number that makes the brief's mechanism the wrong one

A mullion segment in this file is **4.7 kg/m × segment height × 0.72**. On an
approximately 6 m mullion in 8 segments that is about **2.5 kg**. The car is
798 kg. **The mass ratio at this contact is of order 300:1.**

**I predict that giving the car proxy its real dynamic mass changes
`MUL05_S02`'s travel by less than 20 %**, and that the fix named first in my
brief — "a dynamic proxy with the car's real mass and inertia" — therefore
does not fix the defect it is proposed for. An 798 kg body does not notice
2.5 kg. The 45 % momentum figure in the docstring is an *aggregate* over
2,240.9 kg of glass; it is not the impedance any single member sees, and I
think that aggregate has been read as if it were.

I am predicting that my own brief's prime suspect is not guilty of *this*
event. It may still be guilty of others — see P5.

### P5 — where the kinematic proxy IS the cause

The 2,240.9 kg aggregate is real. **I predict the kinematic proxy does show up
in the field statistic** — the median destroyed-bay shard's 88.17 m and the
2,647 shards still over 1 m/s — because the field as a whole *is* comparable
to the car's mass, and because those shards are small enough to be swept
rather than knocked clear. But I predict it shows up as *carrying*, not as
launching: same H_B mechanism, aggregated.

### P6 — the fix

**I predict the effective fix is to withdraw the boundary condition when it
stops representing anything**, not to re-mass it. Specifically: removing the
car proxy's collision after its tail has cleared the wall plane by a stated
margin brings `MUL05_S02` below **10 m** of travel.

### P7 — what the fix costs the car

**Nothing measurable.** The car's transform is read from
`world/car_anim_measured.json` and keyed onto the proxy; if I do not make the
proxy dynamic, the authored trajectory is untouched, and the beat 2 / beat 4
seams must come back **bit-identical**, not merely close.

### P8 — the ending

**I predict the aperture survives.** The aperture is decided in the first ~50
sim frames, while the debris travel is decided over the following 1,500. I
predict f2978 stays within 1 percentage point of the 11.33 % changed > 8/255
and f2940's result holds.

### P9 — the one I expect to be wrong about

I expect at least one of P1–P8 to fail, and if I had to name it I would name
**P6's 10 m**: withdrawing the collider still leaves the segment whatever
speed it had when the collider went away, and a 2.5 kg aluminium box sliding
on concrete at μ = 0.45 from 16 m/s runs **29 m** before it stops. So 10 m may
be unreachable without a second mechanism, and if it is, I will say so and
name the second mechanism rather than move the number.

---

## R2-384 — the 89.79 m is a RIDE, not a launch: `MUL05_S02` spends 161 film frames on the car's airbox, dead centre of a camera locked 6 m off it

`sim/carproxy_probe.py` puts every body of a breach table into the CAR'S OWN
frame at every key. The car's pose is known independently of the solver — it is
read from `world/car_anim_measured.json`, the same file the sim keys the proxy
from — so "is this body being carried?" is answerable without a contact
manifold, which is just as well, because `bpy` exposes none.

**The event, with its first frame.** `MUL05_S02` in
`sim/out/breach_film_R2281_REBAKE.npz`:

| | |
|---|---|
| first movement > 0.05 m | **film f860.0** |
| the car's nose crosses x = 15.000 | **film f859.876** (`Car.impact_frame()`) |
| travel | **89.79 m**, d = (+89.63, −4.95, −1.90) |
| peak speed | **23.06 m/s at f1050** |
| keys inside the car's envelope | **125 of 260, one unbroken run f859 → f1017** |

**P1 lands to within 0.13 of a film frame.** The segment starts moving the
frame the nose arrives, which is what a member struck head-on does.

**And then it does not leave.** The trace, in the car's own coordinates:

| film | world x | z | speed | car-local x | car-local z | what |
|---|---|---|---|---|---|---|
| f862 | 15.77 | 1.98 | 10.34 | +2.29 | 1.96 | ahead of the nose |
| f890 | 19.18 | 1.22 | 12.71 | **+0.05** | 1.22 | arriving on the deck |
| f905 | 20.33 | 1.06 | 15.47 | −0.54 | 1.07 | **on the airbox** (`CAR_TOP_Z` = 0.992) |
| f1000 | 30.61 | 1.17 | 21.79 | −3.43 | 1.20 | sliding aft, still aboard |
| f1047 | 37.99 | 0.63 | 22.58 | −5.25 | 0.68 | past the tail (`TAIL_DX` = −2.678) |
| f1051 | 40.44 | **0.11** | 22.83 | −6.03 | 0.17 | on the ground |
| f1165 | 104.53 | 0.05 | **4.79** | −205.34 | 1.25 | still sliding |

**So the 89.79 m is two numbers, and only one of them is a defect:**

* **25.6 m of RIDE**, f890 → f1051, lying on the car's airbox and engine cover
  while the authored animation takes the car from 19.1 to 41.6 m and from 12.7
  to 22.8 m/s;
* **64.1 m of ordinary slide**, f1051 → f1165, at 3.33 m/s² — which is
  µ = 0.34 against `FRICTION_ALU` × concrete = 0.45 × 0.62 = 0.279 combined,
  i.e. plain sliding friction doing exactly what it should.

The slide is honest physics applied to a speed the segment should never have
had. **The ride is the defect**, and P2 is confirmed with room to spare: a
single contact with a plane moving at 16.398 m/s and `rest` 0.05 / 0.10 cannot
send a body above ≈18 m/s, and this one reaches 23.06.

**It is not a small defect and it is not off camera.** `sim/sagpx.py` through
the ONER track: at f905 the car projects at u = 1792, at f1000 at u = 1913, at
f1050 at u = 2136 — the camera is **locked on the car** at **6.0 to 12.9 m**
for the whole ride. A 2.5 kg aluminium mullion segment lies on the airbox of an
F1 car, in the middle of a 4K frame, six metres from the lens, for 161 film
frames of beat 3.

### The other two capture modes, and the worst travellers in the file

`sim/carproxy_census.py`, same method over all 3,948 bodies, envelope = the
convex union of `breachlib.car_proxy_parts()` inflated by 120 mm:

| | R6 SHIPPED | **R2281 RE-BAKE** |
|---|---|---|
| distance TRANSPORTED inside the car's envelope | 5,802 m | **40,587 m** |
| distance travelled free | 26,722 m | 199,427 m |
| transport share of all travel | 17.8 % | **16.9 %** |
| bodies carried > 1 m | 2,395 | **2,629** |
| — at the nose | 1,475 (19.4 kg) | 1,771 (29.4 kg) |
| — on the deck | 870 (26.2 kg) | **795 (151.3 kg)** |
| — under the floor | 37 (0.3 kg) | 46 (1.2 kg) |

**The transport SHARE is the same in both bakes.** The capture mechanism is not
something the corrected thresholds introduced — it is pre-existing, it is in
the shipped table too, and correcting the frame only gave it seven times as
much to carry. That is R2-290's "both bakes are wrong about the debris",
measured.

**The worst travellers are not on the deck, they are underneath it.** The
fifteen furthest-travelled bodies in the re-bake are all `GS_b05_004xx`, at
**204.96 – 205.01 m**, and their car-local position is **x = −1.72 m ± 0.01 m,
z ≈ 0.01 m, held for 236 consecutive keys (f859 → f1094)**. Ten millimetres of
scatter over 226 film frames is not sliding contact — it is a clamp. They are
wedged between the proxy's `floor` part and the slab and dragged at the car's
own speed to **43.58 m/s**.

**And the geometry says they had no way out.** `breachlib.car_proxy_parts()`
puts `floor` at **z 0.008 … 0.055** — an 8 mm ground clearance — while the
curtain wall's glass is **11.5 mm laminate**. Nothing lying on the slab in the
car's track can pass under that floor. It is a squeegee, and it is 1.52 m wide.


---

## R2-385 — the kinematic proxy is NOT what makes the debris travel, and no re-massing of it — dynamic, hybrid or otherwise — would have helped

My brief names the prime suspect and quotes `build_breach_sim.py`'s own
docstring for it: the proxy is `kinematic=True`, so it has infinite mass, "cannot
lose momentum", and "every joule the collision should have taken out of the car
is instead pumped into the field". The docstring's supporting figure is that the
shard field takes **up to 45 %** of the car's momentum.

**The 45 % is real as an aggregate and it is the wrong quantity for this
defect.** Here is the impedance the actual bodies see.

### The masses at the three contacts that produce the travel

| body | mass | mass ratio to the car's 798 kg |
|---|---|---|
| `MUL05_S02`, the 89.79 m mullion segment | 4.7 kg/m × 0.775 m × 0.72 = **2.623 kg** | **304 : 1** |
| `GS_b05_00434`, the 205.01 m underfloor shard | **0.0025 kg** | **319,000 : 1** |
| the whole deck-carried population | 151.3 kg | 5.3 : 1 |

### What the ride actually costs the car

`MUL05_S02` gains 12.707 → 22.829 m/s over the 1.149 s it lies on the deck.
That is an impulse of **26.54 N·s**, a mean force of **23.10 N**, and
**0.203 % of the car's 13,086 kg·m/s at the glass plane**. A dynamic 798 kg car
would have been slowed by **0.033 m/s** by the entire event and would have
carried the segment to within a third of a percent of the same place.

The underfloor case is worse for the hypothesis, not better. Dragging a 2.5 g
shard against µ = 0.32 × 0.62 needs **0.005 N**. The car's static weight alone
is **7,828 N**. The surplus is a factor of a million and a half. Whether the
thing pressing down has infinite mass or 798 kg is not a question the shard can
tell the difference between.

**And the deck ride is not even a mass phenomenon.** A body lying on a surface
is carried by friction, and the carrying force is µ·m_body·g — it contains the
carrier's mass nowhere at all. `FRICTION_ALU` × the proxy's 0.55 gives
2.428 m/s²; the segment is actually accelerating at **8.81 m/s²**, so the rest
comes from normal impacts on the airbox's and rear wing's vertical faces — and
those are bounded by the car's *momentum*, of which this costs 0.2 %.

**P4 is confirmed, and it was a prediction against my own brief.** A dynamic
proxy at the car's real mass and inertia would not have moved this defect. Nor
would a hybrid with a finite effective mass at the contact, unless that
effective mass were of the order of the *shard's* — 2.6 kg for the mullion
segment, 2.5 g for the glass — which is not "the car's real mass and inertia",
it is a car made of polystyrene.

**I therefore decline the fix my brief names first, and I am declining it on
the numbers rather than on cost.** It is also the fix that would have been
expensive: it puts a solver inside a keyed animation the rest of the film's
continuity is built on, and it would have bought nothing.

### Where the 45 % IS true, and what it is true about

`sim/carproxy_census.py` runs the momentum budget the docstring argues from,
Σm|v| over all 3,948 bodies against 798·v_car, in world time:

| film frame | field | car | field / car |
|---|---|---|---|
| f860 | 1,732 | 13,283 | 13.0 % |
| f880 | 3,290 | 13,392 | **24.6 %** |
| f950 | 3,851 | 17,308 | 22.2 % |
| **f1049 (peak)** | **6,510** | 23,392 | **27.8 %** |
| f1165 | 1,191 | 58,748 | 2.0 % |

So the field really does hold a quarter of the car's momentum during the
breach, and a car that were dynamic really would decelerate hard. **That is a
statement about the car, not about the debris** — and it is already recorded as
a DECISION rather than a consequence (R2-099): the film's car does not slow
down because its animation says so, and changing that is a change to
`anim/carrig.py`. What it is *not* is an explanation of why one mullion segment
went 89.79 m, because that segment is 0.2 % of the budget.

### Two predictions half-right, said plainly

* **P3** predicted the carrying signature and got the mechanism right — the
  acceleration runs for 276 sim frames beginning 130 sim frames after first
  contact, exactly the "not a launch" shape. Its second clause asked for **≥
  300 consecutive sim frames** inside the envelope and the measurement is
  **288**. Narrowly wrong, and I am not moving the number.
* **P5** predicted the kinematic proxy would still show up in the *field*
  statistic through the same carrying mechanism. It does — 40,587 m of
  transport — but the census also shows the transport SHARE is **17.8 % in the
  shipped table against 16.9 % in the re-bake**, i.e. the mechanism is
  unchanged and only the amount of loose debris grew. P5 is right about the
  mechanism and understated how old it is.


---

## R2-386 — two of Blender 5.2's three ways to switch a collider off do nothing, and the test that found it is four lines of scene

The fix I am going to argue for needs the car proxy to stop colliding partway
through a bake without its transform changing. Blender exposes three plausible
switches and the manual distinguishes none of them for a PASSIVE KINEMATIC
body, so `sim/tmp/test_rb_enabled.py` builds the smallest scene that can answer
it — an active cube resting on a passive kinematic plate — keys each switch to
turn off at frame 30, bakes 60 frames, and asks the only question that settles
it: **does the cube fall through?**

| keyed property | cube z at f5 / f25 / f31 / f59 | fell through |
|---|---|---|
| `rigid_body.enabled` | 2.26 / 2.20 / 2.20 / **2.20** | **no** |
| `rigid_body.kinematic` | 2.26 / 2.20 / 2.20 / **2.20** | **no** |
| `rigid_body.collision_collections` | 2.26 / 2.20 / 2.19 / **−4.87** | **YES** |

Only the collision collections are re-read per frame. So the withdrawal is a
move from collision collection 0 — which every other body in this scene is in,
by `objects_add`'s default — to collection 1, which nothing is in.

**And it costs two F-curves, not thirty-six.** The eighteen proxy parts already
share one action and one slot (that is the whole reason the car costs 6 curves
instead of 108), so the two boolean curves go on the same channelbag and every
part switches on the same frame *by construction* rather than by eighteen
correct writes.

**It also broke the gate that proves the car's curve is linear, and that is
worth recording.** `prove_linear()` walked every fcurve in the action and did
`ref = loc[:, fc.array_index] if fc.data_path == "location" else rot[:, ...]`,
so the two new CONSTANT boolean curves would have been read as *rotation*
curves, failed the LINEAR flag test, and refused the bake — with a message
about the car's curve that would have been true and completely misleading.
`_act_fcurves()` now filters to `location` / `rotation_euler` and **counts what
it excluded** into `linearity.non_motion_curves`, so the exclusion is in the
report rather than in the code's memory.

**A note on the smoke test that failed first.** The first version of the switch
test had the plate scaled after creation and the rigid body added before the
depsgraph had seen the scale, so Bullet built a 4 m box where the picture
showed a 0.2 m one, the cube started 2 m inside it, and all three switches
"failed" identically — by launching the cube upward at 72 m/s. Three identical
results is not three measurements; it is one bug. The fix was one
`view_layer.update()`.


---

## R2-387 — what the ending can and cannot cost, committed before the fix exists

The 11.33 % was measured on
`render/film14_breach_R2281_FRAMEONLY_DIAGNOSTIC_DO_NOT_SHIP.blend` — the
corrected FRAME on the SHIPPED glass — so the statistic that says the aperture
reads is a statistic about **where the frame's thirty released bodies end up**.
Three of them end up 89 m downrange. It is therefore a fair question whether
the ending was bought by the very bulldozer I am about to remove, and it has to
be answered *before* the answer is available.

`sim/sagpx.py`, projecting each released frame body's RESTING position through
the ONER track, against `wallstats.py`'s own `WOUND_bridged` rectangle
(u 1891–1949, v 1041–1120):

| body | travel | rests at x | u, v at f2978 | in the wound box |
|---|---|---|---|---|
| `MUL05_S00 / S01 / S02` (+plates) | 88.3 / 89.0 / 89.8 m | 103–105 | 1800–1805, **1436–1445** | no |
| `MUL05_S03 / S04` | 13.3 / 12.7 m | 27–28 | 1902–1904, 1157–1160 | no |
| `MUL05_S05 / S06 / S07` | 7.6 / 7.6 / 7.6 m | 19.7–21.3 | 1922–1924, 1134–1139 | no |
| `TRN_z0_b04 / b05` | 53.1 / 69.8 m | 68 / 85 | 1914 / 1941, 1300 / 1364 | no |
| `TRN_z1_b04 / b05`, `TRN_z2_b04 / b05` | 5.5–8.6 m | 18.0–22.8 | 1894–1950, 1128–1145 | no |

**At f2978, zero of the thirty released frame bodies rest inside the wound
box.** The ground plane at the wall itself projects to v 1119 at f2978 — one
pixel above the box's lower edge — so *anything* that comes to rest on the
apron beyond x ≈ 15.5 m is below the measured region. **The 11.33 % was not
bought by the 89 m.** Had those three segments stopped at 30 m they would have
projected at v ≈ 1167, still forty-seven pixels clear.

**f2940 is the tighter frame and that is where the risk is.** Its box bottom
corresponds to ground at x ≈ 19.6 m, and **two bodies already rest inside it**
— `TRN_z2_b04` and its pressure plate, at x = 18.05, u 1909, v 1116. So the
f2940 result is already tolerant of released members lying in the lower
aperture, which is what R2-294 predicted and got right.

### The prediction

**P10.** The fix moves `MUL05_S00/S01/S02` from x ≈ 104 to somewhere in
x 25–50, and moves nothing else in the frame by more than 3 m. **f2978's
11.33 % holds to within 1.5 percentage points and `grid_contrast` stays under
0.012.** f2940's result holds.

**P11.** The number at risk is **f2940, not f2978**, and the mechanism if it
fails is *more* frame bodies coming to rest inside x < 19.6 m with |y| < 2.9 m
— i.e. the fix stopping them too early rather than too late. If f2940 moves and
f2978 does not, that is the reason, and I will report the resting x of every
released member rather than argue about the pixels.


---

## R2-388 — the ablation: withdrawing the boundary condition is REFUTED, and it was my own committed fix

Three 400-frame cells, identical in everything but the car proxy, at the
derived frame thresholds. 400 sim frames is film f845 → f1005, which contains
the impact, the underfloor clamp, and 100 of the 161 film frames of the deck
ride. `sim/tmp/run_r2386_ablations.sh`, all three `EXIT=0`.

| | **A0** shipped proxy | **A1** withdraw at tail-clear | **A2** friction 0.55 → 0.20 |
|---|---|---|---|
| `MUL05_S02` travel / peak | 14.46 m / 18.39 m/s | 11.69 m / 15.31 m/s | 15.60 m / **26.20 m/s** |
| `GS_b05_00434` travel / peak | 15.84 m / 24.80 m/s | 12.68 m / 19.02 m/s | **0.02 m / 10.77 m/s** |
| **TOTAL transport, all bodies** | **32,064 m** | 23,825 m (−26 %) | **7,869 m (−75 %)** |
| — nose plow | 22,944 m | 18,020 m | **5,846 m** |
| — deck ride | 8,507 m | 5,523 m | **1,826 m** |
| — underfloor clamp | 368 m | 163 m | **71 m** |
| **PRICE: bodies inside the car, worst frame** | 111 (at impact) | **1,526** | 113 (at impact) |
| PRICE: samples over 100 bodies inside | **0 of 100** | **41 of 100** | **0 of 100** |
| CONTROL untouched mullions, max travel | 0.000133 m | 0.000907 m | 0.000086 m |
| **connected aperture** (`breach_metrics`) | **2.15 × 6.00 m** | **2.15 × 6.00 m** | **2.15 × 6.00 m** |
| bay 4 / bay 5 vacated | 96.7 / 95.4 % | 96.7 / 95.4 % | 98.4 / 95.3 % |
| metrics CONTROLS | PASS | PASS | PASS |

### P6 is wrong, and it is wrong twice over

I committed, before any of this existed, that "the effective fix is to withdraw
the boundary condition when it stops representing anything" and that it would
bring `MUL05_S02` below 10 m. **It does neither.**

* It removes **26 %** of the transport, against friction's **75 %**. The
  withdrawal happens at film f876.8 and by then the plow has already formed:
  most of the transport is bought in the 130 sim frames before it.
* And it has a price I did not price. **The car overtakes the cloud it just
  made.** With the collider on, the car pushes the debris ahead of it forever
  and can never catch it; with the collider off, the debris coasts at 15–18 m/s
  while the authored animation takes the car to 24, 30, 40 m/s, and the car
  drives straight through it:

| sim frame | film | bodies inside the car (A1) | their glass area |
|---|---|---|---|
| 227 (withdrawal) | f876.8 | 15 | 0.004 m² |
| 280 | f911.2 | 89 | 0.98 m² |
| 300 | f924.2 | 897 | 1.75 m² |
| **323** | **f939.2** | **1,526** | **2.40 m²** |
| 350 | f956.8 | 1,426 | 0.78 m² |
| 380 | f976.3 | **0** | 0.00 m² |

**Forty-six film frames of the car driving through two and a half square metres
of its own glass, dead centre, six metres from the lens, in slow motion.** The
baseline with the collider on is 15 bodies, and that is shard *origins* inside a
convex proxy part while they rest against it, not visible overlap.

**I am not proposing withdrawal and I am not proposing a later withdrawal
either** — the overtake is structural. The car is authored to accelerate away
from a cloud it gave its own speed to, so there is no frame at which the
collider can leave without the car then passing through what it left behind.

### What the ablation DOES establish

* **The aperture is insensitive to every one of these.** Same connected
  2.15 × 6.00 m in all three cells, same bays, `CONTROLS PASS` in all three,
  untouched mullions at 10⁻⁴ m. Whatever the fix turns out to be, it is not
  going to be paid for out of the ending. That is P8's premise, measured
  early and on the cheap cells rather than asserted at the end.
* **Friction is the lever the mechanism said it would be.** The 205 m
  underfloor clamp — the single worst traveller in the file — goes to **23 mm**
  when the proxy is not grippier than aluminium. It was a friction clamp all
  along, exactly as R2-385's arithmetic said.
* **And friction alone is not the whole fix.** A2's median displacement at
  f1005 is 15.44 m against A0's 15.78 m, and its field median speed at the last
  frame is *higher* (20.19 against 18.15 m/s). Cutting the grip stops the car
  *carrying* the debris and does nothing about the debris having been *launched*
  at the car's own speed. Which is R2-389.


---

## R2-389 — cutting the proxy's grip puts five mullion segments back in the middle of the aperture, and R2-293's four cells could not have seen it

A2 is refused, and the reason is the one thing this job was told not to trade.

`MUL05_S03 … S07` — the 4.65 m of mullion above the car's roofline — in the two
cells at sim frame 400:

| segment | z at impact | A0 (friction 0.55) end | A2 (friction 0.20) end | A0 travel | A2 travel |
|---|---|---|---|---|---|
| `MUL05_S03` | 2.73 | (23.00, −0.91, 0.13) | **(15.00, 0.02, 2.64)** | 8.56 m | **0.14 m** |
| `MUL05_S04` | 3.51 | (22.24, −0.74, 0.12) | **(15.01, 0.02, 3.41)** | 8.12 m | **0.15 m** |
| `MUL05_S05` | 4.28 | (18.70, 0.08, 1.07) | **(15.01, 0.01, 4.19)** | 4.98 m | **0.15 m** |
| `MUL05_S06` | 5.06 | (18.03, 0.27, 0.74) | **(15.02, 0.01, 4.96)** | 5.35 m | **0.16 m** |
| `MUL05_S07` | 5.83 | (17.36, 0.47, 0.40) | **(15.02, 0.00, 5.74)** | 5.98 m | **0.16 m** |

In A2 the column **does not come down**. It drops 0.09 m in 1.06 s and stops —
2 % of a free fall — and it is still standing in the wall plane at the end of
the cell. Projected through the ONER track onto the closing frame it lands
**dead centre of `wallstats`'s own wound rectangle**:

| segment | u, v at f2978 | u, v at f2940 | inside the wound box |
|---|---|---|---|
| `MUL05_S03` | 1920.3, 1085.9 | 1920.2, 1084.4 | **yes** |
| `MUL05_S04` | 1920.3, 1076.0 | 1920.2, 1077.0 | **yes** |
| `MUL05_S05` | 1920.1, 1066.0 | 1920.1, 1069.5 | **yes** |
| `MUL05_S06` | 1920.1, 1056.0 | 1920.1, 1062.1 | **yes** |
| `MUL05_S07` | 1920.0, 1046.0 | 1920.0, 1054.6 | **yes** |

Five aluminium members standing in a vertical line down the middle of the hole
the whole block exists to open. **That is the ending, and cutting the proxy's
friction takes it away.** This is the P11 mechanism, committed in R2-387 before
any of these cells existed, and it fires at f2978 as well as f2940.

### Why the column falls, and what actually pulls it out

The car's roof is at 0.992 m and `MUL05_S04` starts at 3.51 m, so the car never
touches it. What takes it out is the **chain**: the car tears out the bottom
2.3 m, that piece is gripped and dragged, and the segment-to-segment joints
above it are pulled through their threshold one after another. Cut the grip and
the bottom piece slides off the nose instead of being held against it, the
impulse the chain sees is shorter and smaller, the joint above breaks early,
and the column above is left hanging with nothing to pull it.

**That is real, and it is the right behaviour.** A mullion is one extrusion;
taking the bottom of it out at 16 m/s brings the rest with it. So the car's grip
is not a nuisance parameter here — it is load-bearing for the frame result.

### And this qualifies an inherited conclusion, without overturning it

R2-293 separated the transom threshold from the head model with four
off-diagonal cells and concluded, correctly, that **the derived transom
threshold does all of it and the head model does nothing measurable**. Its
`8.8/FIXED` cell reproduces the whole collapse with the head still bolted on.

**All four of those cells hold the car proxy at friction 0.55.** They vary the
frame against itself, so they can rank the two frame parameters against each
other — which is what they were built to do — and they cannot see that a third
parameter, outside the frame entirely, is also necessary. A2 is the fifth cell,
and it says the transom threshold is **necessary but not sufficient**: at 8.8
with a slippery car, six of six transom ends still let go and the column still
stays up.

I am not proposing to change anything in R2-293's conclusion. I am recording
that "the derived transom threshold does all of it" is true *within the
experiment that measured it*, and that the car's grip is the other half.

---

## R2-390 — P12: what the air-drag cell will show, committed while it bakes

`--air-drag derived` (R2-388) with the car proxy left exactly as it shipped.
Written and committed while B0/B1/B2 are still baking.

* **P12a** The frame collapse survives untouched. `MUL05_S03…S07` travel within
  20 % of A0's 8.56 / 8.12 / 4.98 / 5.35 / 5.98 m, and none of them is left
  standing in the wall plane.
* **P12b** The deck ride is reduced but not removed: `MUL05_S02`'s peak speed
  falls from 18.39 m/s to under 16 m/s. The drag on that segment is
  0.284 per second, i.e. 5.7 m/s² at 20 m/s, against the 8.81 m/s² the car puts
  into it — the same order, and short of cancelling it.
* **P12c** The underfloor clamp is NOT fixed by air. `GS_b05_00434` is held
  rigidly between the floor and the slab; drag on a clamped body changes
  nothing. Its travel stays above 10 m. **Only the friction that clamps it
  moves it, and friction is now refused.**
* **P12d** Total transport falls by less than 40 % (against friction's 75 %),
  because transport is contact-driven and air only opposes it.
* **P12e** The thing that matters — the field's speed when the keys run out —
  falls substantially: median under 12 m/s at the last frame of the cell,
  against A0's 18.15.
* **P12f** No interpenetration price at all: fewer than 150 bodies inside the
  car at the worst frame, and that frame is the impact itself.
* **P12g** The connected aperture is unchanged at 2.15 × 6.00 m with
  `CONTROLS PASS`.

If P12c holds, the underfloor clamp and the deck ride survive into the shipped
bake as **stated residual defects**, and the reason will be that the only lever
that moves them is the same lever that closes the aperture.


---

## R2-391 — the seam table, BEFORE column, measured with the script that will measure the AFTER column

`sim/seams.py`, run on the two tables that already exist. It measures the car's
seams and the table's seams with one piece of code so the two columns cannot
drift, and it was validated against numbers it did not produce: it reproduces
`rest_gate.py`'s **1,599** bodies over 1 mm/film-frame on the shipped table and
R2-290's **2,647** over 1 m/s and **u 884…3465** on the re-bake, to the body.

### The car — the one-take law

| | R6 SHIPPED | R2281 RE-BAKE |
|---|---|---|
| `car_anim_measured.json`, 2,978 frames, sha256[:16] | `7fe6b8a97b362ac0` | `7fe6b8a97b362ac0` |
| **f865, beat 2 \| beat 3** loc | 14.969 → 15.590 → 16.091 | identical |
| speed across the join | 16.769 → 15.677 → 15.617 m/s | identical |
| worst \|a\| within ±5 frames (beat median) | 25.39 (9.34) m/s² | identical |
| **f1057, beat 3 \| beat 4** loc | 52.556 → 53.901 → 55.265 | identical |
| speed across the join | 32.061 → 32.508 → 32.955 m/s | identical |
| worst \|a\| within ±5 frames (beat median) | 10.76 (11.60) m/s² | identical |

They are identical because **the car's transform is an input to this sim and an
output of nothing in it.** `breachlib.Car` reads
`world/car_anim_measured.json`; the sim keys the proxy from it and writes
nothing back. That is the whole reason I refused the dynamic proxy in R2-385 on
numbers rather than on cost — the cost was going to be this table.

### The table — the release seam and the last key

| | R6 SHIPPED (live) | **R2281 RE-BAKE (not shippable)** |
|---|---|---|
| span | f845 – f1165 | f845 – f1165 |
| **release pop** (first key vs the static wall) | **0.000000 m** | **0.000000 m** |
| bodies over 1 mm / film frame at the last key | 1,599 | **2,734** |
| **bodies over 1 m/s at the last key** | **70** | **2,646** |
| median speed at the last key | 0.016 m/s | **4.736 m/s** |
| max speed at the last key | 73.17 m/s | 24.89 m/s |
| end x: median / p95 / max | 16.26 / 17.07 / 641.8 | **102.81 / 103.57 / 261.9** |
| bodies in the closing raster (f2978) | 3,891 | 3,947 |
| **frozen-and-moving in the closing raster** | **13** | **2,645** |
| their pixel extent | 477 × 896 px | **2,581 × 1,018 px** |
| their u range | 1,774 – 2,268 | **884 – 3,465** |

**The release seam is clean in both** — nothing pops on the frame it is
released — so the whole of the seam defect is at the far end: 2,645 bodies
freeze mid-slide across two-thirds of the closing frame's width. That is the
number the fix has to move, and it is the number the AFTER column will be read
on.

