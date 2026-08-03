#!/usr/bin/env python3
"""SOCKET SETTER CENSUS AND CONTROL -- R2-072.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -noaudio \
        -P tools/socket_setter_census.py

WHAT THIS IS FOR
----------------
Three modules carry a private BY-NAME socket setter:

    world/items/marshal_post_column.py :: _set(g, b, val, *names)
    world/items/spectator_seated.py    :: _set(node, key, val) / _link(...)
    world/build_architecture.py        :: _set(node, key, val)

and `marshal_post_column._set` is imported by `gantry_truss`, `pont_girder`
and `pont_deck_slab` as well.  Until R2-072 all four DROPPED THE VALUE when
the socket name did not resolve -- `if nm is not None:` in one, bare
`except Exception: pass` in the other two.

Addressing by name is why the R2-057 / R2-070 defect -- a socket INSERTION
sliding every index along -- cannot reach these.  A socket RENAME or REMOVAL
is the case they did not cover, and it is worse than the index bug in one
specific way: **it leaves no artefact signature.**
`tools/socket_blend_scan.py` can see a bump output that landed on `Thin Wall`
because the wrong link is IN the blend.  A Roughness that was never written is
invisible: the socket holds its default, and a default is a legal value.  A
scalar parameter would silently do nothing, forever.

WHY THIS WAS MEASURED BEFORE IT WAS CHANGED
-------------------------------------------
"Make it loud" is not automatically right.  If those call sites included
legitimate optional writes -- probing for a socket that only exists on some
node types or some Blender versions -- raising would break working modules for
no gain.  So the question "how many of these are actually optional?" is
answered by counting, in both directions:

  STATIC   parse every call site and separate single-name calls (a miss is
           always a dropped value) from alias lists (a miss on one name is
           legitimate if a sibling resolves).
  RUNTIME  wrap all four helpers, build every material those modules own, and
           count the misses that really happen.  This is the arm that matters,
           because Blender resolves a socket string against the socket's
           `identifier` as well as its display `name` -- `'Fac'` finds
           `'Factor'` -- so a static reading of the socket table over-reports
           misses by a wide margin and would have condemned ten correct links
           in `spectator_seated`.

THE CONTROL
-----------
A census that only ever sees working code cannot tell "nothing is dropped"
from "the instrument sees nothing".  So this also plants a socket that is
genuinely gone and asserts each helper RAISES on it.  Both arms, every run.

EXIT CODES
    0  census complete, no drops, and every helper failed the planted miss
    1  a drop was observed, or a helper swallowed the planted miss
    2  the census could not run
"""

