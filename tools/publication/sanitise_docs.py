#!/usr/bin/env python3
"""Sanitise f1-round2 for public publication: prose AND code.

PASS 1 — PROSE (.md/.txt)
  P  paths containing /home/<user>, and the session scratchpad path
  H  rented-host identifiers (machine / instance / offer / container ids, IPs,
     broker labels, ssh port) -> stable pseudonyms, so identity-over-time
     findings survive
  M  account balances / credit remaining -> $[redacted]; costs and $/hr kept

PASS 2 — CODE AND RECORDS (.py/.sh/.json/.log)
  P  paths only, with a per-language policy (see PASS 2 below)

Pass 1 was written when the only publication risk anybody had counted was in
prose. It was correct for prose and is unchanged. But the owner's home
directory appears 1,200 times in this repository and only 3 of those are in a
.md file: the other 1,197 are in Python, shell, JSON and logs, where pass 1
never looked. Pass 2 is that other 99.75%.

Usage:
    python3 tools/publication/sanitise_docs.py                 # dry run, both
    python3 tools/publication/sanitise_docs.py --apply         # write
    python3 tools/publication/sanitise_docs.py --verify-canon  # check the map
    python3 tools/publication/sanitise_docs.py --prose-only    # pass 1 only

THE ONE INVARIANT
-----------------
`mach-11` and `id-016` must mean the same host in every document, forever.
That is the only reason the aliases exist rather than blanks: "the same machine
refused our key 61 h apart" is a finding, and it cannot be stated if the alias
moves between documents.

So the alias map is APPEND-ONLY. `alias_canon.txt` holds the identifiers in
allocation order and the alias is the line number. Its first 82 lines are the
set present at `c18c9f4~1`, the tree as it stood before the first sanitisation
commit, and `--verify-canon` re-derives them from that commit and checks them.
New identifiers are appended and take the next free number. Nothing is ever
re-sorted, and no identifier is ever removed, even if the document that
mentioned it is deleted.

The earlier version of this script rebuilt the map by sorting whatever 8-digit
numbers it found in the corpus at the time. That renumbers every alias the
moment a new lower-numbered id appears, silently, with no error.
"""
import argparse
import ast
import io
import os
import platform
import re
import subprocess
import sys
import tokenize
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUBDIR = os.path.join(ROOT, "tools", "publication")
CANON = os.path.join(PUBDIR, "alias_canon.txt")
CANON_BASE_COMMIT = "c18c9f4~1"

ap = argparse.ArgumentParser(add_help=True)
ap.add_argument("--apply", action="store_true",
                help="write the changes; default is a dry run")
ap.add_argument("--verify-canon", action="store_true",
                help="re-derive the canonical alias map from %s and stop"
                     % CANON_BASE_COMMIT)
ap.add_argument("--prose-only", action="store_true",
                help="run pass 1 only; skip the .py/.sh/.json/.log pass")
args = ap.parse_args()
DRY = not args.apply

# Files that belong to the publication decision itself, or that carry the
# redaction scheme as their subject matter.  Never rewrite these.
#
#   tools/publication/* -- alias_canon.txt IS the map.  The old file list matched
#   `*.txt` repo-wide, so a run would have replaced all 82 identifiers in the map
#   with their own aliases and destroyed it.  Caught by a dry run; it would not
#   have announced itself.
OWNED_BY_OTHERS = {
    "README.md", "LICENSE", "LICENSE-DOCS", "LICENSE.md", "LICENSE.txt",
    "COPYING", "COPYING.md", "NOTICE", "CONTRIBUTING.md",
}


def _git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout


def corpus():
    """Tracked AND untracked-but-not-ignored .md/.txt.

    Untracked files are included on purpose. The last pass missed four staging
    documents that had appeared but had not been added yet; a document is a
    publication risk from the moment it is written, not from the moment it is
    committed.
    """
    tracked = _git("ls-files", "*.md", "*.txt").split()
    untracked = _git("ls-files", "--others", "--exclude-standard",
                     "*.md", "*.txt").split()
    out = []
    for f in sorted(set(tracked) | set(untracked)):
        if f in OWNED_BY_OTHERS:
            continue
        if f.startswith("tools/publication/"):
            continue
        if os.path.isfile(os.path.join(ROOT, f)):
            out.append(f)
    return out, len(tracked), len(untracked)


# ------------------------------------------------------------------ alias map
# every 8-digit number in the corpus EXCEPT these, which are real measurements
NOT_IDS = {"22945780",   # triangle count
           "64971343", "67679807",  # sha256 prefixes
           "99926553",   # tail of 0.99926553
           "20260802",   # a date
           "00000000"}   # padding


