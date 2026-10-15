# FreeCAD 1.1 Script to build the Ratchet Latch Lever from engineering drawing c548c73008.png
# All dimensions are in mm.

import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create document
doc = App.newDocument("RatchetLever")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "L_total", "Dimensions", "Total length")
params.addProperty("App::PropertyLength", "L_main", "Dimensions", "Main body length")
params.addProperty("App::PropertyLength", "W_main", "Dimensions", "Main body width")
params.addProperty("App::PropertyLength", "R_main", "Dimensions", "Main body radius")
params.addProperty("App::PropertyLength", "H_main", "Dimensions", "Main body height")
params.addProperty("App::PropertyLength", "R_ratchet", "Dimensions", "Ratchet tooth height")
params.addProperty("App::PropertyLength", "R_handle", "Dimensions", "Handle radius")
params.addProperty("App::PropertyLength", "R_mount", "Dimensions", "Mounting hole radius")
params.addProperty("App::PropertyLength", "L_mount", "Dimensions", "Mounting hole diameter")
params.addProperty("App::PropertyLength", "L_pin", "Dimensions", "Pin diameter")
params.addProperty("App::PropertyLength", "R_pin", "Dimensions", "Pin shoulder radius")
params.addProperty("App::PropertyLength", "H_pin", "Dimensions", "Pin shoulder height")
params.addProperty("App::PropertyLength", "R_throat", "Dimensions", "Throat radius")
params.addProperty("App::PropertyLength", "L_throat", "Dimensions", "Throat length")
params.addProperty("App::PropertyLength", "R_arm", "Dimensions", "Arm length")
params.addProperty("App::PropertyLength", "H_arm", "Dimensions", "Arm height")
params.addProperty("App::PropertyLength", "R_arm_end", "Dimensions", "Arm end radius")
params.addProperty("App::PropertyLength", "L_arm_end", "Dimensions", "Arm end length")
params.addProperty("App::PropertyLength", "R_pivot", "Dimensions", "Pivot radius")
params.addProperty("App::PropertyLength", "H_pivot", "Dimensions", "Pivot height")
params.addProperty("App::PropertyLength", "R_gear", "Dimensions", "Gear radius")
params.addProperty("App::PropertyLength", "L_gear", "Dimensions", "Gear length")
params.addProperty("App::PropertyLength", "R_gear_hole", "Dimensions", "Gear hole radius")
params.addProperty("App::PropertyLength", "L_gear_hole", "Dimensions", "Gear hole diameter")
params.addProperty("App::PropertyLength", "R_gear_tooth", "Dimensions", "Gear tooth height")
params.addProperty("App::PropertyLength", "L_gear_tooth", "Dimensions", "Gear tooth length")
params.addProperty("App::PropertyLength", "R_gear_tooth_radius", "Dimensions", "Gear tooth radius")
params.addProperty("App::PropertyLength", "L_gear_tooth_depth", "Dimensions", "Gear tooth depth")
params.addProperty("App::PropertyLength", "R_gear_tooth_angle", "Dimensions", "Gear tooth angle")
params.addProperty("App::PropertyLength", "L_gear_tooth_arc", "Dimensions", "Gear tooth arc")
params.addProperty("App::PropertyLength", "R_gear_tooth_start", "Dimensions", "Gear tooth start angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_end", "Dimensions", "Gear tooth end angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_center", "Dimensions", "Gear tooth center angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_width", "Dimensions", "Gear tooth width")
params.addProperty("App::PropertyLength", "R_gear_tooth_height", "Dimensions", "Gear tooth height")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_angle", "Dimensions", "Gear tooth width angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_angle", "Dimensions", "Gear tooth height angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_start", "Dimensions", "Gear tooth width start angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_start", "Dimensions", "Gear tooth height start angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_end", "Dimensions", "Gear tooth width end angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_end", "Dimensions", "Gear tooth height end angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_center", "Dimensions", "Gear tooth width center angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_center", "Dimensions", "Gear tooth height center angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_arc", "Dimensions", "Gear tooth width arc")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_arc", "Dimensions", "Gear tooth height arc")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_start_angle", "Dimensions", "Gear tooth width start arc angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_start_angle", "Dimensions", "Gear tooth height start arc angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_end_angle", "Dimensions", "Gear tooth width end arc angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_end_angle", "Dimensions", "Gear tooth height end arc angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_center_angle", "Dimensions", "Gear tooth width center arc angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_center_angle", "Dimensions", "Gear tooth height center arc angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_arc_angle", "Dimensions", "Gear tooth width arc angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_arc_angle", "Dimensions", "Gear tooth height arc angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_start_arc", "Dimensions", "Gear tooth width start arc")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_start_arc", "Dimensions", "Gear tooth height start arc")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_end_arc", "Dimensions", "Gear tooth width end arc")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_end_arc", "Dimensions", "Gear tooth height end arc")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_center_arc", "Dimensions", "Gear tooth width center arc")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_center_arc", "Dimensions", "Gear tooth height center arc")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_start_arc_angle", "Dimensions", "Gear tooth width start arc angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_start_arc_angle", "Dimensions", "Gear tooth height start arc angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_end_arc_angle", "Dimensions", "Gear tooth width end arc angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_end_arc_angle", "Dimensions", "Gear tooth height end arc angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_width_center_arc_angle", "Dimensions", "Gear tooth width center arc angle")
params.addProperty("App::PropertyLength", "R_gear_tooth_height_center_arc_angle", "Dimensions", "Gear tooth height center arc angle")

