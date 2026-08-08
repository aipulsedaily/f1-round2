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
import datetime
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
    e.pop("R2_GUARD_SEED_TTL_H", None)
    e.pop("R2_GUARD_RETIRE_MIN_AGE_H", None)
    e.pop("R2_GUARD_AUTOSEED", None)
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
        print("C14 an explicit claim must be able to TAKE an auto-leased path")
        print("    Found in live use, not here: the auto-lease refused a claim")
        print("    on files their author had just edited, which is the normal")
        print("    case and would have made claiming impossible.")
        open(os.path.join(r, "world/items/erin.py"), "w").write("# erin\n")
        open(os.path.join(r, "world/items/alice.py"), "a").write("# c14\n")
        sh("git add world/items/alice.py", r)
        sh('git commit -q -m "alice, unrelated c14"', r, {"R2_AGENT": "alice"})
        held = json.load(open(os.path.join(
            r, ".git", "r2-guard", "leases", "inflight-auto.json")))["paths"]
        record("C14 erin's new file was auto-leased", True,
               "world/items/erin.py" in held)
        rc, out = sh("python3 tools/gitguard.py claim world/items/erin.py", r,
                     {"R2_AGENT": "erin"})
        record("C14b erin can claim it", "OK", "OK" if rc == 0 else "CLASH",
               out.strip().splitlines()[-1][:44])
        sh("git add world/items/erin.py", r)
        rc, out = sh('git commit -q -m "erin commits her own"', r,
                     {"R2_AGENT": "erin"})
        record("C14c and then commit it", "ALLOWED", guard_verdict(rc, out))
        rc, out = sh('git commit -q -m "alice takes erins file"', r,
                     {"R2_AGENT": "alice"})
        record("C14d VACUITY: alice still cannot", "REFUSED",
               guard_verdict(rc, out))
        sh("git reset -q", r)

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

        # ---------------------------------------------------------------
        print("")
        print("C15 A MIXED CLAIM MUST REPORT THE TRUE PARTITION  (R2-2231)")
        print("    Measured verbatim in the live repo: seven paths, four of")
        print("    them free, answered `FAIL (3 clashes, nothing claimed)`.")
        print("    A guard that says no when the truth is four-of-seven is")
        print("    misreporting its own state.")
        sh("git reset -q", r)
        for n in ("f1", "f2", "f3", "f4"):
            open(os.path.join(r, "world/items/%s.py" % n), "w").write("# %s\n" % n)
        want_free = ["world/items/f1.py", "world/items/f2.py",
                     "world/items/f3.py", "world/items/f4.py"]
        want_clash = ["world/items/bob.py", "tools/audio_thing.py", "docs/NOTE.md"]
        rc, out = sh("python3 tools/gitguard.py claim " + " ".join(want_free + want_clash),
                     r, {"R2_AGENT": "frank"})
        record("C15 mixed claim: all 4 free paths reported CLAIMED", True,
               all(("CLAIMED  " + p) in out for p in want_free),
               out.strip().splitlines()[-1][:52])
        record("C15b and all 3 clashes named with their owner", True,
               all(p in out for p in want_clash)
               and "bob" in out and "carol" in out)
        # THE LOAD-BEARING ONE: it must not have claimed zero.
        fl = os.path.join(r, ".git", "r2-guard", "leases", "frank.json")
        held = json.load(open(fl))["paths"] if os.path.exists(fl) else []
        record("C15c the 4 free paths really ARE in frank's lease", sorted(want_free),
               sorted(p for p in held if p in want_free))
        record("C15d and NONE of the clashing 3 were taken", [],
               sorted(p for p in held if p in want_clash))
        record("C15e exit code says PARTIAL, distinctly from FAIL", 3, rc,
               "STAGE RESULT: %s" % ("PARTIAL" if "PARTIAL" in out else "?"))
        # VACUITY, BOTH ENDS: the same command shape must still be able to
        # return a plain OK and a plain FAIL, or "PARTIAL" proves nothing.
        open(os.path.join(r, "world/items/f5.py"), "w").write("# f5\n")
        rc, out = sh("python3 tools/gitguard.py claim world/items/f5.py", r,
                     {"R2_AGENT": "frank"})
        record("C15f VACUITY: an all-free claim is still rc 0 / OK", (0, True),
               (rc, "STAGE RESULT: OK" in out))
        rc, out = sh("python3 tools/gitguard.py claim world/items/bob.py docs/NOTE.md",
                     r, {"R2_AGENT": "frank"})
        record("C15g VACUITY: an all-clashing claim is still rc 1 / FAIL", (1, True),
               (rc, "STAGE RESULT: FAIL" in out))
        # And the old atomic behaviour must still be reachable on demand.
        rc, out = sh("python3 tools/gitguard.py claim --atomic world/items/f6.py "
                     "world/items/bob.py", r, {"R2_AGENT": "frank"})
        held = json.load(open(fl))["paths"]
        record("C15h --atomic keeps the old all-or-nothing path", (1, False),
               (rc, "world/items/f6.py" in held))

        # ---------------------------------------------------------------
        print("")
        print("C16 RETIRING A STALE SEED -- AND REFUSING A LIVE AGENT  (R2-2232)")
        print("    Both directions. A retire command that has only ever been")
        print("    seen to succeed is not a control, it is a hazard.")
        ld = os.path.join(r, ".git", "r2-guard", "leases")
        seed_name = "inflight-2026-08-07"
        old = (datetime.datetime.now()
               - datetime.timedelta(hours=9)).replace(
                   microsecond=0).isoformat()
        open(os.path.join(r, "world/items/orphan.py"), "w").write("# orphan\n")
        open(os.path.join(r, "world/items/keep.py"), "w").write("# keep\n")
        json.dump({"owner": seed_name, "created": old,
                   "paths": ["world/items/orphan.py", "world/items/keep.py"]},
                  open(os.path.join(ld, seed_name + ".json"), "w"))
        # -- direction 1: it retires a stale seed path.
        rc, out = sh("python3 tools/gitguard.py retire world/items/orphan.py", r,
                     {"R2_AGENT": "grace"})
        still = json.load(open(os.path.join(ld, seed_name + ".json")))["paths"]
        record("C16 dry run names the path and writes NOTHING",
               (True, True, True),
               ("world/items/orphan.py" in out, "DRY RUN" in out,
                "world/items/orphan.py" in still))
        rc, out = sh("python3 tools/gitguard.py retire --apply world/items/orphan.py",
                     r, {"R2_AGENT": "grace"})
        still = json.load(open(os.path.join(ld, seed_name + ".json")))["paths"]
        record("C16b --apply retires exactly that path", ["world/items/keep.py"],
               still, "rc=%d" % rc)
        # It must produce an UNOWNED path, not one owned by the retirer.
        gl = os.path.join(ld, "grace.json")
        record("C16c retire gives the path to NOBODY, least of all the retirer",
               False,
               os.path.exists(gl)
               and "world/items/orphan.py" in json.load(open(gl))["paths"])
        record("C16d and the retirement is logged with the actor's own name", True,
               os.path.exists(os.path.join(r, ".git", "r2-guard", "retire.log"))
               and "retired_by=grace" in open(os.path.join(
                   r, ".git", "r2-guard", "retire.log")).read())
        # end to end: the real author can now claim and commit it
        rc, out = sh("python3 tools/gitguard.py claim world/items/orphan.py", r,
                     {"R2_AGENT": "heidi"})
        sh("git add world/items/orphan.py", r)
        rc, out = sh('git commit -q -m "heidi lands the orphan"', r,
                     {"R2_AGENT": "heidi"})
        record("C16e the unblocked path reaches a commit", "ALLOWED",
               guard_verdict(rc, out))

        # -- direction 2: IT MUST REFUSE. Four separate ways in, all closed.
        bobl = os.path.join(ld, "bob.json")
        bob_before = json.load(open(bobl))["paths"]
        rc, out = sh("python3 tools/gitguard.py retire --apply world/items/bob.py",
                     r, {"R2_AGENT": "grace"})
        record("C16f S1: refuses a LIVE NAMED agent's path", (2, True),
               (rc, "REFUSED [S1]" in out and "bob" in out))
        record("C16g and bob's lease is byte-identical afterwards", bob_before,
               json.load(open(bobl))["paths"])
        rc, out = sh("python3 tools/gitguard.py retire --apply --owner bob --all-paths",
                     r, {"R2_AGENT": "grace"})
        record("C16h S1: refuses --owner bob --all-paths too", (2, True),
               (rc, "REFUSED [S1]" in out))
        record("C16i and bob's lease is STILL byte-identical", bob_before,
               json.load(open(bobl))["paths"])
        # ...and the teeth are still in: bob's path still refuses alice.
        open(os.path.join(r, "world/items/bob.py"), "a").write("# c16\n")
        sh("git add world/items/bob.py", r)
        rc, out = sh('git commit -q -m "alice after a refused retire"', r,
                     {"R2_AGENT": "alice"})
        record("C16j VACUITY: bob's path still refuses alice after the refusal",
               "REFUSED", guard_verdict(rc, out))
        sh("git restore --staged world/items/bob.py", r)
        # S2: a FRESH seed is not retirable at all.
        json.dump({"owner": "inflight-fresh",
                   "created": datetime.datetime.now().replace(
                       microsecond=0).isoformat(),
                   "paths": ["world/items/keep.py"]},
                  open(os.path.join(ld, "inflight-fresh.json"), "w"))
        rc, out = sh("python3 tools/gitguard.py retire --apply --owner inflight-fresh "
                     "--all-paths", r, {"R2_AGENT": "grace"})
        record("C16k S2: refuses a seed younger than the age floor", (2, True),
               (rc, "REFUSED [S2]" in out))
        # S4: the impersonation shape is refused BY NAME.
        rc, out = sh("python3 tools/gitguard.py retire --apply --owner %s --all-paths"
                     % seed_name, r, {"R2_AGENT": seed_name})
        record("C16l S4: refuses R2_AGENT set to the lease owner's own name",
               (2, True), (rc, "REFUSED [S4]" in out))
        rc, out = sh("python3 tools/gitguard.py retire --apply world/items/keep.py", r)
        record("C16m refuses with no identity at all", (2, True),
               (rc, "no identity" in out))
        # and after all four refusals the seed still holds what it held
        record("C16n after every refusal the seed is unchanged",
               ["world/items/keep.py"],
               json.load(open(os.path.join(ld, seed_name + ".json")))["paths"])

        # ---------------------------------------------------------------
        print("")
        print("C17 A SEED AND A WORKING LEASE MUST NOT SHARE ONE LIFETIME")
        print("    Lowering the global TTL to expire the 8 h seed would have")
        print("    expired three agents that were committing at that moment.")
        sh("git reset -q", r)
        open(os.path.join(r, "world/items/keep.py"), "a").write("# c17\n")
        sh("git add world/items/keep.py", r)
        rc, out = sh('git commit -q -m "alice takes a seed path, seed ttl 0"', r,
                     {"R2_AGENT": "alice", "R2_GUARD_SEED_TTL_H": "0"})
        record("C17 R2_GUARD_SEED_TTL_H=0 expires the SEED", "ALLOWED",
               guard_verdict(rc, out))
        # THE LOAD-BEARING HALF: the same knob must not touch a live agent.
        open(os.path.join(r, "world/items/bob.py"), "a").write("# c17b\n")
        sh("git add world/items/bob.py", r)
        rc, out = sh('git commit -q -m "alice takes bobs path, seed ttl 0"', r,
                     {"R2_AGENT": "alice", "R2_GUARD_SEED_TTL_H": "0"})
        record("C17b the SAME knob does NOT expire a live agent's lease",
               "REFUSED", guard_verdict(rc, out),
               "names bob: %s" % ("world/items/bob.py" in out))
        sh("git restore --staged world/items/bob.py", r)
        rc, out = sh("python3 tools/gitguard.py retire --apply --min-age-h 0 "
                     "world/items/bob.py", r, {"R2_AGENT": "grace"})
        record("C17c --min-age-h 0 is not a way into a named lease either",
               (2, True), (rc, "REFUSED [S1]" in out))

        # ---------------------------------------------------------------
        print("")
        print("C18 THE BYPASS MUST BE IMPOSSIBLE TO MISTAKE FOR A PASS")
        print("    An escape hatch indistinguishable from success is worse")
        print("    than no guard at all.")
        sh("git reset -q", r)
        open(os.path.join(r, "world/items/bob.py"), "a").write("# c18\n")
        sh("git add world/items/bob.py", r)
        rc, out = sh('git commit -q -m "alice bypasses loudly"', r,
                     {"R2_AGENT": "alice", "R2_GITGUARD": "off"})
        record("C18 the bypassed commit announces itself unmistakably", True,
               "GITGUARD IS OFF" in out and "NOT CHECKED" in out)
        record("C18b and its STAGE RESULT line is BYPASSED, never OK", (True, False),
               ("STAGE RESULT: BYPASSED" in out, "STAGE RESULT: OK" in out))
        logp = os.path.join(r, ".git", "r2-guard", "bypass.log")
        record("C18c the log names the actor AND the staged paths", True,
               os.path.exists(logp)
               and "world/items/bob.py" in open(logp).read()
               and "alice" in open(logp).read())
        # The direct-invocation path: `gitguard.py check` must not answer OK
        # to an agent whose hook has been switched off underneath it.
        rc, out = sh("python3 tools/gitguard.py check", r,
                     {"R2_AGENT": "alice", "R2_GITGUARD": "off"})
        record("C18d `check` under an inherited R2_GITGUARD=off never says OK",
               (True, False),
               ("STAGE RESULT: BYPASSED" in out, "STAGE RESULT: OK" in out))
        rc, out = sh("python3 tools/gitguard.py status --quiet", r)
        record("C18e `status` surfaces that a bypass happened at all", True,
               "BYPASSED COMMIT" in out)
        # OPT-IN REFUSAL: a repository can close the hatch.
        open(os.path.join(r, ".git", "r2-guard", "no-bypass"), "w").write("")
        open(os.path.join(r, "world/items/bob.py"), "a").write("# c18f\n")
        sh("git add world/items/bob.py", r)
        rc, out = sh('git commit -q -m "alice bypasses, refused"', r,
                     {"R2_AGENT": "alice", "R2_GITGUARD": "off"})
        record("C18f with .git/r2-guard/no-bypass the hatch is REFUSED",
               "REFUSED", guard_verdict(rc, out))
        os.remove(os.path.join(r, ".git", "r2-guard", "no-bypass"))
        rc, out = sh('git commit -q -m "alice bypasses, allowed again"', r,
                     {"R2_AGENT": "alice", "R2_GITGUARD": "off"})
        record("C18g VACUITY: the same commit passes once the marker is gone",
               "ALLOWED", guard_verdict(rc, out))

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
