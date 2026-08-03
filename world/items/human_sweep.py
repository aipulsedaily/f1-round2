"""human_sweep -- run `humankit.build_figure` across its WHOLE parameter space.

WHY THIS EXISTS. `humankit._skirt` had never executed until source ~40 of a
402-source spectator library, because every item built before the crowd was a
trousered male: crew, marshal, paddock, driver. It crashed with a numpy shape
error the first time a woman wore a skirt, and it took the whole library build
down. A sample of fifty figures drawn from the shipped weights will not find the
next one of those -- `blouse` is w=(0.00, 0.12), `skirt` is (0.00, 0.20),
`bucket` is 0.03, `binocular` is 0.02, and the product of two rare draws on one
figure is rarer still.

So this does not sample. It ENUMERATES:

  * every (top x bottom x sex) -- 11 x 7 x 2, every garment pair that can exist
  * every (headwear x shoe x sex x age_band) -- including `bald` + hat
  * every (pose archetype x sex x age_band) -- all 31 poses, seated and standing
  * every (prop x prop_hand x grip) -- both hands, empty and closed
  * every (role x LOD) -- and the LODs matter, `station`/`ring` go to 8 at L3
  * the DISTRIBUTION TAILS as explicit bodies: 3.4 sigma tall, BMI 46, BMI 14,
    a 5-year-old, an 84-year-old, and each of those in a skirt and in shorts

and it reports every exception with the argument tuple that produced it, plus a
geometry sanity pass on every figure that did build (non-finite vertices,
degenerate triangles, zero-area faces, contact residual, anything below the
contact plane, and an empty-mesh check -- a piece that silently produces nothing
is the failure mode that does NOT raise).

    python3 world/items/human_sweep.py --plan            # what it will run
    python3 world/items/human_sweep.py --jobs 6          # the whole thing
    python3 world/items/human_sweep.py --stage garments  # one stage
"""

import argparse
import itertools
import math
import os
import sys
import traceback

import numpy as np

