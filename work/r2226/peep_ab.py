"""Downscaled A/B peeps -- LOOK at the artefact, not only at the number."""
import os
import sys, json
import numpy as np
sys.path.insert(0, os.path.expanduser("~/f1-round2/world/items"))
import human_png as PNG

def down(a, k):
    h, w = a.shape[0] // k * k, a.shape[1] // k * k
    return a[:h, :w].reshape(h // k, k, w // k, k, 3).mean(axis=(1, 3)).astype(np.uint8)

def peep(tag, before, after, occ_json, frame, item, pad=90, k=2):
    o = json.load(open(occ_json))["frames"][str(frame)]["items"][item]
    bx = [u["box"] for u in o["units"] if u.get("in_frustum")]
    A = PNG.read(before); B = PNG.read(after)
    H, W = A.shape[:2]
    fb = [[b[0], H - b[3], b[2], H - b[1]] for b in bx]      # flip v
    x0 = max(0, int(min(b[0] for b in fb)) - pad); x1 = min(W, int(max(b[2] for b in fb)) + pad)
    y0 = max(0, int(min(b[1] for b in fb)) - pad); y1 = min(H, int(max(b[3] for b in fb)) + pad)
    print("%s crop x[%d %d] y[%d %d]  (%dx%d)" % (tag, x0, x1, y0, y1, x1-x0, y1-y0))
    for nm, img in (("before", A), ("after", B)):
        c = img[y0:y1, x0:x1, :3]
        while max(c.shape[0], c.shape[1]) > 1100:
            c = down(c, 2)
        PNG.write(os.path.expanduser("~/f1-round2/work/r2226/peep_%s_%s.png") % (tag, nm), c)
        print("   wrote peep_%s_%s.png  %s" % (tag, nm, c.shape))

peep("f654_crew", os.path.expanduser("~/f1-round2/work/r2226/f654_before.png"),
     os.path.expanduser("~/f1-round2/work/r2226/f654_after.png"),
     os.path.expanduser("~/f1-round2/work/r2226/after_verify.json"), 654, "crew_figure")
peep("f1126_ts", os.path.expanduser("~/f1-round2/work/r2226/f1126_before.png"),
     os.path.expanduser("~/f1-round2/work/r2226/f1126_after.png"),
     os.path.expanduser("~/f1-round2/work/r2226/after_verify.json"), 1126, "timing_stand")
print(">> STAGE RESULT: PEEP_OK")
