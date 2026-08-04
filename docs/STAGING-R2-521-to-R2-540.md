# STAGING — R2-521 to R2-540 (the hero bodywork's paint)

Owner: the hero-subject material block. `docs/DEFECT-LOG-R2.md` is not mine to edit.

**The subject:** `LiveryPaint`, the material on the car's 14 bodywork panels —
`EC_shell`, `MB_nose`, `MB_chassis_fwd`, `MB_chassis_cockpit`, `MB_sidepod_L/R`,
`MB_engine_cover`, `MB_tail_fairing`, `MB_tail_cap`, `NOSE_Shell`, `SP_flank`,
`SP_front`, `SP_mirror`, `SP_scoop`. Authored in round 1 as
`/home/zany/opus5-car-render/build/s03_materials.py::livery_paint`, tier B.

**The report:** the bodywork reads as translucent pale-blue glass —
`r1full_000697.png` head-on, and (R2-543, an independent gate) across f643-f739
at a clean three-quarter as well, with "internal lattice, wiring and far-side
suspension visible through the skin".

**The two hypotheses put to this block:** (1) one opaque material whose head-on
read is a near-mirror clearcoat plus Fresnel, or (2) genuine transmission in the
body shader. R2-543's three-quarter frames were taken to make (2) much the more
likely, because a Fresnel story cannot make a body transparent across a wide arc.

**Neither is what is happening.** It is measured below, three independent ways,
and the answer is a third thing.

---

## R2-521 — TRANSMISSION IS NOT THE CAUSE. It is exactly zero, and the control that says so is a rendered A/B, not a socket reading

### 1. The static reading, on the file that was actually rendered

`world/car_anim.blend` is the file the film scene appends the car from, but it is
not the file the ladder rendered. `render/film14_breach_r6.blend` is — 4.99 GB,
against 11 GB of RAM, so it cannot be opened. `bpy.data.libraries.load()` reads
the datablock index and pulls only what is asked for, which makes the question
answerable in 40 seconds (`work/r2521/probe_filmblend.py`):

```
render/film14_breach_r6.blend      192 materials, 33,565 objects
  car materials present: LiveryPaint CarbonFibre CarbonMatte CarbonCeramic
                         MatteBlack Titanium SteelFastener AnodisedRed
                         AnodisedGold SuedeGrip WheelRim TyreRubber

  EVERY ONE:   Transmission Weight = 0.0   unlinked
               Alpha               = 1.0   unlinked
               Thin Wall           = 0.0
               0 Glass / Refraction / Transparent / Translucent / Mix Shader /
                 Add Shader / Volume / SSS nodes anywhere in any of their trees
  LiveryPaint: 120 nodes, byte-for-byte the same tree as in car_anim.blend
```

That is a reading, not a control, and this project has repeatedly paid for fixes
aimed at the wrong cause. So it was rendered.

### 2. The control the brief asked for — same panel, same light, transmission forced to zero

`work/r2521/build_ab.py` builds one .blend carrying twelve shader variants as
twelve FRAMES, with the car, the turntable and everything else FROZEN at world
frame 697 (measured drift between variant frames: **0.000e+00 m**), and one
camera keyframed to two stations taken straight out of `render/film14_path.json`
— the ONER's own f697 head-on and its own f655 three-quarter. Twelve separate
files would have been 3.6 GB of upload into a farm box with 9.9 GB free.

Rendered as sequence `r2521ab`, 1280x720 / 64 samples, fixed seed, AgX / look
None / exposure -3.628.

```
                                        max     mean    px differing
                                        LSB     |d|     by >2 LSB
A_shipped  vs  B_trans0                   1    0.0168        0        <- THE CONTROL
A_shipped  vs  P_trans035                99    0.3104   28,763        <- positive control
```

**Forcing `Transmission Weight` to zero changes nothing** — one LSB of GPU
non-determinism, not a single pixel moving by more than two. **Setting it to 0.35
changes 28,763 pixels.** The rig can see transmission; the shipped material has
none.

### 3. The complete energy budget, which needs no ablation at all

