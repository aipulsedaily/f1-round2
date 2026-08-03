# Staged for the defect log's owner

Kept out of `docs/DEFECT-LOG-R2.md` deliberately: that file has one owner, to keep
the numbering collision-free. Paste or renumber as you see fit.

Two of these are **corrections to entries that already exist** and are written to
sit inside R2-088 and R2-091 rather than as new numbers, because a correction in
place is more honest than a new entry that leaves the original claim standing.
Four are new, in the block R2-112 to R2-115.

---

## CORRECTION to R2-088 — the gate that finally measured roll shipped a metric that saturates, and its default input was a generation old

Two corrections, and the first is the one that matters.

**The metric was wrong.** `tools/horizon_gate.py` measured tilt as
`asin(right.z)` — the angle of the camera's right axis above the horizontal
plane. That saturates at ±90°: it cannot distinguish a camera rolled θ from one
rolled 180−θ, and **as a camera passes through fully inverted it returns to
zero.** The correct image rotation is `atan2(right.z, up.z)`, and the sign of
`up.z` settles it in one character. The old metric discarded that sign entirely.

| frame | shipped `asin(right.z)` | true `atan2(right.z, up.z)` | up.z |
|---|---|---|---|
| **f2651** | **+1.99°** | **+176.65°** | −0.594 **inverted** |
| f2661 | −52.92° | −101.23° | −0.158 **inverted** |
| f2666 | −59.88° | −81.71° | +0.126 |
| f2680 | −33.83° | −36.97° | +0.740 |

The camera is **fully inverted for 28 consecutive frames, f2636–f2663**, peaking
3.3° from perfectly upside-down at f2651 — where the shipped metric reported
1.99°, i.e. level. **It called the worst frame in the film the best.**

So the claim R2-088 makes about itself — that it is the instrument nobody had —
stands, and the number it published, 59.88° in beat 6, was wrong: the peak is
122.93°, and f2666 is −81.71°, not −59.88°.

**Found by looking.** A render agent rendered f2666, measured the dominant
straight-edge direction *in the pixels* at +83° from horizontal, and refused to
accept a geometry number that disagreed with the picture. The instrument had six
controls, a census and a published finding, and not one of them was a frame.

**Second correction, and it is the same failure one level out. The gate's own
negative control was failing, and not because the gate was wrong.** See R2-115
and R2-114 below: `--selftest` reported `HORIZON_GATE_SELFTEST_BROKEN` on a clean
tree because the gate defaulted to `render/film11_path.json` and film12 — built
twenty minutes later with R2-085's fix in it — was never wired in. Anyone
re-running the selftest to check R2-088's finding would have been told the
instrument was broken, while looking at the wrong path.

Both are fixed. Selftest is 7/7, with a new synthetic arm P4 — a camera rolled
exactly 170°, which reads 170.000000 on the corrected metric and 10.000000 on the
one this gate shipped with. **That arm exists because the broken metric survived
six controls.**

---

## CORRECTION to R2-091 — the waiver is WITHDRAWN, and the roll it waived has been fixed rather than accepted

R2-091 waived beat 6's roll as "a banked peel-off, not a defect", on the strength
of f2680 and f2694. **Both bracket the peak.** The peak was then rendered and it
does not read:

* **f2666** — the frame is on its **side**. The track runs top-to-bottom, the pit
  garages are a vertical stripe against the left edge, and there is **no sky and
  no horizon in it at all**. Confirmed by a second reader on the same render.
* **f2661** — the pit-lane lines run vertically down the left edge; the car is
  vertical. Also on its side.
* **f2680 reads as a bank, and the reason is visible: it has sky in one corner,**
  so the viewer can tell which way up is. f2666 has none.

So the waiver held from about f2673 onward and **did not hold across
f2658–f2670**. A waiver written from bracketing frames is an assumption, and the
peak refuted this one.

**The part of R2-091 that generalises still stands and was not touched:** the
gate was never re-tuned to stop firing. It kept failing beat 6 until the camera
was fixed.

**And most of the inversion was genuinely harmless — checked, not assumed.**
f2646 and f2651 were rendered: near-nadir shots in which the car fills the frame
with no world reference, so being upside down in them is invisible. The
`|pitch| ≤ 45°` scope was doing its job. The damage was confined to the frames
where the world re-entered shot while the roll was still past vertical.

**The waiver is now moot rather than merely withdrawn.** R2-112 removes the roll:
worst tilt with a horizon in shot over f2600–f2714 goes −122.93° → **1.71°**, 32
FAIL frames → **0**, 28 inverted frames → **0**. The shipped rolled path is kept
as `docs/horizon_pre_R2112_path.json` and is now this gate's positive control.

---

