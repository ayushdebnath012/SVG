import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# Create a new document
doc = App.newDocument("PulleyWheel")

# --- Parameters ---
# We define these as properties on a specific object to keep them editable and named.
# To ensure they are globally accessible or easily referenced, we will store them in a specific object.
param_obj = doc.addObject("App::FeaturePython", "Parameters")
# Since "App::FeaturePython" is an API placeholder for custom features, we will use a simple PropertySet 
# which is the standard way to add named parameters in PartDesign without custom code.
param_obj = doc.addObject("PartDesign::VarSet", "Parameters")

# Define parameters
param_obj.addProperty("App::PropertyLength", "center_bore_diameter", "Dimensions", "25.0")
param_obj.addProperty("App::PropertyLength", "hub_outer_diameter", "Dimensions", "40.0")
param_obj.addProperty("App::PropertyLength", "pulley_outer_diameter", "Dimensions", "195.0")
param_obj.addProperty("App::PropertyLength", "pulley_overall_width", "Dimensions", "95.0")
param_obj.addProperty("App::PropertyLength", "hub_axial_width", "Dimensions", "55.0")
param_obj.addProperty("App::PropertyLength", "center_bore_axial_depth", "Dimensions", "70.0")
param_obj.addProperty("App::PropertyLength", "inner_web_small_diameter", "Dimensions", "131.54")
param_obj.addProperty("App::PropertyLength", "inner_web_large_diameter", "Dimensions", "147.54")
param_obj.addProperty("App::PropertyLength", "rim_inner_small_diameter", "Dimensions", "144.0")
param_obj.addProperty("App::PropertyLength", "rim_inner_large_diameter", "Dimensions", "160.0")
param_obj.addProperty("App::PropertyLength", "pulley_base_plate_thickness", "Dimensions", "20.0")
param_obj.addProperty("App::PropertyInteger", "number_of_mounting_lugs", "Dimensions", "2")
param_obj.addProperty("App::PropertyInteger", "number_of_mounting_holes", "Dimensions", "2")
param_obj.addProperty("App::PropertyLength", "mounting_hole_diameter", "Dimensions", "15.0")
param_obj.addProperty("App::PropertyLength", "mounting_hole_center_half_spacing", "Dimensions", "47.5")
param_obj.addProperty("App::PropertyLength", "mounting_lug_outer_arc_radius", "Dimensions", "17.0")
param_obj.addProperty("App::PropertyLength", "mounting_lug_outer_arc_central_angle", "Dimensions", "17.0") # Will convert to length (degrees * pi / 180)
param_obj.addProperty("App::PropertyLength", "mounting_lug_fillet_radius", "Dimensions", "13.0")
param_obj.addProperty("App::PropertyLength", "mounting_lug_fillet_central_angle", "Dimensions", "15.0") # Will convert
param_obj.addProperty("App::PropertyLength", "central_web_half_length", "Dimensions", "25.0")
param_obj.addProperty("App::PropertyLength", "central_web_outer_half_height", "Dimensions", "34.5")
param_obj.addProperty("App::PropertyLength", "lug_plate_attachment_y", "Dimensions", "-55.0")
param_obj.addProperty("App::PropertyLength", "lug_plate_pad_depth", "Dimensions", "20.0")

# Helper function to get a length from a dimension (handling degrees)
def get_length(name):
    val = doc.getObject("Parameters").getPropertyByName(name).getValueAsAmount("Length")
    if name in ["mounting_lug_outer_arc_central_angle", "mounting_lug_fillet_central_angle"]:
        # Convert degrees to radians * pi? No, FreeCAD expressions handle units.
        # But if the property is stored as Length, we need to be careful. 
        # The prompt says "180.0 degrees". If we store it as Length 180, FreeCAD treats it as 180mm.
        # We need to store the value in radians if the property is Length, OR use expressions.
        # Let's store the value in mm but convert it in the expression if needed, 
        # or better: store the value in radians directly? 
        # Actually, let's just store the numeric value in a property and use it in expressions with conversion.
        # Wait, standard practice: Store the angle in degrees in a PropertyLength? 
        # FreeCAD PropertyLength stores mm. 
        # Let's store the value in radians directly in the property to avoid conversion logic in expressions?
        # Or, simpler: Just use the value in an expression like pi/180 * Value.
        # Let's assume the property holds the number "180" but interpreted as mm.
        # We will construct the expression to convert it.
        # Actually, let's just set the value to the radian equivalent now.
        # 180 deg = PI rad.
        return val * math.pi / 180.0
    return val

# --- Geometry Setup ---
# Global Y is the wheel axis.
# Wheel extends rearward (negative Y).
# Front plane: Y = 0.
# Rear plane: Y = -pulley_overall_width.

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject("Body")

# Create Planes
# XY_Plane: X-Z plane at Y=0. Used for main profile.
plane_XY = body.newObject("PartDesign::Plane", "XY_Plane")
plane_XY.Placement = App.Placement(App.Vector(0, 0, 0))
plane_XY.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 0) # Align normal to Y

