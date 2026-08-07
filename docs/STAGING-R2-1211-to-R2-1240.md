# STAGING — R2-1211 to R2-1240

Block: **THE RUBBER THE CAR LAYS DOWN AT LAUNCH.** The client, rewatching the
720p demo: *"tire marks on the showroom and concrete is not noticeable enough in
the first drive off the showroom etc."*

Nothing here is written into `docs/DEFECT-LOG-R2.md`; that file has one owner.

**Verdict in one line.** The client is right, and the reason is not faintness —
**on the showroom side there is no rubber at all, and the rubber that does exist
is painted across 34 metres of apron where the tyres never slip, while the only
place they do slip is a 24 cm patch on the turntable deck that nothing marks.**

> ## ⚠ THE PROPOSED APRON FIX WAS TESTED IN THE FILM AND DOES NOT WORK
>
> **R2-1225.** A matched A/B at f981 — one blend, one process, one camera, one
> sun, one seed, three link states of a single material — refutes the claim this
> block was building on.
>
> | | mean tone | **lateral gradient p99.5** | width at half depth |
> |---|---:|---:|---:|
> | **A** existing paint | −2.28 % | **0.324 %/mm** | 379 mm |
> | **B** `tyre_deposit`, N=60 | −0.20 % | **0.319 %/mm** | 119 mm |
> | **C** the concrete's *own* mottle | sd 7.21 % | **4.272 %/mm** | — |
>
> **The edge advantage is not there.** 0.324 against 0.319 %/mm is
> indistinguishable — against a synthetic-gate claim of 6.6×. B's transition is
> shorter but its amplitude is 3.2× smaller, and a gradient is the ratio of the
> two. **B is invisible at 1:1**; A is visible and reads as **mottle, not a
> mark**. The module's version reads about **a third as much** as what it
> replaces.
>
> **And the reason is deeper than tuning: the concrete's own lateral gradient is
> 13× either mark.** No mark of this kind on this substrate can win on edge
> contrast, because the substrate already has more edge than the mark does.
>
> ### Why the synthetic gate and the film disagreed by 20×
>
> Diagnosed by the module's author against their own result (R2-1233), and it is
> the most transferable finding in this block.
>
> **The gate's substrate replica was not the substrate.** `_concrete_substrate`
> carried `M_Surf_Concrete`'s Principled parameters and its bay hash and **none
> of its crazing, efflorescence, joints or grit**. So the replica gave the
> deposit ≈ **20× more amplitude** than the real material does — **−4.35 % in
> the gate against −0.20 % in the film** — and the 6.6× ratio was quoted with a
> denominator consisting of exactly the structure the replica had left out.
>
> **The control had already said so and it was filed as noise.** The gate
> reported *"substrate sd 41.39 %"* and set it aside as a lighting artefact.
> Measured properly that is the concrete's own **4.272 %/mm**, and it is the
> whole answer.
>
> **The rule this earns: a gate that measures contrast against a replica
> substrate must refuse to emit a contrast statistic at all unless the replica
> carries the real substrate's structure.** A ratio is only as real as its
> denominator, and a replica built from a material's *parameters* is not a
> replica of the material.
> **R2-1213, R2-1215 and R2-1219 all reasoned about the wrong axis** — including
> the correction that replaced "too weak" with "no edge". That correction was
> right that amplitude was not the problem and wrong about what was.
>
> **The hypothesis that survives, untested:** the mottle is *isotropic* and a
> tyre mark is *anisotropic and continuous over tens of metres*. What makes a
> real skid mark read is *longitudinal coherence* — two parallel lines the eye
> segments because they run unbroken along x — not the sharpness of their y
> edge. Every measurement in this block, mine and the module's, was taken
> **across** the mark. Nobody measured **along** it.
>
> **THE LESSON IS BIGGER THAN THE MARK, AND IT INDICTS THE CORRECTION AS WELL AS
> THE ORIGINAL.** This block went "too weak" → "no edge" → both wrong, and the
> two answers sit on the *same cross-section*. **A correction inherits the axis
> of the thing it corrects**, which is exactly how a second wrong answer looks
> like progress. Re-measuring more carefully on the axis you already chose feels
> like rigour and cannot find an error in the choice of axis. Nothing in this
> document caught it; it took a null result in the film.
>
> ### The prediction, stated BEFORE the measurement so it can be falsified
>
> Recorded in advance deliberately — R2-1214's floor sign was written the same
> way and turned out **wrong**, which was worth more than a retrofitted
> explanation would have been.
>
> The eye behaves as a **matched filter along the mark's axis**. Integrating a
> coherent line along x over N samples grows its signal as **N**, while
> isotropic mottle grows as **√N** — so **SNR grows as √(L / ℓ)**, with ℓ the
> mottle's correlation length and L the mark's coherent length.
>
> If ℓ ≈ 0.1 m and the mark runs 34 m, √340 ≈ **18×**. That is enough to make a
> mark at **a thirteenth** of the mottle's local contrast still read — which
> would explain the f981 null *and* why real skid marks read on real aggregate.
>
> **The falsifiable claims:** (1) the control's correlation length is short and
> roughly isotropic; (2) along-track integrated SNR rises as √L for the mottle
> and faster for a coherent mark; (3) at least one arm crosses a detection
> threshold at some L ≤ 34 m. **If the marks do not survive unbroken along x —
> if the substrate chops them into segments — the mechanism fails and no amount
> of amplitude or edge fixes it.** In that case the honest answer to the client
> is about the **concrete**, its mottle amplitude and correlation length, and not
> about the rubber at all. That would be a finding, not a failure.
>
> **What the module does deliver is containment**, which is a correctness win
> and not a visibility one: B is ≈0 outside |y| = 670 mm and back to ≈0 by
> 930 mm; A runs 350 → 970+ mm with no boundary anywhere.
>
> **Two limits on this verdict, both stated by the agent that produced it.**
> f981 is the *least* favourable of the four shortlisted frames, and **the launch
> patches were never in frame** — they are 31 m behind the car there, so this
> tests only the tractive *film*. The module's hard 12 mm patch edges, and the
> deck's measured **+23.2 %**, remain untested by any render.

---

## THE PREMISE CHECK FIRST — and it does not go the way R2-651 went

R2-651 established that a 720p verdict on surface appearance can be flatly
wrong: *"no texture"* on the asphalt was an artefact of the proxy, and the 4K
frames carry aggregate, joints and zone changes. The same question was asked
here before anything was authored — **can 720p even show this?**

Method: ray-cast **from** the screen against the real piecewise ground rather
than projecting world quads **to** it, so coverage falls out for free and the
frame edge and horizon clip correctly. Coverage-weighted, over all 433 camera
keys in beats 2–6. Pixel law from `itemkit.px_per_m` / `mm_per_px`; camera keys
from `docs/beat_sheet.json`, read only.

| surface | in N keys | coverage p50 | mm/px @4K p50 | mm/px @720p p50 | grazing p50 | **band @4K** | **band @720p** |
|---|---:|---:|---:|---:|---:|---|---|
| **the mark itself** | 29 | **0.040 %** | 1.75 | 5.26 | 5.8° | 3.5 – 842 mm | 10.5 – 842 mm |
| dais deck | 39 | **23.9 %** | 1.31 | 3.92 | 8.4° | 2.6 – 627 mm | 7.8 – 627 mm |
| dais platform | 39 | 3.8 % | 0.67 | 2.02 | 13.0° | 1.3 – 324 mm | 4.0 – 324 mm |
| delivery ramp | 23 | 1.8 % | 1.19 | 3.57 | 13.9° | 2.4 – 572 mm | 7.1 – 572 mm |
| showroom floor | 86 | 4.5 % | 3.31 | 9.92 | 7.5° | 6.6 – 1587 mm | 19.8 – 1587 mm |
| apron near | 62 | **62.1 %** | 2.73 | 8.18 | 26.2° | 5.5 – 1309 mm | 16.4 – 1309 mm |
| apron far | 77 | 2.3 % | 3.89 | 11.68 | 28.4° | 7.8 – 1869 mm | 23.4 – 1869 mm |

**The answer splits, and the split is the useful part.**

*The tonal footprint is not resolution-limited.* A mark's own footprint is a
200–600 mm feature and that is inside the band on every surface at **both**
resolutions, clearing the 720p floor by 25–75×. Contrast R2-651: *aggregate* is
2–6 mm, inside 4K's 2.6 mm floor and below 720p's 7.8 mm floor, which is
precisely why the proxy could not show it. A skid mark is two orders of
magnitude away from that boundary. **"The marks are there and 720p cannot show
them" is refuted.**

*But the mark is seen almost edge-on, and that does bite.* At the best key
(f813) the two patches together are only **0.071 % of the frame**, because
grazing is 5.8°. Each patch is 242 mm long × 251 mm wide; the width runs across
the line of sight and stays ≈ 213 px at 4K, but the length foreshortens by
sin 5.8° to ≈ **21 px at 4K and ≈ 7 px at 720p**. The mark reads as a thin
transverse bar, not a streak.

**The consequence for the fix, and it is the one that matters: authoring the
physically exact 24 cm patch and nothing else will read at 4K and will still be
marginal at 720p.** Correct is not the same as sufficient here. See R2-1215.

---

## THE STRUCTURAL FACT EVERY EARLIER READING OF THIS COMPLAINT MISSED

**The car does not launch on the showroom floor.** Per
`world/items/dais_delivery_ramp.py`, whose constants are parsed out of
`docs/circuit_spec.json` and which is identical by construction to
`anim/carrig._ramp_ground` — the function the car's 2,978 frames were solved
against:

- it launches on a **turntable deck at z = 0.340 m**, deck face radius 3.402 m
- runs down a **delivery ramp** from x = +3.70 to x = +6.30, falling to z = 0
- reaches the **showroom floor** only at x = 6.30
- **the glass plane is at x = 15.000** — the 10.6 in beat 2's last anchor is a
  *camera* position, not the glass
- the **concrete apron** (`SURF_AccessRoad`) begins at x = 15.000

So "the showroom" in the client's note is **four running surfaces**, in four
materials, owned by four modules — and the launch rubber lands on the one nobody
had been discussing. It is not even a floor: it is **brushed metal**
(`TurntableTop`, metallic 0.86, roughness 0.335–0.455).

---

## R2-1211 — the rubber is painted over 34 m where there is no slip, and absent over the 24 cm where all of it is

**This is the finding.**

### The deposit, derived not painted

From the telemetry, walked through `anim/filmtime.py` and `carrig.CarRig`:

| | value |
|---|---|
| rear rolling radius | **0.360 m** (not 0.378 — see below) |
| slip window | **film frames 817–827**, world t 0.0115–0.3865 |
| peak slip velocity | **19.20 m/s**, peak slip ratio **30.8** |
| tyre surface slid | **3.29034 m**, while the car moved 0.2416 m |
| **mark, per rear wheel** | **x −1.80000 → −1.55840, length 0.2416 m** |
| lateral | y = ± 0.79750 (`HALF_TRACK_REAR`) |
| height | z = 0.340, deck radius r = 1.75–1.96 |
| contact patch width | **251.1 mm** (\|y\| 0.672–0.923) |
| trailing edge | **hard** — terminates at 2.7 % of peak at hook-up, does not fade |
| **surface split** | **100.0000 % on `Turntable_Deck`.** Zero ramp, zero floor, zero apron |
| slip elsewhere in the lap | **none** — no corner-exit spin, no lockup |

Normal load contributes nothing: the rear axle sits at 0.5782 mg for the whole
window, **0.00 % modulation**. Pitch would move the patch 0.009 mm, roll
0.000 mm, steer is zero. **The profile is pure slip velocity.**

Normalised d(s) over the ten frames: 1.000, 0.954, 0.794, 0.646, 0.507, 0.381,
0.267, 0.168, 0.086, 0.027. Half the mass is in the first 60 mm. A 256-point
resample is in `work/r2_1211_rubber_tracks.json`.

### Against what is painted

`world/build_surface.py:2835-2841` paints launch rubber on `SURF_AccessRoad`
(`M_Surf_Concrete`): two streaks at `uv_su` |u| = 0.72 m, falling **linearly
from full strength at t = 0 (the glass plane, world x = 15.000) to zero at
t = 34 m** — world x = 15 → 49.

| | where rubber is deposited | where rubber is painted |
|---|---|---|
| along the route | x = −1.800 → −1.558 | x = 15 → 49 |
| length | 0.2416 m | 34 m |
| surface | turntable deck, z = 0.340, brushed metal | access road, z ≈ 0, concrete |
| **overlap** | **none** | |

Slip velocity over x = 15 → 49 is **exactly 0.0 m/s**. The car passes x = 15 at
16.2 m/s and x = 49 at 31.4 m/s, fully hooked up.

This is R2-651's defect rotated onto the other axis. R2-651 found rubber painted
a median 4.96 m *lateral* of the driven line; this is rubber painted 15–49 m
*longitudinal* of the only place the car ever slips.

The lateral error here is small but real, and confirmed not to be a coordinate
artefact — `uv_su` u = 0 is world y = 0 exactly on that span:

- painted at |y| = **0.72**, tyres run at **0.79750** → **77.5 mm inboard**,
  p50 = max (the car is dead straight there). The tyre runs on the *shoulder* of
  its own mark.
- painted core is 200 mm wide against a real contact patch of **251.1 mm** — the
  core covers 148 mm of it, **59 %**.

### The rolling radius was 0.360 all along, and 0.378 was a measurement artefact

Recorded because the wrong number nearly propagated into this block. An earlier
pass read 0.378 by pairing a **forward-difference** ω (rows 52→56) with a
**point** speed at row 52. Midpoint-matched it gives 0.360712. Three independent
confirmations of 0.360: `carrig.py` measures the tyre mesh at 0.35998; round 1's
`build/spec.py` declares `TYRE_R = 0.360`; and the telemetry is *constructed* as
`wheel_rot_rad = s_m / 0.36 + slip`, residual sd **8.0e-05 rad** over 1,683
no-slip rows — a peak-to-peak of 2.8e-04 that is exactly one unit of the CSV's
4-dp rounding of `s_m`. At 0.378 that residual drifts to 545 rad.

**This also settles which distance column to trust.** `s_m` is the constructed
basis; the earlier three-way disagreement between `s_m`, `x` and ∫`speed_ms`·dt
over the launch window was an artefact of the same bad radius plus reading `x`
as if the telemetry origin were the world origin. It is not: the car launches at
world x = −1.80.

### And a claimed lock-up that does not exist

The same bad radius produced an apparent negative-slip excursion after frame 8 —
the wheel supposedly turning slower than the car. **It is not there.** Outside
the 817–827 window the per-frame residual never exceeds 0.065 mm against a
0.101 mm quantisation floor; `carrig` makes rolling contact exact by
construction. No lock-up, no drag, no second deposit.

### Path agreement — R2-651's check, passed

Tracks derived from `car_anim_car.json`, then the telemetry walked
*independently* through `filmtime.py` + `carrig.CarRig` and compared over all
2,978 film frames: **p50 0.000282 mm, max 0.000701 mm.** The film-time map
checks out to 5.0e-07 s. The derived contact-patch path and the car's actual
rendered path are the same path.

---

## R2-1212 — on the deck, the ramp and the showroom floor there is no rubber at all, and there never was

`FloorPolished` (round 1,
`/home/zany/opus5-car-render/build/s03_materials.py:15-71`) is eleven nodes: a
base speckle, a two-octave roughness break-up, one bump. No rubber, skid,
deposit or scuff term. `grep -rn FloorPolished /home/zany/f1-round2` returns
**zero hits** — round 2 never re-authors it; it arrives as an appended datablock
via `tools/build_film_scene.py:316-333`. `A_ConcApron` and `A_ForecourtSlab`
(`build_architecture.py:1302 mat_slab`) have no rubber term either. Neither does
the turntable top.

**Confirmed on pixels, not inferred.** At f828 — 10 frames after
`launch_film_t` = 34.0718, the moment the deposit should be freshest — the deck
was cropped at its true height (z = 0.340) from
`render/showlight/p_a_f0828_e-3.628.png` and boosted 2.5× and 6×. It is a
featureless light-grey gradient. A 6× boost would make a 2 % tonal dip obvious.
There is nothing there.

The deck is **23.9 % of the frame at p50 and 32.8 % at peak, at 1.31 mm/px**.
This is not a small or a badly-resolved surface. It is a quarter of the frame,
empty.

---

## R2-1213 — the apron's rubber does render ~~and is 2–3× too weak to read~~

> **SUPERSEDED IN ITS CONCLUSION BY R2-1219 §5. The measurement below is real;
> the inference drawn from it was wrong.** Reproduced on an identical substrate
> under an identical camera and sun, `build_surface`'s launch paint measures
> **−18.79 %**, not −5.73 %. The −5.73 % is a *deviation from the local lighting
> trend* along a lateral sweep smoothed over a 0.9 m window, and a 640 mm
> feathered streak is largely absorbed into the trend it is being measured
> against. My estimator was the wrong instrument for this feature size.
>
> **The existing paint is not weak. It is strong — and it has no edge.** Its
> lateral gradient is **0.243 %/mm**, against a substrate whose own bay hash
> swings ± 14.5 %. A 640 mm feathered wash with an edge that soft reads as
> *mottle* at any amplitude. That, not faintness, is why the client cannot see
> it. Read the rest of this section as the record of how the defect was found,
> and R2-1219 for what it actually is.

Measured at 4K on `render/breach_f9/f9_3840_f1030.png` — lateral sweeps across
the access road, deviation from the local lighting trend inside the tyre band
|y| = 0.55–1.05 m:

| span (world x) | authored falloff | **measured deviation** | peak |
|---|---:|---:|---:|
| 15 – 19 | 0.94 | **−5.73 %** | −9.78 % |
| 19 – 25 | 0.79 | **−3.95 %** | −8.33 % |
| 25 – 33 | 0.59 | **−2.03 %** | −4.24 % |
| 33 – 45 | 0.29 | −0.15 % | −8.33 % |

The decay tracks the authored linear falloff, which identifies the signal as the
paint and not a shadow. **So it is there, and it does render — at 5.7 % mean
darkening at its strongest.**

Against what? `mat_slab`'s per-bay tone hash alone swings **± 14.5 %**, and the
measured trend-deviation sd on the same surface is 2.4–5.0 %. **A 5.7 % mark on
a surface carrying ± 14.5 % of its own variation is a 1–2 sigma feature** —
buried in the concrete's own mottle, which is what "not noticeable enough"
describes. Through the glass at f866 the same lines measure −3.2 % / −2.3 %,
below the surface noise entirely.

Why it is weak, from `build_surface.py:2835-2841` and `:2884`:

| channel | what the mark does | verdict |
|---|---|---|
| base colour | ≤ 0.55 mix toward linear (0.042, 0.039, 0.038), then multiplied by a stain noise remapped to 0.4–1.0 | under-driven |
| roughness | `rough −= launch * 0.18` (0.80 → 0.62) | present but small |
| specular | **untouched** — flat 0.32, no coat | **missing** |
| relief | **`launch` is not in the height chain at all** | **missing** |

---

## R2-1214 — the fix on the polished floor must NOT be a dark albedo mix

Stated here because it is counter-intuitive and it is the trap.

`FloorPolished`'s base colour is a ramp between linear **0.030 and 0.068**
(mean ≈ 0.044). The rubber tone already used on the apron is linear **0.042** —
**brighter than the darker half of the floor's own base colour.** A rubber smear
of the apron's pigment laid on the showroom floor would *lighten* it.

The floor's blacks are dark because of a **0.45-weight clearcoat at 0.045
roughness over a 0.055–0.155 base** (Specular IOR Level 0.55, IOR 1.52). Those
pixels are lifted off zero almost entirely by specular return, and real rubber
on polished concrete kills that coat.

So the floor's mark is a **roughness and coat-weight modulation with a
near-neutral albedo**, not a pigment mix — which is also what the client's own
note implies about a polished indoor floor. It carries a crushed-black risk the
apron's does not: suppressing the coat removes the one thing holding those
pixels above zero.

> **THE FLOOR'S SIGN IS ASSERTED HERE AND HAS NOT BEEN MEASURED. Treat it as
> unverified until the floor gate lands.** This section was written before the
> deck was measured, and the deck is the cautionary case: its sign was left
> unstated, everyone assumed "rubber = dark", and it came back **+23.2 %
> brighter**.
>
> The floor is predicted to go the *other* way from the deck, and the two
> predictions are consistent rather than contradictory — but only because the
> substrates differ:
>
> * **Deck — a conductor** (metallic 0.86, base 0.048). It has **no diffuse
>   lobe**; a dielectric film *adds* one. **Brighter.** Measured.
> * **Floor — a dielectric** whose blacks are held off zero almost entirely by a
>   0.45-weight coat. Rubber *kills* that coat and removes the return.
>   **Darker.** **Predicted, not measured.**
>
> The mechanism is the same in both cases — a rubber film replaces the
> substrate's interface — and it reads opposite because one substrate's light is
> specular-from-metal and the other's is specular-from-coat.

