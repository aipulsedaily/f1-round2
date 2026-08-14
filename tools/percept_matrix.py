#!/usr/bin/env python
"""THE CONTROL MATRIX. It runs FIRST, and nothing else runs if it is wrong.

    "If any control returns the wrong verdict, the run exits non-zero and the
     verdict on the real master is UNDEFINED and unreported."
        -- docs/audio-rebuild3/SPEC-ENGINE-AND-GATES.md, Tier 2

Three previous audio masters were rejected by the client and all eight gates
passed every time. The reason was never a bad threshold: it was that nobody
ever watched a gate FIRE. This file is the fix. It:

  0. audits every threshold's `source` and REFUSES to run if any of them is
     derived from the artefact under test;
  1. runs the permanent control corpus -- synthesised degenerates, the two
     anti-cheat controls, the two physics-true positives, and the DELIVERED
     REJECTED MASTER -- and checks each returns the verdict it is required to;
  2. runs the per-gate mutation controls: each gate's own defect deliberately
     re-injected into a signal that otherwise passes. A gate that does not move
     when its own defect is re-injected is proven blind and is DELETED, not
     tuned;
  3. only then adjudicates the master under test.

Usage:
    python -m tools.percept_matrix                     # corpus + mutations
    python -m tools.percept_matrix --wav audio/out/master.wav --adjudicate
    python -m tools.percept_matrix --only C4_delivered_master
"""

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                  # noqa: E402
from audio.controls import synth as C                           # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEET_PATH = os.path.join(ROOT, "docs", "beat_sheet.json")
SPEC_PATH = os.path.join(ROOT, "docs", "circuit_spec.json")


def _film_sheet():
    return json.load(open(SHEET_PATH))


_TEL_CACHE = {}


def _telemetry(kind):
    if kind is None:
        return None
    if kind == "constant_rpm":
        return P.constant_rpm_telemetry()
    if kind not in _TEL_CACHE:
        spec = json.load(open(SPEC_PATH))
        _TEL_CACHE[kind] = P.film_telemetry(spec, SHEET_PATH)
    return _TEL_CACHE[kind]


def stems_dir_for(wav):
    """THE STEM RUN THAT BELONGS TO `wav`: the `stems/` directory beside it.

    R2-4079 -- THIS RUNNER WAS JUDGING ANOTHER FILE'S STEMS. `_stems` read a
    HARD-CODED `audio/out/stems`, which is the stem run of the DELIVERED,
    REJECTED master. So every G-BALANCE number the matrix printed about any
    other master was a number about the artefact the client rejected: R2-4075
    caught it because they came back bit-identical to C4's (-3.30 dB, 1.000),
    and measured against its own stems the same build read +10.55 dB on beat 1.

    That is not a G-BALANCE bug. It is a RUNNER bug of exactly the family this
    rebuild exists to correct -- an instrument that silently reports on a file
    nobody asked about -- and it is the same shape as R2-4078's `--report`
    reading an input, and as `verify.py:816`'s bar read out of the artefact.
    The fix is that the stems FOLLOW the signal: a master's stems are the ones
    rendered beside it, they are named per signal rather than per process, and
    a signal with no stem run gets INAPPLICABLE, which is not PASS."""
    return os.path.join(os.path.dirname(os.path.abspath(wav)), "stems")


def _stems(kind, stems_dir):
    """Stems for G-BALANCE, from `stems_dir` and from nowhere else.

    Returns (stems | None, provenance dict). A missing directory is reported
    rather than silently substituted, and a directory whose own manifest names
    a DIFFERENT master is refused outright -- judging a master with another
    master's stems is the defect this signature exists to make impossible."""
    prov = {"telemetry_kind": kind, "stems_dir": stems_dir, "used": False}
    if kind != "film" or not stems_dir:
        prov["why"] = ("this signal declares no film telemetry, so it has no "
                       "stem run; G-BALANCE is INAPPLICABLE, which is not PASS")
        return None, prov
    if not os.path.isdir(stems_dir):
        prov["why"] = ("no stem run at %s -- G-BALANCE is INAPPLICABLE, which "
                       "is not PASS" % stems_dir)
        return None, prov
    man_path = os.path.join(stems_dir, "STEMS_OF.json")
    if os.path.isfile(man_path):
        man = json.load(open(man_path))
        prov["manifest"] = man
        prov["stems_of"] = man.get("master_wav")
    else:
        prov["manifest"] = None
        prov["stems_of"] = None
        prov["manifest_note"] = (
            "this stem run predates STEMS_OF.json and cannot name the master it "
            "was rendered with; its provenance is the directory it sits in")
    import soundfile as sf                                      # noqa: PLC0415
    out = {}
    for fn in sorted(os.listdir(stems_dir)):
        if not fn.endswith(".wav"):
            continue
        x, sr = sf.read(os.path.join(stems_dir, fn), always_2d=True)
        out[fn[:-4]] = (np.asarray(x, dtype=np.float32), int(sr))
    if not out:
        prov["why"] = "%s holds no .wav stems" % stems_dir
        return None, prov
    prov["used"] = True
    prov["n_stems"] = len(out)
    prov["stems"] = sorted(out)
    return out, prov


