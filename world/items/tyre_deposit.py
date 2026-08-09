#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tyre_deposit.py — THE RUBBER THE CAR ACTUALLY LAYS DOWN, as a shader node group.

    build + save a gate scene:
        /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
            -P world/items/tyre_deposit.py -- --test-scene --substrate concrete \
            --save world/items/tyre_deposit_test.blend

    the gate (renders and MEASURES, ~20 renders, all local, all tiny):
        /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
            -P world/items/tyre_deposit.py -- --gate

    selftest (no bpy needed):
        python3 world/items/tyre_deposit.py --selftest

NOTHING HERE IS WIRED INTO THE FILM. This module owns four node groups and
three replica materials and touches no other module. `world/build_surface.py`,
`FloorPolished` and `TurntableTop` are read, never written.

===============================================================================
1.  WHAT THIS IS
===============================================================================
A **deposit field** — world-space, derived from `work/r2_1211_rubber_tracks.json`
and `telemetry/telemetry.csv`, never painted by eye — and **three
substrate-specific applications** of it: rough concrete, brushed metal, polished
floor. The field is `TDP_DepositField`, a shader node group whose only
coordinate input is a WORLD position; the applications are three more node
groups that take a substrate's channels in and hand them back modified.

The field has two components.

**(a) THE LAUNCH PATCH.** Two patches, one per rear wheel, world
x −1.80000 → −1.55840, y = ±0.79750, contact patch 251.1 mm wide
(|y| 0.672 … 0.923), on the turntable deck at z = 0.340. The along-track profile
is the per-frame `deposit_norm` of `wheels.RL/RR`, decade

    1.000  0.954  0.794  0.646  0.507  0.381  0.267  0.168  0.086  0.027

and it TERMINATES at 2.7 % of peak — the tyre hooks up, it does not fade. Both
edges (the leading one where the tyre stood, the trailing one where it hooked
up) are authored at **12 mm**, the floor of the resolvable band: as hard as the
camera can see and no harder.

**IT IS TIME-GATED.** The patch does not exist before film frame 817 and grows
along the mark over frames 818–827, driven by a `Front X` value that is
keyframed from the wheel's own per-frame world x. A statically painted deck mark
would sit under a PARKED CAR for the ~473 frames of beat 1 that see that ground
at 27–43° — a worse defect than the one being fixed. See §6.

**(b) THE TRACTIVE-SLIP FILM.** `carrig` makes rolling contact exact by
construction; that is a kinematic simplification, not physics. A driven tyre
transmitting tractive force runs a non-zero longitudinal slip ratio, and the
telemetry carries the quantity it depends on. Derivation, all of it from real
columns:

    mu_used(t) = accel_long_ms2(t) / (2 * normal_load_norm(t) * g)

`normal_load_norm` is this wheel's share of the car's weight, from the tracks
JSON (static rear split plus longitudinal transfer); the 2 is the two driven
wheels. Over x = 15 → 49 that is **mu_used = 1.6968 … 1.7023, p50 1.7004** —
flat, because `accel_long_ms2` is 10.659 … 10.699 across the whole span.

Slip ratio is proportional to the tractive force in the linear region,
kappa = mu_used / (C_kappa/Fz), so the SHAPE is mu_used and there is one scale
constant. It is set by the brief's target — 1 m of tyre surface slid over
x = 15 … 49 — and then CHECKED against the physics:

    integral of mu_used ds over x = 15..49        =  57.4657 m
    kappa = mu_used * (1.0 / 57.4657)             =  mu_used * 0.0174017
    => kappa over x = 15..49                      =  0.02953 … 0.02962
    => slid over x = 15..49                       =  1.00000 m   (by construction)
    => slid over the whole straight drive-out     =  1.84825 m   (x −1.558 … 62.04)