**AND THE FLOOR PREDICTION ABOVE IS WRONG. The floor is predicted BRIGHTER too,
and the reason is one I had no way to see from the substrate alone.**

I reasoned about what a rubber *mark* does to a coated dielectric. **No mark
lands on the floor.** The floor receives only the **10.6 nm tractive film**, and
that is precisely the thickness at which the three deposit scales diverge
(R2-1221). Under the corrected model the coat is **broadened, not removed**:

| | wetting-driven (superseded) | interface-driven (corrected) |
|---|---:|---:|
| Coat Weight | 0.45 → 0.2401 (**47 % suppression**) | 0.45 → 0.4244 (**5.7 %**) |
| Roughness | — | 0.105 → 0.342 |
| Coat Roughness | — | 0.045 → 0.237 |

A broadened coat at essentially full weight scatters the same energy over a
wider lobe. **That reads brighter, and it makes the crushed-black warning above
likely moot rather than live.**

> **THE CAP STAYS ANYWAY, AND NOT OUT OF TIMIDITY.** The coat-suppression cap
> earns its place the moment an optically thick mark lands on a coated
> dielectric. This film is not that, but a **launch patch** would be — 11.0 µm,
> which saturates every scale. Relaxing the cap because the *film* is harmless
> would remove the guard exactly where it is needed.
>
> **AND THE R2-082 GATE IS NOT SETTLED BY THIS.** The module's floor arm is lit
> by the contract sun, not the showroom's 61-lamp rig — the film blends OOM on
> this 11 GB box. Its exposure is solved so the *control* floor sits at the 0.10
> mean measured on `render/showlight/p_a_f0828_e-3.628.png`, then shared by both
> arms. **That makes the delta trustworthy and the absolute black level a
> stand-in.** A 0.0000 % result from that scene is evidence, not the gate. The
> gate is a beat-1/2 film frame and has still never been run post-levelling.

The **deck** is a different problem again: brushed metal at metallic 0.86,
roughness 0.335–0.455. On metal a rubber film is mostly a **metallic → dielectric
transition plus a roughness rise** — it kills the anisotropic brush sheen.

> **AND THE SIGN IS THE OPPOSITE OF EVERY OTHER SURFACE IN THIS DOCUMENT.**
> This section named the mechanism and never stated which way it goes, and the
> first clean measurement of the deck settles it: the launch patches read
> **+23.2 %** — a **brightening**, and **15× the apron's derived deposit**.
> A conductor at base 0.048 has **no diffuse lobe at all**; making it dielectric
> *adds* one. **A tyre scuff on dark machined metal is a pale smear, not a black
> one.** Anyone authoring to the intuition "rubber = dark" will build it
> backwards here — and this document encouraged that intuition for four
> sections before anything measured it.

So the deck is where the **derived physics actually delivers** — +23.2 % against
the apron's +1.56 % — and R2-1216 is where it collides with what the camera can
see. Both are true at once and neither cancels the other.

**R2-082's constraint, and a gap in it.** R2-082 has *no entry* in
`docs/DEFECT-LOG-R2.md`; it survives as prose in `world/film_exposure.py:225-228`
and as the levelling identity in `world/showroom_lighting.py:44-52`
(`LIFT_STOPS = −FILM_EXPOSURE = +3.628`, every interior lamp × 12.3634).
**There is no post-levelling black-level measurement of any beat-2 frame on
disk** — the only `exposure_histogram` run on a beat-2 frame is the *pre*-levelling
`render/exposure_beats/beats.json` at `crushed_lo_pct 2.498`.

One measurement was taken to stand in that gap:
`render/showlight/p_a_f0828_e-3.628.png` gives **0.0000 % pure black**, frame
luminance min 0.00476, deck track lines at mean 0.155–0.327. The deck is a
*light* surface and a mark on it is safe. The floor proper measures ≈ 0.10 and
is not. Any floor mark must be re-gated before it ships.

---

## R2-1215 — the physically exact mark is not sufficient on its own, and the honest way to extend it

The exact deposit is two patches 242 × 251 mm, seen at 5.8° grazing, ≈ 7 px tall
at 720p. Author only that and the client will look at the next 720p cut and say
the same thing again.

**Do not answer that by painting a longer mark by eye — that is how R2-651
happened.** The defensible extension is a term the model is currently missing.

`carrig` makes rolling contact **exact by construction** outside the wheelspin
window. That is a kinematic simplification, not physics: a driven tyre
transmitting tractive force always runs a non-zero longitudinal slip ratio,
typically 2–8 % under hard acceleration. That micro-slip is exactly why real
acceleration zones rubber in, and the telemetry already carries the quantity it
depends on — `accel_long_ms2`, real data, not invented.

Order of magnitude, to show it is a wash and not a mark: over x = 15 → 49 the
car goes 16.2 → 31.4 m/s in ≈ 1.4 s; at a 3–5 % slip ratio that is ≈ 0.6–1.0 m/s
of slip velocity, ≈ 1 m of tyre surface slid — **about 30 % of the launch's
3.29 m, but spread over 34 m instead of 0.24 m**, i.e. ~~roughly 1/140 of~~
**1/460 of the mean and 1/1040 of the peak** areal density (corrected in
R2-1219 §1; the 1/140 dropped the 30 % factor and the two sentences disagreed by
3.3×).

**And the conclusion that follows from the corrected number is not the one this
section drew.** At that density the film transfers ≈ 10.6 nm of rubber over
0.34 % coverage — which changes no albedo at all. The whole effect is *gloss*,
and glossier concrete under a bright sky at 30° is **brighter**: the derived
single pass measures **+1.66 %**, not a darkening. **No visible pigment on that
apron is derivable from this car's single pass**, which also means the existing
paint was never a physics claim. See R2-1219.

Recommended shape of the fix, in priority order **(revised — the first draft of
this list put the deck at number one, and R2-1216 shows that was wrong)**:

1. **Re-base and ~~strengthen~~ SHARPEN the apron streak.** It is the only
   surface the fix can actually be judged on. Move it from |u| = 0.72 to
   0.79750 so the tyre stops running on the outboard shoulder of its own mark,
   widen the core from 200 mm to 251.1 mm, replace the arbitrary 34 m linear
   falloff with the derived profile, and give it the specular and relief
   channels it lacks entirely.

   > **The target changed once it was measured properly.** This originally read
   > "the number to beat is −5.73 %", i.e. make it *darker*. That was wrong on
   > both counts: the existing paint measures **−18.79 %** and is already strong
   > (R2-1219 §5), and the module's replacement is *weaker* in mean tone at
   > N=60 (−4.21 %). **The number to beat is the EDGE: 0.243 %/mm.** A 640 mm
   > feathered wash reads as mottle on a substrate whose bay hash swings
   > ± 14.5 % no matter how dark it is. Strengthening it further would have made
   > a darker smudge, not a mark.
2. **Add the tractive-slip term** driven by `accel_long_ms2`, so that falloff is
   derived rather than arbitrary.
3. **Author the launch patch on the deck — time-gated, as a correctness detail,
   not as the headline.** It must not exist before film frame 817.
4. **Every mark instanced once, varied per instance** — no stamp reused. The
   named failure on this project is *"one tree spammed 100 times"*.

---

## R2-1216 — the deck mark can never carry this fix, and painted statically it is a worse defect than the one being fixed

Measured against the **live** camera (`render/film17_path.json`, sha256-verified
against `docs/LIVE-CAMERA.md`). Note `docs/screen_presence.json` was measured
against a path that document itself declares stale, and its beat-1 numbers are
void; this supersedes them.

- **The car's own body covers both patches until film frame 837.** They are
  exposed for **five frames**.
- Best case, f837: **3.5° grazing, 3,452 px total, ≈ 8 px deep.**
- **The only good angles on that ground are f374 (27.6°) and f424 (42.7°) — both
  before the launch.** So a *statically* painted deck mark would sit visible
  under a **parked car for ≈ 473 frames of beat 1**.

That last point is the one that matters: the obvious implementation of the
physically correct fix ships a bigger, longer-lived defect than the complaint it
answers. **Any deck mark must be gated on scene time to frames 817+.** It is now
gated, and `--bindtest` measures 0 lit pixels before f818.

This is why the priority list above was inverted. The deck is 23.9 % of the
frame; *the patches on it* are 0.040 %.

> **REVISED ON MEASUREMENT — author it after all.** This section originally
> concluded the deck patch was "worth 5 frames at 8 px" and should be dropped if
> gating proved awkward. The first clean measurement (R2-1214) puts the patches
> at **+23.2 % over 13,112 px** — high contrast, and the *opposite sign* to what
> was assumed. Five frames of a 23 % feature is a real thing on screen, not a
> rounding error; five frames of a 3 % one would not have been. **The exposure
> argument was right and the contrast assumption was wrong, and only the second
> one decided whether to build it.** Build it: it is cheap, it is now correctly
> gated, and it is the one place on this whole drive-out where the derived
> physics produces something the eye can actually find.
>
> **Confirmed under the corrected physics.** The +23.2 % survives the three-scale
> model *exactly*: the launch patch is **11.0 µm** of rubber, which saturates all
> three scales, so `wetting = interface = 1.0000` inside the mark and Metallic
> goes 0.86 → 0.0516 under **both** models — a delta of **+0.0000**. Only the
> surrounding film band moved, which is the spurious +52.2 % of R2-1221
> disappearing and the metal correctly staying metal. The number this revision
> rests on is not a casualty of the correction that invalidated its neighbours.

---

## R2-1217 — the delivery ramp is not in the film at all

`dais_delivery_ramp` is **`HOLD` / `GATE_NOT_ACCEPTED`** in
`world/items/PLACEMENT.json` (only 4 of 42 items are `PLACE`), and
`tools/build_film_scene.py:298` composites only `Floor`, `GW_*`,
`Turntable_Deck`, `Platform_Dais`. **The car currently drives on nothing from
x = 3.31 to x = 6.30.** Derived deposit there is 0.0, so it does not block this
block — but it is a hole in the floor of the showroom and it belongs to whoever
owns placement.

Related: `world/items/access_road_slab.py` and its "unrubbered, no racing line"
manifest are *also* `HOLD` and govern nothing. An earlier reading of this block
treated that manifest as a contract forbidding the apron fix. **It is not a
contract.** The shipped apron is `build_surface.py:2834-2840`, whose own comment
reads *"the car has been down here exactly once, so the rubber is a single pair
of streaks either side of the launch axis, not a rubbered-in line"* —
strengthening those streaks is consistent with the shipped design, not a
violation of it.

---

## R2-1218 — the verification plan, and what it costs

**Every frame needed for the diagnostic pass already exists at 720p on disk**
(`/home/zany/vast-render/out2/seq/r2full/`). Looking at the current state costs
**$0**, and it was done: at f965, f973, f981 and f1030 the sunlit apron is
visibly clean behind a car that has just launched through it. The complaint
reproduces by eye in exactly the frames the client watched.

Shortlist for the 4K A/B, by surface, ranked by grazing angle × coverage:

| surface | frames | best |
|---|---|---|
| **concrete apron** | **981, 973, 965, 1030** | f981 at 44.1° / 16.4 % |
| showroom floor | 856, 872, 864 | f856 at 15.9° / 6.6 %, 582 px/m |
| dais deck | 837, (424, 374 pre-launch) | f837 at 3.5° / 0.042 % |

Costs, measured, not estimated:

| | |
|---|---|
| 4K frame | **$0.019 – 0.031** |
| 720p frame | $0.0053 |
| **apron-only A/B** (4 frames × 2) | **≈ $0.35** |
| full 12-frame A/B (24 renders) | ≈ $0.75, worst case $0.91 |
| same via `--zoom` crops | ≈ $0.55 |
| credit | **$60.56** (was $62.46 earlier in this same block) |
| **the 4K master itself** | **$74 – 81 — more than the account holds** |

**That last line is the one to act on, and the gap is widening.** Credit fell
**$1.90 during this block without a single frame being queued by it** — rented
cards idling. The master does not fit in the remaining credit today, and every
idle hour makes it fit less well. Not this block's problem to solve, but it must
not be discovered at delivery.

**Routing.** Send to **broker 1** (`VASTRENDER_URL=http://127.0.0.1:8760`). A
bare `rq anim` **self-routes to broker 2**, where the client's own beat-1 proxy
job runs — last seen **774/792**, `VERIFIED — every frame present, complete,
consistent, and not blank`, confirmed untouched.

Two things moved mid-block and invalidate any cached command line. **Broker 1
swapped cards**: `47049525` was destroyed and replaced by **`47090933`** at
$0.4147–0.436/hr on a *direct IP* (`host-A:PORT`) rather than a
`*.vast.ai` relay. And the per-frame seconds above were measured on `47039886`.
**Host lottery on this market is ± 45 % on speed**, so treat the timings as
indicative until one frame confirms them on whatever card is live; the dollar
conclusion is unaffected. Note also that `vastctl status` lists **only broker
1's card** by design — the two brokers run under different labels so they cannot
reap each other. Check both, or use `panic.sh`, for a complete view.

**Tooling gap.** No single script performs a matched A/B. `tools/peep.py ab`
**asserts nothing** — it will label two unrelated shots BEFORE/AFTER without
complaint. Pass `--exposure -3.628` explicitly **on both arms** (the worker
re-asserts an explicit value after `frame_set`; a null one it does not), and
prefer one blend with a toggle over two blends, because `view_transform` and
`look` cannot be set over the protocol and are recorded nowhere.

---

## THE OCTAVE PRESCRIPTION — so this does not repeat the circuit's mistake

The circuit road shipped twenty procedural layers of which **eight were above
the camera's resolvable band, nine below, and one inside**. Intersecting the
bands measured above across all surfaces at both resolutions:

- **below ≈ 2.4 mm** — below the band on every surface. Material only; never
  pattern, never geometry.
- **12 – 300 mm** — inside the band on **every** surface at **both** 4K and
  720p. This is where the mark's structure must live: streak edges, the
  shoulder/centre density split across the 251.1 mm contact patch, longitudinal
  striations, scuff mottle.
- **above ≈ 572 mm** — past the ceiling on the deck and the ramp; reads as a
  shape, not a surface.

Amplitudes come from `itemkit.relief_amplitude_for(m, λ)`, **not typed** — the
law exists because 14 of 28 modules once shipped a dead bump stack, and because
every relief stage in all four of these materials is currently a typed literal
(`PAVING_RELIEF`, `build_architecture.py:915-923`; `strength`/`distance` pairs at
`build_surface.py:2887-2888`; `s03_materials.py:66-67`). For reference:

| λ | m = 0.12 | m = 0.28 | m = 0.45 |
|---:|---:|---:|---:|
| 12 mm | 0.051 mm | 0.118 mm | 0.190 mm |
| 25 mm | 0.106 mm | 0.247 mm | 0.396 mm |
| 120 mm | 0.507 mm | 1.183 mm | 1.903 mm |
| 300 mm | 1.267 mm | 2.958 mm | 4.758 mm |

