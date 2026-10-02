import copy,json,sys,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
from svgpathtools import parse_path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cad_part_nesting as n

class NestingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.t=json.loads((n.DATA/'tasks.json').read_text())['tasks'][0]
    def test_reference_continuous_and_discrete(self):
        self.assertTrue(n.grade(self.t,self.t['reference_poses'])['pass'])
        self.assertTrue(n.audit(self.t,n.DATA/'reference.svg')['pass'])
    def test_missing_and_off_stock(self):
        poses=copy.deepcopy(self.t['reference_poses']);del poses['P01'];poses['P02']['x']=100
        kinds={v['kind'] for v in n.grade(self.t,poses)['violations']}
        self.assertTrue({'missing_part','outside_stock'} <= kinds)
    def test_collision(self):
        poses={p['id']:{'x':0,'y':0,'rotation':0} for p in self.t['parts']}
        self.assertTrue(any(v['kind']=='overlap' for v in n.grade(self.t,poses)['violations']))
    def test_rotation_rule(self):
        self.assertEqual(n.rotate([(0,0),(1,0),(1,1)],90),[(0,1),(1,0),(1,1)])
        with self.assertRaises(ValueError):n.rotate([(0,0)],45)
    def test_svg_coordinate_tamper(self):
        tree=ET.parse(n.DATA/'reference.svg');e=next(e for e in tree.getroot().iter() if e.get('data-piece')=='P01');path=parse_path(e.attrib['d'])
        for seg in path:seg.start+=1;seg.end+=1
        e.set('d',path.d())
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'tampered.svg';tree.write(p)
            self.assertFalse(n.audit(self.t,p)['pass'])

if __name__=='__main__':unittest.main()
