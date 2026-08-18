# Publication sanitisation — RUN THIS AGAIN BEFORE YOU PUBLISH

`sanitise_docs.py` redacts the documentation for public release. `alias_canon.txt`
is its alias map.

**Both were rescued out of `/tmp` on 2026-08-15.** They were written to a
RAM-backed scratch directory, which is one reboot from gone, and the only
instruction to re-run them existed in a chat transcript. This project's own log
records the same failure repeatedly — a finding that lives only in a
conversation is a finding that is already lost — so they live here now.

## Why re-running matters, and it is not optional

**The corpus is a moving target.** During the sanitisation pass itself,
`docs/BROKEN-INSTRUMENTS.md` was created by a parallel agent carrying a raw
machine identifier, and four untracked `docs/STAGING-*.md` files appeared
needing the same treatment. A pass that was complete when it finished was
already incomplete an hour later.

**So: run this immediately before publication, not once and then trusted.**

## How to run it

```sh
cd /path/to/this/repo
python3 tools/publication/sanitise_docs.py                 # dry run, idempotent
python3 tools/publication/sanitise_docs.py --apply         # write
python3 tools/publication/sanitise_docs.py --verify-canon  # check the alias map
```

Exit status is meaningful: **3 means the corpus contains a machine id or an IP
address the script does not know how to redact.** It is not a warning to skim
past — those identifiers are being left in the clear.

### The alias map, and why it is append-only

**The map is rebuilt from `c18c9f4~1`** — the tree as it stood before the first
sanitisation commit. `alias_canon.txt` is that map. Rebuilding it from a later
tree renumbers every existing alias, which silently breaks the one property the
aliases exist to preserve: that `mach-11` means the same host in every document
that mentions it. **Identity across time is the finding** — "the same machine
refused our key 61 h apart" cannot be stated if the alias moves between
documents.

That used to be a rule you had to remember. It is now a property of the code:

- `alias_canon.txt` **is** the map, in allocation order; the alias is the line
  number. New identifiers are **appended** and take the next free number. The
  file is never sorted and nothing is ever removed from it.
- `--verify-canon` re-derives the first 82 entries from `c18c9f4~1` and checks
  them in order. It passes today. **Run it rather than trusting this sentence.**
- The machine-id list in the script is likewise frozen in allocation order, with
  a comment saying to append and not insert.

The previous version rebuilt the map by sorting whatever 8-digit numbers were in
the corpus at the time. On a corpus that had already been sanitised, that finds
only the *new* identifiers and numbers them from `id-001` — a total renumbering
with no error and no output that would have looked wrong.

### Three bugs the re-run found, recorded because they will recur

1. **The script rewrote its own alias map.** The file list matched `*.txt`
   repo-wide, and `alias_canon.txt` is a tracked `.txt` full of the very
   identifiers being redacted. A run would have replaced all 82 with their own
   aliases and destroyed the map. `tools/publication/` is now excluded.
2. **`alias_canon.txt` had no trailing newline**, so appending a new id would
   have produced `4752304941234567` — one corrupted entry, one missing entry,
   and a file that still parses. The append now checks the last byte.
3. **A new host IP would have passed silently.** `IPS` holds three hosts because
   three were in the corpus when it was written; a fourth was substituted by
   nothing and reported by nothing. There is now an IP-shape detector with an
   explicit benign list, and it was proved to fire on a planted address.

### The corpus now includes untracked files

A document is a publication risk from the moment it is written, not from the
moment it is committed — the last pass missed four staging documents for exactly
that reason. The file list is now tracked **plus** untracked-but-not-ignored
`.md`/`.txt`, minus `README`, `LICENSE`, `LICENSE-DOCS`, `NOTICE` and
`tools/publication/`.

## What it does, and what it deliberately does not

**Redacts:** absolute paths, session scratchpad paths, rented-host and instance
identifiers, account balances, the live-site hostname.

