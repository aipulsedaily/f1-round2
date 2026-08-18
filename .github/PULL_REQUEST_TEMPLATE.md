<!--
Read CONTRIBUTING.md first if you have not. The one rule there is that a change
which fixes something must say HOW the fix was measured — the number before, the
number after, and what produced them.

Delete any section that genuinely does not apply, and say why rather than
deleting it silently.
-->

## What this changes, in one line

<!-- State the finding or the effect, not the filename. -->

## What was measured

<!--
Before / after, with the command that produced them. Paste the
`>> STAGE RESULT:` line if a gate emitted one.

    before:  <number>   <command>
    after:   <number>   <same command>
-->

## Could that measurement have failed?

<!--
Name an input that would have made your check say the opposite. If you cannot,
say so — an honest "I could not construct one" is a real answer and is more
useful than an implied guarantee.

If this PR adds or changes a gate: does it ship a positive control, something
the gate MUST reject? A gate that has never failed has not been shown to work.
-->

## Did you open the artefact?

<!--
For anything visual or audible: which frame did you open, or what did you listen
to? "A metric quoted without opening the frame is a claim, not evidence"
(R2-430). N/A is fine where nothing is rendered.
-->

## Log entry

<!--
New defects and fixes get an entry appended to a docs/STAGING-R2-*.md file, with
the next free number from docs/DUPLICATE-ID-SWEEP-R2.md. Put the id here.
-->

- Entry: `R2-____`
- Staging file: `docs/STAGING-R2-____-to-R2-____.md`

## Checklist

- [ ] No secrets, tokens, API keys or account balances anywhere in the diff
- [ ] No home directories, hostnames, personal email addresses or private site names — paths use `os.path.expanduser("~/f1-round2/…")` / `$HOME/f1-round2/…`
- [ ] No downloaded, purchased, sampled or AI-generated assets — everything is built by code in this repository
- [ ] `git add` was path-scoped; no `git add -A`
- [ ] Commit subject states the finding, not the file
- [ ] `python3 tools/docs_relink.py` exits 0 (documentation changes)
- [ ] No history rewrite — the docs cite 83 commit SHAs in 218 places
