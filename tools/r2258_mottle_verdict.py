"""R2-258 — THE MOTTLING VERDICT.

The review asked: is the sign band's dirt map at the wrong scale, or is that
correct weathering at 180 m?

MEASURED, with identical processing on both sides:

  A  the delivered frame `2972abcb3fa1.png`, in the CADENCE fascia banner's
     clean print band (v 0.20-0.38 -- above the low stiffener at v=0.14, below
     the logotype at v=0.43), sampled uniformly in METRES along the banner by
     projecting its circuit-frame coordinates through frame 2575's camera;

  B  `mat_print`'s own colour field, rendered flat and orthographic at
     0.005 m/px onto a 44.0 x 1.60 m plate carrying the banner's UV layout, the
     CADENCE base colour and the unit's real aux (age 0.2783, dirt 0.3578),
     then RESAMPLED to A's 65.4 px/m and smeared by A's own measured motion blur
     (8 px along the banner, 15 px across).

STATISTIC: the fraction of variance in each spatial octave, along the banner.
"Where is the energy?" is the actual question a scale complaint asks, and a
single 'feature size' number cannot answer it -- mat_print is deliberately
multi-scale (orange peel 8 mm, squeegee 30 mm, rain streaks 93 mm, wash 0.24 m,
mottle 0.56 m), so any one number is an average over a design.

CONTROLS: the same field rendered with the LARGE-SCALE MOTTLE node moved 3x
coarser (0.6 cyc/m) and 3x finer (5.4 cyc/m).  If the statistic cannot tell
those from the authored 1.8 cyc/m, it is measuring nothing and its verdict on
the delivered frame is worthless.
"""
import math
import subprocess

import numpy as np

W_PX, H_PX = 3840, 2160
SENSOR, LENS = 36.0, 40.7321
CAM_P = np.array([-68.37986, -164.94598, 4.72238])
CAM_Q = (0.672424, 0.613148, -0.279232, -0.306471)
ROT, PC, PW = math.radians(40.0), (-350.0, 72.0), (15.0, 0.0)
BX, Z0, H_M, W_M = -452.055, 8.92, 1.60, 44.0
V0, V1 = 0.20, 0.38
PXM = 65.4                      # delivered px per metre on the banner
SMEAR_ALONG, SMEAR_ACROSS = 8, 15    # delivered px, from the camera path
HERE = "/home/zany/f1-round2/work/r2256/"


def c2w(cx, cy, cz):
    dx, dy = cx - PC[0], cy - PC[1]
    return np.array([PW[0] + dx * math.cos(ROT) - dy * math.sin(ROT),
                     dx * math.sin(ROT) + dy * math.cos(ROT), cz])


def qm(q):
    w, x, y, z = np.array(q) / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


Rw = qm(CAM_Q).T
F_PX = W_PX * LENS / SENSOR


def project(P):
    v = Rw @ (np.asarray(P, float) - CAM_P)
    d = -v[2]
    return (W_PX * 0.5 + F_PX * v[0] / d, H_PX * 0.5 - F_PX * v[1] / d, d)


