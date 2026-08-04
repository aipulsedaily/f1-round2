#!/usr/bin/env python3
"""HOW BIG IS A SHED FRAME MEMBER ON SCREEN, at a given film frame.

    .venv/bin/python sim/shedpx.py --frame 880 \\
        --film sim/out/breach_film.npz \\
        --ref  sim/out/breach_film_R6_SHIPPED.npz \\
        --out  sim/out/shedpx_f0880.json

Beat 3 is where R6 actually pays: at f0880 two segments of mullion 5 tumble in
the aperture beside the car, projecting 426 x 428 px and 461 x 292 px at 4K.
A job that chases the CLOSING frame must not cost that, and "must not cost
that" needs a number that can be compared, not two pictures and an opinion.

Computed from the film table and `eastframe.plan()` alone -- no render, no
Blender, so it can be run the moment a bake lands and hours before its frames
come back from the farm.

TWO THINGS IT DELIBERATELY DOES NOT DO ITSELF.  The film table is read through
`resample.read_film`, and the pose at a frame through that module's own
`expand()`, so this measures the SAME reconstruction the applier keys and the
verifier checks -- the decimated curves re-evaluated with linear interpolation
-- rather than a second implementation of it that could drift.  The projection
goes through `wallproj`, which every other pixel figure in this block goes
through and which was validated against an independent agent's 28.5 x 77.6 px.

It reports EVERY replaced piece, sorted by projected area, so a regression is
a piece that got smaller and a gain is a piece that was not there before --
rather than whichever two numbers somebody chose to quote.
"""

import argparse
import json
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "sim"))
import eastframe as EF                                            # noqa: E402
import resample as RS                                             # noqa: E402
import wallproj as PJ                                             # noqa: E402


def qmat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def measure(path, frame, track):
    film = RS.read_film(path)
    names = film["names"]
    idx = {n: i for i, n in enumerate(names)}
    home = np.array([film["keys_of"](i)[1][0] for i in range(len(names))],
                    float)
    pl = EF.plan(names, film["release"], home)
    L, Q = film["expand"]([frame])          # the reconstruction, not the bake

    rows = {}
    for p in pl["pieces"]:
        if p["driver"] is None:
            continue
        j = idx[p["driver"]]
        loc, q = L[0, j], Q[0, j]
        piv = np.asarray(p["pivot"], float)
        # a box is (x0, x1, y0, y1, z0, z1); use eastframe's own vertex order
        # rather than a second copy of the convention
        C = np.concatenate([EF._box_verts(b) for b in p["boxes"]])
        W = (qmat(q) @ (C - piv).T).T + loc
        uv, zc, _ = PJ.project(frame, W, track)
        if (zc <= 0).any():
            # behind the camera: a projected box is meaningless there and a
            # silently huge number would be worse than an omission
            rows[p["name"]] = dict(behind_camera=True)
            continue
        w = float(uv[:, 0].max() - uv[:, 0].min())
        h = float(uv[:, 1].max() - uv[:, 1].min())
        home_loc = film["keys_of"](j)[1][0]
        rows[p["name"]] = dict(
            w_px=round(w, 1), h_px=round(h, 1), area_px=round(w * h, 0),
            range_m=round(float(zc.mean()), 2),
            travel_m=round(float(np.linalg.norm(loc - home_loc)), 4))
    return dict(table=os.path.basename(path), n_pieces=len(pl["pieces"]),
                mullions_replaced=sorted(pl.get("mullions_replaced", [])),
                pieces=rows)


def area(v):
    return v.get("area_px", 0.0) if not v.get("behind_camera") else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", type=int, default=880)
    ap.add_argument("--film", default=os.path.join(R2,
                                                   "sim/out/breach_film.npz"))
    ap.add_argument("--ref", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--track", default=PJ.TRACK)
    a = ap.parse_args()
    track = PJ.load(a.track)

    now = measure(a.film, a.frame, track)
    doc = dict(frame=a.frame, track=a.track, after=now)
    print("frame %d, %s: %d pieces, mullions replaced %s"
          % (a.frame, now["table"], now["n_pieces"], now["mullions_replaced"]))
    for k, v in sorted(now["pieces"].items(), key=lambda kv: -area(kv[1]))[:8]:
        if v.get("behind_camera"):
            continue
        print("   %-18s %7.1f x %7.1f px  area %10.0f  travel %8.3f m"
              % (k, v["w_px"], v["h_px"], v["area_px"], v["travel_m"]))

    verdict = "no reference"
    if a.ref and os.path.exists(a.ref):
        ref = measure(a.ref, a.frame, track)
        doc["before"] = ref
        shrunk, grew, new = [], [], []
        for k, v in now["pieces"].items():
            r = ref["pieces"].get(k)
            if r is None:
                new.append(k)
            elif area(v) < 0.9 * area(r):
                shrunk.append([k, area(r), area(v)])
            elif area(v) > 1.1 * area(r):
                grew.append([k, area(r), area(v)])
        gone = [k for k in ref["pieces"] if k not in now["pieces"]]
        doc["regression"] = dict(shrunk=shrunk, grew=grew,
                                 new_pieces=new, pieces_gone=gone)
        print("\nvs %s: %d shrunk >10%%, %d grew >10%%, %d new pieces, "
              "%d pieces gone" % (ref["table"], len(shrunk), len(grew),
                                  len(new), len(gone)))
        for k, r, v in sorted(shrunk, key=lambda t: t[1] - t[2],
                              reverse=True)[:8]:
            print("   SHRUNK %-18s %10.0f -> %10.0f px" % (k, r, v))
        for k, r, v in sorted(grew, key=lambda t: t[2] - t[1],
                              reverse=True)[:8]:
            print("   GREW   %-18s %10.0f -> %10.0f px" % (k, r, v))
        verdict = "NONE" if (not shrunk and not gone) else "CHECK"
    print("STAGE RESULT: shedpx f%04d  regression=%s" % (a.frame, verdict))

    if a.out:
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with open(a.out, "w") as fh:
            json.dump(doc, fh, indent=1, default=float)
        print("wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
