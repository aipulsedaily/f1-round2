# Staged for the defect log's owner — R2-148 to R2-152

Kept out of `docs/DEFECT-LOG-R2.md` deliberately: that file has one owner, to keep
the numbering collision-free. My block is R2-148 to R2-155 and I have used five of
it. Paste or renumber as you see fit.

All of this is the same job: **landing R2-132's `build_architecture` fix in an
artefact**, which is R2-071's rule — *a source fix has a build artefact downstream
of it, and the fix is not landed until that artefact has been rebuilt and re-read.*

---

## R2-148 — assembly9: one object of 28,781 moved, and for the first time it was a vertex COUNT

`world/build_architecture.py` was fixed at `54dd6b8` (22:06). `assembly8` was built
at **19:38**. R2-132's own closing line says it: *"A WORLD REBUILD IS OWED. Nothing
here has moved a vertex in assembly8."* `film12` and `film13` were both built on the
defective world. This is that rebuild, read back from the file.

| | assembly8 | assembly9 |
|---|---|---|
| objects | 28,781 | 28,781 |
| total verts | 1,282,465,803 | **1,282,477,674** (+11,871) |
| objects moved | — | **1** |
| bit-identical | — | 28,780 |
| different vertex COUNT | — | **1** |
| materials moved | — | **0 of 132** |

`ARCH_Paving_ApronPlatform`: **128,722 → 140,593 verts (+9.222 %)**. Five of its six
bbox extremes are **bit-identical**; the sixth, `bbox y max`, moved **46.8 mm**.
`apron_platform_m2` **5881.5 → 6421.2**, reproducing R2-132's test-build figure
exactly in the full assembly.

**a5→a6, a6→a7 and a7→a8 all held 1,282,465,803 vertices to the digit.** This is the
first assembly diff in this project where the count moves at all, because the fix
does not *shift* a slab — it *lays* one.

**The prediction was written at 22:48 while `build_architecture` was still building**
(`v124/PREDICTION.md`), and one part of it is wrong. It predicted the bbox would
extend outboard. **It does not**: the slab grew entirely inside its own envelope and
the one extreme that moved went *inward*. The apron sweep curves, so its bounding box
was already set by the stations where `platform_edge` is widest, and the released
ground fills in behind that line. **Direction of the finding right, stated shape of it
wrong, and it is recorded as wrong rather than quietly dropped.**

The half that was *not* obvious and had to be checked rather than assumed:
`build_terrain` and `build_dressing` run **after** `build_architecture`, so "they were
not edited" is not sufficient on its own. Every `ray_cast` in `build_terrain` is inside
`test_scene()`, `selftest()` or `bake_cameras()` and **none is reachable from
`build()`**; `build_dressing` has none; `embed_ground_contacts` and `cull_unowned` both
query `world_ground_z` (the model) and never the apron mesh; and every builder in
`build()` takes its own freshly seeded `random.Random(20NN)`, so a bigger grid
consuming more draws cannot perturb what follows it. All four held.

**`build_architecture`'s own contract gate goes 2 failures → 1.** BLACK recesses
5 → 1; *"no ARCH mesh coplanar with another module on the Beat-4 route"* **FAIL (2
samples, both `ARCH_Paving_ApronPlatform`) → PASS (0)**. And *"paving stays inside the
contract's declared rectangles"* goes 35,474 → **40,184** up-faces with **0 outside**,
which is the row that says the fix did not spill the way its first version did.

`fp_diff.py` was run with four controls in one batch: its own 7-arm `--selftest`, the
a5→a6 pair where `BR_Transit_NorthWall` is known to have moved 3.1885 m (reports 1,
3.1885 m), and a **negative arm that declares `--expect-moved 0` on this pair and must
exit 1** — it does. R2-111 repaired this file because it computed `moved`, printed it
and never consulted it; the expectation is now declared on the command line.

---

## R2-149 — film14 on assembly9: 37 of 37 readback fields identical, and the camera is byte-identical

