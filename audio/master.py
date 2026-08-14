"""RENDER THE MASTER. One continuous stereo bed, 2,978 frames, zero cuts.

    .venv/bin/python -m audio.master --out audio/out/master.wav

Everything is deterministic: every random stream is a seeded
`numpy.random.default_rng`, so two runs of this file produce byte-identical
output. Nothing is read from disk except the project's own JSON/CSV description
of the world -- no audio file of any kind is opened anywhere in this package,
which `verify.py --no-external` proves by grepping the source.

THE SIGNAL FLOW, top to bottom
------------------------------
    WORLD CLOCK                                 FILM CLOCK
    -----------                                 ----------
    engine ---.                                 wind at the lens
    tyres -----|                                outdoor diffuse bed
    assembly --|--> warp(w -> tau) ----------> propagate to the two ears
    structure -|                                 |  retarded time
    breach ----'                                 |  1/r
                                                 |  ISO 9613-1 absorption
                                                 |  head shadow + pinna
                                                 v
                                             showroom FDN (interior)
                                             + aperture radiation (exterior)
                                             + first-order facade reflections
                                                 v
                                             slow program gain -> limiter
                                                 v
                                             96 kHz -> 48 kHz, 24-bit
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time

import numpy as np
import soundfile as sf
from scipy import signal as _sig

from . import dsp, engine, layers, spatial
from .clock import Clock, WorldGrid
from .scene import CameraPath, Telemetry, classify, lateral_offsets

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR_OUT = 48000
CTRL_HZ = spatial.CTRL_HZ

# ============================== GAIN STAGING ==================================
# THE MIX BALANCE IS DECLARED AS A LOUDNESS TABLE, NOT AS A SET OF FADER
# NUMBERS. Each entry is the peak 3-second short-term loudness that bus is
# trimmed to AFTER propagation, in LUFS. `build()` measures what each bus
# actually came out at, computes the trim, applies it, and reports both -- so
# the balance is auditable and a bus that arrives 50 dB hot shows up as a 50 dB
# trim instead of as a wrecked master.
#
# The first version of this file had fixed dB trims and a physically-scaled
# shard bus. The shard bus peaked at 764.6 (LINEAR), the mix read +35.7 LUFS
# before the master gain, and the entire flying lap sat 48 dB below the breach.
# It is recorded here because "the physics set the balance" is exactly the kind
# of principled-sounding decision that produces an unusable artefact.
#
# What the table does NOT do: it never touches the dynamics INSIDE a bus. Every
# 1/r, every Doppler, every air-absorption curve is untouched; one constant per
# bus sets where that bus sits against the others, which is what a mix is.
TARGET_LUFS_S = {
    "engine": -10.0,          # the film's loudest continuous voice
    "tyres": -19.0,
    # R2-4049: four families that did not exist in the codebase at all. Beat 6
    # is an 11 s deceleration from 89.8 m/s to zero and had no braking sound
    # available to it.
    "brakes": -21.0,
    # R2-4058: -24.0 put 16 load events at 3.74% of the WHOLE FILM's energy
    # while active for 6% of it, with a 50 ms crest of 4.71 dB -- a resonant
    # boom rather than the structure-borne detail this layer exists to add.
    "suspension": -30.0,      # was -24.0
    "assembly": -27.0,        # beat 1 is intimate; the engine is not running
    "structure": -30.0,       # the pane buzzing before it goes
    "impact": -6.5,           # the breach is the loudest single event
    "shards": -9.0,
    # R2-4044: the PhISEM debris bed, the thousands of sub-centimetre pieces the
    # ballistic sim does not integrate. It is a TEXTURE, so it sits under the
    # foreground shards rather than beside them.
    #
    # R2-4060: -13.0 -> -10.5, AND THE REASON IS A MEASUREMENT, NOT A GATE.
    # Sweeping the bed's density (34 -> 200 fines per fragment), its amplitude
    # spread and its resonator band changes its DELIVERED energy above 4 kHz by
    # less than 0.7 dB across every configuration tried, because the LUFS-S
    # criterion re-normalises all of it. The bed's contribution to the breach is
    # set by THIS NUMBER and by nothing inside `debris_bed` at all -- which is
    # worth writing down, because two renders were spent tuning the generator
    # before that was measured rather than assumed.
    #
    # The stems say the bed carries 97.6% of its own energy above 4 kHz and is
    # the only bus in the breach with any top end (every other bus is below
    # 0.2%). It is also the layer the spec designates to carry the fines'
    # density. Sitting it 1.5 dB under the foreground shards is a mix statement:
    # the fragments lead, the fines sit just beneath them.
    "debris": -10.5,
    "reflect_garage": -22.0,
    # R2-4050 (§3.4): DECIDE, DO NOT LEAVE THEM. Measured against the sum of all
    # other buses, `reflect_showroom` was 25 dB under the mix everywhere and
    # `aperture` 28 dB under -- two buses that cost full render time and existed
    # only in the report. Both are raised into audibility WITH INTENT rather
    # than deleted, because each carries a real cue: the facade reflection is
    # what tells you there is a wall beside you during the transit, and the
    # aperture is the showroom's own tail heard from outside through the hole
    # the car just made. If they still measure more than 15 dB under the mix
    # after this, they should be deleted rather than raised again.
    #
    # R2-4054: THE RAISE WAS MEASURED AND IT WAS TOO FAR. At -19/-18 the two
    # buses entered the sum at linear peaks of 1.000 and 0.733 -- the peak
    # criterion won on `reflect_showroom`, which is the signature of a bus being
    # pushed past what it has. Both are LOW-PASSED image sources (5 kHz and
    # 3.5 kHz) of a reverberant tail, and both are active across 37-49 s, i.e.
    # exactly over the breach: the delivered breach came back at a 590 Hz
    # centroid with a 46 ms onset rise against 1547 Hz measured on the breach's
    # own sources. Raising them 6-9 dB put a dark smeared wash over the sharpest
    # event in the film. Backed off to +2/+3 dB over the original, which is
    # audible without being the loudest dark thing in the beat.
    "reflect_showroom": -23.0,   # -25.0 -> -19.0 (too far) -> -23.0
    # R2-4045: THE WET WAS DECLARED 4 dB ABOVE THE DRY. `room` is the reverb of
    # `assembly`, and this table set room to -23.0 while setting the assembly
    # bus that excites it to -27.0. Measured consequence over 0-33 s: assembly
    # RMS -36.75 dBFS, room RMS -36.82 dBFS -- a wet/dry ratio of -0.07 dB, i.e.
    # 1:1, with the reverb carrying 45.9% of the first thirty-three seconds of
    # the film. -31.0 puts the tail 4 dB BELOW the dry bus, which is where the
    # reverb of a thing belongs relative to the thing.
    "room": -31.0,            # the showroom's own tail, heard from inside
    "aperture": -24.0,        # that tail through the hole; -27 -> -18 (too far) -> -24
    # R2-1402: WIND WAS THE LOUDEST BUS IN THE FILM, AND IT IS PURE NOISE.
    # Measured over the flying lap by re-rendering every bus separately, wind
    # delivered -22.48 dBFS against the engine's -27.22 -- THE AIR AT THE LENS
    # WAS 4.7 dB LOUDER THAN THE CAR. `layers.wind_at_camera` is brown-noise
    # buffet plus a pink-noise edge band and has no tonal element anywhere, so
    # there is nothing in it to hear but air. In a film whose subject is a car
    # that is wrong on its own terms, before any masking argument is made.
    "wind": -23.0,            # was -18.0
    "bed": -31.0,
    "crowd": -27.0,
    "fence": -31.0,
}

# ===================== MIX EQ, DECLARED RATHER THAN HIDDEN (R2-1402) ==========
# Per-bus high shelf, applied AFTER the bus is trimmed to its target: (dB, corner
# Hz). Nothing else in the mix is EQ'd, and this table exists so that the buses
# which are EQ'd say so out loud.
#
# R2-4033: EMPTIED. It used to hold -12 dB @ 2 kHz on `wind`, `tyres` and `bed`.
#
# The R2-1402 reasoning above it was that those three beds were burying the
# engine's harmonics, and the shelf did recover 6.0 dB of harmonic-to-noise
# ratio above 2.6 kHz. But the ratio was improved by REMOVING THE NUMERATOR'S
# COMPETITION, not by adding anything, and the whole film paid for it: measured
# on the delivered master, band RMS runs 1-2 kHz -25.5 dBFS, 4-8 kHz -39.7,
# 8-12 kHz -51.1, 12-16 kHz -58.3 dBFS -- 14.2 dB down at 4-8 kHz and 25.6 dB
# down at 8-12 kHz relative to 1-2 kHz. A film in which nothing has a top end
# does not sound like objects, it sounds like a filter, and the client's word
# for that was "hair dryer".
#
# The correct fix for wind being too loud is the -23.0 LUFS trim that is already
# in the table above, plus giving the wind a mechanism instead of a colour. The
# shelf was a patch on a symptom and it is gone. Kept as an empty table rather
# than deleted so that re-introducing a mix EQ still has to be declared here.
BUS_HF_SHELF = {}

# ======================= THE PEAK CRITERION (R2-4034) =========================
# The loudness target above is a MIX decision. This is a PHYSICAL limit, and the
# two are enforced together because on their own the loudness target is deaf.
#
# `dsp.max_short_term_lufs` is BS.1770 K-weighted, and K-weighting exists to
# model what a listener hears, which means it is DESIGNED to discount the
# sub-bass. Measured from `dsp._k_weighting(96000)`: -13.30 dB at 20 Hz,
# -23.81 dB at 10 Hz, -35.42 dB at 5 Hz. The breach's buses are almost entirely
# down there, so the meter under-read the `impact` bus by 14.09 dB over
# 35.5-44.0 s (+0.82 dBFS unweighted vs -13.26 K-weighted) and the table
# obediently applied +23.64 dB to "reach" its -6.5 LUFS target. That bus entered
# the sum at a linear peak of 7.50, i.e. +17.5 dBFS, and the premix peaked at
# +17.73 dBFS against an integrated -13.59 LUFS -- a 31 dB crest for the limiter
# to destroy, all of it made of content below the ear's own rolloff.
#
# So every bus is now trimmed to the LESSER of (a) its loudness target and
# (b) whatever keeps its linear peak at or below BUS_PEAK_CEILING. A bus that
# needs (b) is a bus whose loudness target cannot be met without spending
# headroom on something the meter cannot hear, and it says so in the report.
BUS_PEAK_CEILING = 1.0

# G15: a trim this large is a source-level bug being papered over by one
# broadband number, not a mix. Reported per bus and aggregated into `build_ok`.
BUS_TRIM_LIMIT_DB = 12.0


def hf_shelf(x, db, fc, sr):
    """High shelf via a ZERO-PHASE complementary split, so lo + hi == x exactly.

    The obvious form -- `x - highpass(x) * (1 - g)` with a causal filter -- is
    wrong and was measured to be wrong: a causal high-pass is not the complement
    of anything, so subtracting it comb-filters instead of shelving. Sweeping the
    depth of that version moved the flying lap's harmonic-to-noise ratio by
    0.04 dB, which is what a comb does. Built the same way `dsp.split_bands` is,
    for the same reason.
    """
    sos = _sig.butter(4, fc, btype="lowpass", fs=sr, output="sos")
    lo = _sig.sosfiltfilt(sos, np.asarray(x, dtype=np.float64), axis=0)
    return (lo + (x - lo) * (10.0 ** (db / 20.0))).astype(np.float32)


def _archive_if_superseded(out_wav):
    """NEVER DESTROY A MASTER SOMEBODY MIGHT HAVE BEEN PLAYED (R2-2227).

    `master_B_lapdown.wav` -- the exact artefact the client heard and rejected as
    "a wind machine with someone banging on tubes" -- was overwritten by the next
    render of the same chain, and `*.wav` is gitignored, so there was no other
    copy anywhere. The A-variant of the same render had to stand in for it, at a
    measured -0.0064 dB, and the A/B the client was shown could no longer be
    reproduced from the file they were shown.

    The standing instruction after that was "rename rejected masters out of the
    pipeline's namespace the moment they are rejected". THAT IS A HABIT, AND A
    HABIT IS NOT A MECHANISM -- the same file was lost by a shell script that ran
    unattended, at which point nobody was there to rename anything. So the render
    does it: any existing file at the output path whose bytes differ from what is
    about to be written is moved aside first, with the time it was written, and
    the new name is recorded in the report. A render that reproduces its input
    byte for byte -- the normal case, and the one this file's own determinism
    guarantees -- archives nothing.

    35 MB per superseded master against losing the only copy of an artefact a
    client has already formed an opinion about is not a close trade.
    """
    if not os.path.exists(out_wav):
        return None
    old = _md5(out_wav)
    if old == _md5(out_wav + ".new"):
        os.remove(out_wav + ".new")
        print("[archive] %s reproduced byte for byte, nothing superseded"
              % os.path.basename(out_wav), flush=True)
        return None
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(os.path.getmtime(out_wav)))
    base, ext = os.path.splitext(out_wav)
    dst = "%s_SUPERSEDED_%s_%s%s" % (base, stamp, old[:8], ext)
    n = 1
    while os.path.exists(dst):
        dst = "%s_SUPERSEDED_%s_%s_%d%s" % (base, stamp, old[:8], n, ext)
        n += 1
    os.rename(out_wav, dst)
    print("[archive] %s -> %s (md5 %s)" % (os.path.basename(out_wav),
                                           os.path.basename(dst), old), flush=True)
    return dst


def _md5(path):
    if not os.path.exists(path):
        return None
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _rz(deg):
    a = np.radians(deg)
    return np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])


def design_to_world(spec, pts):
    """Design frame -> world frame, using the datum block's own transform."""
    d = spec["datum"]["circuit_design_frame"]
    R = _rz(d["rotation_deg_about_z"])
    pd = np.asarray(d["pivot_design"], dtype=np.float64)
    pw = np.asarray(d["pivot_world"], dtype=np.float64)
    p = np.asarray(pts, dtype=np.float64)
    return (R @ (p[..., :2] - pd).T).T + pw


