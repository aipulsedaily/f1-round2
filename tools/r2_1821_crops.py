"""R2-1821: the before/after crops and the numbers beside them, at 1:1.

    .venv/bin/python tools/r2_1821_crops.py A.png B.png --out DIR [--label ...]

Cuts the SAME rectangles out of both arms at full delivered resolution, stacks them
one above the other, and writes the fine-detail sd of each crop into the file name --
so the picture and the number cannot drift apart between here and the report.

The rectangles are the client's own description, banded by distance from the pit wall,
because the whole finding is that the defect is a GRADIENT in that distance: R2-1661
scores 0.998 predicted cover at the far edge of this field and 0.058 against the wall.
A single crop of "the field" would average those and show a fix that half-worked.
"""
import sys, os, json, argparse
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r2_1821_ground_detail import luma, tile_sd, region_stat, TILE

Image.MAX_IMAGE_PIXELS = None

CROPS = {
    # name                       x     y     w    h
    "01_against_the_wall":    (2050, 1250, 900, 500),
    "02_mid_field":           (2450, 1400, 900, 620),
    "03_outer_field":         (2900, 1500, 900, 600),
    "04_along_the_wall":      (1500, 1450, 900, 650),
    "05_left_infield":        (  90,  540, 900, 260),
    "06_the_verge_and_beyond": (1150, 640, 900, 360),
}


def parse():
    p = argparse.ArgumentParser()
    p.add_argument("a"); p.add_argument("b")
    p.add_argument("--out", required=True)
    p.add_argument("--label", default="A|B")
    p.add_argument("--json", default=None)
    return p.parse_args()


def main():
    o = parse()
    os.makedirs(o.out, exist_ok=True)
    IA, IB = Image.open(o.a).convert("RGB"), Image.open(o.b).convert("RGB")
    if IA.size != IB.size:
        print(">> STAGE RESULT: R2_1821_CROPS_FAIL size %s vs %s" % (IA.size, IB.size))
        return
    LA, LB = luma(o.a), luma(o.b)
    SA, SB = tile_sd(LA), tile_sd(LB)
    la, lb = o.label.split("|")
    res = {}
    print("== 1:1 crops, %s vs %s, fine-detail sd in 8-bit levels ==" % (la, lb))
    print("%-26s %9s %9s %10s" % ("crop", la, lb, "change"))
    for nm, box in CROPS.items():
        ra, rb = region_stat(LA, SA, box), region_stat(LB, SB, box)
        x, y, w, h = box
        st = Image.new("RGB", (w, h * 2 + 8), (24, 24, 24))
        st.paste(IA.crop((x, y, x + w, y + h)), (0, 0))
        st.paste(IB.crop((x, y, x + w, y + h)), (0, h + 8))
        st.save(os.path.join(o.out, "%s__%s_%.2f__%s_%.2f.png"
                             % (nm, la, ra["sd"], lb, rb["sd"])))
        ch = ("%+.0f %%" % (100 * (rb["sd"] / ra["sd"] - 1))) if ra["sd"] > 0.05 else "n/a"
        print("%-26s %9.2f %9.2f %10s" % (nm, ra["sd"], rb["sd"], ch))
        res[nm] = dict(box=list(box), a=ra, b=rb)
    if o.json:
        json.dump(res, open(o.json, "w"), indent=1)
    print("crops written to %s  (top half = %s, bottom half = %s)" % (o.out, la, lb))
    print(">> STAGE RESULT: R2_1821_CROPS_OK")


main()
