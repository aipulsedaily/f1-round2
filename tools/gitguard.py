#!/usr/bin/env python3
"""THE SHARED INDEX HAS AN OWNER PER PATH, AND GIT IS MADE TO ENFORCE IT.

Defect #115.  This repository is worked by several agents at once.  The
standing rule has always been *path-scope every `git add`, never `-A`*, and it
is written into `docs/SESSION-HOLD.md`, into every agent brief, and into the
defect log four separate times.  It has still been violated twice, and each
violation swept another agent's in-flight source files into a commit that did
not own them (R2-226 took four of R2-274's files; see also R2-234, where
`git commit --amend` rewrote a *different agent's* commit message because
`--amend` takes whatever `HEAD` happens to be).

    A WARNING IS NOT A MECHANISM.

The mechanism is a lease.  An agent claims the paths it is working on; the
`pre-commit` hook refuses any commit that stages a path leased by somebody
else, and names the owner.  Nothing is lost when it fires -- the index is left
exactly as it was -- so a false refusal costs one command and a true refusal
saves somebody's afternoon.

WHY THE LEASES LIVE IN `.git/`
------------------------------
`docs/SESSION-HOLD.md` line 23: files in the worktree "are not safe from
`git checkout` or `git add -A`".  A lease store in the worktree would be
swept by the very command it exists to refuse, and reverted by the very
checkout it exists to survive.  `.git/r2-guard/` is outside the index by
construction: `git add -A` cannot stage it and `git checkout` cannot touch it.

WHAT IT REFUSES, AND WHAT IT DELIBERATELY DOES NOT
--------------------------------------------------
It refuses ONLY on positive detection:

  R1  a staged path is held by a live lease whose owner is not you
  R2  a staged path is held by a live lease and you have no identity at all
      (`R2_AGENT` unset) -- an anonymous committer cannot own anything
  R3  `git commit --amend` (R2-234), unless `R2_AMEND_OK=1`

A staged path that nobody has leased is ALLOWED.  That keeps the false-positive
rate at zero and means the guard can be installed into a live repository with
six agents mid-flight without stopping any of them.  The price is that the
guard protects exactly those paths somebody has claimed -- so `seed-inflight`
exists to claim, in one command, everything that is dirty right now, which is
by definition somebody's unfinished work.

FAILING OPEN, ON PURPOSE
------------------------
Any internal error in this file ALLOWS the commit and prints a loud warning.
A guard that bricks six agents' commits because of its own bug is a worse
outcome than the defect it guards, and this project has spent the day
discovering that its instruments were the problem more often than its renders
were.  `R2_GITGUARD=off` bypasses it and logs the bypass to
`.git/r2-guard/bypass.log`.

USAGE
-----
    tools/gitguard.py install                 # sets core.hooksPath
    R2_AGENT=me tools/gitguard.py claim world/items/foo.py docs/BAR.md
    R2_AGENT=me tools/gitguard.py release world/items/foo.py
    tools/gitguard.py seed-inflight --owner inflight-2026-08-07
    R2_AGENT=me tools/gitguard.py retire <path>          # preview
    R2_AGENT=me tools/gitguard.py retire --apply <path>  # stale SEEDS only
    tools/gitguard.py status
    tools/gitguard.py check                   # what the hook runs
    tools/gitguard.py selftest                # controls, incl. ones that FAIL

`check` prints exactly one `>> STAGE RESULT:` line.  Blender exits 0 on an
uncaught exception and this project judges on that line rather than on `$?`;
this file keeps the same convention even though it is not Blender, because the
people reading its output are looking for that line.
"""
import os
import sys
import json
import time
import fnmatch
import subprocess
import datetime

def _hours(name, default):
    """A malformed TTL must not turn the guard into a crash.

    A hook that dies with a traceback exits non-zero and BLOCKS every commit in
    the repository, which is the failure mode this file is most afraid of.
    """
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return float(default)


TTL_HOURS = _hours("R2_GUARD_TTL_H", "24")

# A SEED AND A WORKING AGENT'S LEASE MUST NOT SHARE ONE LIFETIME.  (R2-2232.)
#
# `inflight-2026-08-07` held 305 paths for over eight hours against a 24 h TTL
# and had become a blanket refusal: it was seeded to protect work from before
# the guard existed, that session is gone, and the lease is not.  The only knob
# that could expire it was `R2_GUARD_TTL_H`, which is GLOBAL -- lowering it to
# 8 would have simultaneously expired three agents that were committing through
# the guard at that moment.  Any fix with that blast radius is the wrong fix.
#
# So a seed now has its own clock.  It DEFAULTS TO THE GLOBAL ONE, which means
# nothing changes for anybody today -- the point is only that the two are now
# separable, so a coordinator can shorten a seed's life without shortening a
# working agent's.  The deliberate, path-granular version of that is `retire`.
SEED_TTL_HOURS = _hours("R2_GUARD_SEED_TTL_H",
                        os.environ.get("R2_GUARD_TTL_H", "24"))

# `retire` will not touch a seed younger than this.  It is NOT a TTL: nothing
# expires on its own at 8 h.  It is the age below which the guard refuses to
# believe a seed is abandoned, and it is deliberately shorter than the 24 h
# working TTL because a seed is a snapshot of one moment, not a session: the
# auto-lease has re-described the tree many times over by the time a seed is
# this old, and what the snapshot still holds is no longer anybody's afternoon.
DEFAULT_RETIRE_MIN_AGE_H = _hours("R2_GUARD_RETIRE_MIN_AGE_H", "8")


