"""THE REST GATE — does the field stop moving somewhere the camera cannot see?

    python3 sim/rest_gate.py --out sim/out/rest_gate.json
    python3 sim/rest_gate.py --selftest

WHAT THIS IS FOR
================
`apply_breach.py` keys the bake in film frames and lets every curve extrapolate
CONSTANT.  Past the last key — f1165 — every body holds its pose exactly, for
the remaining 1,813 frames of a film with **zero cuts**.  Measured on the
artefact, not on the flag: 34,164 curves, all CONSTANT, and evaluating
`render/film14_breach.blend` at f1166, f1400, f2565, f2901 and f2978 gives
`max |p(f) - p(f1165)| = 0.000 m` on all 3,796 shard objects, against a positive
control that moves 42.417 m between f1000 and f1050.

So the field does not twitch and it does not drift.  It STOPS, in one frame,
and **2,275 of 3,948 bodies are still moving when it does.**

That is only not a cut because of where the camera is.  This gate measures that,
because it is currently true by luck and nothing was watching it:

    the wound is on screen        f857..895, f1026..1050
    THE LAST KEY                  f1165          <- 237 m away, 159.5 deg
                                                    off the camera's own axis,
                                                    i.e. BEHIND IT
    the wound is on screen again  f1322..1334, and after

The freeze happens 115 frames after the last clear sight of the wall and 157
frames before the next one.  Re-author beat 4's camera to hold on the showroom
a second longer and the audience watches 2,275 pieces of glass stop dead
together.

THE `mobility` PROPERTY, CARRIED FORWARD
=======================================
`build_breach_sim.null_verdict` grew a `mobility` field so that a null which
passes *because nothing can move* is visible in the verdict rather than
indistinguishable from a null that passes because nothing should move.  The same
hazard is here in its exact mirror: this gate can pass because the residual
motion is small, or it can pass because **the wound is off screen and would pass
whatever the field did**.  Those are completely different assurances and the
verdict says which one it is, in `assurance`.

WHAT IT MEASURES, IN REAL UNITS
===============================
  residual_px   the residual motion at the last key, projected through the
                REAL camera at the first frame the wound is next on screen.
                Metres per film frame x pixels per metre at that range.  A
                figure in pixels is the only one that decides anything.
  margin_frames how many frames separate the last key from the nearest frame on
                which the wound is on screen.  Zero or negative means the freeze
                is inside a shot.

CONTROLS — all four must fire or the gate refuses to report
  NEG  the camera track and the bake as they are: margin positive, and the
       residual under TOL_PX.
  POS1 move the last key into the middle of the f1026..1050 shot.  The gate must
       fail on margin.
  POS2 keep the last key where it is but give the field 60 m/s of residual.
       The gate must fail on pixels at the next sighting -- this is the arm that
       proves `assurance` is not just a label: with the wound off screen at the
       key itself, only the NEXT sighting can catch it.
  DISC the pixel arm must fire ON ITS OWN.  POS1 fails both arms and that is
       correct -- a key inside a shot is also a key a few frames from a 40 m
       sighting -- so the discriminating claim is the other one: POS2 keeps the
       real key, PASSES margin by 115 frames, and still fails on pixels.  If
       POS2 ever passes both, the pixel arm has stopped measuring anything.

WHAT THIS GATE DOES NOT DO
==========================
`on_screen()` has no occlusion term, so it over-states visibility.  That is the
safe direction here — it can only make the off-screen window it certifies
SHORTER — but it means the frames it calls visible are candidates, not
sightings.  Rendered and checked: at f2565 the wound's projected position is
squarely behind a gantry pylon.  Any claim that the wound IS seen has to come
from a frame, not from this file.
"""
import argparse
import json
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in ("sim", "anim"):
    p = os.path.join(R2, _p)
    if p not in sys.path:
        sys.path.insert(0, p)

import sagpx as SP                                                # noqa: E402
import resample as RS                                             # noqa: E402

