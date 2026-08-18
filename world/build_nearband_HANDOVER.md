# HANDOVER — wiring `build_nearband` into the main terrain build

**Status: NOT APPLIED.** `world/build_terrain.py` is live, a ground fix is being
verified at f2760 and a rebuild is in flight, so nothing in this note has been
written to it. This is the patch spec, for whoever owns that file next.

`world/build_nearband.py` is standalone-runnable and self-gating today
(`--full`, `--terrain-only`, `--selftest`). Nothing below is needed to *use* it;
it is only needed to have `build_terrain.build()` call it as one more tier.

**Line numbers below are against `build_terrain.py` md5
`65f5ae608494e12acab51370e3c9bd2e`.** That file moved twice while this module was
being written (`habitat()` gained `paved` mid-session), so check the anchor TEXT, not
the number. Note especially that `c_weeds = _sub(root, "WeedsStones")` appears
**twice** — at 3975 inside `build()` and at 5149 inside `macro_probe()`. PATCH 2
targets the first. `macro_probe` is the 200 m verge window and does not need this
tier; if you want it there too it is the same three lines against its own locals.

---

## The short version

**Four edits, ~10 lines, no behavioural change to any existing tier.** The module
takes only things `build()` has already made (`Ground`, `GridZ`, `CameraPath`,
`Raster`, the library, the rng, the quality dial) and returns a stats dict.

Nothing in `habitat()` changes. Nothing in the `wood` expression changes. The gate
at `smoothstep(52.0, 150.0, D)` **stays exactly as it is** — this tier is its
complement, and if the gate moves the complement must move with it, which is why
`build_nearband.selftest()` measures the gate edge off the live `habitat()` and
fails if it has drifted more than 3 m.

---

## PATCH 1 — the import

`build_terrain.py`, after line 66 (`import itemkit as K`):

```python
import build_nearband as NB       # the D <= 52 m band `wood` evacuates (R2-1156)
```

`build_nearband` imports `build_terrain`, so this is a cycle. It is a **safe** one
only if the import is placed here, at the end of the header block, *after* `HERE` is
on `sys.path` and *before* anything at module scope in `build_nearband` needs a
`build_terrain` symbol — and `build_nearband` has no module-scope use of `T.*`
except `T.VPFX` and `C.*`/`K.*`, which are available by then.

**If that makes anyone uncomfortable, do it lazily instead** and the cycle is gone
entirely:

```python
    # inside build(), at the call site
    import build_nearband as NB
```

The lazy form is the recommended one. It costs nothing and it means a broken
`build_nearband` can never stop `build_terrain` from importing.

## PATCH 2 — the collection

`build_terrain.py`, after line 3975 (`c_weeds = _sub(root, "WeedsStones")`):

```python
    c_nb = _sub(root, "NearBand")
```

`purge()` already handles idempotency: it walks `root`'s children and removes every
collection and object under them, and it removes every datablock whose name starts
with `PFX` or `VPFX`. Everything `build_nearband` creates is named `VEG_nb_*`, so it
is already inside `purge()`'s scope and **`purge()` needs no change**.

## PATCH 3 — the call

`build_terrain.py`, immediately after line 4138 (`stats["instanced_tris"] =
inst_tris`) and before the `# -- GRASS ---` block at 4140:

```python
    # -- NEAR BAND: the ground `wood` evacuates ---------------------------------
    # `wood *= smoothstep(52.0, 150.0, D)` above is exactly zero for D <= 52 m, and
    # `wood` gates all five woody tiers, so 18.0 % of ground screen-area-time has no
    # woody cover available to it at any density.  build_nearband is the complement
    # of that gate: nb = 1 - smoothstep(52, 150, D), shaped in `f` by a height
    # ceiling so nothing stands in the runoff.  See build_nearband.md.
    log("near band (the complement of the woodland gate)")
    import build_nearband as NB
    nbstats = NB.build(dict(gr=gr, gz=gz, cam=cam, ras=ras, lib=lib, rng=rng,
                            root=root, dom=(X0, X1, Y0, Y1)),
                       quality=q, coll=c_nb)
    stats["instanced_tris"] = stats.get("instanced_tris", 0) \
        + nbstats.pop("nb_instanced_tris", 0)
    stats.update(nbstats)
```

Placement in the sequence is deliberate: **after** the shrub/sapling/fern block (so
the near band can be measured against a scene that already has the woodland tier in
it) and **before** grass, so the ground cover tiers still see the same `ras` and the
same `rng` stream position they always have relative to each other... which they do
not, and that is PATCH 3's one real consequence — see "What this changes" below.

## PATCH 4 — the summary walk

`build_terrain.py`, line 4179:

```python
-    for c in (c_ground, c_trees, c_shrub, c_grass, c_weeds):
+    for c in (c_ground, c_trees, c_shrub, c_grass, c_weeds, c_nb):
```

