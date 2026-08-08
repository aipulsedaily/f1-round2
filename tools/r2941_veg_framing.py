"""R2-2941: WHAT PIXEL SIZE DOES A TREE ACTUALLY OCCUPY IN THIS FILM?

    python3 tools/r2941_veg_framing.py --out work/r2941/veg_framing.json
    python3 tools/r2941_veg_framing.py --selftest

WHY THIS EXISTS
---------------
`docs/WAVE2-RANKING.md` sec 3 ranks 11 trees as ranks 1-11, carrying 50.2 % of all
item screen presence, every one of them at a peak of 2160 px and every one of
them reporting the *identical* `min_depth_m` of 4.577 m.  Eleven independent
measurements do not agree to four decimal places.  That number is one shared
HOST's best moment inherited by eleven items that have no geometry of their own
in the host-resolution table (sec 2, weakness 1: "0 of 435 items resolve to a
host list containing their own geometry").

The one item where the framing was re-derived from the camera rather than
inherited -- `lighting_mast`, R2-1362 -- moved from a host-derived 7.602 m /
2160 px to a measured 84.18 m / 588 px.  **A 3.67x linear overstatement, up to
13x in a px^2 ranking statistic.**  WAVE2-RANKING sec 7 step 4 says to do the same
thing for the trees BEFORE building one, because it "gates the top 50 % of the
ranking".  This is that measurement.

WHAT IS DIFFERENT HERE FROM THE RANKING
---------------------------------------
The ranking asked "how big is this item's HOST".  This asks "how big is THIS
INSTANCE", because for vegetation the instances are the one class of thing in
this world whose own authored positions and bounding boxes ARE on disk:
`work/w2_0/retier_a10/world_points.npz` carries `veg_origin` (27,969 x 3),
`veg_bbox` (27,969 x 6) and `veg_name`, dumped from the assembled world.  No
host table is consulted and none is needed.

THE CAMERA IS RESOLVED, NOT NAMED
---------------------------------
Through `tools/live_campath.py`, which is the only thing allowed to answer
"which camera is live".  Note that this is `render/film19_path.json` -- the
ranking was measured against `film17_path.json`, which `docs/LIVE-CAMERA.md`
superseded on 2026-08-07 under R2-1701.  So the ranking is a measurement of a
camera the film no longer has, on top of everything else.

EVERY ASSUMPTION, STATED
------------------------
1. PROJECTION.  Blender convention, camera down local -Z, +Y up, sensor fit AUTO
   on 3840x2160 so the 36 mm dimension is HORIZONTAL.  `s = 3840 * lens / 36`;
   an object of height h at pinhole depth d subtends `h * s / d` pixels.  The
   maths is `screen_presence.camera_track`, IMPORTED, not retyped -- this file
   defines no sensor constant of its own.

2. IN FRAME.  The instance's bbox is projected as an axis-aligned world box; all
   eight corners are projected and the box counts as in frame when its projected
   rectangle overlaps 3840x2160 and its nearest corner has depth > 0.  Height in
   px is taken as the projected vertical extent, CLAMPED to the frame -- a tree
   that overfills is credited 2160 px and no more, which is what "peak px" means
   everywhere else in this campaign.

3. OCCLUSION IS NOT TESTED, DELIBERATELY.  This is an UPPER BOUND on how big a
   tree ever reads.  That is the safe direction for the decision it informs: if
   the upper bound is small, the tree tier's triangle crisis is an artifact and
   the finding is strong.  If the upper bound is large, this measurement has not
   settled anything and occlusion must be added before anyone builds to it.
   Saying which of those happened is this tool's actual output.

4. THE WORLD IS `assembly10`, THE CAMERA IS `film19`.  These are not the same
   pass.  Vegetation placement is authored by `world/build_terrain.py` from a
   fixed seed (`meta.seed`) and is not camera-dependent, so the mismatch does not
   affect WHERE the trees are; it is recorded in the output rather than argued
   away.

SELFTEST
--------
`--selftest` is not decoration.  It builds a synthetic camera and a synthetic
box at a known distance and checks the projected height against closed-form
`h * 3840 * lens / 36 / d`, and -- the arm that matters -- it checks that a box
placed BEHIND the camera and a box placed outside the frustum are both reported
as never in frame.  A visibility instrument that cannot say "no" is the defect
class this project keeps finding (R2-018, R2-019), so the negative arms are the
point and the tool exits non-zero if they do not fire.
"""
import argparse
import json
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "tools"))
import live_campath as LC                                        # noqa: E402
from screen_presence import camera_track, RES_X, RES_Y           # noqa: E402

