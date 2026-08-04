# R2-187..194 — predictions, written BEFORE the apply finished and BEFORE any frame was rendered

Written 2026-08-04 01:1x UTC, while `apply_breach.py` was building shards into
`render/film14.blend`. Nothing below is read off the applied scene.

## What I am betting on, mechanically

`film13_breach` = assembly8 + bake. `film14` = assembly9 + the same camera.
`film14_breach` = assembly9 + the same bake.

The bake is a **file** — `sim/out/breach_film.npz`, sha unchanged — and the applier
reads it, the fracture plan `sim/out/fracture_wall.npz`, and the camera polyline out
of `docs/beat_sheet.json`. **None of those three inputs is a function of the world.**
`assembly9 − assembly8` is one object, `ARCH_Paving_ApronPlatform`, +11,871 verts of
pit-exit paving, entirely inside its own bbox except for one extreme that moved 46.8 mm
*inward*. It is not in the glazing pocket, it is not in the fracture plan, and it does
not touch the camera.

So the applied breach must come out **numerically identical** to film13's, and every
difference is a finding.

---

## P1 — the readback is identical to film13's in all four fields

    objects 3806    tris 278864    keys 5798701    hero 3573

**Falsified if any one of them differs.** And each one falsifies something different,
which is why all four are worth stating:

* `objects` or `tris` moving ⇒ the **fracture plan** moved (it decides shard count and
  which bays exist). Nothing should have touched it.
* `keys` moving ⇒ the **resample** moved, or a bay's swap frame moved (the hide keys
  are 3 per channel per animated object and are counted in this total).
* `hero` moving ⇒ **the camera moved.** `hero` is `dist_to_path(shard keys) <= 6.0 m`
  against `camera_polyline()`, and `film14_path.json` has the same sha as
  `film13_path.json`. A change here would mean the byte-identical-camera claim is
  false somewhere that the path JSON does not capture.

Read back from the saved `.blend`, not from `sim/out/apply_film14.json`.

## P2 — the scene object total is film14's + 3806, and the apron is in the file

`ARCH_Paving_ApronPlatform` must be present in `film14_breach` with **140,593 verts**
(assembly9's number, R2-148). If it reads 128,722 the apply was run on the wrong film.

## P3 — the east wall is glazed, and I will only believe the picture

Ten `GP_b*` panes present, none `hide_render` at frame 1. **The metric that is supposed
to watch this is broken** — `n_GW_Right_Glass` counts round 1's object names and reads
0 for a correct scene as well as an empty one — so the test is a render.

f0858 from `film14_breach` shows a **glazed** east wall: reflections and transmission
through ten panes with the mullion grid over them. **Falsified if it is bare bars with
the paddock through them**, which is what film10–13 render because `apply_breach` is
what supplies the glazing and was never re-run on them.

## P4 — f0866 and f0890 are the film13 pictures, to within the render's own noise

Content, restating what P3 of `sim/out/slab_prediction.json` scored on film13_breach:

* **f0866** — clear glass with a **localised burst** of fragments where the car is. Not
  a continuous field of overlapping parallel translucent slabs.
* **f0890** — large angular fragments dispersing at varied orientations, glass on the
  ground, the hole open and growing.

Quantitatively: `film14_breach` f0866 vs the archived `film13_breach` f0866 differ only
at the Cycles reproducibility floor. R2-150 measured that floor as **4.85 % of pixels
differ at all, 0.00 % differ by more than 2/255, max 3/255** — but that was a different
instance on a different night, so **I will re-render f0866 from `film13_breach` on the
instance I am using and take the floor live.** Without that control the comparison
asserts nothing.

**Falsified if any region differs by more than 8/255 above the live floor.** That would
mean `ARCH_Paving_ApronPlatform` is in frustum at f866 — which would be *interesting*,
not bad: it would mean the pit-exit repair reads in beat 3 as well as at f1104, and
R2-150's "f1104 is the best view" would need a companion.

## P5 — the applied CURVES reproduce the bay-4 numbers, not just the table

The claim that closed R2-097 was measured on `sim/out/breach_film.npz`. That file is
the same file, so re-running `slabcheck` on it would assert **nothing about this apply**.
So the test is run on the **scene**: evaluate `GS_b04_*` world positions off the applied
f-curves at f845 (the table's first frame, which is home) and at 866 / 880 / 900 / 920,
and take the median 3D displacement.

    predicted, from the scene:  f866  2288.5 mm     f900  2615.1 mm
    and f900 > f866, i.e. no return
    the null it is against:     the shipped 4000 bake, 530 mm -> 48 mm

Tolerance: the resample kept 65.3 % of keys and declares `max_pos_err_m` 0.0015, and the
applier writes LINEAR interpolation between kept keys, so a frame that is not itself a
kept key can sit up to **1.5 mm** off the table. **I predict agreement within 2 mm.**
Falsified if the scene disagrees with the table by more than that — that would mean the
curves are not carrying the bake.

## P6 — the gates, each with the control that discriminates

| gate | predicted on film14_breach | control, and why it is not vacuous |
|---|---|---|
| `socket_index_audit --blend` | **PASS** | `film10` — the assembly6 control — must still **FAIL with 27 findings**. If film10 has started passing the gate has stopped measuring. |
| `verify_breach.py --swap-scene` | **PASS, 0 problems**, all six fractured bays (2,3,4,5,6,7) swapping on **frame 860** | the same script's `--swap` arm on the *table* still reports the defect (bay 5 worst gap 2,118 frames). Table FAILs, scene PASSes: that pairing is what shows the applier is the fix. |
| `apply_breach --selftest` (census) | PASS | it is the east-wall census's own must-fail arms |

## P7 — the three inherited items do not move, because they are properties of the bake

    below floor      627 bodies, worst 154.6 m down, 1.9 % of the field
    not at rest      2,275 bodies over 1 mm/frame at the last key
    cluster B        348 shards to 106 m/s with no measurable contact

All three are read out of `breach_film.npz`, which is byte-identical, so **I predict all
three are unchanged**. I will nevertheless measure the first two **on the applied scene**
rather than on the table, because the scene is the decimated LINEAR reconstruction and is
the thing that renders — and a body 154 m under the floor is a body whose keys the
applier wrote.

**Falsified if the scene's below-floor count differs from 627 by more than the handful
the 1.5 mm resample tolerance can explain.**

## P8 — `--force` is still right, and R5 refuses on a class the sim itself builds

I predict film14's R5 finding is **bit-identical** to film13's: the same nine names with
the same `(n_in, n_tri, n_clear)` triples, the same 18 capture-band members, the same 79
AABB candidates. If it is not, something moved in the pocket and `--force` would be a
new decision rather than the same one.

*(Recorded before the apply, after the preflight-only run: it is identical. See the
report.)*

## What I cannot predict

Whether the three round-1 transom rails that R5 names — `GW_Right_Transom_0/1/2` at
z 1.35 / 2.85 / 4.35 — read as **unbroken bars across the aperture** in f0874/f0890.
The sim models those rails as ACTIVE bodies that shed segments (`TRN_z*_b*`, 2 segments
of mullion 5 detach), but **R6 is open**: `apply_breach` writes MUL*/TRN* transforms and
nothing binds a mesh to them, so what renders is round 1's *static* frame. Whether that
is visible is a picture question and I have not looked yet.
