"""THE CAMPAIGN PLAN: tier counts, agent counts and the FRAME/MACRO-peep split.

    python3 tools/agents_per_round.py \
        --items work/tier2/item_presence_a6.json \
        --peeps work/tier2/frame_peeps.json \
        --stamp work/tier2/inputs_a6.json \
        --out   docs/proposed_tiers.json

WHY THIS FILE EXISTS
--------------------
`docs/proposed_tiers.json` carried `agents_per_round`, `comparison` and
`bulk_cells` -- the numbers wave 2 is scoped against -- and **no script in the
repository wrote them.**  `tools/item_presence.py` writes `tier_counts` and
`groups`; every other key in that file came from somewhere that is not on
disk.  The `TOTAL_PER_ROUND` of 169 was therefore a number no one could
re-derive after the world or the camera moved, which is precisely when it
needs re-deriving.

Four of the five collapse rules WERE recoverable, by reproducing each stated
sub-total against the 2026-08-02 item table until it matched exactly:

    hero_build       51 agents  = distinct (module, name-family) among HERO
    reads_at_speed   45 agents  = distinct (module, name-family) among MID
    texture_and_mass 22 agents  = 16 (module, zone) cells holding >=6 BULK
                                  items, + 1 owner per module among the 20
                                  cells holding fewer (40 items, 6 modules)
    adversarial MACRO 15 peeps  = distinct name-family among the HERO items
                                  whose measured peak_sharp_px_4k > 1000

All four reproduce to the digit, so they are transcribed here rather than
guessed.  The fifth -- "36 FRAME-peeps" -- is NOT recoverable and is not
pretended to be; see `tools/frame_peeps.py`, which searched 1,296 candidate
binnings against the exact camera the old run used and found TWELVE that give
36 regimes at 88-90 %.  This file therefore takes the FRAME-peep count from
whatever `frame_peeps.py` reports under its own declared bands, and records
the bands in the output.

READ THE 4K FIELD.  The MACRO-peep rule tests `peak_sharp_px_4k`.  Reading
`peak_sharp_px` -- which is a per-metre figure, not a pixel count -- returns
0.0 for every people item and would argue the crowd work away; the real
figure for marshal and crew figures is 767.2 sharp px.  The field name is
spelled out in one place, here, so the next reader does not have to find that
out the hard way.
"""
import os, sys, json, time, argparse, collections

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Same collapse as tools/item_presence.py. One agent owns a name-family and
# emits its children, because the children ARE the parent at another scale.
FAM_ALIAS = {"catch": "catch_fence", "pit": None, "la": "la_passerelle",
             "tyre": None, "grass": "grass_clump", "team": "team_truck"}
BULK_CELL_MIN = 6          # a (module, zone) cell smaller than this has no agent
MACRO_PX = 1000.0          # HERO items above this get a macro reviewer


