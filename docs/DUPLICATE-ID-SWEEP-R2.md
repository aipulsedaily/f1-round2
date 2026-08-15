# The duplicate-ID sweep, and the renumbering it authorises (task #170)

**Measured 2026-08-14, before anything was renumbered.** This file is the
citation evidence. It is committed *first*, on its own, so that if the
renumbering has to be redone the mapping does not have to be re-derived — after
a renumbering there is no way to recover which of two entries a citation meant.

---

## 1. WHAT WAS MEASURED

`docs/DEFECT-LOG-R2.md`, at `d5521ea`:

```
1,181  entry headings of the form  "## R2-nnn — ..."
1,154  distinct IDs among them
   27  IDs carried by TWO entirely different entries
```

The 27 are not scattered. They are four contiguous blocks:

| block | IDs | count |
|---|---|---|
| A | R2-1091 … R2-1098 | 8 |
| B | R2-1121 … R2-1123 | 3 |
| C | R2-1151 … R2-1157 | 7 |
| D | R2-1181 … R2-1189 | 9 |

Nothing else in the file collides. Headings that share a number with a
*sub-section* of the same entry (`### R2-952 — VERIFIED` under `## R2-952`),
and range banners (`## R2-2950..R2-2959 — …`), are not collisions and are left
alone.

## 2. HOW IT HAPPENED

Each block exists twice because two writers allocated the same range hours
apart, and neither could see the other:

* **the island** — a staging block merged into the log as a unit. Its numbers
  were allocated from a named file whose own header records the range check it
  did (`docs/STAGING-R2-1151-to-R2-1180.md:3`: *"Range check before writing:
  `R2-1151…R2-1180` is unused anywhere in `docs/`"*). It sits out of numeric
  position in the file.
* **the spine** — the main thread's own continuous narrative, which runs
  unbroken from R2-1061 to R2-1197 and allocated the same numbers on its way
  past.

Dated from `git log -S` on each heading:

| block | island landed | spine landed |
|---|---|---|
| A R2-1091…1098 | 08-07 10:32 `281fa13` | 08-07 14:27–14:45 `7b6e135`/`67d164f`/`c2089e7` |
| B R2-1121…1123 | 08-07 14:56 `f330e9c` | 08-07 15:49 `51f3fdf` |
| C R2-1151…1157 | 08-07 14:56 `f330e9c` | 08-07 21:18–22:01 `9c84382`/`9f27e08`/`f18faf7` |
| D R2-1181…1189 | 08-07 14:56 `f330e9c` | 08-08 01:40–02:03 `59b0805`/`3ea8a6f`/`00afd9e`/`f0d4d04` |

**In all four blocks the island is the earlier allocation and the spine is the
later one.** File order and clock order agree, so "the earlier occurrence in the
file" and "the earlier occurrence in time" name the same entry throughout. That
was checked rather than assumed, because the file is not in chronological order.

## 3. THE SWEEP

Every text file under `~/f1-round2` and `~/vast-render` was
scanned for `R2-nnnn`, `R2_nnnn`, `R2 nnnn` and `r2nnnn` for all 27 numbers,
filenames included. **204 hits.** Of those, 54 are the colliding headings
themselves and 27 are staging-file copies of headings; the rest are citations.

Each citation was resolved **from the citing sentence's own content**, not from
position. Full list, with the entry each one means:

### Block A — R2-1091 … R2-1098

| citation | text that decides it | means |
|---|---|---|
| `tools/live_campath.py:16` | *"`world/camera_rig_path.json` sat byte-identical to…"* | island |
| `tools/live_campath.py:46` | `why="R2-1091 A/B against the stale"` | island |
| `tools/retier.sh:53` | *"43 tools read it; this was one of them"* | island |
| `tools/sheet_reproduces.py:9` | *"the same failure three times — R2-1007, R2-1091…"* | island |
| `docs/LIVE-CAMERA.md:39` | *"Why it exists — R2-1007 and R2-1091"* | island |
| `DEFECT-LOG:28688` | *"R2-1091 through R2-1096 is pure geometry"* (inside the island) | island |
| `DEFECT-LOG:28656/28657/29012/29013/28951` | the island's own reader table | island |
| `DEFECT-LOG:33073` | *"43 tools read the stale file"* | island |
| `STAGING-R2-1271-to-R2-1400.md:939`, `work/w2r1286/STAGING.bak.md:294` | copies of 33073 | island |
| `DEFECT-LOG:31387` | *"the distinction I paid for an hour earlier"* — code path vs. grep | **spine** |
| `DEFECT-LOG:33459` | *"appears only in `selftest()` and the CLI default"* — the retraction | **spine** |
| `DEFECT-LOG:33539` | *"the host lottery costs ±45 % and sticker price is nearly worthless"* | **spine** (1094) |
| `DEFECT-LOG:45927` | *"certifies the shipping bake is verifiably the right one"* | **spine** (1097) |
| `STAGING-R2-2461-to-R2-2520.md:132` | copy of 45927 | **spine** (1097) |

### Block B — R2-1121 … R2-1123

| citation | text that decides it | means |
|---|---|---|
| `sim/fracture.py:1011` | *"what 'just relabel bays 3 and 6 retained' actually costs"* | island |
| `sim/slabcheck.py:210`, `:485` | the `role`-is-not-an-outcome rule | island |
| `sim/land_breach.sh:85`, `:97` | *"STAGE 3 … GATED ON NOTHING"* | island |
| `docs/SESSION-HOLD.md:53`, `:60` | *"slabcheck … CLOSED — R2-1121. It exits 0."* | island |
| `docs/NEXT-REBUILD.md:177`, `:185`, `:189`, `:215` | slabcheck; *"mullions 4 and 6"* | island |
| `DEFECT-LOG:37107` | *"`slabcheck` is NOT a blocker … closed at R2-1121"* | island |
| `DEFECT-LOG:45964` | quotes *"it belongs to whoever next has a reason to re-bake"* verbatim | island |
| `STAGING-R2-2461-to-R2-2520.md:169` | copy of 45964 | island |
| `tools/film_bar.py:46`, `DEFECT-LOG:47415`, `STAGING-R2-2821-to-R2-2880.md:169` | *"`gate_exit`'s VACUOUS distinction (R2-1121)"* | **NEITHER — see §5** |

Nothing anywhere cites the spine's R2-1121/1122/1123.

### Block C — R2-1151 … R2-1157

| citation | text that decides it | means |
|---|---|---|
| `tools/r2_1881_bake_cams.py:25`, `:27` | *"an A/B was reported to the client as 'the fix does not work' when arm B had…"* | **spine** |
| `tools/r2_1881_ab.sh:11`, `:15` | *"compare the two arms' camera manifests"* | **spine** |
| `tools/r2_1898_split_arms.py:17` | *"an A/B whose arms differ in the tier under test"* | **spine** |
| `DEFECT-LOG:41593` | *"an arm that had rendered with a socket unlinked"* | **spine** |
| `DEFECT-LOG:41663` | *"differ in camera, lens, exposure and film transparency at once"* | **spine** |
| `DEFECT-LOG:41823` | *"both arms would log a clean `build_terrain` run"* | **spine** |
| `STAGING-R2-1881-to-R2-1980.md:693/763/962` | copies of the three above | **spine** |
| `render/world/assembly/r2/SHIPPING.md:40` | *"the R2-1154 `assert_wired` addition"* | **spine** (1154) |
| `…/v126/build_assembly11.sh:20` | *"K.assert_wired, R2-1154"* | **spine** (1154) |
| `DEFECT-LOG:37362` | quotes the spine's own heading sentence verbatim | **spine** (1155) |
| `world/build_nearband.py:6` | *"WHAT IS WRONG, MEASURED (R2-1156)"* — the near band | **spine** (1156) |
| `world/build_nearband_HANDOVER.md:40`, `:210` | *"the D ≤ 52 m band `wood` evacuates"* | **spine** (1156) |
| `tools/r2_1821_ground_detail.py:2`, `:10` | *"the client's 'blank grass no detail nothing'"* | **spine** (1156) |
| `DEFECT-LOG:37270`, `:40096`, `:40475`, `:40516` | the same near-band / ground-detail thread | **spine** (1156) |
| `STAGING-R2-1701-to-R2-1760.md:455`, `STAGING-R2-1821-to-R2-1880.md:5/164/206` | copies of the above | **spine** (1156) |
| `DEFECT-LOG:31832`, `:32145` | inside the island, *"the sheet … is untracked"* | island (1157) |
| `DEFECT-LOG:32120` | inside the island, *"the fix in R2-1153 cannot be committed"* | island (1153) |

**Block C is the one that inverts.** Every citation from outside the log names
the *spine*; the island is cited by nothing but its own staging file and its own
three internal cross-references.

### Block D — R2-1181 … R2-1189

| citation | text that decides it | means |
|---|---|---|
| `audio/dsp.py:491` | *"`sosfiltfilt` … so the claim can be exact"* — the audio class sweep | island |
| `DEFECT-LOG:32212` | *"the whole argument for R2-1183"* (inside the island) | island |
| `DEFECT-LOG:32393` | *"in-point click on the A/B files"* (inside the island) | island |

Nothing anywhere cites the spine's R2-1181…1189.

## 4. THE DECISION

**Rule: the entry that external code and briefs already cite keeps the number;
the other one moves. Applied per block, so that no block is fragmented.**

This is the project's own precedent, set at the 2026-08-02 renumbering recorded
in the log at R2-054/R2-055/R2-057 and R2-051/052/053 — *"Each pair was resolved
by keeping the number that EXTERNAL CODE already cites, and moving the other."*
It is the reason the renumbering below touches **no source file at all**.

Applying it block by block:

| block | cited from outside | therefore MOVES | to |
|---|---|---|---|
| A R2-1091…1098 | island (5 sites, incl. `tools/live_campath.py`) | the **spine** | R2-4091…R2-4098 |
| B R2-1121…1123 | island (11 sites, incl. `sim/slabcheck.py`) | the **spine** | R2-4121…R2-4123 |
| C R2-1151…1157 | **spine** (8 sites, incl. `world/build_nearband.py`) | the **island** | R2-4151…R2-4157 |
| D R2-1181…1189 | island (`audio/dsp.py`) | the **spine** | R2-4181…R2-4189 |

The mapping is **new = old + 3000** in every case; only *which side* moves
varies, and that is decided by the table above rather than by position.

Blocks are moved whole. The alternative — deciding each of the 27 numbers
independently — would have split block C into `4151, 1152, 1153, 4154, 1155,
4156, 1157` on one side and its inverse on the other, which makes both halves
unreadable and is a worse outcome than the ambiguity it removes.

**Why R2-4091…R2-4189.** The highest number allocated anywhere is R2-4025, and
the highest *reserved* by a staging filename is R2-4080
(`docs/STAGING-R2-4021-to-R2-4080.md`). A full-tree scan for `R2-40xx`/`R2-41xx`
finds nothing at or above 4081. The 2026-08-02 renumbering's first attempt
created a **fifth** duplicate by moving entries into numbers that were already
taken; the range here was checked against the log, against every staging file
including the unmerged ones, and against `~/vast-render`.

**R2-4091 … R2-4189 IS NOW RESERVED. Do not allocate into it.**

## 5. WHAT IS DELIBERATELY NOT TOUCHED

* **`tools/film_bar.py:46`, `DEFECT-LOG:47415`, `STAGING-R2-2821-to-R2-2880.md:169`**
  — *"`gate_exit`'s VACUOUS distinction (R2-1121)"*. Neither R2-1121 mentions
  `gate_exit` or `VACUOUS`; the material they describe is in R2-1154. This is a
  **pre-existing mis-citation, not a casualty of the collision**, and it is not
  guessed at here: R2-1121 keeps its number, so the reference is left exactly as
  it was. Whoever owns `film_bar.py` should correct it.
* **Every staging file's headings.** They record what was staged under what
  number and are historical. Only `docs/STAGING-R2-1151-to-R2-1180.md` becomes
  misleading — its entries are the ones that moved — so it gets a banner at the
  top rather than a rewrite.
* **`docs/STAGING-R2-1881-to-R2-1980.md`, `docs/SESSION-HOLD.md`,
  `render/world/assembly/r2/SHIPPING.md`** and the other files dirty in the
  working tree. Their citations all point at entries that **keep** their
  numbers, so nothing needs changing in them; staging another agent's in-flight
  file to fix a citation that is already correct is the R2-226 defect for no
  gain.

## 6. THE EDIT SET THIS AUTHORISES

`docs/DEFECT-LOG-R2.md` — 27 headings, each with a `RENUMBERED` banner; 7
citations (`31387`, `33459`, `33539`, `45927` → spine; `31832`, `32120`,
`32145` → island); one reservation note in the header.

`docs/STAGING-R2-2461-to-R2-2520.md` — one citation, line 132.

`docs/STAGING-R2-1151-to-R2-1180.md` — one banner at the top.

**No source file changes. No dirty file is staged.**

---
---

# THE SECOND SWEEP (2026-08-15): THE RESERVATION WAS BREACHED, AND THE FIX IS NOT THE OBVIOUS ONE

**Measured 2026-08-15, before anything was renumbered.** Same discipline as the
first sweep and for the same reason: after a renumbering there is no way to
recover which of two entries a citation meant. This half is committed *first*,
on its own, so the mapping survives if the renumbering has to be redone.

## 7. WHAT WAS MEASURED

Every `## R2-nnnn — ` heading in `docs/DEFECT-LOG-R2.md` and in **all 81 staging
files**, merged and unmerged, plus a full-tree token sweep of `~/f1-round2` and
`~/vast-render` for `R2-nnnn`, `R2_nnnn`, `R2 nnnn` and `r2nnnn`, filenames
included, and every commit message in the repository.

```
1,212  entry headings in DEFECT-LOG-R2.md   (1,181 plain + 31 letter-suffixed)
    0  IDs duplicated INSIDE the log        <-- task #170 is clean
```

**The log itself has no duplicates.** The #170 renumbering did what it said it
did. Everything below is a staging-vs-log or staging-internal collision, i.e. a
merge hazard, not an existing defect in the log.

### 7.1 The true collision set

| # | ID | occurrence A | occurrence B |
|---|---|---|---|
| 1 | `R2-4151` | `DEFECT-LOG-R2.md:31805` — *"R2-1084's timeline is wrong"* (moved here by #170, was R2-1151) | `STAGING-R2-4141-to-R2-4200.md:1371` — *"THE MIX. THE 8.38 dB IS NOT IN THE CEILING"* |
| 2 | `R2-4152` | `DEFECT-LOG-R2.md:31860` — *"ROOT CAUSE: the fix was generated into a candidate and never promoted"* (was R2-1152) | `STAGING-R2-4141-to-R2-4200.md:1859` — *"THE ENGINE. THE FILM WAS DELIVERING 6.5x THE WORLD'S ENGINE ENERGY"* |
| 3–19 | `R2-4039` … `R2-4055` (**17**) | `STAGING-R2-4021-to-R2-4080.md:669–1113` — the **gates** pass | `STAGING-R2-4021-to-R2-4080.md:1115–1917` — the **chain-and-glass** pass |

**Three corrections to the account this task was given.**

* **The internal duplicate count is 17, not 13.** The brief said *"`R2-4039`,
  `R2-4044…R2-4055`"*. It missed **`R2-4040`, `R2-4041`, `R2-4042`, `R2-4043`**,
  which collide too — the chain pass files them under the *combined* headings
  `## R2-4040/4041 — THE SHARDS` (line 1158) and `## R2-4042/4043 — THE BREACH
  AS FIVE LAYERS` (line 1215). A heading regex anchored on `^## R2-\d+ — `
  does not match those, so a count taken that way reads 13 and is wrong by four.
  **This is the same class of instrument defect this project has spent weeks
  cataloguing: the count was not of the thing, it was of the thing's usual
  spelling.** All four are cited from `audio/layers.py`.
* **`R2-4141`…`R2-4150` do NOT collide with anything.** They are inside the
  reserved band and were allocated in breach of it, but #170 only ever used
  `4091–4098 / 4121–4123 / 4151–4157 / 4181–4189` within that band. Ten
  heavily-cited IDs therefore need no move at all — see §10.
* **Two further staging-internal duplicates exist and are out of scope**:
  `STAGING-R2-1881-to-R2-1980.md` has `R2-1898` twice (lines 818 and 913), and
  `STAGING-R2-821-to-R2-850.md` has `R2-840` twice (lines 780 and 851). Both
  files are already merged and the log resolved both at merge time (the log
  carries `R2-840a`…`R2-840r`). Recorded here so the next sweep does not think
  it found something new.

## 8. THE DECISION, AND WHY IT INVERTS THE BRIEF

The task directed that the **audio** entries move. **Measurement says the
opposite, and the project's own rule — set at the 2026-08-02 renumbering and
re-applied at #170 — decides it: *the entry that external code and briefs
already cite keeps the number; the other one moves.***

### 8.1 `R2-4151` / `R2-4152`

| | log side (#170's block C) | audio side (rebuild 4) |
|---|---|---|
| live source files citing it | **0** | **8** for R2-4151, **7** for R2-4152 — chiefly `audio/master.py` (22 sites) and `audio/layers.py` (5), plus `tools/` |
| tool files named for it | 0 | **9** — `tools/r2_4151_*.py` ×3, `tools/r2_4152_*.py` ×6 |
| on-disk artefacts named for it | 0 | **13** — `audio/out/r2_4151/master_R2-4151.wav`, `…/r2_4152/master_R2-4152.wav`, matrices, stems |
| files in `watch/` citing it | 0 | **3**, including the delivered master **`watch/PART2_AUDIO_MASTER_R2-4152.wav`** — *the ID is in the filename* |
| files this task MAY NOT EDIT citing it | 1 (`docs/README.md`, describing this very collision) | **5** — `watch/INDEX.md`, `watch/listen_2026-08-14/CLIPS_OF.json`, `docs/README.md`, `docs/READING-LIST.md`, `docs/DOC-ACCURACY-AUDIT.md` |
| commit messages citing it | 1 (`613342a`) | **4** (`6270825`, `bfa01ab`, `3438c44`, `75d3edf`) |

`R2-4153`, `R2-4154`, `R2-4155`, `R2-4156` appear in **exactly one file in
either tree** — the log itself. Block C is cited by nothing outside the three
documents that record its own renumbering, exactly as §3 of this file found when
it called block C *"cited by nothing but its own staging file and its own three
internal cross-references"*.

**Moving the audio entries is not merely more expensive — this task's own
constraints make it impossible to do correctly.** It is forbidden to edit
`watch/`, `docs/README.md`, `docs/READING-LIST.md` and
`docs/DOC-ACCURACY-AUDIT.md`; five of them cite the audio `R2-4151`/`R2-4152`,
and one of them **is a delivered `.wav` whose filename carries the number**. The
renumbering would leave the client-facing index and a shipped artefact pointing
at a number that no longer exists, and would be forbidden from repairing them.
That is not resolving an ambiguity, it is relocating it somewhere it cannot be
reached.

**And it fragments the wrong block.** Moving audio `4151/4152` splits the audio
rebuild into `4141–4150` + two strays; moving log block C leaves **both** blocks
contiguous — `4141…4152` for the audio rebuild, `4201…4207` for block C. §4's
*"blocks are moved whole"* is satisfiable only one way round.

The cost of moving block C a second time is real and is not hidden: those seven
entries will carry a two-hop trail, `R2-1151 → R2-4151 → R2-4201`. Each banner
states both hops. It is the smaller cost by roughly a factor of six, it touches
no source file and no delivered artefact, and it is what the project's own rule
requires.

### 8.2 `R2-4039` … `R2-4055`

Two passes wrote into `STAGING-R2-4021-to-R2-4080.md`:

* **the chain-and-glass pass** — `R2-4030…R2-4063`, commit `08634c2`, at lines
  461–659 and 1115–1917. Its numbering is contiguous across both stretches.
* **the gates pass** — `R2-4039…R2-4055`, commit `ce369f2`, at lines 669–1113.
  A parallel agent; §7's line 1945 calls it *"a parallel agent"* in so many words.

| | chain-and-glass pass | gates pass |
|---|---|---|
| live source citations | **~35** — `audio/layers.py` (20), `audio/master.py` (10), `tools/r2_4030_breach_bench.py`, `tools/r2_4141_tail_hf.py`, `tools/r2_4151_landing.patch` | **1** — `audio/percept.py:165` |
| artefacts named for it | **5** — `audio/out/bench_R2-4043.json`, `audio/out/r2_4021/*_R2-4051.*` ×4 | 0 |
| files this task MAY NOT EDIT citing it | 0 | **1** — `docs/BROKEN-INSTRUMENTS.md` (3 citations) |
| would moving it fragment the pass? | **yes** — splits a contiguous `4030…4063` | no — `4039…4055` moves whole |

**The gates pass moves.** One source citation against thirty-five, and it is a
comment line this task is permitted to correct.

## 9. THE MAPPING

**`R2-4201 … R2-4260` was checked free** against the log, against all 81 staging
files including the unmerged ones, against `~/vast-render`, and against every
filename in both trees. The highest ID in use anywhere is `R2-4189`; the highest
*reserved* by a staging filename is `R2-4200`. Nothing exists at or above 4201.
This is the check the 2026-08-02 renumbering's first attempt skipped, and it is
why that attempt created a fifth duplicate.

### 9.1 Log block C — the #170 island, second hop

| was (round 1) | was (#170) | **is now** | entry |
|---|---|---|---|
| R2-1151 | R2-4151 | **R2-4201** | R2-1084's timeline is wrong |
| R2-1152 | R2-4152 | **R2-4202** | ROOT CAUSE: generated into a candidate, never promoted |
| R2-1153 | R2-4153 | **R2-4203** | FIXED by promotion |
| R2-1154 | R2-4154 | **R2-4204** | THE DEFECT BEHIND THE DEFECT |
| R2-1155 | R2-4155 | **R2-4205** | the beat-1 PASS before 03:48 was a SATURATED metric |
| R2-1156 | R2-4156 | **R2-4206** | two things I did not touch, and why |
| R2-1157 | R2-4157 | **R2-4207** | the sheet the film is built from is untracked |

`new = old + 50`. The block moves whole.

### 9.2 The gates pass in `STAGING-R2-4021-to-R2-4080.md`

| was | **is now** | entry |
|---|---|---|
| R2-4039 | **R2-4239** | THE HEADLINE, WITH THE NUMBER THAT MATTERS |
| R2-4040 | **R2-4240** | DELETED: 629 LINES, NOT RECALIBRATED |
| R2-4041 | **R2-4241** | THE SELF-REFERENTIAL CALIBRATION RULE IS NOW BANNED IN CODE |
| R2-4042 | **R2-4242** | THREE INSTRUMENTS WHERE THERE WAS ONE NUMBER |
| R2-4043 | **R2-4243** | THE INSTRUMENTS RE-VALIDATE THEMSELVES ON EVERY INVOCATION |
| R2-4044 | **R2-4244** | G-RING REPLACES `waveguide`, ON THE WAV, AGAINST SABINE |
| R2-4045 | **R2-4245** | SIX GATES WITH NO PREDECESSOR |
| R2-4046 | **R2-4246** | INAPPLICABLE IS A DISTINCT OUTCOME AND NEVER COUNTS AS PASS |
| R2-4047 | **R2-4247** | `verify.py` NO LONGER CLAIMS A QUALITY VERDICT |
| R2-4048 | **R2-4248** | SPLICE DETECTION IS NOW FILM-WIDE |
| R2-4049 | **R2-4249** | THE DOPPLER GATE IS EXTENDED, AND PORTABLE BEFORE B7 |
| R2-4050 | **R2-4250** | THE PERMANENT CONTROL CORPUS: NINE CONTROLS |
| R2-4051 | **R2-4251** | EVERY GATE WATCHED TO FIRE: 12 OF 12 MUTATIONS |
| R2-4052 | **R2-4252** | G-CONSTRUCT ON THE CURRENT TREE: 35 VIOLATIONS |
| R2-4053 | **R2-4253** | DEVIATIONS FROM THE SPEC, DECLARED RATHER THAN QUIET |
| R2-4054 | **R2-4254** | SIX INSTRUMENT BUGS FOUND BY THE POSITIVE CONTROLS |
| R2-4055 | **R2-4255** | HOW TO RUN IT |

`new = old + 200`. The block moves whole. **The chain-and-glass pass keeps
`R2-4039…R2-4055` unchanged**, and so does every source citation of them.

## 10. STALE COMMIT MESSAGES — HOW TO READ THEM

**Commit messages cannot be rewritten and several are now wrong.** This is the
table to resolve them by.

| commit | its message says | it actually means |
|---|---|---|
| `ce369f2` | *"R2-4039..4055: replace the eight gates that passed three rejected masters"* | **R2-4239…R2-4255** — the gates pass |
| `08634c2` | *"R2-4030..4063: the shared chain and the glass breach"* | unchanged — the chain pass keeps its numbers |
| `613342a` | *"#170: 27 duplicated IDs resolved -- R2-4091..4098/4121..4123/**4151..4157**/4181..4189"* | the `4151..4157` clause now reads **R2-4201…R2-4207** |
| `1910065` | *"#170: the two staging citations the renumbering left pointing at the wrong entry"* | one of the two is block C's, now **R2-4201…R2-4207** |
| `6270825` | *"R2-4151: the 8.38 dB was never in the mix"* | **unchanged** — the audio entry keeps R2-4151 |
| `bfa01ab` | *"R2-4152: the engine was delivering 6.5x…"* | **unchanged** — the audio entry keeps R2-4152 |
| `3438c44`, `75d3edf` | R2-4152 clip manifest / `watch/INDEX` | **unchanged** |

**Rule of thumb for a reader hitting a stale reference:** a commit dated
2026-08-14 or later that says `R2-4151`/`R2-4152` means the **audio** entry,
which still carries that number. A reference to `R2-4151..4157` as a *block*
means the seven log entries now at `R2-4201…R2-4207`.

## 11. WHAT THIS SWEEP DELIBERATELY DOES NOT TOUCH

* **`R2-4141` … `R2-4150` stay exactly where they are.** They sit inside the
  band §4 reserved, and that was a real breach of the reservation — but they
  collide with nothing, and they are cited by 5 files in `watch/`, 4 files this
  task may not edit, 20+ source files, 24 tool filenames and 5 commit messages.
  **Moving ten uncontested IDs to tidy a reservation would manufacture the exact
  ambiguity the reservation exists to prevent.** The reservation is corrected in
  the log header instead, to record that they are legitimately held.
* **`docs/BROKEN-INSTRUMENTS.md`** cites the **gates** pass at three places —
  `:53` (R2-4039 → now R2-4239), `:383` (R2-4041 → now R2-4241), `:438` (R2-4040
  → now R2-4240), and a range row at `:1517` (*"R2-4030 – R2-4043"*, which spans
  both passes and was already ambiguous). Another agent owns that file and holds
  a live lease on it. **Reported, not edited.**
* **`docs/README.md`, `docs/READING-LIST.md`, `docs/DOC-ACCURACY-AUDIT.md`.**
  `README.md` §"Navigation hazards" describes this collision as an open problem
  and cites `R2-4151`/`R2-4152`/`R2-4157`; its `R2-4151`/`R2-4152` references
  remain correct for the audio entries, its `R2-4157` reference now reads
  `R2-4207`, and the hazard itself is now closed. `READING-LIST.md`'s
  `R2-4151`/`R2-4152` citations are the audio entries and remain correct.
  **Reported, not edited.**
* **The other staging files' headings.** Historical, as in §5.

## 12. THE EDIT SET THIS AUTHORISES

`docs/DEFECT-LOG-R2.md` — 7 headings and their banners; internal citations at
`31856`, `32156`, `32181`; the reservation note in the header.

`docs/STAGING-R2-4021-to-R2-4080.md` — 17 headings in lines 669–1113, the
section header at `669`, and 7 resolved citations from the engine pass at
`1945`, `2091`, `2400`, `2458`, `2588`, `2654`, `2684`. **Citations at `2019`,
`2382`, `2386`, `2926`, `2937` mean the chain pass and are left alone**; each
was resolved from the citing sentence's own content, not from position.

`docs/STAGING-R2-1151-to-R2-1180.md` — its banner, updated to the second hop.

`audio/percept.py` — one comment citation, line 165.

**One source file changes, by one comment line. No dirty file is staged. No
file in `watch/` is touched.**
