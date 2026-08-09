# R2-3601..R2-3660 — the "ground cover × near band" interaction does not exist

Agent `r2-3601-dressing`. Task: find and fix the interaction defect that costs
`build_dressing` its 247 objects, land the eight-path commit set, rebuild and
gate assembly15, and fix the `retire`-reports-OK defect.

**Read this first:**

1. **There is no interaction.** The ground cover is innocent and so is
   `build_nearband`. The four bisect arms differed by a variable nobody knew
   was moving: **which `blender` binary ran them.** This box has two Blender
   5.2.0 builds with the **same version string and the same build hash**, and
   they ship **different numpy versions**. The two arms that failed ran under
   `/usr/bin/blender` (numpy 2.5.1); all four arms that passed ran under
   `/opt/blender-5.2.0-linux-x64/blender` (numpy 2.3.4). (R2-3602)
2. **The code defect is real and is now fixed** — `build_dressing.station_world`
   returned rank-1 arrays for scalar input and twelve call sites did `float()`
   on them. That is a DeprecationWarning under numpy 2.3 and a hard TypeError
   under numpy 2.5. **Reproduced in 4 seconds with no terrain, no near band and
   no scene at all**, which is what proves the bisect wrong. (R2-3602)
3. **The eight-path landing is STILL blocked, on six paths, and I am holding.**
   The two the brief freed are genuinely free and I hold both. The other six are
   held by **`r2-3541-assembly15` — the previous agent's own live lease**, which
   it never released. `retire` refuses a named agent's lease by design, and the
   instruction is never to release a lease I do not own. **Six paths need one
   command from you** (R2-3604).
4. `retire` on a path that does not exist now **REFUSES**. Old behaviour
   reproduced verbatim against `HEAD`'s copy, new behaviour observed beside it.
   (R2-3603)

---

## R2-3602 — THE BISECT WAS CONFOUNDED BY THE INTERPRETER

### What the log actually said, and why it could not be numpy 2.3

The failure, verbatim from `assembly15.log`:

```
  File "/home/zany/f1-round2/world/build_dressing.py", line 747, in anchor
    wx, wy, wz = float(wx), float(wy), float(wz)
                 ~~~~~^^^^
TypeError: only 0-dimensional arrays can be converted to Python scalars
```

That message **does not exist anywhere in `/opt/blender-5.2.0-linux-x64`.** Its
numpy 2.3.4 raises `only length-1 arrays can be converted to Python scalars`,
and only for arrays of size > 1; `float(np.zeros(1))` merely warns. Observed:

| array shape | numpy 2.3.4 (`/opt`) | numpy 2.5.1 (`/usr/bin`) |
| --- | --- | --- |
| `()` | 1.0 | 1.0 |
| `(1,)` | 1.0 *(DeprecationWarning)* | **TypeError: only 0-dimensional arrays…** |
| `(1,1)` | 1.0 | **TypeError: only 0-dimensional arrays…** |
| `(2,)` | TypeError: only **length-1** arrays… | TypeError: only 0-dimensional arrays… |

The string is present on this box in exactly one place:
`/usr/lib/python3.14/site-packages/numpy/_core/_multiarray_umath.*.so`, i.e.
**numpy 2.5.1**. So the failing process was not the Blender everything else in
this project is built with.

### The two binaries

| | `/opt/blender-5.2.0-linux-x64/blender` | `/usr/bin/blender` |
| --- | --- | --- |
| version string | `Blender 5.2.0 LTS` | `Blender 5.2.0 LTS` |
| build hash | `fbe6228777e7` | `fbe6228777e7` |
| build date | **2026-07-14 01:32:04** | **2026-07-15 11:48:12** |
| python | 3.13.13 | 3.14.6 |
| **numpy** | **2.3.4** | **2.5.1** |
| size | 174,666,336 | 116,010,608 |
| how you get it | absolute path | **a bare `blender` on `PATH`** |

Same name, same version, same hash. **The only thing that separates them in a
log header is a build date, and nobody reads a build date.**

### The bisect, re-read against the binary that ran each arm

Taken from the `Blender 5.2.0 LTS (hash … built …)` line at the top of each
arm's own log, which was in the record all along:

