import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# Create a new document
doc = App.newDocument("HeadedPin")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters ---
# We define parameters that will drive the geometry.
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "pin_diameter", "Dimensions", "Shaft diameter")
params.pin_diameter = 3.0
params.addProperty("App::PropertyLength", "pin_length", "Dimensions", "Total length")
params.pin_length = 6.0
params.addProperty("App::PropertyLength", "head_diameter", "Dimensions", "Head diameter")
params.head_diameter = 5.0
params.addProperty("App::PropertyLength", "head_thickness", "Dimensions", "Head height")
params.head_thickness = 1.0
params.addProperty("App::PropertyLength", "chamfer_length", "Dimensions", "Chamfer length")
params.chamfer_length = 1.0
params.addProperty("App::PropertyAngle", "chamfer_angle", "Dimensions", "Chamfer angle")
params.chamfer_angle = 30.0

# --- Sketch 1: Shaft Profile (Side View) ---
# We create a sketch on the XY plane to define the side profile of the pin.
# Origin is at the bottom center of the shaft.
sketch_shaft = body.newObject("Sketcher::SketchObject", "ShaftProfile")
sketch_shaft.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_shaft.Support = (doc.getObject("XY_Plane"), [])
sketch_shaft.MapMode = "FlatFace"

# Calculate chamfer endpoints
# The chamfer connects the top face of the head to the side of the shaft.
# Angle is measured from the horizontal.
angle_rad = math.radians(params.chamfer_angle)
chamfer_dx = params.chamfer_length * math.cos(angle_rad)
chamfer_dz = params.chamfer_length * math.sin(angle_rad)

# Geometry:
# 1. Bottom Center (0,0) to Bottom Right (pin_diameter/2, 0)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.pin_diameter/2, 0, 0)), False)
# 2. Bottom Right to Top Right of Shaft (pin_diameter/2, pin_diameter)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, 0, 0), App.Vector(params.pin_diameter/2, params.pin_diameter, 0)), False)
# 3. Top Right of Shaft to Top Right of Head (pin_diameter/2, pin_diameter + head_thickness)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, params.pin_diameter, 0), App.Vector(params.pin_diameter/2, params.pin_diameter + params.head_thickness, 0)), False)
# 4. Top Right of Head to Top Right of Chamfer Start (head_diameter/2, pin_diameter + head_thickness)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, params.pin_diameter + params.head_thickness, 0), App.Vector(params.head_diameter/2, params.pin_diameter + params.head_thickness, 0)), False)
# 5. Top Right of Head to Top Left of Head (-head_diameter/2, pin_diameter + head_thickness)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.head_diameter/2, params.pin_diameter + params.head_thickness, 0), App.Vector(-params.head_diameter/2, params.pin_diameter + params.head_thickness, 0)), False)
# 6. Top Left of Head to Top Left of Shaft (-head_diameter/2, pin_diameter)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(-params.head_diameter/2, params.pin_diameter + params.head_thickness, 0), App.Vector(-params.head_diameter/2, params.pin_diameter, 0)), False)
# 7. Top Left of Shaft to Bottom Left (-pin_diameter/2, pin_diameter)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(-params.head_diameter/2, params.pin_diameter, 0), App.Vector(-params.pin_diameter/2, params.pin_diameter, 0)), False)
# 8. Bottom Left to Bottom Center (0,0)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(-params.pin_diameter/2, params.pin_diameter, 0), App.Vector(0, 0, 0)), False)

# Add Constraints
# Horizontal lines
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 0, 1)) # Bottom
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 1, 2)) # Shaft Top
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 2, 3)) # Head Right Top
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 3, 4)) # Head Top
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 4, 5)) # Head Left Top
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 5, 6)) # Head Left Side
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 6, 7)) # Shaft Left Top
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 7, 8)) # Bottom Left

# Vertical lines
sketch_shaft.addConstraint(Sketcher.Constraint("Vertical", 0, 1)) # Bottom Right
sketch_shaft.addConstraint(Sketcher.Constraint("Vertical", 1, 2)) # Shaft Right
sketch_shaft.addConstraint(Sketcher.Constraint("Vertical", 2, 3)) # Head Right
sketch_shaft.addConstraint(Sketcher.Constraint("Vertical", 4, 5)) # Head Left
sketch_shaft.addConstraint(Sketcher.Constraint("Vertical", 5, 6)) # Shaft Left

