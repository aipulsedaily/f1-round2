# R2-2521 .. R2-2580 — contract 1.2.0 leftovers, re-audited

Agent `r2-2521-contract-leftovers`. Task #78.

**The headline is that #78 was already done**, in commit `de3a1aa` by
`r2-1761-debt`, roughly eight hours before this task was issued. Rather than
redo it, this pass did what the block-camera task did: **read the artefact, not
the record of the artefact** — verified the three fixes by execution, then went
looking for what the fix missed. It missed four more copies of the same box, one
of which has diverged **now**, and one of which carries a provenance field
asserting a measurement its code never performs.

---

## 0. Lease

`claim` returned **PARTIAL (rc 0, `>> STAGE RESULT: PARTIAL (3 claimed, 3 clashes)`)**.

| path | status |
|---|---|
| `world/build_surface.py` | CLAIMED |
| `world/build_architecture.py` | CLAIMED |
| `docs/STAGING-R2-2521-to-R2-2580.md` | CLAIMED |
| `world/world_contract.py` | **CLASH** — `r2-1761-debt` |
| `world/build_dressing.py` | **CLASH** — `r2-1761-debt` |
| `tools/placement_gate.py` | **CLASH** — `r2-1761-debt` |

Nothing was released or retired. `tools/placement_gate.py` is additionally
**dirty with `r2-2341-placement-determinism`'s uncommitted work** (563 added
lines, the `half_width_fn` refusal and the determinism harness), so it is held
by one agent and being written by another. Every finding below that lands in a
clashed file is written up as handover, not applied.

---

## 1. STALE PADS — already fixed, verified, **not a defect any more**

`build_dressing.UNTRUSTED_PAD_M`. Was `42.0`, a frozen pad named after
`build_barriers`' deficit smoothing, which contract 1.1.0 deleted. Now
`float(C.OWNERSHIP_BLEND_M)` = 60.0.

Verified by reading the file, not the commit: `world/build_dressing.py:623`.
The pad's own block records the measurement — since 1.2.0 clamped
`barrier_offset` by `owned_edge`, `min(barrier_offset − verge_edge)` is
1.0000 m / 8.5000 m against a 0.30 m threshold, so `bad = 0 of 3675` on both
sides and the dilation of an empty mask is empty at 42 m and at 60 m: **0
stations change hands**. The guard is latent, not dead — an injected 3-station
break suppresses 87 at 42 m and 123 at 60 m.

**Verdict: closed. No action.**

---

## 2. UNREACHABLE FALLBACKS — **redundant, not symptomatic**, and correctly left alone

The 11 `getattr(C, NAME, <literal>)` sites in `build_surface`,
`build_architecture`, `render_setup3` and `build_film_scene`.

The brief's test is *why* they are unreachable. Answered structurally, not by
inspection of the call sites:

**All three consumer modules import the contract unconditionally at module
top** — `world/build_surface.py:77`, `world/build_architecture.py:58`,
`render_setup3.py:19` — with no `try/except ImportError`. There is therefore no
guard above the fallbacks that could be broken. A `getattr` default is reachable
**iff the contract imports and lacks the name**; a contract that fails to import
kills the module outright. So the fallbacks are unreachable *by the contract's
namespace*, which is redundancy by design, not a corpse propped up by a broken
guard.

Contract selftest `[19]` (added by `de3a1aa`) asserts exactly the right thing —
not that the literals agree, but that **every name a consumer falls back on is
still exported**, so every fallback stays unreachable. Run and observed:

```
[19] THE CONSUMERS' getattr FALLBACKS ARE UNREACHABLE  (R2-071)
  ok   every name a consumer falls back on is exported here    11 sites, 6 names, all resolved
  ok   ... and the divergence each dead literal hides is measured
       3 of 11 disagree: ACCESS_RIBBON_T_MIN@build_architecture:110  0.0000 vs -0.3000 = 0.300 m
                         ACCESS_RIBBON_T_MIN@build_architecture:6637 0.0000 vs -0.3000 = 0.300 m
                         PIT_WALL_S0@render_setup3:201            3447.7092 vs 3430.0000 = 17.709 m
  ok   CONTROL: the same sweep FAILS a name this file does not export
  ok   CONTROL: `defined but absent from __all__` still counts as armed
PASS  (155 checks, 0 failed)
```

