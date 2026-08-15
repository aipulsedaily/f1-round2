# Shared chain + glass breach + non-engine layers

Produced by a diagnosis + design workflow, 2026-08-14, against the
DELIVERED master. Every claim carries the number it was measured from.
Nothing here is inherited from an earlier report -- three previous audio
rebuilds passed all eight gates and were rejected by the client.

---

I have what I need. Every contested claim is now settled against the signal rather than the report.

---

# BUILD SPEC — everything except the engine, plus the shared chain
**Repo:** `~/f1-round2` · **Scope:** all non-engine layers + master chain · **Engine + 8 gates owned by a separate workflow**

---

## 1. IS A SHARED STAGE THE ROOT CAUSE? — YES. Three of them, in series, and they are causally linked.

**Fix these first. Every source rebuild below is worthless until they land.** I re-measured rather than trusting `master_report.json`, because the report is actively lying.

### The measurement that settles it

Summing the 14 stems in `audio/out/stems/` (dumped post-trim, pre-limiter — `master.py:398` `add()`) and dividing the resampled master by that sum recovers the true gain curve:

| window | total chain gain |
|---|---|
| beat 1 quiet (5–30 s) | **+17.21 dB** |
| IMPACT (35.8–36.6 s) | **−14.96 dB** |
| breach (36–44 s) | −9.20 dB |
| lap (50–110 s) | +7.51 dB |

That is a **32.2 dB swing**. `program_gain` is hard-bounded to +7/−3 dB (`master.py:604`), so *at most 10 dB* of it is the program gain. Decomposing: uniform makeup ≈ **+10.2 dB**, therefore the limiter is pulling **≈ −22.2 dB at the impact**.

`master_report.json` reports `limiter.max_gain_reduction_db = −0.124`.

**The report is wrong by 22 dB**, because `master.py:633-641` runs the limiter up to 8 times in a loop and `gr` is reassigned every iteration — only the last, gentlest pass survives into the report. A second 8-pass loop runs at 48 kHz (`gr3`). *One earlier diagnosis declared the limiter "REFUTED" on the strength of that 0.124 figure. That refutation is wrong and must not be carried forward.*

### Why the limiter is doing that — the causal chain

It is not a badly tuned limiter. It is a correct limiter fed an insane signal. Three stages:

**(A) `master.py:365` `warp()` is a varispeed resampler, not a time-stretch.**
`grid.to_film()` → `clock.catmull_rom()` resamples the world-rate buffer onto the film clock. Beat 3 runs world time down to `solved_floor = 0.153719`, so everything warped is **transposed down 6.51× (31.4 semitones)**.

The internal control — same synthesiser, only the clock differs — is decisive. `shards.wav` spectral centroid:

| 41–43 s | 43–44 s | **44.0–45.2 s** (ramp ends) |
|---|---|---|
| 20.5 Hz | 34.8 Hz | **147.9 Hz** |

A 4.25× jump at exactly the ramp boundary, on the same generator. The shard synthesiser declares ring frequencies up to 18.9 kHz; the warp lands the whole field in the infrasonic.

**(B) `master.py:399` `add()` gain-stages every bus on a meter that cannot hear the result.**
`dsp.max_short_term_lufs` is BS.1770 K-weighted. Measured from `dsp._k_weighting(96000)`: **−13.30 dB @ 20 Hz, −23.81 dB @ 10 Hz, −35.42 dB @ 5 Hz.** The `impact` bus over 35.5–44 s measures **+0.82 dBFS unweighted but −13.26 K-weighted — the meter under-reads it by 14.09 dB.** To hit its `TARGET_LUFS_S["impact"] = −6.5` the table applies **+23.64 dB**, and the bus enters the sum at a linear peak of 7.50 (**+17.5 dBFS**).

**(C) The premix therefore peaks at +17.73 dBFS**, of which, over 35.5–44 s:

| <20 Hz | 20–30 | 30–60 | 500–2k | 2–8k | >8k |
|---|---|---|---|---|---|
| **80.23%** | 7.30% | 6.35% | 0.388% | **0.030%** | 0.014% |

**87.5% of the breach's energy is below 30 Hz and inaudible.** The limiter then removes 22 dB — from *everything*, including the 0.03% that is actually the glass. A 30 Hz high-pass on the premix drops RMS 8.71 dB but peak only 0.99 dB, confirming the sub-bass is pure limiter fuel.

### Verdict, plainly

> **The engine and the glass fail together because they share a mix bus whose gain-staging meter is deaf to the frequencies the mix is made of, feeding a limiter that removes up to 22 dB and reports 0.1 dB. Upstream of that, the world-time warp transposes every world-attached source 6.51× down at the exact moment of the breach. No improvement to any synthesiser can survive this chain.**

**Refuted, do not re-spend effort:** clipping (0 samples over, −1.10 dBTP), resampling artefacts (chain reconstructs to −123.7 dBFS), a shared noise seed (stems cross-correlate ≤0.057), film-wide mono collapse (global L/R corr 0.759, side/mid −8.62 dB — the *breach* is near-mono, but that is a symptom of its sub-60 Hz domination, not a separate bug), and reverb wash outside beat 1.

---

## 2. THE GLASS BREACH REBUILD — beat **3**, `3_breach`, **36.0–44.0 s**

> **Scope correction the brief needs:** the brief calls the breach "beat 4". It is not. `docs/beat_sheet.json`: `3_breach` = 36.0–44.0 s; `4_transit` = 44.0–49.6 s (apron/merge arc, no glass). Nose meets pane at `filmtime.GLASS_WORLD_T` → film t = **36.00010 s**, frame 864. Anyone auditioning "beat 4" has been listening to the transit.

### 2.0 The architectural fix that must come first — render shards on the FILM grid

`layers.render_shards` (`layers.py:495`) synthesises modal rings into a **world-rate** buffer, which `warp()` then resamples. **Stop doing that.**

Change the contract: `render_shards` takes the clock and, per contact event, maps world time → film time (`clock.film_at_world`) for the **event onset only**, then synthesises the modal decay in **film-rate samples at the true ring frequency**. Slow motion then stretches the *shower* — events spread out, exactly as intended — while every shard still rings at its physical pitch. This is one change and it is worth more than everything else in this section. Same treatment for `impact_event`.

*(Note: real slow-motion sound design never varispeeds debris 6.5× down. It re-times the event schedule and leaves the objects sounding like objects.)*

### 2.1 The pane — `layers.plate_modes` / `layers.glass_wall`

Four defects, all parametric:

| # | Defect | Now | Set to |
|---|---|---|---|
| 1 | `fmax` | `1600.0` | **18000.0** |
| 2 | `m,n` loop range | `range(1,26)` | **m→56, n→140** |
| 3 | `q` | `45.0` | **frequency-dependent, see below** |
| 4 | `keep` | `72` | **400** |

Defects 1+2 together are the big one. `glass_wall` correctly weights modes by radiation efficiency `min(1,(f/f_c)²)` with **f_c = 1004 Hz** — then selects from a mode set that *stops just above f_c*. With `m,n ≤ 25` the ceiling is 4718 Hz regardless of `fmax`. **The entire band where a 12 mm pane actually radiates — 1 kHz to 20 kHz — is never generated.**

Modal density is analytic and constant: `D = E h³/(12(1−ν²)) = 10800 N·m`, `ρh = 30`, `k = (π/2)√(D/ρh) = 29.80`, so **dN/df = πab/(4k) = 0.314 modes/Hz** → 502 modes below 1600 Hz, **6272 below 20 kHz**. Keeping 400 of ~6300 by `(coupling × radiation)` weight is ~400 biquads over a gated 36 s window — trivial offline.

**Damping.** `q=45` is a loss factor η = 1/Q = **0.022** — that is plastic, not glass. The pane is rendered ~22× too dead. Use, with the edge-clamped mullion frame accounted for:

- **f < 500 Hz: Q = 400** (boundary/joint-dominated)
- **f 500–2000 Hz: Q ramp 400 → 1000**
- **f > 2000 Hz: Q = 1200** (material-dominated, annealed soda-lime η ≈ 1e-3)

At 3 kHz this takes T60 from 0.033 s to **0.73 s**. The frequency-dependent Q is itself a strong material cue.

**Coupling.** Keep the existing odd-odd `1/(mn)` rule for the *acoustic pre-load* from the approaching car (uniform pressure). But the nose is a **point load** — for the strike, use `sin(mπx₀/a)·sin(nπy₀/b)` at the impact point, which couples to every mode.

### 2.2 The shards — `layers.shard_ballistics` / `layers.render_shards`

