# Publication audit — f1-round2

### A full-history secret scan, and what is still exposed under each publishing option

Audit date: 2026-08-18. Scope: **every object in the git object database**, not
only the working tree — 1,930 blobs, 1,742 trees, 647 commit objects, plus the
one `refs/notes/commits` note and the 228 uncommitted working-tree changes.

---

## 0. THE BLOCKER THAT NO SCAN CAN CLEAR — CLEARED 2026-08-18

> ## RESOLVED: the account owner reports the vast.ai API key was **revoked** on 2026-08-18, along with an SSH key.
>
> **Revocation is stronger than the rotation this section demanded.** A rotated
> key leaves the old one alive until it is deleted server-side; a revoked key
> cannot authenticate at all. The eight-character fragment in the sibling
> repository's history therefore describes a credential that no longer exists.
>
> **Two qualifications, and neither is a formality.**
>
> 1. **CLIENT-REPORTED, not measured.** Revocation was deliberately *not*
>    verified by calling the vast.ai API, because there is no read-only way to
>    ask whether a key is dead that does not involve presenting it — the test
>    would be the exposure, performed to check whether the exposure had closed.
>    Confirm it visually instead: console → Account → API keys, and the old key
>    is **absent from the list**.
> 2. **This does not mean the key was never exposed.** It sat in plaintext on
>    disk. That happened, and nothing below is retracted. Revocation is what
>    makes the disclosure harmless, not what makes it untrue.
>
> **This repository never contained the key or any fragment of it** — §1's scan
> covers that, and it was already true. This section was here because the two
> repositories share one account, and a live disclosed credential is a reason
> not to publish *anything* that advertises the account. That reason is gone.
>
> **The blocker as it stood while the key was live is kept verbatim below**, on
> the same principle as everything else in this document: the argument for why
> plaintext means disclosed is the argument that got the key revoked.

### The blocker as written (— 2026-08-18)

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
$ python3 triage.py ~/f1-round2
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
$ python3 entropy_full.py ~/f1-round2
repo=~/f1-round2  total high-entropy tokens=5466
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

> ### APPLIED, 2026-08-18 — the first option, and here is why not the third.
>
> The values — both the three addresses **and** the eighteen real vast.ai
> machine ids beside them, which this section did not count — now live in
> `tools/publication/host_canon.txt`, which is **gitignored**. The aliases stay
> in `sanitise_docs.py`. A clone gets the method, the reasoning and the alias
> vocabulary, which is everything that makes that file worth reading, and no way
> to invert any of it. This is the same fix, for the same reason, that the
> sibling repository applied in its `04648a38` — a commit whose subject is
> literally *"untrack the table that de-aliases the docs"*.
>
> **Not the placeholder option**, which was tempting and is worse. Substituting
> RFC 5737 addresses into `IPS` leaves a table that still *looks* authoritative
> and silently maps nothing — every future lookup missing, every alias quietly
> not applied, while the tool still reports success. That is precisely the
> failure `.gitignore` reasons about for `farm/hostrates.json` in the sibling
> repo: "the machine id IS the lookup key, so opaque labels would not break the
> leak, they would break the TABLE". **Absence is legible; a wrong table is not.**
>
> **Losing the file is safe, and that is the only thing that makes ignoring it
> defensible.** The map is needed to SUBSTITUTE, never to DETECT. With it gone,
> `MACH_SHAPE` and `IP_SHAPE` still fire on any unknown machine id or non-benign
> address and still report it — the check that actually protects a *new*
> document, and the one that caught a planted `203.0.113.77` canary going
> through a full run untouched. The tool says so on stderr and declines to
> rewrite. Verified both ways: with the map present, `18 machine aliases`,
> 0 files changed of 141 prose and 0 of 1049 code/records, `no unknown machine
> ids or IP addresses in the corpus`; with the map moved away, `0 machine
> aliases`, the same clean corpus, and the notice printed.
>
> **`alias_canon.txt` was deliberately left tracked**, and that is a different
> judgement, not an oversight. It holds 8-digit vast.ai *offer and instance*
> ids: opaque integers in one vendor's database, identifying nothing to anyone
> outside that account, routing nowhere. An IP address is *reachable* — that is
> the entire difference, and it is the same line drawn in the sibling repo's
> §4 about machine ids. `--verify-canon` also re-derives those 82 ids from
> `6970fdc~1`, so untracking the file would not remove them from a clone
> anyway; it would only break the verification.
>
> **What this does NOT fix: history.** These three addresses still appear
> un-aliased in earlier blobs of `docs/DEFECT-LOG-R2.md` and
> `docs/STAGING-R2-3841-to-R2-3900.md` (130, 26 and 16 occurrences), and the
> pre-sanitisation tree at `6970fdc~1` still holds every identifier in the
> clear. Fixing the current tree closes the *decoder ring* — the docs can no
> longer be inverted by reading a tracked file — but anyone willing to walk the
> history can still recover the addresses directly. **That is a live residual
> exposure and it is an Option B decision (`--replace-text`), not something a
> tree edit can reach.** See §6.

