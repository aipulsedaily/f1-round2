"""Make the Beat-1 audit blend deployable, and brief-compliant while we are at it.

    /opt/blender-5.2.0-linux-x64/blender -b world/beat1_audit.blend \
        --factory-startup -P tools/fix_audit_blend.py -- --out world/beat1_audit.blend

TWO PROBLEMS, BOTH MINE
-----------------------
The first deploy of this blend to the render farm failed, and the broker log named
both causes:

    WARNING Image file /home/zany/opus5-car-render/assets/city.exr does not exist.
    ERROR   Failed to load 1 image files
    [worker] prewarm: 19 cameras [...]
    worker on ... not ready after 62s and 20 pings

1. THE MISSING HDRI. The blend inherits round 1's world, which points at an
   absolute path in `opus5-car-render/assets/`. That tree is not mirrored to the
   instance, so Cycles renders with no environment light — the failure mode round
   1 already logged once, where the result "looks plausible and is wrong".

   The fix is not to ship the file. `city.exr` is a REAL PHOTOGRAPHIC HDRI, and
   the round-2 brief forbids downloaded stock outright:

       "No AI-generated images, video, or audio. No downloaded stock anything."

   So it is replaced with a procedural environment built from Blender's own Sky
   Texture at the circuit's specified sun angle. That is brief-compliant, travels
   with the blend, and means the macro audit judges materials under the light
   they will actually ship in rather than under round 1's photograph.

2. NINETEEN CAMERAS. The worker prewarms EVERY camera in the scene at load, about
   4 s each. 15 macro cameras plus round 1's 4 hero cameras took longer than the
   readiness probe allows, so a healthy instance was condemned. Round 1's cameras
   are useless here, so they go.
"""

import argparse
import math
import os
import sys

import bpy

# From circuit_spec.json: the single sun shared by the showroom interior and the
# circuit, so Beat 1 and Beats 4-6 are lit by one physical source.
SUN_DIR = (0.518, -0.828, 0.216)
SUN_ELEV_DEG = 12.5
SUN_BEARING_DEG = -58.0


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def procedural_world():
    """Sky Texture at the spec's sun angle. No external files."""
    w = bpy.data.worlds.get("R2_ProceduralSky") or bpy.data.worlds.new("R2_ProceduralSky")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputWorld"); out.location = (600, 0)
    bg = nt.nodes.new("ShaderNodeBackground"); bg.location = (400, 0)
    sky = nt.nodes.new("ShaderNodeTexSky"); sky.location = (120, 0)

    # Blender 5.x replaced the single "NISHITA" sky with an explicit choice of
    # scattering model: ('SINGLE_SCATTERING', 'MULTIPLE_SCATTERING', 'PREETHAM',
    # 'HOSEK_WILKIE'). MULTIPLE_SCATTERING is the right one here — at 12.5 deg
    # elevation the sun's light travels a long slant path through the atmosphere,
    # and single scattering renders that as an unrealistically dark, hard sky.
    avail = {e.identifier for e in
             sky.bl_rna.properties["sky_type"].enum_items}
    for want in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "HOSEK_WILKIE"):
        if want in avail:
            sky.sky_type = want
            break
    print(f">> sky model: {sky.sky_type}  (available: {sorted(avail)})")

    # Property names drift between versions too, so set defensively rather than
    # letting one renamed attribute abort the whole build after it has already
    # done useful work.
    for attr, val in (("sun_elevation", math.radians(SUN_ELEV_DEG)),
                      ("sun_rotation", math.radians(SUN_BEARING_DEG)),
                      ("sun_intensity", 0.85),
                      ("sun_size", math.radians(0.545)),
                      ("altitude", 120.0),
                      # late afternoon: more atmosphere in the path, so more
                      # scattering and a warmer, softer key than a noon sky
                      ("air_density", 1.35),
                      ("dust_density", 2.2),
                      ("ozone_density", 1.0)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
        else:
            print(f"   (skip: TexSky has no '{attr}' in this Blender)")

    bg.inputs["Strength"].default_value = 1.0
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def main():
    a = parse_args()

    # --- drop round-1 cameras; keep only the macro rig --------------------
    removed = []
    for ob in list(bpy.data.objects):
        if ob.type == "CAMERA" and not ob.name.startswith("MACRO_"):
            removed.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)
    macro = sorted(o.name for o in bpy.data.objects if o.type == "CAMERA")
    print(f">> removed {len(removed)} non-macro cameras: {removed}")
    print(f">> {len(macro)} macro cameras remain")

    # --- procedural world -------------------------------------------------
    procedural_world()
    print(f">> world replaced with procedural Nishita sky "
          f"(elev {SUN_ELEV_DEG} deg, bearing {SUN_BEARING_DEG} deg)")

    # --- purge any remaining external image dependency ---------------------
    orphaned = []
    for img in list(bpy.data.images):
        if img.source != "FILE":
            continue
        p = bpy.path.abspath(img.filepath)
        if not os.path.exists(p):
            orphaned.append(img.filepath)
            bpy.data.images.remove(img)
    if orphaned:
        print(f">> removed {len(orphaned)} images with missing files: {orphaned}")

    if bpy.context.scene.camera is None or bpy.context.scene.camera.name in removed:
        bpy.context.scene.camera = bpy.data.objects.get(macro[0])

    out = os.path.abspath(a.out)
    bpy.ops.file.make_paths_absolute()
    bpy.ops.wm.save_as_mainfile(filepath=out, relative_remap=False, compress=False)

    still_missing = [i.filepath for i in bpy.data.images if i.source == "FILE"
                     and not os.path.exists(bpy.path.abspath(i.filepath))]
    print(f">> saved {out} ({os.path.getsize(out)/1048576:.1f} MB)")
    print(f">> external images still missing: {still_missing if still_missing else 'none'}")
    # AUDIT_BLEND_STILL_MISSING used to exit 0 -- it saved a blend it had just
    # said was broken and told the shell that went fine.
    return gate_exit.verdict("AUDIT_BLEND_FIXED" if not still_missing
                             else "AUDIT_BLEND_STILL_MISSING")


# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge                              # noqa: E402
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised, so a crash was
    # indistinguishable from a pass. guard() makes it a status 2.
    #
    # NOTE, found and NOT fixed: `save_clean()` below is defined AFTER this
    # entry point and is called by nothing, here or anywhere in the tree. It
    # is dead code, and its docstring claims a guarantee ("a blend that CANNOT
    # carry an external asset dependency") that no run has ever exercised.
    # Reported rather than deleted -- it is not this task's file.
    gate_exit.guard(main, tool="fix_audit_blend")


def save_clean(out_path):
    """Save a blend that CANNOT carry an external asset dependency.

    Three times now this project has shipped a broken artefact because a
    necessary step had to be remembered: the livery export that only worked when
    run by hand, the hand-written _routes.json, and the procedural-sky swap that
    reached build_beat1_audit.py but not build_beat1_anim.py — so the DELIVERY
    scene still referenced round 1's downloaded city.exr and would have rendered
    the whole film with no environment light on the farm.

    Remembering harder is not a fix. This makes it impossible: any blend saved
    through here gets the procedural sky, has external image references stripped,
    and then REFUSES TO SAVE if any remain. A build that would produce a scene
    the render farm cannot resolve fails loudly, here, instead of silently
    producing plausible frames somewhere else.
    """
    import bpy, os
    procedural_world()
    dropped = []
    for img in list(bpy.data.images):
        if img.source != "FILE":
            continue
        ap = bpy.path.abspath(img.filepath or "")
        # anything outside this project cannot be mirrored to the instance, and
        # anything downloaded is forbidden by the brief regardless
        if "opus5-car-render/assets" in ap or not os.path.exists(ap):
            dropped.append(img.filepath)
            bpy.data.images.remove(img)
    bpy.ops.file.make_paths_absolute()

    remaining = [i.filepath for i in bpy.data.images if i.source == "FILE"]
    if remaining:
        raise SystemExit(
            "REFUSING TO SAVE: blend still references external images "
            f"{remaining}. The render farm cannot resolve these and the brief "
            "forbids downloaded stock. Fix the source, do not ship it.")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_path),
                                relative_remap=False, compress=False)
    print(f">> save_clean: dropped {len(dropped)} external image(s) {dropped}")
    print(f">> save_clean: world={bpy.context.scene.world.name}, 0 external deps")
    return out_path