**Defect A — amplitude is inversely proportional to pitch.** `layers.py:425` `m = GLASS_RHO*GLASS_H*L*L` (= 30L²) and `:465` `amp = m*vz_in`, while `:450` `f1 = 0.47*(GLASS_H/L²)*GLASS_CL` (= 30.59/L²). Therefore **amp = 917.7·vz/f1**. Big slabs are loud and low; bright chips are silent. Measured consequence: the top 10 contacts carry 32.1% of all shard energy and **all ten ring at 54.4 Hz** (the L=0.75 m clamp).

**Fix:** multiply each mode by the radiation efficiency the same file already computes and then declines to use here — `_rad(f) = min(1,(f/f_c)²)`, f_c = 1004 Hz. Additionally apply the per-shard size high-pass at `f = c/(2πa) = 109.2/L` Hz (ka=1), first order. A 54 Hz contact drops **25.4 dB**; small shards become naturally bright. This makes the size↔brightness relationship physical rather than authored.

**Defect B — three pure sines, zero noise.** `layers.py:518-522`: ratios `1 : 2.08 : 3.41`, one shared exponential decay, plus a 0.4 ms DC bump. That is the textbook definition of a struck bar — **this is literally the client's "banging on tubes"**. Rebuild:

- **8–14 modes per shard**, not 3. (Zheng & James shipped ~13 modes/piece for a glass table; that is the published bar.)
- **Per-shard mode ratios.** Draw aspect ratio `r ~ lognormal(0, 0.35)`, use free-plate `f_mn` for sides `L√r, L/√r`; jitter each ratio by `lognormal(0, 0.08)`. No two shards may share a spectrum. Free square plate reference ratios: `1 : 1.47 : 1.81 : 2.60 : 2.60 : 4.56`.
- **Per-mode decay.** Replace the single `decay` with `τ_n = Q/(π f_n)`, Q = 800–1500. Frequency-proportional damping is the cue listeners use to identify material. Currently all modes share one decay capped at 0.45 s and scaled *linearly* in L, which is wrong twice over (τ should ∝ L²).
- **Replace the 0.4 ms DC bump** with a proper acceleration-noise transient: `d/dt` of the contact force, band-limited, scaled by `m·Δv`. The current bump has energy at DC — it is a click, not a transient.

**Defect C — silent shards.** `render_shards` skips any mode with `f >= sr*0.45` (43.2 kHz at 96 k). Solving `30.59/L² = 43200` → **every shard smaller than L = 26.6 mm renders as pure silence**, and `shard_ballistics` draws L from 0.015 m with small sizes concentrated at the impact point. The fine debris that carries the actual "glass" percept is being dropped on the floor. **Fix:** render sub-26.6 mm shards as a filtered noise burst centred where the mode would be (above ~16 kHz it is a spectral tilt, not a pitch), *or* raise internal rate to 192 kHz for this layer and decimate. Add an assertion: every event in the summary dict must produce non-zero output.

**Defect D — event density.** `master_report.json` breach_sim: 351 shards, 995 contacts over 3.148 s = 316 events/s generated. Measured onsets in the delivered 1–4 kHz band: **5–13.5/s**. A 25–60× shortfall, entirely caused by §1. Auditory fusion into a continuous texture needs >20–30 events/s; the peak of the shower should be **several hundred/s** decaying to a sparse tail where individual tinkles are wanted.

**Fragment count — make this choice explicitly.** Current code gives 185 pieces/m² over 11.9 m², which is a *laminated/annealed* answer (power-law size distribution). Architectural showroom glazing would realistically be toughened, which fragments *exponentially* with ~10⁴ pieces/m². Recommendation: **model it as laminated** (matches the visual breach and the 351-shard sim the film already renders) and get density from the PhISEM bed below rather than by inflating shard count.

### 2.3 Layering for the breach — 5 layers, physically time-aligned

Define t=0 as contact. Offset each layer by its *physical* propagation delay (r/c), not by taste.

| layer | content | timing | band |
|---|---|---|---|
| **1. Fracture rip** | crack impulses scattered across the crack-front sweep | **not instantaneous** — crack tip ≈ 0.5–0.6 c_R ≈ **1750 m/s**; 2.125 m short span = **1.21 ms**, 5.6 m span = **3.2 ms**. Scatter impulses by distance/1750. | 3–7 kHz core (documented glass-shatter band) |
| **2. Pane modal collapse** | §2.1 bank, excited by point load, gated off ~40 ms after contact | 0–40 ms | 1–18 kHz |
| **3. Delayed flexural** | damped low waveform — a real, distinctive, currently **absent** feature of glass breakage | **+50–100 ms** | ~200 Hz |
| **4. Shard shower** | §2.2 modal events, film-grid scheduled | 0–8 s, density-decaying | 500 Hz–18 kHz |
| **5. PhISEM debris bed** | the thousands of sub-cm pieces you should not integrate individually | 0–8 s | res 3–8 kHz, Q 20–60, τ_sys 0.4–1.5 s, peak rate 300–2000 ev/s |

Cross-fade layer 4↔5 by shard size (foreground = largest ~200 shards). This also closes the sub-26.6 mm hole from the other direction. Add a low-amplitude scrape/skitter continuation for the last 0.3–1.5 s of each shard's life — real debris slides after it bounces; the current field stops dead.

**Excitation model** for every impact in the film (replaces bare impulses): Hertzian half-cosine `F(t) = F_max(1 − cos(2πt/T))`. T is the physical hardness knob, and it sets the excitation cut-off at ~1/T:
- glass-on-glass / shard-on-concrete: **T = 0.05–0.3 ms**
- carbon panel on carbon: T = 0.3–1 ms
- rubber tyre on kerb: T = 3–15 ms

**Sub layer:** the current `impact_event` thud (41/58/79 Hz sines, `layers.py:553`) can stay as the *felt weight*, but it must be level-matched **after** the master chain is fixed, and high-passed at 30 Hz. Right now it is 87% of the beat.

---

## 3. EVERY OTHER NON-ENGINE SOUND

### 3.1 The generator monoculture — the "wind blower" percept

Census of `layers.py`: **24 noise-generator call sites** (`dsp.white/pink/brown`) and **16 `np.sin` sites**, and *nothing else*. Every one of the 12 non-engine layers is either (a) band-filtered Gaussian noise or (b) a sum of exponentially-decaying sines. `dsp.comb_pipe` and `dsp.blowdown_pulse` are called **only** from `engine.py`. No waveguide, no nonlinearity, no contact model, no self-excited oscillator exists outside the engine.

**The client's two complaints are the project's two generators.** Median 50 ms crest factor across the film is **9.70 dB — below Gaussian white noise** (~10.9 dB). Nothing in 124 seconds has the local peak structure of a real physical event.

Every item below must introduce a **third mechanism**. Filtering noise differently is not a fix.

### 3.2 Rebuilds

**`tyres()` (`layers.py:32`) — replace filtered noise with a self-excited oscillator.**
Real squeal is stick-slip, not noise. Implement Coulomb friction with velocity weakening — `μ(v) = μ_k + (μ_s−μ_k)·exp(−|v_slip|/v_c)`, μ_s/μ_k = 1.2–1.6, v_c = 0.05–0.3 m/s — driving a mass-spring tread element, and let it limit-cycle. The output is naturally a sawtooth-ish relaxation oscillation with strong harmonics, which is what squeal *is* and why noise never sounds right.
- Squeal centre **600–900 Hz, driven by slip ratio and normal load, NOT road speed.** Glide it: measured real braking events rise ~670 → 850 Hz across the stop.
- **Add tyre cavity resonance — currently absent and highly characteristic.** 18" F1 wheel: mean radius 0.2945 m, circumference 1.850 m → **f₁ = 343/1.850 = 185 Hz**, plus 2f₁, 3f₁. Under load the mode **splits** into fore-aft and vertical a few Hz apart → slow beating. Reproduce the split; it is the giveaway.
- **F1 tyres are slicks: do NOT add tread-block passing tonality.**

**`wind_at_camera()` (`layers.py:140`) — it is the loudest thing in the lap and it is pure brown+pink noise.**
Two fixes:
1. **Split into ≥2 sources with different velocity exponents.** Dipole (edges, wings, mirrors) scales `U⁶`; quadrupole (underbody/wake) scales `U⁸`. From 100→300 km/h the dipole rises 28.6 dB and the quadrupole 38.2 dB — **the wake layer must overtake the edge layer at speed.** One noise source with one gain curve reads as a fader move, not as speed.
2. **Spectral centroid must track U.** Strouhal `f = 0.2·U/d`. At 80 m/s: sidepod edge (d=0.15 m) → 107 Hz; mirror stalk (0.05) → 320 Hz; winglet (0.02) → 800 Hz; trailing edge (0.005) → 3.2 kHz. All scale **linearly** with speed.
3. Use **Goody's wall-pressure spectrum** shape (ω² rise, ω^−0.7 overlap, ω^−5 roll-off) instead of pink/brown. Add slow large-eddy AM at `U/(5δ)` ≈ 2–20 Hz, depth 3–6 dB, or the wind sits still.

