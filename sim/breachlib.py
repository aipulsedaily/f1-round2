"""BREACH SHARED — the clock, the car, and the wall, for everything in sim/.

Standard library plus numpy only, so it imports identically under the project
venv and inside Blender 5.2.  It builds nothing.

THE TWO CLOCKS, AND WHY THE SIM RUNS ON THE SECOND ONE
======================================================
The film is 2,978 frames at 24 fps.  Beat 3 (frames 865-1056) ramps WORLD time
down to a solved floor of 0.153719 and back, so those 192 film frames consume
exactly 1.600 s of world time and the two clocks are offset by 6.400 s for the
rest of the take.  `anim/filmtime.py` owns that mapping and this module walks it
rather than re-deriving it.

A rigid-body solver integrates in whatever time its frames represent.  Baking the
sim ON FILM FRAMES would therefore apply gravity per film frame while the car
crawls at 15.4 % — the shards would fall at 1 g while the car moves at 0.154 g's
worth of distance, i.e. 6.5x too fast relative to the picture.  That is exactly
the "floaty moon-gravity debris" failure the brief warns about, arrived at from
the opposite direction: the debris would be LEADEN, not floaty, and it would be
leaden only during the ramp, which is the one place anyone is looking.

So the sim runs on a uniform WORLD-time grid at SIM_FPS, with the car driven by
its own world-time transform, and the result is RESAMPLED onto film frames
afterwards.  Gravity, restitution and friction are then all correct by
construction and the slow motion is a sampling operation, not a physics one.

THE SHUTTER IS NOT THIS MODULE'S PROBLEM, AND IS DELIBERATELY FLAT
------------------------------------------------------------------
Cycles integrates motion blur over FILM frames.  The ramp is already baked into
the per-film-frame transforms this module emits, so a shutter that also scaled
with world time would apply the slowdown twice.  180 deg flat over a beat-3 film
frame IS 1/312 s of world time — a 156 fps high-speed camera — which is the
correct instrument for the shot.

WHERE THE CAR ACTUALLY IS WHEN THE GLASS GOES
=============================================
`docs/beat_sheet.json` calls film t = 36.0 (frame 865) "IMPACT".  It is not.
`filmtime.GLASS_WORLD_T` puts the car's ORIGIN on x = 15.000 at that frame, and
the car's nose is +3.020 m ahead of its origin (`anim/carpath.CAR_LEN` 5.698;
`anim/carrig` documents the 3.020 offset as the cause of R2-026 / R2-047).  So
the nose reaches the breach plane when the origin reaches x = 11.980, which the
measured animation puts at film frame 859.85 — 5.15 frames BEFORE beat 3 starts,
while world time is still running at 1.0 and the car is doing 16.4 m/s.

That is not a defect this module may fix: R2-047 records the decision to leave
it, because moving it moves the breach frame, beat 3's ramp, GLASS_WORLD_T and
the 124.0833 s master.  It IS a fact the sim must obey — the glass breaks when
the car arrives, not when the beat sheet says so — so `impact_frame()` is
measured off the geometry and the sim window opens before beat 3 does.
"""

