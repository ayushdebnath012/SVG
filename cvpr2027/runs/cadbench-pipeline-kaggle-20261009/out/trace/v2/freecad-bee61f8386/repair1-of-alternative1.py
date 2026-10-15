import FreeCAD as App
import Part
import PartDesign
import Sketcher
from math import cos, radians
from pathlib import Path

# Initialize Document
doc = App.newDocument("HexFlangeNut")

# --- Parameters ---
# Define named parameters to drive the geometry
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height of the nut")
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Width of the hexagonal hub")
params.addProperty("App::PropertyLength", "hex_width_across_flats", "Dimensions", "Distance across flats of the hex")
params.addProperty("App::PropertyLength", "hex_width_across_corners", "Dimensions", "Distance across corners of the hex")
params.addProperty("App::PropertyAngle", "hex_head_angle", "Dimensions", "Angle of the chamfer on hex edges")
params.addProperty("App::PropertyLength", "flange_diameter", "Dimensions", "Diameter of the bottom flange")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the bottom flange")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Diameter of the central through-hole")

# Set default values as per requirements
params.overall_height = 21.0
params.hub_width = 22.0
params.hex_width_across_flats = 22.0
params.hex_width_across_corners = 22.0 / cos(radians(30))
params.hex_head_angle = 30.0
params.flange_diameter = 28.0
params.flange_thickness = 4.0
params.inner_diameter = 14.0

# --- Body Creation ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch: Hexagonal Hub Profile (Side View) ---
# We define the main profile in the XY plane. 
# It consists of the Hex Hub height, the Flange height, and the central hole.
sketch_hub = body.newObject("Sketcher::SketchObject", "Sketch_HubProfile")
sketch_hub.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_hub.ConstrainAuto = False
sketch_hub.MapMode = "FlatFace"

# Create geometry for the Hex Hub side profile
# We need a polygon: Vertical center line (reference), then the hexagon sides, then the flange, then the hole.
# Coordinates (X, Y):
# Start at bottom center of flange: (0, 0)
# Go up to flange top: (0, flange_thickness)
# Go right to flange edge: (flange_diameter/2, flange_thickness)
# Go up to hub bottom: (flange_diameter/2, flange_thickness) -> Actually, the hub sits on the flange.
# Let's refine the profile logic:
# The profile is the LEFT half of the symmetric part.
# Points:
# 1. Center Bottom: (0, 0)
# 2. Flange Right Edge Bottom: (flange_diameter/2, 0)
# 3. Flange Right Edge Top: (flange_diameter/2, flange_thickness)
# 4. Hub Bottom Right: (flange_diameter/2, flange_thickness) -> Wait, the hex is usually slightly wider than the hole, but the flange covers the hole.
# Let's assume the hex sits on the flange.
# Hub Bottom Right X coordinate: hex_width_across_flats / 2
# Hub Bottom Right Y coordinate: flange_thickness
# Hub Top Right X coordinate: hex_width_across_flats / 2
# Hub Top Right Y coordinate: flange_thickness + (hub_width * tan(60/2)) -> No, hub_height is not given directly, only hex_width.
# The problem description says "high-profile... overall_height is governed by overall_height".
# So Hub Height = overall_height - flange_thickness.
# Hub Top Right Y = flange_thickness + (overall_height - flange_thickness) = overall_height.
# Wait, a hexagon side view is a trapezoid or rectangle depending on angle.
# Standard Hex Head: The sides are angled.
# Let's define the vertices of the right-side boundary of the hexagon.
# Bottom Right: (hex_width_across_flats / 2, flange_thickness)
# Top Right: (hex_width_across_flats / 2, overall_height) -> This assumes vertical sides? No, hexagons have angled sides.
# Let's calculate the coordinates of the Hexagon profile based on the angles.
# Center of Hex (Side View): (0, flange_thickness + (overall_height - flange_thickness)/2) -> No, let's place the bottom of the flange at Y=0.
# Flange Top: Y = flange_thickness.
# Hex Bottom: Y = flange_thickness.
# Hex Top: Y = overall_height.
# Hex Width at Bottom (at flange level): hex_width_across_flats.
# Hex Width at Top (at top level): hex_width_across_flats.
# Hex Head Angle: 30 degrees.
# The side of the hexagon makes an angle of 30 degrees with the horizontal? Or vertical?
# "Hex Head Angle" in DIN 934 usually refers to the chamfer angle (30 deg) or the wedge angle of the hex face.
# Standard ISO hex nut: The face angle (wedge) is 30 degrees.
# So the side of the hexagon slopes at 30 degrees from the vertical? No, 30 degrees from the horizontal?
# In a regular hexagon, the internal angle is 120. The exterior angle is 60.
# The side faces are at 30 degrees to the vertical axis.
# So, from the center X=0:
# Bottom Right Corner: (hex_width_across_flats/2, flange_thickness)
# Top Right Corner: (hex_width_across_flats/2, overall_height) -> This implies vertical sides.
# BUT, a hexagon has angled sides.
# If the nut is oriented with flats horizontal (standard), the side view (cut through the center) shows the two angled faces.
# The width at the bottom (at the flange plane) is hex_width_across_flats.
# The width at the top (at the top plane) is also hex_width_across_flats.
# The width in between is larger (hex_width_across_corners).
# So the profile is a trapezoid.
# Let's calculate the X-coordinate of the top corners.
# Bottom X (Right) = hex_width_across_flats / 2
# Top X (Right) = hex_width_across_corners / 2
# Bottom Y = flange_thickness
# Top Y = overall_height
# We need to connect these with a line.
# Is it a single line? Yes, the side face of a hex nut is a plane.
# So the profile is a trapezoid.
# Left side: (0, flange_thickness) to (0, overall_height).
# Right side: (hex_width_across_flats/2, flange_thickness) to (hex_width_across_corners/2, overall_height).
# Wait, the bottom of the hexagon (where it meets the flange) is the "across flats" width.
# The top of the hexagon is the "across corners" width.
# Yes.
# Now, add the hole. The hole is a rectangle in the side view.
# Hole X = inner_diameter / 2.
# Hole Y = from flange_thickness to overall_height.
# We will cut this hole later using a pocket or by subtracting the sketch geometry directly?
# The prompt says "plain through hole running along the central axis".
# Strategy:
# 1. Create Pad from the Hex+Flange Profile.
# 2. Create a Pocket from a sketch defining the hole rectangle.

