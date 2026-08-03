# R2-042 — which transit curve is right: the arc or the chord

Decided 2026-08-02, in the main thread, from the source files themselves.

---

## 1. THE VERDICT

**The R150 arc is right. `tools/build_telemetry.py`'s chord interpolation is a bug,
and it violates that same file's own declared policy.** Confidence: high.

What would change my mind: evidence that the transit merge was *deliberately*
exempted from the file's stated analytic-geometry policy — a comment, a changelog
entry, or a spec field marking leg 2 as a polyline rather than an arc. I looked and
found none; the only comment at the site describes what the code does, not why.

**THE REBUILD (#53) MAY START NOW.** Fixing the telemetry moves no world geometry.

---

## 2. THE EVIDENCE

### (a) The file forbids, in its own header, exactly what it does at line 281

`tools/build_telemetry.py` lines 30–34:

> *"Geometry is evaluated ANALYTICALLY from the spec's elements (straights and
> circular arcs), not from the 202 exported control points. The control points are
> a rendering convenience with a stated worst chord error of 0.123 m; integrating
> speed along chords would accumulate that error into the lap time and hence into
> the audio sync."*

The file states the policy, states the mechanism of harm, and names the consequence
— lap time and audio sync. Then, 250 lines later, line 281:

```python
# Transit world positions come from the leg endpoints, interpolated; the lap
# then continues from the start/finish line.
pts = [legs[0]["from_world"]] + [l["to_world"] for l in legs]
cum = np.concatenate([[0.0], np.cumsum([l["length_m"] for l in legs])])
tx  = np.interp(tr_s, cum, [p[0] for p in pts])
ty  = np.interp(tr_s, cum, [p[1] for p in pts])
```

The **lap** is evaluated analytically, as the header promises. The **transit** is
not. The comment describes the mechanism without ever claiming it is correct.

### (b) The declared leg is unambiguously an arc, and its sagitta IS the discrepancy

Measured from `docs/circuit_spec.json`:

| leg | declared `length_m` | chord \|to−from\| | difference |
|---|---|---|---|
| 0 | 11.980 | 15.000 | **−3.020** (see §6) |
| 1 | 49.600 | 49.600 | 0.000 — straight |
| 2 | **104.700** | **102.607** | +2.093 — the R150/40° merge |
| 3 | 215.600 | 215.648 | −0.048 |

For R = 150 m, θ = 40°:

```
arc length  = R·θ            = 150 × 0.69813 = 104.72 m   -> declared 104.700  ✓
chord       = 2R·sin(θ/2)    = 300 × 0.34202 = 102.61 m   -> measured  102.607 ✓
sagitta     = R(1−cos(θ/2))  = 150 × 0.06031 =   9.05 m   -> measured    9.044 ✓
```

The declared length is the **arc** length to three decimal places, and the sagitta
of that arc is *exactly* the 9.044 m divergence everyone has been measuring. There
is no ambiguity about what the spec declares.

### (c) It is internally inconsistent, so it is wrong under EITHER reading

`cum` is built from `length_m` — **arc** lengths — while `tx`/`ty` interpolate
position along **chords**. The car therefore advances **104.700 m of arc-length
distance along a 102.607 m chord**: 2.093 m of distance error on that leg alone.

This matters more than the lateral error, because it means **speed is corrupted
too**, not merely position. `tr_s` drives `tr_v`, `tr_dt` and hence the frame
timing. A chord that is honestly parameterised would at least be self-consistent;
this one is not. Whatever the intended curve, this code does not implement it.

### (d) The correction table was already there, and already said so

`world/build_barriers.py` §21 carries an independent correction table peaking at
**+8.95 m**, ending with the comment:

> *"Delete this the day the telemetry and access_route_point agree."*

Someone hit this before, treated the ribbon as authoritative enough to correct
*against*, and left a note saying the disagreement was the defect.

---

## 3. THE EVIDENCE AGAINST — stated honestly

- **The prior pointed at the convenient answer.** "Arc is right" is the reading that
  lets a held multi-hour rebuild start immediately. That is exactly the situation in
  which a conclusion deserves suspicion, and it is why this was checked against the
  source rather than reasoned from plausibility.
- **A stalled agent reported a decisive-sounding comment that does not exist.** Its
  final line quoted the beat-4 camera as saying *"cutting the chord of the R150
  merge; the car is on the arc below."* A full-tree grep finds no such text. The
  nearest match is `world/build_surface.md:215`, *"20 % of the arc below"* — about
  apex-station placement, where "below" means further down the document. **That
  quote is not evidence and must not be cited.** None of the verdict above rests on
  it.
- **The chord has been the shipped behaviour for the whole project.** Every frame of
  telemetry, the camera rig and the audio master were built on it. Longevity is not
  correctness, but it does mean this fix has a real blast radius (§5).

---

## 4. THE CHANGE REQUIRED — do not make it as part of the rebuild

**File:** `tools/build_telemetry.py`, around lines 277–283.

Replace the endpoint `np.interp` with the same analytic element evaluation the lap
already uses: straights evaluated linearly, circular arcs evaluated as arcs, so that
arc-length parameter `tr_s` maps to a point genuinely that far along the element.
`world_contract.access_route_point` already does exactly this and is the reference —
but note **RULE 2**: the contract must not import from `tools/`, and `build_telemetry`
should not import the contract if that creates a cycle. Duplicating the evaluation is
acceptable here *only* if a test asserts the two agree; prefer a shared helper.

