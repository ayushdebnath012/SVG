"""Independent P2 FEM reference for Astra's convective-plate task.

Weak form: integral grad(T).grad(v) + integral_Robin 5*T*v = 0.
Left edge T=100; ambient=0; conductivity normalized to one. This is a
dimensionless-coordinate 2-D benchmark, not a material-specific design analysis.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import skfem
from skfem import MeshTri, Basis, FacetBasis, ElementTriP2, BilinearForm, asm, condense, solve
from skfem.models.poisson import laplace


def fem(n, all_three=True):
    mesh = MeshTri.init_tensor(np.linspace(0, 2, 2*n+1), np.linspace(0, 1, n+1))
    basis = Basis(mesh, ElementTriP2())
    facets = mesh.facets_satisfying(lambda x: np.isclose(x[0], 2) | (
        (np.isclose(x[1], 0) | np.isclose(x[1], 1)) if all_three else np.zeros(x.shape[1], dtype=bool)))
    boundary = FacetBasis(mesh, basis.elem, facets=facets)
    @BilinearForm
    def robin(u, v, w): return 5*u*v
    R = asm(robin, boundary); A = asm(laplace, basis) + R
    D = basis.get_dofs(lambda x: np.isclose(x[0], 0)).all()
    prescribed = basis.zeros(); prescribed[D] = 100
    start = time.perf_counter()
    u = solve(*condense(A, basis.zeros(), x=prescribed, D=D))
    residual = A@u
    convection = float(np.sum(R@u)); reaction = float(np.sum(residual[D]))
    free = np.setdiff1d(np.arange(basis.N), D)
    metrics = {'n': n, 'elements': int(mesh.nelements), 'dofs': int(basis.N),
               'solve_seconds': time.perf_counter()-start,
               'free_residual_max': float(np.max(np.abs(residual[free]))),
               'convective_outflow_over_k': convection, 'left_reaction_inflow_over_k': reaction,
               'discrete_heat_balance_relative': abs(reaction-convection)/abs(convection)}
    return basis, u, metrics


def probe(basis, u, points):
    return np.concatenate([basis.probes(points[:, i:i+128])@u for i in range(0, points.shape[1], 128)])


def main():
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--fd-reference', type=Path)
    a = p.parse_args(); a.output.mkdir(parents=True, exist_ok=True)
    b, u, anchor = fem(8, all_three=False)
    exact = 100*(1-5*b.doflocs[0]/11)
    anchor['max_error_linear_manufactured_C'] = float(np.max(np.abs(u-exact)))
    assert anchor['max_error_linear_manufactured_C'] < 1e-8
    gx, gy = np.linspace(0, 2, 161), np.linspace(0, 1, 81)
    X, Y = np.meshgrid(gx, gy); points = np.array([X.ravel(), Y.ravel()])
    fields, meshes = [], []
    for n in (12, 24, 48, 96, 192):
        b, u, metrics = fem(n)
        field = probe(b, u, points).reshape(X.shape)
        metrics.update(min_temperature_C=float(field.min()), max_temperature_C=float(field.max()))
        assert metrics['discrete_heat_balance_relative'] < 1e-8
        assert field.min() >= -0.1 and field.max() <= 100.1
        fields.append(field); meshes.append(metrics)
        np.savez_compressed(a.output/f'mesh-{n}.npz', points=b.mesh.p, triangles=b.mesh.t,
                            doflocs=b.doflocs, temperature_dofs=u, x=gx, y=gy, field=field)
        print('FEM', json.dumps(metrics), flush=True)
    differences = []
    for i in range(len(fields)-1):
        delta = np.abs(fields[i+1]-fields[i])
        differences.append({'coarse_n': meshes[i]['n'], 'fine_n': meshes[i+1]['n'],
                            'max_C': float(delta.max()), 'mean_C': float(delta.mean()),
                            'rms_C': float(np.sqrt(np.mean(delta**2)))})
    np.savez_compressed(a.output/'plate_convective_edges.npz', x=gx, y=gy, field=fields[-1])
    report = {'solver': 'scikit-fem P2 triangular Galerkin', 'skfem_version': skfem.__version__,
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'problem': {'domain': [0, 2, 0, 1], 'left_C': 100, 'ambient_C': 0, 'h_over_k': 5},
              'anchor': anchor, 'meshes': meshes, 'mesh_differences': differences,
              'notes': ['Mesh differences estimate numerical sensitivity, not certified error bounds.',
                        'Global balance uses the assembled boundary reaction.',
                        'Mixed-boundary corner singularities can slow convergence.',
                        'Stored regular grid adds interpolation error to SVG auditing.']}
    if a.fd_reference:
        from scipy.interpolate import RegularGridInterpolator
        z = np.load(a.fd_reference)
        fd = RegularGridInterpolator((z['y'], z['x']), z['field'])(np.c_[Y.ravel(), X.ravel()]).reshape(X.shape)
        delta = np.abs(fd-fields[-1])
        report['historical_fd_difference_C'] = {'max': float(delta.max()), 'mean': float(delta.mean())}
    (a.output/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4))
    levels = [10, 20, 40, 60, 80]
    contours = ax.contour(X, Y, fields[-1], levels=levels)
    ax.clabel(contours, fmt='%g °C'); ax.set_aspect('equal')
    ax.set(xlabel='x', ylabel='y', title='Independent FEM: heat conduction with three convective edges')
    fig.tight_layout(); fig.savefig(a.output/'reference.png', dpi=180)
    fig.savefig(a.output/'reference.svg'); plt.close(fig)
    print('REFERENCE COMPLETE', json.dumps(differences), flush=True)


if __name__ == '__main__': main()
