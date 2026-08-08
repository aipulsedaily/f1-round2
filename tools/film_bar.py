#!/usr/bin/env python3
"""THE BAR, WITH EVERY LINE OF IT COUNTED.  R2-2821.

    python3 tools/film_bar.py --work work/r22101 --name film23_breach
    python3 tools/film_bar.py --work work/r22101 --name film23_breach \
                              --rig world/surface_test_filmpose.blend
    python3 tools/film_bar.py --selftest            (no Blender, no artefacts)

WHY THIS FILE EXISTS
====================
`render/world/assembly/r2/v127/verify_film23.sh` is the thing that decides
whether a film is fit to render, and it has been REPORTING CHECKS THAT NEVER
EXECUTED.  Three separate mechanisms, all the same disease:

  1. A CHECK THAT READS A KEY NOBODY EMITS.  v124, v125 and v126 all asked
     `measure_film_scene.py` for `resolution_x`, `resolution_y`, `clip_start`,
     `clip_end` and `camera`.  It emitted NONE of them.  All five fell into an
     `else: print('NOT REPORTED')` branch and were counted as NEITHER pass nor
     fail -- including the line that names the delivery format.  Silence and a
     pass were spelled the same way.

  2. A GUARD THAT CANNOT FIRE.  `tools/rig_preflight.py` needs `bpy` and was
     invoked as `python3 tools/rig_preflight.py`.  It has NEVER run.  Its only
     output on every film ever verified was:

         ModuleNotFoundError: No module named 'bpy'

  3. AN EXIT STATUS THAT GOES IN THE BIN.  `set -o pipefail` is not set in
     these scripts, so

         python3 tools/rig_preflight.py 2>&1 | tail -12
         echo "  rig_preflight exit=$?"

     reports `tail`'s status.  Measured: the tool exits 1, the bar prints
     `exit=0`, and nothing consumes either number.  Same for `slabcheck`, whose
     bar line literally reads "MUST exit 0".

THE RULE THIS FILE ENFORCES
===========================
    A CHECK THAT CANNOT BE EVALUATED MUST NEVER BE INDISTINGUISHABLE FROM ONE
    THAT PASSED.

So there are three verdicts here, not two.  `UNMEASURABLE` is what a missing
key, a missing log or a stage that never ran produces, it is printed in the
column where OK would go, and IT COUNTS AS A FAILURE.  That is `gate_exit`'s
VACUOUS distinction (R2-1121) applied to the bar itself: the gate that judges
everything else was the last one still spelling "could not measure" as 0.

TWO-VERDICT TRAP
================
Blender 5.2 exits 0 on an uncaught script exception, so `$?` is not evidence
and this file judges stages on their printed `>> STAGE RESULT:` lines.  A log
carrying TWO verdicts (R2-2108: `sys.exit` inside `try/except BaseException`
printed both `STRIP_MEASURED` and `STRIP_ABSENT` on a correct film) has an
unread verdict, so `stage()` requires EXACTLY ONE and fails on two.

CONSTANTS
=========
Exposure, the lift and the scene mark are IMPORTED from `world/film_exposure.py`
and `world/showroom_lighting.py`; the frame count is read from the beat sheet
`build_film_scene.py` itself reads.  Nothing derivable is retyped -- seven
copies of the car's bounding box were found in this codebase on 2026-08-08 and
this file is not making an eighth of anything.

The delivery raster and the clip range have NO defining module in this project
(3840 appears as a literal in nine files, `clip_end = 200000.0` in three), so
they are declared below, once, and that gap is reported rather than papered
over.
"""
import argparse
import json
import os
import re
import subprocess
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if R2 not in sys.path:
    sys.path.insert(0, R2)
sys.path.insert(0, os.path.join(R2, "tools"))

import gate_exit                                                 # noqa: E402

BLENDER = "/opt/blender-5.2.0-linux-x64/blender"   # /usr/bin/blender has no
                                                   # CUDA kernels -- do not
                                                   # substitute it.

