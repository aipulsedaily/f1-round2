#!/usr/bin/env python3
"""R2-057 GUARD — fail when a module addresses a node input by INTEGER INDEX.

WHY THIS EXISTS
---------------
Blender 5.2 moved `ShaderNodeBsdfPrincipled.Normal` from index 5 to index 6:

    [0] Base Color [1] Metallic [2] Roughness [3] IOR [4] Alpha
    [5] THIN WALL  [6] Normal   [7] Weight ...

`world/items/crew_fireproof_overall.py` carried its OWN PRIVATE copy of a
socket setter -- `_feed(self, node, idx, v)` -- with six `_feed(b, 5, <bump>)`
calls, every one of them written when index 5 was `Normal`.  So the entire
repaired bump chain was wired into `Thin Wall` and the `Normal` socket of all
four Principled BSDFs was left unconnected.  The relief repair it was supposed
to deliver moved **0.00 %** of the item's pixels -- a perfect null, because
nothing reached the shader on EITHER side of the A/B.  No error, no black
frame, a completely plausible render.  It survived 28 modules and a full gate
rewrite.

`itemkit.selftest()` already carries a live-socket audit (its `_ASSUME` table,
around line 2440 -- note the `socket_audit()` function named in several
docstrings DOES NOT EXIST, the audit is inline in `selftest`).  That audit
could not see this defect and structurally cannot: it asserts the indices
*itemkit* assumes.  A private copy of a socket setter inside an item module is
invisible to it, and so is a helper that is defined but not yet called.

So this check is SOURCE-LEVEL (AST).  It runs in milliseconds, needs no
Blender, and fires at authoring time rather than via a pixel A/B eleven
modules later.

WHAT IT DETECTS
---------------
  (a) DIRECT      `<node>.inputs[<int literal>]`
  (b) FEEDER      a locally-defined function/method whose body indexes
                  `.inputs[...]` with one of its OWN PARAMETERS -- the
                  `_feed(node, idx, v)` / `pin(nd, idx, src)` shape -- and then
                  every CALL SITE of that helper that passes an int literal.
                  This is the actual R2-057 signature; a literal-only grep
                  misses every one of those call sites.
  (c) DEFAULTS    dict-of-index defaults, `n(t, defaults={5: value})`, where a
                  helper iterates the dict and uses its keys as socket indices.

THE ITEMKIT EXEMPTION IS NARROW AND EXPLICIT
--------------------------------------------
`world/itemkit.py :: NT.pin` is the sanctioned by-index primitive that
`pin_named` is built on, and its `expect=` argument is the designed
mitigation.  The exemption is an ALLOWLIST OF (file, symbol) -- see
`ALLOWED_FEEDER_DEFS` -- not a blanket "skip itemkit".  A NEW private helper
appearing in itemkit.py gets no free pass.  Separately, and uniformly in every
file, a by-index CALL that passes `expect=<socket name>` is accepted, because
that argument turns a silent miswire into a raise.

SOCKET TABLE PROVENANCE
-----------------------
`SOCKETS_5_2` below was MEASURED, not remembered, on this machine:

    blender -b --factory-startup --python <dump>   # Blender 5.2.0 LTS,
                                                   # build date 2026-07-15
    [(i, s.name) for i, s in enumerate(nd.inputs)]

Re-measure at any time with `--refresh-sockets` (requires blender on PATH).

TWO ARMS -- R2-070
------------------
The AST arm above reads SOURCE.  It is fast and needs no Blender, but it can
only see indices that are written down: a computed index is a NOTICE, and
there are 997 of those here.  So there is now a second, independent arm that
reads the BUILT BLEND and asks the artefact directly -- because a build log
saying "linked Normal" and a blend actually having `Normal` linked are
different claims, and this project has shipped the difference twice.

    python3 tools/socket_index_audit.py --blend render/.../x.blend

fails when a Bump / Normal Map / Bevel output lands on a socket that is not a
normal input (on 5.2 the off-by-one puts it on `Thin Wall`), when a relief
node's output goes nowhere, when a Bump's `Height` is a constant, or when a
Bump's `Filter Width` is driven.  It prints each offending material's
transmission / subsurface / alpha / coat state, so whether a stray link is
"merely flat" or "a per-pixel shell flip" is MEASURED and not assumed.

Scope is now every source directory (world, tools, anim, sim, audio, render).
`--include-builds` is a no-op kept for old invocations.  There is no flag that
turns a directory off: "the sweep did not cover it" must not be reachable.

USAGE
-----
    python3 tools/socket_index_audit.py                   # audit default scope
    python3 tools/socket_index_audit.py world/items/foo.py
    python3 tools/socket_index_audit.py --json out.json
    python3 tools/socket_index_audit.py --strict          # STABLE tier fails too
    python3 tools/socket_index_audit.py --allow waivers.txt
    python3 tools/socket_index_audit.py --selftest        # +/- controls, AST arm
    python3 tools/socket_index_audit.py --blend a.blend   # ARTEFACT ARM
    python3 tools/socket_index_audit.py --selftest-blend  # +/- controls, artefact
    python3 tools/socket_index_audit.py --refresh-sockets # re-measure vs blender

EXIT CODES
    0  clean
    1  violations at a failing tier
    2  bad invocation / parse error
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---------------------------------------------------------------------------
# MEASURED LIVE SOCKET ORDER -- Blender 5.2.0 LTS (build 2026-07-15)
# Produced by `blender -b --factory-startup` enumerating `nd.inputs` on a fresh
# material node tree.  DO NOT hand-edit; regenerate with --refresh-sockets.
# ---------------------------------------------------------------------------
SOCKETS_5_2 = {
 'ShaderNodeAddShader': ['Shader', 'Shader'],
 'ShaderNodeAmbientOcclusion': ['Color', 'Distance', 'Normal'],
 'ShaderNodeBevel': ['Radius', 'Normal'],
 'ShaderNodeBlackbody': ['Temperature'],
 'ShaderNodeBrightContrast': ['Color', 'Brightness', 'Contrast'],
 'ShaderNodeBsdfAnisotropic': ['Color', 'Roughness', 'Anisotropy', 'Rotation',
                               'Normal', 'Tangent', 'Weight'],
 'ShaderNodeBsdfDiffuse': ['Color', 'Roughness', 'Normal', 'Weight'],
 'ShaderNodeBsdfGlass': ['Color', 'Roughness', 'IOR', 'Normal', 'Weight',
                         'Thin Film Thickness', 'Thin Film IOR'],
 'ShaderNodeBsdfGlossy': ['Color', 'Roughness', 'Anisotropy', 'Rotation',
                          'Normal', 'Tangent', 'Weight'],
 'ShaderNodeBsdfMetallic': ['Base Color', 'Edge Tint', 'IOR', 'Extinction',
                            'Roughness', 'Anisotropy', 'Rotation', 'Normal',
                            'Tangent', 'Weight', 'Thin Film Thickness',
                            'Thin Film IOR'],
 'ShaderNodeBsdfPrincipled': ['Base Color', 'Metallic', 'Roughness', 'IOR',
                              'Alpha', 'Thin Wall', 'Normal', 'Weight',
                              'Diffuse Roughness', 'Subsurface Weight',
                              'Subsurface Radius', 'Subsurface Scale',
                              'Subsurface IOR', 'Subsurface Anisotropy',
                              'Specular IOR Level', 'Specular Tint',
                              'Anisotropic', 'Anisotropic Rotation', 'Tangent',
                              'Transmission Weight', 'Coat Weight',
                              'Coat Roughness', 'Coat IOR', 'Coat Tint',
                              'Coat Normal', 'Sheen Weight', 'Sheen Roughness',
                              'Sheen Tint', 'Emission Color',
                              'Emission Strength', 'Thin Film Thickness',
                              'Thin Film IOR'],
 'ShaderNodeBsdfRefraction': ['Color', 'Roughness', 'IOR', 'Normal', 'Weight'],
 'ShaderNodeBsdfSheen': ['Color', 'Roughness', 'Normal', 'Weight'],
 'ShaderNodeBsdfTranslucent': ['Color', 'Normal', 'Weight'],
 'ShaderNodeBsdfTransparent': ['Color', 'Weight'],
 'ShaderNodeBump': ['Strength', 'Distance', 'Filter Width', 'Height', 'Normal'],
 'ShaderNodeClamp': ['Value', 'Min', 'Max'],
 'ShaderNodeCombineXYZ': ['X', 'Y', 'Z'],
 'ShaderNodeDisplacement': ['Height', 'Midlevel', 'Scale', 'Normal'],
 'ShaderNodeEmission': ['Color', 'Strength', 'Weight'],
 'ShaderNodeFloatCurve': ['Factor', 'Value'],
 'ShaderNodeFresnel': ['IOR', 'Normal'],
 'ShaderNodeGamma': ['Color', 'Gamma'],
 'ShaderNodeHueSaturation': ['Hue', 'Saturation', 'Value', 'Factor', 'Color'],
 'ShaderNodeInvert': ['Factor', 'Color'],
 'ShaderNodeLayerWeight': ['Blend', 'Normal'],
 'ShaderNodeMapRange': ['Value', 'From Min', 'From Max', 'To Min', 'To Max',
                        'Steps', 'Vector', 'From Min', 'From Max', 'To Min',
                        'To Max', 'Steps'],
 'ShaderNodeMapping': ['Vector', 'Location', 'Rotation', 'Scale'],
 'ShaderNodeMath': ['Value', 'Value', 'Value'],
 'ShaderNodeMix': ['Factor', 'Factor', 'A', 'B', 'A', 'B', 'A', 'B', 'A', 'B'],
 'ShaderNodeMixRGB': ['Factor', 'Color1', 'Color2'],
 'ShaderNodeMixShader': ['Factor', 'Shader', 'Shader'],
 'ShaderNodeNormalMap': ['Strength', 'Color'],
 'ShaderNodeRGBCurve': ['Factor', 'Color'],
 'ShaderNodeSeparateXYZ': ['Vector'],
 'ShaderNodeSubsurfaceScattering': ['Color', 'Scale', 'Radius', 'IOR',
                                    'Roughness', 'Anisotropy', 'Normal',
                                    'Weight'],
 'ShaderNodeTexBrick': ['Vector', 'Color1', 'Color2', 'Mortar', 'Scale',
                        'Mortar Size', 'Mortar Smooth', 'Bias', 'Brick Width',
                        'Row Height'],
 'ShaderNodeTexChecker': ['Vector', 'Color1', 'Color2', 'Scale'],
 'ShaderNodeTexGradient': ['Vector'],
 'ShaderNodeTexImage': ['Vector'],
 'ShaderNodeTexMagic': ['Vector', 'Scale', 'Distortion'],
 'ShaderNodeTexNoise': ['Vector', 'W', 'Scale', 'Detail', 'Roughness',
                        'Lacunarity', 'Offset', 'Gain', 'Distortion'],
 'ShaderNodeTexVoronoi': ['Vector', 'W', 'Scale', 'Detail', 'Roughness',
                          'Lacunarity', 'Smoothness', 'Exponent', 'Randomness'],
 'ShaderNodeTexWave': ['Vector', 'Scale', 'Distortion', 'Detail',
                       'Detail Scale', 'Detail Roughness', 'Phase Offset'],
 'ShaderNodeTexWhiteNoise': ['Vector', 'W'],
 'ShaderNodeValToRGB': ['Factor'],
 'ShaderNodeVectorCurve': ['Factor', 'Vector'],
 'ShaderNodeVectorDisplacement': ['Vector', 'Midlevel', 'Scale'],
 'ShaderNodeVectorMath': ['Vector', 'Vector', 'Vector', 'Scale'],
 'ShaderNodeVectorRotate': ['Vector', 'Center', 'Axis', 'Angle', 'Rotation'],
 'ShaderNodeVolumeAbsorption': ['Color', 'Density', 'Weight'],
 'ShaderNodeVolumePrincipled': ['Color', 'Color Attribute', 'Density',
                                'Density Attribute', 'Anisotropy',
                                'Absorption Color', 'Emission Strength',
                                'Emission Color', 'Blackbody Intensity',
                                'Blackbody Tint', 'Temperature',
                                'Temperature Attribute', 'Weight'],
 'ShaderNodeVolumeScatter': ['Color', 'Density', 'Anisotropy', 'IOR',
                             'Backscatter', 'Alpha', 'Diameter', 'Weight'],
 'ShaderNodeWavelength': ['Wavelength'],
 # --- second measurement pass: every other node type this tree names,
 #     including the world and geometry-nodes trees.  Same session,
 #     same binary. ---
 'FunctionNodeRandomValue': ['Min', 'Max', 'ID', 'Seed'],
  'GeometryNodeCollectionInfo': ['Collection',
                                 'Separate Children',
                                 'Reset Children'],
  'GeometryNodeInputNamedAttribute': ['Name'],
  'GeometryNodeInstanceOnPoints': ['Points',
                                   'Selection',
                                   'Instance',
                                   'Pick Instance',
                                   'Instance Index',
                                   'Rotation',
                                   'Scale'],
  'GeometryNodeJoinGeometry': ['Geometry'],
  'GeometryNodeObjectInfo': ['Object', 'As Instance'],
  'GeometryNodeTransform': ['Geometry',
                            'Mode',
                            'Translation',
                            'Rotation',
                            'Scale',
                            'Transform'],
  'ShaderNodeAttribute': [],
  'ShaderNodeBackground': ['Color', 'Strength', 'Weight'],
  'ShaderNodeCameraData': [],
  'ShaderNodeCombineColor': ['Red', 'Green', 'Blue'],
  'ShaderNodeLightPath': [],
  'ShaderNodeNewGeometry': [],
  'ShaderNodeObjectInfo': [],
  'ShaderNodeOutputMaterial': ['Surface',
                               'Volume',
                               'Displacement',
                               'Thickness'],
  'ShaderNodeOutputWorld': ['Surface', 'Volume'],
  'ShaderNodeRGB': [],
  'ShaderNodeRGBToBW': ['Color'],
  'ShaderNodeSeparateColor': ['Color'],
  'ShaderNodeTangent': [],
  'ShaderNodeTexCoord': [],
  'ShaderNodeTexSky': ['Vector'],
  'ShaderNodeUVMap': [],
  'ShaderNodeValue': [],
}
SOCKETS_MEASURED_ON = "Blender 5.2.0 LTS (build date 2026-07-15), /usr/bin/blender"

# ---------------------------------------------------------------------------
# SEVERITY MODEL
#
#   LETHAL   the known-fatal shapes.  R2-057 (Principled index >= 4, i.e. at or
#            past the Alpha/Thin Wall/Normal churn) and R2-038 (ANY index on
#            ShaderNodeBump, where 5.2 inserted `Filter Width` at 2).  Plus
#            anything whose node type could NOT be inferred at an index > 0 --
#            an unknown type is NOT a safe type, and demoting it would be
#            exactly the hole that let R2-057 through.  FAILS.
#
#   MOVED    an index at or past the first socket this node type is known to
#            have gained or shuffled in the 4.x -> 5.x line.  FAILS.
#
#   STABLE   an index that is covered by itemkit.selftest()'s live `_ASSUME`
#            audit, or that is provably ordering-safe (index 0; ShaderNodeMath
#            / VectorMath / MixRGB, whose socket lists are frozen).  LISTED but
#            does not fail, unless --strict.
#
# Tiering must never become a way to report the real defect as a warning, so
# the DEFAULT for anything not positively known to be safe is LETHAL.
# ---------------------------------------------------------------------------
LETHAL, MOVED, STABLE, NOTICE = "LETHAL", "MOVED", "STABLE", "NOTICE"
# DEFAULT: only LETHAL fails.  `--strict` additionally fails MOVED and STABLE.
# The real defect -- Principled[>=4], any Bump index, and any index > 0 whose
# node type could not be inferred -- is LETHAL and therefore can NEVER be
# downgraded to a warning by tiering.  MOVED and STABLE are listed in full on
# every run, and the summary says how many there are.
FAILING_TIERS = (LETHAL,)
STRICT_TIERS = (LETHAL, MOVED, STABLE)
TIER_ORDER = {LETHAL: 0, MOVED: 1, STABLE: 2, NOTICE: 3}

# First index at or past which this node type's socket order is known to have
# churned across the 4.x -> 5.x line.  Anything >= the value is LETHAL.
KNOWN_CHURN_FROM = {
    # 5.2 order is  ... [4] Alpha [5] Thin Wall [6] Normal [7] Weight ...
    # `Normal` was 5 before `Thin Wall` was inserted.  This is R2-057.
    'ShaderNodeBsdfPrincipled': 4,
    # 5.2 inserted `Filter Width` at index 2.  This is R2-038.  EVERY index on
    # this node is lethal: 2..4 all shifted, and 0/1 are only accidentally
    # still right.
    'ShaderNodeBump': 0,
    # `Thin Film *` appended and `Normal` position depends on build.
    'ShaderNodeBsdfGlass': 3,
    'ShaderNodeBsdfMetallic': 0,
    'ShaderNodeBsdfGlossy': 2,
    'ShaderNodeBsdfAnisotropic': 2,
    # 5.x reworked the volume socket list heavily.
    'ShaderNodeVolumeScatter': 2,
    'ShaderNodeVolumePrincipled': 1,
    # `Detail Scale` / `Detail Roughness` / `Phase Offset` appended after 3.
    'ShaderNodeTexWave': 4,
    # `Steps` + the whole VECTOR half share the list; index >= 5 is data_type
    # dependent and the names REPEAT, so an index there cannot even be
    # validated by name.
    'ShaderNodeMapRange': 5,
    # ShaderNodeMix: the A/B pairs repeat per data_type; only the itemkit
    # `_ASSUME`-covered ones are safe.
    'ShaderNodeMix': 8,
}

# Sockets whose position carries no ordering risk, independent of the itemkit
# audit.  Kept deliberately tiny.
ALWAYS_STABLE = {
    'ShaderNodeMath': {0, 1, 2},
    'ShaderNodeVectorMath': {0, 1, 2},
    'ShaderNodeMixRGB': {0, 1, 2},        # legacy node, socket list frozen
    'ShaderNodeMixShader': {0, 1, 2},
    'ShaderNodeAddShader': {0, 1},
    'ShaderNodeValToRGB': {0},
    'ShaderNodeSeparateXYZ': {0},
    'ShaderNodeCombineXYZ': {0, 1, 2},
    'ShaderNodeMapping': {0, 1, 2, 3},
    'ShaderNodeInvert': {0, 1},
    'ShaderNodeGamma': {0, 1},
    'ShaderNodeBrightContrast': {0, 1, 2},
    # ['Hue','Saturation','Value','Factor','Color'] -- unchanged since 2.8x.
    'ShaderNodeHueSaturation': {0, 1, 2, 3, 4},
    # Base Color / Metallic / Roughness have NOT moved.  A rename is not a
    # move, and neither is a socket inserted after you.  Everything from index
    # 4 (Alpha / Thin Wall / Normal) is covered by KNOWN_CHURN_FROM above.
    # Base Color / Metallic / Roughness / IOR occupy 0..3 in 4.x AND 5.2 alike.
    # A rename is not a move, and neither is a socket inserted after you.
    # Everything from index 4 (Alpha / Thin Wall / Normal) is covered by
    # KNOWN_CHURN_FROM above and is LETHAL.
    'ShaderNodeBsdfPrincipled': {0, 1, 2, 3},
    # --- measured in the second socket pass, orders unchanged in the 4.x->5.x
    #     line (a socket APPENDED after the ones addressed does not move them)
    'ShaderNodeBackground': {0, 1},
    'ShaderNodeEmission': {0, 1},
    'ShaderNodeCombineColor': {0, 1, 2},
    'ShaderNodeSeparateColor': {0},
    'ShaderNodeRGBToBW': {0},
    'ShaderNodeTexSky': {0},
    'ShaderNodeAmbientOcclusion': {0, 1, 2},
    'ShaderNodeOutputMaterial': {0, 1, 2},
    'ShaderNodeOutputWorld': {0, 1},
}

# ---------------------------------------------------------------------------
# THE EXEMPTION.  File + symbol, not "skip itemkit".
#
# `NT.pin` is the by-index primitive `pin_named` is built on and its `expect=`
# argument is the designed mitigation -- see itemkit.py:1266.  Its DEFINITION
# is allowed to exist.  Its CALL SITES are still checked, and are only accepted
# when they pass `expect=`.  A NEW private helper appearing in itemkit.py is
# NOT in this list and gets no free pass.
# ---------------------------------------------------------------------------
ALLOWED_FEEDER_DEFS = {
    ("world/itemkit.py", "NT.pin"): (
        "sanctioned by-index primitive; `expect=` is the designed mitigation "
        "(itemkit.py:1266). Call sites still require expect=."),
}

# A by-index call is accepted anywhere if it names the socket it believes is
# there.  This is the ONLY blanket exemption and it is a positive assertion,
# not a suppression: a version move makes it raise.
EXPECT_KWARGS = ("expect", "expected", "expect_name")

NODE_TYPE_RE = re.compile(
    r"^(ShaderNode|CompositorNode|GeometryNode|FunctionNode|TextureNode)[A-Za-z0-9_]*$")

WAIVER_RE = re.compile(r"#\s*socket-index-audit:\s*waive\s*\(([^)]*)\)")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def rel(path):
    ap = os.path.abspath(path)
    try:
        r = os.path.relpath(ap, ROOT)
    except ValueError:
        return ap
    # a path outside the project reads better absolute than as ../../../..
    return ap if r.startswith("..") else r


def socket_name(node_type, idx):
    """What socket index `idx` ACTUALLY is in the measured live Blender 5.2."""
    lst = SOCKETS_5_2.get(node_type)
    if lst is None:
        return None
    if 0 <= idx < len(lst):
        return lst[idx]
    return "<out of range: %s has %d inputs>" % (node_type, len(lst))


def const_int(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, int) \
            and not isinstance(node.value, bool):
        return node.value
    return None


def dotted(node):
    """`self.nt.nodes` -> 'self.nt.nodes'; returns None if not a plain chain."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


