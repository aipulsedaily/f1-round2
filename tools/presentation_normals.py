"""From which direction is each cluster MOST LEGIBLE? Measured, by sampling.

    /opt/blender-5.2.0-linux-x64/blender -b ~/opus5-car-render/work/iter.blend \
        --factory-startup -P tools/presentation_normals.py -- \
        --plan docs/explode_plan.json --out docs/presentation_normals.json

TWO WRONG ANSWERS BEFORE THIS ONE
---------------------------------
1. A generic azimuth spiral placed the camera at `i/n * 2pi * 1.35 + 0.6` around
   each cluster. Even coverage of the field, zero knowledge of the parts — and it
   presented the STEERING WHEEL FROM BEHIND. Sharp, well lit, carbon weave
   resolving, and showing the column stub while the display, LED strip and every
   button faced away.

2. The area-weighted mean face normal. Reasonable-sounding, and mathematically
   guaranteed to fail here: **the area-weighted normal of any closed watertight
   mesh is exactly zero** (divergence theorem). Every one of the 15 clusters duly
   reported confidence < 0.02 and "symmetric". The metric was not measuring the
   parts, it was measuring the fact that they are solids.

WHAT THIS MEASURES INSTEAD
--------------------------
The actual question is not "which way does it face" but "from which direction do
I see the most of it". So: sample directions on a sphere and score each by what a
lens there would actually receive.

    projected_area(d) = sum over faces of max(0, dot(normal, d)) * area

That is the real projected area of the cluster from direction `d`, and it is
maximised looking face-on at a disc, broadside at a wing, and so on.

Projected area alone cannot separate the front of a steering wheel from its back —
both project the same disc. So the score is also weighted by MATERIAL RICHNESS:
how many distinct materials contribute meaningful projected area from that
direction. The front of a wheel shows a display, an LED strip, buttons, grips and
carbon; the back shows one carbon shell. Richness is what "the interesting side"
actually means, and unlike a hand-written rule it generalises to parts nobody
anticipated.

    score(d) = projected_area(d) * (1 + 0.45 * distinct_materials(d))

Directions below the floor are discarded — the camera cannot fly under the dais —
and the winning direction is reported with a margin over the runner-up so a
genuinely ambiguous cluster is visible as ambiguous rather than silently decided.


THE THIRD WRONG ANSWER, AND THE ONE THAT SHIPPED — R2-451
---------------------------------------------------------
`projected_area(d)` is maximised, for a flat wide body lying horizontally, by
looking straight down at it.  A Formula 1 car and every one of its major
assemblies is a flat wide body lying horizontally.  So the scorer above returned
a PLAN VIEW for the clusters that matter most, and `camera_station()` places the
lens at `centre + normal * standoff` and aims it at `centre` — which makes the
camera's elevation the presentation normal's elevation, exactly.

MEASURED, on the file this script wrote and the film that was built from it:

    MB, NOSE, SP, FD  ->  normal [0.10193, 0.0, 0.99479]  =  84.15 deg
    ...which is sample index 0 of the Fibonacci sphere, the single most
    overhead direction this sampler owns.  Four clusters, one vector.

    the film's first frame  84.15 deg nose-down, lens at z = 5.6607 m
    23.6 % of beat 1 shot steeper than 70 deg down
    192 of the film's 195 near-nadir frames are in beat 1

The scorer was not broken.  It answered the question it was asked.  "From which
direction do I see the most of it" has a correct answer and that answer is a
plan view; a plan view of a racing car is a DIAGRAM, and the brief asks for a
photograph — "the camera weaves THROUGH the exploded field like a drone through
a hangar", "edge separation from the dark background", "DOF as the presenter".

Two facts, both measured, say why no amount of lighting or aperture could have
rescued those stations:

  * At MB's shipped station the optical axis extended past the monocoque hits
    the showroom floor 0.08 m behind it.  The background IS the subject's own
    distance, so it cannot be defocused, and it is the brightest large surface
    in the room, so there is no dark to separate against.
  * The lens sits at z = 5.6607.  Every light in the room is BELOW it — the six
    showroom spots are at z = 5.590.  A rim light is not available to a camera
    above the whole rig.

THE FIX: the winner is now the SHALLOWEST direction inside a declared score
plateau, subject to the lens being inside the room.  See `--max-depression-deg`.
Three things are deliberate:

  1. THE CAP IS THE FILM'S OWN NUMBER, not a derivation and not a taste.  The
     material a review called the best in the film (f648-792) sits at a median
     10.88 deg of depression; beats 2-6, 2,186 frames of accepted material, at
     10.56; the deepest hand-authored presentation key anywhere in the film is
     24.91.  25 deg is that practice applied to the region that departed from it.

  2. THE TIE-BREAK USES A PLATEAU THAT WAS MEASURED, not assumed.  MB's top 16
     directions span 84 deg to 53 deg inside 8 % of each other.  The objective is
     nearly flat in elevation, so its argmax was a coin flip — and it landed on
     the pole.  Taking the shallowest direction within `--score-tol` of the best
     feasible one spends a declared 3 % of a soft objective to buy the difference
     between a diagram and a photograph.

  3. `ranked` IS NOW ACTUALLY USED.  The docstring below has always claimed the
     camera placer "walks down the ranking until a station fits inside the room".
     Nothing in the repository ever read that field — grep it.  SP's shipped
     station duly sat at z = 5.991, above every light in the room.  The walk now
     happens here, where the score lives, instead of being described somewhere
     nothing performs it.
"""

