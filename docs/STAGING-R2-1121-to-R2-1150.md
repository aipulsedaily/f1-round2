# STAGING R2-1121 to R2-1150

Owner: the bays 3/6 look call. Staged here for `DEFECT-LOG-R2.md`, which I do
not edit.

---

## R2-1121 — BAYS 3 AND 6 STAY. The relabel was NOT free, and that is the finding.

`slabcheck` exited 1 because bays 3 and 6 are role `destroyed` and read
`DID_NOT_MOVE` (0.9 % and 9.0 % vacated by area). The blocker was framed as a
free choice: **(a)** relabel them `retained`, costing nothing, or **(b)** make
them leave, costing a re-bake.

**(a) as stated is not free.** Measured, both plans built from the same seed:

| bay | shipped rule | shards | flipped rule (`bent_stub` retains) | shards | geometry |
| --- | --- | --- | --- | --- | --- |
| 0,1,8,9 | intact | 1 | intact | 1 | byte-identical |
| 2 | retained | 195 | retained | 195 | byte-identical |
| **3** | destroyed | **202** | retained | **198** | **every polygon different** |
| 4 | destroyed | 1531 | destroyed | 1531 | byte-identical |
| 5 | destroyed | 1485 | destroyed | 1485 | byte-identical |
| **6** | destroyed | **200** | retained | **178** | **every polygon different** |
| 7 | retained | 183 | retained | 183 | byte-identical |

`fracture_pane` reads `pane.role` to pick `n_radial` — **15 radials for
`destroyed`, 7 for `retained`** (`sim/fracture.py:764`). Relabelling a bay
re-fractures it. Different polygons mean different `GS_bNN_NNNNN` names, which
means the 20 MB bake table no longer addresses the shards, which means a
**re-bake — the same bill as (b)**.

**One word was doing two jobs.** `role` is a *fracture-density input*; the gate
read it as an *outcome assertion*. Bays 3 and 6 are `destroyed` **and** stay,
and both are true: they are next to the strike so they are radialled hard, and
they each keep a jamb so they do not go. No single word could carry that, and
R2-1049 is what happens when one is asked to.

So the fix is to separate the two facts, and *then* (a) is free.

### The decision: bays 3 and 6 STAY

Taken at 4K/1:1 on the shipping camera, not from the 720p read in R2-1080.

**Provenance of every frame used, stated up front:**

| evidence | frame | build | rendered |
| --- | --- | --- | --- |
| `out2/seq/b129_ctrl/b129_ctrl_000880.png` | f880 | `film16_breach.blend`, 3840x2160 / 512 spp | 08-07 07:29 |
| `out2/seq/r21121_wound4k/` | f866/868/870/872/876 | **`film17_breach.blend`** (the served blend), 3840x2160 / 512 spp | this task |
| `out2/seq/r2full/` | f860–f890 | 720p, 08-04/05 | framing only — a 720p frame cannot resolve a crack |

`render/film16_path.json` and `render/film17_path.json` are **the same camera
through this whole window.** Over f855–f959, position and focal length are
**bit-identical on every frame** (worst 0.000000 m, 0.000000 mm); the only
difference anywhere is a **1e-6 quaternion component**, which is the file's
6-decimal rounding. The breach bake is the same `sim/out/breach_film.npz` in
both. So f880 from film16 is valid evidence about film17's *glass*; the
film16→17 changes are elsewhere in the take.

**The one build change that could still overturn this is `--fracture-faces`
(breach frost), which is in no film and is off by default.** It can only make
the fracture network *more* visible — `out2/6a119c8a3e07.png` shows frosted
glass rendering bright white — so it cannot flip "reads as cracked glass" into
"reads as a flat sheet". It is not a reason to hold the decision.

### What the 4K actually shows

Bay 3 at f880 is 1.6 m from the lens at **1,524 px/m** — a 25 cm shard is
**381 px**. This is the largest and closest the standing glass is ever filmed.

It reads as **cracked laminated glass**. The fracture network renders as fine
bright hairlines where the 0.6 mm chamfered arris catches the sun, and as thin
dark seams against the sky. The pane stays continuous across them: no gaps, no
parallax step, no separated slabs.

Ground truth was projected from the bake and drawn over the 4K frame; the
outlines land exactly on the visible hairlines, so what is being judged is
bay 3's own fracture and not something in front of it. Measured, with a
negative control — the *same* network rotated 37° about the pane centre, so it
samples the same picture in the same places along lines that are not cracks:

