#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spectator_crowd_world.py — THE WHOLE CROWD, ON THE SEATS THE WORLD BUILT.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/spectator_crowd_world.py -- \
        --out world/items/spectator_crowd_world.blend

WHAT THIS IS AND IS NOT
=======================
It is **not** a new figure generator and it is not a new crowd composer.
`world/items/spectator_crowd.py` + `world/humankit.py` are both of those, they
are `ITEM_ACCEPTED` 8 of 8 on their own gate, and `spectator_crowd --selftest`
is 14 checks 0 failed with a control on every one.  Nothing here rebuilds any
of it.

It is the **seating plan for the whole circuit**, and it exists because
`world/items/PLACEMENT.json` blocks `spectator_crowd` on `NO_WORLD_FRAME` —
*"the test blend lays the population out on a grid for the macro camera; the
module never resolves world positions, so there is nothing to place"* — and
**that blocker is false**.  Measured off `spectator_crowd_test.blend`'s own
depsgraph: 3,803 realised instances at world x[263.34, 395.69] y[51.65, 168.34]
z[2.56, 10.05], against TRIBUNE PRINCIPALE's seats at x[262.96, 397.02]
y[51.65, 168.34] z[3.00, 10.06].  **The population was already standing on the
real stand.**  The grid is the 894-source library contact sheet, which is a
different collection.

So this file does three things the existing module does not, and each of them
is a number rather than a preference.

1.  IT SEATS THE CROWD ON THE SEATS THAT EXIST.
    `spectator_crowd.seat_array()` reads `grandstand_riser_unit.seat_grid()`,
    which returns **18,408** seats.  `build_architecture` — the module that
    actually casts the chairs into the ship — casts **18,350**, and
    `assembly9_build.json` records `grandstand_seats = 18350` from its own
    counter.  `world/items/grandstand_seats.py` replays `_grandstand_block()`
    with its own per-block seed and publishes the register; this file reads
    that.  The 58-seat difference is small.  The next one is not.

2.  IT DOES NOT SIT ANYBODY ON A FOLDED SEAT.
    `build_architecture._seat()` folds a tip-up seat at `rng.random() < 0.22`
    on seat kinds 0 and 2 — TRIBUNE OUEST, T15, PRINCIPALE and EST.
    **3,311 of the 18,350 chairs in this world are folded up.**  A figure on
    one is sitting on a vertical seat back with nothing under it.  Neither
    seat register knew this before; it is only visible by replaying the
    builder's own random stream.  15,039 seats can hold a person, and that —
    not 18,350 — is the occupancy ceiling.

        block                seats  kind   folded    pct
        TRIBUNE OUEST        3,071     0      669  21.8 %
        TRIBUNE T15          4,077     2      868  21.3 %
        VIRAGE OUEST         2,143     1        0   0.0 %
        TRIBUNE PRINCIPALE   5,542     0    1,231  22.2 %
        TRIBUNE EST          2,522     2      543  21.5 %
        TRIBUNE TEMPORAIRE     995     3        0   0.0 %

    The fold pattern is also the first layer of the patchiness a grandstand
    needs, and it is one the architecture already chose.  It is not noise
    added on top of a full stand: it is 18 % of the seating physically unable
    to hold anybody, in a spatial pattern that differs block by block.

3.  EVERY BLOCK LOOKS AT THE CAR AT THE MOMENT THE CAMERA LOOKS AT IT.
    The crowd is static geometry in a single 124 s take, so its gaze is baked
    once.  `spectator_crowd.build_scene` bakes it at one frame for one block.
    Six blocks are read by the camera at six different moments, so each block's
    focus is `car_at(f)` at the frame where THAT block carries the most crowd
    pixels — measured in `work/r2296/frame_area.json` by projecting all 18,350
    seats through `render/film14_path.json` and ray-casting each one against
    `assembly9`'s own `ARCH_Grandstand_*` meshes.  The frames are pinned in
    `world/items/crowd_focus_frames.json` so a rebuild reproduces them.

