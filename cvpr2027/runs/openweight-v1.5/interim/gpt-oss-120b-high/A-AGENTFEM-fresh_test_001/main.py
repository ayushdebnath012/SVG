"""AgentFEM bracket analysis for task A-AGENTFEM-fresh_test_001

This script reads the STEP geometry from the input directory, generates a quadratic
tetrahedral mesh using Gmsh with a nominal mesh size of 9 mm (as used by the
publisher), applies fixed boundary conditions on all faces lying in the plane
z = 0, applies a uniform downward pressure of 1.98728 MPa on the top seat face
(z = 189 mm) and solves the linear elastic problem using scikit‑fem.

The script produces the required artifact files:

- results.json               : contains the requested output quantities.
- part.step                  : a copy of the input geometry (the analysis
                               solid is unchanged).
- mesh.msh                   : the Gmsh mesh (quadratic tetrahedra).
- fields.npz                 : numpy archive with node coordinates and the
                               displacement vector (DOF values).
- solver.log                 : log of the solver steps.
- refinement.json            : basic information about the mesh used.
- environment.json           : software versions and modelling assumptions.
"""

import os
import sys
import json
import numpy as np
import gmsh
import meshio
import cadquery as cq
from skfem import asm, solve, enforce, Basis
from skfem.models.elasticity import linear_elasticity
from skfem.mesh import MeshTet2
from skfem.element import ElementTetP2
from skfem.element.element_vector import ElementVector

# ----------------------------------------------------------------------------
# Helper to write log output
log_file = open('solver.log', 'w')

def log(msg: str):
    print(msg)
    print(msg, file=log_file)
    log_file.flush()

# ----------------------------------------------------------------------------
# Paths
input_dir = os.getenv('CADFEM_INPUT_DIR')
if not input_dir:
    raise RuntimeError('CADFEM_INPUT_DIR not set')
geom_path = os.path.join(input_dir, 'geometry.step')

# ---------------------------------------------------------------------------
# 1. Copy the input STEP file to part.step (the analysis solid must be in mm)
#    The supplied STEP is already in mm, so a direct copy is sufficient.
import shutil
shutil.copyfile(geom_path, 'part.step')
log('Copied geometry.step to part.step')

# ---------------------------------------------------------------------------
# 2. Build the Gmsh mesh (quadratic tetrahedra, nominal size ~9 mm)
log('Initializing Gmsh')

gmsh.initialize()
gmsh.model.add('bracket')
# Import STEP geometry
log(f'Importing STEP geometry from {geom_path}')
shape_tags = gmsh.model.occ.importShapes(geom_path)
# Synchronize CAD kernel
gmsh.model.occ.synchronize()
# Identify the volume (there should be exactly one solid)
volumes = gmsh.model.getEntities(dim=3)
if not volumes:
    raise RuntimeError('No volume found in STEP file')
log(f'Found {len(volumes)} volume(s)')
# (Optional) assign a physical group for the volume for later reference
vol_tag = volumes[0][1]
# Set mesh size: nominal 9 mm
nominal_size = 9.0
gmsh.option.setNumber('Mesh.MeshSizeMax', nominal_size)
# Use quadratic (second order) elements
gmsh.option.setNumber('Mesh.ElementOrder', 2)
# Generate the 3‑D mesh
log('Generating 3‑D mesh')
# Ensure that the geometry is not too coarse; let Gmsh decide internals.
# The default behavior respects the MeshSizeMax above.

gmsh.model.mesh.generate(3)
# Write mesh to file
mesh_file = 'mesh.msh'
log(f'Writing mesh to {mesh_file}')

gmsh.write(mesh_file)
# Finalize Gmsh (release resources)

gmsh.finalize()
log('Gmsh finalised')

# ---------------------------------------------------------------------------
# 3. Load mesh with meshio and build a quadratic tetrahedral mesh for scikit‑fem
mesh_io = meshio.read(mesh_file)
# Extract points (shape (N,3)) and tetra10 connectivity
points = mesh_io.points.T  # (3, N)
# Find tetra10 cell block
cell_block = None
for block in mesh_io.cells:
    if block.type == 'tetra10':
        cell_block = block.data
        break
