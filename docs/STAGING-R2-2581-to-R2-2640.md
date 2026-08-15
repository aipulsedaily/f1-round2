# STAGING R2-2581 to R2-2640 — disk reclaim before the 4K master

Agent `r2-2581-disk`. 2026-08-08.

Task #79. The question was whether the 4K master fits. **It does, with room to
spare — and the reason it looked like it did not was a wrong per-frame constant,
for the second time in this project.**

---

## R2-2581 — the answer up front

```
before   67 GB free   (526 G used of 594 G, 89 %)   -- and falling: two ~10 GB
                                                       builds were in flight,
                                                       it touched 56 GB mid-task
after   149 GB free   (444 G used of 594 G, 75 %)
recovered                                            129.53 GB
```

**The 4K master needs ~24 GB, not ~45 GB.** It fits roughly six times over.

---

## R2-2582 — where the 480 GB was

`render/` measured 481 GB. It did not break down the way the directory listing
suggested, and that mattered: **351 GB of it was loose files in `render/` itself**,
not in any subdirectory. The subdirectories only accounted for ~135 GB.

| | |
|---|---|
| loose `.blend` / `.blend1` in `render/` (123 files) | **351 GB** |
| `render/world/` (assemblies + world renders) | 94 GB |
| everything else in `render/` (50 subdirs, largest 4.5 GB) | ~36 GB |
| `world/` (item libraries, `world/items` = 38 GB) | 72 GB |
| `work/` | 29 GB |
| `sim/`, `cache/`, `audio/`, `tmp/`, rest | ~8 GB |

The generational sprawl is real: `film6` … `film23`, `film9_breach` …
`film18_breach`, `assembly5` … `assembly14`, at 4.3–10.4 GB each.

---

## R2-2583 — what was LIVE, established before anything was touched

`lsof +D` returned **nothing** for `render/` — it is unreliable here and would
have given a false all-clear. `/proc/<pid>/fd` is authoritative and was used
instead.

At the time of measurement:

| PID | reading | writing |
|---|---|---|
| 2003282 | `render/film23.blend` | `render/film23_breach.blend@` |
| 2003465 | `render/world/assembly/r2/assembly14.blend` | `render/r22161_after.blend@` |
| 2046796 | `world/verify_world.blend` | `work/r2-2341/runs/head/r5.json` |

Both `.blend@` files are Blender's mid-save temporaries. **Two ~10 GB writes were
in flight throughout this task**, which is why free space fell from 67 GB to
56 GB while measuring. Both landed intact afterwards:
`film23_breach.blend` 10,439 MB, `r22161_after.blend` 9,545 MB.

Also live and untouched: `work/r22161_proxy/`, `~/vast-render/out3…out11/`
(whole-film proxy, 960×540), `render/r2401/`.

---

## R2-2584 — the free win, which was the whole win

**224 `.blend1` / `.blend2` Blender backups totalling 149.5 GB.** Blender writes
one on every save; each is by construction the previous generation of a `.blend`
that still sits next to it. `docs/WAVE2-SCOPE.md:698-722` had already named
deleting them as the project's disk policy.

Two exclusion rules were applied before deleting anything, and both caught real
cases:

**Excluded — orphans (5 files, 1.4 GB).** A `.blend1` with no matching `.blend`
is not a backup of anything; it is the only surviving copy. These are the exact
"looks regenerable and is not" case:

```
world/items/access_road_slab_draft.blend1        290 MB
work/r2116/scratch/gravel_bed_surface_ctl.blend1 1.0 GB
work/gru/probe0.blend1                           139 MB
render/exposure_cal/expcal_{agx,std}_atmo.blend1 1.6 MB each
```

**Excluded — modified in the last 2 hours (3 files, 18.7 GB).**
`render/film23.blend1` and `render/r22161_after.blend1` are the backup halves of
the two scenes being written right now. Deleting them gains nothing durable —
Blender recreated `r22161_after.blend1` at 9,544 MB the moment its save landed —
and the rename-over race is not worth running for space that is not needed.

**Deleted: 216 files, 129.53 GB.** Manifest with path, size, mtime and the
superseding `.blend` for every entry: `docs/manifest_blend1.tsv`.

All 33 `film*.blend` scenes verified present afterwards. Nothing else was deleted.

---

## R2-2585 — the per-frame size, measured, not assumed

The brief assumed ~15 MB/frame. `docs/RENDER-LADDER.md:89-90` used 7.2–7.8 MB but
measured it on `render/breach_f9/` — **film9, a much sparser world**, so it was
fair to distrust it now that `world/items` is 38 GB.

Census of every 3840×2160 PNG on the box: **1,705 frames, 10,576 PNGs inspected.**
The decisive finding is that the population splits cleanly in two:

| | N | mean | note |
|---|---|---|---|
| **8-bit RGB** | 870 | **8.08 MB** | the delivery format |
| 16-bit RGB | 835 | 15.87 MB | pixel-peep / witness analysis frames |

**The scary numbers were bit depth, not density.** `work/r2791/ab/f000371_FIX.png`
is 36 MB and 3840×2160 — and 16-bit. Every delivery-spec render of record is
8-bit: `r2943_4k` 9.22 MB, `r2851_4k_A_shipped` 9.12, `fleetproof` 7.88–8.46,
`b5verdict_4k` 7.27.

