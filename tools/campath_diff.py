"""Path A vs path B, with the R2-103 rounding floor handled and the self-null first.

The stored quaternions are rounded to six decimals, so `2*acos(|dot|)` on a file
against a BIT-IDENTICAL copy of itself does not return zero: it returns 0.203 deg,
because |q| is off unit by ~8e-7 and acos amplifies that by a square root. Every
angle here is therefore taken on RE-NORMALISED, sign-normalised quaternions, and
the self-null is printed first so the floor is visible before any verdict.
"""
import json, math, sys

def load(p):
    return {e["f"]: e for e in json.load(open(p))["path"]}

def ang(qa, qb, renorm=True):
    if renorm:
        na = math.sqrt(sum(x*x for x in qa)) or 1.0
        nb = math.sqrt(sum(x*x for x in qb)) or 1.0
        qa = [x/na for x in qa]; qb = [x/nb for x in qb]
    d = sum(qa[i]*qb[i] for i in range(4))
    return 2.0*math.degrees(math.acos(max(-1.0, min(1.0, abs(d)))))

def diff(a, b, lo, hi, renorm=True):
    wp = wq = wl = 0.0; fp = fq = fl = 0; n = 0
    for f in sorted(a):
        if f < lo or f > hi or f not in b: continue
        n += 1
        d = max(abs(a[f]["p"][i]-b[f]["p"][i]) for i in range(3))
        if d > wp: wp, fp = d, f
        q = ang(a[f]["q"], b[f]["q"], renorm)
        if q > wq: wq, fq = q, f
        l = abs(a[f]["lens"]-b[f]["lens"])
        if l > wl: wl, fl = l, f
    return n, wp, fp, wq, fq, wl, fl

A, B = sys.argv[1], sys.argv[2]
a, b = load(A), load(B)
print("SELF-NULL  %s vs itself" % A.split("/")[-1])
for rn, nm in ((False, "raw stored q  (the R2-103 trap)"), (True, "re-normalised q")):
    n, wp, fp, wq, fq, wl, fl = diff(a, a, 1, 10**9, rn)
    print("   %-32s frames %4d  dp %.6g m  dq %.6f deg  dlens %.6g mm"
          % (nm, n, wp, wq, wl))
print("\nA=%s   B=%s" % (A.split("/")[-1], B.split("/")[-1]))
for lo, hi, nm in ((1, 792, "beat 1        f1-792"),
                   (1, 590, "  presentations f1-590"),
                   (591, 647, "  CORNER_FL+close f591-647"),
                   (648, 792, "  PROTECTED     f648-792"),
                   (793, 2978, "beats 2-6     f793-2978")):
    n, wp, fp, wq, fq, wl, fl = diff(a, b, lo, hi)
    print("   %-28s frames %4d  worst dp %8.4f m @f%-5d  dq %7.3f deg @f%-5d  dlens %.4g mm"
          % (nm, n, wp, fp, wq, fq, wl))
print("STAGE RESULT OK")
