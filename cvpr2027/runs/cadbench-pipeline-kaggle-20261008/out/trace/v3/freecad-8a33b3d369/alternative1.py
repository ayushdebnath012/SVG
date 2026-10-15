import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Initialize Document
doc = App.newDocument("ServoBracket")
doc.Label = "ServoBracket_Assembly"

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

# Create Parameters Object
params = body.newObject("App::VarSet", "Parameters")

# Define Parameters
params.addProperty("App::PropertyLength", "bracket_overall_width", "Dimensions", "Overall width Z")
params.bracket_overall_width = 32.36

params.addProperty("App::PropertyLength", "bracket_flange_left_x", "Dimensions", "Datum X")
params.bracket_flange_left_x = -81.93

params.addProperty("App::PropertyLength", "bracket_flange_outer_y", "Dimensions", "Datum Y")
params.bracket_flange_outer_y = 47.38

params.addProperty("App::PropertyLength", "bracket_top_flange_length", "Dimensions", "Flange Length X")
params.bracket_top_flange_length = 57.0

params.addProperty("App::PropertyLength", "bracket_top_flange_thickness", "Dimensions", "Flange Thickness -Y")
params.bracket_top_flange_thickness = 3.99

params.addProperty("App::PropertyLength", "bracket_vertical_web_thickness", "Dimensions", "Web Thickness -X")
params.bracket_vertical_web_thickness = 2.0

params.addProperty("App::PropertyLength", "bracket_leg_length", "Dimensions", "Leg Length -Y")
params.bracket_leg_length = 66.99

params.addProperty("App::PropertyLength", "bracket_cutout_length", "Dimensions", "Cutout Length X")
params.bracket_cutout_length = 40.0

params.addProperty("App::PropertyLength", "bracket_cutout_width", "Dimensions", "Cutout Width Z")
params.bracket_cutout_width = 20.0

params.addProperty("App::PropertyLength", "bracket_cutout_depth", "Dimensions", "Cutout Depth -Y")
params.bracket_cutout_depth = 10.0

params.addProperty("App::PropertyLength", "bracket_mounting_hole_diameter", "Dimensions", "Mounting Hole Dia")
params.bracket_mounting_hole_diameter = 3.0

params.addProperty("App::PropertyLength", "bracket_left_mounting_hole_end_offset", "Dimensions", "Left Hole End Offset")
params.bracket_left_mounting_hole_end_offset = 4.8

params.addProperty("App::PropertyLength", "bracket_right_mounting_hole_end_offset", "Dimensions", "Right Hole End Offset")
params.bracket_right_mounting_hole_end_offset = 4.44

params.addProperty("App::PropertyLength", "servo_arm_plate_thickness", "Dimensions", "Plate Thickness X")
params.servo_arm_plate_thickness = 4.0

params.addProperty("App::PropertyLength", "servo_arm_attachment_to_round_center_length", "Dimensions", "Dist to Round Center")
params.servo_arm_attachment_to_round_center_length = 92.14

params.addProperty("App::PropertyLength", "servo_arm_mounting_hole_diameter", "Dimensions", "Servo Mount Dia")
params.servo_arm_mounting_hole_diameter = 4.2

params.addProperty("App::PropertyLength", "servo_attachment_left_hole_x_offset", "Dimensions", "Left Hole X Off")
params.servo_attachment_left_hole_x_offset = -12.0

params.addProperty("App::PropertyLength", "servo_attachment_horizontal_pair_y_offset", "Dimensions", "Horizontal Pair Y Off")
params.servo_attachment_horizontal_pair_y_offset = 0.0

params.addProperty("App::PropertyLength", "servo_attachment_vertical_pair_x_offset", "Dimensions", "Vertical Pair X Off")
params.servo_attachment_vertical_pair_x_offset = 0.01

params.addProperty("App::PropertyLength", "servo_attachment_top_hole_y_offset", "Dimensions", "Top Hole Y Off")
params.servo_attachment_top_hole_y_offset = 12.0

params.addProperty("App::PropertyLength", "servo_attachment_right_hole_x_offset", "Dimensions", "Right Hole X Off")
params.servo_attachment_right_hole_x_offset = 12.0

