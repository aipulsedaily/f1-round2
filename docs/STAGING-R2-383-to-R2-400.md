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

