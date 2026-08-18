"""Bake Beat 1's exploded field into a blend, with one macro camera per cluster.

    /opt/blender-5.2.0-linux-x64/blender -b ~/opus5-car-render/work/iter.blend \
        --factory-startup -P tools/build_beat1_audit.py -- \
        --plan docs/explode_plan.json --out world/beat1_audit.blend --dist 1.2

WHY BAKE A BLEND INSTEAD OF RENDERING LOCALLY
---------------------------------------------
The render farm's worker varies only camera, resolution and samples per job, and
discovers cameras from the blend at load — it never configures them. A pose that
moves 616 objects therefore cannot be expressed as a job and has to be baked into
a .blend and rendered with `--scene`. Round 1 learned this the hard way and also
learned the corollary: bake from a STALE scene and you get a technically perfect
render of geometry that no longer exists.

WHY THE AUDIT USES THE EXPLODED STATE
-------------------------------------
The brief requires close-ups "at the actual camera distance from the beat sheet".
In Beat 1 the parts are not on the car — they hang in the exploded field with the
camera weaving between them. Auditing the assembled car would test a presentation
that never appears on screen. This bakes the real thing: real offsets, real
neighbours in the background, real showroom light.

The source blend is opened READ-ONLY and saved to a NEW path. iter.blend is round
1's deliverable and is never written.
"""

import argparse
import json
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# Showroom interior, measured from round 1: floor 30 x 22 m centred on the origin,
# 6.5 m ceiling. Margin keeps the lens off the glass and out of the slab.
_M = 0.45
ROOM_MIN = (-15.0 + _M, -11.0 + _M, 0.35)
ROOM_MAX = (15.0 - _M, 11.0 - _M, 6.5 - _M)


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--plan", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--dist", type=float, default=1.2)
    p.add_argument("--lens", type=float, default=50.0)
    p.add_argument("--fstop", type=float, default=2.8)
    p.add_argument("--control-plant-missing-image", action="store_true",
                   help="POSITIVE CONTROL ONLY. Plant an image datablock "
                        "pointing at a path that does not exist, so the "
                        "missing-image check can be SEEN to fail. Never use "
                        "this for an audit blend you intend to render.")
    return p.parse_args(argv)


