import os
import sys
import shutil
import json
import numpy as np
import gmsh
import skfem
from skfem import Mesh, Basis, asm, solve
from skfem.element import ElementTetP2
from skfem import ElementVector
from skfem.models.elasticity import lame_parameters, linear_elasticity
from skfem import LinearForm

def generate_mesh(mesh_size, filename, geom_path):
    """Generate a quadratic tetrahedral mesh using Gmsh.
    mesh_size: target mesh size (max) in mm.
    filename: output .msh filename.
    geom_path: path to STEP geometry.
    """
    gmsh.initialize()
    gmsh.model.add('bracket')
    gmsh.merge(geom_path)
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber('Mesh.ElementOrder', 2)
    gmsh.option.setNumber('Mesh.MeshSizeMax', mesh_size)
    gmsh.model.mesh.generate(3)
    if os.path.exists(filename):
        os.remove(filename)
    gmsh.write(filename)
    gmsh.finalize()
    return filename

def solve_mesh(mesh_file, compute_fields=True):
    # Material parameters
    E = 70e3
    nu = 0.33
    lam, mu = lame_parameters(E, nu)
    # Load mesh
    m = Mesh.load(mesh_file)
    vec_elem = ElementVector(ElementTetP2())
    vol_basis = Basis(m, vec_elem)
    # Determine top and bottom Z using vertex coordinates (first nvertices entries)
    nverts = m.nvertices
    vertex_z = m.p[2, :nverts]
    top_z = vertex_z.max()
    bottom_z = vertex_z.min()
    # Identify top facets for traction load
    boundary_facet_ids = m.boundary_facets()
    facet_nodes = m.facets
    z_coords = m.p[2, facet_nodes]
    centroids_z = z_coords.mean(axis=0)
    top_facets = boundary_facet_ids[np.isclose(centroids_z[boundary_facet_ids], top_z, atol=1e-3)]
    load_basis = vol_basis.boundary(facets=top_facets)
    # Assemble stiffness matrix
    a = linear_elasticity(lam, mu)
    K = asm(a, vol_basis)
    # Traction (negative Z)
    traction = np.array([0.0, 0.0, -1.98728])
    @LinearForm
    def neumann(v, w):
        return v[0] * traction[0] + v[1] * traction[1] + v[2] * traction[2]
    f = asm(neumann, load_basis)
    # Dirichlet BC on bottom vertices (fixed)
    vertex_indices = np.arange(nverts)
    bottom_vertices = vertex_indices[np.isclose(vertex_z, bottom_z, atol=1e-3)]
    fixed_dofs = vol_basis.dofs.nodal_dofs[:, bottom_vertices].reshape(-1)
    # Apply BC by modifying matrix and RHS
    from scipy.sparse import lil_matrix
    K_mod = K.tolil()
    K_mod[fixed_dofs, :] = 0
    K_mod[:, fixed_dofs] = 0
    K_mod[fixed_dofs, fixed_dofs] = 1
    b = f.copy()
    b[fixed_dofs] = 0
    K_mod = K_mod.tocsr()
    u = solve(K_mod, b)
    # Compute displacement magnitudes
    ux = u[::3]
    uy = u[1::3]
    uz = u[2::3]
    mag = np.sqrt(ux**2 + uy**2 + uz**2)
    max_disp = mag.max()
    # Mean seat displacement (top vertices)
    top_vertices = vertex_indices[np.isclose(vertex_z, top_z, atol=1e-3)]
    uz_top_dofs = vol_basis.dofs.nodal_dofs[2, top_vertices]
    seat_mean_disp = -u[uz_top_dofs].mean()
    if compute_fields:
        np.savez('fields.npz', coords=m.p, disp=u)
    return seat_mean_disp, max_disp, m, u

def mesh_stats(m):
    return {"num_nodes": int(m.p.shape[1]), "num_elements": int(m.t.shape[1])}

def main():
    log = open('solver.log', 'w')
    sys.stdout = log
    sys.stderr = log
    input_dir = os.getenv('CADFEM_INPUT_DIR')
    if not input_dir:
        raise RuntimeError('CADFEM_INPUT_DIR not set')
    geom_path = os.path.join(input_dir, 'geometry.step')
    shutil.copyfile(geom_path, 'part.step')
    # Coarse mesh (9 mm)
    coarse_mesh_file = 'mesh.msh'
    generate_mesh(9.0, coarse_mesh_file, geom_path)
    seat_coarse, max_coarse, m_coarse, u_coarse = solve_mesh(coarse_mesh_file, compute_fields=True)
    # Fine mesh (5 mm) for refinement data
    fine_mesh_file = 'mesh_fine.msh'
    generate_mesh(5.0, fine_mesh_file, geom_path)
    seat_fine, max_fine, m_fine, u_fine = solve_mesh(fine_mesh_file, compute_fields=False)
    # Write results.json
    results = {"outputs": {"seat_mean_displacement_mm": float(seat_coarse),
                           "max_displacement_mm": float(max_coarse)}}
    with open('results.json', 'w') as f:
        json.dump(results, f, indent=2)
    # Write refinement.json
    refinement = {"resolutions": [
        {"mesh_size_mm": 9.0,
         "mesh_info": mesh_stats(m_coarse),
         "seat_mean_displacement_mm": float(seat_coarse),
         "max_displacement_mm": float(max_coarse)},
        {"mesh_size_mm": 5.0,
         "mesh_info": mesh_stats(m_fine),
         "seat_mean_displacement_mm": float(seat_fine),
         "max_displacement_mm": float(max_fine)}
    ]}
    with open('refinement.json', 'w') as f:
        json.dump(refinement, f, indent=2)
    # Write environment.json
    import platform
    env = {
        "software": {
            "python": platform.python_version(),
            "gmsh_api_version": f"{gmsh.GMSH_API_VERSION_MAJOR}.{gmsh.GMSH_API_VERSION_MINOR}.{gmsh.GMSH_API_VERSION_PATCH}",
            "skfem_version": skfem.__version__,
            "numpy_version": np.__version__
        },
        "units": {"length": "mm", "stress": "MPa", "force": "N"},
        "modeling_assumptions": {
            "linear_elastic": True,
            "small_displacements": True,
            "material": {"E": 70000, "nu": 0.33},
            "boundary_conditions": {
                "fixed_bottom": "zero displacement on faces at z=0",
                "traction_top": {"t_z": -1.98728}
            }
        }
    }
    with open('environment.json', 'w') as f:
        json.dump(env, f, indent=2)
    # Write a brief summary to the solver log
    print("Completed analysis")
    print(f"Seat mean displacement (coarse): {seat_coarse} mm")
    print(f"Max displacement (coarse): {max_coarse} mm")
    log.close()

if __name__ == '__main__':
    main()