import json
import math
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "anim"), os.path.join(R2, "sim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import filmtime as FT                                              # noqa: E402

# --------------------------------------------------------------------------- #
#  CONSTANTS.  Each one is READ from a named file, never chosen here.
# --------------------------------------------------------------------------- #
FPS = 24
SIM_FPS = 240                 # world-time samples per second.  10 film frames'
                              # worth, and 1.54 samples per film frame at the
                              # ramp floor, which is what the resampler needs.
CAR_JSON = os.path.join(R2, "world", "car_anim_measured.json")
SHEET = os.path.join(R2, "docs", "beat_sheet.json")
WALL_IFACE = os.path.join(R2, "world", "items",
                          "mullion_intact_interface.json")

# anim/carpath.py
CAR_LEN = 5.698
CAR_HALF_W = 2.005 / 2.0
CAR_TOP_Z = 0.992
NOSE_DX = 3.020               # anim/carrig.py: "the car's nose offset, exactly"
TAIL_DX = NOSE_DX - CAR_LEN   # -2.678
WHEEL_R = 0.36                # world/car_anim_car.json
WHEELBASE = 3.6
AXLE_F, AXLE_R = 1.8, -1.8
TRACK_F, TRACK_R = 0.8475, 0.7975     # measured contact half-tracks

GLASS_PLANE_X = 15.000        # world_contract.ACCESS_GLASS_X

# Material numbers, used for mass and for the constraint thresholds.
RHO_GLASS = 2500.0            # kg/m3, soda-lime
RHO_PVB = 1070.0
RHO_ALU = 2700.0


# --------------------------------------------------------------------------- #
#  1.  THE CLOCK
# --------------------------------------------------------------------------- #

class Clock(object):
    """film frame <-> world seconds, both ways, walking filmtime's own ramp."""

    def __init__(self, sheet_path=SHEET):
        with open(sheet_path) as fh:
            self.sheet = json.load(fh)
        self.total = int(self.sheet["total_frames"])
        self.scales, self.info = FT.build_time_map(self.sheet, self.total, FPS)
        self.wt = FT.world_time_table(self.scales, self.total, FPS)
        self._w = np.array(self.wt[1:])            # world t at frames 1..N
        # the ramp must integrate to what the sheet declares, or nothing below
        # is worth reading
        r = self.info[0]
        assert abs(r["achieved_world_s"] - r["declared_world_s"]) < 1e-6, r
        self.ramp_frames = tuple(r["frames"])
        self.floor = r["solved_floor"]

    def world_t(self, frame):
        """World seconds at a film frame; linear between frames."""
        f = np.clip(np.asarray(frame, float), 1.0, self.total)
        i = np.floor(f).astype(int)
        w = f - i
        j = np.minimum(i + 1, self.total)
        return self._w[i - 1] * (1.0 - w) + self._w[j - 1] * w

    def frame_at_world_t(self, t):
        """The film frame at a world time.  The map is monotone (every scale is
        > 0), so a search is exact."""
        t = np.asarray(t, float)
        i = np.searchsorted(self._w, t).clip(1, self.total - 1)
        w0, w1 = self._w[i - 1], self._w[i]
        d = np.where(np.abs(w1 - w0) < 1e-12, 1.0, w1 - w0)
        return i + (t - w0) / d


# --------------------------------------------------------------------------- #
#  2.  THE CAR
# --------------------------------------------------------------------------- #

class Car(object):
    """CAR_ROOT's measured per-film-frame transform, re-indexed by WORLD time.

    The transform is READ from `world/car_anim_measured.json`, which is a sample
    of `world/car_anim.blend` itself, so this cannot drift from the animation
    the film renders.  Nothing here modifies the car: the sim layers on top of a
    motion that is authored as one continuous rigid body through the breach,
    with no yaw, no lock-up and no impact response, and any change to that
    belongs in the car rig.
    """

    def __init__(self, path=CAR_JSON, clock=None):
        with open(path) as fh:
            d = json.load(fh)
        self.meta = {k: v for k, v in d.items() if k != "frames"}
        fr = d["frames"]
        self.n = len(fr)
        self.loc = np.array([f["loc"] for f in fr], float)
        self.rot = np.array([f["rot"] for f in fr], float)   # XYZ euler, rad
        self.clock = clock or Clock()
        assert self.n == self.clock.total, (self.n, self.clock.total)
        self.wt = self.clock._w

    # -- identity -------------------------------------------------------- #
    def identity_ok(self, stamp=None):
        """The measured file must still describe the blend on disk.

        REMOTE RUNS.  The bake is 3,090 bodies and 9,612 constraints and does
        not fit in this box's remaining RAM while other agents hold 7 GB, so it
        goes to the rented machine via `rq exec` — where `world/car_anim.blend`
        does not exist and never will (it is 300 MB of car the sim does not
        need; only its measured transform table travels).

        The check does NOT get skipped there.  It is performed LOCALLY at bundle
        time and its result is written to a STAMP that travels in the bundle,
        content-addressed with everything else.  The remote side then asserts
        that the stamp describes the very `car_anim_measured.json` it is holding.
        A stamp that does not match the measurement it ships with is refused;
        an absent stamp is refused.  What cannot be verified remotely is only
        that the blend has not changed SINCE the bundle was built, and that
        window is the submit itself.
        """
        p = self.meta.get("blend")
        if p and os.path.exists(p):
            st = os.stat(p)
            if self.meta.get("blend_bytes") != st.st_size:
                return False, ("%s is %d bytes, was %s when sampled"
                               % (p, st.st_size, self.meta.get("blend_bytes")))
            return True, "%s, %d bytes (checked against the blend)" % (
                os.path.basename(p), st.st_size)
        stamp = stamp or os.path.join(R2, "sim", "out", "car_identity.json")
        if not os.path.exists(stamp):
            return False, ("sampled blend %r is not on disk and there is no "
                           "identity stamp at %s" % (p, stamp))
        with open(stamp) as fh:
            sd = json.load(fh)
        for k in ("blend", "blend_bytes", "blend_mtime"):
            if sd.get(k) != self.meta.get(k):
                return False, ("the identity stamp describes %r/%s, the "
                               "measurement in hand is %r/%s"
                               % (sd.get("blend"), sd.get("blend_bytes"),
                                  self.meta.get("blend"),
                                  self.meta.get("blend_bytes")))
        if sd.get("measured_sha256") != _sha256(CAR_JSON):
            return False, "the stamp's sha256 is not this measurement's"
        return True, ("%s, %d bytes (stamped locally %s)"
                      % (os.path.basename(str(p)), sd["blend_bytes"],
                         sd.get("stamped_at")))

    # -- sampling -------------------------------------------------------- #
    def at_world_t(self, t):
        """(loc, euler) at world time t, linear in world time.

        Linear is right and bezier would be wrong: this is a RESAMPLE of an
        already-authored curve onto a denser grid, and any smoothing here would
        put the sim's car somewhere the film's car is not.
        """
        t = np.atleast_1d(np.asarray(t, float))
        i = np.searchsorted(self.wt, t).clip(1, self.n - 1)
        w0, w1 = self.wt[i - 1], self.wt[i]
        d = np.where(np.abs(w1 - w0) < 1e-12, 1.0, w1 - w0)
        a = ((t - w0) / d)[:, None]
        loc = self.loc[i - 1] * (1 - a) + self.loc[i] * a
        rot = self.rot[i - 1] * (1 - a) + self.rot[i] * a
        return loc, rot

    def nose_x(self, frame=None):
        """World x of the nose at every film frame."""
        return self.loc[:, 0] + NOSE_DX

    def impact_frame(self):
        """The FRACTIONAL film frame at which the nose reaches x = 15.000.

        Measured off the animation, not read off the beat sheet.  See the module
        docstring: they disagree by 5.15 frames and the animation is the one the
        camera photographs.
        """
        x = self.nose_x()
        idx = np.where(x >= GLASS_PLANE_X)[0]
        if len(idx) == 0:
            raise RuntimeError("the car never reaches the glass plane")
        j = int(idx[0])                       # first frame at/over the plane
        if j == 0:
            return 1.0
        x0, x1 = x[j - 1], x[j]
        a = (GLASS_PLANE_X - x0) / (x1 - x0)
        return float(j + a)                   # frames are 1-based: index j == frame j+1

    def impact_world_t(self):
        return float(self.clock.world_t(self.impact_frame()))


# --------------------------------------------------------------------------- #
#  3.  THE CAR'S COLLIDER
# --------------------------------------------------------------------------- #
#  A convex DECOMPOSITION, in the car's local frame, metres.  Each part is a
#  convex point cloud; the sim gives each its own CONVEX_HULL body and parents
#  them to one animated empty.
#
#  WHY A PROXY AND NOT THE CAR'S OWN 616 MESHES
#  --------------------------------------------
#  * an active body may only carry a CONVEX shape in Bullet, and the car is
#    emphatically not convex; its own mesh would have to be decomposed anyway
#  * the car is a PASSIVE KINEMATIC body here — it is not being simulated, it is
#    a moving boundary condition — so what matters is its SILHOUETTE and its
#    stiff features, not its surface detail
#  * loading `world/car_anim.blend` (300 MB, 616 meshes) into the sim scene
#    would put the whole car in the sim cache for no physical gain
#
#  Every dimension below is from `world/car_anim_car.json`, `anim/carpath.py`
#  and the measured contact points, and `verify_proxy()` asserts the proxy's
#  bounding box against them rather than trusting this comment.

def car_proxy_parts():
    """[(name, Nx3 local points)] — the convex parts of the car collider."""
    hw = CAR_HALF_W
    parts = []

    def box(nm, x0, x1, y0, y1, z0, z1):
        pts = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1)
                        for z in (z0, z1)], float)
        parts.append((nm, pts))

    def wedge(nm, pts):
        parts.append((nm, np.asarray(pts, float)))

    # --- front wing: full width, 0.070 .. 0.290 high, the first thing to arrive
    box("wing_f", 2.560, NOSE_DX, -0.950, 0.950, 0.070, 0.185)
    # endplates, stiff vertical fins at the tips
    box("ep_l", 2.500, NOSE_DX, 0.880, 0.950, 0.055, 0.290)
    box("ep_r", 2.500, NOSE_DX, -0.950, -0.880, 0.055, 0.290)
    # --- nose cone: a tapered wedge from the tip back to the bulkhead
    wedge("nose", [
        (2.980, -0.055, 0.360), (2.980, 0.055, 0.360),
        (2.980, -0.055, 0.470), (2.980, 0.055, 0.470),
        (1.500, -0.300, 0.200), (1.500, 0.300, 0.200),
        (1.500, -0.300, 0.620), (1.500, 0.300, 0.620)])
    # --- monocoque / survival cell
    wedge("tub", [
        (1.500, -0.300, 0.030), (1.500, 0.300, 0.030),
        (1.500, -0.310, 0.640), (1.500, 0.310, 0.640),
        (-0.300, -0.420, 0.020), (-0.300, 0.420, 0.020),
        (-0.300, -0.430, 0.900), (-0.300, 0.430, 0.900)])
    # --- sidepods, left and right
    for s, nm in ((+1, "pod_l"), (-1, "pod_r")):
        wedge(nm, [
            (1.000, s * 0.300, 0.040), (1.000, s * 0.740, 0.100),
            (1.000, s * 0.300, 0.560), (1.000, s * 0.700, 0.480),
            (-1.100, s * 0.300, 0.040), (-1.100, s * 0.560, 0.090),
            (-1.100, s * 0.300, 0.620), (-1.100, s * 0.520, 0.520)])
    # --- airbox / roll hoop / halo crown
    box("airbox", -0.700, 0.100, -0.230, 0.230, 0.780, CAR_TOP_Z)
    box("halo", 0.500, 1.150, -0.240, 0.240, 0.860, 0.960)
    # --- engine cover and rear structure
    wedge("cover", [
        (-0.300, -0.430, 0.030), (-0.300, 0.430, 0.030),
        (-0.300, -0.420, 0.860), (-0.300, 0.420, 0.860),
        (-2.100, -0.170, 0.030), (-2.100, 0.170, 0.030),
        (-2.100, -0.160, 0.560), (-2.100, 0.160, 0.560)])
    # --- floor
    box("floor", -2.100, 1.500, -0.760, 0.760, 0.008, 0.055)
    # --- rear wing
    box("wing_r", TAIL_DX, -2.200, -0.535, 0.535, 0.700, 0.980)
    box("rep_l", TAIL_DX, -2.150, 0.500, 0.535, 0.320, 0.980)
    box("rep_r", TAIL_DX, -2.150, -0.535, -0.500, 0.320, 0.980)
    # --- four wheels, as 16-gons of the tyre's outer profile
    for ax, tr, tag in ((AXLE_F, TRACK_F, "F"), (AXLE_R, TRACK_R, "R")):
        w = 0.305 if tag == "F" else 0.405       # tyre section width
        for s, side in ((+1, "L"), (-1, "R")):
            th = np.linspace(0, 2 * math.pi, 16, endpoint=False)
            ring = np.c_[ax + WHEEL_R * np.cos(th),
                         np.zeros(16),
                         WHEEL_R + WHEEL_R * np.sin(th)]
            inner = ring.copy()
            inner[:, 1] = s * (tr - 0.5 * w)
            outer = ring.copy()
            outer[:, 1] = s * (tr + 0.5 * w)
            parts.append(("tyre_%s%s" % (tag, side),
                          np.vstack([inner, outer])))
    return parts


