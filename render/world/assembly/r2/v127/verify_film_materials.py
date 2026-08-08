"""R2-2101 -- DID R2-2041's TWO FIXES SURVIVE INTO THE FILM?

    /opt/blender-5.2.0-linux-x64/blender -b <film.blend> --factory-startup \
        -noaudio -P render/world/assembly/r2/v127/verify_film_materials.py \
        -- --json <out.json>

R2-2041 verified the carbon twill in the CAR blend and the tyre deposit in the
ASSEMBLY blend.  Neither had ever been read back out of a FILM, and "the source
is correct" has been the trap four times on this project.  The bar:

    CarbonFibre  Mapping.Scale     62.8319   and on its `.001` twin
    concrete     `Traffic Passes`  1000.0000
    node groups  exactly TWO `TDP_*`         four would mean N = 1000 leaked
                                             onto the showroom surfaces

WRITTEN AGAINST THE THREE WAYS THIS BLOCK'S OWN INSTRUMENTS FAILED (R2-2041,
"the instrument failed three times in this block, in the direction that
flatters"), because the next instrument is the likeliest thing to be wrong:

  1. NO `is` ON A `bpy_struct`.  Two reads of the same node return two
     different Python wrappers, so identity is ALWAYS False and the test fails
     on correctly wired material.  Everything here compares by NAME.
  2. `Mapping.Scale` IS A VECTOR.  Reading it as a float raised `ValueError`,
     Blender exited 0, and six PASS lines printed with no verdict at all.  It
     is read as three components here, and the whole run is wrapped so that an
     exception still prints a `>> STAGE RESULT:` line.  A crash must be a FAIL,
     never a silence.
  3. TWO `TDP_*` GROUPS IS THE PASS, NOT FOUR.  An instrument that demanded
     four reported FAIL on a correct film.  Two is right, and that two is right
     is itself the evidence N = 1000 did not reach the deck and the floor.

THE TWO-VERDICT TRAP.  This prints exactly one `>> STAGE RESULT:` line, at the
end, and nothing else in the file prints that token.
"""
import json
import os
import sys

WANT_SCALE = 62.8319
WANT_PASSES = 1000.0
WANT_TDP_GROUPS = 2

rows = []
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
out_json = argv[argv.index("--json") + 1] if "--json" in argv else None


def chk(name, got, want, tol=None, note=""):
    if tol is None:
        ok = (got == want)
    else:
        try:
            ok = abs(float(got) - float(want)) <= tol
        except (TypeError, ValueError):
            ok = False
    rows.append({"check": name, "want": want, "got": got, "ok": bool(ok),
                 "note": note})
    print("[%s] %-46s want %-12s got %-16s %s"
          % ("PASS" if ok else "FAIL", name, want, got, note))
    return ok


def vec3(sock):
    """`Mapping.Scale` is a Vector. Read it as three floats, never as one.

    R2-2041's `verify_carbon.py` did `float(sock.default_value)` here, raised
    `ValueError`, and Blender exited 0 with no verdict printed.
    """
    v = sock.default_value
    try:
        return [round(float(c), 4) for c in v]
    except TypeError:
        return [round(float(v), 4)]


