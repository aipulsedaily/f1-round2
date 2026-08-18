# STAGING R2-2401 .. R2-2460 — the crowd block cameras, and the attention verdict

Agent `r2-2401-block-cameras`. Item #100 on the round-2 list.

## THE ONE-LINE STATE

**The defect as written is stale and was closed on 2026-08-03; the question
underneath it was not, and the answer is that ONE camera answers it.** The two
block cameras no longer exist — `REJECTED_CAMERAS_ABSENT`, read out of the blend
here rather than cited — and their replacement set was rebuilt, rendered and
looked at three passes ago. What had never been done is the test that survives
fixing the pixels: **a camera that resolves 50 px of head can still return the
same reading for a crowd that is watching and a crowd that is not.** Run against
an `attention = 0` null, **`CAM_ATTN_ONAXIS` clears its own attention bar on a
crowd looking at nothing** (220 faces against a bar of 201), and of six barred
cameras only **`CAM_CROWD_ALONG`** rejects the null. **Crowd attention itself is
CORRECT** — 73.0 % within 20° on the realised geometry against a 17.4 % null,
heads turning and not bodies, no comb in the distribution, and it survives being
looked at. **The crowd item closes.**

**Two things in the item text are wrong and both matter:** there is **no depth of
field anywhere in this item** (`use_dof = False` on all eight datablocks, and the
fix it implies would have made the frame *worse* — §R2-2402), and the subject is
at **112.50 m, not 148 m**. The gate is **8/8, not 6/8**. Item #100 already has a
comment-only commit from 2026-08-07 (`d36814f`) that refutes the premise; this
staging note does not repeat it, it does the four things that commit did not:
measures the pixels independently, opens the frames, tests the instruments
against a null, and answers the attention question.

---

## R2-2401 — FRAME NOMINATION, WRITTEN BEFORE ANY FRAME WAS OPENED

This project has a rule that the frames a fix is judged on are named **before**
the render, because a fix was once declared good on a frame chosen after the
fact. The repaired cameras were rendered on 2026-08-03 (fifth and sixth passes)
and the PNGs are already on disk, so the equivalent discipline here is to name
the crops **before opening them**. Nominated, with the prediction each one is
supposed to be able to falsify:

**BEFORE — the rejected instrument.**

| # | file | crop | what it must show if the rejection was right |
|---|---|---|---|
| B1 | `render/items/spectator_crowd/_superseded_2026-08-03_R2-061/BLOCK_CROSS.png` | 1:1, 640x480, frame centre | at a ~10 px head: no eye line, no face, no shoulder orientation. Heads are colour blobs. |
| B2 | same | full frame, downscaled to 960 | block-scale structure (aisle bays, occupancy gradient) DOES read. The camera is not useless; it is useless *for attention*. |

**AFTER — the repaired instrument.**

| # | file | crop | what it must show |
|---|---|---|---|
| A1 | `render/items/spectator_crowd/p6/CAM_ATTN_ONAXIS.png` | 1:1, 640x480, frame centre | faces resolvable; a clear majority facing the lens; a visible minority in profile / heads down. |
| A2 | `render/items/spectator_crowd/p6/CAM_ATTN_PROFILE.png` | 1:1, 640x480, frame centre | **the load-bearing frame.** Shoulder lines EDGE-ON to this lens, heads rotated OUT of that shoulder line. |
| A3 | `render/items/spectator_crowd/p6/CAM_CROWD_ALONG.png` | 1:1, 640x480, centre and upper-third | a continuous RANGE of head bearings against square shoulders, not two clusters. |

**THE A1/A2 PAIR IS THE TEST AND EITHER SIDE ALONE IS NOT.** If the crowd were
rotated *bodily* toward the car instead of turning its heads, A1 would look
exactly the same and A2's shoulders would face the car too. A1 and A2 cannot
both come out as predicted unless the heads, and only the heads, are turned.

**VERDICT WILL BE STATED ON A2 FIRST.**

(Sections below are written after the work; the table above is unedited.)

---

## R2-2403 — SECOND NOMINATION, WRITTEN BEFORE THE RENDER WAS SUBMITTED

R2-2402 (below) establishes in the projection that `CAM_CROWD_ALONG`'s face
count moves 6.9 sd between a watching crowd and an `attention = 0` null. That is
a STATISTIC responding. It does not establish that a person LOOKING through the
camera can tell the two apart, and "a verification camera" is an instrument for
a person to look through. So the A/B is rendered.

