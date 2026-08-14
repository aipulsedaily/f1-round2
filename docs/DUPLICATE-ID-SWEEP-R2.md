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

Every text file under `/home/zany/f1-round2` and `/home/zany/vast-render` was
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
including the unmerged ones, and against `/home/zany/vast-render`.

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