| arm | ground cover | nearband | binary (from its log) | numpy | dressing |
| --- | :-: | :-: | --- | :-: | --- |
| assembly15 | IN | ✓ | **built 07-15 → `/usr/bin`** | **2.5.1** | **FAIL 1.1 s** |
| assembly15 rebuild | IN | ✓ | **built 07-15 → `/usr/bin`** | **2.5.1** | **FAIL 1.1 s** |
| no nearband (`asm_nonb.log`) | IN | — | built 07-14 → `/opt` | 2.3.4 | OK, 247 |
| `TERRAIN_R2970_BEFORE=1` (`gcout.log`) | OUT | ✓ | built 07-14 → `/opt` | 2.3.4 | OK, 247 |
| isolation B (`nbprobe.log`) | IN | ✓ | built 07-14 → `/opt` | 2.3.4 | OK, 247 |
| dressing probe (`dressprobe.log`) | — | — | built 07-14 → `/opt` | 2.3.4 | OK |

**The variable that separates FAIL from OK is the binary, and it separates them
perfectly — six arms, no exceptions.** The ground cover and the near band are
100 % confounded with it, which is why "either alone is fine" looked like an
interaction: the two arms that dropped an arm were also the two arms that were
launched with an absolute path.

It also explains the one result the previous agent flagged as odd — isolation B
reproducing the assembler's exact module sequence and *not* reproducing the
failure. It was not the hand-built `NEARBAND_CTX`. It was `$B`.

### The defect underneath, which is real, and reproduces in 4 seconds

```python
def station_world(s, lat, side):
    P = C.su_to_world(np.asarray(s, float), np.abs(np.asarray(lat, float)), side)
    P = np.atleast_2d(P)                       # <-- rank-1 out, even for scalar in
    return P[..., 0], P[..., 1], P[..., 2]
```

`world_contract.su_to_world` **already returns three Python floats** when both
its arguments are scalars. `station_world` pushed them through `atleast_2d` and
handed back three shape-`(1,)` arrays anyway, and all twelve scalar call sites
in `build_dressing` then wrote `float(wx)`. Under numpy 2.5 that is a
TypeError, on the **first** marshal post, 1.1 s in.

The reproduction needs no terrain, no near band, no ground cover and no scene:

```
NUMPY 2.5.1
  scalar station_world -> ndarray ndim 1
  float(wx) RAISE TypeError : only 0-dimensional arrays can be converted to Python scalars
>> STAGE RESULT: ANCHOR_FAIL
```

**That single run falsifies the interaction.** `TERRAIN_R2970_BEFORE` is unset
in it — the ground cover branch is the one under test — and there is no
`build_nearband` in the process.

### The fix

`station_world` returns what the contract returned: **scalar in, scalar out**,
and arrays only when it was given arrays (the one call site at
`build_dressing.py:4999` that passes vectors keeps its arrays, checked). The
control was observed to fail before it was trusted, and after the fix:

| arm | numpy 2.3.4 | numpy 2.5.1 |
| --- | --- | --- |
| `station_world` scalar arm returns | `float` ndim 0 | `float` ndim 0 |
| `station_world` array arm returns | shape `(5,)` | shape `(5,)` |
| `anchor()` on all 24 planned marshal posts | 0 raised | **0 raised** (was 24) |
| `build_dressing.build()` standalone | **247 objects** | *see R2-3605* |

`anchor("post01", …)` returns the identical
`(449.5424456801129, 242.1665445219794, -0.3267031277527681, 21.807978221131346)`
under both numpys, so this is a type fix and not a numeric one.

### And the binary is now pinned, because the code fix is not the whole defect

Fixing `station_world` fixes the crash that happened. It does not fix the thing
that made a two-day defect hunt land on the wrong suspect: **a build can select
a different interpreter by accident and the artefact does not say so.**
`assemble.py` catches every module exception and saves the blend regardless — by
design, so one broken module still leaves a probeable world — so the whole
symptom was a 9 GB world silently missing its ad boards, tyre stacks,
flagpoles, marshal posts and TV cameras, and one line in a 4,000-line log.

`tools/buildlock.sh` is the choke point every heavy build in this project
already passes through, so the pin went there: any argument whose basename is
`blender` must resolve to the reference binary, or the build is **refused**
before it starts. `R2_ALLOW_ANY_BLENDER=1` is the out-loud escape hatch for
deliberately testing the other one. Five controls, all observed:

| control | expected | observed |
| --- | --- | --- |
| bare `blender` | REFUSED | `BUILDLOCK REFUSED (wrong Blender)`, names both paths |
| `/usr/bin/blender` | REFUSED, command never runs | refused; the payload printed nothing |
| `R2_ALLOW_ANY_BLENDER=1 /usr/bin/blender` | warns, runs | `WARNING … Allowed because R2_ALLOW_ANY_BLENDER=1`, payload ran |
| `/opt/…/blender` | untouched | ran |
| `/usr/bin/python3` (not blender at all) | untouched | ran |

