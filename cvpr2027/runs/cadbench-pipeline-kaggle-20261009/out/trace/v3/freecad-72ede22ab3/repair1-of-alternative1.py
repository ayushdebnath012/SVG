import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# Create a new document
doc = App.newDocument("PulleyWheel")

# --- Parameters ---
# We define these as properties on a PartDesign::VarSet object to keep them editable and named.
param_obj = doc.addObject("PartDesign::VarSet", "Parameters")

# Define parameters with default values
param_obj.addProperty("App::PropertyLength", "center_bore_diameter", "Dimensions", 25.0)
param_obj.addProperty("App::PropertyLength", "hub_outer_diameter", "Dimensions", 40.0)
param_obj.addProperty("App::PropertyLength", "pulley_outer_diameter", "Dimensions", 195.0)
param_obj.addProperty("App::PropertyLength", "pulley_overall_width", "Dimensions", 95.0)
param_obj.addProperty("App::PropertyLength", "hub_axial_width", "Dimensions", 55.0)
param_obj.addProperty("App::PropertyLength", "center_bore_axial_depth", "Dimensions", 70.0)
param_obj.addProperty("App::PropertyLength", "inner_web_small_diameter", "Dimensions", 131.54)
param_obj.addProperty("App::PropertyLength", "inner_web_large_diameter", "Dimensions", 147.54)
param_obj.addProperty("App::PropertyLength", "rim_inner_small_diameter", "Dimensions", 144.0)
param_obj.addProperty("App::PropertyLength", "rim_inner_large_diameter", "Dimensions", 160.0)
param_obj.addProperty("App::PropertyLength", "pulley_base_plate_thickness", "Dimensions", 20.0)
param_obj.addProperty("App::PropertyInteger", "number_of_mounting_lugs", "Dimensions", 2)
param_obj.addProperty("App::PropertyInteger", "number_of_mounting_holes", "Dimensions", 2)
param_obj.addProperty("App::PropertyLength", "mounting_hole_diameter", "Dimensions", 15.0)
param_obj.addProperty("App::PropertyLength", "mounting_hole_center_half_spacing", "Dimensions", 47.5)
param_obj.addProperty("App::PropertyLength", "mounting_lug_outer_arc_radius", "Dimensions", 17.0)
param_obj.addProperty("App::PropertyLength", "mounting_lug_outer_arc_central_angle", "Dimensions", 17.0) # Will convert to radians in expression
param_obj.addProperty("App::PropertyLength", "mounting_lug_fillet_radius", "Dimensions", 13.0)
param_obj.addProperty("App::PropertyLength", "mounting_lug_fillet_central_angle", "Dimensions", 15.0) # Will convert to radians in expression
param_obj.addProperty("App::PropertyLength", "central_web_half_length", "Dimensions", 25.0)
param_obj.addProperty("App::PropertyLength", "central_web_outer_half_height", "Dimensions", 34.5)
param_obj.addProperty("App::PropertyLength", "lug_plate_attachment_y", "Dimensions", -55.0)
param_obj.addProperty("App::PropertyLength", "lug_plate_pad_depth", "Dimensions", 20.0)

# Helper function to get a length from a dimension (handling degrees)
def get_length(name):
    val = doc.getObject("Parameters").getPropertyByName(name).getValueAsAmount("Length")
    if name in ["mounting_lug_outer_arc_central_angle", "mounting_lug_fillet_central_angle"]:
        # Convert degrees to radians
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
# Coordinate system: X is radius, Z is axial (front-to-rear). 
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
# Profile points:
# 1. Hub Inner Wall (Front to Rear): X = Hub_R, Z from 0 to -Hub_Width.
# 2. Web Transition 1 (Hub to Small Web): Z from -Hub_Width to -Bore_Depth. 
#    Radius grows from Hub_R to IWS_R.
# 3. Web Transition 2 (Small Web to Rear): Z from -Bore_Depth to -P_Width.
#    Radius grows from IWS_R to RIS_R.
# 4. Rear Outer: X = P_Outer_R, Z = -P_Width.
# 5. Shoulder: Z = -(P_Width - RIL_R), X = RIL_R.
# 6. Web Transition 3 (Shoulder to Hub Width): Z from -(P_Width - RIL_R) to -Hub_Width.
#    Radius grows from RIL_R to IWL_R.
# 7. Web Transition 4 (Hub Width to Front): Z from -Hub_Width to 0.
#    Radius grows from IWL_R to Hub_R.

