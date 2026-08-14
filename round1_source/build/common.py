"""Shared mesh / material helpers for the F1 showroom build.

Everything is metric: 1 Blender unit = 1 metre. The car is modelled to real
2024-spec dimensions (5.6 m long, 2.0 m wide, 0.72 m tyre diameter).
"""

import math

import bmesh
import bpy
from mathutils import Vector

TAU = math.pi * 2.0


# --------------------------------------------------------------------------- #
# collections
# --------------------------------------------------------------------------- #

def collection(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    target = parent or bpy.context.scene.collection
    if c.name not in target.children:
        # unlink from anywhere else first so re-runs do not duplicate parents
        for other in bpy.data.collections:
            if c.name in other.children:
                other.children.unlink(c)
        if c.name in bpy.context.scene.collection.children and target is not bpy.context.scene.collection:
            bpy.context.scene.collection.children.unlink(c)
        target.children.link(c)
    return c


def purge_collection(name):
    """Delete a collection and every object inside it (idempotent rebuilds)."""
    c = bpy.data.collections.get(name)
    if c is None:
        return
    for ob in list(c.objects):
        data = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if data is None:
            continue
        try:
            if data.users:
                continue
        except ReferenceError:
            continue
        for lib in (bpy.data.meshes, bpy.data.curves, bpy.data.lights,
                    bpy.data.cameras, bpy.data.metaballs):
            try:
                lib.remove(data)
                break
            except (ReferenceError, RuntimeError, TypeError):
                continue
    for child in list(c.children):
        purge_collection(child.name)
    bpy.data.collections.remove(c)


# --------------------------------------------------------------------------- #
# mesh construction
# --------------------------------------------------------------------------- #

def new_obj(name, verts, faces, coll=None, smooth=True, auto_smooth=None):
    """Build a mesh object from raw vert/face lists, normals recalculated."""
    if name in bpy.data.objects:
        old = bpy.data.objects[name]
        od = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if od and od.users == 0 and isinstance(od, bpy.types.Mesh):
            bpy.data.meshes.remove(od)

    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate(verbose=False)
    me.update()

    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()

    if smooth:
        for p in me.polygons:
            p.use_smooth = True

    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)

    if auto_smooth is not None:
        shade_auto_smooth(ob, auto_smooth)
    return ob


def shade_auto_smooth(ob, angle_deg=35.0):
    """Smooth-by-angle without operators.

    `bpy.ops.object.shade_auto_smooth` needs a 3D-viewport context, which does
    not exist while the UI sits on the Rendering workspace - it raised
    "context is incorrect" mid-build. Marking edges sharp above the threshold
    produces the same shading and works headless, from any workspace.
    """
    me = ob.data
    for p in me.polygons:
        p.use_smooth = True

    thresh = math.cos(math.radians(angle_deg))
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.normal_update()
    for e in bm.edges:
        lf = e.link_faces
        if len(lf) == 2:
            e.smooth = lf[0].normal.dot(lf[1].normal) >= thresh
        else:
            e.smooth = True
    bm.to_mesh(me)
    bm.free()
    me.update()
    return ob


def loft(rings, closed=True, cap_start=True, cap_end=True):
    """Bridge a list of equal-length vertex rings into a quad surface.

    rings: list[list[(x, y, z)]] - every ring must have the same point count and
    consistent point ordering, otherwise the surface twists.
    """
    n = len(rings[0])
    for r in rings:
        if len(r) != n:
            raise ValueError(f"ring length mismatch: {len(r)} != {n}")

    verts = [tuple(v) for ring in rings for v in ring]
    faces = []
    span = n if closed else n - 1
    for i in range(len(rings) - 1):
        a, b = i * n, (i + 1) * n
        for j in range(span):
            j2 = (j + 1) % n
            faces.append((a + j, a + j2, b + j2, b + j))
    if closed and cap_start:
        faces.append(tuple(range(n))[::-1])
    if closed and cap_end:
        s = (len(rings) - 1) * n
        faces.append(tuple(range(s, s + n)))
    return verts, faces


def box(name, x0, x1, y0, y1, z0, z1, coll=None, smooth=False):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return new_obj(name, v, f, coll=coll, smooth=smooth)


def revolve(name, profile, segments=128, coll=None, smooth=True,
            auto_smooth=30.0, merge=1e-4, axis_offset=(0.0, 0.0)):
    """Solid of revolution around +Z from a (radius, z) profile.

    Points at radius 0 collapse into a single pole vertex after the merge pass,
    which is what keeps the caps free of degenerate fan triangles.
    """
    ox, oy = axis_offset
    rings = []
    for r, z in profile:
        ring = []
        for i in range(segments):
            t = TAU * i / segments
            ring.append((ox + r * math.cos(t), oy + r * math.sin(t), z))
        rings.append(ring)
    verts, faces = loft(rings, closed=True, cap_start=False, cap_end=False)
    ob = new_obj(name, verts, faces, coll=coll, smooth=smooth)
    merge_doubles(ob, merge)
    if auto_smooth is not None:
        shade_auto_smooth(ob, auto_smooth)
    return ob