**The right long-term home for this is `assemble.py`**, which should record the
interpreter and numpy version in `<blend>_build.json` and in the scene next to
`world_source_sha256` — a fingerprint over 94 source files that says nothing
about the interpreter answers "would a rebuild be this file?" with a yes it has
not earned. `assemble.py` is held by `r2-3541-assembly15` (R2-3604), so it is
proposed, not done.

---

## R2-3603 — `retire` ON A PATH THAT DOES NOT EXIST NOW REFUSES

The defect, reproduced against `HEAD`'s own copy of the file in a throwaway
repo with a 30 h stale seed holding `world/itemkit.py`, asked for the brief's
typo `world/items/itemkit.py`:

```
######## HEAD's gitguard ########
  nothing selected.  Name a path, or --owner <seed> [--all-paths].
>> STAGE RESULT: OK (0 retired, nothing selected)
rc=0
```

```
######## after this change ########
  REFUSED -- 1 path(s) that do not exist, and are held by no lease:
    world/items/itemkit.py
        did you mean:  world/itemkit.py
  Retiring a path that does not exist frees nothing.  Reporting
  OK for it is how a landing stays blocked while the record says
  it was unblocked (R2-3603).  Check the path and run it again.
>> STAGE RESULT: FAIL (0 retired, 1 nonexistent path(s))
rc=2
```

Two halves, because there are two ways to succeed at doing nothing:

* **A named path that no lease mentions, that is not on disk, and that git has
  never heard of, is a typo.** REFUSED, rc 2. It also offers the paths whose
  basename matches, which is what turns a refusal into a repair.
* **Named paths that exist but no seed holds** are no longer `OK` either:
  `FAIL (0 retired, N path(s) held by no retirable lease)`. A bare `retire`
  with no paths is still `OK` — that one is a listing, and nothing was asked
  for.

`holds()` is consulted in both directions first, so a path a seed covers via a
broader directory entry is still "known" and still gets the existing, correct
`SKIPPED … retire removes entries; it does not split them` message.

Five controls added to `tools/gitguard_selftest.py`, including a vacuity arm so
the refusal cannot be blanket:

```
PASS C16o a retire aimed at a NONEXISTENT path REFUSES     want=(2, True, False) got=(2, True, False)
PASS C16p and it names the path it thinks you meant        want=True  got=True
PASS C16q the refusal left the seed exactly as it was      want=['world/items/keep.py', 'world/itemkit.py'] got=[same]
PASS C16r VACUITY: the corrected path still retires normally want=(0, ['world/items/keep.py']) got=(0, [...])
PASS C16s a real path that NO SEED HOLDS is not an OK either want=(2, True, False) got=(2, True, False)
>> STAGE RESULT: OK (0 failures of 67 checks)
```

---

## R2-3604 — THE LANDING IS BLOCKED ON SIX PATHS, BY THE PREVIOUS AGENT'S LEASE

The brief's two paths are genuinely free and are now mine. The other six are
not free and never were: **`r2-3541-assembly15` claimed them during its own run
and its lease is still LIVE** (age 3.0 h, ttl 24 h). Asked of the lease store,
one path at a time:

| path | result |
| --- | --- |
| `world/itemkit.py` | **CLAIMED** |
| `world/items/tyre_deposit.py` | **CLAIMED** |
| `world/build_items.py` | **CLASH** — `r2-3541-assembly15` |
| `world/build_barriers.py` | **CLASH** — `r2-3541-assembly15` |
| `world/items/PLACEMENT.json` | **CLASH** — `r2-3541-assembly15` |
| `world/items/spectator_crowd_world.py` | **CLASH** — `r2-3541-assembly15` |
| `world/build_nearband.py` | **CLASH** — `r2-3541-assembly15` |
| `render/world/assembly/r2/assemble.py` | **CLASH** — `r2-3541-assembly15` |

`retire` refuses a named agent's lease categorically (S1, no `--force`), which
is correct and should stay that way, and the standing instruction is never to
release a lease I do not own. **So I am holding, and the previous agent's own
argument still stands: all eight or none.**

**One command from the lease's owner unblocks it:**

```
R2_AGENT=r2-3541-assembly15 tools/gitguard.py release \
    world/build_items.py world/build_barriers.py world/items/PLACEMENT.json \
    world/items/spectator_crowd_world.py world/build_nearband.py \
    render/world/assembly/r2/assemble.py
```

