"""WITNESS FRAMES — look at the breach, held, from the camera that films it.

    blender -b sim/out/breach_sim.blend --factory-startup -P sim/witness.py -- \
        --out sim/render/witness.blend --frames 860 866 880 920 1000 1056

A sim is unusually good at hiding defects in motion.  This builds a scene that
can be RENDERED — the contract's own sun and sky, the film's exposure, and the
ONE camera placed exactly where `docs/beat_sheet.json` puts it on the frame
asked for — so a shard that interpenetrates, pops, or vanishes for three frames
can be seen held.

THE CAMERA IS THE FILM'S, NOT A CONVENIENT ONE
----------------------------------------------
Beat 3 has 30 declared camera keys with world position, look-at, lens, f-stop
and focus distance.  This interpolates them at the requested frame rather than
inventing a flattering angle, because the brief's requirement is that the sim
looks correct from the ENTIRE camera arc, and an angle chosen after the fact is
the one place a destruction sim is always fine.

THE LIGHT IS THE CONTRACT'S, VIA `world/itemkit.contract_sun`
-------------------------------------------------------------
Not re-derived here.  That helper exists precisely because two modules quoting
the sun independently is how wave 1 got a rig that does not exist, and it
refuses a sun that points up.

    FILM_EXPOSURE = -3.628.  NOT -3.048: that value was derived and refuted and
    over-exposes by 0.586 stops.  `tools/build_verify_scene.py` asserts it.

THE SHUTTER IS FLAT 180 DEGREES, DELIBERATELY
---------------------------------------------
Cycles integrates blur over FILM frames and the ramp is already baked into the
per-film-frame animation, so scaling the shutter by world time would apply the
slowdown twice.  One beat-3 film frame spans 1/156 s of world time, so 180 deg
is 1/312 s — exactly a 156 fps high-speed camera, which is the instrument this
shot is pretending to be.  `--shutter-mode world` exists for A/B only.
"""

import argparse
import json
import math
import os
import sys

import bpy                                                        # noqa: E402
from mathutils import Vector                                      # noqa: E402

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "sim"), os.path.join(R2, "world"),
           os.path.join(R2, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import breachlib as BL                                            # noqa: E402

FILM_EXPOSURE = -3.628


def beat3_key_at(frame, sheet=None):
    """Interpolate beat 3's declared camera keys at a FILM frame."""
    sheet = sheet or json.load(open(BL.SHEET))
    keys = []
    for k in sorted(sheet.keys()):
        # "beats" is a LIST of beat records; "beat1".."beat6" are the dicts that
        # carry the camera keys.  Same trap as apply_breach hit.
        b = sheet[k]
        if not k.startswith("beat") or not isinstance(b, dict):
            continue
        keys.extend(b.get("camera_keys", []))
    keys.sort(key=lambda x: x["t"])
    t = (frame - 1) / float(BL.FPS)
    ts = [k["t"] for k in keys]
    if t <= ts[0]:
        return keys[0]
    if t >= ts[-1]:
        return keys[-1]
    i = max(1, min(len(ts) - 1, next(j for j, v in enumerate(ts) if v >= t)))
    a, b = keys[i - 1], keys[i]
    w = (t - a["t"]) / max(b["t"] - a["t"], 1e-9)
    out = {}
    for f in ("world", "look_at"):
        out[f] = [a[f][c] * (1 - w) + b[f][c] * w for c in range(3)]
    for f in ("lens_mm", "fstop", "focus_distance_m"):
        out[f] = a.get(f, 0.0) * (1 - w) + b.get(f, 0.0) * w
    out["t"] = t
    return out


def make_cam(name, key):
    cd = bpy.data.cameras.new(name)
    cd.lens = float(key["lens_mm"])
    cd.sensor_width = 36.0
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = float(key.get("fstop", 4.0))
    cd.dof.focus_distance = float(key.get("focus_distance_m", 6.0))
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    p = Vector(key["world"])
    ob.location = p
    d = (Vector(key["look_at"]) - p)
    if d.length < 1e-6:
        d = Vector((1, 0, 0))
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--frames", type=int, nargs="+",
                   default=[858, 861, 865, 870, 880, 920, 980, 1056, 1200])
    p.add_argument("--shutter-mode", choices=("flat", "world"), default="flat")
    p.add_argument("--sim-scene", action="store_true",
                   help="the blend is the WORLD-TIME sim, so map the requested "
                        "film frames onto its own frame numbering")
    return p.parse_args(argv)


