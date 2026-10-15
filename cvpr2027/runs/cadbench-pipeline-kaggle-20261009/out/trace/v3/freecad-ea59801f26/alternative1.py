Looking at the engineering drawing, I need to create a triangulated clevis mount bracket. Let me analyze the geometry and dimensions:

The part has:
1. A main body with complex geometry
2. Multiple holes and pockets
3. Angled features with 45° angles
4. Fillets and chamfers
5. Various cylindrical features

I'll create a comprehensive script that builds this part using PartDesign features with proper sketches.

```python
from pathlib import Path
import FreeCAD as App, Part, Sketcher
import math

# Create document
doc = App.newDocument("TriangulatedClevisMountBracket")

# Create body
body = doc.addObject("PartDesign::Body", "Body")

# Add parameters for key dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "main_width", "Dimensions", "main width")
params.main_width = 18.0
params.addProperty("App::PropertyLength", "main_height", "Dimensions", "main height")
params.main_height = 85.74
params.addProperty("App::PropertyLength", "base_width", "Dimensions", "base width")
params.base_width = 17.05
params.addProperty("App::PropertyLength", "base_height", "Dimensions", "base height")
params.base_height = 4.0
params.addProperty("App::PropertyLength", "flange_height", "Dimensions", "flange height")
params.flange_height = 4.5
params.addProperty("App::PropertyLength", "thickness", "Dimensions", "thickness")
params.thickness = 1.0
params.addProperty("App::PropertyLength", "fillet_radius", "Dimensions", "fillet radius")
params.fillet_radius = 2.0
params.addProperty("App::PropertyLength", "hole_d1", "Dimensions", "hole diameter 1")
params.hole_d1 = 2.5
params.addProperty("App::PropertyLength", "hole_d2", "Dimensions", "hole diameter 2")
params.hole_d2 = 3.0
params.addProperty("App::PropertyLength", "hole_d3", "Dimensions", "hole diameter 3")
params.hole_d3 = 2.5
params.addProperty("App::PropertyLength", "hole_d4", "Dimensions", "hole diameter 4")
params.hole_d4 = 2.2
params.addProperty("App::PropertyLength", "distance_x1", "Dimensions", "distance x1")
params.distance_x1 = 14.07
params.addProperty("App::PropertyLength", "distance_x2", "Dimensions", "distance x2")
params.distance_x2 = 72.56
params.addProperty("App::PropertyLength", "distance_y1", "Dimensions", "distance y1")
params.distance_y1 = 3.0
params.addProperty("App::PropertyLength", "distance_y2", "Dimensions", "distance y2")
params.distance_y2 = 12.0
params.addProperty("App::PropertyLength", "base_hole_d1", "Dimensions", "base hole diameter 1")
params.base_hole_d1 = 2.3
params.addProperty("App::PropertyLength", "base_hole_d2", "Dimensions", "base hole diameter 2")
params.base_hole_d2 = 3.1
params.addProperty("App::PropertyLength", "flange_hole_d1", "Dimensions", "flange hole diameter 1")
params.flange_hole_d1 = 2.2
params.addProperty("App::PropertyLength", "flange_hole_d2", "Dimensions", "flange hole diameter 2")
params.flange_hole_d2 = 3.0
params.addProperty("App::PropertyLength", "offset_x", "Dimensions", "offset x")
params.offset_x = 4.5
params.addProperty("App::PropertyLength", "offset_y", "Dimensions", "offset y")
params.offset_y = 4.07
params.addProperty("App::PropertyLength", "flange_width", "Dimensions", "flange width")
params.flange_width = 13.24
params.addProperty("App::PropertyLength", "flange_height2", "Dimensions", "flange height 2")
params.flange_height2 = 3.34
params.addProperty("App::PropertyLength", "flange_diameter", "Dimensions", "flange diameter")
params.flange_diameter = 4.76
params.addProperty("App::PropertyLength", "flange_hole_d3", "Dimensions", "flange hole diameter 3")
params.flange_hole_d3 = 2.56
params.addProperty("App::PropertyLength", "flange_hole_d4", "Dimensions", "flange hole diameter 4")
params.flange_hole_d4 = 4.5
params.addProperty("App::PropertyLength", "base_hole_d3", "Dimensions", "base hole diameter 3")
params.base_hole_d3 = 2.5

# Create planes
XY_Plane = doc.addObject("PartDesign::Plane", "XY_Plane")
XY_Plane.Placement = App.Placement(App.Vector(0, 0, 0))
body.Placement = App.Placement(App.Vector(0, 0, 0))
XY_Place = doc.addObject("PartDesign::Plane", "XZ_Plane")
XZ_Place.Placement = App.Placement(App.Vector(0, 0, 0))
body.Placement = App.Placement(App.Vector(0, 0, 0))
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create base sketch for main body
sketch1 = body.newObject("Sketcher::SketchObject", "Sketch_Base")
sketch1.Placement = App.Placement(App.Vector(0, 0, 0))
sketch1.ConstrainAuto = True
sketch1.TangentConstraint = True
sketch1.Closed = True

# Create base profile
# Main body outline
line1 = sketch1.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.main_width, 0, 0)), False)
line2 = sketch1.addGeometry(Part.LineSegment(App.Vector(params.main_width, 0, 0), App.Vector(params.main_width, params.main_height, 0)), False)
line3 = sketch1.addGeometry(Part.LineSegment(App.Vector(params.main_width, params.main_height, 0), App.Vector(0, params.main_height, 0)), False)
line4 = sketch1.addGeometry(Part.LineSegment(App.Vector(0, params.main_height, 0), App.Vector(0, 0, 0)), False)

# Add constraints
sketch1.addConstraint(Sketcher.Constraint("Equality", line1, line2, 1, 2))
sketch1.addConstraint(Sketcher.Constraint("Vertical", line1, line2, 1, 2))
sketch1.addConstraint(Sketcher.Constraint("Horizontal", line2, line3, 1, 2))
sketch1.addConstraint(Sketcher.Constraint("Vertical", line3, line4, 1, 2))
sketch1.addConstraint(Sketcher.Constraint("Horizontal", line4, line1, 1, 2))

# Pad the base
pad_base = body.newObject("PartDesign::Pad", "Pad_Base")
pad_base.Profile = sketch1
pad_base.Length = params.thickness
pad_base.Midplane = True

# Create base pocket sketch
sketch2 = body.newObject("Sketcher::SketchObject", "Sketch_BasePocket")
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.ConstrainAuto = True
sketch2.TangentConstraint = True
sketch2.Closed = True

# Base pocket - through hole
circle1 = sketch2.addGeometry(Part.Circle(App.Vector(params.main_width/2, params.main_height/2, 0), App.Vector(0, 0, 1), params.hole_d1/2), False)

# Add constraints
sketch2.addConstraint(Sketcher.Constraint("Center", circle1, 1, 1))

# Pocket through
pocket_base = body.newObject("PartDesign::Pocket", "Pocket_Base")
pocket_base.Profile = sketch2
pocket_base.Type = "ThroughAll"

# Create angled feature sketch
sketch3 = body.newObject("Sketcher::SketchObject", "Sketch_Angle")
sketch3.Placement = App.Placement(App.Vector(params.main_width/2, params.main_height/2, 0))
sketch3.ConstrainAuto = True
sketch3.TangentConstraint = True
sketch3.Closed = True

# Create angled profile
# Left angled edge
line_angled1 = sketch3.addGeometry(Part.LineSegment(App.Vector(-params.main_width/2 + params.offset_x, params.main_height/2, 0), App.Vector(-params.main_width/2 + params.offset_x, params.main_height/2 + params.base_height, 0)), False)
line_angled2 = sketch3.addGeometry(Part.LineSegment(App.Vector(-params.main_width/2 + params.offset_x, params.main_height/2 + params.base_height, 0), App.Vector(-params.main_width/2 + params.offset_x + params.base_height, params.main_height/2 + params.base_height, 0)), False)
line_angled3 = sketch3.addGeometry(Part.LineSegment(App.Vector(-params.main_width/2 + params.offset_x + params.base_height, params.main_height/2 + params.base_height, 0), App.Vector(-params.main_width/2 + params.offset_x, params.main_height/2 + params.base_height + params.base_height, 0)), False)
line_angled4 = sketch3.addGeometry(Part.LineSegment(App.Vector(-params.main_width/2 + params.offset_x, params.main_height/2 + params.base_height + params.base_height, 0), App.Vector(-params.main_width/2 + params.offset_x, params.main_height/2, 0)), False)

# Add constraints
sketch3.addConstraint(Sketcher.Constraint("Length", line_angled1, 1, 2))
sketch3.addConstraint(Sketcher.Constraint("Length", line_angled2, 1, 2))
sketch3.addConstraint(Sketcher.Constraint("Length", line_angled3, 1, 2))
sketch3.addConstraint(Sketcher.Constraint("Length", line_angled4, 1, 2))

# Create fillet
fillet_angled = body.newObject("PartDesign::Fillet", "Fillet_Angled")
fillet_angled.Profile = sketch3
fillet_angled.Radius = params.fillet_radius

# Create base holes
sketch4 = body.newObject("Sketcher::SketchObject", "Sketch_BaseHoles")
sketch4.Placement = App.Placement(App.Vector(0, 0, 0))
sketch4.ConstrainAuto = True
sketch4.TangentConstraint = True
sketch4.Closed = True

# Base holes
hole1 = sketch4.addGeometry(Part.Circle(App.Vector(params.main_width/2 - params.distance_x1/2, params.main_height/2, 0), App.Vector(0, 0, 1), params.hole_d1/2), False)
hole2 = sketch4.addGeometry(Part.Circle(App.Vector(params.main_width/2 + params.distance_x1/2, params.main_height/2, 0), App.Vector(0, 0, 1), params.hole_d1/2), False)

# Add constraints
sketch4.addConstraint(Sketcher.Constraint("Center", hole1, 1, 1))
sketch4.addConstraint(Sketcher.Constraint("Center", hole2, 1, 1))
sketch4.addConstraint(Sketcher.Constraint("Distance", hole1, hole2, 1, 2, params.distance_x1))

# Pocket base holes
pocket_holes = body.newObject("PartDesign::Pocket", "Pocket_BaseHoles")
pocket_holes.Profile = sketch4
pocket_holes.Type = "ThroughAll"
pocket_holes.Type = "ThroughAll"

# Create flange sketch
sketch5 = body.newObject("Sketcher::SketchObject", "Sketch_Flange")
sketch5.Placement = App.Placement(App.Vector(params.main_width/2, params.main_height/2, 0))
sketch5.ConstrainAuto = True
sketch5.TangentConstraint = True
sketch5.Closed = True

# Flange profile
flange_circle = sketch5.addGeometry(Part.Circle(App.Vector(params.main_width/2, params.main_height/2 + params.flange_height, 0), App.Vector(0, 0, 1), params.flange_width/2), False)
flange_rect1 = sketch5.addGeometry(Part.LineSegment(App.Vector(params.main_width/2 - params.flange_width/2, params.main_height/2 + params.flange_height, 0), App.Vector(params.main_width/2 - params.flange_width/2, params.main_height/2 + params.flange_height + params.flange_height2, 0)), False)
flange_rect2 = sketch5.addGeometry(Part.LineSegment(App.Vector(params.main_width/2 - params.flange_width/2, params.main_height/2 + params.flange_height + params.flange_height2, 0), App.Vector(params.main_width/2 + params.flange_width/2, params.main_height/2 + params.flange_height + params.flange_height2, 0)), False)
flange_rect3 = sketch5.addGeometry(Part.LineSegment(App.Vector(params.main_width/2 + params.flange_width/2, params.main_height/2 + params.flange_height + params.flange_height2, 0), App.Vector(params.main_width/2 + params.flange_width/2, params.main_height/2 + params.flange_height, 0)), False)
flange_rect4 = sketch5.addGeometry(Part.LineSegment(App.Vector(params.main_width/2 + params.flange_width/2, params.main_height/2 + params.flange_height, 0), App.Vector(params.main_width/2 - params.flange_width/2, params.main_height/2 + params.flange_height, 0)), False)

# Add constraints
sketch5.addConstraint(Sketcher.Constraint("Center", flange_circle, 1, 1))
sketch5.addConstraint(Sketcher.Constraint("Vertical", flange_rect1, flange_rect2, 1, 2))
sketch5.addConstraint(Sketcher.Constraint("Horizontal", flange_rect2, flange_rect3, 1, 2))

# Pad flange
pad_flange = body.newObject("PartDesign::Pad", "Pad_Flange")
pad_flange.Profile = sketch5
pad_flange.Length = params.flange_height2
pad_flange.Midplane = True

# Create flange holes
sketch6 = body.newObject("Sketcher::SketchObject", "Sketch_FlangeHoles")
sketch6.Placement = App.Placement(App.Vector(params.main_width/2, params.main_height/2 + params.flange_height, 0))
sketch6.ConstrainAuto = True
sketch6.TangentConstraint = True
sketch6.Closed = True

# Flange holes
hole3 = sketch6.addGeometry(Part.Circle(App.Vector(params.main_width/2, params.main_height/2 + params.flange_height + params.flange_height2/2, 0), App.Vector(0, 0, 1), params.flange_hole_d1/2), False)
hole4 = sketch6.addGeometry(Part.Circle(App.Vector(params.main_width/2 + params.offset_x, params.main_height/2 + params.flange_height + params.flange_height2/2, 0), App.Vector(0, 0, 1), params.flange_hole_d2/2), False)
hole5 = sketch6.addGeometry(Part.Circle(App.Vector(params.main_width/2 - params.offset_x, params.main_height/2 + params.flange_height + params.flange_height2/2, 0), App.Vector(0, 0, 1), params.flange_hole_d2/2), False)

# Add constraints
sketch6.addConstraint(Sketcher.Constraint("Center", hole3, 1, 1))
sketch6.addConstraint(Sketcher.Constraint("Center", hole4, 1, 1))
sketch6.addConstraint(Sketcher.Constraint("Center", hole5, 1, 1))

# Pocket flange holes
pocket_flange_holes = body.newObject("PartDesign::Pocket", "Pocket_FlangeHoles")
pocket_flange_holes.Profile = sketch6
pocket_flange_holes.Type = "ThroughAll"

# Create bottom base holes
sketch7 = body.newObject("Sketcher::SketchObject", "Sketch_BottomHoles")
sketch7.Placement = App.Placement(App.Vector(0, 0, 0))
sketch7.ConstrainAuto = True
sketch7.TangentConstraint = True
sketch7.Closed = True

# Bottom holes
hole6 = sketch7.addGeometry(Part.Circle(App.Vector(params.main_width/2, params.main_height/2 - params.distance_y2/2, 0), App.Vector(0, 0, 1), params.base_hole_d1/2), False)
hole7 = sketch7.addGeometry(Part.Circle(App.Vector(params.main_width/2 + params.distance_y2/2, params.main_height/2 - params.distance_y2/2, 0), App.Vector(0, 0, 1), params.base_hole_d2/2), False)
hole8 = sketch7.addGeometry(Part.Circle(App.Vector(params.main_width/2 - params.distance_y2/2, params.main_height/2 - params.distance_y2/2, 0), App.Vector(0, 0, 1), params.base_hole_d2/2), False)

# Add constraints
sketch7.addConstraint(Sketcher.Constraint("Center", hole6, 1, 1))
sketch7.addConstraint(Sketcher.Constraint("Center", hole7, 1, 1))
sketch7.addConstraint(Sketcher.Constraint("Center", hole8, 1, 1))

# Pocket bottom holes
pocket_bottom_holes = body.newObject("PartDesign::Pocket", "Pocket_BottomHoles")
pocket_bottom_holes.Profile = sketch7
pocket_bottom_holes.Type = "ThroughAll"