params.addProperty("App::PropertyLength", "servo_attachment_bottom_hole_y_offset", "Dimensions", "Bottom Hole Y Off")
params.servo_attachment_bottom_hole_y_offset = -12.0

params.addProperty("App::PropertyLength", "servo_center_bore_diameter", "Dimensions", "Center Bore Dia")
params.servo_center_bore_diameter = 3.10

params.addProperty("App::PropertyAngle", "servo_arm_semicircle_angle", "Dimensions", "Semicircle Angle")
params.servo_arm_semicircle_angle = 180.0

# --- Feature 1: L-Section Support ---
sketch_l = body.newObject("Sketcher::SketchObject", "Sketch_LSection")
sketch_l.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
sketch_l.ConstraintFixAtPlane = "XY_Plane"
sketch_l.MapMode = "PlaneOnPlane"
sketch_l.Plane = "XY_Plane"

# Add Geometry for L-Section
# Datum Point (0,0) is top-left outer corner.
# Flange: Extends +X by top_flange_length, -Y by top_flange_thickness
# Web: From end of flange, extends -Y by leg_length, -X by vertical_web_thickness

# Vertices:
# 1: (0, 0) - Top Left Outer
# 2: (top_flange_length, 0) - Top Right Outer
# 3: (top_flange_length, -top_flange_thickness) - Web Start Top
# 4: (top_flange_length - vertical_web_thickness, -top_flange_thickness) - Web Start Inner Top
# 5: (top_flange_length - vertical_web_thickness, -(top_flange_thickness + leg_length)) - Web End Inner
# 6: (0, -(top_flange_thickness + leg_length)) - Bottom Left Outer

l_geom = [
    Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.bracket_top_flange_length, 0, 0)),
    Part.LineSegment(App.Vector(params.bracket_top_flange_length, 0, 0), App.Vector(params.bracket_top_flange_length, -params.bracket_top_flange_thickness, 0)),
    Part.LineSegment(App.Vector(params.bracket_top_flange_length, -params.bracket_top_flange_thickness, 0), App.Vector(params.bracket_top_flange_length - params.bracket_vertical_web_thickness, -params.bracket_top_flange_thickness, 0)),
    Part.LineSegment(App.Vector(params.bracket_top_flange_length - params.bracket_vertical_web_thickness, -params.bracket_top_flange_thickness, 0), App.Vector(params.bracket_top_flange_length - params.bracket_vertical_web_thickness, -(params.bracket_top_flange_thickness + params.bracket_leg_length), 0)),
    Part.LineSegment(App.Vector(params.bracket_top_flange_length - params.bracket_vertical_web_thickness, -(params.bracket_top_flange_thickness + params.bracket_leg_length), 0), App.Vector(0, -(params.bracket_top_flange_thickness + params.bracket_leg_length), 0)),
    Part.LineSegment(App.Vector(0, -(params.bracket_top_flange_thickness + params.bracket_leg_length), 0), App.Vector(0, 0, 0)),
]

for seg in l_geom:
    sketch_l.addGeometry(seg, False)

sketch_l = sketch_l.update() # Update to add constraints

# Pad the L-Section
pad = body.newObject("PartDesign::Pad", "Pad_LSection")
pad.Profile = sketch_l
pad.Length = params.bracket_overall_width
pad.Midplane = False
pad.Reversed = False

# --- Feature 2: Blind Cutout ---
# Plane: Top surface of the flange (Z=0, Y = -top_flange_thickness, X varies)
# Wait, the flange is at Y=0 to Y=-thickness. Top surface is Y=0.
# The cutout opens from the outer surface of the top flange. 
# Datum (0,0,0) is top-left outer. So top surface is Y=0 plane.
# Cutout is centered along flange length and global Z.
# Length X: centered. Width Z: centered.

sketch_cutout = body.newObject("Sketcher::SketchObject", "Sketch_Cutout")
sketch_cutout.Placement = App.Placement(App.Vector(params.bracket_top_flange_length/2, 0, 0), App.Rotation()) # Centered in X
sketch_cutout.ConstraintFixAtPlane = "XY_Plane"
sketch_cutout.MapMode = "PlaneOnPlane"
sketch_cutout.Plane = "XY_Plane"

