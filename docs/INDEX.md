# `docs/INDEX.md` — every file in this directory, one line each

`docs/` holds **144 tracked files: 106 markdown and 38 data artefacts**, about
**142,100 lines of prose**. This page exists so that nobody has to open all of
them to find the shape of the thing.

*Measured 2026-08-18 against the tracked tree, after this page, `QUICKSTART.md`
and `GITHUB-PAGE.md` were added — the first draft said 141/103 and was made
stale by its own commit, which is a small demonstration of why every count on
this page ships with the command that re-derives it.*

**This is the inventory. Three other pages are the route in:**

| page | what it is for |
|---|---|
| [`../README.md`](../README.md) | what the project is, in thirty seconds |
| [`README.md`](README.md) | how the log is organised, live-vs-historical, glossary, timeline |
| [`READING-LIST.md`](READING-LIST.md) | ~60 curated entries out of 1,295, with a ten-minute list at the top |
| [`BROKEN-INSTRUMENTS.md`](BROKEN-INSTRUMENTS.md) | the one essay to read if you read nothing else |

---

## 1. Read these

Documents written to be read by someone who was not here.

| file | lines | what it covers |
|---|---|---|
| [`BROKEN-INSTRUMENTS.md`](BROKEN-INSTRUMENTS.md) | 1,536 | **The headline document.** Twenty-six cases of a check that returned the same answer whether the defect was present or absent, grouped by mechanism into seven families, with a synthesis and a `Corrections` section retracting two of the project's own folk claims. Needs no knowledge of films, audio or render farms. |
| [`READING-LIST.md`](READING-LIST.md) | 191 | A curated route through the defect log: a ten-minute list, then nine themed sections (broken instruments, retractions, fixes correctly not shipped, the world, the render farm, multi-agent collisions, the audio, the generalised laws, where the film is actually proven). |
| [`README.md`](README.md) | 209 | How `docs/` works: the `R2-nnn` numbering rules and their four conventions, which documents are live and which are historical, a glossary of the project's vocabulary, and a dated timeline. |
| [`DEFECT-LOG-R2.md`](DEFECT-LOG-R2.md) | 67,640 | **The log itself.** 1,316 entry headings, 1,295 distinct IDs, `R2-001` … `R2-4255`, appended in merge order rather than numeric order. Do not start at line 1. |
| [`THE-BRIEF-ROUND2.md`](THE-BRIEF-ROUND2.md) | 151 | The client's brief, verbatim, including the one-shot law and the no-downloaded-assets rule. **The film is judged against this file.** |
| [`DOC-ACCURACY-AUDIT.md`](DOC-ACCURACY-AUDIT.md) | 646 | A pre-publication audit hunting one class: a claim that was true when written and is false now, and a correction that never propagated. **Read it before quoting a number out of any planning document here.** Some of its severity-1 findings have since been fixed in the files they name — check the file, not the audit. |
| [`MASTER-RUNBOOK.md`](MASTER-RUNBOOK.md) | 328 | The 4K master: the spec as a ceiling, the seven un-waivable gates, measured per-beat cost, and the fleet-size table. Its `LIVE: THE MASTER IS RENDERING` banner describes 2026-08-09; the render finished 2026-08-13 (`R2-3927`). Read the gates and the cost tables; read the banner as history. |
| [`PUBLICATION-AUDIT.md`](PUBLICATION-AUDIT.md) | 470 | The full-history secret scan and the publication go/no-go, including the three history options priced against each other. **Contains the outstanding blocker: the vast.ai API key must be rotated.** |
| [`SANITISATION-R2-CODE.md`](SANITISATION-R2-CODE.md) | 261 | How the owner's home directory was removed from 322 tracked source files, the per-language rewrite policy and why a path in prose and a path in code are not the same problem, and the four traps that passed a clean-looking run before being caught. |
| [`QUICKSTART.md`](QUICKSTART.md) | — | What you can run in a fresh clone with no GPU, no film and no render farm — and the measured verdict of every item selftest, including the ones that fail. |
| [`GITHUB-PAGE.md`](GITHUB-PAGE.md) | — | Suggested repository description, topics and social preview for the GitHub page, plus the pre-publication checklist. |

## 2. Specifications and design decisions