Worth naming the shape: **an agent's lease outlives the agent.** A seed lease
has `retire`; a named lease has nothing but its 24 h TTL and its owner, and the
owner is gone. Every finished agent leaves its paths locked for a day. That is
the third distinct way this landing has been blocked, and unlike the first two
it is structural.

### The buildability probe, run again, both arms, on the REFERENCE binary

The instruction is to require the positive control before spending 22 minutes.
Done, with one correction to the record first: **the R2-3542 run of this probe
was itself launched with `/usr/bin/blender`** (`probe_WT.log` line 2, built
2026-07-15) — the binary that breaks the build — **and it passed.** It passes
because it stops at `build_surface`, four stages before `build_dressing`. A
probe that green-lights a 22-minute assembly cannot be blind to the thing that
breaks the assembly, and this one was.

Re-run today on `/opt/blender-5.2.0-linux-x64/blender`:

```
>> STAGE RESULT: HEAD     SOURCE_UNBUILDABLE (5 of 5 probes failed)
>> STAGE RESULT: WORKTREE SOURCE_BUILDABLE   (0 of 5 probes failed: none)
```

HEAD's five are unchanged and each was observed: `build_nearband`
ModuleNotFoundError, `itemkit.detail_for` / `itemkit.assert_wired`
AttributeError, `build_items.class_feature_owned_at` AttributeError,
`tyre_deposit` ModuleNotFoundError. **HEAD does not build because the landing is
blocked (R2-3604); the worktree — which is the tree the assembler actually
reads — does, with the positive control observed.**

---

## R2-3605 — THE REBUILD: 247 OBJECTS BACK, AND NOTHING ELSE MOVED

Built under `tools/buildlock.sh` from the worktree, ground cover **IN**
(`TERRAIN_R2970_BEFORE` unset), near band **IN**, full seven-module sequence,
on the reference binary:

```
[ASM] surface:      ok=True  43.5s   58
[ASM] barriers:     ok=True  49.3s   189
[ASM] architecture: ok=True  90.8s   220
[ASM] terrain:      ok=True 729.3s   28,745
[ASM] nearband:     ok=True 176.4s   29,115
[ASM] dressing:     ok=True 103.4s   29,362      <-- was ok=False 1.1s, 29,115
[ASM] items:        ok=True 104.5s   31,068
>> STAGE RESULT: ASSEMBLE_OK
```

**`dressing` reaches 29,362 — assembly14's exact post-dressing count — with the
ground cover IN and the near band IN.** That is the arm the bisect said was
impossible.

### Nothing is lost. The number is zero.

Per-prefix census, assembly14 against the rebuilt assembly15, from the two
`_build.json` reports:

| prefix | assembly14 | assembly15 | delta |
| --- | ---: | ---: | ---: |
| ARCH | 31 | 31 | 0 |
| BR | 131 | 131 | 0 |
| CFP | 676 | 676 | 0 |
| CRF | 120 | 120 | 0 |
| **DR** (dressing) | **247** | **247** | **0** |
| SPECX | 900 | 900 | 0 |
| SURF | 58 | 58 | 0 |
| TER | 1 | 1 | 0 |
| TS | 10 | 10 | 0 |
| VEG | 28,894 | 28,894 | 0 |
| **total objects** | **31,068** | **31,068** | **0** |
| total meshes | 4,247 | 4,247 | 0 |
| total materials | 181 | 181 | 0 |
| blend | 9,132.9 MB | 9,142.5 MB | +9.6 MB |

**Every prefix matches to the object.** The 247 dressing objects are back in
full: 24 marshal posts, 515 barrier ad boards, 128 fence banners, 9 billboards,
119 tyre stacks, 12 flagpoles, 13 TV cameras, 46 gullies, 65 junction boxes,
1,015 ground anchors registered. assembly15 is assembly14's object graph
**plus** the ground cover, which is exactly what the pass was supposed to buy.

`render/world/assembly/r2/assembly15.blend`, 9,586,629,865 bytes, sha256
`f6e35b2169a6bacebdf9427018d3c588f47b2cf884c4901e8c80992aaec22c2f`.

---

## R2-3606 — THE GATES, NOW THAT THEY ARE PASSES THE WORLD HAS EARNED

The previous agent withheld `placement_gate`, z-fight and the socket blend arm
because a CLEAN from a world with no ad boards, tyre stacks or marshal posts is
not a verdict. That judgement was right and the withholding is now discharged:
**the 247 objects are in the world these gates were run on.**

