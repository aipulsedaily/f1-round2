#!/usr/bin/env python
"""R2-4141 -- THE DRAG-CHAIN SWEEP, run because the prediction was wrong.

The chain was added on the reasoning that a moving machine is a train of
contacts rather than a tone with an envelope on it, and that adding the train
would raise the cell's local dynamic range toward the positive control's. IT
DID THE OPPOSITE: the cell alone went from 11.95 dB to 8.35 dB and the layer
from 17.09 to 16.82.

The reason is in the rate. A 50 mm link pitch at 1-5 m/s articulates at 20-100
Hz, so a 20 ms window -- which is what G-EVENT's short-term level is -- always
contains between half an articulation and two. A train that dense does not make
the level fluctuate; it FILLS THE TROUGHS, which is the same thing a hair dryer
does, arrived at from the opposite direction. Density in events is not the same
quantity as density in the envelope, and this is the measurement that separates
them.

This sweeps the level and prints the curve so the value shipped is the measured
one and not the argued one. It renders the cell ONLY -- no part impacts -- so it
runs in seconds.
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                    # noqa: E402
from audio import layers                                          # noqa: E402
from audio.clock import Clock, WorldGrid                          # noqa: E402
from tools.r2_4081_asm_bench import beat1_clusters, _to_measure_sr  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEAT1_S = 33.0

# THE REJECTED VOICE LIVES HERE, not on the render path. It was written into
# `layers.servo_traverse`, measured, and taken out again; keeping it in the tool
# that measured it means the rejection can be reproduced without re-deriving the
# thing that was rejected.
ENERGY_CHAIN_PITCH_M = 0.050   # link pitch of the drag chain on a gantry axis


def energy_chain(sr, v, seed):
    """THE DRAG CHAIN, and it is the voice that makes a moving axis EVENTFUL.

    Every gantry carries its cables in an articulated energy chain, and as the
    carriage travels each link rolls through the chain's bend radius and drops
    onto its own stop. The link pitch is 50 mm for this size of chain, so the
    articulation rate is v / p -- 20 to 100 Hz over this film's commanded feeds.
    That is A RATE, not a pitch: it is an order of magnitude below the 80 Hz
    floor G-SUSTAIN tracks, it sweeps continuously with the carriage, and it
    stops dead when the carriage does.

    WHY IT IS HERE. R2-4141's first build had traverses whose only voice was
    the drive's own order set -- a continuous signal for the length of a move --
    and the cell measured 11.95 dB of local dynamic range on its own, BELOW
    G-EVENT's 13.7 dB bar and only 3.2 dB clear of blower-into-tubes. The
    missing thing was not level and not spectrum: it was that a moving machine
    is a train of contacts, not a tone with an envelope on it. This is the
    physics that was left out, and it is the difference between the two.

    Each articulation is a Hertzian contact into the link's own plate modes
    (a 30 x 50 x 4 mm glass-filled polyamide link, so eta is high and the ring
    is 10-30 ms), scaled by the carriage's kinetic energy at that instant.
    """
    n = v.shape[0]
    rng = np.random.default_rng(seed)
    v_max = max(float(v.max()), 1e-9)
    # phase in LINKS: the number of articulations is the distance travelled
    # divided by the pitch, which is arithmetic and not a rate that was chosen.
    links = np.cumsum(v) / (sr * ENERGY_CHAIN_PITCH_M)
    exc = np.zeros(n)
    k0 = 0
    idx = np.searchsorted(links, np.arange(1.0, float(links[-1]) + 1.0))
    for i in idx[:4000]:
        if i >= n - 4:
            break
        f = layers.hertz_force(sr, 8.0e-4) * float(rng.uniform(0.55, 1.0)) \
            * (v[i] / v_max) ** 2          # kinetic energy of the link
        L = min(len(f), n - i)
        exc[i:i + L] += f[:L]
        k0 += 1
    if k0 == 0:
        return np.zeros(n), 0
    # the link is a small stiff plate; eta 0.12 for glass-filled polyamide, so
    # T60 = 2.2/(eta*pi*f) is 10-30 ms and nothing rings into the next link
    modes = [(620.0, 1.0), (1310.0, 0.62), (2280.0, 0.40), (3610.0, 0.24)]
    return layers._ring_from(sr, modes, exc, 0.12, seed + 3), k0



def cell_only(sr, t_end=BEAT1_S, chain_ratio=0.0):
    """The cell alone, optionally with the drag chain put back in.

    The chain is re-injected by WRAPPING `layers.servo_traverse` rather than by
    editing it, so the render path is measured exactly as it ships and the
    rejected voice cannot come back by accident.
    """
    clock = Clock(os.path.join(ROOT, "docs", "beat_sheet.json"), sr=sr)
    tw = WorldGrid(clock).t
    m = (tw + clock.launch_film_t >= -0.5) & (tw + clock.launch_film_t <= t_end)
    i0, i1 = int(np.argmax(m)), int(len(m) - np.argmax(m[::-1]))
    real = layers.servo_traverse
    if chain_ratio > 0.0:
        def patched(sr_, dur_s, reach_m, arm_hz, seed, **kw):
            y = real(sr_, dur_s, reach_m, arm_hz, seed, **kw)
            v, _al = layers._smoothstep_move(sr_, dur_s, reach_m)
            ch, _k = energy_chain(sr_, v, seed + 401)
            cpk = float(np.abs(ch).max())
            if cpk <= 0:
                return y
            return y + ch / cpk * max(float(np.abs(y).max()), 1e-12) * chain_ratio
        layers.servo_traverse = patched
    try:
        return layers.cell_events(tw[i0:i1], beat1_clusters(), sr,
                                  clock.launch_film_t)
    finally:
        layers.servo_traverse = real


def row(x, sr, label):
    x = np.asarray(x, dtype=np.float64)
    x, sr = _to_measure_sr(x, sr)
    n = min(len(x), int(BEAT1_S * sr))
    ns = P.note_statistics(x[:n], sr, n / sr)
    ldr = P.local_dynamic_range(x[:n], sr)
    return {"label": label, "ldr_median_db": ldr["median_db"],
            "ldr_p25_db": ldr["p25_db"], "note_cover": ns["note_cover"],
            "chord_cover": ns["chord_cover"],
            "held_power_share": ns["held_power_share"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratios", default="0,0.1,0.2,0.35,0.6,0.85")
    ap.add_argument("--sr", type=int, default=96000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rows = []
    for r in [float(v) for v in a.ratios.split(",")]:
        x, info = cell_only(a.sr, chain_ratio=r)
        rr = row(x, a.sr, "chain : drive = %.3g" % r)
        rr["chain_ratio"] = r
        rows.append(rr)
        print("%-22s LDR %6.2f dB (p25 %6.2f)  note %.3f chord %.3f "
              "heldpow %.4f" % (rr["label"], rr["ldr_median_db"],
                                rr["ldr_p25_db"], rr["note_cover"],
                                rr["chord_cover"], rr["held_power_share"]),
              flush=True)
    print("\nG-EVENT bar %.1f dB; C9 positive 21.4-37.4 dB; loudest negative "
          "(blower into tubes) 8.79 dB; hair dryer 4.70; white noise 0.65."
          % P.V("G_EVENT.min_local_dynamic_range_db"))
    if a.out:
        json.dump(rows, open(a.out, "w"), indent=1)
        print(">> " + a.out)


if __name__ == "__main__":
    main()
