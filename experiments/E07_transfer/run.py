"""Score the two sealed model predictions against an independent native hydraulic calculation."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from experiments.common import save_summary
from . import predict
from .predict import OUT,N,G,C0,P0,TIMES,SOURCE,features


def reference(amplitude, rtol):
    # Liquid volume stored by isothermal compression of a gas. Positive Q flows down pressure.
    initial=np.zeros((N,N))
    initial[SOURCE]=amplitude/(P0+amplitude)
    def rhs(t, liquid):
        v=liquid.reshape(N,N)
        p=v/(1-v)
        rate=np.zeros_like(p)
        for axis in (0,1):
            potential=np.moveaxis(p,axis,0)
            flux=potential[:-1]-potential[1:]
            change=np.moveaxis(rate,axis,0)
            change[:-1]-=flux
            change[1:]+=flux
        return (G/C0)*rate.ravel()
    solution=solve_ivp(rhs,(0,TIMES[-1]),initial.ravel(),method="DOP853",rtol=rtol,atol=rtol*1e-4,t_eval=TIMES)
    if not solution.success:
        raise RuntimeError(solution.message)
    vol=solution.y.T.reshape(-1,N,N)
    return (vol/(1-vol))*(P0/amplitude),float(np.ptp(vol.sum(axis=(1,2))))


def run(out):
    record=json.loads((out/"predictions.json").read_text())
    path=out/"predictions.npz"
    rows=[]
    arrays={}
    with np.load(path) as archive:
        for amplitude in record["amplitudes_pa"]:
            truth,drift=reference(amplitude,1e-10)
            coarse,_=reference(amplitude,1e-8)
            arrays[f"native_{amplitude}"]=truth
            scores={}
            for name,data in [("M0",coarse),("M1",archive["M1"]),("M2",archive["M2"])]:
                scores[name]={"normalized_rmse":float(np.sqrt(np.mean((data-truth)**2))),
                              **features(data)}
            rows.append({"amplitude_pa":amplitude,"reference":features(truth),"scores":scores,
                         "stored_volume_drift_fraction_of_gas_volume":drift})
    np.savez_compressed(out/"reference.npz",**arrays)
    score=lambda i,m: rows[i]["scores"][m]["normalized_rmse"]
    checks={"reference_integrator":max(score(i,"M0") for i in (0,1))<1e-7,
            "storage_conserved":max(r["stored_volume_drift_fraction_of_gas_volume"] for r in rows)<1e-10}
    verdict={"small_pointwise_rmse_within_scope":score(0,"M1")<min(.02,score(0,"M2")),
             "nonlinear_pulse_increases_error":score(1,"M1")>score(0,"M1")}
    save_summary(out,{"runs":rows,"registered_predictions":verdict,"checks":checks,"target":"synthetic",
                      "predictions_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                      "external_filter_chips":{"doi":"10.1186/s13036-018-0126-3","assessed":3,
                        "independent_cutoff_targets":0,"reason":"Methods Eq. 1 computes cutoff from the step time constant."}},
                 __file__,predict.__file__)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,default=OUT)
    run(p.parse_args().out)