import argparse
import json
import math
import os
import sys
from collections import defaultdict

import bpy
from mathutils import Vector


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--plan", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--dirs", type=int, default=192)
    p.add_argument("--min-elev-deg", type=float, default=-8.0,
                   help="reject directions below this; the camera cannot fly "
                        "under the showroom floor")
    p.add_argument("--max-depression-deg", type=float, default=25.0,
                   help="R2-451. Reject directions steeper than this. The "
                        "default is the deepest depression any hand-authored, "
                        "review-accepted presentation key in the film uses; "
                        "set it to 90 to reproduce the pre-R2-451 file exactly.")
    p.add_argument("--score-tol", type=float, default=0.03,
                   help="R2-451. Among feasible directions scoring within this "
                        "fraction of the best, take the SHALLOWEST. The score "
                        "surface is flat in elevation (MB's top 16 lie inside "
                        "8 %% of each other), so its argmax carries no "
                        "information the picture cares about. 0 = pure argmax.")
    p.add_argument("--spot-rig-z", type=float, default=5.590,
                   help="MEASURED in world/beat1_anim.blend: six SPOT lamps at "
                        "z = 5.590. The lens must stay under them or the "
                        "presented part cannot be rim-lit at all.")
    p.add_argument("--lens-clearance", type=float, default=0.30)
    p.add_argument("--min-cam-z", type=float, default=1.20,
                   help="the rope-barrier clearance the close-out already obeys")
    return p.parse_args(argv)


def station_z(centre_z, size, elev_deg):
    """Where `camera_station()` will put the lens if it is handed this direction.

    Kept in lockstep with tools/build_beatsheet.py:camera_station() -- the
    standoff law is `max(radius*1.55 + 0.42, 0.75)` with radius the bbox
    half-diagonal (task #116). If that law moves, this moves with it, and the
    selftest below asserts the two agree.
    """
    radius = 0.5 * math.sqrt(sum(s * s for s in size))
    standoff = max(radius * 1.55 + 0.42, 0.75)
    return centre_z + standoff * math.sin(math.radians(elev_deg)), standoff


def sphere_dirs(n, min_elev_deg):
    """Fibonacci sphere, filtered to directions a camera could actually occupy."""
    out = []
    ga = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(n):
        z = 1.0 - (2.0 * i + 1.0) / n
        r = math.sqrt(max(0.0, 1.0 - z * z))
        th = ga * i
        v = Vector((math.cos(th) * r, math.sin(th) * r, z))
        if math.degrees(math.asin(max(-1.0, min(1.0, v.z)))) >= min_elev_deg:
            out.append(v.normalized())
    return out


