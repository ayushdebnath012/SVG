"""CAD/FEM diagnostic metrics v0.1. Never executes submitted code or certifies workflow."""
from __future__ import annotations
import argparse
import itertools
import json
import math
import numbers
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree


def finite(value, name="array"):
    a = np.asarray(value, dtype=float)
    if not a.size or not np.isfinite(a).all():
        raise ValueError(name + " must be nonempty and finite")
    return a


def positive(value, name):
    x = float(value)
    if not math.isfinite(x) or x <= 0:
        raise ValueError(name + " must be positive and finite")
    return x


def surface_metrics(pred, ref, reference_diagonal, threshold_fraction=.005):
    """Symmetric nearest-neighbor metrics between two point clouds, no rescaling/alignment.

    Point-to-point distances between independent samplings carry a sampling floor; CAD
    geometry_metrics uses exact point-to-surface distances instead."""
    p, q = finite(pred), finite(ref)
    if p.ndim != 2 or q.ndim != 2 or p.shape[1] != 3 or q.shape[1] != 3:
        raise ValueError("Surface point clouds must be N x 3")
    return distance_summary(cKDTree(q).query(p)[0], cKDTree(p).query(q)[0], reference_diagonal, threshold_fraction)


def distance_summary(dp, dq, reference_diagonal, threshold_fraction=.005):
    """Chamfer/Hausdorff/F1 from directional distances: predicted->reference dp, reference->predicted dq."""
    dp, dq = finite(dp, "dp"), finite(dq, "dq")
    scale = positive(reference_diagonal, "reference_diagonal")
    tau = positive(threshold_fraction, "threshold_fraction") * scale
    precision, recall = float(np.mean(dp <= tau)), float(np.mean(dq <= tau))
    cd = .5 * (dp.mean() + dq.mean())
    cd2 = .5 * (np.mean(dp**2) + np.mean(dq**2))
    return {"cd_l1": float(cd), "cd_l1_over_reference_diagonal": float(cd/scale),
            "cd_l2_squared": float(cd2), "cd_l2_squared_over_diagonal_squared": float(cd2/scale**2),
            "hausdorff": float(max(dp.max(), dq.max())),
            "hausdorff_p95": float(max(np.quantile(dp,.95), np.quantile(dq,.95))),
            "surface_precision": precision, "surface_recall": recall,
            "surface_f1": 2*precision*recall/(precision+recall) if precision+recall else 0.,
            "surface_threshold_physical": tau, "surface_threshold_fraction": threshold_fraction,
            "predicted_samples": len(dp), "reference_samples": len(dq)}


def edit_headroom(iou_prediction_target, iou_original_target):
    """BenchCAD's clipped edit improvement; return N/A on near-no-op reference pairs."""
    a, b = float(iou_prediction_target), float(iou_original_target)
    if not all(math.isfinite(x) and 0 <= x <= 1 for x in (a,b)):
        raise ValueError("IoUs must lie in [0,1]")
    return float(np.clip((a-b)/(1-b),0,1)) if b < .99 else None


def benchcad2_part_terms(iou, primitive_baseline, predicted_betti, reference_betti):
    """Combine trusted upstream measurements; NOT an implementation of its geometry pipeline.

    Inputs must already satisfy BenchCAD 2's solid gate, voxel/normalization and
    topology-counting rules. This compatibility score never grants an engineering pass.
    """
    x, x0 = finite([iou, primitive_baseline])
    if not (0 <= x <= 1 and 0 <= x0 <= 1):
        raise ValueError("IoU and baseline must lie in [0,1]")
    p, r = list(predicted_betti), list(reference_betti)
    if len(p) != 3 or len(r) != 3 or any(type(v) is not int or v < 0 for v in p+r):
        raise ValueError("Betti counts must be three nonnegative integers")
    overlap = float(np.clip((x-x0)/(1-x0),0,1)) if x0 < 1 else float(x >= 1)
    topology = math.prod(((min(a,b)+1)/(max(a,b)+1))**2 for a,b in zip(p,r))
    return {"chance_corrected_iou": overlap, "topology_count_score": topology,
            "part_v1_from_supplied_terms": .8*overlap+.2*topology,
            "official_geometry_pipeline_reproduced": False,
            "engineering_pass": None}


