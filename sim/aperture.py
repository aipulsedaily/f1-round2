"""THE APERTURE, AS A HOLE YOU COULD DRIVE THROUGH — not as a bbox of origins.

`build_breach_sim.aperture_report` takes the bounding box of the ORIGINS of the
shards that moved.  That measure has two failure modes and both of them fired:

  * it is a bbox, so one shard leaving from the top corner and one from the
    bottom corner report a 6 m aperture with 6 m of intact glass between them;
  * the fracture is radially graded, so 2,512 shards leaving can be a 3.9 x 1.8 m
    nucleus of small cells while every large cell above it stays put.

This measures the thing the camera sees: rasterise the wall plane at 25 mm,
mark each cell OCCUPIED by the shard polygon that covers it, clear the cells
whose shard has left, and take the LARGEST CONNECTED empty region.  That is a
hole.  Its bbox is then an honest bbox, because the region is connected.

CONTROLS (aperture_controls) — every one of them must fire:
  positive  every shard gone      -> hole == the full glazed area of the bays
  negative  no shard gone         -> hole == 0
  shape     a synthetic 3 x 2 m rectangle of gone shards -> 3 x 2 m recovered
  bbox-trap two lone opposite corners gone -> the OLD bbox measure reports the
            whole pane; this one reports two specks.  If that does not separate
            them the instrument is not measuring connectivity.
"""
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(R2, "sim") not in sys.path:
    sys.path.insert(0, os.path.join(R2, "sim"))

CELL_M = 0.025


def _rasterise(plan, cell=CELL_M, bays=None):
    """-> (owner grid, extent).  owner[i,j] = (bay, shard_index) or -1."""
    rects = plan["rects"]
    use = sorted(bays if bays is not None else rects)
    u0 = min(rects[b][0] for b in use)
    u1 = max(rects[b][1] for b in use)
    v0 = min(rects[b][2] for b in use)
    v1 = max(rects[b][3] for b in use)
    nu = int(np.ceil((u1 - u0) / cell))
    nv = int(np.ceil((v1 - v0) / cell))
    owner = np.full((nu, nv), -1, np.int32)
    key = []
    uu = u0 + (np.arange(nu) + 0.5) * cell
    vv = v0 + (np.arange(nv) + 0.5) * cell
    UU, VV = np.meshgrid(uu, vv, indexing="ij")
    for bay in use:
        for k, s in enumerate(plan["panes"].get(bay, [])):
            P = np.asarray(s["poly"], float)
            lo, hi = P.min(0), P.max(0)
            i0 = max(0, int((lo[0] - u0) / cell) - 1)
            i1 = min(nu, int((hi[0] - u0) / cell) + 2)
            j0 = max(0, int((lo[1] - v0) / cell) - 1)
            j1 = min(nv, int((hi[1] - v0) / cell) + 2)
            if i1 <= i0 or j1 <= j0:
                continue
            m = _inside(P, UU[i0:i1, j0:j1], VV[i0:i1, j0:j1])
            sub = owner[i0:i1, j0:j1]
            sub[m & (sub < 0)] = len(key)
            key.append((bay, s["id"]))
    return owner, key, (u0, u1, v0, v1), cell


def _inside(P, X, Y):
    """even-odd point-in-polygon, vectorised over a grid block."""
    n = len(P)
    inside = np.zeros(X.shape, bool)
    j = n - 1
    for i in range(n):
        xi, yi = P[i]
        xj, yj = P[j]
        cond = ((yi > Y) != (yj > Y))
        with np.errstate(divide="ignore", invalid="ignore"):
            xint = (xj - xi) * (Y - yi) / (yj - yi + 1e-300) + xi
        inside ^= cond & (X < xint)
        j = i
    return inside


def _largest_component(mask):
    """4-connected largest True component.  Iterative flood fill; no scipy."""
    nu, nv = mask.shape
    seen = np.zeros_like(mask)
    best = None
    best_n = 0
    for si in range(nu):
        for sj in range(nv):
            if not mask[si, sj] or seen[si, sj]:
                continue
            stack = [(si, sj)]
            seen[si, sj] = True
            comp = []
            while stack:
                i, j = stack.pop()
                comp.append((i, j))
                for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b = i + di, j + dj
                    if 0 <= a < nu and 0 <= b < nv and mask[a, b] \
                            and not seen[a, b]:
                        seen[a, b] = True
                        stack.append((a, b))
            if len(comp) > best_n:
                best_n, best = len(comp), comp
    return best or []


MUL_PITCH = 2.2            # mullion centres at y = -11.0 .. 11.0
MUL_Y0 = -11.0
SEG_H = 0.7745             # 8 segments over the 6.196 m storey


def _strip_mask(plan, owner, ext, cell, gone_mullions):
    """Un-glazed cells that a DEPARTED mullion segment used to fill.

    gone_mullions: set of (mullion_index, segment_index) that moved > 0.25 m.
    A mullion with one un-segmented body reports segment 0 for its whole height.
    """
    nu, nv = owner.shape
    u0, _, v0, _ = ext
    uu = u0 + (np.arange(nu) + 0.5) * cell
    vv = v0 + (np.arange(nv) + 0.5) * cell
    mi = np.rint((uu - MUL_Y0) / MUL_PITCH).astype(int)
    # segment index from the S00 centre 0.405 and 0.7745 pitch
    sj = np.clip(np.rint((vv - 0.405) / SEG_H).astype(int), 0, 7)
    out = np.zeros_like(owner, bool)
    ung = owner < 0
    for i in range(nu):
        if abs(uu[i] - (MUL_Y0 + mi[i] * MUL_PITCH)) > 0.5 * cell + 0.040:
            continue                      # not inside a 30 mm mullion strip
        for j in range(nv):
            if not ung[i, j]:
                continue
            if (mi[i], sj[j]) in gone_mullions:
                out[i, j] = True
    return out


