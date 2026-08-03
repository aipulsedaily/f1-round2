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

R2-171: THE SKY SHORTFALL, CHASED DOWN.  IT IS THE CLOUDS.
------------------------------------------------------------
The bullet above left the cause open and stated the size wrong.  Both are now
measured, and neither answer is "build_sky is delivering the wrong light".

**THE SIZE.  0.123 stops is what the shortfall COSTS THE FILM, not how far
`C.SKY_IRRADIANCE` is out.**  The sky term is out by log2(11.1818/8.4593) =
**+0.402 stops**.  It reads as 0.123 because the film's light is sun-dominated:
the sky is 8.459 of a predicted 25.985 W/m2, so an error in it is diluted 3.07x
against the total.  0.402 stops is TEN TIMES the instrument's 0.04-stop floor,
not three.  The two routes to the same excess -- 2.7225 W/m2 on the sky, 2.3154
W/m2 on the total -- agree to 0.021 stops, inside that floor.

**THE CAUSE.  `calibrate()` and `build_world()` do not build the same sky.**
`build_sky.calibrate()` bakes the constant from a throwaway `CAL_world` holding
ONE bare `ShaderNodeTexSky`.  `build_sky.build_world()` -- the world the film is
rendered in -- is that same node with an aerosol mottle and THREE alpha-
composited cloud decks over it (cirrus 0.560, altocumulus 0.535, cumulus 0.620
cover; `CUMULUS_LIT` is 20.7 against a mean blue-sky radiance of 2.69).  The
exposure calibration measured the FILM's world.  So the constant is not a wrong
measurement of the film's sky; it is an EXACT measurement of a sky the film does
not build.

MEASURED, `tools/sky_cause.py` -> `world/sky_cause.json`, on calibrate()'s own rig, E = pi*L on
an albedo-1.0 lambertian plane, no sun lamp and no atmosphere geometry in the
scene at all:

    bare Sky Texture at the contract's parameters   8.4602   +0.0001 stops
    build_sky.build_world(), untouched             11.1524   +0.3987 stops
    the same world, three deck factors forced to 0  8.4602   +0.0001 stops

The first row is the POSITIVE CONTROL and it reproduces the baked constant to
0.0001 stops, so `calibrate()` is reproducible and the constant is right about
its own subject.  The third row lands back on it exactly, so **the three cloud
decks are 100 % of the gap and the aerosol mottle is 0.000 stops of it** -- as
its own `MULTIPLY_ADD(2*0.010, 1-0.010)` construction predicts.  The world's
solar disc is gated on `Is Camera Ray` and contributes nothing.  11.1524 here
against 11.1818 from the exposure calibration -- two rigs, two instruments,
**0.0038 stops apart**.

**AND THE TINT IS OUT BY MORE THAN THE LEVEL IS.**  Per channel the decks add
**+1.076 / +0.464 / +0.054 stops**: `C.SKY_TINT` is published as
(0.3115, 0.5582, 1.0000) and the shipped sky measures (0.6323, 0.7412, 1.0000).
The film's fill light is far less blue than the contract says.  That moves
nothing in this file -- the tint is normalised out of the exposure -- but it is
the larger error, and `kerb_precast_unit`'s "anything the sun cannot reach is
blue by construction" was reasoned from the published tint.

WHY THE CONSTANT IS STILL NOT FIXED, AND WHAT IT WOULD COST
------------------------------------------------------------
Because fixing it MOVES `FILM_EXPOSURE`, and it moves it AWAY FROM ITS OWN
MEASUREMENT.  Re-baking `C.SKY_IRRADIANCE` to the shipped sky's
(8.913, 10.448, 14.096) and dropping the shortfall term to zero gives:

    C.lambert_radiance(0.18) mean   1.48883 -> 1.64314
    CONTRACT_EXPOSURE                -3.048 -> -3.190
    FILM_EXPOSURE                    -3.628 -> **-3.653**

-3.628 sits +0.0063 stops from the 5090's measured -3.6343.  The "corrected"
chain sits -0.0187 stops from it -- **three times further out**.  The present
chain is wrong twice with opposite signs (a sky 0.402 stops low, and the -0.117
plug below) and those two errors cancel to 0.006 stops.  Making the derivation
honest without re-measuring everything downstream would make the FILM's number
worse.  So this stays a named finding, and the decision is escalated rather than
taken here.

