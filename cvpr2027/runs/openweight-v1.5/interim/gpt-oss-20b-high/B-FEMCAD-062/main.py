import os, sys
import numpy as np
import meshio
import gmsh
import scipy.sparse
from scipy.sparse.linalg import spsolve
import math, json, shutil

# Material properties
E = 210000.0
nu = 0.3
lam = E * nu / ((1 + nu) * (1 - 2 * nu))
mu = E / (2 * (1 + nu))

# Geometry: plate 0<=x<=100, 0<=y<=5, 0<=z<=50, cylindrical hole radius 10 at (50, 25) along y.
x_min, x_max = 0.0, 100.0
y_min, y_max = 0.0, 5.0
z_min, z_max = 0.0, 50.0

# Build part.step with CadQuery
try:
    import cadquery as cq
except Exception as e:
    print('CadQuery not available:', e)
    sys.exit(1)

box = cq.Workplane('XY').box(x_max - x_min, y_max - y_min, z_max - z_min, centered=False)
cyl = cq.Workplane('XZ').center(50.0, 25.0).circle(10.0).extrude(5.0)
plate = box.cut(cyl)
plate.val().exportStep('part.step')

# Mesh generation

def generate_mesh(step_file, mesh_file, mesh_size):
    gmsh.initialize()
    gmsh.option.setNumber('General.Verbosity', 0)
    gmsh.model.add('plate')
    gmsh.model.occ.importShapes(step_file)
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber('Mesh.MeshSizeMax', mesh_size)
    gmsh.model.mesh.generate(3)
    gmsh.write(mesh_file)
    gmsh.finalize()

# SOLVER

def solve_fem(mesh_file):
    mesh = meshio.read(mesh_file)
    points = mesh.points
    cells = mesh.cells_dict['tetra']
    num_nodes, _ = points.shape
    num_dofs = num_nodes * 3

    # Boundary conditions: nodes with x==0 fixed
    fixed_node_mask = np.abs(points[:, 0]) < 1e-8
    fixed_dofs_mask = np.repeat(fixed_node_mask, 3)
    free_dofs_mask = ~fixed_dofs_mask
    free_dof_indices = np.arange(num_dofs)[free_dofs_mask]
    free_map = -np.ones(num_dofs, dtype=int)
    free_map[free_dof_indices] = np.arange(len(free_dof_indices))

    K = scipy.sparse.lil_matrix((len(free_dof_indices), len(free_dof_indices)), dtype=np.float64)
    F = np.zeros(len(free_dof_indices), dtype=np.float64)

    # Elasticity matrix D
    D = np.zeros((6,6))
    for i in range(3):
        D[i,i] = lam + 2*mu
        for j in range(i+1,3):
            D[i,j] = lam
            D[j,i] = lam
    for i in range(3,6):
        D[i,i] = mu

    # Traction: uniform traction of 1000 N total on x=100 face
    traction_pressure = 1000.0 / (5.0 * 50.0)  # 4 MPa

    def element_stiffness(verts):
        A = np.ones((4,4))
        A[:,1:] = verts
        invA = np.linalg.inv(A)
        grads = invA[1:,:].T
        B = np.zeros((6,12))
        for j in range(4):
            g = grads[j]
            col = 3*j
            B[0,col] = g[0]
            B[1,col+1] = g[1]
            B[2,col+2] = g[2]
            B[3,col] = g[1]
            B[3,col+1] = g[0]
            B[4,col+1] = g[2]
            B[4,col+2] = g[1]
            B[5,col] = g[2]
            B[5,col+2] = g[0]
        J = verts[1:] - verts[0]
        vol = abs(np.linalg.det(np.c_[J[0], J[1], J[2]])) / 6.0
        Ke = vol * B.T @ D @ B
        return Ke

    # Assemble system
    for elem in cells:
        verts = points[elem]
        Ke = element_stiffness(verts)
        gdofs = np.empty(12, dtype=int)
        gdofs[0::3] = elem * 3
        gdofs[1::3] = elem * 3 + 1
        gdofs[2::3] = elem * 3 + 2
        for i_local, gi in enumerate(gdofs):
            if fixed_dofs_mask[gi]:
                continue
            row = free_map[gi]
            for j_local, gj in enumerate(gdofs):
                if fixed_dofs_mask[gj]:
                    continue
                col = free_map[gj]
                K[row,col] += Ke[i_local, j_local]

    # Traction load on face x=100
    for tri in mesh.cells_dict.get('triangle', []):
        node_ids = tri
        x_vals = points[node_ids,0]
        if np.allclose(x_vals, 100.0, atol=1e-6):
            p0, p1, p2 = points[node_ids]
            area = 0.5 * np.linalg.norm(np.cross(p1-p0, p2-p0))
            load_per_node = traction_pressure * area / 3.0
            for nid in node_ids:
                dof = nid * 3
                if not fixed_dofs_mask[dof]:
                    F[free_map[dof]] += load_per_node

    # Solve linear system
    u_free = spsolve(K.tocsr(), F)
    u = np.zeros(num_dofs)
    u[free_dof_indices] = u_free

    # Compute von Mises stress per element and nodal von Mises average
    vm_elements = []
    vm_per_node = np.zeros(num_nodes)
    cnt_node = np.zeros(num_nodes, dtype=int)
    for elem in cells:
        verts = points[elem]
        # B matrix
        A = np.ones((4,4))
        A[:,1:] = verts
        invA = np.linalg.inv(A)
        grads = invA[1:,:].T
        B = np.zeros((6,12))
        for j in range(4):
            g = grads[j]
            col = 3*j
            B[0,col] = g[0]
            B[1,col+1] = g[1]
            B[2,col+2] = g[2]
            B[3,col] = g[1]
            B[3,col+1] = g[0]
            B[4,col+1] = g[2]
            B[4,col+2] = g[1]
            B[5,col] = g[2]
            B[5,col+2] = g[0]
        gdofs = np.empty(12, dtype=int)
        gdofs[0::3] = elem * 3
        gdofs[1::3] = elem * 3 + 1
        gdofs[2::3] = elem * 3 + 2
        u_elem = u[gdofs]
        strain = B @ u_elem
        stress = D @ strain
        sm = stress
        vm = math.sqrt((sm[0]-sm[1])**2 + (sm[1]-sm[2])**2 + (sm[2]-sm[0])**2 + 6*(sm[3]**2 + sm[4]**2 + sm[5]**2)) / math.sqrt(2)
        vm_elements.append(vm)
        for node in elem:
            vm_per_node[node] += vm
            cnt_node[node] += 1
    vm_per_node /= cnt_node
    max_vm = max(vm_elements)

    return {
        'max_vm': max_vm,
        'num_elements': len(cells),
        'num_nodes': num_nodes,
        'points': points,
        'displacement': u.reshape((num_nodes,3)),
        'vonmises': vm_per_node
    }

