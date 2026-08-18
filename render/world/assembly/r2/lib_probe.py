"""Shared helpers for the round-2 assembly verification probes.

Loaded by every probeX.py with exec(open(...).read()).  Nothing here builds
geometry; it only classifies what is already in the scene and casts rays.
"""
import sys, os, json, time, math
import numpy as np
import bpy
from mathutils import Vector

WORLD = os.path.expanduser("~/f1-round2/world")
if WORLD not in sys.path:
    sys.path.insert(0, WORLD)
import world_contract as C

OUT_DIR = os.path.expanduser("~/f1-round2/render/world/assembly/r2")
LAP = C.LAP

# ---------------------------------------------------------------- roles ----
def role(name):
    if name.startswith("VEG_"):
        return "vegetation"
    if name.startswith("TER_"):
        return "TER_Ground"
    if name.startswith("DR_"):
        return "dressing"
    if name.startswith("ARCH_"):
        # PAINT IS NOT GROUND.  `ARCH_Markings` and `ARCH_RoadMarkings` are the
        # pit-lane and road lines: single quads 8-10 mm over whatever they are
        # painted on, and `ARCH_Markings` is ONE FLAT PLANE -- all 7 166 verts at
        # z = 0.007 -- so it does not follow the surface under it at all.  They
        # were classified "arch", which is in GROUND_ROLES, so a stripe of paint
        # answered "is there ground here?" with yes.  That is how 7.10 m2 of
        # painted line over an unbuilt substrate read as covered ground, and it
        # is the same shape as `n_GW_Right_Glass`: a metric that returns the same
        # answer whether the thing under it is there or not.
        if name.startswith("ARCH_Markings") or name.startswith("ARCH_RoadMarkings"):
            return "arch_paint"
        return "arch"
    if name.startswith("SURF_"):
        if name == "SURF_Track":
            return "track"
        if name.startswith("SURF_Kerb"):
            return "kerb"
        if name.startswith("SURF_AccessRoad"):
            return "access"
        return "surface_other"
    if name.startswith("BR_"):
        for pre, r in (("BR_Verge", "verge_platform"),
                       ("BR_Runoff", "runoff_asphalt"),
                       ("BR_Trap", "gravel_bed"),
                       ("BR_Gravel", "gravel_bed"),
                       ("BR_Stone", "gravel_stones"),
                       ("BR_Subbase", "subbase")):
            if name.startswith(pre):
                return r
        return "barrier_struct"
    return "other"


GROUND_ROLES = {"track", "kerb", "access", "surface_other", "arch",
                "verge_platform", "runoff_asphalt", "gravel_bed",
                "gravel_stones", "subbase", "TER_Ground"}
# Deliberately NOT in GROUND_ROLES: see `role()`.  Kept as its own set rather
# than dropped on the floor, because "is there paint here" is a real question and
# a probe that wants to ask it should not have to re-derive the prefixes.
PAINT_ROLES = {"arch_paint"}
STRUCT_ROLES = {"barrier_struct"}


def selftest_roles():
    """A role table nobody exercises drifts.  This is cheap enough to run on
    import from any probe that cares, and it fails loudly rather than returning a
    plausible classification for a name that has since been renamed."""
    cases = [("ARCH_Paving_ApronPlatform", "arch", True),
             ("ARCH_Markings", "arch_paint", False),
             ("ARCH_RoadMarkings", "arch_paint", False),
             ("SURF_Track", "track", True),
             ("TER_Ground_042", "TER_Ground", True),
             ("BR_Runoff_A", "runoff_asphalt", True),
             ("VEG_Grass_1", "vegetation", False)]
    bad = [(n, role(n), r, role(n) in GROUND_ROLES, g)
           for (n, r, g) in cases
           if role(n) != r or (role(n) in GROUND_ROLES) != g]
    if bad:
        raise AssertionError("lib_probe.role() drifted: %s" % (bad,))
    return len(cases)


def owner(name):
    if name.startswith("SURF_"):
        return "surface"
    if name.startswith("BR_"):
        return "barriers"
    if name.startswith("ARCH_"):
        return "architecture"
    if name.startswith("TER_") or name.startswith("VEG_"):
        return "terrain"
    if name.startswith("DR_"):
        return "dressing"
    return "?"