`work/r2521/pass_probe.py` masks the 14 panels by `pass_index` — exact, no edge
estimation, no colour keying — and measures every light path leaving them.
**Light passes multiplied by their colour passes:** Cycles stores `Diffuse
Direct` WITHOUT the surface colour, and the first draft of this probe summed the
uncoloured passes and read "47 % diffuse" off a surface whose diffuse colour is
0.012 and whose glossy colour is 0.27. That number was wrong by 17x.

```
station                     diffuse   glossy   emission   TRANSMISSION
head-on     (ONER f697)      2.78 %   96.44 %    0.78 %     0.0000 %
three-quarter (ONER f655)    7.32 %   88.94 %    3.74 %     0.0000 %

  transmission-pass pixels above 1e-6, out of 5,138 / 11,622:   0 and 0
  maximum transmission-pass pixel:                              0.0 and 0.0
  diffuse + glossy + emission + transmission  vs  the Combined pass:
      head-on        19.03819  vs  19.03819      delta 2.9e-06
      three-quarter   6.01280  vs   6.01280      delta 3.4e-06

positive control — the SAME panels, the SAME light, Transmission Weight 0.35:
      2,612 and 6,593 transmission-pass pixels light up, peaking at 29.4 / 51.4
```

**The picture of the bodywork is fully accounted for by reflection, paint and
glow, at both stations, to six decimal places. Nothing arrives through these
panels.** Hypothesis 2 is dead, and it is dead at the three-quarter station too,
which is the station that was thought to prove it.

### 4. And the visibility control, which is the one to look at

Variant `K_panelsonly` hides all 602 other CAR meshes and renders the 14
bodywork panels alone — no suspension, no wheels, no wings, no internals, no
lattice, nothing whatsoever behind the skin.

**The shell still reads as translucent pale-blue glass.**
`out/seq/r2521ab/r2521ab_000012.png`.

There is nothing left for it to be transparent *to*. What is being read as
"internal structure seen through the skin" is the panel's own surface.

---

## R2-522 — WHAT IT ACTUALLY IS: the panel has no paint in it. 96 % of the hero subject's appearance is the room reflected in it

Measured, from the same probe:

```
the bodywork's DIFFUSE COLOUR (its albedo), luminance:   0.0121
```

For scale: fresh asphalt is 0.05-0.07, a "midnight" automotive navy 0.02-0.04, a
mid navy 0.05-0.09. **The hero subject of the film is painted in something
darker than a road surface**, and then 62 % of what little diffuse response that
leaves is removed again by `Metallic = 0.62`.

A surface with no diffuse response is not a dark surface. It is a **mirror**, and
a mirror in a showroom full of structure looks like a window onto structure. That
is the whole of the effect:

| | head-on | three-quarter |
|---|---|---|
| the room, reflected | **96.4 %** | **88.9 %** |
| the car's own paint | 2.8 % | 7.3 % |
| the livery, glowing | 0.8 % | 3.7 % |

And it explains the thing the two hypotheses were built to explain — why f697
looks like glass and f655 looks like navy. It is not the material swinging with
angle. **It is what the mirror is pointed at.** Head-on the panels reflect a
bright ceiling and a lit room; at three-quarter they reflect a darker wall, so
the same 2.8-7.3 % of actual paint is a bigger share of a smaller number and the
navy shows. The material never changed.

### The ablation ladder, ranked by how much each moved the picture

All at the head-on station, 1280x720/64, against `A_shipped`:

```
variant          mean |d|   px>2LSB    what it says
K_panelsonly      14.1124   281,680    (visibility, not a shader change)
Q_albedolift       2.2002    77,724    lifting the basecoat x6 is the single
                                       biggest shader change available
N_noartwork        0.9171    44,222    livery colour AND glow both off
C_nocoat           0.8313    53,096    the clearcoat is NOT the mirror on its own
H_nometal          0.6666    31,934
G_flatpaint        0.6260    35,452
D_coatwhite        0.4614    39,220    the pale blue is not the coat tint either
F_noemis           0.3938    26,914    the teal network goes; the glass stays
P_trans035         0.3104    28,763    <- ADDING 35 % REAL TRANSMISSION
B_trans0           0.0168         0    <- the noise floor
```

