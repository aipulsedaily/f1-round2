# What assembly9 must differ from assembly8 in — WRITTEN BEFORE THE DIFF RAN

Recorded 2026-08-03 22:48, while `build_architecture` was still running (surface
and barriers were done at 105 s; the fingerprint pass has not been started).
Same discipline as `v123/PREDICTION.md`, and for the same reason: a diff read
after the fact is a story, a diff read against a written expectation is a
measurement.

## The source delta is exactly two commits, and only one of them can move a vertex

`assembly8.blend` was built 2026-08-03 19:38 at `2806c3c`-era source. Since then
three commits have touched anything the assembler reads:

| commit | file | can it move a vertex? |
|---|---|---|
| `54dd6b8` 22:06 | `world/build_architecture.py` | **YES — this is the point** |
| `412d2e2` 22:42 | `world/world_contract.py` | **NO** |
| `48dfa24` 22:43 | `render/world/assembly/r2/lib_probe.py` | not read by `assemble.py` |

`build_surface.py`, `build_barriers.py`, `build_terrain.py` and
`build_dressing.py` are **byte-identical to the ones assembly8 was built from**
(`build_surface`/`build_barriers` untouched since the baseline commit,
`build_terrain` last touched 09:55, `build_dressing` 18:36 — both before 19:38).

### why `world_contract` cannot move anything

`412d2e2` is +104/−7 and **every changed line is inside `selftest()` or is a
comment**: two `chk(...)` label strings renamed to "nobody DECLARES", the apron
tie window derived instead of typed (R2-141), the `> 0.999` predicate corrected
to `== 1` (R2-142), and a new overlap pin (R2-143). `__version__` is `1.2.1` in
both. `selftest()` is not called by `assemble.py` or by any `build()`. **No
geometric constant, no field function, no rectangle changed.**
**PREDICTION: `assembly9_build.json["contract"] == "1.2.1"`, same as assembly8.**

## What MUST move: `ARCH_Paving_ApronPlatform`, and it is the only object

`54dd6b8` changes two things, both inside the pit-exit apron:

1. `apron_clearance` — `d_out` becomes `inf` where the sample is inside the
   `apron` rectangle **and** inside none of `pit_lane` / `garages` / `paddock`.
   The outboard cut is released only there.
2. `build_apron_platform` — `UMAX` is now `max(platform_edge.max(), the u the
   declared apron rectangle actually reaches) + 3.0` instead of
   `platform_edge.max() + 3.0`.

`build_apron_platform` returns **exactly one object**, `mb.build(...)` on
`MB("ARCH_Paving_ApronPlatform")`. Nothing else in the module calls
`apron_clearance` outside `verify_contract()`, which is a gate and builds no
geometry.

**PREDICTIONS:**

1. **Exactly 1 of 28,781 objects moves, and its name is
   `ARCH_Paving_ApronPlatform`.**
2. That object's **vertex COUNT CHANGES** — it grows from 128,722. This is the
   first assembly diff in this project where a vertex count moves at all; every
   previous one (a5→a6, a6→a7, a7→a8) held 1,282,465,803 verts exactly.
   **So `total_verts` will INCREASE**, and `fp_diff`'s
   "objects with a different vertex COUNT" will read **1, not 0**.
3. The growth is **outboard at the pit exit only**: the bbox should extend in
   the direction of increasing `u` near s 3200–3430, and the bbox in `z` should
   not move at all (the slab is flat at `APRON_Z` with a −0.30 m formation, and
   the fix adds area, not height).
4. **`apron_platform_m2` 5881.5 → 6421.2** in `assembly9_build.json`'s
   architecture summary (the R2-132 test-build figure; the module is
   deterministic, so the full assembly must reproduce it).
5. The build prints a new line `[apron] grid u UMIN .. UMAX`, with UMIN
   unchanged and UMAX ≈ **43.4** (declared apron reaches u ≈ 40.4) where the old
   bound was `max(platform_edge)+3 ≈ 23.9`.

## What MUST NOT move — and this is the half that is actually being tested

`build_terrain` and `build_dressing` run **after** `build_architecture` in
`assemble.py`'s module order, so "they were not edited" is not by itself enough:
they could read the scene. **They do not.**

* `build_terrain`'s four `ray_cast` calls are all inside `test_scene()`,
  `selftest()` and `bake_cameras()` — **none of them is reachable from
  `build()`**. `build_surface`'s single `ray_cast` is inside `verify()`.
* `build_dressing` has **zero** `ray_cast` calls and does not import
  `build_architecture`.
* Inside `build_architecture` itself, the two post-pass operations that *could*
  couple the apron to its neighbours do not: `embed_ground_contacts` tests
  `abs(world_z − APRON_Z) < 4 mm` per object against the **contract model**, and
  `cull_unowned` kills up-faces whose owner from `wgz` (again the model, not the
  mesh) is neither `OWNER_APRON` nor `OWNER_TERRAIN`. Neither reads the apron
  mesh. The new apron faces are themselves `OWNER_APRON`, so `cull_unowned`
  will not eat them.
* **No RNG bleed.** Every builder in `build()` gets its own freshly seeded
  `random.Random(20NN)`; `build_apron_platform` has `random.Random(2011)` to
  itself. Consuming a different number of draws for a bigger grid therefore
  cannot perturb `build_markings`, `build_pit_building` or anything after it.
  *This is the single most likely way this prediction could be wrong, and it is
  the first thing to check if a second ARCH object moves.*

**PREDICTIONS:**

6. **28,780 objects BIT-IDENTICAL.** In particular `TER_Ground`, all 131 `BR_*`,
   all 58 `SURF_*`, all 246 `DR_*`, all 28,314 `VEG_*`, and the other 30
   `ARCH_*` — including `ARCH_Markings`, which R2-132 says gains a substrate but
   is one flat plane at z = 0.007 that cannot know about it.
7. **Object count unchanged at 28,781**; name-set symmetric difference **0**.
8. **0 of 132 material graphs move.** The fix adds no node, no link, no default
   and no material; it only changes which quads a mesh builder emits. Measured
   over every material with the R2-102 graph census, not the bump census.
9. `socket_index_audit --blend assembly9.blend` **PASS**, and the same arm on
   `assembly6.blend` must still **FAIL with 27 findings** or the audit proves
   nothing.
10. `build_architecture`'s own gate goes **2 failures → 1** (R2-132: 13 black
    recesses + coplanar-on-Beat-4 → 9 black recesses, coplanar cleared). Both
    are pre-existing at HEAD. A *rise* above 2 would be mine.

## The null this run is really testing

A ~35-minute regeneration of five modules must reproduce the four unchanged
modules **bit-for-bit**. If a single `SURF_*`, `BR_*`, `TER_*` or `DR_*` vertex
moves, the build is not deterministic and every fingerprint comparison this
project has ever made — a5→a6, a6→a7, a7→a8 and this one — is void.

And the counter-null, which R2-102 earned the hard way: **the module build
report will again show ~0 substantive differences except timings, the output
path and `apron_platform_m2`. That proves nothing.** The counts were
bit-identical while `TER_Ground` rose 326 m. Judge on fingerprints.
