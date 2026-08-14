#!/usr/bin/env python
"""R2-4150 -- THE BREACH REBUILD, AS A PATCH. IT IS NOT IN THE RENDER PATH AND
THE REASON IS MEASURED, NOT CAUTIOUS.

The rebuild below was written into `audio/layers.py`, rendered end to end, and
adjudicated. **The glass layer got 4.3x more articulate and the delivered beat
got WORSE**, because the mix trimmed the improved bus 8.38 dB down. See
R2-4150(7)-(9) in `docs/STAGING-R2-4141-to-R2-4200.md` for the numbers. Nothing
shipped, so `audio/layers.py` in git still reproduces
`PART2_AUDIO_MASTER_R2-4147.wav` byte for byte -- which is this project's
standing rule (R2-4149(5)) and the reason this file exists instead of a commit.

`tools/r2_4150_tail_ab.py`-style patching, same contract as R2-4149's:

    from tools.r2_4150_breach_rebuild import patched
    with patched(eta=0.030, population="picture"):
        ev, summ = layers.shard_ballistics(spec, v)

WHAT IT CHANGES, and both are argued in full in the staging entry:

  DAMPING    `shard_modes` rang every fragment at Q = 800-1500 -- eta
             0.00067-0.00125, BELOW the published internal loss factor of
             monolithic float glass. The picture's glazing is
             5 mm HS / 1.5 mm PVB / 5 mm HS laminated (`sim/out/
             fracture_wall.json`), a constrained-layer damping sandwich whose
             composite loss factor is 0.02-0.06 published and <= 0.423 x
             eta_PVB by Ross-Kerwin-Ungar. THIS IS THE WHOLE FIX.

  POPULATION `shard_ballistics` drew its own size law and produced 351 pieces
             of median 321 mm with a MINIMUM of 40 mm, against the delivered
             frames' 3216 of median 21 mm spanning 8-495 mm. A picture desync
             on its own terms; worth 0.017 of AMI and 43x the energy above
             4 kHz, and NOT the fix.
"""

import contextlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import layers                                         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BREACH_SIM_JSON = os.path.join(ROOT, "sim", "out", "breach_sim.json")
FRACTURE_WALL_JSON = os.path.join(ROOT, "sim", "out", "fracture_wall.json")

# The middle of the published PVB-laminate band, inside the RKU ceiling of
# 0.423 x eta_PVB = 0.063 for this section. `tools/r2_4150_glass_material.py`
# derives both and checks its own plate arithmetic against a published case
# first.
LAMINATE_ETA = 0.030
LAMINATE_ETA_PUBLISHED = (0.020, 0.060)

_CACHE = {}


def picture_fragments():
    """THE FRAGMENTS THE DELIVERED FRAMES CONTAIN, read rather than invented.

    `sim/fracture.py` partitions every pane -- radials first, then hoops
    arrested on them, then a mosaic coarsening outward, with the 16 mm clamped
    under the pressure plate holding SLABS -- and publishes one record per shard
    in `sim/out/breach_sim.json`, which is TRACKED and is the same partition the
    4K frames were rendered from.

    Validated against the delivered bake (`sim/out/breach_film.npz`, untracked,
    used here only as evidence): of the 3016 shards in the bays the section
    destroys, **2936 displace more than 0.5 m** and 2837 reach the floor, while
    the other four bays contribute 24 pieces between them. The bay test is
    therefore the picture's own answer to "which glass comes down", to 97 %.

    Returns (L_m, mass_kg, origin_xyz, clamped).
    """
    if "frags" in _CACHE:
        return _CACHE["frags"]
    with open(FRACTURE_WALL_JSON) as fh:
        wall = json.load(fh)
    gone = {b["uid"] for b in wall["breach_state"] if b["beat3"] == "destroyed"}
    with open(BREACH_SIM_JSON) as fh:
        meta = json.load(fh)["shard_meta"]
    keep = sorted((m for m in meta if m["bay"] in gone), key=lambda m: m["name"])
    out = (np.sqrt(np.array([m["area"] for m in keep], dtype=np.float64)),
           np.array([m["mass"] for m in keep], dtype=np.float64),
           np.array([m["origin"] for m in keep], dtype=np.float64),
           np.array([bool(m["clamped"]) for m in keep]))
    _CACHE["frags"] = out
    return out


