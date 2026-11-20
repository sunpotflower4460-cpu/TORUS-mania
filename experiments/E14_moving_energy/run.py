"""Follow the energy inside a moving toroidal control volume."""
import argparse
from pathlib import Path

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.integrate import cumulative_trapezoid

from experiments.common import save_summary
from experiments.E03_vortex import fluid, topology
from experiments.E06_jet import run as jet
from experiments.E11_energy_transport import run as previous_energy

OUT = Path(__file__).resolve().parents[2] / "research/results/E14"
FLOW_START = 1.25
FLOW_END = 2.25
RATES = ["carried_out", "carried_in", "pressure_out", "viscous_out",
         "dissipation", "unit_pressure_offset_out"]


def interval_rule(n, low, high):
    x,w = leggauss(n)
    length = high-low
    return low+(x+1)*length/2,w*length/2


class Tube:
    """Quadrature for the surface and solid volume of a circular torus."""
    def __init__(self, major, minor, counts):
        self.major, self.minor = major,minor
        n_phi,n_theta,n_r = counts
        phi = np.arange(n_phi)*2*np.pi/n_phi
        theta = np.arange(n_theta)*2*np.pi/n_theta
        radius, dr_weights = interval_rule(n_r,0.,minor)
        self.angular_element = (2*np.pi)**2/(n_phi*n_theta)
        self.cos_phi = np.tile(np.cos(phi),n_theta)
        self.sin_phi = np.tile(np.sin(phi),n_theta)
        cos_theta = np.cos(theta)[:,None]
        sin_theta = np.sin(theta)[:,None]
        self.surface_r = np.repeat(major+minor*cos_theta,n_phi)
        self.surface_z = np.repeat(minor*sin_theta,n_phi)
        self.nr = np.repeat(cos_theta,n_phi)
        self.nz = np.repeat(sin_theta,n_phi)
        self.surface_weights = self.angular_element*minor*self.surface_r
        r,ang,p = np.meshgrid(radius,theta,phi,indexing="ij")
        self.volume_r = (major+r*np.cos(ang)).ravel()
        self.volume_z = (r*np.sin(ang)).ravel()
        self.volume_phi = p.ravel()
        weights = self.angular_element*(r*(major+r*np.cos(ang))*dr_weights[:,None,None])
        self.volume_weights = weights.ravel()

    def surface(self, z):
        return np.column_stack((self.surface_r*self.cos_phi,self.surface_r*self.sin_phi,
                                self.surface_z+z))

    def volume(self, z):
        return np.column_stack((self.volume_r*np.cos(self.volume_phi),
                                self.volume_r*np.sin(self.volume_phi), self.volume_z+z))


def flux_parts(flux, surface_weights):
    return float(surface_weights @ flux.clip(min=0)), float(surface_weights @ (-flux).clip(min=0))


def finalize(t, stored, rates, midpoint=False):
    if midpoint:
        increments = np.diff(t)[:, None] * rates
        cumulative = np.vstack((np.zeros(rates.shape[1]), np.cumsum(increments, axis=0)))
    else:
        cumulative = cumulative_trapezoid(rates, t, axis=0, initial=0.)
    carried_out, carried_in, pressure, viscous, loss, gauge = cumulative.T
    difference = stored-stored[0]+carried_out-carried_in+pressure+viscous+loss
    scale = max(stored.max(),carried_out[-1],carried_in[-1],loss[-1],
                abs(pressure).max(),abs(viscous).max())
    values = {name:float(values[-1]) for name,values in zip(RATES,cumulative.T,strict=True)}
    result = {"initial_energy":float(stored[0]),"final_energy":float(stored[-1]),
              "final_over_initial":float(stored[-1]/stored[0]),
              "normalized_balance_error":float(abs(difference).max()/scale),
              "cumulative":values,
              "cumulative_per_initial_energy":{name:value/stored[0] for name,value in values.items()},
              "optical_or_advective_exchange_per_initial":float((carried_out[-1]+carried_in[-1])/stored[0])}
    return result,np.column_stack((t,stored,cumulative,difference))


def center_height(tank, velocity):
    x,y,z = tank.coords()
    w = tank.curl(velocity)
    angular = abs(x*w[1]-y*w[0])/np.hypot(x,y)
    restricted = np.where(z>=.35,angular,0.)
    mask = restricted>=.35*restricted.max()
    return float(np.sum(restricted*mask*z)/np.sum(restricted*mask)), angular


