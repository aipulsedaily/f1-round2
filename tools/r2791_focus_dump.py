"""Dump beat 1's ACTUAL focus/aperture curve from the SHIPPING blend, plus what
the focal plane is actually sitting on.

    ./rq exec --root ~/f1-round2 --closure \
        --include 'docs/explode_plan.json' --include 'docs/beat_sheet.json' \
        --scene render/film16_breach.blend \
        --entry tools/r2791_focus_dump.py \
        --arg --scene --arg scene.blend --arg --out --arg out/focusdump.json \
        --output focusdump.json --timeout 3600

`work/b1dof/dump.json` is from `render/film14.blend` and its camera POSITIONS
are stale: film16's beat-1 tour was re-stationed by the R2-451/R2-464 re-aim
(f1-f592 differ; the protected close-out f648-792 is identical). Any focus
verdict computed on that dump is a verdict about a camera that is not shipping.

Three things are recorded that the film14 dump does not have:

 1. THE RAW F-CURVES for `focus_distance` and `aperture_fstop` -- key
    coordinates, handles and interpolation, over all 2978 frames. The per-frame
    sample cannot tell you whether a value is a KEY or an INTERPOLATION, and the
    difference is the whole question: a focus that is right at 16 stations and
    wrong between them is a keying defect, not a taste call.

 2. A CENTRE-OF-FRAME RAYCAST per frame -- 9 rays over the central 20% of the
    frame. This says what the lens is POINTED AT, in metres, independently of
    any schedule. It is the reference that survives a re-time, because it is
    read off the camera's own aim rather than off a frame number.

 3. A RAYCAST TO THE FOCAL PLANE -- is there any geometry at `focus_distance`
    along the view axis at all? This separates "the focus is tracking something
    real that is not the subject" from "the focus is tracking nothing".

Blender 5.2 exits 0 on an uncaught exception. Judge on STAGE RESULT only.
"""

import json
import math
import os
import sys
import traceback

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default


def find(rel):
    """Data file, wherever the bundle put it."""
    for base in (ROOT, HERE, os.getcwd()):
        p = os.path.join(base, rel)
        if os.path.exists(p):
            return p
    raise IOError("cannot find %s (looked under %s)" % (rel, [ROOT, HERE, os.getcwd()]))


def dump_fcurves(id_data, label):
    """Every key of every DOF/lens channel, with handles and interpolation."""
    out = {}
    ad = getattr(id_data, "animation_data", None)
    if ad is None:
        return out
    actions = []
    if ad.action:
        actions.append(("action:" + ad.action.name, ad.action))
    for tr in ad.nla_tracks:
        for st in tr.strips:
            if st.action:
                actions.append(("nla:%s:%s" % (tr.name, st.name), st.action))
    for aname, act in actions:
        # Blender 4.4+/5.x: channels may live in slotted layers.
        curves = list(getattr(act, "fcurves", []) or [])
        if not curves:
            for lay in getattr(act, "layers", []) or []:
                for strip in getattr(lay, "strips", []) or []:
                    for cb in getattr(strip, "channelbags", []) or []:
                        curves.extend(list(cb.fcurves))
        for fc in curves:
            key = "%s|%s|%s[%d]" % (label, aname, fc.data_path, fc.array_index)
            out[key] = {
                "extrapolation": fc.extrapolation,
                "n_keys": len(fc.keyframe_points),
                "keys": [{
                    "f": round(k.co[0], 4),
                    "v": round(k.co[1], 6),
                    "interp": k.interpolation,
                    "hl": [round(k.handle_left[0], 4), round(k.handle_left[1], 6)],
                    "hr": [round(k.handle_right[0], 4), round(k.handle_right[1], 6)],
                    "hlt": k.handle_left_type,
                    "hrt": k.handle_right_type,
                } for k in fc.keyframe_points],
            }
    return out