def legacy_fragments(spec, seed=31337, max_shards=2200):
    """THE SIZE LAW THE REBUILD REPLACED, verbatim from R2-4149, so the 2x2 can
    be measured rather than asserted."""
    ap = spec["showroom"]["breach_aperture_m"]
    W, H = float(ap["width"]), float(ap["height"])
    cx, cy, cz = ap["centre_world"]
    rng = np.random.default_rng(seed)
    L, org = [], []
    area = 0.0
    while area < W * H and len(L) < max_shards:
        y = rng.uniform(-W * 0.5, W * 0.5)
        z = rng.uniform(cz - H * 0.5, cz + H * 0.5)
        d = float(np.hypot(y - 0.0, z - 0.60))
        s = (0.030 + 0.34 * np.clip(d / 3.2, 0.0, 1.0)) * float(rng.lognormal(0.0, 0.45))
        s = float(np.clip(s, 0.015, 0.75))
        area += s * s
        L.append(s)
        org.append([cx, y, z])
    L = np.array(L)
    return (L, layers.GLASS_RHO * layers.GLASS_H * L ** 2, np.array(org),
            np.zeros(len(L), dtype=bool))


def laminate_shard_modes(eta=LAMINATE_ETA):
    """`layers.shard_modes` with the laminate's loss factor.

    tau_n = 1 / (pi eta f_n). The draw is lognormal about eta because a loss
    factor is a ratio and its scatter is multiplicative; at sigma 0.25 the
    middle 95 % spans 0.0184-0.0490 for eta = 0.030.
    """
    orig = layers.shard_modes

    def modes(L, rng, **kw):
        f, amps, _tau, _q = orig(L, rng, **kw)
        e = float(eta * rng.lognormal(0.0, 0.25))
        return f, amps, 1.0 / (np.pi * e * f), 1.0 / e
    return modes


