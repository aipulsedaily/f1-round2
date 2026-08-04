# Staged for the defect log's owner — R2-266 to R2-274

Kept out of `docs/DEFECT-LOG-R2.md` deliberately: that file has one owner. My
block is **R2-266 to R2-280** and I have used nine of it. Paste or renumber as
you see fit.

All of it is one job: **making the aperture read in the closing frame.** This
was an APPLY and a set of measurements, **not a bake**. `sim/out/breach_film.npz`
is untouched and byte-identical to the one `film14_breach` was built from.

Artefacts

| | |
|---|---|
| **`render/film14_breach_r6.blend`** | the ship candidate — `film14` + the breach + **the east frame** |
| `render/film14_breach_r6_DEMO.blend` | **NOT A DELIVERY.** The demonstrator behind R2-273 |
| `sim/eastframe.py` | new — the frame plan, no `bpy`, 11 controls |
| `sim/wallstats.py` | new — region statistics off the projected wall, with the controls |
| `sim/out/eastframe_prediction.json` | written **before** the after-render was queued |
| `sim/out/frame_verify_r6.json` | read back from the saved 4.99 GB blend |
| `render/r6_before/`, `render/r6_after/`, `render/r6_demo/` | the pictures |

---

## R2-266 — R6 was a requirement addressed to nobody, and 152 bodies were counted and thrown away

`apply_breach.REQUIREMENTS` has carried **R6 `frame_transform_binding`** since the
module was written: *"whoever meshes mullion_intact / mullion_bent_stub /
curtain_wall_transom binds to the MUL\*/TRN\* names in `sim/out/breach_film.npz`."*
Nobody was whoever. The corresponding code in `build()` was:

```python
n_frame = 0
for j, nm in enumerate(names):
    if not (nm.startswith("MUL") or nm.startswith("TRN")):
        continue
    n_frame += 1
log("frame bodies in the table: %d ..." % n_frame)
```

It counts 152 bodies, **prints the count, and writes nothing.** So every film
built since the breach first shipped renders round 1's static, undeformed
aluminium grid straight across a 2.15 × 6.00 m hole — including the closing
wide, which is the only place in the film where the wound is legibly on screen
at all, and the biggest look in the picture.

`render/breach_f9/f9_1920_f0880.png` is the evidence and always was: the car is
already outside, the wall is a spiderweb, and **the frame it went through has
not moved by one vertex.**

**A printed count looks exactly like a used count.** The log line was truthful,
was read by everyone who ran the applier, and said `152` every time — the same
number a correct build would print.

**Fixed** by `sim/eastframe.py` + `apply_breach.build_frame()`. Round 1's
`GW_Right_Mull_04/05/06` and `GW_Right_Transom_0/1/2` are deleted at apply time
and rebuilt as the 39 pieces the bake partitions them into, keyed off the baked
transforms. Read back from the saved 4.99 GB blend: at frames 1 and 844 every
replaced member's world AABB equals round 1's to **0.0000 mm**, and the eight
mullions the fix does not touch move **0.0 m** at every frame tested.

---

## R2-267 — the bake breaks 1.55 m of one mullion and nothing else, and the headline says otherwise

The standing description is *"mullion 5 travelling 4.43 m and shedding two
segments."* Both halves are true and together they read as a frame that came
apart. Measured over every frame body in `sim/out/breach_film.npz`:

| body | max travel |
|---|---|
| `MUL05_S01` | **4.742 m** |
| `MUL05_S00` | **3.932 m** |
| `MUL05_S02` … `S07` (z 1.55 → 6.22) | 0.145, 0.112, 0.083, 0.057, 0.034, 0.017 m |
| every segment of mullion **4** (released) | ≤ **0.024 m** |
| every segment of mullion **6** (released) | ≤ **0.026 m** |
| **every one of the twelve released transom bodies** | ≤ **0.089 m** |

Mullion 5 has **eight** segments. Two leave. **Six stay, and so do all three
transoms, at every level, in every bay.** "Shedding two segments" is a
statement about 2 of 8 and it was being read as a statement about the member.

At the closing frame the wound is 57.7 × 77.8 px for the bridged aperture and
the scale is **12.96 px/m**, so 89 mm of transom travel is **1.2 px**. Applying
the bake faithfully changes about **20 px of roughly 4,500**. This was
predicted in `sim/out/eastframe_prediction.json` before the after-render was
queued, and the render agrees.

**So the sim and the film do disagree about the transoms, and the disagreement
is the opposite way round from the one in the brief:** `build_breach_sim.py`
does model them as active bodies that can shed, and the solver's answer is that
they do not.

---