def feature_prf(matched, predicted_count, reference_count):
    """Counts must come from evaluator geometric matching, not model feature labels."""
    for x in (matched,predicted_count,reference_count):
        if type(x) is not int or x < 0:raise ValueError("Feature counts must be nonnegative integers")
    if matched > min(predicted_count,reference_count):raise ValueError("Invalid feature matching")
    if not predicted_count and not reference_count:return {"precision":None,"recall":None,"f1":None}
    p=matched/predicted_count if predicted_count else 0.
    r=matched/reference_count if reference_count else 0.
    return {"precision":p,"recall":r,"f1":2*p*r/(p+r) if p+r else 0.}


def essential_operation_recall(observed_executed_ops, required_ops):
    required=set(required_ops)
    return len(required.intersection(observed_executed_ops))/len(required) if required else None


def qoi_metrics(prediction, reference, *, atol, rtol, offset=0.):
    if any(isinstance(v,(bool,np.bool_)) or not isinstance(v,numbers.Real)
           for v in (prediction,reference,atol,rtol,offset)):
        raise ValueError("Scalar quantities must be real numbers, not booleans or strings")
    p,r=finite([prediction,reference]);a,b=finite([atol,rtol])
    if a<0 or b<0:raise ValueError("Tolerances must be nonnegative")
    offset=float(finite([offset])[0]);absolute=abs(p-r);denom=abs(r-offset)
    limit=a+b*denom
    return {"absolute_error":float(absolute),
            "relative_error":float(absolute/denom) if denom else None,
            "tolerance_normalized_error":float(absolute/limit) if limit else (0. if absolute==0 else None),
            "positive_log_ratio_error":float(abs(math.log(p/r))) if p>0 and r>0 else None,
            "absolute_tolerance":float(a),"relative_tolerance":float(b),"offset":offset,
            "within_tolerance":bool(absolute<=limit)}


def field_metrics(prediction, reference, weights):
    """Volume/area/time-weighted comparison on the SAME evaluator grid and field basis."""
    p,r,w=finite(prediction),finite(reference),finite(weights)
    if p.shape!=r.shape or p.ndim not in (1,2) or w.shape!=(len(r),) or np.any(w<=0):
        raise ValueError("Field/grid/weight mismatch or nonpositive integration weights")
    e=(p-r).reshape(len(r),-1);ref=r.reshape(len(r),-1)
    numerator=float(np.sum(w[:,None]*e**2));denominator=float(np.sum(w[:,None]*ref**2))
    return {"weighted_relative_l2":math.sqrt(numerator/denominator) if denominator>0 else None,
            "weighted_absolute_l2":math.sqrt(numerator),
            "weighted_rmse":math.sqrt(numerator/(w.sum()*e.shape[1])),
            "max_pointwise_vector_error":float(np.max(np.linalg.norm(e,axis=1))),
            "relative_l2_defined":denominator>0,"evaluation_points":len(r),"coverage":1.0}


def energy_error(prediction, reference, reference_stiffness):
    p,r=finite(prediction),finite(reference)
    if p.ndim!=1 or p.shape!=r.shape:raise ValueError("Energy metric requires equal free-DOF vectors")
    k=finite(reference_stiffness)
    if k.shape!=(len(r),len(r)) or not np.allclose(k,k.T):raise ValueError("Reference stiffness must be symmetric")
    np.linalg.cholesky(k)  # Small evaluator operators only; excludes null/rigid-body DOFs.
    e=p-r;num=float(e@k@e);den=float(r@k@r)
    return {"relative_energy_error":math.sqrt(max(0,num)/den) if den>0 else None,
            "absolute_energy_error":math.sqrt(max(0,num))}


