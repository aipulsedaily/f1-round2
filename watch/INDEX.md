# What is in this folder, and which of it is a claim about the film as it stands

**Everything in `watch/` is a claim about the current film whether it was meant
as one or not.** This project has now twice had a client judgement formed
against an artefact that was out of date — the audio clips that were 2.5 hours
behind their master, and `PART2_opening_53s.mp4`, which is a camera that had
already been replaced when it was watched. Both were labelled correct *at the
moment they were cut* and neither was labelled at all afterwards.

So this file exists to say, per artefact, **what it shows and whether it is
still true.** It is written by dates that can be checked, not by memory.

---

## CURRENT — safe to judge the film by

| file | cut | shows |
|---|---|---|
| `AFTER_opening_18s.mp4` | 08-08 01:36 | the opening tempo pass (R2-1606). The most recent camera deliverable. |
| `BEFORE_opening_18s.mp4` | 08-07 17:52 | its matched BEFORE. Correctly named. |
| `audio/` | 08-08 03:14 | re-cut from the master; `audio/INDEX.md` explains the earlier staleness and states it is fixed. |

## SUPERSEDED — do not judge the current film by these

| file | cut | why it is not current |
|---|---|---|
| **`PART2_opening_53s.mp4`** | **08-07 03:10** | **Pre-R2-831 camera.** The beat-1 re-frame/re-pace landed at 08-07 04:11, an hour *after* this was cut. The camera in this file no longer exists. This is the file the client may have formed their pacing judgement from. |
| **`PART2_closing_17s.mp4`** | **08-07 03:11** | Same batch, and additionally pre-dates the R2-943 lap-down (08-07 14:12) which put a moving car in the closing frames. The ending in this file is the *smudge* ending. |
| `seq1/`, `seq2/` | 08-07 03:10 | frame sequences from the same superseded batch. |
| `AFTER_beat1_33s.mp4` | 08-07 16:02 | a valid AFTER for the beat-1 **re-frame**, but it predates the opening tempo pass. Superseded by `AFTER_opening_18s.mp4` for any question about pacing. |
| `BEFORE_beat1_33s.mp4` | 08-07 03:15 | its matched BEFORE, same batch as the superseded PART2 pair. |

## A/B PAIRS — each is a claim only about its own question

| file | cut | question it answers |
|---|---|---|
| `R2851_ending_CANDIDATE.mp4` / `R2851_ending_SHIPPED_A.mp4` | 08-07 07:25 | an ending A/B. Both arms predate the lap-down. |
| `R2943_ending_LAPDOWN.mp4` | 08-07 14:12 | the lap-down ending. Beat 6 is under active work; check with its owner before treating this as final. |

## LINKS

`r2943_4k`, `r2943b6_frames` are symlinks into `~/vast-render/out/seq/`. They
follow whatever is at the other end and are **not** snapshots.

---

### The rule this folder now runs on

If you cut something in here, put a row in this table in the same action. An
artefact whose provenance lives only in a chat transcript is an artefact that
will be mistaken for current the next time somebody opens the folder — which is
exactly what happened twice.