POINTS_NPZ = os.path.join(R2, "work", "w2_0", "retier_a10", "world_points.npz")
ARCH_PY = os.path.join(R2, "world", "build_architecture.py")


def r1_shell():
    """The pavilion plan, READ from `build_architecture.py`'s own definition.

    `build_architecture` imports bpy at module scope, so it cannot be imported
    from bare python; the constant is lifted out of its AST instead.  That is
    still one definition with one owner -- the alternative is an eighth copy of
    a world constant, which is the defect this project logs most (R2-2177).
    """
    import ast
    tree = ast.parse(open(ARCH_PY).read())
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(
                getattr(t, "id", "") == "R1_SHELL" for t in n.targets):
            return tuple(ast.literal_eval(n.value))
    raise RuntimeError("R1_SHELL not found in %s -- refusing to guess" % ARCH_PY)


def camera_inside_pavilion(C, pad_m=3.0, roof_z=14.0):
    """Frames where the camera is under the round-1 pavilion shell.

    Vegetation is all outdoors, so for these frames an occlusion-free upper
    bound is not a bound on anything -- the shell is between them.  Proved
    rather than assumed: `work/r22161_proxy/r22161_proxy_000147.png` is the
    frame this tool nominated as the paddock avenue's 2600 px peak, and it is a
    wheel macro inside the showroom with no vegetation anywhere in it.
    """
    x0, x1, y0, y1 = r1_shell()
    return ((C[:, 0] > x0 - pad_m) & (C[:, 0] < x1 + pad_m)
            & (C[:, 1] > y0 - pad_m) & (C[:, 1] < y1 + pad_m)
            & (C[:, 2] < roof_z))

# The bands the campaign already speaks in (WAVE2-RANKING sec 2).
BANDS = (60, 150, 300)


def _corners(bbox):
    """(N,6) world aabb -> (N,8,3) corners."""
    lo, hi = bbox[:, :3], bbox[:, 3:]
    c = np.empty((bbox.shape[0], 8, 3), dtype=np.float64)
    k = 0
    for ix in (0, 1):
        for iy in (0, 1):
            for iz in (0, 1):
                c[:, k, 0] = hi[:, 0] if ix else lo[:, 0]
                c[:, k, 1] = hi[:, 1] if iy else lo[:, 1]
                c[:, k, 2] = hi[:, 2] if iz else lo[:, 2]
                k += 1
    return c


