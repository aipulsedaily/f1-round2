"""ARE THE BODIES THAT END UNDER THE FLOOR THE SAME BODIES AS CLUSTER B?

    .venv/bin/python work/r2187/clusterb.py

Two of the three inherited open items may be one item:

  * 70 shards end below the floor, the worst 154.6 m down (R2-196's corrected
    figure, reproduced independently off the applied scene).
  * cluster B of R2-096: 348 shards reaching 106 m/s with no measurable
    contact, undiagnosed.

A body that leaves at 106 m/s and is never stopped goes a long way, and "a long
way" from a wall at z ~ 3 m with gravity on is exactly how you end up 154 m
below a floor.  If the two sets are the same set, that is one defect with two
symptoms and the sink count is a DOWNSTREAM READING of the blow-up rather than
an independent problem -- which changes who owns it and what fixing it means.

This does not diagnose cluster B.  It asks whether the overlap is there.
CONTROL: the same overlap computed against a random subset of the same size,
so "70 of the fastest 348" is read against what chance would give.
"""
import json
import os
import sys

import numpy as np

R2 = os.path.expanduser("~/f1-round2")
sys.path.insert(0, os.path.join(R2, "sim"))
import resample as RS          # noqa: E402
import fracture as FR          # noqa: E402
import shardmesh as SM         # noqa: E402
import breachlib as BL         # noqa: E402

SINK_M = 0.004

film = RS.read_film(os.path.join(R2, "sim/out/breach_film.npz"))
names = film["names"]
frames = np.arange(int(film["span"][0]), int(film["span"][1]) + 1)
L, Q = film["expand"](frames)
fps = 24.0

is_gs = np.array([n.startswith("GS_b") for n in names])

# speed proxy: metres per FILM FRAME between reconstruction samples, x fps
step = np.linalg.norm(np.diff(L, axis=0), axis=2) * fps      # (nf-1, nbody)
vmax = step.max(axis=0)

# lowest vertex at the last frame, rotated -- the corrected sink measure
plan = FR.load(os.path.join(R2, "sim/out/fracture_wall.npz"))
loc_verts = {}
for bay in sorted(plan["panes"]):
    if plan["roles"][bay] == "intact":
        continue
    for s in plan["panes"][bay]:
        nm = "GS_b%02d_%05d" % (bay, s["id"])
        V, _F = SM.prism(s["poly"], 14.95500, 14.96650, detail=1,
                         seed=1000 * bay + s["id"])
        loc_verts[nm] = np.asarray(V, float)


def qmat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


lo = np.full(len(names), np.inf)
for j, nm in enumerate(names):
    V = loc_verts.get(nm)
    if V is None:
        continue
    R = qmat(Q[-1, j] / np.linalg.norm(Q[-1, j]))
    lo[j] = (V @ R.T)[:, 2].min() + L[-1, j, 2]

sunk = (lo < -SINK_M) & is_gs
n_sunk = int(sunk.sum())

rng = np.random.default_rng(2187)
rows = {}
for thr in (60.0, 100.0, 106.0):
    fast = (vmax >= thr) & is_gs
    both = int((fast & sunk).sum())
    # CONTROL: a random set of the same size as `fast`, drawn from the shards
    trials = []
    idx = np.flatnonzero(is_gs)
    for _ in range(200):
        pick = rng.choice(idx, size=int(fast.sum()), replace=False)
        m = np.zeros(len(names), bool)
        m[pick] = True
        trials.append(int((m & sunk).sum()))
    rows["v >= %.0f m/s" % thr] = dict(
        n_fast=int(fast.sum()), of_which_sunk=both,
        pct_of_sunk_explained=round(100.0 * both / max(n_sunk, 1), 1),
        chance_mean=round(float(np.mean(trials)), 1),
        chance_p95=int(np.percentile(trials, 95)))

out = dict(bodies=len(names), shards=int(is_gs.sum()),
           sunk_rotated=n_sunk,
           worst_below_m=round(float(-lo[np.isfinite(lo)].min()), 3),
           vmax_of_sunk=dict(
               median=round(float(np.median(vmax[sunk])), 1),
               min=round(float(vmax[sunk].min()), 1),
               max=round(float(vmax[sunk].max()), 1)),
           vmax_of_the_rest=dict(
               median=round(float(np.median(vmax[is_gs & ~sunk])), 1),
               p99=round(float(np.percentile(vmax[is_gs & ~sunk], 99)), 1)),
           overlap=rows,
           speed_note="max |dx| per film frame x 24, on the decimated "
                      "reconstruction -- the same table the scene was built "
                      "from, so this is the speed the RENDER has, not the "
                      "240 Hz bake's")
print(json.dumps(out, indent=1))
with open(os.path.join(R2, "work/r2187/clusterb.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print("STAGE RESULT: clusterb done")
