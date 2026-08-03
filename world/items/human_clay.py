"""human_clay -- a dependency-free clay render of one figure, for LOOKING at.

WHY THIS EXISTS. `item_gate` renders its witness on the 5090 and the deliverable
macro goes the same way, but a GPU queue can be an hour deep and the question
"is this a person" is about GEOMETRY, which needs no path tracer to answer. This
projects the mesh through the item's own camera and z-buffers it in numpy, with
a Lambert term from the contract sun. No Cycles, no GPU, no dependency, seconds.

It is deliberately NOT a substitute for the macro. It has no shader, no shadow,
no bounce and no subsurface, so it cannot tell you whether the cloth reads as
cloth -- that is what `human_fabric_probe` and the witness frame are for. What
it CAN tell you, at the framing the film actually uses, is whether the head has
a face, whether the fingers separate, whether the prop is in the hand and
whether the silhouette is a person. Four of the ten measured defects are
silhouette-and-surface-normal defects and this sees all four.

    python3 world/items/human_clay.py --seed 20260802 --px 767 --out /tmp/clay
"""

import argparse
import math
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
for _p in (_HERE, _WORLD):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import human_png as HP                                          # noqa: E402
import humankit as HK                                           # noqa: E402
import world_contract as C                                      # noqa: E402


def triangles(fig):
    """The figure's mesh as one (T, 3, 3) array of world-space triangles, plus
    a material index per triangle."""
    m = fig["mesh"]
    V, Q, T, QM, TM, _A = m.finish()
    V = np.asarray(V, float)
    tris = []
    mats = []
    if len(Q):
        Q = np.asarray(Q, int)
        tris.append(V[Q[:, [0, 1, 2]]])
        tris.append(V[Q[:, [0, 2, 3]]])
        mats.append(np.asarray(QM, int))
        mats.append(np.asarray(QM, int))
    if len(T):
        T = np.asarray(T, int)
        tris.append(V[T])
        mats.append(np.asarray(TM, int))
    return np.concatenate(tris, 0), np.concatenate(mats, 0)


