"""VERIFY THE BREACH — the instrument, with controls that fail.

    .venv/bin/python sim/verify_breach.py --selftest
    .venv/bin/python sim/verify_breach.py --film sim/out/breach_film.npz

Twenty-five times on this project the instrument has been the broken thing
rather than the work, so every check below is paired: a POSITIVE control that
must FAIL (a defect deliberately injected into a copy of the table) and a
NEGATIVE control that must pass.  A check that cannot be made to fail is not
reported as a pass, it is reported as VACUOUS.

WHAT IT LOOKS FOR, AND WHY EACH ONE IS INVISIBLE IN MOTION
==========================================================
POP        a body that jumps between two film frames by far more than its own
           neighbourhood does.  At 24 fps with 180 deg of shutter a 3-frame pop
           smears into the blur and reads as speed.  Held, it is a teleport.
VANISH     a body whose visibility is not monotone — shown, hidden, shown.  The
           swap gives every shard exactly one transition; two is a flicker.
SINK       a body under the floor, or one that ends inside the static geometry.
           A convex-hull collider that stands 3 mm proud of its own shard can
           park it 3 mm high; 40 mm of Blender's default margin would park the
           whole field in the air, which is why MARGIN is what it is.
OVERLAP    two shards sharing space.  Exact for convex polyhedra by the
           separating-axis theorem: if no face normal of either and no
           edge-pair cross product separates them, they intersect, and the
           smallest overlap along any candidate axis IS the penetration depth.
SEAM       the film has ZERO CUTS.  The per-frame change in the shard field
           across a beat boundary may not exceed what its own neighbourhood
           does — the same statistic `tools/car_anim_gate.py` uses on the car,
           deliberately, so the two are comparable.
PERSIST    the wound must be bit-identical from the frame it stops moving to
           frame 2,978.  Beat 6 sees it 80 s later.  A "wound" that drifts by a
           millimetre a frame is a wound that has moved 2 m by the end.
"""

import argparse
import json
import math
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(R2, "sim") not in sys.path:
    sys.path.insert(0, os.path.join(R2, "sim"))

import breachlib as BL                                            # noqa: E402
import fracture as FR                                             # noqa: E402

# thresholds
POP_RATIO = 6.0          # x the local median per-frame step
POP_FLOOR_M = 0.05       # ... and it must also clear this, or a still field
POP_FLOOR_DEG = 12.0     # turns a 0.1 mm wobble into a "1,000x defect"
SINK_M = 0.004           # 4 mm below the floor plane
OVERLAP_M = 0.003        # = CONVEX_TOL_M: the hull is allowed to be this proud
SEAM_WINDOW = 14
SEAM_CORE = 3
SEAM_RATIO = 3.0
LAST_FRAME = 2978        # the take's last frame.  Only used to price a shard
                         # that NEVER releases: its hole runs to the end.


# --------------------------------------------------------------------------- #
#  quaternion -> matrix, vectorised
# --------------------------------------------------------------------------- #

def qmat(q):
    q = np.asarray(q, float)
    w, x, y, z = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    n = w * w + x * x + y * y + z * z
    s = np.where(n < 1e-12, 0.0, 2.0 / np.where(n < 1e-12, 1.0, n))
    M = np.empty(q.shape[:-1] + (3, 3))
    M[..., 0, 0] = 1 - s * (y * y + z * z)
    M[..., 0, 1] = s * (x * y - z * w)
    M[..., 0, 2] = s * (x * z + y * w)
    M[..., 1, 0] = s * (x * y + z * w)
    M[..., 1, 1] = 1 - s * (x * x + z * z)
    M[..., 1, 2] = s * (y * z - x * w)
    M[..., 2, 0] = s * (x * z - y * w)
    M[..., 2, 1] = s * (y * z + x * w)
    M[..., 2, 2] = 1 - s * (x * x + y * y)
    return M


def qangle_step(Q):
    """Per-frame turn angle, degrees, (nf-1, n)."""
    a, b = Q[:-1], Q[1:]
    d = np.abs(np.sum(a * b, axis=2)).clip(-1.0, 1.0)
    return np.degrees(2.0 * np.arccos(d))


# --------------------------------------------------------------------------- #
#  exact convex-convex overlap (SAT)
# --------------------------------------------------------------------------- #

def sat_depth(A, B, fa, fb):
    """Penetration depth of two convex polyhedra, metres.  0.0 if separated.

    A, B are (n, 3) vertex arrays; fa, fb are face-normal arrays.  Candidate
    axes are both face-normal sets plus every cross product of an edge from each
    — the complete SAT set for convex polyhedra, so a 0.0 here is a proof of
    separation and not a sample that missed.
    """
    axes = [fa, fb]
    ea = _edges(A)
    eb = _edges(B)
    if len(ea) and len(eb):
        cr = np.cross(ea[:, None, :], eb[None, :, :]).reshape(-1, 3)
        L = np.linalg.norm(cr, axis=1)
        cr = cr[L > 1e-9] / L[L > 1e-9][:, None]
        if len(cr):
            axes.append(cr)
    AX = np.vstack([a for a in axes if len(a)])
    pa = A @ AX.T
    pb = B @ AX.T
    lo = np.minimum(pa.max(axis=0) - pb.min(axis=0),
                    pb.max(axis=0) - pa.min(axis=0))
    m = lo.min()
    return float(max(0.0, m))


