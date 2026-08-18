"""R2-401 -- measure the driver/cockpit fit off the MESH, not off the report.

    /opt/blender-5.2.0-linux-x64/blender -b world/car_anim_driver.blend \
        --factory-startup -noaudio -P tools/r2401_cockpit_fit.py -- \
        --out docs/r2401_cockpit_fit.json

`docs/driver_placement.json`'s `anchors_local` table is the module's PREDICTION,
taken before `place_driver`'s -16.405 mm crown correction translated every
DRV_* object.  Every number below is read off the emitted geometry at the
assembled fit frame instead.

What it answers:
  1. where the shoulder line actually is, relative to the cockpit rim ABOVE IT
     (not the rim's global max, which is 0.63 m forward at the dash);
  2. what is above the helmet crown, by raycasting up from it -- i.e. where the
     "0.054 m of headroom" comes from and what object owns it;
  3. how far the figure can rise before it hits each of those things.
"""
import argparse
import json
import os
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIT_FRAME = 1200


def log(m):
    sys.stdout.write("[r2401] %s\n" % m)
    sys.stdout.flush()


def local_points(ob, dg, Minv):
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    M = Minv @ ob.matrix_world
    P = np.array([list(M @ v.co) for v in me.vertices], dtype=np.float64)
    ev.to_mesh_clear()
    return P


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(R2, "docs/r2401_cockpit_fit.json"))
    ap.add_argument("--frame", type=int, default=FIT_FRAME)
    a = ap.parse_args(argv)

    sc = bpy.context.scene
    sc.frame_set(a.frame)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    root = bpy.data.objects["CAR_ROOT"]
    Minv = root.matrix_world.inverted()

    seat = bpy.data.objects["CI_seat"]
    off = float((Minv @ seat.matrix_world).translation.length)
    if off > 0.02:
        print("STAGE RESULT: FAIL -- frame %d is mid-explode (%.3f m)" % (a.frame, off))
        return 1
    log("frame %d assembled (interior %.5f m off home)" % (a.frame, off))

    rep = {"frame": a.frame, "interior_offset_m": off}

    # ---- every DRV_* and the cockpit parts, in CAR_ROOT-local ---------------
    drv = {}
    for o in bpy.data.objects:
        if not o.name.startswith("DRV_") or o.type != 'MESH':
            continue
        if len(o.data.polygons) == 0:
            continue
        P = local_points(o, dg, Minv)
        drv[o.name] = P
        rep.setdefault("drv_bounds", {})[o.name] = {
            "min": P.min(0).tolist(), "max": P.max(0).tolist(),
            "verts": int(len(P)), "faces": int(len(o.data.polygons)),
            "hide_render": bool(o.hide_render),
        }
    log("%d DRV_* meshes with faces: %s" % (len(drv), sorted(drv)))

    # ---- the shoulder line -------------------------------------------------
    # DRV_Suit's shoulders are the widest+highest torso mass either side of the
    # centreline BEHIND the wheel.  Take, per side, the highest suit vertex in
    # the band |y| in 0.13..0.26 and x in -0.15..0.10 (the deltoid), which is
    # where a shoulder is on this figure -- the anchor table puts shoulder_l at
    # x -0.013, y 0.191.
    suit = drv.get("DRV_Suit")
    sh = {}
    if suit is not None:
        for lab, s in (("L", 1.0), ("R", -1.0)):
            m = ((suit[:, 1] * s > 0.13) & (suit[:, 1] * s < 0.26)
                 & (suit[:, 0] > -0.15) & (suit[:, 0] < 0.10))
            if m.sum() == 0:
                continue
            Q = suit[m]
            i = int(np.argmax(Q[:, 2]))
            sh[lab] = {"n": int(m.sum()), "top": Q[i].tolist(),
                       "z_top": float(Q[i, 2])}
    rep["shoulder"] = sh

    # HANS / collar top -- the highest thing on the torso either way
    for nm in ("DRV_HANS", "DRV_Harness", "DRV_Balaclava", "DRV_Helmet"):
        if nm in drv:
            rep.setdefault("part_top_z", {})[nm] = float(drv[nm][:, 2].max())

    # ---- the cockpit rim ABOVE the shoulders --------------------------------
    # CI_seal's global max z (0.7298) is at the dash, 0.63 m forward.  What
    # occludes a shoulder is the rim directly outboard of it.
    seal = local_points(bpy.data.objects["CI_seal"], dg, Minv)
    rep["CI_seal_global"] = {"min": seal.min(0).tolist(), "max": seal.max(0).tolist()}
    rim = {}
    for lab, s in (("L", 1.0), ("R", -1.0)):
        m = (seal[:, 1] * s > 0.10) & (np.abs(seal[:, 0] - 0.0) < 0.15)
        if m.sum():
            rim[lab] = {"n": int(m.sum()),
                        "z_top": float(seal[m][:, 2].max()),
                        "z_mean": float(seal[m][:, 2].mean())}
    # and the rim in a longitudinal sweep, so the profile is visible
    prof = []
    for x0 in np.arange(-0.20, 0.65, 0.05):
        m = (np.abs(seal[:, 0] - x0) < 0.025) & (np.abs(seal[:, 1]) > 0.10)
        if m.sum():
            prof.append([round(float(x0), 3), int(m.sum()),
                         round(float(seal[m][:, 2].max()), 4)])
    rep["rim_at_shoulder"] = rim
    rep["rim_profile_x_ztop"] = prof

    # ---- what is above the helmet crown -------------------------------------
    helm = drv["DRV_Helmet"]
    crown_i = int(np.argmax(helm[:, 2]))
    crown = helm[crown_i]
    rep["crown_local"] = crown.tolist()
    log("helmet crown (CAR_ROOT-local) %s" % np.round(crown, 4).tolist())

    # Build one BVH of every CAR mesh (everything not DRV_*) in CAR_ROOT-local
    # and shoot rays straight up from a disc of points on the helmet's upper
    # cap.  The nearest hit per ray is the ceiling over that point.
    verts, faces, owner_tab = [], [], []
    car_names = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name.startswith("DRV_"):
            continue
        if len(o.data.polygons) == 0:
            continue
        try:
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
        except Exception:
            continue
        M = Minv @ o.matrix_world
        base = len(verts)
        # only keep geometry anywhere near the cockpit -- the whole car is 9.6 M
        # triangles and the ceiling test only needs the box over the driver.
        vs = [M @ v.co for v in me.vertices]
        if not vs:
            ev.to_mesh_clear(); continue
        vz = np.array([[v.x, v.y, v.z] for v in vs])
        if (vz[:, 0].min() > 1.2 or vz[:, 0].max() < -0.9
                or vz[:, 2].max() < 0.3 or vz[:, 2].min() > 1.9
                or vz[:, 1].min() > 0.6 or vz[:, 1].max() < -0.6):
            ev.to_mesh_clear(); continue
        car_names.append(o.name)
        verts.extend([(v.x, v.y, v.z) for v in vs])
        for p in me.polygons:
            vi = list(p.vertices)
            for k in range(1, len(vi) - 1):
                faces.append((base + vi[0], base + vi[k], base + vi[k + 1]))
                owner_tab.append(o.name)
        ev.to_mesh_clear()
    log("ceiling BVH: %d objects, %d verts, %d tris" % (len(car_names), len(verts), len(faces)))
    rep["ceiling_bvh_objects"] = sorted(car_names)
    bvh = BVHTree.FromPolygons(verts, faces, all_triangles=True, epsilon=0.0)

    # helmet upper cap: every vertex within 40 mm of the crown height
    cap = helm[helm[:, 2] > crown[2] - 0.04]
    if len(cap) > 4000:
        cap = cap[np.random.default_rng(0).choice(len(cap), 4000, replace=False)]
    hits = []
    for p in cap:
        loc, nrm, fi, dist = bvh.ray_cast(Vector(p) + Vector((0, 0, 1e-4)),
                                          Vector((0, 0, 1)), 3.0)
        if loc is not None:
            hits.append((float(dist), owner_tab[fi] if fi < len(owner_tab) else "?",
                         [float(v) for v in loc]))
    rep["cap_points"] = int(len(cap))
    rep["cap_rays_hit"] = int(len(hits))
    if hits:
        hits.sort()
        rep["ceiling_min"] = {"clearance_m": hits[0][0], "owner": hits[0][1],
                              "at": hits[0][2]}
        from collections import Counter
        c = Counter(h[1] for h in hits)
        rep["ceiling_owners"] = c.most_common(8)
        # per-owner minimum clearance
        mins = {}
        for d, n, _ in hits:
            mins[n] = min(mins.get(n, 9e9), d)
        rep["ceiling_min_per_owner"] = sorted(mins.items(), key=lambda kv: kv[1])
        log("CEILING over the helmet: nearest %.4f m owned by %s"
            % (hits[0][0], hits[0][1]))
        for n, d in rep["ceiling_min_per_owner"][:8]:
            log("   %-34s %.4f m" % (n, d))
    else:
        rep["ceiling_min"] = None
        log("CEILING: no ray from the helmet cap hits any car mesh within 3 m")

    # ---- how far can the WHOLE figure rise? --------------------------------
    # Sweep dz and, for each, find the first contact between any visible DRV_*
    # vertex raised by dz and the car BVH above it.  Cheap version: for a set of
    # driver vertices, ray_cast straight up once and take min clearance; that is
    # exact for a vertical translation against anything the ray hits.
    probe = []
    for nm, P in drv.items():
        if bpy.data.objects[nm].hide_render:
            continue
        Q = P
        if len(Q) > 6000:
            Q = Q[np.random.default_rng(1).choice(len(Q), 6000, replace=False)]
        probe.append((nm, Q))
    clear = {}
    for nm, Q in probe:
        best = 9e9; who = None; where = None
        for p in Q:
            loc, nrm, fi, dist = bvh.ray_cast(Vector(p) + Vector((0, 0, 1e-4)),
                                              Vector((0, 0, 1)), 2.0)
            if loc is not None and dist < best:
                best = float(dist); who = owner_tab[fi] if fi < len(owner_tab) else "?"
                where = [float(v) for v in p]
        if who is not None:
            clear[nm] = {"clearance_m": best, "owner": who, "from": where}
    rep["vertical_clearance_per_drv"] = clear
    for nm in sorted(clear, key=lambda k: clear[k]["clearance_m"]):
        log("  RISE LIMIT %-16s %.4f m  -> %s" % (nm, clear[nm]["clearance_m"],
                                                  clear[nm]["owner"]))
    if clear:
        k = min(clear, key=lambda k: clear[k]["clearance_m"])
        rep["max_rigid_rise_m"] = clear[k]["clearance_m"]
        rep["max_rigid_rise_blocker"] = [k, clear[k]["owner"]]

    # ---- halo ---------------------------------------------------------------
    halo = local_points(bpy.data.objects["halo_assembly_HoopTube"], dg, Minv)
    rep["halo_bounds"] = {"min": halo.min(0).tolist(), "max": halo.max(0).tolist()}
    # the halo's centre hoop directly over the head: |y| < 0.10
    m = np.abs(halo[:, 1]) < 0.10
    if m.sum():
        rep["halo_centre_span"] = {"n": int(m.sum()),
                                   "z_min": float(halo[m][:, 2].min()),
                                   "z_max": float(halo[m][:, 2].max()),
                                   "x_min": float(halo[m][:, 0].min()),
                                   "x_max": float(halo[m][:, 0].max())}

    json.dump(rep, open(a.out, "w"), indent=1, default=float)
    log("wrote %s" % a.out)
    print("STAGE RESULT: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