**Pseudonymises rather than blanks** host identifiers — `mach-NN`, `id-NNN`,
`host-A/B/C`, `fleetNN-LABEL`. Blanking them would delete the measurement while
leaving the prose looking intact.

**Keeps, on purpose:**

- **burn rates and costs** — `$0.4627/hr`, `$132.57 of the $150 ceiling` are
  engineering findings
- **client quotes verbatim**, typos and profanity included — they are the evidence
- **datacentre geographies** — load-bearing for the round-trip-time findings
- **every retraction and wrong prediction**

## The one deliberate exception has been RETIRED

The previous version of this file argued that `R2-3868` should keep its
`$154.87` balance in the clear, because the surrounding passage gave
`~$139 of $150` and `~72 h needed`, so the balance fell out by arithmetic anyway
— and **a redaction that can be reversed by arithmetic is worse than none,
because it implies a protection that does not exist.**

That reasoning was sound when it was written and is no longer true. Commit
`57f9f09` coarsened every other runway number in the corpus precisely so that
`burn × runway` stops reconstructing anything. Once that landed, the exception
lost the premise it stood on: the figure was no longer recoverable, so leaving it
was no longer a statement about arithmetic, just a balance in the clear.

It is now redacted, in both `docs/DEFECT-LOG-R2.md` and its staging copy. The
surrounding argument — 89.3 h of runway against ~72 h needed, and the margin
being thin enough that the next adverse event was worth surfacing — is untouched
and still reads.

**Keep the principle, drop the instance.** A redaction reversible by arithmetic
is still worse than none; that specific redaction just stopped being reversible.

## Before publishing, verify rather than assume

```sh
grep -rn "/home/[a-z]" docs/ watch/ --include=*.md | grep -v tools/publication

# exclude the well-known public addresses, or you will chase your own tail
grep -rnE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" docs/ watch/ --include=*.md \
  | grep -vE "127\.0\.0\.1|1\.1\.1\.1|8\.8\.8\.8|0\.0\.0\.0"

grep -rniE "api[_-]?key|secret|token|password" docs/ watch/ --include=*.md
```

Each should return nothing that is not an explanation of the redaction scheme
itself.

**Known benign hits, already checked so you need not re-check them:** `127.0.0.1`
is architecturally load-bearing throughout; `1.1.1.1` appears twice as a *ping
target* in a network-flap diagnosis and is Cloudflare's public resolver, not
anybody's host. The first run of the IP check above flagged both and neither was
a leak — **which is the point of stating them here rather than leaving the next
person to rediscover it.**

**And the deeper caution: a clean grep from a broken search is this project's
most-catalogued defect.** One audit in this repo reported a whole tree clean
because a recursive `grep` had suppressed stderr and bailed early on a 12 GB
directory; the per-file checks found the thing it had missed. **Before believing
a negative, confirm your search would have found the thing if it were there** —
plant a known string and check that it fires.

### The plant-and-prove procedure, written down so it is repeated and not improvised

Note the **unquoted** heredoc: `$HOME` is expanded when the canary is planted,
so the file on disk carries the real home directory while this document does
not. Writing the literal here is what left the author's login in the one file
that claims to remove it, through a complete and otherwise clean run.

```sh
cat > docs/ZZ-CANARY.md <<EOF
Path leak: $HOME/f1-round2/world/build_sky.py
Bare home leak: $HOME
IP leak: 203.0.113.77 and also 198.51.100.4:21104
Secret leak: api_key=CANARY0123
Machine leak: machine 99999 condemned
Vast id leak: instance 41234567
Balance leak: credit \$12.34 remaining
Code path leak, .py: ROOT = "$HOME/f1-round2/world"
Code path leak, .sh: cd $HOME/f1-round2
EOF
cp docs/ZZ-CANARY.md watch/ZZ-CANARY.md   # prove BOTH trees are reached
cp docs/ZZ-CANARY.md docs/ZZ_CANARY.py    # prove PASS 2 is reached as well
cp docs/ZZ-CANARY.md docs/ZZ_CANARY.sh
```