def main():
    a = parse_args()
    sc = bpy.context.scene
    try:
        import itemkit as IK
        IK.contract_sun("WIT_", scene=sc, sky=True)
        lit = "world/itemkit.contract_sun"
    except Exception as e:                                # noqa: BLE001
        # Refusing to invent a rig: a witness frame lit by a made-up sun is a
        # picture of the wrong thing, and the whole point of this file is to
        # look at the real one.
        raise SystemExit("REFUSING: could not build the contract sun (%s). "
                         "The witness must be lit by the film's own rig." % e)

    # STRIP THE RIGID BODY WORLD.  The broker refused this scene's first
    # submission and was right to: a blend carrying a rigidbody_world with no
    # cache makes Blender SIMULATE the frame instead of reading it, and a
    # simulation reached by jumping to a frame does not continue the previous
    # one.  Nothing rendered here ever needs live physics — the wall standing is
    # geometry, and everything after it arrives as baked F-curves from
    # `apply_breach`.  A render scene that can still simulate is a render scene
    # that can disagree with the bake.
    stripped = False
    if sc.rigidbody_world is not None:
        try:
            bpy.ops.rigidbody.world_remove()
            stripped = True
        except Exception:                                  # noqa: BLE001
            sc.rigidbody_world = None
            stripped = True
    # No per-object `rigidbody.object_remove()` loop: that operator is ~20 ms a
    # call and gets worse as the scene fills, so on 4,025 bodies it is minutes,
    # and it buys nothing — with no world, per-object rigid body settings are
    # inert and the broker's guard reads `scene.rigidbody_world`.

    sc.render.engine = "CYCLES"
    sc.cycles.device = "GPU"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = FILM_EXPOSURE
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5          # 180 deg, FLAT
    sc.render.motion_blur_position = "CENTER"
    if a.shutter_mode == "world":
        # A/B ONLY.  See the module docstring: this is the double correction.
        clock = BL.Clock()
        f = sc.frame_current
        sc.render.motion_blur_shutter = 0.5 * clock.scales[max(0, f - 1)]

    info = dict(frames=[], lit_by=lit, exposure=FILM_EXPOSURE,
                rigidbody_world_stripped=stripped,
                shutter_mode=a.shutter_mode,
                shutter=sc.render.motion_blur_shutter)
    clock = BL.Clock()
    for f in a.frames:
        key = beat3_key_at(f)
        sim_f = f
        if a.sim_scene:
            wt = float(clock.world_t(float(f)))
            t0 = BL.sim_window()[0]
            sim_f = int(round((wt - t0) * BL.SIM_FPS)) + 1
        cam = make_cam("WIT_f%04d" % f, key)
        info["frames"].append(dict(film_frame=f, sim_frame=sim_f,
                                   camera=cam.name, lens_mm=key["lens_mm"],
                                   world=key["world"], look_at=key["look_at"],
                                   fstop=key["fstop"],
                                   focus_m=key["focus_distance_m"]))
    sc.camera = bpy.data.objects[info["frames"][0]["camera"]]
    bpy.ops.wm.save_as_mainfile(filepath=a.out)
    with open(a.out.replace(".blend", ".json"), "w") as fh:
        json.dump(info, fh, indent=1, default=float)
    print(json.dumps(info, indent=1, default=float))


if __name__ == "__main__":
    main()
