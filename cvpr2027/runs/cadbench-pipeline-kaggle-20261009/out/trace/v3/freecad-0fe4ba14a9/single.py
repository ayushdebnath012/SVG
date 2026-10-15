import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration Parameters ---
# Derived from the problem description
PARAMS = {
    "rod_outer_diameter": 30.0,
    "rod_cross_section_length": 30.0,
    "rod_cross_section_width": 30.0,
    "rod_end_body_length": 40.0,
    "rectangular_slot_width": 7.0,
    "rectangular_slot_count": 3,
    "spacing_distance_between_rectangular_slots": 15.0,
    "first_slot_left_edge_x_offset": 210.0,
    "clevis_pin_hole_diameter": 15.0,
    "clevis_slot_end_arc_radius": 15.66,
    "clevis_slot_end_arc_center_x": -233.58,
}

# --- Document Setup ---
doc = App.newDocument("LinkageRod")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters Object ---
# We create a VarSet to hold the named parameters for easy editing later
params = body.newObject("App::VarSet", "Parameters")
for name, value in PARAMS.items():
    params.addProperty("App::PropertyFloat", name, "Parameters", name)
    params.setValue(name, value)

# --- Helper to get parameter value ---
def get_param(name):
    return params.getValue(name)

# --- Base Cylinder (The Stock) ---
# We create a large cylinder that covers the entire length of the part.
# Length calculation:
# Left end center: -233.58 - 15.66 = -249.24
# Right end center: 233.58 + 15.66 = 249.24
# Total length needed approx 500mm to be safe.
total_length = 600.0
radius = get_param("rod_outer_diameter") / 2.0

base_sketch = body.newObject("Sketcher::SketchObject", "BaseStockSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.Support = (doc.getObject("XY_Plane"), [])
base_sketch.ConstrainToCurrentPlane = True
base_sketch.MapMode = "FlatFace"

# Add a large circle for the stock
base_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius), False)
base_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 1, radius))
base_sketch.addConstraint(Sketcher.Constraint("Center", 0, 1))

# Pad the stock
stock_pad = body.newObject("PartDesign::Pad", "StockPad")
stock_pad.Profile = base_sketch
stock_pad.Length = total_length
stock_pad.Type = "Solid"
stock_pad.Midplane = False
stock_pad.Reversed = False

