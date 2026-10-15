import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create new document
doc = App.newDocument("BushingPart")

# Define named parameters for easy editing later
params = doc.addObject("App::VarSet", "Dimensions")
params.addProperty("App::PropertyLength", "bushing_body_outer_diameter", "Dimensions", "Outer diameter of the main sleeve")
params.addProperty("App::PropertyLength", "bushing_body_inner_diameter", "Dimensions", "Inner diameter of the main sleeve")
params.addProperty("App::PropertyLength", "bushing_body_length", "Dimensions", "Total length of the sleeve body")
params.addProperty("App::PropertyLength", "lower_sleeve_extension_length", "Dimensions", "Length of the bottom extension")
params.addProperty("App::PropertyLength", "top_inner_flange_thickness", "Dimensions", "Thickness of the top inner lip flange")
params.addProperty("App::PropertyLength", "top_inner_flange_inner_diameter", "Dimensions", "Inner diameter of the top lip flange")
params.addProperty("App::PropertyLength", "bottom_flange_outer_diameter", "Dimensions", "Outer diameter of the bottom flange")
params.addProperty("App::PropertyLength", "bottom_flange_thickness", "Dimensions", "Thickness of the bottom flange")
params.addProperty("App::PropertyLength", "expansion_slit_length", "Dimensions", "Total length of the expansion slit")
params.addProperty("App::PropertyLength", "expansion_slit_width", "Dimensions", "Width of the expansion slit at the surface")
params.addProperty("App::PropertyLength", "expansion_slit_depth", "Dimensions", "Radial depth of the slit from the outer surface")
params.addProperty("App::PropertyLength", "top_flange_bore_diameter", "Dimensions", "Diameter of the top recess bore")
params.addProperty("App::PropertyLength", "top_flange_bore_depth", "Dimensions", "Depth of the top recess")

# Set initial values
params.bushing_body_outer_diameter = 150.0
params.bushing_body_inner_diameter = 130.0
params.bushing_body_length = 640.0
params.lower_sleeve_extension_length = 20.0
params.top_inner_flange_thickness = 10.0
params.top_inner_flange_inner_diameter = 85.0
params.bottom_flange_outer_diameter = 190.0
params.bottom_flange_thickness = 10.0
params.expansion_slit_length = 630.0
params.expansion_slit_width = 30.0
params.expansion_slit_depth = 5.0
params.top_flange_bore_diameter = 100.0
params.top_flange_bore_depth = 30.0

# Create the Body
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject("Body")

# Create the main body sketch on XY plane (center of the part)
# Origin: (0,0,0) -> Center of the bushing
sketch_main = body.newObject("Sketcher::SketchObject", "MainSketch")
sketch_main.Placement = App.Placement(App.Vector(0, 0, -params.bushing_body_length/2.0))
sketch_main.AttachmentSupport = [App.getDocument("PartDesign").getObject("XY_Plane")] # Assuming standard planes exist or we create them
# Since we are in a new doc, standard planes might not exist. Let's define coordinates manually or assume standard setup.
# To be safe in a script, we usually attach to planes. If planes don't exist, Sketcher might fail.
# Standard practice in scripts: assume XY_Plane exists or create it.
# Let's try to create the planes if they don't exist, or just attach to the document's XY_Plane if it's the default.
# FreeCAD 1.1 usually starts with XY_Plane, YZ_Plane, XZ_Plane in PartDesign workbench.
# However, to be robust, we will define vectors directly if needed, but Sketcher needs a face/plane.
# Let's assume standard planes exist as per FreeCAD default document structure.
# If not, we can create them.
# Let's create the planes explicitly to ensure robustness.

# Create XY_Plane if not exists (usually index 0 in PartDesign)
if "XY_Plane" not in doc:
    xy_plane = doc.addObject("PartDesign::Plane", "XY_Plane")
    xy_plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation())
    doc.recompute()
if "YZ_Plane" not in doc:
    yz_plane = doc.addObject("PartDesign::Plane", "YZ_Plane")
    yz_plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(App.Rotation(0,0,1))) # Rotated 90 deg
    doc.recompute()
if "XZ_Plane" not in doc:
    xz_plane = doc.addObject("PartDesign::Plane", "XZ_Plane")
    xz_plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(App.Rotation(0,1,0))) # Rotated 90 deg
    doc.recompute()

# Re-attach to specific planes
sketch_main.Placement = App.Placement(App.Vector(0, 0, -params.bushing_body_length/2.0))
sketch_main.AttachmentSupport = [doc.getObject("XY_Plane")]
sketch_main.ViewObject.Placement = App.Placement(App.Vector(0,0,0))

# Add Geometry: Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bushing_body_outer_diameter / 2.0)
sketch_main.addGeometry(outer_circle, False)

# Add Geometry: Inner Circle
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bushing_body_inner_diameter / 2.0)
sketch_main.addGeometry(inner_circle, False)

# Add Geometry: Top Edge (for the lip)
# The top of the sleeve is at z = -length/2 + length = length/2
top_z = params.bushing_body_length / 2.0
top_edge = Part.LineSegment(App.Vector(0, 0, top_z), App.Vector(0, 0, top_z))
sketch_main.addGeometry(top_edge, False)