> ### RESOLVED, 2026-08-18 — the history is done too.
>
> Appended, not merged: the block above was accurate when written and "this does
> not fix history" is exactly the kind of admission that should survive being
> fixed. **A second `filter-repo` pass removed all three addresses from history**
> — 190 occurrences across 66 blobs, six tracked paths and one commit message,
> replaced with the same `host-A`/`host-B`/`host-C` aliases the corpus uses, so
> history and the sanitised tree now agree instead of contradicting each other.
>
> Two numbers in the paragraph above were also wrong and are corrected here
> rather than edited away. The occurrence counts "130, 26 and 16" are per-file
> counts of the current blobs; **across every object in the database the real
> figures are 139, 31 and 20** — 190 in total, of which four are in a *commit
> message*, which no blob-level count can see. The two-file list is short as
> well: `docs/STAGING-R2-1211-to-R2-1240.md`,
> `docs/STAGING-R2-3901-to-R2-3960.md` and **this audit file itself** also
> carried them, alongside the `sanitise_docs.py` table §4 is about — six paths,
> not two. The full method, the backup, the
> `refs/notes` re-check and the gate results are in §6, "UPDATE 2".

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

**No LAN/private-range IPs and no MAC addresses appear anywhere in the tracked
tree**, and no reference to the owner's private companion website does either.

**Two claims that stood here were wrong, and are corrected rather than quietly
edited**, because a publication audit that overstates its own coverage is worth
less than no audit:

- *"no machine hostnames"* was **false**. 46 tracked records stamped the
  authoring workstation's real hostname beside the run timestamp, as
  `"host": "<name>"` — 33 item-gate verdicts under `render/items/`, plus the
  tiering inputs and the placement records. Not one of them contains a home
  directory, so every check aimed at `/home/` walked straight past all 46. They
  are now aliased to `"host": "workstation"`, which is what the field was
  saying: measured on the local box rather than on a rented one. The sanitiser
  now surveys every value the field takes and prints the distinct set, so the
  next value it grows cannot pass in silence.
- *"three references to the part-1 domain in `docs/MASTER-PLAN.md`"* is **no
  longer true**: that file now contains zero. Whether it ever did is not
  re-checkable from here, and the number is repeated rather than re-derived,
  which is how a stale figure survives an audit.

The private site is deliberately not named again anywhere in this repository —
this file was the last tracked place it appeared, and naming it at all
discloses that it exists. Whether that matters is the owner's call, not the
sanitiser's.

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
> fb4f23145734aeae0362b1202030b3ec928a8fd2   docs: full-history secret audit…
> 40ba8b62680e0b3884a3e47e3ae4b39fedb86fa5   docs: correct the commit-identity…
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

Also present in tracked files when this audit was written, and identifying of
the build machine: **322 tracked files contained the owner's home directory** —
1,200 occurrences, of which only 3 were in a `.md` and the other 1,197 were in
Python, shell, JSON and logs, where the prose sanitiser never looked. That is a
username in a path, not a credential.

**That figure is now 0 tracked files and 0 occurrences.** `sanitise_docs.py`
grew a second pass with a per-language policy — `os.path.expanduser("~/…")` in
Python, `$HOME/…` in shell, repo-relative in the records, which is the more
useful form for reading a verdict — so the resolved path is unchanged on the
machine this was built on and a clone into `~/f1-round2` works too. See
`docs/SANITISATION-R2-CODE.md` for the before/after and the verification.

---

## 6. What remains exposed under each of the three publishing options

The choice of publishing strategy is the owner's. This audit did not make it,
and **no history was rewritten in producing this document** — but history *has*
been rewritten since, and the update below records it. Here is what each option
actually leaves behind.

