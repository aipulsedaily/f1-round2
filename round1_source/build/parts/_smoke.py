"""Smoke test part: proves the harness end-to-end."""
import common as C
import spec as S

NAME = "_smoke"

def build(coll, ctx=None):
    ob = C.revolve("Smoke_Torus", [(0.10,0.0),(0.12,0.02),(0.10,0.04),(0.08,0.02),(0.10,0.0)],
                   segments=64, coll=coll, auto_smooth=32.0)
    S.assign(ob, "CarbonFibre")
    return [ob]