# ---------------------------------------------------------- visibility ----
def hide(pred, verbose=True):
    """hide_viewport removes an object from the evaluated depsgraph, so
    scene.ray_cast will not see it."""
    n = 0
    for ob in bpy.data.objects:
        if pred(ob):
            if not ob.hide_viewport:
                ob.hide_viewport = True
                n += 1
    bpy.context.view_layer.update()
    if verbose:
        print("[probe] hid %d objects" % n)
    return n


def show_all():
    for ob in bpy.data.objects:
        ob.hide_viewport = False
    bpy.context.view_layer.update()


def dg():
    return bpy.context.evaluated_depsgraph_get()


DOWN = Vector((0.0, 0.0, -1.0))


def top_hit(x, y, z0=400.0, D=None):
    """Topmost surface at (x, y).  Returns (z, object_name) or (None, None)."""
    D = D or dg()
    ok, loc, nrm, idx, ob, mat = bpy.context.scene.ray_cast(
        D, Vector((x, y, z0)), DOWN)
    if not ok:
        return None, None
    return loc.z, ob.name


def stack(x, y, z0=400.0, zmin=-60.0, D=None, maxhits=24, eps=1e-4):
    """Every surface under (x, y), top first: [(z, name), ...]."""
    D = D or dg()
    out = []
    z = z0
    for _ in range(maxhits):
        ok, loc, nrm, idx, ob, mat = bpy.context.scene.ray_cast(
            D, Vector((x, y, z)), DOWN)
        if not ok or loc.z < zmin:
            break
        out.append((loc.z, ob.name))
        nz = loc.z - eps
        if nz >= z:
            break
        z = nz
    return out


# ----------------------------------------------------------- statistics ---
def stats(a, nd=6):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return {"n": 0}
    return {"n": int(a.size),
            "min": round(float(a.min()), nd),
            "max": round(float(a.max()), nd),
            "mean": round(float(a.mean()), nd),
            "p05": round(float(np.percentile(a, 5)), nd),
            "p50": round(float(np.percentile(a, 50)), nd),
            "p95": round(float(np.percentile(a, 95)), nd),
            "p99": round(float(np.percentile(a, 99)), nd),
            "rms": round(float(np.sqrt((a ** 2).mean())), nd)}


def runs(vals):
    """Contiguous runs in a sorted list of numbers with a fixed step."""
    vals = sorted(set(vals))
    if not vals:
        return []
    out = []
    a = b = vals[0]
    step = None
    for v in vals[1:]:
        if step is None:
            step = v - a
        if abs(v - b - step) < 1e-6 or v - b <= step + 1e-6:
            b = v
        else:
            out.append([a, b]); a = b = v
    out.append([a, b])
    return out


# ------------------------------------------------------- WHERE TO WRITE ----
# `save()` JOINED ITS ARGUMENT ONTO OUT_DIR, so it could only ever write into
# the assembly root. probe_pitexit.py combined it with `os.path.basename(OUT)`
# and therefore ignored every output path it was ever given -- v120/battery.sh
# asked for v120/pitexit_v120.json and the file landed in the assembly root.
#
# It was worse than one misplaced file. probeA.py .. probeK.py all called it
# with FIXED names, so v120's battery and v121's battery wrote to the same
# eleven paths, and v120/collect.py then read `probeD.json` / `probeG.json`
# that the v121 run had already overwritten -- a cross-version diff between a
# file and itself. The three `*_partial.json` checkpoints were shared the same
# way.
#
# All of them now use `resolve_out()`, `sidecar()` and `write_out()` below,
# which write where they were told and refuse to invent a destination;
# `save()` itself now raises, so the idiom cannot return by copy-paste.
# Controls: selftest_probe_out.py, selftest_probe_isolation.py.

