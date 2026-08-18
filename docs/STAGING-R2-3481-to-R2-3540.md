# STAGING R2-3481 .. R2-3540 — assembly15 cannot be built, because committed source does not build at all

The task was: build `assembly15` from committed source and prove it reproduces.

**It cannot be built.** Not "it built and a gate regressed" — the committed tree
does not produce a world. Six independent breaks, every one of them observed
rather than inferred, and one of them is that **the assembler which records the
fingerprint is itself uncommitted**.

The drift is also not two modules. It is **six of the ten** `assemble.py`
stamps, plus four load-bearing inputs the fingerprint does not cover at all.

**No world was built. No gate was run. No source was committed.** The landing
that would fix this is blocked on a lease I do not own (§5).

---

## R2-3481 — THE DRIFT LIST: SIX OF TEN, AND THE FINGERPRINT IS HONEST

`assembly14_build.json` records a sha256 for each of the ten modules
`_source_fingerprint()` enumerates. Held against `HEAD` and against the working
tree:

| module | assembly14 | HEAD | worktree | verdict |
| --- | --- | --- | --- | --- |
| `world/build_architecture.py` | `7e78c253` | `7e78c253` | `7e78c253` | match |
| `world/build_dressing.py` | `f5d4cc5d` | `f5d4cc5d` | `f5d4cc5d` | match |
| `world/build_sky.py` | `1fbe8ff6` | `1fbe8ff6` | `1fbe8ff6` | match |
| `world/world_contract.py` | `dd4acd11` | `dd4acd11` | `dd4acd11` | match |
| `world/build_surface.py` | `678fdb3f` | `9b5d6fb2` | `9b5d6fb2` | **DRIFT** — HEAD ahead, 29+/3−, a14's state is committed at `45543535` |
| `world/build_terrain.py` | `991b15a0` | `d09ac2a8` | `d09ac2a8` | **DRIFT** — a14's state is in **no commit and nowhere on disk** |
| `world/build_barriers.py` | `2d435466` | `9adcb1d9` | `2d435466` | **DRIFT** — **HEAD is BEHIND**; a14 == worktree, 16+/1− uncommitted |
| `world/build_items.py` | `fbf7bc1e` | `0fbb6e94` | `fbf7bc1e` | **DRIFT** — **HEAD is BEHIND**; 287+/11− uncommitted |
| `world/itemkit.py` | `41ec66bc` | `0f12b3c3` | `41ec66bc` | **DRIFT** — **HEAD is BEHIND**; 442+/1− uncommitted |
| `world/build_nearband.py` | `3fa0729a` | *absent* | `3fa0729a` | **DRIFT** — **untracked; there is no committed source** |

`world/build_rig_filmpose.py` is stamped by HEAD's rule but not by a14: it
postdates the build (`d9c160d`).

**The fingerprint is trustworthy, and that was checked rather than assumed.** A
chunked byte scan of `assembly14.blend` finds `world_source_sha256`,
`world_source_read_utc` and the string `991b15a0…eec3f` each present exactly
once in the artefact. The sidecar and the copy welded into the scene agree, so
the table above is the world's own account of itself.

*(Instrument note: plain `grep -c` on the 8.9 GB blend returned nothing at all
and exit 1 — a file with no newlines defeats it. The count above is a chunked
`bytes.count` scan. Do not use `grep` to interrogate a blend.)*

### The direction of the drift is the surprise

Two modules drifted the way the brief expected — `surface` and `terrain` moved
*forward* and HEAD carries work a14 never saw. **Three moved the other way.**
`barriers`, `items` and `itemkit` are the state a14 read, and **HEAD is 745
lines behind them**. Building "from committed source" would not pick up newer
work on those three; it would *throw away* the class-feature-ownership arm
(R2-227/R2-331) and the itemkit guards, both of which are in the ship.

### assembly14's terrain source is gone

`991b15a0…` was searched for across all 4 commits that touch the file on every
ref, and across all 3,829 python files under the repo. **Not found.** The other
five a14 states are all still recoverable (four in the worktree, `surface` at
`45543535`). Terrain is not.

`assembly13` read the *same* terrain source and its terrain summary is identical
to a14's on every key but `build_s`, so the two ships cannot be differenced to
recover what it contained either.

**`assembly14` is permanently unreproducible.** That is not fixable by any
action available now; it can only be superseded.

---

## R2-3482 — HEAD DOES NOT BUILD. SIX BREAKS, OBSERVED

Same probe, same Blender, same data files, two source trees — HEAD extracted
via `git archive`, and the working tree in place.

```
>> STAGE RESULT: HEAD     SOURCE_UNBUILDABLE (5 of 5 probes failed)
>> STAGE RESULT: WORKTREE SOURCE_BUILDABLE   (0 of 5 probes failed)
```

The positive control matters: the probe passes 5/5 on the worktree, so the
failures below are HEAD's and not the instrument's.

