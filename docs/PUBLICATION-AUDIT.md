# Publication audit — f1-round2

### A full-history secret scan, and what is still exposed under each publishing option

Audit date: 2026-08-18. Scope: **every object in the git object database**, not
only the working tree — 1,930 blobs, 1,742 trees, 647 commit objects, plus the
one `refs/notes/commits` note and the 228 uncommitted working-tree changes.

---

## 0. THE BLOCKER THAT NO SCAN CAN CLEAR

> ## The vast.ai API key must be rotated by the account owner before either repository is published.
>
> This is **not** conditional on what the scan found. The key was written to
> disk in plaintext at `~/.config/vastai/vast_api_key` and, in the sibling
> `vast-render` repository, a fragment of it reached a tracked source file and a
> commit message. A key that has existed in plaintext outside a secret manager
> must be treated as disclosed. Scrubbing a repository removes the *record* of a
> key; it does not remove the *exposure*. Rotation is the only thing that does,
> and only the account owner can perform it.
>
> Rotate at <https://console.vast.ai/> → Account → API keys: issue a new key,
> update `VAST_API_KEY` in the environment and `~/.config/vastai/vast_api_key`,
> then **delete the old key server-side** so the disclosed value stops being
> able to rent, destroy and spend.
>
> Until that is done, treat the publication date as irrelevant: the risk is
> already live.

---

## 1. Verdict for this repository

**GO for publication on secrets — with one content fix and one owner decision.**

| Class | Result |
|---|---|
| vast.ai API key (full, 64 hex) | **0 occurrences** anywhere in history or tree |
| vast.ai API key (first 16 hex) | **0 occurrences** |
| vast.ai API key (first 8 hex) | **0 occurrences** |
| Private-key headers (RSA/EC/OPENSSH/PGP) | 0 |
| AWS / GCP / Azure credentials | 0 |
| GitHub / Slack / Stripe / OpenAI / Anthropic / npm / PyPI / HF tokens | 0 |
| JWTs, `Authorization: Bearer` headers | 0 |
| `.env`, `.netrc`, `*.pem`, `*.key`, `id_rsa`, credentials files — **ever committed** | 0 |
| High-entropy strings not explained as a path, hash or identifier | **0** |
| Real routable IP addresses | **3** — see §4, needs a fix |
| Personal email in commit author/committer fields | **601 of 638** commits — see §5, owner decision |

The two items that are not zero are dealt with in §4 and §5. Neither is a
credential.

---

## 2. How the scan was done, and why a zero here is worth something

**A search proves nothing unless the needle is real.** An earlier pass on this
project ran `git log -S` against an API-key prefix that had been *guessed*
rather than read, got zero hits, and briefly concluded the history was clean.
That result was worthless. This audit was built to not repeat it.

**The needle was read, not guessed.** The live key was read from
`~/.config/vastai/vast_api_key` (65 bytes: 64 lowercase hex characters plus a
newline), which establishes the vast.ai key format as **64 lowercase hex**. The
key itself appears nowhere in this document. Its SHA-256, which is safe to
publish and lets the owner confirm which key was audited, is:

```
8e41ee3c9ac96fd77d06379d6bd18ec66d7b90a07fe409f131a2d64a11224aed
```

**The scanner was proved to work before any zero from it was believed.** A
throwaway repository was built with four secrets committed and then *deleted* in
a later commit, so that they survived only in history — exactly the case that
matters:

```
$ git init canary && cd canary
$ printf 'VAST_API_KEY=%s\n' "$PLANT" > .env          # fake 64-hex vast key
$ printf -- '-----BEGIN RSA PRIVATE KEY-----\n...' > id_rsa
$ printf 'aws_key = "AKIAIOSFODNN7EXAMPLE"\nghp_abc...' > leak.py
$ git add . && git commit -m "oops: commit credentials"
$ git rm .env id_rsa leak.py && git commit -m "remove credentials"
$ printf '...?api_key=%s\n' "$REAL_KEY" > real_leak.txt   # the LIVE key
$ git add real_leak.txt && git commit -m "planted real key"
$ git rm real_leak.txt && git commit -m "removed"
$ git ls-files            # working tree is empty — nothing left to see
$ python3 scan.py canary
```

Result — every planted secret found, in blobs no longer reachable from the tree:

```
blobs_scanned 4 commits 4
SUMMARY: {
 "LIVE_VAST_KEY_FULL": 1,
 "LIVE_VAST_KEY_PREFIX16": 1,
 "LIVE_VAST_KEY_PREFIX8_ANYCTX": 1,
 "PLANTED_CANARY": 1,
 "aws_akia": 1,
 "github_tok": 1,
 "hex64": 2,
 "private_key_hdr": 1
}
secret_filenames: [['214d9fad…', '.env'], ['491aaa85…', 'id_rsa']]
```

Only after that did a zero from this scanner mean anything. The same scanner,
unchanged, then found **6 real hits in the sibling `vast-render` repository**
(documented in that repo's own `docs/PUBLICATION-AUDIT.md`), which is a second,
independent demonstration that it is not silently returning zeros.

**Object enumeration used `git cat-file --batch-all-objects`**, which walks the
entire object database including objects unreachable from any ref — not
`rev-list HEAD`, which would miss exactly the blobs an amended or reset commit
leaves behind. This mattered: in `vast-render` it surfaced one key-bearing blob
that no ref points at.

```
$ git cat-file --batch-all-objects --batch-check='%(objecttype)' | sort | uniq -c
   1930 blob
    647 commit
   1742 tree
```

Commit **messages** were scanned as well as commit contents, and commit
author/committer identities separately. Git notes were scanned. The 228
uncommitted working-tree changes were scanned on disk, since they are not yet
objects.

---

## 3. The one number that looked alarming and is not: 676 sixty-four-character hex strings

A 64-lowercase-hex string is exactly the shape of a vast.ai API key. This
repository contains 676 of them, 171 distinct. **Every one is a content hash,
and none is the key.**

```
$ python3 triage.py /home/zany/f1-round2
hex64 occurrences (full history) = 676
hex64 DISTINCT values            = 171
live key present among distinct hex64? False
```

They live in the provenance records the build writes for every generated
asset — `render/items/*/gate.json`, `world/items/PLACEMENT.json`,
`world/car_anim_car.json` — and in the staging logs, always as a `"sha256":`
field or a `file → hash` table:

```
"bytes": 170986,
"sha256": "3b9d07043cf326992a7e23b195498364727c1ddd3610e78168856cf8dd246220"
```

This is worth stating explicitly because it is the failure mode that makes
secret scanning hard in this repository specifically: a project that records the
hash of everything it builds looks, to a pattern matcher, exactly like a project
that has leaked hundreds of API keys. The distinguishing test is not the shape,
it is whether the live key is among them. It is not.

The entropy sweep tells the same story. 5,466 strings of 24+ characters scored
above 4.4 bits/byte; **every single one** classified as a filesystem path or a
multi-word identifier, with **zero residue**:

```
$ python3 entropy_full.py /home/zany/f1-round2
repo=/home/zany/f1-round2  total high-entropy tokens=5466
     4911  filesystem-path
      555  identifier/prose
  DISTINCT RESIDUE VALUES = 0
```

Likewise the 8 `secret_assign` hits are test assertions, not secrets —
`want_token="RIG_PREFLIGHT_OK"`, `want_token="FILM_MATERIALS_OK"` in
`tools/film_bar.py` — and the 4 email matches are the GitHub noreply address
used as an *example* in `README.md` and `tools/publication/`.

---

## 4. The one real finding: the sanitiser ships its own de-aliasing table

Three real routable IP addresses of rented vast.ai GPU hosts survive in the
current tracked tree. All three are in **one file**:

```
$ git grep -l -F "host-A"   # and the other two
tools/publication/sanitise_docs.py
```

```python
IPS = {"host-A": "host-A",
       "host-B":   "host-B",
       "host-C": "host-C"}
```

The documentation was correctly sanitised — those addresses appear in the docs
only as `host-A`/`host-B`/`host-C`. But `sanitise_docs.py` is itself tracked, so
**shipping the sanitiser ships the lookup table that undoes it.** Anyone with
the published repository can reverse every alias in the docs by reading line 194.

This is the same class of mistake the sibling repository already caught and
documented in its `.gitignore`, about a different file:

> *"Anyone holding both files joins them on those values and recovers every
> identifier the aliasing was for. While this file was tracked, the docs'
> redaction was cosmetic."*

**Recommended fix (owner's call, not applied by this audit):** move the `IPS`
table out of the tracked file and load it from an untracked local file, or
gitignore `sanitise_docs.py` itself, or replace the real addresses with the
RFC 5737 documentation-range placeholders the file already uses elsewhere
(`203.0.113.77`, `198.51.100.4` — those are reserved-for-documentation and are
correctly *not* a leak).

These are third-party hosts' addresses, not the owner's. The severity is
"discloses which machines were rented", not "grants access".

In **history**, the same three addresses also appear un-aliased in earlier
versions of `docs/DEFECT-LOG-R2.md` and `docs/STAGING-R2-3841-to-R2-3900.md`
(130, 26 and 16 occurrences respectively across all blobs). Fixing the current
file does not remove them from history — see §6.

Everything else IP-shaped is clean: `127.0.0.1`, `0.0.0.0`, `1.1.1.1`,
`8.8.8.8`, the RFC 5737 ranges, and `5.2.0.1`, which is not an address at all —
it is the Blender version in the sanitiser's own comment explaining that
version-shaped strings are excluded.

**No LAN/private-range IPs, no machine hostnames, and no references to the
private `f1-site-part2` website appear anywhere in the tracked tree** (`git grep
-l "f1-site-part2"` → 0 files). Three references to the *part-1* domain
`f1-opus5.aipulsedaily.ai` exist in `docs/MASTER-PLAN.md`; that site is already
public, so this is disclosure of nothing.

---

## 5. Personal identity in commit metadata — the owner's decision

Not a secret, but it is personal data, and it is the single largest
privacy question in this repository.

```
$ git log master --pretty='%ae' | sort | uniq -c | sort -rn
    567 <owner-personal-address-1>@gmail.com     [redacted in this document]
     34 <owner-personal-address-2>@gmail.com     [redacted in this document]
     15 agent@local
     11 r2-3841@f1round2
      5 r2-3001@f1round2
      3 noreply@users.noreply.github.com
      1 r2-4150@f1-round2.local
      1 claude@local
      1 agent@f1-round2
```

**601 of 638 commits on `master` carry one of two personal Gmail addresses** in
the author or committer field. Before this audit the addresses appeared *only*
in commit metadata: `git grep` found them in **zero tracked files**.

> **Disclosure — this audit briefly made that worse, and the fix is incomplete.**
> The first draft of this document pasted the `git log` output above verbatim,
> with both addresses unredacted, and committed it. They are redacted in the
> working tree now, but the earlier versions are already blobs in this
> repository's history:
>
> ```
> 1936f22b002f297e5dc58f947a484dbb4f0711c5   docs: full-history secret audit…
> f7348f9dad171993ded70e2d6758a13de7141260   docs: correct the commit-identity…
> ```
>
> History was **not** rewritten to remove them, because rewriting is the
> owner's decision and this round was explicitly scoped not to. The practical
> effect is small — the same addresses are already in 601 commit author fields,
> so these two blobs disclose nothing that Option A does not disclose anyway —
> but under **Option B or C the blob content must be scrubbed as well as the
> author metadata**, or the redaction will be undone by two commits that were
> supposed to be documenting the problem.
>
> It is recorded here rather than quietly fixed because this is the exact
> failure this repository's `docs/BROKEN-INSTRUMENTS.md` exists to catalogue:
> a check that reports clean while the thing it checks is broken. An audit that
> leaks the data it is auditing is that, in miniature.

Future commits are already safe. `.git/config` in both repositories now sets

```
user.name  = SuperComboGamer
user.email = 36320904+SuperComboGamer@users.noreply.github.com
```

which is GitHub's standard `ID+username@users.noreply.github.com` privacy
address — designed to be public, and the correct thing to commit under. It
attributes commits to the account without exposing a personal mailbox. This
fixes what comes next and changes nothing that already exists.

*(Audit note: this setting changed during the audit — at 03:39 on 2026-08-18 it
was still the generic `noreply@users.noreply.github.com` in both repos. The
value above is the state at the time of writing. Re-check it with
`git config --show-origin --get user.email` before publishing rather than
trusting this document.)*

Also present in tracked files, and not personal but identifying of the build
machine: **322 tracked files contain the literal string `/home/zany`**. That is
a username in a path, not a credential.

---

## 6. What remains exposed under each of the three publishing options

The choice of publishing strategy is the owner's. This audit does not make it,
and **no history was rewritten in producing this document.** Here is what each
option actually leaves behind.

### Option A — publish as-is, with full history

Ships: 638 commits of genuine engineering history, all SHAs stable, all 220
in-doc SHA citations still resolving.

Still exposed:
- Two personal Gmail addresses in 601 of 638 commit author/committer fields,
  permanently, in a form GitHub displays on every commit page.
- Three real vast.ai host IPs, in the current `sanitise_docs.py` **and** in
  historical versions of two docs.
- `/home/zany` in 322 tracked files.
- **No credentials.** The key is not here in any form.

### Option B — `git filter-repo` rewrite (mailmap + IP replacement)

Ships: all 638 commits with rewritten identities and scrubbed blobs.

Fixes: the Gmail addresses in every commit; the historical IP occurrences; the
`/home/zany` paths if a blob-content replacement is included.

Cost, measured rather than assumed:

```
$ # distinct 7-40 char hex strings in docs that resolve to a real commit
$ ... 81 distinct SHAs, cited in 220 places across docs/ and *.md
```

**Every one of those 220 citations goes stale**, because a rewrite changes every
SHA from the first rewritten commit onward. The engineering log is the most
valuable thing in this repository and it cites its own history by SHA; a rewrite
silently turns 220 of those references into dangling identifiers. If this option
is chosen, the rewrite must be followed by a mechanical old-SHA → new-SHA
rewrite pass over `docs/`, using the mapping `git filter-repo` writes to
`.git/filter-repo/commit-map`. That pass is not optional and it is not
difficult, but skipping it degrades the documentation.

Still exposed after B: nothing from the credential classes; the third-party host
IPs only if the replacement list is incomplete.

### Option C — fresh single-commit init

Ships: the current tree, one commit, clean identity.

Fixes: everything in metadata, everything in history, at once. The unreachable
blob problem disappears because there is no history to hold one.

Cost: **638 commits of real engineering history are lost**, and with them the
ability to read the append-only log against the changes it describes. For a
project whose distinguishing feature is an honest record of what was tried and
what turned out to be wrong, this is the option that destroys the most value.
The in-doc SHA citations become references to commits that no longer exist
anywhere, which is worse than B's stale-but-mappable references.

Still exposed after C: the three IPs in `sanitise_docs.py`, since they are in
the current tree — Option C does not fix a present-tense leak. Fix §4 first
regardless of which option is chosen.

### A hazard that applies to all three: how the repository is copied

This repository holds **40 unreachable objects** — 22 blobs, 14 trees, 4
commits — left behind by amended or reset commits:

```
$ git rev-list --all --reflog --objects | wc -l      # 4279 reachable
$ git cat-file --batch-all-objects --batch-check | wc -l   # 4319 in the ODB
$ git fsck --unreachable | awk '{print $2}' | sort | uniq -c
     22 blob
      4 commit
     14 tree
```

Some of them carry the un-aliased IPs of §4. Whether they travel depends on the
copying method, and this was **tested in the sibling repository** rather than
assumed:

- `git push` / clone over the pack protocol → **only reachable objects move.**
- `git clone /local/path` → hardlinks the entire object database, unreachable
  objects **included**.
- Tarring or `rsync`-ing the `.git` directory → carries everything.

Publishing by pushing to GitHub is therefore the safest mechanism. Run
`git gc --prune=now` before any hand-off that is not a push.

### Recommendation

§4 must be fixed before any option. Beyond that, A and B are both defensible and
the choice is about how much the owner minds their address being on 601 public
commits; C is not recommended, because it pays the highest price for a problem
that B solves. **This repository's secret posture is clean under all three.**

---

## 7. Reproducing this audit

The scanner is not checked in — it reads the live key in order to search for it,
and a tool that does that should not be a tracked file. To reproduce:

1. Enumerate every object with `git cat-file --batch-all-objects --batch-check`,
   not `rev-list HEAD`.
2. Read the real key from `~/.config/vastai/vast_api_key`; derive needles for the
   full value, the first 16 characters and the first 8.
3. Add format patterns for private-key headers, `AKIA`/`ASIA`, `AIza`,
   `ghp_`/`github_pat_`, `xox[abposr]-`, `sk-`/`sk-ant-`, `ya29.`, `npm_`,
   `hf_`, JWT triplets, `Authorization: Bearer`, and 64-lowercase-hex.
4. Add a Shannon-entropy sweep over 24+ character tokens at ≥ 4.4 bits/byte, and
   **classify the hits** rather than eyeballing them — in this repository the
   raw count is 5,466 and the meaningful count is 0.
5. **Plant a secret in a scratch clone, delete it in a later commit, and confirm
   the scanner still finds it, before believing any zero.**

Step 5 is the one that was skipped last time.