def _check_stem_provenance(prov, wav):
    """A stem run that NAMES a different master is a hard stop, not a warning."""
    if prov.get("stems_of") is None:
        return None
    if os.path.abspath(prov["stems_of"]) != os.path.abspath(wav):
        return ("the stem run at %s declares itself the stems of %s, not of %s"
                % (prov["stems_dir"], prov["stems_of"], wav))
    return None


def run_signal(x, sr, sheet, telemetry_kind, gates=None, stems_dir=None):
    """Signal gates only. G-CONSTRUCT is a property of the SOURCE TREE, not of
    any wav, so running it per-control would attach the repo's verdict to every
    signal in the corpus and tell us nothing about the signal. It is run once,
    on its own, below.

    `stems_dir` is the stem run belonging to THIS signal. There is no default
    and no fallback: the old `with_stems=True` handed every film-telemetry
    signal the same hard-coded directory."""
    sheet = sheet or _film_sheet()
    tel = _telemetry(telemetry_kind)
    stems, prov = _stems(telemetry_kind, stems_dir)
    gates = gates or P.QUALITY_GATES
    rep = P.run_suite(x, sr, sheet, stems=stems, telemetry=tel, gates=gates)
    rep["stem_provenance"] = prov
    return rep


# ==================================================== per-gate mutations ====
def _add_comb(x, sr, d1=681, d2=1084):
    """master.py:530-532, verbatim: sum the tail with a delayed copy of itself.
    Prints a fixed 141.0 / 88.6 Hz comb -- the largest cepstral feature in the
    whole first 30 seconds of the delivered master."""
    y = x.copy()
    y[:, 0] = x[:, 0] * 0.75 + np.roll(x[:, 0], d1) * 0.35
    y[:, 1] = np.roll(x[:, 1], d2) * 0.75 + x[:, 1] * 0.30
    return y


def _add_broadband(x, sr, gain=1.6):
    """layers.py:391, verbatim in spirit: a 900-6000 Hz white band at a gain
    higher than both tonal terms combined."""
    from scipy import signal as sg                              # noqa: PLC0415
    rng = np.random.default_rng(4041)
    sos = sg.butter(2, [900.0, 6000.0], btype="bandpass", fs=sr, output="sos")
    n = x.shape[0]
    r = np.sqrt(np.mean(x ** 2))
    y = x.copy()
    for c in range(x.shape[1]):
        nz = sg.sosfilt(sos, rng.standard_normal(n))
        y[:, c] += nz / np.sqrt(np.mean(nz ** 2)) * r * gain
    return y


def _resonator_bank(x, sr, q=80.0, modes=(187.0, 242.0, 332.0, 452.0, 614.0)):
    from scipy import signal as sg                              # noqa: PLC0415
    y = np.zeros_like(x)
    for c in range(x.shape[1]):
        acc = np.zeros(x.shape[0])
        for f in modes:
            w0 = 2 * np.pi * f / sr
            al = np.sin(w0) / (2 * q)
            b = np.array([al, 0.0, -al])
            a = np.array([1.0 + al, -2.0 * np.cos(w0), 1.0 - al])
            acc += sg.lfilter(b / a[0], a / a[0], x[:, c])
        y[:, c] = acc / max(np.sqrt(np.mean(acc ** 2)), 1e-20) * \
            np.sqrt(np.mean(x[:, c] ** 2))
    return y