if cell_block is None:
    raise RuntimeError('No quadratic tetrahedral cells (tetra10) found in mesh')
# Convert to (10, Nelem) for scikit‑fem (transpose)
cells = cell_block.T
# Build MeshTet2 (quadratic tetrahedral mesh)
mesh = MeshTet2(points, cells)
log(f'Created MeshTet2: {mesh.nvertices} vertices, {mesh.nelements} elements')

# ---------------------------------------------------------------------------
# 4. Identify boundary facets for foot (z~0) and top seat (z~max)
# Retrieve boundary facet indices (triangular facets on the surface)
boundary_facets = mesh.boundary_facets()
log(f'Total boundary facets: {len(boundary_facets)}')
# Gather z‑coordinates of facet vertices
facet_node_ids = mesh.facets[:, boundary_facets]  # shape (3, Nfacets)
facet_z = mesh.p[2, facet_node_ids]  # (3, Nfacets)
# Tolerance for detecting planar faces (mm)
ztol = 1e-3
# Foot facets: all three vertices have |z| < ztol
foot_mask = np.all(np.abs(facet_z) < ztol, axis=0)
foot_facet_indices = boundary_facets[foot_mask]
log(f'Identified {len(foot_facet_indices)} foot facets (z~0)')
# Top seat facets: all three vertices have |z - max_z| < ztol
max_z = mesh.p[2, :].max()
top_mask = np.all(np.abs(facet_z - max_z) < ztol, axis=0)
top_facet_indices = boundary_facets[top_mask]
log(f'Identified {len(top_facet_indices)} top seat facets (z~{max_z:.3f})')

# ---------------------------------------------------------------------------
# 5. Finite element setup (vector displacement field)
vol_elem = ElementVector(ElementTetP2(), dim=3)
basis = Basis(mesh, vol_elem)
log(f'FEM basis: {basis.N} total DOFs')

# Material properties (E in MPa, ν dimensionless)
E = 70e3      # MPa
nu = 0.33
# Convert to Lamé parameters (MPa)
lam = (E * nu) / ((1 + nu) * (1 - 2 * nu))
mu = E / (2 * (1 + nu))
log(f'Lamé parameters: Lambda={lam:.3f} MPa, Mu={mu:.3f} MPa')

# Assemble stiffness matrix
log('Assembling stiffness matrix')
K = asm(linear_elasticity(Lambda=lam, Mu=mu), basis)

# ---------------------------------------------------------------------------
# 6. Assemble load vector from uniform pressure on top seat facets
# Pressure (MPa) acting downward (negative z direction)
pressure = 1.98728  # MPa
# Initialise load vector (global DOFs)
F = np.zeros(basis.N)
log('Assembling load vector from pressure')
for facet in top_facet_indices:
    # Node ids of the triangular facet
    nid = mesh.facets[:, facet]
    v0 = mesh.p[:, nid[0]]
    v1 = mesh.p[:, nid[1]]
    v2 = mesh.p[:, nid[2]]
    # Compute area vector (0.5 * cross(v1-v0, v2-v0)) – direction follows right-hand rule
    area_vec = 0.5 * np.cross(v1 - v0, v2 - v0)
    area = np.linalg.norm(area_vec)
    if area == 0:
        continue
    # Unit normal (may point inward or outward depending on facet orientation)
    n = area_vec / area
    # Determine sign based on the normal's z component (positive for outward on the top face)
    sign = np.sign(n[2]) if n[2] != 0 else 1.0
    # Traction vector: pressure acting downward = -p * outward_normal.
    # If the computed normal points inward (sign < 0) we flip the sign.
    traction = -pressure * n * sign
    # Lumped nodal forces: distribute equally to the three vertices
    force_per_node = traction * (area / 3.0)
    for node in nid:
        # The three displacement components share the same node index in the vector field
        for comp in range(3):
            dof_index = basis.dofs.nodal_dofs[comp, node]
            F[dof_index] += force_per_node[comp]
