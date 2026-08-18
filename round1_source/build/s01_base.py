"""Increment A: scene reset, render settings, colour management, world HDRI.

Idempotent - safe to re-run after edits.
"""

import math
import os

import bpy

import common as C

PROJ = os.path.expanduser("~/opus5-car-render")
# D124: interior.exr showed a flat tan wall through the curtain glass, which read
# as a beige backdrop rather than an outside. city.exr puts a plausible urban
# exterior behind the glass in the rear-quarter frame.
HDRI = os.path.join(PROJ, "assets", "city.exr")


def wipe_default():
    """Remove Blender's startup Cube/Light/Camera but keep anything we built."""
    for name in ("Cube", "Light", "Camera"):
        ob = bpy.data.objects.get(name)
        if ob is not None:
            data = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if data and data.users == 0:
                for lib in (bpy.data.meshes, bpy.data.lights, bpy.data.cameras):
                    try:
                        lib.remove(data)
                        break
                    except (TypeError, RuntimeError):
                        pass
    c = bpy.data.collections.get("Collection")
    if c is not None and not c.objects and not c.children:
        bpy.data.collections.remove(c)


def render_settings():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "GPU"
    sc.cycles.samples = 256
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.01
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    # Enough bounces for glass + polished floor without wrecking render time.
    sc.cycles.max_bounces = 12
    sc.cycles.diffuse_bounces = 4
    sc.cycles.glossy_bounces = 8
    sc.cycles.transmission_bounces = 12
    sc.cycles.transparent_max_bounces = 12
    sc.cycles.volume_bounces = 0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    # Fireflies on a mirror floor come from tiny bright samples; clamp indirect.
    sc.cycles.sample_clamp_indirect = 8.0
    sc.cycles.blur_glossy = 0.6

    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1080
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.filter_size = 1.5
    sc.render.dither_intensity = 1.0   # 8-bit PNG output: kills gradient banding
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"

    sc.unit_settings.system = "METRIC"
    sc.unit_settings.length_unit = "METERS"

    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0


# NOTE on dais banding: a critic pass found the deck quantising to 8 levels with
# a 115 px run in 8-bit, which at 8K would become ~460 px. Measured in 16 bit the
# same scan carries 274 levels with a 9 px max run - the RENDER is clean, and the
# delivered PNGs are 16-bit, so the banding is a display-space artefact only.
# Adding grain here was tried and abandoned: Blender 5.x unified the compositor
# Mix/Math/Noise nodes into the ShaderNode family and white noise there has no
# per-pixel vector source. Dither at export instead (tools/publish.py), which
# fixes the case that actually matters - an 8-bit copy posted to the web.


def compositor_bloom(strength=0.06, size=8, threshold=1.4):
    """Subtle bloom via the 5.x compositing node group (Cycles has no built-in).

    Blender 5.x replaced the Composite node with a Group Output on the scene's
    compositing node group. The render still arrives through a Render Layers
    node - feeding the tree from Group Input instead renders pure black, which
    is exactly what defect D001 was.
    """
    sc = bpy.context.scene
    ng = bpy.data.node_groups.get("ShowroomComp")
    if ng is None:
        ng = bpy.data.node_groups.new("ShowroomComp", "CompositorNodeTree")
    ng.nodes.clear()
    ng.interface.clear()
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")

    rl = ng.nodes.new("CompositorNodeRLayers")
    rl.location = (-400, 0)
    rl.scene = sc

    glare = ng.nodes.new("CompositorNodeGlare")
    glare.location = (0, 0)
    glare.inputs["Type"].default_value = "Bloom"
    glare.inputs["Quality"].default_value = "High"
    glare.inputs["Threshold"].default_value = threshold
    glare.inputs["Smoothness"].default_value = 0.35
    glare.inputs["Strength"].default_value = strength
    glare.inputs["Size"].default_value = size
    glare.inputs["Saturation"].default_value = 1.0

    gout = ng.nodes.new("NodeGroupOutput")
    gout.location = (400, 0)

    ng.links.new(rl.outputs["Image"], glare.inputs["Image"])
    ng.links.new(glare.outputs["Image"], gout.inputs["Image"])

    sc.compositing_node_group = ng
    sc.render.use_compositing = True
    return ng


def world_hdri(strength=0.55, rotation_deg=115.0, visible_bg=True):
    w = bpy.data.worlds.get("ShowroomWorld")
    if w is None:
        w = bpy.data.worlds.new("ShowroomWorld")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()

    out = C.node(nt, "ShaderNodeOutputWorld", (700, 0))
    bg = C.node(nt, "ShaderNodeBackground", (480, 0))
    env = C.node(nt, "ShaderNodeTexEnvironment", (200, 0))
    mapping = C.node(nt, "ShaderNodeMapping", (0, 0))
    texco = C.node(nt, "ShaderNodeTexCoord", (-220, 0))

    name = os.path.basename(HDRI)
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.load(HDRI, check_existing=True)
    env.image = img

    mapping.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(rotation_deg))
    bg.inputs["Strength"].default_value = strength

    C.wire(nt, texco, "Generated", mapping, "Vector")
    C.wire(nt, mapping, "Vector", env, "Vector")
    C.wire(nt, env, "Color", bg, "Color")
    C.wire(nt, bg, "Background", out, "Surface")

    # The room is enclosed, so the HDRI only ever shows through glass; keeping it
    # camera-visible avoids a black void if a camera clips the wall.
    bpy.context.scene.render.film_transparent = False
    w.cycles_visibility.camera = visible_bg
    return w


def build():
    wipe_default()
    render_settings()
    compositor_bloom()
    world_hdri()
    for n in ("SHOWROOM", "CAR", "LIGHTS", "CAMERAS", "PROPS"):
        C.collection(n)
    return {
        "engine": bpy.context.scene.render.engine,
        "view_transform": bpy.context.scene.view_settings.view_transform,
        "look": bpy.context.scene.view_settings.look,
        "world": bpy.context.scene.world.name,
        "collections": [c.name for c in bpy.context.scene.collection.children],
    }
