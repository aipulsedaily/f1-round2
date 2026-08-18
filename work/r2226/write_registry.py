#!/usr/bin/env python3
"""Write world/items/PLACEMENT.json from the measured facts + the placement judgements.

Facts come from work/r2226/registry_facts.json (module AST + canonical gate.json
+ blend sha256 + the inventory probe). Judgements are stated here, each with the
artefact that establishes it.
"""
import json, os, time

ROOT = os.path.expanduser("~/f1-round2")
facts = json.load(open(os.path.join(ROOT, "work/r2226/registry_facts.json")))

# --------------------------------------------------------------------------
# The class-level geometry each item would double-build, MEASURED from
# assembly9_build.json's own counters and assembly9's object-name list.
# `object`   -> a whole object; the placement stage can remove it here.
# `welded_in`-> welded inside a shared class mesh; removing it is a change to
#               the class module and a full assembly, which this stage may not
#               do. Reported as REBUILD_OWED.
SUPERSEDE = {
 "timing_stand": [{"welded_in": "ARCH_PitWall", "counter": "pit_wall_stands", "n": 5,
   "reason": "build_architecture welds 5 stands into ARCH_PitWall's single mesh; "
             "the item builds 10. Census §2.2: 'timing_stand's feature IS in the "
             "world as pit_wall_stands = 5 welded inside ARCH_PitWall'."}],
 "pit_wall_unit": [{"welded_in": "ARCH_PitWall", "counter": "pit_wall_stands", "n": 5,
   "reason": "ARCH_PitWall IS the pit wall. Placing 119 hero units beside it "
             "double-builds the whole wall."}],
 "armco_post": [{"welded_in": "BR_Armco_*", "counter": "armco_posts", "n": 3561,
   "reason": "build_barriers welds 3,561 posts into 27 BR_Armco_* meshes with "
             "1,781 panels and 4,675 bolts. The posts cannot be lifted out "
             "without a build_barriers change."}],
 "catch_fence_post": [{"welded_in": "BR_FenceStruct_*", "counter": "fence_posts", "n": 676,
   "reason": "build_barriers reports fence_posts = 676 and the item builds 676. "
             "The counts agree exactly, so this is unambiguously the same "
             "population twice -- welded into 27 BR_FenceStruct_* meshes."}],
 "tyre_wall_tyre": [{"object": "BR_TyreWall_T4",
   "reason": "BR_TyreWall_T4 is a WHOLE OBJECT in assembly9 and is exactly the "
             "wall this item rebuilds (s 912-1058). This one supersede is "
             "removable at placement time -- but only once the item ships its "
             "full population; see blockers."}],
 "heras_fence_panel": [{"welded_in": "BR_Transit_Fence", "counter": "gates", "n": 28,
   "reason": "the transit-corridor fencing is BR_Transit_Fence + "
             "BR_Transit_FenceMesh; the item's 771 panels span a wider "
             "footprint than either, so the overlap is not established and the "
             "swap is not a clean one."}],
 "gantry_truss": [{"welded_in": "ARCH_Gantry", "counter": "gantry_soffit_z", "n": None,
   "reason": "ARCH_Gantry is the start gantry. The item is the same structure."}],
 "pont_girder": [{"welded_in": "ARCH_PontPlongee", "counter": "bridges", "n": 2,
   "reason": "ARCH_PontPlongee is the plunge bridge; PGD_Girders are its girders."}],
 "pont_deck_slab": [{"welded_in": "ARCH_PontPlongee", "counter": "bridges", "n": 2,
   "reason": "as pont_girder -- the same bridge."}],
 "terrain_ground": [{"welded_in": "TER_Ground", "counter": "objects", "n": 1,
   "reason": "TER_Ground is the terrain. The item is a hero patch of the same."}],
 "forecourt_paving_bay": [{"welded_in": "ARCH_Paving_Forecourt", "counter": "paving_bays", "n": 5491,
   "reason": "build_architecture pavings the forecourt already."}],
 "paddock_paving_bay": [{"welded_in": "ARCH_Paving_Paddock", "counter": "paving_bays", "n": 5491, "reason": "as forecourt_paving_bay."}],
 "hospitality_deck": [{"welded_in": "ARCH_Ground_Decks", "counter": "ground_decks", "n": 5,
   "reason": "ground_decks = 5 and the item builds 5. The counts agree exactly."}],
 "team_truck_trailer": [{"welded_in": "ARCH_Ground_Compound", "counter": "transporters", "n": 20,
   "reason": "transporters = 20 welded into ARCH_Ground_Compound."}],
 "grandstand_riser_unit": [{"welded_in": "ARCH_Grandstand_*", "counter": "terrace_bays", "n": 918, "reason": "the grandstands are built."}],
 "kerb_precast_unit": [{"welded_in": "SURF_Kerb_*", "counter": "kerb_runs", "n": 35, "reason": "35 kerb runs, 1.6 M triangles, already built."}],
 "armco_w_beam": [{"welded_in": "BR_Armco_*", "counter": "armco_panels", "n": 1781, "reason": "as armco_post."}],
 "marshal_post_column": [{"welded_in": "DR_Post_*", "counter": "objects", "n": 24, "reason": "24 DR_Post_* objects are the marshal posts."}],
 "marshal_post_deck": [{"welded_in": "DR_Post_*", "counter": "objects", "n": 24, "reason": "as marshal_post_column."}],
 "mullion_intact": [{"welded_in": "(round-1 showroom, film14 only)", "counter": None, "n": None,
   "reason": "the showroom is NOT in assembly9; it is round-1 geometry composited "
             "into film14. Census §1.4."}],
 "showroom_facade_panel": [{"welded_in": "(round-1 showroom, film14 only)", "counter": None, "n": None, "reason": "as mullion_intact."}],
 "dais_delivery_ramp": [{"welded_in": "(round-1 showroom, film14 only)", "counter": None, "n": None, "reason": "as mullion_intact."}],
 "access_road_slab": [{"welded_in": "SURF_AccessRoad", "counter": "access_quads", "n": 35904, "reason": "the access road is built."}],
 "asphalt_wearing_course": [{"welded_in": "SURF_Track", "counter": "road_quads", "n": 516664, "reason": "the racing surface is built."}],
 "gravel_bed_surface": [{"welded_in": "BR_Trap_*", "counter": "stones", "n": 240000, "reason": "20 BR_Trap_* beds with 240,000 stones are built."}],
 "tyre_blanket": [], "crew_figure": [], "crew_fireproof_overall": [],
 "driver_figure": [], "paddock_personnel_figure": [],
 "spectator_seated": [], "spectator_crowd": [], "spectator_standing_ga": [],
 "showroom_facade_panel_v2": [], "pit_wall_unit_itemkit": [],
}

