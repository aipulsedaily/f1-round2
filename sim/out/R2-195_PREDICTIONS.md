# BREACH CONTINUITY — predictions, written BEFORE the data exists

Block R2-195..R2-205. Written 2026-08-04 against `sim/tmp/breach_full_m1.npz`
(the raw 1,657-frame bake, 3,948 bodies, 240 Hz, world_t 1.1564..8.0564) and
`sim/out/breach_film.npz` (the decimated film table, 3,948 bodies, film frames
845..1165).

Nothing below has been measured yet. Each prediction states the quantity, the
units, and what number would refute it. Secondary quantifiers are marked
`[2nd]` and are reported whether or not they hold.

---

## P1 — the field FREEZES; it does not twitch

`apply_breach.py` writes `fc.extrapolation = "CONSTANT"` (line 462/475) and its
own header says so. So at the beat 3 -> 4 boundary the field does not keep
settling and does not drift: past the last key every body holds its last pose
exactly.

- **Primary:** in `render/film14_breach.blend`, `max |p(f2901) - p(f1165)|` over
  every shard object == **0.000 m exactly** (not "small" — exactly zero, because
  a constant F-curve returns the same float).
- **Refuted by:** any non-zero displacement, which would mean some curves
  extrapolate LINEAR and 2,275 bodies fly off to infinity through beats 4-6.
- `[2nd]` every one of the 3,806 applied objects has `extrapolation == CONSTANT`
  on all 7 channels; zero exceptions.

## P2 — the freeze is NOT at the beat 3 -> 4 boundary, and the boundary is not where to look

Beat 3 ends at f1056. The bake's last key is **f1165**, 109 frames later, i.e.
already inside beat 4. So the discontinuity — if there is a visible one — lands
at **f1165**, not at f1056, and the beat boundary itself is unremarkable.

- **Primary:** at f1056 the field is still playing normally: median per-body
  step f1055->f1056 is within 3x of the median step at f1000.
- **Refuted by:** the bake table ending before f1056, or by a step at f1056.

## P3 — the "2,275 still moving" are dominated by bodies in free fall off the edge of the world, not by a settling pile

`build_breach_sim.py` builds a **finite** static floor: `SIM_FloorIn`
x -15.00..14.94, y -11..11; `SIM_Threshold` x 14.94..15.00, y -14..14;
`SIM_FloorOut` x 15.00..46.00, y -14..14. Outside that footprint there is
**nothing to land on.**

- **Primary:** of the 627 bodies that end below the floor, **>= 500** left the
  floor's footprint horizontally before crossing z = 0 — i.e. at the frame they
  first go below z = 0 their (x, y) is outside the union of those three boxes.
  This is *running off the edge*, not tunnelling.
- **Refuted by:** most of them crossing z = 0 while inside the footprint, which
  would be tunnelling and would indict SUBSTEPS/MARGIN instead.
- `[2nd]` the body holding `max_speed_last_frame_ms = 108.24` is one of the
  sub-floor bodies, and its speed at the last frame is within 20 % of
  `g * (t_last - t_cross)` — a free-fall signature with no drag and no contact.
- `[2nd]` of the 2,275 bodies moving > 1 mm/film-frame at the last key,
  >= 25 % are sub-floor.

## P4 — the sub-floor bodies are invisible, so the defect is arithmetic, not photographic

They are 154 m below a floor the camera never sees the underside of, and they
are frozen there for beats 4-6.

- **Primary:** at f1165 and at f2901, **zero** sub-floor bodies project inside
  the 3840x2160 raster with a clear line of sight; every one is either behind
  the camera, outside the frustum, or occluded by the floor slab.
- **Refuted by:** any of them being visible, which turns an arithmetic defect
  into a rendering one.

## P5 — cluster B is a BOND impulse, not a contact

348 shards to 106 m/s at sim frames 243..252 with p50 distance to the nearest
car proxy part of **1.02 m** and nothing within 10 mm of a static surface
(`sim/tmp/bu5.json`). Nothing touched them. What is left is the constraint
network: mean bond degree 7.03, and the fastest shard in cluster A reverses
direction and travels **west at 137 m/s** one sim frame after moving east — a
slingshot, which is what an un-broken stretched joint does.

- **Primary:** at peak-1, the median distance from a cluster-B body to its
  **bonded** neighbours is **> 0.10 m** — six times the ~0.016 m nearest-
  neighbour spacing the field sits at — while a matched control set of ordinary
  (never-hot) shards from the same bays at the same frames stays under 0.05 m.
  A bond stretched a decimetre is a spring loaded with the energy that comes
  back out as 106 m/s.
