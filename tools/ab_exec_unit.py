#!/usr/bin/env python3
"""ONE UNIT OF THE REMOTE-EXEC A/B: build one item module and save its .blend.

    blender -b --factory-startup -P tools/ab_exec_unit.py -- \
            --item kerb_precast_unit --out out/build.json

The unit is deliberately the same one `docs/operations.md` §"The A/B that was
supposed to justify this" measured: **import the module, run `test_scene()`,
save the `.blend`** — nothing fetched, nothing rendered, no gate. Identical on
both sides of the comparison, so the only thing that differs between a local
run and a remote one is the CPU underneath it.

Two things it deliberately does NOT do:

* it does not declare the `.blend` as an exec output. The blend is written next
  to the job and dies with it. Fetching 26 multi-hundred-megabyte blends back
  would measure this laptop's downlink, which is the thing exec exists to avoid
  paying for, and it is not part of the build unit.
* it does not import the module through `world.items.<x>` — `world/` has no
  `__init__.py` and every item module inserts its own `sys.path` entries at
  import time. It is loaded from its file, which is what `blender -P` does to
  the modules themselves.

The JSON it writes is the measurement: `build_s` is the module's own
`test_scene()` and `save_s` the save, so a run can say whether a slow unit was
slow at geometry or at I/O.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--item", required=True)
    p.add_argument("--out", required=True, help="where to write the timing JSON")
    p.add_argument("--blend", default="build.blend",
                   help="where to save the .blend; NOT an exec output")
    a = p.parse_args(argv)

    src = os.path.join(ROOT, "world", "items", a.item + ".py")
    if not os.path.isfile(src):
        raise SystemExit(f"no such item module: {src}")

    t0 = time.time()
    spec = importlib.util.spec_from_file_location(f"item_{a.item}", src)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    imported = time.time()

    mod.test_scene()
    built = time.time()

    import bpy                                                  # noqa: PLC0415
    blend = os.path.abspath(a.blend)
    os.makedirs(os.path.dirname(blend) or ".", exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True,
                                relative_remap=False)
    done = time.time()

    rec = {
        "item": a.item,
        "import_s": round(imported - t0, 3),
        "build_s": round(built - imported, 3),
        "save_s": round(done - built, 3),
        "total_s": round(done - t0, 3),
        "blend_bytes": os.path.getsize(blend),
        "host": os.uname().nodename,
    }
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as fh:
        json.dump(rec, fh, indent=2)
    print("AB_UNIT " + json.dumps(rec))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
