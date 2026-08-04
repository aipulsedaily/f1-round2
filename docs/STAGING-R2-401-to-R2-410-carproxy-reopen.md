# STAGING — the car-proxy reopen (numbers to be assigned by the log's owner)

The coordinator has reopened this. The framing I was given — that the cause was
the kinematic car's inability to lose momentum to 2,240.9 kg of glass — is
refuted by my own measurement (0.203 % of the car's momentum), and they have
said plainly that the framing was theirs. What is left standing is the thing
the data actually points at:

> `MUL05_S02` travels **55.35 m**. **25.6 m of that was riding the car's deck**
> and the rest is the slide that ride paid for. Two independent questions:
> **why is it on the car at all**, and **why does it slide so far once it
> leaves**. And the acceptance criterion is not a distance — it is whether it
> reads wrong on screen.

---

## R2-4xx — six predictions, committed before the reopened search

Written before any of the three measurements below is run. Everything used is
data already on disk: `sim/out/breach_film_R2387.npz`, `sim/tmp/r2386/A0.npz`,
and the ONER camera track.

### On the RIDE — is it a solver failure or a modelled outcome?

Three candidate mechanisms were named: a collision-shape gap, a substep/CCD
failure at speed, or the fracture releasing pieces inside the car's swept
volume. **I predict none of them.**

* **P20 — no tunnelling.** `MUL05_S02` is **never inside a car-proxy part** at
  any frame, on the 128-direction over-approximating hull test that already
  over-counts. If it had tunnelled through the bodywork it would have to appear
  inside it for at least one sampled frame.
* **P21 — not released inside the swept volume.** At its first movement the
  segment's car-local x is **greater than +2.0 m**, i.e. ahead of the nose
  (`NOSE_DX` = 3.020), and its world z is **above `CAR_TOP_Z` = 0.992**. It is
  not born inside the car.
* **P22 — it falls onto the car, and that is what the scene says should
  happen.** `MUL05_S02` spans z 1.55–2.33 m, centre 1.94. The car strikes the
  mullion at 0–1 m, this segment is pushed forward at **about 10 m/s against
  the car's 16.4**, so the car overtakes it while it is still falling, and it
  lands on a deck whose top is at 0.992 m. I predict the trace shows world z
  decreasing monotonically through the crossing with **no discontinuity**, and
  car-local x decreasing smoothly from +2.7 through zero. If so, the ride is
  not a bug to fix; it is a consequence to accept or to design out of the
  *proxy's geometry*, and saying otherwise would be inventing a defect.

### On the SLIDE — 64 m of architectural aluminium

* **P23 — the slide is honest sliding friction at a defensible coefficient, and
  the artefact is that the piece never tumbles.** Bullet combines friction
  multiplicatively, so aluminium 0.45 × concrete 0.62 = **0.279**, which is a
  real µ for aluminium on concrete. I predict the measured deceleration during
  the free slide is within 25 % of µg = 2.74 m/s², **and** that the segment's
  angular speed during that slide is **under 2 rad/s** — i.e. it lies flat on
  one face of a box and skates. A real 160 × 75 mm extrusion tumbles end over
  end and digs in. **If the angular speed is low, the fix is a shape and a
  rotational drag, not a friction number**, and lowering µ would be fitting.

### On the CRITERION — pixels, not metres

* **P24 — the 55 m is not what is on screen; the ride is.** I predict
  `MUL05_S02` at rest projects to **under 40 px of length in the closing
  frames**, and that its largest on-screen presence by an order of magnitude is
  during the ride in beat 3, at 6–13 m from the lens. **The frames that decide
  this are f0890–f1050, not f2940/f2978.**
* **P25 — the one I expect to be wrong.** P24 assumes the resting place is far
  and small. If any of the three lower mullion segments comes to rest inside
  the *beat 4* camera's view of the apron — the take is continuous and the car
  drives past its own debris — then the metre count matters after all and P24
  is the wrong question. I have not looked, and I would rather be caught by
  this than not have written it down.


---

## R2-4xx — the ride is not a solver failure, and the 55.35 m decomposes exactly

Three controls on `MUL05_S02`, run before anything was changed.

### P20, P21, P22 — all three confirmed. Nothing is broken.

| control | result |
|---|---|
| frames INSIDE any car-proxy part (128-direction hull test, which OVER-counts) | **0 of 400** |
| car-local x at first movement | **+2.912 m** — ahead of the nose (`NOSE_DX` 3.020), not born inside |
| world z at first movement | **1.949 m** — twice `CAR_TOP_Z` (0.992) |
| largest single-frame Δz over the whole descent | **0.0237 m**; frames with Δz > 0.25 m: **0** |
| largest single-frame step, any axis | **0.0767 m** — 9.6 mm per substep at 1,920 Hz, against a 75 mm section |

**No tunnelling, no CCD failure, no piece released inside the car.** The segment
descends smoothly from z 1.949 to the deck over 117 sim frames while the car
drives under it. It crosses the nose plane at z 1.954 — a metre clear of the
roof — and reaches deck height 119 frames later at car-local x −0.378.

**So the mechanism is exactly what the scene says should happen.**
`MUL05_S02` spans z 1.55–2.33 m. The car strikes the mullion at 0–1 m, this
segment is pushed forward at about 10 m/s against the car's 16.4, the car
overtakes it while it is still falling, and it lands on a deck whose top is at
0.992 m. **There is no bug here to fix.** Had I gone looking for a collision
gap or a substep failure I would have found nothing, and three predictions said
so before the test.

### The 55.35 m, decomposed on the production bake

| phase | `MUL05_S02` | `MUL05_S00` | `TRN_z0_b05` |
|---|---|---|---|
| **aboard the car** | sim f142–476, film **f859.6–f1038.7**, **1.396 s world** | f861.6–f973.7, 0.896 s | f859.5–f993.2, 1.108 s |
| distance carried | **22.93 m** | 12.46 m | 15.25 m |
| **speed at separation** | **23.08 m/s** | 19.49 m/s | 21.73 m/s |
| free slide | 21.63 m from 15.62 m/s | 25.61 m from 18.31 m/s | 24.08 m from 17.34 m/s |
| measured deceleration | **4.47 m/s² (µ_eff 0.456)** | 4.98 (0.508) | 5.34 (0.544) |
| **angular speed while sliding** | median **0.99 rad/s**, p90 2.85 | 1.10, 4.85 | 0.75, 2.46 |
| total | **55.35 m** | 54.00 m | 55.14 m |

**P23 scores half.** I predicted the deceleration would be within 25 % of
µg = 2.74 m/s² and it is **4.47–5.34** — 63 to 95 % higher, because the air I
added is doing about half the work. That clause is **WRONG**, and wrong in the
direction that flatters the fix, which is the direction to be most suspicious
of. The other clause is **RIGHT**: the median angular speed while sliding is
**0.75–1.10 rad/s**, about a sixth of a revolution per second. **These pieces
do not tumble. They lie on one face of a box and skate**, which a bent 160 × 75
extrusion on tarmac does not do.

### And the criterion: P24 confirmed, and it changes what has to be fixed

Projecting each far traveller through the ONER track for all 2,134 frames of
the take:

| body | biggest on screen | at | range | **at rest, f2978** |
|---|---|---|---|---|
| `TRN_z0_b05` | **1,879 px long** | f971 | 2.9 m | **30.6 px** |
| `TRN_z0_b04` | **1,507 px** | f970 | 3.6 m | 30.4 px |
| `MUL05_S00` | 864 px | f977 | 2.4 m | 11.3 px |
| `MUL05_S01` | 704 px | f976 | 2.9 m | 11.3 px |
| `MUL05_S02` | 614 px | f972 | 3.3 m | **11.3 px** |

**The 55 m is 11 pixels. The ride is nineteen hundred.** At rest these members
are 8–31 px in the closing frames — at the limit of what R2-278 says can be
measured at all. Their entire on-screen life is **f0967–f0978**, where five
structural members ride the car past a lens 2.4 to 3.6 m away, in slow motion,
filling up to half the frame width.

**So the metre count was the wrong target and the coordinator is right that the
criterion is pixels — but the answer that follows is not "55 m is acceptable".
It is that the ride, not the distance, is the thing on screen, and the ride is
enormous.** I am not claiming these pieces are out of shot. They are the shot.