## R2-268 — the head restraint is 97× the load it carries, across a joint the interface records as an expansion gap

Why six segments of mullion 5 stay up with nothing under them:

```python
add_constraint("CON_MUL%02d_HEAD" % uid, segs[-1], head, C_con,
               thresh=args.t_mullion_joint * 0.5, loc=(xf1, y, z1))
```

`t_mullion_joint` is 40, so the threshold is **20**. In Bullet's units at
240 Hz × 8 substeps that is **20 × 1920 = 38.4 kN** sustained (R2-092's own
conversion). What it is holding:

| | |
|---|---|
| mullion 5 above z 1.55 — 4.650 m × 4.7 kg/m | 21.9 kg → **215 N** |
| half of the six transom stubs in bays 4 and 5 — 6 × 6.16 kg | 18.5 kg → **181 N** |
| **total** | **396 N** |
| **ratio** | **97×** — and **179×** against the mullion alone |

And the joint it is applied to is one the wall interface itself says carries
nothing: `world/items/…_interface.json` records `head_expansion_gap_m` for
**every** station, **0.0172 m at mullion 5**. A stick curtain wall is
**bottom-anchored**; the head is a movement joint whose whole purpose is to let
the mullion grow and shrink without loading it. The sim bolts 38.4 kN across
it.

**This is the one parameter that decides whether the aperture reads**, and it is
not a threshold anybody tuned — it is `mullion_joint × 0.5`, inherited from the
segment-to-segment joint, applied to a joint of a completely different kind.

**Recipe for the re-bake** (`sim/build_breach_sim.py`, one call site): make the
head a `GENERIC` constraint with the vertical axis free — `add_constraint`
already takes `kind=` and a `post=` hook onto the `rigid_body_constraint` — or,
if a FIXED joint is kept, set its threshold from the dead load rather than from
the joint threshold. Predicted outcome: mullion 5's remaining 4.67 m falls, and
the six transom stubs bolted into it in bays 4 and 5 go with it.

---

## R2-269 — the film's transoms are 250 mm from the ones that were simulated, and the 250 mm is the whole answer

| | z of the three transoms |
|---|---|
| round 1 `GW_Right_Transom_0/1/2` — **what renders** | **1.350 / 2.850 / 4.350** |
| `wall_iface transom_landings` — **what was simulated** | **1.600 / 3.100 / 4.600** |

Now put that beside R2-267's segment boundaries. Mullion 5 is cut into eighths
of 0.7757 m, and the segments that leave are `S00` (z 0.000 – 0.775) and `S01`
(**0.775 – 1.551**).

> **Round 1's transom 0 sits at z 1.3125 – 1.3875 — entirely inside `S01`, the
> segment the bake threw 4.74 m. The sim put its transom at 1.600, inside `S02`,
> which stayed. The transom that survives in the bake is bolted to a piece of
> mullion that is still there; the transom that renders is bolted to a piece of
> mullion that is four metres away on the apron.**

That is not a rounding difference, it is the difference between a supported
member and an unsupported one, and it has never been simulated either way. The
two geometries must be made to agree before the frame's behaviour means
anything — either the sim is rebuilt at round 1's landings, or the frame is
supplied at the interface's (see R2-270, which is the same choice).

---

## R2-270 — round 1's east frame stands 80 mm east of the plane the section calls outermost

| | x |
|---|---|
| round 1 `GW_Right_Mull_*`, `GW_Right_Transom_*`, `Sill`, `Head` | **14.920 … 15.080** |
| `wall_iface` / `mullion_intact.section()` | **14.840 … 15.000** |

`fracture_wall.json`'s own section note: *"x = 15.000 is the OUTERMOST surface
of the wall (the cover cap face). **Nothing in this assembly is east of it.**"*
Round 1's cap face is at **15.080**, and the applier has been supplying glass at
14.955/14.9665 into a frame 80 mm out of position ever since R3 moved it.

**Not fixed, deliberately, and this is the one judgement call in the job.**
Supplying the frame at the interface position would move **every** mullion 80 mm
and **every** transom 250 mm across the whole east elevation — the elevation
beat 1 looks at for 33 s from 1.6 m, where 250 mm is **583 px**. That is a large
change to a shipped beat, it is not what R6 was asked to fix, and it would
destroy the negative control that makes the rest of this work checkable.

So `sim/eastframe.py` cuts the replacement from **round 1's own box, at round
1's coordinates**, and merely partitions it. Consequences, all measured:

* six of the ten bays keep round 1's vertices exactly and must be
  **pixel-identical** between the two builds — R2-150's free negative control,
  obtained here from the fix's own blast radius rather than from an occluder;
