"""R2-3721 item 2: was anything BUILT that shouldn't have been, or SKIPPED that
should have been built -- decided against the DELIVERED camera, not the orphan.

    python3 builtcheck.py BASE_item_presence.json NEW_item_presence.json

The wave-2 build set is defined in docs/WAVE2-SCOPE.md sec 3.1 as the UNBUILT
items measured HERO (W2-A) or MID (W2-B); BULK gets a class-level pass and no
module (W2-D), and 24 BULK items with >= 2 dependants get an interface stub
(W2-C). BUILT is read the way work/w2_0/tier_delta.py reads it and the way
WAVE2-SCOPE sec 1.1 defines it: a world/items/*.py whose FILENAME is a manifest
item id. Never typed here.

Four questions, and each is answered from the tier under the DELIVERED camera:

  1. BUILT and BULK under the delivered camera -- a dedicated module exists for
     something the delivered film never resolves. "Built that shouldn't have
     been" in the strong sense.
  2. BUILT and BULK under the delivered camera BUT HERO/MID under the orphan --
     the subset of (1) the camera defect can be blamed for.
  3. UNBUILT and HERO/MID under the delivered camera -- the wave-2 build set as
     it should have been.
  4. The subset of (3) that the orphan camera hid: BULK under the orphan and
     HERO/MID under the delivered camera. "Skipped that should have been built"
     and attributable to the defect.
"""
import json
import os
import sys

R2 = os.path.expanduser("~/f1-round2")


def built_ids():
    man = json.load(open(os.path.join(R2, "docs/item_manifest.json")))
    rows = man["items"] if isinstance(man, dict) else man
    ids = {r["id"] for r in rows}
    d = os.path.join(R2, "world/items")
    stems = {f[:-3] for f in os.listdir(d) if f.endswith(".py")}
    return ids & stems


def load(p):
    d = json.load(open(p))
    return {r["id"]: r for r in d["items"]}


def px(r):
    return (r.get("measured") or {}).get("peak_unocc_sharp_px_4k", 0) or 0


def main():
    base, new = load(sys.argv[1]), load(sys.argv[2])
    B = built_ids()
    print("BUILT item modules: %d   manifest items: %d" % (len(B), len(new)))

    def T(c, i):
        return c[i]["proposed_tier"]

    def row(i):
        return ("      %-32s orphan %-5s delivered %-5s  %8.1f -> %8.1f px  %s"
                % (i, T(base, i), T(new, i), px(base[i]), px(new[i]),
                   new[i]["zone"]))

    q1 = sorted(i for i in B if T(new, i) == "BULK")
    print("\n1. BUILT, and BULK under the DELIVERED camera: %d of %d built"
          % (len(q1), len(B)))
    for i in q1:
        print(row(i))

    q2 = [i for i in q1 if T(base, i) in ("HERO", "MID")]
    print("\n2.   ...of which the ORPHAN camera called HERO or MID -- i.e. built "
          "on a tier the delivered camera does not support: %d" % len(q2))
    for i in q2:
        print(row(i))

    q3 = sorted(i for i in new if i not in B and T(new, i) in ("HERO", "MID"))
    print("\n3. UNBUILT and HERO/MID under the DELIVERED camera (the wave-2 "
          "build set as it should be): %d" % len(q3))
    print("      HERO %d   MID %d"
          % (sum(1 for i in q3 if T(new, i) == "HERO"),
             sum(1 for i in q3 if T(new, i) == "MID")))

    q4 = sorted(i for i in q3 if T(base, i) == "BULK")
    print("\n4.   ...of which the ORPHAN camera called BULK, so they were never "
          "in the build set at all: %d" % len(q4))
    for i in q4:
        print(row(i))

    q5 = sorted(i for i in new if i not in B and T(base, i) in ("HERO", "MID")
                and T(new, i) == "BULK")
    print("\n5. UNBUILT, in the build set under the ORPHAN, and BULK under the "
          "DELIVERED camera -- work that would have been wasted: %d" % len(q5))
    for i in q5:
        print(row(i))

    q6 = sorted(i for i in new if i not in B and T(base, i) == "MID"
                and T(new, i) == "HERO")
    q7 = sorted(i for i in new if i not in B and T(base, i) == "HERO"
                and T(new, i) == "MID")
    print("\n6. UNBUILT, MID -> HERO (needs macro history it was not budgeted "
          "for): %d" % len(q6))
    for i in q6:
        print(row(i))
    print("\n7. UNBUILT, HERO -> MID (budgeted macro history it does not need): "
          "%d" % len(q7))
    for i in q7:
        print(row(i))

    print("\n>> STAGE RESULT: BUILTCHECK built_bulk=%d built_demoted=%d "
          "should_build_new=%d would_be_wasted=%d mid_to_hero=%d hero_to_mid=%d"
          % (len(q1), len(q2), len(q4), len(q5), len(q6), len(q7)))


main()