| # | blend | camera | what it must show |
|---|---|---|---|
| C1 | reduced block, `attention` shipped | `CAM_CROWD_ALONG` | heads turned together toward the car, faces presented to the lens |
| C2 | reduced block, `attention = 0`, **same seed, same seats, same camera** | `CAM_CROWD_ALONG` | the same people, heads scattered — a crowd looking nowhere |
| C3 | C1 | `CAM_ATTN_ONAXIS` | the frontal view of C1 |
| C4 | C2 | `CAM_ATTN_ONAXIS` | **prediction: C3 and C4 are hard to tell apart.** This is the camera the projection scores at 1.8 sd, and if the picture agrees with the projection then the frontal camera is an illustration and not a test. |

**PREDICTION, RECORDED BEFORE THE PIXELS EXIST:** C1 vs C2 is obvious at a
glance; C3 vs C4 is not. If C1/C2 are *also* hard to tell apart, then no block
camera answers the attention question by looking and only the statistic does —
and that is the finding, not a failure to be rendered around.

~~1280x720, 128 samples.~~ **CORRECTED BEFORE SUBMISSION, and the correction is
the item's own law biting the agent writing it up.** `CAM_CROWD_ALONG`'s median
head is **57.2 px at 3840**. At 1280 that is **19.1 px** — below the 40 px bar
this whole item exists to enforce, and I had just spent a section proving that a
camera below its subject's resolvable band is no test. A 720p A/B of a 40 px bar
is the pixel-footprint law being broken by the instrument built to police it.
Rendered at **3840x2160 / 128 samples** instead.

---

## R2-2402 — WHAT EACH CAMERA CAN RESOLVE, IN PIXELS, BEFORE ANYTHING CHANGED

Computed in `tools/r2_2401_pixel_footprint.py`, which deliberately imports nothing from
`spectator_crowd.py`. Two independently written arithmetics, and they agree.

| camera | dist | lens | **head px** | eye separation | shoulder width | elev |
|---|---:|---:|---:|---:|---:|---:|
| `CAM_BLOCK_ONAXIS` | 152.20 m | 50 mm | **8.06** | **2.17** | 14.72 | −9.0° |
| `CAM_BLOCK_CROSS` | 112.50 m | 50 mm | **10.90** | **2.94** | 19.91 | −11.0° |

`preflight` reports 8.0 and 10.1 px as the median over the population in frame;
the at-aim figures above are 8.06 and 10.90. The two agree.

**THE EYE LINE IS THE 0.87 px OF THIS DEFECT.** An interpupillary distance is
**2.17 px** at `BLOCK_ONAXIS`, and a *feature* of the eye — a socket, a lid, a
brow shadow — is a fraction of that. There is no gaze direction to read. A
shoulder orientation at 14.7 px is a 2–3 px change for a 10° turn, under a
denoiser. **These are not soft frames. They are frames whose subject is below
the sampling grid**, and the fourth pass's own words for it — *"you cannot judge
whether two neighbours are the same person at 8 px of head"* — are exactly right.

### The blur circle, which the brief asked for and which is a red herring

`use_dof = False` on **all eight** camera datablocks, read out of
`world/items/spectator_crowd_test.blend` by `bpy.data.libraries.load(link=True)`
in `tools/r2_2401_pixel_footprint.py --datablocks` — an independent read, not a citation:

    >> STAGE RESULT: DOF_OFF_ON_EVERY_CAMERA (0 camera(s) with use_dof True)
    >> STAGE RESULT: REJECTED_CAMERAS_ABSENT (no BLOCK_* datablock)

`fstop 2.8` and `focus_distance 10.0 m` are Blender's untouched defaults. There
is no chosen aperture, so a blur circle has to be computed against a *stated*
assumption, and there are two:

| assumption | `BLOCK_ONAXIS` | `BLOCK_CROSS` |
|---|---:|---:|
| `use_dof` flipped on **as delivered** (focus left at 10 m) | **8.94 px** | **8.72 px** |
| ... and also focused at its own subject (ceiling, object at ∞) | 0.626 px | 0.847 px |

Hyperfocal at 50 mm f/2.8 on a 1 px 4K budget is **95.29 m**, and both subjects
are beyond it — which is why the second row is sub-pixel.