> ### UPDATE, 2026-08-18 — OPTION B WAS CHOSEN AND EXECUTED. This section is now history, not a menu.
>
> Every commit's **author and committer** were rewritten to
> `SuperComboGamer <36320904+SuperComboGamer@users.noreply.github.com>` with
> `git filter-repo` 2.47.0. `%ae%` and `%ce%` were identical throughout, so
> rewriting only the author would have left the address in every commit.
>
> **`git log --all --format='%an <%ae>%n%cn <%ce>' | sort -u` now returns exactly
> one line.** Commit counts are unchanged, no `refs/original` remains, no remote
> exists, and nothing was pushed. A verified `git bundle` of the pre-rewrite
> history was taken first.
>
> **THE ONE THING THAT ALMOST GOT AWAY — read this before trusting any similar
> job.** A default `git filter-repo` run **does not touch `refs/notes/commits`**.
> Not a flag anyone forgot: it is deliberate, and the reason is in the tool's own
> source —
>
> ```python
> # refs/notes/ put commit-message-related material in blobs, and name their
> # files according to the hash of other commits.  That totally messes with
> # all normal callbacks; ...
> if commit.branch.startswith(b'refs/notes/'):
>   self._imported_refs.add(commit.branch)
>   commit.dump(self._output)
>   return          # <- dumped BEFORE any name/email callback runs
> ```
>
> This repository has exactly one note. Its notes commit was authored **and**
> committed by the personal Gmail, and `git rev-list --count HEAD` never sees it
> — which is why this repository's commit count reads 654 one way and 655 the
> other. So a filter-repo run that reported complete success left the personal
> address in a repository that every check so far had certified clean, and the
> only reason it was caught is that the run was **rehearsed on a throwaway mirror
> clone and the notes ref was checked by name**. `git clone` does not copy
> `refs/notes` either, so the rehearsal had to be a `--mirror`.
>
> The notes ref was therefore rebuilt by hand, and it needed three separate
> repairs, none of which any tool does for you:
>
> 1. the notes **commit** re-created with the correct identity, original dates
>    preserved;
> 2. the note **re-attached** — a note's *filename* is the SHA of the commit it
>    annotates, so after the rewrite it was hanging off a commit that no longer
>    existed and `git notes show` returned nothing;
> 3. the note's **body** repointed: it cites two commits in prose, inside a git
>    object that no `git ls-files` scan can see. One of them, `e4d1d90`, was
>    **unreachable** — it survived only in the reflog, filter-repo did not carry
>    it over, and the note's instruction to run `git show e4d1d90` is now
>    impossible. The note says so rather than pointing at a dead hash.
>
> **Citations were repointed too**: 272 occurrences of 93 distinct commits across
> 46 files, including a live code constant (`CANON_BASE_COMMIT` in
> `sanitise_docs.py`) and 18 cross-references to the sibling repository, which
> was rewritten in the same round. Verified against the pre-rewrite object
> database restored from the bundle: **zero stale citations.**
>
> What Option B did **not** fix, and what §4 and the options below still describe
> accurately: the rewrite changed identities, not content. Third-party IP
> addresses and rented-host identifiers remain in historical blobs. That needs
> `--replace-text` and is still an open decision.