| file | lines | what it covers |
|---|---|---|
| [`circuit_spec.md`](circuit_spec.md) | 1,321 | **The buildable circuit.** The synthesis of three candidate layouts into the shipped 3,675 m circuit: geometry, corner-by-corner, surfaces, elevation, and the grafts taken from the rejected candidates. |
| [`circuit_D_camera.md`](circuit_D_camera.md) | 795 | Candidate D, "Vitrine" — designed backwards from the camera move. It won on all three judging axes and is the base layout. |
| [`circuit_A_flowing.md`](circuit_A_flowing.md) | 698 | Candidate A, "Vallon" — a road laid over a landscape. Grafts from it survive in the shipped spec. |
| [`circuit_C_street.md`](circuit_C_street.md) | 660 | Candidate C, "Circuit du Quartier Vitrine" — a harbour-and-old-town street circuit. Not chosen; the reasoning is the useful part. |
| [`beat_sheet.md`](beat_sheet.md) | 94 | The six beats of the single take and their frame budgets. **`R2-417` records that this file and `beat_sheet.json` disagree about the film's last image — prefer the JSON.** |
| [`item_manifest.md`](item_manifest.md) | 2,416 | One row per discrete physical object a human would name — `armco_post`, not `barriers`. The work list the item campaign was scoped against. |
| [`MASTER-PLAN.md`](MASTER-PLAN.md) | 628 | The 2026-07-30 layout plan: circuit siting, showroom siting, world layout. Says "the one document to read first"; it was, then. |
| [`LIVE-CAMERA.md`](LIVE-CAMERA.md) | 78 | Which path file is the live camera, by sha256, and the verification that the declaration covers the delivered film. |
| [`R2-042-DECISION.md`](R2-042-DECISION.md) | 211 | A single decision, written out: the transit curve, arc versus chord, decided from the source files. |
| [`RENDER-LADDER.md`](RENDER-LADDER.md) | 371 | Why nothing goes straight to 4K, and why stills and sequences catch different defect classes. **The argument holds; its costings do not** — `R2-1057` records it wrong for the fourth time. Use `MASTER-RUNBOOK.md`'s measured tables. |
| [`DUPLICATE-ID-SWEEP-R2.md`](DUPLICATE-ID-SWEEP-R2.md) | 439 | The numbering authority: how ID collisions are adjudicated by citation weight, the reserved and vacated ranges, and the stale-commit-message mapping. Committed *before* any renumbering, because afterwards there is no way to recover which entry a citation meant. |

## 3. Campaigns and briefs

Each answers a question that was live on its own date, and each states that date
at the top.

| file | lines | what it covers |
|---|---|---|
| [`ITEM-CAMPAIGN-BRIEF.md`](ITEM-CAMPAIGN-BRIEF.md) | 432 | The contract for the per-item hero-asset campaign: one agent per item, and what "built" has to mean before an item may be placed. |
| [`HUMAN-FIGURE-BRIEF.md`](HUMAN-FIGURE-BRIEF.md) | 128 | People — the hardest asset class in the film, and the workflow written after the client rejected the first attempt. |
| [`ITEM-PRESENCE-CENSUS.md`](ITEM-PRESENCE-CENSUS.md) | 1,119 | How many items are gated, tiered and scored for screen presence while being **absent from the ship**. The answer changed the campaign's scope. |
| [`WAVE2-SCOPE.md`](WAVE2-SCOPE.md) | 1,084 | How big wave 2 is and what it costs. Builds nothing. Superseded on §3 by `WAVE2-RANKING.md`, and on trees by `R2-1883`/`R2-1887`. |
| [`WAVE1-PEEP-SYNTHESIS.md`](WAVE1-PEEP-SYNTHESIS.md) | 121 | Six independent adversarial pixel-peeps of six foundation items. **Every one returned REWORK; zero SHIP.** Some of its amplitude verdicts are unsafe (`R2-020`); the absent-feature findings stand. |
| [`PLAN-scope-optimisation.md`](PLAN-scope-optimisation.md) | 650 | Cutting the agent count without cutting what the viewer sees. Every claim marked MEASURED or not. |
| [`PLAN-throughput-optimisation.md`](PLAN-throughput-optimisation.md) | 826 | Execution efficiency only: how to build 435 items in days instead of weeks. |
| [`audio-rebuild3/SPEC-ENGINE-AND-GATES.md`](audio-rebuild3/SPEC-ENGINE-AND-GATES.md) | 361 | The engine percepts and the gate replacement, measured against the delivered master. **This is the file whose gate suite passed a two-second loop tiled 16.5 times** — `BROKEN-INSTRUMENTS.md` §I.1. |
| [`audio-rebuild3/SPEC-CHAIN-AND-GLASS.md`](audio-rebuild3/SPEC-CHAIN-AND-GLASS.md) | 491 | The shared chain, the glass breach and the non-engine layers, likewise measured rather than designed. |

## 4. Handover notes — historical, read for the record

These are snapshots of a moment. They are kept because a superseded decision's
measurement is usually still the useful part, and because this project does not
delete documents that turned out to be wrong.

| file | lines | state it captures |
|---|---|---|
| [`RESUME-HERE.md`](RESUME-HERE.md) | 117 | 2026-08-04, at a hard weekly usage limit, log at 425 entries. `R2-1050` records that it once told the next reader to redo a change that had already been landed, measured and reverted — corrected in place, with the correction stated rather than the line quietly replaced. |
| [`SESSION-HOLD.md`](SESSION-HOLD.md) | 80 | 2026-08-07, log at 685 entries. Its blocker list is closed. |
| [`NEXT-REBUILD.md`](NEXT-REBUILD.md) | 246 | Everything one rebuild had to carry before the master could start. That rebuild happened and shipped as `assembly15` / `film25_breach.blend`. Its asphalt re-budget row is marked **WRONG** in place by `R2-3061`. |

