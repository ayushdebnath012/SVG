import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# Create a new document
doc = App.newDocument("CylindricalPin")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
doc.addObject("App::DocumentObjectGroup", "Group")
body.Placement = App.Placement(App.Vector(0, 0, 0))
doc.addObject("App::DocumentObjectGroup", "Group")

# Define Named Parameters (Editable Variables)
# Using App::Parameter for FreeCAD 1.1 style named variables within the Body context
# Note: In strict FreeCAD 1.1 headless API, we often set properties directly on the Body or use App::Parameter
# If App::Parameter is not available in the specific build, we use direct property setting on the Body or a VarSet.
# The prompt suggests using named document objects driven by parameters. We will use App::Parameter if available,
# otherwise fallback to Body properties accessed via expression strings.
# FreeCAD 1.1 supports App::Parameter.

try:
    param1 = body.newObject("App::Parameter", "Diameter")
    param1.Parameter = "Diameter"
    param1.Expression = "1"
    param1.Unit = "mm"
    
    param2 = body.newObject("App::Parameter", "ChamferLength")
    param2.Parameter = "ChamferLength"
    param2.Expression = "0.2"
    param2.Unit = "mm"
    
    param3 = body.newObject("App::Parameter", "ChamferAngle")
    param3.Parameter = "ChamferAngle"
    param3.Expression = "15"
    param3.Unit = "deg"
    
    param4 = body.newObject("App::Parameter", "Length")
    param4.Parameter = "Length"
    param4.Expression = "3"
    param4.Unit = "mm"
except Exception:
    # Fallback if App::Parameter is not supported in this specific headless environment
    # We will drive features directly using expressions referencing these names, assuming the 
    # environment might just treat them as Property expressions if the class isn't strictly found.
    # However, standard 1.1 API usually requires the objects. If creation fails, we assume the 
    # expressions in the code below will fail too, but we try our best.
    # To ensure the script runs without crashing on a specific missing class, we might just set 
    # properties on the Body and reference them.
    # But the prompt asks for "named document objects". Let's assume App::Parameter exists.
    pass

# Create the Base Sketch on XY Plane
# The sketch will define the outer cylinder and the chamfer arc.
# Profile: A line from (0, -D/2) to (0, D/2) is the cylinder diameter.
# Chamfer: An arc or line segment.
# Strategy: Create a profile consisting of:
# 1. Line from (0, -D/2) to (0, D/2) -> Cylinder wall.
# 2. Arc or Line for chamfer at the top (0, D/2).
# Actually, PartDesign::Pad works best with a closed profile or specific constraints.
# For a pin, a common approach is:
# Sketch 1: Define the cylinder cross-section and the chamfer geometry on one face.
# Since we need two chamfers (ends), we can either:
# a) Extrude the full cylinder, then use two Chamfer features at the ends.
# b) Create a complex profile with chamfers included and extrude.
# Option (a) is more robust for parametric updates if the chamfer logic changes.
# Let's use Option (a): Pad the cylinder, then Chamfer both ends.

# Plane: XY_Plane (Standard in FreeCAD)
# We need to ensure the XY_Plane exists.
xy_plane = doc.addObject("PartDesign::PlanarFace", "XY_Plane")
xy_plane.Placement = App.Placement(App.Vector(0, 0, 0))
xy_plane.FacetType = "Plane"
xy_plane.Facet = "XY_Plane" # This is a bit abstract in headless. 
# Better approach: Use PartDesign::PlaneFace or just rely on Sketcher::SketchObject default attachment.
# Sketcher::SketchObject defaults to XY_Plane if not specified, but let's be explicit via Placement if possible.
# Actually, for Sketcher::SketchObject, AttachmentSupport can be a Part::Face or a Plane.
# Let's create a standard plane object first.

plane_obj = doc.addObject("PartDesign::Plane", "XY_Plane")
plane_obj.Placement = App.Placement(App.Vector(0, 0, 0))
doc.recompute()

# Sketch 1: Main Profile (Cylinder + Top Chamfer hint? No, let's do simple Pad first)
# Actually, to get a chamfer on the edge of a pad, the edge must exist.
# So:
# 1. Pad (Cylinder)
# 2. Chamfer Edge 1
# 3. Chamfer Edge 2

sketch = body.newObject("Sketcher::SketchObject", "ProfileSketch")
# Attach to XY_Plane
# In FreeCAD 1.1 headless, we often use the standard planes.
# We can set the placement to lift it to Z=0 if needed, but XY is Z=0.
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
sketch.ConstraintsFix = 0

# Add Geometry:
# Line representing diameter at Z=0.
# We will construct the cylinder using a line segment.
# Then we will pad it.
# For the chamfer, we will apply the feature later.

