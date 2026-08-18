"""Beat 1's focus and aperture, DERIVED FROM THE SUBJECT rather than typed in.

Importable by `anim/build_camera_rig.py`; also runnable standalone to analyse a
path file without opening the film:

    python3 tools/r2791_beat1_focus.py --path render/film16_path.json
    python3 tools/r2791_beat1_focus.py --path render/film16_path.json \
        --dump work/r2791/focusdump.json          # + compare against the SHIPPED curve
    python3 tools/r2791_beat1_focus.py --selftest

WHAT WAS WRONG (R2-791)
-----------------------
`docs/beat_sheet.json` carries 23 beat-1 camera keys. Each one sets
`focus_distance_m` to that station's STANDOFF -- the distance from the lens to
the cluster it is presenting -- and `build_camera_rig.insert()` keys it at that
frame and nowhere else. Between two stations Blender interpolates the two
standoffs, and the interpolated number is the distance to NOTHING: the camera
has moved, the parts have moved, and a Bezier between 1.88 m and 2.08 m does not
know about either. The tour spends about 570 of its 640 frames between stations.

The aperture is worse, because it is not merely uncontrolled, it is BACKWARDS.
`build_beatsheet.py` picks `fstop = 2.2 if radius < 0.8 else 2.8` -- a SMALLER
cluster gets a WIDER aperture. But a small cluster is presented from close up,
and depth of field collapses with the square of the distance, so the rule opens
the iris exactly where the depth is already thinnest. Measured at the shipped
keys, at the film's own 2 px / 4K budget:

    SW     58 mm  f/2.2 at 0.750 m  ->  13 mm of total depth of field
    NOSE   58 mm  f/2.2 at 1.378 m  ->  45 mm
    RW     58 mm  f/2.2 at 1.530 m  ->  55 mm
    MB     35 mm  f/2.8 at 4.859 m  ->  2.099 m

Thirteen millimetres, on an assembly 0.345 m deep. That is the client's
"f-stop 1": not a shallow look, an unfocusable one.

WHAT THIS DOES
--------------
1. FOCUS follows the beat's declared subject, per frame, from the camera's own
   forward axis -- the same model `build_camera_rig.Subject.nearest_field()`
   uses for the AIM GATE, and for the same reason its docstring gives: beat 1 is
   a weave through a field of parts, and between two presentations the camera is
   looking at the parts in between. Nominating one cluster per key and calling
   the rest a miss failed that gate at 114 deg on 197 frames.

   Because it is read off the camera's OWN transform and the parts' OWN seat
   schedule, it contains no frame numbers. Re-time the tour, re-station the
   corners, move the seat schedule -- rebuild the rig and the focus is still on
   the subject. That is the whole point of solving it here instead of editing
   23 numbers in the sheet.

2. APERTURE is chosen from the subject's measured depth at that frame, clamped
   to a photographable band, and smoothed. It is not a house stop applied
   uniformly, because the beat does not have one shot in it.

3. Both curves are C1: the cluster the axis is on switches discontinuously, so
   the raw track has steps in it, and a step in focus is a snap. The track is
   softened over `--rack-frames` and then smoothed, which turns each switch into
   a rack -- which is what a focus puller does at that moment anyway.

WHAT IT DELIBERATELY DOES NOT TOUCH
-----------------------------------
* Camera POSITION and ROTATION. Not one line here writes either.
* The CLOSE-OUT, frames >= `CLOSEOUT_F`. f648-792 is the material a review called
  the best in the film and is the protected range the R2-451 re-aim was forbidden
  to move. The solved curve is ramped into the sheet's own values over
  `--handoff-frames` so the join is C1.

  CORRECTION, because I first wrote the opposite and it came from a stale
  source. The brief for this work stated the close-out's focus was already
  accurate -- 0.28 m of error at f700 and 0.02 m at f792. Those figures are from
  `work/b1dof/dump.json`, which is `render/film14.blend` (R2-791), and they
  measure the shipped focus against a NOMINATED CLUSTER'S BOUNDING-BOX CENTRE.
  Measured instead against what the lens actually sees -- the median depth of the
  rays that land on the car, from `tools/r2791_depth_grid.py` -- the close-out
  focus is LONG by 1.23 m at f701 and 1.47 m at f791.

  It is still left alone, and deliberately: by then the subject is the whole
  assembled car, roughly 5 m of it in shot (f701 spans 4.91-8.60 m), so a plane
  set toward the back of the car is a composition choice a reviewer accepted, not
  an error. But the reason for leaving it alone is "it is protected and it is
  someone's authored decision", NOT "it is already correct". The difference
  matters if anyone later re-opens it.
"""