Same instrument, same reference binary, both worlds, `placement_gate` and
`probeG` and the socket audit **re-measured on assembly14 today** rather than
quoted:

| gate | assembly14 | assembly15 (rebuilt) | verdict |
| --- | --- | --- | --- |
| `placement_gate` | **`PLACEMENT_CLEAN`, 0** (+1,203 hidden on 894 non-rendering meshes) | **`PLACEMENT_CLEAN`, 0** (+1,203 hidden on 894 meshes) | **PASS — identical, and earned** |
| closest approach, car_path | `BR_Concrete_L12` **+4.608 m** | `BR_Concrete_L12` **+4.608 m** | identical (and = `SHIPPING.md:512`) |
| closest approach, camera_path | `BR_Verge_R` +0.648 m | `BR_Verge_R` +0.648 m | identical |
| closest approach, road_corridor | `ARCH_Gantry` +1.149 m | `ARCH_Gantry` +1.149 m | identical |
| z-fight (`probeG`) | 0 coplanar columns of 41; `NO_COPLANARITY`; scan keys **present** | 0 of 41; `NO_COPLANARITY`; keys present | **identical, line for line** |
| z-fight controls | 0 mm → 144/144, 1 mm → 144/144, 50 mm → 0/144 | same | **3/3 PASS both worlds** |
| socket, **blend** arm | **PASS**, 233 trees, no Bump driving Filter Width | **PASS**, 233 trees | identical |
| triangle budget — RENDERED | 15,099,440,337 ¹ | **17,691,299,239** | **+17.16 %** |
| triangle budget — INSTANCES | 13,842,597,953 ¹ | 16,434,456,855 | +18.72 % |
| EVALUATED | 1,256,842,384 / 30,204 objs ¹ | **1,256,842,384 / 30,204 objs** | **IDENTICAL** |
| BASE | 123,307,968 / 3,445 meshes ¹ | 123,422,404 / **3,445 meshes** | +114,436 tris, mesh count identical |
| variety — realized instances | 4,966,913 ¹ | **4,966,913** | **IDENTICAL** |
| variety — distinct sources | 1,569 ¹ | **1,569** | **IDENTICAL** |
| variety — VEG / SPECX split | 823 / 746 ¹ | **823 / 746** | **IDENTICAL** |
| variety — top share, gini | 2.03 % ¹ | **2.0 %, gini 0.867** | unchanged |
| `instance_variety` verdict | clean ¹ | **`INSTANCE_VARIETY_CLEAN`** | **PASS**, no family past 40 % |
| ground cover present | absent | **`GROUNDCOVER PRESENT` — 32 of 32 clumps carry panicle geometry** | as intended |
| total objects | 31,068 | **31,068** | **IDENTICAL** |

¹ measured by `r2-3541` earlier the same day with the same tool on the same
reference binary (`poly_census`, `instance_variety`); the assembly14 blend has
not changed since, and I did not re-run those two 19-minute censuses. Every
other assembly14 row above I measured myself today.

**The instrument was observed to fire before any of this was believed.**
`placement_gate --selftest`: `all 60 controls behaved`, including the positive
ones that must fire (`a PLAIN object 0.20 m into the car path is a violation
fires=True expected=True`) → `PLACEMENT_SELFTEST_OK`. `probeG` carries its own
three controls and all three passed on both worlds — and, per its own history,
the two scan **keys are present** rather than absent, which is the failure mode
that once read as "fine".

### The one gate that is not a world gate

`winding_audit` is a per-item sweep, not a whole-world verdict. Its subject is
unchanged in every respect that matters: the item generators and
`world/items/PLACEMENT.json` are byte-identical to the ones assembly14 built
from, and the item object counts land on assembly14's to the object (`CFP` 676,
`CRF` 120, `SPECX` 900, `TS` 10). A sweep over the collection that actually
changed — the 247 dressing objects — is reported in R2-3607.

### Nothing regressed on any gate. The answer to "what does it still lose" is 0.

assembly15 matches assembly14 on **every** gate, matches it object for object,
mesh for mesh and material for material, and adds **+17.16 %** of traced
triangles as ground cover. Against the market measurement that is already
settled (R2-3544/45: the film goes 50.6 → ~59.3 GiB, needs a 74.1 GiB card, and
the same seven offers clear it; the first offer is not lost until +44.5 %),
**assembly15 is a ship candidate and assembly14 is superseded.**

---

## R2-3607 — TWO CLOSING MEASUREMENTS

### The winding sweep over the collection that actually changed