The full chain was re-run in order — `author_beats2_5.py` → `build_camera_rig.py` →
`build_film_scene.py` — with **no `--world-override`**; `SHIPPING.md` was updated to
declare assembly9 first, so `refuse_unless_world_is_declared()` is satisfied honestly.
Both world guards printed clean: *"WORLD: assembly9.blend, the ship declared in
SHIPPING.md"* and *"WORLD STALENESS: none"*.

**Two nulls, and they are what make the pixel comparison below a world comparison:**

* `docs/beat_sheet.json` sha `2ee973b8` **before and after** the author pass — it is
  idempotent, as r2100 and r2127 both measured.
* `world/camera_rig_path.json` sha `f1c65c46` before and after the rig build, and
  `render/film14_path.json` is **the same sha as `render/film13_path.json`**. The
  camera is byte-identical across the two films. **The only thing that differs between
  film13 and film14 is the world.**

| readback, from the saved blend | film9 (broken) | film13 | **film14** |
|---|---|---|---|
| interior lamp load | 3,737.113 W | 46,203.313 W | **46,203.313 W** |
| `_sl_base` lamp stamps | 0 | 23 | **23** |
| `scene_mark` | null | 3.628 | **3.628** |
| `assert_levelled` | REFUSED | PASS | **PASS** |

`readback_diff.py`: **37 fields compared, 37 identical, 0 differ.**

The levelling identity **recomputed from film14's own `_sl_base` properties**, not
quoted: base 3,737.113 × 2^3.628 = 46,203.306 against **46,203.313** measured,
residual **0.007 W**, worst per-lamp ratio (`WallWash_BackUp`) 12.363369363 against
12.363368794 — nine decimals, so no lamp hid inside the total. Deck top 0.3400, floor
top 0.0000, frames 1–2978 @ 24, scale 1.0, 28 Vitrines / 0 parented to `CAR_ROOT`,
camera `ONER` clip 0.05 / 200000, exposure −3.628 AgX.

**Gates, each with both controls:**

| gate | artefact | control |
|---|---|---|
| `horizon_gate --selftest` | 7/7 | includes P4, the 170°-rolled synthetic |
| `horizon_gate` f2600–2714 | **1.71° worst, 0 FAIL, 0 WARN, 0 inverted** | pre-R2112 path **FAIL**, −122.93°, 28 inverted, 32 FAIL frames |
| `horizon_gate --census` | bounds lie strictly between 2.48° and 122.93° | — |
| `seam_gate --selftest` | **7/7** on the repaired default `world/camera_rig_path.json` | three must-fail arms |
| `seam_gate` artefact | chord **2.0893**, speed **1.2727**, look **13.2504**, lens **−0.051**, SEAM_OK | — |
| `socket_index_audit --blend` | film14 **PASS**, 226 trees | film10 **FAIL, 27 findings**; film13 PASS |
| `campath_gate` | **PASS, 0 FAIL, 5 advisory** | see R2-151 |

**R2-103's floor was paid attention to rather than re-derived.** `path_diff.py` run on
`film14_path.json` **against itself** reports **1,429 of 2,978 frames "MOVED"** and
0.2032° of rotation. The strict componentwise comparison on the same self-null reports
**0**. Only then was film13 → film14 compared: **0 / 2978 position, 0 / 2978 rotation,
0 / 2978 lens.**

---

## R2-150 — THE PIT-EXIT REPAIR READS ON SCREEN, and it is not subtle

R2-133 left this open and named it the commercially important half: *"A 390 m² hole
nobody can see from the only camera that exists is a different priority from one that
reads on screen, and nobody yet knows which this is."*

**It reads.** f1104 rendered from film13 (defective world) and film14 (fixed world),
`ONER`, 3840×2160, 256 samples, same farm, same settings, **byte-identical camera**.

**THE CONTROL IS A REPEAT RENDER OF THE SAME SCENE, and without it none of the
numbers below mean anything.** Two Cycles renders do not have to agree, so "5 % of the
frame changed" is not a finding until you know what 0 % looks like:

    film13 vs film13 RENDERED AGAIN     4.85 % of pixels differ at all
                                        0.00 % differ by more than 2/255
                                        mean |delta| 0.048, MAXIMUM 3/255

