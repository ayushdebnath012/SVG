import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("CylindricalPin")

# Create the Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a VarSet to hold parameters for easy editing
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "diameter", "Dimensions", "Pin Diameter")
params.addProperty("App::PropertyLength", "length", "Dimensions", "Overall Length")
params.addProperty("App::PropertyLength", "chamfer_length", "Dimensions", "Chamfer Length")
params.addProperty("App::PropertyAngle", "chamfer_angle", "Dimensions", "Chamfer Angle")

# Set default values
params.diameter = 1.0
params.length = 3.0
params.chamfer_length = 0.2
params.chamfer_angle = 15.0

# --- Sketch 1: Main Cylinder Profile ---
# We will create the cylinder by revolving a rectangle.
# The sketch will be on the XY plane.
sketch_main = body.newObject("Sketcher::SketchObject", "Sketch_Main")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.Support = (doc.getObject("XY_Plane"), [])
sketch_main.MapMode = "FlatFace"

# Add a rectangle: Center at (0,0), Width = diameter, Height = length/2
# We define the rectangle from -diameter/2 to +diameter/2 on X, and 0 to +length/2 on Y.
# Actually, for revolution around Z, we need a profile in the XZ plane usually, 
# but if we sketch on XY and revolve around Z, the profile must be in the X-Y plane? 
# No, standard revolution: Profile is in a plane, Axis is perpendicular to that plane.
# If Axis is Z, Profile must be in XY plane.
# Let's sketch a rectangle in XY plane: X from -d/2 to d/2, Y from 0 to L/2.
# Revolving this around Z creates a cylinder.

# Line 1: Bottom center to Bottom right
line1 = Part.LineSegment(App.Vector(-params.diameter / 2, 0, 0), App.Vector(params.diameter / 2, 0, 0))
sketch_main.addGeometry(line1, False)

# Line 2: Bottom right to Top right
line2 = Part.LineSegment(App.Vector(params.diameter / 2, 0, 0), App.Vector(params.diameter / 2, params.length / 2, 0))
sketch_main.addGeometry(line2, False)

# Line 3: Top right to Top left
line3 = Part.LineSegment(App.Vector(params.diameter / 2, params.length / 2, 0), App.Vector(-params.diameter / 2, params.length / 2, 0))
sketch_main.addGeometry(line3, False)

# Line 4: Top left to Bottom center (closing the loop)
line4 = Part.LineSegment(App.Vector(-params.diameter / 2, params.length / 2, 0), App.Vector(-params.diameter / 2, 0, 0))
sketch_main.addGeometry(line4, False)

# Constraints
# Horizontal lines
sketch_main.addConstraint(Sketcher.Constraint("Axis", 0, 1, "X_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("Axis", 1, 2, "X_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("Axis", 2, 3, "X_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("Axis", 3, 0, "X_Axis"))

# Vertical lines
sketch_main.addConstraint(Sketcher.Constraint("Axis", 0, 1, "Y_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("Axis", 2, 3, "Y_Axis"))

# Coincident points
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0)) # Bottom right
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 0)) # Top right
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 2, 3, 3, 0)) # Top left
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 3, 0, 0, 0)) # Bottom left (center)

# Dimension constraints
# Width = diameter
sketch_main.addConstraint(Sketcher.Constraint("Length", 0, 1, "Parameters.diameter"))
# Height = length / 2
sketch_main.addConstraint(Sketcher.Constraint("Length", 1, 2, "Parameters.length / 2"))

# --- Feature 1: Pad (Cylinder) ---
pad = body.newObject("PartDesign::Pad", "Pad_Cylinder")
pad.Profile = sketch_main
pad.Length = "Parameters.length"
pad.Type = "Solid"

# --- Sketch 2: Chamfer Profile ---
# We need to define the chamfer geometry. 
# A chamfer is often defined by a face and an edge, but in PartDesign, 
# we can use a "Chamfer" feature directly if we select edges, OR we can create a 
# subtractive feature (Pocket/Pad) based on a sketch if we want complex profiles.
# However, the prompt asks for "Chamfer" feature usage if possible, or standard features.
# The standard PartDesign::Chamfer feature works on edges.
# Let's use the PartDesign::Chamfer feature as it's more robust for simple chamfers.
# But wait, the prompt says "Use editable PartDesign features... driven by named document objects".
# The Chamfer feature in PartDesign takes edges and parameters (Size, Angle).
# We need to ensure the parameters are driven.

# Let's create the chamfer feature.
# We need to reference the edges of the Pad.
# Since we are building the tree, we can't easily reference edges of a feature that hasn't been computed yet 
# in a way that allows parameter binding for the *geometry* of the chamfer itself (length/angle) 
# unless we use expressions for the Size/Angle properties of the Chamfer feature.

