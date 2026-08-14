"""THE PERMANENT CONTROL CORPUS.

A gate suite that cannot fail these is not finished. Every signal here is
SYNTHESISED from code -- there are no recordings, no impulse responses and no
sample packs anywhere in this package, and there never will be.

The corpus has two halves and both are load-bearing:

  NEGATIVE CONTROLS, which must FAIL.
    C1  octave-matched filtered noise -- the literal hair dryer
    C2  a 2 s block tiled to length -- the literal tape loop
    C3  noise through high-Q inharmonic pipes -- the client's exact words,
        "a wind blower with someone banging on tubes", built as a signal
    C4  audio/out/master.wav, THE DELIVERED REJECTED MASTER, retained
        permanently. A gate that passes the artefact the client rejected is
        broken by definition, and C4 is what makes that statement executable.
    C5  the delivered master with beat 1 replaced by a tiled block -- the file
        that passes all eight OLD gates with ALL_PASS=True and exit 0
    C6  ANTI-CHEAT: a jittered metronome of identical gestures. Must fail
        G-GESTURE and PASS G-MOD, so that "just add jitter" cannot buy a pass.
    C7  ANTI-CHEAT: the delivered master plus a broad spectral tilt. Must fail
        G-FLAT, proving the per-band construction is tilt-immune -- the
        whole-band SFM reads a reassuring 0.0142 on the delivered master and
        that is what let it ship.

  POSITIVE CONTROLS, which must PASS.
    C8  a constant-rpm power unit built from first principles
    C8b a physically-constructed showroom beat: non-uniform arrivals, plate
        modes per cluster, distinct gestures, a diffuse tail

Without the positive half a suite that failed everything would look finished.
With it, every bar in `percept.py` is bracketed on both sides by a signal whose
truth is known by construction.

`audio/controls/` is EXCLUDED from G-CONSTRUCT's noise-source law, because
synthesising a hair dryer is this package's job. The exclusion is checked, not
asserted: `percept.g_construct` fails if any render-path module imports it.
"""

from .synth import (                                             # noqa: F401
    CONTROLS, SR, FILM_S, build, build_all, cache_path,
    octave_matched_noise, tiled_loop, blower_plus_tubes,
    jittered_identical_gestures, spectral_tilt, constant_rpm_pu,
    physical_showroom_beat, diffuse_tail, comb_tail, distinct_gestures,
)
