"""Build the POSITIVE CONTROL camera: the rig with its orientation frozen.

    python3 tools/make_control_path.py --out /tmp/frozen_path.json

WHY
---
"Test every new gate against an artefact already known to be bad and confirm it
fails" is the only technique that has reliably worked on this project (MASTER-PLAN
sec 6).  `screen_presence.py` is a new instrument, so it needs one.

The artefact known to be bad is the pre-#34 camera rig, documented in
PLAN-scope-optimisation sec 1 and measured there: 24 keys for 2,978 frames, no
rotation key anywhere after frame 754, so the orientation is FROZEN for the
launch, the breach, the transit, the whole flying lap and the ending -- 65.8 %
of the film.  That rig no longer exists on disk.

This reconstructs its defining defect exactly and nothing else: the CURRENT
positions and lens, with the quaternion held at its frame-754 value from frame
755 to the end.  Position is left alone deliberately, so the only difference
between control and subject is the one thing the measurement is supposed to be
sensitive to -- where the camera is POINTED.

If `screen_presence.py` does not report a large loss of coverage against this
path, the instrument is measuring something other than what it claims to.
"""
import json, argparse, os

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ap = argparse.ArgumentParser()
ap.add_argument("--path", default=os.path.join(R2, "world/camera_rig_path.json"))
ap.add_argument("--freeze-after", type=int, default=754)
ap.add_argument("--out", required=True)
a = ap.parse_args()

d = json.load(open(a.path))
path = d["path"]
frozen_q = None
for p in path:
    if p["f"] == a.freeze_after:
        frozen_q = list(p["q"])
        frozen_lens = p["lens"]
        break
if frozen_q is None:
    raise SystemExit(f"frame {a.freeze_after} not in path")

for p in path:
    if p["f"] > a.freeze_after:
        p["q"] = frozen_q
        p["lens"] = frozen_lens

json.dump({"frames": d["frames"], "path": path,
           "CONTROL": f"orientation and lens frozen at frame {a.freeze_after}; "
                      f"positions unchanged. Reconstructs the pre-#34 defect."},
          open(a.out, "w"))
print(f"wrote {a.out}: quaternion frozen at {frozen_q}, lens {frozen_lens} mm, "
      f"from frame {a.freeze_after + 1} to {d['frames']} "
      f"({100.0 * (d['frames'] - a.freeze_after) / d['frames']:.1f} % of the film)")
