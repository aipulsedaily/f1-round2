"""PROPAGATION. The camera is the listener, and it is a listener with two ears.

Nothing here is a pan pot. A source is placed in the world, the two ears are
placed on the camera, and the wave is followed from one to the other:

  1. RETARDED TIME. Sound emitted at the source at film time t_e reaches an ear
     at the film time t_a that solves

         |ear(t_a) - src(t_e)|  =  c * (t_a - t_e)

     i.e. the wavefront is a sphere expanding at c from where the source was
     when it emitted, and the ear meets it wherever its own trajectory crosses
     it. Solved by fixed-point iteration; the iteration is a contraction with
     factor |v_ear| / c <= 101.9 / 342.0 = 0.30, so five passes converge to
     well under a sample.

     DOPPLER IS NOT APPLIED. There is no `f * c / (c - v_r)` anywhere in this
     file. The source signal is simply read at the emission times that the
     arrival grid demands, and every Doppler effect -- source motion, LISTENER
     motion, the asymmetry between them, the compression of a whole transient,
     the different shift at each ear -- falls out of that one resample. A
     formula would have had to be told which of those cases it was in.

  2. TWO EARS, TWO SOLVES. The ears sit at +/- 87.5 mm along the camera's local
     +X. Each gets its own retarded-time solution, so the interaural TIME
     difference is the actual difference in path length -- including the part
     that comes from the camera rolling, and including the fact that at 100 m/s
     the two ears are not sampling the same wavefront.

  3. SPHERICAL SPREADING, 1/r on pressure, referenced at 1 m and floored at 1 m
     so a camera that flies 1.68 m from the car does not produce a singularity.

  4. AIR ABSORPTION, ISO 9613-1, per octave band, per sample: 10^(-alpha(f)*r/20).
     At 8 kHz that is 10.5 dB per 100 m, which is why the car sounds like a
     different instrument at 26 m and at 500 m.

  5. HEAD SHADOW AND AN ELEVATION SHELF, per octave band, from the direction of arrival in
     CAMERA-LOCAL coordinates (Blender: -Z forward, +Y up, +X right). The head
     model is a rigid sphere approximation and the pinna model is a parametric
     elevation-dependent notch. Stated plainly: these are analytic
     approximations, NOT a measured HRTF. A measured HRTF is a downloaded data
     set and the brief forbids downloaded anything.

BEAT 3: WHY THE SOUND DOES NOT SLOW DOWN THE WAY THE PICTURE DOES
-----------------------------------------------------------------
This is the deliberate decision the brief asks for, and it is a split:

  * Everything the WORLD emits is on the world clock. The engine, the tyres,
    the glass, the structure are all synthesised in world seconds and warped
    onto film time by `clock.WorldGrid.to_film`. When world time falls to
    0.1537, they drop 30.5 semitones and stretch 6.5x together. The engine
    smears down; the shatter smears down; nothing is special-cased.

  * PROPAGATION is on the FILM clock, at the real speed of sound, because the
    air is the air the camera is flying through and the camera is flying in real
    time. The camera does not slow down at the breach -- the brief's whole
    "money moment" is that it keeps flying while the world does not -- so the
    Doppler the camera generates by its own motion is a REAL-TIME Doppler, at
    full strength, while the car's contribution is nearly frozen.

  The rejected alternative was to slow c along with the world, treating the
  slow-motion as a property of a filmed reality rather than of the events. It
  was rejected because it flattens exactly the effect the beat exists for: with
  c scaled by 0.1537 the camera's 40 m/s arc around the shard field would be
  Mach 0.76 and the arc would tear itself into a shockwave artefact. The
  chosen model instead gives a slow, sub-audio-rate world heard by a fast,
  real-time observer -- which is what the shot literally is.

  ARRIVAL OF THE IMPACT. It is not placed. The impact is emitted at world
  t = 1.92815 (the nose at the glass plane x = +15.0, `filmtime.GLASS_WORLD_T`),
  which the clock maps to a film time, and it then takes |camera - glass| / c to
  arrive. `master.py` reports the measured delay.
"""

from __future__ import annotations

import numpy as np

from . import dsp
from .clock import catmull_rom

C_AIR = float(dsp.speed_of_sound(18.0))       # 342.04 m/s at 18 C
R_REF = 1.0                                   # m, reference distance for 1/r
CTRL_HZ = 960


def _interp_rows(t_ctrl, arr_ctrl, t):
    """Linear interpolation of an (N,3) control-rate track at times `t`."""
    return np.stack([np.interp(t, t_ctrl, arr_ctrl[:, k]) for k in range(3)], axis=1)


