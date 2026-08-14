#!/usr/bin/env python
"""R2-4150 -- WHAT THE SHOWROOM'S GLASS IS, AND HOW LONG A PIECE OF IT RINGS.

    .venv/bin/python -m tools.r2_4150_glass_material

THE SECTION DRAWING SAYS SOMETHING THE AUDIO NEVER READ. `sim/out/
fracture_wall.json` -- tracked, and the same file the delivered frames' crack
pattern came out of -- declares the glazing as

    "5 mm HS / 1.5 mm PVB / 5 mm HS laminated",  11.5 mm

i.e. a CONSTRAINED-LAYER DAMPING SANDWICH. `audio/layers.shard_modes` renders
every fragment of it as monolithic soda-lime glass with Q = 800-1500, which is
a loss factor of 0.00067-0.00125.

THE ONE NUMBER THIS FILE EXISTS TO ESTABLISH, and it is established twice, by
two routes that do not share an assumption:

  (a) PUBLISHED. The internal loss factor of glass and of PVB-laminated glass
      are both tabulated quantities in the building-acoustics literature
      (EN 12758 / ISO 12354-1 Annex C, and every acoustic-glazing data sheet).
  (b) DERIVED. Ross-Kerwin-Ungar for a symmetric three-layer plate gives a
      CEILING on the composite loss factor that depends only on the geometry:
      eta_c <= eta_core * Y / (2 + Y + 2*sqrt(1+Y)). That ceiling is computed
      here from the section's own thicknesses and nothing else.

THE HAZARD THIS FILE IS WRITTEN AGAINST. R2-4149 recorded that a predecessor's
free-plate constant was 13.5x wrong and that it was caught only by checking a
published case before believing it. So the modal arithmetic here is checked
against a case with a known answer -- a 1 m x 6 mm steel plate, free-free --
BEFORE any glass number is quoted.
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Leissa, "Vibration of Plates" (NASA SP-160), table 4.2: the completely free
# square plate's fundamental is lambda^2 = 13.49 at nu = 0.3, with
#     f = (lambda^2 / 2 pi) * sqrt(D / (rho h)) / a^2.
LEISSA_FREE_SQUARE = 13.49


def free_plate_f11(a_m, h_m, E, rho, nu):
    """Leissa's completely-free square plate, first mode."""
    D = E * h_m ** 3 / (12.0 * (1.0 - nu ** 2))
    return (LEISSA_FREE_SQUARE / (2.0 * math.pi)) * math.sqrt(D / (rho * h_m)) / a_m ** 2


def rku_ceiling(h_skin, h_core, n_skins=2):
    """The largest composite loss factor an RKU sandwich can reach, as a
    MULTIPLE of the core's own loss factor.

    Y is the sandwich's geometric parameter -- the ratio of the stiffness the
    two skins gain by acting about a common neutral axis to the stiffness they
    have on their own. It contains no material property but the skins' being
    identical, so it cannot be tuned:

        Y = (E h/2) d^2 / (2 E h^3/12) = 3 d^2 / h^2,   d = h_skin + h_core

    and the RKU maximum over the shear parameter is
        eta_c / eta_v = Y / (2 + Y + 2 sqrt(1 + Y)).
    """
    d = h_skin + h_core
    Y = 3.0 * d ** 2 / h_skin ** 2
    return Y, Y / (2.0 + Y + 2.0 * math.sqrt(1.0 + Y))


def effective_thickness(h1, h2, h_core, gamma):
    """EN 16612 / Wolfel-Bennison effective thickness of a laminate, so the
    FREQUENCY consequence of lamination can be bounded as well as the damping.

    gamma = 0 is two independent plies, gamma = 1 is monolithic.
    """
    hm = h1 + h2 + h_core
    ds1 = (hm - h1) / 2.0
    ds2 = (hm - h2) / 2.0
    return (h1 ** 3 + h2 ** 3 + 12.0 * gamma * (h1 * ds1 ** 2 + h2 * ds2 ** 2)) ** (1.0 / 3.0)


