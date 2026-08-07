#!/usr/bin/env python3
"""r2881_seat_window.py -- the material-PURE rectangles the seat A/B is judged on.

COMPUTED ONCE, FROM THE GEOMETRY, AND REUSED FOR BOTH ARMS.  A window picked by
eye off one of the two renders lets the arm choose the pixels that flatter it;
this raycasts the camera through every pixel of the crop, records which object
and which material each ray lands on, and then grows the largest axis-aligned
rectangle that is 100 % one material.  Neither render is opened.

It also emits a NEGATIVE CONTROL: the largest pure `LiveryPaint` rectangle in the
same crop.  Nothing in R2-881 touches `LiveryPaint`, so if the control moves by
more than the null, the difference measured on the seat is not the change.

    blender -b <look scene>.blend --factory-startup -noaudio \
        -P tools/r2881_seat_window.py -- --border 0.24 0.58 0.32 0.79 \
        --cam CAM_DRV_F2635 --out work/r2881_seat/windows.json
"""
import argparse, json, os, sys
import bpy
from mathutils import Vector

STEP = 4          # px between rays; the rectangle is grown on this lattice
MIN_W = MIN_H = 96


def log(*a):
    print("[window]", *a); sys.stdout.flush()


def cam_ray(scene, cam, u, v):
    """World origin + direction for normalised camera coords (u, v), v up."""
    d = cam.data
    W, H = scene.render.resolution_x, scene.render.resolution_y
    asp = W / float(H)
    sw = d.sensor_width
    # sensor_fit AUTO: the larger dimension takes sensor_width
    if asp >= 1.0:
        sx, sy = sw, sw / asp
    else:
        sx, sy = sw * asp, sw
    x = (u - 0.5) * sx
    y = (v - 0.5) * sy
    local = Vector((x, y, -d.lens))
    M = cam.matrix_world
    o = M.translation
    dirw = (M.to_3x3() @ local).normalized()
    return o, dirw


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--cam", required=True)
    ap.add_argument("--frame", type=int, default=2635)
    ap.add_argument("--border", type=float, nargs=4, required=True,
                    metavar=("MINX", "MAXX", "MINY", "MAXY"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    sc = bpy.context.scene
    sc.frame_set(a.frame)
    cam = bpy.data.objects[a.cam]
    sc.camera = cam
    dg = bpy.context.evaluated_depsgraph_get()
    W, H = sc.render.resolution_x, sc.render.resolution_y
    x0, x1, y0, y1 = a.border
    cw, ch = int(round((x1 - x0) * W)), int(round((y1 - y0) * H))
    log("crop %dx%d px from border %s at %s frame %d" % (cw, ch, a.border, a.cam, a.frame))

    nx, ny = cw // STEP, ch // STEP
    grid = [[None] * nx for _ in range(ny)]
    for j in range(ny):
        # image row j from the TOP; v is measured from the bottom
        v = y1 - (j * STEP + STEP * 0.5) / float(H)
        for i in range(nx):
            u = x0 + (i * STEP + STEP * 0.5) / float(W)
            o, d = cam_ray(sc, cam, u, v)
            hit, loc, nrm, idx, ob, mw = sc.ray_cast(dg, o, d)
            if not hit or ob is None:
                continue
            mat = None
            try:
                ev = ob.evaluated_get(dg)
                if ev.data.polygons and ev.material_slots:
                    mi = ev.data.polygons[idx].material_index
                    if mi < len(ev.material_slots) and ev.material_slots[mi].material:
                        mat = ev.material_slots[mi].material.name
            except Exception:
                pass
            grid[j][i] = (ob.name.split(".")[0], mat)

    from collections import Counter
    c = Counter(g for row in grid for g in row if g)
    log("what the crop is made of (top 14 of %d):" % len(c))
    for k, n in c.most_common(14):
        log("   %-34s %6d cells  %5.2f %%" % (k, n, 100.0 * n / (nx * ny)))

    out = {"border": a.border, "crop_w": cw, "crop_h": ch, "step": STEP,
           "frame": a.frame, "cam": a.cam, "windows": {},
           "composition": {"%s|%s" % k: n for k, n in c.most_common(40)}}

    # ---- the mask, which is what the measurement actually uses -------------
    # A RECTANGLE IS THE WRONG SHAPE HERE and the run above proves it: the seat
    # is crossed by four harness straps and the driver's arms, so the largest
    # 100 %-pure `CI_seat` rectangle in this crop is 36x68 px — too few pixels to
    # carry a band-pass statistic.  The mask keeps every pixel of the material
    # and the measure script erodes it by 12 px before reading, which is 3x the
    # widest Gaussian in the DoG ladder, so no band value it reports has seen a
    # pixel of anything else.  Same rigour, thirty times the sample.
    import numpy as np
    def _own(obj, mat):
        return lambda g, o=obj, m=mat: g[0] == o and g[1] == m
    groups = {
        # per OBJECT, not per material: the six shells sit at different angles to
        # the key and carry different amounts of crease, and pooling them hides
        # which of the four fixes did what.
        "CI_seat":        _own("CI_seat", "CarbonMatte"),
        "CI_liner":       _own("CI_liner", "CarbonMatte"),
        "CI_seatpad":     _own("CI_seatpad", "SuedeGrip"),
        "CI_sidehead":    _own("CI_sidehead", "SuedeGrip"),
        "CI_headrest":    _own("CI_headrest", "SuedeGrip"),
        "CI_harness_web": _own("CI_harness_web", "SuedeGrip"),
        # the monocoque's own CarbonMatte: the same material fix, on a part that
        # is NOT the seat.  A free second sample of the weave change.
        "MB_carbonmatte": _own("MB_chassis_cockpit", "CarbonMatte"),
        # NEGATIVE CONTROL — R2-881 does not touch LiveryPaint.
        "control_paint": lambda g: g[1] == "LiveryPaint",
    }
    names = list(groups)
    lab = np.zeros((ny, nx), dtype=np.uint8)          # 0 = none of them
    for j in range(ny):
        for i in range(nx):
            g = grid[j][i]
            if not g:
                continue
            for k, nm in enumerate(names):
                if groups[nm](g):
                    lab[j, i] = k + 1
                    break
    npz = os.path.splitext(os.path.abspath(a.out))[0] + "_mask.npz"
    np.savez_compressed(npz, labels=lab, step=STEP, crop_w=cw, crop_h=ch,
                        names=np.array(names))
    for k, nm in enumerate(names):
        n = int((lab == k + 1).sum())
        log("mask %-14s %6d lattice cells = %.2f %% of the crop"
            % (nm, n, 100.0 * n / (nx * ny)))
    log("wrote %s" % npz)
    out["mask_npz"] = npz
    out["mask_names"] = names

    def largest_rect(pred):
        """Maximal-area all-true axis-aligned rectangle, histogram method."""
        h = [0] * nx
        best = (0, None)
        for j in range(ny):
            for i in range(nx):
                h[i] = h[i] + 1 if (grid[j][i] and pred(grid[j][i])) else 0
            st = []
            for i in range(nx + 1):
                cur = h[i] if i < nx else 0
                start = i
                while st and st[-1][1] > cur:
                    s, hh = st.pop()
                    area = hh * (i - s)
                    if area > best[0]:
                        best = (area, (s, j - hh + 1, i - s, hh))
                    start = s
                st.append((start, cur))
        return best[1]

    wanted = {
        "seat_carbon": lambda g: g[0] == "CI_seat" and g[1] == "CarbonMatte",
        "seat_suede":  lambda g: g[0] in ("CI_seatpad", "CI_sidehead",
                                          "CI_headrest") and g[1] == "SuedeGrip",
        "webbing":     lambda g: g[0] == "CI_harness_web" and g[1] == "SuedeGrip",
        "control_paint": lambda g: g[1] == "LiveryPaint",
    }
    for nm, pred in wanted.items():
        r = largest_rect(pred)
        if r is None:
            log("%-14s NO PURE RECTANGLE" % nm)
            continue
        px = [r[0] * STEP, r[1] * STEP, r[2] * STEP, r[3] * STEP]
        if px[2] < MIN_W or px[3] < MIN_H:
            log("%-14s pure rect too small: %s px" % (nm, px))
        out["windows"][nm] = px
        log("%-14s x %4d y %4d w %4d h %4d  (%d px)"
            % (nm, px[0], px[1], px[2], px[3], px[2] * px[3]))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    log("wrote %s" % a.out)
    print(">> STAGE RESULT: R2881_WINDOWS_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
