import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("PulleyWheel")

# --- Parameters ---
# Define parameters as App::PropertyLength or similar to keep them editable
# We will use a VarSet to hold the parameters and reference them in expressions
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "center_bore_diameter", "Dimensions", "25.0")
params.addProperty("App::PropertyLength", "hub_outer_diameter", "Dimensions", "40.0")
params.addProperty("App::PropertyLength", "pulley_outer_diameter", "Dimensions", "195.0")
params.addProperty("App::PropertyLength", "pulley_overall_width", "Dimensions", "95.0")
params.addProperty("App::PropertyLength", "hub_axial_width", "Dimensions", "55.0")
params.addProperty("App::PropertyLength", "center_bore_axial_depth", "Dimensions", "70.0")
params.addProperty("App::PropertyLength", "inner_web_small_diameter", "Dimensions", "131.54")
params.addProperty("App::PropertyLength", "inner_web_large_diameter", "Dimensions", "147.54")
params.addProperty("App::PropertyLength", "rim_inner_small_diameter", "Dimensions", "144.0")
params.addProperty("App::PropertyLength", "rim_inner_large_diameter", "Dimensions", "160.0")
params.addProperty("App::PropertyLength", "pulley_base_plate_thickness", "Dimensions", "20.0")
params.addProperty("App::PropertyInteger", "number_of_mounting_lugs", "Mounting", "2")
params.addProperty("App::PropertyInteger", "number_of_mounting_holes", "Mounting", "2")
params.addProperty("App::PropertyLength", "mounting_hole_diameter", "Mounting", "15.0")
params.addProperty("App::PropertyLength", "mounting_hole_center_half_spacing", "Mounting", "47.5")
params.addProperty("App::PropertyLength", "mounting_lug_outer_arc_radius", "Mounting", "17.0")
params.addProperty("App::PropertyLength", "mounting_lug_outer_arc_central_angle", "Mounting", "17.0") # 180 deg in radians approx 3.14, but let's use a length property for angle in degrees if possible, or just hardcode logic. 
# Note: PartDesign features usually take angles in degrees for some, but internal math is radians. 
# However, App::PropertyLength is for length. Let's use App::PropertyLength for the radius and store angle in a separate property or just use a fixed value if the API doesn't support degrees directly in a length property.
# Actually, let's use App::PropertyLength for the radius and App::PropertyLength for the angle (storing degrees) is not standard. 
# Standard is App::PropertyLength for length. For angles, we often use App::PropertyLength and divide by 180/pi or just use a number.
# Let's create specific properties for angles in degrees.
params.addProperty("App::PropertyLength", "mounting_lug_outer_arc_central_angle_deg", "Mounting", "180.0")
params.addProperty("App::PropertyLength", "mounting_lug_fillet_radius", "Mounting", "13.0")
params.addProperty("App::PropertyLength", "mounting_lug_fillet_central_angle_deg", "Mounting", "90.0")
params.addProperty("App::PropertyLength", "central_web_half_length", "Mounting", "25.0")
params.addProperty("App::PropertyLength", "central_web_outer_half_height", "Mounting", "34.5")
params.addProperty("App::PropertyLength", "lug_plate_attachment_y", "Mounting", "-55.0")
params.addProperty("App::PropertyLength", "lug_plate_pad_depth", "Mounting", "20.0")

# --- Body Setup ---
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Global Planes ---
# We need XY (X-Z plane), XZ (X-Y plane), YZ (Y-Z plane)
# FreeCAD default planes:
# XY_Plane: X-Y plane (Z=0) -> Normal Z
# XZ_Plane: X-Z plane (Y=0) -> Normal Y
# YZ_Plane: Y-Z plane (X=0) -> Normal X

# We will create sketches on these planes.
# Wheel Axis is Global Y.
# Front Plane is Y = 0 (X-Z plane).
# Rear Plane is Y = -pulley_overall_width (X-Z plane).

# Create Plane Objects if they don't exist (usually they do in a new doc, but let's be safe)
# Actually, in a new document, XY_Plane, XZ_Plane, YZ_Plane exist.
# Let's verify or create them.
for name in ["XY_Plane", "XZ_Plane", "YZ_Plane"]:
    if not doc.getObject(name):
        plane = doc.addObject("PartDesign::Plane", name)
        plane.Placement = App.Placement(App.Vector(0, 0, 0))
        plane.Placement = App.Placement(App.Vector(0, 0, 0)) # Reset
        # Default placements:
        # XY_Plane: X-Y plane
        # XZ_Plane: X-Z plane
        # YZ_Plane: Y-Z plane
        # We need to ensure they are standard.
        if name == "XY_Plane": plane.Placement = App.Placement(App.Vector(0, 0, 0))
        if name == "XZ_Plane": plane.Placement = App.Placement(App.Vector(0, 0, 0))
        if name == "YZ_Plane": plane.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Feature 1: Hub Bore (Front) ---