**There is no newer-is-denser trend.** 8-bit 4K means by date: Jul 28 7.69,
Jul 29 8.88, Aug 3 7.76, Aug 4 7.70, Aug 7 7.93, Aug 8 8.97. Pre-Aug-3 frames are
*larger* than Aug 6+ frames. The spread is driven by shot content (gravel and
asphalt macro plates at 15–16 MB), not by calendar. The four `fleetproof`
sequences, same scene same day on four brokers, span 7.88–8.46 MB on their own —
as wide as the entire apparent date effect.

The right basis is the `seq/` continuous-camera frames from Aug 6+, the only
apples-to-apples analogue of a master: **N=85, mean 8.083 MB, median 8.136,
p95 8.797, max 11.014.**

```
2,978 frames x 8.083 MB (mean)   =  23.5 GiB     <- expected
2,978 frames x 8.797 MB (p95)    =  25.6 GiB     <- planning figure
2,978 frames x 11.01 MB (max)    =  31.3 GiB     <- pathological worst case
```

---

## R2-2586 — does it fit

**Yes, comfortably.**

```
free now                              149 GB
4K PNG master (p95 basis)              26 GB
ProRes 422 HQ, 124.08 s                11 GB
H.265 delivery                         <1 GB
one more film scene generation         10 GB
                                     -------
whole delivery + a build                47 GB
margin                                102 GB
```

Even at the pathological 11.01 MB/frame the master is 31 GB and the margin is
97 GB. **No encode-and-delete in flight, no alternate filesystem, no dropping
intermediate scenes.** Render it straight to disk.

The thing to watch is not the master, it is the build set: film scenes cost
~10 GB per generation and `.blend1` regenerates at full size on every save. Two
live scenes are already carrying 18.7 GB of backup between them. **At seven
agents that is the burn rate, and the `.blend1` sweep is the lever — it can be
re-run at any time and will keep returning tens of GB.**

---

## R2-2587 — what was deliberately NOT deleted

Space stopped being the constraint at 149 GB free, so nothing below was touched.
Every one of these was a live candidate that failed a check:

**`tmp/` — 733 MB, and the brief said it was safe.** It is gitignored and has
zero tracked files (verified: `git ls-files tmp` = 0). It is still not safe:

```
tmp/r2179/marshal_post_deck_test_PRE_R2179.blend   426 MB   a PRE-change state
tmp/brokerbase/, tmp/brokerfix/, tmp/broker_revert/  68 hand-written .py files
```

A `_PRE_` blend is a before-state — the thing an A/B is measured against — and
the broker trees are revert points for `~/vast-render`. Untracked means
unrecoverable. **733 MB is not worth that against 102 GB of margin.**

**`/tmp/blender_*` — 141 dirs, 24 MB, and `/tmp` is tmpfs.** It is RAM, not
`/dev/vda3`; clearing it frees no disk at all. Worth flagging separately though:
**`/tmp` is at 4.5 G of 5.9 G on a box with 11 GB RAM and 32/43 GB swap gone.**
That is memory pressure, not disk, and it is not from Blender's temp dirs.

**Every `.blend` scene, including the ones the docs call throwaway.** ~35 GB was
available here — `film19.blend` (7.5 GB, "superseded and its verification bar
never ran"), `film16_R2851.blend` (8.0 GB, "THE PROBE BLENDS ARE THROWAWAY"),
`film14_breach_r6b.blend`, the two `r2607_unbend_*_DO_NOT_SHIP.blend`,
`film14_breach_R2281_FRAMEONLY_DIAGNOSTIC_DO_NOT_SHIP.blend`. **A `DO_NOT_SHIP`
in a filename is a name, not a measurement, and the standing rule here is that
deletions are justified by measurement.** The measurement says the space is not
needed. Recommending them is the correct output; deleting them is not.

**Doc-protected, never to be deleted** (from the evidence sweep):

- `render/ladder/film9_ladder.blend` — 4.5 GB, carries a `.sha256` sidecar, the
  only such sidecar in the project
- `film9.blend`, `film10.blend` — `world/assembly/r2/SHIPPING.md:65-67`,
  "deliberate controls and MUST NOT be deleted"; `MASTER-PLAN.md:102-104` notes
  deleting film10 "silently turns every audit that cites it into a vacuous pass"
- `assembly6/7/9/10.blend` — bound by written hashes in `WAVE2-SCOPE.md:35,427`,
  `WAVE2-RANKING.md:52`, `STAGING-R2-2341-to-R2-2400.md:364`
- `film17_R2943.blend` — scene hash `ec95e539bb6a04d4`, the only delivery-spec
  fleet render on record
- `film14_breach_r6.blend` — `STAGING-R2-416-to-R2-450.md:1628`, "Do not delete them"
- `assembly14.blend` — the shipping world, `SHIPPING.md:3`; `build_film_scene.py`
  refuses any other
- `film23.blend` / `film23_breach.blend` — the current lineage

---

## R2-2588 — corrections to the record

- **`docs/RENDER-LADDER.md:107` says "136 GB free" and "no disk blocker".** The
  free-space figure was stale (it was 67 GB at the start of this task, 56 GB
  mid-task) but **the conclusion was right and is now right again by measurement,
  not by luck.** Its ~22 GB master estimate is confirmed at 23.5–25.6 GiB.
- **`docs/WAVE2-SCOPE.md:698-722` "short by 318 GB" stands** — that is the 407-item
  wave, a different question from the master, and it is still unfunded.
- The `.blend1` sweep is repeatable. It should be run before the master starts,
  not instead of.
