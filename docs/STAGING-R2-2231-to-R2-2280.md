# STAGING R2-2231 .. R2-2280 — repairs to `tools/gitguard.py`

R2-2229 and R2-2230 record defects 1 and 2 *as found*. This file records the
**repairs**, the controls that prove them, and two things nobody was looking
for. `docs/DEFECT-LOG-R2.md` is not edited here; the coordinator merges it.

The guard was built to stop one agent's commit clobbering another's work. On
the evening of 2026-08-07 it spent its time blocking authors from committing
their own files, and by 06:30 it was **causing the loss it was built to
prevent** — not by letting anyone clobber anything, but by keeping finished,
gated work out of the only place it would be safe from `git checkout`.

---

## R2-2231 — `claim` was all-or-nothing, so it misreported its own state

**Found.** Measured verbatim, seven paths of which four were freely claimable:

```
claim (all 7)  -> CLASH audio/verify.py, audio/master.py, tools/audio_watch_clips.py
                  >> FAIL (3 clashes, nothing claimed)
claim (the 4)  -> (4 path(s) released from inflight-auto -- an explicit claim wins)
                  >> OK (0 clashes)
```

One stale entry in an argument list turned a partial block into a total one.
Two agents read the first line as a hard refusal and stalled; it took three
separate commands to discover the real shape.

**Why this was the more serious of the two defects.** A stale lease at least
names the path it holds. A guard that answers *"no"* when the truth is *"four
of seven"* is misreporting its own state, and there is no way to recover the
truth from its output — you have to bisect the argument list by hand.

**Fixed.** `cmd_claim` now partitions per path and prints both halves:

```
CLAIMED  docs/STAGING-R2-2231-to-R2-2280.md
CLASH    tools/gitguard.py  held by r2-1761-debt (agent, via tools/gitguard.py, 8.4 h old)
CLASH    tools/gitguard_selftest.py  held by r2-1761-debt (agent, via ..., 8.4 h old)

  claimed 1 of 3 requested for r2-2231-gitguard; lease now holds 1 path(s)
>> STAGE RESULT: PARTIAL (1 claimed, 2 clashes)
```

**The exit status, decided deliberately** (written out in the docstring at the
call site, not only here). An agent scripting against this must be able to tell
*"nothing claimed"* from *"most claimed"*, and one bit cannot carry three
outcomes, so there are three codes:

| rc | STAGE RESULT | meaning |
|----|--------------|---------|
| 0  | `OK`         | every requested path is now yours |
| 3  | `PARTIAL`    | some are yours, some clashed |
| 1  | `FAIL`       | nothing was claimed; every path clashed |

`3` is new and is chosen so that the old `rc != 0` test keeps its old meaning
exactly — *you did not get everything you asked for*. The STAGE RESULT word is
the primary channel (this project judges on that line) and `PARTIAL` is neither
`OK` nor `FAIL`, so a caller grepping for `OK` gets the conservative answer
rather than a false pass.

**The atomicity is not removed, only defaulted away.** `claim --atomic` still
does exactly what the old command did, and the partial case announces itself
at the call site rather than silently. Control C15h holds that path open.

---

## R2-2232 — a manual seed outlived its session and became a blanket refusal

`inflight-2026-08-07` held 305 paths, was 8.4 h old against a 24 h TTL, and had
no way to expire and no legitimate way for a coordinator to retire part of it.

The reasoning in the old comment at `cmd_claim` — *that set is somebody's
unfinished work from before the guard existed, and saying so out loud once is
the entire point of it* — **is sound and is still in the file.** It was never
the defect. The defect was that "once" had no way to end.

### (a) The legitimate retirement path: `gitguard.py retire`

The only mechanism that existed was

```
R2_AGENT=inflight-2026-08-07 tools/gitguard.py release <path>
```

— setting your identity to another owner's name to release their lease.
Whatever the intent, the **shape** of that is impersonating a lease owner; a
safety classifier refused it and was right to. A guard whose only escape hatch
looks like impersonation gets routed around. `retire` is that hatch built in
the open.

**Four independent reasons it cannot take a path from a live agent** — four,
because one would be an assertion, and this project has been burned by
assertions:

- **S1** It only ever edits a lease whose owner is *seed-shaped* (`inflight`,
  `inflight-*`). A named agent's lease is refused outright, at any age, and
  **there is no `--force`**. S1 also refuses a path that a seed and a live
  named agent *both* hold — see the note below.
- **S2** A seed younger than `--min-age-h` (default 8 h) is refused, so a fresh
  seed still does its job.
- **S3** It only ever *removes* entries. There is no code path by which
  retiring transfers ownership to the caller. What it produces is an **unowned**
  path, which the rightful author then claims under their own name.
