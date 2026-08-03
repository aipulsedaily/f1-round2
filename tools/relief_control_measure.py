"""Measure the gate's own relief statistic on the positive-control ladder.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/relief_control_measure.py -- --dir render/relief_control

Reuses `relief_anisotropy()` STRAIGHT OUT OF tools/item_gate.py — importing the
real function, not a reimplementation. A reimplementation would test my
understanding of the check rather than the check itself, which is the same class
of error as measuring the wrong quantity in the first place.

WHAT A PASS LOOKS LIKE

    dip(a_flat)  ~ dip(f_printed) ~ 0     flat plate and printed decoy read as nothing
    dip(d_8mm)  >> dip(a_flat)            real relief is found
    dip(b) < dip(c) < dip(d)              MONOTONIC in feature height

Monotonicity is the strongest available evidence. A single threshold can be luck;
a statistic that tracks the physical quantity across four known heights is
measuring what it claims to.

THE DECOY IS THE POINT. Panel (f) is the rib pattern painted on as an albedo
change with zero geometry. If it scores like a real rib panel, the check is
measuring CONTRAST rather than RELIEF — and 21 of the gate's 28 verdicts rest on
it.
"""

import argparse
import glob
import importlib.util
import math
import os
import sys

import numpy as np
import bpy

# Imported by path, not by package: this runs inside Blender's interpreter with
# whatever cwd the caller happened to have.
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402

R2 = "/home/zany/f1-round2"

SUN_ELEV_DEG = 12.5
SUN_BEARING_DEG = -58.0

ORDER = ["a_flat_0mm", "b_rib_0p5mm", "c_rib_2mm", "d_rib_8mm",
         "e_bolts_3mm", "f_printed_0mm"]
HEIGHT_MM = {"a_flat_0mm": 0.0, "b_rib_0p5mm": 0.5, "c_rib_2mm": 2.0,
             "d_rib_8mm": 8.0, "e_bolts_3mm": 3.0, "f_printed_0mm": 0.0}


