"""Name every object that differs between two vertex fingerprints, field by field.

    python3 fp_object_detail.py OLD.json NEW.json [--all]

`fp_diff.py` answers "how many moved" and checks that count against a declared
expectation.  It deliberately does not say WHAT changed, and for a7 -> a8 that
detail had to be assembled by hand into SHIPPING.md.  A bbox that grew is a
different event from a bbox that held while the hash changed, and a vertex COUNT
that changed is a third thing again -- assembly9 is the first diff in this
project where one does.

Prints, per differing object: vertex count, the three bbox corners, the
coordinate sums, and which of those are BIT-IDENTICAL.  "bit-identical" is
meant literally -- the fingerprint stores 6 dp, and a field that reproduces to
all six is reported as unchanged rather than as a small number.
"""
import json
import sys


def load(p):
    return json.load(open(p))["rows"]


def fmt(a, b, name, unit="m"):
    if a == b:
        return "  %-10s %s   BIT-IDENTICAL" % (name, a)
    return "  %-10s %s -> %s   delta %+.6f %s" % (name, a, b, b - a, unit)


def main(argv):
    if len(argv) < 2:
        print("usage: fp_object_detail.py OLD.json NEW.json [--all]")
        return 2
    A, B = load(argv[0]), load(argv[1])
    show_all = "--all" in argv
    ka, kb = set(A), set(B)
    only_a, only_b = sorted(ka - kb), sorted(kb - ka)
    if only_a:
        print("ONLY IN OLD (%d): %s" % (len(only_a), only_a[:20]))
    if only_b:
        print("ONLY IN NEW (%d): %s" % (len(only_b), only_b[:20]))
    if not only_a and not only_b:
        print("name-set symmetric difference: 0")

    moved = sorted(k for k in (ka & kb) if A[k]["hash"] != B[k]["hash"])
    print("objects differing: %d of %d common" % (moved and len(moved) or 0,
                                                  len(ka & kb)))
    for k in moved if (show_all or len(moved) <= 25) else moved[:25]:
        a, b = A[k], B[k]
        print("\n--- %s" % k)
        if a["verts"] == b["verts"]:
            print("  verts      %d   UNCHANGED" % a["verts"])
        else:
            print("  verts      %d -> %d   %+d (%.3f %%)"
                  % (a["verts"], b["verts"], b["verts"] - a["verts"],
                     100.0 * (b["verts"] - a["verts"]) / a["verts"]))
        for i, ax in enumerate("xyz"):
            print(fmt(a["bbox_min"][i], b["bbox_min"][i], "bbox %s min" % ax))
            print(fmt(a["bbox_max"][i], b["bbox_max"][i], "bbox %s max" % ax))
        for i, ax in enumerate("xyz"):
            print(fmt(a["sum"][i], b["sum"][i], "sum %s" % ax))
        print(fmt(a["sumsq"], b["sumsq"], "sumsq", "m2"))
        print("  hash       %s -> %s" % (a["hash"], b["hash"]))
    print("\n>> STAGE RESULT: FP_OBJECT_DETAIL_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