- **S4** It refuses to run when `R2_AGENT` equals the lease owner — the exact
  impersonation shape above — and requires a real identity, which is written to
  `.git/r2-guard/retire.log` with every path retired.

It is a **dry run unless `--apply`** and prints every path either way.

**S1 was widened by a control, not by design.** C17c ran `retire --min-age-h 0`
against a path held by *both* a stale seed and a live agent. The first version
retired the seed's copy and reported `OK` — while the named owner still held it
and the guard still refused every commit of it. `0 retired` would have been
honest; an `OK` that leaves the path exactly as blocked as before is the same
misreporting-its-own-state defect as R2-2231. A live named holder now blocks the
path outright, in every mode.

### (b) A seed and a working agent's lease no longer share one lifetime

`R2_GUARD_TTL_H` is global: lowering it to 8 to expire this seed would have
simultaneously expired `inflight-auto` and every named agent committing at that
moment. Rejected.

Seeds now have their own clock, `R2_GUARD_SEED_TTL_H`, which **defaults to the
global one** — nothing changes for anybody today. The point is only that the
two are now *separable*, so a coordinator can shorten a seed's life without
shortening a working agent's. C17/C17b prove both halves: the knob expires the
seed, and the same knob leaves a live agent's lease refusing.

`DEFAULT_RETIRE_MIN_AGE_H` (8 h) is **not** a TTL — nothing expires on its own
at 8 h. It is the age below which the guard refuses to believe a seed is
abandoned.

### Live proof, both directions, on the real repository

```
$ R2_AGENT=r2-2231-gitguard gitguard.py retire --apply tools/author_beats2_5.py
  seed inflight-2026-08-07  (age 8.41 h, 305 path(s) held, TTL 24 h)
  retiring 1 path(s):
    tools/author_beats2_5.py
  These paths are now UNOWNED, not yours.  Claim what is yours:
>> STAGE RESULT: OK (1 retired, 0 refusal(s))

$ R2_AGENT=r2-2231-gitguard gitguard.py retire --apply tools/gitguard.py
  REFUSED [S1] r2-1761-debt
    r2-1761-debt is a NAMED AGENT's lease (LIVE, 8.36 h old), not a seed.
    retire never touches one, at any age, and there is no --force.
>> STAGE RESULT: FAIL (0 retired, 1 refusal(s))          rc=2
```

The refusal was reproduced against all three live agents named in the brief —
`r2-1761-debt`, `r2-2041-carbon-rubber`, `r2-2101-breach-strip` — including on
**this author's own assigned file**, which the command refuses him too.

---

## R2-2233 — the escape hatch that looked like a guard

`R2_GITGUARD=off` printed one quiet line to stderr and exited 0, and the commit
looked exactly like a checked one. Worse, the hook exited *before* ever calling
python, so an agent that had **inherited** the variable from a parent shell it
never wrote could run `gitguard.py check`, get the full guard run, and read a
clean `>> STAGE RESULT: OK` that the hook was never going to enforce.

- The hook now prints a four-line banner naming the variable and the agent,
  logs the **staged path list** as well as the actor, and its STAGE RESULT line
  is `BYPASSED` — **never `OK`**.
- `check`, `claim` and `status` announce the variable from inside python, so
  the direct-invocation path cannot answer `OK` either.
- `status` reports how many bypassed commits are in `bypass.log` and shows the
  last three. A bypass nobody looks at is barely better than a silent one.
- **It is refusable.** `touch .git/r2-guard/no-bypass` makes the hook refuse the
  bypass outright. Opt-in, because turning it on retroactively would strand an
  agent relying on the bypass right now; the banner is unconditional.

**The installed hook in this repository has not been updated.** `tools/githooks/`
is leased by the live agent `r2-1761-debt`, so re-running `gitguard.py install`
would dirty another agent's leased files. The template in `gitguard.py` is
fixed and proven by C18; **the live hook needs one `gitguard.py install` once
that lease frees.** Until then the python-side announcements are in force and
the hook's bypass line is the old quiet one.

---

## R2-2234 — the `pid` field was never a liveness signal and looked exactly like one

Found while auditing the stale seed. Every lease recorded `os.getpid()` — the
pid of the one-shot `gitguard.py claim` process, which has **already exited** by
the time the command returns. Checked against `/proc`:

```
inflight-2026-08-07   pid=1839836  alive=False
inflight-auto         pid=1878989  alive=False
r2-1761-debt          pid=1842320  alive=False
r2-2041-carbon-rubber pid=1955661  alive=False
r2-2101-breach-strip  pid=1972067  alive=False
r2-2161-pacing        pid=2004008  alive=False   <- created four minutes earlier
...                                                 by an agent demonstrably working
```

