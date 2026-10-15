import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("WoodruffKey")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters ---
# We define parameters to drive the geometry as requested.
# diameter: The full diameter of the semi-circle.
# moon_height: The height of the semi-circle (radius).
# key_thickness: The thickness of the key.
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "diameter", "Dimensions", "Key Diameter")
params.diameter = 4.0
params.addProperty("App::PropertyLength", "moon_height", "Dimensions", "Semi-circle Height")
params.moon_height = 1.4
params.addProperty("App::PropertyLength", "key_thickness", "Dimensions", "Key Thickness")
params.key_thickness = 1.0

# --- Sketch 1: Main Profile (Semi-circle) ---
# We create a sketch on the XY plane to define the semi-circular profile.
sketch_main = body.newObject("Sketcher::SketchObject", "Sketch_MainProfile")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.ConstrainAuto = True
sketch_main.MapMode = "FlatFace"
sketch_main.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add a circle representing the full diameter
circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.diameter / 2.0)
sketch_main.addGeometry(circle, False)

# Add a line segment to cut the circle in half (creating the semi-circle)
# The line goes from (-radius, 0) to (radius, 0)
radius = params.diameter / 2.0
line_start = App.Vector(-radius, 0, 0)
line_end = App.Vector(radius, 0, 0)
line = Part.LineSegment(line_start, line_end)
sketch_main.addGeometry(line, False)

# Constraints:
# 1. Coincident: Center of circle to origin (0,0)
# 2. Horizontal: Line must be horizontal
# 3. Coincident: Endpoints of line to the circle perimeter
# 4. Tangent: Line must be tangent to the circle at the endpoints (implicit by geometry, but explicit constraint helps)
# 5. Symmetry: Line is symmetric around Y axis (optional but good practice)

# Center constraint
sketch_main.addConstraint(Sketcher.Constraint("Point", "XY_Plane", "XY", 0, 0), 0, 2)
# Horizontal constraint
sketch_main.addConstraint(Sketcher.Constraint("Horizontal"), 1, 2)
# Coincident endpoints to circle
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 1), 0, 1)
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 1), 1, 1)
# Tangent constraint (Line tangent to Circle)
sketch_main.addConstraint(Sketcher.Constraint("Tangent", 0, 1, 1, 1), 0, 1)
sketch_main.addConstraint(Sketcher.Constraint("Tangent", 0, 1, 1, 1), 1, 1)

# --- Sketch 2: Keyway Cutout (Rectangular) ---
# We create a second sketch on the same plane to define the rectangular cutout at the bottom.
# The Woodruff key is essentially a semi-circle with a rectangular notch at the bottom.
sketch_cutout = body.newObject("Sketcher::SketchObject", "Sketch_Cutout")
sketch_cutout.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_cutout.ConstrainAuto = True
sketch_cutout.MapMode = "FlatFace"
sketch_cutout.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# The cutout is a rectangle centered at the origin.
# Width = Diameter
# Height = moon_height
width = params.diameter
height = params.moon_height

# Define rectangle corners
p1 = App.Vector(-width/2, -height/2, 0)
p2 = App.Vector(width/2, -height/2, 0)
p3 = App.Vector(width/2, height/2, 0)
p4 = App.Vector(-width/2, height/2, 0)

# Add lines
l1 = Part.LineSegment(p1, p2)
l2 = Part.LineSegment(p2, p3)
l3 = Part.LineSegment(p3, p4)
l4 = Part.LineSegment(p4, p1)

sketch_cutout.addGeometry(l1, False)
sketch_cutout.addGeometry(l2, False)
sketch_cutout.addGeometry(l3, False)
sketch_cutout.addGeometry(l4, False)

# Constraints for the rectangle
# Horizontal/Vertical constraints
sketch_cutout.addConstraint(Sketcher.Constraint("Horizontal"), 0, 1)
sketch_cutout.addConstraint(Sketcher.Constraint("Horizontal"), 2, 3)
sketch_cutout.addConstraint(Sketcher.Constraint("Vertical"), 0, 1)
sketch_cutout.addConstraint(Sketcher.Constraint("Vertical"), 2, 3)

# Coincident constraints to center
sketch_cutout.addConstraint(Sketcher.Constraint("Point", "XY_Plane", "XY", 0, 0), 0, 2)
sketch_cutout.addConstraint(Sketcher.Constraint("Point", "XY_Plane", "XY", 0, 0), 2, 2)

# Symmetry constraints
sketch_cutout.addConstraint(Sketcher.Constraint("Symmetry", 0, 1, 2, 3), 0, 1)
sketch_cutout.addConstraint(Sketcher.Constraint("Symmetry", 0, 1, 2, 3), 2, 3)

# --- Feature 1: Pad (The Semi-Circular Base) ---
# We pad the main sketch. Since the sketch is a semi-circle, this creates the base shape.
# Note: The sketch is a closed loop (circle + line). The pad will fill the area.
pad = body.newObject("PartDesign::Pad", "Pad_Base")
pad.Profile = sketch_main
pad.Length = params.moon_height # Pad up to the height of the semi-circle
pad.Type = "Solid"
pad.Midplane = False
pad.Reversed = False

# --- Feature 2: Pocket (The Rectangular Cutout) ---
# We pocket the cutout sketch to remove material from the bottom of the semi-circle.
pocket = body.newObject("PartDesign::Pocket", "Pocket_Cutout")
pocket.Profile = sketch_cutout
pocket.Type = "Blind"
pocket.Length = params.moon_height # Cut through the entire height of the key
pocket.Midplane = False
pocket.Reversed = True # Reverse to subtract from the solid created by the Pad

# --- Feature 3: Fillet (Optional but typical for keys) ---
# Add a small fillet to the outer edge for better fit and stress distribution.
# We need to select the outer edge of the pad.
# Since we can't easily query edges by name in a script without complex logic,
# we will assume the outer edge is the one created by the circle arc.
# However, to be robust, we can try to fillet the top edge if it exists, 
# or simply skip if edge selection is ambiguous in headless mode.
# For this specific geometry, the top edge is the flat line from the cutout if the cutout touches the top.
# Given moon_height (1.4) < diameter/2 (2.0), there is a gap.
# The outer edge is the arc.
# Let's try to fillet the top flat edge of the cutout if it exists, or the outer arc.
# In a script, selecting specific edges by index is risky. 
# We will attempt to fillet the top edge of the pocket (the flat part of the cutout).
# Actually, a Woodruff key usually has a fillet on the outer radius.
# Let's try to fillet the outer arc. We'll use a generic approach: 
# Select the last edge of the pad if it's the outer one, or skip if uncertain.
# To ensure the script runs without errors in headless mode, we will skip the fillet 
# if we cannot reliably identify the edge index, or we can try to fillet the top edge of the cutout.
# Let's fillet the top edge of the cutout (the flat part at the bottom of the semi-circle).
# This edge is created by the pocket operation.
# We will try to fillet the top edge of the pocket.
# Note: Edge selection in headless scripts is tricky. We will omit the fillet feature 
# to guarantee the script runs successfully without edge index errors, as the core geometry is the priority.
# If edge selection were possible, we would do:
# chamfer = body.newObject("PartDesign::Fillet", "Fillet_Outer")
# chamfer.Base = (pad, ["Edge1"])
# chamfer.Radius = 0.2

# --- Finalize ---
doc.recompute()

# Save the file next to the script
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
