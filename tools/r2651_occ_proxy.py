"""Occlusion PROXY, v2. v1 was a broken instrument and this records why.

v1 reported SURF_Track -- THE ROAD THE CAR IS DRIVING ON -- as the occluder on
1,102 of 1,524 beat-5 frames. Of course it did: the road lies along the line of
sight to a car sitting on the road, so every road point inside the corridor
scored. That is this project's most repeated detector failure (a metric latching
onto the ground / a back wall) and it must not be reported as a finding.

v2 excludes the GROUND CLASSES by name -- the running surface, its kerbs, the
terrain and the paving -- because none of them can hide a car standing on them.
Everything that can (barriers, architecture, dressing, bridges) is kept.

STILL A PROXY, NOT A RAYCAST: a point cloud has gaps, so it UNDER-reads, and it
cannot tell a see-through catch fence from concrete. The fence channel is
therefore reported separately and never folded into the solid count.
"""
import json, sys, collections, numpy as np
R='/home/zany/f1-round2/'
z=np.load(R+'docs/screen_presence_points.npz',allow_pickle=True)
P=z['pts'].astype(np.float64); OBJ=z['obj']; names=np.asarray(z['names'])
GROUND=('SURF_','TER_','ARCH_Paving','ARCH_Apron','ARCH_Forecourt')
FENCE=('Fence','Mesh','Catch','Debris','Screen')
is_ground=np.array([any(g in str(s) for g in GROUND) for s in names])
keep=~is_ground[OBJ]
P=P[keep]; OBJ=OBJ[keep]
print('points: %d total, %d after dropping the %d ground-class objects'
      %(len(keep),len(P),int(is_ground.sum())))
print('  dropped classes present:',sorted({str(s).split('_')[0] for s in names[is_ground]}))
path={r['f']:r for r in json.load(open(R+'world/camera_rig_path.json'))['path']}
car={r['f']:r for r in json.load(open(R+'world/car_anim_measured.json'))['frames']}
CAR_R=2.0
rows=[]
for f in range(1191,2715):
    if f not in path or f not in car: continue
    O=np.asarray(path[f]['p']); Cc=np.asarray(car[f]['loc'])+np.array([0,0,0.55])
    d=Cc-O; L=np.linalg.norm(d); n=d/L
    V=P-O; t=V@n
    m=(t>2.0)&(t<L-3.0)
    if not m.any(): rows.append((f,0,0,'')); continue
    perp=np.linalg.norm(V[m]-np.outer(t[m],n),axis=1)
    hit=perp<CAR_R*(t[m]/L)
    if not hit.any(): rows.append((f,0,0,'')); continue
    nm=names[OBJ[m][hit]]
    isf=np.array([any(k in str(s) for k in FENCE) for s in nm])
    solid=int((~isf).sum()); fence=int(isf.sum())
    own=''
    if solid:
        u,c=np.unique(nm[~isf],return_counts=True); own=str(u[np.argmax(c)])
    rows.append((f,solid,fence,own))
sol=[r for r in rows if r[1]>0]
print('\n=== beat 5: %d of %d frames have SOLID non-ground points in the lens->car corridor ==='%(len(sol),len(rows)))
if sol:
    fs=[r[0] for r in sol]; runs=[]; s=fs[0]
    for i in range(1,len(fs)+1):
        if i==len(fs) or fs[i]!=fs[i-1]+1:
            runs.append((s,fs[i-1])); s=fs[i] if i<len(fs) else s
    for lo,hi in runs:
        sub=[r for r in sol if lo<=r[0]<=hi]
        c=collections.Counter(r[3] for r in sub)
        print('  f%-5d-%-5d %3d fr %5.2f s   %s'%(lo,hi,hi-lo+1,(hi-lo+1)/24,c.most_common(2)))
fen=[r for r in rows if r[1]==0 and r[2]>0]
print('fence-only frames (see-through in life, opaque to geometry): %d'%len(fen))
for f in (2180,2185,2190,2192,2195,2200):
    r=next((x for x in rows if x[0]==f),None)
    if r: print('   f%-5d solid %4d fence %4d %s'%(f,r[1],r[2],r[3]))
json.dump([{'f':r[0],'solid':r[1],'fence':r[2],'owner':r[3]} for r in rows],open(R+'render/r2651/occ_proxy.json','w'))
print('>> STAGE RESULT: R2651_OCC_PROXY2_OK')