All eight dead, with no error, including one created four minutes before the
check. Anyone reaching for it to decide whether an agent is still around gets
*"everyone is dead"*, every time — the same shape as the fingerprint that
covered zero modules while reporting success. It is written as `claim_pid` now
and nothing reads it. There is no liveness signal to replace it with: **an agent
is a conversation, not a process.** The honest answers are the lease's age and
its `updated` stamp.

---

## The seed's 305 paths: measured, not assumed

The question was whether they are genuinely somebody's unfinished work or
largely abandoned. Measured at 06:35 on 2026-08-08:

| | |
|---|---|
| still dirty in the worktree | **304 / 304** |
| of which **untracked** (new files, never committed) | 277 |
| of which tracked-and-modified | 27 |
| under `tmp/` (scratch, untracked **and unignored**) | **160** |
| also held by a live named agent | 0 |
| real source outside `tmp/` (`.py`/`.sh`) | 69 |
| `docs/*.md` | 8 |

Last-written age:

| age | count |
|---|---|
| < 8 h | **8** |
| 8–12 h | 9 |
| 12–24 h | 36 |
| 1–3 days | 47 |
| **> 3 days** | **204** |

**The answer is: largely abandoned, and the fraction that is not abandoned is
the part the seed was hurting.** Two-thirds of the set has not been written in
over three days. Over half of it is scratch debris under `tmp/`, swept in only
because `seed-inflight` claims the entire dirty set and `tmp/` is untracked but
not ignored. Eight paths have been touched in the last eight hours.

The one confirmed casualty is the clearest case of all.
`tools/author_beats2_5.py` — the generator for `docs/beat_sheet.json`, the
camera beat sheet the whole film is authored from — is **not unfinished work
from a vanished session.** It is finished, gated work belonging to an agent that
is alive right now and cannot commit it, because `HEAD`'s copy of the generator
does not contain the beat-5 feature at all (`frame_u` 0 vs 47) and the sheet
cannot land without it. The seed swept in a path whose author is still at the
keyboard, and then had no way to let go.

**Recommendation:** `tmp/` belongs in `.gitignore`. It is 53 % of the seed, none
of it is anybody's afternoon, and every one of those entries is a future false
refusal. That alone would have made this seed a fifth of its size.

---

## Controls

Every new control was run against the **pre-fix** guard first — `git show
HEAD:tools/gitguard.py` beside the new selftest — and every one of them failed.
A control that has never been observed to fail is not a control.

```
fail-first (new selftest, pre-fix guard):   >> STAGE RESULT: FAIL (22 failures of 62 checks)
after the repairs:                          >> STAGE RESULT: OK   (0 failures of 62 checks)
```

All 40 pre-existing controls passed in **both** runs, so the harness itself is
not what changed.

New controls, and what each one is worth:

| control | proves | failed pre-fix? |
|---|---|---|
| C15, C15c, C15e | a mixed claim reports the true partition and does **not** claim zero | yes |
| C15b | the clashes are named with their owner | no — the old guard did this |
| C15d, C15f, C15g | vacuity: all-free is still `OK`, all-clash is still `FAIL`, nothing extra was taken | no — hold the ends fixed |
| C15h | `--atomic` still gives the old all-or-nothing behaviour | no — by construction |
| C16, C16b, C16d, C16e | retire dry-runs, then retires exactly one seed path, logs the actor, and the path reaches a commit | yes |
| C16c | retire gives the path to **nobody**, least of all the retirer | no — vacuous pre-fix |
| C16f, C16h, C16k, C16l, C16m | it refuses: a live agent's path, `--owner <agent> --all-paths`, a fresh seed, the impersonation shape, no identity | yes |
| C16g, C16i, C16j, C16n | and after every refusal the lease is byte-identical and still has teeth | no — vacuous pre-fix |
| C17 | `R2_GUARD_SEED_TTL_H=0` expires the seed | yes |
| C17b | **the same knob does not expire a live agent's lease** | no — vacuous pre-fix |
| C17c | `--min-age-h 0` is not a way into a named lease either | yes |
| C18 .. C18e | the bypass announces itself, never says `OK`, logs the staged paths, and `status` surfaces it | yes |
| C18f, C18g | the bypass is refusable, and the identical commit passes once the marker is gone | yes |

Six of the new controls pass in both states. They are listed as such on
purpose: they are not evidence of the repair, they are there to catch the
repair breaking them, and calling them proof would be the vacuity this file
exists to avoid.

---

## Still open

**The guard has no way to represent a reassignment.** `tools/gitguard.py` and
`tools/gitguard_selftest.py` — the files repaired here — are leased by the live
agent `r2-1761-debt`. The repairs are written, proven by 62 controls, and
**cannot be committed by their author**, which is the exact failure this file
documents. There is no legitimate command for it and one was deliberately not
invented: any coordinator override an agent can type is an override every agent
can type, and that is the guard undone. It needs a human, or the owner's
release. See the note in the handover.
