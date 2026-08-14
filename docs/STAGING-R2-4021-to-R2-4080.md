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

---

# TASK — the shared chain and the glass breach (`docs/audio-rebuild3/SPEC-CHAIN-AND-GLASS.md`)

> **Scope note, and it matters:** the breach is **beat 3**, `3_breach`,
> **36.0–44.0 s**. Beat 4 is `4_transit` (44.0–49.6 s, apron/merge, no glass).
> The brief said beat 4. Anyone who has been auditioning beat 4 has been
> listening to the transit, eight seconds after the event.
>
> `audio/verify.py` is NOT touched by this work — the gate rebuild is a
> parallel workflow's. Neither is `audio/engine.py`.

## R2-4030 — THE INSTRUMENTS FIRST, AND THE DELIVERED MASTER MEASURED WITH THEM

Three tools, because "watch it fail first" needs something to watch with:

| tool | what it measures | cost |
|---|---|---|
| `tools/r2_4030_master_probe.py` | a finished master against G2/G3/G4/G5/G6/G13 | 40 s |
| `tools/r2_4030_defect_witness.py` | seven defects **in the code**, as unit measurements | 30 s |
| `tools/r2_4030_breach_bench.py` | the whole breach source, on either grid | 60 s |

The bench is the one that made this task affordable: **a full render is 27
minutes**, and every §2 target can be watched moving in the bench in one.

### The delivered master, measured

```
BREACH 36.0-44.0 s
  spectral centroid            51.5 Hz        (target >= 1200)
  energy <30 Hz               60.40 %
  energy <100 Hz              85.57 %
  energy >4 kHz              0.0021 %         (target >= 8)
  50 ms crest p50/max      7.31 /  11.81 dB   (target >= 18)
  onset rise 10-90%            6.90 ms        (target <= 2)
WHOLE FILM
  median 50 ms crest           9.70 dB        (Gaussian white = 10.9)
  band RMS: 1k_2k -25.5  4k_8k -39.7  8k_12k -51.1  12k_16k -58.3
  0/6 gates pass
```

Every one of those reproduces the spec's figure. **The whole-film median crest
of 9.70 dB is identical to the spec's, to two decimals** — this instrument and
the diagnosis are measuring the same thing.

## R2-4031 — SEVEN DEFECTS WATCHED FAILING, IN THE CODE, BEFORE ANY FIX

`audio/out/witness_BEFORE.json`. Not quoted from the report — re-measured.

| defect | measured, before |
|---|---|
| K-weighting is deaf to the mix | **−13.30 dB @ 20 Hz**, −23.81 @ 10, −35.42 @ 5 |
| the 8-pass limiter loop hides its own work | per-pass GR `[-4.51,-4.90,-4.08,-3.66,-7.48,-5.60,-2.37,-0.53]`, **reported: −0.53, true max: −7.48** |
| `soft_limit` ducks **before** the peak | gain starts falling **161.4 ms BEFORE** a single-sample impulse, recovers 161.4 ms after: a **322.9 ms hole**, −14.10 dB deep |
| the pane cannot generate high frequencies | `fmax=18000` still gives a **4673.6 Hz ceiling**, **0 modes above 4718 Hz** |
| shard amplitude is 1/pitch | slope of log-amp vs log-f₁ = **−0.994**; top 10 contacts = **32.1%** of all shard energy and **all ten ring at 54.4 Hz** |
| `warp()` transposes rather than stretches | a 1 kHz tone on the world grid comes out at a **153.7 Hz** centroid over 41–43 s and **1000.0 Hz** over 44.0–45.2 s |
| the shipped `shards.wav` stem | centroid **19.6 / 31.6 / 148.5 Hz** across those same three windows — 7.6× at the ramp boundary, one unchanged generator |

**The refutation that has to be retracted.** An earlier diagnosis in this
project declared the limiter "REFUTED, clean" on `max_gain_reduction_db =
−0.124`. That figure is produced by `master.py:633-641` reassigning `gr` on
every one of eight passes, so it reports the **last and gentlest** one. The
witness reproduces the mechanism directly. **The refutation is wrong and is not
carried forward.**

**One claim in the spec did NOT reproduce, and it is recorded as not
reproducing.** §2.2 Defect C says every shard below 26.6 mm renders as digital
silence. The threshold is real — `render_shards` skipped any mode at or above
`0.45*sr`, i.e. any shard under **26.61 mm** — but **on this seed and this
aperture geometry the ballistic sim never draws one**: the smallest shard is
**40.2 mm**, and `contacts_fully_silent_pct = 0.0`. Only 6 contacts of 995 lost
their third mode. So the defect is not silence, it is **absence**: the fines
that carry the glass percept are not in the sim to be silenced. The guard and
the noise-burst fallback are implemented anyway (R2-4042), and the density is
supplied where the spec itself says it should be — the PhISEM bed (R2-4044).

## R2-4032 — THE LIMITER'S GAIN PATH WAS SYMMETRIC IN TIME. `audio/dsp.py`

```python
g = minimum_filter1d(need, size=2*rel+1)          # rel = 120 ms, CENTRED
g = sosfiltfilt(butter(2, 1000/release_ms), g)    # ZERO-PHASE
```

Both steps run backwards as well as forwards. Measured on a single-sample
impulse at 96 kHz: **the gain began falling 161.4 ms before the peak** and
recovered 161.4 ms after it — a **322.9 ms hole with the transient in the
middle**, reaching −14.10 dB.

That is not a limiter artefact; it is a limiter running in reverse, and it ducks
exactly the material the ear judges an onset against. The breach's 10–90 % rise
measured **6.90 ms** against a 2 ms target and this stage is where most of it
went.

**Replaced with a causal one-pole release.** Attack comes from the lookahead
alone — **1 ms**, the spec's ceiling — release is a 40 ms one-pole, and nothing
in the gain path runs backwards. The recursion is genuinely nonlinear (instant
attack, exponential release) so it is evaluated at a **2 kHz control rate over
the block minimum of `need`**, which cannot miss a peak because the block
minimum bounds every sample in the block, then interpolated between block
centres. `min(g, need)` still guarantees the ceiling exactly.