WHAT THE CAMERA ACTUALLY SEES, AND WHY THAT SETS THE BUDGET
===========================================================
Measured, not taken from the manifest.  Every one of the 18,350 seats projected
through every one of the 2,978 frames of `film14_path.json`, at 3840x2160 /
36 mm sensor, with one ray per in-frame seat against the shipping world's own
grandstand meshes (5,785,050 rays; control: the same rays aimed 200 m BEHIND
each seat return 0 of 400 unoccluded against 277 of 400 for the seats):

    largest seated figure anywhere in the film         54.4 px   (f2614)
    median per-seat peak                               36.1 px
    95th percentile per-seat peak                      44.9 px
    seats that ever exceed 60 px                            0
    nearest camera-facing seat, whole take               32.7 m
    frames carrying any unoccluded seat        655 of 2,978  (27.3 s)
    peak crowd coverage of one 4K frame               15.58 %   (f2607)

`docs/item_manifest.json` scores this item **hero, 14.7 m, 254 px**, and
`docs/screen_presence.json` gives it **peak_sharp 199.1 px**.  Neither is about
a seat: the manifest's 14.7 m never happens, and `screen_presence`'s number is a
ZONE figure — 159.3 px/m times a declared height, shared identically by
`spectator_seated`, `spectator_standing_ga` and `ga_viewing_bank`, and driven by
`ARCH_LaPasserelle` at 10.756 m (`HUMAN-REFERENCE.md` §0000000.3 reaches the
same conclusion independently).  **The real number is 4.7x smaller than the
manifest's.**

That is why the library is built at the module's own default `L1` and not
pushed to `L0`: at 54 px of FIGURE the head is 14 px, and the whole seven-pass
quality campaign in `HUMAN-REFERENCE.md` was judged at 47-960 px of HEAD.  The
open cosmetic defects there — the hair crust, the cap draw, the face relief —
are between one and two orders of magnitude below a pixel here.  The thing that
is not below a pixel is whether the stands are empty.

THE NO-REPEATS LINE
===================
894 library sources for ~12,000 people is ~13 copies of each source, and that
is the number this file has to defend.  It is defended spatially, not globally:

  * `spectator_crowd._separate_twins` re-rolls `k` wherever two people within
    `TWIN_RADIUS_M = 2.6` m drew the same source.  Its own selftest measures
    **0 of 21,519 neighbour pairs within 2.6 m share a source**, against a
    uniform-hash control at 119 of 21,519 (0.553 %).
  * The plan is built **per block**, so the six blocks' twin fields are solved
    independently — and two blocks are 200-400 m apart, which is not a
    neighbourhood any viewer reads.
  * `top_share` per family: 1 source of 900 objects = 0.11 %, against
    `build_items.FAMILY_TOP_SHARE_MAX` of 10 %.
  * And it is measured ON SCREEN rather than asserted, by
    `--measure-twins`: project every placed person through the film's own
    camera at the frames where the crowd is largest and count neighbour pairs
    within 4 head-widths that share a source, against a control that assigns
    sources by a uniform hash on the same points.

