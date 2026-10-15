import FreeCAD as App
import Part
from pathlib import Path

# Create a new document
doc = App.newDocument("SteppedShaft")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
doc.addObject("App::DocumentObjectGroup", "Group")
doc.recompute()

# --- Parameters ---
# We will store parameters in a VarSet object attached to the Body
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "shaft_section_1_diameter", "Dimensions", "Diameter of section 1")
params.addProperty("App::PropertyLength", "shaft_section_1_length", "Dimensions", "Length of section 1")
params.addProperty("App::PropertyLength", "shaft_section_2_diameter", "Dimensions", "Diameter of section 2")
params.addProperty("App::PropertyLength", "shaft_section_2_length", "Dimensions", "Length of section 2")
params.addProperty("App::PropertyLength", "shaft_section_3_diameter", "Dimensions", "Diameter of section 3")
params.addProperty("App::PropertyLength", "shaft_section_3_length", "Dimensions", "Length of section 3")
params.addProperty("App::PropertyLength", "shaft_section_4_diameter", "Dimensions", "Diameter of section 4")
params.addProperty("App::PropertyLength", "shaft_section_4_length", "Dimensions", "Length of section 4")
params.addProperty("App::PropertyLength", "shaft_section_5_diameter", "Dimensions", "Diameter of section 5")
params.addProperty("App::PropertyLength", "shaft_section_5_length", "Dimensions", "Length of section 5")

# Set default values as per description
params.shaft_section_1_diameter = 10.0
params.shaft_section_1_length = 40.0
params.shaft_section_2_diameter = 15.0
params.shaft_section_2_length = 30.0
params.shaft_section_3_diameter = 20.0
params.shaft_section_3_length = 40.0
params.shaft_section_4_diameter = 40.0
params.shaft_section_4_length = 10.0
params.shaft_section_5_diameter = 30.0
params.shaft_section_5_length = 20.0

# --- Sketch 1: Base Section (Section 1) ---
# We create a sketch on the XY plane. 
# The sketch will define the profile of the first section.
sketch1 = body.newObject("Sketcher::SketchObject", "Sketch_Section1")
sketch1.Placement = App.Placement(App.Vector(0, 0, 0))
sketch1.Support = (doc.getObject("XY_Plane"), [])
sketch1.MapMode = "FlatFace"

# Add geometry: A circle for the diameter and a line for the length
# Center at (0,0), Radius = D1/2
r1 = params.shaft_section_1_diameter / 2.0
sketch1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r1), False)

# Add a line from center to the edge to define the length direction
# We need a point on the circle. Let's use the circle's geometry to find a point.
# However, in FreeCAD scripting, it's easier to add a line segment manually if we know coordinates.
# We will add a line from (0,0,0) to (r1, 0, 0) to define the start of the length.
# Then we will add another line or use constraints.
# Actually, for a Pad, we need a closed profile. 
# Let's create a rectangle profile for the first section.
# Width = D1, Height = L1.
# Center at (0,0).
# Points: (-D1/2, -L1/2), (D1/2, -L1/2), (D1/2, L1/2), (-D1/2, L1/2)

# Let's use a simpler approach: Create a sketch with a circle and a line, then use constraints?
# No, Pad requires a closed profile.
# Let's create a rectangle directly in the sketch.
# We need to reference the parameters.
# We can add lines and then constrain them, or just add the vertices if we were using a different method.
# Standard way: Add lines, then constraints.
# But to make it fully parametric and robust, let's add 4 lines forming a rectangle.
# Line 1: (-D1/2, -L1/2) to (D1/2, -L1/2)
# Line 2: (D1/2, -L1/2) to (D1/2, L1/2)
# Line 2: (D1/2, L1/2) to (-D1/2, L1/2)
# Line 4: (-D1/2, L1/2) to (-D1/2, -L1/2)

