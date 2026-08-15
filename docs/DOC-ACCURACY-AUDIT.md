# DOC ACCURACY AUDIT — pre-publication

**Written 2026-08-15. Read-only audit. Nothing outside this file was changed.**

This audit hunts one defect class: **a claim that was true when written and is
false now**, and **a correction that never propagated to the other places the
original claim lives**. Every finding below was checked against the artefact,
the source, or the filesystem — never against another summary. Where a claim
could only be checked against another document, it is labelled UNRESOLVED
rather than adjudicated.

**Coverage is partial and stated honestly in the last section. Read that before
treating anything here as an all-clear.**

---

## SEVERITY 1 — MUST FIX BEFORE PUBLISHING

### 1.1 `watch/INDEX.md` says the delivery masters carry R2-4152 audio. They do not.

**Where:** `watch/INDEX.md`, the **CURRENT** table, rows for
`PART2_THE_FILM_4K_ProRes422HQ.mov` (line 19), `PART2_THE_FILM_4K_h265.mp4`
(line 20) and `PART2_AUDIO_MASTER_R2-4152.wav` (line 21).

**What it says:** *"AUDIO REBUILT 08-15 — now R2-4152 — carries
`PART2_AUDIO_MASTER_R2-4152.wav`"*, *"same new audio"*, and the R2-4152 row is
headed *"The audio master the two films carry."*

**What is actually true:** both films carry `audio/out/master.wav` — the
original. Measured by extracting the audio stream and hashing the raw PCM:

```
ProRes422HQ.mov  audio stream s24le md5   27fa64ee09602b6f18bd444ac8589247
audio/out/master.wav            s24le md5 27fa64ee09602b6f18bd444ac8589247   <- MATCH
PART2_AUDIO_MASTER_R2-4152.wav  s24le md5 d4c40d3291b7ba2af6577af72661c0f5
PART2_AUDIO_MASTER_R2-4147.wav  s24le md5 c828d173e03afcccd15c2488fee50978
PART2_AUDIO_MASTER_R2-4141.wav  s24le md5 6f4af7e9c852901d01c5f5270246f5fa
```

The file mtimes agree: both films are **08-15 01:00**, not the **08-15 00:32**
the table records — 00:32 was the R2-4152 mux, 01:00 was the revert.

**The correction exists in the same file and did not reach the table.** Twenty-six
lines below, the *"CLIENT DECISION 2026-08-15"* section says correctly: *"Both
films above carry `audio/out/master.wav`."* So the revert added a section and
left the table it contradicts standing.

**Why this is severity 1:** this table is the first thing in the delivery index,
it is explicitly framed as *"CURRENT — safe to judge the film by"*, and this
file exists **because two client judgements were already formed against stale
artefacts**. It is the audit's target defect reproducing inside the document
written to prevent it.

Also stale by the same decision, same file:
* line 24, `listen_2026-08-14/` — *"the thing to actually play"*. The A/B it
  serves (R2-4152 vs R2-4147) has been decided against both arms.
* line 61's heading correctly marks the R2-4152 section superseded; the table
  row does not.

---

### 1.2 `vast-render/README.md` states no GPU has ever been rented. ~$216 and 2,764 jobs say otherwise.

**Where:** `~/vast-render/README.md` §Status (lines 192–212), §Credentials
(228–239), §Next: calibrate (214–226), §Open questions (316–319).

**What it says:**
> **No instance has ever been rented — $[redacted] credit untouched.**
> **Untested until first rental:** provisioning on a real instance, the 5090
> render path, and cold-start timing.
> Account 627622. **Credit $[redacted], balance $[redacted]**
> Calibration render on a real 5090 to replace the 2–8 min/frame estimate
> range with a measured number. ~$0.05.

**What is actually true**, read from the twelve broker SQLite databases
(`state*/broker.db`, opened read-only):

| | |
|---|---|
| jobs across 12 brokers | **2,764** |
| cumulative `meta.spend_usd` | **$215.75** |
| vast.ai credit, most recent sample | **$45.2304** |
| distinct instances in the three master brokers alone | 39 (state3 8, state4 16, state5 15) |
| delivered | a 2,978-frame 4K master, verified present frame 1–2978, 0 missing |

The calibration render the README lists as the next step was superseded by a
full production run; per-frame time is measured at 283.3 s (runbook) and the
"est. 2–8 min" in the §Why table (line 16) is a dead estimate.

**Why this is severity 1:** a stranger reads §Status as a safety statement —
*nothing has been spent, nothing is proven* — and both halves are wrong. It also
sets the wrong prior for every cost figure downstream.

---