The `.py` and `.sh` copies are not decoration. Pass 1 and pass 2 are different
code on different file types, and a canary that only ever lands in a `.md`
proves nothing about the 1,197 occurrences that were in Python, shell, JSON and
logs. Delete `docs/ZZ_CANARY.py` before running with `--apply`.

Run all three greps and the sanitiser dry run. **Every one must report the
canary.** Then delete both copies, re-run, and only now is a clean result worth
something. The addresses above are RFC 5737 documentation ranges, so a canary
that escapes cannot be mistaken for a real host.

Two things this catches that a plain re-run does not:

- **Coverage.** `grep -rl "" docs/ watch/ --include=*.md | wc -l` against
  `find docs/ watch/ -name '*.md' -type f | wc -l` — the two numbers must be
  equal. That is the direct test for the bail-early failure, and it is one line.
- **Whether the tool can fail at all.** The IP detector in `sanitise_docs.py`
  exists only because the canary walked straight through a full run untouched
  and unreported. The re-run alone would have said "clean".

Never `--apply` with a canary in the tree: the run would append the fake
identifiers to `alias_canon.txt`, and the map is append-only, so they would be
there for good.

---

## `make_fresh_init.sh` — the other publication decision, built rather than described

The sanitiser cleans the documents. It does nothing about the **commit
metadata**, and that is the second and larger publication decision.

Most of this repository's ~635 commits carry a personal email address in their
author and committer fields. `.git/config` now sets
`user.email = noreply@users.noreply.github.com`, which fixes every FUTURE commit
and changes nothing that already exists. So the owner picks one of:

| | what you keep | what you give up |
|---|---|---|
| publish **with** history | 635 commits of provenance; `git log` reads as documentation | the address is public, permanently, in every mirror and fork |
| publish a **fresh init** | the address never appears | the entire log, and every SHA the docs cite |

`tools/publication/make_fresh_init.sh` builds the second option into
`../publish/f1-round2-fresh/` so it can be opened and weighed instead of
imagined. It copies **tracked files only**, `git init`s, commits once with the
noreply identity, verifies the result, and prints what was lost.

```sh
tools/publication/make_fresh_init.sh                 # ../publish/f1-round2-fresh
tools/publication/make_fresh_init.sh DEST --from-head
```

It never writes inside this repository, never deletes anything, refuses a
non-empty destination, refuses a destination inside any git repository, and
creates no remote.

**`--force` on the `git add` is load-bearing, not laziness.** This repository
deliberately tracks 70 files that its own `.gitignore` excludes — the item gate
verdicts under `render/`, the film-bar probes under `work/` — because they are
records that cannot be regenerated. The first run of the script copied 998 files
and committed 928; a plain `git add -A` had read the copied `.gitignore` and
dropped them all. The file-count check is what caught it, which is the argument
for having a verification step that can fail rather than a script that prints
"done".

### A correction to the received wisdom, which changes the decision

The reason given for ruling out a history **rewrite** was that the documentation
cites ~4,100 commit SHAs, so `filter-repo` would de-reference all of them.

**Measured, that is not what the corpus contains.** Resolving every hex token in
the tracked docs against this repository's object store:

```
distinct commit SHAs cited in tracked .md   82
occurrences of them                        214
distinct R2-NNNN entry ids                1474
occurrences of those                      8616
```

The ~4,100 figure is the scale of the **entry-ID** citations, which a rewrite
does not touch at all. The actual exposure is **82 SHAs**. That is still real
work, and `git filter-repo` emits a `commit-map` that makes rewriting them
mechanical. **A rewrite is a live third option and should be priced before the
fresh init is accepted** — it is the only one that keeps the provenance *and*
removes the address. Work on a clone; never on the only copy.