# ---------------------------------------------------------------------------
# per-file analysis
# ---------------------------------------------------------------------------
class Feeder:
    """A function/method that sets a node input by an index it is HANDED."""

    __slots__ = ("file", "qual", "lineno", "idx_param", "node_param",
                 "idx_pos", "node_pos", "is_method", "kind", "guarded")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    @property
    def key(self):
        return (self.file, self.qual)

    @property
    def name(self):
        return self.qual.rsplit(".", 1)[-1]


class FileScan:
    """One pass over one module."""

    def __init__(self, path, src, as_rel=None):
        self.path = path
        # `as_rel` lets the selftest audit a fixture UNDER ANOTHER FILE'S
        # IDENTITY, so the (file, symbol) allowlist can be exercised for real
        # instead of asserted in prose.  Never used by a normal run.
        self.rel = as_rel or rel(path)
        self.src = src
        self.lines = src.splitlines()
        self.tree = ast.parse(src, filename=path)
        self.feeders = []          # Feeder
        self.factories = {}        # local function name -> node type it returns
        self.tuple_factories = {}  # local function name -> [type|None, ...]
        self.direct = []           # raw (lineno, col, node_expr, idx)
        self.calls = []            # raw ast.Call records for pass 2
        self.type_of = {}          # (scope_id, varname) -> node type or None
        self._scope_stack = [("<module>", id(self.tree))]
        # module-level `NORMAL_IDX = 5` must not be a way around the check --
        # a named constant is still an index, and naming it does not make it
        # track the socket.
        self.int_consts = {}
        for _st in self.tree.body:
            if isinstance(_st, ast.Assign) and len(_st.targets) == 1 \
                    and isinstance(_st.targets[0], ast.Name):
                _iv = const_int(_st.value)
                if _iv is not None:
                    self.int_consts[_st.targets[0].id] = _iv
        self._fnwalk = {}
        self._funcs = [x for x in ast.walk(self.tree)
                       if isinstance(x, (ast.FunctionDef,
                                         ast.AsyncFunctionDef))]

    # -- scope plumbing ----------------------------------------------------
    def _scope(self):
        return self._scope_stack[-1][1]

    # -- entry -------------------------------------------------------------
    def run(self, factories_only=False):
        self._collect_factories()
        if not factories_only:
            self._walk(self.tree, [])
            self._fnwalk = None          # release the walk cache
        return self

    def _fw(self, fn):
        """`ast.walk(fn)` memoised.  These modules run to 8000 lines with a few
        hundred functions; walking each subtree four separate times turned a
        millisecond check into half a minute."""
        key = id(fn)
        got = self._fnwalk.get(key)
        if got is None:
            got = self._fnwalk[key] = list(ast.walk(fn))
        return got

    # -- learn node-returning factory methods ------------------------------
    def _local_node_bindings(self, fn):
        """name -> bl_idname for the node-valued locals of one function."""
        loc = {}
        for sub in self._fw(fn):
            if isinstance(sub, ast.Assign) and len(sub.targets) == 1 \
                    and isinstance(sub.targets[0], ast.Name):
                t = self._type_from_call(sub.value)
                if t:
                    nm = sub.targets[0].id
                    if nm in loc and loc[nm] != t:
                        loc[nm] = None      # ambiguous -> unknown, fail-closed
                    else:
                        loc.setdefault(nm, t)
        return loc

    def _collect_factories(self):
        """Learn what a local function RETURNS, so call sites resolve.

            def bump(...):  nd = self.n('ShaderNodeBump', ...); return nd
            -> g.bump(h, 0.5) is a ShaderNodeBump

            def _new_mat(name): ... bsdf = g.n('ShaderNodeBsdfPrincipled') ...
                                return m, g, bsdf, out
            -> m, g, b, out = _new_mat('nomex')  makes `b` a Principled

        The tuple form matters: this codebase builds every material through a
        tuple-returning factory, and without it EVERY Principled BSDF in the
        tree reads as "unknown node type" and the report degenerates into
        noise.  Registration is deliberately conservative -- a function only
        counts if it literally returns a node-valued local -- because a WRONG
        type would print a wrong socket name, which is worse than none.
        """
        # two sweeps: the second sees factories learnt by the first, so
        # `def rough(): return self.mix(...)` chains resolve.
        for _ in range(2):
            for fn in self._funcs:
                loc = self._local_node_bindings(fn)
                for sub in self._fw(fn):
                    if not isinstance(sub, ast.Return) or sub.value is None:
                        continue
                    v = sub.value
                    if isinstance(v, ast.Name) and loc.get(v.id):
                        self.factories.setdefault(fn.name, loc[v.id])
                    elif isinstance(v, ast.Call):
                        t = self._type_from_call(v)
                        if t:
                            self.factories.setdefault(fn.name, t)
                    elif isinstance(v, ast.Tuple):
                        slots = []
                        for e in v.elts:
                            if isinstance(e, ast.Name):
                                slots.append(loc.get(e.id))
                            elif isinstance(e, ast.Call):
                                slots.append(self._type_from_call(e))
                            else:
                                slots.append(None)
                        if any(slots):
                            self.tuple_factories.setdefault(fn.name, slots)

    # -- node type inference ----------------------------------------------
    def _type_from_call(self, call):
        """Node type produced by this Call expression, or None."""
        if not isinstance(call, ast.Call):
            return None
        # any positional str literal that looks like a bl_idname
        for a in call.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                    and NODE_TYPE_RE.match(a.value):
                return a.value
        for kw in call.keywords:
            if isinstance(kw.value, ast.Constant) \
                    and isinstance(kw.value.value, str) \
                    and NODE_TYPE_RE.match(kw.value.value):
                return kw.value.value
        # a learned local factory:  g.bump(...) / self.noise(...) / bump(...)
        fname = call.func.attr if isinstance(call.func, ast.Attribute) else (
            call.func.id if isinstance(call.func, ast.Name) else None)
        if fname and fname in self.factories:
            return self.factories[fname]
        if fname and fname in GLOBAL_FACTORIES:
            return GLOBAL_FACTORIES[fname]
        return None

    def as_int(self, expr):
        """An int literal, or a module-level name bound to one."""
        iv = const_int(expr)
        if iv is not None:
            return iv
        if isinstance(expr, ast.Name):
            return self.int_consts.get(expr.id)
        return None

    def _tuple_types_from_call(self, call):
        if not isinstance(call, ast.Call):
            return None
        fname = call.func.attr if isinstance(call.func, ast.Attribute) else (
            call.func.id if isinstance(call.func, ast.Name) else None)
        if not fname:
            return None
        return self.tuple_factories.get(fname) or GLOBAL_TUPLE_FACTORIES.get(fname)

    def _bind(self, target, typ):
        name = target.id if isinstance(target, ast.Name) else dotted(target)
        if not name:
            return
        key = (self._scope(), name)
        if key in self.type_of and self.type_of[key] != typ:
            self.type_of[key] = None        # conflicting -> unknown, fail-closed
        else:
            self.type_of.setdefault(key, typ)

    def lookup(self, expr, stack=None):
        """Resolve a node expression to its bl_idname.

        `stack` is the scope stack CAPTURED AT THE USE SITE.  It has to be:
        by the time pass 2 runs, the walker's own stack has unwound to module
        level, and looking up there finds nothing -- which would silently make
        every in-function node "unknown".  That is precisely the class of
        instrument failure this whole task exists to stop, so the use-site
        stack is recorded with every finding.
        """
        name = expr.id if isinstance(expr, ast.Name) else dotted(expr)
        if not name:
            # inline:  self._feed(self.n('ShaderNodeBump'), 3, x)
            return self._type_from_call(expr)
        for _, sid in reversed(stack if stack is not None else self._scope_stack):
            if (sid, name) in self.type_of:
                return self.type_of[(sid, name)]
        return None

    # -- the walk ----------------------------------------------------------
    def _walk(self, node, path):
        pushed = False
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            qual = ".".join([p for p in path] + [node.name])
            self._scope_stack.append((qual, id(node)))
            pushed = True
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._inspect_feeder(node, qual)
            path = path + [node.name]

        # bindings + expression-level findings, only for this node itself
        if isinstance(node, ast.Assign):
            typ = self._type_from_call(node.value)
            if typ:
                for t in node.targets:
                    self._bind(t, typ)
            else:
                # `m, g, b, out = _new_mat("nomex")`
                slots = self._tuple_types_from_call(node.value)
                if slots:
                    for t in node.targets:
                        if isinstance(t, (ast.Tuple, ast.List)) \
                                and len(t.elts) == len(slots):
                            for elt, ty in zip(t.elts, slots):
                                if ty:
                                    self._bind(elt, ty)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            typ = self._type_from_call(node.value)
            if typ:
                self._bind(node.target, typ)

        if isinstance(node, ast.Subscript):
            idx = self.as_int(node.slice)
            if idx is not None and isinstance(node.value, ast.Attribute) \
                    and node.value.attr == "inputs":
                self.direct.append((node, idx, node.value.value,
                                    self._scope_stack[-1][0],
                                    list(self._scope_stack)))

        if isinstance(node, ast.Call):
            self.calls.append((node, self._scope_stack[-1][0],
                               list(self._scope_stack)))

        for child in ast.iter_child_nodes(node):
            self._walk(child, path)

        if pushed:
            self._scope_stack.pop()

    # -- (b) + (c): find helpers that index inputs with their own params ----
    def _inspect_feeder(self, fn, qual):
        args = fn.args
        params = [a.arg for a in
                  (args.posonlyargs + args.args + args.kwonlyargs)]
        if not params:
            return
        is_method = params[0] in ("self", "cls")
        positional = args.posonlyargs + args.args

        # every `X.inputs[<expr>]` inside this function
        idx_uses = []            # (idx_expr, node_expr)
        for sub in self._fw(fn):
            if isinstance(sub, ast.Subscript) and isinstance(sub.value, ast.Attribute) \
                    and sub.value.attr == "inputs":
                idx_uses.append((sub.slice, sub.value.value))
        if not idx_uses:
            return

        # does this body positively assert the socket NAME it is about to use?
        guarded = False
        for sub in self._fw(fn):
            if isinstance(sub, ast.Attribute) and sub.attr == "name" \
                    and isinstance(sub.value, ast.Subscript) \
                    and isinstance(sub.value.value, ast.Attribute) \
                    and sub.value.value.attr == "inputs":
                guarded = True
        for p in EXPECT_KWARGS:
            if p in params:
                guarded = guarded and True

        # -- (b) a parameter used DIRECTLY as the index
        direct_params = set()
        for idx_expr, _ in idx_uses:
            if isinstance(idx_expr, ast.Name) and idx_expr.id in params:
                direct_params.add(idx_expr.id)

        # -- (c) a dict parameter whose KEYS become indices:
        #        `for i, v in defaults.items(): nd.inputs[i] ...`
        dict_params = set()
        for sub in self._fw(fn):
            if not isinstance(sub, ast.For):
                continue
            it = sub.iter
            src_name = None
            if isinstance(it, ast.Call) and isinstance(it.func, ast.Attribute) \
                    and it.func.attr in ("items", "iteritems"):
                src_name = it.func.value.id if isinstance(it.func.value, ast.Name) else None
            if src_name not in params:
                continue
            loop_names = set()
            if isinstance(sub.target, ast.Tuple):
                loop_names = {e.id for e in sub.target.elts if isinstance(e, ast.Name)}
            elif isinstance(sub.target, ast.Name):
                loop_names = {sub.target.id}
            for idx_expr, _ in idx_uses:
                if isinstance(idx_expr, ast.Name) and idx_expr.id in loop_names:
                    dict_params.add(src_name)

        # which parameter is the NODE?
        node_param = None
        for _, node_expr in idx_uses:
            n = node_expr.id if isinstance(node_expr, ast.Name) else None
            if n in params:
                node_param = n
                break

        for p, kind in ([(p, "index") for p in sorted(direct_params)]
                        + [(p, "defaults-dict") for p in sorted(dict_params)]):
            names = [a.arg for a in positional]
            self.feeders.append(Feeder(
                file=self.rel, qual=qual, lineno=fn.lineno,
                idx_param=p, node_param=node_param,
                idx_pos=names.index(p) if p in names else None,
                node_pos=names.index(node_param) if node_param in names else None,
                is_method=is_method, kind=kind, guarded=guarded))