# --- Dimension Values ---
params.L_total = 142.65
params.L_main = 110.93
params.W_main = 18.0
params.R_main = 8.03
params.H_main = 14.0
params.R_ratchet = 3.2
params.R_handle = 8.95
params.R_mount = 3.0
params.L_mount = 6.0
params.L_pin = 3.0
params.R_pin = 4.5
params.H_pin = 1.5
params.R_throat = 2.0
params.L_throat = 8.0
params.R_arm = 37.6
params.H_arm = 3.0
params.R_arm_end = 2.0
params.L_arm_end = 4.0
params.R_pivot = 2.5
params.H_pivot = 4.0
params.R_gear = 10.0
params.L_gear = 5.0
params.R_gear_hole = 4.0
params.L_gear_hole = 8.0
params.R_gear_tooth = 2.0
params.L_gear_tooth = 3.0
params.R_gear_tooth_radius = 1.0
params.L_gear_tooth_depth = 1.0
params.R_gear_tooth_angle = 30.0
params.L_gear_tooth_arc = 2.0
params.R_gear_tooth_start = 0.0
params.R_gear_tooth_end = 360.0
params.R_gear_tooth_center = 180.0
params.R_gear_tooth_width = 2.0
params.R_gear_tooth_height = 1.0
params.R_gear_tooth_width_angle = 30.0
params.R_gear_tooth_height_angle = 30.0
params.R_gear_tooth_width_start = 0.0
params.R_gear_tooth_height_start = 0.0
params.R_gear_tooth_width_end = 360.0
params.R_gear_tooth_height_end = 360.0
params.R_gear_tooth_width_center = 180.0
params.R_gear_tooth_height_center = 180.0
params.R_gear_tooth_width_arc = 2.0
params.R_gear_tooth_height_arc = 1.0
params.R_gear_tooth_width_start_angle = 0.0
params.R_gear_tooth_height_start_angle = 0.0
params.R_gear_tooth_width_end_angle = 360.0
params.R_gear_tooth_height_end_angle = 360.0
params.R_gear_tooth_width_center_angle = 180.0
params.R_gear_tooth_height_center_angle = 180.0
params.R_gear_tooth_width_arc_angle = 2.0
params.R_gear_tooth_height_arc_angle = 1.0
params.R_gear_tooth_width_start_arc = 0.0
params.R_gear_tooth_height_start_arc = 0.0
params.R_gear_tooth_width_end_arc = 360.0
params.R_gear_tooth_height_end_arc = 360.0
params.R_gear_tooth_width_center_arc = 180.0
params.R_gear_tooth_height_center_arc = 180.0
params.R_gear_tooth_width_start_arc_angle = 0.0
params.R_gear_tooth_height_start_arc_angle = 0.0
params.R_gear_tooth_width_end_arc_angle = 360.0
params.R_gear_tooth_height_end_arc_angle = 360.0
params.R_gear_tooth_width_center_arc_angle = 180.0
params.R_gear_tooth_height_center_arc_angle = 180.0