def hole(plan, gone_ids, cell=CELL_M, bays=None, grid=None,
         gone_mullions=None):
    """gone_ids: set of (bay, shard_id) that have LEFT the wall.

    Returns TWO holes and they answer different questions:

      hole_*          the mullion strips between bays are OPAQUE.  A hole that
                      spans two bays is only connected if you ignore the
                      aluminium between them, and this number does not.
      hole_bridged_*  the strips are PASS-THROUGH.  This is the right number
                      exactly when the mullions in the span have themselves
                      left, which `mullion_intact.breach_state()` declares for
                      4, 5 and 6 — so the caller must say which it means.

    The declared 9.6 m spans four bays.  Neither number is the aperture on its
    own; quoting one without the mullion state is how a 13 m bbox got quoted
    off two shards.
    """
    if grid is None:
        grid = _rasterise(plan, cell, bays)
    owner, key, ext, cell = grid
    gone_cell = np.zeros(len(key) + 1, bool)
    for k, bs in enumerate(key):
        if bs in gone_ids:
            gone_cell[k] = True
    glazed = owner >= 0
    empty = glazed & gone_cell[np.clip(owner, 0, None)]
    a = cell * cell
    out = dict(cell_m=cell,
               glazed_area_m2=float(glazed.sum() * a),
               vacated_area_m2=float(empty.sum() * a),
               vacated_pct=float(100.0 * empty.sum() / max(1, glazed.sum())))
    passable = ~glazed
    if gone_mullions is not None:
        # A mullion strip is passable ONLY where its own segment has left.
        # Without this gate the strips form a continuous ladder up the whole
        # wall and the "bridged" hole reports 13.2 x 6.05 m with NOTHING gone.
        passable = _strip_mask(plan, owner, ext, cell, gone_mullions)
    for tag, mask in (("hole", empty), ("hole_bridged", empty | passable)):
        comp = _largest_component(mask)
        if not comp:
            out.update({tag + "_area_m2": 0.0, tag + "_w_m": 0.0,
                        tag + "_h_m": 0.0})
            continue
        ij = np.array(comp)
        u0, _, v0, _ = ext
        uu = u0 + ij[:, 0] * cell
        vv = v0 + ij[:, 1] * cell
        # area is always GLASS vacated, never the aluminium we bridged over
        garea = float(empty[ij[:, 0], ij[:, 1]].sum() * a)
        out.update({
            tag + "_area_m2": garea,
            tag + "_w_m": float(uu.max() - uu.min() + cell),
            tag + "_h_m": float(vv.max() - vv.min() + cell),
            tag + "_u": [float(uu.min()), float(uu.max() + cell)],
            tag + "_v": [float(vv.min()), float(vv.max() + cell)],
            tag + "_fill_pct": float(
                100.0 * len(comp) /
                max(1, ((uu.max() - uu.min()) / cell + 1) *
                    ((vv.max() - vv.min()) / cell + 1)))})
    return out


def old_bbox(plan, gone_ids):
    """The measure this replaces, so the two can be printed side by side."""
    us, vs = [], []
    for bay, ss in plan["panes"].items():
        for s in ss:
            if (bay, s["id"]) in gone_ids:
                c = s["centroid"]
                us.append(c[0])
                vs.append(c[1])
    if not us:
        return dict(width_m=0.0, height_m=0.0, n=0)
    return dict(width_m=float(max(us) - min(us)),
                height_m=float(max(vs) - min(vs)), n=len(us))


def aperture_controls(plan, bays=(2, 3, 4, 5, 6, 7), cell=0.05):
    """Four controls.  Two must pass, two must FAIL the old measure."""
    grid = _rasterise(plan, cell, bays)
    allid = set()
    for b in bays:
        for s in plan["panes"].get(b, []):
            allid.add((b, s["id"]))
    r = {}
    # positive: everything gone
    r["POS_all_gone"] = hole(plan, allid, cell, bays, grid)
    # negative: nothing gone
    r["NEG_none_gone"] = hole(plan, set(), cell, bays, grid)
    # shape: a synthetic 3 x 2 m window of shards
    rects = plan["rects"]
    uc = 0.5 * (rects[4][0] + rects[5][1])
    vc = 0.5 * (rects[4][2] + rects[4][3])
    win = set()
    for b in bays:
        for s in plan["panes"].get(b, []):
            c = s["centroid"]
            if abs(c[0] - uc) < 1.5 and abs(c[1] - vc) < 1.0:
                win.add((b, s["id"]))
    r["SHAPE_3x2m"] = hole(plan, win, cell, bays, grid)
    r["SHAPE_3x2m"]["old_bbox"] = old_bbox(plan, win)
    # bbox trap: two lone shards at opposite corners
    cor = []
    for b in bays:
        for s in plan["panes"].get(b, []):
            cor.append((b, s["id"], s["centroid"]))
    lo = min(cor, key=lambda t: t[2][0] + t[2][1])
    hi = max(cor, key=lambda t: t[2][0] + t[2][1])
    trap = {(lo[0], lo[1]), (hi[0], hi[1])}
    r["TRAP_two_corners"] = hole(plan, trap, cell, bays, grid)
    r["TRAP_two_corners"]["old_bbox"] = old_bbox(plan, trap)
    return r


if __name__ == "__main__":
    import json
    import fracture as FR
    plan = FR.load(os.path.join(R2, "sim/out/fracture_wall.npz"))
    print(json.dumps(aperture_controls(plan), indent=1))
