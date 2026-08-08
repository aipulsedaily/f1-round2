# STAGING R2-3061 .. R2-3120 — the road surface, near-field

Agent `r2-3061-asphalt`. Leases: `world/build_surface.py`,
`tools/r2_3061_*.py`, this file.

---

## R2-3061 — THE ANSWER IS (b), AND IT IS READ OFF THE ARTEFACT

The brief offered three possibilities and asked for a measurement, not a record:

* **(a)** the asphalt re-budget is in source but not in the rendered film
* **(b)** it is in the film and still measures blank
* **(c)** it was never wired into the shipped path

**It is (b).** Both the proxy's scene and the ship candidate carry the whole
R2-1031 re-budget:

```
tools/r2_3061_film_material.py --blend render/film22.blend
  pulled 'M_Surf_Asphalt' out of film22.blend  (1129 nodes, 1593 links)
  amp_field PRESENT   chip_hi PRESENT   offline PRESENT   ravel PRESENT
  screed    PRESENT   craze   PRESENT   pluck   PRESENT   h_hard PRESENT
  >> STAGE RESULT: FILM_CARRIES_REBUDGET (8/8)

  same result, byte-identical census, on render/film23_breach.blend
```

`bpy.data.libraries.load` pulls the one material and its dependencies out of the
10 GB film without opening the scene, so this cost a seek rather than an hour of
swap. The 38-texture wavelength census of the material inside the rendered film
is **identical to a fresh build of `world/build_surface.py` at HEAD**, including
every layer R2-1031 added: nest 69.0 mm, seg2 187.6 mm, screed 277.8 mm,
craze 303.0 mm, ravel 454.5 mm.

The record agrees once you look at the right record. `assembly14_build.json`
records `world/build_surface.py` at sha256 `678fdb3fa6a7…`, which is the blob at
commit `244ff16`; `git merge-base --is-ancestor cc38455 244ff16` confirms the
R2-1031 re-budget commit is an ancestor of it. The **only** difference between
that state and HEAD is `76a685b`, which replaces four retyped car-box literals
with `C.CAR_BODY_*` and is inert by its own measurement.

> ### CORRECTION FOR WHOEVER PLANS THE REBUILD
> `docs/NEXT-REBUILD.md` lists **"Asphalt relief re-budget"** in the table
> headed *"Landed in SOURCE, in no film blend"*. **That row is wrong.** It is in
> `film22.blend` and in `film23_breach.blend`, and it has been since
> `assembly11` (2026-08-07 22:40). **The rebuild does not carry a fix for this;
> the rebuild reproduces what has already been measured as defective.**
> This is not a small bookkeeping error: it is the difference between "nothing
> to do, the rebuild handles it" and "this is unfixed".

### The false negative this file caught on itself

The first version of `r2_3061_film_material.py` looked for the re-budget's tags
as node **names** and printed `FILM_MISSING_REBUDGET (0/8)`. `_G.tag()` writes
`node.label = "DBG:" + name`. Had that gone unchecked it would have sent this
task off to re-author a material that was already there — the exact outcome the
brief was written to prevent, arrived at by an instrument rather than by a
document. What caught it was the wavelength census printed beside the verdict:
38 textures at wavelengths identical to a fresh build is not what a missing
re-budget looks like. The tag check now also prints how many labelled nodes
exist at all, so "found 0 of 8" can never again be indistinguishable from
"looked in the wrong field".

---

## R2-3062 — WHERE THE RE-BUDGET WORKS, AND WHERE IT STOPS

`tools/r2_3061_*` join the instrument's own per-tile numbers
(`work/r22881/scan.npz`, all 2,978 × 48 tiles) to the geometry it never
measured: a vectorised ray through every tile centre of 148 sampled frames,
onto `world_contract.ground_z`, giving each tile its **surface class**, its
**millimetres per 4K pixel**, and its **180-degree-shutter smear**. The
contract's own `project()` is used for the inverse — this project does not need
an eighth copy of that search.

Two confounds had never been controlled for, and both are large.