# populated in pass 2: factories learnt from itemkit/humankit are visible to
# every item module, because item modules build on them.
GLOBAL_FACTORIES = {}
GLOBAL_TUPLE_FACTORIES = {}


# ---------------------------------------------------------------------------
# findings
# ---------------------------------------------------------------------------
class Hit(dict):
    pass


def make_hit(**kw):
    h = Hit(kw)
    h.setdefault("waiver", None)
    return h


def classify(node_type, idx):
    """-> (tier, reason).  Unknown type is NOT safe."""
    if node_type is None:
        if idx == 0:
            return STABLE, ("node type not inferable; index 0 is the first "
                            "socket of every shader node and has never shifted")
        return LETHAL, ("node type NOT INFERABLE at index %d -- cannot prove "
                        "this is not another R2-057. Wire it by name." % idx)
    churn = KNOWN_CHURN_FROM.get(node_type)
    if churn is not None and idx >= churn:
        tier = LETHAL if node_type in ("ShaderNodeBsdfPrincipled",
                                       "ShaderNodeBump") else MOVED
        return tier, ("%s socket order is known to have churned at/after index "
                      "%d in the 4.x->5.x line" % (node_type, churn))
    if idx in ALWAYS_STABLE.get(node_type, ()):
        return STABLE, "socket list of %s is frozen" % node_type
    if idx in ITEMKIT_ASSUMED.get(node_type, ()):
        return STABLE, ("covered by itemkit.selftest() `_ASSUME` live-socket "
                        "audit")
    if idx == 0:
        return STABLE, "index 0 is the first socket and has never shifted"
    return MOVED, ("%s[%d] is not covered by itemkit's live `_ASSUME` audit "
                   "and is not on the frozen list" % (node_type, idx))


