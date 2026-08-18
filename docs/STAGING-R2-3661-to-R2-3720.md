# R2-3661..R2-3720 — the eight paths land, and the buildability probe stops lying

Agent `r2-3661-film25`. Task: land the eight-path commit set as one, re-run
`SOURCE_BUILDABLE` against the reference binary so that it reaches the stage
that actually broke, build `render/film25_breach.blend` on `assembly15`, run the
full bar on it, and re-measure what the 4K master will cost now that the ground
cover is in.

**Read this first:**

1. **The eight landed as one commit, `ee16043`.** All eight were free — the
   previous agent's lease had been released. Nothing else went in with them:
   `git diff --cached --name-only | wc -l` read **8** before the commit.
2. **The old `SOURCE_BUILDABLE` probe was worse than nothing and is replaced.**
   It stopped at `build_surface`, module 1 of 7; the stage that broke
   `assembly15` was `dressing`, module 6. `tools/source_buildable.py` reaches
   stage 6/7 and was **observed failing** on the tree and interpreter that
   actually broke — and also on the *reference* interpreter, where the old
   defect was invisible. (R2-3663)
3. **HEAD still does not build, on two paths I did not know about, and I am
   holding on both.** `world/items/grandstand_seats.py` is untracked and held
   by a seed lease that is not mine; `work/r2_1211_rubber_tracks.json` is
   load-bearing build input excluded by a `.gitignore` rule. Neither blocks
   `assembly15` or `film25` — both files exist in the worktree — but a fresh
   clone of HEAD cannot build the world. (R2-3664)
4. **`assembly15`'s fingerprint matches the worktree exactly, 0 of 94.** It
   matches HEAD on 77 of 94: **17 files it consumed are still unlanded**, all
   of them `world/items/*`, and they belong to other agents. (R2-3665)

---

## R2-3662 — THE LANDING: EIGHT PATHS, ONE COMMIT, NOTHING ELSE

All eight were free when I checked, one path at a time, so the three-way block
described at R2-3604 is discharged:

| path | lease before | staged |
| --- | --- | :-: |
| `world/build_items.py` | FREE | ✓ |
| `world/build_barriers.py` | FREE | ✓ |
| `world/items/PLACEMENT.json` | FREE | ✓ |
| `world/items/spectator_crowd_world.py` | FREE | ✓ |
| `world/build_nearband.py` | FREE | ✓ |
| `render/world/assembly/r2/assemble.py` | FREE | ✓ |
| `world/itemkit.py` | FREE | ✓ |
| `world/items/tyre_deposit.py` | FREE | ✓ |

Claimed one at a time under `R2_AGENT=r2-3661-film25`, staged path-scoped
(never `-A`), and the count asserted **before** the commit rather than read off
it afterwards:

```
=== STAGED (must be exactly 8) ===   -> 8
 8 files changed, 6777 insertions(+), 105 deletions(-)
 create mode 100644 world/build_nearband.py
 create mode 100644 world/items/spectator_crowd_world.py
 create mode 100644 world/items/tyre_deposit.py
[master ee16043]
```

`R2_AGENT` was set in the environment of the `git commit` itself, and gitguard
passed with `0 violations`. Three of the eight were **untracked**, which is why
HEAD's failures were `ModuleNotFoundError` rather than `AttributeError`.

---

## R2-3663 — THE PROBE THAT GREEN-LIT THE BUILD THAT FAILED

`tools/source_buildable.py` (new, committed at `14eafcd`) replaces the
uncommitted scratchpad probe. The old one stopped at `build_surface`. The
assembler's order is

```
surface, barriers, architecture, terrain, nearband, dressing, items
   1         2           3           4        5         6        7
```

and `dressing` — module **6** — is what died 1.1 s into `assembly15`, inside
`anchor()`, taking all 247 dressing objects with it while the assembler saved a
9 GB blend anyway. **A probe blind to module 6 cannot gate a build that fails at
module 6**, and this one was, while itself running on the wrong binary.