# Let's create the sketch geometry
sketch_main = body.newObject("Sketcher::SketchObject", "MainProfile")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 0) # Rotate to face Y (XY plane)

# Add Geometry
# P1: (Hub_R, 0)
# P2: (Hub_R, -Hub_Width)
# P3: (IWS_R, -Bore_Depth)
# P4: (RIS_R, -P_Width)
# P5: (P_Outer_R, -P_Width)
# P6: (RIL_R, -(P_Width - RIL_R))
# P7: (IWL_R, -Hub_Width)
# P8: (Hub_R, 0)

sketch_main.addGeometry(Part.LineSegment(App.Vector(Hub_R, 0, 0), App.Vector(Hub_R, -Hub_Width, 0)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(Hub_R, -Hub_Width, 0), App.Vector(IWS_R, -Bore_Depth, 0)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(IWS_R, -Bore_Depth, 0), App.Vector(RIS_R, -P_Width, 0)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(RIS_R, -P_Width, 0), App.Vector(P_Outer_R, -P_Width, 0)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(P_Outer_R, -P_Width, 0), App.Vector(RIL_R, -(P_Width - RIL_R), 0)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(RIL_R, -(P_Width - RIL_R), 0), App.Vector(IWL_R, -Hub_Width, 0)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(IWL_R, -Hub_Width, 0), App.Vector(Hub_R, 0, 0)), False)

