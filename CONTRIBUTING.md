# Contributing to f1-round2

This repository is the source and the engineering record of a finished film. It
is not a library, it has no API, and there is no roadmap. What it has is a
**method**, and the method is the thing worth preserving — so this document is
mostly about how work is recorded rather than how code is formatted.

Read [`docs/BROKEN-INSTRUMENTS.md`](docs/BROKEN-INSTRUMENTS.md) before you read
the rest of this file. Everything below is a consequence of it.

---

## The one rule

**A change that fixes something must say how the fix was measured.**

Not "tested". Not "verified". *Measured* — with the number before, the number
after, and what instrument produced them. This project's largest defect class,
recorded twenty-six times, is a check that returned the same answer whether the
defect was present or absent. The defence against it is not more care; it is
being specific enough that a reader can tell whether the measurement could have
come out differently.

Three questions a fix should answer somewhere:

1. **What did you measure, and what did it read before?**
2. **Could that measurement have failed?** If you cannot describe an input that
   would have produced a different answer, you have not measured anything.
3. **Did you look at the artefact?** For anything visual or audible: open the
   frame, play the sound. *"A metric quoted without opening the frame is a
   claim, not evidence"* (`R2-430`).

---

## The engineering log

`docs/DEFECT-LOG-R2.md` is append-only and is the repository's primary output.
If you fix a defect, add an entry.

**Numbering.** Entries are `## R2-nnnn — one-line finding`, not zero-padded.
[`docs/DUPLICATE-ID-SWEEP-R2.md`](docs/DUPLICATE-ID-SWEEP-R2.md) holds the next
free number and the ranges that are reserved or vacated. Take the next free
number and update that table in the same change.

**Where to write.** Add to a `docs/STAGING-R2-<lo>-to-R2-<hi>.md` file, not to
the log directly. Staging is merged into the log by identity, never by position.
If you must touch the log, append; never edit an entry to make it right.

**Four conventions, each of which exists because of a specific incident:**

| convention | why |
|---|---|
| **Entries are never edited to be right.** A later entry corrects an earlier one and *both stay*. | *"A document that silently changes its mind teaches nobody anything"* (`R2-1050`). `R2-430` retracts `R2-429` and then carries a correction saying the retraction's own replacement number was also wrong. Follow the chain forward. |
| **Staging files are historical.** They record what was staged under what number and are not rewritten when the log is later corrected. | Otherwise there is no way to reconstruct what a citation meant. |
| **A range banner may cover several numbers in one heading.** | `## R2-3721..R2-3736 — …`. Heading count and allocated-number count differ, deliberately. |
| **On an ID collision, the entry that external code and briefs already cite keeps the number; the other moves, whole.** | Measured by citation weight, not by seniority. The method and the evidence are in `DUPLICATE-ID-SWEEP-R2.md`, which was committed *before* any renumbering. |

**A good entry states what was believed, what was measured, and what the
measurement turned out to mean — including when the first diagnosis was wrong.**
The most-read entries in this log are the ones where the author is the person
being corrected. Retractions are welcome here and are not a mark against anyone;
[`docs/READING-LIST.md`](docs/READING-LIST.md) §2 is nothing but retractions and
is one of the more useful sections.

---

## Gates, controls, and verdicts

If you add or change a check:

- **A gate must be able to fail.** Ship a **positive control** — something the
  gate *must* reject — alongside it. A gate that has never failed has not been
  shown to work (`R2-110`, `R2-151`).
- **A gate must not pass an empty set.** Exit `*_VACUOUS`, never `PASS`, when
  there was nothing to test. `R2-018` is the founding case: two gates printed
  green having tested zero of zero.
- **Print what you tested, not just the verdict.** A pass that does not name its
  subject cannot be distinguished from a pass over nothing.
- **Print the distribution next to the threshold.** A threshold and the quantity
  it judges are one instrument; changing either alone silently rescales the
  verdict and neither half announces it (`R2-2172`).
- **Emit the verdict line.** Every gate prints
  `>> STAGE RESULT: <VERDICT>` — e.g. `PLACEMENT_CLEAN`, `COLLISION_VACUOUS`,
  `FILM_BAR_PASS`. **Callers grep for that line, not for an exit status**,
  because Blender 5.2 exits 0 on an uncaught exception (`R2-2824`). If you write
  a caller, do not trust `$?` from a Blender run, and set `pipefail` if you pipe
  it anywhere.