def gray(path, w, h):
    raw = subprocess.run(["/usr/bin/magick", path, "-colorspace", "RGB",
                          "-depth", "16", "gray:-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=">u2").reshape(h, w).astype(np.float64) / 65535.0


OCT = [(0.02, 0.05), (0.05, 0.10), (0.10, 0.20), (0.20, 0.40),
       (0.40, 0.80), (0.80, 1.60), (1.60, 3.20)]     # metres per cycle


def octaves(rows, d_m):
    """fraction of variance per spatial octave, along the banner."""
    n = rows.shape[1]
    f = np.fft.rfftfreq(n, d=d_m)                     # cycles / metre
    lam = np.divide(1.0, f, out=np.full_like(f, 1e9), where=f > 0)
    win = np.hanning(n)
    P = np.zeros_like(f)
    for r in rows:
        r = r - r.mean()
        P += np.abs(np.fft.rfft(r * win)) ** 2
    P[0] = 0.0
    tot = P.sum()
    return np.array([P[(lam >= a) & (lam < b)].sum() / tot for (a, b) in OCT]), tot


def degrade(field, fd):
    """resample a 0.005 m/px field to the delivered frame's px/m and smear it."""
    k = max(1, int(round((1.0 / PXM) / fd)))
    h, w = field.shape
    f = field[:h // k * k, :w // k * k]
    f = f.reshape(h // k, k, w // k, k).mean(axis=(1, 3))
    for n, ax in ((SMEAR_ALONG, 1), (SMEAR_ACROSS, 0)):
        if n > 1:
            ker = np.ones(n) / n
            f = np.apply_along_axis(lambda v: np.convolve(v, ker, mode='same'), ax, f)
    return f, fd * k


def show(tag, frac):
    print("    %-30s %s" % (tag, "  ".join("%5.1f" % (100 * v) for v in frac)))


print("=" * 84)
print("A.  THE DELIVERED FRAME  2972abcb3fa1.png")
img = gray("/home/zany/vast-render/out/2972abcb3fa1.png", W_PX, H_PX)
top, bot = project(c2w(BX, 2.0, Z0 + H_M)), project(c2w(BX, 2.0, Z0))
print("    banner depth               %.2f m      <- the review's premise was 180 m"
      % bot[2])
print("    1.60 m panel spans         %.1f px  -> %.1f px/m"
      % (bot[1] - top[1], (bot[1] - top[1]) / H_M))
print("    deleted PASSERELLE centre  px %.1f, %.1f  (reported crop 1530-2150, 280-420)"
      % project(c2w(-452.10, 2.0, 9.65))[:2])
ys = np.linspace(-14.0, 18.0, 1600)
dA = ys[1] - ys[0]
rowsA = np.array([[img[int(round(project(c2w(BX, cy, Z0 + vf * H_M))[1])),
                       int(round(project(c2w(BX, cy, Z0 + vf * H_M))[0]))]
                   for cy in ys] for vf in np.linspace(V0, V1, 9)])
q10, q90 = np.percentile(rowsA, [10, 90])
print("    clean print band p90/p10   %.3f  (sampled at %.4f m per sample)"
      % (q90 / q10, dA))
fracA, _ = octaves(rowsA, dA)

print("")
print("VARIANCE BY SPATIAL OCTAVE ALONG THE BANNER, %% of total")
print("    %-30s %s" % ("metres per cycle:",
                        "  ".join("%5s" % ("%g-%g" % o) for o in OCT)))
show("A  DELIVERED FRAME", fracA)

fw, fh = 8800, 320
fd0 = W_M / fw
res = {}
for tag, path in (("B  mat_print AS AUTHORED (1.8)", "print_field.png"),
                  ("C1 CONTROL mottle 0.6 cyc/m", "print_field_coarse.png"),
                  ("C2 CONTROL mottle 5.4 cyc/m", "print_field_fine.png")):
    fld = gray(HERE + path, fw, fh)
    dg, dd = degrade(fld, fd0)
    h = dg.shape[0]
    band = dg[int(V0 * h):max(int(V0 * h) + 2, int(V1 * h))]
    fr, _ = octaves(band, dd)
    res[tag] = fr
    show(tag, fr)

print("")
print("=" * 84)


def chi(a, b):
    return float(np.sum((a - b) ** 2) / np.sum(b ** 2)) ** 0.5


bt = "B  mat_print AS AUTHORED (1.8)"
print("DISTANCE FROM THE DELIVERED FRAME (relative L2 over the octave profile):")
for tag in res:
    mark = "  <-- best" if chi(fracA, res[tag]) == min(
        chi(fracA, res[t]) for t in res) else ""
    print("    %-32s %.4f%s" % (tag, chi(fracA, res[tag]), mark))
print("")
print("CONTROL SEPARATION (the statistic must be able to tell them apart):")
print("    authored vs 3x coarse            %.4f"
      % chi(res[bt], res["C1 CONTROL mottle 0.6 cyc/m"]))
print("    authored vs 3x fine              %.4f"
      % chi(res[bt], res["C2 CONTROL mottle 5.4 cyc/m"]))
print("=" * 84)
