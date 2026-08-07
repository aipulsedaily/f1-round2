# WHICH PATH FILE IS THE LIVE CAMERA

**`render/film17_path.json`**

sha256 `676798074601107f2260905b67ded44e28a646535658b3612e016c730b85a15b`

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
