#!/usr/bin/env python3
"""CONTROLS FOR tools/report_repro.py.  Defect #97.

Four verdicts, and every one of them is driven by a case constructed to
produce it.  A differ that only ever emits ATTRIBUTED would look perfectly
healthy on real data and would be useless, because the two verdicts that
matter -- NON_REPRODUCIBLE and INSENSITIVE -- are precisely the ones that
never arise unless something is wrong.  So each is manufactured here.

The load-bearing checks are the vacuity ones:

  V1  a change buried in a nested float MUST be seen.  If `_body()` were
      broken -- returning a constant, or comparing only top-level keys --
      every pair on earth would come back REPRODUCED and this file would
      pass without noticing.  So the detector is fed a difference it must
      find, at the bottom of a nested structure.
  V2  the same numbers in a different key order MUST come back REPRODUCED.
      A differ that calls key order a regression gets ignored within a day,
      and an ignored guard is an absent guard.
"""
import os
import sys
import json
import shutil
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import provenance as P                                            # noqa: E402
import report_repro as RR                                         # noqa: E402

RESULTS = []


def record(name, want, got, detail=""):
    ok = (want == got)
    RESULTS.append((name, want, got, ok))
    print("  %-4s %-56s want=%-17s got=%-17s %s"
          % ("PASS" if ok else "FAIL", name, want, got, detail))
    return ok


def body(closest=7.6054, obj="ARCH_RetainEdge", extra=None):
    """A stand-in placement report body, shaped like the real one."""
    d = {"violations": [], "total": 0,
         "closest_approach_m": {
             "road_corridor": {"object": obj, "clearance_m": closest,
                               "at_world": [1.0, 2.0, 3.0]},
             "car_path": {"object": "BR_Verge_R", "clearance_m": 0.648,
                          "at_world": [4.0, 5.0, 6.0]},
             "camera_path": {"object": None, "clearance_m": None}},
         "method": "analytic signed distance to keep-out volume"}
    if extra:
        d.update(extra)
    return d


