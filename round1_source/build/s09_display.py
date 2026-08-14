"""Put REAL car components in the display vitrine, not stand-ins.

Runs AFTER s08_assemble, because it clones geometry out of the assembled car.

WHY THIS MODULE EXISTS
----------------------
s07_props builds the vitrine and, on its three stands, three hand-modelled
approximations: `Vitrine_Disc` (a revolved ring), `Vitrine_Gear*` (three revolved
discs with box teeth) and `Vitrine_Wishbone*` (three swept tubes). They read as
"a brake disc, a gearbox, a wishbone" from ten metres and as obvious placeholders
up close - which is a problem in a room whose entire purpose is to show how much
work went into the car.

The car already contains the real parts, modelled properly:

    brake_assembly_FL_Disc        53 680 polys, drilled and vaned
    brake_assembly_FL_Caliper      5 038 polys
    suspension_front_FL_Arms      real wishbones with rod ends and jam nuts
    suspension_rear_RL_Driveshaft  real shaft, boots and clamps

So clone those onto the stands instead. `ob.copy()` without copying `ob.data`
shares the mesh, so a 53 680-poly brake disc on a plinth costs one object header
and no geometry - the same trick tools/ghost.py uses for the x-ray twin.

The placeholders are DELETED rather than hidden: leaving them inside the real
parts would put two surfaces in the same place and produce z-fighting on the one
prop the viewer is invited to look at closely.
"""

import math

import bpy
from mathutils import Vector

# stand -> (car object prefixes to clone, target height of the group in metres)
# Heights come from the stand tops in s07_props.build_vitrine: A 0.120,
# B 0.100, C 0.090 above the plinth, with the display volume about 0.34 m tall.
EXHIBITS = {
    "A": {  # brake corner: disc, vanes, bell, caliper and pad stack
        "parts": ("brake_assembly_FL_Disc", "brake_assembly_FL_DiscVanes",
                  "brake_assembly_FL_Bell", "brake_assembly_FL_Caliper",
                  "brake_assembly_FL_PadPlate", "brake_assembly_FL_PadFriction",
                  "brake_assembly_FL_Pistons"),
        "stand": "Vitrine_StandA", "height": 0.300, "spin": 18.0, "tilt": 8.0,
    },
    "B": {  # driveline: shaft, boots, clamps - the closest thing the car has to
            # a "gearbox" exhibit, and it is real
        "parts": ("suspension_rear_RL_Driveshaft", "suspension_rear_RL_Boots",
                  "suspension_rear_RL_Clamps", "suspension_rear_RL_JamNuts"),
        "stand": "Vitrine_StandB", "height": 0.280, "spin": -24.0, "tilt": 0.0,
    },
    "C": {  # front suspension: arms, rod ends, fittings
        # NB the front suspension module names its hardware Fasteners/Seals;
        # RodEnds and JamNuts only exist on the REAR. Naming the rear parts here
        # silently dropped two of five exhibits until the missing-part warning
        # printed them.
        "parts": ("suspension_front_FL_Arms", "suspension_front_FL_Fittings",
                  "suspension_front_FL_Adjusters", "suspension_front_FL_Fasteners",
                  "suspension_front_FL_Seals"),
        "stand": "Vitrine_StandC", "height": 0.260, "spin": 34.0, "tilt": 6.0,
    },
}

PLACEHOLDER_PREFIXES = ("Vitrine_Disc", "Vitrine_Bell", "Vitrine_Gear",
                        "Vitrine_GearTeeth", "Vitrine_Shaft",
                        "Vitrine_Wishbone", "Vitrine_RodEnd")


def _bounds(objs):
    pts = []
    for ob in objs:
        pts += [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(p[i] for p in pts) for i in range(3)))
    hi = Vector((max(p[i] for p in pts) for i in range(3)))
    return lo, hi


def _stand_perch(name):
    """World (x, y, top_z) of a stand, read from the object itself.

    s07_props lays the vitrine out around a local origin and then moves the whole
    group into the room with _transform_group, so the stand offsets in that
    module (-0.78, 0.02, 0.82) are LOCAL. Using them as world coordinates put all
    16 cloned parts next to the car at the world origin, several metres from the
    display case, which is exactly what happened on the first attempt. Read the
    placed object instead and the vitrine can be moved without touching this.
    """
    ob = bpy.data.objects.get(name)
    if ob is None:
        return None
    lo, hi = _bounds([ob])
    return Vector(((lo.x + hi.x) * 0.5, (lo.y + hi.y) * 0.5, hi.z))


def build():
    car = bpy.data.collections.get("CAR")
    props = bpy.data.collections.get("PROPS") or bpy.context.scene.collection
    if car is None:
        print("!! s09_display: no CAR collection - the car must be assembled first")
        return []
    if bpy.data.objects.get("Vitrine_Plinth") is None:
        print("!! s09_display: no vitrine in the scene - nothing to fill")
        return []

    removed = 0
    for ob in list(bpy.data.objects):
        if any(ob.name.startswith(p) for p in PLACEHOLDER_PREFIXES):
            bpy.data.objects.remove(ob, do_unlink=True)
            removed += 1

    made = []
    for tag, spec in EXHIBITS.items():
        perch = _stand_perch(spec["stand"])
        if perch is None:
            print(f"!! s09_display: {spec['stand']} not in the scene - stand {tag} skipped")
            continue
        src = [o for o in car.all_objects
               if o.type == "MESH" and o.name in spec["parts"]]
        missing = set(spec["parts"]) - {o.name for o in src}
        if missing:
            print(f"!! s09_display stand {tag}: missing {sorted(missing)}")
        if not src:
            continue

        clones = []
        for ob in src:
            new = ob.copy()              # shares ob.data: no geometry cost
            new.name = f"Vitrine_{tag}_{ob.name}"
            props.objects.link(new)
            new.matrix_world = ob.matrix_world.copy()
            clones.append(new)

        # Scale the group to the display height and sit it on its stand.
        lo, hi = _bounds(clones)
        size = max(hi.z - lo.z, hi.x - lo.x, hi.y - lo.y) or 1.0
        s = spec["height"] / size
        centre = (lo + hi) * 0.5

        from mathutils import Matrix
        M = (Matrix.Translation(perch + Vector((0.0, 0.0, spec["height"] * 0.5)))
             @ Matrix.Rotation(math.radians(spec["spin"]), 4, "Z")
             @ Matrix.Rotation(math.radians(spec["tilt"]), 4, "X")
             @ Matrix.Scale(s, 4)
             @ Matrix.Translation(-centre))
        for new in clones:
            new.matrix_world = M @ new.matrix_world
        made += clones
        polys = sum(len(o.data.polygons) for o in clones)
        print(f">> vitrine {tag}: {len(clones)} real parts, {polys:,} polys "
              f"(shared meshes), scaled {s:.3f}")

    bpy.context.view_layer.update()
    print(f">> s09_display: replaced {removed} placeholders with {len(made)} "
          f"cloned car components")
    return made


if __name__ == "__main__":
    build()