def _fixed_resonators(x, sr):
    """G-ROOM(b)'s defect: whatever you strike, the room replies at the same
    pitches. Full replacement, no dry blend -- an earlier version kept 25 % dry
    and the gate did not move, correctly: filtering a periodic source through a
    resonator leaves a periodic source, and the MUTATION was wrong, not the
    gate."""
    return _resonator_bank(x, sr)


def _noise_through_tubes(x, sr):
    """G-HNR's defect, at the level of the whole beat: the tonal voice replaced
    by NOISE through the same fixed high-Q pipes. Zero line spectrum, zero
    periodicity, narrow peaks everywhere -- the signal the shipped harmonic gate
    scored +4.04 dB and called clean."""
    rng = np.random.default_rng(1917)
    nz = np.stack([rng.standard_normal(x.shape[0]) for _ in range(x.shape[1])],
                  axis=1)
    for c in range(x.shape[1]):
        nz[:, c] *= np.sqrt(np.mean(x[:, c] ** 2))
    return _resonator_bank(nz, sr)


def _fdn_comb_tail(x, sr):
    """G-ROOM(a)'s defect: an 8-tap FDN with no diffusion stages, whose fixed
    lines are harmonics of a delay length."""
    y = np.zeros_like(x)
    for c in range(x.shape[1]):
        t = C.comb_tail(x[:, c], sr, rt60_s=2.4)
        y[:, c] = x[:, c] * 0.35 + t / max(np.sqrt(np.mean(t ** 2)), 1e-12) * \
            np.sqrt(np.mean(x[:, c] ** 2))
    return y


def _long_tail(x, sr):
    """G-RING's defect: a tail at RT60 4.5 s in a room whose Sabine RT60 is
    2.4 s. Built with velvet noise so that ONLY the decay time is wrong and the
    comb structure is not -- a mutation that injects two defects at once cannot
    show which gate saw which."""
    y = np.zeros_like(x)
    for c in range(x.shape[1]):
        t = C.diffuse_tail(x[:, c], sr, rt60_s=4.5, seed=31 + c)
        y[:, c] = x[:, c] * 0.30 + t / max(np.sqrt(np.mean(t ** 2)), 1e-12) * \
            np.sqrt(np.mean(x[:, c] ** 2))
    return y


def _exact_grid(x, sr):
    """Put the gestures back on an exact 1.375 s grid: 33 frames at 24 fps,
    the delivered master's own metronome."""
    return C.jittered_identical_gestures(sr, x.shape[0] / sr, 1.375, 0.0, 12)


def _identical_gestures(x, sr):
    """Same gesture every time, jittered grid -- the C6 defect, re-injected."""
    return C.jittered_identical_gestures(sr, x.shape[0] / sr, 1.375, 0.15, 12)


def _tile(x, sr, block_s=2.0):
    n = int(block_s * sr)
    reps = int(np.ceil(x.shape[0] / n))
    return np.tile(x[:n], (reps, 1))[:x.shape[0]]


def _detune_order(x, sr):
    """A comb that does NOT track the telemetry: the constant-rpm positive
    control resampled so its lines sit 9 % off the rpm the telemetry declares."""
    from scipy import signal as sg                              # noqa: PLC0415
    n = x.shape[0]
    y = np.stack([sg.resample_poly(x[:, c], 100, 109) for c in range(x.shape[1])],
                 axis=1)
    out = np.zeros_like(x)
    m = min(n, y.shape[0])
    out[:m] = y[:m]
    return out


def _held_chord(x, sr):
    """G-SUSTAIN's defect, injected as the cheapest possible version of it:
    THREE HELD NOTES over the positive control, at the level a pad sits at.

    Not a musical quotation and not a scale -- three arbitrary frequencies in
    an arbitrary ratio (1 : 1.331 : 1.587, none of them a small-integer
    interval), because the property being gated is HOLDING, not harmony. If
    the gate only fired on consonant intervals it would be a taste instrument;
    it fires on three things that do not move, which is what a machine never
    does."""
    n = x.shape[0]
    t = np.arange(n) / sr
    r = np.sqrt(np.mean(x ** 2))
    y = x.copy()
    for c in range(x.shape[1]):
        pad = np.zeros(n)
        for f, a in ((233.0, 1.0), (310.1, 0.8), (369.7, 0.7)):
            for k, ak in ((1, 1.0), (2, 0.45), (3, 0.25), (4, 0.12)):
                pad += a * ak * np.sin(2 * np.pi * f * k * t + 0.7 * c + 0.3 * k)
        y[:, c] += pad / np.sqrt(np.mean(pad ** 2)) * r * 0.55
    return y


