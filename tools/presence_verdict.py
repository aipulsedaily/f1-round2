"""The verdict: what the measurement says about the three predicted errors.

    python3 tools/presence_verdict.py --presence docs/screen_presence.json \
        [--control /tmp/control_objects.json --subject docs/screen_presence_objects.json]

Prints, in order:
  0. the POSITIVE CONTROL -- does the instrument fail the camera known to be bad?
  1. FRUSTUM  -- manifest px vs measured in-frame px
  2. MOTION   -- how many items never resolve surface detail, and what they carry
  3. BUDGET   -- where the frames actually go, MEASURED per beat rather than tagged
  4. the re-tier, with agent counts, against the scope plan's proposal
  5. the items whose tier moves furthest, both directions
"""
import json, argparse, collections
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--presence", required=True)
ap.add_argument("--control", default="")
ap.add_argument("--subject", default="")
a = ap.parse_args()

P = json.load(open(a.presence))
items = P["items"]
ok = [r for r in items if r["measured"]]

# ---------------------------------------------------------------- 0. control
if a.control and a.subject:
    C = json.load(open(a.control))
    S = json.load(open(a.subject))
    cs = {o["object"]: o for o in C["objects"]}
    ss = {o["object"]: o for o in S["objects"]}
    common = sorted(set(cs) & set(ss))
    print("=" * 78)
    print("0. POSITIVE CONTROL — the same measurement against the camera known to be bad")
    print("   (current rig, orientation frozen at frame 754: the pre-#34 defect,")
    print("    positions untouched so the ONLY difference is where it points)")
    # The first version of this check summed point-frames over the whole world
    # and asked for a 25 % drop. It got 77.6 % and declared the instrument
    # broken. The instrument was fine; the STATISTIC was. A camera flying the
    # circuit with a frozen orientation still has ground in front of it on most
    # frames, and a frozen stare at slow-moving terrain is SHARPER than a
    # tracking one -- the control's total sharp frames are 162 % of the
    # subject's. Aggregate world coverage cannot tell a camera pointed at the
    # film from one pointed at a field. Per-object presence can.
    sa = np.array([float(ss[k].get("peak_unocc_sharp_px_per_m") or 0) for k in common])
    cb = np.array([float(cs[k].get("peak_unocc_sharp_px_per_m") or 0) for k in common])
    fa = np.array([float(ss[k].get("frames_sharp") or 0) for k in common])
    fb = np.array([float(cs[k].get("frames_sharp") or 0) for k in common])
    lost_all = int(((fb == 0) & (fa > 0)).sum())
    halved = int((cb < sa / 2).sum())
    print(f"   objects compared                       {len(common):5d}")
    print(f"   objects that lose ALL sharp presence    {lost_all:5d}"
          f"   ({100.0*lost_all/len(common):.1f} %)")
    print(f"   objects that lose >= half their peak    {halved:5d}"
          f"   ({100.0*halved/len(common):.1f} %)")
    print(f"   NAIVE aggregate (why it had to be dropped): total sharp frames "
          f"subject {int(fa.sum()):,d} vs control {int(fb.sum()):,d} "
          f"= {100.0*fb.sum()/max(1,fa.sum()):.0f} %")
    print("   VERDICT:", "the instrument SEES the defect"
          if lost_all > 0.2 * len(common) else
          "*** THE INSTRUMENT DOES NOT SEE THE DEFECT — do not trust anything below ***")
    named = ["BR_Transit_TyreWall", "BR_Transit_Portal", "ARCH_Paving_ApronPlatform",
             "ARCH_LaPasserelle", "ARCH_Grandstand_03_PRINCIPALE", "ARCH_PontPlongee",
             "SURF_Kerb_T4_in0"]
    print("   the objects the film is declared to be ABOUT, peak sharp px/m:")
    for k in named:
        if k in ss and k in cs:
            print(f"     {k:<30} {float(ss[k].get('peak_unocc_sharp_px_per_m') or 0):8.1f}"
                  f"  ->  {float(cs[k].get('peak_unocc_sharp_px_per_m') or 0):8.1f}")

# ---------------------------------------------------------------- 1. frustum
print("=" * 78)
print("1. FRUSTUM — manifest peak px vs MEASURED peak in-frame px")
mpx = np.array([r["manifest_onscreen_px_4k"] for r in ok], float)
peak = np.array([r["measured"]["peak_px_4k"] for r in ok], float)
sharp = np.array([r["measured"]["peak_sharp_px_4k"] for r in ok], float)
usharp = np.array([r["measured"]["peak_unocc_sharp_px_4k"] for r in ok], float)
hero = np.array([r["manifest_hero"] for r in ok])


def line(lbl, v):
    print(f"   {lbl:<32} median {np.median(v):7.0f}   >=300 px {int((v>=300).sum()):4d}"
          f"   <150 px {int((v<150).sum()):4d}   ==0 {int((v==0).sum()):4d}")


line("manifest onscreen_px_4k", mpx)
line("MEASURED peak in-frame", peak)
line("MEASURED peak sharp (smear<=6)", sharp)
line("MEASURED peak sharp+unoccluded", usharp)
r = np.where(peak > 0, mpx / np.maximum(peak, 1e-9), np.nan)
print(f"   manifest overstates peak in-frame size by: median {np.nanmedian(r):.2f}x  "
      f"p10 {np.nanpercentile(r,10):.2f}x  p90 {np.nanpercentile(r,90):.2f}x")
r2 = np.where(sharp > 0, mpx / np.maximum(sharp, 1e-9), np.inf)
fin = np.isfinite(r2)
print(f"   ... and peak SHARP size by:                median {np.median(r2[fin]):.2f}x  "
      f"p10 {np.percentile(r2[fin],10):.2f}x  p90 {np.percentile(r2[fin],90):.2f}x")

