"""R2-401 -- what the cockpit is worth on screen, frame by frame, in pixels.

    .venv/bin/python tools/r2401_cockpit_sweep.py

No Blender and no occlusion term: this answers "how big, and from what angle",
which is what decides whether a 0.05 m change in the driver's height can be seen
at all.  Occlusion is answered separately and exactly by
`tools/driver_containment.py`'s alpha masks, which is where the shoulders are
shown to contribute ~1 % of the driver's pixels at the largest frame.

Two numbers per frame:

  px_per_m   the projected scale at the cockpit's depth.  A displacement of
             `dz` metres moves the figure `dz * px_per_m` pixels on a 3840-wide
             frame, so this converts every candidate fix into screen pixels.

  elev_deg   the camera's elevation above the cockpit APERTURE PLANE.  The
             torso sits below the aperture's lower edge (CI_seal z 0.5849) and
             can only be seen through the opening; at a shallow elevation the
             rim ring occludes it whatever height the driver is at.  Without
             this the sweep would nominate frames where the cockpit is huge and
             edge-on, at which no change to the driver is visible at all.

THE IN-FRAME TEST IS THE APERTURE, NOT THE HELMET
-------------------------------------------------
The first cut asked whether the CROWN projected inside the frame plus a 200 px
margin, and it nominated frames 530-533 as the four biggest cockpits in the
film at 4,940 px/m.  They are not: at frame 530 the camera is 1.27 m off the
car and the cockpit's eight aperture corners project to x 2,548..7,304 -- ONE
of the eight is on a 3,840 px frame and the crown is 3,591 px across, off the
right-hand edge.  `place_driver`'s own appearance gate had already measured
that run as OFF SCREEN and the two disagreed, which is how it was caught.  The
test is now all eight corners of the CI_seal aperture box, and a frame counts
only if at least `--need-corners` of them land on the frame.
"""
import json
import math
import os

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RX, RY, SEN = 3840.0, 2160.0, 36.0

# CAR_ROOT-local, measured on the emitted mesh -- docs/r2401_cockpit_fit.json
LM = {
    "crown":       (-0.0544, -0.0027, 0.8770),
    "shoulder_l":  (-0.0367,  0.1884, 0.5992),
    "shoulder_r":  (-0.0290, -0.1867, 0.6014),
    "chest":       ( 0.1325,  0.0000, 0.4499),   # anchor, less the 16.4 mm corr.
    "rim_fwd":     ( 0.6260,  0.0000, 0.7298),   # CI_seal max
    "rim_aft":     (-0.1620,  0.0000, 0.7298),
    "ap_lo":       ( 0.2000,  0.0000, 0.5849),   # aperture lower edge
    "wheel":       ( 0.4980,  0.0000, 0.4947),
}
# the eight corners of the CI_seal aperture box -- the in-frame test
APERTURE_BOX = [(x, y, z) for x in (-0.1620, 0.6260)
                for y in (-0.1985, 0.1985) for z in (0.5849, 0.7298)]
DRIVER_FROM = 580        # place_driver --appear: before this he is keyed hidden
APERTURE_N = np.array([0.0, 0.0, 1.0])           # the opening faces up


def car_matrix(rot):
    rx, ry, rz = rot
    cx, cy, cz = math.cos(rx), math.cos(ry), math.cos(rz)
    sx, sy, sz = math.sin(rx), math.sin(ry), math.sin(rz)
    return (np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
            @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
            @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))


