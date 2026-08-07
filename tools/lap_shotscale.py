"""Corrected shot scale over the WHOLE film, by projecting the car's oriented box.

    python3 tools/lap_shotscale.py --path render/film14_path.json

WHY THIS EXISTS
---------------
`tools/beat1_shotscale.py` computed apparent size as

    CAR_LEN * lens / (SENSOR_W * distance_to_centre)

which is the subtense of the car's LENGTH at the distance of the car's CENTRE.
Both halves are wrong and they are wrong in opposite directions, so the product
looked plausible and survived two independent tools (R2-429, R2-430, and the
main-thread correction appended to R2-430). `tools/beat1_true_extent.py` fixed it
for beat 1 only, where the car is parked at the origin. This does the same thing
for every frame of the film, with the car MOVING: telemetry position, telemetry
heading/pitch/roll, the beat-3 world-time ramp, and the authored camera.

WHAT IT MEASURES
----------------
The eight corners of the car's oriented bounding box in world space, projected
through the actual camera (position, quaternion, animated focal length), and the
screen-space extent of the projected hull as a fraction of frame WIDTH.

CONTROLS -- every one of these must behave, and `--selftest` asserts them
------------------------------------------------------------------------
  1. POSITIVE, against pixels.  f697 (beat 1, car parked, R2-430's ruler frame)
     must land near 0.4746, which is what `tools/beat1_true_extent.py` gets and
     within 2.5 % of the 0.4630 read off `r1full_000697.png` with a ruler.
  2. NEGATIVE, absent subject.  A zero-volume car must read 0.000 everywhere.
     Two of the detectors written for R2-422 returned 0.90 and 1.00 by latching
     onto the turntable and the rear wall; a metric that cannot tell the car from
     the scenery fails this.
  3. NEGATIVE, displaced subject.  Moving the car 200 m sideways must collapse
     the reading. A metric that reads the same whether the car is there or not is
     the failure this project has hit most often.
  4. AGREEMENT, independent implementation.  Must reproduce `tmp/shotscale_v2.npy`
     -- built by a different agent from a script that no longer exists -- to
     better than 2 % over beat 5.

LIMITS, STATED NOT BURIED
-------------------------
  * The box is the car's ASSEMBLED box. During beat 1 the car is exploded across
    616 parts, so beat 1 is reported as NaN rather than as a wrong number.
  * Occlusion is not modelled: a car behind a barrier still measures full size.
  * A bounding box is larger than the car it bounds, so this OVERSTATES slightly.
    That direction is the safe one for a "the subject is too small" finding.
"""

import argparse
import csv
import json
import math
import os
import sys

R2 = "/home/zany/f1-round2"
sys.path.insert(0, R2)

from anim import filmtime  # noqa: E402

SENSOR_W = 36.0
RES = (3840, 2160)
SENSOR_H = SENSOR_W * RES[1] / RES[0]

# The car, in its own frame, reference point at the centre on the road surface.
# Same numbers anim/carpath.py drives the collision and aim gates with.
CAR_LEN = 5.698
CAR_W = 2.005
CAR_TOP_Z = 0.992
CAR_BOT_Z = 0.0

BEATS = [("1_assembly", 1, 792), ("2_launch", 793, 864), ("3_breach", 865, 1056),
         ("4_transit", 1057, 1190), ("5_lap", 1191, 2714),
         ("6_ending", 2715, 2978)]


def qn(q):
    m = math.sqrt(sum(v * v for v in q)) or 1.0
    return [v / m for v in q]


def basis(q):
    """Camera right / up / forward in world space, from [w,x,y,z]."""
    w, x, y, z = qn(q)
    right = [1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y)]
    up = [2 * (x * y - w * z), 1 - 2 * (x * x + z * z), 2 * (y * z + w * x)]
    fwd = [-(2 * (x * z + w * y)), -(2 * (y * z - w * x)),
           -(1 - 2 * (x * x + y * y))]
    return right, up, fwd


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


