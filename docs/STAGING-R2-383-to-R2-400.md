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