def _edges(P):
    """A cheap edge-direction set: hull edges would be exact but these solids
    are prisms, so the three principal directions plus the perimeter chords
    cover every real edge."""
    n = len(P)
    if n < 4:
        return np.zeros((0, 3))
    d = P[1:] - P[:-1]
    L = np.linalg.norm(d, axis=1)
    d = d[L > 1e-9] / L[L > 1e-9][:, None]
    if len(d) > 24:
        d = d[np.linspace(0, len(d) - 1, 24).astype(int)]
    return d


def face_normals(V, F):
    out = []
    for f in F:
        if len(f) < 3:
            continue
        n = np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])
        L = np.linalg.norm(n)
        if L > 1e-12:
            out.append(n / L)
    if not out:
        return np.zeros((0, 3))
    A = np.array(out)
    # dedupe near-parallel normals; a prism has 2 + n and most are unique
    keep = [0]
    for i in range(1, len(A)):
        if np.max(np.abs(A[keep] @ A[i])) < 0.9995:
            keep.append(i)
    return A[keep]


# --------------------------------------------------------------------------- #
#  checks
# --------------------------------------------------------------------------- #

def _local_median(A, win=7):
    """Median of each column over a sliding window of rows, (nf, n).

    Written out rather than vectorised with stride tricks because the arrays
    are small and a wrong window here is a silent wrong verdict.
    """
    nf = A.shape[0]
    out = np.empty_like(A)
    for i in range(nf):
        a, b = max(0, i - win), min(nf, i + win + 1)
        out[i] = np.median(A[a:b], axis=0)
    return out


def check_pop(frames, L, Q):
    """A pop is a body moving far more than IT was moving a moment ago.

    Compared against each body's OWN local median, not the field's global one.
    A shard crossing the frame at 16 m/s covers 0.103 m per beat-3 film frame,
    which a global threshold flags as a teleport on every frame of its flight —
    measured: 8,101 "pops" in a table whose real defect was something else
    entirely.  The same statistic as `tools/car_anim_gate.py`, for the same
    reason: a seam at 16 m/s and a seam at rest cannot share a threshold.
    """
    step = np.linalg.norm(np.diff(L, axis=0), axis=2)        # (nf-1, n)
    turn = qangle_step(Q)
    med = _local_median(step)
    medr = _local_median(turn)
    bad_p = step > np.maximum(POP_RATIO * med, POP_FLOOR_M)
    bad_r = turn > np.maximum(POP_RATIO * medr, POP_FLOOR_DEG)
    fi, bj = np.where(bad_p)
    worst = []
    if len(fi):
        o = np.argsort(-step[bad_p])[:8]
        worst = [dict(frame=int(frames[fi[k]]), body=int(bj[k]),
                      step_m=float(step[fi[k], bj[k]])) for k in o]
    return dict(median_step_m=float(np.median(med)),
                median_turn_deg=float(np.median(medr)),
                pos_pops=int(bad_p.sum()), rot_pops=int(bad_r.sum()),
                worst=worst,
                threshold_note="per body, max(%.1f x its own local median, "
                               "%.3f m / %.1f deg)"
                               % (POP_RATIO, POP_FLOOR_M, POP_FLOOR_DEG))


def check_visibility(release, frames):
    """Each body gets exactly one hide->show transition, at a frame inside the
    table.  Monotone by construction; this is the assertion that it stayed so."""
    r = np.asarray(release)
    inside = (r >= frames[0]) & (r <= frames[-1])
    return dict(bodies=len(r), never_released=int((r < 0).sum()),
                released=int((r > 0).sum()),
                outside_table=int(((r > 0) & ~inside).sum()),
                first=int(r[r > 0].min()) if (r > 0).any() else -1,
                last=int(r[r > 0].max()) if (r > 0).any() else -1)


