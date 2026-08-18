"""CHECK 3 OF THE MASTER'S THREE FRAME CHECKS: DECODE AND GEOMETRY.

    .venv/bin/python tools/r23841_verify_frames.py \
        --dir ~/vast-render/out3/seq/master4k \
        --dir ~/vast-render/out4/seq/master4k \
        --dir ~/vast-render/out5/seq/master4k \
        --first 1 --last 2978 --res 3840 2160 \
        --json work/r23841/decode.json

WHY THIS EXISTS SEPARATELY FROM `fleetctl verify`
-------------------------------------------------
`fleetctl verify` already does two of the three checks the master needs, and
does them well: it re-hashes every PNG on disk and compares each hash against
the sha256 the BROKER recorded independently at fetch time, and it reports
coverage (present / missing / duplicated / out-of-range) per broker.

What it does not do is DECODE. Its `width`, `height` and `blank` columns are
read out of each broker's own SQLite — they are the broker's measurement,
recorded by the same process that fetched the frame. So:

  * a PNG that is structurally intact enough to hash but truncated in its IDAT
    stream passes, because nothing ever inflates it;
  * a resolution check sourced from the record cannot catch a record that is
    wrong about the file;
  * and the blank verdict is the broker's own verdict, re-read. Re-reading a
    verdict is not a second opinion.

This tool therefore decodes every frame from scratch, measures the pixels it
gets, and reaches its own verdict. It deliberately does NOT import
`broker.imgstat`: running the same classifier over the same frames a second
time would agree with itself by construction and prove nothing.

THE THRESHOLDS, AND WHERE THEY COME FROM
----------------------------------------
`~/vast-render/broker/config.py` records the measured population this farm has
actually returned, in normalised 0-1 luminance:

    sd 0.00000  mean 0.00000    a black 4K frame                    <- wrong
    sd 0.00794  mean 0.77401    a flat grey 4K frame, 14 levels     <- wrong
    sd 0.03494  mean 0.30798    the FLATTEST LEGITIMATE frame, 212 levels

So the two populations are separated by a factor of 4.4 in standard deviation,
and any threshold in between splits them. This tool uses **sd < 0.01**, which
is 3.5x below the flattest real frame ever returned here and just above the
flat-grey failure — the same place `config.py` puts it, derived from the same
measurements rather than copied from its code.

A frame is reported FLAT if sd < 0.01, and additionally BLACK if its mean is
also under 0.02 (~5 grey levels, below which nobody can see anything).

`--min-levels` counts distinct 8-bit levels present in the luminance. The flat
grey 4K frame had 14; the flattest legitimate frame had 212. Default 32 is well
clear of both.

WHAT COUNTS AS A FAILURE
------------------------
  * a file that will not decode, or decodes short
  * any frame whose decoded size is not exactly the expected resolution
  * more than one distinct resolution across the delivered set
  * any FLAT or BLACK frame
  * a gap or a duplicate in the frame numbering

Exit status is 1 on any of those and 0 only when every frame passed, and the
verdict is printed as a `>> STAGE RESULT:` line because on this project a log
that ends is not a stage that ended.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageFile

# A truncated PNG must RAISE, not be silently padded with grey. Pillow's
# default for this is forgiving and that forgiveness is exactly the failure
# this check exists to catch.
ImageFile.LOAD_TRUNCATED_IMAGES = False

FRAME_RE = re.compile(r"_(\d{6})\.png$")

# Rec.709 luma. The frames are SDR Rec.709 8-bit RGB.
LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float64)


def measure(args):
    """Decode ONE frame and measure it. Runs in a worker process."""
    path, want_w, want_h = args
    out = {"path": path, "err": None}
    try:
        with Image.open(path) as im:
            im.load()                      # force the full IDAT inflate
            w, h = im.size
            out["width"], out["height"] = w, h
            out["mode"] = im.mode
            if (w, h) != (want_w, want_h):
                out["err"] = f"resolution {w}x{h}, wanted {want_w}x{want_h}"
                return out
            rgb = np.asarray(im.convert("RGB"), dtype=np.uint8)
    except Exception as exc:                        # noqa: BLE001
        out["err"] = f"{type(exc).__name__}: {exc}"
        return out

    y = (rgb.astype(np.float64) / 255.0) @ LUMA
    out["mean"] = float(y.mean())
    out["sd"] = float(y.std())
    out["levels"] = int(np.unique((y * 255.0).round().astype(np.uint8)).size)
    out["bytes"] = os.path.getsize(path)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", action="append", required=True, dest="dirs",
                    help="a directory of delivered frames; repeatable")
    ap.add_argument("--first", type=int, required=True)
    ap.add_argument("--last", type=int, required=True)
    ap.add_argument("--res", type=int, nargs=2, required=True,
                    metavar=("W", "H"))
    ap.add_argument("--flat-sd", type=float, default=0.01)
    ap.add_argument("--black-mean", type=float, default=0.02)
    ap.add_argument("--min-levels", type=int, default=32)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2)))
    ap.add_argument("--json")
    a = ap.parse_args()

    want_w, want_h = a.res
    want = list(range(a.first, a.last + 1))

    # --- collect, and notice a frame delivered twice ----------------------
    by_frame: dict[int, list[str]] = defaultdict(list)
    for d in a.dirs:
        p = Path(d)
        if not p.is_dir():
            print(f"  !! not a directory: {d}")
            continue
        for f in sorted(p.glob("*.png")):
            m = FRAME_RE.search(f.name)
            if m:
                by_frame[int(m.group(1))].append(str(f))

    missing = [f for f in want if f not in by_frame]
    dupes = {f: v for f, v in by_frame.items() if len(v) > 1}
    stray = sorted(f for f in by_frame if f < a.first or f > a.last)

    todo = [(v[0], want_w, want_h) for f, v in sorted(by_frame.items())]
    print(f"decoding {len(todo)} frame(s) from {len(a.dirs)} directory(ies) "
          f"on {a.workers} worker(s) — this reads every byte")

    results = {}
    order = [f for f, _ in sorted(by_frame.items())]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for fr, res in zip(order, ex.map(measure, todo, chunksize=8)):
            results[fr] = res

    # --- verdicts ---------------------------------------------------------
    broken = {f: r for f, r in results.items() if r["err"]}
    ok = {f: r for f, r in results.items() if not r["err"]}
    sizes = {(r["width"], r["height"]) for r in ok.values()}
    flat = {f: r for f, r in ok.items()
            if r["sd"] < a.flat_sd or r["levels"] < a.min_levels}
    black = {f: r for f, r in flat.items() if r["mean"] < a.black_mean}

    print(f"\nsequence frames {a.first}-{a.last} ({len(want)} wanted)")
    print(f"  present            {len(by_frame)}")
    print(f"  missing            {len(missing)}"
          + (f"  {missing[:12]}{'...' if len(missing) > 12 else ''}"
             if missing else ""))
    print(f"  duplicated         {len(dupes)}"
          + (f"  {sorted(dupes)[:12]}" if dupes else ""))
    print(f"  outside range      {len(stray)}")
    print(f"  decoded            {len(ok)}")
    print(f"  FAILED to decode   {len(broken)}")
    for f, r in list(sorted(broken.items()))[:10]:
        print(f"    !! frame {f}: {r['err']}")
    print("  resolutions        "
          + (", ".join(f"{w}x{h}" for w, h in sorted(sizes, key=str))
             if sizes else "(none)"))
    if ok:
        sds = sorted(r["sd"] for r in ok.values())
        means = sorted(r["mean"] for r in ok.values())
        lv = sorted(r["levels"] for r in ok.values())
        print(f"  luminance sd       min {sds[0]:.5f}  "
              f"median {sds[len(sds) // 2]:.5f}  max {sds[-1]:.5f}")
        print(f"  luminance mean     min {means[0]:.5f}  "
              f"median {means[len(means) // 2]:.5f}  max {means[-1]:.5f}")
        print(f"  distinct levels    min {lv[0]}  "
              f"median {lv[len(lv) // 2]}  max {lv[-1]}")
    print(f"  FLAT (sd<{a.flat_sd} or levels<{a.min_levels})   {len(flat)}"
          + (f"  {sorted(flat)[:10]}" if flat else ""))
    print(f"  of those, BLACK (mean<{a.black_mean})    {len(black)}")

    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps({
            "first": a.first, "last": a.last, "res": [want_w, want_h],
            "dirs": a.dirs,
            "thresholds": {"flat_sd": a.flat_sd, "black_mean": a.black_mean,
                           "min_levels": a.min_levels},
            "missing": missing, "duplicated": {str(k): v for k, v in dupes.items()},
            "stray": stray,
            "frames": {str(k): results[k] for k in sorted(results)},
        }, indent=1))
        print(f"  written to {a.json}")

    bad = bool(missing or dupes or stray or broken or flat or len(sizes) != 1)
    if bad:
        print(f"\n>> STAGE RESULT: FAIL — {len(missing)} missing, {len(dupes)} "
              f"duplicated, {len(stray)} out of range, {len(broken)} that would "
              f"not decode, {len(sizes)} distinct resolution(s), {len(flat)} "
              f"flat/near-blank.")
        return 1
    print(f"\n>> STAGE RESULT: PASS — all {len(want)} frames decoded from "
          f"scratch, exactly one resolution ({want_w}x{want_h}), no gaps, no "
          f"duplicates, no flat or near-blank frames.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
