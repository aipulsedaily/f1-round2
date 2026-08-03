"""CIRCUIT VITRINE -- AUDIO. One continuous synthesised master for the single take.

Nothing in this package is sampled, recorded, downloaded or model-generated.
Every oscillator, noise band, filter, resonance and impact is built from numbers
in these files. `verify.py --` proves it by AST-scanning the package for any call
that could read a recorded sound, and tests that scan against three artefacts
constructed to be caught.

    .venv/bin/python -m audio.master     -> out/master.wav + out/master_report.json
    .venv/bin/python -m audio.verify     -> out/verify_report.json + spectrograms

    clock.py    film time <-> world time at 96 kHz. IMPORTS anim/filmtime.py.
    scene.py    the car (telemetry), the listener (camera rig), the surface.
    dsp.py      phase integration, noise, ISO 9613-1 air absorption, FDN reverb,
                BS.1770-4 loudness, true-peak limiter.
    engine.py   the 1.6 L V6 turbo hybrid, built as a mechanism.
    layers.py   tyres, wind, showroom acoustic, ambience, crowd, structure,
                assembly, the breach.
    spatial.py  retarded-time propagation to two ears. No Doppler formula.
    master.py   the mix.
    verify.py   the gates, each with a positive control.

Every non-obvious constant is derived in the module docstring where it lives,
and every decision that was made and then reversed by a measurement is written
down next to the measurement that reversed it.
"""
