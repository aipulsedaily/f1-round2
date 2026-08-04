#!/usr/bin/env python3
"""THE TWO FRAME THRESHOLDS, DERIVED FROM THE FASTENER — NOT FITTED TO A PICTURE.

R2-092 corrected `THRESH_MULLION_JOINT` and `THRESH_MULLION_BASE` by computing
them from the extrusion's own failure load and left the other two alone.  This
module is the same arithmetic for the two survivors:

  * `THRESH_TRANSOM` — the transom end into the mullion's SP1 screw port;
  * `CON_MUL*_HEAD` — the mullion head into the head beam.

It is stdlib-only and it runs OUTSIDE Blender, so the numbers can be checked
without a 2 h 25 m bake in the way.  Everything it reads about the joint it
reads from `world/items/mullion_intact_interface.json`, which is the file the
sim itself builds the wall from; everything it reads about the fastener it
reads from published material data quoted inline with its source.  The two are
kept apart on purpose and the output labels every line DECLARED, PUBLISHED or
JUDGEMENT, because the previous estimate of this joint ("~15 kN") was
engineering judgement stated as if it were a measurement, and the whole point
of R2-092 was to stop doing that.

    python3 sim/frame_thresholds.py [--json sim/out/frame_thresholds.json]
"""

import argparse
import json
import math
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IFACE = os.path.join(R2, "world", "items", "mullion_intact_interface.json")

# --------------------------------------------------------------------------- #
#  THE UNIT CONVERSION.  This is R2-092's and it is the reason any of this is
#  arithmetic rather than taste.
#
#  Blender hands `breaking_threshold` to Bullet's setBreakingImpulseThreshold,
#  which compares it against the impulse applied in ONE SUBSTEP.  The sim runs
#  at 240 Hz with 8 substeps, so a substep is 1/1920 s and a threshold T holds a
#  sustained force of T x 1920 N.  A threshold is therefore a force divided by
#  1920 and nothing else; every "too strong by 97x" in this project is that
#  division not having been done.
# --------------------------------------------------------------------------- #
SIM_FPS = 240
SUBSTEPS = 8
RATE = SIM_FPS * SUBSTEPS          # 1920 substeps per second


def T_of(force_N):
    return force_N / float(RATE)


def F_of(T):
    return T * float(RATE)


# --------------------------------------------------------------------------- #
#  PUBLISHED MATERIAL AND FASTENER DATA.  Each of these is a number somebody
#  else measured and published; none of them is a choice made here.
# --------------------------------------------------------------------------- #
PUBLISHED = {
    # ISO 68-1 / ISO 724 basic profile, M6 coarse (p = 1.0 mm)
    "M6_pitch_mm": 1.0,
    "M6_stress_area_mm2": 20.12,      # ISO 898-1 A_s = pi/4 (d2+d3)^2/4
    "M6_minor_dia_mm": 4.773,         # d3
    "M6_pitch_dia_mm": 5.350,         # d2
    # ISO 3506-1 property class A2-70
    "A2_70_Rm_MPa": 700.0,
    # EN 1993-1-8 Table 3.4: shear resistance of a bolt with the shear plane
    # through the threaded part, austenitic stainless -> alpha_v = 0.6
    "shear_factor_threaded": 0.60,
    # Aluminum Association / ASM, 6063-T6 extrusion
    "AL6063T6_Rm_MPa": 241.0,
    "AL6063T6_shear_ultimate_MPa": 152.0,
    # linear mass of the modelled mullion extrusion (build_breach_sim, 4.7 kg/m)
    "mullion_kg_per_m": 4.7,
    "transom_kg_per_m": 2.9,
    "g": 9.80665,
}


def load_iface(path=IFACE):
    with open(path) as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- #
#  A. THE TRANSOM END -> MULLION SCREW PORT
# --------------------------------------------------------------------------- #

