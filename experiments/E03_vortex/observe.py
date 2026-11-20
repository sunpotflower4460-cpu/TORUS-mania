"""Matched observables for an imposed ring, interacting rings and a boundary-driven jet."""
import numpy as np
from scipy.signal import find_peaks

from .topology import component_topology


def field_metrics(tank, u, pressure, pair):
    vel = tank.centers(u)
    omega = tank.curl(vel)
    mag = np.linalg.norm(omega, axis=0)
    speed = np.linalg.norm(vel, axis=0)
    x,y,z = tank.coords()
    r = np.hypot(x,y)
    azimuthal = (x*omega[1]-y*omega[0])/np.maximum(r, 1e-30)
    weight = np.maximum(np.abs(azimuthal)-.15*np.max(np.abs(azimuthal)), 0)
    def moments(w):
        mass = w.sum()
        if mass < 1e-15:
            return None
        rc, zc = (w*r).sum()/mass, (w*z).sum()/mass
        width = np.sqrt((w*((r-rc)**2+(z-zc)**2)).sum()/mass)
        return [float(zc), float(rc), float(width)]
    def location(a, fn):
        idx = np.unravel_index(fn(a), a.shape)
        return {"value": float(a[idx]), "xyz": [float(tank.axes[i][j]) for i,j in enumerate(idx)]}
    result = {"omega_peak": location(mag, np.argmax), "speed_peak": location(speed, np.argmax),
              "p_min": location(pressure, np.argmin), "core_z_r_rms": moments(weight),
              "topology": {str(f): component_topology(mag, f) for f in (.25,.35,.50)}}
    mid = tank.n//2
    result["upper_half_energy"] = float(.5*(vel[:,:,:,mid:]**2).sum()*tank.h**3)
    # Positive is upward across the midplane; includes viscous stress in the Laplacian form.
    iz = mid
    um = .5*(vel[:,:,:,iz-1]+vel[:,:,:,iz])
    pressure_mid = .5*(pressure[:,:,iz-1]+pressure[:,:,iz])
    adv_pressure = (pressure_mid + .5*np.sum(um*um, axis=0))*u[2][:,:,iz]
    visc_flux = -tank.nu*np.sum(um*(vel[:,:,:,iz]-vel[:,:,:,iz-1])/tank.h, axis=0)
    result["midplane_energy_flux"] = float((adv_pressure+visc_flux).sum()*tank.h**2)
    result["upward_flux_near_inlet"] = float(np.maximum(u[2][:,:,max(1,round(.5/tank.h))], 0).sum()*tank.h**2)
    if pair:
        profile = weight.sum(axis=(0,1))
        peaks = find_peaks(profile, height=.15*profile.max(), distance=max(2,round(.5/tank.h)))[0]
        result["resolved_pair_z_r_rms"] = None
        if len(peaks) == 2:
            a,b = peaks
            valley = a+int(np.argmin(profile[a:b+1]))
            if profile[valley] < .85*min(profile[a],profile[b]):
                result["resolved_pair_z_r_rms"] = [moments(weight*(z <= tank.axes[2][valley])),
                                                    moments(weight*(z > tank.axes[2][valley]))]
    plane = tank.n//2
    fields = {"speed": speed[:,plane,:], "vorticity": mag[:,plane,:], "p": pressure[:,plane,:]}
    return result, fields


def evolve(tank, u, duration, dt, port=None, tracers=False, pair=False, sample=.125):
    """Integrate through both the drive and decay; save all snapshot metrics and tracer positions."""
    steps = round(duration/dt)
    if abs(steps*dt-duration) > 1e-12:
        raise ValueError("Duration must be an integer number of steps")
    zmid = tank.length/2
    points = np.array([[0,0,zmid-.3], [0,0,zmid], [.6,0,zmid], [1.,0,zmid],
                       [1.4,0,zmid], [1.,0,zmid+.35], [-1.,0,zmid]])
    frozen_points = points.copy()
    initial_vel = tank.centers(u) if tracers else None
    residence = np.zeros(len(points))
    a, v = tank.rhs(u)
    pressure = tank.project([q+dt*(f+g) for q,f,g in zip(u,a,v)], port(0) if port else None, dt)
    energies = []
    images = {}
    rows = []
    total_work = np.zeros(4)
    max_div = max_flux = peak_cfl = largest_residual = 0.
    e0 = tank.inner(u,u)/2
    for step in range(steps+1):
        t = step*dt
        if step % max(1,round(sample/dt)) == 0 or step == steps:
            metrics, fields = field_metrics(tank, u, pressure, pair)
            energies.append(tank.inner(u,u)/2)
            residual = energies[-1]-e0-total_work.sum()
            largest_residual = max(largest_residual, abs(residual))
            metrics.update(time=t, energy=energies[-1], cumulative_work=total_work.tolist(),
                           energy_residual=float(residual))
            if tracers:
                metrics.update(tracers=points.tolist(), frozen_field_tracers=frozen_points.tolist(),
                               sampled_core_residence_s=residence.tolist())
            rows.append(metrics)
            if step in (0, steps) or (port and abs(t-1.)<1e-9):
                images.update({f"{name}_{step}": values for name,values in fields.items()})
        if step == steps:
            break
        u, pressure, mid, work = tank.step(u, dt, port(t+dt/2) if port else None,
                                           port(t+dt) if port else None)
        total_work += work
        div = tank.divergence(u)
        max_div = max(max_div, float(np.abs(div).max()))
        flux = sum((np.take(q,-1,axis=i)-np.take(q,0,axis=i)).sum() for i,q in enumerate(u))*tank.h**2
        max_flux = max(max_flux, abs(float(flux)))
        cfl = sum(float(np.abs(q).max()) for q in mid)*dt/tank.h
        peak_cfl = max(peak_cfl, cfl)
        if not np.isfinite(cfl) or cfl > 1.2:
            raise ArithmeticError(f"Unstable flow CFL={cfl} at t={t}")
        if tracers:
            live = tank.centers(mid)
            midpoint = points+.5*dt*tank.sample(live,points)
            points += dt*tank.sample(live,midpoint)
            fp = frozen_points+.5*dt*tank.sample(initial_vel,frozen_points)
            frozen_points += dt*tank.sample(initial_vel,fp)
            mag = np.linalg.norm(tank.curl(live), axis=0)
            residence += dt*(tank.sample(mag[None],midpoint)[:,0] >= .35*mag.max())
    # Normalization remains meaningful for a tank which starts at rest.
    scale = max(1e-15, max(energies), np.abs(total_work).max())
    summary = {"n": tank.n, "length": tank.length, "nu": tank.nu, "dt": dt, "duration": duration,
               "periodic_axes": tank.periodic, "max_div": max_div, "max_abs_net_flux": max_flux,
               "max_cfl": peak_cfl, "max_energy_residual_rel": float(largest_residual/scale),
               "initial_energy": e0, "rows": rows}
    return summary, images
