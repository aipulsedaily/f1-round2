# Sanitising the CODE, not just the prose — 322 tracked files → 0

The first sanitisation pass cleaned `.md` and `.txt`. It was correct for what it
covered and it reported a clean run, twice. The number it never printed is the
one that mattered:

```
$ git ls-files -z | xargs -0 grep -lIE '/home/[a-z][a-z0-9_-]*' | wc -l
322
$ git ls-files -z | xargs -0 grep -hoIE '/home/[a-z][a-z0-9_-]*' | wc -l
1200
```

(Written against `/home/<name>` rather than against the actual login, so this
document does not reintroduce the string it is about. Both commands print `0`
today.)

**Only 3 of those 1,200 occurrences were in a `.md`.** The other 1,197 were in
Python, shell, JSON and logs — 135 `.py`, 64 `.sh`, 96 `.json`, 23 `.log`,
`.gitignore`, and one extensionless bash script — and a tool that globs on
`*.md`/`*.txt` cannot see any of them however many times it is re-run.

That is this repository's own signature defect wearing publication clothes: a
check that reports clean because of where it looked, not because of what is
there. `docs/BROKEN-INSTRUMENTS.md` catalogues the same shape in a limiter that
reported 0.124 dB while removing 22.

## The result

| | before | after |
|---|---|---|
| tracked files carrying the home directory or the login | **322** | **0** |
| occurrences of the login in tracked files | **1200** | **0** |
| tracked files stamping the workstation's hostname | **50** | **0** |
| occurrences of the hostname | **46** | **0** |
| tracked files carrying an email address | 3 | 3 — all `…@users.noreply.github.com`, checked, benign |
| tracked files naming the private companion site | 1 | 0 |
| LAN/private-range IPs, MAC addresses | 0 | 0 |

Reproduce both numbers with the two commands at the top of this file.

## Why a path in code could not be treated like a path in prose

Prose gets the better documentation: `/home/<user>/f1-round2/world/build_terrain.py`
becomes `world/build_terrain.py`, which is more useful than the original because
it is the path a reader can act on.

**Code gets opened.** These scripts are launched by Blender with `-P` from
whatever directory the caller happened to be standing in, so making a literal
relative would change which file it opens — silently, and only sometimes. So
the policy is per-language, and it is chosen so that **the resolved value is
byte-identical on the machine this repository was built on**:

| file class | `/home/<user>/f1-round2/x` becomes | why |
|---|---|---|
| `.md` `.txt` | `x` | repo-relative reads better than an absolute path |
| `.json` `.log` | `x` | inert records; nothing resolves a path out of them at runtime, and repo-relative is what you want when diffing a verdict |
| `.sh` | `$HOME/f1-round2/x` | the shell expands it to the original |
| `.py` | `os.path.expanduser("~/f1-round2/x")` | Python does **not** expand `~`, so the literal cannot simply become `~/…` |

`$HOME` and `expanduser("~")` both give back the original absolute path on the
owner's machine, so nothing that ran yesterday stops running. For a stranger who
clones into `~/f1-round2` they resolve correctly too — which the hard-coded
original never did, so the scripts are strictly more portable than before.

`import os` was added to 32 Python files that needed it and did not have it.
Only module-level `import os` / `import os.path` counts as having it: `from os
import path` binds `path`, not `os`, and would have left a `NameError` behind a
rewrite that looked finished.

## The four things a regex would have got wrong, and how each was caught

Each of these went through a full run of the first version of the extended tool
and came out looking correct.

**1. Docstrings are prose that happen to be string literals.** Roughly half the
scripts open with a docstring quoting the exact Blender command line used to run
them, home directory and all. Wrapping those in `os.path.expanduser` would turn
documentation into an expression and change nothing about how the file runs.
They are told apart by POSITION, from the AST, not by "is it triple-quoted" —
because a triple-quoted string is also how several of these files hold a heredoc
they hand to a subprocess.

