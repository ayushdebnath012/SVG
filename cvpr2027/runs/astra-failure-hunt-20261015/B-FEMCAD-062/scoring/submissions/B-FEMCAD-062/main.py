import os
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

import sys
import json
import time
import shutil
import subprocess
import platform
from pathlib import Path
import numpy as np
import gmsh

OUT = Path(os.environ.get("CADFEM_OUTPUT_DIR", ".")).resolve()
OUT.mkdir(parents=True, exist_ok=True)
os.chdir(OUT)
START = time.time()
LOG = open("solver.log", "w", buffering=1)

def log(s):
    LOG.write(str(s) + "\n")
    print(s, flush=True)

def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2))

def numbers(line):
    try:
        return [float(v.replace("D", "E")) for v in line.split()]
    except ValueError:
        return None

def read_dat(path):
    stresses = []
    element_ids = []
    ips = []
    disp = {}
    mode = None
    for line in Path(path).read_text().splitlines():
        low = line.lower()
        if "stresses" in low and "elem" in low:
            mode = "stress"
            continue
        if "displacements" in low:
            mode = "disp"
            continue
        vals = numbers(line)
        if not vals:
            continue
        if mode == "stress" and len(vals) == 8:
            element_ids.append(int(vals[0]))
            ips.append(int(vals[1]))
            stresses.append(vals[2:])
        elif mode == "disp" and len(vals) == 4:
            disp[int(vals[0])] = vals[1:]
    if not stresses or not disp:
        raise RuntimeError("Missing stress or displacement records in CalculiX output.")
    return (np.asarray(stresses), np.asarray(element_ids, dtype=np.int64),
            np.asarray(ips, dtype=np.int64), disp)

def vmises(s):
    return np.sqrt(0.5*((s[:,0]-s[:,1])**2 + (s[:,1]-s[:,2])**2
                         + (s[:,2]-s[:,0])**2)
                   + 3*(s[:,3]**2+s[:,4]**2+s[:,5]**2))

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.option.setNumber("General.NumThreads", 2)
gmsh.model.add("plate_with_through_hole")
occ = gmsh.model.occ
box = occ.addBox(0, 0, 0, 100, 5, 50)
hole = occ.addCylinder(50, 0, 25, 0, 5, 0, 10)
solids, _ = occ.cut([(3, box)], [(3, hole)])
occ.synchronize()
gmsh.write("part.step")

surfaces = [t for d,t in gmsh.model.getEntities(2)]
fixed_faces, loaded_faces, hole_faces = [], [], []
for t in surfaces:
    bb = gmsh.model.getBoundingBox(2, t)
    if abs(bb[0]) < 1e-5 and abs(bb[3]) < 1e-5:
        fixed_faces.append(t)
    if abs(bb[0]-100) < 1e-5 and abs(bb[3]-100) < 1e-5:
        loaded_faces.append(t)
    if gmsh.model.getType(2,t) == "Cylinder":
        hole_faces.append(t)
if not fixed_faces or not loaded_faces or not hole_faces:
    raise RuntimeError("Unable to identify required CAD faces.")
for dim, tags, name in [
    (3, [t for d,t in solids], "plate"),
    (2, fixed_faces, "fixed_x0"),
    (2, loaded_faces, "traction_x100"),
    (2, hole_faces, "hole_free")]:
    p = gmsh.model.addPhysicalGroup(dim, tags)
    gmsh.model.setPhysicalName(dim,p,name)

gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
gmsh.option.setNumber("Mesh.SaveAll", 1)
gmsh.option.setNumber("Mesh.Algorithm", 6)
gmsh.option.setNumber("Mesh.Algorithm3D", 1)
gmsh.option.setNumber("Mesh.ElementOrder", 2)
gmsh.option.setNumber("Mesh.SecondOrderLinear", 0)
gmsh.option.setNumber("Mesh.Optimize", 1)
gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
dist = gmsh.model.mesh.field.add("Distance")
gmsh.model.mesh.field.setNumbers(dist, "FacesList", hole_faces)
gmsh.model.mesh.field.setNumber(dist, "Sampling", 180)
th = gmsh.model.mesh.field.add("Threshold")
gmsh.model.mesh.field.setNumber(th, "InField", dist)
gmsh.model.mesh.field.setNumber(th, "DistMin", 0)
gmsh.model.mesh.field.setNumber(th, "DistMax", 5)
gmsh.model.mesh.field.setAsBackgroundMesh(th)

ccx = shutil.which("ccx")
if not ccx:
    raise RuntimeError("CalculiX executable not found")
env = {
    "python": sys.version, "platform": platform.platform(),
    "numpy": np.__version__, "gmsh": gmsh.__version__,
    "solver": ccx, "threads": 2,
    "units": {"length": "mm", "force": "N", "stress": "MPa"},
    "input_files": [],
}
inpdir = Path(os.environ.get("CADFEM_INPUT_DIR", "."))
if inpdir.exists():
    env["input_files"] = [{"name": p.name, "bytes": p.stat().st_size}
                          for p in inpdir.iterdir() if p.is_file()]
dump("environment.json", env)
history = []
converged = False

