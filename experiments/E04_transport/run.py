"""E04. Hydraulic transport and single-edge loss on a registered finite candidate grid."""
import argparse
import itertools
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, minimum_spanning_tree
from experiments.common import save_summary

OUT = Path(__file__).resolve().parents[2]/"research/results/E04"
XY = np.array([(x,y) for y in range(5) for x in range(5)])
EDGES = np.array([(i,j) for i in range(len(XY)) for j in range(i+1,len(XY)) if np.abs(XY[i]-XY[j]).sum()==1])
INC = np.zeros((len(XY), len(EDGES)))
INC[EDGES[:,0],np.arange(len(EDGES))] = 1
INC[EDGES[:,1],np.arange(len(EDGES))] = -1
BUDGET = 24.
ROOTS, LEAVES = [1,3], [20,22,24]


def loads(commodity, changing):
    sources, sinks = (ROOTS, LEAVES) if commodity=="water" else (LEAVES, [1,3,12])
    base = np.zeros(len(XY))
    base[sources] = 1/len(sources)
    if not changing:
        base[sinks] = -1/len(sinks)
        return base[:,None]
    demand = np.repeat(base[:,None],len(sinks),axis=1)
    demand[sinks,np.arange(len(sinks))] = -1.
    return demand


def material(g):
    return g * (BUDGET/np.sqrt(g).sum())**2


def pressures(g, demand):
    lap = (INC*g) @ INC.T
    p = np.zeros_like(demand)
    p[1:] = np.linalg.solve(lap[1:,1:],demand[1:])
    return p


def develop(initial, demand, law, dt):
    g=initial.copy()
    if law=="adaptive":
        for _ in range(round(20/dt)):
            q = g[:,None]*(INC.T@pressures(g,demand))
            g += dt*(np.mean(np.abs(q)**1.2,axis=1)-g)
            g=np.maximum(g,1e-9)
    else:
        # With fixed edge currents, minimizing loss with sum(area)=B gives area ∝ <Q²>^(1/3).
        for _ in range(80):
            q=g[:,None]*(INC.T@pressures(g,demand))
            area=np.maximum(np.mean(q*q,axis=1)**(1/3),1e-4)
            g=material(area**2)
    return material(g)


def components(g):
    graph = (np.abs(INC[:,g>0]) @ np.abs(INC[:,g>0]).T)>0
    return connected_components(csr_matrix(graph), directed=False)


def solve(g, requested):
    ncomp, groups = components(g)
    delivered = requested.copy()
    p = np.zeros_like(requested)
    lap=(INC*g)@INC.T
    for ci in range(ncomp):
        nodes=np.flatnonzero(groups==ci)
        local=requested[nodes]
        src=local.clip(min=0); sink=(-local).clip(min=0)
        balanced=np.minimum(src.sum(axis=0),sink.sum(axis=0))
        supplied=src*balanced/np.maximum(src.sum(axis=0),1e-20)
        received=sink*balanced/np.maximum(sink.sum(axis=0),1e-20)
        delivered[nodes]=supplied-received
        free=nodes[1:]
        if len(free):
            p[free]=np.linalg.solve(lap[np.ix_(free,free)],delivered[free])
    flow=g[:,None]*(INC.T@p)
    unmet=1-delivered.clip(min=0).sum(axis=0)
    return {"cycles": int((g>0).sum()-len(XY)+ncomp),
            "loss": float(np.mean(np.sum(flow*(INC.T@p),axis=0))),
            "unmet": float(max(0.,unmet.mean())),
            "kcl": float(np.max(abs(INC@flow-delivered)))}


def junctions(g):
    angles,radii=[],[]
    for node in range(len(XY)):
        incident=np.flatnonzero((INC[node]!=0)&(g>0))
        if len(incident)<3:
            continue
        for a,b in itertools.combinations(incident,2):
            va=XY[EDGES[a].sum()-node]-XY[node]
            vb=XY[EDGES[b].sum()-node]-XY[node]
            angles.append(float(np.degrees(np.arccos(np.dot(va,vb)))))
            radii.append(float((min(g[a],g[b])/max(g[a],g[b]))**.25))
    return {"pairs":len(angles),"angles_deg":sorted(set(angles)),
            "mean_radius_ratio":float(np.mean(radii)) if radii else None}


def assess(g, demand, threshold):
    active=np.where(g>=threshold*g.max(),g,0.)
    active=material(active)
    baseline=solve(active,demand)
    injuries=[]
    for edge in range(len(active)):
        damaged=active.copy()
        damaged[edge]=0
        injuries.append(solve(damaged,demand))
    return {**baseline,"material":float(np.sqrt(active).sum()),"junctions":junctions(active),
            "cut_mean_unmet":float(np.mean([r["unmet"] for r in injuries])),
            "cut_max_unmet":max(r["unmet"] for r in injuries),
            "max_kcl_including_cuts":max(r["kcl"] for r in injuries+[baseline]),
            "cuts":injuries}


def run(out):
    out.mkdir(parents=True,exist_ok=True)
    runs,arrays=[],{"xy":XY,"edges":EDGES}
    for seed in (11,29,47):
        rng=np.random.default_rng(seed)
        initial=material(np.exp(rng.normal(0,.15,len(EDGES))))
        order=np.zeros((len(XY),len(XY)))
        order[tuple(EDGES.T)] = rng.uniform(.5,1.5,len(EDGES))
        tree=minimum_spanning_tree(order+order.T).toarray()
        mask=(tree+tree.T)[tuple(EDGES.T)]>0
        extra=mask.copy()
        extra[np.flatnonzero(~mask)[0]]=True
        for commodity,changing in itertools.product(("water","sugar"),(False,True)):
            demand=loads(commodity,changing)
            designs={"tree":material(mask.astype(float)),"one_loop":material(extra.astype(float)),
                     "uniform":material(np.ones(len(EDGES))),"material_optimum":develop(initial,demand,"optimum",.1)}
            for dt in (.1,.2):
                designs[f"adaptive_{dt}"]=develop(initial,demand,"adaptive",dt)
            for name,g in designs.items():
                key=f"{seed}_{commodity}_{int(changing)}_{name}"
                arrays[key]=g
                for threshold in (.001,.0001):
                    r=assess(g,demand,threshold)
                    arrays[key+f"_cuts_{threshold}"]=np.array([[c["unmet"],c["loss"],c["cycles"],c["kcl"]] for c in r.pop("cuts")])
                    runs.append({"seed":seed,"commodity":commodity,"varying_sinks":changing,
                                 "design":name,"threshold":threshold,**r})
    np.savez_compressed(out/"networks.npz",**arrays)
    checks={"material_matched": all(abs(r["material"]-BUDGET)<1e-8 for r in runs),
            "mass_after_all_cuts":all(r["max_kcl_including_cuts"]<1e-7 for r in runs),
            "control_cycle_ranks":all(r["cycles"]=={"tree":0,"one_loop":1,"uniform":16}[r["design"]]
                                    for r in runs if r["design"] in ("tree","one_loop","uniform")),
            "damage_contrast":all(r["cut_max_unmet"]>0 for r in runs if r["design"]=="tree") and
                              all(r["cut_max_unmet"]<1e-10 for r in runs if r["design"]=="uniform")}
    save_summary(out,{"rows":runs,"checks":checks,"cuts_column_order":["unmet","loss","cycles","kcl"]},__file__)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,default=OUT)
    run(parser.parse_args().out)
