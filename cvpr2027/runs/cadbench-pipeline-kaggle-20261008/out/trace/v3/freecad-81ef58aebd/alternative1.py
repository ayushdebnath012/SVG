from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

# Create the document
doc = App.newDocument("HingeLeaf")

# Define parameters as document objects for easy editing
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "hinge_leaf_plate_length", "Dimensions", "Length of the leaf plate")
params.addProperty("App::PropertyLength", "hinge_leaf_plate_width", "Dimensions", "Width of the leaf plate")
params.addProperty("App::PropertyLength", "hinge_leaf_plate_thickness", "Dimensions", "Thickness of the leaf plate")
params.addProperty("App::PropertyLength", "hinge_leaf_corner_arc_radius", "Dimensions", "Radius for rounding corners")
params.addProperty("App::PropertyLength", "barrel_knuckle_length", "Dimensions", "Length of one knuckle")
params.addProperty("App::PropertyLength", "outer_barrel_arc_radius", "Dimensions", "Outer radius of knuckle")
params.addProperty("App::PropertyLength", "inner_barrel_arc_radius", "Dimensions", "Inner radius of knuckle")
params.addProperty("App::PropertyLength", "barrel_knuckle_fillet_radius", "Dimensions", "Fillet radius for knuckles")
params.addProperty("App::PropertyLength", "barrel_knuckle_open_gap", "Dimensions", "Gap to open barrel")
params.addProperty("App::PropertyLength", "barrel_axis_offset_above_leaf_top", "Dimensions", "Offset of axis above top face")
params.addProperty("App::PropertyLength", "spacing_distance_between_barrel_knuckles", "Dimensions", "Distance between knuckles")
params.addProperty("App::PropertyLength", "mounting_hole_diameter", "Dimensions", "Diameter of mounting holes")
params.addProperty("App::PropertyInteger", "barrel_knuckle_count", "Dimensions", "Total number of knuckles")
params.addProperty("App::PropertyInteger", "number_of_mounting_holes", "Dimensions", "Total number of mounting holes")
params.addProperty("App::PropertyLength", "mounting_hole_center_horizontal_distance", "Dimensions", "Horizontal dist from centerline")
params.addProperty("App::PropertyLength", "mounting_hole_center_vertical_distance", "Dimensions", "Vertical dist from centerline")

# Set values
params.hinge_leaf_plate_length = 80.0
params.hinge_leaf_plate_width = 35.0
params.hinge_leaf_plate_thickness = 1.5
params.hinge_leaf_corner_arc_radius = 5.0
params.barrel_knuckle_length = 20.0
params.outer_barrel_arc_radius = 4.0
params.inner_barrel_arc_radius = 2.5
params.barrel_knuckle_fillet_radius = 0.5
params.barrel_knuckle_open_gap = 0.7819448
params.barrel_axis_offset_above_leaf_top = 3.9228258
params.spacing_distance_between_barrel_knuckles = 40.0
params.mounting_hole_diameter = 5.0
params.barrel_knuckle_count = 2
params.number_of_mounting_holes = 3
params.mounting_hole_center_horizontal_distance = 26.0
params.mounting_hole_center_vertical_distance = 13.0

# Create the Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Step 1: Create the Main Plate ---
# Sketch on XY plane
sketch_plate = body.newObject("Sketcher::SketchObject", "Plate_Sketch")
sketch_plate.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_plate.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch_plate.ConstrainAuto = False
sketch_plate.LockAuto = False

# Define geometry for the plate (centered)
# We will construct a path along the centerline and extrude, then add the thickness.
# Actually, it's easier to sketch the profile on XZ or YZ and extrude on Y?
# Let's stick to standard: Sketch on XY, extrude along Z for thickness.
# Plate is centered on its two in-plane axes. Let's say Length is along X, Width along Y.
# Center at (0,0).
# Length = 80, Width = 35.

# We need a closed profile for the base pad.
# Corners are rounded with quarter arcs tangent to the edges.
# Coordinates:
# Top-Left: (-40, 17.5)
# Top-Right: (40, 17.5)
# Bottom-Right: (40, -17.5)
# Bottom-Left: (-40, -17.5)
# Corners: 
# TL: Center at (-40+5, 17.5-5) = (-35, 12.5)
# TR: Center at (40-5, 17.5-5) = (35, 12.5)
# BR: Center at (40-5, -17.5+5) = (35, -12.5)
# BL: Center at (-40+5, -17.5+5) = (-35, -12.5)

# Add Points
sketch_plate.addGeometry(Part.Point(App.Vector(-40, 17.5, 0)), False)
sketch_plate.addGeometry(Part.Point(App.Vector(40, 17.5, 0)), False)
sketch_plate.addGeometry(Part.Point(App.Vector(40, -17.5, 0)), False)
sketch_plate.addGeometry(Part.Point(App.Vector(-40, -17.5, 0)), False)

