# `round1_source/` — the recipe for the car, vendored

**This directory is a frozen, byte-faithful copy of the round-1 code that builds
the car.** Nothing in round 2 builds from it. It exists so that the answer to
*"what happens if round 1 vanishes?"* is **"run one script for five minutes"**
rather than *"the hero asset is unrecoverable"*.

```
round1_source/build/            <- /home/zany/opus5-car-render/build/        (minus __pycache__)
round1_source/tools/rebuild_scene.py
                                <- /home/zany/opus5-car-render/tools/rebuild_scene.py
```

Copied 2026-08-14 (task #168, R2-4026..R2-4029). 2.4 MB, 46 Python files, all
text. Verified byte-faithful at copy time with `diff -r`.

---

## The problem it closes

Round 2's car chain bottoms out in round 1, and it does so *at build time*, not
merely historically:

```
render/film25_breach.blend        the delivered master's scene
  <- world/car_anim.blend         anim/build_car_anim.py, run on beat1_anim.blend
  <- world/beat1_anim.blend       anim/build_beat1_anim.py, run on ...
  <- /home/zany/opus5-car-render/work/iter.blend      288,254,978 B, 2026-07-26
```

`anim/build_beat1_anim.py` reads every part's seated transform straight out of
that blend — *"the seated pose is not authored, it is the round-1 car"* — so the
scene is not a starting point it could do without. Made unavailable, the chain
does not degrade; **Blender exits 1 before the script runs at all.**

Three properties made that worth acting on:

* **`f1-round2` tracks no blends** (`.gitignore:12 *.blend`, and `git ls-files`
  returns zero of them), so no on-disk artefact in this repo is a backup.
* **Round 1 is not a git repository.** There is no `.git` anywhere under
  `/home/zany/opus5-car-render`. It has no history to recover from.
* **Round 1 is read-only to this project**, so round 2 cannot protect it in
  place.

## What is NOT true, and it changes the remedy

**`iter.blend` is not an unregenerable artefact. It is a build output, and its
build is deterministic.** Round 1's own README gives the command that produces
it, and running that command today reproduces the shipped scene exactly.

Measured on 2026-08-14, `/opt/blender-5.2.0-linux-x64/blender` (hash
`fbe6228777e7`), a fresh build compared against the shipped `iter.blend`:

| | result |
|---|---|
| file size | **288,254,978 B — identical to the byte** |
| objects | 947 / 947, **0 names only in one side** |
| worst Δ location, rotation, scale, dimensions over all 947 | **0.000e+00** |
| mesh objects geometry-fingerprinted (SHA-256 over vertex coordinates, polygon and edge counts, material slots) | 919 / 919 |
| **geometry mismatches** | **0**, over **4,721,531 vertices / 4,598,601 polygons** |
| materials, cameras, lights, collection tree | 51 / 4 / 23, identical |
| raw bytes differing | 20,608 of 288,254,978 = **0.0071 %**, isolated 4-byte words at a fixed stride plus the embedded file path — datablock session identifiers, not data |

So the thing that cannot be regenerated was never the 288 MB binary. **It is the
2.4 MB of Python that emits it, sitting in an unversioned directory** — and that
is what is vendored here, because copying the artefact would have preserved the
cheap half of the problem and left the expensive half where it was.

Not copying the blend is also the repository's own policy applied honestly:
`.gitignore:12` excludes `*.blend` as *"all regenerable, all enormous"*, and this
one is exactly that. A 288 MB blob would have grown a 41 MB `.git` by about
eight times, permanently, for every clone, to store something a five-minute
command rebuilds.

## Proof that the vendored copy is sufficient

`reconstitute.sh` rebuilds the scene from this directory with **zero references
to round 1** — it asserts that by grepping its own working tree for the string
and refusing if one survives. Run end to end on 2026-08-14:

```
>> working tree at /tmp/r1recon.MX3MZI has ZERO references to round 1
>> scene: 919 meshes, 4,598,601 polys, 23 lamps
>> reconstituted r1_recon.blend (288254978 bytes) from vendored source alone
   geometry fingerprints vs the shipped iter.blend:  0 mismatches / 919 meshes

then the round-2 car chain, run on that reconstitution:
>> seat check: worst deviation 0.0000 mm over 616 parts, 0 stragglers
>> save_clean: world=R2_ProceduralSky, 0 external deps
>> animated 616 objects across 15 clusters
>> saved beat1_from_recon.blend  291,187,821 B
>> STAGE RESULT: BEAT1_ANIM_OK
```

**291,187,821 bytes is the size of the shipping `world/beat1_anim.blend` to the
byte.** The claim is not that the recipe looks complete; it is that the chain's
first artefact came out the same size from a tree that had never seen round 1.

## The one input that is deliberately missing

`build/s01_base.py:154` loads `$PROJ/assets/city.exr`, and `images.load()`
**raises** when the file is absent, so the round-1 build will not complete
without something at that path. Round 1's `city.exr` is a real photographic HDRI
and the round-2 brief forbids downloaded stock outright, so **it is not vendored
and must not be.**

It does not need to be. `reconstitute.sh` generates an 8×4 px stub, and the
content never survives anyway: every round-2 build path saves through
`tools/fix_audit_blend.save_clean()`, which replaces the world with a procedural
Sky Texture, strips external images and refuses to save if one remains. The file
has to *exist*; it does not have to be anything.

**This is how #168 found a second round-1 coupling.** `save_clean`'s strip rule
tested the literal substring `"opus5-car-render/assets"` — which is not "outside
this project", it is "inside round one", and it worked only because round 1
happens to live at that path. Rebuild the identical scene anywhere else and the
HDRI reference survives the strip, trips the refusal, and the car chain stops one
line before saving. That is not a hypothetical: it is what the first run of
`reconstitute.sh` did. The rule now asks whether the path is outside
`f1-round2`, which is the question it was always trying to ask (R2-4028).

## What would be lost if this directory and round 1 both vanished

Everything the car is. `iter.blend` supplies the whole of round 1 to round 2 —
616 car meshes plus `CAR_ROOT`, 76 showroom objects, 61 lights, 189 props, 51
materials, 4,598,601 base polygons — and **none of it is derivable from anything
tracked in `f1-round2`.** `docs/explode_plan.json` (tracked) names the parts but
holds no geometry; `docs/inventory_iter.json` records every seated transform to
six decimals but is gitignored, and transforms without meshes are not a car.

## Rules for this directory

1. **Do not build from it.** The live chain runs on round 1, at
   `/home/zany/opus5-car-render/work/iter.blend`, and should keep doing so while
   round 1 exists. Two live copies of a build tree is a drift problem, and this
   copy exists precisely so there is never a question about which is canonical.
2. **Do not edit it.** It is byte-faithful on purpose, so that while the
   original still exists a reader can `diff -r` the two and get silence. The one
   patch a standalone run needs (two absolute paths) is applied by
   `reconstitute.sh` to a throwaway copy, never here.
3. **Round 1 stays read-only.** Nothing in #168 wrote to it; that was verified
   by comparing a full `find -printf '%T@ %s %p'` snapshot before and after every
   run, including the ones that imported its modules
   (`PYTHONDONTWRITEBYTECODE=1`, so not even a `.pyc` landed).
4. **If round 1 is ever deleted, this stops being a backup and becomes the
   source.** Delete rule 1 at that point and say so here.