`winding_audit --collection R2_Dressing --rays 600`, run on both worlds. This
is the sweep whose subject is the 247 objects that came back, and it is
**bit-identical across all 21 metrics**:

| metric | assembly14 | assembly15 |
| --- | ---: | ---: |
| objects / pieces | 234 / 83,392 | 234 / 83,392 |
| faces / triangles | 3,033,086 / 4,279,866 | 3,033,086 / 4,279,866 |
| inward pieces / faces / triangles | 33,172 / 1,284,660 / 1,652,976 | 33,172 / 1,284,660 / 1,652,976 |
| `inward_area_frac` | 0.42354882123355553 | **0.42354882123355553** |
| `inconsistent_edges`, `mirrored_by_matrix`, `flipped` | 0, 0, 0 | 0, 0, 0 |
| ray arm: hits / back / fraction | 600 / 84 / 0.14 | 600 / 84 / 0.14 |

Seventeen significant figures of agreement on `inward_area_frac` is the
strongest available statement that **the fix is a type change and not a
numeric one**: the dressing geometry assembly15 contains is the geometry
assembly14 contained, to the bit. (`anchor("post01", …)` also returns the same
four numbers to the last digit under both numpys — R2-3602.)

The standing `inward_area_frac` of 0.42 is a **pre-existing** property of these
meshes and of the idioms they are built from, unchanged by anything here, and
is not a regression to attribute to this pass.

### `build_dressing` is now clean under the numpy that broke it

Not merely at the crash site — the whole stage:

```
NUMPY 2.5.1 BLENDER 5.2.0 LTS b'2026-07-15'
DRESSING objects_added=247  ok=True  52.5s
>> STAGE RESULT: DRESSONLY_OK (247 objects)
```

So the one `station_world` return was the module's only dependence on the
removed deprecation. The build still ships on `/opt` — that is the binary this
project's entire artefact history was produced with, and changing it is a
separate decision with its own evidence — but the module no longer breaks if
somebody picks the other one, and `tools/buildlock.sh` now stops them picking
it by accident.

---

## R2-3608 — WHAT I AM RECOMMENDING, AND WHAT I AM HOLDING

**Ship assembly15.** It is assembly14's world object-for-object with the ground
cover added, it passes every gate assembly14 passes with numbers that are
identical or better, and the cost question was settled at R2-3544/45 and is not
reopened by anything here.

**The eight-path landing is still not landed and it is not mine to unblock**
(R2-3604). Six paths sit under `r2-3541-assembly15`'s live lease. One `release`
from that owner, and the set goes in as one commit.

**What landed here instead** — five paths, all held under `r2-3601-dressing`,
none of them among the eight:

| path | change |
| --- | --- |
| `world/build_dressing.py` | `station_world` returns scalars for scalar input (R2-3602) |
| `tools/buildlock.sh` | refuses a build launched with a non-reference `blender` (R2-3602) |
| `tools/gitguard.py` | `retire` refuses a nonexistent path instead of reporting OK (R2-3603) |
| `tools/gitguard_selftest.py` | five controls for it, including a vacuity arm (R2-3603) |
| `docs/STAGING-R2-3601-to-R2-3660.md` | this file |

**Proposed for `docs/DEFECT-LOG-R2.md`** (not written there — that file is
merged by the coordinator):

1. **Two Blender binaries with the same version string and hash and different
   numpys.** Cost: one bisect that reached a confident wrong conclusion about
   two innocent modules, and a 9 GB artefact that lost 247 objects silently.
   Detection: the build-date line nobody reads. Now pinned at `buildlock.sh`.
2. **`station_world` returned rank-1 arrays for scalar input** and twelve call
   sites `float()`-ed them, depending on a numpy deprecation that is already an
   error in the wild.
3. **`retire` on a nonexistent path reported OK.** Fixed, with controls.
4. **An agent's lease outlives the agent.** A seed lease can be retired; a
   named lease can only be released by an owner who no longer exists, or waited
   out for 24 h. Three landings have now been blocked by lease bookkeeping and
   this is the only one of the three with no mechanism at all.
5. **The `SOURCE_BUILDABLE` probe stops at `build_surface`,** four stages before
   the one that broke, so it green-lit the assembly that failed — and it was
   itself run on the wrong binary while doing so.
6. **`assemble.py` fingerprints 94 source files and not the interpreter.** It
   should record Blender's build hash + date and `numpy.__version__` beside
   `world_source_sha256`. Held by `r2-3541-assembly15`; proposed, not done.

