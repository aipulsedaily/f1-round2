# STAGING R2-2641 to R2-2700 — landing the r2-1761-debt backlog

Agent `r2-2641-land-debt`. 2026-08-08. Task #151.

Three bodies of finished work were reported as stranded behind the
`r2-1761-debt` lease. **Two of them landed. The third was already in `HEAD`
and needed nothing — it was landed hours ago under a different filename than
the one the handover named.** The one thing that could not be done is the one
the handover flagged: the live `pre-commit` hook.

---

## R2-2641 — the answer up front

| | |
|---|---|
| `8eb3c40` | `tools/gitguard.py`, `tools/gitguard_selftest.py` — the guard repairs |
| `6e8be7c` | `tools/placement_gate.py` — the R2-2341 determinism work, sha `93af5324216fe2e9` |
| — | the contract work (`_car_box()` from the contract) was **already committed** at `e241b2f` |
| **NOT DONE** | `gitguard.py install`. `tools/githooks/` is still leased by `r2-1761-debt`. |

**The live hook is still the old one — but only in its bypass branch.** See
R2-2645; the distinction is load-bearing and the handover's flat "the live hook
is still the old one" understates what is already active.

---

## R2-2642 — the guard repairs, verified against both guards

I did not take the reported figure on faith. `tools/gitguard_selftest.py` runs
entirely inside a throwaway repository and resolves the guard as its own
sibling, so pointing it at a different `gitguard.py` is a one-line control:

```
$ git show HEAD:tools/gitguard.py > $SCRATCH/gitguard.py
$ cp tools/gitguard_selftest.py $SCRATCH/
$ cd $SCRATCH && python3 gitguard_selftest.py
>> STAGE RESULT: FAIL (22 failures of 62 checks)

$ cd ~/f1-round2 && python3 tools/gitguard_selftest.py
>> STAGE RESULT: OK (0 failures of 62 checks)
```

**The harness file is byte-identical in the two runs.** That is what makes the
22 mean something: it is not a new test suite scoring its own new code, it is
one suite scoring two guards, and the 40 checks that predate this work pass in
both. Reported as 22 / 62 and 0 / 62; reproduced as 22 / 62 and 0 / 62.

Re-run after committing, from the committed tree:

```
>> STAGE RESULT: OK (0 failures of 62 checks)
```

What the 22 cover: `retire` (C16–C16n), per-path `claim` returning `PARTIAL`
(C15 family), the separable seed TTL (C17–C17c), and the `BYPASSED` result line
(C18–C18g).

Committed as **`8eb3c40`**.

---

## R2-2643 — the placement gate, verified against both gates

Same discipline. The gate needs Blender, so both runs are the same blend and
the same four frozen inputs, judged on the printed `STAGE RESULT` line because
Blender exits 0 on an uncaught script exception:

```
blend    render/world/assembly/r2/v120/ctl_place_neg.blend
inputs   work/r2-2341/frozen/{circuit_spec.json,telemetry.csv,
                              beat_sheet.json,camera_rig_path.json}
wrapper  bash tools/buildlock.sh ...

HEAD gate   sha aa9f0712d0690ba7   >> all 26 controls behaved
                                   >> STAGE RESULT: PLACEMENT_SELFTEST_OK
this gate   sha 93af5324216fe2e9   >> all 42 controls behaved
                                   >> STAGE RESULT: PLACEMENT_SELFTEST_OK
```

Reported as 26 → 42; reproduced as 26 → 42, zero `FAIL` rows in either. The
working-tree file's sha256 is `93af5324216fe2e97e29abacff09532004048ce2df176f7e7b5d7593015b56e6`,
which is the sha the R2-2341 staging doc names, so the file I committed is the
file that was measured.

The `HEAD` gate used for the control is `git show HEAD:tools/placement_gate.py`,
sha256 `aa9f0712d0690ba70049ecbf62121e57b4cb45d25b5429f82712afd895a0532a` — the
same pinned copy `work/r2-2341/repeat.sh` documents, i.e. `HEAD` had not moved
under `placement_gate.py` since that campaign.

Re-run after committing, from the committed tree:

```
>> all 42 controls behaved
>> STAGE RESULT: PLACEMENT_SELFTEST_OK
```

Zero `FAIL` rows in all three runs of the fixed gate.

Logs: `work/r2-2641/selftest_{HEAD,verify,postcommit}.log`.

Committed as **`6e8be7c`**.

### The end-to-end exit-3 control, reproduced against the committed gate

`tools/placement_determinism_control.py` wraps `placement_gate.measure` so the
second pass returns one changed `closest_approach` object name, runs the gate's
own `main()`, and requires a refusal — then removes the perturbation and
requires a verdict. Against the gate as committed at `6e8be7c`:

```
   PASS  a deliberately non-deterministic measure() is REFUSED   got=PLACEMENT_NONDETERMINISTIC_REFUSED  exit code 3
   PASS  ...and the refusal is NOT spelled as a pass             code 3
   PASS  the unperturbed run is NOT refused as non-deterministic verdict PLACEMENT_FAIL (exit 1)
   PASS  the unperturbed run reaches a real placement verdict    verdict PLACEMENT_FAIL
>> STAGE RESULT: PLACEMENT_DETERMINISM_CONTROL_OK
```

