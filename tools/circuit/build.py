"""Circuit VITRINE — full solve: plan, elevation, speed, world transform, optics."""
import numpy as np, math, json
from geo import elements, walk, solve, D2R

G = 9.81
DS = 0.25
LTARGET = 3675.0

# ---------------------------------------------------------------- 1. plan
FREE, RES = solve(LTARGET)
E = elements(*FREE)
REC, FIN = walk(E)
LEN = FIN[3]

def sample_plan(E, ds=DS):
    xs, ys, hs, ks, ss = [], [], [], [], []
    x, y, h, s = 0.0, 0.0, 0.0, 0.0
    for nm, t, R, ang, L in E:
        n = max(1, int(round(L/ds)))
        step = L/n
        if t == 'S':
            for i in range(n):
                xs.append(x); ys.append(y); hs.append(h); ks.append(0.0); ss.append(s)
                x += step*math.cos(h); y += step*math.sin(h); s += step
        else:
            sgn = 1.0 if ang > 0 else -1.0
            k = sgn/R
            for i in range(n):
                xs.append(x); ys.append(y); hs.append(h); ks.append(k); ss.append(s)
                dh = step*k
                cx = x - sgn*R*math.sin(h); cy = y + sgn*R*math.cos(h)
                th = math.atan2(y-cy, x-cx) + dh
                x = cx + R*math.cos(th); y = cy + R*math.sin(th)
                h += dh; s += step
    xs.append(x); ys.append(y); hs.append(h); ks.append(0.0); ss.append(s)
    return (np.array(xs), np.array(ys), np.array(hs), np.array(ks), np.array(ss))

X, Y, H, K, S = sample_plan(E)
N = len(S)

# ---------------------------------------------------------------- 2. elevation
# PVI = (station, elevation, vertical-curve length)
PVI = [
    (   0.0,  0.000,   0.0),   # S/F line, on the flat pit-straight plateau
    ( 470.0,  0.000,  80.0),   # end of the flat plateau (T2 exit)
    ( 800.0, -0.700, 100.0),   # east chute has drifted down
    ( 950.0, -3.150, 110.0),   # foot of the fall — hairpin braking board
    (1035.0, -3.400,  60.0),   # T4 exit  = LOW POINT
    (1215.0,  5.960,  90.0),   # top of LA RAMPE (+5.20% over 180 m)
    (1790.0,  8.000,  60.0),   # T8 apex = SUMMIT
    (1955.0,  7.700,  80.0),   # summit shelf through T9
    (2095.0,  4.900, 100.0),   # foot of the summit rollover (-2.00% over 140 m)
    (2430.0,  3.850,  70.0),   # sweeper shelf, gently falling
    (2540.0,  3.520, 140.0),   # LE BASCULEMENT — crest at the top of the plunge
    (2700.0, -3.600,  80.0),   # foot of LA PLONGEE (-4.45% over 160 m)
    (2790.0, -3.720,  90.0),   # T12 = west LOW POINT
    (3115.0,  0.000, 120.0),   # T15 exit, back on the plateau
    (LTARGET, 0.000,   0.0),
]

def profile(sarr):
    ps = np.array([p[0] for p in PVI]); pz = np.array([p[1] for p in PVI])
    pl = np.array([p[2] for p in PVI])
    grades = (pz[1:]-pz[:-1])/(ps[1:]-ps[:-1])
    z = np.interp(sarr, ps, pz)
    g = np.zeros_like(sarr)
    for i in range(len(ps)-1):
        m = (sarr >= ps[i]) & (sarr <= ps[i+1])
        g[m] = grades[i]
    for j in range(1, len(ps)-1):
        L = pl[j]
        if L <= 0: continue
        gi, go = grades[j-1], grades[j]
        d = go - gi
        a, b = ps[j]-L/2, ps[j]+L/2
        m = (sarr >= a) & (sarr <= b)
        x = sarr[m] - ps[j]
        z[m] += d/(2*L)*(x + L/2)**2 - d*np.maximum(x, 0.0)
        g[m] = gi + d/L*(x + L/2)
    return z, g, grades, ps, pz, pl

Z, GRAD, GRADES, PS, PZ, PL = profile(S)

# ---------------------------------------------------------------- 3. vehicle
MASS = 830.0
def a_lat(v):    return np.minimum(15.0 + 0.0050*v*v, 48.0)          # D (verified)
def a_trac(v):   return np.minimum(11.0 + 0.0022*v*v, 20.0)          # corrected traction
def a_pow(v):    return 800.0/np.maximum(v, 1.0)                     # 664 kW at the wheels
def a_drag(v):   return 0.00092*v*v
def a_brk(v):    return np.minimum(1.25 + 2.2e-4*v*v, 5.0)*G         # A (grafted)