| # | break at HEAD | stage it kills |
| --- | --- | --- |
| 1 | `world/build_nearband.py` — `ModuleNotFoundError` | `nearband` |
| 2 | `itemkit.detail_for` missing; `build_terrain` calls it at ~40 sites | `terrain` |
| 3 | `itemkit.assert_wired` missing; `build_surface` calls it | `surface` |
| 4 | `build_items.class_feature_owned_at` missing; **`build_architecture` calls it and that module is byte-identical at a14, HEAD and worktree** | `architecture` |
| 5 | `build_surface` imports `tyre_deposit` → `world/items/tyre_deposit.py` is **untracked** | `surface` |
| 6 | `world/items/PLACEMENT.json` at HEAD marks **1** row PLACE, worktree marks **4** | `items` |

Break 4 is the sharpest: a *fully committed, undrifted* module calls into an API
that exists only in an uncommitted file. Break 6 is the quietest — it would not
crash, it would silently build a world missing `CFP` 676, `SPECX` 900 and `TS`
10, i.e. **1,586 objects**, and report success.

### The assembler itself is uncommitted — this is the root of the family

`render/world/assembly/r2/assemble.py` is dirty by 91+/2−, and HEAD's version:

* has **no `_source_fingerprint()` at all**, and
* has **no `nearband` stage** in `MODS`.

So even if every break above were fixed, a build from committed source would
produce a six-module world **carrying no fingerprint** — the deliverable
"show assembly15 matches HEAD on every module" is not merely failing, it is
**unproducible from the record**. The R2-1822 mechanism that exists to make
artefacts attributable was never itself committed.

### Four load-bearing inputs the fingerprint does not cover

`_source_fingerprint()` enumerates `world/*.py` matching `build_*`,
`world_contract.py`, `itemkit.py`. It therefore says nothing about
`assemble.py`, `world/items/PLACEMENT.json`, or any `world/items/*.py` — and the
`items` stage's entire behaviour is decided by exactly those. A world can differ
from another by 1,586 objects with an identical fingerprint.

---

## R2-3483 — THE GROUND COVER IS **NOT** IN assembly14

Asked of the datablocks, not the source — which is the only way to ask it, since
a14's terrain source no longer exists.

`world/build_terrain.py` carries its own A/B switch, `TERRAIN_R2970_BEFORE`
(module scope, R2-2970). Running the module's **own generators** in both arms
gives a reference signature; `assembly14.blend` was then linked read-only and
held against it.

| signature | BEFORE (pass OUT) | AFTER (pass IN) | **assembly14** |
| --- | --- | --- | --- |
| grit `sharp_face` — flat/smooth | **0 / 12** | 12 / 0 | **0 / 24** |
| fescue hero, `verts/polys == 1.75` exactly | **11 / 11** | 0 / 11 | **11 / 11** |
| tussock hero, `verts/polys == 1.75` exactly | **11 / 11** | 0 / 11 | **11 / 11** |
| fescue hero polys | 2532–3816 | 2885–4317 | 2400–3900 |
| tussock hero polys | 2484–3864 | 3506–5657 | 2424–3840 |

`verts/polys == 1.75` exactly is the discriminator, and it is structural rather
than statistical: a hero clump is `blades × 12` polys and `blades × 21` verts of
ribbon and nothing else. A panicle is built from tubes, so **any** clump
carrying one breaks the ratio. In the AFTER arm 0 of 11 clumps hold it. In
assembly14, **22 of 22 hold it exactly.**

**Verdict: the shipped world has no panicle on any fescue or tussock clump, and
its grit is smooth-shaded with no cleavage planes.** `film24_breach` is built on
that world, so the delivered film does not contain the ground-cover pass either.

This also settles the provenance question: a14's lost `991b15a0` is a
**pre-ground-cover** terrain, and `9bfd9a5`'s 1,101-line landing is (at least)
the pass a14 never saw.

### The triangle cost is more than double the figure on the ticket

Measured from the generator, mean over 11 hero clumps per kind:

| kind | BEFORE | AFTER | cost |
| --- | --- | --- | --- |
| fescue | 3013 | 3435 | **+14.0 %** |
| tussock | 3372 | 4894 | **+45.1 %** |
| both | 3193 | 4165 | **+30.5 %** |

The **+13.9 %** on the ticket is the *fescue* number. Tussock's panicle fraction
is `seed=0.45` against fescue's `0.15`, so it costs three times as much, and the
brief's figure understates the pass by more than 2×.

**Say the number, as asked.** Applying +30.5 % to the ~10.9 G hero-grass share
of assembly14's 16.31 G evaluated triangles:

```
hero grass   10.9 G  ->  14.2 G
total        16.31 G ->  19.63 G evaluated   (+20.4 %)
instanced    15.12 G ->  18.44 G
```