def verify_proxy():
    """The proxy's envelope against the numbers it claims to be built from."""
    parts = car_proxy_parts()
    P = np.vstack([p for _n, p in parts])
    lo, hi = P.min(axis=0), P.max(axis=0)
    out = dict(
        n_parts=len(parts), n_points=len(P),
        bbox_min=lo.tolist(), bbox_max=hi.tolist(),
        length=float(hi[0] - lo[0]), width=float(hi[1] - lo[1]),
        height=float(hi[2] - lo[2]))
    out["checks"] = [
        ("nose at +%.3f" % NOSE_DX, abs(hi[0] - NOSE_DX) < 1e-9),
        ("tail at %.3f" % TAIL_DX, abs(lo[0] - TAIL_DX) < 1e-9),
        ("length == CAR_LEN %.3f" % CAR_LEN,
         abs(out["length"] - CAR_LEN) < 1e-9),
        ("width == 2.005", abs(out["width"] - 2.0 * CAR_HALF_W) < 0.06),
        ("top == CAR_TOP_Z %.3f" % CAR_TOP_Z, abs(hi[2] - CAR_TOP_Z) < 1e-9),
        ("nothing below the ground plane", lo[2] >= -1e-9),
        ("every part is a real volume",
         all(len(p) >= 4 and np.linalg.matrix_rank(p - p.mean(0)) == 3
             for _n, p in parts)),
    ]
    out["ok"] = all(c for _n, c in out["checks"])
    return out


