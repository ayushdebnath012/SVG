import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("ElbowFlange")

# --- Parameters ---
# Define a VarSet to hold all parameters for easy editing
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "flange_outer_diameter", "Dimensions", "Outer diameter of the flange")
params.addProperty("App::PropertyLength", "elbow_flange_length", "Dimensions", "Length of the straight flange section")
params.addProperty("App::PropertyLength", "elbow_flange_height", "Dimensions", "Height of the flange face")
params.addProperty("App::PropertyAngle", "elbow_angle", "Dimensions", "Angle of the elbow (degrees)")
params.addProperty("App::PropertyLength", "elbow_radius", "Dimensions", "Radius of the elbow curve")
params.addProperty("App::PropertyLength", "elbow_pipe_diameter", "Dimensions", "Diameter of the pipe")
params.addProperty("App::PropertyLength", "elbow_pipe_thickness", "Dimensions", "Thickness of the pipe wall")
params.addProperty("App::PropertyLength", "bolt_circle_radius", "Dimensions", "Radius of the bolt circle")
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of the bolt holes")
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Number of bolt holes")

# Set values as per requirements
params.flange_outer_diameter = 200.0
params.elbow_flange_length = 300.0
params.elbow_flange_height = 300.0
params.elbow_angle = 90.0
params.elbow_radius = 100.0
params.elbow_pipe_diameter = 100.0
params.elbow_pipe_thickness = 5.0
params.bolt_circle_radius = 72.5
params.bolt_hole_diameter = 16.0
params.number_bolt_holes = 8

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Flange Sketch (Top View) ---
# We will create the flange profile on the XY plane.
# The profile will be a rectangle with a hole in the middle (for the pipe) and bolt holes.
# However, to make the elbow rotation easier, we often define the flange on a plane perpendicular to the elbow axis.
# Let's define the main flange sketch on the XY plane.
# The elbow will be created by revolving a profile on the XZ plane.
# The flanges will be added as Pads extending from the elbow body.

# 1. Main Flange Profile Sketch (XY Plane)
# This sketch defines the cross-section of the flange and the pipe connection.
# We need to be careful with the coordinate system.
# Let's assume the elbow bends in the XZ plane.
# The flange is perpendicular to the elbow axis.
# If the elbow axis is initially along Z, the flange is in XY.
# If the elbow bends 90 deg, the second flange will be in XZ (or similar).

# Let's create the first flange sketch on the XY plane.
# The profile will be a rectangle representing the flange face, with a circular cutout for the pipe.
# We will add bolt holes here.

sketch_flange = body.newObject("Sketcher::SketchObject", "FlangeProfile")
sketch_flange.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_flange.Support = (doc.getObject("XY_Plane"), [])
sketch_flange.MapMode = "FlatFace"

# Define the flange outer diameter circle
# Center at (0,0), Radius = flange_outer_diameter / 2
r_flange = params.flange_outer_diameter / 2.0
circle_flange = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_flange)
sketch_flange.addGeometry(circle_flange, False)

# Define the pipe inner diameter circle (for the cutout)
# The pipe diameter is params.elbow_pipe_diameter
# The flange height is params.elbow_flange_height.
# The sketch is on the face of the flange.
# We need to cut a hole of size (pipe_diameter + 2*thickness) or just pipe_diameter?
# Usually, the flange covers the pipe. The hole should match the pipe outer diameter.
r_pipe_outer = params.elbow_pipe_diameter / 2.0
circle_pipe = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_pipe_outer)
sketch_flange.addGeometry(circle_pipe, False)

# Add bolt holes
# Bolt circle radius
r_bolt = params.bolt_circle_radius
# Bolt hole diameter
d_bolt = params.bolt_hole_diameter
r_bolt_hole = d_bolt / 2.0

# We need to generate points on the bolt circle.
# Since we can't use loops easily in pure Part/Sketcher API without a loop function,
# we will add the first hole and then use a pattern later, or add all holes manually if N is small.
# N=8 is small enough to add manually or use a loop if we define a helper.
# Let's use a loop to add the geometry to the sketch.
import math

# Add bolt hole geometries
for i in range(params.number_bolt_holes):
    angle = (i / params.number_bolt_holes) * 360.0 * math.pi / 180.0
    x = r_bolt * math.cos(angle)
    y = r_bolt * math.sin(angle)
    center = App.Vector(x, y, 0)
    hole = Part.Circle(center, App.Vector(0, 0, 1), r_bolt_hole)
    sketch_flange.addGeometry(hole, False)

