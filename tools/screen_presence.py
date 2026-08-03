"""MEASURED screen presence of the assembled world against the REAL camera.

    python3 tools/screen_presence.py --points <world_points.npz> \
        --out docs/screen_presence.json [--frames 1-2978] [--stride 1]

WHAT THIS REPLACES
------------------
`item_manifest.json.nearest_camera_m` is the minimum distance from a
RECONSTRUCTED camera corridor -- prose in `item_manifest.md` sec 1, no script,
unreproducible -- to an object whose position is recorded nowhere.  It contains
no information about whether the camera is POINTED at the thing, for how long,
how fast it crosses the frame, or whether anything is in front of it.

This measures those four quantities against `world/camera_rig_path.json`, the
2,978-sample per-frame path emitted by the rig build itself.

THE MEASUREMENT, AND EVERY ASSUMPTION IN IT
-------------------------------------------
1. CAMERA.  Per frame: world position, orientation quaternion and the EVALUATED
   focal length, read from the rig's own sampled path.  Blender convention: the
   camera looks down its local -Z with +Y up.  Sensor fit is AUTO on a 3840x2160
   frame, so the 36 mm sensor dimension is the HORIZONTAL one and the pixel
   scale is `s = 3840 * lens_mm / 36` pixels per unit of (x / depth).
   `depth` throughout is -Z in camera space -- the pinhole depth, which is what
   sets projected size -- NOT the radial distance the manifest used.

2. FRUSTUM.  A point is in frame when depth > 0 and its projection lands inside
   3840x2160.  This is the correction the scope plan predicted analytically:
   the manifest quotes size at closest approach, which for anything the camera
   PASSES is abeam, i.e. 63 degrees outside a 35 mm frame.

3. SIZE.  `px_per_metre = s / depth`.  An item of height h at that point
   subtends `h * px_per_metre` pixels of the 4K frame.

4. SMEAR.  Measured, not modelled: the same WORLD POINT is projected with the
   camera of frame f and of frame f+1, and the pixel displacement between the
   two is the screen-space motion the Vector pass would report.  Multiplied by
   the shutter.  Since R2-037 the shutter is a FLAT 180 degrees (0.5 of a
   frame) for the whole take and `--uniform-shutter` is the mode that ships:
   `build_camera_rig.py` used to key `0.5 * world_time_scale[f]`, which beat
   3's ramp took to 0.077, and that was a DOUBLE CORRECTION -- the world-time
   slowdown is already baked into the per-film-frame animation.  Without the
   flag this tool still reproduces the old ramped shutter, for the diff;
   `anim/filmtime.py` owns that mapping and is imported here rather than
   reimplemented.
   The world geometry is static, so all of this smear is camera motion; a moving
   subject (the car) is not measured by this tool and is not in the manifest.

5. OCCLUSION.  A depth buffer is rasterised from the point cloud itself at
   quarter resolution and each point is compared against it.  The point cloud is
   a surface sample at `cell_m` spacing, so the buffer has holes, and a hole can
   only let a hidden point through as visible.  **The occlusion figure is
   therefore a LOWER BOUND: `ever_unoccluded = False` is proof, `True` is not.**
   Stated because the reverse mistake -- treating an unproven pass as a pass --
   is R2-018 and R2-019 on this project.  A demotion made on it is safe in the
   same direction: ignoring occlusion can only overestimate visibility.

6. WHAT AN ITEM IS.  The assembled world contains 468 evaluated objects and
   28,313 vegetation instances.  **None of them is a manifest item.**  Items are
   features distributed over host geometry that the class-level placement
   systems built -- `armco_splice_bolt` lives wherever `BR_Armco_*` runs, and
   407 of the 435 have no module of their own yet at all.  So each item is
   mapped to a HOST SET of world objects by an explicit, auditable rule table
   (`hosts.py` alongside this file), and the item inherits the best moment any
   of its host surface ever has.  That is deliberately GENEROUS: an item cannot
   be seen better than its host, so every number here is an upper bound on the
   item, and a demotion taken against an upper bound is safe.
"""
import sys, os, json, time, argparse

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "anim"))
import filmtime as FT                                            # noqa: E402