# Add Geometry: Bottom Edge (for the extension start)
bottom_z = -params.bushing_body_length / 2.0
bottom_edge = Part.LineSegment(App.Vector(0, 0, bottom_z), App.Vector(0, 0, bottom_z))
sketch_main.addGeometry(bottom_edge, False)

# Add constraints
# Coincident: Top edge center to origin (on Z axis) - implicit by placement
# Coincident: Bottom edge center to origin
# Tangent: Inner and Outer circles
sketch_main.addConstraint(Sketcher.Constraint("Equal", 0, 1, 2, 1)) # Outer radius
sketch_main.addConstraint(Sketcher.Constraint("Equal", 0, 3, 4, 1)) # Inner radius
# Tangent between circles
sketch_main.addConstraint(Sketcher.Constraint("Tangent", 0, 0, 1, 0))
sketch_main.addConstraint(Sketcher.Constraint("Tangent", 0, 1, 3, 0))

# Pad the main body
pad_main = body.newObject("PartDesign::Pad", "PadMainBody")
pad_main.Profile = sketch_main
pad_main.Length = params.bushing_body_length
pad_main.Reverse = False
pad_main.Type = "Solid"
doc.recompute()

# --- Lower Sleeve Extension ---
# Sketch on XZ plane (side view)
sketch_lower = body.newObject("Sketcher::SketchObject", "SketchLowerExt")
sketch_lower.Placement = App.Placement(App.Vector(0, 0, -params.bushing_body_length/2.0), App.Rotation(App.Rotation(0,0,1))) # Rotate to look from side
sketch_lower.AttachmentSupport = [doc.getObject("XZ_Plane")]
sketch_lower.ViewObject.Placement = App.Placement(App.Vector(0,0,0))

# Geometry: Outer Arc (Extension side)
# Center at (0,0), Radius = Outer/2
# We need an arc from bottom of main body up to extension length
# Main body bottom is at z=0 in this local sketch (due to placement)
# Extension goes down to z = -lower_sleeve_extension_length
# Actually, let's keep the sketch on the side wall.
# Let's re-position. The main body pad ended at z = -length/2.
# So the bottom face is at z = -length/2.
# We want to extend downwards.
# Let's place the sketch on the XZ plane at the bottom face.
sketch_lower.Placement = App.Placement(App.Vector(0, 0, -params.bushing_body_length/2.0), App.Rotation(App.Rotation(0,0,1)))
sketch_lower.AttachmentSupport = [doc.getObject("XZ_Plane")]

# Line for bottom edge of main body
line_bottom = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0, 0, 0)) # Point at origin
# Let's define the profile on the XZ plane.
# Origin (0,0) is the center axis.
# X axis is horizontal, Z axis is vertical.
# The main body is from Z=0 to Z=extension_length (positive up) in the sketch?
# No, the main body is below.
# Let's place the sketch such that Z=0 is the start of the extension.
# Extension goes from Z=0 to Z=-extension_length.
# Let's just draw lines.
# Line 1: From (0,0) to (Outer/2, 0)
# Line 2: From (Outer/2, 0) to (Outer/2, -extension_length)
# Line 3: From (Outer/2, -extension_length) to (-Outer/2, -extension_length)
# Line 4: From (-Outer/2, -extension_length) to (-Outer/2, 0)
# Line 5: From (-Outer/2, 0) to (0,0) (Axis)
# Inner circle: From (0,0) with radius Inner/2

# Simplified: Draw the profile of the extension relative to the main body bottom.
# Main body bottom is at Z=0 in this sketch.
# Extension goes down.
# Let's define the sketch on the face at the bottom of the main body.
# The face normal is Z (in global).
# In the sketch plane (XZ), the Y coordinate is 0.
# Let's define the geometry.

# Outer Arc/Line
outer_bottom = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.bushing_body_outer_diameter/2, 0, 0))
sketch_lower.addGeometry(outer_bottom, False)
# Vertical side
ext_side = Part.LineSegment(App.Vector(params.bushing_body_outer_diameter/2, 0, 0), App.Vector(params.bushing_body_outer_diameter/2, 0, -params.lower_sleeve_extension_length))
sketch_lower.addGeometry(ext_side, False)
# Bottom of extension
ext_bottom = Part.LineSegment(App.Vector(params.bushing_body_outer_diameter/2, 0, -params.lower_sleeve_extension_length), App.Vector(-params.bushing_body_outer_diameter/2, 0, -params.lower_sleeve_extension_length))
sketch_lower.addGeometry(ext_bottom, False)
# Vertical side up
ext_side_up = Part.LineSegment(App.Vector(-params.bushing_body_outer_diameter/2, 0, -params.lower_sleeve_extension_length), App.Vector(-params.bushing_body_outer_diameter/2, 0, 0))
sketch_lower.addGeometry(ext_side_up, False)
# Axis line
axis_line = Part.LineSegment(App.Vector(-params.bushing_body_outer_diameter/2, 0, 0), App.Vector(0, 0, 0))
sketch_lower.addGeometry(axis_line, False)