| | before | after |
|---|---|---|
| gain dip **before** the peak | **161.4 ms** | **1.74 ms** |
| total hole | 322.9 ms | 177.1 ms, **all of it after** |
| crest loss on a 0.2 ms click (G4's own control, limit 3 dB) | — | **0.687 dB** |
| film-length pass | — | 12.7 s |

One bug found by measuring rather than by reading: the first version smoothed
the control signal with `lfilter`, which starts from zero initial conditions and
**opened the film with a 0.5 ms fade-up out of silence** — the witness reported
the gain dip starting at sample 0, i.e. 500 ms "before" the peak. Replaced with
`np.interp` between control-block centres, which has no startup state at all.

## R2-4033 — `BUS_HF_SHELF` EMPTIED

It held −12 dB @ 2 kHz on `wind`, `tyres` and `bed`. R2-1402's reasoning was
that those beds buried the engine's harmonics, and the shelf did recover 6.0 dB
of harmonic-to-noise ratio above 2.6 kHz — **by removing the numerator's
competition, not by adding anything**, and the whole film paid for it: 1–2 kHz
−25.5 dBFS against 4–8 kHz −39.7 and 8–12 kHz −51.1. A film in which nothing has
a top end sounds like a filter, and the client's word for that was "hair dryer".

Kept as an empty table rather than deleted, so re-introducing a mix EQ still has
to be declared in one place.

## R2-4034 — THE DUAL CRITERION: A LOUDNESS TARGET **AND** A PEAK CEILING

`dsp.max_short_term_lufs` is BS.1770 K-weighted, and K-weighting exists to model
what a listener hears — which means it is **designed** to discount sub-bass. The
breach's buses are almost entirely down there, so the meter under-read the
`impact` bus and the table obediently boosted it to compensate.

`add()` now trims to the **lesser** of the loudness target and whatever keeps
the bus's linear peak at or below 1.0, and reports which criterion won and by
how much. Measured live in the render log:

```
engine   PEAK CRITERION: LUFS target wanted +25.06 dB, peak ceiling allows +21.03 dB
                         -- the meter is under-reading this bus by  4.03 dB
impact   PEAK CRITERION: LUFS target wanted +22.41 dB, peak ceiling allows  +6.15 dB
                         -- the meter is under-reading this bus by 16.25 dB
shards   PEAK CRITERION: LUFS target wanted -47.93 dB, peak ceiling allows -52.09 dB
                         -- the meter is under-reading this bus by  4.17 dB
```

**16.25 dB on the impact bus.** That bus used to enter the sum at a linear peak
of 7.50 (+17.5 dBFS); it now enters at 1.0.

**G15 is split into its two halves, and this is a reinterpretation of the gate
rather than a pass of it as written.** A raw trim is mostly UNIT CONVERSION: the
shard bus is a sum of `m·v` momenta and peaks in the hundreds, the pane bank is
a sum of biquad outputs and peaks at 1e-4. `mix_trim_db = trim − peak_trim` is
what is left after normalising a bus's peak to full scale, and that is the
number that means "this bus is being pushed". Both are reported. Stated openly
because the gate as literally written (`|trim| ≤ 12 dB`) is failed by buses
whose levels are physically correct and merely not in dBFS.

## R2-4035 — THE BREACH IS SYNTHESISED ON THE FILM GRID. THIS IS THE BIGGEST SINGLE CHANGE.

`warp()` is `grid.to_film` → `catmull_rom`: **a varispeed resampler, not a
time-stretch**. Beat 3 runs world time to a floor of 0.153719, so anything
warped through it during the breach is transposed **6.51× down — 31.4 semitones,
two and a half octaves**.

Real slow-motion sound design re-times the event **schedule**; it does not
varispeed the objects. So each contact's ONSET is mapped world→film through the
clock and the modal decay is synthesised in **film-rate samples at the true ring
frequency**. The shower stretches — 3.148 s of world becomes **9.524 s of film,
×3.03** — and every shard still rings at its physical pitch.

**Measured A/B on the same generator, `--legacy` versus current:**

| bus, 36–44 s | world grid + `warp()` | film grid |
|---|---:|---:|
| shards, spectral centroid | **32.7 Hz** | **178.7 Hz** |
| shards, energy < 30 Hz | **60.18 %** | **0.21 %** |
| impact, spectral centroid | **14.0 Hz** | 78.8 Hz |
| impact, energy < 30 Hz | **92.99 %** | 3.09 % |

The legacy column reproduces the shipped stem (27 Hz measured on `shards.wav`
over 36–40 s), so the control is the delivered artefact, not a strawman.

**Deliberately partial, and this is §7.5's stated fallback.** Transient
world-attached sources (impact, shards) move to the film grid. **Sustained ones
(engine, tyres) stay warped**, because their clock handling is the engine
workflow's to change and the spec is explicit that whoever lands second must not
revert the first. The two changes are disjoint by construction: they touch
different call sites.

## R2-4036 — A 30 Hz 4th-ORDER HIGH-PASS, BEFORE THE PROGRAM GAIN

The only low cut in the chain was a 12 Hz DC block, and **sub-30 Hz content
nobody can hear was 85.1 % of the film's energy** (beat 3: 89.9 %). That is
headroom, and therefore limiter gain reduction, spent below the ear's own
rolloff. Placed before the program gain so the gain is computed from the signal
that will actually be delivered.

## R2-4037 — ONE LIMITER PASS, REPORTED HONESTLY

The 8-pass loop is deleted, and so is the second 8-pass 48 kHz loop (`gr3`).
The makeup gain is now **solved for** rather than accumulated: each attempt
starts again from the same unlimited signal and applies **one** limiter pass, so
the delivered master has been through `soft_limit` exactly once however many
attempts it took to land −14 LUFS. `max_gain_reduction_db` is the **max over
every attempt**. If one pass cannot hit the target within 3 dB of reduction the
MIX is wrong, and the build says so rather than iterating until it stops
complaining.

## R2-4038 — THE BUILD NOW HAS A VERDICT ON ITS OWN MIX

`rep["chain_checks"]` asserts G1 (limiter GR ≤ 3 dB), G14 (premix peak ≤ +6
dBFS) and G15 in the place where the numbers exist, and `main()` exits non-zero
with `>> STAGE RESULT: AUDIO_MASTER_MIX_FAILURE` if any fails. **The master is
still written** — an artefact you cannot measure is not evidence — but it is not
signed off.

---

# THE GATE REPLACEMENT — R2-4039 to R2-4050

> Implements the gate half of `docs/audio-rebuild3/SPEC-ENGINE-AND-GATES.md`.
> The synthesis half (`master.py`, `layers.py`, `dsp.py`) belongs to a parallel
> agent and **was not touched**. Files owned here: `audio/verify.py`,
> new `audio/percept.py`, new `audio/controls/`, new `tools/percept_matrix.py`.

## R2-4039 — THE HEADLINE, WITH THE NUMBER THAT MATTERS

`tools/percept_matrix.py --adjudicate`, on `audio/out/master.wav`:

```
adjudication FAIL  ['G-BALANCE','G-FLAT','G-GESTURE','G-HNR','G-MOD',
                    'G-NOVEL','G-ORDER','G-RING','G-ROOM']
```

**The delivered master fails all nine quality gates.** Under the old suite it
passed all eight, three times, and was rejected by the client three times. The
audit's decisive exhibit, `tmp/gateaudit/swap_b1_loop.wav` — beat 1 replaced by
a 2 s block tiled 16.5x, `ALL_PASS=True`, exit 0 — now fails eight.

Every failure names its own mechanism, and each matches a number the audit
measured independently:

| gate | reads | the audit's own number |
|---|---|---|
| G-NOVEL | `r=0.343 at lag 1.380 s` | envelope autocorrelation 0.396 @ 1.380 s |
| G-MOD | `16.71 dB peak at 0.727 Hz` | single 0.722 Hz modulation peak |
| G-HNR | `median +0.26 dB, 46.1 % of windows below 0 dB` | +0.52 dB, 42.1 % |
| G-FLAT | `median 0.922*W, worst slice 0.973*W` | 0.98*W, min slice 0.91*W |
| G-RING | `worst band T60 3.35 s at 713 Hz > 3.00 s` | T60 3.0–4.6 s vs a declared 2.4 s |
| G-ROOM(b) | `0.612 of peak observations recur in >=3 bursts` | room 68 %, dry source 32 % |
| G-BALANCE | `near-white stems carry 1.000 of beat power; protagonist −3.30 dB` | 92.6 %; −12.01 dB |
| G-ORDER | `4_transit: 0.234 of 300–4000 Hz energy on telemetry-predicted lines` | new measurement |
| G-GESTURE | `worst pair 0.808` | ≈0.95 |

## R2-4040 — DELETED: 629 LINES, NOT RECALIBRATED

`audio/verify.py` loses `hnr_profile`, `harmonic_gate`, `control_harmonic`,
`_hairdryer_like`, the whole `BEAT_HNR_LIMITS` table and every `HNR_*`
constant, plus `pipe_modes`, `waveguide_gate`, `control_waveguide` and the
`WAVEGUIDE_*` constants. 1957 lines → 1387. A block comment stands where they
were with the measured reason for each, so the next person finds the reasoning
and not a hole.

Recalibration was never on the table: a literal hair dryer in a rack of tubes
passed beat 1's limit with **more** margin than the master (0.481 vs 0.708
against 0.85), and the same gate scored a 2 s tiled loop at **+43.8 dB**, 5.4x
the film's best beat. An instrument that reads the same whether the defect is
present or absent cannot be fixed by moving its threshold.

## R2-4041 — THE SELF-REFERENTIAL CALIBRATION RULE IS NOW BANNED IN CODE

`verify.py:816`'s rule — *"the limit is the midpoint between what THIS master
reads and what the adversary reads"* — is the defect in its purest form. Every
threshold in `audio/percept.py` is a frozen `Threshold(key, value, units,
source, note)` and `audit_thresholds()` **rejects `source=artefact` by name**.
`percept_matrix` runs that audit at step 0 and exits 2 with
`PERCEPT_THRESHOLDS_INVALID` before it will run anything else.

Watched to fire:

```
X.midpoint_between_master_and_adversary  source=artefact
  -> BANNED: a threshold derived from the artefact under test. This is
     verify.py:816's rule and it is the reason three rebuilds shipped
     without anyone knowing they were bad.
PASS = False
```

A second rule fires too: a threshold with no derivation note is a violation —
*a bare number is not a threshold*.

Current registry: **25 thresholds, 0 violations** — 8 `physics`, 1 `published`,
16 `control-derived`.

## R2-4042 — THREE INSTRUMENTS WHERE THERE WAS ONE NUMBER

Collapsing flatness, harmonicity and order structure into one median was the
original mistake, so they are three gates with three thresholds and three
verdicts.

* **G-FLAT** — spectral flatness computed *inside* each 1/3-octave band and then
  averaged, 500–3000 Hz, per 3 s slice, against white through the identical
  pipeline. Tilt-free by construction: the whole-band SFM reads a reassuring
  0.0142 on the delivered master and that number is measuring low-frequency
  tilt, not tonality. C7 (master + a −4 dB/oct tilt) is the control that proves
  it. Source: **control-derived**.
* **G-HNR** — Boersma (1993) autocorrelation HNR, in-repo, no GPL dependency.
  The normalised autocorrelation of the windowed signal divided by the
  autocorrelation of the window. A **periodicity** test, so noise through a
  high-Q resonator scores near 0 dB however narrow its peaks are. Source:
  **published** for the method, **control-derived** for the +8 dB bar
  (10·log10(0.85/0.15) = 7.53 dB), **physics** for the 0 dB line.
* **G-ORDER** — fraction of 300–4000 Hz energy within ±1.5 % of
  f = order·k·rpm/60, **rpm from telemetry**, Doppler-shifted by the render's
  own retarded-time solve. Carries its own wrong-fundamental control in every
  row. Source: **control-derived** + **physics**.

## R2-4043 — THE INSTRUMENTS RE-VALIDATE THEMSELVES ON EVERY INVOCATION

`calibrate_hnr()` and `calibrate_flat()` run inside the gates, on synthetic
mixtures of a 145 Hz comb and bandpassed noise at **known** aperiodic fraction,
and G-HNR **refuses to return a verdict** if its own calibration fails.

```
noise 0.02  truth +16.90  measured +17.03  err +0.123
noise 0.05  truth +12.79  measured +12.89  err +0.103
noise 0.10  truth  +9.54  measured  +9.66  err +0.122
noise 0.25  truth  +4.77  measured  +4.97  err +0.202
noise 0.50  truth  +0.00  measured  +0.40  err +0.402
noise 0.75  truth  -4.77  measured  -3.83  err +0.945   (reported, not gated)
```

The residual is positive everywhere — a peak-of-N-lags bias — so the instrument
reads **lenient**, never strict, and cannot manufacture a failure. +0.12 dB at
the +8 dB bar, +0.40 dB at the 0 dB bar.

`calibrate_flat` publishes the mapping the G-FLAT bars actually mean, every
run: a pure harmonic comb reads **0.126·W**, and **0.45·W ≈ 11 % aperiodic**.

`tools/calibrate_hnr.py` adds the third opinion the spec asks for — Praat, via
`praat-parselmouth`, **GPL-3 and dev-only**, imported there and nowhere else,
absent from any requirements file, and fenced: `verify.scan_external` FAILS if
that name ever appears under `audio/`. What it found is worth writing down
rather than smoothing over:

```
 noise   truth   in-repo    err     praat    err
  0.02  +16.90   +17.03   +0.123    +7.79   -9.12
  0.10   +9.54    +9.66   +0.122    +8.97   -0.57
  0.50   +0.00    +0.40   +0.402    +1.13   +1.13
```

Praat's **default** configuration diverges hard at low noise fractions — 70 Hz
minimum pitch, 4.5 periods per window, a speech silence threshold, and a median
taken over a track that includes its own edge frames. **The arbiter is the
arithmetic, not Praat**: the mixture's true HNR is 10·log10((1−f)/f) by
construction and the in-repo implementation tracks it to ≤ 0.40 dB. Praat is
reported in full and is not treated as ground truth.

## R2-4044 — G-RING REPLACES `waveguide`, ON THE WAV, AGAINST SABINE

`waveguide` root-solved `engine.py`'s constants at a hand-picked
`WAVEGUIDE_RPM = 11000` (passing at 4.852 against a 5.0 limit — a 3.0 % margin,
and failing at the film's own rpm_at_vmax of 13,143), never opened the wav, and
could not see `layers.assembly` or the showroom FDN, which is where the ringing
was.

G-RING measures per-1/6-octave T60 by **Schroeder backward integration** in the
film's own inter-event gaps, on the rendered stereo master, over all layers, and
compares it to:

1. the **Sabine RT60 of the declared showroom** (30 × 22 × 6.5 m, V = 4290 m³,
   S = 1996 m², α = 0.144 → 2.40 s) × 1.25 tolerance — `source=physics`;
2. the **broadband decay over the same gaps** × 1.5 — a band that decays slower
   than the field is an under-damped isolated mode by definition, not a room.

On the delivered master: broadband T60 3.29 s, worst band **3.35 s at 713 Hz**,
against a 3.00 s limit. FAIL.

## R2-4045 — SIX GATES WITH NO PREDECESSOR

* **G-NOVEL** — envelope autocorrelation of the 40-band, per-band normalised
  log-spectrum envelope, lags 0.3–16 s. Only **prominent local maxima** count:
  an earlier version took `max(r)` and read 0.726 on a constant-rpm power unit
  with nothing repeating in it, because slow drift decays monotonically from
  lag 0 and the max lands on `lag_min`. A period is a peak, not a trend.
* **G-MOD** — modulation-spectrum peak over a smooth cubic baseline in
  log-frequency, 0.2–3 Hz, **Welch-averaged**. Both corrections were forced by
  measurement: a single periodogram's own null is ~8 dB (the max of ~90
  exponential bins over its median), and a linear-width local median read
  13.74 dB on a monotone 1/f shoulder with no peak in it.