# Since we can't easily create vertices with expressions in the addGeometry call without complex logic,
# we will create the lines with fixed coordinates relative to the center, and then use constraints 
# to link them to the parameters? 
# Actually, the cleanest way in FreeCAD script for a rectangle is to add 4 lines and constrain them.
# But wait, we can just add the lines with calculated coordinates based on the current parameter values 
# and then set the constraints. The constraints will update the geometry when recomputed.
# However, the coordinates of the lines themselves are static vectors. 
# To make the lines move with parameters, we usually need to use expressions in the sketcher constraints 
# or use a different approach.
# 
# Alternative: Use a single circle and a line, then use a "Pad" with a specific profile? 
# No, Pad needs a closed loop.
# 
# Best approach for parametric rectangle in script:
# 1. Add 4 lines.
# 2. Add constraints: Horizontal, Vertical, Coincident, Equal, etc.
# 3. This is tricky because the lines are static.
# 
# Let's try a different strategy: 
# Create a sketch with a circle (diameter) and a line (length). 
# Then use a "Pad" with "Midplane" or specific length? 
# No, the section lengths are different.
# 
# Let's go with the 4-line rectangle approach but initialize them at the center.
# We will add constraints to make it a rectangle centered at origin.
# We will NOT set the size via expressions on the lines themselves (which is hard), 
# but we will rely on the fact that we can update the sketch geometry? 
# No, that's not how it works.
# 
# Correct approach for parametric dimensions in Sketcher via script:
# We add the lines. We add constraints. 
# We cannot easily set the length of a line to a parameter expression in the script 
# unless we use the `setExpression` method on the constraint.
# 
# Let's do this:
# 1. Add 4 lines forming a rectangle centered at (0,0).
# 2. Add constraints to make it a rectangle.
# 3. Add constraints to set the width and height to the parameters.
#    - Width constraint: Distance between left and right vertical lines = D1
#    - Height constraint: Distance between top and bottom horizontal lines = L1
#    - Centering: Midpoint of width = 0, Midpoint of height = 0.
# 
# This is complex to script perfectly without errors.
# 
# Simpler approach: 
# Create a sketch with a circle (radius = D1/2).
# Create a sketch with a line (length = L1).
# Combine them? No.
# 
# Let's use the "Pad" feature's ability to extrude a sketch.
# If we create a sketch with a circle, we get a cylinder.
# If we create a sketch with a rectangle, we get a block.
# 
# Let's try to construct the rectangle using 4 lines and constraints.
# Line 1: (-D1/2, -L1/2) to (D1/2, -L1/2) -> Horizontal bottom
# Line 2: (D1/2, -L1/2) to (D1/2, L1/2) -> Vertical right
# Line 3: (D1/2, L1/2) to (-D1/2, L1/2) -> Horizontal top
# Line 4: (-D1/2, L1/2) to (-D1/2, -L1/2) -> Vertical left
# 
# Constraints:
# - Coincident: All 4 lines meet at corners.
# - Horizontal: Line 1 and 3.
# - Vertical: Line 2 and 4.
# - Equal: Line 1 length = Line 3 length. Line 2 length = Line 4 length.
# - Center: Midpoint of Line 1 = (0,0). Midpoint of Line 2 = (0,0).
# - Size: We can't easily set the size of the lines to parameters directly in the script 
#   without using expressions on the constraints.
# 
# Let's use expressions on the constraints!
# Constraint: "Distance" between two points? No, between two lines?
# We can use "Distance" constraint between two points on the lines?
# Or "Equal" constraint between a line length and a parameter?
# 
# Actually, there is a simpler way. 
# We can create the sketch, add the lines, and then use `setExpression` on the constraints 
# to drive the dimensions.
# 
# Let's implement the rectangle with constraints.
# 
# Step 1: Add 4 lines.
# Step 2: Add constraints.
# Step 3: Set expressions on constraints to drive dimensions.

# Define helper to add line
def add_line(sketch, p1, p2):
    sketch.addGeometry(Part.LineSegment(p1, p2), False)

# Define helper to add constraint
def add_constraint(sketch, c_type, idx1, idx2, idx3=None, idx4=None, expr=None):
    # idx1, idx2 are indices of the first geometry (line)
    # idx3, idx4 are indices of the second geometry (line or point)
    # This is tricky because indices are 0-based and refer to the list of geometries.
    # We need to be careful with the order.
    pass

# Let's just do it manually.
# Geometries:
# 0: Line 1 (Bottom)
# 1: Line 2 (Right)
# 2: Line 3 (Top)
# 3: Line 4 (Left)

# Add lines
# We need to calculate the initial positions. 
# We will use the current parameter values to place them initially.
# But the sketch will recompute, so we need to ensure the constraints hold.
# Initial placement:
# D1 = 10, L1 = 40.
# p1 = (-5, -20), p2 = (5, -20)
# p3 = (5, -20), p4 = (5, 20)
# p5 = (5, 20), p6 = (-5, 20)
# p7 = (-5, 20), p8 = (-5, -20)

# We will add the lines.
# Then we add constraints.
# Then we set expressions on the constraints to drive the size.

# Line 1: Bottom
p1 = App.Vector(-params.shaft_section_1_diameter/2, -params.shaft_section_1_length/2, 0)
p2 = App.Vector(params.shaft_section_1_diameter/2, -params.shaft_section_1_length/2, 0)
sketch1.addGeometry(Part.LineSegment(p1, p2), False)

