"""Final verification + JSON/markdown data emit for circuit VITRINE."""
import numpy as np, math, json
from geo import elements, walk, solve, D2R
from build import (E, REC, X, Y, Z, S, V, T, K, GRAD, LEN, LAP, CORNERS, to_world,
                   WX, WY, DS, N, corner_speed, a_trac, a_pow, a_drag, a_brk, G,
                   FREE, RES, PVI, PS, PZ, PL, GRADES, THETA, RM, CD, CW)
from part2 import (V_GLASS, T_LAUNCH, V_A, T_A, V_M, T_M, V_L, T_L,
                   T_LAP_ONSCREEN, control_points, cp_error, W, SF_W)
from part3 import car_at_t, angsep, WALL, WALLN, GANTRY

R2D = 180.0/math.pi
APER_W, APER_H = 9.6, 5.6
RESX, RESY = 3840, 2160

# ---------------------------------------------------------------- optics helpers
def project_px(cam, lens, target, aim, width, plane_normal=None):
    """rendered pixel width of a `width`-metre object, incl. rectilinear edge stretch"""
    cam = np.asarray(cam, float); target = np.asarray(target, float); aim = np.asarray(aim, float)
    f = aim-cam; f /= np.linalg.norm(f)
    d = target-cam; dist = float(np.linalg.norm(d))
    theta = math.acos(max(-1, min(1, float(f @ (d/dist)))))
    w = width
    if plane_normal is not None:
        dp = d[:2]/np.linalg.norm(d[:2])
        w = width*abs(float(dp @ plane_normal))
    fpx = RESX/2/math.tan(math.atan(18.0/lens))
    return dist, math.degrees(theta), w*fpx/dist/math.cos(theta)**2

def aim_between(cam, a, b):
    cam = np.asarray(cam, float)
    u = (np.asarray(a, float)-cam); u /= np.linalg.norm(u)
    w = (np.asarray(b, float)-cam); w /= np.linalg.norm(w)
    m = u+w; m /= np.linalg.norm(m)
    return cam + 400.0*m

# ---------------------------------------------------------------- BEAT 6
HOLD_CAM = np.array([-120.0, -360.0, 118.0])
HOLD_LENS = 22.0
PEEL = np.array([-260.5, 0.0, 2.8])
KEY0 = np.array([-40.0, -150.0, 62.0])       # t=0, raised from D's 55 to clear grandstands
GRAND_Y = (-34.0, -62.0); GRAND_H = 14.0; GRAND_X = (-420.0, 180.0)

def gs_clear(cam, tgt):
    cam = np.asarray(cam, float); tgt = np.asarray(tgt, float)
    worst = 1e9
    for yb in GRAND_Y:
        if (cam[1]-yb)*(tgt[1]-yb) > 0: continue
        t = (yb-cam[1])/(tgt[1]-cam[1]); p = cam+t*(tgt-cam)
        if GRAND_X[0] <= p[0] <= GRAND_X[1]:
            worst = min(worst, p[2]-GRAND_H)
    return worst

def beat6_report():
    rows = []
    keys = [(-3.0, PEEL, 26.0), (0.0, KEY0, 21.0),
            (2.0, np.array([-53.0, -240.0, 88.0]), 21.5),
            (4.0, np.array([-79.0, -305.0, 106.0]), 21.8),
            (6.0, np.array([-108.0, -348.0, 116.0]), 22.0),
            (7.0, HOLD_CAM, 22.0), (8.5, HOLD_CAM, 22.0), (10.0, HOLD_CAM, 22.0)]
    prev = None
    for t, cam, lens in keys:
        car, vk, sc = car_at_t(t) if t >= 0 else (np.array([-260.5+83.1*t, 0, 0.6]), 299.0, 0)
        aim = aim_between(cam, car, WALL) if t >= 0 else car
        dcar, thcar, pxcar = project_px(cam, lens, car, aim, 5.698)
        dw, thw, pxw = project_px(cam, lens, WALL, aim, 22.0, WALLN)
        _, _, pxa = project_px(cam, lens, np.array([-350.0, 72.0, 2.85]), aim, APER_W, WALLN)
        sep = angsep(cam, car, WALL)
        hfov = 2*math.degrees(math.atan(18.0/lens))
        spd = 0.0 if prev is None else float(np.linalg.norm(cam-prev[1]))/(t-prev[0])
        rows.append(dict(t=t, cam=cam.tolist(), lens=lens, car_d=dcar, car_px=pxcar,
                         car_kph=vk, wall_d=dw, wall_px=pxw, aper_px=pxa, sep=sep,
                         hfov=hfov, fits=sep+6 < hfov, cam_speed=spd,
                         gs_car=gs_clear(cam, car), gs_wall=gs_clear(cam, WALL)))
        prev = (t, cam)
    return rows

