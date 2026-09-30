"""Controlled synthetic pilot: radar echo envelope with an astronomical clock.

Run using Python with numpy, scipy and matplotlib. No paid services or downloads.
"""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.signal import lombscargle,stft
from astronomy_clock import fit_clock,design

ROOT=Path(__file__).resolve().parent
CASES=('steady','accelerating','decelerating','gaps','symmetric','noise')

def simulate(case,seed):
    if case not in CASES:raise ValueError('Unknown case')
    rng=np.random.default_rng(7000+seed)
    t=np.arange(1200)/40
    f0=.48+rng.uniform(-.035,.035);drift=.014+rng.uniform(-.002,.002)
    if case=='steady':drift=0.
    if case=='decelerating':f0=.72+rng.uniform(-.035,.035);drift=-.009
    phase=2*np.pi*(f0*t+.5*drift*t*t)
    initial=rng.uniform(-np.pi,np.pi)
    envelope=1+.35*np.sin(phase+initial)+.14*np.cos(2*phase+.7)
    if case=='symmetric':envelope=1+.02*np.sin(phase+initial)+.4*np.cos(2*phase+.7)
    # Stylized scattering: bulk phase + periodic radial micromotion phase.
    iq=envelope*np.exp(1j*(2*np.pi*5*t+1.1*np.sin(phase+initial)))
    iq+=.13*(rng.normal(size=len(t))+1j*rng.normal(size=len(t)))
    if case=='noise':iq=.5*(rng.normal(size=len(t))+1j*rng.normal(size=len(t)))
    keep=np.ones(len(t),dtype=bool)
    if case=='gaps':keep=~((t>7)&(t<10));keep &= rng.random(len(t))>.18
    return t[keep],iq[keep],f0,drift

def spectral_clocks(t,y):
    frequency=np.linspace(.15,1.6,4096)
    power=lombscargle(t,y-y.mean(),2*np.pi*frequency,normalize=True)
    fixed=float(frequency[np.argmax(power)])
    regular=np.arange(0,t[-1]+1e-8,1/40)
    filled=np.interp(regular,t,y)
    f,ts,z=stft(filled-filled.mean(),fs=40,nperseg=256,noverlap=224,nfft=2048,boundary=None,padded=False)
    mask=(f>=.15)&(f<=1.6);ridge=f[mask][np.argmax(abs(z[mask]),axis=0)]
    slope,intercept=np.polyfit(ts,ridge,1)
    # Same supplied f0/drift bounds as the astronomical model.
    intercept=float(np.clip(intercept,.3,.85));slope=float(np.clip(slope,-.015,.025))
    return dict(constant=(fixed,0.),stft=(intercept,slope))

def evaluate(t,y,test_t,test_y,params,f0,drift):
    a=design(t,*params,2);coef=np.linalg.lstsq(a,y,rcond=None)[0]
    # design normalizes its trend by window length, so construct the test
    # trend in the training coordinate system to avoid changing its meaning.
    b=design(test_t,*params,2);b[:,1]=test_t/np.ptp(t)
    pred=b@coef
    return dict(nmse=float(np.mean((test_y-pred)**2)/max(np.var(test_y),1e-12)),
                frequency_mae=float(np.mean(abs(params[0]+params[1]*test_t-(f0+drift*test_t))))) ,pred

def run():
    out=ROOT/'results';out.mkdir(exist_ok=True);rows=[];started=time.perf_counter()
    protocol_hash=hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest()
    for case in CASES:
        for seed in range(5):
            path=out/f'{case}_{seed}.json'
            if path.exists():
                old=json.loads(path.read_text());assert old['protocol_sha256']==protocol_hash
                rows.extend(old['rows']);continue
            t,iq,f0,drift=simulate(case,seed);y=abs(iq);training=t<20
            tx,yy=t[training],y[training];te,ye=t[~training],y[~training]
            assert tx.max()<te.min()
            # No true parameters are passed into either estimation routine.
            a=time.perf_counter();params=spectral_clocks(tx,yy);spectral_seconds=time.perf_counter()-a
            a=time.perf_counter();report,_=fit_clock(tx,yy,(.3,.85),(-.015,.025),seed=91+seed*2)
            clock_seconds=time.perf_counter()-a
            params['astronomy']=(report['frequency_initial']-report['frequency_drift']*report['time_origin'],report['frequency_drift'])
            if case!='noise':params['oracle']=(f0,drift)
            current=[];predictions={}
            for arm,p in params.items():
                metrics,pred=evaluate(tx,yy,te,ye,p,f0,drift)
                if case=='noise':metrics['frequency_mae']=None
                row=dict(case=case,seed=seed,arm=arm,**metrics,f0=p[0],drift=p[1])
                if arm=='astronomy':row.update(status=report['status'],reasons=report['reasons'],seconds=clock_seconds)
                current.append(row);predictions[arm]=pred
            np.savez_compressed(out/f'{case}_{seed}.npz',time=t,iq=iq,test_time=te,test_envelope=ye,**predictions)
            data=dict(protocol_sha256=protocol_hash,true_f0=f0 if case!='noise' else None,true_drift=drift if case!='noise' else None,clock_report=report,spectral_seconds=spectral_seconds,rows=current)
            path.write_text(json.dumps(data,indent=2));rows.extend(current)
            print(case,seed,'clock',report['status'],'NMSE', {r['arm']:round(r['nmse'],3) for r in current},flush=True)
    (out/'scores.json').write_text(json.dumps(rows,indent=2))
    summary={}
    for case in CASES:
        summary[case]={}
        for arm in ('constant','stft','astronomy','oracle'):
            selected=[r for r in rows if r['case']==case and r['arm']==arm]
            if not selected:continue
            summary[case][arm]={metric:float(np.mean([r[metric] for r in selected])) if selected[0][metric] is not None else None for metric in ('nmse','frequency_mae')}
        summary[case]['accepted']=sum(r.get('status')=='accepted_model' for r in rows if r['case']==case and r['arm']=='astronomy')
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    (out/'audit.json').write_text(json.dumps(dict(protocol_sha256=protocol_hash,code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),seconds_this_invocation=time.perf_counter()-started,scope='synthetic envelope only; no physical radar validation; true test withheld from estimators'),indent=2))
    make_report(summary)

