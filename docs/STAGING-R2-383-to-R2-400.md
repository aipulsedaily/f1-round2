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
