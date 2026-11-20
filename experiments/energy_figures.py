"""Generate figures for the circulation and local-energy experiments."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from scipy.constants import epsilon_0

ROOT = Path(__file__).resolve().parents[1]/"research/results"
BLUE, ORANGE, GRAY = "#0c6885", "#ba581d", "#63747c"


def read(root, directory):
    return json.loads((root/directory/"summary.json").read_text())


def plot_observations(root, out):
    geometry = read(root,"E09")
    observations = read(root,"E10")
    fig, axes = plt.subplots(2,2,figsize=(9.5,6.8),layout="constrained")

    ax = axes[0,0]
    values = [row for row in geometry["shells"] if row["shell"]=="thick" and row["grid"]==[64,256]]
    x = np.arange(len(values))
    coefficients = np.array([d["norm_matrix_diagonal_m"] for d in values])
    ax.bar(x-.17,coefficients[:,0]*1000,.32,label="Longitudinal",color=BLUE)
    ax.bar(x+.17,coefficients[:,1]*1000,.32,label="Meridional",color=ORANGE)
    ax.set(xticks=x,xticklabels=["Both","Longitudinal","Meridional","Neither"],
           xlabel="Paths left closed",ylabel="Energy coefficient (mm)",title="A   Closed paths support independent circulation")
    ax.legend(frameon=False,loc="upper right")

    ax = axes[0,1]
    d = observations["magnetic_profile"]
    radius = np.array(d["radius_mm"])
    ax.errorbar(radius,np.array(d["measured_gauss"])*.1,yerr=d["reading_uncertainty_gauss"]*.1,
                fmt="o",ms=3.5,color=BLUE,label="Published measurements")
    ax.plot(radius,np.array(d["absolute_prediction_gauss"])*.1,color=ORANGE,
            lw=1.7,label="Ampère prediction · no fit")
    ax.set(xlabel="Distance from axis (mm)",ylabel="Toroidal field (mT)",
           title="B   Internal field of a 12-turn solenoid")
    ax.legend(frameon=False)

    ax = axes[1,0]
    d = observations["barrier"]
    pts = np.array(d["barrier_over_chemical_potential_and_survival"]).T
    ax.scatter(*pts,marker="s",s=27,color=BLUE,label="Published settings")
    ax.axvline(1,ls="--",lw=1,color=GRAY,label="Barrier equals chemical potential")
    ax.set(xlabel="Central barrier / chemical potential",
           ylabel="Fraction still circulating after 2 s",ylim=(-.06,1.14),
           title="C   Superfluid flow survives higher central barriers")
    ax.legend(frameon=False,loc="lower right")

    ax = axes[1,1]
    rows = observations["coil"]["rows"]
    observed = [row["observed_nh"] for row in rows]
    predicted = [row["ideal_nh"] for row in rows]
    ax.plot([10,50],[10,50],color=GRAY,ls="--",label="Equality")
    ax.scatter(observed,predicted,color=ORANGE,s=32,label="Three measured designs")
    ax.set(xlim=(10,50),ylim=(10,50),xlabel="Measured inductance (nH)",
           ylabel="Ideal core prediction (nH)",title="D   Core-only model underestimates bench values")
    ax.legend(frameon=False)
    fig.savefig(out/"circulation_and_measurements.png",dpi=172)
    plt.close(fig)


def contour(ax,x,z,value,title,label,fig,cmap):
    image = ax.pcolormesh(x,z,value.T,shading="nearest",cmap=cmap)
    ax.contour(x,z,value.T,levels=[.35*value.max()],colors=["white"],linewidths=.85)
    ax.set(title=title,xlabel="x (m)" if cmap=="magma" else "x (mm)",
           ylabel="z (m)" if cmap=="magma" else "z (mm)")
    fig.colorbar(image,ax=ax,label=label,pad=.03,shrink=.82)


def plot_fields(root, out):
    fig, axes = plt.subplots(2,2,figsize=(9,7.9),layout="constrained")
    with np.load(root/"E11/fluid/field_64.npz") as d:
        x,z = d["axis_horizontal_m"],d["axis_vertical_m"]
        contour(axes[0,0],x,z,d["vorticity_s_inv"],"A   Jet vorticity","Magnitude (s⁻¹)",fig,"magma")
        contour(axes[0,1],x,z,d["energy_j_m3"],"B   Jet kinetic energy","Density (J/m³)",fig,"magma")
    for ax in axes[0]:
        ax.set(xlim=(-1.75,1.75),ylim=(0,2.7))
        ax.add_patch(Rectangle((-1.5,.75),3,1.5,lw=1,ls="--",edgecolor="#70c5e3",facecolor="none"))
    with np.load(root/"E11/light/field_q20_imag.npz") as d:
        x,z=d["x"],d["z"]
        contour(axes[1,0],x,z,abs(d["electric"]),"C   Toroidal pulse electric field",
                "Azimuthal magnitude (V/m)",fig,"viridis")
        contour(axes[1,1],x,z,d["energy"]*epsilon_0*1.e15,"D   Pulse electromagnetic energy",
                "Density (10⁻¹⁵ J/m³)",fig,"viridis")
        # A section of the local Poynting vector, with both axes sampled on the same grid.
        sr,sz = d["flux_r"],d["flux_z"]
        x_direction = x/np.hypot(x,.0625)
        magnitude = np.hypot(sr,sz)
        threshold = .06*magnitude.max()
        dx = np.where(magnitude>threshold,sr*x_direction[:,None],np.nan)
        dz = np.where(magnitude>threshold,sz,np.nan)
        sample = slice(3,None,5)
        axes[1,1].quiver(x[sample], z[sample],dx[sample,sample].T,dz[sample,sample].T,
                         color="white",width=.004,scale=magnitude.max()*14.)
    for ax in axes[1]:
        ax.set(xlim=(-5.5,5.5),ylim=(-3.,3.))
    fig.suptitle("Field geometry and energy density · white contours at 35% of each peak",
                 fontsize=12,weight="bold")
    fig.savefig(out/"fields_and_energy.png",dpi=172)
    plt.close(fig)


def run(root, out):
    out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,
                         "axes.spines.top":False,"axes.spines.right":False,"axes.titleweight":"bold"})
    plot_observations(root,out)
    plot_fields(root,out)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    run(args.root,args.out or args.root/"energy_figures")