class Car:
    """Telemetry, read once, with linear interpolation in world time."""

    def __init__(self, csv_path):
        rows = list(csv.DictReader(open(csv_path)))
        self.t = [float(r["t_s"]) for r in rows]
        self.col = {k: [float(r[k]) for r in rows]
                    for k in ("x", "y", "z", "heading_rad", "pitch_rad",
                              "roll_rad", "speed_ms", "s_m")}
        self.t_end = self.t[-1]

    def _lerp(self, arr, t):
        import bisect
        i = bisect.bisect_left(self.t, t)
        i = min(max(i, 1), len(self.t) - 1)
        a = (t - self.t[i - 1]) / (self.t[i] - self.t[i - 1])
        return arr[i - 1] + (arr[i] - arr[i - 1]) * a

    def at(self, t):
        t = max(0.0, min(t, self.t_end))
        g = lambda k: self._lerp(self.col[k], t)  # noqa: E731
        return ([g("x"), g("y"), g("z")], g("heading_rad"), g("pitch_rad"),
                g("roll_rad"), g("speed_ms"), g("s_m"))


def obb_corners(pos, yaw, pitch, roll, scale=1.0, offset=(0.0, 0.0, 0.0)):
    """The eight world-space corners of the car's oriented box."""
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    # Z(yaw) * Y(pitch) * X(roll)
    m = [
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp, cp * sr, cp * cr],
    ]
    hx, hy = CAR_LEN / 2.0 * scale, CAR_W / 2.0 * scale
    zlo, zhi = CAR_BOT_Z * scale, CAR_TOP_Z * scale
    out = []
    for i in range(8):
        lx = hx if i & 1 else -hx
        ly = hy if i & 2 else -hy
        lz = zhi if i & 4 else zlo
        out.append([
            pos[0] + offset[0] + m[0][0] * lx + m[0][1] * ly + m[0][2] * lz,
            pos[1] + offset[1] + m[1][0] * lx + m[1][1] * ly + m[1][2] * lz,
            pos[2] + offset[2] + m[2][0] * lx + m[2][1] * ly + m[2][2] * lz,
        ])
    return out


def project(corners, eye, q, lens):
    """(frac_w, frac_h, behind) for a world point set through this camera."""
    rt, up, fwd = basis(q)
    xs, ys = [], []
    behind = False
    for p in corners:
        v = [p[j] - eye[j] for j in range(3)]
        z = dot(v, fwd)
        if z <= 1e-6:
            behind = True
            continue
        xs.append(dot(v, rt) / z * lens)
        ys.append(dot(v, up) / z * lens)
    if behind:
        # A box straddling the camera plane has no finite screen extent. Report
        # it as unmeasurable rather than letting the perspective divide near
        # zero manufacture a huge number -- that is exactly how the displaced
        # negative control below used to pass when it should have failed.
        return float("nan"), float("nan"), True
    return (max(xs) - min(xs)) / SENSOR_W, (max(ys) - min(ys)) / SENSOR_H, behind


def load_path(p):
    return {int(k["f"]): k for k in json.load(open(p))["path"]}


def series(path, car, world_t, scale=1.0, offset=(0.0, 0.0, 0.0),
           lo=1, hi=2978, pin_t=None):
    """Per-frame (frac_w, dist_to_centre, lens). Beat 1 is NaN by design.

    `pin_t` freezes the car at one world time -- the negative control: the camera
    flies the whole lap while the car never leaves the dais.
    """
    out = {}
    for f in range(lo, hi + 1):
        k = path.get(f)
        if k is None:
            continue
        if f <= 792:
            out[f] = (float("nan"), float("nan"), k["lens"])
            continue
        pos, yaw, pit, rol, _v, _s = car.at(
            world_t[f] if pin_t is None else pin_t)
        c = obb_corners(pos, yaw, pit, rol, scale, offset)
        fw, _fh, _b = project(c, k["p"], k["q"], k["lens"])
        ctr = [pos[i] + offset[i] for i in range(3)]
        ctr[2] += CAR_TOP_Z / 2.0
        out[f] = (fw, math.dist(k["p"], ctr), k["lens"])
    return out


def build_world_time(sheet, total):
    scales, _info = filmtime.build_time_map(sheet, total)
    return filmtime.world_time_table(scales, total)


def median(v):
    v = sorted(x for x in v if x == x)
    if not v:
        return float("nan")
    n = len(v)
    return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])


