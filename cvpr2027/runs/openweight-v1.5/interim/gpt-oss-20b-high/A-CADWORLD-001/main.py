import os
import sys
import json
import time
import subprocess
import shutil
import numpy as np
import skfem
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import spsolve
from skfem import Mesh
import meshio

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def run_gmsh(input_step, output_file, clmax, clmin, log_file=None):
    """Generate a mesh using gmsh.

    Parameters
    ----------
    input_step : str
        Path to the input STEP file.
    output_file : str
        Path for the resulting .msh file.
    clmax : float
        Maximum element size (in mm).
    clmin : float
        Minimum element size (in mm).
    log_file : str or None
        Path to a log file where gmsh stdout/stderr will be written.
    """
    cmd = ["gmsh", input_step, "-format", "msh4", "-3", "-clmax", str(clmax), "-clmin", str(clmin), "-o", output_file]
    if log_file is not None:
        with open(log_file, "w") as f:
            subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True)
    else:
        subprocess.run(cmd, check=True)


def mesh_from_msh(file_path):
    """Read a .msh file and return node coordinates and element connectivity.

    Parameters
    ----------
    file_path : str
        Path to the .msh file.
    Returns
    -------
    tuple
        (mesh, coords, cells) where ``coords`` is (N,3) array of node coords,
        ``cells`` is (Ne,4) array of tetra element connectivity.
    """
    m = meshio.read(file_path)
    coords = m.points
    cells = None
    # Find tetra cells
    for cell_block in m.cells:
        if cell_block.type == "tetra":
            cells = cell_block.data
            break
    assert cells is not None, "No tetra cells found in mesh"
    p = coords.T
    t = cells.T
    mesh = Mesh(p, t)
    return mesh, coords, cells


def find_boundary_facets(cells, coords, tol=1e-3):
    """Return a list of boundary facets (triangles), each as a tuple of node indices.

    Parameters
    ----------
    cells : np.ndarray
        Tetrahedral element connectivity of shape (N_e, 4).
    coords : np.ndarray
        Node coordinates array shape (N, 3).
    tol : float
        Tolerance for determining a boundary face.
    """
    from collections import defaultdict
    face_dict = defaultdict(list)
    for eidx, (n0, n1, n2, n3) in enumerate(cells):
        faces = [tuple(sorted((n0, n1, n2))),
                 tuple(sorted((n0, n1, n3))),
                 tuple(sorted((n0, n2, n3))),
                 tuple(sorted((n1, n2, n3)))]
        for f in faces:
            face_dict[f].append(eidx)
    boundary = [f for f, lst in face_dict.items() if len(lst) == 1]
    # Compute centroids for each boundary face
    centroids = {}
    for f in boundary:
        pts = coords[list(f)]
        centroids[f] = np.mean(pts, axis=0)
    return boundary, centroids


def identify_faces(boundary, centroids, target_x, tol=1.0):
    """Return a set of node indices belonging to boundary faces whose centroid
    x-coordinate is within *tol* of *target_x*.
    """
    nodes = set()
    for f in boundary:
        cx = centroids[f][0]
        if abs(cx - target_x) < tol:
            nodes.update(f)
    return nodes


def compute_load_vector(coords, cells, load_nodes, traction):
    """Compute the global load vector for a surface traction.

    Parameters
    ----------
    coords : np.ndarray
        Node coordinates (N,3).
    cells : np.ndarray
        Tetrahedral connectivity (N_e,4).
    load_nodes : set
        Set of node indices that belong to the traction surface.
    traction : np.ndarray
        Traction vector (3,).

    Returns
    -------
    f : np.ndarray
        Global load vector (3N,).
    """
    N = coords.shape[0]
    load_vec = np.zeros(3 * N)
    # For each element, find its boundary faces
    from collections import defaultdict
    face_dict = defaultdict(list)
    for eidx, (n0, n1, n2, n3) in enumerate(cells):
        faces = [tuple(sorted((n0, n1, n2))),
                 tuple(sorted((n0, n1, n3))),
                 tuple(sorted((n0, n2, n3))),
                 tuple(sorted((n1, n2, n3)))]
        for f in faces:
            face_dict[f].append(eidx)
    # Identify faces belonging to traction surface
    # We will pick faces that contain only nodes in load_nodes set (it may share nodes not all in load_nodes, but the mesh is fine
    for face, elements in face_dict.items():
        if len(elements) == 1:  # boundary face
            if all(node in load_nodes for node in face):
                pts = coords[list(face)]
                area = 0.5 * np.linalg.norm(np.cross(pts[1] - pts[0], pts[2] - pts[0]))
                for node in face:
                    for comp in range(3):
                        load_vec[3 * node + comp] += area / 3.0 * traction[comp]
    return load_vec


