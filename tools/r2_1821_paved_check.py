"""R2-1821: does `paved` put ground cover back on the pit straight WITHOUT putting
any of it on build_architecture's concrete?

    blender -b --factory-startup -noaudio -P tools/r2_1821_paved_check.py

Runs build_terrain's OWN placement functions -- `verge_band`, the meadow grid and the
sward grid -- over the pit-straight window, with the mask as it is and with the drawn
district it replaces, and counts what survives WHERE.

THREE ASSERTIONS, AND THE THIRD IS THE ONE THAT MATTERS
  1. RESTORED   the grass shoulder of the pit straight (f = 0..42 m outboard of the
                rim, circuit y < 0, which is 0.0 % paved) must come back from ~nothing
                to verge-band density.  This is the client's "5 feet from the road".
  2. UNCHANGED  the garages and the paddock -- circuit y 23.5..115, which IS the
                architecture -- must still take no ground cover.
  3. CLEAN      not one placed clump, drift or meadow tuft may land where
                `C.apron_platform_mask` is True.  A mask that restores the shoulder by
                also paving over the paddock with grass is not a fix, and a count of
                what came BACK cannot see that; only a count of what landed ON THE
                CONCRETE can.  This is the negative control and it is manufactured
                from the contract at run time, so it cannot expire.
"""
import bpy, sys, os, json
import numpy as np

sys.path.insert(0, os.path.expanduser("~/f1-round2/world"))
sys.path.insert(0, os.path.expanduser("~/f1-round2"))
import build_terrain as T
import world_contract as C

FAIL = []


