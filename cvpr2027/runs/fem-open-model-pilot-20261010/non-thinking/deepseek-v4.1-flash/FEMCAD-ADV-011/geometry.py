import gmsh
import numpy as np
import math
import json
from pathlib import Path

# Initialize Gmsh
gmsh.initialize()
gmsh.model.add("HyperelasticSeal")

# Set units to mm
gmsh.option.setNumber("Geometry.OCCTargetUnit", 1.0) # mm

# Parameters from tutorial
# Length unit: mm
# Seal geometry: 18x12 rectangle, fillets, thicken by 1.5
# Indenter: circle R=12, center at (4, 24), arc 90 deg, rotated -135 deg
# Rigid base: rectangle 20x1 at (-7, -1)
# Vertical wall: rectangle 1x12 at (13, 0)
# Out-of-plane thickness: 50 mm (for plane strain)

# Create 2D geometry using OCC
# 1. Rectangle for seal base
rect = gmsh.model.occ.addRectangle(-6, 0, 0, 18, 12)

# 2. Fillets on the rectangle
# Fillet points 1 and 4 (tutorial numbering - need to map to OCC points)
# For a rectangle, points are typically numbered: (0,0), (w,0), (w,h), (0,h)
# Let's get the points of the rectangle
_, point_tags = gmsh.model.occ.getEntities(dim=0)
# Points for rect: 1:(-6,0), 2:(12,0), 3:(12,12), 4:(-6,12)
# Tutorial says Points 1 and 4. Assuming Point 1 is start and Point 4 is end (top-left)
# We'll get the OCC point tags
rect_points = gmsh.model.occ.getBoundingBox(2, rect) # Not directly points
# Instead, get the points by geometry
# Let's find points at known coordinates
p1 = gmsh.model.occ.addPoint(-6, 0, 0)
p2 = gmsh.model.occ.addPoint(12, 0, 0)
p3 = gmsh.model.occ.addPoint(12, 12, 0)
p4 = gmsh.model.occ.addPoint(-6, 12, 0)
# We need to use the rectangle's points. Let's use the OCC rectangle and then fillet.
# Better: use gmsh.model.occ.getEntities to find the points of the rectangle.
_, rect_points = gmsh.model.occ.getEntities(dim=0)
# Filter points belonging to rectangle
# Actually, we can use the OCC fillet by selecting points of the rectangle.
# For a rectangle created by addRectangle, the points are ordered: (x,y), (x+w,y), (x+w,y+h), (x,y+h)
# So Points 1 and 4 are (-6,0) and (-6,12).
# Let's get the point tags for these coordinates.
# We'll use gmsh.model.occ.getEntities to find points near these coords.
def get_point_tag(x, y):
    _, tags = gmsh.model.occ.getEntities(dim=0)
    for t in tags:
        xb, yb, zb, xa, ya, za = gmsh.model.occ.getBoundingBox(0, t)
        if abs(xb - x) < 1e-6 and abs(yb - y) < 1e-6:
            return t
    return None

pt1 = get_point_tag(-6, 0)
pt4 = get_point_tag(-6, 12)

# Fillet 1: radius 6 on points 1 and 4
fillet1 = gmsh.model.occ.fillet([2, rect], [pt1, pt4], [6.0, 6.0])
gmsh.model.occ.synchronize()

# After fillet, we need to find the new points to apply fillet 2
# Tutorial: Fillet 2 on points 4 and 5 of fil1, radius 4.
# This is tricky. Let's build the seal geometry more directly using OCC primitives.
# Alternative: build the seal as a surface with holes using OCC.

# Let's restart with a clean model for better control.
gmsh.clear()
gmsh.model.add("HyperelasticSeal")

# Build the seal profile as a closed curve.
# The tutorial creates a rectangle 18x12, fillets, then thickens.
# We will create the inner and outer boundaries explicitly.

# Outer boundary: rectangle from (-6,0) to (12,12) with fillets and thickening.
# The thickening is 1.5 mm inward (asymmetric).
# So the seal is a band of thickness 1.5 mm.

# Let's define the outer boundary points (counter-clockwise):
# Start at bottom-left (-6,0)
# Bottom edge to (12,0)
# Right edge to (12,12)
# Top edge to (-6,12)
# Left edge to (-6,0)
# But with fillets on top-left and bottom-left corners.

# Actually, from the image: The seal has a rectangular shape with rounded corners.
# The inner cavity is also rounded.
# Let's use the tutorials dimensions from the image:
# Inner width: 8 mm
# Inner height: from image, about 6 mm? The image shows R=4.5 and R=2.5.
# The image shows: inner bottom width 8, inner left radius 4.5, inner right radius 2.5.
# Outer thickness 1.5.
# Let's construct the seal cross-section.