RES_X, RES_Y = 3840.0, 2160.0
# THE TOLERANCE, AND WHY IT IS ONE PIXEL AND NOT A NUMBER THAT MADE IT PASS.
# The quantity is the SIZE OF THE STEP THAT NEVER HAPPENS: the distance a body
# would have covered in the next film frame if the bake had continued, in
# pixels, at the first frame the wound is next on screen.  Below one pixel per
# frame the raster cannot represent the difference between "still moving" and
# "stopped", so the freeze is not merely subtle, it is unrepresentable.  That is
# a statement about a 3840x2160 image, not about this field.
# Measured on the shipped bake at f1322, over 3,665 above-floor bodies in the
# raster: p50 0.008, p99 0.083, max 0.518 px, ONE body over 0.5 and NONE over
# 1.0.  The gate reports that distribution so the max is not taken on trust.
TOL_PX = 1.0
MIN_MARGIN_FRAMES = 24   # one second of screen time either side of the freeze

# the connected aperture, from sim/out/metrics_NEW.json
WOUND = np.array([[14.9665, -2.185, 0.0875], [14.9665, -0.035, 0.0875],
                  [14.9665, -0.035, 6.0875], [14.9665, -2.185, 6.0875]])


def project(pts, cam, R, fpx):
    rel = (pts - cam) @ R
    zc = -rel[:, 2]
    ok = zc > 1e-6
    u = np.full(len(pts), np.nan); v = np.full(len(pts), np.nan)
    u[ok] = 1920.0 + fpx * rel[ok, 0] / zc[ok]
    v[ok] = 1080.0 - fpx * rel[ok, 1] / zc[ok]
    return u, v, zc, ok


def on_screen(track, rect=WOUND):
    """Per frame: is the wound rectangle in front of the camera and inside the
    raster?  Occlusion is NOT modelled -- this over-states visibility, which is
    the safe direction for a gate that has to prove something is UNSEEN."""
    R = SP._rot(track["quat"])
    fpx = track["lens"] / 36.0 * RES_X
    out = np.zeros(len(track["frame"]), bool)
    for k in range(len(out)):
        u, v, _zc, ok = project(rect, track["loc"][k], R[k], fpx[k])
        if not ok.all():
            continue
        out[k] = (np.nanmax(u) >= 0 and np.nanmin(u) < RES_X
                  and np.nanmax(v) >= 0 and np.nanmin(v) < RES_Y)
    return out


