import FreeCAD as App
import Part
from pathlib import Path
import Sketcher

# Create a new document
doc = App.newDocument("MG90_Servo_Mount_Base")

# Create the main body
body = doc.addObject("PartDesign::Body", "Body")

# Define named parameters for key dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "base_width", "Dimensions", "Base width")
params.base_width = 59.0

params.addProperty("App::PropertyLength", "base_height", "Dimensions", "Base height")
params.base_height = 27.0

params.addProperty("App::PropertyLength", "mount_height", "Dimensions", "Mount height")
params.mount_height = 37.0

params.addProperty("App::PropertyLength", "mount_width", "Dimensions", "Mount width")
params.mount_width = 30.0

params.addProperty("App::PropertyLength", "mount_thickness", "Dimensions", "Mount thickness")
params.mount_thickness = 3.5

params.addProperty("App::PropertyLength", "hole_diameter", "Dimensions", "Mount hole diameter")
params.hole_diameter = 3.8

params.addProperty("App::PropertyLength", "hole_spacing", "Dimensions", "Mount hole spacing")
params.hole_spacing = 24.5

params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Bore diameter")
params.bore_diameter = 2.0

params.addProperty("App::PropertyLength", "bore_depth", "Dimensions", "Bore depth")
params.bore_depth = 10.0

params.addProperty("App::PropertyLength", "bore_offset", "Dimensions", "Bore offset from edge")
params.bore_offset = 11.5

params.addProperty("App::PropertyLength", "fillet_radius", "Dimensions", "Fillet radius")
params.fillet_radius = 1.5

params.addProperty("App::PropertyLength", "chamfer_size", "Dimensions", "Chamfer size")
params.chamfer_size = 1.0

# Create the base sketch
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.Constraints = []
base_sketch.AddGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.base_width, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(params.base_width, 0, 0), App.Vector(params.base_width, params.base_height, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(params.base_width, params.base_height, 0), App.Vector(0, params.base_height, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(0, params.base_height, 0), App.Vector(0, 0, 0)), False)

# Add constraints to base sketch
base_sketch.AddConstraint(Sketcher.Constraint("Length", 0, 1, params.base_width), False)
base_sketch.AddConstraint(Sketcher.Constraint("Length", 1, 2, params.base_height), False)
base_sketch.AddConstraint(Sketcher.Constraint("Length", 2, 3, params.base_width), False)
base_sketch.AddConstraint(Sketcher.Constraint("Length", 3, 0, params.base_height), False)
base_sketch.AddConstraint(Sketcher.Constraint("Perpendicular", 0, 1, 1, 2), False)
base_sketch.AddConstraint(Sketcher.Constraint("Perpendicular", 1, 2, 2, 3), False)
base_sketch.AddConstraint(Sketcher.Constraint("Perpendicular", 2, 3, 3, 0), False)
base_sketch.AddConstraint(Sketcher.Constraint("Perpendicular", 3, 0, 0, 1), False)

# Create the mount sketch
mount_sketch = body.newObject("Sketcher::SketchObject", "MountSketch")
mount_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
mount_sketch.Constraints = []

# Mount base rectangle
mount_base = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.mount_width, 0, 0))
mount_sketch.AddGeometry(mount_base, False)
mount_base2 = Part.LineSegment(App.Vector(params.mount_width, 0, 0), App.Vector(params.mount_width, params.mount_thickness, 0))
mount_sketch.AddGeometry(mount_base2, False)
mount_base3 = Part.LineSegment(App.Vector(params.mount_width, params.mount_thickness, 0), App.Vector(0, params.mount_thickness, 0))
mount_sketch.AddGeometry(mount_base3, False)
mount_base4 = Part.LineSegment(App.Vector(0, params.mount_thickness, 0), App.Vector(0, 0, 0))
mount_sketch.AddGeometry(mount_base4, False)