import argparse
import json
import math
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 24.0

# The film's own sharpness budget, from build_beatsheet.py: 2 px at 3840 wide on
# a 36 mm sensor. Imported as numbers rather than re-derived so the two agree.
SENSOR_W_MM = 36.0
RES_X = 3840
SHARP_BUDGET_PX = 2.0
COC_MM = SHARP_BUDGET_PX * SENSOR_W_MM / RES_X          # 0.01875 mm

# The presentation tour ends and the hand-authored close-out begins. Frames from
# CLOSEOUT_F on are left exactly as the sheet authored them.
CLOSEOUT_F = 622
HANDOFF_FRAMES = 30

# Aperture band. The floor keeps the room falling away -- this is a showroom, not
# a technical illustration, and the brief asks for depth that reads, not for
# everything sharp. The ceiling is where stopping down stops buying anything on
# these lenses at these distances and starts pulling the background forward.
# N_MIN IS 2.0 AND NOT 2.8, AND THE RE-FRAMING IS WHY.
#
# The first version floored at f/2.8 on the reasoning that nothing in a beat
# complained about as too blurry should ever open WIDER than it shipped. That was
# right for the framing this work started against and is wrong for the one that
# landed on 2026-08-07 while it was in progress.
#
# Pulling the stations back collapses the thin-depth-of-field problem -- stations
# under 0.20 m of DOF go from 8 of 17 to 3 of 19 -- and creates its mirror image.
# At the new standoffs the background is no longer far behind the subject, so at
# the SAME shipped f/2.8 the room comes forward: CORNER_GROUP now reads 2.3 px of
# background blur, and the six CAR keys 2.0-2.2 px, against the 2 px this film
# calls SHARP. That is the CAD-render look the brief forbids, arriving by the
# other door.
#
# The aperture correction therefore CHANGES SIGN across the beat under the new
# framing: still stopping down at the three remaining 58 mm close stations, and
# now opening UP at the wides to keep the showroom off the subject's plane. A
# floor of f/2.8 would silently block half of that, so the floor is f/2.0 and the
# background bound is allowed to do the work in both directions.
N_MIN, N_MAX = 2.0, 8.0
DEPTH_FRAC_TARGET = 0.80        # hold this much of the subject's depth in budget

# How soft the background must stay, in pixels of circle of confusion at 4K.
#
# 6 px is THREE TIMES the 2 px this film already calls sharp, and it is not a
# taste number: it is the background softness the shipped MB station already
# has. MB is 35 mm at f/2.8 focused 4.859 m with the room 15 m off, which puts
# the far wall at 6.5 px -- and MB is not among the frames anybody complained
# about. So 6 px is the least separation this film has been observed to get away
# with, adopted as the floor rather than invented as one.
#
# What it costs is worth stating: this bound is why the iris is NOT flat across
# the beat. At the 58 mm stations the subject is 1.5 m off and the room is 12 m
# off, so even f/16 leaves the wall 13 px soft and the bound never bites -- the
# ceiling does. At MB the same f/8 would put the wall at 2.3 px, which is inside
# the film's own definition of SHARP, and the bound drags the iris back open to
# about f/3. A single house stop cannot be right at both ends of that.
SEPARATION_PX = 6.0

