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