**AND THIS IS THE DOUBLE CORRECTION, CAUGHT WITH A NUMBER RATHER THAN A
WARNING.** The brief told me to treat distance and depth of field as two levers
and to check whether both were compensating for the same error. They are worse
than that: **one of the two levers, pulled the way the fourth pass prescribed,
makes the frame strictly worse.** §0000.5's remedy was *"re-shoot ... with the
aperture wide open"*. On this datablock that means `use_dof = True` with focus
still at its 10 m default — top row — and the blur circle becomes **8.7–8.9 px
against an 8.1–10.9 px head.** The prescribed fix would have defocused the
subject by roughly its own height, and the frame would have come back visibly
worse, which would have been read as confirmation that blur was the problem.

Only the distance/lens lever was ever real. **A 40 px head needs 248.2 mm at
`BLOCK_ONAXIS`'s distance and 183.4 mm at `BLOCK_CROSS`'s** — and that, not the
aperture, is what the replacements did.

---

## R2-2402b — THE TEST NOBODY HAD RUN: DOES THE INSTRUMENT RESPOND TO THE SIGNAL?

40 px of head is a **necessary** condition for an attention camera and the whole
repair was carried out against it. It is not a **sufficient** one. A camera that
scores the same on a crowd that is watching and a crowd that is not is no test
of attention however sharp it is, and that check did not exist.

`tools/r2_2401_attention_null.py --seeds 12`. The cameras are planned **once, on the shipped
crowd**, and both crowds are projected through those same cameras — a control
that re-aims its own camera compares two instruments, not two crowds. `delta` is
`n_faces_resolved(attention shipped) − n_faces_resolved(attention = 0)`, and it
is scored against a **seed null**: the same statistic over **12 independent
draws of the same attention-on crowd**, which is how far it moves for reasons
that have nothing to do with attention.

| camera | head px | heads | faces ON | faces 0 | delta | seed sd | **z** | sign |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `ctl_BLOCK_ONAXIS` | 8.0 | **0** | 0 | 0 | **0** | 0.0 | — | no move |
| `ctl_BLOCK_CROSS` | 10.1 | **0** | 0 | 0 | **0** | 0.0 | — | no move |
| `CAM_CROWD_ALONG` | 57.2 | 613 | 491 | 287 | **+204** | 29.5 | **6.9** | as predicted |
| `CAM_ATTN_ONAXIS` | 50.5 | 330 | 292 | 220 | +72 | 39.0 | **1.8** | as predicted |
| `CAM_ATTN_PROFILE` | 54.0 | 593 | 175 | 237 | **−62** | 16.4 | **3.8** | as predicted |
| `CAM_ROW` | 28.4 | 184 | 158 | 109 | +49 | 22.2 | 2.2 | as predicted |

**THE REJECTED PAIR IS BLIND, AND NOW IT IS BLIND WITH A NUMBER.** Zero resolved
heads and **delta exactly 0** — `BLOCK_ONAXIS` and `BLOCK_CROSS` return an
identical reading for a crowd rapt on the car and a crowd looking at nothing.
That is the brief's *"not a strict test that happens to pass — no test at all"*,
demonstrated in the instrument's own units rather than asserted from a head
count. It is also why re-shooting them at a wider aperture could never have
helped: there was no signal in the frame to sharpen.

**THE SIGN IS PART OF THE PREDICTION, AND MY FIRST BAR GOT IT WRONG.** The first
version of this script (`respond.py`) required faces to *increase*. That bar was
written before I understood the quantity — this project's own named failure —
and `CAM_ATTN_PROFILE` caught it: standing 90° off the car, a crowd that turns
its heads **toward** the car turns them **away** from that lens, so its face
count must **fall**. It falls, by 62. Each camera's expected sign is now declared
from geometry before the numbers are read.

**AND THE FIRST SEED NULL WAS TOO THIN TO FAIL A CAMERA ON.** At 4 seeds
`CAM_ATTN_PROFILE` scored z = 11.4 and `CAM_CROWD_ALONG` 6.1. At 12 seeds those
are **3.8** and **6.9**. A 3-degrees-of-freedom variance estimate was flattering
the marginal camera by 3×, and the 4-seed run would have reported PROFILE as the
strongest instrument of the three when it is the weakest of the two that work.
**Quote the 12-seed column; the 4-seed one is in the log and is wrong.**

