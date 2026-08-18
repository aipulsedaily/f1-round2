#!/usr/bin/env python3
"""Draft world/items/PLACEMENT.json from measured facts.

Every field is read from an artefact: the module source (COLL/PFX), the
canonical gate.json (verdict, objects found, instances declared), the blend on
disk (sha256, mtime) and, where one was run, the inventory probe.
"""
import ast, hashlib, json, os, re, sys

ROOT = os.path.expanduser("~/f1-round2")
ITEMS = os.path.join(ROOT, "world", "items")
GATES = os.path.join(ROOT, "render", "items")
INV = os.path.join(ROOT, "work", "r2226")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def consts(path):
    """ITEM / COLL / PFX style constants, read from the AST, not regex-guessed."""
    src = open(path, encoding="utf-8", errors="replace").read()
    out = {}
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for n in tree.body:
        if not isinstance(n, ast.Assign):
            continue
        tgts = [t.id for t in n.targets if isinstance(t, ast.Name)]
        # tuple assignment: ITEM, COLL, PFX = "a", "b", "c"
        if len(n.targets) == 1 and isinstance(n.targets[0], ast.Tuple):
            names = [e.id for e in n.targets[0].elts if isinstance(e, ast.Name)]
            if isinstance(n.value, ast.Tuple) and len(names) == len(n.value.elts):
                for nm, v in zip(names, n.value.elts):
                    if isinstance(v, ast.Constant) and isinstance(v.value, str):
                        out[nm] = v.value
            continue
        if isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            for t in tgts:
                out[t] = n.value.value
    return out

CKEYS = ("COLL", "COLL_NAME", "ROOT_COLL", "COLLECTION", "COLL_ROOT")
PKEYS = ("PFX", "OBJ_PREFIX", "PREFIX", "GATE_PREFIX")
IKEYS = ("ITEM", "ITEM_ID")

rows = []
for f in sorted(os.listdir(ITEMS)):
    if not f.endswith(".py"):
        continue
    mod = f[:-3]
    c = consts(os.path.join(ITEMS, f))
    item = next((c[k] for k in IKEYS if k in c), mod)
    coll = next((c[k] for k in CKEYS if k in c), None)
    pfx = next((c[k] for k in PKEYS if k in c), None)
    blend = os.path.join(ITEMS, mod + "_test.blend")
    g = os.path.join(GATES, item, "gate.json")
    gd = json.load(open(g)) if os.path.exists(g) else None
    invp = os.path.join(INV, "inv_%s.json" % mod)
    inv = json.load(open(invp)) if os.path.exists(invp) else None
    rows.append({
        "module": mod, "item": item, "collection": coll, "prefix": pfx,
        "blend": blend if os.path.exists(blend) else None,
        "blend_sha": sha(blend) if os.path.exists(blend) else None,
        "gate_result": (gd or {}).get("result"),
        "gate_objects": ((gd or {}).get("measured") or {}).get("objects"),
        "gate_declared": ((gd or {}).get("measured") or {}).get("instances_declared"),
        "gate_subject": (gd or {}).get("subject_selection"),
        "inv_objects": (inv or {}).get("n_objects"),
        "inv_meshes": (inv or {}).get("n_distinct_meshes"),
        "inv_rig": (inv or {}).get("rig_subcollections"),
    })
json.dump(rows, open(os.path.join(INV, "registry_facts.json"), "w"), indent=1)
for r in rows:
    print("%-30s item=%-28s coll=%-32s pfx=%-12s blend=%s gate=%s obj=%s/%s inv=%s" % (
        r["module"], r["item"], r["collection"], r["prefix"],
        "Y" if r["blend"] else "-", (r["gate_result"] or "-")[:13],
        r["gate_objects"], r["gate_declared"], r["inv_objects"]))
