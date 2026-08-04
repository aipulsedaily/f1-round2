"""Measure the glass winding A/B. Numbers, not a look at the pictures.

    .venv/bin/python tools/glass_winding_ab_measure.py

Reads the seven renders and reports, for each comparison:
  * mean |delta| over the frame, in 8-bit levels
  * the fraction of pixels that move by more than 1, 2 and 8 levels
  * the same, restricted to each south pane's own screen-space quad, so the
    claim "exactly the six mis-wound panes changed" is a measurement and not an
    inference from a picture.

THE NULL IS THE UNIT.  A_CTL and D_NULL are the same wall, correctly wound, at
two different world offsets. Whatever they differ by is the floor; any other
comparison is only real if it clears it.
"""
import json, os, sys
import numpy as np
from PIL import Image

ROOT = "/home/zany/f1-round2"
R = os.path.join(ROOT, "render/glass_ab/renders")
W, H, SENSOR = 1600, 900, 36.0
F_SOUTH, F_EAST = 645, 863
OFFSETS = {"CTL": (0.0, 0.0, 0.0)}   # take 2: every variant at the same place


def load(tag):
    p = os.path.join(R, tag + ".png")
    if not os.path.exists(p):
        return None
    a = np.asarray(Image.open(p).convert("RGB"), dtype=np.float64)
    return a


def R_of(q):
    w, x, y, z = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w),   2*(x*z+y*w)],
                     [2*(x*y+z*w),   1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w),   2*(y*z+x*w),   1-2*(x*x+y*y)]])


def stats(a, b, mask=None):
    d = np.abs(a - b).max(axis=2)
    if mask is not None:
        d = d[mask]
    n = d.size
    return {"n_px": int(n), "px_changed": int((d > 0).sum()),
            "mean_levels": float(d.mean()),
            "p99_levels": float(np.percentile(d, 99)) if n else 0.0,
            "max_levels": float(d.max()) if n else 0.0,
            "frac_gt1": float((d > 1).mean()) if n else 0.0,
            "frac_gt2": float((d > 2).mean()) if n else 0.0,
            "frac_gt8": float((d > 8).mean()) if n else 0.0}


def row(name, s):
    print("  %-36s mean %8.5f  max %5.0f  px changed %9d  >1 %8d  >8 %8d"
          % (name, s["mean_levels"], s["max_levels"], s["px_changed"],
             int(round(s["frac_gt1"] * s["n_px"])),
             int(round(s["frac_gt8"] * s["n_px"]))))


# ---- pane screen-space quads, from the measured world geometry -------------- #
panes = {p["object"]: p for p in
         json.load(open(os.path.join(ROOT, "work/r2171_glass/glass_normals.json")))}
build = json.load(open(os.path.join(ROOT, "render/glass_ab/g_LIVE.json")))
shipped = {k: {"correct": v["shipped_outward"]}
           for k, v in build["south"].items()}
path = {int(k["f"]): k for k in
        json.load(open(os.path.join(ROOT, "render/film13_path.json")))["path"]}


def pane_mask(nm, frame, variant):
    p = panes[nm]
    off = np.array(OFFSETS["CTL"])
    lo, hi = np.array(p["bbox_min"]), np.array(p["bbox_max"])
    corners = np.array([[lo[0], lo[1], lo[2]], [hi[0], lo[1], lo[2]],
                        [hi[0], hi[1], hi[2]], [lo[0], hi[1], hi[2]]]) + off
    k = path[frame]
    c = np.array(k["p"]) + off
    Rm = R_of(k["q"]); fpx = k["lens"] / SENSOR * W
    L = (corners - c) @ Rm
    z = -L[:, 2]
    if (z <= 1e-4).any():
        return None
    u = fpx * L[:, 0] / z + W / 2.0
    v = -fpx * L[:, 1] / z + H / 2.0
    u0, u1 = int(max(0, np.floor(u.min()))), int(min(W, np.ceil(u.max())))
    v0, v1 = int(max(0, np.floor(v.min()))), int(min(H, np.ceil(v.max())))
    if u1 <= u0 or v1 <= v0:
        return None
    m = np.zeros((H, W), bool)
    m[v0:v1, u0:u1] = True
    return m


imgs = {t: load(t) for t in ("S_CTL_a", "S_CTL_b", "S_LIVE", "S_NEG",
                             "S_NOGLASS", "E_CTL_a", "E_CTL_b", "E_GPFLIP",
                             "E_NOGP")}
missing = [k for k, v in imgs.items() if v is None]
if missing:
    print("MISSING RENDERS: %s" % missing)
    print(">> STAGE RESULT: GLASS_AB_MEASURE_INCOMPLETE")
    sys.exit(1)

out = {}
print("SOUTH GLAZING -- the film's camera at frame %d (beat 1), 1600x900, "
      "1024 spp, no denoise, seed 0" % F_SOUTH)
print("  as shipped: %d of 14 panes wound INTO the building"
      % sum(0 if v["correct"] else 1 for v in shipped.values()))
null = stats(imgs["S_CTL_a"], imgs["S_CTL_b"])
row("NULL      CTL vs CTL re-render", null); out["south_null"] = null
sL = stats(imgs["S_LIVE"], imgs["S_CTL_a"])
row("SHIPPED   LIVE   vs CTL", sL); out["south_live_vs_ctl"] = sL
sN = stats(imgs["S_NEG"], imgs["S_CTL_a"])
row("POS CTRL  NEG    vs CTL", sN); out["south_neg_vs_ctl"] = sN
sX = stats(imgs["S_NOGLASS"], imgs["S_CTL_a"])
row("SENSITIVITY  no glass at all vs CTL", sX); out["south_noglass_vs_ctl"] = sX