def render(fig, px_height=767.0, res=(900, 1400), az=206.0, el=6.0,
           lens_mm=35.0, mats_tint=True):
    """Z-buffered clay pass. Returns (H, W, 3) uint8.

    Orthographic in the plane of the figure -- at 8.5 m on a 35 mm lens the
    perspective divide across a 0.5 m deep body is 3 %, which is below the
    thing being looked at and buys a much simpler and much faster rasteriser.
    """
    P, MI = triangles(fig)
    a, e = math.radians(az), math.radians(el)
    view = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a),
                     math.sin(e)])
    right = np.array([-math.sin(a), math.cos(a), 0.0])
    up = np.cross(view, right)
    W, H = int(res[0]), int(res[1])
    lo = P.reshape(-1, 3).min(0)
    hi = P.reshape(-1, 3).max(0)
    ppm = px_height / max(hi[2] - lo[2], 1e-6)
    ctr = 0.5 * (lo + hi)
    X = (P @ right - ctr @ right) * ppm + W * 0.5
    Y = -((P @ up - ctr @ up) * ppm) + H * 0.5
    Z = P @ view
    N = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    ln = np.linalg.norm(N, axis=1)
    N = N / np.maximum(ln, 1e-12)[:, None]
    sun = np.array(C.SUN_DIR, float)
    sun = sun / np.linalg.norm(sun)
    lam = np.clip(N @ sun, 0.0, 1.0)
    amb = 0.28 + 0.30 * np.clip(N[:, 2], -1, 1) * 0.5 + 0.15
    shade = np.clip(0.20 + 0.95 * lam + 0.22 * amb, 0.0, 1.0)
    # a faint per-material tint so skin, cloth, hair and props separate by eye
    TINT = {HK.MAT_SKIN: (1.00, 0.86, 0.78), HK.MAT_TOP: (0.80, 0.84, 0.95),
            HK.MAT_LEG: (0.74, 0.76, 0.84), HK.MAT_HAIR: (0.55, 0.47, 0.42),
            HK.MAT_SHOE: (0.60, 0.58, 0.58), HK.MAT_SOLE: (0.72, 0.70, 0.68),
            HK.MAT_EYE: (0.35, 0.35, 0.38), HK.MAT_ACC: (0.92, 0.78, 0.55),
            HK.MAT_NAIL: (1.00, 0.92, 0.88)}
    tint = np.array([TINT.get(int(i), (0.85, 0.85, 0.85)) for i in MI]) \
        if mats_tint else np.ones((len(MI), 3))
    col = np.clip(shade[:, None] * tint, 0, 1)

    img = np.zeros((H, W, 3), np.float32)
    zbuf = np.full((H, W), 1e18)
    order = np.argsort(-Z.mean(1))            # far to near, painter + z test
    x0 = np.floor(X.min(1)).astype(int)
    x1 = np.ceil(X.max(1)).astype(int)
    y0 = np.floor(Y.min(1)).astype(int)
    y1 = np.ceil(Y.max(1)).astype(int)
    for t in order:
        if ln[t] < 1e-14:
            continue
        ax, bx, cx = X[t]
        ay, by, cy = Y[t]
        ix0 = max(0, x0[t]); ix1 = min(W - 1, x1[t])
        iy0 = max(0, y0[t]); iy1 = min(H - 1, y1[t])
        if ix1 < ix0 or iy1 < iy0:
            continue
        xs = np.arange(ix0, ix1 + 1)
        ys = np.arange(iy0, iy1 + 1)
        gx, gy = np.meshgrid(xs + 0.5, ys + 0.5)
        d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(d) < 1e-12:
            continue
        w0 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / d
        w1 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / d
        w2 = 1.0 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        z = Z[t].mean()
        sub = zbuf[iy0:iy1 + 1, ix0:ix1 + 1]
        hit = inside & (z < sub)
        if not hit.any():
            continue
        sub[hit] = z
        img[iy0:iy1 + 1, ix0:ix1 + 1][hit] = col[t]
    bg = 0.55
    img[zbuf > 1e17] = bg
    return (np.clip(img, 0, 1) * 255).astype(np.uint8), ppm


def main():
    p = argparse.ArgumentParser(prog="human_clay")
    p.add_argument("--seed", type=int, default=20260802)
    p.add_argument("--px", type=float, default=767.0)
    p.add_argument("--lod", default="L0")
    p.add_argument("--archetype", default=None)
    p.add_argument("--role", default="paddock")
    p.add_argument("--out", default="/tmp/clay")
    p.add_argument("--az", type=float, default=206.0)
    a = p.parse_args()
    lod = {"L0": HK.LOD_L0, "L1": HK.LOD_L1, "L2": HK.LOD_L2,
           "L3": HK.LOD_L3}[a.lod]
    fig = HK.build_figure(seed=a.seed, lod=lod, role=a.role,
                          archetype=a.archetype, adult_only=True)
    img, ppm = render(fig, px_height=a.px, az=a.az)
    os.makedirs(a.out, exist_ok=True)
    whole = os.path.join(a.out, "clay_whole.png")
    HP.write(whole, img)
    H, W = img.shape[:2]
    # head crop at 4x, which is where "is it a person" is actually decided
    top = int(H * 0.5 - a.px * 0.5)
    hh = int(a.px * 0.15)
    hc = img[max(0, top - 6):top + hh, W // 2 - hh // 2:W // 2 + hh // 2]
    HP.write(os.path.join(a.out, "clay_head.png"),
             np.repeat(np.repeat(hc, 4, 0), 4, 1))
    print("  seed %d  %s  %d tris  %s  %.0f px tall (%.1f px/m)  prop=%s"
          % (a.seed, fig["archetype"], fig["tris"], fig["body"].sex, a.px, ppm,
             fig.get("prop")))
    print("  wrote %s and clay_head.png (head band at 4x)" % whole)


if __name__ == "__main__":
    main()