# YZ_Plane: X-Y plane at Z=0. Used for mounting lugs (symmetric about X axis).
plane_YZ = body.newObject("PartDesign::Plane", "YZ_Plane")
plane_YZ.Placement = App.Placement(App.Vector(0, 0, 0))
plane_YZ.Placement.Rotation = App.Rotation(App.Vector(1, 0, 0), 0) # Align normal to Z

# XZ_Plane: X-Z plane at Y=-width. Used for rear reference if needed.
plane_XZ = body.newObject("PartDesign::Plane", "XZ_Plane")
plane_XZ.Placement = App.Placement(App.Vector(0, -doc.getObject("Parameters").getPropertyByName("pulley_overall_width").getValueAsAmount("Length"), 0))
plane_XZ.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 0)

# --- Step 1: Main Wheel Profile (Rotation around Y) ---
# Sketch on XY_Plane (X-Z plane). 
# Profile needs to be closed.
# Coordinate system: X is radius, Z is axial (front-to-rear). 
# Wait, standard XY plane in FreeCAD: X horizontal, Y vertical. 
# If we map Sketcher XY to World XZ, then Sketcher Y corresponds to World Z.
# Let's define the sketch on the XY_Plane (Normal is Y).
# So Sketcher X = World X, Sketcher Y = World Z.
# The rotation axis must be World Y.
# The profile is in the X-Z plane.

sketch_main = body.newObject("Sketcher::SketchObject", "MainProfile")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 0) # Rotate to face Z? No, XY plane faces Y.
# Actually, PartDesign::Plane "XY_Plane" usually has normal Y. 
# So the sketch lies in the X-Z plane.
# Let's use explicit coordinates.
# Origin (0,0,0) in world is center.
# Profile points: (Radius, Axial).
# In Sketcher: Point 0 is (X, Z).

# Dimensions
C_Bore = get_length("center_bore_diameter")
C_Bore_R = C_Bore / 2.0
Hub_OD = get_length("hub_outer_diameter")
Hub_R = Hub_OD / 2.0
P_Outer = get_length("pulley_outer_diameter")
P_Outer_R = P_Outer / 2.0
P_Width = get_length("pulley_overall_width")

# Inner Web Small Diameter
IWS_D = get_length("inner_web_small_diameter")
IWS_R = IWS_D / 2.0
# Inner Web Large Diameter
IWL_D = get_length("inner_web_large_diameter")
IWL_R = IWL_D / 2.0
# Rim Inner Small Diameter
RIS_D = get_length("rim_inner_small_diameter")
RIS_R = RIS_D / 2.0
# Rim Inner Large Diameter
RIL_D = get_length("rim_inner_large_diameter")
RIL_R = RIL_D / 2.0

# Hub Axial Width (Hub extends from Front (0) to -Hub_Width)
Hub_Width = get_length("hub_axial_width")

# Center Bore Axial Depth (Bore extends from Front (0) to -Bore_Depth)
Bore_Depth = get_length("center_bore_axial_depth")

# Define Points (X, Z)
# Z=0 is Front. Z=-P_Width is Rear.
# Bore: Circle at X=0, Z from 0 to -Bore_Depth.
# Hub: Rect from X=Hub_R, Z=0 to Z=-Hub_Width.
# Web Small (Inner): Rect from X=IWS_R, Z=-Hub_Width to Z=-Bore_Depth.
# Web Small (Outer? No, transition):
# "A straight web transition then reaches rim_inner_small_diameter at the rear plane"
# This implies the web thickness changes?
# Let's re-read carefully:
# "The bore wall continues rearward by center_bore_axial_depth, where the section extends outward to inner_web_small_diameter."
# So at Z=-Bore_Depth, Radius is IWS_R.
# "A straight web transition then reaches rim_inner_small_diameter at the rear plane set by pulley_overall_width."
# So from Z=-Bore_Depth to Z=-P_Width, Radius increases from IWS_R to RIS_R.
# "The outer rim is defined by pulley_outer_diameter and extends forward from the rear plane to its front shoulder."
# "The setback of this shoulder from the front plane equals the radius defined by rim_inner_large_diameter" -> This phrasing is tricky.
# "Setback... equals the radius defined by rim_inner_large_diameter". 
# RIL_R = 80.0 mm. P_Width = 95.0.
# Shoulder is at Z = -(P_Width - RIL_R) = -(95 - 80) = -15.0?
# "From there, a straight transition reaches inner_web_large_diameter at the station set by hub_axial_width"
# Hub axial width is 55. So at Z = -55.0, Radius = IWL_R.
# "Then returns radially to the hub." -> From Z=-55 to Z=0, Radius goes from IWL_R to Hub_R.

