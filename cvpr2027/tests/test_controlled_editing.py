import copy
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from controlled_editing_data import build,execute,make_document,solve_plate
from train_controlled_editing import score_action


class ControlledEditingTests(unittest.TestCase):
    def setUp(self):
        self.doc=make_document('test',random.Random(42))
        self.cid=self.doc['contours'][0]['id']

    def test_solver_matches_analytic(self):
        for w,h in ((.7,2.5),(2.5,.7),(1,1)):
            *_,stats=solve_plate(w,h,397,281)
            self.assertLess(stats['max_error_against_exact_K'],1e-8)
            self.assertLess(stats['relative_linear_residual'],1e-12)

    def test_style_does_not_change_geometry_or_claims(self):
        before=copy.deepcopy(self.doc)
        after=execute(self.doc,{'action':'style','target':self.cid,'attribute':'stroke','value':'#2563eb'})['document']
        self.assertEqual(self.doc,before)
        a=ET.fromstring(after['svg']);b=ET.fromstring(before['svg'])
        for left,right in zip(a.iter(),b.iter()):
            if left.get('id')==self.cid:left.set('stroke',right.get('stroke'))
        self.assertEqual(ET.tostring(a),ET.tostring(b))
        self.assertEqual(after['solution_id'],before['solution_id'])

    def test_protected_properties_and_visibility(self):
        for attr,val in [('d','M0 0 L1 1'),('transform','scale(2)'),('opacity',0),
                         ('data-level',0),('stroke','white'),('stroke','#ffffff'),
                         ('stroke-width',0),('stroke-width',True),('stroke-width',float('nan'))]:
            with self.subTest(attr=attr,val=val),self.assertRaises(ValueError):
                execute(self.doc,{'action':'style','target':self.cid,'attribute':attr,'value':val})

    def test_recompute_never_recertifies_old_drawing(self):
        outcome=execute(self.doc,{'action':'recompute','parameter':'left_temperature','value':400})
        self.assertEqual(outcome['status'],'requires_solver')
        self.assertEqual(outcome['document'],self.doc)

    def test_labels_cannot_enter_field_or_change_value(self):
        lid=self.doc['labels'][0]['id']
        for action in [{'action':'move_label','target':lid,'x':100,'y':200},
                       {'action':'move_label','target':lid,'x':500,'y':200,'text':'999 K'}]:
            with self.assertRaises(ValueError):execute(self.doc,action)

    def test_all_attempts_and_semantic_misuse_scored(self):
        row={'document':self.doc,'target':{'action':'reject','reason':'numerical_claim'}}
        self.assertFalse(score_action(row,'not JSON')['exact_action'])
        wrong={'action':'style','target':self.cid,'attribute':'stroke','value':'#2563eb'}
        metrics=score_action(row,json.dumps(wrong))
        self.assertTrue(metrics['executor_accepts']);self.assertTrue(metrics['unsafe_edit'])
        self.assertFalse(metrics['exact_action'])

    def test_reproducible_case_split(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            self.assertEqual(build(a,counts=(3,2,2,2)),build(b,counts=(3,2,2,2)))
            seen=set()
            for split in ('train','validation','test','ood'):
                rows=[json.loads(l) for l in (Path(a)/f'{split}.jsonl').read_text().splitlines()]
                cases={r['case_id'] for r in rows}
                self.assertFalse(seen&cases);seen|=cases
                for row in rows:
                    ids=[c['id'] for c in row['document']['contours']]
                    self.assertEqual(len(ids),len(set(ids)))
                    self.assertEqual(row['document']['record']['physical_problem']['family']=='annulus',split=='ood')

    def test_formatting_sensitivity_does_not_cherry_pick_objects(self):
        row={'document':self.doc,'target':{'action':'reject','reason':'numerical_claim'}}
        text=json.dumps(row['target'])
        metrics=score_action(row,'```json\n'+text+'\n```')
        self.assertFalse(metrics['exact_action'])
        self.assertTrue(metrics['fence_normalized_exact_action'])
        for bad in (text+','+text,'```json\n'+text+',\n'+text+'\n```','explanation '+text):
            self.assertFalse(score_action(row,bad)['fence_normalized_exact_action'])


if __name__=='__main__':unittest.main()