# Constraints for the flange sketch
# Coincident center of flange and pipe
sketch_flange.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
# Concentric flange and pipe
sketch_flange.addConstraint(Sketcher.Constraint("Concentric", 0, 1, 1, 2))
# Concentric pipe and bolt holes
for i in range(params.number_bolt_holes):
    angle = (i / params.number_bolt_holes) * 360.0 * math.pi / 180.0
    # We need to reference the specific hole. Sketcher constraints usually work by index.
    # This is tricky to automate perfectly without knowing the internal index order.
    # Alternative: Use a Polar Pattern feature later on the solid, which is more robust.
    # For now, let's just constrain the bolt holes to be concentric with the pipe.
    # We can't easily reference them by index in a loop without knowing the order.
    # Let's skip explicit concentric constraints for bolt holes in the sketch and rely on the pattern.
    # Instead, let's constrain the bolt holes to be on the bolt circle.
    # This requires a "Point on Circle" constraint, but Sketcher doesn't have a direct "Point on Circle" for circles.
    # It has "Point on Line" or "Coincident".
    # Let's just leave the bolt holes unconstrained relative to each other in the sketch, 
    # and use a Polar Pattern feature to place them perfectly.
    # Wait, the sketch needs to be valid.
    # Let's constrain the bolt holes to be concentric with the pipe.
    # We can do this by referencing the center of the bolt hole and the center of the pipe.
    # But we don't know the index.
    # Let's try a different approach: Create the bolt holes in the sketch, then use a Polar Pattern feature 
    # to replicate the first bolt hole. This is cleaner.
    pass

# Let's remove the bolt holes from the sketch and add them via a pattern feature.
# Re-add only the flange and pipe circles.
sketch_flange.removeGeometry(sketch_flange.Geometry[2]) # Remove pipe circle (index 2)
sketch_flange.removeGeometry(sketch_flange.Geometry[3]) # Remove first bolt hole (index 3)
# Actually, let's just rebuild the sketch cleanly.
sketch_flange = body.newObject("Sketcher::SketchObject", "FlangeProfile")
sketch_flange.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_flange.Support = (doc.getObject("XY_Plane"), [])
sketch_flange.MapMode = "FlatFace"

# Add Flange Outer Circle
circle_flange = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_flange)
sketch_flange.addGeometry(circle_flange, False)

# Add Pipe Outer Circle
circle_pipe = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_pipe_outer)
sketch_flange.addGeometry(circle_pipe, False)

# Constraints
sketch_flange.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
sketch_flange.addConstraint(Sketcher.Constraint("Concentric", 0, 1, 1, 2))

# --- Elbow Profile Sketch (XZ Plane) ---
# This sketch defines the cross-section of the elbow pipe.
# It will be revolved around the Z axis (or Y axis depending on orientation).
# Let's assume the elbow bends in the XZ plane, so the axis of revolution is the Y axis.
# The profile will be a rectangle with a hole.
# The rectangle height will be the pipe diameter.
# The rectangle width will be the elbow radius + pipe radius (to cover the curve).
# Actually, the elbow is a torus segment.
# The profile is a rectangle of height = pipe_diameter, and width = elbow_radius + pipe_radius.
# The center of the rectangle should be at (elbow_radius, 0) if the axis is at 0.
# Let's place the profile such that the inner radius of the elbow is at the axis.
# So the rectangle starts at x=0 and ends at x=elbow_radius + pipe_radius.
# The y-coordinates are from -pipe_radius to +pipe_radius.

sketch_elbow = body.newObject("Sketcher::SketchObject", "ElbowProfile")
sketch_elbow.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_elbow.Support = (doc.getObject("XZ_Plane"), [])
sketch_elbow.MapMode = "FlatFace"

# Define the elbow profile rectangle
# Height = pipe_diameter
# Width = elbow_radius + pipe_radius
# Position: Bottom-left at (0, -pipe_radius)
h_pipe = params.elbow_pipe_diameter
w_elbow = params.elbow_radius + h_pipe / 2.0

rect_elbow = Part.makeBox(w_elbow, h_pipe, App.Vector(0, -h_pipe/2, 0))
sketch_elbow.addGeometry(rect_elbow, False)

# Define the hole in the elbow profile
# The hole is centered in the rectangle.
hole_elbow = Part.Circle(App.Vector(w_elbow/2, 0, 0), App.Vector(0, 0, 1), h_pipe/2)
sketch_elbow.addGeometry(hole_elbow, False)

# Constraints
sketch_elbow.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Center of rect and hole
sketch_elbow.addConstraint(Sketcher.Constraint("Concentric", 0, 1, 1, 2)) # Center of rect and hole

# --- Create the Elbow Body ---
# Revolve the elbow profile around the Y axis (which is the vertical axis in XZ plane? No, Y is perpendicular to XZ).
# In FreeCAD, XZ plane has normal Y. So revolving around Y axis creates a torus-like shape.
# The axis of revolution for the sketch on XZ plane is the Y axis.
# We need to reference the Y axis.
# The sketch is on XZ plane. The Y axis is the normal to the plane.
# We can use the Y_Axis object.

