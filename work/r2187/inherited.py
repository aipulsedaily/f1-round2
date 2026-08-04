"""THE THREE INHERITED OPEN ITEMS, MEASURED ON A LIKE-FOR-LIKE SET.

    .venv/bin/python work/r2187/inherited.py

`sim/out/verify.json` reports 627 bodies below the floor and quotes them against
3,948 bodies.  `work/r2187/scene_slab.py` reports 575 against 3,796.  Those are
not the same denominator: the table carries 3,948 bodies of which 152 are
MUL*/TRN* FRAME bodies that the applied scene does not instance at all (R6 --
apply_breach writes their transforms and nothing binds a mesh to them).

Comparing 627 with 575 and calling the difference an improvement would be
comparing two different populations.  So this recomputes the table's numbers
restricted to the GS_* shards, which is exactly the set the scene contains, and
only then puts the two side by side.
"""
import json
import os
import sys

import numpy as np

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "sim"))
import resample as RS          # noqa: E402
import fracture as FR          # noqa: E402
import shardmesh as SM         # noqa: E402

SINK_M = 0.004

film = RS.read_film(os.path.join(R2, "sim/out/breach_film.npz"))
names = film["names"]
# the DECIMATED RECONSTRUCTION, which is what verify_breach measures and what
# the applied f-curves are -- not the raw bake
frames = np.arange(int(film["span"][0]), int(film["span"][1]) + 1)
L, _Q = film["expand"](frames)

is_gs = np.array([n.startswith("GS_b") for n in names])
is_frame = np.array([n.startswith(("MUL", "TRN")) for n in names])
print("table bodies %d = GS %d + MUL/TRN %d + other %d"
      % (len(names), int(is_gs.sum()), int(is_frame.sum()),
         len(names) - int(is_gs.sum()) - int(is_frame.sum())))

# per-body lowest mesh vertex relative to its origin, so "below the floor" means
# the same thing here as it does in the scene
plan = FR.load(os.path.join(R2, "sim/out/fracture_wall.npz"))
low = {}
for bay in sorted(plan["panes"]):
    if plan["roles"][bay] == "intact":
        continue
    for s in plan["panes"][bay]:
        nm = "GS_b%02d_%05d" % (bay, s["id"])
        V, _F = SM.prism(s["poly"], 14.95500, 14.96650, detail=1,
                         seed=1000 * bay + s["id"])
        low[nm] = float(np.asarray(V)[:, 2].min())
r = np.array([low.get(n, 0.0) for n in names])

out = {}
for tag, sel in (("all bodies", np.ones(len(names), bool)),
                 ("GS_* shards only", is_gs)):
    z = L[-1, sel, 2] + r[sel]
    step = np.linalg.norm(L[-1, sel] - L[-2, sel], axis=1)
    out[tag] = dict(n=int(sel.sum()),
                    below_floor=int((z < -SINK_M).sum()),
                    below_floor_pct=round(100.0 * float((z < -SINK_M).mean()), 1),
                    worst_m=round(float(-z.min()), 3),
                    moving_over_1mm=int((step > 0.001).sum()),
                    moving_pct=round(100.0 * float((step > 0.001).mean()), 1),
                    worst_step_m=round(float(step.max()), 4))
print(json.dumps(out, indent=1))
print("last two table frames: %d, %d" % (frames[-2], frames[-1]))
with open(os.path.join(R2, "work/r2187/inherited_table.json"), "w") as fh:
    json.dump(dict(rows=out, last_frames=[int(frames[-2]), int(frames[-1])]),
              fh, indent=1)
print("STAGE RESULT: inherited done")