def weighted_quantile(values, weights, quantile):
    v,w=finite(values),finite(weights)
    if v.ndim!=1 or w.shape!=v.shape or np.any(w<=0) or not 0<=quantile<=1:
        raise ValueError("Invalid weighted quantile inputs")
    order=np.argsort(v);vs,ws=v[order],w[order]
    return float(vs[min(len(vs)-1,np.searchsorted(np.cumsum(ws)/ws.sum(),quantile))])


def force_moment_balance(points, forces, couples, reference_length):
    x,f,c=finite(points),finite(forces),finite(couples)
    if x.shape!=f.shape or c.shape!=f.shape or x.ndim!=2 or x.shape[1]!=3:
        raise ValueError("Forces, couples and coordinates must be equal N x 3 arrays")
    length=positive(reference_length,"reference_length")
    force_scale=float(np.linalg.norm(f,axis=1).sum())
    moment_scale=length*force_scale+float(np.linalg.norm(c,axis=1).sum())
    net_f=f.sum(0);net_m=(np.cross(x,f)+c).sum(0)
    return {"net_force":net_f.tolist(),"net_moment":net_m.tolist(),
            "relative_force_imbalance":float(np.linalg.norm(net_f)/force_scale) if force_scale else None,
            "relative_moment_imbalance":float(np.linalg.norm(net_m)/moment_scale) if moment_scale else None}


def modal_assurance(prediction, reference, mass=None):
    p,r=finite(prediction),finite(reference)
    if p.ndim!=1 or p.shape!=r.shape:raise ValueError("Modes must share registered DOFs")
    if mass is None:inner=lambda a,b:float(a@b)
    else:
        m=finite(mass)
        if m.shape!=(len(r),len(r)) or not np.allclose(m,m.T):raise ValueError("Invalid mass operator")
        np.linalg.cholesky(m);inner=lambda a,b:float(a@m@b)
    den=inner(p,p)*inner(r,r)
    if den<=0:raise ValueError("Zero mode vector")
    return float(np.clip(inner(p,r)**2/den,0,1))


def convergence_diagnostic(mesh_sizes, quantities, safety_factor=1.25):
    h,q=finite(mesh_sizes),finite(quantities)
    if h.shape!=(3,) or q.shape!=(3,) or not h[0]>h[1]>h[2]>0:
        raise ValueError("Exactly three completed coarse-to-fine levels required")
    safety_factor=positive(safety_factor,"safety_factor")
    change=float(abs(q[2]-q[1])/abs(q[2])) if q[2] else None
    result={"finest_relative_change":change,"observed_order":None,"gci_fine":None,
            "convergence_certified":False,"richardson_assumptions_met":False}
    r0,r1=h[0]/h[1],h[1]/h[2];d0,d1=q[0]-q[1],q[1]-q[2]
    if not np.isclose(r0,r1,rtol=1e-5):result['reason']='unequal refinement ratios';return result
    if d0*d1<=0 or abs(d0)<=abs(d1):result['reason']='oscillatory, identical or noncontracting sequence';return result
    order=math.log(abs(d0/d1))/math.log(r0)
    result.update(observed_order=order,richardson_assumptions_met=True,
                  gci_fine=float(safety_factor*change/(r0**order-1)) if change is not None else None,
                  reason='Richardson model diagnostic only; requires same mode, setup and asymptotic-regime review')
    return result


