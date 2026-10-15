import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("CoaxialPin")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

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
# We will use a line segment for the profile to make the Pad easier to control, 
# but a circle is more robust for the rod itself. Let's use a circle.
# Actually, for a Pad to work well with a circle, we need to ensure the circle is the profile.
# Let's create a circle centered at (0,0,0) with radius = rod_diameter/2.
r_rod = params.rod_diameter / 2.0
sketch_rod.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_rod), False)

# Constraint: Center on origin
sketch_rod.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch_rod.addConstraint(Sketcher.Constraint("Radius", 0, r_rod))

# Pad the rod to define the full length.
# Length = rod_length.
# The pad will create the solid cylinder.
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
# This is a Pad expanding the rod.
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
# Chamfer the edges created by the shoulder pad.
# The shoulder pad creates a cylinder of diameter shoulder_diameter.
# The edges are at Z = shoulder_length.
chamfer_shoulder = body.newObject("PartDesign::Chamfer", "Chamfer_Shoulder")
chamfer_shoulder.Base = (pad_shoulder, ["Edge1"]) # Edge1 is the top edge of the shoulder
chamfer_shoulder.Size = params.shoulder_edge_chamfer_length
chamfer_shoulder.Type = "Linear"
chamfer_shoulder.Method = "Distance"

# 2.3 Piston Head Groove 1
# Diameter: piston_head_first_groove_diameter, Width: piston_head_first_groove_width
# Starts at Z = shoulder_length.
# We need to subtract material.
# Profile: Circle with radius = (piston_head_first_groove_diameter / 2)
# Position: Z = shoulder_length
# Note: The sketch needs to be on the face of the shoulder.
# Since the shoulder is a cylinder, we can sketch on the top face (Z=shoulder_length).
# However, PartDesign sketches are usually on planes. We can use the XY plane and offset the sketch.
# Or we can use the "Offset" property of the sketch.
# Let's use the XY plane and offset the sketch by shoulder_length.

sketch_g1 = body.newObject("Sketcher::SketchObject", "Sketch_Groove1")
sketch_g1.Placement = App.Placement(App.Vector(0, 0, params.shoulder_length))
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
pocket_g1.Reversed = True # Subtract

# 2.4 Piston Head Groove 2
# Starts after gap from end of Groove 1.
# Z_start = shoulder_length + width_g1 + gap_g1_to_g2
# Diameter: piston_head_second_groove_diameter, Width: piston_head_second_groove_width

z_g2_start = params.shoulder_length + params.piston_head_first_groove_width + params.piston_head_first_to_second_groove_axial_gap
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
# Starts after gap from end of Groove 2.
# Z_start = z_g2_start + width_g2 + gap_g2_to_boss
# Diameter: piston_head_recess_boss_diameter, Length: piston_head_recess_boss_length
# This is a subtractive feature (Pocket) to create a recess.

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
# The outer diameter is piston_head_outer_diameter.
# The chamfer connects the outer diameter to the recess boss diameter? 
# No, the description says: "The terminal boss ends with an equal-length edge chamfer."
# And "All groove transitions are tangent... using specified inner and outer fillet radii."
# The head lands use piston_head_outer_diameter.
# So the chamfer is on the top edge of the piston head (outer diameter).
# It connects the outer diameter to the recess boss diameter? 
# Wait, the recess boss is a hole in the head. The head lands are the material between the grooves and the boss.
# The "terminal boss" is the recessed portion.
# The chamfer is on the top edge of the piston head.
# The top edge of the piston head is at Z = z_boss_start + length_boss.
# The diameter at this edge is piston_head_outer_diameter.
# The chamfer connects this edge to the recess boss diameter? 
# Usually, a chamfer on a boss connects the outer surface to the inner surface of the boss.
# Let's assume the chamfer is on the top face of the piston head, connecting the outer rim to the recess boss.
# But the recess boss is a hole. The chamfer would be on the top edge of the hole? 
# Or is the "terminal boss" a raised feature? 
# "The recessed terminal boss begins after... and its far edge is the terminal end of the piston head."
# This implies the boss is a hole (recess).
# "The terminal boss ends with an equal-length edge chamfer."
# This likely means the top edge of the recessed boss (the hole) has a chamfer.
# The hole diameter is piston_head_recess_boss_diameter.
# The chamfer connects the hole diameter to the outer diameter of the head? 
# Or does it connect the hole diameter to the bottom of the head? 
# Given "edge chamfer", it's likely on the top edge of the hole.
# Let's apply a chamfer to the top edge of the pocket_boss.
# The pocket_boss creates a hole of diameter piston_head_recess_boss_diameter.
# The chamfer should be on the top edge of this hole.
# The chamfer size is params.piston_head_end_chamfer_length.
# The chamfer connects the hole diameter to the outer diameter? 
# If the chamfer is on the top edge of the hole, it connects the hole diameter to the outer diameter of the head.
# Let's assume the chamfer is on the top edge of the pocket_boss.
# The edge is the top edge of the hole.
# The chamfer will connect the hole diameter to the outer diameter of the head.
# Wait, the pocket_boss is a hole. The top edge of the hole is at Z = z_boss_start + length_boss.
# The chamfer will be on this edge.
# The chamfer size is params.piston_head_end_chamfer_length