### 1.3 `SHIPPING.md` — the file designated as THE answer for the world — names the wrong assembly.

**Where:** `render/world/assembly/r2/SHIPPING.md` line 3.

**What it says:** *"`assembly14.blend` — built 2026-08-07 22:40 … PROMOTED
2026-08-07 under R2-1701 as THE STALENESS REBUILD"*.

**What is actually true:** the delivered film was rendered on **assembly15**.
`render/world/assembly/r2/assembly15.blend` and `assembly15_build.json` exist on
disk. `docs/MASTER-RUNBOOK.md` line 8 records *"world assembly15, 0 of 94 source
files drifted"*; `watch/INDEX.md` line 19 records *"on world `assembly15`"*.

The runbook goes further and says assembly14's verdicts **do not transfer**:

> assembly14's verdict does not transfer — the 50 meshes it skipped as *empty*
> are exactly the `VEG_*` ground cover that carries geometry in assembly15

**Why this is severity 1:** `docs/LIVE-CAMERA.md` line 37 names this file as the
canonical declaration — *"This file is to the camera what
`render/world/assembly/r2/SHIPPING.md` is to the world: the ONE place the answer
is written down."* LIVE-CAMERA's own body documents this exact failure recurring
three times for the camera. This is the fourth, on the world.

**Note for whoever fixes it:** `SHIPPING.md` is **modified in the working tree**
(`git diff --stat` shows +42/−5) — an agent may already be mid-edit. Do not
collide.

Secondary, same file: the header declares assembly14 and the section immediately
under it is titled *"R2-1701 — why assembly11 exists"*, with an assembly10↔11
table. The document has been re-headed without its body being re-based.

---

### 1.4 The 34.3 MB/frame figure was retracted twice and still drives two vast-render docs.

**Where it still stands:**
* `vast-render/docs/agents.md` lines 183–191 — the worked example
  `local disk: 102.1 GB needed (2978 x 34.3 MB)` … `!! IT DOES NOT FIT` …
  *"a 4K master is ~34 MB a frame"*.
* `vast-render/docs/operations.md` line 1376 — *"returned PNG | 30.5–34.7 MB →
  **34.3 MB/frame** at 512"*, and lines 1098–1102 — *"2,978 of them is **102 GB**
  … The batch fills the disk at about frame **2,455** — eighteen days and ~$155
  of GPU in — after which every remaining frame fails on write."*

**Where it was retracted:** `f1-round2/docs/RENDER-LADDER.md`, §"THE DISK BLOCKER
WAS NEVER REAL", dated **2026-08-03**:

> **~7.5 MB/frame at 4K, not 34.3.** … **every disk conclusion drawn from it was
> wrong by 4.6x** … The prediction that a 4K master would die at about frame
> 2,274 was an artefact of the bad constant.

**What is actually true — measured on the delivered master itself**, not on
either document:

```
out3/seq/master4k   993 frames   7,457 MB
out4/seq/master4k   993 frames   7,062 MB
out5/seq/master4k   992 frames   7,747 MB
                  2,978 frames  22,266 MB  ->  7.48 MB/frame mean
PNG header: 3840x2160, bit depth 8, colour type 2 (8-bit RGB)
```

**22.3 GB, not 102 GB. 7.48 MB/frame, not 34.3.** The master did not fill the
disk and did not stop at frame 2,455; all 2,978 frames are present.
`docs/MASTER-RUNBOOK.md` independently measured 8.083 MB mean and explains why:
*"Delivery frames are 8-bit RGB at 8.08 MB mean, not the 15 MB assumed. The
16-bit 15.87 MB population is pixel-peep frames, not deliverables."*

**Mitigating, and worth stating so nobody over-corrects:** the *code* is fine.
`broker/seq.py:local_space` takes `mean_bytes` from `db.mean_bytes_for_spec`, so
the live warning is derived from measured frames. **Only the documentation
carries the dead constant** — but agents.md presents it as a worked example a
reader will believe.

---

### 1.5 `agents.md` still publishes the exec A/B as a REJECT. Two other docs carry the re-run that reversed it.

**Where it still stands:** `vast-render/docs/agents.md` lines 503–519:

> **Read the measurement before you reach for this.** … on the hardware this
> farm actually rents it is **1.7x** the local machine's build throughput, not
> the 3-5x the plan that motivated it predicted. … **The remote box does not
> scale with slots** … throughput plateaus near 160 items/hour however the slots
> are set.

**Where it was reversed:** `vast-render/docs/operations.md` §"THE RE-RUN,
2026-08-14: 3.65x ON A BOX THAT MEETS THE SPEC. THE REJECT FALLS", and
`README.md` lines 336–349. Both record 276.9 items/h against 75.9 local =
**3.65x**, against a 2.00x adoption bar, and explicitly name **two of the three
original findings as now the other way round** — including the slots plateau
agents.md still states.

