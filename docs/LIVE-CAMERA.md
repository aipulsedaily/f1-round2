# WHICH PATH FILE IS THE LIVE CAMERA

**`render/film24_path.json`**

sha256 `9d055d63da7249935cb3f6e5905beeed709c9cde8874d44e67c172e3300971a7`

Declared 2026-08-09 02:4x under R2-3742 by coordinator ruling, replacing
`render/film19_path.json` (`363e4e88b3…`). film24 carries beat 1's re-pace,
beat 5's re-pace and beat 6's closing lens.

**THIS IS THE THIRD RECURRENCE OF THE SAME DEFECT AND IT IS WORTH SAYING
PLAINLY.** film17 was declared while film18 was newest (R2-1701). Then
film19's bytes stayed declared while film21, film22 and film23 were built —
which was *accurate*, because all four are byte-identical — and then film24
was built at 2026-08-08 19:21 and did not re-declare. So between 19:21 on
08-08 and this line, `bash tools/retier.sh` would have re-tiered the entire
item campaign against film19. That is not hypothetical: `retier.sh` resolves
its camera through `live_campath.load()` and takes no camera argument by
design, precisely so that this file is the only answer.

The gap film19 → film24 is real if smaller than the orphan's: 1,374 frames
differ in position (max 0.264 m), 1,522 in lens (max 7.03 mm) and 1,724 by
more than 0.2 deg (max 12.05 deg).

**And a document that names the wrong camera is exactly how the item tiering
came to be swept against a path that never rendered a frame** — see
R2-3721/#159, where `docs/screen_presence*.json` was derived from
`render/film14_path.json`'s bytes under the filename
`world/camera_rig_path.json`, and 17 of 435 items sat on the wrong tier
because of it. This file is cheap to update and that is the whole point of it.

`audio/scene.py` reads this declaration for its listener (R2-1705), so a stale
line here is audible as well as visible.

This file is to the camera what `render/world/assembly/r2/SHIPPING.md` is to the
world: the ONE place the answer is written down. `tools/live_campath.py` parses
it and RAISES if it cannot. Nothing else may keep its own copy of the answer.

## Why it exists — R2-1007 and R2-1091

`world/camera_rig_path.json` was byte-identical to `render/film16_path.json` for
three days while `render/film17_path.json` was the film's camera. **43 tools read
the stale file; one read the live one.** Measured divergence, all of it inside
beat 1 (f2–f780):

| quantity | worst | p50 over the divergent span |
| --- | --- | --- |
| position | **9.866 m** at f545 | 2.83 m |
| focal length | **23.0 mm** at f223 (58 mm vs 35 mm) | 6.05 mm |
| orientation | **103.3 deg** at f527 | 13.7 deg |

From f781 onward the two files are bit-identical in position and lens; only
sub-0.2-deg quaternion rounding remains. The two curves converge to exactly zero
at **f754**, which is beat 1's last camera key — beat 2 onward was never
re-authored, so nothing outside beat 1 can be affected by this class of drift.

## Why a declaration and not a filename convention

`anim/build_camera_rig.py:1585` writes `os.path.splitext(--out)[0] + "_path.json"`.
The path file's name is a **side effect of an output argument**, not a published
artefact with an owner. `world/camera_rig_path.json` therefore exists only when
the rig is built standalone with `--out world/camera_rig.blend`, which last
happened in `render/world/assembly/r2/v125/build_film16.sh` on 2026-08-04 15:49.
The film build has since moved to `tools/build_film_scene.py`, which calls
`build_camera_rig.main()` with its own `--out render/filmNN.blend` (R2-840e), so
the canonical-looking file in `world/` is an orphan of a retired build script.
Nothing rewrote it because nothing was ever responsible for it.

A filename convention cannot fix that, because the convention is what broke.
A declaration can, because updating it is a decision someone makes.

## How to update this file

When the rig is rebuilt and a new film path supersedes this one, change BOTH the
bold filename and the sha256 above. `tools/live_campath.py` compares the hash on
every load and RAISES on a mismatch, so a rebuild that is not declared here fails
every reader loudly instead of being picked up silently. That is deliberate: the
failure mode this guards is a rebuild nobody announced.
