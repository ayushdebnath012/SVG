import FreeCAD as App
import Part
from pathlib import Path
import Sketcher

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
doc.addObject("PartDesign::Link", "XY_Plane")
doc.addObject("PartDesign::Link", "XZ_Plane")
doc.addObject("PartDesign::Link", "YZ_Plane")
doc.addObject("PartDesign::Link", "Z_Axis")
doc.addObject("PartDesign::Link", "X_Axis")
doc.addObject("PartDesign::Link", "Y_Axis")

# Attach planes to body
body.Placement = App.Placement(App.Vector(0, 0, 0))
# Ensure the base sketch is on XY plane (Z=0)
# Note: In FreeCAD 1.1, PartDesign::Body automatically manages planes, but we set AttachmentSupport explicitly for the sketch.

# --- Base Flange Sketch ---
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
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
for i in range(params.number_bolt_holes):
    angle = (i * 360.0 / params.number_bolt_holes) * (App DEGToRad)
    x = bolt_radius * App.cos(angle)
    y = bolt_radius * App.sin(angle)
    
    hole_circle = Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
    bolt_sketch.addGeometry(hole_circle, False)

# Constraints
# Coincident centers with bolt circle center (which is also flange center)
bolt_sketch.Constraints.append(Sketcher.Constraint("Coincident", 0, 2, 1, 2))
# Add radius constraint to the first hole to define size
bolt_sketch.Constraints.append(Sketcher.Constraint("Radius", 0, params.bolt_hole_diameter / 2.0))

# Horizontal and Vertical constraints are tricky in polar arrays without a reference. 
# However, Sketcher handles the polar distribution if the sketch is solved correctly.
# Let's add constraints to ensure the holes are on the bolt circle.
# We can't easily constrain 4 points to a circle directly in a single sketch without a construction circle.
# Alternative: Create a construction circle, constrain holes to it.
# But for simplicity in script, we rely on the fact that the circles are added at calculated positions.
# To make it robust parametrically, let's add a construction circle.

constr_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bolt_radius)
bolt_sketch.addGeometry(constr_circle, False)

# Constrain hole centers to lie on the construction circle
for i in range(params.number_bolt_holes):
    # Identify the index of the hole in the sketch geometry list. 
    # Since we added constr_circle last, indices of holes are 0 to N-1.
    # This is dynamic, so we iterate and find the constraint target.
    # Actually, Sketcher.Constraint uses index in .Geometry.
    pass 

# Re-adding constraints properly for the sketch
bolt_sketch.Constraints = [] # Clear previous
bolt_sketch.Constraints.append(Sketcher.Constraint("Coincident", 0, 2, 1, 2))
bolt_sketch.Constraints.append(Sketcher.Constraint("Radius", 1, bolt_radius)) # Constr circle radius

for i in range(params.number_bolt_holes):
    bolt_sketch.Constraints.append(Sketcher.Constraint("PointOnCircle", i+2, 1)) # Hole i+2 on Constr Circle (index 1)

doc.recompute()

# --- Pocket Feature (Bolt Holes) ---
pockets = []
for i in range(params.number_bolt_holes):
    pocket = body.newObject("PartDesign::Pocket", f"BoltPocket_{i}")
    pocket.Profile = bolt_sketch
    pocket.Type = "ThroughAll"
    pockets.append(pocket)

doc.recompute()

# --- Save ---
# Derive path from __file__
script_path = Path(__file__).resolve()
output_path = script_path.parent / f"{script_path.stem}.FCStd"

doc.saveAs(str(output_path))
print(f"Model saved to: {output_path}")