**The band is not a fixed size in metres.** 16-64 px at 4K is 0.33-1.33 m of
road at the film-wide median sampling of 20.8 mm/px, and **61-243 mm** at
f1787's 3.80 mm/px. A table indexed in pixels compares 4 cm of road against
2.5 m of it. Indexed in world scale instead, with the subject box excluded and
smear held under 40 px:

```
band (mm)      ASPHALT              KERB_BAND            RUNOFF / TERRAIN
             raw     rel   n       raw     rel   n       raw     rel   n
  60-120         .                     .                0.00852 0.024  61
 120-250     0.00210 0.005  96     0.00653 0.014  17    0.00810 0.021 138
 250-500     0.00549 0.014 137     0.00953 0.024  24    0.00937 0.030 245
 500-1000    0.00756 0.023  92     0.00809 0.023  21    0.01146 0.036 394
1000-2000    0.01074 0.035  23     0.00993 0.025   7    0.01328 0.035 309
2000+        0.01732 0.057  15           .              0.01031 0.028 302
```

`rel` is the band divided by the tile's own mean level, because the raw band is
an absolute Laplacian magnitude and asphalt is the darkest large surface in the
film. **The darkness confound is refuted rather than assumed**: the tile means
are 0.451 / 0.351 / 0.327 for asphalt against 0.393 / 0.392 / 0.330 for terrain
in the same rows, so the two are being read at the same level and the raw and
relative columns tell the same story.

**The re-budget worked, at the scale it aimed at.** Above 1 m the asphalt equals
or beats every other surface in the frame — 0.035 against terrain's 0.035, and
0.057 against 0.028 above 2 m. Below 250 mm it delivers **0.005 against the
terrain's 0.021 and the kerb's 0.014, a quarter of what everything around it
carries**, and the deficit grows monotonically as the scale gets finer.

And the same join reproduces R2-2881's own shape finding — *"64 % of the empty
tiles are in the bottom two rows"* — with the surface named, which is what turns
a shape into a cause:

```
   tile row   ASPHALT tiles empty      GROUND BESIDE IT empty     median range
      0        48.1 % of 79             5.7 % of 332                22.1 m
      1        39.6 % of 144            7.3 % of 533                40.2 m
      2        24.4 % of 357            1.7 % of 649                44.2 m
      3        21.7 % of 692            5.6 % of 395                24.0 m
      4        59.0 % of 619           10.1 % of 427                16.9 m
      5        73.6 % of 515           12.8 % of 523                14.5 m
```

**In the two nearest rows the road reads empty three quarters of the time and
the runoff beside it one time in eight** — same frame, same lens, same grade,
same distance, same shutter. Whatever this is, it is a property of the road
surface and not of the delivery.

**Why it stops there is in R2-1031's own arithmetic.** It derived the film's
readable band from a road-coverage-weighted median of 20.8 mm/px and concluded
"about 40 mm to 2 m", then placed six meso structures at 0.15-1.0 m. That is a
correct fix for the median frame. The frames R2-2881 named are not median
frames: f1787 samples at **3.80 mm/px**, five times finer than the sharpest
frame the material has ever been tested at, and nobody re-derived the target
band for them.

---

## R2-3063 — THE CONFOUND NOBODY CONTROLLED: THE SHUTTER

`build_surface.FILM_POSE_FRAMES` is `(1547, 2225, 2000, 1226)`. Those were
chosen off `render/r2651/track_scale.json` as the frames where the surface is
sharpest. The same table, same column, for the frames the client is complaining
about:

```
              mm/px   road cover   CoC     camera streak @4K
  f1547        11.77     46 %      0.80 px      7.0 px    <- a test frame
  f2225        20.96     18 %      0.26        10.3 px    <- a test frame
  f1226        51.52     41 %      0.46         5.4 px    <- a test frame
  f2000        11.46     50 %      0.02        69.7 px    <- a test frame
  ------------------------------------------------------------------
  f1350         5.18     62 %      0.45       214.0 px    <- the defect
  f2622         4.22     98 %      2.11       213.2 px    <- the defect
  f1787         3.80     91 %      0.24       245.2 px    <- the defect
```

