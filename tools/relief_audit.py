"""Relief audit — what does this item's surface actually do to the LIGHT?

    blender -b <file.blend> --factory-startup -P tools/relief_audit.py -- \
            --item <id> [--collection <NAME>] [--out <json>]

WHY. What the eye judges is not the height of a bump, it is the RADIANCE
MODULATION it produces, and under this film's 12.47 deg sun the conversion has a
4.5x amplifier in it (itemkit section 5b). Three amplitude sets were rendered
and REJECTED on the human figures and every one of them had been reasoned about
in millimetres of cloth. `relief_reads_as_lip_and_shade` is the check 21 of 28
wave-1 items fail, and none of those 21 modules had any way of knowing what
number to aim at.

BOTH LAYERS, because correcting one and not the other is exactly what happened:

  SHADER   every ShaderNodeBump in every material of the item, walked back to
           the procedural texture driving its Height, reported as slope and m.
  GEOMETRY the mesh's own dihedral angles, banded by edge length, reported as
           an RMS slope and m at each band. The human figures' fold field was
           still at m = 2.32 AFTER the shader had been corrected to 0.28, and
           nothing that reads materials could ever have seen it.

READ THE CAVEATS IN `bump_relief_report`. `height_pp` defaults to the
conservative 1.0, so a stage reported at m = 0.02 is at most 0.02 and probably
less -- which is the direction that matters when the finding is "there is not
enough relief here".
"""
import argparse
import json
import os
import sys

import numpy as np

import bpy

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "world"))
import itemkit as K                                          # noqa: E402

sys.path.insert(0, os.path.join(_ROOT, "tools"))
from winding_audit import collect                            # noqa: E402


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--item", default=None)
    ap.add_argument("--collection", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    objs = collect(a.collection, a.item)
    mats, seen = [], set()
    for ob in objs:
        for ms in ob.material_slots:
            m = ms.material
            if m is None or m.name in seen or not m.node_tree:
                continue
            seen.add(m.name)
            rows = K.bump_relief_report(m.node_tree)
            if rows:
                mats.append({"material": m.name, "bumps": rows})

    ms = [r["m"] for mt in mats for r in mt["bumps"] if r.get("m") is not None]
    unknown = sum(1 for mt in mats for r in mt["bumps"] if r.get("m") is None)
    # R2-038's signature, free: a bump whose Height is fed by ANOTHER BUMP is a
    # normal chain plugged into the height socket, and a bump whose Height is
    # unlinked has a constant there -- a constant has zero gradient, so that
    # stage contributes no relief at all and nothing but this can see it.
    dead = sum(1 for mt in mats for r in mt["bumps"] if r.get("height_unlinked"))
    swapped = sum(1 for mt in mats for r in mt["bumps"]
                  if r.get("height_driven_by_a_bump"))

    # the geometry layer, on the same subject the gate judges: the largest body
    big = sorted(objs, key=lambda o: len(o.data.polygons), reverse=True)[:3]
    geo = []
    for ob in big:
        rows = K.geometry_relief_report(ob.data)
        geo.append({"object": ob.name, "triangles": len(ob.data.loop_triangles)
                    or len(ob.data.polygons), "bands": rows})

    rep = {
        "item": a.item,
        "blend": bpy.data.filepath,
        "sun_elev_deg": K.sun_elev_deg(),
        "sun_amplifier": round(K.sun_amplifier(), 3),
        "materials_with_bump": len(mats),
        "bump_stages": sum(len(mt["bumps"]) for mt in mats),
        "bump_stages_undeterminable": unknown,
        "bump_height_unlinked": dead,
        "bump_height_driven_by_a_bump": swapped,
        "m_min": round(float(np.min(ms)), 5) if ms else None,
        "m_median": round(float(np.median(ms)), 5) if ms else None,
        "m_max": round(float(np.max(ms)), 5) if ms else None,
        "m_sum": round(float(np.sum(ms)), 5) if ms else None,
        "bands": K.RELIEF_BANDS,
        "shader": mats,
        "geometry": geo,
    }
    txt = json.dumps(rep, indent=1)
    print("RELIEF_AUDIT_JSON_BEGIN")
    print(txt)
    print("RELIEF_AUDIT_JSON_END")
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
    gate_exit.guard(main, tool="relief_audit")