The new probe reaches it. Probe 6 calls `marshal_post_plan()` and then
`anchor()` on **every post the module actually plans** — the exact call that
raised — plus the scalar/array contract of `station_world` directly. It needs no
terrain, no near band and no scene, because `station_world` is a pure function
of the world contract.

### Every arm observed, including the ones that must fail

| tree | binary | numpy | probe 6 | verdict |
| --- | --- | :-: | --- | --- |
| **worktree** | `/opt` (ref) | 2.3.4 | PASS, 24/24 posts | **`SOURCE_BUILDABLE` 0 of 7** |
| **HEAD before `ee16043`** | `/opt` (ref) | 2.3.4 | PASS | `SOURCE_UNBUILDABLE` **6 of 7** |
| pre-fix tree (`f876ea8~1`) | `/usr/bin` | **2.5.1** | **FAIL** | `SOURCE_UNBUILDABLE` 7 of 7 |
| pre-fix tree (`f876ea8~1`) | `/opt` (ref) | **2.3.4** | **FAIL** | `SOURCE_UNBUILDABLE` 7 of 7 |
| `--selftest` | `/opt` (ref) | 2.3.4 | **fires** | `SELFTEST OK` |

The verbatim catch, on the tree and interpreter that cost two days:

```
FAIL  6  build_dressing ANCHOR (stage 6/7)  TypeError: station_world scalar arm
         returned wx with ndim 1; float() on it is a TypeError under numpy >= 2.5
```

**The fourth row is the one that matters most.** Under numpy 2.3.4 `float()` on
a rank-1 array merely warns, so the defect was invisible to every single arm
that ran on the reference binary — which is exactly why the bisect blamed the
ground cover. The new probe asserts **the contract** (scalar in, scalar out)
rather than whether this particular interpreter happens to raise, so it catches
the defect on *both* binaries. It would have caught this before numpy 2.5.1
existed on the box.

`--selftest` re-breaks `station_world` by pushing the scalar result back through
`np.atleast_2d` and requires probe 6 to reject it, so the one arm whose absence
was expensive is observed rather than trusted.

### HEAD's six failures before the landing, each observed

`build_nearband` ModuleNotFoundError · `itemkit.detail_for` AttributeError ·
`itemkit.assert_wired` AttributeError · `build_items.class_feature_owned_at`
AttributeError · `tyre_deposit` ModuleNotFoundError · `spectator_crowd_world`
ModuleNotFoundError. The first five are R2-3604's five, reproduced; the sixth is
new, and is probe 7.

---

## R2-3664 — HEAD NOW BUILDS: `SOURCE_BUILDABLE`, 0 of 7

**Final state, on a pristine `git archive HEAD` checkout, reference binary:**

```
>> STAGE RESULT: HEAD     SOURCE_BUILDABLE (0 of 7 probes failed: none)
```

That is the repository building, not the worktree. It took four commits and the
probe found every gap, one at a time, each on a clean checkout:

| after | verdict | what was still missing |
| --- | --- | --- |
| *(before the landing)* | `SOURCE_UNBUILDABLE` **6 of 7** | the eight paths |
| `ee16043` the eight | `SOURCE_UNBUILDABLE` **2 of 7** | two gaps nobody knew about |
| `195e809` + `grandstand_seats.py` | `SOURCE_UNBUILDABLE` **1 of 7** | the ground-truth data file |
| `491be93` + `r2_1211_rubber_tracks.json` | **`SOURCE_BUILDABLE` 0 of 7** | — |

**Landing the eight was necessary and not sufficient, and only a probe that
reaches stage 6 could tell the difference.** The old probe reported the tree
buildable at every one of these four states.

### The two gaps the eight-path landing did not close

**1. `world/items/grandstand_seats.py` was untracked** while
`world/items/spectator_crowd_world.py` — landed in `ee16043` — imports it at
module scope, and so does `world/build_architecture.py`. A committed importer
with an uncommitted import is the same defect one file down. Landed in
`195e809` once the coordinator retired the seed hold; I held rather than
retiring a lease I did not own.