**The material has never been looked at, in a test frame or in a gate, under
anything within thirty times the shutter of the frames it is being judged on.**

### STATE THIS IN THE GENERAL FORM, BECAUSE IT IS NOT ABOUT ASPHALT

This project keeps a family of defects called *"an instrument that reads the
same whether the thing is there or not"* — `NEXT-REBUILD.md` says it now has
more than a dozen members. **This is a new and different kind, and it needs its
own name:**

> **A TEST BED THAT DOES NOT RESEMBLE THE DELIVERY.**
>
> Every instrument here worked. `relief_gate` passed, `bump_relief_report`
> audited the right wavelengths, the octave-contrast probe measured real
> contrast, the four film-pose frames were chosen off a real per-frame table and
> rendered at real delivery resolution. **Nothing was vacuous and nothing was
> broken.** They were simply all run on frames where the ground drags **5.4 to
> 69.7 px** across the open shutter, and the film delivers this surface on
> frames where it drags **213 to 245 px**. The surface was never once evaluated
> under the motion it actually experiences.

The reason it evaded everything is that the test frames were selected *by
sharpness* — `FILM_POSE_FRAMES` picked the frames where the surface is most
readable, which is the natural thing to do when the question is "does the
aggregate exist" and the exactly wrong thing to do when the question is "does
the audience see it".

**It generalises to every surface in this film that has been judged on a still,
and most of them have been.** Anything tuned on `surface_test_*.blend`,
`macro_audit.py` (which sets `use_motion_blur = False` explicitly, and says why
— *"a still audit; blur would mask softness"*), `idpass_probe.py` or
`driver_containment.py` has the same exposure. The right correction is not to
stop using stills — a still is the correct bed for "is it authored" — but to
require that any surface finding also be taken **once** at the delivered
shutter, on a frame chosen from the DEFECT end of `track_scale.json`'s `mb`
column rather than the sharp end. That is what `r2_3061_nearfield_scene.py`
does, and it costs one extra camera in the same blend.

Independently confirmed. A separate ray probe written for this task puts f1787's
tile-centre smear at 205-232 px at 4K and its sampling at 3.35-4.05 mm/px;
`track_scale.json` — a different instrument, written by a different agent for a
different purpose — says 245.2 px and 3.80 mm/px. Two independent measurements
of the same quantity agree.

The shutter is a second, multiplicative term, and it is not small:

```
ASPHALT, world band 60-500 mm, by shutter smear (raw / rel / n)
   0-40 px   40-80 px   80-160 px  160-320 px   320+ px
   0.0040     0.0026     0.0016     0.0010      0.0006     raw
   0.011      0.008      0.006      0.003       0.002      rel

KERB_BAND, same band, same bins
   0.0093     0.0112     0.0094     0.0102      0.0080     raw
   0.021      0.030      0.032      0.029       0.015      rel
```

The kerb is **flat** across the whole smear range and the asphalt falls 6x. A
180-degree shutter does not remove contrast, it removes it **along one axis**;
what survives is contrast large enough to survive being averaged over 245 px in
that direction, and the kerb's painted blocks are, and the asphalt's is not.

On the finding's own tile the axis is measurable. Predicting the smear direction
from the camera path and measuring the direction of least variation in the
native 4K frame:

```
f1787 tile(3,1)   smear 218.8 px   predicted axis 105.8 deg   measured 106.7 deg
                  across/along the smear axis: 3.26 / 2.30 / 1.84 at L = 8/16/32 px
```

**Consequence for the fix, and it is the whole reason this section exists.**
Structure authored into 16-64 px on these frames is halved before it reaches the
audience, because the shutter erases the along-road axis of it. The material's
own finest in-band layer, `streak2` at 91 mm across by 3.3 m along, is oriented
exactly along the smear. Authoring more longitudinal structure into this
material would be this project's third documented double correction. What
survives is **isotropic and transverse** contrast at 40-250 mm.

---

## R2-3064 — THE NEAR-FIELD RIG (in flight)