def evaluate(track, vis, last_key, resid_ms, P_end, tol_px=TOL_PX,
             min_margin=MIN_MARGIN_FRAMES):
    """resid_ms: (N,) residual speed per body, m/s, at the last key."""
    frames = track["frame"]
    R = SP._rot(track["quat"])
    fpx = track["lens"] / 36.0 * RES_X
    vis_f = frames[vis]
    before = vis_f[vis_f < last_key]
    after = vis_f[vis_f > last_key]
    key_on_screen = bool(last_key in set(vis_f.tolist()))
    margin = 0 if key_on_screen else int(min(
        (last_key - before.max()) if len(before) else 10 ** 6,
        (after.min() - last_key) if len(after) else 10 ** 6))

    # the residual, in pixels, at the next frame the wound IS on screen.
    #
    # SPLIT BY THE FLOOR, AND SAY SO.  70 bodies ran off the edge of the sim's
    # finite static ground (it stops at x 46 / |y| 14) and are still in free
    # fall at the last key, one of them at 108.24 m/s and 154.6 m down.  They
    # project inside the raster and they are behind the terrain, so charging
    # the gate 11.98 px for a shard under the ground would fail it for a reason
    # no viewer can see -- and DROPPING them silently would hide R2-197 inside
    # a passing gate.  So they are measured separately and reported on their own
    # line, and the gate's verdict is the above-floor arm.
    if len(after):
        f_next = int(after.min())
        k = int(np.searchsorted(frames, f_next))
        rel = (P_end - track["loc"][k]) @ R[k]
        zc = -rel[:, 2]
        ok = zc > 1e-6
        px = np.zeros(len(P_end))
        px[ok] = (resid_ms[ok] / 24.0) * fpx[k] / zc[ok]
        u, v = np.full(len(P_end), np.nan), np.full(len(P_end), np.nan)
        u[ok] = 1920.0 + fpx[k] * rel[ok, 0] / zc[ok]
        v[ok] = 1080.0 - fpx[k] * rel[ok, 1] / zc[ok]
        inr = ok & (u >= 0) & (u < RES_X) & (v >= 0) & (v < RES_Y)
        above = inr & (P_end[:, 2] >= 0.0)
        under = inr & (P_end[:, 2] < 0.0)
        resid_px = float(px[above].max()) if above.any() else 0.0
        dist = ([round(float(q), 4) for q in
                 np.percentile(px[above], [50, 90, 99, 100])] if above.any()
                else None)
        n_over = {t: int((px[above] > t).sum()) for t in (0.1, 0.25, 0.5, 1.0)} \
            if above.any() else {}
        resid_px_under = float(px[under].max()) if under.any() else 0.0
        n_in, n_under = int(above.sum()), int(under.sum())
    else:
        f_next, resid_px, n_in = None, 0.0, 0
        resid_px_under, n_under = 0.0, 0
        dist, n_over = None, {}

    ok_margin = (not key_on_screen) and margin >= min_margin
    ok_px = resid_px <= tol_px
    return dict(
        last_key=int(last_key),
        last_sighting_before=int(before.max()) if len(before) else None,
        next_sighting_after=f_next,
        freeze_is_inside_a_shot=key_on_screen,
        margin_frames=margin, min_margin_frames=min_margin,
        bodies_still_moving_at_the_last_key=int((resid_ms / 24.0 > 1e-3).sum()),
        max_residual_ms=round(float(resid_ms.max()), 4),
        bodies_in_raster_at_next_sighting=n_in,
        residual_px_per_frame_at_next_sighting=round(resid_px, 4),
        residual_px_p50_p90_p99_max=dist,
        residual_px_bodies_over={str(k): v for k, v in n_over.items()},
        tol_px=tol_px,
        sub_floor=dict(
            bodies_in_raster_but_under_the_floor=n_under,
            residual_px_per_frame=round(resid_px_under, 4),
            counted_towards_the_verdict=False,
            why="R2-197: they left the sim's finite static ground and are in "
                "free fall.  They are behind the terrain from every camera in "
                "this take, so they cannot make a picture wrong -- but they "
                "are wrong, and this line exists so a passing gate cannot be "
                "read as their absence."),
        MARGIN_OK=bool(ok_margin), PIXELS_OK=bool(ok_px),
        PASS=bool(ok_margin and ok_px),
        # THE mobility-STYLE FIELD.  Why did this pass?
        assurance=("the residual is under tolerance AND the freeze is off "
                   "screen" if (ok_margin and ok_px and resid_px > 1e-6) else
                   "OFF SCREEN ONLY -- the wound is not visible at the freeze, "
                   "so this would pass whatever the field did.  The pixel arm "
                   "is measured at the NEXT sighting and nowhere else."
                   if ok_margin and ok_px else "FAILED"),
    )


def load_state():
    track = SP.load_track()
    film = RS.read_film(os.path.join(R2, "sim/out/breach_film.npz"))
    span = film["span"]
    frames = np.arange(int(span[0]), int(span[1]) + 1)
    L, _Q = film["expand"](frames)
    bake = np.load(os.path.join(R2, "sim/tmp/breach_full_m1.npz"))
    resid = np.linalg.norm(bake["loc"][-1] - bake["loc"][-2], axis=1) * 240.0
    return track, int(span[1]), L[-1], resid


