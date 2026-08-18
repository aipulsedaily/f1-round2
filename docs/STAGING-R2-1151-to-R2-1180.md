# STAGING — R2-1151 to R2-1180 · R2-1084 re-opened: the sheet did not regress

> ## MERGED, THEN RENUMBERED — THESE ENTRIES ARE NOW R2-4201 … R2-4207
>
> **2026-08-14, #170.** The range check below was honest and still wrong: the
> main thread was writing R2-1151…R2-1157 into the log at the same time, from a
> different session, and neither side could see the other. Both landed, and for
> a week each of those seven numbers named two entirely different entries.
>
> **Resolved by moving the seven in THIS file**, because every citation from
> outside the log — `tools/r2_1881_ab.sh`, `tools/r2_1881_bake_cams.py`,
> `tools/r2_1898_split_arms.py`, `world/build_nearband.py`,
> `tools/r2_1821_ground_detail.py`, `render/world/assembly/r2/SHIPPING.md` —
> means the main thread's entries, and nothing outside cites these.
>
> **Add 3050 to read the log: R2-1151→R2-4201 … R2-1157→R2-4207.** (They were briefly R2-4151…R2-4157, from 2026-08-14 to 2026-08-15; that range collided a second time, with the audio rebuild, and these seven moved again. A citation of R2-4151/R2-4152 written after 2026-08-14 means the AUDIO entry, not one of these.) The headings
> below are left at their staged numbers as the historical record of what was
> staged under what. **Do not cite R2-1151…R2-1157 from this file.** Full
> account: `docs/DUPLICATE-ID-SWEEP-R2.md`.

Range check before writing: `R2-1151…R2-1180` is unused anywhere in `docs/`.
`docs/STAGING-R2-1181-to-R2-1210.md` holds R2-1181…R2-1187 and is another
agent's. No collision.

**Do not merge into `docs/DEFECT-LOG-R2.md` from here — the main thread owns it.**

---

## R2-1151 — R2-1084's timeline is wrong. `docs/beat_sheet.json` was not edited at 05:03.

The report says the sheet "was edited at 05:03" and thereby "reintroduced" a
beat-1 failure that a 04:15 farm run had shown fixed. **Reproduced first, as
required, before touching anything** — unmodified `anim/build_camera_rig.py`
(confirmed clean against HEAD, `git diff --stat HEAD` empty) on the sheet as it
stood:

    >> per-beat verdict:
         1_assembly    FAIL   subject reaches 1.155 of the half-frame at frame 431 (margin 0.92)
         2_launch      PASS
         3_breach      PASS
         4_transit     PASS
         5_lap         PASS
         6_ending      PASS
    >> STAGE RESULT: CAMERA_RIG_FAIL
    blender exit=0

`work/r21084/repro_shipped.log`. **All three numbers match character-for-character
— 1.155, f431, margin 0.92.** The failure is real and it is on the shipped sheet.

**The 05:03 file is not the sheet.** mtimes:

| file | mtime |
|---|---|
| `docs/beat_sheet.json` | **03:48:42** |
| `tools/build_beatsheet.py` | 04:46:56 |
| **`anim/build_camera_rig.py`** | **05:03:06** |

The thing edited at 05:03 was **the rig builder**, committed at 05:06 as
`0d3ae18` — *"beat 6: R2-859..R2-861 — aim keying, the post levers, and a moved
sheet"*. Its only code change is beat 6's aim-keying stride, made sheet-driven
with the historical constants as defaults and stated bit-identical by default.
It cannot touch beat 1.

**The sheet has not been written since 03:48 — which is BEFORE the 04:15 PASS,
not after it.** Nothing was reintroduced at 05:03, because nothing was written
at 05:03. R2-861 in `docs/STAGING-R2-851-to-R2-880.md` already recorded the
03:48 move and already proved the FAIL pre-existing with the original code; that
entry's finding was carried into the R2-1084 write-up with its causality
inverted.

### The trail R2-1084 recommends does not exist

> `git log -p -- docs/beat_sheet.json` … is the trail.