**Why this is severity 1:** agents.md is the doc a builder reads to decide
whether to use `rq exec` at all, and it tells them not to bother, on a
measurement its own repo has published a reversal of.

**Note:** `docs/agents.md` mtime is **2026-08-15 01:07** — it is being edited
right now. This may already be in hand.

---

### 1.6 Both `rq exec` runbook examples name an entry script that does not exist.

| doc | line | `--entry` it gives | exists? |
|---|---|---|---|
| `vast-render/README.md` | 330 | `tools/item_build.py` | **no** |
| `vast-render/docs/agents.md` | 540 | `tools/build_item.py` | **no** |

Checked against `tools/`. The real command is
**`tools/item_build_cmd.py`**, and it does take `--item`:

```
365:    p.add_argument("--item")
366:    p.add_argument("--out")
```

Both examples are copy-pasteable and both fail. They also disagree with each
other, which is how a reader ends up believing one of them is right.

Aggravating: `item_build_cmd.py`'s own header documents this exact class of
failure — *"Handed the wrong save flag, a module … THROWS THE RESULT AWAY and
exits 0"* — so a wrong entry path here is not a benign typo in this codebase.

---

### 1.7 `operations.md`'s environment-variable table gives two wrong defaults.

Checked line by line against `~/vast-render/broker/config.py`.

| var | operations.md says | `config.py` actually | verdict |
|---|---|---|---|
| `DISK_GB` | `30` | **`80`** (line 770) | **WRONG** |
| `SCENE_CACHE_GB` | `8.0`, "cache ceiling in TOTAL BYTES" | **`0.0`** (line 181) — 0 means *derive* from measured disk at `SCENE_CACHE_FRACTION` 0.80, floored at `SCENE_CACHE_FLOOR_GB` 4.0 | **WRONG, and the semantics changed** |