def merge_doubles(ob, dist=1e-4):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def grid_surface(rows):
    """rows: list[list[(x,y,z)]] -> open quad sheet (no wrap, no caps)."""
    n = len(rows[0])
    verts = [tuple(v) for row in rows for v in row]
    faces = []
    for i in range(len(rows) - 1):
        a, b = i * n, (i + 1) * n
        for j in range(n - 1):
            faces.append((a + j, a + j + 1, b + j + 1, b + j))
    return verts, faces


# --------------------------------------------------------------------------- #
# profile maths
# --------------------------------------------------------------------------- #

def catmull_rom(points, samples):
    """Sample a Catmull-Rom spline through `points` (list of 2-tuples)."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    segs = len(pts) - 3
    for i in range(samples):
        u = i / (samples - 1)
        f = u * segs
        seg = min(int(f), segs - 1)
        t = f - seg
        p0, p1, p2, p3 = pts[seg], pts[seg + 1], pts[seg + 2], pts[seg + 3]
        t2, t3 = t * t, t * t * t
        out.append(tuple(
            0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t
                   + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                   + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3)
            for k in range(len(p1))
        ))
    return out


def ring_from_half(x, half_pts, samples=33):
    """Mirror a half section profile [(y, z), ...] into a closed ring at station x.

    half_pts must run bottom-centre (y=0) -> outboard -> top-centre (y=0).
    Result is counter-clockwise in the YZ plane, 2*samples-2 points.
    """
    half = catmull_rom(half_pts, samples)
    half[0] = (0.0, half[0][1])
    half[-1] = (0.0, half[-1][1])
    ring = [(x, y, z) for (y, z) in half]
    ring += [(x, -y, z) for (y, z) in reversed(half[1:-1])]
    return ring


def superellipse_ring(x, half_w, z_bot, z_top, n_top=3.0, n_bot=5.0, n_pts=48):
    """Rounded-rect section: high n = boxy, n=2 = ellipse."""
    zc, zh = 0.5 * (z_bot + z_top), 0.5 * (z_top - z_bot)
    ring = []
    for i in range(n_pts):
        t = TAU * i / n_pts
        ct, st = math.cos(t), math.sin(t)
        e = 2.0 / (n_top if st >= 0 else n_bot)
        y = half_w * math.copysign(abs(ct) ** e, ct)
        z = zc + zh * math.copysign(abs(st) ** e, st)
        ring.append((x, y, z))
    return ring


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def blend_profiles(pa, pb, t):
    """Blend two equal-length half profiles."""
    return [(lerp(a[0], b[0], t), lerp(a[1], b[1], t)) for a, b in zip(pa, pb)]


# --------------------------------------------------------------------------- #
# modifiers
# --------------------------------------------------------------------------- #

def add_bevel(ob, width=0.004, segments=3, angle=40.0, clamp=True):
    m = ob.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.use_clamp_overlap = clamp
    m.harden_normals = False
    return m


def add_subsurf(ob, levels=2, render=None):
    m = ob.modifiers.new("Subdivision", "SUBSURF")
    m.levels = levels
    m.render_levels = levels if render is None else render
    return m


def add_solidify(ob, thickness=0.004, offset=-1.0):
    m = ob.modifiers.new("Solidify", "SOLIDIFY")
    m.thickness = thickness
    m.offset = offset
    return m


def add_mirror(ob, axis=(False, True, False), merge=0.0005):
    m = ob.modifiers.new("Mirror", "MIRROR")
    m.use_axis = axis
    m.use_mirror_merge = True
    m.merge_threshold = merge
    return m


# --------------------------------------------------------------------------- #
# materials
# --------------------------------------------------------------------------- #

def material(name, reuse=True):
    """Get-or-create a node material; returns (mat, nodetree, principled|None)."""
    mat = bpy.data.materials.get(name)
    if mat and not reuse:
        bpy.data.materials.remove(mat)
        mat = None
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (200, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat, nt, bsdf


def assign(ob, mat, slot=0):
    while len(ob.data.materials) <= slot:
        ob.data.materials.append(None)
    ob.data.materials[slot] = mat
    return ob


def node(nt, kind, loc=(0, 0), **props):
    n = nt.nodes.new(kind)
    n.location = loc
    for k, v in props.items():
        if "." in k:
            head, tail = k.split(".", 1)
            setattr(getattr(n, head), tail, v)
        else:
            setattr(n, k, v)
    return n


def sock(n, key):
    return n.inputs[key] if isinstance(key, str) else n.inputs[key]


def wire(nt, a, aout, b, bin_):
    out = a.outputs[aout] if isinstance(aout, (str, int)) else aout
    inp = b.inputs[bin_] if isinstance(bin_, (str, int)) else bin_
    return nt.links.new(out, inp)


def set_defaults(n, **kw):
    for k, v in kw.items():
        key = k.replace("_", " ")
        if key in n.inputs:
            n.inputs[key].default_value = v
        elif k in n.inputs:
            n.inputs[k].default_value = v
        else:
            raise KeyError(f"{n.bl_idname} has no input {k!r} / {key!r}: "
                           f"{[s.name for s in n.inputs]}")
    return n


# --------------------------------------------------------------------------- #
# misc
# --------------------------------------------------------------------------- #

def move_to(ob, coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob


def deg(d):
    return math.radians(d)
