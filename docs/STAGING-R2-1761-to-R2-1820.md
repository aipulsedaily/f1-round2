# STAGING — R2-1761 to R2-1820 — the debt board, before the masters

Numbers to be assigned by the log's owner. **`docs/DEFECT-LOG-R2.md` not edited.**

Six long-open items, closed by measurement wherever measurement would do it.
The brief said a clean sweep of six fixes would be the least likely outcome and
would be distrusted. It was right — **six items produced thirteen separate
verdicts and only four of them are FIXED**:

```
#78   stale pad                FIXED         #90   paint over void       ALREADY CLOSED
#78   unreachable fallbacks    CONFIRMED     #90   floating paint        DECLINED (handed over)
#78   the private car box      FIXED         #90   the glass mouth sink  REFUTED
#97   the stamp                ALREADY CLOSED   #100  the DOF camera     ALREADY CLOSED + REFUTED
#97   report-vs-report         FIXED         #100  the 11-deg camera     REFUTED
#115  the index race           FIXED
#120  hospitality_deck         REFUTED (another session) -- my first answer RETRACTED
```

**Six instrument failures were caught, five of them in instruments written
today**, and in three cases the broken instrument had already produced a
confident number: *78.101 m² of floating paint*, an amend guard that could not
see `--amend`, and a differ that reported NON_REPRODUCIBLE for a change it had
silently discarded.

---

## R2-17xx — #115: THE PATH-SCOPE RULE IS NOW A HOOK, AND ITS FIRST ACT WAS TO REFUSE ITS OWN AUTHOR

**FIXED.**

The rule *"path-scope every `git add`, never `-A`"* is written into
`docs/SESSION-HOLD.md`, into every agent brief issued today, and into the defect
log four separate times. It has still been violated twice, each time sweeping
another agent's in-flight source into a commit that did not own them. R2-234 is
the same failure through a different door: `git commit --amend` rewrote a
*different agent's* commit message, because `--amend` takes whatever `HEAD`
happens to be and in a tree with concurrent agents that is not necessarily
yours.

Before this entry the repository had **no hooks at all** — `core.hooksPath`
unset, `.git/hooks/` containing nothing but git's own samples. Five statements
of a rule and zero enforcement of it.

> **A warning is not a mechanism.**

`tools/gitguard.py`, `tools/gitguard_selftest.py`, `tools/githooks/pre-commit`,
`tools/githooks/prepare-commit-msg`, and `core.hooksPath = tools/githooks`.

**The mechanism is a lease.** An agent claims the paths it is working on; the
`pre-commit` hook refuses any commit that stages a path leased by somebody else
and **names the owner**. It refuses only on positive detection — an unleased
staged path is allowed — so it was installable into a live tree with six agents
mid-flight without stopping any of them.

**The leases live in `.git/r2-guard/`, and that is not an implementation
detail.** `docs/SESSION-HOLD.md` line 23 says worktree files "are not safe from
`git checkout` or `git add -A`". A lease store in the worktree would be swept by
the very command it exists to refuse.

**Seeded, so it protects work belonging to agents who have never heard of it.**
`seed-inflight` claimed all **312** currently-dirty paths for a stand-in owner.
A file modified and uncommitted is by definition unfinished; anyone wanting to
commit one now says so out loud, once, and the refusal message carries the exact
command.

### The controls, including the ones that had to fail

`tools/gitguard_selftest.py` builds a throwaway repository, casts two agents,
and runs **22 checks, `>> STAGE RESULT: OK (0 failures)`**. It never touches the
live repository.

The load-bearing ones are the vacuity controls:

```
C4   the IDENTICAL `git add -A` sweep, with bob's lease deleted   -> ALLOWED
C6   the IDENTICAL index, with the lease aged past its TTL        -> ALLOWED
C6b  the SAME index again with the lease live                     -> REFUSED
```

Without C4 and C6, C2's refusal would prove something about the test and nothing
about the lease. Also proven able to fail: `git commit -a` (C11), a commit issued
from a **subdirectory** (C12 — `core.hooksPath` is relative, and a guard that
quietly stops running when you are cd'd into `world/items` is indistinguishable
from no guard), directory and glob lease forms (C7), and an anonymous committer
with `R2_AGENT` unset (C5).

**C8 is the one that keeps it from being worse than the defect.** A broken lease
store must ALLOW the commit and say so loudly. A guard that bricks six agents'
commits because of its own bug is a worse outcome than the sweep it guards, and
this project has spent the day discovering that its instruments were the problem
more often than its renders were. `R2_GITGUARD=off` bypasses and logs to
`.git/r2-guard/bypass.log`.

### The selftest caught the guard's own broken instrument

The first `--amend` refusal **did not fire**, and only the control found it.

