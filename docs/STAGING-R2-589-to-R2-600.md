# STAGING — R2-589 onward

Continues `docs/STAGING-R2-581-to-R2-600.md`, which ends at R2-588. Nothing here
is merged into `docs/DEFECT-LOG-R2.md` by me.

**Scope of this pass.** One thing only: R2-588's pixel finding at f2110 said
variant B's peak is too aggressive, so B is retuned and re-gated. The candidate
stays a candidate — `docs/beat_sheet.json` carries other agents' live sheets and
this must not race them.

**Artefacts.** Candidate:
`render/film14_path_R2581B_ramp_RETUNED_CANDIDATE.json` (untracked; `render/*` is
gitignored). Pixels: `docs/peep/r2581/retune/`. Tools: `tools/r2581_cropview.py`
(new) and one gap closed in `tools/r2581_lensfix.py`.

**One thing came back that was not being looked for:** the peak frame renders
with no car in it at all. See R2-594 — it is occlusion, it belongs to another
agent's defect, and it is not caused by the lens.

---

## R2-589 — the instrument for a framing decision, and the control it has to fail

R2-588 rendered four matched pairs for $0.05 and found the thing no number
showed: at f2110 the biggest zoom "leaves a bare strip of asphalt — the wide had
more in it." **Choosing how far to pull the peak back is a question about what
is inside the frame, and only a picture answers it.** Rendering a ladder of
candidate focals would be six or eight more GPU frames per trial.

`tools/r2581_cropview.py`. For a fixed camera a lens `z` times longer is
*exactly* the centre `1/z` of the same render — the same identity R2-586 used to
render the `after` frames with `--zoom Z --border 0.5±0.5/Z`, read backwards. So
the **framing** of any candidate focal can be previewed by cropping the `before`
frame that is already on disk, at no cost.

**What it is not.** The crop does not reproduce **resolution**: a real render at
`z` puts `z` times more samples on the car. The preview is therefore pessimistic
about how well the subject *reads* and says nothing about detail. It answers
"what is in the frame" and nothing else, and the frame that decides the retune is
still rendered for real in R2-592.

**The control, in both directions.** R2-588 proved the emulation one way round —
`after` downscaled correlates 0.98–1.00 with its own `before` and 0.10–0.21 with
a different frame's. `--selftest` re-derives that through *this* code path, so an
off-by-one origin, a wrong aspect or a silent no-op cannot pass:

```
  PASS  f2050 z=1.9726  crop(before) vs its OWN after +0.9916   vs f2170's after +0.0941
  PASS  f2110 z=2.0839  crop(before) vs its OWN after +0.9889   vs f2170's after -0.0680
  PASS  f2170 z=1.7106  crop(before) vs its OWN after +0.9944   vs f2050's after +0.0971
  PASS  f2200 z=1.6781  crop(before) vs its OWN after +0.9970   vs f2170's after +0.1433
  PASS  negative/no-op  the UNCROPPED before correlates +0.1665 with the after;
        a cropper that silently did nothing would have to score < 0.90 and it does
SELFTEST PASS
```

The no-op line is the one that matters. Roughly a third of this project's
findings have been broken instruments; a cropper that returned its input would
have scored 0.99 on the first four rows if the comparison had been made the lazy
way, and it scores 0.17 here.

---

## R2-590 — where f2110's context actually dies: between 1.55x and 1.65x

The ladder, off `docs/peep/r2581/r2581_before_2110.png`, previews in
`tmp/r2581_retune/`:

| zoom | what is in the frame |
|---|---|
| 1.00x (as shipped) | the road running away, the barrier wall diagonal, the far **esses**, a marshal post, the tree line, a distant building. A genuinely good wide. |
| 1.35x | all of it still there, tighter. |
| **1.50x** | the road's exit sweep, the full barrier diagonal, the first far loop and the marshal post at the top edge. **Still a shot of a circuit.** |
| 1.55x | the far loop is clipped by the top edge; it reads, barely. **The boundary.** |
| 1.60x | the far track is a sliver at the very top; the S is gone. |
| 1.65x | barrier wall reduced to a corner; road, two verges. |
| 1.94x (variant B) | asphalt and two grass verges. A sliver of barrier top-left. |
| 2.08x (variant A, rendered) | asphalt and two grass verges. R2-588's finding, confirmed. |

**The criterion, stated so it can be disagreed with.** The thing worth keeping at
f2110 is the *far track the car is driving toward* — the esses at the top of
frame. It is what makes a head-on approach a shot of a place rather than a shot
of a lane, and it is the only element in the frame that gives the ten seconds
anywhere to go. It survives to 1.55x and is gone by 1.65x.

