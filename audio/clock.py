"""THE TWO CLOCKS, at audio sample rate.

The film is 2,978 frames at 24 fps = 124.0833 s of SCREEN time. The car's motion
lives in `telemetry/telemetry.csv`, indexed by WORLD time. Beat 3's speed ramp
consumes 8.0 s of screen time to advance 1.6 s of world time, so the two clocks
separate by exactly 6.4 s and never re-converge.

`anim/filmtime.py` is the project's one implementation of that map and is
IMPORTED here, never re-derived. What this module adds is the thing filmtime
does not provide: the map at 96 kHz instead of at 24 Hz.

WHY THAT MATTERS, AND WHY IT IS NOT JUST INTERPOLATION
------------------------------------------------------
filmtime hands back one `world_time_scale` per FRAME. Held piecewise-constant,
that scale steps by up to (1 - 0.153719) / 6 = 0.141 from one frame to the next
during the ramp's six-frame ease-in. A 14 % step in the world clock is a 14 %
step in the engine's pitch — two and a half semitones, inside 42 ms. That is a
click, and the brief explicitly forbids stepped time ("Ramps must be smooth
(eased time curves, no stepped time), and the audio must ramp with them").

So the per-frame scale is treated as a sample of a continuous function at each
frame's CENTRE and reconstructed with a shape-preserving (PCHIP) interpolant,
which is C1 and cannot overshoot into scale < 0. The reconstruction is then
corrected so that

    integral over the ramp of (1 - scale) dtau  ==  6.4000000 s   EXACTLY

because 6.4 s is not a free parameter: it is the permanent offset every other
artefact in the project has been built against. The correction is a raised-cosine
bump that is zero at both ramp edges, so scale is still exactly 1.0 outside the
ramp and the function stays C1. The bump's amplitude comes out around 0.1 %,
i.e. inaudible, and `Clock.report()` states the measured value rather than
asserting it.

WHAT IS ON WHICH CLOCK  (the single rule this whole module obeys)
-----------------------------------------------------------------
Everything attached to the WORLD is generated on the world clock and observed
through this map: engine, tyres, glass, structure, crowd. Slowing the world
therefore lowers their pitch and stretches their envelopes together, which is
what the brief asks for ("the engine and shatter smear down as time slows").

Everything attached to the CAMERA or to the AIR stays on the film clock: wind
noise at the lens, and acoustic propagation delay. Sound does not slow down
because the picture does. Justified at length in `spatial.py`.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

_ANIM = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "anim")
if _ANIM not in sys.path:
    sys.path.insert(0, _ANIM)

import filmtime as FT  # noqa: E402  (the project's one film-time implementation)


class Clock:
    """Film time <-> world time at `sr`, plus the frame grid both are checked on."""

    def __init__(self, sheet_path, sr=96000):
        with open(sheet_path) as fh:
            self.sheet = json.load(fh)
        self.fps = int(self.sheet["fps"])
        self.total_frames = int(self.sheet["total_frames"])
        self.sr = int(sr)

        # --- the project's per-frame map, untouched ---------------------------
        self.frame_scales, self.ramp_info = FT.build_time_map(self.sheet, self.total_frames, self.fps)
        self.world_of_frame = FT.world_time_table(self.frame_scales, self.total_frames, self.fps)

        self.n = self.total_frames * self.sr // self.fps
        assert self.total_frames * self.sr % self.fps == 0, "sr must divide evenly into the frame grid"
        self.film_t = np.arange(self.n, dtype=np.float64) / self.sr
        self.duration_s = self.total_frames / self.fps

        # --- reconstruct a C1 scale from the frame samples --------------------
        from scipy.interpolate import PchipInterpolator

        fs = np.asarray(self.frame_scales, dtype=np.float64)
        centres = (np.arange(self.total_frames) + 0.5) / self.fps
        # clamp the ends so the interpolant does not extrapolate away from 1.0
        cx = np.concatenate([[-1.0], centres, [self.duration_s + 1.0]])
        cy = np.concatenate([[fs[0]], fs, [fs[-1]]])
        scale = PchipInterpolator(cx, cy)(self.film_t)

        # --- force the ramp's world-time budget to be exactly right -----------
        # (1 - scale) is non-zero only inside the ramp. Its integral is the
        # permanent film/world offset, and it must be 6.4000000 s.
        deficit = 1.0 - scale
        self.ramp_span = None
        if self.ramp_info:
            r = self.ramp_info[0]
            f0, f1 = r["frames"]
            # PCHIP through frame CENTRES starts bending half a frame before the
            # ramp's first frame and finishes half a frame after its last, so the
            # correction has to be applied over the deficit's true SUPPORT, not
            # over the declared frame span. Two frames of pad each side, then
            # asserted to contain all of it.
            pad = 2 * self.sr // self.fps
            i0 = (f0 - 1) * self.sr // self.fps - pad
            i1 = f1 * self.sr // self.fps + pad
            self.ramp_span = (i0, i1)
            outside = float(np.abs(np.delete(deficit, np.arange(i0, i1))).max())
            assert outside < 1e-12, f"world-time deficit leaks outside the padded ramp: {outside}"
            target = (r["frames"][1] - r["frames"][0] + 1) / self.fps - r["declared_world_s"]
            seg = deficit[i0:i1]
            have = float(seg.sum()) / self.sr
            # raised cosine, zero at both edges -> stays C1, keeps scale==1 outside
            u = np.linspace(0.0, 1.0, seg.shape[0], endpoint=False)
            bump = 0.5 * (1.0 - np.cos(2.0 * np.pi * u))
            denom = float((bump * seg).sum()) / self.sr
            self.ramp_correction_eps = (target - have) / denom if denom != 0 else 0.0
            deficit[i0:i1] = seg * (1.0 + self.ramp_correction_eps * bump)
            self.ramp_declared_offset_s = target
            self.ramp_pchip_offset_s = have
        else:
            self.ramp_correction_eps = 0.0
            self.ramp_declared_offset_s = 0.0
            self.ramp_pchip_offset_s = 0.0

        self.scale = 1.0 - deficit                      # dw/dtau, per sample
        # world time, integrated. Trapezoid so the sum is second-order accurate.
        cum = np.concatenate([[0.0], np.cumsum(0.5 * (self.scale[1:] + self.scale[:-1]))]) / self.sr
        self.w = cum - FT.LAUNCH_FILM_T
        # world time at the exact END of the last frame (the last SAMPLE sits one
        # sample-period earlier, and the offset check is a whole-film quantity).
        self.world_at_end_of_film = float(self.w[-1] + self.scale[-1] / self.sr)
        self.launch_film_t = FT.LAUNCH_FILM_T
        self.glass_world_t = FT.GLASS_WORLD_T

        # --- the check: agree with filmtime AT THE FRAMES ---------------------
        idx = np.arange(1, self.total_frames + 1) * self.sr // self.fps - 1
        got = self.w[idx]
        want = np.asarray(self.world_of_frame[1:], dtype=np.float64)
        self.frame_agreement_max_s = float(np.abs(got - want).max())
        self.world_end_s = float(self.w[-1])

    # ------------------------------------------------------------------ maps --
    def world_at_film(self, tau):
        """World time at film time(s) tau (seconds). Vectorised."""
        return np.interp(np.asarray(tau, dtype=np.float64), self.film_t, self.w)

    def film_at_world(self, wt):
        """Film time at world time(s) wt. `w` is strictly increasing, so exact."""
        return np.interp(np.asarray(wt, dtype=np.float64), self.w, self.film_t)

    def frame_of_film(self, tau):
        return np.clip((np.asarray(tau) * self.fps).astype(int) + 1, 1, self.total_frames)

    # --------------------------------------------------------------- reports --
    def report(self):
        return {
            "sr_internal": self.sr,
            "fps": self.fps,
            "total_frames": self.total_frames,
            "duration_s": self.duration_s,
            "samples": int(self.n),
            "launch_film_t": self.launch_film_t,
            "glass_world_t": self.glass_world_t,
            "world_t_at_first_sample": float(self.w[0]),
            "world_t_at_last_sample": self.world_end_s,
            "world_t_at_end_of_film": self.world_at_end_of_film,
            "permanent_offset_s": float(self.duration_s - self.world_at_end_of_film - self.launch_film_t),
            "ramp": self.ramp_info,
            "ramp_sample_span": list(self.ramp_span) if self.ramp_span else None,
            "ramp_declared_offset_s": self.ramp_declared_offset_s,
            "ramp_pchip_offset_before_correction_s": self.ramp_pchip_offset_s,
            "ramp_correction_eps": self.ramp_correction_eps,
            "scale_min": float(self.scale.min()),
            "scale_max": float(self.scale.max()),
            "max_scale_step_per_frame_piecewise_const": float(
                np.abs(np.diff(np.asarray(self.frame_scales))).max()),
            "max_scale_step_per_sample_smoothed": float(np.abs(np.diff(self.scale)).max()),
            "agreement_with_filmtime_at_frames_max_s": self.frame_agreement_max_s,
        }


# ------------------------------------------------------------------ world grid --
class WorldGrid:
    """A uniform WORLD-time grid at the same sample rate, and the warp to film.

    All world-attached sources are synthesised on this grid and then warped once,
    with a Catmull-Rom interpolator, onto the film grid. One warp, one artefact
    budget, one thing to verify.
    """

    def __init__(self, clock: Clock, pad_s=0.5):
        self.clock = clock
        self.sr = clock.sr
        self.t0 = float(np.floor(clock.w[0] - pad_s))
        self.t1 = float(np.ceil(clock.w[-1] + pad_s))
        self.n = int(round((self.t1 - self.t0) * self.sr)) + 1
        self.t = self.t0 + np.arange(self.n, dtype=np.float64) / self.sr
        # fractional index into the world grid for every film sample
        self.warp_index = (clock.w - self.t0) * self.sr

    def to_film(self, x):
        """Warp a world-clock signal onto the film clock (Catmull-Rom)."""
        return catmull_rom(x, self.warp_index)

    def index_of_world_t(self, wt):
        return (np.asarray(wt, dtype=np.float64) - self.t0) * self.sr


def catmull_rom(x, idx):
    """Cubic Catmull-Rom resample of `x` at fractional indices `idx`.

    Linear interpolation would do here numerically, but it is a first-order
    lowpass whose corner moves with the fractional part, so a CONSTANT fractional
    delay (which is what the whole film outside the ramp is) would apply a
    constant, audible HF loss, and a slowly varying one would sweep it. Cubic
    keeps the passband flat to well past 20 kHz at a 96 kHz grid.
    """
    x = np.asarray(x)
    n = x.shape[0]
    i = np.floor(idx).astype(np.int64)
    f = (idx - i).astype(np.float64)
    i0 = np.clip(i - 1, 0, n - 1)
    i1 = np.clip(i, 0, n - 1)
    i2 = np.clip(i + 1, 0, n - 1)
    i3 = np.clip(i + 2, 0, n - 1)
    p0, p1, p2, p3 = x[i0], x[i1], x[i2], x[i3]
    f2 = f * f
    f3 = f2 * f
    out = 0.5 * ((2.0 * p1)
                 + (-p0 + p2) * f
                 + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * f2
                 + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * f3)
    return out.astype(np.float32, copy=False)