RES_X, RES_Y = 3840, 2160
SENSOR_MM = 36.0
SMEAR_SHARP_PX = 6.0          # tools/item_gate.py's own hero resolve threshold
OCC_RES = 4                   # depth buffer is 1/4 linear -> 960 x 540
OCC_TOL_M = 0.75              # a point within this of the buffer counts as the front


# --------------------------------------------------------------------------
def camera_track(path_json):
    """(C, R, s, lens) per frame from the rig's own sampled path."""
    d = json.load(open(path_json))
    path = d["path"]
    n = len(path)
    C = np.array([p["p"] for p in path], dtype=np.float64)
    Q = np.array([p["q"] for p in path], dtype=np.float64)
    lens = np.array([p["lens"] for p in path], dtype=np.float64)
    # Blender quaternion (w, x, y, z) -> rotation matrix
    w, x, y, z = Q[:, 0], Q[:, 1], Q[:, 2], Q[:, 3]
    Rm = np.empty((n, 3, 3))
    Rm[:, 0, 0] = 1 - 2 * (y * y + z * z)
    Rm[:, 0, 1] = 2 * (x * y - z * w)
    Rm[:, 0, 2] = 2 * (x * z + y * w)
    Rm[:, 1, 0] = 2 * (x * y + z * w)
    Rm[:, 1, 1] = 1 - 2 * (x * x + z * z)
    Rm[:, 1, 2] = 2 * (y * z - x * w)
    Rm[:, 2, 0] = 2 * (x * z - y * w)
    Rm[:, 2, 1] = 2 * (y * z + x * w)
    Rm[:, 2, 2] = 1 - 2 * (x * x + y * y)
    s = RES_X * lens / SENSOR_MM
    return C, Rm, s, lens, n


def shutter_track(sheet_json, total_frames, base_shutter=0.5):
    sheet = json.load(open(sheet_json))
    scales, info = FT.build_time_map(sheet, total_frames)
    return np.array(scales) * base_shutter, info


def beat_of_frame(sheet_json, total_frames, fps=24):
    sheet = json.load(open(sheet_json))
    lab = np.empty(total_frames, dtype=object)
    lab[:] = "?"
    bounds = []
    for b in sheet["beats"]:
        f0 = int(round(b["start_s"] * fps)) + 1
        f1 = int(round((b["start_s"] + b["duration_s"]) * fps))
        f0 = max(1, f0); f1 = min(total_frames, f1)
        lab[f0 - 1:f1] = b["name"]
        bounds.append((b["name"], f0, f1))
    return lab, bounds


