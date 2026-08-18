"""Which world geometry does each manifest item live on?

THE PROBLEM THIS SOLVES, STATED BEFORE THE TABLE
------------------------------------------------
`docs/item_manifest.json` has 435 records and no coordinates.  The assembled
world (`assembly2.blend`, contract 1.0.1) has 468 evaluated objects and 28,313
vegetation instances, and **not one of them is a manifest item**.  The world was
built by class-level placement systems -- `BR_Armco_L07` is 300 m of barrier
run, `ARCH_PaddockBuildings` is every paddock building welded into one mesh --
while the manifest names the FEATURES those systems do or will carry.  407 of
the 435 items have no module of their own yet at all.

So "where is `truck_mud_flap`" has no exact answer and will not have one until
the item campaign builds it.  What DOES have an exact answer is "where is the
geometry a mud flap hangs off", and that is `ARCH_Ground_Compound` /
`ARCH_Paving_Paddock` in the transporter park.

THE RULE, AND ITS DIRECTION OF ERROR
------------------------------------
Each item maps to a HOST SET of world objects.  Its measured screen presence is
the BEST moment any point of any host ever has.  An item cannot be seen better
than the surface it sits on, so every number derived this way is an UPPER BOUND
on the item.  That matters: a demotion taken against an upper bound is safe,
a promotion is not.  Where the table is wrong it is wrong generously.

Two tiers, and which one an item got is recorded per item in the output:

  NAMED   the item resolves to specific objects by name -- `kerb_hero_t4` ->
          `SURF_Kerb_T4_*`, `gantry_*` -> `ARCH_Gantry`, `pont_*` ->
          `ARCH_PontPlongee`.  Tight, and the host really is the thing.
  ZONE    the item resolves only to its zone's host objects -- `bin_liner` ->
          the whole paddock.  For an item with hundreds of instances spread
          over the zone this is close to right; for a single-instance item it
          is loose and generous, and the count of hosts is reported so a reader
          can see which.

An item that resolves to NOTHING is reported as `unmapped` rather than assigned
a default.  On this project an instrument that quietly falls through to a
weaker answer is R2-019, and it passed a mannequin crowd.

THE THIRD TIER, ADDED R2-1385: SELF
-----------------------------------
Everything above was written when the sentence "not one of them is a manifest
item" was TRUE.  It stopped being true when `assembly10` placed the first four
item modules, and **nothing here noticed**, because the whole table maps an item
to somebody ELSE'S geometry and there was no rule that could prefer the item's
own.  Measured (R2-1277): 1,700 item objects were in the point cloud and were
being measured perfectly well as objects, while `timing_stand` the ITEM resolved
to `ARCH_PitWall` and `catch_fence_post` to `BR_FenceStruct_*`.  **0 of 435 items
resolved to a host list containing their own datablock, including the four that
were physically in the ship.**

And no instrument fired.  `audit()` reported `dead=[]` and `unmapped=[]` and both
were TRUE: every item did resolve to *a* host.  It resolved to the wrong one.
That is this project's most-logged defect shape -- a guard that cannot fire --
and the reason the census below is returned whether or not anything is wrong.

  SELF    the item's OWN declared prefix has geometry in the world, so the item
          is measured as itself.  This is not an upper bound; it is the item.
          The prefix is NOT guessed from the id -- guessing a convention is
          R2-180 -- it is read from `world/items/PLACEMENT.json`, which
          establishes `collection` and `prefix` per row by AST from each
          module's own top-level constants (see its `how_a_row_is_established`).

SELF beats NAMED beats ZONE.  A row whose prefix matches nothing in the world
falls through to the class host exactly as before, so a HOLD row -- and there
are 38 of them -- costs nothing and needs no special case.  **Presence of
geometry decides, not the `state` field**, which is what keeps this correct
while `world/items/` is being written underneath the measurement.
"""
import json
import os
import re

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLACEMENT = os.path.join(R2, "world", "items", "PLACEMENT.json")

