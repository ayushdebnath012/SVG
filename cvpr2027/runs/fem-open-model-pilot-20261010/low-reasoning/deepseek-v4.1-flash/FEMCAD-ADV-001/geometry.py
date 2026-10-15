import gmsh
import math
import numpy as np
from pathlib import Path

# --- Gmsh OCC geometry for rubber boot seal (surrogate, see limitations) ---
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.option.setNumber("General.Verbosity", 2)
gmsh.model.add("rubber_boot_seal")

occ = gmsh.model.occ

# Units: mm

# ---------- helpers ----------
def qbezier(p0, p1, p2, n=15):
    pts = []
    for t in np.linspace(0.0, 1.0, n):
        mt = 1.0 - t
        x = mt*mt*p0[0] + 2.0*mt*t*p1[0] + t*t*p2[0]
        y = mt*mt*p0[1] + 2.0*mt*t*p1[1] + t*t*p2[1]
        pts.append((x, y))
    return pts

def offset_polyline(pts, distance):
    n = len(pts)
    normals = []
    for i in range(n):
        if i == 0:
            dx = pts[1][0] - pts[0][0]
            dy = pts[1][1] - pts[0][1]
        elif i == n-1:
            dx = pts[-1][0] - pts[-2][0]
            dy = pts[-1][1] - pts[-2][1]
        else:
            dx = pts[i+1][0] - pts[i-1][0]
            dy = pts[i+1][1] - pts[i-1][1]
        L = math.hypot(dx, dy)
        if L < 1e-12:
            nx, ny = 0.0, 0.0
        else:
            nx, ny = -dy/L, dx/L
        normals.append((nx, ny))
    return [(pts[i][0] + distance*normals[i][0],
             pts[i][1] + distance*normals[i][1]) for i in range(n)]

def add_point(x, y, z=0.0, size=2.0):
    return occ.addPoint(x, y, z, size)

def add_line(p1, p2):
    return occ.addLine(p1, p2)

def make_face_from_closed_points(pts):
    tags = [add_point(x, y) for (x, y) in pts]
    edges = []
    n = len(tags)
    for i in range(n):
        edges.append(add_line(tags[i], tags[(i+1) % n]))
    wire = occ.addWire(edges, -1)
    return occ.addPlaneSurface([wire], -1)

# ---------- rubber profile centerline (explicit tutorial coordinates, surrogate closure) ----------
raw = []
raw.append((0.0, 100.0))
raw.append((20.0, 100.0))
raw += qbezier((20.0, 100.0), (35.0, 110.0), (45.0, 110.0))
raw += qbezier((45.0, 110.0), (52.0, 110.0), (55.0, 90.0))
raw += [(55.0, 90.0), (58.0, 90.0)]
raw += qbezier((58.0, 90.0), (65.0, 110.0), (73.0, 110.0))
raw += qbezier((73.0, 110.0), (80.0, 110.0), (85.0, 76.0))
raw += [(85.0, 76.0), (88.0, 76.0)]
# surrogate connector (missing exact copied curves)
raw += [(88.0, 76.0), (148.0, 48.0)]
raw += qbezier((148.0, 48.0), (150.0, 58.0), (164.0, 58.0))
raw += qbezier((164.0, 58.0), (174.0, 58.0), (174.0, 48.0))
raw += qbezier((174.0, 48.0), (174.0, 30.0), (195.0, 30.0))
raw += [(195.0, 30.0), (225.0, 30.0)]
# surrogate closure (missing top/inner surface)
raw += [(225.0, 30.0), (0.0, 100.0)]

# one-sided thickness 3 mm
outer = offset_polyline(raw, 3.0)
loop = raw + list(reversed(outer))

# build rubber face
rubber_face = make_face_from_closed_points(loop)

# revolve rubber half-domain (-90 to +90 deg), axis y
rubber_rev = occ.revolve([(2, rubber_face)], 0,0,0, 0,1,0, math.pi, numElements=[24])
rubber_vol = rubber_rev[0][1]

# ---------- pipe (hollow half cylinder, rigid) ----------
pipe_face_pts = [(24.0, -10.0), (27.0, -10.0), (27.0, 265.0), (24.0, 265.0)]
pipe_face = make_face_from_closed_points(pipe_face_pts)
pipe_rev = occ.revolve([(2, pipe_face)], 0,0,0, 0,1,0, math.pi, numElements=[12])
pipe_vol = pipe_rev[0][1]

# ---------- physical groups ----------
gmsh.model.addPhysicalGroup(3, [rubber_vol], tag=1, name="rubber")
gmsh.model.addPhysicalGroup(3, [pipe_vol], tag=2, name="pipe")

# boundary surface classification
all_surfs = gmsh.model.getBoundary([(3, rubber_vol), (3, pipe_vol)], oriented=False)
for dim, tag in all_surfs:
    xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(2, tag)
    if abs(xmin) < 1e-3 and abs(xmax) < 1e-3:
        gmsh.model.addPhysicalGroup(2, [tag], tag=10, name="symmetry")
    if abs(ymin - 100.0) < 1e-3 and abs(ymax - 100.0) < 1e-3:
        gmsh.model.addPhysicalGroup(2, [tag], tag=11, name="fixed_bottom")
    if abs(ymin + 10.0) < 1e-3 and abs(ymax + 10.0) < 1e-3:
        gmsh.model.addPhysicalGroup(2, [tag], tag=12, name="pipe_bottom")
    if xmax > 26.0 and zmax > 26.0 and ymin > -10.0 and ymax < 265.0:
        gmsh.model.addPhysicalGroup(2, [tag], tag=13, name="pipe_outer")

gmsh.model.mesh.generate(3)
gmsh.write("part.step")
gmsh.write("mesh.msh")
gmsh.finalize()