- **Refuted by:** bonded-neighbour distances at peak-1 being ordinary, which
  would mean the impulse arrives from somewhere I have not looked.
- `[2nd]` the bonds in question have not broken at peak-1: the pair is still in
  the constraint list and its separation is still growing at peak.
- `[2nd]` the blow-up population is concentrated at the bottom of the wall
  (`bu4.json`: 52.6 % of shards with origin z < 0.30 m blow up, vs 21.8 % of
  the field), so the sill row is over-represented and the mechanism should show
  a bond-length or bond-degree difference there.

## P6 — the wound is legible in beat 6 and marginal in beat 5

Beat 6 centres the breach at f2901 at 21 x 24 px; beat 5 gives 33 x 123 px for
179 frames.

- **Primary:** at f2901 the aperture reads as a **dark hole**, not as a bright
  patch or as intact glass: mean radiance inside the 21 x 24 px wound box is
  **below** the mean of an equal-area box on the adjacent intact glass.
- **Refuted by:** the wound being brighter than or equal to the glass beside
  it, which at 21 px would read as a smudge and not as a hole.
- `[2nd]` at f2565 (beat 5) the wound's 33 x 123 px is enough to show the
  **mullion 5 stub** — the 4.43 m travelled member — as a distinct vertical
  feature, not just a dark slot.

## P7 — the free negative control

Any tail fix I apply acts on the bodies that are still moving at the last key.
The bodies that are **already asleep** at the last key are a negative control
that costs nothing: they must not move by one float.

- **Primary:** under the fix, bodies with last-frame speed < 1 mm/film-frame
  move **0.000 m**, while the treated population moves by a measurable amount.
  If both move, the fix is not selective and the measurement is worthless.
- The occluded arm: bodies below the floor are never on camera, so their
  treatment can be verified as *arithmetic only* — the rendered frame must be
  bit-identical whether they are repaired or not.

---

### What I expect to have to decide

If P1 and P3 hold, the tail is a **freeze of a field that is 96 % already at
rest plus a few hundred projectiles**, and the fix is not a re-bake: it is to
finish the projectiles' trajectories honestly and give the sill/floor a
footprint they cannot leave. If P3 is refuted and this is tunnelling, the fix
is a solver setting and a re-bake is on the table — at 2h25m, and I would say
so before spending it.

---

## ADDENDUM — P5 sharpened, written after reading `_pvb_post` and BEFORE measuring

`build_breach_sim._pvb_post` makes the PVB a `GENERIC_SPRING` with **hard linear
limits at +-0.045 m on all three axes** (`use_limit_lin_*`), not just a spring,
and `THRESH_PVB = 0.9`. The bond is `t_bond_per_m * L` = `100 * L`. The glass
edge is `THRESH_GLASS_EDGE = 2.5`.

Bullet's `setBreakingImpulseThreshold` is an **impulse in kg m/s**, and it is
tested against the impulse the constraint has ALREADY applied. So the last
impulse a joint is permitted to deliver before it is allowed to break is the
threshold itself — and the velocity that buys depends on the **mass on the other
end**, which none of these numbers was ever divided by. The shards are grams:
`bu4.json` puts the blow-up population's median mass at **10.38 g**.

    PVB   0.9   / 0.01038 kg =  87 m/s
    bond  100*L / 0.01038 kg = 289 m/s at L = 0.030 m
    edge  2.5   / 0.01038 kg = 241 m/s

Cluster B peaks at **106.5 m/s** and cluster A at **137.05 m/s**, both inside
that envelope, both with no contact. So:

- **P5a (primary, quantitative):** for the 828 blow-up shards (peak > 60 m/s),
  the product `mass * peak_speed` — an impulse in kg m/s — concentrates at the
  constraint thresholds rather than being spread. Specifically I predict the
  **median of `m * v_peak` over cluster B lies between 0.5 and 3.0 kg m/s**,
  i.e. within a factor of ~3 of `THRESH_PVB = 0.9`, and NOT at the 0.01-0.1
  scale that a contact with a 16.4 m/s car would produce (0.01038 * 16.4 =
  0.17, and a bounce at most doubles it).
- **P5b (negative control):** for a matched set of ordinary shards from bays 4
  and 5 that never exceed 60 m/s, `m * v_peak` is **at least 5x smaller** in the
  median. If both populations sit at the same impulse the measure is not
  discriminating and P5a proves nothing.