`tools/r2_3061_nearfield_scene.py` builds one blend, one camera, six frames:
1350 / 1787 / 2622 on the delivered path with the film's own 0.5 shutter, lens,
f-stop and focus, and 4350 / 4787 / 5622 at **the same poses held still** — five
identical keys, so camera velocity is exactly zero and the same view renders
with no motion blur at all.

The still twin is the control the whole question turns on:

* healthy still, empty live → the defect is the shutter, and shader authoring
  cannot reach it
* empty in both → the material is blank in that band and `_mat_asphalt` is the
  repair

Both arms are one camera at different frame numbers, so the control rides in the
same broker job and costs no extra cold start — and on this fleet the cold start,
not the rendering, is what a job costs. The file refuses to write a blend whose
two arms are not measurably different, checked on the evaluated depsgraph at
±0.25 frame rather than on the keys it just wrote.

Judged by `tools/r2_3061_judge.py`, which imports `tools/r2_2881_pixelpeep.py`
and uses its `pyramid`, its 12-proxy-px tile erosion and its
`Gates.TILE_COARSE = 0.0020` unchanged, so a number here and a number in
`work/r22881/findings.json` mean the same thing.

Both arms are built from an EXPLICIT `build_surface.py`, named on the command
line and sha256'd into the log: the BEFORE arm runs
`git show HEAD:world/build_surface.py`, the AFTER arm runs the worktree. Nothing
is stashed or checked out — six other agents are live in this repository and a
`git stash` here would take their files with it.

### Two API traps this rig walked into, recorded because they will recur

* `Action.fcurves` **does not exist in Blender 5.2** — actions are slotted and the
  curves are under `action.layers[].strips[].channelbag(slot)`. The first version
  walked it, raised `AttributeError`, and **Blender exited 0**; `buildlock.sh`
  duly printed `rc=0` on a run that wrote no blend at all. Judged on
  `>> STAGE RESULT:` lines, as the standing rule says. The fix sets
  `preferences.edit.keyframe_new_interpolation_type` instead, which needs no
  traversal and cannot go stale against the next API move.
* Interpolation is not cosmetic here. On BEZIER keys the camera eases into every
  key, so the live arm's sub-frame velocity across the open shutter would be the
  ease curve's rather than the delivered path's — the rig would reproduce a
  streak, but not the film's.

---

## R2-3064b — A COLD START IS 82 % OF A SMALL JOB'S BILL, AND THE SECOND ONE IS FREE

Measured while costing this A/B, and it is worth more than this A/B.

The R2-2881 4K arm cost **$0.1158**, of which **518 s of cold start** and only
259 s of rendering — its own PROVENANCE says so: *"real driver of the cost was
the 518 s cold start, not the 259 s of rendering."* `docs/operations.md:1339`
puts a healthy cold start at **502 s**. So on any job short of an hour, the
rental is mostly paying to boot.

**Two jobs do not have to pay it twice, and no flag is needed.**
`docs/operations.md:36`: `IDLE_GRACE` is *"seconds of idle before the instance
is stopped"* — the instance is stopped on **idleness**, never on job completion.
`rq`'s own `cmd_anim` docstring: *"Submit a frame range as one job… the scene
must be uploaded once and stay resident for the whole shot."* So submitting the
second job **while the first is still running** means the queue never goes idle,
the timer never starts, and the second job inherits a warm instance. The only
cost is one scene switch, governed by
`max(SCENE_STARVE_SEC, SCENE_SWITCH_PAYBACK × reload_cost)`, and at ~58 MB per
blend that is seconds.

**This roughly halves a two-job A/B and it applies to the 4K master**, which is
a dozen-plus rentals. It is recorded here rather than in the broker's own docs
because vast-render is another agent's ground on this project; **somebody who
owns `/home/zany/vast-render/docs/operations.md` should fold it in there**,
beside the cold-start row it is derived from.

---

## R2-3065 — THE 45-160 mm OCTAVE, AUTHORED

`world/build_surface._mat_asphalt`. Three structures, all new, all inside
45-160 mm, **all in ALBEDO and ROUGHNESS and none of them a new bump stage.**