# Line 2: Right
p3 = App.Vector(params.shaft_section_1_diameter/2, -params.shaft_section_1_length/2, 0)
p4 = App.Vector(params.shaft_section_1_diameter/2, params.shaft_section_1_length/2, 0)
sketch1.addGeometry(Part.LineSegment(p3, p4), False)

# Line 3: Top
p5 = App.Vector(params.shaft_section_1_diameter/2, params.shaft_section_1_length/2, 0)
p6 = App.Vector(-params.shaft_section_1_diameter/2, params.shaft_section_1_length/2, 0)
sketch1.addGeometry(Part.LineSegment(p5, p6), False)

# Line 4: Left
p7 = App.Vector(-params.shaft_section_1_diameter/2, params.shaft_section_1_length/2, 0)
p8 = App.Vector(-params.shaft_section_1_diameter/2, -params.shaft_section_1_length/2, 0)
sketch1.addGeometry(Part.LineSegment(p7, p8), False)

# Constraints
# 1. Coincident: p2 and p3 (Bottom-Right corner)
sketch1.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Line 0 end, Line 1 start
# 2. Coincident: p4 and p5 (Top-Right corner)
sketch1.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1)) # Line 1 end, Line 2 start
# 3. Coincident: p6 and p7 (Top-Left corner)
sketch1.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1)) # Line 2 end, Line 3 start
# 4. Coincident: p8 and p1 (Bottom-Left corner)
sketch1.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 0, 1)) # Line 3 end, Line 0 start

# 5. Horizontal: Line 0 and Line 2
sketch1.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
sketch1.addConstraint(Sketcher.Constraint("Horizontal", 2, 1))

# 6. Vertical: Line 1 and Line 3
sketch1.addConstraint(Sketcher.Constraint("Vertical", 1, 1))
sketch1.addConstraint(Sketcher.Constraint("Vertical", 3, 1))

# 7. Equal: Length of Line 0 = Length of Line 2
sketch1.addConstraint(Sketcher.Constraint("Equal", 0, 1, 2, 1))
# 8. Equal: Length of Line 1 = Length of Line 3
sketch1.addConstraint(Sketcher.Constraint("Equal", 1, 1, 3, 1))

# 9. Centering: Midpoint of Line 0 = (0,0)
# We can use "Center" constraint if available, or "Distance" from origin.
# Let's use "Distance" from origin for the midpoint.
# But Sketcher constraints don't have "Midpoint". 
# We can use "Point" constraint? No.
# We can use "Distance" between the midpoint of the line and the origin (0,0).
# But we don't have a point object for the midpoint.
# 
# Alternative: Use "Center" constraint on the line relative to the plane?
# Sketcher has "Center" constraint: "Center" on a line relative to a plane?
# Yes, "Center" constraint can be used.
# Let's try: "Center" on Line 0 relative to XY_Plane? No, that constrains the line to be centered on the plane.
# We want the line to be centered at (0,0).
# 
# Actually, we can use "Distance" constraint between the midpoint of the line and the origin.
# But we need a point.
# 
# Let's use a simpler trick: 
# Add a point at (0,0) and constrain the lines to be symmetric?
# Or use "Center" constraint on the line itself?
# In FreeCAD Sketcher, "Center" constraint is available for lines.
# It constrains the center of the line to the center of the plane (if FlatFace) or a specific point.
# Let's assume "Center" works.
# 
# If not, we can use "Distance" from the origin.
# Let's try to add a point at (0,0) first.
# Point at origin:
# We can add a point geometry? No, Sketcher doesn't have a "Point" geometry type in the same way.
# But we can use a "Point" constraint?
# 
# Let's use the "Center" constraint.
# Constraint: "Center" on Line 0.
# This will center the line on the XY plane.
# But we need to center it on the Z axis too? No, the line is in XY plane.
# Centering on XY plane means the midpoint is at (0,0) in XY.
# So:
sketch1.addConstraint(Sketcher.Constraint("Center", 0, 1)) # Center Line 0
sketch1.addConstraint(Sketcher.Constraint("Center", 1, 1)) # Center Line 1 (Vertical line)

# 10. Drive dimensions with parameters
# We need to set the length of Line 0 to D1 and Line 1 to L1.
# We can use "Distance" constraint between the endpoints?
# Or "Equal" constraint between the line length and a parameter?
# Sketcher constraints support expressions.
# We can add a "Distance" constraint between two points?
# Or we can use "Equal" constraint between the line length and a parameter.
# 
# Let's try: "Equal" constraint between Line 0 length and a parameter.
# But we need to