# --- BEGIN resolve_out (self-contained: os/sys/json only, and exercised by
# --- selftest_probe_out.py, which extracts THIS EXACT TEXT and runs it) ------
def resolve_out(argv, blend_path=None, tool="probe"):
    """The ONE absolute path this run may write to, or SystemExit.

    Reads only the arguments after `--` (everything before them belongs to
    Blender).  Accepts `--out PATH`, `--out=PATH`, or a single bare positional
    `*.json` for the callers that predate `--out`.  Returns an absolute path
    whose parent exists and is writable.  Never guesses.
    """
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    out, positional = None, []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--out":
            if i + 1 >= len(args) or args[i + 1].startswith("--"):
                raise SystemExit("[%s] --out needs a path after it" % tool)
            out = args[i + 1]
            i += 2
            continue
        if a.startswith("--out="):
            out = a.split("=", 1)[1]
            if not out:
                raise SystemExit("[%s] --out= needs a path after it" % tool)
            i += 1
            continue
        if a.endswith(".json"):
            positional.append(a)
        i += 1
    if out is None:
        if len(positional) > 1:
            raise SystemExit("[%s] ambiguous output: %d bare .json arguments "
                             "(%s). Use --out." % (tool, len(positional),
                                                   ", ".join(positional)))
        if positional:
            out = positional[0]
            print("[%s] no --out; taking the bare positional argument %r"
                  % (tool, out))
    if out is None:
        # NOT a place to be helpful. A default here is how a tool comes to
        # overwrite a file nobody asked it to touch.
        suggest = (os.path.splitext(os.path.abspath(blend_path))[0] + "_"
                   + tool + ".json") if blend_path else \
                  os.path.join(os.getcwd(), tool + ".json")
        raise SystemExit(
            "[%s] REFUSING TO RUN: no output path given.\n"
            "    pass  -- --out /absolute/path.json\n"
            "    e.g.  -- --out %s" % (tool, suggest))
    out = os.path.abspath(os.path.expanduser(out))
    if os.path.isdir(out):
        raise SystemExit("[%s] --out %s is a directory" % (tool, out))
    if not out.endswith(".json"):
        raise SystemExit("[%s] --out %s does not end in .json" % (tool, out))
    parent = os.path.dirname(out)
    try:
        os.makedirs(parent, exist_ok=True)
    except OSError as e:
        raise SystemExit("[%s] cannot create %s: %s" % (tool, parent, e))
    if not os.access(parent, os.W_OK):
        raise SystemExit("[%s] %s is not writable" % (tool, parent))
    return out


def sidecar(out, suffix):
    """A second artefact BESIDE `out`, never in a hardcoded directory.

    probeA/B/C checkpoint themselves mid-run with `save("probeA_partial.json")`,
    which joins onto lib_probe's OUT_DIR — so every version of the battery wrote
    its partials to the SAME three paths in the assembly root, and v121 stamped
    on v120's while v120's collect.py was still reading them. A partial is an
    artefact of ONE run and belongs next to that run's output.

        sidecar("/x/v121/probeA_v121.json", "partial")
            -> "/x/v121/probeA_v121_partial.json"
    """
    stem, ext = os.path.splitext(out)
    return stem + "_" + suffix + (ext or ".json")


