#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2651_line_dump.py — publish the driven line and the usage fields as data.

`build_surface.racing_line_offset(s)` is the single thing that decides WHERE the
rubber is painted, and it exists only inside a Blender process. Nothing can check
it against the telemetry, against the delivered frames, or against the car's own
animation while it lives there. This dumps it, plus the four usage fields the
material reads (`rubber`, `spread`, `brake`, `polish`), on the module's own
0.25 m field grid.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/r2651_line_dump.py -- --out=render/r2651/line.json

Judge on the printed STAGE RESULT line.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))

TOKEN_OK = "R2651_LINE_DUMP_OK"


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = os.path.join(ROOT, "render/r2651/line.json")
    for a in argv:
        if a.startswith("--out="):
            out = os.path.join(ROOT, a.split("=", 1)[1])

    import build_surface as B
    import world_contract as C

    B.prepare()

    g = B._fgrid()
    line = B._S["line"]
    data = dict(
        s=[round(float(v), 4) for v in g],
        line=[round(float(v), 5) for v in line],
        rubber=[round(float(v), 5) for v in B._S["rubber"]],
        spread=[round(float(v), 5) for v in B._S["spread"]],
        brake=[round(float(v), 5) for v in B._S["brake"]],
        polish=[round(float(v), 5) for v in B._S["polish"]],
        speed=[round(float(v), 4) for v in B._S["speed"]],
        half_width=[round(float(C.half_width(float(v))), 5) for v in g],
        verge_edge=[round(float(C.verge_edge(float(v))), 5) for v in g],
        meta=dict(lap=float(C.LAP), ds=float(g[1] - g[0]),
                  line_min_radius=float(B._S.get("line_min_radius", -1)),
                  line_lat_g_max=float(B._S.get("line_lat_g_max", -1))),
    )
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(data, open(out, "w"))

    print(">> line offset  min %+.3f  max %+.3f m   |u| p50 %.3f"
          % (line.min(), line.max(), float(np.median(np.abs(line)))))
    print(">> rubber  %.3f .. %.3f    spread  %.3f .. %.3f m"
          % (min(data["rubber"]), max(data["rubber"]),
             min(data["spread"]), max(data["spread"])))
    print(">> wrote %d stations -> %s" % (len(g), out))
    print(">> STAGE RESULT: %s" % TOKEN_OK)


main()
