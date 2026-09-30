"""Recompute saved metrics and check frozen protocol/code/input hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

def main():
    root=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(); parser.add_argument('--results',type=Path,default=root/'results')
    args=parser.parse_args(); r=json.loads((args.results/'results.json').read_text(encoding='utf-8'))
    frozen=json.loads((args.results/'frozen_selection.json').read_text(encoding='utf-8'))
    assert r['config']==frozen
    assert hashlib.sha256((root/'PROTOCOL.md').read_bytes()).hexdigest()==frozen['protocol_sha256']
    for name,digest in frozen['code_sha256'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
    ids={part:{Path(p['file']).stem for p in r['inputs'] if p['part']==part} for part in ('dev','eval')}
    assert not ids['dev']&ids['eval']
    for p in r['inputs']:
        assert hashlib.sha256(Path(p['file']).read_bytes()).hexdigest()==p['sha256'],p['file']
    count=0
    with np.load(args.results/'predictions.npz',allow_pickle=False) as z:
        for row in r['tracks']:
            key=row['track']; ref=z[key+'_reference']
            assert len(ref)==row['frames']
            for name,metrics in row['methods'].items():
                err=z[key+'_'+name]-ref
                assert np.isfinite(err).all()
                assert np.isclose(np.mean(abs(err)),metrics['mae'],rtol=0,atol=1e-12)
                assert np.isclose(np.sqrt(np.mean(err**2)),metrics['rmse'],rtol=0,atol=1e-12)
                count+=2
    for cls,summary in r['summary'].items():
        rows=[row for row in r['tracks'] if cls=='ALL' or row['class']==cls]
        assert len(rows)==summary['tracks']
        for name,mae in summary['mae'].items():
            assert np.isclose(np.mean([row['methods'][name]['mae'] for row in rows]),mae,rtol=0,atol=1e-12)
    result={'verified':True,'metrics_recomputed':count,'input_hashes_checked':len(r['inputs']),
            'dev_eval_ids_disjoint':True,'frozen_code_and_protocol_match':True}
    (args.results/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__': main()