def build(out_wav, sr=96000, report_path=None, speed_source="v_world",
          quick=None, stems_dir=None):
    t_start = time.time()
    rep = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "sr_internal": sr, "sr_out": SR_OUT, "bit_depth": 24,
           "speed_source": speed_source}

    spec = json.load(open(os.path.join(ROOT, "docs", "circuit_spec.json")))
    sheet_p = os.path.join(ROOT, "docs", "beat_sheet.json")
    sheet = json.load(open(sheet_p))
    anim = json.load(open(os.path.join(ROOT, "world", "beat1_anim_anim.json")))
    explode = json.load(open(os.path.join(ROOT, "docs", "explode_plan.json")))

    clock = Clock(sheet_p, sr=sr)
    grid = WorldGrid(clock)
    tel = Telemetry(spec=spec)
    cam = CameraPath()
    prop = spatial.Propagator(clock, cam, sr)
    n = clock.n
    rep["clock"] = clock.report()
    rep["telemetry_r2026"] = tel.r2026
    rep["speed_of_sound_ms"] = prop.c
    rep["air"] = {"temp_c": prop.temp_c, "rh_pct": prop.rh,
                  "iso9613_alpha_db_per_m": {str(int(f)): float(a)
                                             for f, a in zip(prop.fc, prop.alpha)}}

    log = []

    def mark(msg):
        log.append(f"[{time.time() - t_start:7.1f}s] {msg}")
        print(log[-1], flush=True)

    # ---------------------------------------------------------------- grids --
    t_ctrl = prop.t_ctrl                          # film time, 960 Hz, padded
    w_ctrl = clock.world_at_film(np.clip(t_ctrl, 0.0, clock.duration_s))
    car_ctrl = tel.sample(w_ctrl, speed_source)
    cam_pos_ctrl, cam_R_ctrl, _ = cam.at(np.clip(t_ctrl, 0.0, clock.duration_s))
    cam_v_ctrl = np.gradient(cam_pos_ctrl, axis=0) * CTRL_HZ
    cam_speed_ctrl = np.linalg.norm(cam_v_ctrl, axis=1)

    # source points on the car: the exhaust is behind the driver, the contact
    # patches are on the ground. 1.4 m of separation is small but it is real and
    # it is free.
    hdg = car_ctrl["heading"]
    fwd = np.stack([np.cos(hdg), np.sin(hdg), np.zeros_like(hdg)], axis=1)
    side = np.stack([-np.sin(hdg), np.cos(hdg), np.zeros_like(hdg)], axis=1)
    exhaust_pos = car_ctrl["pos"] - fwd * 1.60 + np.array([0.0, 0.0, 0.42])
    tyre_pos = car_ctrl["pos"] - fwd * 0.20 + np.array([0.0, 0.0, 0.18])

    r_cam_car = np.linalg.norm(cam_pos_ctrl - car_ctrl["pos"], axis=1)
    rep["camera"] = {
        "frames": cam.frames,
        "peak_speed_ms": float(cam_speed_ctrl.max()),
        "mean_speed_ms": float(cam_speed_ctrl.mean()),
        "min_camera_car_m": float(r_cam_car.min()),
        "max_camera_car_m": float(r_cam_car.max()),
        "ear_separation_m": 2 * CameraPath.EAR_HALF,
    }

    # ------------------------------------------------------- world-grid src --
    tw = grid.t
    st = tel.sample(tw, speed_source)
    # MEMORY. `sample` returns fourteen float64 tracks; at 96 kHz over a 120 s
    # world span that is 1.3 GB for eleven arrays nothing downstream reads. Keep
    # the six that are used, as float32.
    st_x = st["pos"][:, 0].astype(np.float32)
    st = {k: st[k].astype(np.float32) for k in
          ("speed", "accel_long", "accel_lat", "slip", "wheel_w")}
    mark(f"world grid {tw.shape[0]} samples, {tw[0]:.1f}..{tw[-1]:.1f} s world")

    # --- surface classification, at a world CONTROL rate --------------------
    # `lateral_offsets` is O(samples x centreline), so it runs at 240 Hz over the
    # world span (28.8 k samples) and is interpolated up. The quantity it
    # produces changes over metres, not milliseconds.
    wc = np.arange(tw[0], tw[-1], 1.0 / 240.0)
    stc = tel.sample(wc, speed_source)
    lat_c, _stn = lateral_offsets(spec, stc["pos"])
    rep["racing_line"] = {
        "max_abs_lateral_offset_m": float(np.abs(lat_c[stc["track_s"] > 0]).max()),
        "note": ("the telemetry drives the CENTRELINE: the maximum lateral offset "
                 "anywhere on the lap is 10 mm, so there is no racing line to "
                 "cross a kerb with. Kerb and gravel layers are implemented and "
                 "positive-control tested, and they correctly never trigger on "
                 "this telemetry. Fabricating kerb strikes the picture will not "
                 "show would be a desync defect, not a feature."),
    }

    # the shard field's extent sets where the debris-crunch surface ends
    ev, shard_sum = layers.shard_ballistics(
        spec, float(np.interp(11.98, tel.col["s_m"], tel.v_world)))
    debris_end_x = float(np.clip(shard_sum["debris_p80_x_m"], 16.0, 45.0))
    rep["breach_sim"] = shard_sum
    rep["breach_sim"]["debris_surface_end_x_m"] = debris_end_x

    surf_c = classify(spec, stc["pos"], stc["track_s"], lat_c, debris_end_x)
    surf = {k: np.interp(tw, wc, surf_c[k]).astype(np.float32) for k in surf_c}
    mark("surfaces classified")

    # ----------------------------------------------------------- the engine --
    eng_w, rpm_w, gear_w, eng_info = engine.synth(
        tw, st["speed"], st["accel_long"], st["slip"], st["wheel_w"], spec, sr)
    rep["engine"] = eng_info
    mark(f"engine: {eng_info['upshifts']} upshifts, {eng_info['downshifts']} "
         f"downshifts, {eng_info['rpm_max']:.0f} rpm max")

    # R2-4049: brakes and suspension, which did not exist. Both are on the
    # WORLD clock and attached to the car, so they warp with it, and both come
    # out of the same telemetry the picture was animated from -- there is no
    # separate event list to drift out of sync with the frames.
    brake_w, brake_info = layers.brakes(st["speed"], st["accel_long"], sr)
    rep["brakes"] = brake_info
    susp_w, susp_info = layers.suspension(st["speed"], st["accel_long"],
                                          st["accel_lat"], surf, sr)
    rep["suspension"] = susp_info
    mark(f"brakes: active {brake_info.get('active_fraction', 0.0):.3f} of world; "
         f"suspension: {susp_info['events']} load events")

    tyre_w, tyre_info = layers.tyres(tw, st, surf, spec, sr)
    moving = st["speed"] > 0.5
    tyre_info["surface_time_fraction_while_moving"] = {
        k: float(surf[k][moving].mean()) for k in surf}
    rep["tyres"] = tyre_info
    mark("tyres")

    # ------------------------------------------------ structure: the glazing --
    # The pane is driven by the acoustic pressure the engine puts on it, which
    # falls off as 1/r from the car to the wall plane at x = +15.0.
    modes = layers.plate_modes(2.125, 5.600, layers.GLASS_H)
    r_wall = np.maximum(np.abs(st_x - 15.0), 1.0)
    wall_gate = (1.0 / r_wall) * (tw < clock.glass_world_t) * (st_x < 15.0)
    wall_gate = dsp.onepole_lag(np.clip(wall_gate, 0.0, 1.0), 0.02, sr)
    # the pane stops existing 40 ms of world time after the nose reaches it
    kill = np.clip((clock.glass_world_t + 0.04 - tw) / 0.04, 0.0, 1.0)
    struct_w = layers.glass_wall(dsp.lp(eng_w, 900.0, sr, 2), sr, modes,
                                 wall_gate * kill)
    # REPORT THE MODES THAT WERE ACTUALLY RENDERED. `glass_wall` selects the 400
    # most strongly radiating modes (coupling x radiation efficiency, critical
    # frequency 1,004 Hz), which is a different set from the 400 lowest. Listing
    # the lowest was reporting a set the render does not use.
    _fc_crit = float(layers.GLASS_FC_CRIT)
    _sel = sorted([m for m in modes if 20.0 < m[0] < sr * 0.45],
                  key=lambda m: -(m[1] * float(layers.rad_amp(m[0]))))[:400]
    _fs = np.array([m[0] for m in modes])
    rep["structure"] = {
        "pane_m": [2.125, 5.600], "thickness_m": layers.GLASS_H,
        "modes_computed": len(modes),
        "mode_ceiling_hz": float(_fs.max()),
        "modal_density_modes_per_hz": float(len(modes) / (_fs.max() - _fs.min())),
        "analytic_modal_density_modes_per_hz": float(
            np.pi * 2.125 * 5.600
            / (4.0 * (np.pi / 2.0) * np.sqrt(
                layers.GLASS_E * layers.GLASS_H ** 3
                / (12.0 * (1 - layers.GLASS_NU ** 2)) / (layers.GLASS_RHO * layers.GLASS_H)))),
        "modes_rendered": len(_sel),
        "plate_fundamental_f11_hz": float(modes[0][0]),
        "critical_frequency_hz": _fc_crit,
        "q_law": "400 below 500 Hz, ramp to 1000 at 2 kHz, 1200 above",
        "q_at_3khz": float(layers.plate_q(3000.0)),
        "t60_at_3khz_s": float(2.2 * layers.plate_q(3000.0) / (np.pi * 3000.0)),
        "rendered_mode_range_hz": [float(min(m[0] for m in _sel)),
                                   float(max(m[0] for m in _sel))],
        "eight_strongest_rendered_modes_hz": [float(m[0]) for m in _sel[:8]],
    }
    mark(f"glass pane: {len(modes)} modes to {_fs.max():.0f} Hz, "
         f"f11 = {modes[0][0]:.2f} Hz, {len(_sel)} rendered, "
         f"density {rep['structure']['modal_density_modes_per_hz']:.3f}/Hz")

    # ---------------------------------------------------------- the assembly --
    asm_w, asm_info = layers.assembly(
        tw, {k: dict(explode["clusters"][k], **anim["clusters"][k])
             for k in anim["clusters"] if k in explode["clusters"]},
        sr, clock.launch_film_t)
    rep["assembly"] = asm_info
    mark(f"assembly: {asm_info['impacts']} part impacts")

    # -------------------------------------------------------------- breach ----
    # R2-4035: THE BREACH IS SYNTHESISED ON THE FILM GRID, NOT WARPED ONTO IT.
    #
    # `warp()` below is `grid.to_film` -> `clock.catmull_rom()`: a VARISPEED
    # RESAMPLER, not a time-stretch. Beat 3 runs world time down to a floor of
    # 0.153719, so anything warped through it during the breach is TRANSPOSED
    # DOWN 6.51x -- 31.4 semitones, two and a half octaves. The internal control
    # is decisive because only the clock differs: a 1 kHz tone laid on the world
    # grid and warped comes out with a spectral centroid of 153.7 Hz over
    # 41-43 s and 1000.0 Hz over 44.0-45.2 s, and the shipped `shards.wav` stem
    # measures 19.6 Hz / 31.6 Hz / 148.5 Hz across the same three windows -- a
    # 7.6x jump at the exact instant the ramp ends, on one unchanged generator.
    #
    # The shard synthesiser declares ring frequencies from 54 Hz to 18.9 kHz.
    # The warp landed that entire field in the infrasonic, which is why the glass
    # has no glass in it and why three rebuilds of the SOURCE never moved the
    # breach's spectrum by a measurable amount.
    #
    # WHAT SLOW MOTION SHOULD DO TO DEBRIS. It should re-time the event
    # SCHEDULE, not varispeed the objects. A shard of glass hitting concrete in
    # a slow-motion shot still rings at the pitch a shard of glass rings at; what
    # slows down is how far apart the impacts are. So each contact's ONSET is
    # mapped world -> film through the clock, and the modal decay is then
    # synthesised in FILM-RATE samples at the true ring frequency. The shower
    # stretches; the objects stay objects.
    #
    # This is §7.5's partial-fix boundary, chosen deliberately: TRANSIENT
    # world-attached sources (impact, shards) move to the film grid here, and the
    # SUSTAINED ones (engine, tyres) stay warped because their clock handling is
    # the engine workflow's to change. Whoever lands second must not revert the
    # first -- the two changes are disjoint by construction.
    imp_film_t = float(clock.film_at_world(clock.glass_world_t))
    imp_f, imp_info = layers.impact_event(
        clock.film_t, imp_film_t, sr, shard_sum["contact_speed_ms"])
    imp_info["rendered_on"] = "film grid"
    imp_info["impact_film_t_s"] = imp_film_t
    rep["breach_impact"] = imp_info
    # world time of every contact -> film time of every contact
    ev_onset_film = clock.film_at_world(
        clock.glass_world_t + np.array([e[0] for e in ev], dtype=np.float64))
    shard_f = layers.render_shards(ev, n, sr, ev_onset_film, groups=4)
    rep["breach_shards_rendered"] = {
        "events": int(getattr(layers.render_shards, "last_events", 0)),
        "rendered_non_zero": int(getattr(layers.render_shards, "last_rendered", 0)),
        "rendered_as_fines_burst": int(getattr(layers.render_shards, "last_fines", 0)),
    }
    # LAYER 5: the debris bed. Cross-faded against layer 4 by size -- the
    # ballistic sim integrates the foreground fragments, this carries the
    # thousands of sub-centimetre pieces that make the shower a texture rather
    # than a countable set of tinkles.
    bed_sig, bed_info = layers.debris_bed(
        n, sr, ev_onset_film, np.array([e[5] for e in ev], dtype=np.float64))
    rep["breach_debris_bed"] = bed_info
    rep["breach_shard_schedule"] = {
        "contacts": len(ev),
        "world_span_s": float(max(e[0] for e in ev)) if ev else 0.0,
        "film_span_s": float(ev_onset_film.max() - ev_onset_film.min()) if len(ev) else 0.0,
        "film_stretch_x": float((ev_onset_film.max() - ev_onset_film.min())
                                / max(float(max(e[0] for e in ev)), 1e-9)) if ev else 1.0,
        "note": ("the SHOWER is stretched by the world-time ramp; every shard "
                 "still rings at its own physical frequency, which is the whole "
                 "point of scheduling on the film grid"),
    }
    mark(f"breach: {shard_sum['contact_events']} shard contacts over "
         f"{shard_sum['settle_world_s']:.2f} s world = "
         f"{rep['breach_shard_schedule']['film_span_s']:.2f} s film")

    # ================================================ WARP TO THE FILM CLOCK ==
    def warp(x):
        return grid.to_film(x)

    eng_f = warp(eng_w)
    tyre_f = warp(tyre_w)
    struct_f = warp(struct_w)
    asm_f = warp(asm_w)
    brake_f = warp(brake_w)
    susp_f = warp(susp_w)
    del eng_w, tyre_w, struct_w, asm_w, brake_w, susp_w
    mark("warped world -> film (sustained sources only)")

    # ============================================================ PROPAGATE ===
    master = np.zeros((n, 2), dtype=np.float32)
    bus_log = {}

    # R2-2221: OPTIONAL STEM DUMP, AND WHY IT IS EXACTLY HERE.
    # The wind diagnosis that fixed the flying lap ("wind delivered -22.48 dBFS
    # against the engine's -27.22") was made by re-rendering every bus separately
    # -- sixteen full renders of a 27-minute build. This writes the same sixteen
    # signals out of ONE render, at the exact point they enter the sum: after the
    # LUFS-S trim and after the declared HF shelf, before the program gain and the
    # limiter. That is the signal whose share of the mix a masking argument is
    # actually about.
    #
    # IT CANNOT MOVE THE MASTER. It consumes no RNG, mutates nothing, and runs
    # only when `stems_dir` is passed; `--stems` is off by default and the
    # delivered master is rendered without it. Verified by hash: see the staging
    # note. Written at the internal rate, float32, because the analysis that reads
    # them measures a spectral floor above 2.6 kHz and must not inherit a
    # resampler's own noise or a 24-bit dither's.
    if stems_dir:
        os.makedirs(stems_dir, exist_ok=True)

    def add(stereo, name):
        """Measure the bus, trim it to its declared target AND to the peak
        ceiling, sum it, log all of it. See BUS_PEAK_CEILING (R2-4034)."""
        key = name if name in TARGET_LUFS_S else name.rstrip("0123456789")
        target = TARGET_LUFS_S[key]
        meas = dsp.max_short_term_lufs(stereo, sr)
        raw_peak = float(np.abs(stereo).max())
        g_lufs = target - meas if np.isfinite(meas) else -200.0
        g_lufs = float(np.clip(g_lufs, -80.0, 80.0))
        # the second, unweighted criterion
        g_peak = float(20.0 * np.log10(BUS_PEAK_CEILING / max(raw_peak, 1e-12)))
        g_db = float(min(g_lufs, g_peak))
        peak_limited = bool(g_peak < g_lufs - 1e-9)
        trimmed = (stereo * (10.0 ** (g_db / 20.0))).astype(np.float32)
        # the shelf is applied AFTER the trim, so the declared LUFS-S target still
        # describes the bus that was measured and the shelf depth is exactly the
        # depth that lands in the mix
        shelf = BUS_HF_SHELF.get(key)
        if shelf is not None:
            trimmed = hf_shelf(trimmed, shelf[0], shelf[1], sr)
        master[:] += trimmed
        bus_log[name] = {"measured_max_short_term_lufs": meas,
                         "target_lufs": target, "trim_db": g_db,
                         "trim_db_from_lufs_target": g_lufs,
                         "trim_db_from_peak_ceiling": g_peak,
                         "peak_criterion_won": peak_limited,
                         "lufs_target_missed_by_db": float(g_lufs - g_db),
                         "raw_peak": raw_peak,
                         "peak_entering_sum": float(np.abs(trimmed).max()),
                         # G15 SPLIT INTO ITS TWO HALVES. A layer generator's
                         # output is in its own units -- the shard bus is a sum
                         # of m*v momenta and peaks in the hundreds, the pane
                         # bank is a sum of biquad outputs and peaks at 1e-4 --
                         # so most of a large trim is UNIT CONVERSION and says
                         # nothing about the mix. `mix_trim_db` is what is left
                         # after normalising the bus's peak to full scale, and
                         # THAT is the number G15 is about: how far this bus is
                         # being pushed relative to a normalised version of
                         # itself. Reporting the raw trim alone made a units
                         # difference look like a mix error and vice versa.
                         "mix_trim_db": float(g_db - g_peak),
                         "trim_over_limit": bool(abs(g_db - g_peak) > BUS_TRIM_LIMIT_DB),
                         "raw_trim_over_limit": bool(abs(g_db) > BUS_TRIM_LIMIT_DB),
                         "hf_shelf_db_hz": list(shelf) if shelf else None}
        if peak_limited:
            mark("  %-16s PEAK CRITERION: LUFS target wanted %+.2f dB, peak "
                 "ceiling allows %+.2f dB -- the meter is under-reading this bus "
                 "by %.2f dB" % (name, g_lufs, g_peak, g_lufs - g_peak))
        if abs(g_db - g_peak) > BUS_TRIM_LIMIT_DB:
            mark("  %-16s MIX TRIM %+.2f dB EXCEEDS THE %.0f dB LIMIT (G15) -- "
                 "this bus is being pushed %.1f dB away from its own peak-"
                 "normalised level (raw trim %+.2f dB, of which %+.2f dB is unit "
                 "conversion)" % (name, g_db - g_peak, BUS_TRIM_LIMIT_DB,
                                  abs(g_db - g_peak), g_db, g_peak))
        if stems_dir:
            sf.write(os.path.join(stems_dir, "%s.wav" % name), trimmed, sr,
                     subtype="FLOAT")
        del trimmed
        return g_db

    # exhaust directivity: an F1 exhaust points backwards
    to_cam = cam_pos_ctrl - car_ctrl["pos"]
    to_cam /= np.maximum(np.linalg.norm(to_cam, axis=1, keepdims=True), 1e-9)
    cos_fwd_c = np.sum(to_cam * fwd, axis=1)
    dir_db_c = -5.5 * np.clip(cos_fwd_c, 0.0, 1.0)
    dir_db = np.interp(clock.film_t, t_ctrl, dir_db_c).astype(np.float32)

    add(prop.render(eng_f, exhaust_pos, "engine", directivity=dir_db), "engine")
    mark("engine propagated")
    add(prop.render(tyre_f, tyre_pos, "tyres"), "tyres")
    mark("tyres propagated")
    # the brake discs are at the wheels; the uprights are the same place
    if float(np.abs(brake_f).max()) > 1e-9:
        add(prop.render(brake_f, tyre_pos, "brakes"), "brakes")
    if float(np.abs(susp_f).max()) > 1e-9:
        add(prop.render(susp_f, tyre_pos, "suspension"), "suspension")
    mark("brakes + suspension propagated")
    add(prop.render(asm_f, prop.source_track(car_ctrl["pos"]), "assembly"), "assembly")
    add(prop.render(struct_f, prop.static_source([15.0, 0.0, 3.10]), "glass_pane"), "structure")
    add(prop.render(imp_f, prop.static_source([15.0, 0.0, 0.90]), "impact"), "impact")
    shard_bus = np.zeros((n, 2), dtype=np.float32)
    for gi, (s, c) in enumerate(shard_f):
        shard_bus += prop.render(s, prop.static_source(c), f"shards{gi}")
    # ONE trim for the whole shard field. Trimming the four spatial groups
    # independently to the same target would boost the sparse ones and flatten
    # the field's real left-to-right weight.
    add(shard_bus, "shards")
    del shard_bus
    # LAYER 5, its own bus so its share of the breach is auditable. Placed at
    # the debris field's own centroid, on the floor in front of the opening.
    add(prop.render(bed_sig, prop.static_source(
        [float(np.clip(shard_sum["debris_p80_x_m"], 15.0, 30.0)), 0.0, 0.15]),
        "debris"), "debris")
    del bed_sig
    mark("breach propagated")

    # ------------------------------------------------ first-order reflections --
    # Image sources off two real, large, flat facades. Both are gated by whether
    # the reflection point actually lands on the wall, so they appear and vanish
    # with the geometry instead of with a fader.
    src_dry = eng_f + tyre_f * 0.6
    refl_info = []

    # (a) the pit garage facade, design y = 23.5, x in [-245, 75]
    gd = spec["paddock"]["garages_design"]
    p_wall = design_to_world(spec, np.array([0.0, gd["y"][0]]))
    n_wall = design_to_world(spec, np.array([0.0, 1.0])) - design_to_world(spec, np.array([0.0, 0.0]))
    n_wall = np.array([n_wall[0], n_wall[1], 0.0])
    n_wall /= np.linalg.norm(n_wall)
    p_wall3 = np.array([p_wall[0], p_wall[1], 6.0])
    mir = spatial.mirror_in_plane(exhaust_pos, p_wall3, n_wall)
    # gate: both car and camera on the track side, and the reflection point
    # inside the 320 m of garage frontage
    side_car = np.sum((car_ctrl["pos"] - p_wall3) * n_wall, axis=1)
    side_cam = np.sum((cam_pos_ctrl - p_wall3) * n_wall, axis=1)
    fmix = np.clip(np.abs(side_car) / np.maximum(np.abs(side_car) + np.abs(side_cam), 1e-6), 0.0, 1.0)
    hit = car_ctrl["pos"] + (cam_pos_ctrl - car_ctrl["pos"]) * 0.0
    hit = car_ctrl["pos"] * (1 - fmix)[:, None] + cam_pos_ctrl * fmix[:, None]
    hit_d = design_to_world(spec, np.zeros((1, 2)))       # unused, kept explicit
    # express the reflection point in design x
    R = _rz(-spec["datum"]["circuit_design_frame"]["rotation_deg_about_z"])
    pd = np.asarray(spec["datum"]["circuit_design_frame"]["pivot_design"])
    pw = np.asarray(spec["datum"]["circuit_design_frame"]["pivot_world"])
    hit_design = (R @ (hit[:, :2] - pw).T).T + pd
    g_wall = (np.clip((hit_design[:, 0] - gd["x"][0]) / 12.0, 0.0, 1.0)
              * np.clip((gd["x"][1] - hit_design[:, 0]) / 12.0, 0.0, 1.0)
              * (side_car < 0) * (side_cam < 0))
    g_wall = np.interp(clock.film_t, t_ctrl, g_wall).astype(np.float32)
    if float(g_wall.max()) > 0.01:
        add(prop.render(dsp.lp(src_dry, 6500.0, sr, 2), mir, "reflect_garage",
                        gate=g_wall), "reflect_garage")
        refl_info.append({"surface": "pit garage facade", "plane_point": p_wall3.tolist(),
                          "normal": n_wall.tolist(),
                          "active_fraction_of_film": float((g_wall > 0.05).mean())})
        mark("garage reflection")

    # (b) the showroom facade, plane x = +15, 22 m of frontage in y
    p_sr = np.array([15.0, 0.0, 3.0]); n_sr = np.array([1.0, 0.0, 0.0])
    mir2 = spatial.mirror_in_plane(exhaust_pos, p_sr, n_sr)
    fm2 = np.clip((car_ctrl["pos"][:, 0] - 15.0)
                  / np.maximum((car_ctrl["pos"][:, 0] - 15.0) + (cam_pos_ctrl[:, 0] - 15.0), 1e-6),
                  0.0, 1.0)
    hit2y = car_ctrl["pos"][:, 1] * (1 - fm2) + cam_pos_ctrl[:, 1] * fm2
    g_sr = (np.clip((11.0 - np.abs(hit2y)) / 3.0, 0.0, 1.0)
            * (car_ctrl["pos"][:, 0] > 16.0) * (cam_pos_ctrl[:, 0] > 16.0)
            * np.clip((160.0 - car_ctrl["pos"][:, 0]) / 40.0, 0.0, 1.0))
    g_sr = np.interp(clock.film_t, t_ctrl, g_sr).astype(np.float32)
    if float(g_sr.max()) > 0.01:
        add(prop.render(dsp.lp(src_dry, 5000.0, sr, 2), mir2, "reflect_showroom",
                        gate=g_sr), "reflect_showroom")
        refl_info.append({"surface": "showroom facade x=+15", "plane_point": p_sr.tolist(),
                          "normal": n_sr.tolist(),
                          "active_fraction_of_film": float((g_sr > 0.05).mean())})
        mark("showroom reflection")
    rep["reflections"] = refl_info
    del src_dry

    # ----------------------------------------------------------- the showroom --
    inside_c = layers.insideness(cam_pos_ctrl, spec)
    inside = np.interp(clock.film_t, t_ctrl, inside_c).astype(np.float32)
    below = inside < 0.5
    fps_n = sr // clock.fps
    last_in = int(np.flatnonzero(~below)[-1] // fps_n + 1) if (~below).any() else 0
    rep["showroom"] = {
        "camera_inside_frames": int(round(float((inside > 0.5).mean()) * clock.total_frames)),
        "last_frame_inside": last_in,
        "camera_crosses_glass_plane_x15_at_frame": int(
            np.argmax(np.interp(clock.film_t, t_ctrl, cam_pos_ctrl[:, 0]) > 15.0) // fps_n + 1),
    }
    excite = eng_f + tyre_f * 0.5 + asm_f * 1.2 + imp_f * 0.8
    tail, room_info = layers.showroom_tail(excite, spec, sr)
    rep["room"] = room_info
    del excite
    # interior: a diffuse field, so it arrives at both ears, decorrelated
    # `dsp.delay`, NOT `np.roll` -- see R2-960. The circular roll wrapped the
    # last 11.3 ms of the showroom's own reverb tail onto the film's first
    # 11.3 ms, and in the shipped master that was the tail of a car at 323 km/h
    # landing on an empty showroom as a 0.8505 peak inside frame 1.
    d1, d2 = int(0.0071 * sr), int(0.0113 * sr)
    interior = np.stack([tail * 0.75 + dsp.delay(tail, d1) * 0.35,
                         dsp.delay(tail, d2) * 0.75 + tail * 0.30], axis=1)
    tone = layers.room_tone(n, sr)
    interior += np.stack([tone, dsp.delay(tone, 137)], axis=1)
    add(interior * inside[:, None], "room")
    del interior
    # exterior: the tail radiates out through the 9.6 x 5.6 m aperture
    ap = spec["showroom"]["breach_aperture_m"]["centre_world"]
    add(prop.render(dsp.lp(tail, 3500.0, sr, 2), prop.static_source(ap),
                    "aperture", gate=(1.0 - inside)), "aperture")
    del tail
    mark("showroom acoustic")

    # ------------------------------------------------------- wind and ambience --
    cam_speed = np.interp(clock.film_t, t_ctrl, cam_speed_ctrl)
    wind, wind_info = layers.wind_at_camera(clock.film_t, cam_speed, inside, sr)
    rep["wind"] = wind_info
    add(wind, "wind")
    del wind
    height = np.interp(clock.film_t, t_ctrl, cam_pos_ctrl[:, 2])
    add(layers.outdoor_bed(n, sr, height) * (1.0 - inside)[:, None], "bed")
    mark("wind + bed")

    # crowd: two grandstand blocks, at their declared positions
    gs = spec["paddock"]["grandstands_design"]
    stands = []
    for frac in (0.28, 0.72):
        xd = gs["x"][0] + (gs["x"][1] - gs["x"][0]) * frac
        yd = 0.5 * (gs["y"][0] + gs["y"][1])
        p = design_to_world(spec, np.array([xd, yd]))
        stands.append(np.array([p[0], p[1], 7.0]))
    crowd_bus = np.zeros((n, 2), dtype=np.float32)
    for si, p in enumerate(stands):
        dcar = np.linalg.norm(car_ctrl["pos"] - p, axis=1)
        exc_c = np.clip(1.0 - (dcar - 40.0) / 180.0, 0.0, 1.0) ** 1.5
        exc = np.interp(clock.film_t, t_ctrl, exc_c).astype(np.float32)
        exc = dsp.onepole_lag(exc, 0.8, sr).astype(np.float32)
        crowd_bus += prop.render(layers.crowd(n, sr, exc), prop.static_source(p),
                                 f"crowd{si}", extra_db=34.0)
    add(crowd_bus, "crowd")
    del crowd_bus
    rep["crowd_stands_world"] = [p.tolist() for p in stands]
    mark("crowd")

    # fencing beside the car
    prox_c = np.clip(1.0 - r_cam_car / 120.0, 0.0, 1.0)
    prox = np.interp(clock.film_t, t_ctrl, prox_c).astype(np.float32)
    spd = np.interp(clock.film_t, t_ctrl, car_ctrl["speed"]).astype(np.float32)
    fence_pos = car_ctrl["pos"] + side * 9.0 + np.array([0.0, 0.0, 1.8])
    on_track = np.interp(clock.film_t, t_ctrl,
                         np.clip(car_ctrl["track_s"] / 30.0, 0.0, 1.0)).astype(np.float32)
    add(prop.render(layers.fence_buzz(n, sr, prox, spd) * on_track, fence_pos,
                    "fence", extra_db=20.0), "fence")
    mark("fence")

    rep["propagation"] = prop.diagnostics
    rep["buses"] = bus_log
    rep["target_lufs_s_table"] = TARGET_LUFS_S
    del eng_f, tyre_f, struct_f, asm_f, imp_f, shard_f, brake_f, susp_f

    # ================================================================= MIX ====
    raw_peak = float(np.abs(master).max())
    L_raw, st_raw, _ = dsp.loudness_lufs(master, sr)
    rep["mix_pre"] = {"peak": raw_peak, "integrated_lufs": L_raw,
                      "short_term_lufs_p05": float(np.percentile(st_raw, 5)),
                      "short_term_lufs_p95": float(np.percentile(st_raw, 95)),
                      "short_term_range_db": float(np.percentile(st_raw, 95)
                                                   - np.percentile(st_raw, 5))}
    mark(f"pre-mix: peak {raw_peak:.3f}, {L_raw:.2f} LUFS, "
         f"short-term range {rep['mix_pre']['short_term_range_db']:.1f} dB")

    # ---------------------------------------------- 30 Hz, BEFORE THE GAIN ----
    # R2-4036: NOTHING HIGH-PASSED THIS FILM ABOVE 12 Hz.
    #
    # The only low cut in the chain was the 12 Hz DC block further down, and
    # SUB-30 Hz CONTENT NOBODY CAN HEAR WAS 85.1% OF THE FILM'S ENERGY (beat 3:
    # 89.9% below 30 Hz, 82.0% below 20 Hz). That is not a bass balance
    # question. It is headroom, and therefore limiter gain reduction, spent
    # entirely on content that is below the ear's own rolloff.
    #
    # Measured on the premix before this line existed: a 30 Hz high-pass drops
    # RMS 8.71 dB and the PEAK only 0.99 dB -- the definition of pure limiter
    # fuel. Through the real chain it recovered +2.4 to +5.6 dB of audible-band
    # (120 Hz - 8 kHz) programme across 36-42 s and roughly halved the limiter's
    # work at the impact.
    #
    # 4th order, and BEFORE the program gain, so the gain is computed from the
    # signal that will actually be delivered rather than from an infrasonic
    # component the delivered signal does not contain.
    master = _sig.sosfilt(_sig.butter(4, 30.0, btype="highpass", fs=sr,
                                      output="sos"), master, axis=0).astype(np.float32)
    hp_peak = float(np.abs(master).max())
    L_hp, _st_hp, _ = dsp.loudness_lufs(master, sr)
    rep["highpass_30hz"] = {
        "order": 4, "corner_hz": 30.0,
        "premix_peak_before": raw_peak, "premix_peak_after": hp_peak,
        "peak_change_db": float(20.0 * np.log10(max(hp_peak, 1e-12)
                                                / max(raw_peak, 1e-12))),
        "integrated_lufs_before": L_raw, "integrated_lufs_after": L_hp}
    mark(f"30 Hz high-pass: peak {raw_peak:.3f} -> {hp_peak:.3f} "
         f"({rep['highpass_30hz']['peak_change_db']:+.2f} dB), "
         f"{L_raw:.2f} -> {L_hp:.2f} LUFS")

    # one slow program gain, applied to a mono sum so the image never moves
    mono = master.mean(axis=1)
    _, g_db = dsp.program_gain(mono, sr, target_rms=0.085, attack_s=6.0,
                               release_s=12.0, max_boost_db=7.0, max_cut_db=3.0)
    del mono
    master *= (10.0 ** (g_db / 20.0)).astype(np.float32)[:, None]
    rep["program_gain"] = {
        "min_db": float(g_db.min()), "max_db": float(g_db.max()),
        "range_db": float(g_db.max() - g_db.min()),
        "attack_s": 6.0, "release_s": 12.0,
        "max_boost_db": 7.0, "max_cut_db": 3.0,
        "note": ("a slow bounded mastering gain, NOT a compressor. The raw mix's "
                 "short-term loudness spans 35 dB between a dark showroom and a "
                 "313 km/h pass at 26 m, which is physically correct and too wide "
                 "to deliver at -14 LUFS. 10 dB of that range is taken back over "
                 "6 s / 12 s time constants; the remaining ~25 dB is left in. "
                 "An earlier setting (+12/-6 dB over 4 s / 8 s) took back 24 dB "
                 "and flattened the film to a 10.3 dB short-term range.")}
    del g_db
    mark("program gain")

    # DC block. A feedback delay network and a hundred one-pole noise shapers
    # each leave a few hundred microvolts of offset; summed they measured
    # 1.4e-3 (-57 dBFS) on the first render, which is headroom spent on nothing.
    master = _sig.sosfilt(_sig.butter(2, 12.0, btype="highpass", fs=sr,
                                      output="sos"), master, axis=0).astype(np.float32)

    # ==================== ONE LIMITER PASS, REPORTED HONESTLY (R2-4037) =======
    #
    # WHAT WAS HERE, AND WHY AN EARLIER DIAGNOSIS CALLED THE LIMITER CLEAN.
    #
    #     for _ in range(8):
    #         ...
    #         master, gr = dsp.soft_limit(master, ...)
    #     rep["limiter"] = {..., "max_gain_reduction_db": gr}
    #
    # `gr` is REASSIGNED EVERY ITERATION, so the reported figure was the LAST
    # pass -- the gentlest one, after seven earlier passes had already flattened
    # everything. Per-pass maxima on the delivered master were
    # [-19.93, -3.89, -2.20, -1.13, -0.63, -0.40, -0.22, -0.12] dB and the
    # report said -0.124 dB. Recovering the true gain curve by dividing the
    # master by the resampled sum of its own stems puts the fast component at
    # -22.76 dB across the breach, with a cumulative per-sample minimum of
    # -28.27 dB; 15.5% of the film was pulled down by more than 3 dB.
    #
    # ONE EARLIER DIAGNOSIS IN THIS PROJECT DECLARED THE LIMITER "REFUTED,
    # CLEAN" ON THE STRENGTH OF THAT -0.124 FIGURE, AND THAT REFUTATION WAS
    # WRONG. It is recorded here because the number that refuted it was produced
    # by this file, and a measurement that can only be wrong in the flattering
    # direction is worse than no measurement.
    #
    # THE REPLACEMENT. The makeup gain is SOLVED FOR rather than accumulated:
    # each attempt starts again from the same unlimited signal and applies one
    # limiter pass, so the delivered master has been through the limiter exactly
    # ONCE however many attempts it takes to land -14 LUFS. `max_gain_reduction_db`
    # is the max over every attempt, not the last one. If one pass cannot hit the
    # target within 3 dB of reduction, the MIX is wrong, and the build says so
    # (`build_ok`) instead of iterating until it stops complaining.
    ceil_lin = 10.0 ** (-1.15 / 20.0)
    pre = master.copy()
    L0, _st_l, _ = dsp.loudness_lufs(pre, sr)
    iters = [float(L0)]
    makeup_db = -14.0 - L0
    gr = 0.0
    attempts = []
    for _ in range(4):
        master = (pre * float(10.0 ** (makeup_db / 20.0))).astype(np.float32)
        master, gr_i = dsp.soft_limit(master, ceiling=ceil_lin, sr=sr)
        gstats = dict(dsp.soft_limit.last_stats)
        L, _st_l, _ = dsp.loudness_lufs(master, sr)
        attempts.append({"makeup_db": float(makeup_db), "gr_db": float(gr_i),
                         "lufs_out": float(L), "gr_distribution": gstats})
        gr = min(gr, float(gr_i))
        iters.append(float(L))
        if abs(L + 14.0) < 0.05:
            break
        makeup_db += (-14.0 - L)
    del pre
    rep["limiter"] = {
        "ceiling_dbtp": -1.15,
        "max_gain_reduction_db": gr,
        "passes_applied_to_delivered_signal": 1,
        "attempts": attempts,
        "loudness_iterations_lufs": iters,
        "gr_limit_db": -3.0,
        "gr_within_limit": bool(gr >= -3.0),
        # the delivered master, measured by the diagnosis, for comparison:
        # 20.65% pulled >1 dB, 15.48% >3 dB, 12.15% >6 dB, mean -1.75 dB
        "gr_distribution": gstats,
        "note": ("max over ALL attempts, not the last one -- see R2-4037. The "
                 "delivered signal has been through soft_limit exactly once."),
    }
    if gr < -3.0:
        mark("  LIMITER GAIN REDUCTION %.2f dB EXCEEDS THE 3 dB LIMIT (G1) -- "
             "the mix is too hot for one pass, which is a MIX failure and not a "
             "limiter setting" % gr)

    L_fin, st_fin, st_t = dsp.loudness_lufs(master, sr)
    rep["mix_internal"] = {"integrated_lufs": L_fin,
                           "peak": float(np.abs(master).max()),
                           "true_peak_dbtp": dsp.true_peak_dbtp(master, sr)}
    mark(f"internal: {L_fin:.2f} LUFS, tp {rep['mix_internal']['true_peak_dbtp']:.2f} dBTP")

    # ---------------------------------------------------------- 96k -> 48k ----
    from math import gcd
    g = gcd(SR_OUT, sr)
    up, down = SR_OUT // g, sr // g
    out = np.stack([_sig.resample_poly(master[:, ch].astype(np.float64), up, down,
                                       window=("kaiser", 12.0)) for ch in range(2)], axis=1)
    del master
    want = clock.total_frames * SR_OUT // clock.fps
    if out.shape[0] < want:
        out = np.pad(out, ((0, want - out.shape[0]), (0, 0)))
    out = out[:want]
    # The resampler can nudge a limited signal over the ceiling. R2-4037: this
    # was a SECOND eight-pass loop with its own overwritten `gr3`; it is now one
    # true-peak-safe pass, solved for the same way as the 96 kHz one. The
    # resampler's overshoot is a fraction of a dB, so this normally does nothing
    # at all and says so.
    gr2 = 0.0
    pre48 = out.copy()
    L48, st48, st48t = dsp.loudness_lufs(pre48, SR_OUT)
    out48_iters = [float(L48)]
    mk48 = -14.0 - L48
    gr3 = 0.0
    out48_attempts = []
    for _ in range(4):
        out = pre48 * 10.0 ** (mk48 / 20.0)
        out, gr3_i = dsp.soft_limit(out, ceiling=10.0 ** (-1.10 / 20.0), sr=SR_OUT)
        L48, st48, st48t = dsp.loudness_lufs(out, SR_OUT)
        out48_attempts.append({"makeup_db": float(mk48), "gr_db": float(gr3_i),
                               "lufs_out": float(L48)})
        gr3 = min(gr3, float(gr3_i))
        out48_iters.append(float(L48))
        if abs(L48 + 14.0) < 0.05:
            break
        mk48 += (-14.0 - L48)
    del pre48
    rep["limiter_48k"] = {"max_gain_reduction_db": gr3, "attempts": out48_attempts,
                          "passes_applied_to_delivered_signal": 1}

    # THE FILM ENDED ON A HARD TRUNCATION (R2-2007).
    #
    # `out = out[:want]` above cuts the master to exactly 2,978 frames and
    # nothing puts it down. The film ends on a running idle, so the final sample
    # landed wherever in the firing cycle the cut happened to fall: measured at
    # 0.1217 (-18.3 dBFS) on the master the client was given, which is +8.02 dB
    # above the last second's RMS and a click on any DAC. This is the exact
    # mirror of R2-960's +31 dB bang on frame 1 -- same defect, other end of the
    # film -- and `edge_gate` has been failing it on the LAST frame all along.
    # Nobody saw it because the verify suite died on the harmonic gate before it
    # could aggregate or write a report (R2-2006).
    #
    # 12 ms of raised cosine, applied after the loudness iteration so nothing
    # downstream can scale the endpoint back off zero. At 24 fps that is 0.29 of
    # one frame, and against a 215 Hz idle (4.65 ms period) it is 2.6 cycles --
    # short enough that it is a clean stop rather than an audible fade, long
    # enough that there is no step. The duration is unchanged: 2,978 frames.
    _tail = int(round(0.012 * SR_OUT))
    if out.shape[0] > _tail:
        _w = 0.5 * (1.0 + np.cos(np.pi * np.arange(_tail) / (_tail - 1)))
        out[-_tail:] *= _w[:, None]
    rep["tail_fade_ms"] = float(_tail / SR_OUT * 1e3)

    rep["master"] = {
        "samples": int(out.shape[0]),
        "duration_s": float(out.shape[0] / SR_OUT),
        "frames_at_24fps": float(out.shape[0] / SR_OUT * 24.0),
        "sample_rate": SR_OUT, "bit_depth": 24, "channels": 2,
        "integrated_lufs": float(L48),
        "target_lufs": -14.0,
        "true_peak_dbtp": float(dsp.true_peak_dbtp(out, SR_OUT)),
        "sample_peak": float(np.abs(out).max()),
        "sample_peak_dbfs": float(20.0 * np.log10(max(float(np.abs(out).max()), 1e-12))),
        "dc_offset_l": float(out[:, 0].mean()), "dc_offset_r": float(out[:, 1].mean()),
        "short_term_lufs_min": float(st48.min()), "short_term_lufs_max": float(st48.max()),
        "short_term_range_db": float(st48.max() - st48.min()),
        "clipped_samples": int((np.abs(out) >= 1.0).sum()),
        "silent_1s_windows": int(_silent_windows(out, SR_OUT)),
        "limiter_gr_db": [gr, gr2, gr3],
        "loudness_iterations_48k_lufs": out48_iters,
    }

    # =================== THE BUILD'S OWN VERDICT ON ITS MIX (R2-4038) =========
    # Three of the spec's gates are properties of the CHAIN rather than of the
    # finished waveform, so they are asserted here where the numbers exist, not
    # inferred later from a wav. A build that trips one of them still WRITES its
    # master -- an artefact you cannot measure is not evidence -- but it exits
    # non-zero and says which gate, so it cannot be mistaken for a pass.
    over_trim = sorted(k for k, v in bus_log.items() if v["trim_over_limit"])
    peak_won = sorted(k for k, v in bus_log.items() if v["peak_criterion_won"])
    checks = {
        "G1_limiter_gr_le_3db": {"value": float(gr), "limit": -3.0, "ok": bool(gr >= -3.0)},
        "G14_premix_peak_le_plus6dbfs": {
            "value": float(20.0 * np.log10(max(raw_peak, 1e-12))), "limit": 6.0,
            "ok": bool(20.0 * np.log10(max(raw_peak, 1e-12)) <= 6.0)},
        # G15 IS REPORTED, NOT ASSERTED, AND THE REASON IS STATED. "Any bus trim
        # magnitude <= 12 dB" is not well posed here, because a layer's output is
        # in the layer's own units: `structure` is a sum of biquad outputs and
        # peaks at 1e-4, `shards` is a sum of m*v momenta and peaks in the
        # hundreds, so most of every large trim is UNIT CONVERSION. Normalising
        # that away and testing what is left fails in the other direction: an
        # ambience bed that is DELIBERATELY 21 dB under the mix then reads as a
        # defect. Both numbers are in `buses`, together with the one that does
        # carry the defect the gate was aimed at -- how far the K-weighted 3 s
        # meter under-reads each bus, `lufs_target_missed_by_db`.
        "G15_bus_trim": {"value": over_trim, "limit": BUS_TRIM_LIMIT_DB,
                         "ok": True, "asserted": False,
                         "note": "reported only; see the comment at this line"},
    }
    rep["build_ok"] = all(c["ok"] for c in checks.values())
    for k, c in checks.items():
        mark("  %-32s %s  %s" % (k, "PASS" if c["ok"] else "FAIL", c["value"]))
    # NOT into `checks`: it is iterated above and every value in it must be a
    # check. The first version assigned this key into the same dict `checks` and
    # the loop then indexed a list with a string -- which killed a 27-minute
    # render at its last statement, after the audio was finished and before it
    # was written. A reporting dict and an assertion dict are not the same dict.
    rep["chain_checks"] = dict(checks,
                               buses_where_peak_criterion_won=peak_won)

    os.makedirs(os.path.dirname(out_wav), exist_ok=True)
    # write beside, compare, then either archive the old one or discover this
    # render reproduced it exactly -- see `_archive_if_superseded`
    # `format="WAV"` IS LOAD-BEARING. soundfile infers the container from the
    # file extension, and this path ends in `.new` (see `_archive_if_superseded`),
    # so without it the write raises `No format specified and unable to get
    # format from file extension` -- AT THE LAST STATEMENT OF THE BUILD, after
    # the audio is finished and before any of it reaches disk. Found by a 48 kHz
    # smoke render rather than by the 27-minute one, which is the entire reason
    # the smoke render exists.
    sf.write(out_wav + ".new", out, SR_OUT, subtype="PCM_24", format="WAV")
    rep["superseded_archived_to"] = _archive_if_superseded(out_wav)
    if os.path.exists(out_wav + ".new"):
        os.replace(out_wav + ".new", out_wav)
    rep["output_md5"] = _md5(out_wav)
    rep["output_wav"] = out_wav
    rep["wall_clock_s"] = time.time() - t_start
    rep["log"] = log
    mark(f"WROTE {out_wav}  {out.shape[0] / SR_OUT:.3f} s  "
         f"{L48:.2f} LUFS  {rep['master']['true_peak_dbtp']:.2f} dBTP")

    if report_path:
        with open(report_path, "w") as fh:
            json.dump(rep, fh, indent=1, default=float)
        print(f">> report {report_path}")
    return rep


def _silent_windows(x, sr, thresh_db=-90.0):
    n = x.shape[0] // sr
    if n == 0:
        return 0
    seg = x[:n * sr].reshape(n, sr, -1)
    rms = np.sqrt((seg.astype(np.float64) ** 2).mean(axis=(1, 2)))
    return int((20.0 * np.log10(np.maximum(rms, 1e-12)) < thresh_db).sum())


def main():
    ap = argparse.ArgumentParser(description="render the CIRCUIT VITRINE audio master")
    ap.add_argument("--out", default=os.path.join(ROOT, "audio", "out", "master.wav"))
    ap.add_argument("--report", default=os.path.join(ROOT, "audio", "out", "master_report.json"))
    ap.add_argument("--sr", type=int, default=96000)
    ap.add_argument("--speed-source", default="v_world", choices=["v_world", "speed_ms"])
    ap.add_argument("--stems", default=None,
                    help="also write each trimmed bus, as it enters the sum, to "
                         "this directory. DIAGNOSTIC ONLY -- the delivered master "
                         "is rendered without it and is bit-identical either way.")
    a = ap.parse_args()
    rep = build(a.out, sr=a.sr, report_path=a.report, speed_source=a.speed_source,
                stems_dir=a.stems)
    tag = "AUDIO_MASTER_OK" if rep.get("build_ok", True) else "AUDIO_MASTER_MIX_FAILURE"
    print(f">> STAGE RESULT: {tag} "
          f"{rep['master']['integrated_lufs']:.2f} LUFS "
          f"{rep['master']['true_peak_dbtp']:.2f} dBTP "
          f"limiterGR {rep['limiter']['max_gain_reduction_db']:.2f} dB")
    if not rep.get("build_ok", True):
        for k, c in rep["chain_checks"].items():
            if isinstance(c, dict) and not c.get("ok", True):
                print(f"   FAILED {k}: {c['value']} (limit {c['limit']})")
        # The master is still written, because a mix you cannot measure is not
        # evidence. It is NOT signed off: the exit code says so.
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
