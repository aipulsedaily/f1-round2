"""Look at the rendered frames: is there a black line at the apron edge, is the
glass mouth still a black slot, and does the grass hold up at 1:1?

    .venv/bin/python imgprobe.py <mode> <args...>
"""
import sys, os, json
import numpy as np
from PIL import Image

OUT = os.path.expanduser("~/f1-round2/render/world/assembly/r2")


def load(p):
    im = Image.open(p)
    a = np.asarray(im.convert("RGB"), dtype=np.float64)
    if a.max() > 1.5:
        a = a / (65535.0 if im.mode.startswith("I") or a.max() > 255 else 255.0)
    return a


def lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def darkline(path, label):
    """Scan every image column for the darkest run of pixels and report how deep
    the darkest local minimum goes relative to its own neighbourhood.  A black
    construction joint shows up as a persistent dark ridge running across the
    frame; a correctly-closed joint does not."""
    a = load(path); L = lum(a)
    H, W = L.shape
    # local background = a 41 px vertical median, so a 1-3 px dark line is a
    # residual against the surface it sits in
    from numpy.lib.stride_tricks import sliding_window_view
    k = 41
    pad = np.pad(L, ((k // 2, k // 2), (0, 0)), mode="edge")
    med = np.median(sliding_window_view(pad, k, axis=0), axis=-1)
    resid = L - med
    dark = resid < -0.06
    # a joint is a long connected run: count per-row
    row_runs = dark.sum(axis=1)
    col_runs = dark.sum(axis=0)
    res = {"file": os.path.basename(path), "label": label, "size": [W, H],
           "mean_lum": round(float(L.mean()), 5),
           "p01_lum": round(float(np.percentile(L, 1)), 5),
           "min_lum": round(float(L.min()), 6),
           "pixels_below_0.02": int((L < 0.02).sum()),
           "pixels_below_0.05": int((L < 0.05).sum()),
           "dark_residual_pixels": int(dark.sum()),
           "dark_residual_pct": round(100.0 * dark.sum() / L.size, 4),
           "worst_row": int(row_runs.argmax()),
           "worst_row_dark_px": int(row_runs.max()),
           "worst_col": int(col_runs.argmax()),
           "worst_col_dark_px": int(col_runs.max()),
           "resid_min": round(float(resid.min()), 5)}
    return res


def band(path, y0, y1, x0, x1, label):
    a = load(path); L = lum(a)
    sub = L[y0:y1, x0:x1]
    return {"file": os.path.basename(path), "label": label,
            "box": [x0, y0, x1 - x0, y1 - y0],
            "mean": round(float(sub.mean()), 5),
            "min": round(float(sub.min()), 6),
            "p01": round(float(np.percentile(sub, 1)), 5),
            "p50": round(float(np.percentile(sub, 50)), 5),
            "below_15pct_of_p50": int((sub < 0.15 * np.percentile(sub, 50)).sum()),
            "pixels": int(sub.size)}


def detail(path, y0, y1, x0, x1, label):
    """local contrast / detail: what a 1:1 grass crop is actually judged on"""
    a = load(path); L = lum(a)
    sub = L[y0:y1, x0:x1]
    from numpy.lib.stride_tricks import sliding_window_view
    w = sliding_window_view(sub, (9, 9))
    loc = w.reshape(w.shape[0], w.shape[1], -1)
    sd = loc.std(axis=-1)
    mu = loc.mean(axis=-1)
    # zero crossings along scanlines = how many light/dark alternations
    d = np.diff(sub, axis=1)
    sgn = np.sign(d)
    cross = (np.diff(sgn, axis=1) != 0).sum() / max(1.0, sub.shape[0]) / \
        max(1.0, sub.shape[1] / 1000.0)
    return {"file": os.path.basename(path), "label": label,
            "box": [x0, y0, x1 - x0, y1 - y0],
            "mean": round(float(sub.mean()), 5),
            "local9x9_sigma": round(float(sd.mean()), 5),
            "local9x9_mean": round(float(mu.mean()), 5),
            "relative_contrast_pct": round(100.0 * float(sd.mean()) /
                                           max(1e-9, float(mu.mean())), 3),
            "crossings_per_1000px_scanline": round(float(cross), 2)}


def crop(path, out, x, y, w, h):
    im = Image.open(path).convert("RGB")
    im.crop((x, y, x + w, y + h)).save(out)
    print(">> crop", out, w, "x", h)


if __name__ == "__main__":
    m = sys.argv[1]
    if m == "darkline":
        print(json.dumps(darkline(sys.argv[2], sys.argv[3]), indent=1))
    elif m == "band":
        p, y0, y1, x0, x1, lab = sys.argv[2:8]
        print(json.dumps(band(p, int(y0), int(y1), int(x0), int(x1), lab), indent=1))
    elif m == "detail":
        p, y0, y1, x0, x1, lab = sys.argv[2:8]
        print(json.dumps(detail(p, int(y0), int(y1), int(x0), int(x1), lab), indent=1))
    elif m == "crop":
        crop(sys.argv[2], sys.argv[3], *[int(v) for v in sys.argv[4:8]])
    elif m == "stats":
        for p in sys.argv[2:]:
            a = load(p); L = lum(a)
            print("%-34s mean %.4f  sd %.4f  min %.5f  p01 %.4f  max %.4f  "
                  "black(<0.02) %d" % (os.path.basename(p), L.mean(), L.std(),
                                       L.min(), np.percentile(L, 1), L.max(),
                                       int((L < 0.02).sum())))