log('Load vector assembled')

# ---------------------------------------------------------------------------
# 7. Apply Dirichlet BC on foot facets (fixed all displacement components)
log('Applying Dirichlet boundary conditions on foot')
fixed_dofs = basis.dofs.get_facet_dofs(foot_facet_indices).all()
K_bc, F_bc = enforce(K, F, D=fixed_dofs)
log(f'Number of fixed DOFs: {len(fixed_dofs)}')

# ---------------------------------------------------------------------------
# 8. Solve linear system
log('Solving linear system')
U = solve(K_bc, F_bc)
log('Solver finished')

# ---------------------------------------------------------------------------
# 9. Post‑processing – compute required output quantities
# Vertex nodes (original geometric vertices) are the first nvertices entries
n_vert = mesh.nvertices
# Displacement components at vertex nodes (extracted from the DOF vector)
ux_vert = U[basis.dofs.nodal_dofs[0, :n_vert]]
uy_vert = U[basis.dofs.nodal_dofs[1, :n_vert]]
uz_vert = U[basis.dofs.nodal_dofs[2, :n_vert]]
# Identify vertices belonging to the top seat (z ~= max_z)
vert_z = mesh.p[2, :n_vert]
top_vertex_mask = np.abs(vert_z - max_z) < ztol
# Mean downward displacement (positive value) on top seat
seat_mean_disp = -np.mean(uz_vert[top_vertex_mask])
# Maximum displacement magnitude anywhere in the bracket (all vertices)
disp_mag = np.sqrt(ux_vert**2 + uy_vert**2 + uz_vert**2)
max_disp = np.max(disp_mag)
log(f'Seat mean displacement (mm): {seat_mean_disp:.6e}')
log(f'Max displacement (mm): {max_disp:.6e}')

# ---------------------------------------------------------------------------
# 10. Write results.json
results = {
    "outputs": {
        "seat_mean_displacement_mm": float(seat_mean_disp),
        "max_displacement_mm": float(max_disp)
    }
}
with open('results.json', 'w') as f:
    json.dump(results, f, indent=2)
log('Wrote results.json')

# ---------------------------------------------------------------------------
# 11. Write mesh.msh (already written by Gmsh) – ensure it exists in output dir
# (No further action needed; the file was created earlier.)

# ---------------------------------------------------------------------------
# 12. Write fields.npz – store node coordinates and the full displacement vector
np.savez('fields.npz', coordinates=mesh.p, displacement=U)
log('Wrote fields.npz')

# ---------------------------------------------------------------------------
# 13. Write refinement.json – include basic mesh information
refinement_info = {
    "mesh": {
        "type": "tetra10",
        "num_vertices": int(mesh.nvertices),
        "num_elements": int(mesh.nelements),
        "nominal_mesh_size_mm": nominal_size
    }
}
with open('refinement.json', 'w') as f:
    json.dump(refinement_info, f, indent=2)
log('Wrote refinement.json')

# ---------------------------------------------------------------------------
# 14. Write environment.json – software versions and modelling assumptions
env = {
    "software": {
        "python": sys.version.split(' ')[0],
        "gmsh": gmsh.__version__,
        "cadquery": cq.__version__,
        "skfem": __import__('skfem').__version__,
        "meshio": __import__('meshio').__version__,
    },
    "units": {
        "length": "mm",
        "stress": "MPa"
    },
    "material": {
        "E": E,
        "nu": nu,
        "lambda": lam,
        "mu": mu
    },
    "boundary_conditions": {
        "fixed": "all displacement components on faces with z≈0",
        "pressure": {
            "magnitude_MPa": pressure,
            "direction": "-z (downward)",
            "applied_to": "faces with z≈max_z"
        }
    },
    "mesh_assumptions": {
        "element_type": "quadratic tetrahedral (tetra10)",
        "nominal_size_mm": nominal_size,
        "order": 2
    }
}
with open('environment.json', 'w') as f:
    json.dump(env, f, indent=2)
log('Wrote environment.json')

log_file.close()
print('Analysis completed successfully.')
