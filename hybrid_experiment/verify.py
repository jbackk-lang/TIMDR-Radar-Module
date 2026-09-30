"""Recompute all saved forecast metrics without running optimizers again."""
import hashlib,json
from pathlib import Path
import numpy as np
from run import evaluate,CASES

root=Path(__file__).resolve().parent
provenance=json.loads((root/'PROVENANCE.json').read_text())
assert hashlib.sha256((root/'astronomy_clock.py').read_bytes()).hexdigest()==provenance['sha256']
protocol=hashlib.sha256((root/'PROTOCOL.md').read_bytes()).hexdigest()
allrows=json.loads((root/'results/scores.json').read_text());count=0
for case in CASES:
    for seed in range(5):
        saved=json.loads((root/f'results/{case}_{seed}.json').read_text())
        assert saved['protocol_sha256']==protocol
        a=np.load(root/f'results/{case}_{seed}.npz');t=a['time'];y=abs(a['iq']);train=t<20
        assert t[train].max()<a['test_time'].min()
        np.testing.assert_allclose(t[~train],a['test_time'])
        for row in saved['rows']:
            assert row in allrows
            metrics,pred=evaluate(t[train],y[train],a['test_time'],a['test_envelope'],(row['f0'],row['drift']),saved['true_f0'] or 0,saved['true_drift'] or 0)
            np.testing.assert_allclose(pred,a[row['arm']],rtol=1e-12,atol=1e-12)
            assert abs(metrics['nmse']-row['nmse'])<1e-10
            if row['frequency_mae'] is not None:assert abs(metrics['frequency_mae']-row['frequency_mae'])<1e-10
            count+=1
assert count==115==len(allrows)
summary=json.loads((root/'results/summary.json').read_text())
for case in CASES:
    for arm in ('constant','stft','astronomy','oracle'):
        rows=[r for r in allrows if r['case']==case and r['arm']==arm]
        if not rows:continue
        assert abs(np.mean([r['nmse'] for r in rows])-summary[case][arm]['nmse'])<1e-12
report=dict(status='passed',trials=30,predictions_verified=count,source_hash_verified=True,split_verified=True,protocol_sha256=protocol)
(root/'results/verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
