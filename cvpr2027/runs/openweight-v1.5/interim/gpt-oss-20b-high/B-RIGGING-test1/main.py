#!/usr/bin/env python
# Rigging plate analysis for test 1
import os, json, numpy as np, scipy.sparse as sp
from scipy.sparse import lil_matrix, csr_matrix
from scipy.sparse.linalg import spsolve
import gmsh
import cadquery as cq
import skfem.io.meshio as meshio
import time
import shutil

# Geometry
Lx, Ly, T = 152.40, 235.58, 12.00
# Material
E, nu = 71.7e9, 0.33
lam = E*nu/((1+nu)*(1-2*nu)); mu=E/(2*(1+nu))
C = np.zeros((6,6)); C[0,0]=lam+2*mu; C[0,1]=C[0,2]=lam
C[1,0]=lam; C[1,1]=lam+2*mu; C[1,2]=lam
C[2,0]=lam; C[2,1]=lam; C[2,2]=lam+2*mu
C[3,3]=C[4,4]=C[5,5]=mu

def mesh(fname,size):
    gmsh.initialize()
    gmsh.model.add('p')
    gmsh.model.occ.addBox(0,0,0,Lx,Ly,T)
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber('Mesh.MeshSizeMax',size)
    gmsh.model.mesh.generate(3)
    gmsh.write(fname)
    gmsh.finalize()

coarse='mesh_coarse.msh'; mesh(coarse,30)
fine='mesh_fine.msh'; mesh(fine,15); shutil.copyfile(fine,'mesh.msh')

def assemble(mesh):
    n=mesh.nvertices; p=mesh.p/1000; t=mesh.t; nE=mesh.nelements
    K=lil_matrix((n*3,n*3),dtype=np.float64); F=np.zeros(n*3,dtype=np.float64)
    left=set(); right=set(); supp=set()
    for f in mesh.boundary_facets():
        ids=mesh.facets[:,f]; xs=mesh.p[0,ids]
        if abs(xs.mean()-0)<1e-3: left.update(ids)
        if abs(xs.mean()-Lx)<1e-3: right.update(ids)
    for i,y in enumerate(mesh.p[1]):
        if abs(y-0)<1e-3: supp.add(i)
    area=(T/1000)*(Lx/1000); fmag=12000/area
    tr_l=np.array([0,fmag,0]); tr_r=np.array([0,-fmag,0])
    a=np.zeros((nE,6,12))
    for e in range(nE):
        nid=t[:,e]; pm=p[:,nid]
        M=np.ones((4,4)); M[1:]=pm; inv=np.linalg.inv(M); a0=inv[1]; b0=inv[2]; c0=inv[3]
        for i_local in range(4):
            i0=i_local*3; ai=a0[i_local]; bi=b0[i_local]; ci=c0[i_local]
            a[e,0,i0]=ai; a[e,1,i0+1]=bi; a[e,2,i0+2]=ci
            a[e,3,i0]=bi; a[e,3,i0+1]=ai; a[e,4,i0+1]=ci; a[e,4,i0+2]=bi
            a[e,5,i0]=ci; a[e,5,i0+2]=ai
        Vs=np.abs(np.linalg.det(np.vstack((pm[:,1]-pm[:,0],pm[:,2]-pm[:,0],pm[:,3]-pm[:,0]))))/6.
        Ke=Vs*(a[e].T @ C @ a[e])
        for ii,ni in enumerate(nid):
            I=ni*3
            for jj,nj in enumerate(nid):
                J=nj*3
                K[I:I+3,J:J+3]+=Ke[ii*3:(ii+1)*3, jj*3:(jj+1)*3]
    for f in mesh.boundary_facets():
        ids=mesh.facets[:,f]; cm=mesh.p[:,ids]/1000
        area=0.5*np.linalg.norm(np.cross(cm[:,1]-cm[:,0], cm[:,2]-cm[:,0]))
        avgx=mesh.p[0,ids].mean()
        if abs(avgx-0)<1e-3: tvec=tr_l
        elif abs(avgx-Lx)<1e-3: tvec=tr_r
        else: continue
        fcon=tvec*area/3
        for n in ids:
            for d in range(3): F[n*3+d]+=fcon[d]
    for n in supp:
        I=n*3; K[I:I+3,:]=0; K[:,I:I+3]=0; K[I:I+3,I:I+3]=np.eye(3); F[I:I+3]=0
    return K.tocsr(),F


def solve(file,full=False):
    m=meshio.from_file(file,None); K,F=assemble(m)
    u=spsolve(K,F)
    ne=m.nelements; t=m.t; p=m.p/1000
    SM=np.empty((ne,6)); VM=np.empty(ne); cen=np.empty((ne,3))
    for e in range(ne):
        nid=t[:,e]; pm=p[:,nid]
        M=np.ones((4,4)); M[1:]=pm; inv=np.linalg.inv(M); a0=inv[1]; b0=inv[2]; c0=inv[3]
        a=np.zeros((6,12))
        for i_l in range(4):
            i0=i_l*3; ai=a0[i_l]; bi=b0[i_l]; ci=c0[i_l]
            a[0,i0]=ai; a[1,i0+1]=bi; a[2,i0+2]=ci
            a[3,i0]=bi; a[3,i0+1]=ai; a[4,i0+1]=ci; a[4,i0+2]=bi
            a[5,i0]=ci; a[5,i0+2]=ai
        u_nodes = u.reshape((-1,3))
        up = u_nodes[nid].reshape(12,)
        eps=a@up
        s=C@eps; SM[e]=s/1e6
        Sxx,Syy,Szz,Sxy,Syz,Szx=s
        vm=np.sqrt(0.5*((Sxx-Syy)**2+(Syy-Szz)**2+(Szz-Sxx)**2)+3*(Sxy**2+Syz**2+Szx**2))/1e6
        VM[e]=vm
        cen[e]=p[:, nid].mean(axis=1)
    maxvm=VM.max()
    if full:
        return maxvm, u.reshape(-1,3)*1000, SM, cen, VM
    return maxvm

maxc=solve(coarse)
maxf, u, SM, cen, VM=solve('mesh.msh',True)

fine_mesh=meshio.from_file('mesh.msh',None); nodes=fine_mesh.p.T
np.savez('fields.npz', node_ids=np.arange(1,fine_mesh.nvertices+1), coordinates_mm=nodes, displacements_mm=u, element_ids=np.arange(1,fine_mesh.nelements+1), element_centroid_mm=cen, stresses_MPa=SM, vonMises_MPa=VM)

with open('results.json','w') as f: json.dump({'outputs':{'max_von_mises_MPa':float(maxf)}},f)

coarse_mesh=meshio.from_file(coarse,None)
ref={'refinements':[{'resolution':'coarse','vertices':int(coarse_mesh.nvertices),'elements':int(coarse_mesh.nelements),'max_von_mises_MPa':float(maxc)},
                    {'resolution':'fine','vertices':int(fine_mesh.nvertices),'elements':int(fine_mesh.nelements),'max_von_mises_MPa':float(maxf)}]}
with open('refinement.json','w') as f: json.dump(ref,f)

with open('solver.log','w') as f: f.write('Gmsh version: unknown\nMax stress coarse: '+str(maxc)+'\nMax stress fine: '+str(maxf)+'\n')

part=cq.Workplane('XY').box(Lx, Ly, T, centered=False)
cq.exporters.export(part,'part.step')

environment={'description':'rigging plate', 'material':{'E':E,'nu':nu},'mesh_file':'mesh.msh','step_file':'part.step'}
with open('environment.json','w') as f: json.dump(environment,f,indent=2)