`SCENE_CACHE_FRACTION` and `SCENE_CACHE_FLOOR_GB` are undocumented in
operations.md entirely. The prose elsewhere in the same file (*"The cache is
bounded by `SCENE_CACHE_GB`"*) reads as if the absolute ceiling is still the
mechanism.

`config.py`'s own comment confirms the change is deliberate and the doc is the
thing lagging:

> Set SCENE_CACHE_GB to pin an explicit ceiling; 0 (the default) means derive.

Every other row in that table that I checked was correct — see §CLEAN.

Downstream of the `DISK_GB` error: `agents.md` line 572 — *"The instance has
30 GB and twelve of these run at once"* — and its status example
`8.7G used of 30.0G`.

---

### 1.8 `MASTER-RUNBOOK.md` opens with a LIVE banner for a render that finished three days ago.

**Where:** `docs/MASTER-RUNBOOK.md` lines 3–55.

**What it says:**
> ## LIVE: THE MASTER IS RENDERING. Launched 2026-08-09 ~04:30Z.
> ETA ~82 h, around 2026-08-12
> spend ~$0.99 of a ~$102-113 projection, cap $150, credit $[redacted]
> **1. WATCH THE FIRST 12-HOUR RETIREMENT — do not assume the resume worked.**
> Due **16:06:32 / 16:07:02 / 16:07:33Z**. It has **never fired on this project**

**What is actually true:** the master completed; the ProRes and H.265 masters
were delivered and filed (`watch/INDEX.md`; git commits `7badbf7`, `5ab6969`).
The three master brokers rented 39 distinct instances over the run, so the 12 h
retirement path was exercised many times. Credit is **$[redacted]**, not $172.34.

The whole file is a launch-eve document — gates, a live spend line, "read this
before touching anything", "the brokers are DETACHED". It is the most
authoritative-looking file in `docs/` and a stranger will read it as present
tense. It needs a dated banner saying the render is done; the measurements below
the banner are still valuable and should be kept.

---

### 1.9 `README.md` and `operations.md` both present $[redacted] credit as the current safe posture.

* `README.md` line 239: *"**Credit $[redacted], balance $[redacted], autobilling appears off**
  — which is the correct safe posture: prepaid credit is the only hard spend
  ceiling vast.ai offers."*
* `operations.md` lines 903–905: *"The only real ceilings are **prepaid credit
  with autobilling off** (currently $25.00, autobill `None` — correct)."*

Actual credit, from `meta.credit` across brokers, most recent sample:
**$45.2304**. The project has spent ~$215.75 through this ceiling, which means
credit has been topped up repeatedly. A reader deciding whether a run is
affordable against "$25 untouched" is reasoning from a number three top-ups old.

Also in this family, unmarked: `README.md` line 18 *"Cost: **$0.326/hr**"*. The
exclusive-card market this project actually rents on is documented at
$0.4237–0.4889/hr (fleet.md), $0.454/hr (MASTER-RUNBOOK) and $0.508/hr
(operations.md re-run). `$0.326` predates the `gpu_frac>=0.99` exclusivity
requirement, which operations.md itself says costs about 8%.

---

### 1.10 Three planning documents describe a world that no longer exists and are not marked.

| file | dated | describes | reality |
|---|---|---|---|
| `docs/RESUME-HERE.md` | 2026-08-04 | ship candidate `film16_breach.blend`; two renders in flight; "**Landed in SOURCE but NOT in any film** — the next rebuild must carry all three" | film25_breach shipped; all three landed |
| `docs/SESSION-HOLD.md` | 2026-08-07 | encoder PID 1083726 live, brokers 8760/8761 holding instances, **"Credit $[redacted]"**, "**TWO BLOCKERS before any master**" | master rendered and delivered |
| `docs/NEXT-REBUILD.md` | 2026-08-07 | "**The 4K master cannot start until one rebuild carries all of this.** Anything rendered before it is superseded by construction." | the rebuild happened; the master started, finished and shipped |

None carries a supersede banner (`grep -iE 'SUPERSEDED\|OBSOLETE\|HISTORICAL\|ARCHIVED'`:
RESUME-HERE and SESSION-HOLD have **zero** hits; NEXT-REBUILD's one hit is
internal prose, not a header).

These are the highest-risk unmarked files because all three are written as
*entry points* — "RESUME HERE", "read these first, in this order". They are
where a stranger starts, and they hand out live-sounding instructions
(`rq teardown` on two brokers, "DO NOT CLOBBER — 12 modified files", a $[redacted]
credit figure, two open blockers) about a state that ended a week ago.

---

### 1.11 Five different totals for the same master cost, none of them cross-referenced.

Every one of these is presented as a current measured projection in its own file:

| doc | figure | basis |
|---|---|---|
| `vast-render/docs/operations.md` §"What the 2,978-frame 4K master costs" | **454 h / 18.9 days / $185** | 510.5 s/frame on `render3.blend` |
| `f1-round2/docs/RENDER-LADDER.md` | **322 h / 13.4 days / $131** | per-beat weighting of 60.2 s and 510.5 s |
| `vast-render/docs/fleet.md` line 143 | *"against a master of **~$82**"* | unstated |
| `f1-round2/docs/MASTER-RUNBOOK.md` | **245.5 GPU-h / 3.5 days / $112.88** at 3 cards | 283.3 s/frame on `film23_breach` at delivery spec |
| git commit `4a4e1c8` (vast-render) | *"the master is 180 h and $80 … not 322 h and $146"* | — |

**`multi-gpu.md` already adjudicates this and the adjudication did not
propagate.** Its correction section says:

> Everything below the "Status 2026-08-04" line was fit to **510.5 s/frame**, the
> `render3.blend` anchor. That anchor is not the film, and it has now produced
> **four** wrong master estimates in both directions — 322 h/$146, then
> 180 h/$80, then 172 h/$76, then 155 h/$70.

So the two survivors built on the retracted anchor — operations.md's $185/454 h
and RENDER-LADDER's $131/322 h — are named as wrong by a sibling document and
still stand unmarked. **MASTER-RUNBOOK's $112.88 is the only figure measured at
true delivery spec on the scene that rendered**, and it is the one a stranger is
least likely to find, because it sits under a stale LIVE banner.

I am **not** adjudicating the actual final spend — see UNRESOLVED §U1.

---

### 1.12 `watch/audio/INDEX.md` tells the client the breach was measured and is not defective. It was defective.

**Where:** `watch/audio/INDEX.md`, §"Why we thought the
ending was broken, and why it is not".

**What it says (client-facing):**
> So this round we went and measured those two, expecting to find a third defect.
> **We did not find one** …
> **The breach.** Above 2.6 kHz the breach carries **0.02 % of its own energy**
> … there is no engine note in it to find. There never was. **Breaking glass is
> broadband; that is what breaking glass is.**

**What was found later**, in `watch/INDEX.md`'s own R2-4079 section:
> the world-time warp was a **varispeed resampler**, transposing every
> world-attached source **6.51× down** at the breach — which is why the glass
> had no glass in it

| | delivered master | after the fix |
|---|---:|---:|
| breach spectral centroid | 51.5 Hz | 1372.1 Hz |
| breach energy below 100 Hz | 85.57 % | 1.88 % |

And again at R2-4152: the glazing is laminated and *"no line of the audio had
read that"*; the audio was synthesising 351 fragments of median 321 mm where the
picture has 3,216 of median 21 mm.

`watch/audio/INDEX.md` carries **no supersede banner**, and `watch/INDEX.md`
line 29 points readers at it with *"`audio/INDEX.md` explains the earlier
staleness and states it is fixed."*

**This is not academic.** The client's decision reverted the delivery to
`audio/out/master.wav` — the master these defects are *in*. So the published
package contains a client-facing page asserting the breach was measured clean,
next to a delivered master that measures 85.57 % of the breach's energy below
100 Hz. Whichever way that is resolved, the two cannot both stand unlabelled.

---

## SEVERITY 2 — WORTH KNOWING

**2.1 `MASTER-RUNBOOK.md` §AUDIO: "all 8 gates green".** Line 311: *"Master
byte-identical at `d5087fd021b5f748f176ecb2b6c1de67` … -14.00 LUFS, -1.10 dBTP,
all 8 gates green."* The hash and the loudness are **correct** (I measured
−14.0 LUFS on `audio/out/master.wav`), but "all 8 gates green" was retracted:
commit `ce369f2` is *"replace the eight gates that passed three rejected
masters"*, and `watch/INDEX.md` records *"all eight audio gates passed every
time. **The gates were the first defect and have been replaced.**"* The runbook's
"AUDIO — done" framing also predates five rebuilds and a client reversal.