**B at f2110 is 1.94x, only 7 % below the 2.08x that was rendered.** The pixel
objection R2-588 raised against A therefore lands on B essentially unchanged —
this is not a defect B already avoided.

**So the cap is z ≤ 1.50 at f2110**, taken with margin rather than at the 1.55
boundary, and the price is a lower headline median. That is the trade R2-588
asked for.

---

## R2-591 — variant B, retuned: `--ramp 0.035 0.065`, peak 185.1 mm → 142.5 mm

`tools/r2581_lensfix.py --ramp 0.035 0.065 --out
render/film14_path_R2581B_ramp_RETUNED_CANDIDATE.json`. Same tool, same support
f1997–f2244, same guarantees. The ramp's *shape* is preserved — B ran
4.5 %→8.5 %, a 1.89x demand growth; the retune runs 3.5 %→6.5 %, 1.86x — so this
is B pulled back, not a different design.

```
     f   lens0   lens1     x    size0    size1
  2010    65.8    66.1  1.00   10.75%   10.80%
  2030    68.6    75.6  1.10    3.79%    4.17%
  2050    70.0    87.7  1.25    3.75%    4.70%
  2070    71.4    98.7  1.38    3.82%    5.28%
  2090    73.7   108.3  1.47    3.02%    4.44%
  2110    74.9   112.2  1.50    3.26%    4.87%   <- the frame the cap was set on
  2130    76.6   113.8  1.49    4.69%    6.97%
  2150    79.4   118.7  1.50    5.42%    8.11%
  2170    81.0   127.2  1.57    4.39%    6.90%
  2190    84.8   142.1  1.68    4.91%    8.23%   <- the peak
  2210    85.0   126.8  1.49    4.25%    6.33%
  2230    81.6    85.2  1.04    5.70%    5.96%
  2250    64.6    64.6  1.00    9.09%    9.09%
```

**The four variants side by side, over f2012–f2256 (245 frames, 10.21 s).**
`build` is the median of the last third over the median of the first third —
the number that says whether the passage goes anywhere:

```
variant               median%    min%    p10%  first3rd  last3rd  build  <4.41%  peakmm
shipping                 4.41    2.96    3.18      3.94     4.91   1.25x     123    85.0
A floor 6.46             7.58    4.18    6.15      7.32     7.40   1.01x       3   158.1
B ramp 4.5->8.5          7.30    4.74    5.62      6.19     8.68   1.40x       0   185.1
B retuned 3.5->6.5       6.11    3.95    4.43      4.95     7.16   1.44x      20   142.5
```

**The headline, in one line each:**

* **median 6.11 %** (shipping 4.41 %, B 7.30 %)
* **minimum 3.95 %**, at f2044 (shipping 2.96 %, B 4.74 %)
* **peak focal 142.5 mm**, down from B's 185.1 mm

**What the retune costs, stated.** The minimum is now 3.95 % rather than B's
4.74 %, and 20 frames of the 245 fall back below the shipping median — but they
are four short ripples, f2029–2032, f2041–2047, f2093–2098 and f2218–2220, the
longest 7 frames (0.29 s). B's headline claim of "no frame under 4.5 %" does not
survive the retune; the claim that the passage *builds* does, and slightly better
than B's own (1.44x against 1.40x), because the pull-back takes more out of the
front of the ramp than the back.

**142.5 mm is still 1.19x beat 5's authored maximum elsewhere** (120.0 mm at
t=98.6, the long-lens follow into T12). B's 185.1 mm was 1.54x. The retune brings
the passage close to the film's existing lens vocabulary instead of well outside
it. Worst 4K motion smear over the 246 touched frames falls 143 px → **109 px**,
against R2-424's 200 px flag and the film's own untouched 424 px at f2634.