## 5. Data artefacts in `docs/` — 38 files

These are not documentation; they are **records that cannot be regenerated**.
Re-running the tool that made one cannot restore it — it can only produce a
different verdict under the same filename — which is why they are in git at all.
Several are deliberately named `_SUPERSEDED_` or `_CANDIDATE`: a candidate sheet
is not the shipped sheet, and `R2-1099` cost ten hours to a fix that was
generated into a candidate and never promoted.

### Generated sources of truth — prefer these over the prose

| file | what it holds |
|---|---|
| `beat_sheet.json` | the six beats, frame budgets and per-beat camera intent, machine-readable. **Authoritative where `beat_sheet.md` disagrees** (`R2-417`). |
| `circuit_spec.json` | the circuit as data: datum, corner geometry, surfaces, elevation. Schema `f1-round2/circuit_spec/1.0`. |
| `item_manifest.json` | one row per physical object the item campaign owns. Schema `f1-round2/item_manifest/1.0`. |
| `explode_plan.json` | the beat-1 explode: measured car bbox, ride height, per-cluster offsets. The entry that produced it (`R2-001`) is the one where the brief's stated axis turned out not to be the car's. |

### Measurements and verdicts

| file(s) | what they record |
|---|---|
| `driver_placement.json`, `R2_3361_driver_placement.json`, `driver_containment.json` | where the driver sits in the cockpit, and whether he is inside the aperture on the frames that show him. Successive dated re-measurements, kept side by side. |
| `r2_3361_cockpit_surface.json` | the cockpit surface the placement was solved against. |
| `collision.log`, `collision_anim.json`, `collision_anim.log` | the collision gate's output over the animation — the gate whose ranking by `tri_pairs` put a correctly-placed pit wall at #1 (`R2-017`). |
| `placement.log`, `normals.log`, `camrig.log`, `beat1_anim.log`, `inventory_iter.log`, `build_audit.log`, `fix_audit.log` | run logs kept as the evidence behind specific entries. They are quoted by ID in the log. |
| `frame_peeps.json` | the frame-sampling plan for pixel-peeping: speed and lens bands across all 2,978 frames. |
| `proposed_tiers.json`, `tiering_inputs.json` | the detail-tier proposal, and its inputs stamped with sha256 — written after `#97`, where a report changed on an unchanged blend because its inputs were rebuilt underneath it and nothing recorded that. |
| `horizon_pre_R2112_path.json`, `seam_pre_R2064_path.json`, `seam_pre_R2064_sheet.json`, `subject_sweep_pre_R2085_path.json` | **before-state snapshots**, named for the entry that changed the thing. They exist so a later measurement has something to be a difference from. |
| `manifest_blend1.tsv` | the `.blend1` sweep: what was deleted, its size, and what superseded it. |
| `r2_4020_waitmem_timeline.tsv` | a half-second-resolution memory timeline from `R2-4020` — RSS, high-water mark, available memory and swap through one build. |
| `*_CANDIDATE.json` (`R2451_`, `R2464_`, `R2829_`, `R2851_`, `beat_sheet_R2731_PONT_CAMERA_`) | beat sheets and presentation normals that were generated, measured, and **not promoted**. Kept under names no pipeline step writes to. |
| `*_SUPERSEDED_*.json` (`frame_peeps_`, `proposed_tiers_` ×2, `tiering_inputs_`) | outputs superseded by a later camera or a later contract, named for what superseded them. |

## 6. The engineering log and its staging files

**How an entry gets written.** Agents append to a `STAGING-R2-<lo>-to-R2-<hi>.md`
file; a coordinator merges staging into `DEFECT-LOG-R2.md` **by identity, never
by position**. Staging files are then historical — they record what was staged
under what number, and are not rewritten when the log is later corrected.

**Two things to know before you use the filenames as an index:**

1. **The range in a filename is where entries were *meant* to go, not what is
   inside.** Measured: `STAGING-R2-1761-to-R2-1820.md` contains only `R2-17`
   headings; `STAGING-R2-4021-to-R2-4080.md` contains `R2-4021` … `R2-4255`. The
   table below gives the range **actually inside each file**. To find one entry,
   grep rather than guess:

   ```bash
   grep -rn '^## R2-1401 ' docs/
   ```

2. **Everything in the tracked staging files is already merged.** Measured
   2026-08-18: of the 794 distinct IDs across the 71 tracked staging files,
   **zero** are missing from `DEFECT-LOG-R2.md`. `docs/README.md` still carries a
   line saying `R2-4024 … R2-4152` are unmerged; that was true when written and
   was closed by commit `8c8d601`. Corrected in place there, and stated here so
   the correction is not only in one file.