PROBES = {"human_clay", "human_fabric_probe", "human_peep", "human_png",
          "human_sweep", "human_bench"}
# Modules whose test blend lays the population out on a GRID for looking at,
# not at world coordinates. Read from the module source: `ob.location =
# (off + (n % per_row) * pitch, ...)`.
GRID_LAID = {"spectator_crowd", "spectator_standing_ga"}
# Modules that build in a LOCAL frame and publish place=(R, t). Placing them
# needs the transform applied; the stage refuses `frame: world` for these.
LOCAL_FRAME = {"pont_girder", "pont_deck_slab", "gantry_truss", "driver_figure",
               "crew_fireproof_overall"}
DUPLICATE_OF = {"pit_wall_unit_itemkit": "pit_wall_unit",
                "showroom_facade_panel_v2": "showroom_facade_panel"}

RIG_DEFAULT = lambda c: [c + "/Cameras", c + "/Standins"]

items = []
for f in facts:
    mod, item = f["module"], f["item"]
    blockers = []
    if mod in PROBES:
        blockers.append({"kind": "NOT_AN_ITEM",
                         "detail": "tooling/probe module; declares no manifest id "
                                   "and its absence from the world is correct "
                                   "(census §2.4)"})
    if mod in DUPLICATE_OF:
        blockers.append({"kind": "DUPLICATE_MODULE",
                         "detail": "second implementation of %r; placing both "
                                   "would place the item twice"
                                   % DUPLICATE_OF[mod]})
    if f["blend"] is None and mod not in PROBES:
        blockers.append({"kind": "NO_BUILT_BLEND",
                         "detail": "no world/items/%s_test.blend on disk" % mod})
    if f["gate_result"] is None and mod not in PROBES:
        blockers.append({"kind": "NO_GATE_REPORT",
                         "detail": "no render/items/%s/gate.json" % item})
    elif f["gate_result"] not in (None, "ITEM_ACCEPTED"):
        blockers.append({"kind": "GATE_NOT_ACCEPTED",
                         "detail": "canonical gate.json result is %r"
                                   % f["gate_result"]})
    if mod in GRID_LAID:
        blockers.append({"kind": "NO_WORLD_FRAME",
                         "detail": "the test blend lays the population out on a "
                                   "grid for the macro camera; the module never "
                                   "resolves world positions, so there is "
                                   "nothing to place"})
    if mod in LOCAL_FRAME:
        blockers.append({"kind": "LOCAL_FRAME",
                         "detail": "builds in a local frame and publishes "
                                   "place=(R, t); the stage needs the transform "
                                   "applied and this registry does not yet "
                                   "carry it"})
    go, gd = f["gate_objects"], f["gate_declared"]
    if go and gd and gd > 1 and go < gd:
        blockers.append({"kind": "PARTIAL_BUILD",
                         "detail": "the blend holds %d units; the item declares "
                                   "%d. A gating sample is not the shipping "
                                   "population." % (go, gd)})
    sup = SUPERSEDE.get(mod, [])
    welded = [s for s in sup if "welded_in" in s]
    if welded:
        blockers.append({"kind": "SUPERSEDE_WELDED",
                         "detail": "the world already builds this feature, "
                                   "welded into %s. Census §3.2: 'the moment it "
                                   "is placed the old version has to come out.'"
                                   % ", ".join(s["welded_in"] for s in welded)})
    coll = f["collection"]
    row = {
        "key": mod,
        "item": item,
        "module": "world/items/%s.py" % mod,
        "collection": coll,
        "prefix": f["prefix"],
        "frame": "world",
        "source_blend": (os.path.relpath(f["blend"], ROOT) if f["blend"] else None),
        "source_sha256": f["blend_sha"],
        "expect_objects": f["inv_objects"] if f["inv_objects"] is not None else f["gate_objects"],
        "expect_objects_source": ("inventory probe work/r2226/inv_%s.json" % mod)
                                 if f["inv_objects"] is not None
                                 else "render/items/%s/gate.json measured.objects" % item,
        "rig_subcollections": (f["inv_rig"] if f["inv_rig"] is not None
                               else (RIG_DEFAULT(coll) if coll else None)),
        "gate_result_at_registry_time": f["gate_result"],
        "supersedes": sup,
        "state": "PLACE" if not blockers else "HOLD",
        "blockers": blockers,
    }
    items.append(row)

