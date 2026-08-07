# STAGING — R2-851 to R2-880 · beat 6, the closing wide

Owner: the beat-6 camera. Merge by identity, never by position.
**Nothing here has been rendered yet** except where a frame is named. A candidate
render of R2-853 is in flight; every claim below that is not marked MEASURED ON
FRAMES is measured on the camera path, not on pixels.

The client's note, in full:

> "Also the ending I don't like. We just zoom out so you see all the patches in
>  the land etc."

---

## R2-851 — the closing wide contains a 91.5 deg/s whip pan, and the film's law forbids one

**MEASURED** on `world/camera_rig_path.json`, the shipped rig.

`sheet["aim"]["6_ending"]` hands the subject off from the car to a fixed point —
the breached facade at `[15, 0, 3.1]` — over `car_until_t 4.0 → point_from_t 6.0`.
At the moment of the hand-off those two subjects are **82 deg apart** in bearing
from the camera, so the aim does not ease between them, it *travels* between them:

| | shipped | this candidate |
|---|---:|---:|
| peak pan, beat 6 | **91.5 deg/s** at f2832 | 11.0 deg/s at f2810 |
| mean pan, beat 6 | 10.94 deg/s | 3.77 deg/s |
| worst rotation smear @4K, 180 deg shutter | **84.8 px** at f2832 | 36.5 px at f2976 |

f2814–f2858 is 44 frames — 1.83 s — of ~95 deg of yaw. At the 18.8–19.5 mm lens
the beat is carrying there, that is 84.8 px of uniform smear across the whole 4K
frame. On the 720p encode the client watched it is visible as a mush: the frame
at f2835 has no readable edge anywhere in it.

**The continuity gate does not see this and cannot.** `rot_limit_deg` is **45.0
degrees per frame** — 1,080 deg/s — so a whip would have to be twelve times
worse before the gate noticed. The gate's own report calls beat 6 the *best*
beat in the film: `aim_per_beat["6_ending"].ang` is **0.054 deg**, because the
camera is pointed at its declared subject to a twentieth of a degree the entire
time. It is aimed perfectly at the wrong thing, and both facts are true at once.

> The brief's law is *"Zero cuts. Zero crossfades. **Zero hidden whip-pan
> cheats.**"* This whip is not hiding a cut, so it does not violate the letter.
> It is still the one gesture the law names by name, and it is in the last beat.

**Recommend a rate bound on the beat sheet**, not just the per-frame step: pan
rate has no gate anywhere in this film, exactly as R2-113 found lens rate had
none (`campath_gate` computes `dlens` and never uses it). A sensible bound is
the smear it produces, since that is the thing that damages the picture:
`rate_deg_s * (shutter/fps) * (3840 / hfov_deg)` under ~40 px at 4K.

---

## R2-852 — the film's subject leaves the film 5.5 s before the film ends

**MEASURED** by projecting `anim/carpath.Car` through the shipped rig, per frame.

| frame | car distance | car width @4K | screen x (of 3840) | |
|---:|---:|---:|---:|---|
| f2714 | 85 m | 200.0 px | 1920 | centred, the seam |
| f2790 | 300 m | 50.0 px | 1920 | centred |
| f2810 | 381 m | 38.5 px | 1920 | centred |
| f2830 | 464 m | 31.3 px | **3436** | at the right edge |
| f2860 | 580 m | 24.7 px | 5385 | **off frame** |
| f2978 | 1000 m | (45.8 px) | 11641 | off frame, 84 deg away |

The car exits frame at roughly **f2845** and never returns. **133 frames — 5.5 s
— of the film's ending have no car in them.** The film's last three frames were
independently found to have the car hidden behind `BR_FenceMesh_L03`; that is
true but it is downstream of this. The car is not occluded at f2978, it is
*84 degrees outside the field of view*.

R2-113 established the constraint honestly and it still holds: the car and the
wound are ~1 km apart at f2978 and no single frame can hold both. **What R2-113
did not weigh is that choosing the wound costs the film its subject for the last
quarter of the beat**, and the subject is the thing the audience has been asked
to care about for 113 seconds. That trade was never stated as a trade.

Note also: the shipped hold is **0.0022 m of movement and 0.00 deg of pan over
72 frames** — R2-113's own words, *"it is not a held frame, it is a still"* —
and its remedy was a lens push on a frozen camera. A lens push on a locked-off
frame is what a still photograph being zoomed looks like. **That is precisely
what "we just zoom out" is describing**, and the client is describing the last
gesture of the film accurately.

