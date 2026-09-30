"""Reproducible dev-only selection and real-radar eval. See PROTOCOL.md."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from scipy.stats import mannwhitneyu
from frequency_field import prepare, peak, exponential, ridge, confidence

ROOT=Path(__file__).resolve().parent
GRID={'exponential':[.2,.5,.8],'ridge':[2.,10.,50.]}

def dump(path,obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')

def tracks(data,part):
    files=sorted((data/part).glob('*.npz'))
    if not files:
        raise ValueError('No input tracks: '+str(data/part))
    for p in files:
        with np.load(p,allow_pickle=False) as z:
            obj={k:z[k] for k in z.files}
        t=(obj['ts']-obj['ts'][0])/1000.
        t0=time.perf_counter()
        prepared=prepare(obj['spec'],t,obj['frames'],float(obj['prf']),float(obj['fc']))
        prep_seconds=time.perf_counter()-t0
        ref=np.asarray(obj['velocity'],dtype=float)
        if ref.shape != t.shape or not np.isfinite(ref).all():
            raise ValueError('Invalid reference '+p.name)
        yield p,obj,prepared,ref,prep_seconds

def predict(name,d,param):
    if name=='peak': return peak(*d)
    if name=='exponential': return exponential(*d,alpha=param)
    return ridge(*d,acceleration=param)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',type=Path,default=Path('C:/Users/jback/Downloads/a/DATA/open_radar'))
    parser.add_argument('--out',type=Path,default=ROOT/'results')
    args=parser.parse_args(); out=args.out; out.mkdir(parents=True,exist_ok=True)
    if (out/'results.json').exists():
        raise SystemExit('Results already exist; use a new --out directory to preserve the original run.')
    start=time.perf_counter()
    dev=[]; inputs=[]
    for n,(p,z,d,ref,_) in enumerate(tracks(args.data,'dev'),1):
        pp=peak(*d)
        row={'track':p.stem,'sign_errors':[float(np.mean(abs(s*pp-ref))) for s in (1,-1)],'models':{}}
        for method,grid in GRID.items():
            for param in grid:
                pp=predict(method,d,param)
                row['models'][f'{method}:{param}']=[float(np.mean(abs(s*pp-ref))) for s in (1,-1)]
        dev.append(row)
        inputs.append({'part':'dev','file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        if n%50==0: print('dev tracks',n,flush=True)
    si=int(np.argmin(np.mean([r['sign_errors'] for r in dev],axis=0)))
    sign=(1,-1)[si]
    selection={}
    for method,grid in GRID.items():
        scores=[float(np.mean([r['models'][f'{method}:{param}'][si] for r in dev])) for param in grid]
        selection[method]={'parameter':grid[int(np.argmin(scores))],'dev_mae_grid':dict(zip(map(str,grid),scores))}
    config={'sign':sign,'selection':selection,'dev_tracks':len(dev),
      'protocol_sha256':hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest(),
      'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'frequency_field.py',ROOT/'benchmark.py')}}
    # Persist the choice BEFORE loading any eval reference.
    dump(out/'frozen_selection.json',config); dump(out/'dev_scores.json',dev)
    print('FROZEN',json.dumps(config['selection']),flush=True)
    methods={'peak':None,**{m:s['parameter'] for m,s in selection.items()}}
    rows=[]; saved={}; rng=np.random.default_rng(20260930)
    for n,(p,z,d,ref,prep_time) in enumerate(tracks(args.data,'eval'),1):
        row={'track':p.stem,'class':str(z['cls']),'frames':len(ref),'prepare_seconds':prep_time,'methods':{}}
        for name,param in methods.items():
            predict(name,d,param) # warmup
            elapsed=[]
            for _ in range(3):
                before=time.perf_counter(); pred=predict(name,d,param); elapsed.append(time.perf_counter()-before)
            pred=sign*pred
            saved[p.stem+'_'+name]=pred
            row['methods'][name]={'mae':float(np.mean(abs(pred-ref))),'rmse':float(np.sqrt(np.mean((pred-ref)**2))),
              'seconds':float(np.median(elapsed)),'repeats_seconds':elapsed}
            if name=='ridge':
                db,ok=confidence(d[0],d[1],sign*pred)
                row['ridge_high_prominence_fraction']=float(np.mean(ok))
                saved[p.stem+'_ridge_prominence_db']=db
        perm=np.arange(len(ref))
        for ix in d[3]: perm[ix]=rng.permutation(ix)
        shuffled=(d[0][perm],d[1],d[2],d[3])
        shuffled_pred=sign*ridge(*shuffled,acceleration=methods['ridge'])
        restored=np.empty_like(shuffled_pred); restored[perm]=shuffled_pred
        row['methods']['shuffled_ridge']={'mae':float(np.mean(abs(restored-ref))),'rmse':float(np.sqrt(np.mean((restored-ref)**2)))}
        saved[p.stem+'_shuffled_ridge']=restored
        saved[p.stem+'_reference']=ref
        saved[p.stem+'_time_seconds']=d[2]
        saved[p.stem+'_frames']=z['frames']
        rows.append(row)
        inputs.append({'part':'eval','file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        if n%40==0: print('eval tracks',n,flush=True)
    summary={}
    names=list(methods)+['shuffled_ridge']
    for cls in sorted({r['class'] for r in rows})+['ALL']:
        rr=[r for r in rows if cls=='ALL' or r['class']==cls]
        summary[cls]={'tracks':len(rr),'frames':sum(r['frames'] for r in rr),
          'mae':{m:float(np.mean([r['methods'][m]['mae'] for r in rr])) for m in names},
          'mean_track_rmse':{m:float(np.mean([r['methods'][m]['rmse'] for r in rr])) for m in names}}
    base=np.array([r['methods']['peak']['mae'] for r in rows])
    bootstrap=np.random.default_rng(20260930).integers(0,len(rows),(2000,len(rows)))
    comparisons={}
    for name in names[1:]:
        alt=np.array([r['methods'][name]['mae'] for r in rows]); diff=base-alt
        u,pval=mannwhitneyu(base,alt,alternative='two-sided')
        comparisons[name]={'mean_improvement_m_s':float(diff.mean()),
          'bootstrap95':np.quantile(diff[bootstrap].mean(1),[.025,.975]).tolist(),
          'tracks_better':int(np.sum(diff>0)),'tracks_worse':int(np.sum(diff<0)),
          'mann_whitney_U':float(u),'p_bonferroni_descriptive':min(1.,float(pval)*3),
          'rank_biserial_descriptive':float(2*u/len(rows)**2-1)}
    timing={name:sum(r['methods'][name]['seconds'] for r in rows) for name in methods}
    result={'source':'https://github.com/openradarinitiative/open_radar_datasets',
      'reference':'Same-radar measured radial velocity, NOT independent truth',
      'scope':'Exploratory frequency-field prototype; not astronomy-clock validation',
      'config':config,'summary':summary,'comparisons_vs_peak':comparisons,
      'prediction_seconds_sum_of_track_medians':timing,'prepare_seconds':sum(r['prepare_seconds'] for r in rows),
      'elapsed_seconds':time.perf_counter()-start,'tracks':rows,'inputs':inputs}
    np.savez_compressed(out/'predictions.npz',**saved)
    dump(out/'results.json',result)
    print(json.dumps({k:result[k] for k in ('summary','comparisons_vs_peak','prediction_seconds_sum_of_track_medians','elapsed_seconds')},indent=2),flush=True)

if __name__=='__main__': main()
