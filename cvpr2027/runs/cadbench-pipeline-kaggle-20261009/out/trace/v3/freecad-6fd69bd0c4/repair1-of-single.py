import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# Create a new document
doc = App.newDocument("PerforatedMountPlate")

# Create the main body
body = doc.addObject("PartDesign::Body", "Body")

# Create a parameter set for dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "outer_hex_size", "Dimensions", "Outer hexagon size")
params.addProperty("App::PropertyLength", "inner_hex_size", "Dimensions", "Inner hexagon size")
params.addProperty("App::PropertyLength", "center_hole_dia", "Dimensions", "Center hole diameter")
params.addProperty("App::PropertyLength", "mounting_hole_dia", "Dimensions", "Mounting hole diameter")
params.addProperty("App::PropertyLength", "mounting_hole_depth", "Dimensions", "Mounting hole depth")
params.addProperty("App::PropertyLength", "fillet_radius", "Dimensions", "Corner fillet radius")
params.addProperty("App::PropertyLength", "chamfer_size", "Dimensions", "Chamfer size")
params.addProperty("App::PropertyLength", "plate_thickness", "Dimensions", "Plate thickness")
params.addProperty("App::PropertyLength", "section_thickness", "Dimensions", "Section thickness")

# Set parameter values from the drawing
params.outer_hex_size = 72.12
params.inner_hex_size = 58.0
params.center_hole_dia = 8.0
params.mounting_hole_dia = 3.2
params.mounting_hole_depth = 1.5
params.fillet_radius = 3.0
params.chamfer_size = 1.5
params.plate_thickness = 5.6
params.section_thickness = 1.5

# Create the base sketch on XY plane
sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.ConstrainAuto = True
sketch.TechDrawPictogramSequence = []

# Create outer hexagon (72.12 mm across flats)
# For a regular hexagon, side = outer_hex_size / sqrt(3)
outer_side = params.outer_hex_size / (2 * 0.8660254037844386)  # 2 * cos(30°)
outer_hex = Part.makeHexagon(outer_side, 6)
sketch.addGeometry(outer_hex, False)

# Create inner hexagon (58 mm across flats)
inner_side = params.inner_hex_size / (2 * 0.8660254037844386)
inner_hex = Part.makeHexagon(inner_side, 6)
sketch.addGeometry(inner_hex, False)

# Add constraints to center the hexagons
sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch.addConstraint(Sketcher.Constraint("Center", 1, 0))
sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2))
sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 3, 1, 3))

# Create the pad feature
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = sketch
pad.Length = params.plate_thickness
pad.Type = "Solid"
pad.MidPlane = False
pad.Reversed = False

# Create a sketch for the center hole
center_hole_sketch = body.newObject("Sketcher::SketchObject", "CenterHoleSketch")
center_hole_sketch.Placement = App.Placement(App.Vector(0, 0, params.plate_thickness))
center_hole_sketch.ConstrainAuto = True
center_hole_sketch.TechDrawPictogramSequence = []

# Add center hole circle
center_hole = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.center_hole_dia / 2)
center_hole_sketch.addGeometry(center_hole, False)
center_hole_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))

# Create pocket for center hole
center_pocket = body.newObject("PartDesign::Pocket", "CenterPocket")
center_pocket.Profile = center_hole_sketch
center_pocket.Type = "ThroughAll"
center_pocket.Base = (pad, ["Face1"])

# Create a sketch for the 8 mounting holes
mounting_hole_sketch = body.newObject("Sketcher::SketchObject", "MountingHoleSketch")
mounting_hole_sketch.Placement = App.Placement(App.Vector(0, 0, params.plate_thickness))
mounting_hole_sketch.ConstrainAuto = True
mounting_hole_sketch.TechDrawPictogramSequence = []

# Calculate mounting hole positions (8 holes on a circle)
# Based on the drawing, the mounting holes are arranged in a circle
# The distance from center to mounting hole centers appears to be around 30.5 mm
mounting_radius = 30.5
num_holes = 8
hole_angle = 360.0 / num_holes

for i in range(num_holes):
    angle = i * hole_angle
    x = mounting_radius * App.Vector(math.cos(angle), math.sin(angle), 0)
    hole = Part.Circle(x, App.Vector(0, 0, 1), params.mounting_hole_dia / 2)
    mounting_hole_sketch.addGeometry(hole, False)

# Add constraints to center the mounting holes
mounting_hole_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))

# Create pockets for mounting holes
mounting_pockets = []
for i in range(num_holes):
    angle = i * hole_angle
    x = mounting_radius * App.Vector(math.cos(angle), math.sin(angle), 0)
    
    # Create a sketch for each mounting hole
    hole_sketch = body.newObject("Sketcher::SketchObject", f"MountingHoleSketch{i}")
    hole_sketch.Placement = App.Placement(x)
    hole_sketch.ConstrainAuto = True
    hole_sketch.TechDrawPictogramSequence = []
    
    # Add hole circle
    hole = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.mounting_hole_dia / 2)
    hole_sketch.addGeometry(hole, False)
    hole_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
    
    # Create pocket
    pocket = body.newObject("PartDesign::Pocket", f"MountingPocket{i}")
    pocket.Profile = hole_sketch
    pocket.Type = "ThroughAll"
    pocket.Base = (pad, ["Face1"])
    mounting_pockets.append(pocket)

# Add fillets to the outer edges
fillet = body.newObject("PartDesign::Fillet", "Fillet")
fillet.Base = (pad, ["Edge1"])
fillet.Radius = params.fillet_radius
fillet.Type = "Radius"

# Add chamfers to the edges
chamfer = body.newObject("PartDesign::Chamfer", "Chamfer")
chamfer.Base = (pad, ["Edge1"])
chamfer.Size = params.chamfer_size
chamfer.Type = "Size"

# Recompute the document
doc.recompute()

# Save the document
doc.saveAs(str(Path(__file__).resolve().with_suffix(".FCStd")))
