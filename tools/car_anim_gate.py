"""CAR ANIMATION GATE — is the car on the road, are the wheels honest, is it one take?

    .venv/bin/python tools/car_anim_gate.py \
        [--measured world/car_anim_measured.json] [--selftest]

Reads `tools/sample_car_blend.py`'s dump — which is `matrix_world` off the built
blend, not the author's model — and measures five things. Every one of them has a
control that must fail and a control that must pass; `--selftest` runs them and
exits non-zero unless every verdict is the expected one.

WHY THIS IS NOT `tools/wheel_rotation_gate.py`
-----------------------------------------------
That gate measures `telemetry.csv`, and it says so. It has four controls and they
all behave. It also has ONE STATED BLIND SPOT: both of its measurements are
anchored on `s_m`, so it cannot see an error in `s_m` itself. There is one, it is
logged as R2-026/R2-047, and it is 25.2 % over the 47 frames of the launch.

MEASUREMENT B HERE IS THE CLOSURE OF THAT BLIND SPOT. Rolling contact is checked
against the distance the car's own keyed transform covers between one frame and
the next — the chord, corrected to the arc by the car's own keyed yaw change —
and `s_m` is never read. Control 3 below is exactly the series `wheel_rotation_
gate.py` passes and this one must not.

WHAT IS MEASURED

  A. MONOTONICITY. `diff(spin)` over all 2,978 film frames, from the F-curve the
     scene evaluates. Must be >= 0 everywhere. Plus: the spin F-curve must agree
     with the spin hub's WORLD matrix modulo 2*pi, and the witness tyre four
     parent levels below it must have turned by the same angle — a key that
     drives nothing would otherwise pass A perfectly.

  B. ROLLING CONTACT, against the ground and not against `s_m`. Per frame:

         residual = spin_step * WHEEL_RADIUS - chord_step

     where `chord_step` is the straight-line distance between the two keyed
     CAR_ROOT positions, which — the keys being LINEAR and per frame — is the
     distance the car actually travels on screen over that frame. Outside the
     flagged wheelspin window the residual must be zero to `TOL_CONTACT_MM`
     millimetres of road. Across the window it must SUM to the declared slip.

  C. THE SANCTIONED WHEELSPIN SURVIVES. The window must carry at least
     `MIN_SANCTIONED_SLIP_REV`. A series that has been "corrected" into pure
     rolling contact must FAIL, and control 2 is that series.

  D. CONTINUITY, IN WORLD TIME. Speed and attitude rate on both sides of every
     beat boundary, and the step across it. Measured per second of WORLD time and
     not per frame, because beat 3's declared speed ramp collapses world time to
     15.4 % over six frames and a per-frame metric calls that a discontinuity —
     it is the shot. Per-frame figures are reported too, because they are what is
     on screen, but the verdict is taken on the physics.

     Two seams carry a real step, both of them inherited from the telemetry and
     both already in the defect log. They are listed in `KNOWN_SEAM_DEFECTS` with
     the magnitude measured today, so the gate passes them and FAILS if either
     gets worse — which is the only useful behaviour for a defect that has been
     deliberately left in place.

  F. BEAT 1 IS UNTOUCHED. CAR_ROOT and all eight hubs at their rest transforms
     for every one of frames 1-792, and 24 witness parts across 16 frames of the
     assembly matched against the same measurement taken on
     `world/beat1_anim.blend` itself.

  E. THE CAR IS ON THE ROAD. The four contact patches — each spin hub's keyed
     world origin, which is the wheel centre, less the rolling radius — against
     `world_contract.ground_z`, the function `world/build_surface.py` builds the
     road mesh from. Measured at the WHEEL and not at the chassis, because the
     chassis moves on its suspension by up to 55 mm and is therefore not where
     the tyre is. This is the number that a picture is still required to confirm;
     it is not a substitute for looking.

TOLERANCES ARE DERIVED, NOT FITTED
-----------------------------------
`TOL_CONTACT_MM` is 1.0 mm of road per frame, and after the fix it is not close.
Blender stores object locations as float32; at the largest coordinate in the film
(|p| ~ 1,500 m) one ULP is 1.2e-4 m, and a chord is a difference of two of them,
so position quantisation alone accounts for ~0.35 mm. The rotation channel is
float32 too and carries 14,026 rad, where one ULP is 1.2e-3 rad = 0.44 mm of
road. 1.0 mm is those two with room, and it is 0.0028 rad of wheel — 0.16
degrees, which no lens in this film resolves.

The SEAM thresholds are a ratio AND an absolute floor, and it takes both. A pure
ratio blew up 1,580x at the beat-2/3 boundary on a rotation step of 0.029 deg,
because the twelve frames before it were flat to six decimals and the median of
"nothing" is zero. A pure absolute cannot serve a seam at rest and a seam at
92 m/s with one number. A seam fails only if it is BOTH out of character for its
own neighbourhood AND large enough to see.
"""

import argparse
import bisect
import json
import math
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "anim"))
sys.path.insert(0, os.path.join(R2, "world"))
import carrig as CR                                                # noqa: E402
import world_contract as C                                         # noqa: E402

