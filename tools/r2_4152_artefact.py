#!/usr/bin/env python
"""R2-4152 -- THE ARTEFACT TEST. Judge the film, not the gate.

    .venv/bin/python -m tools.r2_4152_artefact NEWTAG [OLDTAG]

R2-4151 improved the adjudication -- three failure lines gone, none added, AMI
0.1409 -> 0.1710 -- and withheld anyway, because the ablation said three
quarters of the gain was SUBTRACTION: the delivered breach was 3.6 dB darker at
4-8 kHz, the glass 6.9 dB quieter, and the engine 79 % of the beat. That was the
right call and this file exists so the same test is applied to this pass with
the same numbers in the same units.

Every row is measured on the DELIVERED masters and their own stem runs, never on
a dry layer -- a layer bench has now mis-sized a mix effect in two consecutive
passes (R2-4150(10)#1 and R2-4151(10)#1), in opposite directions.
"""

import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal as _sig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from audio import dsp, percept as P                              # noqa: E402

BREACH = (36.0, 44.0)
BEAT1 = (0.0, 33.0)


def ami(x, sr):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    return P.articulation_modulation_index(x, sr).get("ami", float("nan"))


def band_db(x, sr, lo, hi):
    m = np.asarray(x, dtype=np.float64)
    if m.ndim > 1:
        m = m.mean(axis=1)
    f, pxx = _sig.welch(m, sr, nperseg=8192)
    return 10.0 * np.log10(max(float(pxx[(f >= lo) & (f < hi)].sum()), 1e-30))


def stems(tag, t0, t1):
    d = os.path.join(ROOT, "audio", "out", tag, "stems")
    names = sorted(n[:-4] for n in os.listdir(d) if n.endswith(".wav"))
    sr = sf.info(os.path.join(d, names[0] + ".wav")).samplerate
    a, b = int(t0 * sr), int(t1 * sr)
    out = {}
    for nm in names:
        x, _ = sf.read(os.path.join(d, nm + ".wav"), start=a, stop=b,
                       always_2d=True)
        out[nm] = np.asarray(x, dtype=np.float64)
    return out, sr


def master(tag):
    for nm in os.listdir(os.path.join(ROOT, "audio", "out", tag)):
        if nm.startswith("master_") and nm.endswith(".wav"):
            return os.path.join(ROOT, "audio", "out", tag, nm)
    raise SystemExit("no master in %s" % tag)


def main():
    new = sys.argv[1] if len(sys.argv) > 1 else "r2_4152"
    old = sys.argv[2] if len(sys.argv) > 2 else "r2_4147"
    print("THE ARTEFACT TEST -- %s against the SHIPPED %s\n" % (new, old))

    # --- 1. the breach, on the stems --------------------------------------
    print("1. THE BREACH (36-44 s), ON THE DELIVERED STEMS.\n")
    print("   %-34s %12s %12s %10s" % ("", old, new, "delta"))
    rows = []
    S = {t: stems(t, *BREACH) for t in (old, new)}
    for t in (old, new):
        s, sr = S[t]
        tot = sum(float((v ** 2).sum()) for v in s.values())
        m = sum(s.values())
        rows.append({
            "beat AMI": ami(m, sr),
            "beat RMS dBFS": 10 * np.log10(float((m.mean(axis=1) ** 2).mean())),
            "beat 4-8 kHz dB": band_db(m, sr, 4000, 8000),
            "beat 8-16 kHz dB": band_db(m, sr, 8000, 16000),
            "shards LUFS-S": dsp.max_short_term_lufs(s["shards"], sr),
            "debris LUFS-S": dsp.max_short_term_lufs(s["debris"], sr),
            "engine LUFS-S": dsp.max_short_term_lufs(s["engine"], sr),
            "engine share %": 100.0 * float((s["engine"] ** 2).sum()) / tot,
            "shards share %": 100.0 * float((s["shards"] ** 2).sum()) / tot,
            "debris share %": 100.0 * float((s["debris"] ** 2).sum()) / tot,
            "impact LUFS-S": dsp.max_short_term_lufs(s["impact"], sr),
        })
    for k in rows[0]:
        print("   %-34s %12.4f %12.4f %+10.4f"
              % (k, rows[0][k], rows[1][k], rows[1][k] - rows[0][k]))
    print()
    print("   R2-4151's THREE INDICTMENTS, RESTATED IN THE SAME UNITS:")
    print("     the breach %+.2f dB at 4-8 kHz against the master it replaces"
          % (rows[1]["beat 4-8 kHz dB"] - rows[0]["beat 4-8 kHz dB"]))
    print("     the glass  %+.2f dB (shards delivered LUFS-S)"
          % (rows[1]["shards LUFS-S"] - rows[0]["shards LUFS-S"]))
    print("     the engine %.1f %% of the beat, was %.1f %%"
          % (rows[1]["engine share %"], rows[0]["engine share %"]))
    print("   R2-4151 read -3.60 dB, -6.88 dB and 79 %, and was withheld on it.\n")

    # --- 2. beat 1 must not have moved ------------------------------------
    print("2. BEAT 1, WHICH IS PICTURE-LOCKED.\n")
    xo, sro = sf.read(master(old), always_2d=True)
    xn, srn = sf.read(master(new), always_2d=True)
    n = min(int(33.0 * sro), int(33.0 * srn))
    a, b = xo[:n].astype(np.float64), xn[:n].astype(np.float64)
    # the film's own programme gain is allowed to differ; anything else is not
    g = float((a * b).sum() / max(float((a * a).sum()), 1e-30))
    res = b - a * g
    print("   best-fit pure gain NEW/OLD over 0-33 s   %+.4f dB" % (20 * np.log10(g)))
    print("   residual after removing it               %+.2f dB below the signal"
          % (10 * np.log10(max(float((res ** 2).sum()), 1e-30)
                           / max(float((b ** 2).sum()), 1e-30))))
    print("   IF THAT RESIDUAL IS NOT FAR DOWN, BEAT 1 MOVED AND THE PASS IS OVER.\n")

    # --- 3. the whole film -------------------------------------------------
    print("3. THE WHOLE FILM.\n")
    for tag, x, sr in ((old, xo, sro), (new, xn, srn)):
        L, _, _ = dsp.loudness_lufs(x.astype(np.float64), sr)
        print("   %-10s %+8.2f LUFS-I  %+7.2f dBTP  4-8 kHz %+7.2f dB"
              % (tag, L, dsp.true_peak_dbtp(x, sr), band_db(x, sr, 4000, 8000)))


if __name__ == "__main__":
    main()