# --------------------------------------------------------------------------
# ZONE -> host object name patterns.  Regexes against the object name.
# Every pattern here was checked against the actual 468-object name list dumped
# from assembly2.blend; a pattern that matches nothing is a mapping defect and
# `audit()` prints it.
ZONE_HOSTS = {
    "showroom_breach":  [r"^ARCH_ShowroomSurrounds$", r"^ARCH_Paving_ApronPlatform$",
                         r"^ARCH_Paving_Forecourt$"],
    "transit_corridor": [r"^BR_Transit_", r"^SURF_AccessRoad$", r"^ARCH_RetainEdge$",
                         r"^ARCH_Paving_ApronPlatform$"],
    "paddock":          [r"^ARCH_PaddockBuildings$", r"^ARCH_Paving_Paddock$",
                         r"^ARCH_Ground_Compound$", r"^ARCH_Ground_ServiceRoad$",
                         r"^ARCH_Ground_Furniture$", r"^ARCH_Ground_Fences$",
                         r"^ARCH_Ground_Decks$", r"^ARCH_RaceControl$"],
    "pit_building":     [r"^ARCH_PitBuilding_", r"^ARCH_Paving_Garages$"],
    "pit_lane":         [r"^ARCH_Paving_PitLane$", r"^ARCH_PitWall$",
                         r"^ARCH_Paving_Garages$"],
    "pit_straight":     [r"^ARCH_Gantry$", r"^ARCH_LaPasserelle$", r"^ARCH_PitWall$",
                         r"^SURF_Track$", r"^SURF_GridNum_", r"^DR_Flagpoles$"],
    "grandstand":       [r"^ARCH_Grandstand_"],
    "crowd":            [r"^ARCH_Grandstand_", r"^ARCH_Ground_Decks$",
                         r"^ARCH_Ground_Furniture$", r"^ARCH_LaPasserelle$"],
    "track_surface":    [r"^SURF_Track$", r"^SURF_ApronJoint$", r"^SURF_AccessRoad$"],
    "kerbs_markings":   [r"^SURF_Kerb_", r"^DR_Kerb_", r"^ARCH_RoadMarkings$",
                         r"^ARCH_Markings$", r"^DR_Paint_", r"^SURF_GridNum_"],
    "runoff":           [r"^BR_Runoff_", r"^BR_Verge_", r"^BR_Subbase_",
                         r"^BR_Trap_", r"^BR_Stones_"],
    "barriers":         [r"^BR_Armco_", r"^BR_FenceMesh_", r"^BR_FenceStruct_",
                         r"^BR_FenceWire_", r"^BR_TecPro_", r"^BR_TyreWall_",
                         r"^BR_Concrete_", r"^BR_Transit_"],
    "bridges":          [r"^ARCH_PontPlongee$", r"^DR_BridgeBanners$"],
    "trackside":        [r"^DR_Post_", r"^DR_Sign_", r"^DR_Ad_", r"^DR_Ban_",
                         r"^DR_Billboard_", r"^DR_Marker_", r"^DR_Speaker_",
                         r"^DR_TVCam_", r"^DR_Tyres_", r"^DR_Apex_",
                         r"^DR_Flagpoles$"],
    "vegetation":       [r"^VEG", r"^TER_Ground$", r"^ARCH_Ground_Planting$"],
    # People are NOT BUILT.  Every figure is placed on trackside, pit-lane or
    # paddock ground, so they inherit that ground's screen presence.  This is
    # the loosest row in the table and it is flagged as such per item.
    "people":           [r"^DR_Post_", r"^ARCH_Paving_PitLane$", r"^ARCH_PitWall$",
                         r"^ARCH_Ground_Compound$", r"^ARCH_Paving_Paddock$"],
    # Ephemera is by definition everywhere the camera looks at the ground.
    "ephemera":         [r"^SURF_", r"^ARCH_Paving_", r"^BR_Trap_", r"^BR_Verge_",
                         r"^ARCH_Ground_Compound$", r"^TER_Ground$"],
}