def _octave_matched(x, sr):
    """G-EVENT's defect, and the sharpest statement of why it exists: the
    control's OWN octave-band spectrum, re-synthesised as stationary noise.

    Every spectral statistic in the suite is approximately preserved by this
    mutation -- same energy in every octave, same tilt, same bandwidth -- and
    every event in the beat is gone. If the suite cannot fail this, it cannot
    fail a hair dryer, which is what it was asked to do three rejections ago."""
    y = np.zeros_like(x)
    for c in range(x.shape[1]):
        n = C.octave_matched_noise(x[:, c:c + 1], sr, seed=1401 + c)
        n = np.asarray(n).reshape(-1)[:x.shape[0]]
        y[:len(n), c] = n / max(np.sqrt(np.mean(n ** 2)), 1e-20) * \
            np.sqrt(np.mean(x[:, c] ** 2))
    return y


MUTATIONS = [
    # (label, base control, mutation, gate that MUST fire)
    #
    # R2-4081 MOVED TWO BASES AND ADDED TWO ROWS. M-FLAT and M-HNR now run on
    # the ENGINE control, because G-FLAT and G-HNR are engine-beat instruments
    # from this pass on and a mutation aimed at a beat the gate no longer judges
    # would report the gate blind when it is merely out of scope. Everything
    # aimed at beat 1 now runs on C9, the percussive positive, because a
    # mutation has to be injected into something that PASSES before the
    # injection or it proves nothing.
    ("M-FLAT  broadband bed over the constant-rpm unit",
     "C8_constant_rpm_pu", _add_broadband, "G-FLAT"),
    ("M-HNR   noise through fixed high-Q pipes at beat level",
     "C8_constant_rpm_pu", _noise_through_tubes, "G-HNR"),
    ("M-SUST  three held notes over the assembly cell",
     "C9_assembly_cell", _held_chord, "G-SUSTAIN"),
    ("M-EVENT the assembly cell's own spectrum, stationary",
     "C9_assembly_cell", _octave_matched, "G-EVENT"),
    ("M-NOVEL 2 s block tiled over the assembly cell",
     "C9_assembly_cell", _tile, "G-NOVEL"),
    ("M-MOD   gestures back on an exact 1.375 s grid",
     "C9_assembly_cell", _exact_grid, "G-MOD"),
    ("M-GEST  one gesture repeated, jittered grid",
     "C9_assembly_cell", _identical_gestures, "G-GESTURE"),
    ("M-ROOMc master.py:530-532 self-delay comb re-injected",
     "C9_assembly_cell", _add_comb, "G-ROOM"),
    ("M-ROOMb fixed inharmonic resonator bank, no dry blend",
     "C9_assembly_cell", _fixed_resonators, "G-ROOM"),
    ("M-ROOMa 8-tap FDN, no diffusion: lines are delay harmonics",
     "C9_assembly_cell", _fdn_comb_tail, "G-ROOM"),
    # M-RING STAYS ON C8b. G-RING needs inter-event gaps to backward-integrate
    # a decay out of, and C9 is a DENSE beat by design -- 580 contacts over
    # 33 s -- so G-RING is INAPPLICABLE on it and a mutation injected there
    # reports the gate blind when it is only unable to look. The carrier for a
    # mutation has to be a signal the gate can measure; C8b's sparse clicks
    # over a bed can be, whatever else is wrong with C8b.
    ("M-RING  tail at RT60 4.5 s in a 2.4 s Sabine room",
     "C8b_tonal_showroom_drone", _long_tail, "G-RING"),
    ("M-ORDER comb detuned 9 % off the telemetry rpm",
     "C8_constant_rpm_pu", _detune_order, "G-ORDER"),
]