# --- Lug Geometry Construction ---
# We will build the lugs using a sketch on the XY plane (perpendicular to X axis)
# and then revolve them? No, the problem describes a rod aligned with X.
# The lugs are at the ends. The cross section is in the YZ plane.
# So we should sketch on the XZ plane (for the profile along Y) or YZ plane (for profile along X)?
# Let's analyze: "Width is measured along Y and thickness along Z".
# The rod is along X.
# The cross section of the rod is a circle in YZ.
# The lugs are at the ends.
# The cuts are "transverse rectangular cutting profiles". Transverse to X means they are in the YZ plane.
# So we need to sketch the profile of the cuts on the YZ plane (which is the XZ plane rotated? No, YZ plane is perpendicular to X).
# In FreeCAD, planes are XY, XZ, YZ.
# YZ plane is the plane where X=0.
# We need to create a sketch on the YZ plane to define the cross-section of the lugs and slots.
# Then we can use a Pad along X? Or a Revolution?
# The problem says "long, straight linkage rod aligned with global X".
# The lugs are at the ends.
# The cuts are transverse.
# So the geometry is extruded along X.
# Strategy:
# 1. Create a sketch on the YZ plane (X=0).
# 2. Define the shape of the lug cross-section (Circle minus slots).
# 3. Pad this sketch along the X axis to create the full rod.
# Wait, the lugs are "at each end". The rod is continuous.
# If we pad a cross-section along X, we get a cylinder.
# The lugs are just the ends of this cylinder, but modified.
# The description says: "Each end carries an identical rounded lug... The cylindrical material envelope applies to the entire finished part".
# This implies the base is a cylinder, and the lugs are just the ends of that cylinder, but with specific slotting and rounding.
# Actually, "rounded lug formed from the same cylindrical stock".
# "Outward-facing semicircle... defines the rounded trimming boundary".
# This suggests the ends are not flat. They are rounded.
# So the base shape is a cylinder.
# The "lugs" are the ends of this cylinder.
# The slots are cut into these ends.
# The ends are rounded (semicircle in XY plane? No, "Outward-facing semicircle in the XY plane").
# Wait, if the rod is along X, the end face is in the YZ plane.
# "Outward-facing semicircle in the XY plane".
# If the rod is along X, the XY plane contains the rod axis.
# A semicircle in the XY plane would be a curve along the rod?
# Let's re-read carefully: "Outward-facing semicircle in the XY plane defines the rounded trimming boundary at each outer end".
# If the rod is along X, the "end" is at some X coordinate.
# The "trimming boundary" is the edge of the material at that end.
# If the boundary is a semicircle in the XY plane, it means the cut is along the X axis?
# No, "Outward-facing".
# Maybe the rod is along Z? "aligned with global X".
# Okay, Rod is along X.
# End face is in YZ plane.
# "Outward-facing semicircle in the XY plane".
# This is confusing. If the end is in YZ, how can the boundary be in XY?
# Unless the "rounded lug" is a feature that sticks out?
# "Each end carries an identical rounded lug formed from the same cylindrical stock".
# "The cylindrical material envelope applies to the entire finished part".
# This implies the stock is a cylinder. The lugs are just the ends.
# Maybe the "rounded trimming boundary" refers to the profile of the end cap?
# If the end cap is a semicircle in XY, it would look like a D-shape from the top?
# But the envelope is circular.
# Let's reconsider the orientation.
# Maybe the rod is along Z? "aligned with global X". No.
# Maybe the "semicircle in the XY plane" is a typo in my interpretation and it means the profile of the end is a semicircle in the YZ plane?
# "Outward-facing semicircle in the XY plane".
# If I have a cylinder along X. The end is at X = -L.
# The face is in YZ.
# If I cut a semicircle in XY, I am cutting along the X axis?
# Let's assume the standard interpretation for such linkage parts:
# The ends are rounded. The rounding is usually a fillet or a specific shape.
# "Outward-facing semicircle... radius clevis_slot_end_arc_radius".
# "Centered on the rod axis at X = clevis_slot_end_arc_center_x".
# This implies the center of the arc is at a specific X.
# If the arc is in the XY plane, it lies in the plane Z=0.
# So the arc is a curve in the X-Y plane.
# This defines the boundary of the material in the X-Y plane?
# But the material is a cylinder (Y^2 + Z^2 <= R^2).
# If the boundary is in XY, it restricts X and Y.
# This sounds like the end of the rod is not a flat plane, but a curved surface defined by this arc.
# Specifically, the material exists where X is "inside" the arc?
# Or the material is cut by this arc?
# "defines the rounded trimming boundary".
# "Retain only material that also lies within the cylindrical envelope".
# So we have a cylinder. We cut it with a surface defined by the arc.
# The arc is in XY. Center at (Cx, 0, 0). Radius R_arc.
# Equation: (X - Cx)^2 + Y^2 <= R_arc^2 ?
# If so, this cuts the cylinder.
# Since the cylinder is Y^2 + Z^2 <= R_cyl^2.
# The intersection of these two volumes creates the "rounded end".
# This makes sense. The end is rounded in the X-Y direction, but the Z extent is still limited by the cylinder diameter.
# So the end face is not flat. It's a curved surface.
# And the slots are cut into this.

# Let's refine the plan:
# 1. Base Cylinder: Extrude a circle (YZ plane) along X.
#    Actually, easier: Pad a circle (XY plane) along Z? No, rod is X.
#    Pad a circle (YZ plane) along X.
#    Circle in YZ: Center (0,0,0), Radius = rod_outer_diameter/2.
#    Pad along X axis. Length = Total Length.
#    This creates the cylinder.
#
# 2. The "Lug" shape is defined by the intersection of the cylinder and the "Arc" cut.
#    The Arc cut is in the XY plane.
#    We need to subtract the region outside the arc?
#    "Outward-facing... defines the rounded trimming boundary".
#    Usually, this means the material is kept inside the arc.
#    The arc is centered at X = -233.58. Radius 15.66.
#    The rod extends to the left.
#    So the left end is rounded.
#    We need to cut the cylinder with a plane/surface defined by the arc.
#    Since the arc is in XY, the cut surface is a cylinder of radius R_arc along Z?
#    No, the arc is a 2D curve. To make it a 3D cut, we extrude it along Z?
#    Yes, "Outward-facing semicircle in the XY plane".
#    So we create a sketch in XY plane. Draw the arc.
#    Extrude this sketch along Z to create a cutting surface (a cylinder of radius R_arc).
#    Then subtract this from the main body?
#    Wait, if we subtract a cylinder of radius 15.66 along Z, centered at X=-233.58.
#    The main body is a cylinder of radius 15 along X.
#    The intersection will create the rounded end.
#    But we also have slots.
#
# 3. Slots:
#    "subtract rectangular_slot_count parallel transverse rectangular cutting profiles".
#    "Transverse" means perpendicular to the rod axis (X). So they are in the YZ plane.
#    "Rectangular". Width along Z.
#    "Centers are evenly spaced... centered as a group about Z = 0".
#    "Each cut starts at the absolute X distance first_slot_left_edge_x_offset from the origin".
#    "Extends outward beyond the rounded end".
#    So the slots are extruded along X?
#    Yes, "transverse rectangular cutting profiles".
#    Profile is in YZ plane.
#    Extrude along X.
#    Start X = first_slot_left_edge_x_offset.
#    End X = ? "extends outward beyond the rounded end".
#    The rounded end is at X approx -233.58 - 15.66 = -249.
#    The start is at 210.
#    So the slots go from X=210 to X = -infinity (or until they hit the rounded end).
#    Since we are subtracting, we can just make them long enough to cover the whole part.
#    Length = Total Length + buffer.