def read_canon():
    ids, seen = [], set()
    with open(CANON, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            if line in seen:
                sys.exit(f"FATAL: {CANON} lists {line} twice. The alias map "
                         f"must be a bijection; fix it before running.")
            seen.add(line)
            ids.append(line)
    return ids


def verify_canon():
    """Re-derive the first block of the map from the commit it came from."""
    names = [f for f in _git("ls-tree", "-r", "--name-only",
                             CANON_BASE_COMMIT).split()
             if f.endswith((".md", ".txt")) and f not in OWNED_BY_OTHERS
             and not f.startswith("tools/publication/")]
    eight = set()
    for f in names:
        blob = subprocess.run(["git", "show", f"{CANON_BASE_COMMIT}:{f}"],
                              cwd=ROOT, capture_output=True, text=True)
        eight.update(re.findall(r"\b[0-9]{8}\b", blob.stdout))
    derived = sorted(eight - NOT_IDS, key=int)
    canon = read_canon()
    head = canon[:len(derived)]
    print(f"canonical base commit : {CANON_BASE_COMMIT}")
    print(f"derived from that tree: {len(derived)} identifiers")
    print(f"alias_canon.txt holds : {len(canon)} identifiers "
          f"({len(canon) - len(derived)} appended since)")
    if head == derived:
        print("RESULT: PASS — the first "
              f"{len(derived)} entries match the base tree in order, so "
              "id-001..id-%03d still mean what they meant." % len(derived))
        return 0
    print("RESULT: FAIL — the map has been renumbered against the base tree.")
    for i, (a, b) in enumerate(zip(head, derived)):
        if a != b:
            print(f"  first divergence at id-{i + 1:03d}: "
                  f"canon has {a}, base tree has {b}")
            break
    return 1


if args.verify_canon:
    sys.exit(verify_canon())

CANON_IDS = read_canon()
ID_MAP = {n: "id-%03d" % (i + 1) for i, n in enumerate(CANON_IDS)}

files, n_tracked, n_untracked = corpus()

# anything 8-digit and id-shaped that the canon has never seen.
#
# The github-noreply guard has to be HERE as well as in the substitution, and
# forgetting it here is the more expensive mistake of the two: this loop is
# what decides what gets APPENDED TO THE PERMANENT MAP. Guarding only the
# substitution would leave the document correct and the map permanently
# holding a GitHub account id as `id-083`, which the map's own charter forbids
# ever removing.
GITHUB_NOREPLY = re.compile(
    r"(?<![\d.])\b([0-9]{8})\b\+[^\s@]+@users\.noreply\.github\.com")
found = set()
for f in files:
    with open(os.path.join(ROOT, f), encoding="utf-8") as fh:
        body = fh.read()
    found.update(re.findall(r"(?<![\d.])\b[0-9]{8}\b(?!\d)", body))
    found -= set(GITHUB_NOREPLY.findall(body))
NEW_IDS = sorted(found - NOT_IDS - set(ID_MAP), key=int)
for i, n in enumerate(NEW_IDS):
    ID_MAP[n] = "id-%03d" % (len(CANON_IDS) + i + 1)   # appended, never inserted

# ------------------------------------------------------------- machine aliases
#
# 2026-08-18 — THE VALUES USED TO BE LITERALS RIGHT HERE, AND THAT WAS THE
# WHOLE LEAK.
#
# `docs/PUBLICATION-AUDIT.md` §4 is titled "The one real finding: the sanitiser
# ships its own de-aliasing table", and this was it. Eighteen real vast.ai
# machine ids and THREE REAL ROUTABLE IP ADDRESSES of rented third-party GPU
# hosts sat in this file as source literals. The documentation was correctly
# sanitised — the corpus says `mach-11` and `host-A` — but **this file is
# tracked, so shipping the sanitiser shipped the lookup table that undoes it.**
# Anyone with the published repository could reverse every alias in every
# document by reading two lines of Python. The redaction was cosmetic.
#
# The sibling repository had already caught the identical shape and written it
# into its own `.gitignore`, about `farm/hostrates.json`:
#
#     "Anyone holding both files joins them on those values and recovers every
#      identifier the aliasing was for. While this file was tracked, the docs'
#      redaction was cosmetic."
#
# It also fixed it the same way this does — `d056d4ba` over there is literally
# "untrack the table that de-aliases the docs".
#
# THE VALUES NOW LIVE IN AN UNTRACKED LOCAL FILE and the ALIASES stay here.
# `tools/publication/host_canon.txt` is gitignored, so a clone gets the method,
# the reasoning and the alias vocabulary — everything that makes this file worth
# reading — and gets no way to invert any of it.
#
# WHY THIS IS SAFE TO LOSE, WHICH IS THE ONLY QUESTION THAT MATTERS.
# The map is needed to SUBSTITUTE, not to DETECT. Without it:
#   * every existing document is unaffected; the corpus is already sanitised;
#   * `MACH_SHAPE` and `IP_SHAPE` below still fire on any machine id or any
#     non-benign address in the corpus, and still report it as unknown — which
#     is the check that actually protects a NEW document, and the check that
#     caught a planted 203.0.113.77 canary going through a full run untouched;
#   * only the automatic rewrite of a NEW occurrence is unavailable, and it
#     fails LOUD rather than silently doing nothing.
# So the failure mode of losing the map is "you are told to alias it by hand",
# not "it is silently published in the clear".
#
# Frozen in allocation order. NOT sorted at runtime, and NOT sorted in the file:
# sorting means that adding one machine below the current minimum silently
# shifts every alias above it. Append to the END and nowhere else — the same
# append-only charter `alias_canon.txt` carries, for the same reason.
HOST_CANON = os.path.join(PUBDIR, "host_canon.txt")


def read_host_canon():
    """Load the untracked machine-id and IP alias values.

    Returns (machines, ips). Missing file is NOT fatal — see the block above:
    detection survives without it and substitution is what degrades.
    """
    machines, ips = [], {}
    if not os.path.isfile(HOST_CANON):
        return machines, ips
    with open(HOST_CANON, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            kind, _, value = line.partition(":")
            if kind.strip() == "machine":
                machines.append(value.strip())
            elif kind.strip() == "ip":
                real, _, alias = value.partition("=")
                ips[real.strip()] = alias.strip()
    return machines, ips


MACHINES, IPS = read_host_canon()
assert len(set(MACHINES)) == len(MACHINES), "duplicate machine id"
MACH_MAP = {n: "mach-%02d" % (i + 1) for i, n in enumerate(MACHINES)}

if not MACHINES and not IPS:
    print("NOTE: %s is absent, so machine ids and host IPs will be DETECTED "
          "and reported but NOT substituted." % os.path.relpath(HOST_CANON, ROOT),
          file=sys.stderr)
    print("      That file is deliberately untracked — it is the table that "
          "de-aliases the corpus, and publishing it would make the aliasing "
          "cosmetic. See docs/PUBLICATION-AUDIT.md §4.", file=sys.stderr)

counts = Counter()


def sub(pattern, repl, text, tag, flags=0):
    new, n = re.subn(pattern, repl, text, flags=flags)
    if n:
        counts[tag] += n
    return new


def clean(text):
    # ---- P: paths -------------------------------------------------------
    # HOME is the detected login's home directory, not a literal. The literal
    # used to be written here, and this file is excluded from its own corpus,
    # so the one occurrence of the owner's login left in the whole repository
    # after a complete, successful, twice-verified run was inside the tool
    # that had just removed all the others.
    HOME = re.escape(HOMEDIR)
    text = sub(SCRATCH_RE.pattern, "SCRATCHPAD", text, "P/scratchpad")
    text = sub(r"/tmp/claude-[0-9]+/[^/\s`]*/[0-9a-fA-F-]{36}/scratchpad",
               "SCRATCHPAD", text, "P/scratchpad")
    text = sub("`" + HOME + r"/\.\.\.`", "`/home/<user>/...`", text, "P/generic")
    text = sub(HOME + r"/f1-round2/", "", text, "P/repo-relative")
    text = sub(HOME + r"/f1-round2", "~/f1-round2", text, "P/repo-bare")
    text = sub(HOME + r"/vast-render", "~/vast-render", text, "P/vast-render")
    text = sub(HOME + r"/opus5-car-render", "~/opus5-car-render",
               text, "P/opus5")
    text = sub(HOME + r"/publish", "~/publish", text, "P/publish")
    # THE CATCH-ALL, AND IT IS NOT REDUNDANT. Every rule above names a
    # directory; a sentence that says "322 tracked files contain /home/<user>"
    # names none, and three of those sentences — in an audit whose whole
    # subject is this leak — went through a complete run untouched because
    # nothing matched a bare home directory. The login is the personal datum,
    # with or without a path after it.
    text = sub(HOME + r"(?![A-Za-z0-9._/-])", "/home/<user>", text, "P/bare")

    # ---- H: rented-host identifiers -------------------------------------
    for ip, alias in IPS.items():
        text = sub(re.escape(ip) + r":21104", alias + ":PORT", text, "H/ip-port")
        text = sub(re.escape(ip), alias, text, "H/ip")

    # broker labels carry an epoch suffix unique to the account
    text = sub(r"\b(fleet[0-9]{2})-[0-9]{9,}\b", r"\1-LABEL", text, "H/label")

    # 8-digit vast instance / offer / container ids.  Guard against decimals
    # (0.99926553) and comma-grouped byte counts.
    #
    # NOTE the counting.  re.subn reports how many times the pattern MATCHED,
    # and this pattern matches every 8-digit number including the measurements
    # in NOT_IDS, which map to themselves.  Counting matches would report nine
    # redactions on a corpus with zero raw ids left in it — a number that looks
    # like work being done.  Count substitutions that actually changed the text.
    # A GITHUB ACCOUNT ID IS ALSO EIGHT DIGITS. `<id>+<name>@users.noreply.
    # github.com` is the privacy address GitHub issues, and the leading number
    # is the account id — nothing to do with a rented host. Left to the rule
    # below it became `id-083`, which did two kinds of damage at once: it
    # corrupted the one document that tells the owner what to commit under, and
    # it appended a non-host identifier to an APPEND-ONLY map that by its own
    # charter can never drop it again. Recognised by shape rather than by
    # blacklisting the number, because the account can change and the shape
    # cannot.
    def _id(m):
        s = m.group(0)
        tail = m.string[m.end():m.end() + 64]
        if tail.startswith("+") and "@users.noreply.github.com" in tail:
            return s
        a = ID_MAP.get(s, s)
        if a != s:
            counts["H/vast-id"] += 1
        return a
    text = re.sub(r"(?<![\d.])\b[0-9]{8}\b(?!\d)", _id, text)

    # machine ids: 4-6 digits, only the known set
    def _mach(m):
        s = m.group(0)
        a = MACH_MAP.get(s, s)
        if a != s:
            counts["H/machine-id"] += 1
        return a
    text = re.sub(r"(?<![\d.])\b(?:%s)\b(?!\d)" % "|".join(
        sorted(MACHINES, key=lambda x: -len(x))), _mach, text)

    # ---- M: account balances --------------------------------------------
    # Only the numeral is replaced; surrounding markdown (**, |, backticks) and
    # every cost / rate / cap figure is left alone.
    R = "$[redacted]"
    # a dollar figure that never ends on a comma (so "$150, credit" splits right)
    NUM = r"\$~?[0-9](?:[0-9,]*[0-9])?(?:\.[0-9]+)?"

    # stragglers where the balance is not adjacent to the word credit/balance
    for old, new in [
        ("credit $54.36 → $54.04.", "credit %s → %s." % (R, R)),
        ("| credit $69.59 | **$69.52** |", "| credit %s | **%s** |" % (R, R)),
        ("(was $62.46 earlier in this same block)",
         "(was %s earlier in this same block)" % R),
        ("not the $73.33 the", "not the %s the" % R),
        ("authorise $300 against $72 and", "authorise $300 against %s and" % R),
        ("$300 nominal against $72 real", "$300 nominal against %s real" % R),
        ("of runway against $72.39.", "of runway against %s." % R),
        ("start is **~$65.7**", "start is **~%s**" % R),
        ("(not from `rq`): $69.52.", "(not from `rq`): %s." % R),
        # --- added on the re-run.  The corpus grew a doc-accuracy audit whose
        # whole subject is stale numbers, and it quotes live balances to make
        # the point.  The point survives the redaction; the balance does not
        # need to.
        ("| vast.ai credit, most recent sample | **$45.2304** |",
         "| vast.ai credit, most recent sample | **%s** |" % R),
        ("most recent sample:\n**$45.2304**.", "most recent sample:\n**%s**." % R),
        ('(currently $25.00, autobill `None`', '(currently %s, autobill `None`' % R),
        ('against "$25 untouched"', 'against "%s untouched"' % R),
    ]:
        if old in text:
            counts["M/straggler"] += text.count(old)
            text = text.replace(old, new)

    def _money(tag):
        def f(m):
            counts[tag] += 1
            return m.group(1) + R
        return f

    # "credit $62.57", "Credit remaining **$45.47**", "| credit | **$60.56**",
    # "Credit at teardown: $68.10", "credit at 17:00   $74.34", "Credit is\n$154.87"
    text = re.sub(
        r"(\b(?i:credit|balance)\b(?:\s+remaining)?"
        r"(?:\s+(?i:is|was|before|after))?(?:\s+untouched)?"
        r"(?:\s+(?i:at)(?:\s+[0-9:]+|\s+teardown)?)?"
        r"(?:\s+when[^$\n]{0,60})?"
        r"\s*[|:,]?\s*\*{0,2})(?:" + NUM + r")",
        _money("M/credit-lead"), text)

    # "$68.10 credit", "$74.06 of credit", "$73.33 balance"
    text = re.sub(
        r"()(?:" + NUM + r")(?=\s+(?:of\s+)?(?:credit|balance)\b)",
        _money("M/credit-trail"), text)
    return text


# ==========================================================================
# PASS 2 — CODE AND RECORDS  (.py, .sh, .json, .log, shebang files)
# ==========================================================================
# Two things pass 1 does MUST NOT be done here, and they are the reason this is
# a separate pass rather than a wider file glob on the existing one.
#
# 1. THE 8-DIGIT ALIAS MAP MUST NOT TOUCH DATA. A vast instance id and a vertex
#    count are both 8-digit integers. NOT_IDS lists the five measurements that
#    happened to appear in PROSE; the .json under render/ and work/ is nothing
#    but measurements. Widening the pass-1 glob to *.json would have rewritten
#    triangle counts, frame numbers and hash prefixes into id-NNN, in files
#    nobody reads by eye, and every gate verdict in the repository would have
#    become quietly false. So pass 2 rewrites PATHS ONLY.
#
# 2. A PATH IN PROSE IS READ; A PATH IN CODE IS OPENED. Pass 1 turns
#    "/home/<user>/f1-round2/world/build_terrain.py" into
#    "world/build_terrain.py", which is better documentation than the original.
#    Doing that to a string literal makes it depend on the working directory,
#    and these scripts are launched by Blender with -P from wherever the caller
#    happened to be standing. The .json records the same paths and is read back
#    by the audit tools. So the policy is per-language, and it is chosen so the
#    RESOLVED value is byte-identical on the machine this repo was built on:
#
#      .md .txt   (pass 1)   /home/<user>/f1-round2/x  ->  x
#      .json .log            /home/<user>/f1-round2/x  ->  x
#      .sh                   /home/<user>/f1-round2/x  ->  $HOME/f1-round2/x
#      .py        "/home/<user>/f1-round2/x"
#                            ->  os.path.expanduser("~/f1-round2/x")
#
#    $HOME and expanduser("~") both give back the original absolute path on the
#    owner's machine, so nothing that ran yesterday stops running. For a
#    stranger who clones to ~/f1-round2 they resolve correctly too, which the
#    hard-coded original never did. _assert_roundtrip below checks the identity
#    rather than asserting it in a comment.
#
#    .json and .log are inert records — no process resolves a path out of them
#    at runtime, they are what a gate SAW — so they take the prose policy, and
#    repo-relative is the more useful form for a reader diffing a verdict.

def detect_login():
    """Find the login whose home directory this corpus mentions.

    NOT hardcoded, and not taken from `whoami` either, for two different
    reasons that both matter.

    Hardcoding it means the string this tool exists to delete is written into
    the tool, and `tools/publication/` is excluded from its own corpus, so the
    finished repository would publish the owner's login in the one file that
    claims to remove it. That is not a hypothetical trade-off: it was the last
    remaining occurrence after the first full run.

    Taking it from the environment means that running as root, or in a
    container, or under sudo — all of which happen — makes every path rule
    match nothing, and the tool then prints a clean report over an unsanitised
    tree. A checker that quietly does nothing is worse than no checker.

    So it is MEASURED from the corpus: whichever /home/<name> is actually
    present, reported by name and count, and an explicit "nothing to do" when
    the tree is already clean. SANITISE_LOGIN overrides it for the case where
    the corpus is clean but you want to re-prove the rules fire.
    """
    env = os.environ.get("SANITISE_LOGIN")
    if env:
        return env, {env: -1}
    seen = Counter()
    pats = ["*.md", "*.txt", "*.py", "*.sh", "*.json", "*.log"]
    names = set(_git("ls-files", *pats).split())
    names |= set(_git("ls-files", "--others", "--exclude-standard",
                      *pats).split())
    names |= set(DOTFILES)
    for f in names:
        if f.startswith("tools/publication/"):
            continue        # it quotes the patterns it removes
        p = os.path.join(ROOT, f)
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                body = fh.read(4_000_000)
        except OSError:
            continue
        for m in re.finditer(r"/home/([A-Za-z0-9][A-Za-z0-9._-]*)", body):
            seen[m.group(1)] += 1
    if not seen:
        return None, seen
    return seen.most_common(1)[0][0], seen


# Config files with prose comments in them, which carry no extension and no
# shebang and so were invisible to every glob in this file. .gitignore was the
# last tracked file in the repository still naming the owner's home directory,
# in a comment explaining a cross-repo symlink — a real point about the
# pipeline, which is why it is rewritten and not deleted.
DOTFILES = [".gitignore", ".gitattributes", ".editorconfig"]

USER, LOGIN_HITS = detect_login()
HOMEDIR = "/home/" + (USER or "\x00-no-login-detected")
SELF_REPO = "f1-round2"

# Sibling projects the logs legitimately refer to. Anything under /home/<user>/
# that is NOT on this list is an unrelated project of the owner's and its very
# name is personal data, so it is reported rather than rewritten.
KNOWN_SIBLINGS = {SELF_REPO, "vast-render", "opus5-car-render", "publish"}

# The agent session scratchpad. It carries the login AND a session uuid, and it
# is /tmp, so nothing about it is worth preserving except that it was scratch.
SCRATCH_RE = re.compile(
    r"/tmp/claude-[0-9]+/-home-" + re.escape(USER or "\x00") +
    r"-[A-Za-z0-9._-]+/[0-9a-fA-F-]{36}/scratchpad")
SCRATCH_CODE = "/tmp/f1-round2-scratch"

PATH_RE = re.compile(re.escape(HOMEDIR) + r"(/[A-Za-z0-9._-]+)?")

# ------------------------------------------------------- the machine's name
# 46 tracked records stamp the authoring workstation's hostname beside the
# timestamp of the run that produced them: `"host": "<name>"`. It is a real
# machine on somebody's desk and it is not a path, so nothing above touched it.
#
# It is ALIASED rather than removed because it is doing work. Its whole job in
# these records is to say "this verdict was measured on the local box, not on a
# rented one", and that distinction is exactly what the rented-host aliases
# elsewhere exist to keep readable. `workstation` says it and names nobody.
#
# `"host"` is TWO SCHEMAS in this repository and only one of them is a machine:
#     {"stamped_at": ..., "host": "<hostname>"}      the machine
#     {"host": "ARCH_PitWall", "host_verts": 24664}  a 3D object an item sits on
# so the substitution is keyed to the detected hostname and not to the field
# name. Every other value the field takes is reported once, for one glance,
# rather than rewritten or ignored.
MACHINE_NAME = os.environ.get("SANITISE_HOST") or platform.node()
HOST_FIELD = re.compile(r'("host"\s*:\s*")([^"]*)(")')
HOST_ALIAS = "workstation"

code_counts = Counter()
code_notes = []          # (relpath, note) — things a human must look at
host_values = Counter()  # every value the `"host"` field takes, surveyed


def _unknown_siblings(text, rel):
    """Flag /home/<user>/<something-we-do-not-recognise>.

    The login is removed from these the same as any other path, so this is not
    a leak of the username. It is a DISCLOSURE question, which is a different
    thing and belongs to the owner: `~/some-other-project/` still names a
    directory of theirs that has nothing to do with this film, and the fact
    that it exists is information the repository was not meant to publish.
    """
    seen = set()
    for m in PATH_RE.finditer(text):
        seg = (m.group(1) or "/").lstrip("/")
        if seg and seg not in KNOWN_SIBLINGS and seg not in seen:
            seen.add(seg)
            code_notes.append(
                (rel, "names an unrecognised directory of the owner's, %r. The"
                      " login is removed but the DIRECTORY NAME survives —"
                      " decide whether it discloses an unrelated project."
                 % ("~/" + seg)))


def _host_field(text, rel):
    """Alias the authoring machine's hostname where a record stamps it."""
    def f(m):
        if m.group(2) == MACHINE_NAME:
            code_counts["H/hostname"] += 1
            return m.group(1) + HOST_ALIAS + m.group(3)
        if m.group(2) not in (HOST_ALIAS, ""):
            code_notes.append(
                (rel, '"host": %r is not the detected machine name %r — check '
                      "whether it is a hostname or a 3D object"
                 % (m.group(2), MACHINE_NAME)))
        return m.group(0)
    return HOST_FIELD.sub(f, text)


def _record_paths(text, rel):
    """Policy for inert records (.json, .log) and for shell comments."""
    _unknown_siblings(text, rel)
    text, n = SCRATCH_RE.subn("SCRATCHPAD", text)
    code_counts["P/scratchpad"] += n
    text, n = re.subn(re.escape(HOMEDIR + "/" + SELF_REPO) + "/", "", text)
    code_counts["P/repo-relative"] += n
    for sib in sorted(KNOWN_SIBLINGS, key=len, reverse=True):
        text, n = re.subn(re.escape(HOMEDIR + "/" + sib), "~/" + sib, text)
        code_counts["P/sibling-tilde"] += n
    text, n = re.subn(re.escape(HOMEDIR) + r"(?![A-Za-z0-9._-])",
                      "~", text)
    code_counts["P/home-bare"] += n
    return text


_HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def _sh_quote_state(text, pos, state=None):
    """Shell quoting state at `pos`: None, "'" or '"'. `state` carries in.

    Shell quoting is not nestable and not regex-decidable, but it IS a
    three-state machine, and the distinction matters enormously here: $HOME
    expands inside double quotes and does not expand inside single quotes.

    IT MUST CARRY ACROSS LINES. The line this check exists for is

        $B -b $A10 --factory-startup --python-expr "
        ...
        _reg = json.load(open('/home/<user>/f1-round2/world/items/PLACEMENT.json'))

    — a shell double-quoted string opened eight lines earlier and still open.
    Judged one line at a time it looks single-quoted and the tool sends it to a
    human as unfixable; judged with the state carried in, the single quotes are
    PYTHON's, inside the shell's double-quoted argument, the shell does expand
    $HOME, and the rewrite is both safe and automatic. A per-line reset was
    wrong in exactly the direction that produces false confidence about how
    much still needs doing by hand.

    IT ALSO HAS TO SKIP COMMENTS. Carrying state across lines without doing so
    made things worse, not better: these scripts are heavily commented in
    English, every "doesn't" and "script's" opened a single-quoted string that
    never closed, and the tool went from two hand-fixes to nineteen — all but
    three of them imaginary. A checker that over-reports is not the safe
    direction; it buries the real hits.
    """
    i = 0
    while i < pos and i < len(text):
        c = text[i]
        if state is None:
            if c == "\\":
                i += 2
                continue
            if c == "#" and (i == 0 or text[i - 1] in " \t\n;&|(") :
                break                      # comment to end of line
            if c in "'\"":
                state = c
        elif c == state:
            state = None
        elif state == '"' and c == "\\":
            i += 2
            continue
        i += 1
    return state


def _sh_line(line, rel):
    _unknown_siblings(line, rel)
    line, n = SCRATCH_RE.subn(SCRATCH_CODE, line)
    code_counts["P/scratchpad"] += n
    # Plain $HOME, not "$HOME". Most of these occurrences are already inside a
    # double-quoted string or a heredoc-adjacent Python line, and splicing a
    # quote pair into those produces `""$HOME"/f1-round2/x"` — which the shell
    # still resolves but which is no longer valid Python once the heredoc is
    # read. $HOME is correct in every context here and this repository's home
    # directory contains no whitespace, so the word-splitting argument for the
    # quotes does not apply.
    line, n = re.subn(re.escape(HOMEDIR) + r"(?![A-Za-z0-9._-])", "$HOME", line)
    code_counts["P/sh-home"] += n
    return line


def _shell_paths(text, rel):
    """Policy for shell: $HOME expands to exactly what the literal said.

    Line-by-line rather than whole-file, because a .sh in this repository is
    frequently a wrapper around a QUOTED heredoc of Python:

        python3 - <<'PY'
        ...
        PY

    Inside `<<'PY'` the shell expands nothing at all, so writing $HOME there
    produces a program that opens a directory literally named `$HOME`. Every
    heredoc in this repository is the quoted form, so a whole-file regex would
    have got every one of them wrong, and silently: the script would still run
    and would still print a verdict.
    """
    out = []
    inside = None                   # (delimiter, expands)
    qstate = None                   # shell quote state carried between lines
    for i, line in enumerate(text.splitlines(keepends=True), 1):
        touched = HOMEDIR in line or SCRATCH_RE.search(line)
        if inside is not None:
            if line.strip() == inside[0]:
                inside = None
            elif touched:
                if inside[1]:
                    line = _sh_line(line, rel)
                else:
                    code_notes.append(
                        (rel, "line %d: %s inside the quoted heredoc <<'%s', "
                              "where the shell expands nothing — fix by hand"
                         % (i, HOMEDIR, inside[0])))
            out.append(line)
            continue
        if touched:
            at = line.find(HOMEDIR)
            if _sh_quote_state(line, at, qstate) == "'":
                code_notes.append(
                    (rel, "line %d: %s inside single quotes, where $HOME does "
                          "not expand — fix by hand" % (i, HOMEDIR)))
            else:
                line = _sh_line(line, rel)
        qstate = _sh_quote_state(line, len(line), qstate)
        m = _HEREDOC.search(line)
        if m and qstate is None:
            inside = (m.group(2), m.group(1) == "")
        out.append(line)
    return "".join(out)


# ------------------------------------------------------------------ python
_STR_PREFIX = re.compile(r"^([A-Za-z]*)('''|\"\"\"|'|\")")
_SKIP = {tokenize.NL, tokenize.COMMENT, tokenize.NEWLINE,
         tokenize.INDENT, tokenize.DEDENT}


def _assert_roundtrip(old_body, new_body):
    """expanduser('~/x') on the owner's box must give back the original.

    Checked textually against the literal home directory rather than against
    os.path.expanduser, because this script is frequently run as a different
    user (or in a container) than the one whose paths are being removed, and
    then expanduser('~') is not HOMEDIR and the check would pass or fail for
    reasons that have nothing to do with the rewrite.
    """
    return new_body.replace("~", HOMEDIR, 1) == old_body


def _sig(toks, i, step):
    j = i + step
    while 0 <= j < len(toks) and toks[j].type in _SKIP:
        j += step
    return toks[j] if 0 <= j < len(toks) else None


def _docstring_starts(src):
    """(line, col) of every module / class / function docstring in the file.

    A docstring is PROSE that happens to be a string literal. Roughly half the
    scripts in this repository open with a docstring that quotes the exact
    blender command line used to run them, home directory and all, and those
    must be rewritten the way a .md is rewritten — repo-relative, readable —
    not wrapped in os.path.expanduser, which would turn the documentation into
    an expression and change nothing about how the file runs.

    Told apart by position from the AST rather than by "is it triple quoted",
    because a triple-quoted string is also how several of these files hold a
    heredoc they hand to a subprocess.
    """
    out = set()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                and isinstance(first.value.value, str):
            out.add((first.value.lineno, first.value.col_offset))
    return out


def _py_rewrite(src, rel):
    """Token-aware rewrite of /home/<user> inside a Python source file.

    Works on tokens, not on the raw text, because occurrences that look
    identical to a regex need opposite treatment:

        PATH = "/home/<user>/f1-round2/world"      a path -> wrap in expanduser
        print("see /home/<user>/f1-round2/world")  prose  -> textual, no wrap
        \"\"\"run: blender -P ... /home/<user>/...\"\"\"   docstring -> textual

    and on RUNS of adjacent string tokens rather than single tokens, because
    Python concatenates them implicitly and wrapping only the first produces
    `os.path.expanduser("a") "b"` — a syntax error. Two real paths in this
    repository are written that way, one of them the argument to
    `bpy.ops.wm.open_mainfile`, so the run is wrapped as a whole:

        bpy.ops.wm.open_mainfile(filepath="/home/<user>/f1-round2/world/items/"
                                          "hospitality_deck_test.blend")

    becomes one expanduser call around both halves, and the line still opens
    the file it always opened.
    """
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenError, SyntaxError) as exc:
        code_notes.append((rel, "will not tokenise (%s) — left untouched" % exc))
        return src, False

    docstrings = _docstring_starts(src)
    starts = [0]
    for line in src.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))

    def off(pos):
        return starts[pos[0] - 1] + pos[1]

    def split_lit(tok):
        m = _STR_PREFIX.match(tok.string)
        if not m:
            return None
        prefix, quote = m.group(1), m.group(2)
        return prefix, quote, tok.string[len(prefix) + len(quote):-len(quote)]

    edits = []          # (start_offset, end_offset, replacement)
    wrapped = 0
    i = 0
    while i < len(toks):
        t = toks[i]
        if t.type == tokenize.COMMENT:
            if HOMEDIR in t.string or SCRATCH_RE.search(t.string):
                edits.append((off(t.start), off(t.end),
                              _record_paths(t.string, rel)))
                code_counts["P/py-comment"] += 1
            i += 1
            continue
        if t.type != tokenize.STRING:
            if HOMEDIR in t.string or SCRATCH_RE.search(t.string):
                # FSTRING_MIDDLE and anything else: report, never guess.
                code_notes.append(
                    (rel, "line %d: %s in a %s token — fix by hand"
                     % (t.start[0], HOMEDIR, tokenize.tok_name[t.type])))
            i += 1
            continue

        # ---- gather the whole implicit-concatenation run ------------------
        run = [i]
        j = i
        while True:
            nxt = _sig(toks, j, +1)
            if nxt is None or nxt.type != tokenize.STRING:
                break
            j = toks.index(nxt, j + 1)
            run.append(j)
        i = j + 1

        rtoks = [toks[k] for k in run]
        parts = [split_lit(x) for x in rtoks]
        if any(p is None for p in parts) and any(
                HOMEDIR in x.string for x in rtoks):
            code_notes.append((rel, "line %d: unparseable string literal"
                               % rtoks[0].start[0]))
            continue
        if any(p is None for p in parts):
            continue

        # THE RUN, NOT THE TOKEN, IS THE UNIT OF INTEREST. A path can be split
        # across the pieces of an implicit concatenation, and then it is in
        # NEITHER piece as far as a per-token search is concerned — and it is
        # not in the joined SOURCE either, because the quotes sit in the middle
        # of it. That is not hypothetical: prove_items_cheap.py splits the
        # session scratchpad path exactly on the "…-car-render/" boundary, so
        # the first version of this function found nothing there, rewrote
        # nothing, warned about nothing, and reported a clean run over a file
        # that still named the owner. The joint has to be made on the string
        # VALUES, which is what the interpreter concatenates.
        joined = "".join(p[2] for p in parts)
        if HOMEDIR not in joined and not SCRATCH_RE.search(joined):
            continue

        for x in rtoks:
            _unknown_siblings(x.string, rel)

        is_doc = (rtoks[0].start in docstrings)
        binary = any(c in p[0].lower() for p in parts for c in "bf")
        first_body = parts[0][2]

        def as_text():
            for x, (pre, q, body) in zip(rtoks, parts):
                if HOMEDIR in body or SCRATCH_RE.search(body):
                    edits.append((off(x.start), off(x.end),
                                  pre + q + _record_paths(body, rel) + q))

        # scratchpad: /tmp, not /home; never needs wrapping, only replacing
        if SCRATCH_RE.search(joined) and HOMEDIR not in joined:
            q0 = parts[0][1]
            new_joined, n = SCRATCH_RE.subn(SCRATCH_CODE, joined)
            if binary or q0 not in ("'", '"') or q0 in new_joined:
                code_notes.append(
                    (rel, "line %d: scratchpad path in an awkward literal — "
                          "fix by hand" % rtoks[0].start[0]))
                continue
            code_counts["P/scratchpad"] += n
            edits.append((off(rtoks[0].start), off(rtoks[-1].end),
                          q0 + new_joined + q0))
            continue

        # A home path SPLIT across the pieces: no piece starts with it, so the
        # wrap test below would fall through to the text branch and quietly
        # leave the login in the file. Say so instead.
        if HOMEDIR in joined and not any(HOMEDIR in p[2] for p in parts):
            code_notes.append(
                (rel, "line %d: %s is split across a concatenated literal — "
                      "fix by hand" % (rtoks[0].start[0], HOMEDIR)))
            continue

        if is_doc:
            as_text()
            code_counts["P/py-docstring"] += 1
            continue

        if first_body.startswith(HOMEDIR + "/") and not binary \
                and parts[0][1] in ("'", '"'):
            new_first = "~" + first_body[len(HOMEDIR):]
            if not _assert_roundtrip(first_body, new_first):
                code_notes.append((rel, "line %d: round-trip check FAILED, "
                                        "not rewritten" % rtoks[0].start[0]))
                as_text()
                continue
            if any(HOMEDIR in p[2] for p in parts[1:]):
                code_notes.append(
                    (rel, "line %d: %s appears in a LATER piece of a "
                          "concatenated literal too — fix by hand"
                     % (rtoks[0].start[0], HOMEDIR)))
                as_text()
                continue
            # one expanduser around the entire run, whatever its shape
            run_src = src[off(rtoks[0].start):off(rtoks[-1].end)]
            head = parts[0][0] + parts[0][1] + first_body + parts[0][1]
            assert run_src.startswith(head), rel
            new_head = parts[0][0] + parts[0][1] + new_first + parts[0][1]
            edits.append((off(rtoks[0].start), off(rtoks[-1].end),
                          "os.path.expanduser(" + new_head
                          + run_src[len(head):] + ")"))
            wrapped += 1
            code_counts["P/py-expanduser"] += 1
        else:
            why = ("f/b-string" if binary else
                   "path is not at the start of the literal")
            code_notes.append(
                (rel, "line %d: not wrapped (%s) — rewritten as text, CHECK "
                      "that this literal is not opened"
                 % (rtoks[0].start[0], why)))
            as_text()
            code_counts["P/py-text"] += 1

    if not edits:
        return src, False
    out = src
    for a, b, new in sorted(edits, reverse=True):
        out = out[:a] + new + out[b:]
    if wrapped:
        out = _ensure_import_os(out, rel)
    return out, True