def _mutation_balance():
    """G-BALANCE's defect, re-injected at stem level. Baseline: the protagonist
    carries the beat and the near-white stem is 20 dB under it. Mutation: the
    near-white stem comes up 26 dB, which is the delivered master's beat 1
    (92.6 % of power in two stems measuring 82-85 % of white). G-BALANCE must
    pass the first and fail the second, or it is not measuring balance."""
    sr = C.SR
    beat = C.physical_showroom_beat(sr)[:, 0]
    n = beat.shape[0]
    rng = np.random.default_rng(4242)
    from scipy import signal as sg                              # noqa: PLC0415
    sos = sg.butter(2, [900.0, 6000.0], btype="bandpass", fs=sr, output="sos")
    nz = sg.sosfilt(sos, rng.standard_normal(n))
    nz = nz / np.sqrt(np.mean(nz ** 2)) * np.sqrt(np.mean(beat ** 2))
    beats = [P.Beat("1_assembly", 0.0, n / sr)]
    out = {}
    for label, g in (("baseline (near-white stem 20 dB down)", 10 ** (-20 / 20)),
                     ("MUTATION (near-white stem 6 dB up)", 10 ** (6 / 20))):
        stems = {"assembly": (beat.astype(np.float32), sr),
                 "wind": ((nz * g).astype(np.float32), sr)}
        out[label] = P.g_balance(stems, sr, beats)
    return out


def _mutation_construct(tmpdir):
    """G-CONSTRUCT's defect, as three source fixtures. The first is
    layers.py:391 verbatim -- band-limited, yes, but with no derivation for
    900, 6000 or 0.6, and weighted higher than both tonal terms combined."""
    cases = {
        "bp_no_derivation":
            "import dsp\ndef srv(n, sr, seed):\n"
            "    return dsp.bp(dsp.white(n, seed + 1), 900.0, 6000.0, sr, 2) * 0.6\n",
        "raw_white_to_bus":
            "import dsp\ndef bed(n, seed):\n    return dsp.white(n, seed) * 0.5\n",
        "rng_click":
            "import numpy as np\ndef click(L, rng, tt):\n"
            "    return rng.standard_normal(L) * np.exp(-tt / 0.004)\n",
    }
    res = {}
    for name, src in cases.items():
        d = os.path.join(tmpdir, f"_gc_{name}")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "bad.py"), "w") as fh:
            fh.write(src)
        r = P.g_construct(d)
        res[name] = {"hits": r["n_hits"], "verdict": r["verdict"],
                     "what": [h["what"] for h in r["hits"]]}
        os.remove(os.path.join(d, "bad.py"))
        os.rmdir(d)
    return res


def run_mutations(verbose=True):
    rows = []
    cache = {}
    for label, base, fn, gate in MUTATIONS:
        if base not in cache:
            cache[base] = C.build(base)
        b = cache[base]
        t0 = time.time()
        x = fn(b["x"], b["sr"])
        rep = run_signal(x, b["sr"], b["sheet"], b["telemetry_kind"], gates=(gate,))
        fired = rep["quality_verdicts"].get(gate) == P.FAIL
        rows.append({"mutation": label, "base": base, "gate": gate,
                     "verdict": rep["quality_verdicts"].get(gate),
                     "FIRED": bool(fired),
                     "failures": rep["gates"][gate]["failures"][:3],
                     "seconds": round(time.time() - t0, 1)})
        if verbose:
            print(f"   {'FIRED ' if fired else 'BLIND '} {gate:<10s} {label}")
            for f in rows[-1]["failures"]:
                print(f"            {f}")

    bal = _mutation_balance()
    keys = list(bal)
    fired = (bal[keys[0]]["verdict"] == P.PASS
             and bal[keys[1]]["verdict"] == P.FAIL)
    rows.append({"mutation": "M-BAL   near-white stem raised 26 dB",
                 "base": "synthetic stem pair", "gate": "G-BALANCE",
                 "verdict": bal[keys[1]]["verdict"], "FIRED": bool(fired),
                 "baseline_verdict": bal[keys[0]]["verdict"],
                 "failures": bal[keys[1]]["failures"][:3]})
    if verbose:
        print(f"   {'FIRED ' if fired else 'BLIND '} G-BALANCE  M-BAL   "
              f"near-white stem raised 26 dB (baseline "
              f"{bal[keys[0]]['verdict']})")
        for f in rows[-1]["failures"]:
            print(f"            {f}")

    gc = _mutation_construct(os.path.join(ROOT, "tmp"))
    fired = all(v["verdict"] == P.FAIL for v in gc.values())
    rows.append({"mutation": "M-CONS  three source fixtures that break the law",
                 "base": "AST fixtures", "gate": "G-CONSTRUCT",
                 "verdict": "FAIL" if fired else "PASS", "FIRED": bool(fired),
                 "cases": gc, "failures": []})
    if verbose:
        print(f"   {'FIRED ' if fired else 'BLIND '} G-CONSTRUCT M-CONS  "
              f"three source fixtures that break the law")
        for k, v in gc.items():
            print(f"            {k}: {v['hits']} hit(s) -> {v['verdict']}")
    return rows