Both controls fire. **Verdict: not a defect. Deleting them would remove a
deliberate v1.0.x back-compat shim that costs nothing and is guarded.** A
well-argued null.

### Two residuals on `[19]` itself, for the owner of `world_contract.py`

**(a) `_FB` is a hand-typed inventory of the call sites — the instrument built
to fix source-versus-artefact keeps its own copy of the artefact.** It cannot
see a 12th `getattr` site added by any of the seven live agents; a new one would
sail past and `[19]` would still print PASS. It is *already* stale in its site
column: the table says `build_film_scene:419`, the real site is
`tools/build_film_scene.py:491`. The table's *contents* are currently complete
(independently swept — 11 sites, and the sweep agrees), so this is a blind spot,
not yet an error. Fix: derive `_FB` by scanning the tree for
`getattr\((C|WC),\s*"([A-Z_]+)"` rather than typing it.

**(b) `[19]` compares each literal to the contract but never to the *other
consumer*.** `ACCESS_RIBBON_T_MIN` has two different fallbacks for the same
contract name — `0.0` at `build_surface:124`, `-RIBBON_SAW_M` = −0.30 at
`build_architecture:110`. If the name were ever dropped, the two modules would
build the same boundary 0.300 m apart, which is precisely the defect the
contract's own prose cites (three modules, three margins, 64 m² of Beat-3→4
hinge with no ground). This is *correct* as back-compat — each fallback
preserves its own module's pre-contract behaviour — and `[19]`'s
name-stays-exported assertion is the right guard for it. Noted, not changed.

---

## 3. THE GATE THAT KEEPS ITS OWN CAR BOX

### 3a. Has the duplicated box diverged? **It had. 340 mm. It is now clean, and I watched the guard refuse.**

`tools/placement_gate.py` kept `CAR_BODY_W_M / CAR_RIDE_HEIGHT_M /
CAR_BODY_TOP_M / CAR_MARGIN` privately. `0.992` — the box's **thickness** — sat
in the slot meaning the box's **top**, against a car measured at z 0.340..1.332.
The car-path z band therefore stopped at 1.592 m where it should reach 1.932 m.
`intrusion()` returns `-1e9` outside the band, so anything in that 340 mm slice
directly over the driven line never reached the distance test: invisible to
`violations` **and** to `closest_approach`.

`de3a1aa` corrected the literal and added a six-quantity diff against the
contract. Baseline run, this pass:

```
>> car path: 1743 stations, half-width 1.60 m, band -0.300 .. +1.932 m
   the gate's car box agrees with world_contract's   worst |delta| = 0.000e+00 m over 6 quantities
   the band FLOOR tests at least as deep as the contract's box   40 mm deeper
>> all 39 controls behaved
>> STAGE RESULT: PLACEMENT_SELFTEST_OK
```

**The built-in negative control feeds hardcoded historical numbers to the
comparator; it never proves the wiring from the module globals.** So I injected
the real fault into a copy — `CAR_BODY_TOP_M = 0.992` — and ran it:

```
>> car path: 1743 stations, half-width 1.60 m, band -0.300 .. +1.592 m
   FAIL  the gate's car box agrees with world_contract's   worst |delta| = 3.400e-01 m
>> 1 SELFTEST CONTROL(S) MISBEHAVED
>> STAGE RESULT: PLACEMENT_SELFTEST_FAIL
```

The guard is live and correctly wired: the injection moves the measured band
**and** trips the check. **Observed to fail before being trusted.**

> Method note: the first injected run printed a `ModuleNotFoundError` traceback
> and **exited rc=0**. Judged on `$?` it was a pass. That is the standard this
> project keeps, reproduced in passing.

### 3b. Which verdicts does the 340 mm slice invalidate? **46 of 48 reports on disk.**

