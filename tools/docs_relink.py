#!/usr/bin/env python3
"""Re-derive the `#L<n>` anchors that documentation uses to point into
`docs/DEFECT-LOG-R2.md`.

WHY THIS EXISTS.  `docs/READING-LIST.md` is the document a newcomer is sent to
first, and every one of its ~111 links carries a hard line number into a
67,000-line append-only log.  The log is edited at the top as well as appended
to at the bottom, so a single inserted paragraph silently moves every anchor
below it.  Measured on 2026-08-18, **all 111 anchors were off by exactly +17**:
every link in the curated reading list landed seventeen lines short of the entry
it names.  Nothing failed, nothing warned, and the links still rendered.

That is this project's commonest defect wearing a different coat — a thing that
reads the same whether it is right or wrong — so it gets an instrument that can
fail rather than a note asking people to be careful.

    tools/docs_relink.py                 # --check: report drift, exit 1 if any
    tools/docs_relink.py --apply         # rewrite the anchors, then re-verify

WHAT IT WILL NOT DO.  It only rewrites the number after `#L` in a link whose
text names an entry id it can find in the log.  It never invents an anchor,
never touches a link to an entry the log does not contain, and refuses to write
if the result would not verify.  An entry that has moved to a staging file, or
that does not exist, is REPORTED — not silently dropped and not silently
repointed at something nearby.

Runs under plain CPython.  No Blender, no dependencies.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_REL = "docs/DEFECT-LOG-R2.md"

# Documents that carry anchors into the log.  Add to this list rather than
# globbing: a glob would quietly start rewriting a file nobody reviewed.
TARGETS = [
    "docs/READING-LIST.md",
]

# [`R2-012`](DEFECT-LOG-R2.md#L260) L260
#
# The trailing ` L260` is a VISIBLE label, and `READING-LIST.md` carries one
# after every single link.  It is matched and rewritten with the href, because a
# link that jumps to line 277 while the page still says "L260" is worse than one
# that is merely stale — the reader now has two numbers and no reason to prefer
# either.  The link text is deliberately permissive about material outside the
# backticks, so `[`R2-430` retracted](…)` is not silently skipped.
LINK_RE = re.compile(
    r"\[(?P<text>[^\]]*`(?P<eid>R2-\d+)[^`]*`[^\]]*)\]"
    r"\((?P<path>(?:docs/)?DEFECT-LOG-R2\.md)#L(?P<line>\d+)\)"
    r"(?P<label> L(?P<lline>\d+))?"
)
HEAD_RE = re.compile(r"^## (R2-\d+)")


def entry_lines(log_path: str) -> dict[str, int]:
    """id -> 1-based line of its FIRST `## R2-nnn` heading.

    First, not last: an entry can be corrected by a later block that repeats the
    heading, and a reader following a citation wants the original.
    """
    out: dict[str, int] = {}
    with open(log_path, encoding="utf-8", errors="replace") as fh:
        for n, line in enumerate(fh, 1):
            m = HEAD_RE.match(line)
            if m and m.group(1) not in out:
                out[m.group(1)] = n
    return out


def scan(text: str, pos: dict[str, int]):
    """-> (drifted, correct, unknown) lists of (eid, cited, actual)."""
    drifted, correct, unknown = [], [], []
    for m in LINK_RE.finditer(text):
        eid, cited = m.group("eid"), int(m.group("line"))
        label = int(m.group("lline")) if m.group("lline") else None
        actual = pos.get(eid)
        if actual is None:
            unknown.append((eid, cited, None, label))
        elif actual == cited and (label is None or label == actual):
            correct.append((eid, cited, actual, label))
        else:
            drifted.append((eid, cited, actual, label))
    return drifted, correct, unknown


def rewrite(text: str, pos: dict[str, int]) -> str:
    def sub(m: re.Match) -> str:
        actual = pos.get(m.group("eid"))
        if actual is None:
            return m.group(0)  # unknown entry: leave it exactly as found
        out = "[%s](%s#L%d)" % (m.group("text"), m.group("path"), actual)
        if m.group("label"):
            out += " L%d" % actual
        return out

    return LINK_RE.sub(sub, text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--apply", action="store_true",
                    help="rewrite the anchors (default is a read-only check)")
    args = ap.parse_args()

    log_path = os.path.join(REPO, LOG_REL)
    if not os.path.exists(log_path):
        print("MISSING: %s" % LOG_REL)
        print(">> STAGE RESULT: DOCS_RELINK_CRASH")
        return 2

    pos = entry_lines(log_path)
    print("log: %s, %d distinct entry headings" % (LOG_REL, len(pos)))

    total_drift = total_ok = total_unknown = 0
    for rel in TARGETS:
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            print("  %-28s MISSING" % rel)
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        drifted, correct, unknown = scan(text, pos)
        total_drift += len(drifted)
        total_ok += len(correct)
        total_unknown += len(unknown)

        print("  %-28s %d anchors: %d correct, %d drifted, %d unresolvable"
              % (rel, len(drifted) + len(correct) + len(unknown),
                 len(correct), len(drifted), len(unknown)))
        offsets = sorted({a - c for _, c, a, _lab in drifted})
        if offsets:
            print("      drift offsets present: %s"
                  % ", ".join("%+d" % o for o in offsets))
        for eid, cited, _actual, _lab in unknown:
            print("      UNRESOLVABLE %s cited at L%d — not a heading in the log"
                  % (eid, cited))
        for eid, cited, actual, lab in drifted[:5]:
            if cited == actual and lab is not None:
                print("      %s href L%d is right, VISIBLE LABEL says L%d"
                      % (eid, actual, lab))
            else:
                print("      %s cited L%d, actual L%d%s"
                      % (eid, cited, actual,
                         "" if lab in (None, cited) else " (label L%d)" % lab))
        if len(drifted) > 5:
            print("      … and %d more" % (len(drifted) - 5))

        if args.apply and drifted:
            new = rewrite(text, pos)
            d2, c2, u2 = scan(new, pos)
            if d2:
                print("      REFUSED to write: %d anchors still wrong after "
                      "rewrite" % len(d2))
                print(">> STAGE RESULT: DOCS_RELINK_CRASH")
                return 2
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
            print("      rewritten: %d anchors, %d now correct, %d left alone"
                  % (len(drifted), len(c2), len(u2)))

    if total_ok + total_drift + total_unknown == 0:
        # An empty scan reporting success is the exact failure this repository
        # is a catalogue of.  Refuse instead.
        print(">> STAGE RESULT: DOCS_RELINK_VACUOUS — 0 anchors examined")
        return 3

    if args.apply:
        print(">> STAGE RESULT: DOCS_RELINK_APPLIED")
        return 0
    if total_drift or total_unknown:
        print(">> STAGE RESULT: DOCS_RELINK_DRIFT")
        return 1
    print(">> STAGE RESULT: DOCS_RELINK_CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
