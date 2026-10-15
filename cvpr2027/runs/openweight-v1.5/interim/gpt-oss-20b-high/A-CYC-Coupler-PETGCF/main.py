import gmsh, os, numpy as np, skfem
from skfem.mesh import MeshTet
from skfem.element import ElementTetP1, ElementVector
import skfem.models.elasticity as me
from scipy.sparse.linalg import spsolve
import json, shutil, time, scipy

# Working directories
input_dir = os.getenv('CADFEM_INPUT_DIR', '')
part_step_path = os.path.join(input_dir, 'part.step')
# Copy part.step to output directory
shutil.copy(part_step_path, 'part.step')

# Material properties
E = 3000.0  # MPa
nu = 0.36
lam = (E * nu) / ((1 + nu) * (1 - 2 * nu))
mu = E / (2 * (1 + nu))

# Load data
load_face_index = 14
load_total_force = 100.052  # N
load_area_mm2 = 267.272  # mm^2
load_per_node = load_total_force / 3.0  # N per node for uniform traction

# Fixed faces
fixed_faces = [5, 6]

# Mesh parameters
mesh_sizes = {
    'coarse': 4.0,   # mm (maximum element size)
    'fine': 1.0      # mm
}

# Function to build mesh and solve
def build_and_solve(mesh_size, write_mesh=False):
    gmsh.initialize()
    gmsh.merge(part_step_path)
    # Create physical groups with tags equal to face indices
    for f in fixed_faces + [load_face_index]:
        gmsh.model.addPhysicalGroup(2, [f], tag=f)
    gmsh.option.setNumber('Mesh.MeshSizeMax', mesh_size)
    gmsh.model.mesh.generate(3)
    if write_mesh:
        gmsh.write('mesh.msh')
    # Gather mesh data before finalizing gmsh
    node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
    load_tags = gmsh.model.mesh.getNodesForPhysicalGroup(2, load_face_index)[0]
    fixed5_tags = gmsh.model.mesh.getNodesForPhysicalGroup(2, fixed_faces[0])[0]
    fixed6_tags = gmsh.model.mesh.getNodesForPhysicalGroup(2, fixed_faces[1])[0]
    # Collect element connectivity for tetrahedra (element type 4 in gmsh)
    elem_types, elem_tags, elem_nodes = gmsh.model.mesh.getElements(3)
    # Find the index of the tetrahedral element type (4)
    # In practice gmsh returns a single element type list
    tet_nodes = elem_nodes[0]
    num_tets = tet_nodes.shape[0] // 4
    # Convert node coordinates to (3, N) array for skfem
    p = node_coords.reshape(-1, 3).T
    # Build node mapping tag->index
    nodemap = {tag: i for i, tag in enumerate(node_tags)}
    # Create connectivity array (4, num_tets)
    t = np.zeros((4, num_tets), dtype=int)
    for i in range(num_tets):
        t[:, i] = [nodemap[n] for n in tet_nodes[4 * i:4 * (i + 1)]]
    gmsh.finalize()
    # Build skfem MeshTet
    mesh = MeshTet(p, t)
    elem = ElementTetP1()
    elem_vec = ElementVector(elem, dim=3)
    basis = skfem.Basis(mesh, elem_vec)
    # Assemble stiffness matrix
    K = me.linear_elasticity(Lambda=lam, Mu=mu).assemble(basis)
    N = K.shape[0]
    # Apply load as nodal force: constant traction on load face
    f = np.zeros(N)
    for tag in load_tags:
        idx = nodemap[tag]
        f[3 * idx] += load_per_node
    # Apply Dirichlet BC by removing DOFs on fixed faces
    fixed_nodes = set(fixed5_tags.tolist() + fixed6_tags.tolist())
    fixed_dofs = np.concatenate([np.arange(3 * i, 3 * i + 3) for i in fixed_nodes])
    free_dofs = np.setdiff1d(np.arange(N), fixed_dofs)
    Kff = K[free_dofs, :][:, free_dofs]
    fl = f[free_dofs]
    # Solve system
    u = np.zeros(N)
    start = time.time()
    u[free_dofs] = spsolve(Kff, fl)
    solve_time = time.time() - start
    # Compute max displacement magnitude
    disp_vec = u.reshape(-1, 3)
    max_disp = np.max(np.linalg.norm(disp_vec, axis=1))
    # Save displacements to fields.npz (only for fine mesh)
    if write_mesh:
        coords = p.T
        node_ids = np.array(node_tags, dtype=int)
        np.savez_compressed('fields.npz', node_ids=node_ids, coordinates=coords, displacements=disp_vec)
    # Collect statistics for refinement.json
    stats = {
        'nodes': len(node_tags),
        'elements': t.shape[1],
        'max_displacement_mm': max_disp,
        'solve_time_s': solve_time
    }
    return stats

