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
