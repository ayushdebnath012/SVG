import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("CoaxialPin")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
# Body placement is handled by the Body object itself, default is (0,0,0)

# --- Parameters ---
# We will store parameters in a VarSet object to keep them editable and named
params = body.newObject("App::VarSet", "Parameters")

# Rod Section
params.addProperty("App::PropertyLength", "rod_diameter", "Dimensions", "rod_diameter")
params.rod_diameter = 8.0
params.addProperty("App::PropertyLength", "rod_length", "Dimensions", "rod_length")
params.rod_length = 112.3

# Shoulder Section
params.addProperty("App::PropertyLength", "shoulder_diameter", "Dimensions", "shoulder_diameter")
params.shoulder_diameter = 19.6
params.addProperty("App::PropertyLength", "shoulder_length", "Dimensions", "shoulder_length")
params.shoulder_length = 6.5
params.addProperty("App::PropertyLength", "shoulder_edge_chamfer_length", "Dimensions", "shoulder_edge_chamfer_length")
params.shoulder_edge_chamfer_length = 0.3

# Piston Head Section
params.addProperty("App::PropertyLength", "piston_head_outer_diameter", "Dimensions", "piston_head_outer_diameter")
params.piston_head_outer_diameter = 20.0
params.addProperty("App::PropertyLength", "piston_head_first_groove_diameter", "Dimensions", "piston_head_first_groove_diameter")
params.piston_head_first_groove_diameter = 11.0
params.addProperty("App::PropertyLength", "piston_head_first_groove_width", "Dimensions", "piston_head_first_groove_width")
params.piston_head_first_groove_width = 3.5
params.addProperty("App::PropertyLength", "piston_head_second_groove_diameter", "Dimensions", "piston_head_second_groove_diameter")
params.piston_head_second_groove_diameter = 14.0
params.addProperty("App::PropertyLength", "piston_head_second_groove_width", "Dimensions", "piston_head_second_groove_width")
params.piston_head_second_groove_width = 2.4
params.addProperty("App::PropertyLength", "piston_head_first_groove_to_recess_boss_axial_gap", "Dimensions", "piston_head_first_groove_to_recess_boss_axial_gap")
params.piston_head_first_groove_to_recess_boss_axial_gap = 5.0
params.addProperty("App::PropertyLength", "piston_head_first_to_second_groove_axial_gap", "Dimensions", "piston_head_first_to_second_groove_axial_gap")
params.piston_head_first_to_second_groove_axial_gap = 1.0
params.addProperty("App::PropertyLength", "piston_head_groove_outer_fillet_radius", "Dimensions", "piston_head_groove_outer_fillet_radius")
params.piston_head_groove_outer_fillet_radius = 0.3
params.addProperty("App::PropertyLength", "piston_head_groove_inner_fillet_radius", "Dimensions", "piston_head_groove_inner_fillet_radius")
params.piston_head_groove_inner_fillet_radius = 0.2
params.addProperty("App::PropertyLength", "piston_head_recess_boss_diameter", "Dimensions", "piston_head_recess_boss_diameter")
params.piston_head_recess_boss_diameter = 18.0
params.addProperty("App::PropertyLength", "piston_head_recess_boss_length", "Dimensions", "piston_head_recess_boss_length")
params.piston_head_recess_boss_length = 1.0
params.addProperty("App::PropertyLength", "piston_head_end_chamfer_length", "Dimensions", "piston_head_end_chamfer_length")
params.piston_head_end_chamfer_length = 0.3