print("\n  per pane (screen-space bbox of each pane at this camera):")
print("  %-22s %-9s %10s %10s %10s" % ("pane", "shipped", "null mean",
                                       "live mean", "allneg mean"))
per = {}
for nm in sorted(panes):
    if not nm.startswith("GW_Front_Glass"):
        continue
    m = pane_mask(nm, F_SOUTH, "CTL")
    if m is None or m.sum() < 200:
        continue
    a = stats(imgs["S_CTL_a"], imgs["S_CTL_b"], m)
    b = stats(imgs["S_LIVE"], imgs["S_CTL_a"], m)
    c = stats(imgs["S_NEG"], imgs["S_CTL_a"], m)
    tag = "OUTWARD" if shipped[nm]["correct"] else "INWARD"
    print("  %-22s %-9s %10.3f %10.3f %10.3f  (%d px)"
          % (nm, tag, a["mean_levels"], b["mean_levels"], c["mean_levels"],
             m.sum()))
    per[nm] = {"shipped_outward": shipped[nm]["correct"], "px": int(m.sum()),
               "null": a, "live_vs_ctl": b, "neg_vs_ctl": c}
out["south_per_pane"] = per

print("\nEAST WALL GP_b* -- 11.5 mm thick closed panes, film camera frame %d "
      "(last frame before the breach)" % F_EAST)
nullE = stats(imgs["E_CTL_a"], imgs["E_CTL_b"])
row("NULL      CTL vs CTL re-render", nullE); out["east_null"] = nullE
sF = stats(imgs["E_GPFLIP"], imgs["E_CTL_a"])
row("POS CTRL  GPFLIP vs CTL", sF); out["east_flip_vs_ctl"] = sF
sY = stats(imgs["E_NOGP"], imgs["E_CTL_a"])
row("SENSITIVITY  no panes at all vs CTL", sY); out["east_nogp_vs_ctl"] = sY

# ---- verdict --------------------------------------------------------------- #
# The null is the SAME blend re-rendered from the SAME camera at the SAME world
# coordinates, so it is not "small", it is the floor: 25 px of 1,440,000 at a
# maximum of one 8-bit level, which is the GPU's own non-determinism and nothing
# else. Against a floor that tight, "detectable" and "worth fixing" are two
# different questions, so they are asked separately and answered separately.
print("")
bad = []
DETECT = 10.0        # px changed must clear the null by this factor
for tag, null_, neg_, sens_ in (("SOUTH  zero-thickness panes", null, sN, sX),
                                ("EAST   11.5 mm closed panes", nullE, sF, sY)):
    print("%s" % tag)
    print("   NULL          CTL re-rendered           %9d px  max %3.0f levels"
          % (null_["px_changed"], null_["max_levels"]))
    print("   SENSITIVITY   delete the glass          %9d px  max %3.0f  "
          "mean %8.4f" % (sens_["px_changed"], sens_["max_levels"],
                          sens_["mean_levels"]))
    print("   POS CONTROL   invert every pane         %9d px  max %3.0f  "
          "mean %8.5f" % (neg_["px_changed"], neg_["max_levels"],
                          neg_["mean_levels"]))
    if sens_["px_changed"] < 0.5 * sens_["n_px"]:
        bad.append("%s: DELETING the glass changes only %d of %d px, so this "
                   "camera barely sees it and the winding test on it is "
                   "vacuous" % (tag, sens_["px_changed"], sens_["n_px"]))
    det = neg_["px_changed"] > DETECT * max(null_["px_changed"], 1)
    print("   -> winding is %s: %d px against a null of %d (x%.0f)"
          % ("DETECTABLE" if det else "NOT DETECTABLE ABOVE THE NULL",
             neg_["px_changed"], null_["px_changed"],
             neg_["px_changed"] / max(null_["px_changed"], 1)))
    if not det:
        bad.append("%s: inverting every pane does not clear the null; this "
                   "instrument cannot see winding here and no row above it "
                   "means anything" % tag)
    r = neg_["mean_levels"] / max(sens_["mean_levels"], 1e-12)
    print("   -> inverting the glass costs %.4f %% of what REMOVING it costs"
          % (100.0 * r))
    out[("south" if tag.startswith("SOUTH") else "east") + "_invert_vs_remove"] = float(r)
print("")
for b in bad:
    print("FAIL " + b)
print("SHIPPED SOUTH GLAZING vs the correctly-wound control: %d of %d px, "
      "max %.0f level, mean %.5f -- %.0fx the null"
      % (sL["px_changed"], sL["n_px"], sL["max_levels"], sL["mean_levels"],
         sL["px_changed"] / max(null["px_changed"], 1)))
out["verdict"] = {"south_live_vs_ctl_px": sL["px_changed"],
                  "south_neg_vs_ctl_px": sN["px_changed"],
                  "south_null_px": null["px_changed"],
                  "east_flip_vs_ctl_px": sF["px_changed"],
                  "east_null_px": nullE["px_changed"]}
json.dump(out, open(os.path.join(ROOT, "world/glass_ab_measured.json"),
                    "w"), indent=1)
print(">> STAGE RESULT: GLASS_AB_MEASURE_%s" % ("OK" if not bad else "FAIL"))