def retarded(t_ctrl, src_ctrl, ear_ctrl, c=C_AIR, iters=6):
    """Arrival time and geometry for one ear, on the control grid.

    Returns (t_arrive, r, ear_at_arrival, src_minus_ear_unit).
    """
    t_e = t_ctrl
    src = src_ctrl
    t_a = t_e.copy()
    for _ in range(iters):
        e = _interp_rows(t_ctrl, ear_ctrl, t_a)
        r = np.linalg.norm(src - e, axis=1)
        t_a = t_e + r / c
    e = _interp_rows(t_ctrl, ear_ctrl, t_a)
    d = src - e
    r = np.linalg.norm(d, axis=1)
    return t_a, r, e, d / np.maximum(r, 1e-9)[:, None]


def _shadow_db(cos_ear, f):
    """Rigid-sphere head shadow, dB of attenuation at frequency f.

    `cos_ear` is the cosine between the ear's outward normal and the direction
    of arrival: +1 the source is straight at that ear, -1 it is on the far side.
    The shadow is frequency dependent because a head is only an obstacle once
    its diameter is comparable to a wavelength: ka = 2*pi*f*0.0875/c reaches 1
    at 620 Hz, which is where the curve starts to bite.
    """
    ka = 2.0 * np.pi * f * 0.0875 / C_AIR
    depth = 16.0 * (ka ** 2 / (1.0 + ka ** 2))          # dB at full occlusion
    return depth * np.clip(-cos_ear, 0.0, 1.0) ** 1.2


def _elevation_db(elev, f):
    """Elevation cue as a gentle high-frequency shelf, NOT as a notch.

    A real pinna puts a deep, NARROW notch between 6 and 12 kHz whose frequency
    climbs with elevation. The first version modelled exactly that -- and then
    applied it through an OCTAVE filterbank, which cannot represent a narrow
    notch and turned it into a 9 dB scoop across 6.5-11 kHz at BOTH ears, at
    every instant of the film. Measured on the master: 8.5 dB below a pink
    reference at 4 kHz and 13.6 dB at 6.3 kHz. The cue was audible only as a
    blanket over the whole mix.

    What survives at octave resolution is the robust low-order part of the same
    cue: sources above the listener are brighter, sources below are duller.
    Modelled as a +/- 3 dB shelf hinged at 3 kHz. Stated plainly: this is a
    coarse analytic approximation, not a measured HRTF, and a measured HRTF is a
    downloaded data set the brief forbids.
    """
    shelf = np.clip(np.sin(np.clip(elev, -1.2, 1.2)), -1.0, 1.0)
    tilt = 1.0 / (1.0 + (3000.0 / np.maximum(f, 1.0)) ** 2)      # 0 at LF, 1 at HF
    return -3.0 * shelf * tilt


def _torso_db(cos_front, f):
    """Shoulder/torso reflection: a shallow comb around 1-3 kHz for frontal
    sources, absent behind. Adds the front/back cue that a sphere alone lacks."""
    return -2.5 * np.clip(cos_front, 0.0, 1.0) * np.exp(-((np.log2(np.maximum(f, 1.0) / 2000.0)) / 0.7) ** 2)