**Adding thirty-five per cent genuine transmission moves the picture less than
five of the ablations do, and barely more than the noise floor.** The panel was
already behaving like glass without any.

Two negatives worth keeping, because both were plausible and both are wrong:

* **The clearcoat is not the mirror.** `C_nocoat` removes it entirely and the
  body is still glassy — `Metallic 0.62` over a 0.006 base is its own near-black
  mirror, and it goes white at grazing on its own.
* **The pale blue is not `Coat Tint`.** `D_coatwhite` neutralises
  (0.68, 0.82, 0.90) and moves 0.46 mean LSB. On a panel that is 96 % reflection
  the tint had almost nothing to tint. The blue is the room.

### What the glowing network is, and what it is not

`F_noemis` removes the teal cell network from the body and leaves the glass read
untouched. So the network is not the cause — but it *is* the thing being
described as "internal lattice and wiring", and it is worth naming exactly:

round 1 puts the artwork's entire pattern in **`Emission Strength`**, as a
five-rung ladder (streams 0.35, graph edges 0.40, graph junctions 3.20, pulse
line 6.00, numeral 9.00). `Emission Color` is a **flat** cyan. So the body-wide
node-graph network is a body-wide *light source*, radiating through the paint,
and it reads as glowing internals wherever the mirror behind it is dark. That is
also why it is far more visible at three-quarter (3.74 %) than head-on (0.78 %).

---

## R2-523 — a rig that measures a room 12.4x too dark measures nothing. The first build of this one did

Recorded because it nearly produced a confident wrong answer, and because the
next agent to build a rig out of `world/car_anim.blend` will hit it.

The first build of the A/B rig rendered the showroom almost black, and the first
pass-probe run reported **29.5 % emission** at the three-quarter station. Both
came from the same cause:

> `world/car_anim.blend` carries round 1's practicals at the level they were
> authored for, which `s05_lighting_v2.py`'s own docstring pins to **view
> exposure 0.000**. The film grades at **-3.628**, and `world/showroom_lighting.py`
> lifts every interior practical by exactly `+3.628` stops **in the film scene**
> to cancel that. `car_anim.blend` has not had that lift applied.

Verified against the shipped scene rather than assumed — light energies linked
out of `render/film14_breach_r6.blend`:

```
              car_anim.blend    film14_breach_r6.blend    car_anim x 2^3.628
Key                 1097.5              13568.94               13568.8
Fill                 743.0               9186.59
Rim                  300.6               3716.01
Spot_0               471.9               5834.65
FloorGraze            21.8                269.47
```

Every rig in this block now calls `showroom_lighting.apply(scene)` and then
`assert_levelled(scene)` before it does anything else. With the room at the
film's level the emission share falls from 29.5 % to **3.74 %** and the glossy
share rises to 88.9 % — the diagnosis got *stronger*, but it would have been
argued from the wrong numbers.

**The rule this leaves:** any rig built on `car_anim.blend` (or
`car_anim_driver.blend`) and graded at `FILM_EXPOSURE` must level the practicals
first, or it is not looking at the film's room.

---

## R2-524 — the fix: `world/car_paint.py`

Round 1's tree is read-only, so round 2 retro-fits the car's materials from its
own side. This is the sibling of `tools/imperfections.py`:
**`imperfections.py` owns wear, dust, scratches and the clearcoat's micro
break-up; `world/car_paint.py` owns the paint STACK — what the panel is made
of.** Run `car_paint` first, `imperfections` second; both chain onto whatever
they find, both are reversible.

Everything is procedural and hand-built. Nothing downloaded, nothing generated.