`prepare-commit-msg` is documented to receive `source="commit"` and the SHA when
amending — **but only when git is reusing the old message.**
`git commit --amend -m "..."` passes `source="message"` and no SHA. The hook was
keyed on the documented argument and sailed straight past **the exact command
that rewrote another agent's commit in R2-234.**

```
C3  git commit --amend -m "..."     want=REFUSED  got=ALLOWED     <- first run
C3  git commit --amend -m "..."     want=REFUSED  got=REFUSED     <- after
```

Replaced with a detector that reads the invoking `git` process's real argv from
`/proc`, walking up from the hook. Tenth instrument finding of the session, and
the second caught before it cost anything.

### Proven on the live repository, without touching the shared index

Staged two of another agent's genuinely in-flight files into a **throwaway
index** (`GIT_INDEX_FILE`), so the real one was never written:

```
audio/dsp.py               leased by inflight-2026-08-07  (0.0 h old)
world/build_barriers.py    leased by inflight-2026-08-07  (0.0 h old)
>> STAGE RESULT: FAIL (2 violations)          real index after: 0 staged paths
```

**And it refused its own author.** The first `claim` of my own files came back
`CLASH ... tools/githooks/pre-commit is already leased by inflight-2026-08-07`,
because `seed-inflight` had swept up the hook files I had just written. That is
the guard working, on me, one minute after installation.

### THE SEED WAS A SNAPSHOT, AND WITHIN TWENTY MINUTES IT WAS PROTECTING THE WRONG SET

Found by another agent's situation rather than by my own test, which is the
honest way to record it. `seed-inflight` claimed the 312 paths dirty at 22:09
**and nothing after that.** By 22:30 a peer had begun editing
`tools/placement_gate.py`, which had been **clean at seed time** — so it was
unleased, and a `git add -A` would have taken it exactly as before. *A guard that
protects only the work that existed at install time protects the wrong set within
the hour.*

The hook now **auto-leases any dirty, unclaimed path on every commit**, so
protection tracks the tree instead of a timestamp. It cost nothing to adopt: no
new command, no change to how anyone commits. Its first live run picked up
**32 paths** that had appeared since the snapshot.

Staged paths are deliberately excluded — auto-leasing the files of the commit
being made would refuse every commit in the repository until its author claimed
each file first, and *a guard people must negotiate with on every commit is a
guard people turn off*. `R2_GITGUARD=off` is worse than no guard, because it
looks like one.

**Adding it broke four green controls at once, and all four were right to
break.**

- **C5b — "the SAME index committed by its OWNER" — went REFUSED.** A path could
  be held by both its real owner and by `inflight-auto`, so the guard refused the
  author on their own file. Fixed by making **an explicit claim beat an automatic
  lease**.
- **C3c — `--amend` with the escape hatch — went REFUSED**, naming *the guard's
  own hook files*. `--amend` pulls the previous commit's whole tree into the
  index, which surfaced a **ratchet**: a path auto-leased while dirty stayed
  leased forever, even after being committed. Left alone, refusals would have
  accumulated against files committed hours earlier until the guard was pure
  noise. The auto-lease is now **pruned to what is still dirty** on every run.
- **C4 and C13d — the two vacuity controls — went REFUSED**, which is the failure
  that matters most: had they stayed green by accident, C2 and C13c would have
  been proving nothing.

**And the first version of C13d was itself a broken control.** It staged the
whole tree and came back REFUSED — for three reasons that had nothing to do with
the auto-lease it was written to test. It would have read as a pass. Rewritten to
stage exactly one file, so the verdict is about one variable.

`>> STAGE RESULT: OK (0 failures of 26 checks)`

### What it deliberately does not do

It cannot tell a sweep from a deliberate broad commit *by an agent who has
claimed nothing*. Ownership has to be asserted by somebody, and the honest
version of that is a lease rather than a heuristic on staged-set size — a
heuristic would produce false refusals, and a guard people learn to bypass is an
absent guard. `seed-inflight` is what makes that assertion free today.

---

## R2-17xx — #97: PLACEMENT REPORTS — HALF WAS ALREADY CLOSED, AND THE HALF THAT WAS NOT IS THE HALF THE ITEM IS NAMED FOR

**PARTLY ALREADY CLOSED, PARTLY FIXED.** Details below; the premise needed
splitting before either verdict was available.

### Already closed, and closed well — do not rebuild it

`tools/provenance.py` (487 lines) and `tools/input_stamp.py` both exist and both
name **defect #97 in their own docstrings**. `placement_gate.py` already stamps
every report it writes, declaring `blend`, `spec`, `telemetry`, `beat_sheet` and
`camera_path`.