# --------------------------------------------------------------------------
# the bar's declared numbers
# --------------------------------------------------------------------------
#: NO DEFINING MODULE EXISTS FOR THESE.  See the docstring.  If one is ever
#: written (`world/delivery.py`), delete this block and import it.
RES_X, RES_Y, RES_PCT = 3840, 2160, 100
CLIP_START, CLIP_END = 0.05, 200000.0
CAMERA_NAME = "ONER"
FPS = 24

#: film23's predicted load, from `world/showroom_strip.py --selftest`, printed
#: BEFORE the build.  Per-film, so it is an argument, not a constant.
FILM23 = dict(watts=46866.886, stamps=24,
              strip_size_y=0.10, strip_radiance=47.4569)

#: film24's OWN prediction.  R2-3361.
#:
#: `FILM23` IS FILM23'S PREDICTION AND JUDGING FILM24 BY IT WOULD BE MOVING THE
#: GOALPOSTS, even though -- as it happens -- the two agree to the last digit.
#: The point of the number is not its novelty, it is that it was computed from
#: arithmetic BEFORE the artefact existed and could not have been read off it.
#: This one was printed at 2026-08-08T18:59:12Z into
#: `work/r23361/PREDICTION_film24_20260808T185912Z.log`, which predates
#: `render/film24_breach.blend`, and the chain behind it is:
#:
#:     R2-1146 strip source 50.0 W / luma(COLD) 0.931576 = 53.6725 W
#:     levelled by 2**LIFT_STOPS = 2**3.628                = 12.363369
#:       -> 53.6725 x 12.363369                            =    663.573 W
#:     46203.313 (the pre-strip interior load) + 663.573    =  46866.886 W
#:     n_lamp_stamps 23 -> 24
#:     radiance 53.6725 / (3.60 x 0.10 x pi)               =     47.4569
#:
#: THEY AGREE BECAUSE THE PREDICTION IS A FUNCTION OF THE SHOWROOM, NOT OF THE
#: CAR, and film24 differs from film23 only in the car's keys and the camera.
#: `world/showroom_lighting.py::SHELL` is what levels a lamp, and the car
#: carries no lamp inside it -- checked on both blends rather than assumed
#: (`work/r23361/lampcheck.log`).  If a future film ever adds one, the
#: 46203.313 baseline literal inside `world/showroom_strip.py` is wrong and
#: this dict must be re-derived, not copied.
FILM24 = dict(watts=46866.886, stamps=24,
              strip_size_y=0.10, strip_radiance=47.4569)

#: Per-film predictions, selected by `--want`.  Adding a film here is how a new
#: generation declares what it expects; editing an existing entry is how the
#: record of what an OLD generation was judged against gets destroyed.
WANTS = {"film23": FILM23, "film24": FILM24}

#: The `>>` IS OPTIONAL, AND THAT IS A FINDING, NOT A CONVENIENCE.  R2-2821.
#: `gate_exit._VERDICT_RE` requires `>>`, and every verify script greps
#: `^>> STAGE RESULT`.  But `work/r2100/measure_film_extra.py` and
#: `sim/slabcheck.py` print a BARE `STAGE RESULT:` -- so their verdicts are
#: invisible to every reader in the project, including `gate_exit.scan`.  Two
#: spellings of the same convention is one spelling too many; this regex reads
#: both so a stage cannot hide behind punctuation, and the two files are named
#: in the staging note so the convention can be made single.
VERDICT_RE = r">{0,2} *STAGE RESULT: *(.+)"


def film_constants():
    """(exposure, lift_stops) from the film's own modules.  No literals."""
    from world import film_exposure as FX
    from world import showroom_lighting as SL
    return float(FX.FILM_EXPOSURE), float(SL.LIFT_STOPS)


def sheet_frames(path=None):
    """The frame count `build_film_scene.py` reads, from the file it reads it
    from.  Returns None if the sheet is absent -- which makes the frame_end
    check UNMEASURABLE rather than passing it against a remembered 2978."""
    path = path or os.path.join(R2, "docs", "beat_sheet.json")
    try:
        return int(json.load(open(path))["total_frames"])
    except Exception:                                            # noqa: BLE001
        return None


# --------------------------------------------------------------------------
# the judge
# --------------------------------------------------------------------------
MISSING = object()          # distinct from None: a key that is ABSENT is not
                            # a key whose value is null


