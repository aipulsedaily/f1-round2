# STAGING — R2-541 … R2-580

Per-beat pixel-peep defect gate against `out/seq/r1full` (task #38), the first
attempt to look at the whole film as pixels.

**Method.** Seven contact sheets covering every frame on disk, then full-resolution
reads of 12 frames and 14 magnified crops. Every verdict below was reached by
looking at an image. Where a number appears it is there to size a thing I already
saw, never to stand in for having seen it. Crops are in `docs/peep/`.

**Provenance.** `r1full`, 1280×720, 64 samples, `spec_hash 2b46bc3e1868e66d`,
mean 60.97 s/frame. These are 720p proxies of a 3840×2160 / 24 fps / 2,978-frame
delivery. Anything whose verdict depends on 4K detail is marked as undecidable here.

---

## R2-541 — the pass this gate was opened on is not finished; it is 26 % of the way through, and every one of the nine dense blocks has zero frames

The gate was briefed against *"the first full render ladder pass, which has just
completed — 127 frames … covering frames 1 through 2978 … plus nine dense blocks.
Zero blank, zero failed."*

**The directory is being written to while I read it.** Frame counts taken by me,
by `ls`, minutes apart:

```
15:22:04   r1full_000733.png     (mtime of the newest file when I started)
15:30:35   r1full_000775.png     136th … no, 135th file
15:33:03   r1full_000781.png     136 files
```

One frame every ~72 s, ascending, stride 6. **`manifest.json` is a snapshot, not
a ledger** — written 15:24:33, it described 130 frames while 135 were on disk.
Re-reading it later gives a different, larger number. Any statement of the form
"the pass contains N frames" is true only of the instant it was taken.

**The job table settles it.** From `manifest.json` `summary.jobs`:

| job | range | step | state | done |
|---|---|---:|---|---:|
| `b3d8bf1c783b` | 1 … 2001 | 1 | **done** | 6/6 |
| `bf01e668aca9` | 1 … 595 | 6 | **done** | 100/100 |
| `b84197ef5120` | 601 … 1195 | 6 | **running** | 26/100 |
| `e6a38372a20a` | 1201 … 1795 | 6 | queued | 0/100 |
| `6ca53e616c34` | 1801 … 2395 | 6 | queued | 0/100 |
| `96ac3f6721d4` | 2401 … 2977 | 6 | queued | 0/97 |
| `c099333b30b7` | 400 … 519 | 1 | queued | 0/120 |
| `1dc5651c48fc` | 745 … 864 | 1 | queued | 0/120 |
| `47bfcdc6d5f3` | 865 … 984 | 1 | queued | 0/120 |
| `a5bbc5c59bee` | 1041 … 1160 | 1 | queued | 0/120 |
| `b47eecaf6f4a` | 1161 … 1280 | 1 | queued | 0/120 |
| `5f96c288bf7b` | 1900 … 2019 | 1 | queued | 0/120 |
| `5e1f754b3f7b` | 2575 … 2694 | 1 | queued | 0/120 |
| `ae315375b3c3` | 2695 … 2814 | 1 | queued | 0/120 |
| `a452013422e6` | 2859 … 2978 | 1 | queued | 0/120 |

(plus 22 `canceled` step-1 jobs from an earlier plan, all 0/120.)

**The nine dense blocks exist — as nine queued jobs holding 1,080 frames, none of
which has been rendered.** The brief's "nine dense blocks" is a correct reading of
the *plan*. It is not a description of the *output*. What is on disk is one
6-frame probe (1, 2, 900, 901, 2000, 2001, all written 12:40–12:44) and a stride-6
crawl that started at f1 and has reached f781.

**Remaining:** 74 frames in the running job + 297 in the three queued stride jobs
+ 1,080 in the dense blocks = **1,451 frames ≈ 24.6 h** at the measured 61 s/frame.

*Generalises to:* **a job plan read as a job result.** Every number in the briefing
— 127, "1 through 2978", "nine dense blocks", "zero failed" — is present and
correct somewhere in `manifest.json`. Four of them come from `summary.jobs[*]`
(what was *asked for*) and one from `summary.verdicts` (what *arrived*), and the
two were merged into a single sentence. A queued job and a done job are one
`state` field apart and the field was not read.

---

## R2-542 — five of the six beats have never been rendered. Beats 2, 4 and 6 have zero frames; beats 3 and 5 have two frames each, and both pairs are adjacent

Beat boundaries from `docs/beat_sheet.md` at 24 fps:

| beat | frames | n | frames sampled | distinct instants | % of beat |
|---|---|---:|---|---:|---:|
| 1 `assembly` | 1–792 | 792 | 1, 2, 7 … 781 (stride 6) | 132 | **16.7 %** |
| 2 `launch` | 793–864 | 72 | — | **0** | **0 %** |
| 3 `breach` | 865–1056 | 192 | 900, 901 | **1** | 1.0 % |
| 4 `transit` | 1057–1190 | 134 | — | **0** | **0 %** |
| 5 `lap` | 1191–2714 | 1524 | 2000, 2001 | **1** | 0.13 % |
| 6 `ending` | 2715–2978 | 264 | — | **0** | **0 %** |

Beats 2–6 are **2,186 frames (91 s, 73 % of the film)** represented by **4 frames
at 2 instants**, 0.18 % by count and — because 900/901 and 2000/2001 are
consecutive, 1/24 s apart — **2 moments out of 2,186**.

What that forecloses, concretely, because each is a *motion* defect and a pair of
adjacent frames cannot show it:

* the launch wheelspin (beat 2) — the one sanctioned rolling-contact violation,
  ~10 frames, **none rendered**;
* the speed ramp into and out of the breach (beat 3) — an 8 s eased time curve
  seen at one instant 1.5 s in;
* whether shutter scales with world-time during the ramp (motion blur at slowed
  speed) — needs consecutive frames *inside* the ramp;
* the exposure animation from interior spill to daylight over ~15 frames (beat 4)
  — **none rendered**;
* the ≥3 s near-hover doppler pass and the onboard-follow at 330 km/h (beat 5);
* the closing wide and the 3 s hold, including whether the breached showroom is
  visible with its wound (beat 6) — **none rendered**;
* **every seam between beats.** All five inter-beat transitions fall in unrendered
  frames. The ONE-SHOT LAW is the film's top constraint and not one of its joins
  has been looked at.

Even beat 1 is not covered to its end: the last sampled frame is f781 and the beat
runs to f792, so **the beat's own climax — the push onto the completed car with the
spot rigs ramping ~1 stop over 12 frames — has not been rendered either.**

*This entry exists so that no summary of this pass can say "the film is clean."*
The film has not been seen. One beat has been sampled; five have not.

---

## R2-543 — the car's bodywork renders TRANSPARENT for the whole of beat 1. It is a glass model of an F1 car, not a painted one

**The finding.** Monocoque, nose, sidepod and engine cover all render as tinted
transmissive material. You can see the internal lattice, the wiring, the far-side
suspension and the turntable *through* the skin, continuously, in every frame of
beat 1 where the body is in shot.

Evidence, worst to least ambiguous:

* `peep/r2541_f655_chassis_transparent_3x.png` — **f655**, 3×. The nose reads as
  smoked blue-green acrylic. The internal cellular structure and two internal rods
  are plainly visible through the outer surface. The teal livery survives only as a
  1-px edge line along the chine.
* `peep/r2541_f727_cockpit_5x.png` — **f727**, 5×. Through the sidepod skin: the
  internal web, the far-side floor, and the fact that **the cockpit is empty**
  (see R2-548).
* `peep/r2541_f727_chassis_transparent_3x.png` — **f727**, 3×, the same body from
  further out: the turntable surface is visible through the flank.
* Full frames **f643, f649, f655, f661, f667, f673, f679, f685, f691, f697, f703,
  f709, f715, f721, f727, f733, f739** — every wide of the seated car. Same read.
* It is also visible at the far end of the beat: **f1** (the tub, through the 84°
  down-angle), **f187–f229**, **f307–f349**, **f409–f445**.

**This is not the framing defect that was already logged.** R2-425 and R2-429
describe f25–f43 as *"a large translucent blue wedge fills the frame vertically"*
and treat it as a composition failure — the subject is unreadable because the
camera is too close and too steep. **The wedge is translucent because the material
is translucent.** Both entries had the pixel in front of them and named the wrong
cause, because at f25 the framing defect is real and sufficient to explain an
unreadable frame. At **f643–f739 the framing is fine** — a clean three-quarter wide
of the whole car on the turntable — and the car is still see-through. Fixing the
camera would not have touched this.

**Not intended.** No `x-ray`, `cutaway`, `ghost` or `translucent` art direction
appears in `part2.md`, in `THE-BRIEF-ROUND2.md`, or in the beat sheet. The brief
asks for paint with depth, carbon weave, crisp decals and clearcoat.
`DEFECT-LOG-R2.md` has no entry for it; the only nearby claim is at line 3276,
*"All four are opaque (Transmission 0, Subsurface 0, Alpha 1.0, Coat 0)"* — a
statement about four *track* materials reached via `marshal_post_column.NG`, not
about the car.

**Not decidable here:** whether the cause is Transmission, Alpha, or a backface /
normals problem. That is a blend-file question, not a 720p question. What is
decided is that the surface is not opaque.

---

## R2-544 — every aero surface renders as untextured grey clay. There is no carbon weave anywhere in beat 1

The brief makes this a named gate: *"carbon weave must resolve as actual weave (no
blur, no obvious tiling at macro distance), decals crisp at pixel level … edge
bevels present."* At the camera distances the beat sheet actually flies, at 720p:

