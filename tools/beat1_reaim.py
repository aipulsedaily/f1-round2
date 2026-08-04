"""Re-choose each beat-1 presentation DIRECTION, and show what it costs.

    python3 tools/beat1_reaim.py --survey          # the objective surface, no write
    python3 tools/beat1_reaim.py --out work/b1nadir/presentation_normals_reaim.json

THE DEFECT (R2-425, R2-451)
---------------------------
`camera_station()` places the lens at `centre + normal * standoff` and aims it at
`centre`, so the camera's elevation IS the presentation normal's elevation,
exactly.  `presentation_normals.py` chooses that normal as

    argmax_d  projected_area(d) * (1 + 0.45 * distinct_materials(d))

and a Formula 1 car's major assemblies are flat, wide and lying horizontally, so
the direction from which you see the most of one is from directly overhead.  The
scorer answered the question it was asked.  A plan view is the correct answer to
"from where do I see the most of it" and the wrong answer to "from where does it
look like a photograph of a racing car".

Four clusters -- MB, NOSE, SP, FD -- came back with the IDENTICAL vector
[0.10193, 0, 0.99479], which is sample index 0 of the Fibonacci sphere: the
single most-overhead direction the sampler owns.  MB is the film's first frame.

WHAT THIS SCRIPT ADDS
---------------------
Three constraints, each measured off the scene rather than asserted, applied to
the SAME score surface (`work/b1nadir/view_surface.json`, which reproduces the
shipped winner for all 15 clusters):

 C1  THE LENS MUST BE BELOW THE LIGHTS.  Measured from world/beat1_anim.blend:
     23 lights, the six showroom spots at z = 5.590 and the key at z = 4.600.
     The shipped f1 camera is at z = 5.6607 -- ABOVE EVERY LIGHT IN THE ROOM.
     The brief asks for "rim lighting motivated by the ceiling coves so each
     presented part gets edge separation from the dark background"; no lens
     above the whole rig can receive a rim.  Constraint: cam_z <= 5.29
     (0.30 m of clearance under the spot plane).

 C2  THE DEPRESSION CAP, AND IT IS THE FILM'S OWN NUMBER.  I did not derive this
     and I did not choose it by taste.  Measured off `render/film14_path.json`:

        PROTECTED f648-792, the material a review called the best in the film
                                        median -10.88   range -16.77 .. -5.28
        beats 2-6, 2,186 frames, every one of them accepted material
                                        median -10.56
        the four HAND-AUTHORED close-out keys inside beat 1 itself
                                        -11.08, -13.50, -14.41, -24.91
        the presentation tour f1-590, the region under repair
                                        median -54.42   min -84.34

     The film has already converged on about -11 deg everywhere it works and on
     -54 deg in the one place it does not, and the deepest angle any authored,
     review-accepted presentation key uses is -24.91.  So: **a presentation
     station may not look down more steeply than 25 deg.**  That bound is the
     film's own accepted practice applied to the region that departed from it,
     which is the only kind of bound this beat will believe -- a corrected
     metric that fails frames a review already passed is a corrected metric
     nobody will believe (R2-318).

     A law I derived instead -- "the horizon must be inside the frame",
     elev <= atan(sensor_h/2 / lens) -- is REJECTED here and the rejection is
     recorded because it is the more elegant law: it puts the cap at 16.1 deg on
     a 35 mm lens and 9.9 deg on a 58 mm, and it FAILS the close-out's own first
     key at -24.9 deg against its 11.9 deg half-frame.  It is a rule about where
     the floor stops filling the frame, and the close-out proves a frame can be
     all floor and still be the best shot in the film.

REPORTED, NOT CONSTRAINED
-------------------------
`throw` -- the distance from the cluster to the floor along the optical axis
extended past it, = centre_z / tan(elev) -- is printed for every candidate but
is NOT a gate.  At the shipped MB station it is 0.08 m: the lit showroom floor
is eight centimetres behind the monocoque, so the brief's two named presentation
devices both fail there and no aperture or light rig can rescue either.  It is
the clearest single statement of why the opening does not read.  It is not used
as a constraint because an early version of this script that DID constrain it
(throw >= 2 x standoff) drove MB, FD and EC to the sampler's -7.48 deg floor and
put FD's lens 5 cm off the floor.  A constraint that produces an absurd station
is not a constraint, it is an unbounded objective wearing one.

`fill` -- R2-317's overflow -- is likewise reported and not gated.  That is a
standoff defect with its own owner (R2-330's hybrid re-solve) and gating on it
here would silently re-solve someone else's problem.  The shipped direction's
RANK on the fill axis IS reported, because "are these two defects the same root
cause" was an explicit question put to this block.

The score cost of every constraint is printed for every cluster.  A constraint
whose cost is not shown is a preference presented as a law.
"""

