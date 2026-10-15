import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create new document
doc = App.newDocument("SlottedChannelGuideBracket")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")

# Create named parameters for dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "total_length", "Dimensions", "Total length of the bracket")
params.total_length = 155.0

params.addProperty("App::PropertyLength", "main_height", "Dimensions", "Main body height")
params.main_height = 35.0

params.addProperty("App::PropertyLength", "web_thickness", "Dimensions", "Web thickness")
params.web_thickness = 1.5

params.addProperty("App::PropertyLength", "slot_width", "Dimensions", "Slot width")
params.slot_width = 12.0

params.addProperty("App::PropertyLength", "slot_depth", "Dimensions", "Slot depth")
params.slot_depth = 15.0

params.addProperty("App::PropertyLength", "slot_spacing", "Dimensions", "Slot spacing")
params.slot_spacing = 37.5

params.addProperty("App::PropertyLength", "flange_width", "Dimensions", "Flange width")
params.flange_width = 27.0

params.addProperty("App::PropertyLength", "flange_depth", "Dimensions", "Flange depth")
params.flange_depth = 18.0

params.addProperty("App::PropertyLength", "corner_radius", "Dimensions", "Corner radius")
params.corner_radius = 3.0

params.addProperty("App::PropertyLength", "fillet_radius", "Dimensions", "Fillet radius")
params.fillet_radius = 2.5

# Create base sketch on XY plane
sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.ConstrainAuto = True
sketch.ConstrainFully = True
sketch.MapMode = "FlatFace"
sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [""])

# Add geometry to base sketch
sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(155, 0, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(155, 0, 0), App.Vector(155, 35, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(155, 35, 0), App.Vector(0, 35, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(0, 35, 0), App.Vector(0, 0, 0)), False)

# Add fillets to base sketch
sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.corner_radius), False)
sketch.addGeometry(Part.Circle(App.Vector(155, 0, 0), App.Vector(0, 0, 1), params.corner_radius), False)
sketch.addGeometry(Part.Circle(App.Vector(0, 35, 0), App.Vector(0, 0, 1), params.corner_radius), False)
sketch.addGeometry(Part.Circle(App.Vector(155, 35, 0), App.Vector(0, 0, 1), params.corner_radius), False)

# Add constraints to base sketch
sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, params.total_length))
sketch.addConstraint(Sketcher.Constraint("Length", 1, 2, params.main_height))
sketch.addConstraint(Sketcher.Constraint("Length", 2, 3, params.total_length))
sketch.addConstraint(Sketcher.Constraint("Length", 3, 0, params.main_height))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 3))
sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 2))
sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))
sketch.addConstraint(Sketcher.Constraint("Radius", 4, 0, params.corner_radius))
sketch.addConstraint(Sketcher.Constraint("Radius", 5, 1, params.corner_radius))
sketch.addConstraint(Sketcher.Constraint("Radius", 6, 2, params.corner_radius))
sketch.addConstraint(Sketcher.Constraint("Radius", 7, 3, params.corner_radius))

# Create pad feature
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = sketch
pad.Length = params.main_height
pad.Type = "Solid"

# Create slot sketch
slot_sketch = body.newObject("Sketcher::SketchObject", "SlotSketch")
slot_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
slot_sketch.ConstrainAuto = True
slot_sketch.ConstrainFully = True
slot_sketch.MapMode = "FlatFace"
slot_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [""])

# Add slot geometry
slot_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.slot_width, 0, 0)), False)
slot_sketch.addGeometry(Part.LineSegment(App.Vector(params.slot_width, 0, 0), App.Vector(params.slot_width, params.slot_depth, 0)), False)
slot_sketch.addGeometry(Part.LineSegment(App.Vector(params.slot_width, params.slot_depth, 0), App.Vector(0, params.slot_depth, 0)), False)
slot_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.slot_depth, 0), App.Vector(0, 0, 0)), False)

# Add fillets to slot
slot_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.fillet_radius), False)
slot_sketch.addGeometry(Part.Circle(App.Vector(params.slot_width, 0, 0), App.Vector(0, 0, 1), params.fillet_radius), False)
slot_sketch.addGeometry(Part.Circle(App.Vector(0, params.slot_depth, 0), App.Vector(0, 0, 1), params.fillet_radius), False)
slot_sketch.addGeometry(Part.Circle(App.Vector(params.slot_width, params.slot_depth, 0), App.Vector(0, 0, 1), params.fillet_radius), False)

# Add constraints to slot sketch
slot_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, params.slot_width))
slot_sketch.addConstraint(Sketcher.Constraint("Length", 1, 2, params.slot_depth))
slot_sketch.addConstraint(Sketcher.Constraint("Length", 2, 3, params.slot_width))
slot_sketch.addConstraint(Sketcher.Constraint("Length", 3, 0, params.slot_depth))
slot_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
slot_sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 3))
slot_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 2))
slot_sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))
slot_sketch.addConstraint(Sketcher.Constraint("Radius", 4, 0, params.fillet_radius))
slot_sketch.addConstraint(Sketcher.Constraint("Radius", 5, 1, params.fillet_radius))
slot_sketch.addConstraint(Sketcher.Constraint("Radius", 6, 2, params.fillet_radius))
slot_sketch.addConstraint(Sketcher.Constraint("Radius", 7, 3, params.fillet_radius))

