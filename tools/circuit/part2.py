"""Part 2: transit, beat timings, doppler, Beat-6 optics, control points."""
import numpy as np, math, json
from build import (E, REC, X, Y, Z, S, V, T, K, GRAD, LEN, LAP, CORNERS, to_world,
                   WX, WY, DS, N, corner_speed, a_trac, a_pow, a_drag, a_brk, G,
                   FREE, RES, PVI, PS, PZ, PL, GRADES, THETA, RM, CD, CW, profile)

R2D = 180.0/math.pi

def kph(v): return v*3.6

# ------------------------------------------------------------ 1. TRANSIT
# world: showroom floor z=0, car centred at origin, nose +3.02, glass plane X=+15
MU_FLOOR, MU_APRON = 0.85, 0.90
FPS = 24.0

def launch():
    v, d, t = 0.0, 0.0, 0.0
    dt = 1/FPS/8
    # 10 frames of sanctioned wheelspin, effective 0.55 of traction
    while t < 10/FPS:
        a = 0.55*MU_FLOOR*11.0
        v += a*dt; d += v*dt; t += dt
    v_ws, d_ws, t_ws = v, d, t
    while d < 11.98:
        a = min(MU_FLOOR*(11.0+0.0022*v*v), 800/max(v, 1)) - 0.00092*v*v
        v += a*dt; d += v*dt; t += dt
    return v, t, v_ws, d_ws, t_ws

V_GLASS, T_LAUNCH, V_WS, D_WS, T_WS = launch()

def roll(v0, dist, mu, dt=1/FPS/8):
    v, d, t = v0, 0.0, 0.0
    while d < dist:
        a = min(mu*(11.0+0.0022*v*v), 800/max(v, 1)) - 0.00092*v*v
        v += a*dt; d += v*dt; t += dt
    return v, t

# apron 49.6 m, merge arc 104.7 m (R150), both unrubbered
V_A, T_A = roll(V_GLASS, 49.6, MU_APRON)
V_M, T_M = roll(V_A, 104.7, MU_APRON)
# 215.6 m of pit straight (full grip) to the line
V_L, T_L = roll(V_M, 215.6, 1.0)

# ------------------------------------------------------------ 2. BEAT 5 elapsed
# car enters the lap at V_L, accelerates on the flat straight, then follows the
# steady-state profile; find line-to-line elapsed time.
def lap_from(v_entry):
    v = v_entry; t = 0.0
    for i in range(N-1):
        v = min(v, V[i])            # can never exceed the steady-state ceiling
        a = min(a_trac(v), a_pow(v)) - a_drag(v) - G*GRAD[i]
        vn = math.sqrt(max(1.0, v*v + 2*a*DS))
        vn = min(vn, V[i+1])
        t += DS/max(0.5*(v+vn), 1.0)
        v = vn
    return t, v

T_LAP_ONSCREEN, V_END = lap_from(V_L)

# ------------------------------------------------------------ 3. DOPPLER
S11_0, S11_1 = 2403.03, 2700.64
def at(s):
    i = int(round(s/DS)) % N
    return X[i], Y[i], Z[i], V[i], T[i]

# choose hover station: peak speed inside S11
mask = (S >= S11_0) & (S <= S11_1)
i_pk = np.argmax(np.where(mask, V, 0))
S_PEAK = S[i_pk]

def doppler(s_station, off=26.0):
    i = int(round(s_station/DS))
    hx, hy = X[i], Y[i]
    # outboard normal: corner turns left through T12, so 'outside' is to the right
    hdg = math.atan2(Y[i+1]-Y[i-1], X[i+1]-X[i-1])
    nx, ny = math.sin(hdg), -math.cos(hdg)     # right-hand normal
    cam = (hx+off*nx, hy+off*ny, Z[i]+2.40)
    rows = []
    for d in (-200, -120, -60, 0, +60, +120, +200):
        j = int(round((s_station+d)/DS))
        p = np.array([X[j], Y[j], Z[j]])
        r = p - np.array(cam)
        rng = np.linalg.norm(r)
        # radial velocity: component of car velocity along camera->car
        hj = math.atan2(Y[j+1]-Y[j-1], X[j+1]-X[j-1])
        vel = V[j]*np.array([math.cos(hj), math.sin(hj), GRAD[j]])
        vr = float(np.dot(vel, r/rng))
        rows.append((d, kph(V[j]), T[j]-T[i], rng, vr, 343.0/(343.0-vr)))
    # time car spends within +-200 m of the station
    j0 = int(round((s_station-200)/DS)); j1 = int(round((s_station+200)/DS))
    return cam, rows, T[j1]-T[j0]

# ------------------------------------------------------------ 4. WORLD OPTICS
def W(x, y):
    a, b = to_world(x, y); return float(a), float(b)

SF_W = W(0.0, 0.0)
BREACH_W = (15.0, 0.0)
BREACH_N = np.array([1.0, 0.0, 0.0])
WALL_CTR = np.array([15.0, 0.0, 3.10])          # 6.2 m clear head
APERTURE_W, APERTURE_H = 9.6, 5.6
APERTURE_C = np.array([15.0, 0.0, 2.85])

