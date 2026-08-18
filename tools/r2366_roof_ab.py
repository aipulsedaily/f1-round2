#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2-374.  THE SHOWROOM ROOF A/B ON THE DELIVERED 4K FRAME, WITH ITS NULL.

    python3 tools/r2366_roof_ab.py \
        work/r2372/ab_before.png work/r2372/ab_after.png work/r2372/ab_null.png \
        --json work/r2372/ab.json --crops work/r2372

    BEFORE  render/film14_breach_r6.blend        the flat 8-vertex slab
    AFTER   render/r2372_roof_after.blend        the same file plus the roof
    NULL    render/r2372_roof_null.blend         a BYTE-IDENTICAL `cp` of AFTER

Every arm is the film's own ONER camera at frame 2978, 3840x2160, the same
lens, the same animated DOF, 400 samples, adaptive 0.01, OpenImageDenoise on
GPU, no border. The only thing that differs between BEFORE and AFTER is the
126 objects `tools/r2366_roof_build.py` adds above z = 6.500.

A DIFFERENCE IS ONLY EVIDENCE IF IT IS BIGGER THAN THE NULL. Cycles is
stochastic and OIDN is not idempotent across runs, so two renders of the same
scene do not match bit for bit; the NULL measures exactly how far apart "no
change at all" lands, and the BEFORE/AFTER distance has to clear it. This is
`tools/r2256_ab_measure.py`'s pattern and its arithmetic.

AND THE FREE NEGATIVE CONTROL (R2-150). The change is 126 objects inside
x +-15.3, y +-11.3, z 6.5..9.7 -- a 30 x 22 m box on top of one building. A
region of the frame that box cannot reach must sit AT THE NULL, and if it does
not then the diff is measuring the renderer and not the roof. Two are used: the
sky above the horizon, which nothing on a roof can touch, and the near
foreground apron, which is 300 m in front of the showroom. Both are named and
measured, not asserted.