def run():
    tmp = tempfile.mkdtemp(prefix="report-repro-selftest-")
    try:
        tele = os.path.join(tmp, "telemetry.csv")
        cam = os.path.join(tmp, "camera_rig_path.json")
        blend = os.path.join(tmp, "world.blend")
        for p, txt in ((tele, "s,x,y\n0,0,0\n"), (cam, '{"frames": 2978}\n'),
                       (blend, "BLENDER-v502" + "x" * 4096)):
            open(p, "w").write(txt)

        def stamped(path, rep, inputs=None):
            rep = dict(rep)
            rep[P.STAMP_KEY] = P.stamp(
                tool_file=os.path.join(HERE, "placement_gate.py"),
                tool_version="placement_gate; spec r7",
                inputs=inputs or [("blend", blend), ("telemetry", tele),
                                  ("camera_path", cam)])
            json.dump(rep, open(path, "w"), indent=1)
            return path

        print("REPORT-REPRO SELFTEST   (defect #97)")
        print("scratch: %s" % tmp)
        print("")

        # -- N1 negative control -------------------------------------------
        a = stamped(os.path.join(tmp, "a.json"), body())
        b = stamped(os.path.join(tmp, "b.json"), body())
        record("N1 identical inputs, identical results", "REPRODUCED",
               RR.compare(a, b)["verdict"])

        # -- P1 THE ALARM --------------------------------------------------
        b2 = stamped(os.path.join(tmp, "b2.json"), body(closest=4.608,
                                                        obj="BR_Concrete_L12"))
        r = RR.compare(a, b2)
        record("P1 same inputs, closest approach moved 7.6054 -> 4.608",
               "NON_REPRODUCIBLE", r["verdict"])
        record("P1b and the moved volume is named", True,
               any(c["volume"] == "road_corridor"
                   for c in r["closest_approach_delta"]),
               str(r["closest_approach_delta"][:1]))

        # -- P2 attribution ------------------------------------------------
        open(tele, "w").write("s,x,y\n0,0,0\n1,1,1\n")     # telemetry rebuilt
        b3 = stamped(os.path.join(tmp, "b3.json"), body(closest=4.608,
                                                        obj="BR_Concrete_L12"))
        r = RR.compare(a, b3)
        record("P2 telemetry moved AND results moved", "ATTRIBUTED", r["verdict"])
        record("P2b it names telemetry and only telemetry", ["telemetry"],
               [m["role"] for m in r["moved_inputs"]])

        # -- P3 insensitive ------------------------------------------------
        b4 = stamped(os.path.join(tmp, "b4.json"), body())   # same numbers as a
        r = RR.compare(a, b4)
        record("P3 telemetry moved, not one number changed", "INSENSITIVE",
               r["verdict"])

        # -- P5 the undeclared-code channel --------------------------------
        # world_contract.py is stamped by provenance BY DEFAULT, never on a
        # command line.  It is the input most able to move an answer while
        # nobody is looking, so it gets its own control.
        fake_contract = os.path.join(tmp, "world_contract.py")
        open(fake_contract, "w").write('__version__ = "1.2.1"\n')
        s_a = P.stamp(tool_file=os.path.join(HERE, "placement_gate.py"),
                      inputs=[("blend", blend)],
                      also_hash=[("world_contract", fake_contract)])
        ra = body()
        ra[P.STAMP_KEY] = s_a
        pa = os.path.join(tmp, "ca.json")
        json.dump(ra, open(pa, "w"), indent=1)
        open(fake_contract, "w").write('__version__ = "1.2.1"\nHALF_WIDTH=7.5\n')
        s_b = P.stamp(tool_file=os.path.join(HERE, "placement_gate.py"),
                      inputs=[("blend", blend)],
                      also_hash=[("world_contract", fake_contract)])
        rb = body(closest=4.608)
        rb[P.STAMP_KEY] = s_b
        pb = os.path.join(tmp, "cb.json")
        json.dump(rb, open(pb, "w"), indent=1)
        r = RR.compare(pa, pb)
        record("P5 contract changed with the SAME declared version string",
               "ATTRIBUTED", r["verdict"])
        record("P5b attributed to code:world_contract, not to the version label",
               True, any(m["role"] == "code:world_contract"
                         for m in r["moved_inputs"]),
               "moved=%s" % [m["role"] for m in r["moved_inputs"]])

        # -- P6 role mismatch ----------------------------------------------
        b5 = stamped(os.path.join(tmp, "b5.json"), body(closest=4.608),
                     inputs=[("blend", blend), ("telemetry", tele),
                             ("camera_path", cam), ("beat_sheet", cam)])
        r = RR.compare(a, b5)
        record("P6 one run declares an input the other never did", "ATTRIBUTED",
               r["verdict"])
        record("P6b the undeclared role is called out", ["beat_sheet"],
               [m["role"] for m in r["role_mismatch"]])

        # -- P4 unstamped ---------------------------------------------------
        bare = os.path.join(tmp, "bare.json")
        json.dump(body(), open(bare, "w"), indent=1)
        record("P4 one report unstamped", "UNCITEABLE",
               RR.compare(a, bare)["verdict"])

        # -- V1 VACUITY: a nested change must be SEEN -----------------------
        deep_a = stamped(os.path.join(tmp, "d1.json"),
                         body(extra={"nest": {"a": {"b": [1, 2, 3.0000001]}}}))
        deep_b = stamped(os.path.join(tmp, "d2.json"),
                         body(extra={"nest": {"a": {"b": [1, 2, 3.0000002]}}}))
        record("V1 a change 4 levels down IS detected (detector not blind)",
               True, RR.compare(deep_a, deep_b)["results_differ"])

        # -- V2 VACUITY: key order is NOT a regression ----------------------
        ord_a = body()
        ord_b = {k: ord_a[k] for k in reversed(list(ord_a.keys()))}
        pa2 = stamped(os.path.join(tmp, "o1.json"), ord_a)
        pb2 = stamped(os.path.join(tmp, "o2.json"), ord_b)
        record("V2 same numbers in a different key order", "REPRODUCED",
               RR.compare(pa2, pb2)["verdict"])

        # -- R1/R2 the consumer-side gate ------------------------------------
        try:
            RR.require(bare)
            got = "returned"
        except SystemExit as e:
            got = "SystemExit(%s)" % e.code
        record("R1 require() on an unstamped report", "SystemExit(1)", got)
        try:
            RR.require(a)
            got = "returned"
        except SystemExit as e:
            got = "SystemExit(%s)" % e.code
        record("R2 require() on a stamped report", "returned", got)
        try:
            RR.require(bare, allow_unstamped_reason="declared control")
            got = "returned"
        except SystemExit as e:
            got = "SystemExit(%s)" % e.code
        record("R3 require() with an explicit declared reason", "returned", got)

        print("")
        failed = [x for x in RESULTS if not x[3]]
        for name, want, got, _ in failed:
            print("  FAILED: %s  want=%r got=%r" % (name, want, got))
        print(">> STAGE RESULT: %s (%d failures of %d checks)"
              % ("OK" if not failed else "FAIL", len(failed), len(RESULTS)))
        return 0 if not failed else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(run())
