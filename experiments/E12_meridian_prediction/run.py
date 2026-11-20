"""Predict three-dimensional level sets from a single meridian."""
import argparse
from pathlib import Path

import numpy as np
from scipy import ndimage

from experiments.common import save_summary
from experiments.E03_vortex import fluid, topology
from experiments.E06_jet import run as jet
from experiments.E11_energy_transport import run as energy_transport

OUT = Path(__file__).resolve().parents[2]/"research/results/E12"
THRESHOLDS = (.50,.35)


def meridian_prediction(values, fraction):
    """A compact, hole-free cross-section away from the axis sweeps out a solid torus."""
    n = values.shape[0]
    section = values[n//2:,n//2,:]
    peak = float(section.max())
    if peak < 1.e-10:
        return {"candidate": False, "touches_axis": False, "touches_outer_boundary": False,
                "has_hole": False, "section_cells": 0, "section_peak": peak}
    labels, _ = ndimage.label(section>=fraction*peak,structure=np.ones((3,3),dtype=bool))
    counts = np.bincount(labels.ravel())
    largest = labels==(1+np.argmax(counts[1:]))
    axis = bool(largest[0].any())
    boundary = bool(largest[-1].any() or largest[:,0].any() or largest[:,-1].any())
    hole = bool((ndimage.binary_fill_holes(largest) & ~largest).any())
    return {"candidate": not (axis or boundary or hole),
            "touches_axis": axis, "touches_outer_boundary": boundary,
            "has_hole": hole, "section_cells": int(largest.sum()), "section_peak": peak}


def compare(fields, metadata):
    rows = []
    for name, values in fields.items():
        for fraction in THRESHOLDS:
            prediction = meridian_prediction(values,fraction)
            observed = topology.component_topology(values,fraction)
            rows.append({**metadata,"variable": name,"threshold": fraction,
                         "predicted": prediction, "three_d": observed,
                         "three_d_peak": float(values.max()),
                         "match": prediction["candidate"]==observed["candidate"]})
    return rows


def optical_cases():
    n = 96
    axis = -6. + (np.arange(n)+.5)*(12./n)
    x,y,z = np.meshgrid(axis,axis,axis,indexing="ij",sparse=True)
    radius = np.hypot(x,y)
    rows = []
    for q2 in (3,8,12):
        for phase in ("real","imag"):
            for t in (.25,.75):
                electric, b_r, b_z = energy_transport.maxwell(radius,z,t,q2,phase)
                rows.extend(compare({"electric_azimuthal": abs(electric),
                     "electromagnetic_energy": .5*(electric**2+b_r**2+b_z**2)},
                    {"q2": q2,"phase": phase,"time": t,"n": n}))
    return rows


def jet_cases(case):
    shape,speed,duration = jet.CASES[case]
    rows, balances = [], []
    for n in (48,64):
        tank = fluid.Tank(n,inlet=True)
        inlet = jet.profile(tank,shape,speed)

        def port(t):
            return inlet*np.sin(np.pi*t/duration)**2 if t<duration else tank.zero_plane

        dt = 1/128
        velocity = tank.zeros()
        accumulated_work = 0.
        maximum_residual = 0.
        maximum_energy = 0.
        maximum_divergence = 0.
        sample_steps = [round((duration+lag)/dt) for lag in (.25,.75)]
        for step in range(1,sample_steps[-1]+1):
            velocity,_,_,work = tank.step(velocity,dt,port((step-.5)*dt),port(step*dt))
            accumulated_work += work.sum()
            total_energy = tank.inner(velocity,velocity)/2
            maximum_energy = max(maximum_energy,total_energy)
            maximum_residual = max(maximum_residual,abs(total_energy-accumulated_work))
            if step in sample_steps:
                maximum_divergence = max(maximum_divergence,float(abs(tank.divergence(velocity)).max()))
                centers = tank.centers(velocity)
                curl = tank.curl(centers)
                x,y,_ = tank.coords()
                angular = (x*curl[1]-y*curl[0])/np.hypot(x,y)
                rows.extend(compare({"vorticity_azimuthal": abs(angular),
                             "kinetic_energy": energy_transport.kinetic(centers)},
                            {"case": case,"time_s": step*dt,"n": n}))
        balances.append({"n": n,"max_sample_divergence_s_inv": maximum_divergence,
                         "energy_relative_residual": maximum_residual/maximum_energy})
    return rows, balances


def performance(rows):
    result = []
    for fraction in THRESHOLDS:
        scored = [r for r in rows if r["threshold"]==fraction]
        matched = sum(r["match"] for r in scored)
        positive = sum(r["three_d"]["candidate"] for r in scored)
        result.append({"threshold": fraction,"observations": len(scored),"matched": matched,
                       "positives": positive,"negatives": len(scored)-positive,
                       "correct_fraction": matched/len(scored)})
    return result


def run(out, group):
    out.mkdir(parents=True,exist_ok=True)
    balances = []
    if group=="light":
        rows = optical_cases()
    elif group=="circle":
        rows = []
        for case in ("weak","long"):
            case_rows, case_balances = jet_cases(case)
            rows.extend(case_rows)
            balances.extend({"case": case,**item} for item in case_balances)
    else:
        rows,balances = jet_cases("slit")
    metric = performance(rows)
    primary = metric[0]
    verdict = primary["correct_fraction"]>=.9 and min(primary["positives"],primary["negatives"])>0
    checks = {"registered_counts": primary["observations"]=={"light":24,"circle":16,"slit":8}[group]}
    if balances:
        checks["jet_balance"] = all(m["max_sample_divergence_s_inv"]<1.e-8
                                    and m["energy_relative_residual"]<.02 for m in balances)
    save_summary(out,{"group": group,"trials": rows,"performance": metric,
                      "passes_registered_accuracy_if_axisymmetric": verdict if group!="slit" else None,
                      "balances": balances,"checks": checks},
                 __file__,energy_transport.__file__,topology.__file__,fluid.__file__,jet.__file__)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group",required=True,choices=["light","circle","slit"])
    parser.add_argument("--out",type=Path,default=OUT)
    args = parser.parse_args()
    run(args.out/args.group,args.group)
