"""Part 3: Beat-6 camera optimisation (design frame), occlusion, catch-up chords."""
import numpy as np, math
from build import X, Y, Z, S, V, T, GRAD, LEN, LAP, DS, N, REC

R2D = 180.0/math.pi
WALL = np.array([-350.0, 72.0, 3.10])
WALLN = np.array([math.cos(-40*math.pi/180), math.sin(-40*math.pi/180)])
APER_W = 9.6
GANTRY = np.array([0.0, 0.0, 9.0])

def car_at_t(t):
    tt = t % LAP
    i = int(np.searchsorted(T, tt)); i = min(max(i, 0), N-1)
    return np.array([X[i], Y[i], Z[i]+0.6]), V[i]*3.6, S[i]

def angsep(cam, p, q):
    u = np.asarray(p, float)-np.asarray(cam, float); u /= np.linalg.norm(u)
    w = np.asarray(q, float)-np.asarray(cam, float); w /= np.linalg.norm(w)
    return math.degrees(math.acos(max(-1, min(1, float(u@w)))))

def px_facade(cam, lens, resx=3840):
    d = WALL - np.asarray(cam, float)
    dist = float(np.linalg.norm(d))
    dp = d[:2]/np.linalg.norm(d[:2])
    cosoff = abs(float(dp @ WALLN))
    hfov = 2*math.atan(36.0/2/lens)
    ppm = resx/(2*dist*math.tan(hfov/2))
    return dist, math.degrees(math.acos(min(1, cosoff))), 22.0*cosoff*ppm, APER_W*cosoff*ppm

def lens_for(hfov_deg): return 18.0/math.tan(math.radians(hfov_deg/2))
def hfov_of(lens):      return 2*math.degrees(math.atan(18.0/lens))

def search(t0=7.0, t1=10.0, margin=9.0, lens_min=18.0, zmax=130.0,
           xr=(-520, 200, 10.0), yr=(-620, -120, 10.0), zr=(40, 130, 5.0)):
    best = None
    cars = [car_at_t(t)[0] for t in np.arange(t0, t1+0.01, 0.5)]
    for xc in np.arange(*xr):
        for yc in np.arange(*yr):
            for zc in np.arange(*zr):
                cam = np.array([xc, yc, zc])
                sep = max(max(angsep(cam, c, WALL) for c in cars),
                          angsep(cam, GANTRY, WALL))
                hfov = sep + margin
                if hfov > 95.0: continue
                lens = lens_for(hfov)
                if lens < lens_min: continue
                dist, off, fpx, apx = px_facade(cam, lens)
                if best is None or fpx > best[0]:
                    best = (fpx, apx, cam.copy(), lens, sep, dist, off, hfov)
    return best

def clearance_report(cam, targets, ybands):
    cam = np.asarray(cam, float)
    out = []
    for nm, tg in targets:
        tg = np.asarray(tg, float)
        for ylab, yb in ybands:
            if (cam[1]-yb)*(tg[1]-yb) > 0: continue
            t = (yb-cam[1])/(tg[1]-cam[1])
            p = cam + t*(tg-cam)
            out.append((nm, ylab, yb, p[0], p[2]))
    return out

if __name__ == "__main__":
    print("=== car positions after the line (flying lap) ===")
    for t in np.arange(0, 11, 1.0):
        p, vk, s = car_at_t(t)
        print(f"  t={t:4.1f}s s={s:7.1f} ({p[0]:8.1f},{p[1]:8.1f},{p[2]:+5.2f}) {vk:6.1f} km/h")

    print("\n=== HOLD SEARCH (frame must hold t=+7.0..+10.0 AND the S/F gantry) ===")
    for lm in (18.0, 20.0, 24.0):
        b = search(lens_min=lm)
        fpx, apx, cam, lens, sep, dist, off, hfov = b
        print(f" lens>={lm:4.1f}: cam=({cam[0]:7.1f},{cam[1]:7.1f},{cam[2]:5.1f}) lens={lens:5.1f}mm "
              f"hfov={hfov:5.1f} maxsep={sep:5.1f}  wall {dist:5.0f} m off {off:4.1f}deg "
              f"facade {fpx:5.1f}px aper {apx:5.1f}px")
    # refine around the best
    b = search(lens_min=20.0, xr=(-320, -80, 4.0), yr=(-420, -200, 4.0), zr=(50, 130, 2.0))
    fpx, apx, cam, lens, sep, dist, off, hfov = b
    print(f"\n REFINED: cam=({cam[0]:.1f},{cam[1]:.1f},{cam[2]:.1f}) lens={lens:.1f}mm "
          f"hfov={hfov:.1f} sep={sep:.1f} wall {dist:.0f} m off {off:.1f}deg "
          f"facade {fpx:.1f}px aperture {apx:.1f}px")
    print("  frame check over the hold:")
    for t in np.arange(6.5, 10.6, 0.5):
        c, vk, s = car_at_t(t)
        print(f"    t={t:4.1f} car {np.linalg.norm(c-cam):6.0f} m {vk:5.0f} km/h "
              f"sep(car,wall)={angsep(cam, c, WALL):5.1f} sep(car,gantry)={angsep(cam,c,GANTRY):5.1f}")
    print("  ray crossings (x, z) at key y bands:")
    for nm, yl, yb, px_, pz in clearance_report(
            cam, [("wall", WALL), ("gantry", GANTRY), ("car@+8.5", car_at_t(8.5)[0])],
            [("grandstand front", -30.0), ("grandstand back", -58.0),
             ("track s edge", -8.0), ("centreline", 0.0), ("pit wall", 11.5),
             ("garage front", 23.5), ("garage back", 40.5)]):
        print(f"    {nm:10s} @ {yl:18s} y={yb:6.1f}  x={px_:8.1f}  z={pz:7.2f}")