# --- Sketch 1: Main Body ---
sketch1 = body.newObject("Sketcher::SketchObject", "MainBodySketch")
sketch1.Placement = App.Placement(App.Vector(0, 0, 0))
sketch1.Support = [doc.getObject("XY_Plane"), [""]]
sketch1.MapMode = "Plane"
sketch1.Constraints = []

# Add geometry
sketch1.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(110.93, 0, 0)), False)
sketch1.addGeometry(Part.LineSegment(App.Vector(110.93, 0, 0), App.Vector(110.93, 18.0, 0)), False)
sketch1.addGeometry(Part.LineSegment(App.Vector(110.93, 18.0, 0), App.Vector(0, 18.0, 0)), False)
sketch1.addGeometry(Part.LineSegment(App.Vector(0, 18.0, 0), App.Vector(0, 0, 0)), False)

# Add constraints
sketch1.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))  # Left end
sketch1.addConstraint(Sketcher.Constraint("Coincident", 0, 3, 1, 3))  # Right end
sketch1.addConstraint(Sketcher.Constraint("Horizontal", 0, 2, 1, 1))  # Top line
sketch1.addConstraint(Sketcher.Constraint("Horizontal", 0, 3, 1, 3))  # Bottom line
sketch1.addConstraint(Sketcher.Constraint("Vertical", 0, 2, 1, 1))  # Left line
sketch1.addConstraint(Sketcher.Constraint("Vertical", 0, 3, 1, 3))  # Right line
sketch1.addConstraint(Sketcher.Constraint("Length", 0, 2, 110.93))  # Total length
sketch1.addConstraint(Sketcher.Constraint("Length", 0, 3, 18.0))  # Total width

# --- Sketch 2: Main Body Radius ---
sketch2 = body.newObject("Sketcher::SketchObject", "MainBodyRadiusSketch")
sketch2.Placement = App.Placement(App.Vector(110.93, 9.0, 0))
sketch2.Support = [doc.getObject("XY_Plane"), [""]]
sketch2.MapMode = "Plane"
sketch2.Constraints = []

# Add geometry
sketch2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 8.03), False)

# Add constraints
sketch2.addConstraint(Sketcher.Constraint("Radius", 0, 2, 8.03))  # Radius

# --- Sketch 3: Mounting Hole ---
sketch3 = body.newObject("Sketcher::SketchObject", "MountingHoleSketch")
sketch3.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch3.Support = [doc.getObject("XY_Plane"), [""]]
sketch3.MapMode = "Plane"
sketch3.Constraints = []

# Add geometry
sketch3.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 3.0), False)

# Add constraints
sketch3.addConstraint(Sketcher.Constraint("Radius", 0, 2, 3.0))  # Radius

# --- Sketch 4: Throat ---
sketch4 = body.newObject("Sketcher::SketchObject", "ThroatSketch")
sketch4.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch4.Support = [doc.getObject("XY_Plane"), [""]]
sketch4.MapMode = "Plane"
sketch4.Constraints = []

# Add geometry
sketch4.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 2.0), False)

# Add constraints
sketch4.addConstraint(Sketcher.Constraint("Radius", 0, 2, 2.0))  # Radius

# --- Sketch 5: Arm ---
sketch5 = body.newObject("Sketcher::SketchObject", "ArmSketch")
sketch5.Placement = App.Placement(App.Vector(93.02, 9.0, 0))
sketch5.Support = [doc.getObject("XY_Plane"), [""]]
sketch5.MapMode = "Plane"
sketch5.Constraints = []