| layer | wavelength | what it is | why it is shaped that way |
|---|---|---|---|
| `nest_tone` | 69.0 mm | the existing `nest` field read a second way: stone-on-stone contact zones whose binder film has worn off — exposed fracture faces, paler and slightly cooler than the mortar-rich ground between them | the octave's DENSE term. Read on a wider window than `amp_field`'s, which wants the cores; on the narrow window the octave arrives as dots rather than a texture. Same field, so it cannot disagree with the amplitude stage about where the stone is |
| `scab` / `scab_rim` | 128.2 mm | a plucked CLUSTER — dark binder-rich floor, pale fractured rim, ~5 % of cells, gated on `age` and `rubber` because scabbing is a fatigue failure and needs load | hard-edged, which is what a band-pass sees, and isotropic, which is what the shutter cannot erase along one axis. The rim is an annulus off the same distance field as the floor, so a scab cannot get its rim somewhere else |
| `chatter` | 84.7 mm | a vibratory drum's washboard across a hot mat — an octave finer than the screed plate's 0.44 m ripple, and a different machine | **transverse**. The shutter smears ALONG the road, so this is the layer that survives f1787. Wavelength on `s`, bar length on `u`, exactly as `screed` does it, so `_vector_gain` reads the same axis for both |

### A claim I wrote into the source and then had to withdraw

The first version of the comment block above said *"in ALBEDO, between `seg2` at
188 mm and `pluck` at 48 mm, there is nothing."* A graph walk back from the
Principled BSDF — added to `r2_3061_film_material.py` as
`reach_channels()` — says **all six in-band textures reach `Base Color`**, so
that sentence was false and it was in the file before it was checked. What is
true is the **route**:

```
   69.0 mm  nest     -> amp_field -> chip_hi   scales an 18 mm chip field's amplitude
   47.6 mm  pluck    -> a direct tonal term, over ~1.7 % of cells
   90.9 mm  streak2  -> only the rubbered band's WIDTH, and longitudinal
   41.7 mm  warp     -> a coordinate warp; carries no contrast at all
```

So there is **no direct tonal term** between 188 mm and 48 mm: everything in
that octave arrives as a modulation of something else's amplitude. That was
R2-1031's design and it is right where a chip is sub-pixel — but at 3.80 mm/px
an 18 mm chip is five pixels, the pixel no longer receives the field's local
mean, and the modulation competes with the chip-to-chip variance instead of
setting it. **The delivered numbers are the evidence; the route is the mechanism
they are consistent with, and the source now labels it as such rather than as a
finding.**

**No new bump stage, and that is a decision rather than an omission.** Every
bump stage in this material is budgeted at one wavelength so
`bump_relief_report` can audit it; adding an 85 mm term to a stage budgeted at
300 mm would make the audit report whichever input the DFS popped first — the
defect the `h_fine` comment already records. It is also R2-1031's own argument
one octave finer: `relief_amplitude_for` wants real millimetres of geometry to
reach the modulation band at 128 mm, a wearing course does not have them, and
inventing them would be a lie about the object. What a wearing course does have
at this scale is places that are a different colour and a different roughness.

**The weights are set against the measured deficit.** The delivered 120-250 mm
band is 0.005 of the tile mean against the runoff's 0.021, so the octave has to
gain about 4x. `seg2`'s ±7.5 % was the only in-band albedo this material had, so
the three above are sized to add roughly three more times that, split across
three structures rather than concentrated in one louder one.

**The octave census confirms they landed where they were aimed:** 41 textures,
**8 inside 40-250 mm** against 6 before, the two new ones at **128.2 mm** and
**84.7 mm**, and nothing above 250 mm or below 40 mm moved.

### The change is ADDITIVE ONLY, measured node-for-node

Both materials built side by side in one process and compared:

```
   nodes 1129 -> 1180        links 1593 -> 1667
   TexNoise   22 -> 23       TexVoronoi 12 -> 13     (+1 each: chatter, scab)
   tags added:   DBG:chatter, DBG:nest_tone, DBG:scab, DBG:scab_rim
   tags removed: []          object-space wavelengths removed: []
   >> STAGE RESULT: MATDIFF_ADDITIVE_ONLY
```