def joint_verdict(gates, required, *, reference_ready, applicable=True):
    """Consumes evaluator-owned evidence ONLY. Missing review never becomes a pass."""
    if type(reference_ready) is not bool:raise ValueError("Reference readiness must be an evaluator boolean")
    if not reference_ready:return {"eligible":False,"joint_pass":None,"status":"reference_hold"}
    if not applicable:return {"eligible":False,"joint_pass":None,"status":"different_task_track"}
    if not required:raise ValueError("At least one required gate is necessary")
    values=[gates.get(k) for k in required]
    if any(v is not None and type(v) is not bool for v in values):raise ValueError("Gate values must be bool or null")
    failed=[k for k in required if gates.get(k) is False]
    missing=[k for k in required if gates.get(k) is None]
    return {"eligible":True,"joint_pass":not failed and not missing,
            "status":"failed_gate" if failed else ("unverified" if missing else "verified_pass"),
            "failed_gates":failed,"unverified_gates":missing}


def family_macro(rows, metric="joint_pass"):
    groups={}
    for row in rows:
        if not row['eligible']:continue
        if type(row.get(metric)) is not bool:raise ValueError("Eligible rows require a boolean metric")
        groups.setdefault(row['engineering_family'],[]).append(float(row[metric]))
    return {"family_macro":float(np.mean([np.mean(x) for x in groups.values()])) if groups else None,
            "task_micro":float(np.mean([v for x in groups.values() for v in x])) if groups else None,
            "families":len(groups),"tasks":sum(map(len,groups.values()))}


def proper_rotations():
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1,-1),repeat=3):
            m=np.zeros((3,3))
            for i in range(3):m[i,perm[i]]=signs[i]
            if np.linalg.det(m)>.5:yield m


def closest_points_on_triangles(p, a, b, c):
    """Exact closest point on triangle (a_i,b_i,c_i) to p_i, row-wise (Ericson, Real-Time Collision Detection, 5.1.5)."""
    dot=lambda x,y:np.einsum('ij,ij->i',x,y)
    ab,ac,bc=b-a,c-a,c-b
    d1,d2=dot(ab,p-a),dot(ac,p-a);d3,d4=dot(ab,p-b),dot(ac,p-b);d5,d6=dot(ab,p-c),dot(ac,p-c)
    va,vb,vc=d3*d6-d5*d4,d5*d2-d1*d6,d1*d4-d3*d2
    safe=lambda x:np.where(x==0,1.,x)
    denom=safe(va+vb+vc)
    out=a+ab*(vb/denom)[:,None]+ac*(vc/denom)[:,None]  # face interior
    # Voronoi regions, lowest priority first so the earlier tests of the reference algorithm win.
    for mask,point in [
        ((va<=0)&(d4-d3>=0)&(d5-d6>=0),lambda:b+bc*((d4-d3)/safe((d4-d3)+(d5-d6)))[:,None]),
        ((vb<=0)&(d2>=0)&(d6<=0),lambda:a+ac*(d2/safe(d2-d6))[:,None]),
        ((d6>=0)&(d5<=d6),lambda:c),
        ((vc<=0)&(d1>=0)&(d3<=0),lambda:a+ab*(d1/safe(d1-d3))[:,None]),
        ((d3>=0)&(d4<=d3),lambda:b),
        ((d1<=0)&(d2<=0),lambda:a)]:
        out=np.where(mask[:,None],point(),out)
    return out


