#!/usr/bin/env python3
"""
R2-3901 — the orphan ledger.

WHY THIS EXISTS
---------------
Each 12-hour retirement drops the frame that was in flight. Whether that frame
is ever rendered again depends on which recovery path the broker took:

  * a **transport-only** failure resumes the SAME in-memory todo list, which
    never contained the lost frame -> the frame is orphaned PERMANENTLY;
  * a **deploy** failure requeues the JOB, which recomputes the todo from the
    files on disk -> the frame comes back on its own.

So a sequence job's own `COMPLETE` line is not coverage: it completes against
its own todo list. This tool reconstructs, from each broker's log, exactly which
frames were skipped and never came back, and prints the set that a re-submission
of `master4k` must therefore render.

THE TEST IT SETS UP
-------------------
At re-submission time the broker prints

    sequence master4k job <id>: 2978 frame(s) requested, N already delivered,
                                K to render

`K` must equal this tool's `PREDICTED` count.

  * K  > predicted -> something is dropping frames that this model does not
                      explain. STOP; do not encode.
  * K  < predicted -> the gap reader is wrong. STOP; do not encode.
  * K == predicted -> the model is confirmed and the re-render is the known
                      recovery of known casualties.

Reads only. Touches nothing.
"""

import os
import re
import sys
import json

VR = os.path.expanduser("~/vast-render")
NAME = "master4k"
FIRST, LAST = 1, 2978

# broker index -> (out dir, state dir). Blocks are discovered, not assumed.
BROKERS = [3, 4, 5]

RE_PLAN = re.compile(
    r"sequence " + NAME + r" job ([0-9a-f]+): (\d+) frame\(s\) requested, "
    r"(\d+) already delivered, (\d+) to render"
)
RE_DONE = re.compile(
    r"sequence " + NAME + r" frame (\d+) done \((\d+)/(\d+)\)"
)
RE_CANCEL = re.compile(r"sequence " + NAME + r" job ([0-9a-f]+) canceled")
RE_COMPLETE = re.compile(r"sequence " + NAME + r" job ([0-9a-f]+) COMPLETE")


def frames_on_disk():
    """Every master4k frame number present as a real .png, across all brokers."""
    have = {}
    for b in BROKERS:
        d = os.path.join(VR, "out%d" % b, "seq", NAME)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if not f.endswith(".png"):
                continue
            m = re.search(r"(\d+)\.png$", f)
            if not m:
                continue
            n = int(m.group(1))
            path = os.path.join(d, f)
            try:
                if os.path.getsize(path) == 0:
                    continue          # a zero-byte file is not a delivered frame
            except OSError:
                continue
            have.setdefault(n, []).append(b)
    return have


def read_log(b):
    """Ordered (job, frame) delivery stream plus the plan lines, for broker b."""
    p = os.path.join(VR, "state%d" % b, "broker.log")
    jobs = []          # [{id, requested, delivered, todo, frames: [...]}]
    cur = None
    if not os.path.exists(p):
        return jobs
    with open(p, "r", errors="replace") as fh:
        for line in fh:
            m = RE_PLAN.search(line)
            if m:
                cur = {
                    "id": m.group(1),
                    "requested": int(m.group(2)),
                    "delivered": int(m.group(3)),
                    "todo": int(m.group(4)),
                    "frames": [],
                    "complete": False,
                    "canceled": False,
                }
                jobs.append(cur)
                continue
            m = RE_DONE.search(line)
            if m and cur is not None:
                cur["frames"].append(int(m.group(1)))
                continue
            m = RE_CANCEL.search(line)
            if m:
                for j in jobs:
                    if j["id"] == m.group(1):
                        j["canceled"] = True
                continue
            m = RE_COMPLETE.search(line)
            if m:
                for j in jobs:
                    if j["id"] == m.group(1):
                        j["complete"] = True
    return jobs


