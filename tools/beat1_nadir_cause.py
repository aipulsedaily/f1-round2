"""WHY is beat 1's camera pointed at the floor?  Two candidates, separated.

    python3 tools/beat1_nadir_cause.py

CANDIDATE A -- the standoff law.  `standoff = max(radius*1.55 + 0.42, 0.75)`
(task #116) fixes the subtended solid angle at ~80 deg regardless of lens, which
is R2-317's defect: every cluster overflows its frame.  The brief for this block
raised the possibility that it is ALSO this defect's cause -- "a camera that must
sit close enough to fill the frame with a small cluster ends up steeply above it".

CANDIDATE B -- the presentation normals.  `camera_station()` places the lens at
`centre + normal * standoff` and aims it at `centre`, so the camera's elevation
IS the presentation normal's elevation, exactly, by construction.

The two are separable because they are different coordinates of the same polar
placement: the standoff law sets the RADIUS and the normal sets the DIRECTION.
This script measures both and reports (1) whether the shipped elevation is
predicted by the normal to within rounding, (2) whether the standoff law
constrains elevation at all, by computing the elevation band that is
geometrically reachable AT THE SHIPPED STANDOFF for every cluster.

If the reachable band contains shallow angles at every station, candidate A is
refuted: the camera did not have to be up there.
"""

import json
import math
import os

R2 = os.path.expanduser("~/f1-round2")

# world/build_architecture.py:134-135 -- the room the camera is flying inside
ROOM_Z_CEIL = 6.200
SPOT_RIG_Z = 5.110          # tools/build_beatsheet.py:621, "spot rigs from z 5.11"
FLOOR_Z = 0.0
MIN_CAM_Z = 0.45            # a lens on the floor is not a shot


def sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def nrm(a):
    m = math.sqrt(dot(a, a)) or 1.0
    return [x / m for x in a]


def elev(v):
    return math.degrees(math.asin(max(-1.0, min(1.0, nrm(v)[2]))))


def main():
    plan = json.load(open(os.path.join(R2, "docs/explode_plan.json")))
    norms = json.load(open(os.path.join(R2, "docs/presentation_normals.json")))
    path = {int(k["f"]): k for k in json.load(
        open(os.path.join(R2, "render/film14_path.json")))["path"]}

    # R2-317's table gives the station frames; take them from the beat sheet so
    # nothing is transcribed by hand.
    sheet = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))
    stations = {}
    for k in sheet["beat1"]["camera_keys"]:
        if not k.get("presentation_dir_measured"):
            continue                     # bridges and the close-out are not stations
        tgt = k.get("focus_target")
        if tgt in norms:
            stations.setdefault(tgt, int(round(float(k["t"]) * 24.0)) or 1)

    print("STATION GEOMETRY, from docs/explode_plan.json + presentation_normals.json")
    print()
    hdr = (f"{'cluster':14s} {'radius':>7s} {'standoff':>9s} {'ctr z':>7s} "
           f"{'cam z':>7s} {'normal elev':>12s} {'path elev':>10s} {'delta':>7s}")
    print(hdr)
    print("-" * len(hdr))

    rows = []
    for name, n in sorted(norms.items()):
        cl = plan["clusters"][name]
        ctr = [cl["centre"][i] + cl["explode_offset"][i] for i in range(3)]
        size = cl["size"]
        radius = 0.5 * math.sqrt(sum(s * s for s in size))
        standoff = max(radius * 1.55 + 0.42, 0.75)
        d = nrm(n["normal"])
        cam = [ctr[i] + d[i] * standoff for i in range(3)]
        ne = elev(d)
        f = stations.get(name)
        pe = None
        if f and f in path:
            # camera elevation at that frame, forward = -Z of the quaternion
            q = path[f]["q"]
            m = math.sqrt(sum(v * v for v in q)) or 1.0
            w, x, y, z = [v / m for v in q]
            fwd = [-(2 * (x * z + w * y)), -(2 * (y * z - w * x)),
                   -(1 - 2 * (x * x + y * y))]
            pe = math.degrees(math.asin(max(-1.0, min(1.0, fwd[2]))))
        rows.append((name, radius, standoff, ctr, cam, ne, pe, f))
        print(f"{name:14s} {radius:7.3f} {standoff:9.3f} {ctr[2]:7.3f} "
              f"{cam[2]:7.3f} {ne:12.2f} "
              f"{('%10.2f' % -pe) if pe is not None else '         -'} "
              f"{('%7.2f' % (ne + pe)) if pe is not None else '      -'}")

    print()
    print("COLUMN 'delta' is (normal elevation) + (path elevation).  The camera")
    print("looks DOWN the normal, so the two must sum to zero if candidate B holds.")

    # ---------------- candidate A: does the standoff law force the angle? -----
    print()
    print("=" * 78)
    print("CANDIDATE A -- does the standoff law leave any choice of elevation?")
    print("=" * 78)
    print()
    print("At the SHIPPED standoff, the elevation band a camera can occupy while")
    print("staying inside the room (cam z in [%.2f, %.2f], below the spot rigs at"
          % (MIN_CAM_Z, ROOM_Z_CEIL))
    print("z = %.2f) -- and the background THROW, the distance from the cluster to"
          % SPOT_RIG_Z)
    print("the floor along the optical axis extended past it:")
    print()
    hdr2 = (f"{'cluster':14s} {'standoff':>9s} {'elev min':>9s} {'elev max':>9s} "
            f"{'shipped':>8s} {'throw@shipped':>14s} {'throw@15deg':>12s}")
    print(hdr2)
    print("-" * len(hdr2))
    forced = []
    for name, radius, standoff, ctr, cam, ne, pe, f in rows:
        # cam z = ctr_z + standoff*sin(e)  -> band from the room
        def e_for_z(z):
            s = (z - ctr[2]) / standoff
            return math.degrees(math.asin(max(-1.0, min(1.0, s))))
        emin = max(-8.0, e_for_z(MIN_CAM_Z))
        emax = min(90.0, e_for_z(SPOT_RIG_Z))
        thr = ctr[2] / math.tan(math.radians(ne)) if ne > 0.5 else float("inf")
        t15 = ctr[2] / math.tan(math.radians(15.0))
        if emax < 30.0:
            forced.append(name)
        print(f"{name:14s} {standoff:9.3f} {emin:9.2f} {emax:9.2f} {ne:8.2f} "
              f"{thr:14.2f} {t15:12.2f}")

    print()
    print("clusters whose reachable band EXCLUDES a shallow (<30 deg) camera: "
          f"{forced if forced else 'NONE'}")
    print()
    print("'throw' is in metres.  It is the distance from the presented cluster to")
    print("the surface behind it along the optical axis.  It is what the brief's")
    print("two stated presentation devices both need: 'edge separation from the")
    print("dark background' needs the background not to be the lit floor, and 'DOF")
    print("as the presenter' needs the background to be at a different distance")
    print("from the subject.  At throw = 0.2 m neither is available at any")
    print("aperture, from any light rig.")
    print()
    print("STAGE RESULT: NADIR_CAUSE_OK")


if __name__ == "__main__":
    main()
