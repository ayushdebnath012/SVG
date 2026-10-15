import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("WheelHubMotor")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We will store parameters in a VarSet object to keep the tree clean and editable
params = body.newObject("App::VarSet", "Parameters")

# Axial Stations (Z coordinates)
params.addProperty("App::PropertyLength", "left_axial_tip", "Stations", "Leftmost tip")
params.left_axial_tip = -11.75
params.addProperty("App::PropertyLength", "right_axial_tip", "Stations", "Rightmost tip")
params.right_axial_tip = 188.25

params.addProperty("App::PropertyLength", "housing_left_axial_station", "Stations", "Start of housing")
params.housing_left_axial_station = 60.75
params.addProperty("App::PropertyLength", "housing_right_axial_station", "Stations", "End of housing")
params.housing_right_axial_station = 101.75

params.addProperty("App::PropertyLength", "left_shaft_shoulder_axial_station", "Stations", "Shaft shoulder start")
params.left_shaft_shoulder_axial_station = 28.25
params.addProperty("App::PropertyLength", "left_collar_inner_axial_station", "Stations", "Collar inner start")
params.left_collar_inner_axial_station = 30.75
params.addProperty("App::PropertyLength", "left_collar_lip_end_axial_station", "Stations", "Collar lip end")
params.left_collar_lip_end_axial_station = 34.25
params.addProperty("App::PropertyLength", "left_collar_outer_axial_station", "Stations", "Collar outer end")
params.left_collar_outer_axial_station = 35.25
params.addProperty("App::PropertyLength", "left_taper_start_axial_station", "Stations", "Taper start")
params.left_taper_start_axial_station = 35.40
params.addProperty("App::PropertyLength", "left_taper_end_axial_station", "Stations", "Taper end")
params.left_taper_end_axial_station = 46.75
params.addProperty("App::PropertyLength", "left_housing_neck_transition_axial_station", "Stations", "Neck transition")
params.left_housing_neck_transition_axial_station = 49.75
params.addProperty("App::PropertyLength", "left_flange_shoulder_transition_axial_station", "Stations", "Flange shoulder transition")
params.left_flange_shoulder_transition_axial_station = 53.75
params.addProperty("App::PropertyLength", "left_flange_outer_face_axial_station", "Stations", "Flange outer face")
params.left_flange_outer_face_axial_station = 54.75
params.addProperty("App::PropertyLength", "left_flange_inner_face_axial_station", "Stations", "Flange inner face")
params.left_flange_inner_face_axial_station = 59.75

params.addProperty("App::PropertyLength", "right_housing_neck_axial_station", "Stations", "Right neck start")
params.right_housing_neck_axial_station = 115.75
params.addProperty("App::PropertyLength", "right_taper_end_axial_station", "Stations", "Right taper end")
params.right_taper_end_axial_station = 117.27
params.addProperty("App::PropertyLength", "right_land_start_axial_station", "Stations", "Right land start")
params.right_land_start_axial_station = 118.75
params.addProperty("App::PropertyLength", "right_bearing_shoulder_axial_station", "Stations", "Right bearing shoulder")
params.right_bearing_shoulder_axial_station = 127.75
params.addProperty("App::PropertyLength", "right_shaft_shoulder_axial_station", "Stations", "Right shaft shoulder")
params.right_shaft_shoulder_axial_station = 155.75
params.addProperty("App::PropertyLength", "right_flange_inner_face_axial_station", "Stations", "Right flange inner")
params.right_flange_inner_face_axial_station = 102.75
params.addProperty("App::PropertyLength", "right_flange_outer_face_axial_station", "Stations", "Right flange outer")
params.right_flange_outer_face_axial_station = 107.75

params.addProperty("App::PropertyLength", "left_collar_base_transition_axial_station", "Stations", "Collar base transition")
params.left_collar_base_transition_axial_station = 31.25
params.addProperty("App::PropertyLength", "left_collar_outer_transition_axial_station", "Stations", "Collar outer transition")
params.left_collar_outer_transition_axial_station = 35.75

params.addProperty("App::PropertyLength", "right_flange_inner_rim_axial_station", "Stations", "Right rim inner")
params.right_flange_inner_rim_axial_station = 103.25
params.addProperty("App::PropertyLength", "right_flange_outer_rim_axial_station", "Stations", "Right rim outer")
params.right_flange_outer_rim_axial_station = 105.75
params.addProperty("App::PropertyLength", "right_flange_shoulder_transition_axial_station", "Stations", "Right shoulder transition")
params.right_flange_shoulder_transition_axial_station = 108.75
params.addProperty("App::PropertyLength", "right_housing_neck_transition_axial_station", "Stations", "Right neck transition")
params.right_housing_neck_transition_axial_station = 112.75

