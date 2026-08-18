"""THE UN-BEND, AS PIXELS.  Builds the BENT half of a one-variable A/B.

    /opt/blender-5.2.0-linux-x64/blender -b render/film14_breach_r6.blend \
        --python sim/unbend_ab.py -- \
        --out render/r2607_unbend_BENT_DO_NOT_SHIP.blend

WHY A SECOND SCENE AND NOT TWO FRAMES
=====================================
`MUL05_S02` deflects 145 mm at f861 and is home by f870 -- the un-bend is NINE
film frames.  The obvious experiment is to diff f861 against f870.  It cannot
work, and the numbers say so before any pixel is spent: projected through the
camera track's own pose and its 28.3 mm lens,

    camera-induced shift of a STATIC point, f861 -> f870   1478.9 px
    the member's own 145 mm deflection at f861               41.1 px

so a temporal diff is 97 % camera.  The only design that isolates the member is
THE SAME FRAME FROM TWO SCENES WITH ONE VARIABLE BETWEEN THEM.

WHAT THE VARIABLE IS
====================
The pieces that RECOVER -- deflect and return to the intact rest pose -- are
pinned to their f861 pose for the whole take.  Everything else is untouched,
including `BF_MUL05_S00` and `BF_MUL05_S01`, the two that genuinely leave: they
are not part of the defect and moving them would put two variables in one
picture.

So at f870:
    render/film14_breach_r6.blend    the wall has repaired itself   (A, shipped)
    this scene                       the wall is still bent         (B)

The difference between those two images is the defect, at the moment its
consequence is on screen, with the camera, the lighting, the glass, the car and
every other object identical by construction.

THIS SCENE IS NOT A DELIVERY and cannot become one.  It holds a pose the solver
never produced, for 2,978 frames.  It exists to be differenced against the ship
candidate and for nothing else -- hence the name.
"""
import argparse
import json
import os
import sys

import numpy as np

import bpy

R2 = os.path.expanduser("~/f1-round2")
for _p in ("sim",):
    _q = os.path.join(R2, _p)
    if _q not in sys.path:
        sys.path.insert(0, _q)

import breach_metrics as BM                                        # noqa: E402


def log(m):
    print("[unbend_ab] %s" % m, flush=True)


def curves_of(ob):
    out = {}
    ad = ob.animation_data
    if ad is None or ad.action is None:
        return out
    slot = getattr(ad, "action_slot", None)
    for layer in ad.action.layers:
        for strip in layer.strips:
            cb = strip.channelbag(slot) if slot is not None else None
            if cb is None:
                continue
            for fc in cb.fcurves:
                out[(fc.data_path, fc.array_index)] = fc
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--pin-frame", type=int, default=861,
                    help="the frame whose pose the recovering pieces hold")
    ap.add_argument("--report", default=os.path.join(
        R2, "sim/out/unbend_ab.json"))
    args = ap.parse_args(argv)

    coll = bpy.data.collections.get("BREACH_Frame")
    if coll is None or not len(coll.objects):
        print(">> STAGE RESULT: UNBEND_NO_FRAME_BODIES")
        return 1
    pieces = list(coll.objects)
    log("BREACH_Frame: %d pieces" % len(pieces))

    pinned, left_alone, rep = [], [], []
    for ob in pieces:
        fcs = curves_of(ob)
        if not fcs:
            left_alone.append((ob.name, "unanimated"))
            continue
        kf = sorted({int(k.co[0]) for fc in fcs.values()
                     for k in fc.keyframe_points})
        if not kf:
            left_alone.append((ob.name, "no keys"))
            continue

        def ev(dp, ix, default):
            fc = fcs.get((dp, ix))
            return fc.evaluate(args.pin_frame) if fc is not None else default

        home = np.array([ev("location", i, ob.location[i]) for i in range(3)])
        # the piece's own home is its pose before anything moves
        h0 = np.array([fcs[("location", i)].evaluate(kf[0])
                       if ("location", i) in fcs else ob.location[i]
                       for i in range(3)])
        P = np.array([[fcs[("location", i)].evaluate(f)
                       if ("location", i) in fcs else ob.location[i]
                       for i in range(3)] for f in kf])
        dsp = np.linalg.norm(P - h0, axis=1)
        pk, en = float(dsp.max()), float(dsp[-1])
        recovers = (pk > BM.DEFLECT_M
                    and en / max(pk, 1e-12) < BM.RETURN_FRAC)
        if not recovers:
            left_alone.append((ob.name, "peak %.4f end %.4f -- leaves or "
                                        "never deflected" % (pk, en)))
            continue

        # PIN: replace every transform curve with a single key at the pin
        # frame, CONSTANT both ways.  The piece then holds its f861 pose on
        # all 2,978 frames.
        vals = {}
        for (dp, ix), fc in list(fcs.items()):
            if dp not in ("location", "rotation_quaternion"):
                continue
            v = fc.evaluate(args.pin_frame)
            vals[(dp, ix)] = v
            kps = fc.keyframe_points
            while len(kps):
                kps.remove(kps[0])
            kps.insert(float(args.pin_frame), float(v))
            kps[0].interpolation = "CONSTANT"
            fc.extrapolation = "CONSTANT"
            fc.update()
        pinned.append(ob.name)
        rep.append(dict(name=ob.name, peak_m=round(pk, 4), end_m=round(en, 4),
                        pinned_at=args.pin_frame,
                        offset_from_home_m=round(
                            float(np.linalg.norm(home - h0)), 4)))

    rep.sort(key=lambda d: -d["offset_from_home_m"])
    log("pinned %d pieces at f%d; left %d alone"
        % (len(pinned), args.pin_frame, len(left_alone)))
    for d in rep[:8]:
        log("   %-22s peak %.4f  held at %.4f m from home"
            % (d["name"], d["peak_m"], d["offset_from_home_m"]))

    out = dict(pin_frame=args.pin_frame, pinned=rep,
               left_alone=[list(x) for x in left_alone],
               n_pinned=len(pinned), n_left=len(left_alone),
               source=bpy.data.filepath, written=args.out,
               note="B half of the un-bend A/B.  A is film14_breach_r6.blend, "
                    "unmodified.  Render the SAME frame from both.")
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    json.dump(out, open(args.report, "w"), indent=1)

    ok = len(pinned) > 0
    if ok:
        bpy.ops.wm.save_as_mainfile(filepath=args.out, compress=False)
        log("wrote %s (%.2f GB)"
            % (args.out, os.path.getsize(args.out) / 1e9))
    print(">> STAGE RESULT: %s"
          % ("UNBEND_BENT_BUILT" if ok else "UNBEND_NOTHING_TO_PIN"))
    return 0 if ok else 1


if __name__ == "__main__":
    _a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    try:
        main(_a)
    except Exception:                                          # noqa: BLE001
        import traceback
        traceback.print_exc()
        print(">> STAGE RESULT: UNBEND_ERROR")
