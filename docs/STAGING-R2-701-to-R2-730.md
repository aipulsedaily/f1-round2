# STAGING R2-701 .. R2-730 — the rear-wing aerofoil correction, baked and judged

Staged here, not in `DEFECT-LOG-R2.md`.  Entry numbers are provisional.

Scope handed to me: bake `--rear-wing aerofoil` (committed in `sim/breachlib.py`,
never run), judge it against the peak window of the deck ride with R2-700's POSE
criterion, and say plainly if it does not work.

---

## R2-701 — WHAT THE 58.6 % DESCRIBES, and it is not the car anyone will see

Stated once, because the number has already nearly been misread and it is quoted
in three documents.

**`wing_r` — 0.478 m chord, 1.070 m span, 0.280 m thick, t/c = 58.6 % — is a
part of `sim/breachlib.py`'s CAR COLLISION PROXY.  It is eighteen convex boxes
and wedges that exist only inside the rigid-body solver.  It is not the rendered
car, it is not in any film scene, and no shot contains it.**  The rendered rear
wing is a properly swept thin aerofoil and is visible as one in
`render/r2387/COMPARE_ride_f0972_R6_vs_REBAKE_vs_R2387.png`, left and centre
panels.  Nothing in this block touches render geometry, and `--rear-wing
aerofoil` cannot: `car_proxy_parts()` is imported by the sim and by nothing that
builds a scene.

What the proxy's tray costs is a picture defect, not a modelling one.

## R2-702 — PRE-REGISTERED: seven predictions, written before either cell landed

Both cells were submitted at 19:52 and this section was written while they baked.
The bake is one variable against the R2387 production table: same bundle hash
(`7db0e9db3f025c50`), same thresholds, same air model, same friction, same
substeps — `--rear-wing aerofoil` against `--rear-wing solid`.

| | prediction |
|---|---|
| **P30** | The tray releases.  `MUL05_S02`'s longest run within ±0.5 m of car-local x = −2.200 while above the deck falls from **127 film frames** to **under 40**. |
| **P31** | The pose gate (`sim/ridepose.py`, R2-703) PASSES the aerofoil cell: no structural member is aboard and under 3 px/frame of car-relative motion for 12 consecutive film frames. |
| **P32** | The solid control reproduces the R2387 production table's `MUL05_S02` track to within decimation tolerance, so the difference between the two new cells is attributable to the wing and nothing else.  **If this fails, every A/B on this beat — mine, R2-387's, R2-281's — is unattributable, and that is the finding rather than the wing.** |
| **P33** | The count of structural members aboard does NOT go to zero.  The nose capture (R2-384: 1,771 bodies carried at the nose) is a different mechanism at the other end of the car and the mainplane's thickness has nothing to do with it. |
| **P34** | The "across" statistic — the member's own long axis dotted into the car's y — falls for the worst aboard member, from ~0.70 towards under 0.40.  What makes a bar lie transversely is being stopped square-on by a full-width leading face. |
| **P35** | The wall is unchanged: connected aperture stays 2.15 × 6.00 m with bay 5 at 100 %.  The wing is 4.9 m behind the nose and reaches the glass plane long after it has failed. |
| **P36** | **The one I expect to be wrong.**  Thinning the mainplane leaves the two endplates (z 0.320–0.980) and the engine cover below it in place, so the tray may become a SLOT: a member could wedge between the mainplane's underside at z = 0.9226 and the cover, and ride on in a pose that is lower but just as static.  If the still-run survives at 12+ frames in a different place, the correction has moved the trap rather than opened it, and the answer is negative. |

### P37 and P38 — added while the cells baked, off a measurement I did not expect

Committed before either table existed, and written because the measurement below
makes a clean win less likely rather than more.

**THE MEMBER IS NOT ON THE WING DURING THE FRAMES THAT READ AS BROKEN.**
`MUL05_S02` in R2387, car-local, against a proxy whose highest point anywhere is
`CAR_TOP_Z` = 0.992 and whose rear wing tops out at 0.980:

| film | car-local x | z | gap above the wing's top surface | nearest thing below it |
|---|---|---|---|---|
| f0900–f0935 | −0.90 → −1.85 | **0.88–1.04** | **−0.10 to +0.06 m** — in contact | glass at 0.80–0.92 |
| f0940 | −1.67 | 1.22 | +0.24 | 1.18 |
| **f0967–f0977** | **−2.0 → −2.2** | **1.52–1.55** | **+0.54 to +0.57 m** | **glass at 1.20–1.25, a 0.30 m AIR GAP** |
| f0990 | −2.41 | 1.61 | +0.63 | 1.57 |

So the ride has **two phases**, and only the first is a contact with the tray:

* **f0890–f0935 — on the deck and against the wing.**  z sits within ±0.1 m of
  the wing's top surface while x walks aft to the leading face at −2.200.  This
  is the phase `--rear-wing aerofoil` is aimed at.
* **f0935 onward — airborne, and co-moving.**  It rises 0.6 m, holds station in
  the car's frame to within 0.4 m over 40 film frames, and has 0.3 m of nothing
  underneath it.  **The frames R2-700 judged, f0967–f0977, are entirely in this
  second phase.**  Whatever is keeping it overhead there, it is not the tray's
  leading face, because the tray is half a metre below it.