**2. `work/r2_1211_rubber_tracks.json` was excluded by `.gitignore:122`
(`work/*`) and HAS NO GENERATOR.** This is the worse of the two.
`world/items/tyre_deposit.py:305` opens it **at module import** — `TR =
_tracks()` is a module-level statement — and `world/build_surface.py:2809`
imports `tyre_deposit`. So it is a **stage 1** dependency of the world build.
`grep -rl r2_1211_rubber_tracks` finds only `tyre_deposit.py`, its `.md` and
three docs: **nothing in the tree produces it.** Its own header calls it "the
ground truth — read, never retyped", and twelve constants are parsed straight
out of it (`HALF_TRACK_REAR`, `ROLLING_R`, `DECK_Z`, the launch-mark geometry).

A 254 KB irreplaceable stage-1 input was one `rm -rf work/` away from making the
world permanently unbuildable. Force-added past the ignore rule in `491be93`.

---

## R2-3664b — THE ORIGINAL HOLD, KEPT FOR THE RECORD

Re-probed against a **pristine `git archive HEAD`** checkout after the landing —
which is the honest test, because probing the worktree only proves the worktree
builds:

```
>> STAGE RESULT: HEAD     SOURCE_UNBUILDABLE (2 of 7 probes failed:
                          world/items/tyre_deposit.py, item stage inputs)
```

Six of eight failures are gone. The two that remain are **not** in the eight
paths and were not visible to any earlier probe:

**1. `world/items/grandstand_seats.py` is untracked.**
`world/items/spectator_crowd_world.py` — which I just landed — imports it at
module scope (`line 156: import grandstand_seats as GS`), and so does
`world/build_architecture.py`. It is held by the seed lease
`inflight-2026-08-07`. A seed lease *is* retirable by design, but the standing
instruction is never to release or retire a lease I do not own, so **I am
holding and reporting it rather than acting.** One command from the coordinator
lands it.

**2. `work/r2_1211_rubber_tracks.json` is excluded by `.gitignore:122` (`work/*`).**
`world/items/tyre_deposit.py:305` opens it at import time, and `build_surface`
imports `tyre_deposit` — so this is a **stage-1** dependency, not an item-stage
one. It is 259,915 bytes of derived deposit-field data. This is a policy
question, not a lease question: `work/` is ignored on purpose, and a
load-bearing build input living there means a fresh clone cannot build the
world. Flagging, not fixing.

**Neither blocks anything shipped.** Both files exist in the worktree,
`assembly15` was built from the worktree, and `film25` is built on `assembly15`.
The claim that is now false is only the strongest one — "a fresh clone of HEAD
reproduces the world" — and it was false before the landing too, silently.

---

## R2-3665 — WHAT `assembly15` WAS ACTUALLY BUILT FROM

`assemble.py` fingerprints 94 source files at read time. Checked both ways:

| compared against | files differing |
| --- | ---: |
| **the worktree, now** | **0 of 94** |
| **HEAD, after the landing** | **17 of 94** |