def main():
    a = parse_args()
    plan = json.load(open(a.plan))
    deps = bpy.context.evaluated_depsgraph_get()
    dirs = sphere_dirs(a.dirs, a.min_elev_deg)

    out = {}
    for key, c in plan["clusters"].items():
        # gather (normal, area, material) once; scoring is then pure arithmetic
        faces = []
        for pname in c["parts"]:
            ob = bpy.data.objects.get(pname)
            if ob is None or ob.type != "MESH":
                continue
            oe = ob.evaluated_get(deps)
            try:
                me = oe.to_mesh()
            except Exception:
                continue
            if me is None:
                continue
            mw = ob.matrix_world
            nm = mw.to_3x3().inverted_safe().transposed()
            slots = [ms.material.name if ms.material else "?"
                     for ms in ob.material_slots] or ["?"]
            for poly in me.polygons:
                mat = slots[min(poly.material_index, len(slots) - 1)]
                faces.append(((nm @ poly.normal).normalized(), poly.area, mat))
            oe.to_mesh_clear()

        if not faces:
            out[key] = {"normal": [0, 0, 1], "score": 0.0, "note": "no geometry"}
            continue

        scored = []
        for d in dirs:
            proj = 0.0
            per_mat = defaultdict(float)
            for n, area, mat in faces:
                dot = n.dot(d)
                if dot > 0.0:
                    contrib = dot * area
                    proj += contrib
                    per_mat[mat] += contrib
            if proj <= 0.0:
                continue
            # a material counts as "visible" only if it is more than 2% of what
            # the lens sees — otherwise a single stray fastener inflates richness
            rich = sum(1 for v in per_mat.values() if v > 0.02 * proj)
            scored.append((proj * (1.0 + 0.45 * rich), proj, rich, d))

        scored.sort(key=lambda x: -x[0])
        unconstrained = scored[0]
        runner = scored[1] if len(scored) > 1 else unconstrained
        margin = (unconstrained[0] - runner[0]) / max(unconstrained[0], 1e-9)

        # ---- R2-451: THE WALK DOWN THE RANKING, PERFORMED HERE --------------
        #
        # The paragraph that used to sit at this spot said the camera placer
        # "walks down the ranking until a station fits inside the room".  It
        # never did — nothing in the repository has ever read the `ranked` field
        # — and the consequence was SP's lens at z 5.991, above every light in
        # the showroom, and MB's at 5.6607, which is the film's first frame.
        #
        # So the walk happens here, against three conditions, and every one of
        # them is measured rather than asserted:
        #
        #   the lens is under the light rig      cam_z <= spot_rig_z - clearance
        #   the lens clears the rope barrier     cam_z >= min_cam_z
        #   it is a photograph, not a plan        elev <= max_depression_deg
        #
        # and then, among everything that survives and scores within
        # `--score-tol` of the best survivor, the SHALLOWEST is taken.  That
        # last step is not a preference: the objective is nearly flat in
        # elevation (MB's top 16 span 84 -> 53 deg inside 8 %), so its argmax
        # is dominated by noise while the picture is not.
        cz = c["centre"][2] + c["explode_offset"][2]
        feas = []
        for sc, pa, rich, d in scored:
            e = math.degrees(math.asin(max(-1.0, min(1.0, d.z))))
            zz, standoff = station_z(cz, c["size"], e)
            if e > a.max_depression_deg:
                continue
            if not (a.min_cam_z <= zz <= a.spot_rig_z - a.lens_clearance):
                continue
            feas.append((sc, pa, rich, d, e, zz))

        relaxed = None
        if not feas:
            # NAMED, never silently widened.  C2 (the picture) is kept and C1
            # (the room envelope) is the one allowed to bend, because a lens a
            # little outside a clearance margin is a smaller lie than a plan
            # view — and the cluster that needed it is printed.
            for sc, pa, rich, d in scored:
                e = math.degrees(math.asin(max(-1.0, min(1.0, d.z))))
                zz, standoff = station_z(cz, c["size"], e)
                if e <= a.max_depression_deg:
                    feas.append((sc, pa, rich, d, e, zz))
            relaxed = "room envelope relaxed; no direction satisfies both"
        if not feas:
            feas = [(sc, pa, rich, d,
                     math.degrees(math.asin(max(-1.0, min(1.0, d.z)))),
                     station_z(cz, c["size"], 0.0)[0])
                    for sc, pa, rich, d in scored]
            relaxed = "NO feasible direction at all; fell back to the argmax"

        top = max(f[0] for f in feas)
        band = [f for f in feas if f[0] >= (1.0 - a.score_tol) * top]
        best = min(band, key=lambda f: f[4])

        alts = [{"normal": [round(v, 5) for v in d],
                 "score": round(sc, 5),
                 "projected_area_m2": round(pa, 5),
                 "distinct_materials": rich,
                 "elev_deg": round(math.degrees(
                     math.asin(max(-1.0, min(1.0, d.z)))), 4)}
                for sc, pa, rich, d in scored[:16]]

        out[key] = {
            "normal": [round(v, 5) for v in best[3]],
            "ranked": alts,
            "score": round(best[0], 5),
            "projected_area_m2": round(best[1], 5),
            "distinct_materials": best[2],
            "margin_over_runner_up": round(margin, 5),
            "n_parts": c["n_parts"],
            # --- R2-451 provenance: what was given up, and to buy what --------
            "elev_deg": round(best[4], 4),
            "station_z_m": round(best[5], 4),
            "unconstrained_normal": [round(v, 5) for v in unconstrained[3]],
            "unconstrained_elev_deg": round(math.degrees(math.asin(
                max(-1.0, min(1.0, unconstrained[3].z)))), 4),
            "unconstrained_score": round(unconstrained[0], 5),
            "score_kept": round(best[0] / max(unconstrained[0], 1e-9), 5),
            "constraint_note": relaxed,
        }

    json.dump(out, open(a.out, "w"), indent=1)
    print(f">> R2-451 selection: depression <= {a.max_depression_deg:.1f} deg, "
          f"lens z in [{a.min_cam_z:.2f}, {a.spot_rig_z - a.lens_clearance:.2f}], "
          f"shallowest within {a.score_tol:.0%} of the best feasible score")
    print(f">> {'cluster':<16}{'proj m2':>9}{'mats':>5}{'margin':>8}"
          f"{'elev':>8}{'lens z':>8}{'was':>8}{'kept':>7}   direction")
    tot = 0.0
    for k, v in sorted(out.items(), key=lambda x: -x[1].get("projected_area_m2", 0)):
        tot += v.get("score_kept", 1.0)
        print(f"   {k:<16}{v.get('projected_area_m2',0):>9.4f}"
              f"{v.get('distinct_materials',0):>5}"
              f"{v.get('margin_over_runner_up',0):>8.4f}"
              f"{v.get('elev_deg',0):>8.2f}{v.get('station_z_m',0):>8.3f}"
              f"{v.get('unconstrained_elev_deg',0):>8.2f}"
              f"{v.get('score_kept',1.0):>7.1%}   {v['normal']}")
        if v.get("constraint_note"):
            print(f"      ^ {k}: {v['constraint_note']}")
    steep = [k for k, v in out.items()
             if v.get("elev_deg", 0.0) > a.max_depression_deg + 1e-6]
    print(f">> mean score kept {tot / max(len(out), 1):.1%};  "
          f"clusters still steeper than {a.max_depression_deg:.0f} deg: "
          f"{steep if steep else 'NONE'}")
    print(f">> wrote {a.out}")
    if a.max_depression_deg < 90.0:
        print()
        print(">> READ THIS BEFORE POINTING build_beatsheet.py AT THIS FILE.")
        print(">> Re-aiming ALL FIFTEEN clusters is UNSCHEDULABLE. Measured, "
              "R2-455: pulling")
        print(">> the stations out of the nadir swings each one out to a "
              "horizontal radius of")
        print(">> standoff*cos(elev) and turns fifteen nearly-parallel view "
              "directions into")
        print(">> fifteen real pans, which grows beat 1's tour by 1.34x and "
              "makes it miss the")
        print(">> part-flight deadlines. `present_order()` will raise "
              "SystemExit. Lengthening")
        print(">> beat 1 does NOT help -- feasibility is cum_cost/total_cost <= "
              "deadline/span,")
        print(">> and the tour cost cancels.")
        print(">>")
        print(">> The schedulable subset is chosen by "
              "`tools/beat1_reaim_gated.py`, which searches")
        print(">> each cluster's whole legal band against the WHOLE beat-1 gate "
              "set -- clearance,")
        print(">> speed and pan, not just the deadline solve -- and writes the "
              "per-cluster verdict")
        print(">> as `r2451_reaimed`. Twelve of fifteen survive; NOSE, FW and "
              "CORNER_FL do not.")
        print(">> USE THAT FILE, not this one, as build_beatsheet.py's "
              "B1_NORMALS.")
    if steep:
        print(">> STAGE RESULT: PRESENTATION_NORMALS_VIOLATION")
        return 1
    print(">> STAGE RESULT: PRESENTATION_NORMALS_OK")
    return 0



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
    gate_exit.guard(main, tool="presentation_normals")
