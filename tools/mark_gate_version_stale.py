"""MARK a gate report that was written by an older, weaker gate.

    python3 tools/mark_gate_version_stale.py            # dry run
    python3 tools/mark_gate_version_stale.py --apply

THE PROBLEM
===========
`tools/item_gate.py` was rewritten on 2026-07-29. Before the rewrite it ran
FOUR checks. It now runs EIGHT. The four it gained are the four that look at
the rendered surface rather than at the node graph:

    witness_frame_valid
    surface_microstructure
    relief_reads_as_lip_and_shade
    silhouette_departs_from_analytic

Every `ITEM_ACCEPTED` written before the rewrite is therefore stale BY
CONSTRUCTION. It is not "an old pass that is probably still fine": it is a pass
awarded by an instrument that could not perform half of the current test, and
nothing on the face of the file says so. A reader who opens
`render/items/timing_stand/gate.json`, sees ITEM_ACCEPTED, and moves on has been
misled by an artefact that is telling the literal truth about a question nobody
is asking any more.

WHY NOT JUST RE-GATE?
=====================
Re-gating is the right answer and this tool is not a substitute for it. It costs
one 4K/512-sample witness render per module on the rented 5090 -- which is DOWN
as of this run -- plus a full staging pass over blends up to 240 MB. The
marking costs milliseconds and can be done now. Marked, a stale pass cannot be
misread; unmarked, it will be, because it already was.

HOW BADLY DOES THE VERDICT ACTUALLY MOVE?
=========================================
Measured, not guessed. Thirteen modules held a 4-check ITEM_ACCEPTED and were
re-gated under the 8-check gate on 2026-08-02:

    SIX of the thirteen flipped to ITEM_REJECTED  (46 %)
    armco_w_beam, crew_fireproof_overall, grandstand_riser_unit,
    kerb_precast_unit, marshal_post_column, team_truck_trailer

and every one of them failed on `relief_reads_as_lip_and_shade` or was
un-measurable on it -- i.e. on one of the four checks the old gate did not have.

READ THAT NUMBER CAREFULLY. Those thirteen were also REBUILT between the two
gate runs (R2-038: dead bump stacks repaired, 111 stages -> 0). So 46 % mixes
two changes, and the rebuild was an IMPROVEMENT. The modules marked by this
tool have NOT been rebuilt. 46 % is therefore a floor, not an estimate.

WHAT THIS TOOL DOES TO THE FILE
===============================
It edits `gate.json` in place, and it is deliberate about which key it touches:

    result   ->  "GATE_VERSION_STALE"
    the original verdict is preserved verbatim under
    "result_of_4_check_gate_<date>"

because `result` is the key that tooling and readers actually consult, and a
truthful value there is worth more than a truthful footnote beside a misleading
one. Nothing else in the file is altered, and a byte-identical copy of the file
as it was written is saved next to it before anything is changed.
"""
import argparse
import json
import os
import shutil
import sys
import time

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS = os.path.join(R2, "render", "items")

CURRENT_CHECKS = [
    "no_external_assets", "material_depth", "geometry_resolves_at_distance",
    "per_instance_variation", "witness_frame_valid", "surface_microstructure",
    "relief_reads_as_lip_and_shade", "silhouette_departs_from_analytic",
]

# Measured on 2026-08-02, see the module docstring.
FLIPPED = ["armco_w_beam", "crew_fireproof_overall", "grandstand_riser_unit",
           "kerb_precast_unit", "marshal_post_column", "team_truck_trailer"]
FLIP_DENOM = 13


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true")
    p.add_argument("--min-checks", type=int, default=len(CURRENT_CHECKS))
    a = p.parse_args(argv)

    marked, skipped = [], []
    for m in sorted(os.listdir(ITEMS)):
        gj = os.path.join(ITEMS, m, "gate.json")
        if not os.path.isfile(gj):
            continue
        try:
            rep = json.load(open(gj))
        except Exception as e:
            skipped.append((m, "unreadable: %s" % e))
            continue
        checks = rep.get("checks") or {}
        if rep.get("result") == "GATE_VERSION_STALE":
            skipped.append((m, "already marked"))
            continue
        if len(checks) >= a.min_checks:
            skipped.append((m, "%d checks -- current" % len(checks)))
            continue

        day = time.strftime("%Y_%m_%d",
                            time.localtime(os.stat(gj).st_mtime))
        missing = [c for c in CURRENT_CHECKS if c not in checks]
        orig_key = "result_of_%d_check_gate_%s" % (len(checks), day)
        orig = rep.get("result")

        out = {"REPORT_STATUS": {
            "status": "GATE_VERSION_STALE",
            "one_line": ("this verdict was awarded by a %d-check gate; the "
                         "current gate runs %d, and this item has NOT been "
                         "measured against the other %d"
                         % (len(checks), len(CURRENT_CHECKS), len(missing))),
            "written_at": time.strftime(
                "%Y-%m-%dT%H:%M:%S", time.localtime(os.stat(gj).st_mtime)),
            "checks_it_ran": sorted(checks),
            "checks_it_COULD_NOT_RUN": missing,
            "why_that_matters": (
                "the missing checks are the ones that look at the RENDERED "
                "SURFACE rather than at the node graph. A node count cannot "
                "see a dead socket: R2-038 wired a whole bump chain into the "
                "wrong Principled input and passed a 4-check gate for four "
                "days while producing no relief at all."),
            "measured_flip_rate": (
                "%d of %d modules that held a 4-check ITEM_ACCEPTED flipped to "
                "ITEM_REJECTED when re-gated under the 8-check gate on "
                "2026-08-02 (%.0f %%): %s. Those modules had ALSO been repaired "
                "in between, so this is a FLOOR for an unrepaired module, not "
                "an estimate."
                % (len(FLIPPED), FLIP_DENOM, 100.0 * len(FLIPPED) / FLIP_DENOM,
                   ", ".join(FLIPPED))),
            "what_is_owed": (
                "a re-gate: one 4K/512-sample witness render per module on the "
                "5090 plus a staging pass. Until then this file states what it "
                "measured and does not state that the item is good."),
            "original_verdict_preserved_as": orig_key,
            "untouched_copy": "_superseded_gate_version/gate.json.as_written",
            "marked_by": os.path.abspath(__file__),
            "marked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }}
        # `result` first among the originals so a reader hits it early, then
        # everything else verbatim and in its original order.
        out["result"] = "GATE_VERSION_STALE"
        out[orig_key] = orig
        for k, v in rep.items():
            if k not in ("result", "REPORT_STATUS"):
                out[k] = v

        marked.append((m, orig, len(checks)))
        if a.apply:
            sup = os.path.join(ITEMS, m, "_superseded_gate_version")
            os.makedirs(sup, exist_ok=True)
            shutil.copy2(gj, os.path.join(sup, "gate.json.as_written"))
            with open(gj, "w") as fh:
                json.dump(out, fh, indent=1)

    for m, orig, n in marked:
        print("MARK   %-28s %-16s (%d checks)" % (m, orig, n))
    for m, why in skipped:
        print("skip   %-28s %s" % (m, why))
    print("\n%s -- %d marked, %d skipped"
          % ("APPLIED" if a.apply else "DRY RUN (nothing changed)",
             len(marked), len(skipped)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
