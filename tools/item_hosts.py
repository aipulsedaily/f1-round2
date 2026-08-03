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
"""
import re

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


def hosts_for(item, all_names):
    """-> (list of object names, tier) where tier is NAMED / ZONE / UNMAPPED."""
    iid = item["id"]
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


def audit(items, all_names):
    """Every pattern that matches nothing, and every item that maps to nothing."""
    dead = []
    for pats in list(ZONE_HOSTS.values()) + [p for _, p in NAMED]:
        for p in pats:
            if not any(re.search(p, n) for n in all_names):
                dead.append(p)
    unmapped = [it["id"] for it in items if hosts_for(it, all_names)[1] == "UNMAPPED"]
    return sorted(set(dead)), unmapped
