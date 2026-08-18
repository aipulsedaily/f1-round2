"""Turn the measured per-object screen presence into a per-ITEM table + a re-tier.

    python3 tools/item_presence.py --npz docs/screen_presence_points.npz \
        --out docs/screen_presence.json --tiers docs/proposed_tiers.json

Reads what `screen_presence.py` measured against the real camera, maps each of
the 435 manifest items onto its host geometry with `item_hosts.py`, and writes
one record per item.  It does NOT touch `docs/item_manifest.json`: changing the
manifest is a decision, this is a measurement.
"""
import sys, os, json, argparse, collections
import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "tools"))
import item_hosts as HOSTS                                        # noqa: E402

FPS = 24
RES_X = 3840


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", required=True)
    ap.add_argument("--manifest", default=os.path.join(R2, "docs/item_manifest.json"))
    ap.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    ap.add_argument("--objects", default=os.path.join(R2, "docs/screen_presence_objects.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--tiers", required=True)
    # THE CONTROL ARM, and the only reason it exists. Without a way to run the
    # pre-R2-1385 resolution, "SELF_HOST_MISSED is 0" is unfalsifiable: it
    # would be 0 both when the fix works and when the guard is vacuous. With
    # it, the same guard on the same npz reports 4 and then 0, which is what
    # makes the 0 mean something. See work/w2_0b/ctl_self_hosts.sh.
    ap.add_argument("--no-self-hosts", action="store_true",
                    help="CONTROL: resolve hosts the pre-R2-1385 way, ignoring "
                         "each item's own declared geometry. The audit still "
                         "runs and is expected to REFUSE.")
    ap.add_argument("--allow-self-host-missed", action="store_true",
                    help="do not exit non-zero when SELF_HOST_MISSED is "
                         "non-empty. For the control arm, which needs the "
                         "output written so the two runs can be diffed.")
    a = ap.parse_args()

    z = np.load(a.npz, allow_pickle=True)
    names = [str(x) for x in z["names"]]
    of_any, of_sharp, of_usharp = z["of_any"], z["of_sharp"], z["of_usharp"]
    of_flat, of_depth = z["of_flat"], z["of_depth"]
    nobj, nframes = of_any.shape
    nidx = {n: i for i, n in enumerate(names)}

    sheet = json.load(open(a.sheet))
    bounds = []
    for b in sheet["beats"]:
        f0 = max(1, int(round(b["start_s"] * FPS)) + 1)
        f1 = min(nframes, int(round((b["start_s"] + b["duration_s"]) * FPS)))
        bounds.append((b["name"], f0, f1))

    man = json.load(open(a.manifest))
    items = man["items"]

    # The ledger is read ONCE, here, and the same dict is handed to both the
    # resolver and the audit -- so the guard cannot be checking a different
    # ledger than the measurement used.
    ledger = HOSTS.placement_prefixes()
    self_px = None if a.no_self_hosts else ledger
    if a.no_self_hosts:
        print("[IP] CONTROL ARM: --no-self-hosts, resolving the pre-R2-1385 way")
    print("[IP] ledger %s: %d ids declare a prefix, read %s"
          % (os.path.relpath(HOSTS.PLACEMENT, R2), len(ledger),
             __import__("time").strftime("%Y-%m-%dT%H:%M:%S", __import__("time").localtime(
                 os.path.getmtime(HOSTS.PLACEMENT)))))

    dead, unmapped, census = HOSTS.audit(items, names, self_px)
    print(f"[IP] host patterns matching nothing: {dead}")
    print(f"[IP] items with no host at all: {len(unmapped)} {unmapped[:20]}")
    print("[IP] measured as THEMSELVES: %d   against a class host: %d   "
          "ledger row present but geometry absent: %d"
          % (census["items_measured_against_own_geometry"],
             census["items_measured_against_a_class_host"],
             census["items_with_a_ledger_row_whose_geometry_is_absent"]))
    for m in census["SELF_HOST_MISSED"]:
        print("[IP] SELF_HOST_MISSED %-24s %5d objects of %s measured against "
              "%s %s" % (m["item"], m["own_objects"], m["declared_prefixes"],
                         m["measured_against_instead"], m["hosts"][:3]))

    recs = []
    for it in items:
        h, tier = HOSTS.hosts_for(it, names, self_px)
        hidx = [nidx[n] for n in h]
        # The SAME dimension the manifest's own px formula uses, so the two
        # numbers are comparable. For 42 items that is an IN-PLANE size (paint,
        # joints, stains, paving bays) rather than a height, and those are the
        # ones the foreshortening plane has to be applied to.
        hh = float(it.get("px_measured_dimension_m") or it.get("typical_height_m") or 0.1)
        flat = abs(hh - float(it.get("typical_height_m") or 0.0)) > 1e-9
        if not hidx:
            recs.append({"id": it["id"], "zone": it["zone"], "module": it["module"],
                         "height_m": hh, "instances": it["instances"],
                         "manifest_hero": it["hero"],
                         "manifest_nearest_camera_m": it["nearest_camera_m"],
                         "manifest_onscreen_px_4k": it["onscreen_px_4k"],
                         "host_tier": "UNMAPPED", "hosts": [], "n_hosts": 0,
                         "measured_as_self": False,
                         "measured": None})
            continue
        A = of_any[hidx].max(axis=0)
        S = of_sharp[hidx].max(axis=0)
        U = (of_flat if flat else of_usharp)[hidx].max(axis=0)
        D = of_depth[hidx]
        D = np.where(D > 0, D, np.inf).min(axis=0)
        # The manifest clamps at the frame height and flags overfills_frame.
        # Clamping here too keeps the two columns comparable; without it an
        # item reads 4,790 px against a 2,160 px frame and the ratio between
        # the two columns stops meaning anything.
        CLAMP = 2160.0
        ovf = bool((A * hh > CLAMP).any())

        vis = A > 0
        nvis = int(vis.sum())
        per_beat = {}
        for nm, f0, f1 in bounds:
            seg = A[f0 - 1:f1]
            Useg = U[f0 - 1:f1]
            if (seg > 0).any():
                per_beat[nm] = {"frames_visible": int((seg > 0).sum()),
                                "peak_px_4k": round(min(2160.0, float(seg.max() * hh)), 1),
                                "frames_at_300px": int((Useg * hh >= 300).sum()),
                                "frames_at_150px": int((Useg * hh >= 150).sum())}
        peak_f = int(np.argmax(A)) + 1 if nvis else 0
        sharp_f = int(np.argmax(S)) + 1 if (S > 0).any() else 0
        us_f = int(np.argmax(U)) + 1 if (U > 0).any() else 0
        recs.append({
            "id": it["id"], "zone": it["zone"], "module": it["module"],
            "height_m": hh, "instances": it["instances"],
            "manifest_hero": it["hero"],
            "manifest_nearest_camera_m": it["nearest_camera_m"],
            "manifest_onscreen_px_4k": it["onscreen_px_4k"],
            "host_tier": tier, "n_hosts": len(h),
            # THE FIELD A READER HAS TO CHECK BEFORE QUOTING A NUMBER. True =
            # this is the item. False = this is an UPPER BOUND on the item,
            # taken from whatever it sits on, and `mullion_intact` reporting
            # 1,053 px off forecourt paving while the showroom is not in the
            # world at all is what that is worth.
            "measured_as_self": tier == "SELF",
            "size_is_in_plane": flat,
            "hosts": h if len(h) <= 12 else h[:12] + [f"...+{len(h)-12} more"],
            "measured": {
                "frames_visible": nvis,
                "frames_visible_pct": round(100.0 * nvis / nframes, 2),
                "frames_sharp": int((S > 0).sum()),
                "frames_unoccluded_sharp": int((U > 0).sum()),
                # the load-bearing counts: how long is it BOTH big enough AND
                # sharp enough AND in front of whatever else is in the frame.
                # "frames_visible" alone is not a fidelity signal -- a zone-
                # mapped item is "visible" for most of the take because its
                # zone is, which says nothing about the item.
                "frames_at_300px": int((U * hh >= 300).sum()),
                "frames_at_150px": int((U * hh >= 150).sum()),
                "frames_at_60px": int((U * hh >= 60).sum()),
                "ever_unoccluded": bool((U > 0).any() or (of_usharp[hidx] > 0).any()),
                "min_depth_m": round(float(D.min()), 3) if np.isfinite(D).any() else None,
                "overfills_frame": ovf,
                "peak_px_4k": round(min(CLAMP, float(A.max() * hh)), 1),
                "peak_frame": peak_f,
                "peak_sharp_px_4k": round(min(CLAMP, float(S.max() * hh)), 1),
                "peak_sharp_frame": sharp_f,
                "peak_unocc_sharp_px_4k": round(min(CLAMP, float(U.max() * hh)), 1),
                "peak_unocc_sharp_frame": us_f,
                "beats": per_beat,
            },
        })

    # ---- the re-tier -----------------------------------------------------
    # Thresholds are the scope plan's own, restated so they can be argued with:
    #   HERO  >= 300 px, sharp, unoccluded, for at least 24 frames (1.0 s) in
    #         total across the take. Both halves matter: 300 px is what makes
    #         surface history visible, and one frame of it is a flash nobody
    #         reads.
    #   MID   >= 150 px sharp for at least 12 frames (0.5 s) -- silhouette,
    #         mass, correct value, genuine per-instance variation, no macro
    #         history.
    #   BULK  on screen, but never both big enough and sharp enough for long
    #         enough. Exists as tone. Built by the class-level system, not by a
    #         dedicated agent.
    #   NEVER not in frustum on any of the 2,978 frames -- provably not in the
    #         film, and the only tier that is a fact rather than a threshold.
    def tier_of(r):
        m = r["measured"]
        if m is None:
            return "UNMAPPED"
        if m["frames_visible"] == 0:
            return "NEVER"
        if m["frames_at_300px"] >= 24:
            return "HERO"
        if m["frames_at_150px"] >= 12:
            return "MID"
        return "BULK"

    for r in recs:
        r["proposed_tier"] = tier_of(r)

    counts = collections.Counter(r["proposed_tier"] for r in recs)
    host_counts = collections.Counter(r["host_tier"] for r in recs)
    print("[IP] proposed tiers:", dict(counts))
    print("[IP] host tiers:", dict(host_counts))

    # WHAT THIS RUN ACTUALLY READ, taken from the measurement rather than
    # asserted in prose. METHOD below is a fixed description of the technique
    # and used to name assembly2.blend and contract 1.0.1 inside itself; when
    # the tiering was re-derived against assembly6 those sentences became
    # false while the file still looked authoritative. A description of the
    # method may be static. The identity of the inputs may not.
    measured_against = {"NOTE": "generated from this run's own inputs; the prose "
                                "in METHOD describes the TECHNIQUE, not which "
                                "world or camera it was pointed at"}
    try:
        objs = json.load(open(a.objects))
        pc = objs.get("point_cloud", {})
        measured_against.update({
            "world_blend": pc.get("blend"),
            "point_cloud_cell_m": pc.get("cell_m"),
            "point_cloud_cap_per_object": pc.get("cap_per_object"),
            "point_cloud_objects_capped": "see keep_fraction in the points npz",
            "camera_path": objs.get("camera_path"),
            "points_file": objs.get("points_file"),
            "sweep_generated": objs.get("generated"),
            "frames": objs.get("frames"),
            "shutter_mode": objs.get("shutter_mode", "NOT RECORDED -- this sweep "
                                     "predates shutter_mode being written; check "
                                     "the 'shutter' array in the points npz"),
        })
    except Exception as exc:                                        # noqa: BLE001
        measured_against["UNAVAILABLE"] = (
            "could not read --objects (%s): the world and camera this run was "
            "pointed at are NOT recorded, which is defect #97. Re-run with "
            "--objects pointing at screen_presence.py's own output." % (exc,))

    json.dump({
        "generated": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
        "MEASURED_AGAINST": measured_against,
        "METHOD": METHOD,
        "source_npz": os.path.abspath(a.npz),
        "frames": nframes,
        "host_patterns_matching_nothing": dead,
        "items_with_no_host": unmapped,
        # BOTH OF THE TWO ABOVE WERE [] ON THE 08-04 RUN, on a file where 435
        # of 435 items were measured against the wrong geometry. They are not
        # wrong; they answer a question nobody was failing. The census below is
        # the one that answers the question that was failing.
        "self_host_census": census,
        "resolution_mode": ("PRE_R2_1385_CONTROL (--no-self-hosts)"
                            if a.no_self_hosts else "SELF_PREFERRED"),
        "tier_counts": dict(counts),
        "host_tier_counts": dict(host_counts),
        "items": recs,
    }, open(a.out, "w"), indent=1)
    print(f"[IP] wrote {a.out}")

    # ---- agent counts, by (module, name-family) collapse ------------------
    # The scope plan's collapse unit: (module, name-family). One agent owns the
    # family and emits its children, because the children ARE the parent at a
    # different scale -- armco_splice_bolt, armco_reflector, armco_spacer_block
    # and armco_terminal all live on the beam armco_w_beam already emits, and
    # four agents that cannot see each other produce four unrelated rusts on
    # one barrier.
    FAM_ALIAS = {"catch": "catch_fence", "pit": None, "la": "la_passerelle",
                 "tyre": None, "grass": "grass_clump", "team": "team_truck"}

    def family(r):
        tok = r["id"].split("_")
        f = tok[0]
        al = FAM_ALIAS.get(f, f)
        if al is None:                       # ambiguous head -- keep two tokens
            al = "_".join(tok[:2])
        return (r["module"], al)

    groups = collections.defaultdict(list)
    for r in recs:
        groups[(r["proposed_tier"], family(r))].append(r["id"])
    by_tier = collections.defaultdict(list)
    for (t, fam), ids in groups.items():
        by_tier[t].append({"family": list(fam), "items": sorted(ids)})
    plan = {t: {"items": counts[t], "groups": len(by_tier[t])} for t in counts}
    json.dump({"generated": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
               "tier_counts": dict(counts),
               "groups_per_tier": plan,
               "groups": {t: sorted(v, key=lambda g: g["family"]) for t, v in by_tier.items()}},
              open(a.tiers, "w"), indent=1)
    print(f"[IP] wrote {a.tiers}: " + json.dumps(plan))

    # ---- the verdict -----------------------------------------------------
    # This is the instrument R2-1277 found missing. It is deliberately NOT
    # "did the resolver assign SELF" -- that would be the fix marking its own
    # homework. It asks the ledger and the name list directly: is there an
    # item whose own geometry is in this world and which this run measured
    # against something else. On the 08-04 inputs, unfixed, that is 4. Fixed,
    # on the same npz, it is 0.
    n = census["SELF_HOST_MISSED_n"]
    if n and not a.allow_self_host_missed:
        print("[IP] %d item(s) have their own geometry in this world and were "
              "measured against a class host anyway. Every tier verdict on "
              "them is an upper bound on a thing that is standing right there."
              % n)
        return gate_exit.verdict("ITEM_PRESENCE_SELF_HOST_MISSED")
    return gate_exit.verdict("ITEM_PRESENCE_OK")


METHOD = {
    "VALIDATION": {
        "1_against_an_independent_instrument":
            "The camera model here reproduces the aim gate inside "
            "anim/build_camera_rig.py -- written separately, for a different "
            "purpose -- to 0.004 deg. Beat 6's declared fixed subject "
            "(15.0, 0.0, 3.1) comes out at a worst 0.0804 deg from the "
            "camera's -Z over frames 2859-2978 against the rig's own reported "
            "0.0765 deg. Controls: assuming the camera looks down +Z gives "
            "180.0 deg, -Y or +X gives 90.0 deg, so the test can fail.",
        "2_against_a_camera_known_to_be_bad":
            "The whole sweep was re-run against a POSITIVE CONTROL: the same "
            "rig with its orientation frozen at frame 754, which reconstructs "
            "the pre-#34 defect (no rotation key for 74.7 % of the film). "
            "192 of 560 objects lose ALL sharp presence and 321 lose at least "
            "half their peak size. The objects the film is declared to be "
            "about collapse: BR_Transit_TyreWall 358 -> 0 px/m, "
            "BR_Transit_Portal 77 -> 0, ARCH_LaPasserelle 47 -> 0, "
            "ARCH_Grandstand_03_PRINCIPALE 12.4 -> 0, ARCH_PontPlongee "
            "179.6 -> 8.5, SURF_Kerb_T4_in0 151.2 -> 12.2. "
            "NOTE, because it is the useful part: the FIRST control statistic "
            "tried was total point-frames over the whole world, and it gave "
            "77.6 % and declared the instrument broken. It was the statistic "
            "that was broken -- a camera flying the circuit with a frozen "
            "stare still has ground in front of it, and a frozen stare at "
            "slow-moving terrain is SHARPER than a tracking one, so the "
            "control's total sharp frames are 162 % of the subject's. "
            "Aggregate world coverage cannot tell a camera pointed at the film "
            "from one pointed at a field.",
        "3_against_a_real_render":
            "tools/idpass_emissive.py gives every object a unique flat "
            "emission colour and renders the scene in Cycles at 1 sample with "
            "a 0.01 px filter, so the combined buffer IS a per-object ID pass "
            "with the renderer doing the frustum test, the occlusion and the "
            "coverage. Run on world/verify_surface.blend (58 real world "
            "objects, the same camera path) over 8 frames spread across the "
            "take: 464 object-frames, 94.2 % agreement. All 27 disagreements "
            "are in ONE direction -- this measurement says in-frame where "
            "Cycles renders no pixel -- and every one of them is an object "
            "under 18 px per metre, i.e. sub-pixel at the 960x540 test "
            "resolution. Cycles never rendered an object this measurement said "
            "was off screen: 0 misses in the direction that would matter.",
        "4_by_eye":
            "WITHDRAWN 2026-08-03 -- THE FRAMES WERE 3.628 STOPS OVER. This key "
            "used to say that eight frames rendered at 1280x720 from "
            "world/verify_world.blend (300, 660, 950, 1100, 2280, 2450, 2700, "
            "2950) 'confirm what the numbers say', naming grass filling the "
            "doppler hover at 2280 and 'the trackside hoardings smeared to "
            "transparency' at 2700. Those frames were built by "
            "tools/build_verify_scene.py before it applied a grade, on assembly "
            "blends that carry view exposure +0.000, against the film's MEASURED "
            "-3.628 (world/film_exposure.py). Their mean luminance is 0.714-0.893. "
            "MEASURED on the matching pair for the same rig: the SAME frame that "
            "clips 0.000 %% of pixels at -3.628 (render/exposure_beats/cal_960.png, "
            "mean 0.0166, p99 0.0456) clips 23.6 %% of pixels with a saturated "
            "channel at +0.000 (render/shutter_ab/*_f960.png, mean 0.494, p99 "
            "0.9901). 'Smeared to transparency' is exactly the read that 3.6 "
            "stops of over-exposure fabricates. THIS CONFIRMATION IS UNMEASURED, "
            "NOT REFUTED: the numbers may well be right, but no picture has yet "
            "been looked at that could confirm them. To restore it, rebuild the "
            "rig (build_verify_scene.py now applies and asserts the grade) and "
            "re-render those eight frames. Frames 1145-1882 could not be checked "
            "this way in any case: verify_world.blend predates the current rig "
            "and its camera differs there by up to 40.4 m.",
    },
    "what": "Peak on-screen size, frames visible, motion smear and occlusion for "
            "every manifest item, measured against the camera path emitted by "
            "anim/build_camera_rig.py and the surfaces of an assembled world. "
            "WHICH world and WHICH camera path this particular run read is in "
            "the MEASURED_AGAINST block at the top of the output, never here: "
            "this key used to name assembly2.blend, and it went on naming it "
            "after the tiering had been re-derived against assembly6.",
    "camera": "Per frame: position, orientation and EVALUATED focal length from "
              "the rig's own sampled path. Blender convention, -Z forward, +Y up, "
              "sensor fit AUTO on 3840x2160 so 36 mm is the horizontal dimension. "
              "Pixel scale s = 3840 * lens_mm / 36; size = height_m * s / depth, "
              "where depth is -Z in camera space (pinhole depth), NOT the radial "
              "distance the manifest's nearest_camera_m used.",
    "frustum": "A point counts only when its projection lands inside 3840x2160 "
               "with depth > 0. This is the correction that matters: closest "
               "approach for anything the camera PASSES is abeam, which at 35 mm "
               "is 63 degrees outside the frame.",
    "smear": "MEASURED, not modelled. The same world point is projected through "
             "frame f's camera and frame f+1's camera; the pixel displacement is "
             "what a Cycles Vector pass reports. Multiplied by the shutter, which "
             "since R2-037 is a FLAT 180 degrees -- 0.5 of a frame -- for the "
             "whole take: build_camera_rig.py used to key "
             "0.5 * world_time_scale[f], which during beat 3's speed ramp fell to "
             "0.0769 and left beat 3's static geometry 6.5x too crisp, because "
             "the world-time slowdown is ALREADY baked into the per-film-frame "
             "animation and scaling the shutter applied it a second time. The rig "
             "keys a flat 180-degree shutter for the whole take since R2-037 "
             "(there is NO --shutter-mode flag; that citation was a phantom). "
             "This measurement is run with screen_presence.py --uniform-shutter to "
             "match. SHARP means smear <= 6 px of the 4K frame, which is "
             "tools/item_gate.py's own hero resolve threshold.",
    "size_convention": "The dimension used is the manifest's own "
                       "px_measured_dimension_m, so the measured number is "
                       "directly comparable with its onscreen_px_4k. For 42 "
                       "items that dimension is IN PLANE (paint, joints, "
                       "stains, paving bays), and for those the measurement "
                       "multiplies by the foreshortening |n . vhat| with n = +Z "
                       "-- the angle the surface is actually seen at. The "
                       "manifest applies its formula to an in-plane dimension "
                       "with no regard for viewing angle, which for a road "
                       "under a camera 1.9 m up is the difference between a 1 m "
                       "paving bay and a 5 cm one.",
    "tiers": "HERO = >=300 px, sharp, unoccluded, on >=24 frames (1.0 s) in "
             "total. MID = >=150 px on >=12 frames. BULK = on screen but never "
             "both big and sharp for long enough. NEVER = not in frustum on any "
             "of the 2,978 frames. Only NEVER is a fact rather than a threshold.",
    "occlusion": "A depth buffer rasterised from the point cloud itself at "
                 "960x540 and compared per point. The cloud is a surface sample "
                 "at 1 m spacing, so the buffer has holes and a hole can only "
                 "let a hidden point through as visible. The occlusion figure is "
                 "a LOWER BOUND: ever_unoccluded == false is proof, true is not.",
    "items_are_not_objects": "The assembled world has 468 evaluated objects and "
                             "28,313 vegetation instances and NONE of them is a "
                             "manifest item -- 407 of the 435 items have no module "
                             "yet, and the rest are features distributed over "
                             "class-level placement geometry. Each item is mapped "
                             "to a HOST SET by the explicit table in "
                             "tools/item_hosts.py and inherits the best moment any "
                             "host surface ever has. That is an UPPER BOUND on the "
                             "item: it cannot be seen better than what it sits on. "
                             "host_tier records whether the mapping was NAMED "
                             "(specific objects) or ZONE (the whole zone).",
    "limitations": [
        "These are the positions of the world AS IT EXISTED IN THE BLEND NAMED IN "
        "MEASURED_AGAINST, not as it will be after the next rebuild of the "
        "modules. Barrier, catch-fence and runoff items are the ones a contract "
        "change can move: between contract 1.0.1 (assembly2) and 1.2.1 "
        "(assembly6) barrier_offset moved by up to 52 m and 247 of 497 shared "
        "objects moved by more than 1 cm. render/world/assembly/r2/SHIPPING.md is "
        "the authority on which assembly is current, and it records that "
        "assembly5 and assembly6 have BIT-IDENTICAL module summaries while "
        "differing by 3.19 m of Beat-4 wall -- so a summary that does not change "
        "is not evidence that geometry did not move, and the sha256 in "
        "MEASURED_AGAINST is what actually distinguishes them.",
        "People, crowd and 407 of the 435 items are NOT BUILT. Their host is the "
        "ground or structure they will stand on.",
        "The point cloud is a 1 m voxel sample of evaluated mesh vertices, capped "
        "at 250,000 cells per object with the kept fraction recorded. Sub-metre "
        "features are represented by the surface they sit on.",
        "Vegetation is one point per instance origin (28,313 of them). Particle "
        "and geometry-node children inside those objects -- the 1.4 M grass "
        "clumps -- are not enumerated individually.",
        "The car is not in this scene, so it neither occludes nor is measured.",
        "The 34 vegetation SCATTER HOSTS (VEG_grass_fescue_F, VEG_shrub_bramble_L1, "
        "VEG_grit_chip and friends) are sampled from their BASE meshes -- 4.7 M "
        "vertices which are the clump POSITIONS. Their evaluated form is those "
        "positions with a clump instanced onto each, and that is where the "
        "census's 1.21 billion triangles are. So a grass clump's SIZE is its own "
        "declared height at the measured distance, not a measured silhouette.",
        "The point cloud is voxelised at 1 m, so every distance in this file "
        "carries about +-0.9 m of quantisation. That matters only for the very "
        "closest approaches; it does not affect a 0.8 m vs 3.8 m disagreement.",
        "A CROSS-CHECK the reader should know did not complete: a real Cycles "
        "IndexOB + Vector pass over the whole 2,978-frame take was designed and "
        "attempted but is not achievable with the infrastructure available. The "
        "render broker exposes no custom-pass option, and `rq exec` -- which "
        "does run arbitrary Blender -- hard-kills a job at 3,600 s and stages "
        "its inputs through a single `zstd -19` ssh pipe that gives up at "
        "1,800 s. assembly2.blend is 4.19 GB of largely incompressible float "
        "data and reached 57 % of that window. What was done instead: the "
        "measurement was validated against the camera rig's own independently "
        "written aim gate (agreement 0.004 deg), against a POSITIVE CONTROL "
        "camera carrying a known defect, and against eight frames rendered on "
        "the GPU and looked at.",
    ],
}



# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised: `blender -b -P x.py`
    # prints the traceback and exits 0, MEASURED on this box. A gate that
    # crashed was indistinguishable from one that passed. guard() makes an
    # uncaught exception a status 2 and passes any real verdict through
    # unchanged. One shared helper, not N copies -- see tools/gate_exit.py.
    gate_exit.guard(main, tool="item_presence")
