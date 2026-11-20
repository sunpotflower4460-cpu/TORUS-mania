"""E03 calibration: analytic axisymmetric ring, matched controls, time-evolving incompressible flow."""
import argparse
from pathlib import Path
import numpy as np
from experiments.common import save_summary
from . import fluid, observe, topology
from .fluid import Tank, initial_rings, ring_velocity

OUT = Path(__file__).resolve().parents[2] / "research/results/E03"


def taylor_green(n):
    g = Tank(n)
    u = g.zeros()
    k = np.pi / g.length
    for i in (0,1):
        x,y,_ = g.coords(i)
        a,b = k*(x+g.length/2),k*(y+g.length/2)
        u[i][:] = np.sin(a)*np.cos(b) if i == 0 else -np.cos(a)*np.sin(b)
    g.project(u)
    initial = [q.copy() for q in u]
    dt = 1/32
    for _ in range(8):
        u,p,_,_ = g.step(u,dt)
    decay = np.exp(-2*g.nu*k*k*8*dt)
    err = [q-decay*ref for q,ref in zip(u,initial)]
    x,y,_ = g.coords()
    exact_p = .25*(np.cos(2*k*(x+g.length/2))+np.cos(2*k*(y+g.length/2)))*np.exp(-4*g.nu*k*k*7.5*dt)
    return {"velocity_rel_l2": np.sqrt(g.inner(err,err)/g.inner(u,u)),
            "pressure_rel_l2": float(np.sqrt(np.mean((p-exact_p)**2)/np.mean(exact_p**2))),
            "max_div": float(np.abs(g.divergence(u)).max())}


def controls(n):
    tank = Tank(n)
    x,y,z = tank.coords()
    base = np.zeros((n,n,n))
    records = {}
    for name, components in {
        "rest": (base,base,base), "uniform": (base+1,base,base),
        "shear": (base+y,base,base),
        "local_rotation": (-y*np.exp(-(x*x+y*y)),x*np.exp(-(x*x+y*y)),base),
    }.items():
        vel = np.array(np.broadcast_arrays(*components))
        mag = np.linalg.norm(tank.curl(vel),axis=0)
        records[name] = topology.component_topology(mag,.35)
    for name, mask in {"solid_ring": (np.hypot(x,y)-1)**2+(z-3)**2 < .42**2,
                       "ball": x*x+y*y+(z-3)**2 < 1,
                       "shell": np.abs(np.sqrt(x*x+y*y+(z-3)**2)-1)<.25}.items():
        records[name] = topology.component_topology(mask.astype(float),.35)
    return records


def streamline_control():
    # Exact unbounded NS solution: solid rotation plus translation; p is quadratic.
    omega, speed = 2*np.pi, .4
    def velocity(t,p):
        return np.array([speed-omega*p[1], omega*(p[0]-speed*t)])
    result = {}
    for moving in (False,True):
        p = np.array([1.,0.])
        dt=1/256
        for i in range(256):
            t=i*dt if moving else 0.
            h=dt if moving else 0.
            a=velocity(t,p)
            b=velocity(t+h/2,p+dt*a/2)
            c=velocity(t+h/2,p+dt*b/2)
            d=velocity(t+h,p+dt*c)
            p += dt/6*(a+2*b+2*c+d)
        result["live_displacement" if moving else "frozen_displacement"] = float(np.linalg.norm(p-[1,0]))
    return result


def run(out):
    out.mkdir(parents=True,exist_ok=True)
    z = np.linspace(-2,2,17)
    axis = {}
    for count in (32,64):
        _,uz = ring_velocity(np.array([0.]),z,4,.4,sections=count)
        axis[str(count)] = float(np.max(np.abs(uz-2/(1+z*z+.4**2)**1.5)))
    rs,zs = np.meshgrid(np.linspace(0,2,33),np.linspace(-1,1,33))
    coarse = ring_velocity(rs,zs,4,.4,sections=32)
    fine = ring_velocity(rs,zs,4,.4,sections=64)
    stats = {"analytic_axis_errors":axis,"off_axis_quadrature_max_change":float(np.max(np.abs(np.subtract(coarse,fine)))),
             "translated_rotation":streamline_control(), "taylor_green":{}, "controls":{}, "runs":[], "checks":{}}
    checks = stats["checks"]
    checks["axis_solution"] = max(axis.values()) < 1e-10
    checks["tracer_control"] = stats["translated_rotation"]["frozen_displacement"] < 1e-7 and abs(stats["translated_rotation"]["live_displacement"]-.4)<1e-7
    for n in (32,48):
        stats["taylor_green"][str(n)] = cal = taylor_green(n)
        stats["controls"][str(n)] = ref = controls(n)
        checks[f"manufactured_{n}"] = cal["velocity_rel_l2"]<.03 and cal["pressure_rel_l2"]<.03 and cal["max_div"]<1e-8
        checks[f"topology_{n}"] = ref["solid_ring"]["candidate"] and ref["shell"]["cavities"]==1 and all(not v["candidate"] for k,v in ref.items() if k!="solid_ring")
    for n,dt in [(32,1/64),(32,1/128),(48,1/128)]:
        g=Tank(n)
        row,fields=observe.evolve(g,initial_rings(g,[(3,4,.4)]),.75,dt,tracers=True)
        stats["runs"].append(row)
        np.savez_compressed(out/f"slice_{n}_{round(1/dt)}.npz",**fields)
        checks[f"balance_{n}_{dt}"] = row["max_div"]<1e-8 and row["max_abs_net_flux"]<1e-9 and row["max_energy_residual_rel"]<.02 and row["rows"][-1]["energy"]<row["initial_energy"]
    shifts=[r["rows"][-1]["core_z_r_rms"][0]-r["rows"][0]["core_z_r_rms"][0] for r in stats["runs"]]
    stats["core_displacements"] = shifts
    stats["spatial_change_relative"] = abs(shifts[1]-shifts[2])/abs(shifts[2])
    stats["speed_resolved"] = stats["spatial_change_relative"]<=.25
    save_summary(out,stats,__file__,fluid.__file__,observe.__file__,topology.__file__)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,default=OUT)
    run(parser.parse_args().out)
