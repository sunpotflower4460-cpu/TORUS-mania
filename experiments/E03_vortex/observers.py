"""Measure a fixed-flux neck and compare matched, solenoidal random initial fields."""
import argparse
from pathlib import Path

import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.ndimage import gaussian_filter

from experiments.common import save_summary
from . import fluid, observe, topology


def flux_profile(axial, center):
    radius = np.linspace(0, 1.5, 161)
    angles = np.arange(64)*2*np.pi/64
    x = radius[:,None]*np.cos(angles)
    y = radius[:,None]*np.sin(angles)
    offsets = np.arange(-6,7)*.125
    widths = []
    for offset in offsets:
        z = np.full_like(x, center+offset)
        w = axial(x, y, z)
        flux = 2*np.pi*cumulative_trapezoid(radius*w.mean(axis=1), radius, initial=0.)
        hits = np.flatnonzero(flux >= .10)
        if not len(hits) or np.min(w[:hits[0]+1]) <= 0:
            widths.append(None)
            continue
        idx = hits[0]
        widths.append(float(np.interp(.10,flux[idx-1:idx+1],radius[idx-1:idx+1])))
    result = {"offset_m": offsets.tolist(), "radius_m": widths, "ratio": None, "neck": None}
    if None not in widths:
        ratio = widths[6]/min(widths[0],widths[-1])
        result.update(ratio=ratio, neck=bool(ratio<=.92 and abs(offsets[np.argmin(widths)])<=.125))
    return result


def random_field(tank, seed, target_energy):
    rng = np.random.default_rng(seed)
    u = tank.zeros()
    for _ in range(12):
        modes = rng.integers(1,5,size=3)
        amplitude = rng.normal(size=3)
        amplitude -= modes * (amplitude @ modes) / (modes @ modes)
        for i in range(3):
            value = amplitude[i]
            for j, coord in enumerate(tank.coords(i)):
                angle = np.pi*modes[j]*(coord-tank.origin[j])/tank.length
                value = value*(np.sin(angle) if i==j else np.cos(angle))
            u[i] += value
    tank.project(u)
    scale = np.sqrt(2*target_energy / tank.inner(u,u))
    return [v*scale for v in u]


def threshold_tests(tank, u):
    magnitude = np.linalg.norm(tank.curl(tank.centers(u)),axis=0)
    results = {}
    for sigma in (0., .10):
        filtered = gaussian_filter(magnitude,sigma/tank.h,mode="reflect") if sigma else magnitude
        results[str(sigma)] = {str(f): topology.component_topology(filtered,f) for f in (.25,.35,.50)}
    return results


def run(out):
    profiles = {"uniform": flux_profile(lambda x,y,z: np.ones_like(x),3.),
                "potential": flux_profile(lambda x,y,z: 1.5+.8*((x*x+y*y)/2-(z-3)**2),3.)}
    rows = []
    for n in (32,48):
        tank = fluid.Tank(n)
        u = fluid.initial_rings(tank,[(3.,4.,.4)])
        e = tank.inner(u,u)/2
        field = {"n": n, "initial_ring": threshold_tests(tank,u), "random": []}
        for seed in (11,29,47):
            rnd = random_field(tank,seed,e)
            field["random"].append({"seed": seed, "energy_match_relative": abs(tank.inner(rnd,rnd)/(2*e)-1),
                                    "max_div": float(abs(tank.divergence(rnd)).max()),
                                    "topology": threshold_tests(tank,rnd)})
        for step in range(97):
            if step in (0,96):
                obs, _ = observe.field_metrics(tank,u,np.zeros((n,n,n)),False)
                w = tank.centers(u)[2:3]
                def axial(x,y,z):
                    pts = np.column_stack([q.ravel() for q in (x,y,z)])
                    return tank.sample(w,pts)[:,0].reshape(x.shape)
                profiles[f"ring_{n}_{step}"] = flux_profile(axial,obs["core_z_r_rms"][0])
            if step < 96:
                u, _, _, _ = tank.step(u,1/128)
        rows.append(field)
    checks = {"potential_neck": profiles["potential"]["neck"], "uniform_no_neck": not profiles["uniform"]["neck"],
              "balanced_random_fields": all(r["energy_match_relative"]<1e-10 and r["max_div"]<1e-8
                                            for f in rows for r in f["random"])}
    out.mkdir(parents=True,exist_ok=True)
    save_summary(out, {"profiles": profiles, "topology_trials": rows, "checks": checks}, __file__,
                 fluid.__file__, observe.__file__, topology.__file__)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[2]/"research/results/E03/observers")
    run(p.parse_args().out)