**`showroom_tail()` (`layers.py:198`) — the "The Tubes over and over" percept.**
Over 0–33 s the reverb bus and the dry bus it is the reverb *of* are within **0.07 dB** of each other. `TARGET_LUFS_S` sets `room = −23.0` while `assembly = −27.0` — **the wet is declared 4 dB above the dry.** Worse, the reverberant field is spectrally *identical* to the direct sound (wet−dry tilt flat to ±1.1 dB across 125 Hz–16 kHz, and the reverb is actually *louder* at 4–8 kHz). A real room's tail must be darker — air absorption plus surface absorption.
- **Set `room` to −31.0 LUFS-S** (≈4 dB *below* the assembly bus).
- Apply frequency-dependent decay so RT60 falls with frequency: keep 2.4 s low but take **HF to 0.35 s above 4 kHz** (currently 0.85 s flat-ish and undamped).
- Beat 1 attacks measure 23–42 ms rise times versus 0–8 ms inside the breach — that smearing is the reverb, not a compressor.

**`assembly()` (`layers.py:344`) — 4 sines at `1 : 2.31 : 3.87 : 6.1`.**
Every part seat in beat 1 is the same 4-sine bank transposed. Give each cluster its **own** mode set derived from its actual geometry (beam ratios `1 : 2.756 : 5.404` for extrusions, plate ratios for panels), per-mode `τ_n = Q/(πf_n)` with **η = 5e-3–2e-2 (Q 50–200) for bolted/joint-dominated assemblies** regardless of base material, and drive them with Hertzian contact forces of the right T rather than impulses.

**Carbon vs metal — three numbers, all audible:** CFRP η is 30–300× higher than aluminium (ring dies in tens of ms, not seconds); specific stiffness `√(E/ρ)` is *comparable or higher* (~8000–9000 m/s vs 5055), so **carbon is not lower in pitch, it is shorter in time**; orthotropy splits degenerate mode pairs → slow beating over the first 20–50 ms. Synthesise all three.

**`impact_event()` mullion (`layers.py:565`)** — the physics is sound (free-free beam, f₁ = 31.6 Hz, β = 4.730/7.853/10.996/14.137, implied Q = 89 which is correctly joint-dominated). **Keep it.** One fix: higher modes must decay by the same η, not by the ad-hoc `1/(k+1)^0.6`.

### 3.3 Four sound families that do not exist anywhere in the codebase

Grep for brake/damper/suspension/shift/gear/kerb across `audio/*.py` returns nothing outside `engine.gear_and_rpm`. **Beat 6 is an 11.0 s deceleration from 83.1 m/s to zero with no braking sound available to it.** Build:

1. **Brakes** — carbon-carbon disc: rubbing tone 1.5–4 kHz modulated by disc rotation rate, plus low-Q judder at wheel-rotation harmonics. Gate on the telemetry's decel. **Required for beat 6 and every corner in the lap.**
2. **Suspension / dampers / kerb strikes** — two-stage: rubber-mediated contact (T = 3–15 ms → low thump, rolls off above ~100 Hz) followed by structure-borne ring of upright/wishbone at beam modes 100 Hz–2 kHz, η ≈ 1e-2. Heavily damped 1.5–4 Hz body mode modulates the tyre-load-dependent layers.
3. **Downshift / gearshift transient** — *interfaces with the engine workflow*; see §6 note.
4. **Continuous contact / scrape** — synthesise a spatial roughness profile with power-law spectrum `S(k) ∝ k^−w`, w ≈ 2.2 asphalt / 2.5 glass-on-concrete, and read it at `f = v·k`. Speed then changes pitch *and* brightness for free, with no resampling artefact. Feed it through the sliding object's modal bank.

### 3.4 Buses that are inaudible or buried — decide, don't leave them

Measured against the sum of all other buses: `structure` best −14 dB, `fence` best −15 dB, `reflect_showroom` best −25 dB, `aperture` best −28 dB. **`aperture` and `reflect_showroom` are 25+ dB under the mix everywhere and cost full render time.** Either raise them into audibility with intent or delete them; do not ship buses that exist only in the report.

### 3.5 The film-wide top-end deficit

Whole-film band RMS: 1–2 kHz −25.5 dBFS, 4–8 kHz −39.8, 8–12 kHz −51.1, 12–16 kHz −58.1. That is **14.3 dB down at 4–8 kHz and 25.6 dB down at 8–12 kHz** relative to 1–2 kHz. Part is the declared `BUS_HF_SHELF` of **−12 dB @ 2 kHz on wind, tyres and bed**. **Remove that shelf entirely** — it was a patch for wind being too loud, and the correct fix is the −23.0 LUFS trim that is already in place plus §3.2's rebuild. The rest is ISO 9613 air absorption (legitimate) and dark sources (fixed above).

---

## 4. THE MASTER CHAIN AS IT SHOULD BE

`audio/master.py`. Ordered. **Bold = must remove or replace.**

### 4.1 Remove

1. **The 8-pass limiter loop (`master.py:633-641`) — delete the loop.** One limiter pass, one ceiling, gain reduction *reported honestly*. If one pass cannot hit −14 LUFS without >3 dB of reduction, **the mix is wrong and the build must fail**, not iterate until it stops complaining.
2. **The second 8-pass 48 kHz loop (`gr3`)** — replace with a single true-peak-safe pass.
3. **`dsp.soft_limit`'s 240 ms gain hold (`dsp.py:446-453`).** `minimum_filter1d(need, size=2*rel+1)` with `release_ms=120` pins gain to the minimum over ±120 ms, then `sosfiltfilt` — **zero-phase, so it also ducks BEFORE the peak.** Every transient digs a 240 ms hole in everything around it. Replace with a causal one-pole release, **release 30–60 ms**, lookahead ≤1 ms, and no `filtfilt` anywhere in a gain path.
4. **`BUS_HF_SHELF`** — delete all three entries (§3.5).
5. **The `warp()` call on `imp_f` and `shard_f`** — superseded by film-grid rendering (§2.0).

### 4.2 Replace

6. **Gain staging must not be K-weighted-only.** Replace the single `dsp.max_short_term_lufs` trim in `add()` with a **dual criterion**: trim to the LUFS-S target *and* assert the bus's resulting linear peak is ≤ 1.0. Any bus needing >12 dB of trim in either direction is a **build failure**, not a rescue. Current trims: `structure +52.39`, `shards −46.12`, `fence +35.62`, `impact +23.64`, `engine +24.99` — every one of those is a source-level bug being papered over by one broadband number.
7. **Trim on a representative window, not each bus's single loudest 3 s.** Keying every bus to its own peak moment normalises them all to the same target and flattens the film's internal relief.
8. **Add a 30 Hz 4th-order high-pass before the program gain.** The only current low cut is a 12 Hz DC block (`master.py:626`). Measured effect at the breach: RMS −8.71 dB, peak only −0.99 dB; recovers **+2.4 to +5.6 dB of audible-band (120 Hz–8 kHz) programme** across 36–42 s and roughly halves the limiter's work. Sub-30 Hz is 85.1% of the whole film's energy and nobody can hear it.
9. **Air absorption as a single minimum-phase filter**, not `split_bands` + sum. The split is numerically exact, but band-splitting and re-summing smears a 0.5 ms transient. For impact material this matters.

### 4.3 Keep

- `program_gain` at 6 s/12 s, +7/−3 dB. Measured range 10.25 dB — genuinely slow, genuinely bounded, **not** the crusher. The docstring's reasoning is correct.
- The 96 kHz internal rate and the `resample_poly` kaiser-12 downsample. Verified transparent.
- The 12 ms tail fade and the DC block.

### 4.4 Targets

| quantity | target |
|---|---|
| LUFS-I | −14.0 |
| True peak | ≤ −1.0 dBTP |
| **Limiter max GR, whole film** | **≤ 3.0 dB — and reported as the max over all passes** |
| Premix peak before master chain | **≤ +6 dBFS** (currently +17.73) |
| LRA | 12–16 LU |
| Breach (36–44 s) energy >4 kHz | **≥ 8%** (currently 0.006%) |
| Breach spectral centroid | **≥ 1200 Hz** (currently 54.8 Hz) |
| Breach 50 ms crest | **≥ 18 dB** (currently 9.24 dB) |

---

## 5. ACCEPTANCE TEST

A listener has to agree, so the test is anchored to what a listener would say. Every gate ships with a **degenerate control that MUST fail** — matching this project's existing discipline of never trusting a check that has not been seen to fail.

### 5.1 Listening test (the actual bar)

Blind A/B, 5 naive listeners, current master vs rebuild. Present three clips: 0–33 s, 36–44 s, 60–70 s. Ask exactly the client's questions:
1. "Does this sound like a hair dryer or a wind blower?" — **≤1 of 5 may say yes** (currently the stated verdict).
2. "Does anything sound like banging on tubes?" — **0 of 5** on the 0–33 s clip.
3. "Is that glass breaking?" — **≥4 of 5 unprompted yes** on the 36–44 s clip.

