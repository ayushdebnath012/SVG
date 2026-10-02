import copy,json,math,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cad_functional_sizing as s

class FunctionalSizingTests(unittest.TestCase):
    def test_batch_matches_scalar_assembly_multiple_loads(self):
        t=s.make_task(0)
        designs=np.random.default_rng(4021).integers(0,4,(5,8))
        batch=s.evaluate(t,designs)
        for i,d in enumerate(designs):
            m=copy.deepcopy(t['model'])
            for v,k in zip(m['members'],d):v['h_mm']=t['catalog_h_mm'][k]
            checks=[]
            for loads in t['load_cases']:
                m['loads']=loads
                for node in m['nodes']:
                    m['probe']=node;checks.append(s.fem.solve(m,subdivisions=2))
            for k,source in [('ux_mm','ux_mm'),('uy_mm','uy_mm'),('stress_mpa','peak_stress_mpa')]:
                self.assertAlmostEqual(batch[k][i],max(abs(r[source]) for r in checks),places=7)

    def test_axial_compression_euler_and_tension(self):
        t=s.make_task(0);t['model']={'nodes':{'A':[0,0],'B':[0,1000]},'supports':{'A':[0,1,2]},'members':[{'id':'C','a':'A','b':'B','E':200000.,'b_mm':80.}]}
        t['load_cases']=[{'B':[0,-100000,0]}]
        r=s.rows(t,[[0]])[0];I=80*120**3/12
        self.assertAlmostEqual(r['buckling_utilization'],2*100000/(math.pi**2*200000*I/1000**2))
        self.assertAlmostEqual(r['uy_mm'],100000*1000/(200000*80*120))
        t['load_cases']=[{'B':[0,100000,0]}]
        self.assertEqual(s.rows(t,[[0]])[0]['buckling_utilization'],0.)

    def test_svg_readback_detects_section_mismatch(self):
        t=s.make_task(0);d=[0,1,2,3,0,1,2,3];svg=s.drawing(t,d)
        self.assertEqual(s.read_drawing(t,svg),d)
        with self.assertRaises(ValueError):s.read_drawing(t,svg.replace('height="24.0"','height="25.0"',1))

    def test_frozen_oracles_are_feasible(self):
        ts=json.loads((s.DATA/'tasks.json').read_text())['tasks']
        for t in ts:
            self.assertTrue(s.rows(t,[t['oracle']['best']['design']])[0]['all_constraints_pass'])
            self.assertEqual(t['oracle']['enumerated'],65536)

    def test_catalog_indices_cannot_silently_round(self):
        with self.assertRaises(ValueError):s.evaluate(s.make_task(0),[[0.1]*8])

if __name__=='__main__':unittest.main()