# Inner Circle (for the hole continuation)
inner_bottom = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bushing_body_inner_diameter/2.0)
sketch_lower.addGeometry(inner_bottom, False)

# Constraints
sketch_lower.addConstraint(Sketcher.Constraint("Point", 0, 0, 0, 1)) # Start at origin
sketch_lower.addConstraint(Sketcher.Constraint("Point", 1, 0, 1, 1)) # End at x=outer/2, z=0
sketch_lower.addConstraint(Sketcher.Constraint("Length", 1, 2, params.lower_sleeve_extension_length))
sketch_lower.addConstraint(Sketcher.Constraint("Length", 2, 3, params.bushing_body_outer_diameter))
sketch_lower.addConstraint(Sketcher.Constraint("Point", 4, 0, 0, 1))
sketch_lower.addConstraint(Sketcher.Constraint("Point", 5, 0, 1, 1))
sketch_lower.addConstraint(Sketcher.Constraint("Point", 6, 0, 2, 1))
sketch_lower.addConstraint(Sketcher.Constraint("Tangent", 0, 0, 1, 0))
sketch_lower.addConstraint(Sketcher.Constraint("Tangent", 1, 0, 2, 0))
sketch_lower.addConstraint(Sketcher.Constraint("Tangent", 2, 0, 3, 0))
sketch_lower.addConstraint(Sketcher.Constraint("Tangent", 3, 0, 4, 0))
sketch_lower.addConstraint(Sketcher.Constraint("Tangent", 4, 0, 5, 0))
# Inner circle tangent to outer lines
sketch_lower.addConstraint(Sketcher.Constraint("Tangent", 7, 0, 1, 0))
sketch_lower.addConstraint(Sketcher.Constraint("Tangent", 7, 0, 2, 0))

# Pad the extension (Subtract? No, this is additive material if we are building from inside out?
# Wait, the main body is a hole in the center.
# The extension continues the outer shell.
# So we PAD with solid=True.
pad_ext = body.newObject("PartDesign::Pad", "PadLowerExt")
pad_ext.Profile = sketch_lower
pad_ext.Length = params.lower_sleeve_extension_length
pad_ext.Reverse = False # Extrude in negative Z direction relative to sketch?
# The sketch is on the XZ plane. The normal is Y.
# We need to extrude along -Y to go "down" in the model if we oriented the sketch correctly?
# Actually, let's use the Z direction in the global frame for the main body.
# The main body was extruded along Z.
# The bottom face is at Z = -length/2.
# We want to extend further in -Z.
# The sketch is on the XZ plane (side view). The normal of the face is Y.
# Extruding along Y will move the part sideways.
# This approach is tricky with sketch orientation.
# Alternative: Create a sketch on the bottom face directly using the Face as support.
# Let's restart the extension logic to be simpler.
# Instead of side view sketch, let's use a sketch on the bottom face (XZ plane).
# We can rotate the sketch to align with the extrusion direction.
# Or better: Use a sketch on the XY plane at the bottom Z, and extrude along Z.
# Let's do that.

# Reset/Correct approach for Lower Extension:
# Create sketch on XY plane at Z = -length/2.
# Extrude along Z.
# Profile: Outer arc from -length/2 to -length/2 - extension_length.
# Inner arc (hole).

# Remove previous sketch and pad if they failed or are complex. 
# Let's rebuild the extension cleanly.
# Sketch on XY plane, offset Z.
sketch_lower_clean = body.newObject("Sketcher::SketchObject", "SketchLowerExtClean")
sketch_lower_clean.Placement = App.Placement(App.Vector(0, 0, -params.bushing_body_length/2.0 - params.lower_sleeve_extension_length))
# Wait, we need to build it from the existing solid.
# Let's place the sketch on the bottom face of the MAIN body (at -length/2).
# Then extrude downwards.
sketch_lower_clean.Placement = App.Placement(App.Vector(0, 0, -params.bushing_body_length/2.0))
sketch_lower_clean.AttachmentSupport = [doc.getObject("XY_Plane")]
# Rotate the sketch 90 degrees so it lies on the bottom face and extrudes down?
# No, if we attach to XY plane, the sketch is on XY plane. Extruding along Z goes UP.
# We need to extrude DOWN.
# So we place the sketch on the bottom face, and extrude with Reverse=True.
# But the sketch must be on the face.
# Let's attach to the bottom face of the body?
# The body object has faces.
# Let's use the XY_Plane but rotate the sketch 180 around X axis so Z becomes -Z?
# Or just extrude with negative length? Pad doesn't support negative length directly, only Reverse.
# If we put the sketch on the bottom face, the normal points -Z.
# Extruding with Reverse=True goes in the direction of the normal (-Z).
# So we need the sketch to be on the bottom face.
# How to make a sketch on a specific face?
# sketch_lower_clean.Placement = App.Placement(App.Vector(0, 0, -params.bushing_body_length/2.0))
# sketch_lower_clean.AttachmentSupport = [doc.getObject("XY_Plane")] # This puts it on XY plane.
# We need it on the bottom face.