def flow_rates(tank, tube, center, translation, fields):
    vel, e, p, grad_e, loss = fields
    on = tank.sample(np.concatenate((vel,e[None],p[None],grad_e)),tube.surface(center))
    cx,cy = tube.cos_phi,tube.sin_phi
    direction = np.column_stack((tube.nr*cx,tube.nr*cy,tube.nz))
    normal = np.sum(on[:,:3]*direction,axis=1)
    moved = on[:,3]*(normal-translation*tube.nz)
    carried_out,carried_in = flux_parts(moved,tube.surface_weights)
    pressure = tube.surface_weights @ (normal*on[:,4])
    viscosity = -tank.nu*(tube.surface_weights @ np.sum(on[:,5:8]*direction,axis=1))
    dissipated = tube.volume_weights @ tank.sample(loss[None],tube.volume(center))[:,0]
    return [carried_out,carried_in,pressure,viscosity,dissipated,tube.surface_weights @ normal]


def collocated_terms(tank, mid, p):
    vel = tank.centers(mid)
    e = previous_energy.kinetic(vel)
    gradients = np.gradient(vel,tank.h,axis=(1,2,3),edge_order=2)
    loss = tank.nu*sum(np.sum(g*g,axis=0) for g in gradients)
    return vel,e,p,np.array(np.gradient(e,tank.h,edge_order=2)),loss


def flow_case(n):
    tank = fluid.Tank(n,viscosity=.05,inlet=True)
    inlet = jet.profile(tank,"circle",1.)

    def port(t):
        return inlet*np.sin(np.pi*t)**2 if t<1. else tank.zero_plane

    dt = 1/128
    start,end = round(FLOW_START/dt),round(FLOW_END/dt)
    u = tank.zeros()
    histories = {(fine,moving):{"energy":[],"powers":[]} for fine in (False,True) for moving in (False,True)}
    rule = {False:Tube(.75,.40,(16,32,8)),True:Tube(.75,.40,(32,64,16))}
    heights, topology_at_samples = [], []
    old_z, fixed_z = None,None
    for step in range(1,end+1):
        u,p,mid,_ = tank.step(u,dt,port((step-.5)*dt),port(step*dt))
        if step<start:
            continue
        vel = tank.centers(u)
        e = previous_energy.kinetic(vel)
        z, angular = center_height(tank,vel)
        if step==start:
            fixed_z = z
        if min(z,fixed_z)-rule[True].minor<=tank.h/2:
            raise ValueError(f"Tube touches the inlet grid at step {step} of n={n}")
        heights.append(z)
        if (step-start)%16==0:
            topology_at_samples.append({"t_s":step*dt,"azimuthal_vorticity":
                                        topology.component_topology(angular,.35),
                                        "kinetic_energy":topology.component_topology(e,.35)})
        terms = collocated_terms(tank,mid,p) if old_z is not None else None
        for (fine,moving), series in histories.items():
            tube = rule[fine]
            z_now = z if moving else fixed_z
            series["energy"].append(float(tube.volume_weights @ tank.sample(e[None],tube.volume(z_now))[:,0]))
            if old_z is not None:
                z_mid = (z+old_z)/2 if moving else fixed_z
                speed = (z-old_z)/dt if moving else 0.
                series["powers"].append(flow_rates(tank,tube,z_mid,speed,terms))
        old_z = z
    times = np.linspace(FLOW_START,FLOW_END,len(heights))
    arrays = {"t_s":times,"ring_center_z_m":np.array(heights)}
    trials = {}
    for (fine,moving), series in histories.items():
        name = ("fine" if fine else "coarse")+("_moving" if moving else "_fixed")
        values, table = finalize(times,np.array(series["energy"]),np.array(series["powers"]),midpoint=True)
        arrays[name] = table
        trials[name] = values
    return {"grid":n,"dt_s":dt,"energy_units":"J at density 1 kg/m3",
            "time_s":[FLOW_START,FLOW_END],"tube_radii_m":[.75,.40],
            "tracking_height_m":[float(heights[0]),float(heights[-1])],
            "topology_at_samples":topology_at_samples,"trials":trials},arrays


def light_fields(r,z,t,q2,part):
    e_phi,b_r,b_z = previous_energy.maxwell(r,z,t,q2,part)
    return (e_phi**2+b_r**2+b_z**2)/2,e_phi*b_z,-e_phi*b_r


def whole_space(t,q2,part,n):
    s,w = interval_rule(n,0.,1.)
    radius = 5*s/(1-s)
    dr = w*5/(1-s)**2
    angle = np.pi*(s-.5)
    z = 5*np.tan(angle)
    dz = w*5*np.pi/np.cos(angle)**2
    measure = (2*np.pi*radius*dr)[:,None]*dz[None,:]
    e,_,sz = light_fields(radius[:,None],z[None,:],t,q2,part)
    energy = np.sum(e*measure)
    momentum = np.sum(sz*measure)
    center = np.sum(z[None,:]*e*measure)/energy
    return {"t":t,"energy":float(energy),"axial_momentum":float(momentum),"center":float(center)}