| | prediction |
|---|---|
| **P37** | The aerofoil correction will change the FIRST phase — contact against the wing at f0890–f0935 — and that is measurable as the tray-band residence falling from **86 film frames** (`MUL05_S02`, ±0.5 m of x = −2.200 while above the deck; `MUL05_S02_P` 108) toward R2281's **26–32**. |
| **P38** | **The one that decides the block, and I am genuinely unsure of it.**  Whether removing the catch also removes the airborne co-moving phase at f0967–f0977.  If the loft at f0935 is the tray throwing it, yes.  If the member would be lofted by the deck and the glass raft anyway, the peak frames come back looking much as they do now and **the correction is real, aimed at a real defect, and still does not fix the picture** — which is a negative result, not a failed bake, and is to be reported as one. |

Note what P37/P38 do to R2-4xx's account.  "It is being caught, released and
caught again by a wall" is right about f0917–f0935 and is **not** what is
happening at the peak; the reopened search measured car-local x against the
wing's face and did not check the z gap.  The mechanism is real; its reach into
the frames that matter was assumed rather than measured.

## R2-703 — THE ACCEPTANCE TEST, BUILT AND CALIBRATED BEFORE THE BAKE LANDED

R2-700 fixed the criterion in words and refused to fix it as a count:

> debris travelling alongside, tumbling or trailing is fine and desirable;
> something lying flat across the bodywork **with no relative motion** is what
> reads as broken.

`sim/ridepose.py` implements exactly that and nothing else.  Per structural body
(the 152 non-glass bodies), per film frame:

* **aboard** — car-local position over the car's plan and above the deck
  (z > 0.55).  Deliberately not `carproxy_census`'s envelope, whose ceiling at
  car-local z = 1.112 m is why it reported `MUL05_S02 transported 0.0 m` for a
  body that was riding at z 0.95–1.69.
* **still** — measured **in pixels**, because the eye is judging a picture.  The
  body's actual screen position against where it would be had it been WELDED to
  the car since the previous frame:
  `rel_px(f) = |proj_f(p(f)) − proj_f(c(f) + R(f)·q(f−1))|`.
  A member locked to the bodywork scores ~0 px however fast the car travels; one
  tumbling alongside scores tens.  Absolute screen motion is reported beside it,
  because the read is the CONTRAST between the two — "at rest in a shot where
  everything else is smeared".
* **across** — the member's long axis, taken from its intact rest pose in the
  wall, expressed in the car's frame.  |axis·y_car| ≈ 1 is a bar lying
  transversely across the car; ≈ 0 is one pointing where the car is going.

**It was calibrated against the three bakes whose verdicts R2-700 had already
fixed by eye, before it was ever pointed at a new one**, over f0940–f1060:

| | aboard | lowest own-motion ratio | members carried | across | verdict | R2-700's verdict by eye |
|---|---|---|---|---|---|---|
| **R6 SHIPPED** | **0** | n/a | n/a | n/a | **VACUOUS** | wrong, car emerges pristine |
| **R2281 RE-BAKE** | 8 | **0.337** | **0 of 8** | 0.04–0.13 | **PASS** | reads as an accident — accept |
| **R2387 AIR** | 10 | **0.076** | **8 of 10** | 0.41–0.81 | **FAIL** | reads as broken — reject |

**Three things about that table matter more than the verdicts.**

1. **It reproduces the eye on a measurement the eye was not consulted about.**
   The member count is 8 against 10 — still nearly useless, exactly as R2-700
   said.  Every member aboard in R2281 moves 34–43 % of its screen motion under
   its own steam; eight of ten in R2387 move under 24 % and two under 9 %.
   **The "across" statistic agrees independently** — 0.04–0.13 against 0.41–0.81
   — and two independent discriminators agreeing is the only reason to believe
   either.
2. **R6 does not pass.  It is VACUOUS, and the gate says so in those words.**
   Nothing can come to rest on a car that nothing comes off.  A gate that
   reported "PASS" here would ship the 29.5×-too-strong thresholds, which is
   exactly the trap R2-700 warned about — "a reviewer picking the safest-looking
   of the three would be picking the broken one".  `n_aboard` is printed beside
   every verdict for that reason.
3. **The obvious reading of the criterion — "near-static for N frames" — does
   not survive contact with the data, and finding that out is worth more than
   the gate.**  Implemented as a run length it INVERTS when the window moves:

| members with a still run ≥ 12 frames at 3 px | f0900–f1060 | f0940–f1060 | f0967–f0977 |
|---|---|---|---|
| R2281 RE-BAKE — the one the eye ACCEPTS | **6** | 0 | 0 |
| R2387 AIR — the one the eye REJECTS | 2 | **2** | 0 |

On the widest window the accepted bake fails harder than the rejected one; on
the narrowest neither fails at all.  **A run length is a bounded measure and it
reports confidently about its bound** — the same shape of error as
`carproxy_census`'s z-ceiling, and the third instance of it in this block.  The
ratio does not move:

