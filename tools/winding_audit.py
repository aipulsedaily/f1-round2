"""Winding audit — which side of every built surface does the renderer get?

    blender -b <file.blend> --factory-startup -P tools/winding_audit.py -- \
            --item <id> [--collection <NAME>] [--rays 600] [--out <json>]
            [--fix --save <out.blend>]

WHY. An orientation audit of a finished human figure found 54 of 318 emitted
pieces facing INWARD -- head shell, ears, hair, both shoe uppers, both soles and
all 22 tread bars. Cycles flips a back-facing normal for diffuse, so none of it
rendered black; it rendered with every bump INVERTED, a brow ridge lit as a
groove. Every check in the project passed, because every check measured the
MODEL and none measured the SIDE.

The idioms that produce it -- lofting rings, sweeping profiles, capping
boundary loops, and above all MIRRORING ACROSS AN AXIS, which reverses winding
by construction -- are the idioms all 28 wave-1 item modules are built from.
This runs itemkit's `winding_audit` over every mesh in a built blend, so the
question gets an answer per module without re-running 28 builders.

WHAT IT REPORTS, per object and summed per module:

    pieces / inward         connected components, and how many face inward
    inward_tri_frac         the number that says whether it MATTERS -- a
                            reversed washer is not a reversed head shell
    inconsistent_edges      pieces wound inconsistently WITHIN themselves,
                            which signed volume cannot see and which no flip
                            can repair
    mirrored_by_matrix      objects whose own matrix has a negative
                            determinant: correct geometry, reversed on arrival
    inside_out_fraction     rays cast, first hit taken, back faces counted --
                            the only statistic that measures the picture

`--fix` repairs the meshes in place and `--save` writes the result; the audit is
re-run afterwards and BOTH numbers are in the report, because a repair that is
not measured after the fact is a hope.
"""
import argparse
import json
import os
import sys
import time

import numpy as np

import bpy

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "world"))
import itemkit as K                                          # noqa: E402

CONTEXT_TOKENS = ("standin", "context", "ctx", "ground", "camera", "cam_",
                  "sun", "light", "world")


def _is_context(name):
    n = name.lower()
    return any(t in n for t in CONTEXT_TOKENS)


def collect(collection=None, item=None):
    """Mesh objects of the item, excluding standins the gate also excludes."""
    if collection:
        c = bpy.data.collections.get(collection)
        if c is None:
            raise SystemExit("no collection %r; have %s"
                             % (collection, [x.name for x in bpy.data.collections]))
        obs = list(c.all_objects)
    else:
        cands = [c for c in bpy.data.collections
                 if c.name.startswith("W_Item_")]
        if item:
            key = item.replace("_", "").lower()
            pick = [c for c in cands if c.name.replace("_", "").lower()
                    .endswith(key)]
            cands = pick or cands
        if not cands:
            obs = list(bpy.context.scene.objects)
        else:
            c = max(cands, key=lambda c: len(c.all_objects))
            obs = list(c.all_objects)
    return [o for o in obs if o.type == "MESH" and o.data
            and len(o.data.polygons) and not _is_context(o.name)]


def audit(objs, rays=0, fix=False):
    tot = {"objects": 0, "pieces": 0, "inward": 0, "faces": 0,
           "inward_faces": 0, "triangles": 0, "inward_triangles": 0,
           "flat": 0, "inconsistent_edges": 0, "mirrored_by_matrix": 0,
           "flipped": 0, "statistics_disagree": 0}
    per = []
    seen = {}
    for ob in objs:
        me = ob.data
        # one datablock can be shared by many objects; audit it once
        if me.name in seen:
            r = dict(seen[me.name])
        else:
            r = K.mesh_winding_report(me, apply=fix)
            seen[me.name] = dict(r)
        det = float(np.linalg.det(np.array(ob.matrix_world.to_3x3())))
        tot["objects"] += 1
        tot["pieces"] += r["pieces"]
        tot["inward"] += r["inward"]
        tot["faces"] += r["faces"]
        tot["inward_faces"] += r["inward_faces"]
        tot["triangles"] += r["triangles"]
        tot["inward_triangles"] += int(round(r["inward_area_frac"]
                                             * r["triangles"]))
        tot["flat"] += r["flat"]
        tot["sheet_pieces"] = tot.get("sheet_pieces", 0) + r.get("sheet_pieces", 0)
        tot["undecidable"] = tot.get("undecidable", 0) + r.get("undecidable", 0)
        tot["inconsistent_edges"] += r["inconsistent_edge_pairs"]
        tot["flipped"] += r.get("flipped", 0)
        tot["mirrored_by_matrix"] += 1 if det < 0 else 0
        tot["statistics_disagree"] += 0 if r["statistics_agree"] else 1
        if r["inward"] or r["inconsistent_edge_pairs"] or det < 0:
            per.append({"object": ob.name, "mesh": me.name,
                        "pieces": r["pieces"], "inward": r["inward"],
                        "inward_faces": r["inward_faces"],
                        "inward_area_frac": round(r["inward_area_frac"], 6),
                        "inconsistent_edge_pairs": r["inconsistent_edge_pairs"],
                        "matrix_det": round(det, 6)})
    tot["inward_area_frac"] = (tot["inward_faces"] / tot["faces"]
                               if tot["faces"] else 0.0)
    if rays:
        # THE QUESTION A COUNT CANNOT ANSWER. An inward piece BURIED inside
        # solid geometry costs nothing; a cavity liner emitted as its own closed
        # shell is LEGITIMATELY inward and flipping it would BE the defect; a
        # reversed head shell is the whole reason this file exists. Only a first
        # hit tells them apart, so every back-facing hit is attributed to the
        # piece it came from.
        #
        # Scoped by OBJECT, never by triangle: a subsample makes "first hit"
        # mean nothing, so it takes whole objects, largest first, up to a cap.
        big = sorted(objs, key=lambda o: len(o.data.polygons), reverse=True)
        pick, n = [], 0
        for o in big:
            if n + len(o.data.polygons) > 400000 and pick:
                break
            pick.append(o)
            n += len(o.data.polygons)
        tot["ray"] = ray_attribute(pick, rays)
        tot["ray"]["objects"] = len(pick)
    return tot, per


