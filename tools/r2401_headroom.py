"""R2-401 -- what is actually above and behind the driver's head.

    /opt/blender-5.2.0-linux-x64/blender -b world/car_anim_driver.blend \
        --factory-startup -noaudio -P tools/r2401_headroom.py

`tools/r2401_cockpit_fit.py` shot 4,000 rays straight up off the helmet's upper
cap and NONE of them hit any car mesh within 3 m -- so "0.054 m of headroom to
the engine cover" cannot be a vertical clearance.  This prints the objects it
could be a SILHOUETTE reference to instead, and the halo's own z profile along
the car, so the halo-apex comparison can be read as the height comparison it is
rather than as the clearance it is not.
"""
import json
import os
import sys

import bpy
import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCH = ("MB_engine_cover", "EC_shell", "EC_hoop", "EC_bulkhead", "EC_fin",
         "EC_duct", "EC_tcam", "EC_louvres", "EC_pans", "MB_chassis_cockpit",
         "CI_headrest", "CI_sidehead", "CI_seal", "halo_assembly_HoopTube",
         "halo_assembly_PillarTube", "halo_assembly_FinBlade",
         "halo_assembly_PodShell")


def main():
    sc = bpy.context.scene
    sc.frame_set(1200)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    root = bpy.data.objects["CAR_ROOT"]
    Minv = root.matrix_world.inverted()
    rep = {}

    def pts(n):
        ob = bpy.data.objects.get(n)
        if ob is None:
            return None
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        M = Minv @ ob.matrix_world
        P = np.array([list(M @ v.co) for v in me.vertices])
        ev.to_mesh_clear()
        return P

    print("%-32s %-26s %-26s" % ("object", "min (x,y,z)", "max (x,y,z)"))
    for n in WATCH:
        P = pts(n)
        if P is None:
            print("  %-30s ABSENT" % n)
            continue
        rep[n] = {"min": P.min(0).tolist(), "max": P.max(0).tolist(),
                  "verts": int(len(P))}
        print("%-32s %-26s %-26s" % (n, np.round(P.min(0), 4).tolist(),
                                     np.round(P.max(0), 4).tolist()))

    # the highest car surface in the head box, and where
    print("\n-- the ceiling over the head box (x -0.35..0.25, |y| < 0.30) --")
    best = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name.startswith("DRV_") or not len(o.data.polygons):
            continue
        P = pts(o.name)
        if P is None or not len(P):
            continue
        m = ((P[:, 0] > -0.35) & (P[:, 0] < 0.25) & (np.abs(P[:, 1]) < 0.30)
             & (P[:, 2] > 0.60))
        if m.sum():
            best.append((float(P[m][:, 2].max()), o.name, int(m.sum())))
    best.sort(reverse=True)
    rep["head_box_tallest"] = best[:20]
    for z, n, k in best[:20]:
        print("   z_max %.4f  %-34s %d verts in the box" % (z, n, k))

    # the halo hoop's z profile along x, per side band -- is it ever OVER the
    # head, or does it only pass BESIDE it?
    P = pts("halo_assembly_HoopTube")
    print("\n-- halo HoopTube z, by x slice --")
    prof = []
    for x0 in np.arange(-0.20, 1.00, 0.05):
        m = np.abs(P[:, 0] - x0) < 0.025
        if not m.sum():
            continue
        Q = P[m]
        cen = np.abs(Q[:, 1]) < 0.10
        row = [round(float(x0), 3), int(m.sum()),
               round(float(Q[:, 2].min()), 4), round(float(Q[:, 2].max()), 4),
               round(float(np.abs(Q[:, 1]).min()), 4),
               int(cen.sum())]
        prof.append(row)
        print("   x %+.2f  n %5d  z %.4f..%.4f  |y|min %.4f  centre-verts %d"
              % (row[0], row[1], row[2], row[3], row[4], row[5]))
    rep["halo_profile"] = prof

    out = os.path.join(R2, "docs/r2401_headroom.json")
    json.dump(rep, open(out, "w"), indent=1, default=float)
    print("\nwrote %s" % out)
    print("STAGE RESULT: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
