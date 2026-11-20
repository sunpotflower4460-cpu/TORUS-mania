"""Finite-duration matched-flux jets in a 3-D tank initially at rest."""
import argparse
from pathlib import Path
import numpy as np
from experiments.common import save_summary
from experiments.E03_vortex import fluid, observe, topology

OUT=Path(__file__).resolve().parents[2]/"research/results/E06"
CASES={"off":("circle",0.,1.),"weak":("circle",.25,1.),"circle":("circle",1.,1.),
       "ellipse":("ellipse",1.,1.),"slit":("slit",1.,1.),"long":("circle",1.,2.),
       "periodic_sides":("circle",1.,1.),"larger":("circle",1.,1.)}


def profile(tank,shape,bulk):
    x,y,_=tank.coords(2)
    x,y=x[:,:,0],y[:,:,0]
    if shape=="slit":
        # Rectangle with full-width ratio 4:1 and area pi, smooth profile vanishes at all edges.
        half_long=np.sqrt(np.pi)
        half_short=half_long/4
        raw=(np.maximum(1-(x/half_long)**2,0)*np.maximum(1-(y/half_short)**2,0))**2
    else:
        a=np.sqrt(2.) if shape=="ellipse" else 1.
        raw=np.maximum(1-(x/a)**2-(y*a)**2,0)**2
    return raw * ((np.pi*bulk)/(raw.sum()*tank.h**2))


def run(out,case):
    out.mkdir(exist_ok=True,parents=True)
    shape,bulk,duration=CASES[case]
    resolutions=[(32,1/64),(48,1/128)]
    if case=="circle":
        resolutions.insert(1,(32,1/128))
    if case=="larger":
        resolutions=[(64,1/128)]
    runs=[]
    for n,dt in resolutions:
        tank=fluid.Tank(n, length=8. if case=="larger" else 6., periodic=(0,1) if case=="periodic_sides" else (), inlet=True)
        inlet=profile(tank,shape,bulk)
        def port(t):
            return inlet*(np.sin(np.pi*t/duration)**2 if t<duration else 0.)
        row,arrays=observe.evolve(tank,tank.zeros(),duration+.75,dt,port=port)
        row.update(shape=shape, bulk_peak_m_s=bulk, port_peak_m_s=float(inlet.max()), pulse_s=duration,
                   integrated_volume_m3=float(sum(port((j+.5)*dt).sum()*tank.h**2*dt for j in range(round(duration/dt)))),
                   nominal_stroke_over_equiv_diameter=bulk*duration/4)
        for f in (".25",".35",".50"):
            key=str(float(f))
            times=[r["time"] for r in row["rows"] if r["topology"][key]["candidate"]]
            row.setdefault("detected_times",{})[key]=times
        np.savez_compressed(out/f"slice_{n}_{round(1/dt)}.npz",**arrays)
        runs.append(row)
    checks={"initially_quiescent":all(r["initial_energy"]==0 for r in runs),
            "matched_volume":all(abs(r["integrated_volume_m3"]-np.pi*bulk*duration/2)<1e-8 for r in runs),
            "incompressible":all(r["max_div"]<1e-8 and r["max_abs_net_flux"]<1e-9 for r in runs),
            "energy_budget":all(r["max_energy_residual_rel"]<.02 for r in runs)}
    if case=="off":
        checks["no_forcing_control"]=all(all(x["omega_peak"]["value"]==0 and not x["topology"]["0.35"]["candidate"] for x in r["rows"]) for r in runs)
    save_summary(out,{"case":case,"runs":runs,"checks":checks},__file__,fluid.__file__,observe.__file__,topology.__file__)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,default=OUT)
    p.add_argument("--case",choices=CASES)
    args=p.parse_args()
    for name in ([args.case] if args.case else CASES):
        run(args.out/name,name)