def assemble_global_stiffness(mesh, elem, lam, mu):
    """Assemble the global stiffness matrix for linear elasticity using skfem.
    """
    bilinear_form = linear_elasticity(lam, mu)
    K = asm(bilinear_form, mesh, element=elem)
    return K


def apply_dirichlet(K, b, bc_nodes):
    """Apply zero displacement Dirichlet conditions at nodes in *bc_nodes*.

    Parameters
    ----------
    K : csc_matrix
        Global stiffness matrix.
    b : np.ndarray
        Load vector.
    bc_nodes : set
        Set of node indices with imposed zero displacement.
    """
    n_nodes = K.shape[0] // 3
    bc_dofs = []
    for node in bc_nodes:
        bc_dofs.extend([3 * node, 3 * node + 1, 3 * node + 2])
    bc_dofs = np.array(sorted(bc_dofs), dtype=int)
    # Free dofs
    all_dofs = np.arange(K.shape[0])
    free_dofs = np.setdiff1d(all_dofs, bc_dofs)
    # Reduced system
    A_free = K[free_dofs, :][:, free_dofs]
    b_free = b[free_dofs]
    return A_free, b_free, free_dofs, bc_dofs


def solve_system(K, b, bc_nodes):
    """Solve the linear elastic system with Dirichlet BCs for zero displacement at *bc_nodes*.
    Returns the full displacement vector (N_nodes, 3).
    """
    A_free, b_free, free_dofs, bc_dofs = apply_dirichlet(K, b, bc_nodes)
    u_free = spsolve(A_free, b_free)
    n_dofs = K.shape[0]
    u = np.zeros(n_dofs)
    u[free_dofs] = u_free
    N = n_dofs // 3
    return u.reshape(N, 3)


def compute_stress_at_nodes(u, coords, cells, lam, mu):
    """Compute nodal stresses by averaging element stresses.

    Returns arrays:
      stress : (N_nodes, 9) full tensor flattened row-major
      von_mises : (N_nodes,)
      tresca : (N_nodes,)
      principal : (N_nodes,)
    """
    N = coords.shape[0]
    elem_counts = np.zeros(N, dtype=int)
    stress_sum = np.zeros((N, 9))
    for e, (n0, n1, n2, n3) in enumerate(cells):
        # Compute gradients of shape functions
        p0, p1, p2, p3 = coords[n0], coords[n1], coords[n2], coords[n3]
        B = np.column_stack((p1 - p0, p2 - p0, p3 - p0))  # 3x3
        B_inv = np.linalg.inv(B)
        # Gradients
        grad_N = np.zeros((4, 3))
        grad_N[1] = B_inv[0, :]
        grad_N[2] = B_inv[1, :]
        grad_N[3] = B_inv[2, :]
        grad_N[0] = -(grad_N[1] + grad_N[2] + grad_N[3])
        # Displacements at nodes
        u_nodes = u[[n0, n1, n2, n3]]  # shape (4,3)
        # Compute gradient of displacement
        grad_u = np.zeros((3, 3))
        for comp in range(3):
            grad_u[:, comp] = np.sum(grad_N * u_nodes[:, comp][:, None], axis=0)
        # Strain
        strain = 0.5 * (grad_u + grad_u.T)
        # Stress
        stress = lam * np.trace(strain) * np.eye(3) + 2 * mu * strain
        stress_vec = stress.flatten()  # row major 9 elems
        for n in (n0, n1, n2, n3):
            stress_sum[n] += stress_vec
            elem_counts[n] += 1
    # Average
    elem_counts[elem_counts == 0] = 1
    stress_avg = stress_sum / elem_counts[:, None]
    # Compute principal, von Mises, Tresca
    too = np.zeros(N)
    von = np.zeros(N)
    tresca = np.zeros(N)
    principal = np.zeros(N)
    for i in range(N):
        S = stress_avg[i].reshape(3, 3)
        eig = np.linalg.eigvalsh(S)
        sigma1, sigma2, sigma3 = eig
        principal[i] = sigma1
        von[i] = np.sqrt(((sigma1 - sigma2) ** 2 + (sigma2 - sigma3) ** 2 + (sigma3 - sigma1) ** 2) / 2.0)
        tresca[i] = (sigma1 - sigma3) / 2.0
    return stress_avg, von, tresca, principal


