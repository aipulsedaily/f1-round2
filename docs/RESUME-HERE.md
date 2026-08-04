# RESUME HERE — state at the weekly usage limit, 2026-08-04 ~20:30

Two agents were terminated mid-task by a hard weekly usage limit
(resets **Aug 9, 5pm UTC**). This file is what someone needs to pick it up.

## The renders are UNAFFECTED and still running

They are GPU jobs on rented vast.ai boxes, not Claude work. They will
complete on their own and write frames to disk. **Nothing needs to be done
to keep them alive**, and nobody is watching them.

```
r2beat1   broker 1 (8760)   792 frames  f1-792      11.50 h   $6.17
r2full    broker 2 (8761)  1247 frames  f793-2978   14.57 h   $6.97
                                 in parallel, ~14.6 h, $13.14 total
```

Frames land in `~/vast-render/out/seq/r2beat1/` and `out2/seq/r2full/`.
Check with `cd ~/vast-render && ./rq status` and
`VASTRENDER_URL=http://127.0.0.1:8761 ./rq status`.

**Two rented cards are billing at ~$1.01/hr combined.** If the passes finish
and nothing else is queued, `rq teardown` on BOTH brokers stops the meter —
teardown is per-broker and will report success while the other still bills.

## The ship candidate

`render/film16_breach.blend` — beat-1 camera at -10.00 deg, driver in the
cockpit, 1,707 placed items, breach applied and confirmed three ways,
sign fixed, levelling identity closing to 0.007 W.

## Landed in SOURCE but NOT in any film — the next rebuild must carry all three

1. `world/car_paint.py` v5 + `imperfections.py` on both car sources.
   Albedo 0.0121 -> 0.0372. The largest visual change on the film.
2. `world/showroom_ceiling.blend` — 6.99 MB library. The three-line append
   is already in `tools/build_film_scene.py`.
3. Beat-5 lens retune candidate:
   `render/film14_path_R2581B_ramp_RETUNED_CANDIDATE.json` — deliberately
   NOT folded into `beat_sheet.json`.

## Work that was in flight when the limit hit

- **Rear-wing bake** — the tray hypothesis was REFUTED at 240 Hz (R2-707):
  the member never comes within 60 mm of the solid wing against a 40 mm
  margin. Its next step, never taken: find what the mullion IS touching.
  Both bake cells exist and are verified —
  `sim/out/breach_film_R2701A.npz` (aerofoil) and `_R2701S.npz` (solid),
  N=520, film f845-1051, one variable apart.
- ~~Items pixel proof (#121, #133)~~ **CLOSED.** `ITEMS_REACHED_A_FRAME` at
  f2978: SPECX_ 68,025 px, TS_ 11,821, CFP_ 10,263, CRF_ 6,232, negative
  control 0. `DRV_` reads 0 there and is a SEPARATE open question — the
  closing wide puts the car at ~1,000 m where a helmet is sub-pixel, so
  measure it at a frame where the driver is known to read (f800), not there.
- **Relief specimen (#52)** — a multi-material known-truth ladder at
  item-like pixel densities. The shipped ladder frames at 7,111 px/m against
  items at 170-2,333, so it cannot adjudicate the item failures. Wave 2 is
  deliberately unauthored until this settles.
- **Occlusion sweep (#132)** — the car is fully hidden behind a parapet at
  f2190, and `lap_shotscale.py` is blind to occlusion by declaration.
- **Breach un-bend A/B (#32)** — needs the manufactured control (A vs NULL,
  same content, different file) before its 15.09 % means anything.

## The defect log

`docs/DEFECT-LOG-R2.md`, **425 entries**. Agents stage into
`docs/STAGING-R2-*.md` and the main thread merges by identity, never by
position.

## Closed since this file was written

- **The f792/793 seam is CLEAN** (R2-442) — and the two frames came from
  different machines, so it cleared the beat seam and the batch seam at once.
- **The exposure ramp does not exist** (R2-438/439). All five pre-registered
  predictions scored; P4 failed and the bound was the author's, not the film's.
- **The breach reads on screen** (R2-710): intact f866, crazes f868, separates
  into independently-tilting facets f870-872 with the mullions standing,
  transits f899-903, clear f904. No held frames, no pops in f860-930.
- **The slab un-break is UNRESOLVABLE at rung 1** and must be judged on the sim
  trajectories or a higher rung. 483 mm is ~40 px on a 15 m wall at 720p,
  before fracture and motion blur, and by f870 there is no coherent sheet left
  to track.
- **Occlusion (R2-651..666)**: the car is wholly hidden behind the pit building
  for f1114-1116 at 10-11 m, and behind `BR_FenceMesh_L03` on **f2976-2978,
  the film's last three frames** — an object already logged at +7.105 m of
  lateral intrusion against a 7.39 m half-width. `PONT_S 2410 -> 2460` closes
  the beat-5 blackout. NOT tested: `DR_BridgeBanners`, because the raycast
  world omits dressing and items, and the banners will not follow `PONT_S`.
- **Seven orphaned Blender processes reaped**, ~35 GB, using
  `ppid == 1 AND /proc/PID/cwd reads "(deleted)"`. An exec-server restart
  leaks its children and nothing reaps them; the leak is invisible to the
  memory gate it then defeats. **Handed on, not fixed.**