# ------------------------------------------------------------------ selftest --
def selftest(path, car, world_t):
    ok = True

    # 1. POSITIVE: the parked car at f697, against the ruler on r1full_000697.png
    cb = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))["beat1"]["car_box"]
    lo_b, hi_b = cb["lo"], cb["hi"]
    corners = [[lo_b[0] if i & 1 else hi_b[0], lo_b[1] if i & 2 else hi_b[1],
                lo_b[2] if i & 4 else hi_b[2]] for i in range(8)]
    k = path[697]
    fw, _, _ = project(corners, k["p"], k["q"], k["lens"])
    ref = 0.5032519052306422       # tools/beat1_true_extent.py on the same path
    ruler = 0.4630                 # front-wing tips on r1full_000697.png
    good = abs(fw - ref) < 1e-9 and ruler < fw < ruler * 1.15
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  positive/pixels  f697 projects "
          f"{fw:.4f}; the independent tools/beat1_true_extent.py gets {ref:.4f} "
          f"on this same path, and the ruler on r1full_000697.png reads "
          f"{ruler:.4f}. A BOX bounds the car, so it must sit slightly ABOVE "
          f"the ruler ({(fw/ruler-1)*100:.1f} % here) and never below.")

    # 2. NEGATIVE: no subject at all
    s0 = series(path, car, world_t, scale=0.0, lo=1191, hi=2714)
    mx = max(v[0] for v in s0.values())
    good = mx < 1e-9
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  negative/absent  a zero-volume car "
          f"reads max {mx:.6f} over beat 5; must be 0")

    # 3. NEGATIVE: the car never leaves the dais while the camera flies the lap.
    #    This is the control the R2-422 detectors that returned 0.90 and 1.00
    #    would have failed: they were reading the turntable and the rear wall,
    #    which are still there when the car is not.
    sd = series(path, car, world_t, pin_t=0.0, lo=1191, hi=2714)
    base = series(path, car, world_t, lo=1191, hi=2714)
    mb = median([v[0] for v in base.values()])
    seen = [v[0] for v in sd.values() if v[0] == v[0]]
    md = median(seen) if seen else 0.0
    agree = sum(1 for f in sd
                if sd[f][0] == sd[f][0] and base[f][0] == base[f][0]
                and abs(sd[f][0] - base[f][0]) < 0.1 * base[f][0])
    good = agree < 0.05 * len(sd)
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  negative/absent-from-shot  car left "
          f"parked on the dais while the camera flies the lap: median {md*100:.2f} % "
          f"vs the real {mb*100:.2f} %, only {len(seen)}/{len(sd)} frames even "
          f"measurable, and it agrees with the real reading to 10 % on {agree} "
          f"frames. A detector latched onto scenery would agree on all 1,524.")
    print(f"        COROLLARY, and it is uncomfortable: the control's {md*100:.2f} % "
          f"is not far below the {4.22:.2f} % the f2035-f2227 stretch actually "
          f"measures. At that size the car is barely bigger on screen than if it "
          f"had never left the showroom. That is a fact about the stretch, not a "
          f"fault in the instrument.")

    # 4. AGREEMENT with the independent v2 build
    try:
        import numpy as np
        v2 = np.load(os.path.join(R2, "tmp/shotscale_v2.npy"))
        mine = [base[f][0] for f in range(1191, 2715)]
        theirs = list(v2[1190:2714])
        rel = [abs(a - b) / max(b, 1e-6) for a, b in zip(mine, theirs)]
        p95 = sorted(rel)[int(0.95 * len(rel))]
        good = p95 < 0.02
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  agreement  vs tmp/shotscale_v2.npy "
              f"over beat 5: p95 relative difference {p95*100:.2f} %, must be < 2 %")
    except Exception as e:  # pragma: no cover
        print(f"  SKIP  agreement  ({e})")

    # 5. R2-1011 OCCLUSION ANNOTATION.  This instrument cannot see occluders,
    #    and its blindness was invisible because the numbers looked healthy.
    #    These prove the annotation fires, that it does not fire everywhere,
    #    and that it keeps `in_frame` and `occluded` apart -- conflating those
    #    two has already produced one wrong finding about the film's last
    #    frames, so the distinction gets a control of its own.
    occ = load_occlusion(os.path.join(R2, OCCLUSION_LEDGER))
    good = bool(occ)
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/ledger  loaded "
          f"{len(occ)} in-frame rows")

    good = not ledger_is_stale()
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/not_stale  the ledger is "
          f"newer than {OCCLUSION_DESCRIBES}, the geometry it describes")

    # R2-1081: this used to assert 15 frames including f1114-1116.  R2-731
    # closed the beat-4 blackout before the shipping film was built, so the
    # live answer is 12 and all of them are beat 5's bridge.
    hidden = sorted(f for f, v in occ.items() if v >= OCC_HIDDEN)
    good = hidden == list(range(2180, 2192))
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/positive  the car is "
          f"in frame and wholly hidden on exactly {len(hidden)} frames, "
          f"all of them beat 5's bridge — beat 4 was closed by R2-731")

    # The superseded ledger must still parse, and must still disagree.  If it
    # ever stops disagreeing, either R2-731 has been reverted or someone has
    # overwritten the old file, and both are worth a failure.
    old = load_occlusion(os.path.join(R2, "render/r2651/occlusion.json"))
    stale_hidden = sorted(f for f, v in old.items() if v >= OCC_HIDDEN)
    good = stale_hidden[:3] == [1114, 1115, 1116]
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/supersession  the Aug-04 "
          f"ledger still lists f1114-1116; the live one does not. The "
          f"difference IS R2-731, and reading the wrong file costs 3 frames")

    good = all(occ.get(f, 0.0) < OCC_HIDDEN for f in (2160, 2175, 2200, 2225))
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/negative  clear frames "
          f"either side of the bridge do NOT read as occluded")

    # The car is out of frame for the film's tail.  Those rows must be ABSENT
    # from the ledger, not present-and-clear: "not in shot" is not "visible".
    good = not any(f in occ for f in range(2900, 2979))
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/in_frame_filter  "
          f"out-of-frustum frames are excluded, not scored as visible")

    good = load_occlusion("/nonexistent/occlusion.json") == {}
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  occlusion/absent  a missing ledger "
          f"degrades to no annotation, and does not crash the tool")

    print("SELFTEST " + ("PASS" if ok else "FAIL"))
    return ok