# Add geometry
sketch5.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(37.6, 0, 0)), False)
sketch5.addGeometry(Part.LineSegment(App.Vector(37.6, 0, 0), App.Vector(37.6, 3.0, 0)), False)
sketch5.addGeometry(Part.LineSegment(App.Vector(37.6, 3.0, 0), App.Vector(0, 3.0, 0)), False)
sketch5.addGeometry(Part.LineSegment(App.Vector(0, 3.0, 0), App.Vector(0, 0, 0)), False)

# Add constraints
sketch5.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))  # Left end
sketch5.addConstraint(Sketcher.Constraint("Coincident", 0, 3, 1, 3))  # Right end
sketch5.addConstraint(Sketcher.Constraint("Horizontal", 0, 2, 1, 1))  # Top line
sketch5.addConstraint(Sketcher.Constraint("Horizontal", 0, 3, 1, 3))  # Bottom line
sketch5.addConstraint(Sketcher.Constraint("Vertical", 0, 2, 1, 1))  # Left line
sketch5.addConstraint(Sketcher.Constraint("Vertical", 0, 3, 1, 3))  # Right line
sketch5.addConstraint(Sketcher.Constraint("Length", 0, 2, 37.6))  # Arm length
sketch5.addConstraint(Sketcher.Constraint("Length", 0, 3, 3.0))  # Arm height

# --- Sketch 6: Arm End Radius ---
sketch6 = body.newObject("Sketcher::SketchObject", "ArmEndRadiusSketch")
sketch6.Placement = App.Placement(App.Vector(130.62, 9.0, 0))
sketch6.Support = [doc.getObject("XY_Plane"), [""]]
sketch6.MapMode = "Plane"
sketch6.Constraints = []

# Add geometry
sketch6.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 2.0), False)

# Add constraints
sketch6.addConstraint(Sketcher.Constraint("Radius", 0, 2, 2.0))  # Radius

# --- Sketch 7: Pivot ---
sketch7 = body.newObject("Sketcher::SketchObject", "PivotSketch")
sketch7.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch7.Support = [doc.getObject("XY_Plane"), [""]]
sketch7.MapMode = "Plane"
sketch7.Constraints = []

# Add geometry
sketch7.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 2.5), False)

# Add constraints
sketch7.addConstraint(Sketcher.Constraint("Radius", 0, 2, 2.5))  # Radius

# --- Sketch 8: Gear ---
sketch8 = body.newObject("Sketcher::SketchObject", "GearSketch")
sketch8.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch8.Support = [doc.getObject("XY_Plane"), [""]]
sketch8.MapMode = "Plane"
sketch8.Constraints = []

# Add geometry
sketch8.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 10.0), False)

# Add constraints
sketch8.addConstraint(Sketcher.Constraint("Radius", 0, 2, 10.0))  # Radius

# --- Sketch 9: Gear Hole ---
sketch9 = body.newObject("Sketcher::SketchObject", "GearHoleSketch")
sketch9.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch9.Support = [doc.getObject("XY_Plane"), [""]]
sketch9.MapMode = "Plane"
sketch9.Constraints = []

# Add geometry
sketch9.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 4.0), False)

# Add constraints
sketch9.addConstraint(Sketcher.Constraint("Radius", 0, 2, 4.0))  # Radius

# --- Sketch 10: Gear Tooth ---
sketch10 = body.newObject("Sketcher::SketchObject", "GearToothSketch")
sketch10.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch10.Support = [doc.getObject("XY_Plane"), [""]]
sketch10.MapMode = "Plane"
sketch10.Constraints = []

# Add geometry
sketch10.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 2.0), False)

# Add constraints
sketch10.addConstraint(Sketcher.Constraint("Radius", 0, 2, 2.0))  # Radius

# --- Sketch 11: Gear Tooth Radius ---
sketch11 = body.newObject("Sketcher::SketchObject", "GearToothRadiusSketch")
sketch11.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch11.Support = [doc.getObject("XY_Plane"), [""]]
sketch11.MapMode = "Plane"
sketch11.Constraints = []

# Add geometry
sketch11.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 1.0), False)

# Add constraints
sketch11.addConstraint(Sketcher.Constraint("Radius", 0, 2, 1.0))  # Radius

