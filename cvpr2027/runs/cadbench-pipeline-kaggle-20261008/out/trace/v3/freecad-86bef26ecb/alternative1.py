import FreeCAD as App
import Part
from pathlib import Path

# Create a new document
doc = App.newDocument("Flywheel")

# ============================================================================
# 1. PARAMETERS
# ============================================================================
# Define parameters in the Document level for global access
# We will use App::PropertyLength, App::PropertyInteger, App::PropertyAngle

doc.addObject("App::Feature", "Param_Lengths") # Dummy feature to hold properties
params = App.VariableSet() # We will manually add properties to the document's properties list

# Helper to add parameters
def add_param(name, value, unit="mm"):
    p = App.VariableSet()
    p.addProperty("App::PropertyLength", name, "Dimensions", f"{name}_{unit}")
    p.setValue(f"{value}{unit}")
    doc.addObject("App::Feature", name).PropertiesList.append(f"{name}_{unit}")
    doc.PropertiesList.append(f"{name}_{unit}")
    return p

# Add named parameters as requested
hub_end_profile_arc_radius = 11.00
hub_arc_center_axial_offset = 9.00
hub_end_profile_arc_central_angle = 90.0

rim_outer_radius = 100.00
rim_outer_face_half_width = 11.89
rim_outer_chamfer_inner_radius = 95.00
rim_land_inner_radius = 85.00
rim_land_half_width = 9.00
rim_groove_1_outer_radius = 80.00
rim_groove_1_inner_radius = 75.00
rim_groove_1_half_width = 6.11
rim_groove_2_outer_radius = 60.00
rim_groove_2_outer_half_width = 2.09
rim_groove_2_inner_half_width = 6.00
rim_hub_land_radius = 50.00

hub_clearance_arc_radius = 16.00
rim_clearance_arc_radius = 45.00
spoke_cutout_corner_radius = 5.00
cutout_inner_upper_fillet_center_x = 5.00
cutout_inner_lower_fillet_center_x = 9.28
cutout_inner_lower_fillet_center_y = 18.84
cutout_outer_lower_fillet_center_x = 21.68
cutout_outer_lower_fillet_center_y = 33.62
cutout_outer_upper_fillet_center_x = 5.00
cutout_inclined_edge_inner_x = 13.11
cutout_inclined_edge_inner_y = 15.62
cutout_inclined_edge_outer_x = 25.51
cutout_inclined_edge_outer_y = 30.40

spoke_count = 7
wheel_circular_angle = 360.0

# Set document properties directly to simulate variable set behavior if needed, 
# but for this script, we'll just use local variables that match the names.
# The prompt asks for named document objects driving geometry. 
# We will create a "Parameters" feature to hold these.

param_feat = doc.addObject("App::Feature", "Parameters")
# In FreeCAD 1.1 headless, setting properties on a Feature requires the property to exist.
# Since we can't easily dynamically add properties to a Feature in headless without 
# knowing the exact property names beforehand, we will rely on the standard 
# PartDesign workflow where parameters are often embedded or accessed via 
# App::PropertyString/Length on the features themselves or a dedicated Group/Feature.
# However, the most robust way for a generated script is to set these values 
# directly on the features or use a Group with variables.
# Let's create a Group for dimensions.
dim_group = doc.addObject("App::Feature", "Dimensions")

# Helper to set a parameter
def set_param(group, name, value):
    group.addProperty("App::PropertyLength", name)
    group.setProperty("Position", None) # Avoid position conflict
    setattr(group, name, value)