# --------------------------------------------------------------------------
# ITEM id substring -> host patterns, applied BEFORE the zone rule and winning
# when it fires.  These are the items whose host really is a named object.
NAMED = [
    (r"^kerb_hero_t4$",                 [r"^SURF_Kerb_T4_"]),
    (r"^gantry_",                       [r"^ARCH_Gantry$"]),
    (r"^start_light",                   [r"^ARCH_Gantry$"]),
    (r"^la_passerelle_",                [r"^ARCH_LaPasserelle$"]),
    (r"^passerelle_crowd",              [r"^ARCH_LaPasserelle$"]),
    (r"^pont_",                         [r"^ARCH_PontPlongee$", r"^DR_BridgeBanners$"]),
    (r"^bridge_expansion_joint$",       [r"^ARCH_PontPlongee$", r"^SURF_Track$"]),
    (r"^pit_wall_",                     [r"^ARCH_PitWall$"]),
    (r"^timing_stand",                  [r"^ARCH_PitWall$"]),
    (r"^pit_board$",                    [r"^ARCH_PitWall$"]),
    (r"^armco_",                        [r"^BR_Armco_"]),
    (r"^catch_fence_",                  [r"^BR_FenceMesh_", r"^BR_FenceStruct_",
                                         r"^BR_FenceWire_"]),
    (r"^tecpro_",                       [r"^BR_TecPro_"]),
    (r"^tyre_wall_",                    [r"^BR_TyreWall_", r"^BR_Transit_TyreWall$"]),
    (r"^concrete_barrier_block$|^concrete_lifting_eye$",
                                        [r"^BR_Concrete_"]),
    (r"^transit_tyre_wall_stack$",      [r"^BR_Transit_TyreWall$"]),
    (r"^transit_debris_fence$",         [r"^BR_Transit_Fence$", r"^BR_Transit_FenceMesh$"]),
    (r"^pit_exit_portal",               [r"^BR_Transit_Portal$"]),
    (r"^portal_boom_gate$",             [r"^BR_Transit_Portal$"]),
    (r"^apron_wall_",                   [r"^BR_Transit_NorthWall$"]),
    (r"^access_road_",                  [r"^SURF_AccessRoad$"]),
    (r"^grid_num|^grid_box|^grid_numeral$",
                                        [r"^SURF_GridNum_", r"^ARCH_RoadMarkings$"]),
    (r"^start_finish_line$",            [r"^ARCH_RoadMarkings$", r"^SURF_Track$"]),
    (r"^kerb_precast_unit$|^kerb_bedding_joint$|^kerb_end_ramp$|^kerb_negative_trough$",
                                        [r"^SURF_Kerb_", r"^DR_Kerb_"]),
    (r"^gravel_|^gravel_bed_surface$",  [r"^BR_Trap_", r"^BR_Stones_"]),
    (r"^grass_runoff_turf$|^verge_",    [r"^BR_Verge_", r"^BR_Runoff_"]),
    (r"^runoff_",                       [r"^BR_Runoff_", r"^BR_Subbase_"]),
    (r"^grandstand_",                   [r"^ARCH_Grandstand_"]),
    (r"^big_screen|^timing_tower$|^podium_",
                                        [r"^ARCH_Grandstand_Towers$",
                                         r"^ARCH_Grandstand_Terrace$"]),
    (r"^marshal_post_",                 [r"^DR_Post_"]),
    (r"^tv_camera_|^tv_cam",            [r"^DR_TVCam_"]),
    (r"^tyre_stack_trackside$",         [r"^DR_Tyres_"]),
    (r"^advertising_board$|^apex_sponsor_board$|^free_standing_hoarding$|^hoarding_leg$",
                                        [r"^DR_Ad_", r"^DR_Billboard_", r"^DR_Apex_"]),
    (r"^catch_fence_banner$",           [r"^DR_Ban_"]),
    (r"^distance_marker_board$|^corner_number_plate$|^corner_name_plate$",
                                        [r"^DR_Marker_", r"^DR_Sign_"]),
    (r"^pa_horn_speaker$",              [r"^DR_Speaker_"]),
    (r"^team_truck_|^truck_|^motorhome_unit$|^hospitality_",
                                        [r"^ARCH_Ground_Compound$",
                                         r"^ARCH_Ground_Decks$"]),
    (r"^garage_",                       [r"^ARCH_PitBuilding_", r"^ARCH_Paving_Garages$"]),
    (r"^showroom_|^glass_|^mullion_|^curtain_wall_|^glazing_|^wall_stud_framing$|"
     r"^floor_shard|^dais_|^concrete_spall|^breach_dust",
                                        [r"^ARCH_ShowroomSurrounds$",
                                         r"^ARCH_Paving_ApronPlatform$"]),
    (r"^forecourt_|^exterior_ground_apron$",
                                        [r"^ARCH_Paving_Forecourt$",
                                         r"^ARCH_Paving_ApronPlatform$"]),
    (r"^asphalt_|^track_|^lockup_skid_mark$|^launch_rubber_stripe$|^rubber_line_deposit$|"
     r"^tyre_marble$|^marble_drift_bank$|^timing_loop_sawcut$",
                                        [r"^SURF_Track$", r"^SURF_ApronJoint$"]),
    (r"^white_line_edge$|^pit_exit_blend_line$|^pit_exit_gore$|^pit_lane_speed_line$|"
     r"^pit_box_marking$",              [r"^ARCH_RoadMarkings$", r"^ARCH_Markings$",
                                         r"^ARCH_Paving_PitLane$"]),
    (r"^terrain_ground$|^escarpment_skyline$|^drainage_ditch$|^field_boundary_fence$|"
     r"^farm_gate$|^rock_|^bare_soil_scar$",
                                        [r"^TER_Ground$"]),
    (r"^tree_|^shrub_|^hedgerow_section$|^fern_clump$|^log_pile$|^fallen_branch$|"
     r"^leaf_litter$|^moss_patch$",     [r"^VEG"]),
    (r"^grass_clump_|^weed_joint_colonist$|^grass_clipping_drift$",
                                        [r"^VEG", r"^TER_Ground$"]),
    (r"^paddock_avenue_tree$|^planter_shrub$", [r"^VEG", r"^ARCH_Ground_Planting$"]),
    (r"^flagpole$|^sponsor_flag$|^windsock$", [r"^DR_Flagpoles$"]),
    (r"^heras_|^jersey_barrier$|^traffic_cone$|^cone_connector_bar$|^cable_ramp$",
                                        [r"^BR_Transit_", r"^SURF_AccessRoad$"]),
    (r"^race_control_building$",        [r"^ARCH_RaceControl$"]),
    (r"^media_centre_building$|^medical_centre_building$",
                                        [r"^ARCH_PaddockBuildings$"]),
]