| lowest own-motion ratio of any member aboard | f0900–f1060 | f0940–f1060 | f0967–f0977 |
|---|---|---|---|
| R2281 RE-BAKE | 0.304 | 0.337 | 0.378 |
| R2387 AIR | 0.125 | 0.076 | 0.110 |

Three windows, a factor of three in every one, an empty gap from 0.19 to 0.30
for a threshold to sit in, and the same ordering the eye gave.  0.25 is the
middle of that gap and is not tuned finer than that.  **The run length is still
reported on every run, clearly marked as not gated on.**

## R2-704 — the bake, and what it cost

Both cells run on the rented 5090 instance (`46819442`, $0.5778/hr, already up
and shared with four other agents' jobs) via `rq exec --closure`, which derived
a 9-module bundle from `sim/remote_bake.py` plus five data files — 5.5 MB, no
scene push.  Two cells at ~1 slot each:

| cell | job | argv | 
|---|---|---|
| **A** aerofoil | `1edd5b763b30` | `--rear-wing aerofoil` |
| **S** solid control | `9c977a75f91d` | `--rear-wing solid` |

**Stated cost: ~2.5 instance-hours for the pair running concurrently ≈ $1.45**,
on an instance that was already rented.  A second-seed pair, if the first result
warrants it, is the same again.

**Why it went to the farm rather than this box, and the guard that sent it.**
`Car.identity_ok()` REFUSED the local bake:

```
REFUSING: /home/zany/f1-round2/world/car_anim.blend is 301667220 bytes,
was 300235801 when sampled.
```

Another agent re-saved the car blend at 19:30, growing it by 1,431,419 bytes.
The remote path is not an evasion of that guard — `sim/remote_bake.py` exists
precisely because the 300 MB blend never travels, and the check is then made
against the content-addressed stamp that ships with the measurement — but the
guard's actual question still had to be answered.

## R2-705 — the guard fired on a MATERIALS edit, and the car's animation is BIT-IDENTICAL

The question the guard asks is "is the sim still driven by the car the film
renders?"  It was answered by measurement rather than by inference.
`tools/sample_car_blend.py`, the same instrument that produced
`world/car_anim_measured.json`, was re-run against the blend as it stands now,
over the beat-3 range only (`--frames 845-1165`, 321 frames), writing to a
scratch path — **nothing shared was overwritten**.  Against the measurement the
sim actually uses:

| | difference |
|---|---|
| `CAR_ROOT` location, all 321 frames | **0.000e+00 m** |
| `CAR_ROOT` XYZ euler, all 321 frames | **0.000e+00 rad** |
| four contact patches, all 321 frames | **0.000e+00 m** |
| wheel-spin F-curves (FL/FR/RL/RR) | **0.000e+00 rad** |

**Bit-identical, on every channel the sim reads, across the whole of beat 3.**
The 1.4 MB the blend gained is the R2-521 surface-detail pass — `world/car_anim_imp.json`,
written a minute after the save, is a table of `dust_rough`, `wear_polish`,
`paint_peel` and `glass_smudge` constants — and it cannot move a rigid body.

So the guard was right to fire (the file it was told to watch did change) and
wrong about what it implied.  **`Car.identity_ok()` watches the blend's SIZE,
which is a proxy for the animation and not the animation.**  A materials edit
trips it; an animation edit that happened to leave the file the same size would
not.  That is worth an entry of its own and is not fixed here: this block did
not touch `sim/breachlib.py`.

What it means for this A/B: the cells are driven by the same car R2387, R2281
and the shipped table were driven by, and that car is still the film's car.
**Nothing is stale and no result below is qualified by it.**

## R2-706 — the camera track this block measures pixels through is CURRENT, and the check took two minutes

Every pixel figure in R2-4xx and in everything below goes through
`sim/out/oner_camera_track.json`, which was dumped from **film14** at 15:19.
The film has since moved to **film16** (7.5 GB, `render/film16_breach.blend` is
what the farm is serving).  A superseded camera track would silently invalidate
the 11 px / 1,879 px comparison, the own-motion ratio, and every frame in this
block.

It does not, and the reason is specific.  `render/film14_path.json` against
`render/film16_path.json`, all 2,978 frames, position / quaternion / lens:

| | max Δposition | max Δquaternion | max Δlens |
|---|---|---|---|
| beats 1–2, f1–f864 | **9.206 m** | 1.977 | **23.00 mm** |
| **beat 3's ramp, f865–f1056** | **0.0000** | **0.0000** | **0.0000** |
| **the judged window, f940–f1060** | **0.0000** | **0.0000** | **0.0000** |
| **the peak, f0967–f0977** | **0.0000** | **0.0000** | **0.0000** |
| beat 4, f1057–f2978 | **0.0000** | **0.0000** | **0.0000** |

The camera between film14 and film16 is **bit-identical from f865 to the end of
the film**.  All of the movement is in beats 1–2, which is another agent's
re-framing work.  The track is therefore exactly right for this block, and this
is a measurement rather than an assumption — which matters, because "the camera
has moved twice since" is written into `sim/land_breach.sh` as a standing
hazard.