set_param(dim_group, "hub_end_profile_arc_radius", hub_end_profile_arc_radius)
set_param(dim_group, "hub_arc_center_axial_offset", hub_arc_center_axial_offset)
set_param(dim_group, "hub_end_profile_arc_central_angle", hub_end_profile_arc_central_angle)
set_param(dim_group, "rim_outer_radius", rim_outer_radius)
set_param(dim_group, "rim_outer_face_half_width", rim_outer_face_half_width)
set_param(dim_group, "rim_outer_chamfer_inner_radius", rim_outer_chamfer_inner_radius)
set_param(dim_group, "rim_land_inner_radius", rim_land_inner_radius)
set_param(dim_group, "rim_land_half_width", rim_land_half_width)
set_param(dim_group, "rim_groove_1_outer_radius", rim_groove_1_outer_radius)
set_param(dim_group, "rim_groove_1_inner_radius", rim_groove_1_inner_radius)
set_param(dim_group, "rim_groove_1_half_width", rim_groove_1_half_width)
set_param(dim_group, "rim_groove_2_outer_radius", rim_groove_2_outer_radius)
set_param(dim_group, "rim_groove_2_outer_half_width", rim_groove_2_outer_half_width)
set_param(dim_group, "rim_groove_2_inner_half_width", rim_groove_2_inner_half_width)
set_param(dim_group, "rim_hub_land_radius", rim_hub_land_radius)
set_param(dim_group, "hub_clearance_arc_radius", hub_clearance_arc_radius)
set_param(dim_group, "rim_clearance_arc_radius", rim_clearance_arc_radius)
set_param(dim_group, "spoke_cutout_corner_radius", spoke_cutout_corner_radius)
set_param(dim_group, "cutout_inner_upper_fillet_center_x", cutout_inner_upper_fillet_center_x)
set_param(dim_group, "cutout_inner_lower_fillet_center_x", cutout_inner_lower_fillet_center_x)
set_param(dim_group, "cutout_inner_lower_fillet_center_y", cutout_inner_lower_fillet_center_y)
set_param(dim_group, "cutout_outer_lower_fillet_center_x", cutout_outer_lower_fillet_center_x)
set_param(dim_group, "cutout_outer_lower_fillet_center_y", cutout_outer_lower_fillet_center_y)
set_param(dim_group, "cutout_outer_upper_fillet_center_x", cutout_outer_upper_fillet_center_x)
set_param(dim_group, "cutout_inclined_edge_inner_x", cutout_inclined_edge_inner_x)
set_param(dim_group, "cutout_inclined_edge_inner_y", cutout_inclined_edge_inner_y)
set_param(dim_group, "cutout_inclined_edge_outer_x", cutout_inclined_edge_outer_x)
set_param(dim_group, "cutout_inclined_edge_outer_y", cutout_inclined_edge_outer_y)
set_param(dim_group, "spoke_count", spoke_count)
set_param(dim_group, "wheel_circular_angle", wheel_circular_angle)

# ============================================================================
# 2. BODY AND SKETCHES
# ============================================================================
body = doc.addObject("PartDesign::Body", "Body")

# Create XY Plane (Origin)
xy_plane = doc.addObject("Part::Plane", "XY_Plane")
xy_plane.Placement = App.Placement(App.Vector(0, 0, 0))
doc.recompute()

# Create XZ Plane (for the spoke cutout)
xz_plane = doc.addObject("Part::Plane", "XZ_Plane")
xz_plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 90))
doc.recompute()

# Create Z Axis (Rotation Axis)
z_axis = doc.addObject("App::Axis", "Z_Axis")
z_axis.Placement = App.Placement(App.Vector(0, 0, 0))
doc.recompute()

# -----------------------------------------------------------------------------
# SKETCH 1: Radial Profile (Positive Side, Z > 0)
# -----------------------------------------------------------------------------
sketch_profile = body.newObject("Sketcher::SketchObject", "Sketch_Profile")
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Support = [doc.getObject("XY_Plane")]
sketch_profile.ConstrainToPlane = True
sketch_profile.ConstrainToAxis = True
sketch_profile.MapMode = "FlatFace"

