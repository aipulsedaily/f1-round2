"""Every per-frame claim I made about beat 1, checked on the built path.

R2-842 happened because the FRAMING gate checks KEYS and I made claims about
SPANS. These are the other span claims in the same block.
"""
import json, math, sys
PATH=sys.argv[1] if len(sys.argv)>1 else 'world/R2829_camera_rig_path.json'
P={e['f']:e for e in json.load(open(PATH))['path']}
SW=36.0; SH=36.0*2160/3840
CAR_LO=(-2.70,-1.00,0.34); CAR_HI=(3.02,1.00,1.33)
def qmat(q):
    w,x,y,z=q
    return [[1-2*(y*y+z*z),2*(x*y-w*z),2*(x*z+w*y)],
            [2*(x*y+w*z),1-2*(x*x+z*z),2*(y*z-w*x)],
            [2*(x*z-w*y),2*(y*z+w*x),1-2*(x*x+y*y)]]
def fill(e,lo,hi):
    p=e['p']; R=qmat(e['q']); lens=e['lens']; us=[];vs=[]
    for ix in(0,1):
     for iy in(0,1):
      for iz in(0,1):
       pt=[lo[0] if ix==0 else hi[0], lo[1] if iy==0 else hi[1], lo[2] if iz==0 else hi[2]]
       d=[pt[i]-p[i] for i in range(3)]
       cx=sum(d[i]*R[i][0] for i in range(3)); cy=sum(d[i]*R[i][1] for i in range(3))
       cz=sum(d[i]*R[i][2] for i in range(3))
       if cz>=-1e-6: return None
       us.append(cx/-cz*lens); vs.append(cy/-cz*lens)
    return max((max(us)-min(us))/SW,(max(vs)-min(vs))/SH)
def boxdist(p,lo,hi):
    d=[max(lo[i]-p[i],0.0,p[i]-hi[i]) for i in range(3)]
    return math.sqrt(sum(v*v for v in d))

print('CLAIM 1 — the payoff orbit holds the WHOLE assembled car, every frame')
vals=[(f,fill(P[f],list(CAR_LO),list(CAR_HI))) for f in range(464,793)]
bad=[(f,v) for f,v in vals if v is None or v>1.0]
xs=[v for _,v in vals if v is not None]
print(f'   f464-792  min {min(xs):.3f}  max {max(xs):.3f}  mean {sum(xs)/len(xs):.3f}')
print(f'   frames that do NOT fit: {len(bad)}'+('' if not bad else f'  worst {max(v for _,v in bad):.3f}'))
print('   VERDICT:', 'PASS' if not bad else 'FAIL')

print()
print('CLAIM 2 — the orbit never comes near the car box (floor 0.30 m)')
cl=[(f,boxdist(P[f]['p'],CAR_LO,CAR_HI)) for f in range(464,793)]
mn=min(cl,key=lambda x:x[1])
print(f'   worst clearance {mn[1]:.3f} m @f{mn[0]}   VERDICT:', 'PASS' if mn[1]>0.30 else 'FAIL')

print()
print('CLAIM 3 — beat 1 as a whole never flies through the car')
cl2=[(f,boxdist(P[f]['p'],CAR_LO,CAR_HI)) for f in range(1,793)]
mn2=min(cl2,key=lambda x:x[1])
print(f'   worst clearance {mn2[1]:.3f} m @f{mn2[0]}   VERDICT:', 'PASS' if mn2[1]>0.30 else 'FAIL')

print()
print('CLAIM 4 — the establishing frame is still the beat\'s widest shot (~35% of frame width)')
plan=json.load(open('docs/explode_plan.json'))
lo=[1e9]*3; hi=[-1e9]*3
for k,c in plan['clusters'].items():
    off=c['explode_offset']
    for i in range(3):
        lo[i]=min(lo[i], c['bbox_min'][i]+off[i]); hi[i]=max(hi[i], c['bbox_max'][i]+off[i])
f1=fill(P[1],lo,hi)
print(f'   f1 exploded-field fill {f1:.3f} of frame   (the field is the subject at f1)')
carf1=fill(P[1],list(CAR_LO),list(CAR_HI))
print(f'   f1 assembled-car-box fill {carf1:.3f}  (R2-826 reported f1 = 35.0% by this measure)')
print('   VERDICT:', 'PASS — unchanged' if carf1 is not None and abs(carf1-0.350)<0.02 else 'CHECK')
