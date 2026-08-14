"""Rebuild the WHOLE scene from source: showroom + lighting + props + car.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/rebuild_scene.py -- --out work/scene_new.blend

    # showroom only, skip the 105 s car assembly while iterating on the room
    ... -P tools/rebuild_scene.py -- --out work/room.blend --no-car

Existing scripts assumed a pre-built `f1_showroom.blend` and only rebuilt the CAR
into it, so a change to s02_showroom / s05_lighting / s07_props had no path into a
rendered frame at all. That is a large part of why the room got 181 lines of
attention while the car got 4.35 M polys.

Order matters: s01_base wipes the scene and sets render/world/compositor state, so
it must run first or later modules get deleted.

Also applies the two post-build passes so an iteration is directly comparable with
the delivered frames:
  * tools/quality.py settings (caustics, 64 bounces, real GI, no clamp, 16-bit)
  * the dais albedo retune (0.60 -> 0.40) that took frame clipping 2.95 % -> 0.30 %
Pass --raw to skip both and get the unmodified build.
"""

import argparse
import importlib
import os
import sys
import time

import bpy

sys.path.insert(0, "/home/zany/opus5-car-render/build")

# (module, [entry functions], description). Not every module exposes build():
# s03_materials has build_showroom_materials/build_car_materials, and calling the
# wrong name silently skipped it, which surfaced as
# KeyError: key "TyreRubber" not found three stages later.
STAGES = [
    ("s01_base", ["build"], "scene, world HDRI, compositor"),
    # Materials must exist before anything that assigns them: s02 wants
    # FloorPolished/PlatformBody and s07 wants TyreRubber, and a missing key
    # raises rather than warning, aborting the whole rebuild.
    ("s03_materials", ["build_showroom_materials", "build_car_materials"],
     "the shared material registry"),
    ("s02_showroom", ["build"], "floor, shell, glazing, platform"),
    ("s05_lighting", ["build"], "coves, spot rig, key/fill/rim"),
    ("s06_cameras", ["build"], "the four hero cameras"),
    ("s07_props", ["build"], "tyre stacks, cases, stanchions, plaque"),
]


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--no-car", action="store_true",
                   help="skip s08_assemble (~105 s) while iterating on the room")
    p.add_argument("--raw", action="store_true",
                   help="skip the quality + dais passes")
    p.add_argument("--dais-albedo", type=float, default=0.40)
    return p.parse_args(argv)


def main():
    a = parse_args()
    t_all = time.time()
    for name, fns, what in STAGES:
        m = importlib.import_module(name)
        importlib.reload(m)
        t = time.time()
        ran = []
        for fn in fns:
            f = getattr(m, fn, None)
            if f is None:
                # Loud, not silent: a skipped stage shows up as a confusing
                # KeyError much later, in a different module.
                print(f"!! {name}.{fn}() MISSING - stage incomplete")
                continue
            f()
            ran.append(fn)
        print(f">> {name:16s} {time.time() - t:6.1f}s  {what}  [{', '.join(ran)}]")

    if not a.no_car:
        import s08_assemble
        importlib.reload(s08_assemble)
        t = time.time()
        r = s08_assemble.build(verbose=False)
        print(f">> s08_assemble    {time.time() - t:6.1f}s  "
              f"{r['total_polys']:,} polys, {r['parts_ok']} parts, "
              f"failed={r['parts_failed']}")

    # s09 clones REAL car components into the display vitrine, so it can only run
    # once the car exists. s07 built hand-modelled stand-ins; s09 deletes those
    # and replaces them with the actual brake corner, driveshaft and wishbones.
    if not a.no_car:
        import s09_display
        importlib.reload(s09_display)
        t = time.time()
        s09_display.build()
        print(f">> s09_display    {time.time() - t:6.1f}s  real parts into the vitrine")

    if not a.raw:
        sc = bpy.context.scene
        cy = sc.cycles
        for k, v in (("max_bounces", 64), ("diffuse_bounces", 32),
                     ("glossy_bounces", 32), ("transmission_bounces", 32),
                     ("volume_bounces", 16), ("transparent_max_bounces", 64),
                     ("caustics_reflective", True), ("caustics_refractive", True),
                     ("sample_clamp_indirect", 0.0), ("sample_clamp_direct", 0.0),
                     ("blur_glossy", 0.0), ("filter_width", 1.30),
                     # ao_bounces silently swaps real GI for an AO approximation
                     # after N bounces; at 1 it made max_bounces=64 meaningless.
                     ("ao_bounces_render", 0), ("ao_bounces", 0),
                     ("use_fast_gi", False)):
            if hasattr(cy, k):
                setattr(cy, k, v)
        sc.render.image_settings.color_depth = "16"
        mat = bpy.data.materials.get("PlatformBody")
        if mat and mat.use_nodes:
            n = next((x for x in mat.node_tree.nodes
                      if x.type == "BSDF_PRINCIPLED"), None)
            if n:
                v = a.dais_albedo
                n.inputs["Base Color"].default_value = (v, v * 1.008, v * 1.033, 1.0)
                print(f">> dais albedo -> {v:.2f}")
        print(">> quality pass applied (caustics, 64 bounces, real GI, 16-bit)")

    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    polys = sum(len(o.data.polygons) for o in meshes)
    cams = [o.name for o in bpy.context.scene.objects if o.type == "CAMERA"]
    lamps = len([o for o in bpy.context.scene.objects if o.type == "LIGHT"])
    print(f">> scene: {len(meshes)} meshes, {polys:,} polys, {lamps} lamps, "
          f"cameras {cams}")
    # Blender relativises external paths on save (the "Relative Paths" pref), so
    # an absolute /home/zany/opus5-car-render/assets/city.exr becomes
    # //../assets/city.exr, which the remote deploy resolves to /assets/city.exr
    # and cannot find. The render then proceeds with NO environment lighting and
    # looks plausible but wrong - caught only because the broker now warns.
    # Force every external reference back to absolute and disable remapping.
    for img in bpy.data.images:
        if img.filepath and not img.packed_file:
            ap = bpy.path.abspath(img.filepath)
            if ap != img.filepath:
                print(f">> unrelativised {img.name}: {img.filepath} -> {ap}")
            img.filepath = ap
    missing = [i.name for i in bpy.data.images
               if i.filepath and not i.packed_file
               and not os.path.exists(bpy.path.abspath(i.filepath))]
    if missing:
        print(f"!! MISSING image files after build: {missing}")
    bpy.ops.wm.save_as_mainfile(filepath=a.out, relative_remap=False, compress=False)
    print(f">> wrote {a.out} in {time.time() - t_all:.1f}s total")


main()