### 5.2 Measured gates

| # | Gate | Threshold | Degenerate control that MUST fail |
|---|---|---|---|
| G1 | Limiter GR, max over **all** passes | ≤ 3.0 dB | Restore the 8-pass loop → must report >20 dB, not 0.124 |
| G2 | Breach energy >4 kHz | ≥ 8% | Current master → 0.006%, fail |
| G3 | Breach spectral centroid | ≥ 1200 Hz | Re-enable `warp()` on shards → 54.8 Hz, fail |
| G4 | Breach 50 ms crest | ≥ 18 dB | Feed a 0.2 ms click of known crest through the chain; crest loss must be ≤3 dB |
| G5 | Onset rise, breach, 10–90% | ≤ 2 ms | Zero-phase limiter restored → must fail |
| G6 | Shard event density, 1–4 kHz onsets, peak | ≥ 150/s | Current master → 13.5/s, fail |
| G7 | **Silent-content check** | every event in the sim summary produces non-zero output | Set `fmax` back to 43.2 kHz threshold → sub-26.6 mm shards silent, fail |
| G8 | Modal density of pane response | 0.314 ±25% modes/Hz | `fmax=1600` → ~0.05, fail |
| G9 | Size↔frequency regression across shard population | `log f₁` vs `log L` slope = **−2.0 ±0.1** | Any authored frequency table → fail |
| G10 | Per-mode Q of a rendered single shard | 500–2000 | `q=45` → 45, fail |
| G11 | Wet/dry ratio, beat 1 | dry ≥ 4 dB above wet | Current (`room −23`/`assembly −27`) → −0.07 dB, fail |
| G12 | Reverb spectral tilt, wet−dry, 4–8 kHz vs 250–500 Hz | ≤ −6 dB (tail must be darker) | Current → +1.3 dB, fail |
| G13 | Median 50 ms crest, whole film | **> 11.0 dB** (must beat Gaussian noise) | White noise fed through chain → 10.9 dB, fail |
| G14 | Premix peak pre-master | ≤ +6 dBFS | Current → +17.73, fail |
| G15 | Any bus trim magnitude | ≤ 12 dB | Current `structure` +52.39 → fail |
| G16 | Wind level vs speed | dipole and quadrupole components fit U⁶/U⁸ within ±3 dB over 100–300 km/h | Single-source noise bed → fail |
| G17 | Energy budget | shard radiated energy < impact radiated energy | Current (shards peak +8.52 dBFS) → fail |

**G13 is the single most diagnostic gate in the set.** If the film's median crest factor is below white noise, it is statistically noise, and no listener will call it a car.

---

## 6. INTERFACE WITH THE ENGINE WORKFLOW

- **The shared chain is mine; the engine source is theirs.** §4's changes to `master.py` and `dsp.soft_limit` affect the engine bus identically. The engine workflow must **not** independently re-tune `TARGET_LUFS_S["engine"]` (currently −10.0, trim +24.99 dB) until §4 lands — with a fixed chain the engine will need re-levelling from scratch, and doing it twice wastes the pass.
- **`warp()` applies to `eng_f` and `tyre_f` too.** The engine is transposed 6.51× down at the breach by the same stage. §2.0's film-grid rendering must be applied to the engine's world-attached layers as well — **that is a joint change to `master.py:365`, and whoever lands it second must not revert the first.**
- **Downshift/gearshift (§3.3 item 3)** belongs to the engine workflow's `gear_and_rpm`. I am flagging it, not building it.
- The lap's masking problem (`wind` is the only non-engine element that ever rises above the mix, median −1 dB, best +14 dB) is **jointly owned** — my §3.2 wind rebuild plus their engine work.

---

## 7. WHAT WOULD MAKE ME ABANDON THIS APPROACH

Stated in advance, with the measurement that would trigger each:

1. **If fixing the chain alone (§4, no source changes) does not measurably move the breach.** Land §4 first, re-render, re-measure G2/G3/G4. If breach energy >4 kHz stays below ~1% and crest stays under 12 dB, then the chain was *not* the dominant cause, my §1 verdict is wrong, and the effort should move entirely to sources. **This is the cheapest test in the plan and it must be run first, before any source work.**
2. **If G13 (median crest > 11.0 dB) cannot be reached** after both chain and source rebuilds, the problem is architectural — everything is still noise-derived — and the answer is to abandon incremental repair of `layers.py` and rebuild it on a genuine modal/contact-force engine from scratch.
3. **If the listening test in §5.1 still returns "wind blower" from ≥3 of 5** after all gates pass, then the gates measure the wrong quantities and the whole measurement framework must be rebuilt against listener response rather than physics invariants. Physics invariants are a *proxy*; the client is the ground truth.
4. **If the 400-mode pane and 8–14-mode shards push render time past ~4× current.** The budget is generous (a month is acceptable) but not unbounded; if it blows up, drop to the PhISEM bed for everything below the largest 200 shards and accept the foreground/background split as the permanent architecture rather than an optimisation.
5. **If `warp()` cannot be removed** because some downstream consumer depends on world-grid rendering in a way I have not found. In that case the fallback is to warp *only* sustained sources (engine, tyres, wind) and render all transient sources (impact, shards, structure, assembly) directly on the film grid — a partial fix, and I would say so rather than claim the defect closed.

---

**Files this spec touches:** `audio/master.py` (lines 365, 399-422, 521-535, 604, 626, 633-641, plus `TARGET_LUFS_S` and `BUS_HF_SHELF` tables) · `audio/dsp.py` (lines 446-453 `soft_limit`) · `audio/layers.py` (lines 32 `tyres`, 140 `wind_at_camera`, 198 `showroom_tail`, 285 `plate_modes`, 307 `glass_wall`, 344 `assembly`, 396 `shard_ballistics`, 495 `render_shards`, 534 `impact_event`) · `audio/clock.py` (line 202 `to_film`) · new layers for brakes, suspension/kerb, and scrape.

---

# SUPPORTING DIAGNOSIS (measured)