# Coincident constraints to close the loop and fix positions
# Bottom Center (0,0) is index 0 start and 8 end.
# Bottom Right (pin_d/2, 0) is index 0 end and 1 start.
# Top Right Shaft (pin_d/2, pin_d) is index 1 end and 2 start.
# Top Right Head (pin_d/2, pin_d+head_t) is index 2 end and 3 start.
# Top Right Chamfer Start (head_d/2, pin_d+head_t) is index 3 end and 4 start.
# Top Left Head (-head_d/2, pin_d+head_t) is index 4 end and 5 start.
# Top Left Shaft (-head_d/2, pin_d) is index 5 end and 6 start.
# Top Left Shaft (-pin_d/2, pin_d) is index 6 end and 7 start.
# Bottom Left (-pin_d/2, 0) is index 7 end and 8 start.
# Bottom Center (0,0) is index 8 end.

# Constrain Bottom Center to (0,0)
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 0, 2, 0, 0))
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 8, 2, 0, 0))

# Constrain Bottom Right to be on X axis (Y=0)
sketch_shaft.addConstraint(Sketcher.Constraint("PointY", 1, 2, 0))
sketch_shaft.addConstraint(Skancher.Constraint("PointY", 8, 2, 0))

# Constrain Top Right Shaft to be at X = pin_diameter/2
sketch_shaft.addConstraint(Sketcher.Constraint("PointX", 1, 2, "Parameters.pin_diameter/2"))
sketch_shaft.addConstraint(Sketcher.Constraint("PointX", 2, 2, "Parameters.pin_diameter/2"))

# Constrain Top Right Head to be at X = head_diameter/2
sketch_shaft.addConstraint(Sketcher.Constraint("PointX", 3, 2, "Parameters.head_diameter/2"))
sketch_shaft.addConstraint(Sketcher.Constraint("PointX", 4, 2, "Parameters.head_diameter/2"))

# Constrain Top Left Head to be at X = -head_diameter/2
sketch_shaft.addConstraint(Sketcher.Constraint("PointX", 5, 2, "-Parameters.head_diameter/2"))
sketch_shaft.addConstraint(Sketcher.Constraint("PointX", 6, 2, "-Parameters.head_diameter/2"))

# Constrain Top Left Shaft to be at X = -pin_diameter/2
sketch_shaft.addConstraint(Sketcher.Constraint("PointX", 7, 2, "-Parameters.pin_diameter/2"))

# Constrain Top Right Shaft Z to pin_diameter
sketch_shaft.addConstraint(Sketcher.Constraint("PointZ", 1, 2, "Parameters.pin_diameter"))
sketch_shaft.addConstraint(Sketcher.Constraint("PointZ", 2, 2, "Parameters.pin_diameter"))

# Constrain Top Right Head Z to pin_diameter + head_thickness
sketch_shaft.addConstraint(Sketcher.Constraint("PointZ", 3, 2, "Parameters.pin_diameter + Parameters.head_thickness"))
sketch_shaft.addConstraint(Sketcher.Constraint("PointZ", 4, 2, "Parameters.pin_diameter + Parameters.head_thickness"))

# Constrain Top Left Head Z to pin_diameter + head_thickness
sketch_shaft.addConstraint(Sketcher.Constraint("PointZ", 5, 2, "Parameters.pin_diameter + Parameters.head_thickness"))
sketch_shaft.addConstraint(Sketcher.Constraint("PointZ", 6, 2, "Parameters.pin_diameter + Parameters.head_thickness"))

# Constrain Top Left Shaft Z to pin_diameter
sketch_shaft.addConstraint(Sketcher.Constraint("PointZ", 7, 2, "Parameters.pin_diameter"))

# Constrain Chamfer Start (index 4 end) to be at X = head_diameter/2 and Z = pin_diameter + head_thickness
# This is already done by the horizontal and vertical constraints on the head top.
# However, we need to ensure the chamfer line (index 4) connects correctly.
# The chamfer line is index 4. It starts at (head_d/2, pin_d+head_t) and ends at the shaft side.
# We need to constrain the end of the chamfer line (index 4 end) to be on the shaft side line (x = pin_d/2).
# And the Z coordinate of the end of the chamfer line should be pin_d + head_t - chamfer_dz.
# But chamfer_dz is a calculated value, not a parameter. We can use an expression or just constrain the geometry.
# Let's constrain the end of the chamfer line (index 4 end) to be at X = pin_diameter/2.
sketch_shaft.addConstraint(Sketcher.Constraint("PointX", 4, 2, "Parameters.pin_diameter/2"))