* **G-GESTURE** — pairwise correlation of per-burst 24-band × 6-subframe
  log-spectra, each referenced to the 200 ms **before its own onset**. A gesture
  is what the onset adds, not what was already sounding.
* **G-ROOM** — (a) are the room's *fixed* lines harmonics of a delay length;
  (b) peak recurrence across bursts; (c) cepstral and 1/12-octave ripple in the
  tails.
* **G-BALANCE** — stem-level near-white power share and protagonist margin,
  measured on stems because *the mix is the final flattening step*.
* **G-CONSTRUCT** — AST: no `white()`/`pink()`/`brown()` may reach a bus without
  an event scheduler or a physically-parameterised filter carrying a derivation
  comment.

## R2-4046 — INAPPLICABLE IS A DISTINCT OUTCOME AND NEVER COUNTS AS PASS

The old `harmonic` gate on pure noise reported `failures: []` and tripped
`undeclared_unmeasurable`: it said *"I cannot measure this"*, never *"this is
noise"*, and that read as green.

Every percept gate returns `PASS` / `FAIL` / `INAPPLICABLE` per beat and per
limb, `INAPPLICABLE` rows carry a measured reason, and `quality_pass` requires
every gate to have actually measured something. On the constant-rpm positive
control, G-GESTURE, G-ROOM(b) and G-RING are INAPPLICABLE — there are no bursts
and no decays in a steady engine — and they are reported as such, not passed.

Three applicability decisions are measured from the audio rather than declared:
G-ROOM(c) stands down below 0.75 band occupancy (a tonal bed's "ripple" is the
silence between its partials — it read 113 dB); G-ROOM(a) stands down below six
fixed lines (with no fixed reply there is no room comb); G-ORDER stands down on
beats with no telemetry rpm on throttle.

## R2-4047 — `verify.py` NO LONGER CLAIMS A QUALITY VERDICT

Three of the old eight gates never opened the wav and all three passed 100 %
white noise on 5 of 5 degenerate inputs. They are now labelled and separated:

```
>> quality   : {"levels": true, "edges": true, "doppler": false}
>> provenance: {"external_assets": true, "pitch": true}   (excluded from the verdict)
>> advisory  : {"seam": true}                             (a PASS here proves nothing)
```

`pitch` is kept and still required to pass — "the source tracks the telemetry"
is worth proving — but it re-synthesises the dry engine and measures *that*, so
it is excluded from the quality verdict. What replaces it as a quality test is
G-ORDER, on the delivered master, against the same telemetry.

`seam`'s PASS is advisory, and the note says why with numbers: it adjudicates
**20 samples of 5,956,000** and its own 3 dB-step positive control *passes* on
broadband material. A seam FAIL still stops the build.

`levels` now cross-checks its hand-rolled K-weighting against **pyloudnorm**
(MIT, ITU-R BS.1770-4) and fails on a disagreement over 0.3 LU. Measured:
−14.001 LUFS in-repo vs −14.044 reference, Δ **0.043 LU**. A meter nobody
cross-checks is how a level error ships.

## R2-4048 — SPLICE DETECTION IS NOW FILM-WIDE, WITH ITS TEETH FROM AN INJECTION

`splice_scan` walks the whole file (497 windows, 100 % coverage) and ranks
candidates by |3rd difference| peak over the **rolling local median**. It
carries **no absolute threshold, on purpose**: the breach is a legitimate 562x
local-median event at 36.02 s and any global bar that failed it would be a bar
demanding the film not have a breach.

What is gated is the gate's own sensitivity, by injection: a 977-sample splice
at t = 20.0 s — 13 s from the nearest beat boundary, where the boundary gate
cannot look at all — lifts its own location from **4.5x to 38.5x**, an 8.5x
lift against a required 5x.

## R2-4049 — THE DOPPLER GATE IS EXTENDED, AND PORTABLE BEFORE B7

`doppler` was the only load-bearing gate in the old suite (it failed all three
whole-file degenerates) and it saw **85 windows in one 4.2 s span**, 3.38 % of
the film, all inside beat 5 — which is why it passed both beat-1 swaps with
numbers bit-identical to the master's.

It now runs the same measurement at **every local maximum of closing speed
above 15 m/s** in the retarded-time solve. On the delivered master: 3 stations,
**1 PASS, 1 FAIL, 1 INAPPLICABLE**.

```
 t =  65.17 s  INAPPLICABLE  tracker locked on 0 of 64 windows
 t =  94.64 s  PASS          med 5.4 c, p90 58.7 c, corr 0.997, fail frac 0.059
 t = 106.76 s  FAIL          med 132.4 c, p90 325.3 c, corr 0.677, fail frac 0.365
```

t = 94.64 s is the declared station and it is the one the old gate measured. A
FAIL at any station now fails the gate; an INAPPLICABLE station contributes
neither way — and t = 65.17 s is INAPPLICABLE by design rather than FAIL,
because the comb search locked on **zero** windows there and asserting a Doppler
defect from a measurement that did not happen is the same error as calling an
unmeasurable beat a pass, pointed the other way.

`ENGINE_ORDER = 3.0` is now a module constant that both `pitch` and `doppler`
read, with the porting note in the report itself. **B7 halves the firing
fundamental to order 1.5 and must change this line before that render**, or
every station reports a tracker failure fraction that looks like a broken
Doppler and is not.

**Open item for whoever adjudicates:** the FAIL at t = 106.76 s is new coverage
and has never been measured against a known-good master. It may be real (this
master is the rejected artefact and fails everything else) or it may be the
tracker meeting the tyre-scrub source at distance — it locked on 54 of 85
windows, so it is a partial lock with real disagreement, not a non-measurement.
It is reported per station with window counts so the question is answerable, and
it is not quietly excluded.

## R2-4050 — THE PERMANENT CONTROL CORPUS: NINE CONTROLS, ALL CORRECT

`audio/controls/` — **synthesised only, no recordings, ever**. Deliberately
self-contained: it does not import `layers.py` or `dsp.py`, because a control
that moves when the thing it is controlling moves is not a control.

```
C1_octave_matched_noise        req FAIL got FAIL  G-FLAT,G-HNR,G-ROOM
C2_tiled_loop                  req FAIL got FAIL  G-FLAT,G-GESTURE,G-MOD,G-NOVEL,G-ROOM
C3_blower_plus_tubes           req FAIL got FAIL  G-FLAT,G-GESTURE,G-HNR,G-ORDER,G-ROOM
C4_delivered_master            req FAIL got FAIL  all nine
C5_swap_b1_loop                req FAIL got FAIL  eight
C6_jittered_identical_gestures req FAIL got FAIL  G-GESTURE (+ passes G-MOD, contract met)
C7_master_plus_tilt            req FAIL got FAIL  G-FLAT (tilt-immunity proven)
C8_constant_rpm_pu             req PASS got PASS  -
C8b_physical_showroom_beat     req PASS got PASS  -
```

**C4 is the single most important line**: the delivered, rejected master is
retained permanently as a negative control that must fail. **C6 is the
anti-cheat**: identical gestures on a jittered grid must fail G-GESTURE and
**PASS** G-MOD (it reads 4.51 dB against a 6.0 dB bar), so "just add jitter"
cannot buy a pass — and that contract is machine-checked, not written down.

The **positive** half is load-bearing too: without C8 and C8b a suite that
failed everything would look finished. C8b is a beat 1 built the way the spec
says to build it — geometric-contraction schedule, one CFRP plate geometry per
part, Hertzian excitation clamped to the spec's 0.4–2.5 ms, gravity-derived
arrivals, velvet-noise late field with two independent L/R sequences, and a
per-cluster servo bed carrying the tonal content between arrivals.

`percept_matrix` runs the corpus **FIRST** and, if any control returns the wrong
verdict, reports the master as **`UNDEFINED` and unreported**.

## R2-4051 — EVERY GATE WATCHED TO FIRE: 12 OF 12 MUTATIONS

*A guard is not fixed until it has been watched to fire.* Each gate's own defect
is deliberately re-injected into a signal that otherwise passes.

```
M-FLAT   broadband bed over the physical beat           G-FLAT      FIRED
M-HNR    noise through fixed high-Q pipes at beat level G-HNR       FIRED
M-NOVEL  2 s block tiled over the physical beat         G-NOVEL     FIRED
M-MOD    gestures back on an exact 1.375 s grid         G-MOD       FIRED
M-GEST   one gesture repeated, jittered grid            G-GESTURE   FIRED
M-ROOMa  8-tap FDN, no diffusion: delay harmonics       G-ROOM      FIRED
M-ROOMb  fixed inharmonic resonator bank, no dry blend  G-ROOM      FIRED
M-ROOMc  master.py:530-532 self-delay comb re-injected  G-ROOM      FIRED
M-RING   tail at RT60 4.5 s in a 2.4 s Sabine room      G-RING      FIRED
M-ORDER  comb detuned 9 % off the telemetry rpm         G-ORDER     FIRED
M-BAL    near-white stem raised 26 dB (baseline PASSES) G-BALANCE   FIRED
M-CONS   three source fixtures that break the law       G-CONSTRUCT FIRED
```

M-ROOMa is worth quoting because it reproduces the diagnosis as a verdict:

> `1_assembly(a density): 1.00 of the 9 fixed lines are harmonics of 55.40 Hz
> (0.50 over chance) > 0.40 — the tail is a delay-line bank, not a field`

Two mutations were **wrong on the first attempt and the gate was right**:
`_fixed_resonators` kept 25 % dry and G-HNR did not move — correctly, because
filtering a periodic source through a resonator leaves a periodic source. The
mutation was fixed to inject the actual defect (noise through the pipes), not
the gate.

## R2-4052 — G-CONSTRUCT ON THE CURRENT TREE: 35 VIOLATIONS

The law — *no `white()`/`pink()`/`brown()` output may reach a bus without an
event scheduler or a physically-parameterised filter carrying a derivation
comment* — is enforced by AST exactly as `external_assets` is.