# Cutout Geometry: Rectangle
# Width X = bracket_cutout_length
# Width Z = bracket_cutout_width
# Centered at the sketch origin (which is centered on the flange length)
# Y=0 is the surface. We will create the shape and then pocket it.

cutout_geom = [
    Part.LineSegment(App.Vector(-params.bracket_cutout_length/2, -params.bracket_cutout_width/2, 0), App.Vector(params.bracket_cutout_length/2, -params.bracket_cutout_width/2, 0)),
    Part.LineSegment(App.Vector(params.bracket_cutout_length/2, -params.bracket_cutout_width/2, 0), App.Vector(params.bracket_cutout_length/2, params.bracket_cutout_width/2, 0)),
    Part.LineSegment(App.Vector(params.bracket_cutout_length/2, params.bracket_cutout_width/2, 0), App.Vector(-params.bracket_cutout_length/2, params.bracket_cutout_width/2, 0)),
    Part.LineSegment(App.Vector(-params.bracket_cutout_length/2, params.bracket_cutout_width/2, 0), App.Vector(-params.bracket_cutout_length/2, -params.bracket_cutout_width/2, 0)),
]

for seg in cutout_geom:
    sketch_cutout.addGeometry(seg, False)
sketch_cutout = sketch_cutout.update()

pocket_cutout = body.newObject("PartDesign::Pocket", "Pocket_Cutout")
pocket_cutout.Profile = sketch_cutout
pocket_cutout.Type = "Blind"
pocket_cutout.Depth = params.bracket_cutout_depth
pocket_cutout.Reversed = True # Remove material

# --- Feature 3: Mounting Holes ---
# Four holes in the cutout area.
# Columns near flange ends. Rows at 1/4 and 3/4 of cutout width.
# Flange length direction is X.
# Cutout is centered on flange.
# Left offset from left end of cutout: bracket_left_mounting_hole_end_offset
# Right offset from right end of cutout: bracket_right_mounting_hole_end_offset

# Center of cutout is at X = 0 (relative to sketch_cutout placement).
# Left edge of cutout: -cutout_length/2. Right edge: +cutout_length/2.
# Hole X centers:
# Left Column: -cutout_length/2 + left_offset
# Right Column: +cutout_length/2 - right_offset

# Rows: 1/4 and 3/4 of width from center (Z axis).
# Row 1 (Top/Z+): +width/4
# Row 2 (Bottom/Z-): -width/4

# We will create a sketch for holes and use holes feature, or create circles and pattern?
# Using Holes feature is cleaner for mounting holes.

# Let's define the hole positions relative to the cutout sketch plane.
# We can create a single sketch for all 4 holes, centered at cutout center.

sketch_holes = body.newObject("Sketcher::SketchObject", "Sketch_MountingHoles")
sketch_holes.Placement = App.Placement(App.Vector(params.bracket_top_flange_length/2, 0, 0), App.Rotation())
sketch_holes.ConstraintFixAtPlane = "XY_Plane"
sketch_holes.MapMode = "PlaneOnPlane"
sketch_holes.Plane = "XY_Plane"

# Calculate Hole Centers
left_col_x = -params.bracket_cutout_length/2 + params.bracket_left_mounting_hole_end_offset
right_col_x = params.bracket_cutout_length/2 - params.bracket_right_mounting_hole_end_offset
top_row_z = params.bracket_cutout_width/4
bottom_row_z = -params.bracket_cutout_width/4

# Left Top
sketch_holes.addGeometry(Part.Circle(App.Vector(left_col_x, 0, top_row_z), App.Vector(0, 0, 1), params.bracket_mounting_hole_diameter/2), False)
# Left Bottom
sketch_holes.addGeometry(Part.Circle(App.Vector(left_col_x, 0, bottom_row_z), App.Vector(0, 0, 1), params.bracket_mounting_hole_diameter/2), False)
# Right Top
sketch_holes.addGeometry(Part.Circle(App.Vector(right_col_x, 0, top_row_z), App.Vector(0, 0, 1), params.bracket_mounting_hole_diameter/2), False)
# Right Bottom
sketch_holes.addGeometry(Part.Circle(App.Vector(right_col_x, 0, bottom_row_z), App.Vector(0, 0, 1), params.bracket_mounting_hole_diameter/2), False)

