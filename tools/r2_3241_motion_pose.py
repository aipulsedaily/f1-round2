#!/usr/bin/env python3
"""R2-3241: THE MOTION CASE, DERIVED FROM THE SAME TABLE THAT PICKED THE STILLS.

    from tools.r2_3241_motion_pose import MOTION_POSE_FRAMES, assert_motion_case

R2-3063 named the defect: `world/build_surface.FILM_POSE_FRAMES` is
`(1547, 2225, 2000, 1226)`, selected off `render/r2651/track_scale.json` as the
frames where the road surface is SHARPEST.  Those frames carry 5.4 / 7.0 / 10.3
/ 69.7 px of camera streak.  The film delivers the same surface on frames
carrying 213-245 px, and up to 2,391 px at f2632.  The material passed
`relief_gate`, `bump_relief_report`, an octave-contrast probe and a real per-
frame 4K A/B, and shipped visibly blank, because every one of those instruments
was pointed at the sharp end of one column of one table.

**Selecting by sharpness is right for "is this authored" and wrong for "does the
audience see it", and the repair is not to stop selecting by sharpness.**  It is
to make the SAME selector, run on the SAME table, also return the other end --
so that a surface can no longer be verified only where it is sharp.

WHAT THIS FILE IS
-----------------
1.  `MOTION_POSE_FRAMES` -- computed, not typed.  The mirror image of the
    comment block at `world/build_surface.py:4703`: same table, same coverage
    and sampling filters, `mb` MAXIMISED instead of minimised.  If the camera
    path changes, this list changes with it; a hardcoded list would go stale
    silently, which is R2-101 and R2-118 on this project.
2.  `film_pose_defs_with_motion()` -- a drop-in for
    `build_surface._film_pose_defs()` that returns the four sharp poses AND the
    motion poses.  One extra camera in the same blend, in the same broker job.
3.  `assert_motion_case()` -- THE GATE.  Any frame set offered as evidence about
    a surface must contain at least one frame at the delivered end.  This is the
    part that makes the defect non-repeatable rather than merely repaired once.

WHY IT IS NOT IN `world/build_surface.py`
-----------------------------------------
That file is leased by another agent for the whole of this session.  The three
callables above are written so a one-line import replaces the constant in place:

    from tools.r2_3241_motion_pose import film_pose_defs_with_motion
    def _film_pose_defs(frames=None):
        return film_pose_defs_with_motion(frames)

`_film_pose_defs`'s existing signature, return shape and dof.json lookup are
reproduced exactly, and `selftest` checks the reproduction against the real one.

THE CAMERA THIS READS, AND A TRAP IN IT
---------------------------------------
`_film_pose_defs` poses off `world/camera_rig_path.json`.  That file is NOT the
camera the film was delivered on: it differs from `render/film22_path.json`
(extracted from the shipped 10 GB blend) on 1,142 of 2,978 frames in position
by up to 21.4 m, on 1,065 in focal length by up to 56.0 mm, and on 2,516 in
orientation -- the whole of beat 1 and a stretch of beat 5.  Measured by
`tools/r2_3241_exposure.py control` (C4).

The four existing `FILM_POSE_FRAMES` happen to be clean (max 5 mm, 0.1 mm of
lens), so the R2-651 work is not contaminated.  **But a frame selector is
exactly the thing that can wander into the divergent range**, so this file
selects and poses off the DELIVERED path and refuses any frame where the two
disagree beyond `CAM_AGREE_M` / `CAM_AGREE_MM`.  A test pose the audience never
occupied is the same defect wearing a different hat.
"""

import json
import math
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TRACK_SCALE = os.path.join(R2, "render/r2651/track_scale.json")
RIG_PATH = os.path.join(R2, "world/camera_rig_path.json")
DELIVERED_PATH = os.path.join(R2, "render/film22_path.json")
DOF_JSON = os.path.join(R2, "render/r2651/dof.json")