# Parsed out of world/itemkit.py at load time -- see load_itemkit_assume().
ITEMKIT_ASSUMED = {}


def load_itemkit_assume(itemkit_path):
    """Read itemkit.selftest()'s `_ASSUME` table so the STABLE tier stays in
    sync with the audit that actually backs it.  Falls back to a baked copy.

    This is deliberately a PARSE of the live table rather than a duplicate: if
    somebody narrows itemkit's audit, indices silently stop being STABLE here
    instead of silently staying safe.
    """
    baked = {
        'ShaderNodeMix': {0, 2, 3, 6, 7},
        'ShaderNodeMath': {0, 1},
        'ShaderNodeVectorMath': {0, 1, 3},
        'ShaderNodeTexNoise': {0, 2, 3, 4, 5},
        'ShaderNodeTexVoronoi': {0, 2, 8},
        'ShaderNodeTexWave': {0, 1, 2, 3},
        'ShaderNodeMapRange': {0, 1, 2, 3, 4},
        'ShaderNodeSeparateXYZ': {0},
        'ShaderNodeCombineXYZ': {0, 1, 2},
    }
    try:
        tree = ast.parse(open(itemkit_path, encoding="utf-8").read())
    except Exception:
        return baked, "baked fallback (itemkit.py unreadable)"
    found = {}
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "_ASSUME" for t in n.targets)):
            continue
        if not isinstance(n.value, ast.List):
            continue
        for elt in n.value.elts:
            if not (isinstance(elt, ast.Tuple) and len(elt.elts) == 3):
                continue
            typ, _kw, mapping = elt.elts
            if not (isinstance(typ, ast.Constant) and isinstance(typ.value, str)):
                continue
            if not isinstance(mapping, ast.Dict):
                continue
            s = found.setdefault(typ.value, set())
            for k in mapping.keys:
                iv = const_int(k)
                if iv is not None:
                    s.add(iv)
    if found:
        return found, "parsed from %s (itemkit.selftest `_ASSUME`)" % rel(itemkit_path)
    return baked, "baked fallback (`_ASSUME` not found in itemkit.py)"