| f880, ±8 px perpendicular profiles | n | median &#124;ΔL&#124; | frac SNR > 3 |
| --- | --- | --- | --- |
| 4K, bay 3's real crack network | 681 | **0.0150** | 29 % |
| 4K, −ve control (rotated 37°) | 745 | 0.0077 | 10 % |
| 720p, bay 3's real crack network | 569 | 0.0387 | 50 % |
| 720p, −ve control (rotated 37°) | 626 | 0.0116 | 13 % |

**Read this honestly: it establishes that the network renders, and it does NOT
establish that 4K was needed.** Real cracks separate from fake ones by 1.95×
in amplitude at 4K and 3.33× at 720p — the *per-edge* separation is if anything
stronger at 720p, because a downscale packs the same step into fewer pixels.
The thing 720p cannot settle is not whether there is a step; it is whether the
polygons are **cells of one sheet or separate hard-edged quads**, which is a
spatial-coherence judgement about glass continuity *across* each seam. That is
why R2-1080 was right to refuse to call it, and why this had to be looked at
rather than measured. What the 4K adds is that a 25 cm cell spanning ~380 px
shows unbroken glass across its seams, with the scene behind refracting
continuously through it.

Two supporting facts about the frame itself:

* `tools/peep.py stats` over bay 3's half of the 4K frame: mean 0.489,
  **clipped 0.00000, crushed 0.00000**, sat 0.106. Nothing is crushed or
  lifted; this is a valid delivery-grade image to judge on.
* `sharp(varLap)` is **0.63e-4 over bay 3's half against 2.91e-4 over the
  aperture half** — the standing pane is 4.6× softer than the hole, because it
  is a near foreground under the shot's own DOF and motion blur. A pane that is
  the softest thing in frame is not going to read as hard-edged slabs.

### The physical case, which is stronger than the look case

**Nothing in the delivered bake could make bays 3 and 6 leave.** Measured on
`sim/out/breach_film.npz`, median segment travel over f858–f1165:

| mullion | declared `beat3` | segments | last &#124;disp&#124; | max any segment |
| --- | --- | --- | --- | --- |
| 3 | bent_stub | 8 | 0.000 m | **0.000 m** |
| 4 | destroyed | 8 | 0.000 m | **0.023 m** |
| 5 | destroyed | 8 | 0.000 m | **4.742 m** |
| 6 | destroyed | 8 | 0.000 m | **0.026 m** |
| 7 | bent_stub | 8 | 0.000 m | **0.000 m** |

**Only `MUL05_S00` and `MUL05_S01` leave** — 3.93 m and 4.43 m, the two
segments below z ≈ 1.59. `MUL05_S02` peaks at **0.145 m**, which is the
`BF_MUL05_S02 = 0.1449 m` guard in the verification bar: this is the right bake.

So bays 3 and 6 have **both jambs standing** in the delivered take, and neither
was struck — the car's impactors span y −1.085…+1.085, which is bays 4 and 5.
There is no mechanism by which those panes could go. Option (b) is not "make
two panes leave"; it is "destroy the frame the aperture is currently framed
by" — mullions 4 and 6 are what make the hole 4.35 m and not 8.77 m.

### The picture stake is smaller than it looks — bay 6's especially

Shards actually on screen, and the clipped footprint of each pane in the 4K
frame (both bays fall out of frame; the swap is f860):

| frame | bay 3 shards / px wide / % of frame | bay 6 shards / px wide / % of frame |
| --- | --- | --- |
| f860 | 6 / 53 / 0.4 % | 123 / 442 / 5.9 % |
| f864 | 69 / 1145 / 26.2 % | 121 / 790 / **7.3 %** |
| f866 | 77 / 1419 / 35.4 % | 119 / 599 / **8.2 %** ← bay 6's peak |
| f870 | 74 / 1627 / 45.1 % | 50 / 222 / 3.4 % |
| f874 | 62 / 1708 / 50.1 % | **0 / 0 / 0 %** |
| f880 | 55 / 1759 / **52.1 %** | 0 |
| f894 | 11 / 1377 / 42.4 % | 0 |

**Bay 3 is half the 4K frame for twenty frames.** **Bay 6's entire life as
broken glass is f860–f872 — 13 frames, 0.54 s — never exceeding 8.2 % of frame,
foreshortened at a grazing angle in the left corner.** Re-baking the wall to
change what bay 6 does would buy nothing anyone will see. Bay 3 is where the
whole stake is, and bay 3 is the one that reads well.