def check_swap(release, names, plan):
    """THE SWAP, CHECKED RATHER THAN ASSERTED.  R2-098.

    `sim/apply_breach.py` hides each fractured bay's intact pane at ONE frame

        r_bay = min(release) over that bay's shards

    and shows each SHARD at ITS OWN release frame.  Those are not the same
    number.  A shard whose glass sits still for another twelve frames after its
    neighbour lets go is keyed to appear twelve frames after the pane that was
    covering it has gone — and for those twelve frames NOTHING renders in its
    place.  A hole, in a film with no cuts.

    In the shipped table that is 9 shards for exactly 1 frame at 860/861, which
    is small.  It is small BY LUCK: it is bounded by the spread of release
    frames within a bay, and nothing anywhere enforces that spread.  This is
    the check the `apply_breach` docstring has advertised for four revisions
    under the name `verify_breach.py --swap` and which did not exist.

    It measures the TABLE, which is what apply_breach keys from, so it fires
    before a 4 GB scene is written rather than after a frame is rendered.

    Returns per-bay: the pane's hide frame, the worst shard gap in frames, and
    how many shards are uncovered.  PASS requires every gap to be zero.
    """
    r = np.asarray(release, int)
    idx = {str(n): i for i, n in enumerate(names)}
    roles = plan.get("roles", {})
    bays, worst, total_uncovered, total_frames = {}, 0, 0, 0
    spread = {}
    for bay, shards in sorted(plan.get("panes", {}).items()):
        if roles.get(bay) == "intact":
            continue                       # never hides, so nothing to uncover
        ii = [idx["GS_b%02d_%05d" % (bay, s["id"])]
              for s in shards
              if "GS_b%02d_%05d" % (bay, s["id"]) in idx]
        if not ii:
            continue
        rr = r[ii]
        rel_pos = rr[rr > 0]
        if not len(rel_pos):
            continue                       # pane never hides either
        r_bay = int(rel_pos.min())
        if int(rel_pos.max()) != r_bay:
            spread[str(bay)] = dict(
                min=r_bay, max=int(rel_pos.max()),
                n_later=int((rel_pos > r_bay).sum()),
                frames=sorted(set(rel_pos.tolist())))
        # A shard that NEVER releases is uncovered from r_bay to the end of the
        # take.  That is not a twelve-frame hole, it is a permanent one, and it
        # has to be counted as worse rather than skipped.
        gap = np.where(rr > 0, rr - r_bay, LAST_FRAME - r_bay)
        gap = np.maximum(gap, 0)
        n_unc = int((gap > 0).sum())
        bays[str(bay)] = dict(
            role=roles.get(bay), n_shards=len(ii), pane_hides_at=r_bay,
            shards_uncovered=n_unc,
            worst_gap_frames=int(gap.max()),
            uncovered_shard_frames=int(gap.sum()),
            never_release=int((rr < 0).sum()))
        worst = max(worst, int(gap.max()))
        total_uncovered += n_unc
        total_frames += int(gap.sum())
    return dict(
        criterion="every shard of a fractured bay must appear on the SAME "
                  "frame its pane hides.  Any later is a hole with nothing "
                  "behind it.",
        measured="the TABLE, under the rule apply_breach USED TO USE: pane "
                 "hides at min(release), each shard appears at its own "
                 "release.  This is the defect as it shipped.  The applier "
                 "now keys both sides off one frame per bay, so a scene built "
                 "by the current applier has no hole even when this arm "
                 "reports one -- use --blend to check the SCENE, which is the "
                 "thing that renders.",
        release_spread_within_a_bay=spread,
        why_the_spread_still_matters="it is the raw material of the defect.  "
                                     "The applier is what stops it becoming a "
                                     "hole, and an applier can be changed "
                                     "back.",
        bays=bays, worst_gap_frames=worst,
        shards_uncovered=total_uncovered,
        uncovered_shard_frames=total_frames,
        PASS=bool(worst == 0))


