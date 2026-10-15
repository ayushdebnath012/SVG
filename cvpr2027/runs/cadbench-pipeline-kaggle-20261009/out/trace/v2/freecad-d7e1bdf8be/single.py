import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("HeadedPin")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters ---
# We define parameters that will drive the geometry.
# Note: In FreeCAD 1.1, we can use App::PropertyLength/PropertyAngle directly on the Body 
# or create a VarSet. For simplicity and robustness in scripts, we often set properties 
# directly on the Body if they are simple, or use a VarSet for complex dependencies.
# Here we will use a VarSet to keep the tree clean and editable.

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
sketch_shaft = body.newObject("Sketcher::SketchObject", "ShaftProfile")
sketch_shaft.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_shaft.Support = (doc.getObject("XY_Plane"), [])
sketch_shaft.MapMode = "FlatFace"

# Add geometry for the shaft profile
# Line 1: Bottom of shaft to center
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(-params.pin_diameter/2, 0, 0), App.Vector(0, 0, 0)), False)
# Line 2: Center to top of shaft
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0, params.pin_diameter/2, 0)), False)
# Line 3: Top of shaft to top of head (vertical line up)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(0, params.pin_diameter/2, 0), App.Vector(0, params.head_diameter/2, 0)), False)
# Line 4: Top of head to top of chamfer start (horizontal)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(0, params.head_diameter/2, 0), App.Vector(-params.chamfer_length, params.head_diameter/2, 0)), False)
# Line 5: Chamfer slope (calculated based on angle)
# The chamfer is defined by length and angle. 
# We need the endpoint of the chamfer.
# Vertical drop = chamfer_length * sin(angle)
# Horizontal run = chamfer_length * cos(angle)
# But the sketch is 2D (XZ plane effectively if we rotate, or just X,Y here).
# Let's assume the sketch is in the XZ plane (Side view).
# X is horizontal, Z is vertical.
# Start of chamfer: (-chamfer_length, head_thickness/2) -> Wait, let's re-orient.
# Let's make the sketch in the XZ plane where X is horizontal and Z is vertical.
# Center is (0,0).
# Shaft top: (0, pin_diameter/2)
# Head top: (0, head_diameter/2)
# Head bottom: (0, head_thickness/2)
# Shaft bottom: (0, -pin_diameter/2)

# Let's rebuild the sketch geometry carefully for a Side View (XZ plane).
# Origin at center of shaft bottom? No, let's keep origin at center of shaft bottom for simplicity of constraints, 
# or center of the whole part. Let's use center of the shaft bottom as origin (0,0).
# Then Shaft goes from 0 to pin_diameter. Head goes from pin_diameter to pin_diameter + head_thickness.
# This makes constraints easier.

# Re-creating Sketch with Origin at Bottom Center of Shaft
sketch_shaft.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_shaft.Support = (doc.getObject("XY_Plane"), [])
sketch_shaft.MapMode = "FlatFace"

# Geometry:
# 1. Bottom Center (0,0) to Bottom Right (pin_diameter/2, 0)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.pin_diameter/2, 0, 0)), False)
# 2. Bottom Right to Top Right of Shaft (pin_diameter/2, pin_diameter)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, 0, 0), App.Vector(params.pin_diameter/2, params.pin_diameter, 0)), False)
# 3. Top Right of Shaft to Top Right of Head (pin_diameter/2, pin_diameter) -> (pin_diameter/2, pin_diameter + head_thickness)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, params.pin_diameter, 0), App.Vector(params.pin_diameter/2, params.pin_diameter + params.head_thickness, 0)), False)
# 4. Top Right of Head to Top Right of Chamfer Start (pin_diameter/2, pin_diameter + head_thickness) -> (pin_diameter/2 - chamfer_length, pin_diameter + head_thickness)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, params.pin_diameter + params.head_thickness, 0), App.Vector(params.pin_diameter/2 - params.chamfer_length, params.pin_diameter + params.head_thickness, 0)), False)
# 5. Chamfer Line
# Angle is measured from the horizontal? Usually chamfer angle is from the horizontal surface.
# If angle is 30 deg, the slope is tan(30).
# dx = chamfer_length * cos(30)
# dy = chamfer_length * sin(30)
# We are going left and down.
# End point X = Start X - chamfer_length * cos(angle)
# End point Z = Start Z - chamfer_length * sin(angle)
# Wait, the previous segment was horizontal. The chamfer connects the horizontal top of the head to the vertical side of the shaft?
# No, usually a headed pin has a chamfer on the top edge of the head.
# So we go from (Head_Top_Right) to (Head_Top_Left) then down? 
# Or from (Head_Top_Right) to (Shaft_Top_Right)?
# Standard chamfer: Connects the corner of the head to the side of the shaft.
# Let's assume the chamfer connects the top face of the head to the side of the shaft.
# Start: (pin_diameter/2, pin_diameter + head_thickness)
# End: (pin_diameter/2 - chamfer_length * cos(angle), pin_diameter + head_thickness - chamfer_length * sin(angle))
# But this end point must align with the shaft side? 
# Actually, the chamfer length is the length of the cut.
# Let's calculate the endpoint.
import math
angle_rad = math.radians(params.chamfer_angle)
chamfer_dx = params.chamfer_length * math.cos(angle_rad)
chamfer_dz = params.chamfer_length * math.sin(angle_rad)

