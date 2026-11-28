# Post-hoc diagnosis (not registered): composition before the first drop below 0.8 cooperators in runs whose
# late-window mean is below 0.8 (if no drop after generation 500, the first drop at all). Run from rung5c_partial_empathy/data/.
import numpy as np, glob
for step in ("c1","c2"):
    er=[]
    for f in sorted(glob.glob(f"{step}/runs/main_test_*.npz")):
        c=np.load(f)["counts"].astype(float)/1000; d=c[:,0]; a=c[:,1]; coop=1-d
        if coop[1501:2001].mean()>=0.8: continue
        t=next((g for g in range(500,2001) if coop[g]<0.8), None)
        if t is None: t=next(g for g in range(0,2001) if coop[g]<0.8)
        er.append((t,a,1-a-d,d))
    print(step, "eroded", len(er))
    for lag in (400,200,100,50,0):
        rows=[e for e in er if e[0]-lag>=0]
        print(f"  {lag:3d} before: ALLC {np.mean([e[1][e[0]-lag] for e in rows]):.3f} DISC {np.mean([e[2][e[0]-lag] for e in rows]):.3f} ALLD {np.mean([e[3][e[0]-lag] for e in rows]):.3f}")