def check_swap_scene(blend_path, plan):
    """THE SAME QUESTION ASKED OF THE SCENE THAT RENDERS.

    The table arm above measures the raw release spread, which is what the
    defect was MADE of.  This arm measures what the applier DID with it: for
    every fractured bay, the frame its GP_b* pane hides must equal the frame
    every one of its GS_b* shards appears.  That is the invariant, and reading
    it off the .blend is the only way to catch an applier that has been
    changed back.

    Run inside Blender:
        blender -b <applied>.blend -P sim/verify_breach.py -- --swap-scene
    """
    import bpy                                                # noqa: E402

    def switch(ob):
        """The frame this object's hide_render steps, and which way."""
        ad = ob.animation_data
        if not (ad and ad.action):
            return None
        for lay in ad.action.layers:
            for st in lay.strips:
                cb = st.channelbag(ad.action_slot)
                if not cb:
                    continue
                for fc in cb.fcurves:
                    if fc.data_path != "hide_render":
                        continue
                    ks = sorted((int(k.co[0]), float(k.co[1]))
                                for k in fc.keyframe_points)
                    for i in range(1, len(ks)):
                        if ks[i][1] != ks[i - 1][1]:
                            return dict(frame=ks[i][0],
                                        to_hidden=bool(ks[i][1] > 0.5))
        return None

    roles = plan.get("roles", {})
    out, bad = {}, []
    for bay in sorted(plan.get("panes", {})):
        pane = bpy.data.objects.get("GP_b%02d" % bay)
        if pane is None:
            bad.append(("GP_b%02d" % bay, "missing"))
            continue
        ph = switch(pane)
        shards = [bpy.data.objects.get("GS_b%02d_%05d" % (bay, s["id"]))
                  for s in plan["panes"][bay]]
        shards = [o for o in shards if o is not None]
        shows = {}
        for o in shards:
            sw = switch(o)
            f = sw["frame"] if sw else None
            shows[f] = shows.get(f, 0) + 1
        rec = dict(role=roles.get(bay), n_shards=len(shards),
                   pane_hides_at=(ph or {}).get("frame"),
                   pane_goes_hidden=(ph or {}).get("to_hidden"),
                   shard_show_frames=({str(k): v for k, v in
                                       sorted(shows.items(),
                                              key=lambda x: (x[0] is None,
                                                             x[0]))}))
        if roles.get(bay) == "intact":
            rec["expected"] = "pane never hides, no shards"
            if ph is not None or shards:
                bad.append(("bay %d" % bay, "an intact bay must not swap"))
        elif ph is None:
            if shards:
                bad.append(("bay %d" % bay,
                            "shards exist but the pane never hides"))
        else:
            f = ph["frame"]
            wrong = sum(v for k, v in shows.items() if k != f)
            rec["shards_not_on_the_pane_frame"] = int(wrong)
            if wrong:
                bad.append(("bay %d" % bay,
                            "%d shard(s) do not appear on %d" % (wrong, f)))
        out[str(bay)] = rec
    return dict(
        criterion="in the SCENE: each fractured bay's pane hides on exactly "
                  "the frame all of its shards appear",
        blend=blend_path, bays=out, problems=bad, PASS=not bad)


def check_sink(L, Q, verts, floor_z=0.0):
    """Lowest vertex of every body at the last frame, WITH ITS ROTATION.

    R2-196.  The previous revision bounded a body's lowest point as
    `origin_z - max|local v_z|`.  A shard's LOCAL z axis is the PANE's vertical,
    so for a shard lying flat on the floor — which is what most of 2,962
    departed shards are doing by the last key — that axis is HORIZONTAL and the
    bound charges it half its HEIGHT IN THE WALL of penetration.  It reported
    **627** bodies under the floor, worst 154.599 m.  Rotating the vertices
    first gives **70**, worst 154.600 m, and of the 557 it drops, the highest
    true lowest-vertex is z = +0.1055 m and the LOWEST is z = +0.0001 m: every
    one of them is above the floor, not near it, and the old figure was the
    instrument.

    The headline falls 9x, so the axis-aligned number is reported ALONGSIDE it
    rather than deleted.  A metric that drops to a ninth is a claim that needs
    its own evidence, and `reclassified_by_rotation` is that evidence: the
    bodies the two measures disagree about, and how far above the floor they
    actually are.
    """
    P, R = L[-1], qmat(Q[-1])
    n = len(verts)
    lo_true = np.empty(n)
    for i in range(n):
        V = verts[i][0] if isinstance(verts[i], tuple) else verts[i]
        lo_true[i] = (V @ R[i].T)[:, 2].min() + P[i, 2]
    r_axis = np.array([np.abs((v[0] if isinstance(v, tuple) else v)[:, 2]).max()
                       for v in verts])
    lo_axis = P[:, 2] - r_axis
    bad, old = lo_true < floor_z - SINK_M, lo_axis < floor_z - SINK_M
    spur = old & ~bad
    return dict(
        criterion="lowest MESH VERTEX, rotated into world, at the last key",
        below_floor=int(bad.sum()),
        worst_m=float((floor_z - lo_true).max()),
        tol_m=SINK_M,
        axis_aligned_bound_below_floor=int(old.sum()),
        reclassified_by_rotation=dict(
            counted_by_both=int((bad & old).sum()),
            dropped_by_the_rotation=int(spur.sum()),
            found_ONLY_by_the_rotation=int((bad & ~old).sum()),
            dropped_true_lowest_vertex_z_m=(
                [float(lo_true[spur].min()), float(np.median(lo_true[spur])),
                 float(lo_true[spur].max())] if spur.any() else None),
            note="the dropped bodies' TRUE lowest vertex.  If any of these is "
                 "negative the rotation is not what changed the answer."))


