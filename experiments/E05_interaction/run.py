"""Intervene on two pairs of phases, and evolve two finite-core rings in the same fluid."""
import argparse
from pathlib import Path
import numpy as np
from experiments.common import save_summary
from experiments.E03_vortex import fluid,observe,topology

OUT=Path(__file__).resolve().parents[2]/"research/results/E05"
MODES=("independent","A_to_B","both","common_clock")
PAIRS={"base":(1.6,4.,.4,.05),"opposite":(1.6,-4.,.4,.05),"far":(2.2,4.,.4,.05),
       "weaker_B":(1.6,2.,.4,.05),"thicker_B":(1.6,4.,.55,.05),"more_viscous":(1.6,4.,.4,.08)}


def phase_rhs(t,p):
    ref=2*np.pi*np.array([1.,np.sqrt(2)])
    rate=np.zeros_like(p)
    rate[...,0,:]=ref
    rate[...,1,:]=ref+[.4,.6]
    diff=p[...,1,:]-p[...,0,:]
    rate[1,...,1,:]-=np.sin(diff[1])
    rate[2,...,0,:]+=np.sin(diff[2])
    rate[2,...,1,:]-=np.sin(diff[2])
    rate[3]+=np.sin(ref*t-p[3])
    return rate


def phases(out):
    out.mkdir(exist_ok=True,parents=True)
    stats=[]
    for hz in (64,128):
        # Together integrate mode, initial condition, intervention, pair, component.
        state=np.zeros((4,3,3,2,2))
        for seed_index,seed in enumerate((11,29,47)):
            state[:,seed_index]=np.random.default_rng(seed).uniform(0,2*np.pi,(2,2))
        times=np.arange(40*hz+1)/hz
        trajectory=np.empty((len(times),*state.shape))
        dt=1/hz
        for i,t in enumerate(times):
            if i==20*hz:
                state[:,:,1,0,:]+=.4
                state[:,:,2,1,:]+=.4
            trajectory[i]=state
            if i==len(times)-1:
                break
            a=phase_rhs(t,state)
            b=phase_rhs(t+dt/2,state+dt*a/2)
            c=phase_rhs(t+dt/2,state+dt*b/2)
            d=phase_rhs(t+dt,state+dt*c)
            state+=dt*(a+2*b+2*c+d)/6
        # Keep one sample every 1/8 s for replaying the intervention and relaxation.
        np.savez_compressed(out/f"phase_{hz}.npz",time=times[::hz//8],phase=trajectory[::hz//8])
        for m,mode in enumerate(MODES):
            for j,seed in enumerate((11,29,47)):
                x=trajectory[:,m,j]
                delta=x[:,0,1,:]-x[:,0,0,:]
                response=x[:,1:]-x[:,0:1]
                baseline=lambda t:np.abs(np.angle(np.exp(1j*response[round(t*hz)])))
                r={"mode":mode,"seed":seed,"hz":hz,
                   "plv_last_10s":np.abs(np.exp(1j*delta[30*hz:]).mean(axis=0)).tolist(),
                   "B_from_A_at_21":baseline(21)[0,1].tolist(),
                   "A_from_B_at_21":baseline(21)[1,0].tolist(),
                   "self_after_A_at_40":baseline(40)[0,0].tolist(),
                   "relative_recovery_error_at_40":np.abs(np.angle(np.exp(1j*(response[-1,0,1]-response[-1,0,0])))).tolist()}
                stats.append(r)
    checks={"registered_direction":all((min(r["B_from_A_at_21"])>.01)==(r["mode"] in ("A_to_B","both")) and
                                       (min(r["A_from_B_at_21"])>.01)==(r["mode"]=="both") for r in stats),
            "common_drive_can_lock":all(min(r["plv_last_10s"])>.99 for r in stats if r["mode"]=="common_clock")}
    save_summary(out,{"runs":stats,"checks":checks},__file__)


def rings(out,case):
    out.mkdir(exist_ok=True,parents=True)
    gap,strength,core,viscosity=PAIRS[case]
    results=[]
    for n,dt in ((32,1/64),(48,1/128)):
        tank=fluid.Tank(n,viscosity=viscosity)
        a=(3-gap/2,4.,.4)
        b=(3+gap/2,strength,core)
        by_group={}
        for group,initial in (("A",[a]),("B",[b]),("AB",[a,b])):
            s,fields=observe.evolve(tank,fluid.initial_rings(tank,initial),.75,dt,pair=group=="AB")
            if group=="AB":
                np.savez_compressed(out/f"pair_slice_{n}.npz",**fields)
            by_group[group]=s
        final=[by_group[g]["rows"][-1] for g in ("A","B","AB")]
        resolved=final[2]["resolved_pair_z_r_rms"]
        r={"n":n,"dt":dt,"gap":gap,"strength_B":strength,"core_B":core,"viscosity":viscosity,
           "groups":by_group,"relative_shift_from_singles":None}
        if resolved:
            initial_pair=by_group["AB"]["rows"][0]["resolved_pair_z_r_rms"]
            if initial_pair:
                r["relative_shift_from_singles"]=[(resolved[i][0]-initial_pair[i][0])-
                    (final[i]["core_z_r_rms"][0]-by_group[g]["rows"][0]["core_z_r_rms"][0])
                    for i,g in enumerate(("A","B"))]
        flux=[]
        for j,time in enumerate(by_group["AB"]["rows"]):
            flux.append(time["midplane_energy_flux"]-sum(by_group[g]["rows"][j]["midplane_energy_flux"] for g in ("A","B")))
        r["integrated_midplane_flux_excess"]=float(np.trapezoid(flux,dx=.125))
        results.append(r)
    checks={"balance":all(s["max_div"]<1e-8 and s["max_abs_net_flux"]<1e-9 and s["max_energy_residual_rel"]<.02
                          for r in results for s in r["groups"].values())}
    save_summary(out,{"case":case,"runs":results,"checks":checks},__file__,fluid.__file__,observe.__file__,topology.__file__)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case",choices=["phases",*PAIRS])
    p.add_argument("--out",type=Path,default=OUT)
    args=p.parse_args()
    for c in ([args.case] if args.case else ["phases",*PAIRS]):
        if c=="phases":
            phases(args.out/c)
        else:
            rings(args.out/c,c)