# --- the provenance stamp, deliberately INSIDE this block --------------------
#
# WHICH BLEND DID THIS PROBE OPEN?
#
# A probe output that cannot answer that is worthless, and here it has been
# worse than worthless: a harness measured a FOUR-DAY-OLD blend and returned
# mean |diff| 7.69e-06 against a 7.70e-06 noise floor. Flawless, entirely
# convincing, and the real answer was 57.50 %. Nothing in the output said which
# file it had read.
#
# Probes here run against assembly2 / assembly5 / assembly6 / render2 and older
# copies, in loops, from several directories, and the outputs are then DIFFED
# ACROSS VERSIONS. A diff between two probe outputs is meaningless unless both
# say what they measured.
#
# IT LIVES INSIDE THE `resolve_out` MARKERS ON PURPOSE. `v120/vertex_fingerprint.py`
# and `selftest_probe_out.py` extract exactly this block by regex and exec it
# standalone. Defining the stamp outside the markers would let `write_out` be
# extracted WITHOUT it -- an unstamped writer, in the one file whose subject is
# writers that do not say what they did. The extraction must be unable to
# separate them.
#
# The .blend is hashed in full: a few seconds on a 4 GB assembly against a probe
# run measured in minutes. There is deliberately no opt-out, because a truncated
# hash is a hash that agrees across two different files.
_TOOLS = os.path.expanduser("~/f1-round2/tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
import provenance as _prov                                       # noqa: E402

# NOT `__file__`. Every probe loads this file with
# `exec(open(lib_probe.py).read())`, which runs it in the PROBE's namespace,
# where `__file__` is the probe -- so `__file__` here names probeA.py, not this
# file. Getting that wrong would file the wrong hash under the label
# "lib_probe", which is precisely the quiet mislabelling this block exists to
# stop.
_LIB_PROBE_PY = os.path.expanduser("~/f1-round2/render/world/assembly/r2/lib_probe.py")


def _stamped(obj):
    """Attach the provenance header, if the payload can hold one.

    A probe returning a bare list keeps its shape -- a stamp is not worth
    breaking a consumer over -- but that is said out loud rather than silently.
    """
    # Both of these are resolved defensively BECAUSE THIS BLOCK IS EXTRACTED
    # AND EXEC'D STANDALONE by vertex_fingerprint.py and selftest_probe_out.py,
    # in namespaces that have no `bpy` and no `__file__`. A stamp that raises
    # is a writer that cannot write, so it degrades to naming what it does
    # know rather than exploding -- and `blend: NOT_GIVEN` is then a recorded
    # fact about the run, not a silent omission.
    blend = None
    _b = globals().get("bpy")
    if _b is not None:
        blend = _b.data.filepath or None
    st = _prov.stamp(
        tool_file=globals().get("__file__") or _LIB_PROBE_PY,
        tool_version="assembly probe via lib_probe",
        inputs=[("blend", blend)],
        also_hash=[("lib_probe", _LIB_PROBE_PY)],
    )
    if isinstance(obj, dict):
        out = {_prov.STAMP_KEY: st}
        out.update(obj)
        return out
    print("[probe] NOTE: payload is a %s, not a dict -- provenance stamp "
          "could not be attached to it" % type(obj).__name__)
    return obj


def write_out(path, obj):
    """Write to the ABSOLUTE path we were given, WITH its provenance.

    Deliberately NOT save(): that one joins its argument onto the hardcoded
    OUT_DIR, which is half of the defect described just above.
    """
    with open(path, "w") as f:
        json.dump(_stamped(obj), f, indent=1, default=str)
    print("[probe] wrote", path)
    return path
# --- END resolve_out ---------------------------------------------------------




def save(name, obj=None):
    """REMOVED. It was the mechanism of the cross-version overwrite.

    It joined `name` onto the hardcoded OUT_DIR, so a probe could only ever
    write into the assembly root and every version of every battery wrote to
    the same filenames. `probeA.json` .. `probeK.json` and the three
    `*_partial.json` checkpoints were all shared across v120 and v121, and
    v120/collect.py read files v121 had already replaced.

    All eleven probes now call `resolve_out()` / `write_out()`. This body is
    kept, and raises, so the idiom cannot come back by copy-paste from an old
    file -- a silently-working `save()` is exactly how it spread to eleven
    files in the first place.
    """
    raise SystemExit(
        "[probe] save(%r) is REMOVED: it wrote to a hardcoded OUT_DIR and was "
        "the mechanism of the v120/v121 overwrite.\n"
        "    use:  OUT = resolve_out(sys.argv, blend_path=bpy.data.filepath, "
        "tool='probeX')\n"
        "          write_out(OUT, payload)\n"
        "          write_out(sidecar(OUT, 'partial'), payload)   # checkpoints"
        % (name,))


# ------------------------------------------------------------- geometry ---
def world_verts(ob, D=None):
    """Evaluated world-space vertices of one object as an (N,3) array."""
    D = D or dg()
    ev = ob.evaluated_get(D)
    try:
        me = ev.to_mesh()
    except Exception:
        return None
    if me is None or len(me.vertices) == 0:
        try:
            ev.to_mesh_clear()
        except Exception:
            pass
        return None
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    M = np.array(ev.matrix_world)
    co = co @ M[:3, :3].T + M[:3, 3]
    ev.to_mesh_clear()
    return co


def su_of(P, chunk=200000):
    """(s, u) of an (N,3) world array."""
    s = np.empty(len(P)); u = np.empty(len(P))
    for i in range(0, len(P), chunk):
        j = min(i + chunk, len(P))
        ss, uu = C.project(P[i:j, 0], P[i:j, 1])
        s[i:j] = ss; u[i:j] = uu
    return s, u


print("[probe] contract %s  lap %.1f" % (C.__version__, LAP))
