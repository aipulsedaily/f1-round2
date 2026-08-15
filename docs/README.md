# `docs/` — start here

This is the engineering log of **a 124-second, 2,978-frame, 4K film that is one
unbroken camera take with zero cuts**, built entirely from procedural geometry
and code-synthesised audio. No downloaded models, no stock footage, no photo
textures, no AI-generated anything — the brief forbids all of it
([`THE-BRIEF-ROUND2.md`](THE-BRIEF-ROUND2.md)).

**It was written as the work happened, including the parts that were wrong.**
That is the point of it. The log records instruments that could not detect the
thing they existed to detect, headline findings that were published and then
retracted by their own authors, fixes that were built and measured and correctly
not shipped, and five successive audio rebuilds that each measured better than
the last and were each rejected by ear. Read as a success story it is
misleading; read as a record of being wrong in public it is the most useful
thing here.

The film is finished. It is at `watch/PART2_THE_FILM_4K_h265.mp4` (880 MB
viewing copy) and `watch/PART2_THE_FILM_4K_ProRes422HQ.mov` (11.25 GB delivery
master).

---

## Where to start, by what you want

| you want | read, in order |
|---|---|
| **the film, and what it is** | [`THE-BRIEF-ROUND2.md`](THE-BRIEF-ROUND2.md) (the client's brief) → [`../watch/INDEX.md`](../watch/INDEX.md) (which artefact is current and which is stale) → [`beat_sheet.md`](beat_sheet.md) (the six beats) |
| **the interesting failures** | [`READING-LIST.md`](READING-LIST.md) — a curated ~60 entries out of 1,226, grouped by theme, each with a line on why it is worth opening. There is a ten-minute list at the top. |
| **the single defect this project kept finding** | [`BROKEN-INSTRUMENTS.md`](BROKEN-INSTRUMENTS.md) — one failure catalogued twenty-six times across subsystems that share no code, grouped by mechanism rather than by subsystem. It needs no knowledge of films, audio or render farms. `READING-LIST.md` §1 is the same territory as an index into the log; this is the essay. |
| **the rendering pipeline and what it cost** | [`MASTER-RUNBOOK.md`](MASTER-RUNBOOK.md) (the spec, the seven un-waivable gates, the measured per-beat cost) → `READING-LIST.md` §5 (the fleet campaign) → [`RENDER-LADDER.md`](RENDER-LADDER.md) (why nothing goes straight to 4K — but see the staleness warning below) |
| **the verification philosophy** | `READING-LIST.md` §8 (the laws the project generalised), then §1 (the instruments that failed, which is where the laws came from) |
| **the world and how it was built** | [`MASTER-PLAN.md`](MASTER-PLAN.md) → [`circuit_spec.md`](circuit_spec.md) → `READING-LIST.md` §4 |
| **to add an entry to the log** | the numbering rules below, then [`DUPLICATE-ID-SWEEP-R2.md`](DUPLICATE-ID-SWEEP-R2.md) §4 for the reserved ranges |

---

## How the numbering works

Every defect gets an entry with an ID of the form **`R2-nnn`**, written as a
level-2 heading:

```
## R2-374 — the shared A/B image reader byte-swaps every 16-bit pixel …
```

IDs are **not zero-padded to a fixed width** — the earliest are `R2-001`, the
latest `R2-4157` — so sort them numerically, not as strings, and grep for
`'^## R2-374 '` rather than `R2-0374`. Audio defects share the numbering with
visual ones; the brief requires it.

**The two files that hold entries:**

| | |
|---|---|
| **`DEFECT-LOG-R2.md`** | the merged log. **1,226 entries, 61,810 lines, 3.2 MB.** Appended chronologically, in merge order rather than numeric order. |
| **`STAGING-R2-<lo>-to-R2-<hi>.md`** | **81 files, 941 headings, 887 distinct IDs.** Agents write here; the coordinator merges into the log by identity, never by position. **74 of those IDs have not been merged yet** — see below. |

Four conventions matter, and each exists because of a specific incident:

1. **Entries are never edited to be right.** A later entry corrects an earlier
   one and both stay. `R2-2168` retracts its own author's published finding in
   full; `R2-430` retracts `R2-429`'s headline and then carries an appended
   main-thread correction saying the retraction's *own* replacement number was
   also wrong. Follow the chain forward, not the first statement you find.
   *"A document that silently changes its mind teaches nobody anything"*
   (`R2-1050`).
2. **Staging files are historical.** They record what was staged under what
   number. They are not rewritten when the log is corrected.
3. **A range banner covers several numbers in one heading** — e.g.
   `## R2-3721..R2-3736 — task #162: the variety gate now sees the trees`. So
   the count of headings is lower than the count of allocated numbers.
4. **When two entries collide on a number, the entry that external code and
   briefs already cite keeps it, and the other moves.** Blocks move whole. The
   full method, the citation-by-citation evidence and the dating are in
   [`DUPLICATE-ID-SWEEP-R2.md`](DUPLICATE-ID-SWEEP-R2.md), which was committed
   *before* any renumbering because after a renumbering there is no way to
   recover which of two entries a citation meant. 27 entries moved on
   2026-08-14; each carries a `RENUMBERED` banner naming its old number.

### Navigation hazards — RESOLVED 2026-08-15, kept because the resolution matters

**Both hazards below are now CLOSED.** They are left here because how they were
counted is more instructive than that they existed, and because six git commit
messages still name the old numbers.

- **~~`R2-4151` and `R2-4152` each name two different entries~~ — FIXED.** The
  **log** block moved to `R2-4201 … R2-4207`; the **audio** entries kept their
  numbers. That direction was the opposite of what was first instructed, and the
  measurement decided it: the audio entries are cited by **27 live source sites**,
  9 tool files, 13 artefacts, and — decisively — a **delivered artefact**,
  `watch/PART2_AUDIO_MASTER_R2-4152.wav`. Moving them would have stranded a
  shipped file and the client-facing index on a dead number. The log block was
  cited by **nothing but the log itself**.
- **~~13 internally duplicated IDs~~ — it was 17, and the undercount is the
  lesson.** `R2-4040`–`R2-4043` collide too, but the second pass filed them under
  *combined* headings — `## R2-4040/4041` — which the pattern `^## R2-\d+ — `
  does not match. **The count was not of the thing, it was of the thing's usual
  spelling.** Resolved by moving the *gates* pass to `R2-4239 … R2-4255`.
- **The blanket reservation `R2-4091 … R2-4189` is RETIRED.** It was allocated
  into twice — once by the audio rebuild, and once by the very sweep that
  declared it. It is replaced by a single rule: **the next free number is
  `R2-4256`**, with a table in `DUPLICATE-ID-SWEEP-R2.md`. `R2-4153 … R2-4157`
  are marked **VACATED — DO NOT REUSE**; they were live for one day and
  reallocating them would rebuild the ambiguity a third time.
- **Six commit messages now name stale IDs**, including the fixing commit's own
  subject. Git history cannot be rewritten here without de-referencing ~4,100 SHA
  citations, so the mapping is recorded in `DUPLICATE-ID-SWEEP-R2.md` §10 instead.
  **A stale commit message resolved by a table beats a rewritten history that
  breaks every citation in the corpus.**

**And the merge that lands staging into the log no longer deduplicates by ID.**
Dedup-by-identity would have silently skipped the audio entries as "already
present" and reported success — the exact instrument-that-reads-the-same-either-way
failure this corpus is a catalogue of. It now appends and proves the result three
independent ways: arithmetic (1,212 + 90 = 1,302), a string search for all 90
staged headings, and a byte-level proof that the pre-merge log is an exact prefix
of the result.
- **`R2-4024 … R2-4152` are not in the merged log yet.** They are the delivery
  finish and the four audio rebuilds, and they live only in
  `STAGING-R2-4021-to-R2-4080.md`, `STAGING-R2-4081-to-R2-4140.md` and
  `STAGING-R2-4141-to-R2-4200.md`.
- **Line numbers drift.** `READING-LIST.md` quotes them for convenience; the
  reliable lookup is `grep -n '^## R2-1401' docs/DEFECT-LOG-R2.md`.

---

## Which documents are live, and which are historical

Several documents in here are explicitly superseded. They are kept because the
measurement behind a superseded decision is usually still the useful part.

### Live — quote these

| file | what it is |
|---|---|
| `DEFECT-LOG-R2.md` | the merged log. Still appended to. |
| `STAGING-R2-*.md` | in-flight entries; the 4021+ files hold the unmerged tail. |
| `DUPLICATE-ID-SWEEP-R2.md` | the numbering authority and the reserved ranges. |
| `THE-BRIEF-ROUND2.md` | the client's brief. The film is judged against this. |
| `BROKEN-INSTRUMENTS.md` | the twenty-six-case catalogue of guards that could not fire, grouped by mechanism. Written to be readable with no knowledge of this project. |
| `DOC-ACCURACY-AUDIT.md` | a pre-publication audit hunting one class — a claim that was true when written and is false now, and a correction that never propagated. **Read it before quoting a number out of any planning document in here**, including the ones this file marks live. Several of its severity-1 findings have already been fixed in the files they name; check the file, not the audit, for the current text. |
| `../watch/INDEX.md` | **the only place that says which artefact is current.** Every file in `watch/` is a claim about the film whether it was meant as one or not; twice a client judgement was formed against an artefact that was out of date. Updated 2026-08-15 with the audio decision. |
| `MASTER-RUNBOOK.md` | the 4K master: spec, the seven un-waivable gates, the measured per-beat cost. Its `LIVE: THE MASTER IS RENDERING` banner describes 2026-08-09; **the render finished 2026-08-13** (`R2-3927`). Read the gates and the cost tables; read the banner as history. |
| `LIVE-CAMERA.md` | declares `render/film24_path.json` (sha256 `9d055d63…`) as the live camera. Verified: `render/film25_path.json`, the path of the blend the master rendered from, is **byte-identical** to it, so the declaration covers the delivered film. |
| `beat_sheet.json`, `circuit_spec.json` | the generated sources of truth. Note `R2-417`: `beat_sheet.md` and `beat_sheet.json` disagree about the film's last image, and `R2-656`/`R2-658` record a third beat table in circulation wrong by 910 frames. **Prefer the JSON.** |

### Historical — read for the record, do not act on

| file | why |
|---|---|
| `MASTER-PLAN.md` | written 2026-07-30 and says "the one document to read first". It was, then. For anything about the master, `MASTER-RUNBOOK.md` supersedes it. |
| `RESUME-HERE.md` | state at 2026-08-04, when the log had 425 entries. `R2-1050` records that it once told the next reader to redo a change that had been landed, measured and reverted; that line is corrected in place, with the correction stated rather than the line quietly replaced. |
| `SESSION-HOLD.md` | state at 2026-08-07, when the log had 685 entries. Its blocker list is closed. |
| `NEXT-REBUILD.md` | the manifest for the rebuild that became `assembly15` / `film25_breach.blend`. That rebuild happened and shipped. Its asphalt-re-budget row is marked **WRONG** in place by `R2-3061`, and `R2-3066` reverted the octave authored for it. |
| `RENDER-LADDER.md` | the argument for stills-plus-sequences is sound and still applies. **Its costings are not.** `R2-1057` records it wrong for the fourth time with a fifth error already staged; `R2-784` records it quoting a different scene's rate. Use `MASTER-RUNBOOK.md`'s measured tables. |
| `WAVE2-SCOPE.md`, `WAVE2-RANKING.md` | the item campaign's scoping. `WAVE2-RANKING.md` supersedes `WAVE2-SCOPE.md` §3 by its own header; both are then superseded on trees by `R2-1883` and `R2-1887` — the tree tier was declared unbuildable while a 33.26 M-triangle vegetation library with 26,641 trees was already shipping in the film. |
| `WAVE1-PEEP-SYNTHESIS.md` | six adversarial reviews, zero SHIP. Some of its amplitude verdicts are unsafe: `R2-020` found the frames were rendered at 1920×1080 while the gate scored them at 3840. The absent-feature findings stand. |
| `ITEM-PRESENCE-CENSUS.md`, `R2-042-DECISION.md`, `HUMAN-FIGURE-BRIEF.md`, `ITEM-CAMPAIGN-BRIEF.md`, `PLAN-scope-optimisation.md`, `PLAN-throughput-optimisation.md` | single-question documents, each answering a question that was live on its own date. Each states its date at the top. |
| `*_SUPERSEDED_*.json`, `*_CANDIDATE.json` | deliberately kept and deliberately named. A candidate sheet is not the shipped sheet — `R2-1099` cost ten hours to a fix that was generated into a candidate and never promoted. |

---

## Glossary

| term | meaning |
|---|---|
| **beat** | one of the film's six movements: 1 assembly (792 frames), 2 launch (72), 3 breach (192), 4 transit (134), 5 lap (1,524), 6 ending (264). They are movements, not shots — there is no cut between them. |
| **the one-shot law** | the brief's absolute constraint: one camera, one continuous path, zero cuts, zero crossfades, zero hidden whip-pans, first frame to last. Everything bends to it. Checked in `R2-423` (path) and `R2-711` (pixels). |
| **gate** | a program that inspects an artefact and prints a verdict. Gates block; they are not advisory. |
| **`>> STAGE RESULT: <VERDICT>`** | the printed verdict line every gate emits — `PLACEMENT_CLEAN`, `COLLISION_VACUOUS`, `FILM_BAR_PASS`. It appears 273 times in the log and in 200 files under `tools/`. **Callers grep for this line, not for an exit status**, because Blender 5.2 exits 0 on an uncaught exception (`R2-2824`). |
| **vacuous** | a verdict on an empty test set. `R2-018` is the founding case: two gates printed a green result having tested zero of zero. Gates now exit `*_VACUOUS` rather than pass. |
| **control** | an artefact fed to an instrument to prove the instrument works. |
| **positive control** | something the instrument **must fail**. A gate that has never failed has not been shown to work. |
| **negative control** | something it **must pass**. The bar's own negative control is `film10`, whose header reads: *if film10 ever comes back PASS the instrument is broken and every PASS above it is vacuous.* It was piped into `tail` for four film generations (`R2-2824`). |
| **the bar** | `tools/film_bar.py`, the 41-row acceptance suite a film blend must clear. Three verdicts: `OK`, `FAIL`, `UNMEASURABLE` — silence is not a pass. |
| **the ladder / rung** | the render-resolution ladder. Rung 1 is 1280×720 at 64 samples; delivery is 3840×2160 at 512. A rung-1 result cannot adjudicate a delivery-spec question (`R2-15xx`, `R2-710`). |
| **peep / pixel-peep** | opening a delivered frame at 1:1 and looking at it. `docs/peep/` holds the crops. The project's recurring lesson is that a metric quoted without opening the frame is a claim, not evidence (`R2-430`). |
| **assemblyN / filmN** | the world build and the film blend built from it. `assembly15` / `film25_breach.blend` (sha16 `1d2aa2d86533574e`) rendered the delivered film. |
| **the wound** | the breached showroom, which must persist visibly for the rest of the film because there is no cut to hide behind. |
| **the client** | the person the film is for, quoted verbatim throughout — *"AUDIO IS SHIT SOUNDS LIKE A HAIR BLOWER"*, *"anything 5 feet away from the main road … have blank grass no detail nothing"*. The notes are often more diagnostically precise than the instruments were. |

---

## Timeline

| when | what |
|---|---|
| **2026-07-28** | STEP ZERO. The car is inventoried before any planning (`round2_inventory.md`). `R2-001`–`R2-010` are all found before a frame exists. |
| **2026-07-30** | `MASTER-PLAN.md`: circuit, showroom siting, world layout. |
| **2026-08-02** | The first ID collision and the renumbering precedent that `DUPLICATE-ID-SWEEP-R2.md` later cites (`R2-051`/`052`/`053`, `R2-054`/`055`/`057`). |
| **2026-08-03** | Git history begins: *"Baseline: f1-round2 source at contract 1.2.1"*. 618 commits follow. |
| **2026-08-04** | A hard weekly usage limit stops two agents mid-task. `RESUME-HERE.md` is written at 425 entries. |
| **2026-08-07** | Session hold at 685 entries. `NEXT-REBUILD.md` — everything one rebuild must carry. The client's beat-1 notes arrive. |
| **2026-08-08** | `MASTER-RUNBOOK.md` written from measurements. Beat-5 re-pace promoted. |
| **2026-08-09 ~04:30Z** | **The 4K master starts** on three rented RTX 5090s, from `film25_breach.blend` on `assembly15`. |
| **2026-08-09 → 08-13** | The fleet campaign: the 12-hour retirement fires on all three cards at once (`R2-3861`), a real five-minute network outage that the middleware survives (`R2-3860`), four bad hosts in nineteen rentals, one job failure escalated rather than worked around (`R2-3925`). |
| **2026-08-13 05:45:19Z** | **2,978 of 2,978 frames on disk**, verified three independent ways (`R2-3927`). |
| **2026-08-14 02:15–02:29Z** | The ProRes 422 HQ master encoded and verified (`R2-4021`); the H.265 viewing copy follows (`R2-4024`). |
| **2026-08-14** | Task #170: the duplicate-ID sweep and the 27-entry renumbering. |
| **2026-08-14 → 08-15** | Four further audio rebuilds — `R2-4079`, `R2-4141`, `R2-4147`, `R2-4152` — each measuring better than the last. |
| **2026-08-15** | **The client hears them and rules: *"orginal audio was better go back to orgininal audio"*.** The films revert to `audio/out/master.wav`. All five rebuilds and their measurements are kept. |

The single most load-bearing sentence in `watch/INDEX.md` is about that last
row, and it is the reason this documentation is worth publishing:

> **five successive rebuilds each measured better than the last, and the client
> rejected every one by ear. Any future pass should treat that as the primary
> evidence — not as a reason to try a sixth with the same instruments.**
