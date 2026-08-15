# STAGING R2-3961 to R2-4020

## R2-4020 — THE SWEEP AFTER THE GITIGNORED BUILD INPUT, AND FOUR MEASUREMENT PASSES THAT RAN OUTSIDE THE LOCK

Two defects, both local, neither touching the master render. The 4K master was
live on three rented 5090s throughout and nothing here went near it, its
brokers, its jobs or any instance. One heavy Blender pass was run, under
`tools/buildlock.sh` like everything else, and it is the measurement Part 2
rests on.

---

# PART 1 — THE SWEEP (task #164)

`work/r2_1211_rubber_tracks.json` was found gitignored and force-added. The
question this part answers is **what else is in that position**.

## The method, and why extension-grepping would have missed it

The known defect could not be found by looking for JSON files. It hid because
`world/items/tyre_deposit.py` does this **at module scope**:

```python
TRACKS_JSON = os.path.join(_ROOT, "work", "r2_1211_rubber_tracks.json")   # L295
def _tracks(): ...  json.load(open(TRACKS_JSON))                          # L304-305
TR = _tracks()                                                            # L308  <-- top level
```

`TR = _tracks()` is an ordinary-looking assignment. The `open()` is one call
away, and it fires on `import tyre_deposit` — which `world/build_surface.py`
does at L2809, making the file a **stage-1 dependency of the world build**.

So the sweep was done twice, from both ends:

1. **Import-graph walk** from `assemble.py`, `world/build_surface.py` and
   `tools/build_film_scene.py`, resolving the runtime `sys.path` inserts
   (`world/`, `world/items/`, `tools/`) — without those, `import tyre_deposit`
   does not resolve at all and the known defect is invisible. **19 modules**
   in the transitive closure; every literal path passed to `open`, `json.load`,
   `np.load`, `csv.DictReader`, `bpy.data.libraries.load`,
   `bpy.ops.wm.open_mainfile` and `bpy.data.images.load` collected.
2. **An AST pass over the whole repo** for *module-scope* reads, including the
   one-level indirection above (a top-level statement calling a module-level
   function that contains an `open`). **474 module-scope read sites**;
   filtering the `list.append` collisions leaves the table below.

**The method was calibrated before it was trusted**: the AST pass reports
`world/items/tyre_deposit.py 308 INDIRECT via _tracks() load,open`. It finds
the known defect, so it is allowed to be believed about the rest.

Each surviving path was then asked the two questions: **is it tracked**, and
**if it vanished, what regenerates it**.

## Everything the build opens, and its verdict

### Read at IMPORT time (hard dependency of an `import` statement)

| path | opened by | tracked? | verdict |
| --- | --- | --- | --- |
| `docs/circuit_spec.json` | `world_contract.py:339` (direct), `build_barriers.py:83`, `build_dressing.py:74` | **tracked** | clear |
| `docs/item_manifest.json` | `world/items/heras_fence_panel.py:268` via `_manifest_record()` | **tracked** | clear |
| `docs/circuit_spec.json` | `world/items/dais_delivery_ramp.py:218` via `_spec_dais()` | **tracked** | clear |
| `telemetry/telemetry.csv` | `tyre_deposit.py:380` via `_film_profile()` | **tracked** (`.gitignore:100`, re-included on purpose) | clear |
| `work/r2_1211_rubber_tracks.json` | `tyre_deposit.py:305` via `_tracks()` | **tracked** (force-added, R2-3961) | already fixed |
| 11 × `world/*.py`, 84 × `world/items/*.{py,json}`, `assemble.py` | `assemble.py:132` `_source_fingerprint()`, byte-hashed | **tracked** | clear |

Three more import-time reads were found beyond the known one
(`item_manifest.json`, and `circuit_spec.json` from two item modules). **All
three are tracked.**

### Read during `build()`

