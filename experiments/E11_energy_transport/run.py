"""Audit local mechanical and electromagnetic energy density and flux."""
import argparse
from pathlib import Path

import numpy as np
from scipy.constants import c, epsilon_0

from experiments.common import save_summary
from experiments.E03_vortex import fluid, topology
from experiments.E06_jet import run as jet

OUT = Path(__file__).resolve().parents[2] / "research/results/E11"
THRESHOLDS = (.25, .35, .50)
LIGHT_LENGTH_M = 1.e-3
LIGHT_FIELD_V_M = 1.
ENERGY_UNIT = epsilon_0 * LIGHT_FIELD_V_M**2 * LIGHT_LENGTH_M**3
FLUX_UNIT = epsilon_0 * c * LIGHT_FIELD_V_M**2 * LIGHT_LENGTH_M**2


def regions(tag, energy, axes):
    """Find threshold topology and overlap independently for tag and energy."""
    radius = []
    for values in (tag, energy):
        if float(values.max()) < 1.e-10:
            radius.append(None)
            continue
        i, j, k = np.unravel_index(values.argmax(), values.shape)
        radius.append([float(np.hypot(axes[0][i], axes[1][j])), float(axes[2][k])])
    reports = {}
    for threshold in THRESHOLDS:
        masks = [values >= threshold*values.max() if values.max()>1.e-10
                 else np.zeros(values.shape, dtype=bool) for values in (tag, energy)]
        intersection = np.count_nonzero(masks[0] & masks[1])
        union = np.count_nonzero(masks[0] | masks[1])
        total = float(np.sum(energy))
        reports[str(threshold)] = {
            "tag": topology.component_topology(tag, threshold),
            "energy": topology.component_topology(energy, threshold),
            "jaccard_all_above_threshold": float(intersection/union) if union else None,
            "total_energy_fraction_in_tag_mask": float(energy[masks[0]].sum()/total) if total else None,
        }
    return {"peak_tag_r_z": radius[0], "peak_energy_r_z": radius[1], "thresholds": reports}


def kinetic(velocity):
    return np.sum(velocity**2, axis=0) / 2


def fluid_flux(tank, staggered, p, bounds):
    velocities = tank.centers(staggered)
    energy = kinetic(velocities)
    face_rates = []
    net_mass_flux = 0.
    for direction, (lo, hi) in enumerate(bounds):
        cross_section = [slice(start,end) for start,end in bounds]
        speed = staggered[direction]
        for face, sign in ((lo,-1), (hi,1)):
            cross_section[direction] = face
            u_normal = speed[tuple(cross_section)]
            cross_section[direction] = face-1
            e_left = energy[tuple(cross_section)]
            p_left = p[tuple(cross_section)]
            cross_section[direction] = face
            e_right = energy[tuple(cross_section)]
            p_right = p[tuple(cross_section)]
            face_energy = (e_left+e_right)/2
            face_pressure = (p_left+p_right)/2
            convection = sign * np.sum(face_energy*u_normal)*tank.h**2
            pressure = sign * np.sum(face_pressure*u_normal)*tank.h**2
            viscous = -sign * tank.nu * np.sum(e_right-e_left)*tank.h
            net_mass_flux += float(sign*u_normal.sum()*tank.h**2)
            face_rates.append([float(convection), float(pressure), float(viscous)])
    # Interior-only central differences. All six faces are away from the tank walls.
    volume = tuple(slice(lo,hi) for lo,hi in bounds)
    dissipation = 0.
    for direction, (lo,hi) in enumerate(bounds):
        low = list(volume)
        high = list(volume)
        low[direction] = slice(lo-1,hi-1)
        high[direction] = slice(lo+1,hi+1)
        gradient = (velocities[(slice(None), *high)]-velocities[(slice(None), *low)])/(2*tank.h)
        dissipation += float(np.sum(gradient**2)*tank.nu*tank.h**3)
    return np.array(face_rates), dissipation, net_mass_flux