One hypothesis I formed from the record and had to drop: I expected the stamp to
record the contract as a **version label**, which `input_stamp.py`'s own docstring
warns is not a fact — *"assembly5 and assembly6 disagree by 3.19 m of wall and
BOTH report contract 1.2.0. The version is a label; the hash is the fact."*
**It does not.** `provenance.stamp()` appends `world_contract.py` and
`itemkit.py` to `also_hash` **by default**, without the caller having to
remember, precisely because they change an answer without appearing in argv.
`--selftest`: **13/13 checks pass**, with positive controls that fire (input
drift, a same-size edit, a stale sibling, a missing input).

That premise was wrong and no code was written for it.

### Still open, and it is exactly what #97 says

**`verify()` compares a report to disk AS IT IS NOW.** #97's question is a
different one — *the closest approach moved between run A and run B; which of
them moved it?* — and `verify()` cannot answer it, because by the time anyone
asks, disk is at some third state and neither run's inputs are on it any more.
Nothing in the repository could ask A-against-B.

**And no consumer refused an unstamped report.** `tools/placement_depth.py` read
`rep["violations"]` blind. A four-day-old file computed exactly as smoothly as a
fresh one — which is R2-735's entire entry: three placement reports, two answers,
and *the newest file was the stale one*, settled by mtime and by byte-comparing
rows because none of them could say what it measured.

**All six placement reports on disk are unstamped**, verified rather than
assumed:

```
UNSTAMPED  docs/placement_report.json        UNSTAMPED  docs/placement_depth.json
UNSTAMPED  docs/placement_report_r2.json     UNSTAMPED  docs/placement_after_46.json
UNSTAMPED  docs/placement_report_cam34.json  UNSTAMPED  docs/placement_before_46.json
```

### What was built

`tools/report_repro.py` + `tools/report_repro_selftest.py`. Four verdicts:

```
inputs same,  results same     REPRODUCED
inputs moved, results moved    ATTRIBUTED        -- and it names which
inputs same,  results moved    NON_REPRODUCIBLE  <- the alarm #97 is named for
inputs moved, results same     INSENSITIVE       <- the quieter one, worth as much
```

`INSENSITIVE` earns its place: a report whose numbers do not move when a declared
input moves may not be reading that input at all — **a metric that reads the same
present or absent**, the single commonest defect shape in this log. A differ that
could only emit `ATTRIBUTED` would launder exactly that failure as a success.

`--require` is the consumer half, now wired into `tools/placement_depth.py`: it
refuses an unstamped report unless the caller passes
`--allow-unstamped "<why>"`. A stamp nobody checks is a header — R2-1099 already
paid for a fix written to a file the pipeline does not read.

### All four verdicts, demonstrated on the real tool with real inputs

`placement_gate.py --selftest` run four times under Blender 5.2, ~7 min each,
CPU only, serialised behind a shared `flock` because an 8 GB exec and an 8 GB
render cannot share an 11 GB box:

```
run1 vs run2   identical inputs                       REPRODUCED
run1 vs run3   spec gains a key nothing reads         INSENSITIVE
run1 vs run4   one elevation PVI, 8.00 -> 8.25 m      ATTRIBUTED
run1 vs docs/placement_report_cam34.json              UNCITEABLE
```

**The gate is deterministic.** Identical inputs give a byte-identical body. So
#97's *"changed with no world change"* was **not** non-determinism — it was
undeclared input drift, and provenance now records it.

**And run 3/4 caught something I never staged.** `beat_sheet` moved between run 1
and run 3 — another agent rebuilt `docs/beat_sheet.json` underneath my runs while
they were queued:

```
MOVED   beat_sheet   1925655f295193c1 -> 7be83550177ce9ec
```

That is **#97 happening live, detected, in an experiment aimed at something
else.** It is also the exact mechanism the original defect describes: an input
rebuilt underneath a measurement by an owner on a different schedule. Under the
old regime this run would have produced a number that silently disagreed with
run 1 and nothing would have said why.

**The `INSENSITIVE` verdict earned itself immediately.** Adding a key to the spec
moved the hash and moved **not one number** — correct, and precisely the reading
that would otherwise be mistaken for "the input does not matter" when it may
equally mean "the report never read it".

### TWO CORRECTIONS TO THIS ENTRY, BOTH AGAINST MY OWN CLAIMS

**1. The determinism result does NOT cover `closest_approach`.** The `--selftest`
report writes `controls` and `failures`; it has **no `closest_approach_m` block
at all**. I was one paragraph from stating a REPRODUCED verdict as though it
covered the number #97 is named for. It does not, and re-running the gate on the
shipped world was not affordable here.

**2. A stamped report of the wrong quantity is still wrong.** A peer working #78
found that `build_volumes` uses `0.992` — the car box's **thickness** — as if it
were the box's **top**, against a measured box at z 0.340…1.332:

```
band TOP    gate 1.5920    contract 1.9320    delta -0.3400 m
```

and `intrusion()` returns **−1e9 outside the band** (`placement_gate.py:503-508`
at HEAD, verified), so anything in that 340 mm slice over the driven line **never
reached the distance test and could not appear in `closest_approach` either.**