The rest of the blast radius, so it is on the record: `C.DIRECT_TO_DIFFUSE`
(2.072 published, 1.572 from the shipped sky) is asserted by the contract's own
selftest and would FAIL; `C.lambert_radiance` is the material-calibration law of
the whole film ("if a material's rendered patch is not within a few percent of
lambert_radiance, the material is wrong, not the light"); `terrain_ground.py`'s
`CALIBRATION_PASS` gate has a 16 % tolerance widened specifically to absorb this;
`build_architecture.py`'s `SKY_TEST_STRENGTH = 0.804` is a hand-derived ratio of
the constant; and `build_sky`'s own `CUMULUS_SHADE` is computed FROM
`sum(SKY_IRRADIANCE)/3`, so the decks that cause the excess are lit by the
constant that under-reports them -- **a re-bake is a fixed-point iteration, not
an assignment.**

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
#:
#: **-0.117 IS NOT THE MEASUREMENT AND NEVER WAS.**  The measurement, quoted on
#: the line above, is 0.1231.  -0.117 is the value that makes
#: round(-3.048 - 0.463 - 0.117, 3) come out at exactly -3.628, the number
#: render_setup2/3 and build_terrain each hardcoded.  It is a PLUG fitted to
#: preserve the shipped constant, and the selftest below cannot see the
#: difference because 0.1231 - 0.117 = 0.0061 is inside its 0.05 tolerance.
#: Named here because a constant whose own docstring quotes a different number
#: three lines above it is this project's most-repeated defect shape.
#: The residual is published separately so the two can never again be confused.
SKY_SHORTFALL_STOPS = -0.117

#: What the exposure calibration actually measured for the same quantity.
#: NOT used in FILM_EXPOSURE -- see SKY_SHORTFALL_STOPS. The 0.0061 stops
#: between them is the rounding that pins FILM_EXPOSURE to its shipped value.
SKY_SHORTFALL_MEASURED_STOPS = -0.1231

#: R2-171: the sky term's own error, and its measured cause. `C.SKY_IRRADIANCE`
#: describes a BARE Sky Texture (8.4602 measured, +0.0001 stops from the baked
#: constant); the film's world adds three cloud decks (11.1524, +0.3987 stops).
#: Zero the decks and it returns to 8.4602. See the docstring, and
#: `tools/sky_cause.py` for the rig, and `--gate-selftest` for its controls.
SKY_TERM_SHORTFALL_STOPS = -0.3987
SKY_SHORTFALL_CAUSE = ("build_sky.calibrate() bakes SKY_IRRADIANCE from a bare "
                       "ShaderNodeTexSky; build_sky.build_world() composites "
                       "three cloud decks over it. The decks are 100% of the "
                       "gap; the aerosol mottle is 0.000 stops of it.")

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

#: R2-171's three renders, written by `tools/sky_cause.py`. Kept in `world/`
#: rather than under `render/` because `render/*` is gitignored and this one
#: gates a published constant: an untracked input to a tracked gate goes missing
#: on the next clone and the gate then passes by default.
SKY_CAUSE_JSON = os.path.join(_HERE, "sky_cause.json")


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
    bad += sky_checks()
    for b in bad:
        print("   FAIL " + b)
    print(">> STAGE RESULT: " + ("FILM_EXPOSURE_OK" if not bad
                                 else "FILM_EXPOSURE_FAIL"))
    return 0 if not bad else 1


def sky_checks(path=None, quiet=False):
    """R2-171. HOLD THE SKY SHORTFALL TO ITS MEASURED CAUSE.

    The shortfall used to be a sentence.  A sentence cannot notice when the
    thing it describes changes, and the thing it describes is `build_sky`, which
    is under active rebuild.  This reads `world/sky_cause.json` -- written by
    `tools/sky_cause.py`, three renders on calibrate()'s own rig -- and holds
    four claims, two of which are controls:

      1  POSITIVE CONTROL.  A bare Sky Texture at the contract's parameters must
         reproduce `C.SKY_IRRADIANCE`.  If it does not, `calibrate()` is not
         reproducible and nothing below can be interpreted.
      2  THE SIZE.  build_world() - bare == SKY_TERM_SHORTFALL_STOPS.
      3  THE CAUSE.  Zero the three deck factors and it returns to bare.
      4  NEGATIVE CONTROL.  The finding must not be VACUOUS.  If build_world()
         and the bare node agreed, checks 2 and 3 would both pass on a world
         with no clouds in it and this gate would be measuring nothing.  So the
         gap is required to be REAL, and `decks_zeroed` is required to be
         non-empty -- a label rename would otherwise turn check 3's control into
         a second copy of its subject, which is a mistake this project has
         already shipped once.

    It does NOT gate `SKY_IRRADIANCE` against the film's sky.  That discrepancy
    is real, measured, and deliberately not fixed here; see the docstring.
    """
    import json
    out = []
    p = path or SKY_CAUSE_JSON
    say = (lambda *a: None) if quiet else (lambda *a: print(*a))
    if not os.path.exists(p):
        say("   FAIL no sky measurement at %s. Re-run: blender -b "
            "--factory-startup -P tools/sky_cause.py -- world/sky_cause.json. "
            "UNPROVEN IS A FAIL." % p)
        return ["no sky measurement at %s" % p]
    m = json.load(open(p))
    try:
        bare = sum(m["BARE"]) / 3.0
        ship = sum(m["SHIPPED"]) / 3.0
        nocl = sum(m["NOCLOUD"]) / 3.0
        baked = float(m["baked_mean"])
        decks = list(m.get("decks_zeroed") or [])
    except (KeyError, TypeError, ZeroDivisionError) as e:
        return ["world/sky_cause.json is not a sky measurement: %s" % e]
    import math
    st = lambda a, b: math.log2(a / b)
    R = MEASUREMENT_RESOLUTION_STOPS
    say("   SKY  bare %.4f  shipped %.4f  no-cloud %.4f  baked %.4f W/m2"
        % (bare, ship, nocl, baked))
    d = st(bare, baked)
    say("   [1] POSITIVE CONTROL bare vs baked constant   %+.4f stops" % d)
    if abs(d) > R:
        out.append("a bare Sky Texture at the contract's parameters reads "
                   "%+.4f stops from the baked C.SKY_IRRADIANCE; calibrate() "
                   "is not reproducible" % d)
    d = st(ship, bare) - (-SKY_TERM_SHORTFALL_STOPS)
    say("   [2] shipped - bare vs published %+.4f            %+.4f stops"
        % (SKY_TERM_SHORTFALL_STOPS, d))
    if abs(d) > R:
        out.append("the sky term's shortfall measures %+.4f stops against the "
                   "published %+.4f" % (-st(ship, bare), SKY_TERM_SHORTFALL_STOPS))
    d = st(nocl, bare)
    say("   [3] THE CAUSE  decks off returns to bare       %+.4f stops" % d)
    if abs(d) > R:
        out.append("zeroing the cloud decks does NOT return the sky to the "
                   "bare node (%+.4f stops); the decks are no longer the whole "
                   "cause and SKY_SHORTFALL_CAUSE is stale" % d)
    gap = st(ship, bare)
    say("   [4] NEGATIVE CONTROL  the gap is real          %+.4f stops, "
        "%d decks zeroed" % (gap, len(decks)))
    if abs(gap) <= R:
        out.append("build_world() and the bare node agree to %+.4f stops, so "
                   "checks [2] and [3] are measuring nothing" % gap)
    if not decks:
        out.append("`decks_zeroed` is empty -- the no-cloud control is a second "
                   "copy of its own subject")
    return out


def gate_selftest():
    """Prove `sky_checks` FAILS the inputs it is supposed to fail.

    A gate that has only ever been run against a passing input is a gate nobody
    has tested.  Each case below corrupts ONE claim in a copy of the real
    measurement and requires a failure; the untouched file is required to pass.
    """
    import copy, json, tempfile
    if not os.path.exists(SKY_CAUSE_JSON):
        print("   FAIL no %s to build the broken copies from" % SKY_CAUSE_JSON)
        print(">> STAGE RESULT: FILM_EXPOSURE_GATE_FAIL")
        return 1
    real = json.load(open(SKY_CAUSE_JSON))
    cases = []
    a = copy.deepcopy(real); a["BARE"] = [v * 1.5 for v in a["BARE"]]
    cases.append(("[1] a bare sky that does not reproduce the constant", a))
    b = copy.deepcopy(real); b["SHIPPED"] = [v * 1.4 for v in b["SHIPPED"]]
    cases.append(("[2] a shortfall of the wrong size", b))
    c = copy.deepcopy(real); c["NOCLOUD"] = list(c["SHIPPED"])
    cases.append(("[3] decks off that does NOT return to bare", c))
    d = copy.deepcopy(real); d["SHIPPED"] = list(d["BARE"])
    d["NOCLOUD"] = list(d["BARE"])
    cases.append(("[4] a world with no gap at all -- the vacuous case", d))
    e = copy.deepcopy(real); e["decks_zeroed"] = []
    cases.append(("[4] a no-cloud control that zeroed nothing", e))
    bad = []
    for name, doc in cases:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(doc, f)
            tmp = f.name
        got = sky_checks(tmp, quiet=True)
        os.unlink(tmp)
        print("   %-56s -> %s" % (name, "REJECTED" if got else
                                  "ACCEPTED -- THE GATE IS BLIND HERE"))
        if not got:
            bad.append("sky_checks accepts " + name)
    got = sky_checks(quiet=True)
    print("   %-56s -> %s" % ("the real measurement, untouched",
                              "accepted" if not got else "REJECTED: %s" % got))
    if got:
        bad.append("sky_checks rejects the real measurement: %s" % got)
    for b_ in bad:
        print("   FAIL " + b_)
    print(">> STAGE RESULT: " + ("FILM_EXPOSURE_GATE_OK" if not bad
                                 else "FILM_EXPOSURE_GATE_FAIL"))
    return 0 if not bad else 1


if __name__ == "__main__":
    if "--gate-selftest" in sys.argv:
        sys.exit(gate_selftest())
    sys.exit(selftest())