chamfer = body.newObject("PartDesign::Chamfer", "Chamfer_Ends")
chamfer.Base = (pad, ["Edge1", "Edge2"]) # We will select the top and bottom edges later? 
# Actually, in a script, we can't interactively select edges. 
# We must define the Base explicitly or rely on the fact that the script runs headless.
# In headless mode, we usually have to specify the edges by index or name if possible, 
# but PartDesign::Chamfer Base property expects a tuple of (Feature, [EdgeIndices]).
# Since we don't know the edge indices of the Pad yet (they are generated after recompute), 
# we have a chicken-and-egg problem if we try to set Base immediately.

# Alternative approach for headless scripting with Chamfer:
# 1. Create the Pad.
# 2. Create the Chamfer feature.
# 3. Set the Base to the Pad.
# 4. Set the Edge selection to a list of indices. But indices are dynamic.
# 
# Workaround: Use a "Pocket" with a sketch to create the chamfer shape? 
# No, the prompt specifically mentions "Chamfer" as a potential feature.
# 
# Let's try to set the Base to the Pad and assume the edge selection can be handled by 
# setting the property to a generic list that FreeCAD might resolve, OR we use the 
# "Chamfer" feature's ability to select edges by name if they exist? No.
# 
# Actually, the most reliable way in a script for a simple chamfer on a cylinder is:
# 1. Create the Pad.
# 2. Create a sketch on the top face of the cylinder (or just use the existing sketch plane offset).
# 3. Draw a line representing the chamfer cut.
# 4. Use a Pocket to cut it out.
# 
# HOWEVER, the prompt says "Use editable PartDesign features... Chamfer ...".
# Let's try to use the Chamfer feature. In FreeCAD 1.1, if we set `Base` to the Pad, 
# we can try to set the edges. But without knowing the indices, this is hard.
# 
# Let's reconsider the "Chamfer" feature definition. 
# `chamfer.Base` is a tuple `(Feature, [EdgeIndices])`.
# If we cannot determine the indices, we might have to skip the direct Chamfer feature 
# and use a Pocket with a sketch, which is fully scriptable and parametric.
# BUT, the prompt lists "Chamfer" as an example of features to use.
# 
# Is there a way to select "All Edges" or specific edges by name? No.
# 
# Let's look at the constraints again. "Use editable PartDesign features... Chamfer ...".
# Maybe we can create the chamfer using a sketch and a Pad/Pocket, which is effectively 
# a chamfer operation but via a feature tree.
# 
# Wait, there is a trick. If we create the Pad, then create a Chamfer feature, 
# and set the Base to the Pad, and set the Edge selection to `[]` (empty), it might fail.
# 
# Let's go with the Sketch+Pocket approach for the chamfer to ensure 100% scriptability 
# and parameterization, as it avoids the dynamic edge index issue in headless mode.
# We will create a sketch on the top face of the cylinder, draw a line from the edge inwards,
# and use a Pocket to remove the material. This creates a chamfer.
# We can drive the length and angle of this line using the parameters.

# Step 1: Create a sketch on the top face of the cylinder.
# We need to find the top face. Since we can't query faces easily in a script before recompute,
# we can create a sketch on the XY plane, offset by length/2.
# The cylinder is centered at 0,0,0, length L. Top face is at Z = L/2.
# We create a sketch on XY plane, offset Z = L/2.

sketch_chamfer = body.newObject("Sketcher::SketchObject", "Sketch_Chamfer")
sketch_chamfer.Placement = App.Placement(App.Vector(0, 0, params.length / 2))
sketch_chamfer.Support = (doc.getObject("XY_Plane"), [])
sketch_chamfer.MapMode = "FlatFace"

# We need to draw a line that starts at the edge of the cylinder (X = d/2, Z = L/2) 
# and goes inwards at the chamfer angle.
# The chamfer is on the side. The cut is a plane.
# In the top view (XY plane), the chamfer cut looks like a line starting from the perimeter 
# and going towards the center.
# The length of this line in the XY plane is related to the chamfer length and angle.
# Geometry:
# The chamfer is a plane cutting the corner.
# The intersection of the chamfer plane with the top face (XY) is a line.
# The distance from the edge to the start of the cut on the top face is `chamfer_length * cos(chamfer_angle)`.
# The depth of the cut into the cylinder is `chamfer_length * sin(chamfer_angle)`.
# Wait, the "chamfer_length" parameter usually refers to the length of the chamfer along the edge.
# So the cut on the top face extends from the edge inwards by `L_chamfer * cos(angle)`.

