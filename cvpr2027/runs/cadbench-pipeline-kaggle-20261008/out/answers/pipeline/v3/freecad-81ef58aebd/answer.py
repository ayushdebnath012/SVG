import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Dimensions as specified in the prompt
params = {
    "hinge_leaf_plate_thickness": 1.5,
    "hinge_leaf_corner_arc_radius": 5.0,
    "hinge_leaf_plate_length": 80.0,
    "hinge_leaf_plate_width": 35.0,
    "plate_corner_quarter_angle": 90.0, # Degrees, though geometry uses 90 deg arc
    
    "barrel_knuckle_length": 20.0,
    "outer_barrel_arc_radius": 4.0,
    "inner_barrel_arc_radius": 2.5,
    "barrel_knuckle_fillet_radius": 0.5,
    "barrel_knuckle_open_gap": 0.7819448,
    "barrel_axis_offset_above_leaf_top": 3.9228258,
    
    "barrel_knuckle_count": 2,
    "spacing_distance_between_barrel_knuckles": 40.0,
    
    "mounting_hole_diameter": 5.0,
    "number_of_mounting_holes": 3,
    "mounting_hole_center_horizontal_distance": 26.0,
    "mounting_hole_center_vertical_distance": 13.0
}

# --- Document Setup ---
doc = App.newDocument("HingeLeaf")
doc.Label = "HingeLeaf"

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters Object ---
# We create a VarSet to hold the parameters as editable properties
param_obj = body.newObject("App::VarSet", "Parameters")
for key, value in params.items():
    param_obj.addProperty("App::PropertyFloat", key, "Parameters", key)
    param_obj[key] = value

# --- Helper to get parameter value ---
def get_param(name):
    return param_obj[name]

# --- Feature 1: Base Plate Sketch ---
# Create a sketch on the XY plane
sketch_plate = body.newObject("Sketcher::SketchObject", "PlateSketch")
sketch_plate.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_plate.ConstrainToCurrentPlacement = True
sketch_plate.ConstrainToCurrentView = True
sketch_plate.MapMode = "FlatFace"
sketch_plate.Support = (doc.getObject("XY_Plane"), [""])

# Define the plate geometry
# Center at (0,0). Length along X, Width along Y.
# Corners are rounded.
# We will construct the profile using lines and circles.
# 
# Coordinates:
# Center: (0, 0)
# Length: L, Width: W
# Radius: R
# 
# Points:
# P1 (Left): (-L/2, -W/2)
# P2 (Left Top): (-L/2, W/2)
# P3 (Right Top): (L/2, W/2)
# P4 (Right): (L/2, -W/2)
# 
# Arcs:
# Left: Center (-L/2, 0), Radius R
# Right: Center (L/2, 0), Radius R

L = get_param("hinge_leaf_plate_length")
W = get_param("hinge_leaf_plate_width")
R = get_param("hinge_leaf_corner_arc_radius")

# Add Geometry
# Left Vertical Line
sketch_plate.addGeometry(Part.LineSegment(App.Vector(-L/2, -W/2, 0), App.Vector(-L/2, W/2, 0)), False)
# Top Horizontal Line
sketch_plate.addGeometry(Part.LineSegment(App.Vector(-L/2, W/2, 0), App.Vector(L/2, W/2, 0)), False)
# Right Vertical Line
sketch_plate.addGeometry(Part.LineSegment(App.Vector(L/2, W/2, 0), App.Vector(L/2, -W/2, 0)), False)
# Bottom Horizontal Line
sketch_plate.addGeometry(Part.LineSegment(App.Vector(L/2, -W/2, 0), App.Vector(-L/2, -W/2, 0)), False)

# Left Corner Arc
sketch_plate.addGeometry(Part.Circle(App.Vector(-L/2, 0, 0), App.Vector(0, 0, 1), R), False)
# Right Corner Arc
sketch_plate.addGeometry(Part.Circle(App.Vector(L/2, 0, 0), App.Vector(0, 0, 1), R), False)

# Constraints
# Coincident points for corners
# Left Top
sketch_plate.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Line 0, Pt 2 (Top) with Line 1, Pt 1 (Start) - actually indices are tricky.
# Let's use explicit indices based on addGeometry order.
# 0: Left Vert, 1: Top Horiz, 2: Right Vert, 3: Bottom Horiz
# 4: Left Arc, 5: Right Arc

# Left Top Corner (Intersection of 0 and 1)
# Line 0 end is (-L/2, W/2). Line 1 start is (-L/2, W/2).
sketch_plate.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # End of 0, Start of 1
# Left Bottom Corner (Intersection of 0 and 3)
# Line 0 start is (-L/2, -W/2). Line 3 end is (-L/2, -W/2).
sketch_plate.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 3, 2)) # Start of 0, End of 3

# Right Top Corner (Intersection of 1 and 2)
# Line 1 end is (L/2, W/2). Line 2 start is (L/2, W/2).
sketch_plate.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1)) # End of 1, Start of 2
# Right Bottom Corner (Intersection of 2 and 3)
# Line 2 end is (L/2, -W/2). Line 3 start is (L/2, -W/2).
sketch_plate.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1)) # End of 2, Start of 3

