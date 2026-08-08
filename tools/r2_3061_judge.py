"""R2-3061: JUDGE THE NEAR-FIELD RIG'S FRAMES ON THE INSTRUMENT THAT FOUND THE DEFECT.

    .venv/bin/python tools/r2_3061_judge.py --dir <4K png dir> \
        --probe <tile classification json> [--label BEFORE]

It does not build a second instrument. `tools/r2_2881_pixelpeep.py` is imported
and its `pyramid`, `lum_of`, `Gates.TILE_COARSE` and 12-proxy-px tile erosion are
used exactly as `confirm4k` uses them, so a number here and a number in
`work/r22881/findings.json` mean the same thing. The one thing added is the join
to WHICH SURFACE each tile is on, from the ray probe, because "the asphalt is
blank" is a claim about the asphalt and 19 of the 144 tiles on these frames are
not asphalt at all.

THE PAIR IT REPORTS
-------------------
Frames f and f + 3000 are the same camera pose; f is on the film's moving path
with the 180-degree shutter open and f + 3000 is held still. So:

    still  -- what the MATERIAL delivers at the film's own sampling
    live   -- what the AUDIENCE receives after the shutter

and their ratio is the shutter's share of the defect, measured rather than
argued. Neither number alone can separate a blank material from an erased one.
"""
import argparse
import json
import os
import sys

import numpy as np

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "tools"))
sys.path.insert(0, R2)

import r2_2881_pixelpeep as PP                      # noqa: E402

STILL_OFFSET = 3000
TW4 = PP.TW * PP.UPSCALE
TH4 = PP.TH * PP.UPSCALE
M4 = PP.TILE_MARGIN * PP.UPSCALE


def bands_4k(png):
    """(coarse, fine, mean) per tile, natively at 3840x2160.

    Levels 4..5 of a 6-level pyramid on the native frame ARE 16-64 px at 4K --
    the same physical band the proxy reads at its own L2..L3. `confirm4k` in
    the instrument does exactly this; the construction is copied, not re-derived.
    """
    from PIL import Image
    a = np.asarray(Image.open(png).convert("RGB"), np.float32) / 255.0
    lum = PP.lum_of(a)
    lev = PP.pyramid(lum, 6)

    def tm(x):
        b = x.reshape(PP.TY, TH4, PP.TX, TW4)[:, M4:TH4 - M4, :, M4:TW4 - M4]
        return b.mean(axis=(1, 3))

    c = np.stack([tm(l) for l in lev])
    return c[4:6].mean(axis=0), c[0:2].mean(axis=0), tm(lum)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--probe", required=True)
    ap.add_argument("--label", default="")
    ap.add_argument("--pattern", default="%s_%06d.png")
    ap.add_argument("--seq", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    kindmap = {}
    smearmap = {}
    gsdmap = {}
    for r in json.load(open(a.probe))["rows"]:
        kindmap[(r["f"], r["r"], r["c"])] = r["kind"]
        smearmap[(r["f"], r["r"], r["c"])] = r["smear_px"]
        gsdmap[(r["f"], r["r"], r["c"])] = r["gsd_mm"]

    pngs = {}
    for fn in sorted(os.listdir(a.dir)):
        if not fn.endswith(".png"):
            continue
        digits = "".join(ch for ch in fn if ch.isdigit())
        try:
            f = int(digits[-6:])
        except ValueError:
            continue
        pngs[f] = os.path.join(a.dir, fn)
    if not pngs:
        raise SystemExit("no PNGs in " + a.dir)

    G = PP.Gates()
    res = {}
    for f in sorted(pngs):
        coarse, fine, mean = bands_4k(pngs[f])
        res[f] = (coarse, fine, mean)

    print("\n=== R2-3061 near-field rig %s ===" % (a.label or ""))
    print("threshold: a tile is EMPTY below coarse %.4f (r2_2881_pixelpeep "
          "Gates.TILE_COARSE, calibrated on a flattened tile at 0.00143 and "
          "9.6x below that tile intact)" % G.TILE_COARSE)
    print("\n%6s %-6s %6s %10s %10s %10s %8s %8s"
          % ("frame", "arm", "tiles", "coarse med", "coarse p25", "fine med",
             "mean", "empty"))
    rows = []
    for f in sorted(pngs):
        base = f - STILL_OFFSET if f - STILL_OFFSET in pngs or f > 3000 else f
        arm = "still" if f > 3000 else "live"
        coarse, fine, mean = res[f]
        sel = np.zeros((PP.TY, PP.TX), bool)
        for r in range(PP.TY):
            for c in range(PP.TX):
                if kindmap.get((base, r, c)) == "ASPHALT":
                    sel[r, c] = True
        if not sel.any():
            print("%6d %-6s   NO ASPHALT TILES CLASSIFIED (probe missing f%d)"
                  % (f, arm, base))
            continue
        cb, fb, mb = coarse[sel], fine[sel], mean[sel]
        print("%6d %-6s %6d %10.5f %10.5f %10.5f %8.3f %8d"
              % (f, arm, int(sel.sum()), float(np.median(cb)),
                 float(np.percentile(cb, 25)), float(np.median(fb)),
                 float(np.median(mb)), int((cb < G.TILE_COARSE).sum())))
        rows.append(dict(frame=f, base=base, arm=arm, n=int(sel.sum()),
                         coarse_med=float(np.median(cb)),
                         coarse_p25=float(np.percentile(cb, 25)),
                         fine_med=float(np.median(fb)),
                         mean_med=float(np.median(mb)),
                         empty=int((cb < G.TILE_COARSE).sum())))

    print("\n--- the shutter's share, per pose (still / live on the SAME view) ---")
    for f in sorted(pngs):
        if f > 3000:
            continue
        s = f + STILL_OFFSET
        if s not in res:
            continue
        rl = [r for r in rows if r["frame"] == f]
        rs = [r for r in rows if r["frame"] == s]
        if not rl or not rs:
            continue
        print("   f%-5d  still %.5f   live %.5f   the shutter removes %.2fx"
              % (f, rs[0]["coarse_med"], rl[0]["coarse_med"],
                 rs[0]["coarse_med"] / max(rl[0]["coarse_med"], 1e-9)))

    # THE FINDING'S OWN TILE, named rather than averaged
    print("\n--- the finding's own tile, f1787 (3,1) ---")
    for f, arm in ((1787, "live"), (4787, "still")):
        if f in res:
            print("   %-5s coarse %.5f   fine %.5f   mean %.3f"
                  % (arm, float(res[f][0][3, 1]), float(res[f][1][3, 1]),
                     float(res[f][2][3, 1])))
    if a.out:
        json.dump(rows, open(a.out, "w"), indent=1)
        print("\n>> wrote %s" % a.out)
    print(">> STAGE RESULT: JUDGE_OK")


main()