- **P5c `[2nd]`:** peak speed and mass are **inversely** related across the
  blow-up population — `log v_peak` vs `log m` has a slope near **-1**, which is
  what `v = J/m` at fixed J looks like and what a contact-driven field does NOT
  look like (a collision imparts a velocity, not an impulse).
- **P5d `[2nd]`:** the blow-up population is over-represented among
  **laminated** shards, because only laminated shards get a PVB constraint
  (`if s["laminated"]`).

**If P5a and P5c hold, cluster B is not a collision at all** and the fix is
dimensional, not a solver setting: thresholds have to be expressed as the
velocity change they are allowed to buy the lighter of the two bodies.

---
---

# OUTCOMES — appended after the measurements, nothing above edited

Scripts: `sim/tmp/cont/an_{tail,sink2,visible,impulse,hang,hang2}.py`,
`sim/tmp/cont/p1_extrap.py`, `sim/tmp/cont/p4_occlusion.py`. Gate:
`sim/rest_gate.py`. Renders: `work/cont/`.

| | prediction | outcome |
|---|---|---|
| **P1** | the field freezes, `max\|p(f2901)-p(f1165)\| == 0.000 m` | **HELD.** 34,164 F-curves, census `{CONSTANT: 34164}`, zero exceptions. Evaluated in `film14_breach.blend` at f1166/f1400/f2565/f2901/f2978: 0.000 m and **0 objects moved**, against a positive control of 42.417 m over 3,795 objects between f1000 and f1050. |
| **P1 `[2nd]`** | every object CONSTANT on all 7 channels | **HELD**, and the count is 34,164 curves rather than the 3,806 × 7 = 26,642 I guessed — 3,796 shards × 9 (loc 3 + quat 4 + 2 hide channels). |
| **P2** | the freeze is at f1165, not at the beat 3→4 boundary | **HELD**, and stronger than predicted: the wound leaves the frame at **f1051**, five frames *before* beat 3 ends. Beat 3 ends on the car in the corridor with no wall in shot (rendered, `work/cont/f1056_hd.png`). |
| **P3** | ≥ 500 of the 627 left the floor's footprint horizontally | **REFUTED AS STATED, AND THE PREMISE WAS WRONG.** There are not 627 bodies below the floor; there are **70**. Of those 70, **55 walked off the edge** and 15 tunnelled — the ratio predicted, on a population 9× smaller. See P3b. |
| **P3b** (not predicted) | — | **The 627 was the instrument.** `check_sink` bounded the lowest point as `origin_z − max\|local v_z\|`, and a shard's local z is the *pane's* vertical. Rotating the vertices: 627 → 70. The 557 dropped have true lowest vertices from **+0.0001 to +0.1055 m** — every one above the floor. `found_ONLY_by_the_rotation` = 0, so nothing is lost. |
| **P3 `[2nd]`** | the 108.24 m/s body is sub-floor and within 20 % of free fall | **HALF HELD, AND THE QUANTIFIER FAILED.** It is sub-floor (`GS_b04_00446`, final z −154.53 m). But free fall from its crossing predicts 56.30 m/s and it measures 108.24 — **ratio 1.92**, not 1.0 ± 0.2. It left the ground already travelling much faster than the −4.84 m/s it crossed z = 0 with, so something accelerated it after it left. Reported as failing. |
| **P3 `[2nd]`** | ≥ 25 % of the 2,275 movers are sub-floor | **REFUTED.** 70 of 2,275 = **3.08 %**. The movers are a settling pile: 2,205 above-floor bodies at p50 **0.056 m/s**, p99 0.414, max 2.01, with only **7** over 1 m/s. |
| **P4** | zero sub-floor bodies visible | **HELD geometrically, NOT by ray-cast.** All 70 sight lines cross z = 0 strictly between camera and body at f1322/f2565/f2901/f2978, landing at x 35…617, y ±38 (f2901) — built ground, and the rendered f2901 crop shows continuous paving with no shards. **The ray-cast arm did not run**: `scene.ray_cast` over 28,781 objects was OOM-killed locally with 2 GB free. So this is a geometric argument plus a picture, not a traced ray, and it assumes the ground sheet is opaque and present at those points. |
| **P5** | cluster B is a stretched bond: median bonded-neighbour separation > 0.10 m at peak−1 | **REFUTED.** It is **0.0019 m**, and **0.0 %** of the hot population is over 0.10 m on bonds or over the PVB's 0.045 m limit. Nothing is stretched. |
| **P5a** | `m·v_peak` for cluster B in [0.5, 3.0] kg m/s | **HELD numerically** — median **0.834**, against `THRESH_PVB = 0.9`. |
| **P5b** | ordinary shards ≥ 5× smaller in `m·v_peak` | **REFUTED, and it kills P5a's interpretation.** Ordinary shards median **0.616**, ratio **1.34**. The measure does not discriminate, so P5a's proximity to 0.9 proves nothing. |
| **P5c `[2nd]`** | log v vs log m slope ≈ −1 over the hot set | **REFUTED.** Slope **−0.017**, r = −0.06 — no mass dependence at all. The *ordinary* population does show it: −0.358, r = −0.80. The blow-up is not `v = J/m`. |
| **P5d `[2nd]`** | laminated shards over-represented among the hot | **REFUTED.** Field 14.20 %, hot **14.37 %**. |
| **P5 outcome** | — | **The clusters are not in the film.** `bu1..bu9` measured `breach_bake.npz` — bond 4000, superseded. Identity proved: the shipped film table's last frame is bit-identical to `breach_full_m1.npz` (0 m) and **626.781 m** from `breach_bake.npz`. Same script on both: over 60 m/s **828 → 7**, peak **137.05 → 110.41**, cluster A **480 → 0**, cluster B **348 → 0**, with every other input identical. |
| **P6** | the wound reads as a dark hole at f2901 | **REFUTED BY THE PICTURE.** It reads as **crazed glass in a complete standing frame**, with debris on the apron. The static round-1 mullion grid runs unbroken across the aperture. R2-095/R6, seen from a real beat-6 frame. |
| **P6 `[2nd]`** | mullion 5's stub is legible at f2565 | **UNANSWERABLE AS ASKED.** At f2565 the wound's projected position is **behind the gantry pylon**, and at f2575 (the closest beat-5 approach, 184 m) it is destroyed by motion blur. Beat 5 never gives a legible look at the wall. |
| **P7** | the fix moves only the treated population | **NOT EXERCISED.** No tail fix was applied, because the freeze was measured to be off camera and the residual under a pixel. The negative-control design stands unused. |