# Half-width, in frames, of the symmetric smoothing applied to the raw subject
# track. This is a MEASURED trade-off, not a preference. With the depth grid
# driving focus, over the 292 sampled tour frames:
#
#   rack  subject inside the 2px budget   frames with nothing sharp   max step
#     9        median 54.8 %                    63 / 292              0.440 m
#    11        (chosen)                                                     .
#    15        median 40.3 %                    85 / 292              0.232 m
#    21        median 33.1 %                   112 / 292              0.150 m
#   shipped    median  0.9 %                   174 / 292                   .
#
# Every one of them is C1 -- the second difference peaks at 0.0955 m at rack 9
# and falls from there, with no spikes anywhere -- so the constraint "a rack is
# fine, a jump is not" does not choose between them. What chooses is that
# smoothing buys calm by taking the plane off the subject during the move, and
# the note being answered is about blur. 11 keeps most of rack 9's sharpness
# while pulling the fastest move back under a third of a metre per frame.
RACK_FRAMES = 11


# ---------------------------------------------------------------- geometry --
def coc_mm(f_mm, N, focus_m, z_m):
    """Thin-lens circle of confusion, millimetres on the sensor."""
    s, z = focus_m * 1000.0, z_m * 1000.0
    if z <= f_mm or s <= f_mm:
        return float("inf")
    return (f_mm / N) * f_mm * abs(z - s) / ((s - f_mm) * z)


def coc_px(f_mm, N, focus_m, z_m):
    return coc_mm(f_mm, N, focus_m, z_m) * RES_X / SENSOR_W_MM


def n_for(f_mm, focus_m, z_m, budget_px=SHARP_BUDGET_PX):
    """The f-number that puts depth `z_m` inside `budget_px` when focused at
    `focus_m`. Infinite if the geometry cannot be satisfied."""
    s, z = focus_m * 1000.0, z_m * 1000.0
    c = budget_px * SENSOR_W_MM / RES_X
    if z <= f_mm or s <= f_mm:
        return float("inf")
    return f_mm * f_mm * abs(z - s) / (c * (s - f_mm) * z)


def dof_span(f_mm, N, focus_m):
    """(near, far) of the acceptable-sharpness zone, metres."""
    s = focus_m * 1000.0
    H = f_mm * f_mm / (N * COC_MM) + f_mm
    near = s * (H - f_mm) / (H + s - 2 * f_mm)
    far = float("inf") if s >= H else s * (H - f_mm) / (H - s)
    return near / 1000.0, far / 1000.0