THE FIRST HYPOTHESIS FOR "NO CHANGE" IS THAT THE CHANGE NEVER HAPPENED, so this
prints each input's mtime, size and sha256 prefix before it prints a single
statistic.
"""

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

W, H = 3840, 2160
SENSOR = 36.0
FRAME = 2978
ROOF = dict(x=(-15.25, 15.25), y=(-11.25, 11.25), z=6.500)

# The regions, in delivered-frame pixels (x0, x1, y0, y1), top-left origin.
#   roof        the projected slab quad's AABB, grown to hold the parapet and
#               the tallest plant -- computed, not typed; see `regions()`.
#   NEGATIVE CONTROLS, chosen because the change cannot reach them:
#   sky         above the skyline, 300 px band at the top of the frame
#   foreground  the bottom 260 px, apron ~300 m in front of the showroom
CONTROLS = {
    "sky_top_band": (0, 3840, 0, 300),
    "foreground_apron": (0, 3840, 1900, 2160),
}


def quat_to_mat(q):
    w, x, y, z = q
    n = math.sqrt(w * w + x * x + y * y + z * z)
    w, x, y, z = w / n, x / n, y / n, z / n
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def pose():
    p = json.load(open(os.path.join(R2, "world/camera_rig_path.json")))["path"]
    return [r for r in p if r["f"] == FRAME][0]


def project(P, e):
    R = quat_to_mat(e["q"])
    fpx = (e["lens"] / SENSOR) * W
    V = np.asarray(P, float) - np.asarray(e["p"], float)
    Cc = V @ R
    d = -Cc[..., 2]
    return np.stack([fpx * Cc[..., 0] / d + W * 0.5,
                     -fpx * Cc[..., 1] / d + H * 0.5], axis=-1)


def regions():
    """The roof box, projected. Every corner of the BUILT extent, not the slab.

    The built roof reaches z = 9.654 (the AHU stack) and x/y +-15.295 (the
    coping oversail), and a mask cut to the flat slab would leave the plant --
    which is most of the change -- outside the region being measured.
    """
    e = pose()
    lo = np.array([-15.295, -11.295, 6.500])
    hi = np.array([15.295, 11.295, 9.660])
    C = np.array([[lo[0] if i & 1 else hi[0],
                   lo[1] if i & 2 else hi[1],
                   lo[2] if i & 4 else hi[2]] for i in range(8)])
    P = project(C, e)
    x0, x1 = int(math.floor(P[:, 0].min())) - 2, int(math.ceil(P[:, 0].max())) + 2
    y0, y1 = int(math.floor(P[:, 1].min())) - 2, int(math.ceil(P[:, 1].max())) + 2
    R = dict(CONTROLS)
    R["roof"] = (max(x0, 0), min(x1, W), max(y0, 0), min(y1, H))
    # the slab quad on its own, for the "how flat WAS it" histogram
    q = project(np.array([(ROOF["x"][0], ROOF["y"][0], ROOF["z"]),
                          (ROOF["x"][0], ROOF["y"][1], ROOF["z"]),
                          (ROOF["x"][1], ROOF["y"][1], ROOF["z"]),
                          (ROOF["x"][1], ROOF["y"][0], ROOF["z"])]), e)
    R["roof_deck_only"] = (int(q[:, 0].min()) + 3, int(q[:, 0].max()) - 3,
                           int(q[:, 1].min()) + 3, int(q[:, 1].max()) - 3)
    return R


def stamp(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    st = os.stat(path)
    return dict(path=path, bytes=st.st_size,
                mtime=time.strftime("%Y-%m-%d %H:%M:%S",
                                    time.localtime(st.st_mtime)),
                sha256=h.hexdigest()[:16])


# ---------------------------------------------------------------------------
# R2-373.  READING A 16-BIT GREY STREAM, AND THE BYTE ORDER THAT WAS WRONG.
#
# `tools/r2256_ab_measure.py`'s `gray()` -- the established pattern this file
# was told to follow -- reads ImageMagick's `gray:-` output as `dtype=">u2"`
# with no `-endian` on the command line. On this box (ImageMagick 7.1.2-27
# Q16-HDRI) that stream is LITTLE-endian, so every value comes back byte
# swapped. Measured on the flat-slab BEFORE arm, over the same pixels:
#
#     read as ">u2", no -endian     mean 0.64337   sd 0.300907
#     read as ">u2", -endian MSB    mean 0.29559   sd 0.001567
#
# The second is a flat plane, which is what the picture is. The first is noise
# with a plausible-looking mean, and it is what a byte-swapped 16-bit ramp
# always looks like: the low byte becomes the high byte, so a smooth gradient
# turns into a sawtooth and a FLAT SURFACE ACQUIRES sd = 0.30. Every band-pass
# statistic taken through it is measuring the byte order.
#
# So the byte order is STATED on the command line rather than defaulted, and
# then CHECKED against an independent 8-bit read of the same file, because a
# stated assumption that is never tested is the same class of thing as an
# unstated one.
# ---------------------------------------------------------------------------
def _read16(path, w, h):
    raw = subprocess.run(["/usr/bin/magick", path, "-colorspace", "RGB",
                          "-depth", "16", "-endian", "MSB", "gray:-"],
                         capture_output=True).stdout
    if len(raw) != w * h * 2:
        raise SystemExit("REFUSING: %s gave %d bytes, expected %d"
                         % (path, len(raw), w * h * 2))
    a = np.frombuffer(raw, dtype=">u2").astype(np.float64).reshape(h, w) / 65535.0
    raw8 = subprocess.run(["/usr/bin/magick", path, "-colorspace", "RGB",
                           "-depth", "8", "gray:-"], capture_output=True).stdout
    b = np.frombuffer(raw8, dtype=np.uint8).astype(np.float64).reshape(h, w) / 255.0
    d = float(np.abs(a - b).mean())
    if d > 0.01:
        raise SystemExit(
            "REFUSING: the 16-bit and 8-bit reads of %s differ by %.4f mean "
            "absolute. That is a byte-order or a colourspace fault, not "
            "quantisation (which is bounded by 1/512 = 0.00195)." % (path, d))
    return a


def gray(path):
    dim = subprocess.run(["/usr/bin/magick", "identify", "-format", "%w %h",
                          path], capture_output=True, text=True).stdout.split()
    w, h = int(dim[0]), int(dim[1])
    if (w, h) != (W, H):
        raise SystemExit("REFUSING: %s is %dx%d, not the delivered %dx%d"
                         % (path, w, h, W, H))
    return _read16(path, w, h)


def cut(a, r):
    x0, x1, y0, y1 = r
    return a[y0:y1, x0:x1]


def stats(a, b, r):
    d = cut(a, r) - cut(b, r)
    return dict(rms=float(np.sqrt((d ** 2).mean())),
                p999=float(np.percentile(np.abs(d), 99.9)),
                mx=float(np.abs(d).max()),
                over02=float((np.abs(d) > 0.02).mean()),
                npx=int(d.size))


def tile_map(B, A, N, tile=120):
    """WHERE THE CHANGE REACHES, AND WHAT THE FLOOR REALLY IS.

    A single named negative control tests one guess about where the change
    cannot go. This tests every 120 px tile in the frame, which is both stronger
    evidence and the only way the SECOND number below could have been found.

    TWO FLOORS, AND THE FIRST ONE IS THE WRONG ONE.

    The NULL is `after` rendered twice from a byte-identical copy: it measures
    how far apart two renders of the SAME scene land. But BEFORE and AFTER are
    two renders of DIFFERENT scenes, and Cycles' adaptive sampler allocates
    against a whole-frame noise threshold while OpenImageDenoise is a
    convolutional network with a large receptive field. Change anything and
    every pixel in the frame moves a little, everywhere, forever. Measured
    here: over the 473 of 576 tiles that carry none of the change, the
    BEFORE/AFTER rms is a median of **2.00x** the same-scene null and never
    exceeds 5.3x.

    So `is this control at the same-scene null` is a test NO PIXEL IN THE FRAME
    passes, including pixels 40 km from the building, and a control judged
    against it fails for a reason that has nothing to do with the change. The
    right reference is the DIFFERENT-SCENE FLOOR: the distribution of the same
    ratio over the tiles that provably carry nothing. This function measures it
    from the frame itself rather than assuming a number.
    """
    H, W2 = B.shape[0] // tile, B.shape[1] // tile
    ab = np.zeros((H, W2)); nl = np.zeros((H, W2)); ov = np.zeros((H, W2))
    for i in range(H):
        for j in range(W2):
            sl = (slice(i * tile, (i + 1) * tile),
                  slice(j * tile, (j + 1) * tile))
            a = B[sl] - A[sl]; b = A[sl] - N[sl]
            ab[i, j] = float(np.sqrt((a ** 2).mean()))
            nl[i, j] = float(np.sqrt((b ** 2).mean()))
            ov[i, j] = float((np.abs(a) > 0.02).mean())
    rat = ab / np.maximum(nl, 1e-12)
    carry = ov > 0.01                      # tiles that carry the change
    quiet = ov <= 0.0005                   # tiles that provably carry none
    out = dict(tile=tile, n_tiles=int(ov.size),
               n_carrying=int(carry.sum()), n_quiet=int(quiet.sum()),
               carrying=[dict(x=[int(j * tile), int((j + 1) * tile)],
                              y=[int(i * tile), int((i + 1) * tile)],
                              ab_rms=ab[i, j], null_rms=nl[i, j],
                              ratio=rat[i, j], over02=ov[i, j])
                         for i, j in zip(*np.where(carry))],
               floor=dict(ab_rms_median=float(np.median(ab[quiet])),
                          ab_rms_max=float(ab[quiet].max()),
                          null_rms_median=float(np.median(nl[quiet])),
                          ratio_median=float(np.median(rat[quiet])),
                          ratio_p95=float(np.percentile(rat[quiet], 95)),
                          ratio_max=float(rat[quiet].max())))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("null")
    ap.add_argument("--json", default=None)
    ap.add_argument("--crops", default=None)
    ap.add_argument("--crop-zoom", type=int, default=350)
    a = ap.parse_args()

    print(">> INPUT IDENTITY  (the first hypothesis for `no change` is that "
          "the change never happened)")
    ids = {}
    for tag, p in (("before", a.before), ("after", a.after), ("null", a.null)):
        ids[tag] = stamp(p)
        print("   %-7s %-46s %10d B  %s  sha %s"
              % (tag, os.path.basename(p), ids[tag]["bytes"], ids[tag]["mtime"],
                 ids[tag]["sha256"]))
    if ids["after"]["sha256"] == ids["null"]["sha256"]:
        raise SystemExit("REFUSING: AFTER and NULL are the same FILE. The null "
                         "has to be a second RENDER of the same scene, not a "
                         "copy of the same picture.")

    R = regions()
    B, A, N = gray(a.before), gray(a.after), gray(a.null)

    print("\n>> REGIONS (delivered 4K pixels, top-left origin)")
    for k, r in sorted(R.items()):
        print("   %-18s x %4d-%4d  y %4d-%4d   %8d px"
              % (k, r[0], r[1], r[2], r[3], (r[1] - r[0]) * (r[3] - r[2])))

    out = {"inputs": ids, "regions": {k: list(v) for k, v in R.items()},
           "measure": {}}
    print("\n>> %-20s %-26s %9s %9s %9s %9s"
          % ("region", "pair", "rms", "p99.9", "max", ">0.02"))
    for k in ("roof", "roof_deck_only", "sky_top_band", "foreground_apron"):
        r = R[k]
        sn = stats(A, N, r)
        sd = stats(B, A, r)
        out["measure"][k] = {"null": sn, "ab": sd,
                             "ratio": sd["rms"] / max(sn["rms"], 1e-12)}
        print("   %-20s %-26s %9.5f %9.5f %9.5f %8.2f%%"
              % (k, "NULL  after vs after-again", sn["rms"], sn["p999"],
                 sn["mx"], 100 * sn["over02"]))
        print("   %-20s %-26s %9.5f %9.5f %9.5f %8.2f%%   %6.1fx the null"
              % ("", "A/B   before vs after", sd["rms"], sd["p999"], sd["mx"],
                 100 * sd["over02"], out["measure"][k]["ratio"]))

    # --- what the roof surface's own tonal distribution did -----------------
    r = R["roof_deck_only"]
    print("\n>> THE ROOF'S OWN TONAL DISTRIBUTION  (region %s)" % (r,))
    print("   %-8s %8s %8s %8s %8s %8s %9s"
          % ("arm", "mean", "sd", "p5", "p50", "p95", "p95-p5"))
    for tag, im in (("before", B), ("after", A), ("null", N)):
        v = cut(im, r).ravel()
        p5, p50, p95 = np.percentile(v, [5, 50, 95])
        out.setdefault("tonal", {})[tag] = dict(
            mean=float(v.mean()), sd=float(v.std()), p5=float(p5),
            p50=float(p50), p95=float(p95), spread=float(p95 - p5))
        print("   %-8s %8.4f %8.4f %8.4f %8.4f %8.4f %9.4f"
              % (tag, v.mean(), v.std(), p5, p50, p95, p95 - p5))

    if a.crops:
        os.makedirs(a.crops, exist_ok=True)
        cx0, cx1, cy0, cy1 = R["roof"]
        for tag, p in (("before", a.before), ("after", a.after),
                       ("null", a.null)):
            o = os.path.join(a.crops, "crop_%s_%dx.png" % (tag, a.crop_zoom // 100))
            subprocess.run(["/usr/bin/magick", p, "-crop",
                            "%dx%d+%d+%d" % (cx1 - cx0, cy1 - cy0, cx0, cy0),
                            "+repage", "-filter", "point", "-resize",
                            "%d%%" % a.crop_zoom, o], check=True)
            print("   wrote %s" % o)
            out.setdefault("crops", {})[tag] = o
        # and the brief's own crop box, so it can be put beside the artefact
        for tag, p in (("before", a.before), ("after", a.after)):
            o = os.path.join(a.crops, "briefcrop_%s_35x.png" % tag)
            subprocess.run(["/usr/bin/magick", p, "-crop", "560x380+1680+880",
                            "+repage", "-filter", "point", "-resize", "350%",
                            o], check=True)
            print("   wrote %s" % o)

    # --- where the change reaches, over the WHOLE frame ---------------------
    tm = tile_map(B, A, N)
    out["tile_map"] = tm
    f = tm["floor"]
    print("\n>> WHERE THE CHANGE REACHES  (%d px tiles, %d of them)"
          % (tm["tile"], tm["n_tiles"]))
    print("   %d tile(s) carry it (more than 1%% of their pixels over 0.02):"
          % tm["n_carrying"])
    for t in tm["carrying"]:
        print("      x %4d-%4d  y %4d-%4d   A/B rms %.5f  null %.5f  "
              "%6.1fx  over0.02 %5.1f%%"
              % (t["x"][0], t["x"][1], t["y"][0], t["y"][1], t["ab_rms"],
                 t["null_rms"], t["ratio"], 100 * t["over02"]))
    print("   THE DIFFERENT-SCENE FLOOR, from the %d tile(s) that carry none:"
          % tm["n_quiet"])
    print("      A/B rms median %.5f (max %.5f) against a same-scene null of "
          "%.5f" % (f["ab_rms_median"], f["ab_rms_max"], f["null_rms_median"]))
    print("      ratio  median %.2fx   p95 %.2fx   max %.2fx"
          % (f["ratio_median"], f["ratio_p95"], f["ratio_max"]))

    # --- the verdict --------------------------------------------------------
    m = out["measure"]
    # JUDGED AGAINST THE DIFFERENT-SCENE FLOOR, NOT THE SAME-SCENE NULL. See
    # `tile_map`: no pixel in this frame sits at the same-scene null, because
    # the adaptive sampler and the denoiser both respond to the whole frame.
    bar = f["ratio_p95"]
    roof_ok = m["roof"]["ratio"] > 10.0 * bar
    ctl_bad = [k for k in ("sky_top_band", "foreground_apron")
               if m[k]["ratio"] > bar]
    out["control_bar_ratio"] = bar
    out["verdict"] = ("ROOF_AB_CLEARS_NULL" if roof_ok and not ctl_bad else
                      "ROOF_AB_CONTROL_MOVED_FAIL" if ctl_bad else
                      "ROOF_AB_AT_THE_NULL_FAIL")
    print("")
    print("   the roof region moves %.1fx the same-scene null and %.1fx the "
          "different-scene floor"
          % (m["roof"]["ratio"], m["roof"]["ratio"] / f["ratio_median"]))
    print("   the bar a negative control must sit under is the floor's p95, "
          "%.2fx" % bar)
    for k in ("sky_top_band", "foreground_apron"):
        print("   NEGATIVE CONTROL %-18s %.2fx the null  (%s)"
              % (k, m[k]["ratio"],
                 "AT THE FLOOR" if m[k]["ratio"] <= bar else
                 "ABOVE THE FLOOR -- the diff is not only the roof"))
    if a.json:
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
        json.dump(out, open(a.json, "w"), indent=1)
        print("   wrote %s" % a.json)
    print("\nSTAGE RESULT: r2366_roof_ab %s"
          % ("PASS (%s)" % out["verdict"] if roof_ok and not ctl_bad
             else "FAIL (%s)" % out["verdict"]))
    return 0 if (roof_ok and not ctl_bad) else 1


if __name__ == "__main__":
    sys.exit(main())