* `peep/r2541_f727_frontwing_clay_3x.png` — **f727**, 3×. The front wing fills a
  third of the frame. Flat matte mid-grey, uniform, no weave, no decals, no
  imperfection layer, no clearcoat. Four dots on the endplate and one faint red
  line are the entire surface story.
* `peep/r2541_f631_frontwing_clay_2p5x.png` — **f631**, 2.5×. Same, plus the
  mounting pylons are untextured trapezoids, and the curved element surfaces show
  visible **banding / faceting** across the shading gradient.
* `peep/r2541_f511_tyre_notread_3x.png` — **f511**, 3×. A front tyre at a
  presentation distance: **no tread, no sidewall lettering, no rubber grain, no
  shoulder wear.** Smooth dark grey with a clean red band. It reads as moulded
  plastic.
* The rear wing at **f235–f283** is a plain dark slab across the frame for 2 s.
* The turntable, the showroom floor and the apron concrete (f900) are smooth
  gradients with no surface at any scale.

**What DOES read:** the steering wheel at **f367–f391** is the one part in the beat
that survives its close-up — buttons, rotaries, a legible display, grips with a
distinct material. It proves the pipeline can carry detail and that the rest of the
car simply does not have any. The halo assembly at **f139–f181** is second best.

*At 4K this gets worse, not better* — every one of these is a magnification of
nothing, and the beat's whole purpose is macro presentation.