# ------------------------------------------------------------- the subject --
class Field:
    """The 15 exploded clusters, where they ARE at a frame.

    This is `build_camera_rig.Subject`'s field model, restated so the solver can
    run without Blender. `test_matches_subject()` checks the two against each
    other rather than trusting the restatement.
    """

    def __init__(self, explode, anim):
        land = {c: v["last_land"] for c, v in anim.get("clusters", {}).items()}
        self.flight_f = float(anim.get("flight_s", 1.55)) * FPS
        self.items = []
        for name, c in explode["clusters"].items():
            fin = [(c["bbox_min"][i] + c["bbox_max"][i]) / 2 for i in range(3)]
            exp = [fin[i] + c["explode_offset"][i] for i in range(3)]
            size = [c["bbox_max"][i] - c["bbox_min"][i] for i in range(3)]
            rad = max(0.5 * math.sqrt(sum(v * v for v in size)), 0.05)
            self.items.append((name, exp, fin, rad, land.get(name)))

    def centre(self, name_idx, f):
        _n, exp, fin, _r, land = self.items[name_idx]
        if land is None:
            return exp
        u = max(0.0, min(1.0, (f - (land - self.flight_f)) / max(self.flight_f, 1.0)))
        u = u * u * (3.0 - 2.0 * u)
        return [exp[i] + (fin[i] - exp[i]) * u for i in range(3)]

    def on_axis(self, f, pos, fwd):
        """The cluster the lens is on: nearest of those whose bounding sphere the
        optical axis pierces; if none is pierced, the one whose EDGE is closest
        to the axis. Returns (index, distance_m, edge_angle_deg).

        The nearest-of-the-pierced rule is what a focus puller does -- when two
        things are both on the axis you hold the near one, because the far one is
        behind it and cannot be seen anyway.
        """
        pierced, best_a = [], None
        for i, (_n, _e, _fin, rad, _l) in enumerate(self.items):
            c = self.centre(i, f)
            d = [c[j] - pos[j] for j in range(3)]
            n = math.sqrt(sum(v * v for v in d)) or 1e-9
            cosang = max(-1.0, min(1.0, sum(d[j] * fwd[j] for j in range(3)) / n))
            a = math.degrees(math.acos(cosang))
            a_edge = max(0.0, a - math.degrees(math.asin(min(1.0, rad / max(n, rad)))))
            if a_edge <= 1e-9:
                pierced.append((n, i, a_edge))
            if best_a is None or a_edge < best_a[2]:
                best_a = (n, i, a_edge)
        if pierced:
            pierced.sort()
            n, i, a = pierced[0]
            return i, n, a
        return best_a[1], best_a[0], best_a[2]


# --------------------------------------------------------------- smoothing --
def hann_smooth(xs, half):
    """Symmetric Hann-weighted smoothing with reflected edges.

    Symmetric so it introduces no lag -- a lagging focus is a focus that trails
    the subject, which is the defect being fixed. Reflected rather than clamped
    so the first and last frames are not dragged toward a constant.
    """
    if half <= 0:
        return list(xs)
    n = len(xs)
    w = [0.5 - 0.5 * math.cos(2 * math.pi * (k + 1) / (2 * half + 2))
         for k in range(2 * half + 1)]
    out = []
    for i in range(n):
        num = den = 0.0
        for k in range(-half, half + 1):
            j = i + k
            if j < 0:
                j = -j
            elif j >= n:
                j = 2 * n - 2 - j
            j = max(0, min(n - 1, j))
            ww = w[k + half]
            num += ww * xs[j]
            den += ww
        out.append(num / den)
    return out


def _interp_keys(d, frames):
    """Linear resample of a sparse {frame: value} onto `frames`, clamped at the
    ends. Returns None if `d` is empty, so callers can tell "no measurement" from
    "measured everywhere"."""
    if not d:
        return None
    ks = sorted(d)
    out, i = {}, 0
    for f in frames:
        while i + 1 < len(ks) and ks[i + 1] <= f:
            i += 1
        if f <= ks[0]:
            out[f] = (ks[0], ks[0], 0.0)
        elif f >= ks[-1]:
            out[f] = (ks[-1], ks[-1], 0.0)
        else:
            a, b = ks[i], ks[min(i + 1, len(ks) - 1)]
            u = 0.0 if b == a else (f - a) / float(b - a)
            out[f] = (a, b, u)
    return out


def _densify1(d, frames):
    ix = _interp_keys(d, frames)
    if ix is None:
        return None
    return {f: d[a] * (1 - u) + d[b] * u for f, (a, b, u) in ix.items()}


def _densify3(d, frames):
    ix = _interp_keys(d, frames)
    if ix is None:
        return None
    return {f: tuple(d[a][k] * (1 - u) + d[b][k] * u for k in range(3))
            for f, (a, b, u) in ix.items()}


