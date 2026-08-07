#!/usr/bin/env python3
"""CONTROLS FOR tools/gitguard.py, INCLUDING THE ONES THAT MUST FAIL.

Defect #115.  The guard is worthless unless it can be shown refusing a real
sweep, and *equally* worthless unless it can be shown ALLOWING that same sweep
once the lease is removed -- otherwise a refusal proves nothing about the
lease and everything about some accident of the test.

The commonest defect across this project's 830 log entries is not a bad
render, it is a broken instrument: a bay list hardcoded so a bay was never
measured, a metric reading 791 frames as exactly 0.00, a "control" that passed
only because it discarded 70 % of its work.  So every check below is run in
BOTH states, and the vacuity controls (C4, C6) are the load-bearing ones.

Runs entirely inside a throwaway repository under the scratch directory.  It
never touches the live repository, never runs a git write in it, and never
reads its index.
"""
import os
import sys
import json
import shutil
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(HERE, "gitguard.py")


def sh(cmd, cwd, env=None, expect=None):
    e = dict(os.environ)
    e.pop("R2_AGENT", None)
    e.pop("R2_GITGUARD", None)
    e.pop("R2_AMEND_OK", None)
    e.pop("R2_GUARD_TTL_H", None)
    e.update(env or {})
    p = subprocess.run(cmd, cwd=cwd, env=e, shell=isinstance(cmd, str),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode(errors="replace")
    return p.returncode, out


def make_repo(tmp):
    r = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(r, "world", "items"))
    os.makedirs(os.path.join(r, "tools"))
    os.makedirs(os.path.join(r, "docs"))
    shutil.copy(GUARD, os.path.join(r, "tools", "gitguard.py"))
    sh("git init -q .", r)
    sh("git config user.email a@b.c", r)
    sh("git config user.name tester", r)
    sh("git config commit.gpgsign false", r)
    for p in ("world/items/alice.py", "world/items/bob.py",
              "tools/audio_thing.py", "docs/NOTE.md"):
        open(os.path.join(r, p), "w").write("# base\n")
    sh("git add world tools docs", r)
    sh("git -c core.hooksPath=/dev/null commit -q -m base", r)
    sh("python3 tools/gitguard.py install", r)
    # Commit the hooks in the BASE commit. Left dirty they are in-flight work
    # like any other, the auto-lease correctly claims them, and every later
    # control then inherits a refusal that has nothing to do with what it is
    # testing. Removing a harness artefact, not weakening a check.
    sh("git add tools/githooks", r)
    sh("git -c core.hooksPath=/dev/null commit -q -m hooks", r)
    return r


RESULTS = []


def record(name, want, got, detail=""):
    ok = (want == got)
    RESULTS.append((name, want, got, ok, detail))
    print("  %-4s %-58s want=%-7s got=%-7s %s"
          % ("PASS" if ok else "FAIL", name, want, got, detail))
    return ok


def guard_verdict(rc, out):
    """ALLOWED / REFUSED, read off the commit's exit code."""
    return "REFUSED" if rc != 0 else "ALLOWED"


