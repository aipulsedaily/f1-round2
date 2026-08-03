"""THE FILM'S EXPOSURE. One number, one derivation, one place.

    import film_exposure                       # world/ is already on sys.path
    scene.view_settings.exposure = film_exposure.FILM_EXPOSURE

    python3 world/film_exposure.py --selftest  # gate it against the render

WHY THIS FILE EXISTS
--------------------
Two numbers claimed to be the film's exposure and they were 0.580 stops apart,
maintained independently, with nothing that could ever notice they disagreed:

    world_contract.REFERENCE_EXPOSURE_EXTERIOR  = -3.048   derived, in the contract
    render_setup2.py / render_setup3.py         = -3.628   hardcoded, no comment
    build_terrain.py                            = -3.628   hardcoded a second time

Now there is one expression, `FILM_EXPOSURE`, built FROM the contract's constant,
and everything that renders imports it.  They cannot drift apart because there is
only one of them.

WHICH ONE WAS RIGHT — MEASURED, ON THE 5090, NOT ARGUED
--------------------------------------------------------
`tools/exposure_calibration.py` renders an 18 % lambertian card under
`build_sky`'s actual light beside a 32-rung emissive ladder of known linear
radiance, and reads the card's linear value off the ladder.  Six variants,
decomposing the light; two view transforms that share no code path, required to
agree.  Every number below is from `render/exposure_cal/expcal_measured.json`:

    downwelling irradiance on a horizontal surface, channel mean, W/m2
      sky alone, no atmosphere                     11.1818
      sky + atmosphere, no sun                     12.9655
      sun + sky, no atmosphere                     28.3005
      sun + sky + atmosphere  = THE FILM'S LIGHT   39.0106
      what C.lambert_radiance's inputs predict     25.9851

    an 18 % card therefore renders at   2.2351 (AgX)   2.2133 (Standard)
    -> the exposure that puts it on AgX mid grey is  -3.6343 / -3.6201
    -> the two transforms agree to      0.0141 stops
    -> the closed-form sRGB inverse, a third route, gives 2.2304

**THE HARDCODED -3.628 IS RIGHT, TO 0.006 STOPS. THE DERIVED -3.048 IS 0.586
STOPS WRONG, AND WRONG IN THE DIRECTION THAT OVER-EXPOSES.**  The defect report
that started this work had it the other way round -- it read the hardcode as
0.58 stops UNDER the derived value.  It is the derived value that is 0.58 stops
OVER, and rendering the film at -3.048 would have blown the highlights.

WHY THE CONTRACT'S DERIVATION IS WRONG, IN TWO NAMED PARTS
-----------------------------------------------------------
`REFERENCE_EXPOSURE_EXTERIOR` is log2(0.18 / mean(C.lambert_radiance(0.18))) and
that arithmetic is exact.  Its INPUTS are not the light the film is rendered in:

  * ATMOSPHERE_STOPS.  `build_sky.build()` always creates `SKY_AirColumn` and
    `SKY_AirBoundary`, a homogeneous Rayleigh + Mie slab.  Its in-scattering is
    real illumination and `C.SKY_IRRADIANCE` does not contain it.  MEASURED by
    hiding exactly those two objects and re-rendering: 28.3005 -> 39.0106 W/m2.

  * SKY_SHORTFALL_STOPS.  Even with the atmosphere gone the card still lands
    0.123 stops above the formula, because `C.SKY_IRRADIANCE` itself is low:
    the sky delivers a MEASURED 11.1818 W/m2 against the constant's 8.4593.
    That is a finding for `build_sky`, not something to absorb silently, so it
    is named and published separately rather than rolled into the airlight.

THE VALUE IS NOT MOVED TO -3.6343, AND THAT IS DELIBERATE
----------------------------------------------------------
The measurement's own resolution is about 0.04 stops (the calibration file
derives that from its leave-one-out control).  -3.628 sits 0.006 stops from the
measured value -- six times INSIDE the instrument's noise.  Moving a shipped
constant by less than you can measure is churn, and it would break the pixel
comparability of every frame already rendered at -3.628, including the three
render_setup cameras placed at bit-identical positions for exactly that reason.
So the number stays and the SELFTEST holds it to the measurement.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import world_contract as C                                        # noqa: E402

# ---------------------------------------------------------------------------
#  THE ONE EXPRESSION
# ---------------------------------------------------------------------------

#: The contract's derivation, from `C.lambert_radiance(0.18)`. Correct as
#: arithmetic; its inputs are an incomplete description of the shipped light.
CONTRACT_EXPOSURE = C.REFERENCE_EXPOSURE_EXTERIOR                 # -3.048

#: SKY_Atmosphere's in-scattering, which C.SKY_IRRADIANCE omits.
#: MEASURED: 39.0106 / 28.3005 W/m2 = +0.4630 stops.
ATMOSPHERE_STOPS = -0.463

#: C.SKY_IRRADIANCE is itself low against the sky it was measured from.
#: MEASURED: 28.3005 / 25.9851 W/m2 = +0.1231 stops. A finding for build_sky.
SKY_SHORTFALL_STOPS = -0.117

#: What the film renders at. -3.628, which is what render_setup2.py,
#: render_setup3.py and build_terrain.py each used to hardcode on their own.
FILM_EXPOSURE = round(CONTRACT_EXPOSURE + ATMOSPHERE_STOPS
                      + SKY_SHORTFALL_STOPS, 3)

#: The brief's interior-to-daylight ramp. The camera rig keys FILM_EXPOSURE
#: minus this at the interior end. Kept here so the ramp's two ends come from
#: one file as well.
#:
#: **0.0 SINCE 2026-08-03, AND IT WAS POINTING THE WRONG WAY.**
#:
#: The rig computes ``interior = daylight - INTERIOR_STOPS``, so 0.85 made the
#: interior DARKER -- and the interior was the end that was already black. Beat 1
#: was losing 1.30 % of the frame to literal 0/0/0, a continuous band along the
#: car's floor edge and sidepod undercut. The compensation was deepening the
#: defect it looked like it was there to solve.
#:
#: The real cause was never the ramp: the showroom's practicals are round 1's
#: rig, tuned on a curve its own docstring pins to "exposure 0", carried into a
#: film that grades at -3.628. ``world/showroom_lighting.py`` levels them by
#: exactly ``-FILM_EXPOSURE`` and the crush goes to 0.0000 % on every frame of
#: beats 1-2, measured on matched pairs at a flat -3.628.
#:
#: With the practicals levelled, 0.85 is not merely unnecessary -- it is
#: harmful. Measured both ways: at 0.0 the interior sits at mean 0.32-0.48 with
#: **0.0000 % pure black on every frame and the exposure never moves across all
#: 2,978 cut-free frames**; at 0.85 it is survivable (pure black <= 0.0010 %) but
#: **puts an 0.85-stop iris move on screen at the breach**.
#:
#: That last point decides it. This is ONE UNBROKEN TAKE WITH ZERO CUTS. An
#: exposure ramp across the breach is a camera visibly adjusting, with no cut to
#: hide it behind -- precisely what the brief forbids and exactly the option that
#: was rejected when this was decided. Choosing 0.85 here would reintroduce
#: through the back door the thing the relight was chosen instead of.
#:
#: If a deliberate interior/exterior ramp is ever wanted as a LOOK, it belongs in
#: the grade as an authored decision, not as a correction constant.
INTERIOR_STOPS = 0.0

#: The measurement's own resolution, from tools/exposure_calibration.py's
#: leave-one-out control. Nothing here is meaningful below this.
MEASUREMENT_RESOLUTION_STOPS = 0.05

VIEW_TRANSFORM = C.VIEW_TRANSFORM                                 # "AgX"
VIEW_LOOK = C.VIEW_LOOK                                           # "None"

MEASURED_JSON = os.path.join(os.path.dirname(_HERE), "render",
                             "exposure_cal", "expcal_measured.json")


def apply(scene):
    """Set a scene's whole grade from this file. Returns what it set."""
    scene.view_settings.view_transform = VIEW_TRANSFORM
    scene.view_settings.look = VIEW_LOOK
    scene.view_settings.exposure = FILM_EXPOSURE
    return {"view_transform": VIEW_TRANSFORM, "look": VIEW_LOOK,
            "exposure": FILM_EXPOSURE,
            "derivation": "%.3f contract %+.3f atmosphere %+.3f sky shortfall"
                          % (CONTRACT_EXPOSURE, ATMOSPHERE_STOPS,
                             SKY_SHORTFALL_STOPS)}