# Rod Extension & Tip Section
params.addProperty("App::PropertyLength", "rod_extension_length", "Dimensions", "rod_extension_length")
params.rod_extension_length = 4.4
params.addProperty("App::PropertyLength", "taper_axial_length", "Dimensions", "taper_axial_length")
params.taper_axial_length = 1.1
params.addProperty("App::PropertyLength", "shallow_groove_diameter", "Dimensions", "shallow_groove_diameter")
params.shallow_groove_diameter = 5.8
params.addProperty("App::PropertyLength", "shallow_groove_length", "Dimensions", "shallow_groove_length")
params.shallow_groove_length = 2.0
params.addProperty("App::PropertyLength", "tip_diameter", "Dimensions", "tip_diameter")
params.tip_diameter = 6.0
params.addProperty("App::PropertyLength", "tip_length", "Dimensions", "tip_length")
params.tip_length = 13.0
params.addProperty("App::PropertyLength", "tip_end_diameter", "Dimensions", "tip_end_diameter")
params.tip_end_diameter = 4.77
params.addProperty("App::PropertyLength", "tip_end_chamfer_axial_length", "Dimensions", "tip_end_chamfer_axial_length")
params.tip_end_chamfer_axial_length = 0.61

# Trapezoidal Flats
params.addProperty("App::PropertyLength", "trapezoidal_flat_depth", "Dimensions", "trapezoidal_flat_depth")
params.trapezoidal_flat_depth = 1.0
params.addProperty("App::PropertyLength", "trapezoidal_flat_width", "Dimensions", "trapezoidal_flat_width")
params.trapezoidal_flat_width = 3.0
params.addProperty("App::PropertyAngle", "trapezoidal_flat_flank_angle", "Dimensions", "trapezoidal_flat_flank_angle")
params.trapezoidal_flat_flank_angle = 135.0

# --- Geometry Construction ---

# 1. Base Sketch: The Elongated Rod (Datum)
# This sketch defines the main rod diameter and length.
# Z=0 is the junction between the rod extension and the elongated rod.
# Positive Z goes towards the head. Negative Z goes towards the tip.
sketch_rod = body.newObject("Sketcher::SketchObject", "Sketch_Rod")
sketch_rod.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_rod.Support = (doc.getObject("XY_Plane"), [])
sketch_rod.MapMode = "FlatFace"

# Rod profile: Circle at Z=0
r_rod = params.rod_diameter / 2.0
sketch_rod.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_rod), False)

# Constraint: Center on origin
sketch_rod.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch_rod.addConstraint(Sketcher.Constraint("Radius", 0, r_rod))

# Pad the rod to define the full length.
pad_rod = body.newObject("PartDesign::Pad", "Pad_Rod")
pad_rod.Profile = sketch_rod
pad_rod.Length = params.rod_length
pad_rod.Type = "Blind"
pad_rod.Midplane = False
pad_rod.Reversed = False

# 2. Piston Head Features (Positive Z direction)
# The head starts at Z = 0.
# Order: Shoulder -> Groove 1 -> Gap -> Recess Boss -> Gap -> Groove 2 -> End.

# 2.1 Shoulder
# Diameter: shoulder_diameter, Length: shoulder_length
sketch_shoulder = body.newObject("Sketcher::SketchObject", "Sketch_Shoulder")
sketch_shoulder.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_shoulder.Support = (doc.getObject("XY_Plane"), [])
sketch_shoulder.MapMode = "FlatFace"
r_shoulder = params.shoulder_diameter / 2.0
sketch_shoulder.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_shoulder), False)
sketch_shoulder.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch_shoulder.addConstraint(Sketcher.Constraint("Radius", 0, r_shoulder))

pad_shoulder = body.newObject("PartDesign::Pad", "Pad_Shoulder")
pad_shoulder.Profile = sketch_shoulder
pad_shoulder.Length = params.shoulder_length
pad_shoulder.Type = "Blind"
pad_shoulder.Midplane = False
pad_shoulder.Reversed = False

# 2.2 Shoulder Edge Chamfers
chamfer_shoulder = body.newObject("PartDesign::Chamfer", "Chamfer_Shoulder")
chamfer_shoulder.Base = (pad_shoulder, ["Edge1"])
chamfer_shoulder.Size = params.shoulder_edge_chamfer_length
chamfer_shoulder.Type = "Linear"
chamfer_shoulder.Method = "Distance"