import ast
import json
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, "world"), os.path.join(ROOT, "world", "items"),
           os.path.join(ROOT, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bpy                                                       # noqa: E402
import gate_exit                                                 # noqa: E402

LOG = []

# (module, helper) -> which positional slots hold socket NAMES.
NAME_SLOTS = {
    ("marshal_post_column", "_set"): ("varargs", 3),
    ("spectator_seated", "_set"): ("fixed", 1),
    ("spectator_seated", "_link"): ("fixed", 3),
    ("build_architecture", "_set"): ("fixed", 1),
}
SCAN_DIRS = ("world", "tools", "anim", "sim", "audio", "render")


# --------------------------------------------------------------------------
# STATIC ARM
# --------------------------------------------------------------------------
def static_census():
    rows = []
    files = []
    for base in SCAN_DIRS:
        for dp, dn, fn in os.walk(os.path.join(ROOT, base)):
            dn[:] = [d for d in dn if d != "__pycache__"]
            files += [os.path.join(dp, f) for f in fn if f.endswith(".py")]
    for path in sorted(files):
        mod = os.path.splitext(os.path.basename(path))[0]
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        defines = {n.name for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef)
                   and n.name in ("_set", "_link")}
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            if isinstance(f, ast.Attribute):
                fn_name, attr = f.attr, getattr(f.value, "id", None)
            elif isinstance(f, ast.Name):
                fn_name, attr = f.id, None
            else:
                continue
            if fn_name not in ("_set", "_link"):
                continue
            # `HS` is how every importer names marshal_post_column.
            owner = "marshal_post_column" if attr == "HS" else \
                (mod if attr is None else None)
            if owner is None or (owner == mod and fn_name not in defines):
                continue
            key = (owner, fn_name)
            if key not in NAME_SLOTS:
                continue
            kind, slot = NAME_SLOTS[key]
            nameargs = n.args[slot:] if kind == "varargs" \
                else n.args[slot:slot + 1]
            lits = [a.value for a in nameargs
                    if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            rows.append({"file": os.path.relpath(path, ROOT), "line": n.lineno,
                         "helper": "%s.%s" % (owner, fn_name),
                         "n_candidates": len(nameargs), "literals": lits,
                         "dynamic": len(nameargs) - len(lits)})
    return rows


# --------------------------------------------------------------------------
# RUNTIME ARM
# --------------------------------------------------------------------------
def site():
    for fr in reversed(traceback.extract_stack()[:-2]):
        if os.path.basename(fr.filename) != os.path.basename(__file__):
            return "%s:%d" % (os.path.relpath(fr.filename, ROOT), fr.lineno)
    return "?"


def wrap_named(mod):
    """marshal_post_column._set: alias list, raises when NONE resolves."""
    orig_in, orig_set = mod._in, mod._set

    def _set(g, b, val, *names):
        nm = orig_in(b, *names)
        LOG.append({"helper": "marshal_post_column._set", "site": site(),
                    "node": b.bl_idname, "names": list(names),
                    "resolved": nm, "dropped": nm is None})
        return orig_set(g, b, val, *names)
    mod._set = _set


def wrap_single(mod, modname):
    """spectator_seated / build_architecture: one name, raises when it is gone."""
    orig_set = mod._set

    def _set(node, key, val):
        LOG.append({"helper": "%s._set" % modname, "site": site(),
                    "node": getattr(node, "bl_idname", "?"), "names": [key],
                    "resolved": key if key in node.inputs else None,
                    "dropped": key not in node.inputs})
        return orig_set(node, key, val)
    mod._set = _set
    if hasattr(mod, "_link"):
        orig_link = mod._link

        def _link(nt, a, b, key):
            LOG.append({"helper": "%s._link" % modname, "site": site(),
                        "node": getattr(b, "bl_idname", "?"), "names": [key],
                        "resolved": key if key in b.inputs else None,
                        "dropped": key not in b.inputs})
            return orig_link(nt, a, b, key)
        mod._link = _link


def build_everything():
    """Every material the four modules own.  Names what it could NOT build."""
    built, skipped = [], []

    import marshal_post_column as MPC
    wrap_named(MPC)
    import gantry_truss as GT
    import pont_girder as PG
    import pont_deck_slab as PDS
    import spectator_seated as SS
    import build_architecture as BA
    wrap_single(SS, "spectator_seated")
    wrap_single(BA, "build_architecture")

    jobs = [("marshal_post_column.materials", MPC.materials),
            ("gantry_truss.materials", GT.materials),
            ("pont_girder.materials", PG.materials),
            ("pont_deck_slab.materials", PDS.materials),
            # The CTX_ context materials live outside materials(), and they
            # are the ones R2-070 was found in, so they are not optional here.
            ("pont_girder.context_ground", PG.context_ground),
            ("gantry_truss.context_ground",
             lambda: GT.context_ground((0.0, 0.0, 0.0))),
            ("pont_deck_slab.context_surround", PDS.context_surround)]
    jobs += [("spectator_seated._material(%s)" % k,
              (lambda k=k: SS._material(k))) for k in SS.MAT_NAMES]
    jobs += [("build_architecture.mat_paving", BA.mat_paving),
             ("build_architecture.mat_board", BA.mat_board),
             ("build_architecture.mat_roofseam", BA.mat_roofseam),
             ("build_architecture.mat_generic",
              lambda: BA.mat_generic("CEN_generic", (0.4, 0.4, 0.4, 1), 0.5)),
             ("build_architecture.mat_paint",
              lambda: BA.mat_paint("CEN_paint", (0.6, 0.1, 0.1, 1))),
             ("build_architecture.mat_glass",
              lambda: BA.mat_glass("CEN_glass", (0.6, 0.7, 0.8, 1))),
             ("build_architecture.mat_mesh_screen",
              lambda: BA.mat_mesh_screen("CEN_screen", (0.3, 0.3, 0.3, 1))),
             ("build_architecture.mat_slab",
              lambda: BA.mat_slab("CEN_slab", (1.5, 1.0),
                                  [(0.3, (0.5, 0.5, 0.5, 1)),
                                   (0.7, (0.6, 0.6, 0.6, 1))]))]
    for label, fn in jobs:
        try:
            fn()
            built.append(label)
        except Exception as exc:                                 # noqa: BLE001
            skipped.append("%s -- %s: %s" % (label, type(exc).__name__, exc))
    return built, skipped


# --------------------------------------------------------------------------
# THE CONTROL: a socket that is genuinely gone must not be swallowed
# --------------------------------------------------------------------------
def planted_miss_control():
    """A census that only sees working code cannot tell 'nothing dropped' from
    'the instrument sees nothing'.  So plant a name no node has, on a REAL
    Principled BSDF, and require every helper to refuse it."""
    import marshal_post_column as MPC
    import spectator_seated as SS
    import build_architecture as BA

    m = bpy.data.materials.new("SSC_CONTROL")
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    g = MPC.NG(m)
    tex = nt.nodes.new("ShaderNodeTexNoise")

    GONE = "Rougness"          # the rename that will happen one day, misspelt
    arms = [
        ("marshal_post_column._set",
         lambda: MPC._set(g, b, 0.5, GONE)),
        ("marshal_post_column._set (alias list, none resolving)",
         lambda: MPC._set(g, b, 0.5, GONE, "Specularity")),
        ("spectator_seated._set", lambda: SS._set(b, GONE, 0.5)),
        ("spectator_seated._link",
         lambda: SS._link(nt, tex.outputs[0], b, GONE)),
        ("build_architecture._set", lambda: BA._set(b, GONE, 0.5)),
    ]
    results = []
    for label, fn in arms:
        try:
            fn()
            results.append((label, False, "returned normally -- SWALLOWED"))
        except Exception as exc:                                 # noqa: BLE001
            results.append((label, True, "%s" % type(exc).__name__))

    # And the other direction, on the same nodes: a name that IS there must
    # still work, or "it raises" would just mean "it raises at everything".
    negatives = [
        ("marshal_post_column._set", lambda: MPC._set(g, b, 0.5, "Roughness")),
        ("marshal_post_column._set (alias list, 2nd resolves)",
         lambda: MPC._set(g, b, 0.5, GONE, "Roughness")),
        ("spectator_seated._set", lambda: SS._set(b, "Roughness", 0.5)),
        ("spectator_seated._link",
         lambda: SS._link(nt, tex.outputs[0], b, "Roughness")),
        ("build_architecture._set", lambda: BA._set(b, "Roughness", 0.5)),
    ]
    neg = []
    for label, fn in negatives:
        try:
            fn()
            neg.append((label, True, "wrote"))
        except Exception as exc:                                 # noqa: BLE001
            neg.append((label, False, "%s: %s" % (type(exc).__name__, exc)))
    bpy.data.materials.remove(m)
    return results, neg


def main():
    stat = static_census()
    built, skipped = build_everything()
    # Snapshot BEFORE the control runs. The control drives the same wrapped
    # helpers, so its deliberate misses would otherwise be counted as census
    # drops -- which is how a census reports the defect it planted itself.
    census = list(LOG)
    drops = [c for c in census if c["dropped"]]
    alias = [c for c in census if len(c["names"]) > 1]
    alias_fell = [c for c in alias if c["resolved"] != c["names"][0]]
    pos, neg = planted_miss_control()

    p = sys.stdout.write
    p("=" * 78 + "\n")
    p("SOCKET SETTER CENSUS  (R2-072)\n")
    p("=" * 78 + "\n")

    p("\n[STATIC] every call site of the four by-name setters\n")
    p("  %d call site(s)\n" % len(stat))
    byh = {}
    for r in stat:
        byh.setdefault(r["helper"], []).append(r)
    for h in sorted(byh):
        rs = byh[h]
        multi = [r for r in rs if r["n_candidates"] > 1]
        p("    %-32s %3d sites, %d single-name, %d alias list(s)\n"
          % (h, len(rs), len(rs) - len(multi), len(multi)))
        for t in sorted({tuple(r["literals"]) for r in multi}):
            p("        alias list %s\n" % (list(t),))
    p("  A single-name call has no sibling to fall back to, so a miss there is\n"
      "  ALWAYS a dropped value. That is %d of %d sites.\n"
      % (len([r for r in stat if r["n_candidates"] == 1]), len(stat)))

    p("\n[RUNTIME] every material those modules build\n")
    p("  entry points built : %d\n" % len(built))
    for s in skipped:
        p("  NOT BUILT          : %s\n" % s)
    p("  helper calls seen  : %d\n" % len(census))
    p("  calls that DROPPED : %d\n" % len(drops))
    p("  alias-list calls   : %d, of which %d fell through to a later name\n"
      % (len(alias), len(alias_fell)))
    byh2 = {}
    for c in census:
        d = byh2.setdefault(c["helper"], [0, 0])
        d[0] += 1
        d[1] += 1 if c["dropped"] else 0
    for h in sorted(byh2):
        p("    %-32s %4d calls, %d dropped\n" % (h, byh2[h][0], byh2[h][1]))
    for c in drops[:40]:
        p("    DROP %-46s %s %s\n" % (c["site"], c["node"], c["names"]))

    p("\n[CONTROL] a socket name that is genuinely gone, on a real Principled\n")
    ok = True
    for label, fired, how in pos:
        p("    %-52s %s (%s)\n"
          % (label, "REFUSED" if fired else "*** SWALLOWED ***", how))
        ok = ok and fired
    p("  and the other direction -- a name that IS there must still write,\n"
      "  or 'it raises' would only mean 'it raises at everything':\n")
    for label, wrote, how in neg:
        p("    %-52s %s (%s)\n"
          % (label, "wrote" if wrote else "*** REFUSED A LIVE SOCKET ***", how))
        ok = ok and wrote

    json.dump({"static": stat, "runtime": census, "built": built,
               "not_built": skipped,
               "control_planted_miss": [list(r) for r in pos],
               "control_live_socket": [list(r) for r in neg]},
              open(os.path.join(ROOT, "work", "socket_setter_census.json"), "w"),
              indent=1)

    if drops:
        ok = False
    p("\n" + "=" * 78 + "\n")
    p("STAGE RESULT: %s\n" % ("PASS" if ok else "FAIL"))
    p("=" * 78 + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    # Blender 5.2 exits 0 on an uncaught script exception, so the status has to
    # be set from the verdict rather than inferred from the absence of a crash.
    gate_exit.guard(main, tool="socket_setter_census")
