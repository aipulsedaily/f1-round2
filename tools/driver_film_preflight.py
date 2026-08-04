"""R2-250 -- will `build_film_scene.py` accept `world/car_anim_driver.blend`?

`tools/build_film_scene.py` is out of bounds to edit (hard constraint 7) and it
carries four hard refusals on the CAR collection it appends.  Building a 4.5 GB
film scene to discover one of them fires is an expensive way to ask.  This
replays exactly those four checks -- read out of `build_film_scene.py`, quoted
in the code below so a drift between the two is visible -- against a driver car
blend, in an empty scene, in about a minute.

    blender -b --factory-startup -noaudio -P tools/driver_film_preflight.py -- \
        --car world/car_anim_driver.blend

It is a PREFLIGHT and not a substitute: it proves the append succeeds and the
refusals do not fire.  It does not prove the film renders.
"""

import argparse
import os
import sys

import bpy

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def log(m):
    sys.stdout.write("[preflight] %s\n" % m)
    sys.stdout.flush()


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--car", default=os.path.join(R2, "world/car_anim_driver.blend"))
    a = ap.parse_args(argv)

    scene = bpy.context.scene
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)

    with bpy.data.libraries.load(a.car, link=False) as (src_data, dst_data):
        if "CAR" not in src_data.collections:
            print("STAGE RESULT: FAIL -- %s has no CAR collection" % a.car)
            return 1
        dst_data.collections = ["CAR"]
        loaded = dst_data.collections
    car = [c for c in loaded if c is not None][0]
    scene.collection.children.link(car)
    log("appended CAR: %d direct objects, %d including children"
        % (len(car.objects), len(car.all_objects)))

    fails = []

    # 1. CAR_ROOT present
    root = None
    for o in car.objects:
        if o.name.startswith("CAR_ROOT"):
            root = o
    if root is None:
        fails.append("no CAR_ROOT in the appended CAR collection")

    # 2. exactly 8 CARRIG_* hubs
    hubs = [o.name for o in car.objects if o.name.startswith("CARRIG_")]
    if len(hubs) != 8:
        fails.append("%d CARRIG_* hub empties, expected 8" % len(hubs))

    # 3. no parent outside the CAR collection -- the one the driver could break,
    #    because DRV_* hang off DRV_Install which hangs off CAR_ROOT.
    names = set(x.name for x in car.objects)
    orphans = [o.name for o in car.objects
               if o.parent is not None and o.parent.name not in names]
    if orphans:
        fails.append("%d parts have a parent outside CAR: %s"
                     % (len(orphans), orphans[:6]))

    # 4. CAR_ROOT animated
    if root is not None and not (root.animation_data and root.animation_data.action):
        fails.append("CAR_ROOT carries no animation")

    drv = sorted(o.name for o in car.objects if o.name.startswith("DRV_"))
    log("CAR_ROOT %r, %d children, %d hubs, %d orphans"
        % (getattr(root, "name", None),
           len(root.children) if root else -1, len(hubs), len(orphans)))
    log("DRV_* that survived the append (%d): %s" % (len(drv), drv))

    # the driver has to have brought his materials and his action with him
    # read the materials OFF the driver's own slots.  Matching bpy.data by
    # name prefix found the CAR's CarbonFibre and called it the driver's.
    mats = sorted({ms.material.name for n in drv
                   for ms in bpy.data.objects[n].material_slots
                   if ms.material is not None})
    log("materials on DRV_* slots: %d %s" % (len(mats), mats))
    if drv and len(mats) < 8:
        fails.append("only %d materials on the driver's slots -- the shading "
                     "did not come across" % len(mats))
    # NO EXTERNAL ASSETS.  `Render Result` and `Viewer Node` are Blender's own
    # internal images and are not evidence of anything; the question is whether
    # any material on the driver samples a FILE, or carries an image node at
    # all.  Both are checked, because a node with no image assigned today is a
    # file path tomorrow.
    filed = [i.name for i in bpy.data.images if i.filepath]
    texnodes = [(m.name, n.name) for m in bpy.data.materials
                if m.name.startswith("DRV_") and m.use_nodes
                for n in m.node_tree.nodes
                if n.type in ('TEX_IMAGE', 'TEX_ENVIRONMENT')]
    log("NO-EXTERNAL-ASSETS: %d images with a filepath, %d image-texture nodes "
        "in the %d DRV_ materials" % (len(filed), len(texnodes), len(mats)))
    if filed:
        fails.append("%d image datablocks carry a filepath: %s" % (len(filed), filed[:6]))
    if texnodes:
        fails.append("%d image-texture nodes in DRV_ materials: %s"
                     % (len(texnodes), texnodes[:6]))
    inst = bpy.data.objects.get("DRV_Install")
    act = (inst.animation_data.action.name
           if inst and inst.animation_data and inst.animation_data.action else None)
    log("DRV_Install action: %r" % act)
    if inst is None:
        fails.append("DRV_Install did not come across")
    elif act is None:
        fails.append("DRV_Install lost its action -- the driver would not "
                     "arrive with the seat")
    elif not act.startswith("DRV_Install_"):
        fails.append("DRV_Install is on %r, which is not its own COPY -- "
                     "writing through it would edit the car's seat (R2-245)"
                     % act)

    # visibility keys have to survive too, or he pops into the opening shot
    if drv:
        vis = {}
        for f in (1, 300, 579, 580, 2632):
            scene.frame_set(f)
            bpy.context.view_layer.update()
            vis[f] = sum(1 for n in drv
                         if not n.startswith("DRV_Boot")
                         and n != "DRV_Install"
                         and bpy.data.objects[n].hide_render)
        n_keyed = len([n for n in drv if not n.startswith("DRV_Boot")
                       and n != "DRV_Install"])
        log("hidden of %d keyed DRV_* by frame: %s" % (n_keyed, vis))
        if not (vis[1] == vis[300] == vis[579] == n_keyed
                and vis[580] == 0 and vis[2632] == 0):
            fails.append("the appearance keys did not survive the append: %s"
                         % vis)

    for f in fails:
        log("REFUSAL: %s" % f)
    print("STAGE RESULT: %s" % ("OK" if not fails else "FAIL"))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
