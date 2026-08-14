#!/usr/bin/env python
"""R2-4150 -- THE BREACH, ABLATED. TWO CHANGES, MEASURED SEPARATELY AND
TOGETHER, WITH EVERY CONTROL RUN BEFORE ANY OF IT IS BELIEVED.

    .venv/bin/python -m tools.r2_4150_breach_bench [--full]

The rebuild lives in `tools/r2_4150_breach_rebuild.py` as a PATCH, not in
`audio/layers.py`, because it was rendered end to end and **the delivered beat
got worse** -- see R2-4150(7). `audio/layers.py` in git therefore still
reproduces the shipped master, which is this project's standing rule.

THE TWO CHANGES
  DAMPING      every fragment rang at Q = 800-1500, eta 0.00067-0.00125, BELOW
               the published internal loss factor of monolithic float glass.
               The picture's glazing is 5 mm HS / 1.5 mm PVB / 5 mm HS
               laminated -- a constrained-layer damping sandwich at eta
               0.02-0.06 published, <= 0.423 x eta_PVB by Ross-Kerwin-Ungar.
  POPULATION   `shard_ballistics` drew its own size law -- 351 pieces, median
               321 mm, MINIMUM 40 mm -- against the delivered frames' 3216 of
               median 21 mm spanning 8-495 mm.

WHAT THIS BENCH REFUSES TO DO. It does not read a knob until a bar is cleared.
The eta sweep prints the WHOLE published band and the conclusion has to hold
across all of it; the legacy population is regenerated rather than deleted so
the 2x2 can be measured; and AMI's own hole -- a single impulse in silence
reads 37 -- is checked against every candidate, because a score that comes from
one bang over a quiet bed is the gate being gamed and not a breach.
"""

import argparse
import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                   # noqa: E402
from audio.clock import Clock                                    # noqa: E402
from tools import r2_4150_breach_rebuild as RB                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEMS = os.path.join(ROOT, "audio", "out", "r2_4147", "stems")
SR = 96000
BREACH = (36.0, 44.0)
V_CONTACT = 16.70928590302728          # the render's own, from the telemetry
LEGACY_ETA = 1.0 / 1150.0              # midpoint of the retired Q = 800-1500


def ami(x, sr=SR):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    return P.articulation_modulation_index(x, sr).get("ami", float("nan"))