---

## CORRECTIONS FROM THE COORDINATOR, APPLIED

Three numbers in my brief were superseded mid-task. What changed, and what it
did to the results above:

**"2,275 bodies not at rest" vs "1,599".** Both are right and they are
different measurements. Settled in `sim/rest_gate.load_state`:

| artefact | measure | over 1 mm/frame | worst |
|---|---|---|---|
| the reconstruction | step between the last two FILM keys, f1164→f1165 | **1,599 of 3,796 (42.1 %)** | 3.049 m/frame |
| the raw bake | last SIM step (1/240 s) scaled to a film frame | **2,275 of 3,948 (57.6 %)** | 4.510 m/frame |

The gap is the decimator — it drops any key whose linear reconstruction error
is under 1.5 mm, which is exactly the small residual motions — and one film
frame spans ten sim frames at the end of beat 3's ramp, so the reconstruction
reports an average where the bake reports an instantaneous velocity. The gate
now uses the reconstruction, per `verify_breach.run`'s own rule, and reports the
bake beside it as `solver_state`. **It does not change the verdict**: the
residual at the next sighting falls 0.518 → 0.103 px, inside a 1.0 px tolerance
either way.

**The `matrix_world` trap.** `p1_extrap.py` did read `matrix_world`, so it was
exposed. Re-measured on the **F-curves** in `sim/rest_gate.py --blend`, which
are defined whether or not anything is drawn: 26,572 transform curves, census
`{CONSTANT: 34164}`, `max|delta| = 0.0` at f1166/f1400/f2565/f2901/f2978 with
**0 curves moving**, positive control 42.417 over 26,524 curves. The two methods
agree to the last bit — 42.41694641113281 either way — so P1 stands, but it now
stands on the arm that cannot be fooled.

**"627 below the floor" splices two instruments.** Agreed, and independently
reproduced: 70 rotated vs 626/627 axis-aligned (I measure 627 at the 4 mm
tolerance; the difference is one body at the boundary), with every dropped body
above the floor. R2-197 owns the cause and the fix is next-bake-only, so the 70
are still in `film14_breach.blend`.

**`check_persist` returned no verdict for 1,813 frames.** Not in my predictions
at all — I had not looked at it. Fixed as R2-200: it now REFUSES with
`PASS=False`, names the frames it cannot see, and names the arm that can.