# --------------------------------------------------------------------------
def build_grid(pts, cell):
    q = np.floor(pts / cell).astype(np.int64)
    key = ((q[:, 0] + 200000) * 400000 + (q[:, 1] + 200000)) * 400000 + (q[:, 2] + 200000)
    order = np.argsort(key, kind="stable")
    ks = key[order]
    uniq, start = np.unique(ks, return_index=True)
    counts = np.diff(np.append(start, len(ks)))
    centres = (q[order[start]].astype(np.float64) + 0.5) * cell
    return order, start, counts, centres


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", required=True)
    ap.add_argument("--path", default=os.path.join(R2, "world/camera_rig_path.json"))
    ap.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--maxrange", type=float, default=1500.0)
    ap.add_argument("--gridcell", type=float, default=32.0)
    ap.add_argument("--npz", default="", help="also write the per-point arrays here")
    ap.add_argument("--uniform-shutter", action="store_true",
                    help="THE SHIPPING MODE since R2-037 was fixed. Use a flat "
                         "180-degree shutter (0.5 of a frame) for the whole take. "
                         "build_camera_rig.py used to scale the shutter with WORLD "
                         "time so the slowed car blurred correctly, but the camera "
                         "keeps flying in FILM time and the world is static, so beat "
                         "3's static geometry was blurred for 0.077 of a frame "
                         "instead of 0.5 -- 6.5x too crisp, and the slowdown was "
                         "applied twice. The rig now defaults to --shutter-mode flat; "
                         "pass this so the measurement matches. Omitting it "
                         "reproduces the old ramped shutter, which is only useful as "
                         "the other half of a diff.")
    a = ap.parse_args()

    t0 = time.time()
    z = np.load(a.points, allow_pickle=True)
    pts = z["pts"].astype(np.float64)
    obj = z["obj"]
    names = list(z["names"])
    meta = json.loads(str(z["meta"]))
    veg_origin = z["veg_origin"].astype(np.float64)
    veg_name = list(z["veg_name"])
    print(f"[SP] {len(pts)} evaluated points over {len(names)} objects; "
          f"{len(veg_origin)} vegetation instances", flush=True)

    # vegetation joins the cloud as one point per instance, labelled by family
    if len(veg_origin):
        fam = {}
        vlab = np.empty(len(veg_origin), dtype=np.int64)
        base = len(names)
        for i, nm in enumerate(veg_name):
            f = "_".join(str(nm).split("_")[:-1]) or str(nm)
            if f not in fam:
                fam[f] = base + len(fam)
                names.append(f)
            vlab[i] = fam[f]
        pts = np.vstack([pts, veg_origin])
        obj = np.concatenate([obj, vlab.astype(np.int32)])
        print(f"[SP] + {len(fam)} vegetation families -> {len(pts)} points", flush=True)

    npts = len(pts)
    # per-object surface sampling spacing, for the occlusion splat and for a
    # caller that wants to know how coarse this is
    spacing = np.full(len(names), meta["cell_m"], dtype=np.float64)
    for m in meta["objects"]:
        if m["name"] in names:
            i = names.index(m["name"])
            spacing[i] = meta["cell_m"] / max(1e-6, np.sqrt(m["keep_fraction"]))

    C, Rm, s, lens, nframes = camera_track(a.path)
    shutter, ramp_info = shutter_track(a.sheet, nframes)
    if a.uniform_shutter:
        shutter = np.full(nframes, 0.5)
    beats, bounds = beat_of_frame(a.sheet, nframes)
    print(f"[SP] camera {nframes} frames, lens {lens.min():.1f}-{lens.max():.1f} mm, "
          f"shutter {shutter.min():.4f}-{shutter.max():.4f}", flush=True)

    order, gstart, gcount, gcentre = build_grid(pts, a.gridcell)
    ncell = len(gcentre)
    cell_r = a.gridcell * 0.8660254         # half diagonal
    print(f"[SP] {ncell} grid cells of {a.gridcell} m", flush=True)

    # ---- per-point accumulators -----------------------------------------
    peak_ppm = np.zeros(npts, dtype=np.float32)          # best px per metre, in frame
    peak_f = np.zeros(npts, dtype=np.int32)
    sharp_ppm = np.zeros(npts, dtype=np.float32)         # ... and smear <= 6 px
    sharp_f = np.zeros(npts, dtype=np.int32)
    unocc_ppm = np.zeros(npts, dtype=np.float32)         # ... and in front of the z-buffer
    unocc_sharp_ppm = np.zeros(npts, dtype=np.float32)
    nvis = np.zeros(npts, dtype=np.int32)
    nunocc = np.zeros(npts, dtype=np.int32)
    mindepth = np.full(npts, np.inf, dtype=np.float32)
    first_f = np.zeros(npts, dtype=np.int32)
    last_f = np.zeros(npts, dtype=np.int32)
    beat_mask = np.zeros(npts, dtype=np.uint8)           # bit per beat
    bidx = {b[0]: i for i, b in enumerate(bounds)}

    # cell-level "ever in frustum at any range", full range, no occlusion
    cell_seen = np.zeros(ncell, dtype=bool)

    # ---- per-OBJECT x per-FRAME, so an item's frame count is exact ------
    # An item's hosts are a SET of objects, so "how many frames is this item on
    # screen" is a union over that set and cannot be recovered from per-point
    # totals. 520-ish objects x 2,978 frames x 4 bytes is 6 MB a plane.
    nobj = len(names)
    of_any = np.zeros((nobj, nframes), dtype=np.float32)      # max px/m, in frustum
    of_sharp = np.zeros((nobj, nframes), dtype=np.float32)    # ... and smear <= 6 px
    of_usharp = np.zeros((nobj, nframes), dtype=np.float32)   # ... and unoccluded
    of_flat = np.zeros((nobj, nframes), dtype=np.float32)     # ... x foreshortening
    of_depth = np.full((nobj, nframes), np.inf, dtype=np.float32)
    col = np.zeros(nobj, dtype=np.float32)
    cold = np.zeros(nobj, dtype=np.float32)

    ox, oy = RES_X / 2.0, RES_Y / 2.0
    ow, oh = RES_X // OCC_RES, RES_Y // OCC_RES
    frames = list(range(0, nframes, a.stride))
    t1 = time.time()
    ncand_total = 0

    for fi in frames:
        Cf, Rf, sf = C[fi], Rm[fi], s[fi]
        fj = min(fi + 1, nframes - 1)
        Cn, Rn, sn = C[fj], Rm[fj], s[fj]
        halfx = np.arctan(0.5 * SENSOR_MM / lens[fi])
        halfy = np.arctan(0.5 * SENSOR_MM * RES_Y / RES_X / lens[fi])
        half = max(halfx, halfy) * 1.4143            # circumscribing cone

        # --- cell cull ---------------------------------------------------
        d = gcentre - Cf
        rng = np.sqrt((d * d).sum(axis=1))
        fwd = -Rf[:, 2]
        along = d @ fwd
        # a cell is a candidate if any part of its sphere can be inside the cone
        cosang = np.divide(along, np.maximum(rng, 1e-9))
        ang = np.arccos(np.clip(cosang, -1, 1))
        margin = np.arcsin(np.clip(cell_r / np.maximum(rng, cell_r), -1, 1))
        keep = (along > -cell_r) & (ang - margin < half)
        cell_seen |= keep
        keep &= (rng < a.maxrange + cell_r)
        ci = np.nonzero(keep)[0]
        if len(ci) == 0:
            continue
        idx = np.concatenate([order[gstart[c]:gstart[c] + gcount[c]] for c in ci])
        ncand_total += len(idx)

        P = pts[idx] - Cf
        xc = P @ Rf[:, 0]; yc = P @ Rf[:, 1]; zc = P @ Rf[:, 2]
        depth = -zc
        ok = depth > 0.05
        if not ok.any():
            continue
        idx = idx[ok]; xc = xc[ok]; yc = yc[ok]; depth = depth[ok]
        px = ox + sf * xc / depth
        py = oy + sf * yc / depth
        inf = (px >= 0) & (px < RES_X) & (py >= 0) & (py < RES_Y) & (depth < a.maxrange)
        if not inf.any():
            continue
        idx = idx[inf]; px = px[inf]; py = py[inf]; depth = depth[inf]
        xc = xc[inf]; yc = yc[inf]

        # FORESHORTENING, for the 42 manifest items whose size is measured IN
        # PLANE (paint, joints, stains, paving bays) rather than as a height.
        # The manifest applies its px formula to an in-plane dimension with no
        # regard for the angle it is seen at, which for a road surface under a
        # camera 1.9 m up is the difference between a 1 m bay and a 5 cm one.
        # For a horizontal element the projected fraction is |n . vhat| with
        # n = +Z, i.e. |dz| / |P|.
        dist = np.sqrt(xc * xc + yc * yc + depth * depth)
        graze = np.abs(pts[idx][:, 2] - Cf[2]) / np.maximum(dist, 1e-6)

        # --- smear: the same world point through the NEXT frame's camera ---
        Pn = pts[idx] - Cn
        zn = -(Pn @ Rn[:, 2])
        zn = np.where(zn > 0.05, zn, 0.05)
        pxn = ox + sn * (Pn @ Rn[:, 0]) / zn
        pyn = oy + sn * (Pn @ Rn[:, 1]) / zn
        smear = shutter[fi] * np.hypot(pxn - px, pyn - py)

        ppm = (sf / depth).astype(np.float32)

        # --- occlusion: rasterise the cloud's own depth buffer ------------
        qx = np.clip((px / OCC_RES).astype(np.int32), 0, ow - 1)
        qy = np.clip((py / OCC_RES).astype(np.int32), 0, oh - 1)
        flat = qy * ow + qx
        buf = np.full(ow * oh, np.inf, dtype=np.float32)
        np.minimum.at(buf, flat, depth.astype(np.float32))
        front = depth <= buf[flat] + OCC_TOL_M

        # --- accumulate ---------------------------------------------------
        # `idx` holds each point at most once per frame, so plain fancy
        # indexing is correct here and ufunc.at (which is 20-50x slower) is not
        # needed. The z-buffer below is the one place duplicates are the point.
        f1 = fi + 1
        nvis[idx] += 1
        mindepth[idx] = np.minimum(mindepth[idx], depth.astype(np.float32))
        better = ppm > peak_ppm[idx]
        bi = idx[better]
        peak_ppm[bi] = ppm[better]; peak_f[bi] = f1
        sh = smear <= SMEAR_SHARP_PX
        if sh.any():
            i2 = idx[sh]; p2 = ppm[sh]
            b2 = p2 > sharp_ppm[i2]
            sharp_ppm[i2[b2]] = p2[b2]; sharp_f[i2[b2]] = f1
        if front.any():
            i3 = idx[front]; p3 = ppm[front]
            nunocc[i3] += 1
            b3 = p3 > unocc_ppm[i3]
            unocc_ppm[i3[b3]] = p3[b3]
            fs = front & sh
            if fs.any():
                i4 = idx[fs]; p4 = ppm[fs]
                b4 = p4 > unocc_sharp_ppm[i4]
                unocc_sharp_ppm[i4[b4]] = p4[b4]
        newf = first_f[idx] == 0
        first_f[idx[newf]] = f1
        last_f[idx] = f1
        beat_mask[idx] |= np.uint8(1 << bidx.get(beats[fi], 7))

        # --- per-object columns for this frame ----------------------------
        oi = obj[idx]
        col[:] = 0.0
        np.maximum.at(col, oi, ppm)
        of_any[:, fi] = col
        cold[:] = np.inf
        np.minimum.at(cold, oi, depth.astype(np.float32))
        of_depth[:, fi] = cold
        if sh.any():
            col[:] = 0.0
            np.maximum.at(col, oi[sh], ppm[sh])
            of_sharp[:, fi] = col
        fs2 = front & sh
        if fs2.any():
            col[:] = 0.0
            np.maximum.at(col, oi[fs2], ppm[fs2])
            of_usharp[:, fi] = col
            col[:] = 0.0
            np.maximum.at(col, oi[fs2], ppm[fs2] * graze[fs2].astype(np.float32))
            of_flat[:, fi] = col

        if fi % 250 == 0:
            print(f"[SP] frame {f1}/{nframes}  cand {len(idx)}  "
                  f"{time.time()-t1:.0f}s", flush=True)

    print(f"[SP] swept {len(frames)} frames in {time.time()-t1:.1f}s, "
          f"{ncand_total/1e6:.1f} M point-projections", flush=True)

    out = {
        "pts": pts.astype(np.float32), "obj": obj,
        "peak_ppm": peak_ppm, "peak_f": peak_f,
        "sharp_ppm": sharp_ppm, "sharp_f": sharp_f,
        "unocc_ppm": unocc_ppm, "unocc_sharp_ppm": unocc_sharp_ppm,
        "nvis": nvis, "nunocc": nunocc, "mindepth": mindepth,
        "first_f": first_f, "last_f": last_f, "beat_mask": beat_mask,
        "names": np.array(names, dtype=object),
        "cell_seen": cell_seen, "gcentre": gcentre,
        "spacing": spacing,
        "of_any": of_any, "of_sharp": of_sharp, "of_usharp": of_usharp,
        "of_flat": of_flat,
        "of_depth": np.where(np.isfinite(of_depth), of_depth, 0).astype(np.float32),
        "shutter": shutter.astype(np.float32), "lens": lens.astype(np.float32),
        "campos": C.astype(np.float32),
    }
    npz_path = a.npz or (os.path.splitext(a.out)[0] + "_points.npz")
    np.savez_compressed(npz_path, **out)
    print(f"[SP] wrote {npz_path} in {time.time()-t0:.1f}s total", flush=True)

    # per-object roll-up, so the raw measurement is readable without the npz
    rows = []
    for i, nm in enumerate(names):
        m = obj == i
        if not m.any():
            continue
        rows.append({
            "object": nm, "points": int(m.sum()),
            # FRAMES, from the per-object-per-frame plane. The first version of
            # this line counted POINTS with nvis>0 and called them frames, and
            # reported TER_Ground on 230,685 frames of a 2,978-frame film. A
            # number larger than its own maximum is the cheapest defect to
            # catch and it still needed catching.
            "frames_visible": int((of_any[i] > 0).sum()),
            "frames_sharp": int((of_sharp[i] > 0).sum()),
            "points_ever_in_frustum": int((nvis[m] > 0).sum()),
            "points_ever_unoccluded": int((nunocc[m] > 0).sum()),
            "min_depth_m": float(np.min(mindepth[m])) if np.isfinite(mindepth[m]).any() else None,
            "peak_px_per_m": float(peak_ppm[m].max()),
            "peak_sharp_px_per_m": float(sharp_ppm[m].max()),
            "peak_unocc_px_per_m": float(unocc_ppm[m].max()),
            "peak_unocc_sharp_px_per_m": float(unocc_sharp_ppm[m].max()),
            "peak_frame": int(peak_f[m][np.argmax(peak_ppm[m])]),
            "sharp_frame": int(sharp_f[m][np.argmax(sharp_ppm[m])]),
            "total_point_frames": int(nvis[m].sum()),
            "beats": sorted({b[0] for b in bounds
                             if (beat_mask[m] & np.uint8(1 << bidx[b[0]])).any()}),
        })
    json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "points_file": os.path.abspath(a.points),
               "camera_path": os.path.abspath(a.path),
               "frames": nframes, "stride": a.stride,
               "max_range_m": a.maxrange,
               "smear_sharp_px": SMEAR_SHARP_PX,
               # THE SHUTTER MODE, RECORDED. --uniform-shutter is the difference
               # between a flat 180 degrees and beat 3's ramp bottoming out at
               # 27.7 degrees, and it is what last moved the HERO count from 91
               # to 75. It was reconstructable only from the shutter array
               # buried in the npz, so two runs could differ by the single most
               # consequential flag this tool has and neither json would say so.
               "shutter_mode": "flat_180deg" if a.uniform_shutter else "world_time_ramped",
               "shutter_min": float(shutter.min()), "shutter_max": float(shutter.max()),
               "uniform_shutter_flag": bool(a.uniform_shutter),
               "point_cloud": {k: v for k, v in meta.items() if k != "objects"},
               "ramp": ramp_info,
               "objects": rows},
              open(a.out, "w"), indent=1)
    print(f"[SP] wrote {a.out}", flush=True)


if __name__ == "__main__":
    main()