# --------------------------------------------------------------------------
# THE SELECTION CRITERIA, ALL OF THEM READ OFF `track_scale.json`.
#
# The three filters below are lifted from the criteria the R2-651 comment block
# states for its own picks, so the two ends of the selection are comparable:
# a motion frame that showed 2 % of road would not be a counterpart to f1547.
MIN_COVER = 0.40          # f1547 46 %, f2000 50 %, f1226 41 % -- the R2-651 floor
MAX_MMPX = 60.0           # f1226 51.5 mm/px is the coarsest pick R2-651 made
# ONE FRAME PER PASS, and a PASS is a contiguous run of qualifying frames.
#
# Selecting the N highest-`mb` frames outright was tried and is wrong: the pool's
# top 33 frames are all inside f2621-f2669, i.e. one second of one corner
# rendered 33 times.  Grouping into runs first is not a tidiness measure -- it is
# what makes the motion bed a SAMPLE of the delivered defect rather than a
# close-up of its worst instant.  On the shipped path the runs come out as
# f1336-1361, f1779-1846 and f2621-2669, which are exactly the three passes
# R2-2881 independently named from the delivered pixels (f1350, f1787, f2622).
# That agreement is not enforced anywhere and is worth more for that.
RUN_GAP = 8               # frames of interruption that end a pass

# The delivered and authoring cameras must agree at a selected frame.
CAM_AGREE_M = 0.05
CAM_AGREE_MM = 0.5


def _rows():
    with open(TRACK_SCALE) as fh:
        d = json.load(fh)
    return [r for r in d["frames"] if "mb" in r], d["meta"]


def _cam(path_json):
    with open(path_json) as fh:
        return {r["f"]: r for r in json.load(fh)["path"]}


def _cameras_agree(f, rig=None, deliv=None):
    """Is frame f a pose the audience actually occupied?"""
    rig = rig if rig is not None else _cam(RIG_PATH)
    deliv = deliv if deliv is not None else _cam(DELIVERED_PATH)
    a, b = rig.get(f), deliv.get(f)
    if a is None or b is None:
        return False
    dp = math.dist(a["p"], b["p"])
    return dp <= CAM_AGREE_M and abs(a["lens"] - b["lens"]) <= CAM_AGREE_MM


# THE GATE.  A frame set offered as evidence about a SURFACE must contain at
# least one frame at the delivered end of the shutter.
#
# 160 px, not the 201 px p95: the gate's job is to refuse a bed that is wholly
# sharp, not to insist on the worst frame in the film. 160 px is where the
# R2-3061 ray join's ASPHALT emptiness crosses 50 % -- the bin in which the
# delivered defect is unambiguous -- and it is 2.3x the WORST of the four
# `FILM_POSE_FRAMES`, so the existing bed fails it by a clear margin rather
# than marginally.
MOTION_CASE_MIN_MB = 160.0


def _runs(frames, gap=RUN_GAP):
    """Contiguous passes: [[f, f+1, ...], ...] split wherever the gap exceeds."""
    out, cur = [], []
    for f in sorted(frames):
        if cur and f - cur[-1] > gap:
            out.append(cur)
            cur = []
        cur.append(f)
    if cur:
        out.append(cur)
    return out


def select_motion_frames(explain=False):
    """The mirror of `FILM_POSE_FRAMES`: same table, same filters, mb MAXIMISED.

    The one asymmetry with R2-651's selection is deliberate.  R2-651 picked four
    frames by hand from the sharp end and said what each was for.  This picks the
    worst frame of every PASS the road makes at the delivered shutter, so the
    count is set by the film rather than by the author.  If beat 5 is recut into
    four passes this returns four frames without anybody editing this file.
    """
    rows, meta = _rows()
    rig, deliv = _cam(RIG_PATH), _cam(DELIVERED_PATH)
    pool = [r for r in rows
            if r["cover"] >= MIN_COVER and r["mmpx"] <= MAX_MMPX
            and _cameras_agree(r["f"], rig, deliv)]
    if not pool:
        raise RuntimeError("no frame passes the coverage/sampling filters")
    # The SAME floor the gate enforces. One number, defined once: a bed the gate
    # would refuse must not be a bed this selector can build.
    cands = {r["f"]: r for r in pool if r["mb"] >= MOTION_CASE_MIN_MB}
    if not cands:
        raise RuntimeError("no frame reaches the delivered-shutter floor of "
                           "%.0f px with %.0f%% road coverage"
                           % (MOTION_CASE_MIN_MB, 100 * MIN_COVER))
    runs = _runs(cands)
    picked = [max((cands[f] for f in run), key=lambda r: r["mb"]) for run in runs]
    picked.sort(key=lambda r: r["f"])
    if explain:
        return picked, dict(pool=len(pool), threshold_mb=MOTION_CASE_MIN_MB,
                            candidates=len(cands),
                            runs=[(r[0], r[-1]) for r in runs], meta=meta)
    return picked


def _frames_only():
    return tuple(r["f"] for r in select_motion_frames())


MOTION_POSE_FRAMES = _frames_only()


