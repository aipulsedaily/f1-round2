"""THE BREACH FINES — the glass the fracture model deletes, put back in the air.

    .venv/bin/python sim/debris.py --selftest
    .venv/bin/python sim/debris.py --build --out sim/out/breach_debris.npz

numpy only, no bpy.  `sim/apply_breach.py --debris` consumes the table this
writes.  It does NOT touch `sim/out/breach_film.npz`, does not re-bake, and does
not change one vertex of the shard field: the fines ride on top of a table that
is already shipped.

--------------------------------------------------------------------------- #
WHY THERE IS NO DEBRIS CLOUD, AND WHY A DEBRIS CLOUD IS NOT WHAT TO BUILD
--------------------------------------------------------------------------- #
R2-129 traced the absence correctly: `apply_breach` builds each shard as a solid
prism and no pass anywhere in `build_breach_sim` / `fracture` / `apply_breach`
ever authored a particle.  R2-546 confirmed it by eye -- "clean flat panes, no
dust burst, no shard cloud".  The obvious repair is a debris cloud and the
obvious repair is WRONG, for a reason that is arithmetic rather than taste.

Laminated glass does not shed a cloud.  That is what the interlayer is FOR.  A
5 / 1.5 PVB / 5 laminate struck at speed crazes, tears and hinges; the fragments
stay on the interlayer and travel as slabs.  The free fines it does shed come
from two places only, and both of them are small:

    the CRUSHED CONTACT   where the nose, the wing endplates and the front
                          tyres grind the outer ply against the interlayer, the
                          free face of that ply spalls forward.
    the ARRIS            every fracture edge chips.  There are 540 m of crack
                          in this wall and every millimetre of it is a chipped
                          edge.

Weighed below, the two come to 2.073 kg out of 2,255.3 kg of glass -- ONE PART
IN 1,088.  Suspended over the contact footprint that is optically dense for a few
frames and thin thereafter.  Any "cloud" a viewer could point at needs an order
of magnitude more mass than the wall contains in a form that can leave it, and
the project's own calibration rule for wear -- "if a viewer can point at the
dirt effect, it is too strong" -- rules exactly that out.  So what is built here
is not a cloud.  It is a FIELD OF FINE GLASS: individually resolvable flakes
that catch the 12.47 deg sun and smear into 100-200 px streaks at the shutter
this beat uses, plus a brief dense burst at the contact that is optical depth
and not geometry (see `powder_report`).

--------------------------------------------------------------------------- #
THE MASS IS NOT CHOSEN.  IT IS RECOVERED.
--------------------------------------------------------------------------- #
`ledger()` weighs, exactly, every gram the shard mesher deletes:

    KERF      `shardmesh.KERF_M` insets every shard by 0.4 mm so two convex
              hulls that share a face do not start life interpenetrating.  Over
              540 m of bonded crack through an 11.5 mm laminate that is 14.40 kg
              of glass that exists in the pane and exists in no rendered object.
              AND THE PROJECT HAS BEEN QUOTING IT WITHOUT KNOWING: the wall's
              declared glass mass, 2,240.9 kg, is `mass_after_kerf_kg` to four
              figures.  The pane's actual mass is 2,255.3 kg.  The 14.4 kg
              difference is not an approximation anybody made -- it is this
              deletion, and it has been the headline number all along.
              `shardmesh.py` already justifies it as "the crack takes material
              with it ... it sheds dust".  THIS MODULE IS THAT SENTENCE KEPT.
    CHAMFER   the 0.6 mm arris on both perimeter rings at detail >= 1.  That is
              a chipped edge, modelled as removed material, and it is the most
              literally correct free-debris source in the whole pipeline.
    CONVEXIFY `fracture._finish` drops slivers.  Weighed, and reported.

The kerf is a CEILING, not the budget, and saying so matters.  A real crack in
soda-lime glass has a kerf of microns: 0.4 mm was picked to keep Bullet stable
(the first full-wall bake without it flew apart at 120.7 m/s) and using it as a
dust mass would over-state the physical fines by two to three orders of
magnitude.  The budget actually spent is derived from the contact instead --
`crush_report()` -- and then checked against the ceiling, which it must not
exceed.  It comes to 13.5 % of it -- and even f_spall = 1.0, every gram of the
crushable ply going free, is only 65 %.  The kerf deletion is larger than the
entire ply it could come from.  That is how big a numerical artefact 0.4 mm is.

--------------------------------------------------------------------------- #
WHAT THIS ALSO ANSWERS: R2-700'S SIZE-DISTRIBUTION OBSERVATION
--------------------------------------------------------------------------- #
R2-700 saw one bake read as "a continuous sheet" on ten times fewer shards than
another (249 vs 2,580) and concluded the variable is the SHARD SIZE
DISTRIBUTION, which neither count nor mass captures.  Measured on the shipped
plan, that distribution is:

    92.4 % of the glass mass is in pieces 160 mm and larger
     1.3 %                    in pieces under 40 mm
    and inside the crushed zone the pieces are near-MONODISPERSE -- p10 11.8 mm,
    p90 28.7 mm, a 2.4x spread, because a recursive mosaic that splits until it
    is under a target area produces cells clustered just under that target.

Real comminution is scale-free; a Schuhmann fit to the crushed-zone shards gives
b = 3.68 against a physical 0.8-1.2, which is a statement about the generator,
not about glass.  So the missing thing is not "more shards": it is the LOWER
TAIL, three decades of it, from the model's 8 mm floor down to the resolution
limit.  This module is that tail.  One fix, both defects.

--------------------------------------------------------------------------- #
THE REPRESENTATION, AND ITS ONE APPROXIMATION STATED PLAINLY
--------------------------------------------------------------------------- #
A kilogram of millimetre glass is three quarters of a million flakes.  They
cannot each be an animated Blender object, so chips are carried in PUFFS: one
puff is one spall site in one SIZE BIN, holding 8-40 chips inside a ~50 mm ball,
keyed as one rigid body with its own ballistic-plus-drag path and its own spin.

Grouping by size bin is not a convenience.  Aerodynamic drag on a flake goes as
1/d (`drag_k`), so a 6 mm chip coasts 3.4 m and a 1 mm chip coasts 0.57 m: a
puff of mixed sizes would have to disperse and a rigid one could not.  Binned by
size, every chip in a puff shares a trajectory to within a few per cent over the
whole flight, and the rigid approximation costs nothing that can be seen.

WHAT IT DOES COST, said out loud: chips inside a puff do not tumble
independently, they tumble with it.  At the 180 deg shutter this beat runs --
0.0032 s of world time at the ramp's 15.4 % -- a chip's own spin is smeared out
within the frame anyway, and the puff spin supplies the between-frame change.
A field where every chip tumbled on its own would twinkle slightly more.  That
is the trade and it bought a 60x reduction in animated objects.
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

import debrismesh as DM                                            # noqa: E402
import fracture as FR                                              # noqa: E402
import shardmesh as SM                                             # noqa: E402

OUT = os.path.join(R2, "sim", "out")

RHO_GLASS = 2500.0
RHO_AIR = 1.225
CD_FLAKE = 1.17                    # the same plate Cd build_breach_sim uses
G = 9.80665
LAM_TH = SM.GLASS_TH if hasattr(SM, "GLASS_TH") else 0.0115
GLASS_X_IN, GLASS_X_OUT = 14.955, 14.9665
PLY_M = 0.005                      # one ply of the 5 / 1.5 PVB / 5 laminate

# --------------------------------------------------------------------------- #
#  THE CRUSHED CONTACT.  Every number here is read off the fracture model's own
#  energy field, not invented alongside it.
# --------------------------------------------------------------------------- #
# `fracture.Impact.energy` is a stretched exponential whose exponent q = 1.7 was
# chosen, in that module's own words, so that "the crushed zone [has] a flat top
# the width of the contact, which is what a comminuted zone is".  E_CRUSH is the
# edge of that flat top.  It is not a new parameter; it is a reading of one.
E_CRUSH = 0.90

# The one number in this file that is a judgement and not a measurement, so it
# is alone, named, and cited.  Of the outer ply inside the crushed footprint,
# the fraction that leaves as free fines rather than staying bonded to the
# interlayer.  Bounds that bracket it: a roughness-layer model of the fracture
# surfaces alone gives 93 g (all sub-50 um), and a contact-volume model with
# every crushed grain going free gives 9.05 kg.  0.12 sits between them at
# 1.09 kg and is inside the 12.43 kg kerf ceiling by 11x.
# IF THIS IS WRONG IT IS WRONG BY A FACTOR, NOT A DECADE, and `--f-spall` sweeps
# it without a rebuild.
F_SPALL = 0.12

# Schuhmann / Gates-Gaudin: cumulative mass passing d goes as (d/D)**b.  b = 1.0
# is the textbook value for brittle comminution and is what the shard plan does
# NOT have (it fits 3.68, which is the mosaic generator's signature).  D is the
# top size: a flake bigger than this is not a flake, it is one of the 8 mm
# shards `fracture.py` already owns, and double-counting it would put the same
# glass on screen twice.
SCHUHMANN_B = 1.0
D_TOP = 0.006
D_BOT = 5.0e-5                     # below this it is powder; see powder_report

# The ejection cone.  Spall off a free face leaves normal to that face at a
# small fraction of the impactor speed; the car is doing ~40 m/s at the wall.
EJECT_FRAC = (0.04, 0.20)          # of the parent shard's own release speed
EJECT_CONE_DEG = 38.0
EJECT_MIN_MS = 0.8

PUFF_BALL_M = 0.050                # chips of one puff are born inside this ball
PUFF_MIN, PUFF_MAX = 8, 40
PUFF_SPIN_RADS = (2.0, 14.0)       # world rad/s

# Pixel grading, exactly the currency the rest of this project argues in.
PX_W, SENSOR_MM = 3840, 36.0       # the delivery format, not rung 1
PX_MIN = 1.6                       # a chip below this at its own closest
                                   # approach is not built; see select()


# --------------------------------------------------------------------------- #
#  1.  THE LEDGER.  What the mesher deleted, to the gram.
# --------------------------------------------------------------------------- #

def ledger(plan, detail=1):
    """Weigh every gram of glass the shard mesher removes.

    Exact, not modelled: it builds the shard both ways (with and without the
    kerf/chamfer) and differences the signed volumes.  That is slow enough to be
    worth doing once and important enough that estimating it would be silly --
    the entire debris budget is checked against this ceiling.
    """
    th = GLASS_X_OUT - GLASS_X_IN
    rows = []
    for bay in sorted(plan["panes"]):
        if plan["roles"][bay] == "intact":
            continue
        for s in plan["panes"][bay]:
            A = float(s["area"])
            V_cell = A * th                                  # the pane's own
            Vk, Fk = SM.prism(s["poly"], GLASS_X_IN, GLASS_X_OUT,
                              detail=0, seed=0)
            V_kerf = SM.volume(Vk, Fk)                       # kerf applied
            Vc, Fc = SM.prism(s["poly"], GLASS_X_IN, GLASS_X_OUT,
                              detail=detail, seed=1000 * bay + s["id"])
            V_built = SM.volume(Vc, Fc)                      # + chamfer
            rows.append((bay, s["id"], V_cell, V_kerf, V_built, s["energy"]))
    a = np.array([(r[2], r[3], r[4]) for r in rows])
    e = np.array([r[5] for r in rows])
    m_cell, m_kerf, m_built = (a * RHO_GLASS).sum(axis=0)
    out = dict(
        n_shards=len(rows),
        mass_cells_kg=float(m_cell),
        mass_after_kerf_kg=float(m_kerf),
        mass_built_kg=float(m_built),
        kerf_kg=float(m_cell - m_kerf),
        chamfer_kg=float(m_kerf - m_built),
        deleted_kg=float(m_cell - m_built),
        deleted_frac=float((m_cell - m_built) / m_cell),
        detail=detail)
    # split the kerf by where its crack lies in the comminution field
    hi = e >= E_CRUSH
    out["kerf_in_crush_kg"] = float(
        ((a[hi, 0] - a[hi, 1]) * RHO_GLASS).sum())
    out["kerf_far_field_kg"] = out["kerf_kg"] - out["kerf_in_crush_kg"]
    out["note"] = (
        "kerf_kg is a CEILING set by a numerical choice (Bullet's collision "
        "margin), not a physical dust mass: a real crack in soda-lime glass "
        "has a kerf of microns.  kerf_far_field_kg is fracture-surface "
        "roughness that stays ON the shard and its correct rendering is a "
        "frosted thickness band, not a particle.")
    return out


# --------------------------------------------------------------------------- #
#  2.  THE BUDGET.  Derived from the contact, capped by the ledger.
# --------------------------------------------------------------------------- #

def crush_report(plan, f_spall=F_SPALL):
    """The crushed footprint and the free-fines mass it yields."""
    A_crush = 0.0
    A_dest = 0.0
    for bay in sorted(plan["panes"]):
        if plan["roles"][bay] == "intact":
            continue
        for s in plan["panes"][bay]:
            A_dest += s["area"]
            if s["energy"] >= E_CRUSH:
                A_crush += s["area"]
    m_ply = A_crush * PLY_M * RHO_GLASS
    return dict(E_CRUSH=E_CRUSH,
                footprint_m2=float(A_crush),
                fractured_glass_m2=float(A_dest),
                footprint_frac=float(A_crush / A_dest),
                outer_ply_in_footprint_kg=float(m_ply),
                f_spall=f_spall,
                crush_spall_kg=float(m_ply * f_spall))


def budget(plan, led=None, f_spall=F_SPALL):
    """The two free-fines sources, and the ceiling test."""
    led = led or ledger(plan)
    cr = crush_report(plan, f_spall)
    b = dict(crush=cr, ledger=led)
    b["crush_spall_kg"] = cr["crush_spall_kg"]
    b["arris_spall_kg"] = led["chamfer_kg"]
    b["free_kg"] = b["crush_spall_kg"] + b["arris_spall_kg"]
    b["ceiling_kg"] = led["kerf_kg"] + led["chamfer_kg"]
    b["frac_of_ceiling"] = b["free_kg"] / b["ceiling_kg"]
    b["PASS"] = bool(b["free_kg"] <= b["ceiling_kg"])
    b["free_frac_of_wall"] = b["free_kg"] / led["mass_cells_kg"]
    return b


# --------------------------------------------------------------------------- #
#  3.  THE SIZE LAW, and what it implies before a single chip is built.
# --------------------------------------------------------------------------- #

def draw_sizes(rng, n, d_bot=D_BOT, d_top=D_TOP, b=SCHUHMANN_B):
    """n plan sizes from the Schuhmann mass distribution.

    Cumulative MASS passing d is (d/D)^b, so the number density is
    dN/dd ~ d^(b-4).  Inverting the number CDF analytically keeps this exact
    rather than rejection-sampled, which matters because the mass the field
    carries is then a closed-form check (`law_report`) and not a tally.
    """
    p = b - 3.0                      # dN/dd ~ d^(p-1)
    u = rng.random(n)
    lo, hi = d_bot ** p, d_top ** p
    return (lo + u * (hi - lo)) ** (1.0 / p)


def law_report(mass_kg, d_bot=D_BOT, d_top=D_TOP, b=SCHUHMANN_B):
    """Count, mass and PROJECTED AREA per size decade, closed form.

    Projected area is the one that decides whether the field reads: a chip's
    contribution to the frame is its area, and the total area is what sets the
    optical depth of the part that is too small to resolve.
    """
    phi = DM.SHAPE_FACTOR
    # mass per unit d:  dM/dd = mass * b * d^(b-1) / D^b
    # count per unit d: dN/dd = (dM/dd) / (rho * phi * d^3)
    K = mass_kg * b / (RHO_GLASS * phi * d_top ** b)

    def _pow_int(a, c, p):
        """int_a^c x^(p-1) dx, with the p = 0 branch that is a logarithm.

        b = 1 (the physical value) makes the projected-area exponent exactly
        zero and b = 3 (the negative control) does the same to the count's, so
        both branches are exercised on every selftest rather than lying in wait.
        """
        return (math.log(c / a) if abs(p) < 1e-12 else (c ** p - a ** p) / p)

    def N(a, c):
        return K * _pow_int(a, c, b - 3.0)

    def A(a, c):                      # projected area, ~0.25 d^2 per chip
        return 0.25 * K * _pow_int(a, c, b - 1.0)

    def M(a, c):
        return mass_kg * ((c / d_top) ** b - (a / d_top) ** b)

    edges = [d_bot]
    while edges[-1] < d_top:
        edges.append(min(edges[-1] * 10.0, d_top))
    bands = []
    for i in range(len(edges) - 1):
        a, c = edges[i], edges[i + 1]
        bands.append(dict(d_lo_mm=1000 * a, d_hi_mm=1000 * c,
                          count=float(N(a, c)), mass_kg=float(M(a, c)),
                          proj_area_m2=float(A(a, c))))
    return dict(mass_kg=mass_kg, d_bot_mm=1000 * d_bot, d_top_mm=1000 * d_top,
                b=b, bands=bands,
                total_count=float(N(d_bot, d_top)),
                total_proj_area_m2=float(A(d_bot, d_top)))


def powder_report(plan, mass_kg, d_split=0.0015):
    """The fraction that CANNOT be geometry, and what omitting it costs.

    Below `d_split` a chip is under 2 px at 4K even at the camera's closest
    approach to the wound (1.022 m at f903, 2,191 px/m).  It cannot read as a
    shape; it can only read as extinction.  So it is weighed as an optical
    medium and NOT built, and this is the number that says whether that is
    defensible.
    """
    lo = law_report(mass_kg, D_BOT, d_split)
    frac = ((d_split / D_TOP) ** SCHUHMANN_B)
    m_lo = mass_kg * frac
    lo = law_report(m_lo, D_BOT, d_split)
    A = lo["total_proj_area_m2"]
    sig = 2.0 * A                    # extinction ~ 2 x geometric at these sizes
    out = dict(d_split_mm=1000 * d_split, powder_kg=float(m_lo),
               powder_count=lo["total_count"],
               powder_proj_area_m2=float(A),
               extinction_cross_section_m2=float(sig))

    # HOW BIG IS THE CLOUD, AND HOW LONG DOES IT LAST.
    #
    # THE FIRST REVISION OF THIS FUNCTION GOT BOTH WRONG AND IN THE SAME
    # DIRECTION -- optimistically.  It divided the extinction by "the aperture
    # after 0.3 s" and "25 m of apron after 1.0 s" and reported tau falling
    # 8.35 -> 0.23 -> 0.04, i.e. a brief burst that blows away with the car.
    # Those volumes were ASSUMED, and they assumed the powder travels.  It does
    # not.  `drag_k` goes as 1/d, so a 0.6 mm flake has a drag length of 0.34 m:
    # the powder stops within a third of a metre of the crack that made it.  It
    # does not follow the car onto the apron and it does not thin by spreading.
    # It hangs.
    #
    # What actually removes it is SETTLING, and that is slow.  Terminal speed is
    # sqrt(g/k) = sqrt(g d / 1.76e-3): 2.89 m/s at 1.5 mm but 0.53 m/s at 50 um,
    # and the EXTINCTION is dominated by the fine end while the MASS is
    # dominated by the coarse end.  Beat 3 is eight seconds of screen time at
    # the ramp's 15.4 %, which is about 1.5 s of WORLD time -- less than the
    # fall time of anything under half a millimetre.
    #
    # So the honest statement is the opposite of the first one: this is not a
    # flash, it is a persistent, optically thick cloud sitting in the aperture.
    def _v_term(d):
        return math.sqrt(G / drag_k(d))

    # cloud radius: the ejecta's own drag-limited range, saturating fast
    kf = float(drag_k(0.0006))
    v0 = 12.0
    A0 = crush_report(plan)["footprint_m2"]
    prof = []
    for t in (0.0, 0.05, 0.15, 0.3, 0.6, 1.0, 1.5, 3.0, 6.0, 12.0):
        r = max(0.05, math.log1p(kf * v0 * t) / kf)
        area = A0 + 2.0 * math.sqrt(A0) * r + 0.25 * math.pi * r * r
        # settled fraction of the EXTINCTION (not of the mass): integrate the
        # projected area still airborne, i.e. sizes whose fall time from the
        # cloud's own height exceeds t
        H = 3.0
        d_fallen = min(d_split, max(D_BOT, (1.76e-3 / G) * (H / max(t, 1e-6)) ** 2))
        # projected area remaining is the part of the law below d_fallen
        rem = (law_report(m_lo, D_BOT, d_fallen)["total_proj_area_m2"] / A
               if d_fallen > D_BOT else 0.0)
        prof.append(dict(t_world_s=t, cloud_r_m=round(r, 3),
                         airborne_frac=round(min(1.0, rem), 4),
                         tau=round(2.0 * A * min(1.0, rem) / max(area, 1e-9), 3)))
    out["profile"] = prof
    out["v_term_m_s"] = {"1.5 mm": round(_v_term(0.0015), 2),
                         "0.5 mm": round(_v_term(0.0005), 2),
                         "0.1 mm": round(_v_term(0.0001), 2),
                         "50 um": round(_v_term(5e-5), 2)}
    out["drag_length_m_at_0.6mm"] = round(1.0 / kf, 3)
    out["verdict"] = (
        "NOT a brief burst.  The powder's drag length is 0.34 m, so it stops "
        "at the wall instead of travelling with the car, and what clears it is "
        "settling, which for the sizes that carry the extinction takes many "
        "seconds of WORLD time against a beat that spends about 1.5 s of it.  "
        "As modelled it is a persistent, optically thick cloud standing in the "
        "aperture -- which is a CONTINUITY question (the wound is framed again "
        "in beat 6) before it is a render-cost one.  It is still not built, and "
        "the reason has changed: not 'too small to be geometry' but 'too "
        "long-lived to add without deciding what it does to beats 4-6'.")
    return out


# --------------------------------------------------------------------------- #
#  4.  MOTION.  Ballistic with quadratic drag, integrated in WORLD time.
# --------------------------------------------------------------------------- #

def drag_k(d):
    """1/length constant for a tumbling flake: dv/dt = -k |v| v + g.

    A convex body tumbling with no preferred orientation presents S/4 (Cauchy);
    for a flake of plan size d, S ~ 0.5 d^2, so A_proj ~ 0.125 d^2, and the mass
    is rho * SHAPE_FACTOR * d^3.  k therefore goes as 1/d and the whole
    behaviour of this field follows from that one line: fine glass stops.
    """
    m_over_d3 = RHO_GLASS * DM.SHAPE_FACTOR
    return 0.5 * RHO_AIR * CD_FLAKE * 0.125 / (m_over_d3 * np.asarray(d, float))


def fly(p0, v0, k, t, z_floor=0.0, r_rest=0.002, g_z=-G):
    """Integrate one trajectory at world times `t` (seconds from birth).

    RK4 with a fixed substep; the whole field is a few thousand paths so
    accuracy is free.  Lands and stays: once z is at the floor and the vertical
    speed is small the path is clamped, which is what makes the wound persist in
    beats 4-6 for the same zero cost the shards' CONSTANT extrapolation gets.
    """
    t = np.asarray(t, float)
    P = np.empty((len(t), 3))
    p = np.array(p0, float)
    v = np.array(v0, float)
    g = np.array([0.0, 0.0, float(g_z)])
    zf = z_floor + r_rest
    landed = False
    t_land = float(t[-1]) if len(t) else 0.0

    def acc(vv):
        s = float(np.linalg.norm(vv))
        return g - k * s * vv

    tp = 0.0
    now = 0.0
    for i, tt in enumerate(t):
        n = max(1, int(math.ceil((tt - tp) / 0.002)))
        h = (tt - tp) / n if n else 0.0
        for _ in range(n):
            if landed:
                break
            now += h
            # RK4 ON THE FULL STATE [p, v], not on v with a hand-rolled
            # position update.  The first revision advanced p by
            # h*(v + 0.25*dv) -- second-order at best -- and the no-drag
            # control caught it at 1.7 mm over 0.4 s.  A 1.7 mm error is
            # 3.7 px at this beat's closest approach, so it was not academic.
            v1 = v
            a1 = acc(v)
            v2 = v + 0.5 * h * a1
            a2 = acc(v2)
            v3 = v + 0.5 * h * a2
            a3 = acc(v3)
            v4 = v + h * a3
            a4 = acc(v4)
            p = p + (h / 6.0) * (v1 + 2 * v2 + 2 * v3 + v4)
            v = v + (h / 6.0) * (a1 + 2 * a2 + 2 * a3 + a4)
            if p[2] <= zf:
                p[2] = zf
                # a flake does not bounce; it skitters and stops.  Bleed the
                # horizontal in one step rather than pretending to model it.
                v[:] = 0.0
                if not landed:
                    # the SUBSTEP clock, not the key time: `tp` is the previous
                    # KEY, so using it put every landing at the start of
                    # whatever key interval it happened in -- up to half a
                    # second early on the first interval.
                    t_land = now
                landed = True
        P[i] = p
        tp = tt
    return P, t_land


# --------------------------------------------------------------------------- #
#  5.  THE FIELD.
# --------------------------------------------------------------------------- #

def parent_state(film, j, clock, rel=None, window=5):
    """(home position, LAUNCH velocity) for shard index j, world units.

    The velocity has to be measured across the interval the shard actually
    leaves on, and the FIRST KEY INTERVAL IS NOT THAT INTERVAL.

    The resampled table keeps a key at the start of the sim span and then keys
    the motion: `GS_b04_00000` has keys at f845, f859, f860, f861 ... and its
    displacement over f845 -> f859 is EXACTLY ZERO, because it has not released
    yet.  Differencing the first two keys -- which the first revision of this
    function did -- therefore returned 0.00 m/s for every shard in the wall, and
    every puff launched on the `EJECT_MIN_MS` floor alone: measured 0.53-1.05
    m/s against a shard field doing 20 m/s, travelling a median of 0.45 m
    instead of several metres.  A debris field that stays at the wall while the
    glass leaves is worse than none, and NOTHING in the mass ledger, the size
    law or the pixel grade would have said a word about it.  It was caught by
    asking the table what speed it thought the glass was doing.

    So: the fastest key interval inside a short window at and after the shard's
    release.  That is its launch, and it is what the render shows.
    """
    fk, kl, _kq = film["keys_of"](j)
    if len(fk) < 2:
        return kl[0], np.zeros(3)
    r = int(fk[0]) if rel is None else int(rel)
    i0 = int(np.searchsorted(fk, r))
    i0 = min(max(i0, 0), len(fk) - 2)
    i1 = min(i0 + window, len(fk) - 1)
    if i1 <= i0:
        return kl[0], np.zeros(3)
    dt = np.diff(clock.world_t(fk[i0:i1 + 1]))
    dx = np.diff(kl[i0:i1 + 1], axis=0)
    ok = dt > 1e-9
    if not ok.any():
        return kl[0], np.zeros(3)
    v = np.where(ok[:, None], dx / np.maximum(dt, 1e-9)[:, None], 0.0)
    return kl[0], v[int(np.argmax(np.linalg.norm(v, axis=1)))]


def build_field(plan, film, clock, f_spall=F_SPALL, seed=20260807,
                n_sites=4200, site_cap=160, verbose=True):
    """Emit puffs.  Returns (puffs, chips, report)."""
    rng = np.random.default_rng(seed)
    bud = budget(plan, f_spall=f_spall)
    idx = {n: i for i, n in enumerate(film["names"])}

    # ---- the emission sites ------------------------------------------------ #
    # A site is a CRACK: a bonded pair of shards.  Its position is the midpoint
    # of the two parents' home origins (they are 20 mm apart in the crush zone,
    # so the midpoint is the crack to within a few mm) and its birth frame is
    # the later of the two releases, because until both parents have let go
    # there is no opening for a flake to leave through.
    sites = []
    E = {}
    for bay, shards in plan["panes"].items():
        for s in shards:
            E[(bay, s["id"])] = s["energy"]
    for bay, rows in plan["bonds"].items():
        for i, j, L in rows:
            na = "GS_b%02d_%05d" % (bay, i)
            nb = "GS_b%02d_%05d" % (bay, j)
            ja, jb = idx.get(na), idx.get(nb)
            if ja is None or jb is None:
                continue
            e = 0.5 * (E[(bay, i)] + E[(bay, j)])
            sites.append((bay, ja, jb, float(L), e))
    if verbose:
        print("[debris] %d bonded cracks are candidate emission sites"
              % len(sites))

    L = np.array([s[3] for s in sites])
    ecr = np.array([s[4] for s in sites])
    crush = ecr >= E_CRUSH

    # crush spall is emitted only from cracks inside the footprint, weighted by
    # crack length; arris spall from EVERY crack, likewise.  Two populations,
    # two weightings, because they are two different physical events.
    w_crush = np.where(crush, L, 0.0)
    w_arris = L.copy()
    w_crush = w_crush / w_crush.sum() if w_crush.sum() > 0 else w_crush
    w_arris = w_arris / w_arris.sum()

    n_crush = int(round(n_sites * 0.55))
    n_arris = n_sites - n_crush
    pick_c = rng.choice(len(sites), size=n_crush, replace=False, p=w_crush)
    pick_a = rng.choice(len(sites), size=n_arris, replace=False, p=w_arris)

    rel = film["release"]
    span = film["span"]
    cache = {}

    def state(j):
        if j not in cache:
            cache[j] = parent_state(film, j, clock, rel=rel[j])
        return cache[j]

    puffs, chips = [], []
    dropped_no_release = 0

    for kind, pick, mass in (("crush", pick_c, bud["crush_spall_kg"]),
                             ("arris", pick_a, bud["arris_spall_kg"])):
        per_site = mass / max(len(pick), 1)
        for si in pick:
            bay, ja, jb, Lb, e = sites[si]
            ra, rb = int(rel[ja]), int(rel[jb])
            fb = max(ra, rb)
            if fb <= span[0]:
                dropped_no_release += 1
                continue
            pa, va = state(ja)
            pb, vb = state(jb)
            p0 = 0.5 * (pa + pb)
            v_par = 0.5 * (va + vb)
            sp = float(np.linalg.norm(v_par))

            # THE SITE'S POPULATION IS COMPLETE ABOVE A FLOOR, NOT SAMPLED
            # ACROSS THE WHOLE LAW.  The first revision drew PUFF_MAX sizes
            # from the full 50 um .. 6 mm law per site and spent 0.00004 kg of
            # a 2.073 kg budget: with dN/dd ~ d^-3, 999 draws in 1,000 are
            # under 200 um and carry no mass at all.  A field built that way is
            # a million invisible specks and no glass.
            #
            # So: pick the floor that puts `site_cap` chips at this site, emit
            # EVERY chip above it, and declare the rest.  Density and size
            # distribution are then correct above the floor -- which is the only
            # regime where either can be seen -- instead of being uniformly
            # 1/1000 too sparse everywhere.
            d_site = _floor_for_count(per_site, site_cap)
            n_here = int(round(_count_above(per_site, d_site)))
            if n_here < PUFF_MIN:
                continue
            allsz = np.sort(draw_sizes(rng, n_here, d_site, D_TOP))

            # SIZE BINS -> PUFFS.  drag_k goes as 1/d, so a puff must be
            # narrow in d or it cannot be rigid.
            edges = np.searchsorted(allsz, np.geomspace(d_site, D_TOP, 5))
            bnds = sorted(set([0] + list(edges) + [len(allsz)]))
            for a, c in zip(bnds[:-1], bnds[1:]):
                if c - a < PUFF_MIN:
                    continue
                dz = allsz[a:c]
                dm = float(np.mean(dz))
                ejf = rng.uniform(*EJECT_FRAC)
                ax = _cone(rng, np.array([1.0, 0.0, 0.0]), EJECT_CONE_DEG)
                v0 = v_par + ax * max(EJECT_MIN_MS, ejf * sp)
                pid = len(puffs)
                puffs.append(dict(
                    id=pid, kind=kind, bay=int(bay), birth=int(fb),
                    p0=p0.copy(), v0=v0, d_mean=dm, k=float(drag_k(dm)),
                    n=int(c - a),
                    spin=float(rng.uniform(*PUFF_SPIN_RADS)),
                    spin_axis=_unit(rng.normal(size=3)),
                    mass=float((RHO_GLASS * DM.SHAPE_FACTOR * dz ** 3).sum())))
                for q, dd in enumerate(dz):
                    chips.append((pid, float(dd),
                                  _ball(rng, PUFF_BALL_M)))
    msz = np.array([c[1] for c in chips]) if chips else np.zeros(0)
    rep = dict(budget=bud, n_sites=len(sites), n_puffs=len(puffs),
               n_chips=len(chips), site_cap=site_cap,
               dropped_sites_never_released=dropped_no_release,
               mass_emitted_kg=float(sum(p["mass"] for p in puffs)),
               d_emitted_mm=dict(
                   p05=float(1000 * np.percentile(msz, 5)) if len(msz) else 0.,
                   p50=float(1000 * np.median(msz)) if len(msz) else 0.,
                   p95=float(1000 * np.percentile(msz, 95)) if len(msz) else 0.,
                   dmin=float(1000 * msz.min()) if len(msz) else 0.))
    rep["mass_emitted_frac_of_budget"] = (
        rep["mass_emitted_kg"] / max(bud["free_kg"], 1e-12))
    if verbose:
        print("[debris] %d puffs, %d chips, %.4f kg emitted of a %.4f kg "
              "budget (%.1f %%); chip size p05/p50/p95 = %.2f/%.2f/%.2f mm"
              % (len(puffs), len(chips), rep["mass_emitted_kg"],
                 bud["free_kg"], 100 * rep["mass_emitted_frac_of_budget"],
                 rep["d_emitted_mm"]["p05"], rep["d_emitted_mm"]["p50"],
                 rep["d_emitted_mm"]["p95"]))
    return puffs, chips, rep


def _count_above(mass_kg, d, d_top=D_TOP, b=SCHUHMANN_B):
    """How many chips of at least `d` a mass `mass_kg` of the law contains.

    Closed form, the same K as `law_report`, so the emitter and the report
    cannot drift apart.
    """
    K = mass_kg * b / (RHO_GLASS * DM.SHAPE_FACTOR * d_top ** b)
    p = b - 3.0
    return K * (d_top ** p - d ** p) / p


def _floor_for_count(mass_kg, n, d_top=D_TOP, b=SCHUHMANN_B):
    """Invert `_count_above`: the size floor that yields n chips."""
    K = mass_kg * b / (RHO_GLASS * DM.SHAPE_FACTOR * d_top ** b)
    p = b - 3.0
    v = d_top ** p - n * p / K
    return float(max(D_BOT, v ** (1.0 / p)))


def _slerp1(a, b, u):
    """Slerp one quaternion pair.  Reference only -- the shipped curves are
    LINEAR by requirement (`apply_breach.prove_curves`), and this exists to
    measure how far from slerp that linearity puts them."""
    d = float(a @ b)
    if d < 0.0:
        b, d = -b, -d
    if d > 1.0 - 1e-10:
        q = (1 - u) * a + u * b
        return q / max(float(np.linalg.norm(q)), 1e-15)
    th = math.acos(d)
    s = math.sin(th)
    return (math.sin((1 - u) * th) * a + math.sin(u * th) * b) / s


def _unit(v):
    v = np.asarray(v, float)
    return v / max(float(np.linalg.norm(v)), 1e-12)


def _cone(rng, axis, half_deg):
    axis = _unit(axis)
    c = math.cos(math.radians(half_deg))
    z = rng.uniform(c, 1.0)
    ph = rng.uniform(0, 2 * math.pi)
    s = math.sqrt(max(0.0, 1.0 - z * z))
    t = _unit(np.cross(axis, [0.0, 0.0, 1.0]
                       if abs(axis[2]) < 0.9 else [1.0, 0.0, 0.0]))
    b = np.cross(axis, t)
    return _unit(z * axis + s * (math.cos(ph) * t + math.sin(ph) * b))


def _ball(rng, r):
    while True:
        q = rng.uniform(-1, 1, 3)
        if float(q @ q) <= 1.0:
            return q * r


# --------------------------------------------------------------------------- #
#  6.  TRAJECTORIES AND THE PIXEL GRADE.
# --------------------------------------------------------------------------- #

MAX_KEY_ANGLE = 0.30               # rad of puff spin between two keys, TARGET
# ...and the hard bound the controls gate on.  The target cannot always be met:
# key frames are INTEGERS, so no scheduler can put two keys closer than one film
# frame, and at the ramp's 15.4 % a 14 rad/s spin turns 0.09 rad in one frame
# (0.58 rad once the ramp exits, which is why the spin stops at landing).  What
# actually matters is that component-wise lerp stays indistinguishable from
# slerp, and it does: measured 1.5e-4 rad at a 0.337 rad gap.  pi/4 is where
# that starts to be untrue, and 2*pi is where the arc reverses.
KEY_ANGLE_HARD = math.pi / 4.0


def integrate(puffs, clock, keys_per_puff=26, dur_s=1.10, total=2978,
              max_angle=MAX_KEY_ANGLE):
    """Key frames and world transforms for every puff.

    TRANSLATION wants LOG-spaced keys.  The whole path is over in the first
    tenth of a second -- a flake with k = 0.6/m at 20 m/s has lost half its
    speed in 60 mm -- so uniform keys would spend twenty of twenty-six of them
    on a chip lying still on the floor.

    ROTATION WANTS SOMETHING ELSE ENTIRELY, and getting this wrong is silent.
    Blender interpolates the four quaternion F-curves COMPONENT-WISE, not by
    slerp, and normalises on evaluation.  Over a small angle that is
    indistinguishable from slerp; over a large one it is not merely inaccurate,
    it is BACKWARDS.  A puff spinning at 14 rad/s with a 0.4 s gap between keys
    turns 5.6 rad, the component-wise path takes the short way round --
    5.6 - 2*pi = -0.68 rad -- and the puff renders rotating slowly the WRONG
    WAY.  Tumble is most of what makes a field of flakes read as glass, so this
    would have quietly cost the pass its point.

    So the key times are the UNION of the log-spaced translation times and a set
    spaced so no interval turns more than `max_angle`.  Both channels are then
    evaluated on that union.  The quaternions are also carried into a single
    hemisphere (dot with the previous key >= 0), because a sign flip between two
    keys is the same failure a second time.
    """
    for p in puffs:
        t = np.concatenate([[0.0],
                            np.geomspace(0.004, dur_s, keys_per_puff - 1)])
        spin = max(float(p["spin"]), 1e-9)
        n_rot = int(math.ceil(spin * dur_s / max_angle))
        if n_rot > 1:
            t = np.union1d(t, np.linspace(0.0, dur_s, n_rot + 1))
        f = clock.frame_at_world_t(clock.world_t(p["birth"]) + t)
        f = np.clip(np.round(f).astype(int), 1, total)
        # collapse duplicate frames (the ramp is 15.4 %, so early keys collide);
        # keep the LAST t for each frame so the interval a key represents is not
        # systematically short
        u, ui = np.unique(f[::-1], return_index=True)
        t = t[::-1][ui]
        P, t_land = fly(p["p0"], p["v0"], p["k"], t)
        p["kf"] = u
        p["kl"] = P
        p["t_land"] = t_land
        # A FLAKE THAT HAS LANDED IS NOT SPINNING.  Clamping the spin at the
        # landing time is physically obvious and it also removes the only place
        # the key-angle bound could not be met: the flight is over inside the
        # 15.4 % ramp, where a film frame is 0.0064 world seconds, but the keys
        # run on to 1.10 s and cross the ramp exit, where a film frame is
        # 0.0417 s and a 14 rad/s spin turns 0.58 rad in ONE FRAME -- finer than
        # which no keying can go.
        ang = spin * np.minimum(t, t_land)
        ax = p["spin_axis"]
        Q = np.c_[np.cos(0.5 * ang), np.sin(0.5 * ang)[:, None] * ax[None, :]]
        s = np.sign(np.einsum("ij,ij->i", Q[:-1], Q[1:]))
        s[s == 0] = 1.0
        Q[1:] *= np.cumprod(s)[:, None]
        p["kq"] = Q
        p["max_key_angle"] = (float(np.max(np.abs(np.diff(ang))))
                              if len(ang) > 1 else 0.0)
    return puffs


def camera_track(path=None):
    """The film's per-frame camera, from `sim/dump_camera_track.py`.

    NOT `camera_polyline()`.  The hero-shard grade in apply_breach uses the beat
    sheet's coarse key polyline, which is right for "did this shard ever come
    near the camera" and wrong here: a chip's on-screen size needs the camera's
    position AT THE FRAME THE CHIP IS AT and the focal length it had there,
    and beat 3 runs the lens from 28.4 mm down to 21.0 mm across the transit.
    R2-706 is explicit that every pixel figure goes through this file.
    """
    path = path or os.path.join(OUT, "oner_camera_track.json")
    rows = np.array(json.load(open(path)), float)
    return dict(frame=rows[:, 0].astype(int), loc=rows[:, 1:4],
                quat=rows[:, 4:8], lens=rows[:, 8])


def _fwd(q):
    """Blender camera forward (-Z of its own frame) from (w, x, y, z)."""
    w, x, y, z = q.T
    return np.c_[-2 * (x * z + y * w), -2 * (y * z - x * w),
                 -(1 - 2 * (x * x + y * y))]


def peak_px(puffs, chips, trk, px_w=PX_W, sensor=SENSOR_MM):
    """Largest on-screen size, in pixels at 4K, each chip ever reaches.

    Measured at the chip's OWN frames, against the camera's own position, lens
    and facing at each of them.  A chip behind the camera scores zero: the
    grade must not spend its budget on glass that is out of shot, and half this
    field is emitted from a wall the camera goes through.
    """
    F, L, Q, LEN = trk["frame"], trk["loc"], trk["quat"], trk["lens"]
    best = np.zeros(len(puffs))
    dmin = np.full(len(puffs), 1e9)
    for i, p in enumerate(puffs):
        kf = np.clip(p["kf"], F[0], F[-1]) - F[0]
        rel = p["kl"] - L[kf]
        d = np.linalg.norm(rel, axis=1)
        ahead = np.einsum("ij,ij->i", rel, _fwd(Q[kf])) > 0.0
        d = np.where(ahead, np.maximum(d, 0.05), 1e9)
        sc = px_w * LEN[kf] / (sensor * d)
        best[i] = sc.max()
        dmin[i] = d.min()
    cid = np.array([c[0] for c in chips])
    csz = np.array([c[1] for c in chips])
    return csz * best[cid], dmin[cid]


def select(px, budget_chips=260000, px_min=PX_MIN):
    """Which chips get built.  Two gates, both stated in pixels.

    1.  a chip that never reaches `px_min` at 4K is not built.  Below ~1.6 px
        a chip cannot be told from shot noise once the beat's own 100-200 px
        of motion smear is applied, and building it costs the same as one that
        can be seen.
    2.  what survives is capped at `budget_chips`, largest-on-screen first, so
        the trade is spent where it registers.

    Both gates report what they dropped, in mass and in count.  A grade that
    only reports what it kept is the one that hides the field going thin.
    """
    keep = px >= px_min
    if keep.sum() > budget_chips:
        thr = np.partition(px[keep], keep.sum() - budget_chips)[
            keep.sum() - budget_chips]
        keep &= px >= thr
    return keep


# --------------------------------------------------------------------------- #
#  7.  SAVE / LOAD
# --------------------------------------------------------------------------- #

def save(puffs, chips, keep, report, path=None):
    path = path or os.path.join(OUT, "breach_debris.npz")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ck = np.array([c[0] for c in chips])[keep]
    cs = np.array([c[1] for c in chips])[keep]
    co = np.array([c[2] for c in chips])[keep]
    live = np.unique(ck)
    remap = -np.ones(len(puffs), int)
    remap[live] = np.arange(len(live))
    # THE PER-PUFF MASS MUST BE THE MASS THAT SURVIVED THE GRADE, not the mass
    # the puff was emitted with.  `p["mass"]` is the latter, and writing it here
    # made `apply_breach.build_debris` report 1.002 kg for a field the grade had
    # cut to 0.884 -- a 13 % over-statement of the only number in this pass that
    # is supposed to be conserved, printed by the applier into every build
    # report.  Recomputed from the kept chips.
    kept_mass = np.zeros(len(puffs))
    np.add.at(kept_mass, ck, RHO_GLASS * DM.SHAPE_FACTOR * cs ** 3)
    kf, kl, kq, cnt, meta = [], [], [], [], []
    for i in live:
        p = puffs[i]
        kf.append(p["kf"])
        kl.append(p["kl"])
        kq.append(p["kq"])
        cnt.append(len(p["kf"]))
        meta.append((p["birth"], p["bay"], 0 if p["kind"] == "crush" else 1,
                     p["d_mean"], p["k"], kept_mass[i]))
    np.savez_compressed(
        path,
        key_count=np.array(cnt, np.int32),
        key_frame=np.concatenate(kf).astype(np.int32),
        key_loc=np.concatenate(kl).astype(np.float64),
        key_quat=np.concatenate(kq).astype(np.float64),
        puff_meta=np.array(meta, np.float64),
        chip_puff=remap[ck].astype(np.int32),
        chip_size=cs.astype(np.float64),
        chip_off=co.astype(np.float64))
    with open(path.replace(".npz", ".json"), "w") as fh:
        json.dump(report, fh, indent=1, default=float)
    return path


def load(path=None):
    path = path or os.path.join(OUT, "breach_debris.npz")
    z = np.load(path, allow_pickle=False)
    cnt = z["key_count"].astype(int)
    off = np.concatenate([[0], np.cumsum(cnt)])
    # MATERIALISE THE ARRAYS ONCE.  An NpzFile is lazy: `z["key_frame"]`
    # decompresses the whole 14 MB member on EVERY access, so closing the
    # subscript over `z` -- which the first revision did -- made `keys_of`
    # cost a full decompression per puff and the applier's 11,551 calls an
    # afternoon.  `resample.read_film` has the same shape and does the same
    # thing; it gets away with it because the applier calls `keys_of` once per
    # shard on arrays it has already touched.
    kf, kl, kq = z["key_frame"], z["key_loc"], z["key_quat"]
    return dict(n_puffs=len(cnt), key_count=cnt,
                key_frame=kf, key_loc=kl, key_quat=kq,
                puff_meta=z["puff_meta"],
                chip_puff=z["chip_puff"], chip_size=z["chip_size"],
                chip_off=z["chip_off"],
                keys_of=lambda j: (kf[off[j]:off[j + 1]],
                                   kl[off[j]:off[j + 1]],
                                   kq[off[j]:off[j + 1]]))


# --------------------------------------------------------------------------- #
#  8.  CONTROLS.
# --------------------------------------------------------------------------- #

def selftest():
    bad = []

    def check(name, cond, detail=""):
        print("   %-52s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            bad.append(name)

    rng = np.random.default_rng(7)

    # --- the size law carries the mass it says it carries ------------------- #
    # THE COUNT IS THE WELL-CONDITIONED TEST AND THE MASS IS NOT.  With
    # dN/dd ~ d^-3 over three decades, half the mass sits in the top octave and
    # a 400k sample puts ~80 chips there, so a mass comparison is a 10 %
    # Monte-Carlo measurement dressed up as an identity.  The first revision of
    # this control failed at 12 % and the sampler was correct.  So: compare the
    # CUMULATIVE COUNT at fixed sizes, which every sample contributes to.
    n = 2000000
    d = draw_sizes(rng, n)
    lr = law_report(1.0)
    worst = 0.0
    for d0 in (1e-4, 2e-4, 5e-4, 1e-3):
        emp = float((d >= d0).mean())
        exact = law_report(1.0, d0, D_TOP)["total_count"] / lr["total_count"]
        worst = max(worst, abs(emp / exact - 1.0))
    check("size law: empirical CDF matches the closed form", worst < 0.05,
          "worst relative error %.3f over four cut sizes" % worst)
    check("size law: sampled sizes stay inside [D_BOT, D_TOP]",
          d.min() >= D_BOT * 0.999 and d.max() <= D_TOP * 1.001)
    # NEGATIVE CONTROL: b = 3 -- the mosaic generator's own signature, fitted at
    # 3.68 on the crushed-zone shards -- must starve the fine decades.  That is
    # the whole reason the shard plan has no lower tail to extrapolate.
    fine3 = law_report(1.0, b=3.0)["bands"][0]["mass_kg"]
    fine1 = law_report(1.0, b=1.0)["bands"][0]["mass_kg"]
    check("NEGATIVE: a b=3 law starves the fine decades", fine1 / fine3 > 100,
          "b=1 puts %.1fx more mass in the first decade (%.4f vs %.6f kg)"
          % (fine1 / fine3, fine1, fine3))

    # --- drag: the 1/d law and its consequence ------------------------------ #
    k6, k1 = drag_k(0.006), drag_k(0.001)
    check("drag_k goes as 1/d", abs(k6 * 0.006 - k1 * 0.001) < 1e-12)
    check("a 6 mm flake coasts further than a 1 mm flake",
          1.0 / k6 > 3.0 * (1.0 / k1),
          "%.2f m vs %.2f m" % (1.0 / k6, 1.0 / k1))

    # --- the integrator ----------------------------------------------------- #
    # POSITIVE CONTROL: with drag off, fly() must reproduce the closed-form
    # parabola to machine-ish precision.  This is the control that would have
    # caught an RK4 written with the wrong position update.
    t = np.linspace(0, 0.4, 40)
    P, _tl = fly([0, 0, 10.0], [5.0, 0, 0], 0.0, t, z_floor=-100.0)
    ex = np.c_[5.0 * t, 0 * t, 10.0 - 0.5 * G * t ** 2]
    err = float(np.abs(P - ex).max())
    check("no-drag integration IS the parabola", err < 2e-4, "max %.2e m" % err)

    # POSITIVE CONTROL: with gravity off, 1-D quadratic drag has a closed form
    # v = v0/(1+k v0 t), x = ln(1+k v0 t)/k.  GRAVITY MUST BE OFF FOR THIS, and
    # the first revision left it on and compared x only -- which is wrong,
    # because |v| couples the axes: the falling component inflates the drag on
    # the horizontal one.  It failed at 15.6 mm and the integrator was right.
    kk, v0 = 0.6, 20.0
    P2, _tl2 = fly([0, 0, 0], [v0, 0, 0], kk, t, z_floor=-100.0, g_z=0.0)
    ex2 = np.log1p(kk * v0 * t) / kk
    err2 = float(np.abs(P2[:, 0] - ex2).max())
    check("quadratic drag IS ln(1+k v0 t)/k, gravity off", err2 < 1e-6,
          "max %.2e m" % err2)

    # --- the quaternion keying, which failed silently once ------------------ #
    # THE QUANTITY THAT MATTERS IS THE RELATIVE ROTATION BETWEEN TWO KEYS, not
    # the absolute angle at either of them.  The first version of this control
    # compared absolute angles extracted with atan2(|v|, |w|), which folds into
    # [0, pi]; a puff that turns 15 rad over its flight has keys well past that,
    # so the check reported a 0.128 rad error that was entirely its own wrapping.
    # It also declared a 5.6 rad gap a failure when 5.6 rad is fine -- the real
    # cliff is at 2*pi, where the shortest quaternion arc reverses.
    import breachlib as _BL
    _ck = _BL.Clock()
    # 3.0 m up, or they land on frame one and the control is vacuous -- which
    # is exactly what the first run of it did, reporting a 0.000 rad worst gap
    # over three spin rates and passing.  A control that cannot fail is not one.
    fake = [dict(p0=np.array([15.0, 0.0, 3.0]), v0=np.array([8.0, 0, 2.0]),
                 k=0.6, birth=870, spin=sp,
                 spin_axis=_unit(np.array([0.3, 1.0, -0.2])))
            for sp in (2.0, 8.0, 14.0)]
    integrate(fake, _ck)
    worst_q, worst_gap = 0.0, 0.0
    for p in fake:
        Q = p["kq"]
        for i in range(len(Q) - 1):
            a, b = Q[i], Q[i + 1]
            rel = abs(2.0 * math.acos(min(1.0, abs(float(a @ b)))))
            worst_gap = max(worst_gap, rel)
            # what Blender does: lerp the four channels, normalise.  Compare it
            # against slerp at the same parameter.
            for u in (0.25, 0.5, 0.75):
                nl = (1 - u) * a + u * b
                nl = nl / max(float(np.linalg.norm(nl)), 1e-15)
                sl = _slerp1(a, b, u)
                worst_q = max(worst_q,
                              2.0 * math.acos(min(1.0, abs(float(nl @ sl)))))
    check("component-wise lerp of the keys IS slerp to 1e-3 rad",
          worst_q < 1e-3,
          "worst %.2e rad, worst key gap %.3f rad, over spins 2/8/14 rad/s"
          % (worst_q, worst_gap))
    check("no key interval turns more than KEY_ANGLE_HARD",
          all(p["max_key_angle"] <= KEY_ANGLE_HARD for p in fake),
          "worst %.4f rad; target %.2f, hard bound %.3f (one film frame is the "
          "floor on key spacing)"
          % (max(p["max_key_angle"] for p in fake), MAX_KEY_ANGLE,
             KEY_ANGLE_HARD))
    # NEGATIVE CONTROL: the genuine failure mode is a gap past 2*pi, where the
    # shortest quaternion arc goes the OTHER WAY and the puff renders spinning
    # backwards.  7.0 rad must be caught.
    ax = np.array([0.0, 0.0, 1.0])
    qa = np.array([1.0, 0.0, 0.0, 0.0])
    qb = np.r_[math.cos(3.5), math.sin(3.5) * ax]
    nl = 0.5 * (qa + qb)
    nl /= np.linalg.norm(nl)
    # SIGNED about the spin axis: an unsigned atan2(|v|, w) cannot express the
    # failure, which is that the rotation reverses.
    got = 2.0 * math.atan2(float(nl[1:] @ ax), float(nl[0]))
    check("NEGATIVE: a 7.0 rad key gap interpolates BACKWARDS", got < 0.0,
          "midpoint reads %+.3f rad where the truth is +3.500" % got)

    _lp, _lt = fly([0, 0, 1.0], [0, 0, 0], 0.6, [0.5, 5.0, 60.0])
    check("a flake lands and stays landed",
          abs(_lp[-1][2] - _lp[-2][2]) < 1e-9 and _lt < 5.0,
          "landed at t = %.3f s" % _lt)

    # --- THE LAUNCH VELOCITY, on the shipped table -------------------------- #
    # The control that would have caught a field of debris standing still while
    # the glass left at 20 m/s, and the negative control is the bug itself.
    import resample as _RS
    _film = _RS.read_film(os.path.join(OUT, "breach_film.npz"))
    _rel = _film["release"]
    idx = [i for i, n in enumerate(_film["names"])
           if n.startswith("GS_b04_") or n.startswith("GS_b05_")][:60]
    good = np.array([np.linalg.norm(parent_state(_film, j, _ck, rel=_rel[j])[1])
                     for j in idx])
    check("struck-bay shards launch at 5-40 m/s on the shipped table",
          5.0 < float(np.median(good)) < 40.0,
          "p05 %.1f p50 %.1f p95 %.1f m/s over %d shards"
          % (*np.percentile(good, [5, 50, 95]), len(idx)))
    # NEGATIVE CONTROL: the first-key-interval measure -- what this function
    # used to do -- must read ~zero, or the fix is not a fix.
    # NOT `bad` -- that name is the failure accumulator this whole selftest
    # reports on, and shadowing it with a numpy array made the final verdict
    # line raise instead of print.  Caught on the run that added this control.
    first_iv = []
    for j in idx:
        fk, kl, _q = _film["keys_of"](j)
        dt = float(_ck.world_t(fk[1]) - _ck.world_t(fk[0]))
        first_iv.append(np.linalg.norm(kl[1] - kl[0]) / max(dt, 1e-9))
    first_iv = np.array(first_iv)
    check("NEGATIVE: differencing the FIRST two keys reads ~zero",
          float(np.median(first_iv)) < 0.05
          and float(np.median(good)) > 100 * max(float(np.median(first_iv)),
                                                 1e-6),
          "first-interval p50 %.4f m/s against a launch of %.1f m/s"
          % (float(np.median(first_iv)), float(np.median(good))))

    # --- the ledger, on the real plan --------------------------------------- #
    plan = FR.load()
    led = ledger(plan)
    check("ledger: the kerf is 5-40 kg (it is a real, large deletion)",
          5.0 < led["kerf_kg"] < 40.0, "%.2f kg" % led["kerf_kg"])
    check("ledger: built mass < cell mass, by exactly kerf + chamfer",
          abs((led["mass_cells_kg"] - led["mass_built_kg"])
              - (led["kerf_kg"] + led["chamfer_kg"])) < 1e-6)
    bud = budget(plan, led)
    check("BUDGET IS UNDER THE LEDGER CEILING", bud["PASS"],
          "%.3f kg free vs %.3f kg deleted (%.1f %%)"
          % (bud["free_kg"], bud["ceiling_kg"], 100 * bud["frac_of_ceiling"]))
    check("the field is one part in several hundred of the wall",
          bud["free_frac_of_wall"] < 0.005,
          "%.5f of 2,255 kg" % bud["free_frac_of_wall"])

    # NEGATIVE CONTROL: the ceiling test must be capable of failing.
    big = budget(plan, led, f_spall=2.0)
    check("NEGATIVE: f_spall = 2.0 breaks the ceiling test", not big["PASS"],
          "%.2f kg free vs %.2f kg ceiling"
          % (big["free_kg"], big["ceiling_kg"]))
    # AND THE FACT THAT FALLS OUT OF IT, which is worth more than the control:
    # even f_spall = 1.0 -- every gram of the outer ply inside the crushed
    # footprint leaving as free fines, which is physically the most that can
    # happen -- is still comfortably UNDER the ceiling.  The kerf deletion is
    # larger than the entire crushable ply.  That is how large a numerical
    # artefact 0.4 mm is, and it is why the kerf must never be spent as a
    # budget.
    mx = budget(plan, led, f_spall=1.0)
    check("the physical maximum is still under the ceiling", mx["PASS"],
          "f_spall=1.0 -> %.2f kg, %.0f %% of the %.2f kg deleted"
          % (mx["free_kg"], 100 * mx["frac_of_ceiling"], mx["ceiling_kg"]))

    print("   STAGE RESULT: debris %s"
          % ("PASS" if not bad else "FAIL " + ",".join(bad)))
    return 1 if bad else 0


# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true",
                    help="the ledger, the budget and the size law, no build")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--out", default=os.path.join(OUT, "breach_debris.npz"))
    ap.add_argument("--film", default=os.path.join(OUT, "breach_film.npz"))
    ap.add_argument("--shards", default=os.path.join(OUT, "fracture_wall.npz"))
    ap.add_argument("--f-spall", type=float, default=F_SPALL)
    ap.add_argument("--sites", type=int, default=4200)
    ap.add_argument("--site-cap", type=int, default=160,
                    help="chips emitted per site; sets the per-site size floor")
    ap.add_argument("--chips", type=int, default=260000)
    ap.add_argument("--px-min", type=float, default=PX_MIN)
    ap.add_argument("--seed", type=int, default=20260807)
    a = ap.parse_args()

    if a.selftest:
        sys.exit(selftest())

    plan = FR.load(a.shards)
    if a.report:
        led = ledger(plan)
        bud = budget(plan, led, a.f_spall)
        print(json.dumps(dict(ledger=led, budget=bud,
                              law=law_report(bud["free_kg"]),
                              powder=powder_report(plan,
                                                   bud["crush_spall_kg"])),
                         indent=1, default=float))
        return

    if not a.build:
        ap.error("one of --selftest / --report / --build")

    import breachlib as BL
    import resample as RS
    clock = BL.Clock()
    film = RS.read_film(a.film)
    puffs, chips, rep = build_field(plan, film, clock, a.f_spall, a.seed,
                                    a.sites, a.site_cap)
    integrate(puffs, clock)
    trk = camera_track()
    px, dist = peak_px(puffs, chips, trk)
    keep = select(px, a.chips, a.px_min)
    sz = np.array([c[1] for c in chips])
    mm = RHO_GLASS * DM.SHAPE_FACTOR * sz ** 3
    rep["grade"] = dict(
        px_min=a.px_min, budget_chips=a.chips,
        chips_total=int(len(chips)), chips_built=int(keep.sum()),
        mass_total_kg=float(mm.sum()), mass_built_kg=float(mm[keep].sum()),
        px_p50_built=float(np.median(px[keep])) if keep.any() else 0.0,
        px_p95_built=float(np.percentile(px[keep], 95)) if keep.any() else 0.0,
        px_max=float(px.max()),
        closest_approach_m_p05=float(np.percentile(dist[keep], 5))
        if keep.any() else 0.0,
        puffs_built=int(len(np.unique(np.array([c[0] for c in chips])[keep]))))
    rep["powder"] = powder_report(plan, rep["budget"]["crush_spall_kg"])
    rep["law"] = law_report(rep["budget"]["free_kg"])
    out = save(puffs, chips, keep, rep, a.out)
    print(json.dumps(rep["grade"], indent=1, default=float))
    print("[debris] wrote %s (%.2f MB)" % (out, os.path.getsize(out) / 1e6))
    print("STAGE RESULT: debris_build PASS")


if __name__ == "__main__":
    main()
