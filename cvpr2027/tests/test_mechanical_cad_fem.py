import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from mechanical_cad_fem import solve

class ElasticityChecks(unittest.TestCase):
 def setUp(self):
  self.points=10*np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]],float)
  self.tet=np.array([[0,1,2,6],[0,2,3,6],[0,3,7,6],[0,7,4,6],[0,4,5,6],[0,5,1,6]])
 def test_analytic_uniform_tension(self):
  m,u,v=solve(self.points,self.tet,nu=0,exact_planes=True)
  self.assertAlmostEqual(m['compliance_N_mm'],10/(210000*100),places=15)
  self.assertTrue(np.allclose(v,.01))
 def test_force_and_modulus_scaling(self):
  a,_,_=solve(self.points,self.tet,nu=0,exact_planes=True)
  b,_,_=solve(self.points,self.tet,nu=0,force=2,exact_planes=True)
  c,_,_=solve(self.points,self.tet,nu=0,E=420000,exact_planes=True)
  self.assertAlmostEqual(b['compliance_N_mm']/a['compliance_N_mm'],4)
  self.assertAlmostEqual(c['compliance_N_mm']/a['compliance_N_mm'],.5)
 def test_rotated_fixture_invariance(self):
  a,_,_=solve(self.points,self.tet,nu=0,exact_planes=True)
  th=.73;R=np.array([[np.cos(th),0,np.sin(th)],[0,1,0],[-np.sin(th),0,np.cos(th)]])
  b,_,_=solve(self.points@R.T,self.tet,axis=R@np.array([0.,0.,1.]),nu=0,exact_planes=True)
  self.assertAlmostEqual(b['compliance_N_mm']/a['compliance_N_mm'],1)
  self.assertLess(b['relative_moment_balance_error'],1e-10)
if __name__=='__main__':unittest.main()
