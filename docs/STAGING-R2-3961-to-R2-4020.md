# STAGING R2-3961 to R2-4020

## R2-3961 — THE PRORES 422 HQ MASTER IS ENCODED AND VERIFIED

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

## R2-3962 — A 27-MINUTE IDLE GAP, AND THE LESSON IS ABOUT SEQUENCING NOT ABOUT THE ENCODE

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