# Let's re-evaluate the "Arc" cut.
# If the slots are in YZ plane, and the arc cut is in XY plane (extruded along Z).
# The arc cut is a cylinder along Z.
# The slots are prisms along X.
# The intersection of these cuts with the main cylinder creates the complex end shape.
#
# Wait, "Outward-facing semicircle in the XY plane".
# If the arc is in XY, and we extrude it along Z, we get a cylinder along Z.
# The main body is a cylinder along X.
# The intersection of two cylinders (one along X, one along Z) is a Steinmetz solid-like shape.
# But the arc is only a semicircle.
# "Outward-facing".
# If the arc is (X-Cx)^2 + Y^2 = R^2.
# And we keep the material where (X-Cx)^2 + Y^2 <= R^2?
# This would mean the material is bounded by this cylinder along Z.
# But the main body is bounded by Y^2 + Z^2 <= R_cyl^2.
# So the end shape is the intersection of:
# 1. Cylinder X (Radius R_cyl)
# 2. Cylinder Z (Radius R_arc, centered at X=Cx)
# This creates a rounded end.
#
# However, the slots are "transverse".
# If the slots are in YZ plane, they are perpendicular to X.
# They are extruded along X.
# They start at X=210.
# They go to the left.
# They will intersect the "Cylinder Z" cut.
#
# Let's check the coordinates.
# Cx = -233.58. R_arc = 15.66.
# Leftmost point of arc: -233.58 - 15.66 = -249.24.
# Rightmost point of arc: -233.58 + 15.66 = -217.92.
# Slot start: 210.
# So the slots start at 210 and go left.
# They pass through the arc region (-217 to -249).
# So the slots will be cut into the rounded end.
#
# This seems consistent.
#
# Plan:
# 1. Create Base Cylinder (Pad Circle in YZ along X).
# 2. Create Slot Prisms (Pad Rect in YZ along X).
#    - Profile: Rectangle in YZ. Width = slot_width. Height = infinite (or large).
#    - Position: Centered at Z = 0, 15, -15.
#    - X range: 210 to -1000 (long enough).
# 3. Create End Cut (Pad Arc in XY along Z).
#    - Profile: Semicircle in XY.
#    - Center: (Cx, 0).
#    - Radius: R_arc.
#    - Direction: Along Z.
#    - Type: Subtract?
#    - Wait, if we subtract a cylinder along Z from the main body, we get the rounded end.
#    - But the main body is a cylinder along X.
#    - The intersection of Cylinder X and Cylinder Z is the rounded end.
#    - So we need to subtract the volume of Cylinder Z from Cylinder X?
#    - No, that would remove the center.
#    - We want to KEEP the intersection.
#    - So we need to subtract the COMPLEMENT of the intersection.
#    - Or, simpler:
#      The final shape is Cylinder X INTERSECT Cylinder Z.
#      We can build Cylinder X.
#      Then we need to cut away everything outside Cylinder Z.
#      The region outside Cylinder Z is defined by (X-Cx)^2 + Y^2 > R_arc^2.
#      This is hard to define as a single subtraction.
#      Alternative:
#      The "rounded trimming boundary" implies the end is rounded.
#      Maybe the "Arc" is a sketch on the end face?
#      No, "Outward-facing semicircle in the XY plane".
#      Let's assume the standard way to model this:
#      The end is defined by a surface.
#      We can create a sketch in XY plane.
#      Draw the arc.
#      Extrude it along Z to create a "cutting tool" (a cylinder).
#      If we subtract this cylinder from the main body, we remove the center?
#      No, the main body is Y^2 + Z^2 <= R^2.
#      The cutting tool is (X-Cx)^2 + Y^2 <= R_arc^2.
#      If we subtract the tool, we remove the region where (X-Cx)^2 + Y^2 <= R_arc^2.
#      This removes the center of the rod! That's wrong.
#      We want to KEEP the region where (X-Cx)^2 + Y^2 <= R_arc^2.
#      So we need to subtract the region where (X-Cx)^2 + Y^2 > R_arc