# Sketch on XZ_Plane (Y=0)
sketch_hub_front = body.newObject("Sketcher::SketchObject", "Sketch_Hub_Front")
sketch_hub_front.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_hub_front.AttachmentSupport = (doc.getObject("XZ_Plane"), [])
sketch_hub_front.ConstrainToCurrentPlane = True
sketch_hub_front.MapMode = "FlatFace"

# Hub Outer Circle
sketch_hub_front.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hub_outer_diameter.Value / 2.0), False)
# Bore Circle
sketch_hub_front.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.center_bore_diameter.Value / 2.0), False)

# Constraints
sketch_hub_front.addConstraint(Sketcher.Constraint("Center", 0, 1)) # Center of outer
sketch_hub_front.addConstraint(Sketcher.Constraint("Center", 0, 2)) # Center of inner
sketch_hub_front.addConstraint(Sketcher.Constraint("Radius", 0, 1, params.hub_outer_diameter.Value / 2.0))
sketch_hub_front.addConstraint(Sketcher.Constraint("Radius", 0, 2, params.center_bore_diameter.Value / 2.0))
sketch_hub_front.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Concentric

# Pad the hub bore rearward
pad_hub = body.newObject("PartDesign::Pad", "Pad_Hub_Bore")
pad_hub.Profile = sketch_hub_front
pad_hub.Length = params.center_bore_axial_depth.Value
pad_hub.Type = "Blind"
pad_hub.Reverse = True # Pad in negative Y
pad_hub.MidPlane = False

# --- Feature 2: Web Transition (Front to Rear) ---
# The web starts at the hub outer diameter and goes to inner_web_small_diameter at the rear plane.
# We need a sketch at the rear plane (Y = -pulley_overall_width).
# However, the prompt says: "The bore wall continues rearward... where the section extends outward to inner_web_small_diameter. A straight web transition then reaches rim_inner_small_diameter at the rear plane".
# This implies the web profile is defined at the rear plane.
# Let's create a sketch at the rear plane.

rear_plane_y = -params.pulley_overall_width.Value
sketch_web_rear = body.newObject("Sketcher::SketchObject", "Sketch_Web_Rear")
sketch_web_rear.Placement = App.Placement(App.Vector(0, rear_plane_y, 0))
sketch_web_rear.AttachmentSupport = (doc.getObject("XZ_Plane"), [])
sketch_web_rear.MapMode = "FlatFace"

# Profile at rear plane:
# Inner radius: inner_web_small_diameter / 2
# Outer radius: rim_inner_small_diameter / 2
# Wait, the prompt says: "reaches rim_inner_small_diameter at the rear plane".
# And "The outer rim is defined by pulley_outer_diameter and extends forward from the rear plane to its front shoulder."
# So at the rear plane, we have the inner web diameter and the start of the outer rim.
# Let's define the profile at the rear plane.
# Inner arc: inner_web_small_diameter / 2
# Outer arc: rim_inner_small_diameter / 2
# But wait, the prompt says "straight web transition then reaches rim_inner_small_diameter at the rear plane".
# This implies the web thickness changes from (hub_outer - bore) to (rim_inner_small - bore)?
# No, the web is the material between the hub and the rim.
# Let's assume the profile at the rear plane is an annulus from inner_web_small_diameter to rim_inner_small_diameter.
# Then the outer rim extends forward from here.

sketch_web_rear.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_web_small_diameter.Value / 2.0), False)
sketch_web_rear.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.rim_inner_small_diameter.Value / 2.0), False)
sketch_web_rear.addConstraint(Sketcher.Constraint("Center", 0, 1))
sketch_web_rear.addConstraint(Sketcher.Constraint("Center", 0, 2))
sketch_web_rear.addConstraint(Sketcher.Constraint("Radius", 0, 1, params.inner_web_small_diameter.Value / 2.0))
sketch_web_rear.addConstraint(Sketcher.Constraint("Radius", 0, 2, params.rim_inner_small_diameter.Value / 2.0))
sketch_web_rear.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))

# Pad this profile forward (positive Y) to the front plane (Y=0)?
# The prompt says: "The outer rim ... extends forward from the rear plane to its front shoulder."
# So we pad from rear plane to front plane.
# Distance = pulley_overall_width.
pad_web_rear = body.newObject("PartDesign::Pad", "Pad_Web_Rear")
pad_web_rear.Profile = sketch_web_rear
pad_web_rear.Length = params.pulley_overall_width.Value
pad_web_rear.Type = "Blind"
pad_web_rear.Reverse = False # Pad in positive Y