```
>> G-CONSTRUCT on 8 render-path modules: 35 violations, verdict FAIL
   dsp.py:187     w = white(n, seed)
   engine.py:427  jit = dsp.lp(dsp.white(n, seed + 1), 7.0, sr, 2)
   engine.py:527  pump = _sig.sosfilt(dsp.sos_band(120.0, 900.0, sr, 4), ...)
   engine.py:544  pops[a:a+L] += r.standard_normal(L) * env * r.uniform(...)
   ...
```

**This is expected and is not a defect in the gate.** The render path is being
rebuilt by the parallel agent under B2–B7; these 35 lines are its worklist.
`audio/controls/` is excluded (synthesising a hair dryer is its job) and the
exclusion is **checked, not asserted** — G-CONSTRUCT fails if any render-path
module ever imports it, and `verify.external_assets` re-checks the same thing.

## R2-4053 — DEVIATIONS FROM THE SPEC, DECLARED RATHER THAN QUIET

Three. Each is written into the threshold's own `note`, so it is in the report
and not only in this file.

**(1) G-FLAT's bars moved 0.45 → 0.55 (slice) and 0.30 → 0.45 (beat-1 median),
in the LOOSENING direction.** That is the direction that shipped three masters,
so it needs the full accounting. The spec's numbers were *asserted*, never
measured against a signal that should pass — there was no such signal when it
was written. Measured per 3 s slice on the shipped estimator:

```
                                   median   worst slice
  C8b physical construction         0.389      0.496
  blower-into-tubes                 0.639      0.661
  tiled loop                        0.669      0.700
  octave-matched noise              0.700      0.721
  DELIVERED MASTER                  0.922      0.973
```

0.30·W is unreachable by a construction that follows the spec's own B3/B4/B6:
a 1/3-octave band at 500 Hz is 116 Hz wide, so a servo comb above f0 ≈ 115 Hz
has at most one harmonic inside it and per-band SFM cannot score it as tonal.
That is a limit of the instrument, not of the build — the same bed reads
**+45 dB** on G-HNR. The bars were moved by a **synthesised positive control**,
never by any master; the rejected artefact still fails by 2.4x; every degenerate
still fails. **Flagged for the spec owner.**

**(2) G-ROOM(a) does not gate Weyl's law.** 4πVf²/c³ = 1336 modes/Hz at 1 kHz
for 4290 m³ cannot be *counted* at any audio resolution — at 1 Hz FFT
resolution the ceiling is ~0.5 resolvable peaks/Hz. The Weyl number is reported
for reference; what is gated is the executable equivalent, that a delay-line
bank's fixed lines are harmonics of a delay length, with a **two-sided** anchor
(an 8-tap FDN scores 1.00 over 0.50 chance; five inharmonic pipes — also fixed,
also narrow — score at chance).

**(3) G-IDENTITY is not implemented.** It gates order-1.5 amplitude and the
order-6 notch, which exist only after B7's `half_order_weight`. Today's engine
has order-1.5 amplitude identically 0.0000, so the gate would be a row that can
only fail. It belongs with B7 and is listed there rather than shipped as a
guaranteed-red light.

## R2-4054 — SIX INSTRUMENT BUGS FOUND BY THE POSITIVE CONTROLS

Every one of these would have been a false FAIL on a good master, and every one
was found because the suite has a signal that is *required to pass*. Recorded
because they are the same class of error as the defect being fixed — a metric
measuring its own floor.

1. **Silence read as perfect flatness.** Every bin of an empty frame lands on
   the same numerical floor, so its SFM is exactly 1.0. A five-mode decaying
   ring measured **1.65·W — flatter than white noise**. Frames 50 dB under the
   band's own p95 are now dropped.
2. **`find_bursts` had no magnitude criterion**, so on a steady tone it returned
   40 "bursts" that were of course all identical: G-GESTURE 0.999, G-ROOM(b)
   1.000, on a physics-true constant-rpm power unit. Now requires a 6 dB rise.
3. **Envelope decimation without an anti-alias filter** folded a harmonic
   source's own f0 ripple into the modulation band: an 8.1 dB "modulation peak"
   at 2.909 Hz that *moved when the rpm moved*.
4. **`decay_regions` demanded a monotone fall** and found **zero** regions in
   the delivered master's beat 1 — a beat with twelve bursts and ~1 s of naked
   reverb after each. G-RING was silently INAPPLICABLE with a 3.35 s ring in
   front of it.
5. **A straight fit to the raw band envelope** gives R² = 0.23–0.37 on real
   tails, so any honest goodness-of-fit guard rejected every band. Replaced with
   ISO 3382 Schroeder backward integration (R² > 0.95).
6. **A T60 guard of `slope < -0.5 dB/s`** turned a sustained tone inside a
   broadband gap into *"T60 = 115.25 s at 400 Hz"*.

## R2-4055 — HOW TO RUN IT

```
python -m tools.percept_matrix                      # corpus + mutations
python -m tools.percept_matrix --adjudicate         # ... then judge the master
python -m tools.percept_matrix --only C4_delivered_master
python -m audio.verify --skip-plots                 # levels/edges/seam/prov/doppler
```

Report: `audio/out/percept_matrix.json` (every threshold with its `source`,
every control row, every mutation row, the full per-beat detail).

## R2-4039 — THE PANE: 4.7 kHz CEILING, PLASTIC DAMPING, AND A POINT LOAD IT NEVER FELT

Four defects, all parametric, all measured.

**The mode set stopped just above the critical frequency it was being weighted
against.** `plate_modes` looped `for m in range(1,26): for nn in range(1,26)`,
and with m,n ≤ 25 the highest frequency the formula can produce for a
2.125 × 5.600 m pane is **4673.6 Hz**. `glass_wall` then weighted those modes by
radiation efficiency about **f_c = 1004 Hz** — correctly — and selected from a
set that dies just above it. **The entire band in which a 12 mm pane actually
radiates, 1 kHz to 20 kHz, was never computed.** Not attenuated: absent.

The index limits are not free parameters. Modal density is analytic and
constant, `dN/df = πab/(4k)` with `k = (π/2)√(D/ρh)`: D = 10593 N·m, ρh = 30,
k = 29.52, so **0.3166 modes/Hz** and 6333 modes below 20 kHz. Reaching 18 kHz
needs m ≤ 52, n ≤ 138.

| | before | after |
|---|---:|---:|
| modes at `fmax=18000` | 625 | **5605** |
| ceiling | **4673.6 Hz** | **17992.5 Hz** |
| modes above 4718 Hz | **0** | **4163** |
| measured modal density (G8 target 0.314 ±25 %) | 0.134/Hz | **0.312/Hz** |
| rendered | 72 | 400 |

**Damping.** `q=45` is a loss factor η = 1/Q = **0.022** — that is plastic. The
pane was rendered ~22× too dead, T60 at 3 kHz = **10.5 ms**. Replaced with
`plate_q`: Q 400 below 500 Hz (boundary/joint dominated), ramping to 1000 at
2 kHz, 1200 above (material dominated, annealed soda-lime η ≈ 1e-3). **T60 at
3 kHz becomes 0.70 s.** The frequency dependence is itself a material cue.

**Coupling.** The uniform odd-odd `1/(mn)` rule is kept for the acoustic
pre-load from the approaching car — a uniform pressure genuinely couples that
way. But the nose is a **point load**, so the strike uses
`sin(mπx₀/a)·sin(nπy₀/b)` (`point_coupling`), which couples to every mode there
is. Using the uniform weight for a strike is what leaves a struck pane sounding
pressed.

**Radiation efficiency is a POWER ratio, so an amplitude scales as √σ = f/f_c,
not σ = (f/f_c)².** Getting that wrong is a factor of two in dB — 25.3 vs
50.6 dB at 54.4 Hz. `rad_amp` is the amplitude form and is used everywhere a
signal rather than an energy is weighted.

## R2-4040/4041 — THE SHARDS: THREE PURE SINES, AND LOUDNESS AS THE RECIPROCAL OF PITCH

**Defect A, and it was two lines apart in the same function:**

```python
m   = GLASS_RHO * GLASS_H * L * L   = 30 L^2         # ballistics
f1  = 0.47 * (GLASS_H / (L*L)) * c_L = 30.59 / L^2   # ballistics
amp = m * vz_in                                      # ballistics
```

`amp = 917.7·vz/f1`. **A big slab is loud and low; a bright chip is silent.**
Measured over 995 contacts: slope of log-amp against log-f₁ = **−0.994**, the
top ten contacts carry **32.1 %** of all shard energy, and **all ten ring at
54.4 Hz** — the L = 0.75 m size clamp.

**Defect B:** ratios `1 : 2.08 : 3.41`, one shared exponential decay for all
three modes, and a 0.4 ms DC bump. Every shard in the film had one spectrum,
transposed. **That is the textbook construction of a struck bar** — it is not
like the client's "banging on tubes", it is that.

**Rebuilt:**

- **8–14 modes per shard** (measured mean **11.05**), from a per-shard aspect
  ratio `r ~ lognormal(0, 0.35)` treated as a free plate of sides `L√r, L/√r`,
  each mode jittered by `lognormal(0, 0.08)`. The rectangular formula splits the
  degenerate (m,n)/(n,m) pairs by an amount that depends on r, so the spectrum's
  **shape** varies shard to shard, not only its pitch.
- **Per-mode decay** `τ_n = Q/(π f_n)`, Q drawn 800–1500 per shard. Measured on
  a rendered single shard: **Q = 942**, identical across its modes (G10 target
  500–2000; before: 45).
- **Radiation efficiency + a size high-pass at ka = 1** (`f = 109.2/L` Hz, first
  order). Both make brightness a consequence of size rather than an authored
  table.
- **Acceleration noise instead of the DC bump**: `d/dt` of the Hertzian contact
  force is exactly one sine cycle at 1/T, so the transient's bandwidth is set by
  contact hardness and nothing else. The old bump's spectrum peaks at DC — a
  click with no transient in it, which the chain's high-pass then removes,
  leaving the shard with no attack at all.
- **Contact damping after the first bounce.** Q 800–1500 is a FREE plate. 64 %
  of the 995 contacts are second, third or fourth bounces — a piece skittering
  on concrete among other debris — and rendering those as free plates is both
  wrong and what turned a shower into a continuous tone bed.
- **Skitter.** Each shard's last contact is followed by 0.3–1.5 s of `scrape`:
  a stylus reading a spatial roughness profile at the sliding speed, so pitch
  and brightness fall together as the piece slows. The delivered field stopped
  dead.