**~19.6 G evaluated is a render-threatening number** and it is the first thing
to measure on a real assembly15, not the last. The other grass kinds
(`meadow` 0.55, `dry` 0.10, `reed`, …) also lose their panicles in the BEFORE
arm, so the whole 55-mesh library moves and the true total may be higher than
this fescue/tussock extrapolation.

---

## R2-3484 — GATE VERDICTS: NONE, AND WHY THAT IS THE HONEST ANSWER

`placement_gate`, the variety census, the triangle budget, and the z-fight,
winding and socket audits all take a world. **No assembly15 exists**, so there
is nothing to gate. Recording "not run" rather than carrying assembly14's
numbers forward under a new name:

| gate | assembly14 (baseline) | assembly15 |
| --- | --- | --- |
| `placement_gate` | `PLACEMENT_CLEAN, 0` (`SHIPPING.md:512`, after `2247a4d`/`ea54e51`) | **NOT RUN — no world** |
| variety | 1,569 sources / 4,966,913 instances / top 2.03 % | **NOT RUN — no world** |
| triangle budget | 15.12 G instanced, 16.31 G evaluated | **NOT RUN** (predicted ~19.6 G, R2-3483) |
| z-fight / winding / socket | passed | **NOT RUN — no world** |

No gate regressed, because no gate ran. Nothing here is worse than assembly14
on a measured gate; the finding is one level below that.

---

## R2-3485 — WHAT A film25 WOULD DIFFER BY, BEYOND THE GROUND COVER

For beat 6's comparison against `film24_breach`:

1. **`build_surface` +29/−3** (`298ab63`, `95abe8c`, `12104cf`) — the R2-3061
   asphalt re-budget and the R2-3066 octave revert. a14 predates all three.
   **This changes the asphalt shader under every frame** and is not the ground
   cover.
2. **`build_terrain`, unbounded and unknowable.** `9bfd9a5` landed 1,101
   insertions / 71 deletions. a14 sat somewhere inside that range and its exact
   state is gone, so **the terrain delta between a14 and HEAD cannot be
   bounded** — only the ground-cover part of it has been identified, from the
   artefact. Anything else in those 1,101 lines will arrive in film25 unannounced.
3. **Items: no delta *if* the landing is done correctly.** a14 == worktree on
   `build_items`/`itemkit`/`barriers`/`PLACEMENT.json`. But a naive build from
   *current* HEAD drops 1,586 objects (R2-3482 break 6) — that would move beat 6
   hard and for the wrong reason.

Item 2 is the one that puts beat 6's comparison at risk, and no amount of care
in building assembly15 recovers it.

---

## R2-3486 — BLOCKED: THE LANDING NEEDS A LEASE I DO NOT OWN

Making HEAD buildable means committing the state a14 actually read, plus the
assembler. The set, and its lease position:

| path | why | lease |
| --- | --- | --- |
| `world/itemkit.py` | breaks 2, 3 | `inflight-2026-08-07` **CLASH** |
| `world/build_items.py` | break 4 | `inflight-2026-08-07` **CLASH** |
| `world/build_barriers.py` | calls `class_feature_owned` | `inflight-2026-08-07` **CLASH** |
| `world/items/PLACEMENT.json` | break 6 | `inflight-2026-08-07` **CLASH** |
| `world/items/spectator_crowd_world.py` | untracked PLACE row | `inflight-2026-08-07` **CLASH** |
| `world/items/tyre_deposit.py` | break 5 | free |
| `world/build_nearband.py` | break 1 | `inflight-auto` (yields to a claim) |
| `render/world/assembly/r2/assemble.py` | fingerprint + nearband stage | `inflight-auto` (yields to a claim) |

Five of eight are held by `inflight-2026-08-07`, a 22.5 h seed that
`gitguard status` labels `[STALE SEED -- retirable]`. **I did not retire it.**
The instruction for this task is to never retire a lease I do not own, and to
hold and surface it — so that is what this is. `claim` against it returns CLASH
and points at `retire`; nothing else clears it.

**I also did not land the two free paths.** Committing `assemble.py` and
`build_nearband.py` alone would leave HEAD still unbuildable while making it
*look* repaired — the next agent would read a committed assembler with a
fingerprint in it and reasonably assume the tree builds. This landing is only
correct as one set.

`world/build_surface.py` is held by `r2-3061-asphalt` (named, 3.9 h, never
retirable) — but it needs no commit: HEAD already equals the worktree there.

---

## What is needed to unblock

1. Clear or reassign `inflight-2026-08-07` for the five paths in R2-3486.
2. Land all eight as one commit set, `R2_AGENT` set on the commit itself,
   `git add` path-scoped.
3. Re-run the R2-3482 probe and require `SOURCE_BUILDABLE` **before** spending a
   ~22 min assembly.
4. Then build assembly15 under `tools/buildlock.sh`, re-fingerprint, and gate.
   Expect ~9.6 GB (120 GB free — headroom is fine) and check the triangle total
   against the ~19.6 G prediction in R2-3483 first.

Nothing in the above needs rendering, and none was done.