# Add Arcs (Quarter circles)
# TL Arc: Start (-40, 17.5), End (-35, 12.5), Radius 5
sketch_plate.addGeometry(Part.Arc(App.Vector(-40, 17.5, 0), App.Vector(-35, 12.5, 0), App.Vector(-35, 12.5, 0), 0.0, 1.5707963267948966), False)
# TR Arc: Start (40, 17.5), End (35, 12.5), Radius 5
sketch_plate.addGeometry(Part.Arc(App.Vector(40, 17.5, 0), App.Vector(35, 12.5, 0), App.Vector(35, 12.5, 0), 0.0, 1.5707963267948966), False)
# BR Arc: Start (40, -17.5), End (35, -12.5), Radius 5
sketch_plate.addGeometry(Part.Arc(App.Vector(40, -17.5, 0), App.Vector(35, -12.5, 0), App.Vector(35, -12.5, 0), 0.0, 1.5707963267948966), False)
# BL Arc: Start (-40, -17.5), End (-35, -12.5), Radius 5
sketch_plate.addGeometry(Part.Arc(App.Vector(-40, -17.5, 0), App.Vector(-35, -12.5, 0), App.Vector(-35, -12.5, 0), 0.0, 1.5707963267948966), False)

# Add Lines
sketch_plate.addGeometry(Part.LineSegment(App.Vector(-40, 17.5, 0), App.Vector(40, 17.5, 0)), False)
sketch_plate.addGeometry(Part.LineSegment(App.Vector(40, 17.5, 0), App.Vector(40, -17.5, 0)), False)
sketch_plate.addGeometry(Part.LineSegment(App.Vector(40, -17.5, 0), App.Vector(-40, -17.5, 0)), False)
sketch_plate.addGeometry(Part.LineSegment(App.Vector(-40, -17.5, 0), App.Vector(-40, 17.5, 0)), False)

# Constraints
# Horizontal lines
sketch_plate.addConstraint(Sketcher.Constraint("Horizontal", 0)) # Line 0
sketch_plate.addConstraint(Sketcher.Constraint("Horizontal", 3)) # Line 3
# Vertical lines
sketch_plate.addConstraint(Sketcher.Constraint("Vertical", 1)) # Line 1
sketch_plate.addConstraint(Sketcher.Constraint("Vertical", 2)) # Line 2
# Dimensions
sketch_plate.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, -40, 40))
sketch_plate.addConstraint(Sketcher.Constraint("DistanceY", 0, 1, -17.5, 17.5))
# Coincident points for closure
sketch_plate.addConstraint(Sketcher.Constraint("Point", 0, "XY", 0, 0)) # Top Left Y
sketch_plate.addConstraint(Sketcher.Constraint("Point", 1, "XY", 40, 0)) # Top Right X
sketch_plate.addConstraint(Sketcher.Constraint("Point", 2, "XY", 40, 0)) # Top Right Y
sketch_plate.addConstraint(Sketcher.Constraint("Point", 3, "XY", -40, 0)) # Bottom Right X
sketch_plate.addConstraint(Sketcher.Constraint("Point", 4, "XY", -40, 0)) # Bottom Right Y
# Actually, simpler: just constrain distances and use the points implicitly defined by lines.
# Let's re-add constraints to ensure closure and symmetry
sketch_plate.addConstraint(Sketcher.Constraint("Point", 0, "XY", 0, 0)) # Center of top left point
sketch_plate.addConstraint(Sketcher.Constraint("Point", 1, "XY", 40, 0)) # Center of top right point
sketch_plate.addConstraint(Sketcher.Constraint("Point", 2, "XY", 40, 0)) # Center of bottom right point
sketch_plate.addConstraint(Sketcher.Constraint("Point", 3, "XY", -40, 0)) # Center of bottom left point
sketch_plate.addConstraint(Sketcher.Constraint("Point", 4, "XY", 0, -17.5)) # Center of bottom point
# This is getting complex with indices. Let's rely on the explicit coordinates and simple constraints.
# Re-adding constraints for robustness:
# Horizontal Top
sketch_plate.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, 0, 0)) # Force top line horizontal
# Horizontal Bottom
sketch_plate.addConstraint(Sketcher.Constraint("DistanceX", 3, 4, 0, 0))
# Vertical Right
sketch_plate.addConstraint(Sketcher.Constraint("DistanceY", 1, 2, 0, 0))
# Vertical Left
sketch_plate.addConstraint(Sketcher.Constraint("DistanceY", 0, 3, 0, 0))

# Center the sketch
sketch_plate.addConstraint(Sketcher.Constraint("Center", 0, "XY", 0, 0))
sketch_plate.addConstraint(Sketcher.Constraint("Center", 3, "XY", 0, 0))

sketch_plate.recompute()

# Pad the plate
pad_plate = body.newObject("PartDesign::Pad", "Pad_Plate")
pad_plate.Profile = sketch_plate
pad_plate.Length = params.hinge_leaf_plate_thickness
pad_plate.Type = "Solid"
pad_plate.makeSolid = True
pad_plate.setExpression("Length", "Parameters.hinge_leaf_plate_thickness")