params.addProperty("App::PropertyLength", "left_flange_outer_rim_axial_station", "Stations", "Left rim outer")
params.left_flange_outer_rim_axial_station = 56.75
params.addProperty("App::PropertyLength", "flange_outer_rim_radial_station", "Stations", "Rim outer radius")
params.flange_outer_rim_radial_station = 67.50
params.addProperty("App::PropertyLength", "left_flange_inner_rim_axial_station", "Stations", "Left rim inner")
params.left_flange_inner_rim_axial_station = 59.25
params.addProperty("App::PropertyLength", "flange_inner_rim_radial_station", "Stations", "Rim inner radius")
params.flange_inner_rim_radial_station = 69.00

params.addProperty("App::PropertyLength", "flange_shoulder_transition_radial_station", "Stations", "Shoulder transition radius")
params.flange_shoulder_transition_radial_station = 61.00

# Radii
params.addProperty("App::PropertyLength", "shaft_radius", "Radii", "Shaft radius")
params.shaft_radius = 6.00
params.addProperty("App::PropertyLength", "shaft_shoulder_radius", "Radii", "Shaft shoulder radius")
params.shaft_shoulder_radius = 10.00

params.addProperty("App::PropertyLength", "left_collar_base_radius", "Radii", "Collar base radius")
params.left_collar_base_radius = 26.58
params.addProperty("App::PropertyLength", "left_collar_lip_radius", "Radii", "Collar lip radius")
params.left_collar_lip_radius = 27.08
params.addProperty("App::PropertyLength", "left_collar_outer_radius", "Radii", "Collar outer radius")
params.left_collar_outer_radius = 36.15

params.addProperty("App::PropertyLength", "left_taper_start_radius", "Radii", "Taper start radius")
params.left_taper_start_radius = 36.50
params.addProperty("App::PropertyLength", "left_taper_end_radius", "Radii", "Taper end radius")
params.left_taper_end_radius = 47.85
params.addProperty("App::PropertyLength", "left_housing_neck_radius", "Radii", "Left housing neck radius")
params.left_housing_neck_radius = 57.00

params.addProperty("App::PropertyLength", "housing_outer_radius", "Radii", "Housing outer radius")
params.housing_outer_radius = 60.00
params.addProperty("App::PropertyLength", "flange_outer_radius", "Radii", "Flange outer radius")
params.flange_outer_radius = 69.50

params.addProperty("App::PropertyLength", "housing_end_transition_fillet_radius", "Radii", "Housing end fillet")
params.housing_end_transition_fillet_radius = 3.00
params.addProperty("App::PropertyLength", "flange_shoulder_fillet_radius", "Radii", "Flange shoulder fillet")
params.flange_shoulder_fillet_radius = 1.00
params.addProperty("App::PropertyLength", "flange_outer_corner_fillet_radius", "Radii", "Flange outer corner fillet")
params.flange_outer_corner_fillet_radius = 2.00
params.addProperty("App::PropertyLength", "flange_inner_corner_fillet_radius", "Radii", "Flange inner corner fillet")
params.flange_inner_corner_fillet_radius = 0.50

params.addProperty("App::PropertyLength", "right_housing_neck_inner_radius", "Radii", "Right neck inner")
params.right_housing_neck_inner_radius = 22.00
params.addProperty("App::PropertyLength", "right_housing_neck_outer_radius", "Radii", "Right neck outer")
params.right_housing_neck_outer_radius = 57.00
params.addProperty("App::PropertyLength", "right_taper_end_radius", "Radii", "Right taper end radius")
params.right_taper_end_radius = 20.00
params.addProperty("App::PropertyLength", "right_bearing_shoulder_radius", "Radii", "Right bearing shoulder radius")
params.right_bearing_shoulder_radius = 17.00

params.addProperty("App::PropertyLength", "mounting_bolt_circle_radius", "Radii", "Bolt circle radius")
params.mounting_bolt_circle_radius = 63.25
params.addProperty("App::PropertyLength", "mounting_hole_diameter", "Radii", "Mounting hole diameter")
params.mounting_hole_diameter = 2.60

params.addProperty("App::PropertyLength", "right_cutout_width", "Radii", "Right cutout width")
params.right_cutout_width = 2.00
params.addProperty("App::PropertyLength", "right_cutout_height", "Radii", "Right cutout height")
params.right_cutout_height = 10.28
params.addProperty("App::PropertyLength", "right_cutout_lower_transverse_coordinate", "Radii", "Right cutout Y offset")
params.right_cutout_lower_transverse_coordinate = -5.14
params.addProperty("App::PropertyLength", "right_cutout_depth", "Radii", "Right cutout depth")
params.right_cutout_depth = 32.50

params.addProperty("App::PropertyLength", "left_cutout_width", "Radii", "Left cutout width")
params.left_cutout_width = 2.00
params.addProperty("App::PropertyLength", "left_cutout_height", "Radii", "Left cutout height")
params.left_cutout_height = 20.00
params.addProperty("App::PropertyLength", "left_cutout_depth", "Radii", "Left cutout depth")
params.left_cutout_depth = 40.00

