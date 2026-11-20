"""Freeze predictions using only the fluid calibration and registered holdout inputs."""
import argparse
import json
from pathlib import Path
import numpy as np
from experiments.E03_vortex.fluid import Tank

OUT=Path(__file__).resolve().parents[2]/"research/results/E07"
N=7
P0=100000.
G=1e-12
C0=2e-12
TIMES=np.arange(161)*.05
SOURCE=(0,3)
REMOTE=(-1,3)


def train(n):
    tank=Tank(n,periodic=(0,1,2))
    u=tank.zeros()
    x,y,_=tank.coords(2)
    k=2*np.pi/tank.length
    u[2][:]=np.cos(k*x)*np.cos(k*y)
    initial=u[2].copy()
    dt=1/64
    for _ in range(32):
        u,_,_,_=tank.step(u,dt)
    amplitude=float(np.sum(initial*u[2])/np.sum(initial**2))
    return {"n":n,"end_amplitude":amplitude,"kappa":-np.log(amplitude)/(2*tank.nu*k*k*.5)}


def laplacian(periodic):
    m=np.zeros((N*N,N*N))
    for i,j in np.ndindex(N,N):
        for di,dj in ((1,0),(0,1)):
            x,y=i+di,j+dj
            if not periodic and (x>=N or y>=N):
                continue
            a=i*N+j; b=(x%N)*N+y%N
            m[a,a]+=1; m[b,b]+=1
            m[a,b]-=1; m[b,a]-=1
    return m


def model(periodic,kappa):
    l,v=np.linalg.eigh(laplacian(periodic))
    source=np.zeros((N,N)); source[SOURCE]=1
    modes=v.T@source.ravel()
    field=(np.exp(-np.outer(TIMES,l)*(G/C0)*kappa)*modes)@v.T
    return field.reshape(-1,N,N)


def features(field):
    trace=field[:,SOURCE[0],SOURCE[1]]
    i=np.flatnonzero(trace<.5)[0]
    half=TIMES[i-1]+(TIMES[i]-TIMES[i-1])*(trace[i-1]-.5)/(trace[i-1]-trace[i])
    return {"half_time_s":float(half),"opposite_1s_fraction":float(field[20,REMOTE[0],REMOTE[1]])}


def run(out):
    out.mkdir(parents=True,exist_ok=True)
    calibration=[train(n) for n in (16,32)]
    kappa=calibration[-1]["kappa"]
    arrays={name:model(periodic,kappa) for name,periodic in (("M1",False),("M2",True))}
    np.savez_compressed(out/"predictions.npz",time_s=TIMES,**arrays)
    record={"training":calibration,"amplitudes_pa":[1000,50000],"kappa_shared":kappa,
            "predictions_fraction":{k:features(a) for k,a in arrays.items()},
            "fit_parameter_counts":{"M0":0,"M1":1,"M2":1},"target_fit_counts":[0,0,0]}
    (out/"predictions.json").write_text(json.dumps(record,indent=2)+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,default=OUT)
    run(p.parse_args().out)
