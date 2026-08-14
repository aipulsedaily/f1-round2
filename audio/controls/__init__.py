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
    C8b ANTI-CHEAT, and a POSITIVE UNTIL R2-4081 MEASURED IT: the cheapest
        signal that clears the old beat-1 tonality bars. 98.3 % of its power
        is a servo comb, it holds one pitch for 8.49 s, and its 20 ms level
        varies by 0.64 dB inside a 2 s window -- white noise varies by 0.65.
        It cleared the +8 dB HNR bar by 24 dB and was the evidence that bar
        was reachable; the fourth master built toward that bar was rejected
        as "a shitty musical". The SIGNAL is untouched: what R2-4081 changed
        is the claim made about it, and it changed on numbers.

  POSITIVE CONTROLS, which must PASS.
    C8  a constant-rpm power unit built from first principles
    C9  an assembly cell on the film's own picture-locked contact schedule:
        ~780 Hertzian contacts, a geometry per part, thin-ring and plate
        modes, jet-noise exhausts with a Strouhal peak, servo moves that
        GLIDE, joint damping that puts T60 in tens of milliseconds. It is the
        percussive, inharmonic, transient-dense, UNPITCHED half of the corpus,
        and until R2-4081 it did not exist -- which is why every beat-1 bar
        was anchored on a drone.

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
    assembly_cell, ring_modes, jet_exhaust, servo_move, nut_runner,
    conveyor_bed,
)