Every placement-gate report in the tree, keyed on `clearances.car_band_top`
(the field `de3a1aa` added — absent means the run predates the fix):

| | count |
|---|---:|
| reports predating the fix (blind slice live) | **46** |
| reports after the fix (`car_band_top = 1.932`) | 2 |
| pre-fix reports carrying a numeric `car_path` clearance | **35** |
| pre-fix `car_path` violation entries recorded | 54 |

**All 35 of those clearance figures are unsound in one direction only.**
`closest_approach` is a maximum over per-vertex intrusions, and every vertex in
the blind slice returned `-1e9`; a `-1e9` can never raise a maximum. So each
number is a **lower bound on the true intrusion** — the world may be worse than
reported, never better. That is the direction that manufactures false PASSes.

The ones that matter, because they are the acceptance reports for the shipped
world and they all concluded *zero* car-path violations:

```
render/world/assembly/r2/v122/placement_v122.json          BR_Concrete_L12   +4.6084 m   0 car viol
render/world/assembly/r2/v122/placement_v122_ground.json   BR_Concrete_L12   +4.6084 m   0
render/world/assembly/r2/v121/placement_v121.json          BR_Concrete_L12   +4.6084 m   0
render/world/assembly/r2/v121/placement_v121_ground.json   BR_Concrete_L12   +4.6084 m   0
render/world/assembly/r2/v120/placement_v120_recheck.json  BR_Concrete_L12   +4.6084 m   0
work/instrument-fixes/placement_assembly5_fixed.json       BR_Concrete_L12   +4.6084 m   0
render/world/assembly/r2/v120/placement_v120.json          ARCH_RetainEdge   +0.3592 m   0
render/world/assembly/r2/v120/placement_v120_ground.json   ARCH_RetainEdge   +0.3592 m   0
docs/placement_after_46.json                               ARCH_RetainEdge   -0.1553 m   0   <- negative, and still CLEAN
```

`docs/placement_after_46.json` is compromised twice over: a **negative**
car-path clearance reported with zero violations, which is the edge-family
courtesy leak the gate's own selftest already documents.

### 3c. How much of that slice was actually blind? **Measured independently: 92.20 % was covered by another volume.**

The commit claims 92.20 % on report. I re-derived it from the telemetry and the
contract's own centreline rather than trusting it — the slice is a disc of
radius 1.6025 m spanning z +1.592..+1.932 m about each telemetry point; the
question is whether the road corridor (radius `half_width + 0.50`, band
`elevation ± (0.50, 4.50)`) already covered that space:

```
telemetry stations: 1743
  fully covered (whole disc inside the corridor)  1607 / 1743 =  92.20 %
  centre covered (lenient)                        1611 / 1743 =  92.43 %
  NOT covered at all (true blind spot)             132 / 1743 =   7.57 %
  partially covered (centre yes, disc no)            4 / 1743 =   0.23 %

  uncovered: rows 0..131 contiguous — lateral |u| 8.85..81.64 m against a
             corridor of 8.50 m, world x 0.0..132.8, y 0.0..16.4
```

132 + 4 = **136 stations = 7.80 %** not fully covered, which reproduces the
commit's figure exactly by an independent route. The exposure is **one
contiguous run, rows 0..131 — the dais-to-paddock transit**, where the car is
8.85–81.64 m off the circuit centreline and no other volume was watching.
On the lap proper the corridor caught anything in the slice, though it would
have logged it as a *corridor* violation, not a car one.

**So: the 35 figures are suspect, and the suspicion is concentrated in the
transit.** Re-running the assembly reports needs the 3.9 GB blends and is a
separate job.

### 3d. **The check runs only under `--selftest`. It never runs on a verdict.**

`main()` early-returns into `selftest(a)`; the production path builds volumes and
writes the report without ever touching the contract diff. The report records
the gate's *own* constants under `clearances` — good, two reports can be diffed
— but never the contract's, so an already-issued report cannot be audited
against the contract after the fact either.