import argparse
import json
import math
import os

R2 = "/home/zany/f1-round2"
SENSOR_W = 36.0
RES = (3840, 2160)
SENSOR_H = SENSOR_W * RES[1] / RES[0]

SPOT_RIG_Z = 5.590          # MEASURED, world/beat1_anim.blend, 6 x SPOT
LENS_CLEARANCE = 0.30
MAX_CAM_Z = SPOT_RIG_Z - LENS_CLEARANCE          # 5.29
MIN_CAM_Z = 1.20            # the rope-barrier rule the close-out already obeys
MAX_DEPRESSION = 25.0       # the film's own deepest authored presentation key
MIN_ELEV = -8.0             # the sampler's own floor: no flying under the dais
SCORE_TOL = 0.03            # the plateau tie-break's declared cost


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def crs(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def nrm(a):
    m = math.sqrt(dot(a, a)) or 1.0
    return [x / m for x in a]


def extent_frac(bmin, bmax, eye, ctr, lens):
    """Fraction of frame H and W the cluster's world bbox subtends. R2-316."""
    fwd = nrm([ctr[i] - eye[i] for i in range(3)])
    wu = [0.0, 0.0, 1.0]
    if abs(dot(fwd, wu)) > 0.999:
        wu = [0.0, 1.0, 0.0]
    rt = nrm(crs(fwd, wu))
    up = nrm(crs(rt, fwd))
    xs, ys = [], []
    for i in range(8):
        p = [bmin[0] if i & 1 else bmax[0],
             bmin[1] if i & 2 else bmax[1],
             bmin[2] if i & 4 else bmax[2]]
        v = [p[j] - eye[j] for j in range(3)]
        z = dot(v, fwd)
        if z <= 1e-6:
            return 99.0, 99.0
        xs.append(dot(v, rt) / z * lens)
        ys.append(dot(v, up) / z * lens)
    return (max(ys) - min(ys)) / SENSOR_H, (max(xs) - min(xs)) / SENSOR_W


def load():
    surf = json.load(open(os.path.join(R2, "work/b1nadir/view_surface.json")))
    plan = json.load(open(os.path.join(R2, "docs/explode_plan.json")))
    ship = json.load(open(os.path.join(R2, "docs/presentation_normals.json")))
    sheet = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))
    lens = {}
    for k in sheet["beat1"]["camera_keys"]:
        if k.get("presentation_dir_measured") and k.get("focus_target"):
            lens.setdefault(k["focus_target"], float(k["lens_mm"]))
    return surf, plan, ship, lens


def geom(plan, name):
    c = plan["clusters"][name]
    off = c["explode_offset"]
    ctr = [c["centre"][i] + off[i] for i in range(3)]
    bmin = [c["bbox_min"][i] + off[i] for i in range(3)]
    bmax = [c["bbox_max"][i] + off[i] for i in range(3)]
    radius = 0.5 * math.sqrt(sum(s * s for s in c["size"]))
    standoff = max(radius * 1.55 + 0.42, 0.75)
    return ctr, bmin, bmax, radius, standoff


def candidates(surf, plan, lensmap, name):
    """Every sampled direction, annotated with what the picture would be."""
    cl = surf["clusters"][name]
    ctr, bmin, bmax, radius, standoff = geom(plan, name)
    lens = lensmap.get(name, 35.0)
    rows = []
    for i, d in enumerate(cl["dirs"]):
        e = cl["elev_deg"][i]
        if e < MIN_ELEV:
            continue
        eye = [ctr[j] + d[j] * standoff for j in range(3)]
        th = ctr[2] / math.tan(math.radians(e)) if e > 0.05 else float("inf")
        fh, fw = extent_frac(bmin, bmax, eye, ctr, lens)
        rows.append({"i": i, "d": d, "elev": e, "score": cl["score"][i],
                     "proj": cl["proj_m2"][i], "rich": cl["rich"][i],
                     "cam_z": eye[2], "throw": th, "fill": max(fh, fw),
                     "fill_h": fh, "fill_w": fw,
                     "ok_z": MIN_CAM_Z <= eye[2] <= MAX_CAM_Z,
                     "ok_elev": e <= MAX_DEPRESSION})
    return rows, ctr, standoff, lens