---

## R2-853 — CANDIDATE: lens and aim only. Every camera position byte-identical.

`docs/R2851_beat_sheet_CANDIDATE.json`, built to
`work/r2851/camrig_R2851.blend` + `_path.json`.

    >> STAGE RESULT: CAMERA_RIG_CONTINUOUS_AND_AIMED

Two edits and nothing else:

| `beat6.keys[].t` | −3.0 | −1.0 | 0.0 | 2.0 | 4.0 | 6.0 | 8.0 | 11.0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lens shipped | 32 | 28 | 24 | 21 | 19.5 | 18.75 | 40 | 74 |
| lens candidate | 32 | 28 | 24 | 21 | **22** | **30** | **55** | **130** |

and `aim["6_ending"]` becomes the car for the whole beat (`car_until_t` and
`point_from_t` both 11.0, so `fixed_point` stays declared and the
`undeclared()` validator is still satisfied).

**Every `world[]` and every `speed` is unchanged, so the position path is not a
new curve — it is the same curve.** Verified frame by frame against
`world/camera_rig_path.json`:

* **f1–f2714, worst position delta `0.000e+00` m, quaternion `0.000e+00`, lens
  `0.000e+00` mm.** The candidate is bit-identical to the shipped film up to and
  including the seam frame.
* **The f2714/2715 seam is arithmetically the same object in both:** 2.5454 m
  and 0.1063 deg in the shipped rig, 2.5454 m and 0.1063 deg in the candidate.
  The 1.33 % / ±0.72 MAD pixel measurement of that seam is not at risk, because
  no input to it moved.
* f2715–f2978 worst position delta **2.26e-3 m** — the Hermite resample's own
  float noise, not a change.
* `worst position jump 4.247 m at f1209` and `worst rotation step 12.957 deg at
  f2634` — both identical to the shipped rig, i.e. beat 6 does not become the
  film's worst case in either metric.

What it buys, on the path (**not yet on frames**):

* peak pan **91.5 → 11.0 deg/s**, smear **84.8 → 36.5 px**. The whip is gone —
  not smoothed, *gone*, because the camera is now following something that
  genuinely moves through that arc instead of jumping to a point 82 deg away.
* the car is in frame on **every frame of the beat**, and it never drops below
  **35 px** at 4K.
* the last 3 s stops being a still: **2.89 deg of pan** across f2906–2978 where
  the shipped hold has 0.00, and the car **grows from 45.8 px to 78.5 px** as
  the lens lengthens. The hold now has a reason to be a hold.
* the wide still happens, and earlier, where it is a landscape rather than a
  plan: f2763–f2811 at 21–22 mm and 62–99 m altitude, ~483 m across frame.

**What it gives up, stated plainly:** the breached facade. It is no longer in
the last frame at all. See R2-855.

---

## R2-854 — the "patches in the land" are a 155 m Voronoi partition, and the lens crops them but does not fix them

Mechanism established by forensics on `world/build_terrain.py` (findings are
that agent's; recorded here because they decide what the closing wide is allowed
to look at). **Do not merge this as a terrain fix — it belongs to #127's thread
and to whoever owns `build_terrain`.**

`field_pattern()` (`build_terrain.py:1140-1163`) is a Voronoi partition on a
**155 m lattice** warped by only ±46 m, so its cells are convex polygons with
**straight edges**. One `fid` per cell drives *both* colour terms:

* `ter_field` → `pal[floor(fid*3)]`, a **three-entry palette**, mixed in at a
  hard **0.55** constant (`build_terrain.py:2818`) — `pal[2]` = `(0.290, 0.215,
  0.093)` is the tan/khaki region;
* `ter_dry` → `0.15 + 0.85*fid`, swinging the other 45 % between albedo 0.051
  and 0.127 — **1.3 stops**.

Because they share `fid` they **add instead of decorrelating**, and the
transition occupies exactly one 2.5 m vertex cell. Meanwhile the ground shader's
colour spectrum has **nothing at all between 0.385 m and 7.7 m**, and nothing
unconditional between 0.385 m and 19 m. At the shipped closing wide's ~339 mm/px
everything at or below 0.4 m is sub-pixel, so **the only structure that survives
into the frame is 19 m and coarser** — which is to say, the patches, and nothing
else. Grass geometry is culled to zero beyond 700 m of the camera path, so most
of that frame is bare shaded mesh.

**What the candidate's lens does about it, arithmetically:**

