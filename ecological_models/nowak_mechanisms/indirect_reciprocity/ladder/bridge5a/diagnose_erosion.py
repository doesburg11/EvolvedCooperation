# Post-hoc diagnosis (not registered): strategy composition before the first late drop below 0.8 cooperators.
# Run from bridge5a/data/: python3 ../diagnose_erosion.py
import numpy as np, glob, json, sys
N=1000
for step in ("b1","b2"):
    er, ok = [], []
    for f in sorted(glob.glob(f"{step}/runs/main_test_*.npz")):
        z=np.load(f); c=z["counts"].astype(float)/N; d=c[:,0]; a=c[:,1]; disc=1-a-d; coop=1-d
        win=coop[1501:2001].mean()
        if win>=0.8: ok.append((a,disc,d)); continue
        t=next(g for g in range(500,2001) if coop[g]<0.8)  # first drop below bar after gen 500
        er.append((t,a,disc,d))
    ts=np.array([e[0] for e in er])
    print(f"{step}: eroded {len(er)}, held {len(ok)}; first drop below 0.8 after gen 500: median {int(np.median(ts))}, IQR {int(np.percentile(ts,25))}-{int(np.percentile(ts,75))}")
    for lag in (400,200,100,50,0):
        A=np.mean([e[1][e[0]-lag] for e in er]); D=np.mean([e[2][e[0]-lag] for e in er]); X=np.mean([e[3][e[0]-lag] for e in er])
        print(f"  eroded, {lag:3d} gens before drop: ALLC {A:.3f} DISC {D:.3f} ALLD {X:.3f}")
    for g in (500,1000,1500,2000):
        A=np.mean([o[0][g] for o in ok]); D=np.mean([o[1][g] for o in ok]); X=np.mean([o[2][g] for o in ok])
        print(f"  held, gen {g}: ALLC {A:.3f} DISC {D:.3f} ALLD {X:.3f}")
    # recovery? eroded runs at gen 2000
    print("  eroded at gen 2000: coop mean %.3f, recovered (coop>=0.8) %d" % (np.mean([1-e[3][2000] for e in er]), sum(1-e[3][2000]>=0.8 for e in er)))