**Ten staging files are not tracked** and will not be in a clone:
`STAGING-R2-1121-to-R2-1150`, `-1271-to-1400`, `-1401-to-1450`, `-1541-to-1600`,
`-1661-to-1700`, `-1701-to-1760`, `-1821-to-1880`, `-1981-to-2040`,
`-3541-to-3600`, `-3661-to-3720`. Their entries were measured against the merged
log: **all but one are present in `DEFECT-LOG-R2.md`.** The single entry that
exists nowhere in the tracked tree is **`R2-1661`**. `WAVE2-RANKING.md` is
likewise untracked and is cited by `README.md` §"Historical". Whether those
files are promoted before publication is the owner's decision; the loss if they
are not is one log entry and one ranking document, not ten files' worth.

### The 71 tracked staging files

| file | entries | ID range actually inside | first entry |
|---|---|---|---|
| [`STAGING-R2-281-to-R2-295.md`](STAGING-R2-281-to-R2-295.md) | 2 | R2-278 … R2-299 | R2-298 — three corrections the recovered frames force, two of them to my own conclusions |
| [`STAGING-R2-383-to-R2-400.md`](STAGING-R2-383-to-R2-400.md) | 18 | R2-293 … R2-400 | R2-383 — nine predictions about the 89.79 m event, committed before the data |
| [`STAGING-R2-401-to-R2-410-carproxy-reopen.md`](STAGING-R2-401-to-R2-410-carproxy-reopen.md) | 3 | R2-4 | R2-4xx — six predictions, committed before the reopened search |
| [`STAGING-R2-401-to-R2-415.md`](STAGING-R2-401-to-R2-415.md) | 10 | R2-401 … R2-410 | R2-401 — the driver is 92 % helmet, and that is the whole of the finding |
| [`STAGING-R2-416-to-R2-450.md`](STAGING-R2-416-to-R2-450.md) | 28 | R2-416 … R2-443 | R2-416 — rung 1's cost is BEAT-INDEPENDENT, and the master's is not |
| [`STAGING-R2-451-to-R2-470.md`](STAGING-R2-451-to-R2-470.md) | 20 | R2-429 … R2-470 | R2-451 — the film looks 84.15 degrees down because `presentation_normals.py` was asked which direction show… |
| [`STAGING-R2-501-to-R2-520.md`](STAGING-R2-501-to-R2-520.md) | 16 | R2-501 … R2-517 | R2-501 — every number in the establishing station's own comment block was from a superseded solve, and the … |
| [`STAGING-R2-521-to-R2-540.md`](STAGING-R2-521-to-R2-540.md) | 14 | R2-521 … R2-534 | R2-521 — TRANSMISSION IS NOT THE CAUSE. It is exactly zero, and the control that says so is a rendered A/B,… |
| [`STAGING-R2-541-to-R2-580.md`](STAGING-R2-541-to-R2-580.md) | 11 | R2-541 … R2-551 | R2-541 — the pass this gate was opened on is not finished; it is 26 % of the way through, and every one of … |
| [`STAGING-R2-581-to-R2-600.md`](STAGING-R2-581-to-R2-600.md) | 8 | R2-581 … R2-588 | R2-581 — the corrected instrument, rebuilt from scratch, and the negative controls it has to fail |
| [`STAGING-R2-589-to-R2-600.md`](STAGING-R2-589-to-R2-600.md) | 6 | R2-589 … R2-594 | R2-589 — the instrument for a framing decision, and the control it has to fail |
| [`STAGING-R2-601-to-R2-620.md`](STAGING-R2-601-to-R2-620.md) | 9 | R2-601 … R2-609 | R2-601 — the wall does un-break, but not the half everybody has been measuring, and not for the reason the … |
| [`STAGING-R2-621-to-R2-650.md`](STAGING-R2-621-to-R2-650.md) | 14 | R2-504 … R2-634 | R2-621 — R2-504's architecture claim is TRUE, and it is now confirmed from two independent directions rathe… |
| [`STAGING-R2-651-to-R2-680.md`](STAGING-R2-651-to-R2-680.md) | 16 | R2-547 … R2-666 | R2-651 — the rubber is painted 4.96 m from where the car drives, and the module predicted this failure in w… |
| [`STAGING-R2-701-to-R2-730.md`](STAGING-R2-701-to-R2-730.md) | 6 | R2-701 … R2-706 | R2-701 — WHAT THE 58.6 % DESCRIBES, and it is not the car anyone will see |
| [`STAGING-R2-731-to-R2-760.md`](STAGING-R2-731-to-R2-760.md) | 10 | R2-731 … R2-740 | R2-731 — the three occlusions: one closed in source, one is not a defect, and one is a rejected fix |
| [`STAGING-R2-761-to-R2-790.md`](STAGING-R2-761-to-R2-790.md) | 30 | R2-700 … R2-790 | R2-761 — THE DEBRIS IS ABSENT BY CONSTRUCTION, AND THE MASS THAT IS MISSING IS 14.398 kg, EXACTLY, AND THE … |
| [`STAGING-R2-791-to-R2-820.md`](STAGING-R2-791-to-R2-820.md) | 20 | R2-791 … R2-807 | R2-791 — THE BRIEFED MEASUREMENT WAS TAKEN FROM THE WRONG BLEND |
| [`STAGING-R2-821-to-R2-850.md`](STAGING-R2-821-to-R2-850.md) | 41 | R2-116 … R2-842 | R2-821 — the client's three notes are TWO defects, and framing is not the cause of the pacing one |
| [`STAGING-R2-851-to-R2-880.md`](STAGING-R2-851-to-R2-880.md) | 12 | R2-851 … R2-862 | R2-851 — the closing wide contains a 91.5 deg/s whip pan, and the film's law forbids one |
| [`STAGING-R2-881-to-R2-910.md`](STAGING-R2-881-to-R2-910.md) | 0 | — | (no `## R2-` heading — prose or a range banner only) |
| [`STAGING-R2-911-to-R2-940.md`](STAGING-R2-911-to-R2-940.md) | 8 | R2-700 … R2-918 | R2-911 — THE FOURTH HYPOTHESIS DIES, AND IT TAKES THE QUESTION WITH IT. NOTHING IS TOUCHING THE CAR — CLOSE… |
| [`STAGING-R2-941-to-R2-970.md`](STAGING-R2-941-to-R2-970.md) | 29 | R2-941 … R2-965 | R2-941 — the flying lap ends 4.15 m before the line, and the beat boundary is 0.018 s after it |
| [`STAGING-R2-971-to-R2-990.md`](STAGING-R2-971-to-R2-990.md) | 16 | R2-862 … R2-986 | R2-971 — PRE-REGISTERED. Twelve falsifiers, written before a single frame of this arm existed. |
| [`STAGING-R2-971-to-R2-999.md`](STAGING-R2-971-to-R2-999.md) | 18 | R2-971 … R2-988 | R2-971 — THE 4K MASTER DOES NOT FIT, AND THE STATED GAP WAS TOO SMALL |
| [`STAGING-R2-1001-to-R2-1030.md`](STAGING-R2-1001-to-R2-1030.md) | 13 | R2-591 … R2-1013 | R2-1001 — the 8.04 s "one third size" defect is real as a NUMBER and false as a PICTURE. At 4K the car is a… |
| [`STAGING-R2-1031-to-R2-1060.md`](STAGING-R2-1031-to-R2-1060.md) | 7 | R2-1031 … R2-1037 | R2-1031 — the surface is not untextured; its detail is authored in octaves the film's camera cannot resolve… |
| [`STAGING-R2-1061-to-R2-1090.md`](STAGING-R2-1061-to-R2-1090.md) | 12 | R2-84 … R2-1072 | R2-1061 — R2-1042's frame was rendered in a rig whose sun is 139.6° from the film's, and that is 100 % of t… |
| [`STAGING-R2-1091-to-R2-1120.md`](STAGING-R2-1091-to-R2-1120.md) | 8 | R2-1091 … R2-1098 | R2-1091 — THE BLAST RADIUS OF THE STALE CAMERA IS SMALL, AND IT IS ALL IN BEAT 1 |
| [`STAGING-R2-1151-to-R2-1180.md`](STAGING-R2-1151-to-R2-1180.md) | 7 | R2-1084 … R2-1157 | R2-1151 — R2-1084's timeline is wrong. `docs/beat_sheet.json` was not edited at 05:03. |
| [`STAGING-R2-1181-to-R2-1210.md`](STAGING-R2-1181-to-R2-1210.md) | 9 | R2-1181 … R2-1189 | R2-1181 — the +31.3 dB frame-1 defect REPRODUCES, exactly, and the fix holds |
| [`STAGING-R2-1211-to-R2-1240.md`](STAGING-R2-1211-to-R2-1240.md) | 9 | R2-1211 … R2-1227 | R2-1211 — the rubber is painted over 34 m where there is no slip, and absent over the 24 cm where all of it is |
| [`STAGING-R2-1241-to-R2-1270.md`](STAGING-R2-1241-to-R2-1270.md) | 8 | R2-1241 … R2-1248 | R2-1241 — `db.claim` IS cross-process atomic, and the obvious control does not prove it |
| [`STAGING-R2-1601-to-R2-1660.md`](STAGING-R2-1601-to-R2-1660.md) | 6 | R2-1601 … R2-1606 | R2-1601 — THE FILM HAS ONE FLAT STRETCH OF 82.5 SECONDS, AND IT IS NOT THE OPENING |
| [`STAGING-R2-1761-to-R2-1820.md`](STAGING-R2-1761-to-R2-1820.md) | 5 | R2-17 | R2-17xx — #115: THE PATH-SCOPE RULE IS NOW A HOOK, AND ITS FIRST ACT WAS TO REFUSE ITS OWN AUTHOR |
| [`STAGING-R2-1881-to-R2-1980.md`](STAGING-R2-1881-to-R2-1980.md) | 23 | R2-1881 … R2-1902 | R2-1881 — `min_depth_m` 4.577 m IS THE GRASS. Every tree in the top 11 was ranked on the vegetation layer's… |
| [`STAGING-R2-2041-to-R2-2100.md`](STAGING-R2-2041-to-R2-2100.md) | 3 | R2-2041 … R2-2043 | R2-2041 — two proven fixes that could not reach a frame, applied and verified IN THE ARTEFACT |
| [`STAGING-R2-2101-to-R2-2160.md`](STAGING-R2-2101-to-R2-2160.md) | 11 | R2-1146 … R2-2111 | R2-2101 — `film21_breach.blend` does not exist because two collections wanted the same name |
| [`STAGING-R2-2161-to-R2-2220.md`](STAGING-R2-2161-to-R2-2220.md) | 15 | R2-2161 … R2-2178 | R2-2161 — THE 85-SECOND FLAT RUN DOES NOT EXIST. It is one argument passed to one function. |
| [`STAGING-R2-2221-to-R2-2280.md`](STAGING-R2-2221-to-R2-2280.md) | 3 | R2-2221 … R2-2230 | R2-2221 — the gate now covers the film |
| [`STAGING-R2-2231-to-R2-2280.md`](STAGING-R2-2231-to-R2-2280.md) | 4 | R2-2231 … R2-2234 | R2-2231 — `claim` was all-or-nothing, so it misreported its own state |
| [`STAGING-R2-2281-to-R2-2340.md`](STAGING-R2-2281-to-R2-2340.md) | 3 | R2-2281 … R2-2283 | R2-2281 — `vastctl status` and `vastctl reap` were both blind to the entire |
| [`STAGING-R2-2341-to-R2-2400.md`](STAGING-R2-2341-to-R2-2400.md) | 1 | R2-2341 | R2-2341 — #97 (REOPENED): THE REPORT IS REPRODUCIBLE, THE NUMBER IS NOT A PROPERTY OF THE WORLD, AND THE SH… |
| [`STAGING-R2-2401-to-R2-2460.md`](STAGING-R2-2401-to-R2-2460.md) | 10 | R2-2401 … R2-2409 | R2-2401 — FRAME NOMINATION, WRITTEN BEFORE ANY FRAME WAS OPENED |
| [`STAGING-R2-2461-to-R2-2520.md`](STAGING-R2-2461-to-R2-2520.md) | 5 | R2-2461 … R2-2465 | R2-2461 — THE REINSTATING ARGUMENT, IN ONE SENTENCE, QUOTED |
| [`STAGING-R2-2521-to-R2-2580.md`](STAGING-R2-2521-to-R2-2580.md) | 0 | — | (no `## R2-` heading — prose or a range banner only) |
| [`STAGING-R2-2581-to-R2-2640.md`](STAGING-R2-2581-to-R2-2640.md) | 8 | R2-2581 … R2-2588 | R2-2581 — the answer up front |
| [`STAGING-R2-2641-to-R2-2700.md`](STAGING-R2-2641-to-R2-2700.md) | 7 | R2-2641 … R2-2647 | R2-2641 — the answer up front |
| [`STAGING-R2-2701-to-R2-2760.md`](STAGING-R2-2701-to-R2-2760.md) | 11 | R2-2701 … R2-2711 | R2-2701 — the answer up front |
| [`STAGING-R2-2761-to-R2-2820.md`](STAGING-R2-2761-to-R2-2820.md) | 9 | R2-2761 … R2-2769 | R2-2761 — THE FIRST THING I DID WAS REBUILD THE RIG, AND IT MOVED THE DEFECT |
| [`STAGING-R2-2821-to-R2-2880.md`](STAGING-R2-2821-to-R2-2880.md) | 7 | R2-2821 … R2-2827 | R2-2821 — `rig_preflight` had never executed, and could not have |
| [`STAGING-R2-2881-to-R2-2940.md`](STAGING-R2-2881-to-R2-2940.md) | 9 | R2-2881 … R2-2890 | R2-2881 — THE HEADLINE: THE CLIENT'S NOTE IS INVERTED. THE GRASS IS FINE; THE ASPHALT IS BLANK. |
| [`STAGING-R2-2941-to-R2-3000.md`](STAGING-R2-2941-to-R2-3000.md) | 11 | R2-1381 … R2-2999 | R2-2941..R2-2949 — the trees were never within 74 metres, and the ranking that put them first was measuring… |
| [`STAGING-R2-3001-to-R2-3060.md`](STAGING-R2-3001-to-R2-3060.md) | 25 | R2-3001 … R2-3024 | R2-3001 — the probe, and what it cost |
| [`STAGING-R2-3061-to-R2-3120.md`](STAGING-R2-3061-to-R2-3120.md) | 7 | R2-3061 … R2-3066 | R2-3061 — THE ANSWER IS (b), AND IT IS READ OFF THE ARTEFACT |
| [`STAGING-R2-3121-to-R2-3180.md`](STAGING-R2-3121-to-R2-3180.md) | 7 | R2-2821 … R2-3126 | R2-3120 — THE NEGATIVE CONTROL RAN, AND IT FAILED. The bar is not vacuous. |
| [`STAGING-R2-3181-to-R2-3240.md`](STAGING-R2-3181-to-R2-3240.md) | 8 | R2-2521 … R2-3188 | R2-3181 — #155a: the clamp is gone, and the private reader with it |
| [`STAGING-R2-3241-to-R2-3300.md`](STAGING-R2-3241-to-R2-3300.md) | 9 | R2-3241 … R2-3249 | R2-3241 — THE ANSWER, IN ONE LINE |
| [`STAGING-R2-3301-to-R2-3360.md`](STAGING-R2-3301-to-R2-3360.md) | 11 | R2-3301 … R2-3311 | R2-3301 — the camera tracks a car that is not in the scene |
| [`STAGING-R2-3361-to-R2-3420.md`](STAGING-R2-3361-to-R2-3420.md) | 11 | R2-3308 … R2-3371 | R2-3361 — THE CHAIN IN R2-3308 IS WRONG ABOUT LINK 5, AND THE CORRECTION NAMES THE ACTUAL MISTAKE |
| [`STAGING-R2-3421-to-R2-3480.md`](STAGING-R2-3421-to-R2-3480.md) | 1 | R2-3421 … R2-3432 | R2-3421..R2-3432 — task #160: does the world READ as repetitive? The 2.03 % is a number that could not have… |
| [`STAGING-R2-3481-to-R2-3540.md`](STAGING-R2-3481-to-R2-3540.md) | 6 | R2-3481 … R2-3486 | R2-3481 — THE DRIFT LIST: SIX OF TEN, AND THE FINGERPRINT IS HONEST |
| [`STAGING-R2-3601-to-R2-3660.md`](STAGING-R2-3601-to-R2-3660.md) | 7 | R2-3602 … R2-3608 | R2-3602 — THE BISECT WAS CONFOUNDED BY THE INTERPRETER |
| [`STAGING-R2-3721-to-R2-3780.md`](STAGING-R2-3721-to-R2-3780.md) | 2 | R2-3721 … R2-3736 | R2-3721..R2-3736 — task #162: the variety gate now sees the trees, and the trees are measured for the first… |
| [`STAGING-R2-3781-to-R2-3840.md`](STAGING-R2-3781-to-R2-3840.md) | 1 | R2-3781 … R2-3796 | R2-3781..R2-3796 — the last four items: the tiering that promoted them is a host measurement, and the item … |
| [`STAGING-R2-3841-to-R2-3900.md`](STAGING-R2-3841-to-R2-3900.md) | 23 | R2-3841 … R2-3864 | R2-3841 — WHICH BLEND, AND WHY IT IS NOT FILM26 |
| [`STAGING-R2-3901-to-R2-3960.md`](STAGING-R2-3901-to-R2-3960.md) | 27 | R2-3901 … R2-3927 | R2-3901 — HANDOVER TAKEN MID-CYCLE-3, AND THE ORPHAN MODEL IS NOW MECHANICAL |
| [`STAGING-R2-3961-to-R2-4020.md`](STAGING-R2-3961-to-R2-4020.md) | 1 | R2-4020 | R2-4020 — THE SWEEP AFTER THE GITIGNORED BUILD INPUT, AND FOUR MEASUREMENT PASSES THAT RAN OUTSIDE THE LOCK |
| [`STAGING-R2-4021-to-R2-4080.md`](STAGING-R2-4021-to-R2-4080.md) | 74 | R2-4021 … R2-4255 | R2-4021 — THE PRORES 422 HQ MASTER IS ENCODED AND VERIFIED |
| [`STAGING-R2-4081-to-R2-4140.md`](STAGING-R2-4081-to-R2-4140.md) | 7 | R2-4079 … R2-4087 | R2-4081 — WHAT THE BENCHES IN THIS PASS HAD ALREADY ESTABLISHED |
| [`STAGING-R2-4141-to-R2-4200.md`](STAGING-R2-4141-to-R2-4200.md) | 12 | R2-4064 … R2-4152 | R2-4141 — THE FIRST MEASUREMENT: THE INHERITED BUILD WAS THE REJECTED ONE, AGAIN |