TOL_CONTACT_MM = 1.0
MIN_SANCTIONED_SLIP_REV = 0.25
TOL_ROAD_M = 0.030            # see verdict(): what the contact solve claims
TOL_FCURVE_VS_MATRIX_RAD = 1.0e-4

# Continuity. The film is 24 fps; these are what a SEAM may not exceed beyond
# what its own neighbourhood already does. Stated as a RATIO to the local median
# rather than as an absolute, because a seam at 92 m/s and a seam at rest cannot
# share a threshold, and an absolute one would have to be set for the faster.
SEAM_WINDOW = 14              # frames either side used as the local reference
SEAM_CORE = 3                 # frames either side that COUNT AS the seam
SEAM_RATIO = 3.0              # a seam may not be 3x its own neighbourhood ...
# ... AND it must also clear an absolute floor, or a quiet neighbourhood turns a
# 0.029 deg wobble into a 1,580x "defect" (measured: it did). These are what
# would be SEEN across one frame at 24 fps.
SEAM_FLOOR = {"dv_ms": 1.0,                     # 3.6 km/h in 1/24 s
              "domega_rads": math.radians(24.0)}   # 1 deg of attitude per frame

# THE TWO STEPS THAT ARE ALREADY IN THE DEFECT LOG, with the magnitude measured
# on this build. The car reproduces the telemetry faithfully and the telemetry
# has these in it; neither is repairable from inside a car rig, and both were
# left in place deliberately by the decisions recorded against them. Recording
# the size here means the gate passes today and fails the day one grows.
KNOWN_SEAM_DEFECTS = {
    ("2_launch|3_breach", "dv_ms"): (
        1.75, "R2-026 / R2-047: leg 0's `length_m` is measured from the car's "
              "NOSE and its endpoints from the ORIGIN, so `transit_path` runs "
              "11.980 m of arc length across 15.000 m of world X and the car's "
              "world speed is 25.2 % high for the whole launch. The ratio "
              "decays back to 1.0 over three rows, and those rows are the glass "
              "plane, so the correction lands on this seam as -1.72 m/s. NOT "
              "FIXED DELIBERATELY (R2-047): the honest fix moves the breach "
              "frame and with it beat 3's ramp, filmtime.GLASS_WORLD_T and the "
              "124.0833 s master. Nothing a car rig can do about it without "
              "moving the car off the telemetry everything else reads."),
    ("4_transit|5_lap", "dv_ms"): (
        5.80, "R2-046: the transit solve and the lap solve each produce their "
              "own speed at the start/finish line and nothing reconciles them, "
              "so the car crosses 42.6 km/h faster than it arrives (288.16 -> "
              "330.80 km/h in one telemetry row). The time map spreads it over "
              "three film frames: +4.48, +5.79, +1.76 m/s."),
}
KNOWN_SEAM_HEADROOM = 1.20    # a known defect may not grow by more than 20 %


def load(path):
    d = json.load(open(path))
    fr = d["frames"]
    n = len(fr)
    out = {"n": n, "meta": d}
    out["loc"] = np.array([f["loc"] for f in fr])
    out["rot"] = np.array([f["rot"] for f in fr])
    out["spin"] = np.array([[f["spin_fc"][c] for c in ("FL", "FR", "RL", "RR")]
                            for f in fr])
    out["steer"] = np.array([[f["steer_fc"].get(c, 0.0) for c in ("FL", "FR")]
                             for f in fr])
    out["contacts"] = {c: np.array([f["contacts"][c] for f in fr])
                       for c in ("FL", "FR", "RL", "RR")}
    out["hub_y"] = np.array([f.get("spin_hub_local_y", 0.0) for f in fr])
    out["tyre"] = np.array([f.get("tyre_rel", np.eye(4).tolist()) for f in fr])
    out["tyre_hub"] = np.array([f.get("tyre_rel_hub", np.eye(4).tolist())
                                for f in fr])
    return out


def check_identity(m, strict=True):
    """The artefact measured must BE the artefact on disk. Not a formality."""
    p = m["meta"].get("blend")
    notes = []
    if not p or not os.path.exists(p):
        notes.append("the sampled blend %r is not on disk now" % p)
        return notes
    st = os.stat(p)
    if m["meta"].get("blend_bytes") != st.st_size:
        notes.append("%s is %d bytes now, %s when it was sampled"
                     % (p, st.st_size, m["meta"].get("blend_bytes")))
    if abs((m["meta"].get("blend_mtime") or 0) - st.st_mtime) > 1e-6:
        notes.append("%s was modified at %.1f, sampled at %.1f — the dump "
                     "describes a different file from the one on disk"
                     % (p, st.st_mtime, m["meta"].get("blend_mtime") or 0))
    return notes


# ---------------------------------------------------------------- the film ---
def film_context(sheet_path, telemetry, spec_path):
    spec = json.load(open(spec_path))
    rig = CR.CarRig(telemetry, spec)
    W, _info, sheet = CR.world_time_table(sheet_path)
    beats = []
    for b in sheet["beats"]:
        f0 = int(round(b["start_s"] * 24)) + 1
        f1 = int(round((b["start_s"] + b["duration_s"]) * 24))
        beats.append((b["name"], f0, f1))
    return rig, W, sheet, beats