def corner_speed(R):
    v = 40.0
    for _ in range(80):
        v = math.sqrt(min(15.0 + 0.0050*v*v, 48.0)*R)
    return v

# curvature-limited ceiling
RAD = np.where(np.abs(K) > 1e-9, 1.0/np.maximum(np.abs(K), 1e-9), 1e9)
VCAP = np.array([corner_speed(r) if r < 5e8 else 200.0 for r in RAD])
VCAP = np.minimum(VCAP, 200.0)

def solve_speed():
    v = VCAP.copy()
    for it in range(60):
        v0 = v.copy()
        # forward (traction/power limited)
        for i in range(N-1):
            a = min(a_trac(v[i]), a_pow(v[i])) - a_drag(v[i]) - G*GRAD[i]
            vn = math.sqrt(max(1.0, v[i]**2 + 2*a*DS))
            v[i+1] = min(v[i+1], vn)
        # wrap
        a = min(a_trac(v[-1]), a_pow(v[-1])) - a_drag(v[-1]) - G*GRAD[-1]
        v[0] = min(v[0], math.sqrt(max(1.0, v[-1]**2 + 2*a*DS)))
        # backward (brake limited)
        for i in range(N-1, 0, -1):
            a = a_brk(v[i]) + a_drag(v[i]) + G*GRAD[i]
            vp = math.sqrt(max(1.0, v[i]**2 + 2*max(a, 1.0)*DS))
            v[i-1] = min(v[i-1], vp)
        a = a_brk(v[0]) + a_drag(v[0]) + G*GRAD[0]
        v[-1] = min(v[-1], math.sqrt(max(1.0, v[0]**2 + 2*max(a, 1.0)*DS)))
        if np.max(np.abs(v-v0)) < 1e-6:
            break
    return v

V = solve_speed()
T = np.concatenate([[0.0], np.cumsum(DS/((V[:-1]+V[1:])/2))])
LAP = T[-1]

# ---------------------------------------------------------------- 4. corners
CORNERS = []
for e in REC:
    if e['type'] != 'A':
        continue
    nm = e['name']
    sa = 0.5*(e['s0']+e['s1'])
    i = int(round(sa/DS))
    ia, ib = int(round(e['s0']/DS)), int(round(e['s1']/DS))
    seg = slice(ia, ib+1)
    vap = V[seg].min()
    CORNERS.append(dict(name=nm, R=e['R'], ang=e['ang'], arc=e['L'],
                        s0=e['s0'], s1=e['s1'], sapex=sa,
                        x=X[i], y=Y[i], z=Z[i],
                        v_apex=vap*3.6, v_in=V[ia]*3.6, v_out=V[ib]*3.6,
                        latg=(vap**2/e['R'])/G, t=T[i], grad=GRAD[i]*100))

def brake_zone(s_turnin):
    """walk back from turn-in while the car is decelerating"""
    i = int(round(s_turnin/DS))
    j = i
    while j > 1 and V[j-1] > V[j]:
        j -= 1
    return (S[j], S[i], V[j]*3.6, V[i]*3.6, S[i]-S[j], T[i]-T[j],
            (V[j]**2-V[i]**2)/(2*max(S[i]-S[j], 1e-9))/G)

# ---------------------------------------------------------------- 5. world xform
THETA = 40.0*D2R
CD = np.array([-350.0, 72.0])      # breach-face centre, circuit design frame
CW = np.array([15.0, 0.0])         # breach-face centre, world (round-1 showroom)
RM = np.array([[math.cos(THETA), -math.sin(THETA)], [math.sin(THETA), math.cos(THETA)]])
def to_world(px, py):
    p = np.stack([np.asarray(px, float)-CD[0], np.asarray(py, float)-CD[1]])
    q = RM @ p
    return q[0]+CW[0], q[1]+CW[1]

WX, WY = to_world(X, Y)

# ---------------------------------------------------------------- 6. checks
def min_separation():
    idx = np.arange(0, N, 8)
    P = np.stack([X[idx], Y[idx]], 1)
    sv = S[idx]
    best = 1e9; bi = None
    for a in range(len(idx)):
        d = np.hypot(P[:, 0]-P[a, 0], P[:, 1]-P[a, 1])
        ds_ = np.abs(sv-sv[a]); ds_ = np.minimum(ds_, LEN-ds_)
        m = ds_ > 220.0
        if m.any():
            k = np.argmin(np.where(m, d, 1e9))
            if d[k] < best:
                best = d[k]; bi = (sv[a], sv[k])
    return best, bi