---

## R2-545 — frames with no subject in them at all, graded `blank: OK` by the manifest

**f523** (`t = 21.79 s`) is a smooth dark-grey gradient with a white arc in the
top-left corner. There is nothing in it. **f493** is the same with a single thin
diagonal line. **f607** (`peep/r2541_f607_clip_2p5x.png`) is a completely
defocused tyre filling the frame — a shape, not a part. **f475, f481, f529** are
near-identical smears.

f523 and f493 fall inside the `CORNER_RL` / `CORNER_RR` presentation windows
(19.36 s–22.88 s); f607 is inside `CORNER_FR`/`CORNER_FL`. **Four of the fifteen
clusters have their mandated readable moment, and the readable moment is a grey
field.**

**The manifest grades all of them `blank: OK`,** because `blank` is a check on
whether pixels were written, and pixels were written. That is not a criticism of
the check — it is the point of this entry. I then tried to build a metric that
*would* catch them, and **it does not work either**:

```
frame   sd   coarse_sd (16x-downsampled, i.e. large-scale content, not edge energy)
 523  0.095   0.0944     a grey field with nothing in it
 493  0.067   0.0660     a grey field with one line
 283  0.099   0.0946     a large grey wing panel, legibly framed
 271  0.103   0.0992     ditto
2000  0.099   0.0954     the flying lap: car, kerbs, gravel, track, all present
```

**f2000 — a fully composed aerial with the car, the racing line, both kerbs and a
gravel trap in it — scores the same as f523, which contains nothing.** A structure
metric cannot separate "empty" from "wide". I am reporting the frames because I
looked at them, and reporting the metric's failure so nobody builds the gate on it.

---

## R2-546 — the only rendered frame of the breach shows a handful of clean flat panes, no dust and no debris cloud

**f900** (`t = 37.5 s`, 1.5 s into an 8 s beat) —
`peep/r2541_f900_breach_shards_3x.png`, and the full frame.

* The shards are **large flat panes with perfectly straight edges**, overlapping in
  a few planes. No thickness reads, no edge refraction, no tumble, no spin. They
  look like intersecting quads.
* **One** piece of small debris is visible in the crop. There is no dust burst at
  the breach, no shard cloud around the car, no secondary debris skittering. The
  ground debris that does exist reads as scattered dark specks — pepper, not glass.
* The car has already cleared the wall and is ~20 m onto the apron at 1.5 s into
  the beat, which makes the *money moment of the entire video* — the camera arcing
  through an erupting shard field at 15–25 % world-time — something that must be
  happening in frames 865–899, **none of which have been rendered**.

**Under-claimed deliberately:** one frame of an eight-second destruction sim
cannot tell you the sim is wrong. It tells you what this instant looks like, and
this instant does not look like an eruption. The verdict belongs to job
`47bfcdc6d5f3` (865–984), which is queued.

