"""STEP ZERO — enumerate what round 1 actually produced.

    /opt/blender-5.2.0-linux-x64/blender -b <blend> --factory-startup \
        -P /home/zany/f1-round2/tools/inventory.py -- --out <out.json>

WHY THIS EXISTS
---------------
The round-2 brief opens with: "Do NOT assume what it produced — inventory it."
That instruction is earned. Round 1's own defect log records three separate
occasions where work was done against an assumed scene state and had to be
redone, including a bake taken from a stale blend that produced a technically
perfect render of geometry that no longer existed.

So this reads the blend and reports only what is in it. Every number below is
measured, never inferred from a name or a doc.

WHAT IT REPORTS, AND WHY EACH FIELD IS HERE
-------------------------------------------
  * BASE vs EVALUATED polygons. 122 BEVEL, 58 SOLIDIFY and 13 MIRROR modifiers
    take round 1 from 4.35 M base polys to ~9.6 M evaluated triangles. The
    exploded-layout maths in Beat 1 must use EVALUATED bounds or parts will be
    spaced by the wrong volume, and a MIRROR modifier means the base mesh is
    HALF the real object — round 1 lost a day to exactly that (D163: a bisect
    ran on the base mesh, silently splitting only 10 of 23 parts).
  * WORLD-SPACE bounds and centre, not local. Round 1's s09_display.py put 16
    cloned parts at the world origin because it treated local stand offsets as
    world coordinates. Beat 1 explodes parts along mechanically sensible axes
    from their FINAL transforms, so world space is the only useful frame.
  * Parent/child hierarchy and collection membership, so assembly CLUSTERS can
    be derived from real structure rather than a preset list.
  * Modifier stacks, so nothing is animated without knowing what will re-
    evaluate when it moves.
  * Flags for anything that looks like leftover WIP, hidden, zero-poly, or
    parented outside its collection — the brief asks for surprises to be
    resolved explicitly rather than silently inherited.
"""

import argparse
import json
import os
import sys
from collections import defaultdict

import bpy
from mathutils import Vector


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def world_bounds(ob):
    """World-space AABB from the EVALUATED object.

    bound_box is local and pre-modifier. For a MIRROR'd part that is half the
    real extent, and for a SOLIDIFY'd one it is missing the shell thickness.
    """
    deps = bpy.context.evaluated_depsgraph_get()
    ob_eval = ob.evaluated_get(deps)
    try:
        me = ob_eval.to_mesh()
    except Exception:
        return None
    if me is None or len(me.vertices) == 0:
        try:
            ob_eval.to_mesh_clear()
        except Exception:
            pass
        return None
    mw = ob.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    n_verts, n_polys = len(me.vertices), len(me.polygons)
    n_tris = sum(len(p.vertices) - 2 for p in me.polygons)
    ob_eval.to_mesh_clear()
    return {
        "min": [round(v, 5) for v in lo],
        "max": [round(v, 5) for v in hi],
        "size": [round(v, 5) for v in (hi - lo)],
        "centre": [round(v, 5) for v in ((lo + hi) * 0.5)],
        "eval_verts": n_verts,
        "eval_polys": n_polys,
        "eval_tris": n_tris,
    }


def collections_of(ob):
    return sorted(c.name for c in ob.users_collection)


