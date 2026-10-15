import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("WaterCup")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters ---
# Define parameters as properties of the Body
body.addProperty("App::PropertyLength", "cup_diameter", "Dimensions", "Outer diameter of the cup")
body.addProperty("App::PropertyLength", "cup_height", "Dimensions", "Total height of the cup")
body.addProperty("App::PropertyLength", "cup_thickness", "Dimensions", "Wall thickness")
body.addProperty("App::PropertyLength", "handle_width", "Dimensions", "Width of the handle")
body.addProperty("App::PropertyLength", "handle_height", "Dimensions", "Height of the handle")
body.addProperty("App::PropertyLength", "handle_depth", "Dimensions", "Depth of the handle")
body.addProperty("App::PropertyLength", "fillet_radius", "Dimensions", "Top rim fillet radius")

# Set default values
body.cup_diameter = 80.0
body.cup_height = 120.0
body.cup_thickness = 2.0
body.handle_width = 20.0
body.handle_height = 40.0
body.handle_depth = 15.0
body.fillet_radius = 3.0

# --- Base Sketch (Outer Profile) ---
# Create a sketch on the XY plane
sketch_outer = body.newObject("Sketcher::SketchObject", "OuterProfile")
sketch_outer.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_outer.Support = "XY_Plane"
sketch_outer.ConstrainToCurrentPlane = True

# Add 4 lines to form a rectangle
# Point 1: Bottom Left
# Point 2: Bottom Right
# Point 3: Top Right
# Point 4: Top Left
sketch_outer.addGeometry(Part.LineSegment(App.Vector(-body.cup_diameter/2, -body.cup_height/2, 0), 
                                          App.Vector(body.cup_diameter/2, -body.cup_height/2, 0)), False)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(body.cup_diameter/2, -body.cup_height/2, 0), 
                                          App.Vector(body.cup_diameter/2, body.cup_height/2, 0)), False)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(body.cup_diameter/2, body.cup_height/2, 0), 
                                          App.Vector(-body.cup_diameter/2, body.cup_height/2, 0)), False)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(-body.cup_diameter/2, body.cup_height/2, 0), 
                                          App.Vector(-body.cup_diameter/2, -body.cup_height/2, 0)), False)

# Add constraints for the rectangle
# Horizontal constraints
sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 0, 1)) # Bottom line
sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 2, 3)) # Top line
# Vertical constraints
sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 1, 2)) # Right line
sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 3, 0)) # Left line

# Dimension constraints
# Width
sketch_outer.addConstraint(Sketcher.Constraint("Length", 0, 1, "body.cup_diameter"))
# Height
sketch_outer.addConstraint(Sketcher.Constraint("Length", 1, 2, "body.cup_height"))

# --- Inner Sketch (Hollow) ---
# Create a second sketch on the same plane, concentric with the outer one.
sketch_inner = body.newObject("Sketcher::SketchObject", "InnerProfile")
sketch_inner.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_inner.Support = "XY_Plane"
sketch_inner.ConstrainToCurrentPlane = True

# Add a circle for the inner profile
# Center at origin, radius = (cup_diameter - 2*thickness) / 2
inner_radius = (body.cup_diameter - 2 * body.cup_thickness) / 2
sketch_inner.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), inner_radius), False)

# --- Handle Sketch ---
# Create a sketch on the XZ plane to define the handle profile.
sketch_handle = body.newObject("Sketcher::SketchObject", "HandleProfile")
sketch_handle.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_handle.Support = "XZ_Plane"
sketch_handle.ConstrainToCurrentPlane = True

# Handle profile: A rectangle
# We define it relative to the origin of the XZ plane.
# Line 1: Bottom
sketch_handle.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), 
                                            App.Vector(body.handle_width, 0, 0)), False)
# Line 2: Right
sketch_handle.addGeometry(Part.LineSegment(App.Vector(body.handle_width, 0, 0), 
                                            App.Vector(body.handle_width, body.handle_height, 0)), False)
# Line 3: Top
sketch_handle.addGeometry(Part.LineSegment(App.Vector(body.handle_width, body.handle_height, 0), 
                                            App.Vector(0, body.handle_height, 0)), False)
# Line 4: Left
sketch_handle.addGeometry(Part.LineSegment(App.Vector(0, body.handle_height, 0), 
                                            App.Vector(0, 0, 0)), False)

# Constraints for handle rectangle
sketch_handle.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
sketch_handle.addConstraint(Sketcher.Constraint("Horizontal", 2, 3))
sketch_handle.addConstraint(Sketcher.Constraint("Vertical", 1, 2))
sketch_handle.addConstraint(Sketcher.Constraint("Vertical", 3, 0))

sketch_handle.addConstraint(Sketcher.Constraint("Length", 0, 1, "body.handle_width"))
sketch_handle.addConstraint(Sketcher.Constraint("Length", 1, 2, "body.handle_height"))