The gate's own words, written by the author of this guard: *"a hand diff that
nobody schedules is not an instrument."* A `--selftest`-only diff is that
sentence one level up. **Recommendation: run the six-row diff in `build_volumes`
and refuse the run on disagreement**, the same way `half_width_fn` now refuses a
contract that will not import.

### 3e. **The independence justification does not survive contact with the spec.**

The copy is defended by *"a gate that imports the thing it checks can agree with
a wrong number"* (R2-044). Tested against what the file actually does:

* **The gate does not check the car box.** It checks *world objects* against the
  car's swept volume. The box is an **input**, not the subject of the verdict.
  Importing an input is not importing the thing you check.
* **The copy is not a second derivation.** `elevation_fn()` genuinely
  re-implements the spec's `elevation.station_z_pvi` from `circuit_spec.json` —
  two methods, one requirement, and its cross-check is meaningful. The car box
  has **no independent source to be independent of**: `circuit_spec.json`
  contains no car dimensions at all (`vehicle_model` holds masses and
  accelerations; `2.005`, `5.698`, `0.992` appear **zero** times). Both the
  contract and the gate transcribe the *same* measurement, `round2_inventory.md`
  §3. Two transcriptions of one measurement are not two methods — they cannot
  disagree except by drift, and drift is exactly what happened.
* **The coupling already exists.** Since R2-2341 the gate *refuses* if the
  contract exists and will not import, and it *prefers* the contract's
  `half_width`. Contract availability is already a hard precondition of any
  verdict; deriving the car box adds no failure mode that is not already fatal.

**The copy buys nothing and can only drift.** Recommendation stands: delete it
and derive from `world_contract`, keeping `CAR_ZLO = -0.30` as the one number
that is genuinely a deliberate stricter-than-derived choice (and which already
carries its own directional assertion). Not applied — the file is leased by
`r2-1761-debt` and dirty with `r2-2341`'s work.

---

## 4. THE FINDING THE FIX MISSED — **there are seven copies of the car box, not two, and one has diverged now**

`de3a1aa` fixed the copy it was pointed at. Sweeping for the numbers rather than
for the name:

| # | location | box | status |
|---|---|---|---|
| 0 | `world_contract.py:2237` | 5.698 × 2.005 × 0.992, ride 0.340, top 1.332 | **the source** |
| 1 | `build_surface.py:139` `CAR_WIDTH` | `C.CAR_BODY_W_M` | correct, RULE 1 |
| 2 | `build_surface.py:4287` `_car_box()` | retyped `5.698, 2.005, 0.992, 0.340` | **FIXED HERE** (§5) |
| 3 | `tools/placement_gate.py:173` | private, guarded | correct today, `--selftest` only |
| 4 | `tools/build_beatsheet.py:1954` `CAR_BOX_LO/HI` | (−2.70,−1.00,0.34)..(3.02,1.00,1.33) | **DIVERGED** |
| 5 | `docs/beat_sheet.json` `beat1.car_box` | the artefact of #4 | **DIVERGED** |
| 6 | `tools/lap_shotscale.py:68` | LEN 5.698, W 2.005, TOP_Z 0.992, **BOT_Z 0.0** | **suspect** |
| 7 | `tools/r2651_occlusion_sweep.py:120` | LEN 5.698, W 2.005, TOP_Z 0.992, BOT_Z 0.020 | **suspect** |

### 4a. `build_beatsheet` / `beat_sheet.json` — diverged, and in the unsafe direction

```
              beat sheet          contract        delta
X span        5.720 m             5.698 m         +22.0 mm   (tail rounded OUT, safe)
Y span        2.000 m             2.005 m          -5.0 mm   (2.5 mm per side, UNSAFE)
Z top         1.330 m             1.332 m          -2.0 mm   (UNSAFE)
```

The beat sheet's numbers are the contract's rounded to 2 dp — outward at the
tail, **inward in Y and Z**. A box smaller than the car in the two axes a camera
weaves through. It gates beat 1: `build_beatsheet.py:2027` uses these constants
for `min_clearance_to_car_m` against `CAR_CLEAR_M = 0.30`, and three tools read
the emitted JSON (`beat1_shotscale.py:76`, `beat1_true_extent.py:108`,
`lap_shotscale.py:217`). 3 mm against a 300 mm floor is 1 % — small, real,
unguarded, and wrong in the direction that passes things it should not.