## 7. Documentation that lives outside `docs/`

Module documentation sits beside the module it describes, because a `.md` two
directories away from its `.py` goes stale without anyone noticing.

| file | lines | what it covers |
|---|---|---|
| [`../world/WORLD_CONTRACT.md`](../world/WORLD_CONTRACT.md) | 795 | The single source of truth for anything two or more modules share. Ownership rules: who is allowed to create what. |
| [`../world/build_surface.md`](../world/build_surface.md) | 1,309 | The driving surface — asphalt, its relief, its wear, and the budget it is built to. |
| [`../world/build_terrain.md`](../world/build_terrain.md) | 1,109 | Landform, treeline, undergrowth, grass. The vegetation library lives here. |
| [`../world/build_barriers.md`](../world/build_barriers.md) | 1,067 | Armco, catch fence and the runoff platform. |
| [`../world/build_architecture.md`](../world/build_architecture.md) | 798 | The built environment: showroom, pit buildings, grandstands. |
| [`../world/build_dressing.md`](../world/build_dressing.md) | 599 | Trackside dressing and how it is scattered. |
| [`../world/build_sky.md`](../world/build_sky.md) | 479 | The sky, the sun and the air between them — the file that exists because no HDRI was allowed. |
| [`../world/build_items.md`](../world/build_items.md) | 244 | The stage between `world/items/` and `assemble.py`, and the gate verdict an item must carry to be placed. |
| [`../world/items/HUMAN-REFERENCE.md`](../world/items/HUMAN-REFERENCE.md) | 2,186 | Read before building any figure item. The hardest asset class, worked out once. |
| [`../world/items/REFERENCE.md`](../world/items/REFERENCE.md) | 185 | Read before writing any item module. One item built end to end as the worked example. |
| [`../render/world/assembly/r2/SHIPPING.md`](../render/world/assembly/r2/SHIPPING.md) | 523 | **Which assembly is the shipping world, and why it was promoted.** More load-bearing than it looks: the film build appends onto a prebuilt world and does not rebuild it. |
| [`../watch/INDEX.md`](../watch/INDEX.md) | 390 | The only place that says which artefact is current. Everything in `watch/` is a claim about the film whether it was meant as one or not. |
| [`../watch/audio/INDEX.md`](../watch/audio/INDEX.md) | 229 | The listening pass, and the client's verdict on each of the five audio rebuilds, verbatim. |
| [`../tools/publication/README.md`](../tools/publication/README.md) | 257 | The sanitiser, the canary procedure that proves it can fail, and why "run once, then trust" is not good enough for a corpus that is still moving. |
| [`../round2_inventory.md`](../round2_inventory.md) | 242 | STEP ZERO: what round 1 actually produced, inventoried before any round-2 planning. |
| [`../round1_source/PROVENANCE.md`](../round1_source/PROVENANCE.md) | 146 | Why a 2.4 MB build *recipe* was vendored instead of the 288 MB artefact it produces. |
| [`../sim/out/R2-195_PREDICTIONS.md`](../sim/out/R2-195_PREDICTIONS.md) | 246 | Breach continuity predictions, **written before the data existed**. |
| [`../work/r2187/PREDICTION.md`](../work/r2187/PREDICTION.md) | 137 | `R2-187`…`194` predictions, written before the apply finished and before any frame was rendered. |
| [`../render/world/assembly/r2/v124/PREDICTION.md`](../render/world/assembly/r2/v124/PREDICTION.md) | 123 | What assembly9 must differ from assembly8 in — written before the diff ran. |

The three `PREDICTION.md` files are a house convention rather than an accident:
**write down what you expect to see before you look**, so that a result cannot
be read as confirming whatever was believed at the time. Several of the log's
sharpest entries exist because a prediction file disagreed with the outcome.

---

## Re-deriving the counts on this page

```bash
# tracked files in docs/, markdown vs data
git ls-files docs/ | wc -l
git ls-files docs/ | grep -c '\.md$'

# entries in the merged log
grep -cE '^## R2-' docs/DEFECT-LOG-R2.md          # headings
grep -oE '^## R2-[0-9]+' docs/DEFECT-LOG-R2.md | sort -u | wc -l   # distinct IDs

# which file holds an entry
grep -rn '^## R2-1401 ' docs/

# staging IDs that are NOT in the merged log (expected: none)
comm -23 \
  <(grep -hoE '^## R2-[0-9]+' docs/STAGING-*.md | grep -oE '[0-9]+' | sort -u) \
  <(grep -hoE '^## R2-[0-9]+' docs/DEFECT-LOG-R2.md | grep -oE '[0-9]+' | sort -u)
```

If any of those disagree with the numbers above, **the command is right and this
page is stale.** Append the correction rather than editing the number out — that
is the house rule everywhere else in this corpus and it applies here too.
