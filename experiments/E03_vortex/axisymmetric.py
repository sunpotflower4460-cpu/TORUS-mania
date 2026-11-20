"""Axisymmetric, swirl-free viscous ring in an impermeable free-slip cylinder.
State eta=omega_theta/r, streamfunction psi=r² chi. Conservative annular advection.
"""
import argparse
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu
from experiments.common import save_summary


class Cylinder:
    def __init__(self,n):
        self.n=n; self.h=3/n
        self.r=(np.arange(n)[:,None]+.5)*self.h
        self.z=(np.arange(2*n)[None,:]+.5)*self.h
        self.edge=np.arange(n+1)[:,None]*self.h
        # (1/r³) d_r (r³ d_r) using exact shell integrals of r³.
        shell=(self.edge[1:]**4-self.edge[:-1]**4)/4
        lo=(self.edge[:-1]**3/(self.h*shell)).ravel()
        hi=(self.edge[1:]**3/(self.h*shell)).ravel()
        diag=-lo-hi
        diag[-1]-=hi[-1]  # zero at the wall, half cell away
        radial=sparse.diags((lo[1:],diag,hi[:-1]),(-1,0,1))
        axial=sparse.diags((np.ones(2*n-1),-2*np.ones(2*n),np.ones(2*n-1)),(-1,0,1)).tolil()
        axial[0,0]=axial[-1,-1]=-3
        self.lap=sparse.kronsum(axial.tocsr()/self.h**2,radial.tocsr(),format="csr")
        self.poisson=splu((-self.lap).tocsc())

    def field(self,eta):
        chi=self.poisson.solve(eta.ravel()).reshape(eta.shape)
        psi=np.zeros((self.n+1,2*self.n+1))
        psi[1:-1,1:-1]=(chi[:-1,:-1]+chi[1:,:-1]+chi[:-1,1:]+chi[1:,1:])*.25*self.edge[1:-1]**2
        ur=np.zeros((self.n+1,2*self.n))
        ur[1:]=-np.diff(psi[1:],axis=1)/(self.h*self.edge[1:])
        uz=np.diff(psi,axis=0)/(self.r*self.h)
        return ur,uz

    def rhs(self,eta):
        ur,uz=self.field(eta)
        fr=np.zeros_like(ur); fz=np.zeros_like(uz)
        fr[1:-1]=self.edge[1:-1]*ur[1:-1]*(eta[:-1]+eta[1:])*.5
        fz[:,1:-1]=uz[:,1:-1]*(eta[:,:-1]+eta[:,1:])*.5
        return (.05*(self.lap@eta.ravel()).reshape(eta.shape)
                -(np.diff(fr,axis=0)/self.r+np.diff(fz,axis=1))/self.h)

    def observables(self,eta):
        ur,uz=self.field(eta)
        div=(np.diff(self.edge*ur,axis=0)/self.r+np.diff(uz,axis=1))/self.h
        volume=2*np.pi*self.r*self.h**2
        energy=np.sum(volume*((ur[:-1]+ur[1:])**2+(uz[:,:-1]+uz[:,1:])**2))/8
        omega=eta*self.r
        weight=np.maximum(abs(omega)-.15*abs(omega).max(),0)*volume
        return {"energy":float(energy),"enstrophy_dissipation":float(.05*np.sum(volume*omega**2)),
                "max_div":float(abs(div).max()),"core_z":float(np.sum(weight*self.z)/np.sum(weight))}


def run(out):
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for n,dt in [(24,1/128),(48,1/256)]:
        c=Cylinder(n)
        k=np.pi/6
        phi=(1-c.r**2/9)*np.sin(k*c.z)
        source=(8/9)*np.sin(k*c.z)+k*k*phi
        inferred=c.poisson.solve(source.ravel()).reshape(phi.shape)
        err=float(np.linalg.norm(inferred-phi)/np.linalg.norm(phi))
        eta=np.zeros_like(phi)
        for angle in 2*np.pi*(np.arange(128)+.5)/128:
            d2=1+c.r**2-2*c.r*np.cos(angle)+(c.z-3)**2+.4**2
            eta+=(3*4*.4**2/(2*128))*np.cos(angle)/(d2**2.5*c.r)
        obs=[c.observables(eta)]
        for _ in range(round(.75/dt)):
            mid=eta+dt/2*c.rhs(eta)
            eta+=dt*c.rhs(mid)
            obs.append(c.observables(eta))
        e0=obs[0]["energy"]
        diss=np.trapezoid([x["enstrophy_dissipation"] for x in obs],dx=dt)
        rows.append({"n_r":n,"n_z":2*n,"dt":dt,"poisson_rel_l2":err,"max_div":max(x["max_div"] for x in obs),
                     "energy_budget_error_rel":float(abs(obs[-1]["energy"]-e0+diss)/e0),
                     "displacement_m":obs[-1]["core_z"]-obs[0]["core_z"],"samples":obs[::round(.125/dt)]})
    checks={"poisson":all(r["poisson_rel_l2"]<.02 for r in rows),
            "flux":all(r["max_div"]<1e-8 for r in rows),
            "viscous_budget":all(r["energy_budget_error_rel"]<.05 for r in rows)}
    save_summary(out,{"runs":rows,"checks":checks},__file__)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,default=Path(__file__).resolve().parents[2]/"research/results/E03/cylinder")
    run(p.parse_args().out)
