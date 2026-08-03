"""Diff two assembleN_build.json module reports, field by field.

    python3 work/r2100/build_json_diff.py OLD.json NEW.json

SHIPPING.md's own warning applies to this file more than to any other: every
module summary in assembly5 and assembly6 was BIT-IDENTICAL while one object
had moved 3.19 m. So this is NOT evidence about geometry -- it is the
complement of the vertex fingerprint. It answers "did any module report a
different count, area or total", which is the only question it can answer, and
the wall-clock timings are separated out because they are expected to differ
and are not findings.
"""
import json
import sys

a = json.load(open(sys.argv[1]))
b = json.load(open(sys.argv[2]))


def flat(d, p=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flat(v, p + "/" + str(k)))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.update(flat(v, p + "[%d]" % i))
    else:
        out[p] = d
    return out


fa, fb = flat(a), flat(b)
TIMING = ("/build_s",)
keys = sorted(set(fa) | set(fb))
real, timing, path = [], [], []
for k in keys:
    if fa.get(k) == fb.get(k):
        continue
    if k.endswith("/s") or k.endswith("/build_s") or k in TIMING:
        timing.append(k)
    elif "blend" in k or k.endswith("/path"):
        path.append(k)
    else:
        real.append(k)

print("fields compared: %d" % len(keys))
print("WALL-CLOCK ONLY (expected to differ, not findings): %d" % len(timing))
for k in timing:
    print("   %-40s %s -> %s" % (k, fa.get(k), fb.get(k)))
print("OUTPUT PATH / SIZE: %d" % len(path))
for k in path:
    print("   %-40s %s -> %s" % (k, fa.get(k), fb.get(k)))
print("SUBSTANTIVE DIFFERENCES: %d" % len(real))
for k in real:
    print("   %-40s %r -> %r" % (k, fa.get(k), fb.get(k)))
print("STAGE RESULT: %s"
      % ("BUILD_REPORTS_IDENTICAL_APART_FROM_TIMING_AND_PATH" if not real
         else "BUILD_REPORTS_DIFFER"))