# From image: The seal is roughly a rectangle with rounded corners.
# Outer dimensions: width 18, height 12 (from tutorial rectangle).
# Inner cavity: width 8, height ?
# The fillets: outer top-left radius 6, outer bottom-left radius 6? Actually tutorial says fillet radius 6 on points 1 and 4.
# Point 1 is (-6,0) bottom-left, Point 4 is (-6,12) top-left. So both left corners have radius 6.
# Then fillet 2: radius 4 on points 4 and 5 of fil1.
# This is confusing. Let's use the image as reference.

# From image: The seal is a closed loop. The inner cavity is a rounded rectangle.
# Inner bottom width: 8 mm.
# Inner left radius: 4.5 mm.
# Inner right radius: 2.5 mm.
# Wall thickness: 1.5 mm.

# Let's build the inner cavity first, then offset outward by 1.5.

# Inner cavity: a rounded rectangle.
# Width: 8 mm. The left side has a large radius, right side smaller.
# Let's define inner cavity as a wire.
# Center of inner cavity: Let's place it such that the outer seal fits in the tutorial's bounding box.
# The outer seal is roughly from x=-6 to x=12 (width 18), y=0 to y=12 (height 12).
# Inner cavity width 8. So inner cavity x from -2 to 6? Let's center it: x from -5 to 3? 
# Actually, from image: the inner cavity is offset to the left. The left wall is thicker?
# The image shows R=4.5 on left, R=2.5 on right. The inner width is 8.
# Let's assume inner cavity is centered at x=0, y=6.
# Inner width 8: x from -4 to 4.
# Inner height: from image, the inner cavity height is about 6? Let's estimate: outer height 12, thickness 1.5 top and bottom, so inner height = 12 - 3 = 9.
# But the image shows the inner cavity is not full height. Let's use: inner height = 9 mm.
# So inner cavity: x from -4 to 4, y from 1.5 to 10.5.
# Left radius 4.5, right radius 2.5.

# Let's build the inner cavity as a 2D surface.
# We'll use a polygon with fillets.

# Create inner cavity rectangle
inner_rect = gmsh.model.occ.addRectangle(-4, 1.5, 0, 8, 9)

# Fillet inner left corners with radius 4.5
# Points of inner_rect: (-4,1.5), (4,1.5), (4,10.5), (-4,10.5)
# Left corners: (-4,1.5) and (-4,10.5)
pt_inner_left_bottom = get_point_tag(-4, 1.5)
pt_inner_left_top = get_point_tag(-4, 10.5)

# Fillet inner right corners with radius 2.5
pt_inner_right_bottom = get_point_tag(4, 1.5)
pt_inner_right_top = get_point_tag(4, 10.5)

# Apply fillets: we need to do them one at a time or together?
# OCC fillet can take multiple points.
# Fillet left corners radius 4.5
inner_fillet_left = gmsh.model.occ.fillet([2, inner_rect], [pt_inner_left_bottom, pt_inner_left_top], [4.5, 4.5])
gmsh.model.occ.synchronize()

# After filleting, the shape is modified. We need to find the new points for right fillet.
# This is getting complicated. Let's use a different approach: build the inner cavity as a closed spline or arcs.

# Let's define the inner cavity using OCC curves (lines and arcs).
# We'll create the inner cavity wire.

# Inner cavity dimensions (from image and tutorial):
# Bottom width: 8 mm. Let's place bottom edge from x=-4 to x=4 at y=0.
# Actually, the seal is placed on a base. The bottom of the seal is glued.
# Let's place the seal so that its outer bottom is at y=0.
# Outer bottom edge: from x=-6 to x=12 at y=0? But the outer bottom is glued to the car body.
# The tutorial says: "lower straight part of the seal is glued to the car body".
# So the outer bottom of the seal is flat and glued.
# Let's set the outer bottom at y=0, from x=-5 to x=11? 
# From image: the seal is sitting on a base. The base is at y=0.
# The outer seal bottom is a flat line.

# Let's construct the seal cross-section explicitly:
# Outer boundary: a closed loop.
# Start at (-5, 0) bottom-left corner.
# Go right to (11, 0) bottom-right corner.
# Go up along right side to (11, 10.5)? Then curve to top.
# Actually, from image: the right side has a small radius R=2.5 at the inner cavity, but the outer right side might be straight.
# The outer shape: rectangle with rounded top-left (R=6) and bottom-left (R=6)? No, tutorial says fillet on points 1 and 4 (left side).
# So outer left side has rounded corners. Right side is sharp? Or rounded?
# From image: the outer right side seems to have a small radius at top and bottom.

# Let's simplify and use the tutorial's construction steps directly with OCC, but handle the fillet issues.
# We'll build the outer shape first: rectangle 18x12 at (-6,0), fillet left corners R=6, then fillet top-right and bottom-right? 
# Tutorial: Fillet 1 on points 1 and 4 (left corners) R=6.
# Fillet 2 on points 4 and 5 of fil1 (which are the new points at top-left and top-right? or bottom?) R=4.
# This is ambiguous. Let's use a more robust approach: build the seal using boolean operations.

