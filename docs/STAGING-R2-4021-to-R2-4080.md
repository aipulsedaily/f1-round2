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

## R2-4024 — THE H.265 VIEWING COPY, AND THE 0.333 ms AUDIO QUESTION ADJUDICATED BY COUNTING

Encoded detached, 02:57:23Z -> 04:22:19Z, **5,082 s (1 h 25 m)** against a ~3.1 h
estimate. **880,272,255 B = 880 MB**, inside the 1 GB brief ceiling and between
R2-3854's 856 MB target and 934 MB VBV-pinned bounds.

```
== watch/PART2_THE_FILM_4K_h265.mp4
  PASS  nb_read_frames (COUNTED) = 2978
  PASS  width = 3840   height = 2160   r_frame_rate = 24/1
  PASS  color_primaries/transfer/space = bt709,  color_range = tv
  PASS  video start_time = 0.000000
  PASS  duration = 124.083333 s
  PASS  audio stream present (aac, 48000 Hz, 2 ch), start_time = 0.000000
  PASS  frame 0 matches master4k_000001.png  (PSNR 43.85 dB)
  PASS  frame 2977 matches master4k_002978.png  (PSNR 40.23 dB)
  PASS  faststart (moov before mdat)
ALL CHECKS PASSED
```

`hvc1` and the full bt709 set both landed, so the `setparams` fix held on the
real file and not just on the four-frame probe.

### The audio number: refuted as a defect, by counting samples rather than reasoning

The container reports audio `124.083000` against video `124.083333` — 0.333 ms.
**Counted off the artefacts:**

| | samples | seconds |
| --- | ---: | --- |
| source `audio/out/master.wav` | **5,956,000** | 124.083333 |
| ProRes master, decoded | **5,956,000** | exact, and bit-identical |
| **H.265 AAC, decoded** | **5,956,608** | **608 samples LONGER** |
| H.265 container `duration_ts` | 5,955,984 | 124.083000 |

**The decoded audio is longer than the source, not shorter.** A truncation
presents as *fewer* decoded samples; there are 608 *more*, which is AAC filling
its final 1024-sample frame (5,818 frames emitted, one frame of priming removed
by the decoder). **No audio is missing, so there is nothing to be out of sync
with at the tail.**

**And the 0.333 ms is not AAC granularity** — that would be a multiple of 1024
samples; this is 16. The mechanism is coarser and is in the container:

```
mvhd timescale = 1000        duration = 124084
round(124.083333 * 1000) = 124083 ms  ->  at 48 kHz = 5,955,984
```

**The MP4 movie header stores duration at millisecond resolution**, so
124.083333 s is written as 124083 ms and reads back as 124.083000 s — the
reported figure, exactly. A bookkeeping rounding in the header, 16 samples wide,
with the full audio present in the stream.

**Confirmed rather than waved through**, which was the right instruction: the
answer was in the same direction as "probably rounding", but the *reason* given
first (AAC frame granularity) was wrong, and only counting distinguished them.

## R2-4025 — FILED, AND THE BANNER IS RETIRED

Both files moved from gitignored `tmp/` into `watch/`, and **re-verified after
the move** — 2,978 counted frames each, so nothing was truncated in transit.

```
watch/PART2_THE_FILM_4K_ProRes422HQ.mov   11,252,309,062 B   2026-08-14 02:29
watch/PART2_THE_FILM_4K_h265.mp4             880,272,255 B   2026-08-14 04:22
```

`watch/INDEX.md` gains two **CURRENT** rows carrying real provenance — source
blend and its sha16, world, frame range, spec, and the fact that the audio was
muxed losslessly and verified bit-identical rather than rebuilt.

**The R2-3181 "DO NOT JUDGE THE ENDING" blockquote is removed**, replaced by a
block that names `PART2_THE_FILM_4K_ProRes422HQ.mov` and
`PART2_THE_FILM_4K_h265.mp4` as the files that supersede every clip above. It
states what the old banner claimed, that it is fixed in delivered pixels, and
that the clips above remain superseded **for a different reason than before** —
they are old cuts of a film that now exists in full.

### One repository hazard worth flagging rather than fixing unilaterally

**`watch/` tracks no video.** `git ls-files watch/` returns only `INDEX.md`,
`audio/INDEX.md` and `audio/clips.json`; `*.mp4` is gitignored at `.gitignore:21`.
**`*.mov` is not**, so the 11.25 GB ProRes master now sits in `watch/` as an
untracked file that a single `git add -A` would commit permanently into history.

The standing rule — *`git add` path-scoped only, never `-A`* — already prevents
this, and only `watch/INDEX.md` was committed here. **But the rule is now the
only thing standing between the repository and an 11 GB blob.** Adding `*.mov`
alongside `*.mp4` in `.gitignore` would make it structural instead of
behavioural. **Not done unilaterally** — it is a shared file and the call is the
coordinator's.

---

# TASK #168 — the round-1 dependency at the root of the car chain

## R2-4026 — IT IS READ AT BUILD TIME. THIS IS NOT A NULL.