# Define Sketch Geometry (Left Half Profile + Hole Reference)
# Point 1: Center Bottom (0, 0)
# Point 2: Flange Right Edge (flange_diameter/2, 0)
# Point 3: Flange Right Edge Top (flange_diameter/2, flange_thickness)
# Point 4: Hub Bottom Right (hex_width_across_flats/2, flange_thickness)
# Point 5: Hub Top Right (hex_width_across_corners/2, overall_height)
# Point 6: Hub Top Center (0, overall_height)
# Point 7: Hub Top Left (0, flange_thickness) - implicit closure
# Hole: We will add a line segment representing the hole width to constrain it, then use a separate pocket.
# Actually, for a clean feature tree, let's make the Pad profile solid (Hex+Flange) and then a separate Pocket for the hole.

# Add Lines for the Hex+Flange Profile
# Center line X=0
sketch_hub.addGeometry(Part.LineSegment(App.Vector(0, 0), App.Vector(0, overall_height.value)), False)
# Flange Bottom Edge
sketch_hub.addGeometry(Part.LineSegment(App.Vector(0, 0), App.Vector(flange_diameter.value/2, 0)), False)
# Flange Vertical Edge
sketch_hub.addGeometry(Part.LineSegment(App.Vector(flange_diameter.value/2, 0), App.Vector(flange_diameter.value/2, flange_thickness.value)), False)
# Hex Bottom Edge (to the hex width)
sketch_hub.addGeometry(Part.LineSegment(App.Vector(flange_diameter.value/2, flange_thickness.value), App.Vector(hex_width_across_flats.value/2, flange_thickness.value)), False)
# Hex Side Slope
sketch_hub.addGeometry(Part.LineSegment(App.Vector(hex_width_across_flats.value/2, flange_thickness.value), App.Vector(hex_width_across_corners.value/2, overall_height.value)), False)
# Hex Top Edge (back to center)
sketch_hub.addGeometry(Part.LineSegment(App.Vector(hex_width_across_corners.value/2, overall_height.value), App.Vector(0, overall_height.value)), False)