def load_gate():
    """Import the REAL item_gate module, so we test the shipped code."""
    path = os.path.join(R2, "tools/item_gate.py")
    spec = importlib.util.spec_from_file_location("item_gate", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["item_gate"] = mod
    spec.loader.exec_module(mod)
    return mod


def load_png(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float64).reshape(h, w, 4)
    bpy.data.images.remove(img)
    a = a[::-1]                                  # row 0 = top
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    alpha = a[..., 3]
    return lum, alpha


def sun_screen_dir():
    """The sun's direction projected into screen space, as (drow, dcol).

    The camera looks from (cx, -0.42, 0.62) at (cx, 0, 0): a level-ish view down
    the +Y axis. Screen +col is world +X, screen +row is world -Y (into the
    frame). The sun bearing is measured from +Y toward +X.
    """
    el = math.radians(SUN_ELEV_DEG)
    az = math.radians(SUN_BEARING_DEG)
    dx = math.cos(el) * math.sin(az)
    dy = -math.cos(el) * math.cos(az)
    return (-dy, dx)


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(R2, "render/relief_control"))
    a = ap.parse_args(argv)

    G = load_gate()
    print(f">> imported relief_anisotropy from tools/item_gate.py")
    print(f">> RELIEF_MARGIN {G.RELIEF_MARGIN}  RELIEF_DIP_FLOOR "
          f"{G.RELIEF_DIP_FLOOR}  RELIEF_CONTROL_SANE {G.RELIEF_CONTROL_SANE}")

    sun_rc = sun_screen_dir()
    print(f">> sun screen dir (row, col) = ({sun_rc[0]:+.3f}, {sun_rc[1]:+.3f})")

    rows = []
    for name in ORDER:
        p = os.path.join(a.dir, name + ".png")
        if not os.path.exists(p):
            print(f"   (missing {name}.png)")
            continue
        lum, alpha = load_png(p)
        mask = alpha > 0.5
        if int(mask.sum()) < 5000:
            print(f"   ({name}: only {int(mask.sum())} subject px)")
            continue
        dip, detail = G.relief_anisotropy(lum, mask, sun_rc, r=2)
        rows.append((name, HEIGHT_MM[name], dip, detail, int(mask.sum())))

    print(f"\n{'panel':<18}{'height':>9}{'dip':>10}{'along':>9}{'across':>9}"
          f"{'lag':>6}{'px':>10}")
    for name, hmm, dip, detail, npx in rows:
        if dip is None:
            print(f"  {name:<16}{hmm:>8.1f}mm   NOT MEASURED "
                  f"({detail.get('reason')})")
            continue
        print(f"  {name:<16}{hmm:>8.1f}mm{dip:>10.4f}"
              f"{detail.get('dip_along', float('nan')):>9.4f}"
              f"{detail.get('dip_across', float('nan')):>9.4f}"
              f"{detail.get('best_lag_px', 0):>6}{npx:>10,}")

    d = {n: v for n, _h, v, _dd, _p in rows if v is not None}

    print("\n--- VERDICT ---")
    ok = True

    if "a_flat_0mm" in d and "d_rib_8mm" in d:
        found = d["d_rib_8mm"] - d["a_flat_0mm"]
        good = found > G.RELIEF_MARGIN
        ok &= good
        print(f"  8 mm ribs over flat plate      {found:+.4f}  "
              f"(needs > {G.RELIEF_MARGIN})  {'PASS' if good else '*** FAIL: '
              'the check is BLIND to real relief'}")

    if "f_printed_0mm" in d and "a_flat_0mm" in d:
        decoy = d["f_printed_0mm"] - d["a_flat_0mm"]
        good = decoy <= G.RELIEF_MARGIN
        ok &= good
        print(f"  printed decoy over flat plate  {decoy:+.4f}  "
              f"(needs <= {G.RELIEF_MARGIN})  {'PASS' if good else '*** FAIL: '
              'the check scores PAINT as RELIEF'}")

    if "f_printed_0mm" in d and "c_rib_2mm" in d:
        sep = d["c_rib_2mm"] - d["f_printed_0mm"]
        good = sep > 0.0
        ok &= good
        print(f"  2 mm ribs over printed decoy   {sep:+.4f}  "
              f"(needs > 0)          {'PASS' if good else '*** FAIL: cannot tell '
              'geometry from paint'}")

    ladder = [d.get(k) for k in ("a_flat_0mm", "b_rib_0p5mm", "c_rib_2mm",
                                 "d_rib_8mm")]
    if all(v is not None for v in ladder):
        mono = all(ladder[i] <= ladder[i + 1] + 1e-9 for i in range(3))
        ok &= mono
        print(f"  monotonic 0 -> 0.5 -> 2 -> 8 mm  "
              f"{[round(v,4) for v in ladder]}  "
              f"{'PASS' if mono else '*** FAIL: not monotonic in feature height'}")

    if "e_bolts_3mm" in d and "a_flat_0mm" in d:
        bolts = d["e_bolts_3mm"] - d["a_flat_0mm"]
        good = bolts > G.RELIEF_MARGIN
        ok &= good
        print(f"  3 mm chamfered bolts over flat {bolts:+.4f}  "
              f"(needs > {G.RELIEF_MARGIN})  {'PASS' if good else '*** FAIL: '
              'misses the exact feature marshal_post_deck was failed for'}")

    if not ok:
        print(">> 21 of the gate's 28 verdicts rest on this check. Do not trust "
              "them until this passes.")
    return gate_exit.verdict("RELIEF_CHECK_VALIDATED" if ok
                             else "RELIEF_CHECK_SUSPECT")


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised; guard() makes the verdict
    # main() returns the process status, and an exception a status 2.
    gate_exit.guard(main, tool="relief_control_measure")
