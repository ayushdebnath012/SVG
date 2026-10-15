"""Small-strain, axisymmetric frictionless contact of the supplied hemisphere.
All dimensions are mm, forces N, and stresses MPa.  The full 2*pi factor
is included in the axisymmetric weak form, hence the load is 10000 N.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
import json
import math
import time
from pathlib import Path
import numpy as np
import cadquery as cq
import gmsh
from scipy.sparse.linalg import spsolve
from skfem import MeshTri, Basis, FacetBasis, ElementTriP1, ElementVector, BilinearForm, LinearForm, asm

E = 210000.0
nu = 0.3
F = 10000.0
lam = E * nu / ((1 + nu) * (1 - 2 * nu))
mu = E / (2 * (1 + nu))

@BilinearForm
def elasticity(u, v, w):
    r = w.x[0]
    du = u.grad[0, 0] + u.grad[1, 1] + u[0] / r
    dv = v.grad[0, 0] + v.grad[1, 1] + v[0] / r
    epsdot = (u.grad[0, 0] * v.grad[0, 0]
              + u.grad[1, 1] * v.grad[1, 1]
              + u[0] * v[0] / r**2
              + 0.5 * (u.grad[0, 1] + u.grad[1, 0]) * (v.grad[0, 1] + v.grad[1, 0]))
    return 2 * np.pi * r * (lam * du * dv + 2 * mu * epsdot)

@LinearForm
def loading(v, w):
    return -w.pressure * 2 * np.pi * w.x[0] * v[1]

def mesh_meridian(R, h):
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal', 0)
    gmsh.option.setNumber('General.NumThreads', 2)
    gmsh.model.add('hemisphere_meridian')
    g = gmsh.model.geo
    p0 = g.addPoint(0, 0, 0)
    pc = g.addPoint(0, R, 0)
    pr = g.addPoint(R, R, 0)
    axis = g.addLine(p0, pc)
    top = g.addLine(pc, pr)
    arc = g.addCircleArc(pr, pc, p0)
    loop = g.addCurveLoop([axis, top, arc])
    g.addPlaneSurface([loop])
    g.synchronize()
    # Locally uniform resolution in the whole contact zone, then a smooth
    # size transition into the remainder of the actual finite hemisphere.
    field = gmsh.model.mesh.field.add('MathEval')
    gmsh.model.mesh.field.setString(field, 'F',
        f'{h}+0.05*Max(0,Sqrt(x*x+y*y)-1.6)')
    gmsh.model.mesh.field.setAsBackgroundMesh(field)
    gmsh.option.setNumber('Mesh.MeshSizeFromPoints', 0)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature', 0)
    gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary', 0)
    gmsh.option.setNumber('Mesh.MeshSizeMax', 1.5)
    gmsh.option.setNumber('Mesh.Algorithm', 6)
    gmsh.model.mesh.generate(2)
    tags, xyz, _ = gmsh.model.mesh.getNodes()
    xyz = np.asarray(xyz).reshape(-1, 3)
    idx = np.argsort(tags)
    tags = np.asarray(tags)[idx]
    xy = xyz[idx, :2].T
    _, elem = gmsh.model.mesh.getElementsByType(2)
    tri = np.searchsorted(tags, np.asarray(elem).reshape(-1, 3)).T
    ct, _, _ = gmsh.model.mesh.getNodes(1, arc, includeBoundary=True)
    contact = np.unique(np.searchsorted(tags, ct))
    gmsh.finalize()
    return MeshTri(xy, tri), contact

def solve_contact(R, h):
    start = time.time()
    mesh, cb = mesh_meridian(R, h)
    basis = Basis(mesh, ElementVector(ElementTriP1()), intorder=4)
    K = asm(elasticity, basis).tocsc()
    top = mesh.facets_satisfying(lambda x: np.isclose(x[1], R, atol=1e-8))
    fb = FacetBasis(mesh, basis.elem, facets=top)
    f = asm(loading, fb, pressure=F / (np.pi * R**2))
    # The only artificial constraints remove the nonphysical radial rigid
    # mode on the axis. No vertical or radial support is placed at the top.
    axis = np.where(np.abs(mesh.p[0]) < 1e-9)[0]
    fixed_radial = 2 * axis
    cb = cb[np.argsort(mesh.p[0, cb])]
    cdofs = 2 * cb + 1
    gap0 = mesh.p[1, cb]
    rr = mesh.p[0, cb]
    # Lumped surface test-function integrals, evaluated on the horizontal
    # projection. These convert nodal normal reactions into pressure.
    weights = np.zeros(len(cb))
    for i in range(len(cb) - 1):
        r0, r1 = rr[i:i+2]
        dr = r1 - r0
        weights[i] += 2 * np.pi * dr * (r0 / 2 + dr / 6)
        weights[i+1] += 2 * np.pi * dr * (r0 / 2 + dr / 3)
    ah = (3 * F * R * (1 - nu**2) / (4 * E))**(1/3)
    active = rr < ah
    all_dofs = np.arange(basis.N)
    for it in range(60):
        D = np.r_[fixed_radial, cdofs[active]]
        u = np.zeros(basis.N)
        u[cdofs[active]] = -gap0[active]
        free = np.setdiff1d(all_dofs, D, assume_unique=False)
        u[free] = spsolve(K[free][:, free], (f - K @ u)[free])
        reaction = K @ u - f
        gap = gap0 + u[cdofs]
        # Primal-dual active-set / semismooth Newton update.
        pd = reaction[cdofs] / weights
        new_active = pd - (E / h) * gap > 0
        if np.array_equal(active, new_active):
            break
        active = new_active
    else:
        raise RuntimeError('Contact active set did not converge')
    pressure = reaction[cdofs] / weights
    n = int(np.sum(active))
    a_low = float(np.max(rr[active]))
    a_high = float(np.min(rr[~active]))
    # Away from the edge, Hertz pressure squared is linear in r^2.
    # Fitting it over the resolved interior gives an edge estimate without
    # the O(h) ambiguity of the last contacting mesh node.
    fit = active & (rr <= 0.85 * a_low)
    coef = np.polyfit(rr[fit]**2, pressure[fit]**2, 1)
    afit = float(np.sqrt(-coef[1] / coef[0]))
    pfit = float(np.sqrt(coef[1]))
    pmax = float(np.max(pressure[active]))
    out = dict(mesh_size_mm=h, vertices=int(mesh.nvertices),
        elements=int(mesh.nelements), iterations=it+1,
        contact_radius_bracket_mm=[a_low, a_high],
        fitted_contact_radius_mm=afit, fitted_peak_pressure_MPa=pfit,
        nodal_peak_pressure_MPa=pmax, total_contact_force_N=float(np.sum(reaction[cdofs])),
        applied_force_N=float(-np.sum(f[1::2])),
        minimum_gap_mm=float(np.min(gap)),
        minimum_active_pressure_MPa=float(np.min(pressure[active])),
        elapsed_seconds=time.time()-start)
    print(json.dumps(out), flush=True)
    np.savetxt(f'contact_h{h:.3f}.csv', np.c_[rr, gap0, u[cdofs], gap, pressure, active],
               delimiter=',', header='r_mm,z_mm,uz_mm,gap_mm,pressure_MPa,active', comments='')
    return out

def main():
    inp = Path(os.environ.get('CADFEM_INPUT_DIR', 'inputs'))
    solid = cq.importers.importStep(str(inp / 'hemisphere.step')).val()
    bbox = solid.BoundingBox()
    R = 0.5 * bbox.xlen
    assert abs(R-50) < 1e-5 and abs(bbox.zmin) < 1e-5
    assert abs(solid.Volume() - 2*np.pi*R**3/3) < 1e-3
    exact_a = (3*F*R*(1-nu**2)/(4*E))**(1/3)
    exact_p = 3*F/(2*np.pi*exact_a**2)
    convergence = [solve_contact(R, h) for h in [0.02, 0.01, 0.005]]
    final = convergence[-1]
    for run in convergence:
        assert abs(run['total_contact_force_N'] - F) < 1e-4 * F
        assert run['minimum_gap_mm'] > -1e-8
        assert run['minimum_active_pressure_MPa'] >= -1e-5
    for key in ['fitted_contact_radius_mm', 'fitted_peak_pressure_MPa']:
        assert abs(final[key] / convergence[-2][key] - 1) < 0.002
    results = {'outputs': {
        'contact_radius_mm': final['fitted_contact_radius_mm'],
        'max_contact_pressure_MPa': final['fitted_peak_pressure_MPa']}}
    Path('results.json').write_text(json.dumps(results, indent=2)+'\n')
    Path('analysis.json').write_text(json.dumps({
        'method':'Axisymmetric P1 displacement finite elements; unilateral rigid frictionless contact, primal-dual active set; full finite hemisphere',
        'pressure_recovery':'Normal nodal reaction divided by projected axisymmetric tributary area; least-squares pressure-squared fit over inner 85% of contact radius to recover peak and sub-element edge',
        'radius_mm':R, 'E_MPa':E, 'nu':nu, 'force_N':F,
        'Hertz_halfspace_reference':{'contact_radius_mm':exact_a,'max_contact_pressure_MPa':exact_p},
        'mesh_convergence':convergence}, indent=2)+'\n')

if __name__ == '__main__':
    main()