def selftest():
    track, last_key, P_end, resid = load_state()
    vis = on_screen(track)
    res, n = [], [0]

    def check(name, cond, detail=""):
        n[0] += 1
        res.append((name, bool(cond), detail))
        print("  %-72s %s %s" % (name, "PASS" if cond else "FAIL", detail))

    neg = evaluate(track, vis, last_key, resid, P_end)
    check("-ve control: the shipped bake and the shipped camera pass",
          neg["PASS"], "margin %d frames, %.3f px"
          % (neg["margin_frames"], neg["residual_px_per_frame_at_next_sighting"]))

    # POS1: move the last key into the middle of the f1026..1050 sighting
    inside = int(track["frame"][vis][(track["frame"][vis] > 1000)
                                     & (track["frame"][vis] < 1100)].mean())
    p1 = evaluate(track, vis, inside, resid, P_end)
    check("+ve control: a last key INSIDE a shot fails on margin",
          (not p1["PASS"]) and not p1["MARGIN_OK"],
          "key f%d, inside_a_shot=%s" % (inside, p1["freeze_is_inside_a_shot"]))

    # POS2: the real key, but 60 m/s of residual
    p2 = evaluate(track, vis, last_key, np.full_like(resid, 60.0), P_end)
    check("+ve control: 60 m/s of residual fails on PIXELS at the next sighting",
          (not p2["PASS"]) and not p2["PIXELS_OK"] and p2["MARGIN_OK"],
          "%.2f px vs tol %.2f" % (p2["residual_px_per_frame_at_next_sighting"],
                                   p2["tol_px"]))

    # DISCRIMINATION.  P1 fails BOTH arms -- a key inside a shot is also a key
    # 12 frames from a 40 m sighting, so its residual is large too, and that is
    # correct rather than a defect in the control.  What has to be shown is that
    # the PIXEL arm is not merely a shadow of the margin arm: P2 keeps the real
    # key, passes margin comfortably, and still fails.  If P2 ever passes margin
    # AND pixels, the pixel arm has stopped measuring anything.
    check("discrimination: the pixel arm fires on its own, with margin passing",
          p2["MARGIN_OK"] is True and p2["PIXELS_OK"] is False
          and p1["MARGIN_OK"] is False,
          "P1 margin=%s px=%s | P2 margin=%s px=%s"
          % (p1["MARGIN_OK"], p1["PIXELS_OK"], p2["MARGIN_OK"], p2["PIXELS_OK"]))

    # the assurance field must not claim more than it measured
    check("assurance names WHY it passed, not just THAT it passed",
          "OFF SCREEN ONLY" in neg["assurance"] or "AND the freeze is off"
          in neg["assurance"], neg["assurance"][:60])

    bad = [r for r in res if not r[1]]
    print("\n%s" % ("all checks passed" if not bad
                    else "%d check(s) FAILED" % len(bad)))
    print("STAGE RESULT: %s" % ("PASS" if not bad else "FAIL"))
    return 0 if not bad else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default=os.path.join(R2, "sim/out/rest_gate.json"))
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    track, last_key, P_end, resid = load_state()
    vis = on_screen(track)
    rep = evaluate(track, vis, last_key, resid, P_end)
    rep["frames_the_wound_is_on_screen"] = int(vis.sum())
    rep["note_on_occlusion"] = (
        "on_screen() does not model occlusion, so it OVER-states visibility. "
        "A rendered check at f2565 found the wound behind the gantry pylon "
        "while this test called it visible.  For a gate that has to prove "
        "something is UNSEEN that is the safe direction; for any claim that it "
        "IS seen, open the frame.")
    with open(a.out, "w") as fh:
        json.dump(rep, fh, indent=1)
    print(json.dumps(rep, indent=1))
    print("STAGE RESULT: %s" % ("PASS" if rep["PASS"] else "FAIL"))


if __name__ == "__main__":
    main()