It returns nothing. **`docs/beat_sheet.json` is gitignored** —
`.gitignore:37`. The sheet the entire film is built from is untracked, so a
03:48 rewrite of it left no audit record at all, and the timeline in R2-1084 had
to be reconstructed from mtimes and build logs. **See R2-1157.**

---

## R2-1152 — ROOT CAUSE: the fix was generated into a candidate and never promoted.

The failing sheet has **19** camera keys in beat 1. Every PASS in the 04:05–04:49
window has **20**. Diffed whole-tree, `docs/beat_sheet.json` against
`docs/R2829_beat_sheet_CANDIDATE.json` — **five differences, all in beat 1, and
four of them derived:**

    LEN  /beat1/camera_keys                        19 -> 20
    LEN  /beat1/flight                             18 -> 19
    DIFF /beat1/path_length_m                      63.048 -> 69.839
    DIFF /beat1/mean_camera_speed_ms               1.911  -> 2.116
    DIFF /beat1/max_estimated_pan_widths_per_frame 0.0747 -> 0.1072

Beats 2–6, the seam block, `time_map`, `aim`, `beat6.aim_keying`, `total_s` and
`total_frames` are **identical**. The one real difference is a single key:

    {"t": 17.375, "world": [-3.7873, 2.2103, 3.004], "look_at": [-3.3182, 0.0, 1.1353],
     "lens_mm": 36.5, "focus_target": "CORNER_GROUP_APPROACH", "fstop": 2.8,
     "focus_distance_m": 2.932,
     "note": "R2-837 approach: the lens reaches its wide end BEFORE the turn into the
              corner group needs it. Without it the rig ramps 58->35 mm linearly over
              65 frames and 14 frames (f420-433) carry a subject outside a frame a
              37 mm lens would have held."}

**The key's own note describes f431.** This is R2-837, part of the client-driven
beat-1 re-frame/re-pace, and it is the fix.

### Why it never reached the shipped sheet

`tools/build_beatsheet.py:2302`:

    dest = os.environ.get("B1_SHEET_OUT", os.path.join(DOCS, "beat_sheet.json"))

`B1_SHEET_OUT` exists so "a candidate sheet must be measurable end to end before
`docs/` is touched" — correct design. R2-837's key was added to the generator at
04:46 and emitted **with the override in force**, into
`docs/R2829_beat_sheet_CANDIDATE.json`. The promotion run — the same generator
with no override — **was never made.** `docs/beat_sheet.json` has sat at its
03:48 content ever since, stale against its own generator by one key.

**So nothing was reintroduced. The shipped sheet never carried the fix.** The
04:15-window PASS was not an anomaly and not wrong; it was a true statement
about a file that is not the one the pipeline reads. R2-1084's framing —
"reintroduced a failure that had been fixed" — is refuted. The correct framing is
**an unpromoted fix**, which is a different defect with a different remedy.

Proof the generator is the authority and the sheet was merely stale: regenerated
to a scratch path, then diffed.

    B1_SHEET_OUT=work/r21084/regen.json .venv/bin/python tools/build_beatsheet.py
    >> STAGE RESULT: BEATSHEET_OK

    regen vs docs/R2829_beat_sheet_CANDIDATE.json   ->  0 differences
    regen vs docs/beat_sheet.json (shipped)         ->  the 5 above

---

## R2-1153 — FIXED by promotion, and the pixels re-measured rather than assumed.

    cp docs/beat_sheet.json work/r21084/beat_sheet.BEFORE_R21084.json
    .venv/bin/python tools/build_beatsheet.py          # no override
    >> STAGE RESULT: BEATSHEET_OK

No hand-editing of JSON: the sheet is regenerated from the generator that already
held R2-837's key, so the client's re-pace and re-frame notes are carried by
construction rather than by my re-typing them.

**All six beats PASS** (`work/r21084/verify_fixed.log`):

    1_assembly PASS   2_launch PASS   3_breach PASS
    4_transit  PASS   5_lap    PASS   6_ending PASS
    >> STAGE RESULT: CAMERA_RIG_CONTINUOUS_AND_AIMED

Beat 1's own numbers move from failing to comfortable — **frame-offset
1.155 → 0.480** against the 1.0 bound, aim 14.12° → 7.74°, and the worst frame
moves f431 → f166.

### The runtime is untouched

**2,978 frames, `total_s` unchanged, 124.1 s reported by the rig.** The added key
sits at t=17.375 s, inside beat 1's existing 0–33 s span; no beat duration, start
or boundary moves. Nothing here wants to move the runtime.

### The boundaries, measured in pixels as instructed — not assumed

Per-frame camera paths of the old and new builds compared directly, all 2,978
frames:

| range | worst Δposition | worst Δquaternion | worst Δlens |
|---|---:|---:|---:|
| beat 1  f1–792 | 14.710 m | 1.7e+00 | 17.326 mm |
| beat 2  f793–1056 | **0.000000000 m** | 1e-06 | 0.000 |
| beat 3  f1057–1400 | **0.000000000 m** | 1e-06 | 0.000 |
| beat 4  f1401–2000 | **0.000000000 m** | 2e-06 | 0.000 |
| beat 5  f2001–2714 | **0.000000000 m** | 1e-06 | 0.000 |
| beat 6  f2715–2978 | **0.000000000 m** | 1e-06 | 0.000 |

* **The f792/793 seam is untouched.** Δposition at f792 and f793 is
  `0.000000000 m` exactly, quaternion ≤1e-6 (~0.0001°, ~0.006 px at 4K). **The
  1.33 % seam measurement is not at risk** — the change stops at f754 and the
  bridge block f755–792 is bit-identical.
* **The closing is untouched.** f2715–2978 is `0.000000000 m` throughout;
  f2977 and f2978 both 1e-6 on quaternion. The closing aim gate is unaffected;
  the rig reports `6_ending worst 0.04° at f2722` against its 32° bound, and
  beat 6's geometry is bit-identical to the build the 0.11°/f2977 figure was
  taken on.
* The beat-1 changes are the intended re-route: `path_length_m` 63.0 → 69.8 m.

### The quaternion warning, checked

The 1.7e+00 component delta at f417 is a **sign-representation artifact, not a
reversal**: `q` and `−q` are the same rotation. True angular difference between
the two builds there is **33.2°**, which is the re-aim into the corner group that
R2-837's key exists to make. Within the fixed build, rotation is continuous —
worst frame-to-frame step **3.73° in beat 1** and **12.96° at f2633** across the
whole film, against the rig's 45° limit. **No backwards run, no 2π wrap.** The
rig's own `worst position jump` and `worst rotation step` lines are identical
before and after.

---

## R2-1154 — THE DEFECT BEHIND THE DEFECT, and it is two defects.

> A build that prints two verdicts and is judged on one is a build with an
> unread verdict.

Correct, and the mechanism is now identified exactly.

**(a) The rig printed FAIL and exited 0.** `main()` ended with a bare `print` and
fell off the end. Measured above: `blender ... -P build_camera_rig.py` returned
**0** with `CAMERA_RIG_FAIL` in the log.

**(b) The failure could not propagate, because the caller is in-process.**
`tools/build_verify_scene.py:372` loads **this very file** by importlib, sets
`sys.argv`, `exec_module`s it and calls `mod.main()`. `main()` *returned normally
after printing the failure*, so the re-key stage carried on, finished its own
job, and printed its own passing verdict underneath. **That is precisely the
two-verdict log R2-1084 describes**, and it is why the rig's verdict was only
ever seen "on its way past".

### The fix

`anim/build_camera_rig.py` now adopts `tools/gate_exit.py`, the module this
project already wrote for this exact family:

    rc = gate_exit.verdict("CAMERA_RIG_FAIL" if fails
                           else "CAMERA_RIG_CONTINUOUS_AND_AIMED")
    if rc != gate_exit.PASS:
        sys.exit(rc)
    return rc

    if __name__ == "__main__":
        gate_exit.guard(main, tool="build_camera_rig")

**On PASS it returns rather than exiting, deliberately.** A `SystemExit(0)` here
would unwind the *caller* too, and `build_verify_scene.py` has work after
`mod.main()` — the grade assertion that deletes a mis-graded blend. Success must
not abort the chain; failure must.

The rig could not adopt `gate_exit` before now because **its own verdict tokens
had no code**: `CAMERA_RIG_CONTINUOUS_AND_AIMED` and `FILM_SCENE_REKEYED_*` both
mapped to **CRASH(2)**, the module's deliberate "unrecognised is not a pass"
default. Both are now registered, spelled in full so a future
`CAMERA_RIG_AIM_FAIL` cannot be swallowed by a loose prefix.

### `gate_exit.scan()` — the last line is not the only line read

New in `tools/gate_exit.py`. Collects **every** `>> STAGE RESULT:` line and
reduces them by severity (CRASH > FAIL > VACUOUS > PASS — *not* numeric order,
since VACUOUS is 3 and CRASH is 2). **A log with no verdict at all is CRASH, not
PASS**, because Blender exits 0 on an uncaught exception and silence is the shape
a crash actually has here. Usable as a CLI on any log:

    python tools/gate_exit.py build.log      # $? is the real status

This closes a hole in the control itself: `gate_exit_selftest.py:251` read
`said[-1]`, so the file that exists to catch "prints FAIL, exits 0" was itself
judging on the last line.

### PROVED IT FIRES — on this exact sheet, with a negative control

This project has repeatedly found guards that could not fire, so both directions
are recorded.

**1. The rig, on the exact failing sheet** (`work/r21084/guard_broken.log`):

    blender ... --sheet work/r21084/beat_sheet.BEFORE_R21084.json
    >> STAGE RESULT: CAMERA_RIG_FAIL
    BLENDER EXIT = 1          <-- was 0 before the fix

**2. The rig, on the fixed sheet** — must not fire:

    >> STAGE RESULT: CAMERA_RIG_CONTINUOUS_AND_AIMED
    BLENDER EXIT = 0

**3. Propagation through the chaining stage.**
`work/r21084/chain_control.py` reproduces `build_verify_scene.py`'s exact call
shape — importlib load, `exec_module`, `mod.main()` in-process, then the caller
prints its own verdict — without needing an 8 GB film blend.

| sheet | verdicts printed | exit |
|---|---|---|
| **failing** | `CAMERA_RIG_FAIL` only — **the caller's verdict is never reached** | **1** |
| fixed | `CAMERA_RIG_CONTINUOUS_AND_AIMED` then `FILM_SCENE_REKEYED_CHAINCTL` | 0 |

The two-verdict log can no longer be produced from a failing rig, and the
success path still completes both stages.

**4. The scanner, on a real two-verdict log** built from the genuine failing rig
output plus a genuine passing re-key tail:

    >> gate_exit.scan two_verdict.log: 2 verdict(s)
       << 1/2  CAMERA_RIG_FAIL                    FAIL
          2/2  FILM_SCENE_REKEYED_R2851           PASS
    >> STATUS FAIL — 1 non-pass verdict(s): CAMERA_RIG_FAIL
       THE LAST LINE IS A PASS (FILM_SCENE_REKEYED_R2851) AND THE BUILD IS NOT.
    SCANNER EXIT = 1

The **old last-line reader on the same text returns PASS** — the fault is
reproduced in the control, so the control is not vacuous. On the clean build log
the scanner exits 0.

**5. Eleven controls added to `tools/gate_exit_selftest.py` §7**, including the
fault-reproduction case ("the last-line reader calls the two-verdict log a
PASS"), the severity reductions, the no-verdict case and the CLI.
**`>> STAGE RESULT: GATE_EXIT_SELFTEST_OK` — all 62 controls behaved**
(51 pre-existing, unchanged, plus 11).

---

## R2-1155 — the beat-1 PASS before 03:48 was a SATURATED metric, and it measured all 791 frames while doing it.

Two logs in the window (`work/r2851/build.log` 03:33,
`work/r2851/rekey_R2851.log` 04:28) show a beat 1 of **35** rig keys — the
pre-03:48, 23-camera-key sheet — reporting:

    1_assembly    worst 0.00 deg at frame 0  (bound 30.0)   frame-offset 0.000
    1_assembly    PASS

Reproduced on a 23-key sheet (`work/r21084/repro_23key.log`): identical.
**`n` = 791 — every frame was measured**, so this is not "not measured". The
value is saturated. Beat 1's metric is a **minimum over 15 clusters of the angle
to the cluster's edge, clamped at zero** (`nearest_field`,
`a = max(0.0, a - asin(rad/n))`). On the old slower, closer weave *some* cluster
covered the lens axis on all 791 frames, so the metric sat on its clamp and
**could not report anything else** — the R2-316 family.

The consequence matters for how R2-1084 is read:

* Old sheet → metric pinned at 0.000, PASS carries no information.
* 03:48 re-pace (63.0 m path, 1.91 m/s) → metric becomes live and immediately
  reports a **real** off-frame subject at f431.
* +R2-837's key → **0.480, measured and non-degenerate.**

**So the f431 FAIL was never a regression of a good state — it was the first
time the gate could see beat 1 at all.** The 03:48 sheet did not break beat 1;
it made beat 1 legible to its own gate. Not fixed here (the clamp is defensible
for "is the lens on the field") but it should not be quoted as a pass without
the saturation caveat. **Flagged, not changed.**

---

## R2-1156 — two things I did not touch, and why

* **`world/camera_rig_path.json` is stale against both builds**, and was already
  so before this fix: worst Δposition **11.31 m** against the pre-fix build and
  **9.87 m** against the fixed one. It is behind the sheet by more than this
  change moves anything. 43 readers and a proxy render in flight; **not
  regenerated here** — it needs its own owner and its own gate.
* **`tools/build_beatsheet.py`'s docstring claims it writes
  `docs/beat_sheet.{json,md}`. It does not write the `.md`** — no such write
  exists in the file, and `docs/beat_sheet.md` has been unchanged since
  **2026-07-28**, i.e. stale across every sheet change since. Phantom claim in a
  docstring; the `.md` is 10 days behind the film. Flagged only.

---

## R2-1157 — the sheet the film is built from is untracked, and that is why none of this had a trail

`.gitignore:37` excludes `docs/beat_sheet.json`. Consequences, all observed here:

* `git log -p -- docs/beat_sheet.json` returns nothing, so the 03:48 rewrite has
  no author, no diff and no message. R2-1084's timeline had to be rebuilt from
  mtimes and logs, and it came out inverted.
* **The fix in R2-1153 cannot be committed.** It exists on disk only. A
  `git checkout` or a clean clone does not carry it, and the next agent to
  regenerate with `B1_SHEET_OUT` unset is the only thing that reproduces it.
* Candidates *are* tracked (`docs/R2829_beat_sheet_CANDIDATE.json`,
  `docs/R2851_beat_sheet_CANDIDATE.json` are both in git). **The candidates are
  versioned and the shipped artefact is not**, which is exactly backwards and is
  the structural reason a fix could sit in a candidate for ten hours without
  anyone seeing that `docs/` had not moved.

**Recommended, NOT done** — un-ignoring a 156 KB file that 40+ tools read, while
other agents are mid-flight, is not a change to make unilaterally. Raising it for
whoever owns `.gitignore`.

---

## Cost

**$0.** Everything above ran locally on CPU: seven rig builds and two generator
runs against `world/beat1_anim.blend` (291 MB, no film blend needed), plus the
`gate_exit` selftest. **No broker time, nothing queued, nothing rendered.** The
beat-1 proxy render on broker 2 was not touched, not inspected and not jumped.

## Files

| path | what |
|---|---|
| `docs/beat_sheet.json` | **FIXED** (regenerated; untracked — see R2-1157) |
| `anim/build_camera_rig.py` | FAIL now exits non-zero and propagates |
| `tools/gate_exit.py` | `scan()`, `scan_report()`, CLI, rig tokens registered |
| `tools/gate_exit_selftest.py` | §7, 11 new controls, 62 total |
| `work/r21084/beat_sheet.BEFORE_R21084.json` | the failing sheet, kept as the control input |
| `work/r21084/chain_control.py` | the in-process chain positive control |
| `work/r21084/*.log` | every run quoted above |