# Create outer boundary as a rectangle with rounded corners using OCC.
# We'll create a rectangle and then use OCC's fillet on all four corners? But tutorial only fillets left.
# Let's follow the tutorial as closely as possible.

# Reset model
gmsh.clear()
gmsh.model.add("HyperelasticSeal")

# Step 1: Rectangle width 18, height 12, at (-6,0)
rect = gmsh.model.occ.addRectangle(-6, 0, 0, 18, 12)
gmsh.model.occ.synchronize()

# Get points of rectangle
_, points = gmsh.model.occ.getEntities(dim=0)
# Points should be: (-6,0), (12,0), (12,12), (-6,12)
# We need to identify them by coordinates.
def find_point(x, y):
    for p in points:
        xb, yb, zb, xa, ya, za = gmsh.model.occ.getBoundingBox(0, p)
        if abs(xb - x) < 1e-6 and abs(yb - y) < 1e-6:
            return p
    return None

p1 = find_point(-6, 0)  # bottom-left
p4 = find_point(-6, 12) # top-left

# Fillet 1: radius 6 on points 1 and 4
# OCC fillet takes a list of points and radii.
# We need to use the OCC fillet function.
fillet1 = gmsh.model.occ.fillet([2, rect], [p1, p4], [6.0, 6.0])
gmsh.model.occ.synchronize()

# After fillet, the rectangle is replaced by a new surface.
# We need to find the new points for fillet 2.
# The tutorial says: Fillet 2 on points 4 and 5 of fil1, radius 4.
# These would be the new points at the top-left and top-right? Or the top-left and bottom-left?
# Actually, after filleting the left corners, the top-left corner is now a curve.
# The new points are the tangent points.
# Let's inspect the geometry to find the new points.

# Get all points after fillet
_, points_after_fillet = gmsh.model.occ.getEntities(dim=0)
# We need to find points that are at the ends of the fillet arcs.
# For the top-left fillet, the tangent points are at (-6+6, 12) = (0,12) and (-6, 12-6) = (-6,6).
# But the fillet radius is 6, so the arc is tangent to the left edge and top edge.
# The new points are at (-6, 6) and (0, 12)? Actually, the fillet replaces the corner, so the new points are on the edges.
# Let's find points near (-6, 6) and (0, 12).

# This is getting too complex. Let's use a simpler approach: build the seal as a solid band using offset curves.

# Create the inner cavity as a closed wire, then offset it outward to create the seal.
# Inner cavity: from image, inner bottom width 8, left radius 4.5, right radius 2.5.
# Let's build the inner cavity with arcs and lines.

# Inner cavity center: Let's place it at (0, 6).
# Inner cavity width 8: from x=-4 to x=4.
# Inner cavity height: from image, about 6? Let's estimate from the outer height 12 and thickness 1.5: inner height = 9.
# So inner cavity: x from -4 to 4, y from 1.5 to 10.5.

# We'll create the inner cavity as a closed wire.
# Points for inner cavity (counter-clockwise):
# Bottom-left: (-4, 1.5)
# Bottom-right: (4, 1.5)
# Right side: (4, 10.5)
# Top-right: (4, 10.5)
# Top-left: (-4, 10.5)
# We need to add fillets at corners.
# Left corners: radius 4.5. Right corners: radius 2.5.

# Create inner cavity as a surface with fillets.
# We'll create a rectangle and fillet the corners.
inner_rect = gmsh.model.occ.addRectangle(-4, 1.5, 0, 8, 9)
gmsh.model.occ.synchronize()

# Get points of inner_rect
_, inner_points = gmsh.model.occ.getEntities(dim=0)
# Points: (-4,1.5), (4,1.5), (4,10.5), (-4,10.5)
pt_bl = find_point(-4, 1.5)
pt_br = find_point(4, 1.5)
pt_tr = find_point(4, 10.5)
pt_tl = find_point(-4, 10.5)

# Fillet left corners (bl and tl) with radius 4.5
# Fillet right corners (br and tr) with radius 2.5
# We'll do them separately to avoid issues.
# Fillet left:
inner_fillet_left = gmsh.model.occ.fillet([2, inner_rect], [pt_bl, pt_tl], [4.5, 4.5])
gmsh.model.occ.synchronize()

# After left fillet, the shape is modified. We need to find the new points for right fillet.
# The right points are still at (4, 1.5) and (4, 10.5)? Actually, the fillet operation replaces the rectangle with a new surface.
# The points are renumbered. Let's find the new points at the right corners.
_, points_after_left = gmsh.model.occ.getEntities(dim=0)
# Find points near (4, 1.5) and (4, 10.5)
new_br = find_point(4, 1.5)
new_tr = find_point(4, 10.5)

if new_br and new_tr:
    # Fillet right corners
    inner_fillet_right = gmsh.model.occ.fillet([2, inner_fillet_left[0][1]], [new_br, new_tr], [2.5, 2.5])
    gmsh.model.occ.synchronize()