## R2-112 — the peel-off rolled the camera past vertical with the world in shot, and the roll reference had changed subject halfway through

Thirteen frames, f2658–f2670, on their side. The pictures are in
`work/r2112/`; f2666 before and after is the pair to look at.

**Root cause, and it is not the correction rate.** `look_quat` rejects world up
as a roll reference once it comes within 26.7° of the view axis — pitch 63.3° —
and beat 6's peel-off carries the view through **pitch 80.5°**. So for the whole
nadir pass the roll was corrected toward the **direction of travel**, which is a
good reference for a top-down follow and has nothing to do with level, while the
error against world up grew unwatched to **163° by f2638**. Everything after that
is the error being paid back at the 3°/frame limiter — **38 consecutive frames at
3.00–3.30°/frame, f2657 to f2694** — and the world comes back into shot at f2657
with 123° still owed.

**Fixed by holding world up as the reference through the pass** (`PEEL_REF_MIN`
0.15, i.e. to pitch 81.4°) so the error never accumulates, plus a raised
correction limit inside the same window. Both are scoped to a window derived from
the beat sheet — `PEEL_LEAD_FRAMES` before beat 6's declared peel key to the start
of beat 6 — and the build prints the window together with the near-vertical span
it actually caught, so a window that stops containing the thing it exists for
cannot do so silently. It caught 18 near-vertical keys, f2630–f2656; the film's
other 26 are untouched.

| cone | rate | worst tilt f2600-2714 | FAIL frames | inverted | beat 5 smear | campath |
|---|---|---|---|---|---|---|
| 0.45 | 3 | −122.93° | 32 | 28 | 16.18 % | PASS *(shipped)* |
| 0.15 | 8 | 31.61° | 13 | 0 | 18.92 % | PASS |
| **0.15** | **10** | **1.71°** | **0** | **0** | **22.07 %** | **PASS** ← shipped |
| 0.15 | 12 | 1.71° | 0 | 0 | 25.47 % | FAIL |
| 0.45 | 15 | 1.71° | 0 | 0 | 47.83 % | FAIL |

Ten is **bracketed**, not tuned: eight does not finish the job, twelve is the
first value campath refuses. The control — cone 0.45, rate 3 — rebuilds the
shipped path **bit-identically**, 0.000000e+00 on position, quaternion and lens
across all 2,978 frames. Beats 1, 2, 3, 4 and 6 are unchanged to the digit. The
four beat-1→2 invariants are exact: chord 2.0893 m, speed 1.2727 m/s, look
13.2504°, lens −0.051 mm, and every derived seam figure is identical.

**R2-089's two candidates were re-costed against the corrected metric and both
rejections stand.** The global limit reproduces to the digit — 47.83 % of frame
width at f1800, which is R2-085's own defect class.

**AND THE OBVIOUS THIRD CANDIDATE WAS BUILT, MEASURED AND THROWN AWAY, which is
the part worth keeping.** Raise the limit wherever the horizon is *out* of shot,
on the argument that such a frame has nothing for the roll to be level against —
and f2646 and f2651 were rendered and do support that argument *for those frames*.
Swept at 6/10/15/18/24/30/45 it cost **47.83 % at f1800 and 27.81 % at f75: the
same cost, to the digit, as the global fix it was supposed to improve on.**

> **The pitch test is not a scope. The correction limit only ever BINDS where the
> view is near-vertical — that is the only place transport outruns 3°/frame — so
> scoping it to near-vertical views selects every frame it was already acting on
> and excludes none of them.** f1800 sits at pitch 64.0° carrying 88.0° of roll
> and f75 at pitch 80.6° carrying 112.9°; in both, the roll is plainly visible
> because **the subject** is in frame even though the horizon is not. "No horizon"
> was verified to mean "no visible roll" on two frames of beat 6 and assumed to
> mean it everywhere else. It does not.

**C1 overstates a roll, and the bracket was still drawn on it rather than argued
with.** campath's C1 is `2·acos|q₀·q₁| / hFOV` — the total rotation angle between
two frames — so it cannot tell an axial roll from a pan. 22 % of frame width is
what the **corners** do; the centre, where the car is, does not move.

---

## R2-113 — the closing hold was a freeze, and no single lens can show the circuit and the wound

The last 3 s is **0.00 m of camera movement over 72 frames**, so at a fixed lens
f2906 and f2978 are the same picture: mean |difference| **0.8/255**, 56 pixels of
2.07 M differing by more than 16. It is not a held frame, it is a still.

R2-090 closed the car: it and the wound are **966 m apart** at f2978, and
requiring both in frame pushes the camera back at exactly the rate a longer lens
gains, so the car is pinned at `1920 × 5.698 / 966` = **11.3 px** from any
position at any focal length. The car's beat is real and lives at f2756–f2832.