def fluid_experiment(n, dt):
    tank = fluid.Tank(n, viscosity=.05, inlet=True)
    bounds = ((n//4,3*n//4), (n//4,3*n//4), (n//8,3*n//8))
    volume = tuple(slice(lo,hi) for lo,hi in bounds)
    inlet = jet.profile(tank, "circle", 1.)

    def port(time):
        return inlet*np.sin(np.pi*time)**2 if time<1. else tank.zero_plane

    velocity = tank.zeros()
    cumulative_flux, cumulative_diss, absolute_work = np.zeros((6,3)), 0., np.zeros(4)
    local_scale, local_residual, tank_residual, maximum_mass = 1.e-20, 0., 0., 0.
    snapshots = []
    traces = np.zeros((round(1.75/dt)+1,6))
    for step in range(1, len(traces)):
        velocity, pressure, mid, work = tank.step(velocity, dt, port((step-.5)*dt), port(step*dt))
        rates, loss, mass_flux = fluid_flux(tank, mid, pressure, bounds)
        cumulative_flux += rates*dt
        cumulative_diss += loss*dt
        absolute_work += work
        collocated = tank.centers(velocity)
        energy = kinetic(collocated)
        local_energy = float(energy[volume].sum()*tank.h**3)
        tank_energy = tank.inner(velocity, velocity)/2
        residual = local_energy + cumulative_flux.sum() + cumulative_diss
        local_scale = max(local_scale, local_energy, abs(cumulative_flux.sum()), cumulative_diss)
        local_residual = max(local_residual, float(abs(residual)))
        tank_residual = max(tank_residual, abs(tank_energy-absolute_work.sum()))
        maximum_mass = max(maximum_mass, abs(mass_flux))
        traces[step] = [step*dt, local_energy, cumulative_flux.sum(), cumulative_diss, residual, tank_energy]
        if step % round(.125/dt)==0:
            vort = np.linalg.norm(tank.curl(collocated), axis=0)
            snapshots.append({"t_s": step*dt, **regions(vort, energy, tank.axes)})
    # Same treatment on the known no-flow and through-flow control in the interior.
    control = tank.zeros()
    rest_flux, rest_diss, _ = fluid_flux(tank, control, np.zeros((n,n,n)), bounds)
    control[2].fill(1.)
    through_flux, through_diss, _ = fluid_flux(tank, control, np.zeros((n,n,n)), bounds)
    midplane = tank.n//2
    images = {"axis_horizontal_m": tank.axes[0], "axis_vertical_m": tank.axes[2],
              "energy_j_m3": energy[:,midplane,:], "vorticity_s_inv": vort[:,midplane,:],
              "budget": traces}
    return {"n": n, "dt_s": dt, "density_kg_m3": 1., "kinematic_viscosity_m2_s": tank.nu,
            "control_volume_m": [[-1.5,1.5],[-1.5,1.5],[.75,2.25]],
            "control_faces": ["x-", "x+", "y-", "y+", "z-", "z+"],
            "flux_terms": ["advective", "pressure", "viscous"],
            "flux_out_j_by_face_and_term": cumulative_flux.tolist(),
            "energy_final_j": local_energy, "loss_j": cumulative_diss,
            "maximum_local_flux_of_mass_m3_s": maximum_mass,
            "relative_local_residual": local_residual/local_scale,
            "relative_whole_box_residual": tank_residual/max(traces[:,5]),
            "rest_test": {"net_flux_w": float(rest_flux.sum()), "dissipation_w": rest_diss},
            "through_flow_test": {"net_flux_w": float(through_flux.sum()), "dissipation_w": through_diss,
                                  "axial_faces_w": through_flux[-2:,0].tolist()},
            "snapshots": snapshots}, images


def maxwell(radius, z, t, q2, component):
    """TE Hertz-potential solution, with normalized c=epsilon=mu=1."""
    a = 1. + 1j*(z-t)
    b = q2 - 1j*(z+t)
    denominator = radius**2 + a*b
    e_phi = 4*radius*(-1j*(a+b))/denominator**3
    b_r = 4*radius*(1j*(b-a))/denominator**3
    b_z = 4/denominator**2 - 8*radius**2/denominator**3
    return tuple(getattr(value, component) for value in (e_phi,b_r,b_z))


def maxwell_residual(q2, part, delta):
    radius = np.linspace(.2,2.8,14)[:,None]
    z = np.linspace(-1.5,1.5,13)[None,:]
    t = .35
    ns = maxwell(radius,z,t,q2,part)
    differences = []
    for axis in range(3):
        plus_args, minus_args = [radius,z,t], [radius,z,t]
        plus_args[axis] = plus_args[axis]+delta
        minus_args[axis] = minus_args[axis]-delta
        plus = maxwell(*plus_args,q2,part)
        minus = maxwell(*minus_args,q2,part)
        differences.append([(p-m)/(2*delta) for p,m in zip(plus,minus)])
    (er,brr,bzr), (ez,brz,bzz), (et,brt,bzt) = differences
    errors = [brr+ns[1]/radius+bzz, et-(brz-bzr), brt-ez, bzt+(er+ns[0]/radius)]
    scale = max(float(abs(value).max()) for value in ns)
    return float(max(abs(value).max() for value in errors) / scale)


def optical_budget(q2, part, cells):
    # Fixed cylinder in normalized coordinates, integrated with midpoints on faces.
    dr, dz = 3/cells, 4/cells
    radius = (np.arange(cells)+.5)*dr
    z = -2+(np.arange(cells)+.5)*dz
    times = np.linspace(-.5,.5,cells+1)
    energy, flux = [], []
    for t in times:
        ef, br, bz = maxwell(radius[:,None],z,t,q2,part)
        energy.append(float(np.sum((ef**2+br**2+bz**2)*radius[:,None])*np.pi*dr*dz))
        es, _, bs = maxwell(3.,z,t,q2,part)
        side = 2*np.pi*3*np.sum(es*bs)*dz
        ed, bd, _ = maxwell(radius,-2.,t,q2,part)
        bottom = 2*np.pi*np.sum(ed*bd*radius)*dr
        et, bt, _ = maxwell(radius,2.,t,q2,part)
        top = -2*np.pi*np.sum(et*bt*radius)*dr
        flux.append([float(side),float(bottom),float(top)])
    energy, flux = np.array(energy), np.array(flux)
    work = np.diff(times)[:,None]*(flux[1:]+flux[:-1])/2
    integrated_flux = np.vstack((np.zeros(3), np.cumsum(work,axis=0)))
    residual = energy-energy[0]+integrated_flux.sum(axis=1)
    return {"cells": cells, "faces": ["side", "z-", "z+"],
            "energy_begin": float(energy[0]), "energy_end": float(energy[-1]),
            "integrated_outward_flux": integrated_flux[-1].tolist(),
            "relative_energy_residual": float(abs(residual).max()/energy.max()),
            "time_unit_s": LIGHT_LENGTH_M/c, "energy_unit_j": ENERGY_UNIT, "power_unit_w": FLUX_UNIT}


def wave_controls():
    z = np.linspace(-np.pi,np.pi,32)
    times = np.linspace(0.,2*np.pi,257)[:,None]
    positive = np.cos(z-times)
    negative = np.cos(z+times)
    e, b = positive+negative, negative-positive
    propagation = .5*(positive**2+(-positive)**2)
    energy_flux = -positive*(-positive)
    return {"traveling_flux_to_density_error": float(abs(propagation-energy_flux).max()),
            "standing_max_absolute_mean_flux": float(abs(np.trapezoid(-e*b,x=times[:,0],axis=0)).max()/(2*np.pi))}


def optical_experiment(q2, part):
    reports, visual = [], {}
    for n in (48,96):
        axis = -6.+(np.arange(n)+.5)*12/n
        x,y,z = np.meshgrid(axis,axis,axis,indexing="ij",sparse=True)
        for t in (-.5,0.,.5):
            electric, br, bz = maxwell(np.hypot(x,y),z,t,q2,part)
            energy = .5*(electric**2+br**2+bz**2)
            reports.append({"n": n, "time": t, **regions(abs(electric),energy,[axis]*3)})
            if n==96 and t==0.:
                plane = n//2
                visual = {"x": axis, "z": axis, "electric": electric[:,plane,:],
                          "energy": energy[:,plane,:],
                          "flux_r": (electric*bz)[:,plane,:], "flux_z": (-electric*br)[:,plane,:]}
    return {"q2": q2, "component": part, "snapshots": reports,
            "budget": [optical_budget(q2,part,n) for n in (64,128)],
            "max_normalized_field_equation_residual": maxwell_residual(q2,part,.0005)}, visual


def run(out, domain):
    out.mkdir(parents=True, exist_ok=True)
    if domain == "fluid":
        trials = []
        for n in (48,64):
            result, arrays = fluid_experiment(n, .0078125)
            np.savez_compressed(out/f"field_{n}.npz", **arrays)
            trials.append(result)
        checks = {
            "control_volume_energy": all(r["relative_local_residual"]<.05 for r in trials),
            "whole_tank_energy": all(r["relative_whole_box_residual"]<.02 for r in trials),
            "no_net_mass_accumulation": all(r["maximum_local_flux_of_mass_m3_s"]<1.e-8 for r in trials),
            "known_flux_controls": all(r["rest_test"]=={"net_flux_w":0.,"dissipation_w":0.}
                      and r["through_flow_test"]["net_flux_w"]==0.
                      and r["through_flow_test"]["axial_faces_w"]==[-4.5,4.5] for r in trials),
        }
        sources = [fluid.__file__, jet.__file__]
        summary = {"trials": trials}
    else:
        trials, control = [], wave_controls()
        for q2 in (5,20):
            for part in ("real","imag"):
                result, arrays = optical_experiment(q2,part)
                np.savez_compressed(out/f"field_q{q2}_{part}.npz", **arrays)
                trials.append(result)
        checks = {
            "maxwell_field_equations": all(r["max_normalized_field_equation_residual"]<1.e-4 for r in trials),
            "poynting_cylinder_energy": all(b["relative_energy_residual"]<.02
                                          for r in trials for b in r["budget"]),
            "plane_wave_controls": max(control.values())<1.e-10,
        }
        sources = []
        summary = {"trials": trials, "wave_controls": control}
    save_summary(out, {**summary,"checks":checks}, __file__, topology.__file__, *sources)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", required=True, choices=["fluid","light"])
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    run(args.out/args.domain, args.domain)