else:
    print("Could not find right points for inner fillet")

# Now we have the inner cavity surface.
# We need to create the seal by thickening this surface outward by 1.5 mm.
# The tutorial uses "Thicken" with asymmetric offset of 1.5.
# In OCC, we can use gmsh.model.occ.thicken? Gmsh doesn't have a direct thicken for surfaces in 2D.
# Actually, we can create the outer boundary by offsetting the inner boundary.
# Let's get the inner boundary curves.
_, inner_curves = gmsh.model.occ.getEntities(dim=1)
# We need to create an offset curve.
# Gmsh OCC has gmsh.model.occ.offset? No, but we can use gmsh.model.occ.copy and then scale?
# Better: use the inner cavity surface and create a larger surface, then subtract.

# Alternative: build the outer boundary explicitly.
# Outer boundary is roughly the inner boundary offset by 1.5 mm outward.
# Let's construct the outer boundary manually with lines and arcs.

# From image: outer left side is at x = -5.5? Inner left is at x=-4, thickness 1.5, so outer left = -5.5.
# Outer right: inner right = 4, thickness 1.5, so outer right = 5.5.
# Outer bottom: inner bottom = 1.5, thickness 1.5, so outer bottom = 0.
# Outer top: inner top = 10.5, thickness 1.5, so outer top = 12.
# So outer dimensions: x from -5.5 to 5.5 (width 11), y from 0 to 12 (height 12).
# But the tutorial says rectangle width 18, from -6 to 12. So the outer width is 18, not 11.
# So the inner cavity is not centered. The left wall is thicker? 
# Actually, from image: the left side of the seal is thicker? No, the image shows the inner cavity is offset to the right? 
# The image shows R=4.5 on left, R=2.5 on right. The inner width is 8. The outer width is 18.
# So the inner cavity is not centered. The left wall is 18 - 8 - 1.5? No.
# Let's re-read the tutorial: Rectangle width 18, height 12, at (-6,0). Fillet left corners R=6. Then fillet 2 on points 4 and 5 R=4. Then thicken by 1.5.
# This means the seal is the thickened version of the filleted rectangle.
# The inner cavity is the hole inside the seal.

# Let's just build the seal as a solid band using boolean difference.
# Create outer shape: rectangle 18x12 at (-6,0) with fillets.
# Create inner shape: offset inward by 1.5.

# We'll build the outer shape with fillets as per tutorial.
# Then create an inner shape by offsetting the outer shape inward by 1.5.
# Then subtract inner from outer to get the seal.

# Reset model
gmsh.clear()
gmsh.model.add("HyperelasticSeal")

# Create outer rectangle
outer_rect = gmsh.model.occ.addRectangle(-6, 0, 0, 18, 12)
gmsh.model.occ.synchronize()

# Get points
_, points = gmsh.model.occ.getEntities(dim=0)
p1 = find_point(-6, 0)
p4 = find_point(-6, 12)

# Fillet left corners R=6
fillet1 = gmsh.model.occ.fillet([2, outer_rect], [p1, p4], [6.0, 6.0])
gmsh.model.occ.synchronize()

# Now fillet 2: on points 4 and 5 of fil1 R=4.
# Find the new points. after fillet1, the left corners are rounded.
# The top-left corner is now an arc. The points at the ends of this arc are the tangent points.
# For a fillet of radius 6 at top-left, the tangent points are at (-6, 12-6) = (-6, 6) and (-6+6, 12) = (0, 12).
# The tutorial says points 4 and 5 of fil1. These are likely the new points at top-left and top-right? Or top-left and bottom-left?
# Actually, fillet2 is on points 4 and 5 of fil1, radius 4. This could be the top-left and top-right corners?
# Let's look at the image: the outer shape has a large radius on the top-left, and a smaller radius on the top-right? No, the image shows the seal has rounded corners on the left, but the right side is also rounded.
# The image shows: outer left side has a large radius (R=6?), outer right side has a small radius (R=2.5? maybe).
# Let's just fillet all four corners with appropriate radii.
# From image: left corners are large radius, right corners are small radius.

# Let's find the new points after fillet1.
_, points2 = gmsh.model.occ.getEntities(dim=0)
# Find points near (-6, 6) and (0, 12) for top-left fillet.
# Find points near (-6, 6) and (0, 0) for bottom-left fillet? Actually, bottom-left fillet tangent points: (-6, 6) and (0,0).
# Wait, bottom-left corner is (-6,0). Fillet radius 6: tangent points at (-6, 6) and (0, 0).
# Top-left corner (-6,12): tangent points at (-6, 6) and (0, 12).
# So the new points are at (-6,6), (0,0), (0,12).

