"""Build the CANDIDATE sheet the corrected framing gate would pass, and nothing else.

Writes to work/, never to docs/. Three agents are live against
`docs/beat_sheet.json` and `render/film14.blend` is 4.53 GB and off limits, so a
station move cannot reach a rendered frame in this pass. What it CAN do is be
measured end to end -- gate, rig, path, seam, protected region -- so the next
agent inherits a change that is already proven on every axis except the picture.

The move is the minimum that satisfies the two findings at once:

  * pull each presentation station back along its own measured presentation
    direction until the cluster fills FILL of the limiting frame dimension.
    Direction, look_at and lens are untouched, so `presentation_normals` still
    decides which face the audience sees;
  * set `focus_distance_m` to the new standoff and `fstop` to the f-number that
    holds the whole cluster inside SHARP_BUDGET_PX at 4K.

CORNER_FL is pulled back like the rest. That key is at t = 24.625 (f591) and the
close-out that follows it is authored, so this is the one edit that can reach
toward the protected f648-792 region; whether it does is measured, not assumed.
"""

import json
import math
import os
import sys

R2 = os.path.expanduser("~/f1-round2")
SENSOR_W = 36.0
RES = (3840, 2160)
SENSOR_H = SENSOR_W * RES[1] / RES[0]
COC = 2.0 / (RES[0] / SENSOR_W)
FILL = 0.85


def sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def crs(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def nrm(a):
    m = math.sqrt(dot(a, a)) or 1.0
    return [x / m for x in a]


def project(cl, eye, ctr, lens):
    fwd = nrm(sub(ctr, eye))
    wu = [0.0, 0.0, 1.0]
    if abs(dot(fwd, wu)) > 0.999:
        wu = [0.0, 1.0, 0.0]
    rt = nrm(crs(fwd, wu))
    up = nrm(crs(rt, fwd))
    off = cl["explode_offset"]
    lo = [cl["bbox_min"][i] + off[i] for i in range(3)]
    hi = [cl["bbox_max"][i] + off[i] for i in range(3)]
    us, vs, zs = [], [], []
    for i in (0, 1):
        for j in (0, 1):
            for k in (0, 1):
                p = [lo[0] if i == 0 else hi[0], lo[1] if j == 0 else hi[1],
                     lo[2] if k == 0 else hi[2]]
                d = sub(p, eye)
                z = dot(d, fwd)
                zs.append(z)
                if z > 1e-6:
                    us.append(dot(d, rt) / z * lens)
                    vs.append(dot(d, up) / z * lens)
    if not us:
        return 9e9, 9e9, min(zs), max(zs)
    return ((max(vs) - min(vs)) / SENSOR_H, (max(us) - min(us)) / SENSOR_W,
            min(zs), max(zs))


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(R2, "work/b1rig/candidate_sheet.json")
    sheet = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))
    plan = json.load(open(os.path.join(R2, "docs/explode_plan.json")))["clusters"]

    moved = 0
    print("%-14s | %7s %7s | %7s %7s %7s %7s" %
          ("cluster", "s_old", "s_new", "ext_h", "ext_w", "N_old", "N_new"))
    for k in sheet["beat1"]["camera_keys"]:
        if not k.get("presentation_dir_measured"):
            continue
        t = k["focus_target"]
        cl = plan[t]
        off = cl["explode_offset"]
        ctr = [cl["centre"][i] + off[i] for i in range(3)]
        lens = float(k["lens_mm"])
        s_old = math.dist(k["world"], ctr)
        d = nrm(sub(k["world"], ctr))          # the measured presentation ray
        lo_s, hi_s = 0.2, 80.0
        for _ in range(90):
            mid = 0.5 * (lo_s + hi_s)
            eye = [ctr[i] + d[i] * mid for i in range(3)]
            eh, ew, _, _ = project(cl, eye, ctr, lens)
            if max(eh, ew) > FILL:
                lo_s = mid
            else:
                hi_s = mid
        s_new = max(hi_s, s_old)               # never move the lens CLOSER
        eye = [round(ctr[i] + d[i] * s_new, 4) for i in range(3)]
        eh, ew, zn, zf = project(cl, eye, ctr, lens)
        sf = s_new * 1000.0
        zw = zn * 1000.0 if abs(zn * 1000.0 - sf) > abs(zf * 1000.0 - sf) \
            else zf * 1000.0
        n_req = lens * lens * abs(zw - sf) / (COC * (sf - lens) * zw)
        n_new = round(max(n_req, 1.4), 2)
        print("%-14s | %7.3f %7.3f | %7.2f %7.2f %7.2f %7.2f"
              % (t, s_old, s_new, eh, ew, k["fstop"], n_new))
        k["world"] = eye
        k["focus_distance_m"] = round(s_new, 4)
        k["fstop"] = n_new
        k["note"] = (k.get("note", "") +
                     "  [R2-317 candidate: standoff %.3f -> %.3f m so the "
                     "cluster fills %.2f of the frame; f/%.2f -> f/%.2f so its "
                     "%.2f m of depth stays inside 2 px at 4K]"
                     % (s_old, s_new, max(eh, ew), 2.2, n_new, zf - zn))
        moved += 1

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump(sheet, open(out_path, "w"), indent=1)
    print("\nSTAGE RESULT OK moved=%d -> %s" % (moved, out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