def run():
    tmp = tempfile.mkdtemp(prefix="gitguard-selftest-")
    try:
        r = make_repo(tmp)
        print("R2 GITGUARD SELFTEST   (defect #115)")
        print("throwaway repo: %s" % r)
        print("")

        # ---------------------------------------------------------------
        # Bob is another agent, mid-edit on bob.py and audio_thing.py.
        # ---------------------------------------------------------------
        open(os.path.join(r, "world/items/bob.py"), "a").write("# bob in flight\n")
        open(os.path.join(r, "tools/audio_thing.py"), "a").write("# bob in flight\n")
        sh("python3 tools/gitguard.py claim world/items/bob.py tools/audio_*.py",
           r, {"R2_AGENT": "bob"})

        # Alice edits her own file.
        open(os.path.join(r, "world/items/alice.py"), "a").write("# alice\n")
        sh("python3 tools/gitguard.py claim world/items/alice.py",
           r, {"R2_AGENT": "alice"})

        print("C1  the correct thing must still work")
        sh("git add world/items/alice.py", r)
        rc, out = sh('git commit -q -m "alice, path-scoped"', r, {"R2_AGENT": "alice"})
        record("C1 path-scoped add by the owner", "ALLOWED", guard_verdict(rc, out),
               out.strip().splitlines()[-1][:60] if out.strip() else "")

        # ---------------------------------------------------------------
        print("")
        print("C2  THE ACTUAL DEFECT: a blanket add sweeping bob's in-flight work")
        open(os.path.join(r, "world/items/alice.py"), "a").write("# alice again\n")
        sh("git add -A", r)
        staged = sh("git diff --cached --name-only", r)[1].split()
        rc, out = sh('git commit -q -m "alice sweeps the tree"', r, {"R2_AGENT": "alice"})
        swept_bob = [p for p in staged if "bob" in p or "audio_thing" in p]
        record("C2 git add -A over another agent's lease", "REFUSED",
               guard_verdict(rc, out), "swept %s" % swept_bob)
        named = ("world/items/bob.py" in out and "tools/audio_thing.py" in out
                 and "bob" in out)
        record("C2b the refusal NAMES the files and the owner", True, named)
        # Nothing may be lost: the index must survive the refusal untouched.
        still = sh("git diff --cached --name-only", r)[1].split()
        record("C2c the index is untouched by the refusal", sorted(staged),
               sorted(still))

        # ---------------------------------------------------------------
        print("")
        print("C3  --amend, which is `add`'s blind spot (R2-234)")
        sh("git restore --staged world/items/bob.py tools/audio_thing.py", r)
        rc, out = sh('git commit -q --amend -m "alice amends"', r, {"R2_AGENT": "alice"})
        record("C3 git commit --amend", "REFUSED", guard_verdict(rc, out))
        record("C3b the refusal cites R2-234", True, "R2-234" in out)
        rc, out = sh('git commit -q --amend -m "alice amends, declared"', r,
                     {"R2_AGENT": "alice", "R2_AMEND_OK": "1"})
        record("C3c --amend with R2_AMEND_OK=1 (escape hatch works)",
               "ALLOWED", guard_verdict(rc, out))

        # ---------------------------------------------------------------
        print("")
        print("C4  VACUITY CONTROL -- the same sweep, with bob's lease deleted.")
        print("    If this is still REFUSED, C2 proved nothing about the lease.")
        lease = os.path.join(r, ".git", "r2-guard", "leases", "bob.json")
        stash = lease + ".stashed"
        os.rename(lease, stash)
        auto = os.path.join(r, ".git", "r2-guard", "leases", "inflight-auto.json")
        if os.path.exists(auto):
            os.remove(auto)
        sh("git add -A", r)
        rc, out = sh('git commit -q -m "same sweep, no lease"', r,
                     {"R2_AGENT": "alice", "R2_GUARD_AUTOSEED": "off"})
        record("C4 identical sweep with no lease present", "ALLOWED",
               guard_verdict(rc, out))
        os.rename(stash, lease)

        # ---------------------------------------------------------------
        print("")
        print("C5  an anonymous committer cannot own anything (rule R2)")
        open(os.path.join(r, "world/items/bob.py"), "a").write("# bob more\n")
        sh("git add world/items/bob.py", r)
        rc, out = sh('git commit -q -m "who am i"', r)          # R2_AGENT unset
        record("C5 R2_AGENT unset, staging a leased path", "REFUSED",
               guard_verdict(rc, out))
        rc, out = sh('git commit -q -m "bob commits his own"', r, {"R2_AGENT": "bob"})
        record("C5b the SAME index committed by its owner", "ALLOWED",
               guard_verdict(rc, out))

        # ---------------------------------------------------------------
        print("")
        print("C6  VACUITY CONTROL -- an expired lease must not brick the repo.")
        print("    Two agents were killed mid-task here by a usage limit.")
        open(os.path.join(r, "world/items/bob.py"), "a").write("# later\n")
        sh("git add world/items/bob.py", r)
        rc, out = sh('git commit -q -m "alice, bob long gone"', r,
                     {"R2_AGENT": "alice", "R2_GUARD_TTL_H": "0"})
        record("C6 lease older than TTL is ignored", "ALLOWED",
               guard_verdict(rc, out))
        # and the same index, with the lease live, must be refused
        sh("git reset -q --soft HEAD~1", r)
        rc, out = sh('git commit -q -m "alice, bob still here"', r,
                     {"R2_AGENT": "alice", "R2_GUARD_TTL_H": "24"})
        record("C6b the SAME index with the lease live", "REFUSED",
               guard_verdict(rc, out))

        # ---------------------------------------------------------------
        print("")
        print("C7  directory and glob lease forms")
        sh("git restore --staged world/items/bob.py", r)
        sh("python3 tools/gitguard.py claim docs/", r, {"R2_AGENT": "carol"})
        open(os.path.join(r, "docs/NOTE.md"), "a").write("# carol\n")
        sh("git add docs/NOTE.md", r)
        rc, out = sh('git commit -q -m "alice touches carols dir"', r,
                     {"R2_AGENT": "alice"})
        record("C7 directory lease 'docs/' covers docs/NOTE.md", "REFUSED",
               guard_verdict(rc, out))
        sh("git restore --staged docs/NOTE.md", r)
        open(os.path.join(r, "tools/audio_thing.py"), "a").write("# x\n")
        sh("git add tools/audio_thing.py", r)
        rc, out = sh('git commit -q -m "alice touches bobs glob"', r,
                     {"R2_AGENT": "alice"})
        record("C7b glob lease 'tools/audio_*.py' covers tools/audio_thing.py",
               "REFUSED", guard_verdict(rc, out))
        sh("git restore --staged tools/audio_thing.py", r)

        # ---------------------------------------------------------------
        print("")
        print("C8  the guard must FAIL OPEN on its own internal error")
        ld = os.path.join(r, ".git", "r2-guard", "leases")
        bak = ld + ".bak"
        os.rename(ld, bak)
        open(ld, "w").write("this is a file where a directory must be")
        open(os.path.join(r, "world/items/alice.py"), "a").write("# c8\n")
        sh("git add world/items/alice.py", r)
        rc, out = sh('git commit -q -m "guard broken, commit must survive"', r,
                     {"R2_AGENT": "alice"})
        record("C8 broken lease store allows the commit", "ALLOWED",
               guard_verdict(rc, out))
        record("C8b and says so loudly", True, "INTERNAL ERROR" in out)
        os.remove(ld)
        os.rename(bak, ld)

        # ---------------------------------------------------------------
        print("")
        print("C9  the bypass works and is logged")
        open(os.path.join(r, "world/items/bob.py"), "a").write("# c9\n")
        sh("git add world/items/bob.py", r)
        rc, out = sh('git commit -q -m "alice bypasses"', r,
                     {"R2_AGENT": "alice", "R2_GITGUARD": "off"})
        record("C9 R2_GITGUARD=off bypasses", "ALLOWED", guard_verdict(rc, out))
        logp = os.path.join(r, ".git", "r2-guard", "bypass.log")
        record("C9b the bypass is written to bypass.log", True,
               os.path.exists(logp) and "alice" in open(logp).read())

        # ---------------------------------------------------------------
        print("")
        print("C12 the hook must fire from a SUBDIRECTORY too")
        print("    core.hooksPath is relative; a guard that quietly stops")
        print("    running when you happen to be cd'd into world/items is")
        print("    indistinguishable from no guard at all.")
        open(os.path.join(r, "world/items/bob.py"), "a").write("# c12\n")
        sh("git add world/items/bob.py", os.path.join(r, "world", "items"))
        rc, out = sh('git commit -q -m "alice, from a subdir"',
                     os.path.join(r, "world", "items"), {"R2_AGENT": "alice"})
        record("C12 commit issued from world/items/", "REFUSED",
               guard_verdict(rc, out))
        sh("git restore --staged world/items/bob.py", r)

        print("")
        print("C11 `git commit -a` is the same hazard wearing a different flag")
        open(os.path.join(r, "world/items/bob.py"), "a").write("# c11 bob\n")
        open(os.path.join(r, "world/items/alice.py"), "a").write("# c11 alice\n")
        rc, out = sh('git commit -q -a -m "alice commits -a"', r, {"R2_AGENT": "alice"})
        record("C11 git commit -a over another agent's lease", "REFUSED",
               guard_verdict(rc, out), "names bob.py: %s"
               % ("world/items/bob.py" in out))
        sh("git reset -q", r)

        print("")
        print("C13 THE SNAPSHOT HOLE: work that STARTS after the seed")
        print("    Twenty minutes after install, an agent began editing a file")
        print("    that had been clean at seed time. It was unleased, and a")
        print("    blanket add would have taken it exactly as before.")
        sh("git reset -q", r)
        dave = os.path.join(r, "world/items/dave.py")
        open(dave, "w").write("# dave, started AFTER the seed\n")
        # Alice makes an ordinary, unrelated commit. The hook auto-leases
        # whatever else is in flight while it is there.
        open(os.path.join(r, "world/items/alice.py"), "a").write("# c13\n")
        sh("git add world/items/alice.py", r)
        rc, out = sh('git commit -q -m "alice, unrelated"', r, {"R2_AGENT": "alice"})
        record("C13 an unrelated commit still succeeds", "ALLOWED",
               guard_verdict(rc, out))
        record("C13b and it auto-leased dave's new file", True,
               "auto-leased" in out, out.strip().splitlines()[3][:52]
               if len(out.strip().splitlines()) > 3 else "")
        # ONE variable. Stage dave.py and NOTHING else, so the verdict is
        # about dave's auto-lease and not about bob's or carol's manual ones.
        # The first version of this control staged the whole tree and came back
        # REFUSED for three unrelated reasons -- a control that fires for the
        # wrong reason is worth nothing, and it would have read as a pass.
        sh("git add world/items/dave.py", r)
        rc, out = sh('git commit -q -m "alice takes daves new file"', r,
                     {"R2_AGENT": "alice"})
        record("C13c staging dave's auto-leased file is REFUSED", "REFUSED",
               guard_verdict(rc, out), "names dave: %s"
               % ("world/items/dave.py" in out))
        # VACUITY: the IDENTICAL index, with the auto-lease removed, must pass.
        lp = os.path.join(r, ".git", "r2-guard", "leases", "inflight-auto.json")
        if os.path.exists(lp):
            os.remove(lp)
        rc, out = sh('git commit -q -m "same index, no auto-lease"', r,
                     {"R2_AGENT": "alice", "R2_GUARD_AUTOSEED": "off"})
        record("C13d VACUITY: same index with the auto-lease gone", "ALLOWED",
               guard_verdict(rc, out))

        print("")
        print("C10 seed-inflight claims exactly the dirty set")
        open(os.path.join(r, "docs/NEW_UNTRACKED.md"), "w").write("x\n")
        rc, out = sh("python3 tools/gitguard.py seed-inflight --owner inflight", r)
        seeded = json.load(open(os.path.join(
            r, ".git", "r2-guard", "leases", "inflight.json")))["paths"]
        dirty = [l[3:] for l in sh("git status --porcelain=v1 -uall", r)[1].splitlines()]
        record("C10 seeded set == dirty set", sorted(dirty), sorted(seeded))
        record("C10b untracked files are included", True,
               "docs/NEW_UNTRACKED.md" in seeded)

        print("")
        failed = [x for x in RESULTS if not x[3]]
        for name, want, got, ok, detail in failed:
            print("  FAILED: %s  want=%r got=%r" % (name, want, got))
        print(">> STAGE RESULT: %s (%d failures of %d checks)"
              % ("OK" if not failed else "FAIL", len(failed), len(RESULTS)))
        return 0 if not failed else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(run())