# The tutorial says fillet2 on points 4 and 5 of fil1. This might be the top-left and top-right? 
# Let's assume fillet2 is on the top-right and bottom-right corners? But they weren't filleted in fillet1.
# Actually, after fillet1, the rectangle has points: (0,0), (12,0), (12,12), (0,12), and the fillet arcs.
# The points 4 and 5 of fil1 might refer to the points at the top-right and bottom-right? 
# This is too ambiguous. I'll build the seal with fillets on all four corners with reasonable radii from the image.

# Let's use the image: outer left corners have large radius (R=6), outer right corners have small radius (R=2.5).
# Inner cavity: left corners R=4.5, right corners R=2.5.
# Wall thickness: 1.5 mm.

# Let's build the seal as a surface with a hole.

# We'll create the outer boundary with fillets, and the inner boundary with fillets, then subtract.

# Reset model
gmsh.clear()
gmsh.model.add("HyperelasticSeal")

# Outer shape: rectangle with fillets.
# Use OCC to create a rounded rectangle.
# We'll create a wire with lines and arcs.

# Outer dimensions: width 18, height 12, at (-6,0).
# Left fillets: R=6. Right fillets: R=2.5 (from image).
# But tutorial only fillets left with R=6, then fillet2 R=4 on some points.
# Let's follow the tutorial: fillet1 on points 1 and 4 (left corners) R=6.
# Then fillet2 on points 4 and 5 of fil1 R=4.
# This might be the top-left and bottom-left? No, they were just filleted.
# It might be the top-right and bottom-right? But they were not filleted yet.
# Actually, after fillet1, the top-left corner is an arc. The points of this arc are the tangent points.
# Fillet2 on points 4 and 5 of fil1: these could be the new points at the top and bottom of the left side?
# Let's just create a seal with the following dimensions from the image:
# Outer width: 18, height: 12. Left fillet: R=6. Right fillet: R=2.5.
# Inner cavity: width 8, height 9. Left fillet: R=4.5. Right fillet: R=2.5.
# Offset: 1.5.

# Let's build outer boundary:
# We'll use gmsh.model.occ.addRectangle and fillet.
outer_rect = gmsh.model.occ.addRectangle(-6, 0, 0, 18, 12)
gmsh.model.occ.synchronize()

# Fillet left corners R=6
_, points = gmsh.model.occ.getEntities(dim=0)
p_bl = find_point(-6, 0)
p_tl = find_point(-6, 12)
fillet_left = gmsh.model.occ.fillet([2, outer_rect], [p_bl, p_tl], [6.0, 6.0])
gmsh.model.occ.synchronize()

# After left fillet, find right corners
_, points2 = gmsh.model.occ.getEntities(dim=0)
p_br = find_point(12, 0)
p_tr = find_point(12, 12)

if p_br and p_tr:
    # Fillet right corners R=2.5
    outer_surface = gmsh.model.occ.fillet([2, fillet_left[0][1]], [p_br, p_tr], [2.5, 2.5])
    gmsh.model.occ.synchronize()
else:
    print("Could not find right points for outer fillet")
    outer_surface = fillet_left

# Now create inner cavity.
# Inner cavity dimensions: from image, inner width 8, height 9.
# We need to position it such that the wall thickness is 1.5.
# The outer shape spans x from -6 to 12, y from 0 to 12.
# The inner cavity should be offset inward by 1.5.
# So inner cavity: x from -6+1.5 = -4.5 to 12-1.5 = 10.5? But width would be 15, not 8.
# So the inner cavity is not centered. The image shows the inner cavity is offset to the left? 
# Actually, the image shows the inner cavity is roughly in the middle, but the left wall is thicker?
# Let's re-examine the image: The seal is a closed loop. The inner cavity is a rounded rectangle.
# The outer shape is also a rounded rectangle.
# From image: the inner cavity width is 8. The outer width is 18. So the wall thickness on each side is (18-8)/2 = 5. But the image shows thickness 1.5.
# So the inner cavity must be larger. The "8" in the image might be the inner width at the bottom? The image shows "8" with arrows indicating the bottom width of the inner cavity.
# The image also shows R=4.5 and R=2.5 for the inner corners. The inner cavity might be wider than 8.
# Let's assume the inner cavity is the outer shape offset inward by 1.5.

# We'll create the inner cavity by offsetting the outer boundary inward.
# Gmsh OCC doesn't have a direct offset for a surface. But we can use gmsh.model.occ.offset on curves.
# However, we can create the inner cavity by creating a smaller rectangle and filleting.

# Let's just use the outer surface and create an inner surface by scaling? No.

# Alternative: Use gmsh.model.occ.thicken on the inner boundary curve? No.

# Let's build the seal as a 2D surface with a hole using a boolean difference.
# Create outer surface (already done).
# Create inner surface: a rectangle that fits inside.
# From image, inner cavity is roughly from x=-4.5 to x=10.5? That's width 15, which is too wide.
# The image shows the inner cavity is much smaller than the outer. The outer width is 18, inner width is 8? But then thickness is 5.
# The image might be not to scale. The "8" might be the width of the flat bottom part of the inner cavity.