_ITEMS = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_ITEMS)
for _p in (_WORLD, _ITEMS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import humankit as HK                                          # noqa: E402

AGE_BANDS = ("child", "teen", "adult", "elder")
SEXES = ("M", "F")
LODS = {"L0": HK.LOD_L0, "L1": HK.LOD_L1, "L2": HK.LOD_L2, "L3": HK.LOD_L3}
SEATED = tuple(k for k, v in HK.POSES.items() if v["kind"] == "sit")
UPRIGHT = tuple(k for k, v in HK.POSES.items() if v["kind"] != "sit")


# ---------------------------------------------------------------------------
# The cases.  Each is (stage, label, kwargs-for-build, wardrobe-overrides).
# ---------------------------------------------------------------------------

def _case(stage, label, seed, over=None, **kw):
    return {"stage": stage, "label": label, "seed": seed,
            "over": over or {}, "kw": kw}


def cases(stages=None):
    out = []
    n = 0

    # 1. EVERY GARMENT PAIR ON BOTH SEXES.  `blouse` is female-only at 0.12 and
    #    `skirt` female-only at 0.20; the pair (blouse, skirt) is 2.4 % of the
    #    female draw, i.e. 1 figure in 100, and both of them are code paths.
    for top, bot, sex in itertools.product(sorted(HK.TOPS), sorted(HK.BOTTOMS),
                                           SEXES):
        n += 1
        out.append(_case("garments", "%s+%s/%s" % (top, bot, sex), 700000 + n,
                         over={"top": top, "bottom": bot},
                         sex=sex, age_band="adult", role="spectator",
                         archetype="sit_upright", kind="sit", seat_z=0.0))

    # 2. HEADWEAR x SHOE x SEX x AGE.  A hat on a bald head takes a different
    #    branch from a hat on hair, and `squash` cuts the strand count.
    for hw, sh, sex, ab in itertools.product(sorted(HK.HEADWEAR),
                                             sorted(HK.SHOE_STYLES),
                                             SEXES, AGE_BANDS):
        n += 1
        out.append(_case("kit", "%s/%s/%s/%s" % (hw, sh, sex, ab), 710000 + n,
                         over={"headwear": hw, "shoe": sh},
                         sex=sex, age_band=ab, role="spectator",
                         archetype="stand_relaxed", kind="stand"))
    for hw, sex in itertools.product(sorted(HK.HEADWEAR), SEXES):
        n += 1
        out.append(_case("kit", "bald+%s/%s" % (hw, sex), 715000 + n,
                         over={"headwear": hw, "hair_style": "bald"},
                         sex=sex, age_band="adult", role="spectator",
                         archetype="stand_relaxed", kind="stand"))

    # 3. EVERY POSE ARCHETYPE, both sexes, all four age bands.
    for arche, sex, ab in itertools.product(sorted(HK.POSES), SEXES, AGE_BANDS):
        n += 1
        seated = HK.POSES[arche]["kind"] == "sit"
        out.append(_case("poses", "%s/%s/%s" % (arche, sex, ab), 720000 + n,
                         sex=sex, age_band=ab, role="spectator",
                         archetype=arche, kind="sit" if seated else "stand",
                         seat_z=0.0 if seated else None))

    # 4. EVERY PROP IN EITHER HAND, at both grip extremes.
    for prop, hand, grip in itertools.product(sorted(HK.PROPS), ("L", "R"),
                                              (0.0, 0.7)):
        n += 1
        out.append(_case("props", "%s/%s/g%.1f" % (prop, hand, grip),
                         730000 + n,
                         over={"prop": prop, "prop_hand": hand, "grip": grip},
                         sex="F", age_band="adult", role="spectator",
                         archetype="sit_upright", kind="sit", seat_z=0.0))
    # and every prop on a STANDING figure too -- the grip solve is posed
    for prop in sorted(HK.PROPS):
        n += 1
        out.append(_case("props", "%s/stand" % prop, 735000 + n,
                         over={"prop": prop, "prop_hand": "R"},
                         sex="M", age_band="adult", role="spectator",
                         archetype="stand_relaxed", kind="stand"))

    # 5. EVERY ROLE x EVERY LOD.  L3 drops `station` to 8 and `ring` to 3, and
    #    a garment ridge clamped to 0.62 of a column spacing is a different
    #    number there.
    for role, lod in itertools.product(("spectator", "paddock", "marshal",
                                        "crew"), sorted(LODS)):
        for sex in SEXES:
            n += 1
            out.append(_case("lods", "%s/%s/%s" % (role, lod, sex), 740000 + n,
                             sex=sex, age_band="adult", role=role, lod=lod,
                             archetype="stand_relaxed", kind="stand"))
    # every STAND_ROLE's own archetype table, at every LOD, seated where seated
    for role, lod in itertools.product(HK.STAND_ROLES, sorted(LODS)):
        for arche, _w in HK.STAND_POSES[role]:
            for sex in SEXES:
                n += 1
                seated = role in ("sit", "turned")
                out.append(_case("lods", "%s/%s/%s/%s"
                                 % (role, arche, lod, sex), 745000 + n,
                                 sex=sex, age_band="adult", role="spectator",
                                 lod=lod, archetype=arche,
                                 kind="sit" if seated else "stand",
                                 seat_z=0.0 if seated else None))

    # 6. THE TAILS OF THE DISTRIBUTION.  NOT hand-written bodies: `sample_body`
    #    derives thirty dimensions from stature and BMI and overwriting two
    #    fields afterwards would build a person nothing else agrees with. So
    #    draw 4,000 real bodies per (sex, age) and take the actual extremes --
    #    the tails the shipped sampler can genuinely produce, reached through
    #    the shipped code path.
    for sex, ab in itertools.product(SEXES, AGE_BANDS):
        pool = []
        for i in range(4000):
            sd = 990000 + hash((sex, ab)) % 10000 * 4001 + i
            b = HK.sample_body(HK.rng_for(sd, 1), sex=sex, age_band=ab)
            pool.append((sd, b.stature, b.bmi))
        picks = {
            "tall": max(pool, key=lambda t: t[1]),
            "short": min(pool, key=lambda t: t[1]),
            "heavy": max(pool, key=lambda t: t[2]),
            "thin": min(pool, key=lambda t: t[2]),
            "tall_heavy": max(pool, key=lambda t: t[1] * 0.5 + t[2] * 0.05),
            "short_heavy": max(pool, key=lambda t: t[2] * 0.05 - t[1] * 0.5),
        }
        for nm, (sd, st, bm) in picks.items():
            for top, bot in (("blouse", "skirt"), ("hoodie", "shorts"),
                             ("gilet", "track"), ("buttoned_shirt", "jeans")):
                n += 1
                out.append(_case("tails", "%s/%s/%s/%s+%s %.2fm bmi%.0f"
                                 % (nm, sex, ab, top, bot, st, bm), sd,
                                 over={"top": top, "bottom": bot},
                                 sex=sex, age_band=ab, role="spectator",
                                 archetype="sit_legs_crossed", kind="sit",
                                 seat_z=0.0))

    # 7. GAZE AT THE CLAMP, and the seat solve at every plausible seat height.
    for gz, sex in itertools.product((-95.0, -72.0, -36.0, 0.0, 36.0, 72.0,
                                      95.0), SEXES):
        for pitch in (-24.0, 0.0, 18.0):
            n += 1
            out.append(_case("gaze", "%+.0f/%+.0f/%s" % (gz, pitch, sex),
                             760000 + n, sex=sex, age_band="adult",
                             role="spectator", archetype="sit_upright",
                             kind="sit", seat_z=0.0, gaze=(gz, pitch)))

    # 8. AND THEN A LARGE FULLY-RANDOM DRAW, which is the only thing that
    #    exercises the joint distribution the shipped code actually samples.
    for i in range(1200):
        n += 1
        out.append(_case("random", "r%04d" % i, 770000 + i * 7919,
                         role="spectator",
                         kind="sit" if (i % 3) else "stand",
                         seat_z=0.0 if (i % 3) else None))

    if stages:
        out = [c for c in out if c["stage"] in stages]
    return out


# ---------------------------------------------------------------------------
# Running one case
# ---------------------------------------------------------------------------

def run_case(c):
    kw = dict(c["kw"])
    lod = LODS[kw.pop("lod", "L1")]
    over = dict(c["over"])
    seed = c["seed"]
    r = {"stage": c["stage"], "label": c["label"], "seed": seed}
    try:
        b = HK.sample_body(HK.rng_for(seed, 1), sex=kw.pop("sex", None),
                           age_band=kw.pop("age_band", None))
        if "hair_style" in over:
            b.hair_style = over.pop("hair_style")
        w = HK.sample_wardrobe(HK.rng_for(seed, 2), b,
                               role=kw.get("role"))
        # Substitute the garment TYPE but keep this person's own fit residuals,
        # so a forced pair is still a real draw and not a table constant.
        if "top" in over:
            k0 = HK.TOPS[w["top"]]
            sp = dict(HK.TOPS[over["top"]])
            for k in ("ease", "hem", "sleeve", "lam"):
                sp[k] = sp[k] * (w["top_spec"][k] / max(k0[k], 1e-9))
            sp["sleeve"] = float(np.clip(sp["sleeve"], 0.0, 0.985))
            w["top"], w["top_spec"] = over["top"], sp
        if "bottom" in over:
            k0 = HK.BOTTOMS[w["bottom"]]
            sp = dict(HK.BOTTOMS[over["bottom"]])
            for k in ("ease", "lam"):
                sp[k] = sp[k] * (w["bottom_spec"][k] / max(k0[k], 1e-9))
            w["bottom"], w["bottom_spec"] = over["bottom"], sp
        for k in ("headwear", "shoe", "prop", "prop_hand", "grip"):
            if k in over:
                w[k] = over[k]
                if k == "shoe":
                    w["shoe_spec"] = dict(HK.SHOE_STYLES[over[k]])
        fig = HK.build_figure(seed=seed, lod=lod, body=b, wardrobe=w, **kw)
    except Exception as e:                                   # noqa: BLE001
        r["ok"] = False
        r["err"] = "%s: %s" % (type(e).__name__, e)
        r["tb"] = traceback.format_exc().splitlines()[-6:]
        return r
    # `Mesh.V/Q/T` are LISTS OF ARRAYS, one entry per emitted piece -- they are
    # never a single array until `emit_mesh` concatenates them, which is why a
    # naive np.asarray on them raises a ragged-shape error rather than telling
    # you anything about the figure.
    try:
        m = fig["mesh"]
        V, Q, T3, _QM, _TM, _A = m.finish()
        tri = ([Q[:, (0, 1, 2)], Q[:, (0, 2, 3)]] if len(Q) else []) \
            + ([T3] if len(T3) else [])
        T = np.concatenate(tri) if tri else np.zeros((0, 3), np.int64)
    except Exception as e:                                   # noqa: BLE001
        r["ok"] = False
        r["err"] = "MESH %s: %s" % (type(e).__name__, e)
        r["tb"] = traceback.format_exc().splitlines()[-6:]
        return r
    r["ok"] = True
    r["nv"], r["nt"] = int(len(V)), int(len(T))
    r["nonfinite"] = int((~np.isfinite(V)).any(axis=1).sum()) if len(V) else 0
    if len(T):
        a = V[T[:, 0]]
        e1, e2 = V[T[:, 1]] - a, V[T[:, 2]] - a
        ar = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)
        r["zero_area"] = int((ar < 1e-12).sum())
        r["area_mm2_p01"] = float(np.percentile(ar, 1) * 1e6)
        r["degenerate_index"] = int((T.max() >= len(V)) or (T.min() < 0))
    else:
        r["zero_area"] = -1
        r["area_mm2_p01"] = 0.0
        r["degenerate_index"] = 0
    r["bbox"] = [float(V[:, i].max() - V[:, i].min()) for i in range(3)] \
        if len(V) else [0.0, 0.0, 0.0]
    r["zmin"] = float(V[:, 2].min()) if len(V) else 0.0
    con = fig.get("contact") or {}
    r["seated"] = bool(kw.get("seat_z") is not None)
    # A SEATED FIGURE'S CONTACT IS ITS ISCHIUM, NOT ITS SOLE. `contact
    # ["residual_mm"]` reports |sole_z| for both kinds -- the conditional in
    # `build_figure` has 0.0 in BOTH branches -- so on a seated figure it reads
    # 440 mm and means "the feet hang 440 mm below the seat pan", which is
    # correct behaviour reported under a name that says it is an error.
    r["sole_below_plane_mm"] = float(con.get("below_plane_mm", float("nan")))
    r["sole_z"] = float(con.get("sole_z_after", float("nan")))
    r["contact_mm"] = (0.0 if r["seated"]
                       else float(con.get("residual_mm", float("nan"))))
    r["height_m"] = float(fig.get("height_m", float("nan")))
    r["pieces"] = len(getattr(m, "BLK", []) or [])
    r["flipped"] = int((fig.get("orient") or {}).get("flipped", -1))
    r["tris"] = int(fig.get("tris", 0))
    return r


