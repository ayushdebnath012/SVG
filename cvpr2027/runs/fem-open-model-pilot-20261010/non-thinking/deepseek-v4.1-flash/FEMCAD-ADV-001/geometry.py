import gmsh
import math
import json
from pathlib import Path

# Initialize Gmsh
gmsh.initialize()
gmsh.model.add("rubber_boot_seal")

# ----------------------------------------------------------------------
# 1. Geometry Definition (2D Profile)
# ----------------------------------------------------------------------
# The boot seal is a surface of revolution. We define the 2D cross-section
# in the XZ plane (y=0 is the symmetry plane). The profile is revolved
# around the Z-axis.
# The profile is a closed curve defining the rubber thickness (3 mm).
# Two main regions: the convoluted boot seal and the rigid pipe.

# --- Boot Seal Profile (Outer & Inner Boundaries) ---
# We define the outer profile (from top to bottom) and then offset it
# inwards by 3 mm to get the inner profile. The profile is constructed
# of points connected by splines and lines.

# Outer profile points (x, z) in mm
outer_pts = [
    (30.0, 225.0), (30.0, 195.0), (48.0, 174.0), (58.0, 164.0),
    (58.0, 148.0), (76.0, 88.0), (76.0, 85.0), (110.0, 73.0),
    (110.0, 65.0), (90.0, 58.0), (90.0, 55.0), (110.0, 45.0),
    (110.0, 35.0), (100.0, 20.0), (100.0, 0.0)
]

# Inner profile points (offset by ~3 mm normal to the surface)
# Note: The tutorial mentions a thickness of 3 mm.
inner_pts = [
    (27.0, 225.0), (27.0, 195.0), (45.0, 174.0), (55.0, 164.0),
    (55.0, 148.0), (73.0, 88.0), (73.0, 85.0), (107.0, 73.0),
    (107.0, 65.0), (87.0, 58.0), (87.0, 55.0), (107.0, 45.0),
    (107.0, 35.0), (97.0, 20.0), (97.0, 0.0)
]

# Create points for outer profile
outer_tags = []
for x, z in outer_pts:
    outer_tags.append(gmsh.model.occ.addPoint(x, 0, z))

# Create points for inner profile
inner_tags = []
for x, z in inner_pts:
    inner_tags.append(gmsh.model.occ.addPoint(x, 0, z))

# Create splines and lines for the outer profile
outer_curves = []
for i in range(len(outer_tags)-1):
    outer_curves.append(gmsh.model.occ.addLine(outer_tags[i], outer_tags[i+1]))

# Create splines and lines for the inner profile
inner_curves = []
for i in range(len(inner_tags)-1):
    inner_curves.append(gmsh.model.occ.addLine(inner_tags[i], inner_tags[i+1]))

# Close the profile by connecting the ends
# Top cap
outer_curves.append(gmsh.model.occ.addLine(outer_tags[-1], inner_tags[-1]))
# Bottom cap
outer_curves.append(gmsh.model.occ.addLine(inner_tags[0], outer_tags[0]))

# Create a curve loop and plane surface for the boot cross-section
boot_loop = gmsh.model.occ.addCurveLoop(outer_curves + inner_curves)
boot_surf = gmsh.model.occ.addPlaneSurface([boot_loop])

# --- Pipe Profile ---
# Pipe: Outer radius = 30 - 3 + 1 (overlap) = 28 mm. Inner radius = 25 mm.
# Height = 275 mm, starting at z = -10.
pipe_outer_pts = [(28.0, -10.0), (28.0, 265.0)]
pipe_inner_pts = [(25.0, -10.0), (25.0, 265.0)]

pipe_outer_tags = [gmsh.model.occ.addPoint(x, 0, z) for x, z in pipe_outer_pts]
pipe_inner_tags = [gmsh.model.occ.addPoint(x, 0, z) for x, z in pipe_inner_pts]

pipe_curves = [
    gmsh.model.occ.addLine(pipe_outer_tags[0], pipe_outer_tags[1]),
    gmsh.model.occ.addLine(pipe_outer_tags[1], pipe_inner_tags[1]),
    gmsh.model.occ.addLine(pipe_inner_tags[1], pipe_inner_tags[0]),
    gmsh.model.occ.addLine(pipe_inner_tags[0], pipe_outer_tags[0])
]

pipe_loop = gmsh.model.occ.addCurveLoop(pipe_curves)
pipe_surf = gmsh.model.occ.addPlaneSurface([pipe_loop])

# ----------------------------------------------------------------------
# 2. Revolve to Create 3D Geometry
# ----------------------------------------------------------------------
# Revolve the boot surface around the Z-axis by 90 degrees (from -90 to 90,
# i.e., half domain). The symmetry plane is the XZ plane.
boot_vol = gmsh.model.occ.revolve(
    [(2, boot_surf)], 0, 0, 0, 0, 0, 1, math.pi/2
)