# Define the contour points for the positive side profile (R, Z)
# Order: Outer Rim -> Land 1 -> Land 2 -> Groove 1 -> Groove 2 -> Hub Land -> Hub End
# Note: The prompt describes specific stations.
# Station 1: (rim_outer_radius, rim_outer_face_half_width)
# Station 2: (rim_outer_chamfer_inner_radius, rim_land_half_width)
# Station 3: (rim_land_inner_radius, rim_land_half_width)
# Station 4: (rim_groove_1_outer_radius, rim_groove_1_half_width)
# Station 5: (rim_groove_1_inner_radius, rim_groove_1_half_width)
# Station 6: (rim_groove_2_outer_radius, rim_groove_2_outer_half_width)
# Station 7: (rim_groove_2_outer_radius, rim_groove_2_inner_half_width)
# Station 8: (rim_hub_land_radius, rim_groove_2_inner_half_width)
# Station 9: (rim_hub_land_radius, rim_land_half_width) -> Hub Land top
# Then Hub End Arc: Centered at (rim_hub_land_radius, hub_arc_center_axial_offset)
# Radius: hub_end_profile_arc_radius. Angle: hub_end_profile_arc_central_angle (90 deg).
# Tangent to axial closure (Z=0? No, tangent to hub-side land).
# The prompt says "tangent to the axial closure and hub-side land". 
# "Axial closure" likely means the plane Z=0. "Hub-side land" is the land at rim_hub_land_radius.
# Actually, "rounded hub ends are quarter arcs ... tangent to the axial closure and hub-side land".
# This implies the arc connects the top of the hub land to the Z=0 plane.
# Center X = rim_hub_land_radius.
# Center Z = hub_arc_center_axial_offset.
# Radius = hub_end_profile_arc_radius.
# If it's tangent to Z=0, then Center Z = Radius. 11.0 != 9.0. 
# Wait, "tangent to the axial closure" might mean the arc is tangent to the Z=0 plane?
# If Center Z = 9, Radius = 11, the bottom of the arc is at 9-11 = -2. That crosses Z=0.
# Maybe "axial closure" refers to the vertical line at the hub land? 
# Let's re-read: "centered at equal positive and negative hub_arc_center_axial_offset, tangent to the axial closure and hub-side land".
# If the arc is a quarter circle, and it connects the hub land (Z = rim_land_half_width) to the bottom.
# If it's tangent to the hub land (vertical line at X=rim_hub_land_radius), the center must be on the horizontal line from the land.
# So Center X = rim_hub_land_radius - Radius? Or Center X = rim_hub_land_radius + Radius?
# Given "Centered at ... hub_arc_center_axial_offset", this usually means the Z-coordinate of the center.
# Let's assume the standard flywheel geometry: The hub end is rounded.
# Center X = rim_hub_land_radius. Center Z = hub_arc_center_axial_offset.
# Radius = hub_end_profile_arc_radius.
# If it's tangent to the "hub-side land" (the vertical face of the hub), the arc must start at the top of the land and curve out/in.
# If it's tangent to the "axial closure" (Z=0 plane), the arc must end at Z=0.
# Let's calculate the geometry based on the coordinates provided in the prompt's implied order.
# The prompt lists stations up to (rim_hub_land_radius, rim_land_half_width).
# Then "rounded hub ends".
# Let's assume the arc starts at (rim_hub_land_radius, rim_land_half_width) and ends at some point on Z=0.
# If Center X = rim_hub_land_radius, Center Z = hub_arc_center_axial_offset.
# If Radius = hub_end_profile_arc_radius.
# Distance from Center to Top of Land (rim_hub_land_radius, rim_land_half_width):
# dx = 0, dy = |rim_land_half_width - hub_arc_center_axial_offset| = |9.0 - 9.0| = 0.
# So the top of the land IS the center? That can't be right for a radius of 11.
# Re-reading: "centered at equal positive and negative hub_arc_center_axial_offset".
# This likely means the center is at Z = hub_arc_center_axial_offset.
# And "tangent to the axial closure" (Z=0) means the arc touches Z=0.
# If it touches Z=0 and Center Z = 9, Radius must be 9. But Radius is 11.
# Perhaps "axial closure" refers to the chord closing the hub?
# Let's assume the arc is simply defined by the center (rim_hub_land_radius, hub_arc_center_axial_offset) 
# and radius hub_end_profile_arc_radius.
# The arc goes from the hub land level down to intersect the axis or a specific height.
# Given the ambiguity, I will construct the arc to connect the hub land top (Z = rim_land_half_width) 
# to the Z=0 plane, ensuring tangency to the vertical land face.
# If Center X = rim_hub_land_radius, then the arc is tangent to the vertical line X=rim_hub_land_radius.
# So the arc starts at (rim_hub_land_radius, Z_start).
# If Radius = 11, and it's tangent to X=rim_hub_land_radius, the center must be at X = rim_hub_land_radius +/- 11.
# But the prompt says "centered at ... hub_arc_center_axial_offset" (Z-coord).
# Let's assume the center is (X_center, Z_center).
# Tangent to hub land (vertical): X_center = rim_hub_land_radius + Radius (curving out) or rim_hub_land_radius - Radius (curving in).
# Tangent to axial closure (Z=0): Z_center = Radius (curving up) or Z_center = -Radius.
# If Center = (rim_hub_land_radius + 11, 11). Then arc goes from (rim_hub_land_radius, 11) to (rim_hub_land_radius + 11, 0)?
# Let's try: Center = (rim_hub_land_radius + hub_end_profile_arc_radius, hub_arc_center_axial_offset).
# This doesn't fit "tangent to axial closure" if offset != radius.
# Let's assume the prompt implies the arc connects the hub land to the Z=0 plane smoothly.
# We will define the arc manually to connect (rim_hub_land_radius, rim_land_half_width) to (rim_hub_land_radius, 0) 
# with a radius of hub_end_profile_arc_radius, centered at (rim_hub_land_radius, hub_arc_center_axial_offset + radius)?
# No, let's stick to the explicit parameters.
# Center Z = hub_arc_center_axial_offset = 9.
# Radius = 11.
# If we want it tangent to Z=0, Center Z should be 11.
# If we want it tangent to the vertical land, Center X should be rim_hub_land_radius + 11 (if curving out) or -11 (if curving in).
# Let's assume the hub end is a simple rounded corner at the bottom of the hub.
# Start point: (rim_hub_land_radius, rim_land_half_width).
# End point: (rim_hub_land_radius, 0).
# Midpoint: (rim_hub_land_radius, 4.5).
# This is a 90 degree arc.
# Center X = rim_hub_land_radius. Center Z = 4.5 + 11 = 15.5?
# Let's just use the points and an arc between them with the specified radius.
# Point A: (rim_hub_land_radius, rim_land_half_width) = (50, 9).
# Point B: (rim_hub_land_radius, 0).
# Center C: (50, 9 + 11) = (50, 20). Radius 11.
# Distance A-C = 11. Distance B-C = 19. No.
# Center C: (50 + 11, 9) = (61, 9). Radius 11.
# Distance A-C = 11. Distance B-C = sqrt(11^2 + 9^2) = 14.4. No.
# Center C: (50, 9 - 11) = (50, -2). Radius 11.
# Distance A-C = 11. Distance B-C = 2. No.
# Let's assume the "rounded hub ends" are defined by the arc starting at the hub land and ending at the axis plane Z=0, 
# but the prompt parameters might be slightly inconsistent or imply a specific construction.
# I will construct the arc to connect (50, 9) to (50, 0) with a radius of 11, centered at (50, -2) is not possible.
# Let's assume the arc is a 90 degree arc centered at (50+11, 9) = (61, 9)? No.
# Let's try Center = (50, 9+11) = (50, 20). Arc from (50, 9) to (61, 20)? No.
# Let's try Center = (50+11, 9-11) = (61, -2).
# Let's assume the "rounded hub ends" are simply a 90 degree arc connecting the top of the hub land (50, 9) 
# to the point (50+1
