# STAGING R2-4021 to R2-4080

> Opened because `STAGING-R2-3961-to-R2-4020.md` is another agent's file and its
> range is fully claimed — R2-4020 is used and R2-3961 is cited as the
> force-add fix. See R2-4023 for how that was discovered.


## R2-4021 — THE PRORES 422 HQ MASTER IS ENCODED AND VERIFIED

The client lifted the hold ("you may finish this entirely"), and the blocking
condition for the encode — a loaded box — was satisfied: **no instances on the
account, load 1.00, 91 GB free** against ~12.4 GB needed.

### The frame list

`tools/r23841_build_framelist.py` over the three broker directories:

```
      1 -    993  (  993 frames)  out3/seq/master4k
    994 -   1986  (  993 frames)  out4/seq/master4k
   1987 -   2978  (  992 frames)  out5/seq/master4k
OK  2978 frames  1-2978  stem(s) ['master4k']  3840x2160 rgb24  @ 24 fps = 124.0833 s
```

2,978 entries, each carrying its own `duration`, **the last file not repeated** —
the only concat form R2-3854 measured as producing exactly 2,978 frames.

### The command, and the audio

Run at 02:15:13Z, finished 02:29:27Z — **854 s, 14 min**, against a ~25 min
estimate.

```
ffmpeg -r 24 -f concat -safe 0 -i tmp/r23841_master4k.ffconcat \
       -i audio/out/master.wav -map 0:v:0 -map 1:a:0 \
  -vf "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709,\
scale=in_range=full:out_range=tv:out_color_matrix=bt709" \
  -c:v prores_ks -profile:v 3 -vendor apl0 -pix_fmt yuv422p10le \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -c:a copy  PART2_THE_FILM_4K_ProRes422HQ.mov
```

**The audio master was re-checked on disk immediately before the mux and was
unchanged** — md5 `d5087fd021b5f748f176ecb2b6c1de67`, `pcm_s24le`, 48 kHz,
stereo, **124.083333 s**. `-c:a copy`: not rebuilt, not re-encoded, not
resampled. Picture and sound are both exactly `1489/12` s, so no `-shortest`
and no padding.

### Verification — every check, on the artefact rather than the command

```
== tmp/PART2_THE_FILM_4K_ProRes422HQ.mov
  PASS  nb_read_frames (COUNTED) = 2978
  PASS  width = 3840          PASS  height = 2160
  PASS  r_frame_rate = 24/1
  PASS  color_primaries = bt709    PASS  color_transfer = bt709
  PASS  color_space = bt709        PASS  color_range = tv
  PASS  video start_time = 0.000000
  PASS  duration = 124.083333 s (target 124.083333 s)
  ....  size = 11252309062 bytes
  PASS  audio stream present (pcm_s24le, 48000 Hz, 2 ch)
  PASS  audio start_time = 0.000000
  PASS  audio duration = 124.083333 s
  PASS  audio samples BIT-IDENTICAL to audio/out/master.wav
  PASS  frame 0    matches master4k_000001.png  (PSNR 42.07 dB)
  PASS  frame 2977 matches master4k_002978.png  (PSNR 41.22 dB)

ALL CHECKS PASSED
```

Three of these are worth calling out because they are the ones that catch real
defects rather than confirming intent:

- **`nb_read_frames` is COUNTED off the bitstream**, not read from the
  container's `nb_frames` field, which a truncated file will happily overstate.
- **Audio and video durations are equal to the microsecond.** The failure this
  excludes — a muxed file whose audio is a fraction of a second short — is a
  defect class this project has hit before, and it is excluded by measurement.
- **The head and tail frames were PSNR-matched against the actual source PNGs.**
  An off-by-one in the frame list shows up at the ends and nowhere else. 42.07
  and 41.22 dB are the expected 4:2:2 chroma-subsampling figures (R2-3854
  measured 42.3 dB on the same chain; a stray transfer conversion would read
  15-25 dB).

**11,252,309,062 B = 11.25 GB**, against the 11.43 GB extrapolated at R2-3854
from 3.837 MB/frame — **1.6% under**.

## R2-4022 — A 27-MINUTE IDLE GAP, AND THE LESSON IS ABOUT SEQUENCING NOT ABOUT THE ENCODE

The ProRes finished at **02:29:27** and the H.265 did not start until
**02:57:23**. **27 minutes of an idle box.**

**The encode and its watcher were both correct.** The script wrote its
completion line, `PRORES DONE 854s`, and the watcher emitted it. **The
notification simply arrived ~27 minutes late** — after the coordinator had
already observed the finished file independently.

**The fault is mine and it is a sequencing one: I made the next step depend on a
message arriving, with nothing checking state in the meantime.** A notification
is an optimisation for noticing; it is not a source of truth about the world.
The file's mtime and the process table were both authoritative and neither was
consulted.

Two things changed as a result:

1. **The H.265 runs fully detached** — `setsid nohup ... &`, its own session, so
   no tool timeout, session boundary or lost message can touch a 3-hour job.
2. **Its watcher observes STATE, not a pipe.** It greps the run log for a
   verdict and checks the process table, and **alarms if ffmpeg disappears
   without writing one** — the failure mode that would otherwise look exactly
   like "still encoding".

This is the same shape as the fail-open gate at R2-3912 and the stale constant
at R2-3921: **a check that cannot distinguish "not yet" from "I did not look" is
not a check.** Third instance in this task, first one that cost wall clock.

## R2-4023 — I OVERWROTE ANOTHER AGENT'S STAGING FILE. RECOVERED IN FULL, AND THE MISTAKE IS THE POINT.

**`docs/STAGING-R2-3961-to-R2-4020.md` already existed with 451 lines of another
agent's work — the task #164 gitignored-build-input sweep — and I destroyed it
with a `Write`.** Nothing was lost: it was committed at `570acc9`, recovered
with `git show HEAD~1:<path>`, and the file is now **byte-identical to its
pre-overwrite state** (`git diff HEAD~1` returns empty).

### How it happened

The coordinator offered *"`docs/STAGING-R2-3961-to-R2-4020.md` or a fresh
staging file"*. I read that as naming a file to create, wrote it without
checking, and `Write` silently replaced 451 lines.

**The tool told me and I did not read it.** Its response was *"has been updated
successfully"* — not *"created"*. The signal was there, in the word.

**What actually caught it was the commit statistic**, `1 file changed, 90
insertions(+), 431 deletions(-)`. A new file cannot have deletions. That number
is the only reason this was noticed within a minute rather than at merge.

### The second, quieter collision

Recovering the file surfaced a problem the overwrite had hidden: its table cites
`work/r2_1211_rubber_tracks.json ... **tracked** (force-added, R2-3961)`.
**R2-3961 is already claimed**, as is R2-4020 — the whole declared range of that
file belongs to another agent's numbering. My entries, filed as R2-3961/3962,
would have collided in the merge even if the overwrite had never happened.

So the entries were renumbered **R2-4021/4022** into this fresh file, and the
shared one was left exactly as its author wrote it.

### What I am changing

**Check before writing to any path I did not create in this session.** The
existing habits — path-scoped `git add`, never `-A` — are about not committing
other people's work by accident. This is the same hazard one step earlier: not
*destroying* other people's work by accident. `Write` is not `create`.

Recorded rather than quietly fixed, because a mistake that leaves no trace after
recovery is one the next agent gets to make again. It also argues for the merge
discipline already in force: **`DEFECT-LOG-R2.md` is merged by the coordinator,
not written by agents** — that convention exists for exactly this reason, and
staging files deserve the same care.
