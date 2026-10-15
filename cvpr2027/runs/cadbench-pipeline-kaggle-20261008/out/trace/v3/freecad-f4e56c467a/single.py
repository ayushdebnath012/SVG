import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("DoubleClevisMountBase")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters ---
# Extracted from drawing:
# Overall Length: 170
# Overall Width: 110
# Base Thickness: 20
# Mount Height: 85
# Clevis Width: 95.78
# Clevis Height: 60
# Clevis Radius: 25
# Clevis Hole Diameter: 25
# Clevis Angle: 53.1
# Base Groove Width: 55
# Base Groove Radius: 30
# Base Groove Radius 2: 8
# Base Groove Radius 3: 3
# Base Groove Radius 4: 16
# Base Groove Radius 5: 26
# Base Groove Radius 6: 130 (Distance between centers)
# Base Groove Radius 7: 170 (Overall length)
# Base Groove Radius 8: 34.2 (Angle)
# Base Groove Radius 9: 34.1 (Angle)
# Base Groove Radius 10: 110 (Diameter)
# Base Groove Radius 11: 8 (Diameter)
# Base Groove Radius 12: 50 (Diameter)
# Base Groove Radius 13: 2xR30 (Radius)
# Base Groove Radius 14: 2xR8 (Radius)
# Base Groove Radius 15: 4xR3 (Radius)
# Base Groove Radius 16: 2x16 (Radius)
# Base Groove Radius 17: 2x26 (Radius)

params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "Length", "Dimensions", "Overall Length")
params.Length = 170.0

params.addProperty("App::PropertyLength", "Width", "Dimensions", "Overall Width")
params.Width = 110.0

params.addProperty("App::PropertyLength", "BaseThickness", "Dimensions", "Base Thickness")
params.BaseThickness = 20.0

params.addProperty("App::PropertyLength", "MountHeight", "Dimensions", "Mount Height")
params.MountHeight = 85.0

params.addProperty("App::PropertyLength", "ClevisWidth", "Dimensions", "Clevis Width")
params.ClevisWidth = 95.78

params.addProperty("App::PropertyLength", "ClevisHeight", "Dimensions", "Clevis Height")
params.ClevisHeight = 60.0

params.addProperty("App::PropertyLength", "ClevisRadius", "Dimensions", "Clevis Radius")
params.ClevisRadius = 25.0

params.addProperty("App::PropertyLength", "ClevisHoleDiameter", "Dimensions", "Clevis Hole Diameter")
params.ClevisHoleDiameter = 25.0

params.addProperty("App::PropertyLength", "ClevisAngle", "Dimensions", "Clevis Angle")
params.ClevisAngle = 53.1

params.addProperty("App::PropertyLength", "BaseGrooveWidth", "Dimensions", "Base Groove Width")
params.BaseGrooveWidth = 55.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius1", "Dimensions", "Base Groove Radius 1")
params.BaseGrooveRadius1 = 30.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius2", "Dimensions", "Base Groove Radius 2")
params.BaseGrooveRadius2 = 8.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius3", "Dimensions", "Base Groove Radius 3")
params.BaseGrooveRadius3 = 3.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius4", "Dimensions", "Base Groove Radius 4")
params.BaseGrooveRadius4 = 16.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius5", "Dimensions", "Base Groove Radius 5")
params.BaseGrooveRadius5 = 26.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius6", "Dimensions", "Base Groove Radius 6")
params.BaseGrooveRadius6 = 130.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius7", "Dimensions", "Base Groove Radius 7")
params.BaseGrooveRadius7 = 170.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius8", "Dimensions", "Base Groove Radius 8")
params.BaseGrooveRadius8 = 34.2

params.addProperty("App::PropertyLength", "BaseGrooveRadius9", "Dimensions", "Base Groove Radius 9")
params.BaseGrooveRadius9 = 34.1

params.addProperty("App::PropertyLength", "BaseGrooveRadius10", "Dimensions", "Base Groove Radius 10")
params.BaseGrooveRadius10 = 110.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius11", "Dimensions", "Base Groove Radius 11")
params.BaseGrooveRadius11 = 8.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius12", "Dimensions", "Base Groove Radius 12")
params.BaseGrooveRadius12 = 50.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius13", "Dimensions", "Base Groove Radius 13")
params.BaseGrooveRadius13 = 30.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius14", "Dimensions", "Base Groove Radius 14")
params.BaseGrooveRadius14 = 8.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius15", "Dimensions", "Base Groove Radius 15")
params.BaseGrooveRadius15 = 3.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius16", "Dimensions", "Base Groove Radius 16")
params.BaseGrooveRadius16 = 16.0

params.addProperty("App::PropertyLength", "BaseGrooveRadius17", "Dimensions", "Base Groove Radius 17")
params.BaseGrooveRadius17 = 26.0

# --- Base Sketch ---
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.Constraints = []
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-params.Length/2, 0, 0), App.Vector(params.Length/2, 0, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(params.Length/2, 0, 0), App.Vector(params.Length/2, params.Width/2, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(params.Length/2, params.Width/2, 0), App.Vector(-params.Length/2, params.Width/2, 0)), False)
base_sketch.AddGeometry(Part.LineSegment(App.Vector(-params.Length/2, params.Width/2, 0), App.Vector(-params.Length/2, 0, 0)), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius10/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius12/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius11/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius13/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius14/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius15/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius16/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius17/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius6/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius7/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius8/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius9/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius5/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius4/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius3/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius2/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius1/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius10/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius12/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius11/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius13/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius14/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius15/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius16/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius17/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius6/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius7/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius8/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius9/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius5/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius4/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius3/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius2/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius1/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius10/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius12/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius11/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius13/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius14/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius15/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius16/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius17/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius6/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius7/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius8/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius9/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius5/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius4/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius3/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius2/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius1/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius10/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius12/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius11/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius13/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.BaseGrooveRadius14/2), False)
base_sketch.AddGeometry(Part.Circle(App.Vector(0,
