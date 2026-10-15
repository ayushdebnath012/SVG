import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("HeadlessPin")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create a VarSet to hold parameters for easy editing
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "diameter", "Dimensions", "Pin diameter")
params.addProperty("App::PropertyLength", "length", "Dimensions", "Pin length")
params.addProperty("App::PropertyLength", "chamfer_length", "Dimensions", "Chamfer length")
params.addProperty("App::PropertyAngle", "chamfer_angle", "Dimensions", "Chamfer angle")

# Set default values based on requirements
params.diameter = 3.0
params.length = 6.0
params.chamfer_length = 1.0
params.chamfer_angle = 30.0

# Create the base sketch on the XY plane
sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch.MapMode = "FlatFace"
sketch.ConstrainAuto = False
sketch.ConstrainFully = True

# Add a circle for the pin profile
circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.diameter)
sketch.addGeometry(circle, False)

# Add constraints to center the circle
# Constraint: Center of circle to origin (0,0)
# We use the "Center" constraint type which constrains the center of the circle to the origin
sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))

# Create the Pad feature to extrude the pin
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = sketch
pad.Length = params.length
pad.Type = "Solid"
pad.Reversed = False
pad.MidPlane = False

# Create a second sketch for the chamfer on the top face of the pad
# We need to reference the top face of the pad
chamfer_sketch = body.newObject("Sketcher::SketchObject", "ChamferSketch")
chamfer_sketch.Placement = App.Placement(App.Vector(0, 0, params.length))
chamfer_sketch.AttachmentSupport = (pad, ["Top"])
chamfer_sketch.MapMode = "FlatFace"
chamfer_sketch.ConstrainAuto = False
chamfer_sketch.ConstrainFully = True

# Add a line for the chamfer profile
# The line starts at the center and goes out to the chamfer length
line_start = App.Vector(0, 0, 0)
line_end = App.Vector(params.chamfer_length, 0, 0)
line = Part.LineSegment(line_start, line_end)
chamfer_sketch.addGeometry(line, False)

# Add constraints for the chamfer sketch
# 1. Center the line start at the origin
chamfer_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
# 2. Fix the length of the line
chamfer_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, params.chamfer_length))
# 3. Fix the angle of the line (30 degrees)
chamfer_sketch.addConstraint(Sketcher.Constraint("Angle", 0, 1, params.chamfer_angle))

# Create the Chamfer feature
chamfer = body.newObject("PartDesign::Chamfer", "Chamfer")
chamfer.Profile = chamfer_sketch
chamfer.Type = "ThroughAll"
chamfer.Base = (pad, ["Top"])
chamfer.Method = "Angle"

# Force recompute to ensure all features are calculated
doc.recompute()

# Save the document to the specified path derived from __file__
output_path = Path(__file__).resolve().with_suffix(".FCStd")
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