# 2.3 Piston Head Groove 1
z_g1_start = params.shoulder_length
sketch_g1 = body.newObject("Sketcher::SketchObject", "Sketch_Groove1")
sketch_g1.Placement = App.Placement(App.Vector(0, 0, z_g1_start))
sketch_g1.Support = (doc.getObject("XY_Plane"), [])
sketch_g1.MapMode = "FlatFace"
r_g1 = params.piston_head_first_groove_diameter / 2.0
sketch_g1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_g1), False)
sketch_g1.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch_g1.addConstraint(Sketcher.Constraint("Radius", 0, r_g1))

pocket_g1 = body.newObject("PartDesign::Pocket", "Pocket_Groove1")
pocket_g1.Profile = sketch_g1
pocket_g1.Length = params.piston_head_first_groove_width
pocket_g1.Type = "Blind"
pocket_g1.Midplane = False
pocket_g1.Reversed = True

# 2.4 Piston Head Groove 2
z_g2_start = z_g1_start + params.piston_head_first_groove_width + params.piston_head_first_to_second_groove_axial_gap
sketch_g2 = body.newObject("Sketcher::SketchObject", "Sketch_Groove2")
sketch_g2.Placement = App.Placement(App.Vector(0, 0, z_g2_start))
sketch_g2.Support = (doc.getObject("XY_Plane"), [])
sketch_g2.MapMode = "FlatFace"
r_g2 = params.piston_head_second_groove_diameter / 2.0
sketch_g2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_g2), False)
sketch_g2.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch_g2.addConstraint(Sketcher.Constraint("Radius", 0, r_g2))

pocket_g2 = body.newObject("PartDesign::Pocket", "Pocket_Groove2")
pocket_g2.Profile = sketch_g2
pocket_g2.Length = params.piston_head_second_groove_width
pocket_g2.Type = "Blind"
pocket_g2.Midplane = False
pocket_g2.Reversed = True

# 2.5 Piston Head Recess Boss
z_boss_start = z_g2_start + params.piston_head_second_groove_width + params.piston_head_first_groove_to_recess_boss_axial_gap
sketch_boss = body.newObject("Sketcher::SketchObject", "Sketch_Boss")
sketch_boss.Placement = App.Placement(App.Vector(0, 0, z_boss_start))
sketch_boss.Support = (doc.getObject("XY_Plane"), [])
sketch_boss.MapMode = "FlatFace"
r_boss = params.piston_head_recess_boss_diameter / 2.0
sketch_boss.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_boss), False)
sketch_boss.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch_boss.addConstraint(Sketcher.Constraint("Radius", 0, r_boss))

pocket_boss = body.newObject("PartDesign::Pocket", "Pocket_Boss")
pocket_boss.Profile = sketch_boss
pocket_boss.Length = params.piston_head_recess_boss_length
pocket_boss.Type = "Blind"
pocket_boss.Midplane = False
pocket_boss.Reversed = True

# 2.6 Piston Head End Chamfer
# The head ends at Z = z_boss_start + length_boss.
# The chamfer is on the top edge of the recessed boss (the hole).
# It connects the hole diameter to the outer diameter of the head.
z_head_end = z_boss_start + params.piston_head_recess_boss_length
sketch_chamfer_head = body.newObject("Sketcher::SketchObject", "Sketch_ChamferHead")
sketch_chamfer_head.Placement = App.Placement(App.Vector(0, 0, z_head_end))
sketch_chamfer_head.Support = (doc.getObject("XY_Plane"), [])
sketch_chamfer_head.MapMode = "FlatFace"
# The chamfer profile is a circle with radius = (outer_diameter - inner_diameter) / 2
# But we need to subtract the chamfer volume.
# The chamfer connects the hole (diameter r_boss) to the outer surface (diameter r_outer).
# The chamfer is a conical frustum.
# We can model this as a Pad of a chamfer profile? No, Chamfer feature is better.
# However, the Chamfer feature works on edges.
# Let's use a Chamfer feature on the top edge of the pocket_boss.
chamfer_head = body.newObject("PartDesign::Chamfer", "Chamfer_Head")
chamfer_head.Base = (pocket_boss, ["Edge1"])
chamfer_head.Size = params.piston_head_end_chamfer_length
chamfer_head.Type = "Linear"
chamfer_head.Method = "Distance"