**2. Implicit string concatenation.** Python joins `"a" "b"` into one string.
Wrapping only the first piece produces `os.path.expanduser("a") "b"`, a syntax
error — and worse, a path split across the pieces is in NEITHER piece as far as
a per-token search is concerned, and not in the joined source either, because
the quotes sit in the middle of it. `prove_items_cheap.py` splits the session
scratchpad path exactly on that boundary. The first version of the rewriter
found nothing there, rewrote nothing, warned about nothing, and reported a clean
run over a file that still named the owner. The joint has to be made on the
string VALUES, which is what the interpreter concatenates. Two real paths in
this repository are written this way, one of them the argument to
`bpy.ops.wm.open_mainfile`.

**3. Quoted heredocs.** Every heredoc in this repository is `<<'PY'`, the quoted
form, inside which the shell expands nothing at all. Writing `$HOME` there
produces a program that opens a directory literally named `$HOME`. A whole-file
regex over `.sh` would have got every one of them wrong, and silently: the
script would still run and still print a verdict. The shell pass now walks line
by line tracking heredoc state, and the eight lines inside quoted heredocs were
fixed by hand with `os.path.expanduser` — they are Python, not shell.

**4. Shell quoting is a state machine, and it crosses lines.** One line looked
single-quoted and unfixable:

```sh
$B -b $A10 --factory-startup --python-expr "
...
_reg = json.load(open('/home/<user>/f1-round2/world/items/PLACEMENT.json'))
```

Those single quotes are Python's, inside a shell double-quoted argument opened
eight lines earlier, so the shell **does** expand `$HOME` and the rewrite is safe
and automatic. Carrying the quote state across lines fixed that — and
immediately broke nineteen other lines, because these scripts are heavily
commented in English and every "doesn't" and "script's" opened a string that
never closed. The state machine now skips comments. A checker that over-reports
is not the safe direction; it buries the real hits.

Also corrected on the way: the substitution was originally `"$HOME"`, which is
the better shell idiom in isolation and produces `""$HOME"/f1-round2/x"` when
spliced into a string that was already double-quoted — still resolvable by the
shell, no longer valid Python once the heredoc is read.

## The hostname, which nothing was looking for

46 tracked records stamp the authoring workstation's real hostname beside the
run timestamp — 33 item-gate verdicts under `render/items/`, plus the tiering
inputs and the placement records:

```json
{"stamped_at": "2026-08-04T01:42:17", "host": "<name>", ...}
```

**Not one of them contains a home directory.** Every check aimed at `/home/`
walked past all 46, and the publication audit's claim that "no machine hostnames
appear anywhere in the tracked tree" was false when it was written. The
pass-2 file filter had the same hole and was widened for the same reason: a
record whose only personal datum is a machine name must not be skipped by a
home-directory-shaped test.

They are **aliased, not removed**: `"host": "workstation"`. The field's whole job
is to say "measured on the local box, not on a rented one", which is exactly the
distinction the `mach-NN` aliases exist to keep readable elsewhere.

`"host"` is two schemas here and only one of them is a machine —
`{"host": "ARCH_PitWall", "host_verts": 24664}` is a 3D object an item sits on —
so the substitution is keyed to the detected hostname, not to the field name, and
the tool now prints every distinct value the field takes with a mark against each.

## The tool no longer contains what it removes

After a complete, verified run, the last occurrence of the owner's login in the
entire repository was **inside the sanitiser**, which is excluded from its own
corpus by design. The finished repository would have published the login in the
one file claiming to remove it.

The login is now **measured from the corpus** rather than hardcoded — whichever
`/home/<name>` is actually present, reported by name and count, with an explicit
"nothing to do" when the tree is already clean. It is deliberately not taken
from the environment either: this script gets run as root, in containers and
under sudo, and `$USER` there makes every path rule match nothing while the
report still says APPLIED.

`SANITISE_LOGIN=<name>` overrides it, which is what the canary procedure needs
now that the tree is clean. The canary recipe in
`tools/publication/README.md` was likewise changed to an **unquoted** heredoc, so
`$HOME` expands when the canary is planted and the document itself never carries
the login. It also plants `.py` and `.sh` copies: pass 1 and pass 2 are different
code on different file types, and a canary that only ever lands in a `.md` proves
nothing about the 1,197 occurrences that were not in one.

## A GitHub account id is also eight digits