# Create pocket feature for slot
pocket = body.newObject("PartDesign::Pocket", "Pocket")
pocket.Profile = slot_sketch
pocket.Length = params.slot_depth
pocket.Type = "Blind"

# Create flange sketch
flange_sketch = body.newObject("Sketcher::SketchObject", "FlangeSketch")
flange_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
flange_sketch.ConstrainAuto = True
flange_sketch.ConstrainFully = True
flange_sketch.MapMode = "FlatFace"
flange_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [""])

# Add flange geometry
flange_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.flange_width, 0, 0)), False)
flange_sketch.addGeometry(Part.LineSegment(App.Vector(params.flange_width, 0, 0), App.Vector(params.flange_width, params.flange_depth, 0)), False)
flange_sketch.addGeometry(Part.LineSegment(App.Vector(params.flange_width, params.flange_depth, 0), App.Vector(0, params.flange_depth, 0)), False)
flange_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.flange_depth, 0), App.Vector(0, 0, 0)), False)

# Add fillets to flange
flange_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.corner_radius), False)
flange_sketch.addGeometry(Part.Circle(App.Vector(params.flange_width, 0, 0), App.Vector(0, 0, 1), params.corner_radius), False)
flange_sketch.addGeometry(Part.Circle(App.Vector(0, params.flange_depth, 0), App.Vector(0, 0, 1), params.corner_radius), False)
flange_sketch.addGeometry(Part.Circle(App.Vector(params.flange_width, params.flange_depth, 0), App.Vector(0, 0, 1), params.corner_radius), False)

# Add constraints to flange sketch
flange_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, params.flange_width))
flange_sketch.addConstraint(Sketcher.Constraint("Length", 1, 2, params.flange_depth))
flange_sketch.addConstraint(Sketcher.Constraint("Length", 2, 3, params.flange_width))
flange_sketch.addConstraint(Sketcher.Constraint("Length", 3, 0, params.flange_depth))
flange_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
flange_sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 3))
flange_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 2))
flange_sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))
flange_sketch.addConstraint(Sketcher.Constraint("Radius", 4, 0, params.corner_radius))
flange_sketch.addConstraint(Sketcher.Constraint("Radius", 5, 1, params.corner_radius))
flange_sketch.addConstraint(Sketcher.Constraint("Radius", 6, 2, params.corner_radius))
flange_sketch.addConstraint(Sketcher.Constraint("Radius", 7, 3, params.corner_radius))

# Create pad feature for flange
flange_pad = body.newObject("PartDesign::Pad", "FlangePad")
flange_pad.Profile = flange_sketch
flange_pad.Length = params.flange_depth
flange_pad.Type = "Solid"

# Create web sketch
web_sketch = body.newObject("Sketcher::SketchObject", "WebSketch")
web_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
web_sketch.ConstrainAuto = True
web_sketch.ConstrainFully = True
web_sketch.MapMode = "FlatFace"
web_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [""])

# Add web geometry
web_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.web_thickness, 0, 0)), False)
web_sketch.addGeometry(Part.LineSegment(App.Vector(params.web_thickness, 0, 0), App.Vector(params.web_thickness, params.main_height - params.flange_depth, 0)), False)
web_sketch.addGeometry(Part.LineSegment(App.Vector(params.web_thickness, params.main_height - params.flange_depth, 0), App.Vector(0, params.main_height - params.flange_depth, 0)), False)
web_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.main_height - params.flange_depth, 0), App.Vector(0, 0, 0)), False)

# Add fillets to web
web_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.corner_radius), False)
web_sketch.addGeometry(Part.Circle(App.Vector(params.web_thickness, 0, 0), App.Vector(0, 0, 1), params.corner_radius), False)
web_sketch.addGeometry(Part.Circle(App.Vector(0, params.main_height - params.flange_depth, 0), App.Vector(0, 0, 1), params.corner_radius), False)
web_sketch.addGeometry(Part.Circle(App.Vector(params.web_thickness, params.main_height - params.flange_depth, 0), App.Vector(0, 0, 1), params.corner_radius), False)

# Add constraints to web sketch
web_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, params.web_thickness))
web_sketch.addConstraint(Sketcher.Constraint("Length", 1, 2, params.main_height - params.flange_depth))
web_sketch.addConstraint(Sketcher.Constraint("Length", 2, 3, params.web_thickness))
web_sketch.addConstraint(Sketcher.Constraint("Length", 3, 0, params.main_height - params.flange_depth))
web_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
web_sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 3))
web_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 2))
web_sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))
web_sketch.addConstraint(Sketcher.Constraint("Radius", 4, 0, params.corner_radius))
web_sketch.addConstraint(Sketcher.Constraint("Radius", 5, 1, params.corner_radius))
web_sketch.addConstraint(Sketcher.Constraint("Radius", 6, 2, params.corner_radius))
web_sketch.addConstraint(Sketcher.Constraint("Radius", 7, 3, params.corner_radius))

# Create pad feature for web
web_pad = body.newObject("PartDesign::Pad", "WebPad")
web_pad.Profile = web_sketch
web_pad.Length = params.main_height - params.flange_depth
web_pad.Type = "Solid"

# Create chamfer feature
chamfer = body.newObject("PartDesign::Chamfer", "Chamfer")
chamfer.Base = (pad, ["Edge1"])
chamfer.Size = params.fillet_radius
chamfer.Type = "Linear"

# Recompute the document
doc.recompute()

# Save the document
doc.saveAs(str(Path(__file__).resolve().with_name("answer.FCStd")))