# --- Step 2: Create Knuckles ---
# We need to create sketches for the knuckles. 
# Knuckles are aligned along the "positive longitudinal end". 
# Longitudinal end is +X. So knuckles start at X = 40 (edge of plate).
# They extend INWARD (towards -X).
# First knuckle: Start at X=40, End at X = 40 - barrel_knuckle_length.
# Second knuckle: Start at X = 40 - spacing, End at X = 40 - spacing - barrel_knuckle_length.

# Let's create a generic sketch object for the knuckle profile.
# We will place it on a plane perpendicular to the X-axis at the start of the first knuckle.
# Plane: XZ plane at X = 40.
# Wait, PartDesign Sketches are on faces or planes. 
# We can use the existing XZ plane but offset it.
# Or create a new plane. Let's create a plane for each knuckle.

# Helper to create a plane at X = x_pos
def create_plane_at_x(x_pos):
    p = doc.addObject("Part::Plane", f"Plane_Knuckle_{x_pos}")
    p.Placement = App.Placement(App.Vector(x_pos, 0, 0))
    return p

plane_knuckle_1 = create_plane_at_x(40.0)
plane_knuckle_2 = create_plane_at_x(40.0 - params.spacing_distance_between_barrel_knuckles)

# --- Knuckle 1 Sketch ---
sketch_knuckle_1 = body.newObject("Sketcher::SketchObject", "Sketch_Knuckle_1")
sketch_knuckle_1.Placement = App.Placement(App.Vector(40.0, 0, 0))
sketch_knuckle_1.AttachmentSupport = (doc.getObject("XZ_Plane"), []) # Default XZ is at 0,0,0
# We need to rotate/translate the sketch to lie on the plane at X=40.
# Actually, if we use the XZ plane at origin, and rotate 90 deg around Y, we get a plane at Y=0, Z=0... no.
# XZ plane is normal to Y. We need a plane normal to X.
# Let's use the YZ plane (normal to X) and shift it.
sketch_knuckle_1.Placement = App.Placement(App.Vector(40.0, 0, 0))
# But the default placement of a sketch on YZ plane puts the origin of the sketch at the origin of the world.
# We need to place the sketch such that its "local" YZ corresponds to the world plane at X=40.
# Since the sketch is on YZ, the X coordinate is constant. 
# So we just need to set the Placement to (40, 0, 0).
# However, the sketch's local axes must align with the plane.
# The YZ plane has axes Y and Z. Our sketch needs to be in the YZ plane.
# So we create the sketch geometry in YZ coordinates.

# Knuckle Geometry:
# Cross section in YZ plane.
# Center of knuckle? 
# "Join the outer barrel wall to the first broad face"
# "First broad face" is the plate face at X=40.
# "Radial opening points back toward that plate edge".
# So the barrel opens towards -X.
# The axis of the barrel is offset from the plate edge.
# "Beyond the opposite broad face by barrel_knuckle_open_gap" -> +Z direction?
# "Beyond the knuckle-side plate edge by barrel_axis_offset_above_leaf_top" -> +Y direction?
# Let's assume:
# Plate is in XY. Top face is Y = 17.5.
# Knuckle is on the side X=40.
# "Radial opening points back toward that plate edge" -> Opening is along -X.
# "Axis lies beyond the opposite broad face by barrel_knuckle_open_gap" -> Opposite broad face is Y = -17.5.
# So axis is at Y = -17.5 + barrel_knuckle_open_gap? Or maybe the "opposite" refers to the other knuckle?
# "Opposite broad face" usually means the face opposite to the one it joins. It joins the +Y face (top). Opposite is -Y face.
# So axis Y = -17.5 + barrel_knuckle_open_gap.
# "Beyond the knuckle-side plate edge by barrel_axis_offset_above_leaf_top" -> Knuckle-side plate edge is Y=17.5.
# So axis Y = 17.5 + barrel_axis_offset_above_leaf_top.
# Let's re-read carefully: "Its radial opening points back toward that plate edge".
# If it joins the top edge (Y=17.5), the opening points towards the top edge? No, "back toward".
# Maybe the knuckle is centered on the long edge?
# "Two aligned barrel knuckles along one long edge".
# So they are at Y = +/- 17.5? Or centered at Y=0?
# "Centered on its two in-plane axes". The plate is centered.
# "Two aligned barrel knuckles along one long edge". This implies they are on the same side? 
# Or one on each side of the long edge?
# "Along one long edge" usually means on the edge itself. But there are two knuckles.
# Are they both on the +X end? Yes, "Place the first flush with the plate's positive longitudinal end".
# Are they on the top and bottom of the plate? 
# "Two aligned barrel knuckles along one long edge".
# Let's assume they are symmetric about the X-axis (Y=0), located at Y = +/- 17.5.
# But the description says "along one long edge". This is singular.
# Maybe they are both on the +X end, one on top, one on bottom?
# Or maybe they are both on the +X end, and "edge