def plant_fault(objs):
    """Reverse the biggest piece of the biggest object. Positive control."""
    if not objs:
        return None
    ob = max(objs, key=lambda o: len(o.data.polygons))
    me = ob.data
    r = K.mesh_winding_report(me)
    pf = r["piece_of_face"]
    big = int(np.bincount(pf, minlength=r["pieces"]).argmax())
    nl, nf = len(me.loops), len(me.polygons)
    lv = np.empty(nl, np.int32); me.loops.foreach_get("vertex_index", lv)
    ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
    sel = np.flatnonzero(pf == big)
    out = lv.copy()
    for f in sel:
        s, c = int(ls[f]), int(lt[f])
        out[s:s + c] = lv[s:s + c][::-1]
    me.loops.foreach_set("vertex_index", out)
    me.update()
    me.update_tag()
    return {"object": ob.name, "piece": big, "faces_reversed": int(len(sel)),
            "of_faces": int(nf)}


def ray_attribute(objs, n_rays, seed=7):
    """inside_out_fraction, but every back-facing hit is named."""
    VS, FS, lab, base = [], [], [], 0
    for ob in objs:
        r = K.mesh_winding_report(ob.data, with_tri_piece=True)
        if not r.get("triangles"):
            continue
        P = r["verts"]
        M = np.array(ob.matrix_world)
        P = P @ M[:3, :3].T + M[:3, 3]
        T = r["tri_index"].astype(np.int64)
        # SAME COMPENSATION AS itemkit._world_triangles, AND IT WAS MISSING HERE
        # FOR ONE PASS. A negative-determinant matrix reverses winding in world
        # space and Cycles flips the normal back, so not doing this read
        # `grandstand_riser_unit` -- the one object in 30 modules with a
        # mirrored matrix -- as 96 % back-facing on geometry the renderer is
        # perfectly happy with. Two code paths, one rule.
        if float(np.linalg.det(M[:3, :3])) < 0.0:
            T = T[:, ::-1].copy()
        VS.append(P)
        FS.append(T + base)
        base += len(P)
        lab.append((ob.name, r["tri_piece"], r["inward_mask"]))
    if not VS:
        return {"rays": 0, "hits": 0, "back": 0, "fraction": 0.0}
    V = np.concatenate(VS)
    F = np.concatenate(FS)
    out = K.inside_out_fraction(n_rays=n_rays, seed=seed, verts=V, tris=F,
                                return_hits=True)
    # attribute
    offs, acc = [], 0
    for (nm, tp, inw), f in zip(lab, FS):
        offs.append((acc, acc + len(f), nm, tp, inw))
        acc += len(f)
    named = {}
    for idx, isback in zip(out.pop("hit_tri", []), out.pop("hit_back", [])):
        if not isback:
            continue
        for a, b, nm, tp, inw in offs:
            if a <= idx < b:
                key = "%s#piece%d" % (nm, int(tp[idx - a]))
                named[key] = named.get(key, 0) + 1
                break
    out["back_by_piece"] = dict(sorted(named.items(), key=lambda kv: -kv[1])[:20])
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--item", default=None)
    ap.add_argument("--collection", default=None)
    ap.add_argument("--rays", type=int, default=0)
    ap.add_argument("--plant-fault", action="store_true",
                    help="POSITIVE CONTROL, IN SITU. Reverse the winding of "
                         "the largest piece of the largest object and audit "
                         "that. A synthetic sphere proves the arithmetic; this "
                         "proves the instrument fires on THIS module's real "
                         "geometry, at its real scale, through the same code "
                         "path -- and that the ray statistic moves with it. "
                         "Never saved.")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--save", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    t0 = time.time()
    objs = collect(a.collection, a.item)
    planted = None
    if a.plant_fault:
        planted = plant_fault(objs)
    before, per_before = audit(objs, rays=a.rays, fix=False)
    if planted:
        before["planted_fault"] = planted
    rep = {"item": a.item, "blend": bpy.data.filepath, "before": before,
           "offenders": per_before[:200], "n_offenders": len(per_before)}
    if a.fix:
        after, per_after = audit(objs, rays=a.rays, fix=True)
        # audit() with fix=True reports the state it FOUND; re-run clean
        after2, per_after2 = audit(objs, rays=a.rays, fix=False)
        rep["repaired"] = after["flipped"]
        rep["after"] = after2
        rep["n_offenders_after"] = len(per_after2)
        if a.save:
            bpy.ops.wm.save_as_mainfile(filepath=a.save)
            rep["saved"] = a.save
    elif a.plant_fault and a.save:
        # the control scene, for rendering. Never overwrites the source.
        bpy.ops.wm.save_as_mainfile(filepath=a.save)
        rep["saved"] = a.save
    rep["seconds"] = round(time.time() - t0, 1)
    txt = json.dumps(rep, indent=1)
    print("WINDING_AUDIT_JSON_BEGIN")
    print(txt)
    print("WINDING_AUDIT_JSON_END")
    if a.out:
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(txt)



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
    gate_exit.guard(main, tool="winding_audit")