# The one PLACE. Everything about it is measured above; this records WHY it is
# the only one, in the file the stage reads.
for r in items:
    if r["key"] == "crew_figure":
        r["state"] = "PLACE"
        r["place_because"] = (
            "ITEM_ACCEPTED; 120 objects built against 120 declared, so the "
            "blend is the whole population and not a gating sample; every unit "
            "is its own mesh datablock (120/120, top_share 0.833 %); the module "
            "resolves each figure through world_contract at build time so the "
            "blend is already in world coordinates; and it supersedes NOTHING "
            "-- census §2.5: 0 of assembly9's 30,183 datablock names and 0 of "
            "film14's 32,069 match figure|person|crowd|spectat|skin|hair|human|"
            "crew|driver, and there is no skin, flesh or hair material among "
            "the 130 / 191. This is the first human geometry in the film.")

n_place = sum(1 for r in items if r["state"] == "PLACE")
reg = {
 "schema": "f1-round2/item_placement/1.0",
 "generated": time.strftime("%Y-%m-%d"),
 "defect_block": "R2-226",
 "purpose": ("THE PLACEMENT LEDGER. One row per module under world/items/. "
             "world/build_items.py places every row whose state is PLACE and "
             "REFUSES any item that has no row -- there is no auto-detection "
             "and no fallback, because R2-180 is what a fallback looks like."),
 "how_a_row_is_established": {
   "collection/prefix": "read from the module's own top-level constants by AST "
                        "(work/r2226/gen_registry.py); agrees with the census "
                        "§8 table on all 41 rows, two independent readings",
   "expect_objects":    "the inventory probe where one was run, else the "
                        "canonical gate.json's measured.objects",
   "source_sha256":     "sha256 of the whole blend, never a prefix of it",
   "supersedes":        "assembly9_build.json's own counters and assembly9's "
                        "object-name list, read back from the 4.21 GB artefact",
 },
 "counts": {"rows": len(items), "state_PLACE": n_place,
            "state_HOLD": len(items) - n_place},
 "items": items,
}
out = os.path.join(ROOT, "world", "items", "PLACEMENT.json")
json.dump(reg, open(out, "w"), indent=1)
print("wrote %s: %d rows, %d PLACE, %d HOLD" % (out, len(items), n_place, len(items)-n_place))
import collections as C
k = C.Counter(b["kind"] for r in items for b in r["blockers"])
for kk, v in k.most_common():
    print("   %-24s %d" % (kk, v))