def family(r):
    tok = r["id"].split("_")
    al = FAM_ALIAS.get(tok[0], tok[0])
    return "_".join(tok[:2]) if al is None else al


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True, help="item_presence.py --out")
    ap.add_argument("--peeps", default="", help="frame_peeps.py --out")
    ap.add_argument("--stamp", default="", help="input_stamp.py --out")
    ap.add_argument("--against", default="", help="an earlier proposed_tiers.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    d = json.load(open(a.items))
    items = d["items"]
    counts = collections.Counter(i["proposed_tier"] for i in items)

    hero = [i for i in items if i["proposed_tier"] == "HERO"]
    mid = [i for i in items if i["proposed_tier"] == "MID"]
    bulk = [i for i in items if i["proposed_tier"] == "BULK"]

    hero_groups = sorted({(i["module"], family(i)) for i in hero})
    mid_groups = sorted({(i["module"], family(i)) for i in mid})

    cells = collections.Counter((i["module"], i["zone"]) for i in bulk)
    big = {k: v for k, v in cells.items() if v >= BULK_CELL_MIN}
    small = {k: v for k, v in cells.items() if v < BULK_CELL_MIN}
    owners = sorted({k[0] for k in small})
    bulk_agents = len(big) + len(owners)

    macro = [i for i in hero
             if (i.get("measured") or {}).get("peak_sharp_px_4k", 0.0) > MACRO_PX]
    macro_fams = sorted({family(i) for i in macro})

    fp = json.load(open(a.peeps)) if a.peeps and os.path.exists(a.peeps) else None
    frame_peeps = fp["FRAME_PEEPS"] if fp else 0
    review = frame_peeps + len(macro_fams)
    total = len(hero_groups) + len(mid_groups) + bulk_agents + review

    out = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "SOURCE": os.path.abspath(a.items) + " -- measured, not assigned. This file "
                  "is a PROPOSAL; docs/item_manifest.json is deliberately untouched, "
                  "because changing the manifest is a decision and this is a "
                  "measurement.",
        "RULE": d.get("METHOD", {}).get("tiers") if isinstance(d.get("METHOD"), dict)
                else None,
        "INPUT_IDENTITY": json.load(open(a.stamp)) if a.stamp and os.path.exists(a.stamp)
                          else "NOT STAMPED -- see tools/input_stamp.py and defect #97",
        "tier_counts": dict(counts),
        "agents_per_round": {
            "hero_build": {
                "items": len(hero), "agents": len(hero_groups),
                "unit": "(module, name-family); one agent owns the family and emits "
                        "its children"},
            "reads_at_speed": {
                "items": len(mid), "agents": len(mid_groups),
                "unit": "(module, name-family); silhouette, mass, value, "
                        "per-instance variation"},
            "texture_and_mass": {
                "items": len(bulk), "agents": bulk_agents,
                "unit": "(module, zone) cells of >=%d items get an agent each "
                        "(%d cells, %d items); the %d cells under %d items (%d items) "
                        "roll into their module owner (%s)"
                        % (BULK_CELL_MIN, len(big), sum(big.values()), len(small),
                           BULK_CELL_MIN, sum(small.values()), ", ".join(owners))},
            "adversarial_review": {
                "agents": review,
                "frame_peeps": frame_peeps,
                "macro_peeps": len(macro_fams),
                "macro_items": len(macro),
                "unit": "%d FRAME-peeps -- one per vantage regime MEASURED in the "
                        "built rig (beat x speed-band x lens-band x altitude-band, "
                        ">=%s frames each), each judged at the real camera, lens, "
                        "distance and shutter. Plus %d MACRO-peeps, one per "
                        "name-family among the %d HERO items whose measured "
                        "peak_sharp_px_4k exceeds %d -- the only items in the film "
                        "that genuinely receive macro scrutiny. NOT one peep per "
                        "item in a test scene at nearest_camera_m."
                        % (frame_peeps,
                           fp["bands"]["min_frames"] if fp else "?",
                           len(macro_fams), len(macro), int(MACRO_PX)),
                "FRAME_PEEP_ROUTE": (fp or {}).get("ROUTE",
                    "tools/frame_peeps.py was not run -- the count is 0 and the "
                    "total is short by it."),
                "frame_peep_bands": (fp or {}).get("bands"),
                "frame_peep_coverage_pct": (fp or {}).get("coverage_pct"),
                "macro_families": macro_fams,
            },
            "TOTAL_PER_ROUND": total,
        },
        "bulk_cells": (
            [{"module": k[0], "zone": k[1], "items": v, "own_agent": True}
             for k, v in sorted(big.items(), key=lambda x: -x[1])]
            + [{"module": k[0], "zone": k[1], "items": v, "own_agent": False,
                "rolls_into": k[0]}
               for k, v in sorted(small.items(), key=lambda x: -x[1])]),
        "groups": {
            "HERO": [{"family": list(g),
                      "items": sorted(i["id"] for i in hero
                                      if (i["module"], family(i)) == g)}
                     for g in hero_groups],
            "MID": [{"family": list(g),
                     "items": sorted(i["id"] for i in mid
                                     if (i["module"], family(i)) == g)}
                    for g in mid_groups],
        },
    }

    if a.against and os.path.exists(a.against):
        prev = json.load(open(a.against))
        pa = prev.get("agents_per_round", {})
        out["comparison"] = {
            "against": os.path.abspath(a.against),
            "against_generated": prev.get("generated"),
            "previous": {"tier_counts": prev.get("tier_counts"),
                         "agents": {k: (v.get("agents") if isinstance(v, dict) else v)
                                    for k, v in pa.items()}},
            "now": {"tier_counts": dict(counts),
                    "agents": {"hero_build": len(hero_groups),
                               "reads_at_speed": len(mid_groups),
                               "texture_and_mass": bulk_agents,
                               "adversarial_review": review,
                               "TOTAL_PER_ROUND": total}},
        }

    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print("[APR] tiers %s" % dict(counts))
    print("[APR] agents hero=%d mid=%d bulk=%d review=%d (frame %d + macro %d) "
          "TOTAL=%d" % (len(hero_groups), len(mid_groups), bulk_agents, review,
                        frame_peeps, len(macro_fams), total))
    print("[APR] wrote " + a.out)


if __name__ == "__main__":
    main()