class TriangleSurface:
    """Tessellated surface for exact point-to-surface distance.

    Long triangles are bisected so every triangle lies within `reach` of its centroid; a point's
    nearest centroid then bounds which triangles can hold its closest point, so pruning is exact."""
    def __init__(self, triangles, max_edge, max_triangles=3_000_000):
        tri=finite(triangles,"triangles")
        if tri.ndim!=3 or tri.shape[1:]!=(3,3):raise ValueError("Triangles must be T x 3 x 3")
        tri=tri[np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)>0]
        if not len(tri):raise ValueError("Empty tessellation")
        max_edge=positive(max_edge,"max_edge")
        while True:
            edges=np.linalg.norm(tri[:,[1,2,0]]-tri,axis=2)  # edge k joins vertex k to vertex k+1
            k=edges.argmax(1);long=edges[np.arange(len(tri)),k]>max_edge
            if not long.any():break
            t,k=tri[long],k[long];i=np.arange(len(t))
            v0,v1,v2=t[i,k],t[i,(k+1)%3],t[i,(k+2)%3];mid=(v0+v1)/2
            tri=np.concatenate([tri[~long],np.stack([v0,mid,v2],1),np.stack([mid,v1,v2],1)])
            if len(tri)>max_triangles:raise ValueError("Tessellation too large for exact distance evaluation")
        self.triangles=tri;centroids=tri.mean(1)
        self.reach=float(np.linalg.norm(tri-centroids[:,None],axis=2).max())
        normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);self.normals=normal/np.linalg.norm(normal,axis=1)[:,None]
        self.tree=cKDTree(centroids)

    def closest(self, points, max_pairs=2_000_000):
        """Distances, closest surface points and the unit normals of the triangles holding them."""
        q=finite(points,"points")
        nearest=self.tree.query(q)[0]+self.reach  # a centroid lies on the surface, so the answer is no farther
        counts=self.tree.query_ball_point(q,nearest,return_length=True)
        distance=np.empty(len(q));closest=np.empty_like(q);normal=np.empty_like(q);start=0
        while start<len(q):
            stop=start+max(1,int(np.searchsorted(np.cumsum(counts[start:]),max_pairs)))
            lists=self.tree.query_ball_point(q[start:stop],nearest[start:stop])
            n=np.fromiter(map(len,lists),int,len(lists));owner=np.repeat(np.arange(len(n)),n)
            index=np.concatenate(lists).astype(int);t=self.triangles[index];x=q[start:stop][owner]
            cp=closest_points_on_triangles(x,t[:,0],t[:,1],t[:,2]);d2=((cp-x)**2).sum(1)
            first=np.lexsort((d2,owner))[np.r_[0,np.cumsum(n)[:-1]]]
            distance[start:stop]=np.sqrt(d2[first]);closest[start:stop]=cp[first];normal[start:stop]=self.normals[index[first]];start=stop
        return distance,closest,normal


def tessellation(shape, tolerance):
    vertices,faces=shape.tessellate(tolerance)
    return np.array([x.toTuple() for x in vertices])[np.asarray(faces)]


def sample_triangles(tri, n, seed):
    areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
    if areas.sum()<=0:raise ValueError("Empty tessellation")
    rng=np.random.default_rng(seed);chosen=tri[rng.choice(len(tri),n,p=areas/areas.sum())]
    uv=rng.random((n,2));a=np.sqrt(uv[:,0]);b=uv[:,1]
    return (1-a[:,None])*chosen[:,0]+(a*(1-b))[:,None]*chosen[:,1]+(a*b)[:,None]*chosen[:,2]


def surface_for(tri):
    """Exact-distance surface; bisection length from the part's own size bounds the triangle count."""
    extent=tri.reshape(-1,3).max(0)-tri.reshape(-1,3).min(0)
    return TriangleSurface(tri,float(np.linalg.norm(extent))/100)


def read_step(path):
    """Every root of the STEP file (cq.importers.importStep(...).val() kept only the first body)."""
    import cadquery as cq
    from OCP.STEPControl import STEPControl_Reader
    reader=STEPControl_Reader()
    if int(reader.ReadFile(str(path)))!=1:raise ValueError("Unreadable STEP")
    reader.TransferRoots();one=reader.OneShape()
    if one.IsNull():raise ValueError("Empty STEP")
    shape=cq.Shape.cast(one)
    if not shape.isValid() or not shape.Solids() or shape.Volume()<=0:raise ValueError("Invalid or empty BRep")
    return shape


def centre_of_mass(shape):
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    props=GProp_GProps();BRepGProp.VolumeProperties_s(shape.wrapped,props);c=props.CentreOfMass()
    return np.array([c.X(),c.Y(),c.Z()])