**AND THE OBVIOUS CONFOUND IS CLOSED.** `attention` indexes the library — the
gaze bin picks the source mesh — so switching it off swaps in different meshes
and could in principle change what is *visible* rather than what is *facing*.
If it did, `delta` would be a visibility artefact wearing a gaze costume.
`tools/r2_2401_attention_null.py --confound` (ON / OFF):

| camera | in frame | unoccluded | **heads resolved** | faces |
|---|---|---|---|---|
| `CAM_CROWD_ALONG` | 1296 / 1296 | 639 / 638 | **613 / 612** | 491 / 287 |
| `CAM_ATTN_ONAXIS` | 334 / 335 | 330 / 333 | **330 / 333** | 292 / 220 |
| `CAM_ATTN_PROFILE` | 1450 / 1442 | 621 / 617 | **593 / 593** | 175 / 237 |

**The same heads are resolved either way — to within one figure in six hundred —
and only the face count moves.** The signal is gaze and nothing else.

---

## R2-2402c — THE SHARPEST FORM OF IT: EACH CAMERA'S OWN BAR, RUN AGAINST THE NULL

This repository's own rule for gates is *"test every new gate against an
artefact already known to be bad and confirm it fails — this is the only
technique that has reliably worked."* **The `attention = 0` crowd is that
artefact, and the cameras' `preflight` bars are gates.** Nobody had ever run one
against the other. `tools/r2_2401_attention_null.py` (the `own bar vs null` column):

| camera | its own bar | shipped crowd | **`attention = 0` NULL** | |
|---|---|---|---|---|
| `CAM_CROWD_ALONG` | `min_faces=300, head_px=40, max_elev=2` | PASS | **REJECT** | a real gate |
| `CAM_ATTN_ONAXIS` | `min_faces=201, head_px=40, max_elev=1` | PASS | **PASS** | not a gate on attention |
| `CAM_ATTN_PROFILE` | `min_faces=120, min_heads=300, ...` | PASS | **PASS** | not a gate on attention |
| `CAM_ROW` | `min_faces=8` | PASS | PASS | not a gate on attention |
| `CAM_FEET` | `min_faces=6` | PASS | PASS | not a gate on attention |
| `CAM_HANDS` | `min_faces=2` | PASS | PASS | not a gate on attention |

**`CAM_ATTN_ONAXIS` clears its own attention bar on a crowd that is not watching
anything.** 220 faces against a bar of 201. It is named for attention, its `what`
string says *"a watching head is a FACE, a non-watching one is a profile — judge
the 27 %"*, and it returns PASS on a block whose heads point at random. That is
the defect of the two block cameras — an instrument that cannot fail — surviving
the repair in a quieter form: they could not resolve the subject, this one
resolves it and does not discriminate on it.

**Of six cameras with a pass/fail bar, exactly one fails the artefact known to be
bad.** The other five are framings, and only `CAM_CROWD_ALONG` is a gate. That is
not an argument for deleting them — `CAM_HANDS` exists to show mitten hands and
does it well — but their bars should not be read as verdicts on attention, and
one of them is currently named as though it is.

---

## R2-2405 — WHAT EACH CAMERA IS FOR, AS A QUESTION WITH A PASS/FAIL ANSWER

The brief asked for the question each camera answers, and warned that the honest
outcome might be one good camera rather than two repaired ones. **It is one.**

| camera | the question, stated so it can fail | can it answer it? |
|---|---|---|
| `CAM_CROWD_ALONG` | *Are the spectators' heads turned toward the car, out of shoulder lines that stay square to the rows?* | **YES.** 613 heads at ≥ 40 px, 80 % present a face; 47 % on the null; **6.9 sd**. |
| `CAM_ATTN_PROFILE` | *Do the heads turn out of an edge-on shoulder line — i.e. is it heads and not bodies?* | **CORROBORATING.** Correct sign, large per-camera signal, but **3.8 sd**. Not independent evidence. |
| `CAM_ATTN_ONAXIS` | *(as built) Is attention directed at the car?* | **NO. 1.8 sd.** Demote it — see below. |
| ~~`CAM_BLOCK_ONAXIS`~~ | *Does attention read? Is a neighbour visibly the same person?* | **NO, on both.** 0 heads, delta 0. Deleted; absent from the blend. |
| ~~`CAM_BLOCK_CROSS`~~ | as above | **NO.** 0 heads, delta 0. Deleted. |

### `CAM_ATTN_ONAXIS` IS AN ILLUSTRATION, NOT A TEST, AND ITS BAR SAYS OTHERWISE