def main():
    have = frames_on_disk()
    disk = set(have)

    dupes = sorted(n for n, bs in have.items() if len(bs) > 1)
    outside = sorted(n for n in disk if n < FIRST or n > LAST)

    print("=" * 74)
    print("ORPHAN LEDGER for sequence %r   (%d-%d)" % (NAME, FIRST, LAST))
    print("=" * 74)
    print("frames on disk           %d / %d" % (len(disk), LAST - FIRST + 1))
    if dupes:
        print("!! delivered by >1 broker %s" % dupes[:20])
    if outside:
        print("!! outside the range      %s" % outside[:20])

    all_orphans = set()
    per_broker = {}

    for b in BROKERS:
        jobs = [j for j in read_log(b) if j["frames"] or j["todo"]]
        if not jobs:
            continue
        live = jobs[-1]                      # the job actually running now
        stream = live["frames"]
        if not stream:
            # A job requeued but not yet delivering. It has no cursor and can
            # orphan nothing: its todo was just recomputed from disk, so every
            # frame absent from its block is back ON the list. This is the state
            # that recovers a broker's earlier casualties.
            per_broker[b] = {
                "cursor": "requeued",
                "orphans": [],
                "job": live["id"],
                "plan_lines": len(jobs),
                "requeued": True,
                "complete": live["complete"],
                "todo": live["todo"],
                "done_in_pass": 0,
            }
            continue

        lo, cursor = min(stream), max(stream)

        # Frames this job's own delivery stream skipped over. A skip that IS on
        # disk was delivered by an earlier pass (fine). A skip that is NOT on
        # disk was dropped in flight and is on no todo list anywhere.
        skipped = [n for n in range(lo, cursor + 1)
                   if n not in disk and n not in set(stream)]

        # A job that was requeued recomputes from disk, so anything it skipped
        # below its own start was already delivered. Only report real absences.
        orphans = sorted(skipped)
        all_orphans.update(orphans)
        per_broker[b] = {
            "cursor": cursor,
            "orphans": orphans,
            "job": live["id"],
            "plan_lines": len(read_log(b)),
            "requeued": len([j for j in read_log(b) if not j["canceled"]]) > 1,
            "complete": live["complete"],
            "todo": live["todo"],
            "done_in_pass": len(stream),
        }

    print()
    print("%-9s %-14s %8s %9s %8s  %s" %
          ("broker", "live job", "cursor", "done/todo", "plans", "orphans"))
    print("-" * 74)
    for b in BROKERS:
        d = per_broker.get(b)
        if not d:
            print("%-9s %-14s %8s" % ("fleet%02d" % b, "-", "no job"))
            continue
        print("%-9s %-14s %8s %4d/%-4d %8d  %s" % (
            "fleet%02d" % b, d["job"], d["cursor"],
            d["done_in_pass"], d["todo"], d.get("plan_lines", 0),
            d["orphans"] or "none"))

    # Everything still absent, split into "will be rendered by the running
    # fleet" and "will not be, because it is on no todo list".
    absent = sorted(set(range(FIRST, LAST + 1)) - disk)
    not_yet = sorted(set(absent) - all_orphans)

    print()
    print("ORPHANED (on no todo list, only a re-submission recovers these):")
    print("    %s" % (sorted(all_orphans) or "none"))
    print("    count = %d" % len(all_orphans))
    print()
    print("NOT YET RENDERED (the running fleet still owes these): %d" % len(not_yet))
    print()
    print("PREDICTED 'to render' ON RE-SUBMISSION = %d" % len(absent))
    print("    = %d orphaned + %d not yet rendered" % (len(all_orphans), len(not_yet)))
    print()
    print("At re-submission the broker's own plan line must read")
    print("    2978 frame(s) requested, %d already delivered, %d to render"
          % (len(disk), len(absent)))
    print("A DIFFERENT NUMBER MEANS STOP, NOT ADJUST.")

    if "--json" in sys.argv:
        out = {
            "on_disk": len(disk),
            "orphans": sorted(all_orphans),
            "not_yet": len(not_yet),
            "predicted_to_render": len(absent),
            "per_broker": {str(k): v for k, v in per_broker.items()},
            "duplicated": dupes,
            "outside_range": outside,
        }
        path = os.path.expanduser("~/f1-round2/work/r23901/orphan_ledger.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump(out, fh, indent=2)
        print("\nwrote %s" % path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
