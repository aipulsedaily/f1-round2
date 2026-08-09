"""R2-3721 -- DOES THE REPAIRED VARIETY GATE SEE 40 TREES SPAMMED FROM ONE MESH?

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -noaudio \
        -P tools/r2_3721_variety_gate_control.py -- --out work/r23721/gate_control.json

WHY THIS EXISTS
===============
`tools/instance_variety.py` polices "no repeated assets -- one tree spammed 100
times is the named failure", and until R2-3721 it counted ZERO trees: it walked
`depsgraph.object_instances` with `if not inst.is_instance: continue`, and
`build_terrain.instance_plants()` places every tree in the world as a LINKED
DUPLICATE OBJECT, which has `is_instance == False`.
`tools/r2_3421_instance_variety_control.py` built 40 trees from one mesh and
watched the gate report nothing.

This is the successor control for the repaired gate, and it is stricter in
three ways that matter:

  * IT DRIVES THE REAL FILE, NOT A COPY OF ITS LOGIC.  R2-3421's control
    reimplemented the gate's counting loop inline, so it could only ever have
    tested the reimplementation.  Arm B here imports `instance_variety.census`
    and arms C/D/E/F run `tools/instance_variety.py` as a SUBPROCESS and read
    its exit status, so a gate that regresses cannot pass this file.

  * IT WATCHES THE OLD CODE FAIL FIRST.  Arm A is the retired walk, verbatim,
    on the same scene.  A control nobody has seen fail is not evidence, and
    this project has found over a dozen instruments that passed vacuously.

  * IT PROVES THE NEW MEASURE IS A SCREEN EVENT, NOT A CENSUS.  Arms C and D
    contain THE SAME 40 INSTANCES OF THE SAME ONE MESH -- identical `top_share`
    of 1.000, identical instance count -- and differ only in where they stand.
    If the new number does not separate them it is just `top_share` again.

THE SCENES
==========
    A/C  `grove`   40 linked-duplicate trees, ONE mesh, in an 8x5 grid that
                   fits the frame at 60 m, plus a geometry-nodes grass emitter
                   with 40 instances over TWO meshes.  Everything co-visible.
    D    `strung`  THE SAME 40 TREES ON THE SAME MESH, strung out at 150 m
                   spacing so that exactly one of them is ever in frame.
    E    `swarm`   120 co-visible trees from one mesh -- OVER the named failure
                   of 100 -- which the gate must FAIL on.
    F    `grove` with no `--path`: co-visibility is a screen event and a gate
                   with no screen must REFUSE, not pass.

WHAT WOULD FALSIFY EACH ARM
===========================
    A  the retired walk reporting 40 -- then the R2-3424 defect never existed.
    B  `census()` reporting the trees as GN instances, or not at all.
    C  the grove's tree mesh not measuring 40 co-visible sharp copies.
    D  `strung` measuring anything like 40 -- the metric would be blind to
       where things stand, which is the entire complaint against `top_share`.
    E  the gate returning 0/PASS on 120 co-visible copies of one mesh.
    F  the gate returning PASS with no camera.
"""
import argparse
import json
import math
import os
import subprocess
import sys
from collections import Counter

import bpy
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import gate_exit                                                    # noqa: E402
import instance_variety as IV                                       # noqa: E402

R2 = os.path.dirname(_HERE)
REFERENCE_BLENDER = "/opt/blender-5.2.0-linux-x64/blender"

N_TREES = 40
N_POINTS = 40
N_SWARM = 120
WALL_LEAK_MAX = 2
TREE_H = 3.0
CAM_Y = -60.0
CAM_Z = 3.0
LENS = 50.0

RESULTS = []


def check(label, ok, detail=""):
    RESULTS.append({"check": label, "ok": bool(ok), "detail": detail})
    print("  %-4s %s%s" % ("ok" if ok else "FAIL", label,
                           ("   [%s]" % detail) if detail else ""))
    return bool(ok)


# ---------------------------------------------------------------------------
# scene construction
# ---------------------------------------------------------------------------
def _tree_mesh():
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.6, depth=TREE_H)
    t = bpy.context.object
    t.name = "VEG_tree_oak0_000000"
    t.data.name = "VEG_tree_oak_L0_00"
    t.location = (0.0, 0.0, TREE_H / 2)
    return t