> **If `closest_approach` has a blind slice, "it changed with no world change" may
> never have been a reproducibility question at all.** It may be a value that was
> not measuring what it claimed. Attribution machinery sits *downstream* of that,
> and their fix is upstream of my instrument.

### I READ AN UNCOMMITTED WORKING-TREE EDIT AS PRIOR ART, AND REPORTED IT AS CLOSED

The trap is new and worth its own line, because it cost a peer their credit and
nearly closed a live item.

While working in `placement_gate.py` I found a section headed *"8b. THE PRIVATE
CAR BOX vs THE CONTRACT'S (R2-071, item 78)"* — citing the item number — and
relayed it as evidence that #78's third sub-claim was **already closed**. It was
not. It was another agent's **uncommitted edit, twenty minutes old**. The file on
disk showed the fix; history showed nobody had ever made it:

```
git log -S "THE PRIVATE CAR BOX" -- tools/placement_gate.py    0 commits
git log -S "item 78"             -- tools/placement_gate.py    0 commits
git log -S "R2-071"              -- tools/placement_gate.py    0 commits
git show HEAD:tools/placement_gate.py   594: r = 0.5 * 2.005 + CAR_MARGIN
                                        599: "zband": (-0.3, 0.992 + CAR_MARGIN)
```

Today has produced four *source-versus-artefact* failures — a socket default read
instead of its link, a chain script read instead of the blend, a stale ledger
read instead of the geometry, a render arm nobody interrogated. **This is the
fifth, and the first where the artefact was a file rather than a render: the
working tree read as history.**

> **On a box where a dozen agents share one checkout, "the file says so" and "the
> project decided so" are different claims.** `git log -S` is the cheap
> discriminator and it takes seconds.

Retracted in full to its author; the credit for 8b is theirs.

### The differ's own broken instrument, caught by its own control

Control P5 — *the contract changed while its declared version string stayed
`1.2.1`* — came back `NON_REPRODUCIBLE` when it should have been `ATTRIBUTED`.

**A role is not unique.** `provenance.stamp()` appends `world_contract` and
`itemkit` by default and does **not** deduplicate by role, so passing
`also_hash=[("world_contract", <another copy>)]` yields a stamp with two entries
under that role. Keying a dict on the role silently kept the last and dropped the
other — **an attribution tool laundering the very thing it exists to
attribute.** Fixed to compare the multiset of hashes per role.

`>> STAGE RESULT: OK (0 failures of 16 checks)`, including the two vacuity
controls: V1 feeds it a difference buried four levels down that it **must** find
(a `_body()` returning a constant would make every pair on earth `REPRODUCED`),
and V2 requires the same numbers in a different key order to come back
`REPRODUCED` — a differ that calls key order a regression is ignored within a day.

### The honest limit

This does not re-run the gate against the shipped 7.98 GB world, so the six stale
reports on disk stay stale. It makes them **unciteable rather than
silently citable**, and makes the next pair attributable. Re-running the gate on
the ship needs an 8 GB Blender process, and a rebuild is in flight on an 11 GB
box.

---

## R2-17xx — #90: THE THREE UNLOGGED DEFECTS, RE-MEASURED ON THE SHIP — AND `matrix_world` READS IDENTITY ON A LINKED OBJECT

**#1 ALREADY CLOSED · #2 DECLINED (confirmed live, handed over) · #3 REFUTED
(confirmed, not re-litigated).**

All three recovered from one place — `docs/DEFECT-LOG-R2.md:4584-4589`, inside
R2-132, under *"Three defects that had never been written up, now measured"*.
Each string appears **exactly once** in the whole log, which is what made them
recoverable at all.

```
1  paint over void -- 7.10 m2                                     pit exit
2  paint floating up to 367.9 mm above its substrate              pit exit
3  the glass mouth's 100 mm sink -- REFUTED                       glass mouth
```

*"All arrived at contract 1.1.1"* is right for #1 and #2: v1.1.1 moved
`PIT_WALL_X0` 17.7 m west, the bay field's west end moved with it, and
`apron_clearance`'s outboard cut did not follow. The *"assembly defect #2 / #3"*
comments at `build_architecture.py:77` and `:113` are a **different, older
numbering** and are not these three.

### Two broken instruments, and the second is the one to keep

**`matrix_world` is runtime data, and it reads IDENTITY for link-loaded
objects.** `build_architecture` builds `ARCH_Markings` and the bay fields in the
**circuit** frame (40°) but the forecourt and `ARCH_Paving_ApronPlatform` in the
**world** frame. Reading identity for all of them put half the world 500 m from
the other half —

> **and it still produced plausible numbers**, because the paint and the pit-lane
> bays were wrong *the same way*: a p50 gap of 6.37 mm, which looks like a clean
> result.