Without this, `stats["objects"]` and `stats["unique_meshes"]` under-count by the near
band's contribution. `stats["evaluated_tris"]` is already correct because the near
band's triangles arrive through `stats["instanced_tris"]` in PATCH 3.

---

## What this changes, and what it does not

**Does not change:** `habitat()`, the `wood` expression, `species_pick`, the woodland
tier, the hedgerow tier, the avenue, the shrub/sapling/fern tiers, `build_grass`,
`build_sward`, `build_weeds_and_stones`, `build_grit`, `cut_field`, `build_ground`,
`purge`, `selftest`, or any constant in the file.

**Does change, and it must be stated:** `NB.build()` draws from the shared `rng`.
Inserting it before `build_grass` therefore **shifts the random stream** for grass,
sward, weeds, stones and grit. No tier's *design* changes and no count changes by
more than sampling noise, but **no frame will be bit-identical to a pre-patch
frame**, so this cannot be landed as a "no-op refactor" and any A/B against an
existing render must be rebuilt on both sides.

If that is unacceptable at the point this is landed, the fix is one line: give the
near band its own generator,

```python
    nbstats = NB.build(dict(..., rng=np.random.default_rng(NB.SEED), ...), ...)
```

and every downstream tier keeps the exact stream it has today. This is the safer
option and is what I would land. The only thing it costs is that `TERRAIN_QUALITY`
no longer perturbs the near band's draws in the same way it perturbs everyone
else's, which is not a property anything depends on.

## Cost, so it can be budgeted before it is landed

See §12 of `build_nearband.md` for the measured figures from the standalone build.
Two of them govern whether this lands as-is:

* **base library** — the near band adds its own clump/hedge/planter meshes and tops
  up the short-tree library. This is resident memory, once, shared by every
  instance.
* **instanced triangles** — this is the number that moves render time, and it is
  concentrated in the 20-52 m band, which is the closest ground to the lens for most
  of the film. If it has to come down, the dial is `NB_TIERS[*]["dens"]` and
  `NB_TREE_DENS`, in that order; `pitch` is the wrong dial because the clump was
  sized to the pitch and changing one without the other changes the plan cover by
  the square.

`NEARBAND_QUALITY` is an independent environment dial (defaults to
`TERRAIN_QUALITY`), so the near band can be thinned for local test renders without
touching the rest of the world.

## Ordering in `assemble.py`'s `MODS`

**`build_nearband` goes AFTER `terrain`, unconditionally.** It captures `Ground`,
`GridZ`, `CameraPath`, `Raster` and `build_library` from that module's `build()`, and
its density is *defined* as the complement of that module's `wood` gate. It cannot
precede what it reads. There is no configuration in which the reverse order is
meaningful, so this is a hard edge, not a preference.

## A QUESTION FOR THE R2-1821 AUTHOR, WHICH I HAVE NOT ANSWERED

R2-1821 moved the three ground-cover tiers from the hand-drawn `built` district to the
contract's `paved` field, and **deliberately kept `built` as the tree keep-out**:
*"Trees, shrubs, ferns, weeds, grit and the park species mix still read `built`,
because a tree keep-out around a paddock genuinely IS a district."*

`build_nearband` places **44.9 instances/ha inside that district against woodland's
1.8/ha — a 25x ratio** over 13.3 ha. That is a direct disagreement with a live
decision, not an ordering accident, so it is written here rather than resolved.

What is actually placed there is amenity planting, not woodland: clipped hedge runs
and kerbed planters under 1.45 m, plus ornamental hawthorn/rowan standards at
3.2-6.0 m, all driven from `C.platform_field` (the declared paving edge), all outside
the road corridor, the beat-3/4 transit route and the forecourt box. The design claim
is that this is what a paddock perimeter has on it and is not the thing the keep-out
was written to exclude. **The R2-1821 author should rule.**

If the ruling is that the keep-out covers amenity planting too, the change is one
line — drop the `build_amenity()` call from `build_nearband.build()` — and none of
the no-cliff evidence moves, because it is computed over open country
(`built < 0.30`) precisely so this question cannot contaminate it.

## The one thing `build_terrain` could usefully export, but does not have to

`habitat()`'s gate constants `52.0` and `150.0` are literals inside the function
body. `build_nearband` re-states them as `WOOD_GATE_D` and **measures them off the
live `habitat()` in its selftest**, failing if the measured edge has moved more than
3 m. That instrument is sufficient, and it is deliberately in the *new* file so that
this handover requires no change to the live one.

If at some later point `build_terrain.py` is being edited anyway, promoting them to a
module constant

```python
WOOD_GATE_D = (52.0, 150.0)     # near-band tier is the exact complement of this
...
    wood *= smoothstep(WOOD_GATE_D[0], WOOD_GATE_D[1], D)
```

would let `build_nearband` import them instead of measuring them, and would put a
grep-able marker on the line that caused R2-1156. That is a nicety, not a
requirement, and it is **not** part of the patch above.