```
substrate   2x2 twill carbon, TRIPLANAR, 5.0 mm tow pitch, telegraphing through
            the paint in albedo (+-8.5 %), roughness and normal (40 um).
            The twill is `mod(i - j, 4) < 2` — a 2/2 float advancing one tow per
            row — and each tow is a parabolic dome across its own width, so the
            albedo, the gloss and the relief are all read off ONE height field
            and cannot disagree with each other. Faded toward its own mean over
            |dot(N,I)| 0.10-0.42, because Cycles cannot prefilter a procedural
            and a foreshortened twill aliases into moire.
basecoat    a SCREEN lift, not a gain: screen(a,b) maps black to b exactly and
            leaves white at white, so VOID_NAVY goes 0.0107 -> 0.0283 luminance
            (2.6x) while the livery's signal-white bars, calibrated in round 1
            against a 1100 W key, do not move at all. A multiply would have
            pushed them to 1.7 and clipped them.
metallic    0.62 -> 0.10, as a SCALE on the existing link so the nose's carbon
            dissolve still reaches 0. Metallic is not "has flake in it": it
            deletes the diffuse lobe and colours the specular by the base
            colour, which is precisely the two things measured wrong.
flake       per-cell facet normals from a smooth-F1 Voronoi at 0.35 mm, gated by
            a 55/m drift field so the flake settles in drifts as real paint
            does, plus a per-cell gloss lift. The shipped material's "flake" was
            a SCREEN blend of a scalar noise into the colour — that brightens,
            it cannot sparkle. FLAKE IS A NORMAL, NOT A COLOUR.
pearl       a LayerWeight FACING shift navy -> teal, peaking 0.35 at the
            shoulder. Facing, not Fresnel, for the reason round 1 established on
            this same car: at Blend 0.28 the Fresnel output puts its whole
            transition inside the last 12 degrees before grazing.
clear       Coat Tint (0.68,0.82,0.90) -> (0.96,0.975,1.00); Coat Roughness
            0.022 -> 0.038. imperfections.py adds a PROPORTIONAL +-20 % on top,
            so lifting the base value widens that break-up in proportion too.
orange peel ROUND 1 PUT IT ON THE WRONG NORMAL. `livery_paint` builds a
            scale-140 noise -> Bump(0.035, 0.0025) and feeds it to
            `Principled.Normal` — the BASE. Orange peel is a clearcoat surface;
            it is what makes a reflection ripple. Under a 0.022-roughness coat a
            base-normal perturbation is very nearly invisible. The existing bump
            chain is not rebuilt, it is RE-ROUTED to `Coat Normal`, so round 1's
            tuning of its amplitude survives intact.
livery      moved out of the glow and into the pigment. The pattern is in
            Emission STRENGTH and the colour socket is flat, so the STRENGTH
            drives the mix factor and the colour is what gets mixed in — feeding
            the colour socket to a factor, which the first draft of this module
            did, floods the whole body flat cyan. Emission itself is passed
            through a ramp that cuts the BOTTOM of round 1's ladder (streams
            0.35, graph edges 0.40 -> x0.25) and leaves the TOP alone (pulse line
            6.00, numeral 9.00 -> x1.00), so the body-wide network stops being a
            light source and the film's two designed light sources do not move.
```

**Reversibility is gated, not asserted.** `--strip` removes every `R2CP_*` node
and restores the ten Principled sockets from a JSON snapshot stored on the
material. Measured: apply then strip on a copy of `world/car_anim.blend` and
compare the full node list, the full link list and every unlinked socket value
against the untouched original — **IDENTICAL: True**, 98 nodes removed, 10
sockets restored.

Cost: +100 nodes on a 120-node tree.

---

## R2-525 — the before/after, and the two things the macro station settled

`render/r2521/r2521_before.blend` and `render/r2521/r2521_after.blend` are one
geometry, one freeze, one camera, four stations, and **the only difference
between the two files is whether `world/car_paint.py` has been run.** Sequences `r2521before` (out/seq) and `r2521after6` (out2/seq — the bulk broker),
1920x1080 / 160 samples, AgX / None / -3.628.  `r2521after`, `...after2`,
`...after4` and `...after5` are the superseded tuning arms and are kept only so
the retunes in R2-526, R2-527 and R2-529 can be checked.

```
f1  wide head-on      the ONER at world f697
f2  wide three-quarter the ONER at world f655
f3  flank macro       0.62 m off MB_sidepod_L on a 65 mm lens  (~5,500 px/m)
f4  nose macro        0.55 m off MB_nose on a 58 mm lens
```