rev_elbow = body.newObject("PartDesign::Revolution", "ElbowRevolve")
rev_elbow.Profile = sketch_elbow
rev_elbow.ReferenceAxis = (doc.getObject("Y_Axis"), [])
rev_elbow.Angle = 360.0

# --- Create the Flanges ---
# We need to add flanges at both ends of the elbow.
# The elbow is a torus segment. The "ends" are the inner and outer radii of the torus.
# Inner radius = elbow_radius
# Outer radius = elbow_radius + pipe_radius
# The flanges are perpendicular to the elbow axis.
# Since the elbow axis is the Y axis, the flanges are in the XY and XZ planes?
# No, the elbow axis is the Y axis. The flanges are perpendicular to the Y axis.
# So the flanges are in the XZ plane?
# Wait, if the elbow is a torus segment around the Y axis, the "ends" are at the top and bottom of the torus (along Y).
# The flanges are perpendicular to the Y axis, so they are in the XZ plane.
# But the elbow profile was on the XZ plane.
# Let's re-orient.
# Standard elbow: Pipe runs along Z, bends 90 deg to run along X.
# Let's stick to the torus model.
# Axis of revolution: Y.
# Profile: Rectangle on XZ plane.
# The torus is generated by revolving the rectangle around Y.
# The "ends" of the elbow are at the top (max Y) and bottom (min Y) of the torus.
# The flanges are perpendicular to the Y axis, so they are in the XZ plane.
# But the elbow profile is already in the XZ plane.
# This means the flanges are coplanar with the profile sketch?
# No, the flanges are attached to the torus surface.
# The torus surface at the top (max Y) is a circle in the XZ plane.
# The flange is a disk in the XZ plane.
# So we can create the flanges by extruding the flange profile along the Y axis.
# But the flange profile is in the XZ plane.
# We need to extrude it along the Y axis.
# The extrusion direction is the normal to the XZ plane, which is Y.
# So we can use a Pad with the flange profile and a specific direction.

# Flange 1 (Top)
# Extrude along +Y
pad_flange1 = body.newObject("PartDesign::Pad", "Flange1")
pad_flange1.Profile = sketch_flange
pad_flange1.Length = params.elbow_flange_height
pad_flange1.Direction = (App.Vector(0, 1, 0), []) # Extrude along +Y

# Flange 2 (Bottom)
# Extrude along -Y
pad_flange2 = body.newObject("PartDesign::Pad", "Flange2")
pad_flange2.Profile = sketch_flange
pad_flange2.Length = params.elbow_flange_height
pad_flange2.Direction = (App.Vector(0, -1, 0), []) # Extrude along -Y

# --- Bolt Holes ---
# We need to add bolt holes to the flanges.
# The bolt holes are on the flange faces (XZ plane).
# We can use a Pocket feature on the flange faces.
# The profile for the pocket is the bolt hole circle.
# We need to create a sketch for the bolt hole on the XZ plane.
# But the flanges are already created.
# We can create a sketch on the XZ plane, then use a Pocket feature.
# The pocket will subtract the material.

# Create a sketch for the bolt hole on the XZ plane.
# We need to place the bolt hole at the correct position on the flange.
# The flange is a disk of radius r_flange.
# The bolt circle is at r_bolt.
# We need to create a sketch that contains the bolt hole geometry.
# Since we have 8 holes, we can use a Polar Pattern feature.
# Let's create a sketch with one bolt hole.
sketch_bolt = body.newObject("Sketcher::SketchObject", "BoltHoleSketch")
sketch_bolt.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_bolt.Support = (doc.getObject("XZ_Plane"), [])
sketch_bolt.MapMode = "FlatFace"

# Add one bolt hole circle
hole_bolt = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_bolt_hole)
sketch_bolt.addGeometry(hole_bolt, False)

# Create a Pocket for the bolt hole
pocket_bolt = body.newObject("PartDesign::Pocket", "BoltPocket")
pocket_bolt.Profile = sketch_bolt
pocket_bolt.Type = "ThroughAll" # Cut through the flange

# Now, we need to pattern this pocket.
# The pockets are on the flanges.
# The flanges are at the top and bottom of the elbow.
# The bolt holes are arranged in a circle around the Y axis.
# We can use a Polar Pattern feature.
# The axis of the pattern is the Y axis.
# The original is the pocket.
# The angle is 360, occurrences = number_bolt_holes.

# However, the pocket is on the flange face.
# The flange face is in the XZ plane.
# The Y axis is perpendicular to the XZ plane.
# So a polar pattern around the Y axis will rotate the pocket around the Y axis.
# This is exactly what we want