params.addProperty("App::PropertyLength", "flange_rim_transition_entry_angle", "Angles", "Rim entry angle")
params.flange_rim_transition_entry_angle = 0.0
params.addProperty("App::PropertyLength", "flange_shoulder_transition_exit_angle", "Angles", "Shoulder exit angle")
params.flange_shoulder_transition_exit_angle = 270.0
params.addProperty("App::PropertyLength", "left_collar_outer_transition_angle", "Angles", "Collar outer transition angle")
params.left_collar_outer_transition_angle = 135.0

params.addProperty("App::PropertyLength", "cutout_pair_negative_edge_offset", "Radii", "Cutout pair offset")
params.cutout_pair_negative_edge_offset = -7.00
params.addProperty("App::PropertyLength", "mounting_pattern_axis_offset", "Radii", "Mounting pattern offset")
params.mounting_pattern_axis_offset = 0.00

params.addProperty("App::PropertyInteger", "number_of_mounting_holes", "Counts", "Number of holes")
params.number_of_mounting_holes = 18
params.addProperty("App::PropertyInteger", "rectangular_cutout_count", "Counts", "Number of cutouts")
params.rectangular_cutout_count = 2

# --- Sketch 1: Main Profile ---
# This sketch defines the half-profile (X >= 0) in the XZ plane.
# We will use the YZ plane for the sketch to make X the radial dimension and Z the axial dimension.
# Wait, standard convention: Sketch on YZ plane -> X is normal (Radial), Y is Axial? 
# Let's stick to the prompt's implied coordinate system: 
# "Axial stations are measured from the hub-axis datum, radial dimensions are measured outward from that axis"
# Let's put the sketch on the XZ plane (Y=0). X = Radius, Z = Axial.
# However, FreeCAD Sketcher on XZ plane usually has X as horizontal, Z as vertical.
# Let's use the XZ plane. X = Radius, Z = Axial.

sketch_profile = body.newObject("Sketcher::SketchObject", "ProfileSketch")
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Support = [App.getDocument("WheelHubMotor").getObject("XY_Plane")] # Actually XY is X,Y. We need XZ.
# Let's use the standard planes. XY is Z=0. XZ is Y=0. YZ is X=0.
# We want X=Radius, Z=Axial. So we sketch on XZ plane (Y=0).
# But the default Support for a new sketch is the first plane found. 
# Let's explicitly set it to XZ_Plane.
sketch_profile.Support = [App.getDocument("WheelHubMotor").getObject("XZ_Plane")]
sketch_profile.MapMode = "FlatFace"
sketch_profile.ConstrainToCurrentPlane = True

# Helper to add line segments
def add_line(sk, p1, p2, constr_type="Horizontal", constr_val=None):
    # p1, p2 are (x, z)
    sk.addGeometry(Part.LineSegment(App.Vector(p1[0], 0, p1[1]), App.Vector(p2[0], 0, p2[1])))
    # Constraints
    # We need to constrain points to axes or each other.
    # Point 1: (0,0)
    # Point 2: (R, Z)
    # We will add constraints manually for robustness.
    pass

# Define the profile points (X=Radius, Z=Axial)
# Start at Left Tip (0, -11.75)
# 1. Shaft (0, -11.75) to (6, -11.75) -> Radius 6
# 2. Shaft Shoulder (6, -11.75) to (6, 28.25) -> Radius 6, Z to 28.25
# 3. Collar Base (6, 28.25) to (26.58, 28.25) -> Z 28.25, R to 26.58
# 4. Collar Base Transition (26.58, 28.25) to (28.08, 31.25) -> 90 deg quadrant? 
#    Prompt: "rounded transition is either a 90-degree quadrant from a radial to an axial tangent"
#    From Radial (horizontal) to Axial (vertical). 
#    Start (26.58, 28.25). End (28.08, 31.25).
#    dx = 1.5, dz = 3.0. Slope = 2. Not 90 deg.
#    Wait, "radial to an axial tangent". 
#    If we are moving from a vertical cylinder (collar base) to a slanted surface?
#    No, collar base is vertical (constant R). Then we go to a slanted surface?
#    Actually, the collar base is a cylinder. The next feature is the collar lip?
#    "The collar rises from left_collar_base_radius through its named lip and outer stations"
#    This implies the collar is a stepped cylinder.
#    Let's re-read carefully: "The collar rises from left_collar_base_radius ... through its named lip and outer stations"
#    This suggests the collar is a cylinder of radius left_collar_base_radius up to some point, then steps up?
#    Or is it a conical transition?
#    "Every named straight, tapered, and cylindrical segment is joined tangentially by the applicable transition radius"
#    So:
#    1. Shaft (R=6) to Shaft Shoulder (R=10). Tangent? No, step.
#    2. Shaft Shoulder (R=10) to Collar Base (R=26.58). Step.
#    3. Collar Base (R=26.58) to Collar Lip (R=27.08). Step?
#    4. Collar Lip (R=27.08) to Collar Outer (R=36.15). Step?
#    The prompt says "joined tangentially by the applicable