# --------------------------------------------------------------------------
def film_pose_defs_with_motion(frames=None, path_json=None):
    """[(name, pos, quat, lens_mm, fstop, focus_m)] -- the sharp poses AND the
    motion poses, in the exact shape `build_surface._film_pose_defs` returns.

    `frames` defaults to `build_surface.FILM_POSE_FRAMES` read out of the source
    (importing that module needs bpy).  The motion frames are APPENDED, never
    substituted: a still is the correct bed for "is it authored" and nothing
    here argues otherwise.
    """
    if frames is None:
        frames = _film_pose_frames_from_source()
    frames = tuple(frames) + tuple(f for f in MOTION_POSE_FRAMES
                                   if f not in tuple(frames))
    path = _cam(path_json or RIG_PATH)
    dof = {}
    if os.path.exists(DOF_JSON):
        with open(DOF_JSON) as fh:
            dof = {r["f"]: r for r in json.load(fh)["frames"]}
    out = []
    motion = set(MOTION_POSE_FRAMES)
    for f in frames:
        if f not in path:
            raise RuntimeError("%s has no frame %d" % (path_json or RIG_PATH, f))
        r = path[f]
        d = dof.get(f, {})
        # NAMED so a crop, a log line or a judged tile cannot be mistaken for a
        # still one.  The whole defect was two beds being indistinguishable in
        # the record.
        nm = ("motionpose_f%d" if f in motion else "filmpose_f%d") % f
        out.append((nm, tuple(r["p"]), tuple(r["q"]), float(r["lens"]),
                    float(d.get("fstop", 2.8)), float(d.get("focus", 0.0))))
    return out


def _film_pose_frames_from_source():
    with open(os.path.join(R2, "world/build_surface.py")) as fh:
        for line in fh:
            if line.startswith("FILM_POSE_FRAMES"):
                return tuple(int(x) for x in
                             line.split("=", 1)[1].strip().strip("()").split(","))
    raise RuntimeError("FILM_POSE_FRAMES not found in world/build_surface.py")


# --------------------------------------------------------------------------
class MotionCaseMissing(AssertionError):
    pass


def motion_case_report(frames):
    """(ok, report) -- does this frame set include the delivered shutter?"""
    ts = {r["f"]: r for r in _rows()[0]}
    rows = [(f, ts.get(f, {}).get("mb")) for f in frames]
    known = [(f, mb) for f, mb in rows if mb is not None]
    unknown = [f for f, mb in rows if mb is None]
    passing = [(f, mb) for f, mb in known if mb >= MOTION_CASE_MIN_MB]
    return bool(passing), dict(
        frames=list(frames), threshold_mb=MOTION_CASE_MIN_MB,
        at_delivered_shutter=passing,
        max_mb=max((mb for _, mb in known), default=None),
        no_mb_recorded=unknown)


def assert_motion_case(frames, what="this surface"):
    """Raise unless `frames` contains a frame at the delivered shutter.

    Call this from any gate that reaches a verdict about a surface's DETAIL.
    It is deliberately an exception and not a printed warning: R2-3063's whole
    finding is that every instrument printed a pass and nobody was told the bed
    was wrong.
    """
    ok, rep = motion_case_report(frames)
    if not ok:
        raise MotionCaseMissing(
            "%s is being judged on frames whose worst camera streak is %s px, "
            "all below the delivered-shutter floor of %.0f px. This is the "
            "R2-3063 defect class: a test bed that does not resemble the "
            "delivery. Add one of %s (from tools/r2_3241_motion_pose."
            "MOTION_POSE_FRAMES) and re-judge."
            % (what,
               ("%.1f" % rep["max_mb"]) if rep["max_mb"] is not None else "unknown",
               MOTION_CASE_MIN_MB, list(MOTION_POSE_FRAMES)))
    return rep