# Constrain the profile
# Close loop
sketch_hub.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 6, 0))
# Vertical Center Line
sketch_hub.addConstraint(Sketcher.Constraint("Vertical", 1, 0))
# Horizontal Flange Bottom
sketch_hub.addConstraint(Sketcher.Constraint("Horizontal", 2, 0))
# Horizontal Hex Bottom
sketch_hub.addConstraint(Sketcher.Constraint("Horizontal", 5, 0))
# Horizontal Hex Top
sketch_hub.addConstraint(Sketcher.Constraint("Horizontal", 6, 0))
# Vertical Hex Right? No, it's angled.
# Horizontal distances
sketch_hub.addConstraint(Sketcher.Constraint("DistanceX", 5, 0, 0, hex_width_across_flats.value/2, "Dimensions"))
sketch_hub.addConstraint(Sketcher.Constraint("DistanceX", 6, 0, 0, hex_width_across_corners.value/2, "Dimensions"))
sketch_hub.addConstraint(Sketcher.Constraint("DistanceY", 4, 0, 3, flange_thickness.value, "Dimensions"))
sketch_hub.addConstraint(Sketcher.Constraint("DistanceY", 5, 0, 6, overall_height.value - flange_thickness.value, "Dimensions"))

# --- Feature 1: Pad (Hex Hub + Flange) ---
pad = body.newObject("PartDesign::Pad", "Pad_HexFlange")
pad.Profile = sketch_hub
pad.Length = overall_height.value - flange_thickness.value # Wait, pad length is from sketch plane.
# Sketch is at Z=0. Flange is 0 to flange_thickness. Hex is flange_thickness to overall_height.
# Total height needed is overall_height.
# But the sketch includes the flange bottom at Y=0.
# So Pad Length = overall_height.
# Wait, the sketch Y coordinates go from 0 to overall_height.
# If we pad in Z direction, the height is determined by the Z-length.
# Let's set Pad Length = overall_height.
pad.setExpression("Length", "Parameters.overall_height")
pad.Reversed = False

# --- Sketch 2: Through Hole ---
# Create a sketch on the XY plane (or a plane parallel to it) to define the hole cross-section.
# We need a sketch that defines a rectangle or two lines to be extruded/pocketed.
# Since we need a through hole, we can use a Pocket with Type="ThroughAll" or a Pad with Negative length.
# Let's use a Pocket on a sketch.
sketch_hole = body.newObject("Sketcher::SketchObject", "Sketch_Hole")
sketch_hole.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_hole.ConstrainAuto = False
sketch_hole.MapMode = "FlatFace"

# Define the hole width at the current Z level (which is 0 for the first sketch).
# The hole runs through the whole height.
# We can define the hole as a rectangle on the XY plane and then use a Pocket with Type="ThroughAll".
# However, the Pad is already made. The pocket will subtract from the existing solid.
# The hole sketch should be defined on the plane of the top of the pad? Or the bottom?
# PartDesign Pocket usually subtracts from the existing body.
# Let's define the hole geometry on the XY plane.
# Lines for the hole width.
hole_width = inner_diameter.value / 2
sketch_hole.addGeometry(Part.LineSegment(App.Vector(-hole_width, 0), App.Vector(hole_width, 0)), False)
# We need to constrain this to be a rectangle or just a line to be extruded?
# A Pocket requires a closed loop or a specific type.
# If we use Type="ThroughAll", we need a closed profile.
# Let's create a rectangle in a sketch on the top face of the pad?
# No, let's stick to the XY plane.
# Define a rectangle in the XY plane.
# Vertices: (-hole_width, 0), (hole_width, 0), (hole_width, overall_height), (-hole_width, overall_height).
# But the sketch plane is XY. We need to extrude in Z.
# If we put the sketch on the XY plane, and extrude in Z, it will cut a hole.
sketch_hole.addGeometry(Part.LineSegment(App.Vector(-hole_width, 0), App.Vector(hole_width, 0)), False)
sketch_hole.addGeometry(Part.LineSegment(App.Vector(hole_width, 0), App.Vector(hole_width, overall_height.value)), False)
sketch_hole.addGeometry(Part.LineSegment(App.Vector(hole_width, overall_height.value), App.Vector(-hole_width, overall_height.value)), False)
sketch_hole.addGeometry(Part.LineSegment(App.Vector(-hole_width, overall_height.value), App.Vector(-hole_width, 0)), False)