Afterwards there is nothing to see either way: bay 3 returns at f1016–1051 at
25–34 m (25 cm = 25–33 px), and every later run — including the closing
re-frame of the wound at f2834–2978 — is at **190–950 m, where a 25 cm shard is
0.8–5.8 px**.

**The closing re-frame of the wound (f2834–2978) is at 506–595 m**, where a
25 cm shard is 1.0–3.3 px. Nothing about this decision survives to beat 6.

### The change

`sim/fracture.py` — new section 4b, `outcome_of()` / `bay_outcomes()`. The
plan's claim about what a bay *does*, derived from the wall spec's own `beat3`
mullion states and **not from the bake the gate is checking**. The rule is a
statement about laminated glass: a pane is captured on four edges — head, sill,
two jambs — and it goes when **both jambs go**. A `bent_stub` is a jamb that
deformed and stayed. `Pane.role` is untouched and now carries a comment saying
what it is.

`sim/slabcheck.py` — `ROLE_REQUIRES` → `OUTCOME_REQUIRES`, keyed on
`LEAVES`/`STAYS`. `run()` reports `outcome`, `fracture_role` and `role`
side by side so nobody re-conflates them, and raises if the shard plan carries a
bay the wall spec does not declare. The failure line now reads
`BAY n IS DECLARED X AND READS Y`.

**No geometry changed. No bake changed. `fracture_wall.npz` and
`breach_film.npz` are untouched.**

```
STAGE RESULT: slabcheck PASS {"2":"DID_NOT_MOVE","3":"DID_NOT_MOVE",
                              "4":"LEAVES","5":"LEAVES",
                              "6":"DID_NOT_MOVE","7":"DID_NOT_MOVE"}       exit 0
```

| bay | outcome | fracture_role | verdict | vacated by area | peak net | align at end |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | STAYS | retained | DID_NOT_MOVE | 1.6 % | 27.4 mm | 0.09° |
| 3 | STAYS | **destroyed** | DID_NOT_MOVE | 0.9 % | 14.8 mm | 0.11° |
| 4 | LEAVES | destroyed | LEAVES | 96.8 % | 4989.3 mm | 46.56° |
| 5 | LEAVES | destroyed | LEAVES | 95.4 % | 2809.6 mm | 83.51° |
| 6 | STAYS | **destroyed** | DID_NOT_MOVE | 9.0 % | 32.6 mm | 0.13° |
| 7 | STAYS | retained | DID_NOT_MOVE | 3.6 % | 26.1 mm | 0.18° |

Bays 3 and 6 sit with bays 2 and 7 on every column that describes motion, and
apart from them on the one column that describes fracture. That is the whole
finding, and the table now says it.

### Controls: 16 → 22, all green, 1.6 s

The ten measurement controls and the six R2-1049 adjudicator controls are
unchanged in substance (renamed to the outcome vocabulary). Six new ones:

```
OUT_BOTH_JAMBS_GONE   destroyed|destroyed -> LEAVES
OUT_ONE_JAMB_BENT     destroyed|bent_stub -> STAYS   -- a stub is a jamb
OUT_ONE_JAMB_INTACT   destroyed|intact    -> STAYS
OUT_UNTOUCHED         intact|intact       -> INTACT, and INTACT is never judged
OUT_NOT_ROLE          +ve control: the shipping plan's roles do NOT map onto
                      the wall's declared outcomes -- they differ on exactly
                      bays [3, 6].  If a future edit collapses the two words
                      back into one, this fires.
OUT_ROLE_IS_DENSITY   the STAYS bays 3/6 still carry 202/200 shards against
                      retained 2/7's 195/183 -- the reason the relabel was not
                      free, pinned as a control.
```

`OUT_NOT_ROLE` is the control that would have caught R2-1049 on the day the
wall was declared, and it costs nothing: it reads the shipped `.npz`, no bake.

### Cost

$0.14 of GPU, five 4K frames on broker 2's existing instance with
`film17_breach.blend` already resident — no 8 GB transfer, submitted at
`--prio 120`, strictly behind the beat-1 proxy (90) and the queued beat-5 job
(110). Nothing was jumped and nothing was disturbed.

---

## R2-1123 — `land_breach.sh` STAGE 3 NOW GATES. It never has.