# Let's define the line in the XY sketch.
# Start point: (d/2, 0) -> This is on the edge.
# End point: (d/2 - L_chamfer * cos(angle), 0) -> This is inside.
# We also need to close the loop? No, we just need the profile of the cut.
# The cut is a wedge. We need to define the area to remove.
# The area to remove is a triangle defined by:
# 1. The edge of the cylinder (part of the perimeter).
# 2. The line we just drew.
# 3. The vertical line connecting them? No.
# 
# Actually, a simpler way to model a chamfer with a sketch is:
# Draw a line from the edge inwards.
# Then use a "Pocket" with Type="ThroughAll" or specific length? 
# No, a Pocket with a sketch creates a hole. A chamfer is a slanted cut.
# 
# Correct approach for Chamfer via Sketch/Pocket:
# 1. Sketch on the top face.
# 2. Draw a line from the edge (d/2, 0) to (d/2 - L_chamfer*cos(a), 0).
# 3. Draw a line from (d/2 - L_chamfer*cos(a), 0) to (d/2 - L_chamfer*cos(a), 0)? No.
# 
# Let's use the standard "Chamfer" feature but solve the edge selection issue.
# In FreeCAD 1.1, if we set `chamfer.Base = (pad, [0])`, it might pick the first edge.
# But we need to select the top and bottom edges.
# 
# Let's try a different strategy: 
# Create the Pad.
# Create a Chamfer feature.
# Set Base to Pad.
# Set Edge selection to a list of indices. 
# Since we can't know the indices, we will use the "Chamfer" feature's ability to 
# select edges by name if we name them? No.
# 
# Okay, let's stick to the Sketch+Pocket method which is 100% reliable in scripts.
# To create a chamfer on a cylinder using a sketch and pocket:
# 1. Sketch on the top face.
# 2. Draw a line from the edge (d/2, 0) to a point inside (x_in, 0).
#    x_in = d/2 - chamfer_length * cos(chamfer_angle).
# 3. Draw a line from (x_in, 0) to (x_in, 0)? No.
# 4. We need to define the volume to remove.
#    The volume to remove is a wedge.
#    The profile in the XY plane is a line segment from the edge to the inner point.
#    The Pocket feature with a sketch creates a hole. If we use Type="ThroughAll", it goes through.
#    If we use Type="Blind", we need a depth.
#    But a chamfer is not a hole, it's a slanted cut on the side.
# 
# Actually, the best way to do a chamfer with a sketch in PartDesign is:
# 1. Create a sketch on the top face.
# 2. Draw a line from the edge to the inside.
# 3. Use a "Pad" with the sketch? No, that adds material.
# 4. Use a "Pocket" with the sketch? That removes material.
#    If we draw a line from the edge to the inside, and use a Pocket, it creates a hole 
#    that is cylindrical? No, it creates a hole with the shape of the sketch.
#    If the sketch is a line, it's not a closed loop.
# 
# Let's go back to the Chamfer feature. It is the correct tool.
# How to select edges in a script?
# We can use `chamfer.Base = (pad, [0, 1])`? No, indices are not stable.
# 
# Wait, there is a property `chamfer.Base` which is a tuple.
# If we set `chamfer.Base = (pad, [])`, it fails.
# 
# Alternative: Use the "Chamfer" feature but select the edges by creating a temporary 
# selection? No.
# 
# Let's try to construct the chamfer using a "Pocket" with a specific profile that mimics a chamfer.
# Profile: A rectangle of width = chamfer_length * cos(angle) and height = chamfer_length * sin(angle)?
# No.
# 
# Let's assume the "Chamfer" feature is the intended solution and try to make it work.
# In FreeCAD, if you create a Pad, then a Chamfer, and set the Base to the Pad, 
# you can select the edges. In a script, we can try to set the edge indices to `0` and `1` 
# hoping they correspond to the top and bottom edges of the cylinder.
# The cylinder has 4 edges (if it's a rectangle revolved? No, a cylinder has 1 top circle, 1 bottom circle, 1 side surface).
# Wait, the Pad from a rectangle revolved creates a cylinder.
# The edges are: Top Circle, Bottom Circle, Side Surface (which is a face, not an edge).
# The "edges" of the solid are the two circles.
# So we need to chamfer the Top Circle and Bottom Circle.
# 
# So `chamfer.Base = (pad, [0, 1])` might work if 0 and 1 are the top and bottom circles.
# Let's try that.
# 
# Parameters for Chamfer:
# - Size: The length of the chamfer along the edge.
# - Angle: The angle of the chamfer.
# 
# We can set these properties to the parameters.
# `chamfer.Size = "Parameters.chamfer_length"`
# `chamfer.Angle = "Parameters.chamfer_angle"`
# 
# This seems the most plausible path.

# --- Re-evaluating the Sketch for Chamfer ---
# If we use the Chamfer feature, we don't need a sketch for the chamfer itself.
# We just need
