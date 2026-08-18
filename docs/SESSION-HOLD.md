# SAFE TO RELOAD — state at the hold, 2026-08-07

All subagents stopped cleanly. Nothing was torn down. **Reloading the session
loses nothing**: the filesystem, the farm and the encoder are all independent of
it.

## Still running WITHOUT a session, deliberately

| what | where | why it was left up |
|---|---|---|
| **Beat-1 encoder** | PID 1083726, `nohup setsid work/r2840/encode_when_ready.sh` | 48 h window, detached. Fires on 792/792, runs `rq seq verify` + an independent missing-frame-number check, aborts rather than encode short. Output -> `watch/AFTER_beat1_33s.mp4` |
| **Beat-1 render** | broker 2 (8761), `film17_breach.blend` | **624 of 792 frames done.** Killing it wastes ~$2.6 already spent and it answers two of the client's three beat-1 notes |
| **Broker 1** (8760) | instance id-040, $0.4627/hr | **IDLE, depth 0.** `HIBERNATE_SEC` is 3600, so it self-destroys within the hour. No action needed |
| **Broker 2** (8761) | instance id-037, $0.4403/hr | depth 6, 3 running |

**Credit $[redacted].** Spend continues while the beat-1 render finishes — roughly
$1.50 more. To stop all spend: `./rq teardown` on both brokers, and accept
losing 624 frames.

## DO NOT CLOBBER — 12 modified files from stopped agents

These are mid-edit and **uncommitted on purpose**. They are safe on disk; they
are not safe from `git checkout` or `git add -A`.

```
sim/apply_breach.py                     world/build_barriers.py
tools/r2731_camera_clearance.py         world/build_items.py
world/items/PLACEMENT.json              world/items/driver_figure.py
world/items/showroom_ceiling.py         world/camera_rig_continuity.json
world/camera_rig_path.json              + 3 staging docs
```

`world/build_architecture.py` carries another agent's uncommitted paving-relief
work. **`git add` path-scoped only, never `-A`** — a blanket add has swept other
agents' work into the wrong commit twice.

## Read these first, in this order

1. **`docs/NEXT-REBUILD.md`** — the single manifest. 14 source changes that must
   land in ONE build, 6 ordering constraints that fail silently if violated, the
   verification bar, and the corrected master costing **with a warning not to
   quote it**.
2. **`docs/RESUME-HERE.md`** — open threads. Two landmines removed today.
3. **`docs/DEFECT-LOG-R2.md`** — 685 entries.

## ~~THREE~~ TWO BLOCKERS before any master

1. **The beat sheet reintroduces a beat-1 camera failure** (R2-1084).
   `CAMERA_RIG_FAIL 1_assembly: 1.155 of the half-frame at f431`. Fixed at
   04:15, reintroduced by a sheet edit at 05:03. It is printed as the *first* of
   two STAGE RESULT lines and the second is a pass — **anything reading the last
   line sees a clean run.**
2. ~~**`slabcheck` exits 1** (R2-1049).~~ **CLOSED — R2-1121. It exits 0.**
   Bays 3 and 6 STAY; judged at 4K/1:1, not at 720p. **No geometry and no bake
   changed**, and `BF_MUL05_S02 = 0.1449 m` still holds. The "re-label is free"
   option was **false, and was measured**: `role` picks `n_radial` (15 vs 7),
   so relabelling re-fractures bay 3 202→198 shards and bay 6 200→178 and costs
   the same re-bake as making them leave. The fix separates the
   fracture-density input from the plan's outcome claim. Selftest 16 → 22
   controls, all green. See `docs/STAGING-R2-1121-to-R2-1150.md`, and R2-1122
   in it for the same defect one level up (mullions 4 and 6, not fixed).
3. **Budget.** Master is 155.0 h; it fits $[redacted] credit *by fifteen cents* and only
   on a cheaper card. **The client's ask is ~$25.** Supply survey found 1x and 8x
   are the only deep markets and the 1x->8x price gap (8.8 %) is *smaller than
   host-to-host speed variance* (9.0 %) — so width buys wall-clock, not money.

## The one thing no agent can do

**Nobody has listened to this film.** The audio has been judged by spectrogram
only. `np.roll` put **+31.3 dB on frame 1 of every master ever produced** and
every gate passed it (R2-1088/R2-1090). `audio/out/ab/ending_A_nolapdown.wav`
and `ending_B_lapdown.wav` are cut so a person can decide.

## Next session

`CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION=1000` is now in `~/.claude/settings.json`
(this session was capped at 200 and spent them). The work that wants that
parallelism is **#52, the item campaign** — ~407 objects, genuinely fan-out
shaped, and the largest remaining quality gap against the client's
"materials must have depth" bar.