def cam_matrix(q):
    w, x, y, z = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def main():
    cp = json.load(open(os.path.join(R2, "render/film14_path.json")))["path"]
    car = json.load(open(os.path.join(R2, "world/car_anim_car.json")))["samples"]
    names = list(LM)
    P = np.array([LM[n] for n in names], float)
    NB = len(APERTURE_BOX)
    P = np.vstack([np.array(APERTURE_BOX, float), P])
    names = ["ap%d" % i for i in range(NB)] + names

    rows = []
    for i, c in enumerate(cp):
        f = c["f"]
        s = car[i]
        assert s["f"] == f
        M = car_matrix(s["rot"])
        W = (M @ P.T).T + np.array(s["loc"], float)
        p = np.array(c["p"], float)
        R = cam_matrix(c["q"])
        d = W - p
        dep = -(d @ R[:, 2])
        S = RX * float(c["lens"]) / SEN
        # cockpit centre depth == the shoulder midpoint
        zc = 0.5 * (dep[names.index("shoulder_l")] + dep[names.index("shoulder_r")])
        if zc <= 0.05:
            rows.append((f, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
            continue
        ppm = S / zc
        # elevation of the camera above the aperture plane, in the CAR frame
        v = p - W[names.index("ap_lo")]
        n = M @ APERTURE_N
        L = np.linalg.norm(v)
        elev = math.degrees(math.asin(float(np.dot(v, n) / max(L, 1e-9))))
        # is the cockpit in frame?  ALL EIGHT aperture corners, no margin.
        good = dep[:NB] > 0.02
        apx = RX / 2 + S * (d[:NB] @ R[:, 0]) / np.where(good, dep[:NB], 1.0)
        apy = RY / 2 + S * (d[:NB] @ R[:, 1]) / np.where(good, dep[:NB], 1.0)
        inf = int(((apx >= 0) & (apx < RX) & (apy >= 0) & (apy < RY) & good).sum())
        # the aperture's screen extent, in px, clipped to the frame
        w = float(min(apx.max(), RX) - max(apx.min(), 0.0)) if inf else 0.0
        h = float(min(apy.max(), RY) - max(apy.min(), 0.0)) if inf else 0.0
        rows.append((f, ppm, elev, float(zc), float(inf), w, h))

    A = np.array(rows)
    NEED = 6
    on = A[(A[:, 4] >= NEED) & (A[:, 0] >= DRIVER_FROM)]
    print("frames with >= %d/8 aperture corners in frame AND the driver present "
          "(f >= %d): %d of %d" % (NEED, DRIVER_FROM, len(on), len(A)))
    print("helmet 0.26 m at 366 px  ->  px/m check: %.1f" % (366 / 0.26))

    # what a 54 mm raise is worth, in pixels, per frame
    for dz, lab in ((0.054, "+54 mm (to the engine-cover deck)"),
                    (0.077, "+77 mm (joint-anchor vs suit-surface datum gap)"),
                    (0.135, "+135 mm (chest to the aperture's lower edge)"),
                    (0.229, "+229 mm (hip onto round 1's seat pan)")):
        px = on[:, 1] * dz
        print("  %-44s median %6.1f px  p90 %6.1f  max %7.1f"
              % (lab, np.median(px), np.percentile(px, 90), px.max()))

    # how long is the cockpit big at all?
    for thr in (100, 200, 300):
        n = int((on[:, 1] * 0.26 >= thr).sum())
        print("  helmet >= %4d px: %4d frames (%.2f s at 24 fps)" % (thr, n, n / 24.0))

    order = on[np.argsort(-on[:, 1])]
    print("\ntop 25 by px/m:")
    for r in order[:25]:
        print("   f%-5d px/m %7.1f  elev %5.1f deg  depth %5.2f m  aperture "
              "%4.0f x %4.0f px  54 mm = %5.1f px" %
              (r[0], r[1], r[2], r[3], r[5], r[6], r[1] * 0.054))

    out = os.path.join(R2, "docs/r2401_cockpit_sweep.json")
    json.dump({"columns": ["frame", "px_per_m", "elev_deg", "depth_m",
                           "aperture_corners_in_frame", "aperture_w_px",
                           "aperture_h_px"],
               "need_corners": NEED, "driver_from": DRIVER_FROM,
               "rows": A.tolist(),
               "landmarks_car_root_local": LM},
              open(out, "w"))
    print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