(The control file itself is leased by `r2-2341-placement-determinism` and is
not committed here — only run.)

### It is split from its own staging doc, deliberately

§8 of `docs/STAGING-R2-2341-to-R2-2400.md` asks for four paths in one commit.
Three of them — `tools/placement_determinism_control.py`,
`tools/placement_entropy_probe.py`, and the staging doc itself — are leased by
`r2-2341-placement-determinism`, which is not me:

```
$ R2_AGENT=r2-2641-land-debt python3 tools/gitguard.py claim tools/placement_entropy_probe.py
    tools/placement_entropy_probe.py -- ask r2-2341-placement-determinism to release it.  Do NOT set R2_AGENT=r2-2341-placement-determinism.
>> STAGE RESULT: FAIL (0 claimed, 1 clashes)
```

The same for `tools/placement_determinism_control.py` and
`docs/STAGING-R2-2341-to-R2-2400.md`: `FAIL (0 claimed, 1 clashes)` each,
naming the same owner.

I did not retire it and did not set `R2_AGENT` to that owner's name. The guard
would have refused me anyway — a live NAMED agent's lease is retirable by
nobody but its owner, which is control C16f — and being refused by the
mechanism I was landing an hour earlier is the mechanism working.

**The split loses no reproduction.** The rule that matters is *commit a
generator with anything derived from it*; `placement_gate.py` **is** the
generator and it is committed whole. Nothing derived from it went in with it.
The two held tools are controls that exercise the gate, not artefacts it
produced, and the staging doc is prose. They remain uncommitted in the working
tree for their owner.

---

## R2-2644 — a finding I got by running that control on the wrong blend

I first ran the determinism control against `ctl_place_neg.blend` — the
*negative* control scene — instead of `ctl_place_pos.blend`. It reported:

```
   FAIL  a deliberately non-deterministic measure() is REFUSED  got=PLACEMENT_CLEAN  exit code 0
>> STAGE RESULT: PLACEMENT_DETERMINISM_CONTROL_FAIL
```

That reads as *the gate failed to refuse a non-deterministic input*. **It is
not what happened.** The perturbation is:

```python
for k in sorted(closest):
    d, name, at = closest[k]
    closest[k] = (d, name + "_INJECTED", at)
    break
```

On a scene where nothing comes within bounding-box reach of any keep-out,
`closest` is **empty** — the report's `closest_approach_m` is three `null`
objects with `"measured, nothing close"` — so the loop body never runs, nothing
is injected, and the gate is entirely right to say `IDENTICAL`.

**The control is vacuous on any scene with no near approach, and it does not
say so.** It fails safe — it never spells the vacuum as a pass, which is more
than most of the instruments in this log manage — but its failure text names
the wrong culprit, and an agent who hits this while the gate is genuinely
healthy will spend the evening on `placement_gate.py`.

`tools/placement_determinism_control.py` is leased by
`r2-2341-placement-determinism`, so **I have not touched it.** The one-line
repair for its owner: assert that `closest` was non-empty before trusting the
result, e.g. fail with `the perturbation had nothing to perturb — this blend
cannot exercise this control` rather than with the gate's verdict. Evidence:
`work/r2-2641/determinism_control{,_pos}.{log,json}`.

## R2-2645 — the contract work was already in HEAD, under a filename nobody named

The handover described `_car_box()` deriving the four car-box numbers from the
contract instead of retyping `5.698, 2.005, 0.992, 0.340`, in
`world/world_contract.py`, `world/build_dressing.py` and
`world/items/spectator_crowd.py`.

**All three of those files are clean against `HEAD`.** There is no `_car_box`
in any of them. There never was:

```
$ grep -rn "_car_box" --include=*.py .
world/build_surface.py:4144:    _car_box(scene, station)
world/build_surface.py:4278:def _car_box(scene, station, name="TEST_CarBox"):
world/build_surface.py:4697:            _car_box(scene, station, "TEST_CarBox_" + nm)
tools/placement_gate.py:1566:  rows[-1]["shipped_car_box_worst_delta_m"] = was_worst
```

The function lives in `world/build_surface.py`, which is leased by
`r2-2521-contract-leftovers` — and that agent committed it itself, at
**`e241b2f`**, together with its evidence in
`docs/STAGING-R2-2521-to-R2-2580.md` (the 48 024 IEEE-754 doubles, and the
2001/2001 poses that move 0.3400 m under the historical fault). `git status`
is empty for `world/build_surface.py`. The earlier half —
`world/world_contract.py` and `world/build_dressing.py` — landed at `de3a1aa`.

Nothing to land. **Recording it because a handover that names three innocent
files as carrying stranded work is how a later agent ends up "re-landing" a
change by rewriting a clean file.** I claimed all three, found them clean, and
committed nothing to them.