chamfer_start = App.Vector(params.pin_diameter/2, params.pin_diameter + params.head_thickness, 0)
chamfer_end = App.Vector(params.pin_diameter/2 - chamfer_dx, params.pin_diameter + params.head_thickness - chamfer_dz, 0)

sketch_shaft.addGeometry(Part.LineSegment(chamfer_start, chamfer_end), False)
# 6. Shaft Side down to bottom
# We need to connect the chamfer end to the shaft side.
# Ideally, the chamfer end should touch the shaft side line.
# Let's add the vertical line from the chamfer end down to the shaft level? 
# No, the chamfer usually cuts the corner.
# Let's assume the geometry is: Shaft side vertical, Head top horizontal, Chamfer diagonal.
# So we need a line from Chamfer End to (pin_diameter/2, pin_diameter).
# But wait, the chamfer length is fixed. If the angle is 30, the vertical drop is small.
# The point (pin_diameter/2, pin_diameter) is the corner of the shaft.
# The chamfer connects the top of the head to the side of the shaft.
# So the line goes from (Head_Top_Right) to (Shaft_Top_Right)? No, that's a corner cut.
# Let's assume the chamfer connects the top face of the head to the side face of the shaft.
# So the endpoint of the chamfer must lie on the line x = pin_diameter/2.
# If the chamfer length is 1.0 and angle is 30, the horizontal projection is 0.866.
# So the endpoint X is pin_diameter/2 - 0.866.
# The endpoint Z is pin_diameter + head_thickness - 0.5.
# This point is NOT on the shaft side (x = pin_diameter/2).
# This implies the chamfer is on the top face of the head, cutting into the head, not connecting to the shaft side directly?
# Or maybe the "chamfer length" is the length along the hypotenuse.
# Let's assume the standard interpretation: A chamfer on the top edge of the head.
# It connects the top face of the head to the side face of the head? No, that's a fillet or a different chamfer.
# It connects the top face of the head to the side face of the SHAFT.
# For this to work, the chamfer must start at the top edge of the head and end at the side of the shaft.
# If the angle is 30 degrees (from horizontal), then:
# Vertical drop = L * sin(30)
# Horizontal run = L * cos(30)
# The endpoint must be at x = pin_diameter/2.
# So the start point must be at x = pin_diameter/2 + L*cos(30).
# But the head diameter is larger than the shaft.
# So the start point is on the top face of the head.
# The end point is on the side of the shaft.
# This works perfectly.
# So:
# Start Point (on head top): (pin_diameter/2 + chamfer_length * cos(angle), pin_diameter + head_thickness)
# End Point (on shaft side): (pin_diameter/2, pin_diameter + head_thickness - chamfer_length * sin(angle))