# Mount top rectangle
mount_top = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.mount_width, 0, 0))
mount_sketch.AddGeometry(mount_top, False)
mount_top2 = Part.LineSegment(App.Vector(params.mount_width, 0, 0), App.Vector(params.mount_width, params.mount_height, 0))
mount_sketch.AddGeometry(mount_top2, False)
mount_top3 = Part.LineSegment(App.Vector(params.mount_width, params.mount_height, 0), App.Vector(0, params.mount_height, 0))
mount_sketch.AddGeometry(mount_top3, False)
mount_top4 = Part.LineSegment(App.Vector(0, params.mount_height, 0), App.Vector(0, 0, 0))
mount_sketch.AddGeometry(mount_top4, False)

# Mount hole
mount_hole = Part.Circle(App.Vector(params.mount_width/2, params.mount_height/2, 0), App.Vector(0, 0, 1), params.hole_diameter/2)
mount_sketch.AddGeometry(mount_hole, False)

# Add constraints to mount sketch
mount_sketch.AddConstraint(Sketcher.Constraint("Length", 0, 1, params.mount_width), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Length", 1, 2, params.mount_thickness), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Length", 2, 3, params.mount_width), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Length", 3, 0, params.mount_thickness), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Perpendicular", 0, 1, 1, 2), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Perpendicular", 1, 2, 2, 3), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Perpendicular", 2, 3, 3, 0), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Perpendicular", 3, 0, 0, 1), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Length", 0, 4, params.mount_width), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Length", 4, 5, params.mount_height), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Length", 5, 6, params.mount_width), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Length", 6, 0, params.mount_height), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Perpendicular", 0, 4, 4, 5), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Perpendicular", 4, 5, 5, 6), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Perpendicular", 5, 6, 6, 0), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Perpendicular", 6, 0, 0, 4), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Center", 7, 0, 0, 0), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Center", 7, 0, 0, 0), False)
mount_sketch.AddConstraint(Sketcher.Constraint("Radius", 7, params.hole_diameter/2), False)

# Create the bore sketch
bore_sketch = body.newObject("Sketcher::SketchObject", "BoreSketch")
bore_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
bore_sketch.Constraints = []

# Bore circle
bore_circle = Part.Circle(App.Vector(params.bore_offset, params.mount_height/2, 0), App.Vector(0, 0, 1), params.bore_diameter/2)
bore_sketch.AddGeometry(bore_circle, False)

# Add constraints to bore sketch
bore_sketch.AddConstraint(Sketcher.Constraint("Radius", 0, params.bore_diameter/2), False)
bore_sketch.AddConstraint(Sketcher.Constraint("DistanceX", 0, 0, params.bore_offset), False)
bore_sketch.AddConstraint(Sketcher.Constraint("DistanceY", 0, 0, params.mount_height/2), False)

# Create the main pad feature
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = base_sketch
pad.Length = params.mount_height
pad.Type = "Solid"
pad.Midplane = False
pad.Reversed = False

# Create the mount pad feature
mount_pad = body.newObject("PartDesign::Pad", "MountPad")
mount_pad.Profile = mount_sketch
mount_pad.Length = params.mount_thickness
mount_pad.Type = "Solid"
mount_pad.Midplane = False
mount_pad.Reversed = False

# Create the mount hole pocket feature
mount_hole_pocket = body.newObject("PartDesign::Pocket", "MountHolePocket")
mount_hole_pocket.Profile = mount_sketch
mount_hole_pocket.Type = "ThroughAll"
mount_hole_pocket.Type = "Blind"
mount_hole_pocket.Length = params.hole_diameter

# Create the bore pocket feature
bore_pocket = body.newObject("PartDesign::Pocket", "BorePocket")
bore_pocket.Profile = bore_sketch
bore_pocket.Type = "Blind"
bore_pocket.Length = params.bore_depth
bore_pocket.Type = "ThroughAll"

# Create the fillet feature
fillet = body.newObject("PartDesign::Fillet", "Fillet")
fillet.Base = (pad, ["Edge1"])
fillet.Radius = params.fillet_radius
fillet.Type = "Radius"

# Create the chamfer feature
chamfer = body.newObject("PartDesign::Chamfer", "Chamfer")
chamfer.Base = (pad, ["Edge1"])
chamfer.Size = params.chamfer_size
chamfer.Type = "Size"

# Recompute the document
doc.recompute()

# Save the document
doc.saveAs(str(Path(__file__).resolve().with_suffix(".FCStd")))