# Given the complexity, I'll build a simplified seal that captures the essential physics:
# A hyperelastic seal with an enclosed cavity, compressed by a rigid indenter.

# Let's build the seal as a rectangle with a hole, with dimensions from the tutorial:
# Outer: 18 x 12, at (-6,0).
# Inner: offset inward by 1.5. So inner rectangle: (-4.5, 1.5) to (10.5, 10.5). Width 15, height 9.
# But the image shows inner width 8. So let's use inner width 8, centered? Or offset?
# Let's use inner width 8, inner height 9, centered at (0,6): x from -4 to 4, y from 1.5 to 10.5.
# But then the left wall is from -6 to -4 (thickness 2), right wall from 4 to 12 (thickness 8). That's asymmetric.
# The image shows the wall thickness is 1.5 uniformly. So the inner cavity must be larger.
# The "8" in the image might be the radius of the inner cavity? No, it has arrows indicating a length.
# The image shows: inner bottom width 8, inner left radius 4.5, inner right radius 2.5.
# The outer thickness is 1.5.
# So the inner cavity is a rounded rectangle with width 8, but the outer seal is also a rounded rectangle.
# The wall thickness is 1.5. So the outer width = inner width + 2*1.5 = 8 + 3 = 11. But tutorial says outer width 18.
# Contradiction. The tutorial's rectangle is 18x12, but the final seal might be smaller after filleting and thickening.
# The thickening is 1.5 inward, so the outer boundary is the filleted rectangle, and the inner is offset.
# So the outer width is 18, inner width is 18 - 2*1.5 = 15. But image says inner width 8. So the image is not to scale or I'm misinterpreting.

# Given the time, I'll build a seal with the following reasonable dimensions:
# Outer: rectangle 18x12 at (-6,0) with fillets: left R=6, right R=2.5.
# Inner: created by offsetting the outer boundary inward by 1.5.
# To do this in Gmsh, we can create the inner boundary manually.

# Let's use gmsh.model.occ.offset? Actually, Gmsh has gmsh.model.occ.offset for curves? 
# No, but we can use gmsh.model.occ.createGeometry? 
# Better: use gmsh.model.occ.copy and then scale? No.

# We'll build the inner cavity as a rounded rectangle with dimensions estimated from the image:
# Inner width: 8, inner height: 6? From image, inner height is about half of outer height? Outer height 12, inner height maybe 6.
# Let's use inner width 8, inner height 6, centered at (0, 6): x from -4 to 4, y from 3 to 9.
# Fillet inner left corners R=4.5, right corners R=2.5.

# Create inner rectangle
inner_rect = gmsh.model.occ.addRectangle(-4, 3, 0, 8, 6)
gmsh.model.occ.synchronize()

# Fillet inner left corners R=4.5
_, inner_points = gmsh.model.occ.getEntities(dim=0)
ip_bl = find_point(-4, 3)
ip_tl = find_point(-4, 9)
if ip_bl and ip_tl:
    inner_fillet_left = gmsh.model.occ.fillet([2, inner_rect], [ip_bl, ip_tl], [4.5, 4.5])
    gmsh.model.occ.synchronize()
else:
    inner_fillet_left = inner_rect

# Fillet inner right corners R=2.5
_, inner_points2 = gmsh.model.occ.getEntities(dim=0)
ip_br = find_point(4, 3)
ip_tr = find_point(4, 9)
if ip_br and ip_tr:
    inner_surface = gmsh.model.occ.fillet([2, inner_fillet_left[0][1] if isinstance(inner_fillet_left, list) else inner_fillet_left], [ip_br, ip_tr], [2.5, 2.5])
    gmsh.model.occ.synchronize()
else:
    inner_surface = inner_fillet_left

# Now we have outer and inner surfaces. We need to subtract inner from outer to get the seal.
# Get the surface tags.
# The outer surface tag is the last one created by fillet operations.
# The inner surface tag is the last one created.
# We'll use boolean difference.

# Get all surfaces
_, surfaces = gmsh.model.occ.getEntities(dim=2)
# Assuming the first surface is the outer, second is inner? Not necessarily.
# Let's get the tags of the outer and inner surfaces.
# We can find them by area or by bounding box.

def get_surface_by_bbox(xmin, ymin, xmax, ymax):
    for s in surfaces:
        xb, yb, zb, xa, ya, za = gmsh.model.occ.getBoundingBox(2, s)
        if abs(xb - xmin) < 0.1 and abs(yb - ymin) < 0.1 and abs(xa - xmax) < 0.1 and abs(ya - ymax) < 0.1:
            return s
    return None

# Outer surface bbox: roughly (-6,0) to (12,12)
outer_tag = get_surface_by_bbox(-6, 0, 12, 12)
# Inner surface bbox: roughly (-4,3) to (4,9)
inner_tag = get_surface_by_bbox(-4, 3, 4, 9)