def peak_share(x):
    """FRACTION OF THE ENERGY IN THE LOUDEST 20 ms. AMI's hole is one impulse
    in silence; anything scoring by a single bang shows up here."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    w = int(0.020 * SR)
    m = (x ** 2)[:len(x) // w * w].reshape(-1, w).sum(axis=1)
    return float(m.max() / max(m.sum(), 1e-30))


class Bench:
    def __init__(self, stems=STEMS):
        self.spec = json.load(open(os.path.join(ROOT, "docs", "circuit_spec.json")))
        self.clock = Clock(os.path.join(ROOT, "docs", "beat_sheet.json"), sr=SR)
        self.a, self.b = int(BREACH[0] * SR), int(BREACH[1] * SR)
        self.sig = {}
        for nm in os.listdir(stems):
            if nm.endswith(".wav"):
                x, _ = sf.read(os.path.join(stems, nm), start=self.a,
                               stop=self.b, always_2d=True)
                self.sig[nm[:-4]] = np.asarray(x, dtype=np.float64)
        self.tot = sum(float((v ** 2).sum()) for v in self.sig.values())
        self.glass_e = float((self.sig["shards"] ** 2).sum()
                             + (self.sig["debris"] ** 2).sum())
        self.rest = sum(v for k, v in self.sig.items()
                        if k not in ("shards", "debris"))

    def field(self, population="picture", eta=RB.LAMINATE_ETA, fines=139950):
        dry, bed, summ, binfo = RB.field(self.spec, self.clock, SR, V_CONTACT,
                                         population=population, eta=eta,
                                         fines_total=fines)
        return (dry[self.a:self.b].astype(np.float64),
                bed[self.a:self.b].astype(np.float64), summ, binfo)

    def in_mix(self, dry, bed, glass_gain_db=0.0):
        """Substitute a glass layer for the delivered one AT THE DELIVERED
        ENERGY and read the sum. This deliberately holds the mix constant --
        R2-4150(7) is what happens when it is not."""
        g = np.stack([dry, dry], axis=1) + np.stack([bed, bed], axis=1)
        g = g * np.sqrt(self.glass_e / max(float((g ** 2).sum()), 1e-30))
        return self.rest + g * 10.0 ** (glass_gain_db / 20.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true",
                    help="also sweep the bed's declared fines total")
    args = ap.parse_args()

    bar = P.V("G_PRESENCE.min_articulation_index")
    B = Bench()
    print("G-PRESENCE's AMI bar is %.2f. The delivered `3_breach` sum reads "
          "%.4f.\n" % (bar, ami(sum(B.sig.values()))))

    print("1. THE 2x2. POPULATION x DAMPING, on the glass layer ALONE")
    print("%-40s %10s %10s %11s" % ("", "AMI", "contacts", "peak 20 ms"))
    cells = {}
    for pop in ("legacy", "picture"):
        for tag, eta in (("Q 800-1500 -- as shipped", LEGACY_ETA),
                         ("laminate eta 0.030", RB.LAMINATE_ETA)):
            dry, bed, summ, binfo = B.field(pop, eta)
            cells[(pop, tag)] = (dry, bed, summ, binfo)
            print("%-40s %10.4f %10d %11.4f"
                  % ("%s population, %s" % (pop, tag), ami(dry + bed),
                     summ["contact_events"], peak_share(dry + bed)))
    print()
    print("   THE SHIPPED COMBINATION IS THE FIRST ROW. The damping is the")
    print("   whole fix and the population is worth 0.017 -- the model this")
    print("   pass inherited was that the population WAS the defect.")
    print()

    print("2. THE SAME FOUR, IN THE MIX, AT THE DELIVERED GLASS ENERGY")
    for k, (dry, bed, _s, _b) in cells.items():
        print("%-40s %10.4f" % ("%s, %s" % k, ami(B.in_mix(dry, bed))))
    print()

    print("3. eta ACROSS THE WHOLE PUBLISHED BAND, picture population")
    print("   published: monolithic glass 0.0006-0.002; PVB laminate")
    print("   0.02-0.06; acoustic PVB 0.1-0.3. RKU ceiling from the section's")
    print("   own thicknesses: 0.063.")
    print("%10s %12s %12s %12s" % ("eta", "1/eta", "glass AMI", "beat AMI"))
    for eta in (0.00087, 0.002, 0.010, 0.020, 0.030, 0.045, 0.060, 0.100):
        dry, bed, _s, _b = B.field("picture", eta)
        mark = "  <- taken" if abs(eta - RB.LAMINATE_ETA) < 1e-9 else ""
        print("%10.5f %12.0f %12.4f %12.4f%s"
              % (eta, 1.0 / eta, ami(dry + bed), ami(B.in_mix(dry, bed)), mark))
    print()
    print("   NO VALUE IN THE PUBLISHED BAND CLEARS THE 0.50 BAR, INCLUDING")
    print("   THE ACOUSTIC-PVB END AT 0.10. That is this pass's protection")
    print("   against its own knob: the result cannot be bought by raising")
    print("   eta, so eta stays in the middle of the band it belongs in.")
    print()

    if args.full:
        print("4. THE BED. Its density was `fines_per_contact` x however many")
        print("   contacts the ballistics happened to make -- so it TRACKED")
        print("   THE SHARD COUNT, which is not a physical quantity.")
        print("%16s %12s %12s %12s"
              % ("declared fines", "fines", "bed AMI", "glass AMI"))
        for f in (1177213, 139950, 40000, 12000):
            d2, b2, _s, bi = B.field("picture", RB.LAMINATE_ETA, fines=f)
            print("%16d %12d %12.4f %12.4f"
                  % (f, bi["fines_events"], ami(b2), ami(d2 + b2)))
        print()
        print("   1,177,213 is what the SHIPPED default silently becomes once")
        print("   the population is correct: 8.4x denser at 113,000 arrivals")
        print("   per second, against a 100 Hz roughness boundary.")


if __name__ == "__main__":
    main()