# --- Sketch 12: Gear Tooth Depth ---
sketch12 = body.newObject("Sketcher::SketchObject", "GearToothDepthSketch")
sketch12.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch12.Support = [doc.getObject("XY_Plane"), [""]]
sketch12.MapMode = "Plane"
sketch12.Constraints = []

# Add geometry
sketch12.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 1.0), False)

# Add constraints
sketch12.addConstraint(Sketcher.Constraint("Radius", 0, 2, 1.0))  # Radius

# --- Sketch 13: Gear Tooth Angle ---
sketch13 = body.newObject("Sketcher::SketchObject", "GearToothAngleSketch")
sketch13.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch13.Support = [doc.getObject("XY_Plane"), [""]]
sketch13.MapMode = "Plane"
sketch13.Constraints = []

# Add geometry
sketch13.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 30.0), False)

# Add constraints
sketch13.addConstraint(Sketcher.Constraint("Radius", 0, 2, 30.0))  # Radius

# --- Sketch 14: Gear Tooth Arc ---
sketch14 = body.newObject("Sketcher::SketchObject", "GearToothArcSketch")
sketch14.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch14.Support = [doc.getObject("XY_Plane"), [""]]
sketch14.MapMode = "Plane"
sketch14.Constraints = []

# Add geometry
sketch14.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 2.0), False)

# Add constraints
sketch14.addConstraint(Sketcher.Constraint("Radius", 0, 2, 2.0))  # Radius

# --- Sketch 15: Gear Tooth Start ---
sketch15 = body.newObject("Sketcher::SketchObject", "GearToothStartSketch")
sketch15.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch15.Support = [doc.getObject("XY_Plane"), [""]]
sketch15.MapMode = "Plane"
sketch15.Constraints = []

# Add geometry
sketch15.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 0.0), False)

# Add constraints
sketch15.addConstraint(Sketcher.Constraint("Radius", 0, 2, 0.0))  # Radius

# --- Sketch 16: Gear Tooth End ---
sketch16 = body.newObject("Sketcher::SketchObject", "GearToothEndSketch")
sketch16.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch16.Support = [doc.getObject("XY_Plane"), [""]]
sketch16.MapMode = "Plane"
sketch16.Constraints = []

# Add geometry
sketch16.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 360.0), False)

# Add constraints
sketch16.addConstraint(Sketcher.Constraint("Radius", 0, 2, 360.0))  # Radius

# --- Sketch 17: Gear Tooth Center ---
sketch17 = body.newObject("Sketcher::SketchObject", "GearToothCenterSketch")
sketch17.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch17.Support = [doc.getObject("XY_Plane"), [""]]
sketch17.MapMode = "Plane"
sketch17.Constraints = []

# Add geometry
sketch17.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180.0), False)

# Add constraints
sketch17.addConstraint(Sketcher.Constraint("Radius", 0, 2, 180.0))  # Radius

# --- Sketch 18: Gear Tooth Width ---
sketch18 = body.newObject("Sketcher::SketchObject", "GearToothWidthSketch")
sketch18.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch18.Support = [doc.getObject("XY_Plane"), [""]]
sketch18.MapMode = "Plane"
sketch18.Constraints = []

# Add geometry
sketch18.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 2.0), False)

# Add constraints
sketch18.addConstraint(Sketcher.Constraint("Radius", 0, 2, 2.0))  # Radius

# --- Sketch 19: Gear Tooth Height ---
sketch19 = body.newObject("Sketcher::SketchObject", "GearToothHeightSketch")
sketch19.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch19.Support = [doc.getObject("XY_Plane"), [""]]
sketch19.MapMode = "Plane"
sketch19.Constraints = []

# Add geometry
sketch19.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 1.0), False)

# Add constraints
sketch19.addConstraint(Sketcher.Constraint("Radius", 0, 2, 1.0))  # Radius

# --- Sketch 20: Gear Tooth Width Angle ---
sketch20 = body.newObject("Sketcher::SketchObject", "GearToothWidthAngleSketch")
sketch20.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch20.Support = [doc.getObject("XY_Plane"), [""]]
sketch20.MapMode = "Plane"
sketch20.Constraints = []

