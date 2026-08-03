"""Measure the avalanche of every hash01 in the wave-1 modules.

A hash used for per-instance variation must AVALANCHE: flipping one input bit
should flip about half the output bits. One that does not decorrelates nothing,
so properties meant to vary independently move together — and a crowd of 7,800
built on it reads as ranks of clones however many source meshes it emits.

This measures, it does not change anything.
"""
import ast, glob, importlib.util, inspect, math, os, sys, types
import numpy as np

def load_fn(path, names=("hash01", "_hash01", "hash_01")):
    """Import ONLY the hash function, without executing the module.

    The modules import bpy and build geometry at import time, so a real import
    is out of the question. Extract the function's AST and exec it alone.

    ALSO exec the module-level constants it may close over. Four modules define
    `_U32 = np.uint32` at module scope and use it inside hash01; extracting the
    def alone raised NameError, which the report printed as "could not measure"
    -- and an unmeasured hash is UNKNOWN, not clean. Constants are hoisted
    best-effort and individually: anything that touches bpy simply fails and is
    skipped, so a module that builds geometry at import time still costs nothing.
    """
    src = open(path).read()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return None, f"unparseable: {e}"
    g = {"np": np, "math": math, "numpy": np}
    # FunctionDef is in here because terrain_ground's hash01 calls a module-level
    # helper `_h2`. Defining a function does not run it, so hoisting every def is
    # free; only the target actually gets called.
    prelude = [n for n in tree.body
               if isinstance(n, (ast.Import, ast.ImportFrom, ast.Assign,
                                 ast.AnnAssign, ast.FunctionDef))]
    for n in prelude:
        try:
            exec(compile(ast.Module(body=[n], type_ignores=[]), path, "exec"), g)
        except Exception:
            pass  # bpy imports, geometry constants -- irrelevant to the hash
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            mod = ast.Module(body=[node], type_ignores=[])
            try:
                exec(compile(mod, path, "exec"), g)
            except Exception as e:
                return None, f"exec failed: {e}"
            return adapt(g[node.name]), None
    return None, "no hash def found"

def adapt(fn):
    """Normalise every signature to one that takes a single key array.

    terrain_ground's is hash01(ix, iy, seed=0) -- three named params, no *keys.
    Calling it with one argument raised TypeError, which again reported as
    "could not measure". Hold the extra params at a fixed value and vary the
    first, which is exactly the per-bit test avalanche() wants.
    """
    try:
        params = list(inspect.signature(fn).parameters.values())
    except (ValueError, TypeError):
        return fn
    if any(p.kind is inspect.Parameter.VAR_POSITIONAL for p in params):
        return fn
    required = [p for p in params
                if p.default is inspect.Parameter.empty
                and p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                               inspect.Parameter.POSITIONAL_OR_KEYWORD)]
    if len(required) <= 1:
        return fn
    pad = len(required) - 1
    return lambda k: fn(k, *([np.asarray(k) * 0 + 7] * pad))

def avalanche(fn, n=4096):
    """Mean fraction of output bits that flip when ONE input bit flips.

    0.5 is ideal. Well under 0.5 means inputs are not being decorrelated.
    """
    rng = np.random.default_rng(12345)
    base = rng.integers(0, 2**20, size=n).astype(np.int64)
    flips = []
    for bit in range(20):
        alt = base ^ (1 << bit)
        try:
            a = np.asarray(fn(base), dtype=np.float64).ravel()
            b = np.asarray(fn(alt), dtype=np.float64).ravel()
        except Exception:
            try:
                a = np.array([float(fn(int(v))) for v in base[:512]])
                b = np.array([float(fn(int(v))) for v in alt[:512]])
            except Exception as e:
                return None, f"uncallable: {e}"
        if a.shape != b.shape or a.size == 0:
            return None, "shape mismatch"
        ai = (np.clip(a, 0, 1) * (2**24 - 1)).astype(np.uint32)
        bi = (np.clip(b, 0, 1) * (2**24 - 1)).astype(np.uint32)
        x = ai ^ bi
        bits = np.zeros(x.shape, dtype=np.float64)
        for k in range(24):
            bits += ((x >> k) & 1)
        flips.append((bits / 24.0).mean())
    return float(np.mean(flips)), None

def control_bad(k):
    """The known-bad form: FNV with no finaliser, low 30 bits kept."""
    out = []
    for v in np.asarray(k).ravel():
        h = 1469598103934665603
        h ^= int(v) & 0xFFFFFFFFFFFFFFFF
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        out.append(float(h % (1 << 30)) / float(1 << 30))
    return np.array(out)

def control_good(k):
    """The reference form: the same FNV with the murmur3 finaliser."""
    out = []
    for v in np.asarray(k).ravel():
        h = 1469598103934665603
        h ^= int(v) & 0xFFFFFFFFFFFFFFFF
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        h ^= h >> 33
        h = (h * 0xFF51AFD7ED558CCD) & 0xFFFFFFFFFFFFFFFF
        h ^= h >> 33
        h = (h * 0xC4CEB9FE1A85EC53) & 0xFFFFFFFFFFFFFFFF
        h ^= h >> 33
        out.append(float(h % (1 << 30)) / float(1 << 30))
    return np.array(out)

# Run the controls FIRST. If the negative control does not come back collapsed
# and the positive one does not come back near 0.5, this tool is measuring
# nothing and every row below it is noise -- so say so and exit non-zero rather
# than print a clean table.
cb, _ = avalanche(control_bad)
cg, _ = avalanche(control_good)
print(f"controls: known-bad FNV {cb:.4f} (want < 0.35),"
      f"  murmur3-finalised {cg:.4f} (want >= 0.45)")
if not (cb is not None and cb < 0.35 and cg is not None and cg >= 0.45):
    print("\nCONTROLS FAILED — this tool is not measuring avalanche. No results reported.")
    sys.exit(2)
print()

rows = []
for path in sorted(glob.glob("*.py")):
    fn, err = load_fn(path)
    if fn is None:
        continue
    av, err2 = avalanche(fn)
    rows.append((os.path.basename(path), av, err2))

print(f"{'module':<32}{'avalanche':>11}   verdict")
good = bad = unk = 0
for name, av, err in sorted(rows, key=lambda r: (r[1] is None, r[1] or 0)):
    if av is None:
        print(f"  {name:<30}{'--':>11}   could not measure: {err}")
        unk += 1
        continue
    if av >= 0.45:
        v = "avalanches (ok)"; good += 1
    elif av >= 0.35:
        v = "WEAK"; bad += 1
    else:
        v = "*** COLLAPSED — properties will move together"; bad += 1
    print(f"  {name:<30}{av:>11.4f}   {v}")
print(f"\n{len(rows)} hash implementations measured: {good} ok, {bad} weak/collapsed, {unk} unmeasurable")
print(f"ideal 0.5000;  reference form measured {cg:.4f} this run;  known-bad FNV {cb:.4f} this run")
sys.exit(1 if (bad or unk) else 0)