class Bar(object):
    """Three verdicts.  OK, FAIL, and UNMEASURABLE -- and UNMEASURABLE is not
    a pass."""

    def __init__(self, out=sys.stdout):
        self.out = out
        self.rows = []                                # (name, want, got, verdict)

    # -- primitives --------------------------------------------------------
    def _row(self, name, want, got, verdict):
        self.rows.append((name, want, got, verdict))
        self.out.write("  %-34s want %-16s got %-22s %s\n"
                       % (name, want, got, verdict))
        return verdict == "OK"

    def chk(self, name, got, want, tol=0.0):
        """A value that IS present, compared."""
        if got is MISSING or got is None:
            return self._row(name, want, "<absent>", "UNMEASURABLE")
        if isinstance(want, (int, float)) and not isinstance(want, bool) \
                and isinstance(got, (int, float)) and not isinstance(got, bool):
            good = abs(float(got) - float(want)) <= tol
        else:
            good = (got == want)
        return self._row(name, want, got, "OK" if good else "FAIL")

    def require(self, name, src, key, want, tol=0.0):
        """Read `key` out of measurement `src` and judge it.

        THE WHOLE POINT: an absent key is UNMEASURABLE, which is a failure.
        This is the branch that printed 'NOT REPORTED' and moved on.
        """
        return self.chk(name, dig(src, key), want, tol)

    def stage(self, name, logpath, want_token, pattern=VERDICT_RE):
        """Judge an external stage on its PRINTED verdict, not on `$?`.

        Blender exits 0 on an uncaught exception, so a log with NO verdict line
        is UNMEASURABLE, and a log with TWO is a FAIL even if one of them says
        what you wanted (R2-2108).
        """
        if not logpath or not os.path.exists(logpath):
            return self._row(name, want_token, "<no log>", "UNMEASURABLE")
        try:
            txt = open(logpath, "rb").read().decode("utf-8", "replace")
        except Exception as exc:                                 # noqa: BLE001
            return self._row(name, want_token, "unreadable: %r" % (exc,),
                             "UNMEASURABLE")
        found = [m.group(1).strip() for m in re.finditer(pattern, txt)]
        if not found:
            return self._row(name, want_token, "<no verdict printed>",
                             "UNMEASURABLE")
        if len(found) > 1:
            return self._row(name, want_token, "%d verdicts: %s"
                             % (len(found), found), "FAIL")
        return self._row(name, want_token, found[0],
                         "OK" if found[0] == want_token else "FAIL")

    def run(self, name, cmd, want_rc=0, want_token=None, log=None,
            rc_is_ok=None):
        """Run a command AS A LIST -- no shell, therefore no pipe, therefore
        the status is the tool's own -- and judge rc AND the printed verdict.

        `cmd` never goes through `/bin/sh`.  That is not a style preference:
        every discarded verdict in this harness came from a `cmd | tail` whose
        status the shell then read as the tool's.
        """
        try:
            p = subprocess.run(cmd, cwd=R2, capture_output=True, text=True)
        except OSError as exc:
            self._row(name, "rc=%s" % want_rc, "could not exec: %r" % (exc,),
                      "UNMEASURABLE")
            return False, None
        if log:
            os.makedirs(os.path.dirname(os.path.abspath(log)), exist_ok=True)
            open(log, "w").write(p.stdout + p.stderr)
        ok = (p.returncode == want_rc) if rc_is_ok is None \
            else rc_is_ok(p.returncode)
        self._row(name + " rc", "rc=%s" % want_rc, "rc=%s" % p.returncode,
                  "OK" if ok else "FAIL")
        if want_token is not None:
            found = [m.group(1).strip() for m in
                     re.finditer(VERDICT_RE, p.stdout + p.stderr)]
            if not found:
                self._row(name + " verdict", want_token,
                          "<no verdict printed>", "UNMEASURABLE")
                ok = False
            elif len(found) > 1:
                self._row(name + " verdict", want_token,
                          "%d verdicts: %s" % (len(found), found), "FAIL")
                ok = False
            else:
                ok = self._row(name + " verdict", want_token, found[0],
                               "OK" if found[0] == want_token else "FAIL") and ok
        return ok, p

    # -- the tally ---------------------------------------------------------
    def counts(self):
        c = dict(claimed=len(self.rows), ok=0, fail=0, unmeasurable=0)
        for _, _, _, v in self.rows:
            c["ok" if v == "OK" else
              ("fail" if v == "FAIL" else "unmeasurable")] += 1
        return c

    def summary(self, tag):
        c = self.counts()
        self.out.write(
            "\n  %d checks claimed | %d OK | %d FAIL | %d UNMEASURABLE\n"
            % (c["claimed"], c["ok"], c["fail"], c["unmeasurable"]))
        if c["unmeasurable"]:
            self.out.write(
                "  UNMEASURABLE IS NOT A PASS.  These are the lines the old bar\n"
                "  printed as 'NOT REPORTED' and counted as neither:\n")
            for n, w, g, v in self.rows:
                if v == "UNMEASURABLE":
                    self.out.write("      %-32s %s\n" % (n, g))
        # gate_exit's own taxonomy: measured-and-dirty is FAIL, could-not-
        # measure is VACUOUS.  Both are non-zero; neither is a pass.
        if c["fail"]:
            return gate_exit.verdict("%s_FAIL" % tag)
        if c["unmeasurable"]:
            return gate_exit.verdict("%s_UNMEASURABLE" % tag)
        return gate_exit.verdict("%s_PASS" % tag)