def measure(bbox, C, Rm, s, frame_chunk=64, near_m=0.05, fids=None):
    """Peak projected height in px per instance, and the frame/depth it happens at.

    Returns dict of arrays, all length N:
        peak_px, peak_frame, peak_depth_m, frames_ge_<band>, ever_in_frame
    """
    n = bbox.shape[0]
    nf = C.shape[0]
    if fids is None:
        fids = np.arange(1, nf + 1)
    corn = _corners(bbox)                                # (N,8,3)

    peak_px = np.zeros(n)
    peak_frame = np.full(n, -1, dtype=np.int64)
    peak_depth = np.full(n, np.inf)
    fcount = {b: np.zeros(n, dtype=np.int64) for b in BANDS}
    ever = np.zeros(n, dtype=bool)

    half_x, half_y = RES_X / 2.0, RES_Y / 2.0

    for f0 in range(0, nf, frame_chunk):
        f1 = min(nf, f0 + frame_chunk)
        for f in range(f0, f1):
            # world -> camera:  v = R^T (P - C)
            d = corn - C[f]                              # (N,8,3)
            v = d @ Rm[f]                                # R^T applied on the right
            depth = -v[:, :, 2]                          # (N,8)
            # A box straddling the camera plane is clamped, not dropped: any
            # corner in front is enough to be on screen.
            front = depth > near_m
            any_front = front.any(axis=1)
            if not any_front.any():
                continue
            dsafe = np.where(front, depth, np.nan)
            px = v[:, :, 0] * s[f] / dsafe
            py = v[:, :, 1] * s[f] / dsafe
            with np.errstate(invalid="ignore"):
                x0 = np.nanmin(px, axis=1); x1 = np.nanmax(px, axis=1)
                y0 = np.nanmin(py, axis=1); y1 = np.nanmax(py, axis=1)
            # Behind-camera corners make the projected box unbounded; when any
            # corner is behind, treat the box as spanning the frame horizontally
            # so we never drop a near overfilling tree.
            straddle = any_front & ~front.all(axis=1)
            x0 = np.where(straddle, -half_x, x0); x1 = np.where(straddle, half_x, x1)

            on = any_front & (x1 >= -half_x) & (x0 <= half_x) \
                           & (y1 >= -half_y) & (y0 <= half_y)
            if not on.any():
                continue
            h = np.clip(y1, -half_y, half_y) - np.clip(y0, -half_y, half_y)
            h = np.where(on, h, 0.0)
            ever |= on
            for b in BANDS:
                fcount[b] += (h >= b)
            better = h > peak_px
            peak_px = np.where(better, h, peak_px)
            peak_frame = np.where(better, fids[f], peak_frame)
            nd = np.where(front, depth, np.inf).min(axis=1)
            peak_depth = np.where(better, nd, peak_depth)

    out = {"peak_px": peak_px, "peak_frame": peak_frame,
           "peak_depth_m": peak_depth, "ever_in_frame": ever}
    for b in BANDS:
        out["frames_ge_%d" % b] = fcount[b]
    return out


def measure_segment(origin, zlo, zhi, C, Rm, s, near_m=0.05, fids=None):
    """Peak projected height of the tree as a VERTICAL SEGMENT at its own trunk.

    The aabb model above saturates: a median oak instance's world aabb is
    29.7 x 29.6 x 23.2 m, so its nearest corner is ~15 m closer than its trunk
    and every species clamps to 2160 px, which is the same uninformative answer
    the host-derived ranking gave.  This model is the one the campaign actually
    means by "peak px": the thing is `height_m` tall, it is at `depth` from the
    pinhole, it reads `height_m * s / depth` pixels.  It is what turned
    `lighting_mast` into 588 px at 84.18 m.

    Depth is measured to the TRUNK, which is the honest distance to the subject.
    """
    n = origin.shape[0]
    if fids is None:
        fids = np.arange(1, C.shape[0] + 1)
    h_m = zhi - zlo
    base = np.stack([origin[:, 0], origin[:, 1], zlo], axis=1)
    top = np.stack([origin[:, 0], origin[:, 1], zhi], axis=1)

    peak_px = np.zeros(n)
    peak_frame = np.full(n, -1, dtype=np.int64)
    peak_depth = np.full(n, np.inf)
    min_depth = np.full(n, np.inf)
    fcount = {b: np.zeros(n, dtype=np.int64) for b in BANDS}
    ever = np.zeros(n, dtype=bool)
    half_x, half_y = RES_X / 2.0, RES_Y / 2.0

    for f in range(C.shape[0]):
        vb_ = (base - C[f]) @ Rm[f]
        vt_ = (top - C[f]) @ Rm[f]
        db = -vb_[:, 2]
        dt = -vt_[:, 2]
        front = (db > near_m) & (dt > near_m)
        if not front.any():
            continue
        with np.errstate(divide="ignore", invalid="ignore"):
            xb = vb_[:, 0] * s[f] / db
            yb = vb_[:, 1] * s[f] / db
            yt = vt_[:, 1] * s[f] / dt
        y0 = np.minimum(yb, yt); y1 = np.maximum(yb, yt)
        on = front & (np.abs(xb) <= half_x) & (y1 >= -half_y) & (y0 <= half_y)
        if not on.any():
            continue
        h = np.where(on, y1 - y0, 0.0)
        h = np.minimum(h, RES_Y * 4.0)   # a segment through the lens is not a size
        ever |= on
        for b in BANDS:
            fcount[b] += (h >= b)
        d = np.where(on, db, np.inf)
        min_depth = np.minimum(min_depth, d)
        better = h > peak_px
        peak_px = np.where(better, h, peak_px)
        peak_frame = np.where(better, fids[f], peak_frame)
        peak_depth = np.where(better, d, peak_depth)

    out = {"peak_px": peak_px, "peak_frame": peak_frame,
           "peak_depth_m": peak_depth, "min_depth_m": min_depth,
           "height_m": h_m, "ever_in_frame": ever}
    for b in BANDS:
        out["frames_ge_%d" % b] = fcount[b]
    return out