# Revolve the pipe surface
pipe_vol = gmsh.model.occ.revolve(
    [(2, pipe_surf)], 0, 0, 0, 0, 0, 1, math.pi/2
)

# ----------------------------------------------------------------------
# 3. Boolean Operations and Physical Groups
# ----------------------------------------------------------------------
gmsh.model.occ.synchronize()

# Identify surfaces for physical groups
# We need to find the surfaces corresponding to the boot, pipe, and boundaries.
# Since the geometry is complex, we use bounding boxes and normal vectors
# to identify the surfaces.

# Get all volumes
volumes = gmsh.model.getEntities(3)
print(f"Volumes: {volumes}")

# Identify the boot and pipe volumes based on their bounding boxes
# Boot volume: z from ~0 to ~225, x from ~25 to ~110
# Pipe volume: z from -10 to 265, x from ~25 to ~28
boot_vol_tag = None
pipe_vol_tag = None
for v in volumes:
    bbox = gmsh.model.getBoundingBox(3, v[1])
    # Boot: larger radial extent
    if bbox[3] - bbox[0] > 50:
        boot_vol_tag = v[1]
    else:
        pipe_vol_tag = v[1]

print(f"Boot volume: {boot_vol_tag}, Pipe volume: {pipe_vol_tag}")

# Add physical groups for materials
gmsh.model.addPhysicalGroup(3, [boot_vol_tag], name="Boot_Rubber")
gmsh.model.addPhysicalGroup(3, [pipe_vol_tag], name="Pipe_Rigid")

# Identify boundary surfaces
surfaces = gmsh.model.getEntities(2)
print(f"Surfaces: {surfaces}")

# Identify the symmetry plane (y=0)
# The symmetry plane is at y=0. Check the bounding box of each surface.
symmetry_faces = []
for s in surfaces:
    bbox = gmsh.model.getBoundingBox(2, s[1])
    if abs(bbox[1]) < 1e-3 and abs(bbox[4]) < 1e-3:
        symmetry_faces.append(s[1])

if symmetry_faces:
    gmsh.model.addPhysicalGroup(2, symmetry_faces, name="Symmetry_Plane")
    print(f"Symmetry faces: {symmetry_faces}")

# Identify the fixed bottom of the seal (z ~ 0)
# The boot bottom is at z=0. Find surfaces with z_min < 1e-3 and z_max < 5.
fixed_bottom_faces = []
for s in surfaces:
    bbox = gmsh.model.getBoundingBox(2, s[1])
    if bbox[2] < 1e-3 and bbox[5] < 5.0:
        fixed_bottom_faces.append(s[1])

if fixed_bottom_faces:
    gmsh.model.addPhysicalGroup(2, fixed_bottom_faces, name="Fixed_Bottom")
    print(f"Fixed bottom faces: {fixed_bottom_faces}")

# Identify the pipe bottom (z ~ -10) for rotation application
pipe_bottom_faces = []
for s in surfaces:
    bbox = gmsh.model.getBoundingBox(2, s[1])
    if bbox[2] < -9.0 and bbox[5] < -5.0:
        pipe_bottom_faces.append(s[1])

if pipe_bottom_faces:
    gmsh.model.addPhysicalGroup(2, pipe_bottom_faces, name="Pipe_Bottom")
    print(f"Pipe bottom faces: {pipe_bottom_faces}")

# Identify contact surfaces
# Pipe outer surface (contact with boot inner surface)
# Boot inner surface (contact with pipe outer and self-contact)
# Boot outer surface (self-contact)

# The easiest way is to identify surfaces based on their radial position and
# whether they belong to the boot or pipe.
# For the pipe, the outer surface is the one with the maximum radius (x~28).
# For the boot, the inner surface is the one facing the pipe (x~25-27),
# and the outer surface is the one facing outward (x~30-110).

# We will use the surface normals and bounding boxes to classify.
# For a surface, we can compute the average normal at the center of mass.

# Get all surfaces of the boot volume
boot_surfaces = gmsh.model.getBoundary([(3, boot_vol_tag)], oriented=False)
boot_surf_tags = [s[1] for s in boot_surfaces]

# Get all surfaces of the pipe volume
pipe_surfaces = gmsh.model.getBoundary([(3, pipe_vol_tag)], oriented=False)
pipe_surf_tags = [s[1] for s in pipe_surfaces]

# Identify pipe outer surface
pipe_outer_surf = None
for s in pipe_surf_tags:
    bbox = gmsh.model.getBoundingBox(2, s)
    # Outer surface has max radius ~28
    if bbox[3] > 27.0:
        pipe_outer_surf = s
        break

if pipe_outer_surf:
    gmsh.model.addPhysicalGroup(2, [pipe_outer_surf], name="Pipe_Outer_Contact")
    print(f"Pipe outer contact: {pipe_outer_surf}")