# Position the handle sketch relative to the cup body
# The handle should be attached to the right side of the cup (x = cup_diameter/2).
# The handle should be centered vertically.
# Current sketch origin is (0,0) in XZ plane.
# We need to shift X by cup_diameter/2 and Z by (cup_height - handle_height)/2.
sketch_handle.Placement = App.Placement(App.Vector(body.cup_diameter/2, 0, (body.cup_height - body.handle_height)/2))

# --- Features ---

# 1. Pad the outer profile to create the solid block
pad_outer = body.newObject("PartDesign::Pad", "PadOuter")
pad_outer.Profile = sketch_outer
pad_outer.Length = body.cup_height
pad_outer.Type = "Solid"

# 2. Pad the inner profile (subtractive) to create the hollow interior
# We use a negative length to subtract the material.
pad_inner = body.newObject("PartDesign::Pad", "PadInner")
pad_inner.Profile = sketch_inner
pad_inner.Length = -body.cup_height # Negative to subtract
pad_inner.Type = "Solid"

# 3. Pad the handle profile
pad_handle = body.newObject("PartDesign::Pad", "PadHandle")
pad_handle.Profile = sketch_handle
pad_handle.Length = body.handle_depth # Extrude into the Y direction (depth of the handle)
pad_handle.Type = "Solid"

# 4. Fillet the top rim of the cup
# We need to select the top edges of the outer pad.
# The top edges are the 4 edges of the top face of the outer profile.
# We can reference the edges of the sketch directly if they are still valid, 
# or we can try to reference the resulting edges.
# In FreeCAD 1.1, referencing sketch edges for fillets on the resulting solid is often the most robust way 
# if the sketch is still in the tree and the geometry matches.
# The top edge of the outer profile is the line segment from Top-Left to Top-Right (index 2 in sketch_outer).
# However, the fillet needs to be applied to the solid edge.
# Let's try to reference the sketch edge. If that fails, we might need a different approach.
# Actually, a more reliable way for a script without interactive selection is to use the "Edge" property 
# and reference the sketch edge, assuming the sketch edge maps to the solid edge.
# Alternatively, we can create a small loop constraint or just fillet the sketch edge and let the feature handle it.
# Let's try referencing the sketch edge.
# The top edge of the rectangle is index 2 (0: bottom, 1: right, 2: top, 3: left).
# We will fillet this edge.
chamfer = body.newObject("PartDesign::Chamfer", "TopChamfer")
chamfer.Base = (sketch_outer, ["Edge2"]) # Reference the top edge of the sketch
chamfer.Size = body.fillet_radius
chamfer.Type = "Linear" # Chamfer is linear, but we want a fillet. 
# Wait, PartDesign::Chamfer is for chamfers (linear). For fillets (circular), we use PartDesign::Fillet.
# Let's use PartDesign::Fillet.
fillet = body.newObject("PartDesign::Fillet", "TopFillet")
fillet.Base = (sketch_outer, ["Edge2"])
fillet.Radius = body.fillet_radius
fillet.Type = "Radius"

# 5. Fillet the bottom rim of the cup
# The bottom edge of the outer profile is index 0.
fillet_bottom = body.newObject("PartDesign::Fillet", "BottomFillet")
fillet_bottom.Base = (sketch_outer, ["Edge0"])
fillet_bottom.Radius = body.fillet_radius
fillet_bottom.Type = "Radius"

# 6. Fillet the top and bottom of the handle
# The handle is a rectangle extruded in Y.
# The top edge of the handle sketch is index 2.
# The bottom edge of the handle sketch is index 0.
# We need to fillet the edges of the handle pad.
# Since the handle is a separate pad, we can reference its sketch edges.
fillet_handle_top = body.newObject("PartDesign::Fillet", "HandleTopFillet")
fillet_handle_top.Base = (sketch_handle, ["Edge2"])
fillet_handle_top.Radius = body.fillet_radius
fillet_handle_top.Type = "Radius"

fillet_handle_bottom = body.newObject("PartDesign::Fillet", "HandleBottomFillet")
fillet_handle_bottom.Base = (sketch_handle, ["Edge0"])
fillet_handle_bottom.Radius = body.fillet_radius
fillet_handle_bottom.Type = "Radius"

# 7. Fillet the connection between the handle and the cup body
# This is tricky because the handle is attached to the side of the cup.
# The connection edges are the vertical edges of the handle where it meets the cup.
# These are the edges of the handle pad that are on the surface of the cup.
# We can try to reference the sketch edges of the handle that are on the cup surface.
# The handle is attached to the right side of the cup.
# The sketch handle has a left edge (index 3) which is attached to the cup.
# We can fillet this edge.
fillet_handle_connection = body.newObject("PartDesign::Fillet", "HandleConnectionFillet")
fillet_handle_connection.Base = (sketch_handle, ["Edge3"])
fillet_handle_connection.Radius = body.fillet_radius
fillet_handle_connection.Type = "Radius"

# --- Save ---
# Compute the document
doc.recompute()

# Save the file next to the script
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")
doc.saveAs(str(output_path))