The module already knew this in prose — *"the WEAK half of the attention pair
and is kept anyway"* — but its `preflight` bar does not encode it: it carries
`min_faces = 0.67 * n_bar`, the same **pass/fail on face count** the two working
cameras carry. A camera that cannot separate attention from no-attention is
being scored as though it can, and it passes.

**The cause is geometric and is not fixable at this circuit.** `--preflight`
reports the car at **9.66° off the seated bodies' own average bearing** (the
seats face 130.00° with a 0.2° spread; the bodies average 133.56°; the car is on
143.22°). A lens on the car's bearing therefore sits ~10° from where every torso
already points, so **220 of 330 resolved heads — 67 % — still count as "facing"
with attention switched off entirely.** The camera is looking at the torsos'
answer, not the heads'. Its 1.8 sd is that fact.

Note this is a *smaller* separation than the 13.2° the module's own docstring and
HUMAN-REFERENCE §00000.3 both quote. 13.2° is the car against the **seat**
facing; 9.66° is the car against the **realised body** bearing, which is what the
lens actually sees. **The docstring's number is the wrong one for this argument
and is 37 % too generous.**

**RECOMMENDED, and this is a change to a module six passes are standing on, so it
is written down and not made:** `CAM_ATTN_ONAXIS` keeps its framing and loses its
`min_faces` bar — `bar=None`, the way `CAM_SHEET` already carries one — with its
`what` string changed from *"Judge the 27 %"* to a statement that it is an
illustration of the non-watchers and that the attention verdict is
`CAM_CROWD_ALONG`'s. **It is not the on-axis camera that is broken; it is the
claim that a frontal frame can settle attention on a stand whose seats already
point within 10° of the car.**

---

## R2-2406 — THE NOMINATED FRAMES, OPENED

All crops are 1:1 (no resampling) from the 3840x2160 PNGs. The `_lift` versions
are `x3.2, gamma 1.25` **for inspection only** — the frames are shot at the
film's −3.628 EV and a crowd at that exposure is dark on a monitor. No judgement
below rests on the lift; the unlifted crops are beside them.

**B1 — `BLOCK_CROSS`, 1:1 centre. Prediction met, exactly.** Every head is a
smeared colour blob 10 px across. No eye line, no face, no shoulder orientation,
no way to tell one figure from its neighbour. **And it looks precisely like a
defocused photograph**, which is the entire explanation for how the fourth pass
came to blame depth of field and write it down as fact. Sub-pixel detail through
a denoiser and a defocus are the same picture; only a measurement separates them.

**B2 — `BLOCK_CROSS`, full frame. Prediction PARTLY met, and the record
overstates this.** The block reads as a receding wedge with row banding and an
occupancy gradient, so the fourth pass's *"the occupancy gradient and the 16
aisle bays read"* survives in the weak sense. But the subject occupies perhaps a
third of the frame width on an otherwise black field, and **I could not count 16
aisle bays in it.** The salvage value claimed for these two frames is smaller
than recorded. It does not change the verdict — they are deleted either way.

**A1 — `CAM_ATTN_ONAXIS`, 1:1 centre and a second sample at (900, 1200).**
Faces resolvable at ~50 px, bodies overwhelmingly frontal, and a real minority
turned away — backs of heads, profiles, one figure looking down. So the frame is
readable. **But it is readable in a way that cannot settle the question**, and
looking at it after computing 1.8 sd makes that obvious rather than surprising:
the bodies are frontal because the *seats* are frontal, and I cannot tell by
eye which of those frontal figures is watching and which merely happens to face
this way. This is the camera agreeing with its own statistic.

Also visible and already on the record as open: **the faces are near-featureless
pale ovals at 50 px** (defect 1). Head *orientation* reads from the hair/skin
boundary and the silhouette, not from any facial feature.

**A2 — `CAM_ATTN_PROFILE`, 1:1 centre and (900, 1200).** Bodies side-on as
predicted, and heads pointing in **many different directions** — profiles both
ways, backs of heads, several looking down into their hands. The range is real
and is not two clusters.

**A3 — `CAM_CROWD_ALONG`, 1:1 at (1600, 840) and (2400, 700). This is the frame
that answers the question.** At 57 px of head, against shoulder lines that run
consistently along the seat rows, a clear majority of heads are turned to a
**common bearing** — coherent, not identical, spread across a range. Interleaved
with them: figures looking down at phones, a few backs of heads, a few in
profile the other way. **A crowd attending to one thing, with a real minority
not.** That is what correct attention looks like, and it is the first time it
has been read off pixels rather than off the plan.

