"""Read R2-1146's strip source back out of a built film.  R2-2101.

    /opt/blender-5.2.0-linux-x64/blender -b <film.blend> --factory-startup \
        -noaudio -P render/world/assembly/r2/v127/measure_strip.py -- \
        --json <out.json>

A separate file rather than a heredoc, because `blender -P -` does NOT read a
script from stdin -- it tries to open a file literally named `-`, fails, and
Blender exits 0 with no verdict.  That is the project's own two-verdict/exit-0
trap, and it was in the first draft of `verify_film23.sh`.

Never writes to the blend.
"""
import json
import os
import sys

sys.path.insert(0, "/home/zany/f1-round2/world")

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []

def probe():
    import bpy
    import showroom_strip as ST
    m = ST.measure(bpy.context.scene)
    print(json.dumps(m, indent=1))
    if "--json" in argv:
        out = argv[argv.index("--json") + 1]
        os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
        json.dump(m, open(out, "w"), indent=1)
        print(">> wrote %s" % out)
    return bool(m.get("present"))


# THE `sys.exit` IS OUTSIDE THE `try`, AND THAT IS THE WHOLE POINT.  R2-2108.
# The first version of this file called `sys.exit(0)` INSIDE a
# `try/except BaseException`.  `sys.exit` raises `SystemExit`, `SystemExit`
# derives from `BaseException`, so the success path was caught by its own
# error handler and the probe printed BOTH verdicts on a correct film:
#
#     >> STAGE RESULT: STRIP_MEASURED
#     >> STAGE RESULT: STRIP_ABSENT (probe raised SystemExit(0))
#
# That is the two-verdict trap, in the file written to avoid the two-verdict
# trap, caught by reading its own output rather than its own source.
# `except Exception` would also fix it; keeping `BaseException` and moving the
# exit out is stricter, because a KeyboardInterrupt or a MemoryError in the
# probe must still be reported as a FAIL and not as a silent success.
ok = False
try:
    ok = probe()
except BaseException as exc:                                     # noqa: BLE001
    import traceback
    traceback.print_exc()
    print(">> STAGE RESULT: STRIP_ABSENT (probe raised %r)" % (exc,))
    raise SystemExit(1)

print(">> STAGE RESULT: %s" % ("STRIP_MEASURED" if ok else "STRIP_ABSENT"))
raise SystemExit(0 if ok else 1)