Caught arithmetically rather than by eye: the printed footprint window was
**565 × 106 m** — the circuit-frame extent — where the world-frame one is
**~491 × 435 m**. The first run's headline *"78.101 m² of floating paint"* was
**pure artefact.** Fixed with `matrix_basis` plus a frame guard anchored to
`_owned()`'s own predicate; control C9 accepts the correct frame (1.0000) and
**refuses** the identity bug (0.4448).

The other: a per-triangle sample cap made the declared 50 mm sampling pitch
fiction — the real pitch was 144 mm — caught by a convergence control that shrank
the cell 4× twice and watched the error **not move**, 0.0420 m² at every pitch.

**The strongest control is the artefact one.** Run against `assembly8` — the
world R2-132 itself measured — through the same binary, the instrument
independently reproduces R2-132's numbers: **370.02 mm** max float against its
**367.9 mm** (0.6 %), and **9.498 m²** paint-over-void against its **7.10 m²**
(the window differs: whole world vs `s 3360-3500 × u 10-42`).

### Results, assembly8 against the shipped assembly10

```
                        assembly8 (pre-fix)      assembly10 (SHIP)
paint over void              9.498 m2                 0.032 m2
gap max                    370.02 mm                146.67 mm
float > 50 mm               36.971 m2               40.971 m2
```

**#1 ALREADY CLOSED** — 9.498 → 0.032 m², by `10442cd`, which landed **2 h 28 m
after assembly8 was built** and was promoted in assembly9/10. The residual is one
≤50 mm sliver at lap **s 3447.66–3447.70** — which is `PIT_WALL_S0 = 3447.71`,
the declared apron/wall boundary — at the instrument's own quantisation floor.

**#2 DECLINED, and confirmed live.** The premise reproduces exactly:
`ARCH_Markings` is still 7,166 verts at **1 distinct z**. Isolated to that object
on the ship: **26.587 m² above 20 mm, 18.213 m² above 50 mm, worst 146.67 mm.**

**Fixing #1 did not fix #2 and never would** — it made the >20 mm area slightly
*worse*, by giving flat paint a dipping surface to hover over. And the root cause
is not the paint's height: at the worst point `world_ground_z` returns **exactly
0.000** and the paint is exactly `MARK_Z` proud of it. It is
`ARCH_Paving_ApronPlatform` sitting **139.2 mm below its own declared datum**.

Declined honestly: **which side is wrong — low slab or flat paint — is not
proven**, and neither fix is validatable without a rebuild while `assembly11` was
building (the R2-380 hazard). The handover carries the discriminating measurement
to run first (~6 min, no rebuild), the exact lines
(`build_architecture.py:1485, 2449, 2474, 2506`, helper at `:213`), and the trap:
**`sit_c` returns the *declared* height, so that fix alone does not close the
139.2 mm.**

**#3 REFUTED, confirmed on the artefact and then stopped.** The arithmetic
reproduces exactly — **4950 samples in the 90–110 mm band, 0 deeper, drop max
exactly 100.00 mm**, spanning **110 columns × 45 rows = 4950**. That is
`R1_FORMATION_Z = -0.100`, deliberate. Both `film16.blend` and `film18.blend`
give `Floor` z_top **+0.0000**, with `Turntable_Deck` reading **+0.3400** as a
positive control proving the script reads meshes rather than a constant. The
older glass-mouth void is now **1 sample** against a historical 1,276 (~64 m²).

**No files in the repository were modified by this item.**

### One operational note, and it is not a small one

A rebuild to `assembly11.blend` was in flight throughout, and **several agents ran
Blender outside the shared lock**. The box reached **0 GB available** and this
item's queue waited ~40 minutes behind an 8-deep `flock` line. The lock only works
if everyone takes it.

---

## R2-17xx — #78: THREE CONTRACT LEFTOVERS, ALL THREE REAL, AND ONE OF THEM MADE A 340 mm SLICE OF THE DRIVEN LINE INVISIBLE

**FIXED (1 and 3), CONFIRMED and guarded (2). None was already closed.**

The contract is at **1.2.1**, not 1.2.0. Selftest **151 checks, 0 failed** on
arrival — `MASTER-PLAN.md`'s quoted "149" is stale by two revisions — and **155,
0 failed** after this item.

They were not discovered here. They are three of the four bullets under
**"Found and NOT fixed"** at the end of R2-044, written down so the next agent
would not have to rediscover them. This item is that agent, and the note worked.

### 1. The stale pad — FIXED, latent rather than live

`build_dressing.py:592` froze `UNTRUSTED_PAD_M = 42.0`, commented as
*"build_barriers' deficit smoothing bleed"*. **That smoothing no longer exists** —
it was deleted after being measured producing a barrier face 18.8 m past the
centreline — and its replacement dilates by `OWNERSHIP_BLEND_M = 60.0 m`. The
frozen pad was **18 m short of the mechanism it was named after**.