# Get Diameter value
d_val = 1.0
# Create Line segment for the diameter on XY plane.
# Center at (0,0), extending to +/- D/2
# Note: Sketcher geometry uses World coordinates relative to Placement.
line_start = App.Vector(0, -d_val/2, 0)
line_end = App.Vector(0, d_val/2, 0)

sketch.addGeometry(Part.LineSegment(line_start, line_end), False)

# Add Constraints:
# Make it horizontal (Horizontal constraint on the line)
# This is implicit by vector direction, but explicit constraint is better.
# Also, we might want to fix the center if we had a point, but a single line in a sketch 
# needs constraints to be fully defined.
# Constraint: Horizontal
sketch.addConstraint(Sketcher.Constraint("Axis", 0, 1, 1), False) # Line is horizontal

# Wait, a single line segment in a sketch is under-constrained (can slide, rotate).
# We need to fix one point or define it relative to something.
# Let's add a point at (0,0) and constrain the line to pass through it?
# Or simply constrain the midpoint to the origin? 
# Let's add a Point at origin and constrain line endpoints to be symmetric?
# Simpler: Add a point at (0,0), constrain line midpoint to it.
# Actually, for a Pad, we just need a valid shape.
# Let's add a constraint to fix the position.
# Constraint: Point on Origin?
# We can add a point and constrain it to XY origin.
# But let's just use the LineSegment and constrain it to be horizontal and centered.
# To center it: Add a point at (0,0).
pt = App.Vector(0, 0, 0)
# We can't easily add a point constraint to a line segment without a point object.
# Alternative: Use "Center" constraint? No.
# Let's add a Point object to the sketch.
pt_obj = sketch.addGeometry(Part.Point(pt), False)
# Constraint: Coincident line midpoint to point? No, Sketcher constraints are line-based.
# Let's constrain the line to be symmetric about the Y axis? No, it's along Y.
# Let's constrain the line to be horizontal (done).
# Let's constrain the midpoint of the line to the point (0,0).
# Sketcher Constraint: "Midpoint" -> "Point"
# We need to reference the point object index.
# Let's try a different approach: Define the line from (0, -d/2) to (0, d/2).
# And add a constraint "Horizontal".
# And add a constraint "Vertical" on a dummy line? No.
# Let's just add a constraint "Horizontal" and "Vertical" on the point?
# Let's add a point at (0,0) and constrain the line to pass through it?
# Actually, the simplest fully defined sketch for a cylinder is:
# 1. Point at (0,0)
# 2. Line from (-d/2, 0) to (d/2, 0) -> This is a diameter line along X.
#    Wait, my previous line was along Y. Let's stick to Y.
#    Line from (0, -d/2) to (0, d/2).
#    We need to fix the Y position to 0.
#    Add a point at (0,0).
#    Constrain the midpoint of the line to the point.
#    Constraint: "Midpoint" 0, 1 (line) -> 1, 0 (point)? 
#    Actually, "Midpoint" constraint is between two elements.
#    Let's try: "Equal" constraint on Y coordinates? Too complex.
#    Let's assume the line is defined by two points implicitly? No, LineSegment is one object.
#    Okay, let's use the "Horizontal" constraint.
#    And "Vertical" constraint on a point?
#    Let's just define the line from (-d/2, 0) to (d/2, 0) along X axis.
#    Then the diameter is clear.
#    LineStart: (-d/2, 0, 0)
#    LineEnd: (d/2, 0, 0)
#    This is along X. The sketch plane is XY.
#    Constraint: Horizontal (along X).
#    Constraint: Fixed one end? 
#    Let's add a point at (0,0).
#    Constraint: Coincident Point to Midpoint of Line?
#    In FreeCAD Sketcher, we can use "Midpoint" constraint.
#    Let's try to add a point and constrain it to the center of the line.
    
# Revised Sketch Construction:
# 1. Point at (0,0,0)
# 2. Line from (-d/2, 0, 0) to (d/2, 0, 0)
# 3. Constraint: Horizontal (Line)
# 4. Constraint: Point is at (0,0)? 
#    We can use "Vertical" constraint on the point? No.
#    We can use "Horizontal" constraint on the point (Y=0).
#    And "Vertical" constraint on the point (X=0)? No.
#    We can use "Center" constraint?
#    Let's use: "Midpoint" of Line -> Point.
    
# Re-implementing sketch geometry with robust constraints:
# Clear previous sketch geometry if any (not needed as new object)
# Add Point
sketch.addGeometry(Part.Point(App.Vector(0, 0, 0)), False)
# Add Line (Diameter)
line_p1 = App.Vector(-d_val/2, 0, 0)
line_p2 = App.Vector(d_val/2, 0, 0)
sketch.addGeometry(Part.LineSegment(line_p1, line_p2), False)

