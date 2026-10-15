import os, json, time
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
import numpy as np
import cadquery as cq
from skfem import MeshQuad, Basis, FacetBasis, ElementQuad2, ElementVector, LinearForm, BilinearForm, Functional, asm
from scipy.sparse.linalg import spsolve

E=100.
force=269.35
@LinearForm
def internal(v,w):
    return np.einsum('ij...,ij...->...',w.P,v.grad)
@BilinearForm
def tangent(u,v,w):
    return E*(np.einsum('ij...,il...,lj...->...',v.grad,u.grad,w.G)
              +.5*np.einsum('ij...,kl...,il...,kj...->...',v.grad,u.grad,w.F,w.F)
              +.5*np.einsum('ij...,kj...,ik...->...',v.grad,u.grad,w.B))
@LinearForm
def load(v,w):
    return -w.traction*v[1]
@Functional
def average_x(w):
    return w.u[0]
@Functional
def average_z(w):
    return w.u[1]

def solve(nx,nz,L,h,width):
    start=time.time()
    mesh=MeshQuad.init_tensor(np.linspace(0,L,nx+1),np.linspace(-h/2,h/2,nz+1))
    element=ElementVector(ElementQuad2())
    basis=Basis(mesh,element,intorder=6)
    right=mesh.facets_satisfying(lambda x: np.isclose(x[0],L))
    fb=FacetBasis(mesh,element,facets=right,intorder=6)
    clamp=basis.get_dofs(lambda x:np.isclose(x[0],0)).all()
    free=np.setdiff1d(np.arange(basis.N),clamp)
    f=asm(load,fb,traction=force/(width*h))
    u=np.zeros(basis.N)
    eye=np.eye(2)[:,:,None,None]
    def state(u, need_k=True):
        F=eye+basis.interpolate(u).grad
        G=.5*(np.einsum('ki...,kj...->ij...',F,F)-eye)
        P=E*np.einsum('ik...,kj...->ij...',F,G)
        r=asm(internal,basis,P=P)
        energy=.5*E*np.sum(np.einsum('ij...,ij...->...',G,G)*basis.dx)
        if need_k:
            B=np.einsum('ik...,jk...->ij...',F,F)
            K=asm(tangent,basis,F=F,G=G,B=B)
            return r,K,energy
        return r,energy
    history=[]
    t=0.; dt=.05
    while t < 1-1e-12:
        target=min(1.,t+dt)
        old=u.copy(); converged=False
        for it in range(35):
            r,K,en=state(u)
            r-=target*f
            norm=np.linalg.norm(r[free])
            if norm<max(1e-7,1e-6*np.linalg.norm(target*f[free])):
                converged=True;break
            du=np.zeros_like(u)
            du[free]=spsolve(K[free][:,free].tocsc(),-r[free])
            pot=en-target*f@u
            descent=r@du
            alpha=1.
            for ls in range(18):
                cand=u+alpha*du
                rn,enn=state(cand,False)
                if enn-target*f@cand <= pot+1e-4*alpha*descent+1e-10:
                    break
                alpha*=.5
            u=cand
        if not converged:
            u=old;dt*=.5
            if dt<1e-5: raise RuntimeError('Continuation failed')
            continue
        t=target
        dx=-asm(average_x,fb,u=fb.interpolate(u))/h
        dz=-asm(average_z,fb,u=fb.interpolate(u))/h
        history.append([t,it,norm,dx,dz])
        print(nx,nz,'load',round(t,5),'iterations',it,'residual',norm,'tip',dx,dz,'seconds',time.time()-start,flush=True)
        if it<7: dt=min(.15,dt*1.4)
    np.savez('solution_%dx%d.npz'%(nx,nz),mesh_points=mesh.p,mesh_elements=mesh.t,dof_locations=basis.doflocs,displacement=u,history=np.array(history))
    return {'nx':nx,'nz':nz,'dofs':int(basis.N),'horizontal':dx,'vertical':dz,'time_s':time.time()-start,'history':history}

def main():
    solid=cq.importers.importStep(os.path.join(os.environ['CADFEM_INPUT_DIR'],'bar.step')).val()
    bb=solid.BoundingBox()
    L,h,width=bb.xlen,bb.zlen,bb.ylen
    print('Dimensions',L,h,width,flush=True)
    studies=[]
    for nx,nz in [(60,2),(120,4),(240,6)]:
        studies.append(solve(nx,nz,L,h,width))
    final=studies[-1]
    with open('results.json','w') as f:
        json.dump({'outputs':{'tip_vertical_deflection_mm':final['vertical'],'tip_horizontal_displacement_mm':final['horizontal']}},f,indent=2)
    with open('convergence.json','w') as f:json.dump(studies,f,indent=2)
    with open('analysis.txt','w') as f:
        f.write('Total-Lagrangian St Venant-Kirchhoff continuum finite element analysis.\n'
                'Quadratic quadrilateral elements, 4x4 Gauss integration, Newton continuation.\n'
                'At Poisson ratio zero the uniform-width solution is exactly a two-dimensional deformation with uy=0: Eyy=Syy=Pyy=0.\n'
                'The 2D x-z continuum problem therefore represents the full 3D bar without beam kinematic assumptions.\n'
                'All displacement components vanish at x=0. The dead reference traction on x=L equals -269.35/(300*102.61) MPa in z.\n'
                'Tip output is the undeformed-area average displacement of the loaded face. Units mm, N, MPa.\n')
        f.write(json.dumps(studies,indent=2))
if __name__=='__main__':main()