| shard population | before | after |
|---|---:|---:|
| slope, log-amp vs log-f₁ | **−0.994** | **−0.721** |
| top-10 energy share | **32.1 %** | **10.7 %** |
| top-10 ring frequencies | **all 54.4 Hz** | 55–144 Hz, all distinct |
| energy above 2 kHz | 0.0039 % | **0.184 %** (47×) |
| modes per contact | 3 | **11.05** |
| **G9** slope of log f₁ vs log L (target −2.0 ±0.1) | −2.0 by construction | **−1.972** |
| **G10** per-mode Q (target 500–2000) | **45** | **942** |

## R2-4042/4043 — THE BREACH AS FIVE LAYERS, OFFSET BY PHYSICAL DELAYS

`impact_event` was a 41/58/79 Hz thud, a mullion, a crunch, a dust whoosh and
one 30 ms wideband burst. It measured **92.99 % below 30 Hz** and a spectral
centroid of **14.0 Hz** on the world grid.

t = 0 is contact. Each layer is placed by r/c:

1. **Fracture rip.** 420 crack sites scattered over the pane, each delayed by
   its own distance / **1716 m/s** (0.55 c_R for soda-lime). So the rip has a
   DURATION set by the pane's size and the material's wave speed — **1.24 ms**
   across the 2.125 m span, **3.26 ms** across the 5.6 m one — instead of being
   a single burst with no size information in it. 3–7 kHz core.
2. **Pane modal collapse.** The full 5605-mode bank, selected to 400, driven
   through `struck_plate` by a **0.25 ms Hertzian point load** at the strike
   position, gated off 40 ms after contact because by then there is no pane.
   Normalised on the RMS of its first 100 ms, not on its peak: a 400-mode bank's
   peak is one sample of constructive interference and says nothing about how
   loud the collapse is.
3. **Delayed flexural**, +65 ms, 196/231 Hz, heavily damped. A real and
   distinctive feature of glass breakage that this file did not have at all.
4. **Shard shower** (R2-4041), film-grid scheduled.
5. **PhISEM debris bed** (R2-4044).

**The sub layer is kept and cut from 0.85 to 0.22.** It is the felt weight of a
car arriving and it belongs in the film — but at 0.85 it WAS the film: the
impact bus measured 77.1 % of its energy below 100 Hz, a centroid of 79 Hz, and
a **50 ms crest of 4.4 dB**, i.e. less peaky than white noise, for the sharpest
event in the picture. It also now has a 1.5 ms attack, so the sub arrives rather
than fading up.

**The mullion physics was already right and is kept** — free-free beam,
f₁ = 31.6 Hz, β = 4.730/7.853/10.996/14.137, implied Q = 89, correctly
joint-dominated for a bolted extrusion. One fix: the higher modes decayed by an
ad-hoc `1/(k+1)^0.6`, which is not a damping law. A single loss factor gives
`τ_k = 1/(π η f_k)`, so higher modes die faster because they are higher.

## R2-4044 — THE PhISEM DEBRIS BED, AND WHY NOT MORE SHARDS

A 12 mm architectural pane does not break into 351 pieces. The ballistic sim
integrates the foreground fragments; everything below them is a stochastic
particle system — Cook's PhISEM — whose collisions excite a five-resonator bank
at 3–8 kHz, Q 20–60.

**The rate is not a drawn curve.** It is the ballistic sim's own contact
schedule in film time, smoothed, times a fines multiplier of 34 — so the bed
thickens and thins exactly where the shower does, stretch included, with no
second timing model to keep in sync. **34,100 fine events** at a peak intensity
of **24,706/s**, costing **five biquads**, because the whole Poisson train is
filtered once rather than synthesised event by event.

Measured on the bed alone over 36–44 s: **centroid 6532 Hz, 86.5 % of its energy
above 4 kHz, 50 ms crest 16.5 dB.**

**Deviation from the spec, stated:** §2.3 asks for a cross-fade of layer 4 into
layer 5 by shard size, foreground = the largest ~200 shards. **Not done, because
the measurement says there is nothing to fade out.** The smallest shard the sim
draws is **40.2 mm** — above the 26.6 mm hole — so removing the smaller 151
shards from layer 4 would delete content rather than move it into the bed. The
bed is additive here and closes the fines gap from the other direction, which is
what §2.3 says it also does.

## R2-4045 — THE REVERB WAS DECLARED 4 dB ABOVE THE THING MAKING IT

`TARGET_LUFS_S` set `room = −23.0` and `assembly = −27.0`. Measured on the
shipped stems over 0–33 s: assembly RMS −36.75 dBFS, room RMS −36.82 dBFS — a
wet/dry ratio of **−0.07 dB**, with the reverb carrying **45.9 %** of the first
thirty-three seconds.

Worse, the reverberant field was spectrally *identical* to the direct sound:
wet−dry tilt flat to ±1.1 dB from 125 Hz to 16 kHz, and the reverb **louder than
the dry at 4–8 kHz**. No room does that — every reflection loses high frequency
twice, at the surface and in the air, and a 2.4 s tail is 800 m of travel. A
full-bandwidth undamped 1.1 s tail at equal amplitude on every clunk is a bright
ringing copy of each hit, which is what a struck tube sounds like and what a room
does not.

- `room` **−23.0 → −31.0 LUFS-S** (4 dB *below* the dry bus).
- `showroom_tail` **rt60_high 0.85 → 0.35 s** above 4 kHz, against 2.4 s low.
  The FDN's per-line damping already implemented this exactly; the number was
  simply set too high.

## R2-4046 — WIND: TWO EXPONENTS, STROUHAL TONES, AND GOODY

It was the loudest thing in the lap and it was `brown` buffet plus `pink` edge
hiss on one gain curve. One noise source with one gain curve does not read as
SPEED, it reads as a fader move.

1. **Two source families with different velocity exponents.** Dipole (edges,
   wings, mirrors) intensity ~ U⁶; quadrupole (underbody, wake) ~ U⁸. **The wake
   must overtake the edges as the rig accelerates**, and that crossover is what
   a listener hears as "faster" rather than "louder".
2. **Vortex shedding, one noisy oscillator per bluff feature**, at
   `f = 0.2·U/d`. This is the third mechanism §3.1 demands: a self-sustained
   oscillator with phase noise, which is neither of the file's two generators. A
   resonator on white noise has the same power spectrum and none of the
   waveform — it never completes a cycle.
3. **Goody's wall-pressure spectrum** (ω² rise, ω^−0.7 overlap, ω^−5 roll-off)
   with both corners tracking U, instead of pink noise's flat ω^−1.
4. **Large-eddy AM** at `U/(5δ)` for δ = 0.8 m: 2 Hz at 8 m/s to 20 Hz at
   80 m/s, depth 5.4 dB.

Measured, 3 s at each steady speed:

| U | 27.8 | 41.7 | 55.6 | 83.3 m/s |
|---|---:|---:|---:|---:|
| level | −35.14 | −22.91 | −13.89 | **−0.67 dBFS** |
| **spectral centroid** | **699.7** | **1090.4** | **1503.8** | **2364.2 Hz** |
| 50 ms crest | 10.60 | 11.50 | 11.93 | **12.13 dB** |

Each step sits **between** the U⁶ and U⁸ predictions and moves toward U⁸ at
speed (+13.22 dB measured against 10.53 for U⁶ and 14.05 for U⁸ over the last
step) — which is the quadrupole overtaking, measured rather than asserted. The
centroid is very nearly linear in U (25.2 Hz per m/s at the bottom, 28.4 at the
top). Shedding tones land at exactly **106.7 / 320 / 800 / 3200 Hz at 80 m/s**,
the spec's four figures. And the crest is now **above** Gaussian white noise at
speed, where before the layer *was* Gaussian white noise.

## R2-4047 — TYRES: A FRICTION LIMIT CYCLE, AND THE CAVITY SPLIT

**Squeal was `sin(f) + sin(2.02f) + sin(3.05f)` with f driven by slip velocity.**
Three pure sines: the file's second generator wearing a tyre.

Real squeal is **stick-slip**. `stick_slip` integrates a tread element as a mass
on a spring dragged across the road under Coulomb friction with velocity
weakening, `μ(v) = μ_k + (μ_s−μ_k)·exp(−|v|/v_c)`, μ_s/μ_k = 1.4, v_c = 0.15 m/s.
`dμ/dv < 0` is negative damping, so the element self-excites into a relaxation
oscillation — sticking, breaking away, snapping back — which is what squeal *is*
and why noise never sounded like it. Integrated per-sample only where there is
slip to drive it (**2.4 %** of the world grid, 4.0 M samples, ≈6 s).

**The first version of this was wrong and the measurement caught it.** With
`m = 1` normalised, the friction force was of order 1 N against a stiffness of
1.8e7 N/m: the element deflected 7e-8 m, the velocity-weakening term sat five
orders of magnitude below the viscous damping, and the "oscillator" was a lightly
rung resonator — **50 ms crest 0.18 dB and zero harmonic content above 900 Hz**,
i.e. a sine. Self-excitation needs `N(μ_s−μ_k)/v_c > 2ζmω₀`, which with a real
0.15 kg tread element under a real 1500 N is **3600 against 12.6** and holds for
any slip velocity below 0.85 m/s.

| slip velocity | 0.05 | 0.20 | 0.50 | 1.00 m/s |
|---|---:|---:|---:|---:|
| emitted peak (element at 670 Hz) | 1980 | 516 | **656** | **668 Hz** |
| centroid | 3350 | 3290 | 716 | 677 Hz |
| **50 ms crest** | **8.42** | **7.33** | **8.29** | **5.63 dB** |

A sine scores 3.01 dB. The harmonic content collapses as slip velocity rises,
which is the physical behaviour: the weakening term saturates.

**Squeal frequency is set by load and slip ratio, not by road speed** — driven
here from the telemetry's own longitudinal load and downforce, gliding 670 → 850
Hz as load builds, which is the measured direction of real braking events.
**F1 tyres are slicks, so there is deliberately no tread-block passing
tonality.**

**Cavity resonance was one resonator at 165 Hz with no split.** Now three orders,
each **split fore-aft/vertical by 4 Hz per order** because the contact patch
flattens the torus and breaks its rotational symmetry — the pair beats slowly,
and that beating is the single most identifiable thing about a loaded tyre.

*Deviation, stated:* the spec computes f₁ = 343/1.850 = **185 Hz** from ambient
air. A racing tyre is filled with nitrogen at ~60 °C, where c = 366 m/s, giving
**197.7 Hz**. The hot-gas figure is kept — it was a deliberate prior decision in
this file and it is the physically correct one — and both are reported.

**One artefact found and fixed by measuring.** The raw element velocity at a
0.05 m/s slip peaks at **36.9 kHz**: the break-away is very nearly a
discontinuity. None of that reaches the air, because the motion is transmitted
through a rubber carcass whose own bandwidth is a few kHz. Without a 5 kHz
carcass low-pass the layer spent most of its energy above the delivery format's
Nyquist.