def fit_pose(pred, ref, points, target, pred_tri, ref_surface, threshold, subsample=4000, iterations=30):
    """Best of 24 proper axis rotations about centre-of-mass alignment, then robust translation refinement.

    Bounding-box centres let one extra or missing feature shift the whole part; centre of mass moves far
    less. The refinement solves point-to-plane least squares over pairs within a cut-off that starts at
    10x the F1 threshold and shrinks to it, so pairs on an extra/missing feature drop out as the fit tightens."""
    cp,cr=centre_of_mass(pred),centre_of_mass(ref)
    P,Q=points[:subsample],target[:subsample];tree=cKDTree(Q);best=None
    for m in proper_rotations():
        p=P@m.T+cr-m@cp
        distance=float(tree.query(p)[0].mean()+cKDTree(p).query(Q)[0].mean())
        if best is None or distance<best[0]:best=(distance,m)
    rotation=best[1];P=P@rotation.T;translation=cr-rotation@cp
    candidate=surface_for(pred_tri@rotation.T)
    def residuals(t):
        dp,on_ref,n_ref=ref_surface.closest(P+t);dq,on_candidate,n_candidate=candidate.closest(Q-t)
        d=np.r_[dp,dq];v=np.r_[on_ref-(P+t),Q-(on_candidate+t)]  # moving the candidate by v closes each pair
        return d,v,np.r_[n_ref,n_candidate],float(np.mean(np.minimum(d,threshold)))
    d,v,n,score=residuals(translation);cutoff=max(10*threshold,2.5*float(np.median(d)));steps=0
    for _ in range(iterations):
        keep=d<=cutoff
        if keep.any():
            nk=n[keep];step=np.linalg.lstsq(nk.T@nk,nk.T@np.einsum('ij,ij->i',nk,v[keep]),rcond=1e-9)[0]
            trial=residuals(translation+step)
            if trial[3]<score:translation=translation+step;d,v,n,score=trial;steps+=1
        else:step=np.zeros(3)
        if cutoff==threshold and np.linalg.norm(step)<1e-4*threshold:break
        cutoff=max(threshold,.6*cutoff)
    return rotation,translation,steps