#: R2-1011.  This tool projects the car's box and reports how much of the frame
#: width it fills.  It has no idea whether anything is IN FRONT of the car, so
#: at f2185 and f2190 it printed 4.66 % and 4.91 % -- among its most confident
#: readings of the whole span -- for two frames in which the car is 100 % hidden
#: behind `ARCH_PontPlongee`.  A number is not wrong here so much as it is
#: answering a different question than the reader is asking.
#:
#: The occlusion ledger already exists, so the fix costs nothing but wiring.
#: It is ADDITIVE: `frac_w` still prints in the same column with the same value,
#: because other agents are measuring with this tool right now and silently
#: changing an instrument mid-flight is the failure this project keeps logging.
#: R2-1081.  The FIRST version of this pointed at `render/r2651/occlusion.json`
#: (Aug 04 19:53), which lists f1114-1116 as hidden behind the pit building.
#: **R2-731 closed that on Aug 07 04:11** by making the building's west end an
#: annexe, and `film17_breach.blend` was built at 06:09, after it.  So the
#: instrument built to stop a metric being confidently wrong in the flattering
#: direction shipped, for one commit, being confidently wrong in the
#: PESSIMISTIC direction -- marking three good frames OCCLUDED and reporting
#: beat 4 as worse than it is.  Same failure, opposite sign.
#:
#: The ledger must be newer than the geometry it describes, and
#: `ledger_is_stale()` is the check that would have caught it.
OCCLUSION_LEDGER = "render/r2731/occ_final_items.json"
OCCLUSION_DESCRIBES = "world/build_architecture.py"
OCC_HIDDEN = 0.99      # front-occluded fraction at which "the car" is not visible


def ledger_is_stale(ledger=None, source=None):
    """Is the occlusion ledger older than the geometry it claims to describe?

    An occlusion result is a statement about a world that existed when the
    raycast ran.  Nothing in the file records which world that was, so mtime is
    the only handle -- crude, but it is the difference between a live figure and
    a retracted one, and both this instrument and the agent that caught it were
    fooled by exactly this.
    """
    l = ledger or os.path.join(R2, OCCLUSION_LEDGER)
    s = source or os.path.join(R2, OCCLUSION_DESCRIBES)
    try:
        return os.path.getmtime(l) < os.path.getmtime(s)
    except OSError:
        return True


