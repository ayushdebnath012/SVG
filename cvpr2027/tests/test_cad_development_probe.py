import copy,json,math,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cad_development_probe as p

class DevelopmentTests(unittest.TestCase):
    def test_uncut_cylinder_area(self):
        t={'spec':dict(kind='cylinder',R=29.,height=84.,seam_rad=.3,bores=[])}
        n=1000;area=p.reference(t,n).sum()*(260/n)**2
        self.assertLess(abs(area-2*math.pi*29*84)/(2*math.pi*29*84),.01)
    def test_uncut_cone_area(self):
        s=dict(kind='cone',r0=18.,r1=46.,height=58.,seam_rad=.47,bores=[])
        n=1000;area=p.reference({'spec':s},n).sum()*(260/n)**2
        exact=math.pi*(s['r0']+s['r1'])*math.hypot(s['r1']-s['r0'],s['height'])
        self.assertLess(abs(area-exact)/exact,.01)
    def test_cylinder_hole_against_independent_trigonometry(self):
        n=500;s=dict(kind='cylinder',R=29.,height=84.,seam_rad=0.,bores=[dict(point=[0,0,42],axis=[1,0,0],radius=12.)])
        v=np.linspace(-130+130/n,130-130/n,n);u,z=np.meshgrid(v,v[::-1])
        expected=(abs(u)<=math.pi*29)&(abs(z)<=42)&((29*np.sin(u/29+math.pi))**2+z*z>=144)
        np.testing.assert_array_equal(p.reference({'spec':s},n),expected)
    def test_axis_scaling_does_not_change_hole(self):
        t=json.loads((p.DATA/'tasks.json').read_text())['tasks'][2];other=copy.deepcopy(t)
        for b in other['spec']['bores']:b['axis']=[x*17 for x in b['axis']]
        np.testing.assert_array_equal(p.reference(t,500),p.reference(other,500))
    def test_numeric_tool_does_not_allow_files(self):
        with self.assertRaises(ValueError):p.numeric_execute("svg=open('/tmp/example').read()")
    def test_vector_contour_export_is_native_svg(self):
        v=np.linspace(-10,10,50);x,y=np.meshgrid(v,v)
        svg=p.contour_svg(v,v,25-x*x-y*y)
        self.assertIn('<path',svg);self.assertNotIn('<image',svg)

if __name__=='__main__':unittest.main()