def transom_threshold(W, verbose=True):
    """Two M6 self-tappers into SP1 in a 6063-T6 extrusion.

    Three candidate failure modes are computed and the SMALLEST governs.  That
    is the whole method: a connection is as strong as its weakest mode, and
    the mode that governs here is not the one the shipped comment implies.
    """
    # SP1 is declared inside `transom_landings`, which is itself the point:
    # the port and the screws that land on it are one declaration.
    sp = W["transom_landings"]["screw_port"]
    sec = W["section"]
    P = PUBLISHED
    out = {"declared": {}, "modes": {}, "judgement": []}

    # ---- what the interface DECLARES about this joint ---------------------- #
    takes = sp["takes"]
    out["declared"]["screw_port_takes"] = takes           # the sentence itself
    out["declared"]["bore_diameter_m"] = sp["bore_diameter_m"]
    out["declared"]["mouth_width_m"] = sp["mouth_width_m"]
    out["declared"]["fastener_grade"] = sec["fastener_grade"]
    out["declared"]["extrusion_alloy"] = sec["extrusion_alloy"]

    # "40 mm minimum engagement" and "6.0 mm nominal" are read out of the
    # sentence rather than retyped, so a change to the interface cannot leave
    # this module quietly computing the old joint.
    d_nom_mm = 6.0
    if "6.0 mm nominal" not in takes:
        raise SystemExit("REFUSING: screw_port.takes no longer says '6.0 mm "
                         "nominal': %r" % takes)
    import re
    m = re.search(r"(\d+(?:\.\d+)?)\s*mm minimum engagement", takes)
    if not m:
        raise SystemExit("REFUSING: screw_port.takes no longer declares a "
                         "minimum engagement: %r" % takes)
    Le_mm = float(m.group(1))
    out["declared"]["nominal_dia_mm"] = d_nom_mm
    out["declared"]["min_engagement_mm"] = Le_mm

    # how many screws per transom end -- COUNTED off transom_landings, not
    # assumed.  The interface lists the z of every screw at every mullion on
    # every line; a transom end is one mullion on one line.
    lines = W["transom_landings"]["lines"]
    counts = set()
    for ln in lines:
        for mu in ln["mullions"]:
            counts.add(len(mu["screws_z"]))
    if counts != {2}:
        raise SystemExit("REFUSING: transom_landings does not declare exactly "
                         "two screws at every station: %r" % sorted(counts))
    n_screw = 2
    gaps = set()
    for ln in lines:
        for mu in ln["mullions"]:
            z = sorted(mu["screws_z"])
            gaps.add(round(z[-1] - z[0], 6))
    out["declared"]["screws_per_transom_end"] = n_screw
    out["declared"]["screw_spacing_m"] = sorted(gaps)

    # ---- MODE 1: the screws shear ----------------------------------------- #
    # The shear plane is the mullion's front face, where the transom end butts
    # it.  The screw is fully threaded there, so the threaded-part factor
    # applies and the area is the tensile stress area.
    tau = P["shear_factor_threaded"] * P["A2_70_Rm_MPa"]          # MPa
    V1 = tau * P["M6_stress_area_mm2"]                            # N per screw
    V_screws = n_screw * V1
    out["modes"]["screw_shear_N"] = V_screws
    out["modes"]["screw_shear_detail"] = (
        "%.2f MPa x %.2f mm^2 = %.0f N per screw x %d = %.0f N"
        % (tau, P["M6_stress_area_mm2"], V1, n_screw, V_screws))

    # ---- MODE 2: the port's internal thread strips ------------------------- #
    # FED-STD-H28 / Machinery's Handbook internal-thread shear area:
    #   A = pi * n * Le * D_min * [ 1/(2n) + 0.57735 (D_min - d2_max) ]
    # with n threads per mm.  SP1 is not a tapped blind hole, it is an OPEN
    # screw race: an 8.5 mm bore with a 5.0 mm mouth, so part of the thread
    # circumference is simply not there.  The engaged fraction is the arc that
    # remains.
    n_thr = 1.0 / P["M6_pitch_mm"]
    A_full = (math.pi * n_thr * Le_mm * d_nom_mm
              * (1.0 / (2.0 * n_thr)
                 + 0.57735 * (d_nom_mm - P["M6_pitch_dia_mm"])))
    r_bore = 0.5 * sp["bore_diameter_m"] * 1000.0                 # mm
    half_mouth = 0.5 * sp["mouth_width_m"] * 1000.0               # mm
    missing_rad = 2.0 * math.asin(min(1.0, half_mouth / r_bore))
    engaged_frac = 1.0 - missing_rad / (2.0 * math.pi)
    A_eng = A_full * engaged_frac
    V_strip = A_eng * P["AL6063T6_shear_ultimate_MPa"] * n_screw
    out["modes"]["thread_strip_N"] = V_strip
    out["modes"]["thread_strip_detail"] = (
        "A_full %.1f mm^2, open race keeps %.1f%% of the circumference "
        "(mouth %.1f mm on a %.1f mm bore = %.1f deg missing) -> %.1f mm^2 "
        "x %.0f MPa x %d = %.0f N"
        % (A_full, 100.0 * engaged_frac, 2 * half_mouth, 2 * r_bore,
           math.degrees(missing_rad), A_eng,
           P["AL6063T6_shear_ultimate_MPa"], n_screw, V_strip))

    # ---- MODE 3: the aluminium bears on the screw shank -------------------- #
    # Transverse load smears over the whole engagement, on the same reduced
    # arc.  Bearing on aluminium is conventionally taken at 2.0 x f_u for a
    # well-confined hole; 1.5 is used here, which is the conservative end.
    BEARING_FACTOR = 1.5
    A_brg = d_nom_mm * Le_mm * engaged_frac
    V_brg = A_brg * BEARING_FACTOR * P["AL6063T6_Rm_MPa"] * n_screw
    out["modes"]["bearing_N"] = V_brg
    out["modes"]["bearing_detail"] = (
        "%.1f mm x %.1f mm x %.3f = %.1f mm^2 x %.1f x %.0f MPa x %d = %.0f N"
        % (d_nom_mm, Le_mm, engaged_frac, A_brg, BEARING_FACTOR,
           P["AL6063T6_Rm_MPa"], n_screw, V_brg))
    out["judgement"].append(
        "bearing factor 1.5 x f_u is a convention, not a measurement; it is "
        "4x clear of the governing mode so it does not decide anything")

    gov = min(("screw_shear", V_screws), ("thread_strip", V_strip),
              ("bearing", V_brg), key=lambda kv: kv[1])
    out["governing_mode"] = gov[0]
    out["capacity_N"] = gov[1]
    out["T"] = T_of(gov[1])

    out["judgement"].append(
        "the shear plane is taken through the THREAD, not a plain shank: a "
        "thread-cutting screw is threaded to the head, so alpha_v = 0.6 and "
        "A_s rather than 0.6 x A_shank.  If the screw had a plain shank at "
        "the joint face the capacity would be %.0f N (T = %.2f) -- 24%% higher "
        "and still the governing mode."
        % (n_screw * 0.6 * PUBLISHED["A2_70_Rm_MPa"]
           * math.pi * 0.25 * d_nom_mm ** 2,
           T_of(n_screw * 0.6 * PUBLISHED["A2_70_Rm_MPa"]
                * math.pi * 0.25 * d_nom_mm ** 2)))
    out["judgement"].append(
        "the flutes of a thread-CUTTING screw remove material at the lead, "
        "not at the head end where the shear plane is, so no flute reduction "
        "is applied.  If one were applied at 15%% the capacity would be "
        "%.0f N (T = %.2f)." % (0.85 * gov[1], T_of(0.85 * gov[1])))
    out["judgement"].append(
        "one scalar has to stand for all six degrees of freedom of a FIXED "
        "constraint.  SHEAR is used because the transom's own dead load and "
        "the impact are both transverse to the screw axis.  The two screws "
        "are %s m apart, so a moment about y is carried as a couple; the "
        "tensile capacity of the pair (%.0f N) is HIGHER than the shear "
        "capacity, so shear remains the conservative scalar."
        % (out["declared"]["screw_spacing_m"],
           n_screw * PUBLISHED["A2_70_Rm_MPa"]
           * PUBLISHED["M6_stress_area_mm2"]))
    return out