The same is true of five of the eleven released paths: `tools/provenance.py`,
`tools/report_repro.py`, `tools/report_repro_selftest.py`,
`tools/placement_depth.py` and `tools/selfintersect_audit.py` are all clean
against `HEAD` — `r2-1761-debt` had already committed them at `4d4ba35` and
`2cc018d` before its lease outlived it. Of the eleven paths released, **three
carried uncommitted work; eight were already landed.**

---

## R2-2646 — the live hook: what is repaired and what is not

`core.hooksPath` is `tools/githooks`, so the live hook is a *worktree file*,
and that path is leased:

```
$ R2_AGENT=r2-2641-land-debt python3 tools/gitguard.py claim tools/githooks/
  tools/githooks/ -- ask r2-1761-debt to release it.  Do NOT set R2_AGENT=r2-1761-debt.
>> STAGE RESULT: FAIL (0 claimed, 1 clashes)
```

`gitguard.py install` writes that file directly with `open()`. The guard only
polices *commits*, so `install` would have succeeded — and overwritten another
owner's leased worktree file, which is exactly the thing the lease exists to
prevent. **I did not run it.** Nor did I point `core.hooksPath` somewhere else:
a hook directory that is not the one everybody's `install` writes to is a worse
outcome than a stale hook, because it is invisible.

**But "the live hook is still the old one" is too coarse.** Diffing the two
files against the committed templates:

| hook | state |
|---|---|
| `tools/githooks/prepare-commit-msg` | **already identical to the repaired template** — no install needed |
| `tools/githooks/pre-commit` | differs **only inside the `R2_GITGUARD=off` branch** |

Everything the hook does on a normal commit is one line — `python3
tools/gitguard.py check` — and `tools/gitguard.py` is now the repaired one, as
of `8eb3c40`. So **R1/R2/R3, `PARTIAL`, `retire`, the seed TTL and the
`check`-side bypass announcement are all live right now.** Verified against the
live tree, read-only:

```
$ R2_GITGUARD=off R2_AGENT=r2-2641-land-debt python3 tools/gitguard.py check
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  This is NOT a pass.  Unset R2_GITGUARD and run again to
  find out what the guard would have said.
>> STAGE RESULT: BYPASSED (guard disabled by R2_GITGUARD=off)
```

What is **still old**, and only this: if somebody sets `R2_GITGUARD=off` and
commits, the shell hook short-circuits before it ever reaches `gitguard.py`,
and in that branch the installed copy still

- prints one quiet line, `R2 GITGUARD BYPASSED (R2_GITGUARD=off) -- logged.`,
  with **no** banner and **no** `>> STAGE RESULT:` line at all — so a bypassed
  commit's output is still mistakable for a checked one (C18, C18b);
- logs the actor but **not the staged paths** (C18c);
- ignores `.git/r2-guard/no-bypass` entirely, so the opt-in refusal cannot be
  turned on (C18f, C18g).

`.git/r2-guard/bypass.log` does not exist, so no commit has taken that branch
in this repository yet.

**TO ACTIVATE, when `r2-1761-debt`'s lease on `tools/githooks/` clears** — it
was created `2026-08-07T22:12:03` and the TTL is 24 h, so it lapses at
**~22:12 on 2026-08-08**, about six and a half hours from this writing — **or
is retired by its owner:**

```
R2_AGENT=<you> python3 tools/gitguard.py claim tools/githooks/
python3 tools/gitguard.py install
git add tools/githooks/pre-commit          # path-scoped, never -A
R2_AGENT=<you> git commit -- tools/githooks/pre-commit
```

`install` is idempotent and rewrites both hooks from the committed templates;
only `pre-commit` will show a diff.

---

## R2-2647 — housekeeping

- `tools/_r2641_gate_HEAD.py` is the pinned `HEAD` gate used for the 26-control
  control. It is **not for committing** and is regenerated with
  `git show ca942f5:tools/placement_gate.py` (the commit that was `HEAD` before
  `8eb3c40`; naming the hash rather than `HEAD~2` because `HEAD` moves under
  you here). Deleted after use.
- `docs/DEFECT-LOG-R2.md` deliberately untouched; the coordinator merges it.
- Every commit was made with `R2_AGENT` set **in the environment of the `git
  commit` itself**, and `git diff --cached --name-only` was read and recognised
  before each one. Neither commit staged a path this agent did not lease.
- The eleven paths released to me were claimed **one at a time**, all eleven
  `OK (1 claimed, 0 clashes)`. `docs/STAGING-R2-2641-to-R2-2700.md` makes twelve.
- The first commit's hook reported `auto-leased 55 dirty path(s) that nobody
  had claimed`. That is `inflight-auto` doing its job — it self-prunes as those
  paths get committed — not a lease this agent took. Worth knowing before
  somebody reads a fresh refusal as a new problem.
- The build lock was honoured. The post-commit gate re-run queued behind
  `r2-2701-libprobe-a14` for several minutes rather than racing it, exactly as
  `tools/buildlock.sh` intends.