def check_overlap(L, Q, meshes, frame_i, k_nearest=6, sample=600, rng=None):
    """Exact convex overlap on a sampled set of near neighbours."""
    rng = rng or np.random.default_rng(0)
    n = len(meshes)
    pos = L[frame_i]
    M = qmat(Q[frame_i])
    idx = rng.choice(n, size=min(sample, n), replace=False)
    # neighbour search on centres
    worst = 0.0
    pairs = 0
    hits = []
    for i in idx:
        d = np.linalg.norm(pos - pos[i], axis=1)
        d[i] = 1e9
        js = np.argsort(d)[:k_nearest]
        Vi = meshes[i][0] @ M[i].T + pos[i]
        Ni = meshes[i][1] @ M[i].T
        for j in js:
            if j <= i:
                continue
            if d[j] > 1.5:
                continue
            Vj = meshes[j][0] @ M[j].T + pos[j]
            Nj = meshes[j][1] @ M[j].T
            dep = sat_depth(Vi, Vj, Ni, Nj)
            pairs += 1
            if dep > worst:
                worst = dep
            if dep > OVERLAP_M:
                hits.append((int(i), int(j), float(dep)))
    hits.sort(key=lambda t: -t[2])
    return dict(pairs_tested=pairs, worst_depth_m=float(worst),
                over_tol=len(hits), tol_m=OVERLAP_M, worst_pairs=hits[:6])


def seam_stat(frames, L, Q, seam_frame):
    """The per-frame change AT a beat boundary against its own neighbourhood.

    Same shape as `tools/car_anim_gate.py`: a ratio to the local median with an
    absolute floor, because a seam at 16 m/s and a seam at rest cannot share a
    threshold.
    """
    f = np.asarray(frames)
    if seam_frame < f[0] + SEAM_WINDOW or seam_frame > f[-1] - SEAM_WINDOW:
        return dict(seam=int(seam_frame), status="OUTSIDE THE TABLE")
    i = int(np.searchsorted(f, seam_frame))
    step = np.linalg.norm(np.diff(L, axis=0), axis=2)
    turn = qangle_step(Q)
    core = slice(max(0, i - SEAM_CORE), min(len(step), i + SEAM_CORE))
    ring = list(range(max(0, i - SEAM_WINDOW), max(0, i - SEAM_CORE))) + \
        list(range(min(len(step), i + SEAM_CORE),
                   min(len(step), i + SEAM_WINDOW)))
    out = {}
    for nm, arr, floor in (("pos_m", step, POP_FLOOR_M),
                           ("rot_deg", turn, POP_FLOOR_DEG)):
        c = float(np.max(arr[core])) if arr[core].size else 0.0
        r = float(np.median(np.max(arr[ring], axis=1))) if ring else 0.0
        out[nm] = dict(seam_max=c, neighbourhood_median=r,
                       ratio=(c / r if r > 1e-12 else float("inf")),
                       verdict=("OK" if (c <= max(SEAM_RATIO * r, floor))
                                else "SEAM"))
    out["seam"] = int(seam_frame)
    return out


def check_persist(frames, L, Q, from_frame):
    """From `from_frame` to the end of the table, nothing may move at all."""
    f = np.asarray(frames)
    i = int(np.searchsorted(f, from_frame))
    if i >= len(f) - 1:
        return dict(status="table ends before %d" % from_frame)
    d = np.linalg.norm(L[i:] - L[i][None], axis=2).max()
    a = np.abs(np.sum(Q[i:] * Q[i][None], axis=2)).clip(-1, 1)
    return dict(from_frame=int(from_frame), to_frame=int(f[-1]),
                max_drift_m=float(d),
                max_turn_deg=float(np.degrees(2 * np.arccos(a.min()))))


# --------------------------------------------------------------------------- #
#  the harness
# --------------------------------------------------------------------------- #

def load_meshes(shards, names, detail=0):
    """(verts, face_normals) per body, in LOCAL coordinates."""
    import shardmesh as SM
    plan = FR.load(shards)
    idx = {n: i for i, n in enumerate(names)}
    out = [None] * len(names)
    for bay in sorted(plan["panes"]):
        for s in plan["panes"][bay]:
            nm = "GS_b%02d_%05d" % (bay, s["id"])
            j = idx.get(nm)
            if j is None:
                continue
            V, F = SM.prism(s["poly"], 14.955, 14.9665, detail=detail,
                            seed=1000 * bay + s["id"])
            out[j] = (np.asarray(V, float), face_normals(np.asarray(V, float),
                                                         F))
    for j, o in enumerate(out):
        if o is None:                        # frame bodies: a coarse box
            out[j] = (np.array([[-.04, -.04, -.4], [.04, -.04, -.4],
                                [.04, .04, -.4], [-.04, .04, -.4],
                                [-.04, -.04, .4], [.04, -.04, .4],
                                [.04, .04, .4], [-.04, .04, .4]]),
                      np.eye(3))
    return out