if __name__ == "__main__":
    print("=== PLAN =====================================================")
    print(f"free straights  S2={FREE[0]:.3f}  S9={FREE[1]:.3f}  S11={FREE[2]:.3f}")
    print(f"closure residual {RES}   length {LEN:.4f} m   end heading {FIN[2]:.6f}")
    print(f"net turn {sum(e[3] for e in E if e[3]):+.4f} deg")
    print(f"plan bbox (design frame) {X.max()-X.min():.1f} x {Y.max()-Y.min():.1f}"
          f"   x[{X.min():.1f},{X.max():.1f}] y[{Y.min():.1f},{Y.max():.1f}]")
    print(f"plan bbox (world)        {WX.max()-WX.min():.1f} x {WY.max()-WY.min():.1f}"
          f"   x[{WX.min():.1f},{WX.max():.1f}] y[{WY.min():.1f},{WY.max():.1f}]")
    ms, mi = min_separation()
    print(f"min non-adjacent centreline separation {ms:.1f} m at s={mi}")

    print("\n=== ELEVATION ================================================")
    print(f"z(0)={Z[0]:.4f}  z(end)={Z[-1]:.4f}  closure err {Z[-1]-Z[0]:+.2e}")
    print(f"grad(0)={GRAD[0]*100:+.4f}%  grad(end)={GRAD[-1]*100:+.4f}%")
    print(f"range {Z.max()-Z.min():.3f} m   min {Z.min():.3f} @ s={S[np.argmin(Z)]:.0f}"
          f"   max {Z.max():.3f} @ s={S[np.argmax(Z)]:.0f}")
    print(f"max grade {GRAD.max()*100:+.3f}%  min grade {GRAD.min()*100:+.3f}%")
    print(f"max |dz/ds| discontinuity {np.max(np.abs(np.diff(GRAD)))*100:.5f}%/step (C1 check)")
    print("tangent grades between PVIs:")
    for i in range(len(PS)-1):
        print(f"   s {PS[i]:7.1f} -> {PS[i+1]:7.1f}  z {PZ[i]:+6.3f} -> {PZ[i+1]:+6.3f}"
              f"   g {GRADES[i]*100:+6.3f}%   len {PS[i+1]-PS[i]:6.1f}")

    print("\n=== SPEED ====================================================")
    print(f"LAP {LAP:.3f} s   avg {LEN/LAP*3.6:.1f} km/h")
    print(f"vmax {V.max()*3.6:.1f} km/h @ s={S[np.argmax(V)]:.0f}"
          f"   vmin {V.min()*3.6:.1f} km/h @ s={S[np.argmin(V)]:.0f}")
    for frac in (1/3, 2/3):
        pass
    print("\nbraking zones:")
    for nm, sti in (("T1", 250.0), ("T4", 939.27), ("T10", 2142.81), ("T12", 2700.64)):
        bz = brake_zone(sti)
        print(f"  {nm}: {bz[2]:.0f} -> {bz[3]:.0f} km/h in {bz[4]:.1f} m / {bz[5]:.2f} s"
              f"  mean {bz[6]:.2f} g   (s {bz[0]:.0f}->{bz[1]:.0f})")
    for thr in (200, 250, 300):
        m = V*3.6 > thr
        print(f"  above {thr} km/h: {m.mean()*100:.1f}% by distance, "
              f"{np.sum(np.diff(T)*m[:-1])/LAP*100:.1f}% by time")

    print("\n=== CORNERS ==================================================")
    print(f"{'name':26s} {'R':>5s} {'ang':>7s} {'arc':>7s} {'apexS':>8s} "
          f"{'in':>6s} {'apex':>6s} {'out':>6s} {'latg':>5s} {'z':>6s} {'grd%':>6s} {'t':>6s}")
    for c in CORNERS:
        print(f"{c['name']:26s} {c['R']:5.0f} {c['ang']:+7.1f} {c['arc']:7.1f} {c['sapex']:8.1f} "
              f"{c['v_in']:6.1f} {c['v_apex']:6.1f} {c['v_out']:6.1f} {c['latg']:5.2f} "
              f"{c['z']:+6.2f} {c['grad']:+6.2f} {c['t']:6.2f}")