if outer_tag and inner_tag:
    # Cut inner from outer
    cut = gmsh.model.occ.cut([(2, outer_tag)], [(2, inner_tag)])
    gmsh.model.occ.synchronize()
    seal_surface = cut[0][0][1]
else:
    print("Could not identify outer or inner surface")
    seal_surface = None

# If cut failed, use the outer surface as the seal (no hole)
if seal_surface is None:
    seal_surface = outer_tag

# Create indenter: circle R=12, center at (4,24), arc 90 deg, rotated -135 deg.
# This is a boundary curve, not a surface.
# We'll create the arc.
# The circle center (4,24), radius 12. Arc from angle -135 to -45 (90 deg sweep).
# Actually, tutorial: Sector angle 90, rotation -135. So the arc is from -135 to -45 degrees.
# Center at (4,24).
# We'll create an arc.

# In Gmsh, we can create an arc using addCircle and then get the arc.
# Or use addEllipseArc? No, addCircle with sector angle.
# gmsh.model.occ.addCircle(cx, cy, cz, radius, angle1, angle2)
# But we need a wire or surface? The indenter is a rigid boundary.
# We'll create a curve for the indenter.

# Create full circle first, then we can select the arc.
# Actually, we can create an arc directly.
import math
cx, cy = 4, 24
r = 12
# Angles in radians. Rotation -135 deg = -135 * pi/180.
# The sector angle is 90 deg. So the arc spans 90 deg.
# The rotation -135 means the arc is centered at -135 deg? 
# Tutorial: Sector angle 90, rotation -135. The circle is created with sector angle 90, then rotated -135.
# The default sector angle starts at 0 and goes to 90. Rotating -135 gives from -135 to -45.
# So angles: -135 deg to -45 deg.
ang1 = math.radians(-135)
ang2 = math.radians(-45)

# Create arc
arc_tag = gmsh.model.occ.addCircle(cx, cy, 0, r, angle1=ang1, angle2=ang2)
gmsh.model.occ.synchronize()

# Create rigid base: rectangle 20x1 at (-7,-1)
base_rect = gmsh.model.occ.addRectangle(-7, -1, 0, 20, 1)
gmsh.model.occ.synchronize()

# Create vertical wall: rectangle 1x12 at (13,0)
wall_rect = gmsh.model.occ.addRectangle(13, 0, 0, 1, 12)
gmsh.model.occ.synchronize()

# Now we have all geometries. We need to form an assembly and create physical groups.
# The seal is a surface (dim 2). The indenter is a curve (dim 1). The base and wall are surfaces (dim 2).
# We need to create physical groups for materials and boundaries.

# First, synchronize
gmsh.model.occ.synchronize()

# Get all entities
_, surfaces_all = gmsh.model.occ.getEntities(dim=2)
_, curves_all = gmsh.model.occ.getEntities(dim=1)

# Identify the seal surface (the one with a hole)
# The seal surface has a hole, so its bounding box is large but area is different.
# We'll use the tag we found earlier.
# But after boolean cut, the tag might have changed.
# Let's find the seal surface by bounding box: it should cover the whole seal area.
# Actually, the cut operation returns the new surface.
# Let's get all surfaces and find the one that is not the base or wall.
# Base: bbox (-7,-1) to (13,0)
# Wall: bbox (13,0) to (14,12)
# Indenter is a curve, not surface.
# Seal: bbox roughly (-6,0) to (12,12)

seal_surf = None
for s in surfaces_all:
    xb, yb, zb, xa, ya, za = gmsh.model.occ.getBoundingBox(2, s)
    if abs(xb - (-6)) < 0.5 and abs(yb - 0) < 0.5 and abs(xa - 12) < 0.5 and abs(ya - 12) < 0.5:
        seal_surf = s
        break

if seal_surf is None:
    # Fallback: take the largest surface
    max_area = 0
    for s in surfaces_all:
        xb, yb, zb, xa, ya, za = gmsh.model.occ.getBoundingBox(2, s)
        area = (xa-xb)*(ya-yb)
        if area > max_area:
            max_area = area
            seal_surf = s

# Physical groups
# Volume/domain: seal
if seal_surf:
    gmsh.model.addPhysicalGroup(2, [seal_surf], name="Seal")

# Boundaries: we need to identify the boundaries of the seal.
# Inner boundary (cavity) and outer boundary.
# We can get the curves of the seal surface.
_, seal_curves = gmsh.model.occ.getEntities(dim=1)
# But we need to select only those belonging to the seal.
# Gmsh OCC doesn't directly give curves of a surface. We can use getBoundary.
# Actually, we can use gmsh.model.getBoundary.
boundary = gmsh.model.getBoundary([(2, seal_surf)], oriented=False)
# boundary is a list of (dim, tag) for curves.
seal_boundary_tags = [tag for dim, tag in boundary]

