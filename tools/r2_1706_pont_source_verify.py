#!/usr/bin/env python3
"""r2_1706_pont_source_verify.py — THE BEAT-5 BRIDGE THREAD, VERIFIED FROM SOURCE.

    .venv/bin/python tools/r2_1706_pont_source_verify.py

R2-1706.  `tools/author_beats2_5.py` carries the bridge thread as `pont_offset()`,
so `docs/beat_sheet.json` regenerates with it and no candidate file has to be
merged.  This re-measures that claim rather than restating it:

  * the source offset is bit-identical to the one R2-1004 measured, and its
    support is EXACTLY f2131-2224 -- zero, not nearly zero, outside it, which is
    what makes both beat-5 boundaries identical without asserting it;
  * `film17_path.json` + the SOURCE's own offset reproduces
    `render/film_path_R2971_PONT_B5_REBASED.json` frame for frame -- so the
    occlusion and acceleration below are measured on the thing the source emits,
    not on a file somebody staged;
  * peak |a| over R2-740's f2120-2240 window, against the shipped path's own;
  * occlusion over ALL FOUR bridge bands, with the instrument's own --selftest
    (two independent depth-tested raycasts, two stations) run first and
    unmodified, so a PASS here is not a PASS of a broken instrument.

BLENDER-FREE, AND HERE IS WHAT THAT LEAVES OPEN: it does not measure the last
hop, sheet keys -> Blender's AUTO_CLAMPED bezier -> built path.  See R2-1706 in
`docs/STAGING-R2-1701-to-R2-1760.md` for the measured 0.128 m that bounds it and
for the rig-build command that would close it.

Judge on the printed `>> STAGE RESULT:` line.  Blender 5.2 exits 0 for a script
that raised, and so does python inside a shell pipeline.
"""
import importlib.util
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "anim"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "world"))


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


AB = _load("_ab", "tools/author_beats2_5.py")           # THE SOURCE
REB = _load("_reb", "tools/r2971_pont_camera_rebase.py")  # the candidate's tool
SL = _load("_sl", "tools/r2731_pont_full_sightline.py")   # the occlusion model

ok = True


def chk(nm, cond, detail=""):
    global ok
    print("   %-56s %s   %s" % (nm, "PASS" if cond else "FAIL", detail))
    ok = ok and bool(cond)


# ---------------------------------------------------------------- 1. offset --
worst = max(max(abs(AB.pont_offset(f)[i] - REB.offset_at(f)[i]) for i in range(3))
            for f in range(2000, 2400))
chk("source pont_offset == the measured candidate's offset", worst < 1e-12,
    "worst %.3e m over f2000-2400" % worst)
nz = [f for f in range(1, 2979) if max(abs(v) for v in AB.pont_offset(f)) > 0.0]
chk("support is exactly f%d-%d and zero elsewhere" % (AB.PONT_F0, AB.PONT_F1),
    min(nz) >= AB.PONT_F0 and max(nz) <= AB.PONT_F1,
    "non-zero on f%d-%d (%d frames)" % (min(nz), max(nz), len(nz)))
chk("both beat-5 boundaries carry exactly zero offset",
    all(AB.pont_offset(f) == (0.0, 0.0, 0.0)
        for f in (1190, 1191, 2714, 2715)))

# ---------------------------------------------- 2. the paths under measurement
base = {k["f"]: k for k in json.load(
    open(os.path.join(ROOT, "render/film17_path.json")))["path"]}
cand = {k["f"]: k for k in json.load(
    open(os.path.join(ROOT, "render/film_path_R2971_PONT_B5_REBASED.json")))["path"]}
src = {f: [k["p"][i] + AB.pont_offset(f)[i] for i in range(3)]
       for f, k in base.items()}
w = max(math.dist(src[f], cand[f]["p"]) for f in base)
chk("source-derived path == the R2-1004 candidate, frame for frame", w < 1e-9,
    "worst %.3e m over all 2,978 frames" % w)

# ------------------------------------------------------------ 3. acceleration
PW = (2120, 2240)


def prof(P):
    v = [math.dist(P[f], P[f + 1]) * 24.0 for f in range(PW[0] - 4, PW[1] + 4)]
    a = [abs(v[i + 1] - v[i]) * 24.0 for i in range(len(v) - 1)]
    fa = PW[0] - 4 + 1 + max(range(len(a)), key=lambda i: a[i])
    return max(v), max(a), fa


print("\n   PEAK |a| over f%d-%d — the window R2-740 and R2-1004 both used" % PW)
for nm, P in (("shipped film17 path", {f: base[f]["p"] for f in base}),
              ("source-derived path", src)):
    v, a, fa = prof(P)
    print("     %-22s peak v %6.2f m/s   peak |a| %6.2f m/s^2 = %.2f g  at f%d"
          % (nm, v, a, a / 9.81, fa))
_, a_ship, _ = prof({f: base[f]["p"] for f in base})
_, a_src, f_src = prof(src)
chk("peak |a| is BELOW the shipped path's own", a_src < a_ship,
    "%.2f vs %.2f m/s^2" % (a_src, a_ship))
chk("peak |a| inside author_beats2_5's craft limit (95.9 m/s^2)", a_src <= 95.9,
    "%.0f %% of the budget" % (100 * a_src / 95.9))

# --------------------------------------------------------------- 4. occlusion
# The instrument reads world/camera_rig_path.json through a module global; feed
# it the path under test instead.  Its own --selftest, which reproduces two
# independent depth-tested raycasts, is run first and unmodified.
print("\n   OCCLUSION, tools/r2731_pont_full_sightline.py")
_sto, _o = sys.stdout, []


class _Cap:
    def write(self, s):
        _o.append(s)

    def flush(self):
        pass


sys.stdout = _Cap()
st = SL.selftest()
sys.stdout = _sto
chk("the instrument's own selftest (two raycasts, two stations)", st,
    "".join(_o).strip().splitlines()[-1].strip())

car = {int(e["f"]): e for e in json.load(
    open(os.path.join(ROOT, "world/car_anim_measured.json")))["frames"]}
win = list(range(2150, 2280))


def blocked(P, solid_only):
    SL._CAM = {f: dict(f=f, p=P[f]) for f in P}
    SL._CAR = car
    rows = SL.run(win, AB.PONT_S, solid_only=solid_only)
    return ([r["f"] for r in rows if r["n"] and r["blocked"] == r["n"]],
            [r["f"] for r in rows if 0 < r["blocked"] < r["n"]])


for bands, nm in ((True, "solid bands only  "),
                  (False, "ALL FOUR BANDS    ")):
    for pn, P in (("shipped", {f: base[f]["p"] for f in base}),
                  ("SOURCE ", src)):
        wh, pa = blocked(P, bands)
        print("     %s %s  wholly hidden %2d %-22s partial %d %s"
              % (nm, pn, len(wh),
                 ("(f%d-%d)" % (min(wh), max(wh))) if wh else "(none)",
                 len(pa), ("f%s" % pa) if pa else ""))
    wh, pa = blocked(src, bands)
    chk("bands=%s: SOURCE path blocks zero frames" % ("solid" if bands else "all4"),
        not wh and not pa, "%d wholly, %d partial" % (len(wh), len(pa)))

print(">> STAGE RESULT: %s" % ("R21706_PONT_SOURCE_OK" if ok
                               else "R21706_PONT_SOURCE_FAIL"))
sys.exit(0 if ok else 1)
