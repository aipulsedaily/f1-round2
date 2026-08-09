"""R2-3721 item 2: the OBJECT-level px/m diff -- the number agents build against.

    python3 objdelta.py BASE_sp_objects.json NEW_sp_objects.json --label L

WHY THIS AND NOT ONLY THE TIER. WAVE2-SCOPE.md sec 2.6's R2-634 re-derivation
already found, for a smaller camera swap than this one:

    TIER changed:                   1 of 560 objects
    peak sharp px/m moved > 10 %:  14 of 560 objects
    "TIER ASSIGNMENT IS ROBUST TO THE CAMERA. px_per_m IS NOT, AND px_per_m IS
     WHAT AGENTS ACTUALLY BUILD AGAINST."

So "no tier moved" is only half an answer. ITEM-CAMPAIGN-BRIEF sec 3 makes the
detail budget a function of px/m -- an item authored for 477 px/m and filmed at
1224 px/m is built to a quarter of the resolution it needs -- and that error is
invisible to a tier count. This prints the same two statistics R2-634 printed,
on the same field, so the two findings are directly comparable.
"""
import argparse
import json
import math


def load(p):
    d = json.load(open(p))
    return {r["object"]: r for r in d["objects"]}, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("new")
    ap.add_argument("--label", default="")
    ap.add_argument("--key", default="peak_unocc_sharp_px_per_m")
    ap.add_argument("--top", type=int, default=25)
    a = ap.parse_args()
    base, bd = load(a.base)
    new, nd = load(a.new)
    ids = sorted(set(base) & set(new))

    print("=" * 96)
    print("OBJECT px/m DELTA  %s" % a.label)
    print("  base camera %s" % bd.get("camera_path"))
    print("  new  camera %s" % nd.get("camera_path"))
    print("  world       %s" % (bd.get("point_cloud", {}).get("blend")))
    print("  common objects %d  (base %d, new %d)" % (len(ids), len(base), len(new)))

    rows = []
    for i in ids:
        ob = float(base[i].get(a.key) or 0.0)
        on = float(new[i].get(a.key) or 0.0)
        if ob <= 0 and on <= 0:
            continue
        rel = (on - ob) / ob if ob > 0 else float("inf")
        l2 = (math.log2(on / ob) if ob > 0 and on > 0 else float("nan"))
        rows.append((abs(rel), rel, l2, i, ob, on))
    n10 = sum(1 for r in rows if abs(r[1]) > 0.10)
    n2x = sum(1 for r in rows if not math.isnan(r[2]) and abs(r[2]) >= 1.0)
    zero = [r for r in rows if r[4] > 0 and r[5] == 0.0]
    born = [r for r in rows if r[4] == 0.0 and r[5] > 0]
    print("\n  %s" % a.key)
    print("    objects with the field nonzero in either arm : %d" % len(rows))
    print("    moved > 10 %%                                 : %d" % n10)
    print("    moved by 2x or more                          : %d" % n2x)
    print("    lost it entirely (was > 0, now 0)            : %d" % len(zero))
    print("    gained it (was 0, now > 0)                   : %d" % len(born))
    fin = [r for r in rows if not math.isnan(r[2])]
    if fin:
        ls = sorted(abs(r[2]) for r in fin)
        print("    |log2 ratio|  p50 %.3f  p90 %.3f  max %.3f"
              % (ls[len(ls) // 2], ls[int(0.9 * len(ls))], ls[-1]))
    rows.sort(reverse=True)
    print("\n    %-40s %10s %10s %9s" % ("object", "base px/m", "new px/m", "change"))
    for _, rel, l2, i, ob, on in rows[:a.top]:
        print("    %-40s %10.1f %10.1f %+8.0f %%"
              % (i, ob, on, 100 * rel if math.isfinite(rel) else 9999))
    print(">> STAGE RESULT: OBJ_PXM_DELTA moved10=%d moved2x=%d of %d"
          % (n10, n2x, len(rows)))


main()