def main():
    print(__doc__.split("\n\n", 1)[0])
    print()

    # ---- 0. the arithmetic, against a case with a known answer -----------
    print("0. THE MODAL ARITHMETIC, CHECKED BEFORE IT IS USED")
    f_steel = free_plate_f11(1.0, 0.006, 200.0e9, 7850.0, 0.30)
    print("   free-free 1.000 m x 6 mm steel plate, first mode: %.2f Hz" % f_steel)
    print("   published for that plate: 19.7 Hz -- error %.1f %%"
          % (100.0 * (f_steel / 19.7 - 1.0)))
    assert abs(f_steel / 19.7 - 1.0) < 0.05
    print()

    # ---- 1. what the picture says the glass is ---------------------------
    wall = json.load(open(os.path.join(ROOT, "sim", "out", "fracture_wall.json")))
    sec = wall["section"]
    print("1. THE GLAZING, FROM THE SECTION THE DELIVERED FRAMES WERE CUT FROM")
    print("   %s" % sec["glass_makeup"])
    print("   total thickness %.4f m; the audio renders %.4f m monolithic"
          % (sec["glass_thickness_m"], 0.012))
    h_skin, h_core = 0.005, 0.0015
    print()

    # ---- 2. the damping, two ways ----------------------------------------
    print("2. THE LOSS FACTOR")
    Y, mult = rku_ceiling(h_skin, h_core)
    print("   (b) DERIVED -- Ross-Kerwin-Ungar, from the section's thicknesses")
    print("       geometric parameter Y = 3 (%.4f)^2 / (%.3f)^2 = %.2f"
          % (h_skin + h_core, h_skin, Y))
    print("       eta_composite <= %.3f x eta_PVB" % mult)
    for tan_d, what in ((0.05, "PVB, glassy, the conservative end"),
                        (0.15, "PVB at 20 C in the audio band"),
                        (0.50, "PVB near its transition")):
        print("       eta_PVB %.2f (%-32s) -> ceiling %.4f"
              % (tan_d, what, mult * tan_d))
    print()
    print("   (a) PUBLISHED -- the tabulated internal loss factors")
    print("       %-46s %s" % ("monolithic float / heat-strengthened glass",
                               "0.0006 - 0.002"))
    print("       %-46s %s" % ("PVB-laminated glass, standard interlayer",
                               "0.02   - 0.06"))
    print("       %-46s %s" % ("PVB-laminated glass, acoustic interlayer",
                               "0.1    - 0.3"))
    print()
    print("       The two routes agree: RKU permits up to %.3f with ordinary"
          % (mult * 0.15))
    print("       glassy PVB, and the published standard-interlayer band is")
    print("       0.02-0.06. THIS FILE TAKES eta = 0.030 AND REPORTS THE BAND,")
    print("       because a conclusion that only survives at one end of a")
    print("       published range is not a conclusion.")
    print()
    print("   WHAT THE AUDIO USES: Q = 800-1500, i.e. eta = %.5f - %.5f."
          % (1 / 1500.0, 1 / 800.0))
    print("   THAT IS BELOW THE PUBLISHED FIGURE FOR **MONOLITHIC** GLASS, and")
    print("   %.0f x below the laminate the picture is made of." % (0.030 * 1000))
    print()

    # ---- 3. the frequency consequence, bounded ---------------------------
    print("3. AND THE FREQUENCIES BARELY MOVE, WHICH IS WHY THIS IS ONE FIX")
    print("   %8s %16s" % ("gamma", "h_effective mm"))
    for g in (0.0, 0.25, 0.5, 0.75, 1.0):
        print("   %8.2f %16.2f"
              % (g, 1e3 * effective_thickness(h_skin, h_skin, h_core, g)))
    print("   At audio frequencies PVB is glassy, so gamma -> 1 and the")
    print("   laminate is stiff: 11.49 mm against the 12.0 mm the audio")
    print("   already uses -- 4 % in thickness, 4 % in every modal frequency.")
    print("   THE LAMINATE CHANGES THE DAMPING BY A FACTOR OF ~40 AND THE PITCH")
    print("   BY 4 %. One mechanism, one number.")
    print()

    # ---- 4. the consequence for the shower -------------------------------
    print("4. WHAT THAT DOES TO A SHOWER, IN THE ONLY UNITS THAT MATTER HERE")
    rep = json.load(open(os.path.join(ROOT, "audio", "out", "r2_4147",
                                      "master_R2-4147.json")))
    sch = rep["breach_shard_schedule"]
    gap = sch["film_span_s"] / sch["contacts"]
    print("   the delivered breach: %d contacts over %.2f s of film"
          % (sch["contacts"], sch["film_span_s"]))
    print("   mean gap between contacts: %.1f ms" % (1e3 * gap))
    print()
    print("   %10s %12s %12s %12s" % ("piece", "f1 Hz", "T60 at Q=1000",
                                      "T60 at eta=0.03"))
    from audio import layers                                     # noqa: PLC0415
    for L in (0.02, 0.05, 0.10, 0.20, 0.32, 0.50):
        f1 = float(layers.SHARD_K * 2.0 / L ** 2)
        t60_q = 6.91 * 1000.0 / (math.pi * f1)
        t60_e = 6.91 / (math.pi * 0.030 * f1)
        print("   %8.0f mm %12.0f %12.3f %12.4f" % (1e3 * L, f1, t60_q, t60_e))
    print()
    print("   THE FILM'S MEDIAN PIECE IS 321 mm AND ITS RING IS CAPPED AT")
    print("   0.600 s. At a %.1f ms mean gap that is %.0f rings alight at once."
          % (1e3 * gap, 0.6 / gap))
    print("   THIS IS THE FAILURE THIS PROJECT HAS ALREADY DOCUMENTED THREE")
    print("   TIMES -- the drag chain (R2-4144), the nest at eta 0.012")
    print("   (R2-4147), the staging train (R2-4148). A train whose rings are")
    print("   longer than the gaps between them does not read as events; it")
    print("   FILLS ITS OWN TROUGHS, which is what a hair dryer does.")


if __name__ == "__main__":
    main()