def dig(src, key):
    """`extra['camera']['clip_start']` as 'camera.clip_start'; list indices as
    integers.  A missing link anywhere returns MISSING, never None -- the two
    mean different things and conflating them is how `resolution[0]` on an
    absent 'resolution' became a silent None."""
    cur = src
    for part in str(key).split("."):
        if isinstance(cur, (list, tuple)):
            try:
                cur = cur[int(part)]
                continue
            except (ValueError, IndexError):
                return MISSING
        if not isinstance(cur, dict) or part not in cur:
            return MISSING
        cur = cur[part]
    return cur


def load(path):
    """A measurement file that is absent yields {} -- and then every key in it
    reads MISSING and every check on it reads UNMEASURABLE.  That is the
    designed behaviour: a probe that did not run must fail the bar, not vanish
    from it."""
    try:
        return json.load(open(path))
    except Exception:                                            # noqa: BLE001
        return {}


# --------------------------------------------------------------------------
# the film23 bar, expressed once
# --------------------------------------------------------------------------
def judge(work, name, rig=None, want=FILM23, out=sys.stdout,
          measured=None, extra=None, strip=None, run_live=True,
          socket=False, film=None):
    exposure, lift = film_constants()
    frames = sheet_frames()
    b = Bar(out)

    m = load(os.path.join(work, "measured_%s.json" % name)) if measured is None \
        else measured
    e = load(os.path.join(work, "extra_%s.json" % name)) if extra is None else extra
    s = load(os.path.join(work, "strip_%s.json" % name)) if strip is None else strip

    out.write("=== the lamps, and the levelling identity ===\n")
    b.require("interior_lamp_watts", e, "interior_lamp_watts_measured",
              want["watts"], 1e-2)
    b.require("n_lamp_stamps", e, "n_lamp_stamps", want["stamps"])
    b.require("scene_mark", e, "scene_mark", lift, 1e-9)
    b.require("assert_levelled", e, "assert_levelled", "PASS")
    # R2-2821: these six were PRINTED by the old bar and judged by nobody.
    b.require("lift_multiplier", e, "lift_multiplier", 2.0 ** lift, 1e-6)
    b.require("identity_residual_w", e, "identity_residual_w", 0.0, 1e-3)
    b.require("identity_base_x_lift", e, "identity_base_x_lift",
              want["watts"], 1e-2)
    b.require("levelled_watts_from_stamps", e, "levelled_watts_from_stamps",
              want["watts"], 1e-2)
    b.require("worst_per_lamp_ratio", e, "worst_per_lamp_ratio.ratio",
              2.0 ** lift, 1e-6)
    b.require("lift_plus_exposure", e, "lift_plus_exposure", 0.0, 1e-9)

    out.write("\n=== the strip source ===\n")
    b.require("strip present", s, "present", True)
    b.require("strip narrow axis m", s, "size_y", want["strip_size_y"], 1e-4)
    b.require("strip radiance (authored)", s, "radiance_authored",
              want["strip_radiance"], 1e-3)
    b.require("strip hidden from camera", s, "visible_camera", False)

    out.write("\n=== the delivery format, the oner, the clip ===\n")
    # EVERY ONE OF THESE now reads a key `measure_film_scene.py` actually
    # emits.  Before R2-2821 the last five read keys that did not exist.
    b.require("resolution_x", m, "resolution_x", RES_X)
    b.require("resolution_y", m, "resolution_y", RES_Y)
    b.require("resolution_pct", m, "resolution_percentage", RES_PCT)
    b.require("fps", m, "fps", FPS)
    b.require("frame_start", m, "frame_start", 1)
    b.require("frame_end", m, "frame_end", frames)
    b.require("view_transform", m, "view_transform", "AgX")
    b.require("look", m, "look", "None")
    b.require("exposure", m, "exposure", exposure, 1e-6)
    b.require("camera", m, "camera", CAMERA_NAME)
    b.require("clip_start", m, "clip_start", CLIP_START, 1e-9)
    b.require("clip_end", m, "clip_end", CLIP_END, 1e-6)
    b.require("n_cameras_in_scene", m, "n_cameras_in_scene", 1)
    b.require("scale_length", m, "scale_length", 1.0, 1e-9)
    # cross-read from the other probe, off the same open blend: if the two
    # instruments disagree about the same file, one of them is wrong and the
    # bar must not pick a favourite silently.
    b.require("resolution_x (extra agrees)", e, "resolution.0", RES_X)
    b.require("camera clip_start (extra agrees)", e, "camera.clip_start",
              CLIP_START, 1e-9)
    b.require("camera object_fcurves", e, "camera.object_fcurves", 10)

    out.write("\n=== the stages that produced those numbers ===\n")
    b.stage("measure_film_scene ran", os.path.join(work, "measure_%s.log" % name),
            "MEASURE_FILM_SCENE_DONE")
    b.stage("measure_film_extra ran", os.path.join(work, "extra_%s.log" % name),
            "FILM_EXTRA_MEASURED")
    b.stage("measure_strip ran", os.path.join(work, "strip_%s.log" % name),
            "STRIP_MEASURED")
    b.stage("film materials", os.path.join(work, "materials_%s.log" % name),
            "FILM_MATERIALS_OK")

    if run_live:
        out.write("\n=== the controls that have to actually execute ===\n")
        # RIG_PREFLIGHT.  Blender, not python3.  A list, not a shell string, so
        # there is no pipe and the status is the tool's own.
        if rig:
            b.run("rig_preflight", [BLENDER, "-b", rig, "--factory-startup",
                                    "-noaudio", "-P",
                                    os.path.join(R2, "tools", "rig_preflight.py")],
                  want_rc=0, want_token="RIG_PREFLIGHT_OK",
                  log=os.path.join(work, "rig_preflight_%s.log"
                                   % os.path.basename(rig)))
        else:
            b._row("rig_preflight", "RIG_PREFLIGHT_OK", "<no --rig given>",
                   "UNMEASURABLE")
        # SLABCHECK.  Its bar line reads "MUST exit 0"; nothing has ever read
        # that status.
        b.run("slabcheck", [os.path.join(R2, ".venv", "bin", "python"),
                            os.path.join(R2, "sim", "slabcheck.py")],
              want_rc=0, log=os.path.join(work, "slabcheck.log"))

    # THE NEGATIVE CONTROL, WHICH THE BAR HAS NEVER ONCE JUDGED.
    # v127's header claims "socket audit  PASS, against film10's standing
    # 27-finding FAIL", and its body is
    #     python3 tools/socket_index_audit.py --blend "$f" 2>&1 | tail -12
    # -- printed, never read, for BOTH arms.  The film10 arm is the only thing
    # in this bar that proves the socket instrument still fires at all; if it
    # ever came back clean every PASS above it would be vacuous, and nothing
    # would have noticed.  It opens two multi-GB blends, so it is opt-in --
    # and NOT running it is UNMEASURABLE, which is not a pass.
    if socket:
        out.write("\n=== socket_index_audit, and its negative control ===\n")
        b.run("socket audit (film)",
              [sys.executable, os.path.join(R2, "tools", "socket_index_audit.py"),
               "--blend", film or os.path.join(R2, "render", "%s.blend" % name)],
              want_rc=0, log=os.path.join(work, "socket_%s.log" % name))
        b.run("socket audit (film10 must still FAIL)",
              [sys.executable, os.path.join(R2, "tools", "socket_index_audit.py"),
               "--blend", os.path.join(R2, "render", "film10.blend")],
              want_rc=1, log=os.path.join(work, "socket_film10.log"))
    else:
        b._row("socket audit (film)", "rc=0", "<not run: pass --socket>",
               "UNMEASURABLE")
        b._row("socket audit (film10 must still FAIL)", "rc=1",
               "<not run: pass --socket>", "UNMEASURABLE")

    return b