**And the sign is not obvious.** On polished floor and brushed metal, rubber is
a film: near-zero relief, all the signal in roughness, coat and metallic. On the
concrete apron, rubber **fills** the surface texture — so where deposit is dense
the correct move is to *reduce* the existing aggregate relief
(`M_Surf_Concrete`'s 2.29 mm and 24.11 mm stages), not add to it. The current
mark does neither.

---

**The prescription now has an instrument, and it is no longer this block's.**
`itemkit.detail_for(λ)` derives the fractal octave count instead of the house
`detail=6`/`detail=8` defaults, and `itemkit.finest_octave_for(λ, detail)` is the
audit direction. The floor is **not typed**: it is `resolvable_mm(..., px=2.0)`,
and that 2 px is the same 2 px already implicit in this document's own table —
every per-surface band floor above is exactly 2 × that surface's mm/px at 4K
(3.89→7.8, 3.31→6.6, 2.73→5.5, 1.31→2.6), and 2 × the delivery ramp's 1.19 mm/px
is **2.38 mm**, which *is* the "below ≈ 2.4 mm, material only" line — reached
from the pixel law rather than asserted. The census of what this catches across
the repo is **R2-1224**.

---

## Pre-existing findings surfaced by this audit, not owned by it

- **`car_anim_car.json` is stale past world t = 72.58** (beat 6, frames 2714+),
  disagreeing with current `carpath.py` by up to **678 m** — it predates
  R2-943's lap-down. Outside this block's span, but it should be rebuilt.
- **`docs/screen_presence.json` is void** — it was measured against a camera
  path that `docs/LIVE-CAMERA.md` itself declares stale. The live path is
  `render/film17_path.json`. Anything that read screen presence for beat 1
  should be re-run.
- **EVERY `detail=6` / `detail=8` NOISE IN THE REPO IS EMITTING OCTAVES BELOW
  THE RESOLVABLE FLOOR.** `ShaderNodeTexNoise` at `Detail = d` emits d+1 octaves
  at λ, λ/2 … λ/2^d. A 120 mm noise at the house default `detail=6` is *also*
  emitting **1.88 mm and 0.94 mm** octaves — below the 12 mm floor and below the
  2.4 mm "material only" line on every surface in this document's own table.
  They cannot reach the image at any resolution this film is graded at, **and
  they are most of the cost**: with house defaults one 4K frame of the concrete
  arm did not finish in ten minutes. This generalises far past this block and
  past the circuit's "nine layers below the band" count, because each of those
  layers was cascading further below it. `tyre_deposit.detail_for(λ)` derives
  the octave count instead; it should be lifted somewhere shared.
- **`work/r2_1211_rubber_tracks.json` contradicts itself.**
  `launch_mark_profile.RL.deposit_norm`'s last sample is 0.00000 while
  `launch_mark.RL.decay_note` says the mark terminates at 2.7 % of peak with a
  hard trailing edge, and `terminal_deposit_norm` is 0.02671. The 256-point
  resample fades the last 12.3 mm to zero — **anyone consuming the resample
  silently loses the feature this document calls distinguishing.** Consume the
  per-frame arrays instead, as `tyre_deposit.py` does. The resample should be
  regenerated.
- `FloorPolished`'s single relief stage is **m = 0.005 at a 7.41 m wavelength**,
  70× below `isotropic_macro`. The floor has, for practical purposes, no relief.
- `M_Surf_Concrete`'s two bump stages report **m = 3.15 and 3.29, both HIGH**
  against `isotropic_macro`, and no swing probe has been run on that material
  the way `tools/r2366_swing.py` was run on the paving family.
- `PAVING_RELIEF`'s 8th tuple element (`m_target`) is unpacked as `_m` in
  `_paving_relief` and **never read** — retune a `scale` or `relief_mul` and the
  amplitude will not follow.
- **R2-082 has no defect-log entry and no post-levelling measurement on disk.**
- `world/items/forecourt_paving_bay.py` and `paddock_paving_bay.py` are
  `OWNERSHIP_STUB`s (R2-331); the class owner is `build_architecture.py`.
- Sibling paving objects `ARCH_Paving_Paddock` / `PitLane` / `Garages` carry
  `M_C2W` — a **40° Z rotation** — so their Object space is not world space. The
  apron, forecourt and floor are all identity and are safe. Do not extend a
  world-locked mark to the rotated three without re-basing.
- `work/bisect.py` shadows the stdlib `bisect` for anything run with `work/` on
  `sys.path`; it breaks `PIL`. Run tooling from outside `work/`.
- `/home/zany/f1-round2/watch/seq1/` symlinks are **off by one**
  (`f000860.png -> r2full_000861.png`). Measure against
  `/home/zany/vast-render/out2/seq/r2full/`.

## Verified clean

`FloorPolished`, `M_Surf_Concrete`, `A_ConcApron`, `A_ForecourtSlab`:
`ShaderNodeTexImage` count **0**, every field procedural, no `images.load`, no
external asset of any kind. All four feed the Principled BSDF **by name**;
`Normal` resolves to index 6 in all four, verified live — no R2-057-family
finding. Whoever adds the mark must keep feeding by name (`_feed_named`,
`world/build_dressing.py:1255-1285`) and must use `6`/`7` for `ShaderNodeMix`
A/B.

## Artefacts

- `work/r2_1211_rubber_tracks.json` — derived contact-patch tracks, deposit
  profiles, surface hand-off, existing-paint cross-check
- `work/r2_1211_band.json` — per-key ground resolvability, all 433 keys
- `work/r2_1211_band.py` — the resolvability measurement

---

# R2-1219 — `world/items/tyre_deposit.py`, built and gated standalone

*(Renumbered from "APPENDED R2-1216" by the block owner: R2-1216 was already
taken by the deck-exposure finding above. Content unaltered.)*

> ⚠ **PARTIALLY RETRACTED BY R2-1220, AND THEN PARTLY RESTORED — read this
> before using any number below.** The gate scenes were photographing the
> **default Cube**, which `--factory-startup` puts at the world origin and which
> `itemkit.purge` is correctly unable to remove.
>
> * **CONCRETE (the apron): RE-MEASURED ON A CLEAN SCENE AND CONFIRMED.** The
>   derived single pass came back at **+1.575 %** against the contaminated
>   **+1.664 %** — a difference of **0.09 pp**. The Cube sat 40 m from that
>   scene's centre and outside its mask. **These conclusions survived by luck of
>   station, not by design**, and that is exactly why they were re-run rather
>   than argued for. The concrete table and everything R2-1222 gates on are live.
> * **DECK and FLOOR: still retracted**, still re-rendering. The deck scene is
>   centred on (0, 0, 0.340) — on the Cube. Its figures were a photograph of it.
> * **Field-probe numbers — density, coverage, the time gate — were never
>   affected** and stand throughout.
>
> The corrections in "FIVE THINGS IN THIS DOCUMENT THAT ARE WRONG" all stand:
> four are arithmetic or source-code facts, and the fifth (the existing paint's
> −18.79 %) is a concrete measurement and is among those re-confirmed. R2-1221
> is the independent in-film A/B at the real camera, unaffected by the Cube.

Written by the module's author. **Nothing here is wired into the film.** Four
shader node groups and three replica materials live in
`world/items/tyre_deposit.py` / `.md`; no existing world module was edited.

    selftest   python3 world/items/tyre_deposit.py --selftest      25 checks, 0 failures
    time gate  blender -b --factory-startup -P world/items/tyre_deposit.py -- --bindtest
    gate       blender -b --factory-startup -P world/items/tyre_deposit.py -- --gate

## What was built

`TDP_DepositField` (world position + `Front X` + `Traffic Passes` -> Density,
Coverage, Wetting, Grain, Launch, Film), and `TDP_Apply_Concrete`,
`TDP_Apply_BrushedMetal`, `TDP_Apply_PolishedFloor`. The delivery ramp was
dropped: `PLACEMENT.json` has it `HOLD` / `GATE_NOT_ACCEPTED` and the derived
deposit there is 0.0.

## FIVE THINGS IN THIS DOCUMENT THAT ARE WRONG

**1. The areal ratio is 1/460, not 1/140.** Launch 3.290344 m over
0.2416 x 0.2511 m = **54.237 m/m² mean, 122.534 m/m² peak**; film 1.0 m over
33.7894 x 0.2511 m = **0.11786 m/m²**. That is **1/460.2** of the mean and
**1/1039.6** of the peak. §R2-1215's 1/140 is 34/0.2416 — the *length* dilution
with its own "about 30 % of the launch's 3.29 m" factor dropped. The two
sentences disagree by 3.3x.

**2. `work/r2_1211_rubber_tracks.json` contradicts itself.**
`launch_mark_profile.RL.deposit_norm`'s last sample is **0.00000**, while
`launch_mark.RL.decay_note` says the mark "terminates at 2.7 % of peak ... a
hard trailing edge, not a fade" and `terminal_deposit_norm` is **0.02671**. The
256-point resample fades the last **12.3 mm** to zero. Anyone consuming that
resample silently loses the feature this document calls the distinguishing one.
`tyre_deposit.py` uses the **per-frame arrays** instead, whose decade reproduces
§R2-1211's exactly.

**3. The derived tractive film is FLAT — the existing paint's falloff is the
wrong shape, not merely too weak.** Over x = 15..49, `accel_long_ms2` is
10.659..10.699 and `mu_used` = `a_x`/(2·`normal_load_norm`·g) is
1.6968..1.7023. Calibrating `kappa = mu_used * 0.0174017` to the brief's 1 m
gives **kappa = 0.02953..0.02962, a variation of 0.304 % across the whole
span** — the exact span over which `build_surface.py:2836` ramps linearly from
1.0 to 0.0. The 2.95 % slip lands inside §R2-1215's own 2–8 % band, and the
implied C_kappa/Fz is 57.5 against the car's *weight*, i.e. **28.7** once the
~2x aerodynamic rear load at 16–31 m/s is allowed — the top of the 15–30 range
for a slick. The derivation closes.

**4. THE OCTAVE LAW WAS BEING BROKEN BY THE FRACTALS, NOT ONLY BY THE
AMPLITUDES.** `ShaderNodeTexNoise` with `Detail = d` emits d+1 octaves at
lam, lam/2 ... lam/2^d. A 120 mm noise at the house default `detail=6` is *also*
emitting **1.88 mm** and **0.94 mm** octaves — below the 12 mm floor and below
the 2.4 mm "material only" line on every surface in §THE OCTAVE PRESCRIPTION's
own table. They cannot reach the image at any resolution this film is graded
at, and they are not free: with the house defaults one 4K frame of the concrete
arm did not finish in ten minutes on this box. `tyre_deposit.detail_for(lam)`
derives the octave count and holds the finest octave at or above the floor;
measured finest octave over all 12 textures in the module is **12.00 mm**. This
is not specific to this block — it applies to every `detail=6`/`detail=8` noise
in the repo.

**5. "The apron mark is 2–3x too weak" does not survive a matched A/B.** See
the table below. Reproduced on an identical substrate under an identical camera
and sun, `build_surface`'s launch paint measures **-18.79 %**, not -5.73 %.
§R2-1213's number is a *deviation from the local lighting trend* along a lateral
sweep, and a 640 mm-wide feathered streak is partly absorbed into the trend it
is being measured against. **The existing paint is not weak. It is strong, and
it is in the wrong place, at the wrong lateral offset, with a falloff the
telemetry contradicts, and with no edge.**

## The measured numbers

### The octave table — every relief stage this module authors

`K.relief_budget`, amplitudes from `K.relief_amplitude_for(m, lam)`; not one
typed millimetre (`selftest [4]` parses this file with `ast` and fails on any
`.bump(distance=)`).

| stage | lam | amp | slope | m pp | band | verdict |
|---|---:|---:|---:|---:|---|---|
| concrete/dep_fill_fine | 22.00 mm | 0.2324 mm | 1.90 deg | 0.300 | isotropic_micro | ok |
| concrete/dep_fill_coarse | 95.00 mm | 1.8425 mm | 3.49 deg | 0.550 | isotropic_macro | ok |
| concrete/dep_shoulder | 251.00 mm | 3.5374 mm | 2.54 deg | 0.400 | isotropic_macro | ok |
| deck/dep_film_micro | 16.00 mm | 0.0789 mm | 0.89 deg | 0.140 | isotropic_micro | ok |
| deck/dep_film_mottle | 130.00 mm | 0.7322 mm | 1.01 deg | 0.160 | isotropic_micro | ok |
| floor/dep_smear_fine | 14.00 mm | 0.0641 mm | 0.82 deg | 0.130 | isotropic_micro | ok |
| floor/dep_smear_broad | 115.00 mm | 0.4858 mm | 0.76 deg | 0.120 | isotropic_micro | ok |

All 7 inside 12–300 mm (14.0 – 251.0 mm) and all inside their named
`K.RELIEF_BANDS` band. Field *structure* wavelengths: patch_rib 83.7 mm,
graining 18.6 mm, scuff_fine 42.0 mm, scuff_coarse 120.0 mm, edges 12 mm.
Finest fractal octave emitted anywhere in the module: **12.00 mm**.

Substrate stages MODULATED but not authored, measured off
`build_surface.py:2887-2888`'s own strength/distance pairs — they reproduce this
document's reported m = 3.15 / 3.29 to three digits:

| substrate stage | lam | amp | m | reduced by up to |
|---|---:|---:|---:|---:|
| `M_Surf_Concrete` micro | 2.29 mm | 0.270 mm | 3.141 | 55 % |
| `M_Surf_Concrete` aggregate | 24.11 mm | 3.000 mm | 3.292 | 90 % |

### The field, measured through a 12-degree-yawed object

Ortho top-down over an exact world window, 0.78 mm/px, on a plane carrying
`Turntable_Deck`'s real 12 deg yaw, so world-locking is exercised and not
assumed.

| | measured | declared |
|---|---|---|
| mark, world x | −1.80706 … −1.55134 | −1.80000 … −1.55840 (+ the 11–15 mm hard edges) |
| length | 0.2557 m | 0.2416 m + two half-edges |
| RL patch centre, world y | **+0.79987** | +0.79750 + its own 2.2 mm jitter = +0.79970 |
| RR patch centre, world y | **−0.79674** | −0.79750 + its own 0.8 mm jitter = −0.79670 |
| patch width | 265.7 / 264.1 mm | 251.1 mm + edge |

Both to better than 0.4 mm, which is half a probe pixel.

**Per-instance variation, measured not claimed:** peak density differs by
**6.40 %** between the two launch patches, mean by **10.74 %**, width by
**1.56 mm**, lateral centres by +2.37 mm and +0.76 mm. Closest pair of noise
origins across the four instances: **9.85 m**, so no two ever sample the same
noise.

**The time gate:** `Front X` before frame 818 -> max density **0.0**, lit pixels
**0**. Mid-wipe -> 102 679 px. Fully laid -> 221 596 px.
`--bindtest` reads the animated socket back at frames 816/818/822/827/1064 as
−1.81200 / −1.79280 / −1.68860 / −1.55840 / +62.03892, each to better than
5e-07, on a 248-key LINEAR/CONSTANT F-curve.

### ROUGH CONCRETE — the apron, priority one, 4K pixel law

4K resolution, 2.71 mm/px (this document's own apron-near p50 is 2.73), traced
region 1689 x 1684 px of 3840 x 2160, 30 deg grazing, contract sun, AgX. Every
arm shares one camera, one sun and one seed, so the ratio arm/control cancels
the lighting exactly. Measured on the deposit's own footprint, 340 485 px.
`existing` is `build_surface.py:2835-2841 + :2884` reproduced WITHOUT its stain
multiplier, i.e. about 40 % stronger than what ships — a deliberately generous
baseline.

| arm | mean | p05 | p50 | p95 | band-vs-shoulder | p99.5 lateral gradient |
|---|---:|---:|---:|---:|---:|---:|
| derived film, N = 1 | **+1.66 %** | −7.03 % | −0.03 % | +14.41 % | +1.70 % | **1.067 %/mm** |
| derived film, N = 60 | **−4.21 %** | −20.39 % | −7.35 % | +17.97 % | −4.13 % | **1.605 %/mm** |
| `build_surface`'s existing paint | **−18.79 %** | −25.54 % | −18.73 % | −11.92 % | −17.49 % | **0.243 %/mm** |

| channel | control | deposit | delta | existing |
|---|---:|---:|---:|---:|
| Roughness | 0.8002 | 0.6664 | **−16.7 %** | −0.0773 |
| Specular IOR Level | 0.3200 | 0.4206 | **+31.4 %** | **+0.0000** |
| Height Coarse, sd (24.11 mm aggregate) | 0.18572 | 0.15757 | **−15.2 %** (−28.2 % at N=60) | **0.0 %** |

Pure black on the delivered 8-bit AgX frame, exposure solved so the CONTROL arm
sits at its measured operating point (−4.123 EV, control mean 0.3845 against a
0.38 target): **0.0000 % on all four arms.**

**READ THE LAST COLUMN OF THE FIRST TABLE, NOT THE FIRST.** In mean tone this
module's derived deposit is WEAKER than the paint it would replace. In *edge*
it is **4.4x** stronger at N = 1 and **6.6x** at N = 60. That is the answer to
"not noticeable enough": the existing mark is a 640 mm-wide feathered wash with
a 0.24 %/mm edge sitting on a surface whose own bay-tone hash swings +-14.5 %,
so it reads as mottle at any amplitude. What makes a tyre mark read is its edge
and its structure in the 12-300 mm band, and the existing paint has neither —
its only spatial scales are a 200 mm core, a 320 mm feather and a 34 m ramp.

**AND THE UNWELCOME PART.** The physically derived single pass is
**+1.66 %** — it does not read, and it is not even a darkening. That is not a
bug: 3 % tractive slip over 34 m transfers about **10.6 nm** of rubber, which
changes no surface's albedo at all (coverage 0.34 %). Its whole effect is in
gloss, and a glossier surface under a bright sky at 30 deg gets slightly
BRIGHTER. **No pigment on that apron is derivable from this car's single pass.**
`Traffic Passes` is where that decision belongs; it has a unit, it defaults to
1, and N = 60 is what it costs to reach the numbers above.

### BRUSHED METAL and POLISHED FLOOR

Both arms are on the render queue at the time of writing: the deck's field probe
hit a genuine bug in this module — `TurntableTop`'s base colour was returned as a
literal 3-tuple, which every Color sink accepted and the probe's Float sink
rejected (`NodeSocketFloat.default_value expected a float type, not tuple`) —
and the fix (an `ShaderNodeRGB` node, so every channel this file passes around
is a link) forced a re-run of those two substrates. `--subs deck,floor` exists
for exactly that. Their numbers will be appended here.

What is already settled for them, from the field probe and the design:

* The deck patch is **time-gated** and measured empty before frame 818, so the
  beat-1 exposure that a static mark would have created cannot occur.
* The floor application contains **no colour to mix toward** — R2-1214's trap is
  designed out rather than remembered. Its only albedo term is
  `base * (1 - 0.10 * coverage)`, monotonically non-brightening for every
  possible base colour.
* The coat suppression is **capped at 62 %** and coat roughness RISES 0.045 ->
  0.30, so the specular return that holds those pixels off zero is spread rather
  than removed. On concrete, pure black measured **0.0000 %** on every arm.

### Law 1

`ShaderNodeTexImage` count across every `TDP_*` node group and material: **0**.
`K.assert_no_external_assets()` -> `{'external_image_files': 0,
'image_texture_nodes': 0}`.

### Cost, measured, because it is not free

At the 4K pixel law on the traced region, one arm of the concrete substrate
alone renders in **2 min 00 s**; the same substrate carrying the deposit field
takes **12 min 05 s** — **6.0x**. Four instances x (a rib wave + a graining wave
+ two scuff noises) is inherent to "no repeated assets", and a shader has no
branch to skip an instance whose lateral band is zero. On a GPU this is
irrelevant; it is recorded because this box has six cores and no usable GPU
today.

## What this block should do next

1. **The apron is a decision, not a derivation.** Ship the derived field at
   N = 1 and the apron reads as a satin band, not a mark. Pick a
   `Traffic Passes` and the numbers above say what it buys. Either way the
   mark moves to |y| = 0.79750, widens to 251.1 mm, loses the 34 m ramp the
   telemetry contradicts, and gains an edge.
2. **`work/r2_1211_rubber_tracks.json` should be regenerated** so
   `launch_mark_profile` stops contradicting `decay_note`.
3. **`detail_for` belongs in `itemkit`, not in one item module.** Every
   `detail=6`/`detail=8` noise in the repo is paying for octaves that cannot
   reach the image.

> **To finish the deck and floor rows:**
> `blender -b --factory-startup -P world/items/tyre_deposit.py -- --gate --samples 20 --subs deck,floor --no-field-probe`
> writes `render/items/tyre_deposit/gate_deck_floor.json`. It was running at the
> time of writing. A first attempt produced garbage and the gate is why we know:
> the deck plane does not fill its 4.9 m / 35 mm frame, the contract sky sat
> behind it, and the probe's mask selected **69 %** of the frame while reporting
> a "Roughness" of **11.25**. The 40 x 20 m concrete plane filled its own frame
> and hid that completely. Probes now render with `scene.world = None`.

---

# R2-1222 — HANDOVER: wiring `tyre_deposit` into `build_surface._mat_concrete`

**`world/build_surface.py` has another owner and was not edited by this block.**
This is the change described precisely enough to apply without a merge conflict.
Everything below has already been built and measured in
`tyre_deposit.mat_concrete()`, which is a faithful replica of `_mat_concrete`'s
substrate — that function is the reference wiring, not prose.

### Where

`world/build_surface.py`, function **`_mat_concrete()` (line 2756)**. Three
edits, all inside it.

### 1. Delete the existing launch paint — five lines

Remove the block at **2836–2841**, comment included:

```python
# the car has been down here exactly once, so the rubber is a single pair of
# streaks either side of the launch axis, not a rubbered-in line
launch = g.mr(g.math("ABSOLUTE", g.math("SUBTRACT", g.math("ABSOLUTE", u), 0.72)),
              0.10, 0.32, 1.0, 0.0)
launch = g.math("MULTIPLY", launch, g.mr(t, 0.0, 34.0, 1.0, 0.0))
launch = g.math("MULTIPLY", launch, g.mr(stain, 0.3, 0.8, 0.4, 1.0))
base = g.mixc(g.math("MULTIPLY", launch, 0.55), base, g.rgb(0.0420, 0.0390, 0.0380))
```

and the roughness line at **2884** that consumes it:

```python
rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", launch, 0.18))
```

`launch` has no other consumer in the function — confirm with a grep before
deleting, and note it is **absent from the height chain**, which is R2-1213's
missing-relief finding.

### 2. Insert the field and the apply group — after the height chain is built, before the bumps

`_mat_concrete` currently ends by building `h`, then two bumps, then the BSDF.
The deposit group must sit **between the height chain and the bumps**, because
it modifies both heights *and* supplies the base normal the substrate's own
bumps then chain onto.

Insert immediately after `h = g.math("ADD", h, g.math("MULTIPLY", mark, 0.30))`
and **before** `nrm = g.bump(micro, ...)`:

**`_mat_concrete` uses `build_surface`'s own `_G` kit, which is NOT itemkit's
`NT`.** `_G` has `.n()` and `.set()`; it has no `.pin_named()` and no
`.object_coords()`. So **`TDP.field_node()`, `TDP.world_position()` and
`TDP.mat_concrete()` cannot be called from here** — they need an `NT`. Only
`TDP.build_groups()`, `TDP.front_x_value_node()` and `TDP.bind_time()` are
kit-independent. Instantiate the groups by hand:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "items"))
import tyre_deposit as TDP

TDP.build_groups()                       # idempotent; builds the four groups

# World position, built with _G. DO NOT reuse this function's existing `P`:
# that is TexCoord->Object, and the deposit field is authored in WORLD metres
# against the car's derived track. They coincide today only because
# `_build_access` writes world-coordinate vertices into an untransformed
# object -- a build coincidence, not a guarantee.
_oc = g.n("ShaderNodeTexCoord").outputs["Object"]
_vt = g.n("ShaderNodeVectorTransform", vector_type="POINT",
          convert_from="OBJECT", convert_to="WORLD")
g.set(_vt.inputs["Vector"], _oc)
Pw = _vt.outputs["Vector"]

# The field.
fld = g.n("ShaderNodeGroup", node_tree=bpy.data.node_groups[TDP.FIELD_GROUP])
g.set(fld.inputs["World Position"], Pw)
g.set(fld.inputs["Traffic Passes"], 60.0)          # art decision -- see below
frontx = TDP.front_x_value_node(g)                 # _G-compatible
g.set(fld.inputs["Front X"], frontx.outputs[0])

# The concrete application.
dep = g.n("ShaderNodeGroup", node_tree=bpy.data.node_groups[TDP.CONC_GROUP])
for _nm, _src in (("Base Color", base), ("Roughness", rough),
                  ("Specular IOR Level", 0.32),
                  ("Height Micro", micro), ("Height Coarse", h),
                  ("Coverage", fld.outputs["Coverage"]),
                  ("Wetting", fld.outputs["Wetting"]),
                  ("Grain", fld.outputs["Grain"]),
                  ("World Position", Pw)):
    g.set(dep.inputs[_nm], _src)