**2.2 `README.md` §Layout and §Docs describe a single-broker system.** No mention
of `fleetctl` (at the repo root), `farm/`, or four of the seven files in `docs/`
— `fleet.md`, `multi-gpu.md`, `incidents.md`, `linked-libraries.md`. The layout
block lists `state/` and `out/` singular; there are twelve of each. The
multi-broker fleet is how the master actually rendered, so this is the README
omitting the system's principal operating mode.

**2.3 `fleet.md` prices the push against "a master of ~$82"** (line 143) — from
the retracted anchor family in §1.11. The conclusion it supports (*"worth about
half a dollar and ten minutes"*) survives at any of the candidate totals, so this
is a wrong number in a right argument. `fleet.md` mtime 01:05 — being edited.

**2.4 The MASTER-RUNBOOK's two RAM recommendations were not implemented, and a
code comment now argues the other way.** The runbook says: *"**Either filter on
`advertised x 0.96`, or raise `RAM_HEADROOM` to 1.30** so the effective margin is
the stated one."* In `vastctl/vastctl.py`: `RAM_HEADROOM` is still **1.25**
(line 479) and `_meets_scene_working_set` still filters on the advertised figure
(`ram_gib_per_gpu`). The comment at line 476 now takes the opposite position —
*"The headroom factor absorbs that gap … which is a second reason not to shave
it toward 1.0."* Both positions are defensible; a reader following the runbook
will believe a change was made that was not.

**2.5 `SCENE_WORKING_SET_GIB` is still 50.6.** MASTER-RUNBOOK measured the
successor value at **52.4173 GiB** (`VmHWM`) and called the 50.6 constant's
successor by name. The constant was not updated. The runbook argues the direction
is safe (all offers clear the implied floor with 20.68 GiB of margin), so this is
a known-and-reasoned gap rather than a defect — but the constant's own docstring
still cites the 50.6 measurement as current.

**2.6 `THE-BRIEF-ROUND2.md` names the deliverable `f1_oneshot_final.mp4`.** The
delivered files are `PART2_THE_FILM_4K_h265.mp4` / `_ProRes422HQ.mov`. The brief
is the client's own document and arguably should not be edited; a mapping note
somewhere would stop a reader hunting for a file that was never created. The
brief's `-14 LUFS` requirement **is** met — verified, see CLEAN.

**2.7 `agents.md`'s "Every flag" table is incomplete.** Missing from it but
present in `./rq render --help`: `--dof {scene,on,off}`, `--no-persistent-data`,
`--no-require-caches`, `--timeout`, `--frame`. `--nodof` is listed as the primary
spelling; the CLI marks it *"deprecated alias for `--dof off`"*. Since
`--dof scene` is the flag that exists to stop a repeat of a round-1 wrongly
blurred render, its absence from the flag table is the notable one. (Being
edited; may be in hand.)

**2.8 `MASTER-RUNBOOK.md`: "The 12 h retirement has never fired on any instance
(longest life 10.7 h)."** True at launch; the master then ran ~4 days across 39
instance rentals in the three master brokers. Listed under "THINGS THAT LOOK
LIKE LEVERS AND ARE NOT", where it now reads as a standing property of the
system rather than a pre-launch gap.

---

## WHAT I CHECKED AND FOUND CLEAN

Negative results are only worth something with the method attached, so each says
how it was checked.

**C1. The "the picture was never touched" claim is true.** `watch/INDEX.md`
claims the video streams survived every mux and the revert. Verified by
re-deriving both, today, from the delivered files:

```
ProRes  video stream MD5 = c346a7a322a4a2a403727c1e85f17511   claimed c346a7a3…  MATCH
H.265   video stream MD5 = 235ef36e844a62b0e303e4138907b9fa   claimed 235ef36e…  MATCH
```

**C2. The 2,978-frame coverage claim is true.** `watch/INDEX.md` claims *"0
missing, 0 duplicated"*. Verified by enumerating filenames across
`out{3,4,5}/seq/master4k`: **2,978 distinct frames, min 1, max 2978, 0 missing.**
Container duration on both films is 124.083333 s, matching the declared
2,978 / 24 fps.

**C3. `LIVE-CAMERA.md`'s declared sha256 is correct.** It declares
`render/film24_path.json` at `9d055d63da7249…`. Re-hashed the file today:
**exact match.** The mechanism it describes (`tools/live_campath.py` raising on
mismatch) has a live, correct declaration behind it.

**C4. The delivered audio meets the brief's loudness spec.** `THE-BRIEF-ROUND2.md`
asks for −14 LUFS integrated. Measured on `audio/out/master.wav` with
`ffmpeg -filter_complex ebur128`: **I: −14.0 LUFS.** The md5 the runbook declares
(`d5087fd021b5f748f176ecb2b6c1de67`) also matches the file on disk.

**C5. `panic.sh` really does destroy everything, including fleet-labelled cards.**
This looked like a serious hazard — `LABEL_PREFIX` defaults to `renderbroker`,
fleet brokers use `fleet03`…`fleet12`, and a label-scoped reap would leave ten
cards billing. Traced it: `vastctl.reap` defaults to `all_instances(client)` and
only narrows with `labelled_only=True`; the CLI is
`doomed = our_instances(client) if args.only_label else all_instances(client)`
(line 1535). The docstring names this as a deliberate fix. **The docs are
accurate and the hazard is closed.**

**C6. The README's "Known constraints in the scene code" are all still true.**
Read `~/opus5-car-render/tools/render.py` directly: it sets
`cam.data.dof.use_dof = False` (line 98) with no restore, and sets
`scene.cycles.denoiser` (line 87) with no `denoising_use_gpu`. Both
`tools/render.py` and `tools/exploded.py` still exist at the paths quoted.

**C7. The rest of the `operations.md` env-var table matches `config.py`.** Beyond
the two errors in §1.7, I checked and confirmed: `IDLE_GRACE` 300,
`HIBERNATE` 3600, `MAX_BATCH_USD` 20.0, `MAX_PER_AGENT` 25, `MAX_QUEUE_DEPTH` 200,
`POLL_INTERVAL` 10.0, `DEPLOY_ATTEMPTS` 3, `MAX_TRANSPORT_ROUNDS` 3,
`MAX_STALLED_ROUNDS` 2, `PUSH_STREAMS` 8, `PUSH_SERIAL_AFTER` 2,
`RECONCILE_AFTER_HEARTBEATS` 3, `DISK_RESERVE_GB` 2.0, `DISK_SAMPLE_SEC` 300,
`SCENE_BATCH_MAX` 25, `SCENE_STARVE_SEC` 300, `SCENE_PRIO_BOOST_SEC` 20,
`SCENE_PRIO_BOOST_MAX_SEC` 1800, `SCENE_SWITCH_PAYBACK` 2.0,
`SCENE_RELOAD_BASE_SEC` 60, `SCENE_RELOAD_SEC_PER_GB` 300, `FETCH_MIN_KBPS` 200,
`FETCH_SAMPLE_MIN_BYTES` 1000000, `FETCH_MIN_SAMPLES` 2, `MAX_FRAMES_PER_JOB` 5000,
`PROGRESS_INTERVAL` 15, `STALL_WARN_SEC` 600, `REATTACH_SEC` 5400,
`KEEP_ON_EXIT` false.

**C8. The blank-frame tuning table matches the source.** `BLANK_SD_MAX` 0.005,
`BLACK_MEAN_MAX` 0.005, `BLANK_ALPHA_MAX` 0.004, `SUSPECT_SD_MAX` 0.02,
`SUSPECT_LEVELS_MAX` 16, `SEQ_OUTLIER_WINDOW` 25, `SEQ_OUTLIER_Z` 8.0,
`SEQ_OUTLIER_MEAN_FLOOR` 0.02, `BLANK_FAILS_JOB` true — all exact.

**C9. The safety constants match.** `MAX_INSTANCE_HOURS` 12.0,
`HEARTBEAT_STALE_SEC` 1800 (the documented 30 min), `MAX_INET_COST_PER_TB` 4.0,
`MIN_CPU_CORES_EFFECTIVE` 32.0, `MIN_CPU_RAM_GB` **72.0** (matching the
MASTER-RUNBOOK's Gate 7 floor exactly), `EXCLUSIVE_GPU_FRAC` 0.99,
`cuda_vers>=12.8` present in `build_query`.

**C10. The blacklist documentation is current.** operations.md says
*"persisted and fleet-wide (`farm/bad_hosts.json`, 7 d TTL, one file for every
broker)"*. `config.BAD_HOSTS_PATH` = `ROOT/farm/bad_hosts.json`,
`BAD_HOST_TTL_SEC` = `7 * 24 * 3600`. Both exact, and the file exists. (A vestigial
`state/bad_hosts.json` also exists and is not what the code reads — harmless.)

**C11. The zstd-level decision matches the code.** README says the default moved
from 19 to 10 and pre-compressed scenes get level 1. `SCENE_ZSTD_LEVEL` = 10,
`SCENE_ZSTD_LEVEL_PRECOMPRESSED` = 1. Exact.

**C12. Every file, script and CLI verb the runbooks reference exists** except the
two in §1.6. Checked: `scripts/panic.sh`, `scripts/brokerd.sh`,
`scripts/probe_offers.py`, `vastctl/vastctl.py`, `worker/client.py`,
`worker/test_worker.py`, `worker/server.py`, `worker/exec_server.py`,
`broker/test_broker.py`, `broker/imgstat.py`, `farm/bad_hosts.json`,
`scenes/blank_probe.blend`, `fleetctl`, `rq`, `f1-round2/tools/ab_exec_unit.py`,
`opus5-car-render/work/f1_complete.blend`, `f1-round2/render/film25_breach.blend`,
`f1-round2/tools/film_bar.py`, `sim/out/fracture_wall.json`,
`sim/out/breach_sim.json`, `docs/beat_sheet.json`, and the three
`tools/r2_4149_*.py`. All `rq` subcommands quoted in the docs
(`render`, `exec`, `anim`, `seq`, `budget`, `get`, `status`, `cancel`,
`teardown`, `resume`, `drift`, and `seq list/status/verify/stats`) are in
`./rq --help`.

**C13. `--frames` syntax, `--dof scene` default, `--allow-blank`,
`--no-require-caches` all exist as documented**, with help text matching the
prose. Verified from `./rq render --help` and `./rq anim --help`.

**C14. `multi-gpu.md` and `incidents.md` are correctly banner-marked.**
`multi-gpu.md` carries two explicit banners — *"THE RECOMMENDED PATH IS NOW BUILT
AND PROVEN"* and *"SUPERSEDED 2026-08-07 — READ THE CORRECTION IMMEDIATELY
BELOW"* — before any stale content. `incidents.md` is newest-first with dated
entries and redacted host ids. **These two are the model the rest of the corpus
should be measured against.**

**C15. The disk-projection code is not fed by the dead 34.3 constant.** Grepped
`broker/*.py` and `rq` for `34.3` and equivalents: zero hits.
`local_space(name, to_render, mean_bytes)` receives `db.mean_bytes_for_spec`.
The live warning is measured; only the docs are stale.

---

## UNRESOLVED — flagged, not guessed

**U1. The master's actual final cost.** The three master brokers' cumulative
`meta.spend_usd` reads $38.03 + $53.14 + $49.89 = **$141.06**, but that is
*cumulative per broker across their whole life*, not per-render, and those
brokers did non-master work before and after. I could not isolate the master's
own spend without joining job rows to instance lifetimes, which I did not do.
**Do not publish $141.06 as the master's cost.** Someone with the job table
should settle it, because it is the number that retires §1.11's five-way
contradiction.

**U2. 7.48 vs 8.083 MB/frame.** My `du` over the three sequence directories gives
7.48 MB mean; MASTER-RUNBOOK reports 8.083 mean / 8.797 p95 from its own sample.
Both refute 34.3 decisively, so the §1.4 finding does not depend on resolving
this — but the two are 8 % apart and I did not determine why (likely a different
subset, or `du` block accounting vs `stat` bytes).

**U3. Whether the `watch/INDEX.md` R2-4152 rows are mid-edit.** The client
decision landed at commit `ed1b614` and the film mtimes are 01:00 today. The
table may be seconds from being fixed by another agent. I did not touch it. The
finding stands until someone confirms the table reads `audio/out/master.wav`.

**U4. What should happen to `watch/audio/INDEX.md` (§1.12).** It is client-facing
prose written in the first person to the client. Whether the right answer is a
banner, a rewrite, or exclusion from the published set is an editorial decision I
should not make. Flagging that it cannot ship as-is is as far as I go.

**U5. `docs/DEFECT-LOG-R2.md` open/closed status.** The log is 61,810 lines with
~4,200 entries. I did **not** build an open-defect index or verify any
"open"/"closed" status other than the ones surfaced by the entry-point documents.
The brief's category 5 — *anything still listed as open that has since been
closed* — is therefore **only spot-checked, not covered.** `grep` for retraction
language returned 60+ hits in the DEFECT-LOG alone; I followed roughly a dozen of
the ones the operator-facing docs depend on and left the rest.

**U6. The 81 `STAGING-R2-*.md` files.** ~70,000 lines. I did not audit them. Per
the brief's prioritisation these are the lowest-value target (a wrong number in a
superseded staging entry matters far less than a wrong command in a runbook), but
they are also where several of the corrections above live, so a claim I marked
"never retracted" could in principle be retracted somewhere in there. Treat this
audit's retraction-hunting as **entry-point-down, not log-up**.