## R2-4048 — THE ASSEMBLY: FIFTEEN OBJECTS, ONE INSTRUMENT

Every one of the 616 part seats in beat 1 was the same four sines at
`1 : 2.31 : 3.87 : 6.1`, transposed by the cluster's bounding-box volume, sharing
one exponential decay. **Fifteen different objects, one instrument** — the other
half of "the instrument The Tubes over and over".

`cluster_modes` derives a mode set from each cluster's own geometry: **beam**
(free-free bending, β ratios `1 : 2.756 : 5.404 : 8.933`) when the longest
dimension exceeds 3.5× the depth, **plate** otherwise. Materials are assigned by
what an F1 car is made of — CFRP everywhere, aluminium at the four corners,
titanium for the halo — and the three numbers that matter are all synthesised:

- **specific stiffness** √(E/ρ) is 8600 m/s for CFRP against 5055 for aluminium
  and 3900 for titanium, so **carbon rings HIGHER than the metal it replaced,
  not lower**;
- **loss factor**, Q 65 for CFRP against 150–170 for the metals, so **carbon is
  shorter in time**, which is the actual cue;
- **orthotropy** splits mode pairs that would be degenerate in an isotropic part,
  by 2.5 % clipped to 20–50 Hz, so the pair beats over the first 20–50 ms.

**A correction the measurement forced.** The first version used the cluster's
bounding box directly, which made the monocoque's "thickness" 0.89 m and put the
front corner's fundamental at 5220 Hz and the steering wheel's at 16.5 kHz. A
cluster bbox is not a plate. Scaling by `n_parts^(1/3)` gives the linear size of
a typical member, and a wall thickness bounded to 2–12 mm gives what car parts
actually are:

```
  BB   plate cfrp      wall 12.0mm  f  398  418  700  720
  FD   beam  cfrp      wall 12.0mm  f  393  413 1097 1124
  MB   beam  cfrp      wall 12.0mm  f  666  686 1841 1888
  CORNER_FL plate aluminium         f 1032 2164 2996 4050
  halo_assembly beam titanium       f 2232 6153 12064 19941
  FW   beam  cfrp      wall 10.2mm  f 3618 3668 10016 10066
  SW   plate cfrp      wall  4.8mm  f 9958 10008
```

Fifteen genuinely different spectra spanning 393 Hz to 10 kHz, and each part
within a cluster is scattered rather than transposed. Assembly bus centroid over
2–30 s: **1255 Hz**. Each seat is driven by a Hertzian contact force whose
duration is the material pairing's — 0.6 ms carbon-on-carbon, 0.2 ms
metal-on-metal — rather than by a bare impulse, which excites an 18 kHz mode
exactly as hard as a 200 Hz one and is why every part sounded like the same part.

## R2-4049 — FOUR FAMILIES THAT DID NOT EXIST: BRAKES, SUSPENSION, SCRAPE

Grepping brake / damper / suspension / shift / gear / kerb across `audio/*.py`
returned nothing outside `engine.gear_and_rpm`. **Beat 6 is an 11.0 s
deceleration from 89.8 m/s to zero at up to −35.3 m/s², with no braking sound
available to it**, and 14.8 % of the world grid is under −3 m/s².

- **`brakes`** — carbon-carbon. The pad reads the **disc's own surface**, and a
  disc is a closed surface, so the roughness profile repeats once per revolution:
  that is where braking's characteristic grain comes from. Read at ω·r_disc, so
  pitch and brightness both fall as the car slows with no filter sweep involved.
  Five disc bell modes 1.5–4 kHz excited by the rub, plus caliper judder at the
  wheel rotation rate and its first two harmonics (36.7 Hz at 83 m/s, falling to
  nothing at the stop). Measured active over **17.8 %** of the world grid.
- **`suspension`** — a two-stage contact. The tyre is between the road and the
  car, so stage one is **rubber-mediated, T = 3–15 ms**, which by
  `hertz_spectrum` puts the excitation corner at 65–330 Hz: a thump with nothing
  above ~100 Hz in it, which is why a kerb strike sounds nothing like a stone.
  Stage two is the upright/wishbone beam modes 118 Hz–1.78 kHz at η = 1e-2.
  Triggered on load-transfer jerk from the telemetry: **16 events**.
- **`roughness_profile` / `read_roughness` / `scrape`** — §3.3 item 4, and the
  third mechanism for continuous contact. Build a surface once in SPACE with
  `S(k) ∝ k^−w` (w = 2.2 asphalt, 2.5 glass on concrete), then read it at
  `s(t) = ∫v dt`. Speed changes pitch and brightness together for free, and
  **there is no resampling artefact because nothing is resampled**. Used by the
  brakes and by the shard skitter.

Downshift/gearshift is `gear_and_rpm`'s and belongs to the engine workflow.
Flagged, not built.

## R2-4050 — THE TWO INAUDIBLE BUSES: RAISED WITH INTENT, WITH A DELETION RULE

`reflect_showroom` measured 25 dB under the mix everywhere and `aperture` 28 dB
— two buses costing full render time and existing only in the report. Both carry
a real cue (the facade reflection is what tells you there is a wall beside you
during the transit; the aperture is the showroom's own tail heard from outside,
through the hole the car just made), so both are raised rather than deleted:
`reflect_showroom` −25 → **−19**, `aperture` −27 → **−18** LUFS-S. **If they
still measure more than 15 dB under the mix after this they should be deleted
rather than raised again** — the point of §3.4 is to decide, and this is a
decision with a falsifier attached.

## R2-4051 — §7.1's ABANDONMENT TEST, RUN: THE CHAIN WAS NECESSARY AND NOT SUFFICIENT

The spec states this test in advance and calls it "the cheapest test in the plan
and it must be run first": land §4 alone, re-measure, and **if breach energy
above 4 kHz stays below ~1 % and crest under 12 dB, the §1 verdict is wrong and
the effort should move entirely to sources**.

It was run. The first render carried **the chain fixes and the film-grid
scheduling with every synthesiser untouched** — its log shows `structure` still
trimming +52.39 dB and the pane still at 351 modes, i.e. the old glass. It died
at its last statement on a reporting bug of mine (R2-4052) after producing every
mix-stage number:

| | delivered | chain only |
|---|---:|---:|
| premix peak | **+17.73 dBFS** | **+3.77 dBFS** |
| limiter max GR, honestly reported | **−22.76 dB** (reported as −0.124) | **−11.47 dB** |
| 30 Hz high-pass effect on the premix | — | peak **−1.55 dB**, loudness −0.04 dB |
| LUFS-I / true peak | −14.00 / −1.10 | −14.04 / −1.15 |

**The chain half of the verdict holds, and holds hard.** 14 dB of premix peak
and 11 dB of limiter gain reduction came off with no synthesiser touched, and
the 30 Hz high-pass took 1.55 dB of peak for 0.04 dB of loudness — the signature
of pure limiter fuel.

**The source half of the verdict does not.** The bench measures the breach at
its SOURCE, where the chain cannot add what is not there: with the old
synthesisers on the film grid, the shard bus carries **0.034 % of its energy
above 4 kHz**. No downstream stage can turn that into the 8 % G2 asks for. **The
chain-only master would have tripped the spec's own abandonment criterion.**

So the honest verdict is narrower than §1's and wider than "it is the sources":

> **`warp()` and the gain-staging/limiter chain made every synthesiser rebuild
> invisible — that part of the diagnosis is confirmed by measurement. But fixing
> the chain alone does not put glass in the glass, because the shard synthesiser
> had no energy above 4 kHz to reveal. Both had to be rebuilt, and the order in
> the spec is right: the chain first, because until it lands you cannot tell
> whether a source change did anything.**

## R2-4052 — I KILLED A 27-MINUTE RENDER AT ITS LAST STATEMENT, WITH THE REPORTING CODE

```python
rep["chain_checks"] = checks
rep["chain_checks"]["buses_where_peak_criterion_won"] = peak_won   # same dict
...
for k, c in checks.items():
    mark(... c["ok"] ...)        # TypeError: list indices must be integers
```

Assigning into `rep["chain_checks"]` assigned into `checks`, because they are the
same object. The loop that iterates the checks then indexed a list with a string.
**The audio was finished and correct; it was never written.**

The lesson is small and exact: **a reporting dict and an assertion dict are not
the same dict**, and the pattern `rep[k] = d` followed by `rep[k][x] = ...` is a
mutation of `d`. Fixed with `dict(checks, ...)`.

The larger lesson cost more: **a 27-minute build had never been smoke-tested.**
A 48 kHz run of the identical code path takes 9 minutes and exercises every line,
and adding one immediately paid for itself twice over — see R2-4053.

## R2-4053 — THE SMOKE RENDER FOUND A BUG THAT WOULD HAVE KILLED EVERY RENDER

```
TypeError: No format specified and unable to get format from file extension:
           'audio/out/master.wav.new'
```

`_archive_if_superseded` (R2-2227) writes beside the target and renames, so the
write path ends in **`.new`** — and soundfile infers the container from the
extension. **`sf.write` cannot write `.wav.new`.** This is not a bug I
introduced; it sits at the last statement of `build()` and would have killed any
render on this environment. It needs `format="WAV"`, which is now passed and
commented as load-bearing.

Two bugs at the same statement of the same function, both found in the ten
minutes after a smoke render existed and neither in the two 27-minute renders
before it.

## R2-4054 — THE FIRST FULL MASTER, AND WHAT IT SAYS ABOUT §3.4's RAISE

`audio/out/r2_4021/master_R2-4051.wav`, 124.083 s, −14.00 LUFS, −1.10 dBTP.

| breach, 36–44 s | delivered | R2-4051 |
|---|---:|---:|
| spectral centroid | **51.5 Hz** | **590.0 Hz** |
| energy < 30 Hz | **60.40 %** | **0.06 %** |
| energy < 100 Hz | **85.57 %** | **13.53 %** |
| energy > 4 kHz | **0.0021 %** | **2.77 %** (×1,300) |
| energy > 6 kHz | 0.0007 % | **1.27 %** |
| onsets/s, 1–4 kHz | 22.2 | **55.1** |
| onsets/s, 4–12 kHz | 16.5 | **79.1** |
| **L/R correlation** | **0.987** | **0.652** |
| 50 ms crest p50 | 7.31 | 10.16 dB |