# --------------------------------------------------------------------------- #
#  4.  THE WALL
# --------------------------------------------------------------------------- #

def _sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def write_stamp(path=None):
    """Verify the measurement against the blend HERE, and record it."""
    import datetime
    path = path or os.path.join(R2, "sim", "out", "car_identity.json")
    with open(CAR_JSON) as fh:
        meta = json.load(fh)
    b = meta.get("blend")
    if not b or not os.path.exists(b):
        raise SystemExit("REFUSING to stamp: %r is not on disk" % b)
    st = os.stat(b)
    if meta.get("blend_bytes") != st.st_size:
        raise SystemExit("REFUSING to stamp: %s is %d bytes, the measurement "
                         "says %s" % (b, st.st_size, meta.get("blend_bytes")))
    d = dict(blend=b, blend_bytes=meta["blend_bytes"],
             blend_mtime=meta.get("blend_mtime"),
             measured_sha256=_sha256(CAR_JSON),
             stamped_at=datetime.datetime.now().isoformat(timespec="seconds"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(d, fh, indent=1)
    return path, d


def wall_iface(path=WALL_IFACE):
    with open(path) as fh:
        return json.load(fh)


def sim_window(car=None, pre_s=0.60, post_s=6.30):
    """(t0, t1, n_frames) — the WORLD-time span the sim covers.

    Opens `pre_s` before the nose reaches the plane for TWO reasons, and the
    second one sets the number: every body has to settle into its own contact
    set before anything hits it, AND the 2|3 seam test needs 14 film frames of
    neighbourhood on the early side of frame 865 to have anything to compare
    the seam against.  0.60 s of world time at scale 1.0 is 14.4 film frames,
    putting the table's first frame at 845 and giving the seam statistic 20
    frames of run-up.  At 0.20 s it started at 855 and the seam check returned
    "OUTSIDE THE TABLE" — a check that cannot run is not a check that passed.
    It closes `post_s` after,
    which is what it takes for a 10 mm fragment thrown at 16 m/s to stop
    skittering on concrete.  The film's ramp is entirely inside this window:
    beat 3 consumes 1.600 s of world time and beat 4 starts immediately after,
    so `t1` has to clear the impact by more than that or the wound would still
    be moving when the camera turns away.
    """
    car = car or Car()
    t0 = car.impact_world_t() - pre_s
    t1 = car.impact_world_t() + post_s
    n = int(round((t1 - t0) * SIM_FPS)) + 1
    return t0, t1, n


def sim_frame_world_t(t0, n):
    return t0 + np.arange(n) / float(SIM_FPS)


def report():
    c = Clock()
    car = Car(clock=c)
    ok, why = car.identity_ok()
    fi = car.impact_frame()
    t0, t1, n = sim_window(car)
    beat3 = [b for b in c.sheet["beats"] if b["name"] == "3_breach"][0]
    return dict(
        car_blend_identity=dict(ok=ok, detail=why),
        total_frames=c.total, ramp_frames=list(c.ramp_frames),
        ramp_floor=c.floor,
        beat3_declared_impact_frame=int(round(beat3["start_s"] * FPS)) + 1,
        measured_nose_at_plane_frame=fi,
        disagreement_frames=fi - (int(round(beat3["start_s"] * FPS)) + 1),
        nose_offset_m=NOSE_DX,
        car_origin_x_at_impact=float(np.interp(
            fi, np.arange(1, c.total + 1), car.loc[:, 0])),
        car_speed_at_impact_ms=float(
            (np.interp(fi + 0.5, np.arange(1, c.total + 1), car.loc[:, 0])
             - np.interp(fi - 0.5, np.arange(1, c.total + 1), car.loc[:, 0]))
            * FPS),
        impact_world_t=car.impact_world_t(),
        sim_window_world_s=[t0, t1], sim_frames=n, sim_fps=SIM_FPS,
        film_frames_covered=[float(c.frame_at_world_t(t0)),
                             float(c.frame_at_world_t(t1))],
        proxy=verify_proxy())


if __name__ == "__main__":
    if "--stamp" in sys.argv:
        p, d = write_stamp()
        print("wrote %s\n%s" % (p, json.dumps(d, indent=1)))
    else:
        print(json.dumps(report(), indent=1, default=float))