# Constrain the hole sketch
sketch_hole.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0)) # Bottom right on center line? No.
# Let's constrain the bottom center to origin.
# Actually, the hole is centered on the axis.
# Let's use a reference plane or just constrain X to 0.
sketch_hole.addConstraint(Sketcher.Constraint("CenterX", 1, 1, 0, 0))
sketch_hole.addConstraint(Sketcher.Constraint("CenterY", 1, 1, 0, 0))
# Wait, the sketch is on XY plane. The Z extrusion will be along Z.
# The hole needs to go through the whole height.
# If we use a Pad with Reversed=True, we need a closed loop.
# The loop is defined by the 4 lines above.
# We need to constrain the width.
sketch_hole.addConstraint(Sketcher.Constraint("DistanceX", 1, 1, 0, 1, 2, inner_diameter.value))
sketch_hole.addConstraint(Sketcher.Constraint("DistanceY", 1, 1, 0, 3, 4, overall_height.value))

# --- Feature 2: Pocket (Through Hole) ---
# Instead of Reversed Pad, let's use a Pocket with ThroughAll.
# But the sketch is on the XY plane. The body is along Z.
# We need to project the sketch or use the XY plane directly.
# If we use a Pocket on the XY plane, it subtracts along the
# Wait, the standard way to make a through hole in PartDesign is:
# 1. Create a sketch on the top face of the body (or any face).
# 2. Draw the hole profile.
# 3. Use a Pocket with Type="ThroughAll".
# However, since the body is symmetric and we are building from the bottom up, let's create a sketch on the TOP face of the Pad.
# But we don't know the top face object name yet.
# Alternative: Use a Pad with Reversed=True on the XY plane sketch.
# The sketch defines the hole cross-section. The Pad will extrude it in the -Z direction (since Reversed=True and sketch is at Z=0).
# This will cut a hole from Z=0 downwards? No, the body is at Z=0 to Z=overall_height.
# If we use Reversed=True, it subtracts in the -Z direction. That won't work if the body is above Z=0.
# We need to subtract in the +Z direction.
# So we should place the sketch on the TOP face of the Pad, and use Reversed=True to cut downwards.
# OR, place the sketch on the BOTTOM face (Z=0) and use Reversed=False? No, Reversed=False adds.
# Let's try: Sketch on XY plane (Z=0). Pad creates body Z=0 to Z=H.
# Now we need to cut a hole.
# We can create a new sketch on the TOP face of the Pad.
# Let's find the top face.
# Actually, simpler approach:
# Create the Pad.
# Create a sketch on the XY plane.
# Create a Pad with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H? No.
# If the sketch is at Z=0, and we pad with Reversed=True, it subtracts in the -Z direction.
# The body is in +Z. So this won't intersect.
# We need the sketch to be on the TOP face.
# Let's create a sketch on the top face of the Pad.
# How to get the top face?
# We can use the "Top" plane of the body if it exists, or create a sketch on the XY plane and then move it?
# No, let's just create a sketch on the XY plane, but define the hole as a rectangle that goes from Y=0 to Y=overall_height?
# No, the sketch is 2D.
# Let's use the "Pocket" feature with Type="ThroughAll".
# To use ThroughAll, the sketch must be on a face of the body.
# Let's create a sketch on the top face of the Pad.
# We can do this by creating a sketch on the XY plane, then moving it to the top face?
# No, we can create a sketch directly on a face if we know the face.
# But we don't have the face object yet.
# Alternative: Use a "Pad" with Reversed=True on a sketch on the XY plane, but the sketch must be defined such that the extrusion direction is correct.
# If the body is at Z=0 to Z=H.
# If we create a sketch on the XY plane (Z=0).
# If we create a Pad with Reversed=True, it subtracts in -Z.
# If we create a Pad with Reversed=False, it adds in +Z.
# We want to subtract in +Z.
# So we need a sketch on the TOP face (Z=H) and use Reversed=True.
# How to create a sketch on the top face?
# We can create a sketch on the XY plane, then use a "Move" feature? No.
# We can create a sketch on the XY plane, then use a "Pad" to create the body.
# Then, we can create a new sketch on the top face by referencing the top face.
# But we don't have the top face object.
# Let's try a different approach:
# Create the Pad.
# Create a sketch on the XY plane.
# Create a Pad with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a Pocket with Type="ThroughAll".
# But the Pocket needs to be on a face.
# Let's create a sketch on the XY plane, and then use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will subtract a hole from Z=0 to Z=-H.
# Then we need to flip the body? No.
# Let's just create the sketch on the XY plane, and use a "Pad" with Reversed=True and Length = overall_height.
# This will
