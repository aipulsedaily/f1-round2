"""MEASURE THE BUILT CAR, off the blend, frame by frame.

    /opt/blender-5.2.0-linux-x64/blender -b world/car_anim.blend \
        --factory-startup -P tools/sample_car_blend.py -- \
        --out world/car_anim_measured.json

This is the instrument half of `tools/car_anim_gate.py`, split off because the
gate has to run under the project venv (numpy, `world_contract`) and the scene
can only be read by Blender.

IT READS THE ARTEFACT, NOT THE AUTHOR'S MODEL. Every number here comes out of
`matrix_world` after a `frame_set` and a depsgraph update — the same evaluation
Cycles does — so a rig that was keyed correctly but wired to nothing produces
zeros here. That failure has happened on this project: a bump chain into the
wrong socket reported "0.00 % changed" because nothing reached the shader on
either side.

The blend's own identity — path, size and mtime — is written into the dump, and
the gate refuses to draw a conclusion if the file on disk has moved since. A
harness measuring a four-day-old blend already produced one flawless, entirely
convincing null on this project.

WHAT IS SAMPLED

  * `CAR_ROOT` world matrix on every frame -> location and XYZ Euler.
  * the four contact patches, as CAR_ROOT's world matrix applied to the measured
    wheel centres dropped to local z = 0. That is where the tyre touches.
  * every spin hub's authored rotation, read with `fcurve.evaluate()` — the
    F-curve, because a rotation matrix only knows an angle modulo 2*pi and the
    film turns the wheels 14,026 radians.
  * the same hub's WORLD matrix, so the F-curve can be checked against the
    transform it is supposed to be driving.
  * `wheel_tyre_RL_Tyre`'s transform RELATIVE TO CAR_ROOT — a real mesh, three
    parent levels down. A rear tyre, because a front one steers as well as spins
    and the check would then have two unknowns in it.
  * a beat-1 witness set: 24 car parts on 16 frames spread over frames 1-792, so
    the gate can prove this build left the assembly bit-identical.
"""

import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

CONTACTS = (("FL", +1.800, +0.84750), ("FR", +1.800, -0.84750),
            ("RL", -1.800, +0.79750), ("RR", -1.800, -0.79750))
WITNESS_TYRE = "wheel_tyre_RL_Tyre"   # REAR: it spins but never steers
BEAT1_WITNESS_FRAMES = (1, 60, 120, 200, 280, 340, 399, 460, 520, 580,
                        640, 696, 704, 740, 770, 792)


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--witness-parts", type=int, default=24)
    p.add_argument("--allow-no-rig", action="store_true",
                   help="sample a blend that has no CARRIG_* hubs — used to "
                        "capture world/beat1_anim.blend as the BEFORE that "
                        "measurement F compares against")
    p.add_argument("--frames", default=None,
                   help="'a-b' to sample a range only")
    return p.parse_args(argv)


def fcurves_of(ob):
    ad = ob.animation_data
    if not (ad and ad.action):
        return []
    act = ad.action
    if hasattr(act, "fcurves"):
        return list(act.fcurves)
    out = []
    slot = getattr(ad, "action_slot", None)
    for layer in act.layers:
        for strip in layer.strips:
            bags = []
            if slot is not None:
                b = strip.channelbag(slot)
                if b:
                    bags.append(b)
            if not bags:
                bags = list(getattr(strip, "channelbags", []))
            for b in bags:
                out += list(b.fcurves)
    return out