NAMED = [(re.compile(a), b) for a, b in NAMED]


def placement_prefixes(registry=PLACEMENT):
    """-> {manifest item id: [declared object-name prefixes]}.

    Read from the ledger, never derived from the id.  Several ids carry more
    than one row (`spectator_seated` has three: two HOLD probes and the PLACE
    row, declaring `SPECX_` and `SPECSEAT_`), so the prefixes are UNIONED --
    the question being asked is "is any geometry this item declares present",
    and answering it from one arbitrarily-chosen row would be a guess.

    Six ledger rows (`human_clay`, `human_peep`, ...) are probes with no
    manifest id and no prefix; they simply never match.

    RAISES if the ledger is unreadable.  A measurement that silently degrades
    to "no item owns any geometry" is precisely the state R2-1277 found, and it
    looked exactly like success.
    """
    reg = json.load(open(registry))
    out = {}
    for r in reg["items"]:
        px, iid = r.get("prefix"), r.get("item")
        if px and iid:
            out.setdefault(iid, [])
            if px not in out[iid]:
                out[iid].append(px)
    return out


def self_hosts(iid, all_names, self_prefixes):
    """-> the item's OWN objects in the world, by its declared prefix."""
    pats = (self_prefixes or {}).get(iid) or []
    return [n for n in all_names if any(n.startswith(p) for p in pats)]


