"""Carry vorticity and a passive magnetic field with independently integrated states."""
import argparse
from pathlib import Path

import numpy as np
from scipy import fft
from scipy.integrate import cumulative_trapezoid
from scipy.ndimage import map_coordinates

from experiments.common import save_summary
from experiments.E03_vortex import topology

OUT = Path(__file__).resolve().parents[2] / "research/results/E13"
LENGTH = 8.
RADIUS = 1.4
WIDTH = .48
MAGNETIC_SCALE_S = .05
DURATION = .8
THRESHOLDS = (.25, .35, .5)


def cross(a, b):
    return np.cross(a, b, axisa=-4, axisb=-4, axisc=-4)


class PeriodicGrid:
    def __init__(self, n):
        self.n = n
        self.h = LENGTH/n
        self.axis = -LENGTH/2 + self.h*np.arange(n)
        modes = (fft.fftfreq(n)*n, fft.fftfreq(n)*n, fft.rfftfreq(n)*n)
        ijk = np.array(np.meshgrid(*modes, indexing="ij"))
        self.k = ijk*(2*np.pi/LENGTH)
        self.k2 = np.sum(self.k**2, axis=0)
        self.inv_k2 = np.divide(1.,self.k2,out=np.zeros_like(self.k2),where=self.k2>0)
        self.retained = (np.abs(ijk)<n/3-.01).all(axis=0)
        self.weights = np.ones(n//2+1)
        self.weights[1:-1] = 2.
        self.normalization = LENGTH**3/n**6

    def spectrum(self, field):
        return self.retained*fft.rfftn(field, axes=(-3,-2,-1), workers=1)

    def physical(self, field):
        return fft.irfftn(field, s=(self.n,)*3, axes=(-3,-2,-1), workers=1)

    def curl(self, field):
        return 1j*cross(self.k,field)

    def project(self, field):
        parallel = np.sum(self.k*field,axis=-4,keepdims=True)
        return field-self.k*parallel*self.inv_k2

    def norm2(self, field, weight=1.):
        return self.normalization*np.sum(weight*self.weights*abs(field)**2,axis=(-4,-3,-2,-1))

    def sample(self, fields, points):
        indices = (np.asarray(points).T + LENGTH/2)/self.h
        return np.array([map_coordinates(field,indices,order=3,mode="grid-wrap")
                         for field in fields]).T

    def ring(self, z_offset=0.):
        x,y,z = np.meshgrid(self.axis,self.axis,self.axis,indexing="ij",sparse=True)
        envelope = 4./RADIUS*np.exp(-((x*x+y*y-RADIUS**2)/(2*RADIUS*WIDTH))**2
                                    -((z-z_offset)/WIDTH)**2)
        real = np.array([-y*envelope, x*envelope, np.zeros_like(envelope)])
        return self.project(self.spectrum(real))


def rhs(grid, state, diffusivities):
    real = grid.physical(np.concatenate((state,grid.curl(state[:1])),axis=0))
    velocity, vorticity = real[0], real[-1]
    nonlinear = grid.spectrum(cross(velocity,np.concatenate((vorticity[None],real[1:-1]))))
    rates = np.concatenate((grid.project(nonlinear[:1]), grid.curl(nonlinear[1:])))
    rates -= diffusivities[:,None,None,None,None]*grid.k2*state
    return rates, velocity


def advance(grid, state, diffusivities, dt, points=None):
    k1, u1 = rhs(grid,state,diffusivities)
    k2, u2 = rhs(grid,state+dt*k1/2,diffusivities)
    k3, u3 = rhs(grid,state+dt*k2/2,diffusivities)
    k4, u4 = rhs(grid,state+dt*k3,diffusivities)
    next_state = state+dt/6*(k1+2*k2+2*k3+k4)
    if points is None:
        return next_state, None
    shape = points.shape
    p = points.reshape(-1,3)
    a = grid.sample(u1,p)
    b = grid.sample(u2,p+dt*a/2)
    c = grid.sample(u3,p+dt*b/2)
    d = grid.sample(u4,p+dt*c)
    return next_state, (p+dt/6*(a+2*b+2*c+d)).reshape(shape)


def sections(size):
    offsets = np.linspace(-.45,.45,size+1)
    sections = []
    for angle in np.arange(4)*np.pi/2:
        er = np.array([np.cos(angle),np.sin(angle),0.])
        center = (RADIUS+offsets[None,:,None])*er[None,None,:]
        sections.append(center+offsets[:,None,None]*np.array([0.,0.,1.]))
    return np.stack(sections)


def flux_measure(grid, physical_fields, physical_curls, points, diffusivities):
    fluxes, resistive_rates = [], []
    for surface in points:
        a,b,c,d = surface[:-1,:-1],surface[1:,:-1],surface[:-1,1:],surface[1:,1:]
        areas = np.concatenate((np.cross(b-a,c-a).reshape(-1,3),
                                np.cross(d-b,c-b).reshape(-1,3)))/2
        midpoints = np.concatenate(((a+b+c).reshape(-1,3), (b+c+d).reshape(-1,3)))/3
        loop = np.concatenate((surface[:-1,0],surface[-1,:-1],
                               surface[:0:-1,-1],surface[0,:0:-1]))
        next_point = np.roll(loop,-1,axis=0)
        edges = next_point-loop
        edge_centers = (next_point+loop)/2
        fluxes.append([np.sum(grid.sample(field,midpoints)*areas) for field in physical_fields])
        resistive_rates.append([-coefficient*np.sum(grid.sample(curl,edge_centers)*edges)
                                for coefficient,curl in zip(diffusivities,physical_curls,strict=True)])
    return np.asarray(fluxes), np.asarray(resistive_rates)


def ring_stats(grid, state, names, diffusivities, points, inspect_shape):
    vorticity = grid.curl(state[:1])
    fields = np.concatenate((vorticity,state[1:]))
    physical = grid.physical(fields)
    curls = grid.physical(grid.curl(fields))
    velocity = grid.physical(state[0])
    flux, rate = flux_measure(grid,physical,curls,points,diffusivities)
    energy = .5*grid.norm2(state)
    dissipation = diffusivities*grid.norm2(state,grid.k2)
    magnetic_work = np.sum(cross(velocity,physical[1:])*curls[1:],axis=(-4,-3,-2,-1))*grid.h**3
    work = np.r_[0.,magnetic_work]
    union = None
    if inspect_shape:
        magnitudes = np.linalg.norm(physical,axis=1)
        union = {name:{str(f):topology.component_topology(mag,f) for f in THRESHOLDS}
                 for name,mag in zip(names,magnitudes,strict=True)}
        union["kinetic_energy_density"] = {str(f):topology.component_topology(np.sum(velocity**2,axis=0),f)
                                            for f in THRESHOLDS}
    return flux,rate,energy,dissipation,work,union


def relative_difference(grid, reference, field):
    return float(np.sqrt(grid.norm2(reference-field)/grid.norm2(reference)))


def run_ring(grid, dt, viscosity, section_size):
    initial_omega = grid.ring()
    velocity = grid.curl(initial_omega)*grid.inv_k2
    if viscosity==0.:
        names = ["vorticity", "matched_ideal"]
        diffusivities = np.array([0.,0.])
        state = np.stack((velocity,MAGNETIC_SCALE_S*initial_omega))
    else:
        names = ["vorticity", "magnetic_ideal", "matched", "faster_diffusion", "shifted", "zero"]
        diffusivities = np.array([viscosity,0.,viscosity,.18,viscosity,viscosity])
        matched = MAGNETIC_SCALE_S*initial_omega
        state = np.stack((velocity,matched,matched,matched,
                          MAGNETIC_SCALE_S*grid.ring(.7),np.zeros_like(matched)))
    points = sections(section_size)
    records, shapes, difference = [],[],[]
    sample_stride = round(.02/dt)
    shape_stride = round(.1/dt)
    num_steps = round(DURATION/dt)
    for step in range(num_steps+1):
        if step%sample_stride==0:
            record = ring_stats(grid,state,names,diffusivities,points,step%shape_stride==0)
            records.append(record[:5])
            if record[-1] is not None:
                shapes.append({"t_s":step*dt,"superlevel":record[-1]})
            ref = MAGNETIC_SCALE_S*grid.curl(state[0])
            index = names.index("matched") if viscosity else 1
            difference.append(relative_difference(grid,ref,state[index]))
        if step<num_steps:
            state, points = advance(grid,state,diffusivities,dt,points)
    times = np.arange(len(records))*.02
    flux,rates,energies,dissipation,work = [np.array(values) for values in zip(*records)]
    integrated_flux = cumulative_trapezoid(rates,times,axis=0,initial=0.)
    flux_error = (flux-flux[0]-integrated_flux)/np.maximum(abs(flux[0]),1.e-12)
    integrated_work = cumulative_trapezoid(work-dissipation,times,axis=0,initial=0.)
    energy_error = (energies-energies[0]-integrated_work)/np.maximum(energies[0],1.e-15)
    div = np.max(abs(np.sum(grid.k*state,axis=1)))/max(abs(state).max(),1.e-20)
    ratios = np.divide(flux[-1],flux[0],out=np.zeros_like(flux[-1]),where=abs(flux[0])>1.e-12)
    e0 = np.where(energies[0] != 0, energies[0], 1.)
    data = {
        "n": grid.n, "dt_s": dt, "section_intervals": section_size, "names": names,
        "coefficients_m2_s": diffusivities.tolist(),
        "flux_units": ["m2/s",*["m3/s"]*(len(names)-1)],
        "energy_units": "J at reference density 1 kg/m3",
        "max_divergence_spectral_relative": float(div),
        "matching_field_max_relative_l2": float(max(difference)),
        "largest_relative_flux_balance_error": dict(zip(names,np.max(abs(flux_error),axis=(0,1)).tolist())),
        "largest_relative_energy_balance_error": dict(zip(names,np.max(abs(energy_error),axis=0).tolist())),
        "relative_final_flux": {name:ratios[:,i].tolist() for i,name in enumerate(names) if name!="zero"},
        "initial_energy_j": dict(zip(names, energies[0].tolist(), strict=True)),
        "relative_final_energy": {name: float(end / start) for name, end, start in
                                  zip(names, energies[-1], e0, strict=True) if name != "zero"},
        "stretching_work_per_initial_energy": dict(zip(names, (np.trapezoid(work, x=times, axis=0) / e0).tolist(), strict=True)),
        "dissipation_per_initial_energy": dict(zip(names, (np.trapezoid(dissipation, x=times, axis=0) / e0).tolist(), strict=True)),
        "zero_field_max": float(abs(state[-1]).max()) if viscosity else None,
        "shifted_final_field_l2_from_reference":
            relative_difference(grid, MAGNETIC_SCALE_S*grid.curl(state[0]), state[names.index("shifted")])
            if viscosity else None,
        "shapes":shapes,
    }
    arrays = {"t_s":times,"flux":flux,"flux_diffusion_rate":rates,"energy":energies,
              "dissipation_power":dissipation,"stretching_power":work,"final_section_xyz_m":points}
    return data,arrays


def shear_case(grid, dt):
    k = 2*np.pi/LENGTH
    z = grid.axis[None,None,:]
    n = grid.n
    velocity, field = np.zeros((3,n,n,n)),np.zeros((3,n,n,n))
    velocity[0] = np.sin(k*z)
    field[2] = .05
    state = grid.spectrum(np.stack((velocity,field)))
    e0 = .5*grid.norm2(state[1])
    for _ in range(round(DURATION/dt)):
        state, _ = advance(grid,state,np.array([.03,.03]),dt)
    physical = grid.physical(state)
    analytic = .05*k*DURATION*np.exp(-.03*k*k*DURATION)*np.cos(k*z)
    abs_difference = np.max(abs(physical[1,0]-analytic))
    omega = np.linalg.norm(grid.physical(grid.curl(state[0])),axis=0)
    return {"n":grid.n,
            "max_error_induced_Bx_normalized":float(abs_difference/abs(analytic).max()),
            "magnetic_energy_initial_j":float(e0),
            "magnetic_energy_end_j":float(.5*grid.norm2(state[1])),
            "vorticity_superlevel":topology.component_topology(omega,.35)}


def run(out, case):
    out.mkdir(parents=True,exist_ok=True)
    n,dt,nu,size = {"ideal32":(32,.01,0.,16), "ideal48":(48,.01,0.,24),
                    "diffusive32":(32,.01,.03,16), "diffusive48":(48,.01,.03,24),
                    "time_refined48":(48,.005,.03,24), "surface_coarse48":(48,.01,.03,16),
                    "shear":(32,.01,.03,16)}[case]
    grid = PeriodicGrid(n)
    if case=="shear":
        result = shear_case(grid,dt)
        checks = {"shear_exact_solution":result["max_error_induced_Bx_normalized"]<.005,
                  "shear_growth":result["magnetic_energy_end_j"]>result["magnetic_energy_initial_j"],
                  "shear_vorticity_not_ring":not result["vorticity_superlevel"]["candidate"]}
    else:
        result, arrays = run_ring(grid,dt,nu,size)
        np.savez_compressed(out/"histories.npz",**arrays)
        checks = {"solenoidal": result["max_divergence_spectral_relative"]<1.e-10,
                  "matched_initial_condition_l2":result["matching_field_max_relative_l2"]<1.e-8,
                  "material_flux_balance":max(result["largest_relative_flux_balance_error"].values())<.05,
                  "energy_balance":max(result["largest_relative_energy_balance_error"].values())<.02}
        if nu:
            remaining = result["relative_final_flux"]
            checks["faster_diffusion_loses_more_flux"] = bool(
                np.mean(remaining["faster_diffusion"])<np.mean(remaining["matched"]))
            checks["zero_field_remains_zero"] = result["zero_field_max"]==0.
    save_summary(out,{"case":case,**result,"checks":checks},__file__,topology.__file__)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case",required=True,choices=["ideal32","ideal48","diffusive32","diffusive48",
                                                      "time_refined48","surface_coarse48","shear"])
    parser.add_argument("--out",type=Path,default=OUT)
    args=parser.parse_args()
    run(args.out/args.case,args.case)