# Run coarse and fine meshes
stats_coarse = build_and_solve(mesh_sizes['coarse'], write_mesh=False)
stats_fine = build_and_solve(mesh_sizes['fine'], write_mesh=True)

# Write results.json
results = {
    'outputs': {
        'max_displacement_mm': stats_fine['max_displacement_mm']
    }
}
with open('results.json', 'w') as f:
    json.dump(results, f, indent=2)

# Write refinement.json
refinement = {
    'coarse': {
        'mesh_size_mm': mesh_sizes['coarse'],
        'nodes': stats_coarse['nodes'],
        'elements': stats_coarse['elements'],
        'max_displacement_mm': stats_coarse['max_displacement_mm']
    },
    'fine': {
        'mesh_size_mm': mesh_sizes['fine'],
        'nodes': stats_fine['nodes'],
        'elements': stats_fine['elements'],
        'max_displacement_mm': stats_fine['max_displacement_mm']
    }
}
with open('refinement.json', 'w') as f:
    json.dump(refinement, f, indent=2)

# Write solver.log
solver_log = []
solver_log.append(f"Gmsh version: {gmsh.__version__}")
solver_log.append(f"NumPy version: {np.__version__}")
solver_log.append(f"SciPy version: {scipy.__version__}")
solver_log.append(f"skfem version: {skfem.__version__}")
solver_log.append("")
solver_log.append("=== Coarse mesh summary ===")
solver_log.append(f"Mesh size (max element): {mesh_sizes['coarse']} mm")
solver_log.append(f"Nodes: {stats_coarse['nodes']}")
solver_log.append(f"Elements: {stats_coarse['elements']}")
solver_log.append(f"Max displacement: {stats_coarse['max_displacement_mm']} mm")
solver_log.append("")
solver_log.append("=== Fine mesh summary (solution) ===")
solver_log.append(f"Mesh size (max element): {mesh_sizes['fine']} mm")
solver_log.append(f"Nodes: {stats_fine['nodes']}")
solver_log.append(f"Elements: {stats_fine['elements']}")
solver_log.append(f"Solve time: {stats_fine['solve_time_s']:.6f} s")
solver_log.append(f"Max displacement: {stats_fine['max_displacement_mm']} mm")
solver_log.append("")
solver_log.append("Solver terminated successfully.")
with open('solver.log', 'w') as f:
    f.write('\n'.join(solver_log))

# Write environment.json
environment = {
    'solver': {
        'name': 'spsolve from scipy.sparse.linalg',
        'scipy_version': scipy.__version__
    },
    'meshing_tool': {
        'name': 'gmsh',
        'version': gmsh.__version__
    },
    'cad_file': 'part.step',
    'physical_groups': {
        'fixed_faces': fixed_faces,
        'load_face': [load_face_index]
    },
    'units': {
        'length': 'mm',
        'force': 'N',
        'stiffness': 'MPa',
        'displacement': 'mm'
    },
    'material': {
        'E': E,
        'nu': nu
    },
    'finite_element': {
        'type': 'P1 tetrahedral',
        'vector_displacement': True
    },
    'mesh_size_target_mm': mesh_sizes['fine'],
    'load_application': {
        'type': 'uniform traction',
        'face': load_face_index,
        'total_force_N': load_total_force,
        'area_mm2': load_area_mm2,
        'direction': [1.0, 0.0, 0.0]
    },
    'modeling_assumptions': {
        'gravity': False,
        'contact': False,
        'small_displacements': True,
        'linear_elasticity': True
    },
    'field_schema': {
        'node_ids': 'Array of node tags from gmsh (int)',
        'coordinates': 'N x 3 array of coordinates in mm (float)',
        'displacements': 'N x 3 array of displacements in mm (float)'
    }
}
with open('environment.json', 'w') as f:
    json.dump(environment, f, indent=2)

print('Computation completed. Results written.')