# --------------------------------------------------------------------------- #
#  B. THE MULLION HEAD -> HEAD BEAM
# --------------------------------------------------------------------------- #

def head_restraint(W, uid=5, n_seg=8, verbose=True):
    """The head is a MOVEMENT JOINT and the interface says so, per station.

    Nothing here is a strength derivation, because the correction is not a
    strength: it is that the joint has a free axis.  What IS computed is the
    dead load the shipped FIXED joint was carrying, so the size of the error
    is a number rather than an adjective.
    """
    P = PUBLISHED
    st = {r["uid"]: r for r in W["stations"]}[uid]
    out = {"declared": {}, "judgement": []}
    gap = st["head_expansion_gap_m"]
    out["declared"]["head_expansion_gap_m"] = gap
    out["declared"]["station"] = {k: st[k] for k in
                                  ("uid", "y", "foot_z", "head_z")}
    all_gaps = [r["head_expansion_gap_m"] for r in W["stations"]]
    out["declared"]["gap_declared_at_every_station"] = (
        len(all_gaps) == len(W["stations"]) and all(g > 0 for g in all_gaps))
    out["declared"]["gap_range_m"] = [min(all_gaps), max(all_gaps)]

    # what the shipped FIXED joint holds up once the car has taken the bottom
    # 2/8 of the mullion out
    z0, z1 = st["foot_z"], st["head_z"]
    seg = (z1 - z0) / float(n_seg)
    hang_len = (n_seg - 2) * seg
    m_mull = P["mullion_kg_per_m"] * hang_len
    # half of each transom stub bolted into it: three lines, two bays
    lines = len(W["transom_landings"]["lines"])
    ys = sorted(r["y"] for r in W["stations"])
    i = ys.index(st["y"])
    bay_w = 0.5 * ((ys[i] - ys[i - 1]) + (ys[i + 1] - ys[i]))
    m_trn = 0.5 * lines * 2 * P["transom_kg_per_m"] * bay_w
    load_N = (m_mull + m_trn) * P["g"]
    out["hanging_length_m"] = hang_len
    out["hanging_mass_kg"] = m_mull + m_trn
    out["dead_load_N"] = load_N
    out["shipped_T"] = 20.0
    out["shipped_F_N"] = F_of(20.0)
    out["over_strength_ratio"] = F_of(20.0) / load_N
    out["fix"] = ("GENERIC constraint, x and y locked at 0, z and all three "
                  "rotations free -- a slider, which is what a %.1f mm "
                  "declared expansion gap is." % (1000.0 * gap))
    out["T_kept"] = 20.0
    out["judgement"].append(
        "the LATERAL capacity of the head anchor is NOT declared anywhere in "
        "wall_iface, so it cannot be derived here.  The shipped 20 is KEPT "
        "UNCHANGED, deliberately: keeping it means nothing that falls in the "
        "re-bake can have been bought by weakening the head.  The only thing "
        "changed about this joint is its KIND, and that comes from a declared "
        "geometric fact (the gap), not from a strength estimate.")
    out["judgement"].append(
        "the dead load above is the STATIC case.  It is not what decides "
        "whether the column comes down in the bake -- the impact transient "
        "is orders larger.  It is quoted because 97x is the size of the "
        "modelling error, not a prediction.")
    return out


# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iface", default=IFACE)
    ap.add_argument("--json", default=os.path.join(R2, "sim", "out",
                                                   "frame_thresholds.json"))
    a = ap.parse_args()
    W = load_iface(a.iface)

    tr = transom_threshold(W)
    hd = head_restraint(W)

    P = lambda *s: print(*s)
    P("")
    P("=" * 74)
    P("THE UNIT CONVERSION (R2-092): T x %d Hz x %d substeps = T x %d N"
      % (SIM_FPS, SUBSTEPS, RATE))
    P("=" * 74)
    P("")
    P("A.  TRANSOM END -> MULLION SCREW PORT   (THRESH_TRANSOM)")
    P("    DECLARED by wall_iface:")
    P("      screw port SP1 takes: %s" % tr["declared"]["screw_port_takes"])
    P("      bore %.1f mm, open mouth %.1f mm; extrusion %s; fasteners %s"
      % (1000 * tr["declared"]["bore_diameter_m"],
         1000 * tr["declared"]["mouth_width_m"],
         tr["declared"]["extrusion_alloy"],
         tr["declared"]["fastener_grade"]))
    P("      %d screws per transom end, counted at all %d x 11 stations, "
      "spacing %s m"
      % (tr["declared"]["screws_per_transom_end"],
         len(W["transom_landings"]["lines"]),
         tr["declared"]["screw_spacing_m"]))
    P("    FAILURE MODES, smallest governs:")
    for k in ("screw_shear", "thread_strip", "bearing"):
        P("      %-13s %9.0f N   %s"
          % (k, tr["modes"][k + "_N"], tr["modes"][k + "_detail"]))
    P("    GOVERNS: %s at %.0f N = %.2f kN"
      % (tr["governing_mode"], tr["capacity_N"], tr["capacity_N"] / 1e3))
    P("    T = %.0f / %d = %.3f    -> THRESH_TRANSOM = %.1f"
      % (tr["capacity_N"], RATE, tr["T"], round(tr["T"], 1)))
    P("    shipped 260.0 = %.0f kN = %.1fx this."
      % (F_of(260.0) / 1e3, F_of(260.0) / tr["capacity_N"]))
    P("    JUDGEMENT in the above:")
    for j in tr["judgement"]:
        P("      - %s" % j)
    P("")
    P("B.  MULLION HEAD -> HEAD BEAM   (CON_MUL*_HEAD)")
    P("    DECLARED: head_expansion_gap_m = %.4f m at mullion 5; declared at "
      "every station, range %.4f .. %.4f m"
      % (hd["declared"]["head_expansion_gap_m"],
         hd["declared"]["gap_range_m"][0], hd["declared"]["gap_range_m"][1]))
    P("    shipped FIXED at T = %.1f = %.1f kN, holding %.1f m of extrusion "
      "plus half of %d transom stubs = %.1f kg = %.0f N"
      % (hd["shipped_T"], hd["shipped_F_N"] / 1e3, hd["hanging_length_m"],
         6, hd["hanging_mass_kg"], hd["dead_load_N"]))
    P("    over-strength %.0fx" % hd["over_strength_ratio"])
    P("    FIX: %s" % hd["fix"])
    P("    threshold KEPT at %.1f -- see judgement" % hd["T_kept"])
    P("    JUDGEMENT in the above:")
    for j in hd["judgement"]:
        P("      - %s" % j)
    P("")
    P("THE CONFIGURATION THIS DERIVES:")
    P("   --t-transom %.1f  --head-restraint slider" % round(tr["T"], 1))
    P("   (bond 100, mullion joint 40, base 120, glass edge 2.5, pvb 0.9 "
      "unchanged from R2-092)")
    P("")

    doc = dict(unit_conversion=dict(sim_fps=SIM_FPS, substeps=SUBSTEPS,
                                    N_per_threshold_unit=RATE),
               published=PUBLISHED, transom=tr, head=hd,
               recommends=dict(t_transom=round(tr["T"], 1),
                               head_restraint="slider"))
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    with open(a.json, "w") as fh:
        json.dump(doc, fh, indent=1)
    print("wrote %s" % a.json)
    print("STAGE RESULT: derived  t_transom=%.1f  head_restraint=slider"
          % round(tr["T"], 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