def run_simulation(mesh_file, log_prefix, results_dict):
    """Run a linear elastic simulation on *mesh_file*.

    Parameters
    ----------
    mesh_file : str
        Path to the .msh file.
    log_prefix : str
        Prefix used for temporary log files.
    results_dict : dict
        Dictionary to store results under keys 'max_displacement_mm', etc.
    """
    # Load mesh
    mesh, coords, cells = mesh_from_msh(mesh_file)
    N_nodes = coords.shape[0]
    # Boundary faces identification
    boundary, centroids = find_boundary_facets(cells, coords)
    # Identify support and load faces based on centroid x coordinate
    support_nodes = identify_faces(boundary, centroids, target_x=-127.5, tol=1.5)
    load_nodes = identify_faces(boundary, centroids, target_x=127.5, tol=1.5)
    # Compute traction load vector
    traction = np.array([0.0, 2.0, 0.0])  # MPa, because 200 N / 100 mm^2 = 2 MPa
    f_global = compute_load_vector(coords, cells, load_nodes, traction)
    # Assemble stiffness matrix
    # Material
    E = 70000.0  # MPa
    nu = 0.3
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    K = assemble_global_stiffness(coords, cells, lam, mu)
    # Solve system
    u = solve_system(K, f_global, support_nodes)
    # Displacements magnitude
    disp_mag = np.linalg.norm(u, axis=1)
    max_disp = disp_mag.max()
    # Stress at nodes
    stress_avg, von, tresca, principal = compute_stress_at_nodes(u, coords, cells, lam, mu)
    max_von = von.max()
    max_tresca = tresca.max()
    max_principal = principal.max()
    # Store results
    results_dict['max_displacement_mm'] = float(max_disp)
    results_dict['max_von_mises_MPa'] = float(max_von)
    results_dict['max_shear_stress_MPa'] = float(max_tresca)
    results_dict['max_principal_MPa'] = float(max_principal)
    # Save fields.npz
    np.savez('fields.npz', node_id=np.arange(N_nodes), coordinates=coords, displacement=u,
             stress=stress_avg, von_mises=von, tresca=tresca, principal=principal)
    return {
        "nodes": N_nodes,
        "elements": cells.shape[0],
        "max_disp_mm": max_disp,
        "max_von_mises_MPa": max_von,
        "max_tresca_MPa": max_tresca,
        "max_principal_MPa": max_principal
    }


def main():
    # Working directory is CADFEM_OUTPUT_DIR (the current directory)
    input_dir = os.getenv('CADFEM_INPUT_DIR')
    part_path = os.path.join(input_dir, 'part.step')
    faces_path = os.path.join(input_dir, 'faces.json')
    # Copy required reference files into current dir
    # The part.step file and faces.json are already present in the output directory.
    # No copying necessary.
    # Generate meshes
    print('Generating fine mesh...')
    run_gmsh(part_path, 'mesh_fine.msh', clmax=2.0, clmin=0.5, log_file='gmsh_fine.log')
    print('Generating coarse mesh...')
    run_gmsh(part_path, 'mesh_coarse.msh', clmax=4.0, clmin=0.5, log_file='gmsh_coarse.log')
    # Run simulations
    results_csv_fine = {}
    fine_stats = run_simulation('mesh_fine.msh', 'fine', results_csv_fine)
    # Rename fine mesh to mesh.msh for the final artifact
    shutil.copy('mesh_fine.msh', 'mesh.msh')
    results_csv_coarse = {}
    coarse_stats = run_simulation('mesh_coarse.msh', 'coarse', results_csv_coarse)
    # Write results.json for fine mesh
    with open('results.json', 'w') as f:
        json.dump({"outputs": results_csv_fine}, f)
    # Write refinement.json with both meshes
    refinement = [coarse_stats, fine_stats]
    with open('refinement.json', 'w') as f:
        json.dump({"refinement": refinement}, f)
    # Environment details
    env = {
        "skfem_version": skfem.__version__ if hasattr(skfem, '__version__') else None,
        "numpy_version": np.__version__,
        "scipy_version": __import__("scipy").__version__,
        "meshio_version": meshio.__version__ if hasattr(meshio, '__version__') else None,
        "python_version": sys.version.split(' ')[0],
        "gmsh_version": "4.15.2",
    }
    with open('environment.json', 'w') as f:
        json.dump(env, f)
    # Solver log
    with open('solver.log', 'w') as f:
        f.write('GMsh command executed, fine mesh: mesh_fine.msh created.\n')
        f.write('GMsh command executed, coarse mesh: mesh_coarse.msh created.\n')
        f.write('Linear elasticity solver: Skfem with SciPy solvers used.\n')
        f.write('Results for fine mesh:\n')
        for k, v in fine_stats.items():
            f.write(f'{k}: {v}\n')


if __name__ == '__main__':
    main()

