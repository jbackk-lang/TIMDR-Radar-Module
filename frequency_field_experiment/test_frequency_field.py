import itertools
import unittest
import numpy as np
from frequency_field import prepare, peak, ridge, path_indices, confidence

class TestField(unittest.TestCase):
    def make(self, p, frames=None):
        f=np.arange(len(p)) if frames is None else np.asarray(frames)
        return prepare(np.sqrt(p),f*.05,f,64.,299792458./2)

    def test_single_and_accelerating(self):
        p=np.ones((40,64))*.01
        bins=20+np.arange(40)//5
        p[np.arange(40),bins]=10
        data=self.make(p)
        np.testing.assert_array_equal(ridge(*data,acceleration=10),data[1][bins])

    def test_interference_control(self):
        p=np.ones((40,64))*.01
        p[:,20]=10
        p[::2,45]=30
        data=self.make(p)
        self.assertGreater(np.mean(abs(peak(*data)+12)),1)
        np.testing.assert_array_equal(ridge(*data,acceleration=2),np.full(40,-12.))

    def test_absent_signal(self):
        data=self.make(np.zeros((10,64)))
        pred=ridge(*data,acceleration=2)
        self.assertFalse(confidence(data[0],data[1],pred)[1].any())

    def test_gap_reset(self):
        p=np.ones((10,64))*.01
        p[:5,10]=10; p[5:,50]=10
        data=self.make(p,[0,1,2,3,4,100,101,102,103,104])
        self.assertEqual(len(data[3]),2)
        np.testing.assert_array_equal(ridge(*data,acceleration=2),np.r_[np.full(5,-22),np.full(5,18)])

    def test_invalid(self):
        for t in ([0,0],[1,0],[0,np.nan]):
            with self.assertRaises(ValueError):
                prepare(np.ones((2,8)),t,[0,1],1,1)

    def test_dynamic_programming_vs_enumeration(self):
        rng=np.random.default_rng(3)
        v=rng.normal(size=(4,3)); e=rng.normal(size=(4,3)); t=np.arange(4)*.1
        def score(path):
            return sum(e[i,j] for i,j in enumerate(path))-sum(min(((v[i,path[i]]-v[i-1,path[i-1]])/.7)**2,25) for i in range(1,4))
        expected=max(itertools.product(range(3),repeat=4),key=score)
        actual=path_indices(v,e,t,.2,5)
        self.assertAlmostEqual(score(actual),score(expected))

if __name__=='__main__':
    unittest.main()