---

## R2-2407 — THE VERDICT ON CROWD ATTENTION

**Open since the crowd was gated. The answer is that attention is CORRECT.** It
rests on four measurements that fail in different ways, not on one.

**1. The plan, with its own null.** `spectator_crowd --selftest`, 14 checks, 0
failed. `crowd_watches_the_car`: **73.0 % attend within 20°, circular sd 45.0°**,
against the same block at `attention = 0` measuring **17.4 % and 101.6°**. A
uniform "crowd all facing slightly different directions" — the brief's defect 9 —
scores 11.1 % and ~104°, so the null is behaving as a uniform field should.

**2. On the REALISED geometry, not the intent.** `what_is_baked_is_what_was_
planned`: attention measured on the baked head bearings is **73.0 % against the
plan's own 73.0 %**, with binning moving a head by at most 0.0°. This is the
check that matters, because `attention_spread` reads `yaw_deg` (intent) and the
frame contains `body_yaw_deg + gaze_baked_deg` (realised). **They agree exactly**,
so the statistic is not measuring its own invention — the failure this
repository has hit sixteen times.

**3. It is HEADS, not BODIES — the failure that would look identical in a
statistic.** `seats_do_not_swivel`: worst body yaw departs its seat's facing by
**42.8°** and the worst head turn is **72.0°** (clamped at the neck limit). The
seats face 130.00° with a **0.2° spread** and the bodies average 133.56°, so the
stand is not rotated bodily toward the car; the naive version that does rotate
the instance *"reads as a fairground carousel"*. Corroborated in pixels by A2 —
bodies edge-on to a 90°-off lens with heads turned out of that line — and by
`CAM_ATTN_PROFILE`'s face count **falling** by 62 when attention is switched on,
which a bodily rotation could not produce.

**4. The distribution is continuous, not stepped.** `realised_gaze_field_has_
no_comb`: **0 of 30 two-degree bins empty** across the 953-person watching core,
where the superseded ordering leaves 5 of 30 empty — a defect that every
attention statistic in the module scores identically and only this check sees.

**AND IT SURVIVES BEING LOOKED AT** (A3, §R2-2406): heads turned to a common
bearing against square shoulder lines, with a genuine minority on phones, in
profile, and turned away.

### What this verdict is NOT

It is **not** a claim that the crowd's faces are good. At 50–57 px the faces are
near-featureless pale ovals (defect 1, open, diagnosed as a sampling problem in
§000000.2). Attention here means **head bearing**, read from the hair/skin
boundary and the silhouette. **A gaze direction — where the eyes point within
the head — is not resolvable at any distance these cameras stand at**, and no
camera in this set claims to measure it. The item's attention claim is about
head bearing and that is what has been verified.