### 4b. **`beat_sheet.json`'s `measured_on` is decorative — the code never measures**

```python
CAR_BOX_LO = (-2.70, -1.00, 0.34)          # build_beatsheet.py:1954, module-level literal
CAR_BOX_HI = (3.02, 1.00, 1.33)            #                   :1955, never reassigned
...
"car_box": {"lo": list(CAR_BOX_LO), "hi": list(CAR_BOX_HI),      # :2447
            "measured_on": "world/beat1_anim.blend"},            # :2450  <- hardcoded string
```

`CAR_BOX_LO/HI` are assigned once, at module level, from literals, and are never
written again. The `measured_on` field is a **hardcoded string emitted beside
them**. Nothing in `build_beatsheet.py` opens `beat1_anim.blend` to measure a
bounding box. This is the purest form of the family the brief lists: **a record
asserting a measurement that was never performed**, and it is worse than a bare
literal because it stops an auditor from looking further.

Not touched — `docs/beat_sheet.json` and the beat authoring tools are explicitly
another agent's. **Handed over.**

### 4c. `lap_shotscale` / `r2651_occlusion_sweep` — the same 340 mm slip, still live

`lap_shotscale.py` is described by `r2651_occlusion_sweep.py:116` as *"the
instrument every other size statement in this round was made with"*. Its box is
`CAR_BOT_Z = 0.0 .. CAR_TOP_Z = 0.992`. The car is `0.340 .. 1.332`. The
**height is right and the placement is wrong** — the body is sat on the road
instead of on 340 mm of ride height, so the projected subject centre
(`lap_shotscale.py:194`, `ctr[2] += CAR_TOP_Z / 2.0` → 0.496 m) is **0.340 m
below the car's true centre at 0.836 m**.

`r2651_occlusion_sweep.py` inherits the convention and documents *only* its
bottom (`0.020`, deliberately lifted off the road to beat coplanar ray noise);
its `CAR_TOP_Z = 0.992` is undefended and looks like the identical slip.

This is `0.992`-as-top for the **third** time in this codebase. Both files are
camera/framing territory (beat-5 A/B, camera rig, crowd block cameras) —
**not touched, handed over.**

---

## 5. WHAT WAS ACTUALLY CHANGED

One file, inside my lease: `world/build_surface.py`, `_car_box()`.

```python
-    L, W, Hh, ride = 5.698, 2.005, 0.992, 0.340
+    L, W, Hh, ride = (C.CAR_BODY_LEN_M, C.CAR_BODY_W_M,
+                      C.CAR_BODY_H_M, C.CAR_RIDE_HEIGHT_M)
```

Four retyped literals, **4 150 lines below line 139 of the same file**, where
`CAR_WIDTH = C.CAR_BODY_W_M` already obeys RULE 1 and says in its own comment
*"the placement gate, the transit keep-out and this module all have to mean the
same car"*. One half of the file obeyed the rule; the other half retyped the
numbers underneath it.

`_car_box()` is reachable only from `_test_props()` and the test-scene builder
(`build_surface.py:4144`, `:4671`), so no shipped geometry depends on it. It is
the scale reference the test harness drops into frame — a scale reference that
is silently the wrong size teaches the eye a wrong size.

### Bit-identity, measured in both directions

All four literals were **bit-identical** to the contract's values, compared as
IEEE-754 doubles rather than printed decimals. The vertex arithmetic is
unchanged and its inputs are the same bits:

```
A. INERT   2001 poses x 8 vertices x 3 coords = 48024 doubles compared
   poses whose vertex bits DIFFER: 0   worst |delta| 0.000e+00 m

B. CONTROL  the same code fed a box with the ride height lost (5.698, 2.005, 0.992, 0.0)
   poses whose vertex bits MOVE: 2001 of 2001   max |delta| 0.3400 m

B2. CONTROL a contract whose CAR_RIDE_HEIGHT_M is +0.5 m moves the box by 0.5000 m

>> STAGE RESULT: CARBOX_DERIVATION_OK
```