def main():
    a = parse_args()
    scene = bpy.context.scene
    deps = bpy.context.evaluated_depsgraph_get()

    out = {
        "blend": bpy.data.filepath,
        "blend_bytes": os.path.getsize(bpy.data.filepath) if bpy.data.filepath else None,
        "blender": bpy.app.version_string,
        "scene": scene.name,
        "frame_range": [scene.frame_start, scene.frame_end],
        "unit_system": scene.unit_settings.system,
        "unit_scale": round(scene.unit_settings.scale_length, 6),
        "render": {
            "engine": scene.render.engine,
            "resolution": [scene.render.resolution_x, scene.render.resolution_y],
            "fps": scene.render.fps,
        },
        "collections": {},
        "objects": [],
        "materials": [],
        "cameras": [],
        "lights": [],
        "warnings": [],
    }

    # ---- collection tree -------------------------------------------------
    def walk(coll, depth=0, parent=None):
        out["collections"][coll.name] = {
            "parent": parent,
            "depth": depth,
            "children": [c.name for c in coll.children],
            "direct_objects": len(coll.objects),
            "all_objects": len(coll.all_objects),
        }
        for c in coll.children:
            walk(c, depth + 1, coll.name)

    walk(scene.collection)

    # ---- objects ---------------------------------------------------------
    base_polys = eval_polys = eval_tris = 0
    by_prefix = defaultdict(lambda: {"count": 0, "eval_tris": 0})

    for ob in scene.objects:
        rec = {
            "name": ob.name,
            "type": ob.type,
            "collections": collections_of(ob),
            "parent": ob.parent.name if ob.parent else None,
            "parent_type": ob.parent_type if ob.parent else None,
            "visible": ob.visible_get(),
            "hide_render": ob.hide_render,
            "location": [round(v, 5) for v in ob.location],
            "rotation_euler": [round(v, 6) for v in ob.rotation_euler],
            "scale": [round(v, 5) for v in ob.scale],
            "dimensions": [round(v, 5) for v in ob.dimensions],
            "modifiers": [{"name": m.name, "type": m.type} for m in ob.modifiers],
            "materials": [ms.material.name if ms.material else None
                          for ms in ob.material_slots],
        }
        if ob.type == "MESH":
            rec["base_verts"] = len(ob.data.vertices)
            rec["base_polys"] = len(ob.data.polygons)
            base_polys += rec["base_polys"]
            wb = world_bounds(ob)
            if wb:
                rec.update(wb)
                eval_polys += wb["eval_polys"]
                eval_tris += wb["eval_tris"]
                # A modifier stack that multiplies geometry is the single most
                # important thing to know before animating a part.
                if rec["base_polys"] and wb["eval_polys"] / max(rec["base_polys"], 1) > 1.5:
                    rec["modifier_multiplier"] = round(
                        wb["eval_polys"] / max(rec["base_polys"], 1), 2)
            else:
                rec["eval_polys"] = 0
                out["warnings"].append(f"{ob.name}: mesh evaluates to zero geometry")
            pfx = ob.name.split("_")[0] + "_"
            by_prefix[pfx]["count"] += 1
            by_prefix[pfx]["eval_tris"] += rec.get("eval_tris", 0)
        elif ob.type == "CAMERA":
            d = ob.data
            out["cameras"].append({
                "name": ob.name, "lens": d.lens, "sensor": d.sensor_width,
                "dof": d.dof.use_dof,
                "fstop": d.dof.aperture_fstop if d.dof.use_dof else None,
                "focus_object": d.dof.focus_object.name if d.dof.focus_object else None,
                "focus_distance": round(d.dof.focus_distance, 4),
                "location": [round(v, 4) for v in ob.matrix_world.translation],
            })
        elif ob.type == "LIGHT":
            d = ob.data
            out["lights"].append({
                "name": ob.name, "light_type": d.type,
                "energy": d.energy, "color": [round(c, 4) for c in d.color],
                "size": getattr(d, "size", None),
                "location": [round(v, 4) for v in ob.matrix_world.translation],
            })
        out["objects"].append(rec)

    # ---- materials -------------------------------------------------------
    for m in bpy.data.materials:
        users = sum(1 for ob in scene.objects
                    for ms in ob.material_slots if ms.material == m)
        out["materials"].append({
            "name": m.name, "users_in_scene": users,
            "use_nodes": m.use_nodes,
            "node_count": len(m.node_tree.nodes) if m.use_nodes and m.node_tree else 0,
            "has_image_texture": bool(m.use_nodes and m.node_tree and any(
                n.type == "TEX_IMAGE" for n in m.node_tree.nodes)),
        })

    out["totals"] = {
        "objects": len(out["objects"]),
        "meshes": sum(1 for o in out["objects"] if o["type"] == "MESH"),
        "base_polys": base_polys,
        "eval_polys": eval_polys,
        "eval_tris": eval_tris,
        "materials": len(out["materials"]),
        "cameras": len(out["cameras"]),
        "lights": len(out["lights"]),
    }
    out["by_prefix"] = {k: v for k, v in sorted(
        by_prefix.items(), key=lambda x: -x[1]["eval_tris"])}

    # ---- surprises the brief asks to be resolved explicitly --------------
    for o in out["objects"]:
        if o["type"] == "MESH" and o.get("base_polys", 0) == 0:
            out["warnings"].append(f"{o['name']}: zero-poly mesh (leftover WIP?)")
        if o["type"] == "MESH" and not o["collections"]:
            out["warnings"].append(f"{o['name']}: in no collection")
        if o["hide_render"]:
            out["warnings"].append(f"{o['name']}: hide_render=True (invisible to Cycles)")
        if o["type"] == "MESH" and any(abs(s - 1.0) > 1e-4 for s in o["scale"]):
            out["warnings"].append(
                f"{o['name']}: non-uniform/unapplied scale {o['scale']} "
                f"— exploded offsets and physics both care")

    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)

    t = out["totals"]
    print(f">> INVENTORY {os.path.basename(out['blend'])}")
    print(f">>   objects {t['objects']}  meshes {t['meshes']}  materials {t['materials']}"
          f"  cameras {t['cameras']}  lights {t['lights']}")
    print(f">>   base polys {t['base_polys']:,}  ->  evaluated tris {t['eval_tris']:,}")
    print(f">>   collections {len(out['collections'])}  warnings {len(out['warnings'])}")
    print(f">> wrote {a.out}")
    print(">> STAGE RESULT: INVENTORY_OK")



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
    gate_exit.guard(main, tool="inventory")