for level, (hf, hb) in enumerate([(0.95, 4.0), (0.65, 3.4), (0.44, 2.9), (0.30, 2.5), (0.22, 2.2)]):
    if level > 1 and time.time()-START > 465:
        log("Time budget prevents another refinement; retaining last solved mesh.")
        break
    gmsh.model.mesh.clear()
    gmsh.model.mesh.field.setNumber(th, "SizeMin", hf)
    gmsh.model.mesh.field.setNumber(th, "SizeMax", hb)
    gmsh.option.setNumber("Mesh.MeshSizeMin", hf)
    gmsh.option.setNumber("Mesh.MeshSizeMax", hb)
    gmsh.model.mesh.generate(3)
    ntags, xyz, _ = gmsh.model.mesh.getNodes()
    xyz = xyz.reshape(-1,3)
    order = np.argsort(ntags)
    ntags, xyz = ntags[order], xyz[order]
    index = {int(t):i for i,t in enumerate(ntags)}
    types, etags, enodes = gmsh.model.mesh.getElements(3)
    allconn = []
    for typ, tags, nodes in zip(types, etags, enodes):
        if typ != 11:
            raise RuntimeError("Expected quadratic tetrahedra only")
        allconn.append(np.asarray(nodes,dtype=np.int64).reshape(-1,10))
    conn_g = np.vstack(allconn)
    conn = conn_g[:,[0,1,2,3,4,5,6,7,9,8]]
    force = {}
    area = 0.0
    for face in loaded_faces:
        ty, _, no = gmsh.model.mesh.getElements(2,face)
        for typ, nodes in zip(ty,no):
            if typ != 9:
                raise RuntimeError("Expected quadratic boundary triangles")
            for tr in np.asarray(nodes).reshape(-1,6):
                v = xyz[[index[int(n)] for n in tr[:3]]]
                a = np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))/2
                area += a
                for n in tr[3:]:
                    force[int(n)] = force.get(int(n),0.0)+4.0*a/3
    if abs(area-250)>1e-5:
        raise RuntimeError("Incorrect loaded-face area")
    fixed = ntags[np.abs(xyz[:,0])<1e-7]
    job = f"refine_{level}"
    with open(job+".inp","w") as f:
        f.write("*HEADING\nPlate with circular through hole; N mm MPa\n*NODE,NSET=ALLN\n")
        for n,p in zip(ntags,xyz):
            f.write(f"{n},{p[0]:.12g},{p[1]:.12g},{p[2]:.12g}\n")
        f.write("*ELEMENT,TYPE=C3D10,ELSET=ALLE\n")
        for e,c in enumerate(conn,1):
            f.write(str(e)+","+",".join(map(str,c))+"\n")
        f.write("*MATERIAL,NAME=STEEL\n*ELASTIC\n210000.,0.3\n")
        f.write("*SOLID SECTION,ELSET=ALLE,MATERIAL=STEEL\n")
        f.write("*NSET,NSET=FIXED\n")
        for i in range(0,len(fixed),16):
            f.write(",".join(map(str,fixed[i:i+16]))+"\n")
        f.write("*BOUNDARY\nFIXED,1,3,0.\n*STEP\n*STATIC\n*CLOAD\n")
        for n,val in sorted(force.items()):
            f.write(f"{n},1,{val:.12g}\n")
        f.write("*NODE PRINT,NSET=ALLN\nU\n*EL PRINT,ELSET=ALLE\nS\n*END STEP\n")
    log(f"Refinement {level}: {len(ntags)} nodes, {len(conn)} C3D10 elements; total traction force {sum(force.values()):.12g} N")
    with open(job+".stdout","w") as out:
        proc = subprocess.run([ccx,"-i",job],stdout=out,stderr=subprocess.STDOUT,
                              timeout=max(30, int(585-(time.time()-START))))
    LOG.write(Path(job+".stdout").read_text())
    if proc.returncode:
        raise RuntimeError("CalculiX failed")
    stress, seid, ip, disps = read_dat(job+".dat")
    vm = vmises(stress)
    peak = float(vm.max())
    change = None if not history else abs(peak-history[-1]["max_von_mises_MPa"])/peak
    history.append({"level":level,"hole_mesh_size_mm":hf,"bulk_mesh_size_mm":hb,
                    "nodes":len(ntags),"elements":len(conn),
                    "max_von_mises_MPa":peak,"relative_change":change,
                    "elapsed_seconds":time.time()-START})
    gmsh.write("mesh.msh")
    u = np.array([disps[int(n)] for n in ntags])
    np.savez_compressed("fields.npz",
        points=xyz, node_ids=ntags,
        cells=np.array([[index[int(n)] for n in c] for c in conn],dtype=np.int64),
        element_ids=np.arange(1,len(conn)+1), displacement=u,
        stress=stress, stress_element_ids=seid, integration_point_ids=ip,
        von_mises=vm,
        stress_components=np.array(["xx","yy","zz","xy","xz","yz"]),
        cell_type=np.array("C3D10"), units=np.array("mm,N,MPa"))
    dump("results.json", {"outputs":{"max_von_mises_MPa":peak}})
    converged = change is not None and change < 0.01
    dump("refinement.json",{
        "method":"Quadratic 3-D tetrahedral linear elasticity; unsmoothed integration-point maximum",
        "criterion":"relative change of maximum von Mises stress below 1 percent",
        "converged":converged,"levels":history})
    log(f"Maximum von Mises = {peak:.8g} MPa; relative change = {change}")
    if converged:
        break

gmsh.finalize()
log("Convergence achieved." if converged else "Convergence not established within available refinement/time budget.")
LOG.close()