def _grass(sc, y0):
    """One emitter, N_POINTS GN instances over a TWO-mesh collection.

    This is how `build_terrain.gn_kind()` places ground cover, and it is the
    arm the gate could always see. It is here so that a gate which "fixed" the
    tree blindness by breaking the instance walk cannot pass.
    """
    lib = bpy.data.collections.new("VEG_grass_lib")
    for j in range(2):
        bpy.ops.mesh.primitive_cube_add(size=0.4, location=(0, 0, -50 - j))
        c = bpy.context.object
        c.name = c.data.name = "VEG_grass_fescue_H%02d_u" % j
        sc.collection.objects.unlink(c)
        lib.objects.link(c)

    me = bpy.data.meshes.new("VEG_grass_fescue_H")
    me.from_pydata([((i % 8) - 3.5, y0 + (i // 8) * 0.6, 0.2)
                    for i in range(N_POINTS)], [], [])
    me.update()
    at = me.attributes.new("inst_idx", "INT", "POINT")
    at.data.foreach_set("value", [i % 2 for i in range(N_POINTS)])
    emit = bpy.data.objects.new("VEG_grass_fescue_H", me)
    sc.collection.objects.link(emit)

    ng = bpy.data.node_groups.new("gn", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    N = ng.nodes
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    iop = N.new("GeometryNodeInstanceOnPoints")
    ci = N.new("GeometryNodeCollectionInfo")
    ci.inputs[0].default_value = lib
    ci.inputs[1].default_value = True
    ci.inputs[2].default_value = True
    na = N.new("GeometryNodeInputNamedAttribute")
    na.data_type = "INT"
    na.inputs[0].default_value = "inst_idx"
    L = ng.links
    L.new(gi.outputs[0], iop.inputs["Points"])
    L.new(ci.outputs[0], iop.inputs["Instance"])
    L.new(na.outputs[0], iop.inputs["Instance Index"])
    iop.inputs["Pick Instance"].default_value = True
    L.new(iop.outputs[0], go.inputs[0])
    emit.modifiers.new("gn", "NODES").node_group = ng


def build(layout):
    """`grove` | `strung` | `swarm` -- the same one mesh, placed differently."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    tree = _tree_mesh()

    if layout == "grove":
        P = [((i % 8 - 3.5) * 6.0, (i // 8) * 6.0, 0.0) for i in range(N_TREES)]
    elif layout == "strung":
        # THE SAME 40 INSTANCES OF THE SAME MESH. Only the geography differs.
        P = [((i - 20) * 150.0, 0.0, 0.0) for i in range(N_TREES)]
    elif layout == "swarm":
        P = [((i % 12 - 5.5) * 3.5, (i // 12) * 3.0, 0.0) for i in range(N_SWARM)]
    else:
        raise SystemExit("REFUSING: unknown layout %r" % layout)

    tree.location = (P[0][0], P[0][1], TREE_H / 2)
    for i, p in enumerate(P[1:], 1):
        ob = bpy.data.objects.new("VEG_tree_oak0_%06d" % i, tree.data)
        ob.location = (p[0], p[1], TREE_H / 2)
        sc.collection.objects.link(ob)

    if layout != "swarm":
        _grass(sc, y0=CAM_Y + 12.0)
    bpy.context.view_layer.update()
    return len(P)


def write_path(path_json, nframes=4):
    """A static camera at 50 mm, 60 m back, looking down world +Y.

    Blender's camera looks along its local -Z with +Y up, so a +90 deg rotation
    about X aims it along +Y: quaternion (w,x,y,z) = (cos45, sin45, 0, 0).
    STATIC on purpose -- shutter smear is then exactly zero, so "sharp" is not
    doing any silent work in the arms that must fire.
    """
    q = [math.cos(math.pi / 4), math.sin(math.pi / 4), 0.0, 0.0]
    d = {"frames": nframes,
         "path": [{"f": f + 1, "p": [0.0, CAM_Y, CAM_Z], "q": q, "lens": LENS}
                  for f in range(nframes)]}
    os.makedirs(os.path.dirname(path_json) or ".", exist_ok=True)
    json.dump(d, open(path_json, "w"))
    return path_json


# ---------------------------------------------------------------------------
# Arm A -- THE RETIRED WALK, VERBATIM. It must fail.
# ---------------------------------------------------------------------------
def retired_walk():
    """`instance_variety.py` as it stood until R2-3721, both ways.

    Kept as source rather than as a claim about source: the counting loop was

        for inst in deps.object_instances:
            if not inst.is_instance:
                continue

    and the only question this arm answers is what that `continue` throws away.
    """
    deps = bpy.context.evaluated_depsgraph_get()
    gated, ungated = Counter(), Counter()
    n_is = n_tot = 0
    for inst in deps.object_instances:
        ob = inst.object
        if ob is None or ob.type != "MESH":
            continue
        n_tot += 1
        key = ob.data.name if ob.data else ob.name
        ungated[key] += 1
        if inst.is_instance:
            n_is += 1
            gated[key] += 1
    return gated, ungated, n_is, n_tot


# ---------------------------------------------------------------------------
def build_shell(blend_out, shell_out, with_wall):
    """Sample the current scene's shell, optionally with a wall in the way.

    The wall is TWO TRIANGLES. That is deliberate: the first version of
    `shell_points()` voxelised VERTICES, which records a 60 m x 12 m panel as
    four corner points and no wall at all -- an occlusion pass that subtracts
    nothing while appearing to work. If arm H passes, the face sampler is
    sampling faces.
    """
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=400.0, location=(0, 200, 0))
    g = bpy.context.object
    g.name = g.data.name = "TER_Ground_ctl"
    if with_wall:
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, -30.0, 6.0))
        w = bpy.context.object
        w.name = w.data.name = "BR_Wall_ctl"
        w.rotation_euler = (math.pi / 2, 0.0, 0.0)
        w.scale = (60.0, 12.0, 1.0)
        print("  built a %d-triangle wall at y=-30, between the camera "
              "(y=%.0f) and the trees (y=0..24)" % (len(w.data.polygons) * 2,
                                                    CAM_Y))
    bpy.context.view_layer.update()
    P, meta = IV.shell_points()
    np.savez_compressed(shell_out, P=P, meta=json.dumps(meta))
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    return P, meta


def run_gate(blend, out_json, path_json, extra=()):
    """The REAL gate, as a subprocess, judged on BOTH status and text."""
    # A STALE REPORT IS A PASS NOBODY EARNED. If the gate crashes, the json
    # from the previous arm is still on disk and every assertion below reads
    # it happily -- which is exactly what happened at R2-3743, where a crashing
    # run was graded on the previous arm's numbers.
    if os.path.exists(out_json):
        os.remove(out_json)
    cmd = [REFERENCE_BLENDER, "-b", blend, "--factory-startup", "-noaudio",
           "-P", os.path.join(_HERE, "instance_variety.py"), "--",
           "--out", out_json]
    if path_json:
        cmd += ["--path", path_json]
    cmd += list(extra)
    r = subprocess.run(cmd, capture_output=True, text=True)
    txt = (r.stdout or "") + (r.stderr or "")
    said = [l for l in txt.splitlines() if "STAGE RESULT" in l]
    # THE WORST verdict in the log, never the last one -- R2-1084.
    scan_rc, _found = gate_exit.scan(txt)
    rep = json.load(open(out_json)) if os.path.exists(out_json) else {}
    return dict(rc=r.returncode, scan_rc=scan_rc,
                verdicts=[s.strip() for s in said], report=rep, log=txt)


def mesh_row(rep, mesh, px="px64"):
    for r in rep.get("sources", []):
        if r["source_mesh"] == mesh:
            return r, r[px]
    return None, None


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", default=None)
    a = ap.parse_args(argv)
    work = a.work or os.path.dirname(os.path.abspath(a.out)) or "."
    os.makedirs(work, exist_ok=True)

    print("reference blender : %s" % REFERENCE_BLENDER)
    print("running blender   : %s\n" % bpy.app.binary_path)
    check("this control is running under the REFERENCE blender",
          os.path.realpath(bpy.app.binary_path)
          == os.path.realpath(REFERENCE_BLENDER),
          bpy.app.binary_path)

    path_json = write_path(os.path.join(work, "ctl_path.json"))

    # ================= ARM A -- WATCH THE RETIRED WALK FAIL ================
    print("\nARM A -- the RETIRED walk (`if not inst.is_instance: continue`) "
          "on 40 trees from ONE mesh.")
    build("grove")
    gated, ungated, n_is, n_tot = retired_walk()
    tm = "VEG_tree_oak_L0_00"
    print("  depsgraph mesh entries: %d total, %d with is_instance == True"
          % (n_tot, n_is))
    print("  %-28s%14s%14s" % ("source mesh", "gate's walk", "unfiltered"))
    for k in sorted(set(gated) | set(ungated)):
        print("  %-28s%14d%14d" % (k, gated.get(k, 0), ungated.get(k, 0)))
    a_gated, a_ungated = gated.get(tm, 0), ungated.get(tm, 0)
    check("RETIRED walk sees 0 of the %d spammed trees (the R2-3424 defect, "
          "reproduced)" % N_TREES, a_gated == 0, "saw %d" % a_gated)
    check("the trees ARE in the depsgraph -- unfiltered walk sees all %d"
          % N_TREES, a_ungated == N_TREES, "saw %d" % a_ungated)
    if gated:
        top = gated.most_common(1)[0]
        check("and the retired walk printed a SPAM verdict about the GRASS "
              "while the 100 %-spammed tree was invisible to it",
              top[1] / sum(gated.values()) > 0.40,
              "top %s at %.0f %%" % (top[0],
                                     100 * top[1] / sum(gated.values())))

    # ================= ARM B -- THE REPAIRED CENSUS ========================
    print("\nARM B -- `instance_variety.census()`, the REAL function, same scene.")
    c = IV.census()
    names = list(c["names"])
    idx = names.index(tm) if tm in names else -1
    n_o = int(c["n_obj"][idx]) if idx >= 0 else 0
    n_i = int(c["n_ins"][idx]) if idx >= 0 else 0
    check("the repaired census sees all %d trees" % N_TREES,
          n_o + n_i == N_TREES, "objects=%d gn_instances=%d" % (n_o, n_i))
    check("and files them as REAL OBJECTS, which is what a linked duplicate is",
          n_o == N_TREES and n_i == 0, "objects=%d gn_instances=%d" % (n_o, n_i))
    gi = [i for i, n in enumerate(names) if n.startswith("VEG_grass_fescue_H")
          and n.endswith("_u")]
    check("the GN arm is not broken by the fix -- %d grass instances over 2 "
          "meshes still counted" % N_POINTS,
          sum(int(c["n_ins"][i]) for i in gi) == N_POINTS,
          "%d over %d meshes" % (sum(int(c["n_ins"][i]) for i in gi), len(gi)))
    hz = float(c["H"][np.nonzero(np.asarray(c["MID"]) == idx)[0][0]]) if idx >= 0 else 0.0
    check("per-instance height is measured, not assumed (%.2f m cone)" % TREE_H,
          abs(hz - TREE_H) < 0.05, "%.3f m" % hz)

    # ================= ARM C -- THE GROVE ==================================
    print("\nARM C -- the whole gate on `grove`: 40 co-visible trees, ONE mesh.")
    grove_blend = os.path.join(work, "ctl_iv_grove.blend")
    bpy.ops.wm.save_as_mainfile(filepath=grove_blend)
    C = run_gate(grove_blend, os.path.join(work, "ctl_iv_grove.json"), path_json)
    row_c, px_c = mesh_row(C["report"], tm)
    print("  verdicts: %s" % C["verdicts"])
    check("gate returns PASS(0) on a grove of 40 -- under the named failure "
          "of %d" % int(IV.SPAM_CVR),
          C["rc"] == gate_exit.PASS and C["scan_rc"] == gate_exit.PASS,
          "rc=%d scan=%d" % (C["rc"], C["scan_rc"]))
    check("and it MEASURED the trees: %s reports %d co-visible sharp copies"
          % (tm, (px_c or {}).get("peak_covisible_sharp", -1)),
          bool(px_c) and px_c["peak_covisible_sharp"] == N_TREES,
          json.dumps(px_c))
    check("the trees are the WORST source mesh in the scene, i.e. the gate is "
          "now graded on them rather than on the grass",
          (C["report"].get("worst_source_mesh") or {}).get("source_mesh") == tm,
          str((C["report"].get("worst_source_mesh") or {}).get("source_mesh")))

    # ================= ARM D -- THE SAME 40, STRUNG OUT ====================
    print("\nARM D -- the SAME 40 instances of the SAME mesh, strung out at "
          "150 m. `top_share` cannot tell C and D apart; this must.")
    build("strung")
    strung_blend = os.path.join(work, "ctl_iv_strung.blend")
    bpy.ops.wm.save_as_mainfile(filepath=strung_blend)
    D = run_gate(strung_blend, os.path.join(work, "ctl_iv_strung.json"),
                 path_json)
    row_d, px_d = mesh_row(D["report"], tm)
    fam_c = {f["family"]: f for f in C["report"].get("families", [])}
    fam_d = {f["family"]: f for f in D["report"].get("families", [])}
    ts_c = (fam_c.get("VEG") or {}).get("top_share_retired_R2_3441")
    ts_d = (fam_d.get("VEG") or {}).get("top_share_retired_R2_3441")
    check("C and D have the SAME instance count of the SAME one mesh",
          (row_c or {}).get("instances") == (row_d or {}).get("instances")
          == N_TREES,
          "%s vs %s" % ((row_c or {}).get("instances"),
                        (row_d or {}).get("instances")))
    check("the RETIRED measure cannot separate them (top_share identical)",
          ts_c is not None and ts_c == ts_d, "%s vs %s" % (ts_c, ts_d))
    check("the NEW measure separates them: grove %s vs strung %s co-visible "
          "sharp" % ((px_c or {}).get("peak_covisible_sharp"),
                     (px_d or {}).get("peak_covisible_sharp")),
          bool(px_d) and px_d["peak_covisible_sharp"] <= 3
          and px_c["peak_covisible_sharp"] >= 10 * max(
              1, px_d["peak_covisible_sharp"]),
          json.dumps(px_d))

    # ================= ARM E -- OVER THE LINE, THE GATE MUST FIRE ==========
    print("\nARM E -- `swarm`: %d co-visible copies of one mesh, over the "
          "named failure of %d." % (N_SWARM, int(IV.SPAM_CVR)))
    build("swarm")
    swarm_blend = os.path.join(work, "ctl_iv_swarm.blend")
    bpy.ops.wm.save_as_mainfile(filepath=swarm_blend)
    E = run_gate(swarm_blend, os.path.join(work, "ctl_iv_swarm.json"), path_json)
    row_e, px_e = mesh_row(E["report"], tm)
    print("  verdicts: %s" % E["verdicts"])
    check("gate returns FAIL(1) and says SPAM",
          E["rc"] == gate_exit.FAIL and E["scan_rc"] == gate_exit.FAIL
          and any("SPAM" in v for v in E["verdicts"]),
          "rc=%d scan=%d %s" % (E["rc"], E["scan_rc"], E["verdicts"]))
    check("and it names the tree mesh, at >= %d co-visible sharp copies"
          % int(IV.SPAM_CVR),
          tm in E["report"].get("over_spam_cvr_unexempt", [])
          and bool(px_e) and px_e["peak_covisible_sharp"] >= IV.SPAM_CVR,
          json.dumps(px_e))

    # ================= ARM F -- NO CAMERA, NO VERDICT ======================
    print("\nARM F -- the grove again with NO --path. A screen event with no "
          "screen must REFUSE.")
    F = run_gate(grove_blend, os.path.join(work, "ctl_iv_nocam.json"), None)
    print("  verdicts: %s" % F["verdicts"])
    check("gate returns VACUOUS(3), not PASS, when it has no camera",
          F["rc"] == gate_exit.VACUOUS and F["scan_rc"] == gate_exit.VACUOUS,
          "rc=%d scan=%d %s" % (F["rc"], F["scan_rc"], F["verdicts"]))

    # ============ ARM G -- OCCLUSION ON, AND THE TREES MUST SURVIVE ========
    print("\nARM G -- the grove again, occlusion SUBTRACTED, nothing in the "
          "way. Subtracting occlusion can only LOWER counts, so the case this "
          "gate exists for must be shown to survive it.")
    build("grove")
    g_blend = os.path.join(work, "ctl_iv_grove_open.blend")
    g_shell = os.path.join(work, "ctl_shell_open.npz")
    SP, smeta = build_shell(g_blend, g_shell, with_wall=False)
    G = run_gate(g_blend, os.path.join(work, "ctl_iv_grove_open.json"),
                 path_json, ["--shell", g_shell])
    row_g, px_g = mesh_row(G["report"], tm)
    check("the shell sampled %d points from %d objects with no wall in it"
          % (len(SP), smeta["shell_objects"]), len(SP) > 100, json.dumps(smeta))
    check("with occlusion ON the gate STILL sees all %d trees" % N_TREES,
          bool(px_g) and px_g["peak_covisible_sharp"] == N_TREES,
          json.dumps(px_g))
    check("and the unsubtracted count is the same %d, i.e. nothing was hidden"
          % N_TREES,
          bool(px_g)
          and px_g["peak_covisible_sharp_no_occlusion"] == N_TREES,
          json.dumps(px_g))
    check("gate still returns PASS(0)", G["rc"] == gate_exit.PASS,
          "rc=%d" % G["rc"])

    # ============ ARM H -- A WALL, AND THEY MUST FALL BECAUSE OF IT ========
    print("\nARM H -- the SAME grove, the SAME camera, occlusion ON, and a "
          "two-triangle wall between the lens and the trees.")
    build("grove")
    h_blend = os.path.join(work, "ctl_iv_grove_walled.blend")
    h_shell = os.path.join(work, "ctl_shell_walled.npz")
    SPw, wmeta = build_shell(h_blend, h_shell, with_wall=True)
    H = run_gate(h_blend, os.path.join(work, "ctl_iv_grove_walled.json"),
                 path_json, ["--shell", h_shell])
    row_h, px_h = mesh_row(H["report"], tm)
    check("the walled shell has more points than the open one (the wall was "
          "actually sampled, not recorded as four corners)",
          len(SPw) > len(SP) + 100, "%d vs %d" % (len(SPw), len(SP)))
    # NOT `== 0`. The shell is a STOCHASTIC surface sample voxel-deduped at
    # 1.5 m, so a cell or two of a 60 m wall can come up empty and let a tree
    # through. That residual is the sampler's coverage, not a hole in the
    # occlusion test, and it is bounded and stated rather than tuned away: at
    # SAMPLE_OVERSAMPLE = 6 the expected coverage is 99.75 %. Anything above a
    # couple of trees means the test itself is leaking.
    n_h = (px_h or {}).get("peak_covisible_sharp", -1)
    check("behind the wall the gate sees %s of the %d trees -- at most %d may "
          "survive the sampler's coverage" % (n_h, N_TREES, WALL_LEAK_MAX),
          bool(px_h) and 0 <= n_h <= WALL_LEAK_MAX, json.dumps(px_h))
    check("and that is at least a %dx reduction, i.e. the wall did the work"
          % 10, bool(px_h) and n_h * 10 <= N_TREES, "%s of %d" % (n_h, N_TREES))
    check("and it fell BECAUSE OF THE WALL, not because the measurement "
          "stopped working: the unsubtracted count on the same run is still "
          "%d" % N_TREES,
          bool(px_h)
          and px_h["peak_covisible_sharp_no_occlusion"] == N_TREES,
          json.dumps(px_h))

    # ---- summary ---------------------------------------------------------
    bad = [r for r in RESULTS if not r["ok"]]
    res = {"n_trees_built": N_TREES, "n_swarm": N_SWARM, "tree_mesh": tm,
           "retired_walk_saw": a_gated, "unfiltered_walk_saw": a_ungated,
           "census_saw_objects": n_o, "census_saw_gn_instances": n_i,
           "grove_covisible_sharp_px64": (px_c or {}).get(
               "peak_covisible_sharp"),
           "strung_covisible_sharp_px64": (px_d or {}).get(
               "peak_covisible_sharp"),
           "swarm_covisible_sharp_px64": (px_e or {}).get(
               "peak_covisible_sharp"),
           "top_share_grove": ts_c, "top_share_strung": ts_d,
           "occ_open_covisible_sharp": (px_g or {}).get("peak_covisible_sharp"),
           "occ_walled_covisible_sharp": (px_h or {}).get(
               "peak_covisible_sharp"),
           "occ_walled_covisible_sharp_no_occlusion": (px_h or {}).get(
               "peak_covisible_sharp_no_occlusion"),
           "spam_cvr": IV.SPAM_CVR, "recog_px": IV.RECOG_PX,
           "checks": RESULTS, "failed": len(bad)}
    json.dump(res, open(a.out, "w"), indent=1)
    print("\nwrote %s" % a.out)
    print("\n%d/%d checks passed" % (len(RESULTS) - len(bad), len(RESULTS)))

    if bad:
        for r in bad:
            print("  FAILED: %s  [%s]" % (r["check"], r["detail"]))
        return gate_exit.verdict("IV_GATE_CONTROL_FAIL",
                                 "  (%d of %d checks)" % (len(bad),
                                                          len(RESULTS)))
    print(">> The repaired gate saw all %d trees spammed from one mesh, graded "
          "the scene on them, separated 40-co-visible from 40-strung-out that "
          "`top_share` calls identical, fired at %d, and refused without a "
          "camera." % (N_TREES, int(IV.SPAM_CVR)))
    return gate_exit.verdict("IV_GATE_CONTROL_OK")


if __name__ == "__main__":
    gate_exit.guard(main, tool="iv_gate_control")
