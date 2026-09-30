"""Photometric clock for approximately constant angular acceleration.

CSV input: time,flux. Frequency is in cycles / time unit. A physical rotation
angle requires an independently justified harmonic interpretation.
Requires numpy and scipy. Run --help for usage.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.optimize import differential_evolution, minimize
from scipy.signal import stft


def design(t, f0, drift, harmonics):
    phase = 2 * np.pi * (f0 * t + .5 * drift * t*t)
    u = t / max(np.ptp(t), 1e-12)
    return np.column_stack([np.ones(len(t)), u] +
        [v for h in range(1, harmonics+1)
         for v in (np.cos(h*phase), np.sin(h*phase))])


def fit_clock(time, flux, f_bounds, drift_bounds, harmonics=2, seed=91):
    t, y = np.asarray(time, float), np.asarray(flux, float)
    valid = np.isfinite(t) & np.isfinite(y)
    t, y = t[valid], y[valid]
    order = np.argsort(t)
    t, y = t[order], y[order]
    if len(t) < 50 or np.any(np.diff(t) <= 0):
        raise ValueError('Need >=50 finite samples with distinct timestamps.')
    origin = float(t[0]); t = t-origin
    if np.std(y) == 0 or not 1 <= harmonics <= 4:
        raise ValueError('Nonconstant flux and 1..4 harmonics required.')
    if not 0 < f_bounds[0] < f_bounds[1] or not drift_bounds[0] < drift_bounds[1]:
        raise ValueError('Invalid search bounds.')
    scale = np.std(y); y = (y-np.mean(y))/scale
    # Fit an explicit chirp model, not independently selected spectral peaks.
    # Uniformly distributed samples reduce optimization cost; final refinement
    # and all quality diagnostics use every available sample.
    ix = np.unique(np.linspace(0, len(t)-1, min(600,len(t))).astype(int))
    def loss(p, tx, yy):
        if min(p[0], p[0]+p[1]*t[-1]) <= 0:
            return 1e6
        a = design(tx, *p, harmonics)
        residual = yy-a@np.linalg.lstsq(a, yy, rcond=None)[0]
        return float(np.mean(residual**2))
    bounds = [f_bounds, drift_bounds]
    candidates = []
    for s in (seed, seed+1):
        opt = differential_evolution(lambda p: loss(p,t[ix],y[ix]), bounds,
            seed=s, popsize=18, maxiter=220, tol=1e-8, polish=True)
        refined = minimize(lambda p: loss(p,t,y), opt.x, method='Nelder-Mead',
            bounds=bounds, options={'maxiter':600,'xatol':1e-10,'fatol':1e-10})
        candidates.append(refined)
    best = min(candidates, key=lambda r:r.fun)
    # Prefer the observed photometric period when the putative fundamental
    # is absent. This convention cannot identify the physical rotation period.
    canonicalized = False
    if harmonics == 2:
        coeff = np.linalg.lstsq(design(t,*best.x,harmonics),y,rcond=None)[0]
        doubled = 2*best.x
        if (np.hypot(*coeff[2:4]) < .2*np.hypot(*coeff[4:6]) and
                all(lo <= v <= hi for v,(lo,hi) in zip(doubled,bounds))):
            trial=minimize(lambda p:loss(p,t,y),doubled,method='Nelder-Mead',
                bounds=bounds,options={'maxiter':600,'xatol':1e-10,'fatol':1e-10})
            if trial.fun <= best.fun + .01:
                best=trial
                canonicalized=True
    f0, drift = best.x
    a = design(t,f0,drift,harmonics)
    coef = np.linalg.lstsq(a,y,rcond=None)[0]
    residual = y-a@coef
    trend = np.column_stack([np.ones(len(t)), t/t[-1]])
    null_res = y-trend@np.linalg.lstsq(trend,y,rcond=None)[0]
    gain = 1-np.sum(residual**2)/max(np.sum(null_res**2),1e-12)
    # Quality gates are explicit engineering defaults, not calibrated probabilities.
    window_edges = np.linspace(0,t[-1],7)
    local_gain=[]
    for left,right in zip(window_edges[:-1],window_edges[1:]):
        m=(t>=left)&(t<=right)
        if m.sum()>=12:
            local_gain.append(float(1-np.mean(residual[m]**2)/max(np.var(y[m]),1e-12)))
    at_boundary = any(min(abs(p-lo),abs(p-hi))/(hi-lo)<.01
                      for p,(lo,hi) in zip(best.x,bounds))
    reasons=[]
    if gain < .45: reasons.append('low_explained_variation')
    if not local_gain or min(local_gain)<.15: reasons.append('local_signal_loss_or_model_mismatch')
    if at_boundary: reasons.append('search_boundary')
    if abs(candidates[0].fun-candidates[1].fun)>.02: reasons.append('optimization_disagreement')
    result={'status':'accepted_model' if not reasons else 'unreliable',
        'reasons':reasons,'time_origin':origin,'frequency_initial':float(f0),
        'frequency_drift':float(drift),'explained_variation':float(gain),
        'local_explained_variation':local_gain,'harmonics':harmonics,
        'frequency_bounds':list(f_bounds),'drift_bounds':list(drift_bounds),
        'photometric_period_canonicalized':canonicalized,
        'physical_rotation_identified':False,
        'scope':'constant frequency drift; fixed harmonic amplitudes; phase relative to first sample',
        'warning':'Photometric periodicity is not uniquely the physical rotation. Bounds are prior information.'}
    frequency=f0+drift*t
    angle=2*np.pi*(f0*t+.5*drift*t*t)
    return result, np.column_stack([t+origin,frequency,angle])


def benchmark():
    rows=[]
    t=np.linspace(0,50,2000)
    for case in ('accelerating','decelerating','harmonic','gaps','dropout','noise'):
        for seed in range(5):
            rng=np.random.default_rng(seed)
            f0,d=(.7,-.006) if case=='decelerating' else (.5,.02)
            phase=2*np.pi*(f0*t+.5*d*t*t)
            clean=np.sin(phase+.4)
            if case=='harmonic': clean=.45*clean+np.sin(2*phase+.8)
            if case=='dropout': clean=clean*((t<15)|(t>35))
            y=clean+.3*rng.normal(size=len(t))
            if case=='noise': y=rng.normal(size=len(t))
            mask=np.ones(len(t),bool)
            if case=='gaps': mask=((t<18)|(t>23))&(rng.random(len(t))>.2)
            report,clock=fit_clock(t[mask],y[mask],(.35,.8),(-.01,.03))
            tt=t[mask]
            row={'case':case,'seed':seed,'status':report['status'],'reasons':report['reasons']}
            if case!='noise':
                row['frequency_mae']=float(np.mean(abs(clock[:,1]-(f0+d*tt))))
                row['relative_phase_max_cycles']=float(np.max(abs(clock[:,2]/(2*np.pi)-(f0*tt+.5*d*tt*tt))))
            if case!='gaps':
                f,ts,z=stft(y,1/(t[1]-t[0]),nperseg=128,noverlap=112)
                m=(ts>=4)&(ts<=46)
                row['original_stft_frequency_mae']=float(np.mean(abs(f[np.argmax(abs(z),axis=0)][m]-(f0+d*ts[m]))))
            rows.append(row)
    return {'notice':'Synthetic benchmark, five seeds per case. Search bounds supplied explicitly; no real-data validation.', 'runs':rows}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--csv',type=Path)
    p.add_argument('--f-bounds',type=float,nargs=2)
    p.add_argument('--drift-bounds',type=float,nargs=2)
    p.add_argument('--harmonics',type=int,default=2)
    p.add_argument('--out',type=Path,default=Path('clock_result'))
    p.add_argument('--benchmark',action='store_true')
    args=p.parse_args()
    if args.benchmark:
        result=benchmark()
    else:
        if args.csv is None or args.f_bounds is None or args.drift_bounds is None:
            p.error('--csv, --f-bounds and --drift-bounds are required')
        data=np.genfromtxt(args.csv,delimiter=',',names=True)
        result,clock=fit_clock(data['time'],data['flux'],args.f_bounds,args.drift_bounds,args.harmonics)
        np.savetxt(args.out.with_suffix('.csv'),clock,delimiter=',',
            header='time,frequency,relative_photometric_angle_radians',comments='')
    args.out.with_suffix('.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