Not one existing layer moved, was rescaled or lost its tag. This change is not
inert — it is meant to change the picture — but it can only change it by
addition, which bounds what an unexpected difference in a later A/B can be.

### The number to beat

```
                                          before            target
  f1787 tile (3,1), coarse 16-64 px @4K   0.00069           >= 0.0020
    (the same frame's verge tile)         0.00853           (the emptiness
                                                             threshold is 0.0020)
  ASPHALT, 120-250 mm world band,
    smear < 40 px, band / tile mean       0.005             ~0.020
```

The near-field rig's **still** arm is where the material's own gain is read,
because that is the arm the shutter is not in. The **live** arm is what the
audience receives, and it will gain less — the shutter takes the along-road half
of anything authored here, which is why two of the three layers are isotropic
and the third runs across the road.

### THE PREDICTION, WRITTEN DOWN BEFORE THE RENDER

Stated so the measurement can falsify it rather than be read to agree with it.

`seg2`'s ±7.5 % grey swing was the only dense in-band tonal term. The three new
layers add roughly ±7.5 % (`nest_tone`), ±3.8 % (`chatter`) and a sparse but
strong `scab`/`scab_rim` pair. Three incoherent fields add in quadrature, so on
**albedo alone** the octave should gain about

```
   sqrt(7.5^2 + 7.5^2 + 3.8^2) / 7.5  =  1.5x
```

and the new layers sit better inside the window than `seg2` does — at 3.80 mm/px
the 16-64 px band is 61-243 mm, which puts `scab` at 34 px dead centre,
`chatter` at 22 px and `nest_tone` at 18 px, against `seg2` at 49 px near the
top edge. The roughness terms add specular contrast at a 12.47 deg sun that this
arithmetic does not capture at all, so the honest prediction is a range:

```
   still arm, asphalt tiles, coarse 16-64 px @4K   1.5x  to  3x
   live arm  (the shutter takes the along-road axis)   about half of that
   f1787 tile (3,1), live, 0.00069 (proxy) / 0.00085 (native)
                                        ->  0.0011 to 0.0018 native
```

**If that is what comes back, the fix as weighted is not enough on its own** and
the weights go up on the next pass, from the same arithmetic rather than by
taste. If the still arm gains 4x or more, the weights are right and something in
this estimate is understated — most likely the roughness at a grazing sun, which
would be worth knowing on its own. **A gain in the still arm with no gain in the
live arm is the third possible answer, and it would mean the shutter is the
binding constraint and the remaining work is a camera-department question, not a
material one.**

**Status: both arms building; renders not yet submitted.**

---

## R2-3066 — THE A/B, MEASURED. THE AUTHORED OCTAVE DID NOT WORK, AND IT IS REVERTED

12 frames, 3840x2160, 32 samples + OIDN, one warm instance, **$0.0957**, instance
torn down and `gpu down` confirmed. Judged with `tools/r2_3061_judge.py`, which
imports the pixel-peep instrument and uses its pyramid, its 12-proxy-px erosion
and its `TILE_COARSE = 0.0020` unchanged.

```
              coarse 16-64 px @4K, median over the ASPHALT tiles
  frame  arm     tiles    BEFORE     AFTER     change
   1350  live      30    0.00093   0.00090    -3.2 %
   1787  live      48    0.00105   0.00103    -1.9 %
   2622  live      47    0.00070   0.00070     0.0 %
   4350  still     30    0.00233   0.00229    -1.7 %
   4787  still     48    0.00257   0.00254    -1.2 %
   5622  still     47    0.00265   0.00260    -1.9 %

  the finding's own tile, f1787 (3,1)
     BEFORE   live 0.00101   still 0.00231
     AFTER    live 0.00098   still 0.00229
```

**THE PREDICTION IS FALSIFIED, AND IT WAS WRITTEN DOWN FIRST.** R2-3065 predicted
the still arm would gain **1.5x to 3x** and f1787 (3,1) live would go
0.00085 -> 0.0011-0.0018. The still arm delivered **0.99x** and the tile moved
**-3 %**. Not a shortfall at the low end of a range — no gain at all.

