# Engine percepts + gate replacement

Produced by a diagnosis + design workflow, 2026-08-14, against the
DELIVERED master. Every claim carries the number it was measured from.
Nothing here is inherited from an earlier report -- three previous audio
rebuilds passed all eight gates and were rejected by the client.

---

# BUILD SPECIFICATION — F1 ROUND 2 AUDIO, REBUILD 3

**Chosen spine:** Design 2 (percept-first: *kill the hiss, break the period, move the resonance*), because it is the only design scoped to the 33 seconds the client actually named. **Grafted from Design 1:** the regulation-derived power unit (uneven firing, wastegate path, turbine impedance), the verification *governance* rules (control corpus, provenance/quality gate split, `source=` on every threshold), and the Weyl-law modal-density bar. **Grafted from the gate audit:** the mutation-control discipline and the retained rejected master as a permanent negative control.

**One overrule, stated openly:** Design 1 wants ignition moved into beat 1 (film t ≈ 18–20 s). I reject it as the critical path. It is a director/picture decision costing ~800 re-rendered 4K frames, and the diagnosis shows beat 1's defect is entirely in the *voice*, the *room*, the *schedule* and the *servo* — none of which need an engine. The thing that actually needs filling is the ~1.04 s of naked reverb between bursts, and 15 per-cluster servo voices (B6) fill it with tonal content at 1/50th the cost. Keep "fire the PU in the showroom" as a deferred creative ask, not a dependency.

---

## 1. ROOT CAUSE OF EACH PERCEPT — ONE SENTENCE, ONE NUMBER

**"Wind blower" / "hair blower":** The first 30 seconds contains no engine at all — `audio/out/stems/engine.wav` is bit-zero until t = **31.395 s** (verified this session) — so 92.6 % of beat-1 power is two broadband stems, `assembly` (46.7 %, SFM 84.5 % of white) and `room` (45.9 %, 81.2 % of white), whose decorrelated sum reaches **98.6 % of white-noise spectral flatness** in 500–3000 Hz (0.5808 vs 0.5891 through the identical pipeline), with the single largest generator being `audio/layers.py:391` — `dsp.bp(dsp.white(n, seed+1), 900.0, 6000.0, sr, 2) * 0.6`, a broadband term weighted **higher than both of the servo's tonal terms combined (0.5 + 0.2)** and carrying 22.2 % of all power over 0–13.5 s, before the first impact exists.

**"The Tubes":** `audio/layers.py:376-378` rings four exponentially-decaying sines at **1 : 2.31 : 3.87 : 6.1** — the free-free metal-bar/pipe mode series — 616 times in 16 s, 73 % of them (450 hits, 7 of 15 clusters) from a **22 Hz-wide pitch centre at 251.8–273.0 Hz**, radiated into an 8-tap FDN (`audio/dsp.py:362-411`) with **zero diffusion stages**, whose 13 strongest lines are every one a harmonic of a delay length matched to **0.01–0.93 %** and which ring at T60 **3.0–4.6 s** against a declared 2.4 s; on top of that `audio/master.py:530-532` sums the tail with a delayed copy of itself (681 / 1084 samples) printing a **fixed 141.0 Hz / 88.6 Hz comb, 16.5–17.6 dB of ripple, the largest cepstral feature in the whole first 30 seconds**.

**"Over and over":** Cluster seat frames sit on an exact uniform frame grid — 33 frames = **1.375000 s** in the delivered master, and I verified `world/beat1_anim_anim.json` at HEAD today reads `[238, 263, 288, 313, 338, 363, 388, 413, 438, 463, 488, 513, 513, 513, 513]`, **diffs all exactly 25 = 1.041667 s** — giving envelope autocorrelation **r = 0.585 at lag 1.374 s** with a clean integer-multiple ladder (2.754/4.133/5.509/6.880/8.260 s), and `audio/layers.py:367` (`fr = seat_f + (last_f - seat_f) * (p / max(nparts-1,1))`) places parts within each cluster on a mathematically exact grid producing pitched buzz tones at **exactly 3·(n_parts−1) Hz** (27, 36, 48, 96, 120, 192, 288, 357 Hz).

**The compounding fact:** the complaint generalises past beat 1. Engine-to-everything-else per beat is **−12.01 / +15.07 / +0.11 / +0.03 / −17.25 dB**. On beat 5 — 63.5 s, **51 % of the film** — engine and broadband bed are **0.03 dB apart**. Only beat 2 (3.0 s, 2.4 %) has an engine on top.

---

## 2. GATES THAT MUST BE **REPLACED**, NOT RECALIBRATED

The audit's decisive proof: beat 1 replaced by one 2.000 s block tiled 16.5× passes **all eight gates**, `ALL_PASS=True`, exit 0 — and the harmonic gate rates that loop **35.9 dB better** than the film it passed. Recalibration cannot fix an instrument that reads the same whether the defect is present or absent.

| Existing gate | Verdict | Replacement |
|---|---|---|
| `harmonic` / `hnr_profile` (`verify.py:1123`) — no f0 estimate, subtracts a 269.5 Hz running median and calls anything above it "tonal"; a literal hair-dryer-into-tubes passes with **more** margin (0.481) than the master (0.708) | **DELETE** | **G-ORDER** (comb tracking against telemetry rpm), **G-FLAT** (tilt-free per-band SFM vs white), **G-HNR** (calibrated Boersma) — three separate instruments, because one number was the original mistake |
| `BEAT_HNR_LIMITS` (`verify.py:864`) — beat 1's bar is −1.0 dB, defined in the code's own comment as *"one decibel above what this metric reads on something with no line spectrum at all"*, with 85 % of windows permitted below even that | **DELETE THE WHOLE TABLE** | Thresholds carry a machine-checked `source ∈ {physics, published, control-derived}`. CI **rejects** any threshold with `source=artefact`. `verify.py:816`'s rule ("the midpoint between what THIS master reads and what the adversary reads") is banned in writing |
| `waveguide` — algebraic root-solve of `engine.py` constants at a hand-picked `WAVEGUIDE_RPM = 11000`; the same gate **FAILS at the film's own rpm_at_vmax of 13,143** (5.798 vs a 5.0 limit); never touches `layers.assembly` or the showroom FDN | **DELETE** | **G-RING**: ring-through and modal decay measured on the **rendered stereo wav**, across the whole rpm sweep, over **all** layers |
| `pitch` — re-synthesises the dry engine from telemetry and measures *that*; passes 100 % white noise | **RECLASSIFY as `provenance`**, excluded from the quality verdict | f0 tracked **on the delivered master** vs telemetry becomes a limb of G-ORDER |
| `external_assets` — AST scan, never opens the wav | **KEEP, reclassified `provenance`** | Extended with **G-CONSTRUCT** (below) |
| `seam` — adjudicates 20 samples of 5,956,000 (0.0003 %); its own 3 dB-step positive control **passes** on broadband material | **KEEP, but its PASS is advisory** | Splice detection runs film-wide, not only at the 5 beat boundaries |
| `edges`, `levels` | **KEEP** | `levels` swaps its hand-rolled meter for `pyloudnorm` |
| `doppler` — the only genuinely load-bearing gate (failed all three whole-file degenerates) but sees 85 windows in one 4.2 s span inside beat 5 | **KEEP AND EXTEND** | Coverage widened to every beat with camera-relative motion; **port it deliberately before B7**, because halving the firing fundamental will break it |

**New gates that have no predecessor at all:** G-NOVEL (self-similarity), G-MOD (modulation spectrum), G-GESTURE (burst-to-burst timbral distinctness), G-ROOM (modal density / mobility / comb ripple), G-BALANCE (stem-level protagonist margin), G-CONSTRUCT (AST: no `white()`/`pink()`/`brown()` may reach a bus without passing an event scheduler or a physically-parameterised filter carrying a derivation comment).

**Two structural rules that fix the class of defect:**
1. `INAPPLICABLE` is a distinct outcome from `PASS` and never counts toward `ALL_PASS`. (Today `harmonic` on pure noise reports `failures: []` and trips `undeclared_unmeasurable` — it says *"I cannot measure this"*, never *"this is noise"*.)
2. Any gate that does not take the rendered stereo master as an input is labelled `provenance` and is excluded from the quality verdict. That alone removes three of the current eight.

---

## 3. SYNTHESIS ARCHITECTURE AND TOOLING

### Architecture: **excitation → body → room → stereo**, with one law

> **No `white()` / `pink()` / `brown()` output may reach a bus. Every source is an event scheduler driving a resonator whose modes come from a geometry.** Machine-checked by G-CONSTRUCT, exactly as `external_assets` is today.

**Layer 1 — Excitation.** Hertzian contact pulse, τ = 2.94·(m²/(R·E*²·v))^(1/5), typically 0.4–2.5 ms, rendered as a raised half-sine — band-limited by construction, f⁻² rolloff above 1/τ. Replaces `click = rng.standard_normal(L) * exp(-tt/0.004)` at gain 0.5 × 616 events.

**Layer 2 — Body.** Reuse the orthotropic modal solver **already in this repo**: `layers.plate_modes(a, b, h, e, nu, rho)` at `audio/layers.py:285`. Call it with CFRP constants (E₁ = 135 GPa, E₂ = 9 GPa, ν = 0.30, ρ = 1600 kg/m³, h = thinnest bbox axis) instead of glass, with **a, b from each cluster's own bounding box in `docs/explode_plan.json`** (already loaded). Damping from CFRP loss factor η = 0.005–0.02 plus clamped-joint η_joint ≈ 0.05–0.1 → T60 **10–40 ms at 1 kHz**, against the ~500 ms currently measured. Select modes by radiation efficiency using the existing `_rad()` critical-frequency weighting from `glass_wall()`; keep 48 per cluster.