**The other three rendered frames, checked at the retuned zooms** rather than
assumed (R2-589's previewer, same caveat about resolution):

* **f2050 at 1.25x** — kerbs, sand trap, verge and both track edges in frame.
  Much less gain than B's 1.60x, and this is where the retune costs most.
* **f2170 at 1.57x** — corner, kerb line, barrier wall, tree line, car on the
  apex. Wider than the 1.71x R2-588 called "the best frame of the eight", so it
  is safe by construction.
* **f2200 at 1.65x** — the `TELCOM` grandstand behind the car, a sliver of one
  bridge pylon at the left edge. Within 2 % of the 1.678x that was rendered, so
  R2-588's reading of that frame carries over unchanged.

**The alternative that was NOT built.** f2110 is starved of content while f2170
and f2200 have a barrier wall and a grandstand to spare, so a content-aware
per-frame target would zoom further where the frame can afford it. That means
abandoning one smooth curve for a curve driven by what is in each frame, which is
new machinery, a new failure mode, and a C1 argument that would have to be made
again. The whole ramp is scaled instead. Recorded so it is not re-derived and
thought overlooked.

---

## R2-592 — the gates, re-run on the retuned curve, and one gap closed

**A gap in the previous pass.** `--selftest` called `design(..., 0.0646)` with the
target hardcoded, so it gated variant A's curve no matter which candidate was
being shipped. It now takes the target from the command line, so **the curve
being gated is the curve being written.** That is the only change to
`tools/r2581_lensfix.py`; the assertions themselves are untouched.

```
  gating the curve for target ramp 3.50 -> 6.50 %
  PASS  compact support   |m-1| outside f1997..f2244 is 0.00e+00
  PASS  C1 lens           candidate |dlens| 3.178 mm/f, |d2lens| 0.842 mm/f2;
                          the SHIPPING film's own worst is 3.178 and 0.842
  PASS  position/rotation untouched
  PASS  negative/no-demand  m = 1 everywhere when the target is already met (0.00e+00)
  PASS  smear ceiling     worst 109 px over 246 touched frames; 0 cross 200 px
SELFTEST PASS
```

The C1 line is worth reading twice: the candidate's roughest frame **is** the
shipping film's roughest frame, the f2250–f2257 doppler zoom, which this change
does not touch. The retuned curve adds nothing rougher than what already ships,
and the threshold is still the film's own number rather than an invented one.

**The gate still fails when it should.** `--inject step|leak|smear` on the
retuned target:

```
                       clean    inject=step   inject=leak   inject=smear
compact support         PASS       FAIL          FAIL          PASS
C1 lens                 PASS       FAIL          FAIL          FAIL
position/rotation       PASS       PASS          PASS          PASS
negative/no-demand      PASS       PASS          PASS          PASS
smear ceiling           PASS       FAIL          PASS          FAIL
```

**The one-shot law, with the R2-103 self-null printed first so the floor is
visible before the verdict:**

```
SELF-NULL  film14_path.json vs itself
   raw stored q  (the R2-103 trap)   dq 0.203165 deg      <- the floor
   re-normalised q                   dq 0.000003 deg

A=film14_path.json  B=film14_path_R2581B_ramp_RETUNED_CANDIDATE.json
   beat 1        f1-792      worst dp 0.0000 m   dq 0.000 deg   dlens 0 mm
     PROTECTED   f648-792    worst dp 0.0000 m   dq 0.000 deg   dlens 0 mm
   beats 2-6     f793-2978   worst dp 0.0000 m   dq 0.000 deg   dlens 57.5 mm
```

**Zero position and zero rotation change across all 2,978 frames.** The only
channel that moves is `lens`, worst delta 57.5 mm against B's 100.1 mm and A's
83.8 mm, and it moves only inside f1997–f2244.

**Still not delivered, on purpose.** The candidate is a per-frame path. It is
**not** folded into `docs/beat_sheet.json` — other agents have live candidate
sheets in that file, and two agents writing one sheet is how a one-shot film
acquires a seam. R2-586's three unpaid costs stand unchanged: the f-stop is
untouched so depth of field must be re-checked against the blend's animated DOF
at merge; the 22 deg aim bound in the sheet is stale at any of these focals
(measured margin is max 0.187 deg off axis, so nothing leaves frame, but the
bound's number would need re-deriving); and a longer lens is still a narrower
view, which is a taste call that a merge is choosing, not inheriting.

## R2-593 — the confirming render, and what it can still overturn

**What the crop cannot answer.** R2-589's previewer is exact on framing and
silent on resolution, so it settles "does f2110 keep its context" and cannot
settle "does the car still read at 1.50x". At 1.50x the car is **4.87 % of frame
width — 62 px at 1280, ~187 px in the 4K delivery** — against 42 px as shipped
and the 85 px at which R2-588 could read endplates, halo and front-wing elements.
The retune is therefore expected to land between "a blue smudge with two dark
blobs for tyres" and "a car that reads", and that is the one claim in this pass
which is asserted from a projection rather than seen.

**Two frames, off the loaded `film14_breach_r6.blend`, 1280x720 / 64 samples /
adaptive 0.01, camera `ONER`, the scene's own AgX and −3.628, prio 89:**

```
ba8ed022c396   f2110  --zoom 1.4969  --border 0.165983 0.834017 (both axes)   the cap frame
b67b883a270f   f2190  --zoom 1.6752  --border 0.201530 0.798470 (both axes)   the new peak, never rendered
```

**Cost: ~$0.013** — about 110 s of GPU at $0.4203/hr, against the eight frames
that cost $0.05 in R2-588. Both delivered; `tmp/r2581_retune/retune_*.png`.

**f2110 at 1.4969x — the retune does what it was retuned for.**

* **The framing.** The far esses the car is driving toward are in frame at the
  top, with the barrier-wall diagonal, the marshal post and the run-off. It is
  still a shot of a circuit. Against variant A's 2.08x — asphalt and two grass
  verges — this is the whole point of the pass.
* **The previewer predicted the render.** The R2-589 crop at z=1.50 correlates
  **+0.9939** with the delivered frame and **−0.0360** with a different frame's.
  The cheap instrument was right about the framing, which is all it claimed.
* **The ruler agrees with the projection, in the direction it must.** Measured
  off the delivered pixels the car spans x 607–665, **59 px = 4.61 %** of frame
  width against the projected **4.87 %** — the box overstates by 5.3 %, inside
  the 0–9 % band R2-584 established over five frames.
* **The subject reads, less well than at 2.08x, better than as shipped.** At 6x
  (`tmp/r2581_retune/zoom_retune_2110.png` against R2-588's
  `zoom_before_2110.png`) the front wing is a distinct blade with endplates, the
  rear wing carries a legible sponsor strip, the four tyres separate cleanly and
  the livery pattern is visible on nose and sidepods. R2-588's `before` at the
  same magnification is a compact blob with the rear wing merged into the
  bodywork. **That is the price of the retune, paid and visible: 59 px where A
  bought 85 px, against 42 px as shipped.**

**Verdict: the retune holds.** f2110 keeps its context and the car still reads.

---

## R2-594 — the peak frame came back with NO CAR IN IT, and the instrument said 8.23 %

`b67b883a270f`, f2190 at 1.6752x — the peak of the retuned ramp — contains a
concrete parapet, a wall with posts and green fencing above it, and a kerb and
gravel trap below. **There is no car anywhere in the frame.** The projection says
the car is 8.23 % of frame width there — about 105 px, impossible to miss.

**It is occlusion, and the instrument declares itself blind to it.**
`tools/lap_shotscale.py`'s own LIMITS section says so in one line: *"Occlusion is
not modelled: a car behind a barrier still measures full size."* At f2190 the car
projects to screen **x 0.500, y 0.493** — dead centre, 183.3 m away, camera 13.7 m
up — and the centre of the delivered frame is the parapet.

**It is the same structure R2-584 already measured, ten frames later.** R2-584 on
f2180: *"the bottom-right 45 % of the frame is filled by a motion-smeared
grandstand structure sweeping through the foreground, its upper edge passing
within a few pixels of the car."* By f2190 that edge has swept over it. R2-588
saw the far side of the same pass at f2200, where the car is visible again as a
62 px chip between two bridge pylons. So the blocked window sits between two
frames that are known-visible, and it is narrow.

**What this does and does not mean for the fix.**

* **The candidate did not cause it and cannot cure it.** Whether a sightline is
  blocked is a property of the ray from camera to car; **focal length does not
  enter it.** The car is equally hidden at the authored 84.8 mm. What the longer
  lens does is make the occluder fill more of the frame.
* **It does mean the fix's back-half numbers are overstated on some frames.**
  The demand curve is driven by measured size, and on the blocked frames the
  measured size is fiction — the delivered subject is 0 %. The ramp's peak is
  therefore parked, by coincidence, on frames where nothing is gained.
* **How many frames are blocked is not established here**, and finding out means
  a ray-cast against the assembled world. The local box has 0 GB of 11 GB free
  and 38 GB of swap in use, so a 5 GB blend cannot be opened here; the honest
  next step is `rq exec` on the rented box, and it belongs with the placement
  defect rather than with the lens.

**Handed on, not chased.** The near-field architecture at f2180/f2190/f2200 is
another agent's defect (R2-588 says so explicitly). This entry adds one fact to
it that was not previously known: **at f2190 the architecture does not merely
compete with the subject, it hides it completely.** Whoever fixes the placement
should re-run `tools/r2581_lensfix.py` afterwards, because the demand curve that
sets this candidate's peak is partly driven by frames whose subject is not
actually on screen.

**Out of scope and left alone:** the near-field architecture at f2180
(grandstand) and f2200 (two bridge pylons). It is a separate defect, it belongs
to another agent, and the retune's shorter lens improves it less than B's did.
