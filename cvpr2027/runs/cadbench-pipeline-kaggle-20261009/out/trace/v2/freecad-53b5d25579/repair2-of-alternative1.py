"""
FreeCAD 1.1 Script to generate a Socket Weld Flange.
Saves the model to /app/answer.FCStd derived from __file__.
"""

from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

# -----------------------------------------------------------------------------
# 1. Setup Document and Parameters
# -----------------------------------------------------------------------------
doc = App.newDocument("SocketFlange")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define named parameters using App::VarSet
# This is the standard way to have editable parameters in PartDesign
params = body.newObject("App::VarSet", "Parameters")

params.addProperty("App::PropertyLength", "outer_circle_diameter", "Dimensions", "Overall outer diameter")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the main flange")
params.addProperty("App::PropertyLength", "total_height", "Dimensions", "Total height of the flange")
params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Center hole diameter")
params.addProperty("App::PropertyLength", "neck_diameter", "Dimensions", "Diameter of the neck")
params.addProperty("App::PropertyLength", "neck_height", "Dimensions", "Height of the neck")
params.addProperty("App::PropertyLength", "socket_diameter", "Dimensions", "Diameter of the socket weld recess")
params.addProperty("App::PropertyLength", "socket_depth", "Dimensions", "Depth of the socket weld recess")
params.addProperty("App::PropertyLength", "raised_face_diameter", "Dimensions", "Diameter of the raised face")
params.addProperty("App::PropertyLength", "raised_face_thickness", "Dimensions", "Thickness of the raised face")
params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Dimensions", "Diameter of the bolt circle")
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of bolt holes")
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Number of bolt holes")

# Set default values as per specification
params.outer_circle_diameter = 130.0
params.flange_thickness = 17.5
params.total_height = 22.0
params.bore_diameter = 41.0
params.neck_diameter = 65.0
params.neck_height = 2.5
params.socket_diameter = 49.5
params.socket_depth = 16.0
params.raised_face_diameter = 73.0
params.raised_face_thickness = 2.0
params.bolt_circle_diameter = 98.5
params.bolt_hole_diameter = 16.0
params.number_bolt_holes = 4

# -----------------------------------------------------------------------------
# 2. Base Flange Body (Extruded Disk)
# -----------------------------------------------------------------------------
# Sketch 1: Outer Circle on XY Plane
sketch_base = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Support = (doc.getObject("XY_Plane"), [""])
sketch_base.MapMode = "FlatFace"

# Outer Circle
circle_base = sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_circle_diameter / 2.0), False)
# Center Coincident Constraint
sketch_base.addConstraint(Sketcher.Constraint("Axis", 0, 2))

# Pad the base flange
pad_base = body.newObject("PartDesign::Pad", "PadFlange")
pad_base.Profile = sketch_base
pad_base.Length = params.total_height
pad_base.Midplane = False # Build upwards from bottom

# -----------------------------------------------------------------------------
# 3. Bore Hole (Through All)
# -----------------------------------------------------------------------------
# Sketch 2: Bore on XY Plane
sketch_bore = body.newObject("Sketcher::SketchObject", "SketchBore")
sketch_bore.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_bore.Support = (doc.getObject("XY_Plane"), [""])
sketch_bore.MapMode = "FlatFace"

circle_bore = sketch_bore.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0), False)
sketch_bore.addConstraint(Sketcher.Constraint("Axis", 0, 2))

pocket_bore = body.newObject("PartDesign::Pocket", "PocketBore")
pocket_bore.Profile = sketch_bore
pocket_bore.Type = "ThroughAll"

# -----------------------------------------------------------------------------
# 4. Neck Pocket (Remove material from bottom)
# -----------------------------------------------------------------------------
# Sketch 3: Neck on XY Plane
sketch_neck = body.newObject("Sketcher::SketchObject", "SketchNeck")
sketch_neck.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_neck.Support = (doc.getObject("XY_Plane"), [""])
sketch_neck.MapMode = "FlatFace"

circle_neck = sketch_neck.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.neck_diameter / 2.0), False)
sketch_neck.addConstraint(Sketcher.Constraint("Axis", 0, 2))

pocket_neck = body.newObject("PartDesign::Pocket", "PocketNeck")
pocket_neck.Profile = sketch_neck
pocket_neck.Length = params.neck_height
pocket_neck.Midplane = False

# -----------------------------------------------------------------------------
# 5. Socket Pocket (Remove material from top)
# -----------------------------------------------------------------------------
# The socket is defined as a recess starting from the top of the "Raised Face".
# Raised Face Thickness = 2mm (Top 2mm of the flange).
# Socket Depth = 16mm (Measured from the bottom of the Raised Face).
# So the socket starts at Z = TotalHeight - RaisedFaceThickness = 22 - 2 = 20mm.
# And cuts downwards for 16mm, ending at Z = 4mm.

# Sketch 4: Socket on XY Plane
sketch_socket = body.newObject("Sketcher::SketchObject", "SketchSocket")
sketch_socket.Placement = App.Placement(App.Vector(0, 0, params.total_height - params.raised_face_thickness))
sketch_socket.Support = (doc.getObject("XY_Plane"), [""])
sketch_socket.MapMode = "FlatFace"

circle_socket = sketch_socket.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.socket_diameter / 2.0), False)
sketch_socket.addConstraint(Sketcher.Constraint("Axis", 0, 2))

pocket_socket = body.newObject("PartDesign::Pocket", "PocketSocket")
pocket_socket.Profile = sketch_socket
pocket_socket.Length = params.socket_depth
pocket_socket.Midplane = False # Cut downwards only

# -----------------------------------------------------------------------------
# 6. Bolt Holes
# -----------------------------------------------------------------------------
# Sketch 5: Single Bolt Hole on XY Plane
sketch_bolts = body.newObject("Sketcher::SketchObject", "SketchBolts")
sketch_bolts.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_bolts.Support = (doc.getObject("XY_Plane"), [""])
sketch_bolts.MapMode = "FlatFace"

circle_bolt_single = sketch_bolts.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0), False)
sketch_bolts.addConstraint(Sketcher.Constraint("Axis", 0, 2))

# Pattern the bolt holes
pattern_bolts = body.newObject("PartDesign::PolarPattern", "PatternBolts")
pattern_bolts.Profile = sketch_bolts
pattern_bolts.Axis = (doc.getObject("Z_Axis"), [""])
pattern_bolts.Occurrences = params.number_bolt_holes
pattern_bolts.Angle = 360.0
pattern_bolts.Distribute = False # Distribute along the circle
pattern_bolts.Reference = (sketch_bolts, [""])

# -----------------------------------------------------------------------------
# 7. Recompute and Save
# -----------------------------------------------------------------------------
doc.recompute()

# Save the file next to the script
script_path = Path(__file__).resolve()
output_path = script_path.with_name("answer.FCStd")

doc.saveAs(str(output_path))
