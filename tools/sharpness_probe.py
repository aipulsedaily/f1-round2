"""Is this frame actually sharp, or is the whole thing uniformly soft?

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/sharpness_probe.py -- a.png b.png ...

WHY
---
The armco_w_beam peep measured mean |Laplacian| across its hero macro:

    near steel face @2.6 m   1.775
    mid                      1.715
    far                      1.790
    ground                   1.580
    SKY                      1.543

**The sky carried 87 % of the detail energy of the in-focus steel.** A sky is a
smooth gradient with essentially no high-frequency content; if it measures nearly
as "detailed" as the focal subject, the number is not reporting subject detail --
the entire frame is uniformly soft.

Depth of field cannot do that: DoF is a function of distance, and near/mid/far
were identical within 4 %.

WHAT THIS MEASURES
------------------
Detail energy (mean |Laplacian|) in horizontal bands, plus the single number that
matters:

    SKY / SUBJECT ratio

    ~0.1 or below   a normally sharp frame -- the sky is smooth, the subject is not
    approaching 1  the frame is soft, whatever the cause

It needs NO reference image and no knowledge of the scene, which is what makes it
usable as a standing gate in the render ladder (#36). The sky is its own control:
it is guaranteed smooth in the real world, so any detail energy it shows is the
render path's noise floor or its blur, not content.

DISAMBIGUATION
--------------
Run it on the same camera with the denoiser ON and OFF:

  * ratio drops sharply with the denoiser off -> the denoiser is eating detail
    (lower adaptive_threshold, raise samples, or feed it albedo/normal passes)
  * ratio stays near 1 in BOTH                -> the subject genuinely has no
    detail, and this is an AMPLITUDE problem in the asset (see R2 defect log,
    "the wave-1 pattern"), not a render bug

Those two causes are indistinguishable from a single frame, which is exactly why
wave 1's reviews could not separate them.
"""

import sys

import numpy as np
import bpy


def load(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float64).reshape(h, w, 4)[..., :3]
    bpy.data.images.remove(img)
    # luminance, and flip so row 0 is the TOP of the frame
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    return lum[::-1]


def detail(p):
    """Mean |Laplacian| — per-pixel high-frequency energy, x1000 for readability."""
    if p.shape[0] < 3 or p.shape[1] < 3:
        return 0.0
    lap = (4.0 * p[1:-1, 1:-1]
           - p[:-2, 1:-1] - p[2:, 1:-1] - p[1:-1, :-2] - p[1:-1, 2:])
    return float(np.abs(lap).mean() * 1000.0)


def main():
    argv = sys.argv
    paths = argv[argv.index("--") + 1:] if "--" in argv else []
    if not paths:
        raise SystemExit("give me one or more PNG paths after --")

    for path in paths:
        try:
            L = load(path)
        except Exception as e:
            print(f"!! {path}: {e}")
            continue
        h, w = L.shape
        bands = {
            "top (sky)": L[: h // 6],
            "upper":     L[h // 6: h // 3],
            "middle":    L[h // 3: h * 2 // 3],
            "lower":     L[h * 2 // 3: h * 5 // 6],
            "bottom":    L[h * 5 // 6:],
        }
        print(f"\n=== {path.split('/')[-1]}  ({w}x{h}) ===")
        print(f"{'band':<12}{'mean lum':>10}{'detail':>10}")
        d = {}
        for k, v in bands.items():
            d[k] = detail(v)
            print(f"{k:<12}{v.mean():>10.4f}{d[k]:>10.3f}")

        sky = d["top (sky)"]
        subj = max(d["middle"], d["lower"], d["bottom"])
        ratio = sky / subj if subj > 1e-9 else float("inf")
        verdict = ("SOFT — sky is as detailed as the subject" if ratio > 0.55 else
                   "suspect" if ratio > 0.30 else
                   "sharp — sky is smooth relative to subject")
        print(f"\n  sky detail      {sky:8.3f}")
        print(f"  subject detail  {subj:8.3f}")
        print(f"  SKY/SUBJECT     {ratio:8.3f}   {verdict}")



# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised: `blender -b -P x.py`
    # prints the traceback and exits 0, MEASURED on this box. A gate that
    # crashed was indistinguishable from one that passed. guard() makes an
    # uncaught exception a status 2 and passes any real verdict through
    # unchanged. One shared helper, not N copies -- see tools/gate_exit.py.
    gate_exit.guard(main, tool="sharpness_probe")
