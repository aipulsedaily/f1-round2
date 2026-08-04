#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
text_overlap_gate.py — R2-256.  NO TWO LEGENDS ON ONE PANEL.

WHY THIS GATE EXISTS
--------------------
A delivered 4K frame (beat 5, `2972abcb3fa1.png`, the La Passerelle fascia over
the pit straight) carried the word `CADENCE` in gold and the word
`PASSERELLE  2` in white printed on top of each other, 45 mm apart in depth and
concentric on the same 44 m fascia.  The panel garbled into `PASSERELICE`.

Every geometry gate in this project passed it, and they were all correct to:
nothing was non-manifold, nothing floated, nothing was coplanar within
`TOL_COPLANAR_M`, no material was miswired.  Two modules simply authored
lettering onto the SAME surface, each from its own frame, neither aware of the
other.  `build_architecture` owns the bridge's structure and put a label on its
truss face; `build_dressing` owns bridge fascia banners (its own .md says so,
"bridge fascia banners | the two overpasses' own geometry, read out of
build_architecture.py | 4") and hung a sponsor banner on the same face.

That is a defect class no existing gate could see, because it is not a property
of either module's output — it is a property of the PAIR.  This gate measures
the pair.

WHAT IT MEASURES
----------------
Every legend-bearing surface the shipping world builds, reduced to an oriented
panel (centre, normal, in-plane axes, in-plane rectangle, slab thickness):

  * `build_architecture.MB.text`  — one panel per extruded glyph run, carried
    into world space by the very matrix `MB.build` gave the object, so the
    circuit frame, the identity-frame forecourt bays and the Pont de la Plongee's
    own `m_pont` frame are each handled by their own matrix and not by an
    assumption.
  * `build_dressing.emit_art`     — one panel per printed board unit (the art
    layer: logotype, strapline, brand mark), in the root accumulator's frame,
    which is world.

Two panels FAIL together when all four hold:

  1. their normals are parallel within `PARALLEL_DEG` (10 deg),
  2. the gap between their slabs along the normal is <= `SEP_M` (0.35 m),
  3. their in-plane rectangles overlap by >= `OVERLAP_FRAC` (15 %) of the
     smaller one,
  4. THEY SAY DIFFERENT THINGS.

Rule 4 is the one that makes the gate usable rather than noisy.  Legends printed
on BOTH faces of a sign are deliberate and correct — `_signpost` in
`build_architecture` does it on purpose ("legend on BOTH faces, light on dark")
and the two runs are 34 mm apart, parallel, and perfectly concentric, so rules
1-3 all fire on them.  What makes the Passerelle defect a defect and the
signpost correct is that the signpost says the same word twice and the fascia
said two different words.  A PCA normal has no sign, so facing cannot separate
them; content can, and content is also exactly what the reviewer read off the
pixels.

CONTROLS.  Both run in the same invocation, so the gate can never become a
vacuous pass:

  POSITIVE  `--positive-control` reconstructs the deleted `PASSERELLE  2` run in
            world space, from the literals the deleted line used, and adds it to
            the panel set.  The gate must FAIL and must name it.  If it does not,
            the detector has stopped working and every PASS it ever printed is
            worthless.
  NEGATIVE  `--negative-control` adds two synthetic panels that are coplanar,
            0.01 m apart in depth, and say different things, but are slid 3.0 m
            apart along the panel so they do not overlap.  The gate must NOT
            flag them.  Without this, "overlap" could be measuring nothing but
            "coplanar" and would condemn every board on every straight.

RUN
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/text_overlap_gate.py -- [--positive-control] [--negative-control]
        [--json PATH]

Blender 5.2 exits 0 on an uncaught script exception, so `$?` is not evidence.
Judge on the printed `STAGE RESULT` line.
"""

import json
import math
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import bpy                                                    # noqa: E402
from mathutils import Matrix, Vector                          # noqa: E402

# --------------------------------------------------------------------------- #
#  thresholds                                                                   #
# --------------------------------------------------------------------------- #
PARALLEL_DEG = 10.0
PARALLEL_COS = math.cos(math.radians(PARALLEL_DEG))
SEP_M = 0.35            # max slab-to-slab gap along the normal
OVERLAP_FRAC = 0.15     # of the SMALLER panel's in-plane area
MIN_AREA = 1e-4         # ignore degenerate runs (m^2)

PANELS = []             # every legend surface, world frame


# --------------------------------------------------------------------------- #
#  1.  panel algebra                                                            #
# --------------------------------------------------------------------------- #
def _panel_from_points(P):
    """(centre, n, u, v, (u0,u1,v0,v1), (t0,t1)) for a thin cloud of points.

    PCA.  The smallest-variance direction of a glyph run or a printed board IS
    its normal; the other two span the panel.  The normal's SIGN is arbitrary
    and is never used - see the module docstring on why facing cannot be the
    discriminator here.
    """
    P = np.asarray(P, float).reshape(-1, 3)
    if len(P) < 3:
        return None
    c = P.mean(axis=0)
    Q = P - c
    try:
        _w, V = np.linalg.eigh(Q.T @ Q)
    except np.linalg.LinAlgError:
        return None
    n = V[:, 0] / max(np.linalg.norm(V[:, 0]), 1e-12)
    u = V[:, 2] / max(np.linalg.norm(V[:, 2]), 1e-12)
    v = np.cross(n, u)
    du, dv, dt = Q @ u, Q @ v, Q @ n
    return dict(c=c, n=n, u=u, v=v,
                rect=(float(du.min()), float(du.max()),
                      float(dv.min()), float(dv.max())),
                slab=(float(dt.min()), float(dt.max())))


def _area(rect):
    return max(0.0, rect[1] - rect[0]) * max(0.0, rect[3] - rect[2])


def _clip_area(quad, rect):
    """Sutherland-Hodgman: area of `quad` (4x2) clipped to axis-aligned `rect`."""
    u0, u1, v0, v1 = rect
    poly = [tuple(p) for p in quad]
    for axis, lim, keep_low in ((0, u0, False), (0, u1, True),
                                (1, v0, False), (1, v1, True)):
        if not poly:
            return 0.0
        out = []
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            ain = (a[axis] <= lim) if keep_low else (a[axis] >= lim)
            bin_ = (b[axis] <= lim) if keep_low else (b[axis] >= lim)
            if ain:
                out.append(a)
            if ain != bin_:
                d = b[axis] - a[axis]
                t = 0.0 if abs(d) < 1e-15 else (lim - a[axis]) / d
                out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        poly = out
    if len(poly) < 3:
        return 0.0
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return abs(s) * 0.5


def _pair_verdict(A, B):
    """None, or a dict describing how A and B share one panel."""
    pa, pb = A["p"], B["p"]
    dot = abs(float(np.dot(pa["n"], pb["n"])))
    if dot < PARALLEL_COS:
        return None
    # slab-to-slab gap along A's normal
    off = float(np.dot(pb["c"] - pa["c"], pa["n"]))
    a0, a1 = pa["slab"]
    b0, b1 = off + pb["slab"][0], off + pb["slab"][1]
    gap = max(0.0, max(a0, b0) - min(a1, b1))
    if gap > SEP_M:
        return None
    aA, aB = _area(pa["rect"]), _area(pb["rect"])
    if aA < MIN_AREA or aB < MIN_AREA:
        return None
    # B's rectangle corners, projected into A's in-plane frame
    u0, u1, v0, v1 = pb["rect"]
    quad = []
    for su, sv in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
        w = pb["c"] + pb["u"] * su + pb["v"] * sv - pa["c"]
        quad.append((float(np.dot(w, pa["u"])), float(np.dot(w, pa["v"]))))
    inter = _clip_area(quad, pa["rect"])
    frac = inter / min(aA, aB)
    if frac < OVERLAP_FRAC:
        return None
    return dict(a=A["label"], b=B["label"],
                a_src=A["src"], b_src=B["src"],
                a_col=A["col"], b_col=B["col"],
                overlap_frac=round(frac, 4),
                overlap_m2=round(inter, 4),
                normal_gap_m=round(gap, 4),
                angle_deg=round(math.degrees(math.acos(min(1.0, dot))), 3),
                world_xy=[round(float(pa["c"][0]), 3),
                          round(float(pa["c"][1]), 3),
                          round(float(pa["c"][2]), 3)])


def _register(src, label, col, pts, extra=None):
    p = _panel_from_points(pts)
    if p is None or _area(p["rect"]) < MIN_AREA:
        return
    rec = dict(src=src, label=label, col=col, p=p)
    if extra:
        rec.update(extra)
    PANELS.append(rec)


def _hexcol(c):
    try:
        return "#%02x%02x%02x" % tuple(
            int(round(255.0 * min(1.0, max(0.0, float(x) ** (1 / 2.2)))))
            for x in c[:3])
    except Exception:
        return "?"


# --------------------------------------------------------------------------- #
#  2.  instrumentation                                                          #
# --------------------------------------------------------------------------- #
def instrument_architecture(BA):
    """Record every `MB.text` run, and world it with the matrix `MB.build` used.

    The clouds are held against the MB INSTANCE, not against `id()`: `build_bridges`
    rebinds `mb` to a second accumulator halfway through, and an id() key would
    have let CPython hand the second one the first one's address.
    """
    pending = []          # [(mb, label, col, verts_local)]
    orig_text = BA.MB.text
    orig_build = BA.MB.build

    def text(self, body, mat4, size, mat, col=(1, 1, 1, 1), *a, **kw):
        n0 = len(self.v)
        orig_text(self, body, mat4, size, mat, col, *a, **kw)
        if len(self.v) > n0:
            pending.append((self, str(body), tuple(col[:3]),
                            np.array(self.v[n0:], float)))

    def build(self, coll, matrix=None, *a, **kw):
        ob = orig_build(self, coll, matrix=matrix, *a, **kw)
        M = np.array(ob.matrix_world if ob is not None
                     else (BA.M_C2W if matrix is None else matrix)).reshape(4, 4)
        keep = []
        for rec in pending:
            if rec[0] is not self:
                keep.append(rec)
                continue
            V = rec[3]
            W = V @ M[:3, :3].T + M[:3, 3][None, :]
            _register("arch", rec[1], _hexcol(rec[2]), W,
                      dict(obj=(ob.name if ob is not None else self.name)))
        pending[:] = keep
        return ob

    BA.MB.text = text
    BA.MB.build = build
    return lambda: len(pending)


def instrument_dressing(BD):
    """Record every printed board's ART layer, in the root accumulator's frame.

    `Local.add` walks the transform up to the root before storing, and the root
    is emitted recentred (a translation absorbed by the object's location), so
    the stored vertices ARE world.
    """
    art_labels = {}
    orig_art_text = BD.Art.text
    orig_emit_art = BD.emit_art

    def art_text(self, body, *a, **kw):
        w = orig_art_text(self, body, *a, **kw)
        art_labels.setdefault(id(self), []).append(str(body))
        return w

    def emit_art(mb, art, surf, aux, *a, **kw):
        root = mb
        while isinstance(root, BD.Local):
            root = root.parent
        n0 = len(root._V)
        orig_emit_art(mb, art, surf, aux, *a, **kw)
        if len(root._V) <= n0:
            return
        P = np.concatenate(root._V[n0:], axis=0)
        labels = art_labels.pop(id(art), [])
        label = " / ".join(labels) if labels else "(art)"
        col = "?"
        for (V, F, c, _l) in art.items:
            if len(V):
                col = _hexcol(c)
        _register("dress", label, col, P, dict(obj=root.name))

    BD.Art.text = art_text
    BD.emit_art = emit_art


# --------------------------------------------------------------------------- #
#  3.  the controls                                                             #
# --------------------------------------------------------------------------- #
def positive_control(BA):
    """Rebuild the deleted `PASSERELLE  2` run, from its own literals.

    This is the R2-256 defect, reconstructed.  `build_bridges` used to end with

        mb.text("PASSERELLE  2", T(X - D / 2 - 0.1, 2.0, soffit + dep - 0.9)
                @ Rz(-90) @ Rx(90), 0.85, "A_Sign", srgb('#e8ebee'), extrude=0.02)

    with X = -450.0, D = 4.0, soffit = 7.50, dep = 3.05, and the accumulator built
    with `matrix=None`, i.e. M_C2W.  Nothing here is a guess.
    """
    X, D, soffit, dep = -450.0, 4.0, 7.50, 3.05
    m = (BA.T(X - D / 2 - 0.1, 2.0, soffit + dep - 0.9)
         @ BA.Rz(-90) @ BA.Rx(90))
    mb = BA.MB("_R2256_positive_control")
    # BA.MB.text is the instrumented one; call the raw curve path instead so the
    # control is registered explicitly and cannot be lost with the accumulator.
    cu = bpy.data.curves.new("_pc", 'FONT')
    cu.body = "PASSERELLE  2"
    cu.size = 0.85
    cu.extrude = 0.02
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.resolution_u = 3
    ob = bpy.data.objects.new("_pc", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    V = np.array([tuple(m @ v.co) for v in me.vertices], float)
    ev.to_mesh_clear()
    bpy.context.scene.collection.objects.unlink(ob)
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    M = np.array(BA.M_C2W).reshape(4, 4)
    W = V @ M[:3, :3].T + M[:3, 3][None, :]
    _register("CONTROL+", "PASSERELLE  2", "#e8ebee", W,
              dict(obj="_R2256_positive_control", control=True))
    del mb
    return len(W)


def negative_control():
    """Coplanar, 10 mm apart, different words - but slid 3.0 m apart.

    If this fires, the gate is measuring coplanarity and not overlap, and would
    condemn every pair of adjacent boards on every straight in the circuit.
    """
    u = np.array([1.0, 0.0, 0.0])
    v = np.array([0.0, 0.0, 1.0])
    n = np.array([0.0, 1.0, 0.0])
    base = np.array([2000.0, 2000.0, 30.0])   # far from any real geometry
    for k, (label, off) in enumerate((("NEGCTL ALPHA", 0.0),
                                      ("NEGCTL BETA", 3.0))):
        pts = []
        for su in np.linspace(-0.6, 0.6, 9):
            for sv in np.linspace(-0.2, 0.2, 5):
                for sn in (-0.005, 0.005):
                    pts.append(base + u * (su + off) + v * sv +
                               n * (sn + k * 0.010))
        _register("CONTROL-", label, "#808080", np.array(pts),
                  dict(obj="_R2256_negative_control", control=True))


# --------------------------------------------------------------------------- #
#  4.  main                                                                     #
# --------------------------------------------------------------------------- #
def run(want_pos, want_neg, json_path):
    t_all = time.time()
    import build_architecture as BA
    left = instrument_architecture(BA)
    t0 = time.time()
    BA.build(verify=False)
    t_arch = time.time() - t0
    n_arch = sum(1 for p in PANELS if p["src"] == "arch")
    print("[TOG] architecture built in %5.1f s -> %4d legend panels "
          "(%d unbuilt accumulators)" % (t_arch, n_arch, left()))

    import build_dressing as BD
    instrument_dressing(BD)
    t0 = time.time()
    BD.build()
    t_dress = time.time() - t0
    n_dress = sum(1 for p in PANELS if p["src"] == "dress")
    print("[TOG] dressing     built in %5.1f s -> %4d printed board panels"
          % (t_dress, n_dress))

    if want_pos:
        nv = positive_control(BA)
        print("[TOG] POSITIVE control injected: PASSERELLE  2, %d verts" % nv)
    if want_neg:
        negative_control()
        print("[TOG] NEGATIVE control injected: 2 coplanar non-overlapping panels")

    # ---- pair sweep, AABB-pruned ------------------------------------------
    print("[TOG] sweeping %d panels ..." % len(PANELS))
    lo = np.array([p["p"]["c"] - (abs(p["p"]["rect"][1]) + abs(p["p"]["rect"][0])
                                  + abs(p["p"]["rect"][3]) + abs(p["p"]["rect"][2])
                                  + SEP_M) for p in PANELS])
    hi = np.array([p["p"]["c"] + (abs(p["p"]["rect"][1]) + abs(p["p"]["rect"][0])
                                  + abs(p["p"]["rect"][3]) + abs(p["p"]["rect"][2])
                                  + SEP_M) for p in PANELS])
    findings = []
    n = len(PANELS)
    order = np.argsort(lo[:, 0])
    for ii in range(n):
        i = int(order[ii])
        for jj in range(ii + 1, n):
            j = int(order[jj])
            if lo[j, 0] > hi[i, 0]:
                break
            if (lo[j, 1] > hi[i, 1] or hi[j, 1] < lo[i, 1] or
                    lo[j, 2] > hi[i, 2] or hi[j, 2] < lo[i, 2]):
                continue
            A, B = PANELS[i], PANELS[j]
            if A["label"] == B["label"]:
                continue          # rule 4: the same legend twice is a sign, not a defect
            f = _pair_verdict(A, B)
            if f:
                f["a_obj"] = A.get("obj", "?")
                f["b_obj"] = B.get("obj", "?")
                findings.append(f)

    neg_hits = [f for f in findings if "NEGCTL" in f["a"] or "NEGCTL" in f["b"]]
    # keyed on the SOURCE tag, not the string: while the defect is still in the
    # tree the real finding says "PASSERELLE  2" too, and matching on the word
    # would file the live defect as its own control and let the gate pass.
    pos_hits = [f for f in findings
                if "CONTROL+" in (f["a_src"], f["b_src"])]
    real = [f for f in findings if f not in neg_hits and f not in pos_hits]

    print("")
    for f in findings:
        tag = ("NEG-CONTROL" if f in neg_hits else
               "POS-CONTROL" if f in pos_hits else "DEFECT")
        print("  [%-11s] %-22s (%s, %s) OVER %-22s (%s, %s)  "
              "%5.1f%% of the smaller, gap %.3f m, %.2f deg, at %s"
              % (tag, f["a"][:22], f["a_src"], f["a_col"],
                 f["b"][:22], f["b_src"], f["b_col"],
                 100.0 * f["overlap_frac"], f["normal_gap_m"],
                 f["angle_deg"], f["world_xy"]))
    print("")

    ok_neg = (not want_neg) or (len(neg_hits) == 0)
    ok_pos = (not want_pos) or (len(pos_hits) > 0)
    ok_real = len(real) == 0
    print("[TOG] panels: arch %d, dressing %d, total %d" % (n_arch, n_dress, n))
    print("[TOG] control NEGATIVE : %s (%d hits, want 0)"
          % ("PASS" if ok_neg else "FAIL", len(neg_hits)))
    print("[TOG] control POSITIVE : %s (%d hits, want >=1)"
          % ("PASS" if ok_pos else "FAIL", len(pos_hits)))
    print("[TOG] real findings    : %d" % len(real))

    out = dict(panels_arch=n_arch, panels_dress=n_dress, panels_total=n,
               parallel_deg=PARALLEL_DEG, sep_m=SEP_M,
               overlap_frac=OVERLAP_FRAC,
               control_negative_hits=len(neg_hits),
               control_positive_hits=len(pos_hits),
               findings=real, all_findings=findings,
               arch_build_s=round(t_arch, 1), dress_build_s=round(t_dress, 1),
               total_s=round(time.time() - t_all, 1))
    if json_path:
        with open(json_path, "w") as fh:
            json.dump(out, fh, indent=1)
        print("[TOG] wrote", json_path)

    good = ok_neg and ok_pos and ok_real
    print("STAGE RESULT: text_overlap_gate %s  "
          "(%d panels, %d real findings, +ctl %s, -ctl %s)"
          % ("PASS" if good else "FAIL", n, len(real),
             "PASS" if ok_pos else "FAIL", "PASS" if ok_neg else "FAIL"))
    return good


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    jp = argv[argv.index("--json") + 1] if "--json" in argv else None
    try:
        good = run("--positive-control" in argv, "--negative-control" in argv, jp)
    except Exception:
        import traceback
        traceback.print_exc()
        print("STAGE RESULT: text_overlap_gate FAIL (uncaught exception)")
        sys.exit(1)
    sys.exit(0 if good else 1)