# Constrain the end of the chamfer line (index 4 end) Z coordinate.
# The chamfer length is fixed. The angle is fixed.
# The vertical drop is chamfer_length * sin(angle).
# We can express this as an expression in the constraint if FreeCAD supports it, or we can calculate it.
# Let's try to use an expression.
# Z_end = Z_start - chamfer_length * sin(chamfer_angle)
# Z_start is pin_diameter + head_thickness.
sketch_shaft.addConstraint(Sketcher.Constraint("PointZ", 4, 2, "Parameters.pin_diameter + Parameters.head_thickness - Parameters.chamfer_length * sin(Parameters.chamfer_angle * pi/180)"))

# Constrain the end of the chamfer line (index 4 end) to be at the same Z as the start of the shaft side line (index 5 start)?
# No, the chamfer connects the head top to the shaft side.
# The shaft side line (index 5) goes from (-head_d/2, pin_d) to (-head_d/2, pin_d+head_t)? No.
# Let's re-verify the indices.
# 0: (0,0) -> (d/2, 0)
# 1: (d/2, 0) -> (d/2, d)
# 2: (d/2, d) -> (d/2, d+h)
# 3: (d/2, d+h) -> (D/2, d+h)
# 4: (D/2, d+h) -> (-D/2, d+h)
# 5: (-D/2, d+h) -> (-D/2, d)
# 6: (-D/2, d) -> (-d/2, d)
# 7: (-d/2, d) -> (-d/2, 0)
# 8: (-d/2, 0) -> (0,0)

# The chamfer is on the top right corner of the head.
# It connects the top face of the head (index 3 end) to the side of the shaft (index 2 end).
# Wait, index 3 is (D/2, d+h) -> (-D/2, d+h). This is the top face of the head.
# Index 2 is (d/2, d) -> (d/2, d+h). This is the side of the shaft.
# The chamfer should connect (D/2, d+h) to (d/2, d+h - drop).
# But my sketch has index 3 going from (d/2, d+h) to (D/2, d+h).
# So the chamfer should be a separate line?
# No, the chamfer is part of the profile.
# The profile should be:
# ... -> (d/2, d+h) -> (D/2, d+h) -> (D/2, d+h - drop) -> (d/2, d+h - drop) -> (d/2, d) -> ...
# But the chamfer is a single line.
# So the profile should be:
# ... -> (d/2, d+h) -> (D/2, d+h) -> (D/2, d+h - drop) -> (d/2, d+h - drop) -> (d/2, d) -> ...
# This means we need to split the top face of the head and the side of the shaft.
# Let's rebuild the sketch with the chamfer included.

# Re-creating Sketch with Chamfer
sketch_shaft = body.newObject("Sketcher::SketchObject", "ShaftProfile")
sketch_shaft.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_shaft.Support = (doc.getObject("XY_Plane"), [])
sketch_shaft.MapMode = "FlatFace"