| | shipped | candidate |
|---|---:|---:|
| widest lens in the beat | 18.75 mm | 22 mm |
| widest frame span | ~1,143 m | ~483 m |
| 155 m field cells across the widest frame | ~7 | ~3 |
| final-frame span | ~595 m | ~277 m |
| 155 m field cells in the final frame | ~4 | **~1.8** |
| final-frame ground sampling | ~74 mm/px | ~72 mm/px |

So the lens **removes most of the patch boundaries from the frame** — that is a
real and cheap answer to the literal complaint. It does **not** make the ground
good, and it makes one thing worse: at 72 mm/px the missing 0.4–19 m detail band
lands at 5–260 px, so the smoothness is now *more* legible per pixel even though
the blotching is less legible per frame. **The candidate's final frame is
centred on T1, which is inside the camera path's own grass-scatter radius**, so
it should have real blade geometry where the shipped final frame (aimed across
6 hectares of paddock concrete and open field) has none. That is a prediction,
and the 4K stills in flight are what tests it.

**Minimum terrain work this shot still needs, in priority order** (all
procedural, all inside existing files, none of it mine to land):

1. **Decorrelate `ter_dry` from `fid` and feather the cell boundary using
   `fdist`** — which is already computed and already used for hedges. ~6 lines.
   Kills the straight-edged patches outright.
2. **Fill the 0.4–60 m hole in `mat_ground`'s colour ladder** and the matching
   normal gap between `bump1` (0.385 m) and `bump2` (7.69 m). `ter_dist` is
   already created as an Attribute node at `build_terrain.py:2785` **and linked
   to nothing** — the crossfade hook exists.
3. **`SKY_STRATA=1`.** Structured low haze is written, tested and documented in
   `build_sky.py:944-966` and is off by default. It is the one-line fix for the
   featureless brown horizon band, which occupies ~15 % of the shipped closing
   frames.
4. Treeline: the beat-6 treeline is **16 unique L2 meshes repeated 150–256×
   each** (birch L2 is 4,089 instances from 16 meshes). That is 1.5–2.5× past
   this project's own "one tree spammed 100 times" red line, and it is only
   visible from altitude — i.e. only in this beat.

**Verdict on the ordering question:** the terrain work does *not* block the
camera change, and the camera change should go first. The reason is not cost, it
is that a beautifully textured version of the shipped ending is still an ending
with no subject in it. Fixing the ground makes the shipped wide *not ugly*; it
cannot make it *about* anything. Conversely the candidate reduces the ground's
share of the frame, which buys the terrain thread time without buying it an
excuse.

---

## R2-855 — what the ending is for, and the alternative that was rejected

The shipped ending's declared content is *"the circuit with the breached
showroom in it"*, and its last gesture is a push from 40 mm to 74 mm that brings
the wound from 37 px to 65 px. R2-113 did honest work to make that read and its
measurements are sound. **It still does not land, and the reason is not
resolution.**

At 65 px in a 3840 px frame the wound is 1.7 % of frame width, sitting in a
field of transporters, containers, light masts and paving of equal contrast,
and the audience last saw that building **80 seconds earlier, from inside, at a
completely different scale**. It asks a viewer to recognise a grey shed and then
read a hole in it, with no isolation, no contrast cue and no lead-in. The client
watched exactly this and reported seeing patches of land — which is what you see
when the intended subject does not resolve as a subject.

**The candidate's answer to "what is being revealed that is worth the last four
seconds":** the car, alone, still running, getting further away and *sharper* as
the lens lengthens on it. The film ends on the thing it is about, leaving under
its own power. The pull-back still happens and still reveals the circuit — it
just stops climbing into a plan view and stops turning its back on the car.

**The alternative, recorded so nobody re-derives it:** keep the wound and fix
its legibility instead — isolate it with light, or push further than 130 mm on
it, or move the hold position. Rejected for the beat because (a) the whip
survives it, since the 82 deg hand-off is what buys the wound at all; (b) it
still costs the last 5.5 s of the film its subject; and (c) the frame around the
wound is a truck park, and no lens fixes that.

**A third option that was NOT rejected and is not mine:** the car does not have
to still be at 300 km/h at f2978. `anim/carpath.Car` extrapolates past the end
of telemetry *"along the circuit's own centreline at its final speed"*
(`carpath.py:28-33`), which is a deliberate choice and a defensible one. A car
that decelerates on its lap-down would let the camera stay much closer to it and
would make a far tighter ending possible. That is a change to the car, not the
camera, and it should be decided by whoever owns the car — but the closing wide
is the only beat it would affect.
