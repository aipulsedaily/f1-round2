#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2-375.  READ THE PAINT-VS-GEOMETRY ARMS.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/r2366_roof_pvg_measure.py -- --dir work/r2372/pvg \
        --json work/r2372/pvg_verdict.json

IT RUNS INSIDE BLENDER ONLY BECAUSE `tools/item_gate.py` IMPORTS `bpy` AT
MODULE SCOPE. Nothing here touches a scene; the statistic is imported rather
than reimplemented precisely so that this tool and the item gate cannot
disagree about what a dip is, and paying one Blender start-up is cheaper than
maintaining a second copy of `relief_anisotropy`.

THE STATISTIC IS `item_gate.relief_anisotropy`, IMPORTED, NOT REIMPLEMENTED.
It is the number the whole R2-060 argument is conducted in, and re-deriving it
here would mean the two tools could disagree about what a dip is. `dip` is the
depth of the negative lobe of the band-passed image's autocorrelation ALONG the
light, minus the same lobe ACROSS it -- so the band-pass's own baseline (0.120
on pure noise) cancels and what is left is the part only a directional light
falling on real relief can make.

THE MASK IS PURE GEOMETRY AND IS THE SAME IN EVERY ARM. It is the round-1 slab
rectangle -- x +-15.25, y +-11.25 at z = 6.500 -- projected through the f2978
ONER pose out of `world/camera_rig_path.json` and eroded. Nothing about it is
read out of any arm's pixels, so no arm can move the goalposts by changing
which pixels are lit. That was `relief_paint_vs_geometry`'s rule and it is the
reason the comparison means anything.

WHAT IT DECIDES
    dip(after_geo)     paint forced constant. Bump and mesh survive.
    dip(after_geonb)   ...and the Normal unlinked.  MESH ONLY.
    dip(after_truegeo) Lambert off the TRUE NORMAL. Bump cannot reach this arm.
    dip(after_paint)   emission of base colour. No sun, no shadow. PAINT ONLY.
    dip(before*)       the flat 4-vertex slab, the same three ways: THE FLOOR.

    If dip(after_geo) and dip(after_truegeo) both stand well clear of the
    before arms, the relief is geometry. If they collapse to the before floor
    and only dip(after_paint) is large, it is paint.

AND THE SUN-FLIP, WHICH IS THE PROJECT'S OWN SEPARATOR (item_gate.two_light_
bands). A lip and its shadow swap ends when the sun crosses to the other side;
a painted step does not move at all. So

    rho = corr(dog(sun A), dog(sun B))    -1 = pure relief, +1 = pure paint

is an independent read that needs no material surgery whatever.