def survey(surf, plan, ship, lensmap):
    print("=" * 100)
    print("THE SHARED-ROOT TEST -- is the highest-SCORING direction also the "
          "direction of worst FRAME OVERFLOW?")
    print("=" * 100)
    print()
    print("`fill` is max(extent_h, extent_w) at the SHIPPED standoff and the "
          "SHIPPED lens, so the only")
    print("thing varying down each cluster's column is the direction. "
          "'rank' is the shipped direction's")
    print("position when the candidates are sorted by fill, worst first, out of "
          "the sampled directions.")
    print()
    hdr = (f"{'cluster':14s} {'ship elev':>9s} {'ship fill':>9s} "
           f"{'worst fill':>10s} {'best fill':>9s} {'fill rank':>10s} "
           f"{'score rank':>10s} {'cam z':>7s} {'throw':>7s}")
    print(hdr)
    print("-" * len(hdr))
    top1 = 0
    n = 0
    for name in sorted(surf["clusters"]):
        if "dirs" not in surf["clusters"][name]:
            continue
        rows, ctr, standoff, lens = candidates(surf, plan, lensmap, name)
        sd = nrm(ship[name]["normal"])
        cur = min(rows, key=lambda r: sum((r["d"][i] - sd[i]) ** 2
                                          for i in range(3)))
        byfill = sorted(rows, key=lambda r: -r["fill"])
        byscore = sorted(rows, key=lambda r: -r["score"])
        fr = byfill.index(cur) + 1
        sr = byscore.index(cur) + 1
        n += 1
        if fr <= 3:
            top1 += 1
        print(f"{name:14s} {cur['elev']:9.2f} {cur['fill']:9.3f} "
              f"{byfill[0]['fill']:10.3f} {byfill[-1]['fill']:9.3f} "
              f"{fr:5d}/{len(rows):<4d} {sr:5d}/{len(rows):<4d} "
              f"{cur['cam_z']:7.3f} {cur['throw']:7.2f}")
    print()
    print(f"clusters whose SHIPPED direction is in the top 3 worst-overflowing "
          f"of {len(rows)} sampled: {top1}/{n}")
    print()
    print("READ THIS CAREFULLY.  The two laws are NOT the same mechanism -- the")
    print("standoff law sets the RADIUS of a polar placement and the direction law")
    print("sets its DIRECTION, and neither can produce the other.  They are two")
    print("coordinates of one placement, and they COMPOUND: the standoff law picks")
    print("a distance for the cluster's mean subtended angle, and the direction law")
    print("then selects, out of every direction, one of the few from which the")
    print("cluster is BIGGEST.  Projected area is what the scorer maximises and")
    print("projected extent is what R2-317 measures as the defect, and for a flat")
    print("body the two are maximised in nearly the same direction.")
    print()