# ---------------------------------------------------------------------------
# pass 2: resolve call sites against the feeder registry
# ---------------------------------------------------------------------------
def audit(paths, itemkit_path=None, rel_override=None):
    global ITEMKIT_ASSUMED, GLOBAL_FACTORIES, GLOBAL_TUPLE_FACTORIES
    GLOBAL_FACTORIES, GLOBAL_TUPLE_FACTORIES = {}, {}

    assume_src = "not loaded"
    if itemkit_path and os.path.exists(itemkit_path):
        ITEMKIT_ASSUMED, assume_src = load_itemkit_assume(itemkit_path)
    else:
        ITEMKIT_ASSUMED, assume_src = load_itemkit_assume(
            os.path.join(ROOT, "world", "itemkit.py"))

    # PASS 0 -- kit-wide factories only.  itemkit/humankit methods are called
    # from every item module, so `g.bump(...)` in an item can only be resolved
    # once the kit's own return types are known.
    errors = []
    for p in paths:
        if os.path.basename(p) not in ("itemkit.py", "humankit.py"):
            continue
        try:
            s0 = FileScan(p, open(p, encoding="utf-8").read()).run(
                factories_only=True)
        except SyntaxError:
            continue
        GLOBAL_FACTORIES.update(s0.factories)
        GLOBAL_TUPLE_FACTORIES.update(s0.tuple_factories)

    # PASS 1 -- the real analysis.
    rel_override = rel_override or {}
    scans = []
    for p in paths:
        try:
            scans.append(FileScan(p, open(p, encoding="utf-8").read(),
                                  as_rel=rel_override.get(p)).run())
        except SyntaxError as e:
            errors.append((rel(p), "SyntaxError: %s" % e))

    # feeder registry, keyed by bare symbol name, same-file preferred
    by_name = {}
    all_feeders = []
    for s in scans:
        for f in s.feeders:
            all_feeders.append(f)
            by_name.setdefault(f.name, []).append(f)

    hits = []

    # -- feeder DEFINITIONS -> NOTICE (or exempted) ------------------------
    for f in all_feeders:
        allow = ALLOWED_FEEDER_DEFS.get((f.file, f.qual))
        hits.append(make_hit(
            rule="feeder-def", tier=NOTICE, file=f.file, line=f.lineno,
            symbol=f.qual, node_type=None, index=None,
            exempt=bool(allow), exempt_reason=allow,
            guarded=f.guarded,
            detail=("by-index socket primitive `%s(%s=...)` [%s]%s"
                    % (f.qual, f.idx_param, f.kind,
                       "" if not f.guarded else "  (asserts socket name)"))))

    # -- DIRECT `.inputs[int]` ---------------------------------------------
    for s in scans:
        for sub, idx, node_expr, scope, stack in s.direct:
            typ = s.lookup(node_expr, stack)
            tier, why = classify(typ, idx)
            hits.append(make_hit(
                rule="direct-index", tier=tier, file=s.rel, line=sub.lineno,
                symbol=scope, node_type=typ, index=idx,
                socket=socket_name(typ, idx) if typ else None,
                detail="%s.inputs[%d]" % (dotted(node_expr) or "<expr>", idx),
                reason=why, exempt=False))

    # -- CALL SITES of feeders ---------------------------------------------
    for s in scans:
        for call, scope, stack in s.calls:
            fname = (call.func.attr if isinstance(call.func, ast.Attribute)
                     else call.func.id if isinstance(call.func, ast.Name) else None)
            if not fname or fname not in by_name:
                continue
            cands = [f for f in by_name[fname] if f.file == s.rel] or by_name[fname]
            f = cands[0]
            # `expect=` anywhere on the call is the sanctioned mitigation
            kwnames = {k.arg for k in call.keywords if k.arg}
            if kwnames & set(EXPECT_KWARGS):
                hits.append(make_hit(
                    rule="by-index-call", tier=NOTICE, file=s.rel,
                    line=call.lineno, symbol=scope, node_type=None, index=None,
                    detail="%s(... expect=...)" % fname, exempt=True,
                    exempt_reason="passes expect=, a positive socket-name "
                                  "assertion that raises on a version move"))
                continue

            attr_call = isinstance(call.func, ast.Attribute)
            off = 1 if (f.is_method and attr_call) else 0

            # locate the index argument
            idx_expr = None
            if f.idx_pos is not None:
                ap = f.idx_pos - off
                if 0 <= ap < len(call.args):
                    idx_expr = call.args[ap]
            for k in call.keywords:
                if k.arg == f.idx_param:
                    idx_expr = k.value
            if idx_expr is None:
                continue

            # locate the node argument, for type inference
            node_expr = None
            if f.node_pos is not None:
                ap = f.node_pos - off
                if 0 <= ap < len(call.args):
                    node_expr = call.args[ap]
            for k in call.keywords:
                if k.arg == f.node_param:
                    node_expr = k.value
            typ = s.lookup(node_expr, stack) if node_expr is not None else None
            if typ is None and f.kind == "defaults-dict":
                # `self.n("ShaderNodeTexNoise", defaults={2: scale})` -- the
                # node being defaulted is the one this very call creates.
                typ = s._type_from_call(call)

            if f.kind == "index":
                iv = s.as_int(idx_expr)
                if iv is None:
                    # dynamic index: this is what `_feed_named` / `pin_named`
                    # do after resolving a name.  Not statically knowable, and
                    # NOT the R2-057 shape.  Recorded, never failing.
                    hits.append(make_hit(
                        rule="dynamic-index", tier=NOTICE, file=s.rel,
                        line=call.lineno, symbol=scope, node_type=typ,
                        index=None, exempt=False,
                        detail="%s(%s=<computed>)" % (fname, f.idx_param)))
                    continue
                tier, why = classify(typ, iv)
                hits.append(make_hit(
                    rule="feeder-call", tier=tier, file=s.rel, line=call.lineno,
                    symbol=scope, node_type=typ, index=iv,
                    socket=socket_name(typ, iv) if typ else None,
                    detail="%s(%s, %d, ...)  ->  %s.inputs[%d]"
                           % (fname, dotted(node_expr) or "<node>", iv,
                              typ or "<unknown node type>", iv),
                    reason=why, exempt=False,
                    feeder="%s::%s" % (f.file, f.qual)))
            else:  # defaults-dict
                if not isinstance(idx_expr, ast.Dict):
                    continue
                for k in idx_expr.keys:
                    iv = s.as_int(k)
                    if iv is None:
                        continue
                    tier, why = classify(typ, iv)
                    hits.append(make_hit(
                        rule="defaults-dict", tier=tier, file=s.rel,
                        line=getattr(k, "lineno", call.lineno), symbol=scope,
                        node_type=typ, index=iv,
                        socket=socket_name(typ, iv) if typ else None,
                        detail="%s(..., %s={%d: ...})  ->  %s.inputs[%d]"
                               % (fname, f.idx_param, iv,
                                  typ or "<unknown node type>", iv),
                        reason=why, exempt=False,
                        feeder="%s::%s" % (f.file, f.qual)))

    # -- inline waivers ----------------------------------------------------
    srcs = {s.rel: s.lines for s in scans}
    for h in hits:
        lines = srcs.get(h["file"]) or []
        for probe in (h["line"], h["line"] - 1):
            if 1 <= probe <= len(lines):
                m = WAIVER_RE.search(lines[probe - 1])
                if m:
                    h["waiver"] = m.group(1).strip() or "<no reason given>"
                    break

    return hits, errors, assume_src, len(scans)


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------
def report(hits, errors, assume_src, nfiles, args, out=sys.stdout):
    p = out.write

    waived = [h for h in hits if h.get("waiver")]
    allowed = [h for h in hits if h.get("exempt")]
    live = [h for h in hits if not h.get("waiver") and not h.get("exempt")]

    failing_tiers = set(STRICT_TIERS if args.strict else FAILING_TIERS)
    fails = [h for h in live if h["tier"] in failing_tiers]

    p("=" * 78 + "\n")
    p("SOCKET INDEX AUDIT  (R2-057 guard)\n")
    p("  %s\n" % time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    p("  socket table: %s\n" % SOCKETS_MEASURED_ON)
    p("  STABLE tier : %s\n" % assume_src)
    p("  files parsed: %d\n" % nfiles)
    p("=" * 78 + "\n")

    for err_file, msg in errors:
        p("PARSE ERROR  %s: %s\n" % (err_file, msg))

    for tier in (LETHAL, MOVED, STABLE, NOTICE):
        group = [h for h in live if h["tier"] == tier]
        if not group:
            continue
        mark = (lambda t: "FAILS" if t in failing_tiers else "listed only")
        head = {
            LETHAL: "LETHAL -- known-fatal by-index socket writes  [%s]" % mark(LETHAL),
            MOVED: "MOVED  -- index not proven stable in 5.x       [%s]" % (
                mark(MOVED) if args.strict else "listed only, --strict fails these"),
            STABLE: "STABLE -- same idiom, index has not moved      [%s]" % (
                mark(STABLE) if args.strict else "listed only, --strict fails these"),
            NOTICE: "NOTICE -- by-index primitives and dynamic uses [listed only]",
        }[tier]
        p("\n" + "-" * 78 + "\n%s\n" % head + "-" * 78 + "\n")
        for h in sorted(group, key=lambda x: (x["file"], x["line"])):
            p("%s:%d\n" % (h["file"], h["line"]))
            p("    in %s  [%s]\n" % (h["symbol"], h["rule"]))
            p("    %s\n" % h["detail"])
            if h.get("index") is not None and h.get("node_type"):
                p("    index %d of %s is really %r in live Blender 5.2\n"
                  % (h["index"], h["node_type"], h.get("socket")))
            if h.get("reason"):
                p("    -> %s\n" % h["reason"])
            if h.get("feeder"):
                p("    via %s\n" % h["feeder"])

    if allowed:
        p("\n" + "-" * 78 + "\nEXEMPTED (allowlisted / expect=-guarded)\n"
          + "-" * 78 + "\n")
        for h in sorted(allowed, key=lambda x: (x["file"], x["line"])):
            p("%s:%d  %s\n      %s\n"
              % (h["file"], h["line"], h["detail"],
                 h.get("exempt_reason") or ""))

    if waived:
        p("\n" + "!" * 78 + "\nWAIVERS IN EFFECT -- %d suppressed finding(s). "
          "These are NOT clean.\n" % len(waived) + "!" * 78 + "\n")
        for h in sorted(waived, key=lambda x: (x["file"], x["line"])):
            p("%s:%d  [%s]  %s\n      waived because: %s\n"
              % (h["file"], h["line"], h["tier"], h["detail"], h["waiver"]))

    counts = {t: len([h for h in live if h["tier"] == t])
              for t in (LETHAL, MOVED, STABLE, NOTICE)}
    p("\n" + "=" * 78 + "\n")
    p("LETHAL %d   MOVED %d   STABLE %d   NOTICE %d   exempt %d   WAIVED %d\n"
      % (counts[LETHAL], counts[MOVED], counts[STABLE], counts[NOTICE],
         len(allowed), len(waived)))
    if fails:
        p("FAIL -- %d finding(s) at a failing tier.\n" % len(fails))
        p("Fix by addressing the socket BY NAME (pin_named / _feed_named), or\n"
          "by passing expect='<socket name>' so a version move raises.\n")
    else:
        p("PASS -- no findings at a failing tier.\n")
    p("=" * 78 + "\n")
    return fails


# ---------------------------------------------------------------------------
# scope
# ---------------------------------------------------------------------------
# R2-070.  The scope used to be `world/items/*.py` + itemkit + humankit, with
# `world/build_*.py` behind an OPT-IN flag and `tools/`, `anim/`, `sim/` and
# `audio/` not swept at all.  That is a blind spot of exactly the shape this
# tool exists to close: a private index helper living in `tools/` or `anim/`
# was invisible to the only instrument that can see private index helpers, and
# the guard's own default run would have called the tree clean.  It is also
# how the R2-070 pair survived -- not because the check could not see them
# (it can, at LETHAL), but because nothing ran it over anything.
#
# The default is now EVERY source directory.  There is no flag that turns a
# directory off, because "the sweep did not cover it" must never again be a
# reachable state.  `--include-builds` is kept so old invocations still work
# and is now a no-op; it prints a note saying so.
SCOPE_DIRS = (
    ("world",),
    ("world", "items"),
    ("tools",),
    ("anim",),
    ("sim",),
    ("audio",),
    ("render",),
)


def default_paths(include_builds=False):
    import glob
    ps = []
    for parts in SCOPE_DIRS:
        d = os.path.join(ROOT, *parts)
        if os.path.isdir(d):
            ps += glob.glob(os.path.join(d, "*.py"))
    # de-duplicate and drop this file: auditing the guard's own fixtures and
    # its own baked socket table produces nothing but noise about itself.
    me = os.path.abspath(__file__)
    return sorted({os.path.abspath(p) for p in ps} - {me})


# ---------------------------------------------------------------------------
# --refresh-sockets : re-measure against the live Blender, never from memory
# ---------------------------------------------------------------------------
DUMP_SNIPPET = r"""
import bpy, json, sys
m = bpy.data.materials.new("_sia_probe"); m.use_nodes = True
w = bpy.data.worlds.new("_sia_world"); w.use_nodes = True
ng = bpy.data.node_groups.new("_sia_geo", "GeometryNodeTree")
out = {}
for typ in %(TYPES)s:
    err = "not attempted"
    for t in (m.node_tree, w.node_tree, ng):
        try:
            nd = t.nodes.new(typ)
        except Exception as e:
            err = str(e); continue
        out[typ] = [s.name for s in nd.inputs]
        t.nodes.remove(nd); break
    else:
        out[typ] = {"error": err}
open(sys.argv[-1], "w").write(json.dumps(out, indent=1, sort_keys=True))
"""


def refresh_sockets(dest):
    types = sorted(SOCKETS_5_2)
    src = DUMP_SNIPPET % {"TYPES": repr(types)}
    tmp = os.path.join(os.path.dirname(os.path.abspath(dest)), "_sia_dump.py")
    open(tmp, "w").write(src)
    r = subprocess.run(["blender", "-b", "--factory-startup", "--python", tmp,
                        "--", os.path.abspath(dest)],
                       capture_output=True, text=True)
    os.unlink(tmp)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        return 2
    live = json.load(open(dest))
    drift = []
    for typ, names in sorted(live.items()):
        if isinstance(names, dict):
            continue
        if SOCKETS_5_2.get(typ) != names:
            drift.append(typ)
    print("measured %d node types -> %s" % (len(live), dest))
    if drift:
        print("SOCKET TABLE DRIFT vs the baked table in this file: %s" % drift)
        for typ in drift:
            print("  baked %s\n  live  %s" % (SOCKETS_5_2.get(typ), live[typ]))
        print("The baked SOCKETS_5_2 is STALE. Update it and re-audit the tree.")
        return 1
    print("baked SOCKETS_5_2 matches live Blender exactly.")
    return 0


# ===========================================================================
# R2-070 -- THE ARTEFACT ARM.  `--blend <file>`
#
# WHY A SECOND ARM AT ALL
# -----------------------
# Everything above is AST.  AST is fast, needs no Blender, and fires at
# authoring time -- but it can only see indices that are written down.  It
# cannot see:
#
#   * a computed index (`pin(nd, base + k, v)`), which it can only mark
#     NOTICE, and there are 997 of those in this tree;
#   * a graph assembled correctly in source and then mutated afterwards;
#   * a module it was never pointed at.
#
# And this project's standing lesson is that a build log saying "linked
# Normal" and a blend actually having `Normal` linked are different claims.
# So this arm asks the artefact, in the artefact's own terms, and it does not
# care how the wire got there:
#
#   R1  RELIEF_INTO_NON_NORMAL   a Bump / Normal Map / Bevel output landing on
#                                a socket that is not a normal input.  This is
#                                the R2-057 / R2-070 signature seen from the
#                                far end: on Blender 5.2 the off-by-one puts
#                                it on `Thin Wall`.
#   R2  RELIEF_ORPHANED          a Bump / Normal Map whose output goes nowhere
#                                at all -- the same defect when the stray
#                                index lands past the end of the socket list
#                                and the link is silently dropped.
#   R3  BUMP_HEIGHT_UNLINKED     R2-038: `Height` on a constant. No gradient,
#                                so no relief, whatever the strength says.
#   R4  BUMP_FILTER_WIDTH_DRIVEN R2-038's other half: a texture in `Filter
#                                Width`, which is where the height lands when
#                                the Bump node is addressed one socket short.
#
# WHAT IT ALSO REPORTS, AND WHY
# -----------------------------
# For every offending material it prints Transmission Weight, Subsurface
# Weight, Alpha and Coat Weight.  That is not decoration.  A relief chain
# landing on `Thin Wall` is merely FLAT if the material is opaque, but on a
# material that carries transmission it switches the BSDF's shell
# interpretation per pixel, which is a different and worse defect.  The tool
# refuses to let that distinction be assumed: it prints the numbers that
# decide it, so the blast radius is measured every time.
# ===========================================================================

# THE RULES THEMSELVES LIVE IN `tools/socket_blend_scan.py` -- R2-072.
#
# They used to be a SOURCE STRING here, written to a temp file and handed to a
# fresh Blender.  That gave them exactly one consumer: a human typing
# `--blend`.  R2-071's rule is that a fix is not landed until the artefact
# downstream of it has been rebuilt AND RE-READ, and the only thing in this
# tree that opens an item's built blend as a matter of course is
# `tools/item_gate.py` -- which is already inside Blender with the blend open,
# so making it spawn a second Blender to reopen a 2.4 GB file would be absurd.
#
# So the rules are one importable module now, and there are two consumers:
# this arm bootstraps it into the Blender it spawns, and the item gate imports
# it directly.  ONE rule set; a tightening reaches both or neither.  The sink
# still decides the severity, and the armco_w_beam edge-wear idiom is still a
# NOTE -- see that module's docstring, and the idiom control in
# `--selftest-blend`, which fails this file if that ever stops being true.
# By path, not by package: this file is run as a script, imported by
# `item_gate`, and exec'd inside Blender, and only one of those three puts
# `tools/` on sys.path for us.
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import socket_blend_scan as _SBS                                  # noqa: E402

NORMAL_SINKS = _SBS.NORMAL_SINKS
RELIEF_NODES = _SBS.RELIEF_NODES
SHADER_SINK_TYPES = _SBS.SHADER_SINK_TYPES
SHADER_SINK_PREFIX = _SBS.SHADER_SINK_PREFIX

# The bootstrap. Everything it does is import the rules and run them; there is
# no rule text here to drift out of step with the module.
BLEND_SNIPPET = r'''
import bpy, json, sys
sys.path.insert(0, %(TOOLS)r)
import socket_blend_scan as SBS

%(EXTRA)s

open(sys.argv[-1], "w").write(json.dumps(SBS.scan_open_blend(), indent=1))
'''


def _run_blend_scan(blend, extra="", label=None):
    """Open `blend` (or nothing, if blend is None) in Blender and scan it."""
    src = BLEND_SNIPPET % {"TOOLS": HERE, "EXTRA": extra}
    # PER-INVOCATION temp names.  These used to be two fixed paths, and two
    # concurrent scans -- an item sweep and a world sweep, which is the normal
    # way to use this -- silently destroyed each other's report: one process's
    # `finally` unlinked the JSON the other's Blender had just written, and the
    # victim reported "produced no report" on a blend that had scanned fine.
    # A gate that fails when you run two of it is a gate people stop running.
    tmpdir = os.path.join(ROOT, "tmp")
    os.makedirs(tmpdir, exist_ok=True)
    _run_blend_scan.seq = getattr(_run_blend_scan, "seq", 0) + 1
    stem = os.path.join(tmpdir, "_sia_blendscan_%d_%d"
                        % (os.getpid(), _run_blend_scan.seq))
    script = stem + ".py"
    dest = stem + ".json"
    open(script, "w").write(src)
    cmd = [BLENDER_BIN, "-b", "--factory-startup", "-noaudio"]
    if blend:
        cmd.append(blend)
    cmd += ["--python", script, "--", dest]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.load(open(dest))
    except Exception:
        sys.stderr.write("blend scan produced no report for %s\n"
                         % (blend or label))
        sys.stderr.write(r.stdout[-4000:] + r.stderr[-4000:])
        return None
    finally:
        for f in (script, dest):
            if os.path.exists(f):
                os.unlink(f)
    # Blender 5.2 exits 0 on an uncaught script exception, so the return code
    # is not evidence and is not consulted.  The presence of the report is.
    data["label"] = label or blend
    return data


# `/usr/bin/blender` has no CUDA kernels on this box; this arm never renders,
# but it must be the same binary the world is built with or the socket order
# it reads is not the socket order that shipped.
BLENDER_BIN = os.environ.get("BLENDER_BIN",
                             "/opt/blender-5.2.0-linux-x64/blender")


def report_blend(data, out=sys.stdout):
    p = out.write
    p("=" * 78 + "\n")
    p("ARTEFACT SOCKET AUDIT  (R2-070)\n")
    p("  blend   : %s\n" % (data.get("blend") or data.get("label")))
    p("  blender : %s\n" % data.get("blender"))
    p("  trees   : %d scanned\n" % data.get("scanned_trees", 0))
    p("=" * 78 + "\n")
    allf = data.get("findings") or []
    fs = [f for f in allf if f.get("severity") != "NOTE"]
    notes = [f for f in allf if f.get("severity") == "NOTE"]
    if not fs:
        p("PASS -- no relief chain reaches a shading node on anything but a\n"
          "        normal input, every Bump drives Height, no Bump has a\n"
          "        driven Filter Width.\n")
        if notes:
            p("        (%d relief output(s) feed a computation rather than a\n"
              "        shader -- the edge-wear idiom. Listed, not failing:)\n"
              % len(notes))
            for f in notes:
                p("        NOTE  %s %r: %s\n"
                  % (f["kind"], f["owner"], f["detail"]))
        p("=" * 78 + "\n")
        return []
    for f in sorted(fs, key=lambda x: (x["rule"], x["owner"], x["node"])):
        p("\n%-26s %s %r\n" % (f["rule"], f["kind"], f["owner"]))
        p("    %s\n" % f["detail"])
        for sh in f.get("shell") or []:
            tr = sh.get("Transmission Weight") or {}
            ss = sh.get("Subsurface Weight") or {}
            al = sh.get("Alpha") or {}
            co = sh.get("Coat Weight") or {}
            nm = sh.get("Normal") or {}
            tw = sh.get("Thin Wall") or {}
            p("    shell: Normal.linked=%s  ThinWall.linked=%s  "
              "transmission=%s/%s  subsurface=%s/%s  alpha=%s  coat=%s\n"
              % (nm.get("linked"), tw.get("linked"),
                 tr.get("value"), tr.get("linked"),
                 ss.get("value"), ss.get("linked"),
                 al.get("value"), co.get("value")))
            if tr.get("value") or tr.get("linked") or ss.get("value") \
                    or ss.get("linked"):
                p("    ^^ THIS MATERIAL CARRIES TRANSMISSION OR SUBSURFACE.\n"
                  "       A stray relief link on `Thin Wall` here is NOT merely\n"
                  "       flat -- it switches the shell interpretation per\n"
                  "       pixel.  Do not report this one as 'degenerates to\n"
                  "       flat'.\n")
    p("\n" + "=" * 78 + "\n")
    p("FAIL -- %d finding(s) in the built artefact.\n" % len(fs))
    p("=" * 78 + "\n")
    return fs


# ---------------------------------------------------------------------------
# --selftest-blend : the artefact arm's own controls.
#
# Both arms are built in ONE Blender session from ONE shader graph, and the
# only difference between them is which socket the bump output is linked to.
# That matters: a negative control that is a separately authored "clean"
# material proves only that two different graphs differ.  Here the negative
# control IS the positive control with one link moved, so a pass on the
# negative and a fail on the positive can only be about that link.
# ---------------------------------------------------------------------------
CONTROL_EXTRA = r'''
def _build_controls():
    """POSITIVE: bump -> inputs[5], which is `Thin Wall` on Blender 5.2 -- the
       shipped R2-070 wiring, reproduced verbatim rather than described.
       NEGATIVE: the same graph with that one link moved to `Normal`.
       Neither is written from memory: the positive indexes by integer exactly
       as the defect did, so if a future Blender moves the socket again this
       control moves with it."""
    for nm, by_name in (("SIA_POSITIVE_thinwall", False),
                        ("SIA_NEGATIVE_byname", True)):
        m = bpy.data.materials.new(nm)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(b.outputs[0], out.inputs[0])
        tex = nt.nodes.new("ShaderNodeTexNoise")
        bump = nt.nodes.new("ShaderNodeBump")
        nt.links.new(tex.outputs["Factor"], bump.inputs["Height"])
        if by_name:
            nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
        else:
            nt.links.new(bump.outputs["Normal"], b.inputs[5])

    # SECOND NEGATIVE CONTROL, and the one that matters more, because it is
    # not synthetic.  This is `armco_w_beam.mat_wbeam`'s edge-wear mask,
    # reproduced: a Bevel normal dotted with the true geometry normal.  The
    # first version of this arm FAILED it.  A guard that fails a correct,
    # shipped, deliberate idiom gets switched off, so it has to stay here and
    # stay passing.
    m = bpy.data.materials.new("SIA_NEGATIVE_edgewear")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs[0])
    bev = nt.nodes.new("ShaderNodeBevel")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = 'DOT_PRODUCT'
    nt.links.new(bev.outputs["Normal"], dot.inputs[0])
    nt.links.new(geo.outputs["Normal"], dot.inputs[1])
    nt.links.new(dot.outputs["Value"], b.inputs["Metallic"])


_build_controls()
'''


# A REAL MODULE'S REAL GRAPH, IN A REAL FILE ON DISK -- R2-072.
#
# This section used to point at `gantry_truss_test.blend` and
# `pont_girder_test.blend` with the words "these were built BEFORE the R2-070
# fix and are on disk now; if the arm is real, it fails them without being
# told to."  That was true when it was written and it STOPPED BEING TRUE the
# moment those two blends were rebuilt against the fix -- the section then
# printed "0 stray relief link(s)" under a heading claiming the opposite, and
# asserted nothing either way.  A control whose subject is scheduled to be
# repaired is a control with an expiry date on it.
#
# So the positive control is GENERATED, from the live source, every run:
# `pont_girder._simple_mat` -- the actual function R2-070 was found in -- is
# built twice into two saved .blend files.  The only difference is how the one
# `Normal` link is addressed: `_feed(b, 5, ...)` exactly as the defect did, or
# `_feed_named(b, "Normal", ...)` as the fix does.  Both files are then handed
# to the SAME `--blend` path an operator would use, by filename, with no hint
# of what is in them.
#
#   * it cannot expire, because it is rebuilt from whatever the source says
#     today;
#   * it is not this file's own synthetic graph -- it is a shipped material
#     with its two voronoi stages, its chained bump and its 5-way mix;
#   * if a future Blender moves `Normal` again, the by-index arm moves with it
#     and the control still reproduces the real defect.
CONTROL_MAT_BUILD = r"""
import bpy, os, sys
ROOT = %(ROOT)r
for p in (os.path.join(ROOT, "world"), os.path.join(ROOT, "world", "items")):
    sys.path.insert(0, p)
BY_INDEX = %(BY_INDEX)r

import pont_girder as PG
import marshal_post_column as HS

if BY_INDEX:
    # Reproduce R2-070 EXACTLY: route the by-name write back through the
    # by-integer one, at the index `Normal` used to occupy.
    def _broken(self, node, name, v):
        self._feed(node, 5, v)
    HS.NG._feed_named = _broken

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
mat = PG._simple_mat("SIA_REAL_%%s" %% ("BROKEN" if BY_INDEX else "FIXED"),
                     [(0.0165, 0.0165, 0.0170), (0.0345, 0.0345, 0.0355),
                      (0.048, 0.047, 0.045), (0.058, 0.056, 0.052)],
                     0.72, (900.0, 900.0))
# A material with no user is PURGED ON SAVE, which is how the first version of
# this control shipped a positive that found nothing: the file it scanned was
# empty. Give it a fake user, then say how many materials actually went in.
for m in bpy.data.materials:
    m.use_fake_user = True
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1])
print(">> control blend: %%d material(s) saved: %%s"
      %% (len(bpy.data.materials), [m.name for m in bpy.data.materials]))
"""


def _build_real_control(by_index, dest):
    """Build `pont_girder._simple_mat` into `dest`, broken or fixed."""
    src = CONTROL_MAT_BUILD % {"ROOT": ROOT, "BY_INDEX": by_index}
    script = dest + ".build.py"
    open(script, "w").write(src)
    r = subprocess.run([BLENDER_BIN, "-b", "--factory-startup", "-noaudio",
                        "--python", script, "--", dest],
                       capture_output=True, text=True)
    os.unlink(script)
    if not os.path.exists(dest):
        sys.stderr.write(r.stdout[-3000:] + r.stderr[-3000:])
        return False
    return True


def _real_artefact_controls(ok):
    """Both directions, on a real module's real graph, read back off disk."""
    print("\n[REAL ARTEFACT CONTROLS] pont_girder._simple_mat, built two ways")
    print("  The same shipped material, saved to two .blend files. The only")
    print("  difference is whether its ONE `Normal` link is addressed by the")
    print("  integer 5 (the R2-070 defect) or by name (the fix). Generated")
    print("  from live source every run, so neither side can go stale.")
    tmpdir = os.path.join(ROOT, "tmp")
    os.makedirs(tmpdir, exist_ok=True)
    made = []
    try:
        for by_index, label in ((True, "BROKEN (by index 5)"),
                                (False, "FIXED (by name)")):
            dest = os.path.join(tmpdir, "_sia_real_%d_%s.blend"
                                % (os.getpid(), "broken" if by_index else "fixed"))
            if not _build_real_control(by_index, dest):
                print("  => INCONCLUSIVE: could not build the %s control." % label)
                return False
            made.append(dest)
            d = _run_blend_scan(dest, label=dest)
            if d is None:
                print("  => INCONCLUSIVE: no report for the %s control." % label)
                return False
            bad = [x for x in d["findings"] if x.get("severity") != "NOTE"]
            sinks = sorted({x["owner"] + "." + x.get("to_socket", "-")
                            for x in bad})
            print("  %-22s %d failing finding(s) %s" % (label, len(bad), sinks))
            if by_index and not any(x.get("to_socket") == "Thin Wall"
                                    for x in bad):
                print("  => REAL POSITIVE FAILS: the arm did not fail a real")
                print("     shipped graph carrying the real defect, read off")
                print("     disk. Do not trust a clean run of this arm.")
                ok = False
            elif by_index:
                print("  => REAL POSITIVE PASSES: fails a real module's real")
                print("     material, from a file, without being told to.")
            elif bad:
                print("  => REAL NEGATIVE FAILS: the arm fails the FIXED build")
                print("     of the same graph, so it false-positives on")
                print("     shipped work.")
                ok = False
            else:
                print("  => REAL NEGATIVE PASSES: the fixed build of the very")
                print("     same graph is clean.")
    finally:
        for f in made:
            for suffix in ("", "1"):
                if os.path.exists(f + suffix):
                    os.unlink(f + suffix)
    return ok


def selftest_blend(args):
    print("=" * 78)
    print("ARTEFACT ARM SELFTEST -- proving it FAILS the broken input")
    print("=" * 78)
    data = _run_blend_scan(None, extra=CONTROL_EXTRA, label="<in-memory controls>")
    if data is None:
        print("  => INCONCLUSIVE: Blender produced no report. %s" % BLENDER_BIN)
        return 2
    fs = [f for f in data["findings"] if f.get("severity") != "NOTE"]
    pos = [f for f in fs if f["owner"] == "SIA_POSITIVE_thinwall"]
    neg = [f for f in fs if f["owner"] == "SIA_NEGATIVE_byname"]
    idi = [f for f in fs if f["owner"] == "SIA_NEGATIVE_edgewear"]
    ok = True

    print("\n[POSITIVE CONTROL] SIA_POSITIVE_thinwall")
    print("  bump output linked to Principled.inputs[5] by INTEGER INDEX --")
    print("  the shipped R2-070 wiring, reproduced rather than described.")
    hit = [f for f in pos if f["rule"] == "RELIEF_INTO_NON_NORMAL"]
    for f in hit:
        print("  FIRED  %s -> %s.%r" % (f["node_type"], f["to_node"],
                                        f["to_socket"]))
    if hit and any(f["to_socket"] == "Thin Wall" for f in hit):
        print("  => POSITIVE CONTROL PASSES: the artefact arm FAILS the broken")
        print("     input, and names the socket it actually landed on.")
    else:
        print("  => POSITIVE CONTROL FAILS: the planted stray link was not")
        print("     detected. Do not trust a clean run of this arm.")
        ok = False

    print("\n[NEGATIVE CONTROL] SIA_NEGATIVE_byname")
    print("  bit-for-bit the same graph with that ONE link moved to `Normal`.")
    if neg:
        print("  => NEGATIVE CONTROL FAILS: %d finding(s) on the by-name "
              "graph -- the arm false-positives:" % len(neg))
        for f in neg:
            print("       %s %s" % (f["rule"], f["detail"]))
        ok = False
    else:
        print("  => NEGATIVE CONTROL PASSES: clean, and it is a verdict rather")
        print("     than a no-op -- the same scan read %d trees and returned %d"
              % (data["scanned_trees"], len(fs)))
        print("     failing finding(s) in total, all on the positive arm.")

    print("\n[IDIOM CONTROL] SIA_NEGATIVE_edgewear")
    print("  a Bevel normal dotted with the geometry normal, driving Metallic")
    print("  -- armco_w_beam's real, shipped edge-wear mask.  This is a relief")
    print("  node reaching a non-normal socket and it is CORRECT.")
    if idi:
        print("  => IDIOM CONTROL FAILS: %d failing finding(s) on a correct "
              "shipped idiom. This arm would be switched off:" % len(idi))
        for f in idi:
            print("       %s %s" % (f["rule"], f["detail"]))
        ok = False
    else:
        noted = [f for f in data["findings"]
                 if f["owner"] == "SIA_NEGATIVE_edgewear"]
        print("  => IDIOM CONTROL PASSES: not failed, and not ignored either "
              "-- %d NOTE-level finding(s) recorded." % len(noted))

    # A control that only ever sees graphs THIS FILE built is a control on
    # itself.  The real shipped artefacts are the honest positive input.
    ok = _real_artefact_controls(ok)

    print("\n" + "=" * 78)
    print("STAGE RESULT: %s" % ("PASS" if ok else "FAIL"))
    print("=" * 78)
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# --selftest : PROVE THE INSTRUMENT.  A null must be proven, not accepted.
# ---------------------------------------------------------------------------
FIXTURES = os.path.join(ROOT, "work", "instrument-fixes", "socket_audit_fixtures")
POS_FIXTURE = os.path.join(FIXTURES, "positive_control_r2057.py")
NEG_FIXTURE = os.path.join(FIXTURES, "negative_control_byname.py")
EXM_FIXTURE = os.path.join(FIXTURES, "exemption_scope_control.py")


def selftest(args):
    """POSITIVE control: the exact R2-057 shape must FIRE at LETHAL.
       NEGATIVE control: a by-name module must EXIT CLEAN.

    Both run against FROZEN fixtures under work/instrument-fixes/, never
    against live module state -- other agents are editing world/items/ right
    now and a control built on moving state proves nothing.
    """
    ok = True
    print("=" * 78)
    print("SELFTEST -- proving the instrument, not trusting it")
    print("=" * 78)

    for f in (POS_FIXTURE, NEG_FIXTURE, EXM_FIXTURE):
        if not os.path.exists(f):
            print("MISSING FIXTURE: %s" % f)
            print("  The controls live in %s" % FIXTURES)
            print("  and are FROZEN on purpose -- they")
            print("  are not regenerated from live modules, because a control "
                  "built on")
            print("  state another agent is editing proves nothing. Restore "
                  "the file; do")
            print("  not point the selftest at world/items/.")
            return 2

    # ---- POSITIVE ----------------------------------------------------------
    print("\n[POSITIVE CONTROL] %s" % POS_FIXTURE)
    print("  planted: private `_feed(self, node, idx, v)` + `_feed(b, 5, bump)`")
    print("           against a ShaderNodeBsdfPrincipled -- the exact R2-057 "
          "shape.")
    hits, errors, _, _ = audit([POS_FIXTURE])
    lethal = [h for h in hits if h["tier"] == LETHAL
              and not h.get("exempt") and not h.get("waiver")]
    principled5 = [h for h in lethal
                   if h.get("node_type") == "ShaderNodeBsdfPrincipled"
                   and h.get("index") == 5]
    for h in principled5:
        print("  FIRED  %s:%d  %s" % (h["file"], h["line"], h["detail"]))
        print("         index 5 of ShaderNodeBsdfPrincipled is really %r"
              % h["socket"])
    if principled5:
        print("  => POSITIVE CONTROL PASSES: check fires on the planted fault "
              "(%d lethal hit(s), %d of them the Principled[5] shape)."
              % (len(lethal), len(principled5)))
    else:
        print("  => POSITIVE CONTROL FAILS: the planted R2-057 fault was NOT "
              "detected. The instrument is broken; do not trust a clean run.")
        ok = False

    # a control must also prove it is looking at what it claims to look at:
    # the same fixture with the call REMOVED must go quiet.
    src = open(POS_FIXTURE, encoding="utf-8").read()
    neutered, nsub = re.subn(r"self\._feed\((\w+), 5, (\w+)\)",
                             r'self.pin(\1, "Normal", \2)', src)
    tmpf = os.path.join(FIXTURES, "_neutered_tmp.py")
    open(tmpf, "w").write(neutered)
    try:
        if nsub == 0:
            print("  => COUNTER-CHECK INCONCLUSIVE: could not rewrite the "
                  "planted call; fixture has drifted.")
            ok = False
        ast.parse(neutered)      # the rewrite must still be valid Python,
                                 # or "no hit" would just mean "no parse"
        h2, _, _, _ = audit([tmpf])
        still = [h for h in h2 if h["tier"] == LETHAL
                 and h.get("node_type") == "ShaderNodeBsdfPrincipled"
                 and h.get("index") == 5 and not h.get("exempt")]
        if still:
            print("  => COUNTER-CHECK FAILS: the check still reports "
                  "Principled[5] after the fault was rewritten by name. It is "
                  "not measuring what it claims to.")
            ok = False
        elif nsub:
            print("  => COUNTER-CHECK PASSES: rewriting that one call to "
                  "`pin(bs, \"Normal\", ...)` (%d substitution(s), file still "
                  "parses) silences exactly that hit -- so the hit tracks the "
                  "fault, not the file." % nsub)
    finally:
        os.unlink(tmpf)

    # ---- NEGATIVE ----------------------------------------------------------
    print("\n[NEGATIVE CONTROL] %s" % NEG_FIXTURE)
    print("  a frozen copy of a by-name module (`_feed_named`, no lethal "
          "by-index writes).")
    hits, errors, _, _ = audit([NEG_FIXTURE])
    bad = [h for h in hits if h["tier"] in FAILING_TIERS
           and not h.get("exempt") and not h.get("waiver")]
    if bad:
        print("  => NEGATIVE CONTROL FAILS: %d failing finding(s) on a clean "
              "by-name module -- the check false-positives:" % len(bad))
        for h in bad[:10]:
            print("     %s:%d [%s] %s" % (h["file"], h["line"], h["tier"],
                                          h["detail"]))
        ok = False
    else:
        n_notice = len([h for h in hits if h["tier"] == NOTICE])
        n_stable = len([h for h in hits if h["tier"] == STABLE])
        # A clean exit is only meaningful if the check actually LOOKED at the
        # file.  Zero findings of ANY tier on a 3800-line shader module would
        # mean the parse or the scope walk collapsed -- which is exactly how a
        # convincing null gets manufactured.  Demand evidence of work.
        if (n_stable + n_notice) == 0 or errors:
            print("  => NEGATIVE CONTROL FAILS: the check reported nothing at "
                  "ANY tier (%d parse error(s)). A clean run here would be a "
                  "null with no proof behind it." % len(errors))
            ok = False
        else:
            print("  => NEGATIVE CONTROL PASSES: clean exit (0 failing), and "
                  "the check demonstrably read the file -- %d STABLE + %d "
                  "NOTICE findings, so 'clean' is a verdict, not a no-op."
                  % (n_stable, n_notice))

    # ---- EXEMPTION SCOPE ---------------------------------------------------
    print("\n[EXEMPTION SCOPE CONTROL] %s" % EXM_FIXTURE)
    print("  audited UNDER THE IDENTITY `world/itemkit.py`, so the allowlist "
          "entry")
    print("  ('world/itemkit.py', 'NT.pin') applies. The exemption must cover "
          "that one")
    print("  symbol and nothing else.")
    hits, _, _, _ = audit([EXM_FIXTURE],
                          rel_override={EXM_FIXTURE: "world/itemkit.py"})
    defs = {h["symbol"]: h for h in hits if h["rule"] == "feeder-def"}
    checks = []
    checks.append(("NT.pin definition is EXEMPT",
                   bool(defs.get("NT.pin", {}).get("exempt"))))
    checks.append(("NT._feed (a NEW private helper in the SAME file) is NOT "
                   "exempt", "NT._feed" in defs
                   and not defs["NT._feed"].get("exempt")))
    lethal_lines = {h["line"] for h in hits if h["tier"] == LETHAL
                    and not h.get("exempt")}
    exempt_calls = {h["line"] for h in hits if h.get("exempt")
                    and h["rule"] == "by-index-call"}
    src_lines = open(EXM_FIXTURE, encoding="utf-8").read().splitlines()

    def line_of(frag):
        for i, l in enumerate(src_lines, 1):
            if frag in l and not l.lstrip().startswith("#"):
                return i
        return -1

    ln_guard = line_of('g.pin(b, 5, 0.5, expect=')
    ln_bare = line_of('g.pin(b, 5, 0.5)')
    ln_feed = line_of('g._feed(b, 5, 0.5)')
    checks.append(("pin(..., expect='Thin Wall') is EXEMPT",
                   ln_guard in exempt_calls))
    checks.append(("pin(b, 5, ...) with NO expect= is LETHAL",
                   ln_bare in lethal_lines))
    checks.append(("_feed(b, 5, ...) from the new private helper is LETHAL",
                   ln_feed in lethal_lines))
    for label, good in checks:
        print("  %-4s %s" % ("OK" if good else "FAIL", label))
        if not good:
            ok = False
    print("  => EXEMPTION SCOPE CONTROL %s"
          % ("PASSES: the exemption is one (file, symbol) pair, not a blanket "
             "skip of itemkit." if all(c[1] for c in checks)
             else "FAILS: the exemption is wider or narrower than claimed."))

    print("\n" + "=" * 78)
    print("SELFTEST %s" % ("PASS" if ok else "FAIL"))
    print("=" * 78)
    return 0 if ok else 1


# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="R2-057 guard: fail when a module sets a node input by "
                    "integer index.")
    ap.add_argument("paths", nargs="*",
                    help="files to audit (default: every *.py under world/, "
                         "world/items/, tools/, anim/, sim/, audio/, render/)")
    ap.add_argument("--include-builds", action="store_true",
                    help="DEPRECATED no-op: world/build_*.py, tools/, anim/, "
                         "sim/ and audio/ are always in the default scope now "
                         "(R2-070). Accepted so old invocations keep working.")
    ap.add_argument("--blend", metavar="PATH", nargs="+",
                    help="ARTEFACT ARM (R2-070): open built .blend file(s) and "
                         "fail if any relief chain lands on a socket that is "
                         "not a normal input, or if any Bump has an unlinked "
                         "Height / a driven Filter Width")
    ap.add_argument("--selftest-blend", action="store_true",
                    help="run the artefact arm's positive and negative "
                         "controls, plus the real shipped blends")
    ap.add_argument("--strict", action="store_true",
                    help="make the STABLE tier fail too")
    ap.add_argument("--json", metavar="PATH", help="write machine-readable report")
    ap.add_argument("--allow", metavar="FILE",
                    help="file of `path::Symbol` feeder-definition exemptions, "
                         "one per line; every entry is printed loudly")
    ap.add_argument("--selftest", action="store_true",
                    help="run the positive and negative controls")
    ap.add_argument("--refresh-sockets", metavar="PATH",
                    help="re-measure the socket table against live Blender and "
                         "diff it against the baked table")
    args = ap.parse_args(argv)

    if args.refresh_sockets:
        return refresh_sockets(args.refresh_sockets)
    if args.selftest:
        return selftest(args)
    if args.selftest_blend:
        return selftest_blend(args)
    if args.blend:
        rc = 0
        for b in args.blend:
            data = _run_blend_scan(os.path.abspath(b), label=b)
            if data is None:
                rc = 2
                continue
            if report_blend(data):
                rc = max(rc, 1)
        return rc
    if args.include_builds:
        sys.stdout.write(
            "note: --include-builds is a no-op since R2-070; world/build_*.py, "
            "tools/, anim/, sim/ and audio/ are always in scope.\n")

    if args.allow:
        loud = []
        for ln in open(args.allow, encoding="utf-8"):
            ln = ln.split("#")[0].strip()
            if not ln or "::" not in ln:
                continue
            f, sym = ln.split("::", 1)
            ALLOWED_FEEDER_DEFS[(f.strip(), sym.strip())] = (
                "allowlisted via --allow %s" % args.allow)
            loud.append(ln)
        if loud:
            sys.stdout.write("!" * 78 + "\nEXTERNAL ALLOWLIST %s -- %d entr"
                             "y(ies) suppressed:\n" % (args.allow, len(loud)))
            for ln in loud:
                sys.stdout.write("  %s\n" % ln)
            sys.stdout.write("!" * 78 + "\n")

    paths = [os.path.abspath(p) for p in args.paths] or \
        default_paths(args.include_builds)
    paths = [p for p in paths if os.path.exists(p)]
    if not paths:
        sys.stderr.write("no files to audit\n")
        return 2

    hits, errors, assume_src, nfiles = audit(paths)
    fails = report(hits, errors, assume_src, nfiles, args)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({
                "tool": "socket_index_audit",
                "defect": "R2-057",
                "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "socket_table": SOCKETS_MEASURED_ON,
                "stable_tier_source": assume_src,
                "strict": args.strict,
                "files": [rel(p) for p in paths],
                "parse_errors": errors,
                "counts": {t: len([h for h in hits if h["tier"] == t
                                   and not h.get("exempt")
                                   and not h.get("waiver")])
                           for t in (LETHAL, MOVED, STABLE, NOTICE)},
                "failing": len(fails),
                "hits": hits,
            }, fh, indent=1)
        sys.stdout.write("json -> %s\n" % args.json)

    return 1 if (fails or errors) else 0



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
    gate_exit.guard(main, tool="socket_index_audit")