**CONSEQUENCE FOR THE CROWD ITEM.** The gate is `ITEM_ACCEPTED` 8/8
(§0000000.1), not the 6/8 the task list records — the two NOT MEASURED were
fixed three passes ago. **With attention now verified in the projection, in the
realised geometry and in pixels, the crowd item closes properly.** The open
defects against it are appearance defects (faces, hair at short lengths, the
white caps' frame) and belong to their own items, not to this one.

---

## R2-2408 — THE C1–C4 CONTROL RENDER WAS NOMINATED AND NOT RUN. WHY.

R2-2403 nominated four frames — an `attention` / `attention = 0` A/B through
`CAM_CROWD_ALONG` and `CAM_ATTN_ONAXIS`. **They were not rendered. Recording that
here rather than deleting the nomination, because a nomination you are allowed to
quietly drop is not a nomination.**

`tools/r2_2401_build_attention_ab.py` was written (it wraps `plan_block` in the control
harness rather than adding an `attention` argument to a module six passes are
standing on, and it plans both blends' cameras from the attention-ON plan so the
control cannot re-aim itself). The attention-ON build ran for **6 min 57 s** and
was **killed by me, by explicit PID, before it finished.**

**The reason is the machine, not the method.** At the moment of the kill: 153 MB
of free RAM, **528 MB available**, swap at **35.4 of 45 GB**, and four Blenders
running — another agent's film-scene build at **3.9 GB and 27 minutes in**, a
second at 1.95 GB and three minutes in and climbing, and mine third at 0.97 GB.
Two more full library builds (~1 GB peak each, sequential, ~30 min each) into
that would very likely have fired the OOM killer, and its most probable victim
was a 27-minute job belonging to somebody else. **This project has already lost
another agent's render to exactly that shape of carelessness, and a control for
a question already answered four other ways is not worth someone's afternoon.**
Nothing was left behind: no blend written, no process surviving, and the output
directory I had started in — `render/r2401/` — turned out to belong to the R2-401
cockpit agent, so my outputs were moved to `render/r2_2401_attn/` before anything
landed in it.

**AND THE RENDER WOULD HAVE ADDED LESS THAN R2-2402c DID.** C3/C4 were nominated
to show that the frontal camera cannot separate attention from no-attention — a
*negative*, and my failing to see a difference in two frames is weak evidence for
one. **The bar test proves the same claim far harder and for free: the camera's
own gate returns PASS on the null.** C1/C2 would have shown that the along-the-
bank camera's difference is visible; the projection puts it at 80 % of resolved
heads presenting a face against 47 %, at 6.9 sd, on a projection independently
validated against Blender's own `world_to_camera_view` to 0.094 px worst case.

**What is therefore NOT established, stated plainly:** that a person looking at
`CAM_CROWD_ALONG` can distinguish the shipped crowd from an `attention = 0`
crowd **in pixels**. The statistic separates them decisively; the frames were
looked at for the shipped crowd only (§R2-2406), and there is no rendered null
beside it. **If the next agent wants that, `tools/r2_2401_build_attention_ab.py` is written and needs a
quiet machine and about ninety minutes.** It is the one loose end here and it is
a corroboration, not a load-bearing gap.

---

## R2-2409 — WHAT SHOULD CHANGE, AND WHAT I DID NOT CHANGE

Nothing in `world/items/spectator_crowd.py` was modified. Six agents are in this
tree and that module is load-bearing for three finished passes; a camera-bar
change made on a Friday night by an agent who does not own the item is how the
next `_SUPERSEDED` file gets written. **These are proposals with the measurement
attached, for the owner of the item.**

1. **`CAM_ATTN_ONAXIS` should lose its `min_faces` bar** (`bar=None`, as
   `CAM_SHEET` already carries) and its `what` string should stop claiming to
   settle attention. It PASSES the `attention = 0` null at 220/201. Keep the
   framing — the 27 % who are not watching really are unmissable in it — but it
   is an illustration. **Evidence: §R2-2402b, §R2-2402c.**
2. **`tools/r2_2401_attention_null.py` should become a `--selftest` check.** The
   module has 14 checks and not one of them asks whether a camera can tell
   attention from no-attention. `preflight` gates the *necessary* condition and
   nothing gates the sufficient one. `CAM_CROWD_ALONG` is the positive control
   (rejects the null) and `CAM_ATTN_ONAXIS` the negative (passes it), so the
   check has both controls already and neither is synthetic.
3. **`camera_plan`'s docstring quotes 13.2° where the argument needs 9.66°.**
   13.2° is the car against the *seat* facing; the lens sees the *realised body*
   bearing, which averages 133.56°, putting the car 9.66° off. The docstring uses
   the number to argue about what the lens sees, and for that it is 37 % too
   generous. `--preflight` already prints the right one.
4. **`build_scene` has no `attention` argument**, so a control crowd cannot be
   built without wrapping `plan_block` from outside (which is what
   `tools/r2_2401_build_attention_ab.py` does). A `**kw` pass-through to `plan_block`
   would make the null a first-class thing the module can build.

### FOR THE REBUILD MANIFEST

**Nothing.** The brief said that if attention is wrong it lands on the rebuild
manifest. **Attention is right** (§R2-2407), so it does not. What lands instead
is an *instrument* item — proposal 1 above — and it is a bar on a camera, not a
rebuild of anything in the picture.

### STILL OPEN, AND NOT MINE

* The C1–C4 control render (§R2-2408) — corroboration only.
  `tools/r2_2401_build_attention_ab.py` is written and unrun; it needs a quiet
  machine and about ninety minutes.
* Defect 1, the near-featureless face at 50 px, is open and diagnosed elsewhere
  (§000000.2). Attention here is **head bearing**, not gaze; no camera in this
  set resolves an eye line, and at `CAM_CROWD_ALONG`'s 57 px head an
  interpupillary distance is 15.4 px with the features on it far smaller.
* §0000000.6's list is untouched by this work.