The verification bar says **"slabcheck MUST exit 0"**. Its only caller was:

```sh
$PY sim/slabcheck.py --film sim/out/breach_film.npz \
    --out sim/out/slab_NEW.json 2>&1 | tail -3
```

`set -u` is on; `pipefail` is not. **The pipeline's status is `tail`'s**, and
there is no `|| die`. So slabcheck's exit code was discarded, and stage 3 could
print `STAGE RESULT: slabcheck FAIL` and the script would carry straight on to
3b. The script's own comment at 3b said so and nobody closed it — which means
**R2-1049 taught the tool to fail and did not give the failure anywhere to
land.** Two of this project's recurring shapes at once: a gate that only prints,
and a `STAGE RESULT: FAIL` line that is not the last one anybody reads.

Now:

```sh
$PY sim/slabcheck.py --film sim/out/breach_film.npz \
    --out sim/out/slab_NEW.json > sim/tmp/slab_stage.txt 2>&1 \
    || { tail -3 sim/tmp/slab_stage.txt; die "slabcheck"; }
tail -3 sim/tmp/slab_stage.txt
```

Exercised both ways, because a gate nobody has seen fail is not a gate:

| | exit | stdout | reaches 3b |
| --- | --- | --- | --- |
| real slabcheck | 0 | `STAGE RESULT: slabcheck PASS {…}` | **yes** |
| +ve control, a stage that exits 1 | **1** | `STAGE RESULT: FAIL -- slabcheck` | **no** |

Note this does **not** make `land_breach.sh` safe to run end to end — NEXT-REBUILD
order-constraint 5 still stands, and stage 1 can still swap in the wrong raw
bake. It makes stage 3 honest.

---

## R2-1122 — MULLIONS 4 AND 6 ARE DECLARED `destroyed` AND DO NOT MOVE. Same defect, not raised.

Not in scope for the bays and **not fixed** — changing a mullion's `beat3`
state changes `active` and the constraint thresholds in `build_breach_sim`
(`sim/build_breach_sim.py:774,825`), so it is a re-bake and must not be done
casually. Logged because it is the identical shape one level up.

The wall declares mullions **4, 5 and 6 `destroyed`**. The bake delivers **one**:
mullion 5, and only its two lowest segments. Mullions 4 and 6 peak at 23 mm and
26 mm and return to 0.000 m.

**The picture is right and the label is wrong, in that order.** Mullions 4 and 6
standing full height are exactly what frames the aperture at 4.35 m at car
height instead of letting it open toward `aperture.CEILING`'s 8.77 m, and
R2-092's connected-hole figures already measure the real thing. Nothing needs
to change in the take. What needs to change, before some future gate joins
mullion `beat3` to mullion travel the way `slabcheck` now joins bay outcome to
bay verdict, is the **declaration** — and that is a re-bake, so it belongs to
whoever next has a reason to re-bake, not to this task.

The general rule, third instance now: **a plan is not evidence that the plan
happened.** `slabcheck` is the only gate in the breach that joins a declaration
to an outcome. Everything else in `wall()['breach_state']` is still an
assertion nobody has checked.

---

## R2-1124 — `fracture.py --selftest` has TWO RED CONTROLS at HEAD. Pre-existing, unowned.

Found while confirming my edit changed nothing. **Not caused by this task and
not fixed**, but it is failing right now and nothing in the pipeline runs it.

```
no shard's hull stands >3 mm proud of it       FAIL  worst 0.00325 m over 2756 shards
no shard exceeds 3x its own local target area  FAIL  worst 5.78x over 2756 shards
2 check(s) FAILED
```

Verified identical when run from `git show HEAD:sim/fracture.py` — same
0.00325 m, same 5.78x, same 2,756 shards. **My change to `fracture.py` is one
comment replaced and one new section appended; it touches no geometry code**
(`git diff` removes exactly three comment lines).

Both are near-misses on a tolerance, not blow-outs: 3.25 mm against a 3.00 mm
bound is 8 % over, and the 5.78x outlier is one shard the splitter gave up on —
the exact failure the second control's own comment says "the picture caught one
that every other number let through". Neither is in the shipping wall's numbers
(`build_wall_plan` is a different seed set from the selftest's single 4242
pane). **Whoever next re-bakes should look at this first**, because fixing
either one changes shard geometry and therefore costs a re-bake anyway — so it
is free to fix *then* and expensive to fix at any other time.