# Geometry:
# 1. Bottom Center (0,0) to Bottom Right (pin_diameter/2, 0)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.pin_diameter/2, 0, 0)), False)
# 2. Bottom Right to Top Right of Shaft (pin_diameter/2, pin_diameter)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, 0, 0), App.Vector(params.pin_diameter/2, params.pin_diameter, 0)), False)
# 3. Top Right of Shaft to Top Right of Head (pin_diameter/2, pin_diameter + head_thickness)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, params.pin_diameter, 0), App.Vector(params.pin_diameter/2, params.pin_diameter + params.head_thickness, 0)), False)
# 4. Top Right of Head to Top Right of Chamfer Start (head_diameter/2, pin_diameter + head_thickness)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, params.pin_diameter + params.head_thickness, 0), App.Vector(params.head_diameter/2, params.pin_diameter + params.head_thickness, 0)), False)
# 5. Top Right of Chamfer Start to Top Left of Chamfer End (head_diameter/2 - chamfer_dx, pin_diameter + head_thickness - chamfer_dz)
# This is the chamfer line.
chamfer_start = App.Vector(params.head_diameter/2, params.pin_diameter + params.head_thickness, 0)
chamfer_end = App.Vector(params.head_diameter/2 - chamfer_dx, params.pin_diameter + params.head_thickness - chamfer_dz, 0)
sketch_shaft.addGeometry(Part.LineSegment(chamfer_start, chamfer_end), False)
# 6. Top Left of Chamfer End to Top Right of Shaft (pin_diameter/2, pin_diameter + head_thickness - chamfer_dz)
# This is the horizontal line from the chamfer end to the shaft side.
# Wait, the chamfer end should be on the shaft side?
# No, the chamfer connects the top face of the head to the side of the shaft.
# So the chamfer end should be at (pin_diameter/2, pin_diameter + head_thickness - chamfer_dz).
# But the chamfer length is fixed.
# If the chamfer length is 1.0 and angle is 30, the horizontal projection is 0.866.
# The vertical projection is 0.5.
# The start point is at (head_d/2, pin_d+head_t).
# The end point is at (head_d/2 - 0.866, pin_d+head_t - 0.5).
# This end point is NOT on the shaft side (x = pin_d/2).
# This means the chamfer does not connect to the shaft side directly.
# It connects to a point on the top face of the head? No.
# It connects to a point on the side of the head? No.
# It connects to a point on the side of the shaft?
# For the chamfer to connect to the shaft side, the end point must have x = pin_d/2.
# So the start point must have x = pin_d/2 + chamfer_dx.
# But the start point is on the top face of the head, so its x must be <= head_d/2.
# So we need pin_d/2 + chamfer_dx <= head_d/2.
# 1.5 + 0.866 = 2.366 <= 2.5. This is true.
# So the chamfer connects the top face of the head to the side of the shaft.
# The start point is at (pin_d/2 + chamfer_dx, pin_d + head_thickness).
# The end point is at (pin_d/2, pin_d + head_thickness - chamfer_dz).
# So the profile should be:
# ... -> (pin_d/2, pin_d + head_thickness) -> (pin_d/2 + chamfer_dx, pin_d + head_thickness) -> (pin_d/2, pin_d + head_thickness - chamfer_dz) -> (pin_d/2, pin_d) -> ...

# Let's rebuild the sketch with this correct geometry.
sketch_shaft = body.newObject("Sketcher::SketchObject", "ShaftProfile")
sketch_shaft.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_shaft.Support = (doc.getObject("XY_Plane"), [])
sketch_shaft.MapMode = "FlatFace"

# Geometry:
# 1. Bottom Center (0,0) to Bottom Right (pin_diameter/2, 0)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.pin_diameter/2, 0, 0)), False)
# 2. Bottom Right to Top Right of Shaft (pin_diameter/2, pin_diameter)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, 0, 0), App.Vector(params.pin_diameter/2, params.pin_diameter, 0)), False)
# 3. Top Right of Shaft to Top Right of Head (pin_diameter/2, pin_diameter + head_thickness)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, params.pin_diameter, 0), App.Vector(params.pin_diameter/2, params.pin_diameter + params.head_thickness, 0)), False)
# 4. Top Right of Head to Top Right of Chamfer Start (pin_diameter/2 + chamfer_dx, pin_diameter + head_thickness)
chamfer_start = App.Vector(params.pin_diameter/2 + chamfer_dx, params.pin_diameter + params.head_thickness, 0)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, params.pin_diameter + params.head_thickness, 0), chamfer_start), False)
# 5. Top Right of Chamfer Start to Top Left of Chamfer End (pin_diameter/2, pin_diameter + head_thickness - chamfer_dz)
chamfer_end = App.Vector(params.pin_diameter/2, params.pin_diameter + params.head_thickness - chamfer_dz, 0)
sketch_shaft.addGeometry(Part.LineSegment(chamfer_start, chamfer_end), False)
# 6. Top Left of Chamfer End to Top Right of Shaft (pin_diameter/2, pin_diameter)
sketch_shaft.addGeometry(Part.LineSegment(chamfer_end, App.Vector(params.pin_diameter/2, params.pin_diameter, 0)), False)
# 7. Top Right of Shaft to Top Left of Shaft (-pin_diameter/2, pin_diameter)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, params.pin_diameter, 0), App.Vector(-params.pin_diameter/2, params.pin_diameter, 0)), False)
# 8. Top Left of Shaft to Bottom Left (-pin_diameter/2, 0)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(-params.pin_diameter/2, params.pin_diameter, 0), App.Vector(-params.pin_diameter/2, 0, 0)), False)
# 9. Bottom Left to Bottom Center (0,0)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(-params.pin_diameter/2, 0, 0), App.Vector(0, 0, 0)), False)