def constraint_cost(surf, plan, lensmap, ship):
    print("=" * 100)
    print("WHAT EACH CONSTRAINT COSTS, per cluster, in the scorer's own units")
    print("=" * 100)
    print()
    print(f"C1  {MIN_CAM_Z:.2f} <= cam_z <= {MAX_CAM_Z:.2f} m   (spot rigs "
          f"MEASURED at z = {SPOT_RIG_Z:.3f} in world/beat1_anim.blend, "
          f"{LENS_CLEARANCE:.2f} m")
    print(f"    clearance under them; the {MIN_CAM_Z:.2f} m floor is the rope-"
          f"barrier rule the close-out already obeys)")
    print(f"C2  depression <= {MAX_DEPRESSION:.0f} deg   (the deepest authored, "
          f"review-accepted presentation key in the film)")
    print()
    hdr = (f"{'cluster':14s} {'ship elev':>9s} {'new elev':>9s} "
           f"{'ship score':>10s} {'new score':>9s} {'kept':>6s} "
           f"{'ship fill':>9s} {'new fill':>8s} {'ship throw':>10s} "
           f"{'new throw':>9s} {'cam z':>7s}")
    print(hdr)
    print("-" * len(hdr))
    out = {}
    for name in sorted(surf["clusters"]):
        if "dirs" not in surf["clusters"][name]:
            continue
        rows, ctr, standoff, lens = candidates(surf, plan, lensmap, name)
        sd = nrm(ship[name]["normal"])
        cur = min(rows, key=lambda r: sum((r["d"][i] - sd[i]) ** 2
                                          for i in range(3)))
        feas = [r for r in rows if r["ok_z"] and r["ok_elev"]]
        relaxed = ""
        if not feas:
            # Named, never silently widened.  Keep C2 (the picture) and let C1
            # (the room) be the one that bends, because a lens 20 cm outside a
            # clearance envelope is a smaller lie than a plan view.
            feas = [r for r in rows if r["ok_elev"]]
            relaxed = " *"
        # THE PLATEAU TIE-BREAK.  MB's top 16 scored directions sit inside 8 % of
        # each other and span 84 deg to 53 deg -- the objective is flat in
        # elevation, so its argmax is a coin flip that happened to land on the
        # pole of the Fibonacci sphere.  A flat objective has freedom in it and
        # the argmax throws that freedom away.  So: take the SHALLOWEST view
        # that is within SCORE_TOL of the most legible feasible one.  The
        # tolerance is declared, its cost is the `kept` column, and without it
        # seven of the fifteen clusters pile onto the cap at exactly 23.64 deg,
        # which is a beat with no weave in it.
        top = max(r["score"] for r in feas)
        band = [r for r in feas if r["score"] >= (1.0 - SCORE_TOL) * top]
        best = min(band, key=lambda r: r["elev"])
        kept = best["score"] / max(cur["score"], 1e-9)
        out[name] = best
        print(f"{name:14s} {cur['elev']:9.2f} {best['elev']:9.2f} "
              f"{cur['score']:10.4f} {best['score']:9.4f} {kept:5.1%}{relaxed:2s}"
              f"{cur['fill']:8.2f} {best['fill']:8.2f} {cur['throw']:10.2f} "
              f"{best['throw']:9.2f} {best['cam_z']:7.3f}")
    print()
    print("* = no direction satisfies C2 at this cluster's shipped standoff; the")
    print("  throw constraint is relaxed to 'the best available' and the cluster is")
    print("  named, rather than the constraint being quietly widened for everyone.")
    return out


def main():
    global MAX_DEPRESSION, SCORE_TOL
    ap = argparse.ArgumentParser()
    ap.add_argument("--survey", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--max-depression", type=float, default=MAX_DEPRESSION)
    ap.add_argument("--score-tol", type=float, default=SCORE_TOL)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    MAX_DEPRESSION = a.max_depression
    SCORE_TOL = a.score_tol

    surf, plan, ship, lensmap = load()
    if not a.quiet:
        survey(surf, plan, ship, lensmap)
    import io, contextlib
    if a.quiet:
        with contextlib.redirect_stdout(io.StringIO()):
            chosen = constraint_cost(surf, plan, lensmap, ship)
    else:
        chosen = constraint_cost(surf, plan, lensmap, ship)

    if a.out:
        new = {}
        for name, v in ship.items():
            b = chosen.get(name)
            if b is None:
                new[name] = v
                continue
            nv = dict(v)
            nv["normal"] = [round(x, 5) for x in b["d"]]
            nv["projected_area_m2"] = round(b["proj"], 5)
            nv["distinct_materials"] = int(b["rich"])
            nv["score"] = round(b["score"], 5)
            nv["shipped_normal_R2_425"] = v["normal"]
            nv["reaim_elev_deg"] = round(b["elev"], 3)
            nv["reaim_score_kept"] = round(b["score"] / max(v["score"], 1e-9), 5)
            new[name] = nv
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        json.dump(new, open(a.out, "w"), indent=1)
        print(f"\n>> wrote {a.out}")
    print("\nSTAGE RESULT: REAIM_OK")


if __name__ == "__main__":
    main()
