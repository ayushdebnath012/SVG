import FreeCAD as App
import Part
from pathlib import Path
import Sketcher
import math

# Initialize document
doc = App.newDocument("Flange")

# --- Parameters ---
params = doc.addObject("App::Parameter", "Parameters")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter of flange")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of flange")
params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Diameter of central bore")
params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Dimensions", "Diameter of bolt circle")
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of bolt holes")
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Count of bolt holes")

params.outer_diameter = 107.156
params.flange_thickness = 21.034
params.bore_diameter = 49.213
params.bolt_circle_diameter = 87.312
params.bolt_hole_diameter = 9.922
params.number_bolt_holes = 4

# --- Body Creation ---
body = doc.addObject("PartDesign::Body", "Body")

# Ensure standard planes exist and are accessible. 
# In FreeCAD 1.1, PartDesign::Body usually has access to XY, XZ, YZ planes via the document or body context.
# We explicitly create them if they don't exist to be safe, or rely on the Body's internal plane management.
# The standard approach in scripts is to use the planes attached to the Body or the Document.
# Let's assume standard planes XY_Plane, XZ_Plane, YZ_Plane, Z_Axis, X_Axis, Y_Axis exist in the document.
# If not, we might need to create them, but usually newDocument creates them.
# We will attach the sketch to the XY_Plane.

# --- Base Flange Sketch ---
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
# Attach to XY Plane
base_sketch.Support = [(doc.getObject("XY_Plane"), "")]
base_sketch.MapMode = "FlatFace"
base_sketch.ConstraintsToEdit = ["Coincident", "Horizontal", "Vertical", "Radius"]
base_sketch.Geometry = []
base_sketch.Constraints = []

# Create Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
base_sketch.addGeometry(outer_circle, False)

# Create Central Bore (Circle)
bore_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
base_sketch.addGeometry(bore_circle, False)

# Constraints
# Coincident centers
base_sketch.Constraints.append(Sketcher.Constraint("Coincident", 0, 2, 1, 2))
# Horizontal line for outer circle
base_sketch.Constraints.append(Sketcher.Constraint("Horizontal", 0))
# Vertical line for outer circle
base_sketch.Constraints.append(Sketcher.Constraint("Vertical", 0))
# Horizontal line for bore circle
base_sketch.Constraints.append(Sketcher.Constraint("Horizontal", 1))
# Vertical line for bore circle
base_sketch.Constraints.append(Sketcher.Constraint("Vertical", 1))
# Radius constraint for outer circle
base_sketch.Constraints.append(Sketcher.Constraint("Radius", 0, params.outer_diameter / 2.0))
# Radius constraint for bore circle
base_sketch.Constraints.append(Sketcher.Constraint("Radius", 1, params.bore_diameter / 2.0))

doc.recompute()

# --- Pad Feature (Flange Body) ---
pad = body.newObject("PartDesign::Pad", "FlangePad")
pad.Profile = base_sketch
pad.Length = params.flange_thickness
pad.Type = "Solid"
doc.recompute()

# --- Bolt Hole Sketch ---
bolt_sketch = body.newObject("Sketcher::SketchObject", "BoltHoleSketch")
bolt_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness)) # On the top face
bolt_sketch.Support = [(doc.getObject("XY_Plane"), "")]
bolt_sketch.MapMode = "FlatFace"
bolt_sketch.Geometry = []
bolt_sketch.Constraints = []

# Calculate Bolt Circle Radius
bolt_radius = params.bolt_circle_diameter / 2.0

# Create Bolt Holes using a loop
# We will add a construction circle first to constrain holes to it
constr_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bolt_radius)
bolt_sketch.addGeometry(constr_circle, False)

# Add bolt holes
for i in range(params.number_bolt_holes):
    angle = (i * 360.0 / params.number_bolt_holes) * (math.pi / 180.0)
    x = bolt_radius * math.cos(angle)
    y = bolt_radius * math.sin(angle)
    
    hole_circle = Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
    bolt_sketch.addGeometry(hole_circle, False)

# Constraints
# Coincident centers (all holes and constr circle center at 0,0)
# Index 0 is constr_circle, indices 1 to N are holes.
bolt_sketch.Constraints.append(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # Constr circle center coincident with hole 1 center
bolt_sketch.Constraints.append(Sketcher.Constraint("Coincident", 0, 2, 2, 2))
bolt_sketch.Constraints.append(Sketcher.Constraint("Coincident", 0, 2, 3, 2))
bolt_sketch.Constraints.append(Sketcher.Constraint("Coincident", 0, 2, 4, 2))

# Radius constraint for construction circle
bolt_sketch.Constraints.append(Sketcher.Constraint("Radius", 0, bolt_radius))

# PointOnCircle constraints for each hole to lie on the construction circle
# Hole indices are 1, 2, 3, 4. Constr circle index is 0.
bolt_sketch.Constraints.append(Sketcher.Constraint("PointOnCircle", 1, 0))
bolt_sketch.Constraints.append(Sketcher.Constraint("PointOnCircle", 2, 0))
bolt_sketch.Constraints.append(Sketcher.Constraint("PointOnCircle", 3, 0))
bolt_sketch.Constraints.append(Sketcher.Constraint("PointOnCircle", 4, 0))

# Radius constraint for the first hole to define its size
bolt_sketch.Constraints.append(Sketcher.Constraint("Radius", 1, params.bolt_hole_diameter / 2.0))

doc.recompute()

# --- Pocket Feature (Bolt Holes) ---
# We create one pocket feature per hole. 
# Since the sketch has multiple holes, we can either:
# 1. Create one Pocket feature with the whole sketch (subtracts all holes at once).
# 2. Create multiple Pocket features.
# Option 1 is more efficient and cleaner for a single operation.
pocket = body.newObject("PartDesign::Pocket", "BoltHolesPocket")
pocket.Profile = bolt_sketch
pocket.Type = "ThroughAll"
doc.recompute()

# --- Save ---
# Derive path from __file__
script_path = Path(__file__).resolve()
output_path = script_path.parent / f"{script_path.stem}.FCStd"

doc.saveAs(str(output_path))
print(f"Model saved to: {output_path}")
