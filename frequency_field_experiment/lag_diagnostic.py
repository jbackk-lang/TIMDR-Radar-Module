"""Post-hoc UAV lag hypothesis, dev-only choice. Not a GPS-delay measurement.

Frozen after main results: +/- .2 seconds in .05-second steps. Same interior
frames for every lag. Compare spectrum prediction at t with reference at t+lag.
Positive lag means later reference better matches current spectrum estimate.
Only UAV dev labels select lag; report eval without further adjustment.
"""
import json
from pathlib import Path
import numpy as np
from benchmark import tracks, dump
from frequency_field import peak, ridge

ROOT=Path(__file__).resolve().parent

def errors(data,part,sign,acceleration):
    rows=[]
    lags=np.arange(-4,5)*.05
    for p,z,d,ref,_ in tracks(data,part):
        if str(z['cls'])!='uav': continue
        methods={'peak':sign*peak(*d),'ridge':sign*ridge(*d,acceleration=acceleration)}
        per={m:[[] for _ in lags] for m in methods}
        count=0
        for ix in d[3]:
            t=d[2][ix]
            inside=ix[(t>=t[0]+.2)&(t<=t[-1]-.2)]
            count+=len(inside)
            if not len(inside): continue
            for j,lag in enumerate(lags):
                aligned=np.interp(d[2][inside]+lag,t,ref[ix])
                for m,pred in methods.items(): per[m][j].extend(abs(pred[inside]-aligned).tolist())
        if count:
            rows.append({'track':p.stem,'frames':count,'mae':{m:[float(np.mean(v)) for v in vv] for m,vv in per.items()}})
    return rows

def main():
    data=Path('C:/Users/jback/Downloads/a/DATA/open_radar')
    config=json.loads((ROOT/'results/frozen_selection.json').read_text())
    lags=np.arange(-4,5)*.05
    dev=errors(data,'dev',config['sign'],config['selection']['ridge']['parameter'])
    devcurve=np.mean([r['mae']['ridge'] for r in dev],axis=0)
    best=int(np.argmin(devcurve))
    dump(ROOT/'results/lag_frozen.json',{'lag_seconds':float(lags[best]),'dev_mae':devcurve.tolist(),'lags_seconds':lags.tolist(),
      'hypothesis':'Post-hoc temporal-offset diagnostic, NOT GPS measurement; fixed +/-0.2s; identical interior frames across lags.'})
    evaluation=errors(data,'eval',config['sign'],config['selection']['ridge']['parameter'])
    result={'selected_lag_seconds':float(lags[best]),'dev_tracks':len(dev),'eval_tracks':len(evaluation),
      'eval_interior_frames':sum(r['frames'] for r in evaluation),'reference':'Same radar, no independent GPS',
      'methods':{m:{'zero_lag_mae':float(np.mean([r['mae'][m][4] for r in evaluation])),
                   'dev_selected_lag_mae':float(np.mean([r['mae'][m][best] for r in evaluation]))} for m in ('peak','ridge')},
      'dev':dev,'eval':evaluation}
    dump(ROOT/'results/lag_diagnostic.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('dev','eval')},indent=2))

if __name__=='__main__': main()