def selftest(path=None):
    """Hold FILM_EXPOSURE to the rendered measurement. UNPROVEN IS A FAIL.

    This is the check that could not exist while the number was hardcoded in
    three files: there was nothing to compare, so nothing ever did.
    """
    import json
    p = path or MEASURED_JSON
    bad = []
    print("FILM_EXPOSURE = %.3f  =  %.3f contract %+.3f atmosphere "
          "%+.3f sky shortfall"
          % (FILM_EXPOSURE, CONTRACT_EXPOSURE, ATMOSPHERE_STOPS,
             SKY_SHORTFALL_STOPS))
    if not os.path.exists(p):
        print("   FAIL no measurement at %s. Rebuild and re-render the "
              "calibration: blender -b --factory-startup -P "
              "tools/exposure_calibration.py -- --build, render the six "
              "CAM_EXPCAL scenes on the 5090, then "
              "tools/exposure_calibration.py --measure. UNPROVEN IS A FAIL."
              % p)
        return 1
    m = json.load(open(p))
    meas = m.get("measured_exposure")
    if meas is None:
        bad.append("the measurement file carries no `measured_exposure`")
    else:
        d = FILM_EXPOSURE - float(meas)
        print("   measured on the 5090            %+.4f" % float(meas))
        print("   FILM_EXPOSURE - measured        %+.4f stops (resolution "
              "%.2f)" % (d, MEASUREMENT_RESOLUTION_STOPS))
        if abs(d) > MEASUREMENT_RESOLUTION_STOPS:
            bad.append("FILM_EXPOSURE is %.4f stops from the measured value, "
                       "past the %.2f stops this measurement can resolve"
                       % (d, MEASUREMENT_RESOLUTION_STOPS))
    for key, const in (("atmosphere_stops", -ATMOSPHERE_STOPS),
                       ("residual_stops", -SKY_SHORTFALL_STOPS)):
        got = m.get(key)
        if got is None:
            bad.append("the measurement file carries no `%s`" % key)
            continue
        print("   %-30s %+.4f measured vs %+.4f published"
              % (key, float(got), const))
        if abs(float(got) - const) > MEASUREMENT_RESOLUTION_STOPS:
            bad.append("`%s` is %.4f measured against %.4f published"
                       % (key, float(got), const))
    # A POSITIVE CONTROL: the number this file replaced must FAIL the same test.
    if meas is not None:
        d_old = CONTRACT_EXPOSURE - float(meas)
        ok = abs(d_old) > MEASUREMENT_RESOLUTION_STOPS
        print("   POSITIVE CONTROL: the contract's own %-6.3f is %+.4f stops "
              "from the measurement -> %s"
              % (CONTRACT_EXPOSURE, d_old,
                 "REJECTED, as it must be" if ok else
                 "ACCEPTED -- THIS TEST CANNOT FAIL AND IS WORTHLESS"))
        if not ok:
            bad.append("the selftest accepts the value that is known to be "
                       "wrong; it is not testing anything")
    for b in bad:
        print("   FAIL " + b)
    print(">> STAGE RESULT: " + ("FILM_EXPOSURE_OK" if not bad
                                 else "FILM_EXPOSURE_FAIL"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(selftest())