# Tangent constraints for arcs
# Left Arc (4) tangent to Left Vert (0)
# Arc 4 center (-L/2, 0). Line 0 is x = -L/2. They are tangent.
# We need to constrain the arc to be tangent to the line.
# Sketcher Constraint "Tangent"
sketch_plate.addConstraint(Sketcher.Constraint("Tangent", 4, 1, 0, 1)) # Arc 4 tangent to Line 0
sketch_plate.addConstraint(Sketcher.Constraint("Tangent", 4, 1, 0, 2)) # Arc 4 tangent to Line 0 (other side)
# Actually, simpler: constrain arc center to line? No, standard way is Tangent.
# Let's rely on the geometry construction being perfect and add tangent constraints to be safe.
# Arc 4 is tangent to Line 0 at (-L/2, R) and (-L/2, -R).
# Line 0 is vertical. Arc 4 is centered on the line.
# We can constrain the Arc center to the Line? No, center is on the line.
# Let's just add Tangent constraints.
sketch_plate.addConstraint(Sketcher.Constraint("Tangent", 4, 1, 0, 1))
sketch_plate.addConstraint(Sketcher.Constraint("Tangent", 4, 1, 0, 2))

# Right Arc (5) tangent to Right Vert (2)
sketch_plate.addConstraint(Sketcher.Constraint("Tangent", 5, 1, 2, 1))
sketch_plate.addConstraint(Sketcher.Constraint("Tangent", 5, 1, 2, 2))

# Tangent between Top Horiz (1) and Left Arc (4)
sketch_plate.addConstraint(Sketcher.Constraint("Tangent", 1, 1, 4, 1))
sketch_plate.addConstraint(Sketcher.Constraint("Tangent", 1, 1, 4, 2))

# Tangent between Top Horiz (1) and Right Arc (5)
sketch_plate.addConstraint(Sketcher.Constraint("Tangent", 1, 1, 5, 1))
sketch_plate.addConstraint(Sketcher.Constraint("Tangent", 1, 1, 5, 2))

# Tangent between Bottom Horiz (3) and Left Arc (4)
sketch_plate.addConstraint(Sketcher.Constraint("Tangent", 3, 1, 4, 1))
sketch_plate.addConstraint(Sketcher.Constraint("Tangent", 3, 1, 4, 2))

# Tangent between Bottom Horiz (3) and Right Arc (5)
sketch_plate.addConstraint(Sketcher.Constraint("Tangent", 3, 1, 5, 1))
sketch_plate.addConstraint(Sketcher.Constraint("Tangent", 3, 1, 5, 2))

# Symmetry constraints for the whole shape
# Mirror across X axis (Y=0)
# We can constrain the center of arcs to Y=0
sketch_plate.addConstraint(Sketcher.Constraint("PointYOnLine", 4, 1, 0, 1)) # Center of arc 4 on X axis
sketch_plate.addConstraint(Sketcher.Constraint("PointYOnLine", 5, 1, 0, 1)) # Center of arc 5 on X axis
# Center of plate (0,0) is implicit.
# Constrain Top edge Y = W/2
sketch_plate.addConstraint(Sketcher.Constraint("PointYOnLine", 1, 1, 0, 1)) # Top edge Y coordinate
# Constrain Bottom edge Y = -W/2
sketch_plate.addConstraint(Sketcher.Constraint("PointYOnLine", 3, 1, 0, 1)) # Bottom edge Y coordinate
# Constrain Left edge X = -L/2
sketch_plate.addConstraint(Sketcher.Constraint("PointXOnLine", 0, 1, 0, 1)) # Left edge X coordinate
# Constrain Right edge X = L/2
sketch_plate.addConstraint(Sketcher.Constraint("PointXOnLine", 2, 1, 0, 1)) # Right edge X coordinate

# --- Feature 2: Pad the Plate ---
pad_plate = body.newObject("PartDesign::Pad", "PadPlate")
pad_plate.Profile = sketch_plate
pad_plate.Length = get_param("hinge_leaf_plate_thickness")
pad_plate.Type = "Solid"
pad_plate.Midplane = False
pad_plate.Reversed = False

# --- Feature 3: Knuckle Sketch ---
# We need to create a sketch for the knuckle profile.
# The knuckle is a cylinder with a radial cut.
# We will create this sketch on the XZ plane (or a plane parallel to it).
# Let's create a plane for the knuckle sketch.
# The knuckle axis is parallel to the Y axis (transverse).
# Wait, the prompt says: "barrel axis lies beyond the opposite broad face... and beyond the knuckle-side plate edge".
# Plate is in XY plane. Thickness is Z.
# "Opposite broad face" -> Z = thickness/2.
# "Knuckle-side plate edge" -> X = L/2 (assuming knuckles are on the right edge).
# So the knuckle axis is at X = L/2 + barrel_axis_offset_above_leaf_top, Z = thickness/2 + barrel_knuckle_open_gap.
# The knuckle extends along the Y axis (transverse).
# Length of knuckle is along Y.
# Cross section is in XZ plane.

