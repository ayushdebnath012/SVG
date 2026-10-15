import json, os
import gmsh
import numpy as np
import meshio
import skfem
import skfem.io.meshio as smo
from skfem.helpers import dot, grad
from skfem import asm
from skfem.element import ElementTetP1
from scipy.sparse.linalg import spsolve


def build_geometry_and_part(step_file='part.step'):
    """Build the spherical capacitor geometry and write part.step."""
    if os.path.exists(step_file):
        os.remove(step_file)
    gmsh.initialize()
    gmsh.model.add('shell')
    outer = gmsh.model.occ.addSphere(0,0,0,10.0)  # radius in mm
    inner = gmsh.model.occ.addSphere(0,0,0,3.0)
    gmsh.model.occ.cut([(3, outer)], [(3, inner)], removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    # Identify inner and outer surfaces via bounding box diameter
    inner_surf = None
    outer_surf = None
    for surf in gmsh.model.getEntities(2):
        bbox = gmsh.model.getBoundingBox(2, surf[1])
        pmin = np.array(bbox[:3])
        pmax = np.array(bbox[3:])
        width = (pmax[0]-pmin[0] + pmax[1]-pmin[1] + pmax[2]-pmin[2]) / 3
        if abs(width - 6.0) < 1e-6:  # inner sphere diameter 6 mm
            inner_surf = surf[1]
        if abs(width - 20.0) < 1e-6:  # outer sphere diameter 20 mm
            outer_surf = surf[1]
    if inner_surf is None or outer_surf is None:
        raise RuntimeError('Could not find inner or outer surfaces.')
    gmsh.model.addPhysicalGroup(2, [inner_surf], name='charged')
    gmsh.model.addPhysicalGroup(2, [outer_surf], name='grounded')
    vol = gmsh.model.getEntities(3)[0][1]
    gmsh.model.addPhysicalGroup(3, [vol], name='dielectric')
    gmsh.write(step_file)
    gmsh.finalize()


def generate_mesh(mesh_file, mesh_size_mm):
    """Generate mesh of a given characteristic length and write to mesh_file."""
    gmsh.initialize()
    gmsh.model.add('shell')
    outer = gmsh.model.occ.addSphere(0,0,0,10.0)
    inner = gmsh.model.occ.addSphere(0,0,0,3.0)
    gmsh.model.occ.cut([(3, outer)], [(3, inner)], removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    # Identify surfaces for physical groups
    inner_surf = None
    outer_surf = None
    for surf in gmsh.model.getEntities(2):
        bbox = gmsh.model.getBoundingBox(2, surf[1])
        pmin = np.array(bbox[:3])
        pmax = np.array(bbox[3:])
        width = (pmax[0]-pmin[0] + pmax[1]-pmin[1] + pmax[2]-pmin[2]) / 3
        if abs(width - 6.0) < 1e-6:
            inner_surf = surf[1]
        if abs(width - 20.0) < 1e-6:
            outer_surf = surf[1]
    gmsh.model.addPhysicalGroup(2, [inner_surf], name='charged')
    gmsh.model.addPhysicalGroup(2, [outer_surf], name='grounded')
    vol = gmsh.model.getEntities(3)[0][1]
    gmsh.model.addPhysicalGroup(3, [vol], name='dielectric')
    gmsh.option.setNumber('Mesh.MeshSizeMax', mesh_size_mm)
    gmsh.model.mesh.generate(3)
    gmsh.write(mesh_file)
    gmsh.finalize()


def solve_mesh(mesh_file):
    """Solve electrostatic problem on given mesh and return relevant data."""
    mesh = meshio.read(mesh_file)
    mesh_tet = smo.from_meshio(mesh)
    V = skfem.Basis(mesh_tet, ElementTetP1())
    eps = 3.9 * 8.854187817e-12
    f = skfem.BilinearForm(lambda u, v, w: dot(grad(u), grad(v)) * eps)
    K = asm(f, V)
    inner_nodes = set()
    outer_nodes = set()
    for fid in mesh_tet.boundaries['charged']:
        inner_nodes.update(mesh_tet.facets[:, fid])
    for fid in mesh_tet.boundaries['grounded']:
        outer_nodes.update(mesh_tet.facets[:, fid])
    Dn = sorted(inner_nodes | outer_nodes)
    vals = np.zeros(len(Dn))
    for idx, node in enumerate(Dn):
        if node in inner_nodes:
            vals[idx] = 1.0
    b = np.zeros(K.shape[0])
    A_lil = K.tolil()
    for idx, val in zip(Dn, vals):
        A_lil[idx, :] = 0.0
        A_lil[idx, idx] = 1.0
        b[idx] = val
    phi = spsolve(A_lil.tocsr(), b)
    pts_mm = mesh_tet.p
    pts = pts_mm / 1000.0
    T = mesh_tet.t
    phi_E = phi[T]
    grad_phi = np.zeros((3, T.shape[1]), dtype=float)
    for e in range(T.shape[1]):
        nodes = T[:, e]
        p = pts[:, nodes]
        A_mat = np.column_stack([np.ones(4), p.T])
        Ainv = np.linalg.inv(A_mat)
        grad_N = Ainv[1:, :]
        grad_phi[:, e] = grad_N @ phi_E[:, e]
    volumes = np.zeros(T.shape[1])
    for e in range(T.shape[1]):
        nodes = T[:, e]
        p = pts[:, nodes]
        vol = np.abs(np.linalg.det(np.column_stack([p[:, 1]-p[:, 0], p[:, 2]-p[:, 0], p[:, 3]-p[:, 0]]))) / 6
        volumes[e] = vol
    W = 0.5 * eps * np.sum((grad_phi**2).sum(0) * volumes)
    C = 2 * W  # Farads
    C_pF = C * 1e12
    return {"C_pF": C_pF, "phi": phi, "coords_mm": pts_mm, "n_nodes": pts_mm.shape[1], "n_elems": T.shape[1]}


if __name__ == "__main__":
    # Build part step file
    build_geometry_and_part('part.step')
    # Generate coarse mesh (2.0 mm characteristic length)
    generate_mesh('mesh_coarse.msh', 2.0)
    # Generate fine mesh (0.5 mm characteristic length)
    generate_mesh('mesh_fine.msh', 0.5)
    # Solve meshes
    coarse_results = solve_mesh('mesh_coarse.msh')
    fine_results = solve_mesh('mesh_fine.msh')
    # Write results.json
    results = {"outputs": {"capacitance_pF": round(fine_results['C_pF'], 6)}}
    with open('results.json', 'w') as f:
        json.dump(results, f)
    # Write solver.log
    with open('solver.log', 'w') as f:
        f.write('Gmsh version: ' + gmsh.GMSH_API_VERSION + '\n')
        f.write('Coarse mesh: nodes={0:d}, elems={1:d}\n'.format(coarse_results['n_nodes'], coarse_results['n_elems']))
        f.write('Fine mesh: nodes={0:d}, elems={1:d}\n'.format(fine_results['n_nodes'], fine_results['n_elems']))
        f.write('Fine capacitance: {:.6f} pF\n'.format(fine_results['C_pF']))
    # Write fields.npz from fine mesh
    np.savez('fields.npz', node_ids=np.arange(fine_results['n_nodes']), coordinates=fine_results['coords_mm'], potential=fine_results['phi'], capacitance_pF=np.array(fine_results['C_pF']))
    # Write refinement.json
    refinement = {"coarse": {"mesh_file": "mesh_coarse.msh", "n_nodes": coarse_results['n_nodes'], "n_elems": coarse_results['n_elems'], "capacitance_pF": round(coarse_results['C_pF'], 6)}, "fine": {"mesh_file": "mesh_fine.msh", "n_nodes": fine_results['n_nodes'], "n_elems": fine_results['n_elems'], "capacitance_pF": round(fine_results['C_pF'], 6)}}
    with open('refinement.json', 'w') as f:
        json.dump(refinement, f)
    # Write environment.json
    env = {"solver": {"name": "spsolve", "library": "scipy.sparse.linalg", "matrix_type": "csr", "approximate_linalg": "direct"}, "libraries": {"skfem": skfem.__version__, "meshio": meshio.__version__, "gmsh": gmsh.GMSH_API_VERSION}, "command": "python main.py", "units": {"distance": "mm", "potential": "V", "capacitance": "pF"}, "field_schema": {"node_ids": "int", "coordinates": "float[3]", "potential": "float", "capacitance_pF": "float"}, "physical_groups": {"dielectric": "volume", "grounded": "face", "charged": "face"}, "discretization": {"element": "tetrahedral P1", "mesh_size_mm_coarse": 2.0, "mesh_size_mm_fine": 0.5}}
    with open('environment.json', 'w') as f:
        json.dump(env, f)
