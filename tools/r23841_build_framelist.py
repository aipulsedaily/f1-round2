"""BUILD THE ONE-SHOT FRAME LIST — 2,978 4K PNGs living in three directories,
handed to ffmpeg as a single continuous input.

    .venv/bin/python tools/r23841_build_framelist.py \
        /home/zany/vast-render/out3/seq/master4k \
        /home/zany/vast-render/out4/seq/master4k \
        /home/zany/vast-render/out5/seq/master4k \
        --first 1 --last 2978 --fps 24 \
        --out /home/zany/f1-round2/tmp/r23841_master4k.ffconcat

WHY IT EXISTS: the film is one unbroken shot, but it renders on a three-card
farm, so the frames land in three blocks in three directories. `-i name_%06d.png`
cannot span directories. The concat demuxer can -- but only in one exact form.
Measured on ffmpeg n8.1.2, on a 48-frame control:

    file + duration + REPEATED last file  -> 49 frames   WRONG (one extra)
    file only, -r 24 as an input option   -> 48 frames   but spews
                                             "PTS ... invalid dropping"
    file only, -r 24 as an OUTPUT option  ->  4 frames   CATASTROPHIC
    file + duration, NO repeated last,
      read with `-r <fps> -f concat`      -> 48 frames   CLEAN, and the
                                             per-frame md5s came back
                                             bit-identical to the source PNGs
                                             in order, no dupes

So this emits the fourth form and nothing else. The last file carries a
`duration` like every other and is NOT repeated; the repeat is the classic
concat-demuxer advice and it is wrong here, because every entry already states
its own duration.

NOTHING IS HARDCODED that can be read off the disk: the filename stem, the
zero-pad width and the per-directory frame ranges are all derived from what is
actually present. The only things you assert are the first frame, the last
frame and the fps -- the three facts the render order cannot tell you.

The script REFUSES to emit a list that is not exactly (last - first + 1)
entries in strictly ascending order with no gap and no duplicate. A silent gap
in a one-shot film is a cut, and a cut is the one thing this film may not have.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

# broker/seq.py:95 -> f"{valid_name(name)}_{int(frame):06d}.png"
# The pad width is NOT taken from that line; it is measured below, so that a
# broker change to 7 digits is picked up instead of silently mis-sorted.
FRAME_RE = re.compile(r"^(?P<stem>.+)_(?P<num>\d+)\.png$")


class FramelistError(RuntimeError):
    """Raised for any condition that would produce a wrong-length film."""


def scan_dir(d: Path) -> dict[int, Path]:
    """Every frame-numbered PNG in `d`, keyed by frame number.

    Rejects a directory whose PNGs disagree about the stem or the pad width --
    that means two jobs wrote into one directory and the frame numbers are not
    from one sequence.
    """
    if not d.is_dir():
        raise FramelistError(f"not a directory: {d}")
    frames: dict[int, Path] = {}
    stems: set[str] = set()
    widths: set[int] = set()
    dupes: list[str] = []
    for entry in sorted(os.listdir(d)):
        m = FRAME_RE.match(entry)
        if not m:
            continue  # manifest.json and friends
        n = int(m.group("num"))
        if n in frames:
            dupes.append(entry)
        frames[n] = d / entry
        stems.add(m.group("stem"))
        widths.add(len(m.group("num")))
    if not frames:
        raise FramelistError(f"no frame-numbered PNGs in {d}")
    if dupes:
        raise FramelistError(f"duplicate frame numbers in {d}: {dupes[:5]}")
    if len(stems) != 1:
        raise FramelistError(f"{d} mixes sequences: stems {sorted(stems)}")
    if len(widths) != 1:
        raise FramelistError(f"{d} mixes zero-pad widths: {sorted(widths)}")
    return frames


def probe_dims(path: Path) -> tuple[int, int, str]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,pix_fmt",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    s = json.loads(out)["streams"][0]
    return int(s["width"]), int(s["height"]), s["pix_fmt"]


def build(dirs: list[Path], first: int, last: int, probe_all: bool):
    if last < first:
        raise FramelistError(f"--last {last} is before --first {first}")
    expected = last - first + 1

    merged: dict[int, Path] = {}
    collisions: list[int] = []
    per_dir = []
    stems: set[str] = set()
    for d in dirs:
        frames = scan_dir(d)
        stems.add(FRAME_RE.match(next(iter(frames.values())).name).group("stem"))
        for n, p in frames.items():
            if n in merged:
                collisions.append(n)
            merged[n] = p
        per_dir.append((d, min(frames), max(frames), len(frames)))
    if collisions:
        raise FramelistError(
            f"{len(collisions)} frame numbers appear in more than one directory, "
            f"e.g. {sorted(set(collisions))[:8]} -- the blocks overlap"
        )

    wanted = list(range(first, last + 1))
    missing = [n for n in wanted if n not in merged]
    if missing:
        runs, start, prev = [], missing[0], missing[0]
        for n in missing[1:]:
            if n != prev + 1:
                runs.append((start, prev))
                start = n
            prev = n
        runs.append((start, prev))
        raise FramelistError(
            f"{len(missing)} of {expected} frames are missing; gaps: "
            + ", ".join(f"{a}-{b}" if a != b else str(a) for a, b in runs[:12])
        )

    seq = [(n, merged[n]) for n in wanted]

    # strict ascending, no gap, no dupe -- restated as an assertion on the built
    # list rather than trusted from the construction above.
    nums = [n for n, _ in seq]
    if len(nums) != expected:
        raise FramelistError(f"built {len(nums)} entries, expected {expected}")
    if any(b - a != 1 for a, b in zip(nums, nums[1:])):
        raise FramelistError("frame numbers are not strictly ascending by 1")
    if len(set(p.resolve() for _, p in seq)) != expected:
        raise FramelistError("the same file is referenced by two frame numbers")

    empty = [str(p) for _, p in seq if p.stat().st_size == 0]
    if empty:
        raise FramelistError(f"{len(empty)} zero-byte PNGs, e.g. {empty[:3]}")

    to_probe = seq if probe_all else [seq[0], seq[len(seq) // 2], seq[-1]]
    dims = {probe_dims(p) for _, p in to_probe}
    if len(dims) != 1:
        raise FramelistError(f"frames disagree on size/format: {sorted(dims)}")
    w, h, pix = dims.pop()

    return seq, per_dir, sorted(stems), (w, h, pix)


def emit(seq, fps: Fraction, out: Path | None) -> str:
    dur = 1 / fps
    lines = ["ffconcat version 1.0"]
    for _, p in seq:
        # Single quotes are the concat demuxer's quoting; a path containing one
        # would corrupt the list, so refuse rather than mangle it.
        s = str(p)
        if "'" in s:
            raise FramelistError(f"path contains a single quote: {s}")
        lines.append(f"file '{s}'")
        lines.append(f"duration {float(dur):.10f}")
    text = "\n".join(lines) + "\n"
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    return text


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("dirs", nargs="+", type=Path,
                    help="frame directories, any order; blocks must not overlap")
    ap.add_argument("--first", type=int, required=True)
    ap.add_argument("--last", type=int, required=True)
    ap.add_argument("--fps", default="24",
                    help="exact fps, integer or fraction e.g. 24000/1001")
    ap.add_argument("--out", type=Path, help="write the .ffconcat here")
    ap.add_argument("--probe-all", action="store_true",
                    help="ffprobe every frame, not just first/middle/last")
    ap.add_argument("--json", type=Path, help="write a summary here")
    a = ap.parse_args(argv)

    fps = Fraction(a.fps)
    try:
        seq, per_dir, stems, (w, h, pix) = build(
            [d.resolve() for d in a.dirs], a.first, a.last, a.probe_all)
        emit(seq, fps, a.out)
    except FramelistError as e:
        print(f"FRAMELIST REFUSED: {e}", file=sys.stderr)
        return 2

    n = len(seq)
    secs = n / float(fps)
    for d, lo, hi, cnt in sorted(per_dir, key=lambda r: r[1]):
        print(f"  {lo:6d} - {hi:6d}  ({cnt:5d} frames)  {d}", file=sys.stderr)
    print(f"OK  {n} frames  {a.first}-{a.last}  stem(s) {stems}  "
          f"{w}x{h} {pix}  @ {fps} fps = {secs:.4f} s", file=sys.stderr)
    if a.out:
        print(f"    wrote {a.out}", file=sys.stderr)

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps({
            "frames": n, "first": a.first, "last": a.last,
            "fps": str(fps), "duration_s": secs,
            "width": w, "height": h, "pix_fmt": pix, "stems": stems,
            "blocks": [{"dir": str(d), "first": lo, "last": hi, "count": c}
                       for d, lo, hi, c in sorted(per_dir, key=lambda r: r[1])],
            "list": str(a.out) if a.out else None,
        }, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
