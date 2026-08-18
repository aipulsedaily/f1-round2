"""WHICH ASSEMBLY IS THE SHIP — read from the ONE file that declares it.

    from shipping_world import declared_shipping_world, declared_shipping_path
    declared_shipping_world()   -> "assembly8.blend"
    declared_shipping_path()    -> "render/world/assembly/r2/assembly8.blend"

WHY THIS IS ITS OWN MODULE
--------------------------
`render/world/assembly/r2/SHIPPING.md` is where the promotion decision is
recorded and argued.  Everything that consumes the shipping world has to agree
with it, and the way this project has repeatedly failed is that a consumer kept
its OWN copy of the answer:

  * R2-071 — `tools/build_film_scene.py` named `assembly6` while `assembly7`
    had been the ship since 04:45.  Two film scenes shipped on a superseded
    world.  Nothing checked, because the name was a literal in the builder.
  * `tools/input_stamp.py:44` declared `assembly6.blend` as the world every
    screen-presence measurement is stamped against, and went on declaring it
    through the `assembly7` promotion.  Nobody owned it, because a default
    argument does not look like a decision.

Both are the same defect: **a second copy of a fact.**  The name is now stated
once, in SHIPPING.md, and parsed once, here.  A consumer that wants to know
the ship imports this; it does not get to have an opinion.

stdlib only, and NO `bpy`.  `input_stamp.py` runs under the plain interpreter
and `build_film_scene.py` runs inside Blender, and one parser has to serve
both — a Blender-only helper would have forced the plain-python caller to keep
the copy this module exists to delete.

IF IT CANNOT PARSE A DECLARATION IT RAISES.  An unreadable declaration must not
degrade into "anything goes"; that is the state R2-071 was found in.
"""

import os
import re

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSEMBLY_DIR = os.path.join(R2, "render/world/assembly/r2")
SHIPPING_MD = os.path.join(ASSEMBLY_DIR, "SHIPPING.md")

_TITLE = "# WHICH ASSEMBLY IS THE SHIPPING WORLD"


def declared_shipping_world(path=SHIPPING_MD):
    """The basename of the declared ship, e.g. ``"assembly8.blend"``.

    The declaration is the first ``**`assemblyN.blend`**`` bold run after the
    title.  ONE declaration: if the file names a second assembly in a bold run
    of its own before the prose gets to the superseded ones, that is ambiguous
    and this raises rather than silently taking the first.
    """
    with open(path) as fh:
        text = fh.read()
    if _TITLE not in text:
        raise SystemExit(
            "REFUSING: %s has no %r heading, so nothing in it declares a "
            "shipping world." % (path, _TITLE))
    head = text.split(_TITLE, 1)[-1]
    m = re.search(r"\*\*`(assembly\d+\.blend)`", head)
    if not m:
        raise SystemExit(
            "REFUSING: cannot read the declared shipping world out of %s. "
            "Nothing may be built against an undeclared world." % path)
    return m.group(1)


def declared_shipping_path(path=SHIPPING_MD):
    """Absolute path to the declared ship. RAISES if the blend is not there.

    A declaration naming a file that does not exist is worse than no
    declaration: every consumer would silently stamp a MISSING input and carry
    on.
    """
    name = declared_shipping_world(path)
    p = os.path.join(ASSEMBLY_DIR, name)
    if not os.path.exists(p):
        raise SystemExit(
            "REFUSING: %s declares %s and that file does not exist at %s."
            % (path, name, p))
    return p


def _selftest():
    """Both controls: it reads the real declaration, and it REFUSES a bad one.

    A parser that has only ever been run on a good file has not been tested;
    the failure mode being guarded is an unparseable declaration degrading
    into a default, so that is the case that has to be shown failing.
    """
    import tempfile
    ok = True

    got = declared_shipping_world()
    print("  POSITIVE  %s -> %s" % (SHIPPING_MD, got))
    if not re.fullmatch(r"assembly\d+\.blend", got):
        print("  => POSITIVE CONTROL FAILS: %r is not an assembly name" % got)
        ok = False
    p = declared_shipping_path()
    print("  POSITIVE  path -> %s  (%.1f MB)"
          % (p, os.path.getsize(p) / 1048576.0))

    with tempfile.TemporaryDirectory() as d:
        bad = os.path.join(d, "SHIPPING.md")
        with open(bad, "w") as fh:
            fh.write("# WHICH ASSEMBLY IS THE SHIPPING WORLD\n\n"
                     "the ship is whatever you like, really\n")
        try:
            declared_shipping_world(bad)
            print("  => NEGATIVE CONTROL FAILS: a file with NO declaration "
                  "was parsed without raising")
            ok = False
        except SystemExit as exc:
            print("  NEGATIVE  undeclared file REFUSED: %s" % str(exc)[:60])

        noheading = os.path.join(d, "NOHEAD.md")
        with open(noheading, "w") as fh:
            fh.write("**`assembly99.blend`** is great\n")
        try:
            declared_shipping_world(noheading)
            print("  => NEGATIVE CONTROL FAILS: a bold assembly name outside "
                  "the declaration section was accepted as the declaration")
            ok = False
        except SystemExit as exc:
            print("  NEGATIVE  no-heading file REFUSED: %s" % str(exc)[:60])

        missing = os.path.join(d, "MISSING.md")
        with open(missing, "w") as fh:
            fh.write("# WHICH ASSEMBLY IS THE SHIPPING WORLD\n\n"
                     "**`assembly99.blend`** — built never\n")
        try:
            declared_shipping_path(missing)
            print("  => NEGATIVE CONTROL FAILS: a declaration naming a "
                  "non-existent blend returned a path")
            ok = False
        except SystemExit as exc:
            print("  NEGATIVE  absent blend REFUSED: %s" % str(exc)[:60])

    print("SELFTEST %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    print(declared_shipping_path())
