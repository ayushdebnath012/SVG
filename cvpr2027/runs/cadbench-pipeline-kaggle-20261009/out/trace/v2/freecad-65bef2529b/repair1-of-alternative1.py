import FreeCAD as App
import Part
import math
from pathlib import Path

# Initialize document
doc = App.newDocument("Flange")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement()

# --- 1. Parameters ---
# Define parameters in the Body via a VarSet
params = body.newObject("App::VarSet", "Parameters")

params.addProperty("App::PropertyLength", "flange_outer_diameter", "Dimensions", "Outer diameter of flange")
params.flange_outer_diameter = 107.156

params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of flange")
params.flange_thickness = 21.034

params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Central bore diameter")
params.bore_diameter = 49.213

params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Dimensions", "Diameter of bolt circle")
params.bolt_circle_diameter = 87.313

params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of bolt holes")
params.bolt_hole_diameter = 9.922

params.addProperty("App::PropertyInteger", "number_of_bolt_holes", "Dimensions", "Count of bolt holes")
params.number_of_bolt_holes = 4

# --- 2. Outer Flange Sketch & Pad ---
# Sketch on XY plane to create the base disk
flange_sketch = body.newObject("Sketcher::SketchObject", "FlangeSketch")
flange_sketch.Placement = App.Placement()
flange_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])
flange_sketch.MapMode = "FlatFace"

# Add outer circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.flange_outer_diameter / 2.0)
flange_sketch.addGeometry(outer_circle, False)

# Add center point (for reference)
center_point = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0, 0, 0))
flange_sketch.addGeometry(center_point, False)

# Pad to create the solid flange
flange_pad = body.newObject("PartDesign::Pad", "FlangePad")
flange_pad.Profile = flange_sketch
flange_pad.Type = "FromCurrent"
flange_pad.Length = params.flange_thickness
flange_pad.MidPlane = False
flange_pad.Reversed = False
flange_pad.setExpression("Length", "Parameters.flange_thickness")

# --- 3. Central Bore Sketch & Pocket ---
# Sketch on XY plane (concentric with flange)
bore_sketch = body.newObject("Sketcher::SketchObject", "BoreSketch")
bore_sketch.Placement = App.Placement()
bore_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])
bore_sketch.MapMode = "FlatFace"

# Add inner circle (bore)
bore_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
bore_sketch.addGeometry(bore_circle, False)

# Add center point
center_point_bore = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0, 0, 0))
bore_sketch.addGeometry(center_point_bore, False)

# Pocket to create the through hole
bore_pocket = body.newObject("PartDesign::Pocket", "BorePocket")
bore_pocket.Profile = bore_sketch
bore_pocket.Type = "ThroughAll"
bore_pocket.MidPlane = False

# --- 4. Bolt Hole Pattern Construction ---
# We need to create the hole profile on a sketch, then pattern it.
# The sketch will be placed on the XY plane, centered at origin.

bolt_profile_sketch = body.newObject("Sketcher::SketchObject", "BoltProfileSketch")
bolt_profile_sketch.Placement = App.Placement()
bolt_profile_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])
bolt_profile_sketch.MapMode = "FlatFace"

# Add bolt hole circle
bolt_circle_geom = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
bolt_profile_sketch.addGeometry(bolt_circle_geom, False)

# Add center point for constraint reference
center_point_bolt = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0, 0, 0))
bolt_profile_sketch.addGeometry(center_point_bolt, False)

# Create the individual bolt hole feature (Pattern will replicate this)
# We place it at the first angle (0 degrees)
bolt_hole = body.newObject("PartDesign::Pocket", "BoltHole")
bolt_hole.Profile = bolt_profile_sketch
bolt_hole.Type = "ThroughAll"
bolt_hole.MidPlane = False

# --- 5. Polar Pattern of Bolt Holes ---
bolt_pattern = body.newObject("PartDesign::PolarPattern", "BoltPattern")
bolt_pattern.Originals = [bolt_hole]
bolt_pattern.Axis = (doc.getObject("Z_Axis"), [])
bolt_pattern.Placement = App.Placement()
bolt_pattern.setExpression("Angle", "360")
bolt_pattern.setExpression("Occurrences", "Parameters.number_of_bolt_holes")
bolt_pattern.setExpression("AngleStep", "360 / Parameters.number_of_bolt_holes")
bolt_pattern.setExpression("OccurrenceAngle", "0")

# --- 6. Recalculate ---
doc.recompute()

# --- 7. Save ---
# Determine output path based on __file__
script_path = Path(__file__).resolve()
output_path = script_path.parent / f"{script_path.stem}.FCStd"

doc.saveAs(str(output_path))
print(f"Model saved to: {output_path}")