`tools/docs_relink.py` is a small worked example of the shape: it can fail, it
refuses to write a result it cannot verify, and it reports a
`DOCS_RELINK_VACUOUS` rather than a pass when it examined nothing.

---

## Predictions

Where a change has a predicted effect, **write the prediction down before you
look at the result.** Three files in this repository do it — `sim/out/`,
`work/r2187/` and `render/world/assembly/r2/v124/` each hold a `PREDICTION.md`
written before the data existed. Several of the log's sharpest entries exist
only because a prediction file disagreed with the outcome and neither could be
quietly reinterpreted afterwards.

---

## Code

There is no linter, no formatter, no test runner and no CI. What there is:

- **Everything is a script.** No packaging, no `requirements.txt`, no imports
  across module boundaries except through the contracts in
  `world/WORLD_CONTRACT.md`.
- **Two interpreters.** Code under `world/`, `sim/` and most of `render/` runs
  *inside* Blender 5.2.0 LTS through `bpy`. Code under `tools/` may run under
  either — check for `HAVE_BPY` before assuming.
- **Paths use `~/f1-round2`.** In Python, `os.path.expanduser("~/f1-round2/…")`;
  in shell, `$HOME/f1-round2/…`. Never an absolute home directory: this is a
  publication requirement, not a style preference, and
  `tools/publication/sanitise_docs.py` will find it if you do.
- **A module owns its slice and knows nothing about the others.** Adding a
  cross-module assumption means adding it to `world/WORLD_CONTRACT.md` first.
- **New item modules** start from `world/items/REFERENCE.md`, and figures from
  `world/items/HUMAN-REFERENCE.md`. An item needs an accepted gate verdict
  before `world/build_items.py` will place it, and the builder refuses rather
  than warns.

Run `python3 tools/docs_relink.py` before committing documentation changes; it
exits non-zero if a link into the defect log has drifted.

---

## Commits

- **The subject states the finding, not the file that changed.** `world: the
  variety gate could not see linked duplicates` beats `update build_terrain.py`.
  The history is meant to be readable as a narrative and largely is.
- **`git add` path-scoped, never `git add -A`.** An 11.25 GB delivery master
  once sat untracked with nothing but that convention protecting it; there is an
  ignore rule now, and the convention still applies.
- **Never `git commit --amend` in a shared checkout.** `R2-234` records an
  `--amend` rewriting a different agent's commit because another commit had
  landed and become `HEAD` in between. It was repaired with `git notes`, not a
  rebase.
- **Set a noreply identity before your first commit:**

  ```bash
  git config user.email 'ID+username@users.noreply.github.com'
  git config user.name  'Your Name'
  ```

- **Do not rewrite history.** The documentation cites 83 distinct commit SHAs in
  218 places, and a rewrite de-references all of them. If a rewrite is ever
  done, it must be followed by a mechanical old→new SHA remap across the corpus
  using `git filter-repo`'s `commit-map`. See
  [`docs/PUBLICATION-AUDIT.md`](docs/PUBLICATION-AUDIT.md) §6.

---

## Publishing, and what must never land

- **No secrets, ever.** No API keys, tokens, credentials or account balances,
  in code, in documentation, or in a log paste. `docs/PUBLICATION-AUDIT.md` is
  the standing scan.
- **No personal data.** No home directories, no hostnames, no personal email
  addresses, no private site names. `tools/publication/sanitise_docs.py` is the
  tool and `tools/publication/README.md` explains why it must be re-run rather
  than trusted.
- **No downloaded, purchased, sampled or AI-generated assets.** This is the
  project's second hard rule after the single take, and a contribution that
  breaks it cannot be accepted whatever else it does. Everything is built from
  code in this repository.

---

## Licence of contributions

By contributing you agree that your contribution is licensed on the same terms
as the file it lands in: **GPL-3.0-or-later** for code and **CC BY-SA 4.0** for
documentation, as set out in [`LICENSE`](LICENSE). There is no CLA and no
copyright assignment.

The rendered film, its frames and its audio masters are **not** covered by
either grant and are not distributed with this repository. Renders you make by
running this code are yours.