**It is not the blend, and that was ruled out first.** `r2_3061_film_material.py`
on the two rendered blends: BEFORE 1129 nodes / 6 textures in 40-250 mm / 21
labels; AFTER **1180 nodes / 8 textures in band / 25 labels**, with 128.2 mm and
84.7 mm present and reaching `Base Color` and `Roughness`. The AFTER blend
carries the new material. The two blends' camera motion is bit-identical
(1.412668 / 1.126481 / 1.693008 m live, 0.000000 m still, both arms), so the
material is the only variable.

**What the layers actually did**, from differencing the two 4K stills directly:

```
  f4787 still   mean 0.2280 -> 0.2245     a UNIFORM DARKENING of -1.5 %
                diff rms 0.00397, of which 0.00353 is the mean shift
                => spatial contrast added ~0.0018 rms, ACROSS ALL SCALES
```

So the three layers are live and doing something, but what they mostly did was
move the DC level down, and the spatial contrast they added — spread over every
scale, not concentrated in 16-64 px — is comparable to the coarse band it was
meant to multiply by three.

**The arithmetic failed in a specific, findable way.** R2-3065 sized `nest_tone`
at +-7.5 % on the assumption that `nest_t` spans 0..1. It is a **SMOOTH_F1**
Voronoi distance field at smoothness 0.55 — smooth, narrow-range, and with a
mean well below 0.5. A field with mean ~0.3 pushed through a 0.938..1.088 grey
multiply has an expected multiplier of ~0.983, i.e. **a 1.7 % darkening**, which
is what was measured (-1.5 %). The mean shift is therefore not a side effect; it
is the whole signature of a weight derived from a distribution that was never
measured. **I sized three layers off an assumed field statistic and rendered
before checking it.**

### THE RESULT THAT DID COME OUT, AND IT IS THE SHUTTER

The still-vs-live control worked perfectly and is the first direct measurement of
the shutter's share on identical geometry:

```
   f1350   still 0.00233   live 0.00093    the shutter removes 2.51x
   f1787   still 0.00257   live 0.00105    the shutter removes 2.45x
   f2622   still 0.00265   live 0.00070    the shutter removes 3.79x

   and in the FINE band, 0-8 px @4K, on the same frames:
   f1787   still 0.01217   live 0.00151    the shutter removes 8.1x
```

`work/r23061/crop_f1787.png` shows it without arithmetic: the **still** panels are
covered in aggregate, the **live** panels are smooth. The material is not blank.
**At the film's own shutter the audience cannot see what is there.**

And the second half of the finding survives too: even with the camera stopped,
the coarse band is **0.0026 against a 0.0020 emptiness threshold**. The surface
is genuinely coarse-poor at this sampling — R2-3062's population result stands —
but the fix authored for it did not move it.

### DISPOSITION: REVERTED

`world/build_surface.py` is restored to `9b5d6fb26e33…`, the blob at `76a685b`,
byte-for-byte. **An additive change that adds no measurable contrast and darkens
the surface 1.5 % is not neutral, and it should not ride into a 2,978-frame
master on the strength of the argument that produced it.** The instruments, the
rig and the measurements stay; only the shader change goes.

**For whoever picks this up — do these in this order, and do not skip 1:**

1. **Measure the three fields' actual distributions before weighting anything.**
   Mean and standard deviation of `nest_t`, `scab`, `scab_rim` and `chatter` as
   the graph evaluates them. Every weight in R2-3065 was derived from an assumed
   0..1 uniform and every one of them was wrong.
2. **Centre any grey multiply on the field's measured mean**, not on 0.5, or the
   layer is a brightness change wearing a contrast change's clothes.
3. **Budget against the still arm**, which is where the material's own gain is
   readable. The live arm is the audience's view and divides by 2.5-3.8.
4. **Ask whether albedo is the right channel at all.** 0.0018 rms of added
   spatial contrast on a 0.22 mean is 0.8 %, and it did not concentrate in the
   band. The still panels say this surface's energy is overwhelmingly at 0-8 px;
   moving energy UP in scale may need the aggregate's own cell size to change,
   not another field multiplied over it.