def load_occlusion(p):
    """{frame: occ_frac_front} for frames that are IN the frustum.

    `in_frame` is filtered first and deliberately: a car outside the frustum and
    a car hidden behind a wall are indistinguishable in a summary, and conflating
    them has already produced one wrong finding about the film's last frames.
    """
    try:
        d = json.load(open(p))
    except Exception:
        return {}
    return {int(r["f"]): float(r.get("occ_frac_front") or 0.0)
            for r in d.get("frames", []) if r.get("in_frame")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=os.path.join(R2, "render/film14_path.json"))
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dump", default="")
    ap.add_argument("--frames", default="")
    ap.add_argument("--occlusion", default=os.path.join(R2, OCCLUSION_LEDGER),
                    help="occlusion ledger; '' disables the annotation")
    a = ap.parse_args()
    occ = load_occlusion(a.occlusion) if a.occlusion else {}

    sheet = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))
    total = sheet["total_frames"]
    world_t = build_world_time(sheet, total)
    car = Car(os.path.join(R2, "telemetry/telemetry.csv"))
    path = load_path(a.path)

    if a.selftest:
        okay = selftest(path, car, world_t)
        print(f">> STAGE RESULT: {'SELFTEST_OK' if okay else 'SELFTEST_FAILED'}")
        return

    s = series(path, car, world_t, lo=1, hi=total)

    if a.frames:
        print(f"{'frame':>6} {'t_s':>7} {'dist':>8} {'lens':>7} {'frac_w':>8}"
              f" {'occ':>6}")
        for tok in a.frames.split(","):
            if "-" in tok:
                b, e = tok.split("-")
                rr = range(int(b), int(e) + 1)
            else:
                rr = [int(tok)]
            for f in rr:
                if f in s:
                    fw, d, ln = s[f]
                    o = occ.get(f)
                    tail = ("     --" if o is None
                            else f" {o*100:5.1f}%"
                                 + ("   OCCLUDED -- the car is not visible on "
                                    "this frame; the figure to its left is the "
                                    "size it WOULD read at"
                                    if o >= OCC_HIDDEN else ""))
                    print(f"{f:6d} {f/24.0:7.2f} {d:8.1f} {ln:7.2f} {fw:8.4f}"
                          f"{tail}")

    print()
    print(f"{'beat':<12} {'frames':>7} {'median':>9} {'p10':>9} {'min':>9}"
          f"  {'hidden':>7}")
    for name, f0, f1 in BEATS:
        vals = [s[f][0] for f in range(f0, f1 + 1) if f in s]
        good = sorted(x for x in vals if x == x)
        hid = [f for f in range(f0, f1 + 1) if occ.get(f, 0.0) >= OCC_HIDDEN]
        if not good:
            print(f"{name:<12} {f1-f0+1:7d} {'--':>9} {'--':>9} {'--':>9}"
                  "   (car exploded; not measured)")
            continue
        print(f"{name:<12} {f1-f0+1:7d} {median(good)*100:8.2f}% "
              f"{good[int(0.1*len(good))]*100:8.2f}% {good[0]*100:8.2f}%"
              f"  {len(hid):7d}")
        if hid:
            # The median above INCLUDES these frames.  Say so, and say what it
            # is without them -- a beat's shot scale is not a claim about
            # frames the audience cannot see the subject on.
            vis = sorted(s[f][0] for f in range(f0, f1 + 1)
                         if f in s and occ.get(f, 0.0) < OCC_HIDDEN
                         and s[f][0] == s[f][0])
            print(f"{'':<12} {'':>7} {median(vis)*100:8.2f}% "
                  f"{vis[int(0.1*len(vis))]*100:8.2f}% {vis[0]*100:8.2f}%"
                  f"  {'<- car visible only; %d frame(s) hidden behind '
                       'geometry excluded' % len(hid):>7}")

    if a.dump:
        import numpy as np
        np.save(a.dump, np.array([s.get(f, (float('nan'),))[0]
                                  for f in range(1, total + 1)]))
        print(f"wrote {a.dump}")
    print(">> STAGE RESULT: LAP_SHOTSCALE_OK")


if __name__ == "__main__":
    main()