---

## R2-547 — a blank white advertising board in the beat-3 background, and a grandstand with no seats

`peep/r2541_f900_blank_billboard_5x.png` — **f900**, 5×.

A **pure white, untextured, self-lit rectangle** stands where a trackside
advertising board belongs. It is brighter than the sky behind it. It carries no
artwork and no text. The brief calls for *"fictional-brand advertising boards"*;
this is the placeholder they were meant to replace.

In the same crop the grandstand is a dark grid with yellow dashes and no seat
geometry, and the pit building is an untextured cream block. `peep/r2541_f900_gantry_4x.png`
shows the catch fencing and gantry truss as bare posts against a flat blue-grey
band — **no signage of any kind on the gantry in the only frame that shows it**
(see R2-549).

Beat 4 is *"the world-design linchpin … dressed at full fidelity because the camera
crosses it in one take."* Its 134 frames are unrendered. f900 is the only look
anyone has had at that dressing, and it shows a placeholder.

---

## R2-548 — the cockpit is empty in the payoff frame of beat 1

`peep/r2541_f727_cockpit_5x.png` — **f727**, 5×. Through the transparent tub
(R2-543): no driver, no seat, no belts, no helmet. Bare structure.

The driver exists — `tools/place_driver.py`, `world/car_anim_driver.blend`,
`docs/driver_placement.json`, and R2-401/R2-402/R2-406's containment work. The
log's own note is *"the look scene is not the film"* (`build_driver_look.py` ships
the car, the driver, sun and sky — no track, no grandstands). **The scene this
ladder is rendering has no driver in it.**

Logging it so it is not rediscovered as a regression, and so that "which blend is
the ladder actually rendering" gets an answer before 24.6 h of farm time lands
against it.

---

## R2-549 — the two known live items: one confirmed with a caveat, one confirmed outright, and the doubling is not where it was said to be

**(a) The 84° opening — CONFIRMED, exactly as described.** **f1** full-frame: the
camera is looking near-straight down into the monocoque. f1–f19 are a plan view of
the tub; the floor signage `MERIDIAN / 3600 mm WHEELBASE` runs up the right edge
and is clipped. Matches R2-425 clause for clause. No further evidence needed.

**(b) The doubled sign text — CONFIRMED, but on the SHOWROOM FACADE, not the
gantry.**

`peep/r2541_f727_meridian_doubled_10x.png` — **f727**, 10×. The `MERIDIAN` wall
sign inside the showroom: **every glyph carries a second offset copy** — an outer
bright outline and an inner bright outline with a dark seam between them, on M, E,
R, D, I, A and N alike. The strapline beneath it is **completely illegible**,
reduced to a broken dashed smear.

`peep/r2541_f727_gantry_24p1_6x.png` — the `24 / P1` pit board, 6×. `24` and `P1`
read (the `1` renders as a bare stroke indistinguishable from `I`). **The two lines
beneath are unreadable blobs** — glyphs colliding into each other, which is what
two overlapping strings do.

`peep/r2541_f727_meridian_sign_5x.png` — the same facade sign at 5× with its
surroundings, showing the wall panel it sits on and a **third** signage element
(`peep/r2541_f727_floating_panel_5x.png`, 5×): a dark angled panel high on the
right of f727, on a pole, whose text is illegible in the showroom's low key. Three
text-bearing panels in one frame; two are unreadable and one is doubled.

`peep/r2541_f900_gantry_4x.png` — the **track** gantry, the panel the known item
names, in the only rendered frame that contains it: **it carries no legible text at
all** at this distance and angle. I cannot confirm or deny doubling on that panel
from this pass.

**Where I stop.** At 720p a 45 mm offset on a sign this size is ~2 px, and **an
extruded metal letterform lit from above produces the same face-plus-bevel double
edge.** I cannot separate the two hypotheses from these pixels. What I *can* assert
without that ambiguity: **the sub-line text on both panels is illegible**, which is
the signature of two small strings overprinting, and **it is happening on two
different panels in the showroom** — so if the queued rebuild fixes only the panel
that was diagnosed, the facade sign and the pit board will still be wrong. That is
the part of this that contradicts the framing I was given.

---

## R2-550 — the flying lap reads as a scale model: unmotivated depth of field plus an untextured track

**f2000** (`t = 83.3 s`), full frame, and `peep/r2541_f2000_car_contact_5x.png`.

* **Tilt-shift.** The frame is sharp in a narrow horizontal band through the car
  and heavily blurred above and below it. At this subject size and distance —
  aerial, car ~200 px of 1280 — no real lens does that, and the effect is the one
  that makes photographs of real places look like model railways. The circuit
  reads as a tabletop.