def main():
    import bpy
    print("file: %s (%.1f MB)"
          % (bpy.data.filepath,
             os.path.getsize(bpy.data.filepath) / 1e6 if bpy.data.filepath
             else 0.0))

    # ---- CARBON ---------------------------------------------------------- #
    # The twin is not incidental: R2-1146 recorded that ten car materials exist
    # TWICE in the film as `.001` copies, so a fix verified on one of them is
    # verified on half the car.  Both are named here and BOTH must be found --
    # a missing twin is reported, never skipped, because "the check did not run"
    # and "the check passed" must not look the same.
    carbon = [m for m in bpy.data.materials
              if m.name == "CarbonFibre" or m.name.startswith("CarbonFibre.")]
    chk("CarbonFibre: material present", len(carbon) >= 1, True)
    print("   CarbonFibre datablocks in the film: %s"
          % sorted(m.name for m in carbon))
    for mat in sorted(carbon, key=lambda m: m.name):
        if mat.node_tree is None:
            chk("%s: has a node tree" % mat.name, False, True)
            continue
        maps = [n for n in mat.node_tree.nodes
                if n.type == "MAPPING" or n.bl_idname == "ShaderNodeMapping"]
        chk("%s: Mapping node count" % mat.name, len(maps), 3,
            note="three Mapping nodes feed the six TexWave")
        for n in sorted(maps, key=lambda n: n.name):
            s = n.inputs.get("Scale")
            if s is None:
                chk("%s: %s has a Scale socket" % (mat.name, n.name),
                    False, True)
                continue
            v = vec3(s)
            chk("%s: %s.Scale" % (mat.name, n.name), v[0], WANT_SCALE, 1e-3,
                note="vector %s" % v)
            if len(v) == 3 and (abs(v[1] - v[0]) > 1e-3
                                or abs(v[2] - v[0]) > 1e-3):
                chk("%s: %s.Scale is uniform" % (mat.name, n.name),
                    False, True, note="components differ: %s" % v)
        # the six TexWave must still be at Scale 1.0 -- R2-2041 moved the
        # pitch on the Mapping nodes and NOT on the waves, and a fix that
        # also moved the waves would double the change
        waves = [n for n in mat.node_tree.nodes if n.type == "TEX_WAVE"]
        chk("%s: TexWave count" % mat.name, len(waves), 6)
        offs = [n.name for n in waves
                if abs(float(n.inputs["Scale"].default_value) - 1.0) > 1e-4]
        chk("%s: every TexWave still at Scale 1.0" % mat.name, offs, [],
            note="moved: %s" % offs if offs else "")

    # ---- RUBBER ---------------------------------------------------------- #
    # `Traffic Passes` is an input on the deposit group.  Find it by NAME
    # wherever it is exposed -- on a group node's input, or as the group's own
    # interface default -- and report every distinct value found, because two
    # different values in one film is the leak this check exists to see.
    found = {}
    for ng in bpy.data.node_groups:
        for n in ng.nodes:
            s = n.inputs.get("Traffic Passes") if hasattr(n, "inputs") else None
            if s is not None and not s.is_linked:
                found.setdefault(round(float(s.default_value), 4), []).append(
                    "%s/%s" % (ng.name, n.name))
    for mat in bpy.data.materials:
        if mat.node_tree is None:
            continue
        for n in mat.node_tree.nodes:
            s = n.inputs.get("Traffic Passes") if hasattr(n, "inputs") else None
            if s is not None and not s.is_linked:
                found.setdefault(round(float(s.default_value), 4), []).append(
                    "%s/%s" % (mat.name, n.name))
    print("   'Traffic Passes' values found: %s"
          % json.dumps({str(k): v[:4] for k, v in sorted(found.items())}))
    chk("Traffic Passes: distinct values", sorted(found), [WANT_PASSES],
        note="more than one value means the deposit is inconsistent")

    tdp = sorted(g.name for g in bpy.data.node_groups
                 if g.name.startswith("TDP_"))
    print("   TDP_* node groups: %s" % tdp)
    chk("TDP_* node group count", len(tdp), WANT_TDP_GROUPS,
        note="FOUR would mean N=1000 leaked to the showroom surfaces")

    # ---- THE TRAP R2-2041 NAMED ------------------------------------------ #
    # `LiveryPaint.Metallic` reads its default 0.62 forever because the socket
    # is LINKED through a MULTIPLY of 0.16129031777381897 = 0.10/0.62.  An
    # instrument that reads `default_value` reports round 1 on a fixed file.
    # It is checked here so this instrument is KNOWN to be able to tell a fixed
    # material from an unfixed one -- an audit that has never made that
    # distinction is not evidence.
    lp = bpy.data.materials.get("LiveryPaint")
    if lp is not None and lp.node_tree is not None:
        b = next((n for n in lp.node_tree.nodes
                  if n.type == "BSDF_PRINCIPLED"), None)
        s = b.inputs.get("Metallic") if b else None
        if s is not None:
            chk("LiveryPaint: Metallic is LINKED", bool(s.is_linked), True,
                note="its default reads %.4f and is dead data"
                     % float(s.default_value))
            # R2-2110.  THERE IS NO SCALAR "EFFECTIVE METALLIC" TO CHECK, and
            # the first version of this check invented one.
            #
            # The chain is  Metallic <- 'R2CP_085_metallic -> paint'
            # (MATH/MULTIPLY), and MEASURED off the shipping car blend:
            #
            #     input[0]  is_linked=True   default 0.5    <- Mix.002 <- a
            #                                                  Voronoi/Map Range
            #                                                  chain: SPATIALLY
            #                                                  VARYING
            #     input[1]  is_linked=False  default 0.16129031777381897
            #
            # so the metallic is a MAP, not a number, and no single value is
            # the answer.  This check first read `input[0].default_value` and
            # got 0.5 -- Blender's default for an unconnected Math socket --
            # producing 0.5 x 0.16129 = 0.080645 and a FAIL on a correct film.
            # THAT IS THE VERY TRAP THIS BLOCK EXISTS TO NAME, one level
            # deeper than where R2-2041 named it: a `default_value` read off a
            # LINKED socket.
            #
            # R2-2041's own "effective Metallic 0.1000" has the same shape.
            # 0.10 = 0.62 x 0.16129, and the 0.62 is the Metallic socket's own
            # default -- the number that same block correctly called "dead
            # data" two lines earlier.  It is arithmetic on a value it had
            # just declared meaningless, and it landed on the intended answer
            # because 0.16129031777381897 IS 0.10/0.62 by construction.
            #
            # What is live, checkable, and actually diagnostic is the MULTIPLY
            # CONSTANT: it is round 2's whole edit to this material, it is
            # exactly 0.10/0.62, and it reads the same on a fixed file and
            # nothing like it on an unfixed one.
            src = s.links[0].from_node if s.is_linked else None
            chk("LiveryPaint: Metallic driven by a MULTIPLY",
                (src.type, src.operation) if src is not None else None,
                ("MATH", "MULTIPLY"))
            if src is not None and src.type == "MATH":
                chk("LiveryPaint: metallic base is a MAP, not a scalar",
                    bool(src.inputs[0].is_linked), True,
                    note="input[0].default_value reads %.4f and is dead data"
                         % float(src.inputs[0].default_value))
                # TOLERANCE 1e-7, AND I GOT THIS WRONG ONCE ALREADY IN THIS
                # BLOCK.  R2-2106 is the same mistake on the levelling
                # identity: a node socket holds a float32, so `0.10/0.62`
                # computed in double (0.161290322581) and the value actually
                # stored (0.161290317774) differ by 4.8e-9 -- inside float32's
                # ~1.9e-8 at this magnitude and nowhere near a 1e-9 bound.
                # 1e-7 is ~5x the float32 rounding and still refuses anything
                # that is not this ratio: round 1 ships no multiply node here
                # at all, and any other metallic target differs in the third
                # decimal, not the eighth.
                k = float(src.inputs[1].default_value)
                chk("LiveryPaint: metallic multiplier", round(k, 12),
                    round(0.10 / 0.62, 12), 1e-7,
                    note="0.10/0.62 to float32; round 1 shipped no such node")

    n_fail = sum(1 for r in rows if not r["ok"])
    if out_json:
        os.makedirs(os.path.dirname(os.path.abspath(out_json)) or ".",
                    exist_ok=True)
        json.dump({"file": bpy.data.filepath, "rows": rows,
                   "failures": n_fail}, open(out_json, "w"), indent=1)
        print("   wrote %s" % out_json)
    return n_fail