# Add geometry
sketch20.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 30.0), False)

# Add constraints
sketch20.addConstraint(Sketcher.Constraint("Radius", 0, 2, 30.0))  # Radius

# --- Sketch 21: Gear Tooth Height Angle ---
sketch21 = body.newObject("Sketcher::SketchObject", "GearToothHeightAngleSketch")
sketch21.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch21.Support = [doc.getObject("XY_Plane"), [""]]
sketch21.MapMode = "Plane"
sketch21.Constraints = []

# Add geometry
sketch21.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 30.0), False)

# Add constraints
sketch21.addConstraint(Sketcher.Constraint("Radius", 0, 2, 30.0))  # Radius

# --- Sketch 22: Gear Tooth Width Start ---
sketch22 = body.newObject("Sketcher::SketchObject", "GearToothWidthStartSketch")
sketch22.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch22.Support = [doc.getObject("XY_Plane"), [""]]
sketch22.MapMode = "Plane"
sketch22.Constraints = []

# Add geometry
sketch22.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 0.0), False)

# Add constraints
sketch22.addConstraint(Sketcher.Constraint("Radius", 0, 2, 0.0))  # Radius

# --- Sketch 23: Gear Tooth Height Start ---
sketch23 = body.newObject("Sketcher::SketchObject", "GearToothHeightStartSketch")
sketch23.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch23.Support = [doc.getObject("XY_Plane"), [""]]
sketch23.MapMode = "Plane"
sketch23.Constraints = []

# Add geometry
sketch23.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 0.0), False)

# Add constraints
sketch23.addConstraint(Sketcher.Constraint("Radius", 0, 2, 0.0))  # Radius

# --- Sketch 24: Gear Tooth Width End ---
sketch24 = body.newObject("Sketcher::SketchObject", "GearToothWidthEndSketch")
sketch24.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch24.Support = [doc.getObject("XY_Plane"), [""]]
sketch24.MapMode = "Plane"
sketch24.Constraints = []

# Add geometry
sketch24.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 360.0), False)

# Add constraints
sketch24.addConstraint(Sketcher.Constraint("Radius", 0, 2, 360.0))  # Radius

# --- Sketch 25: Gear Tooth Height End ---
sketch25 = body.newObject("Sketcher::SketchObject", "GearToothHeightEndSketch")
sketch25.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch25.Support = [doc.getObject("XY_Plane"), [""]]
sketch25.MapMode = "Plane"
sketch25.Constraints = []

# Add geometry
sketch25.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 360.0), False)

# Add constraints
sketch25.addConstraint(Sketcher.Constraint("Radius", 0, 2, 360.0))  # Radius

# --- Sketch 26: Gear Tooth Width Center ---
sketch26 = body.newObject("Sketcher::SketchObject", "GearToothWidthCenterSketch")
sketch26.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch26.Support = [doc.getObject("XY_Plane"), [""]]
sketch26.MapMode = "Plane"
sketch26.Constraints = []

# Add geometry
sketch26.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180.0), False)

# Add constraints
sketch26.addConstraint(Sketcher.Constraint("Radius", 0, 2, 180.0))  # Radius

# --- Sketch 27: Gear Tooth Height Center ---
sketch27 = body.newObject("Sketcher::SketchObject", "GearToothHeightCenterSketch")
sketch27.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch27.Support = [doc.getObject("XY_Plane"), [""]]
sketch27.MapMode = "Plane"
sketch27.Constraints = []

# Add geometry
sketch27.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180.0), False)

# Add constraints
sketch27.addConstraint(Sketcher.Constraint("Radius", 0, 2, 180.0))  # Radius

# --- Sketch 28: Gear Tooth Width Arc ---
sketch28 = body.newObject("Sketcher::SketchObject", "GearToothWidthArcSketch")
sketch28.Placement = App.Placement(App.Vector(106.51, 9.0, 0))
sketch28.Support = [doc.getObject("XY_Plane"), [""]]
sketch28.MapMode = "Plane"
sketch28.Constraints = []

# Add geometry
sketch28.addGeometry(Part.Circle(App.Vector(
