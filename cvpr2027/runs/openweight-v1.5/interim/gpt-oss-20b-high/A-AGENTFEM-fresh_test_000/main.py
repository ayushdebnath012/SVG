import os, json, subprocess, numpy as np
from skfem import asm, solve, CellBasis, BoundaryFacetBasis, ElementVectorH1
from skfem.element.element_tet import ElementTetP2
from skfem.models.elasticity import linear_elasticity, lame_parameters
from skfem.io import meshio as sk_meshio
import skfem

# Path environment
CADFEM_INPUT_DIR = os.getenv('CADFEM_INPUT_DIR', '')
# Copy geometry step file to part.step
input_step = os.path.join(CADFEM_INPUT_DIR, 'geometry.step')
output_part_step = 'part.step'
with open(input_step, 'rb') as f_in:
    data = f_in.read()
with open(output_part_step, 'wb') as f_out:
    f_out.write(data)

# Helper to run mesh generation
def generate_mesh(clmax, order, output_file):
    cmd = [
        'gmsh',
        '--quiet',
        '-format', 'msh4',
        '-3',
        '-order', str(order),
        '-clmax', str(clmax),
        '-clmin', str(clmax),
        '-o', output_file,
        input_step
    ]
    subprocess.check_call(cmd)

# Mesh resolutions
meshes = {
    'coarse': {
        'clmax': 12,
        'order': 2,
        'output': 'mesh_coarse.msh'
    },
    'fine': {
        'clmax': 9,
        'order': 2,
        'output': 'mesh_fine.msh'
    }
}

# Store refinement results
refinement_results = {}

# Solver log content
solver_log_lines = []

for key, cfg in meshes.items():
    generate_mesh(cfg['clmax'], cfg['order'], cfg['output'])
    # Export fine mesh as mesh.msh for artifact requirement
    if key == 'fine':
        import shutil
        shutil.copy(cfg['output'], 'mesh.msh')
    # Load mesh
    sk_mesh = sk_meshio.from_file(cfg['output'], None)
    # Build finite element space
    E = ElementVectorH1(ElementTetP2())
    basis = CellBasis(sk_mesh, E)
    # Elasticity parameters
    E_mod = 70e3  # N/mm^2
    nu = 0.33
    Lambda, Mu = lame_parameters(E_mod, nu)
    elastic_form = linear_elasticity(Lambda, Mu)
    # Assemble stiffness
    K = asm(elastic_form, basis)

    # Load on top face
    z = sk_mesh.p[2]
    facets = sk_mesh.facets
    mask_top = np.all(np.abs(z[facets] - 189) < 1e-6, axis=0)
    face_basis = BoundaryFacetBasis(sk_mesh, E, facets=np.where(mask_top)[0])
    traction = np.array([0.0, 0.0, -1.98728])
    load = asm(lambda v, w: np.tensordot(traction, v, axes=([0],[0])), face_basis)

    # Dirichlet on bottom z=0
    bottom_mask = np.abs(sk_mesh.p[2,:]) < 1e-6
    bottom_nodes = np.where(bottom_mask)[0]
    # mapping raw node idx -> local
    raw_to_local = {raw: local for local, raw in enumerate(np.unique(sk_mesh.t))}
    fixed_dof = []
    for node in bottom_nodes:
        local = raw_to_local.get(node)
        if local is None:
            continue
        fixed_dof.extend(basis.dofs.nodal_dofs[:, local].tolist())
    fixed_dof = np.unique(fixed_dof)

    K_mod = K.tolil()
    K_mod[fixed_dof,:] = 0
    K_mod[:,fixed_dof] = 0
    K_mod[fixed_dof, fixed_dof] = 1
    f_mod = load.copy()
    f_mod[fixed_dof] = 0

    # Solve
    u = solve(K_mod, f_mod)

    # Displacements at nodes
    u_nodal = u[basis.dofs.nodal_dofs.reshape(-1)].reshape(-1,3)
    # seat mean displacement
    top_nodes_raw = np.where(np.abs(sk_mesh.p[2,:] - 189) < 1e-6)[0]
    top_nodes_local = np.array([raw_to_local.get(n) for n in top_nodes_raw if raw_to_local.get(n) is not None])
    top_disp = u_nodal[top_nodes_local, :]
    seat_mean_disp_mm = float(np.mean(-top_disp[:,2]))
    max_disp_mm = float(np.max(np.linalg.norm(u_nodal, axis=1)))

    # Record results
    refinement_results[key] = {
        'nodes': int(sk_mesh.p.shape[1]),
        'elements': int(sk_mesh.t.shape[1]),
        'seat_mean_displacement_mm': seat_mean_disp_mm,
        'max_displacement_mm': max_disp_mm
    }

    # Save fields for the fine mesh only
    if key == 'fine':
        node_ids = np.arange(u_nodal.shape[0], dtype=np.int32)
        coords = sk_mesh.p.T  # shape (N,3)
        displacements = u_nodal
        np.savez('fields.npz', node_ids=node_ids, coordinates=coords, displacements=displacements)
        # Write results.json
        results = {
            'outputs': {
                'seat_mean_displacement_mm': seat_mean_disp_mm,
                'max_displacement_mm': max_disp_mm
            }
        }
        with open('results.json', 'w') as f:
            json.dump(results, f)
        # Write solver log
        solver_log_lines.append(f"Mesh '{cfg['output']}' analysis ...")
        solver_log_lines.append(f"Nodes: {sk_mesh.p.shape[1]}, Elements: {sk_mesh.t.shape[1]}")
        solver_log_lines.append(f"Seat mean disp: {seat_mean_disp_mm:.6e} mm, Max disp: {max_disp_mm:.6e} mm")
        # Capture the solver matrix/x solution? not needed

# Write solver.log
with open('solver.log', 'w') as f:
    f.write('\n'.join(solver_log_lines))

# Write refinement.json
with open('refinement.json', 'w') as f:
    json.dump(refinement_results, f, indent=4)

# Write environment.json
environment = {
    'solver': 'skfem',
    'solver_version': skfem.__version__,
    'assembly': 'skfem.assembly',
    'mesh_generation': 'gmsh',
    'mesh_generation_command': f"gmsh --quiet -format msh4 -3 -order 2 -clmax 9 -clmin 9 -o mesh_fine.msh {input_step}",
    'units': {
        'length': 'mm',
        'force': 'N',
        'stress': 'MPa',
        'displacement': 'mm'
    },
    'field_schema': {
        'displacement': {
            'components': ['x', 'y', 'z'],
            'units': 'mm'
        },
        'seat_mean_displacement': {
            'units': 'mm'
        },
        'max_displacement': {
            'units': 'mm'
        }
    },
    'physical_group_mapping': {},
    'extraction_definitions': {
        'seat_mean_displacement_mm': 'average of displacements on top face (z = 189 mm)',
        'max_displacement_mm': 'maximum magnitude of displacement anywhere'
    },
    'modeling_assumptions': {
        'gravity': 'not applied',
        'material': 'linear isotropic elastic, E=70 GPa, nu=0.33'
    }
}
with open('environment.json', 'w') as f:
    json.dump(environment, f, indent=4)

print('Analysis completed.')
