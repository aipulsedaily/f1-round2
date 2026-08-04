"""Does the repaired apron read as a fix in the film AS SHOT?

    .venv/bin/python work/r2148/f1104_ab.py BEFORE.png AFTER.png MASKS.npz [--diff OUT.png]

The one question the pit-exit work could not answer.  f1104 is the ONER's best
view of the region -- 71.50 m2 unoccluded of 427.60 -- at 17-34 deg line of
sight, so this is the most favourable frame the film has and not a cherry-picked
nadir.

Reports, per region: the fraction of pixels that changed at all, the fraction
that changed by more than 2/255 (above 8-bit dither), mean |delta| and mean RGB
before and after.  The VOID region is the claim; CTL_PAVED and CTL_SKY are the
floor.  A void number that does not stand clear of the controls is not a fix
showing up in the film -- it is two renders of the same frame disagreeing with
each other, and saying so is the finding.
"""
import sys

import numpy as np
from PIL import Image


def load(p):
    im = Image.open(p).convert("RGB")
    return np.asarray(im).astype(np.int16), im.size


def main(argv):
    before, after, masks = argv[0], argv[1], argv[2]
    A, sa = load(before)
    B, sb = load(after)
    if sa != sb:
        print("REFUSE: %s is %s and %s is %s" % (before, sa, after, sb))
        print(">> STAGE RESULT: F1104_AB_REFUSED_SIZE")
        return 3
    M = np.load(masks)
    W, H = int(M["res"][0]), int(M["res"][1])
    if (W, H) != sa:
        print("REFUSE: masks are for %dx%d, images are %dx%d -- the pixel sets "
              "would land somewhere else entirely" % (W, H, sa[0], sa[1]))
        print(">> STAGE RESULT: F1104_AB_REFUSED_RES")
        return 3

    Af, Bf = A.reshape(-1, 3), B.reshape(-1, 3)
    D = np.abs(Af.astype(np.int32) - Bf.astype(np.int32)).max(axis=1)

    print("images   %s  ->  %s   %dx%d" % (before, after, W, H))
    print("%-12s %9s %9s %9s %9s %10s   %s"
          % ("region", "px", "changed", ">2/255", ">8/255", "mean|d|",
             "mean RGB before -> after"))
    rows = {}
    for tag in ("void", "ctl_paved", "ctl_sky"):
        idx = M[tag]
        if not len(idx):
            print("%-12s (empty)" % tag)
            continue
        d = D[idx]
        a, b = Af[idx].mean(axis=0), Bf[idx].mean(axis=0)
        rows[tag] = dict(
            n=len(idx), changed=float((d > 0).mean()),
            gt2=float((d > 2).mean()), gt8=float((d > 8).mean()),
            mean=float(d.mean()),
            before=[round(float(x), 1) for x in a],
            after=[round(float(x), 1) for x in b])
        print("%-12s %9d %8.2f%% %8.2f%% %8.2f%% %10.3f   "
              "(%5.1f,%5.1f,%5.1f) -> (%5.1f,%5.1f,%5.1f)"
              % (tag, len(idx), 100 * rows[tag]["changed"],
                 100 * rows[tag]["gt2"], 100 * rows[tag]["gt8"],
                 rows[tag]["mean"], a[0], a[1], a[2], b[0], b[1], b[2]))

    whole = dict(n=D.size, changed=float((D > 0).mean()),
                 gt2=float((D > 2).mean()), gt8=float((D > 8).mean()),
                 mean=float(D.mean()))
    print("%-12s %9d %8.2f%% %8.2f%% %8.2f%% %10.3f"
          % ("WHOLE FRAME", whole["n"], 100 * whole["changed"],
             100 * whole["gt2"], 100 * whole["gt8"], whole["mean"]))

    if "--diff" in argv:
        out = argv[argv.index("--diff") + 1]
        g = np.clip(D.reshape(H, W) * 8, 0, 255).astype(np.uint8)
        Image.fromarray(np.dstack([g, g, g])).save(out)
        print("amplified (8x) difference image -> %s" % out)

    if "void" in rows and "ctl_paved" in rows:
        v, c = rows["void"]["gt8"], rows["ctl_paved"]["gt8"]
        print()
        print("THE COMPARISON, at the >8/255 threshold:")
        print("  void       %.2f %%" % (100 * v))
        print("  ctl_paved  %.2f %%   (ground built in BOTH builds)" % (100 * c))
        if c >= 0.02 and v < 3 * c:
            verdict = "F1104_AB_NO_CLEAR_DIFFERENCE"
            print("  the void region does NOT stand clear of the control. "
                  "On this frame the repair does not read.")
        elif v > max(3 * c, 0.05):
            verdict = "F1104_AB_VISIBLE"
            print("  the void region stands clear of the control by %.1fx. "
                  "The repair reads in the film as shot." % (v / max(c, 1e-9)))
        else:
            verdict = "F1104_AB_MARGINAL"
            print("  neither clear nor null. Report it as marginal, not as "
                  "whichever of the two is more convenient.")
        print(">> STAGE RESULT: %s" % verdict)
    else:
        print(">> STAGE RESULT: F1104_AB_INCOMPLETE")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
