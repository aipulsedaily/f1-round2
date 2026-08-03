"""Circuit VITRINE — final synthesised spec. Plan geometry closure solve."""
import numpy as np, math, json

D2R = math.pi/180.0

# ---------------------------------------------------------------- element list
# type: 'S' straight (length), 'A' arc (radius, angle deg; + = left/CCW)
# name, type, R, ang, length, free?
def elements(s2, s9, s11, s15=560.0):
    E = [
        ("S0  pit straight S/F->T1", 'S', None, None, 250.0),
        ("T1  Vitrine",              'A', 100.0, +62.0, None),
        ("S1  T1-T2 link",           'S', None, None, 40.0),
        ("T2  Threshold",            'A', 110.0, +30.0, None),
        ("S2  east chute",           'S', None, None, s2),
        ("T3  Long Kink",            'A', 140.0, -28.0, None),
        ("S3  hairpin approach",     'S', None, None, 150.0),
        ("T4  LE PIN (hairpin)",     'A', 28.0, +176.0, None),
        ("S4  hairpin exit ramp",    'S', None, None, 175.0),
        ("T5  Rampe",                'A', 75.0, -88.0, None),
        ("S5  climb straight",       'S', None, None, 230.0),
        ("T6  Weave 1",              'A', 88.0, +38.0, None),
        ("S6  esse link a",          'S', None, None, 42.0),
        ("T7  Weave 2",              'A', 82.0, -44.0, None),
        ("S7  esse link b",          'S', None, None, 40.0),
        ("T8  Crest",                'A', 76.0, +46.0, None),
        ("S8  esse link c",          'S', None, None, 45.0),
        ("T9  Weave 4",              'A', 94.0, -30.0, None),
        ("S9  summit run",           'S', None, None, s9),
        ("T10 Panorama 1",           'A', 125.0, +44.0, None),   # SWAPPED: was 150
        ("T10b release",             'A', 400.0, +8.0, None),    # was 420
        ("T11 Panorama 2",           'A', 150.0, +41.4, None),   # SWAPPED: was 125
        ("S11 doppler straight",     'S', None, None, s11),
        ("T12 Doppler",              'A', 50.0, +52.0, None),
        ("S12 T12-T13 link",         'S', None, None, 55.0),
        ("T13 Hook",                 'A', 70.0, +22.0, None),
        ("S13 T13-T14 link",         'S', None, None, 70.0),
        ("T14 Flick",                'A', 90.0, -19.4, None),
        ("S14 T14-T15 link",         'S', None, None, 95.0),
        ("T15 Gate",                 'A', 105.0, +50.0, None),
        ("S15 pit straight T15->S/F",'S', None, None, s15),
    ]
    out = []
    for nm, t, R, ang, L in E:
        if t == 'A':
            L = abs(ang)*D2R*R
        out.append((nm, t, R, ang, L))
    return out


def walk(E, p0=(0.0, 0.0), h0=0.0):
    """Return list of (name,type,R,ang,L,s0,s1,x0,y0,h0deg) and final state."""
    x, y, h = p0[0], p0[1], h0*D2R
    s = 0.0
    rec = []
    for nm, t, R, ang, L in E:
        rec.append(dict(name=nm, type=t, R=R, ang=ang, L=L, s0=s, s1=s+L,
                        x0=x, y0=y, h0=h/D2R))
        if t == 'S':
            x += L*math.cos(h); y += L*math.sin(h)
        else:
            a = ang*D2R
            # centre is 90deg to the left for +ang, to the right for -ang
            sgn = 1.0 if ang > 0 else -1.0
            cx = x - sgn*R*math.sin(h)
            cy = y + sgn*R*math.cos(h)
            th0 = math.atan2(y-cy, x-cx)
            th1 = th0 + a
            x = cx + R*math.cos(th1); y = cy + R*math.sin(th1)
            h += a
        s += L
    return rec, (x, y, h/D2R, s)


def residual(v, Ltarget):
    E = elements(*v)
    _, (x, y, hd, s) = walk(E)
    return np.array([x, y, s - Ltarget])


def solve(Ltarget, guess=(266.1, 224.9, 306.4)):
    v = np.array(guess, float)
    for _ in range(80):
        r = residual(v, Ltarget)
        J = np.zeros((3, 3))
        for j in range(3):
            dv = v.copy(); dv[j] += 1e-4
            J[:, j] = (residual(dv, Ltarget) - r)/1e-4
        v = v - np.linalg.solve(J, r)
        if np.max(np.abs(residual(v, Ltarget))) < 1e-10:
            break
    return v, residual(v, Ltarget)


if __name__ == "__main__":
    for L in (3675.0, 3650.0, 3700.0):
        v, r = solve(L)
        E = elements(*v)
        _, fin = walk(E)
        print(f"Ltarget={L}: S2={v[0]:.4f} S9={v[1]:.4f} S11={v[2]:.4f}  resid={r}  end={fin}")
