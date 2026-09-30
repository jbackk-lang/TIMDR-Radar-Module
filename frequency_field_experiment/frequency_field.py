"""Classical Doppler ridge tracking; experimental TIMDR component, offline.

No label, range or class input. Spectrum must be fftshift-centred complex Doppler
data with time in seconds. Returns radial m/s, not total speed or spin rate.
"""
import numpy as np
from scipy.ndimage import maximum_filter1d

C = 299792458.0

def prepare(spec, times_s, frames, prf, fc):
    spec = np.asarray(spec)
    t = np.asarray(times_s, dtype=float)
    frames = np.asarray(frames)
    if spec.ndim != 2 or min(spec.shape) < 1 or spec.shape[1] < 3:
        raise ValueError('spec must be nonempty (frames, Doppler bins>=3)')
    if t.shape != (len(spec),) or frames.shape != t.shape:
        raise ValueError('time/frame shape mismatch')
    if not np.isfinite(spec).all() or not np.isfinite(t).all() or not np.isfinite(frames).all():
        raise ValueError('nonfinite data')
    if np.any(np.diff(t) <= 0) or np.any(np.diff(frames) <= 0):
        raise ValueError('times and frame indices must increase')
    if not np.isfinite(prf) or not np.isfinite(fc) or prf <= 0 or fc <= 0:
        raise ValueError('prf and fc must be finite positive Hz')
    power = np.abs(spec.astype(np.complex128))**2
    if not np.isfinite(power).all():
        raise ValueError('power overflow')
    n = spec.shape[1]
    axis = (np.arange(n)-n//2)*prf/n*C/(2*fc)
    dt = np.diff(t)
    breaks = (np.diff(frames) != 1)
    if len(dt):
        breaks |= dt > 1.5*np.median(dt)
    chunks = np.split(np.arange(len(t)), np.flatnonzero(breaks)+1)
    return power, axis, t, chunks

def peak(power, axis, times, chunks):
    return axis[np.argmax(power, axis=1)]

def exponential(power, axis, times, chunks, alpha):
    if not 0 < alpha <= 1:
        raise ValueError('alpha outside (0,1]')
    out = peak(power, axis, times, chunks)
    for ix in chunks:
        for k in ix[1:]:
            out[k] = alpha*out[k]+(1-alpha)*out[k-1]
    return out

def path_indices(velocities, emissions, times, bin_width, acceleration):
    """Maximise sum log emissions - capped transition cost, exact over candidates."""
    if acceleration <= 0 or not np.isfinite(acceleration):
        raise ValueError('acceleration must be finite and positive')
    score = emissions[0].copy()
    parents = np.zeros(velocities.shape, dtype=int)
    for i in range(1,len(times)):
        scale = bin_width+acceleration*(times[i]-times[i-1])
        cost = np.minimum(((velocities[i,:,None]-velocities[i-1,None,:])/scale)**2,25.)
        choices = score[None,:]-cost
        parents[i] = np.argmax(choices,axis=1)
        score = emissions[i]+np.max(choices,axis=1)
        score -= np.max(score)
    path = np.empty(len(times),dtype=int)
    path[-1] = np.argmax(score)
    for i in range(len(times)-1,0,-1):
        path[i-1] = parents[i,path[i]]
    return path

def ridge(power, axis, times, chunks, acceleration, candidates=16):
    if candidates < 1:
        raise ValueError('candidates must be positive')
    k = min(candidates,power.shape[1])
    local = power == maximum_filter1d(power,size=3,axis=1,mode='constant',cval=-np.inf)
    ranked = np.where(local,power,-np.inf)
    # Stable ordering resolves equal-power candidates reproducibly.
    indices = np.argsort(-ranked,axis=1,kind='stable')[:,:k]
    vals = np.take_along_axis(power,indices,axis=1)
    valid = np.take_along_axis(local,indices,axis=1)
    emissions = np.log(np.maximum(vals,1e-300)/np.maximum(power.max(1,keepdims=True),1e-300))
    emissions[~valid] = -np.inf
    velocities = axis[indices]
    chosen = np.empty(len(power),dtype=int)
    for ix in chunks:
        path = path_indices(velocities[ix],emissions[ix],times[ix],abs(axis[1]-axis[0]),acceleration)
        chosen[ix] = indices[ix,path]
    return axis[chosen]

def confidence(power, axis, predicted):
    """Uncalibrated prominence diagnostic; never removes scored predictions."""
    ix = np.clip(np.rint((predicted-axis[0])/(axis[1]-axis[0])).astype(int),0,len(axis)-1)
    ratio = power[np.arange(len(power)),ix]/np.maximum(np.median(power,axis=1),1e-300)
    db = 10*np.log10(np.maximum(ratio,1e-300))
    return db, db >= 13
