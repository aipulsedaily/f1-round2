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

try:
    # A malformed TTL must not turn the guard into a crash: a hook that dies
    # with a traceback exits non-zero and BLOCKS every commit in the repo,
    # which is the failure mode this file is most afraid of.
    TTL_HOURS = float(os.environ.get("R2_GUARD_TTL_H", "24"))
except ValueError:
    TTL_HOURS = 24.0


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
                        "live": False, "age_h": None})
            continue
        try:
            created = datetime.datetime.fromisoformat(lease.get("created", ""))
            age_h = (datetime.datetime.now() - created).total_seconds() / 3600.0
        except Exception:                                         # noqa: BLE001
            age_h = 0.0
        lease["age_h"] = age_h
        lease["live"] = age_h <= TTL_HOURS
        out.append(lease)
    return out


def save_lease(lease, cwd=None):
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
def check(cwd=None, verbose=True):
    """Returns (ok, [violation dicts]).  Never raises -- see FAILING OPEN."""
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
    who = me()
    if not who:
        print("R2_AGENT must be set to claim.  An anonymous agent cannot own a path.")
        return 2
    leases = load_leases(cwd)
    mine = next((x for x in leases if x.get("owner") == who and x.get("live")), None)
    if mine is None:
        mine = {"owner": who, "created": now_iso(), "pid": os.getpid(), "paths": []}
    clashes = []
    for path in argv:
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
                        clashes.append((path, lease["owner"], lp))
    if clashes:
        for path, owner, lp in clashes:
            print("CLASH  %s is already leased by %s (via %s)" % (path, owner, lp))
        print(">> STAGE RESULT: FAIL (%d clashes, nothing claimed)" % len(clashes))
        return 1
    mine["paths"] = sorted(set(mine["paths"]) | set(argv))
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
    auto = next((x for x in load_leases(cwd) if x.get("owner") == AUTO_OWNER), None)
    if auto:
        keep = [p for p in auto.get("paths", [])
                if not any(holds(a, p) or holds(p, a) for a in argv)]
        freed = len(auto.get("paths", [])) - len(keep)
        if freed:
            auto["paths"] = keep
            auto["updated"] = now_iso()
            save_lease(auto, cwd)
            print("  (%d path(s) released from %s -- an explicit claim wins)"
                  % (freed, AUTO_OWNER))
    print("claimed %d path(s) for %s; lease now holds %d"
          % (len(argv), who, len(mine["paths"])))
    print(">> STAGE RESULT: OK (0 clashes)")
    return 0


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
    lease = {"owner": owner, "created": now_iso(), "pid": os.getpid(),
             "paths": sorted(paths),
             "note": "auto-seeded from the dirty worktree at install time "
                     "(defect #115).  Every path here was somebody's unfinished "
                     "work.  Release with R2_AGENT=%s tools/gitguard.py release "
                     "<path> once you have confirmed it is yours." % owner}
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
                             "pid": os.getpid(), "paths": [],
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
    leases = load_leases(cwd)
    if not leases:
        print("no leases")
    for lease in leases:
        print("%-26s %-8s age %6.2f h  %d path(s)%s"
              % (lease.get("owner"), "LIVE" if lease.get("live") else "expired",
                 lease.get("age_h") or 0.0, len(lease.get("paths", [])),
                 "  BROKEN: " + lease["BROKEN"] if "BROKEN" in lease else ""))
        for p in lease.get("paths", [])[:400]:
            print("      %s" % p)
    print(">> STAGE RESULT: OK (%d leases)" % len(leases))
    return 0


HOOK_PRE_COMMIT = """#!/bin/sh
# R2 gitguard -- defect #115.  Installed by tools/gitguard.py install.
# Fails OPEN on any internal error: a guard that bricks six agents' commits
# is worse than the defect it guards.
if [ "$R2_GITGUARD" = "off" ]; then
    mkdir -p "$(git rev-parse --git-dir)/r2-guard"
    echo "$(date -Is) BYPASS by R2_AGENT=${R2_AGENT:-<unset>}" \\
        >> "$(git rev-parse --git-dir)/r2-guard/bypass.log"
    echo "R2 GITGUARD BYPASSED (R2_GITGUARD=off) -- logged." >&2
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
