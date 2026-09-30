"""Small offline consistency pilot; reference is radar velocity, not independent truth."""
from pathlib import Path
import json, time, hashlib
import numpy as np
from scipy.ndimage import median_filter

DATA = Path('C:/Users/jback/Downloads/a/DATA/open_radar')
OUT = Path(__file__).resolve().parent
C = 299792458.

def read(part):
    for p in sorted((DATA / part).glob('*.npz')):
        with np.load(p, allow_pickle=False) as z:
            yield p, {k:z[k] for k in z.files}

def estimates(z):
    power = np.abs(z['spec'].astype(np.complex128))**2
    n = power.shape[1]
    axis = (np.arange(n)-n//2)*float(z['prf'])/n*C/(2*float(z['fc']))
    peak = axis[np.argmax(power, axis=1)]
    smooth = peak.copy()
    # Offline three-frame median, never across discontinuous frame indices.
    for ix in np.split(np.arange(len(peak)), np.flatnonzero(np.diff(z['frames']) != 1)+1):
        smooth[ix] = median_filter(peak[ix], size=3, mode='nearest')
    return peak, smooth

def main():
    start=time.perf_counter()
    # Resolve Doppler sign convention on development tracks only, freeze before eval.
    dev=[]
    for p,z in read('dev'):
        pred,_=estimates(z)
        dev.append([np.mean(np.abs(s*pred-z['velocity'])) for s in (1,-1)])
    sign=(1,-1)[int(np.argmin(np.mean(dev,axis=0)))]
    rows=[]; predictions={}; provenance=[]
    for p,z in read('eval'):
        a,b=estimates(z); ref=z['velocity']
        if not all(np.isfinite(x).all() for x in (a,b,ref)):
            raise ValueError('nonfinite track '+p.name)
        row={'track':p.stem,'class':str(z['cls']),'frames':len(ref)}
        for name,pred in [('doppler_peak',sign*a),('median3',sign*b)]:
            row[name+'_mae_m_s']=float(np.mean(np.abs(pred-ref)))
            predictions[p.stem+'_'+name]=pred
        predictions[p.stem+'_reference']=ref
        predictions[p.stem+'_timestamps']=z['ts']
        rows.append(row)
        provenance.append({'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    summary={}
    for cls in sorted(set(r['class'] for r in rows)) + ['ALL']:
        group=[r for r in rows if cls=='ALL' or r['class']==cls]
        summary[cls]={'tracks':len(group),'frames':sum(r['frames'] for r in group),
          **{name:float(np.mean([r[name+'_mae_m_s'] for r in group])) for name in ('doppler_peak','median3')}}
    result={'source':'https://github.com/openradarinitiative/open_radar_datasets',
      'license':'CC BY-NC 4.0; Gusland et al. 2021, DOI 10.1109/RadarConf2147009.2021.9455239',
      'reference':'Measured radial velocity from same radar, NOT independent ground truth',
      'protocol':'All cached eval tracks; track-macro MAE. No new split. Sign fitted on dev only. Fixed median size 3; offline, no gap bridging. No parameter search.',
      'limitations':'Median is a classical coherence control, NOT the astronomy clock and NOT evidence of TIMDR novelty. Cached windows only, not full dataset.',
      'sign':sign,'dev_tracks':len(dev),'summary':summary,'tracks':rows,'inputs':provenance,
      'elapsed_seconds':time.perf_counter()-start}
    np.savez_compressed(OUT/'predictions.npz',**predictions)
    (OUT/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('sign','dev_tracks','summary','elapsed_seconds')},indent=2))

if __name__=='__main__':
    main()