> ### UPDATE 2, 2026-08-18 — HISTORY WAS REWRITTEN A SECOND TIME, for the IPs.
>
> The paragraph directly above closes with "that needs `--replace-text` and is
> still an open decision". It has been decided and executed. This is appended
> rather than merged into the entry above it because **there were two rewrites**,
> and anyone holding a clone taken between them holds a third set of SHAs.
>
> **What was removed and why.** The three real, globally routable IPv4 addresses
> of **rented vast.ai hosts — other people's machines**, which §4 identified and
> which a tree edit could not reach. They are the last third-party data in this
> repository.
>
> | | count |
> |---|---|
> | distinct routable addresses | **3** |
> | total occurrences | **190** |
> | distinct blobs carrying at least one | 66 |
> | commit **messages** carrying at least one | 1 (4 occurrences in it) |
> | tracked paths ever involved | 6 |
> | occurrences in **unreachable** objects | 0 |
> | occurrences inside **binary** blobs | 0 |
>
> The last two rows are not decoration. `filter-repo --replace-text` **skips any
> blob with a NUL in its first 8 KiB**, so an address inside a `.blend` or a
> rendered frame could not have been removed this way and would have had to be
> reported as unremovable rather than clean. There were none — checked, not
> assumed.
>
> **The substitution is the alias the tree already used**, so history and the
> sanitised corpus now say the same thing: `host-A`, `host-B`, `host-C`, and the
> `<addr>:21104` form as `host-A:PORT`, exactly as `sanitise_docs.py` writes them.
> The real values remain only in the **untracked, gitignored**
> `tools/publication/host_canon.txt`; §4's fix and this one are the same fix
> applied at two depths.
>
> **Method.** `git filter-repo` 2.47.0, `--replace-text` **and**
> `--replace-message` with the same map — both, because one of the occurrences
> was in a commit message and `--replace-text` cannot see those. Rehearsed on a
> throwaway `--mirror` clone and verified there before the real run, which
> reproduced the rehearsal's `HEAD` exactly.
>
> **Backup.** `git bundle --all` to `~/f1-round2-pre-ip-scrub.bundle`, verified
> with `git bundle verify`, and it carries `refs/notes/commits` as well as
> `master`. The earlier `~/f1-round2-prerewrite.bundle` is the *pre-identity*
> state and was **not** overwritten — it is the only copy of that state.
>
> **`refs/notes/commits`, checked again rather than assumed.** The trap above is
> real and it was re-tested: `filter-repo` still returns before its callbacks for
> anything under `refs/notes/`. This time it needed **no repair**, and the reason
> is worth recording because it is luck and not design — this rewrite's first
> changed commit is late enough that **402 of the 656 commits kept their SHAs**,
> including both the commit the note annotates and the commit its body cites, so
> the note was still correctly attached and still resolved. That was *verified*
> — `git notes show`, plus resolving every hash in the note body — not inferred
> from the tool reporting success. A controlled experiment first confirmed the
> failure mode is still live: in a throwaway repository whose annotated commit
> *did* change, the note came out of `filter-repo` hanging off a commit that no
> longer existed.
>
> **State after.** 656 commits on `master` (unchanged) plus the notes commit,
> **254 of 656 SHAs changed**, one identity across all refs, no tags, no
> `refs/original`, no remote, `git fsck` clean, nothing pushed. The 36 untracked
> run artefacts under `audio/out/` are untouched and still untracked.
>
> **Citations repointed: 237 occurrences of 93 distinct commits across 34 files**
> — fewer than last round's 272 only because 402 commits kept their SHAs. That
> includes the live code constant **`CANON_BASE_COMMIT`**, now `6970fdc~1`, and
> the same SHA quoted in `tools/publication/README.md` and in the header comment
> of `alias_canon.txt`; miss any one of those and `--verify-canon` stops being
> able to re-derive the alias map. It also includes the cross-repository
> citations of `vast-render` commits — that repository was rewritten in the same
> round, and both maps have to be in hand before either repository's citations
> can be repointed, because `.gitignore` and `docs/DEFECT-LOG-R2.md` cite it.
> Verified against the pre-rewrite object database restored from the new bundle:
> all 656 map pairs agree on author, committer, both dates and subject.
>
> **A trap worth writing down.** `.git/filter-repo/commit-map` in an
> already-filtered repository is keyed by the **original** pre-first-rewrite
> SHAs, not by the ones the documents currently cite; using it directly repoints
> almost nothing and rewrites prose *about* the first rewrite. The usable map is
> the one from filtering a **fresh clone**. Separately, `filter-repo` repoints
> abbreviated SHAs inside **commit messages** on its own — 27 messages here — so
> the citation pass only has to handle tracked files.
>
> **Gate after: `sanitise_docs.py --verify-canon` → PASS on 82 entries, exit 0.**
> A full-object-database scan of every blob, every commit message and the note,
> testing every dotted quad with `ipaddress.is_global`, reports **zero** routable
> third-party addresses. `5.2.0.1` still appears and is still the Blender version
> in a comment, not an address.


### Option A — publish as-is, with full history

Ships: 638 commits of genuine engineering history, all SHAs stable, all 220
in-doc SHA citations still resolving.

Still exposed:
- Two personal Gmail addresses in 601 of 638 commit author/committer fields,
  permanently, in a form GitHub displays on every commit page.
- Three real vast.ai host IPs, in the current `sanitise_docs.py` **and** in
  historical versions of two docs.
- **The home directory and the workstation's hostname, in HISTORY.** The
  working tree is now clean — 0 tracked files, down from 322 — but the
  sanitisation is a commit, not a rewrite, so every blob before it still holds
  all 1,200 occurrences and all 46 hostname stamps. `git log -p` and every
  GitHub "view file at commit" page still shows them. **This is the one class
  where cleaning the tree does not clean the option**, and it is easy to read
  the 322 → 0 result as if it did.
- **No credentials.** The key is not here in any form.

### Option B — `git filter-repo` rewrite (mailmap + IP replacement)

Ships: all 638 commits with rewritten identities and scrubbed blobs.

Fixes: the Gmail addresses in every commit; the historical IP occurrences; and
the historical home-directory and hostname occurrences **if** a blob-content
replacement is included. `git filter-repo --replace-text` takes a file of
`literal:…==>…` lines; the two that matter are the home directory and the
hostname, and both are one line each. Without that flag a rewrite fixes the
identities and leaves 1,200 paths in the history untouched.

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

Still exposed after C: the three IPs in `sanitise_docs.py` and the alias map
beside it, since they are in the current tree — Option C does not fix a
present-tense leak. Fix §4 first regardless of which option is chosen.

What C now DOES fix for free, which it did not when this section was written:
the home directory and the hostname are gone from the tree, so a fresh init
from `HEAD` carries neither. That is the one respect in which the code
sanitisation changes the balance between the options — it makes C and a
`--replace-text` B equivalent on this class, and leaves A the only option that
still ships all 1,200 occurrences.

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