**Layer 3 — Room.** Delete `showroom_tail`'s FDN. Replace with a hybrid:
- **Early (0–80 ms):** image-source model of the actual 30 × 22 × 6.5 m box to order 3 (343 images), **driven by each cluster's actual source position**. The current FDN has no position input at all — that is precisely why the room answers 430.2 Hz to everything.
- **Late (80 ms → RT60):** **velvet-noise convolution** — 2500 pulses/s, ±1 signs, one pulse per 38-sample grid cell at jittered position, band-split exponential decay to Sabine RT60, FFT overlap-add. Velvet noise **has no modal structure**; its magnitude response is a noise, not a comb, so its frequency-domain autocorrelation has no peak. That is the direct structural answer to "the room replies at the same pitches to 0.01 %".
- Keep `dsp.fdn_reverb` for the circuit/garage reverbs, but **add 4–8 nested allpass diffusion stages** there — the same modal-density deficit applies (0.4255 modes/Hz measured against Weyl's 1336 modes/Hz at 1 kHz for 4290 m³, short by a factor of 3140).

**Layer 4 — Stereo.** Two **independent** velvet sequences for L and R. **Never sum a signal with a delayed copy of itself anywhere in the mix.** Delete `master.py:530-532` (681/1084), `master.py:534` (137 samples on room_tone → 700 Hz comb), `layers.py:168` (0.9 ms on wind → 1.1 kHz comb).

**Engine (film-wide, beats 2/4/5).** Uneven **90/150° firing** — FIA 2025 Art. 5.2.10 permits only three con-rod journals, which with the Art. 5.2.7 90° vee geometrically forces it. `CYL_PHASE_DEG` (0, 240, 480, 120, 360, 600) → **(0, 90, 240, 330, 480, 570)**. Fundamental moves to engine order **1.5** (RPM/40 Hz) with weighting **A(k) = |cos(πk/4)|** — exact null at order 6, full strength at order 12. Implement as one evenly-fired bank generator plus a **quarter-revolution fractional delay (15/RPM s, Lagrange-interpolated)** summed, so the notches slide with RPM (400/1200/2000/2800 Hz at 12 000 rpm) — which no static EQ can fake. Add 1–2 % per-cylinder gain/timing dispersion, stable per cylinder, so the null is not mathematically perfect.

This contradicts an explicit reasoned decision at `audio/engine.py:292-297`. **Both can be partly right** — a shared collector *attenuates* the half-order, it does not *cancel* it. Ship behind `half_order_weight` (0.0 = today, 1.0 = regulation geometry), **default 1.0**, and send the client a bare A/B. Do not present the derivation as settled: no measured F1 spectrum was obtainable (every publisher returned 403).

Delete `rasp` (`engine.py:514-523`, white → 300–2600 Hz, the client's exact complaint band), delete `pump` (`engine.py:527-528`, the periodic part already goes down the primaries per the code's own comment at :529). Keep compressor broadband only at **4–13 kHz with a shaft-tracking upper edge** — above the complaint band — with level derived from mass flow. Add the mandated separate **wastegate tailpipe** (Art. 5.9.2, ≤1500 mm²) as a second, brighter, **turbine-bypassing** pulse path: that is the correct physical origin of the brightness `rasp` was faking.

### FOSS tooling to install — code libraries only, zero content

Target env: `.venv` (Python, numpy 2.5.1, scipy 1.18.0, soundfile 0.14.0, matplotlib already present).

| Package | Version | Licence | Why | Ships content? |
|---|---|---|---|---|
| `pyroomacoustics` | 0.8.x | **MIT** | Image-source method for the 0–80 ms early field, per-surface absorption, source position. Pure geometry→IR algorithm. | **No** — generates IRs from dimensions |
| `pyloudnorm` | 0.1.1 | **MIT** | ITU-R BS.1770-4 meter; replaces the hand-rolled loudness path in `levels` | No |
| `praat-parselmouth` | 0.4.x | **GPL-3.0** | **DEV-ONLY** cross-check of our in-repo Boersma HNR. Kept out of `requirements.txt`, imported only from `tools/calibrate_hnr.py`. Flagged because GPL-3 must not enter the shipped package. | No |

**Do not install** `librosa` (drags numba + soxr for features scipy already gives us). **Do not install** any impulse-response, sample or model pack — the ban is on content, and it is absolute.

**Boersma HNR is implemented in-repo** (`audio/percept.py`), not taken from a GPL dependency; the diagnosis already validated this construction against synthetic mixtures of a 145 Hz comb + bandpassed noise at known noise fractions, returning 16.98/12.86/9.62/4.88/0.22 dB against truths of 16.90/12.79/9.54/4.77/0.00 dB — **error ≤ 0.22 dB**. That calibration re-runs on **every gate invocation**, so the instrument re-validates itself each time.

Extend the `external_assets` AST scan to allow exactly these three imports by name and to **ban any audio file read** anywhere in `audio/`.

---

## 4. ORDERED BUILD STEPS

**B0 — WRITE THE FAILING TEST FIRST. Nothing else may start.** (~2 d)
New `audio/percept.py` (gates) + `tools/percept_matrix.py` (control matrix runner). **Acceptance for B0 itself: the delivered master `audio/out/master.wav` must FAIL G-NOVEL, G-MOD, G-GESTURE, G-ROOM and G-FLAT**, and the three existing degenerates in `tmp/gateaudit/` must fail. If the new suite passes the artefact the client rejected, the suite is wrong and no synthesis work is authorised.

**B1 — PROVENANCE FREEZE.** (~0.5 d)
The delivered master was built from the 33-frame schedule (git 19a55b3); HEAD carries 25 frames (verified above). `master_report.json` cannot tell them apart — impacts = 616, clusters = 15 in **both**. Write a SHA-256 of the resolved seat/land schedule plus the `world/` git rev into `master_report.json`, and make `percept_matrix.py` **refuse to adjudicate** a master whose recorded hash does not match the tree.

**B2 — THE THREE-LINE WIN, SHIPPED AND MEASURED ALONE.** (~1 d)
Delete the three self-delay decorrelators (`master.py:530-532`, `master.py:534`, `layers.py:168`). Substitute independent noise-seeded decorrelation as a placeholder (proper velvet pairs arrive in B4). Render beat 1 only. Target: cepstral peak over 1–30 ms falls from ≈8× median to < 2×; 0.4–6 kHz ripple p95−p5 from 17.6 dB toward ≈10 dB. **Send the client a 33 s A/B clip immediately** — one day of work against the most direct cause of the hollow colour, and it tells us early whether the diagnosis is on target.

**B3 — THE IMPACT VOICE.** (~3 d, ~3 min render)
Rewrite `audio/layers.py:376-380`. Delete the (1.0, 2.31, 3.87, 6.1) bank and the white click. CFRP `plate_modes` per cluster + Hertzian pulse + η-derived damping, rendered as a vectorised biquad bank following the `glass_wall()` pattern.

**B4 — THE ROOM.** (~4 d, ~1 min render)
Replace `layers.showroom_tail()` with image-source early (`pyroomacoustics`) + velvet-noise late, two independent L/R sequences. Add allpass diffusion to `dsp.fdn_reverb` for the circuit/garage uses.

**B5 — THE SCHEDULE. Start in parallel with B3; it is the long pole because it touches picture.** (~3 d + render)
(a) Regenerate `world/beat1_anim_anim.json` with **non-uniform** seat frames on a geometric contraction, gap ratio ≈ 0.86 (2.35 → 0.44 s). An accelerando has no single period, **and it is better filmmaking** — the car converging with rising urgency — so this is not a metric hack. (b) Replace `layers.py:367`'s exact linear placement with per-part gravity-derived arrival, t_land = √(2h/g) from each part's own start height plus one restitution bounce. (c) Playblast at low res and get the director's eye on it **before** spending 4K frames.

**B6 — THE SERVO WHIR.** (~1.5 d)
Rewrite `layers.py:387-391`. Delete `f_srv = 320 + 90·sin(2π·0.11·t)` — one global 9.09 s-period LFO for the entire showroom. One servo per cluster: shaft rate from that cluster's actual animation velocity, gear-mesh at N_teeth × shaft rate, PMSM radial force at 2·f_electrical, stator slot passing. **Broadband gain 0.6 → 0.06**, narrowed to a bearing band. Fifteen independent trajectories have no global period and no fixed pitch. This is also what fills the naked reverb gaps.

**B7 — ENGINE AND FILM-WIDE BALANCE.** (~2.5 d)
`half_order_weight` implementation; delete `rasp` and `pump`; add the wastegate path; replace `COLLECTOR_LOOP_GAIN = 0.14` with a frequency-dependent turbine reflection coefficient. Rebalance wind/tyre buses on beats 4 and 5 to the G-BALANCE margin. **Port the doppler gate to the new fundamental first** — halving f0 will break `verify.track_f0`, and doppler is the only load-bearing survivor.

**B8 — RE-VERIFY AND ADJUDICATE.** (~1 d)
Full control matrix including per-gate mutation controls. Then legacy `verify.py` for what it is genuinely good at (LUFS, true peak, AST scan, splices) and re-normalise — B3/B4 will have moved levels.

**B9 — THE TERMINAL GATE IS THE CLIENT.** Cut a 33 s beat-1 clip and a 20 s lap excerpt with the `half_order_weight` A/B and send them **before** committing to a full 124 s render and a full visual re-render.

**If only one week is available:** B0, B1, B2, B3, B6. Those need no picture decision and carry the largest audible return per day.

---

## 5. ACCEPTANCE TEST

### Tier 1 — the listener (the only sufficient test)
12-item blind forced-choice, 8 s excerpts, new build interleaved with the rejected master's beat 1, a literal hair dryer, noise-through-inharmonic-tubes, and a 2 s tiled loop. One question: **"In one word, what is this?"** **PASS = zero occurrences of blower / dryer / fan / hiss / vacuum / tube / pipe / loop / repeating across the new build's items, from four listeners.** Second pass over full 33 s beats: *"Does anything repeat?"* Every number below is a **proxy** calibrated against these labels, never the reverse.

### Tier 2 — the control matrix. **Runs FIRST. If any control returns the wrong verdict, the run exits non-zero and the verdict on the real master is UNDEFINED and unreported.**

| # | Control | Required verdict | Which gate it must trip |
|---|---|---|---|
| C1 | Octave-matched filtered noise (`verify._hairdryer_like`) | **FAIL** | G-FLAT, G-HNR |
| C2 | 2 s block tiled 63× (`tmp/gateaudit/degen_loop.wav`) | **FAIL** | G-NOVEL, G-MOD, G-GESTURE |
| C3 | Noise through high-Q inharmonic pipes (`degen_blower_plus_tubes.wav`) | **FAIL** | G-ORDER (peaks don't track rpm), G-ROOM |
| C4 | **`audio/out/master.wav` — THE DELIVERED, REJECTED MASTER, retained permanently** | **FAIL** | G-NOVEL, G-MOD, G-GESTURE, G-ROOM, G-FLAT |
| C5 | `tmp/gateaudit/swap_b1_loop.wav` (passes all 8 old gates today) | **FAIL** | G-NOVEL |
| C6 | **ANTI-CHEAT: jittered metronome of identical gestures** (±15 % jitter on 1.375 s, same gesture 12×) | **FAIL** | **G-GESTURE only** — must PASS G-MOD. This exists so that "just add jitter" cannot pass. |
| C7 | **ANTI-CHEAT: delivered master + broad spectral tilt** | **FAIL** | **G-FLAT** — proves the per-band construction is tilt-immune (whole-band SFM reads a reassuring 0.0142 on the delivered master; that is what let this ship) |
| C8 | Physics-true positive: constant-rpm PU render from the new model | **PASS** | all |
| C9..n | **Per-gate mutation controls**: the new master with each gate's specific defect deliberately re-injected | **FAIL that gate, PASS the others** | a gate that does not move when its own defect is re-injected is **proven blind and is deleted, not tuned** |

C4 is the single most important line in this spec: **a gate that passes the artefact the client rejected is broken by definition**, and this makes that statement executable.

### Tier 3 — numeric bars (every one carries `source=`, none derived from the artefact)

| Gate | Bar | Delivered reads | Reference |
|---|---|---|---|
| **G-FLAT** | SFM(500–3000 Hz), 1/3-oct-internal, **every 3 s slice of every beat ≤ 0.45·W**; beat-1 median ≤ 0.30·W | 0.98·W, min slice 0.91·W | W = white through identical pipeline |
| **G-HNR** | Beat-1 Boersma median **≥ +8 dB**; windows below 0 dB **≤ 10 %** | +0.52 dB; 42.1 % | +8 dB = the point where noise fraction < 15 % on the calibrated mixtures |
| **G-BALANCE** | Stems measuring ≥ 0.6·W flat ≤ **25 % of beat power**; protagonist leads summed near-white stems by **≥ +8 dB, every beat** | beat 1: 92.6 %; beats 1/4/5: −12.01/+0.11/+0.03 dB | stem-level, because the *mix* is the final flattening step |
| **G-NOVEL** | Envelope autocorrelation max over lags 0.3–16 s **≤ 0.15**, every beat | beat 1: 0.396 @ 1.380 s | floor 0.016 (noise), ceiling 0.708 (tiled loop) |
| **G-MOD** | Modulation-spectrum peak-to-local-median, 0.2–3 Hz **≤ 4 dB** | single 0.722 Hz peak, next partial 7.3 dB down | — |
| **G-GESTURE** | Pairwise burst similarity mean **≤ 0.55**, max **≤ 0.80** | ≈0.95 | C6 is its control |
| **G-ROOM (a) density** | Within 20 dB of Weyl 4πVf²/c³ = **1336 modes/Hz @ 1 kHz** | 0.4255 → short by 70 dB | Weyl's law, V = 4290 m³ |
| **G-ROOM (b) mobility** | Peak recurrence across bursts **≤ 35 %** | room 68 % / **dry source 32 %** | the dry stem is its own negative control |
| **G-ROOM (c) ripple** | Cepstral peak 1–30 ms **≤ 1.5× median**; 1/12-oct ripple p95−p5 0.4–6 kHz **≤ 8 dB** | ≈8×; 17.6 dB L / 16.5 dB R | — |
| **G-ORDER** | ≥ **60 %** of 300–4000 Hz energy within ±1.5 % of a predicted line f = 1.5·k·rpm/60, rpm from **telemetry, not estimated from audio** | — | telemetry is independent ground truth; this is what C3 fails |
| **G-IDENTITY** | order 1.5 present at ≈ −5.3 dB rel. order 3; order-6 notch **≥ 6 dB** below orders 4.5 and 7.5 | today's engine has order-1.5 amplitude **identically 0.0000** | derived, verified to 1e-12; bar deliberately loose and marked DERIVED-NOT-MEASURED |

---

## 6. WHAT WOULD MAKE ME ABANDON THIS APPROACH

1. **B2 lands and the client hears no difference.** The comb deletion is the sharpest, cheapest prediction in the spec — the cepstrum says it is the largest feature in the first 30 seconds. If removing it is inaudible in a blind A/B, the diagnosis has mislocated the percept and the whole tube branch (B3, B4) is suspect. This is why B2 ships alone, on day one.
2. **The new master passes all of Tier 3 and a listener still says "blower".** Correct response: add that listener's word to the control corpus as a new negative control and go find the metric that separates it. **Never retune a threshold.** If two such rounds happen, the metric-driven approach is abandoned and we go to iterative listening with the gates demoted to regression-only.
3. **The picture is locked and B5 cannot land.** Then the 1.375 s / 1.042 s ladder survives at reduced r. I would say so plainly rather than claim the period was removed, and re-plan around B3 + B6 alone — honest promise drops to "not a hair dryer, still somewhat regular".
4. **Over-correction.** If beat 1 comes back reading dry, small and synthetic, the target was wrong. G-FLAT's bar is 0.30·W, **not zero** — a real showroom has air, HVAC and contact noise. If we hit 0.10·W and the client calls it thin, back off the CFRP damping and the Hertzian bandwidth rather than adding noise back.
5. **The uneven-firing A/B loses.** `engine.py:292-297` may be right about the shared collector. If the client picks `half_order_weight = 0.0`, keep it at 0.0 and delete G-IDENTITY — do not enforce a physical claim we could not corroborate against a measured spectrum.
6. **Velvet convolution cannot hit RT60 within budget.** If a 2.4 s tail at 96 kHz per source position blows the render, fall back to a **16-line mutually-prime FDN with 8 allpass diffusion stages** and widen G-ROOM(a) *with a written justification*. The failure mode to avoid is exactly the one that produced `BEAT_HNR_LIMITS`: quietly deleting the gate that will not pass.

**Files that will change:** `audio/layers.py` (:167-168, :285-340, :344-391), `audio/dsp.py` (:362-411), `audio/master.py` (:521-537), `audio/engine.py` (:136, :183-185, :292-310, :514-529, :607-630), `world/beat1_anim_anim.json`, plus new `audio/percept.py`, `tools/percept_matrix.py`, `tools/calibrate_hnr.py`, `audio/controls/`. `audio/verify.py` loses `harmonic_gate`, `waveguide_gate` and `BEAT_HNR_LIMITS` entirely.

---

# SUPPORTING DIAGNOSIS (measured)

```json
[
 {
  "findings": [
   {
    "claim": "THE WIND BLOWER IS LITERAL: in the 500-3000 Hz band, the first 30 seconds is 98.6% as spectrally flat as white noise. This is the single number that explains the percept.",
    "evidence": "Tilt-free spectral flatness (SFM computed inside each 1/3-octave band then averaged, so spectral TILT cannot contaminate it) over 500-3000 Hz, beat 1 (0-33 s) = 0.5808. Literal white noise through the identical STFT pipeline = 0.5891. Ratio = 98.6%. The octave-matched hair-dryer control built from the master itself (verify.py's own adversary, _hairdryer_like) = 0.6119, so the master's first 30 s is 94.9% as flat as a hair dryer. For contrast, beat 2 (launch, engine exposed) = 0.1603 = 27.2% of white. Beat 1 is 3.6x flatter than the one beat that sounds like an engine. NOTE: the whole-band SFM looks reassuring (0.0142) but that number is measuring the mix's low-frequency tilt, not its tonality - which is why nobody caught this.",
    "explains_which_percept": "wind blower"
   },
   {
    "claim": "The flatness is CONSTANT for the entire 33 seconds - it is not a transient, a fade, or one bad moment. Every three-second slice of beat 1 reads near-white.",
    "evidence": "SFM(500-3000 Hz) per 3 s slice across beat 1: 0.584, 0.587, 0.610, 0.594, 0.589, 0.542, 0.573, 0.568, 0.538, 0.592, 0.584. Range 0.538-0.610 against a white-noise reference of 0.5891. The minimum slice is still 91% of white noise. There is no window in the client's 'first 30 seconds' that is not noise-dominated.",
    "explains_which_percept": "wind blower"
   },
   {
    "claim": "47.0% of beat 1's energy is genuinely aperiodic noise, measured with a calibrated true harmonic-to-noise ratio. The listener is hearing a near-even mix of noise and signal where an engine should be 90%+ periodic.",
    "evidence": "Boersma autocorrelation HNR (Praat's method, the textbook HNR) on beat 1 = +0.52 dB median -> 47.0% of power aperiodic (IQR 37-56%). 42.1% of beat-1 windows sit BELOW 0 dB, i.e. more noise than signal. The octave-matched hair dryer scores -2.44 dB, so the delivered first 30 s sits only +2.96 dB above a literal hair dryer. INSTRUMENT CALIBRATED FIRST: on synthetic mixtures of a 145 Hz harmonic comb plus bandpassed noise at known noise fractions, this measure returned 16.98/12.86/9.62/4.88/0.22 dB against truths of 16.90/12.79/9.54/4.77/0.00 dB - error <=0.22 dB across the whole range that matters here.",
    "explains_which_percept": "wind blower"
   },
   {
    "claim": "The source is named: 92.6% of the first 30 seconds' power comes from two stems that are themselves near-white noise, and the engine stem sits 12.01 dB BELOW them.",
    "evidence": "Beat-1 stem power budget (stems read at their true 96 kHz rate): assembly 46.7% (SFM 0.5281 = 84.5% of white), room 45.9% (SFM 0.5078 = 81.2% of white), engine 5.9%, crowd 1.4%, structure and wind ~0%. Engine-to-everything-else = -12.01 dB. Eight of sixteen stems are digital silence through beat 1 (aperture, bed, fence, impact, reflect_garage, reflect_showroom, shards, tyres). Two independent 82-85%-flat noise sources summing is exactly what produces the master's 98.6% - the mix itself is the final flattening step, because decorrelated noise fills in each source's spectral valleys.",
    "explains_which_percept": "wind blower"
   },
   {
    "claim": "THE WIND BLOWER IS NOT ONLY BEAT 1 - it runs through the whole film. On the flying lap, half the running time, the engine and the broadband noise bed are mixed at EQUAL power, 0.03 dB apart.",
    "evidence": "Engine stem power vs summed other stems, per beat: 1_assembly -12.01 dB, 2_launch +15.07 dB, 4_transit +0.11 dB, 5_lap +0.03 dB, 6_ending -17.25 dB. On beat 5 (49.6-113.1 s, 63.5 s = 51% of the film) the wind stem alone is 36.4% of power at 79.2% of white-noise flatness, tyres 5.5% at 93.3% of white, against engine 50.2%. Restricting to stems MEASURED near-white (>=75% of white flatness): the engine leads them by only +0.32 dB. Four of six beats have the engine at or below the noise bed. Only beat 2 (3.0 s, 2.4% of the film) has the engine clearly on top.",
    "explains_which_percept": "wind blower"
   },
   {
    "claim": "THE GATE CANNOT SEE A WIND BLOWER BY CONSTRUCTION. Its metric has no f0 estimate and no harmonicity test - it only asks 'are there narrow peaks', and noise through any resonator has narrow peaks. I proved it: a literal wind blower pointed into a rack of tubes PASSES beat 1's gate with MORE margin than the delivered master.",
    "evidence": "audio/verify.py:1123 hnr_profile - docstring states 'with NO f0 estimate'; it subtracts a 269.5 Hz-wide running median (23 bins x 11.72 Hz) and calls everything above it 'tonal'. I synthesised a literal wind blower into tubes (white noise -> bank of high-Q peaking filters at inharmonic pipe modes 187/242/332/452/614 Hz; zero line spectrum, zero periodicity) and ran the SHIPPED metric on it. Beat-1 gate limits are hf<-1.0 dB permitted on 0.85 of windows, bb<-1.0 dB on 0.30. Tubes at Q=28: hf frac 0.481, bb frac 0.001 -> PASS. Tubes at Q=80: bb median +4.04 dB, hf frac 0.002 -> PASS, and +4.04 dB is above the gate's 2.0 dB ENGINE bar. Delivered master beat 1: hf frac 0.708, bb frac 0.046 -> PASS, i.e. the master passes with LESS margin than a literal hair dryer in a pipe. The only signal that fails is flat white noise (frac 1.000) - which is precisely the one adversary (_hairdryer_like: octave-matched white noise, no resonances) the thresholds were calibrated against.",
    "explains_which_percept": "both"
   },
   {
    "claim": "The gate's thresholds LICENSE the defect rather than testing for it. Beat 1's bar is a noise generator's score, and 85% of the beat is permitted to sit below even that. 76.5% of the film is held to a noise floor or explicitly excused from the engine bar.",
    "evidence": "BEAT_HNR_LIMITS (verify.py:864): beat 1 threshold -1.0 dB - which the gate's own comment at HNR_NOISE_FLOOR_DB defines as 'one decibel above what this metric reads on something with no line spectrum at all' - with 0.85 of windows permitted below it. The delivered master reads 0.707 (from the project's own audio/out/hnr_evidence.json; my independent reproduction gives 0.708, confirming my instrument). So the gate PASSED beat 1 while measuring that 70.7% of the client's 'first 30 seconds' scores below a noise generator. Summing seconds held only to a -1.0 dB noise floor (beats 1, 3, 6) plus the fractions explicitly permitted below the 3.0 dB engine bar (beats 2, 4, 5): 94.9 s of 124.1 s = 76.5% of the film. Worse, the limits are self-referential - verify.py:816 sets each one at 'the midpoint between what THIS master reads and what the adversary reads', so the bar was drawn from the artefact it was meant to judge. A gate calibrated to the defect cannot fail the defect.",
    "explains_which_percept": "both"
   },
   {
    "claim": "BONUS, SAME ROOT CAUSE - 'The Tubes over and over' is a measurable 1.374 s loop running ~24 times through beat 1, and what loops is 61 FIXED INHARMONIC resonances. That is the literal physical definition of banging on tubes.",
    "evidence": "Autocorrelation of beat 1's amplitude envelope in the 500-3000 Hz band: strongest peak r = 0.585 at 1.374 s, with peaks at every integer multiple - 2.754 s (r=0.542), 4.133 s (0.427), 5.509 s (0.325), 6.880 s (0.322), 8.260 s (0.222). A clean harmonic ladder of lags means one cycle repeating, ~24 times in the 33 s beat. What is being re-excited: 61 fixed narrowband peaks standing 6.2-9.4 dB above the smooth spectral envelope (187.5, 257.8, 427.7, 955.1, 1148.4, 1593.8, 3814.5, 4500.0, 5226.6, 5677.7, 5771.5, 5918.0 Hz among the strongest), with spacing median 87.9 Hz but sd 50.8 Hz - NOT a constant spacing, so NOT a harmonic comb. Fixed, inharmonic, high-Q modes re-struck on a fixed cycle. Both client percepts are one construction: a noise bed carrying the energy, a bank of fixed inharmonic resonances looping on top, and no harmonic engine comb present to mask either.",
    "explains_which_percept": "tubes"
   }
  ],
  "summary": "The client is right and the gates are wrong, and I can put a number on both.\n\nTHE WIND BLOWER IS LITERAL, NOT A METAPHOR. In the 500-3000 Hz band - where the ear is most sensitive and where a hair dryer lives - the first 30 seconds of the delivered master is 98.6% as spectrally flat as white noise (0.5808 vs 0.5891 measured through the identical pipeline), and 94.9% as flat as an octave-matched hair dryer built from the master itself. The engine beat, for contrast, reads 27.2% of white. That flatness holds across every 3-second slice of the beat (0.538-0.610), so there is no moment of the client's \"first 30 seconds\" that is not noise-dominated. A calibrated Boersma harmonic-to-noise ratio agrees: +0.52 dB, meaning 47.0% of beat-1 energy is aperiodic, with 42.1% of windows carrying more noise than signal, sitting just +2.96 dB above a literal hair dryer. I calibrated that instrument against synthetic mixtures of known noise fraction before trusting it (error <=0.22 dB).\n\nTHE SOURCE HAS A NAME. 92.6% of beat-1 power is two stems, `assembly` (46.7%) and `room` (45.9%), which are themselves 84.5% and 81.2% white. The engine stem is 5.9%, sitting 12.01 dB BELOW them. Summing two decorrelated near-white sources is what takes the mix from ~82% to 98.6% flat - the mix is the final flattening step.\n\nAND IT IS NOT ONLY BEAT 1. Engine-to-everything-else per beat: assembly -12.01 dB, launch +15.07, transit +0.11, lap +0.03, ending -17.25. On the flying lap - 63.5 s, half the film - the engine and the broadband bed are mixed at equal power, 0.03 dB apart, with the `wind` stem alone at 36.4% of the beat. Only beat 2, which is 3.0 s and 2.4% of the running time, actually has an engine on top. The client's complaint generalises further than they stated it.\n\nWHY EIGHT GATES PASSED. The gate's metric (verify.py:1123 `hnr_profile`) states in its own docstring that it works \"with NO f0 estimate\": it subtracts a 269.5 Hz-wide running median and calls whatever pokes above it \"tonal\". It never checks that peaks fall on integer multiples of anything. Noise through any resonator makes peaks. So I built the client's complaint as a signal - white noise through a bank of high-Q inharmonic pipe resonances, zero line spectrum, zero periodicity - and ran the shipped metric on it: it PASSES beat 1's gate with more margin than the delivered master does (fraction-below 0.481 vs the master's 0.708 against a 0.85 limit), and at Q=80 it scores +4.04 dB, clearing the gate's 2.0 dB *engine* bar. The only thing this gate can fail is flat white noise, which is exactly the single adversary its thresholds were tuned against.\n\nWorse, the thresholds encode the defect as the specification. Beat 1's bar is -1.0 dB, which the code's own comment defines as one decibel above a signal with no line spectrum at all, and 85% of the beat is permitted below even that. The master reads 0.707 - so the gate passed beat 1 having measured that 70.7% of it scores below a noise generator. Across the film, 94.9 s of 124.1 s (76.5%) is either held only to that noise floor or explicitly excused from the engine bar. And verify.py:816 sets every limit at \"the midpoint between what THIS master reads and what the adversary reads\", so the bar was drawn from the artefact it judges. That is this project's recurring defect in its purest form: a metric that reads the same whether the defect is present or absent, because it was calibrated on the defect.\n\nTHE TUBES ARE THE SAME DEFECT FROM ANOTHER ANGLE. Beat 1's envelope autocorrelates at r=0.585 on a 1.374 s period with a clean ladder of integer-multiple lags - one cycle repeating about 24 times in 33 seconds. What repeats is 61 fixed narrowband resonances 6-9 dB above the envelope, spaced median 87.9 Hz with sd 50.8 Hz, i.e. inharmonic, not a comb. Fixed inharmonic high-Q modes re-struck on a loop is the physical definition of banging on tubes. Both percepts are one construction: a noise bed carrying the energy, fixed inharmonic resonances looping on top, and no harmonic engine comb present to mask either.\n\nRecommendation for whoever fixes this: the HNR gate must be replaced, not retuned - add an f0 estimate and score energy on an integer comb, gate on tilt-free per-band flatness against a white reference, and set thresholds from physics or from a real engine's published spectrum, never from the master under test. Scripts and JSON are in SCRATCHPAD/aud/ (stage1-stage7.py, stage1-stage5.json)."
 },
 {
  "findings": [
   {
    "claim": "The \"over and over\" is a literal metronome: 12 identical impact bursts spaced EXACTLY 1.375 s apart (0.7273 Hz, 43.6 BPM), running 13.83 s to 29.29 s.",
    "evidence": "Master envelope autocorrelation peaks at lag 1.3760 s (r=0.612) with integer harmonics at 2.7573 s (r=0.496), 4.1280 s (r=0.465), 5.5253 s (r=0.336). Modulation spectrum of the 150-8000 Hz envelope over 12-30 s has ONE dominant peak at 0.722 Hz (period 1.384 s); the next partial is 7.3 dB down. Log-spectrum self-similarity peaks at 1.3653/2.7520/4.1173/5.5040/6.8693 s. On the dry assembly stem the 12 loud regions start at 13.85, 15.20, 16.55, 17.95, 19.35, 20.80, 22.10, 23.45, 24.85, 26.20, 27.60, 28.95 s \u2014 gaps 1.30-1.45 s, mean 1.373 s, sd 0.036 s (2.6%). Root cause: world/beat1_anim_anim.json at contract 1.2.1 (git 19a55b3) has cluster seat frames 333, 366, 399 ... 696 \u2014 33 frames apart at 24 fps = 1.375000 s exactly, 12 of them. Predicted first-hit times (13.8333, 15.2083, 16.5833, 17.9583, 19.3333, 20.7083, 22.0833, 23.4583, 24.8333, 26.2083, 27.5833, 28.9583 s) match all 12 measured onsets to within one 0.05 s analysis bin.",
    "explains_which_percept": "tubes"
   },
   {
    "claim": "Every burst has the identical shape and the identical internal rhythm \u2014 0.3333 s of hits then ~1.04 s of nothing but reverb \u2014 so the ear gets the same gesture twelve times, with a 15.3 dB level swing.",
    "evidence": "Every one of the 15 clusters has last_land - seat_frame = 8 frames = 0.33333 s, and layers.assembly:367 places parts at fr = seat + (last-seat)*(p/(nparts-1)), i.e. EXACTLY equal time steps. Intra-burst repetition rate is therefore exactly 3*(n_parts-1) Hz: MB 48.0, FD 27.0, BB 27.0, EC 36.0, CI 42.0, SW 192.0, halo 156.0, SP 36.0, NOSE 96.0, FW 357.0, RW 288.0, CORNER_* 120.0/129.0 Hz. 616 impacts total in 16.0 s. Measured loud-region durations 0.50-0.55 s (0.333 s of hits + ring-out), leaving 0.82-0.87 s of gap. Master short-term band level (150-8000 Hz), 12-30 s: p95-p5 = 15.3 dB.",
    "explains_which_percept": "tubes"
   },
   {
    "claim": "The impact voice IS a struck tube by construction \u2014 four exponentially-decaying sines at the inharmonic ratios 1 : 2.31 : 3.87 : 6.1, which is the timbre of a struck metal bar/pipe, not of a carbon car part landing.",
    "evidence": "audio/layers.py:376-378: `for k, amp in ((1.0,1.0),(2.31,0.45),(3.87,0.22),(6.1,0.10)): hit += amp*sin(2*pi*fp*k*tt)*exp(-tt/(dur*0.28/k**0.5))`, plus a 4 ms noise click, per impact. 616 of these in 16 s. Pitch fp = f0*U(0.82,1.9) where f0 = 210/volume^(1/3); 7 of the 15 clusters (450 of the 616 impacts: BB, halo, FW, RW and the four CORNERs) have f0 inside 251.8-273.0 Hz, so nearly three-quarters of the hits ring from the same 22 Hz-wide pitch centre.",
    "explains_which_percept": "tubes"
   },
   {
    "claim": "Half of the first 30 seconds is reverb, and that reverb is an 8-tap comb whose resonances are FIXED. 13 narrow lines sit 10-19 dB above the local spectrum and every one of them is a harmonic of an FDN delay line, matched to 0.01-0.93%.",
    "evidence": "Bus levels over 0-30 s: assembly -36.34 dBFS, room -36.46 dBFS (room = 49.3% of the power), crowd -52.03 dBFS, wind -125.03 dBFS. Measured fixed lines in the room stem: 241.70, 260.74, 278.32, 430.66, 711.9, 955.1, 989.4, 1423.8, 1595.8, 3811.5, 5223.6, 5935.6, 7438.5 Hz. The showroom FDN (layers.showroom_tail, 30 x 22 x 6.5 m, c=343.2158 m/s, sr=96 kHz) has 8 delay lines of 1818/3077/4196/4293/5203/5282/6417/10563 samples, comb spacings 52.8053/31.1992/22.8789/22.3620/18.4509/18.1749/14.9603/9.0883 Hz. 241.70/260.74/278.32 Hz are harmonics 13/14/15 of the 18.4509 Hz comb of the 18.60 m line (predicted 239.86/258.31/276.76, errors 0.76/0.93/0.56%). 430.66 = h29 of the 22.94 m line (err 0.74%); 1423.83 = h27 of the 6.50 m line (0.13%); 1596.68 = h88 of the 18.88 m line (0.17%); 3811.52 = h255 (0.09%); 5223.63 = h283 (0.04%); 5935.55 = h653 (0.01%); 7438.48 = h403 (0.04%). Spectral autocorrelation over 100 Hz-12 kHz gives comb spacing 90.82 Hz at r=0.420. In the master, 3 lines x 6 Hz = 18% of the 200-300 Hz band carries 41.5% of that band's power.",
    "explains_which_percept": "tubes"
   },
   {
    "claim": "THE TELL-TALE: the resonance does not move with what is being struck. Across the 12 bursts the source's pitch moves 226 -> 864 Hz, but the room answers with the same handful of frequencies to 0.01-0.07% \u2014 430.2 Hz recurs in 7 of 12 bursts with a total spread of 0.27 Hz.",
    "evidence": "Per-burst top-8 spectral peaks, 12 bursts. DRY assembly: centroid mean 418.2 Hz, sd 161.6 Hz (38.6%), range 226-864 Hz; 96 peak observations -> 62 distinct frequencies (1% tolerance), only 32% recurring in >=3 bursts. ROOM (FDN tail): 96 peak observations -> 37 distinct frequencies, 68% recurring in >=3 bursts. Recurrences: 430.2 Hz in 7/12 (spread 0.27 Hz = 0.06%), 1595.8 Hz in 7/12 (0.37 Hz = 0.02%), 1418.0 Hz in 8/12, 989.4 Hz in 4/12 (0.09 Hz = 0.01%), 712.3 Hz in 4/12 (0.03%), 278.8 Hz in 4/12 (0.07%), 242.5 Hz in 3/12 (0.15%), 192.7 Hz in 3/12 (0.19%). Peak-tracking across six 5 s windows of the room stem gives sd 0.056-0.402% for 241.7/260.7/278.3/430.7/1596.7/3811.5 Hz. Note the dry source is its own negative control here: it scatters, the room does not.",
    "explains_which_percept": "tubes"
   },
   {
    "claim": "A hard, fixed COMB FILTER is printed on the entire reverb bus by the stereo decorrelation \u2014 141.0 Hz spacing in the left ear, 88.6 Hz in the right. The delay is confirmed sample-exact by the cepstrum. This is the single most direct cause of a hollow, tube-like colour.",
    "evidence": "audio/master.py:530-532: `d1, d2 = int(0.0071*sr), int(0.0113*sr)` (681 and 1084 samples at 96 kHz = 7.0938 and 11.2917 ms); L = tail*0.75 + delay(tail,d1)*0.35, R = delay(tail,d2)*0.75 + tail*0.30. Real cepstrum of the room stem: L peaks at q = 7.0938 ms (c=0.2278, 141.0 Hz spacing), R peaks at q = 11.2917 ms (c=0.1975, 88.6 Hz spacing) \u2014 both EXACTLY the coded delays, and both roughly 8x the next cepstral peak. Mono sum carries both (11.2917 ms c=0.3403, 7.0938 ms c=0.1514) and it is the largest cepstral feature in the whole master over 0-30 s. Predicted ripple from the coefficients alone: 20*log10(1.10/0.40) = 8.79 dB peak-to-notch every 141.0 Hz (L), 20*log10(1.05/0.45) = 7.36 dB every 88.6 Hz (R). Measured ripple over 0.4-6 kHz, 13-30 s: L p95-p5 = 17.60 dB, R = 16.51 dB (decorrelation comb plus the FDN comb superimposed).",
    "explains_which_percept": "tubes"
   },
   {
    "claim": "The comb lines ring 1.4-1.9x LONGER than the reverb's own declared RT60, so they are heard as pitched resonators sustaining between the bursts rather than as a room decaying.",
    "evidence": "showroom_tail declares rt60_low = 2.4 s, rt60_high = 0.85 s. Measured band-filtered energy decay in the room stem across the 22.35-23.55 s inter-burst gap: 241.7 Hz -13.03 dB/s -> T60 4.60 s; 260.7 Hz -17.29 dB/s -> T60 3.47 s; 1596.7 Hz -19.80 dB/s -> T60 3.03 s; 430.7 Hz -26.80 dB/s -> T60 2.24 s. Structural reason: 8 delay lines totalling 425.5 ms give a modal density of 0.4255 modes/Hz against Jot's bar of 0.15 x T60 = 0.36 for a 2.4 s tail, with no diffusing allpass stages anywhere in dsp.fdn_reverb \u2014 so the tail is a comb bank, not a diffuse field.",
    "explains_which_percept": "tubes"
   },
   {
    "claim": "Before the first burst (0 - 13.83 s) there is no wind layer at all; what sounds like a blower is the assembly layer's \"servo whir\" \u2014 a motor whine sweeping 232-409 Hz on a 9 s cycle sitting on a fixed 900-6000 Hz hiss band.",
    "evidence": "Wind bus max|x| over 0-30 s = 4.26e-06 (-125.03 dBFS). layers.assembly:387-391: f_srv = 320 + 90*sin(2*pi*0.11*t); srv = sin(phase)*0.5 + sin(2.7*phase)*0.2 + bandpass(white, 900, 6000)*0.6 \u2014 the noise term has the largest coefficient. Measured in the file: the 200-460 Hz spectral centroid sweeps between 231.6 Hz and 409.2 Hz (coded extremes 230 and 410), with maxima at t = 0.19 s and t = 9.11 s -> period 8.92 s (coded 1/0.11 = 9.09 s). Long-term average of the assembly stem over 0-9 s peaks at 234.4 Hz (+29.7 dB) and 407.2 Hz (+23.6 dB) \u2014 the two LFO turning points, where the sweep dwells. Master power split over 0-13.5 s: 37.0% below 120 Hz (50/100 Hz mains hum from room_tone), 32.9% in 120-500 Hz (the whine), 22.2% in 900-6000 Hz (the hiss); 33.0% of all power is non-tonal broadband.",
    "explains_which_percept": "wind blower"
   },
   {
    "claim": "The first 30 seconds contains only TWO sources: the impacts and the reverb of those same impacts. Twelve of the sixteen buses are digitally, exactly zero.",
    "evidence": "max|x| over 0-30 s per bus: engine 0.000e+00, tyres 0.000e+00, structure 0.000e+00, impact 0.000e+00, shards 0.000e+00, bed 0.000e+00, aperture/fence/reflect_garage/reflect_showroom silent; wind 4.258e-06; crowd 2.239e-02 (-52.03 dBFS, 16 dB under the other two); room 2.442e-01 (-36.46 dBFS); assembly 2.867e-01 (-36.34 dBFS). There is nothing else for the listener to attend to.",
    "explains_which_percept": "both"
   },
   {
    "claim": "The eight passing gates are structurally incapable of seeing any of this: four of them (pitch, doppler, harmonic, waveguide) measure the engine, and the engine bus is exactly 0.0 for every one of the first 1,440,000 samples. No gate measures envelope periodicity, modulation spectrum, reverb modal density, comb depth, or fixed-resonance recurrence.",
    "evidence": "verify_report.json gate_summary = {levels, edges, seam, external_assets, pitch, doppler, harmonic, waveguide} all true. engine.wav max|x| over 0-30 s = 0.000000e+00 exactly. levels/edges/seam/external_assets are loudness, boundary, splice and provenance checks \u2014 none has a periodicity or spectral-flatness term. A beat 1 made entirely of a 43.6 BPM metronome through a fixed 141 Hz comb passes all eight without a single row moving.",
    "explains_which_percept": "neither"
   },
   {
    "claim": "PROVENANCE WARNING before anyone \"fixes\" this by rebuilding: the delivered master was rendered against the 33-frame (1.375 s) beat-1 schedule, but the schedule now on disk is 25 frames (1.0417 s). A rebuild today makes the metronome FASTER, not absent.",
    "evidence": "audio/out/master.wav is dated Aug 8 02:48; world/beat1_anim_anim.json was rewritten Aug 8 18:10. git 19a55b3 (contract 1.2.1) has seat frames 333..696 at 33-frame spacing = 1.375 s \u2014 this reproduces all 12 measured onsets. git 6e0b37e (current HEAD) has seat frames 238..513 at 25-frame spacing = 1.0417 s, which predicts bursts at 9.875-21.333 s; the file has no impact energy before 13.5 s and plenty at 29 s, so HEAD's schedule is NOT what is in the delivered master. Impact count is 616 and cluster count 15 in both, matching master_report.json assembly = {impacts: 616, clusters: 15}, so the count check cannot tell the two schedules apart either.",
    "explains_which_percept": "tubes"
   }
  ],
  "summary": "\"The Tubes over and over\" is not a vague impression \u2014 it is two exactly measurable mechanisms, and both are in the source code.\n\nTHE PERIOD IS 1.375000 s. Beat 1's soundtrack is twelve impact bursts spaced exactly 33 frames apart at 24 fps (0.7273 Hz, 43.6 BPM), running 13.83 s to 29.29 s. Envelope autocorrelation gives lag 1.3760 s at r=0.612 with clean 2x/3x/4x harmonics; the modulation spectrum has a single dominant peak at 0.722 Hz with the next partial 7.3 dB down. Every burst is the same shape: exactly 0.3333 s of impacts (parts placed at mathematically equal time steps, giving repetition rates of exactly 3*(n_parts-1) Hz) followed by ~1.04 s of nothing but reverb, with a 15.3 dB level swing. Twelve times. That is a metronome, not a car being assembled.\n\nTHE TUBE IS THE REVERB, AND IT IS HALF THE MIX. Over 0-30 s the room bus (-36.46 dBFS) is level with the direct assembly bus (-36.34 dBFS) \u2014 49.3% of the power. That reverb is an 8-tap FDN with no diffusion stages, and its thirteen strongest narrow lines (241.70, 260.74, 278.32, 430.66, 711.9, 955.1, 989.4, 1423.8, 1595.8, 3811.5, 5223.6, 5935.6, 7438.5 Hz) are every one a harmonic of a delay line, matched to 0.01-0.93%. The 241.70/260.74/278.32 Hz triplet is harmonics 13/14/15 of the 18.4509 Hz comb of the 18.60 m line. Those lines ring at T60 3.0-4.6 s against a declared RT60 of 2.4 s.\n\nTHE FIXED-RESONANCE TELL IS PRESENT AND MEASURED. Across the 12 bursts the dry source's centroid moves 226 -> 864 Hz (sd 38.6%) and its peaks scatter across 62 distinct frequencies; the room's answer collapses onto 37, with 430.2 Hz recurring in 7 of 12 bursts inside a 0.27 Hz spread (0.06%) and 989.4 Hz in 4 of 12 inside 0.09 Hz (0.01%). Whatever you strike, the room replies at the same pitches. The dry stem is its own negative control.\n\nAND THERE IS A LITERAL COMB FILTER ON THAT BUS. master.py's stereo decorrelation adds the tail to itself delayed by 681 samples (left) and 1084 samples (right). The cepstrum finds those delays sample-exact \u2014 7.0938 ms / 141.0 Hz spacing in L, 11.2917 ms / 88.6 Hz in R \u2014 as the largest cepstral feature in the whole first 30 seconds, with 16.5-17.6 dB of measured ripple. A fixed comb across the whole spectrum is the definition of a hollow tube.\n\nThe \"wind blower\" in this window is the assembly layer's servo whir, not the wind bus (which is at -125 dBFS): a motor whine sweeping 231.6-409.2 Hz on an 8.92 s cycle over a fixed 900-6000 Hz hiss that carries 22.2% of the power. Twelve of the sixteen buses are exactly 0.0 for the entire first 30 seconds.\n\nWhy all eight gates pass: four of them (pitch, doppler, harmonic, waveguide) measure the engine, and the engine bus is exactly zero for all 1,440,000 samples of this window. No gate measures periodicity, modulation depth, modal density, comb ripple, or resonance recurrence. Beat 1 could be a metronome through a comb filter \u2014 it is \u2014 and every gate reads green.\n\nOne warning: the delivered master was built from the contract-1.2.1 schedule (33 frames, 1.375 s). The schedule on disk today is 25 frames (1.0417 s). Rebuilding without addressing the mechanism makes the metronome faster, not absent \u2014 and the impact/cluster counts (616/15) are identical between the two, so master_report.json cannot tell them apart.\n\nScripts: SCRATCHPAD/aud/ (per.py, per2.py, band.py, spec.py, comb.py, onset.py, burst.py, dry.py, fdn.py, fixed.py, stat.py, servo.py, servo2.py). Sources implicated: audio/layers.py:344-391 (assembly + servo whir), audio/layers.py:198-215 (showroom_tail), audio/dsp.py:362-411 (fdn_reverb), audio/master.py:523-532 (excitation and the decorrelation comb)."
 },
 {
  "findings": [
   {
    "claim": "THE SUITE CANNOT TELL THE FILM'S FIRST 33 SECONDS FROM A TAPE LOOP. I took the delivered master, replaced only beat 1 with a single 2.000 s synthesised block tiled 16.5 times (20 ms crossfade at the splice into beat 2, renormalised to -14.00 LUFS / -1.23 dBTP), and ran audio/verify.py unmodified. All eight gates PASS, ALL_PASS=True, exit 0, '>> STAGE RESULT: AUDIO_VERIFY_OK'.",
    "evidence": "tmp/gateaudit/swap_b1_loop.wav -> {\"levels\": true, \"edges\": true, \"seam\": true, \"external_assets\": true, \"pitch\": true, \"doppler\": true, \"harmonic\": true, \"waveguide\": true}. The harmonic gate scores that looped beat 1 at hnr_above_2k6 = +34.454 dB with fraction_below = 0.000 of a permitted 0.85 \u2014 versus the DELIVERED beat 1 at -1.416 dB and 0.707. The suite does not merely fail to catch the loop, it rates a 2-second loop as 35.9 dB better than the film it passed.",
    "explains_which_percept": "both"
   },
   {
    "claim": "harmonic_gate \u2014 the gate written specifically to catch 'hair blower' \u2014 PASSES a naive looped oscillator outright, and rates it the best signal it has ever scored. Quantity: median-filtered spectral floor, tonal energy above the floor over the floor's own energy, per 43 ms window, gated on the FRACTION of a beat below a per-beat dB threshold. It is a per-window statistic aggregated by a fraction, so it is mathematically invariant to whether the windows are all different or all identical.",
    "evidence": "degen_loop.wav (one 2 s block tiled 63x over the whole 124.083 s) -> harmonic PASS=True, all six beats gated, zero failures, hf = +43.814 dB and bb = +29.695 dB IDENTICALLY on every beat, fraction_below = 0.000 on all twelve limbs. Delivered master's best beat (2_launch) is +8.059 dB. A struck tube is extremely tonal, so it scores 5.4x the film's best.",
    "explains_which_percept": "tubes"
   },
   {
    "claim": "The delivered beat 1 measures 0.577 dB above a LITERAL NOISE GENERATOR on the very statistic written to catch a hair dryer, and the gate's threshold for that beat is deliberately set at the noise floor with 85% of windows permitted below even that. BEAT_HNR_LIMITS['1_assembly']['hf'] = (HNR_NOISE_FLOOR_DB=-1.0, 0.85), where HNR_NOISE_FLOOR_DB is documented as 'one decibel above what this metric reads on something with no line spectrum at all'. Beat 1 is not measured as an engine \u2014 it is exempted from the engine test by name.",
    "evidence": "Measured with verify.hnr_profile on the master and on verify._hairdryer_like(master) (the suite's own literal hair dryer), median hnr_above_2k6 per beat: 1_assembly film -1.416 / noise -1.993 -> margin +0.577 dB. Compare 2_launch +10.156, 5_lap +7.829, 4_transit +5.888. Beat 1 is 26.6% of the film and is the beat the client named.",
    "explains_which_percept": "wind blower"
   },
   {
    "claim": "THREE OF THE EIGHT GATES NEVER OPEN THE DELIVERED WAV AT ALL. external_assets is an AST scan of audio/*.py. pitch re-synthesises the DRY engine from the telemetry on a world clock and tracks THAT. waveguide root-solves engine.py's pipe constants algebraically. None of the three takes the artefact as input, so none can distinguish any two audio files \u2014 and all three passed 100% white noise.",
    "evidence": "verify.py main(): scan_external([PKG]) reads source only; V['pitch'] runs eng_mod.synth(...) then track_f0(dry, ...); V['waveguide'] = waveguide_gate() takes no signal argument. All three PASS on degen_noise.wav, degen_loop.wav, degen_blower_plus_tubes.wav, swap_b1_noise.wav and swap_b1_loop.wav \u2014 5 of 5 degenerate inputs.",
    "explains_which_percept": "both"
   },
   {
    "claim": "waveguide_gate PASSES ONLY BECAUSE OF ITS ONE FREE PARAMETER. It evaluates ring-through at a hand-chosen WAVEGUIDE_RPM = 11000.0, while its own comment states the film's rpm_at_vmax is 13,143. Re-run at the film's actual peak rpm the same gate FAILS its own threshold. It also examines only engine.py's three exhaust elements \u2014 the beat-1 tube ringing lives in layers.assembly and in the showroom FDN, which it cannot see.",
    "evidence": "waveguide_gate() with WAVEGUIDE_RPM swept: 8000 -> median 3.529 / worst 5.304 PASS; 11000 (shipped) -> 4.852 / 7.293 PASS (limits 5.0 / 9.0 \u2014 a 3.0% margin on the median); 13143 (the film's own rpm_at_vmax) -> 5.798 / 8.714 PASS=False. layers.assembly builds 616 impacts across 15 clusters with partial ratios 1 : 2.31 : 3.87 : 6.1 \u2014 inharmonic, i.e. a struck tube \u2014 and the waveguide gate never touches that code path.",
    "explains_which_percept": "tubes"
   },
   {
    "claim": "NOTHING IN THE SUITE COMPUTES SELF-SIMILARITY, so 'over and over' is structurally unmeasurable. Every gate's statistic is either a global scalar (levels), a point statistic (edges: 2 frames; seam: 20 samples), a per-window statistic aggregated by median or fraction (harmonic), a model-only computation (pitch, waveguide, external), or a correlation against a prediction inside one 4.2 s window (doppler). Not one compares any part of the film to any other part.",
    "evidence": "Calibrated envelope autocorrelation (40-band log-spectrum envelope at 100 Hz, normalised per band, lags 0.4-16 s): FLOOR pure filtered noise r = +0.016; CEILING the 2 s tiled loop r = +0.708; DELIVERED BEAT 1 r = +0.3958 at 1.380 s, with harmonics at 4.130 s (r = +0.302) and 8.260 s (r = +0.231) \u2014 a coherent 1.38 s pulse train. Delivered beat 5 r = +0.5929 at 0.400 s. Beat 1 sits 56% of the way from 'no repetition' to 'a 2-second block tiled', and no gate computes any such quantity.",
    "explains_which_percept": "tubes"
   },
   {
    "claim": "harmonic_gate's failure on pure noise is not a content failure \u2014 it is the gate declaring itself BLIND. On filtered noise it reports failures: [] and fails only via undeclared_unmeasurable, because power_ref (the adversary the applicability test is measured against) is built from the signal under test, so when the signal IS a hair dryer every limb reads zero discriminating power. The gate says 'I cannot measure this', never 'this is noise'.",
    "evidence": "degen_noise.wav -> harmonic PASS=False, failures: [], undeclared_unmeasurable: ['1_assembly','2_launch','4_transit','5_lap','6_ending'], every limb APPLICABLE=False. Same on swap_b1_noise.wav: failures: [], undeclared_unmeasurable: ['1_assembly'] \u2014 even though its hf fraction_below was 0.975 against a permitted 0.85 and would have failed on the number too, the gate tripped its blindness guard before it compared.",
    "explains_which_percept": "wind blower"
   },
   {
    "claim": "EVERY HARMONIC THRESHOLD IS DERIVED FROM THE ARTEFACT UNDER TEST, so the pass mark moves with the film. The gate's own stated rule is 'the limit is the midpoint between what THIS master reads and what the adversary reads, rounded to the nearest 0.05'. A film can therefore only fail by being worse than the film the limits were calibrated on \u2014 the instrument is anchored to the thing it is meant to judge.",
    "evidence": "Beat 1 hf: film reads fraction_below 0.707, the octave-matched hair dryer reads 0.952, midpoint 0.8295 -> the shipped limit is 0.85. Beat 4 hf: film 0.379, rejected master 0.964, midpoint 0.6715 -> shipped limit 0.65. HNR_HF_MIN_DB = 3.0 dB was likewise 'placed between' the rejected master's -0.73 dB and the rebuild's +6.7 dB. On the beat-1 scale, pure noise = 0.975, the line = 0.850, the delivered film = 0.707: the pass mark sits at 53% of the gap between the film and a literal wind blower.",
    "explains_which_percept": "wind blower"
   },
   {
    "claim": "seam_gate adjudicates 20 samples of 5,956,000 \u2014 0.0003% of the film \u2014 and its advertised sensitivity is content-dependent and evaporates on broadband material. On filtered noise its OWN positive control for a 3 dB instantaneous level step PASSES, as does its 40 ms crossfade control. Its documented teeth ('3 dB step caught at p99.950') are a property of the delivered master, not of the gate.",
    "evidence": "degen_noise.wav -> seam PASS=True at worst_d3_local_percentile 91.267; control '3 dB level step at beat 4' d3 p98.000 PASS=True; control '40 ms crossfade to elsewhere' p95.140 PASS=True. Only the 977-sample splice still failed. On swap_b1_loop.wav seam reads p85.910 \u2014 bit-identical to the delivered master's p85.910, because the loop's splices are inside beat 1 and the gate only visits the 5 beat boundaries.",
    "explains_which_percept": "tubes"
   },
   {
    "claim": "ONLY TWO OF EIGHT GATES FORM ANY OPINION ABOUT THE CONTENT OF THE FIRST 33 SECONDS, and one of them is a global loudness meter. Time coverage: levels 100% (global scalars), harmonic 93.55%, doppler 3.38% (85 windows in one 4.2 s span, inside beat 5), edges 0.07% (2 frames of 2,978), seam 0.0003% (20 samples), external/pitch/waveguide 0.00%.",
    "evidence": "Of beat 1's 33.0 s: levels judges it only through a 124 s integrated LUFS and a per-second -80 dB floor; edges judges 0.0417 s of it (frame 1); seam judges 0.0001 s (4 samples at t=33.0); doppler, pitch, waveguide and external judge 0.000 s. harmonic_gate is the ONLY gate that scores beat 1's content \u2014 and its threshold for that beat is the noise floor with 85% of windows permitted below it.",
    "explains_which_percept": "both"
   },
   {
    "claim": "doppler_gate is the only genuinely load-bearing gate against degenerate content \u2014 and it is blind to beat 1 entirely. It failed all three whole-file degenerates hard, but it passed BOTH beat-1 swaps with numbers bit-identical to the delivered master's, because its window lives in beat 5.",
    "evidence": "Whole-file degenerates: noise -> med err 1021.1 cents, fail_frac 0.957, PASS=False; loop63x -> corr 0.683, med 383.5, fail_frac 0.694, PASS=False; noise+tubes -> corr 0.699, med 399.6, PASS=False. Beat-1 swaps: swap_b1_noise and swap_b1_loop both -> corr_on_tracked_windows 0.99374, PASS=True \u2014 the same value the delivered master reports (0.993738).",
    "explains_which_percept": "neither"
   },
   {
    "claim": "THE CLIENT'S EXACT DESCRIPTION \u2014 a wind blower with tubes banged on it \u2014 passes six of eight gates, and the harmonic gate rates its BEAT 1 as 100x cleaner than the delivered film's. Octave-matched noise plus the tube loop, level-matched, fails only doppler and one broadband limb of harmonic by 0.033.",
    "evidence": "degen_blower_plus_tubes.wav -> levels/edges/external/pitch/waveguide PASS, harmonic PASS=False on a single limb ('2_launch.bb 0.533 > 0.50 below 2.0 dB'). Its beat 1 scores hf fraction_below 0.007 against a permitted 0.85 and bb 0.002 against 0.30 \u2014 i.e. the gate written to catch a hair blower declares a literal hair blower plus struck tubes to be a clean beat 1, with 120x margin, while the delivered film sits at 0.707/0.85.",
    "explains_which_percept": "both"
   },
   {
    "claim": "The percepts have concrete causes in layers.py that no gate inspects. Beat 1's energy is 52.2% 'room' and 40.6% 'assembly'. The assembly layer's servo whir is an exactly periodic LFO, f_srv = 320 + 90*sin(2*pi*0.11*t) \u2014 a 9.091 s period running the whole beat \u2014 carrying a 900-6000 Hz band-passed white noise at 0.6 against 0.5+0.2 of tonal sine. Its 616 impacts are placed on a uniform time grid within each of 15 clusters, each a 4-partial ring at ratios 1 : 2.31 : 3.87 : 6.1.",
    "evidence": "audio/out/master_report.json: assembly.impacts = 616, assembly.clusters = 15, room.rt60_low_s = 2.4. Stem energy over 0-33 s: room 52.167%, assembly 40.569%, engine 5.087%, crowd 2.156%, everything else <=0.022%. layers.assembly: 'fr = seat_f + (last_f - seat_f) * (p / max(nparts - 1, 1))' is a metronome per cluster; the noise term 'dsp.bp(dsp.white(n, seed+1), 900.0, 6000.0, sr, 2) * 0.6' is the broadband component that outweighs both sine terms.",
    "explains_which_percept": "both"
   }
  ],
  "summary": "AUDIT VERDICT: the gates are broken instruments, and I can prove it with the suite's own code and one file. THE TEST: I took the delivered master, replaced only beat 1 \u2014 the 33 s the client calls a wind blower and The Tubes over and over \u2014 with a single 2.000 s synthesised block tiled 16.5 times, renormalised to the master's own -14.00 LUFS / -1.23 dBTP, and ran audio/verify.py unmodified. ALL EIGHT GATES PASS. ALL_PASS=True. AUDIO_VERIFY_OK. exit 0. The file is at tmp/gateaudit/swap_b1_loop.wav and its report at tmp/gateaudit/out_swap_b1_loop/verify_report.json.\\n\\nFive degenerate signals were built and run through the full suite (matrix in tmp/gateaudit/, one verify_report.json per case). Pure filtered noise \u2014 built with the suite's OWN adversary construction verify._hairdryer_like \u2014 passes 6 of 8. A 2 s oscillator tiled 63 times passes 6 of 8, INCLUDING the harmonic gate that exists specifically to catch this. Noise + struck tubes, the client's literal words, passes 6 of 8.\\n\\nWHY. (1) Three of eight gates never open the delivered wav: external_assets is an AST scan of audio/*.py, pitch re-synthesises the dry engine from telemetry and measures THAT, waveguide root-solves engine.py's constants algebraically. All three pass 100% white noise. They test the source tree, not the artefact. (2) Coverage: only levels (global scalars) and harmonic form any opinion about beat 1's content. edges judges 2 frames of 2,978; seam judges 20 samples of 5,956,000; doppler judges 85 windows in one 4.2 s span inside beat 5. (3) The harmonic gate is a per-window statistic aggregated by a fraction, so it is mathematically invariant to repetition \u2014 it scored the tiled loop at +43.814 dB, 5.4x the delivered film's best beat. (4) Beat 1 is exempted from the engine test by name: its threshold is HNR_NOISE_FLOOR_DB = -1.0 dB, 'one decibel above what this metric reads on something with no line spectrum at all', with 85% of windows permitted below even that. Measured against the suite's own literal hair dryer, the delivered beat 1 sits +0.577 dB above pure noise (launch is +10.156). (5) Every threshold was derived as 'the midpoint between what THIS master reads and what the adversary reads' \u2014 the pass mark is a function of the artefact under test, so a film can only fail by being worse than the film that calibrated the limits. On the beat-1 scale: pure noise 0.975, line 0.850, delivered film 0.707. (6) waveguide passes only because of its one free parameter: at WAVEGUIDE_RPM=11000 it reads median 4.852 against a limit of 5.0; at the film's own rpm_at_vmax of 13,143 the same gate FAILS at 5.798. And it inspects only the three exhaust pipes \u2014 the beat-1 tube ringing is in layers.assembly (616 impacts, inharmonic partials 1 : 2.31 : 3.87 : 6.1) and in the showroom FDN, which it cannot see.\\n\\nLOAD-BEARING vs DECORATIVE. Load-bearing: doppler (the only gate that failed all three whole-file degenerates \u2014 but blind to 96.6% of the film and to 100% of beat 1). Partly load-bearing: harmonic (catches broadband collapse, but only by declaring itself unmeasurable rather than by failing a threshold, and it actively rewards a loop). Decorative for the client's complaint: levels, edges, seam, external_assets, pitch, waveguide \u2014 six of eight, of which three cannot see the audio at all.\\n\\nTHE PERCEPTS HAVE CAUSES. Beat 1 is 52.2% 'room' plus 40.6% 'assembly' by energy. The wind blower is layers.assembly's servo whir, whose 900-6000 Hz band-passed white noise carries gain 0.6 against 0.5+0.2 of tonal sine, riding an exactly periodic LFO f_srv = 320 + 90*sin(2*pi*0.11*t) \u2014 a 9.091 s cycle running the whole beat. The tubes are 616 impacts on a uniform time grid within each of 15 clusters, each a 4-partial ring at inharmonic ratios 1 : 2.31 : 3.87 : 6.1 \u2014 a struck bell, 616 times in 33 seconds. Calibrated envelope self-similarity puts the delivered beat 1 at r = +0.396 with a coherent 1.38 s period and harmonics at 4.13 s and 8.26 s, against a floor of +0.016 (pure noise) and a ceiling of +0.708 (a literal tape loop): 56% of the way to a loop. No gate computes any such quantity.\\n\\nWHAT TO BUILD, in priority order: (a) a repetition/novelty gate \u2014 self-similarity of the spectral envelope across the whole film, with the tiled-loop file as its positive control and pure noise as its negative; (b) rewrite beat 1's threshold so the showroom is held to something other than 'one dB above a noise generator', and derive limits from a source OTHER than the artefact under test; (c) a resonance-decay gate that runs on the RENDERED WAV and over ALL layers, not on engine.py's constants at one hand-picked rpm; (d) make every gate that cannot see the delivered audio report itself as such in gate_summary instead of contributing a PASS. Every degenerate file and report is preserved under tmp/gateaudit/ so any of these can be regression-tested against a signal that is known to be unlistenable."
 }
]
```
