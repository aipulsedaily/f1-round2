"""Controls for "does probe_pitexit.py write where it was told to write?"

    python3 render/world/assembly/r2/selftest_probe_out.py

Needs no Blender and no scene: it lifts the `resolve_out` / `write_out` block
straight out of lib_probe.py (between the BEGIN/END marker comments) and runs
THAT TEXT, so it cannot drift from the shipped code -- if somebody deletes the
block or breaks it, this file stops working rather than quietly passing.  It
also asserts that probe_pitexit.py still CALLS it, because a resolver nothing
calls is not a fix.

POSITIVE CONTROL.  The old two lines are reproduced here verbatim as
`old_out()`, including `os.path.basename` and lib_probe's hardcoded OUT_DIR, and
every case asserts that the OLD code puts the file somewhere ELSE.  A control
that only checks the new code cannot tell "fixed" from "never broken", and this
one reproduces the fault itself rather than leaning on any other module.

Exits non-zero if any control misbehaves.
"""
import json, os, re, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "lib_probe.py")
PROBE = os.path.join(HERE, "probe_pitexit.py")
OLD_OUT_DIR = "/home/zany/f1-round2/render/world/assembly/r2"   # lib_probe.OUT_DIR

# ---------------------------------------------------------------- the code --
m = re.search(r"^# --- BEGIN resolve_out.*?^# --- END resolve_out.*?$",
              open(LIB).read(), re.S | re.M)
if not m:
    sys.exit("FATAL: the resolve_out block is not in %s -- this selftest is "
             "testing nothing." % LIB)
ns = {"os": os, "sys": sys, "json": json}
exec(compile(m.group(0), LIB, "exec"), ns)
resolve_out, write_out = ns["resolve_out"], ns["write_out"]

# The block existing is not the fix; probe_pitexit.py USING it is.
_p = open(PROBE).read()
for _needle, _why in (("resolve_out(sys.argv", "does not call resolve_out()"),
                      ("write_out(OUT, R)", "does not write via write_out()")):
    if _needle not in _p:
        sys.exit("FATAL: probe_pitexit.py %s -- the defect is back." % _why)
if "os.path.basename(OUT)" in _p.split('"""', 2)[-1]:
    sys.exit("FATAL: probe_pitexit.py still strips the directory off its "
             "output path outside the docstring -- the defect is back.")


def old_out(argv):
    """EXACTLY what the shipped tool used to do. The positive control."""
    OUT = argv[-1] if argv[-1].endswith(".json") else "probe_pitexit.json"
    return os.path.join(OLD_OUT_DIR, os.path.basename(OUT))     # lib_probe.save


# ------------------------------------------------------------------ cases --
TMP = tempfile.mkdtemp(prefix="pitexit_out_ctl_")
# so the "bare relative path" case resolves against a scratch CWD and litters
# nothing. `old_out` never writes -- it only computes the path the old code
# WOULD have used -- so no run of this file can touch the assembly root.
os.chdir(TMP)
BLEND = "/home/zany/f1-round2/render/world/assembly/r2/assembly5.blend"
BASE = ["blender", "-b", BLEND, "--factory-startup", "-P", PROBE, "--"]

want_deep = os.path.join(TMP, "nested", "dir", "explicit.json")
CASES = [
    # label,                              args after `--`,           expected
    ("--out with an explicit path",       ["--out", os.path.join(TMP, "explicit.json")],
     os.path.join(TMP, "explicit.json")),
    ("--out= form",                       ["--out=" + os.path.join(TMP, "eq.json")],
     os.path.join(TMP, "eq.json")),
    ("--out into a directory that does not exist yet", ["--out", want_deep],
     want_deep),
    ("--out NOT last on the line",        ["--out", os.path.join(TMP, "first.json"),
                                           "--frames", "3"],
     os.path.join(TMP, "first.json")),
    ("legacy bare positional path",       [os.path.join(TMP, "legacy.json")],
     os.path.join(TMP, "legacy.json")),
    ("legacy bare RELATIVE path",         ["rel_out.json"],
     os.path.join(os.getcwd(), "rel_out.json")),
]

rows, fails = [], []


def check(label, ok, detail):
    rows.append({"case": label, "ok": bool(ok), "detail": detail})
    print("   %s  %-52s %s" % ("PASS" if ok else "FAIL", label, detail))
    if not ok:
        fails.append(label)


print("NEGATIVE CONTROLS -- the new code must land the file exactly where told,")
print("and the OLD code must be shown to land it somewhere else:")
for label, args, want in CASES:
    argv = BASE + args
    got = resolve_out(argv, blend_path=BLEND)
    old = old_out(argv)
    if got != want:
        check(label, False, "resolved %s, wanted %s" % (got, want))
        continue
    # and it must actually WRITE there
    p = write_out(got, {"case": label})
    landed = os.path.isfile(want) and json.load(open(want))["case"] == label
    # POSITIVE CONTROL: the old idiom must NOT have landed it there.
    old_wrong = (old != want)
    check(label, landed and old_wrong,
          "-> %s | old code would have written %s%s"
          % (p, old, "" if old_wrong else "  <-- OLD CODE AGREES?!"))

print()
print("POSITIVE CONTROL -- the old idiom, run on the case the battery actually")
print("used, reproduces the reported defect (file lands in the assembly root):")
batt = "/home/zany/f1-round2/render/world/assembly/r2/v120/pitexit_v120.json"
argv = BASE + [batt]
old = old_out(argv)
new = resolve_out(argv, blend_path=BLEND)
check("v120/battery.sh asked for v120/pitexit_v120.json",
      old == os.path.join(OLD_OUT_DIR, "pitexit_v120.json") and new == batt,
      "old -> %s | new -> %s" % (old, new))
check("and the misplaced artefact is on disk where the OLD code put it",
      os.path.isfile(os.path.join(OLD_OUT_DIR, "pitexit_v120.json"))
      and not os.path.isfile(batt),
      "assembly root has it; v120/ does not")

print()
print("REFUSALS -- being told nothing sensible must be fatal, not a default:")
for label, args in (("no arguments at all", []),
                    ("`--` but no path", ["--frames", "3"]),
                    ("--out with no value", ["--out"]),
                    ("two bare .json paths", [os.path.join(TMP, "a.json"),
                                              os.path.join(TMP, "b.json")]),
                    ("--out that is not .json", ["--out", os.path.join(TMP, "x.txt")]),
                    ("--out onto a directory", ["--out", TMP])):
    argv = BASE + args
    try:
        got = resolve_out(argv, blend_path=BLEND)
        check(label, False, "returned %s instead of exiting" % got)
    except SystemExit as e:
        # the old code, given the same line, silently invented a destination
        old = old_out(argv)
        check(label, True, "SystemExit; old code would have used %s" % old)

print()
if fails:
    print(">> %d CONTROL(S) MISBEHAVED: %s" % (len(fails), fails))
    print(">> STAGE RESULT: PROBE_OUT_SELFTEST_FAIL")
    sys.exit(1)
print(">> all %d controls behaved (scratch dir %s)" % (len(rows), TMP))
print(">> STAGE RESULT: PROBE_OUT_SELFTEST_OK")