# ============================================================== the matrix ==
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav", default=os.path.join(ROOT, "audio", "out", "master.wav"))
    ap.add_argument("--adjudicate", action="store_true",
                    help="after the matrix passes, judge --wav")
    ap.add_argument("--only", default=None, help="run one control by name")
    ap.add_argument("--stems", default=None,
                    help="the stem run belonging to --wav. Defaults to the "
                         "`stems/` directory BESIDE --wav; there is no global "
                         "fallback, because judging one master with another "
                         "master's stems is the R2-4075 defect.")
    ap.add_argument("--skip-mutations", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "audio", "out",
                                                  "percept_matrix.json"))
    a = ap.parse_args()

    report = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "spec": "docs/audio-rebuild3/SPEC-ENGINE-AND-GATES.md"}

    # -- 0. THRESHOLD PROVENANCE ------------------------------------------
    ta = P.audit_thresholds()
    report["threshold_audit"] = ta
    report["thresholds"] = P.thresholds_report()
    print(f">> threshold provenance: {ta['n_thresholds']} thresholds, "
          f"{len(ta['violations'])} violations, PASS={ta['PASS']}")
    for s in P.SOURCES_ALLOWED:
        print(f"   {s:<16s} {len(ta['by_source'][s]):2d}")
    for v in ta["violations"]:
        print(f"   VIOLATION {v['key']}: {v['why']}")
    if not ta["PASS"]:
        print(">> STAGE RESULT: PERCEPT_THRESHOLDS_INVALID")
        return 2

    # -- 1. THE CONTROL CORPUS --------------------------------------------
    names = [a.only] if a.only else list(C.CONTROLS)
    rows, wrong = [], []
    for name in names:
        t0 = time.time()
        b = C.build(name)
        rep = run_signal(b["x"], b["sr"], b["sheet"], b["telemetry_kind"],
                         stems_dir=b["stems_dir"])
        failed_all = P.failing_gates(rep)
        # R2-4081: DECLARED-OPEN GATES ARE REPORTED AND NOT COUNTED. The
        # declaration lives in `audio.controls.synth.OPEN`, it is admissible
        # only with a measured null for the limb it names, and it is printed on
        # every run so it cannot become invisible.
        openg = b.get("open") or {}
        failed = [g for g in failed_all if g not in openg]
        got = ("FAIL" if any(rep["quality_verdicts"].get(g) == P.FAIL
                             for g in rep["quality_verdicts"] if g not in openg)
               or any(rep["provenance_verdicts"].get(g) == P.FAIL
                      for g in rep["provenance_verdicts"] if g not in openg)
               else ("PASS" if rep["no_fail"] or any(
                   v == P.PASS for v in rep["quality_verdicts"].values())
                     else "INAPPLICABLE"))
        ok = (got == b["required_verdict"])
        missing_trips = [g for g in b["must_trip"] if g not in failed]
        wrong_passes = [g for g in b["must_pass"]
                        if rep["quality_verdicts"].get(g) != P.PASS]
        if b["required_verdict"] == "FAIL" and missing_trips:
            ok = False
        if wrong_passes:
            ok = False
        rows.append({
            "control": name, "what": b["what"],
            "required": b["required_verdict"], "got": got,
            "failing_gates": failed,
            "declared_open": {g: openg[g] for g in openg},
            "open_and_failing": [g for g in failed_all if g in openg],
            "must_trip": list(b["must_trip"]), "missing_trips": missing_trips,
            "must_pass": list(b["must_pass"]), "wrong_passes": wrong_passes,
            "inapplicable": rep["inapplicable_gates"],
            "stem_provenance": rep["stem_provenance"],
            "CORRECT": bool(ok), "seconds": round(time.time() - t0, 1),
            "verdicts": rep["quality_verdicts"],
            "detail": {g: rep["gates"][g]["failures"][:4] for g in failed},
        })
        if not ok:
            wrong.append(name)
        mark = "ok  " if ok else "WRONG"
        print(f">> {mark} {name:<34s} required {b['required_verdict']:<4s} "
              f"got {got:<12s} fails: {','.join(failed) or '-'}")
        if missing_trips:
            print(f"        MUST TRIP BUT DID NOT: {missing_trips}")
        if wrong_passes:
            print(f"        MUST PASS BUT DID NOT: {wrong_passes}")
        for g in rows[-1]["open_and_failing"]:
            print(f"        OPEN, NOT COUNTED -- {g}: {openg[g][:120]}...")
            for f in rep["gates"][g]["failures"][:2]:
                print(f"            {f}")
        for g in failed[:6]:
            for f in rep["gates"][g]["failures"][:2]:
                print(f"        {g}: {f}")
    report["corpus"] = rows
    report["corpus_correct"] = len(wrong) == 0

    # -- 2. PER-GATE MUTATION CONTROLS ------------------------------------
    if not a.skip_mutations:
        print(">> per-gate mutation controls (a gate that does not move when "
              "its own defect is re-injected is blind):")
        muts = run_mutations()
        report["mutations"] = muts
        blind = [m["gate"] for m in muts if not m["FIRED"]]
        report["blind_gates"] = sorted(set(blind))
        report["mutations_correct"] = len(blind) == 0
    else:
        report["mutations_correct"] = None

    # -- 2b. G-CONSTRUCT ON THE REAL TREE, ONCE ---------------------------
    gcon = P.g_construct()
    report["g_construct"] = gcon
    print(f">> G-CONSTRUCT on {len(gcon['scanned'])} render-path modules: "
          f"{gcon['n_hits']} violations, verdict {gcon['verdict']}")
    for h in gcon["hits"][:12]:
        print(f"   {h['file']}:{h['line']} {h['what']}")
        if h.get("src"):
            print(f"      {h['src']}")

    matrix_ok = report["corpus_correct"] and (report["mutations_correct"] is not False)

    # -- 3. ONLY NOW, THE MASTER UNDER TEST --------------------------------
    if a.adjudicate:
        if not matrix_ok:
            report["adjudication"] = {
                "verdict": "UNDEFINED",
                "why": ("the control matrix did not return the verdicts it is "
                        "required to, so the verdict on the master under test "
                        "is UNDEFINED and is not reported")}
            print(">> adjudication: UNDEFINED -- the matrix is wrong, so the "
                  "master is unreported")
        else:
            import soundfile as sf                             # noqa: PLC0415
            x, sr = sf.read(a.wav, always_2d=True)
            sdir = a.stems or stems_dir_for(a.wav)
            rep = run_signal(x, sr, None, "film", stems_dir=sdir)
            prov = rep["stem_provenance"]
            mismatch = _check_stem_provenance(prov, a.wav)
            print(f">> stems for adjudication: {sdir} "
                  f"({'used, ' + str(prov.get('n_stems')) + ' stems' if prov['used'] else 'NOT USED'})")
            if not prov["used"]:
                print(f"   {prov.get('why')}")
            if prov.get("manifest_note"):
                print(f"   {prov['manifest_note']}")
            if mismatch:
                # Refusing is the point. The whole reason this argument exists
                # is that the runner used to answer about a file nobody asked
                # about, and it did it silently.
                report["adjudication"] = {"wav": a.wav, "verdict": "UNDEFINED",
                                          "stem_provenance": prov,
                                          "why": mismatch}
                print(f">> adjudication: UNDEFINED -- {mismatch}")
                os.makedirs(os.path.dirname(a.out), exist_ok=True)
                with open(a.out, "w") as fh:
                    json.dump(report, fh, indent=1, default=float)
                print(">> STAGE RESULT: PERCEPT_MATRIX_STEM_PROVENANCE_FAIL")
                return 2
            report["adjudication"] = {
                "wav": a.wav, "stem_provenance": prov,
                "quality_verdicts": rep["quality_verdicts"],
                "provenance_verdicts": rep["provenance_verdicts"],
                "failing_gates": P.failing_gates(rep),
                "verdict": "PASS" if rep["quality_pass"] else "FAIL",
                "report": rep}
            print(f">> adjudication {a.wav}: "
                  f"{report['adjudication']['verdict']} "
                  f"fails {report['adjudication']['failing_gates']}")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(report, fh, indent=1, default=float)
    print(f">> wrote {a.out}")
    print(">> STAGE RESULT:", "PERCEPT_MATRIX_OK" if matrix_ok
          else "PERCEPT_MATRIX_FAIL")
    return 0 if matrix_ok else 1


if __name__ == "__main__":
    sys.exit(main())