`--null` names the repeat render of the `after` arm. Every arm difference is
reported against it, because two renders of the same scene do not match bit for
bit and a difference smaller than that floor is not a difference.
"""

import argparse
import json
import math
import os
import subprocess
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "tools"))
sys.path.insert(0, os.path.join(R2, "world"))

import importlib.util                                            # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


G = load("item_gate", os.path.join(R2, "tools/item_gate.py"))

W, H = 3840, 2160
SENSOR = 36.0
FRAME = 2978
BORDER = (0.453125, 0.549479, 0.504630, 0.587963)
ROOF = dict(x=(-15.25, 15.25), y=(-11.25, 11.25), z=6.500)
SUN_DIR = (0.5178540, -0.8277670, 0.2159390)      # world_contract, TO the sun

ARMS = ["before", "before_geo", "before_geonb", "before_truegeo",
        "before_paint",
        "after", "after_geo", "after_geonb", "after_truegeo", "after_paint"]
RADII = (2, 4, 8)


# ---------------------------------------------------------------------------
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
    u = fpx * Cc[..., 0] / d + W * 0.5
    v = -fpx * Cc[..., 1] / d + H * 0.5
    return np.stack([u, v], axis=-1)


def border_origin():
    return int(round(BORDER[0] * W)), int(round((1.0 - BORDER[3]) * H))


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


def read(path):
    """Linear-light grey, and the offset that maps frame px to this image."""
    dim = subprocess.run(["/usr/bin/magick", "identify", "-format", "%w %h",
                          path], capture_output=True, text=True).stdout.split()
    w, h = int(dim[0]), int(dim[1])
    a = _read16(path, w, h)
    ox, oy = (0, 0) if (w, h) == (W, H) else border_origin()
    return a, (ox, oy), (w, h)


def roof_mask(shape, off):
    """The slab rectangle, projected and rasterised. GEOMETRY, not pixels."""
    e = pose()
    h, w = shape
    corners = [(ROOF["x"][0], ROOF["y"][0], ROOF["z"]),
               (ROOF["x"][0], ROOF["y"][1], ROOF["z"]),
               (ROOF["x"][1], ROOF["y"][1], ROOF["z"]),
               (ROOF["x"][1], ROOF["y"][0], ROOF["z"])]
    P = project(np.array(corners), e) - np.array(off, float)
    yy, xx = np.mgrid[0:h, 0:w]
    inside = np.ones((h, w), bool)
    for i in range(4):
        a, b = P[i], P[(i + 1) % 4]
        cross = (b[0] - a[0]) * (yy - a[1]) - (b[1] - a[1]) * (xx - a[0])
        inside &= (cross >= 0) if i == 0 else True
    # robust point-in-quad: winding sign must agree for all four edges
    sgn = None
    inside = np.ones((h, w), bool)
    for i in range(4):
        a, b = P[i], P[(i + 1) % 4]
        cross = (b[0] - a[0]) * (yy - a[1]) - (b[1] - a[1]) * (xx - a[0])
        if sgn is None:
            sgn = 1.0 if cross[int(P[:, 1].mean()), int(P[:, 0].mean())] > 0 \
                else -1.0
        inside &= (cross * sgn) >= 0
    return inside, P


def sun_screen():
    """The direction the LIGHT TRAVELS, in (row, col) screen pixels."""
    e = pose()
    d = np.array(SUN_DIR, float)
    d = -d / np.linalg.norm(d)                 # from the sun toward the ground
    a = np.array([0.0, 0.0, ROOF["z"]])
    pa = project(a, e)
    pb = project(a + 10.0 * d, e)
    duv = pb - pa
    v = np.array([duv[1], duv[0]])             # (row, col)
    return v / max(np.linalg.norm(v), 1e-9)


def dog_rms(L, mask, r=2):
    B = G._dog(L, r)
    m = G._erode(mask, int(math.ceil(3 * r)))
    return float(np.sqrt((B[m] ** 2).mean())), B, m


def rho_pair(La, Lb, mask, r=2):
    """corr(dog A, dog B) inside the mask. -1 pure relief, +1 pure paint."""
    A = G._dog(np.log(np.maximum(La, 1e-6)), r)
    Bq = G._dog(np.log(np.maximum(Lb, 1e-6)), r)
    m = G._erode(mask, int(math.ceil(3 * r)))
    x, y = A[m], Bq[m]
    return float(((x - x.mean()) * (y - y.mean())).mean()
                 / max(x.std() * y.std(), 1e-30))


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(R2, "work/r2372/pvg"))
    ap.add_argument("--json", default=None)
    ap.add_argument("--r", type=int, default=2)
    a = ap.parse_args(argv)

    ref, off, shape_wh = read(os.path.join(a.dir, "after.png"))
    mask, P = roof_mask(ref.shape, off)
    print("border image %dx%d at frame offset %s" % (shape_wh[0], shape_wh[1], off))
    print("roof quad projects to %s" % np.round(P, 1).tolist())
    print("roof mask %d px of %d (%.1f %%)"
          % (mask.sum(), mask.size, 100.0 * mask.mean()))
    su = sun_screen()
    print("sun travel on screen (row, col) = (%+.3f, %+.3f)" % (su[0], su[1]))
    if mask.sum() < G.MIN_BAND_PX:
        raise SystemExit("REFUSING: mask is %d px, below item_gate.MIN_BAND_PX "
                         "%d" % (mask.sum(), G.MIN_BAND_PX))

    out = {"mask_px": int(mask.sum()), "sun_screen": su.tolist(),
           "r": a.r, "arms": {}}
    imgs = {}
    print("")
    print("BAND ENERGY is the amplitude clause, and on this subject it is the "
          "decisive column.")
    print("`relief_anisotropy`'s dip is a SHAPE-OF-AUTOCORRELATION statistic "
          "tuned for 1-2 px")
    print("isotropic lip-and-shadow dipoles. This roof's read is 10-80 px "
          "shadows lying ALONG")
    print("the light, which item_gate's own docstring says correctly scores a "
          "dip near zero --")
    print("`the correct answer for a direction the light cannot rake across`. "
          "The dip is")
    print("reported because it is the project's statistic; the verdict rests "
          "on band energy,")
    print("which is what item_gate says closes the correlation's blind spot.")
    print("")
    print("  %-16s %9s %9s %9s %10s %10s %10s"
          % ("arm", "dip", "dip_along", "dip_across",
             "band_r2", "band_r4", "band_r8"))
    for arm in ARMS + ["after_null"]:
        p = os.path.join(a.dir, arm + ".png")
        if not os.path.exists(p):
            print("  %-16s  MISSING" % arm)
            continue
        L, o2, _ = read(p)
        if o2 != off:
            raise SystemExit("REFUSING: %s has a different border origin" % arm)
        imgs[arm] = L
        bands = {r: dog_rms(L, mask, r)[0] for r in RADII}
        dip, det = G.relief_anisotropy(L, mask, tuple(su), r=a.r)
        out["arms"][arm] = {"dip": dip, "band_rms": bands[a.r],
                            "band": {str(r): v for r, v in bands.items()},
                            "dip_along": det.get("dip_along"),
                            "dip_across": det.get("dip_across"),
                            "best_lag_px": det.get("best_lag_px")}
        print("  %-16s %9s %9s %9s %10.5f %10.5f %10.5f"
              % (arm, "%.5f" % dip if dip is not None else "-",
                 det.get("dip_along"), det.get("dip_across"),
                 bands[2], bands[4], bands[8]))

    # --- the sun flip, on both before and after -----------------------------
    print("")
    for tag in ("after", "before"):
        f = os.path.join(a.dir, tag + "_sunflip.png")
        if not (os.path.exists(f) and tag in imgs):
            continue
        Lf, _, _ = read(f)
        r = rho_pair(imgs[tag], Lf, mask, a.r)
        out.setdefault("sunflip", {})[tag] = r
        print("  SUN FLIP  %-8s corr(dogA, dogB) = %+.4f   (-1 pure relief, "
              "+1 pure paint)" % (tag, r))

    # --- the verdict --------------------------------------------------------
    A = out["arms"]
    ok = all(k in A and A[k]["dip"] is not None
             for k in ("before", "before_geo", "after", "after_geo",
                       "after_truegeo", "after_paint"))
    if not ok:
        print("\nSTAGE RESULT: r2366_roof_pvg_measure VACUOUS (missing arms)")
        return 3
    floor = max(A["before"]["dip"], A["before_geo"]["dip"])
    out["flat_plate_floor"] = floor
    geo = A["after_geo"]["dip"]
    tru = A["after_truegeo"]["dip"]
    pnt = A["after_paint"]["dip"]
    nul = A.get("after_null", {}).get("dip")
    out["null_dip"] = nul
    print("")
    print("  the flat 4-vertex slab's own dip (the FLOOR)     %.5f" % floor)
    print("  after, paint forced constant   (geo)             %.5f  %+.5f"
          % (geo, geo - floor))
    print("  after, Lambert off the TRUE NORMAL (truegeo)     %.5f  %+.5f"
          % (tru, tru - floor))
    print("  after, emission of base colour (paint only)      %.5f  %+.5f"
          % (pnt, pnt - floor))
    if nul is not None:
        print("  after rendered twice (the NULL)                  %.5f  "
              "|d| %.5f" % (nul, abs(nul - A["after"]["dip"])))

    # THE VERDICT IS THE AMPLITUDE CLAUSE, AT EVERY BAND.
    print("")
    print("  BAND ENERGY, geometry arms against the flat 4-vertex slab")
    print("  %-24s %10s %10s %10s" % ("", "r2", "r4", "r8"))
    ratios = {}
    for tag, num, den in (("after / before", "after", "before"),
                          ("after_geo / before_geo", "after_geo", "before_geo"),
                          ("after_geonb / before_geonb", "after_geonb",
                           "before_geonb"),
                          ("after_truegeo / before_truegeo", "after_truegeo",
                           "before_truegeo"),
                          ("after_paint / before_paint", "after_paint",
                           "before_paint")):
        if num not in A or den not in A:
            continue
        row = []
        for r in RADII:
            n2 = A[num]["band"][str(r)]
            d2 = max(A[den]["band"][str(r)], 1e-9)
            row.append(n2 / d2)
        ratios[tag] = row
        print("  %-24s %9.1fx %9.1fx %9.1fx" % (tag, row[0], row[1], row[2]))
    out["band_ratios"] = ratios
    keep = [A["after_geo"]["band"][str(r)] / max(A["after"]["band"][str(r)], 1e-9)
            for r in RADII]
    out["geo_fraction_of_full"] = keep
    print("  %-24s %9.2f  %9.2f  %9.2f    <- the fraction of the built roof's "
          "band energy that SURVIVES the paint being taken away"
          % ("after_geo / after", keep[0], keep[1], keep[2]))

    real = ((geo - floor) > 0.030 and (tru - floor) > 0.030
            and min(keep) > 0.60
            and (A["after_geo"]["band"]["2"]
                 / max(A["before_geo"]["band"]["2"], 1e-9)) > 5.0)
    out["verdict"] = ("RELIEF_IS_GEOMETRY" if real else
                      "RELIEF_IS_PAINT" if (pnt - floor) > 0.030 else
                      "INCONCLUSIVE")
    if a.json:
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
        json.dump(out, open(a.json, "w"), indent=1)
        print("  wrote %s" % a.json)
    print("\nSTAGE RESULT: r2366_roof_pvg_measure %s"
          % ("PASS (%s)" % out["verdict"] if real
             else "FAIL (%s)" % out["verdict"]))
    return 0 if real else 1


if __name__ == "__main__":
    sys.exit(main())