def make_report(summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    labels={'steady':'Stały obrót','accelerating':'Przyspieszanie','decelerating':'Zwalnianie','gaps':'Luki','symmetric':'Dwie podobne powierzchnie','noise':'Sam szum'}
    arms={'constant':'Stała częstotliwość','stft':'STFT + dryf','astronomy':'Zegar z astronomii','oracle':'Prawdziwy zegar'}
    lines=['# Radar + zegar astronomiczny — wynik pilota','',
           'Wyłącznie symulacja obwiedni echa I/Q. Pięć ziaren na scenariusz. Estymacja na pierwszych 20 s, ocena na ostatnich 10 s. NMSE: mniej = lepiej; 1 odpowiada błędowi równemu wariancji testu. Nie jest to wynik śledzenia trajektorii ani fuzja kamery i radaru.','',
           '| Scenariusz | Stała częstotliwość | STFT + dryf | Zegar astronomiczny | Prawdziwy zegar | Akceptacje zegara |',
           '|---|---:|---:|---:|---:|---:|']
    for case in CASES:
        cells=[f"{summary[case][arm]['nmse']:.3f}" if arm in summary[case] else '—' for arm in arms]
        lines.append('| '+labels[case]+' | '+' | '.join(cells)+f" | {summary[case]['accepted']}/5 |")
    lines+=['','Wszystkie dopasowania, także oznaczone jako niewiarygodne, pozostają w tabeli. Nie wolno używać samego statusu accepted_model jako potwierdzenia fizycznej prędkości obrotu. W przypadku symetrii zegar może śledzić dwukrotną częstość błysków. Dla szumu brak fizycznej częstotliwości i punktu odniesienia oracle.','',
            'Generator ma liniowy dryf i stałe harmoniczne, zgodne z rodziną modelu astronomicznego. Wynik może wykazać przydatność tego założenia w kontrolowanym przykładzie, ale nie przewagę na rzeczywistym radarze. STFT jest jednym ustalonym punktem odniesienia, nie najlepszym możliwym estymatorem.','',
            'Kod estymatora skopiowano bez zmian z TIMDR-orbital-tracker/timdr_orbit/rotation_clock.py; pochodzenie i SHA-256: PROVENANCE.json. Sygnały I/Q, predykcje, parametry, przyczyny odrzucenia i metryki zapisano w results/. Nie zmieniono starego trackera ani modelu RCS kuli.']
    (ROOT/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    fig,axs=plt.subplots(1,2,figsize=(12,4))
    shown=CASES[:4];x=np.arange(len(shown))
    for i,arm in enumerate(arms):
        axs[0].bar(x+(i-1.5)*.2,[summary[c][arm]['nmse'] for c in shown],width=.2,label=arms[arm])
        axs[1].bar(x+(i-1.5)*.2,[summary[c][arm]['frequency_mae'] for c in shown],width=.2)
    for ax in axs:ax.set_xticks(x,[labels[c] for c in shown]);ax.grid(axis='y',alpha=.2)
    axs[0].set_ylabel('NMSE prognozy obwiedni (mniej = lepiej)');axs[1].set_ylabel('MAE częstotliwości obrotu [Hz]')
    axs[0].legend(fontsize=8);fig.suptitle('SYNTETYCZNY PILOT · niewidziane ostatnie 10 sekund · 5 ziaren')
    fig.tight_layout();fig.savefig(ROOT/'comparison.png',dpi=160);plt.close(fig)

if __name__=='__main__':run()