def main():
    a = parse_args()
    src = bpy.data.filepath
    plan = json.load(open(a.plan))

    # ---- apply the exploded offsets --------------------------------------
    moved = 0
    for key, c in plan["clusters"].items():
        off = Vector(c["explode_offset"])
        if off.length < 1e-9:
            continue
        for pname in c["parts"]:
            ob = bpy.data.objects.get(pname)
            if ob is None:
                print(f"!! missing part {pname} (cluster {key})")
                continue
            ob.location = ob.location + off
            moved += 1
    bpy.context.view_layer.update()
    print(f">> applied exploded offsets to {moved} objects")

    # ---- one macro camera per cluster, framing that cluster alone ---------
    deps = bpy.context.evaluated_depsgraph_get()
    npath = os.path.join(os.path.dirname(os.path.abspath(a.plan)), "presentation_normals.json")
    normals = json.load(open(npath)) if os.path.exists(npath) else {}
    print(f">> presentation normals: {len(normals)} clusters"
          if normals else ">> WARNING: no normals, using generic placement")
    cams = {}
    for key, c in plan["clusters"].items():
        pts = []
        for pname in c["parts"]:
            ob = bpy.data.objects.get(pname)
            if ob is None or ob.type != "MESH":
                continue
            oe = ob.evaluated_get(deps)
            try:
                me = oe.to_mesh()
            except Exception:
                continue
            if me:
                mw = ob.matrix_world
                pts += [mw @ v.co for v in me.vertices]
                oe.to_mesh_clear()
        if not pts:
            print(f"!! {key}: no geometry to frame")
            continue
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        ctr = (lo + hi) * 0.5
        radius = max((hi - lo).length * 0.5, 0.02)

        cd = bpy.data.cameras.new(f"MACRO_{key}")
        cd.lens = a.lens
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = a.fstop
        # Focus on the cluster centre, so the part under test is the sharp thing
        # and its neighbours fall off — "DOF as the presenter", per the brief.
        cd.dof.focus_distance = radius + a.dist
        cam = bpy.data.objects.new(f"MACRO_{key}", cd)
        bpy.context.scene.collection.objects.link(cam)

        # Outboard and slightly above. A dead-on axis view flatters shaders and
        # hides the grazing-angle failures macro inspection exists to find.
        # ROOM-CONSTRAINED PLACEMENT.
        #
        # The measured best direction is not always reachable. SP's highest-
        # scoring view is straight up; its exploded centre sits at z 4.2 m, so a
        # 2.54 m standoff put the lens at z 6.7 m — THROUGH the 6.5 m ceiling.
        # That frame came back as flat grey: the underside of the ceiling slab,
        # 12.2 MB against 27-35 MB for every other cluster.
        #
        # Round 1 solved this same class with a room-constrained camera and I
        # did not carry it forward. So: walk the ranked directions and take the
        # first whose station actually fits inside the room; if none of them do,
        # shorten the standoff on the best direction rather than abandoning it.
        ranked = normals.get(key, {}).get("ranked") or []
        if not ranked and normals.get(key, {}).get("normal"):
            ranked = [{"normal": normals[key]["normal"]}]

        def fits(pos):
            return (ROOM_MIN[0] < pos.x < ROOM_MAX[0]
                    and ROOM_MIN[1] < pos.y < ROOM_MAX[1]
                    and ROOM_MIN[2] < pos.z < ROOM_MAX[2])

        d, loc, rank_used, standoff_scale = None, None, None, 1.0
        for ri, alt in enumerate(ranked):
            cand_d = Vector(alt["normal"]).normalized()
            cand = ctr + cand_d * (radius + a.dist)
            if fits(cand):
                d, loc, rank_used = cand_d, cand, ri
                break
        if loc is None and ranked:
            # every direction leaves the room: pull the lens in along the best one
            cand_d = Vector(ranked[0]["normal"]).normalized()
            for scale in (0.8, 0.65, 0.5, 0.4, 0.3):
                cand = ctr + cand_d * (radius + a.dist) * scale
                if fits(cand):
                    d, loc, rank_used, standoff_scale = cand_d, cand, 0, scale
                    break
        if loc is None:
            lateral = 1.0 if ctr.y >= 0 else -1.0
            d = Vector((0.55, 0.72 * lateral, 0.42)).normalized()
            loc = ctr + d * (radius + a.dist)
            rank_used = -1
        if rank_used and rank_used > 0:
            print(f"   {key}: best direction leaves the room, using rank {rank_used}")
        if standoff_scale < 1.0:
            print(f"   {key}: standoff pulled to {standoff_scale:.0%} to stay inside")
        cam.location = loc
        cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
        cams[key] = {"camera": cam.name, "centre": [round(v, 4) for v in ctr],
                     "radius": round(radius, 4),
                     "cam_loc": [round(v, 4) for v in cam.location],
                     "focus_m": round(cd.dof.focus_distance, 4),
                     "n_parts": c["n_parts"], "tris": c["tris"]}
        print(f">> camera MACRO_{key:<16} r={radius:6.3f}m  focus={cd.dof.focus_distance:5.2f}m")

    # ---- procedural sky + camera prune, INLINE ---------------------------
    #
    # These used to live in a separate tools/fix_audit_blend.py that had to be
    # run afterwards. It got forgotten exactly once — a rebuild for a collision
    # test skipped it — and the blend silently went back to round 1's
    # `ShowroomWorld`, which references ~/opus5-car-render/assets/
    # city.exr by absolute path. That file exists locally so nothing complained
    # here; on the render farm the asset tree is not mirrored and the frame
    # rendered with NO ENVIRONMENT LIGHT. The farm reported it; I did not.
    #
    # Two reasons it is inlined now rather than left as a second step:
    #   1. city.exr is a DOWNLOADED PHOTOGRAPHIC HDRI and the round-2 brief
    #      forbids downloaded stock outright, so the correct fix is never to
    #      ship it to the instance — it is to not reference it.
    #   2. A build step that must be remembered is a build step that will be
    #      forgotten. This project has now lost time to that pattern three
    #      times (the livery-by-hand export, the hand-written _routes.json, and
    #      this).
    import fix_audit_blend as FA
    FA.procedural_world()
    removed = [ob.name for ob in list(bpy.data.objects)
               if ob.type == "CAMERA" and not ob.name.startswith("MACRO_")]
    for n in removed:
        bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    for img in list(bpy.data.images):
        if img.source == "FILE" and "city.exr" in (img.filepath or ""):
            bpy.data.images.remove(img)
    print(f">> inlined: procedural sky, dropped {len(removed)} non-macro cameras")

    # ---- quality settings baked in, matching round-1 delivery policy ------
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.max_bounces = 64
    sc.cycles.ao_bounces_render = 0        # was 1: silently replaced GI with AO
    sc.cycles.sample_clamp_indirect = 0.0  # was 8.0: discarded specular energy
    sc.cycles.blur_glossy = 0.0
    sc.cycles.caustics_reflective = True
    sc.cycles.caustics_refractive = True
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.0015
    sc.render.filter_size = 1.30
    sc.render.image_settings.color_depth = "16"

    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    # Absolute paths + no compression: Blender relativises external paths on save,
    # and a remote deploy then resolves //../assets/city.exr to /assets/city.exr,
    # finds nothing, and renders with NO environment light — a result that looks
    # plausible and is wrong. Round 1 lost a render batch to exactly this.
    bpy.ops.file.make_paths_absolute()
    bpy.ops.wm.save_as_mainfile(filepath=out, relative_remap=False, compress=False)

    json.dump({"source": src, "blend": out, "dist": a.dist,
               "lens": a.lens, "fstop": a.fstop, "cameras": cams},
              open(os.path.splitext(out)[0] + "_cams.json", "w"), indent=1)

    # THE FIND WAS PRINTED AND THE OK WAS PRINTED ANYWAY   (fixed 2026-08-03)
    #
    # `missing` was computed here, printed with `!!`, and never consulted before
    # `BEAT1_AUDIT_BLEND_OK` two lines down -- which `gate_exit.guard` then
    # dutifully mapped to exit 0. So the exact failure this function's own
    # comment twenty lines up says cost Round 1 a render batch ("finds nothing,
    # and renders with NO environment light -- a result that looks plausible and
    # is wrong") was DETECTED, ANNOUNCED, and SCORED AS A PASS.
    if a.control_plant_missing_image:
        img = bpy.data.images.new("BEAT1_AUDIT_CONTROL", 4, 4)
        img.source = "FILE"
        img.filepath = "//_control_this_file_does_not_exist.exr"
        print("   !! POSITIVE CONTROL: an image datablock pointing at a path "
              "that does not exist has been planted. The check below MUST "
              "fail. An assertion nobody has seen fail has not been shown to "
              "work.")
    missing = [i.filepath for i in bpy.data.images if i.source == "FILE"
               and not os.path.exists(bpy.path.abspath(i.filepath))]
    print(f">> saved {out}  ({os.path.getsize(out)/1048576:.1f} MB), {len(cams)} macro cameras")
    print(f">> external image files referenced: "
          f"{len([i for i in bpy.data.images if i.source == 'FILE'])}, "
          f"of which UNRESOLVABLE: {len(missing)}")
    if missing:
        for f in missing:
            print(f"   FAIL missing image file: {f}")
        print(">> This blend would render with that texture -- and, if it is "
              "the environment, with NO environment light -- and the result "
              "would look plausible and be wrong. Refusing to call it OK.")
        print(">> STAGE RESULT: BEAT1_AUDIT_BLEND_FAIL_MISSING_IMAGES")
        return
    print(">> STAGE RESULT: BEAT1_AUDIT_BLEND_OK")



# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised: `blender -b -P x.py`
    # prints the traceback and exits 0, MEASURED on this box. A gate that
    # crashed was indistinguishable from one that passed. guard() makes an
    # uncaught exception a status 2 and passes any real verdict through
    # unchanged. One shared helper, not N copies -- see tools/gate_exit.py.
    gate_exit.guard(main, tool="build_beat1_audit")