def hosts_for(item, all_names, self_prefixes=None):
    """-> (list of object names, tier), tier SELF / NAMED / ZONE / UNMAPPED.

    `self_prefixes` omitted reproduces the pre-R2-1385 behaviour exactly, which
    is what the control in `item_presence.py --no-self-hosts` runs.
    """
    iid = item["id"]
    if self_prefixes:
        got = self_hosts(iid, all_names, self_prefixes)
        if got:
            return got, "SELF"
    for rx, pats in NAMED:
        if rx.search(iid):
            got = [n for n in all_names if any(re.search(p, n) for p in pats)]
            if got:
                return got, "NAMED"
    pats = ZONE_HOSTS.get(item["zone"], [])
    got = [n for n in all_names if any(re.search(p, n) for p in pats)]
    if got:
        return got, "ZONE"
    return [], "UNMAPPED"


def audit(items, all_names, self_prefixes=None):
    """-> (dead patterns, unmapped ids, the SELF census).

    THE CENSUS IS RETURNED WHETHER OR NOT ANYTHING IS WRONG.  `dead` and
    `unmapped` are both routinely `[]` on a file where every one of 435 items
    is mis-hosted, because "resolved to nothing" and "resolved to the wrong
    thing" are different failures and only the first had an instrument.

    `self_available_but_not_used` is the one that matters: an item whose own
    declared geometry IS in the world and which was nonetheless measured
    against somebody else's.  It is computed from the ledger and the name list
    DIRECTLY -- not from the tier that was assigned -- so it fires no matter
    which resolution path ran, including the old one.
    """
    dead = []
    for pats in list(ZONE_HOSTS.values()) + [p for _, p in NAMED]:
        for p in pats:
            if not any(re.search(p, n) for n in all_names):
                dead.append(p)

    px = self_prefixes if self_prefixes is not None else placement_prefixes()
    unmapped, missed, used, absent = [], [], [], []
    for it in items:
        iid = it["id"]
        h, tier = hosts_for(it, all_names, self_prefixes)
        if tier == "UNMAPPED":
            unmapped.append(iid)
        own = self_hosts(iid, all_names, px)
        if own and tier != "SELF":
            missed.append({"item": iid, "own_objects": len(own),
                           "declared_prefixes": px.get(iid),
                           "measured_against_instead": tier,
                           "hosts": h[:6]})
        elif own:
            used.append({"item": iid, "own_objects": len(own),
                         "declared_prefixes": px.get(iid)})
        elif iid in px:
            absent.append(iid)

    census = {
        "WHAT_THIS_COUNTS":
            "How each item was measured. SELF = against its own declared "
            "geometry, which is the item. NAMED/ZONE = against a class host, "
            "which is an UPPER BOUND on the item and nothing more.",
        "ledger": os.path.relpath(PLACEMENT, R2),
        "ledger_rows_with_a_prefix": len(px),
        "items_measured_against_own_geometry": len(used),
        "items_measured_against_a_class_host": len(items) - len(used) - len(unmapped),
        "items_with_a_ledger_row_whose_geometry_is_absent": len(absent),
        "SELF_HOST_MISSED": missed,
        "SELF_HOST_MISSED_n": len(missed),
        "measured_as_self": sorted(used, key=lambda d: -d["own_objects"]),
        "ledger_row_geometry_absent": sorted(absent),
    }
    return sorted(set(dead)), unmapped, census