# Main execution
mesh_file_coarse = 'mesh_coarse.msh'
mesh_size_coarse = 10.0
generate_mesh('part.step', mesh_file_coarse, mesh_size_coarse)

mesh_file_mid = 'mesh_mid.msh'
mesh_size_mid = 0.8
generate_mesh('part.step', mesh_file_mid, mesh_size_mid)

mesh_file_fine = 'mesh_fine.msh'
mesh_size_fine = 0.75
generate_mesh('part.step', mesh_file_fine, mesh_size_fine)

res_coarse = solve_fem(mesh_file_coarse)
res_mid = solve_fem(mesh_file_mid)
res_fine = solve_fem(mesh_file_fine)

# Use the finest result for reporting
res = res_fine
print('Max von Mises MPa:', res['max_vm'])
print('Elements:', res['num_elements'], 'Nodes:', res['num_nodes'])

# Save artifacts
results = {'outputs': {'max_von_mises_MPa': res['max_vm']}}
with open('results.json', 'w') as fh:
    json.dump(results, fh, indent=2)

# Copy fine mesh as mesh.msh
shutil.copyfile(mesh_file_fine, 'mesh.msh')

# fields.npz
np.savez('fields.npz', node_ids=np.arange(res['num_nodes']), coordinates=res['points'], displacement=res['displacement'], vonmises=res['vonmises'])

# solver.log
with open('solver.log', 'w') as fh:
    fh.write(f"Python version: {sys.version}\n")
    fh.write(f"gmsh version: {gmsh.__version__}\n")
    fh.write(f"meshio version: {meshio.__version__}\n")
    fh.write(f"Solver: scipy.sparse.linalg.spsolve\n")
    fh.write(f"Displacement degrees of freedom: {res['num_nodes']*3}\n")
    fh.write(f"Max von Mises: {res['max_vm']} MPa\n")

# refinement.json
refinement = [
    {"mesh_size_mm": mesh_size_coarse, "num_elements": res_coarse['num_elements'], "num_nodes": res_coarse['num_nodes'], "max_von_mises_MPa": res_coarse['max_vm']},
    {"mesh_size_mm": mesh_size_mid, "num_elements": res_mid['num_elements'], "num_nodes": res_mid['num_nodes'], "max_von_mises_MPa": res_mid['max_vm']},
    {"mesh_size_mm": mesh_size_fine, "num_elements": res_fine['num_elements'], "num_nodes": res_fine['num_nodes'], "max_von_mises_MPa": res_fine['max_vm']}
]
with open('refinement.json', 'w') as fh:
    json.dump({"refinements": refinement}, fh, indent=2)

# environment.json
env = {
    "skfem_version": None,
    "meshio_version": meshio.__version__,
    "python_version": sys.version.split()[0],
    "gmsh_version": gmsh.__version__,
    "solver": "scipy.sparse.linalg.spsolve",
    "unit_displacement": "mm",
    "unit_stress": "MPa",
    "field_mapping": {
        "node_ids": "node indices",
        "coordinates": "float64 [n_nodes,3] mm",
        "displacement": "float64 [n_nodes,3] mm",
        "vonmises": "float64 [n_nodes] MPa"
    },
    "physical_group_mapping": {
        "fixed_surface": "x=0",
        "traction_surface": "x=100"
    }
}
with open('environment.json', 'w') as fh:
    json.dump(env, fh, indent=2)

print('All artifacts generated')
