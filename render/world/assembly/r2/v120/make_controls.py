"""Build the CONTROL SCENES for the #53 gate battery.

Every gate in this battery is meant to be judged against a case that MUST fail
and a case that MUST pass.  A check that has never failed has not been shown to
work -- fourteen times on this project the instrument was the broken thing.

    blender -b --factory-startup -P v120/make_controls.py
    blender -b --factory-startup -P v120/make_controls.py -- --outdir DIR

Writes TEN tiny .blend files into `--outdir` (this directory by default).
Nothing here touches the world; the control scenes are synthetic on purpose, so
the ONLY thing they can measure is whether the gate's own logic fires.

RUN THIS EVERY BATTERY RUN.  `lib_battery.sh :: regenerate_controls` does.
-----------------------------------------------------------------------------
R2-072: a control that names a stored artefact expires the instant that artefact
stops matching the thing it was built against, and it expires SILENTLY, into a
cheerful pass.  These controls are .blend files on disk and, until 2026-08-03,
NOTHING regenerated them: the battery opened whatever a human last left here.
`ctl_place_pos.blend` in particular is generated FROM THE LIVE CONTRACT --
`C.su_to_world`, `C.half_width`, `C.ground_z` -- so a stale copy is a control
positioned against a corridor that has since moved.  The battery therefore
rebuilds all ten from live source before it uses any of them.

THE DEPTH PAIR WAS A LIE FOR THE WHOLE BATTERY          (found & fixed 2026-08-02)
-----------------------------------------------------------------------------
The sentence above used to read "Every gate in this battery IS judged against a
case that MUST fail and a case that MUST pass."  For depth_probe that was false
from the day this file was written.  The depth pair was built as

    for tag, dz in (("pos", -0.200), ("neg", +0.200)):

so `ctl_depth_neg.blend` -- the control whose whole job is to PASS -- put the
CAR_Wheel 200 mm IN THE AIR above the Turntable_Deck top.  A floating car is a
failure in its own right; that scene was a second POSITIVE control wearing the
negative control's name.  It only ever looked like a negative control because
the depth_probe of the day seeded its running maximum at 0, measured nothing at
all above the deck, and printed DEPTH_PROBE_OK on an empty result.  Two broken
things agreeing is not a control: the "pass" was produced by the bug, not by the
geometry.  When `tools/depth_probe.py` was repaired (2026-08-02) it correctly
returned DEPTH_PROBE_FAIL / FLOATING / -200.00 mm on this scene, which left the
#53 battery with two positive controls for depth and NOTHING that must pass.
The missing case was first built separately as v121/make_depth_true_neg.py; it
is generated here now, and that file is kept only as the historical record.

THE THREE DEPTH CONTROLS THIS FILE NOW WRITES
-----------------------------------------------------------------------------
    ctl_depth_pos.blend         dz = -0.200  wheel sunk 200 mm into the deck
                                             -> MUST FAIL (PENETRATION)
    ctl_depth_float_pos.blend   dz = +0.200  wheel 200 mm in the air
                                             -> MUST FAIL (FLOATING)
    ctl_depth_neg.blend         dz =  0.000  wheel resting on the deck top
                                             -> MUST PASS (CONTACT)

The floating case is KEPT, as a second positive control under a name that says
so.  It is not redundant: penetration and levitation are opposite signs of
`surface_top - z` and they exercise different branches of the probe -- the sunk
wheel tests the `mm > max_depth_mm` bound and the per-surface verdict, the
floating wheel tests the `mm < -max_float_mm` bound and the per-FRAME "nothing
is holding it up" rule, which is the branch that used to be unreachable.  A
battery that dropped it would stop testing the exact defect described above.
The name carries the expectation: nothing called `..._pos` can be read as a
must-pass again, and `ctl_depth_neg.blend` now really is the case that passes.

Observed 2026-08-02 with tools/depth_probe.py --frames 1, on the blends this
file writes:  pos -> DEPTH_PROBE_FAIL rc=1 (PENETRATION +200.00 mm);
float_pos -> DEPTH_PROBE_FAIL rc=1 (FLOATING -200.00 mm);
neg -> DEPTH_PROBE_OK rc=0 (CONTACT 0.00 mm).

All three of ctl_depth_pos / ctl_depth_float_pos / ctl_depth_neg are wired into
v120, v121 and v122's battery.sh as `expect fail` / `expect fail` / `expect
pass`.  (The note that used to stand here said the float case "still needs
wiring in"; it was wired in on 2026-08-03 and the note was left behind.  A
docstring that under-claims a safeguard is the mirror of one that over-claims
it, and both stop the next person looking.)

THE PLACEMENT GATE HAD NO CONTROL AT ALL             (found & fixed 2026-08-03)
-----------------------------------------------------------------------------
`ctl_place_pos.blend` and `ctl_place_neg.blend` were written here from the day
this file existed and **no battery ever ran them**.  v120, v121 and v122 each
`run` placement_gate twice against the world and never once against a case that
must fail or a case that must pass -- so every placement verdict in all three
rested on an instrument that had not been shown to be measuring on that run.
placement_gate is the gate that guards every item placement, and it is the one
this project has already caught testing EMPTY AIR over 28 % of the lap
(MASTER-PLAN §6.17: an absolute world-z band on ground that runs -3.670..+7.964).
All three are wired in now.

AND THE FAR NEGATIVE CONTROL MEASURED NOTHING.  `ctl_place_neg` puts the
obstacle 3 km off the circuit, and the gate's own log says why that is weak:

    tested 1 objects; 1 rejected on bounding box; 0 measured per-vertex

It passes without the per-vertex path ever running, so it can only catch a gate
that INVENTS violations out of nothing.  It cannot catch OVER-rejection -- a
gate whose keep-out volume is too fat, or in the wrong frame -- which is the
failure this project actually had.  So there is a third placement control:

    ctl_place_nearmiss_neg.blend   the same obstacle just OUTSIDE the corridor,
                                   close enough that the gate MUST measure it
                                   per-vertex, and clean when it does.

Its lateral offset is derived from the LIVE contract every run
(`C.half_width(s)` + the gate's own 0.50 m road margin + the cube's half extent
+ `NEARMISS_GAP_M`), so it tracks the corridor instead of expiring against it.
Measured 2026-08-03 at s = 1000 on contract 1.2.1, side +1:

    gap 0.30 m -> road_corridor clearance -0.110 m   PLACEMENT_FAIL
    gap 0.55 m -> road_corridor clearance +0.139 m   PLACEMENT_CLEAN
    gap 0.80 m -> road_corridor clearance +0.389 m   PLACEMENT_CLEAN  <- shipped

i.e. this control sits 0.5 m from flipping, and 1 object is measured per-vertex
rather than 0.  `ctl_assert.py` is what holds it to that: `expect pass` alone
would be satisfied by a control that had quietly become a second 3 km case.
"""
import sys, os, math
import bpy
import numpy as np

_argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
if "--outdir" in _argv:
    HERE = os.path.abspath(_argv[_argv.index("--outdir") + 1])
    os.makedirs(HERE, exist_ok=True)
WORLD = os.path.expanduser("~/f1-round2/world")
if WORLD not in sys.path:
    sys.path.insert(0, WORLD)


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def cube(name, loc, size=1.0, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.data.name = name + "_mesh"
    ob.scale = scale
    return ob


def coll(name, objs):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    for ob in objs:
        for oc in list(ob.users_collection):
            oc.objects.unlink(ob)
        c.objects.link(ob)
    return c


def save(fn):
    p = os.path.join(HERE, fn)
    bpy.ops.wm.save_as_mainfile(filepath=p, compress=True)
    print("[CTL] wrote", p, os.path.getsize(p))


# ------------------------------------------------------------------ 1/2 ---
# placement_gate: an obstacle ON the racing line, and the same obstacle far
# outside every keep-out volume.
fresh()
import world_contract as C                                          # noqa: E402
print("[CTL] contract", C.__version__)

S_CTL = 1000.0
CUBE_HALF_M = 1.0          # the control obstacle is a size=2.0 cube
ROAD_MARGIN_M = 0.5        # placement_gate's own `road_margin`
NEARMISS_GAP_M = 0.80      # see the docstring: 0.30 fails, 0.55 and 0.80 pass
NEARMISS_SIDE = +1.0       # +1 is the side whose camera_path clearance is finite

x0, y0, _z = C.su_to_world(S_CTL, 0.0)
gz = float(C.ground_z(np.array([S_CTL]), np.array([0.0]))[0])
cube("CTL_Obstacle", (float(x0), float(y0), gz + 1.0), size=2.0)
save("ctl_place_pos.blend")

fresh()
import importlib
importlib.reload(C)
# 3 km off the circuit in +x: outside the corridor, the car path and the camera
# path by kilometres.  NOTE what the gate says about this one -- "1 rejected on
# bounding box; 0 measured per-vertex".  It proves the gate does not invent
# violations; it CANNOT prove the gate does not over-reject, because the
# per-vertex path never runs.  That is what the near-miss control below is for.
cube("CTL_Obstacle", (float(x0) + 3000.0, float(y0), gz + 1.0), size=2.0)
save("ctl_place_neg.blend")

# ---- the OVER-REJECTION detector, derived from the live contract -----------
# Just outside the corridor: close enough that the gate must measure it
# per-vertex, far enough that a correct gate must pass it.  Every term comes
# from the contract or from the gate, so the control moves when they do.
fresh()
importlib.reload(C)
u_nm = NEARMISS_SIDE * (C.half_width(S_CTL) + ROAD_MARGIN_M + CUBE_HALF_M
                        + NEARMISS_GAP_M)
xn, yn, _zn = C.su_to_world(S_CTL, float(u_nm))
gzn = float(C.ground_z(np.array([S_CTL]), np.array([u_nm]))[0])
print("[CTL] nearmiss: s=%.1f half_width=%.4f road_margin=%.3f cube_half=%.3f "
      "gap=%.3f -> u=%+.4f m, world (%.3f, %.3f, %.3f)"
      % (S_CTL, C.half_width(S_CTL), ROAD_MARGIN_M, CUBE_HALF_M,
         NEARMISS_GAP_M, u_nm, xn, yn, gzn + 1.0))
cube("CTL_Obstacle", (float(xn), float(yn), gzn + 1.0), size=2.0)
save("ctl_place_nearmiss_neg.blend")

# ------------------------------------------------------------------ 3/4 ---
# collision_gate: a CAR cube inside a SHOWROOM cube, and beside it.
for tag, dx in (("pos", 0.5), ("neg", 5.0)):
    fresh()
    a = cube("CAR_Part", (0.0, 0.0, 0.0), size=1.0)
    b = cube("SHOW_Wall", (dx, 0.0, 0.0), size=1.0)
    coll("CAR", [a])
    coll("SHOWROOM", [b])
    save("ctl_collide_%s.blend" % tag)

# ---------------------------------------------------------------- 5/6/7 ---
# depth_probe: a CAR object THROUGH the deck top, one hovering ABOVE it, and one
# RESTING on it.  dz is the offset of the wheel's underside from the deck top,
# so it is the whole difference between the three scenes -- and dz = 0.0 is the
# only one that must come back OK.  See the module docstring: `neg` used to be
# the +0.200 hover, i.e. a positive control mislabelled as the must-pass case.
DEPTH_CONTROLS = (
    # filename tag        dz        expected verdict from tools/depth_probe.py
    ("pos",             -0.200),  # PENETRATION -> DEPTH_PROBE_FAIL, exit 1
    ("float_pos",       +0.200),  # FLOATING    -> DEPTH_PROBE_FAIL, exit 1
    ("neg",              0.000),  # CONTACT     -> DEPTH_PROBE_OK,   exit 0
)
for tag, dz in DEPTH_CONTROLS:
    fresh()
    deck = cube("Turntable_Deck", (0.0, 0.0, 0.0), size=1.0,
                scale=(6.9, 6.9, 0.340))
    # deck top after scale: 0.5*0.340 = 0.170; move so the top is at 0.340
    deck.location = (0.0, 0.0, 0.340 - 0.170)
    # cube of size 0.5 centred at 0.340 + dz + 0.25 -> underside at 0.340 + dz
    part = cube("CAR_Wheel", (0.0, 0.0, 0.340 + dz + 0.25), size=0.5)
    coll("CAR", [part])
    coll("SHOWROOM", [deck])
    save("ctl_depth_%s.blend" % tag)

# ------------------------------------------------------------------ 8/9 ---
# instance_variety: N realized instances of ONE source mesh (spam), and N
# realized instances of N distinct source meshes (varied).  VERTS instancing
# puts every child at every parent vertex, so the two cases are built by moving
# the count between the parent's vertices and the number of children.
N = 500

fresh()
me = bpy.data.meshes.new("VEG_emitter")
me.from_pydata([(i * 0.5, 0.0, 0.0) for i in range(N)], [], [])
em = bpy.data.objects.new("VEG_Spam", me)
bpy.context.scene.collection.objects.link(em)
em.instance_type = "VERTS"
child = cube("VEG_Spam_src", (0.0, 0.0, 0.0), size=0.2)
child.parent = em
save("ctl_variety_pos.blend")

fresh()
me = bpy.data.meshes.new("VEG_emitter")
me.from_pydata([(0.0, 0.0, 0.0)], [], [])
em = bpy.data.objects.new("VEG_Varied", me)
bpy.context.scene.collection.objects.link(em)
em.instance_type = "VERTS"
for i in range(N):
    ch = cube("VEG_Varied_src%03d" % i, (0.0, 0.0, 0.0), size=0.2 + i * 1e-4)
    ch.data.name = "VEG_src_mesh_%03d" % i
    ch.parent = em
save("ctl_variety_neg.blend")

print("[CTL] ALL CONTROL SCENES WRITTEN")