| path | tracked? | what regenerates it |
| --- | --- | --- |
| `docs/beat_sheet.json` | **tracked** (`.gitignore:46-50` records why it must be) | — |
| `world/camera_rig_path.json` | **tracked** | — |
| `world/items/PLACEMENT.json` | **tracked** | — |
| `world/sky_cause.json` | **tracked** | — |
| `sim/out/apply_requirements.json` | **tracked** | — |
| `render/world/assembly/r2/SHIPPING.md` | **tracked** | — |
| `render/r2651/dof.json` | **UNTRACKED** — `.gitignore:26 render/*` | `tools/r2651_dof_dump.py` (tracked) |
| `render/exposure_cal/expcal_measured.json` | **UNTRACKED** — `.gitignore:26` | `tools/exposure_calibration.py --measure` (tracked, `OUTDIR` L70 is this dir) |
| `render/world/sky/sky_banding.png` | **UNTRACKED** — `.gitignore:78` | `build_sky.render_test()` (tracked) |
| `world/car_anim.blend` (301 MB) | **UNTRACKED** — `.gitignore:12 *.blend` | `anim/build_car_anim.py` (tracked) |
| `world/showroom_ceiling.blend` (7.3 MB) | **UNTRACKED** — `*.blend` | `world/items/showroom_ceiling.py` (tracked) |
| 4 × `world/items/*_test.blend` (up to 2.0 GB) | **UNTRACKED** — `*.blend` | each item's own `world/items/<item>.py` (all tracked) |
| **33 × `render/items/*/gate.json`** | **UNTRACKED** — `.gitignore:26 render/*` | **see below — this is the defect** |

**Counted: 44 distinct build-input paths checked, 42 of them resolvable to a
concrete file. 13 were untracked. 12 of those 13 have a kept, tracked
regenerator. One did not.**

## THE DEFECT: `render/items/*/gate.json`

`world/build_items.py::check_row()` (L497-509):

```python
g = (_abs(row["gate_json"]) if row.get("gate_json")
     else os.path.join(GATE_DIR, row["item"], "gate.json"))
if os.path.exists(g):
    row["_gate_result"] = json.load(open(g)).get("result")
if row.get("require_gate_accepted", True) and row["_gate_result"] != "ITEM_ACCEPTED":
    fatal.append("gate verdict is %r, not ITEM_ACCEPTED ...")
```

`require_gate_accepted` **defaults to True**, so a missing `gate.json` is not a
degradation — it is a **fatal** on that row. `rm -rf render/items/` does not
make the world build worse, it **stops it**. That is precisely the position
`work/r2_1211_rubber_tracks.json` was in, one directory over, and for the same
structural reason: a blanket exclusion written to keep *renders* out of git
(`render/*`) swallowed the *evidence* that was sitting among them.

**And "a script writes it" is true here and beside the point.**
`tools/item_gate.py` will happily produce a `gate.json` — of **a new run**.
This project's own tooling says so, in `tools/r2_1381_rescore.py:9`:

> `gate.json` files are the record of the run that produced them and are not
> edited after the fact.

The 33 files are the record of the runs that **accepted the geometry that
shipped**. Re-rendering cannot restore that record; it can only replace it with
a different one wearing the same name. By the test set for this sweep —
*untracked, and nothing regenerates it* — this is the one that fails.

520 KB across 33 files, so the `.gitignore` header's "large, regenerable
artefacts" reasoning does not reach them either.

### The fix

`.gitignore` gained a block in the house style — every level opened one at a
time and immediately re-closed, because git will not descend into an excluded
directory — with the reasoning above as its comment:

```
!render/items/
render/items/*
!render/items/*/
render/items/*/*
!render/items/*/gate.json
```

**Verified surgical.** `git status --porcelain -uall render/items/` returns
**33 paths, all of them `gate.json`, nothing else**. The gate renders, crops
and EXRs beside them stay ignored (`gate.png`, `foo.exr`, `notes.txt` all still
excluded on a spot check). All 33 staged.