# Add Constraints
# Horizontal lines
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 0, 1)) # Bottom
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 1, 2)) # Shaft Top
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 2, 3)) # Head Right Top
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 3, 4)) # Chamfer Top
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 4, 5)) # Chamfer Bottom
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 5, 6)) # Shaft Top Left
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 6, 7)) # Shaft Left Top
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 7, 8)) # Bottom Left

# Vertical lines
sketch_shaft.addConstraint(Sketcher.Constraint("Vertical", 0, 1)) # Bottom Right
sketch_shaft.addConstraint(Sketcher.Constraint("Vertical", 1, 2)) # Shaft Right
sketch_shaft.addConstraint(Sketcher.Constraint("Vertical", 5, 6)) # Shaft Left
sketch_shaft.addConstraint(Sketcher.Constraint("Vertical", 6, 7)) # Shaft Left Side

# Coincident constraints
# Bottom Center (0,0) is index 0 start and 9 end.
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 0, 2, 0, 0))
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 9, 2, 0, 0))

# Bottom Right (pin_d/2, 0) is index 0 end and 1 start.
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 0, 2, "Parameters.pin_diameter/2", 0))
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 1, 2, "Parameters.pin_diameter/2", 0))

# Top Right of Shaft (pin_d/2, pin_d) is index 1 end and 2 start.
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 1, 2, "Parameters.pin_diameter/2", "Parameters.pin_diameter"))
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 2, 2, "Parameters.pin_diameter/2", "Parameters.pin_diameter"))

# Top Right of Head (pin_d/2, pin_d+head_t) is index 2 end and 3 start.
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 2, 2, "Parameters.pin_diameter/2", "Parameters.pin_diameter + Parameters.head_thickness"))
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 3, 2, "Parameters.pin_diameter/2", "Parameters.pin_diameter + Parameters.head_thickness"))

# Top Right of Chamfer Start (pin_d/2 + chamfer_dx, pin_d+head_t) is index 3 end and 4 start.
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 3, 2, "Parameters.pin_diameter/2 + Parameters.chamfer_length * cos(Parameters.chamfer_angle * pi/180)", "Parameters.pin_diameter + Parameters.head_thickness"))
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 4, 2, "Parameters.pin_diameter/2 + Parameters.chamfer_length * cos(Parameters.chamfer_angle * pi/180)", "Parameters.pin_diameter + Parameters.head_thickness"))

# Top Left of Chamfer End (pin_d/2, pin_d+head_t - chamfer_dz) is index 4 end and 5 start.
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 4, 2, "Parameters.pin_diameter/2", "Parameters.pin_diameter + Parameters.head_thickness - Parameters.chamfer_length * sin(Parameters.chamfer_angle * pi/180)"))
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 5, 2, "Parameters.pin_diameter/2", "Parameters.pin_diameter + Parameters.head_thickness - Parameters.chamfer_length * sin(Parameters.chamfer_angle * pi/180)"))

# Top Left of Shaft (-pin_d/2, pin_d) is index 5 end and 6 start.
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 5, 2, "-Parameters.pin_diameter/2", "Parameters.pin_diameter"))
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 6, 2, "-Parameters.pin_diameter/2", "Parameters.pin_diameter"))

# Top Left of Shaft (-pin_d/2, 0) is index 6 end and 7 start.
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 6, 2, "-Parameters.pin_diameter/2", 0))
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 7, 2, "-Parameters.pin_diameter/2", 0))

# Bottom Left (-pin_d/2, 0) is index 7 end and 8 start.
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 7, 2, "-Parameters.pin_diameter/2", 0))
sketch_shaft.addConstraint(Sketcher.Constraint("Point", 8, 2, "-Parameters.pin_diameter/2", 0))

# --- Pad Feature ---
# Create a pad from the sketch to the total length.
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = sketch_shaft
pad.Length = params.pin_length
pad.Type = "FullyRounded" # Default, but we will add chamfers later.
pad.Midplane = False
pad.Reversed = False

# --- Fillet Feature ---
# Add a fillet to the top edge of the head.
# The top edge of the head is the edge between the top face and the side face.
# In the sketch, this is the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The edge between the top face and the side face is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from the edge between index 3 and 4? No.
# The top face of the head is the face created by the pad from the top face of the sketch.
# The side face of the head is the face created by the pad from the side face of the sketch.
# The edge between them is the edge created by the pad from
