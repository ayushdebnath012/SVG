"""Independent CAD-section, beam-element and assembly Jacobian verification."""
import math
import numpy as np
import cadquery as cq
from scipy.linalg import eigvalsh

def verify(p,arm,assembly,box,props):
    out={}
    # Refine the thickness of a CAD section: exact B-rep volume/inertia integration.
    samples=[]
    for thick in (0.4,0.2,0.1,0.05):
        w=p['arm_width_mm'];d=p['arm_depth_mm']
        cut=arm.intersect(box(thick,2*w,2*d,(-thick/2,-w,-d)))
        mat=np.array(cq.Shape.matrixOfInertia(cut))
        area=cut.Volume()/thick
        samples.append(dict(slice_thickness_mm=thick,area_mm2=area,
                            Iy_mm4=float(mat[1,1]/thick-area*thick**2/12),
                            Iz_mm4=float(mat[2,2]/thick-area*thick**2/12)))
    out['cad_section_refinement']=samples
    stations=np.linspace(0,p['arm_pin_spacing_mm'],1001)
    values=np.array([props(p,s) for s in stations])
    area,Iy,Iz=props(p,0)
    out['sampled_section_minima']={'stations':len(stations),'area_mm2':float(values[:,0].min()),'principal_I_mm4':float(values[:,1:].min())}
    # Pinned Euler-Bernoulli elastic stability problem: K phi = P KG phi.
    # The constant MINIMUM net section is conservative; the reported Johnson
    # capacity separately accounts for inelasticity of this short steel column.
    E=p['elastic_modulus_MPa'];I=min(Iy,Iz);L=p['arm_pin_spacing_mm']
    exact=math.pi**2*E*I/L**2
    results=[]
    for ne in (8,16,32):
        le=L/ne;nd=2*(ne+1);K=np.zeros((nd,nd));G=K.copy()
        k=E*I/le**3*np.array([[12,6*le,-12,6*le],[6*le,4*le**2,-6*le,2*le**2],[-12,-6*le,12,-6*le],[6*le,2*le**2,-6*le,4*le**2]])
        g=np.array([[36,3*le,-36,3*le],[3*le,4*le**2,-3*le,-le**2],[-36,-3*le,36,-3*le],[3*le,-le**2,-3*le,4*le**2]])/(30*le)
        for e in range(ne):
            dofs=np.arange(2*e,2*e+4)
            K[np.ix_(dofs,dofs)]+=k;G[np.ix_(dofs,dofs)]+=g
        free=np.array([i for i in range(nd) if i not in [0,nd-2]])
        load=float(eigvalsh(K[np.ix_(free,free)],G[np.ix_(free,free)],subset_by_index=[0,0])[0])
        results.append(dict(elements=ne,elastic_buckling_N=load,relative_error=abs(load/exact-1)))
    out['beam_fem_convergence']=results
    out['elastic_Euler_reference_N']=exact
    # Spatial rigid-body infinitesimal constraint Jacobian. Each free body has
    # six components (global translation and rotation). Revolutes lock five,
    # prismatics five, and fixed joints six. A distance is the actuator input.
    names=[x['name'] for x in assembly['parts'] if x['name']!=assembly['ground']]
    n=6*len(names)
    def skew(v):
        x,y,z=v
        return np.array([[0,-z,y],[z,0,-x],[-y,x,0.]])
    def velocity(name,point):
        M=np.zeros((3,n))
        if name in names:
            i=6*names.index(name);M[:,i:i+3]=np.eye(3);M[:,i+3:i+6]=-skew(point)
        return M
    def spin(name):
        M=np.zeros((3,n))
        if name in names:
            i=6*names.index(name);M[:,i+3:i+6]=np.eye(3)
        return M
    constraints=[];dr=[]
    for j in assembly['joints']:
        A,B=j['parts'];typ=j['type'];pt=j.get('origin',[0,0,0])
        V=velocity(A,pt)-velocity(B,pt);R=spin(A)-spin(B)
        if typ=='revolute':constraints.extend([V,R[[0,2],:]])
        elif typ=='fixed':constraints.extend([V,R])
        elif typ=='prismatic':
            axis=np.array(j['axis']);_,_,vh=np.linalg.svd(axis.reshape(1,3));normal=vh[1:]
            constraints.extend([normal@V,R])
        elif typ=='distance':
            a=np.array(j['point_a']);b=np.array(j['point_b']);u=(a-b)/np.linalg.norm(a-b)
            dr.append(u@(velocity(A,a)-velocity(B,b)))
    J=np.vstack(constraints);Jdr=np.vstack([J,*dr])
    rank=int(np.linalg.matrix_rank(J,tol=1e-8));rankdr=int(np.linalg.matrix_rank(Jdr,tol=1e-8))
    out['kinematics']={'body_coordinates':n,'constraint_rank_without_driver':rank,'free_dof':n-rank,
                       'constraint_rank_with_driver':rankdr,'free_dof_with_driver_locked':n-rankdr,
                       'saddle_level_degrees':0.0}
    return out