# ---------------------------------------------------------------- 2. motion
print("=" * 78)
print("2. MOTION — items that never resolve surface detail at any moment of the film")
inst = np.array([r["instances"] for r in ok], float)
for thr in (60, 150, 300):
    m = usharp < thr
    print(f"   peak sharp+unoccluded < {thr:3d} px : {int(m.sum()):4d} items, "
          f"{int(inst[m].sum()):9,d} instances, {int((m & hero).sum()):4d} of them "
          f"flagged hero in the manifest")
never = np.array([r["measured"]["frames_visible"] == 0 for r in ok])
print(f"   never in frustum on any of 2,978 frames: {int(never.sum())} items")
noc = np.array([not r["measured"]["ever_unoccluded"] for r in ok])
print(f"   never unoccluded-and-sharp:              {int(noc.sum())} items "
      f"(LOWER BOUND on occlusion — see METHOD)")

# ---------------------------------------------------------------- 3. budget
print("=" * 78)
print("3. FRAME BUDGET — where each item EARNS its fidelity, MEASURED")
print("   'earns' = the beat carries frames where the item is >=150 px, sharp and")
print("   unoccluded. Bare visibility is not a fidelity signal: a zone-mapped item")
print("   is 'visible' whenever its zone is, which says nothing about the item.")
BF = [(b, sum(1 for r in ok if r["measured"]["beats"].get(b, {}).get("frames_at_150px", 0) > 0),
       sum(1 for r in ok if [k for k, v in r["measured"]["beats"].items()
                             if v.get("frames_at_150px", 0) > 0] == [b]),
       sum(1 for r in ok if r["measured"]["beats"].get(b, {}).get("frames_at_300px", 0) >= 24))
      for b in ["1_assembly", "2_launch", "3_breach", "4_transit", "5_lap", "6_ending"]]
FR = {"1_assembly": 792, "2_launch": 72, "3_breach": 192, "4_transit": 134,
      "5_lap": 1524, "6_ending": 264}
print(f"   {'beat':<12} {'frames':>7} {'% film':>7} {'>=150px':>8} {'ONLY here':>10} {'HERO here':>10}")
for b, n150, only, nhero in BF:
    print(f"   {b:<12} {FR[b]:7d} {100.0*FR[b]/2978:6.1f}% {n150:8d} {only:10d} {nhero:10d}")

# ---------------------------------------------------------------- 4. re-tier
print("=" * 78)
print("4. RE-TIER")
tc = collections.Counter(r["proposed_tier"] for r in items)
print("   ", dict(tc))


def family(r):
    tok = r["id"].split("_")
    return (r["module"], "_".join(tok[:2]) if len(tok) > 1 else tok[0])


for t in ("HERO", "MID", "BULK", "NEVER", "UNMAPPED"):
    sel = [r for r in items if r["proposed_tier"] == t]
    if not sel:
        continue
    fams = len({family(r) for r in sel})
    print(f"   {t:<9} {len(sel):4d} items -> {fams:4d} (module, name-family) groups")

# ---------------------------------------------------------------- 5. movers
print("=" * 78)
print("5. BIGGEST TIER MOVES")
order = {"HERO": 3, "MID": 2, "BULK": 1, "NEVER": 0, "UNMAPPED": -1}
dn = sorted((r for r in items if r["manifest_hero"] and r["proposed_tier"] in ("BULK", "NEVER")),
            key=lambda r: -r["manifest_onscreen_px_4k"])
print(f"   demoted from HERO to {{BULK, NEVER}}: {len(dn)}")
for r in dn[:20]:
    m = r["measured"] or {}
    print(f"     {r['id']:<32} manifest {r['manifest_onscreen_px_4k']:5d} px @ "
          f"{r['manifest_nearest_camera_m']:5.1f} m -> measured peak "
          f"{m.get('peak_px_4k',0):7.1f} px, sharp {m.get('peak_unocc_sharp_px_4k',0):7.1f} px, "
          f"{m.get('frames_visible',0):5d} frames")
up = sorted((r for r in items if not r["manifest_hero"] and r["proposed_tier"] == "HERO"),
            key=lambda r: -(r["measured"]["peak_unocc_sharp_px_4k"] if r["measured"] else 0))
print(f"   PROMOTED from non-hero to HERO: {len(up)}")
for r in up[:20]:
    m = r["measured"]
    print(f"     {r['id']:<32} manifest {r['manifest_onscreen_px_4k']:5d} px, not hero -> "
          f"measured sharp {m['peak_unocc_sharp_px_4k']:7.1f} px over "
          f"{m['frames_visible']:5d} frames")

# ---------------------------------------------------------------- nearest_camera_m
print("=" * 78)
print("6. THE SUSPECT FIELD — manifest nearest_camera_m vs MEASURED min depth")
nm = np.array([r["manifest_nearest_camera_m"] for r in ok], float)
md = np.array([(r["measured"]["min_depth_m"] or np.nan) for r in ok], float)
g = np.isfinite(md)
print(f"   items comparable: {int(g.sum())}")
print(f"   manifest nearest_camera_m  median {np.median(nm[g]):8.2f} m")
print(f"   MEASURED min depth in frame median {np.median(md[g]):8.2f} m")
rr = md[g] / np.maximum(nm[g], 1e-9)
print(f"   ratio measured/manifest    median {np.median(rr):6.2f}x  "
      f"p10 {np.percentile(rr,10):.2f}x  p90 {np.percentile(rr,90):.2f}x")
print(f"   items where the manifest is CLOSER than anything measured: "
      f"{int((rr > 1.0).sum())} of {int(g.sum())}")