**It suppresses nothing today, measured rather than assumed.** Since 1.2.0
clamped `barrier_offset` by `owned_edge`, `min(barrier_offset − verge_edge)` is
**1.0000 m** and **8.5000 m** against a 0.30 m threshold — `bad = 0 of 3675` on
both sides, so the dilation is empty at 42 m *and* at 60 m. **0 stations change
hands.** Now reads `float(C.OWNERSHIP_BLEND_M)`.

**And the guard was proven able to fire:** injecting a 3-station break gives 3
bad, and suppression jumps to **87 at 42 m and 123 at 60 m**. Without that
control, "0 stations change hands" is indistinguishable from a dilation that
never ran.

### 2. The unreachable fallbacks — CONFIRMED by execution, closed with an assertion rather than a deletion

All **11** `getattr(C, NAME, literal)` sites resolve; all 11 literals are dead
code. **Three of them disagree with the contract** — `ACCESS_RIBBON_T_MIN` at
`build_architecture:110` and `:6637` (**0.300 m**), and `PIT_WALL_S0` at
`render_setup3:201` (**17.709 m**).

They were **not deleted.** The back-compat justification has no beneficiary —
every `world_contract.py` on the box is 1.2.1 — but deleting them would
contradict a decision the contract states in prose and would remove nothing that
can bite. **What can bite is that the literals are unreachable only while the
name stays exported.** New contract selftest **[19]** asserts exactly that and
prints each hidden delta.

**Two controls, both fire:** an unexported name, and a name **demoted out of
`__all__`**. And the first draft of control 2 named constants that live in
`build_barriers` rather than the contract, and **failed** — the control caught its
own author before it could pass vacuously.

`build_surface.py` is forbidden and needed no handover: its four sites all agree,
and [19] covers them from the contract side.

### 3. The gate's private car box — FIXED, and this one was live

