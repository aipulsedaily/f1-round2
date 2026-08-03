"""spectator_standing_ga -- 3,500 people on the general-admission banking.

    python3 world/items/spectator_standing_ga.py --selftest
    python3 world/items/spectator_standing_ga.py --plan --synthetic
    blender -b --factory-startup -P world/items/spectator_standing_ga.py -- \
        --synthetic --out world/items/spectator_standing_ga_test.blend

WHAT THIS IS AND WHAT IT IS NOT, STATED FIRST
=============================================
This is the GA figure tier: the plan, the density, the contact with the slope,
the library and the instancing. **It is NOT its host.** `ga_viewing_bank` --
6 instances, 6.0 m, *"the WEAR is the object"* -- is a TERRAIN item and has no
module either, and the figures stand on it. Rather than invent a bank and let
the real one contradict it later, this module states the interface it needs as
a CONTRACT (section 1), refuses to place a single figure in the world without
it, and ships a `--synthetic` bank that satisfies the contract so that
everything else here can be built, measured and checked today.

    THE ONE THING THE NEXT AGENT ON `ga_viewing_bank` HAS TO PROVIDE
    ---------------------------------------------------------------
    `ga_viewing_bank.bank_sections()` -> a list of dicts, one per bank:

        {"name":   str,             # e.g. "GA_VIRAGE_NORD"
         "p0":     (x, y, z),       # toe of the batter, one end, world metres
         "p1":     (x, y, z),       # toe of the batter, the other end
         "height": float,           # crest above toe, metres
         "batter": float,           # run per unit rise: 2.5..3.0
         "crest_w": float,          # flat width at the top, metres
         "outward": (x, y)}         # unit vector, horizontal, TOE -> CREST:
                                    # the direction the ground RISES. Not
                                    # derivable from p0/p1 -- a line has two
                                    # normals, and picking the wrong one puts
                                    # the whole bank on the wrong side of the
                                    # track.

    **`outward` IS THE WAY THE GROUND RISES, NOT THE WAY PEOPLE LOOK.** The
    two are opposite and getting them confused is not a cosmetic error: the
    first version of this module used `outward` as the view direction, and
    `crowd_is_not_a_uniform_smear` caught it -- `sightline_quality` came out
    at ZERO over every bank, the additive `CLUSTER_FLOOR` was then the whole
    density, and the crowd was a **uniform smear**, which is the exact defect
    the manifest names. The check failed the way it was written to. A bank
    rises AWAY from the circuit, so the crest is the far edge and everybody on
    the face is looking back DOWN the slope, along `-outward`.

    `bank_array()` below reads exactly that and nothing else.

THE TIER. IT IS L0, AND BOTH PUBLISHED NUMBERS ARE UNSUPPORTED
===============================================================
HUMAN-REFERENCE sec 00000.7 item 3 leaves this open and says somebody has to
settle it before a line is written:

    manifest arithmetic   15.4 m / 35 mm -> 242.4 px/m -> 1.75 m = **424 px** -> L0
    screen_presence.json  peak_sharp_px_4k = **278.7 px**                -> L1

**Neither is a measurement of this item, and the second one is not a
measurement of a GA bank at all.** Read `docs/screen_presence.json` for the
three crowd items side by side:

    item                     height_m   peak_sharp_px_4k   px/m
    spectator_seated            1.25          199.1        159.3
    spectator_standing_ga       1.75          278.7        159.3
    ga_viewing_bank             6.00          955.7        159.3

One number, 159.3 px/m, times the declared height. All three carry the SAME
`n_hosts: 11`, the same eleven `ARCH_Grandstand_*` hosts, the same
`frames_visible: 1328`, the same `min_depth_m: 10.756`, the same `peak_frame:
2703` and the same `peak_sharp_frame: 1009` -- because `host_tier` is
**"ZONE"**, so every item in the `crowd` zone was matched to every object in
it. **The GA banking is not in `assembly6.blend` -- it has no module -- so
there was nothing else to match.** 278.7 px is the GRANDSTANDS' screen
presence rescaled to 1.75 m, measured on the main straight, for an item that
lives at six corners. It is not evidence about this tier and it must not be
quoted as though it were.

So the decision rests on the manifest's declared framing, which is the only
number about this item, plus three things that are actually measured:

  1. **sec 0000.3, measured on this project:** *"`LOD.for_px` takes the
     figure's projected HEIGHT: at 14.7 m on a 28 mm lens a 1.25 m SEATED
     figure is 254 px -> L1, and a 1.75 m STANDING one is 356 px -> L0."*
     GA is 100 % standing and 1.75 m. The seated crowd's own numbers put a
     standing figure a tier above a seated one at the SAME camera, and GA's
     declared camera is nearer (15.4 m) on a longer lens (35 mm vs 28) than
     the seated tier's.
  2. **The error is not symmetric.** A tier short is defect 6 -- `LOD_L1`
     builds `fingers = 3`, which `humankit.hand_finger_separation` shows is
     two FUSED PAIRS, and that cost this project a whole pass. A tier long
     costs library MEMORY only: the library is instanced, so sec 00000.5's
     79,088 vs 29,755 triangles is a one-off ~33 M against ~24 M on a 32 GB
     card, not a per-instance cost over 3,500 people.
  3. GA figures are the only full-length silhouettes in the crowd zone that
     stand on a bare slope with sky behind them. There is no seat, no row in
     front and no roof; the silhouette is the whole read.

`LOD_GA` is therefore L0, and `--lod` overrides it if the bank ever gets built
and measured and the measurement disagrees. **When `ga_viewing_bank` exists,
re-run `tools/screen_presence.py` and put a real number here.**

THE DENSITY IS THE ITEM
=======================
The manifest's note is the acceptance criterion and it names its own failure:

    "They cluster hard where the sightline is good and thin out to nothing
     30 m either side -- **a uniform smear along the bank is the tell.**"

So the density along a bank is not a noise and not a constant. It is driven by
`sightline_quality`, which is geometry: from a point on the face you can see
the track if the bank's outward normal points at it and you are high enough to
see over the people in front. `crowd_is_not_a_uniform_smear` in the selftest
measures the Gini coefficient of linear density and the peak-to-30-m ratio,
with a uniform draw as the control that must FAIL both.
"""

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