* **The asphalt has no texture** (`peep/r2541_f2000_asphalt_notexture_3x.png`,
  3×, a 400×300 patch of track and kerb). A smooth grey-brown gradient. No aggregate, no
  the-brief's *"2–3 mixed detail scales"*, and **no rubbered-in racing line** —
  the single most legible cue that a circuit is a circuit. The white line aliases.
* The gravel trap smears into radial streaks that read as texture stretching
  rather than motion blur.
* The car's livery at this distance reads as mottled blue-black camouflage.
* The tyres show the same clean orange sidewall band and no tread as R2-544.

**Not decidable at 720p:** whether the asphalt has fine detail that a 720p proxy
has simply lost. The *absence of the racing line* is decidable and it is absent —
that is a metres-wide feature, not a fine one. The DOF is decidable and it is wrong.

---

## R2-551 — what I could NOT assess, and why

* **Beats 2, 4 and 6 — no verdict of any kind.** 470 frames, 19.6 s. Nothing was
  rendered. This includes the launch and its wheelspin, the whole transit and its
  exposure ramp, and the entire ending. See R2-542.
* **Beats 3 and 5 — one instant each.** Everything about them that is a property
  of *motion* (the ramp curves, shutter scaling, the doppler hover, suspension
  compression at the fast apex, the deceleration into the closing wide) is
  untouched by two adjacent frames.
* **All five beat seams.** Unrendered. The one-shot law is unverified end to end.
* **Beat 1's own ending**, f782–f792, including the 12-frame 1-stop light ramp.
* **Anything that lives at 4K.** Carbon weave, decal edges, bevel widths, the
  gantry-sign doubling (R2-549), banding vs. dither on curved aero. A 720p proxy
  cannot decide any of them. R2-544's verdict is *"there is nothing there at all"*,
  which 720p can decide; *"the weave is too soft"* it cannot.
* **Whether R2-543's transparency is Transmission, Alpha or flipped normals.** A
  blend question. I did not open the blend.
* **Whether the car contacts the track at f2000.** I cropped to 5× to check for a
  float and the soft contact shadow under the car and the hard sun shadow beside it
  are consistent with contact *and* with a small float. I am not calling it either
  way from one frame at 720p.
* **Whether the shard sim is wrong** (R2-546) — one frame, deliberately
  under-claimed.
* **Audio.** Out of scope for this gate and no mix was examined.
* **Which blend the ladder is rendering.** R2-548 raises it; I did not answer it.

---

## Ranked, worst first

| # | entry | beat | why it ranks here |
|---:|---|---|---|
| 1 | **R2-541** | — | the pass is 26 % done and was gated as complete; 24.6 h of farm time still to run |
| 2 | **R2-542** | 2–6 | 73 % of the film has never been rendered; 2 instants in 2,186 frames |
| 3 | **R2-543** | 1 | the hero object is transparent in every frame of the only rendered beat |
| 4 | **R2-544** | 1 | no carbon weave, no decals, no tread — the beat's stated purpose is macro presentation |
| 5 | **R2-545** | 1 | four clusters' mandated readable moments are grey fields, and no metric catches them |
| 6 | **R2-550** | 5 | tilt-shift DOF + no racing line: the lap reads as a model |
| 7 | **R2-547** | 3/4 | blank white billboard placeholder in the only look at the world dressing |
| 8 | **R2-546** | 3 | the money moment's one frame shows flat panes and no dust |
| 9 | **R2-548** | 1 | empty cockpit in beat 1's payoff frame |
| 10 | **R2-549** | 1/3 | known items confirmed; doubling found on two *other* panels |
| 11 | **R2-551** | — | the explicit statement of non-assessment |

## Where this contradicts the framing I was given

* The pass **has not completed** (R2-541). The coverage gap is not a sampling
  design; the frames do not exist yet.
* The **nine dense blocks contain zero frames** (R2-541), not nine blocks of stills.
* The gap is **wider than stated** — beats 2, 4 and 6 have *nothing*, not thin
  coverage, and beat 1 stops 11 frames short of its own end (R2-542).
* The doubled text is on the **showroom facade sign and the pit board**; the track
  gantry, the panel named in the brief, shows no legible text in the one frame that
  contains it (R2-549).
* Beat 1 was implied to be the well-covered, therefore assessable beat. It is the
  only assessable beat and it is **the worst-looking one**: R2-543, R2-544, R2-545
  and R2-548 all live there, and three of the four are material or content defects
  that no amount of additional camera work fixes.
