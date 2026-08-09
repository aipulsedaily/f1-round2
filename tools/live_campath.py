"""WHICH PATH FILE IS THE LIVE CAMERA — read from the ONE file that declares it.

    from live_campath import load, declared_campath
    declared_campath()  -> "/home/zany/f1-round2/render/film17_path.json"
    load()              -> {"frames": 2978, "path": [...]}       the LIVE camera
    load(byframe=True)  -> {1: {...}, 2: {...}, ...}             keyed by frame

    python3 tools/live_campath.py --selftest

WHY THIS IS ITS OWN MODULE
--------------------------
This is `tools/shipping_world.py` for the camera, and it exists because the
defect that module was written to kill — **a second copy of a fact** — was never
killed for the camera.

R2-1007 / R2-1091: `world/camera_rig_path.json` sat byte-identical to
`render/film16_path.json` for three days while `render/film17_path.json` was the
film's camera. **43 tools read the stale file. One read the live one.** Every
gate, probe and peep in that list was measuring a camera the film does not have,
by up to 9.866 m of position and 23.0 mm of focal length, everywhere in beat 1.

Nothing noticed, and nothing COULD notice, because:

  * `anim/build_camera_rig.py:1585` names its output `splitext(--out)[0] +
    "_path.json"`. The name is a side effect of an argument, so no build step
    owns `world/camera_rig_path.json` and no build step rewrote it.
  * `tools/input_stamp.py` records a sha256 of whatever it is handed, but it is
    a RECORDER, not a COMPARATOR — it has no notion of which file is live. Its
    `default_inputs()` hardcodes `"camera_path": "world/camera_rig_path.json"`,
    the very literal-default pattern its own docstring diagnoses for the world
    role and fixes there via `shipping_world`.
  * `input_stamp.declared_version()` reports `frames=2978` for the stale file
    and `frames=2978` for the live one. **The label reads the same either way**,
    which is the project's most-logged defect shape: an instrument that cannot
    tell present from absent.

THE DESIGN RULE THIS FOLLOWS
----------------------------
A stamp that 43 callers must remember to check will be forgotten by the 44th.
So this module does not offer a stamp to check — it offers the camera, and
there is **no argument for getting the wrong one**. `load()` takes no path.

A caller that genuinely needs a non-live path (an A/B, a control, a historical
re-measurement) must say so out loud:

    load_explicit("render/film16_path.json", why="R2-1091 A/B against the stale")

`why` is required and must be non-empty. A silent stale read is not reachable
through this module's API.

TWO KEYS, NOT ONE
-----------------
`docs/LIVE-CAMERA.md` declares the filename AND pins its sha256. Both are
checked on every load. A rebuild that changes the bytes without updating the
declaration RAISES in every reader rather than being adopted silently — because
the failure being guarded is precisely a rebuild nobody announced.

IF IT CANNOT PARSE, OR THE HASH DISAGREES, IT RAISES. An unreadable or stale
declaration must not degrade into "anything goes"; that is the state R2-1007
found the tree in.

stdlib only, and NO `bpy` — the same constraint `shipping_world` carries, for
the same reason: tools under the plain interpreter and tools inside Blender both
have to be able to import this, or one of them keeps the copy.
"""

import hashlib
import json
import os
import re

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE_MD = os.path.join(R2, "docs", "LIVE-CAMERA.md")

_TITLE = "# WHICH PATH FILE IS THE LIVE CAMERA"

# Known-superseded path files, by sha256, with the reason. These are not merely
# "not live" — they are files a reader has actually been caught reading, so the
# error message can say what went wrong instead of only that something did.
KNOWN_STALE = {
    "d9c8f5c54ccd1ad896d7457ac940d3bd16c80de5445a2d6da4f804606f43d76a":
        "the film16-era rig output (world/camera_rig_path.json == "
        "render/film16_path.json). Superseded 2026-08-07. Diverges from the "
        "live camera by up to 9.866 m and 23.0 mm of lens across f2-f780 "
        "(beat 1). This is R2-1007.",
    # R2-3721 / defect #159.  THE PREVIOUS GENERATION OF THE SAME ORPHAN, and
    # the one that did the damage.  `world/camera_rig_path.json` held THESE
    # bytes (== film13 == film14, and still what git HEAD has) when
    # `docs/screen_presence*.json` was swept at 2026-08-04 01:49; it acquired
    # the film16 bytes above at 15:49 the same day, fourteen hours LATER.  So
    # the entry above does not cover the sweep it was written about: a reader
    # checking the orphan by filename got the film16 bytes and concluded the
    # sweep was film16's, and the sweep's own `campos` array matches film14 to
    # 5 um and film16 only to 8.86 m.
    #
    # Against the delivered camera (film24) these bytes are wrong on 2,347 of
    # 2,978 frames in position (max 21.43 m at f2176), 2,129 in lens (max
    # 56.00 mm at f2978) and 2,456 above 0.2 deg (max 179.52 deg at f87).  The
    # item tiering swept from them puts 17 of 435 items on a different tier and
    # 322 of 559 objects on a px/m detail budget more than 10 % out.
    "f1c65c46459d4488d252434f6ce123473f03051498f4c471110619026010a5e0":
        "the film13/film14-era rig output. This is the exact camera "
        "docs/screen_presence*.json and docs/proposed_tiers.json were swept "
        "against, and it is what git HEAD still has in "
        "world/camera_rig_path.json. 17 of 435 items tier differently under "
        "the delivered camera. This is R2-3721 / defect #159.",
}


def sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _declaration(md=LIVE_MD):
    """(basename, sha256) as declared. RAISES rather than defaulting."""
    if not os.path.exists(md):
        raise SystemExit(
            "REFUSING: %s does not exist, so nothing declares the live camera. "
            "Nothing may be measured against an undeclared camera." % md)
    with open(md) as fh:
        text = fh.read()
    if _TITLE not in text:
        raise SystemExit(
            "REFUSING: %s has no %r heading, so nothing in it declares a live "
            "camera." % (md, _TITLE))
    head = text.split(_TITLE, 1)[-1]
    m = re.search(r"\*\*`(render/film\d+_path\.json)`\*\*", head)
    if not m:
        raise SystemExit(
            "REFUSING: cannot read the declared live camera path out of %s. "
            "Nothing may be measured against an undeclared camera." % md)
    h = re.search(r"sha256 `([0-9a-f]{64})`", head)
    if not h:
        raise SystemExit(
            "REFUSING: %s declares %s but pins no sha256 for it. The filename "
            "alone cannot tell a rebuild from a stale copy — that is exactly "
            "how R2-1007 happened." % (md, m.group(1)))
    return m.group(1), h.group(1)


def declared_campath(md=LIVE_MD):
    """Absolute path to the live camera. RAISES if it is missing or altered."""
    name, want = _declaration(md)
    p = os.path.join(R2, name)
    if not os.path.exists(p):
        raise SystemExit(
            "REFUSING: %s declares %s and that file does not exist at %s."
            % (md, name, p))
    got = sha256(p)
    if got != want:
        raise SystemExit(
            "REFUSING: %s has changed on disk since it was declared.\n"
            "    declared sha256 %s\n"
            "    actual   sha256 %s\n"
            "The camera was rebuilt and %s was not updated. Every measurement "
            "taken between those two events is unattributable. Update the "
            "declaration deliberately — do not silence this."
            % (p, want, got, md))
    return p


def _check_not_stale(p):
    """RAISE with the reason if `p` is a path file known to be superseded."""
    got = sha256(p)
    if got in KNOWN_STALE:
        raise SystemExit(
            "REFUSING to read a KNOWN-STALE camera path.\n"
            "    file   %s\n"
            "    sha256 %s\n"
            "    what   %s\n"
            "Use live_campath.load(), which takes no path and therefore cannot "
            "be pointed at this file." % (p, got, KNOWN_STALE[got]))
    return got


def load(byframe=False, md=LIVE_MD):
    """THE LIVE CAMERA. Takes no path, so it cannot be given the wrong one."""
    p = declared_campath(md)
    _check_not_stale(p)
    with open(p) as fh:
        d = json.load(fh)
    if byframe:
        return {e["f"]: e for e in d["path"]}
    return d


def load_explicit(path, why, byframe=False):
    """A deliberately non-live path, for an A/B or a historical re-measurement.

    `why` is REQUIRED and must be non-empty prose. The point is not that the
    string is validated — it is that a stale read cannot be written by accident,
    and that `grep -rn load_explicit` enumerates every one of them.
    """
    if not why or not str(why).strip():
        raise SystemExit(
            "REFUSING: load_explicit(%r) with no `why`. A non-live camera read "
            "must state its reason, or it is indistinguishable from the bug "
            "R2-1007 logged." % (path,))
    p = path if os.path.isabs(path) else os.path.join(R2, path)
    if not os.path.exists(p):
        raise SystemExit("REFUSING: %s does not exist." % p)
    got = sha256(p)
    note = KNOWN_STALE.get(got)
    print(">> live_campath: DELIBERATE non-live read of %s\n"
          "     sha256 %s\n"
          "     why    %s%s"
          % (p, got, why, ("\n     note   %s" % note) if note else ""))
    with open(p) as fh:
        d = json.load(fh)
    if byframe:
        return {e["f"]: e for e in d["path"]}
    return d


