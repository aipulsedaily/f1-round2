"""Frame-to-frame image change across beat 1 — the instrument for "too slow".

R2-823 measured beat 1's energy curve as INVERTED: 20.27 mean absolute
frame-to-frame luminance change across the unreadable tour against 4.89 across
the readable payoff, a 4.14x collapse exactly where the subject finally appears.
That is the mechanism behind the client's "way too slow I feel", and it is the
thing R2-830/831/833 were built to fix. This is what says whether they did.

WHY THIS FILE EXISTS AT ALL. R2-823's numbers were quoted with no tool beside
them, and two other beat-1 figures in this project turned out to have come from
instruments that do not measure beat 1 (`lap_shotscale.py`, which prints
"car exploded; not measured") or that are unreliable over a quarter of it
(`beat1_true_extent.py`). So this reproduces R2-823 on the SAME frames first and
refuses to report a comparison until it does. An instrument that cannot recover a
known result is not evidence about a new one.

    python3 tools/beat1_energy.py --selftest
    python3 tools/beat1_energy.py --before <dir> --after <dir>

Luminance is Rec.709 on the delivered PNGs, downscaled to 160x90 by ffmpeg so the
measure is of the PICTURE moving rather than of per-pixel sampling noise, and on
a 0-255 scale to match the published figures.
"""
import argparse
import os
import subprocess
import sys

import numpy as np

W, H = 160, 90


def luma_series(seq_dir, pattern=None):
    """-> (n_frames, H, W) uint8 luminance, via one ffmpeg decode."""
    if pattern is None:
        pngs = sorted(f for f in os.listdir(seq_dir) if f.endswith(".png"))
        if not pngs:
            raise SystemExit("no PNGs in %s" % seq_dir)
        stem = pngs[0].rsplit("_", 1)[0]
        digits = len(pngs[0].rsplit("_", 1)[1].split(".")[0])
        pattern = os.path.join(seq_dir, "%s_%%0%dd.png" % (stem, digits))
        start = int(pngs[0].rsplit("_", 1)[1].split(".")[0])
    else:
        start = 1
    cmd = ["ffmpeg", "-v", "error", "-start_number", str(start),
           "-i", pattern, "-vf", "scale=%d:%d" % (W, H),
           "-pix_fmt", "gray", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout
    n = len(raw) // (W * H)
    if n == 0:
        raise SystemExit("ffmpeg decoded 0 frames from %s" % pattern)
    return np.frombuffer(raw[:n * W * H], dtype=np.uint8).reshape(n, H, W)


def deltas(lum):
    """Mean absolute frame-to-frame change, one value per adjacent PAIR."""
    a = lum.astype(np.int16)
    return np.abs(np.diff(a, axis=0)).mean(axis=(1, 2))


def stats(d, lo_s, hi_s, fps=24.0):
    """Stats over pairs whose FIRST frame falls in [lo_s, hi_s)."""
    i0, i1 = int(round(lo_s * fps)), int(round(hi_s * fps))
    seg = d[max(i0, 0):min(i1, len(d))]
    if not len(seg):
        return 0, float("nan"), float("nan")
    return len(seg), float(seg.mean()), float(np.median(seg))


# R2-823's published segmentation and its published results, on the BEFORE
# sequence. The segment edges are properties of the OLD cut and are only used to
# reproduce it; the AFTER sequence is reported against its own landmarks.
R2823 = [
    ("establishing wide", 0.0, 2.5, 60, 13.16, 13.34),
    ("unreadable tour", 2.5, 26.3, 571, 20.27, 19.83),
    ("car resolves", 26.3, 29.0, 65, 14.59, 10.79),
    ("readable payoff", 29.0, 33.0, 95, 4.89, 4.60),
]


def reproduce(d):
    """Can this tool recover R2-823? Returns (ok, rows)."""
    rows, ok = [], True
    for name, lo, hi, n_pub, mean_pub, med_pub in R2823:
        n, mean, med = stats(d, lo, hi)
        # 2 % on the mean is the tolerance: ffmpeg's scaler and whatever R2-823
        # used will not agree to the last decimal, and claiming they should is
        # how a reproduction gets rejected for the wrong reason.
        good = (n == n_pub) and abs(mean - mean_pub) <= 0.02 * mean_pub
        ok = ok and good
        rows.append((name, n, n_pub, mean, mean_pub, med, med_pub, good))
    return ok, rows


def report(name, d, marks, fps=24.0):
    print("\n  %s — %d frame pairs, %.2f s" % (name, len(d), (len(d) + 1) / fps))
    print("  %-22s %8s %8s %8s" % ("segment", "n", "mean", "median"))
    out = {}
    for lbl, lo, hi in marks:
        n, mean, med = stats(d, lo, hi, fps)
        out[lbl] = (n, mean, med)
        print("  %-22s %8d %8.2f %8.2f" % ("%s  %.1f-%.1f s" % (lbl, lo, hi),
                                           n, mean, med))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--before", default=os.path.expanduser("~/vast-render/out/seq/r2beat1"))
    p.add_argument("--after")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()

    db = deltas(luma_series(a.before))
    ok, rows = reproduce(db)
    print("REPRODUCING R2-823 on %s" % a.before)
    print("  %-20s %6s %6s %8s %8s %8s %8s  %s"
          % ("segment", "n", "pub n", "mean", "pub", "median", "pub", ""))
    for nm, n, np_, m, mp, md, mdp, good in rows:
        print("  %-20s %6d %6d %8.2f %8.2f %8.2f %8.2f  %s"
              % (nm, n, np_, m, mp, md, mdp, "ok" if good else "<-- MISMATCH"))
    if not ok:
        print("\n>> STAGE RESULT: ENERGY_SELFTEST_FAIL")
        print("   This tool does not recover R2-823 on R2-823's own frames, so "
              "its numbers on any other sequence are not evidence.")
        return 1
    print("\n>> the instrument recovers R2-823 on R2-823's own frames")
    if a.selftest or not a.after:
        print(">> STAGE RESULT: ENERGY_SELFTEST_OK")
        return 0

    da = deltas(luma_series(a.after))
    # BEFORE: corners land f696-704, so the payoff is f705-792.
    # AFTER:  corners land f513-521, so the payoff is f522-792.
    b = report("BEFORE  %s" % a.before, db,
               [("establishing", 0.0, 2.5), ("tour", 2.5, 26.3),
                ("car resolves", 26.3, 29.0), ("PAYOFF", 29.0, 33.0)])
    c = report("AFTER   %s" % a.after, da,
               [("establishing", 0.0, 2.0), ("tour", 2.0, 19.33),
                ("car resolves", 19.33, 21.71), ("PAYOFF", 21.71, 33.0)])
    rb = b["tour"][1] / b["PAYOFF"][1]
    rc = c["tour"][1] / c["PAYOFF"][1]
    print("\n  tour : payoff energy ratio")
    print("    BEFORE  %.2fx   (%.2f s of payoff)" % (rb, (b["PAYOFF"][0]) / 24.0))
    print("    AFTER   %.2fx   (%.2f s of payoff)" % (rc, (c["PAYOFF"][0]) / 24.0))
    print("\n>> STAGE RESULT: %s"
          % ("ENERGY_INVERSION_FIXED" if rc < 1.5 else
             "ENERGY_STILL_INVERTED" if rc >= rb else "ENERGY_IMPROVED"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