def geometry_metrics(candidate, reference, *, samples=20000, pose="fixed", voxel_resolution=0, threshold_fraction=.005):
    import cadquery as cq
    if samples<100:raise ValueError("At least 100 samples required")
    if pose not in ('fixed','translation_and_24_proper_rotations'):raise ValueError("Unsupported pose policy")
    ref=read_step(reference);bbox=ref.BoundingBox();diagonal=math.sqrt(bbox.xlen**2+bbox.ylen**2+bbox.zlen**2)
    report={"metric_version":"cadfem-metrics-0.1","workflow_verified":None,"candidate_valid":False,
            "pose_policy":pose,"rescaling_permitted":False,"reference_diagonal":diagonal,
            "reference_solids":len(ref.Solids()),"physical_units":"must match task/reference STEP import units",
            "distance_convention":"area-sampled points to the other part's tessellated surface (exact point-to-triangle)"}
    try:pred=read_step(candidate)
    except Exception as error:report['error']=str(error);return report
    report['candidate_valid']=True;report['candidate_solids']=len(pred.Solids())
    pred_tri,ref_tri=tessellation(pred,diagonal*1e-4),tessellation(ref,diagonal*1e-4)
    points,target=sample_triangles(pred_tri,samples,7),sample_triangles(ref_tri,samples,7)
    ref_surface=surface_for(ref_tri);rotation=np.eye(3);translation=np.zeros(3)
    if pose=='translation_and_24_proper_rotations':
        rotation,translation,steps=fit_pose(pred,ref,points,target,pred_tri,ref_surface,threshold_fraction*diagonal)
        report['pose_fit']={"initial_translation":"centre_of_mass","translation_refinement_steps":steps}
    transform=np.eye(4);transform[:3,:3]=rotation;transform[:3,3]=translation
    from OCP.gp import gp_Trsf
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    rigid=gp_Trsf()
    rigid.SetValues(*[float(x) for x in transform[:3,:].ravel()])
    moved=cq.Shape.cast(BRepBuilderAPI_Transform(pred.wrapped,rigid,True).Shape())
    dp=ref_surface.closest(points@rotation.T+translation)[0]
    dq=surface_for(pred_tri@rotation.T+translation).closest(target)[0]
    report.update(distance_summary(dp,dq,diagonal,threshold_fraction))
    report['candidate_to_reference_transform']=transform.tolist()
    a,b=moved.Volume(),ref.Volume();intersection=moved.intersect(ref).Volume()
    if not -1e-7*max(a,b)<=intersection<=min(a,b)+1e-7*max(a,b):raise ValueError("Invalid Boolean intersection volume")
    intersection=float(np.clip(intersection,0,min(a,b)))
    report.update(brep_volume_iou=intersection/(a+b-intersection),relative_volume_error=abs(a-b)/b,
                  relative_symmetric_difference=(a+b-2*intersection)/b,voxel_iou=None,
                  topology_verified=None,feature_fidelity_verified=None,
                  comparability='Physical-unit variant; not the independently normalized BenchCAD official score')
    if voxel_resolution:
        if not 4<=voxel_resolution<=128:raise ValueError("Voxel resolution must be 4..128")
        bb=moved.BoundingBox();lo=np.minimum([bb.xmin,bb.ymin,bb.zmin],[bbox.xmin,bbox.ymin,bbox.zmin]);hi=np.maximum([bb.xmax,bb.ymax,bb.zmax],[bbox.xmax,bbox.ymax,bbox.zmax])
        cell=float(max(hi-lo))/voxel_resolution;centre=(lo+hi)/2;start=centre-cell*voxel_resolution/2
        common=union=0
        for idx in itertools.product(range(voxel_resolution),repeat=3):
            x=tuple(start+(np.asarray(idx)+.5)*cell)
            inside_p=moved.isInside(x,1e-7);inside_r=ref.isInside(x,1e-7)
            common+=inside_p and inside_r;union+=inside_p or inside_r
        report.update(voxel_iou=common/union if union else None,voxel_resolution=voxel_resolution,voxel_cell_size=cell)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='kind',required=True)
    g=sub.add_parser('geometry');g.add_argument('--candidate',type=Path,required=True);g.add_argument('--reference',type=Path,required=True);g.add_argument('--samples',type=int,default=20000);g.add_argument('--pose',choices=['fixed','translation_and_24_proper_rotations'],default='fixed');g.add_argument('--voxel-resolution',type=int,default=0)
    f=sub.add_parser('fields');f.add_argument('--candidate',type=Path,required=True);f.add_argument('--reference',type=Path,required=True);f.add_argument('--field',required=True)
    for p in [g,f]:p.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.kind=='geometry':result=geometry_metrics(args.candidate,args.reference,samples=args.samples,pose=args.pose,voxel_resolution=args.voxel_resolution)
    else:
        with np.load(args.candidate,allow_pickle=False) as p,np.load(args.reference,allow_pickle=False) as r:
            # Never compare differently sampled meshes by array index.
            pp,rp=finite(p['evaluation_points']),finite(r['evaluation_points'])
            if pp.shape!=rp.shape or not np.array_equal(pp,rp):raise ValueError("Evaluator-registered common points required")
            if p['field_unit'].item()!=r['field_unit'].item() or p['coordinate_unit'].item()!=r['coordinate_unit'].item():raise ValueError("Field or coordinate units differ")
            if p['field_basis'].tolist()!=r['field_basis'].tolist():raise ValueError("Field component order/basis differs")
            result=field_metrics(p[args.field],r[args.field],r['weights'])
            result.update(field=args.field,field_unit=r['field_unit'].item(),workflow_verified=None,
                          note='Common-grid artifact diagnostic only; trusted interpolation/provenance must be verified separately')
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':main()