Zero against the worktree is the strong result: **the world this film is built
on is exactly what its source produces**, which is the debt film24's override
explicitly left open ("the world's staleness is a separate, open prescription
for assembly15"). That prescription is discharged.

The 17 that are still unlanded, all under `world/items/`, none of them mine:

```
??  access_road_slab_ownership.json      ??  lighting_mast.py
??  asphalt_wearing_course_ownership.json ??  lighting_mast_interface.json
??  crowd_focus_frames.json              ??  paddock_paving_bay_ownership.json
M   driver_figure.py                     M   showroom_ceiling.py
??  forecourt_paving_bay_ownership.json  ??  terrain_ground_ownership.json
??  grandstand_seats.json                ??  tree_italian_cypress.py
??  grandstand_seats.py                  ??  tree_italian_cypress_interface.json
??  gravel_bed_surface_ownership.json    ??  tree_oak.py
                                         ??  tree_scots_pine.py
```

Four of these are the tree generators behind the 28,894 `VEG` objects. They are
in the artefact and not in the repository.

---

## R2-3666 — THE BROKER THAT RENTS THE MASTER WAS RUNNING PRE-`6beb5c9` CODE

Found while preparing the cost probe, before anything was rented. **This one
would have been paid for out of the master's budget.**

`rq anim` auto-routes to the *bulk* broker on `127.0.0.1:8761`. That process was
**pid 677451, started 2026-08-04 20:20 — 101 hours old — with 14 stale files**,
`vastctl/vastctl.py` among them. Commit `6beb5c9` ("The RAM floor and the
requirement were the same number", 2026-08-08 18:05) is what introduced
`SCENE_WORKING_SET_GIB`, `RAM_HEADROOM` and `_meets_scene_working_set`, and
raised `MIN_CPU_RAM_GB` from 50.0 to 72.0. `config.py`, `fleet.py` and
`vastctl.py` are all read **at process start**.

So the broker that would have rented the card for this probe — and for the 4K
master — **had no working-set gate in it at all**, and a floor of 50 GB against
a film whose resident footprint is projected at ~59.3 GiB. That is precisely the
swap-thrash-that-presents-as-a-network-fault the commit exists to prevent.

Fixed per the documented procedure — `kill -9` the **child**, never the
supervisor, with both queues at `depth=0` so no job could be requeued:

```
kill -9 677451    # bulk broker child; supervisor 677444 untouched -> new child in 4 s
kill -9 1960091   # default broker child; supervisor 1748680 untouched -> new child in 6 s
```

`./rq drift` now reports **zero stale files** on 8760 and 8761, job history
intact (`done=81`), no instance created, credit unchanged. Offline selftest
`478/478`.

**Still stale and deliberately not restarted:** fleet brokers `fleet03`–`fleet11`
on 8762–8770 each carry the same 3 stale files including `vastctl.py`. They are
not on the probe path. **Restart them the same way before any `fleetctl up`.**

### The lesson, which is not about this broker

A long-lived daemon is a **snapshot of the code as it was when it started**. Ten
commits later every reader of the repository sees the fix and the process does
not. Nothing in the landing of `6beb5c9` was wrong; the gap is that landing a
constant does not deploy it. `./rq drift` can see this and nobody was running it.

---

## R2-3667 — THE MARKET, RE-MEASURED, AND THE BASELINE'S PRICE WAS NOT THE OFFER WE RENTED

`vastctl offers --hours 8 --disk 30`, exclusive single-GPU 5090s, today:

| x GiB (`SCENE_WORKING_SET_GIB`) | floor = x x 1.25 | offers clearing | cheapest |
| ---: | ---: | :-: | ---: |
| 50.6 (the current constant) | 63.250 | **9 / 9** | $0.454 |
| 59.3 (the ground-cover projection) | 74.125 | **9 / 9** | $0.454 |
| 62.7 | 78.375 | **9 / 9** | $0.454 |
| **73.1** | 91.375 | **8 / 9** | $0.455 |
| 91.4 | 114.250 | 7 / 9 | $0.455 |

**Both claims in the record hold, and one of them is a knife-edge.** The first
offer is lost at **x = 73.0992** (its 91.3740 GiB / 1.25) — the quoted 73.1
loses that box by **0.0008 GiB**. Do not treat 73.1 as a safe design point in
either direction.

The gap is real and **wider than recorded**: today's purchasable usable
working-set tiers are **73.10, 73.57, then nothing until 99.93**. The ~62.7 GiB
box that anchored the old note **has left the market entirely**.

**The price moved and this is the number that matters for the master:**

| | baseline (2026-08-08) | today |
| --- | ---: | ---: |
| cheapest qualifying 5090 | **$0.3689/hr** | **$0.454/hr** |

That is **+23.1 %** on the GPU-hour, before a single triangle of ground cover is
accounted for.

### And the $112.88 was never priced at $0.3689

245.5 GPU-h x $0.3689 is **$90.58**, not $112.88. The published figure was
re-priced at the enforced 72 GiB floor: $112.88 / 245.5 = **$0.4598/GPU-h**.
Comparing a new total at $0.3689 against $112.88 would book a ~20 % "saving"
that is only a different pool. `work/r23661/mastercost.py` prints both rates and
reproduces $112.90 from the baseline's own per-beat seconds, so the instrument
is calibrated against the figure it is replacing before it is used.

### The BVH premise is wrong, measured

The brief says to discard each card's first frame "which pays the BVH build".
On the baseline job `e551057645fb` the first frame's `render_sec` was
**274.66 s — BELOW the 283.3 s mean**. `render_sec` does not contain the BVH
build; that lives in the ~948 s between job creation and first-frame
completion. Discarding the leader is still right (it absorbs push, scene load
and first-fetch variance, and film25's persistent-data behaviour is unproven)
but it is **not** removing a BVH cost, and subtracting it from a *global mean*
comparison would bias the new figure low. The integration here is per-beat
against the baseline's own per-beat means, so it is like-for-like either way.

---

## R2-3668 — `film25_breach`, AND THE ONE THING THAT CHANGED

`render/film25_breach.blend`, **10,956,580,171 bytes**, built
`2026-08-09T01:34:05Z .. 02:38Z` by
`render/world/assembly/r2/v129/run_rebuild25.sh`.

**Exactly one input differs from film24: the world.** The car is the same
artefact, the sheet is the same sha, the bake is the same file, and the rig
comes out byte-identical. That is what makes the comparison worth anything.

### Provenance, hashed at build time

| input | value |
| --- | --- |
| world | `assembly15.blend` `f6e35b2169a6bace` (9,586,629,865 B) |
| car | `R2_3361_car_anim_driver_CS.blend` `0d83373eb9e9de7b` |
| **beat sheet** | `docs/beat_sheet.json` **`1abee787a8044f35`** — the live sheet |
| breach bake | `sim/out/breach_film.npz` **`3e312977987ac57a`** — film24's, re-used |
| fines library | `world/breach_fines.blend` `3c4e4124619fb9e1` |
| camera path | `render/film25_path.json` **`9d055d63da724993`** |
| pre-breach film | `render/film25.blend` 10,018,722,426 B |

### The five gates, and what each one actually asked

**0/5 `ASSEMBLY15_ACCEPTED`.** Not a summary line — all seven module `ok` flags
asserted individually, because `ok=False` on `dressing` is exactly what the
9 GB-world-missing-247-objects failure looked like. All 7 `ok=True`, all ten
prefixes exact (DR 247, ARCH 31, BR 131, CFP 676, CRF 120, SPECX 900, SURF 58,
TER 1, TS 10, VEG 28,894), 31,068 objects, and **fingerprint 0 of 94 drifted**.

**0b/5 `CAR_KEYS_MATCH_SOURCE`.** The car on disk: `0.000 m` at f1200, f2000,
f2714, f2760, f2850, f2978.

**1/5 `FILM_SCENE_BUILT`** + `CAMERA_RIG_CONTINUOUS_AND_AIMED`, strip added at
53.6725 W / radiance 47.46, sky-camera bind checked (2 parallax driver targets,
all on `ONER`).

**1b/5 `FILM_CAR_KEYS_MATCH_SOURCE` — NEW, AND NEVER RUN BEFORE.**
`check_appended_car_keys()` has only ever been run against *car* blends. The
gate at 0b asks "is the source car right"; this asks **"is the `CAR_ROOT` that
ended up inside the shipped artefact right"**, and only the second question is
about the film. `0.000 m` on all six probes, `animation_data=True`. On
`R22041` the same probe reads **678.031 m** at f2978, so this discriminates.

**2/5 `R2791_APPLY_OK`**, 621 keys, guard clean.

**3/5 `BREACH25_BUILT`.** The bake re-used, not redone, and every guard met:

| guard | want | got |
| --- | --- | --- |
| `BF_MUL05_S02` | 0.1449 | **0.1449** |
| `BF_MUL05_S00` / `S01` | ~3.93 / ~4.74 | 3.9318 / 4.7421 |
| `fines.puffs` / `animated` | 11,246 | 11,246 / 11,246 |
| `fines.tris` | 4,679,872 | 4,679,872 |
| east frame / east wall census | PASS | PASS / PASS |
| intruders over the wound, after | `[]` | **`[]`** |

The `glazing_pocket_clear` preflight FAIL is the documented `--force` case, and
it was **confirmed identical rather than assumed**: film24 and film25 both print
`found 10: [('GW_Front_Mull_14',0,4,4), ('GW_Front_Transom_0',0,6,6),
('GW_Front_Transom_1',0,6,6), ('GW_Front_Transom_2',0,6,6)]` — the same list,
object for object. The decisive check is the post-build census above, which
`--force` does not excuse.

### THE CAMERA DID NOT MOVE, AND THAT IS A RESULT

`film25_path.json` came out at **`9d055d63da724993` — film24's exact sha**, and
the per-beat comparison reads **0 of 6 beats moved**, 0.0000 m and 0.0000 mm on
every one.

Same sheet, same car, same rig builder, **different world** — and a byte-identical
rig. So the ground cover does not perturb the camera, and **film25 is directly
comparable to film24**: beat 6's hard-won before/after survives the world
change. The build refuses `363e4e88b30207ad` (film22/23's path) by name, so
"the rig did not read the live sheet" is excluded rather than hoped.

### The two files this build promised not to touch

Sha taken before and re-taken after, and a difference fails the build:

| file | before | after |
| --- | --- | --- |
| `render/film23_breach.blend` | *(recorded)* | **unchanged** |
| `render/film24_breach.blend` | *(recorded)* | **unchanged** |

---

## R2-3669 — THE PREDICTION HELD, AND IT WAS ON DISK BEFORE THE BUILD

`work/r23661/PREDICTION_film25_20260809T012914Z.log`, written **01:29:14Z**;
`render/film25.blend`'s build began **01:34:05Z**. Five minutes. The log is
committed (`195e809`, force-added past `work/*`) so the ordering is checkable in
history rather than asserted here.

`FILM25` in `tools/film_bar.py` is its own literal, re-derived from
`world/showroom_strip.py --selftest` rather than copied off `FILM24`:

```
50.0 W / luma(COLD) 0.931576              =    53.6725 W
levelled by 2**3.628 = 12.363369          =   663.5727 W
46203.313 + 663.573                       = 46866.886 W
n_lamp_stamps 23 -> 24
53.6725 / (3.60 x 0.10 x pi)              =    47.4569
```

Measured back out of the artefact, against film24 field for field:

| field | predicted | film25 | film24 |
| --- | ---: | ---: | ---: |
| `interior_lamp_watts_measured` | 46866.886 | **46866.885** | 46866.885 |
| `n_lamp_stamps` | 24 | **24** | 24 |
| `scene_mark` | 3.628 | 3.628 | 3.628 |
| `lift_multiplier` | 12.363369 | 12.363369 | 12.363369 |
| `base_watts_from_stamps` | — | 3790.786 | 3790.786 |
| `identity_base_x_lift` | — | 46866.885 | 46866.885 |
| `identity_residual_w` | — | **0.0** | 0.0 |
| `worst_per_lamp_ratio` | — | `WallWash_BackUp` 12.363369363 | identical |
| `assert_levelled` | — | **PASS** | PASS |

**All ten fields identical to film24**, and that is the result the prediction
argued for in advance: the ground cover is TER/VEG geometry, it adds +17.16 %
of traced triangles, and **it carries no lamp**. Agreement between the three
films' dicts is the expected outcome, not evidence of copying — the separate
literal is what makes a future world that *does* add an emitter fail this row
instead of silently inheriting a number nobody re-derived.

---

## R2-3670 — THE BAR: 40/40, AND THE NEGATIVE CONTROL STILL FAILS

```
  40 checks claimed | 40 OK | 0 FAIL | 0 UNMEASURABLE
>> STAGE RESULT: FILM_BAR_PASS
>> STAGE RESULT: REBUILD25_COMPLETE
```

`tools/film_bar.py --want film25 --socket`, nothing opted out.

### THE ONE THAT MATTERS FIRST

```
socket audit (film)                  rc  want rc=0   got rc=0   OK
socket audit (film10 must still FAIL) rc  want rc=1   got rc=1   OK
```

**The film10 negative control returned rc=1.** The socket instrument still
fires on the file it is known to fail on, so the 39 passes above it are worth
something. Had it returned 0 the whole bar would have been vacuous and the
instruction was to stop and say so; it did not.

### All seven sections

| section | rows | result |
| --- | :-: | --- |
| the lamps, and the levelling identity | | all OK, `identity_residual_w 0.0` |
| the strip source | | all OK, radiance 47.4569, size_y 0.10 |
| the delivery format, the oner, the clip | | 3840x2160, 24 fps, 1..2978, AgX, look None, exposure −3.628, clip 0.05/200000 |
| the stages that produced those numbers | 4 | `MEASURE_FILM_SCENE_DONE`, `FILM_EXTRA_MEASURED`, `STRIP_MEASURED`, `FILM_MATERIALS_OK` |
| the controls that have to actually execute | 3 | `rig_preflight` rc=0 + `RIG_PREFLIGHT_OK`, `slabcheck` rc=0 |
| socket_index_audit + negative control | 2 | rc=0 / **rc=1** |
| **total** | **40** | **40 OK, 0 FAIL, 0 UNMEASURABLE** |

### The row that proves landing R2-3124's `token()` fix was load-bearing

```
film materials   want FILM_MATERIALS_OK   got FILM_MATERIALS_OK (0 failures)   OK
```

On HEAD's *previous* bar that comparison is
`'FILM_MATERIALS_OK (0 failures)' == 'FILM_MATERIALS_OK'` → **False**, and the
row FAILs for being correct and informative. That is why the `film_bar.py`
landing could not be reduced to my additive hunk: a bar in history that cannot
reproduce the verdict in the record is worse than the mess it tidies.

### The measurements were film25's own, asserted from outside

The bar reads `measured_<name>.json` and judges its CONTENTS; a stale file has
perfectly good contents, so staleness is not something the bar can catch.
Asserted separately by `work/r23661/artefact_freshness.py`:

```
OK  measured_film25_breach.json   02:56:45  (+1114 s vs the blend)
OK  extra_film25_breach.json      03:12:14  (+2044 s)
OK  strip_film25_breach.json      03:15:00  (+2210 s)
OK  materials_film25_breach.json  03:16:35  (+2305 s)
OK  work/r23361 (film24's evidence) untouched
>> STAGE RESULT: ARTEFACT_FRESHNESS_OK
```

### The two films this run promised not to touch

| file | before | after |
| --- | --- | --- |
| `render/film23_breach.blend` | `642371aea6df60c1` | **`642371aea6df60c1`** |
| `render/film24_breach.blend` | `19b59635d1c394b3` | **`19b59635d1c394b3`** |

### A correction to the record about `measure_film_scene`

It was suspected of not completing, because `work/r23361/REBUILD24.log` ends at
`[gate] ... starting measure_film_scene` and never wrote another line. **The
stage completed; the LOG stopped.** film24's four artefacts are timestamped
20:25 / 20:39 / 20:40 / 20:42 against a 20:00 blend, and its bar read them to
`40 OK | 0 FAIL | 0 UNMEASURABLE`. `film25`'s run captured every line of the
same sequence. **A log that ends is not a stage that ended** — the same class
of error as judging on `$?`.

---

<!-- COST AND FOOTPRINT BELOW -->