# Create a plane for the knuckle sketch
# Origin at the center of the knuckle cross-section.
# We need to calculate the position.
# Plate Center: (0, 0, 0)
# Plate Top Face: Z = thickness/2
# Plate Right Edge: X = L/2
# Knuckle Axis X: L/2 + barrel_axis_offset_above_leaf_top
# Knuckle Axis Z: thickness/2 + barrel_knuckle_open_gap
# Knuckle Axis Y: 0 (Centered transversely)

X_knuckle = L/2 + get_param("barrel_axis_offset_above_leaf_top")
Z_knuckle = get_param("hinge_leaf_plate_thickness")/2 + get_param("barrel_knuckle_open_gap")
Y_knuckle = 0

# Create a plane perpendicular to the Y axis at Y=0, shifted to X_knuckle, Z_knuckle?
# No, the sketch needs to be in the XZ plane.
# We can create a sketch on the XZ plane and then place it.
# Or create a plane.
# Let's create a sketch on the XZ plane and place it at the correct location.
# But the sketch origin is (0,0,0) in the sketcher.
# We will place the sketch object.

sketch_knuckle = body.newObject("Sketcher::SketchObject", "KnuckleSketch")
sketch_knuckle.Placement = App.Placement(App.Vector(X_knuckle, 0, Z_knuckle))
sketch_knuckle.ConstrainToCurrentPlacement = True
sketch_knuckle.MapMode = "FlatFace"
# Attachment support: XZ plane is not a default plane in the document usually, 
# but we can attach to the Body's local coordinate system or use a plane.
# Since we are placing the sketch, we can just define the geometry relative to the placement.
# However, Sketcher::SketchObject needs a Support.
# Let's create a plane object first.
plane_knuckle = doc.addObject("Part::Plane", "PlaneKnuckle")
plane_knuckle.Placement = App.Placement(App.Vector(X_knuckle, 0, Z_knuckle))
plane_knuckle.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 0) # Rotate 90 deg around Y? No.
# XZ plane normal is Y.
# Default XY plane normal is Z.
# We want the sketch to lie in the XZ plane.
# So the normal of the plane should be Y (0, 1, 0).
# Placement: Vector(X_knuckle, 0, Z_knuckle).
# Rotation: To align Z axis of sketch to Y axis of world?
# Sketcher default: Sketch lies in XY plane of its placement.
# We want Sketch to lie in XZ plane of world.
# So we need to rotate the sketch's local XY to world XZ.
# World X -> Sketch X
# World Z -> Sketch Y
# World Y -> Sketch Z (Normal)
# Rotation: 90 deg around X axis?
# If we rotate 90 deg around X:
# (0,0,1) [Z] -> (0,1,0) [Y]. Correct.
# (1,0,0) [X] -> (1,0,0) [X]. Correct.
# (0,1,0) [Y] -> (0,0,-1) [-Z]. Correct.
# So Rotation = App.Rotation(App.Vector(1, 0, 0), 90)

sketch_knuckle.Placement.Rotation = App.Rotation(App.Vector(1, 0, 0), 90)
sketch_knuckle.Support = (plane_knuckle, [""])

# Knuckle Geometry
# Outer Radius: R_out
# Inner Radius: R_in
# Length: L_knuckle
# Cut: Radial cut from inner radius to outer radius?
# "Straight radial edge joins the inner and outer barrel walls."
# "Radial opening points back toward that plate edge" -> Towards negative X.
# So the cut is on the left side of the knuckle (relative to the knuckle axis).
# The knuckle is a cylinder.
# We define the profile in the XZ plane (local to sketch).
# X axis of sketch points to World X.
# Z axis of sketch points to World Y (due to rotation).
# Wait, if Sketch lies in XZ plane, and we rotated 90 deg around X:
# Sketch X = World X.
# Sketch Y = World Z.
# Sketch Z = -World Y.
# So the sketch is in the XZ plane.
# The knuckle extends along the World Y axis.
# In the sketch, the "length" of the knuckle is along the Sketch Z axis (which is -World Y).
# But the knuckle is symmetric around Y=0.
# So the profile should be symmetric around Sketch Z=0.
# The knuckle length is L_knuckle.
# So the profile extends from -L_knuckle/2 to +L_knuckle/2 along the Sketch Z axis.
# The cross section is in the Sketch X axis.
# Outer wall: Circle of radius R_out centered at (0, 0) in Sketch XZ?
# No, the knuckle is a cylinder.
# Profile: A rectangle of width 2*R_out and height L_knuckle, with a cutout.
# Cutout: A rectangle of width 2*R_in and height L_knuckle, shifted to the left (negative X).
# The cutout goes from X = -R_in to X = -R_out?
# "Straight radial edge joins the inner and outer barrel walls."
# This implies the
