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
python3 tools/publication/sanitise_docs.py          # idempotent
```

**The alias map must be rebuilt from `c18c9f4~1`** — the tree as it stood before
the first sanitisation commit. `alias_canon.txt` is that map. Rebuilding it from
a later tree renumbers every existing alias, which silently breaks the one
property the aliases exist to preserve: that `mach-11` means the same host in
every document that mentions it. **Identity across time is the finding** —
"the same machine refused our key 61 h apart" cannot be stated if the alias
moves between documents.

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

## One known, deliberate exception

`R2-3868` states a balance of `$154.87` in the clear. That is not an oversight.
The surrounding passage already gives `~$139 of $150` and `~72 h needed`, so the
burn rate falls straight out and the balance is recoverable by multiplication
regardless. **A redaction that can be reversed by arithmetic is worse than none,
because it implies a protection that does not exist.** The figure is stated where
it does work, and every other runway number in the corpus was coarsened so that
`burn × runway` no longer reconstructs anything.

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