def _has_import_os(tree):
    for node in tree.body:
        if isinstance(node, ast.Import):
            if any(a.name == "os" or a.name.startswith("os.")
                   for a in node.names):
                return True
    return False


def _ensure_import_os(src, rel):
    """Add `import os` if the wrap introduced a use of it and it is missing.

    Only module-level `import os` / `import os.path` counts. `from os import
    path` binds `path`, not `os`, and would leave a NameError behind a rewrite
    that looked finished — which is the whole failure mode this function is
    here to avoid.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        code_notes.append((rel, "post-rewrite parse failed: %s" % exc))
        return src
    if _has_import_os(tree):
        return src
    lines = src.splitlines(keepends=True)
    i = 0
    while i < len(lines) and (lines[i].startswith("#!")
                             or "coding" in lines[i][:40] and
                             lines[i].lstrip().startswith("#")):
        i += 1
    if tree.body and isinstance(tree.body[0], ast.Expr) \
            and isinstance(tree.body[0].value, ast.Constant) \
            and isinstance(tree.body[0].value.value, str):
        i = max(i, tree.body[0].end_lineno)          # past the docstring
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            i = max(i, node.end_lineno)
    lines.insert(i, "import os\n")
    code_counts["P/py-import-os"] += 1
    return "".join(lines)


def code_corpus():
    """Tracked and untracked-but-not-ignored code and records.

    Extensionless files are included when their first line is a shebang:
    tools/r5090 is a bash script with no .sh on it and carried a raw home
    directory through every previous pass because every previous pass globbed
    on extension.
    """
    pats = ["*.py", "*.sh", "*.json", "*.log"]
    names = set(_git("ls-files", *pats).split())
    names |= set(_git("ls-files", "--others", "--exclude-standard",
                      *pats).split())
    names |= set(DOTFILES)
    for f in _git("ls-files").split() + _git(
            "ls-files", "--others", "--exclude-standard").split():
        if "." in os.path.basename(f):
            continue
        p = os.path.join(ROOT, f)
        try:
            with open(p, "rb") as fh:
                if fh.read(2) == b"#!":
                    names.add(f)
        except OSError:
            pass
    names |= set(DOTFILES)
    out = []
    for f in sorted(names):
        if f.startswith("tools/publication/"):
            continue        # this file quotes the patterns it removes
        if os.path.isfile(os.path.join(ROOT, f)):
            out.append(f)
    return out


def sanitise_code():
    changed = []
    for rel in code_corpus():
        p = os.path.join(ROOT, rel)
        try:
            with open(p, encoding="utf-8") as fh:
                old = fh.read()
        except (UnicodeDecodeError, OSError):
            continue
        # Survey EVERY file's `"host"` values, before the filter below decides
        # this file is uninteresting. Reporting only on files that already
        # matched something else would mean a record whose ONLY personal datum
        # is a machine name gets neither rewritten nor mentioned — a clean
        # report produced by not looking, which is the failure this repository
        # keeps a catalogue of.
        for hm in HOST_FIELD.finditer(old):
            host_values[hm.group(2)] += 1

        # NOT `if HOMEDIR not in old: continue`. The hostname rule below is the
        # first thing in this pass that is not about paths, and 46 of the 50
        # records that stamp the machine's name carry no home directory at all
        # — so a home-directory-shaped filter would have skipped every one of
        # them and printed a clean run over 46 files naming a real machine.
        if not (HOMEDIR in old or SCRATCH_RE.search(old)
                or (MACHINE_NAME and MACHINE_NAME in old)):
            continue
        ext = os.path.splitext(rel)[1]
        if HOMEDIR in old or SCRATCH_RE.search(old):
            if ext == ".py":
                new, _ = _py_rewrite(old, rel)
            elif ext == ".sh" or (ext == "" and old.startswith("#!")):
                new = _shell_paths(old, rel)
            else:
                new = _record_paths(old, rel)
        else:
            new = old
        new = _host_field(new, rel)
        if new == old:
            continue
        # Never write a file we have just broken.
        if ext == ".py":
            try:
                compile(new, rel, "exec")
            except SyntaxError as exc:
                code_notes.append((rel, "REFUSED: rewrite does not compile "
                                        "(%s) — file left unchanged" % exc))
                continue
        if ext == ".json":
            import json as _json
            try:
                _json.loads(new)
            except ValueError as exc:
                code_notes.append((rel, "REFUSED: rewrite is not valid JSON "
                                        "(%s) — file left unchanged" % exc))
                continue
        changed.append(rel)
        if not DRY:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(new)
    return changed


# ------------------------------------------------------------------- unknown
# A machine id that is not in MACHINES is invisible to the substitution above:
# it is simply left in the clear, and the run reports success.  That is exactly
# how BROKEN-INSTRUMENTS.md shipped machine 58073 in the middle of a completed
# sanitisation pass.  So look for the shape and complain, rather than assume the
# hardcoded list is still complete.
MACH_SHAPE = re.compile(
    r"\bmachine[ _-]?(?:id)?[ :=#]*([0-9]{4,6})\b", re.I)

# The same hole exists for IP addresses and is not hypothetical: IPS holds three
# hosts because three hosts were in the corpus when it was written.  A fourth
# rented host would be substituted by nothing and reported by nothing.  A canary
# line carrying 203.0.113.77 went through a full run untouched and unmentioned,
# which is how this check came to exist.
#
# BENIGN, checked, and deliberately not flagged:
#   127.0.0.1  architecturally load-bearing throughout
#   1.1.1.1    a ping target in a network-flap diagnosis (Cloudflare resolver)
#   8.8.8.8    likewise
#   0.0.0.0    a bind address
# Version-number-shaped things (5.2.0.1) are excluded by requiring four octets
# that are each a valid 0-255 and by rejecting a leading/trailing dot.
IP_SHAPE = re.compile(r"(?<![\d.])((?:\d{1,3}\.){3}\d{1,3})(?![\d.])")
BENIGN_IPS = {"127.0.0.1", "1.1.1.1", "8.8.8.8", "0.0.0.0", "255.255.255.255"}

# Explained IN A SPECIFIC FILE, and allowed only there.
#
# The obvious fix for these three was to add them to BENIGN_IPS. That would
# have been a mistake, and a self-inflicted one: 203.0.113.77 is the address
# this repository's own plant-and-prove procedure tells you to write into a
# canary file to check that the IP detector can fire at all. Whitelisting it
# globally would leave the procedure printing "clean" for the rest of time
# while proving nothing — the exact instrument failure BROKEN-INSTRUMENTS.md
# is a catalogue of. Keyed to (file, address), the canary in docs/ZZ-CANARY.md
# still fires and the audit that discusses the scheme stays quiet.
IP_EXPLAINED = {
    # a report whose subject IS the redaction scheme; it quotes the RFC 5737
    # documentation ranges as examples and says so on the same line
    ("docs/PUBLICATION-AUDIT.md", "203.0.113.77"),
    ("docs/PUBLICATION-AUDIT.md", "198.51.100.4"),
    # not an address: Blender 5.2.0.1, four dot-separated numbers each < 256
    ("docs/PUBLICATION-AUDIT.md", "5.2.0.1"),
}

unknown_machines = Counter()
unknown_ips = Counter()
for f in files:
    with open(os.path.join(ROOT, f), encoding="utf-8") as fh:
        body = fh.read()
    for m in MACH_SHAPE.finditer(body):
        if m.group(1) not in MACH_MAP:
            unknown_machines[(f, m.group(1))] += 1
    for m in IP_SHAPE.finditer(body):
        ip = m.group(1)
        if ip in BENIGN_IPS or ip in IPS or (f, ip) in IP_EXPLAINED:
            continue
        if any(int(o) > 255 for o in ip.split(".")):
            continue          # not an address; a version or a dotted number
        unknown_ips[(f, ip)] += 1

changed = 0
changed_files = []
for f in files:
    p = os.path.join(ROOT, f)
    with open(p, encoding="utf-8") as fh:
        old = fh.read()
    new = clean(old)
    if new != old:
        changed += 1
        changed_files.append(f)
        if not DRY:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(new)

# Grow the canonical map, append-only, so the next run agrees with this one.
#
# The seek/read dance is not defensive padding. alias_canon.txt was written
# without a trailing newline, so a plain append would have produced
# "4752304941234567" — one corrupted id-082, one silently missing id-083, and a
# map that still parses. Check the last byte instead of assuming it.
if NEW_IDS and not DRY:
    needs_nl = False
    with open(CANON, "rb") as fh:
        if fh.seek(0, os.SEEK_END) and (fh.seek(-1, os.SEEK_END) or True):
            needs_nl = fh.read(1) != b"\n"
    with open(CANON, "a", encoding="utf-8") as fh:
        if needs_nl:
            fh.write("\n")
        for n in NEW_IDS:
            fh.write(n + "\n")

print("DRY RUN (pass --apply to write)" if DRY else "APPLIED")
print(f"corpus: {len(files)} files "
      f"({n_tracked} tracked + {n_untracked} untracked, minus owned/publication)")
print(f"files changed: {changed} of {len(files)}")
for f in changed_files[:20]:
    print(f"    {f}")
if len(changed_files) > 20:
    print(f"    ... and {len(changed_files) - 20} more")
print(f"alias map: {len(CANON_IDS)} canonical ids"
      + (f" + {len(NEW_IDS)} newly appended ({', '.join(NEW_IDS)})"
         if NEW_IDS else " + 0 new"))
print(f"machine aliases: {len(MACH_MAP)} (frozen order)")
for k, v in sorted(counts.items()):
    print(f"  {k:24s} {v}")

rc = 0

# ------------------------------------------------------- pass 2: code/records
code_changed = []
if not args.prose_only:
    code_all = code_corpus()
    code_changed = sanitise_code()
    print(f"\nPASS 2 — code and records")
    if USER is None:
        print("  login detected in the corpus: NONE — no /home/<name> path is "
              "left to remove.\n  Set SANITISE_LOGIN=<name> to re-prove the "
              "rules still fire (see the canary\n  procedure in "
              "tools/publication/README.md).")
    else:
        print("  login detected in the corpus: %r, %d occurrence(s)%s"
              % (USER, LOGIN_HITS[USER],
                 "" if len(LOGIN_HITS) == 1 else
                 "; ALSO SAW %s — check these are not further logins"
                 % ", ".join("%s (x%d)" % (k, v) for k, v in
                             LOGIN_HITS.most_common() if k != USER)))
    print(f"corpus: {len(code_all)} .py/.sh/.json/.log/shebang files "
          f"(tracked + untracked, minus tools/publication)")
    print(f"files changed: {len(code_changed)} of {len(code_all)}")
    for f in code_changed[:20]:
        print(f"    {f}")
    if len(code_changed) > 20:
        print(f"    ... and {len(code_changed) - 20} more")
    for k, v in sorted(code_counts.items()):
        if v:
            print(f"  {k:24s} {v}")
    if host_values:
        print("  \"host\" field values seen across the whole corpus:")
        for v, c in host_values.most_common():
            mark = ("  <- the machine, aliased to %r" % HOST_ALIAS
                    if v == MACHINE_NAME else
                    "  <- already the alias" if v == HOST_ALIAS else
                    "  <- NOT the detected machine name; check it")
            print("      %-24s x%-4d%s" % (repr(v), c, mark))
    if code_notes:
        print("\nWARNING: pass 2 could not decide these on its own. Each is a"
              "\n         path this script did NOT wrap, or refused to write:")
        for rel, note in code_notes:
            print(f"    {rel}: {note}")
        rc = 3
    else:
        print("  every occurrence rewritten mechanically; nothing left to a "
              "human")
if unknown_machines:
    print("\nWARNING: machine-id-shaped numbers not in the alias map. Each is a"
          "\n         raw identifier that this script leaves in the clear:")
    for (f, n), c in sorted(unknown_machines.items()):
        print(f"    {f}: machine {n} (x{c})")
    print("         Append them to the END of MACHINES and re-run. Appending is"
          "\n         not optional wording: inserting renumbers every mach-NN above.")
    rc = 3

if unknown_ips:
    print("\nWARNING: IP addresses not in the alias map and not on the benign"
          "\n         list. This script leaves these in the clear:")
    for (f, ip), c in sorted(unknown_ips.items()):
        print(f"    {f}: {ip} (x{c})")
    print("         Add real rented hosts to IPS as host-D, host-E, ...; add"
          "\n         public well-known addresses to BENIGN_IPS with a reason.")
    rc = 3

if rc == 0:
    print("\nno unknown machine ids or IP addresses in the corpus")
sys.exit(rc)