The question was whether `/home/zany/opus5-car-render/work/iter.blend` is
actually an input to a round-2 build or merely historically upstream. **It is an
input**, and the reason a filename grep is the wrong instrument here is that
**the dependency is not in any code path — it is in the command line.**

```
render/film25_breach.blend      the delivered master's scene
  <- world/car_anim.blend       anim/build_car_anim.py   run ON beat1_anim.blend
  <- world/beat1_anim.blend     anim/build_beat1_anim.py run ON iter.blend
  <- /home/zany/opus5-car-render/work/iter.blend   288,254,978 B, 2026-07-26
```

`tools/build_film_scene.py` defaults `--car` to `world/car_anim.blend` and
appends `CAR` / `SHOWROOM` / `LIGHTS` / `PROPS` out of it. `build_car_anim.py`
is run on `beat1_anim.blend`. And `build_beat1_anim.py` has **no argument for
its base scene at all** — the scene is whatever `blender -b <file>` opened, and
the script reads every part's seated transform straight out of it
(`seated = ob.location.copy()`, captured before a single key is written; its own
header: *"the seated pose is not authored, it is the round-1 car"*).

So there is no constant to find, no default to inspect, and nothing in the repo
that records which blend the car came from. Checked, and clean: none of
`build_beat1_anim.py`, `build_car_anim.py`, `carpath.py`, `carrig.py`,
`filmtime.py`, `car_paint.py`, `imperfections.py`, `build_film_scene.py`,
`fix_audit_blend.py` contains an absolute path outside `f1-round2`. The only
occurrences of the string in the tree are docstring example commands and one
substring test (see R2-4028).

**Tested rather than argued.** With the path unavailable:

```
$ blender -b <missing>/iter.blend --factory-startup -P anim/build_beat1_anim.py -- ...
ERROR Cannot read file "...": No such file or directory
EXIT=1
```

Blender exits before the script runs. The chain does not degrade, warn or fall
back — and **`f1-round2` tracks no blends at all** (`.gitignore:12 *.blend`;
`git ls-files | grep -c .blend` = 0), so no artefact in this repo is a backup.
`/home/zany/opus5-car-render` **is not a git repository** — no `.git` anywhere
under it — so it has no history to recover from either.

## R2-4027 — AND IT IS FULLY REGENERABLE. THE SWEEP'S "NOTHING CAN REBUILD IT" IS HALF WRONG.

`STAGING-R2-3961-to-R2-4020.md` recorded *"nothing in `f1-round2` can rebuild
it"*. True as written, and it reads as *"this binary is irreplaceable"*, which
is false. Round 1's own README gives the command that emits it, and **running
that command today reproduces the shipped scene exactly.**

```
PYTHONDONTWRITEBYTECODE=1 /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
    -P /home/zany/opus5-car-render/tools/rebuild_scene.py -- --out work/t168/r1_fresh.blend
>> s08_assemble  127.0s  4,354,204 polys, 15 parts, failed=[]
>> scene: 919 meshes, 4,598,601 polys, 23 lamps
>> wrote ... in 109.8s total
```

Compared against `iter.blend`, by three independent instruments:

| | result |
|---|---|
| file size | **288,254,978 B — identical to the byte** |
| `tools/inventory.py` totals | 947 objects / 919 meshes / 51 materials / 4 cameras / 23 lights / 4,598,601 base polys / 10,122,867 eval tris — **identical**, and identical to `docs/inventory_iter.json` measured off `iter.blend` on 07-28 |
| object names | 947 vs 947, **0 present on only one side** |
| worst Δ location / rotation / scale / dimensions over all 947 | **0.000e+00** on all four |
| type / parent / collection / material-slot differences | **0 / 0 / 0 / 0** |
| **geometry fingerprint** — SHA-256 over vertex coordinates (1e-6 m), polygon and edge counts, material slots, per object | **0 mismatches over 919 meshes, 4,721,531 vertices, 4,598,601 polygons** |
| raw bytes differing | **20,608 of 288,254,978 = 0.0071 %** — isolated 4-byte words at a fixed ~2.4 kB stride plus the embedded filepath, i.e. per-datablock session identifiers |

The geometry hash is the one that settles it: matching counts and transforms
say nothing about a single vertex, and `work/t168/meshhash.py` reads the
coordinates.

**So the irreplaceable thing was never the 288 MB binary.** It is the **2.4 MB
of Python that emits it** — `opus5-car-render/build/**.py` (46 files) plus
`tools/rebuild_scene.py` — sitting in a directory with no version control.
Copying the artefact, which is what the task offered as the remedy, would have
preserved the cheap half of the problem and left the expensive half where it
was.

## R2-4028 — A SECOND ROUND-1 COUPLING, FOUND BY RUNNING THE FIX RATHER THAN WRITING IT

The first end-to-end run of the reconstitution built the scene correctly and
then **refused at the last line**:

```
>> seat check: worst deviation 0.0000 mm over 616 parts, 0 stragglers
REFUSING TO SAVE: blend still references external images
  ['/home/zany/f1-round2/work/t168/recon_work/assets/city.exr'].
```

`build/s01_base.py:154` calls `bpy.data.images.load()` on
`$PROJ/assets/city.exr`, which **raises** if the file is absent, so the round-1
build will not complete without something at that path. Round 1's `city.exr` is
a real photographic HDRI and the brief forbids downloaded stock, so it cannot be
vendored — a generated 8×4 px stub stands in, and its content never survives
because `save_clean()` replaces the world with a procedural sky anyway.

**But `save_clean()` could not see the stub as external.** Its strip rule was

```python
if "opus5-car-render/assets" in ap or not os.path.exists(ap):
```

which is **not** "outside this project" as its own comment claims — it is
"inside round one", and it worked only because round 1 happens to live at that
path. The one hard build-time coupling to round 1 had **a second, quieter one
hiding behind it: the stripper that removes round 1's HDRI is keyed to round
1's directory name.**

Fixed to ask the question the comment already asked — is the path outside
`f1-round2` — and **behaviour on the current layout is unchanged by proof, not
by test**: the old clause only ever *kept* an image into the refusal, never into
a save, so any input that previously saved successfully saves bit-identically.
The only inputs whose outcome changes are ones that previously **failed**.

Retracted while in there: the note at `fix_audit_blend.py:164` calling
`save_clean()` *"dead code, called by nothing, here or anywhere in the tree"*.
It is called by `anim/build_beat1_anim.py:214` — the first step of the car chain
— and by `world/items/access_road_slab.py`, `gravel_bed_surface.py` and
`asphalt_wearing_course.py`. It also raised live during this task, which is the
opposite of never having run. A stale "this is dead" note on a load-bearing
function is an invitation to delete it.

Also recorded, not actioned: `world/beat1_audit_cams.json` carries
`"source": ".../iter.blend"` and **nothing reads that file** — an orphan record,
not a dependency.

## R2-4029 — THE RECIPE IS VENDORED, AND IT IS PROVEN SUFFICIENT BY RUNNING WITHOUT ROUND 1

`round1_source/` now holds a **byte-faithful frozen copy** of round 1's build
tree, with `PROVENANCE.md` stating where it came from, what it closes, the one
input deliberately missing, and four rules (do not build from it, do not edit
it, round 1 stays read-only, and what to change if round 1 ever goes).

```
round1_source/build/            <- opus5-car-render/build/         46 .py, minus __pycache__
round1_source/tools/rebuild_scene.py
round1_source/PROVENANCE.md
round1_source/reconstitute.sh
```

**Measured cost: 2.4 MB of text, against a 41 MB `.git`.** The 288 MB blend is
deliberately **not** copied: `.gitignore:12` excludes `*.blend` as *"all
regenerable, all enormous"* and this one is exactly that, so committing it would
break the repository's own policy on the policy's own terms — and grow every
future clone by about eight times, permanently, to store something a five-minute
command rebuilds.

`reconstitute.sh` rebuilds the scene from the vendored copy with **zero
references to round 1** — it asserts that by grepping its own working tree for
the string and refusing if one survives — and then the round-2 car chain was run
on the result:

```
>> working tree at /tmp/r1recon.uxthb7 has ZERO references to round 1
>> reconstituted r1_recon.blend (288254978 bytes) from vendored source alone
   geometry fingerprints vs the shipped iter.blend: 0 mismatches / 919 meshes

>> seat check: worst deviation 0.0000 mm over 616 parts, 0 stragglers
>> save_clean: world=R2_ProceduralSky, 0 external deps
>> animated 616 objects across 15 clusters
>> saved beat1_from_recon.blend   291,187,821 B
>> STAGE RESULT: BEAT1_ANIM_OK
```

**291,187,821 B is the size of the shipping `world/beat1_anim.blend` to the
byte.** The claim is not that the recipe looks complete — it is that the chain's
first artefact came out the same size from a tree that had never seen round 1.

### Round 1 was never written to, and that was verified rather than intended

A full `find /home/zany/opus5-car-render -printf '%T@ %s %p\n' | sort` snapshot
was taken before the first run and re-diffed after every run, including the ones
that **import round 1's modules** — `PYTHONDONTWRITEBYTECODE=1` throughout, so
not even a `.pyc` landed in its `build/__pycache__`. All 1,331 entries identical
every time. All heavy Blender work went through `tools/buildlock.sh`.

### What would be lost, stated plainly

`iter.blend` supplies the whole of round 1 to round 2 — 616 car meshes plus
`CAR_ROOT`, 76 showroom objects, 61 lights, 189 props, 51 materials, 4,598,601
base polygons — and **none of it is derivable from anything tracked in
`f1-round2`.** `docs/explode_plan.json` is tracked but names parts without
geometry; `docs/inventory_iter.json` holds every seated transform to six
decimals but is gitignored at `.gitignore:60`, and transforms without meshes are
not a car. That is what the 2.4 MB now covers.
