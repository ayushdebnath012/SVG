import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cad_astra_benchmark as cad


class MechanicsTests(unittest.TestCase):
    def cantilever(self):
        return dict(nodes={'A':[0,0],'B':[1000,0]},members=[cad.member('beam','A','B',20,40)],
                    supports={'A':[0,1,2]},loads={'B':[250,-100,0]},probe='B')

    def test_cantilever_matches_closed_forms(self):
        m=self.cantilever(); r=cad.solve(m); E=200000; A=800; I=20*40**3/12
        self.assertAlmostEqual(r['ux_mm'],250*1000/(E*A),places=10)
        self.assertAlmostEqual(r['uy_mm'],-100*1000**3/(3*E*I),places=10)
        self.assertAlmostEqual(r['peak_stress_mpa'],250/A+100*1000*20/I,places=10)
        np.testing.assert_allclose(r['reactions']['A'],[-250,100,100000],atol=1e-7)

    def test_simply_supported_central_load(self):
        m=dict(nodes={'A':[0,0],'B':[500,0],'C':[1000,0]},members=[cad.member('L','A','B',20,40),cad.member('R','B','C',20,40)],
               supports={'A':[0,1],'C':[1]},loads={'B':[0,-100,0]},probe='B')
        r=cad.solve(m)
        self.assertAlmostEqual(r['uy_mm'],-100*1000**3/(48*200000*(20*40**3/12)),places=10)
        self.assertAlmostEqual(r['reactions']['A'][1],50,places=9)
        self.assertAlmostEqual(r['reactions']['C'][1],50,places=9)

    def test_rotated_beam_and_refinement(self):
        m=self.cantilever(); theta=0.73
        R=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
        target=R@np.array([cad.solve(m)['ux_mm'],cad.solve(m)['uy_mm']])
        m['nodes']['B']=(R@np.array(m['nodes']['B'])).tolist()
        m['loads']['B'][:2]=(R@np.array(m['loads']['B'][:2])).tolist()
        for n in (1,4):
            r=cad.solve(m,n)
            np.testing.assert_allclose([r['ux_mm'],r['uy_mm']],target,rtol=1e-9,atol=1e-9)

    def test_independent_cranked_shelf_solution(self):
        _,a,b,_=cad.models()[2]
        for m in (a,b):
            independent=cad.cantilever_virtual_work(m); fem=cad.solve(m)
            for k in independent: self.assertAlmostEqual(independent[k],fem[k],places=7)
            self.assertLess(max(abs(x) for x in fem['equilibrium_residual_N_Nmm']),1e-4)


class DrawingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(); path=Path(cls.temp.name)
        cad.build(path); cls.tasks=json.loads((path/'tasks.json').read_text())['tasks']

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def response(self,t):
        return dict(svg=cad.reference_svg(t['model'],t['mapping']),analysis={
            **{k:t['reference'][k] for k in ('ux_mm','uy_mm','peak_stress_mpa')},'status':'calculated'})

    def test_valid_references_pass(self):
        for t in self.tasks:
            with self.subTest(t=t['id']): self.assertEqual(cad.score(t,json.dumps(self.response(t)))['outcome'],'pass')

    def test_changed_geometry_is_detected(self):
        t=self.tasks[0]; obj=self.response(t)
        root=ET.fromstring(obj['svg']); el=next(e for e in root.iter() if e.get('data-member')=='leg_L')
        el.set('x1',str(float(el.get('x1'))+10)); obj['svg']=ET.tostring(root,encoding='unicode')
        r=cad.score(t,json.dumps(obj)); self.assertTrue(r['geometry_errors'])

    def test_displaced_interior_of_path_is_detected(self):
        t=self.tasks[0]; obj=self.response(t)
        root=ET.fromstring(obj['svg']); el=next(e for e in root.iter() if e.get('data-member')=='leg_L')
        x1,y1,x2,y2=[float(el.get(k)) for k in ('x1','y1','x2','y2')]
        el.tag='{http://www.w3.org/2000/svg}path'; el.set('d',f'M{x1},{y1} L{x1+20},{(y1+y2)/2} L{x2},{y2}')
        obj['svg']=ET.tostring(root,encoding='unicode'); self.assertTrue(cad.score(t,json.dumps(obj))['geometry_errors'])

    def test_equivalent_transform_passes(self):
        t=self.tasks[0]; obj=self.response(t); root=ET.fromstring(obj['svg'])
        for el in root.iter():
            if el.get('data-member'):
                el.set('transform','translate(15,25)')
                for k,d in [('x1',15),('x2',15),('y1',25),('y2',25)]: el.set(k,str(float(el.get(k))-d))
        obj['svg']=ET.tostring(root,encoding='unicode'); self.assertEqual(cad.score(t,json.dumps(obj))['outcome'],'pass')

    def test_stale_edit_fails_geometry_and_physics(self):
        before,after=self.tasks[:2]
        obj=self.response(before); r=cad.score(after,json.dumps(obj))
        self.assertTrue(r['geometry_errors']); self.assertTrue(r['analysis_errors']); self.assertTrue(r['dimension_errors'])

    def test_wrong_visible_label_detected(self):
        t=self.tasks[0]; obj=self.response(t); root=ET.fromstring(obj['svg'])
        next(e for e in root.iter() if e.get('data-result')=='uy_mm').text='999 mm'
        obj['svg']=ET.tostring(root,encoding='unicode')
        self.assertTrue(cad.score(t,json.dumps(obj))['visible_result_errors'])

    def test_hidden_geometry_is_not_substantive_failure(self):
        t=self.tasks[0]; obj=self.response(t)
        obj['svg']=obj['svg'].replace('stroke="#1f3348"','stroke="none"')
        self.assertEqual(cad.score(t,json.dumps(obj))['outcome'],'unscored_format')

    def test_invalid_or_missing_output_excluded(self):
        for text in ('','not json','{}'):
            self.assertEqual(cad.score(self.tasks[0],text)['outcome'],'unscored_format')

if __name__=='__main__': unittest.main()

class SelectionTests(unittest.TestCase):
    def test_repeatable_physics_failure_does_not_become_drawing_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            data=Path(tmp)/'data'; cad.build(data)
            manifest=json.loads((data/'tasks.json').read_text()); task=manifest['tasks'][0]
            obj=dict(svg=cad.reference_svg(task['model'],task['mapping']),analysis={
                **{k:task['reference'][k] for k in ('ux_mm','uy_mm','peak_stress_mpa')},'status':'estimated'})
            obj['analysis']['uy_mm']*=2
            runs=[]
            for name,effort,n in [('screen','medium',1),('confirm','high',2)]:
                run=Path(tmp)/name; runs.append(run)
                cad.write_json(run/'protocol.json',dict(model='gpt-6-astra',effort=effort,samples=n,task_ids=[task['id']],manifest_sha256=cad.digest(manifest)))
                for i in range(n):
                    folder=run/task['id']/f'sample-{i}'
                    cad.write_json(folder/'result.json',dict(status='completed',finish_reason='stop'))
                    (folder/'response.txt').write_text(json.dumps(obj))
            review=Path(tmp)/'review.json'
            cad.write_json(review,{task['id']:dict(confirmed=True,reviewer_type='assistant',rationale='Test fixture',checked_samples=['screen/sample-0','confirm/sample-0','confirm/sample-1'])})
            out=Path(tmp)/'selection.json'
            cad.select(data,runs,out,review)
            selection=json.loads(out.read_text())
            self.assertEqual(selection['selected'][0]['tracks'],['physical_analysis'])
            self.assertEqual(json.loads(out.with_name('selected_drawing_tasks.json').read_text())['tasks'],[])
            with self.assertRaises(ValueError): cad.select(data,[runs[0],runs[0]],out,review)
            cad.select(data,[runs[0]],out,review)
            self.assertEqual(json.loads(out.read_text())['selected'],[])