def arc_steps(loc, yaw):
    """Per-frame ground distance covered, from the keyed transform alone.

    THE CHORD, and deliberately not an arc. The keys are LINEAR and per frame, so
    between two of them Blender moves the car in a straight line and that
    straight line is the distance the tyre has to roll. Correcting the chord up
    to the arc of the underlying solve would be measuring a path the render never
    takes: at beat 6's 3.83 m steps through T1 the two differ by 5.2 mm, and the
    difference is the polygonisation of the solve, not a property of the car.

    The yaw step is returned alongside because the seam report wants it.
    """
    ch = np.linalg.norm(np.diff(loc, axis=0), axis=1)
    dth = np.diff(np.unwrap(yaw))
    return ch, dth


def measure(m, rig, W, beats, spin_override=None, beat1_before=None):
    """Every number, in real units. `spin_override` is how the controls work."""
    n = m["n"]
    o = {}
    spin = m["spin"].copy() if spin_override is None else spin_override.copy()
    o["corner_spread_rad"] = float(np.abs(spin - spin[:, :1]).max())
    s = spin[:, 0]

    # ---- A. monotonic -----------------------------------------------------
    d = np.diff(s)
    i = int(np.argmin(d))
    o["A_min_step_rad"] = float(d.min())
    o["A_min_step_frame"] = i + 2
    o["A_backwards_frames"] = int((d < -1e-9).sum())
    o["A_total_rad"] = float(s[-1] - s[0])

    # the F-curve must be driving the transform, and the transform the mesh
    o["A_fc_vs_hub_rad"] = float(np.abs(
        ((m["spin"][:, 0] - m["hub_y"] + math.pi) % (2 * math.pi))
        - math.pi).max())
    # THE WITNESS TYRE. `tyre_rel` is a REAR tyre's transform relative to
    # CAR_ROOT, so it is the rest pose turned by the spin and by nothing else.
    # Comparing it against the rest pose gives the accumulated rotation about the
    # wheel axis directly — modulo 2*pi, which is all a matrix can carry and all
    # that is needed to prove the chain from key to geometry is intact.
    # RIGIDITY: `wheel_tyre_RL_Tyre` relative to its own spin hub must be the
    # same matrix on every frame of the film. If the key were driving nothing,
    # this would still be constant — but then the CAR_ROOT-relative angle below
    # would be zero while the F-curve claimed 14,026 rad, so the two together
    # cannot both be satisfied by a disconnected rig.
    # Only from beat 2 on: for frames 1-792 the tyre is flying in from the
    # exploded field on beat 1's own F-curves, so it is SUPPOSED to move
    # relative to its hub there, and a rigidity check over the assembly would
    # be measuring the assembly.
    th = m["tyre_hub"][792:]
    o["A_tyre_rigid_max"] = float(np.abs(th - th[0]).max())
    o["A_tyre_rigid_frames"] = int(len(th))
    # DERIVED, not chosen. This matrix is `spin_hub_world^-1 @ tyre_world` and
    # both operands carry translations out to |p| ~ 1,500 m in float32, so the
    # cancellation leaves about one ULP at that magnitude however rigid the
    # parenting is. Four of them is the floor of what can be measured here.
    o["A_tyre_rigid_tol"] = 4.0 * float(np.spacing(
        np.float32(np.abs(m["loc"]).max())))
    tm = m["tyre"]
    rest = np.array(tm[0])[:3, :3]
    tyre_ang, want_ang = [], []
    for f in range(0, n, max(n // 600, 1)):
        d3 = np.array(tm[f])[:3, :3] @ rest.T
        tyre_ang.append(math.atan2(d3[0][2], d3[0][0]))
        want_ang.append(((s[f] - s[0] + math.pi) % (2 * math.pi)) - math.pi)
    e = np.abs(((np.array(tyre_ang) - np.array(want_ang) + math.pi)
                % (2 * math.pi)) - math.pi)
    # The residual here is the suspension counter-rotation the hub carries so the
    # tyre stays flat on the road: bounded by |body_roll| + |body_pitch|, which
    # this car declares as 1.4 + 1.6 deg. DERIVED, not fitted to the measurement.
    o["A_tyre_vs_fc_max_rad"] = float(e.max())
    o["A_tyre_compliance_bound_rad"] = math.radians(1.4 + 1.6)
    o["A_tyre_frames_checked"] = int(e.size)

    # ---- A. the STEER sense -----------------------------------------------
    # Measurement B proves the SPIN sense on its own: a reversed spin would make
    # `d` negative against a positive chord and the residual would come out at
    # roughly -2x the distance travelled. Steering has no such consequence — a
    # car with its front wheels turned the wrong way still drives the telemetry's
    # line, it just looks insane — so the sense is checked directly, against the
    # curvature of the path the car is on.
    st = m["steer"][:, 0]
    kap = np.array([rig.curvature(max(W[f], 0.0)) for f in range(1, n + 1)])
    live = np.abs(kap) > 1e-3
    o["A_steer_frames"] = int(live.sum())
    o["A_steer_wrong_way"] = int((np.sign(st[live]) != np.sign(kap[live])).sum())
    o["A_steer_max_deg"] = float(np.degrees(np.abs(st).max()))
    # and the magnitude must be Ackermann for THIS wheelbase, not a taste knob
    want = np.arctan(CR.WHEELBASE_M * kap)
    o["A_steer_vs_ackermann_deg"] = float(np.degrees(np.abs(st - want).max()))

    # ---- B. rolling contact, against the ground --------------------------
    arc, dth = arc_steps(m["loc"], m["rot"][:, 2])
    resid = d * CR.WHEEL_RADIUS_M - arc                    # metres of road
    flag = np.array([rig.wheelspin_flag(max(W[f], 0.0)) for f in range(1, n + 1)])
    on = (flag[1:] > 0) | (flag[:-1] > 0)
    o["B_window_frames"] = int(on.sum())
    o["B_window_first"] = int(np.argmax(on)) + 2 if on.any() else -1
    o["B_off_max_mm"] = float(np.abs(resid[~on]).max() * 1000.0)
    o["B_off_max_frame"] = int(np.argmax(np.abs(np.where(~on, resid, 0.0)))) + 2
    o["B_window_slip_rad"] = float(resid[on].sum() / CR.WHEEL_RADIUS_M)
    o["B_window_slip_rev"] = o["B_window_slip_rad"] / (2 * math.pi)
    o["B_declared_slip_rad"] = float(rig.slip_declared_total)
    o["B_ground_m"] = float(arc.sum())
    o["B_rolling_rev"] = o["B_ground_m"] / (2 * math.pi * CR.WHEEL_RADIUS_M)
    o["B_total_rev"] = o["A_total_rad"] / (2 * math.pi)
    o["B_residual_rev"] = o["B_total_rev"] - o["B_rolling_rev"]

    # ---- what `s_m` would have said, so the blind spot is visible ---------
    sm = np.array([rig.car._lerp(rig.s_c, max(min(W[f], rig.t_end), 0.0))
                   for f in range(1, n + 1)])
    o["B_s_m_total_m"] = float(sm[-1] - sm[0])
    o["B_s_m_shortfall_m"] = o["B_ground_m"] - o["B_s_m_total_m"]

    # ---- D. continuity, in WORLD time -------------------------------------
    dW = np.diff(np.array([max(W[f], 0.0) for f in range(1, n + 1)]))
    dW = np.maximum(dW, 1e-9)
    chord = np.linalg.norm(np.diff(m["loc"], axis=0), axis=1)
    vw = chord / dW                                     # world speed, m/s
    dvw = np.diff(vw)                                   # its step, m/s
    yaw = np.unwrap(m["rot"][:, 2])
    att = np.stack([m["rot"][:, 0], m["rot"][:, 1], yaw], 1)
    omega = np.linalg.norm(np.diff(att, axis=0), axis=1) / dW      # rad/s
    domega = np.diff(omega)
    pf = chord                                          # per-frame, on screen
    dpf = np.diff(pf)

    seams = []
    for k in range(len(beats) - 1):
        name_a, _f0a, f1a = beats[k]
        name_b, _f0b, _f1b = beats[k + 1]
        f = f1a
        rec = {"seam": "%s|%s" % (name_a, name_b), "frame": f,
               "v_before": float(vw[max(f - 2, 0)]),
               "v_after": float(vw[min(f, len(vw) - 1)]),
               "step_before_m": float(pf[max(f - 2, 0)]),
               "step_after_m": float(pf[min(f, len(pf) - 1)])}
        for key, arr in (("dv_ms", dvw), ("domega_rads", domega),
                         ("dstep_m", dpf)):
            # A SEAM IS A NEIGHBOURHOOD, NOT A FRAME. R2-046's speed step is
            # spread over three film frames by the time map, and a metric that
            # samples only the boundary frame reads its smallest third: measured
            # 1.764 m/s on the boundary against 5.793 m/s two frames earlier.
            c = min(max(f - 1, 0), len(arr) - 1)
            lo, hi = max(c - SEAM_CORE, 0), min(c + SEAM_CORE + 1, len(arr))
            core = np.arange(lo, hi)
            j = int(core[np.argmax(np.abs(arr[core]))])
            wlo = max(c - SEAM_WINDOW, 0)
            whi = min(c + SEAM_WINDOW + 1, len(arr))
            nb = np.abs(np.concatenate([arr[wlo:lo], arr[hi:whi]]))
            med = float(np.median(nb)) if nb.size else 0.0
            rec[key] = float(arr[j])
            rec[key + "_frame"] = j + 2
            rec[key + "_neighbourhood"] = med
            rec[key + "_ratio"] = (abs(float(arr[j])) / med if med > 1e-12
                                   else (0.0 if abs(arr[j]) < 1e-12
                                         else float("inf")))
        rec["spin_step_rad"] = float(d[min(max(f - 1, 0), len(d) - 1)])
        seams.append(rec)
    o["D_seams"] = seams

    over, known = [], []
    for s2 in seams:
        for key, floor in SEAM_FLOOR.items():
            val = abs(s2[key])
            if s2[key + "_ratio"] <= SEAM_RATIO or val <= floor:
                continue
            k2 = (s2["seam"], key)
            allow = KNOWN_SEAM_DEFECTS.get(k2)
            row = (s2["seam"], s2["frame"], key, s2[key],
                   s2[key + "_neighbourhood"], s2[key + "_ratio"], floor)
            if allow and val <= allow[0] * KNOWN_SEAM_HEADROOM:
                known.append(row + (allow[0], allow[1]))
            else:
                over.append(row + ((allow[0] if allow else None),
                                   (allow[1] if allow else None)))
    o["D_over"] = over
    o["D_known"] = known
    o["D_stale_allowances"] = [
        list(k2) for k2 in KNOWN_SEAM_DEFECTS
        if not any(kn[0] == k2[0] and kn[2] == k2[1] for kn in known)
        and not any(ov[0] == k2[0] and ov[2] == k2[1] for ov in over)]

    # ---- E. on the road ---------------------------------------------------
    dev, dev_worst, dev_where = [], 0.0, None
    for f in range(1, n + 1, 3):
        wt = max(W[f], 0.0)
        s_tel = rig.car.track_s(wt) + CR.SF_TELEMETRY_S
        for corner, ax, hy, _fr in CR.CORNERS:
            hub = m["contacts"][corner][f - 1]      # the wheel CENTRE, keyed
            want_z = CR.contact_z(hub[0], s_tel + ax, hy)
            got_z = hub[2] - CR.WHEEL_RADIUS_M      # the contact patch
            e = got_z - want_z
            dev.append(e)
            if abs(e) > abs(dev_worst):
                dev_worst, dev_where = e, (f, corner)
    dev = np.array(dev) if dev else np.zeros(1)

    # ---- F. beat 1 is untouched -------------------------------------------
    # The rest pose, held for every frame of the assembly. Two ways, because
    # each catches something the other cannot: the CHASSIS must not have moved
    # (CAR_ROOT at its round-1 transform) and neither must the WHEELS (each hub
    # at its measured centre). A build that keyed the hubs from frame 1 would
    # pass the first and fail the second.
    b1 = slice(0, min(792, n))
    o["F_root_loc_max_m"] = float(np.abs(
        m["loc"][b1] - np.array([0.0, 0.0, 0.340])).max())
    o["F_root_rot_max_rad"] = float(np.abs(m["rot"][b1]).max())
    hw = 0.0
    for corner, ax, hy, _fr in CR.CORNERS:
        want = np.array([ax, hy, 0.340 + CR.WHEEL_CENTRE_Z_LOCAL])
        hw = max(hw, float(np.abs(m["contacts"][corner][b1] - want).max()))
    o["F_hub_max_m"] = hw
    o["F_spin_max_rad"] = float(np.abs(spin[b1]).max())
    o["F_frames"] = int(min(792, n))
    o["F_before"] = None
    if beat1_before is not None:
        worst, where = 0.0, None
        for fs, parts in beat1_before.get("beat1_witness", {}).items():
            now = m["meta"].get("beat1_witness", {}).get(fs, {})
            for name, mat in parts.items():
                if name not in now:
                    continue
                d = float(np.abs(np.array(mat) - np.array(now[name])).max())
                if d > worst:
                    worst, where = d, (fs, name)
        o["F_before"] = {"worst_m": worst, "where": where,
                         "blend": beat1_before.get("blend"),
                         "parts": len(beat1_before.get("witness_parts", []))}

    o["E_road_worst_m"] = float(dev_worst)
    o["E_road_worst_where"] = dev_where
    o["E_road_rms_m"] = float(np.sqrt((dev ** 2).mean()))
    o["E_samples"] = int(dev.size)
    return o


def verdict(o, ident_notes):
    bad = []
    for t in ident_notes:
        bad.append("IDENTITY: " + t)
    if o["A_min_step_rad"] < -1e-9:
        bad.append("A: the wheels turn BACKWARDS %.6f rad (%.4f rev) at film "
                   "frame %d, on %d frame(s)"
                   % (-o["A_min_step_rad"], -o["A_min_step_rad"] / (2 * math.pi),
                      o["A_min_step_frame"], o["A_backwards_frames"]))
    if o["A_fc_vs_hub_rad"] > TOL_FCURVE_VS_MATRIX_RAD:
        bad.append("A: the spin F-curve and the hub's WORLD matrix disagree by "
                   "%.2e rad. The key is not driving the transform."
                   % o["A_fc_vs_hub_rad"])
    if o["A_tyre_rigid_max"] > o["A_tyre_rigid_tol"]:
        bad.append("A: the witness tyre is not rigidly attached to its spin hub "
                   "(worst matrix element moves %.2e over the film, against "
                   "%.2e of float32 headroom at this film's coordinates). The "
                   "parenting is wrong."
                   % (o["A_tyre_rigid_max"], o["A_tyre_rigid_tol"]))
    if o["A_tyre_vs_fc_max_rad"] > o["A_tyre_compliance_bound_rad"]:
        bad.append("A: the witness tyre turns %.4f rad away from what the spin "
                   "F-curve claims, over %d frames. The declared suspension "
                   "compliance can only account for %.4f rad of that, so the "
                   "chain from the key to the geometry is broken and every "
                   "other number here is about a wheel that is not moving."
                   % (o["A_tyre_vs_fc_max_rad"], o["A_tyre_frames_checked"],
                      o["A_tyre_compliance_bound_rad"]))
    if o["A_steer_wrong_way"]:
        bad.append("A: the front wheels steer the WRONG WAY on %d of %d "
                   "cornering frames — the sign of the steer angle does not "
                   "match the sign of the path's curvature."
                   % (o["A_steer_wrong_way"], o["A_steer_frames"]))
    if o["A_steer_vs_ackermann_deg"] > 1e-3:
        bad.append("A: the steer angle departs from atan(wheelbase * curvature) "
                   "by up to %.4f deg. It is supposed to be Ackermann for this "
                   "car's measured 3.600 m wheelbase and nothing else."
                   % o["A_steer_vs_ackermann_deg"])
    if o["corner_spread_rad"] > 1e-6:
        bad.append("A: the four wheels do not share a rotation (spread %.2e rad)"
                   % o["corner_spread_rad"])
    if o["B_off_max_mm"] > TOL_CONTACT_MM:
        bad.append("B: rolling contact is broken OUTSIDE the sanctioned "
                   "wheelspin — the wheels slip %.4f mm of road in one frame at "
                   "film frame %d (tolerance %.2f mm). This is measured against "
                   "the distance the car's own keyed transform covers, so it "
                   "does not depend on `s_m` being right."
                   % (o["B_off_max_mm"], o["B_off_max_frame"], TOL_CONTACT_MM))
    if o["B_window_slip_rev"] < MIN_SANCTIONED_SLIP_REV:
        bad.append("C: the sanctioned launch wheelspin has gone missing — the "
                   "flagged %d-frame window carries %.4f rev of slip, and the "
                   "brief sanctions at least %.2f. A gate that 'corrects' this "
                   "window is the wrong gate; this is the one place in the film "
                   "where rotation is deliberately decoupled from ground speed."
                   % (o["B_window_frames"], o["B_window_slip_rev"],
                      MIN_SANCTIONED_SLIP_REV))
    if abs(o["B_window_slip_rad"] - o["B_declared_slip_rad"]) > 0.02:
        bad.append("C: the window carries %.5f rad of slip; the telemetry "
                   "declares %.5f. The sanctioned violation is not the declared "
                   "one (out by %.5f rad)."
                   % (o["B_window_slip_rad"], o["B_declared_slip_rad"],
                      o["B_window_slip_rad"] - o["B_declared_slip_rad"]))
    for (seam, f, k, val, nb, ratio, floor, allow, why) in o["D_over"]:
        if allow is None:
            bad.append("D: at the seam %s, frame %d, %s steps %+.5f — %.1fx its "
                       "own neighbourhood's %.5f and past the %.5f that would "
                       "be seen across one frame. The film is one take with no "
                       "cuts, and this step is not one of the two the defect "
                       "log already accounts for."
                       % (seam, f, k, val, ratio, nb, floor))
        else:
            bad.append("D: the KNOWN step at %s / %s has GROWN to %+.5f, past "
                       "the %.5f recorded against it (+%.0f%% headroom). %s"
                       % (seam, k, val, allow,
                          (KNOWN_SEAM_HEADROOM - 1) * 100, why))
    if o["F_root_loc_max_m"] > 1e-6 or o["F_root_rot_max_rad"] > 1e-6:
        bad.append("F: CAR_ROOT is not at its round-1 rest transform through "
                   "beat 1 (worst %.3e m, %.3e rad over %d frames). Beat 1's "
                   "616 per-part F-curves are in CAR_ROOT's local space, so the "
                   "whole assembly has moved."
                   % (o["F_root_loc_max_m"], o["F_root_rot_max_rad"],
                      o["F_frames"]))
    if o["F_hub_max_m"] > 1e-6 or o["F_spin_max_rad"] > 1e-9:
        bad.append("F: a wheel hub is not at rest through beat 1 (worst %.3e m, "
                   "spin %.3e rad). The car is stationary on the dais for the "
                   "whole assembly and its wheels do not turn."
                   % (o["F_hub_max_m"], o["F_spin_max_rad"]))
    if o["F_before"] and o["F_before"]["worst_m"] > 1e-5:
        bad.append("F: a beat-1 witness part is %.3e off where %s puts it, at "
                   "frame %s (%s). This build was supposed to leave the "
                   "assembly bit-identical."
                   % (o["F_before"]["worst_m"], o["F_before"]["blend"],
                      o["F_before"]["where"][0], o["F_before"]["where"][1]))
    if abs(o["E_road_worst_m"]) > TOL_ROAD_M:
        bad.append("E: a contact patch is %.4f m off the road at frame %s "
                   "corner %s (tolerance %.3f)"
                   % (o["E_road_worst_m"], o["E_road_worst_where"][0],
                      o["E_road_worst_where"][1], TOL_ROAD_M))
    return bad


def report(name, o, bad):
    print("--- %s" % name)
    print("    A  %d frames, total %.1f rad (%.1f rev); min step %+.3e rad at "
          "f%d; %d backwards"
          % (o.get("n", 0) or 0, o["A_total_rad"], o["B_total_rev"],
             o["A_min_step_rad"], o["A_min_step_frame"],
             o["A_backwards_frames"]))
    print("       F-curve vs hub local matrix %.2e rad; witness tyre rigid to "
          "its hub to %.2e over %d frames (float32 floor %.2e); tyre vs F-curve %.4f rad over %d "
          "samples (the "
          "suspension can explain %.4f); corner spread %.2e rad"
          % (o["A_fc_vs_hub_rad"], o["A_tyre_rigid_max"],
             o["A_tyre_rigid_frames"], o["A_tyre_rigid_tol"],
             o["A_tyre_vs_fc_max_rad"], o["A_tyre_frames_checked"],
             o["A_tyre_compliance_bound_rad"], o["corner_spread_rad"]))
    print("       steer: max %.3f deg, Ackermann to %.2e deg, wrong way on "
          "%d of %d cornering frames"
          % (o["A_steer_max_deg"], o["A_steer_vs_ackermann_deg"],
             o["A_steer_wrong_way"], o["A_steer_frames"]))
    print("    B  ground %.2f m from the keyed transform; `s_m` says %.2f m "
          "(short by %.3f m = R2-026/047, and this gate never reads it)"
          % (o["B_ground_m"], o["B_s_m_total_m"], o["B_s_m_shortfall_m"]))
    print("       %.4f rev turned = %.4f rev rolling + %.4f rev slip; worst "
          "off-window slip %.4f mm of road at f%d (tol %.2f)"
          % (o["B_total_rev"], o["B_rolling_rev"], o["B_residual_rev"],
             o["B_off_max_mm"], o["B_off_max_frame"], TOL_CONTACT_MM))
    print("    C  sanctioned window: %d frames from f%d carrying %.5f rad "
          "(%.4f rev); telemetry declares %.5f rad"
          % (o["B_window_frames"], o["B_window_first"], o["B_window_slip_rad"],
             o["B_window_slip_rev"], o["B_declared_slip_rad"]))
    print("    D  beat seams, in WORLD time (the declared beat-3 ramp is not a "
          "discontinuity and this metric does not see it):")
    for s2 in o["D_seams"]:
        print("       f%-5d %-22s v %7.3f -> %7.3f m/s  dv %+7.3f (nbhd "
              "%.3f, x%6.2f)   domega %+8.5f rad/s (nbhd %.5f, x%6.2f)   "
              "on screen %.5f -> %.5f m/frame"
              % (s2["frame"], s2["seam"], s2["v_before"], s2["v_after"],
                 s2["dv_ms"], s2["dv_ms_neighbourhood"], s2["dv_ms_ratio"],
                 s2["domega_rads"], s2["domega_rads_neighbourhood"],
                 s2["domega_rads_ratio"], s2["step_before_m"],
                 s2["step_after_m"]))
    for kn in o["D_known"]:
        print("       KNOWN  %s f%d %s = %+.4f (allowance %.4f, +%.0f%% "
              "headroom)\n              %s"
              % (kn[0], kn[1], kn[2], kn[3], kn[7],
                 (KNOWN_SEAM_HEADROOM - 1) * 100, kn[8]))
    for st in o["D_stale_allowances"]:
        print("       NOTE   the allowance for %s / %s did not fire — the "
              "defect it forgives is gone and the entry can be removed"
              % (st[0], st[1]))
    print("    E  tyre contact patches (wheel centre less the %.3f m rolling "
          "radius) vs the ground the road is built from: worst %+.4f m at "
          "f%s %s, rms %.4f m over %d samples"
          % (CR.WHEEL_RADIUS_M, o["E_road_worst_m"],
             o["E_road_worst_where"][0] if o["E_road_worst_where"] else "-",
             o["E_road_worst_where"][1] if o["E_road_worst_where"] else "-",
             o["E_road_rms_m"], o["E_samples"]))
    print("    F  beat 1 untouched: CAR_ROOT %.2e m / %.2e rad off its rest "
          "pose over %d frames; hubs %.2e m; spin %.2e rad"
          % (o["F_root_loc_max_m"], o["F_root_rot_max_rad"], o["F_frames"],
             o["F_hub_max_m"], o["F_spin_max_rad"]))
    if o["F_before"]:
        print("       against %s: worst witness part %.2e m over %d parts x 16 "
              "frames (%s)"
              % (os.path.basename(o["F_before"]["blend"] or "?"),
                 o["F_before"]["worst_m"], o["F_before"]["parts"],
                 o["F_before"]["where"]))
    for b in bad:
        print("    FAIL " + b)
    print("    %s" % ("PASS" if not bad else "FAIL"))
    return not bad


# ------------------------------------------------------------------ controls --
def _ctrl_noslip(m, rig, W):
    """POSITIVE 1: pure rolling contact, the launch wheelspin deleted.

    Monotonic, and it reconciles perfectly against the ground. Measurement C is
    the only one that can catch it, which is why C exists: the brief sanctions
    exactly one departure from rolling contact and a gate that lets somebody
    quietly remove it is worse than no gate.
    """
    arc, _ = arc_steps(m["loc"], m["rot"][:, 2])
    s = np.concatenate([[0.0], np.cumsum(arc)]) / CR.WHEEL_RADIUS_M
    return np.repeat(s[:, None], 4, axis=1)


def _ctrl_from_s_m(m, rig, W):
    """POSITIVE 2: the wheels driven off `wheel_rot_rad` — i.e. off `s_m`.

    THIS IS THE CONTROL THAT MATTERS. It is strictly increasing, and it
    reconciles against `s_m` exactly, so `tools/wheel_rotation_gate.py` passes
    it — it is, after all, the shipped column. Measurement B must fail it,
    because over the 47 frames of the launch the car covers 14.78 m of ground
    while the column counts 11.81, and wheels that turn 8.4 rad short of the
    road they are on are wheels dragging through a showroom.
    """
    def col(t):
        if t <= 0.0:
            return rig.wheel_c[0]
        if t <= rig.t_end:
            return rig.car._lerp(rig.wheel_c, t)
        # continued the way the column itself would continue, so the failure
        # this control produces is the LAUNCH and not an artefact of the
        # control stopping where the telemetry does
        return rig.wheel_c[-1] + rig.car.v[-1] * (t - rig.t_end) / \
            CR.WHEEL_RADIUS_M
    s = np.array([col(max(W[f], 0.0)) for f in range(1, m["n"] + 1)])
    s = s - s[0]
    return np.repeat(s[:, None], 4, axis=1)


def _ctrl_windowed(m, rig, W):
    """POSITIVE 3: R2-041 rebuilt — the slip written as a window, not held.

    The defect itself: the accumulated launch slip thrown away on the frame the
    tyres hook up, so the wheels un-spin 1.45 revolutions inside one frame.
    Measurement A must catch it and must name the frame.
    """
    s = m["spin"].copy()
    flag = np.array([rig.wheelspin_flag(max(W[f], 0.0))
                     for f in range(1, m["n"] + 1)])
    last = int(np.argmax(flag[::-1] > 0))
    last = m["n"] - 1 - last
    hold = float(rig.slip(rig.t_end))
    s[last + 1:, :] -= hold
    return s


def _ctrl_clean(m, rig, W):
    """NEGATIVE: a clean series built from scratch — ground + declared slip."""
    arc, _ = arc_steps(m["loc"], m["rot"][:, 2])
    roll = np.concatenate([[0.0], np.cumsum(arc)]) / CR.WHEEL_RADIUS_M
    slip = np.array([rig.slip(max(W[f], 0.0)) for f in range(1, m["n"] + 1)])
    return np.repeat((roll + slip)[:, None], 4, axis=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--measured",
                    default=os.path.join(R2, "world/car_anim_measured.json"))
    ap.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    ap.add_argument("--telemetry",
                    default=os.path.join(R2, "telemetry/telemetry.csv"))
    ap.add_argument("--spec", default=os.path.join(R2, "docs/circuit_spec.json"))
    ap.add_argument("--before",
                    default=os.path.join(R2, "world/beat1_anim_measured.json"),
                    help="the same dump taken on world/beat1_anim.blend, so "
                         "measurement F compares against the artefact this "
                         "build started from rather than against itself")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    m = load(a.measured)
    before = json.load(open(a.before)) if os.path.exists(a.before) else None
    if before is None:
        print(">> NOTE: %s absent — measurement F cannot compare against the "
              "blend this build started from. Produce it with "
              "tools/sample_car_blend.py --allow-no-rig --frames 1-792 on "
              "world/beat1_anim.blend." % a.before)
    rig, W, _sheet, beats = film_context(a.sheet, a.telemetry, a.spec)
    ident = check_identity(m)
    print(">> measured %s" % a.measured)
    print(">> blend %s  %s bytes  mtime %s  (%d frames, %d objects, CAR_ROOT "
          "has %d children)"
          % (m["meta"]["blend"], m["meta"]["blend_bytes"],
             m["meta"]["blend_mtime"], m["n"], m["meta"]["objects_in_scene"],
             m["meta"]["car_root_children"]))

    if not a.selftest:
        o = measure(m, rig, W, beats, beat1_before=before)
        o["n"] = m["n"]
        bad = verdict(o, ident)
        ok = report(os.path.basename(m["meta"]["blend"]), o, bad)
        if a.json:
            json.dump(o, open(a.json, "w"), indent=1, default=str)
        print(">> STAGE RESULT: " + ("CAR_ANIM_OK" if ok else "CAR_ANIM_FAIL"))
        sys.exit(0 if ok else 1)

    cases = [
        ("NEGATIVE  the built rig", None, True),
        ("NEGATIVE  a clean series: ground + declared slip", _ctrl_clean, True),
        ("POSITIVE  the launch wheelspin deleted (pure rolling)", _ctrl_noslip,
         False),
        ("POSITIVE  driven off `wheel_rot_rad`, i.e. off `s_m` — THE BLIND SPOT",
         _ctrl_from_s_m, False),
        ("POSITIVE  R2-041 rebuilt: the slip written as a window", _ctrl_windowed,
         False),
    ]
    allok = True
    for name, fn, want_pass in cases:
        ov = None if fn is None else fn(m, rig, W)
        o = measure(m, rig, W, beats, spin_override=ov,
                    beat1_before=before)
        o["n"] = m["n"]
        bad = verdict(o, ident)
        got = not bad
        good = got == want_pass
        allok &= good
        report("%s  [expect %s]" % (name, "PASS" if want_pass else "FAIL"), o, bad)
        print("    SELFTEST %s" % ("ok" if good else
                                   "BROKEN — the gate did not do what it claims"))
    print(">> STAGE RESULT: " + ("CAR_GATE_SELFTEST_OK" if allok
                                 else "CAR_GATE_SELFTEST_BROKEN"))
    sys.exit(0 if allok else 1)



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
    gate_exit.guard(main, tool="car_anim_gate")