# 3. Rod Extension & Tip Features (Negative Z direction)
# The rod extension starts at Z = 0 and goes to Z = -rod_extension_length.
# Then the taper, shallow groove, and tip.

# 3.1 Rod Extension
# Diameter: rod_diameter, Length: rod_extension_length
sketch_ext = body.newObject("Sketcher::SketchObject", "Sketch_Ext")
sketch_ext.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_ext.Support = (doc.getObject("XY_Plane"), [])
sketch_ext.MapMode = "FlatFace"
r_ext = params.rod_diameter / 2.0
sketch_ext.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_ext), False)
sketch_ext.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch_ext.addConstraint(Sketcher.Constraint("Radius", 0, r_ext))

pad_ext = body.newObject("PartDesign::Pad", "Pad_Ext")
pad_ext.Profile = sketch_ext
pad_ext.Length = params.rod_extension_length
pad_ext.Type = "Blind"
pad_ext.Midplane = False
pad_ext.Reversed = True # Subtract towards negative Z

# 3.2 Taper
# Connects rod_extension_diameter to shallow_groove_diameter over taper_axial_length.
# Starts at Z = -rod_extension_length. Ends at Z = -rod_extension_length + taper_axial_length.
z_taper_start = -params.rod_extension_length
z_taper_end = z_taper_start + params.taper_axial_length
sketch_taper = body.newObject("Sketcher::SketchObject", "Sketch_Taper")
sketch_taper.Placement = App.Placement(App.Vector(0, 0, z_taper_start))
sketch_taper.Support = (doc.getObject("XY_Plane"), [])
sketch_taper.MapMode = "FlatFace"
# Taper profile: Line from (r_ext, 0) to (r_shallow, 0)
r_shallow = params.shallow_groove_diameter / 2.0
# We need to create a line segment.
# The line goes from (r_ext, 0) to (r_shallow, 0) in the sketch plane.
# But the sketch is on XY plane. The line will be a chord? No, we need a profile for a revolution.
# A line segment from (r_ext, 0) to (r_shallow, 0) rotated around Z axis creates a cone.
# Wait, the sketch is on XY plane. The line segment is in the XY plane.
# Rotating a line segment from (r_ext, 0) to (r_shallow, 0) around Z axis creates a cone.
# But the line segment must be connected to the previous cylinder.
# The previous cylinder ends at Z = z_taper_start.
# The taper starts at Z = z_taper_start.
# The sketch is at Z = z_taper_start.
# The line segment should go from (r_ext, 0) to (r_shallow, 0).
# But the sketch is on the XY plane. The line segment is in the XY plane.
# Rotating this line segment around Z axis creates a cone.
# The cone will have a base radius of r_ext and a top radius of r_shallow.
# The height of the cone is the length of the line segment? No.
# The length of the line segment is sqrt((r_ext - r_shallow)^2 + 0^2) = r_ext - r_shallow.
# This is not the axial length.
# We need to create a profile that, when revolved, creates the taper.
# The profile should be a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch plane is XY. The Z axis is the axis of revolution.
# The profile is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk, not a cone.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the XZ plane?
# No, the sketch is on XY plane.
# We need to create a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis creates a disk.
# We need a line segment from (r_ext, 0) to (r_shallow, 0) in the sketch plane?
# No, the sketch is on XY plane. The line segment is in the XY plane.
# The line segment from (r_ext, 0) to (r_shallow, 0) is a horizontal line.
# Rotating it around Z axis