**Acceptance:** the rebuilt `telemetry.csv` must land within tolerance of
`world_contract.access_route_point` over all 219 transit frames — the mirror of
contract selftest [18], which currently asserts the *opposite* (that the contract
reproduces the telemetry's chord to 1.02e-4 m). **That selftest assertion must be
inverted when this lands**, or it will fail and it will be right to.

---

## 5. BLAST RADIUS, in dependency order

1. `telemetry/telemetry.csv` — regenerated. Transit x/y move up to 9.044 m; transit
   distance shortens by ~2.09 m on leg 2; **speed and per-frame timing change**.
2. `world_contract.py` selftest **[18]** — its assertion inverts (§4).
3. `world_contract.transit_keepout` — currently the UNION of both curves. Once they
   agree the union collapses to one curve. Safe to leave as a union; it is
   conservative either way. Not urgent.
4. `world/build_barriers.py` §21 — the +8.95 m correction table becomes deletable.
   **This is the note's own stated condition.** Verify it is a no-op before deleting.
5. **The camera rig** — Beat 4 re-times, so its 479 keys must be re-derived and the
   aim gate re-run. Beats 1–3 are unaffected (showroom); beats 5–6 shift only if
   transit duration changes, which it does (~2.09 m shorter at transit speed).
6. **THE AUDIO MASTER MUST REBUILD.** Telemetry is the single source of truth for
   motion *and* audio (#19, #35). Doppler is a retarded-time solve per ear off this
   file, so both the source trajectory and the emission timing change. The 124.0833 s
   master and every gate on it are invalidated. This is the expensive part.
7. `anim/filmtime.py` film-time mapping — re-check; beat 3 already offsets clocks
   6.4 s permanently and beat 4 sits immediately after it.

**No world geometry appears in this list.** That is the whole point.

---

## 6. FOUND, NOT LOGGED ANYWHERE — leg 0 is geometrically impossible

Leg 0 declares `length_m` **11.980** while its endpoints are **15.000 m** apart.
**An arc can never be shorter than its own chord**, so leg 0's `length_m` and its
`from_world`/`to_world` do not describe the same object.

11.98 m is the "11.98 m to the glass at 53.8 km/h" from Beat 2's note, so the likely
explanation is that the length is measured from the car's start position while the
endpoints span dais-origin to breach-plane — i.e. two different datums, which is
survivable but undeclared. **It is not proven benign.** Anyone touching leg 0 should
establish which datum each field uses before trusting either. Logged here because it
was found while measuring something else and belongs in `DEFECT-LOG-R2.md`.

---

## 7. IMPLEMENTED — 2026-08-02, R2-045 in DEFECT-LOG-R2.md

The verdict held. `tools/build_telemetry.py` evaluates the transit analytically,
importing `world_contract.access_route_arrays` rather than duplicating the arc, so
agreement is structural; `tools/transit_line_gate.py` re-derives the same arc from
`circuit_spec.json` alone (R = 150.0160 m over 39.9958 deg) as the independent
second method, and keeps the pre-fix CSV at `telemetry/pre_R2042.csv` as its
positive control. Selftest [18] inverted; 149 checks, 0 failed.

**Two things in S5 were wrong, and the artefact says so:**

1. *"transit distance shortens by ~2.09 m on leg 2; speed and per-frame timing
   change."* Neither happens. `tr_s`/`tr_v`/`tr_T` are integrated from `length_m`
   and never touched the positions, so **`t_s`, `s_m`, `speed_ms`, `speed_kph`,
   `accel_long_ms2`, `wheel_rot_rad`, `pitch_rad`, `z` and `wheelspin` are
   bit-identical over all 1743 frames**, as is every lap frame's x and y. What
   moves is the ground the car actually covers: leg 2's driven path **lengthens by
   2.079 m** to meet the arc length the file always claimed. Beats 5-6 do not
   shift; the 2978-frame, 124.0833 s film stands. The real speed defect was that
   `v_world` — which is what the audio uses — ran **2.078 % under the declared
   column through the merge**, and now runs 0.098 % under.
2. *"Beats 1-3 are unaffected."* Beats 1, 2 and 3 re-author **bit-identically**,
   which is stronger than the claim, but only because `author_beats2_5.py` was
   re-run: the sheet is one Hermite chain across beats 2-5 and it had to be
   re-solved to prove they did not move.

**Also settled: leg 3.** The decision doc did not reach it. The arc exits 5.023 m
left of the pit-straight centreline, so a car left on `access_route_point` would
cross the start/finish line 5.02 m wide of the lap's own first point. Leg 3 is now
the pit straight entered tangent with that offset decaying on a quintic ease —
zero slope and zero curvature at both ends, never more than 0.7405 m from the
spec's chord, and it removes the 18.67 deg and 1.33 deg yaw kinks the chord had at
the merge and at the line. (A cubic smoothstep was tried first and rejected: it is
still turning at the line, which stepped `accel_lat_ms2` 4.034 -> 0.000 m/s^2 at a
beat boundary.)

**S6 (leg 0) is answered and logged as R2-047.** It is not an impossible arc, it is
two datums: `15.000 - 3.020` (the measured car nose) `= 11.980` exactly. That is
also the mechanism behind R2-026's 1.25207. Left bit-identical on purpose — either
half-fix moves the breach frame.