## A SECOND FINDING: THE BATTERY SOURCE `.gitignore` RE-INCLUDES WAS NEVER `git add`ed

Different failure mode, same consequence. `.gitignore:83-96` deliberately
re-includes `render/world/assembly/r2/**/*.py` and `*.sh` — that block exists
*because* the battery had no history. The rule works. **Nobody ran `git add`.**

**14 hand-written source files were sitting untracked with no rule ignoring
them**, including the whole of **v129 — the current generation, the one that
built and verified `film25_breach`, the ship candidate now on the farm**:

```
v129/verify_film25.sh   v129/run_rebuild25.sh   v129/build_breach25.sh   v129/film_car_keys.py
v126/build_assembly11.sh  v126/build_assembly12.sh  v126/build_assembly13.sh
v126/build_breach19.sh    v126/build_car_cs.sh      v126/build_film19.sh
v126/run_rebuild.sh       v126/run_rebuild20.sh     v126/run_rebuild21.sh
v126/verify_film19.sh
```

`git log` on any of them was empty, which is the exact condition
`.gitignore:68-71` says makes R2-079 ("establish a baseline from committed
state before you change anything") structurally impossible. All 14 staged.
**A re-inclusion rule is not a backup; it only makes an `add` possible.**

## CLEARED, WITH THE REASON

Reported so the next sweep does not redo them:

* **`world/car_anim.blend`, `world/showroom_ceiling.blend`, the four
  `world/items/*_test.blend`** — untracked, but each has a tracked builder, and
  at 301 MB / 2.0 GB they are what the `.gitignore` header means by "large,
  regenerable, would make commits useless". Correctly excluded.
* **`render/r2651/dof.json`** — regenerated by `tools/r2651_dof_dump.py`.
  Worth one caution: `build_surface.py:4577` reads it **guarded by
  `os.path.exists`**, so its absence does not raise — it silently changes the
  film pose defs. Regenerable, but it fails quiet rather than loud.
* **`render/exposure_cal/expcal_measured.json`** — regenerated by
  `tools/exposure_calibration.py --measure`, whose `OUTDIR` is that directory.
* **`render/world/sky/sky_banding.png`** — a render, regenerated by
  `build_sky.render_test()`.
* **`docs/r2401_cockpit_fit.json`, `r2401_cockpit_sweep.json`,
  `r2401_headroom.json`** — untracked *and unignored*, which looks like the
  battery case, but they are **outputs** of their own tracked tools and nothing
  reads them as a build input. Not defects.
* **`docs/collision_report.json`, `instance_variety.json`, `inventory_iter.json`,
  `placement*.json`, `presentation_normals.json`, `screen_presence*.json`** —
  untracked, each named individually in `.gitignore:43-56`, all generated
  reports. Correctly excluded.
* **`docs/item_placement.json`** — referenced at `tools/item_placement_gate.py:4`
  and **does not exist**. It is that tool's `--out` example, not an input.
  Nothing reads it. Not a defect.

## THE ONE THING THIS SWEEP CANNOT FIX, STATED PLAINLY

Following the regeneration chain to its root rather than stopping at the first
script that writes the file:

```
render/film25_breach.blend
  <- world/car_anim.blend        (anim/build_car_anim.py)
  <- world/beat1_anim.blend      (anim/build_beat1_anim.py)
  <- ~/opus5-car-render/work/iter.blend      288 MB, 2026-07-26
```

`anim/build_beat1_anim.py:2-3` names it as its input blend. **The entire round-2
car bottoms out in a round-1 artefact that lives outside this repository**, is
288 MB, and is protected by nothing but the convention that round 1 is
read-only. `build_beat1_anim.py`'s own header is explicit that this is
deliberate — "the seated pose is not authored, it is the round-1 car" — so it is
a design choice, not an oversight. It is recorded here because the sweep's
question was *what happens if this vanishes*, and for this one the answer is
that nothing in `f1-round2` can rebuild it. **Not actioned: round 1 is
read-only and out of scope.**

---

# PART 2 — MEASUREMENT PASSES OUTSIDE THE BUILD LOCK (task #165)

## The defect is real, and the script already knew it

`render/world/assembly/r2/v129/verify_film25.sh` ran **five** heavy Blender
steps against `render/film25_breach.blend` (10.9 GB). The fifth — the bar —
was wrapped in `tools/buildlock.sh`, with a comment saying exactly why:

> Wrapped in the build lock because two ~10 GB opens on an 11 GB box do not run
> at half speed -- one of them gets OOM-killed.

The four above it were gated by a local `waitmem` helper instead:

```bash
waitmem () {
  for i in $(seq 1 960); do
    A=$(free -g | awk '/^Mem:/{print $7}')
    [ "$A" -ge 5 ] && { echo "[gate] ${A} GB available, starting $1"; return 0; }
    sleep 30
  done
  echo "[gate] TIMEOUT before $1"; return 1
}
```

The same reasoning that justified the lock for step 5 applies unchanged to
steps 1-4. They were the ones outside it.

## THE MEASUREMENT

One pass run under the lock, instrumented — `VmHWM` polled from `/proc` every
0.5 s, `ru_maxrss` taken from `wait4()`:

| | |
| --- | --- |
| pass | `work/lighting/measure_film_scene.py` on `render/film25_breach.blend` |
| blend on disk | 10,956,580,171 B (10.9 GB) |
| **peak RSS** | **7,847 MB = 7.66 GB** (`VmHWM`; `ru_maxrss` agrees) |
| MemAvailable at start | 7,382 MB |
| **MemAvailable at trough** | **264 MB** |
| box | 11,888 MB RAM, 45 GB swap |

**One pass takes this box to 264 MB.**

**Lane: BIG, for all four.** 7.66 GB is not a `--small` job by any reading —
that lane is two concurrent slots gated at `SMALL_MIN_MB=1000`, sized for the
~400 MB surface builds R2-3066b measured. Putting a 7.66 GB pass in it would
permit two at once and kill the thing the lane exists to protect.

## WATCHED TO FAIL: THE GATE WAS GREEN FOR EXACTLY THE WINDOW THAT MATTERED

`waitmem`'s verdict is a pure function of the number it reads, so it was
evaluated against the recorded MemAvailable of the real pass, at 0.5 s
resolution — not simulated, *the actual guard against the actual ramp*:

```
t=   0.0s  holder_rss=     0 MB  mem_avail= 7382 MB (7 GB)  waitmem: START
t=   2.5s  holder_rss=  1050 MB  mem_avail= 7155 MB (6 GB)  waitmem: START
t=  11.5s  holder_rss=  4312 MB  mem_avail= 6081 MB (5 GB)  waitmem: START
t=  16.5s  holder_rss=  6379 MB  mem_avail= 5495 MB (5 GB)  waitmem: START   <-- last
t=  17.0s  holder_rss=  6938 MB  mem_avail= 5079 MB (4 GB)  waitmem: wait
...
t= 552.5s  holder_rss=  6447 MB  mem_avail= 1291 MB         (trough was 264 MB)
```

**For the first 16.5 seconds, `waitmem` returns START** — while the process it
is standing next to is already committed to 7.66 GB and has touched under 6 of
it. A second pass admitted anywhere in that window lands in a box that ends up
with 264 MB spare, and the OOM killer then takes **the biggest process**, which
is whichever 7.66 GB pass is nearest to finishing, or somebody else's 10 GB
film append.

And `waitmem` sleeps **30 s** between polls, so its sampling interval is nearly
twice the width of the window in which it is wrong. It cannot even see itself
be wrong.

This is the class of defect named in the brief: **a memory poll cannot see
intent.** It samples what is *allocated now*; the quantity that decides whether
the box survives is what is *intended*. Only a lock carries intent, because the
holder registers before it allocates.

Full 0.5 s timeline: `docs/r2_4020_waitmem_timeline.tsv`.

## THE FIX

`waitmem` is gone. The four passes go through `tools/buildlock.sh`, big lane,
via a `runlocked` helper. Two constraints shaped it and both are load-bearing:

**1. The blender binary stays a direct argv element.** `buildlock.sh`'s
wrong-Blender refusal (R2-3602) inspects `basename` of each argument. Wrapping
the command in `bash -c "..."` to get the redirect inside the lock would have
hidden `/opt/blender-.../blender` from that scan and **silently disarmed the
one check standing between this script and a quietly-corrupt world**. That is
an escape hatch by accident, and it is not there.

**2. buildlock's own verdict line must not reach the four logs.** `buildlock`
prints `>> STAGE RESULT: BUILDLOCK RELEASED`. `film_bar.py`'s `VERDICT_RE` is
`>{0,2} *STAGE RESULT:`, and `stage()` **FAILs any log with two verdicts**
(R2-2108). The four logs written by these passes are exactly the four
`film_bar.py` reads. So the naive wrap — `buildlock ... > $W/measure.log` —
would have turned **all four passing bar rows into FAILs**. `runlocked`
captures buildlock's stream to a `.lock.log` beside the log and strips the
BUILDLOCK verdict on the way in, which is the same capture-and-replay the bar
wrapper at the bottom of the file has always used.

```bash
runlocked () {
  local lname="$1" flog="$2"; shift 2
  local raw="${flog%.log}.lock.log"
  bash tools/buildlock.sh "$lname" "$@" > "$raw" 2>&1
  local rc=$?
  grep -av "STAGE RESULT: BUILDLOCK" "$raw" > "$flog"
  [ $rc -eq 0 ] || echo "  [lock] $lname rc=$rc -- refused, or the pass failed; raw log: $raw"
  return $rc
}
```

One deliberate behaviour change: `waitmem` gave up after 8 h and returned
failure; **buildlock queues instead of failing**, by design, so a contended
pass is now late rather than lost.

## PROOF

`runlocked` was extracted verbatim from the edited script (`awk` on the
function body, so there is no second copy to drift) and exercised.

### The two guards, asked the same question at the same instant, disagreeing

This is the whole defect in four lines. While the instrumented 7.66 GB pass
held the lock, a **real** buildlock-wrapped second pass was launched, and
`waitmem`'s gate condition was polled beside it. At the tail of the run the
holder had come down off its peak but was **still resident and still holding
the lock**:

| wall clock | holder | `waitmem` says | `buildlock` says |
| --- | --- | --- | --- |
| 17:18:53 | resident, 2.4 GB, lock held | `wait 3` | **QUEUED** |
| **17:18:58** | **resident, 2.2 GB, lock held** | **`START 5`** | **QUEUED (refused)** |
| **17:19:03** | **resident, 2.3 GB, lock held** | **`START 8`** | **QUEUED (refused)** |
| 17:19:08 | gone, lock released | `START 8` | RAN |

At 17:18:58 and 17:19:03 `waitmem` would have launched a second 7.66 GB pass
**into a box still occupied by the first one**. The lock, asked at the same
moment, refused:

```
BUILD LOCK HELD by 'r2_4020_rss_probe_measure_film_scene pid=3118974 since=17:06:41';
0 waiter(s) ahead of me -- queuing, not racing.
```

The contender was held for the **entire 12½ minutes** the pass ran and started
only after `BUILDLOCK RELEASED`. Same box, same second, one guard green and one
guard red — and the red one is right.

### The three regression tests

`runlocked` sits between two invariants it could easily have broken, so both
were tested rather than reasoned about:

| | test | result |
| --- | --- | --- |
| **T1** | a passing stage leaves **exactly one** verdict in the log `film_bar.py` reads, counted with `film_bar.VERDICT_RE` itself, not a lookalike | **PASS** — 1 verdict, `FILM_MATERIALS_OK (0 failures)`; zero `BUILDLOCK` tokens in the log; buildlock's stream preserved beside it |
| **T2** | buildlock's wrong-Blender refusal is **still armed** through `runlocked` | **PASS** — `/usr/bin/blender` refused, `rc=4`, the wrong binary never ran, and the log is left with **0 verdicts → UNMEASURABLE**, i.e. it fails safe rather than passing quietly |
| **T3** | a second pass **queues** while the lock is held | **PASS** — waited 19 s behind a 20 s holder, logged `queuing, not racing`, and **still exactly 1 verdict** afterwards: the queue chatter is not mistaken for a verdict |

T1 is the one that matters most. The naive wrap really would have failed all
four bar rows, and it would have failed them *on a passing film* — the bar
would have reported a defect that did not exist, which is the failure mode this
log has paid for before.

## WHAT WAS NOT CHANGED, AND WHY

**`v127/verify_film23.sh` and `v128/verify_film24.sh` still contain
`waitmem`.** They carry the same defect. They were left alone deliberately:
they are the scripts that produced film23's and film24's evidence in
`work/r22101` and `work/r23361`, which v129's own header calls "the ONLY proof
that those two ship candidates passed 40/40, and neither is reproducible from
any later state of these files." Both are tracked, so `git show` recovers them
exactly; editing them would gain nothing and would blur what those two films
were actually verified by.

**`v126/verify_film19.sh` also has it**, with a different shape (the socket
audit is inside a loop). Same reasoning.

**The live path is fixed.** v129 is the current generation. **v130, when it is
forked from v129, inherits `runlocked` and must not reintroduce `waitmem`.**

## LEDGER

| | |
| --- | --- |
| build inputs checked | 44 paths, 42 resolvable |
| untracked | 13 |
| untracked but regenerated by a kept, tracked script | 12 |
| **untracked and unregenerable → fixed** | **1 class: 33 × `render/items/*/gate.json`** |
| second finding → fixed | 14 battery source files the `.gitignore` already re-included but nobody `git add`ed |
| not actioned, recorded | round-1 `iter.blend` at the root of the car chain |
| heavy Blender passes run | **1** (under the lock, 739 s, rc=0, `assert_levelled` PASS) |
| master render touched | **none** |

## POSTSCRIPT — THE COMMIT WAS REFUSED FIRST, BY THE DEFECT `.gitignore:29-36` DESCRIBES

The first `git commit` was refused by `gitguard`: all 14 battery source files,
**including the v129 fix itself**, were leased by `inflight-auto` — an
auto-lease that had claimed **202 paths** 12.4 hours earlier, alongside an older
`inflight-2026-08-07` seed holding **295 paths at 67.2 hours**.

Neither was a person doing work. This is exactly the failure `.gitignore:29-36`
was written about — *"a lock that claims 'everything dirty' inherits the tree's
untidiness as policy"*, and every such entry is *"a future false refusal aimed
at whoever next touched that name."* Twelve hours later it was aimed at this
one.

**It was cleared through the front door.** `gitguard.py`'s own docstring
(R2-2232) says the only mechanism that used to exist was
`R2_AGENT=inflight-2026-08-07 gitguard.py release <path>` — setting your
identity to another owner's name — and that *"a guard whose only escape hatch
looks like impersonation is a guard people route around."* `retire` is the
hatch built in the open, and it is what was used:

* dry run first, then `--apply`, **under my own `R2_AGENT`**, never the owner's;
* scoped to the **14 paths of this task**, not `--all-paths`;
* both seeds seed-shaped and past the 8 h floor (S1, S2), **0 refusals**, no
  named agent's lease touched;
* `retire` only *removes*, so the paths came back **unowned** and were then
  claimed under my own identity (S3), which is the step that makes this a
  transfer nobody had to pretend about.

Recorded because a refusal that gets worked around silently is worth more as a
report than as a cleared obstacle.