Matched crops, the box fixed between arms, in `work/r2521/crops/*_AB.png`.
**`f2_quarter_flank_AB.png` is the one frame that carries the whole result**: on
the left the monocoque is a translucent teal-glass tube with the far-side
structure and a pushrod legible through it; on the right it is an opaque painted
navy body with its surface visible, its pulse stripe under the clear, and nothing
showing through it.

### What the BEFORE macro settles, and it is not what was expected

`r2521before_000003.png` puts a `CarbonFibre` part and a `LiveryPaint` panel in
the same frame at the same distance.

**The carbon has a crisp, correct 2x2 twill.** It resolves cleanly, no tiling,
no smear. **The painted panel has nothing at all** — a smooth teal-to-navy
gradient with no weave, no flake, no clearcoat structure, no texture of any kind.

This is a partial correction to R2-544 ("no carbon weave anywhere on the car;
the wings read as flat clay"), and the correction matters because it changes
what has to be built:

> **The carbon weave is authored, it is correct, and it is invisible at rung 1
> for a reason that is arithmetic.** At 1280x720 the car spans roughly 600 px for
> 5.6 m, i.e. **107 px/m**. `CarbonFibre`'s twill is 190 repeats/m — **0.56 px
> per weave cell.** It cannot appear at rung 1 and no amount of authoring will
> make it. At the macro station, 5,500 px/m, the same weave is 29 px per cell and
> it is there. R2-544's evidence is a 720p sequence; the finding it supports is
> "rung 1 cannot show weave", not "the car has no weave".
>
> **What R2-544 is right about is the PAINT**, and the macro frame shows it with
> nothing to argue about: the bodywork panels carry no surface at any distance.

`r2521before_000004.png`, the nose macro, is the frame to put in front of anyone
who wants the defect in one picture: the nose reads as a sheet of wet cellophane
over pale-blue shards. The "shards" are round 1's own designed carbon-dissolve
cells at the nose tip, seen through a mirror finish with no paint over them.

### Where the measurement lands after the fix

Same probe, same rig, same frames, `LiveryPaint` the only thing changed:

```
station                   diffuse    glossy   emission   albedo
head-on         before      2.78 %   96.44 %    0.78 %   0.0121
                after       7.85 %   91.50 %    0.65 %   0.0369
three-quarter   before      7.32 %   88.94 %    3.74 %   0.0121
                after      19.86 %   77.05 %    3.09 %   0.0389

  albedo x3.1-3.2    diffuse share x2.7-2.8    transmission still exactly 0
```

### The MEAN is the wrong statistic, and it hides the answer

"90 % glossy" reads like nothing has changed. It has not changed much *as a
mean*, because a mean over the panel is dominated by its blown highlight: one hot
band at 99 % glossy outweighs a large area of paint. "Does it read as painted or
as chromed" is a question about the TYPICAL pixel, so
`work/r2521/pass_stats.py` re-reads the same EXRs and reports the distribution of
the per-pixel diffuse fraction:

```
                        p10      p25   median      p75      p90
head-on        before   1.36     8.73    31.02    60.69    80.23
               after    3.34    22.89    55.13    81.40    92.83
three-quarter  before   7.14    16.68    40.50    65.27    82.83
               after   19.68    37.18    67.75    86.61    94.88
                                (per-pixel DIFFUSE % of the panel's light)
```

**The median pixel goes from mirror-dominated to paint-dominated at both
stations** — 31 % -> 55 % diffuse head-on, 41 % -> 68 % at three-quarter — and the
bottom quartile, the part that was reading as glass, goes from 8.7 % to 22.9 %
diffuse. That is the change the mean could not show.

---

## R2-526 — a step in a height field is an infinite gradient, and a Bump node reads the gradient

The first rendered pass of the weave came back as **flat rectangular plateaus
with hard stair-steps**, roughly 110 x 30 px at the macro station, which is a
parquet floor and not a woven laminate.

The construction was combinatorially right and numerically wrong. A 2/2 twill
floats each warp over two wefts and under two, advancing one tow per row, and
that is exactly `mod(floor(u) - floor(v), 4) < 2`. But `floor` makes it a **step
function**, and it was being used to SELECT between the warp's height profile and
the weft's. At every tile edge the height jumped discontinuously — and a Bump
node does not read a height, it reads its derivative. 110 x 30 px is 4 tows by 1
tow at a 5 mm pitch: the tile size *is* the twill's repeat, rendered as plateaus.

The fix is to carry the same period, the same diagonal and the same phase in a
function that is smooth:

```
f = 0.5 + 0.5 * cos(2*pi*(u - v)/4)        1 -> warp proud, 0 -> weft proud
h = mix(dome(fract(u)), dome(fract(v)), f)
```

The two domes cross over through the valley where both are near zero, so the
field is continuous everywhere and its gradient is bounded. It is also five nodes
cheaper per projection.

*Generalises to:* **anything a Bump node reads must be C0 at minimum.** `floor`,
`round`, `LESS_THAN`, `GREATER_THAN` and a hard `Mix` factor are all steps, and
all of them will render as faceted plateaus rather than as the pattern they
correctly describe.

---

## R2-527 — a printed livery is an INK, not a light source's colour

Also from the first rendered pass, and worth keeping because the mistake is
tempting whenever artwork is moved out of an emission slot.

The livery's pattern lives in `Emission Strength`; `Emission Color` is a flat
`PULSE_CYAN` (0.028, 0.807, 1.000). Moving the artwork into the paint therefore
means "use the STRENGTH as the mix factor" — but the first version also reused
the flat cyan as the ink, at 0.60, normalised over 0.90. The graph edges (0.40)
and the particle streams (0.35) cover essentially the whole upper body, so every
painted panel printed at ~0.3 of a saturated cyan and **the car came back pale
slate-cyan instead of navy** (`out/seq/r2521after/r2521after_000001.png`, superseded).

A light source's colour is what it emits; an ink's colour is what it reflects,
and those are not interchangeable. Retuned to a deep teal ink
`(0.013, 0.072, 0.098)` at 0.30, normalised over 2.20 so the ladder's faint rungs
print faintly and its junctions print. The pearl came down with it (0.35 -> 0.20,
and its own teal darkened), because two independent teal terms were stacking.

---

## R2-529 — the specular LEVEL is not inflated. Its DOMINANCE and its SHARPNESS were

Put to this block from a 4x crop of `r1full_000817.png`: *"even a perfect
clearcoat over a proper base should not return the room at this intensity —
whatever is driving that specular response needs to come down, or a base coat
will just sit under a mirror."*

Measured, and the second half of that is right and the first half is not.

```
                     diff_col   gloss_col     what gloss_col is
head-on   before      0.0121      0.2714      the panel's specular TINT, per pixel
          after       0.0369      0.2932
3/4       before      0.0121      0.1982
          after       0.0389      0.2155
```

**The specular tint did not come down and should not have.** 0.20-0.29 is what an
IOR-1.5 clearcoat returns averaged over a body this curved: normal incidence is
0.04, but a large fraction of a nose or a sidepod's visible area sits at 45-80
degrees where Fresnel climbs through 0.1 to 0.4, and the mean lands where it
lands. There is no non-physical multiplier in there to remove — no emissive
specular, no metallic left worth the name (0.10), no doubled lobe. Driving it
lower would mean authoring a paint that is not paint.

**What WAS wrong is that it had nothing to compete with, and that it was
mirror-sharp.** Both are now addressed and both are visible in the distribution
above rather than in the mean:

* nothing to compete with — the basecoat lift, `x3.1` on albedo;
* mirror-sharp — `Coat Roughness` 0.022 -> 0.055, and round 1's orange peel moved
  onto the coat normal where it perturbs the reflection instead of sitting
  invisibly under it. 0.022 returns a LEGIBLE IMAGE of the ceiling, which is what
  makes a panel read as chromed; 0.055 returns the same energy as a sheen.

The reflection is still bright, and it should be. A gloss-navy car in a room lit
to 46 kW of practicals *is* mostly reflection. The difference between that and
chrome is whether there is a car underneath, and now there is.

---

## R2-530 — what the ladder can and cannot be asked about surface detail

Two claims about the car's detail arrived from 720p and 4K crops of `r1full`.
Measured against this block's own frames, they resolve into a rule rather than a
verdict, and it is worth writing down because it will keep coming up.

**The rule is px/m, and it is arithmetic, not judgement.**

```
rung 1, 1280x720, car ~600 px for 5.6 m                      107 px/m
the macro station, 1920x1080, 0.62 m on a 65 mm lens       ~5,500 px/m

CarbonFibre's twill              190 repeats/m   ->  0.56 px/cell at rung 1
                                                    29   px/cell at macro
```

A 0.56 px feature cannot be seen, cannot be authored into visibility, and does
not indicate missing authorship. `r2521before_000003.png` puts a `CarbonFibre`
part and a `LiveryPaint` panel in one frame at 5,500 px/m: **the carbon's twill
is crisp and correct; the paint has nothing.** Both statements are about
authorship. Neither could be made at 107 px/m.

Corroborated independently from a 4x crop of `r1full_000817.png`: the engine
cover carries fine louvres, rivet lines, marker lights and correctly swept wing
pylons; the rear-wing element is a thin, properly swept aerofoil section. So
"the car has no surface detail" is too broad. **Detail is present on some
components and absent on others, and the absent one that this block owns is the
paint.**

**And a number that is not about the car at all.** A rear-wing mainplane measured
at 1.070 m span x 0.280 m thick — a 58.6 % thickness-to-chord ratio against a
real 10-15 % — is a measurement of `sim/breachlib.py`'s COLLISION PROXY, not of
the rendered wing. The visible wing is fine. Any fix aimed at that number would
have rebuilt geometry that was never wrong, and the frames would have shown no
improvement. *Generalises to:* **before acting on a measurement of the car, check
which artefact it was taken from** — this project carries a render car, a physics
proxy and several diagnostic blends, and they do not have the same geometry.

---

## R2-528 — handover: where this has to land, and what is still open

**The fix is `world/car_paint.py`, and it HAS been applied to both car sources.**

The car goes into the film through `tools/build_film_scene.py --car <blend>`, and
the `film16` build used `--car world/car_anim_driver.blend`. Applied 2026-08-04,
after checking that no process held either file (`film16.blend` was already built
and `apply_breach` was reading that, not these):

```
world/car_anim.blend           LiveryPaint +94 nodes   R2CP_VERSION 3
world/car_anim_driver.blend    LiveryPaint +94 nodes   R2CP_VERSION 3
  pre-change copy: work/r2521/car_anim_PRE_R2521.blend.bak
  reports:         work/r2521/applied_car_anim{,_driver}.json
```

**`film16.blend` was built at 16:26, before this landed, so it does NOT have the
paint in it.** The next rebuild does. Nothing was done to `film16.blend` or
`film16_breach.blend` — this block did not touch the scene the breach is being
applied to.

It is idempotent (it strips itself before re-applying), it is exactly reversible
(`--strip`, gated: IDENTICAL True on the full node list, the full link list and
every unlinked socket value against an untouched copy), and it must run BEFORE
`tools/imperfections.py`, which chains onto the coat roughness and the coat
normal this module leaves.

**`tools/imperfections.py` has still never been applied to the car either.**
R2-015 closed on the audit blend and its own note says so: "it has NOT yet been
injected into `world/beat1_anim.blend` or into the unified world". Measured here
— `LiveryPaint` in `render/film14_breach_r6.blend` contains **zero
`ShaderNodeGroup` nodes**, so `R2_Imperfection` is not in the shipped car. The
clearcoat orange-peel micro-relief that R2-015 spent six tuning passes on is not
in a single rendered frame of the ladder.

**Still open on the hero subject, and NOT in this block's scope:**

* Tyre tread pattern and sidewall lettering (R2-544). `TyreRubber` is a 15-node
  material with one noise and a bump; whether the tread should be geometry or
  shader is a separate decision from the paint.
* The wings. Their carbon IS authored and correct; whether the rung-1 read of
  "flat clay" needs a lower-frequency, larger-scale surface story that survives
  107 px/m is a real question and a different one from this.
* Fibre striation along each tow. The twill here carries tow shape and the
  twill diagonal; it does not carry the individual filaments, which would show at
  ranges closer than the 0.62 m macro station.