# --- Feature 3: Outer Rim Shoulder ---
# "The outer rim is defined by pulley_outer_diameter and extends forward from the rear plane to its front shoulder."
# "The setback of this shoulder from the front plane equals the radius defined by rim_inner_large_diameter"
# This is confusing. "Setback ... equals the radius".
# Let's interpret: The outer rim starts at the rear plane (Y = -pulley_overall_width) with radius rim_inner_small_diameter/2.
# It extends forward. At some point, it steps up to pulley_outer_diameter.
# The "front shoulder" is the step.
# "Setback of this shoulder from the front plane equals the radius defined by rim_inner_large_diameter".
# This phrasing is tricky. "Setback ... equals the radius".
# Maybe the shoulder is located at Y = -(pulley_overall_width - rim_inner_large_diameter/2)?
# Or maybe the shoulder is at Y = -(pulley_overall_width - rim_inner_large_diameter)?
# Let's re-read: "extends forward from the rear plane to its front shoulder. The setback of this shoulder from the front plane equals the radius defined by rim_inner_large_diameter".
# If setback = radius, then distance from front plane = rim_inner_large_diameter / 2.
# So the shoulder is at Y = -(pulley_overall_width - rim_inner_large_diameter / 2).
# From rear plane to shoulder: length = pulley_overall_width - rim_inner_large_diameter / 2.
# From shoulder to front plane: length = rim_inner_large_diameter / 2.
# At the shoulder, the radius changes from rim_inner_small_diameter to pulley_outer_diameter?
# No, "outer rim is defined by pulley_outer_diameter".
# So the outer rim is the part from rear plane to front plane, but with a step.
# Let's assume the outer rim profile at the rear plane is rim_inner_small_diameter.
# It extends forward to the shoulder.
# At the shoulder, it steps out to pulley_outer_diameter.
# Then it continues to the front plane?
# "From there, a straight transition reaches inner_web_large_diameter at the station set by hub_axial_width, then returns radially to the hub."
# This part describes the inner side of the rim/web transition near the hub.
# Let's break down the geometry again.
# 1. Rear Plane (Y = -W): Inner radius = inner_web_small_diameter/2. Outer radius = rim_inner_small_diameter/2.
# 2. Pad forward to Shoulder (Y = -W + L1).
#    L1 = W - rim_inner_large_diameter/2.
#    At Shoulder, Outer radius becomes pulley_outer_diameter/2. Inner radius stays rim_inner_small_diameter/2?
#    Or does the inner radius also change?
#    "The outer rim is defined by pulley_outer_diameter". This usually means the outermost edge.
#    "From there, a straight transition reaches inner_web_large_diameter at the station set by hub_axial_width".
#    This suggests the inner radius of the rim/web changes from rim_inner_small_diameter to inner_web_large_diameter.
#    And this change happens at a distance "hub_axial_width" from the shoulder? Or from the rear?
#    "at the station set by hub_axial_width". This likely means the axial distance from the shoulder is hub_axial_width.
#    So at Y = Shoulder_Y - hub_axial_width, the inner radius becomes inner_web_large_diameter/2.
#    Then "returns radially to the hub". This means the inner radius goes from inner_web_large_diameter/2 to hub_outer_diameter/2.
#    This happens at the front plane? Or at Y = 0?
#    "This leaves the back of the wheel open around the hub".
#    So the hub is only at the front. The web is open at the back.
#    So the inner radius of the web is:
#    - From Rear Plane to (Shoulder_Y - hub_axial_width): rim_inner_small_diameter/2.
#    - From (Shoulder_Y - hub_axial_width) to Front Plane: inner_web_large_diameter/2.
#    - At Front Plane: Hub Outer Diameter.
#    Wait, the hub is a separate feature we already did (Pad_Hub_Bore).
#    The web is the material connecting the hub to the rim.
#    So the web profile at the front plane (Y=0) should be:
#    Inner radius: hub_outer_diameter/2.
#    Outer radius: pulley_outer_diameter/2.
#    But the prompt says "returns radially to the hub".
#    So at the front plane, the inner radius is hub_outer_diameter/2.
#    And the outer radius is pulley_outer_diameter/2.
#    So the web at the front is an annulus from hub_outer to pulley_outer.
#    But we already have the hub bore (inner radius center_bore).
#    So the web at the front is an annulus from hub_outer to pulley_outer.
#    The hub bore is a hole through the center.
#    So the web at the front is the material between hub_outer and pulley_outer.
#    But the prompt says "The outer rim is defined by pulley_outer_diameter and extends forward from the rear plane to its front shoulder."
#    This implies the outer rim is the outermost part.
#    So the outer radius is pulley_outer_diameter/2 from rear plane to front plane.
#    The inner radius of the rim/web changes.
#    Let's construct this with a sketch at the rear plane and a sketch at the front plane, or a single sketch with a profile that changes?
#    PartDesign Pad takes a single profile.
#    So we need to define the profile at one plane and pad it.
#    If we pad from rear to front, the profile must be defined at the rear plane.
#    But the profile changes along the Y axis.
#    We can use a "Pad" with a "MidPlane" or "Blind" and then use "Fillet" or "Chamfer" or "Groove" to modify it?
#    No, the geometry is stepped.
#    We can use multiple Pads.
#    1. Pad from Rear to Shoulder: Profile at Rear.
#       Inner radius: rim_inner_small_d