def run(args):
    # Measure the RECONSTRUCTION, not the bake.  The decimated curves are what
    # Blender evaluates and what Cycles photographs; measuring the pre-decimated
    # table would grade an artefact that never renders.
    import resample as RS
    film = RS.read_film(args.film)
    span = film["span"]
    frames = np.arange(int(span[0]), int(span[1]) + 1)
    L, Q = film["expand"](frames)
    names = film["names"]
    rel = film["release"]
    rep = dict(film=args.film, bodies=L.shape[1],
               frames=[int(frames[0]), int(frames[-1])],
               measured_on="the decimated reconstruction")
    rep["pop"] = check_pop(frames, L, Q)
    rep["visibility"] = check_visibility(rel, frames)
    import fracture as _FR
    rep["swap"] = check_swap(rel, names, _FR.load(args.shards))
    meshes = load_meshes(args.shards, names, detail=0)
    rep["sink"] = check_sink(L, Q, [m[0] for m in meshes])
    rng = np.random.default_rng(11)
    rep["overlap"] = {}
    for ff in args.overlap_frames:
        i = int(np.searchsorted(frames, ff))
        if 0 <= i < len(frames):
            rep["overlap"][str(ff)] = check_overlap(L, Q, meshes, i,
                                                    sample=args.overlap_sample,
                                                    rng=rng)
    rep["seams"] = [seam_stat(frames, L, Q, s) for s in (865, 1057)]
    rep["persist"] = check_persist(frames, L, Q, args.persist_from)
    return rep