| region | px | film13→film14 >8/255 | repeat-render floor | mean \|Δ\| signal / floor |
|---|---|---|---|---|
| **VOID** — declared, owned, never laid | 12,490 | **34.57 %** | **0.00 %** | **17.578 / 0.054** |
| CTL_PAVED — track asphalt, built in BOTH | 5,066 | **0.00 %** | 0.00 % | 0.304 / 0.050 |
| CTL_SKY — top 8 % of frame | 660,480 | **0.00 %** | 0.00 % | 0.295 / 0.054 |
| whole frame | 8,294,400 | 5.29 % | 0.00 % | 3.005 / 0.048 |

The void region's mean RGB goes **(99.1, 88.2, 74.9) → (116.6, 103.3, 86.6)** — it
lightens, because a lit concrete apron is now there. In the frame's lower-left sixth
the change is **99.72 % of pixels over 8/255, mean |Δ| 59.8, against a floor of
0.035**. That is a factor of **1,710**.

**34.57 % is a LOWER bound.** It is the fraction of *all* in-frustum void pixels, and
R2-140 measured that the pit building shell hides 854 of 1,200 of them. The occluded
ones correctly do not move. Of the ~45 % that are unoccluded, essentially all of them
do.

Two things worth keeping separate. **R2-133 was right about its own question and
wrong about nothing** — its crops were of a different render at a different resolution
and it declined to turn "no hole visible at 18.7°" into a waiver, which was the correct
call. What settles the matter is not a better crop, it is **an A/B with a
reproducibility floor under it**, which nobody had until both worlds existed.

And: **f1104 is the ONER's *shallowest* view of the region** (line of sight 16.8–34.2°,
against −45.9° at the never-rendered f1119). The most favourable frame available was
also the least favourable geometry, and it still reads.

---

## R2-151 — `campath_gate`'s positive control passes, because the gate has no roll term at all

Running the control is the only reason this is known. `docs/horizon_pre_R2112_path.json`
— the path with **28 fully inverted frames and −122.93° of roll**, which `horizon_gate`
fails with 32 FAIL frames — goes through `campath_gate` and returns:

    >> STAGE RESULT: PASS — 0 FAIL, 5 advisory

**the same verdict, and the same five advisories, as film14.** `campath_gate` measures
speed, rotation RATE as a fraction of frame width, and path kink. **It has no roll or
up-vector term**, so a camera that is upside-down for 28 frames is invisible to it.

That is consistent with R2-088 — `horizon_gate` exists *because* nothing measured roll
— but the consequence is specific and was being missed: **a `campath_gate` PASS
reported next to that path as its "positive control" asserts nothing.** Two paths that
DO discriminate, and either should be used instead:

    docs/seam_pre_R2064_path.json   FAIL — 1 FAIL, 6 advisory  (C1_rotation_smear
                                    51 % of frame width/frame at f1461)
    render/film9_path.json          FAIL — 2 FAIL, 12 advisory

---

## R2-152 — `54dd6b8`'s own commit message quotes grid numbers that do not reproduce in the assembly

Small, and exactly the shape this log keeps recording. The fix's comment and commit
message both say a `max(platform_edge) + 3` grid *"would silently truncate the slab at
u ~ 23.9 while the declared apron runs to u ~ 40.4"*. In the full assembly the module
prints:

    [apron] grid u 6.05 .. 47.55  (platform_edge max 40.56; the declared
                                   platform reaches 44.55)

so the two numbers are **43.56 and 44.55**, not 23.9 and 40.4. The fix is right and
its area figures reproduce to the decimal (5881.5 → 6421.2 m²); the *grid* figures
were measured on `work/r2132/arch_base.blend`, a module-standalone test build, and
carried into the source comment as though they described the assembly. **A number
measured on a test rig and written into a comment about the shipping build is the
same defect as a probe window that stops inside the thing it measures** — which is
R2-132 itself.