`36320904+name@users.noreply.github.com` — the leading number is a GitHub
account id, nothing to do with a rented host. The 8-digit rule aliased it to
`id-083` and **appended it to `alias_canon.txt`**, which by its own charter can
never drop an entry again. It corrupted the one document that tells the owner
what to commit under, and polluted the permanent map, in one pass.

Caught by dry run, reverted, and guarded by SHAPE rather than by blacklisting
the number, because the account can change and the shape cannot. The guard is in
**two** places: the substitution, and the discovery loop that decides what gets
appended to the map. Forgetting it in the discovery loop is the more expensive
of the two — the document would have come out correct and the map would have
been permanently wrong.

`--verify-canon` still passes at 82 identifiers, id-001…id-082 unchanged.

## What was verified, and how

Not "it looks right". Each of these is a command that can fail:

- **135 changed `.py` compile**, 0 failures — `compile(open(f).read(), f, 'exec')`.
- **65 shell scripts pass `bash -n`**, 0 failures.
- **96 changed `.json` parse**, 0 failures. The tool also refuses to WRITE a
  `.py` that will not compile or a `.json` that will not parse, so a bad rewrite
  leaves the file alone and says so rather than shipping.
- **The Python embedded in the five quoted heredocs compiles**, extracted and
  checked separately, because `bash -n` sees a heredoc as an opaque string.
- **Every rewritten path still resolves to what it resolved to before.** For each
  changed `.py`, walk the NEW ast, find every `os.path.expanduser(<const>)`,
  expand it with `HOME=/home/<user>`, and require that the resulting absolute path
  was literally present in the OLD blob. 170 calls checked, 0 failures. For each
  changed `.sh`, substitute `$HOME` back and require the line existed: 95 lines,
  0 failures. This is the load-bearing check — it is the difference between "the
  file still parses" and "the file still opens the same thing".
- **A canary was planted in all four file classes and proved to fire** before the
  real run, including the split-literal and single-quote cases, then deleted.
- **A full `--apply` was rehearsed on a throwaway clone first**, and every check
  above was run there before the real tree was touched.

## What was NOT done, and why

**No history was rewritten.** This is a commit, not a `filter-repo` run. Every
blob before it still holds all 1,200 occurrences and all 46 hostname stamps, and
`git log -p` still shows them. **Cleaning the tree does not clean Option A** —
see the corrected §6 of `docs/PUBLICATION-AUDIT.md`, where the three publishing
runbooks are priced against this.

**The 211 untracked-but-unignored files were not committed.** `.gitignore`
already frames that as an owner decision pass, and it is: 67 of them are `.py`
source, 14 are `.md`. They ARE sanitised in the working tree — the tool's corpus
includes untracked files on purpose, since a file is a publication risk from the
moment it is written — so whenever they are promoted they are already clean.

One finding for that decision, measured rather than asserted: **86 of them are
named by a file that IS tracked** — `docs/DEFECT-LOG-R2.md` alone cites dozens.
Published as-is, the repository cites 86 files it does not contain.

**The three vast.ai host IPs and the alias map in `tools/publication/` were left
alone.** They are the map; publishing it de-anonymises every `id-NNN` and
`host-X` in the corpus. Whether `tools/publication/` ships at all is a decision,
not a formatting question, and it is the owner's.

**The GitHub identity in `docs/PUBLICATION-AUDIT.md` was left alone.** It is the
privacy address GitHub issues, designed to be public, and it is the account that
will own the published repository. It is named here so the decision is made
rather than defaulted.

## Still a hard blocker, unchanged by any of this

**The vast.ai API key must be ROTATED before publication.** It sat on disk in
plaintext. A perfect scrub does not un-expose a key that existed; rotation is
the only fix and only the owner can do it. No amount of work in this repository
substitutes for it.

## Re-run before publishing

The corpus is a moving target — this pass alone found four staging documents and
a hostname class that appeared after the previous pass declared itself complete.

```sh
python3 tools/publication/sanitise_docs.py                 # dry run, both passes
python3 tools/publication/sanitise_docs.py --apply
python3 tools/publication/sanitise_docs.py --verify-canon
```

Exit status 3 means something was found that the tool would not decide on its
own. It is not a warning to skim past.