def rebuilt_ballistics(spec, v_contact, fragments, seed=31337):
    """`layers.shard_ballistics`'s mechanics, on a GIVEN fragment population.

    The launch law, the drag, the bounces and the event tuple are unchanged --
    only where each piece starts and how heavy it is comes from outside. The
    integration is vectorised over shards because the population went from 351
    to 3216 and the step is identical either way.
    """
    ap = spec["showroom"]["breach_aperture_m"]
    cx, cy, cz = ap["centre_world"]
    rng = np.random.default_rng(seed)
    Ls, ms, org, clamped = fragments
    ns = Ls.shape[0]
    impact = np.array([cx, 0.0, 0.60])

    p0 = org.copy()
    p0[:, 0] = cx
    rad = p0 - impact[None, :]
    rad[:, 0] = 0.0
    d = np.hypot(rad[:, 1], rad[:, 2])
    nrm = np.maximum(np.linalg.norm(rad, axis=1), 1e-6)
    rad = rad / nrm[:, None]
    rad[d <= 1e-6] = np.array([0.0, 1.0, 0.0])
    sp = v_contact * np.exp(-d / 2.6) * rng.uniform(0.25, 1.15, ns)
    v0 = rad * sp[:, None]
    v0[:, 0] += v_contact * rng.uniform(0.35, 0.95, ns)
    v0 += rng.normal(0.0, 1.4, (ns, 3))
    # a clamped piece is still bolted to something when the pane goes: the
    # section's 16 mm bite is in compression and does not participate in the
    # dice, so those pieces come away later and slower
    v0[clamped] *= 0.45

    K_DRAG = 0.5 * 1.204 * 1.2 / (layers.GLASS_RHO * layers.GLASS_H)
    DT = 1.0 / 480.0
    p, v = p0.copy(), v0.copy()
    bounce = np.zeros(ns, dtype=np.int64)
    alive = np.ones(ns, dtype=bool)
    events, debris_x = [], []
    t = 0.0
    for _step in range(int(6.0 / DT)):
        if not alive.any():
            break
        idx = np.flatnonzero(alive)
        vv = v[idx]
        acc = -K_DRAG * np.linalg.norm(vv, axis=1)[:, None] * vv
        acc[:, 2] -= layers.G
        vv = vv + acc * DT
        pp = p[idx] + vv * DT
        t += DT
        hit = pp[:, 2] <= 0.0
        if hit.any():
            h = idx[hit]
            pp[hit, 2] = 0.0
            vz_in = np.abs(vv[hit, 2])
            e = 0.30 * rng.uniform(0.6, 1.25, h.shape[0])
            ph = pp[hit]
            for k in range(h.shape[0]):
                events.append((t, ph[k].copy(), int(h[k]), float(vz_in[k]),
                               int(bounce[h[k]]), float(Ls[h[k]])))
                debris_x.append(float(ph[k][0]))
            vv[hit, 0] *= 0.72
            vv[hit, 1] *= 0.72
            vv[hit, 2] = vz_in * e
            pp[hit, 2] = 1e-3
            bounce[h] += 1
            alive[h[(vv[hit, 2] < 0.30) | (bounce[h] >= 4)]] = False
        p[idx] = pp
        v[idx] = vv
    events.sort(key=lambda e_: e_[0])
    dx = np.array(debris_x) if debris_x else np.array([15.0])
    summary = {
        "shards": int(ns), "contact_events": len(events),
        "glass_area_m2": float((Ls ** 2).sum()),
        "glass_mass_kg": float(ms.sum()),
        "contact_speed_ms": float(v_contact),
        "shard_size_min_m": float(Ls.min()),
        "shard_size_median_m": float(np.median(Ls)),
        "shard_size_max_m": float(Ls.max()),
        "shards_clamped": int(clamped.sum()),
        "settle_world_s": float(max(e_[0] for e_ in events)) if events else 0.0,
        "debris_p80_x_m": float(np.percentile(dx, 80)),
        "debris_p95_x_m": float(np.percentile(dx, 95)),
        "debris_max_x_m": float(dx.max()),
    }
    return events, summary


@contextlib.contextmanager
def patched(eta=LAMINATE_ETA):
    """Swap the laminate's damping into `layers.shard_modes` for a block."""
    orig = layers.shard_modes
    layers.shard_modes = laminate_shard_modes(eta)
    try:
        yield
    finally:
        layers.shard_modes = orig


def field(spec, clock, sr, v_contact, population="picture", eta=LAMINATE_ETA,
          fines_total=139950):
    """One complete dry glass layer: (shards, bed, ballistics summary, bed info).

    `fines_total` is a TOTAL rather than `debris_bed`'s `fines_per_contact`,
    because that parameter multiplied the contact schedule and therefore made
    the bed's density a function of the shard count -- correcting the population
    took the bed from 139,950 fines to 1,177,213 for no physical reason. The
    default is the delivered figure exactly.
    """
    frags = (legacy_fragments(spec) if population == "legacy"
             else picture_fragments())
    with patched(eta):
        ev, summ = rebuilt_ballistics(spec, v_contact, frags)
        onset = clock.film_at_world(
            clock.glass_world_t + np.array([e[0] for e in ev]))
        sh = layers.render_shards(ev, clock.n, sr, onset, groups=4)
        dry = sum(s for s, _c in sh)
    bed, binfo = layers.debris_bed(
        clock.n, sr, onset, np.array([e[5] for e in ev]),
        fines_per_contact=float(fines_total) / max(len(ev), 1))
    binfo["fines_total_declared"] = int(fines_total)
    return dry, bed, summ, binfo