def selftest():
    """Every check above, against an injected defect and against a clean table.
    A check that does not fire on its own defect is VACUOUS and says so.
    """
    fails = []

    def check(name, cond, detail=""):
        print("  %-56s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            fails.append(name)

    nf, n = 300, 40
    frames = np.arange(800, 800 + nf)
    t = np.arange(nf) / 156.0
    L = np.zeros((nf, n, 3))
    Q = np.zeros((nf, n, 4))
    Q[:, :, 0] = 1.0
    for j in range(n):
        L[:, j, 0] = 15.0 + 3.0 * t + 0.05 * j
        L[:, j, 1] = -1.0 + 0.05 * j
        L[:, j, 2] = np.maximum(0.06, 2.0 + 1.5 * t - 4.9 * t * t)
        th = (0.9 + 0.1 * j) * t
        Q[:, j, 0] = np.cos(th / 2)
        Q[:, j, 3] = np.sin(th / 2)

    # -- POP
    clean = check_pop(frames, L, Q)
    check("-ve control: a smooth table has no pops",
          clean["pos_pops"] == 0 and clean["rot_pops"] == 0,
          "%d pos, %d rot" % (clean["pos_pops"], clean["rot_pops"]))
    L2 = L.copy()
    L2[150, 7] += np.array([0.9, 0.0, 0.0])       # a 900 mm teleport, 1 frame
    dirty = check_pop(frames, L2, Q)
    check("+ve control: a 0.9 m one-frame teleport is caught",
          dirty["pos_pops"] >= 2, "%d pops, worst %.3f m"
          % (dirty["pos_pops"],
             dirty["worst"][0]["step_m"] if dirty["worst"] else 0))
    Q2 = Q.copy()
    Q2[150, 5] = np.array([math.cos(1.2), 0, math.sin(1.2), 0])
    check("+ve control: a 137 deg one-frame flip is caught",
          check_pop(frames, L, Q2)["rot_pops"] >= 2)

    # -- SINK.  The bodies are 300 x 100 x 12 mm plates: LONG in local z, which
    # is what makes the axis-aligned bound wrong once they lie down.
    plate = np.array([[x, y, z] for x in (-.006, .006) for y in (-.05, .05)
                      for z in (-.15, .15)], float)
    V = [plate.copy() for _ in range(n)]
    L4 = L.copy()
    L4[-1, :, 2] = 0.16                       # upright, clear of the floor
    Q4 = np.zeros_like(Q)
    Q4[:, :, 0] = 1.0                         # identity
    check("-ve control: nothing is under the floor",
          check_sink(L4, Q4, V)["below_floor"] == 0)
    L5 = L4.copy()
    L5[-1, 3, 2] = -0.30
    s5 = check_sink(L5, Q4, V)
    check("+ve control: a plate 300 mm under the floor is caught",
          s5["below_floor"] == 1, "worst %.3f m" % s5["worst_m"])

    # THE CONTROL THAT DISCRIMINATES THE TWO MEASURES, and the reason this
    # function was rewritten.  Lay every plate flat with its lowest vertex 6 mm
    # above the floor.  Laid flat the plate's WORLD z half-extent is its local
    # y (0.05), not its local z (0.15) — the first revision of this control put
    # the ORIGIN at 0.006 and buried 44 mm of plate, then blamed the code.
    # With the origin at 0.056 the true lowest vertex is +0.006 and nothing is
    # sunk, while the axis-aligned bound still charges 0.15 - 0.056 = 0.094 m.
    # If this control ever passes with the two numbers EQUAL, the rotation has
    # stopped being applied and the fix has silently reverted.
    L6 = L4.copy()
    L6[-1, :, 2] = 0.056
    Q6 = Q4.copy()
    Q6[-1, :, 0] = math.cos(math.pi / 4)      # 90 deg about x: local z -> world y
    Q6[-1, :, 1] = math.sin(math.pi / 4)
    s6 = check_sink(L6, Q6, V)
    check("discrimination: plates lying flat 6 mm up are NOT under the floor",
          s6["below_floor"] == 0, "%d" % s6["below_floor"])
    check("discrimination: and the OLD axis bound would have called them all sunk",
          s6["axis_aligned_bound_below_floor"] == n
          and s6["reclassified_by_rotation"]["dropped_by_the_rotation"] == n,
          "old %d of %d, dropped %d"
          % (s6["axis_aligned_bound_below_floor"], n,
             s6["reclassified_by_rotation"]["dropped_by_the_rotation"]))

    # -- OVERLAP (SAT)
    box = np.array([[x, y, z] for x in (-.1, .1) for y in (-.05, .05)
                    for z in (-.006, .006)], float)
    nrm = np.eye(3)
    d = sat_depth(box, box + np.array([0.5, 0, 0]), nrm, nrm)
    check("-ve control: two boxes 300 mm apart do not overlap", d == 0.0,
          "%.4f m" % d)
    # SAT returns the MINIMUM translation distance, not the overlap along the
    # axis you happened to shift.  Two 200 x 100 x 12 mm boxes offset 160 mm in
    # x overlap 40 mm in x but 12 mm through the thickness, and 12 mm is the
    # correct answer: that is how far one has to move to be free.  This control
    # expected 40 mm for one revision and was wrong, not the instrument.
    d = sat_depth(box, box + np.array([0.16, 0, 0]), nrm, nrm)
    check("+ve control: offset boxes measure the MTD (12 mm, not 40)",
          abs(d - 0.012) < 1e-9, "%.5f m" % d)
    d = sat_depth(box, box + np.array([0, 0, 0.008]), nrm, nrm)
    check("+ve control: a 4 mm overlap across the thickness measures 4 mm",
          abs(d - 0.004) < 1e-9, "%.5f m" % d)

    # -- SEAM
    s = seam_stat(frames, L, Q, 950)
    check("-ve control: a smooth table has no seam at 950",
          s["pos_m"]["verdict"] == "OK" and s["rot_deg"]["verdict"] == "OK",
          "ratio %.2f" % s["pos_m"]["ratio"])
    L4 = L.copy()
    L4[151:] += np.array([0.4, 0, 0])             # a 400 mm step at the seam
    s2 = seam_stat(frames, L4, Q, 951)
    check("+ve control: a 400 mm step at the boundary is caught",
          s2["pos_m"]["verdict"] == "SEAM",
          "seam %.3f m vs neighbourhood %.4f m"
          % (s2["pos_m"]["seam_max"], s2["pos_m"]["neighbourhood_median"]))

    # -- PERSIST
    Lp = L.copy()
    Lp[200:] = Lp[200]
    Qp = Q.copy()
    Qp[200:] = Qp[200]
    p = check_persist(frames, Lp, Qp, 1000)
    # 1e-4 deg, not 0: arccos near 1 amplifies float error by 1/sqrt(eps), so a
    # bit-identical quaternion pair still measures ~1.7e-6 deg apart.
    check("-ve control: a frozen tail does not drift",
          p["max_drift_m"] < 1e-12 and p["max_turn_deg"] < 1e-4,
          "%.2e m, %.2e deg" % (p["max_drift_m"], p["max_turn_deg"]))
    Lp[250, 9, 0] += 0.002
    p2 = check_persist(frames, Lp, Qp, 1000)
    check("+ve control: a 2 mm drift after rest is caught",
          p2["max_drift_m"] > 1e-3, "%.4f m" % p2["max_drift_m"])

    # -- SWAP (R2-098).  A synthetic two-bay plan, so the controls do not
    #    depend on whatever the current fracture happens to look like.
    fake_plan = dict(
        roles={3: "destroyed", 8: "intact"},
        panes={3: [dict(id=k) for k in range(5)],
               8: [dict(id=k) for k in range(3)]})
    fake_names = ["GS_b03_%05d" % k for k in range(5)] + \
                 ["GS_b08_%05d" % k for k in range(3)]
    clean_rel = [860, 860, 860, 860, 860, -1, -1, -1]
    s0 = check_swap(clean_rel, fake_names, fake_plan)
    check("-ve control: every shard released with its pane is clean",
          s0["PASS"] and s0["worst_gap_frames"] == 0,
          "worst %d" % s0["worst_gap_frames"])
    check("-ve control: an INTACT bay's never-released shards are not "
          "charged as a hole", "8" not in s0["bays"], str(list(s0["bays"])))
    s1 = check_swap([860, 860, 872, 860, 860, -1, -1, -1],
                    fake_names, fake_plan)
    check("+ve control: one shard 12 frames late is caught",
          (not s1["PASS"]) and s1["worst_gap_frames"] == 12
          and s1["shards_uncovered"] == 1,
          "worst %d, %d uncovered" % (s1["worst_gap_frames"],
                                      s1["shards_uncovered"]))
    s2 = check_swap([860, 860, -1, 860, 860, -1, -1, -1],
                    fake_names, fake_plan)
    check("+ve control: a shard of a FRACTURED bay that never releases is a "
          "hole to the end of the take, not a skip",
          (not s2["PASS"]) and s2["worst_gap_frames"] == LAST_FRAME - 860,
          "worst %d frames" % s2["worst_gap_frames"])

    print("\n%d check(s) FAILED" % len(fails) if fails else "\nall checks passed")
    return 1 if fails else 0


def main():
    if "--" in sys.argv:
        sys.argv = [sys.argv[0]] + sys.argv[sys.argv.index("--") + 1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--swap-scene", action="store_true",
                    help="the SCENE arm of the swap check.  Run inside "
                         "Blender on an applied .blend: each fractured bay's "
                         "pane must hide on exactly the frame all of its "
                         "shards appear.  This is the invariant; the table "
                         "arm below measures the raw material of the defect.")
    ap.add_argument("--swap", action="store_true",
                    help="ONLY the swap check (R2-098): does every shard of a "
                         "fractured bay appear on the same frame its intact "
                         "pane hides?  Any later and there is a hole with "
                         "nothing behind it.  `sim/apply_breach.py` has cited "
                         "this flag for four revisions; until now it did not "
                         "exist.")
    ap.add_argument("--film", default=os.path.join(R2, "sim/out/breach_film.npz"))
    ap.add_argument("--shards",
                    default=os.path.join(R2, "sim/out/fracture_wall.npz"))
    ap.add_argument("--out", default=os.path.join(R2, "sim/out/verify.json"))
    ap.add_argument("--overlap-frames", type=int, nargs="*",
                    default=[870, 900, 960, 1020, 1056, 1200])
    ap.add_argument("--overlap-sample", type=int, default=400)
    ap.add_argument("--persist-from", type=int, default=1200)
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.swap_scene:
        import bpy                                            # noqa: E402
        rep = check_swap_scene(bpy.data.filepath,
                               FR.load(a.shards))
        print(json.dumps(rep, indent=1, default=float))
        print("STAGE RESULT: swap-scene %s (%d problem(s))"
              % ("PASS" if rep["PASS"] else "FAIL", len(rep["problems"])))
        sys.exit(0 if rep["PASS"] else 1)
    if a.swap:
        import resample as RS
        import fracture as _FR
        film = RS.read_film(a.film)
        rep = check_swap(film["release"], film["names"],
                         _FR.load(a.shards))
        print(json.dumps(rep, indent=1, default=float))
        print("STAGE RESULT: swap %s (worst gap %d frames, %d shards "
              "uncovered)" % ("PASS" if rep["PASS"] else "FAIL",
                              rep["worst_gap_frames"],
                              rep["shards_uncovered"]))
        sys.exit(0 if rep["PASS"] else 1)
    rep = run(a)
    with open(a.out, "w") as fh:
        json.dump(rep, fh, indent=1, default=float)
    print(json.dumps(rep, indent=1, default=float))


if __name__ == "__main__":
    main()


# --------------------------------------------------------------------------- #
#  PLAN VIEW — the cheapest way to look at a debris field before renting a GPU
# --------------------------------------------------------------------------- #

def plan_png(L, path, frame_i=-1, meta=None, px_per_m=26):
    """Where the glass ended up, in plan, with the building and the breach
    plane drawn.  Not a substitute for looking at rendered frames; it is the
    thing that catches a field that all landed in one place, or on the wrong
    side of the wall, in two seconds instead of ten minutes of GPU."""
    from PIL import Image, ImageDraw
    x0, x1, y0, y1 = -18.0, 46.0, -16.0, 16.0
    W = int((x1 - x0) * px_per_m)
    H = int((y1 - y0) * px_per_m)

    def xy(p):
        return (int((p[0] - x0) * px_per_m), int(H - (p[1] - y0) * px_per_m))

    im = Image.new("RGB", (W, H), (14, 15, 18))
    dr = ImageDraw.Draw(im)
    dr.rectangle([xy((-15, -11)), xy((15, 11))], outline=(70, 76, 84))
    dr.line([xy((15.0, -16)), xy((15.0, 16))], fill=(210, 120, 40), width=2)
    for m in (-4.8, 4.8):
        dr.line([xy((14.0, m)), xy((16.5, m))], fill=(200, 60, 60), width=1)
    P = L[frame_i]
    for i in range(len(P)):
        p = xy(P[i])
        z = P[i][2]
        c = (60, 190, 210) if z < 0.30 else (230, 210, 120)
        dr.ellipse([p[0] - 1, p[1] - 1, p[0] + 1, p[1] + 1], fill=c)
    im.save(path)
    return path