# Let's update the sketch geometry with this logic.
# 1. Bottom Center to Bottom Right
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.pin_diameter/2, 0, 0)), False)
# 2. Bottom Right to Top Right of Shaft
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, 0, 0), App.Vector(params.pin_diameter/2, params.pin_diameter, 0)), False)
# 3. Top Right of Shaft to Top Right of Head (Vertical extension)
# Wait, the head is centered on the shaft.
# So the shaft goes from 0 to pin_diameter.
# The head goes from pin_diameter to pin_diameter + head_thickness.
# The head diameter is head_diameter.
# So the head extends from -head_diameter/2 to +head_diameter/2 relative to center?
# No, let's stick to the coordinate system:
# Origin: Bottom Center of Shaft.
# Shaft: x in [0, pin_diameter], z in [0, pin_diameter].
# Head: x in [-head_diameter/2, head_diameter/2], z in [pin_diameter, pin_diameter + head_thickness].
# This means the head is centered horizontally at x = pin_diameter/2? No, that would be offset.
# The head is centered on the shaft axis.
# So if Shaft is x=[0, pin_diameter], Center is x=pin_diameter/2.
# Head is x=[pin_diameter/2 - head_diameter/2, pin_diameter/2 + head_diameter/2].
# This is getting complicated with offsets.
# Let's simplify: Center the whole part at (0,0).
# Shaft: x in [-pin_diameter/2, pin_diameter/2], z in [0, pin_diameter].
# Head: x in [-head_diameter/2, head_diameter/2], z in [pin_diameter, pin_diameter + head_thickness].
# This is symmetric and easier.

# Reset Sketch
sketch_shaft = body.newObject("Sketcher::SketchObject", "ShaftProfile")
sketch_shaft.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_shaft.Support = (doc.getObject("XY_Plane"), [])
sketch_shaft.MapMode = "FlatFace"

# Geometry (Centered at 0,0)
# 1. Bottom Left to Bottom Right
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(-params.pin_diameter/2, 0, 0), App.Vector(params.pin_diameter/2, 0, 0)), False)
# 2. Bottom Right to Top Right of Shaft
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, 0, 0), App.Vector(params.pin_diameter/2, params.pin_diameter, 0)), False)
# 3. Top Right of Shaft to Top Right of Head (Horizontal)
# Head top is at z = pin_diameter + head_thickness.
# Head right edge is at x = head_diameter/2.
# So we go from (pin_diameter/2, pin_diameter) to (head_diameter/2, pin_diameter + head_thickness)?
# No, the head sits on the shaft.
# So the vertical line goes from (pin_diameter/2, pin_diameter) to (pin_diameter/2, pin_diameter + head_thickness).
# Then horizontal to (head_diameter/2, pin_diameter + head_thickness).
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, params.pin_diameter, 0), App.Vector(params.pin_diameter/2, params.pin_diameter + params.head_thickness, 0)), False)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.pin_diameter/2, params.pin_diameter + params.head_thickness, 0), App.Vector(params.head_diameter/2, params.pin_diameter + params.head_thickness, 0)), False)
# 4. Top Right of Head to Top Left of Head
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(params.head_diameter/2, params.pin_diameter + params.head_thickness, 0), App.Vector(-params.head_diameter/2, params.pin_diameter + params.head_thickness, 0)), False)
# 5. Top Left of Head to Top Left of Shaft
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(-params.head_diameter/2, params.pin_diameter + params.head_thickness, 0), App.Vector(-params.head_diameter/2, params.pin_diameter, 0)), False)
# 6. Top Left of Shaft to Bottom Left
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(-params.head_diameter/2, params.pin_diameter, 0), App.Vector(-params.pin_diameter/2, params.pin_diameter, 0)), False)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(-params.pin_diameter/2, params.pin_diameter, 0), App.Vector(-params.pin_diameter/2, 0, 0)), False)

# Add Constraints
# Horizontal lines
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 0, 1)) # Bottom
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 1, 2)) # Shaft Top
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 2, 3)) # Head Top Right
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 3, 4)) # Head Top Left
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 4, 5)) # Head Left Vertical? No, 4-5 is vertical.
# Let's just constrain verticals and horizontals by index.
# 0-1: Bottom (Horiz)
# 1-2: Shaft Right (Vert)
# 2-3: Head Right Top (Horiz)
# 3-4: Head Top (Horiz)
# 4-5: Head Left Top (Vert)
# 5-6: Head Left Side (Horiz)
# 6-7: Shaft Left Top (Vert)
# 7-8: Shaft Left Side (Vert)
# 8-0: Bottom Left (Horiz)

# Let's use a simpler approach: Constrain all verticals to be vertical and horizontals to be horizontal.
# And constrain the center point to be at (0,0).
# We need to identify the segments.
# Segments:
# 0: (-d/2, 0) -> (d/2, 0) [Horiz]
# 1: (d/2, 0) -> (d/