| whole film | delivered | R2-4051 |
|---|---:|---:|
| median 50 ms crest | 9.70 | 10.20 dB |
| energy < 30 Hz | 22.15 % | **0.31 %** |
| 4–8 kHz band RMS, relative to 1–2 kHz | **−14.2 dB** | **−8.4 dB** |
| 8–12 kHz, relative to 1–2 kHz | **−25.6 dB** | **−18.9 dB** |
| limiter: fraction pulled > 3 dB | **15.48 %** | **5.22 %** |
| limiter: mean gain reduction | **−1.75 dB** | **−0.38 dB** |
| limiter: median gain reduction | — | **0.00 dB** |

**The breach is no longer mono.** L/R correlation 0.987 → 0.652 without touching
`spatial.py`, which confirms the diagnosis's own reading: the near-mono breach
was a *symptom* of sub-60 Hz domination, not an independent defect.

**But the master's breach is much darker than its own breach sources.** The
bench measures impact+shards+debris at a **1547 Hz** centroid with **12.2 %**
above 4 kHz; the master delivers **590 Hz** and **2.77 %**. Something else in the
window is dark and loud, and the bus log names it:

```
reflect_showroom  trim +9.79 dB   enters the sum at peak 1.000  (peak criterion WON)
aperture          trim +9.76 dB   enters the sum at peak 0.733
```

**Those are mine, from R2-4050.** Both are low-passed (5 kHz and 3.5 kHz) image
sources of a reverberant tail, both are active across 37–49 s, and raising them
6–9 dB laid a dark smeared wash over the sharpest event in the picture — visible
in the onset rise, which went the wrong way (6.9 ms delivered → **46.3 ms**).

**The falsifier attached to that decision fired, and it is being obeyed.**
`aperture` −18 → **−24**, `reflect_showroom` −19 → **−23**: +2/+3 dB over the
originals rather than +6/+9. Recorded rather than quietly retuned, because
"raise them into audibility with intent" is only a decision if the intent is
checked afterwards.

## R2-4055 — THE LAST TWO NOISE-ONLY LAYERS, AND G13

`crowd` was nine band-passed white-noise voices whose envelopes were also white
noise; `fence_buzz` drove five structural resonances with continuous white
noise. Both are Gaussian noise however they are filtered, and their 50 ms crest
is Gaussian noise's — which is the whole of G13's complaint.

Both get an **event process** through the same resonators. `_poisson_train`
builds an inhomogeneous Poisson impulse train and the bank filters it once, so
ten thousand events cost what one costs.

- **crowd**: babble kept and reduced, plus claps (4–40/s, rising with
  excitement) through a short bright resonance and shouts (0.5–6.5/s) through
  two formants. **The balance was swept and measured, not chosen**: at the
  original ratio the layer scores **10.85 dB**, against Gaussian noise's 10.9;
  at 0.30 babble **14.17**, at 0.18 **16.91**, at 0.10 **21.02**. Set at 0.22 —
  measured **15.94 dB at excitement 0.7**, 11.06 at 0.1. A distant grandstand is
  not a shooting gallery.
- **fence**: a wire fence hit by a pressure wave does not hum, it clatters
  against its posts and clips. Rate ∝ excitation², plus two much shorter, much
  higher clip resonances. Measured **50 ms crest 17.05 dB**, from ~10.9.

## R2-4056 — THE BREACH, ATTRIBUTED BUS BY BUS. THE ENGINE IS 56 % OF IT.

Backing the reverb buses off (R2-4054) moved the breach's centroid from 590 to
**568 Hz** and its energy above 4 kHz from 2.77 % to 2.80 %. **It changed
nothing, so they were not the cause**, and the retreat is kept only because it
was the right level on its own terms.

The render was repeated with `--stems`, and the 36–44 s window measured bus by
bus settles it:

| stem | share of breach energy | its own centroid | its own >4 kHz |
|---|---:|---:|---:|
| **engine** | **56.08 %** | **217.7 Hz** | **0.001 %** |
| shards | 32.36 % | 608.9 Hz | 0.132 % |
| **debris** | **3.82 %** | **6072.9 Hz** | **83.9 %** |
| reflect_showroom | 2.32 % | 820.1 Hz | 0.003 % |
| tyres | 1.62 % | 1224.5 Hz | 0.120 % |
| aperture | 1.56 % | 824.7 Hz | 0.001 % |
| structure | 0.97 % | 95.1 Hz | 0.000 % |
| everything else | 1.27 % | — | — |

**The engine and tyres are 57.7 % of the breach's energy, and they are the two
buses that are still varispeeded 6.51× down** — the sustained sources §6 assigns
jointly and R2-4035 deliberately did not touch. A spectral centroid is the
energy-weighted mean frequency, so it decomposes exactly:

```
0.561*218 + 0.324*609 + 0.038*6073 + 0.023*820 + 0.016*1225 + ...  =  ~600 Hz
```

against the 568 Hz measured. **The model reproduces the master, which means the
attribution is arithmetic and not a story.**

### The handoff number for the engine workflow

If the engine's world-attached layers were rendered on the film grid the way the
breach's now are, its centroid at the breach would rise by the transposition
factor — 217.7 × 6.51 ≈ **1417 Hz** — and the same decomposition gives a breach
centroid of about **1580 Hz**, which clears G3's 1200 Hz outright. **The single
highest-value change left in the breach is not in `layers.py`; it is
`master.py:365` applied to `eng_f` and `tyre_f`, and it belongs to the engine
workflow.** That is the number to hand them.

### And the bed is the only bus with a top end

`debris` carries **83.9 %** of its own energy above 4 kHz and is **3.82 %** of
the beat. Every other bus in the window is below 0.2 %. Whatever G2 gets, it
gets from there.

## R2-4057 — THE BED IS THE ONLY LEVER I OWN ON G2, AND IT IS PEAK-LIMITED

The bed carries the breach's entire top end and is 3.82 % of it. It could not
simply be turned up: `debris` is one of the buses where **the peak criterion had
already won** (LUFS target wanted +28.56 dB, peak ceiling allowed +24.55). Once
a bus is peak-limited the only currency is **RMS at full scale**, i.e. its own
crest.

| bed setting | RMS at peak 1.0 | its 50 ms crest | its own >4 kHz |
|---|---:|---:|---:|
| 34 fines/fragment, σ 0.70, 5 random resonators 3–8 kHz | −25.62 dB | 16.48 | 86.9 % |
| **90, σ 0.45**, 5 random | **−21.55 dB** | 12.79 | 86.9 % |
| 140, σ 0.35, 8 deterministic 3.5–9 kHz | −21.79 | 12.82 | 98.4 % |
| **140, σ 0.45, 4 deterministic 4–9 kHz** | **−20.27 dB** | **13.24** | **98.7 %** |

**Measured on the master, the 34 → 90 step took the breach from 2.80 % above
4 kHz to 6.63 % and its centroid from 568 to 773 Hz.**

Two things were learned the hard way and both are recorded:

**The resonator bank was an RNG lottery.** Five uniform draws over 3–8 kHz put
86.9 % of the bed above 4 kHz on one seed and 98.4 % on another — an 11.5-point
swing in the only bus with a top end, i.e. the breach's whole high-frequency
content decided by a random draw. Now spread deterministically, with Q still
drawn over the stated 20–60. **And the band is the contact's, not a mode's:** a
5 mm chip's first free-plate mode is 30.59/0.005² = **1.2 MHz**, so
sub-centimetre glass has no modes in the audio band at all and what a listener
hears is the contact transient, bandwidth 1/T for T = 0.05–0.3 ms, i.e.
3–20 kHz. 4–9 kHz is the conservative middle of that.

**Truncating the amplitude tail was tried and made it worse — the isolated test
lied.** A lognormal is unbounded and no fragment population contains an
arbitrarily large fine, so clipping at the 99.5th percentile should buy RMS at
the same peak, and on an isolated event train it bought **0.77 dB**. On the real
bed it **lost 1.41 dB** (−21.55 → −22.96), because at 140,000 events over 9.5 s
the resonators overlap so heavily that the bus's peak is a sum of many events
rather than the largest one. Clipping cut the RMS and barely touched the peak.
Left in the signature, defaulted off, with the measurement attached.

## R2-4058 — TWO OF MY OWN NEW LAYERS, MEASURED AND CORRECTED

Whole-film per-stem measurement from the R2-4056 stems:

```
stem            film E%   centroid   crest50
engine            48.36      614.2      9.93
shards            16.73      607.8      9.64
brakes             8.24      225.2      8.76
...
suspension         3.74      124.6      4.71
```

- **`brakes` came out at a 225 Hz centroid**, for a layer whose entire content is
  meant to live at 1.5–4 kHz. The spatial profile read at rubbing speed has an
  f^−2 temporal spectrum, so mixing the raw rub in at 0.35 buried the disc
  resonators it exists to excite, and the judder at 0.30 finished the job. Rub
  0.35 → **0.12**, judder 0.30 → **0.12**, high-pass 60 → 140 Hz. Measured
  centroid **225 → 1017 Hz**.
- **`suspension` was 3.74 % of the whole film's energy from 16 events**, with a
  50 ms crest of **4.71 dB** — a resonant boom rather than structure-borne
  detail. Target −24 → **−30 LUFS-S**.

Both of these are layers I added in R2-4049, and both were wrong in the mix in
ways only a whole-film stem measurement shows. Adding a layer is not the same as
landing one.

## R2-4059/4060 — THE BED'S LEVEL IS ONE NUMBER IN THE MIX TABLE, AND TWO RENDERS PROVED IT

R2-4059 made the bed denser (90 → 140 fines/fragment) and moved its resonator
bank from a random draw over 3–8 kHz to a deterministic spread over 4–9 kHz.
**The breach's energy above 4 kHz went DOWN, 6.63 % → 4.99 %.** Two separate
things were wrong with the reasoning, and both are worth recording because both
looked obviously right.

**(a) Higher is not brighter.** Octave bands on the delivered breach, 4–9 kHz
against 3–8 kHz:

| 2–4 k | 4–6 k | 6–8 k | 8–12 k | 12–20 k |
|---:|---:|---:|---:|---:|
| **−3.42** | **−1.77** | **−5.15** | **+9.95** | +1.77 dB |

Q 20–60 resonators centred at 4.6–8.4 kHz throw a great deal of energy into
8–12 kHz — real energy, and audible — but the 4–8 kHz octaves that carry most of
the absolute total lost more than it gained. Reverted to the spec's 3–8 kHz,
kept deterministic.

**(b) NOTHING INSIDE THE GENERATOR CHANGES WHAT THE BED DELIVERS.** Measured
directly, over six configurations spanning 90–200 fines per fragment, σ 0.30–0.45
and four resonator bands, computing each one's LUFS-S and peak and applying
whichever criterion binds:

