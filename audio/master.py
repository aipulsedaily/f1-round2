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
    "assembly": -27.0,        # beat 1 is intimate; the engine is not running
    "structure": -30.0,       # the pane buzzing before it goes
    "impact": -6.5,           # the breach is the loudest single event
    "shards": -9.0,
    "reflect_garage": -22.0,
    "reflect_showroom": -25.0,
    "room": -23.0,            # the showroom's own tail, heard from inside
    "aperture": -27.0,        # that tail radiating out through the hole
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
# Hz). Nothing else in the mix is EQ'd, and this table exists so that the three
# buses which are EQ'd say so out loud.
#
# WHY IT IS HERE AND NOT INSIDE `layers.py`. This is a MIX decision and putting
# it in the layer would disguise it as physics. The wind's ~9 dB/octave rolloff
# (pink noise through a one-pole) sits inside the physical range for aerodynamic
# edge noise and is NOT being called a modelling error. What is being said is
# narrower and is a mixing statement: wind, tyre roar and the outdoor bed exist to
# carry SPEED, WEIGHT and SPACE, all three of which live below about 2 kHz, and
# their content above that contributes almost nothing to their purpose while
# sitting exactly where the engine's harmonic signature lives.
#
# The measurement that forced it: with the R2-1401 engine rebuilt, the engine bus
# ALONE reads +14.35 dB harmonic-to-noise above 2.6 kHz over the flying lap and
# the full mix read +0.71 dB. Thirteen and a half dB of the rebuild was being
# thrown away by three noise beds. This table recovers 6.0 dB of it, and it is
# deliberately not more: the beds are still audible, still doing their job, and
# the film's octave balance over the lap comes out BRIGHTER in the 500 Hz - 4 kHz
# region (+2.6 to +3.6 dB relative) and only 1.9 dB darker in the top octave,
# because the engine's own harmonics now occupy the space the noise was in.
BUS_HF_SHELF = {
    "wind": (-12.0, 2000.0),
    "tyres": (-12.0, 2000.0),
    "bed": (-12.0, 2000.0),
}


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
    # REPORT THE MODES THAT WERE ACTUALLY RENDERED. `glass_wall` selects the 72
    # most strongly radiating modes (coupling x radiation efficiency, critical
    # frequency 1,004 Hz), which is a different set from the 72 lowest. Listing
    # the lowest was reporting a set the render does not use.
    _fc_crit = float(dsp.speed_of_sound(18.0)) ** 2 / (1.8 * layers.GLASS_CL * layers.GLASS_H)
    _sel = sorted([m for m in modes if 20.0 < m[0] < sr * 0.45],
                  key=lambda m: -(m[1] * min(1.0, (m[0] / _fc_crit) ** 2)))[:72]
    rep["structure"] = {
        "pane_m": [2.125, 5.600], "thickness_m": layers.GLASS_H,
        "modes_computed_below_1600hz": len(modes),
        "modes_rendered": len(_sel),
        "plate_fundamental_f11_hz": float(modes[0][0]),
        "critical_frequency_hz": _fc_crit,
        "rendered_mode_range_hz": [float(min(m[0] for m in _sel)),
                                   float(max(m[0] for m in _sel))],
        "eight_strongest_rendered_modes_hz": [float(m[0]) for m in _sel[:8]],
    }
    mark(f"glass pane: {len(modes)} modes, f11 = {modes[0][0]:.2f} Hz")

    # ---------------------------------------------------------- the assembly --
    asm_w, asm_info = layers.assembly(
        tw, {k: dict(explode["clusters"][k], **anim["clusters"][k])
             for k in anim["clusters"] if k in explode["clusters"]},
        sr, clock.launch_film_t)
    rep["assembly"] = asm_info
    mark(f"assembly: {asm_info['impacts']} part impacts")

    # -------------------------------------------------------------- breach ----
    imp_w, imp_info = layers.impact_event(
        tw, clock.glass_world_t, sr, shard_sum["contact_speed_ms"])
    rep["breach_impact"] = imp_info
    shard_groups = layers.render_shards(ev, tw, clock.glass_world_t, sr, groups=4)
    mark(f"breach: {shard_sum['contact_events']} shard contacts in "
         f"{shard_sum['settle_world_s']:.2f} s of world time")

    # ================================================ WARP TO THE FILM CLOCK ==
    def warp(x):
        return grid.to_film(x)

    eng_f = warp(eng_w)
    tyre_f = warp(tyre_w)
    struct_f = warp(struct_w)
    asm_f = warp(asm_w)
    imp_f = warp(imp_w)
    shard_f = [(warp(s), c) for s, c in shard_groups]
    del eng_w, tyre_w, struct_w, asm_w, imp_w, shard_groups
    mark("warped world -> film")

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
        """Measure the bus, trim it to its declared target, sum it, log both."""
        key = name if name in TARGET_LUFS_S else name.rstrip("0123456789")
        target = TARGET_LUFS_S[key]
        meas = dsp.max_short_term_lufs(stereo, sr)
        g_db = target - meas if np.isfinite(meas) else -200.0
        g_db = float(np.clip(g_db, -80.0, 80.0))
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
                         "raw_peak": float(np.abs(stereo).max()),
                         "hf_shelf_db_hz": list(shelf) if shelf else None}
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
    del eng_f, tyre_f, struct_f, asm_f, imp_f, shard_f

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

    # hit -14 LUFS, then limit, then re-check -- limiting REMOVES loudness, so
    # this iterates to convergence instead of assuming one pass lands.
    iters = []
    gr = 0.0
    for _ in range(8):
        L, _st_l, _ = dsp.loudness_lufs(master, sr)
        iters.append(float(L))
        if abs(L + 14.0) < 0.05:
            break
        master *= float(10.0 ** ((-14.0 - L) / 20.0))
        master, gr = dsp.soft_limit(master, ceiling=10.0 ** (-1.15 / 20.0), sr=sr)
    rep["limiter"] = {"ceiling_dbtp": -1.15, "max_gain_reduction_db": gr,
                      "loudness_iterations_lufs": iters}

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
    # the resampler can nudge a limited signal over the ceiling: re-limit at 48 k
    gr2 = gr3 = 0.0
    out48_iters = []
    for _ in range(8):
        L48, st48, st48t = dsp.loudness_lufs(out, SR_OUT)
        out48_iters.append(float(L48))
        if abs(L48 + 14.0) < 0.05:
            break
        out = out * 10.0 ** ((-14.0 - L48) / 20.0)
        out, gr3 = dsp.soft_limit(out, ceiling=10.0 ** (-1.10 / 20.0), sr=SR_OUT)
    L48, st48, st48t = dsp.loudness_lufs(out, SR_OUT)

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

    os.makedirs(os.path.dirname(out_wav), exist_ok=True)
    # write beside, compare, then either archive the old one or discover this
    # render reproduced it exactly -- see `_archive_if_superseded`
    sf.write(out_wav + ".new", out, SR_OUT, subtype="PCM_24")
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
    print(">> STAGE RESULT: AUDIO_MASTER_OK "
          f"{rep['master']['integrated_lufs']:.2f} LUFS "
          f"{rep['master']['true_peak_dbtp']:.2f} dBTP")


if __name__ == "__main__":
    main()