def light_rates(tube,t,center,speed,q2,part):
    e,sr,sz = light_fields(tube.surface_r,tube.surface_z+center,t,q2,part)
    carried_out,carried_in = flux_parts(sr*tube.nr+(sz-speed*e)*tube.nz,tube.surface_weights)
    interior,*_ = light_fields(tube.volume_r,tube.volume_z+center,t,q2,part)
    stored = float(tube.volume_weights @ interior)
    return stored,[carried_out,carried_in,0.,0.,0.,0.]


def light_tracers(tube,q2,part,velocity,origin,dt):
    r,z = np.copy(tube.volume_r),tube.volume_z+origin
    weights = tube.volume_weights*light_fields(r,z,0.,q2,part)[0]
    initial = np.sum(weights)
    inside = np.ones(len(r),dtype=bool)
    max_speed = 0.
    trajectory = []

    def transport(r,z,t):
        e,sr,sz = light_fields(r,z,t,q2,part)
        denominator = np.maximum(e,np.finfo(float).tiny)
        return np.stack((sr/denominator,sz/denominator))

    state = np.stack((r,z))
    steps = round(4/dt)
    for i in range(steps+1):
        t = i*dt
        radius, axial = state
        contained = (radius-tube.major)**2+(axial-origin-velocity*t)**2<=tube.minor**2
        inside &= contained
        if i%round(.1/dt)==0:
            trajectory.append([t,np.sum(weights[contained])/initial,np.sum(weights[inside])/initial])
        if i<steps:
            a = transport(*state,t)
            b = transport(*(state+dt*a/2),t+dt/2)
            c = transport(*(state+dt*b/2),t+dt/2)
            d = transport(*(state+dt*c),t+dt)
            state += dt/6*(a+2*b+2*c+d)
            max_speed = max(max_speed,float(np.hypot(*a).max()))
    result = {"dt":dt,"points":len(weights),"max_flux_speed_over_c":max_speed,
              "inside_final_fraction":float(trajectory[-1][1]),
              "always_sampled_inside_fraction":float(trajectory[-1][2])}
    return result,np.array(trajectory)


def optical_superlevels(q2, part, velocity, origin):
    """Classify independently of the imposed integration surface."""
    reports = []
    for n in (64, 96):
        coordinates = -6 + (np.arange(n) + .5) * (12 / n)
        radius = np.hypot(coordinates[:, None], coordinates[None, :])[:, :, None]
        for t in (0., 1., 2., 4.):
            z = coordinates[None, None, :] + origin + velocity * t
            e_phi, b_r, b_z = previous_energy.maxwell(radius, z, t, q2, part)
            energy = (e_phi**2 + b_r**2 + b_z**2) / 2
            fields = {"electric_strength": abs(e_phi), "electromagnetic_energy": energy}
            reports.append({"n": n, "time": t, "thresholds": {
                str(level): {name: topology.component_topology(field, level)
                             for name, field in fields.items()}
                for level in previous_energy.THRESHOLDS
            }})
    return reports


def boost_calibration(q2, part, integrated_velocity):
    """The axial center-of-energy frame has symmetric optical lengths."""
    beta = (q2 - 1) / (q2 + 1)
    gamma = 1 / np.sqrt(1 - beta**2)
    r, z, t = np.meshgrid(np.linspace(.15, 3., 14), np.linspace(-2., 2., 17), [0., .8, 2.1],
                         indexing="ij", sparse=True)
    e, br, bz = previous_energy.maxwell(r, z, t, q2, part)
    boosted = np.array((gamma * (e + beta * br), gamma * (br + beta * e), bz))
    z_rest, t_rest = gamma * (z - beta * t), gamma * (t - beta * z)
    denominator = r**2 + z_rest**2 - t_rest**2 + q2 - 2j * np.sqrt(q2) * t_rest
    complex_fields = (-8 * r * (t_rest + 1j * np.sqrt(q2)) / denominator**3,
                      8 * r * z_rest / denominator**3,
                      4 / denominator**2 - 8 * r**2 / denominator**3)
    direct = np.array([getattr(field, part) for field in complex_fields])
    error = np.max(abs(boosted - direct)) / np.max(abs(direct))
    return {"analytic_velocity_over_c": beta, "velocity_absolute_error": abs(integrated_velocity - beta),
            "boosted_field_max_relative_error": float(error)}