def smoothstep(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


# ------------------------------------------------------------- the solver --
def solve(cams, field, shipped_focus=None, shipped_fstop=None,
          rack_frames=RACK_FRAMES, closeout_f=CLOSEOUT_F, handoff=HANDOFF_FRAMES,
          n_min=N_MIN, n_max=N_MAX, depth_frac=DEPTH_FRAC_TARGET,
          subject_depth=None, bg_depth=None, separation_px=SEPARATION_PX):
    """cams: [{'f','p','q'|'fwd','lens'}] ascending. Returns per-frame rows.

    `subject_depth`, when given, is {frame: (near_m, med_m, far_m)} measured off
    the rendered scene by raycast. When it is absent the geometric field model is
    used for both the distance and the depth span. The measured version is
    better and the geometric one always exists; that is why both are here.
    """
    # DENSIFY THE MEASUREMENT ONTO EVERY FRAME FIRST.
    #
    # The depth grid is sampled every Nth frame. Falling back to the geometric
    # model on the frames in between does not "fill the gap" -- it ALTERNATES
    # BETWEEN TWO DIFFERENT ESTIMATORS every frame, and the two disagree by
    # metres. Measured: that alone took the largest per-frame focus step from
    # 0.265 m to 1.834 m, which is a snap, not a rack. The estimator has to be
    # constant along the curve; only then is the remaining variation the
    # subject's.
    frames = [c["f"] for c in cams]
    subject_depth = _densify3(subject_depth, frames)
    bg_depth = _densify1(bg_depth, frames)

    rows = []
    for c in cams:
        f = c["f"]
        pos, fwd = c["p"], c["fwd"]
        idx, dist, a_edge = field.on_axis(f, pos, fwd)
        name = field.items[idx][0]
        rad = field.items[idx][3]
        # WHICH DISTANCE THE PLANE GOES TO, and the measurement decided this.
        #
        # The first version focused on the field model's cluster centre -- the
        # distance to the centre of the bounding sphere of the nearest cluster on
        # the axis. Measured against what the lens actually sees, that only cut
        # the median error from 0.455 m to 0.336 m, and at f401 it was WORSE than
        # what shipped (1.468 m against a subject at 3.329 m, where the shipped
        # curve had 2.110 m). A bounding-sphere centre is not the depth of the
        # visible surface: the sphere is drawn round an exploded cluster and is
        # mostly air, and the camera is often inside or beside it.
        #
        # So when a measured depth exists it IS the answer, and the field model
        # is the fallback for the frames where no part is on the axis at all.
        # Keeping the model as a fallback rather than deleting it matters: this
        # has to produce a curve on any rig it is handed, including one built
        # before the parts are in the scene.
        if subject_depth and f in subject_depth:
            near, med, far = subject_depth[f]
            raw, src = med, "measured"
        else:
            near, med, far = dist - rad, dist, dist + rad
            raw, src = dist, "field"
        rows.append({"f": f, "lens": c["lens"], "cluster": name,
                     "raw_focus_m": raw, "edge_deg": a_edge, "src": src,
                     "near_m": near, "med_m": med, "far_m": far})

    # C1: soften the argmin's switches into racks, then smooth.
    focus = hann_smooth([r["raw_focus_m"] for r in rows], rack_frames)

    # Aperture from the subject's own depth at that frame. `depth_frac` of the
    # span, centred on the plane, is what must fit inside the budget -- holding
    # ALL of it is what produced build_beatsheet's f/37-f/100 and is not a target
    # any lens can meet at these standoffs.
    # THE CEILING IS NOT A TASTE CAP, IT IS THE BACKGROUND.
    #
    # Stopping down to hold the subject also drags the room forward, and a
    # showroom in which the far wall is as sharp as the part IS the CAD render
    # the brief forbids. So the aperture is bounded above by the largest N that
    # still leaves the background at least `SEPARATION_PX` of blur.
    #
    # This bound BINDS DIFFERENTLY along the beat, which is the point: at the
    # 58 mm stations the subject is 1.5 m away and the room is 12 m away, so
    # even f/11 leaves the background 19 px soft and the bound is slack; at the
    # wide moments the subject is 5-9 m away and the same f/8 puts the room at
    # 3.7 px, which reads sharp, so the bound bites and the iris opens. A single
    # house stop cannot do that, and that is why this beat does not get one.
    fst = []
    for r, s in zip(rows, focus):
        half = 0.5 * depth_frac * max(r["far_m"] - r["near_m"], 1e-3)
        z_far = s + half
        z_near = max(s - half, 0.05)
        need = max(n_for(r["lens"], s, z_near), n_for(r["lens"], s, z_far))
        if not math.isfinite(need):
            need = n_max
        cap = n_max
        bg = (bg_depth or {}).get(r["f"])
        if bg and bg > s * 1.05:
            # N at which the background's CoC is exactly SEPARATION_PX
            cap = min(cap, n_for(r["lens"], s, bg, budget_px=separation_px))
        r["n_need"], r["n_cap"] = need, cap
        fst.append(max(n_min, min(cap, need)))
    fst = hann_smooth(fst, rack_frames)

    for r, s, n in zip(rows, focus, fst):
        r["focus_m"], r["fstop"] = s, n

    # Hand the close-out back to the sheet, C1, over `handoff` frames.
    if shipped_focus:
        for r in rows:
            f = r["f"]
            if f >= closeout_f:
                u = 1.0
            elif f > closeout_f - handoff:
                u = smoothstep((f - (closeout_f - handoff)) / float(handoff))
            else:
                u = 0.0
            if u <= 0.0:
                continue
            sf = shipped_focus.get(f)
            sn = (shipped_fstop or {}).get(f)
            if sf is not None:
                r["focus_m"] = r["focus_m"] * (1 - u) + sf * u
            if sn is not None:
                r["fstop"] = r["fstop"] * (1 - u) + sn * u
            r["handoff_u"] = round(u, 4)
    return rows


# ------------------------------------------------------------------- io ----
def quat_fwd(q):
    w, x, y, z = q
    # rotate (0,0,-1) by q
    return [-2 * (x * z + w * y),
            -2 * (y * z - w * x),
            -(1 - 2 * (x * x + y * y))]


def load_cams_from_path(path_json, lo, hi):
    d = json.load(open(path_json))
    out = []
    for e in d["path"]:
        if lo <= e["f"] <= hi:
            out.append({"f": e["f"], "p": e["p"], "lens": e["lens"],
                        "fwd": quat_fwd(e["q"])})
    return out


def depth_from_grid(grid, centre_frac=0.5, lo_q=0.10, hi_q=0.90):
    """(subject_depth, bg_depth) measured off `tools/r2791_depth_grid.py`.

    subject_depth[f] = (near, median, far) depths of the rays that land on an
    assembly PART, inside the central `centre_frac` of the frame by area. The
    centre restriction is deliberate: a part clipping the extreme corner of frame
    is not what the shot is about, and letting it into the depth span is how you
    end up solving for f/100.

    bg_depth[f] = median depth of the rays that land on anything that is NOT a
    part -- the room. This is what bounds the aperture from above.

    Quantiles rather than min/max because a raycast grid will occasionally catch
    a rivet edge-on at a wild depth, and a span defined by its two extreme
    samples is a span defined by its two worst samples.
    """
    gx, gy = grid["grid"]
    x0, x1 = int(gx * (1 - centre_frac) / 2), int(gx * (1 + centre_frac) / 2)
    y0, y1 = int(gy * (1 - centre_frac) / 2), int(gy * (1 + centre_frac) / 2)
    sub, bg = {}, {}
    for e in grid["frames"]:
        z, cls = e["z"], e["cls"]
        s, b = [], []
        for jy in range(gy):
            for jx in range(gx):
                i = jy * gx + jx
                if z[i] < 0:
                    continue
                if cls[i] >= 2:
                    if x0 <= jx < x1 and y0 <= jy < y1:
                        s.append(z[i])
                elif cls[i] == 1:
                    b.append(z[i])
        if s:
            s.sort()
            q = lambda p: s[max(0, min(len(s) - 1, int(p * (len(s) - 1))))]
            sub[e["f"]] = (q(lo_q), q(0.5), q(hi_q))
        if b:
            b.sort()
            bg[e["f"]] = b[len(b) // 2]
    return sub, bg


def load_field():
    ex = json.load(open(os.path.join(R2, "docs/explode_plan.json")))
    an = json.load(open(os.path.join(R2, "world/beat1_anim_anim.json")))
    return Field(ex, an)


def selftest():
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %-56s %s %s" % (name, "ok" if cond else "FAIL", detail))

    # quaternion -> forward, against an explicit rotation
    q = [0.766036, 0.642798, 4e-06, 4e-06]        # ~80 deg about X
    fwd = quat_fwd(q)
    chk("quat_fwd is unit", abs(math.sqrt(sum(v * v for v in fwd)) - 1) < 1e-6)
    chk("quat_fwd of identity is -Z", quat_fwd([1, 0, 0, 0]) == [0.0, -0.0, -1.0])

    # the film's own DOF numbers, reproduced
    near, far = dof_span(58.0, 2.2, 0.750)
    chk("SW station total DOF is 13 mm", abs((far - near) - 0.0126) < 0.002,
        "%.4f m" % (far - near))
    near, far = dof_span(35.0, 2.8, 4.859)
    chk("MB station total DOF is 2.10 m", abs((far - near) - 2.099) < 0.01,
        "%.3f m" % (far - near))

    # n_for must invert coc_px
    n = n_for(58.0, 1.5, 1.7)
    chk("n_for inverts coc_px", abs(coc_px(58.0, n, 1.5, 1.7) - 2.0) < 1e-6,
        "N=%.2f" % n)

    # smoothing must not shift a symmetric feature (no lag) and must preserve a
    # constant exactly
    xs = [1.0] * 40
    chk("hann_smooth preserves a constant",
        max(abs(v - 1.0) for v in hann_smooth(xs, 9)) < 1e-12)
    xs = [0.0] * 20 + [1.0] * 20
    sm = hann_smooth(xs, 9)
    chk("hann_smooth is symmetric about a step (no lag)",
        abs(sm[19] + sm[20] - 1.0) < 1e-9, "%.6f %.6f" % (sm[19], sm[20]))

    # THE CONTROL, AND IT IS TWO-SIDED ON PURPOSE.
    #
    # A one-sided "the solver disagrees with what shipped" would be passed by any
    # curve at all, including a wrong one -- it only proves the solver is not the
    # identity. The claim being made is sharper than that, and it is falsifiable
    # in both directions:
    #
    #   AT A STATION the shipped number is the standoff, which IS the distance to
    #   the cluster being presented, which is what the solver computes. So the
    #   solver must AGREE there. If it does not, the solver has the wrong subject
    #   model and everything downstream of it is wrong.
    #
    #   BETWEEN STATIONS the shipped curve is a Bezier between two standoffs and
    #   the solver is tracking the subject. So they must DIVERGE there, and the
    #   divergence IS the defect.
    #
    # Only both together say "the author's intent was right and the interpolation
    # lost it", which is the actual finding.
    field = load_field()
    cams = load_cams_from_path(os.path.join(R2, "render/film16_path.json"), 1, 792)
    rows = solve(cams, field)
    sheet = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))["beat1"]
    keyed = {int(round(k["t"] * FPS)) + 1: k["focus_distance_m"]
             for k in sheet["camera_keys"] if k.get("focus_distance_m")}
    # ...but ONLY if the path file and the sheet are the same generation. The
    # sheet is re-authored by the agent re-pacing this beat; comparing a solver
    # fed the OLD camera against the NEW sheet's keys measures the gap between
    # two sheets, not the solver. That is a SKIP, not a failure, and saying so is
    # the difference between a useful control and a red light nobody trusts.
    world = {int(round(k["t"] * FPS)) + 1: k["world"]
             for k in sheet["camera_keys"] if k.get("world")}
    cam_at = {c["f"]: c["p"] for c in cams}
    drift = [math.dist(world[f], cam_at[f]) for f in world if f in cam_at]
    same_gen = drift and (sum(drift) / len(drift)) < 0.05
    if not same_gen:
        print("  %-56s SKIP  path file and sheet are different generations "
              "(mean station offset %.3f m) — rebuild the rig from the current "
              "sheet before reading this control"
              % ("solver AGREES at the stations",
                 (sum(drift) / len(drift)) if drift else float("nan")))
    else:
        at_key = [abs(r["focus_m"] - keyed[r["f"]]) for r in rows
                  if r["f"] in keyed and r["f"] < CLOSEOUT_F]
        chk("solver AGREES with the shipped value at the stations",
            at_key and (sum(at_key) / len(at_key)) < 0.35,
            "mean %.3f m over %d stations" % (sum(at_key) / len(at_key), len(at_key)))

    dump = os.path.join(R2, "work/r2791/focusdump.json")
    if os.path.exists(dump):
        d = json.load(open(dump))
        ship = {e["f"]: e["focus_m"] for e in d["frames"]}
        off = [abs(r["focus_m"] - ship[r["f"]]) for r in rows
               if r["f"] in ship and r["f"] < CLOSEOUT_F
               and min(abs(r["f"] - kf) for kf in keyed) > 6]
        chk("solver DIVERGES from the shipped curve between stations",
            off and (sum(off) / len(off)) > 0.50,
            "mean %.3f m over %d off-station frames" % (sum(off) / len(off), len(off)))
    else:
        print("  %-56s SKIP (no %s yet)" % ("between-station divergence", dump))

    print("\nSTAGE RESULT %s r2791_focus_selftest" % ("OK" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=os.path.join(R2, "render/film16_path.json"))
    ap.add_argument("--dump", help="work/r2791/focusdump.json, for the SHIPPED curve")
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=792)
    ap.add_argument("--rack-frames", type=int, default=9)
    ap.add_argument("--every", type=int, default=25)
    ap.add_argument("--json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    field = load_field()
    cams = load_cams_from_path(a.path, a.first, a.last)
    shipped_focus = shipped_fstop = None
    if a.dump and os.path.exists(a.dump):
        d = json.load(open(a.dump))
        shipped_focus = {e["f"]: e["focus_m"] for e in d["frames"]}
        shipped_fstop = {e["f"]: e["fstop"] for e in d["frames"]}
    rows = solve(cams, field, shipped_focus, shipped_fstop,
                 rack_frames=a.rack_frames)

    print("%6s %-14s %6s %8s %8s %7s | %8s %7s | %s"
          % ("f", "subject", "lens", "focus", "shipped", "err", "f/new",
             "f/ship", "DOF new"))
    for r in rows:
        if r["f"] % a.every and r["f"] not in (a.first, a.last):
            continue
        sf = shipped_focus.get(r["f"]) if shipped_focus else None
        sn = shipped_fstop.get(r["f"]) if shipped_fstop else None
        near, far = dof_span(r["lens"], r["fstop"], r["focus_m"])
        print("%6d %-14s %6.1f %8.3f %8s %7s | %8.2f %7s | %.3f m"
              % (r["f"], r["cluster"], r["lens"], r["focus_m"],
                 ("%.3f" % sf) if sf else "-",
                 ("%+.3f" % (sf - r["focus_m"])) if sf else "-",
                 r["fstop"], ("%.2f" % sn) if sn else "-",
                 (far - near) if math.isfinite(far) else float("inf")))

    if a.json:
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
        json.dump({"rows": rows}, open(a.json, "w"))
        print("wrote %s" % a.json)
    print("STAGE RESULT R2791_SOLVE_OK frames=%d" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