# Identify boot inner and outer surfaces
# We'll use a simple approach: for each boot surface, check if it's on the
# inner side (towards the axis) or outer side.
# Since the boot is convoluted, we check the normal vector at the centroid.
# For a surface, we can get the centroid and normal using gmsh.model.getNormal.

boot_inner_surfs = []
boot_outer_surfs = []

for s in boot_surf_tags:
    # Skip symmetry and bottom/top faces
    bbox = gmsh.model.getBoundingBox(2, s)
    if abs(bbox[1]) < 1e-3 and abs(bbox[4]) < 1e-3:
        continue
    if bbox[2] < 1e-3 and bbox[5] < 5.0:
        continue

    # Get the centroid (approximate using bounding box center for simplicity)
    cx = (bbox[0] + bbox[3]) / 2
    cy = (bbox[1] + bbox[4]) / 2
    cz = (bbox[2] + bbox[5]) / 2

    # Get the normal at the centroid (using the closest parameter)
    # This is a bit tricky; we'll use the fact that the inner surface faces
    # towards the axis. We can check the distance from the axis.
    # Actually, a better way is to check if the surface is part of the
    # original inner or outer profile. But since we revolved, we lost that info.
    # We'll use the radial distance: inner surfaces have smaller x.
    # For a given z, the inner surface should have smaller x than the outer.
    # Since the boot is convoluted, this is not strictly true if we compare
    # different z levels. But for a given z, it is.
    # We can use the fact that the inner surface is the one that was offset
    # inwards. From the profile, the inner surface is always closer to the
    # axis than the outer surface.

    # We'll compute the average radial distance of the surface points.
    # Since we don't have the mesh yet, we can use the bounding box.
    # For a surface at a given z, the inner surface has a smaller x extent.
    # But the boot is not monotonic in z. A simple heuristic:
    # The inner surface is the one that is closer to the pipe (x ~ 25-30).
    # The outer surface is the one further out (x > 30).
    # However, the convolutions go in and out. Let's use the normal vector.
    # The inner surface normal points inwards (towards the axis), the outer
    # surface normal points outwards.
    # We can sample a point on the surface and compute the normal.
    # For a surface, gmsh.model.getNormal(tag, param) gives the normal.
    # We need a parameter on the surface. We can use the center of the
    # bounding box as a parameter, but it may not lie on the surface.
    # Instead, we can use the fact that the surfaces are separated by the
    # convolutions. We'll classify based on the x-coordinate of the centroid.
    # For the boot, the inner surface is roughly at x < 50, outer at x > 50.
    # This is a rough approximation but should work for the convoluted shape.
    # Let's refine: we'll use the fact that the pipe is at x=28. The inner
    # surface of the boot is in contact with the pipe, so it's at x ~ 28.
    # The outer surface is at x > 30.

    # For a more robust classification, we can look at the normal vector.
    # We'll sample the normal at the centroid of the surface.
    # Since we don't have a parametrization, we can use the first node of the
    # surface if we had a mesh. Without mesh, we can use the bounding box
    # and the fact that the inner surface is 'inside' the outer surface.
    # We'll compute the distance from the axis (x^2 + y^2)^0.5 for the
    # bounding box corners. The inner surface has smaller max radius.

    # For simplicity, we'll classify based on the maximum radial distance.
    # Inner surfaces have max radius < 35, outer surfaces have max radius > 35.
    max_r = math.sqrt(bbox[3]**2 + bbox[4]**2)
    if max_r < 35.0:
        boot_inner_surfs.append(s)
    else:
        boot_outer_surfs.append(s)

if boot_inner_surfs:
    gmsh.model.addPhysicalGroup(2, boot_inner_surfs, name="Boot_Inner_Contact")
    print(f"Boot inner contact: {boot_inner_surfs}")

if boot_outer_surfs:
    gmsh.model.addPhysicalGroup(2, boot_outer_surfs, name="Boot_Outer_Contact")
    print(f"Boot outer contact: {boot_outer_surfs}")

# ----------------------------------------------------------------------
# 4. Mesh Generation
# ----------------------------------------------------------------------
# Set mesh size
gmsh.option.setNumber("Mesh.MeshSizeMin", 1.5)
gmsh.option.setNumber("Mesh.MeshSizeMax", 5.0)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 20)
gmsh.option.setNumber("Mesh.Algorithm", 6)  # Frontal-Delaunay
gmsh.option.setNumber("Mesh.RecombineAll", 0)

# Generate 3D mesh
gmsh.model.mesh.generate(3)

# ----------------------------------------------------------------------
# 5. Export
# ----------------------------------------------------------------------
out_dir = Path(".")
gmsh.write(str(out_dir / "part.step"))
gmsh.write(str(out_dir / "mesh.msh"))

print("Exported part.step and mesh.msh")

gmsh.finalize()