def species_of(name):
    """'VEG_tree_oak0_000123' -> 'tree_oak'; 'VEG_sapling_0007' -> 'sapling'."""
    s = str(name)
    if s.startswith("VEG_"):
        s = s[4:]
    # strip the trailing instance index
    parts = s.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        s = parts[0]
    # strip a trailing LOD digit welded to the species key ("tree_oak0")
    if s and s[-1].isdigit():
        s = s[:-1]
    return s.rstrip("_")


def _selftest():
    """Closed-form arm plus two negative arms that MUST fire."""
    ok, fails = 0, []

    def chk(name, cond, detail=""):
        nonlocal ok
        if cond:
            ok += 1
            print("  ok   %s %s" % (name, detail))
        else:
            fails.append(name)
            print("  FAIL %s %s" % (name, detail))

    lens = 35.0
    s = np.array([RES_X * lens / 36.0])
    C = np.array([[0.0, 0.0, 0.0]])
    # identity rotation: Blender camera looks down -Z
    Rm = np.eye(3)[None, :, :]

    # arm 1 -- a 10 m tall, thin box centred on the axis at 100 m depth
    d = 100.0
    bb = np.array([[-0.05, -5.0, -d - 0.05, 0.05, 5.0, -d + 0.05]])
    r = measure(bb, C, Rm, s)
    want = 10.0 * RES_X * lens / 36.0 / d
    got = r["peak_px"][0]
    chk("closed_form_height", abs(got - want) < 0.5,
        "got %.2f px want %.2f px" % (got, want))
    chk("closed_form_depth", abs(r["peak_depth_m"][0] - (d - 0.05)) < 0.2,
        "got %.3f m" % r["peak_depth_m"][0])

    # arm 2 (NEGATIVE) -- the same box BEHIND the camera
    bb_b = np.array([[-0.05, -5.0, d - 0.05, 0.05, 5.0, d + 0.05]])
    rb = measure(bb_b, C, Rm, s)
    chk("negative_behind_camera", (not rb["ever_in_frame"][0]) and rb["peak_px"][0] == 0.0,
        "ever=%s peak=%.2f" % (rb["ever_in_frame"][0], rb["peak_px"][0]))

    # arm 3 (NEGATIVE) -- in front but far outside the horizontal frustum.
    # half-angle: x/depth = 18/lens = 0.5143 ; put it at 5x that.
    off = 5.0 * (18.0 / lens) * d
    bb_o = np.array([[off - 0.05, -5.0, -d - 0.05, off + 0.05, 5.0, -d + 0.05]])
    ro = measure(bb_o, C, Rm, s)
    chk("negative_outside_frustum", (not ro["ever_in_frame"][0]) and ro["peak_px"][0] == 0.0,
        "ever=%s peak=%.2f" % (ro["ever_in_frame"][0], ro["peak_px"][0]))

    # arm 4 -- clamping: a box that overfills is credited RES_Y and no more
    bb_n = np.array([[-0.05, -50.0, -2.05, 0.05, 50.0, -1.95]])
    rn = measure(bb_n, C, Rm, s)
    chk("overfill_clamped_to_frame", abs(rn["peak_px"][0] - RES_Y) < 1e-6,
        "got %.1f px" % rn["peak_px"][0])

    # arm 5 (NEGATIVE control on the control) -- if clamping were absent arm 4
    # would read far above RES_Y; prove the unclamped value really is bigger,
    # so arm 4 is not passing vacuously on a small box.
    raw = 100.0 * RES_X * lens / 36.0 / 2.0
    chk("overfill_arm_is_not_vacuous", raw > RES_Y * 10,
        "unclamped would be %.0f px" % raw)

    # ---- the segment model, which is the one that ships -------------------
    # The segment is vertical in WORLD z, so the identity camera (looking down
    # world -Z) would be staring at the top of it.  Pitch the camera 90 deg so
    # it looks along world +Y with world +Z up -- a normal standing camera.
    ang = np.deg2rad(90.0)
    Rw = np.array([[[1, 0, 0],
                    [0, np.cos(ang), -np.sin(ang)],
                    [0, np.sin(ang), np.cos(ang)]]])
    o2 = np.array([[0.0, d, 0.0]])
    rs = measure_segment(o2, np.array([-5.0]), np.array([5.0]), C, Rw, s)
    want_s = 10.0 * RES_X * lens / 36.0 / d
    chk("segment_closed_form", abs(rs["peak_px"][0] - want_s) < 1.0,
        "got %.2f px want %.2f px" % (rs["peak_px"][0], want_s))
    chk("segment_depth_is_to_trunk", abs(rs["peak_depth_m"][0] - d) < 0.01,
        "got %.3f m" % rs["peak_depth_m"][0])

    # arm S2 (NEGATIVE) -- trunk behind the camera
    o3 = np.array([[0.0, -d, 0.0]])
    rs3 = measure_segment(o3, np.array([-5.0]), np.array([5.0]), C, Rw, s)
    chk("segment_negative_behind", (not rs3["ever_in_frame"][0]) and rs3["peak_px"][0] == 0.0,
        "ever=%s peak=%.2f" % (rs3["ever_in_frame"][0], rs3["peak_px"][0]))

    # arm S3 (NEGATIVE) -- trunk in front but far outside the horizontal frustum
    o4 = np.array([[5.0 * (18.0 / lens) * d, d, 0.0]])
    rs4 = measure_segment(o4, np.array([-5.0]), np.array([5.0]), C, Rw, s)
    chk("segment_negative_offaxis", (not rs4["ever_in_frame"][0]) and rs4["peak_px"][0] == 0.0,
        "ever=%s peak=%.2f" % (rs4["ever_in_frame"][0], rs4["peak_px"][0]))

    # arm S4 -- the two models must DISAGREE on an inflated aabb, or the
    # segment model is not doing the thing it was added to do.
    bb_wide = np.array([[-15.0, d - 15.0, -5.0, 15.0, d + 15.0, 5.0]])
    ra = measure(bb_wide, C, Rw, s)
    chk("segment_disagrees_with_aabb", ra["peak_px"][0] > rs["peak_px"][0] * 1.10,
        "aabb %.1f px vs segment %.1f px (%.2fx)"
        % (ra["peak_px"][0], rs["peak_px"][0], ra["peak_px"][0] / rs["peak_px"][0]))

    # arm 6 -- species_of
    chk("species_of", species_of("VEG_tree_oak0_000123") == "tree_oak"
        and species_of("VEG_sapling_000001") == "sapling",
        "%s / %s" % (species_of("VEG_tree_oak0_000123"), species_of("VEG_sapling_000001")))

    print(">> STAGE RESULT: %s (%d/%d)"
          % ("SELFTEST_PASS" if not fails else "SELFTEST_FAIL", ok, ok + len(fails)))
    return 0 if not fails else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", default=POINTS_NPZ)
    ap.add_argument("--out", default=os.path.join(R2, "work", "r2941", "veg_framing.json"))
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--model", choices=("segment", "aabb"), default="segment",
                    help="segment = trunk height at trunk depth (ships); "
                         "aabb = world bounding box, a loose upper bound")
    ap.add_argument("--exclude-pavilion", action="store_true",
                    help="drop frames where the camera is inside the round-1 "
                         "pavilion; outdoor vegetation is occluded by the shell")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return _selftest()

    campath = LC.declared_campath()
    C, Rm, s, lens, nf = camera_track(campath)
    excluded = 0
    fids = np.arange(1, nf + 1)
    if a.exclude_pavilion:
        keep = ~camera_inside_pavilion(C)
        fids = fids[keep]
        excluded = int((~keep).sum())
        C, Rm, s, lens = C[keep], Rm[keep], s[keep], lens[keep]
        print("excluded %d of %d frames: camera inside the pavilion shell"
              % (excluded, nf))
    if a.stride > 1:
        C, Rm, s, lens = C[::a.stride], Rm[::a.stride], s[::a.stride], lens[::a.stride]
        fids = fids[::a.stride]

    z = np.load(a.points, allow_pickle=True)
    vb = np.asarray(z["veg_bbox"], dtype=np.float64)
    vn = z["veg_name"]
    meta = json.loads(str(z["meta"]))

    print("camera   %s  (%d frames, stride %d)" % (campath, nf, a.stride))
    print("world    %s" % meta.get("blend"))
    print("instances %d" % vb.shape[0])

    vo = np.asarray(z["veg_origin"], dtype=np.float64)
    if a.model == "aabb":
        r = measure(vb, C, Rm, s, fids=fids)
    else:
        r = measure_segment(vo, vb[:, 2], vb[:, 5], C, Rm, s, fids=fids)

    spec = np.array([species_of(n) for n in vn])
    heights = vb[:, 5] - vb[:, 2]

    rows = []
    for sp in sorted(set(spec.tolist())):
        m = spec == sp
        pk = r["peak_px"][m]
        seen = r["ever_in_frame"][m]
        md = r.get("min_depth_m", r["peak_depth_m"])[m]
        md = md[np.isfinite(md)]
        rows.append({
            "species": sp,
            "instances": int(m.sum()),
            "typical_height_m": round(float(np.median(heights[m])), 3),
            "ever_in_frame": int(seen.sum()),
            "peak_px": round(float(pk.max()), 1),
            "peak_px_p50_of_seen": round(float(np.median(pk[seen])), 1) if seen.any() else 0.0,
            "peak_frame": int(r["peak_frame"][m][int(np.argmax(pk))]),
            "depth_at_peak_m": round(float(r["peak_depth_m"][m][int(np.argmax(pk))]), 3),
            "min_depth_m": round(float(md.min()), 3) if md.size else None,
            "instance_frames_ge_60": int(r["frames_ge_60"][m].sum()),
            "instance_frames_ge_150": int(r["frames_ge_150"][m].sum()),
            "instance_frames_ge_300": int(r["frames_ge_300"][m].sum()),
        })
    rows.sort(key=lambda q: -q["peak_px"])

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump({
        "generated_by": "tools/r2941_veg_framing.py",
        "camera": campath,
        "camera_sha_declared_in": "docs/LIVE-CAMERA.md",
        "world_points": a.points,
        "world_blend": meta.get("blend"),
        "model": a.model,
        "frames_excluded_camera_inside_pavilion": excluded,
        "occlusion_tested": False,
        "reading": "UPPER BOUND on projected height; no occlusion, no atmosphere",
        "stride": a.stride,
        "species": rows,
    }, open(a.out, "w"), indent=1)

    w = max(len(q["species"]) for q in rows)
    print("\nmodel=%s\n%-*s %8s %9s %9s %9s %8s %8s %8s" %
          (a.model, w, "species", "inst", "peak_px", "depth_m", "mindep_m", "f>=60", "f>=150", "f>=300"))
    for q in rows:
        print("%-*s %8d %9.1f %9.2f %9.2f %8d %8d %8d" %
              (w, q["species"], q["instances"], q["peak_px"], q["depth_at_peak_m"],
               q["min_depth_m"] if q["min_depth_m"] is not None else -1,
               q["instance_frames_ge_60"], q["instance_frames_ge_150"],
               q["instance_frames_ge_300"]))
    print("\nwrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
