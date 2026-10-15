import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("Bracket")

# Create the main body
body = doc.addObject("PartDesign::Body", "Body")

# Create a parameter set for dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "base_width", "Dimensions", "Base width")
params.base_width = 63.0
params.addProperty("App::PropertyLength", "base_height", "Dimensions", "Base height")
params.base_height = 55.0
params.addProperty("App::PropertyLength", "web_height", "Dimensions", "Web height")
params.web_height = 34.0
params.addProperty("App::PropertyLength", "web_width", "Dimensions", "Web width")
params.web_width = 4.0
params.addProperty("App::PropertyLength", "mounting_hole_dia", "Dimensions", "Mounting hole diameter")
params.mounting_hole_dia = 8.1
params.addProperty("App::PropertyLength", "mounting_hole_offset", "Dimensions", "Mounting hole offset from center")
params.mounting_hole_offset = 25.0
params.addProperty("App::PropertyLength", "top_flange_width", "Dimensions", "Top flange width")
params.top_flange_width = 50.0
params.addProperty("App::PropertyLength", "top_flange_height", "Dimensions", "Top flange height")
params.top_flange_height = 15.0
params.addProperty("App::PropertyLength", "top_flange_radius", "Dimensions", "Top flange corner radius")
params.top_flange_radius = 15.0
params.addProperty("App::PropertyLength", "top_flange_inner_radius", "Dimensions", "Top flange inner corner radius")
params.top_flange_inner_radius = 1.0
params.addProperty("App::PropertyLength", "top_flange_angle", "Dimensions", "Top flange angle")
params.top_flange_angle = 159.5
params.addProperty("App::PropertyLength", "fillet_radius", "Dimensions", "Fillet radius")
params.fillet_radius = 1.0
params.addProperty("App::PropertyLength", "chamfer_size", "Dimensions", "Chamfer size")
params.chamfer_size = 0.8
params.addProperty("App::PropertyLength", "web_chamfer_size", "Dimensions", "Web chamfer size")
params.web_chamfer_size = 0.8

# Create the base sketch (front view)
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.Constraints = []
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 0, 0), App.Vector(31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 0, 0), App.Vector(31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 55, 0), App.Vector(-31.5, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(31.5, 55, 0), App.Vector(-31.5, 55, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-31.5, 0, 0), App.Vector(3