**2.95 % slip lands inside the 2–8 % band the brief names, so the calibration is
self-consistent.** The implied C_kappa/Fz is 1.7004/0.02959 = **57.5** measured
against the car's WEIGHT — twice the 15–30 a slick actually has. That is the
expected factor: the denominator omits aerodynamic downforce, and at 16–31 m/s
this car's real rear normal load is of order 2× its static share, which puts the
true slip stiffness at **28.8** — the top of the textbook range. The two ends of
the derivation meet.

    THE AREAL RATIO IS 1/460, NOT 1/140 — the brief's arithmetic is wrong here.
    Launch: 3.290344 m of slid surface over 0.2416 x 0.2511 m = 0.060664 m²
            => 54.237 m/m² mean, and 0.22144 m over the first 7.197 mm
            => 122.534 m/m² PEAK.
    Film:   1.0 m over 33.7894 x 0.2511 m = 8.4845 m² => 0.11786 m/m².
    ratio = 0.11786 / 54.237  = 1/460.2   against the launch's MEAN
          = 0.11786 / 122.534 = 1/1039.6  against the launch's PEAK
    The brief's 1/140 is 34 m / 0.2416 m, the LENGTH dilution, with the 0.30
    mass factor dropped. Its own two sentences ("about 30 % of the launch's
    3.29 m" and "roughly 1/140 of the areal density") disagree by 3.3x.

===============================================================================
2.  THE THING THAT MAKES 1/460 AND "IT MUST READ" COMPATIBLE
===============================================================================
Under any single monotone opacity law, a film at 1/460 of a mark's areal density
either leaves the mark invisible or leaves the film invisible. That is the real
tension in this block and it is why the apron paint has never worked.

**Rubber does two different things at two different scales, and they saturate
1000x apart.** One transferred film thickness, two laws:

    thickness(D) = D * LAUNCH_PEAK_AREAL * TRANSFER_M_PER_M

with `TRANSFER_M_PER_M` = 9.0e-8 m of film per metre of tyre surface slid per m²
(Archard on rubber/concrete at ~3 bar contact pressure). So

    the launch patch, D = 1        -> 11.0 um of rubber
    the tractive film, D = 9.6e-4  -> 10.6 nm of rubber

    OPTICAL (albedo).  Absorption in carbon-black rubber gives OD ~ 1 at
    TAU_OPTICAL_M = 3.1 um.  11 um is opaque; 10.6 nm is nothing.
    WETTING (roughness / specular / coat / metallic).  Surface energy, and the
    roughness a light ray sees, change at MONOLAYER coverage:
    TAU_WET_M = 7.6 nm, about twenty-five molecular layers.

    coverage = 1 - exp(-D / 0.28110)      launch peak 0.9716, film 0.00341
    wetting  = 1 - exp(-D / 0.00068927)   launch peak 1.0000, film 0.7595

So the launch patch is a black mark AND the tractive film is a 76 %-wetted,
zero-pigment gloss change — from one derived density field, with no art fudge.
**And that is what a fresh rubbered-in acceleration zone looks like in life: not
a stain, a satin band that goes dark at grazing.** It is also exactly the
channel R2-1213 found missing: `M_Surf_Concrete`'s Specular IOR Level is flat
0.32 and the existing mark never touches it.

===============================================================================
3.  THE OCTAVE LAW
===============================================================================
Every structure this module authors lives in **12 mm … 300 mm**, inside the
resolvable band on every relevant surface at BOTH 4K and 720p (staging doc's
band table). Below ~2.4 mm is below the band everywhere — material only.

EVERY relief amplitude comes from `K.relief_amplitude_for(m, wavelength_m)`.
There is not one typed millimetre in this file; `selftest [4]` greps its own
source for `distance=` on a bump and fails if it finds one. `--gate` prints the
`relief_budget` table for every stage, with its band verdict.

The two `M_Surf_Concrete` stages this module MODULATES rather than authors are
measured, not guessed: `build_surface.py:2887-2888` is
`bump(micro, strength=0.45, distance=0.0006)` and
`bump(h, strength=1.0, distance=0.0030)`, which at the staging doc's stated
2.29 mm and 24.11 mm wavelengths reproduce its reported m = 3.15 and 3.29 to
three digits. The 2.29 mm stage is BELOW the band on every surface and carries
m = 3.15; suppressing it is a move toward the law, not away from it.

===============================================================================
4.  THE THREE APPLICATIONS
===============================================================================
**ROUGH CONCRETE — `M_Surf_Concrete`, the access-road apron, PRIORITY ONE.**
It is the only one of the three a material fix can be judged on: frames 981
(44.1° grazing, 16.4 % coverage), 973, 965, 1030. Drop-in replacement for
`build_surface.py:2835-2841` + `:2884`, whose three measured defects are all
fixed here:

    (a) painted at |y| = 0.72, tyres run at |y| = 0.79750  -> re-based to 0.79750
    (b) 200 mm core against a 251.1 mm contact patch       -> 251.1 mm
    (c) -5.73 % at its strongest, no specular, no relief   -> §2's gloss channel,
        Specular IOR Level 0.32 -> 0.52, and a relief contribution that REDUCES
        the aggregate because rubber FILLS texture, it does not add to it.

    And a fourth the staging doc does not name: the existing paint falls
    LINEARLY from full strength at x = 15 to zero at x = 49. The derived
    tractive slip over that span is FLAT to 0.3 % (kappa 0.02953 … 0.02962).
    There is no falloff to author. A linear ramp there is not weak, it is
    the wrong shape.

**BRUSHED METAL — `TurntableTop`, metallic 0.86, roughness 0.335–0.455.**
Where the launch patch actually lands. Rubber on metal is a metallic ->
dielectric transition plus a roughness rise, and it kills the anisotropic brush
sheen: Metallic 0.86 -> 0.052, Roughness -> 0.68, Base Color barely touched
(mixed 0.35 * coverage toward a near-neutral 0.0385). Time-gated; see §6.

**POLISHED FLOOR — `FloorPolished`, base ramp linear 0.030–0.068.**
THE TRAP: the apron's rubber pigment is linear 0.042, BRIGHTER than the darker
half of this floor's own base colour, so a dark albedo MIX would LIGHTEN it.
This application never mixes toward a pigment; the albedo term is a
MULTIPLICATIVE dim, `base * (1 - 0.10 * coverage)`, which is near-neutral and
cannot lighten anything for any base colour. The read is roughness
(0.055–0.155 -> 0.42), coat weight (0.45 -> 0.171, capped at a 62 % suppression)
and coat roughness (0.045 -> 0.30). The cap and the coat-roughness RISE are the
crushed-black guard: R2-082 wants 0.0000 % pure black, those pixels are held off
zero by specular return, and a rougher coat spreads that return instead of
removing it. `--gate` measures pure black on both arms and refuses on any
increase.

    The derived deposit over x = 6.3 … 15 is a tractive FILM and nothing else —
    the launch mark is 8 m behind and the telemetry declares no slip here beyond
    the film. The floor application is built because the film crosses it, not
    because a mark lands on it.

===============================================================================
5.  NO REPEATED ASSETS
===============================================================================
Four instances — `launch_RL`, `launch_RR`, `film_RL`, `film_RR` — and every one
carries its own hashed draw of eight parameters: density gain, lateral centre
offset, patch width, rib weight, rib phase, graining phase, mottle origin (a
full 3-vector, so no two instances see the same noise anywhere) and edge
hardness. `K.hash01` with the murmur3 finaliser, deterministic. `--gate`
MEASURES the spread between the two launch patches off a rendered field probe
rather than claiming it.

===============================================================================
6.  THE TIME GATE, AND WHY IT IS NOT OPTIONAL
===============================================================================
The two patches are exposed for five frames (837–841 at ~3.5° grazing, ~3.4 kpx
total). The same ground is seen at 27.6° and 42.7° at frames 374 and 424 —
BEFORE THE LAUNCH. A static mark is therefore visible under a parked car for
most of beat 1.

`TDP_DepositField` takes a `Front X` float. BOTH terms are masked by
`x <= Front X`, and `bind_time()` keyframes it from the wheel's own per-frame
world x -- 248 keys, film frames 817 -> 1064, x -1.79280 -> 62.039:

    f <= 817   -1.812   (12 mm behind the mark's start: strictly nothing)
    f 818      -1.792803      f 823   -1.662575
    f 819      -1.766776      f 824   -1.636503
    f 820      -1.740703      f 825   -1.610503
    f 821      -1.714676      f 826   -1.584475
    f 822      -1.688603      f 827   -1.558403   ... on to x = 62.039

LINEAR between keys, CONSTANT extrapolation, so the mark wipes on exactly as the
contact patch travels.

THE FILM IS GATED BY THE SAME CURVE, and the first pass of this module said it
should not be. That was wrong, and the field probe caught it: at frame 816 the
deck beyond the mark was already carrying the film at density 4.99e-04. A film
lying on ground the car has not reached is rubber from a drive-out that has not
happened, and the showroom floor at x = 6.3..15 and the apron beyond it are on
screen while the car is still parked on the dais. One curve, both terms.

`FULLY_LAID_X` is the static value for an A/B or a still: past `FILM_X_END`, so
neither edge of the wipe sits inside the thing being measured.

===============================================================================
7.  WORLD SPACE, AND THE R2-651 GUARD
===============================================================================
The field is evaluated in WORLD metres. The coordinate is
`TexCoord -> Object` through a `ShaderNodeVectorTransform` (POINT, OBJECT ->
WORLD), NOT `Geometry -> Position`: same value, but it keeps the itemkit law
that a graph names the space it is working in, and it is exact through the
turntable deck's 12° yaw. `--gate` renders the field through a 12°-yawed object
and MEASURES that the mark still lands at world x = −1.80000.

Precision: itemkit forbids world-space texturing because at |P| ~ 1000 m a float
has ~0.06 mm left. This field is defined only over |x| <= 63.5 m, where a float
has 3.8 um. The module REFUSES to extend past x = 63.5 (`FILM_X_END`) because
that is where the driven line stops being straight — the wheel's y leaves
±0.79750 by more than 2 mm — and a world-locked straight-line mark past there
would be R2-651 for the third time.

===============================================================================
8.  WIRED BY NAME
===============================================================================
Not one shader socket in this file is addressed by index. Blender 5.2 has
Principled `[4] Alpha [5] Thin Wall [6] Normal` — R2-057 wired nine bump chains
into Thin Wall — and Bump has `[2] Filter Width` in front of `[3] Height`.
Everything goes through `NT.pin_named` / `NT.bump` / `_set_named`, `ShaderNodeMix`
A/B through `NT.cmix`/`NT.fmix` which pin 6/7 and 2/3, and `selftest [5]`
measures the live socket names it depends on and fails if any of them move.
"""

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
for _p in (_WORLD, os.path.join(_ROOT, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import itemkit as K                                          # noqa: E402
import world_contract as C                                   # noqa: E402
from film_exposure import FILM_EXPOSURE                      # noqa: E402

try:
    import bpy
except ImportError:                                          # selftest path
    bpy = None

ITEM = "tyre_deposit"
COLL = "W_Item_TyreDeposit"
PFX = "TDP_"
SEED = 20260807

TRACKS_JSON = os.path.join(_ROOT, "work", "r2_1211_rubber_tracks.json")
TELEMETRY_CSV = os.path.join(_ROOT, "telemetry", "telemetry.csv")
GATE_DIR = os.path.join(_ROOT, "render", "items", ITEM)


# ===========================================================================
# 1.  THE GROUND TRUTH — read, never retyped
# ===========================================================================

def _tracks():
    return json.load(open(TRACKS_JSON, encoding="utf-8"))


TR = _tracks()

HALF_TRACK_REAR = float(TR["provenance"]["rig"].split("HALF_TRACK_REAR ")[1]
                        .split(",")[0])                       # 0.79750
ROLLING_R = float(TR["rolling_radius_m"])                     # 0.360
DECK_Z = float(TR["surface_model"]["dais_deck"]["top_z"])     # 0.340
DECK_YAW_DEG = float(TR["surface_model"]["dais_deck"]["yaw_deg"])

_LM = TR["launch_mark"]["RL"]
MARK_X0 = float(_LM["mark_start_world"][0])                   # -1.80000
MARK_X1 = float(_LM["mark_end_world"][0])                     # -1.55840
MARK_LEN = float(_LM["mark_length_m"])                        # 0.2416
MARK_TERMINAL = float(_LM["terminal_deposit_norm"])           # 0.02671
TOTAL_SLID_M = float(TR["slip_summary"]["total_tyre_surface_slid_m"])

#: 251.1 mm, the derived contact-patch width (|y| 0.672 .. 0.923).
PATCH_W = 0.2511

WHEEL_Y = {"RL": +HALF_TRACK_REAR, "RR": -HALF_TRACK_REAR}


def _launch_frames(corner="RL"):
    """(film_frame, world x, deposit_norm) for every frame carrying deposit.

    The per-frame arrays are the ground truth. `launch_mark_profile`'s 256-point
    resample is NOT used for the tail: its last sample is 0.0, which contradicts
    `launch_mark.decay_note` in the same file ("terminates at 2.7 % of peak ...
    a hard trailing edge, not a fade") and its own `terminal_deposit_norm`
    0.02671. The resampler fades the last ~13 mm to zero. See selftest [1].
    """
    w = TR["wheels"][corner]
    ff = w["film_frame"]
    out = []
    for i, f in enumerate(ff):
        d = float(w["deposit_norm"][i])
        if d > 0.0:
            out.append((int(f), float(w["x"][i]), d))
    return out


LAUNCH_FRAMES = _launch_frames("RL")
FIRST_DEPOSIT_FRAME = LAUNCH_FRAMES[0][0]                     # 818
LAST_DEPOSIT_FRAME = LAUNCH_FRAMES[-1][0]                     # 827


def launch_profile_stops(n_dec=6):
    """The along-track density profile as ColorRamp stops, u = s / MARK_LEN.

    Piecewise-constant per-segment data (`deposit_norm` is credited to the
    segment ENDING at its sample) de-staircased through the segment MIDPOINTS,
    with the peak carried flat to u = 0 and the terminal 2.7 % carried flat to
    u = 1. The 24 mm stair steps are inside the resolvable band, so leaving them
    as steps would put visible banding in the mark.
    """
    xs = [MARK_X0] + [x for _f, x, _d in LAUNCH_FRAMES]
    ds = [d for _f, _x, d in LAUNCH_FRAMES]
    stops = [(0.0, 1.0)]
    for i, d in enumerate(ds):
        mid = 0.5 * (xs[i] + xs[i + 1]) - MARK_X0
        u = mid / MARK_LEN
        if u > stops[-1][0] + 1e-4:
            stops.append((round(u, n_dec), d))
    stops.append((1.0, MARK_TERMINAL))
    return stops


LAUNCH_STOPS = launch_profile_stops()


# ---------------------------------------------------------------- the film ---

def _telemetry_cols():
    rows = list(csv.DictReader(open(TELEMETRY_CSV, encoding="utf-8")))
    return (np.array([float(r["t_s"]) for r in rows]),
            np.array([float(r["accel_long_ms2"]) for r in rows]),
            np.array([float(r["speed_ms"]) for r in rows]))


G = 9.80665
#: x where the driven line stops being straight (|y| leaves +-0.79750 by 2 mm).
#: The field REFUSES to be evaluated past here -- see the module docstring §7.
FILM_X_END = 63.5
FILM_CAL_X = (15.0, 49.0)          # the brief's calibration window
FILM_CAL_SLID_M = 1.0              # the brief's target, 1 m of tyre surface


def _film_profile(corner="RR", n=24):
    """(x stops, kappa stops, summary) for the tractive-slip film.

    kappa(x) = mu_used(x) * SCALE, mu_used = a_x / (2 * Fz_norm * g), SCALE set
    so the integral of kappa ds over x = 15..49 is FILM_CAL_SLID_M.
    """
    w = TR["wheels"][corner]
    t = np.array(w["world_t"]); x = np.array(w["x"])
    s = np.array(w["s_along_track_m"]); nl = np.array(w["normal_load_norm"])
    tt, ax, sp = _telemetry_cols()
    axi = np.interp(t, tt, ax)
    mu = np.clip(axi, 0.0, None) / (2.0 * nl * G)
    ds = np.gradient(s)
    cal = (x >= FILM_CAL_X[0]) & (x <= FILM_CAL_X[1])
    integ = float(np.sum(mu[cal] * ds[cal]))
    scale = FILM_CAL_SLID_M / integ
    kap = mu * scale
    span = (x >= MARK_X1) & (x <= FILM_X_END)
    xs = np.linspace(MARK_X1, FILM_X_END, n)
    ks = np.interp(xs, x[span], kap[span])
    summ = dict(
        mu_cal_min=float(mu[cal].min()), mu_cal_max=float(mu[cal].max()),
        mu_cal_p50=float(np.median(mu[cal])),
        integral_mu_ds_cal=integ, scale=scale,
        kappa_cal_min=float(kap[cal].min()), kappa_cal_max=float(kap[cal].max()),
        slid_cal_m=float(np.sum(kap[cal] * ds[cal])),
        slid_span_m=float(np.sum(kap[span] * ds[span])),
        track_len_cal_m=float(ds[cal].sum()),
        kappa_max=float(ks.max()),
        speed_cal=(float(np.interp(t, tt, sp)[cal].min()),
                   float(np.interp(t, tt, sp)[cal].max())),
        implied_slip_stiffness_vs_weight=float(np.median(mu[cal])
                                               / np.median(kap[cal])),
    )
    return xs, ks, summ


FILM_X, FILM_K, FILM = _film_profile()

# --------------------------------------------------------- areal densities ---
#: m of slid tyre surface per m2 of ground at the launch mark's PEAK segment.
#: Density 1.0 in the field means exactly this.
_i0 = TR["wheels"]["RL"]["film_frame"].index(FIRST_DEPOSIT_FRAME)
LAUNCH_PEAK_AREAL = (float(TR["wheels"]["RL"]["slip_distance_m"][_i0])
                     / ((LAUNCH_FRAMES[0][1] - MARK_X0) * PATCH_W))
LAUNCH_MEAN_AREAL = TOTAL_SLID_M / (MARK_LEN * PATCH_W)
FILM_CAL_AREAL = FILM_CAL_SLID_M / (FILM["track_len_cal_m"] * PATCH_W)

#: the film's density in the field's units. ~9.6e-4.
FILM_DENSITY_CAL = FILM_CAL_AREAL / LAUNCH_PEAK_AREAL
FILM_DENSITY_PEAK = (FILM["kappa_max"] / PATCH_W) / LAUNCH_PEAK_AREAL


# ===========================================================================
# 2.  THE TWO SATURATION LAWS  (module docstring §2)
# ===========================================================================

#: metres of transferred rubber film per metre of tyre surface slid per m2.
#: Archard on rubber/concrete at ~3 bar: k ~ 3e-13 m3/(N m) * 3e5 Pa.
TRANSFER_M_PER_M = 9.0e-8
#: optical depth ~1 in carbon-black rubber.
TAU_OPTICAL_M = 3.1e-6
#: monolayer-scale wetting: ~25 molecular layers.
TAU_WET_M = 7.6e-9
#: QUARTER-WAVE. A film only OWNS the Fresnel interface once it is thick
#: against a quarter of a visible wavelength; below that the light still sees
#: the substrate's interface through it. 550/4 = 138 nm, taken at 110 nm.
#:
#: THIS SCALE EXISTS BECAUSE THE GATE CAUGHT ME WITHOUT IT. Metallic, Specular
#: IOR Level and Coat Weight were all driven by WETTING, which saturates at a
#: monolayer -- so a 10.6 nm tractive film was turning brushed metal into a
#: dielectric, and the deck measured **+52.2 % mean over the film band** with
#: the launch mark itself only +23.2 %. A 10 nm transfer film does not stop a
#: metal being a metal. Three effects, three lengths, and each one is a
#: property of the film's THICKNESS against a stated physical scale:
#:
#:   roughness, coat roughness   TAU_WET_M      7.6 nm    surface energy
#:   metallic, specular, coat    TAU_IFACE_M    110 nm    Fresnel interface
#:   base colour                 TAU_OPTICAL_M  3.1 um    optical depth
#:
#: launch mark 11.0 um -> 1.0000 / 1.0000 / 0.9716
#: tractive film 10.6 nm -> 0.7523 / 0.0918 / 0.0034
TAU_IFACE_M = 1.10e-7

_THICK_PER_D = LAUNCH_PEAK_AREAL * TRANSFER_M_PER_M      # m of film at D = 1
TAU_COVER = TAU_OPTICAL_M / _THICK_PER_D                 # ~0.2811
TAU_WET = TAU_WET_M / _THICK_PER_D                       # ~6.89e-4
TAU_IFACE = TAU_IFACE_M / _THICK_PER_D                   # ~9.97e-3


def coverage(d):
    return 1.0 - np.exp(-np.asarray(d, float) / TAU_COVER)


def wetting(d):
    return 1.0 - np.exp(-np.asarray(d, float) / TAU_WET)


def interface(d):
    """How much of the Fresnel interface the film owns. See TAU_IFACE_M."""
    return 1.0 - np.exp(-np.asarray(d, float) / TAU_IFACE)


# ===========================================================================
# 3.  PER-INSTANCE VARIATION  (module docstring §5)
# ===========================================================================

INSTANCES = (
    dict(key="launch_RL", kind="launch", corner="RL"),
    dict(key="launch_RR", kind="launch", corner="RR"),
    dict(key="film_RL", kind="film", corner="RL"),
    dict(key="film_RR", kind="film", corner="RR"),
)


def _ikey(s):
    h = 2166136261
    for ch in str(s):
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


def jit(lo, hi, *keys):
    """A deterministic draw in [lo, hi). `K.hash01`'s murmur3 finaliser is what
    stops seven properties of one instance collapsing onto one value."""
    return lo + (hi - lo) * K.hash01(SEED, *[_ikey(k) for k in keys])


def instance_params(key):
    """The eight independent draws that make each patch its own object."""
    return dict(
        gain=jit(0.90, 1.10, key, "gain"),
        dy=jit(-0.006, 0.006, key, "dy"),
        width=PATCH_W * jit(0.965, 1.035, key, "width"),
        rib_w=jit(0.20, 0.34, key, "rib_w"),
        rib_phase=jit(0.0, 1.0, key, "rib_phase"),
        grain_phase=jit(0.0, 1.0, key, "grain_phase"),
        origin=(jit(-40.0, 40.0, key, "ox"),
                jit(-40.0, 40.0, key, "oy"),
                jit(-40.0, 40.0, key, "oz")),
        edge=jit(0.010, 0.016, key, "edge"),
    )


PARAMS = {i["key"]: instance_params(i["key"]) for i in INSTANCES}


# ===========================================================================
# 4.  THE OCTAVE TABLE — every wavelength this module emits
# ===========================================================================

BAND_LO, BAND_HI = 0.012, 0.300           # the staging doc's window, metres


def detail_for(wavelength_m, lo=None):
    """How many fractal octaves a texture at `wavelength_m` may emit.

    THE OCTAVE LAW APPLIES TO THE FRACTAL, NOT ONLY TO THE AMPLITUDE, and that
    is where this file broke it on its first pass. `ShaderNodeTexNoise` with
    `Detail = d` emits d+1 octaves, at lam, lam/2, lam/4 ... lam/2^d. A 120 mm
    noise at the house default `detail=6` is therefore ALSO emitting a 1.9 mm
    octave and a 0.94 mm octave -- six times below the 12 mm floor and below the
    2.4 mm "material only, never pattern" line on every surface in the staging
    doc's band table. Those octaves cannot reach the image at any resolution
    this film is graded at.

    They are not free. With the house defaults this module shipped with, ONE 4K
    frame of the concrete arm did not finish in ten minutes on this box's CPU
    (its GPU is unavailable today). So the detail is DERIVED rather than typed:
    the finest octave is held at or above the band floor. `detail_for(0.120)`
    = 3, which emits 120 / 60 / 30 / 15 mm and stops.
    """
    lo = BAND_LO if lo is None else lo
    return float(max(0, min(8, int(math.floor(math.log(
        max(float(wavelength_m), 1e-9) / lo, 2.0))))))

#: Pattern structure inside the field. (name, wavelength_m, what it is)
#: Every one is emitted with `detail_for(lam)` octaves, so none of them puts
#: anything below the 12 mm floor.
FIELD_STRUCTURE = (
    ("patch_rib", PATCH_W / 3.0, "the three-rib pressure split across the "
                                 "251.1 mm contact patch"),
    ("graining", 0.0186, "longitudinal graining striations, along the slide"),
    ("scuff_fine", 0.042, "scuff mottle, fine"),
    ("scuff_coarse", 0.120, "scuff mottle, coarse"),
    ("edge", 0.012, "the leading and trailing edges, at the band floor"),
)

#: Relief this module AUTHORS. (name, wavelength_m, modulation_pp, band, sign)
#: Amplitudes are NEVER typed: K.relief_amplitude_for(m, lam) supplies them.
RELIEF = {
    "concrete": (
        ("dep_fill_fine", 0.022, 0.30, "isotropic_micro", -1),
        ("dep_fill_coarse", 0.095, 0.55, "isotropic_macro", -1),
        ("dep_shoulder", 0.251, 0.40, "isotropic_macro", +1),
    ),
    "deck": (
        ("dep_film_micro", 0.016, 0.14, "isotropic_micro", +1),
        ("dep_film_mottle", 0.130, 0.16, "isotropic_micro", +1),
    ),
    "floor": (
        ("dep_smear_fine", 0.014, 0.13, "isotropic_micro", +1),
        ("dep_smear_broad", 0.115, 0.12, "isotropic_micro", +1),
    ),
}

#: Substrate stages this module MODULATES but does not author. Measured off
#: build_surface.py:2887-2888 -- see module docstring §3.
SUBSTRATE_STAGES = (
    ("M_Surf_Concrete micro", 0.00229, 0.0006 * 0.45, 0.55),
    ("M_Surf_Concrete aggregate", 0.02411, 0.0030 * 1.00, 0.90),
)


def relief_rows(which=None, verbose=True):
    """`K.relief_budget` over every authored stage, amplitude derived."""
    out = []
    for surf, stages in RELIEF.items():
        if which and surf != which:
            continue
        rows = K.relief_budget(
            [("%s/%s" % (surf, nm), lam, K.relief_amplitude_for(m, lam))
             for nm, lam, m, _b, _s in stages], verbose=False)
        for r, (_nm, _lam, _m, band, sign) in zip(rows, stages):
            lo, hi = K.RELIEF_BANDS[band]
            r["band"] = band
            r["verdict"] = "LOW" if r["m"] < lo else "HIGH" if r["m"] > hi else "ok"
            r["sign"] = sign
            r["in_window"] = BAND_LO <= r["wavelength_m"] <= BAND_HI
            out.append(r)
    if verbose:
        print("    %-34s %9s %9s %8s %7s %-16s %s"
              % ("stage", "lam mm", "amp mm", "slope", "m pp", "band", "verdict"))
        for r in out:
            print("    %-34s %9.2f %9.4f %8.2f %7.3f %-16s %s%s"
                  % (r["name"], r["wavelength_m"] * 1000.0, r["amp_mm"],
                     r["slope_deg"], r["m"], r["band"], r["verdict"],
                     "" if r["in_window"] else "  OUTSIDE 12-300 mm"))
    return out


# ===========================================================================
# 5.  NODE PLUMBING — by name, always
# ===========================================================================

def _kit(tree):
    """An `itemkit.NT` bound to an EXISTING tree.

    `NT.__init__` creates a material and clears its tree, which is wrong for a
    node group, so it is bypassed exactly as `build_dressing._kit` does. The
    point is to get `NT.bump` -- the by-name, relief-law-carrying one -- rather
    than write a second one here.
    """
    k = K.NT.__new__(K.NT)
    k.m = None
    k.t = tree
    k.x = 0
    return k


def _o(nd, name):
    """(node, index) for an OUTPUT socket addressed by NAME."""
    for i, s in enumerate(nd.outputs):
        if s.name == name:
            return (nd, i)
    raise RuntimeError("%s has no output named %r; it has %s"
                       % (nd.bl_idname, name, [s.name for s in nd.outputs]))


def _set_named(nd, name, value):
    """Set an input default_value BY NAME. The `_feed_named` discipline
    (`world/build_dressing.py:1255-1285`, R2-057) for the non-linked case."""
    for s in nd.inputs:
        if s.name == name:
            s.default_value = value
            return
    raise RuntimeError("%s has no input named %r; it has %s"
                       % (nd.bl_idname, name, [s.name for s in nd.inputs]))


def _new_group(name, ins, outs):
    """A fresh ShaderNodeTree with a named interface. Idempotent by name."""
    old = bpy.data.node_groups.get(name)
    if old is not None:
        bpy.data.node_groups.remove(old)
    ng = bpy.data.node_groups.new(name, "ShaderNodeTree")
    for nm, typ, dflt in ins:
        s = ng.interface.new_socket(nm, in_out="INPUT", socket_type=typ)
        if dflt is not None:
            s.default_value = dflt
        if typ == "NodeSocketFloat":
            # NOT (-10, 10): `Front X` is a WORLD x and runs to +63.6, and a
            # socket range silently clamps a default it does not like.
            s.min_value = -1000.0
            s.max_value = 1000.0
    for nm, typ in outs:
        ng.interface.new_socket(nm, in_out="OUTPUT", socket_type=typ)
    gin = ng.nodes.new("NodeGroupInput")
    gin.location = (-1400, 0)
    gout = ng.nodes.new("NodeGroupOutput")
    gout.location = (1600, 0)
    return ng, gin, gout


def voffset(t, vec, offset):
    """`vec + offset` where `offset` is a literal 3-vector.

    `NT.pin` appends a 1.0 to any 3-tuple because it assumes a colour, which a
    Vector socket refuses. The offset is set on the socket directly instead.
    """
    nd = t.n("ShaderNodeVectorMath", operation="ADD")
    t.pin_named(nd, "Vector", vec)
    nd.inputs[1].default_value = tuple(float(v) for v in offset)
    return _o(nd, "Vector")


def world_position(t):
    """`TexCoord -> Object` through a POINT OBJECT->WORLD VectorTransform.

    Not `Geometry -> Position`: same number, but the graph says which space it
    is in, and itemkit's `NT` deliberately has no `position()`. See §7.
    """
    obj = t.object_coords()
    vt = t.n("ShaderNodeVectorTransform", vector_type="POINT",
             convert_from="OBJECT", convert_to="WORLD")
    t.pin_named(vt, "Vector", obj)
    return _o(vt, "Vector")


# ===========================================================================
# 6.  THE FIELD  —  TDP_DepositField
# ===========================================================================

FIELD_GROUP = PFX + "DepositField"
FIELD_INPUTS = (("World Position", "NodeSocketVector", None),
                ("Front X", "NodeSocketFloat", FILM_X_END + 0.10),
                ("Traffic Passes", "NodeSocketFloat", 1.0))
FIELD_OUTPUTS = (("Density", "NodeSocketFloat"),
                 ("Coverage", "NodeSocketFloat"),
                 ("Interface", "NodeSocketFloat"),
                 ("Wetting", "NodeSocketFloat"),
                 ("Grain", "NodeSocketFloat"),
                 ("Launch", "NodeSocketFloat"),
                 ("Film", "NodeSocketFloat"))


def _saturate(t, d, tau):
    """1 - exp(-d / tau), built out of Math nodes."""
    e = t.math("MULTIPLY", d, -1.0 / float(tau))
    e = t.math("POWER", math.e, e)
    return t.math("SUBTRACT", 1.0, e, clamp=True)


def _lateral(t, y, y0, half_w, edge, rib_w, rib_phase, key):
    """The across-the-patch profile: a 251.1 mm patch with a three-rib split.

    Every wavelength here is in the 12-300 mm window: the rib pitch is
    PATCH_W/3 = 83.7 mm and the edge is the 12 mm band floor.
    """
    dy = t.math("ABSOLUTE", t.math("SUBTRACT", y, y0))
    # the patch envelope, hard-edged at the band floor
    env = t.maprange(dy, half_w - 0.5 * edge, half_w + 0.5 * edge, 1.0, 0.0)
    # three ribs across the patch. A tyre under traction does not lay a flat
    # bar: the shoulders and the centre carry different contact pressure.
    lam = PATCH_W / 3.0
    yy = t.math("ADD", y, rib_phase * lam)
    rib = t.wave(t.comb(0.0, yy, 0.0), wavelength_m=lam, distortion=0.35,
                 detail=detail_for(lam), direction="Y")
    rib = t.maprange(rib, 0.0, 1.0, 1.0 - rib_w, 1.0 + rib_w * 0.55)
    return t.math("MULTIPLY", env, rib), env


def _grain(t, P, key, p):
    """Graining striations + scuff mottle, 0..1, all in-window.

    The origin offset is a full 3-vector drawn per instance, so no two
    instances ever see the same noise -- this is the "one tree spammed 100
    times" guard, applied to a field instead of to a mesh.
    """
    Po = voffset(t, P, p["origin"])
    # striations run ALONG the slide (world x), so the wave varies in y
    st = t.wave(voffset(t, Po, (0.0, p["grain_phase"] * 0.0186, 0.0)),
                wavelength_m=0.0186, distortion=1.1,
                detail=detail_for(0.0186), direction="Y")
    sf = t.noise(Po, wavelength_m=0.042, detail=detail_for(0.042), rough=0.55)
    sc = t.noise(Po, wavelength_m=0.120, detail=detail_for(0.120), rough=0.60)
    g = t.math("MULTIPLY", t.maprange(st, 0.15, 0.85, 0.62, 1.0),
               t.maprange(sf, 0.28, 0.78, 0.70, 1.0))
    g = t.math("MULTIPLY", g, t.maprange(sc, 0.25, 0.80, 0.55, 1.0))
    return g


def build_field_group():
    """`TDP_DepositField`. World position + Front X -> the six field channels."""
    ng, gin, gout = _new_group(FIELD_GROUP, FIELD_INPUTS, FIELD_OUTPUTS)
    t = _kit(ng)
    P = _o(gin, "World Position")
    front = _o(gin, "Front X")
    passes = _o(gin, "Traffic Passes")
    x = t.sep(P, 0)
    y = t.sep(P, 1)
    z = t.sep(P, 2)

    # --- the deck gate. The launch patch exists on the deck plane and nowhere
    # else; without this it would also land on Platform_Dais at z = 0.300 and
    # on the floor at z = 0 directly underneath.
    dz = t.math("ABSOLUTE", t.math("SUBTRACT", z, DECK_Z))
    deck = t.maprange(dz, 0.050, 0.070, 1.0, 0.0)

    # --- the time gate. s_front = Front X - MARK_X0, the wipe front.
    s = t.math("SUBTRACT", x, MARK_X0)
    s_front = t.math("SUBTRACT", front, MARK_X0)
    wipe = t.maprange(t.math("SUBTRACT", s_front, s), 0.0, 0.012, 0.0, 1.0)

    launch_terms, film_terms, grain_terms = [], [], []
    for inst in INSTANCES:
        p = PARAMS[inst["key"]]
        y0 = WHEEL_Y[inst["corner"]] + p["dy"]
        half = 0.5 * p["width"]
        lat, _env = _lateral(t, y, y0, half, p["edge"], p["rib_w"],
                             p["rib_phase"], inst["key"])
        gr = _grain(t, P, inst["key"], p)
        grain_terms.append(t.math("MULTIPLY", gr, lat))

        if inst["kind"] == "launch":
            u = t.maprange(s, 0.0, MARK_LEN, 0.0, 1.0)
            prof = t.ramp(u, [(pos, (v, v, v)) for pos, v in LAUNCH_STOPS])
            # BOTH edges hard, centred on the declared stations, width = the
            # instance's own draw around the 12 mm band floor.
            e = p["edge"]
            lead = t.maprange(s, -0.5 * e, 0.5 * e, 0.0, 1.0)
            trail = t.maprange(s, MARK_LEN - 0.5 * e, MARK_LEN + 0.5 * e, 1.0, 0.0)
            d = t.math("MULTIPLY", prof, t.math("MULTIPLY", lead, trail))
            d = t.math("MULTIPLY", d, t.math("MULTIPLY", lat, deck))
            d = t.math("MULTIPLY", d, wipe)
            d = t.math("MULTIPLY", d, p["gain"])
            # the grain modulates the mark's own density, +-18 %
            d = t.math("MULTIPLY", d, t.maprange(gr, 0.4, 1.0, 0.82, 1.18))
            launch_terms.append(d)
        else:
            ux = t.maprange(x, MARK_X1, FILM_X_END, 0.0, 1.0)
            kn = FILM_K / FILM_K.max()
            stops = [(float(i) / (len(kn) - 1), (float(v), float(v), float(v)))
                     for i, v in enumerate(kn)]
            prof = t.ramp(ux, stops)
            # the film starts where the mark ends and stops where the driven
            # line stops being straight (§7). Both edges at the band floor.
            on = t.math("MULTIPLY",
                        t.maprange(x, MARK_X1 - 0.006, MARK_X1 + 0.006, 0.0, 1.0),
                        t.maprange(x, FILM_X_END - 0.012, FILM_X_END, 1.0, 0.0))
            # the SAME wipe front as the mark: no rubber on ground the car has
            # not reached yet. See `_front_keys`.
            on = t.math("MULTIPLY", on,
                        t.maprange(t.math("SUBTRACT", front, x),
                                   0.0, 0.012, 0.0, 1.0))
            d = t.math("MULTIPLY", prof, t.math("MULTIPLY", lat, on))
            d = t.math("MULTIPLY", d, FILM_DENSITY_PEAK * p["gain"])
            d = t.math("MULTIPLY", d, t.maprange(gr, 0.4, 1.0, 0.80, 1.20))
            # THE ONE ART KNOB IN THIS MODULE, AND IT HAS A UNIT. See §2b.
            d = t.math("MULTIPLY", d, passes)
            film_terms.append(d)

    launch = launch_terms[0]
    for term in launch_terms[1:]:
        launch = t.math("ADD", launch, term)
    film = film_terms[0]
    for term in film_terms[1:]:
        film = t.math("ADD", film, term)
    dens = t.math("ADD", launch, film)
    grain = grain_terms[0]
    for term in grain_terms[1:]:
        grain = t.math("MAXIMUM", grain, term)

    cov = _saturate(t, dens, TAU_COVER)
    ifc = _saturate(t, dens, TAU_IFACE)
    wet = _saturate(t, dens, TAU_WET)

    for nm, src in (("Density", dens), ("Coverage", cov), ("Interface", ifc),
                    ("Wetting", wet),
                    ("Grain", grain), ("Launch", launch), ("Film", film)):
        t.pin_named(gout, nm, src)
    return ng


def field_node(t, front_value=None, front_node=None, passes=None):
    """A `TDP_DepositField` instance wired to world space, in tree `t`."""
    ng = bpy.data.node_groups.get(FIELD_GROUP) or build_field_group()
    n = t.n("ShaderNodeGroup", node_tree=ng)
    t.pin_named(n, "World Position", world_position(t))
    if front_node is not None:
        t.pin_named(n, "Front X", front_node)
    elif front_value is not None:
        t.pin_named(n, "Front X", float(front_value))
    if passes is not None:
        t.pin_named(n, "Traffic Passes", float(passes))
    return n


def front_x_value_node(t, name=PFX + "FrontX"):
    """The `Front X` driver: a Value node this module keyframes. §6."""
    v = t.n("ShaderNodeValue")
    v.label = name
    v.outputs[0].default_value = MARK_X1
    return v


def _front_keys():
    """`Front X` for every film frame, from the wheel's own world x.

    THE FRONT GATES THE FILM TOO, NOT ONLY THE MARK, and the first pass of this
    module got that wrong. A tractive film laid ahead of the car is the same
    beat-1 defect as a static launch mark: the showroom floor at x = 6.3 .. 15
    and the apron beyond it are on screen while the car is still parked on the
    dais, and a film already lying on ground the car has not reached is rubber
    from a drive-out that has not happened. Measured on the first field probe:
    at frame 816 the deck beyond the mark was already carrying the film at
    density 4.99e-04. One curve fixes both.
    """
    w = TR["wheels"]["RL"]
    keys = [(FIRST_DEPOSIT_FRAME - 1, MARK_X0 - 0.012)]
    for f, x in zip(w["film_frame"], w["x"]):
        if int(f) >= FIRST_DEPOSIT_FRAME and float(x) <= FILM_X_END:
            keys.append((int(f), float(x)))
    return keys


FRONT_X_KEYS = _front_keys()

#: `Front X` for a STATIC evaluation -- the A/B arms, and anything that wants
#: the finished state. Past FILM_X_END, so both the mark and the film are fully
#: laid and neither edge of the wipe is sitting inside the thing being measured.
FULLY_LAID_X = FILM_X_END + 0.10


def bind_time(value_node, action_name=PFX + "FrontX"):
    """Keyframe a `Front X` Value node from the wheel's own per-frame world x.

    LINEAR between keys, CONSTANT extrapolation. Up to and including frame 817
    the front sits 12 mm BEHIND the mark's start, so BOTH terms are identically
    zero and nothing can exist under the parked car. The first key carrying
    deposit is 818, because `deposit_norm` is credited to the segment ENDING at
    its sample.

    THE MATERIAL MUST HAVE A USER IN THE SCENE FOR THIS TO DO ANYTHING, and it
    fails silently otherwise. An animated shader node tree is only evaluated by
    the depsgraph if something in the scene uses the material; with no user,
    `frame_set` leaves every frame at the static default and the mark looks
    simply un-animated. Verified: with a user, frames 816/818/822/827/1064 read
    back -1.81200 / -1.79280 / -1.68860 / -1.55840 / +62.03892, each to better
    than 5e-07. Without one, all of them read +63.60000.
    """
    sock = value_node.outputs[0]
    for f, x in FRONT_X_KEYS:
        sock.default_value = float(x)
        value_node.id_data.keyframe_insert(
            'nodes["%s"].outputs[0].default_value' % value_node.name, frame=f)
    for fc in action_fcurves(value_node.id_data):
        fc.extrapolation = "CONSTANT"
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    sock.default_value = FULLY_LAID_X
    return value_node


def action_fcurves(id_data):
    """Every F-curve on `id_data`'s action, on 5.2's SLOTTED actions.

    `Action.fcurves` DOES NOT EXIST IN BLENDER 5.2. It was the whole API in
    4.3 and earlier and it is gone: an action now holds `layers`, each layer
    holds `strips`, and each strip holds a `channelbag` per SLOT, and the
    F-curves live on the channelbag. `bind_time` raised
    `AttributeError: 'Action' object has no attribute 'fcurves'` the first time
    it was ever run, which is the same family of failure as R2-057 -- a socket
    index and an attribute name are both "the API moved and the code did not" --
    except that this one is loud. The legacy path is kept because nothing here
    should care which Blender it is on.
    """
    ad = getattr(id_data, "animation_data", None)
    act = getattr(ad, "action", None) if ad else None
    if act is None:
        return []
    if hasattr(act, "fcurves"):                        # <= 4.3
        return list(act.fcurves)
    out = []
    for layer in act.layers:
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", ()):
                out.extend(cb.fcurves)
    return out


# ===========================================================================
# 7.  THE THREE APPLICATIONS
# ===========================================================================
#
# Each is a node group: substrate channels + the field's channels in, modified
# substrate channels out. That makes each one a drop-in and it makes the
# "everything this module authors" set exactly "the node trees named TDP_*",
# which is the domain `--gate` sweeps for wavelengths and image textures.

CONC_GROUP = PFX + "Apply_Concrete"
DECK_GROUP = PFX + "Apply_BrushedMetal"
FLOOR_GROUP = PFX + "Apply_PolishedFloor"

#: the rubber pigment, linear. Only ever used where it is DARKER than the
#: substrate -- never on FloorPolished. See §4.
COL_RUBBER = (0.0420, 0.0398, 0.0385)

#: THE ONLY ART KNOB IN THIS MODULE, AND IT HAS A UNIT AND A DEFAULT OF 1.
#:
#: The physics is unambiguous and unwelcome: 3 % tractive slip over 34 m leaves
#: ~10 nm of rubber (§2), which changes NO surface's albedo measurably. The
#: derived single-pass film's entire read is therefore in gloss, and if that
#: does not clear the concrete's own +-14.5 % mottle then no PIGMENT on that
#: apron is derivable from this car at all -- which would make the existing
#: -5.73 % paint an art choice with no derivation, applied in the wrong place
#: with the wrong shape and the wrong lateral offset.
#:
#: `Traffic Passes` is the honest place to put that decision. It is the number
#: of equivalent tractive-slip passes the surface carries, it multiplies the
#: film's AREAL DENSITY linearly, and N = 1 is exactly this car, once. The gate
#: renders N = 1 and N = 60 side by side so the cost of the decision is a
#: measured number rather than an argument.
FILM_TRAFFIC_SWEEP = 60.0

# ---- concrete
CONC_ROUGH_TARGET = 0.52          # 0.80 nominal -> 0.52 fully wetted
#: NOT a taste number: Principled's Specular IOR Level is F0/0.08, and rubber
#: at n = 1.52 has F0 = ((n-1)/(n+1))^2 = 0.04258, so the level is 0.5322.
#: 0.32 flat -> 0.5322. This is the channel R2-1213 found MISSING entirely.
CONC_SPEC_TARGET = ((1.52 - 1.0) / (1.52 + 1.0)) ** 2 / 0.08
CONC_ALBEDO_MIX = 0.62            # x coverage; the film's coverage is 0.003
CONC_ALBEDO_DIM = 0.30            # x coverage, multiplicative
CONC_FILL_WET = 0.32              # peak-blunting at monolayer
CONC_FILL_MASS = 0.55             # bulk fill, needs real thickness

# ---- brushed metal
DECK_METALLIC_KILL = 0.94         # 0.86 -> 0.052
DECK_ROUGH_TARGET = 0.68
DECK_ALBEDO_MIX = 0.35
COL_RUBBER_ON_METAL = (0.0385, 0.0372, 0.0364)

# ---- polished floor
FLOOR_ROUGH_TARGET = 0.42
FLOOR_COAT_SUPPRESS = 0.62        # CAPPED. R2-082's crushed-black guard.
FLOOR_COAT_ROUGH_TARGET = 0.30    # the coat still returns light, diffusely
FLOOR_SPEC_TARGET = 0.50
FLOOR_ALBEDO_DIM = 0.10           # MULTIPLICATIVE. Never a mix. §4.


def _wet_grain(t, wet, grain, lo=0.55):
    """Wetting broken up by the grain so it is never a flat wash."""
    return t.math("MULTIPLY", wet, t.maprange(grain, 0.35, 1.0, lo, 1.0))


def _dep_relief(t, surf, mask, P, seed_key):
    """The relief stages this module authors for `surf`, masked by the deposit.

    Amplitudes come from `K.relief_amplitude_for(m, lam)` -- there is no typed
    millimetre anywhere in this function, which is the whole point.
    `relief_budget` reports the FULL-STRENGTH amplitude, which is what the
    surface gets inside the mark; `mask` scales it to zero outside.
    """
    nrm = None
    for nm, lam, m, _band, sign in RELIEF[surf]:
        if not BAND_LO <= lam <= BAND_HI:
            raise RuntimeError(
                "REFUSING: %s/%s is at %.1f mm, outside the 12-300 mm window "
                "that is inside the resolvable band on every relevant surface "
                "at both 4K and 720p. The circuit road shipped 20 layers of "
                "which 17 were outside it." % (surf, nm, lam * 1000.0))
        h = t.noise(voffset(t, P, (jit(-30, 30, seed_key, nm, "x"),
                                   jit(-30, 30, seed_key, nm, "y"),
                                   jit(-30, 30, seed_key, nm, "z"))),
                    wavelength_m=lam, detail=detail_for(lam), rough=0.55)
        h = t.math("SUBTRACT", h, 0.5)
        h = t.math("MULTIPLY", h, float(sign))
        h = t.math("MULTIPLY", h, mask)
        h = t.math("ADD", h, 0.5)
        nrm = t.bump(h, 1.0, normal=nrm, modulation_pp=m, wavelength_m=lam,
                     height_pp=0.62)
    return nrm


def build_concrete_group():
    """`TDP_Apply_Concrete` — the drop-in replacement for the apron paint.

    Four channels, against the existing mark's two:

        Base Color            multiplicative dim + a mix toward COL_RUBBER,
                              both driven by COVERAGE, which for the tractive
                              film is 0.34 % -- i.e. essentially nothing, and
                              that is the physically right answer for one pass.
        Roughness             0.80 -> 0.52 by WETTING. Was -0.18.
        Specular IOR Level    0.32 -> 0.52 by WETTING. Was UNTOUCHED (R2-1213).
        Height (two stages)   the substrate's 2.29 mm and 24.11 mm bumps are
                              REDUCED, because rubber fills texture; plus this
                              module's own three in-window stages.
    """
    ng, gin, gout = _new_group(
        CONC_GROUP,
        (("Base Color", "NodeSocketColor", (0.30, 0.29, 0.28, 1.0)),
         ("Roughness", "NodeSocketFloat", 0.80),
         ("Specular IOR Level", "NodeSocketFloat", 0.32),
         ("Height Micro", "NodeSocketFloat", 0.5),
         ("Height Coarse", "NodeSocketFloat", 0.5),
         ("Coverage", "NodeSocketFloat", 0.0),
         ("Interface", "NodeSocketFloat", 0.0),
         ("Wetting", "NodeSocketFloat", 0.0),
         ("Grain", "NodeSocketFloat", 1.0),
         ("World Position", "NodeSocketVector", None)),
        (("Base Color", "NodeSocketColor"),
         ("Roughness", "NodeSocketFloat"),
         ("Specular IOR Level", "NodeSocketFloat"),
         ("Height Micro", "NodeSocketFloat"),
         ("Height Coarse", "NodeSocketFloat"),
         ("Normal", "NodeSocketVector")))
    t = _kit(ng)
    base = _o(gin, "Base Color")
    rough = _o(gin, "Roughness")
    spec = _o(gin, "Specular IOR Level")
    hm = _o(gin, "Height Micro")
    hc = _o(gin, "Height Coarse")
    cov = _o(gin, "Coverage")
    ifc = _o(gin, "Interface")
    wet = _o(gin, "Wetting")
    grain = _o(gin, "Grain")
    P = _o(gin, "World Position")

    wg = _wet_grain(t, wet, grain)
    ig = _wet_grain(t, ifc, grain)
    cg = t.math("MULTIPLY", cov, t.maprange(grain, 0.35, 1.0, 0.55, 1.0))

    # --- colour. A mix toward the rubber pigment is legitimate HERE and only
    # here: concrete sits near 0.18-0.30 linear, so 0.042 is genuinely darker.
    dim = t.math("SUBTRACT", 1.0, t.math("MULTIPLY", cg, CONC_ALBEDO_DIM))
    col = t.cmix(t.math("MULTIPLY", cg, CONC_ALBEDO_MIX), base, COL_RUBBER)
    mulc = t.n("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
    t.pin_named(mulc, "Factor", 1.0)
    t.pin(mulc, 6, col)
    t.pin(mulc, 7, t.comb(dim, dim, dim))
    col = (mulc, 2)

    # --- roughness and the missing specular channel
    rgh = t.fmix(wg, rough, CONC_ROUGH_TARGET)
    # Specular IOR Level is F0 -- a property of the FRESNEL INTERFACE, so it
    # moves on TAU_IFACE, not on a monolayer. See TAU_IFACE_M.
    spc = t.fmix(ig, spec, CONC_SPEC_TARGET)

    # --- rubber FILLS texture. Both substrate stages come DOWN.
    fill = t.math("ADD", t.math("MULTIPLY", wg, CONC_FILL_WET),
                  t.math("MULTIPLY", cg, CONC_FILL_MASS))
    fill = t.math("MINIMUM", fill, 0.90)
    keep = t.math("SUBTRACT", 1.0, fill)
    hm_o = t.math("ADD", 0.5, t.math("MULTIPLY",
                                     t.math("SUBTRACT", hm, 0.5),
                                     t.math("SUBTRACT", 1.0,
                                            t.math("MULTIPLY", wg, 0.55))))
    hc_o = t.math("ADD", 0.5, t.math("MULTIPLY", t.math("SUBTRACT", hc, 0.5), keep))

    nrm = _dep_relief(t, "concrete", wg, P, "concrete")

    for nm, src in (("Base Color", col), ("Roughness", rgh),
                    ("Specular IOR Level", spc), ("Height Micro", hm_o),
                    ("Height Coarse", hc_o), ("Normal", nrm)):
        t.pin_named(gout, nm, src)
    return ng


def build_deck_group():
    """`TDP_Apply_BrushedMetal` — metallic -> dielectric, plus a roughness rise.

    On metal a rubber film is not a pigment: it is the end of the metal. The
    brush sheen dies because the specular lobe stops being a conductor's.
    """
    ng, gin, gout = _new_group(
        DECK_GROUP,
        (("Base Color", "NodeSocketColor", (0.048, 0.049, 0.053, 1.0)),
         ("Metallic", "NodeSocketFloat", 0.86),
         ("Roughness", "NodeSocketFloat", 0.40),
         ("Coverage", "NodeSocketFloat", 0.0),
         ("Interface", "NodeSocketFloat", 0.0),
         ("Wetting", "NodeSocketFloat", 0.0),
         ("Grain", "NodeSocketFloat", 1.0),
         ("World Position", "NodeSocketVector", None)),
        (("Base Color", "NodeSocketColor"),
         ("Metallic", "NodeSocketFloat"),
         ("Roughness", "NodeSocketFloat"),
         ("Normal", "NodeSocketVector")))
    t = _kit(ng)
    base = _o(gin, "Base Color")
    met = _o(gin, "Metallic")
    rough = _o(gin, "Roughness")
    cov = _o(gin, "Coverage")
    ifc = _o(gin, "Interface")
    wet = _o(gin, "Wetting")
    grain = _o(gin, "Grain")
    P = _o(gin, "World Position")

    wg = _wet_grain(t, wet, grain, lo=0.45)
    ig = _wet_grain(t, ifc, grain, lo=0.45)
    cg = t.math("MULTIPLY", cov, t.maprange(grain, 0.35, 1.0, 0.50, 1.0))

    # METALLIC IS AN INTERFACE EFFECT AND THIS IS THE ONE THE GATE CAUGHT.
    # Driven by wetting, a 10.6 nm tractive film was turning brushed metal into
    # a dielectric and the deck's film band measured +52.2 % against a launch
    # mark of +23.2 %. A 10 nm transfer film does not stop a metal being metal.
    met_o = t.math("MULTIPLY", met,
                   t.math("SUBTRACT", 1.0,
                          t.math("MULTIPLY", ig, DECK_METALLIC_KILL)))
    rgh = t.fmix(wg, rough, DECK_ROUGH_TARGET)
    col = t.cmix(t.math("MULTIPLY", cg, DECK_ALBEDO_MIX), base,
                 COL_RUBBER_ON_METAL)
    nrm = _dep_relief(t, "deck", wg, P, "deck")

    for nm, src in (("Base Color", col), ("Metallic", met_o),
                    ("Roughness", rgh), ("Normal", nrm)):
        t.pin_named(gout, nm, src)
    return ng


def build_floor_group():
    """`TDP_Apply_PolishedFloor` — roughness and coat, NEVER a pigment mix.

    R2-1214 is the trap and it is designed out rather than remembered: there is
    no colour input to mix toward in this graph at all. The only albedo term is
    `base * (1 - 0.10 * coverage)`, which is monotonically non-brightening for
    every possible base colour, so the "rubber lightens a dark floor" failure is
    unrepresentable here.
    """
    ng, gin, gout = _new_group(
        FLOOR_GROUP,
        (("Base Color", "NodeSocketColor", (0.044, 0.045, 0.050, 1.0)),
         ("Roughness", "NodeSocketFloat", 0.10),
         ("Specular IOR Level", "NodeSocketFloat", 0.55),
         ("Coat Weight", "NodeSocketFloat", 0.45),
         ("Coat Roughness", "NodeSocketFloat", 0.045),
         ("Coverage", "NodeSocketFloat", 0.0),
         ("Interface", "NodeSocketFloat", 0.0),
         ("Wetting", "NodeSocketFloat", 0.0),
         ("Grain", "NodeSocketFloat", 1.0),
         ("World Position", "NodeSocketVector", None)),
        (("Base Color", "NodeSocketColor"),
         ("Roughness", "NodeSocketFloat"),
         ("Specular IOR Level", "NodeSocketFloat"),
         ("Coat Weight", "NodeSocketFloat"),
         ("Coat Roughness", "NodeSocketFloat"),
         ("Normal", "NodeSocketVector")))
    t = _kit(ng)
    base = _o(gin, "Base Color")
    rough = _o(gin, "Roughness")
    spec = _o(gin, "Specular IOR Level")
    cw = _o(gin, "Coat Weight")
    cr = _o(gin, "Coat Roughness")
    cov = _o(gin, "Coverage")
    ifc = _o(gin, "Interface")
    wet = _o(gin, "Wetting")
    grain = _o(gin, "Grain")
    P = _o(gin, "World Position")

    wg = _wet_grain(t, wet, grain, lo=0.50)
    ig = _wet_grain(t, ifc, grain, lo=0.50)
    cg = t.math("MULTIPLY", cov, t.maprange(grain, 0.35, 1.0, 0.55, 1.0))

    dim = t.math("SUBTRACT", 1.0, t.math("MULTIPLY", cg, FLOOR_ALBEDO_DIM))
    mulc = t.n("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
    t.pin_named(mulc, "Factor", 1.0)
    t.pin(mulc, 6, base)
    t.pin(mulc, 7, t.comb(dim, dim, dim))
    col = (mulc, 2)

    rgh = t.fmix(wg, rough, FLOOR_ROUGH_TARGET)
    spc = t.fmix(ig, spec, FLOOR_SPEC_TARGET)
    # CAPPED suppression, and the coat gets ROUGHER rather than absent: the
    # specular return that holds these pixels off zero is spread, not removed.
    # The coat is not removed by a monolayer either: a film has to be thick
    # against a quarter wave before it is the new top interface.
    cw_o = t.math("MULTIPLY", cw,
                  t.math("SUBTRACT", 1.0,
                         t.math("MULTIPLY", ig, FLOOR_COAT_SUPPRESS)))
    cr_o = t.fmix(wg, cr, FLOOR_COAT_ROUGH_TARGET)
    nrm = _dep_relief(t, "floor", wg, P, "floor")

    for nm, src in (("Base Color", col), ("Roughness", rgh),
                    ("Specular IOR Level", spc), ("Coat Weight", cw_o),
                    ("Coat Roughness", cr_o), ("Normal", nrm)):
        t.pin_named(gout, nm, src)
    return ng


def build_groups():
    """All four node groups. Idempotent."""
    return (build_field_group(), build_concrete_group(),
            build_deck_group(), build_floor_group())


# ===========================================================================
# 8.  SUBSTRATE REPLICAS — for the gate, and only for the gate
# ===========================================================================
#
# These are REDUCED replicas of three materials this module does not own:
# `M_Surf_Concrete` (world/build_surface.py), `TurntableTop` and `FloorPolished`
# (/home/zany/opus5-car-render/build/s03_materials.py, read-only). They carry
# the same Principled parameters and the same measured self-variation -- in
# particular the concrete's +-14.5 % per-bay tone hash, because THAT is the
# number the deposit's % deviation has to beat -- so a delta measured here is
# comparable to the -5.73 % measured on the real apron. They are not a
# re-authoring of anything and nothing outside this file ever sees them.

BAY_X, BAY_Y = 4.5, 4.0
BAY_TONE_PP = 0.145               # measured: mat_slab's per-bay hash, +-14.5 %


def _bay_tone(t, P):
    """`build_surface`'s per-bay tone chequer, at its own 4.5 x 4.0 m pitch."""
    x = t.sep(P, 0)
    y = t.sep(P, 1)
    bx = t.math("FLOOR", t.math("DIVIDE", x, BAY_X))
    by = t.math("FLOOR", t.math("DIVIDE", t.math("ADD", y, 2.0), BAY_Y))
    h = t.noise(t.comb(bx, by, 2.0), scale=1.0, detail=1.0, rough=0.5)
    return t.maprange(h, 0.0, 1.0, 1.0 - BAY_TONE_PP, 1.0 + BAY_TONE_PP)


def _concrete_substrate(t, P):
    """base colour, roughness, spec, h_micro, h_coarse — the replica."""
    broom = t.wave(P, wavelength_m=0.018, distortion=0.6,
                   detail=detail_for(0.018), direction="Y")
    # the 2.29 mm micro stage at ITS OWN declared wavelength. The real material
    # drives this off a 6 mm Voronoi, which is both below the band and the most
    # expensive node in that tree; the replica states the wavelength it is
    # actually claiming, and every arm shares it identically.
    grit = t.noise(P, wavelength_m=0.00229, detail=0.0, rough=0.5)
    macro = t.noise(P, wavelength_m=0.220, detail=detail_for(0.220), rough=0.60)
    base = t.ramp(macro, [(0.30, (0.2450, 0.2410, 0.2300)),
                          (0.62, (0.2980, 0.2930, 0.2810)),
                          (0.92, (0.3380, 0.3320, 0.3190))])
    tone = _bay_tone(t, P)
    mulc = t.n("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
    t.pin_named(mulc, "Factor", 1.0)
    t.pin(mulc, 6, base)
    t.pin(mulc, 7, t.comb(tone, tone, tone))
    base = (mulc, 2)
    rough = t.math("ADD", 0.80, t.math("MULTIPLY",
                                       t.maprange(broom, 0.2, 0.8, -0.07, 0.07),
                                       1.0))
    h_micro = t.maprange(grit, 0.20, 0.80, 0.0, 1.0)
    h_coarse = t.math("ADD", t.math("MULTIPLY", broom, 0.5),
                      t.math("MULTIPLY", t.maprange(macro, 0.2, 0.8, 0.0, 1.0),
                             0.5))
    return base, rough, 0.32, h_micro, h_coarse


def _deck_substrate(t, P):
    """`TurntableTop`: dark circular-brushed metal. Rings on the OBJECT
    coordinate, exactly as s03_materials builds it -- the deck spins, so its
    brush lay is in object space even though the deposit is world-locked. That
    difference is the reason this module transforms explicitly."""
    obj = t.object_coords()
    rings = t.n("ShaderNodeTexWave", wave_type="RINGS", rings_direction="Z",
                wave_profile="SIN")
    t.pin_named(rings, "Vector", obj)
    _set_named(rings, "Scale", 55.0)
    _set_named(rings, "Distortion", 1.4)
    _set_named(rings, "Detail", 3.0)
    fine = t.n("ShaderNodeTexWave", wave_type="RINGS", rings_direction="Z",
               wave_profile="SAW")
    t.pin_named(fine, "Vector", obj)
    _set_named(fine, "Scale", 260.0)
    _set_named(fine, "Distortion", 2.5)
    _set_named(fine, "Detail", 1.0)
    mix = t.cmix(0.40, _o(rings, "Color"), _o(fine, "Color"))
    rgh = t.ramp(mix, [(0.20, (0.335, 0.335, 0.335)),
                       (0.82, (0.455, 0.455, 0.455))])
    # AN RGB NODE, NOT A LITERAL TUPLE. Returning the measured base colour as a
    # bare 3-tuple worked everywhere it was pinned into a Color socket and blew
    # up the moment the field probe pinned it into a FLOAT one:
    # `NodeSocketFloat.default_value expected a float type, not tuple`. A value
    # that is sometimes a node and sometimes a literal cannot be handed to a
    # generic sink; every channel this file passes around is a link.
    col = t.n("ShaderNodeRGB")
    col.outputs[0].default_value = (0.048, 0.049, 0.053, 1.0)
    return _o(col, "Color"), 0.86, rgh


def _floor_substrate(t, P):
    """`FloorPolished`: base ramp linear 0.030-0.068, roughness 0.055-0.155."""
    obj = t.object_coords()
    n1 = t.noise(obj, scale=2.4 * 0.09, detail=3.0, rough=0.55)
    r1 = t.ramp(n1, [(0.34, (0.055, 0.055, 0.055)), (0.70, (0.155, 0.155, 0.155))])
    spk = t.noise(obj, scale=38.0 * 0.09, detail=2.0, rough=0.75)
    base = t.ramp(spk, [(0.52, (0.030, 0.032, 0.036)),
                        (0.63, (0.058, 0.060, 0.068))])
    return base, r1, 0.55, 0.45, 0.045


# ---------------------------------------------------------------- materials --

def mat_concrete(arm="deposit", front_value=None, passes=None):
    """`TDP_M_Concrete_<arm>`. arm: control | deposit | traffic | existing."""
    t = K.NT("%sM_Concrete_%s" % (PFX, arm))
    P = world_position(t)
    base, rough, spec, hm, hc = _concrete_substrate(t, P)
    nrm = None
    if arm in ("deposit", "traffic"):
        f = field_node(t, front_value=front_value,
                       passes=FILM_TRAFFIC_SWEEP if arm == "traffic"
                       else passes)
        g = t.n("ShaderNodeGroup",
                node_tree=bpy.data.node_groups[CONC_GROUP])
        for nm, src in (("Base Color", base), ("Roughness", rough),
                        ("Specular IOR Level", spec), ("Height Micro", hm),
                        ("Height Coarse", hc),
                        ("Coverage", _o(f, "Coverage")),
                        ("Interface", _o(f, "Interface")),
                        ("Wetting", _o(f, "Wetting")),
                        ("Grain", _o(f, "Grain")), ("World Position", P)):
            t.pin_named(g, nm, src)
        base = _o(g, "Base Color")
        rough = _o(g, "Roughness")
        spec = _o(g, "Specular IOR Level")
        hm = _o(g, "Height Micro")
        hc = _o(g, "Height Coarse")
        nrm = _o(g, "Normal")
    elif arm == "existing":
        # build_surface.py:2835-2841 + :2884 as the baseline arm. u = world y,
        # t = world x - 15 on this span.
        #
        # ONE TERM IS OMITTED, AND IT IS OMITTED IN THE EXISTING PAINT'S FAVOUR.
        # The real line also multiplies `launch` by `mr(stain, 0.3, 0.8, 0.4,
        # 1.0)` -- a stain field this reduced replica does not carry, whose mean
        # over its own remap is about 0.7. Dropping it makes this arm roughly
        # 40 % STRONGER than what `build_surface` actually renders. The baseline
        # the new work is scored against is therefore a generous one, which is
        # the right direction for a number the author of the new thing reports.
        x = t.sep(P, 0)
        y = t.sep(P, 1)
        u = t.math("ABSOLUTE", y)
        tt = t.math("SUBTRACT", x, 15.0)
        launch = t.maprange(t.math("ABSOLUTE", t.math("SUBTRACT", u, 0.72)),
                            0.10, 0.32, 1.0, 0.0)
        launch = t.math("MULTIPLY", launch, t.maprange(tt, 0.0, 34.0, 1.0, 0.0))
        base = t.cmix(t.math("MULTIPLY", launch, 0.55), base, COL_RUBBER)
        rough = t.math("SUBTRACT", rough,
                       t.math("MULTIPLY", launch, 0.18))
    # the substrate's own two bump stages, at the measured wavelengths
    nrm = t.bump(hm, 0.45, normal=nrm,
                 modulation_pp=K.modulation_for_amplitude(0.27, 0.00229),
                 wavelength_m=0.00229, height_pp=1.0)
    nrm = t.bump(hc, 1.0, normal=nrm,
                 modulation_pp=K.modulation_for_amplitude(3.00, 0.02411),
                 wavelength_m=0.02411, height_pp=1.0)
    b = t.principled_out(base_color=base, roughness=rough, metallic=0.0)
    t.pin_named(b, "Specular IOR Level", spec)
    t.pin_named(b, "Normal", nrm)
    return t.m


def mat_deck(arm="deposit", front_value=None, passes=None):
    t = K.NT("%sM_Deck_%s" % (PFX, arm))
    P = world_position(t)
    base, met, rough = _deck_substrate(t, P)
    nrm = None
    if arm in ("deposit", "traffic"):
        f = field_node(t, front_value=front_value,
                       passes=FILM_TRAFFIC_SWEEP if arm == "traffic" else passes)
        g = t.n("ShaderNodeGroup", node_tree=bpy.data.node_groups[DECK_GROUP])
        for nm, src in (("Base Color", base), ("Metallic", met),
                        ("Roughness", rough),
                        ("Coverage", _o(f, "Coverage")),
                        ("Interface", _o(f, "Interface")),
                        ("Wetting", _o(f, "Wetting")),
                        ("Grain", _o(f, "Grain")), ("World Position", P)):
            t.pin_named(g, nm, src)
        base = _o(g, "Base Color")
        met = _o(g, "Metallic")
        rough = _o(g, "Roughness")
        nrm = _o(g, "Normal")
    b = t.principled_out(base_color=base, roughness=rough)
    t.pin_named(b, "Metallic", met)
    t.pin_named(b, "Anisotropic", 0.0)
    t.pin_named(b, "Normal", nrm)
    return t.m


def mat_floor(arm="deposit", front_value=None, passes=None):
    t = K.NT("%sM_Floor_%s" % (PFX, arm))
    P = world_position(t)
    base, rough, spec, cw, cr = _floor_substrate(t, P)
    nrm = None
    if arm in ("deposit", "traffic"):
        f = field_node(t, front_value=front_value,
                       passes=FILM_TRAFFIC_SWEEP if arm == "traffic" else passes)
        g = t.n("ShaderNodeGroup", node_tree=bpy.data.node_groups[FLOOR_GROUP])
        for nm, src in (("Base Color", base), ("Roughness", rough),
                        ("Specular IOR Level", spec), ("Coat Weight", cw),
                        ("Coat Roughness", cr),
                        ("Coverage", _o(f, "Coverage")),
                        ("Interface", _o(f, "Interface")),
                        ("Wetting", _o(f, "Wetting")),
                        ("Grain", _o(f, "Grain")), ("World Position", P)):
            t.pin_named(g, nm, src)
        base = _o(g, "Base Color")
        rough = _o(g, "Roughness")
        spec = _o(g, "Specular IOR Level")
        cw = _o(g, "Coat Weight")
        cr = _o(g, "Coat Roughness")
        nrm = _o(g, "Normal")
    b = t.principled_out(base_color=base, roughness=rough, metallic=0.0)
    t.pin_named(b, "Specular IOR Level", spec)
    t.pin_named(b, "IOR", 1.52)
    t.pin_named(b, "Coat Weight", cw)
    t.pin_named(b, "Coat Roughness", cr)
    t.pin_named(b, "Normal", nrm)
    return t.m


# --------------------------------------------------------------- probes ------

def mat_probe(name, chans, front_value=None):
    """An EMISSION material that emits three shader FIELDS as R, G, B.

    This is how the gate measures roughness rather than asserting it: the
    roughness expression is rendered, at one sample with no bounces and a
    Standard view transform, into a linear EXR. `chans` is a callable taking
    the NT and the world position and returning three (node, socket) floats.
    """
    t = K.NT(PFX + "P_" + name)
    P = world_position(t)
    r, g, b = chans(t, P, front_value)
    e = t.n("ShaderNodeEmission")
    t.pin_named(e, "Color", t.comb(r, g, b))
    t.pin_named(e, "Strength", 1.0)
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(e.outputs[0], out.inputs["Surface"])
    return t.m


def _field_probe_chans(t, P, front_value):
    f = field_node(t, front_value=front_value)
    return _o(f, "Density"), _o(f, "Interface"), _o(f, "Wetting")


def _conc_rough_chans_factory(arm):
    def chans(t, P, front_value):
        base, rough, spec, hm, hc = _concrete_substrate(t, P)
        if arm in ("deposit", "traffic"):
            f = field_node(t, front_value=front_value,
                           passes=FILM_TRAFFIC_SWEEP if arm == "traffic" else None)
            g = t.n("ShaderNodeGroup", node_tree=bpy.data.node_groups[CONC_GROUP])
            for nm, src in (("Base Color", base), ("Roughness", rough),
                            ("Specular IOR Level", spec), ("Height Micro", hm),
                            ("Height Coarse", hc),
                            ("Coverage", _o(f, "Coverage")),
                            ("Interface", _o(f, "Interface")),
                            ("Wetting", _o(f, "Wetting")),
                            ("Grain", _o(f, "Grain")), ("World Position", P)):
                t.pin_named(g, nm, src)
            return _o(g, "Roughness"), _o(g, "Specular IOR Level"), _o(g, "Height Coarse")
        if arm == "existing":
            x = t.sep(P, 0)
            u = t.math("ABSOLUTE", t.sep(P, 1))
            tt = t.math("SUBTRACT", x, 15.0)
            launch = t.maprange(t.math("ABSOLUTE", t.math("SUBTRACT", u, 0.72)),
                                0.10, 0.32, 1.0, 0.0)
            launch = t.math("MULTIPLY", launch, t.maprange(tt, 0.0, 34.0, 1.0, 0.0))
            rough = t.math("SUBTRACT", rough, t.math("MULTIPLY", launch, 0.18))
        return rough, spec, hc
    return chans


def _deck_rough_chans_factory(arm):
    def chans(t, P, front_value):
        base, met, rough = _deck_substrate(t, P)
        if arm in ("deposit", "traffic"):
            f = field_node(t, front_value=front_value,
                           passes=FILM_TRAFFIC_SWEEP if arm == "traffic" else None)
            g = t.n("ShaderNodeGroup", node_tree=bpy.data.node_groups[DECK_GROUP])
            for nm, src in (("Base Color", base), ("Metallic", met),
                            ("Roughness", rough),
                            ("Coverage", _o(f, "Coverage")),
                            ("Interface", _o(f, "Interface")),
                            ("Wetting", _o(f, "Wetting")),
                            ("Grain", _o(f, "Grain")), ("World Position", P)):
                t.pin_named(g, nm, src)
            return _o(g, "Roughness"), _o(g, "Metallic"), _o(g, "Base Color")
        return rough, met, base
    return chans


def _floor_rough_chans_factory(arm):
    def chans(t, P, front_value):
        base, rough, spec, cw, cr = _floor_substrate(t, P)
        if arm in ("deposit", "traffic"):
            f = field_node(t, front_value=front_value,
                           passes=FILM_TRAFFIC_SWEEP if arm == "traffic" else None)
            g = t.n("ShaderNodeGroup", node_tree=bpy.data.node_groups[FLOOR_GROUP])
            for nm, src in (("Base Color", base), ("Roughness", rough),
                            ("Specular IOR Level", spec), ("Coat Weight", cw),
                            ("Coat Roughness", cr),
                            ("Coverage", _o(f, "Coverage")),
                            ("Interface", _o(f, "Interface")),
                            ("Wetting", _o(f, "Wetting")),
                            ("Grain", _o(f, "Grain")), ("World Position", P)):
                t.pin_named(g, nm, src)
            return _o(g, "Roughness"), _o(g, "Coat Weight"), _o(g, "Coat Roughness")
        return rough, cw, cr
    return chans


# ===========================================================================
# 9.  THE STANDALONE SCENE
# ===========================================================================
#
# One plane per substrate, at the world station the substrate really occupies,
# and -- for the deck -- carrying the real 12 deg yaw so that the world-space
# transform is genuinely exercised rather than being an identity. Tiny: two
# triangles, a sun and a camera. Nothing here opens a film blend.

#: THE 4K PIXEL LAW IS PRESERVED EXACTLY; ONLY THE PATH-TRACED REGION IS CUT.
#:
#: `resolution_x` stays 3840 and the measured scale stays 2.705 mm/px on the
#: apron -- against the staging doc's own apron-near p50 of 2.73 mm/px -- so
#: every pixel figure in this gate is a real 4K pixel figure. What the border
#: does is stop Cycles tracing the 66 % of the frame that carries no deposit
#: and no measurement.
#:
#: The reason is the machine, and it is worth writing down rather than hiding:
#: this box has SIX cores, `nvidia-smi` cannot open its GPU today ("Unable to
#: determine the device handle for GPU0"), and three other agents' item gates
#: were rendering on it throughout. A full 4K frame of the concrete arm was
#: taking of the order of half an hour under that load. R2-020's rule is that
#: the RESOLUTION must not be quietly halved -- 11 of 28 wave-1 heroes shipped
#: at 1920 and were scored as 3840. Cropping the traced region does not touch
#: the resolution or the pixel law; halving `resolution_x` would.
RENDER_BORDER = (0.28, 0.72, 0.02, 0.80)     # min_x, max_x, min_y, max_y

SUBSTRATES = {
    "concrete": dict(
        centre=(32.0, 0.0, 0.0), yaw_deg=0.0, size=(40.0, 20.0),
        graze_deg=30.0, lens=35.0, dist=10.1,
        note="the access-road apron, world x = 15..49; the frames it is judged "
             "on are 981/973/965/1030 at 26.8-44.1 deg",
        band=(0.6720, 0.9230)),
    "deck": dict(
        centre=(0.0, 0.0, DECK_Z), yaw_deg=DECK_YAW_DEG, size=(24.0, 14.0),
        graze_deg=30.0, lens=35.0, dist=4.9,
        note="Turntable_Deck. The FILM sees this at 3.5 deg for five frames "
             "(837-841); 30 deg here is a diagnostic angle, stated as such",
        band=(0.6720, 0.9230)),
    "floor": dict(
        centre=(10.5, 0.0, 0.0), yaw_deg=0.0, size=(48.0, 28.0),
        graze_deg=25.0, lens=35.0, dist=12.4,
        note="the showroom floor between the ramp foot and the glass. Only the "
             "tractive film lands here; no launch mark does",
        band=(0.6720, 0.9230)),
}


def _plane(name, centre, yaw_deg, size, coll):
    """A two-triangle plane whose OBJECT space is not world space."""
    hx, hy = 0.5 * size[0], 0.5 * size[1]
    verts = [(-hx, -hy, 0.0), (hx, -hy, 0.0), (hx, hy, 0.0), (-hx, hy, 0.0)]
    # orient=False: a ground plane is DELIBERATELY one-sided and knows which
    # side it wants (+Z). `orient_outward` on a single quad has no interior to
    # reason about, so it would be a coin toss on the face the sun lands on.
    me, off = K.new_mesh(name, verts, quads=[(0, 1, 2, 3)], smooth_deg=0.0,
                         orient=False)
    if max(abs(v) for v in off) > 1e-9:
        raise RuntimeError("plane %s was recentred by %s; it was already "
                           "centred on its own origin" % (name, off))
    ob = bpy.data.objects.new(name, me)
    ob.location = tuple(float(v) for v in centre)
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = (0.0, 0.0, math.radians(float(yaw_deg)))
    coll.objects.link(ob)
    return ob


def build(scene=None, test_scene=False, samples=192, substrate="concrete",
          arm="deposit", stats=None):
    """Build the standalone gate scene for one substrate. Returns a dict.

    Deliberately NOT a film builder. It makes one plane, one sun, one camera
    and the four node groups, and nothing it makes is ever appended anywhere.
    """
    K._require_bpy("build")
    scene = scene or bpy.context.scene
    st = stats if stats is not None else {}
    K.purge(PFX, COLL)
    _empty_the_scene()
    cfg = SUBSTRATES[substrate]
    root = K.coll(COLL)

    build_groups()
    ob = _plane(PFX + "Ground_" + substrate, cfg["centre"], cfg["yaw_deg"],
                cfg["size"], root)
    mats = {
        "concrete": mat_concrete, "deck": mat_deck, "floor": mat_floor,
    }[substrate]
    ob.data.materials.append(mats(arm))

    if test_scene:
        K.contract_sun(PFX, scene=scene, coll_=root, sky=True)
        g = math.radians(cfg["graze_deg"])
        d = cfg["dist"]
        cx, cy, cz = cfg["centre"]
        loc = (cx + d * math.cos(g), cy, cz + d * math.sin(g))
        cam, dist, ppm = K.macro_rig(PFX + "Cam_" + substrate, loc,
                                     (cx, cy, cz), cfg["lens"], root,
                                     scene=scene, samples=samples)
        scene.view_settings.view_transform = C.VIEW_TRANSFORM
        scene.view_settings.exposure = FILM_EXPOSURE
        scene.render.use_border = True
        scene.render.use_crop_to_border = True
        (scene.render.border_min_x, scene.render.border_max_x,
         scene.render.border_min_y, scene.render.border_max_y) = RENDER_BORDER
        st.update(camera=cam.name, distance_m=dist, px_per_m=ppm,
                  mm_per_px=1000.0 / ppm, border=list(RENDER_BORDER),
                  traced_px=[int(3840 * (RENDER_BORDER[1] - RENDER_BORDER[0])),
                             int(2160 * (RENDER_BORDER[3] - RENDER_BORDER[2]))])
    st.update(substrate=substrate, arm=arm, object=ob.name,
              groups=[FIELD_GROUP, CONC_GROUP, DECK_GROUP, FLOOR_GROUP])
    strays = [o.name for o in scene.objects if not o.name.startswith(PFX)]
    if strays:
        raise RuntimeError(
            "REFUSING: %s are in the measurement scene and this module did not "
            "make them. Everything the camera can see has to be this item or "
            "the numbers are about something else." % strays)
    K.assert_no_external_assets()
    return root


def _empty_the_scene():
    """Delete everything this module did not make. `--factory-startup` IS NOT
    AN EMPTY SCENE, and here it cost a whole substrate's gate.

    A factory-startup file contains a 2 m **Cube at the world origin**, a point
    Light and a Camera. `K.purge(PFX, COLL)` deliberately only removes THIS
    item's datablocks -- a purge that took anything else would delete another
    module's sun, which is a documented way to get a black acceptance render.
    So the Cube survives, and the turntable deck's measurement scene is centred
    on (0, 0, 0.340), which is exactly where the Cube is.

    MEASURED, not inferred: with a probe material emitting a constant 0.86 into
    the green channel, 99.7 % of the deck frame came back at a MEAN of 5.390 and
    a MAX of 12.17 -- the default Cube, lit by the default Light, filling the
    frame in front of the plane. Every deck figure in the first two gate runs is
    a photograph of that Cube: mask 70.54 % of frame (the band is ~12 %),
    "Roughness" 9.82 against a real 0.40, "Metallic" 7.27 against a real 0.86.
    The concrete scene sits at x = 32 and the floor at x = 10.5, so the Cube was
    far off-centre there and the bug stayed invisible for a whole substrate.

    `itemkit.emitted_wavelength_m` already carries this warning in prose -- "the
    default Cube once sat between an ortho camera and a measurement plane and
    returned one identical number for fourteen different stages". It is a
    refusal here instead, plus the `strays` check in `build()`.
    """
    for ob in list(bpy.data.objects):
        if not ob.name.startswith(PFX):
            bpy.data.objects.remove(ob, do_unlink=True)


# ===========================================================================
# 10.  INTERFACE
# ===========================================================================

def interface_json(path=None):
    return K.interface_json(
        ITEM, path,
        node_groups=dict(field=FIELD_GROUP, concrete=CONC_GROUP,
                         brushed_metal=DECK_GROUP, polished_floor=FLOOR_GROUP),
        field_inputs=[n for n, _t, _d in FIELD_INPUTS],
        field_outputs=[n for n, _t in FIELD_OUTPUTS],
        coordinate="WORLD metres, via TexCoord->Object + VectorTransform "
                   "POINT OBJECT->WORLD. Valid only for |x| <= %.1f m." % FILM_X_END,
        launch_mark=dict(x0=MARK_X0, x1=MARK_X1, length_m=MARK_LEN,
                         abs_y=HALF_TRACK_REAR, patch_width_m=PATCH_W,
                         deck_z=DECK_Z, terminal=MARK_TERMINAL,
                         first_frame=FIRST_DEPOSIT_FRAME,
                         last_frame=LAST_DEPOSIT_FRAME),
        time_gate=dict(socket="Front X", keys=FRONT_X_KEYS,
                       bind="tyre_deposit.bind_time(value_node)"),
        film=dict(x_start=MARK_X1, x_end=FILM_X_END,
                  kappa_min=float(FILM_K.min()), kappa_max=float(FILM_K.max()),
                  slid_over_15_49_m=FILM["slid_cal_m"],
                  slid_over_span_m=FILM["slid_span_m"],
                  density=FILM_DENSITY_PEAK),
        saturation=dict(tau_cover=TAU_COVER, tau_wet=TAU_WET,
                        tau_iface=TAU_IFACE, tau_iface_m=TAU_IFACE_M,
                        transfer_m_per_m=TRANSFER_M_PER_M,
                        launch_peak_areal_m_per_m2=LAUNCH_PEAK_AREAL,
                        launch_mean_areal_m_per_m2=LAUNCH_MEAN_AREAL,
                        film_areal_m_per_m2=FILM_CAL_AREAL),
        relief=[dict(name=r["name"], wavelength_m=r["wavelength_m"],
                     amp_mm=r["amp_mm"], m=r["m"], band=r["band"])
                for r in relief_rows(verbose=False)],
        octave_window_m=[BAND_LO, BAND_HI],
        instances={k: {kk: vv for kk, vv in v.items()} for k, v in PARAMS.items()},
        note="NOT WIRED INTO THE FILM. Nothing ships until a 4K A/B is approved.")


# ===========================================================================
# 11.  SELFTEST — measured, not asserted; runs without bpy
# ===========================================================================

def selftest(verbose=True):
    fails, n = [], [0]

    def chk(name, ok, detail=""):
        n[0] += 1
        if not ok:
            fails.append(name)
        if verbose:
            print("  %-52s %-4s %s" % (name, "PASS" if ok else "FAIL", detail))

    print("\n[1] THE GROUND TRUTH, AND ONE PLACE THE JSON CONTRADICTS ITSELF")
    chk("the mark is read from the JSON, not typed",
        abs(MARK_X1 - MARK_X0 - MARK_LEN) < 1e-9,
        "x %.5f -> %.5f, length %.4f m, |y| %.5f, patch %.1f mm, z %.3f"
        % (MARK_X0, MARK_X1, MARK_LEN, HALF_TRACK_REAR, PATCH_W * 1000, DECK_Z))
    dec = [round(d, 3) for _f, _x, d in LAUNCH_FRAMES]
    want = [1.0, 0.954, 0.794, 0.646, 0.507, 0.381, 0.267, 0.168, 0.086, 0.027]
    chk("the decade is the staging doc's decade",
        all(abs(a - b) < 6e-4 for a, b in zip(dec, want)) and len(dec) == 10,
        "%s" % dec)
    prof = TR["launch_mark_profile"]["RL"]["deposit_norm"]
    chk("[FINDING] the 256-point resample CONTRADICTS decay_note",
        abs(prof[-1]) < 1e-9 and MARK_TERMINAL > 0.02,
        "resample's last sample is %.5f but `terminal_deposit_norm` is %.5f and "
        "`decay_note` says the mark 'terminates ... not a fade'. The resampler "
        "fades the last %.1f mm to zero. This module uses the PER-FRAME arrays."
        % (prof[-1], MARK_TERMINAL,
           1000.0 * MARK_LEN * (1.0 - float(np.argmax(np.array(prof) <= 0.0267))
                                / (len(prof) - 1.0))))
    chk("the profile ramp is monotone and terminates at 2.7 %",
        all(LAUNCH_STOPS[i][1] >= LAUNCH_STOPS[i + 1][1]
            for i in range(len(LAUNCH_STOPS) - 1))
        and abs(LAUNCH_STOPS[-1][1] - MARK_TERMINAL) < 1e-9,
        "%d stops, peak %.3f, terminal %.5f, hard edges %.0f-%.0f mm"
        % (len(LAUNCH_STOPS), LAUNCH_STOPS[0][1], LAUNCH_STOPS[-1][1],
           1000 * min(p["edge"] for p in PARAMS.values()),
           1000 * max(p["edge"] for p in PARAMS.values())))

    print("\n[2] THE TRACTIVE FILM, DERIVED — and the brief's arithmetic")
    chk("kappa lands inside the 2-8 % band the brief names",
        0.02 <= FILM["kappa_cal_min"] and FILM["kappa_cal_max"] <= 0.08,
        "mu_used %.4f..%.4f (p50 %.4f) -> kappa %.5f..%.5f over x=15..49"
        % (FILM["mu_cal_min"], FILM["mu_cal_max"], FILM["mu_cal_p50"],
           FILM["kappa_cal_min"], FILM["kappa_cal_max"]))
    chk("the calibration hits 1 m of slid tyre surface",
        abs(FILM["slid_cal_m"] - FILM_CAL_SLID_M) < 1e-6,
        "%.6f m over x=15..49 (%.4f m of track); %.5f m over the whole "
        "straight drive-out" % (FILM["slid_cal_m"], FILM["track_len_cal_m"],
                                FILM["slid_span_m"]))
    chk("the implied slip stiffness is physical once downforce is allowed",
        20.0 <= FILM["implied_slip_stiffness_vs_weight"] / 2.0 <= 35.0,
        "C_kappa/Fz = %.1f against the car's WEIGHT; at 16-31 m/s the real rear "
        "load is ~2x static, giving %.1f -- the top of the 15-30 slick range"
        % (FILM["implied_slip_stiffness_vs_weight"],
           FILM["implied_slip_stiffness_vs_weight"] / 2.0))
    ratio_mean = LAUNCH_MEAN_AREAL / FILM_CAL_AREAL
    ratio_peak = LAUNCH_PEAK_AREAL / FILM_CAL_AREAL
    chk("[FINDING] the areal ratio is 1/460, not the brief's 1/140",
        400.0 < ratio_mean < 520.0,
        "launch %.3f m/m2 mean (%.3f peak) vs film %.5f m/m2 -> 1/%.1f of the "
        "mean, 1/%.1f of the peak. The brief's 1/140 is 34/0.2416, the LENGTH "
        "dilution with its own 0.30 mass factor dropped."
        % (LAUNCH_MEAN_AREAL, LAUNCH_PEAK_AREAL, FILM_CAL_AREAL,
           ratio_mean, ratio_peak))
    k = np.asarray(FILM_K)
    cal = (np.asarray(FILM_X) >= 15.0) & (np.asarray(FILM_X) <= 49.0)
    spread = float(k[cal].max() / k[cal].min() - 1.0)
    chk("[FINDING] the derived film is FLAT over x=15..49 — there is no falloff",
        spread < 0.005,
        "kappa varies by %.3f %% across the span the existing paint ramps "
        "LINEARLY from 1.0 to 0.0 over. The existing falloff is not weak, it is "
        "the wrong shape." % (100.0 * spread))

    print("\n[3] THE THREE SATURATION LAWS")
    chk("the launch patch reads as a mark and the film does not",
        coverage(1.0) > 0.95 and coverage(FILM_DENSITY_CAL) < 0.01,
        "coverage: launch peak %.4f, launch terminal %.4f, film %.5f"
        % (coverage(1.0), coverage(MARK_TERMINAL), coverage(FILM_DENSITY_CAL)))
    chk("the film IS wetted, which is where its read comes from",
        0.6 < wetting(FILM_DENSITY_CAL) < 0.95 and wetting(1.0) > 0.999,
        "wetting: launch peak %.4f, film %.4f; tau_cover %.5f, tau_wet %.3e"
        % (wetting(1.0), wetting(FILM_DENSITY_CAL), TAU_COVER, TAU_WET))
    chk("[FINDING] the interface scale, which the gate had to teach me",
        interface(1.0) > 0.999 and interface(FILM_DENSITY_CAL) < 0.15,
        "metallic / specular / coat move on TAU_IFACE = %.1f nm (a quarter "
        "wave), NOT on the monolayer: launch %.4f, film %.4f. Driven by "
        "wetting instead, a %.1f nm tractive film turned brushed metal into a "
        "dielectric and the deck's film band measured +52.2 %% against a launch "
        "mark of +23.2 %%."
        % (1e9 * TAU_IFACE_M, interface(1.0), interface(FILM_DENSITY_CAL),
           1e9 * FILM_DENSITY_CAL * LAUNCH_PEAK_AREAL * TRANSFER_M_PER_M))
    chk("the taus come from a film THICKNESS, not from taste",
        abs(TAU_COVER - TAU_OPTICAL_M / (LAUNCH_PEAK_AREAL * TRANSFER_M_PER_M)) < 1e-12,
        "launch peak = %.2f um of rubber, film = %.2f nm; optical tau %.1f um, "
        "wetting tau %.1f nm"
        % (1e6 * LAUNCH_PEAK_AREAL * TRANSFER_M_PER_M,
           1e9 * FILM_DENSITY_CAL * LAUNCH_PEAK_AREAL * TRANSFER_M_PER_M,
           1e6 * TAU_OPTICAL_M, 1e9 * TAU_WET_M))

    print("\n[4] THE OCTAVE LAW")
    rows = relief_rows()
    chk("every authored relief stage is inside 12-300 mm",
        all(r["in_window"] for r in rows),
        "%d stages, %.1f-%.1f mm"
        % (len(rows), 1000 * min(r["wavelength_m"] for r in rows),
           1000 * max(r["wavelength_m"] for r in rows)))
    chk("every authored relief stage is inside its named RELIEF_BANDS band",
        all(r["verdict"] == "ok" for r in rows),
        "%s" % [(r["name"], r["verdict"]) for r in rows if r["verdict"] != "ok"]
        or "all ok")
    lams = [lam for _n, lam, _d in FIELD_STRUCTURE] + \
           [lam for st in RELIEF.values() for _n, lam, _m, _b, _s in st]
    fin = [(lam, lam / 2.0 ** detail_for(lam)) for lam in lams]
    chk("[FINDING] no fractal in this file emits an octave below the band",
        all(f >= BAND_LO - 1e-9 for _l, f in fin),
        "finest octave over all %d textures is %.2f mm against a %.0f mm floor. "
        "At the house default detail=6 the 120 mm scuff alone would also be "
        "emitting a %.2f mm octave -- invisible at every resolution this film is "
        "graded at, and most of the CPU cost of a 4K frame."
        % (len(fin), 1000 * min(f for _l, f in fin), 1000 * BAND_LO,
           1000 * 0.120 / 64.0))
    chk("every field STRUCTURE wavelength is inside 12-300 mm",
        all(BAND_LO <= lam <= BAND_HI for _n, lam, _d in FIELD_STRUCTURE),
        "%s" % [(n, round(1000 * lam, 1)) for n, lam, _d in FIELD_STRUCTURE])
    # PARSED, not grepped: every `.bump(...)` call in this file must take
    # `modulation_pp=` and must NOT take `distance=`. A grep cannot tell the
    # difference between code and the docstring that quotes build_surface's.
    import ast
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    bumps, bad = 0, []
    for nd in ast.walk(ast.parse(src)):
        if (isinstance(nd, ast.Call) and isinstance(nd.func, ast.Attribute)
                and nd.func.attr == "bump"):
            bumps += 1
            kw = {k.arg for k in nd.keywords}
            if "distance" in kw or "modulation_pp" not in kw:
                bad.append(nd.lineno)
    chk("every bump() call states a modulation, never a distance",
        bumps > 0 and not bad,
        "%d bump() calls parsed, %d with a typed distance= (lines %s). "
        "Amplitudes come only from K.relief_amplitude_for / "
        "K.modulation_for_amplitude." % (bumps, len(bad), bad))
    for nm, lam, amp_m, cut in SUBSTRATE_STAGES:
        m = K.modulation_for_amplitude(amp_m * 1000.0, lam)
        print("    substrate  %-30s lam %7.2f mm  amp %6.3f mm  m %6.3f  "
              "reduced by up to %.0f %%" % (nm, lam * 1000, amp_m * 1000, m,
                                            100 * cut))
    chk("the substrate stages this module modulates were MEASURED, not guessed",
        abs(K.modulation_for_amplitude(0.27, 0.00229) - 3.15) < 0.02
        and abs(K.modulation_for_amplitude(3.00, 0.02411) - 3.29) < 0.02,
        "reproduces the staging doc's reported m = 3.15 and 3.29 from "
        "build_surface.py:2887-2888's own strength/distance pairs")

    print("\n[5] PER-INSTANCE VARIATION")
    keys = ["gain", "dy", "width", "rib_w", "rib_phase", "grain_phase", "edge"]
    coll = {k: [PARAMS[i["key"]][k] for i in INSTANCES] for k in keys}
    dup = [k for k, v in coll.items() if len(set(round(x, 9) for x in v)) < 4]
    chk("all four instances differ in all seven scalar draws", not dup,
        "; ".join("%s %s" % (k, [round(x, 4) for x in v])
                  for k, v in coll.items()))
    o = [PARAMS[i["key"]]["origin"] for i in INSTANCES]
    mind = min(math.dist(o[i], o[j]) for i in range(4) for j in range(i + 1, 4))
    chk("no two instances sample the same noise anywhere",
        mind > 5.0, "closest pair of noise origins is %.2f m apart" % mind)

    print("\n[6] THE TIME GATE")
    chk("nothing exists before the first deposit frame",
        FRONT_X_KEYS[0][1] < MARK_X0 and FRONT_X_KEYS[0][0] == FIRST_DEPOSIT_FRAME - 1,
        "front sits %.1f mm behind the mark start until frame %d, then wipes to "
        "%.5f by frame %d" % (1000 * (MARK_X0 - FRONT_X_KEYS[0][1]),
                              FRONT_X_KEYS[0][0], FRONT_X_KEYS[-1][1],
                              FRONT_X_KEYS[-1][0]))
    chk("the wipe front IS the wheel's own per-frame world x",
        all(abs(FRONT_X_KEYS[i + 1][1] - LAUNCH_FRAMES[i][1]) < 1e-9
            for i in range(len(LAUNCH_FRAMES))),
        "%d keys taken verbatim from wheels.RL.x, frames %d..%d, x %.5f..%.3f"
        % (len(FRONT_X_KEYS), FRONT_X_KEYS[0][0], FRONT_X_KEYS[-1][0],
           FRONT_X_KEYS[1][1], FRONT_X_KEYS[-1][1]))
    chk("the front gates the FILM too, over the whole drive-out",
        FRONT_X_KEYS[-1][1] > 50.0 and len(FRONT_X_KEYS) > 200,
        "the same curve runs to x = %.3f (frame %d), so no rubber of any kind "
        "exists on ground the car has not reached. A film laid ahead of the car "
        "is the same beat-1 defect as a static launch mark."
        % (FRONT_X_KEYS[-1][1], FRONT_X_KEYS[-1][0]))

    print("\n[7] THE R2-651 GUARD")
    w = TR["wheels"]["RR"]
    xs = np.array(w["x"]); ys = np.array(w["y"])
    okspan = xs <= FILM_X_END
    dev = float(np.max(np.abs(ys[okspan] - ys[0])))
    nxt = xs[~okspan].min()
    ndev = float(np.abs(ys[xs == nxt][0] - ys[0]))
    chk("the field's x window is exactly where the driven line is straight",
        dev < 1e-9 and ndev > 0.002,
        "inside the window (x = %.3f .. %.3f, %d samples) the wheel's y is "
        "EXACTLY %.5f -- max deviation %.4f mm. The first sample outside it, at "
        "x = %.3f, is already %.2f mm off. The field REFUSES past x = %.1f."
        % (xs[okspan].min(), xs[okspan].max(), int(okspan.sum()), ys[0],
           1000 * dev, nxt, 1000 * ndev, FILM_X_END))
    chk("the existing apron paint is 77.5 mm inboard and this one is not",
        abs(HALF_TRACK_REAR - 0.72) > 0.07,
        "existing |y| = 0.720 core 200 mm; derived |y| = %.5f core %.1f mm"
        % (HALF_TRACK_REAR, PATCH_W * 1000))

    print("\n%d checks, %d failures" % (n[0], len(fails)))
    if fails:
        print("FAILED: %s" % fails)
    print(">> STAGE RESULT: TYRE_DEPOSIT_SELFTEST_%s"
          % ("PASS" if not fails else "FAIL"))
    return not fails


# ===========================================================================
# 12.  THE GATE — renders, then MEASURES the renders
# ===========================================================================

def _render(scene, path, samples, probe=False):
    """Always to a LINEAR 32-bit EXR under a Standard view transform.

    ONE render per arm, never two. The display-referred 8-bit frame the
    pure-black test needs is produced from THIS buffer by `_to_png` -- rendering
    the same scene twice, once for the measurement and once for the picture,
    would make the two disagree by exactly the sampling noise the test is
    looking for, and on this box (no usable GPU) it would also double an
    already long gate.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene.render.filepath = path
    scene.render.image_settings.file_format = "OPEN_EXR"
    scene.render.image_settings.color_depth = "32"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0.0
    world = scene.world
    if probe:
        # NO SKY BEHIND A PROBE. A probe emits a shader FIELD, so anything that
        # is not the plane must read zero -- and the first deck run proves why:
        # the deck plane is 6.8 m and does not fill a 4.9 m / 35 mm frame, so
        # the contract sky sat behind it at a radiance of several W, the mask
        # `Wetting > 0.30` selected 69 % of the frame instead of the 11 % the
        # band actually covers, and the "Roughness" column came back as 11.25
        # because it was reading sky, not roughness. The 40 x 20 m concrete
        # plane filled its frame and hid the bug completely.
        scene.world = None
        scene.cycles.samples = 1
        scene.cycles.use_denoising = False
        scene.cycles.max_bounces = 0
    else:
        scene.cycles.samples = int(samples)
        scene.cycles.use_denoising = True
        # ONE PLANE, one sun, one sky. The second bounce is this plane lighting
        # itself off a 0.29 albedo at grazing -- below the measurement floor and
        # identical in both arms anyway. Every extra bounce is minutes on a CPU
        # render, and this box has no usable GPU today (nvidia-smi: "Unable to
        # determine the device handle for GPU0") while three other agents hold
        # its cores.
        scene.cycles.max_bounces = 2
        scene.cycles.diffuse_bounces = 1
        scene.cycles.glossy_bounces = 1
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.02
    bpy.ops.render.render(write_still=True)
    scene.world = world
    return path + ".exr"


def _to_png(scene, exr_path, png_path, exposure):
    """The delivered 8-bit frame, from an already-rendered linear EXR.

    `Image.save_render(scene=...)` runs the scene's own colour management over
    the buffer, so this is the same AgX and the same exposure the film applies,
    with no second render.
    """
    img = bpy.data.images.load(exr_path)
    scene.view_settings.view_transform = C.VIEW_TRANSFORM
    scene.view_settings.exposure = float(exposure)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_depth = "8"
    img.save_render(filepath=png_path, scene=scene)
    bpy.data.images.remove(img)
    return png_path


def _read(path, non_color=False):
    img = bpy.data.images.load(path)
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[:, :, :3]


def _lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def gate(samples=192, out=None, subs=("concrete", "deck", "floor"),
         field_probe=True):
    """Build, render and MEASURE. Prints every number; asserts none of them."""
    K._require_bpy("gate")
    out = out or os.path.join(GATE_DIR, "gate_%s.json" % "_".join(subs))
    os.makedirs(GATE_DIR, exist_ok=True)
    rep = {"item": ITEM, "samples": samples}
    scene = bpy.context.scene

    print("\n=== [A] THE RELIEF BUDGET ===")
    rows = relief_rows()
    rep["relief"] = rows
    print("    window %.0f-%.0f mm; all %d stages in window: %s; all in band: %s"
          % (BAND_LO * 1000, BAND_HI * 1000, len(rows),
             all(r["in_window"] for r in rows),
             all(r["verdict"] == "ok" for r in rows)))

    ext = K.assert_no_external_assets()
    print("    assert_no_external_assets -> %s" % ext)

    # ---------------------------------------------------------------- probe --
    if field_probe:
        print("\n=== [B] THE FIELD, MEASURED THROUGH A 12-DEGREE-YAWED OBJECT ===")
        rep["field_probe"] = _gate_field_probe()

    # ------------------------------------------------------------ substrates --
    rep["substrates"] = {}
    for sub in subs:
        print("\n=== [C] %s ===" % sub.upper())
        rep["substrates"][sub] = _gate_substrate(sub, samples)

    # -------------------------------------------------------------- textures --
    tex = _count_tex_images()
    rep["tex_image_nodes"] = tex
    print("\n=== [D] LAW 1 ===")
    print("    ShaderNodeTexImage nodes in every TDP_* tree and material: %d" % tex)
    print("    %s" % K.assert_no_external_assets())

    json.dump(rep, open(out, "w"), indent=1, default=float)
    print("\n>> wrote %s" % out)
    print(">> STAGE RESULT: TYRE_DEPOSIT_GATED")
    return rep


def _count_tex_images():
    n = 0
    for coll_ in (bpy.data.node_groups, bpy.data.materials):
        for d in coll_:
            nt = getattr(d, "node_tree", None) or (
                d if hasattr(d, "nodes") else None)
            if nt is None or not hasattr(nt, "nodes"):
                continue
            n += sum(1 for x in nt.nodes if x.bl_idname == "ShaderNodeTexImage")
    return n


def _ortho_scene(name, centre, half, yaw_deg, z, res=2048):
    """A top-down ORTHO camera over an exact world window. The image is then a
    map of world coordinates and every distance in it can be measured."""
    scene = bpy.context.scene
    root = K.coll(COLL)
    ob = _plane(PFX + "Probe_" + name, (centre[0], centre[1], z), yaw_deg,
                (2.2 * half[0], 2.2 * half[1]), root)
    cd = bpy.data.cameras.new(PFX + "OrthoCam")
    cd.type = "ORTHO"
    cam = bpy.data.objects.new(PFX + "OrthoCam", cd)
    cam.location = (centre[0], centre[1], z + 4.0)
    cam.rotation_mode = "XYZ"
    cam.rotation_euler = (0.0, 0.0, 0.0)      # looking straight down -Z
    root.objects.link(cam)
    scene.camera = cam
    scene.render.engine = "CYCLES"
    res_x = int(res)
    res_y = int(round(res * half[1] / half[0]))
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    # `ortho_scale` is the world size of the LARGER image dimension, not of the
    # width. Setting it to 2*half_x on a 1:3 frame put the window at
    # +-0.133 m in x and +-0.400 m in y, which misses two patches sitting at
    # |y| = 0.7975 entirely and returned a field of exactly zero.
    cd.ortho_scale = 2.0 * (half[0] if res_x >= res_y else half[1])
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.use_border = False
    scene.render.use_crop_to_border = False
    scene.world = None
    return scene, ob, cam


def _gate_field_probe():
    """Ortho top-down over the launch mark, on a 12-deg-yawed object.

    Measures: where the mark actually is in WORLD coordinates, its length, its
    width, its along-track profile against the JSON, the two patches' spread,
    and the time gate at three frames.
    """
    K.purge(PFX, COLL)
    _empty_the_scene()
    build_groups()
    cx = 0.5 * (MARK_X0 + MARK_X1)
    half = (0.40, 1.20)
    scene, ob, _cam = _ortho_scene("field", (cx, 0.0), half, DECK_YAW_DEG,
                                   DECK_Z, res=1024)
    res = {}
    front = {"before": MARK_X0 - 0.012, "mid": LAUNCH_FRAMES[4][1],
             "after": FULLY_LAID_X}
    imgs = {}
    for tag, fx in front.items():
        ob.data.materials.clear()
        ob.data.materials.append(mat_probe("field_" + tag, _field_probe_chans,
                                           front_value=fx))
        p = _render(scene, os.path.join(GATE_DIR, "probe_field_%s" % tag), 1,
                    probe=True)
        imgs[tag] = _read(p)

    a = imgs["after"]
    h, w = a.shape[:2]
    dens = a[:, :, 0]
    # image -> world. x runs UP the image (camera looks down -Z, +Y is up in
    # frame, +X is right)... verified below by comparing against the known y.
    xs = np.linspace(cx - half[0], cx + half[0], w)
    ys = np.linspace(-half[1], half[1], h)
    thr = 0.02 * MARK_TERMINAL
    on = dens > thr
    res["mark_pixels"] = int(on.sum())
    if on.any():
        cols = np.where(on.any(axis=0))[0]
        rowsi = np.where(on.any(axis=1))[0]
        res["world_x_extent"] = [float(xs[cols.min()]), float(xs[cols.max()])]
        res["world_y_extent"] = [float(ys[rowsi.min()]), float(ys[rowsi.max()])]
        res["measured_length_m"] = float(xs[cols.max()] - xs[cols.min()])
        # per-patch: split on sign of y
        prof = {}
        for corner, sgn in (("RL", +1), ("RR", -1)):
            band = (ys * sgn) > 0.2
            sub = dens[band, :]
            colmax = sub.max(axis=0)
            rowmax = sub.max(axis=1)
            yy = ys[band]
            on_y = rowmax > thr
            prof[corner] = dict(
                peak=float(sub.max()),
                mean=float(sub[sub > thr].mean()) if (sub > thr).any() else 0.0,
                area_px=int((sub > thr).sum()),
                y_centre=float(yy[on_y].mean()) if on_y.any() else 0.0,
                y_width=float(yy[on_y].max() - yy[on_y].min()) if on_y.any() else 0.0,
                x_lo=float(xs[np.where(colmax > thr)[0].min()]),
                x_hi=float(xs[np.where(colmax > thr)[0].max()]),
            )
        res["patches"] = prof
        pk = [prof[c]["peak"] for c in ("RL", "RR")]
        mn = [prof[c]["mean"] for c in ("RL", "RR")]
        wd = [prof[c]["y_width"] for c in ("RL", "RR")]
        res["instance_spread"] = dict(
            peak_pct=100.0 * abs(pk[0] - pk[1]) / max(1e-9, 0.5 * (pk[0] + pk[1])),
            mean_pct=100.0 * abs(mn[0] - mn[1]) / max(1e-9, 0.5 * (mn[0] + mn[1])),
            width_mm=1000.0 * abs(wd[0] - wd[1]),
            y_centre_offset_mm=[1000.0 * (prof["RL"]["y_centre"] - HALF_TRACK_REAR),
                                1000.0 * (prof["RR"]["y_centre"] + HALF_TRACK_REAR)],
        )
    res["time_gate"] = {t: dict(max_density=float(imgs[t][:, :, 0].max()),
                                lit_px=int((imgs[t][:, :, 0] > thr).sum()))
                        for t in imgs}
    print("    mark measured at world x %s (declared %.5f .. %.5f)"
          % (["%.5f" % v for v in res.get("world_x_extent", [])], MARK_X0, MARK_X1))
    print("    measured length %.4f m (declared %.4f)"
          % (res.get("measured_length_m", 0.0), MARK_LEN))
    for c in ("RL", "RR"):
        p = res.get("patches", {}).get(c, {})
        print("    patch %s: peak %.4f  mean %.4f  y centre %+.5f  width %.1f mm  "
              "x %.5f..%.5f" % (c, p.get("peak", 0), p.get("mean", 0),
                               p.get("y_centre", 0), 1000 * p.get("y_width", 0),
                               p.get("x_lo", 0), p.get("x_hi", 0)))
    print("    per-instance spread: %s" % res.get("instance_spread"))
    print("    time gate: %s" % res["time_gate"])
    return res


def _gate_substrate(sub, samples):
    """Beauty A/B + roughness probes + pure black, matched camera and exposure."""
    K.purge(PFX, COLL)
    st = {}
    build(scene=bpy.context.scene, test_scene=True, samples=samples,
          substrate=sub, arm="control", stats=st)
    scene = bpy.context.scene
    ob = bpy.data.objects[st["object"]]
    cfg = SUBSTRATES[sub]
    res = dict(cfg_note=cfg["note"], px_per_m=st["px_per_m"],
               mm_per_px=st["mm_per_px"], graze_deg=cfg["graze_deg"],
               resolution=[bpy.context.scene.render.resolution_x,
                           bpy.context.scene.render.resolution_y],
               border=st["border"], traced_px=st["traced_px"])

    arms = (["control", "deposit", "traffic"]
            + (["existing"] if sub == "concrete" else []))
    mk = {"concrete": mat_concrete, "deck": mat_deck, "floor": mat_floor}[sub]
    fv = FULLY_LAID_X                # fully laid, for the static A/B

    beauty = {}
    for arm in arms:
        ob.data.materials.clear()
        ob.data.materials.append(mk(arm, front_value=fv))
        p = _render(scene, os.path.join(GATE_DIR, "%s_%s" % (sub, arm)), samples)
        # LUMINANCE ONLY. This box has 11 GB, other agents are rendering on it,
        # and four 4K RGBA float buffers is half a gigabyte held for nothing.
        beauty[arm] = _lum(_read(p)).astype(np.float32)

    # the deposit's own footprint, as the mask -- measured, not guessed
    ob.data.materials.clear()
    ob.data.materials.append(mat_probe("mask_" + sub, _field_probe_chans,
                                       front_value=fv))
    pm = _render(scene, os.path.join(GATE_DIR, "%s_mask" % sub), 1, probe=True)
    mask_img = _read(pm)
    wet_mask = mask_img[:, :, 2] > 0.30          # the Wetting channel
    mark_mask = mask_img[:, :, 0] > 0.10         # the Density channel: the MARK
    res["mask_px"] = int(wet_mask.sum())
    res["mask_frac"] = float(wet_mask.mean())
    res["mark_px"] = int(mark_mask.sum())
    res["mark_frac"] = float(mark_mask.mean())

    ctl = beauty["control"]
    # EVERY arm is measured on the SAME pixels -- the pixels this module's own
    # deposit lands on. That is deliberately generous to the existing paint,
    # which is 77.5 mm inboard of them: it is being scored on the ground the
    # tyre actually runs over, which is the ground the client is looking at.
    m = wet_mask & (ctl > 1e-6)
    mm = mark_mask & (ctl > 1e-6)
    for arm in arms[1:]:
        dep = beauty[arm]
        r = dep[m] / ctl[m]
        row = dict(
            mean_pct=100.0 * (float(r.mean()) - 1.0),
            p05_pct=100.0 * (float(np.percentile(r, 5)) - 1.0),
            p50_pct=100.0 * (float(np.percentile(r, 50)) - 1.0),
            p95_pct=100.0 * (float(np.percentile(r, 95)) - 1.0),
            n_px=int(m.sum()))
        if mm.sum() > 64:
            rr = dep[mm] / ctl[mm]
            row["mark_only_mean_pct"] = 100.0 * (float(rr.mean()) - 1.0)
            row["mark_only_p05_pct"] = 100.0 * (float(np.percentile(rr, 5)) - 1.0)
            row["mark_only_n_px"] = int(mm.sum())
        res["%s_vs_control" % arm] = row
    # the substrate's own variation on the same pixels, for the sigma question
    inb = ctl[wet_mask & (ctl > 1e-6)]
    res["substrate_variation_pct"] = dict(
        sd_pct=100.0 * float(inb.std() / inb.mean()),
        p05_p95_pp=100.0 * float((np.percentile(inb, 95) - np.percentile(inb, 5))
                                 / inb.mean()))

    # ------- the shader fields themselves: roughness / metallic / coat -------
    fac = {"concrete": _conc_rough_chans_factory, "deck": _deck_rough_chans_factory,
           "floor": _floor_rough_chans_factory}[sub]
    chan_names = {"concrete": ("Roughness", "Specular IOR Level", "Height Coarse"),
                  "deck": ("Roughness", "Metallic", "Base Color.r"),
                  "floor": ("Roughness", "Coat Weight", "Coat Roughness")}[sub]
    fields = {}
    for arm in arms:
        ob.data.materials.clear()
        ob.data.materials.append(mat_probe("f_%s_%s" % (sub, arm), fac(arm),
                                           front_value=fv))
        p = _render(scene, os.path.join(GATE_DIR, "%s_field_%s" % (sub, arm)), 1,
                    probe=True)
        fields[arm] = _read(p)
    res["fields"] = {}
    for i, nm in enumerate(chan_names):
        c = fields["control"][:, :, i][wet_mask]
        d = fields["deposit"][:, :, i][wet_mask]
        row = dict(control_mean=float(c.mean()), deposit_mean=float(d.mean()),
                   delta=float(d.mean() - c.mean()),
                   delta_pct=100.0 * float((d.mean() - c.mean())
                                           / max(abs(c.mean()), 1e-9)))
        if "existing" in fields:
            e = fields["existing"][:, :, i][wet_mask]
            row["existing_mean"] = float(e.mean())
            row["existing_delta"] = float(e.mean() - c.mean())
        res["fields"][nm] = row

    # ---------------------------- pure black, on the DELIVERED 8-bit frame ---
    # The exposure is solved so the CONTROL arm reproduces the operating point
    # the film's own measured frame sits at, then the SAME exposure is used for
    # both arms. For the floor that target is the 0.10 mean the staging doc
    # measures on render/showlight/p_a_f0828_e-3.628.png.
    target = {"floor": 0.10, "deck": 0.24, "concrete": 0.38}[sub]
    ev = FILM_EXPOSURE
    cur = 0.0
    for _it in range(14):
        p = _to_png(scene, os.path.join(GATE_DIR, "%s_control.exr" % sub),
                    os.path.join(GATE_DIR, "%s_solve.png" % sub), ev)
        a = _read(p, non_color=True)
        L = _lum(a)
        cur = float(L[L > 0].mean()) if (L > 0).any() else 1e-4
        d = math.log(max(cur, 1e-6) / target, 2.0)
        if abs(d) < 0.02:
            break
        ev -= d
    res["png_exposure"] = ev
    res["png_control_mean"] = cur
    res["png_target_mean"] = target
    pb = {}
    for arm in arms:
        p = _to_png(scene, os.path.join(GATE_DIR, "%s_%s.exr" % (sub, arm)),
                    os.path.join(GATE_DIR, "%s_png_%s.png" % (sub, arm)), ev)
        a = _read(p, non_color=True)
        black = np.all(a < 0.5 / 255.0, axis=2)
        pb[arm] = dict(pure_black_pct=100.0 * float(black.mean()),
                       pure_black_px=int(black.sum()),
                       lum_min=float(_lum(a).min()),
                       lum_mean=float(_lum(a).mean()),
                       in_mask_min=float(_lum(a)[wet_mask].min()) if wet_mask.any() else 0.0)
    res["pure_black"] = pb

    print("    %s at %.2f mm/px (4K pixel law; traced region %d x %d px of "
          "3840 x 2160), %.0f deg grazing; the deposit's own footprint is "
          "%.2f %% of the traced region (%d px), the MARK %.2f %% (%d px)"
          % (sub, res["mm_per_px"], res["traced_px"][0], res["traced_px"][1],
             res["graze_deg"], 100 * res["mask_frac"], res["mask_px"],
             100 * res["mark_frac"], res["mark_px"]))
    for arm in arms[1:]:
        d = res["%s_vs_control" % arm]
        print("      TONE  %-9s mean %+7.2f %%   p05 %+7.2f %%   p50 %+7.2f %%   "
              "p95 %+7.2f %%   (%d px)%s"
              % (arm, d["mean_pct"], d["p05_pct"], d["p50_pct"], d["p95_pct"],
                 d["n_px"],
                 "   MARK ONLY mean %+.2f %% p05 %+.2f %% (%d px)"
                 % (d["mark_only_mean_pct"], d["mark_only_p05_pct"],
                    d["mark_only_n_px"]) if "mark_only_mean_pct" in d else ""))
    print("      substrate's own variation on the same pixels: sd %.2f %%, "
          "p05-p95 %.1f pp" % (res["substrate_variation_pct"]["sd_pct"],
                               res["substrate_variation_pct"]["p05_p95_pp"]))
    for nm, row in res["fields"].items():
        print("      FIELD %-20s %.4f -> %.4f  (%+.4f, %+.1f %%)%s"
              % (nm, row["control_mean"], row["deposit_mean"], row["delta"],
                 row["delta_pct"],
                 "   existing %+.4f" % row["existing_delta"]
                 if "existing_delta" in row else ""))
    print("      PNG at exposure %+.3f, control mean %.4f (target %.2f)"
          % (res["png_exposure"], res["png_control_mean"], target))
    for arm, v in pb.items():
        print("      BLACK %-9s pure black %.4f %%  (%d px)  lum min %.5f  "
              "in-mask min %.5f"
              % (arm, v["pure_black_pct"], v["pure_black_px"], v["lum_min"],
                 v["in_mask_min"]))
    return res


def bindtest(verbose=True):
    """MEASURE that the time gate actually animates. Needs bpy; not in selftest.

    `--selftest` runs without Blender and therefore cannot see any of the three
    things that were wrong here the first time this was run:
      * `Action.fcurves` does not exist in Blender 5.2 (`action_fcurves`);
      * an animated node tree is not evaluated unless the material has a USER;
      * frame 817 must still be empty -- `deposit_norm` is credited to the
        segment ENDING at its sample, so 818 is the first frame carrying rubber.
    """
    K._require_bpy("bindtest")
    build_groups()
    t = K.NT(PFX + "M_BindTest")
    v = front_x_value_node(t)
    f = field_node(t, front_node=(v, 0))
    e = t.n("ShaderNodeEmission")
    t.pin_named(e, "Color", _o(f, "Density"))
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(e.outputs[0], out.inputs["Surface"])
    bind_time(v)
    name = v.name
    sc = bpy.context.scene
    me = bpy.data.meshes.new(PFX + "BindTestMesh")
    me.vertices.add(3)
    ob = bpy.data.objects.new(PFX + "BindTest", me)
    sc.collection.objects.link(ob)
    me.materials.append(t.m)              # WITHOUT THIS, NOTHING ANIMATES

    ok, rows = True, []
    want = [(700, MARK_X0 - 0.012), (816, MARK_X0 - 0.012),
            (FIRST_DEPOSIT_FRAME - 1, MARK_X0 - 0.012)]
    want += [(fr, x) for fr, x, _d in LAUNCH_FRAMES]
    want += [(FRONT_X_KEYS[-1][0], FRONT_X_KEYS[-1][1]),
             (2900, FRONT_X_KEYS[-1][1])]
    for fr, w in want:
        sc.frame_set(int(fr))
        got = float(t.t.nodes[name].outputs[0].default_value)
        d = abs(got - w)
        rows.append((fr, got, w, d))
        if d > 2e-4:
            ok = False
        if verbose:
            print("    frame %5d  Front X %+11.5f  want %+11.5f  err %.2e"
                  % (fr, got, w, d))
    fcs = action_fcurves(t.m.node_tree)
    nk = sum(len(fc.keyframe_points) for fc in fcs)
    interp = {kp.interpolation for fc in fcs for kp in fc.keyframe_points}
    extra = {fc.extrapolation for fc in fcs}
    ok = (ok and len(fcs) == 1 and nk == len(FRONT_X_KEYS)
          and interp == {"LINEAR"} and extra == {"CONSTANT"})
    print("    %d fcurve, %d keys (FRONT_X_KEYS %d), %r, interp %s, extrap %s"
          % (len(fcs), nk, len(FRONT_X_KEYS), fcs[0].data_path if fcs else None,
             interp, extra))
    print(">> STAGE RESULT: TYRE_DEPOSIT_BINDTIME_%s"
          % ("PASS" if ok else "FAIL"))
    return ok


# ===========================================================================
# 13.  CLI
# ===========================================================================

def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    ap = argparse.ArgumentParser(prog=ITEM)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--test-scene", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--bindtest", action="store_true")
    ap.add_argument("--subs", default="concrete,deck,floor")
    ap.add_argument("--no-field-probe", action="store_true")
    ap.add_argument("--relief", action="store_true")
    ap.add_argument("--substrate", default="concrete", choices=list(SUBSTRATES))
    ap.add_argument("--arm", default="deposit",
                    choices=["control", "deposit", "traffic", "existing"])
    ap.add_argument("--interface", default=None)
    ap.add_argument("--save", default=None)
    ap.add_argument("--samples", type=int, default=192)
    a = ap.parse_args(argv)

    if a.relief:
        relief_rows()
    if a.interface:
        interface_json(os.path.abspath(a.interface))
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.bindtest:
        sys.exit(0 if bindtest() else 1)
    if a.gate:
        gate(samples=a.samples, subs=tuple(a.subs.split(",")),
             field_probe=not a.no_field_probe)
        return
    if a.build or a.test_scene or a.save:
        st = {}
        build(scene=bpy.context.scene, test_scene=a.test_scene,
              samples=a.samples, substrate=a.substrate, arm=a.arm, stats=st)
        if a.save:
            p = os.path.abspath(a.save)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            K.assert_no_external_assets()
            bpy.ops.wm.save_as_mainfile(filepath=p, compress=True)
            K.log("saved %s (%.1f MB)" % (p, os.path.getsize(p) / 1048576.0))
        for k, v in st.items():
            print("  %-16s %s" % (k, v))
        print(">> STAGE RESULT: TYRE_DEPOSIT_BUILT")


if __name__ == "__main__":
    main()