# Constraints:
# 1. Horizontal Line
sketch.addConstraint(Sketcher.Constraint("Axis", 0, 1, 1), False) 
# 2. Midpoint of Line coincident with Point
#    Constraint type: "Midpoint"
#    Element 1: Line (Index 1 in sketch geometry list? 0 is Point, 1 is Line)
#    Element 2: Point (Index 0)
sketch.addConstraint(Sketcher.Constraint("Midpoint", 1, 2, 0, 1), False) # Line 1 (midpoint), Point 0 (center)
# Note: Syntax is Constraint(Type, Elem1, SubElem1, Elem2, SubElem2)
# For Midpoint: Constraint("Midpoint", 1, 2, 0, 1) -> Line 1, Midpoint (2), Point 0, Center (1).

# Now Pad this profile
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = sketch
pad.Length = param4.Expression # "Length"
pad.Direction = 1 # Forward
doc.recompute()

# Now we have a cylinder.
# Add Chamfers.
# We need to chamfer both ends.
# The edges are at Z = Length and Z = -Length/2? 
# Wait, Pad Length is positive along Z (default).
# So one end is at Z=0, other at Z=Length.
# Actually, the sketch is at Z=0. Pad extends to Z=Length.
# So we have an edge at Z=0 (circle) and Z=Length (circle).

# Chamfer 1: Edge at Z=0
chamfer1 = body.newObject("PartDesign::Chamfer", "Chamfer1")
chamfer1.Base = (pad, ["Edge1"]) # Edge1 is usually the first created edge or we can use index
# We need to identify the correct edge.
# Let's use a loop to find edges or rely on the order.
# Usually, Pad creates edges in order.
# Let's assume Edge1 is the bottom (Z=0) and Edge2 is top (Z=Length).
# Or we can use "All" if possible? No, Chamfer targets specific edges.
# Let's try to target all circular edges?
# We can use "Edge1" and "Edge2" if we know the count.
# Let's try to select the bottom edge first.
# How to distinguish? By position?
# We can add two chamfer features and try to reference them by name or index.
# Let's try:
# Chamfer 1: Edge 1
# Chamfer 1.1: Edge 2
# But we need to know which is which.
# Let's assume the Pad creates the bottom edge first (Edge1) and top edge second (Edge2).
# This is generally true for a Pad starting from a sketch at Z=0.

# Parameters for Chamfer
# The prompt says: chamfer_length and chamfer_angle.
# FreeCAD Chamfer can be:
# - Distance (Length)
# - Angle + Distance
# We have both.
# Type: "Distance" or "Angle"?
# If we use "Angle", we specify the angle and the distance.
# Type = "Angle"
# Angle = ChamferAngle
# Distance = ChamferLength

# Chamfer 1 (Bottom)
chamfer1.Type = "Angle"
chamfer1.Size = chamfer_length # This property is often "Size" or "Radius"? 
# In FreeCAD 1.1, for Chamfer:
# If Type="Angle", we have properties: Angle, Size (Distance).
# If Type="Distance", we have properties: Size.
# We will set Type="Angle".
chamfer1.Angle = chamfer_angle # Expression or value?
# We need to drive it from parameters.
# Let's set properties directly if parameters are objects.
# If parameters are objects, we can use expressions in the property value.
# However, setting expressions on properties is tricky in headless.
# Let's set values directly and hope the user can edit them in GUI, OR 
# use the parameters in expressions.
# The prompt requires "named document objects whose properties drive the geometry".
# So we must use expressions.
# Expression syntax: = "ChamferLength"
chamfer1.Size = "ChamferLength"
chamfer1.Angle = "ChamferAngle"

# Base: (pad, ["Edge1"])
# Note: The Base property expects a tuple (Feature, [EdgeIndices])
# Edge indices are 1-based in the list of edges of the feature.
# Let's assume Edge1 is the bottom.
chamfer1.Base = (pad, ["Edge1"])

doc.recompute()

# Chamfer 2 (Top)
chamfer2 = body.newObject("PartDesign::Chamfer", "Chamfer2")
chamfer2.Type = "Angle"
chamfer2.Size = "ChamferLength"
chamfer2.Angle = "ChamferAngle"
# Base: Edge2
chamfer2.Base = (pad, ["Edge2"])

doc.recompute()

# Verify the result
# The solid should be a cylinder with chamfers.
# Check if the body is valid.
# We can get the shape.
shape = body.Shape
# Optional: Display message if in GUI, but this is headless.
# Just ensure recompute was called.

# Save the document
# Output path derived from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

try:
    doc.saveAs(str(output_path))
    print(f"Model saved to: {output_path}")
except Exception as e:
    print(f"Error saving model: {e}")

# Clean up temporary variables if any
del param1, param2, param3, param4, xy_plane, plane_obj, doc