def main():
    scene_path = arg("--scene")
    out_path = arg("--out", "out/focusdump.json")
    lo = int(arg("--first", "1"))
    hi = int(arg("--last", "820"))
    geom_step = int(arg("--geom-step", "4"))
    cam_name = arg("--cam", "ONER")

    if scene_path:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(scene_path))

    scene = bpy.context.scene
    cam = bpy.data.objects.get(cam_name)
    if cam is None:
        print("STAGE RESULT R2791_DUMP_FAIL no camera named %r (have %s)"
              % (cam_name, [o.name for o in bpy.data.objects if o.type == "CAMERA"]))
        return 1
    cd = cam.data

    plan = json.load(open(find("docs/explode_plan.json")))["clusters"]

    # part name -> cluster, for naming raycast hits
    by_name = {o.name: o for o in bpy.data.objects}
    part_cluster, resolved, misses = {}, {}, {}
    for cl, spec in plan.items():
        objs, miss = [], []
        for p in spec["parts"]:
            o = by_name.get(p)
            hits = [o] if o is not None else [
                x for n, x in by_name.items() if n == p or n.startswith(p + ".")]
            if hits:
                objs.extend(hits)
                for h in hits:
                    part_cluster[h.name] = cl
            else:
                miss.append(p)
        resolved[cl] = objs
        misses[cl] = miss
    print(">> resolved %d cluster objects, %d unresolved parts"
          % (sum(len(v) for v in resolved.values()),
             sum(len(v) for v in misses.values())))

    sw = cd.sensor_width
    rx, ry = scene.render.resolution_x, scene.render.resolution_y
    sh = sw * ry / rx

    frames, geom = [], {}
    for f in range(lo, hi + 1):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        ce = cam.evaluated_get(dg)
        m = ce.matrix_world
        eye = m.translation.copy()
        lens = ce.data.lens
        focus_m = ce.data.dof.focus_distance
        fwd = (m.to_quaternion() @ Vector((0.0, 0.0, -1.0))).normalized()
        right = (m.to_quaternion() @ Vector((1.0, 0.0, 0.0))).normalized()
        up = (m.to_quaternion() @ Vector((0.0, 1.0, 0.0))).normalized()

        rec = {
            "f": f,
            "p": [round(v, 6) for v in eye],
            "q": [round(v, 6) for v in m.to_quaternion()],
            "lens": round(lens, 5),
            "focus_m": round(focus_m, 5),
            "fstop": round(ce.data.dof.aperture_fstop, 5),
            "use_dof": bool(ce.data.dof.use_dof),
            "focus_object": (ce.data.dof.focus_object.name
                             if ce.data.dof.focus_object else None),
        }

        # (2) centre-of-frame raycast: 9 rays over the central 20 % of frame
        hits = []
        for iu in (-1, 0, 1):
            for iv in (-1, 0, 1):
                du = iu * 0.10 * sw / 2.0
                dv = iv * 0.10 * sh / 2.0
                d = (fwd * lens + right * du + up * dv).normalized()
                ok, loc, _n, _idx, obj, _mw = scene.ray_cast(dg, eye, d)
                if ok:
                    z = (loc - eye).dot(fwd)
                    hits.append({"u": iu, "v": iv, "dist": round((loc - eye).length, 4),
                                 "z": round(z, 4), "obj": obj.name if obj else None,
                                 "cl": part_cluster.get(obj.name if obj else "", None)})
        rec["centre_hits"] = hits
        onaxis = [h for h in hits if h["u"] == 0 and h["v"] == 0]
        rec["centre_dist_m"] = onaxis[0]["dist"] if onaxis else None
        rec["centre_obj"] = onaxis[0]["obj"] if onaxis else None
        rec["centre_cluster"] = onaxis[0]["cl"] if onaxis else None
        if hits:
            ds = sorted(h["dist"] for h in hits)
            rec["centre_dist_median_m"] = round(ds[len(ds) // 2], 4)
            cls = [h["cl"] for h in hits if h["cl"]]
            rec["centre_cluster_frac"] = round(len(cls) / float(len(hits)), 3)
        else:
            rec["centre_dist_median_m"] = None
            rec["centre_cluster_frac"] = 0.0

        # (3) is there ANY geometry at the focal plane on the view axis?
        rec["focus_minus_centre_m"] = (round(focus_m - rec["centre_dist_m"], 4)
                                       if rec["centre_dist_m"] else None)
        frames.append(rec)

        if (f - lo) % geom_step == 0 or f in (lo, hi):
            g = {}
            for cl, objs in resolved.items():
                lo3, hi3 = [1e18] * 3, [-1e18] * 3
                for o in objs:
                    oe = o.evaluated_get(dg)
                    mw = oe.matrix_world
                    for c in oe.bound_box:
                        w = mw @ Vector(c)
                        for i in range(3):
                            lo3[i] = min(lo3[i], w[i])
                            hi3[i] = max(hi3[i], w[i])
                if lo3[0] < 1e17:
                    g[cl] = [[round(v, 5) for v in lo3], [round(v, 5) for v in hi3]]
            geom[str(f)] = g

    curves = {}
    curves.update(dump_fcurves(cd, "camdata"))
    curves.update(dump_fcurves(cam, "camobj"))

    doc = {
        "blend": bpy.data.filepath,
        "scene_arg": scene_path,
        "camera": cam_name,
        "sensor_width": sw, "sensor_height": cd.sensor_height,
        "sensor_fit": cd.sensor_fit,
        "res": [rx, ry], "res_pct": scene.render.resolution_percentage,
        "fps": scene.render.fps, "frame_end": scene.frame_end,
        "exposure": scene.view_settings.exposure,
        "view_transform": scene.view_settings.view_transform,
        "look": scene.view_settings.look,
        "frames": frames,
        "cluster_bbox": geom,
        "fcurves": curves,
        "unresolved_parts": {k: v for k, v in misses.items() if v},
    }
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    json.dump(doc, open(out_path, "w"))

    nfoc = sum(v["n_keys"] for k, v in curves.items() if "focus_distance" in k)
    nfst = sum(v["n_keys"] for k, v in curves.items() if "aperture_fstop" in k)
    print("STAGE RESULT R2791_DUMP_OK frames=%d geom=%d focus_keys=%d fstop_keys=%d "
          "exposure=%.4f vt=%s look=%s res=%dx%d -> %s"
          % (len(frames), len(geom), nfoc, nfst, scene.view_settings.exposure,
             scene.view_settings.view_transform, scene.view_settings.look,
             rx, ry, out_path))
    return 0


try:
    rc = main()
except Exception:
    traceback.print_exc()
    print("STAGE RESULT R2791_DUMP_FAIL uncaught exception")
    rc = 1
sys.stdout.flush()