THE LIBRARY DOES NOT SHIP VISIBLE
=================================
`build_library(yard=None)` sets `hide_render = True` on every source, which is
the branch `spectator_crowd` wrote for exactly this and which is NOT the branch
its test blend uses — the test blend puts the 894 sources on a contact sheet at
world x[216.8, 247.0] y[-4.3, 44.0] z[0.95, 1.46] with `hide_render = False`,
because `item_gate` picks the median-triangle object out of the collection and
a hidden one renders an empty sky.  **That yard is inside the 4K frustum on 545
of the 2,978 frames, closest at 60.6 m, where a 1.7 m figure is 105 px tall —
twice the size of any spectator in the film.**  Shipping the test blend as-is
would stand 894 unaccounted people in a field beside the circuit, each bigger
on screen than anyone in the stands.  This file takes the `yard=None` branch and
`--verify` re-reads `hide_render` off the saved artefact rather than trusting it.
"""

import argparse
import json
import math
import os
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
for _p in (_WORLD, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import grandstand_seats as GS                                  # noqa: E402
import spectator_crowd as SC                                   # noqa: E402
import humankit as HK                                          # noqa: E402
import itemkit as K                                            # noqa: E402

try:
    import bpy
except ImportError:                                            # pragma: no cover
    bpy = None

#: Same identity as the gated item: same collection, same prefix, same manifest
#: record.  `build_items` refuses to append a collection whose name the scene
#: already holds, so the two rows can never both land.
COLL = SC.COLL
PFX = SC.PFX
LIB_COLL = SC.LIB_COLL
ITEM = SC.ITEM
SEED = 20260804

FOCUS_FRAMES = os.path.join(_HERE, "crowd_focus_frames.json")

#: TARGET OCCUPANCY AS A FRACTION OF THE BLOCK'S PHYSICAL SEATS -- folded ones
#: included in the denominator, because a folded seat is a seat a viewer can
#: see is empty.  These are the only taste numbers in this file and they are
#: stated as taste.  What is NOT taste is the ceiling: a block whose seats are
#: 22 % folded cannot exceed 0.78 however full the race is, and TRIBUNE
#: PRINCIPALE at 0.72 is already 92.6 % of every chair in it that opens.
#:
#: The shape of the ranking is the brief's: the main tribune on the pit
#: straight is the ticket everyone wants; a temporary scaffold stand at the far
#: end of the circuit is where a race weekend's unsold seats are.
#:
#: FOUR OF THESE SIX ARE ABOVE WHAT `compose_stand` CAN PRODUCE, and the build
#: reports it rather than swallowing it (`target_unreachable` below).  Its
#: occupancy field is
#:
#:     want = occ * (1 + 0.10*(1-r01) - 0.45*(2*|c01-0.5|)^2.4 - 0.22*r01^2.2)
#:
#: which at `occ = 0.98` averages ~0.78 of the seats offered to it: 0.995 at the
#: front centre, ~0.76 at the back, ~0.64 at the ends.  That IS the "denser at
#: the centre and front" the brief asks for, so raising the mean means
#: flattening the shape, which is the wrong trade.  The realised build is
#:
#:     TRIBUNE OUEST       1,843 / 3,071   60.0 % physical   76.7 % of open
#:     TRIBUNE T15         2,510 / 4,077   61.6 %            78.2 %   <- ceiling
#:     VIRAGE OUEST        1,414 / 2,143   66.0 %            66.0 %
#:     TRIBUNE PRINCIPALE  3,345 / 5,542   60.4 %            77.6 %   <- ceiling
#:     TRIBUNE EST         1,559 / 2,522   61.8 %            78.8 %   <- ceiling
#:     TRIBUNE TEMPORAIRE    458 /   995   46.0 %            46.0 %
#:     ------------------------------------------------------------
#:     11,129 people over 18,350 chairs, 3,311 of them folded up
#:
#: so the intended ranking is NOT realised: five of six blocks land within
#: 1.8 points of each other at ~61 % and only TRIBUNE TEMPORAIRE separates.
#: To get a gradient the LESSER stands have to come down, not the main tribune
#: go up -- 0.55 / 0.50 / 0.45 / 0.30 for VIRAGE OUEST / EST / OUEST /
#: TEMPORAIRE, leaving the two the camera reads biggest at the ceiling.  That
#: is a ~10,000-person build and it is the next pass, not this one: it costs a
#: 451 s rebuild and the frames now on the farm are of THIS artefact.
OCCUPANCY = {
    "TRIBUNE PRINCIPALE": 0.72,
    "TRIBUNE T15":        0.66,
    "VIRAGE OUEST":       0.66,
    "TRIBUNE EST":        0.62,
    "TRIBUNE OUEST":      0.60,
    "TRIBUNE TEMPORAIRE": 0.46,
}

#: What `compose_stand` is asked for before `plan_block`'s group-wise thinning
#: cuts it to the target.  It has to be comfortably ABOVE the largest ratio of
#: target to seatable seats (TRIBUNE PRINCIPALE, 0.926) or the thinning has
#: nothing to thin and the target is silently missed.
COMPOSE_OCCUPANCY = 0.98


def blocks_all():
    return [b["name"] for b in GS.load()["blocks"]]


def seat_array_world(block, reg=None, include_folded=False):
    """(row, col, x, y, z_pan) in WORLD, plus a facing per seat, for one block.

    Drop-in for `spectator_crowd.seat_array`, and deliberately the same shape:
    an ndarray of five columns and an ndarray of degrees.  The difference is
    the source and the fold filter, both named in the return.
    """
    reg = reg or GS.load()
    rows, face = [], []
    n_fold = 0
    for s in reg["seats"]:
        if reg["blocks"][s["b"]]["name"] != block:
            continue
        if s["folded"]:
            n_fold += 1
            if not include_folded:
                continue
        rows.append((s["row"], s["col"], s["wx"], s["wy"],
                     s["wz"] + reg["pan_above_tread_m"]))
        face.append(reg["facing_world_deg"])
    if not rows:
        raise RuntimeError("no seats for block %r in the register" % block)
    return np.asarray(rows, float), np.asarray(face, float), n_fold


def build_world(seed=SEED, blocks=None, lod=None, lib_limit=None,
                occupancy=None, verbose=True):
    """The whole crowd. -> report dict."""
    if bpy is None:
        raise RuntimeError("needs Blender")
    t0 = time.time()
    reg = GS.load()
    blocks = list(blocks or blocks_all())
    occupancy = dict(OCCUPANCY, **(occupancy or {}))
    focus_frames = json.load(open(FOCUS_FRAMES))

    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    root = K.coll(COLL)
    K.purge(PFX, COLL)
    root = K.coll(COLL)
    lib = K.coll(LIB_COLL, root)
    mats = HK.figure_materials(PFX)

    # ---- the library, ONCE, hidden, for every block ----------------------- #
    objs = SC.build_library(seed, lod=lod, coll=lib, mats=mats,
                            limit=lib_limit, yard=None)
    vis = [o.name for o in objs if not o.hide_render]
    if vis:
        raise RuntimeError(
            "%d of %d library sources are NOT hide_render (%s...). The "
            "yard=None branch is the only one that hides them and it did not "
            "run; shipping this puts %d unaccounted people in a field."
            % (len(vis), len(objs), vis[:4], len(vis)))
    if verbose:
        HK.log("library: %d sources, %d tris, all hide_render"
               % (len(objs), sum(len(o.data.polygons) for o in objs)))

    out = {"blocks": [], "library_sources": len(objs),
           "library_tris": int(sum(len(o.data.polygons) for o in objs)),
           "seed": seed, "lod": (lod.name if lod is not None else "L1"),
           "fields": []}
    plans = {}
    for name in blocks:
        seats, face, n_fold = seat_array_world(name, reg)
        binfo = [b for b in reg["blocks"] if b["name"] == name][0]
        phys = binfo["n_seats"]
        want = int(round(occupancy[name] * phys))
        if want > len(seats):
            raise RuntimeError(
                "%s: target %d people over %d physical seats, but only %d of "
                "them open (%d folded). The target is above the block's "
                "physical ceiling of %.3f."
                % (name, want, phys, len(seats), n_fold, len(seats) / phys))
        f = int(focus_frames[name])
        focus = SC.car_at(f)
        plan = SC.plan_block(seed, seats, face, focus, n_want=want,
                             occupancy=COMPOSE_OCCUPANCY)
        # NAME IT ON THE BLOCK INDEX, NOT THE LAST WORD OF THE BLOCK NAME.
        # "TRIBUNE OUEST" and "VIRAGE OUEST" both end in OUEST, so
        # `name.split()[-1].title()` collides and Blender silently suffixes the
        # second one `SPECX_Crowd_Ouest.001`. Nothing breaks -- 900 objects,
        # 900 meshes, the prefix still matches -- but a `.001` in a shipped
        # blend is the signature of an accidental duplicate, which is exactly
        # what `build_items` reports `materials_name_collided` for, and a
        # reader cannot tell which stand `Ouest.001` is.
        fld = SC.build_field(
            "%sCrowd_%02d_%s" % (PFX, binfo["i"],
                                 name.replace(" ", "").title()),
            plan, lib, root, seed, n_src=len(objs))
        mix = HK.role_mix(plan)
        rec = dict(block=name, physical_seats=phys, folded=n_fold,
                   seatable=len(seats), target=want, placed=len(plan),
                   occ_of_physical=round(len(plan) / float(phys), 4),
                   occ_of_seatable=round(len(plan) / float(len(seats)), 4),
                   # A target the composer's own occupancy field cannot reach
                   # is silently missed otherwise: `n_want` only THINS, so a
                   # target above what `compose_stand` produced does nothing
                   # at all and the block quietly lands wherever the field
                   # put it.  Named, with the shortfall, so the dial cannot
                   # look as though it worked.
                   target_unreachable=bool(len(plan) < want),
                   shortfall=max(0, want - len(plan)),
                   focus_frame=f, focus=[round(c, 2) for c in focus],
                   field=fld.name,
                   roles={k: round(v, 4) for k, v in mix.items()},
                   distinct_sources=len({int(r["src"]) for r in plan}),
                   top_source_share=round(max(
                       [sum(1 for r in plan if int(r["src"]) == s)
                        for s in {int(r["src"]) for r in plan}]
                   ) / float(len(plan)), 5))
        out["blocks"].append(rec)
        out["fields"].append(fld.name)
        plans[name] = plan
        if verbose:
            HK.log("%-20s %5d/%5d seats (%4.1f %% physical, %4.1f %% of open) "
                   "  focus f%-5d  %3d sources  top %.3f %%%s"
                   % (name, rec["placed"], phys, 100 * rec["occ_of_physical"],
                      100 * rec["occ_of_seatable"], f, rec["distinct_sources"],
                      100 * rec["top_source_share"],
                      ("   TARGET UNREACHABLE: asked %d, the occupancy field "
                       "produced %d" % (want, len(plan)))
                      if rec["target_unreachable"] else ""))

    K.assert_no_external_assets()
    out["people"] = sum(b["placed"] for b in out["blocks"])
    out["physical_seats"] = sum(b["physical_seats"] for b in out["blocks"])
    out["folded_seats"] = sum(b["folded"] for b in out["blocks"])
    out["objects"] = len(objs) + len(out["fields"])
    out["secs"] = round(time.time() - t0, 1)
    out["_plans"] = plans
    return out


# --------------------------------------------------------------------------
#  THE VARIETY MEASUREMENT, ON SCREEN, WITH ITS CONTROL
# --------------------------------------------------------------------------

def measure_twins(plans, frames, radius_heads=4.0, res=(3840, 2160),
                  sensor=36.0, path=None, seed=SEED):
    """Neighbour pairs on screen that are the SAME SOURCE MESH, and a control.

    The gate's `top_source_share` cannot answer the red line: one source at
    1/894 is 0.11 % however many copies of it sit side by side.  What a viewer
    reads is two identical people CLOSE TOGETHER, so that is what is counted —
    pairs whose screen centres are within `radius_heads` head-widths, at the
    frames where the crowd is largest.

    THE CONTROL is the same points and the same camera with `src` replaced by
    a uniform hash over the same 894 slots — i.e. exactly the variety the
    library size buys before `_separate_twins` does any work.  A measurement
    that only reports the treated arm cannot say whether the separation did
    anything.
    """
    path = path or os.path.join(_ROOT, "render", "film14_path.json")
    P = {e["f"]: e for e in json.load(open(path))["path"]}
    RES_X, RES_Y = res
    pts, src, ctl = [], [], []
    rr = HK.rng_for(seed, 4242)
    for name, plan in plans.items():
        for r in plan:
            x, y = r["pos"]
            pts.append((x, y, r["z"] + 0.45))
            src.append(int(r["src"]))
            ctl.append(int(rr.u() * 894) % 894)
    Q = np.asarray(pts, float)
    src = np.asarray(src); ctl = np.asarray(ctl)

    def qmat(q):
        w, x, y, z = q
        return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                         [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                         [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])

    rows = []
    for f in frames:
        e = P[f]
        C = np.array(e["p"]); R = qmat(e["q"]); fx = RES_X * e["lens"] / sensor
        V = Q - C
        zc = -(V @ R[:, 2])
        with np.errstate(divide="ignore", invalid="ignore"):
            u = (V @ R[:, 0]) / zc * fx + RES_X * 0.5
            v = (V @ R[:, 1]) / zc * fx + RES_Y * 0.5
        m = (zc > 0.5) & (u > 0) & (u < RES_X) & (v > 0) & (v < RES_Y)
        if m.sum() < 2:
            continue
        U = np.stack([u[m], v[m]], 1)
        s = src[m]; c = ctl[m]
        head_px = 0.222 / zc[m] * fx                 # 0.222 m head, this depth
        rad = radius_heads * head_px
        # brute force in tiles; the counts are small enough and a KD-tree with
        # a per-point radius is not worth the dependency
        n_pair = n_same = n_same_ctl = 0
        order = np.argsort(U[:, 0])
        Us = U[order]; ss = s[order]; cc = c[order]; rr_ = rad[order]
        # The sweep window uses the LARGEST radius in the frame, not each
        # point's own. `j0` only moves forward, so windowing on a small r_i
        # walks it past pairs a later large r_i still needs -- an
        # underestimate of `pairs` that happens to bias both arms identically
        # and would therefore never show up in the ratio.
        rmax = float(rr_.max())
        j0 = 0
        for i in range(len(Us)):
            r_i = rr_[i]
            while Us[j0, 0] < Us[i, 0] - rmax:
                j0 += 1
            for j in range(j0, i):
                d2 = (Us[i, 0]-Us[j, 0])**2 + (Us[i, 1]-Us[j, 1])**2
                if d2 <= r_i * r_i:
                    n_pair += 1
                    n_same += int(ss[i] == ss[j])
                    n_same_ctl += int(cc[i] == cc[j])
        rows.append(dict(frame=f, on_screen=int(m.sum()), pairs=n_pair,
                         same_source=n_same,
                         pct=round(100.0 * n_same / max(1, n_pair), 4),
                         same_source_control=n_same_ctl,
                         pct_control=round(100.0 * n_same_ctl / max(1, n_pair), 4),
                         median_head_px=round(float(np.median(head_px)), 1)))
    return rows


def _main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(prog="spectator_crowd_world")
    ap.add_argument("--out", default=os.path.join(
        _HERE, "spectator_crowd_world.blend"))
    ap.add_argument("--report", default=None)
    ap.add_argument("--blocks", default="all")
    ap.add_argument("--lod", default=None, choices=["L0", "L1", "L2", "L3"])
    ap.add_argument("--lib-limit", type=int, default=None)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--measure-twins", default="2607,1156,1098,1119")
    a = ap.parse_args(argv)

    blocks = blocks_all() if a.blocks == "all" else a.blocks.split("+")
    lod = getattr(HK, "LOD_" + a.lod) if a.lod else None
    rep = build_world(seed=a.seed, blocks=blocks, lod=lod,
                      lib_limit=a.lib_limit)
    plans = rep.pop("_plans")

    if a.measure_twins:
        frames = [int(x) for x in a.measure_twins.split(",") if x]
        rep["twins"] = measure_twins(plans, frames, seed=a.seed)
        print()
        print("ON-SCREEN TWINS -- neighbour pairs within 4 head-widths that "
              "share a source mesh")
        print(" frame  on_screen  head_px    pairs   same  pct      "
              "CONTROL same  pct")
        for r in rep["twins"]:
            print("  %5d %10d %8.1f %8d %6d  %6.3f %%   %10d  %6.3f %%"
                  % (r["frame"], r["on_screen"], r["median_head_px"],
                     r["pairs"], r["same_source"], r["pct"],
                     r["same_source_control"], r["pct_control"]))

    print()
    print("CROWD: %d people on %d physical seats (%d folded up and unusable)"
          % (rep["people"], rep["physical_seats"], rep["folded_seats"]))
    print("       %d objects: %d library sources (hidden) + %d crowd fields"
          % (rep["objects"], rep["library_sources"], len(rep["fields"])))
    print("       built in %.0f s" % rep["secs"])

    if a.out:
        bpy.ops.wm.save_as_mainfile(filepath=a.out, compress=False)
        rep["blend"] = a.out
        rep["blend_mb"] = round(os.path.getsize(a.out) / 1048576.0, 1)
        print("saved %s (%.1f MB)" % (a.out, rep["blend_mb"]))
    if a.report:
        with open(a.report, "w") as fh:
            json.dump(rep, fh, indent=1, default=str)
        print("report -> %s" % a.report)
    print(">> STAGE RESULT: CROWD_WORLD_OK")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