The copy is **deliberate** (R2-044: *"a gate that imports the thing it checks can
agree with a wrong number"*), and it stays private — `build_volumes` still uses
its own literals. **Correcting a wrong literal is not the same as making the gate
read the contract.** But it had drifted:

```
                    gate      contract     delta
swept half-width    1.6025    1.6025       0.0000
band TOP (z)        1.5920    1.9320      -0.3400
```

**`0.992` is `CAR_BODY_H_M` — the box's *thickness* — used as its *top*.** The
measured box is z 0.340…1.332; it sits on 340 mm of ride height. And
`intrusion()` returns **−1e9 outside the band**, so that 340 mm slice over the
driven line **never reached the distance test at all** — invisible to
`violations` *and* to `closest_approach`. The same failure mode as the road
corridor's floating band, one volume along.

**Proven able to fail twice**: 8b's own comparison fires at 0.3400 m against the
shipped box, and a live mutation (`CAR_BODY_TOP_M` 1.332 → 1.232, 100 mm) turned
the gate red — `>> STAGE RESULT: PLACEMENT_SELFTEST_FAIL`, by runtime
monkeypatch, disk untouched at 1.332.

### What this says about #97, which is the reason it matters

Asked directly, and answered with a number rather than a worry: over **92.20 % of
frames the corrected band provably cannot change `closest_approach`** —
`road_corridor` already covers that space (band −0.5…+4.5 about elevation, which
telemetry z tracks to 0.2 mm) and is clean at +1.149 m.

**The uncovered 7.80 % is 136 frames — f0…f135, the transit** — which is R2-042's
territory exactly. That is the only place the question is open, and the only
place worth a 7 GB load., IT HAS NO DEPTH OF FIELD, AND ITS SUBJECT IS NOT AT 148 m

**ALREADY CLOSED, premise REFUTED three ways; the stale record that generated the
item is FIXED (comment only).**

The item described a *"DOF-blur camera whose subject is at 148 m"* and,
separately, an *"11-degree down-angle camera"*. **`SPECX_CAM_BLOCK_CROSS` is both
descriptions of the same object** — an item-campaign witness camera for
`spectator_crowd`, not a film camera and not a blur instrument. Verbatim from
`world/items/spectator_crowd.py:796-802`, it was built to answer *"does attention
read"* and *"is a neighbour visibly the same person"*, and **cannot answer
either**.

**1. It is not a DOF camera.** `use_dof` is `False` and always was, verified two
independent ways: datablock read-back through `libraries.load`, and gradient
energy rising *monotonically* down the frame (0.138 → 0.161), which a defocus
focused at the aim point cannot do. `f/2.8` and `focus 10.0 m` are **untouched
Blender defaults** — there is no chosen aperture to compute with.

**2. Its subject is at 112.50 m, not 148 m.** Only the corrected distance
reproduces the recorded head heights; at the superseded 200 m a 0.23 m head is
6.13 px, not the measured 8.03.

```
                        ONAXIS      CROSS
superseded record       200 m       148 m      <- what the item was written from
reconstructed, measured 152.20 m    112.50 m
```

**3. The brief's hyperfocal reasoning is correct physics about a camera that was
never built.** At 50 mm f/2.8 on a 36 mm sensor, hyperfocal at a 1 px budget is
95.29 m, so 112.5 m is past it and the far limit is infinity:

```
the ceiling on defocus for ANY object in the universe   0.847 px 4K   0.282 px 720p
```

**And that ceiling was checked against a real noise floor rather than declared
small.** Two independent renders of the same frame give the Monte-Carlo null;
this camera's maximum possible defocus scores **0.78x of it**. *A defocus this
camera could produce moves the frame less than re-rendering it does.*

**Why the wrong diagnosis survived: it was numerically plausible.** Had the
aperture been "fixed" at the datablock's own defaults — f/2.8 focused at 10.0 m —
a subject at 112.5 m would blur by **8.72 px at 4K**, four times the noise floor
and entirely convincing. Only a datablock read-back could kill it.

**Camera B, refuted separately.** The film's *"-11 degrees everywhere it works"*
is R2-454's beat-1 **depression cap** — a law, not a camera. And the angle is not
contrast-free: it is **5.00 deg outside the item's own `PREFLIGHT_MAX_ELEV` of
6.0**, and the guard names it verbatim (*"this frame shows the tops of heads, not
faces"*). Its real failure is **10.07 px of head against a 40 px bar, 0 of 3,803
faces resolvable** — levelling it buys nothing. 40 px at 112 m needs a **183 mm**
lens; the shipped replacements use 276 mm and get **57.2 px and 491 resolvable
faces**.

**The guard fires in both directions**, which is why this is closed rather than
merely asserted: `--selftest` check [10] reconstructs both dead cameras and
**demands rejection**; check [14] demands the six replacements pass. 14 checks,
0 failed.

**The instruments were validated against known answers before use.** The CoC
model reproduces the published depth-of-field table for a 50 mm f/1.4 at 2 m, and
its **negative control is the point**: a deliberately broken lens model is caught
at 2 m and is **invisible at 148 m** — so a CoC check run only at 148 m would
have proven nothing.

**Still open and unowned:** R2-1112's *"is the residual blur aperture or
shutter"* has **no instrument**. Of the 53 beat-sheet keys focused beyond 90 m,
only **17** can defocus anything by a whole 4K pixel. If that A/B is commissioned
it must be staged in **beat 1**, where one key reaches 158.92 px — not past 90 m.

**Cost: no GPU, no render, no Blender.** CPU arithmetic and two existing PNGs.

---

## R2-17xx — #120: REFUTED — and this entry is a RETRACTION of my own first answer

**VERDICT: REFUTED. The verdict, the mechanism and the proof belong to the agent
I had commissioned for this item — not to me.** I answered #120 after it had already been answered,
got the right verdict word by the wrong route, and reported a number my own
instrument could not support. Recorded in full because the failure is more useful
than the answer.

### Their answer, which is the correct one

**The premise's causal clause is false, and the disproof is a law rather than a
measurement.** `UNDECIDED` fires on exactly one condition — `material_between is
None` — and `_material_between` never looks for self-intersection at all. **Ray
parity is a mod-2 invariant**, so two interpenetrating *closed* solids still cross
a ray an even number of times: a self-intersection makes the answer **wrong**,
never **absent**. Proved with the tool's own counter — two interpenetrating closed
boxes give **4 crossings, even**, and call a point that is inside both solids
**OUTSIDE**. Both decks are **mod-2 closed** (`boundary_used_once: 0`,
`edges_used_an_ODD_number_of_times: 0`), so no generic ray can cross them oddly.

**The sentence in the item was never a measurement.** It is a hardcoded `why_txt`
literal at `winding_audit.py:891` that fires on *every* abstention whatever caused
it — and the code's own comment three lines above said something different again.

**The real cause is a double-count.** Five of six report **7 crossings**; jitter
the ray by ≤0.5 mm and **12 of 12 rays count 6**. The barycentric test is
inclusive on all three coordinates, and the probe — an upper-facet triangle
centroid — lands exactly on the congruent lower facet's diagonal.

**And the two sixes are a coincidence.** The 6 `CTX_*` are dropped by
`CONTEXT_TOKENS` before the audit runs (`objects_audited: 5`); the 6 slab pairs
are on `HD_Deck_1_Versant` (4) and `HD_Deck_4_Pallas` (2).

> **Had I reconciled those two sixes I would have built a theory on a numerical
> accident.** I came within one step of it: my working hypothesis for an hour was
> that they were the same six.

### What I got wrong, itemised

**1. "6 slab pairs is not any measured quantity" — WRONG.** It is exactly what the
tool prints today. I cited **504** from R2-180 (2026-08-03) against a run whose
current value is **6**, i.e. I answered a question about today with a number from
five days ago — having spent this same session building an instrument whose entire
purpose is to stop people doing that. **#97 is about stale readings carried
forward, and I carried one forward inside the entry next to it.**

**2. My mechanism was wrong.** I claimed within-piece crossings *are* the case
where inside/outside has no answer. Parity is mod-2; there is an answer and it is
wrong. I asserted a mechanism from a plausible geometric story and never checked
whether the tool's abstention branch had anything to do with it. **The symptom was
real and the mechanism was invented.**

**3. My number was not a self-intersection count.** `BVHTree.overlap` is a
**broad phase**. Fed two sub-parts sitting exactly flush — **zero penetration,
nothing wrong at all** — my detector calls them self-intersecting. So
**116,867 is an upper bound contaminated by flush and grazing contact**, on
geometry that is *built* from flush-stacked closed solids. It should not be
cited, and I have added the flush case to `tools/selfintersect_audit.py` as a
**deliberately failing control**, so the tool now refuses to report an artefact
number at all.

**My three controls could not catch it, and that is the lesson.** K1 tests that a
clean mesh reads zero; K2/K3 test that a real crossing is seen and that
piece-splitting works. **Every one of them uses *penetrating* boxes.** Not one fed
it *contact*. The control set had a hole exactly where the real geometry lives —
which is the same shape as a bay list hardcoded so a bay was never measured.

> **A control set proves only the discriminations it actually exercises.** Mine
> exercised "crossing vs no crossing" and never "contact vs penetration", and the
> second is the whole question on a deck of stacked solids.

Their control set had it: **two boards 6e-7 m out of flush → 12 crossings, max
depth 6e-07 m, 0 deeper than 1e-5 m.** Length cannot separate contact from
penetration; only depth can.

### The one thing of mine that survives, and it was theirs first

That the raw whole-object count is meaningless. I measured **94.6 % of 2,170,647
is between-piece assembly contact**; they put it better and more generally —

> **that is worthless, because it is true of nearly every item built by
> accumulating closed solids without a boolean.**

**A true fact that explains nothing is the most expensive kind**, because it
survives every check pointed at it. Carry that into #78, #90, #97 and #100:
**confirm the mechanism, not just the symptom.**

### Two things their final report added, and one is decisive

**The item is not in the shipped world at all.** Verified independently in
`world/items/PLACEMENT.json`:

```
state                          HOLD
gate_result_at_registry_time   ITEM_REJECTED
blockers                       GATE_NOT_ACCEPTED, SUPERSEDE_WELDED
```

and `render/world/assembly/r2/SHIPPING.md` mentions `hospitality` **zero** times.
**So the whole item was a question about geometry that is not in the film** — and
self-intersection is not a rendering defect in any case, because Cycles does not
care. Repairing it would have meant booleaning 15.7 M triangles and destroying
the per-solid `hd_id` / `hd_wear` / `hd_grime` attributes the materials read, to
fix something invisible in a world that does not contain it.

**And a second frame-dependence bug, one day after #90's.** Their first
measurement appended a single deck via `libraries.load` and got 18 pairs on one
deck against the tool's 6 across five. `sheet_facing` welds with
`np.round(Pw, 6)` in **world** space, so *the same deck measured at the origin
segments into different facets from the same deck 300 m out*, and the greedy
pairing then pairs different partners. They discarded the run.

> That is the **second** frame-dependent instrument failure in two items — #90's
> `matrix_world` reading identity on link-loaded objects, and now a world-space
> weld tolerance. Both produced plausible numbers. **On this project, any
> measurement that touches world coordinates should state which frame it welded
> or projected in, before its number is read.**

### Housekeeping

**And it was my own subagent.** I commissioned #120, waited 4.5 h through a box
that twice hit 0 GB, sent two check-ins that bounced, concluded it was dead, and
rebuilt its work worse. It had the answer the whole time and had asked twice for
somebody to stop duplicating it. **The coordination failure is mine, and it is
the more expensive half of this entry.**

`tools/winding_audit.py` is **theirs** and I have not touched it — the UNDECIDED
line now reports the reason the parity arm recorded, with three new hand-counted
controls and the verdict token `SHEET_FACING_UNDECIDED` unchanged so nothing
downstream re-gates. `world/items/hospitality_deck.py` is clean and needs no
repair. My earlier commit `7771717` stands in history with its wrong mechanism;
this is a **correcting commit, not an amend** — which is the remedy R2-234 asked
for and the one my own guard enforces.

**And they reproduced the untouched tool's 2026-08-04 output byte-identically
today.** That is the discriminator for "already fixed" versus "someone is fixing
it right now", and it is the second time in one session I have needed it — the
first was reading an uncommitted working tree as history.