# Let's build the profile line segments:
# 1. Hub Inner Wall (Front to Rear): X = Hub_R, Z from 0 to -Hub_Width.
# 2. Web Transition 1 (Hub to Small Web): Z from -Hub_Width to -Bore_Depth. 
#    At -Hub_Width, X = IWS_R? 
#    Wait, "section extends outward to inner_web_small_diameter". 
#    So at Z = -Bore_Depth, X = IWS_R.
#    At Z = -Hub_Width, X = ? 
#    "straight web transition then reaches rim_inner_small_diameter at the rear plane"
#    This implies a linear ramp from (-Hub_Width, X_start) to (-P_Width, RIS_R).
#    But what is X_start at -Hub_Width? 
#    "A straight web transition then reaches rim_inner_small_diameter at the rear plane"
#    Maybe the "straight web transition" starts from the end of the bore?
#    "The bore wall continues rearward... where the section extends outward to inner_web_small_diameter."
#    So at Z=-Bore_Depth, X = IWS_R.
#    Then "A straight web transition then reaches rim_inner_small_diameter at the rear plane".
#    This suggests a line from (-Bore_Depth, IWS_R) to (-P_Width, RIS_R).
#    What happens between -Hub_Width and -Bore_Depth?
#    The hub ends at -Hub_Width. The bore continues to -Bore_Depth.
#    So we need a vertical drop? Or a step?
#    "straight web transition" implies a slanted line.
#    Let's assume the web profile is continuous.
#    From Z=-Hub_Width (End of Hub) to Z=-Bore_Depth (End of Bore), the radius grows from Hub_R to IWS_R?
#    No, the bore is empty inside. The web is the solid part.
#    The inner wall of the web is the profile we are drawing.
#    Profile:
#    Start at Front (Z=0), X=Hub_R. (Hub Inner)
#    Go to Z=-Hub_Width. (Hub End)
#    Go to Z=-Bore_Depth. (Bore End). Radius increases from Hub_R to IWS_R? 
#    The problem says "bore wall continues... extends outward to inner_web_small_diameter".
#    This implies the bore diameter grows? Or the web thickness grows?
#    Usually "bore wall" means the inner surface of the hub/web.
#    So the inner radius grows from Hub_R to IWS_R between -Hub_Width and -Bore_Depth?
#    Let's assume a straight line from (-Hub_Width, Hub_R) to (-Bore_Depth, IWS_R).
#    Then from (-Bore_Depth, IWS_R) to (-P_Width, RIS_R). (Straight web transition).
#    Then from (-P_Width, RIS_R) to (0, P_Outer_R)? No, "extends forward from the rear plane".
#    So at Z=-P_Width, X=P_Outer_R.
#    "extends forward from the rear plane to its front shoulder."
#    "The setback of this shoulder from the front plane equals the radius defined by rim_inner_large_diameter"
#    Setback = Distance from Front (Z=0) to Shoulder.
#    Shoulder_Z = -(P_Width - RIL_R).
#    At Shoulder_Z, Radius = ?
#    "rim_inner_large_diameter, which also sets the inner rim size at that station."
#    So at Shoulder_Z, Radius = RIL_R.
#    "From there, a straight transition reaches inner_web_large_diameter at the station set by hub_axial_width"
#    Station = -Hub_Width.
#    So line from (Shoulder_Z, RIL_R) to (-Hub_Width, IWL_R).
#    "Then returns radially to the hub."
#    Line from (-Hub_Width, IWL_R) to (0, Hub_R).

# Summary of Points (X, Z):
# P1: (Hub_R, 0)
# P2: (Hub_R, -Hub_Width)
# P3: (IWS_R, -Bore_Depth)  # Assuming linear growth from Hub_R to IWS_R? Or step? "extends outward" suggests growth.
# P4: (RIS_R, -P_Width)     # Rear plane
# P5: (P_Outer_R, -P_Width) # Rear outer
# P6: (RIL_R, -(P_Width - RIL_R)) # Shoulder
# P7: (IWL_R, -Hub_Width)    # Hub width station
# P8: (Hub_R, 0)             # Close loop

# Let's create the sketch geometry
sketch_main.clearGeometries()
sketch_main.addGeometry(Part.LineSegment(App.Vector(Hub_R, 0, 0), App.Vector(Hub_R, -Hub_Width, 0)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(Hub_R, -Hub_Width, 0), App.Vector(IWS_R, -Bore_Depth, 0)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(IWS_R, -Bore_Depth, 0), App.Vector(RIS_R, -P_Width, 0)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(RIS_R, -P_Width, 0), App.Vector(P_Outer_R, -P_Width, 0)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(P_Outer_R, -P_Width, 0), App.Vector(RIL_R, -(P_Width - RIL_R), 0)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(RIL_R, -(P_Width - RIL_R), 0), App.Vector(IWL_R, -Hub_Width, 0)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(IWL_R, -Hub_Width, 0), App.Vector(Hub_R, 0, 0)), False)

# Constraints for Main Sketch
# Close loop
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 7, 0)) # Point 0 and 7 (index 7 is last)
# Coaxial vertical lines
sketch_main.addConstraint(Sketcher.Constraint("Vertical", 0, 0)) # Hub inner
sketch_main.addConstraint(Sketcher.Constraint("Vertical", 7, 0)) # Web inner
# Horizontal lines
sketch_main.addConstraint(Sketcher.Constraint("Horizontal", 3, 1)) # Rear plane
sketch_main.addConstraint(Sk