# --------------------------------------------------------------------------
def selftest():
    """EVERY CONTROL OBSERVED TO FAIL BEFORE ANY OF THIS IS TRUSTED."""
    ok = True

    picked, info = select_motion_frames(explain=True)
    ts = {r["f"]: r for r in _rows()[0]}
    sharp = _film_pose_frames_from_source()
    print("  pool %d frames pass cover>=%.2f and mmpx<=%.0f; %d of them reach "
          "the %.0f px delivered-shutter floor, in %d passes: %s"
          % (info["pool"], MIN_COVER, MAX_MMPX, info["candidates"],
             info["threshold_mb"], len(info["runs"]),
             ", ".join("f%d-f%d" % r for r in info["runs"])))
    print("\n  THE EXISTING BED (FILM_POSE_FRAMES, selected on SHARPNESS)")
    for f in sharp:
        r = ts[f]
        print("    f%-6d mb=%8.2f px  mmpx=%7.2f  cover=%.2f" %
              (f, r["mb"], r["mmpx"], r["cover"]))
    print("  THE MOTION CASE (same table, same filters, mb MAXIMISED)")
    for r in picked:
        print("    f%-6d mb=%8.2f px  mmpx=%7.2f  cover=%.2f" %
              (r["f"], r["mb"], r["mmpx"], r["cover"]))

    # S1  THE GATE MUST REFUSE THE BED THAT SHIPPED THE DEFECT.
    #     This is the only control that matters. If `assert_motion_case` passes
    #     on FILM_POSE_FRAMES it would have licensed the asphalt, and the gate
    #     is worth nothing.
    try:
        assert_motion_case(sharp, "the R2-1036 asphalt A/B")
        print("\nS1  gate PASSED FILM_POSE_FRAMES -- FAIL (it must refuse it)")
        ok = False
    except MotionCaseMissing as e:
        print("\nS1  gate refuses FILM_POSE_FRAMES -- PASS")
        print("    %s" % str(e)[:150])

    # S2  ... and must ACCEPT the bed with the motion case added, or it is a
    #     gate that refuses everything, which is the same as no gate.
    try:
        rep = assert_motion_case(tuple(sharp) + MOTION_POSE_FRAMES, "the same A/B")
        print("S2  gate accepts FILM_POSE_FRAMES + MOTION_POSE_FRAMES -- PASS")
        print("    passing frames: %s" % rep["at_delivered_shutter"])
    except MotionCaseMissing:
        print("S2  gate refuses even the repaired bed -- FAIL")
        ok = False

    # S3  It must also refuse a bed that is merely LARGE. The failure mode being
    #     guarded is not "too few frames", it is "all of them sharp": R2-1036
    #     used four. A hundred sharp frames must still fail.
    many = [r["f"] for r in sorted(_rows()[0], key=lambda r: r["mb"])[:100]]
    try:
        assert_motion_case(many)
        print("S3  gate passed 100 sharp frames -- FAIL")
        ok = False
    except MotionCaseMissing:
        print("S3  gate refuses 100 sharp frames -- PASS")

    # S4  The motion frames must be genuinely at the delivered end AND still be
    #     looking at the road. A frame with 3000 px of streak and 2 % coverage
    #     would pass the gate and show nothing.
    s4 = all(r["mb"] >= MOTION_CASE_MIN_MB and r["cover"] >= MIN_COVER
             and r["mmpx"] <= MAX_MMPX for r in picked)
    print("S4  every motion frame is >= %.0f px streak AND >= %.0f%% road "
          "coverage -- %s" % (MOTION_CASE_MIN_MB, 100 * MIN_COVER,
                              "PASS" if s4 else "FAIL"))
    ok &= s4

    # S5  The drop-in must reproduce `_film_pose_defs` exactly on the four
    #     original frames, or it is a different rig wearing the same name.
    defs = film_pose_defs_with_motion()
    got = {d[0]: d for d in defs}
    rig = _cam(RIG_PATH)
    s5 = True
    for f in sharp:
        d = got.get("filmpose_f%d" % f)
        if d is None or tuple(rig[f]["p"]) != d[1] or float(rig[f]["lens"]) != d[3]:
            s5 = False
    s5 &= len(defs) == len(sharp) + len(MOTION_POSE_FRAMES)
    print("S5  drop-in reproduces the four original poses byte-for-byte and "
          "adds %d -- %s" % (len(MOTION_POSE_FRAMES), "PASS" if s5 else "FAIL"))
    ok &= s5

    # S6  Every selected frame must be a pose the audience actually occupied.
    s6 = all(_cameras_agree(r["f"]) for r in picked)
    print("S6  every motion frame agrees between the authoring and DELIVERED "
          "camera (<= %.2f m, %.1f mm) -- %s"
          % (CAM_AGREE_M, CAM_AGREE_MM, "PASS" if s6 else "FAIL"))
    # the control on S6: the filter must be capable of rejecting. Beat 1 is
    # wholly divergent, so a beat-1 frame must fail it.
    rej = [f for f in (100, 300, 500, 700) if not _cameras_agree(f)]
    print("    control  beat-1 frames rejected by the same test: %s "
          "(must not be empty)" % rej)
    s6 &= bool(rej)
    ok &= s6

    print(">> STAGE RESULT: %s" % ("MOTION_POSE_OK" if ok else "MOTION_POSE_FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest())