# ---------------------------------------------------------------- DOPPLER
DOP_S = 2555.0
def dop_station(s_st=DOP_S, off=26.0):
    i = int(round(s_st/DS))
    hdg = math.atan2(Y[i+1]-Y[i-1], X[i+1]-X[i-1])
    nx, ny = math.sin(hdg), -math.cos(hdg)
    cam = np.array([X[i]+off*nx, Y[i]+off*ny, Z[i]+2.40])
    rows = []
    for d in (-220, -160, -100, -50, 0, +50, +100, +160, +220):
        j = int(round((s_st+d)/DS))
        p = np.array([X[j], Y[j], Z[j]+0.35]); r = p-cam; rng = float(np.linalg.norm(r))
        hj = math.atan2(Y[j+1]-Y[j-1], X[j+1]-X[j-1])
        vel = V[j]*np.array([math.cos(hj), math.sin(hj), GRAD[j]])
        vr = float(vel @ (r/rng))           # +ve = receding
        rows.append((d, V[j]*3.6, T[j]-T[i], rng, vr, 343.0/(343.0+vr)))
    j0, j1 = int(round((s_st-220)/DS)), int(round((s_st+220)/DS))
    return cam, rows, T[j1]-T[j0]

def catchup(s_st=DOP_S, off=26.0, s_follow=3115.0, astern=28.0):
    cam, _, _ = dop_station(s_st, off)
    i = int(round(s_follow/DS))
    hdg = math.atan2(Y[i+1]-Y[i-1], X[i+1]-X[i-1])
    tgt = np.array([X[i]-astern*math.cos(hdg), Y[i]-astern*math.sin(hdg), Z[i]+4.0])
    chord = float(np.linalg.norm(tgt-cam))
    j = int(round(s_st/DS))
    dt = T[i]-T[j]
    path = s_follow-s_st
    return chord, path, dt, chord/dt, path/dt

# ---------------------------------------------------------------- CONTROL POINTS
def cps(tol=0.12, max_straight=40.0, max_arc=12.0):
    idx = [0]
    for e in REC:
        i0, i1 = int(round(e['s0']/DS)), int(round(e['s1']/DS))
        if e['type'] == 'S':
            n = max(1, int(math.ceil(e['L']/max_straight)))
        else:
            th = min(max_arc, 2*math.degrees(math.acos(max(-1, min(1, 1-tol/e['R'])))))
            n = max(1, int(math.ceil(abs(e['ang'])/th)))
        for k in range(1, n+1):
            idx.append(min(i0+int(round(k*(i1-i0)/n)), N-1))
    idx = sorted(set(idx))
    idx[-1] = N-1
    return idx

if __name__ == "__main__":
    print("=== BEAT 6 MOVE ==============================================")
    for r in beat6_report():
        print(f" t{r['t']:+5.1f} cam({r['cam'][0]:7.1f},{r['cam'][1]:7.1f},{r['cam'][2]:5.1f}) "
              f"{r['lens']:5.1f}mm sep{r['sep']:5.1f}/{r['hfov']:5.1f} {'OK' if r['fits'] else 'XX'} | "
              f"car {r['car_d']:5.0f}m {r['car_px']:5.1f}px {r['car_kph']:5.0f}km/h | "
              f"wall {r['wall_d']:5.0f}m {r['wall_px']:6.1f}px aper {r['aper_px']:5.1f}px | "
              f"vcam {r['cam_speed']:5.1f} m/s | gs {r['gs_car']:+7.1f}/{r['gs_wall']:+6.1f}")

    print("\n=== DOPPLER (s=%.0f) =========================================" % DOP_S)
    cam, rows, dwell = dop_station()
    print(f" camera (design frame) ({cam[0]:.1f}, {cam[1]:.1f}, {cam[2]:.2f})   "
          f"world {W(cam[0], cam[1])}   dwell +-220 m = {dwell:.2f} s")
    for d, vk, dt, rng, vr, f in rows:
        print(f"   {d:+5d} m  {vk:6.1f} km/h  t{dt:+6.2f} s  range {rng:6.1f} m  "
              f"vr {vr:+7.1f} m/s  f'/f {f:.3f}")
    fs = [r[5] for r in rows]
    print(f"   sweep {max(fs):.3f} -> {min(fs):.3f} = {12*math.log2(max(fs)/min(fs)):.2f} semitones")
    ch, pa, dt, vc, vcar = catchup()
    print(f"\n catch-up: camera chord {ch:.0f} m vs car path {pa:.0f} m in {dt:.2f} s "
          f"-> ratio {ch/pa:.3f}, camera mean {vc:.1f} m/s ({vc*3.6:.0f} km/h), "
          f"car mean {vcar*3.6:.0f} km/h")
    for alt in (2600.0, 2650.0):
        ch2, pa2, dt2, vc2, _ = catchup(alt)
        print(f"   fallback station s={alt:.0f}: chord {ch2:.0f} m, {dt2:.2f} s, "
              f"mean {vc2:.1f} m/s ({vc2*3.6:.0f} km/h)")

    print("\n=== CONTROL POINTS ===========================================")
    for tol in (0.20, 0.12, 0.08):
        idx = cps(tol)
        err, es = cp_error(idx)
        print(f"  sagitta tol {tol:.2f} m -> {len(idx)} points, measured worst {err:.3f} m at s={es:.0f}")