* the flying pieces follow the bake's rigid motion about the **sim** body's
  centre, so a round 1 piece lands within the 80 mm the two sections differ by:
  for a 0.775 m bar thrown 4.7 m onto an apron, the last significant figure.

**Somebody has to choose**, and the choice is between beat 1's composition and
the section's own declared rule. It should be made looking at a beat-1 frame.

---

## R2-271 — R5's refusal was true, was specific, was overridden on every apply, and named the three objects

`sim/out/apply_film9.json`, `apply_film13.json`, `apply_film14.json` all carry:

```
glazing_pocket_clear  FAIL
pocket_intruders_in_the_clear_opening: [... GW_Right_Transom_0, _1, _2 ...]
```

and `sim/land_breach.sh` said, in as many words:

> *"NOTE: R5 will refuse. The refusal is TRUE and it is about ROUND ONE's frame
> — three transoms across the bays at z 1.35/2.85/4.35 — not about the glass
> being restored. **That is R6 and the geometry is not ours.**"*

**The check had already found the defect, written down the exact object names,
and been correctly explained — and then routed to a requirement that nobody
owned.** Every apply since has passed `--force` over it. R2-125 built the
triangle-vs-box test *specifically* because a vertex test could not see these
three bars, and the thing it was built to see was then classified as somebody
else's problem.

`apply_breach` now runs R5 **again on the scene it is about to write** and
reports the intruders classified by whether they cross the wound. Over the
wound: **3 → 0**. What is left is the south wall's frame, two light fins, and
this module's own transom remainder over the six bays that keep their glass —
all deliberate, none of them across the hole. `land_breach.sh`'s note is
rewritten.

---

## R2-272 — my own first classifier would have reported "0 intruders" while three of my objects lay in the pocket

Self-caught before it shipped, and recorded because it is R2-124's shape in a
fresh coat of paint. The first version of the post-build R5 report filtered on
the name:

```python
east_intr = [x for x in intruders if str(x[0]).startswith("GW_Right")]
```

`BF_TRN0_STATIC` is the same aluminium in the same pocket and does not start
with `GW_Right`, so the line would have printed **"0 east-wall intruders"** with
three of this module's own objects standing in the glazing pocket.

**And the obvious repair is also wrong.** Classifying by world AABB fails in
*both* directions here: `BF_TRN*_STATIC` is one mesh holding **two** boxes
(y −10.919…−4.3625 and 4.3625…11.0), so its bounding box spans the gap between
them and would report it standing in a hole it is nowhere near; round 1's single
21.9 m transom really does cross the wound and its eight vertices are eleven
metres away at the ends. The classifier now asks the same question R5 asks —
triangles against the box by the separating-axis theorem — restricted to bays 4
and 5's clear openings.

---

## R2-273 — the demonstrator: what 2h25m of re-bake buys, priced with a picture instead of an argument

*(fill from `render/r6_demo/` — see the report)*

---

## R2-274 — "the wound is not darker" was right, and the mean is the wrong statistic for it

The standing measurement of the closing frame is that the wound is **not** darker
than adjacent glass — **+0.066** against the left neighbour, **−0.124** against
the right — *"because the wall is transmissive on both sides, so 'hole' versus
'glass' is not a radiance difference at all."* Reproduced independently here on
the delivered f2978 at 4K: wound 0.4142 mean luminance, left neighbour 0.4018,
right neighbour 0.5643.

That diagnosis is correct and it is also the reason the mean can never settle
the question. **What tells a viewer there is a wall is not the glass, it is the
lattice** — at 595 m the only thing rendering the east elevation is a grid of
1 px aluminium lines, and a bay whose glass has gone still has all of them.

So `sim/wallstats.py` measures `grid_contrast`: the amplitude of the transom
lines against a **local** baseline three to five pixels above and below, over
each region's own y span, at the three heights the camera track puts the
transoms at. Two details that are not decoration:

* **local** baseline, because the closing shot has a strong vertical brightness
  gradient across the wall (the lit floor and the plinth are behind its lower
  half) and a baseline half a metre away measures that instead;
* **absolute** value, because round 1's transoms read ~0.2 *darker* than the
  interior seen through the wound and *lighter* than the crazed glass in some
  retained bays. A signed contrast cancels across the wall and reports a lattice
  that is plainly there as nearly zero — R2-181's mistake, where a welded slab's
  mean normal cancelled and the detector reported nothing.

Measured on the delivered f2978: the wound's lattice is **as loud as everybody
else's** (0.037 against 0.037 / 0.068 for its two neighbours and 0.053 / 0.044
for the two untouched groups of three bays). **That equality is the defect,
stated as a number.**
