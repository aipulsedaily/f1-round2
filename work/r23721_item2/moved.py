"""R2-3721 item 2: WHICH BEAT-1 NUMBERS MOVED, and by how much, tier or no tier.

    python3 moved.py BASE_item_presence.json NEW_item_presence.json [--label L]

tier_delta.py answers "did the tier change". That is a THRESHOLDED question and
a threshold hides everything that moves without crossing it. This prints the
continuous quantities the tier rule is actually built out of --

    frames_at_300px   (>= 24 makes HERO)
    frames_at_150px   (>= 12 makes MID)
    peak_unocc_sharp_px_4k

-- ranked by movement, and separately for items whose peak is INSIDE beat 1,
because beat 1 is the span the camera change is concentrated in and "the
tiering barely moves" would be a different claim if beat 1's numbers were
stable than if they moved violently and happened to land the same side of a
threshold. The DISTANCE TO THE NEAREST THRESHOLD is printed for the biggest
movers, because an item that went 22 -> 23 frames at 300 px did not change tier
and is one frame from doing so, and that is worth knowing before the master.
"""
import argparse
import json
import os

R2 = os.path.expanduser("~/f1-round2")


def load(p):
    d = json.load(open(p))
    return {r["id"]: r for r in d["items"]}, d


def beat1_last():
    d = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))
    b = d["beats"][0]
    return int(round((b["start_s"] + b["duration_s"]) * 24))


def g(r, k):
    m = r.get("measured")
    return (m or {}).get(k, 0) or 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("new")
    ap.add_argument("--label", default="")
    ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args()
    B1 = beat1_last()
    base, bd = load(a.base)
    new, nd = load(a.new)
    ids = sorted(set(base) & set(new))

    print("=" * 100)
    print("BEAT-1 NUMBERS  %s" % a.label)
    print("  base %s" % os.path.basename(a.base))
    print("  new  %s" % os.path.basename(a.new))
    print("  beat 1 = f1..f%d" % B1)

    # which items live in beat 1 at all: any host visible during beat 1
    def in_b1(r):
        m = r.get("measured") or {}
        bts = m.get("beats") or {}
        return any(k.startswith("1_") for k in bts)

    b1ids = [i for i in ids if in_b1(base[i]) or in_b1(new[i])]
    print("  items with any beat-1 presence: %d of %d" % (len(b1ids), len(ids)))

    for key, thr, tier in (("frames_at_300px", 24, "HERO"),
                           ("frames_at_150px", 12, "MID")):
        rows = []
        for i in b1ids:
            ob, on = g(base[i], key), g(new[i], key)
            if ob == on:
                continue
            rows.append((abs(on - ob), i, ob, on))
        rows.sort(reverse=True)
        nz = len(rows)
        print("\n  %-16s (>= %d => %s)   %d of %d beat-1 items moved at all"
              % (key, thr, tier, nz, len(b1ids)))
        print("    %-34s %8s %8s %9s   %s"
              % ("item", "base", "new", "delta", "threshold crossing"))
        for _, i, ob, on in rows[:a.top]:
            cross = ""
            if (ob >= thr) != (on >= thr):
                cross = "**CROSSES %s** %s" % (thr, "up" if on >= thr else "down")
            elif abs(on - thr) <= 3 or abs(ob - thr) <= 3:
                cross = "within 3 of the %s line" % thr
            print("    %-34s %8d %8d %+9d   %s" % (i, ob, on, on - ob, cross))

    key = "peak_unocc_sharp_px_4k"
    rows = []
    for i in b1ids:
        ob, on = float(g(base[i], key)), float(g(new[i], key))
        if abs(on - ob) < 1e-9:
            continue
        rel = abs(on - ob) / max(ob, on, 1e-6)
        rows.append((rel, abs(on - ob), i, ob, on))
    rows.sort(reverse=True)
    print("\n  %s   %d of %d beat-1 items moved at all"
          % (key, len(rows), len(b1ids)))
    print("    %-34s %10s %10s %9s  %s" % ("item", "base px", "new px", "delta", "rel"))
    for rel, _, i, ob, on in rows[:a.top]:
        print("    %-34s %10.1f %10.1f %+9.1f  %5.0f %%"
              % (i, ob, on, on - ob, 100 * rel))

    # HOW CLOSE IS THE TIERING TO MOVING AT ALL -- the fragility number
    near = []
    for i in ids:
        for key, thr in (("frames_at_300px", 24), ("frames_at_150px", 12)):
            ob, on = g(base[i], key), g(new[i], key)
            if min(abs(ob - thr), abs(on - thr)) <= 2:
                near.append((i, key, thr, ob, on))
    print("\n  ITEMS SITTING WITHIN 2 FRAMES OF A TIER LINE IN EITHER ARM: %d"
          % len(near))
    for i, key, thr, ob, on in sorted(near):
        print("    %-34s %-16s line %2d   base %3d  new %3d" % (i, key, thr, ob, on))
    print(">> STAGE RESULT: MOVED_REPORTED label=%r near_lines=%d"
          % (a.label, len(near)))


main()
