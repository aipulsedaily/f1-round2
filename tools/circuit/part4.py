"""Part 4: Beat-6 with camera reachability; doppler catch-up chords."""
import numpy as np, math
from build import X, Y, Z, S, V, T, GRAD, LEN, LAP, DS, N
from part3 import car_at_t, angsep, px_facade, lens_for, hfov_of, WALL, WALLN, GANTRY

def car_before(t):
    """position t seconds BEFORE the line, on the flying lap"""
    tt = (LAP - t) % LAP
    i = int(np.searchsorted(T, tt)); i = min(max(i, 0), N-1)
    return np.array([X[i], Y[i], Z[i]]), V[i]*3.6, S[i]

PEEL_T = 3.0
PP, PV, PS_ = car_before(PEEL_T)
PEEL = np.array([PP[0], PP[1], 2.8])
PEEL_V = PV/3.6

def search(t0, t1, margin=9.0, lens_min=20.0, chord_max=430.0, turn_max=85.0,
           xr=(-260, 400, 8.0), yr=(-620, -60, 8.0), zr=(40, 130, 4.0)):
    best = None
    cars = [car_at_t(t)[0] for t in np.arange(t0, t1+0.01, 0.5)]
    for xc in np.arange(*xr):
        for yc in np.arange(*yr):
            for zc in np.arange(*zr):
                cam = np.array([xc, yc, zc])
                d = cam - PEEL
                ch = float(np.linalg.norm(d))
                if ch > chord_max: continue
                if abs(math.degrees(math.atan2(d[1], d[0]))) > turn_max: continue
                sep = max(max(angsep(cam, c, WALL) for c in cars),
                          angsep(cam, GANTRY, WALL))
                hfov = sep + margin
                if hfov > 95.0: continue
                lens = lens_for(hfov)
                if lens < lens_min: continue
                dist, off, fpx, apx = px_facade(cam, lens)
                if best is None or fpx > best[0]:
                    best = (fpx, apx, cam.copy(), lens, sep, dist, off, hfov, ch)
    return best

if __name__ == "__main__":
    print(f"peel-off at t=-{PEEL_T}s : car ({PP[0]:.1f},{PP[1]:.1f}) s={PS_:.1f} "
          f"{PV:.1f} km/h ({PEEL_V:.1f} m/s)")
    print("\n=== reachable hold search ===")
    for (t0, t1) in ((5.0, 8.0), (6.0, 9.0), (7.0, 10.0)):
        for lm in (20.0, 24.0):
            b = search(t0, t1, lens_min=lm)
            if b is None:
                print(f" hold {t0}-{t1}s lens>={lm}: none"); continue
            fpx, apx, cam, lens, sep, dist, off, hfov, ch = b
            cpx = 5.698*3840/(2*np.linalg.norm(car_at_t((t0+t1)/2)[0]-cam)*math.tan(math.radians(hfov/2)))
            print(f" hold {t0:.0f}-{t1:.0f}s lens>={lm:4.1f}: cam=({cam[0]:7.1f},{cam[1]:7.1f},{cam[2]:5.1f}) "
                  f"{lens:5.1f}mm hfov={hfov:5.1f} sep={sep:5.1f} wall {dist:4.0f}m off {off:4.1f}deg "
                  f"facade {fpx:5.1f}px aper {apx:5.1f}px car {cpx:4.1f}px chord {ch:4.0f}m")
    print("\n=== refine best (hold 7-10 s, lens>=22) ===")
    b = search(7.0, 10.0, lens_min=22.0, xr=(-200, 120, 4.0), yr=(-560, -120, 4.0), zr=(40, 130, 2.0))
    fpx, apx, cam, lens, sep, dist, off, hfov, ch = b
    print(f" cam=({cam[0]:.1f},{cam[1]:.1f},{cam[2]:.1f}) lens={lens:.2f}mm hfov={hfov:.1f} "
          f"sep={sep:.1f} wall {dist:.0f} m off {off:.1f} facade {fpx:.1f}px aper {apx:.1f}px "
          f"chord {ch:.0f} m")

    print("\n=== D's station re-evaluated with my geometry ===")
    for cam, lens in (((-55, -460, 104), 26.0), ((-40, -150, 55), 21.0)):
        cam = np.array(cam, float)
        dist, off, fpx, apx = px_facade(cam, lens)
        seps = [angsep(cam, car_at_t(t)[0], WALL) for t in (7, 8.5, 10)]
        print(f"  {tuple(cam)} {lens}mm: hfov {hfov_of(lens):.1f} seps {['%.1f'%s for s in seps]} "
              f"wall {dist:.0f} m off {off:.1f} facade {fpx:.0f}px aper {apx:.0f}px "
              f"chord from peel {np.linalg.norm(cam-PEEL):.0f} m")