base  = dep.outputs["Base Color"]
rough = dep.outputs["Roughness"]
spec  = dep.outputs["Specular IOR Level"]
micro = dep.outputs["Height Micro"]
h     = dep.outputs["Height Coarse"]
nrm   = dep.outputs["Normal"]
```

`_G.set(sock, v)` links when `v` is an output socket and assigns
`default_value` otherwise, so the mixed tuple above is safe as written.

### 3. Chain the substrate's bumps onto the group's normal, and feed Specular

Change the two existing bump calls to pass the group's normal as the base, and
feed the BSDF's Specular from the group instead of the literal `0.32`:

```python
nrm = g.bump(micro, strength=0.45, distance=0.0006, normal=nrm)   # was normal=None
nrm = g.bump(h,     strength=1.0,  distance=0.0030, normal=nrm)   # unchanged
...
g.set(bsdf.inputs["Specular IOR Level"], spec)                    # was 0.32
```

**Order is not negotiable**: field → apply group → substrate bumps → BSDF. The
group reduces both substrate height stages (rubber *fills* texture) and the
reduction has to land before the bumps read them.

### The time binding — the part that is easy to miss

The field masks **both** terms — the launch mark *and* the tractive film — by
**`Front X`**, a Value node keyed from the wheel's own per-frame world x: 248
keys, frames 817→1064, x −1.79280→62.039, LINEAR/CONSTANT. **Without the binding
the deposit exists on frame 1.** Bind the node created in step 2, once the
material has a user in the scene:

```python
TDP.bind_time(frontx)          # the node from step 2
```

> **IT FAILS SILENTLY IF THE MATERIAL HAS NO USER IN THE SCENE.** An animated
> shader node tree is only evaluated by the depsgraph if something in the scene
> uses the material. With no user, `frame_set` leaves every frame at the static
> default and the mark simply looks un-animated — no error, no warning.
> Measured both ways: with a user, frames 816/818/822/827/1064 read back
> −1.81200 / −1.79280 / −1.68860 / −1.55840 / +62.03892, each to better than
> 5e-07; **without one, all five read +63.60000.** So bind *after* the apron
> object exists and carries the material, and assert one non-default frame.

After binding, `Front X` is left at `FULLY_LAID_X` (`FILM_X_END + 0.10`) so a
static evaluation shows the finished state with neither edge of the wipe inside
the region being measured. `--bindtest` measures this
directly: **max density 0.0 and 0 lit pixels before frame 818.**

### `Traffic Passes` — an art decision, correctly labelled

**`passes=60.0`.** The coordinator decided it and it is not derivable: one launch
pass transfers ≈ 10.6 nm of rubber over 0.34 % coverage, changes no albedo, and
measures **+0.71 % with a p50 of −0.91 %** — it straddles zero. The film opens
on a working pit lane, so a used apron is the honest subject. **Do not re-derive
this number and do not present it as physics.** It is exposed as a group input
precisely so it stays visible as a choice.

> ### ⚠ `Traffic Passes` IS PER-SURFACE. **NEVER SET IT GLOBALLY.**
>
> **The apron is the only surface where N is an open question. The deck and the
> floor are N = 1 by construction** — a showroom display turntable has not been
> driven over sixty times.
>
> Measured, on the deck, at N = 60: the film reaches **636 nm**, which is thick
> against the 110 nm quarter-wave interface scale, so it legitimately destroys
> the turntable's *metallic* character and produces an **+84.19 % bright band
> across the deck** — on a surface that is **23.9 % of the frame**. The physics
> is right; applying it there is not.
>
> **A single global knob would have striped the turntable while fixing the
> apron**, and it would have shipped: only the deck arm of the gate makes it
> visible, and the deck arm is the one that had to be re-run twice (R2-1220,
> R2-1221) before it produced a trustworthy number at all.
>
> The launch mark needs no multiplier anywhere: at **11.0 µm** it is already
> 97 % coverage — optically thick on its own — and measures **+23.18 %** on the
> deck at N = 1.
>
> **And N pushes on the black-level gate.** Above N ≈ 60 the Fresnel term is
> saturated, so every further pass is *pure albedo*. The deposit already
> **lowers** concrete's darkest in-footprint pixel (0.22335 → 0.21804). Pure
> black is 0.0000 % today; **any raise of N must re-measure it.**

### What the gate must read afterwards

Re-run `world/items/tyre_deposit.py --selftest` (25 checks, 0 failures) and
`--gate`, then on the rebuilt film material confirm, against the values in
R2-1219:

> **These were briefly retracted by R2-1220 and are now restored.** The concrete
> substrate was re-measured on a scene proven clean and came back within
> **0.09 pp** of the contaminated run, because the default Cube sat 40 m off that
> scene's centre and outside its mask. **This table is the concrete/apron gate
> and it is live.** (The deck and floor tables in R2-1219 remain retracted and
> are still re-rendering — they do not affect this handover, which only touches
> `_mat_concrete`.)

| quantity | must read | status |
|---|---|---|
| **pure black** | **0.0000 % on every arm** | live |
| darkest in-mask pixel | ~~rises~~ **FALLS**, 0.22335 → 0.21804 | **corrected, R2-1230** |
| `ShaderNodeTexImage` count | **0** | live |
| finest emitted octave | **≥ 12.00 mm** | live |
| density before frame 818 | **0 lit px** (`--bindtest`) | live |
| `--selftest` | 25 checks, 0 failures | live |
| `tools/r2_1222_verify_handover.py` | `>> STAGE RESULT: OK (0 failures)` | live |
| lateral gradient p99.5, N=60 | ~~≈ 1.605 %/mm~~ — **in-film: 0.319 vs the paint's 0.324** | **REFUTED, R2-1225** |
| mean tone, N=60 | ≈ −4.21 % (N=1: +1.575 %) | re-confirmed |
| Roughness | 0.8002 → 0.6664 (−16.7 %) | re-confirmed |
| **Specular IOR Level** | **+3.6 %** (was a spurious +31.4 %; existing: **+0.0000**) | re-measured |
| Height Coarse sd | −15.2 % at N=1, −28.2 % at N=60 (existing: 0.0 %) | re-confirmed |

> **CORRECTED — this originally claimed the black-level result runs the helpful
> way.** It does not. Under the three-scale model the deposit **lowers** the
> darkest in-footprint pixel, 0.22335 → 0.21804, rather than raising it: with
> the specular gain cut from a spurious +31.4 % to **+3.6 %**, the albedo dim is
> no longer offset. **Pure black is still 0.0000 % on all four arms**, so the
> R2-082 constraint is survived — but it is survived with less margin than
> claimed, and it is now moved *toward* rather than away from. Anyone raising
> `Traffic Passes` is raising the albedo dim and must re-check it.

**The claim being gated is the edge, not the amplitude.** The existing paint is
*stronger* in mean tone (−18.79 %) and still does not read, because a 640 mm
feathered wash at 0.243 %/mm is mottle on a surface whose bay hash swings
± 14.5 %. R2-1221 tests that claim in the film.

### Two things not to "fix" on the way past

- **The `existing` baseline arm deliberately omits the `stain` multiplier**,
  which makes the baseline ≈ 40 % *stronger* than what `build_surface` actually
  renders. That is intentional: the author of the new thing scored it against a
  generous baseline. Leave it.
- The apron streaks move from |u| = 0.72 to **0.79750** and the core widens from
  200 mm to **251.1 mm**. Those are `HALF_TRACK_REAR` and the measured contact
  patch, not taste.

---

### The handover was executed, not just written

`tools/r2_1222_verify_handover.py` runs the snippet above **verbatim** against
`build_surface._G` in a throwaway material, without editing `build_surface.py`:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/r2_1222_verify_handover.py

**`>> STAGE RESULT: OK (0 failures)`** — 11 checks: both groups instantiate,
`World Position` links, `Front X` links from the Value node, `Traffic Passes`
reads 60.0000, the BSDF's Specular is *linked* rather than the old 0.32 literal,
the two substrate bumps chain onto the apply group's `Normal` in the right
order, the world position goes through a POINT OBJECT→WORLD transform, and no
image texture is introduced. Re-run it after applying the change; if it stops
returning OK, the wiring drifted.

*(The first run failed one check — `from_node is dep`. That was the test's
fault, not the wiring's: Blender returns a fresh RNA proxy per access, so
identity comparison on nodes is invalid. Compare `.name`.)*

---

# R2-1223 — the time-gating defect is a family, and this is how far it was checked

A defect found once in a family is worth testing for across the family. The
family here is: **world state that is a consequence of an event inside the shot,
authored as though it were always true.** It ships as a mark visible before the
thing that caused it.

Found **three times in this block**, and only one of them was predicted:

| surface | how it was found | status |
|---|---|---|
| dais deck | predicted, from camera coverage — a static patch would sit under a **parked car for ≈ 473 frames** of beat 1 | gated on `Front X` |
| concrete apron | **not predicted** — a field probe caught the tractive film at density 4.99e-04 on ground the car had not reached | gated |
| showroom floor | **not predicted** — same probe, same cause | gated |
| delivery ramp | n/a — `HOLD`, not in the film (R2-1217) | dropped |

**Checked: four surfaces. That is all.** The generalisation was not run, and it
is unowned:

- **The breach is the same test inverted.** The showroom is *supposed* to stay
  wounded after t = 36 — but nothing in this block verified it is **intact
  before** it. Glass, debris and the aperture live in `sim/` and
  `world/build_architecture.py`, both outside this block's remit.
- **The circuit's rubbered racing line** is narratively fine (many prior laps)
  but it is on screen for 1,922 frames and R2-651 already found it misplaced by
  a median 4.96 m. Nobody has asked whether anything *else* on that surface
  assumes an event that has not happened yet.
- **Marbles, dust, debris fields and the turntable's own rotation state** were
  not examined.
- **No systematic sweep** was run across the ~42 items in `PLACEMENT.json` for
  statically-authored event consequences. The probe that caught two of the three
  instances above was a field probe on the deposit field specifically; there is
  no general instrument for this, and building one would be cheap next to what
  it catches.

**Stated against this block's own interest:** two of the three instances were
found by an instrument nobody planned, not by the reasoning that predicted the
first. The reasoning generalised the *conclusion* and not the *method*, and
without that probe the fix would have shipped the very defect it was written to
avoid, on two more surfaces than the one it was watching.

---

# R2-1220 — THE MEASUREMENT SCENE WAS PHOTOGRAPHING THE DEFAULT CUBE

**Appended by the author of `world/items/tyre_deposit.py`. It retracts every
substrate number in R2-1219 above; the field-probe numbers there are unaffected
and stand.**

`--factory-startup` **is not an empty scene.** It contains a 2 m **Cube at the
world origin**, a point Light and a Camera. `itemkit.purge(prefix)` deliberately
removes only the calling item's datablocks — a purge that took anything else
would delete another module's sun, which is a documented way to get a black
acceptance render — so the Cube survives into every measurement scene an item
module builds.

**The turntable deck's measurement scene is centred on (0, 0, 0.340). That is
exactly where the Cube is.** Every deck figure in the first three gate runs is a
photograph of the default Cube lit by the default Light.

Measured, not inferred. A probe material emitting the constant **0.86** into its
green channel was rendered at the deck camera:

| | 99.7 % of frame non-zero | mean of green | max of green |
|---|---:|---:|---:|
| before | 99.7 % | **5.390** | 12.167 |
| after `_empty_the_scene()` | 100.0 % | **0.86000** | 0.86000 |

The corrupted deck columns read "Roughness 9.82" against a real 0.40, "Metallic
7.27" against a real 0.86, and a deposit mask covering **70.5 %** of the frame
where the tyre band covers about 12 %. The RGB signature of the bad renders is
7.04 / 5.38 / 2.80 — R > G > B, a warm sunlit surface, not a shader field.

**It hid for a whole substrate because of where the other two scenes sit.** The
concrete scene is centred at x = 32 and the floor at x = 10.5, so the Cube was
40 m and 10 m off-centre in those and its 2 m silhouette never dominated the
frame — but it was still inside the tyre band's own y range, so the concrete
numbers in R2-1219 are retracted as well and are being re-measured.

**This is not specific to this module.** Any item test scene whose subject is
near the world origin has the Cube in it, and `itemkit.emitted_wavelength_m`'s
docstring already records the same failure in prose — *"the default Cube once
sat between an ortho camera and a measurement plane and returned one identical
number for fourteen different stages"* — which means it has now happened at
least twice, and the second time the warning existed and was in the very file
being called. A remembered warning is not an instrument.

**The fix, and it is a refusal rather than a habit.**
`tyre_deposit._empty_the_scene()` deletes every object the module did not make,
and `build()` raises if anything whose name does not start with the item prefix
can reach the camera:

    strays = [o.name for o in scene.objects if not o.name.startswith(PFX)]
    if strays:
        raise RuntimeError("REFUSING: %s are in the measurement scene and this
        module did not make them. Everything the camera can see has to be this
        item or the numbers are about something else." % strays)

**Recommended for the class, not just for this item:** that refusal belongs in
`itemkit` next to `purge`, because `purge`'s docstring correctly explains why it
must NOT delete other datablocks and then leaves the caller with no way to get a
clean scene at all. The two functions are the two halves of one contract.

Re-measured substrate numbers will replace R2-1219's tables.



---

# R2-1224 — the octave census: every fractal `Detail` in the repo, measured

R2-1219 §4 found that `ShaderNodeTexNoise` at `Detail = d` emits **d+1** octaves
at λ, λ/2 … λ/2^d, so a 120 mm noise at the house default `detail=6` is also
emitting 1.88 mm and 0.94 mm — below the "material only, never pattern" line on
every surface in §THE OCTAVE PRESCRIPTION's table, unreachable at any resolution
this film is graded at, and most of the cost. That finding was made inside one
item module. This is the same question asked of the whole repo.

## What was lifted into `itemkit`

`world/items/tyre_deposit.detail_for` now lives in `world/itemkit.py` §5c, with
the relief law. Additive: no existing itemkit function changed.

    K.detail_for(wavelength_m, floor_mm=None, distance_m=None, lens_mm=None,
                 res_x=RES_X_4K, px=None, max_detail=8)   -> Detail, a float
    K.finest_octave_for(wavelength_m, detail, ...)        -> the audit direction

`detail_for` derives the count so the finest octave lands at or above the floor.
`finest_octave_for` is to it what `modulation_for_amplitude` is to
`relief_amplitude_for`, and it is the instrument this census ran on. The floor is
not a table and not a typed millimetre: `floor_mm` if stated, else the pixel law
at `distance_m`/`lens_mm` through `resolvable_mm(..., px=OCTAVE_FLOOR_PX)`, else
`K.OCTAVE_FLOOR_MM`. **`OCTAVE_FLOOR_PX = 2.0` is arithmetic already on this
page**: every per-surface band floor in R2-1211's table is exactly 2 × that
surface's own mm/px at 4K (3.89 → 7.8, 3.31 → 6.6, 2.73 → 5.5, 1.31 → 2.6).
`OCTAVE_FLOOR_MM = 2 × 1.19 = 2.38 mm`, 2 px at the delivery ramp's p50 — which
IS this document's "below ≈ 2.4 mm" line, reached from the pixel law instead of
typed.

`itemkit --selftest`: **25 checks, 0 failures** pure-python; **46 checks, 0
failures** under Blender 5.2. New checks: `detail_for_holds_the_finest_octave`,
`detail_for_is_tight_and_never_crosses_the_floor` (164 (λ, floor) pairs over
4 mm – 4 m × 4 floors: 0 crossings, 0 wasted octaves), and R2-1220's
`scene_purity_refuses_the_default_cube`. `tyre_deposit.py` was **not** changed —
it keeps its own `detail_for` with its own 12 mm band floor, and the duplication
is recorded here rather than removed.

## Method

Static AST scan of `world/`, `world/items/`, `anim/`, `tools/` for every
`ShaderNodeTexNoise` / `TexVoronoi` / `TexWave` and every wrapper that creates
one — 109 creation sites in 56 wrapper functions, reached from **1368 call
sites**. λ comes from `wavelength_m=` / `noise_scale_for` / `voronoi_scale_for` /
`wave_scale_for` / `humankit.tex_scale` where declared (**150** sites); otherwise
from the raw `Scale` × the statically resolved **vector gain** × the measured
`NOISE`/`VORONOI`/`WAVE_WAVELENGTH_FACTOR`. Sites whose coordinate chain does not
resolve (479) are **excluded from every number below**, because `_vector_gain`'s
own docstring records that guessing it was worth a factor of 110. Headline
population: **783 sites in 38 modules** with a trustworthy λ. Verdicts from
`K.finest_octave_for`.

Two floors, because the table has no single one. **2.38 mm** is the strict
"material only" line and UNDER-claims; **7.8 mm** is the coarsest per-surface 4K
floor (apron far) and is used where a site cannot be attributed to a surface. Two
verdicts, because they are two different defects: **tail-only** means λ is above
the floor and the *detail cascade* pushed the finest octave under it — that is
this finding; **λ-itself-below** means the whole texture is under the floor,
which is R2-058's shape, and is counted separately rather than folded in.

## The numbers

| | at 2.38 mm | at 7.8 mm |
|---|---:|---:|
| sites emitting an octave below the floor | **424 / 783 (54 %)** | **543 / 783 (69 %)** |
| — of which **tail-only** (this defect) | 330 (42 %) | 335 (43 %) |
| — of which λ itself is already below | 94 | 208 |
| modules with ≥ 1 offender | 32 / 38 (84 %) | 32 / 38 (84 %) |
| octaves emitted, total | 4093 | 4093 |
| **octaves that cannot reach the image** | **1503 (37 %)** | **2203 (54 %)** |

**IS IT "MOST OF THEM"? Two answers, and only one is yes.** By *sites emitting at
least one unreachable octave*: **yes** — 54 % at the strict floor, 69 % at the
permissive one, 84 % of modules. By *octaves*, which is the count that maps to
cost: **yes** — 2203 of 4093 emitted octaves, **54 %**, are below the 7.8 mm
floor. But by *this specific defect*, the detail cascade dragging an otherwise
legal texture under the floor: **42–43 %**, a large plurality and **not** a
majority. The remainder are textures whose λ was already below the floor before
`Detail` touched it. Both are real, they are not the same bug, and the census
does not merge them to reach a rounder number.

The median tail offender is `detail=6` on a 30–80 mm noise where `detail_for`
returns **2**. Of the 335 tail offenders **324 are `TexNoise`, 11 are `TexWave`,
and zero are `TexVoronoi`** — voronoi's `Detail` defaults to 0 and almost nothing
in this repo raises it.

## Per module

| module | sites | below 2.38 mm | below 7.8 mm | tail-only | finest octave | worst margin | octaves deletable |
|---|---:|---:|---:|---:|---:|---:|---:|
| `items/marshal_post_column.py` | 55 | 34 | 44 | 27 | 0.0403 mm | 193x | 188 |
| `items/timing_stand.py` | 48 | 28 | 35 | 21 | 0.0873 mm | 89x | 131 |
| `items/driver_figure.py` | 36 | 26 | 31 | 5 | 0.0022 mm | 3578x | 118 |
| `items/team_truck_trailer.py` | 42 | 26 | 31 | 18 | 0.0159 mm | 491x | 144 |
| `items/paddock_paving_bay.py` | 32 | 21 | 28 | 24 | 0.0417 mm | 187x | 113 |
| `items/gantry_truss.py` | 27 | 25 | 26 | 16 | 0.0126 mm | 620x | 124 |
| `humankit.py` | 29 | 21 | 25 | 15 | 0.0240 mm | 324x | 103 |
| `items/pont_girder.py` | 26 | 23 | 24 | 16 | 0.0041 mm | 1907x | 117 |
| `items/kerb_precast_unit.py` | 30 | 14 | 23 | 14 | 0.1008 mm | 77x | 74 |
| `build_dressing.py` | 33 | 20 | 22 | 18 | 0.0347 mm | 225x | 98 |
| `items/pit_wall_unit_itemkit.py` | 38 | 14 | 22 | 18 | 0.0379 mm | 206x | 68 |
| `items/catch_fence_post.py` | 21 | 21 | 21 | 8 | 0.0040 mm | 1947x | 147 |
| `items/mullion_intact.py` | 26 | 18 | 21 | 13 | 0.0556 mm | 140x | 82 |
| `items/pit_wall_unit.py` | 36 | 13 | 20 | 17 | 0.0379 mm | 206x | 63 |
| `items/pont_deck_slab.py` | 22 | 15 | 19 | 15 | 0.1190 mm | 66x | 69 |
| `items/grandstand_riser_unit.py` | 47 | 7 | 18 | 15 | 0.2604 mm | 30x | 38 |
| `items/crew_fireproof_overall.py` | 21 | 11 | 17 | 9 | 0.0278 mm | 281x | 64 |
| `items/showroom_ceiling.py` | 28 | 14 | 16 | 6 | 0.0625 mm | 125x | 62 |
| `tools/r2366_roof_build.py` | 21 | 3 | 10 | 10 | 1.3125 mm | 6x | 19 |
| `items/lighting_mast.py` | 18 | 6 | 10 | 6 | 0.0281 mm | 277x | 36 |
| `build_surface.py` | 40 | 7 | 9 | 4 | 0.2500 mm | 31x | 23 |
| `items/dais_delivery_ramp.py` | 11 | 8 | 9 | 8 | 0.0469 mm | 166x | 45 |
| `items/tyre_wall_tyre.py` | 10 | 8 | 9 | 1 | 0.0179 mm | 437x | 37 |
| `items/armco_w_beam.py` | 12 | 8 | 8 | 4 | 0.0357 mm | 218x | 49 |
| `items/gravel_bed_surface.py` | 8 | 6 | 8 | 5 | 0.0149 mm | 524x | 46 |
| `items/tree_italian_cypress.py` | 13 | 6 | 8 | 5 | 0.0137 mm | 570x | 38 |
| `itemkit.py` | 7 | 5 | 5 | 3 | 0.0312 mm | 250x | 28 |
| `items/heras_fence_panel.py` | 7 | 5 | 5 | 3 | 0.0200 mm | 389x | 28 |
| `items/tree_oak.py` | 8 | 3 | 5 | 4 | 0.0859 mm | 91x | 19 |
| `items/asphalt_wearing_course.py` | 6 | 3 | 4 | 2 | 0.0625 mm | 125x | 12 |
| `items/tree_scots_pine.py` | 8 | 2 | 4 | 4 | 1.2500 mm | 6x | 9 |
| `tools/cockpit_surface.py` | 3 | 2 | 3 | 1 | 0.2750 mm | 28x | 8 |
| `tools/winding_probe.py` | 2 | 0 | 2 | 0 | 3.7699 mm | 2x | 2 |
| `items/tyre_deposit.py` | 8 | 1 | 1 | 0 | 2.2900 mm | 3x | 1 |
| *(clean: `armco_post.py`, `crew_figure.py`, `human_bench.py`, `paddock_personnel_figure.py`)* | 4 | 0 | 0 | 0 | 16.95 mm | — | 0 |

## The twelve worst tail offenders by margin

| file | line | λ | detail | finest octave emitted | below 7.8 mm by | `detail_for` says |
|---|---:|---:|---:|---:|---:|---:|
| `humankit.py` | 7716 | 8.0 mm | 8 | **0.031 mm** | 250x | 0 |
| `itemkit.py` | 3662 | 8.0 mm | 8 | **0.031 mm** | 250x | 0 |
| `itemkit.py` | 3685 | 8.0 mm | 8 | **0.031 mm** | 250x | 0 |
| `items/team_truck_trailer.py` | 2803 | 8.3 mm | 8 | **0.033 mm** | 240x | 0 |
| `items/team_truck_trailer.py` | 3226 | 8.4 mm | 8 | **0.033 mm** | 237x | 0 |
| `build_dressing.py` | 1964 | 8.9 mm | 8 | **0.035 mm** | 225x | 0 |
| `items/armco_w_beam.py` | 2224 | 9.1 mm | 8 | **0.036 mm** | 218x | 0 |
| `items/catch_fence_post.py` | 3358 | 9.7 mm | 8 | **0.038 mm** | 206x | 0 |
| `items/pit_wall_unit.py` | 2064 | 9.7 mm | 8 | **0.038 mm** | 206x | 0 |
| `items/pit_wall_unit_itemkit.py` | 1765 | 9.7 mm | 8 | **0.038 mm** | 206x | 0 |
| `items/team_truck_trailer.py` | 3004 | 10.0 mm | 8 | **0.039 mm** | 200x | 0 |
| `humankit.py` | 7848 | 11.0 mm | 8 | **0.043 mm** | 182x | 0 |

The shape is always the same: `detail=8` on an 8–11 mm noise, so the house
default carries nine octaves down to 0.03 mm, ~250× below the floor.
`itemkit.py` appears in its own census — lines 3662/3685 are the selftest's own
control graphs, not shipped, but they do get rendered.

## What this does NOT claim

* 479 call sites were dropped for an unresolved coordinate chain and 106 for an
  unresolvable λ. The true totals are **higher** than the ones above, not lower.
* λ from a raw `Scale` is nominal — the measured house factors, not a render.
  `emitted_wavelength_m()` is the instrument that would settle any single site.
* No render was run and none is needed: this is the same arithmetic
  `finest_octave_for` does, on the graph as written.
* Cost is quoted from R2-1219's measurement (6.0× on one substrate, and one 4K
  frame that did not finish in ten minutes with house defaults). This census
  measures octaves, not seconds.

## Artefacts

`work/r2_1224_octave_census.json`, and the same content at the originally
announced path `work/r2_1220_octave_census.json` — all 1368 sites with file,
line, node type, λ and its provenance, detail and its provenance, finest emitted
octave, per-floor verdicts, deletable octave count, and what `detail_for` would
have returned.

### R2-1220 addendum — how much of R2-1219 the Cube actually cost

Re-measured with `_empty_the_scene()` in place, same camera, same sun, same
seed, same 340 485-px footprint:

| concrete, deposit vs control | before the fix | after the fix |
|---|---:|---:|
| mean | +1.664 % | **+1.575 %** |
| p05 | −7.029 % | −7.203 % |
| p50 | −0.034 % | −0.124 % |
| p95 | +14.413 % | +14.547 % |
| footprint | 11.96 % / 340 485 px | 11.96 % / 340 485 px |

**0.09 pp.** The Cube was 40 m from the concrete camera and its silhouette fell
almost entirely outside the tyre band, so **R2-1219's concrete conclusions
stand** — including the one that matters, that the physically derived single
pass is a *brightening* of about +1.6 % and reads as no mark at all. The deck is
the substrate the Cube destroyed, and the deck is where it was always going to
do the most damage, because the deck is the only one of the three whose scene is
centred on the world origin.

**The lesson is not "the numbers survived".** They survived by luck of station:
had the apron been at x = 0 this block would have shipped a conclusion drawn
from a photograph of a default primitive. That is why the fix is a refusal in
`build()` and not a line in a checklist.

### R2-1220 addendum 2 — the full concrete block, re-measured clean

All three arms, `_empty_the_scene()` in place, 340 485-px footprint, 2.71 mm/px,
30 deg grazing, identical camera/sun/seed:

| arm | mean | p05 | p50 | p95 | (was, with the Cube in frame) |
|---|---:|---:|---:|---:|---:|
| derived film, N = 1 | **+1.56 %** | −7.35 % | −0.19 % | +14.76 % | +1.66 % |
| derived film, N = 60 | **−4.33 %** | −20.87 % | −7.61 % | +18.71 % | −4.21 % |
| existing paint | **−18.82 %** | −25.69 % | −18.75 % | −11.93 % | −18.79 % |

| channel | control | deposit | delta | existing |
|---|---:|---:|---:|---:|
| Roughness | 0.8002 | 0.6664 | **−16.7 %** | −0.0773 |
| Specular IOR Level | 0.3200 | 0.4206 | **+31.4 %** | **+0.0000** |
| Height Coarse (mean) | 0.4995 | 0.4987 | −0.2 % | +0.0000 |

Pure black on the delivered 8-bit AgX frame at the solved exposure (−4.121 EV,
control mean 0.3845 against a 0.38 target): **0.0000 % on all four arms**, and
the deposit RAISES the darkest in-footprint pixel (0.22473 -> 0.22755 ->
0.23035).

**Every figure moved by less than 0.13 pp and no conclusion changed.**
R2-1219's concrete section is reinstated in full.

**One column in it is misleading and this is the correction.** `Height Coarse`
is reported as a MEAN and reads −0.2 %, which looks like "the deposit does
nothing to the relief". It is the wrong statistic: the deposit modulates that
field multiplicatively about its own midpoint, so the mean cannot move — what
"rubber fills the surface texture" means is that the AMPLITUDE falls. Measured
as a standard deviation over the same pixels:

| | control | deposit | traffic |
|---|---:|---:|---:|
| Height Coarse sd | 0.18572 | **0.15757 (−15.2 %)** | **0.13340 (−28.2 %)** |

The existing paint moves it by **0.0 %** — `launch` is not in its height chain
at all, exactly as R2-1213 states. A gate that reports a mean where the physics
is in the variance will report a null for a real effect, which is the same shape
of mistake as R2-1213's own trend-deviation estimator under-reading a broad
mark.

---

# R2-1221 — THE DECK IS THE BIGGEST LEVER, IT READS *LIGHTER*, AND MY FIRST MODEL OF IT WAS WRONG

Appended by the author of `world/items/tyre_deposit.py`. Two findings, one of
them against this module.

## 1. On this deck, rubber is a PALE mark, not a dark one

First clean measurement of `TurntableTop` (metallic 0.86, base linear 0.048,
roughness 0.335–0.455), 1.31 mm/px, 30 deg diagnostic grazing, deposit vs
control as a per-pixel ratio:

| region | px | mean | p05 | p95 |
|---|---:|---:|---:|---:|
| the two launch patches | 13 112 | **+23.2 %** | +14.4 % | +33.5 % |
| the whole deposit footprint | 540 784 | +52.2 % | +13.7 % | +98.1 % |

**The sign is the finding.** §R2-1214 calls the metallic -> dielectric
transition "the single best lever in this block" and it is right about the
magnitude — +23 % inside the mark against +1.6 % for the derived deposit on the
apron, a factor of **15** — but the transition makes the deck **brighter**, not
darker. A conductor at base 0.048 has no diffuse lobe at all; everything it
returns is a specular tinted to 4.8 %. Turning it dielectric ADDS a diffuse term
at roughly the same albedo on top of a Fresnel specular that still rises to 1.0
at grazing. On a surface this dark that is a large *relative* gain. A tyre scuff
on dark machined metal is a pale grey smear in life, and that is what this
measures.

Anyone budgeting this mark as a darkening — including anyone reading
§R2-1214's "kills the anisotropic brush sheen" as "goes dark" — has the sign
backwards.

## 2. AND THE +52 % IS THIS MODULE'S BUG, WHICH THE SAME MEASUREMENT CAUGHT

The launch patch is +23.2 %; the *film band* around it was +52.2 %. **A
tractive film cannot out-read a burnout.** The cause was a category error in
`tyre_deposit`'s own physics: `Metallic`, `Specular IOR Level` and `Coat Weight`
were all driven by the WETTING scale, which saturates at a monolayer (7.6 nm).
The tractive film is **10.6 nm**, so it was 75 % "wetted" and was therefore
turning brushed metal into a dielectric.

**A 10 nm transfer film does not stop a metal being a metal.** Those three
channels are properties of the FRESNEL INTERFACE, and a film only owns the
interface once it is thick against a quarter of a visible wavelength. There are
three physical lengths here, not two, and each channel belongs to exactly one:

| channel | scale | length | launch (11.0 um) | film (10.6 nm) |
|---|---|---:|---:|---:|
| Roughness, Coat Roughness | surface energy | **7.6 nm** | 1.0000 | 0.7523 |
| Metallic, Specular IOR Level, Coat Weight | Fresnel interface, 550/4 nm | **110 nm** | 1.0000 | **0.0918** |
| Base Colour | optical depth | **3.1 um** | 0.9716 | 0.0034 |

`TDP_DepositField` now emits `Interface` alongside `Coverage` and `Wetting`, and
`selftest [3]` is `THE THREE SATURATION LAWS`. Consequences, all in the
direction of less: the deck's tractive film stops being a bright stripe across
the turntable and the launch patch keeps its full transition; the apron's
Specular IOR Level moves 0.32 -> 0.339 instead of 0.32 -> 0.42, so the derived
single-pass film on concrete reads even less than the +1.56 % already reported;
and `FloorPolished`'s coat suppression essentially vanishes for a film-only
surface, which removes most of the crushed-black risk R2-1214 warns about rather
than merely capping it.

**Stated against this block's own interest:** the error was in the module's
headline argument — the one that reconciles a 1/460 areal ratio with both
components being visible — and it was invisible in every number the gate
produced until the deck was measured cleanly, which only happened because the
default Cube was removed (R2-1220). Two instruments, two bugs, and the second
was mine.

All substrate numbers are being re-measured under the three-scale model.

### R2-1221 addendum — answers to the two questions that do not need a render

*(Addressed to whoever revised R2-1214 and R2-1216 on the strength of the deck
sign. Message send failed — no reachable agent by that name — so it is here,
which is the channel that works.)*

#### 1. YES, the deck's +23.2 % survives the three-scale correction EXACTLY. R2-1216 stands.

Not approximately — identically, and it can be written down before the render
because the launch patch is **11.0 um** of transferred rubber, which saturates
every scale in the model:

| density | wetting | interface | coverage |
|---|---:|---:|---:|
| launch peak | 1.0000 | 1.0000 | 0.9715 |
| launch p50 of profile | 1.0000 | 1.0000 | 0.8353 |
| launch terminal 2.7 % | 1.0000 | 0.9313 | 0.0906 |
| tractive film | 0.7523 | **0.0919** | 0.0034 |

Metallic 0.86 through both models, grain factor 1.0:

| | old (wetting) | new (interface) | delta |
|---|---:|---:|---:|
| launch peak | 0.0516 | 0.0516 | **+0.0000** |
| terminal edge | 0.0516 | 0.1071 | +0.0555 |
| tractive film | 0.2518 | **0.7857** | +0.5339 |

The correction is a **no-op wherever the film is optically thick**, so inside the
mark it is bit-for-bit the same shader. What collapses is the FILM band — the
metal stays metal — which is exactly the +52.2 % artefact going away. The
argument gets *stronger*: the mark is now the only thing on the deck instead of
sitting inside a spurious bright stripe that outshone it 2:1. The only real
change in the mark is a slight softening of the last few mm of the trailing
edge, and that is correct: a 2.7 %-density tail IS thinner than a quarter wave.

#### 2. The floor prediction is probably WRONG, and this correction is why

The prediction — "rubber kills that coat and removes the return, therefore
darker" — was right about **the model as it stood** and is broken by the fix.

**No launch mark lands on the floor.** The mark is on the deck at x = -1.80; the
floor at x = 6.3..15 receives the tractive FILM and nothing else. So the floor's
driver is **10.6 nm**, which is precisely where the three scales disagree most.

| Coat Weight 0.45, film-only | result | suppression |
|---|---:|---:|
| old model (coat weight <- WETTING, 7.6 nm) | 0.2401 | **47 %** |
| new model (coat weight <- INTERFACE, 110 nm) | **0.4244** | **5.7 %** |

The rest, unchanged because they are genuine wetting effects:
Roughness 0.105 -> **0.3420**, Coat Roughness 0.045 -> **0.2368**,
Specular IOR Level 0.550 -> 0.5454 (now interface-driven, so nearly inert).

**The floor's deposit stops being "the coat removed" and becomes "the coat
broadened."** That is a different sign of mechanism, not a smaller magnitude of
the same one. A 0.045-roughness coat returns light in a narrow lobe; at a
12.47 deg sun and a 25 deg camera we sit well off it, so broadening to 0.24
moves return TOWARD the camera. **Predicted: brighter, like the deck** — same
deep mechanism, reached by spreading the specular rather than by adding a
diffuse lobe.

**For R2-082, which is the part that matters:** under the corrected physics the
coat is **94 % intact** on a film-only surface, so the crushed-black warning is
very likely moot rather than live — not because the cap is working, but because
nothing on that floor is thick enough to suppress a coat. **Do not relax the cap
on the strength of that.** The cap earns its place the moment an optically thick
mark lands on a coated dielectric, which this film does not and a launch patch
would.

None of this is written as fact until it is rendered. If it comes back darker,
the original reasoning wins and this section will say so.

#### A limit on what my floor number can settle

My floor arm is lit by the **contract sun**, not the showroom's 61-lamp interior
rig, which cannot be loaded here (the film blends OOM on an 11 GB box). The
exposure is solved so the CONTROL floor sits at the **0.10** mean R2-1214
measures on `render/showlight/p_a_f0828_e-3.628.png`, and both arms then share
it. That makes the **delta** trustworthy and the absolute black level a
stand-in. **A 0.0000 % pure-black result from this gate is evidence, not the
R2-082 gate** — that still has to be run on a real beat-1/2 frame, exactly as
R2-1214 already says.

#### Method note, since it cost a run here

`pkill -f <pattern>` matches the pattern against the **invoking shell's own
command line**, so a pattern naming the process you want to kill also names the
shell you are typing it in, and kills the caller. Resolve PIDs through
`ps -eo pid,args` and kill those.

---

# R2-1225 — the apron A/B, rendered IN THE FILM, and it does not go the way the module hoped

**This section was commissioned as R2-1221. By the time it had numbers to write,
R2-1221 had been taken by the deck finding above, so it is filed under the next
free number rather than as a second R2-1221 — the same collision the block owner
had to unpick once already when R2-1219 was renumbered out of R2-1216.**

*It imports no number from R2-1219. That table is retracted by R2-1220 and this
measurement is independent of it: different scene, different camera, different
instrument. Where the two disagree, this one is the one taken in the film.*

## What was rendered

One `rq exec` job on broker 1, **one blend, one process, one camera, one sun,
one seed**, with three link states of ONE material toggled between renders. The
scene-level things the render protocol cannot set — `view_transform`, `look` —
are therefore not "matched", they are the same object. Read back from the built
scene and printed: **AgX / look None / exposure −3.628 / 24.000 fps**, and the
blend already held −3.628 before it was set.

| arm | launch paint | `tyre_deposit` | what it is |
|---|---|---|---|
| **A** | on | off | the film as it stands (`build_surface.py:2835-2841`) |
| **C** | off | off | the substrate — **the control** |
| **B** | off | on, `Traffic Passes` = **60.0** | the module as a drop-in replacement |

`Traffic Passes` was **read back off the built material's socket, not assumed**:
`traffic_passes_readback = 60.0`, and it is re-read and reprinted on every one
of the three renders.

C is why A and B are comparable. `arm/C` per pixel cancels the lighting, the
camera and the sampling exactly, so "the existing paint's gradient" and "the
module's gradient" are two readings of one instrument rather than two arms
measured against each other.

**The existing paint is switched off, not deleted.** `build_surface.py` is held
by another agent and was not touched. The whole mark hangs off one MapRange —
`mr(|(|u|−0.72)|, 0.10, 0.32, 1.0, 0.0)` — identified by its four constants *and*
its input chain (`ABSOLUTE ← SUBTRACT 0.72`), asserted unique, and switched by
setting its To Min to 0. The graft is R2-1222's handover snippet applied to the
live material. Both were proved against `build_surface._mat_concrete()` in a
throwaway material **before any GPU was rented** (`work/r2_1221/dryrun.py`,
16 checks, 0 failures, including that `set_deposit(off)` restores the film's own
tree link-for-link, twice).

**R2-1220's lesson applied as a refusal, not a habit:** the job asserts the film
opened (5 000+ objects), that **no object named `Cube` exists**, that no `TDP_`
object arrived with the film, and it **raycasts the ground under the band** and
reports what it hit — `SURF_AccessRoad`, material `M_Surf_Concrete`, z = 0.000.
It is measuring the surface it claims to be measuring.

## Frame 981 — the only frame that was rendered, and why

3840 × 2160, `RENDER_BORDER` crop **1100 × 820 px at full 4K density**,
**1.649 mm/px** at the band (finer than R2-1218's apron p50 of 2.73), 128
samples, OIDN, the film's own DOF and motion blur untouched. The band sits
≈ 6.4 m from the camera against a 7.02 m focus, so **defocus is not the limiter**;
motion blur is along-track and does not smear an across-track profile.

A two-point timing calibration was run **on the box that would do the work**
rather than carried from R2-1218's card. It under-predicted badly — the two
probe areas were only 4 s apart, so the fit was dominated by the 33.5 s sync
term and it sized the crop for a 150 s render that actually cost **234 s (A),
233 s (C), 357 s (B)**. The deposit arm is **+53 %** on top of the substrate.
The cost governor then correctly refused to start frame 1030: **frames 1030,
973 and 965 were not rendered.**

### Lateral tone, both arms, measured the same way

Profiles are the mean over three lateral sweeps of `arm/C`, resampled to 1 mm
along world y (the pixel path of a straight world line on a plane is straight,
so interpolating between the 5 mm probe samples is exact to well under a pixel).
Gradient is |d/dy| after a 3 mm smooth; `p99.5` over |y| ≤ 1250 mm.

| | mean tone | p05 | min | **lateral gradient p99.5** | gradient max | width at half depth |
|---|---:|---:|---:|---:|---:|---:|
| **A** existing paint | **−2.28 %** | −8.95 % | **−9.85 %** | **0.324 %/mm** | 0.740 %/mm | **379 mm** |
| **B** deposit N = 60 | **−0.20 %** | −1.56 % | **−3.04 %** | **0.319 %/mm** | 0.517 %/mm | **119 mm** |
| **C**'s own lateral mottle | sd **7.21 %** | — | p95 |dev| **15.42 %** | **4.272 %/mm** | — |

Per side, peak darkening and where it sits:

| | +y (sunlit) | −y (shadowed) |
|---|---|---|
| A | −9.85 % at \|y\| = 646 mm | −3.50 % at 677 mm |
| B | −3.04 % at \|y\| = 843 mm | −0.76 % at 774 mm |

## THE THREE THINGS THIS SAYS, AND ONE OF THEM IS UNWELCOME FOR THE MODULE

**1. The claimed edge advantage is not there.** R2-1219 offered the module on the
strength of its lateral gradient. Measured in the film, the two arms are
**0.324 versus 0.319 %/mm — indistinguishable.** The module's transition *is*
shorter, but its amplitude is 3.2× smaller, and a gradient is the ratio of the
two. Whatever the retracted synthetic scene was measuring, this frame does not
reproduce a 6.6× edge, or any edge advantage at all.

**2. Neither mark has an edge in any useful sense.** The concrete's own lateral
gradient, measured on the same pixels by normalising C against a 201 mm running
mean of itself, is **4.272 %/mm — 13× either arm.** Its own lateral swing is
**±15.4 % at p95** against a −9.85 % paint and a −3.04 % deposit. Both marks are
*inside* the substrate's own structure. That is the same conclusion R2-1213
reached about the existing paint, arrived at independently, and it now applies
to the replacement as well.

**3. What the module actually delivers is CONTAINMENT, and that is real.** On
the sunlit side the deposit is ≈ 0 % outside |y| = 670 mm, is present across the
declared 251 mm patch, and is back to ≈ 0 % by 930 mm. The existing paint runs
from |y| = 350 mm to past 970 mm with **no boundary anywhere** — 379 mm wide at
half depth against the deposit's 119 mm. The mark also sits where the wheel
actually was. So the geometric case for the module survives this test intact.
**The visibility case does not.**

## The visual verdict, which is the thing that was asked for

At 1:1 at 4K density, on the sunlit apron:

* **B is invisible.** Put A, C and B side by side on the same pixels and I
  cannot find the deposit. In the amplified difference plate it is a faint
  mottle, partly *blue* — i.e. **brighter** than the control, which is exactly
  what R2-1219 §"THE UNWELCOME PART" predicts a gloss-only film does under a
  bright sky.
* **A is visible, and it reads as MOTTLE, not as a mark.** In an A/C comparison
  it is an obvious broad darkening; on its own, with nothing to compare against,
  it reads as a tonal variation of the concrete. There is no edge to find. It is
  a wash.
* **Neither reads as a tyre mark.** The client's complaint is not answered by
  either arm at this frame.

## Pure black, and the control region

**Pure black (all three 8-bit channels exactly 0), on the delivered crop:**

| arm | pure black |
|---|---:|
| A | **0.01608 %** |
| C | **0.01563 %** |
| B | **0.01563 %** |

**FLAGGED: it is not 0.0000 %.** R2-082's constraint is stated for beat 1–2 and
this is beat 3, but the number is reported as asked. **B and C are identical to
the last digit, so the deposit introduces no crushed black at all**; the existing
paint adds **+0.00045 pp**. The black is a property of the frame — the car's own
shadow is in this crop — and not of either mark.

**Control region, |y| = 1.35–1.75 m, which neither arm touches** (256 samples):

| | luma | R,G,B | saturation | p01 luma |
|---|---:|---|---:|---:|
| C | 84.1901 | 84.317 / 84.073 / 84.973 | 0.011788 | 81.436 |
| B | **84.1901** | **identical to C** | **0.011788** | 81.436 |
| A | 84.1947 | 84.328 / 84.076 / 84.980 | 0.011774 | 81.436 |

**The grade did not move.** B is bit-identical to C outside the mark, which also
proves the pixel alignment of every number above. A differs by **+0.0055 %**,
which is OIDN bleeding across the boundary and is the noise floor of this
instrument. **Blacks were not lifted (p01 identical on all three) and saturation
was not crushed (−0.12 % relative on A, zero on B).**

## What this does not test

* **Only frame 981.** 1030, 973 and 965 were not rendered. 981 is the *least*
  favourable of the four for this question — the crop is dominated by the car,
  its shadow and the near field. **f1030 is the one to run next**: a wide,
  sunlit, in-focus apron behind a small car, and the frame R2-1213's baseline
  was measured on. One more exec job, ≈ 25 min, ≈ **$0.17**, scene already
  staged.
* **The launch PATCHES were never in frame.** They live at world x = −1.80…−1.56,
  **31 m behind the car at f981**. Everything measured here is the tractive
  **film**. The module's hard 12 mm patch edges are untested by this and remain
  untested by anything.
* **N = 60 is the coordinator's art decision and was implemented, not revisited.**
  What this section adds is its price: at N = 60 the film is a third of the
  existing paint's amplitude and does not read.

## Cost, and a shared card

| | |
|---|---:|
| credit before | **$59.49** |
| credit after | **$59.01** |
| farm-wide drop (includes broker 2's own job) | $0.48 |
| **broker 1's card, total billed** | **$0.3061** |
| of which attributable to this section | **≈ $0.20–0.25** |
| the rest | another agent (`carhero`) who shared the card from 17:28 |

## Two defects this section paid for, both worth more than the render

**1. `rq exec` must not render on the GPU while a render worker is warm.**
Broker 1's exec job put a second copy of the 8 GB film on the same 32 GB card as
the warm worker's, and **another agent's job died twice with
`Out of memory in CUDA queue enqueue (integrator_shade_volume)`, the second time
terminally.** Cancelling this job fixed their renders within seconds — the
causation is not inferred, it was tested. `worker/exec_server.py`'s design note
("the *never thread* law is right for GPU work") reasons about CPU builds
running beside the worker; nothing enforces that an exec child is CPU-only, and
`OPTIX_CACHE_PATH` is set for exec children, which reads as an invitation.
**Recommendation: the exec server should refuse `cycles.device = GPU`, or the
broker should not dispatch a GPU exec job while the render worker holds a
scene.** This section's re-run was CPU-only (`--device CPU --threads 12`) and
caused no further interference.

**2. Broker 1 was running code older than its own fix.** The process started at
05:51; `broker/execservice.py` was fixed at 07:45. The stale process staged the
scene to `/workspace/scene.blend` — the exact legacy default `SceneStagingMismatch`
was written to prevent — while the freshly-deployed exec server read
`/workspace/scenes/<digest>/`. It cost **two 8 GB pushes** and would have cost a
third; the refusal that is supposed to be terminal on first sight did not fire,
because the reader's complaint arrived as a plain `RuntimeError`. Restarting
broker 1 through `scripts/brokerd.sh` fixed it immediately (it adopted the
running instance, so the restart was free) and the very next push went to
`/workspace/scenes/493845696f4899f6/film17_breach.blend.part` with `.complete`
written last. **A broker that outlives an edit to its own source is a broker
running code nobody has read.**

## Artefacts

    render/r2_1221/raw/r21221_f0981_{A,C,B}.png   the delivered 4K crops, untouched
    render/r2_1221/strip_f0981_1to1.png           A | C | B on the same pixels, 1:1
    render/r2_1221/band_windows_f0981_1to1.png    1:1 windows ON the driven line
    render/r2_1221/overlay_f0981_x14.png          A−C and B−C at 14x, with the
                                                  declared world lines drawn on
    render/r2_1221/geometry_f0981_on_C.png        the same lines on the control
    render/r2_1221/profile_f0981.png              lateral tone + gradient
    render/r2_1221/profile_f0981_zoom.png         the two arms across the line
    render/r2_1221/measured.json                  every number above
    render/r2_1221/probe.json                     the job's own report
    work/r2_1221/{apron_ab,dryrun,measure,make_crops,plot_profiles,overlay}.py

---

# R2-1228 — THE POLISHED FLOOR IS **BRIGHTER**. MEASURED. THE PREDICTION IS REFUTED.

*(Renumbered from R2-1222 by the block owner: that number was already the
handover section, and `tools/r2_1222_verify_handover.py` is named for it.
Content unaltered. Second heading collision in this block — see also R2-1219,
renumbered from an "APPENDED R2-1216".)*

**Sign first, as asked. The deposit on `FloorPolished` reads LIGHTER, not
darker, and the R2-082 crushed-black warning is NOT the live constraint on this
surface.** The prediction on record in R2-1214 — "rubber kills that coat and
removes the return -> darker" — is refuted by measurement.

4K pixel law, **3.32 mm/px** (R2-1211's own showroom-floor p50 is 3.31), 25 deg
grazing, 282 199 px of footprint (9.92 % of the traced region), identical
camera / sun / seed so the ratio cancels the lighting exactly.

| arm | mean | p05 | p50 | p95 | p99.5 lateral gradient |
|---|---:|---:|---:|---:|---:|
| derived film, N = 1 | **+3.06 %** | −0.57 % | **+2.98 %** | +7.04 % | **0.371 %/mm** |
| derived film, N = 60 | −1.41 % | −12.77 % | +0.24 % | +3.92 % | 0.417 %/mm |

It is brighter almost everywhere: even p05 is only −0.57 %. Only at N = 60,
where `Coverage` finally becomes non-negligible and the albedo dim engages, does
any part of the distribution go meaningfully dark, and even there the median is
**+0.24 %**.

### Pure black — the number R2-082 actually turns on

Exposure solved so the CONTROL arm reproduces R2-1214's own measured floor
operating point: **−5.546 EV gives a control mean of 0.1005 against the 0.10
target.** Both arms then share it.

| arm | pure black | frame lum min | **darkest in-footprint pixel** |
|---|---:|---:|---:|
| control | **0.0000 %** (0 px) | 0.06083 | 0.06138 |
| deposit | **0.0000 %** (0 px) | 0.06083 | **0.06166 — RAISED** |
| traffic N = 60 | **0.0000 %** (0 px) | 0.05885 | 0.06138 — unchanged |

**The deposit does not create black; it lifts the floor's darkest pixel**, the
same direction the concrete arm moved (0.22473 -> 0.22755). The frame minimum is
bit-identical between control and deposit because the darkest pixel in the frame
is outside the deposit's footprint entirely.

### Why the sign came out this way, and why the three-scale fix decided it

The floor never receives a launch mark — the mark is on the deck at x = −1.80;
the floor at x = 6.3…15 gets the **10.6 nm tractive film and nothing else**. At
10.6 nm the three scales disagree by an order of magnitude, and coat weight is
the channel that moved:

| channel | control | deposit | delta | driven by |
|---|---:|---:|---:|---|
| Roughness | 0.0975 | 0.2373 | **+143.4 %** | wetting, 7.6 nm |
| Coat Roughness | 0.0450 | 0.1555 | **+245.5 %** | wetting, 7.6 nm |
| **Coat Weight** | 0.4500 | 0.4366 | **−3.0 %** | **interface, 110 nm** |

Under the superseded wetting-driven model coat weight went **0.45 -> 0.2401, a
47 % suppression**. Under the corrected model it is **3.0 %**. So the deposit
stopped being *"the coat removed"* and became *"the coat broadened"* — and those
have opposite signs at an off-specular view. A 0.045-roughness coat returns
light in a narrow lobe that a 25 deg camera under a 12.47 deg sun sits well off;
widening it to 0.156 moves return **toward** the camera.

**So R2-1214's mechanism was sound and its sign was an artefact of a model that
let a monolayer strip a clearcoat.** Both halves of that sentence matter: the
reasoning identified the right channel, and the wrong saturation length made it
point the wrong way.

### What this does and does not license

**It does NOT license relaxing the coat-suppression cap.** The cap is inert here
only because nothing on this floor is optically thick. The moment a genuinely
thick mark lands on a coated dielectric — which this film never is and a launch
patch would be — `Interface` goes to 1.0, the 62 % suppression engages in full,
and the cap is the only thing standing between R2-082 and a crushed black. It
should stay exactly as it is, and it should stay *because* it is currently doing
nothing.

**And the standing caveat, unchanged.** This arm is lit by the contract sun, not
the showroom's 61-lamp rig, which cannot be loaded on an 11 GB box. Solving the
exposure to R2-1214's measured 0.10 makes the **delta** trustworthy and the
absolute level a stand-in. **0.0000 % here is evidence, not the R2-082 gate**;
that still has to be run on a real beat-1/2 frame.

### The three surfaces, side by side

| surface | derived N = 1 | sign | lateral gradient |
|---|---:|---|---:|
| turntable deck, the launch mark | **+23.2 %** | brighter | — |
| showroom floor, film only | **+3.06 %** | brighter | 0.371 %/mm |
| concrete apron, film only | +1.56 % | brighter | 1.067 %/mm |
| *(the existing apron paint)* | *−18.82 %* | *darker* | *0.243 %/mm* |

**Every derived deposit in this film is a brightening.** The only darkening
anywhere in the block is the hand-painted apron streak, which is also the only
thing in it not derived from the telemetry.

---

## R2-1227 — an exec job took the render worker's card, because nothing said it may not

**The incident.** An agent ran a render through `rq exec` and set
`cycles.device = GPU`. That put a second ~8 GB film scene on the same 32 GB card
as an already-warm render worker holding its own scene. Another agent's
`carhero` job died with `Out of memory in CUDA queue enqueue` **twice — the
second time terminally**. Cancelling the offending exec job fixed the victim
within seconds; the re-run was CPU-only and fine.

**The defect is not the agent.** `worker/exec_server.py` is designed around a
CPU-only assumption from end to end: every sizing decision in it is about a
23-CPU cgroup quota and a 90 GiB `memory.max`, `await_memory` gates admission on
the second of those, and `deprioritise_for_oom` exists specifically so an exec
child is what a RAM squeeze kills rather than the render worker. **None of that
reaches VRAM.** The card has no cgroup, no gate, and no OOM score to bias — two
processes that each fit alone are both admitted and one of them dies inside
CUDA, and which one is not a decision anybody made. The assumption was written
down in four docstrings and enforced in zero lines of code.

This is the fourth member of one family in a day: `pkill -f` matching everything
present; `rq cancel` sweeping four jobs from three owners; a kill entering a
six-deep process chain at the middle; and now an exec claiming a card another
process is using. Every one is an operation whose default scope is *"whatever is
there"* rather than *"what is mine"*, and every one had previously been answered
with a warning.

### The mechanism, in three parts

Written, tested, **not deployed** (see the last section). All in
`~/vast-render`.

**1. The clamp — the half that cannot be argued with.** `run_child` now launches
every exec child with `CUDA_VISIBLE_DEVICES=""` and `HIP_VISIBLE_DEVICES=""`
unless the job declared otherwise. Cycles enumerates zero devices,
`scene.cycles.device = 'GPU'` still assigns cleanly, and the render falls to the
CPU — which is what every exec job on the box was already *assumed* to be doing.

This is deliberately not a predicate about the submitted script. `entry` is
caller-supplied Python — that is the entire point of the job type — so any check
on what the script "intends" is a guess about a file that can compute its intent
at runtime. An empty `CUDA_VISIBLE_DEVICES` is not a guess.

**2. The refusal — the half that names what it is protecting.** `gpu` is now a
declared field (`rq exec --gpu`, default false, validated as a real boolean so a
truthy string cannot declare it by accident). A job that declares it is checked
against who actually holds the card, and refused:

    refusing <job>: the render worker holds
    /workspace/scenes/<hash>/film18.blend on NVIDIA GeForce RTX 5090
    (pid 1234, 8.1G resident). ...

The holder is found the way `reap_orphans` finds what it must **not** touch: by
the literal `-P <workspace>/server.py` token that `remote.worker_launch_cmd`
builds, never by the name "blender", which on that box also matches the exec
server, twelve exec children and every orphan of either. The scene comes free on
the same argv (`-b <blend>`), so *"the worker holds \<scene\>"* is **read**, not
inferred and not kept in a state file somebody has to remember to update. Not a
byte is signalled, connected to, or asked — a ping to the render worker blocks
for the length of a 4K frame, which is exactly the moment the answer is needed.

The check lands in `validate()`, before the slot, before the memory gate and
before any scene push: a refused job costs one `/proc` walk and one
`nvidia-smi`, not a slot and not 8 GB of transfer.

**Terminal, on the first refusal.** Deliberately the opposite verdict to
`ExecMemoryShort`, which sits ten lines away and is a *wait*. Memory comes back
when sibling builds end; the render worker does not end — it holds its scene for
the whole campaign, by design and as the entire reason it exists. A wait would
requeue forever. So it crosses the wire as `gpu_refused: true` and
`broker/execservice.py` calls `fail_terminal`, the way `SceneStagingMismatch` is
handled.

**A refusal, not a silent downgrade.** A downgrade is what part 1 already does
for undeclared jobs; but a job that *declared* `gpu: true` said something, and
quietly doing the opposite of what it said is how this defect stayed invisible.

**3. The clamp is never silent.** Part 1 would have hidden the defect just as
well as the absence of part 1 did. So the bundle is scanned for GPU device
selection, the matching files are named on the reply (`gpu_hints`,
`gpu_clamped`) and logged by the broker at WARNING against the job id. The scan
is **advisory only and never refuses** — a regex over caller-supplied Python is
trivially defeated and just as trivially false-positived, and a scan that could
refuse would break other agents' CPU-only builds on a comment.

**The reverse order is made answerable, not yet guarded.** `ping` now reports
`gpu`: the holder, the cards, and `gpu_jobs` — every admitted job that declared
the card. `remote.ensure_ready` already pings the exec server before it touches
the render worker, so the fact is available exactly where the decision is made.
Consuming it is a broker-side change that is **specified and not written**.

### Verification

`worker/test_exec_server.py` grew a `check_the_gpu_guard` section: **118/118**
(was 103). The tests assert the artefact, not the exception — the clamp is
checked by reading `CUDA_VISIBLE_DEVICES` out of a **real child's environment**,
and the holder detection runs against a **real process started with the real
argv shape** rather than a mock of itself. `broker/test_broker.py` offline:
**474/474** (was 473), the new check pinning `failed 1/3` — terminal, first
refusal.

### And the second defect, which is the more valuable half

The staging bug that preceded this one happened because **broker 1 was running
code older than its own fix**: process started 05:51, `execservice.py` fixed
07:45. It therefore staged to the legacy default `/workspace/scene.blend`, which
is precisely what `SceneStagingMismatch` exists to prevent, and the
terminal-on-first-sight refusal never fired. Everyone debugging it — including
the agent who wrote the fix — was reading a file nothing was executing.

**A fix in the tree and not on the box is a fix that does not exist.** That is a
sentence. `scripts/drift.py` and `./rq drift` are the instrument.

It reads `/proc`, never the broker's HTTP API — *"is that process running the
code I am reading?"* is the one question a process running the wrong code can
answer wrongly. Per file it compares the source mtime and sha256 against the
process's real start time (`/proc/<pid>/stat` field 22 plus `btime`, not the
mtime of `/proc/<pid>`, which is when you looked) and against the PEP 552 `.pyc`
header, which records the source mtime and size **as seen at import**. Three
verdicts: `STALE`, `ok`, and `?` for what cannot be determined. `?` is never
rendered as `ok`.

Its own first draft was wrong in the instructive direction and is worth
recording: it read `broker/__pycache__/app.cpython-**314**.pyc`, left over from
an unrelated 3.14 run, while the brokers run `.venv/bin/python` (3.13,
`cpython-313`) — and reported **seven clean files as STALE**. A drift checker
that cries wolf is worse than none, because the next real one is the one nobody
reads. It now takes the cache tag from the broker's own interpreter, named on
its argv.

**Measured, 2026-08-07 18:2x:**

| broker | pid | started | drifted files |
|---|---:|---|---:|
| default (port 8760, `state/`) | 1748687 | 2026-08-07 17:19:30 | **0** before this task's own edits |
| `ladderbroker` (port 8761, `state2/`) | 677451 | **2026-08-04 20:20:55** | **13** |

`ladderbroker` has been running for **70 hours** against a tree that has moved
thirteen files under it: `app.py` (07:53), `config.py` (05:49), `execremote.py`
(03:35), `execservice.py`, `fleet.py` (07:53), **`remote.py` (07:45 — the exact
file and timestamp from the staging incident)**, `test_broker.py`, `fleetctl`,
`rq`, `brokerd.sh`, `broker2.sh`, `brokerN.sh`, `vastctl.py`. It is executing
none of them. It is the broker that would reproduce the staging bug today.

Two more places now carry the same fact without anyone running a command: the
broker logs its own module hashes and start time at startup
(`broker/app.py:log_own_code`), and the exec server reports `code_sha256` on
every ping, which `ExecService.check_deployed_code` compares against the file it
would have pushed and warns about **once** per version pair. Both of those only
take effect on a restart.

### Deployment status — NOTHING WAS DEPLOYED

No broker was restarted, no job was cancelled, no process was signalled, no
vast.ai instance was touched. Every change is in the working tree only. **The
GPU guard and both startup self-reports take effect only on a restart of the
process that runs them**, which re-claims jobs mid-flight and is a human
decision. `scripts/drift.py` and `./rq drift` work **now**, against the running
processes, with no restart — they were run against both live brokers to produce
the table above.

---

# R2-1229 — every derived deposit in this film is a BRIGHTENING, and the only dark mark is the one nobody derived

The single most useful sentence in this block, and it only became visible once
all three substrates had been measured on a clean scene:

| surface | derived, N=1 | **sign** | provenance |
|---|---:|---|---|
| dais deck (launch mark, 11.0 µm) | **+23.2 %** | **brighter** | derived from telemetry |
| showroom floor (film, 10.6 nm) | **+3.06 %** | **brighter** | derived from telemetry |
| concrete apron (film, 10.6 nm) | **+0.71 %** (p50 −0.91 %) | **brighter, barely** | derived from telemetry |
| *existing apron paint* | *−18.82 %* | *darker* | **hand-painted, derived from nothing** |

**The only darkening anywhere in this block is the one thing not derived from
the telemetry.** Every quantity that came out of the car's actual motion made
its surface *lighter*. That is not a bug in the module — it was measured three
times, on three different substrates, under two different physical models, and
survived the correction that invalidated its neighbours.

And it explains the client's complaint far better than "the marks are too
faint". **The marks are not faint. They are the wrong colour, and physics says
so.**

## Why, in one line per surface

A deposit changes appearance two ways: it **replaces the interface** (specular,
coat, metallic) and it **adds pigment** (albedo). Which dominates depends on
thickness; which *sign* results depends on the substrate:

- **Deck** — a conductor at base 0.048 with **no diffuse lobe**. Any dielectric
  film adds one. Brighter, unavoidably.
- **Floor** — a dielectric whose blacks sit on a 0.45-weight coat. A 10.6 nm
  film **broadens** that coat rather than removing it (R2-1228). Brighter.
- **Apron** — concrete at 0.18–0.30 linear. Rubber's 0.042 *is* darker — but at
  10.6 nm the film contributes **0.34 % coverage**, so there is effectively no
  pigment at all and what is left is gloss. Under a bright sky, brighter.

## The resolution, and it is a continuity decision rather than a rendering one

**One car's first launch cannot make a dark mark on any of these surfaces.**
That is not a shortcoming of the model; it is the correct answer, and R2-1215's
`+1.56 %` is what it looks like.

But a **used** surface can, because accumulated rubber becomes optically thick
and then pigment dominates. That is why real pit lanes and racing lines are
black. The module's albedo channel is coverage-driven on a **3.1 µm** scale, so
coverage ≈ 1 − exp(−t / 3.1 µm):

**Verified against the implementation, not assumed.** `coverage(d)`,
`interface(d)` and `wetting(d)` are `1 − exp(−d/τ)` at
`TAU_OPTICAL_M = 3.1 µm`, `TAU_IFACE_M = 110 nm` (quarter-wave) and
`TAU_WET_M = 7.6 nm`; `Traffic Passes` scales density **linearly**
(`tyre_deposit.py:853`). Recomputing the module's own anchors reproduces its
docstring to four decimals — film 10.6 nm → 0.7521 / 0.0919 / 0.0034 against its
stated 0.7523 / 0.0918 / 0.0034; mark 11.0 µm → 1.0000 / 1.0000 / 0.9712 against
0.9716.

| passes | thickness | **coverage** (albedo) | **interface** (gloss) | character |
|---|---:|---:|---:|---|
| 1 | 10.6 nm | **0.34 %** | 9.2 % | gloss only — measured **+0.71 %**, p50 straddles zero |
| **60** | 636 nm | **18.6 %** | **99.7 %** | measured **−0.20 %, invisible** (R2-1225) |
| 100 | 1.06 µm | 29.0 % | 100 % | |
| 300 | 3.18 µm | 64.2 % | 100 % | pigment now dominates |
| 600 | 6.36 µm | 87.2 % | 100 % | |
| 1000 | 10.6 µm | **96.7 %** | 100 % | optically thick — the **launch patch**'s own regime |

50 % coverage needs **N = 203**; 90 % needs **N = 673**; 97 % needs **N = 1026**.

> **N = 60 IS THE WORST POSSIBLE CHOICE, AND THE TWO COLUMNS SHOW WHY.** The
> *interface* term — which carries all of the brightening — is **99.7 %
> saturated at N = 60**. The *coverage* term — which carries all of the
> darkening — is **18.6 %**. So N = 60 buys the entire gloss brightening and
> almost none of the pigment darkening, and the two nearly cancel. **That is
> −0.20 %.** The null was not a marginal failure; it was measured at the exact
> crossover where the mark has every reason to be invisible.
>
> Everything above N ≈ 60 is **pure albedo**: the Fresnel change is already
> maxed, so additional passes only darken. The whole transition from "glossy
> film" to "black pit exit" happens between **N = 60 and N ≈ 600**, which is
> precisely the interval nobody has rendered.

**This reframes R2-1225's null.** `Traffic Passes = 60` was tested and found
invisible — but at ~20 % coverage it was **never dark enough to test the
longitudinal question at all.** A 20 %-coverage film cannot be dark at any edge
sharpness or any coherence length. The N=60 null is a statement about coverage,
not about coherence. A high-N arm has been requested so the coherence question
is asked of a mark that has something to be coherent about.

> **THE DECISION THIS SURFACES, AND IT IS NOT A RENDERING ONE.** Choosing N is
> choosing **how old the circuit is**, not how visible we would like the mark to
> be. This surface is the **pit-exit access road** (`SURF_AccessRoad`), not a
> showroom forecourt — a pit exit run all season is optically thick and black,
> and at N ≈ 300–1000 the derived model produces exactly that, *darkly*, without
> a single hand-painted number. **That is the setting where the client's
> expectation and the physics stop disagreeing.**
>
> Predicted and on record before the render: **a high-N concrete arm should go
> DARKER**, because rubber at 0.042 is well below concrete's 0.18–0.30, while
> the same film on the deck stays **brighter**. Same film, opposite signs, from
> the substrate alone. **If the high-N concrete arm does not darken, this
> section is wrong.**

---

# R2-1230 — CONCRETE, RE-MEASURED UNDER THE THREE-SCALE MODEL. SUPERSEDES R2-1219's TABLE.

*(Renumbered from R2-1223 by the block owner: that number was already the
time-gating family audit. **Third heading collision in this block** — see also
R2-1219 (from "APPENDED R2-1216") and R2-1228 (from R2-1222). Appending agents
are picking numbers without re-reading the file. Content unaltered.)*

Same camera, sun, seed and 340 485-px footprint. The prediction filed in
R2-1221 was that the apron's specular delta would fall from +31.4 % to a few
per cent and the derived N = 1 film would therefore read **below** its previous
+1.56 %. Both hold.

| arm | mean | p05 | p50 | p95 | (superseded) |
|---|---:|---:|---:|---:|---:|
| derived film, N = 1 | **+0.71 %** | −7.87 % | **−0.91 %** | +13.29 % | +1.56 % |
| derived film, N = 60 | **−4.35 %** | −20.88 % | −7.62 % | +18.69 % | −4.33 % |
| existing paint | **−18.82 %** | −25.69 % | −18.75 % | −11.93 % | −18.82 % |

| channel | control | deposit | delta | superseded | existing |
|---|---:|---:|---:|---:|---:|
| Roughness | 0.8002 | 0.6664 | −16.7 % | −16.7 % | −0.0773 |
| **Specular IOR Level** | 0.3200 | **0.3315** | **+3.6 %** | *+31.4 %* | **+0.0000** |
| Height Coarse (mean) | 0.4995 | 0.4987 | −0.2 % | −0.2 % | +0.0000 |

The two wetting-driven channels are **bit-identical** across the model change,
as they must be; only the interface-driven one moved. The existing paint is
unchanged to four digits because no field touches it — a useful null.

**The apron result gets weaker, not stronger, and that is the honest direction.**
The derived single pass is now **+0.71 % mean with a p50 of −0.91 %** — it
straddles zero. A 10.6 nm transfer film owns 9.2 % of the Fresnel interface and
essentially none of the albedo, so what is left is a roughness change alone.
**There is no derivable mark on that apron from this car's single pass, and the
number is now small enough that saying so is not an interpretation.**

### One correction to R2-1220 addendum 2, against this block's own interest

That addendum reported that the deposit RAISES concrete's darkest
in-footprint pixel. **Under the corrected model it does not.**

| concrete, darkest in-footprint pixel | control | deposit |
|---|---:|---:|
| superseded (specular +31.4 %) | 0.22473 | 0.22755 — raised |
| **corrected (specular +3.6 %)** | 0.22335 | **0.21804 — lowered** |

With the spurious specular lift removed, the roughness change dominates and the
darkest pixels go slightly down instead of up. **Pure black remains 0.0000 % on
all four arms** and 0.218 is nowhere near zero, so nothing is at risk — but the
claim as written was an artefact of the bug and is withdrawn. The floor's lift
(0.06138 -> 0.06166, R2-1222) was measured under the corrected model and stands.


---

# R2-1232 — DECK CONFIRMED ON PIXELS: THE MARK IS UNCHANGED, THE ARTEFACT IS GONE, AND `Traffic Passes` MUST BE PER-SURFACE

*(Renumbered by its own author from R2-1224, which the block owner had already used for the octave census. 1226 and 1227 are skipped in case they are in flight elsewhere. Content unaltered.)*

1.31 mm/px, 30 deg diagnostic grazing, 540 784 px of footprint of which the two
launch patches are **13 112 px (0.46 %)**.

### The prediction filed in R2-1221, checked

| region | superseded | corrected | |
|---|---:|---:|---|
| **the launch patches** | +23.2 % | **+23.18 %** | unchanged, as predicted |
| the whole footprint | +52.2 % | **+10.90 %** | the artefact collapses |

**+23.2 % -> +23.18 %.** The mark is 11.0 um of rubber, which saturates all
three scales, so the correction is a no-op there and the shader is bit-for-bit
the same. The independent check is the `traffic` arm: `Traffic Passes` scales
only the FILM, so its mark must be identical to the deposit arm's — measured
**+23.19 % against +23.18 %**. **R2-1216's revision stands.**

| channel | control | deposit | delta |
|---|---:|---:|---:|
| Roughness | 0.3935 | 0.4975 | +26.4 % (wetting) |
| **Metallic** | 0.8600 | **0.8156** | **−5.2 %** (interface; was driving to 0.25) |
| Base Colour R | 0.0491 | 0.0490 | −0.1 % |

The metal now stays metal across the film band, which is the whole point.

Pure black **0.0000 % on every arm**, and the deposit RAISES the darkest
in-footprint pixel: 0.15861 -> **0.18188** (traffic 0.25859).

### THE NEW FINDING: `Traffic Passes` IS A PER-SURFACE QUANTITY AND MUST NOT BE GLOBAL

| deck, whole footprint | mean | p50 | p95 |
|---|---:|---:|---:|
| N = 1 | +10.90 % | +10.77 % | +27.65 % |
| **N = 60** | **+84.19 %** | **+85.90 %** | **+141.25 %** |

At N = 60 the film is 636 nm thick, which IS thick against a quarter wave, so
`Interface` saturates and the tractive film legitimately kills the deck's
metallic character — producing an **+84 % bright band straight across the
turntable**. The physics is right; applying it here is not. **A showroom display
turntable has not been driven over sixty times.** An access road plausibly has.

So the knob has to be bound per surface, and its values are not free:

* **turntable deck: N = 1, by construction.** The car drives off it once. Any
  other value is a claim about a display object that nothing supports.
* **showroom floor: N = 1** for the same reason.
* **concrete apron: N is the open question**, and it is the only surface where
  it is a question, because it is the only one that is a public access road.

`FILM_TRAFFIC_SWEEP = 60` currently exists only as a gate arm. **It must not
become a global default**; if it ships it ships as a per-material argument on
the apron alone. Recorded here because a single global knob would have put an
84 % stripe on the turntable while fixing the apron, and nothing in the gate
would have objected — the deck arm is the only reason it is visible at all.

### One judgement call this block should make deliberately

The deck's derived N = 1 film band reads **+10.90 %**, against the floor's
+3.06 % and the apron's +0.71 %. All three are the same 10.6 nm film; the deck
shows it 3.6x more strongly than the floor and 15x more than the apron because a
roughness change on a dark conductor moves more radiance than the same change on
a coated dielectric or on matte concrete. R2-1215 asks that the film "read as a
faint continuous tint, never as a mark". **+10.9 % is at the upper edge of
faint**, and it is a band on the surface that is 23.9 % of the frame at p50.
It is derived, not painted — but it should be looked at in the 4K A/B rather
than assumed acceptable because it came out of the physics.

---

# R2-1231 — open: the deck's derived film band is +10.9 % across a quarter of the frame

Raised by the module's author against the module's own result, and left open
rather than resolved, because it is a judgement about the shot and not about the
physics.

At **N = 1** — the correct, derived, non-negotiable setting for the deck — the
launch mark measures **+23.18 %** and is the thing this block set out to build.
But the surrounding **tractive film band** on the same surface measures
**+10.90 %**, and the deck is **23.9 % of the frame** in the beat-2 window.

**That is a 10.9 % brightening across a quarter of the frame, in beat 2.** It is
derived rather than painted, and every step of the derivation has now been
checked twice. But *"the physics produced it"* is not the same as *"it is
acceptable in the shot"*, and this block has already recorded one case
(R2-1216's static deck mark) where a physically correct result would have
shipped a worse defect than the one it fixed.

Specifically it needs checking against **R2-082**: beat 1–2 pure black is
0.0000 % on every frame and the showroom practicals were levelled by an identity
to get there. A broad brightening is not the direction that breaks a black-level
gate — but it *is* the direction that changes the showroom's overall look, and
nobody has looked at it.

**Not to be resolved by argument.** It is on the f837 shortlist for a visual
verdict at 1:1, alongside the launch patches themselves.

---

# R2-1233 — R2-1225 REFUTES MY EDGE CLAIM. IT IS WITHDRAWN.

Written by the author of `world/items/tyre_deposit.py`, about that module.

R2-1225 rendered the apron A/B **in the film** — one blend, one camera, one sun,
one seed, three link states of one material, with the control proving pixel
alignment bit-for-bit. My numbers came from a **reduced replica** in a
standalone scene. **Where they disagree, R2-1225 is right and I am wrong**, and
the disagreement is not small.

| lateral gradient, p99.5 | my replica | **in the film (R2-1225)** |
|---|---:|---:|
| existing paint | 0.243 %/mm | **0.324 %/mm** |
| `tyre_deposit` | 1.067 %/mm (N=1), **1.605** (N=60) | **0.319 %/mm** (N=60) |
| ratio claimed | **4.4x / 6.6x** | **1.0x — none** |

**The "4.4x edge" in R2-1219 and everything built on it is withdrawn.**

## Why the two instruments disagree, and it is my error not theirs

R2-1225 states the mechanism in one line and it is correct: *"The module's
transition IS shorter, but its amplitude is 3.2x smaller, and a gradient is the
ratio of the two."* A gradient is amplitude over distance. I measured a real
improvement in the **distance** and then reported the **quotient**, which also
carries an amplitude my replica got wrong.

**My replica gave the deposit far more amplitude than the real material does.**
Mine read −4.35 % mean at N = 60; the film reads **−0.20 %** — a factor of ~20.
`_concrete_substrate` carries `M_Surf_Concrete`'s Principled parameters and its
+-14.5 % bay-tone hash and **nothing else**: no crazing, no efflorescence, no
joints, no grit, no per-slab segregation. Those are most of what the real
surface does to light, and a roughness-and-specular deposit laid over a much
plainer substrate is a much larger fraction of what is there. The replica was
built to make the % deviation *comparable to the −5.73 % baseline*, and it does
not do that job.

**And my own control said so, if I had read it as evidence rather than as
noise.** I reported "the substrate's own variation on the same pixels: sd
41.39 %" and set it aside as contaminated by the depth-lighting gradient. R2-1225
measures the real thing properly — normalising the control against a 201 mm
running mean of itself — and gets a lateral gradient of **4.272 %/mm, 13x either
mark**, with a p95 lateral swing of **+-15.4 %**. Both marks live inside the
substrate's own structure. That is R2-1213's conclusion about the existing paint,
reached independently, and it now lands on the replacement too.

## What survives, stated narrowly

R2-1225 confirms these, and they are geometric claims rather than photometric
ones — which is exactly the class my instrument could measure and did:

* **Containment. 119 mm at half depth against the existing paint's 379 mm**, ~0 %
  outside |y| = 670 mm, present across the declared 251 mm patch, back to ~0 % by
  930 mm — against a paint that runs from 350 mm to past 970 mm with no boundary
  anywhere.
* **Position.** The mark is where the wheel was, at |y| = 0.79750, not 77.5 mm
  inboard of it.
* **The derived profile, the hard 12 mm edges and the time gate** — none of which
  R2-1225 could test, because the launch patches are 31 m behind the car at f981
  and were never in frame. They remain untested by anything in the film.

## What does NOT survive

* The edge advantage on the apron. Withdrawn.
* Any implication that the module makes the apron read. **R2-1225 looked at it at
  1:1 and could not find it.** That is consistent with my own headline — a
  10.6 nm film owns no albedo — but I paired that honest finding with an edge
  claim that made it sound like a win. It was not.
* **The replica's % deltas as predictors of in-film magnitude, on any surface.**
  R2-1228 (floor) and R2-1232 (deck) were measured on the same replicas and are
  subject to the same error. Their **signs** rest on shading physics that the
  substrate does not change — a conductor has no diffuse lobe wherever it is
  measured, and a coat that is not suppressed cannot darken by being suppressed —
  so I would defend "brighter" on both. **Their magnitudes should be treated as
  upper bounds until measured in the film**, and the deck's +23.2 % launch patch
  is the one worth the render: it is the only optically thick mark in the block
  and the only place the derived physics has real amplitude.

## The instrument lesson, which is the part worth keeping

A standalone gate can measure what a shader **does** — a channel delta, a
world-space position, a saturation law, a time gate. It cannot measure what a
material **reads like**, because reading is a contrast against the rest of the
surface, and the rest of the surface is precisely what a reduced replica leaves
out. I built the replica to make the comparison fair and then quoted a ratio in
which the omission is the denominator.

**R2-1220 and R2-1221 were caught by measurement. This one was caught by someone
else's measurement, in the film, after I had reported.** That is the weaker
position of the three and it is the one to design against: the module's own gate
should have refused to report a contrast statistic at all.

---

# R2-1234 — every instrument in this block was wrong at least once, and always about the environment rather than the subject

Collected because the pattern is sharper than any single instance, and because
this block spent more effort correcting its measurements than making them.

| # | the instrument | what was actually wrong | caught by |
|---|---|---|---|
| R2-1220 | the gate's **scene** | the default Cube sat where the deck scene is centred; three runs of deck figures were photographs of it | the module's author, on a probe |
| R2-1221 | the gate's **physics** | Metallic/Specular/Coat driven by *wetting*, which saturates at a monolayer, so a 10.6 nm film turned metal dielectric | the module's author, on the deck arm |
| R2-1233 | the gate's **substrate** | the replica carried the material's parameters but none of its crazing, efflorescence, joints or grit — a 20× amplitude error | **someone else's render, after publication** |
| R2-1225 | the block owner's **axis** | every measurement taken across the mark, none along it | a null result in the film |
| R2-1213 | the block owner's **estimator** | a 0.9 m trend filter absorbing a 640 mm feature — reported −5.73 % for a −18.82 % mark | a matched A/B |
| R2-1211 | the block owner's **rolling radius** | 0.378 from pairing a forward-difference ω with a point speed; the true value is 0.360 | re-derivation against three sources |

**Not one of these was an error about rubber.** Every one was an error about the
*environment the measurement was taken in* — what else was in the scene, what
physical scale a term saturates on, what the comparison surface actually
contains, which axis the statistic runs along, what a filter passes. **The
subject was never the problem.**

And every one produced a number that looked entirely plausible. "Roughness 9.82"
was obviously broken; **−5.73 %, 6.6×, 0.378 m and +52.2 % were not.** A wrong
instrument does not usually announce itself — it returns a number of the right
order, with the right units, that survives being sanity-checked by the person
who chose the instrument.

**The one to design against is R2-1233**, because it is the only one caught
*after* publication and by someone else. Its fix is a refusal, not a habit: a
gate that measures contrast against a replica must **refuse to emit a contrast
statistic** unless the replica carries the real substrate's structure — the same
shape as R2-1220's fix (refuse to measure a scene containing objects the module
did not make) and the same shape as `assert_scene_is_ours`. **Three of the six
above would have been prevented by an instrument that refuses to run rather than
a person who remembers to check.**

---

# R2-1226 — MEASURED **ALONG** THE MARK. Coherence is real, it is worth 4–5×, and it is not what was missing: **optical thickness was.**

*Commissioned to test one hypothesis — that the eye is a matched filter along a
tyre mark's axis, so a coherent line beats isotropic mottle by √(L/l). The
hypothesis is **confirmed in mechanism and refuted as an explanation.** Along-track
integration is worth a factor of 4.4 on the existing paint, which is the whole
difference between SNR 0.94 across the mark and SNR 4.16 along it. It is still
not enough, and the thing that is enough is `Traffic Passes`.*

> ## THE ONE-LINE ANSWER
>
> **On this substrate a mark reads when it is optically thick, and coherence
> then multiplies it. Neither the existing paint nor the module at N = 60
> reaches a detection threshold at ANY integration length. At N = 300 the
> module's mark reads; at N = 1000 it is unmistakable. And the deck patches
> read — pale, not dark — at f837.**
>
> | arm | mean tone, +y / −y | SNR across (L→0) | **SNR along, best** | reads at 1:1? |
> |---|---:|---:|---:|---|
> | **A** `build_surface` paint | −5.70 / −6.66 % | 0.94 | **4.16** | **no** — a tonal wash |
> | **B** deposit N = 60 | −2.36 / **+2.26** % | 0.41 | 1.60 | **no** — invisible |
> | **B** deposit N = 300 | −10.75 / −5.87 % | 1.52 | **8.21** | yes, faint |
> | **B** deposit N = 1000 | −17.97 / −14.04 % | 2.54 | **13.90** | **yes, plainly** |
> | C the substrate itself | 0 | 0.33 | 0.64 | (the null) |
>
> **R2-1225's arm B was rendered with one of its four channels dead.** Its graft
> wired `Coverage`, `Wetting` and `Grain` into `TDP_Apply_Concrete` and left
> **`Interface` at its 0.0 default — which is the Specular IOR Level channel**,
> the one R2-1213 called *missing* from the existing paint and R2-1219 measured
> at +31.4 %. Every arm here links all four, asserted on the built socket.

## What was rendered, and on what

Three delivered `rq exec` jobs on **broker 1**, all **CPU-only**, one blend, one
camera, one sun, one seed, arms toggled as link states of one material.

| job | frame | arms | exec | delivered |
|---|---|---|---:|---|
| `d529d2bc033e` | 1030 | C, A, B60 + the geometry probe | 2898 s | 3 crops |
| `223c7a4065f9` | 1030 | B300, B1000, C2 (seed 7717), Cnb (no motion blur) | 1845 s | 4 crops |
| `584f9935e6dd` + `09e3e961c13d` | 837 | C, B at **N = 1**, and its occlusion grid | 768 + 1571 s | 2 crops |

**f1030**, `RENDER_BORDER` **2123 × 1136 px at full 4K density** (never a reduced
resolution), border `0.4471354167, 1.0, 0.3356481481, 0.8615740741`, 128 samples,
OIDN, the film's own DOF and motion blur untouched. Read back off the built
scene and printed: **AgX / look None / exposure −3.628 / 24.000 fps**, CPU ×32,
seed 0, motion blur ON at shutter 0.500. Ground under the band raycast-confirmed
**`SURF_AccessRoad` / `M_Surf_Concrete`, z = 0.0000**; no object named `Cube`; no
`TDP_` object arrived with the film; `Traffic Passes` re-read off the socket on
every render.

The second f1030 job ran `--probe-grid 0` with the **first job's explicit
border**, so all seven arms are the same 2 412 328 pixels of the same 4K frame.

**Geometry, and why f1030 and not f981.** The deposit's front is at
`front_x = 37.4517`. The band is unoccluded over **x = 24.13 → 35.87 m on +y
(11.74 m)** and **x = 19.00 → 34.62 m on −y (15.62 m)** — against f981's crop,
which was a 1100 × 820 px cross-section. Scale at the band: **4.90–6.08 mm/px
laterally, 7.73–15.61 mm/px along-track**. Focus is 12.27 m at f/4.99 on a
31.92 mm lens, so the circle of confusion over the band's 15.5–22.0 m is
**0.3–0.8 px: defocus is not the limiter**, and that is arithmetic rather than an
assurance.

**Everything below is measured in world metres, not screen pixels.** Each frame
is rectified onto the ground plane through a pinhole **fitted to Blender's own
`world_to_camera_view` output and refused above 0.01 px** — measured residual
**0.00079 px over 56 points**. Measuring along a diagonal streak in screen space
mixes the two axes; this does not.

---

## 1. The mottle's correlation length — and the substrate is NOT isotropic

Control arm, detrended over a 1.00 × 0.50 m window, 5 mm world cells:

| | sd | p95 |dev| | **1/e** | half | first zero |
|---|---:|---:|---:|---:|---:|
| **along x** — the mark's own axis | 7.64 % | 17.18 % | **0.128 m** | 0.102 m | 0.218 m |
| **along y** — across it | | | **0.183 m** | 0.139 m | 0.331 m |

**The concrete decorrelates 1.43× FASTER along the mark than across it**, and
its 2-D power in the 25 mm – 2 m band splits **37.2 % transverse / 46.1 %
diagonal / 16.6 % longitudinal**. The substrate is anisotropic and its
anisotropy runs the *helpful* way: only a sixth of its structure sits in the
channel a tyre mark occupies. **The premise of the hypothesis is confirmed,
and more strongly than it was stated.**

Two confounds were rendered rather than argued away.

* **The denoiser is not making this number.** A second control at a different
  seed (`C2`) differs from `C` by **sd 1.041 %** with correlation lengths
  0.064 / 0.051 m — **13.6 % of the mottle's amplitude and half its scale.**
* **The camera is not doing the matched filtering.** With motion blur off
  (`Cnb`) the mottle measures sd 8.06 % and 0.122 / 0.171 m. Blur at shutter 0.5
  lengthens the along-track correlation by **4.6 %**. It is not the mechanism.

## 2. Along-track integrated SNR — the hypothesis, tested

The estimator is what an observer has: band tone minus a **cubic in y** fitted
to the mark-free concrete on the same side, evaluated at the band centre. **No
control arm is used in the numerator.** The order is calibrated, not chosen —
`(arm − control)` in the band is model-free, so the right order is the one that
reproduces it while leaving the control at zero:

| deg | control bias | A recovered | (A − C) exact |
|---:|---:|---:|---:|
| 2 | −3.34 % | −9.83 % | −6.86 % |
| **3** | **+0.00 %** | **−6.66 %** | **−6.86 %** |
| 5 | +10.01 % | +2.92 % | −6.86 % |

A quadratic leaves 3.3 % of lateral curvature standing **at the band**, which
does not average down with length and reads as a noise floor the substrate does
not have. **The first version of this section had that bug and it manufactured a
null.**

Noise is the s.d. of the same statistic over 21 mark-free band offsets per side
on the control — the substrate pretending to be a line.

**How fast the substrate averages down, +y:**

| L | 0.1 m | 0.5 m | 1 m | 2 m | 3 m | 5 m | 8 m |
|---|---:|---:|---:|---:|---:|---:|---:|
| noise | 6.88 % | 2.85 % | 1.89 % | 1.44 % | 1.41 % | 1.35 % | **1.26 %** |

**Fitted exponent −0.39 (+y) and −0.19 (−y) against √L's −0.5.** Integration
works, and it stops working: from 0.1 m to 8 m the noise falls **5.46×** where
√L predicts 8.94×, and **essentially all of the gain is earned inside the first
2 metres.** The order-of-magnitude estimate that opened this task — l ≈ 0.1 m,
L = 34 m, so ≈ 18× — is **not available on this substrate at this frame.** What
is available is 4–5×.

**SNR against integration length, as delivered:**

| arm | L→0 | 1 m | 2 m | 8 m | 12 m | **L at SNR 3** | **L at SNR 5** |
|---|---:|---:|---:|---:|---:|---:|---:|
| A +y | 0.94 | 2.98 | 3.82 | **4.16** | — | **1.02 m** | **never** |
| A −y | 0.99 | 1.95 | 2.33 | 2.59 | **2.90** | never | never |
| B60 +y | 0.41 | 1.32 | 1.54 | **1.60** | — | never | never |
| B60 −y | 0.97 | 0.86 | 0.80 | 0.87 | 0.77 | never | never |
| B300 +y | 1.52 | 5.57 | 7.26 | **8.21** | — | 0.40 m | **0.85 m** |
| B300 −y | 0.88 | 1.65 | 2.12 | 2.21 | 2.32 | never | never |
| B1000 +y | 2.54 | 9.31 | 12.18 | **13.90** | — | 0.19 m | **0.40 m** |
| B1000 −y | 2.00 | 4.06 | 5.02 | 5.40 | **5.52** | 0.39 m | **1.98 m** |
| **C** the null | 0.33 | 0.64 | 0.43 | 0.28 | 0.27 | never | never |

**Read the first column against the fourth.** Across the mark — which is where
every measurement in this block was taken, R2-1225's included — the existing
paint is **SNR 0.94: below unity, indistinguishable from the concrete.** Along
its own axis it is **4.16**. That factor of 4.4 is the matched filter, it is
real, and it is the reason a 5.7 % wash on a substrate with a 7.6 % mottle is
visible at all. **It is also not enough: A never crosses the Rose criterion.**

**The apron's own dressing is part of the competition and it is bigger than
either mark.** Scattered debris throws ±30 % and up to +60 % excursions
identically in every arm; 13.6 % of the +y columns carry one. Excluding them,
A +y reaches **5.78 at 8 m** and crosses 5 at **L = 6.41 m** — so the honest
statement is *the paint reaches the threshold only on the sunlit track, only
after six metres of integration, and only if you ignore the gravel*.

## 3. Anisotropy — the mark is a line, and at N = 60 it is not

Structure tensor and sector power on the same rectified pixels:

| field | coherence | transverse | diagonal | **longitudinal** |
|---|---:|---:|---:|---:|
| C, the mottle | 0.486 | 37.2 % | 46.1 % | 16.6 % |
| A − C | 0.759 | 1.2 % | 2.0 % | **96.8 %** |
| **B60 − C** | **0.756** | **10.2 %** | **9.2 %** | **80.6 %** |
| B300 − C | 0.877 | 1.8 % | 1.4 % | 96.8 % |
| B1000 − C | **0.924** | 0.9 % | 0.7 % | **98.3 %** |

**Optical thickness is what makes the module's mark a line.** At N = 60 a fifth
of its power is *not* longitudinal; at N = 1000 it is the most strongly oriented
field in the block — more than the paint it replaces.

## 4. Continuity — and this is where N = 60 stops being a mark at all

Fraction of the run at or beyond half the median depth, and the segments it
breaks into:

| arm | side | median | fraction | segments | longest | **sign flips** |
|---|---|---:|---:|---:|---:|---:|
| A | +y | −5.60 % | 1.000 | **1** | 11.75 m | 0 |
| A | −y | −6.62 % | 0.996 | 3 | 14.55 m | 0 |
| **B60** | +y | −2.36 % | 0.961 | **5** | 3.04 m | **8** |
| **B60** | −y | **+2.37 %** | 0.843 | **14** | 6.42 m | **16** |
| B300 | +y | −10.66 % | 1.000 | 1 | 11.75 m | 0 |
| B1000 | +y | −17.80 % | 1.000 | 1 | 11.75 m | 0 |
| B1000 | −y | −13.89 % | 0.999 | 2 | 11.75 m | 0 |

**At N = 60 the two tracks of one mark have OPPOSITE SIGN**: −2.36 % on the
sunlit side and **+2.37 %, i.e. brighter,** on the other. In the ×14 difference
plate one streak is white and the other is blue. That is not a weak mark; it is
the correct rendering of a **gloss-only** film, whose sign is decided by what
each track happens to reflect. **A tyre does not lay one bright stripe and one
dark one.** Fourteen segments and sixteen sign flips is the arithmetic of it:
*a mark broken every 0.5 m is not a mark*, and at N = 60 it is broken every
57 mm.

## 5. The N sweep — and the sign flips the way the substrate says it should

`Traffic Passes` is **per surface**, and on the apron it is the age of the road,
not a dial on visibility. Coverage saturates as 1 − exp(−thickness / 3.1 µm), so
N = 60 is a 636 nm film at ≈ 20 % coverage — gloss with a hint of pigment, which
**cannot be dark at any edge sharpness or any coherence length.**

| N | thickness | +y | −y | character |
|---:|---:|---:|---:|---|
| 60 | 636 nm | −2.36 % | **+2.36 %** | gloss; opposite signs; broken |
| 300 | 3.2 µm | −10.75 % | −5.87 % | dark on both tracks, unbroken |
| 1000 | 10.6 µm | **−17.97 %** | **−14.04 %** | optically thick, unbroken, 0.924 coherent |

At N = 1000 the deposit is **3.2× the existing paint's amplitude** and it is the
only arm that reads at 1:1 without being told where to look. **The sign is the
one predicted**: on concrete (base 0.18–0.30 linear) an optically thick rubber
film is darker; on the deck's conductor it is brighter. Same film, opposite
signs, measured in the same block.

**Black level, per N, as asked.** Pure black on the delivered 8-bit crop, and
the darkest pixel inside the tyre band:

| arm | pure black | frame min | **darkest band pixel** |
|---|---:|---:|---:|
| C | 0.00216 % | 0.000 | 10.202 |
| A | 0.00236 % | 0.000 | 10.202 |
| B60 | 0.00240 % | 0.000 | 9.987 |
| B300 | 0.00261 % | 0.000 | 9.289 |
| B1000 | **0.00294 %** | 0.000 | **10.954** |

**It is not 0.0000 %, and that is a property of the frame, not of any mark** —
the control is already at 0.00216 % because the car and the tyre-wall shadow are
in this crop. The deposit adds **+0.00078 pp at N = 1000**, and the darkest pixel
*inside the band* comes back **brighter** than the control's, because the added
gloss lifts the shadowed end faster than the albedo dims it. **No high-N arm
introduces crushed black.** This is beat 3; R2-082's gate remains a beat-1/2
frame and is still unrun.

---

## 6. THE DECK AT f837 — the patches read, and they read PALE

`Traffic Passes` read back off the built socket: **1.0**, as it must be for a
display turntable. Material `TurntableTop`; ground raycast **`Turntable_Deck` /
`TurntableTop`, z = 0.34000**; `front_x = −0.34085`, which is exactly
`car_x − 1.80` at that frame, so the patches are fully laid and 1.2–1.5 m behind
the rear axle. Crop 1700 × 440 px at 4K density, 512 samples.

**The car's own rear wheel is still in the way at f837, and the first pass of
this measurement did not know it.** Without an occlusion mask the +y patch's
footprint lands on the tyre and reports **+29.71 %** — a photograph of a rubber
tyre, not of a rubber mark. A 2967-point visibility grid raycast from the camera
(`wheel_tyre_RR_Tyre` is the top occluder at 1017 hits) cuts the patch footprint
to **3476 px**, against R2-1216's independent estimate of 3452 px — two methods,
1 % apart.

| region | px | **B − C** | B vs surrounding deck | C vs surrounding deck |
|---|---:|---:|---:|---:|
| **both launch patches** | 3476 | **+9.29 %** | **+62.66 %** | +48.89 % |
| RL (+y, in shadow) | 1060 | **+33.99 %** | | |
| RR (−y, in light) | 2416 | +3.82 % | | |
| tractive film band | 6089 | **+9.44 %** | +34.07 % | +22.56 % |
| bare deck | 15393 | **+0.04 %** | — | — |

**Verdict: yes, they read.** At 1:1 on the delivered pixels the control deck is
a clean smooth gradient and arm B carries an obvious pale streak running out
from under the wheel. It is a **brightening**, which is the sign R2-1214 spent
four sections encouraging the opposite intuition about.

**Three things this adds that no previous number had.**

1. **+9.29 %, not +23.2 %.** The +23.2 % was a synthetic gate. In the film, at
   3° grazing, under the showroom's real lighting and through the shot's own
   motion blur, the patches measure **+9.29 %**. The physics survives; the
   headline number is 2.5× smaller.
2. **The brightening is 9× stronger on the patch that is in shadow** — +33.99 %
   on RL against +3.82 % on RR. A conductor at base 0.048 returns almost nothing
   in shadow, and a dielectric film *adds a diffuse lobe* that picks up bounce.
   The mechanism is not just confirmed, it is confirmed by its own gradient.
3. **Containment on the deck is exact: bare deck moves +0.04 %.** And pure black
   is **0.0000 % on both arms**, with the darkest in-patch pixel going 65.76 →
   75.93, i.e. up.

**The module's hard 12 mm patch edges are still effectively untested.** At
3.5° grazing and shutter 0.5 the patch is ≈ 8 px deep and smeared along the
direction of travel; the edge is below what this frame can resolve. That is a
statement about the shot, not about the module.

---

## 7. What this means for the block

1. **The correction chain ends here, and it ended on the right axis.** R2-1213
   said *too weak*; R2-1219 said *no edge*; R2-1225 said *neither, the substrate
   has more edge than the mark*; this section says **the axis was never the
   problem — the amplitude was, and the amplitude is `Traffic Passes`.** Note
   the shape of it: three corrections in a row each inherited the previous one's
   frame. The one that broke out was the one that changed what was integrated
   over, not what was measured.
2. **Coherence is worth 4.4× and it is not free money.** It buys its factor in
   the first 2 metres and then stops. Anyone reasoning that a 34 m mark gets
   √340 out of its length is wrong by a factor of four on this concrete.
3. **N = 60 is refuted on evidence, not on taste.** It is invisible, it is
   broken into 14 segments, and its two tracks read opposite signs. **N = 300 is
   the floor for a mark that reads; N = 1000 is what "an access road that has
   been run all season" looks like.** That is a continuity decision about how old
   the circuit is and it belongs to the coordinator — but it is now a decision
   with a measured menu rather than an argument.
4. **R2-1225's containment finding survives intact and is joined by a second
   one.** On the deck the deposit moves bare metal by **+0.04 %**. Correctness
   was never the module's problem.

## Cost, and the farm

| | |
|---|---:|
| credit before | **$59.01** |
| credit when the last job of this section landed | **$57.52** |
| farm-wide drop over that window (includes broker 2's own agent) | $1.49 |
| **broker 1's card, billed across this section** | **$0.3123 → $1.5829 = $1.27**, of which an idle share belongs to whoever comes next |
| net attributable to this section | **≈ $1.05 – $1.27** |
| delivered exec time | 2898 + 1845 + 768 + 1571 = **7082 s** |
| paid for and thrown away | ≈ 3400 s (below) |

**Every `rq exec` job ran `cycles.device = CPU`; the flag to do otherwise was
removed from the script rather than defaulted.** Broker 1 only, URL set
explicitly on every invocation including status reads. **Only job ids submitted
by this section were cancelled**, five of them, all mine: two on a bad bundle or
a bad argument, one because a peer established mid-flight that a deck arm at
N = 60 is void, and two because they were contending for the box with each other.
No `pkill`, no broker restart. Broker 2 was read once and left alone; it is
running another agent's `film18_breach` work at depth 6 and is unharmed.

**The expensive lesson, recorded because it cost an hour of a rented card.**
`scene.ray_cast` on the 8 GB film costs **0.527 s per cast** — it walks 5000+
objects. A 36 391-point visibility grid ate a whole 3500 s exec job before it
rendered anything. The grid only has to resolve a **car**, so 0.25 × 0.10 m cells
are ample; the script now **refuses any grid above 12 000 points** and prints its
own elapsed time. The exec timeout is hard-capped at **3600 s** and there is no
flag to raise it.

## Artefacts

    render/r2_1226/raw/r21226_f1030_{C,A,B60,B300,B1000,C2,Cnb}.png
    render/r2_1226/measured_f1030.json      every number in sections 1-5
    render/r2_1226/blacklevel_f1030.json    pure black and band minima per N
    render/r2_1226/along_f1030.png          ACF, SNR-vs-L, noise-vs-L, contrast along x
    render/r2_1226/lateral_f1030.png        the R2-1225 view, for continuity
    render/r2_1226/window_f1030_1to1.png    C | A | B60 | B300 | B1000 at 1:1
    render/r2_1226/diff_f1030_*_x14.png     amplified differences
    render/r2_1226/geometry_f1030_on_C.png  the declared world lines on the control
    render/r2_1226d/raw/r21226_f0837_{C,B}.png
    render/r2_1226d/measured_deck_f0837.json
    render/r2_1226d/deck_{strip,regions,diff}_f0837*.png
    work/r2_1226/long_ab.py      the render harness (CPU-only by construction)
    work/r2_1226/dryrun.py       both grafts proved against the REAL materials, 0 GPU
    work/r2_1226/measure_long.py the longitudinal instrument
    work/r2_1226/measure_deck.py the deck instrument
    work/r2_1226/plates.py       the pictures
