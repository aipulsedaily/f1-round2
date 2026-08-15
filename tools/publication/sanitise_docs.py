#!/usr/bin/env python3
"""Sanitise prose in f1-round2 tracked .md/.txt for public publication.

Categories:
  P  paths containing /home/zany, and the session scratchpad path
  H  rented-host identifiers (machine / instance / offer / container ids, IPs,
     broker labels, ssh port) -> stable pseudonyms, so identity-over-time
     findings survive
  M  account balances / credit remaining -> $[redacted]; costs and $/hr kept
"""
import re
import sys
import subprocess
from collections import Counter

DRY = "--apply" not in sys.argv
ROOT = "/home/zany/f1-round2"

# README / LICENSE belong to another agent - never touch them.
OWNED_BY_OTHERS = {"README.md", "LICENSE", "LICENSE.md", "LICENSE.txt",
                   "COPYING", "COPYING.md", "CONTRIBUTING.md"}

files = [f for f in subprocess.run(
    ["git", "ls-files", "*.md", "*.txt"],
    cwd=ROOT, capture_output=True, text=True, check=True
).stdout.split() if f not in OWNED_BY_OTHERS]

# ---------------------------------------------------------------- identifiers
MACHINES = [8449, 8512, 31233, 34481, 36179, 43130, 44842, 46633, 52271,
            53711, 58073, 73811, 131197, 137580, 138180, 141468, 142281, 144732]
MACH_MAP = {str(n): "mach-%02d" % (i + 1) for i, n in enumerate(sorted(MACHINES))}

# every 8-digit number in the corpus EXCEPT these, which are real measurements
NOT_IDS = {"22945780",  # triangle count
           "64971343", "67679807",  # sha256 prefixes
           "99926553",  # tail of 0.99926553
           "20260802",  # a date
           "00000000"}  # padding

eight = set()
for f in files:
    with open(f"{ROOT}/{f}", encoding="utf-8") as fh:
        eight.update(re.findall(r"\b[0-9]{8}\b", fh.read()))
VAST_IDS = sorted(eight - NOT_IDS, key=int)
ID_MAP = {n: "id-%03d" % (i + 1) for i, n in enumerate(VAST_IDS)}

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

    # ---- H: rented-host identifiers -------------------------------------
    for ip, alias in IPS.items():
        text = sub(re.escape(ip) + r":21104", alias + ":PORT", text, "H/ip-port")
        text = sub(re.escape(ip), alias, text, "H/ip")

    # broker labels carry an epoch suffix unique to the account
    text = sub(r"\b(fleet[0-9]{2})-[0-9]{9,}\b", r"\1-LABEL", text, "H/label")

    # 8-digit vast instance / offer / container ids.  Guard against decimals
    # (0.99926553) and comma-grouped byte counts.
    def _id(m):
        return ID_MAP.get(m.group(0), m.group(0))
    text = sub(r"(?<![\d.])\b[0-9]{8}\b(?!\d)", _id, text, "H/vast-id")

    # machine ids: 4-6 digits, only the known set
    def _mach(m):
        return MACH_MAP.get(m.group(0), m.group(0))
    text = sub(r"(?<![\d.])\b(?:%s)\b(?!\d)" % "|".join(
        str(n) for n in sorted(MACHINES, key=lambda x: -x)),
        _mach, text, "H/machine-id")

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


changed = 0
for f in files:
    p = f"{ROOT}/{f}"
    with open(p, encoding="utf-8") as fh:
        old = fh.read()
    new = clean(old)
    if new != old:
        changed += 1
        if not DRY:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(new)

print("DRY RUN" if DRY else "APPLIED")
print(f"files changed: {changed} of {len(files)}")
print(f"distinct vast ids pseudonymised: {len(VAST_IDS)}")
print(f"distinct machine ids pseudonymised: {len(MACH_MAP)}")
for k, v in sorted(counts.items()):
    print(f"  {k:24s} {v}")