# THE EXIT IS OUTSIDE THE `try`.  R2-2108.
# The first version called `sys.exit()` INSIDE this `try/except BaseException`.
# `SystemExit` derives from `BaseException`, so the exit was caught by the
# file's own error handler and it printed BOTH verdicts on the same run:
#     >> STAGE RESULT: FILM_MATERIALS_FAIL (1 failures)
#     >> STAGE RESULT: FILM_MATERIALS_FAIL (instrument raised SystemExit(1))
# Here that was merely noisy because both said FAIL -- but the identical bug in
# v127/measure_strip.py turned a pass into "STRIP_MEASURED" followed by
# "STRIP_ABSENT", which is exactly the two-verdict trap this project judges on
# printed tokens to avoid.  Found by reading the output, not the source.
n = None
try:
    n = main()
except BaseException as exc:                                     # noqa: BLE001
    # A CRASH IS A FAIL, NOT A SILENCE.  R2-2041's `verify_carbon.py` raised,
    # Blender exited 0, and it printed six PASS lines and no verdict.
    import traceback
    traceback.print_exc()
    print(">> STAGE RESULT: FILM_MATERIALS_FAIL (instrument raised %r)" % (exc,))
    raise SystemExit(1)

print(">> STAGE RESULT: %s (%d failures)"
      % ("FILM_MATERIALS_OK" if n == 0 else "FILM_MATERIALS_FAIL", n))
raise SystemExit(0 if n == 0 else 1)