sketch_holes = sketch_holes.update()

# Use PartDesign::Hole? Or Pocket?
# PartDesign::Hole is best.
hole_feature = body.newObject("PartDesign::Hole", "Holes_Mounting")
hole_feature.Profile = sketch_holes
hole_feature.Type = "CounterBore" # Standard threaded holes usually counterbore, but prompt says "blind bracket mounting holes". 
# If simple blind holes, use "Blind" and set Depth. If no depth specified other than "share that depth" (referring to cutout depth?), 
# Prompt: "Four equal blind bracket mounting holes share that depth". 
# "That depth" refers to bracket_cutout_depth (10.0mm).
hole_feature.Type = "Blind"
hole_feature.Depth = params.bracket_cutout_depth
hole_feature.Diameter = params.bracket_mounting_hole_diameter
hole_feature.CounterBoreDiameter = 0
hole_feature.CounterBoreDepth = 0
hole_feature.ThroughAll = False

# --- Feature 4: Servo Arm Plate ---
# Plane: Parallel to global Y-Z on the positive-X outer face of the web.
# Web is at X = top_flange_length - vertical_web_thickness.
# Outer face of web (positive X side): X = top_flange_length - vertical_web_thickness.
# Plane is Y-Z.
# Plate thickness centered across that face in global X.
# Thickness = servo_arm_plate_thickness.
# So Plate extends from X = web_face - thickness/2 to X = web_face + thickness/2.
# Web Face X = params.bracket_top_flange_length - params.bracket_vertical_web_thickness.

web_face_x = params.bracket_top_flange_length - params.bracket_vertical_web_thickness

# Sketch Plane: Y-Z plane at X = web_face_x.
sketch_plate = body.newObject("Sketcher::SketchObject", "Sketch_ServoPlate")
sketch_plate.Placement = App.Placement(App.Vector(web_face_x, 0, 0), App.Rotation(App.Rotation().getAngleAxis(0, App.Vector(1, 0, 0)))) # Rotate 90 deg around X? No.
# We need a plane where X is normal.
# FreeCAD XY_Plane has Z normal. XZ has Y normal. YZ has X normal.
# We need a plane at X = web_face_x. The plane itself is the YZ plane.
# In PartDesign, we can use the YZ_Plane and offset the sketch origin? 
# Or use a custom plane. Easiest is to use YZ_Plane and set the sketch placement offset.
# But YZ_Plane is at X=0. We need it at X=web_face_x.
# So: Plane = YZ_Plane, Placement = Placement(web_face_x, 0, 0) with no rotation?
# Wait, if Plane is YZ_Plane, its normal is X. The sketch lies in Y-Z.
# So we just offset the sketch placement X coordinate.
# However, the default YZ_Plane in FreeCAD is centered at 0. 
# Let's try: Plane = "YZ_Plane", Placement = App.Placement(web_face_x, 0, 0)
# This places the sketch on the YZ plane at X=web_face_x.

sketch_plate.Placement = App.Placement(App.Vector(web_face_x, 0, 0), App.Rotation())
sketch_plate.ConstraintFixAtPlane = "YZ_Plane"
sketch_plate.MapMode = "PlaneOnPlane"
sketch_plate.Plane = "YZ_Plane"

# Geometry in Plate Plane (u=Y, v=Z)
# Attachment Edge: Spans full bracket width at the top-flange outer level.
# Top-flange outer level is Y = 0 (relative to bracket datum).
# Bracket width is bracket_overall_width (Z direction).
# So line at Y=0, Z from -width/2 to +width/2.

# Free end: Semicircular end.
# Center of semicircle: 
# u (Y) = bracket_flange_outer_y - servo_arm_attachment_to_round_center_length
# v (Z) = bracket_overall_width / 2
# Diameter = bracket_overall_width.
# Angle = servo_arm_semicircle_angle (180).
# Tangent sides connect to attachment region.

u_center = params.bracket_flange_outer_y - params.servo_arm_attachment_to_round_center_length
v_center = params.bracket_overall_width / 2

# The semicircle is tangent to the attachment line (Y
