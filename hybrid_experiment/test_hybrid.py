import unittest
import numpy as np
from run import simulate,evaluate,spectral_clocks

class HybridTests(unittest.TestCase):
    def test_clock_truth_predicts_unseen_clean_envelope(self):
        t=np.arange(1200)/40;f,d=.47,.013
        phi=2*np.pi*(f*t+.5*d*t*t);y=1+.3*np.sin(phi)+.15*np.cos(2*phi)+.001*t
        train=t<20
        metrics,_=evaluate(t[train],y[train],t[~train],y[~train],(f,d),f,d)
        self.assertLess(metrics['nmse'],1e-20)
        self.assertEqual(metrics['frequency_mae'],0)
        wrong,_=evaluate(t[train],y[train],t[~train],y[~train],(.47,0),f,d)
        self.assertGreater(wrong['nmse'],.5)
    def test_static_clock_baseline(self):
        t=np.arange(800)/40;y=np.sin(2*np.pi*.5*t)
        p=spectral_clocks(t,y)
        self.assertLess(abs(p['constant'][0]-.5),.001)
        self.assertLess(abs(p['stft'][1]),.001)
    def test_gaps_do_not_invent_samples(self):
        t,iq,_,_=simulate('gaps',0)
        self.assertLess(len(t),1200);self.assertTrue(np.all(np.diff(t)>0))
        self.assertTrue(np.isfinite(iq).all());self.assertFalse(np.any((t>7)&(t<10)))

if __name__=='__main__':unittest.main()