def light_case(q2,part,major,minor):
    reference = [whole_space(t,q2,part,256) for t in (0.,1.5,4.)]
    low_order = whole_space(0.,q2,part,128)
    velocity = reference[0]["axial_momentum"]/reference[0]["energy"]
    origin = reference[0]["center"]
    trials,arrays = {},{}
    for fine in (False,True):
        tube = Tube(major,minor,(1,128,24) if fine else (1,64,12))
        times = np.linspace(0.,4.,401 if fine else 201)
        for moving in (False,True):
            speed = velocity if moving else 0.
            name = ("fine" if fine else "coarse")+("_moving" if moving else "_fixed")
            series = [light_rates(tube,t,origin+speed*t,speed,q2,part) for t in times]
            values, data = finalize(times,np.array([e for e,_ in series]),np.array([p for _,p in series]))
            trials[name] = values
            arrays[name] = data
        if q2==20:
            tracer, data = light_tracers(tube,q2,part,velocity,origin,.005 if fine else .01)
            trials["fine_tracers" if fine else "coarse_tracers"] = tracer
            arrays["fine_tracers" if fine else "coarse_tracers"] = data
    return {"q2":q2,"component":part,"energy_units_j":float(previous_energy.ENERGY_UNIT),
            "tube_radii_normalized":[major,minor],"translation_speed_over_c":velocity,
            "whole_space_reference":reference,"low_order_at_zero":low_order,
            "superlevel_topology":optical_superlevels(q2, part, velocity, origin),
            "analytic_center_frame":boost_calibration(q2, part, velocity),
            "trials":trials},arrays


def translating_control():
    """Analytic plane wave crossing a fixed tube and moving with a second tube."""
    tube = Tube(2., .5, (1, 64, 12))
    times = np.linspace(0, 4, 401)
    comparisons = {}
    for speed, name in ((0., "fixed"), (1., "moving")):
        offset = speed * times - times
        energy = np.exp(-(tube.volume_z + offset[:, None])**2)
        stored = energy @ tube.volume_weights
        density = np.exp(-(tube.surface_z + offset[:, None])**2)
        poynting_normal = density * tube.nz
        boundary_term = speed * density * tube.nz
        rates = np.zeros((len(times), len(RATES)))
        for rate, flux in zip(rates, poynting_normal - boundary_term, strict=True):
            rate[:2] = flux_parts(flux, tube.surface_weights)
        comparisons[name], _ = finalize(times, stored, rates)
    return comparisons


def run(out,variant):
    out.mkdir(parents=True,exist_ok=True)
    describe = ["time","energy",*["integral_"+name for name in RATES],"energy_balance_residual"]
    sources = []
    if variant.startswith("flow"):
        result,arrays = flow_case(int(variant[4:]))
        checks = {"moving_and_fixed_energy_budget":all(r["normalized_balance_error"]<=.10
                                                       for r in result["trials"].values())}
        sources = [fluid.__file__,jet.__file__,topology.__file__]
    else:
        result,arrays = light_case(20,"imag",2.05,.65) if variant=="light20" else light_case(5,"real",1.,.40)
        result["translating_wave_control"] = translating_control()
        global_results = result["whole_space_reference"]
        global_energy = np.array([r["energy"] for r in global_results])
        control = result["translating_wave_control"]
        center_error = max(abs(row["center"] - global_results[0]["center"]
                               - result["translation_speed_over_c"] * row["t"])
                           for row in global_results)
        result["whole_space_center_motion_max_error"] = center_error
        checks = {"translating_wave_exact":control["moving"]["normalized_balance_error"]<1.e-12
                                         and control["moving"]["optical_or_advective_exchange_per_initial"]<1.e-12,
                  "fixed_plane_wave_crosses_surface":control["fixed"]["normalized_balance_error"]<1.e-3
                                                   and control["fixed"]["final_over_initial"]<.01,
                  "moving_and_fixed_energy_budget":all(r["normalized_balance_error"]<=.01
                              for name,r in result["trials"].items() if not name.endswith("tracers")),
                  "global_energy_constant":bool(np.ptp(global_energy)/global_energy[0]<.01),
                  "global_velocity_calibration":bool(abs(result["low_order_at_zero"]["energy"]/global_energy[0]-1.)<.01
                                                     and center_error<.01),
                  "analytic_center_frame": result["analytic_center_frame"]["velocity_absolute_error"]<1.e-10
                         and result["analytic_center_frame"]["boosted_field_max_relative_error"]<1.e-10,
                  "tracer_sub_luminal":all(r["max_flux_speed_over_c"]<=1.+1.e-12
                                             for name,r in result["trials"].items() if name.endswith("tracers"))}
        result["tracer_columns"] = ["time","fraction_inside_now","fraction_never_observed_outside"]
        sources = [topology.__file__]
    np.savez_compressed(out/"histories.npz",**arrays)
    save_summary(out,{"variant":variant,"budget_columns":describe,"checks":checks,**result},
                 __file__,previous_energy.__file__,*sources)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant",choices=["flow48","flow64","light20","light5"],required=True)
    parser.add_argument("--out",type=Path,default=OUT)
    args = parser.parse_args()
    run(args.out/args.variant,args.variant)