# --------------------------------------------------------------------------
def selftest():
    """EVERY REPAIRED CHECK, WATCHED FAILING.  A control that has only ever
    been seen to pass is not a control."""
    fails = []

    def t(label, cond, detail=""):
        print("  %-62s %s %s" % (label, "PASS" if cond else "FAIL", detail))
        if not cond:
            fails.append(label)

    exposure, lift = film_constants()
    frames = sheet_frames()
    dev = open(os.devnull, "w")

    good_m = dict(resolution_x=RES_X, resolution_y=RES_Y,
                  resolution_percentage=RES_PCT, fps=FPS, frame_start=1,
                  frame_end=frames, view_transform="AgX", look="None",
                  exposure=exposure, camera=CAMERA_NAME,
                  clip_start=CLIP_START, clip_end=CLIP_END,
                  n_cameras_in_scene=1, scale_length=1.0)
    good_e = dict(interior_lamp_watts_measured=FILM23["watts"],
                  n_lamp_stamps=FILM23["stamps"], scene_mark=lift,
                  assert_levelled="PASS", lift_multiplier=2.0 ** lift,
                  identity_residual_w=0.0,
                  identity_base_x_lift=FILM23["watts"],
                  levelled_watts_from_stamps=FILM23["watts"],
                  worst_per_lamp_ratio=dict(ratio=2.0 ** lift),
                  lift_plus_exposure=0.0,
                  resolution=[RES_X, RES_Y, RES_PCT],
                  camera=dict(clip_start=CLIP_START, object_fcurves=10))
    good_s = dict(present=True, size_y=FILM23["strip_size_y"],
                  radiance_authored=FILM23["strip_radiance"],
                  visible_camera=False)

    def counts(m=None, e=None, s=None):
        b = judge("/nonexistent", "x", measured=m if m is not None else dict(good_m),
                  extra=e if e is not None else dict(good_e),
                  strip=s if s is not None else dict(good_s),
                  out=dev, run_live=False)
        return b.counts(), b

    c, b = counts()
    # The rows that CANNOT be satisfied from a dict of numbers -- four external
    # stages with no logs here, and the two socket-audit arms that need a
    # multi-GB blend.  They are UNMEASURABLE, which is the designed answer:
    # a bar run that did not evaluate them has not passed them.
    n_ext = sum(1 for _, _, g, v in b.rows
                if v == "UNMEASURABLE" and str(g).startswith("<"))
    t("CLEAN: every value check passes on correct measurements",
      c["fail"] == 0 and c["unmeasurable"] == n_ext and n_ext == 6,
      "%d value checks OK, %d external rows UNMEASURABLE (no logs, no blend)"
      % (c["claimed"] - n_ext, n_ext))

    # 1. THE DEFECT ITSELF: a key that is not emitted must be UNMEASURABLE,
    #    and UNMEASURABLE must not be a pass.
    for k in ("resolution_x", "resolution_y", "clip_start", "clip_end",
              "camera"):
        m = dict(good_m)
        m.pop(k)
        c2, _ = counts(m=m)
        t("SILENT->UNMEASURABLE: dropping measured['%s'] is not a pass" % k,
          c2["unmeasurable"] == c["unmeasurable"] + 1
          and c2["ok"] == c["ok"] - 1,
          "unmeasurable %d -> %d" % (c["unmeasurable"], c2["unmeasurable"]))

    # 2. every value check can return FAIL, one at a time.
    perturb = [
        ("interior_lamp_watts", "e", "interior_lamp_watts_measured", 46000.0),
        ("n_lamp_stamps", "e", "n_lamp_stamps", 23),
        ("scene_mark", "e", "scene_mark", 3.0),
        ("assert_levelled", "e", "assert_levelled", "REFUSED: x"),
        ("lift_multiplier", "e", "lift_multiplier", 1.0),
        ("identity_residual_w", "e", "identity_residual_w", 5.0),
        ("identity_base_x_lift", "e", "identity_base_x_lift", 1.0),
        ("levelled_watts_from_stamps", "e", "levelled_watts_from_stamps", 1.0),
        ("lift_plus_exposure", "e", "lift_plus_exposure", 0.5),
        ("strip present", "s", "present", False),
        ("strip narrow axis m", "s", "size_y", 0.2),
        ("strip radiance", "s", "radiance_authored", 1.0),
        ("strip hidden", "s", "visible_camera", True),
        ("resolution_x", "m", "resolution_x", 1920),
        ("resolution_y", "m", "resolution_y", 1080),
        ("resolution_pct", "m", "resolution_percentage", 50),
        ("fps", "m", "fps", 25),
        ("frame_start", "m", "frame_start", 0),
        ("frame_end", "m", "frame_end", 1),
        ("view_transform", "m", "view_transform", "Filmic"),
        ("look", "m", "look", "High Contrast"),
        ("exposure", "m", "exposure", -3.048),
        ("camera", "m", "camera", "Camera"),
        ("clip_start", "m", "clip_start", 0.1),
        ("clip_end", "m", "clip_end", 1000.0),
        ("n_cameras_in_scene", "m", "n_cameras_in_scene", 2),
        ("scale_length", "m", "scale_length", 0.01),
    ]
    fired = 0
    for label, which, key, bad in perturb:
        m, e, s = dict(good_m), dict(good_e), dict(good_s)
        {"m": m, "e": e, "s": s}[which][key] = bad
        c2, _ = counts(m, e, s)
        good = c2["fail"] == 1
        fired += 1 if good else 0
        if not good:
            t("CAN-FAIL: %s" % label, False, "fail count %d" % c2["fail"])
    t("CAN-FAIL: every one of %d value checks returns FAIL when perturbed"
      % len(perturb), fired == len(perturb), "%d/%d" % (fired, len(perturb)))

    # nested-key perturbations, which `dig` has to reach
    e = dict(good_e); e["camera"] = dict(clip_start=0.1, object_fcurves=10)
    t("CAN-FAIL: a nested key (camera.clip_start) is reachable and fails",
      counts(e=e)[0]["fail"] == 1)
    e = dict(good_e); e["camera"] = None
    t("NESTED-ABSENT: camera=None makes its two checks UNMEASURABLE, not OK",
      counts(e=e)[0]["unmeasurable"] == c["unmeasurable"] + 2)
    e = dict(good_e); e["resolution"] = [1920, 1080, 100]
    t("CAN-FAIL: a list index (resolution.0) is reachable and fails",
      counts(e=e)[0]["fail"] == 1)

    # 3. `stage()` -- the two-verdict trap and the no-verdict trap.
    import tempfile
    d = tempfile.mkdtemp()

    def one(text):
        p = os.path.join(d, "l.log")
        open(p, "w").write(text)
        bb = Bar(dev)
        bb.stage("x", p, "STRIP_MEASURED")
        return bb.rows[0][3]

    t("STAGE: one correct verdict is OK",
      one(">> STAGE RESULT: STRIP_MEASURED\n") == "OK")
    t("STAGE: one wrong verdict is FAIL",
      one(">> STAGE RESULT: STRIP_ABSENT\n") == "FAIL")
    t("STAGE: TWO verdicts is FAIL even though one of them is right (R2-2108)",
      one(">> STAGE RESULT: STRIP_MEASURED\n"
          ">> STAGE RESULT: STRIP_ABSENT (probe raised SystemExit(0))\n")
      == "FAIL")
    t("STAGE: a log with a traceback and NO verdict is UNMEASURABLE",
      one("Traceback (most recent call last):\nModuleNotFoundError: bpy\n")
      == "UNMEASURABLE")
    bb = Bar(dev)
    bb.stage("x", os.path.join(d, "does-not-exist.log"), "ANY")
    t("STAGE: a stage that never ran at all is UNMEASURABLE, not silence",
      bb.rows[0][3] == "UNMEASURABLE")

    # 4. `run()` -- no shell, so the status is the tool's own.
    bb = Bar(dev)
    bb.run("true", [sys.executable, "-c", "raise SystemExit(0)"])
    t("RUN: a clean rc=0 is OK", bb.rows[0][3] == "OK")
    bb = Bar(dev)
    bb.run("false", [sys.executable, "-c", "raise SystemExit(1)"])
    t("RUN: rc=1 is FAIL -- not filtered through `| tail`",
      bb.rows[0][3] == "FAIL")
    bb = Bar(dev)
    bb.run("gone", ["/no/such/binary/anywhere"])
    t("RUN: a tool that cannot be executed at all is UNMEASURABLE",
      bb.rows[0][3] == "UNMEASURABLE")
    bb = Bar(dev)
    bb.run("noverdict", [sys.executable, "-c", "print('hi')"],
           want_token="SOMETHING")
    t("RUN: rc=0 with NO printed verdict is UNMEASURABLE (Blender exits 0 on "
      "an exception)",
      [r[3] for r in bb.rows] == ["OK", "UNMEASURABLE"])

    # 5. the summary must refuse when anything is unmeasurable.
    bb = Bar(dev)
    bb._row("a", 1, 1, "OK")
    t("SUMMARY: all-OK yields the PASS code", bb.summary("T") == gate_exit.PASS)
    bb = Bar(dev)
    bb._row("a", 1, 1, "OK")
    bb._row("b", 1, "<absent>", "UNMEASURABLE")
    t("SUMMARY: one UNMEASURABLE row REFUSES the bar",
      bb.summary("T") != gate_exit.PASS)

    t("CONSTANTS: exposure/lift come from the film's own modules",
      abs(exposure + 3.628) < 1e-9 and abs(lift - 3.628) < 1e-9,
      "FILM_EXPOSURE %.3f  LIFT_STOPS %.3f" % (exposure, lift))
    t("CONSTANTS: frame_end comes from the beat sheet, not a literal",
      frames == 2978, "total_frames %s" % frames)

    print("\n>> STAGE RESULT: FILM_BAR_SELFTEST_%s  (%d failed)"
          % ("FAIL" if fails else "PASS", len(fails)))
    return gate_exit.FAIL if fails else gate_exit.PASS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="work/r22101")
    ap.add_argument("--name", default="film23_breach")
    ap.add_argument("--rig", default="",
                    help="comparison rig .blend for rig_preflight")
    ap.add_argument("--socket", action="store_true",
                    help="also run socket_index_audit on the film AND on "
                         "film10, the negative control (opens two "
                         "multi-GB blends)")
    ap.add_argument("--film", default="",
                    help="the .blend, for --socket")
    ap.add_argument("--no-live", action="store_true",
                    help="judge recorded measurements only; do not execute "
                         "rig_preflight or slabcheck")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--want", default="film23", choices=sorted(WANTS),
                    help="WHICH FILM'S PREDICTION to judge against. It "
                         "defaults to film23 so no existing caller changes "
                         "meaning; a new film must name its own, because "
                         "re-using an older film's prediction is moving the "
                         "goalposts in the direction that flatters.")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    want = WANTS[a.want]
    print(">> judged against the %s prediction: %s" % (a.want, want))
    b = judge(os.path.join(R2, a.work), a.name, rig=a.rig or None,
              want=want, run_live=not a.no_live, socket=a.socket,
              film=a.film or None)
    return b.summary("FILM_BAR")


if __name__ == "__main__":
    gate_exit.guard(main)