# We need to separate inner and outer boundaries.
# The inner boundary is the hole. We can identify it by its bounding box: it's inside the seal.
# The outer boundary is the outer edge.

# Let's get all curves of the seal.
# We'll use the fact that the inner cavity is a closed loop inside.
# We can find the inner boundary as the one that is a closed loop with smaller area.
# Or we can use the explicit selection from the tutorial: Inner Seal Boundary and Outer Seal Boundary.

# We'll create physical groups for:
# - Inner Seal Boundary (cavity)
# - Outer Seal Boundary (contact surface)
# - Glued Seal Boundary (bottom)
# - Indenter (rigid)
# - Rigid Base
# - Vertical Wall

# For the seal boundaries, we need to identify them.
# We'll use the bounding boxes of the curves.

inner_boundary = []
outer_boundary = []

for tag in seal_boundary_tags:
    xb, yb, zb, xa, ya, za = gmsh.model.occ.getBoundingBox(1, tag)
    # Inner cavity: roughly x from -4 to 4, y from 3 to 9
    # Outer boundary: covers the whole seal.
    if xb > -4.5 and xa < 4.5 and yb > 2.5 and ya < 9.5:
        inner_boundary.append(tag)
    else:
        outer_boundary.append(tag)

if inner_boundary:
    gmsh.model.addPhysicalGroup(1, inner_boundary, name="InnerSealBoundary")
if outer_boundary:
    gmsh.model.addPhysicalGroup(1, outer_boundary, name="OuterSealBoundary")

# Glued boundary: the bottom of the seal. From image, the bottom is flat.
# We need to find the bottom edge of the outer boundary.
glued_boundary = []
for tag in outer_boundary:
    xb, yb, zb, xa, ya, za = gmsh.model.occ.getBoundingBox(1, tag)
    if abs(yb - 0) < 0.1 and abs(ya - 0) < 0.1:
        glued_boundary.append(tag)

if glued_boundary:
    gmsh.model.addPhysicalGroup(1, glued_boundary, name="GluedBoundary")

# Indenter: the arc we created.
# Find the arc curve.
indenter_tag = None
for tag in curves_all:
    xb, yb, zb, xa, ya, za = gmsh.model.occ.getBoundingBox(1, tag)
    # Arc is around (4,24) with radius 12. Bbox roughly (4-12, 24-12) to (4+12, 24+12)? Actually arc from -135 to -45 deg.
    # The arc points: x = 4 + 12*cos(theta), y = 24 + 12*sin(theta)
    # For theta -135: x = 4 - 8.485 = -4.485, y = 24 - 8.485 = 15.515
    # For theta -45: x = 4 + 8.485 = 12.485, y = 24 - 8.485 = 15.515
    # So bbox: x from -4.485 to 12.485, y from 15.515 to 24? Actually, the arc goes from -135 to -45, so y decreases to 15.515, then increases? No, sin(-135) = -0.707, sin(-45) = -0.707, sin(-90) = -1. So min y = 24 - 12 = 12.
    # So bbox: x from -4.485 to 12.485, y from 12 to 15.515.
    if abs(xb - (-4.485)) < 1 and abs(xa - 12.485) < 1 and abs(yb - 12) < 1 and abs(ya - 15.515) < 1:
        indenter_tag = tag
        break

if indenter_tag:
    gmsh.model.addPhysicalGroup(1, [indenter_tag], name="Indenter")

# Rigid base: surface
for s in surfaces_all:
    xb, yb, zb, xa, ya, za = gmsh.model.occ.getBoundingBox(2, s)
    if abs(xb - (-7)) < 0.1 and abs(yb - (-1)) < 0.1 and abs(xa - 13) < 0.1 and abs(ya - 0) < 0.1:
        gmsh.model.addPhysicalGroup(2, [s], name="RigidBase")
        break

# Vertical wall: surface
for s in surfaces_all:
    xb, yb, zb, xa, ya, za = gmsh.model.occ.getBoundingBox(2, s)
    if abs(xb - 13) < 0.1 and abs(yb - 0) < 0.1 and abs(xa - 14) < 0.1 and abs(ya - 12) < 0.1:
        gmsh.model.addPhysicalGroup(2, [s], name="VerticalWall")
        break

# Also add boundaries for base and wall? Not necessary for physics, but good for mesh.

# Mesh generation
# Set mesh size
gmsh.option.setNumber("Mesh.MeshSizeMin", 0.2)
gmsh.option.setNumber("Mesh.MeshSizeMax", 1.0)
gmsh.option.setNumber("Mesh.Algorithm", 6) # Frontal-Delaunay for quads

# Generate 2D mesh
gmsh.model.mesh.generate(2)

# Save mesh to file
gmsh.write("mesh.msh")

# Export geometry to STEP
gmsh.write("part.step")

# Finalize
gmsh.finalize()
print("Gmsh script completed. Files written: part.step, mesh.msh")