def proj(cam, target, aim, lens, sensor=36.0, resx=3840):
    cam = np.array(cam, float); target = np.array(target, float); aim = np.array(aim, float)
    f = aim - cam; f /= np.linalg.norm(f)
    up = np.array([0, 0, 1.0])
    r = np.cross(f, up); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    d = target - cam
    dist = np.linalg.norm(d)
    xh = math.degrees(math.atan2(float(np.dot(d, r)), float(np.dot(d, f))))
    yv = math.degrees(math.atan2(float(np.dot(d, u)), float(np.dot(d, f))))
    hfov = 2*math.degrees(math.atan(sensor/2/lens))
    vfov = 2*math.degrees(math.atan(sensor*9/16/2/lens))
    return dict(dist=dist, h=xh, v=yv, hfov=hfov, vfov=vfov,
                inframe=(abs(xh) < hfov/2 and abs(yv) < vfov/2),
                pxperm=resx/(2*dist*math.tan(math.radians(hfov/2))))

def facade_px(cam, lens, resx=3840):
    cam = np.array(cam, float)
    d = WALL_CTR - cam; dist = float(np.linalg.norm(d))
    cosoff = abs(float(np.dot(-d/dist, BREACH_N)))
    hfov = 2*math.atan(36.0/2/lens)
    ppm = resx/(2*dist*math.tan(hfov/2))
    return dist, math.degrees(math.acos(min(1, cosoff))), 22.0*cosoff*ppm, APERTURE_W*cosoff*ppm

# ------------------------------------------------------------ 5. CONTROL POINTS
def control_points(max_straight=40.0, max_arc_deg=8.0):
    idx = [0]
    for e in REC:
        i0, i1 = int(round(e['s0']/DS)), int(round(e['s1']/DS))
        if e['type'] == 'S':
            n = max(1, int(math.ceil(e['L']/max_straight)))
        else:
            n = max(1, int(math.ceil(abs(e['ang'])/max_arc_deg)))
        for j in range(1, n+1):
            idx.append(i0 + int(round(j*(i1-i0)/n)))
    idx = sorted(set(min(i, N-1) for i in idx))
    return idx

def cp_error(idx):
    """max distance from the analytic centreline to the polyline through cps"""
    P = np.stack([X[idx], Y[idx]], 1)
    worst = 0.0; ws = 0.0
    for a in range(len(idx)-1):
        i0, i1 = idx[a], idx[a+1]
        p0, p1 = P[a], P[a+1]
        seg = p1-p0; L2 = float(seg@seg)
        for i in range(i0, i1+1):
            q = np.array([X[i], Y[i]])
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, float((q-p0)@seg)/L2))
            d = float(np.linalg.norm(q - (p0+t*seg)))
            if d > worst:
                worst = d; ws = S[i]
    return worst, ws

if __name__ == "__main__":
    print("=== LAUNCH / TRANSIT ==========================================")
    print(f"wheelspin phase: {T_WS:.3f} s, {D_WS:.2f} m, exit {kph(V_WS):.1f} km/h")
    print(f"nose meets glass at {kph(V_GLASS):.1f} km/h after {T_LAUNCH:.3f} s over 11.98 m")
    print(f"apron  49.6 m -> {kph(V_A):.1f} km/h  ({T_A:.2f} s)")
    print(f"merge 104.7 m -> {kph(V_M):.1f} km/h  ({T_M:.2f} s)")
    print(f"pit str 215.6 m -> {kph(V_L):.1f} km/h at the line ({T_L:.2f} s)")
    print(f"BEAT 4 (glass -> line) = {T_A+T_M+T_L:.2f} s over {49.6+104.7+215.6:.1f} m")
    print(f"BEAT 5 on-screen line-to-line = {T_LAP_ONSCREEN:.2f} s (steady lap {LAP:.2f} s)")
    print(f"speed at the line, flying lap = {kph(V[0]):.1f} km/h ; out lap {kph(V_L):.1f} km/h")

    print("\n=== S11 / DOPPLER =============================================")
    print(f"S11 peak speed {kph(V[i_pk]):.1f} km/h at s={S_PEAK:.1f}")
    for st in (2520.0, 2545.0, 2570.0):
        cam, rows, dwell = doppler(st)
        print(f"\n station s={st:.0f} cam=({cam[0]:.1f},{cam[1]:.1f},{cam[2]:.2f}) "
              f"dwell +-200 m = {dwell:.2f} s")
        for d, vk, dt, rng, vr, dop in rows:
            print(f"    {d:+5d} m  {vk:6.1f} km/h  t{dt:+6.2f}s  range {rng:6.1f} m "
                  f"vr {vr:+7.1f} m/s  f'/f {dop:.3f}")
        f = [r[5] for r in rows]
        print(f"    doppler ratio {max(f):.3f} -> {min(f):.3f} = "
              f"{12*math.log2(max(f)/min(f)):.2f} semitones")

    print("\n=== WORLD FRAME ================================================")
    print(f"rotation +{THETA*R2D:.1f} deg about the breach face; breach face -> (15, 0)")
    print(f"S/F line world  ({SF_W[0]:.2f}, {SF_W[1]:.2f}, 0.000)")
    for nm, s in (("T15 exit", 3115.0), ("merge", 3675.0-215.6), ("T1 turn-in", 250.0),
                  ("T4 apex", 982.3), ("T8 apex", 1779.3), ("T12 apex", 2723.3)):
        i = int(round(s/DS)) % N
        w = W(X[i], Y[i])
        print(f"  {nm:12s} s={s:7.1f}  design ({X[i]:8.2f},{Y[i]:8.2f})  "
              f"world ({w[0]:8.2f},{w[1]:8.2f}, {Z[i]:+6.2f})")

    print("\n=== CONTROL POINTS =============================================")
    for ms, ma in ((40, 8), (35, 6), (30, 5)):
        idx = control_points(ms, ma)
        err, es = cp_error(idx)
        print(f"  max_straight={ms} max_arc={ma}deg -> {len(idx)} points, "
              f"worst chord error {err:.3f} m at s={es:.0f}")