class Propagator:
    """Reusable geometry for one listener (the camera) at one sample rate."""

    def __init__(self, clock, camera, sr, temp_c=18.0, rh_pct=55.0):
        self.clock = clock
        self.cam = camera
        self.sr = sr
        self.c = float(dsp.speed_of_sound(temp_c))
        self.temp_c = temp_c
        self.rh = rh_pct
        self.n = clock.n
        self.t = clock.film_t

        pad = 1.0
        self.t_ctrl = np.arange(-pad, clock.duration_s + pad, 1.0 / CTRL_HZ)
        self.earL, self.earR, self.centre, self.R = camera.ears(self.t_ctrl)
        self.ears = (self.earL, self.earR)
        self.alpha = np.array([dsp.iso9613_alpha(f, temp_c, rh_pct)
                               for f in dsp.band_centres(sr)])
        self.fc = np.array(dsp.band_centres(sr))
        self.bands = dsp.band_ranges(sr)
        # band-averaged transmission, not alpha(centre)*r -- see
        # dsp.band_absorption_table for what that shortcut cost.
        self.abs_r, self.abs_db = dsp.band_absorption_table(sr, temp_c, rh_pct)
        self.diagnostics = {}

    # ------------------------------------------------------------------ core --
    def geometry(self, src_ctrl, name=""):
        """Per-ear arrival maps and direction cosines, resampled to audio rate."""
        out = []
        for ear_i, ear in enumerate(self.ears):
            t_a, r, e_at_a, u = retarded(self.t_ctrl, src_ctrl, ear, self.c)
            mono = float(np.diff(t_a).min())
            # camera basis at the ARRIVAL time (that is when the ear hears it)
            R = np.stack([
                np.stack([np.interp(t_a, self.t_ctrl, self.R[:, a, b])
                          for b in range(3)], axis=1) for a in range(3)], axis=1)
            ex, ey, ez = R[:, :, 0], R[:, :, 1], R[:, :, 2]
            # ear outward normal: -X for the left ear, +X for the right
            n_ear = ex * (1.0 if ear_i else -1.0)
            cos_ear = np.sum(u * n_ear, axis=1)
            cos_front = np.sum(u * (-ez), axis=1)
            elev = np.arcsin(np.clip(np.sum(u * ey, axis=1), -1.0, 1.0))

            # -> audio rate. t_a is strictly increasing, so inverting it is a
            #    plain interpolation: for each uniform arrival sample, which
            #    emission time do we read?
            t_e_of_a = np.interp(self.t, t_a, self.t_ctrl)
            idx = t_e_of_a * self.sr
            r_a = np.interp(self.t, t_a, r).astype(np.float32)
            g = {
                "idx": idx,
                "r": r_a,
                "cos_ear": np.interp(self.t, t_a, cos_ear).astype(np.float32),
                "cos_front": np.interp(self.t, t_a, cos_front).astype(np.float32),
                "elev": np.interp(self.t, t_a, elev).astype(np.float32),
                "monotonic_min_dt": mono,
            }
            out.append(g)
        self.diagnostics[name or "src"] = {
            "min_range_m": float(min(g["r"].min() for g in out)),
            "max_range_m": float(max(g["r"].max() for g in out)),
            "arrival_monotonic_min_dt_s": float(min(g["monotonic_min_dt"] for g in out)),
            "max_itd_us": float(np.abs(out[0]["r"] - out[1]["r"]).max() / self.c * 1e6),
        }
        return out

    def render(self, x_film, src_ctrl, name="", gate=None, extra_db=0.0,
               directivity=None):
        """Propagate a film-clock mono source to a stereo pair at the ears.

        `gate` (audio rate, 0..1) multiplies at EMISSION, so a source can be
        faded in and out without ever producing a discontinuity at the ear.
        `directivity` (audio rate, dB) is an emission-side level, e.g. an
        exhaust that is louder behind the car than in front of it.
        """
        geo = self.geometry(src_ctrl, name)
        x = np.asarray(x_film, dtype=np.float32)
        if gate is not None:
            x = x * np.asarray(gate, dtype=np.float32)
        if directivity is not None:
            x = x * (10.0 ** (np.asarray(directivity, dtype=np.float32) / 20.0))
        out = np.zeros((self.n, 2), dtype=np.float32)
        pre = 10.0 ** (extra_db / 20.0)
        for bi, band in enumerate(dsp.split_bands(x, self.sr)):
            f = self.fc[bi]
            for ear_i, g in enumerate(geo):
                y = catmull_rom(band, g["idx"])
                db = np.interp(g["r"], self.abs_r, self.abs_db[bi]) \
                    - _shadow_db(g["cos_ear"], f) \
                    - _elevation_db(g["elev"], f) - _torso_db(g["cos_front"], f)
                gain = (pre / np.maximum(g["r"], R_REF)) * (10.0 ** (db / 20.0))
                out[:, ear_i] += (y * gain).astype(np.float32)
            del band
        return out

    # ------------------------------------------------------- helper geometry --
    def source_track(self, pos_film_ctrl):
        """A moving source's position on the control grid (N,3)."""
        return np.ascontiguousarray(pos_film_ctrl, dtype=np.float64)

    def static_source(self, p):
        return np.repeat(np.asarray(p, dtype=np.float64)[None, :],
                         self.t_ctrl.shape[0], axis=0)


def mirror_in_plane(p, plane_point, plane_normal):
    """Image source for a first-order specular reflection off a big flat wall."""
    n = np.asarray(plane_normal, dtype=np.float64)
    n = n / np.linalg.norm(n)
    d = np.sum((np.asarray(p) - np.asarray(plane_point)) * n, axis=-1)
    return np.asarray(p) - 2.0 * d[..., None] * n