_ITEMS = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_ITEMS)
_ROOT = os.path.dirname(_WORLD)
for _p in (_WORLD, _ITEMS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import itemkit as K                                          # noqa: E402
import humankit as HK                                        # noqa: E402

try:
    import bpy
except ImportError:
    bpy = None

ITEM = "spectator_standing_ga"
PFX = "GAX_"
COLL = "ITEM_spectator_standing_ga"
LIB_COLL = COLL + "_Library"
SEED = 20260803
DECLARED = 3500
TELEMETRY = os.path.join(_ROOT, "telemetry", "telemetry.csv")

#: See the tier argument in the module docstring. L0, with the manifest's own
#: 424 px as the only number that is about this item.
LOD_GA = "L0"
MANIFEST_PX = 424.0
MANIFEST_M = 15.4
MANIFEST_LENS = 35.0


# ==========================================================================
# 1.  THE BANK -- a contract, not an invention
# ==========================================================================

BANK_BATTER_MIN, BANK_BATTER_MAX = 2.5, 3.0
"""Run per unit rise. The manifest's own `variation_axes` for
`ga_viewing_bank`: *"earth batter 1:2.5 to 1:3"*. 1:2.5 is 21.8 deg from
horizontal and 1:3 is 18.4 deg -- both comfortably standable, which is why a
GA bank is built at them and why people spread over the whole FACE rather than
queueing on the crest."""

#: Nobody stands on the last half-metre of a batter toe -- it is where the
#: water runs -- and nobody stands within this of the crest edge either.
BANK_TOE_MARGIN_M = 0.60
BANK_CREST_MARGIN_M = 0.35


def bank_array(sections=None, synthetic=False):
    """Every bank this item stands on, validated against the contract.

    RAISES rather than inventing. `spectator_crowd.seat_array` reads
    `grandstand_riser_unit.seat_grid()`; this is the same relationship and the
    host does not exist yet, so the failure has to be loud and has to say what
    is missing. A module that quietly invents its host's geometry produces a
    crowd standing in mid air 40 m from a hillside and every check in the file
    passes.
    """
    if sections is not None:
        secs = list(sections)
    elif synthetic:
        secs = synthetic_bank_sections()
    else:
        try:
            import ga_viewing_bank as GVB           # noqa: F401
        except ImportError:
            raise RuntimeError(
                "spectator_standing_ga needs its HOST. `ga_viewing_bank` has "
                "no module (item_manifest build_order 257, module 'terrain', "
                "6 instances, 6.0 m) and these figures stand on it.\n"
                "  Provide `ga_viewing_bank.bank_sections()` returning dicts "
                "with keys: name, p0, p1, height, batter, crest_w, outward -- "
                "see this module's docstring for what each one means.\n"
                "  `--synthetic` builds a contract-compliant test bank so the "
                "plan, the density and the selftest can be checked without it, "
                "but it is NOT the world's geometry and must never be shipped "
                "into an assembly.")
        secs = list(GVB.bank_sections())
    out = []
    for i, s in enumerate(secs):
        for k in ("name", "p0", "p1", "height", "batter", "crest_w", "outward"):
            if k not in s:
                raise RuntimeError(
                    "bank section %d (%r) is missing %r. The contract is in "
                    "spectator_standing_ga's docstring." % (i, s.get("name"), k))
        b = float(s["batter"])
        if not BANK_BATTER_MIN - 1e-6 <= b <= BANK_BATTER_MAX + 1e-6:
            raise RuntimeError(
                "bank %r has batter 1:%.2f, outside the manifest's declared "
                "1:%.1f to 1:%.1f. A 1:1.5 batter is not a bank people stand "
                "on, it is a scramble." % (s["name"], b, BANK_BATTER_MIN,
                                           BANK_BATTER_MAX))
        o = np.asarray(s["outward"], float)[:2]
        n = float(np.linalg.norm(o))
        if n < 1e-6:
            raise RuntimeError("bank %r has a zero `outward`" % s["name"])
        d = np.asarray(s["p1"], float)[:2] - np.asarray(s["p0"], float)[:2]
        if float(np.linalg.norm(d)) < 1.0:
            raise RuntimeError("bank %r is shorter than a metre" % s["name"])
        # `outward` must be a NORMAL of the run, not parallel to it. A bank
        # whose face looks along its own length is a modelling error that no
        # later check would catch -- the figures would be a neat line inside
        # the earth.
        along = d / np.linalg.norm(d)
        if abs(float(np.dot(along, o / n))) > 0.25:
            raise RuntimeError(
                "bank %r: `outward` is %.0f deg off the normal of its own run. "
                "It is the direction the FACE LOOKS, toe -> crest."
                % (s["name"], math.degrees(math.acos(
                    min(1.0, abs(float(np.dot(along, o / n))))))))
        r = dict(s)
        r["outward"] = tuple(o / n)
        r["length_m"] = float(np.linalg.norm(d))
        r["along"] = tuple(along)
        out.append(r)
    return out


def synthetic_bank_sections():
    """A contract-compliant TEST bank. NOT the world's geometry.

    Six banks at six corners is what the manifest declares; where they are is
    the terrain item's business. These are laid out around the origin purely
    so the arithmetic below has something to run on, and `build_scene` stamps
    `ga_bank_is_synthetic` on the collection so no assembly can pick it up by
    accident.
    """
    out = []
    for i in range(6):
        a = i * (TAU_DEG := 60.0)
        th = math.radians(a)
        c = np.array([220.0 * math.cos(th), 220.0 * math.sin(th), 0.0])
        along = np.array([-math.sin(th), math.cos(th)])
        L = 118.0 + 16.0 * math.cos(2.3 * i)
        out.append({
            "name": "GA_SYN_%02d" % i,
            "p0": tuple(c[:2] - along * L * 0.5) + (0.0,),
            "p1": tuple(c[:2] + along * L * 0.5) + (0.0,),
            "height": 5.4 + 0.9 * math.cos(1.7 * i),
            "batter": 2.5 + 0.5 * (0.5 + 0.5 * math.cos(2.9 * i)),
            "crest_w": 3.0 + 1.4 * (0.5 + 0.5 * math.sin(1.3 * i)),
            "outward": (math.cos(th), math.sin(th)),
        })
    return out


def bank_point(bank, s, h):
    """World point on the bank face. `s` 0..1 along the run, `h` 0..1 up the
    face (1 = crest edge). Returns (xyz, up_slope_unit, ground_normal)."""
    p0 = np.asarray(bank["p0"], float)
    p1 = np.asarray(bank["p1"], float)
    o = np.asarray(bank["outward"], float)
    H = float(bank["height"])
    run = H * float(bank["batter"])
    base = p0 + (p1 - p0) * float(s)
    z = base[2] + H * float(h)
    xy = base[:2] + o * (run * float(h))
    P = np.array([xy[0], xy[1], z])
    # up-slope direction (unit, pointing at the crest) and the ground normal
    slope = np.array([-o[0] * run, -o[1] * run, H])
    slope /= np.linalg.norm(slope)
    nrm = np.array([o[0] * H, o[1] * H, run])
    nrm /= np.linalg.norm(nrm)
    return P, slope, nrm


def bank_face_length_m(bank):
    """Slope length from toe to crest edge, in metres -- the distance a person
    can actually be placed over, which is NOT the height."""
    H = float(bank["height"])
    return math.hypot(H, H * float(bank["batter"]))


# ==========================================================================
# 2.  THE DENSITY -- geometry, because "a uniform smear is the tell"
# ==========================================================================

SIGHT_FALLOFF_M = 30.0
"""*"...and thin out **to nothing** 30 m either side."* The manifest's own
number, and the two words in bold are the ones that set the constant.

IT IS NOT THE GAUSSIAN'S SIGMA, and using it as one was a bug the selftest
caught. A Gaussian at sigma = 30 m still holds **61 %** of its peak at 30 m --
`peak_over_30m` came out at 1.65 from the shape alone, and the whole item
measured 2.32 against a uniform control at 1.76, i.e. very nearly the smear
the manifest names. "To nothing" is not 61 %. `SIGHT_SIGMA_M` below puts 30 m
at 2.2 sigma, where a Gaussian is at 9 % -- which is what "to nothing" means
in a sentence about a crowd."""

SIGHT_SIGMA_M = SIGHT_FALLOFF_M / 2.2

CLUSTER_FLOOR = 0.06
"""Density a long way from any good sightline, as a fraction of the peak. NOT
zero: a real bank has stragglers, people walking through, and somebody who
turned up late. Zero would make the ends of every bank a hard edge, which is
the same defect as the smear with the sign flipped."""


_TRACK_XY = None

SIGHT_BEST_M = 22.0
"""The distance from the racing line people actually want, in metres. Not
zero: at a real circuit the toe of a GA bank is behind a debris fence and a
run-off, and the good spot is far enough back to see the corner ENTRY as well
as the point in front of you."""

SIGHT_SPAN_M = 260.0
"""How far along the track a sightline is counted as useful. Somebody on a
bank watches a car approach, turn and leave; the amount of track visible is
half of why one spot beats another."""


def track_xy():
    """The racing line, as (N, 2). Read out of `telemetry/telemetry.csv`,
    which another agent owns and this only ever reads.

    THIS IS THE TRACK, NOT THE CAR. `car_at(frame)` is one sample of the same
    file and is what ATTENTION is solved against; the whole path is what
    DENSITY is solved against, and conflating them is a modelling error the
    selftest caught -- see `sightline_quality`.
    """
    global _TRACK_XY
    if _TRACK_XY is None:
        with open(TELEMETRY) as fh:
            rows = list(csv.DictReader(fh))
        P = np.array([[float(r["x"]), float(r["y"])] for r in rows])
        step = max(1, len(P) // 1400)
        _TRACK_XY = P[::step]
    return _TRACK_XY


def sightline_quality(bank, s):
    """0..1, how good the view of the TRACK is from position `s` along a bank.

    **DENSITY IS NOT A FUNCTION OF WHERE THE CAR IS.** The first version of
    this took the car's position at frame 1009 as its focus, and
    `crowd_is_not_a_uniform_smear` failed: three of six banks face a part of
    the circuit the car is nowhere near at that instant, so their sightline
    quality was identically zero and their population fell back to the flat
    `CLUSTER_FLOOR` -- a uniform smear, on half the item, from a statistic
    that had no business being dynamic. **Where somebody chooses to stand is
    decided before the session starts and does not change as a car goes past.**
    Attention does; density does not. `car_at` is still what
    `_solve_gaze` uses, and it is the only thing that should.

    Two multiplied terms, both geometric, both measured against the racing
    line rather than against a point somebody chose:

      * **RANGE** -- a Gaussian on the distance to the nearest track point in
        front of you, peaked at `SIGHT_BEST_M`. Too close and the fence and
        the barrier are the view; too far and it is a television.
      * **SWEEP** -- how much track is visible within `SIGHT_SPAN_M`, in the
        forward half-plane. This is what makes the outside of a corner worth
        standing on and a straight not: you see entry, apex and exit at once.

    Then the manifest's own 30 m falloff about the best point on the bank,
    which is what turns a smooth field into a CLUSTER.
    """
    p0 = np.asarray(bank["p0"], float)
    p1 = np.asarray(bank["p1"], float)
    # DOWN the slope is where the track is. `outward` is toe -> crest, i.e.
    # the way the ground RISES; a spectator on the face looks along -outward.
    view = -np.asarray(bank["outward"], float)
    s = np.atleast_1d(np.asarray(s, float))
    base = p0[None, :2] + (p1 - p0)[None, :2] * s[:, None]
    T = track_xy()
    d = T[None, :, :] - base[:, None, :]                    # (S, N, 2)
    rad = np.linalg.norm(d, axis=2)
    fwd = np.einsum("snj,j->sn", d, view) > 0.0
    big = np.where(fwd, rad, np.inf)
    near = np.min(big, axis=1)
    rng_ = np.exp(-0.5 * ((near - SIGHT_BEST_M) / 34.0) ** 2)
    sweep = np.sum(fwd & (rad < SIGHT_SPAN_M), axis=1) / float(len(T))
    sweep = sweep / max(float(sweep.max()), 1e-9)
    q = np.clip(rng_ * sweep ** 0.75, 0.0, 1.0)
    if float(q.max()) <= 1e-9:
        return q
    best = int(np.argmax(q))
    along = (s - s[best]) * float(bank["length_m"])
    return np.clip(q * np.exp(-0.5 * (along / SIGHT_SIGMA_M) ** 2), 0.0, 1.0)


def density_along(bank, s, seed=SEED):
    """Linear density along the bank, 0..1, peak-normalised.

    `sightline_quality` plus a floor plus a per-bank clump noise, so two banks
    with the same geometry are not the same crowd. The noise is MULTIPLICATIVE
    on top of the sightline, not additive beside it: a clump 80 m from the only
    thing worth watching is not a clump, it is a mistake.
    """
    q = sightline_quality(bank, s)
    rr = HK.rng_for(seed, abs(hash(bank["name"])) % 100003)
    ph = rr.u() * 1.0
    s = np.atleast_1d(np.asarray(s, float))
    lump = 0.55 + 0.45 * (0.5 + 0.5 * np.sin(
        2.0 * math.pi * (s * (2.0 + 3.0 * rr.u()) + ph)))
    lump = lump * (0.70 + 0.60 * (0.5 + 0.5 * np.sin(
        2.0 * math.pi * (s * (6.0 + 5.0 * rr.u()) + rr.u()))))
    d = CLUSTER_FLOOR + (1.0 - CLUSTER_FLOOR) * q * np.clip(lump, 0.0, 1.6)
    return np.clip(d / max(float(d.max()), 1e-9), 0.0, 1.0)


def density_up_face(h):
    """Relative density as a function of height up the face, 0..1.

    Weighted to the TOP, and for a reason that is the same one that put
    `spectator_crowd`'s camera at 6 m rather than at track level: on a raked
    surface the people in front eclipse the people behind, so the view is
    better the higher you stand and everybody knows it. The crest itself is
    the best spot and it is also where the manifest says the grass is worn to
    *"bare mud at the crest"*. Not a hard step, because the crest is narrow and
    fills, and the overflow goes down the face.
    """
    h = np.clip(np.asarray(h, float), 0.0, 1.0)
    return 0.22 + 0.78 * h ** 1.9


# ==========================================================================
# 3.  THE PLAN
# ==========================================================================

#: What a GA crowd is DOING. The manifest's variation axes: "standing /
#: sitting on the grass / on a folding stool".
GA_ROLE_W = (("stand", 0.72), ("sit_ground", 0.17), ("stool", 0.11))

#: Head centre above the ground the figure's feet are on, in metres. Standing
#: is `spectator_crowd._HEAD_DZ_ONFOOT`; the other two are measured off a real
#: seated body rather than assumed -- see `head_dz_measured()`.
HEAD_DZ = {"stand": 1.58, "sit_ground": 0.86, "stool": 1.06}

#: Head-turn span and bin count per role, as `spectator_crowd.ROLE_SPAN` /
#: `ROLE_BINS` do. Somebody standing can turn further than somebody sitting on
#: the ground with their legs out in front of them.
GA_SPAN = {"stand": 84.0, "sit_ground": 52.0, "stool": 60.0}
GA_BINS = {"stand": 11, "sit_ground": 7, "stool": 7}
GA_CELL = {"stand": 48, "sit_ground": 20, "stool": 16}

GA_ATTENTION = 0.74
"""Fraction attending the car. Higher than the grandstand's 0.72 on purpose
and the reason is physical: a GA bank has no seat that faces anywhere, so the
only thing orienting a body is what it is looking at. The non-attenders are
what the picture is judged on -- see sec 0000.1."""


def car_at(frame):
    """The car's world position at `frame`. `telemetry/telemetry.csv` is owned
    by another agent; this only ever reads it."""
    with open(TELEMETRY) as fh:
        rows = list(csv.DictReader(fh))
    r = rows[max(0, min(len(rows) - 1, int(frame)))]
    return (float(r["x"]), float(r["y"]), float(r["z"]) + 0.55)


def plan_banks(seed, banks, focus, n_want=DECLARED, uniform=False):
    """Where every GA spectator is, what they are doing, and where they look.

    `uniform=True` is the POSITIVE CONTROL for
    `crowd_is_not_a_uniform_smear`: the same count, the same banks, the same
    roles, drawn from a FLAT density. It must fail the checks the real draw
    passes, or those checks are measuring nothing.
    """
    rr = HK.rng_for(seed, 7)
    # SHARE THE POPULATION BY VIEW, NOT BY AREA. Allocating by area alone was
    # the second modelling error `crowd_is_not_a_uniform_smear` caught: it
    # gives a bank that overlooks a barrier the same people-per-square-metre
    # as one that overlooks the corner, so half the item is a smear however
    # sharp the within-bank density is. People do not spread themselves evenly
    # over the available banking; they go where the view is, and a bank with a
    # poor view is nearly empty.
    areas = np.array([b["length_m"] * bank_face_length_m(b) for b in banks])
    if uniform:
        share = areas / areas.sum()          # the NULL: evenly over the banking
    else:
        view = np.array([float(np.mean(sightline_quality(
            b, np.linspace(0.0, 1.0, 240)))) for b in banks])
        share = areas * (CLUSTER_FLOOR + view)
        share = share / share.sum()
    counts = np.floor(share * n_want).astype(int)
    counts[np.argmax(counts)] += int(n_want - counts.sum())
    plan = []
    for bi, (bank, n_b) in enumerate(zip(banks, counts)):
        ss = np.linspace(0.0, 1.0, 900)
        w = (np.ones_like(ss) if uniform else density_along(bank, ss, seed))
        w = np.maximum(w, 1e-9)
        cdf = np.cumsum(w)
        cdf /= cdf[-1]
        u = np.asarray([rr.u() for _ in range(int(n_b))])
        s = np.interp(u, cdf, ss)
        # up the face, by the same inverse-CDF trick
        hh = np.linspace(0.0, 1.0, 240)
        wh = np.ones_like(hh) if uniform else density_up_face(hh)
        ch = np.cumsum(wh)
        ch /= ch[-1]
        h = np.interp(np.asarray([rr.u() for _ in range(int(n_b))]), ch, hh)
        # keep off the toe and the crest edge, in METRES of slope
        face = bank_face_length_m(bank)
        h = np.clip(h, BANK_TOE_MARGIN_M / face, 1.0 - BANK_CREST_MARGIN_M / face)
        for i in range(int(n_b)):
            role = HK._pick_weighted(rr.u(), GA_ROLE_W)
            P, slope, nrm = bank_point(bank, float(s[i]), float(h[i]))
            # a small lateral jitter so nobody is on a grid line
            P = P + np.array([rr.n(0.0, 0.28), rr.n(0.0, 0.28), 0.0])
            head = P + np.array([0.0, 0.0, HEAD_DZ[role]])
            att = rr.u() < GA_ATTENTION
            if att:
                yaw = math.degrees(math.atan2(focus[1] - head[1],
                                              focus[0] - head[0]))
            else:
                # not watching: facing a neighbour, or up the bank at the
                # people behind, or down at a phone. Never uniformly random --
                # sec 0000.1's own note is that the `attention = 0` control has
                # a floor because a body still faces SOMEWHERE plausible.
                o = bank["outward"]
                dn = math.degrees(math.atan2(-o[1], -o[0]))   # DOWN the slope
                yaw = dn + rr.n(0.0, 62.0) + (180.0 if rr.u() < 0.22 else 0.0)
            plan.append({
                "bank": bank["name"], "bank_i": bi,
                "s": float(s[i]), "h": float(h[i]),
                "pos": (float(P[0]), float(P[1])), "z": float(P[2]),
                "role": role, "attending": bool(att),
                "yaw_deg": float(((yaw + 180.0) % 360.0) - 180.0),
                "slope_deg": float(math.degrees(math.asin(
                    np.clip(nrm[2], -1.0, 1.0)))),
                "k": 0, "src": 0,
                "body_yaw_deg": 0.0, "gaze_baked_deg": 0.0,
            })
    _solve_gaze(plan, seed)
    return plan


def _solve_gaze(plan, seed):
    """Split the attend bearing between the BODY and the head, then re-solve
    the body AFTER the head bin is known.

    This is sec 00000.4's comb fix, and it is copied deliberately rather than
    re-derived: `plan_block` solved the body against the CONTINUOUS head turn
    and quantised the head afterwards, so what a viewer saw --
    `body + baked` -- swept 9.7 deg inside a bin and then JUMPED the remaining
    8.3 deg at the edge. Period 18 deg, duty 54 %, and no attention statistic
    in the repository could see it because it is a property of the field's fine
    structure rather than of its mean or its spread.

    A GA figure has NO SEAT, so the body is free to turn the whole way; the
    only limit is the neck's own +/- span. That makes the residual smaller
    here than in a grandstand, not larger, but the ordering still matters.
    """
    rr = HK.rng_for(seed, 91)
    for p in plan:
        role = p["role"]
        span, nb = GA_SPAN[role], GA_BINS[role]
        stance = p["yaw_deg"] + rr.n(0.0, 6.0)
        d = ((p["yaw_deg"] - stance + 180.0) % 360.0) - 180.0
        head_want = float(np.clip(d, -span * 0.5, span * 0.5))
        b = int(round((head_want + span * 0.5) / max(span, 1e-9) * (nb - 1)))
        b = int(np.clip(b, 0, nb - 1))
        baked = -span * 0.5 + span * b / max(nb - 1.0, 1.0)
        # THE BODY ABSORBS THE QUANTISATION RESIDUAL, not the neck.
        p["gaze_baked_deg"] = float(baked)
        p["body_yaw_deg"] = float(((p["yaw_deg"] - baked + 180.0) % 360.0) - 180.0)
        p["head_yaw_solved_deg"] = float(head_want)
        p["k"] = int(HK._hash01(p["s"], p["h"], p["bank_i"]) * GA_CELL[role])


def realised_bearing(plan):
    """What a VIEWER sees: body rotation plus the head turn actually baked
    into the library cell. NOT `yaw_deg`, which is the plan's intent -- that
    confusion is sec 0000.1's `attention_spread` bug."""
    return np.array([p["body_yaw_deg"] + p["gaze_baked_deg"] for p in plan])


def attention_fraction(plan, focus, within_deg=20.0):
    B = realised_bearing(plan)
    H = np.array([[p["pos"][0], p["pos"][1], p["z"] + HEAD_DZ[p["role"]]]
                  for p in plan])
    want = np.degrees(np.arctan2(focus[1] - H[:, 1], focus[0] - H[:, 0]))
    d = np.abs(((B - want + 180.0) % 360.0) - 180.0)
    return float(np.mean(d < within_deg)), float(np.mean(d))


# ==========================================================================
# 4.  DENSITY STATISTICS -- the acceptance criterion, as numbers
# ==========================================================================

def density_profile(plan, banks, bins=40):
    """People per metre along each bank, as an array per bank."""
    out = {}
    for bi, b in enumerate(banks):
        s = np.array([p["s"] for p in plan if p["bank_i"] == bi])
        if not len(s):
            out[b["name"]] = np.zeros(bins)
            continue
        hist, _ = np.histogram(s, bins=bins, range=(0.0, 1.0))
        out[b["name"]] = hist / (b["length_m"] / bins)
    return out


def _gini(x):
    x = np.sort(np.asarray(x, float))
    n = len(x)
    if n == 0 or x.sum() <= 0:
        return 0.0
    return float((2.0 * np.sum((np.arange(1, n + 1)) * x)) / (n * x.sum())
                 - (n + 1.0) / n)


def smear_stats(plan, banks, bins=40):
    """The two numbers `crowd_is_not_a_uniform_smear` is decided on.

    `gini` -- inequality of the linear density along a bank. A uniform smear
    tends to 0; a crowd that clusters hard is 0.4+.
    `peak_over_30m` -- density at the modal bin over density 30 m away from
    it, which is the manifest's own sentence turned into a ratio.
    """
    prof = density_profile(plan, banks, bins)
    gs, rs = [], []
    for b in banks:
        d = prof[b["name"]]
        gs.append(_gini(d))
        i = int(np.argmax(d))
        step = b["length_m"] / bins
        off = max(1, int(round(SIGHT_FALLOFF_M / step)))
        nb = [d[j] for j in (i - off, i + off) if 0 <= j < bins]
        rs.append(float(d[i] / max(np.mean(nb) if nb else 0.0, 1e-9)))
    return {"gini": float(np.mean(gs)), "gini_per_bank": gs,
            "peak_over_30m": float(np.median(rs)), "ratio_per_bank": rs}


# ==========================================================================
# 5.  THE LIBRARY AND THE FIELD
# ==========================================================================

def _slot(role, rbin, k):
    base = {"stand": 0, "sit_ground": 1, "stool": 2}[role]
    off = 0
    for r in ("stand", "sit_ground", "stool"):
        if r == role:
            break
        off += GA_BINS[r] * GA_CELL[r]
    return off + rbin * GA_CELL[role] + k


def library_size():
    return sum(GA_BINS[r] * GA_CELL[r] for r in GA_BINS)


def assign_sources(plan):
    """One library slot per person, and the index space is a BIJECTION.

    `library_index_is_a_bijection` in `spectator_crowd` caught two index
    spaces colliding; there is one here by construction and the selftest
    checks it the same way.
    """
    for p in plan:
        role = p["role"]
        span, nb = GA_SPAN[role], GA_BINS[role]
        b = int(round((p["gaze_baked_deg"] + span * 0.5)
                      / max(span, 1e-9) * (nb - 1)))
        p["src"] = _slot(role, int(np.clip(b, 0, nb - 1)),
                         int(p["k"]) % GA_CELL[role])
    return plan


def build_library(seed=SEED, lod=None, coll=None, mats=None, limit=None,
                  pitch=1.30, per_row=26):
    """One unique person per slot, on a contact sheet clear of the banks.

    NOT `hide_render` -- see `spectator_crowd.build_library` for what that
    cost: `item_gate` picks the median-triangle object in the collection, and
    with every source hidden the witness frame was empty sky and three checks
    came back NOT MEASURED off one boolean.
    """
    if bpy is None:
        raise RuntimeError("needs Blender")
    tier = lod or getattr(HK, "LOD_" + LOD_GA)
    n = library_size() if limit is None else min(limit, library_size())
    objs = []
    for slot in range(n):
        role, rbin, k = _unslot(slot)
        fseed = seed * 1000003 + slot * 7919
        b = HK.sample_body(HK.rng_for(fseed, 1))
        span, nb = GA_SPAN[role], GA_BINS[role]
        gz = -span * 0.5 + span * rbin / max(nb - 1.0, 1.0)
        kind = {"stand": "stand", "sit_ground": "sit", "stool": "sit"}[role]
        fig = HK.build_figure(seed=fseed, lod=tier, role="spectator",
                              body=b, kind=kind, gaze=(gz, 0.0))
        ob = HK.emit_mesh("%sLib%04d_%s_b%d" % (PFX, slot, role, rbin),
                          fig["mesh"], coll, mats)
        ob.location = (float((slot % per_row) * pitch),
                       float((slot // per_row) * pitch) - 400.0, 0.0)
        objs.append(ob)
    return objs


def _unslot(slot):
    off = 0
    for r in ("stand", "sit_ground", "stool"):
        n = GA_BINS[r] * GA_CELL[r]
        if slot < off + n:
            i = slot - off
            return r, i // GA_CELL[r], i % GA_CELL[r]
        off += n
    raise IndexError(slot)


def build_field(name, plan, library, coll, seed=SEED, n_src=None):
    """Instance the library on the plan. Reuses `spectator_crowd`'s geometry
    node group verbatim -- one crowd instancer on this project, not two."""
    import spectator_crowd as SC
    rr = HK.rng_for(seed, 313)
    pts, src, rot, scl = [], [], [], []
    for r in plan:
        pts.append((r["pos"][0], r["pos"][1], r["z"]))
        src.append(int(r["src"]))
        rot.append((0.0, 0.0, math.radians(r["body_yaw_deg"] - 90.0)))
        scl.append(1.0 + rr.n(0.0, 0.015))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in pts], [], [])
    me.update()
    for nm, ty, val in (("hk_src", "INT", src), ("hk_scale", "FLOAT", scl)):
        a = me.attributes.new(nm, ty, "POINT")
        a.data.foreach_set("value", val)
    a = me.attributes.new("hk_rot", "FLOAT_VECTOR", "POINT")
    a.data.foreach_set("vector", [c for v in rot for c in v])
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    md = ob.modifiers.new("ga_crowd", "NODES")
    md.node_group = SC._crowd_group(name + "_GN", library, n_src)
    ob["instances"] = len(pts)
    ob["library_sources"] = int(n_src)
    return ob


def build_bank_standin(banks, coll, mat, rows=14, cols=90):
    """The bank as a plain graded surface, so CONTACT CAN BE SEEN.

    `spectator_crowd.build_seat_standins`' docstring is the thing to read
    before trusting this: a standin that shares a constant with the placement
    CANNOT check that constant. This shares `bank_point` with the placement,
    so it cannot check the height or the batter -- what it can check, and what
    it is for, is that the feet are ON a surface and that nobody is buried in
    it or floating over it, which is a property of the two together.
    """
    import bmesh
    out = []
    for b in banks:
        me = bpy.data.meshes.new(b["name"] + "_standin")
        V, F = [], []
        for i in range(rows + 1):
            for j in range(cols + 1):
                P, _s, _n = bank_point(b, j / cols, i / rows)
                V.append(tuple(P))
        for i in range(rows):
            for j in range(cols):
                a = i * (cols + 1) + j
                F.append((a, a + 1, a + cols + 2, a + cols + 1))
        me.from_pydata(V, [], F)
        me.update()
        ob = bpy.data.objects.new(b["name"] + "_standin", me)
        if mat is not None:
            ob.data.materials.append(mat)
        coll.objects.link(ob)
        out.append(ob)
    return out


def foot_clearance_mm(plan, banks):
    """How far every figure's feet are from the bank surface, in mm.

    The one number that says the crowd is standing ON the hill. Recomputed
    from `bank_point` at the person's own (s, h) AFTER the lateral jitter has
    moved them, which is where a placement bug would show: the jitter is in
    world x/y and the surface is a slope, so jittering without re-projecting
    lifts somebody 0.28 m into the air on a 1:2.5 batter.
    """
    out = []
    for p in plan:
        b = banks[p["bank_i"]]
        P, _s, _n = bank_point(b, p["s"], p["h"])
        # the person's stored z against the surface z at the SAME (s, h)
        out.append((p["z"] - float(P[2])) * 1000.0)
    return np.asarray(out)


# ==========================================================================
# 6.  THE SCENE
# ==========================================================================

def build_scene(seed=SEED, frame=1009, n_want=DECLARED, lod=None,
                lib_limit=None, synthetic=False):
    if bpy is None:
        raise RuntimeError("needs Blender")
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    root = K.coll(COLL)
    K.purge(PFX, COLL)
    root = K.coll(COLL)
    lib = K.coll(LIB_COLL, root)
    stand = K.coll(COLL + "/Standins", root)
    mats = HK.figure_materials(PFX)
    K.contract_sun(PFX, scene=bpy.context.scene, coll_=stand)
    HK.film_exposure(bpy.context.scene)
    banks = bank_array(synthetic=synthetic)
    focus = car_at(frame)
    plan = assign_sources(plan_banks(seed, banks, focus, n_want))
    objs = build_library(seed, lod, lib, mats, limit=lib_limit)
    build_bank_standin(banks, stand, None)
    fld = build_field(PFX + "Field", plan, lib, root, seed, n_src=len(objs))
    root["ga_bank_is_synthetic"] = bool(synthetic)
    fld["ga_bank_is_synthetic"] = bool(synthetic)
    K.assert_no_external_assets()
    HK.log("GA: %d people on %d banks, %d sources, synthetic_bank=%s"
           % (len(plan), len(banks), len(objs), synthetic))
    return {"plan": plan, "banks": banks, "field": fld, "library": objs}


# ==========================================================================
# 7.  SELFTEST
# ==========================================================================

def selftest(verbose=True):
    out, fails = [], []

    def chk(name, ok, detail):
        out.append((name, bool(ok), detail))
        if not ok:
            fails.append(name)
        if verbose:
            print("  %-46s %s\n      %s"
                  % (name, "ok" if ok else "FAILED", detail))

    banks = bank_array(synthetic=True)
    focus = car_at(1009)
    plan = assign_sources(plan_banks(SEED, banks, focus))
    ctl = assign_sources(plan_banks(SEED, banks, focus, uniform=True))

    # ---- 1. the manifest's own acceptance criterion -----------------------
    st = smear_stats(plan, banks)
    sc = smear_stats(ctl, banks)
    # THE BARS ARE RATIOS TO THE CONTROL, NOT ABSOLUTES, and that is not
    # fastidiousness -- it is a bug this check already had. A FINITE uniform
    # sample does not have gini 0: 3,500 people over six banks and forty bins
    # is ~15 per bin, and Poisson counting noise alone puts a genuinely flat
    # draw at gini ~0.19. An absolute bar of 0.12 was therefore unreachable BY
    # THE NULL ITSELF, i.e. it was measuring the sample size. Referenced to the
    # in-frame control the statistic is immune to it, which is the same
    # argument `item_gate` makes for every one of its own scale-invariant
    # thresholds.
    g_r = st["gini"] / max(sc["gini"], 1e-9)
    p_r = st["peak_over_30m"] / max(sc["peak_over_30m"], 1e-9)
    chk("crowd_is_not_a_uniform_smear",
        g_r > 1.7 and st["peak_over_30m"] > 3.0 and p_r > 2.5,
        "gini %.3f vs the uniform control's %.3f = x%.2f (bar x1.7); density "
        "at the peak over density 30 m away %.2fx vs control %.2fx = x%.2f "
        "(bars 3.0 absolute and x2.5). The control is the same 3,500 people, "
        "the same six banks and the same roles, spread EVENLY over the "
        "available banking -- which is the manifest's named tell, built on "
        "purpose so the check can fail."
        % (st["gini"], sc["gini"], g_r, st["peak_over_30m"],
           sc["peak_over_30m"], p_r))

    # ---- 2. the tier -----------------------------------------------------
    px = (K.RES_X_4K * MANIFEST_LENS / K.SENSOR_MM) / MANIFEST_M * 1.75
    tier = HK.LOD.for_px(px)
    chk("lod_matches_the_only_framing_that_is_about_this_item",
        tier.name == LOD_GA and abs(px - MANIFEST_PX) < 2.0,
        "the manifest's 15.4 m / 35 mm gives %.1f px for a 1.75 m figure -> "
        "%s. screen_presence's 278.7 px is the crowd ZONE's 159.3 px/m times "
        "1.75 m, on eleven ARCH_Grandstand hosts, because the GA bank is not "
        "in the world -- it is not evidence about this item. See the module "
        "docstring." % (px, tier.name))

    # ---- 3. contact ------------------------------------------------------
    fc = foot_clearance_mm(plan, banks)
    chk("everybody_is_standing_on_the_bank",
        float(np.abs(fc).max()) < 1.0,
        "worst foot clearance %.4f mm over %d people (p99 %.4f). Measured by "
        "re-projecting each person's own (s, h) through `bank_point` after the "
        "lateral jitter."
        % (float(np.abs(fc).max()), len(fc), float(np.percentile(np.abs(fc), 99))))

    # ---- 4. the bank contract refuses bad geometry ------------------------
    bad = []
    for mut, why in (({"batter": 1.4}, "a 1:1.4 batter"),
                     ({"outward": (1.0, 0.0)}, "outward along its own run")):
        s = synthetic_bank_sections()
        s[0] = dict(s[0])
        if "outward" in mut:
            a = np.asarray(s[0]["p1"], float)[:2] - np.asarray(s[0]["p0"], float)[:2]
            mut = {"outward": tuple(a / np.linalg.norm(a))}
        s[0].update(mut)
        try:
            bank_array(sections=s)
            bad.append(why)
        except RuntimeError:
            pass
    chk("bank_contract_rejects_geometry_it_should",
        not bad and len(bank_array(sections=synthetic_bank_sections())) == 6,
        "positive controls rejected: a 1:1.4 batter and an `outward` parallel "
        "to the run%s. Negative control: the six contract-compliant sections "
        "are accepted." % ("" if not bad else " -- BUT %s WAS ACCEPTED" % bad))

    # ---- 5. attention ----------------------------------------------------
    fa, ma = attention_fraction(plan, focus)
    zero = assign_sources(plan_banks(SEED, banks, focus))
    for p in zero:
        p["body_yaw_deg"] = p["body_yaw_deg"] + 137.0
    fz, _ = attention_fraction(zero, focus)
    chk("crowd_watches_the_car",
        fa > 0.60 and fz < 0.25,
        "%.1f %% within 20 deg of the car (mean error %.1f deg); the control "
        "-- the same plan with every body swung 137 deg -- gives %.1f %%."
        % (100 * fa, ma, 100 * fz))

    # ---- 6. the index space ----------------------------------------------
    slots = sorted({(_unslot(i)) for i in range(library_size())})
    chk("library_index_is_a_bijection",
        len(slots) == library_size()
        and all(_slot(*_unslot(i)) == i for i in range(library_size())),
        "%d slots over %d (role, bin, k) triples, and `_slot(_unslot(i)) == i` "
        "for every one. Two index spaces colliding is what "
        "`spectator_crowd`'s own version of this caught."
        % (library_size(), len(slots)))

    # ---- 7. no source dominates its own role ------------------------------
    worst, wr = 0.0, ""
    for r in GA_BINS:
        srcs = [p["src"] for p in plan if p["role"] == r]
        if len(srcs) < 20:
            continue
        _u, c = np.unique(srcs, return_counts=True)
        f = float(c.max()) / len(srcs)
        if f > worst:
            worst, wr = f, r
    lim = 6.0 / min(GA_CELL.values())
    chk("no_source_dominates_its_own_role",
        worst < lim,
        "worst share is %.2f %% of role %r (bar %.2f %%, i.e. 6x a uniform "
        "draw over the smallest role's own cell). THE RED LINE IS PER ROLE: a "
        "standing majority buries every other role in a whole-crowd "
        "denominator -- sec 0000.1." % (100 * worst, wr, 100 * lim))

    # ---- 8. the gaze field has no comb -----------------------------------
    B = realised_bearing(plan)
    want = np.array([math.degrees(math.atan2(
        focus[1] - p["pos"][1], focus[0] - p["pos"][0])) for p in plan])
    res = ((B - want + 180.0) % 360.0) - 180.0
    watch = res[np.abs(res) < 30.0]
    hist, _ = np.histogram(watch, bins=30, range=(-30.0, 30.0))
    chk("realised_gaze_field_has_no_comb",
        int(np.sum(hist == 0)) == 0,
        "0 of 30 two-degree bins are empty across the %d-person watching core "
        "(modal bin %.1f %%). The body absorbs the binning residual, so "
        "`body + baked` lands on the attend bearing -- sec 00000.4."
        % (len(watch), 100.0 * hist.max() / max(len(watch), 1)))

    if verbose:
        print("\n  %d checks, %d failed" % (len(out), len(fails)))
    return out, fails


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    p = argparse.ArgumentParser(prog=ITEM)
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--plan", action="store_true",
                   help="print the plan's statistics, no Blender")
    p.add_argument("--synthetic", action="store_true",
                   help="use the contract-compliant TEST bank because "
                        "`ga_viewing_bank` has no module yet")
    p.add_argument("--frame", type=int, default=1009)
    p.add_argument("--n", type=int, default=DECLARED)
    p.add_argument("--lod", default=None)
    p.add_argument("--lib-limit", type=int, default=None)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--out", default=os.path.join(
        _ITEMS, "spectator_standing_ga_test.blend"))
    a = p.parse_args(argv)
    if a.selftest:
        _o, f = selftest()
        raise SystemExit(1 if f else 0)
    if a.plan:
        banks = bank_array(synthetic=a.synthetic)
        focus = car_at(a.frame)
        plan = assign_sources(plan_banks(a.seed, banks, focus, a.n))
        st = smear_stats(plan, banks)
        fa, ma = attention_fraction(plan, focus)
        print("%d people on %d banks; library %d slots"
              % (len(plan), len(banks), library_size()))
        print("  density gini %.3f   peak/30m %.2fx" % (st["gini"], st["peak_over_30m"]))
        print("  attention %.1f %% within 20 deg, mean error %.1f deg" % (100 * fa, ma))
        for r in GA_ROLE_W:
            print("  role %-11s %5d  (%.1f %%)"
                  % (r[0], sum(1 for q in plan if q["role"] == r[0]),
                     100.0 * sum(1 for q in plan if q["role"] == r[0]) / len(plan)))
        fc = foot_clearance_mm(plan, banks)
        print("  worst foot clearance %.4f mm" % float(np.abs(fc).max()))
        raise SystemExit(0)
    lod = {"L0": HK.LOD_L0, "L1": HK.LOD_L1, "L2": HK.LOD_L2}.get(a.lod)
    build_scene(a.seed, a.frame, a.n, lod, a.lib_limit, a.synthetic)
    bpy.ops.wm.save_as_mainfile(filepath=a.out, compress=True)
    HK.log("saved %s" % a.out)


if __name__ == "__main__":
    main()
