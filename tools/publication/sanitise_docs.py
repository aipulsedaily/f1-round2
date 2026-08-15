#!/usr/bin/env python3
"""Sanitise prose in f1-round2 .md/.txt for public publication.

Categories:
  P  paths containing /home/zany, and the session scratchpad path
  H  rented-host identifiers (machine / instance / offer / container ids, IPs,
     broker labels, ssh port) -> stable pseudonyms, so identity-over-time
     findings survive
  M  account balances / credit remaining -> $[redacted]; costs and $/hr kept

Usage:
    python3 tools/publication/sanitise_docs.py                 # dry run
    python3 tools/publication/sanitise_docs.py --apply         # write
    python3 tools/publication/sanitise_docs.py --verify-canon  # check the map

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
import os
import re
import subprocess
import sys
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

# anything 8-digit and id-shaped that the canon has never seen
found = set()
for f in files:
    with open(os.path.join(ROOT, f), encoding="utf-8") as fh:
        found.update(re.findall(r"(?<![\d.])\b[0-9]{8}\b(?!\d)", fh.read()))
NEW_IDS = sorted(found - NOT_IDS - set(ID_MAP), key=int)
for i, n in enumerate(NEW_IDS):
    ID_MAP[n] = "id-%03d" % (len(CANON_IDS) + i + 1)   # appended, never inserted

# ------------------------------------------------------------- machine aliases
# Frozen in allocation order.  NOT sorted at runtime: sorting means that adding
# one machine below the current minimum silently shifts every alias above it.
# Append new machines to the END of this list and nowhere else.
MACHINES = ["8449", "8512", "31233", "34481", "36179", "43130", "44842",
            "46633", "52271", "53711", "58073", "73811", "131197", "137580",
            "138180", "141468", "142281", "144732"]
assert len(set(MACHINES)) == len(MACHINES), "duplicate machine id"
MACH_MAP = {n: "mach-%02d" % (i + 1) for i, n in enumerate(MACHINES)}

IPS = {"host-A": "host-A",
       "host-B": "host-B",
       "host-C": "host-C"}

counts = Counter()


def sub(pattern, repl, text, tag, flags=0):
    new, n = re.subn(pattern, repl, text, flags=flags)
    if n:
        counts[tag] += n
    return new


def clean(text):
    # ---- P: paths -------------------------------------------------------
    text = sub(r"/tmp/claude-0/-home-zany-opus5-car-render/"
               r"262f2abe-1dfb-4a32-9544-52393037f67a/scratchpad",
               "SCRATCHPAD", text, "P/scratchpad")
    text = sub(r"/tmp/claude-0/[^/\s`]*/262f2abe[^/\s`]*/scratchpad",
               "SCRATCHPAD", text, "P/scratchpad")
    text = sub(r"`/home/zany/\.\.\.`", "`/home/<user>/...`", text, "P/generic")
    text = sub(r"/home/zany/f1-round2/", "", text, "P/repo-relative")
    text = sub(r"/home/zany/f1-round2", "~/f1-round2", text, "P/repo-bare")
    text = sub(r"/home/zany/vast-render", "~/vast-render", text, "P/vast-render")
    text = sub(r"/home/zany/opus5-car-render", "~/opus5-car-render",
               text, "P/opus5")
    text = sub(r"/home/zany/publish", "~/publish", text, "P/publish")

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
    def _id(m):
        s = m.group(0)
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
        if ip in BENIGN_IPS or ip in IPS:
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