def _worker(c):
    try:
        return run_case(c)
    except BaseException as e:                                # noqa: BLE001
        return {"stage": c["stage"], "label": c["label"], "seed": c["seed"],
                "ok": False, "err": "HARNESS %s: %s" % (type(e).__name__, e),
                "tb": traceback.format_exc().splitlines()[-6:]}


def main():
    p = argparse.ArgumentParser(prog="human_sweep")
    p.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2)))
    p.add_argument("--stage", action="append", default=None)
    p.add_argument("--plan", action="store_true")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--out", default=None)
    a = p.parse_args()
    cs = cases(a.stage)
    if a.limit:
        cs = cs[:a.limit]
    if a.plan:
        from collections import Counter
        for k, v in sorted(Counter(c["stage"] for c in cs).items()):
            print("  %-10s %5d" % (k, v))
        print("  %-10s %5d" % ("TOTAL", len(cs)))
        return
    import multiprocessing as mp
    print("sweeping %d cases on %d workers" % (len(cs), a.jobs))
    res = []
    with mp.Pool(a.jobs) as pool:
        for i, r in enumerate(pool.imap_unordered(_worker, cs, chunksize=4)):
            res.append(r)
            if not r["ok"]:
                print("  FAIL %-10s %-34s %s"
                      % (r["stage"], r["label"], r["err"]))
            if (i + 1) % 250 == 0:
                print("  ... %d/%d, %d failed"
                      % (i + 1, len(cs), sum(1 for x in res if not x["ok"])))
    bad = [r for r in res if not r["ok"]]
    print("\n=== %d cases, %d CRASHED ===" % (len(res), len(bad)))
    from collections import Counter
    for k, v in Counter(r["err"].split(":")[0] + " | "
                        + (r["tb"][-3] if len(r["tb"]) > 2 else "")
                        for r in bad).most_common(20):
        print("  %4d  %s" % (v, k.strip()))
    good = [r for r in res if r["ok"]]
    for nm, f in (("non-finite vertices", lambda r: r["nonfinite"] > 0),
                  ("zero-area triangles", lambda r: r["zero_area"] > 0),
                  ("out-of-range face index",
                   lambda r: r.get("degenerate_index", 0)),
                  ("empty mesh", lambda r: r["nt"] == 0),
                  ("standing: contact residual > 1 mm",
                   lambda r: not r["seated"] and r["contact_mm"] > 1.0),
                  ("standing: anything below the ground plane",
                   lambda r: not r["seated"] and r["sole_below_plane_mm"] > 1.0),
                  ("seated: sole above the seat pan",
                   lambda r: r["seated"] and r["sole_z"] > -0.05),
                  ("seated: sole below 0.62 m under the pan",
                   lambda r: r["seated"] and r["sole_z"] < -0.62),
                  ("pieces left inside-out", lambda r: r["flipped"] < 0),
                  ("bbox height < 0.6 m", lambda r: r["bbox"][2] < 0.6),
                  ("bbox height > 2.4 m", lambda r: r["bbox"][2] > 2.4)):
        hit = [r for r in good if f(r)]
        print("  %-44s %5d / %d %s"
              % (nm, len(hit), len(good),
                 "" if not hit else "e.g. " + ", ".join(
                     "%s/%s" % (h["stage"], h["label"]) for h in hit[:3])))
    if good:
        for nm, key in (("zero-area tris per figure", "zero_area"),
                        ("triangles per figure", "tris"),
                        ("emitted pieces per figure", "pieces"),
                        ("pieces flipped outward per figure", "flipped")):
            v = np.array([r[key] for r in good], float)
            print("  %-44s min %d  med %d  max %d"
                  % (nm, v.min(), np.median(v), v.max()))
    if a.out:
        import json
        with open(a.out, "w") as fh:
            json.dump(res, fh)
        print("  wrote %s" % a.out)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