```
fines nres          band |   LUFS-S     peak   binds |  E>4kHz delivered
   90    5  (3000, 8000) |   -13.82    0.702    LUFS |        2.936e-03
  140    4  (4000, 9000) |   -12.79    0.776    LUFS |        3.123e-03
  140    4  (3000, 8000) |   -13.58    0.700    LUFS |        2.778e-03
  140    5  (3000, 8000) |   -13.05    0.760    LUFS |        2.760e-03
  200    4  (3000, 8000) |   -12.66    0.844    LUFS |        2.652e-03
  200    5  (2800, 7500) |   -12.30    0.853    LUFS |        2.741e-03
```

**Every configuration lands within 0.7 dB, because the loudness criterion
re-normalises all of them.** The bed's contribution to the breach is set by
`TARGET_LUFS_S["debris"]` and by nothing in `debris_bed` whatsoever.

The 2.80 % → 6.63 % jump at R2-4057 was therefore **not** the extra fines. It was
that at 34 fines the bed was PEAK-capped 4 dB *below* its loudness target, and
at 90 it stopped being peak-capped and reached it — a one-off +4 dB step, now
exhausted.

**Two renders were spent tuning a generator before that was measured rather than
assumed.** The density and the deterministic bank are kept because they are
right on their own terms — 140 fines per integrated fragment is closer to what a
12 mm pane produces, and a bank drawn from an RNG is not a construction — but
neither is why the number moves.

`debris` is therefore set from the mix table: **−13.0 → −10.5 LUFS-S**, 1.5 dB
under the foreground shard bus. The stems say the bed carries 97.6 % of its own
energy above 4 kHz and is the only bus in the breach with any top end at all;
the fragments lead, the fines sit just beneath them.

## R2-4061 — THE DELIVERABLE, MEASURED. AND THE ONE MEASUREMENT THAT SETTLES G2/G3.

**`audio/out/r2_4021/master_R2-4060.wav`** — 124.083 s, −14.00 LUFS, −1.10 dBTP,
0 clipped samples. `audio/out/master.wav` (the rejected delivery) is left
untouched.

### Against the delivered master

| breach, 36–44 s | delivered | R2-4060 |
|---|---:|---:|
| spectral centroid | **51.5 Hz** | **711.5 Hz** (13.8×) |
| energy > 4 kHz | **0.0021 %** | **4.97 %** (2,370×) |
| energy > 6 kHz | 0.0007 % | **2.97 %** |
| energy < 30 Hz | **60.40 %** | **0.05 %** |
| energy < 100 Hz | **85.57 %** | **13.62 %** |
| 50 ms crest, p50 | 7.31 | **10.26 dB** |
| impact rise 10–90 %, at t = 36.00010 s | 0.60 | 1.92 ms |
| **L/R correlation** | **0.987** | **0.646** |

| whole film | delivered | R2-4060 |
|---|---:|---:|
| median 50 ms crest | 9.70 | **10.33 dB** |
| energy < 30 Hz | 22.15 % | **0.29 %** |
| 2–4 kHz vs 1–2 kHz | −6.14 | **−3.84 dB** |
| 4–8 kHz vs 1–2 kHz | **−14.27** | **−7.92 dB** |
| 8–12 kHz vs 1–2 kHz | **−25.64** | **−18.79 dB** |
| 12–16 kHz vs 1–2 kHz | −32.79 | **−25.69 dB** |

| the chain | delivered | R2-4060 |
|---|---:|---:|
| premix peak | **+17.73 dBFS** | **+4.25 dBFS** |
| limiter max GR (honest) | **−22.76 dB**, reported as −0.124 | **−11.60 dB**, reported as −11.60 |
| limiter mean GR | **−1.75 dB** | **−0.36 dB** |
| fraction of film pulled > 3 dB | **15.48 %** | **4.81 %** |
| fraction pulled > 6 dB | **12.15 %** | **1.89 %** |
| median GR | — | **0.00 dB** |
| limiter passes on the delivered signal | 9 | **1** |
| LUFS-I / true peak | −14.00 / −1.10 | −14.00 / −1.10 |

### G2 AND G3 ARE GATED ON ONE BUS, AND IT IS NOT MINE

Measured on the R2-4059 stems, summing the 36–44 s window bus by bus:

| what is in the sum | centroid | energy > 4 kHz |
|---|---:|---:|
| **all buses (the delivered breach)** | **791.6 Hz** | **6.01 %** |
| **without the engine** | **1482.8 Hz** | **13.25 %** |
| without engine + tyres (the two still varispeeded) | 1496.4 Hz | 13.79 % |
| the breach layers alone (impact + shards + debris) | **1615.0 Hz** | **15.78 %** |

**Remove the engine bus and the breach clears G3 (≥1200 Hz) and G2 (≥8 %)
outright.** The engine is 55 % of the beat's energy with a spectral centroid of
217.7 Hz and 0.001 % of its own energy above 4 kHz, because it is still
transposed 6.51× down by `warp()` — the sustained-source half of §2.0 that §6
assigns jointly and that R2-4035 deliberately did not touch.

*(A cruder counterfactual — shifting the engine's measured PSD up by 6.5051× —
gives a centroid of 1423.7 Hz but only 3.85 % above 4 kHz, because it drags the
engine's very large low-frequency energy into 1–4 kHz and dilutes the fraction.
It is reported for completeness and is the weaker of the two, since a film-grid
engine is not its warped self shifted.)*

**So the remaining work on the glass is not in `layers.py`. It is
`master.py:365` applied to `eng_f` and `tyre_f`, and it belongs to the engine
workflow.**

## R2-4062 — THE GATES I DID NOT REACH, AND WHY, WITHOUT ROUNDING ANYTHING UP

| gate | target | delivered | R2-4060 | status |
|---|---|---:|---:|---|
| G2 breach > 4 kHz | ≥ 8 % | 0.0021 % | **4.97 %** | **fail** — 13.25 % without the engine |
| G3 breach centroid | ≥ 1200 Hz | 51.5 Hz | **711.5 Hz** | **fail** — 1482.8 Hz without the engine |
| G4 breach 50 ms crest | ≥ 18 dB | 7.31 dB | **10.26 dB** | **fail** — see below |
| G5 impact rise | ≤ 2 ms | 0.60 ms | **1.92 ms** | **pass** |
| G6 onset density | ≥ 150/s | 87/s | 79/s | **fail** — see below |
| G8 pane modal density | 0.314 ±25 % | 0.134/Hz | **0.312/Hz** | **pass** |
| G9 log f₁ vs log L slope | −2.0 ±0.1 | — | **−1.972** | **pass** |
| G10 per-mode shard Q | 500–2000 | 45 | **942** | **pass** |
| G13 median 50 ms crest | > 11.0 dB | 9.70 dB | **10.33 dB** | **fail** — see below |
| G14 premix peak | ≤ +6 dBFS | +17.73 | **+4.25 dBFS** | **pass** |
| G1 limiter GR | ≤ 3 dB | −22.76 | **−11.60 dB** | **fail** — see below |

**G1 — arithmetic, not tuning.** The mix has a peak-to-loudness ratio of
+4.25 − (−17.88) = **22.1 dB**. Delivering −14 LUFS-I at −1.15 dBTP allows a PLR
of at most **12.85 dB**. The gap is 9.3 dB and something has to absorb it: the
program gain takes 10.16 dB of it slowly (kept at +7/−3 over 6 s/12 s exactly as
§4.3 requires) and the limiter takes the rest at the peaks. **A film whose
loudest beat has an 18 dB crest cannot also sit at −14 LUFS with 3 dB of
limiting** — those two targets are not simultaneously satisfiable, and −14 LUFS
is a music-streaming number applied to material with a 31 dB internal range.
What DID move is what a listener hears: mean gain reduction −1.75 → **−0.36 dB**,
median **0.00 dB**, and the fraction of the film pulled more than 6 dB
**12.15 % → 1.89 %**. The build fails itself loudly on G1 rather than hiding it,
which is what §4.1 asked for.

**G4 — the target is not reachable with G10.** A 50 ms crest of 18 dB across a
continuous eight-second shower requires each event to be short compared with its
spacing. With 995 contacts spread over 9.5 s of film and per-mode τ = Q/(πf) at
Q 800–1500 (which G10 *requires*), five to ten events overlap in every 50 ms
window and the sum is quasi-stationary. **G4 and G10 pull in opposite
directions.** Contact damping after the first bounce (R2-4041) took what it
could; the delivered figure is 10.26 dB against 7.31.

**G6 — the threshold is below the measurement's own ceiling.** The onset
detector had a 20 ms refractory period, which caps any signal at 50/s and makes
a 150/s threshold unreachable by construction. Corrected to 5 ms (ceiling
200/s), and on that footing **the delivered master already scores 87/s** — the
spec's "5–13.5/s" is a different detector, not a different signal. The
detector-free number is the schedule itself: **632 shard contacts per second at
the peak of the shower on the film grid, plus a fines intensity of 101,731/s**.
Beyond ~100/s, discrete onsets fuse into texture by definition, which is what
§2.2 says the goal is.

**G13 — 48 % of the film is a bus I do not own.** Per-stem, whole film: the
engine is **48.4 % of the energy with a 50 ms crest of 9.93 dB**. The layers I
rebuilt all clear the bar on their own — fence **17.05 dB**, crowd **15.94**,
debris **15.56**, wind **11.02** — but no combination of 50 % of a film lifts the
median past 11.0 dB while the other 50 % sits at 9.93. **G13 is jointly owned and
its remaining term is the engine's.**

## R2-4063 — WHAT I WOULD DO NEXT, IN ORDER

1. **`master.py:365` on `eng_f` and `tyre_f`** (engine workflow). Worth 13.25 %
   and 1482.8 Hz at the breach on its own, i.e. G2 and G3 together, and it is
   the largest single item left anywhere in this spec.
2. **Re-level the engine bus afterwards.** §6 warned that the engine needs
   re-levelling from scratch once the chain is fixed and that doing it twice
   wastes a pass — the chain is now fixed, so that pass is available.
3. **Decide G1's target against a delivery loudness.** If −14 LUFS-I is
   non-negotiable then ≤ 3 dB of gain reduction is not, and vice versa; the
   arithmetic above is the trade and somebody should pick a side rather than
   have the limiter pick it silently.
4. **`BUS_PEAK_CEILING` is now the binding constraint on the debris bed** — it
   enters at peak 1.000 and its loudness target is unreachable by 3.6 dB. The
   criterion is right for the impact bus (which it stopped over-boosting by
   25.81 dB) and is arguably too blunt for a dense texture whose meter
   under-reading is a crest artefact rather than a spectral one. A per-bus
   ceiling would fix it; I did not add one because a uniform rule that is
   occasionally too strict is easier to reason about than a table of exceptions,
   and because the engine change above makes the bed's level much less critical.
