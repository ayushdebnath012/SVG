import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cad_part_cases as p
import cad_astra_benchmark as c

class PlateTests(unittest.TestCase):
    def test_rectangle_fillet_area_closed_form(self):
        path,area=p.fillet([[0,0],[100,0],[100,60],[0,60]],[5]*4)
        self.assertAlmostEqual(area,6000-4*25*(1-np.pi/4),places=8)
        self.assertTrue(path.isclosed())

    def test_signed_area_independent_polygon_quadrature(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp); p.build(out)
            for task in json.loads((out/'tasks.json').read_text())['tasks']:
                paths,ref=p.reference(task['spec']); samples={k:p.sample(v,0.03) for k,v in paths.items()}
                areas={k:abs(float(np.sum(v[:,0]*np.roll(v[:,1],-1)-v[:,1]*np.roll(v[:,0],-1)))/2) for k,v in samples.items()}
                self.assertAlmostEqual(ref['area_mm2'],areas['outer']-sum(v for k,v in areas.items() if k!='outer'),delta=0.01)
                obj={'svg':p.oracle_svg(task['spec']),'analysis':dict(ref,status='calculated')}
                self.assertEqual(c.score(task,json.dumps(obj))['outcome'],'pass')

    def test_stale_edit_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp); p.build(out); a,b=json.loads((out/'tasks.json').read_text())['tasks']
            obj={'svg':p.oracle_svg(a['spec']),'analysis':dict(a['reference'],status='calculated')}
            r=c.score(b,json.dumps(obj))
            self.assertTrue(r['geometry_errors']); self.assertTrue(r['analysis_errors'])

if __name__=='__main__': unittest.main()
