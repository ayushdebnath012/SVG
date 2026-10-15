"""Trusted residual/extraction checks for cycloidal quadratic-tet artifacts.
This never reads target values. It verifies a submitted field against a newly
assembled source-defined linear elasticity operator, not a candidate's residual.
Other physics remain unsupported and never receive automatic approval.
"""
from pathlib import Path
import argparse,json,re
import numpy as np,meshio
from scipy.spatial import cKDTree
from skfem import Basis,FacetBasis,ElementVector,ElementTetP2,Functional,LinearForm,asm
from skfem.io import from_meshio
from skfem.models.elasticity import linear_elasticity,lame_parameters


def check(task,mesh_path,field_path):
 if task['family']!='cycloidal-drive-components':raise ValueError('automatic field physics unsupported for this family')
 E=float(re.search(r'E = ([\d.]+) MPa',task['prompt']).group(1));nu=float(re.search(r'Poisson ratio ([\d.]+)',task['prompt']).group(1).rstrip('.'))
 mm=meshio.read(mesh_path)
 if 'tetra10' not in mm.cells_dict or 'triangle6' not in mm.cells_dict:raise ValueError('curved quadratic Gmsh tetrahedra and physical boundary tags required')
 if len(mm.cells_dict['tetra10'])>220000:raise ValueError('mesh exceeds trusted verifier resource cap')
 mesh=from_meshio(mm);distance,facet=cKDTree(mesh.p[:,mesh.facets].mean(axis=1).T).query(mm.points[mm.cells_dict['triangle6'][:,:3]].mean(1))
 if distance.max()>1e-7:raise ValueError('boundary facet mapping invalid')
 tags=mm.cell_data_dict['gmsh:physical']['triangle6'];mesh=mesh.with_boundaries({name:facet[tags==int(data[0])] for name,data in mm.field_data.items() if int(data[1])==2});basis=Basis(mesh,ElementVector(ElementTetP2()),intorder=4);K=asm(linear_elasticity(*lame_parameters(E,nu)),basis);F=np.zeros(basis.N)
 @Functional
 def area(w):return 1.
 loads=re.findall(r'face (\d+) carries \(([^)]+)\) N',task['prompt'])
 if not loads or 'fixed' not in mesh.boundaries:raise ValueError('expected support/load groups missing')
 for j,(_,v) in enumerate(loads,20):
  tag='load'+str(j)
  if tag not in mesh.boundaries:raise ValueError('expected load group missing: '+tag)
  fb=FacetBasis(mesh,basis.elem,facets=mesh.boundaries[tag],intorder=4);tr=np.array([float(x) for x in v.split(',')])/area.assemble(fb)
  @LinearForm
  def rhs(v,w):return np.einsum('i,ijk->jk',tr,v)
  F+=asm(rhs,fb)
 with np.load(field_path,allow_pickle=False) as z:
  pts=z['coordinates_mm'];u=z['displacement_mm']
  if pts.ndim!=2 or pts.shape[1]!=3 or u.shape!=pts.shape or not np.isfinite(pts).all() or not np.isfinite(u).all():raise ValueError('invalid nodal arrays')
  comp=basis.split_indices();expected=basis.doflocs[:,comp[0]].T
  d,ix=cKDTree(pts).query(expected)
  if len(pts)!=len(expected) or len(set(ix))!=len(ix) or d.max()>1e-7:raise ValueError('fields do not cover the actual finite-element nodes')
  U=np.zeros(basis.N)
  for k,index in enumerate(comp):U[index]=u[ix,k]
 fixed=basis.get_dofs('fixed').all();free=np.setdiff1d(np.arange(basis.N),fixed)
 residual=K@U-F;rel=float(np.linalg.norm(residual[free])/max(np.linalg.norm(F),1e-30));fixed_u=float(np.max(np.abs(U[fixed])));q=float(np.linalg.norm(u,axis=1).max())
 return {'source_operator_residual_relative':rel,'fixed_dof_max_mm':fixed_u,'extracted_max_displacement_mm':q,'field_equilibrium_passed':rel<1e-8 and fixed_u<1e-10,'elements':mesh.nelements,'limitations':['Boundary labels are not yet geometrically audited against all CAD faces.','Equilibrium and extraction checks do not establish geometry/setup/convergence approval by themselves.']}

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--task',type=Path,required=True);a.add_argument('--mesh',type=Path,required=True);a.add_argument('--fields',type=Path,required=True);a.add_argument('--out',type=Path,required=True);x=a.parse_args();r=check(json.loads(x.task.read_text()),x.mesh,x.fields);x.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