# --------------------------------------------------------------------------
# git plumbing
# --------------------------------------------------------------------------
def git(*args, cwd=None, check=True):
    p = subprocess.run(["git"] + list(args), cwd=cwd,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode != 0:
        raise RuntimeError("git %s failed: %s"
                           % (" ".join(args), p.stderr.decode(errors="replace")))
    return p.stdout.decode(errors="replace")


def git_dir(cwd=None):
    return os.path.abspath(os.path.join(
        cwd or os.getcwd(), git("rev-parse", "--git-dir", cwd=cwd).strip()))


def repo_root(cwd=None):
    return git("rev-parse", "--show-toplevel", cwd=cwd).strip()


def lease_dir(cwd=None):
    d = os.path.join(git_dir(cwd), "r2-guard", "leases")
    os.makedirs(d, exist_ok=True)
    return d


def staged_paths(cwd=None):
    """Paths in the INDEX, relative to the repo root.

    `--cached` against HEAD, or against the empty tree on an unborn branch --
    a repository with no commits yet has no HEAD to diff, and the selftest
    builds exactly such a repository.
    """
    try:
        git("rev-parse", "--verify", "HEAD", cwd=cwd)
        out = git("diff", "--cached", "--name-only", "-z", cwd=cwd)
    except RuntimeError:
        out = git("diff", "--cached", "--name-only", "-z",
                  "4b825dc642cb6eb9a060e54bf8d69288fbee4904", cwd=cwd)
    return [p for p in out.split("\0") if p]


def dirty_paths(cwd=None):
    """Everything modified, staged or untracked, relative to the repo root."""
    out = git("status", "--porcelain=v1", "-z", "--untracked-files=all", cwd=cwd)
    fields, res = [f for f in out.split("\0") if f], []
    i = 0
    while i < len(fields):
        f = fields[i]
        code, path = f[:2], f[3:]
        if "R" in code and i + 1 < len(fields):        # rename: dest \0 src
            res.append(fields[i + 1])
            i += 1
        res.append(path)
        i += 1
    return sorted(set(res))


# --------------------------------------------------------------------------
# leases
# --------------------------------------------------------------------------
def now_iso():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def load_leases(cwd=None):
    """Every lease on disk, each tagged live/expired.

    Expiry is what stops a terminated agent from bricking the repository
    forever.  Two agents were killed by a weekly usage limit mid-task on this
    project (docs/RESUME-HERE.md); their leases must not outlive them.
    """
    out = []
    d = lease_dir(cwd)
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        try:
            lease = json.load(open(os.path.join(d, name)))
        except Exception as exc:                                  # noqa: BLE001
            out.append({"owner": name[:-5], "paths": [], "BROKEN": repr(exc),
                        "live": False, "age_h": None, "kind": "agent",
                        "ttl_h": TTL_HOURS})
            continue
        try:
            created = datetime.datetime.fromisoformat(lease.get("created", ""))
            age_h = (datetime.datetime.now() - created).total_seconds() / 3600.0
        except Exception:                                         # noqa: BLE001
            age_h = 0.0
        seed = is_seed_owner(lease.get("owner"))
        lease["age_h"] = age_h
        lease["kind"] = "seed" if seed else "agent"
        lease["ttl_h"] = SEED_TTL_HOURS if seed else TTL_HOURS
        lease["live"] = age_h <= lease["ttl_h"]
        out.append(lease)
    return out


def save_lease(lease, cwd=None):
    """Write a lease.

    THE `pid` FIELD WAS NEVER A LIVENESS SIGNAL AND LOOKED EXACTLY LIKE ONE.
    (R2-2234, found while auditing the stale seed.)  Every lease recorded
    `os.getpid()` -- the pid of the one-shot `gitguard.py claim` process, which
    has already exited by the time the command returns.  Checked against
    /proc, ALL EIGHT leases in the live repository reported a dead pid,
    including one created four minutes earlier by an agent that was demonstrably
    working.  A reader reaching for it to decide whether an agent is still
    around gets "everyone is dead", every time, with no error: the same shape as
    the fingerprint that covered zero modules while reporting success.  It is
    written as `claim_pid` now, and nothing reads it.  There is no liveness
    signal here to replace it with -- an agent is a conversation, not a process
    -- so the honest answers are the lease's own age and its `updated` stamp.
    """
    p = os.path.join(lease_dir(cwd), "%s.json" % lease["owner"])
    tmp = p + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(lease, fh, indent=2, sort_keys=True)
    os.replace(tmp, p)


def holds(lease_path, staged):
    """Does a leased entry cover this staged path?

    Three forms, because all three get used in practice and a guard that only
    understood exact paths would be trivially stepped around:
      exact          world/items/foo.py
      directory      world/items/          (or world/items)
      glob           tools/audio_*.py
    """
    if lease_path == staged:
        return True
    d = lease_path.rstrip("/")
    if staged.startswith(d + "/"):
        return True
    if any(c in lease_path for c in "*?[") and fnmatch.fnmatch(staged, lease_path):
        return True
    return False


def me():
    return os.environ.get("R2_AGENT", "").strip()


# `inflight`, `inflight-auto`, `inflight-2026-08-07`: the stand-in owners the
# guard invents for work whose real author never called `claim`.  A seed owner
# is nobody -- that is the whole point of it -- and `retire` is allowed to act
# on nobody.  Every real agent on this project is named `r2-<ticket>-<topic>`,
# and NO NAMED OWNER IS EVER RETIRABLE, at any age, by any flag.  The prefix is
# therefore reserved: an agent that calls itself `inflight-something` has
# claimed a stand-in name and will be treated as one.
SEED_OWNER_PREFIX = "inflight"


def is_seed_owner(owner):
    owner = (owner or "").strip()
    return owner == SEED_OWNER_PREFIX or owner.startswith(SEED_OWNER_PREFIX + "-")


# --------------------------------------------------------------------------
# detecting `--amend`, which is harder than it looks
# --------------------------------------------------------------------------
def invoking_git_argv():
    """The argv of the `git` process that is running this hook.

    THE OBVIOUS DETECTOR DOES NOT WORK, and the selftest is what found that
    out.  `prepare-commit-msg` is documented to receive source="commit" and
    the SHA when amending -- but only when git is reusing the old message.
    `git commit --amend -m "..."` passes source="message" and no SHA, so a
    hook keyed on that argument sails straight past the exact command that
    rewrote another agent's commit in R2-234.

    Git runs hooks as direct children, so on Linux the real argv is readable
    from /proc.  Walk up from this process (python3 <- sh <- git) until a
    `git` with `commit` in its argv turns up.  If /proc is not readable the
    caller gets (None, []) and falls back to the prepare-commit-msg hook,
    which still catches the interactive `--amend` with no -m.
    """
    pid = os.getpid()
    for _ in range(6):
        try:
            with open("/proc/%d/stat" % pid, "rb") as fh:
                # comm can contain spaces and parens; ppid is the field after
                # the final ')'.
                stat = fh.read().decode(errors="replace")
            pid = int(stat[stat.rfind(")") + 1:].split()[1])
            if pid <= 1:
                break
            with open("/proc/%d/cmdline" % pid, "rb") as fh:
                argv = [a.decode(errors="replace")
                        for a in fh.read().split(b"\0") if a]
        except Exception:                                         # noqa: BLE001
            return None, []
        if argv and os.path.basename(argv[0]).startswith("git") \
                and "commit" in argv:
            return True, argv
    return None, []


def amend_violation():
    found, argv = invoking_git_argv()
    if found and "--amend" in argv:
        return {"rule": "R3", "argv": argv}
    return None


# --------------------------------------------------------------------------
# the check the hook runs
# --------------------------------------------------------------------------
BYPASS_BANNER = [
    "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",
    "!!  R2 GITGUARD IS OFF.  R2_GITGUARD=off IS SET IN THIS SHELL.  !!",
    "!!  NOTHING BELOW HAS BEEN CHECKED AGAINST ANYBODY'S LEASE.     !!",
    "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",
]


def bypassed():
    return os.environ.get("R2_GITGUARD") == "off"


def announce_bypass_env():
    """AN ESCAPE HATCH INDISTINGUISHABLE FROM SUCCESS IS WORSE THAN NO GUARD.

    R2-2233.  `R2_GITGUARD=off` used to be invisible from inside python: the
    hook exited before ever calling this file, so an agent that SET the
    variable -- or, worse, INHERITED it from a parent shell it never wrote --
    got a silent `git commit` and a clean `>> STAGE RESULT: OK` from a
    subsequent `gitguard.py check`, which had cheerfully run the full guard and
    reported a pass that the hook was never going to enforce.

    Every command now says so, and the STAGE RESULT word for a bypassed check
    is BYPASSED -- never OK.  This project judges on that line, so a caller
    grepping for OK gets the conservative answer instead of a false pass.
    """
    if bypassed():
        for line in BYPASS_BANNER:
            print(line)
        return True
    return False


def check(cwd=None, verbose=True):
    """Returns (ok, [violation dicts]).  Never raises -- see FAILING OPEN."""
    if bypassed():
        # The installed hook exits before reaching here, so this is the
        # direct-invocation path -- an agent asking "am I clear to commit?".
        # It must not be told OK by a guard that has been switched off.
        if verbose:
            for line in BYPASS_BANNER:
                print(line)
            print("  identity        R2_AGENT=%s" % (me() or "<UNSET>"))
            print("  staged paths    %d" % len(staged_paths(cwd)))
            print("")
            print("  This is NOT a pass.  Unset R2_GITGUARD and run again to")
            print("  find out what the guard would have said.")
            print("  Every bypassed commit is appended to .git/r2-guard/bypass.log.")
            print(">> STAGE RESULT: BYPASSED (guard disabled by R2_GITGUARD=off)")
        # Fails OPEN on purpose -- see the module docstring.  The exit code
        # stays 0 so that a bypass behaves like a bypass; the STAGE RESULT
        # line, which is what this project reads, never says OK.
        return True, []
    staged = staged_paths(cwd)
    autoseeded = auto_seed(staged, cwd)
    leases = load_leases(cwd)
    who = me()
    violations = []

    am = amend_violation()
    if am and os.environ.get("R2_AMEND_OK") != "1":
        if verbose:
            print("R2 GITGUARD  (defect #115)")
            print("")
            print("  REFUSED -- git commit --amend.  (R2-234)")
            print("")
            print("  `git add` takes a path.  `--amend` takes whatever HEAD")
            print("  happens to be, and in a tree with concurrent agents that is")
            print("  not necessarily yours.  It has already rewritten another")
            print("  agent's commit message on this repository.")
            print("")
            print("  Write a correcting commit, or `git notes add` on the commit")
            print("  you meant to fix.  R2_AMEND_OK=1 overrides if you are certain")
            print("  HEAD is yours -- check with `git log -1 --format=%%H %%s`.")
            print(">> STAGE RESULT: FAIL (1 violations)")
        return False, [am]

    for path in staged:
        for lease in leases:
            if not lease.get("live"):
                continue
            if lease.get("owner") == who and who:
                continue
            for lp in lease.get("paths", []):
                if holds(lp, path):
                    violations.append({
                        "path": path, "owner": lease.get("owner"),
                        "lease_entry": lp, "age_h": round(lease.get("age_h") or 0, 2),
                        "rule": "R2" if not who else "R1",
                    })
                    break
            else:
                continue
            break

    if verbose:
        print("R2 GITGUARD  (defect #115)")
        print("  identity        R2_AGENT=%s" % (who or "<UNSET>"))
        print("  staged paths    %d" % len(staged))
        print("  live leases     %d of %d on disk (TTL %.0f h)"
              % (sum(1 for x in leases if x.get("live")), len(leases), TTL_HOURS))
        if autoseeded:
            print("  auto-leased     %d dirty path(s) that nobody had claimed"
                  % len(autoseeded))
        if violations:
            print("")
            print("  REFUSED -- the index carries paths leased by somebody else.")
            print("  Nothing has been lost; your index is untouched.")
            print("")
            for v in violations:
                print("    %-52s  leased by %s  (via %s, %.1f h old)"
                      % (v["path"], v["owner"], v["lease_entry"], v["age_h"]))
            print("")
            print("  If these really are yours:")
            print("    git restore --staged <path>            # drop it, then commit")
            print("    R2_AGENT=%s tools/gitguard.py release <path>   # as its OWNER"
                  % (violations[0]["owner"]))
            print("  Do NOT use `git add -A`, and do NOT use `git commit --amend`")
            print("  (R2-234: --amend takes whatever HEAD is, which may be theirs).")
        print(">> STAGE RESULT: %s (%d violations)"
              % ("OK" if not violations else "FAIL", len(violations)))
    return (not violations), violations


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------
def cmd_claim(argv, cwd=None):
    """Claim PER PATH, and report the true partition.  (R2-2231.)

    THE DEFECT THIS REPLACES.  `claim` used to be all-or-nothing: one stale
    entry anywhere in the argument list refused the whole list and claimed
    nothing.  Measured verbatim on 2026-08-07, seven paths of which four were
    freely claimable:

        claim (all 7) -> >> STAGE RESULT: FAIL (3 clashes, nothing claimed)
        claim (the 4) -> >> STAGE RESULT: OK (0 clashes)

    Two agents read the first line as a hard refusal and stalled; it took three
    separate commands to discover the real shape.  A guard that answers "no"
    when the truth is "four of seven" IS MISREPORTING ITS OWN STATE, which is
    strictly worse than the stale lease it is reporting -- a stale lease at
    least names the path it holds.

    THE EXIT STATUS, DELIBERATELY.  An agent scripting against this must be
    able to tell "nothing claimed" from "most claimed", and one bit cannot
    carry three outcomes, so there are three codes:

        0  every requested path is now yours          STAGE RESULT: OK
        3  SOME are yours, some clashed               STAGE RESULT: PARTIAL
        1  nothing was claimed; every path clashed    STAGE RESULT: FAIL

    3 is a new code and is chosen so that the old `rc != 0` test still means
    "you did not get everything you asked for" -- an existing caller that
    branches on zero/non-zero keeps its old meaning exactly.  The STAGE RESULT
    word is the primary channel (this project judges on that line), and it is
    PARTIAL, which is neither OK nor FAIL, so a caller grepping for OK gets the
    conservative answer rather than a false pass.

    THE ATOMICITY IS NOT REMOVED, ONLY DEFAULTED AWAY.  Something may depend on
    all-or-nothing, so `--atomic` still does exactly what the old command did,
    and a partial claim says so at the call site rather than silently.
    """
    who = me()
    atomic = "--atomic" in argv
    argv = [a for a in argv if a != "--atomic"]
    if not who:
        print("R2_AGENT must be set to claim.  An anonymous agent cannot own a path.")
        return 2
    if not argv:
        print("claim takes at least one path")
        print(">> STAGE RESULT: FAIL (no paths)")
        return 2
    announce_bypass_env()
    leases = load_leases(cwd)
    mine = next((x for x in leases if x.get("owner") == who and x.get("live")), None)
    if mine is None:
        mine = {"owner": who, "created": now_iso(), "claim_pid": os.getpid(),
                "paths": []}
    clashes, free = [], []
    for path in argv:
        hit = None
        for lease in leases:
            # AUTO_OWNER never clashes. The auto-lease means "dirty and nobody
            # has said whose", so a claim is the answer to it, not a conflict
            # with it -- and it is released a few lines below. Found in live
            # use, one command after the auto-lease was added: claiming three
            # files I had just edited was refused by the guard's own bookkeeping.
            if lease.get("owner") == AUTO_OWNER:
                continue
            if lease.get("live") and lease.get("owner") != who:
                for lp in lease.get("paths", []):
                    if holds(lp, path) or holds(path, lp):
                        hit = (path, lease["owner"], lp, lease.get("age_h") or 0.0,
                               lease.get("kind"))
                        break
            if hit:
                break
        (clashes if hit else free).append(hit or path)

    if clashes and atomic:
        for path, owner, lp, age, kind in clashes:
            print("CLASH  %s is already leased by %s (via %s)" % (path, owner, lp))
        print("  --atomic: %d path(s) were free and were NOT claimed." % len(free))
        print(">> STAGE RESULT: FAIL (%d clashes, nothing claimed)" % len(clashes))
        return 1

    if free:
        mine["paths"] = sorted(set(mine["paths"]) | set(free))
        mine["updated"] = now_iso()
        save_lease(mine, cwd)

    # AN EXPLICIT CLAIM BEATS AN AUTOMATIC LEASE, and the selftest is what
    # forced this.  Adding `auto_seed` broke four green controls at once --
    # including C5b, "the SAME index committed by its OWNER" -- because a path
    # could end up held by both its real owner and by `inflight-auto`, and the
    # guard then refused the author on their own file.  A guard that fights the
    # person who did the claiming is a guard people turn off, and
    # `R2_GITGUARD=off` is worse than no guard because it looks like one.
    #
    # The manual `inflight-*` seed is deliberately NOT released here.  That set
    # is somebody's unfinished work from before the guard existed, and saying so
    # out loud once is the entire point of it.
    #
    # That reasoning still stands and is not what R2-2232 changed.  What was
    # broken was that saying it out loud once had NO WAY TO END: the seed could
    # not expire on its own clock and no coordinator could retire part of it
    # except by setting R2_AGENT to the seed's own name.  A claim against a
    # stale seed therefore still clashes -- and now points at `retire`, which
    # is the legitimate way for that "once" to be over.
    freed = 0
    if free:
        auto = next((x for x in load_leases(cwd)
                     if x.get("owner") == AUTO_OWNER), None)
        if auto:
            # Only the paths actually CLAIMED are taken back from the
            # auto-lease.  Using the whole argument list here would quietly
            # unprotect a path this command just refused to give you.
            keep = [p for p in auto.get("paths", [])
                    if not any(holds(a, p) or holds(p, a) for a in free)]
            freed = len(auto.get("paths", [])) - len(keep)
            if freed:
                auto["paths"] = keep
                auto["updated"] = now_iso()
                save_lease(auto, cwd)

    for path in free:
        print("CLAIMED  %s" % path)
    for path, owner, lp, age, kind in clashes:
        print("CLASH    %s  held by %s (%s, via %s, %.1f h old)"
              % (path, owner, kind, lp, age))
    print("")
    print("  claimed %d of %d requested for %s; lease now holds %d path(s)"
          % (len(free), len(free) + len(clashes), who, len(mine["paths"])))
    if freed:
        print("  (%d path(s) released from %s -- an explicit claim wins)"
              % (freed, AUTO_OWNER))
    if clashes:
        print("")
        print("  The %d clashing path(s) are NOT yours and nothing was taken."
              % len(clashes))
        stale = [c for c in clashes
                 if c[4] == "seed" and c[3] >= DEFAULT_RETIRE_MIN_AGE_H]
        for path, owner, lp, age, kind in clashes:
            if kind == "seed" and age >= DEFAULT_RETIRE_MIN_AGE_H:
                continue
            if kind == "seed":
                print("    %s -- a %.1f h old seed.  It is doing its job: say out"
                      % (path, age))
                print("       loud, once, that this is yours, then ask the owner.")
            else:
                print("    %s -- ask %s to release it.  Do NOT set R2_AGENT=%s."
                      % (path, owner, owner))
        if stale:
            print("    %d path(s) are held by a STALE SEED (>= %.0f h).  A"
                  % (len(stale), DEFAULT_RETIRE_MIN_AGE_H))
            print("    coordinator can retire those without impersonating anyone:")
            print("      R2_AGENT=%s tools/gitguard.py retire --apply %s"
                  % (who, " ".join(c[0] for c in stale[:4])))
    if not clashes:
        print(">> STAGE RESULT: OK (%d claimed, 0 clashes)" % len(free))
        return 0
    if not free:
        print(">> STAGE RESULT: FAIL (0 claimed, %d clashes)" % len(clashes))
        return 1
    print(">> STAGE RESULT: PARTIAL (%d claimed, %d clashes)"
          % (len(free), len(clashes)))
    return 3


def cmd_release(argv, cwd=None):
    who = me()
    if not who:
        print("R2_AGENT must be set to release.")
        return 2
    leases = load_leases(cwd)
    mine = next((x for x in leases if x.get("owner") == who), None)
    if mine is None:
        print("no lease for %s" % who)
        print(">> STAGE RESULT: OK (0 released)")
        return 0
    before = len(mine["paths"])
    mine["paths"] = [p for p in mine["paths"] if p not in argv]
    mine["updated"] = now_iso()
    save_lease(mine, cwd)
    print("released %d path(s) for %s" % (before - len(mine["paths"]), who))
    print(">> STAGE RESULT: OK (0 failures)")
    return 0


def retire_log(cwd=None):
    return os.path.join(git_dir(cwd), "r2-guard", "retire.log")


def cmd_retire(argv, cwd=None):
    """Retire paths from a STALE SEED, and from nothing else.  (R2-2232.)

    THE HOLE THIS FILLS.  A seed lease had no way to expire and no legitimate
    way to be reduced.  The only mechanism that existed was

        R2_AGENT=inflight-2026-08-07 tools/gitguard.py release <path>

    -- setting your identity to another owner's name in order to release their
    lease.  Whatever the intent, the SHAPE of that is impersonating a lease
    owner, a safety classifier refused it, and it was right to: a guard whose
    only escape hatch looks like impersonation is a guard people route around.
    This command is the escape hatch built in the open.

    WHY IT CANNOT TAKE A PATH FROM A LIVE AGENT.  Four independent reasons,
    because one would be an assertion and this project has been burned by
    assertions:

      S1  It only ever edits a lease whose owner is SEED-SHAPED
          (`inflight`, `inflight-*`).  A named agent's lease is refused
          outright, at any age, with no flag that overrides it.  There is no
          `--force`, deliberately.
      S2  A seed younger than --min-age-h (default %(min)g h) is refused, so a
          seed taken minutes ago still does its job of making somebody say out
          loud, once, that a path is theirs.
      S3  It only ever REMOVES entries.  It cannot add a path to any lease, so
          there is no code path by which retiring transfers ownership to the
          caller.  What it produces is an UNOWNED path, which the rightful
          author then claims under their own name.
      S4  It refuses to run when R2_AGENT equals the lease owner -- the exact
          impersonation shape above -- and requires a real identity, which is
          written to .git/r2-guard/retire.log with every path retired.

    It is a dry run unless --apply is given, and it prints every path either
    way.  A destructive command in a tree with a dozen concurrent agents should
    have to be typed twice.

        tools/gitguard.py retire tools/author_beats2_5.py          # preview
        tools/gitguard.py retire --apply tools/author_beats2_5.py
        tools/gitguard.py retire --apply --owner inflight-2026-08-07 --all-paths
    """
    actor = me()
    apply_it = "--apply" in argv
    all_paths = "--all-paths" in argv
    owner_filter = None
    reason = ""
    min_age = DEFAULT_RETIRE_MIN_AGE_H
    rest = []
    i = 0
    flags = {"--apply", "--all-paths", "--dry-run"}
    while i < len(argv):
        a = argv[i]
        if a == "--owner" and i + 1 < len(argv):
            owner_filter = argv[i + 1]
            i += 2
            continue
        if a == "--min-age-h" and i + 1 < len(argv):
            try:
                min_age = float(argv[i + 1])
            except ValueError:
                print("--min-age-h takes a number of hours")
                print(">> STAGE RESULT: FAIL (bad --min-age-h)")
                return 2
            i += 2
            continue
        if a == "--reason" and i + 1 < len(argv):
            reason = argv[i + 1]
            i += 2
            continue
        if a not in flags:
            rest.append(a)
        i += 1

    print("R2 GITGUARD RETIRE  (R2-2232 -- stale seed retirement)")
    if not actor:
        print("")
        print("  REFUSED -- R2_AGENT is unset.")
        print("  Retiring somebody's lease entry is an act with an author, and")
        print("  it is written to retire.log with that author's name.  Set")
        print("  R2_AGENT to YOUR OWN name -- never to the lease owner's.")
        print(">> STAGE RESULT: FAIL (no identity)")
        return 2

    leases = load_leases(cwd)
    # ----------------------------------------------------------------------
    # R2-3603: A RETIRE AIMED AT A PATH THAT DOES NOT EXIST MUST REFUSE.
    #
    # It used to print
    #
    #     nothing selected.  Name a path, or --owner <seed> [--all-paths].
    #     >> STAGE RESULT: OK (0 retired, nothing selected)
    #
    # and exit 0.  A coordinator retired `world/items/itemkit.py` -- the file
    # is at `world/itemkit.py`, one directory up -- read the OK as success,
    # and told the next agent the path was free.  It was not, and the landing
    # of an eight-path commit set was blocked for two more agent-days on a
    # command that had reported it done.  A typo in a path is the single most
    # likely way to call this thing wrongly, and it was the one input that
    # produced a clean exit.
    #
    # `holds()` is used in BOTH directions, exactly as the selection loop
    # below does, so that naming a file a seed holds via a directory entry is
    # still "known" (it is then reported as SKIPPED, which is a different and
    # already-correct message).  A path that no lease mentions AND that git has
    # never heard of AND that is not on disk is a typo, and typos are refused.
    # ----------------------------------------------------------------------
    def _known_to_git(p):
        try:
            git("ls-files", "--error-unmatch", "--", p, cwd=cwd)
            return True
        except RuntimeError:
            return False

    root = repo_root(cwd)
    mentioned = [lp for lease in leases for lp in lease.get("paths", [])]
    unknown = [p for p in rest
               if not any(holds(lp, p) or holds(p, lp) for lp in mentioned)
               and not os.path.exists(os.path.join(root, p))
               and not _known_to_git(p)]
    if unknown:
        print("")
        print("  REFUSED -- %d path(s) that do not exist, and are held by no "
              "lease:" % len(unknown))
        for p in unknown:
            print("    %s" % p)
            near = sorted({lp for lp in mentioned
                           if os.path.basename(lp) == os.path.basename(p)})
            for n in near[:3]:
                print("        did you mean:  %s" % n)
        print("")
        print("  Retiring a path that does not exist frees nothing.  Reporting")
        print("  OK for it is how a landing stays blocked while the record says")
        print("  it was unblocked (R2-3603).  Check the path and run it again.")
        print(">> STAGE RESULT: FAIL (0 retired, %d nonexistent path(s))"
              % len(unknown))
        return 2

    targets = []
    refusals = []
    # A PATH CAN BE HELD BY A SEED *AND* BY A LIVE NAMED AGENT AT ONCE, and the
    # first version of this command retired the seed's copy and reported
    # success -- while the named owner still held it and the guard still
    # refused every commit of it.  A "0 retired" would have been honest; an
    # "OK" that leaves the path exactly as blocked as before is the same
    # misreporting-its-own-state defect this whole change exists to remove.
    # The selftest found it: C17c, `--min-age-h 0` against a path bob owned.
    # So a live named holder blocks the path outright, in every mode.
    blocked = {}
    for lease in leases:
        if lease.get("live") and not is_seed_owner(lease.get("owner")):
            for p in list(rest):
                for lp in lease.get("paths", []):
                    if holds(lp, p) or holds(p, lp):
                        blocked.setdefault(p, lease.get("owner"))

    def refuse(owner, rule, why):
        refusals.append((owner, rule, why))

    if all_paths and not owner_filter:
        print("")
        print("  REFUSED -- --all-paths needs --owner <seed>.")
        print("  Retiring every seed in one command is not a thing this offers.")
        print(">> STAGE RESULT: FAIL (--all-paths without --owner)")
        return 2

    for lease in leases:
        owner = lease.get("owner")
        if owner_filter and owner != owner_filter:
            continue
        if not owner_filter and not rest:
            continue
        # A lease that holds none of the named paths is not a target and not a
        # refusal: it is simply irrelevant, and saying anything about it would
        # bury the one line that matters in noise.
        if rest and not owner_filter and not any(
                any(holds(lp, p) or holds(p, lp) for lp in lease.get("paths", []))
                for p in rest):
            continue
        # S1 -- named agent leases are categorically out of scope.
        if not is_seed_owner(owner):
            # We only get here if this lease was explicitly named or actually
            # holds one of the requested paths, so this is always worth saying.
            live = "LIVE" if lease.get("live") else "expired"
            refuse(owner, "S1",
                   "%s is a NAMED AGENT's lease (%s, %.2f h old), not a seed.\n"
                   "    retire never touches one, at any age, and there is no "
                   "--force.\n"
                   "    If that path really is yours, the owner releases it, or "
                   "you ask\n    the coordinator.  Do NOT set R2_AGENT=%s."
                   % (owner, live, lease.get("age_h") or 0.0, owner))
            continue
        # S4 -- the impersonation shape, refused explicitly.
        if actor == owner:
            refuse(owner, "S4",
                   "R2_AGENT is set to the lease owner's own name.  That is the "
                   "impersonation shape this command exists to replace; run it "
                   "under your own name instead.")
            continue
        # S2 -- age.
        age = lease.get("age_h") or 0.0
        if age < min_age:
            refuse(owner, "S2",
                   "seed is %.2f h old, younger than the %.2f h floor.  A fresh "
                   "seed is doing its job." % (age, min_age))
            continue
        targets.append(lease)

    if not targets and not refusals:
        print("  nothing selected.  Name a path, or --owner <seed> [--all-paths].")
        print("  seeds on disk:")
        for lease in leases:
            if is_seed_owner(lease.get("owner")):
                print("    %-26s age %6.2f h  %d path(s)"
                      % (lease.get("owner"), lease.get("age_h") or 0.0,
                         len(lease.get("paths", []))))
        # R2-3603, second half.  "Nothing selected" is a fine OK when nothing
        # was ASKED FOR -- a bare `retire` is a listing.  It is not an OK when
        # named paths were asked for and not one of them is held by anything
        # retirable: the caller's intent was not satisfied, and the whole
        # reason this block is being rewritten is that a caller believed one
        # of these OK lines.
        if rest:
            print("")
            print("  You named %d path(s) and NO SEED HOLDS ANY OF THEM, so"
                  % len(rest))
            print("  nothing was retired and nothing was unblocked:")
            for p in rest:
                print("    %s" % p)
            print(">> STAGE RESULT: FAIL (0 retired, %d path(s) held by no "
                  "retirable lease)" % len(rest))
            return 2
        print(">> STAGE RESULT: OK (0 retired, nothing selected)")
        return 0

    for owner, rule, why in refusals:
        print("")
        print("  REFUSED [%s] %s" % (rule, owner))
        print("    %s" % why)

    retired_total, changed = [], []
    for lease in targets:
        owner = lease.get("owner")
        held = list(lease.get("paths", []))
        if rest:
            hit = [p for p in held if p in rest]
            miss = [p for p in rest if p not in held]
            # A path given as `world/x.py` when the seed holds `world/` is NOT
            # retirable here: shrinking a directory entry into a path list is a
            # different, larger act than removing an entry, and doing it
            # silently would make the printed plan a lie.
            for p in miss:
                cover = [lp for lp in held if holds(lp, p)]
                if cover:
                    print("")
                    print("  SKIPPED %s" % p)
                    print("    the seed holds it via the broader entry %r, not as "
                          "its own entry." % cover[0])
                    print("    retire removes entries; it does not split them.")
        elif all_paths:
            hit = held
        else:
            hit = []
        held_by_live_agent = [p for p in hit if p in blocked] + [
            p for p in hit
            if p not in blocked and any(
                x.get("live") and not is_seed_owner(x.get("owner"))
                and any(holds(lp, p) or holds(p, lp) for lp in x.get("paths", []))
                for x in leases)]
        for p in sorted(set(held_by_live_agent)):
            owner = blocked.get(p) or next(
                x.get("owner") for x in leases
                if x.get("live") and not is_seed_owner(x.get("owner"))
                and any(holds(lp, p) or holds(p, lp) for lp in x.get("paths", [])))
            print("")
            print("  REFUSED [S1] %s" % p)
            print("    the seed holds it, but so does the LIVE agent %s." % owner)
            print("    Retiring the seed's copy would free nothing and report a")
            print("    success that leaves the path exactly as blocked as it was.")
            refusals.append((owner, "S1", "live agent %s also holds %s"
                             % (owner, p)))
        hit = [p for p in hit if p not in set(held_by_live_agent)]
        if not hit:
            continue
        print("")
        print("  seed %s  (age %.2f h, %d path(s) held, TTL %.0f h)"
              % (owner, lease.get("age_h") or 0.0, len(held), lease.get("ttl_h") or 0))
        print("  retiring %d path(s)%s:"
              % (len(hit), "" if apply_it else "  [DRY RUN -- nothing written]"))
        for p in hit:
            print("    %s" % p)
        retired_total.extend((owner, p) for p in hit)
        changed.append((lease, hit))

    if not retired_total:
        print("")
        print(">> STAGE RESULT: %s (0 retired, %d refusal(s))"
              % ("OK" if not refusals else "FAIL", len(refusals)))
        return 2 if refusals else 0

    if apply_it:
        for lease, hit in changed:
            lease["paths"] = [p for p in lease.get("paths", []) if p not in hit]
            lease["updated"] = now_iso()
            lease.setdefault("retired", []).extend(hit)
            save_lease({k: v for k, v in lease.items()
                        if k not in ("age_h", "live", "kind", "ttl_h")}, cwd)
        try:
            with open(retire_log(cwd), "a") as fh:
                for owner, p in retired_total:
                    fh.write("%s  retired_by=%s  owner=%s  path=%s  reason=%s\n"
                             % (now_iso(), actor, owner, p, reason or "<none>"))
        except Exception as exc:                                  # noqa: BLE001
            print("  WARNING: could not write retire.log: %r" % (exc,))
        print("")
        print("  These paths are now UNOWNED, not yours.  Claim what is yours:")
        print("    R2_AGENT=%s tools/gitguard.py claim %s"
              % (actor, " ".join(p for _, p in retired_total[:4])))
    else:
        print("")
        print("  DRY RUN.  Nothing was written.  Re-run with --apply to do it.")
    print(">> STAGE RESULT: %s (%d retired, %d refusal(s))"
          % ("OK" if apply_it else "DRYRUN", len(retired_total), len(refusals)))
    return 0


try:
    # Interpolated at import so the docstring cannot drift from the constant.
    # Wrapped because under `python -OO` __doc__ is None and this would raise
    # AT IMPORT -- the hook would then die with a traceback and refuse EVERY
    # commit in the repository, which is the one failure this file is most
    # afraid of.  A missing docstring must cost a docstring, not the repo.
    cmd_retire.__doc__ = cmd_retire.__doc__ % {"min": DEFAULT_RETIRE_MIN_AGE_H}
except (TypeError, ValueError, KeyError):                         # noqa: BLE001
    pass


def cmd_seed_inflight(argv, cwd=None):
    """Claim everything that is dirty RIGHT NOW for a stand-in owner.

    The point of the guard is to protect work in flight, and the work in
    flight at the moment it is installed belongs to agents who have never
    heard of it and will never call `claim`.  A file that is modified in the
    worktree and not yet committed is, by definition, unfinished -- so the
    honest default is to treat the whole dirty set as owned by somebody, and
    make anyone who wants to commit one of those paths say so out loud, once.
    """
    owner = "inflight"
    if "--owner" in argv:
        owner = argv[argv.index("--owner") + 1]
    paths = dirty_paths(cwd)
    paths = [p for p in paths if not p.startswith(".git/")]
    if "--merge" in argv:
        prev = next((x for x in load_leases(cwd) if x.get("owner") == owner), None)
        if prev:
            paths = sorted(set(paths) | set(prev.get("paths", [])))
    lease = {"owner": owner, "created": now_iso(), "claim_pid": os.getpid(),
             "paths": sorted(paths),
             "note": "auto-seeded from the dirty worktree at install time "
                     "(defect #115).  Every path here was somebody's unfinished "
                     "work AT THAT MOMENT.  If it is yours, claim it under your "
                     "own name.  Once this seed is past %.0f h a coordinator can "
                     "retire paths from it with `gitguard.py retire --apply "
                     "<path>` -- do NOT set R2_AGENT=%s, which is impersonation "
                     "in shape and is refused (R2-2232)."
                     % (DEFAULT_RETIRE_MIN_AGE_H, owner)}
    save_lease(lease, cwd)
    print("seeded %d dirty path(s) to owner '%s'" % (len(paths), owner))
    for p in paths[:200]:
        print("   %s" % p)
    print(">> STAGE RESULT: OK (%d seeded)" % len(paths))
    return 0


AUTO_OWNER = "inflight-auto"


def auto_seed(staged, cwd=None):
    """Lease every dirty, unleased, UNSTAGED path -- on every commit.

    THE SEED IS A SNAPSHOT, AND THAT WAS A HOLE.  `seed-inflight` claimed the
    312 paths that were dirty when the guard was installed, and nothing at all
    after that.  Within twenty minutes another agent had started editing
    `tools/placement_gate.py`, which had been CLEAN at seed time -- so their
    work was unleased, and a `git add -A` would have taken it exactly as before.
    A guard that protects only the work that existed at install time protects
    the wrong set within the hour.

    So the hook re-seeds continuously.  Every commit anybody makes leases
    whatever else is in flight at that moment, which means the protection
    tracks the tree instead of a timestamp, and it costs nobody anything: no
    adoption, no new command, no change to how anyone commits.

    STAGED PATHS ARE DELIBERATELY EXCLUDED.  Auto-leasing the files of the very
    commit being made would refuse every commit in the repository until its
    author claimed each file first.  That is a defensible rule and it is not
    this one: the point here is to make the guard free, and a guard people must
    negotiate with on every commit is a guard people turn off.  The cost is
    that a sweep in the first moments of a file's life -- before ANY commit has
    run the hook -- is still unguarded.  `seed-inflight --merge` closes that by
    hand when somebody wants it closed.
    """
    if os.environ.get("R2_GUARD_AUTOSEED") == "off":
        return []
    try:
        dirty = [p for p in dirty_paths(cwd) if not p.startswith(".git/")]
        held = set()
        for lease in load_leases(cwd):
            if lease.get("live"):
                held.update(lease.get("paths", []))
        existing = next((x for x in load_leases(cwd)
                         if x.get("owner") == AUTO_OWNER and x.get("live")), None)
        held -= set((existing or {}).get("paths", []))
        fresh = sorted(set(dirty) - set(staged) - held)

        # AND PRUNE.  An auto-lease means exactly one thing -- "this path is
        # uncommitted work in flight" -- so it must end when that stops being
        # true.  Without this the lease is a ratchet: every path ever dirty
        # stays leased forever, refusals accumulate against files that were
        # committed hours ago, and the guard becomes noise. The selftest caught
        # it as an --amend refusal naming the guard's own hook files.
        lease = existing or {"owner": AUTO_OWNER, "created": now_iso(),
                             "claim_pid": os.getpid(), "paths": [],
                             "note": "auto-leased by the pre-commit hook: dirty "
                                     "and unclaimed at the moment somebody else "
                                     "committed. Released automatically once the "
                                     "path is committed and no longer in flight."}
        keep = [p for p in lease["paths"] if p in set(dirty)]
        new = sorted(set(keep) | set(fresh))
        if new == sorted(lease["paths"]):
            return []
        lease["paths"] = new
        lease["updated"] = now_iso()
        save_lease(lease, cwd)
        return fresh
    except Exception:                                             # noqa: BLE001
        return []                                    # never block on this path


def cmd_status(argv, cwd=None):
    announce_bypass_env()
    quiet = "--quiet" in argv or "-q" in argv
    leases = load_leases(cwd)
    if not leases:
        print("no leases")
    for lease in leases:
        retirable = (is_seed_owner(lease.get("owner"))
                     and (lease.get("age_h") or 0.0) >= DEFAULT_RETIRE_MIN_AGE_H)
        print("%-26s %-5s %-8s age %6.2f h / ttl %.0f h  %d path(s)%s%s"
              % (lease.get("owner"), lease.get("kind") or "?",
                 "LIVE" if lease.get("live") else "expired",
                 lease.get("age_h") or 0.0, lease.get("ttl_h") or 0.0,
                 len(lease.get("paths", [])),
                 "  [STALE SEED -- retirable]" if retirable else "",
                 "  BROKEN: " + lease["BROKEN"] if "BROKEN" in lease else ""))
        if not quiet:
            for p in lease.get("paths", [])[:400]:
                print("      %s" % p)
    # A bypass that nobody ever looks at is not much better than a silent one.
    try:
        lines = open(os.path.join(git_dir(cwd), "r2-guard", "bypass.log")).readlines()
        if lines:
            print("")
            print("  %d BYPASSED COMMIT(S) LOGGED (R2_GITGUARD=off).  Last 3:"
                  % len(lines))
            for line in lines[-3:]:
                print("    %s" % line.rstrip()[:150])
    except Exception:                                             # noqa: BLE001
        pass
    print(">> STAGE RESULT: OK (%d leases)" % len(leases))
    return 0


HOOK_PRE_COMMIT = """#!/bin/sh
# R2 gitguard -- defect #115.  Installed by tools/gitguard.py install.
# Fails OPEN on any internal error: a guard that bricks six agents' commits
# is worse than the defect it guards.
if [ "$R2_GITGUARD" = "off" ]; then
    GD="$(git rev-parse --git-dir)"
    mkdir -p "$GD/r2-guard"
    STAGED="$(git diff --cached --name-only | tr '\\n' ' ')"
    echo "$(date -Is) BYPASS by R2_AGENT=${R2_AGENT:-<unset>} staged: $STAGED" \\
        >> "$GD/r2-guard/bypass.log"
    # R2-2233: an escape hatch indistinguishable from success is worse than no
    # guard at all.  This used to print one quiet line and exit 0, and the
    # commit looked exactly like a checked one.
    echo "" >&2
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" >&2
    echo "!!  R2 GITGUARD IS OFF.  THIS COMMIT WAS NOT CHECKED.           !!" >&2
    echo "!!  R2_GITGUARD=off  R2_AGENT=${R2_AGENT:-<unset>}" >&2
    echo "!!  If you did not set that variable, you INHERITED it, and the  !!" >&2
    echo "!!  guard has been off for every commit in this shell.           !!" >&2
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" >&2
    echo "  staged: $STAGED" >&2
    echo "  logged to .git/r2-guard/bypass.log" >&2
    # A repository can refuse the bypass outright by touching this file.  It is
    # opt-in because turning it on retroactively would strand any agent that is
    # relying on the bypass right now; the loud banner above is unconditional.
    if [ -f "$GD/r2-guard/no-bypass" ]; then
        echo ">> STAGE RESULT: FAIL (bypass refused by .git/r2-guard/no-bypass)" >&2
        exit 1
    fi
    echo ">> STAGE RESULT: BYPASSED (guard disabled by R2_GITGUARD=off)" >&2
    exit 0
fi
python3 "$(git rev-parse --show-toplevel)/tools/gitguard.py" check || exit 1
exit 0
"""

HOOK_PREPARE_MSG = """#!/bin/sh
# R2 gitguard -- R2-234.  `git add` takes a path; `--amend` takes whatever
# HEAD happens to be, and in a tree with concurrent agents that is not
# necessarily yours.  An amend on this project has already rewritten another
# agent's commit message.  Write a correcting commit instead.
if [ "$R2_GITGUARD" = "off" ]; then exit 0; fi
if [ "$2" = "commit" ] && [ -n "$3" ]; then
    if [ "$R2_AMEND_OK" = "1" ]; then
        echo "R2 GITGUARD: --amend allowed by R2_AMEND_OK=1 on $3" >&2
        exit 0
    fi
    echo "" >&2
    echo "R2 GITGUARD REFUSED: git commit --amend  (R2-234)" >&2
    echo "  target commit: $3" >&2
    echo "  HEAD is shared.  Between your commit and your amend another" >&2
    echo "  agent's commit can land and become HEAD -- that has already" >&2
    echo "  happened once here, rewriting their message with yours." >&2
    echo "  Write a correcting commit instead, or git notes add." >&2
    echo ">> STAGE RESULT: FAIL (1 violations)" >&2
    exit 1
fi
exit 0
"""


def cmd_install(argv, cwd=None):
    root = repo_root(cwd)
    hooks = os.path.join(root, "tools", "githooks")
    os.makedirs(hooks, exist_ok=True)
    for name, body in (("pre-commit", HOOK_PRE_COMMIT),
                       ("prepare-commit-msg", HOOK_PREPARE_MSG)):
        p = os.path.join(hooks, name)
        with open(p, "w") as fh:
            fh.write(body)
        os.chmod(p, 0o755)
    git("config", "core.hooksPath", "tools/githooks", cwd=cwd)
    print("installed pre-commit and prepare-commit-msg into %s" % hooks)
    print("core.hooksPath = %s" % git("config", "--get", "core.hooksPath", cwd=cwd).strip())
    print(">> STAGE RESULT: OK (0 failures)")
    return 0


def main(argv):
    if not argv:
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "check":
        try:
            ok, _ = check()
        except Exception as exc:                                  # noqa: BLE001
            print("R2 GITGUARD INTERNAL ERROR -- ALLOWING THE COMMIT: %r" % (exc,))
            print(">> STAGE RESULT: OK (guard failed open)")
            return 0
        return 0 if ok else 1
    if cmd == "claim":
        return cmd_claim(rest)
    if cmd == "release":
        return cmd_release(rest)
    if cmd == "seed-inflight":
        return cmd_seed_inflight(rest)
    if cmd in ("retire", "expire-stale"):
        return cmd_retire(rest)
    if cmd == "status":
        return cmd_status(rest)
    if cmd == "install":
        return cmd_install(rest)
    if cmd == "selftest":
        from gitguard_selftest import run                          # noqa: PLC0415
        return run()
    print("unknown command %r" % cmd)
    return 2


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv[1:]))