---

## COVERAGE — read this before trusting the above

**Read in full and checked claim by claim (11 files, ~5,700 lines):**
`vast-render/README.md`, `vast-render/docs/operations.md`,
`vast-render/docs/agents.md`, `vast-render/docs/fleet.md`,
`f1-round2/docs/MASTER-RUNBOOK.md`, `f1-round2/docs/RESUME-HERE.md`,
`f1-round2/docs/SESSION-HOLD.md`, `f1-round2/docs/LIVE-CAMERA.md`,
`f1-round2/watch/INDEX.md`, `f1-round2/watch/audio/INDEX.md`,
`f1-round2/docs/RENDER-LADDER.md` (§budget and §disk in full).

**Read partially — heads, correction banners, and targeted sections:**
`vast-render/docs/multi-gpu.md`, `vast-render/docs/incidents.md`,
`f1-round2/docs/MASTER-PLAN.md`, `f1-round2/docs/NEXT-REBUILD.md`,
`f1-round2/docs/THE-BRIEF-ROUND2.md`, `f1-round2/docs/PLAN-throughput-optimisation.md`,
`f1-round2/render/world/assembly/r2/SHIPPING.md`, `f1-round2/docs/DEFECT-LOG-R2.md`.

**Not read at all:** `vast-render/docs/protocol.md`,
`vast-render/docs/linked-libraries.md`, the 81 `STAGING-R2-*.md` files,
`f1-round2/world/*.md` (9 files, ~6,400 lines), `f1-round2/round2_inventory.md`,
`docs/circuit_*.md`, `docs/item_manifest.md`, `docs/ITEM-PRESENCE-CENSUS.md`,
`docs/WAVE*.md`, `docs/HUMAN-FIGURE-BRIEF.md`, `docs/ITEM-CAMPAIGN-BRIEF.md`,
`docs/R2-042-DECISION.md`, `docs/DUPLICATE-ID-SWEEP-R2.md`, and the ~100 JSON/log
artefacts in `docs/`.

**Numerically: `f1-round2/docs/*.md` alone is 137,502 lines. I read on the order
of 8,000 of them — roughly 6 %.** `vast-render/docs` + README is 5,646 lines and
I read about 85 % of it.

**What that means for the findings.** The severity-1 list is the product of
auditing the **entry points** — the files a stranger opens first, the ones that
say "read this first", and the delivery index — and then checking their claims
against artefacts, source and the filesystem rather than against other prose.
That is the right prioritisation and it found twelve things. **It is not a
complete audit**, and specifically:

* a false claim living only in a staging file, a world build doc, or the body of
  the defect log **would not have been found**;
* "this claim was never retracted anywhere" is a statement about the documents I
  read, not about the corpus;
* the open/closed status of the defect log is **unaudited** (§U5).

**Method note, since it is the point of the exercise.** Every severity-1 finding
was settled against something that is not a document: PCM and video-stream md5s
of the delivered films, `ffprobe` and `ebur128` on the masters, `sha256sum` on
the declared camera path, PNG headers and `du` on the 2,978 delivered frames,
read-only SQLite queries against twelve broker databases, `grep` against
`broker/config.py` and `vastctl/vastctl.py`, `--help` against the live `rq`
binary, and `ls` against every path quoted in a runbook.