The other two subjects are resolved **in sequence rather than in one frame**:

| lens | mullion pitch | sky in frame | the wound | the circuit |
|---|---|---|---|---|
| 18.75 mm | 3.7 px | 29.3 % | 20 px — no resolvable grid to be a hole *in*; reads as a specular hit | 1143 m |
| 40 mm | 7.9 px | 5.7 % | 37 px | 536 m, reads best |
| 74 mm | 14.6 px | 0.0 % | 65 px — grid crisp either side and **absent** across the middle, dais ring legible through it | 290 m, gone |

So the hold **opens at 40 mm and pushes to 74 mm**. Two lens keys move and
nothing else: no key moves in time or space, the hold's two keys keep their
identical positions, and the built path is **0.0022 m over the 72 frames** with
the aim gate at 0.06° and frame-offset 0.001.

---

## R2-114 — a gate's default input was a generation old, and its own negative control failed because of it

`horizon_gate.py --selftest` reported `HORIZON_GATE_SELFTEST_BROKEN` on a clean
tree. The N1 arm — *beats 2 to 5, 1,808 frames, must PASS* — came back FAIL with
**155.65° of roll at f1464** and 50 FAIL frames.

f1464 is fine. The gate defaulted to `render/film11_path.json`; film12 was built
twenty minutes later with R2-085's fix in it and the default was never moved. On
film12 the same frames read −0.00° and the arm passes.

> **A negative control that fails because its INPUT is stale is
> indistinguishable, on the printed line, from the gate being broken** — and this
> file had just been used to publish R2-088.

The default is now `world/camera_rig_path.json`: the camera rig's own output,
which `build_camera_rig.py` writes and `build_film_scene.py` consumes. A numbered
`film*_path.json` is a snapshot of it and there is a new one every time anybody
assembles a scene. **Deliberately not "the newest film\*_path.json"** — picking up
whatever a passing agent dropped in `render/` is how a gate ends up judging
something nobody chose. Instead a check refuses to let the named default rot: if
the newest assembled film scene holds a *different* camera from the rig, the gate
says so and names the file, because the rendered frames come from the scene.

---

## R2-115 — the positive control was anchored to a defect, and fixing the defect took the control away

`horizon_gate.py`'s P3 arm read *"the **live** `--path` over f2640–2700 must
FAIL"*. It was the arm proving the gate fires on a rolled camera. R2-112 levelled
that roll, so P3 began reporting *expected FAIL, got PASS* on a healthy film.

**The version that would have been worse is the one that looks better.** Had P3
been written as a bound — "at least N FAIL frames", "no better than X degrees" —
it would have gone **quietly green** the moment the roll was fixed, and the gate
would have had no positive control from that instant on with nothing on the
printed line saying so. That is R2-072, for the second time on this project.

**A positive control cannot be a defect in the artefact under test, because the
whole point of the work is to remove it.** So the rolled camera is kept:
`docs/horizon_pre_R2112_path.json` is the shipped pre-fix path — 28 inverted
frames, −122.93° at f2657 — and P3 asks the gate to fail it forever. If the file
is missing, the arm FAILS and says the gate has no positive control, rather than
being skipped. In `docs/` and not `work/`, for the reason `seam_gate` already
gives about its own `--pre` control: work/ is gitignored, and a control a tidy-up
can delete is not a control.

---

## Open, and deliberately not given a number without being asked

**The peel-off's BANK is gone, and it was not a design.** R2-091 waived f2680's
−36.97° because it "reads as a banked aerial — the shot a helicopter makes
peeling away from a subject". That bank was the tail of the 176° runaway bleeding
off at the limiter's rate, so removing the runaway removes it: the fixed f2680
measures −17.5° of dominant edge against the level reference of −28.5°, i.e.
level. Rendered, it is a clean legible aerial down the pit straight, and it is
flatter than the frame R2-091 liked. **The bank cannot be kept without keeping
the runaway that produced it** — every swept value either leaves the inversion
(rate ≤ 8) or removes the bank with it (rate ≥ 10). If a banked peel-off is
wanted it has to be AUTHORED as a declared roll on beat 6, which is R2-089's own
closing recommendation and is a change to the beat sheet, not to `look_quat`.

**Nothing in this film gates how fast the lens moves.** `campath_gate` computes
`dlens = np.abs(np.diff(L))` and then never uses it — a dead variable, no
detector, no bound. R2-113 introduces the film's largest single lens move, so it
was measured against the film instead: converting focal length to the motion it
puts on a frame-edge pixel, the push peaks at **0.659 % of frame width per frame
at f2935**, against **2.787 % at f2254** which beat 5 already ships. The push is
4.2× gentler than a lens move already in the film. That is a measurement, not a
gate, and the gap is real.