def main():
    a = parse_args()
    scene = bpy.context.scene
    blend = bpy.data.filepath
    n = scene.frame_end

    root = bpy.data.objects["CAR_ROOT"]
    spin_fc, steer_fc, spin_ob, steer_ob = {}, {}, {}, {}
    for corner, _ax, _hy in CONTACTS:
        s = bpy.data.objects.get("CARRIG_SPIN_%s" % corner)
        t = bpy.data.objects.get("CARRIG_STEER_%s" % corner)
        spin_ob[corner], steer_ob[corner] = s, t
        for fc in fcurves_of(s) if s else []:
            if fc.data_path == "rotation_euler" and fc.array_index == 1:
                spin_fc[corner] = fc
        for fc in fcurves_of(t) if t else []:
            if fc.data_path == "rotation_euler" and fc.array_index == 2:
                steer_fc[corner] = fc
    missing = [c for c, _a, _h in CONTACTS if c not in spin_fc]
    if missing and not a.allow_no_rig:
        raise SystemExit("no spin F-curve on corners %s — the rig is not built"
                         % missing)
    have_rig = not missing

    tyre = bpy.data.objects.get(WITNESS_TYRE)
    plan = json.load(open(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs/explode_plan.json")))
    allparts = sorted(p for v in plan["clusters"].values() for p in v["parts"])
    witness = [allparts[i] for i in range(0, len(allparts),
                                          max(len(allparts) // a.witness_parts, 1))]

    f0, f1 = 1, n
    if a.frames:
        f0, f1 = (int(v) for v in a.frames.split("-"))
    frames, beat1 = [], {}
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        mw = root.matrix_world
        loc = mw.translation
        eul = mw.to_euler("XYZ")
        rec = {"f": f,
               "loc": [loc.x, loc.y, loc.z],
               "rot": [eul.x, eul.y, eul.z],
               "spin_fc": {c: float(spin_fc[c].evaluate(f))
                           for c, _a, _h in CONTACTS if c in spin_fc},
               "steer_fc": {c: float(steer_fc[c].evaluate(f))
                            for c, _a, _h in CONTACTS if c in steer_fc},
               "contacts": {}}
        # WHERE THE TYRE ACTUALLY IS: the spin hub's world origin is the wheel
        # centre, so `z - rolling radius` is the contact patch. Taking it off
        # CAR_ROOT's corners instead would measure the CHASSIS, which moves on
        # its suspension by up to 55 mm and is therefore not where the tyre is.
        for corner, ax, hy in CONTACTS:
            if have_rig:
                p = spin_ob[corner].matrix_world.translation
            else:
                p = mw @ Vector((ax, hy, 0.360))
            rec["contacts"][corner] = [p.x, p.y, p.z]
            q = mw @ Vector((ax, hy, 0.0))
            rec.setdefault("chassis_corners", {})[corner] = [q.x, q.y, q.z]
        # THE F-CURVE MUST BE DRIVING THE TRANSFORM. The spin hub's LOCAL matrix
        # is a pure rotation about Y (its parent is the steer hub), so the angle
        # comes straight out of it with atan2 and no Euler-decomposition branch.
        if have_rig:
            ml = spin_ob["FL"].matrix_local
            rec["spin_hub_local_y"] = float(math.atan2(ml[0][2], ml[0][0]))
        # AND THE TRANSFORM MUST BE DRIVING THE GEOMETRY. The witness is a REAR
        # tyre: it does not steer, so its rotation relative to CAR_ROOT is the
        # spin and nothing else, and the check has no second unknown in it.
        if tyre is not None:
            rec["tyre_rel"] = [list(r) for r in
                               (mw.inverted() @ tyre.matrix_world)]
            if have_rig:
                # RIGIDITY: the tyre relative to its own spin hub. This must be
                # CONSTANT on every frame of the film. It is the one measurement
                # that proves the key reaches the geometry: an angle taken
                # relative to CAR_ROOT instead carries the hub's suspension
                # counter-rotation as well, and cannot separate "the wheel is
                # not turning" from "the body is leaning".
                rec["tyre_rel_hub"] = [
                    list(r) for r in
                    (spin_ob["RL"].matrix_world.inverted() @ tyre.matrix_world)]
        frames.append(rec)
        if f in BEAT1_WITNESS_FRAMES:
            beat1[str(f)] = {w: [list(r) for r in bpy.data.objects[w].matrix_world]
                             for w in witness if w in bpy.data.objects}

    st = os.stat(blend) if blend and os.path.exists(blend) else None
    out = {"blend": blend, "have_rig": have_rig, "frame_range": [f0, f1],
           "blend_bytes": st.st_size if st else None,
           "blend_mtime": st.st_mtime if st else None,
           "frame_end": n, "fps": scene.render.fps,
           "witness_parts": witness,
           "beat1_witness": beat1,
           "objects_in_scene": len(bpy.data.objects),
           "car_root_children": len(root.children),
           "frames": frames}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"))
    print(">> sampled %d frames of %s -> %s (%.1f MB)"
          % (len(frames), os.path.basename(blend), a.out,
             os.path.getsize(a.out) / 1048576.0))
    print(">> STAGE RESULT: CAR_BLEND_SAMPLED")



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
    gate_exit.guard(main, tool="sample_car_blend")