**B and B2 are the controls the coordinator asked for**: a derivation nobody has
watched respond is no better than the copy it replaced. Fed the exact historical
fault — `0.992` as the top, ride height lost — the box moves by 0.3400 m on every
one of 2001 poses. Fed a contract with a different ride height, it moves by
0.5000 m. The derivation is live, not decorative.

No world rebuild was run: no shipped geometry changed, so there is no hash to
compare. The box's bit-identity **is** the identity result, and it is exact.

---

## 6. NOT DONE, AND WHY

* **`tools/placement_gate.py`** — delete the private box, derive from the
  contract (§3e), and move the diff out of `--selftest` into `build_volumes`
  (§3d). Leased by `r2-1761-debt`, and simultaneously dirty with
  `r2-2341-placement-determinism`'s uncommitted work.
* **`world/world_contract.py`** — derive `[19]`'s `_FB` table by scanning
  instead of typing it (§2a); and `CAR_SWEPT_PAD_M` (`:2248`) has **zero
  consumers anywhere in the tree** and its comment states that *"the gate sweeps
  an AXIS-ALIGNED BOX of that half-side, whose corners reach sqrt(2) further
  than its faces."* `intrusion()` sweeps a **cylinder** —
  `math.hypot(p.x - sx, p.y - sy)` — and the whole point of that rewrite was to
  delete the axis-aligned boxes and their diagonal skirt. The constant is a
  fossil of the box era: it over-pads by 0.664 m per side against the gate as
  built, and it is the contract holding a **stale belief about an artefact**.
  Nothing consumes it, so nothing has been mis-built. Leased by `r2-1761-debt`.
* **`tools/build_beatsheet.py`, `docs/beat_sheet.json`** — §4a, §4b. Explicitly
  another agent's; forbidden by the brief.
* **`tools/lap_shotscale.py`, `tools/r2651_occlusion_sweep.py`** — §4c. Camera
  and framing territory.
* **Contract box vs the car asset itself.** Nothing in this repo has ever
  measured `world/car_anim.blend`'s evaluated bounding box against
  `world_contract.CAR_BODY_*`; both the contract and the beat sheet cite
  `round2_inventory.md` §3, which is prose. That is the one check that would make
  the box source-versus-artefact rather than source-versus-source. **Not run:**
  the blend is 302 MB on disk against 2 GB of available RAM with seven agents
  live and `/proc/pressure/memory full avg300=12.06`. Under `tools/buildlock.sh`
  when the box is quiet:
  `bash tools/buildlock.sh carbox blender -b world/car_anim.blend --factory-startup -P <bbox script>`

---

## 7. VERDICTS

| item | was it a defect? | outcome |
|---|---|---|
| stale pads | yes, latent | **already fixed** in `de3a1aa`; verified; no action |
| unreachable fallbacks | **no** | redundant by design, guarded by `[19]` with two firing controls. A defended null |
| the gate's private car box | **yes, and it was live** | fixed in `de3a1aa`; guard **observed to fail** here; 46 of 48 reports on disk are suspect; the copy should still be deleted, not merely corrected |
| **(new)** a 7th copy in `build_surface._car_box` | yes | **fixed here**, bit-identical, controls fire |
| **(new)** `beat_sheet.json` car box | **yes, diverged now** | −2.5 mm/side in Y, −2 mm in Z, unsafe direction; handed over |
| **(new)** `beat_sheet.json` `measured_on` | **yes** | a provenance field asserting a measurement the code never performs; handed over |
| **(new)** `lap_shotscale` / `r2651` box | suspect | `0.992`-as-top for the third time; subject centre 0.340 m low; handed over |
| **(new)** `CAR_SWEPT_PAD_M` | yes, inert | zero consumers; its comment describes a gate geometry that was deleted; handed over |