# --------------------------------------------------------------------- selftest
def _selftest():
    """Every control, and the ones that MUST FAIL are the point.

    A guard that has only ever been run on a good input has not been tested.
    This project's most-logged defect is a guard that cannot fire, so the
    negative controls here feed it the ACTUAL stale file that caused R2-1007 —
    not a synthetic stand-in — and require that it refuses.
    """
    import tempfile
    ok = True

    def chk(name, cond, msg=""):
        nonlocal ok
        print("  %-56s %s  %s" % (name, "ok  " if cond else "FAIL", msg))
        ok = ok and bool(cond)

    def must_raise(name, fn, expect):
        nonlocal ok
        try:
            fn()
        except SystemExit as exc:
            got = str(exc)
            hit = expect.lower() in got.lower()
            print("  %-56s %s  raised, %s %r"
                  % (name, "ok  " if hit else "FAIL",
                     "says" if hit else "but did NOT mention", expect))
            ok = ok and hit
            return
        except Exception as exc:                                   # noqa: BLE001
            print("  %-56s FAIL  raised the wrong type: %r" % (name, exc))
            ok = False
            return
        print("  %-56s FAIL  DID NOT RAISE — the guard is vacuous" % name)
        ok = False

    print(">> SELFTEST live_campath")

    # ---- positive: the real declaration resolves and loads
    p = declared_campath()
    chk("resolves the declared live camera", os.path.exists(p),
        os.path.relpath(p, R2))
    d = load()
    chk("loads it", isinstance(d, dict) and "path" in d,
        "%d frames" % d.get("frames", -1))
    bf = load(byframe=True)
    chk("byframe keys by frame number", bf and min(bf) == 1 and len(bf) == d["frames"],
        "f%d..f%d" % (min(bf), max(bf)))

    # ---- NEGATIVE 1. THE ONE THAT MATTERS.
    # The actual file that caused R2-1007, on disk, right now. If this does not
    # refuse, everything above is decoration.
    stale = os.path.join(R2, "world", "camera_rig_path.json")
    if os.path.exists(stale):
        must_raise("MUST FAIL: the real stale world/camera_rig_path.json",
                   lambda: _check_not_stale(stale), "KNOWN-STALE")
        # and prove the stale file is not merely *different* but the one named
        chk("  ...and it is recognised by CONTENT, not by filename",
            sha256(stale) in KNOWN_STALE,
            "sha %s" % sha256(stale)[:16])
    else:
        chk("MUST FAIL: the real stale file", False,
            "world/camera_rig_path.json is gone — re-point this control")

    # ---- NEGATIVE 2. a stale file under an INNOCENT name still refuses.
    # Renaming a stale file must not launder it, because the R2-1007 file was
    # already sitting under the most innocent name in the tree.
    if os.path.exists(stale):
        with tempfile.TemporaryDirectory() as td:
            disguised = os.path.join(td, "render_film99_path.json")
            with open(stale, "rb") as a, open(disguised, "wb") as b:
                b.write(a.read())
            must_raise("MUST FAIL: the same bytes under an innocent filename",
                       lambda: _check_not_stale(disguised), "KNOWN-STALE")

    # ---- NEGATIVE 3. a declaration whose hash no longer matches the file.
    # This is the "rebuilt but not announced" case, which is the failure mode
    # that will actually recur.
    with tempfile.TemporaryDirectory() as td:
        md = os.path.join(td, "LIVE-CAMERA.md")
        with open(md, "w") as fh:
            fh.write(_TITLE + "\n\n**`render/film17_path.json`**\n\n"
                     "sha256 `" + "0" * 64 + "`\n")
        must_raise("MUST FAIL: declared sha256 disagrees with the file",
                   lambda: declared_campath(md), "changed on disk")

    # ---- NEGATIVE 4. a declaration with no hash at all.
    with tempfile.TemporaryDirectory() as td:
        md = os.path.join(td, "LIVE-CAMERA.md")
        with open(md, "w") as fh:
            fh.write(_TITLE + "\n\n**`render/film17_path.json`**\n")
        must_raise("MUST FAIL: a declaration that pins no sha256",
                   lambda: declared_campath(md), "pins no sha256")

    # ---- NEGATIVE 5. an unparseable declaration must not degrade to a default.
    with tempfile.TemporaryDirectory() as td:
        md = os.path.join(td, "LIVE-CAMERA.md")
        with open(md, "w") as fh:
            fh.write(_TITLE + "\n\nthe camera is whichever one looks right\n")
        must_raise("MUST FAIL: an undeclared camera",
                   lambda: declared_campath(md), "undeclared camera")

    # ---- NEGATIVE 6. a missing declaration file.
    must_raise("MUST FAIL: no declaration file at all",
               lambda: declared_campath(os.path.join(R2, "docs", "NO-SUCH.md")),
               "does not exist")

    # ---- NEGATIVE 7. load_explicit without a reason.
    must_raise("MUST FAIL: load_explicit with an empty why",
               lambda: load_explicit("render/film16_path.json", why="   "),
               "must state its reason")

    # ---- positive: load_explicit WITH a reason works, and says so out loud.
    if os.path.exists(os.path.join(R2, "render/film16_path.json")):
        d16 = load_explicit("render/film16_path.json",
                            why="selftest: proving the deliberate escape hatch works")
        chk("load_explicit with a reason returns the file",
            isinstance(d16, dict) and "path" in d16,
            "%d frames" % d16.get("frames", -1))

    print("\nSTAGE RESULT: %s live_campath_selftest"
          % ("LIVE_CAMPATH_OK" if ok else "LIVE_CAMPATH_FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    import argparse
    import sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(_selftest())
    print(declared_campath())