def check(name, cond, detail):
    print("  %-52s %s   %s" % (name, "OK  " if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


def main():
    spec = json.load(open(T.SPEC_JSON)); beats = json.load(open(T.BEAT_JSON))
    cir = T.Circuit(spec); gr = T.Ground(cir); cam = T.CameraPath(cir, beats)
    gxs = np.arange(-700.0, 1700.0, 12.0); gys = np.arange(-700.0, 2500.0, 12.0)
    GX, GY = np.meshgrid(gxs, gys, indexing="ij")
    gz = T.GridZ(gxs, gys, gr.height(GX.ravel(), GY.ravel()).reshape(GX.shape))
    rng = np.random.default_rng(T.SEED)

    # ---- 1 / 2.  the verge band over the pit straight -----------------------------
    # The station window is the pit straight: the same s = 3115..250 the old comment
    # names.  `verge_band` is called exactly as `build_grass` calls it.
    out = {}
    per_m = max(6, int(900.0 * T.QUAL))
    bands = [T.verge_band(cir, np.random.default_rng(7), side, per_m,
                          swin=(3115.0, C.LAP)) for side in (+1, -1)]
    B = {k: np.concatenate([b[k] for b in bands]) for k in bands[0]}
    hg = T.habitat(gr, gz, cam, B["x"], B["y"], None)
    shoulder = (~B["inside"]) & (B["f"] > 0.0) & (B["f"] < 42.0)
    cx, cy = C.world_to_circuit(B["x"], B["y"])
    south = shoulder & (cy < 0.0)
    keep_old = (hg["built"] < 0.35) | B["inside"]
    keep_new = (hg["paved"] < 0.35) | B["inside"]
    out["verge_shoulder_south_old"] = int((south & keep_old).sum())
    out["verge_shoulder_south_new"] = int((south & keep_new).sum())
    # THE ASSERTION IS COMPLETENESS, NOT A RATIO, and the first version of it got that
    # wrong.  It demanded a 40x gain, which silently assumes the old count was ~0; the
    # old count is 27,051, because the drawn district's 26 m feather lets the two ENDS
    # of the pit straight through.  So the fix could not exceed 11.3x however perfect
    # it was, and a correct fix reported FAIL.  What actually matters is that the
    # shoulder is now WHOLE -- every sample of it, not a multiple of what survived.
    frac = (south & keep_new).sum() / max(1, south.sum())
    check("1  pit-straight SOUTH shoulder, verge band COMPLETE",
          frac > 0.98,
          "%d -> %d of %d samples  (%.1f %% -> %.1f %% complete, %.1fx)"
          % ((south & keep_old).sum(), (south & keep_new).sum(), south.sum(),
             100.0 * (south & keep_old).sum() / max(1, south.sum()), 100.0 * frac,
             (south & keep_new).sum() / max(1, (south & keep_old).sum())))

    arch = (cy > 23.5) & (cy < 115.0) & (cx > -480.0) & (cx < 100.0) & (~B["inside"])
    out["verge_on_paddock_new"] = int((arch & keep_new & C.apron_platform_mask(
        B["x"], B["y"])).sum())
    check("2  garages / paddock take no verge band",
          out["verge_on_paddock_new"] == 0,
          "%d samples kept on declared paving (of %d in the paddock box)"
          % (out["verge_on_paddock_new"], int(arch.sum())))

    # ---- 3.  THE NEGATIVE CONTROL: nothing on the concrete -------------------------
    # All three ground-cover tiers, over the whole apron region, tested against the
    # contract's own mask rather than against the box this module draws.
    on = {}
    on["verge"] = int((keep_new & C.apron_platform_mask(B["x"], B["y"])
                       & (~B["inside"])).sum())

    mx, my, mr = T.jitter_grid(-600.0, 600.0, -600.0, 600.0, 1.35, 4242)
    hm = T.habitat(gr, gz, cam, mx, my, None)
    dm = (0.34 + 0.5 * T.fbm(mx / 26.0, my / 26.0, 3, seed=91))
    dm *= (1.0 - 0.55 * hm["wood"]) * (1.0 - hm["paved"])
    dm *= T.smoothstep(18.0, 55.0, hm["f"]) * T.smoothstep(700.0, 260.0, hm["dcam"])
    mi = np.where(mr < dm * 0.85 * T.QUAL)[0]
    on["meadow"] = int(C.apron_platform_mask(mx[mi], my[mi]).sum())
    out["meadow_placed"] = int(len(mi))

    tot_s = 0
    for Tr in T.SWARD_TIERS:
        lo, hi = Tr["d0"] - 24.0, Tr["d1"] + 26.0
        sx, sy, sr = T.jitter_grid(-600.0, 600.0, -600.0, 600.0, Tr["pitch"],
                                   8100 + ord(Tr["tag"]))
        h = T.habitat(gr, gz, cam, sx, sy, None)
        band = (h["dcam3"] >= lo) & (h["dcam3"] < hi) & (h["f"] > 12.0)
        d = T.smoothstep(lo, Tr["d0"] + 26.0, h["dcam3"])
        if Tr is not T.SWARD_TIERS[-1]:
            d *= T.smoothstep(hi, Tr["d1"] - 24.0, h["dcam3"])
        d *= T.smoothstep(12.0, 34.0, h["f"]) * (1.0 - h["paved"])
        d *= (1.0 - 0.72 * h["wood"])
        d *= (1.0 - 0.55 * T.smoothstep(0.18, 0.46, h["slope"]))
        d *= np.clip(0.50 + 0.62 * (0.5 + 0.5 * T.fbm(sx / 38.0, sy / 38.0, 3, seed=811)), 0, 1)
        d *= np.clip(0.62 + 0.50 * (0.5 + 0.5 * T.fbm(sx / 9.0, sy / 9.0, 2, seed=813)), 0, 1)
        take = np.where(band & (sr < np.clip(d, 0, 1) * T.SWARD_Q
                                * (0.55 + 0.45 * T.QUAL)))[0]
        take = take[T.outside_corridor(sx[take], sy[take], 2.0)]
        on["sward_" + Tr["tag"]] = int(C.apron_platform_mask(sx[take], sy[take]).sum())
        tot_s += len(take)
    out["sward_placed"] = int(tot_s)
    out["on_concrete"] = on
    check("3  NEGATIVE CONTROL: nothing placed on declared paving",
          sum(on.values()) == 0,
          "verge %d, meadow %d of %d, sward %s of %d"
          % (on["verge"], on["meadow"], len(mi),
             "/".join(str(on["sward_" + t["tag"]]) for t in T.SWARD_TIERS), tot_s))

    # the control's own control: with the OLD mask the same test must also pass, or
    # the test is measuring the mask change rather than the concrete.
    dm_old = (0.34 + 0.5 * T.fbm(mx / 26.0, my / 26.0, 3, seed=91))
    dm_old *= (1.0 - 0.55 * hm["wood"]) * (1.0 - 0.92 * hm["built"])
    dm_old *= T.smoothstep(18.0, 55.0, hm["f"]) * T.smoothstep(700.0, 260.0, hm["dcam"])
    mo = np.where(mr < dm_old * 0.85 * T.QUAL)[0]
    # 3b IS NOT DECORATION.  Run under the OLD mask the same test must FIND something,
    # or assertion 3 is passing because the instrument cannot see clumps on concrete at
    # all.  It finds them: a 0.92 multiplier leaves 8 % of the meadow standing
    # EVERYWHERE, including on build_architecture's paving.  So the drawn district was
    # doing both halves of the wrong thing at once -- sterilising 8 ha of open field
    # while leaking clumps onto the concrete it was drawn to protect.
    on_old = int(C.apron_platform_mask(mx[mo], my[mo]).sum())
    out["meadow_on_concrete_old"] = on_old
    check("3b instrument: the OLD mask DID leak onto the concrete",
          on_old > 0,
          "old meadow %d placed, %d of them on declared paving -> new %d"
          % (len(mo), on_old, on["meadow"]))

    print(json.dumps(out, indent=1))
    print(">> STAGE RESULT: %s" % ("R2_1821_PAVED_OK (0 failures)" if not FAIL
                                   else "R2_1821_PAVED_FAIL " + ",".join(FAIL)))


main()