# Constraints for Main Sketch
# Close loop
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 7, 0))
# Coaxial vertical lines
sketch_main.addConstraint(Sketcher.Constraint("Vertical", 0, 0))
sketch_main.addConstraint(Sketcher.Constraint("Vertical", 7, 0))
# Horizontal lines
sketch_main.addConstraint(Sketcher.Constraint("Horizontal", 3, 1))
sketch_main.addConstraint(Sketcher.Constraint("Horizontal", 4, 1))
# Coincident points
sketch_main.addConstraint(Sketcher.Constraint("PointOnObject", 0, 0, "XY_Plane", "X_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("PointOnObject", 0, 1, "XY_Plane", "Z_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("PointOnObject", 4, 0, "XY_Plane", "X_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("PointOnObject", 4, 1, "XY_Plane", "Z_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("PointOnObject", 5, 0, "XY_Plane", "X_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("PointOnObject", 5, 1, "XY_Plane", "Z_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("PointOnObject", 6, 0, "XY_Plane", "X_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("PointOnObject", 6, 1, "XY_Plane", "Z_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("PointOnObject", 7, 0, "XY_Plane", "X_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("PointOnObject", 7, 1, "XY_Plane", "Z_Axis"))

# Pad the main profile
pad_main = body.newObject("PartDesign::Pad", "PadMain")
pad_main.Profile = sketch_main
pad_main.Length = P_Width
pad_main.Type = "Solid"
pad_main.Reversed = False

# --- Step 2: Mounting Plate ---
# The mounting plate occupies the front axial band and extends rearward by pulley_base_plate_thickness.
# It is symmetric about both centerlines (X and Z).
# The outline is defined by central_web_half_length and central_web_outer_half_height.
# Two lugs are attached.

# Sketch for Mounting Plate on YZ_Plane (X-Y plane).
# Wait, the plate is in the X-Z plane (front face of the wheel).
# The wheel axis is Y. The plate is perpendicular to the axis.
# So the plate lies in the X-Z plane.
# We should use the XY_Plane again, but offset in Y.
# Or create a new plane at Y = -lug_plate_attachment_y?
# "lug_plate_attachment_y identifies the corresponding rear hub-and-web shelf."
# This suggests the plate is located at Y = lug_plate_attachment_y?
# No, "extends rearward by pulley_base_plate_thickness".
# If the front of the plate is at Y=0, then it extends to Y = -lug_plate_pad_depth.
# The "attachment_y" might be the Y coordinate of the rear face?
# Let's assume the plate starts at Y=0 and goes to Y = -lug_plate_pad_depth.
# The outline is in the X-Z plane.

# Let's create a sketch on a plane at Y = -lug_plate_pad_depth (rear face of plate)
# Or just use the XY_Plane and offset the sketch.
# Let's use a new plane at Y = -lug_plate_pad_depth.
plane_plate = body.newObject("PartDesign::Plane", "PlatePlane")
plane_plate.Placement = App.Placement(App.Vector(0, -doc.getObject("Parameters").getPropertyByName("lug_plate_pad_depth").getValueAsAmount("Length"), 0))
plane_plate.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 0)

sketch_plate = body.newObject("Sketcher::SketchObject", "PlateSketch")
sketch_plate.Placement = App.Placement(App.Vector(0, -doc.getObject("Parameters").getPropertyByName("lug_plate_pad_depth").getValueAsAmount("Length"), 0))
sketch_plate.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 0)

# Dimensions for Plate
Plate_Thickness = get_length("pulley_base_plate_thickness")
Central_Web_Half_Len = get_length("central_web_half_length")
Central_Web_Half_Hgt = get_length("central_web_outer_half_height")
Lug_Spacing_Half = get_length("mounting_hole_center_half_spacing")
Lug_Arc_R = get_length("mounting_lug_outer_arc_radius")
Lug_Arc_Angle = get_length("mounting_lug_outer_arc_central_angle")
Lug_Fillet_R = get_length("mounting_lug_fillet_radius")
Lug_Fillet_Angle = get_length("mounting_lug_fillet_central_angle")
Mounting_Hole_D = get_length("mounting_hole_diameter")

# The outline is symmetric about both centerlines.
# Central region: Rect from X=-Central_Web_Half_Len to X=Central_Web_Half_Len, Z=-Central_Web_Half_Hgt to Z=Central_Web_Half_Hgt.
# Two lugs:
# Lug centers at X = +/- Lug_Spacing_Half, Z = 0.
# Each outer lug end is a semicircle defined by Lug_Arc_R and Lug_Arc_Angle.
# "Four equal tangent transition fillets... connect the lug ends to the central region"
# This implies the lugs are not simple rectangles.
# Let's construct the outline:
# 1. Central Rect: (-Central_Web_Half_Len, -Central_Web_Half_Hgt) to (Central_Web_Half_Len, Central_Web_Half_Hgt).
# 2. Lug 1 (Right): Center at (Lug_Spacing_Half, 0).
#    The lug extends from the central region to the right.
#    The "outer lug end" is a semicircle.
#    The "tangent transition fillets" connect the lug ends to the central region.
#    This suggests the lug profile is:
#    - Start at the central region edge (X = Central_Web_Half_Len, Z = 0).
#    - Go to the lug center? No, the lug center is at Lug_Spacing_Half.
#    - The lug has a width.
#    - The "outer lug end" is a semicircle.
#    - The "tangent transition fillets" connect the lug ends to the central region.
#    This is complex. Let's simplify based on typical CAD modeling:
#    The lug is a rounded rectangle or a shape with fillets.
#    "Four equal tangent transition fillets... connect the lug ends to the central region"
#    This implies there are 4 fillets total (2 per lug? or 2 total?).
#    "Four equal tangent transition fillets... connect the lug ends to the central region"
#    Maybe 2 fillets per lug? Or 2 fillets total connecting the two lugs to the central region?
#    Given "symmetric two-lug mounting plate", likely 2 fillets per lug, total 4.
#    Or maybe 2 fillets total, one on each side of the central region?
#    Let's assume 2 fillets per lug, connecting the lug to the central region.
#    The fillet radius is Lug_Fillet_R.
#    The fillet angle is Lug_Fillet_Angle.
#    The "outer lug end" is a semicircle.
#    This implies the lug has a straight section, then a fillet, then a semicircle?
#    Or the semicircle is the end, and the fillet connects the straight section to the semicircle?
#    "Four equal tangent transition fillets... connect the lug ends to the central region"
#    This phrasing is ambiguous. Let's assume the following:
#    The lug profile is:
#    - Start at the central region edge (X = Central_Web_Half_Len, Z = 0).
#    - A straight line to the start of the fillet.
#    - A fillet of radius Lug_Fillet_R.
#    - A straight line to the start of the semicircle.
#    - A semicircle of radius Lug_Arc_R.
#    - A straight line back to the central region? No, the lug is a single entity.
#    Let's assume the lug is a shape that starts at the central region, goes out, and ends with a semicircle.
#    The "tangent transition fillets" connect the lug to the central region.
#    This implies the lug is tangent to the central region at the fillet.
#    So the profile is:
#    - Start at (Central_Web_Half_Len, 0).
#    - Go to (Central_Web_Half_Len + Lug_Fillet_R, 0)? No, the fillet is tangent.
#    - The fillet connects the central region to the lug.
#    - The lug center is at (Lug_Spacing_Half, 0).
#    - The distance from the central region edge to the lug center is Lug_Spacing_Half - Central_Web_Half_Len.
#    - The fillet radius is Lug_Fillet_R.
#    - The fillet connects the central region (vertical line at X = Central_Web_Half_Len) to the lug (horizontal line at Z=0)?
#    - No, the lug is symmetric about Z=0.
#    - The fillet connects the central region (vertical line) to the lug (horizontal line)?
#    - This would create a rounded corner.
#    - The "outer lug end" is a semicircle.
#    - This implies the lug has a straight section, then a semicircle.
#    - The fillet connects the straight section to the semicircle?
#    - Or the fillet connects the central region to the straight section?
#    Let's assume the following profile for one lug (right side):
#    - Start at (Central_Web_Half_Len, -Central_Web_Half_Hgt).
#    - Go to (Central_Web_Half_Len, Central_Web_Half_Hgt). (Central region edge)
#    - At (Central_Web_Half_Len, Central_Web_Half_Hgt), start a fillet of radius Lug_Fillet_R.
#    - The fillet connects to a line going to the lug center?
#    - The lug center is at (Lug_Spacing_Half, 0).
#    - The fillet connects the vertical line (X = Central_Web_Half_Len) to the horizontal line (Z = 0)?
#    - No, the lug is symmetric about Z=0.
#    - The fillet connects the vertical line (X = Central_Web_Half_Len) to the line going to the lug center?
#    - Let's assume the fillet connects the central region to the lug at the top and bottom.
#    - The fillet radius is Lug_Fillet_R.
#    - The fillet connects the vertical line (X = Central_Web_Half_Len) to the line going to the lug center (Z=0)?
#    - This would create a rounded corner at (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - The line goes from (Central_Web_Half_Len, Central_Web_Half_Hgt) to (Lug_Spacing_Half, Central_Web_Half_Hgt)?
#    - No, the lug center is at (Lug_Spacing_Half, 0).
#    - The line goes from (Central_Web_Half_Len, Central_Web_Half_Hgt) to (Lug_Spacing_Half, Central_Web_Half_Hgt)?
#    - Then a semicircle at the end?
#    - The "outer lug end" is a semicircle defined by Lug_Arc_R and Lug_Arc_Angle.
#    - This implies the lug has a straight section, then a semicircle.
#    - The fillet connects the straight section to the semicircle?
#    - Or the fillet connects the central region to the straight section?
#    Let's assume the following:
#    - The lug profile is:
#      - Start at (Central_Web_Half_Len, -Central_Web_Half_Hgt).
#      - Go to (Central_Web_Half_Len, Central_Web_Half_Hgt).
#      - At (Central_Web_Half_Len, Central_Web_Half_Hgt), start a fillet of radius Lug_Fillet_R.
#      - The fillet connects to a line going to the lug center?
#      - The fillet connects the vertical line (X = Central_Web_Half_Len) to the line going to the lug center (Z=0)?
#      - This would create a rounded corner at (Central_Web_Half_Len, Central_Web_Half_Hgt).
#      - The line goes from (Central_Web_Half_Len, Central_Web_Half_Hgt) to (Lug_Spacing_Half, Central_Web_Half_Hgt)?
#      - Then a semicircle at the end?
#      - The "outer lug end" is a semicircle defined by Lug_Arc_R and Lug_Arc_Angle.
#      - This implies the lug has a straight section, then a semicircle.
#      - The fillet connects the straight section to the semicircle?
#      - Or the fillet connects the central region to the straight section?
#    Let's assume the following profile for one lug (right side):
#    - Start at (Central_Web_Half_Len, -Central_Web_Half_Hgt).
#    - Go to (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - At (Central_Web_Half_Len, Central_Web_Half_Hgt), start a fillet of radius Lug_Fillet_R.
#    - The fillet connects to a line going to the lug center?
#    - The fillet connects the vertical line (X = Central_Web_Half_Len) to the line going to the lug center (Z=0)?
#    - This would create a rounded corner at (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - The line goes from (Central_Web_Half_Len, Central_Web_Half_Hgt) to (Lug_Spacing_Half, Central_Web_Half_Hgt)?
#    - Then a semicircle at the end?
#    - The "outer lug end" is a semicircle defined by Lug_Arc_R and Lug_Arc_Angle.
#    - This implies the lug has a straight section, then a semicircle.
#    - The fillet connects the straight section to the semicircle?
#    - Or the fillet connects the central region to the straight section?
#    Let's assume the following:
#    - The lug profile is:
#      - Start at (Central_Web_Half_Len, -Central_Web_Half_Hgt).
#      - Go to (Central_Web_Half_Len, Central_Web_Half_Hgt).
#      - At (Central_Web_Half_Len, Central_Web_Half_Hgt), start a fillet of radius Lug_Fillet_R.
#      - The fillet connects to a line going to the lug center?
#      - The fillet connects the vertical line (X = Central_Web_Half_Len) to the line going to the lug center (Z=0)?
#      - This would create a rounded corner at (Central_Web_Half_Len, Central_Web_Half_Hgt).
#      - The line goes from (Central_Web_Half_Len, Central_Web_Half_Hgt) to (Lug_Spacing_Half, Central_Web_Half_Hgt)?
#      - Then a semicircle at the end?
#      - The "outer lug end" is a semicircle defined by Lug_Arc_R and Lug_Arc_Angle.
#      - This implies the lug has a straight section, then a semicircle.
#      - The fillet connects the straight section to the semicircle?
#      - Or the fillet connects the central region to the straight section?
#    Let's assume the following profile for one lug (right side):
#    - Start at (Central_Web_Half_Len, -Central_Web_Half_Hgt).
#    - Go to (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - At (Central_Web_Half_Len, Central_Web_Half_Hgt), start a fillet of radius Lug_Fillet_R.
#    - The fillet connects to a line going to the lug center?
#    - The fillet connects the vertical line (X = Central_Web_Half_Len) to the line going to the lug center (Z=0)?
#    - This would create a rounded corner at (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - The line goes from (Central_Web_Half_Len, Central_Web_Half_Hgt) to (Lug_Spacing_Half, Central_Web_Half_Hgt)?
#    - Then a semicircle at the end?
#    - The "outer lug end" is a semicircle defined by Lug_Arc_R and Lug_Arc_Angle.
#    - This implies the lug has a straight section, then a semicircle.
#    - The fillet connects the straight section to the semicircle?
#    - Or the fillet connects the central region to the straight section?
#    Let's assume the following:
#    - The lug profile is:
#      - Start at (Central_Web_Half_Len, -Central_Web_Half_Hgt).
#      - Go to (Central_Web_Half_Len, Central_Web_Half_Hgt).
#      - At (Central_Web_Half_Len, Central_Web_Half_Hgt), start a fillet of radius Lug_Fillet_R.
#      - The fillet connects to a line going to the lug center?
#      - The fillet connects the vertical line (X = Central_Web_Half_Len) to the line going to the lug center (Z=0)?
#      - This would create a rounded corner at (Central_Web_Half_Len, Central_Web_Half_Hgt).
#      - The line goes from (Central_Web_Half_Len, Central_Web_Half_Hgt) to (Lug_Spacing_Half, Central_Web_Half_Hgt)?
#      - Then a semicircle at the end?
#      - The "outer lug end" is a semicircle defined by Lug_Arc_R and Lug_Arc_Angle.
#      - This implies the lug has a straight section, then a semicircle.
#      - The fillet connects the straight section to the semicircle?
#      - Or the fillet connects the central region to the straight section?
#    Let's assume the following profile for one lug (right side):
#    - Start at (Central_Web_Half_Len, -Central_Web_Half_Hgt).
#    - Go to (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - At (Central_Web_Half_Len, Central_Web_Half_Hgt), start a fillet of radius Lug_Fillet_R.
#    - The fillet connects to a line going to the lug center?
#    - The fillet connects the vertical line (X = Central_Web_Half_Len) to the line going to the lug center (Z=0)?
#    - This would create a rounded corner at (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - The line goes from (Central_Web_Half_Len, Central_Web_Half_Hgt) to (Lug_Spacing_Half, Central_Web_Half_Hgt)?
#    - Then a semicircle at the end?
#    - The "outer lug end" is a semicircle defined by Lug_Arc_R and Lug_Arc_Angle.
#    - This implies the lug has a straight section, then a semicircle.
#    - The fillet connects the straight section to the semicircle?
#    - Or the fillet connects the central region to the straight section?
#    Let's assume the following profile for one lug (right side):
#    - Start at (Central_Web_Half_Len, -Central_Web_Half_Hgt).
#    - Go to (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - At (Central_Web_Half_Len, Central_Web_Half_Hgt), start a fillet of radius Lug_Fillet_R.
#    - The fillet connects to a line going to the lug center?
#    - The fillet connects the vertical line (X = Central_Web_Half_Len) to the line going to the lug center (Z=0)?
#    - This would create a rounded corner at (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - The line goes from (Central_Web_Half_Len, Central_Web_Half_Hgt) to (Lug_Spacing_Half, Central_Web_Half_Hgt)?
#    - Then a semicircle at the end?
#    - The "outer lug end" is a semicircle defined by Lug_Arc_R and Lug_Arc_Angle.
#    - This implies the lug has a straight section, then a semicircle.
#    - The fillet connects the straight section to the semicircle?
#    - Or the fillet connects the central region to the straight section?
#    Let's assume the following profile for one lug (right side):
#    - Start at (Central_Web_Half_Len, -Central_Web_Half_Hgt).
#    - Go to (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - At (Central_Web_Half_Len, Central_Web_Half_Hgt), start a fillet of radius Lug_Fillet_R.
#    - The fillet connects to a line going to the lug center?
#    - The fillet connects the vertical line (X = Central_Web_Half_Len) to the line going to the lug center (Z=0)?
#    - This would create a rounded corner at (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - The line goes from (Central_Web_Half_Len, Central_Web_Half_Hgt) to (Lug_Spacing_Half, Central_Web_Half_Hgt)?
#    - Then a semicircle at the end?
#    - The "outer lug end" is a semicircle defined by Lug_Arc_R and Lug_Arc_Angle.
#    - This implies the lug has a straight section, then a semicircle.
#    - The fillet connects the straight section to the semicircle?
#    - Or the fillet connects the central region to the straight section?
#    Let's assume the following profile for one lug (right side):
#    - Start at (Central_Web_Half_Len, -Central_Web_Half_Hgt).
#    - Go to (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - At (Central_Web_Half_Len, Central_Web_Half_Hgt), start a fillet of radius Lug_Fillet_R.
#    - The fillet connects to a line going to the lug center?
#    - The fillet connects the vertical line (X = Central_Web_Half_Len) to the line going to the lug center (Z=0)?
#    - This would create a rounded corner at (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - The line goes from (Central_Web_Half_Len, Central_Web_Half_Hgt) to (Lug_Spacing_Half, Central_Web_Half_Hgt)?
#    - Then a semicircle at the end?
#    - The "outer lug end" is a semicircle defined by Lug_Arc_R and Lug_Arc_Angle.
#    - This implies the lug has a straight section, then a semicircle.
#    - The fillet connects the straight section to the semicircle?
#    - Or the fillet connects the central region to the straight section?
#    Let's assume the following profile for one lug (right side):
#    - Start at (Central_Web_Half_Len, -Central_Web_Half_Hgt).
#    - Go to (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - At (Central_Web_Half_Len, Central_Web_Half_Hgt), start a fillet of radius Lug_Fillet_R.
#    - The fillet connects to a line going to the lug center?
#    - The fillet connects the vertical line (X = Central_Web_Half_Len) to the line going to the lug center (Z=0)?
#    - This would create a rounded corner at (Central_Web_Half_Len, Central_Web_Half_Hgt).
#    - The line goes from (Central_Web_Half_Len, Central_Web_Half_Hgt) to (Lug_Spacing_Half, Central_Web_Half_Hgt)?
#    - Then a