```json
[
 {
  "findings": [
   {
    "claim": "THE SHARED STAGE IS THE TWO-EAR PROPAGATION MODEL, NOT THE DYNAMICS CHAIN. Every direct (propagated point-source) bus is rendered near-mono. The only width in the film comes from reverb and noise beds. This hits the engine and the glass identically, which is exactly the shared-cause signature the hypothesis predicted \u2014 just in a different stage.",
    "measurement": "Per-bus L/R correlation on the stems: impact 0.996, shards 0.996, assembly 0.944, structure 0.932, fence 0.850, wind 0.865, tyres 0.785, engine 0.732 \u2014 versus crowd 0.027 and bed 0.189 (the only genuinely wide buses). Ear separation 0.175 m (master_report.json /camera/ear_separation_m). Master global corr 0.759, side/mid \u22128.62 dB.",
    "severity": "significant"
   },
   {
    "claim": "THE GLASS BREACH IS EFFECTIVELY MONO AT THE ONE MOMENT THAT MATTERS. Beat 4 in the brief = '3_breach' in docs/beat_sheet.json, 36.0\u201344.0 s (8.0 s, world-time ramp frames 865\u20131056), impact onset measured at 36.0\u201336.2 s. A glass wall exploding around the camera is delivered as a single mono point.",
    "measurement": "Master over 36\u201344 s: L/R correlation 0.993 (median 0.5 s) / 0.987 (whole beat), side/mid \u221224.29 dB = 6% side energy. Source stems: impact side/mid \u221226.10 dB, shards \u221226.51 dB, both corr 0.996. Compare the rest of the film: beat 1 corr 0.502, beat 4 transit 0.677, beat 5 lap 0.717, beat 6 ending 0.268.",
    "severity": "ruins-everything"
   },
   {
    "claim": "THE GLASS HAS NO GLASS IN IT. The breach is a sub-bass thud with its spectrum inverted ~40 dB from what breaking glass is. Real glass fracture energy lives 2\u201312 kHz; this is 87% below 100 Hz. This is literally 'the sound even glass breaking is awful'.",
    "measurement": "Master 36\u201344 s: spectral centroid 58 Hz. Energy fractions <100 Hz 87.4%, 100\u2013500 Hz 10.1%, 0.5\u20132 kHz 0.9%, 2\u20136 kHz 0.0%, >6 kHz 0.00%. Absolute band RMS: 20\u201350 Hz \u221215.8 dBFS vs 4\u20138 kHz \u221256.9 dBFS = 41.1 dB inverted. At the impact peak (40.6\u201341.2 s) centroid is 57 Hz. It is at the SOURCE, not the chain: the impact stem itself peaks at 20\u201350 Hz (\u221211.0 dBFS) and falls to \u221260.8 dBFS at 4\u20138 kHz; shards stem \u221211.3 dBFS at 20\u201350 Hz vs \u221255.2 dBFS at 4\u20138 kHz.",
    "severity": "ruins-everything"
   },
   {
    "claim": "THE FIRST 33 SECONDS ARE HALF REVERB, AND THE REVERB IS NOT A ROOM. Wet/dry is 1:1 and the reverberant field is spectrally IDENTICAL to the direct sound \u2014 a real room's reverb must be darker (air absorption + surface absorption). A full-bandwidth, undamped ~1.1 s tail at equal amplitude on every assembly clunk is precisely the percept 'the instrument The Tubes over and over' / 'banging on tubes'.",
    "measurement": "Beat 1 (0\u201333 s) energy share: assembly (dry) 46.7%, room (reverb) 45.9%. Wet/dry ratio \u22120.07 dB. Decay from the loudest dry hit (t=15.554 s): \u221210 dB at 4 ms, \u221220 dB at 218 ms, \u221230 dB at 555 ms \u2192 RT60 \u2248 1.11 s. Wet-minus-dry spectral tilt over 5\u201330 s: 125\u2013250 Hz \u22120.5 dB, 250\u2013500 +1.0, 500\u20131k \u22121.0, 1\u20132k \u22120.7, 2\u20134k \u22121.1, 4\u20138k +0.3, 8\u201316k \u22120.1 \u2014 flat to \u00b11.1 dB, and the reverb is LOUDER than the dry at 4\u20138 kHz. Mix table sets room to \u221223.0 LUFS-S while the assembly bus it is the reverb of is set to \u221227.0 (audio/master.py target table).",
    "severity": "ruins-everything"
   },
   {
    "claim": "THE WHOLE FILM IS DARK. A shared top-end deficit across every bus is why nothing sounds like a real object. Part is a declared \u221212 dB @ 2 kHz shelf on three buses (wind/tyres/bed, master.py BUS_HF_SHELF), part is ISO 9613 air absorption, part is the sources themselves \u2014 but the client hears it as one thing.",
    "measurement": "Whole-film band RMS: 1\u20132 kHz \u221225.5 dBFS, 2\u20134 kHz \u221231.7, 4\u20138 kHz \u221239.8, 8\u201312 kHz \u221251.1, 12\u201316 kHz \u221258.1 dBFS. That is 14.3 dB down at 4\u20138 kHz and 25.6 dB down at 8\u201312 kHz relative to 1\u20132 kHz. Per-stem band-energy rolloff above 1 kHz: engine \u221210.4 dB/oct, tyres \u22129.3, bed \u22128.6, wind \u22127.9, shards \u22126.9.",
    "severity": "significant"
   },
   {
    "claim": "THE FILM IS STATISTICALLY NOISE, EVERYWHERE. Median 50 ms crest factor is BELOW Gaussian white noise (~10.9 dB for a 2400-sample window). Nothing in 124 seconds has the local peak structure of a real physical event. This is the 'wind blower' / 'hair blower' percept and it is a design-level shared cause: almost every layer is band-filtered Gaussian noise from dsp.white/pink/brown.",
    "measurement": "50 ms crest across the film: p1 5.92, p10 7.91, p50 9.70, p90 11.10, p99 12.38, max 15.75 dB. Energy that originates as band-filtered Gaussian noise (wind+bed+crowd+tyres+fence+room): beat 6 ending 83.2%, beat 1 assembly 47.3%, beat 5 lap 46.2%, beat 4 transit 16.8%.",
    "severity": "significant"
   },
   {
    "claim": "TRANSIENTS SURVIVE \u2014 the 'limiter destroying attacks' hypothesis is REFUTED. The breach has genuinely fast attacks. Where attacks ARE slow is beat 1, and that is the reverb smearing them, not a compressor.",
    "measurement": "Top-15 attack events (1 ms envelope, rise vs preceding 50 ms). Inside the breach: 10\u201390% rise times of 2, 3, 0, 6, 38, 47, 8 ms with rises of 22.3\u201328.7 dB; peak HF (4\u201318 kHz) rise 41.31 dB at t=40.686 s. Inside beat 1: 39, 42, 37, 37, 28, 23, 23 ms. Limiter max gain reduction across the whole film 0.124 dB; program gain range 10.25 dB (\u22123.12 to +7.13) over 6 s / 12 s constants.",
    "severity": "minor"
   },
   {
    "claim": "THE MASTER BUS IS CLEAN. No clipping, no intersample overs, no flat-topping, no squash, no resampling artefacts. Delivery-spec compliant. Nothing in the mastering chain is causing the client's complaint \u2014 this candidate is refuted outright.",
    "measurement": "Sample peak \u22121.100 dBFS both channels; 0 samples |x|\u22651.0, \u22650.999, \u22650.99, \u22650.9772; longest flat-top run 0 samples on both channels. True peak \u22121.097 dBTP (8x oversample), 0 intersample overs. LUFS-I \u221214.00, LRA 13.06 LU, short-term p10 \u221223.84 / p95 \u221210.79 LUFS, momentary p1\u2013p99 range 17.83 LU. Per-beat crest 18.24 / 13.54 / 9.26 / 14.20 / 15.09 / 19.61 dB. 20\u201324 kHz band content \u221273 to \u221281 dBFS (no aliasing images). Seeds are distinct per layer (808/4242/97/311/5150/771/1234/31337/606/20260802) so there is no shared noise stream either.",
    "severity": "null"
   },
   {
    "claim": "THE SAME DEFECTS ARE PRESENT, UNCHANGED, IN BOTH MASTERS THE CLIENT ALREADY REJECTED. Three rebuild attempts moved the sources and never once moved the breach's stereo image or its spectrum. This is the proof that no amount of better sources will fix it.",
    "measurement": "Across master.wav (shipped), master_R2-1400_REJECTED_hairblower.wav, master_R2-2001_REJECTED_tubes.wav and master_SHIPPED_aug2.wav: breach L/R correlation 0.987 / 0.987 / 0.987 / 0.987; breach energy >4 kHz 0.00% / 0.00% / 0.00% / 0.00%; LUFS-I \u221214.00 / \u221214.02 / \u221214.01 / \u221214.02; true peak \u22121.11 / \u22121.18 / \u22121.15 / \u22121.15 dBTP; median 50 ms crest 9.70 / 9.39 / 9.57 / 9.43 dB.",
    "severity": "ruins-everything"
   },
   {
    "claim": "THE NOISE FLOOR NEVER FALLS DURING THE BREACH OR THE TRANSIT \u2014 8 seconds of a car destroying a glass wall has less level relief than a sustained tone. This is the smear, and it comes from the reverb/reflection buses plus the 351-mode shard bed running continuously.",
    "measurement": "20 ms RMS span (p99.9 minus p2) per beat: beat 1 assembly 24.18 dB, beat 2 launch 18.50, beat 3 BREACH 14.19, beat 4 transit 8.61, beat 5 lap 18.47, beat 6 ending 15.04. Breach floor never drops below \u221218.56 dBFS in 8 seconds; the film's quietest 20 ms is \u221237.92 dBFS at t=13.82 s (beat 1).",
    "severity": "significant"
   },
   {
    "claim": "BUS TRIMS ARE KEYED TO EACH BUS'S SINGLE LOUDEST 3-SECOND WINDOW, which normalises every bus's peak moment to the same target and flattens the film's internal relief. It also means two buses were running grossly out of range and were rescued by one broadband number.",
    "measurement": "master_stemrun_report.json /buses: shards measured_max_short_term +37.12 LUFS, raw_peak 547.34, trim \u221246.12 dB. structure measured \u221282.39 LUFS, trim +52.39 dB. engine trim +24.99 dB, impact +23.64 dB. Verified the stems are post-trim: 547.34 x 10^(\u221246.123/20) = 2.71 = +8.66 dBFS vs measured shards stem peak +8.64 dBFS. Stem sum reconstructs the master at 85.6/76.7/\u2014/84.4/68.1/85.4% of energy per beat (corr 0.83\u20130.93), median 85.3% with a 1 s sliding gain.",
    "severity": "minor"
   }
  ],
  "verdict": "Yes, there is a shared defect \u2014 but it is NOT in the dynamics chain: the limiter (0.124 dB max gain reduction), clipping (zero samples over, \u22121.097 dBTP), dynamic range (LRA 13.06 LU, per-beat crest 9.3\u201319.6 dB) and resampling are all measurably clean, and the real shared stage is spatial and spectral \u2014 the two-ear propagation model renders every direct sound near-mono (impact/shards L/R corr 0.996, breach side/mid \u221224.3 dB) while the whole film sits 14\u201326 dB dark above 4 kHz and 50 ms crest factor never exceeds Gaussian noise (median 9.70 dB), with a flat, undamped 1:1 wet/dry reverb owning 45.9% of the first 33 seconds \u2014 and every one of these numbers is IDENTICAL in the two masters the client already rejected, which proves better sources alone cannot fix it."
 },
 {
  "findings": [
   {
    "claim": "THE SHARED STAGE IS REAL: the master limiter runs EIGHT times in series and eats 8.42 dB of programme loudness, and the report hides it because only the last, gentlest pass's gain reduction is stored. audio/master.py:633-641 \u2014 `for _ in range(8): ... master, gr = dsp.soft_limit(master, ceiling=10.0**(-1.15/20.0), sr=sr)` then `rep[\"limiter\"] = {..., \"max_gain_reduction_db\": gr}`. `gr` is overwritten every iteration. Worse, dsp.soft_limit (audio/dsp.py:446-453) HOLDS the reduction: `g = minimum_filter1d(need, size=2*rel+1)` with rel = 120 ms pins the gain to the minimum over a \u00b1120 ms window, then `sosfiltfilt` (ZERO-PHASE, so it also ducks BEFORE the peak) smooths it at 1000/120 = 8.3 Hz. Every transient digs a 240 ms hole in everything around it, eight times over.",
    "measurement": "Exact reconstruction of the chain from audio/out/stems/*.wav reproduces master.wav to max abs diff 6.56e-07 (-123.67 dBFS), so this is the shipped signal. Per-pass max GR: -19.93, -3.89, -2.20, -1.13, -0.63, -0.40, -0.22, -0.12 dB. Report claims max_gain_reduction_db = -0.1243 \u2014 the eighth. Cumulative per-sample limiter gain: MIN -28.27 dB, mean -1.75 dB; 20.65% of the film is pulled down >1 dB, 15.48% >3 dB, 12.15% >6 dB. Loop applies +10.33 dB of make-up to net +1.91 dB => limiter removed 8.42 dB. Worst GR per second: t=35 s -28.27, t=36 -27.12, t=37 -19.90, t=38 -17.89, t=39 -14.00, t=40 -17.21, t=41 -16.12, t=42 -11.18, t=43 -12.00, t=44 -7.82; beat 1 t=13-15 s -8.6/-8.7/-7.2; beat 6 t=108-109 s -14.31. The shipped master's 100 ms peak sits at exactly -1.10 dBFS (the ceiling) in 59 of 124 seconds, and the whole-film 20 ms crest median is 9.79 dB.",
    "severity": "ruins-everything"
   },
   {
    "claim": "THE MIX BALANCE IS SET BY A METER THAT IS DEAF TO THE FREQUENCIES THE MIX IS MADE OF. audio/master.py:399-422 `add()` trims every bus to a `dsp.max_short_term_lufs` target from TARGET_LUFS_S. That meter is BS.1770 K-weighted (dsp.py:524-545, RLB high-pass at 38.135 Hz), and the breach buses are almost entirely below it. So the meter under-reads them and the trim over-boosts them by the same amount, and the resulting inaudible peaks are what drives finding 1. This is the single stage every source passes through, and it is where the film's headroom is spent on content no one can hear.",
    "measurement": "K-weighting response measured from dsp._k_weighting(96000): -13.30 dB at 20 Hz, -19.63 dB at 13 Hz, -23.81 dB at 10 Hz, -35.42 dB at 5 Hz. Over 35.5-44.0 s the `impact` bus has unweighted RMS +0.81 dBFS but K-weighted -13.54 dB \u2014 a 14.35 dB discount; `shards` 9.05 dB; `engine` only 0.51 dB. Consequence from master_report.json buses: impact measured -30.14 LUFS-S, target -6.5, trim +23.64 dB, raw peak 0.493 -> enters the sum at linear peak 7.50 (+17.5 dBFS); shards trim -46.12 dB, enters at 2.70. Pre-master mix peak 7.6995 at film t = 36.019 s. Spectral centroid of the summed mix over 36-40 s = 57 Hz; 82.0% of beat 3's energy is below 20 Hz, 89.9% below 30 Hz, and 0.01% above 2 kHz.",
    "severity": "ruins-everything"
   },
   {
    "claim": "THE BREAKING GLASS CONTAINS NO GLASS, AND THE CAUSE IS ONE LINE: amplitude is exactly inversely proportional to pitch. audio/layers.py:425 `m = GLASS_RHO * GLASS_H * L * L` (= 30*L^2 kg), :465 `amp = m * vz_in`, :450 `f1 = 0.47 * (GLASS_H / (L*L)) * GLASS_CL` (= 30.6/L^2 Hz). So amp = 918*vz/f1 \u2014 a big slab is loud and low, a bright chip is silent. The same file computes the correction that fixes this and does not apply it here: layers.py:328-330 `fc_crit = c^2/(1.8*GLASS_CL*GLASS_H)` = 1004 Hz with `_rad(f) = min(1.0,(f/fc_crit)**2)` is used for the pane in `glass_wall` and omitted from `render_shards`. Applying it would drop a 54 Hz contact 25.4 dB. Separately, a shard contact is three PURE SINES and no noise whatsoever (layers.py:518-522, ratios 1 : 2.08 : 3.41, one common exp decay, plus a 0.4 ms DC bump) \u2014 that is the definition of a struck bar, i.e. \"banging on tubes\".",
    "measurement": "Re-ran layers.shard_ballistics with the shipped contact speed 16.709 m/s: 351 shards, 995 contacts over 53.76 m2 (mean shard 0.39 m across). Energy (amp^2 * decay) share below 500 Hz = 99.7% (705/995 contacts); above 2 kHz = 0.0000% (74 contacts). The TOP 10 CONTACTS CARRY 32.1% OF ALL SHARD ENERGY AND ALL TEN RING AT 54.4 Hz (the L=0.75 m clamp). Energy-weighted median ring frequency 68 Hz; after the beat-3 world-time slowdown (scale floor 0.153719, median 0.678 at contact time, 67.8% of contacts land inside beat 3 carrying 97.1% of the energy) the energy-weighted median HEARD frequency is 13 Hz. Measured on the stem: shards.wav 36-40 s spectral centroid 27 Hz, 0.0% of energy above 1 kHz; impact.wav centroid 12 Hz. The project's own gate already found this and excused itself: verify_new.log \u2014 \"NOT APPLICABLE 3_breach.hf: not audible: the band above 2.6 kHz carries 0.0183% of this beat's energy (limit 0.20%)\".",
    "severity": "ruins-everything"
   },
   {
    "claim": "THERE ARE ONLY TWO GENERATORS IN THE WHOLE NON-ENGINE FILM, AND THEY ARE THE CLIENT'S TWO COMPLAINTS. Every one of the ten non-engine layers in audio/layers.py is built from (a) Gaussian white noise \u2014 `dsp.white` = `np.random.default_rng(seed).standard_normal`, with `dsp.brown` (dsp.py:183) and `dsp.pink` (dsp.py:194) being that identical white noise through an IIR \u2014 or (b) sums of `np.sin` with exponential decay. Family (a) = tyres, wind, outdoor_bed, crowd (9 band-passed white-noise 'voices' whose envelopes are also white noise), fence_buzz, room_tone air/rumble, the crunch, the dust, the smoke, the stones: that is the \"wind blower\"/\"hair blower\". Family (b) = render_shards (3 sines), assembly (4 sines at 1:2.31:3.87:6.1, layers.py:377-378), impact_event thud (41/58/79 Hz sines, :553-554) and mullion (4 bending-mode sines, :565-567): that is \"The Tubes\" and \"banging on tubes\". Nothing outside engine.py uses a waveguide, a nonlinearity, a contact model, or any spectrally rich excitation \u2014 `dsp.comb_pipe` and `dsp.blowdown_pulse` are called ONLY from engine.py. The client is not hearing a bad engine and a bad shatter; they are hearing one noise generator and one sine bank wearing costumes.",
    "measurement": "Call-site census: 24 noise-generator sites (dsp.white/pink/brown/standard_normal) in layers.py vs 9 in engine.py; 16 `np.sin(` sites in layers.py, 13 in engine.py. Zero calls to comb_pipe or blowdown_pulse outside engine.py. A shard contact contains 0 noise samples. Measured stem centroids at the breach confirm the collapse: shards 27 Hz, impact 12 Hz, structure 374 Hz, engine 228 Hz \u2014 the whole event lives in one octave-and-a-half.",
    "severity": "ruins-everything"
   },
   {
    "claim": "IN THE FIRST 33 SECONDS THE REVERB IS LOUDER THAN THE THING MAKING IT. audio/master.py:521-535: `excite = eng_f + tyre_f*0.5 + asm_f*1.2 + imp_f*0.8` feeds `layers.showroom_tail` at RT60 2.4 s low / 0.85 s high, and TARGET_LUFS_S trims the resulting `room` bus to -23.0 LUFS-S while trimming the dry `assembly` that excites it to -27.0. The wet is declared 4 dB above the dry. This is the shared smearing stage the brief asked about, and it lands on exactly the 30 seconds the client described as \"the instrument The Tubes over and over\".",
    "measurement": "Measured from the shipped stems, as they enter the sum. Over 0-33 s: assembly RMS -36.75 dBFS, room RMS -36.82 dBFS \u2014 a 0.07 dB difference. Reverb-to-direct per window: +9.21 dB (0-2 s), +4.78 dB (9-10 s), -1.65 dB (14-20 s), +1.91 dB (20-26 s), +2.34 dB (26-33 s). Only three buses carry anything at all in beat 1 (assembly -36.75, room -36.82, crowd -52.02 dBFS); tyres, bed, fence, aperture, impact, shards and both reflections are all at digital silence.",
    "severity": "significant"
   },
   {
    "claim": "NOTHING HIGH-PASSES THE FILM ABOVE 12 Hz, AND SUB-30 Hz CONTENT NOBODY CAN HEAR IS 85% OF ITS ENERGY. The only low cut in the chain is audio/master.py:626 \u2014 a 2-pole Butterworth at 12 Hz, described as a DC block. Beat 3's world-time slowdown (scale floor 0.153719, a 6.5x stretch, 30.5 semitones) transposes every world-attached source into the infrasonic band and nothing catches it. Counterfactual run through the exact chain: inserting ONE 30 Hz high-pass before the program gain recovers several dB of the audible programme at the breach and halves the limiter's work there.",
    "measurement": "Energy share below 30 Hz: whole film 85.1%, beat 3 breach 89.9% (below 20 Hz: 82.0%), beat 5 lap 12.8%, beat 1 1.8%. A 30 Hz high-pass drops the premix RMS 8.27 dB and its peak only 1.94 dB. Counterfactual through the real chain: audible band (120 Hz-8 kHz) gains +4.35 dB at t=36 s, +5.58 at 37, +3.49 at 38, +2.92 at 39, +2.52 at 40, +2.82 at 41, +2.38 at 42; limiter GR at t=36 s improves from -19.90 to -11.90 dB and total loudness eaten by the limiter falls from 8.42 to 6.70 dB. Honest limit: -26.33 dB of GR still remains after the high-pass, so the sub-bass is roughly half the cause and finding 2's K-weighted trim is the rest.",
    "severity": "significant"
   },
   {
    "claim": "THE BRIEF'S BEAT-4 PREMISE IS WRONG AND THE TIMECODE MATTERS. docs/beat_sheet.json names beat 4 `4_transit` (44.0-49.6 s, \"apron, merge arc, onto the pit straight\"). The GLASS WALL BREACH is beat 3, `3_breach`, 36.0-44.0 s. The nose reaches the pane at world t = 1.92815 (filmtime.GLASS_WORLD_T), which the clock maps to film t = 36.00010 s = frame 864.0. Anyone auditioning \"beat 4\" for the glass has been listening to the transit, 8 seconds after the event.",
    "measurement": "beat_sheet.json beats: 1_assembly 0.0-33.0, 2_launch 33.0-36.0, 3_breach 36.0-44.0, 4_transit 44.0-49.6, 5_lap 49.6-113.1, 6_ending 113.1-124.1. Clock('docs/beat_sheet.json').film_at_world(1.92815) = 36.00010 s, frame 864.002.",
    "severity": "minor"
   },
   {
    "claim": "HYPOTHESES TESTED AND CLEARED, so the parent does not re-spend effort on them: mono/stereo collapse, the resampling path, the slow program gain, and the zero-phase band-split. The image is intact, the resamplers are transparent, the program gain is genuinely slow and bounded, and the complementary band-split is exact \u2014 none of these is the shared defect.",
    "measurement": "Stereo: global L/R correlation 0.759, side/mid -8.62 dB, per-8 s correlation ranges 0.17 to 0.93 \u2014 not collapsed. Resampling: the full chain reconstructed independently (program_gain -> 12 Hz DC block -> 8x loudness/limit -> resample_poly 96k->48k kaiser 12 -> 48k relimit -> 12 ms tail fade) matches the shipped master.wav to 6.56e-07 max abs (-123.67 dBFS), so no hidden resampler or dither artefact exists. program_gain: measured range 10.25 dB (min -3.118, max +7.130) over 6 s/12 s time constants \u2014 an order of magnitude slower than a musical compressor, and it is not the crusher. Band-split: dsp.split_bands telescopes to x exactly and the project's own bandsplit_PASS confirms it; the only colouring it can produce is via unequal per-band air-absorption gains, and at the breach the camera is 2.2-8.5 m from every breach source, where those gains are within a fraction of a dB.",
    "severity": "null"
   }
  ],
  "verdict": "Yes \u2014 there is a shared defect, and it is a three-stage chain in the mix bus rather than either synthesiser: a K-weighted loudness trim that is 14 dB deaf to the sub-bass the breach is made of, feeding an eight-pass true-peak limiter that removes 8.42 dB of programme and up to 28.27 dB locally with a 240 ms zero-phase hold, on top of a film in which every non-engine sound is the same two generators (Gaussian white noise and exponentially-decaying sine stacks) wearing different filters."
 },
 {
  "findings": [
   {
    "claim": "SCOPE CORRECTION FIRST: the glass wall breach is BEAT 3, not beat 4. Beat 4 is '4_transit' (apron/merge arc, no glass). All analysis below is on the correct window.",
    "measurement": "docs/beat_sheet.json beats[]: '3_breach' start_s 36.0, duration_s 8.0, anchor note at t=36.0 = 'IMPACT. world time collapses to 15.4% over 6 frames'. '4_transit' start_s 44.0, duration_s 5.6. Breach window = 36.0-44.0 s.",
    "severity": "null"
   },
   {
    "claim": "THE SHARED DEFECT IS REAL AND IT IS THE WORLD-TIME WARP. audio/master.py:365 warp() is clock.WorldGrid.to_film -> catmull_rom(), a varispeed resampler applied to engine, tyres, structure, assembly, impact and shards alike. It does not time-stretch, it TRANSPOSES. Beat 3 runs world time at a floor of 15.37%, so every warped source in the breach is pitched down by up to 6.51x (31.4 semitones, 2.6 octaves). One stage, both complaints: it turns the glass into subsonic mush and drags the engine's harmonics into the bass at the same moment.",
    "measurement": "master_report.json clock.ramp: frames [865,1056], solved_floor 0.153719, declared_world_s 1.6 over 8.0 s of screen time. 1/0.153719 = 6.51x downward transposition. INTERNAL CONTROL (same synthesiser, only the clock changes): shards stem spectral centroid 41.2 Hz at 36.5-38 s, 30.7 Hz at 38-40, 26.9 Hz at 40-42, 29.3 Hz at 42-43, 37.2 Hz at 43-44 -- then 146.3 Hz at 44.0-45.2 s, 3.55x brighter, the instant the ramp ends and scale returns to 1.0.",
    "severity": "ruins-everything"
   },
   {
    "claim": "CONSEQUENCE: the breaking glass is the DARKEST event in the entire film. It has essentially no energy where glass lives. The shard synthesiser is not at fault -- shard_ballistics declares ring frequencies from 54.4 Hz to 18,911 Hz, and the warp lands the whole range in the bass.",
    "measurement": "master.wav 36-44 s power split: 42.56% below 20 Hz, 38.79% at 20-60 Hz (81.35% below 60 Hz), 6.56% at 150-500, 0.84% at 0.5-2k, 0.03% at 2-5k, 0.004% above 5 kHz (-45.73 dB of total). Compare beat 1 at -26.64 dB above 5 kHz and the flying lap at -19.94 dB. shards stem: 50% of power below 23.4 Hz, 90% below 58.6 Hz, 99.99% below 1078 Hz, 0.00% above 5 kHz. impact stem: 68.98% below 20 Hz, dominant spectral peak at 5.86 Hz. Target for real breaking glass: strong energy above 5 kHz, i.e. tens of percent, not 0.004%.",
    "severity": "ruins-everything"
   },
   {
    "claim": "SECOND SHARED STAGE: the master limiter removes up to 22.8 dB on the breach and its own report says 0.12 dB. audio/master.py runs soft_limit NINE times in cascade (8 passes in the 96 kHz loudness loop + 1 at 48 kHz); the loop's `gr` variable is overwritten every pass, so master_report.json records only the last one. The loop never converged -- 8 iterations, still 0.12 dB off its 0.05 dB tolerance.",
    "measurement": "Recovered the true gain curve by dividing master.wav by the resampled sum of all 14 stems, 20 ms blocks. Total chain gain: +17.21 dB median in quiet beat 1 (5-30 s) vs -16.21 dB at the impact (35.9-36.6 s) = 33.42 dB of squash. Splitting slow from fast: at the impact the slow program gain is -6.47 dB and the FAST limiter component is -10.37 dB; across 36-44 s the fast component reaches -22.76 dB minimum. Over the lap (50-110 s) the fast component's median is 0.00 dB. Loudness iterations [-15.98, -17.81, -16.12, -15.09, -14.61, -14.38, -14.21, -14.12]: loudness FELL 1.83 dB after a +1.98 dB boost on pass 1. 10.33 dB of makeup was pushed in for 1.91 dB of net loudness -- 8.42 dB of program loudness eaten by limiting. Reported max_gain_reduction_db: -0.124.",
    "severity": "ruins-everything"
   },
   {
    "claim": "THIRD SHARED STAGE, and the reason the limiter has to work that hard: the TARGET_LUFS_S gain-staging table normalises every bus by 3-second K-weighted short-term LUFS. K-weighting discounts bass and a 3 s window averages a 50 ms transient over 3 s of near-silence, so the table is blind to both crest factor and spectrum. It therefore massively overdrives exactly the bass-heavy transient buses the breach is made of.",
    "measurement": "impact bus: raw peak 0.493 (-6.14 dBFS), but measures -30.14 LUFS short-term because 96.0% of its energy is below 60 Hz. To reach its -6.5 LUFS target the table applies +23.64 dB, producing a peak of 7.5 linear = +17.5 dBFS. Mix peak before the master chain: 7.699 (+17.73 dBFS) against an integrated -13.59 LUFS -- a 31 dB crest the limiter must then destroy. Other trims the same table produced: structure +52.39 dB, fence +35.62 dB, engine +24.99 dB, shards -46.12 dB (raw peak 547.3).",
    "severity": "ruins-everything"
   },
   {
    "claim": "MEASURED RESULT ON THE GLASS: the smash is the LEAST transient event in the film. Its crest factor is lower than the quiet parts-assembly beat. Onset sharpness fails outright.",
    "measurement": "master.wav crest factor (peak/RMS): impact 35.9-36.3 s = 9.97 dB; 36-39 s = 9.63 dB; 39-44 s tail = 8.99 dB. Compare beat 1 (10-30 s, quiet assembly) = 16.36 dB and the flying lap (60-70 s) = 16.21 dB. Onset rise time at the impact: 6.0 ms from -6 dB to peak, 110.0 ms from -20 dB to peak. Peak is pinned at -1.43 dBFS, i.e. the limiter ceiling, throughout. Real breaking glass: sub-millisecond onset, crest 25-35 dB -- it should be the HIGHEST in the film, and it is the lowest.",
    "severity": "ruins-everything"
   },
   {
    "claim": "DEBRIS SHOWER DENSITY is 25-60x too sparse. The ballistic sim generates a genuinely dense shower; the warp and the limiter throw almost all of it away. At a 23-59 Hz centroid a single cycle lasts 17-43 ms, so a sharp shard onset is physically impossible in the delivered signal regardless of how many events the sim produced.",
    "measurement": "master_report.json breach_sim: 351 shards, 995 contact_events over settle_world_s 3.148 = 316 events/s. Measured onsets in the 1-4 kHz band of master.wav: 5.0/s (36-37 s), 10.0/s (37-39), 13.5/s (39-41), 10.0/s (41-44). Above 5 kHz: 1.0-5.0/s, indistinguishable from the lap reference at 1.7/s.",
    "severity": "significant"
   },
   {
    "claim": "The one glass property that SURVIVED: the debris tail is genuinely irregular, not repetitive. The 'over and over' percept does not come from the breach tail.",
    "measurement": "Autocorrelation of the 2 ms envelope: breach 36-44 s peaks at r=0.125 (0.156 s lag); tail 38-44 s r=0.128 (0.158 s). Both far below any periodicity threshold. No periodic structure in the shard shower.",
    "severity": "null"
   },
   {
    "claim": "REFUTED CANDIDATE - shared noise generator. Every 'different' sound is NOT secretly the same noise. Distinct seeds throughout layers.py (808/4242/97/311/5150/771/1234/31337/606) and the stems are measurably uncorrelated.",
    "measurement": "Max |normalised cross-correlation| between wind/bed/crowd/tyres/fence stems over 60-70 s: highest pair is wind x bed at 0.0565; all ten pairs below 0.057. Independent noise.",
    "severity": "null"
   },
   {
    "claim": "REFUTED CANDIDATES - clipping, resampling artefacts, film-wide mono collapse, reverb wash. None of these is the cause. Note the breach alone DOES collapse to near-mono, but that is a symptom of its sub-60 Hz domination, not an independent bug.",
    "measurement": "clipped_samples 0; true peak -1.10 dBTP; DC offset -2.08e-05 / -2.02e-05; silent_1s_windows 0. Stereo side/mid: whole film -8.62 dB (L/R corr +0.759), beat 1 -6.58 dB, lap -8.06 dB -- all healthy. Breach only: -21.83 dB, L/R corr +0.987. Reverb buses are trimmed well down (room -23, reflect_showroom -25, aperture -27 LUFS) and measure inaudible or near it, so nothing is being smeared into mush.",
    "severity": "null"
   },
   {
    "claim": "INVENTORY VERDICT: this is NOT a one-engine film. 14 buses exist, 13 non-engine, and every one carries signal -- none is digital silence. The problem is masking and mix, not absence. But during the 63.5 s flying lap the only non-engine element that ever rises above the mix is WIND, which the code itself documents as pure brown+pink noise with no tonal element anywhere. Engine plus a noise bed is exactly the 'wind blower' percept. (Overlaps the engine workflow's scope -- flagging, not duplicating.)",
    "measurement": "Per-bus, measured from the stems as level vs the sum of all other buses when active. AUDIBLE: assembly 0.1-33.3 s (median -9 dB, best +3); room 0.0-37.9 s (median +2, best +14); impact 36.0-43.1 s (best +19); shards 36.1-45.2 s (best +18); reflect_garage 46.8-50.7 and 110.4-114.8 s (median -3); wind 44.6-119.7 s (median -1, best +14). MOSTLY MASKED, never rises above the mix: tyres 34.1-115.3 s (best -6 dB); crowd 0.5-113 s (best -4 dB); bed 33.4-123.9 s (best +13 but only under the breach). BURIED: structure (the pane buzzing before it goes) 32.0-36.4 s, best -14 dB; fence 49.7-116 s, best -15 dB. INAUDIBLE: reflect_showroom 38.0-45.7 s, best -25 dB under; aperture 37.2-49.2 and 104.9-113.6 s, best -28 dB under.",
    "severity": "significant"
   },
   {
    "claim": "INVENTORY GAP: four sound families that a car film needs do not exist anywhere in the codebase -- no brakes, no suspension/dampers, no gearshift or downshift, no kerb strikes. layers.py provides only tyres, wind_at_camera, showroom_tail, room_tone, outdoor_bed, crowd, fence_buzz, glass_wall, assembly, shard_ballistics, render_shards, impact_event. A 63.5 s flying lap with no brake and no downshift has no way to express deceleration.",
    "measurement": "Full function list of audio/layers.py (12 generators) plus audio/engine.py. Grep for brake/damper/suspension/shift/gear/kerb across audio/*.py returns no synthesis layer. Beat 6 is an 11.0 s deceleration from 83.1 m/s to 0 with no braking sound available to it.",
    "severity": "significant"
   },
   {
    "claim": "WHY NO GATE CAUGHT ANY OF THIS: the instrumentation measures the wrong quantity at every one of the three shared stages. The limiter reports one of nine passes. The trim table reports LUFS, which is deliberately blind to the sub-20 Hz that dominates the breach. Nothing anywhere measures crest factor, onset time, or high-frequency content.",
    "measurement": "master_report.json limiter.max_gain_reduction_db = -0.12429 (true value -22.76 dB); limiter_gr_db = [-0.124, 0.0, -0.0215] where the middle entry is variable gr2, never assigned inside the loop. rep['buses'] records measured_max_short_term_lufs and trim_db for all 14 buses and no peak-to-loudness ratio. No spectral or transient metric is written for the breach anywhere in the report.",
    "severity": "significant"
   }
  ],
  "verdict": "Yes \u2014 there is a shared defect, in fact three stacked ones, and they explain both complaints at once: the beat-3 world-time warp is a varispeed resampler that transposes the entire breach down 6.51x into the subsonic (only 0.004% of its energy survives above 5 kHz), a crest-and-bass-blind LUFS trim table then pushes those bass-heavy transients to +17.5 dBFS, and nine cascaded limiter passes remove up to 22.8 dB while reporting 0.12 dB \u2014 leaving the glass smash with the lowest crest factor in the film (9.97 dB, below even the quiet assembly at 16.36 dB), so no improvement to either synthesiser could fix it."
 }
]
```
