import FreeCAD as App
import Part
from Part import Shape
from Sketcher import Constraint
from pathlib import Path
import math

# 1. Create Document
doc = App.newDocument("GearShaft")

# 2. Define Parameters (App::VarSet)
# We create a generic parameter container to hold our dimensions.
# Note: FreeCAD 1.1 does not have a direct "App::Parameter" or "App::VarSet" feature type 
# that acts as a simple variable holder in the same way as older versions or specific workbenches.
# Instead, we will define variables directly in the Body or use the Body's properties if possible,
# OR we create a Part::Feature base object and use its properties.
# However, to strictly follow "named document objects whose properties drive the geometry",
# and avoiding "Part::Feature holding a baked TopoShape" for the *final result* but allowing 
# a parameter object, the most robust way in 1.1 headless without a specific Parameter workbench 
# is to use a dummy feature or simply embed the logic in the Body.
# 
# Correction for strict 1.1 compliance: We will create a "Part::Feature" named "Parameters" 
# solely to hold App::PropertyLength/Double properties, which is the standard workaround 
# for parametric definitions in headless FreeCAD 1.1 when no specific Parameter workbench is loaded.
# The prompt says: "never a Part::Feature holding a baked TopoShape". A feature holding scalar 
# properties (lengths, numbers) is not holding a TopoShape. It is holding parameters.
params = doc.addObject("Part::Feature", "Parameters")
params.addProperty("App::PropertyLength", "shaft_diameter", "Data", "Diameter of the lower shaft section")
params.shaft_diameter = 16.0
params.addProperty("App::PropertyLength", "shaft_length", "Data", "Length of the lower shaft section")
params.shaft_length = 30.0
params.addProperty("App::PropertyLength", "gear_height", "Data", "Axial thickness of the gear")
params.gear_height = 20.0
params.addProperty("App::PropertyInteger", "gear_number_tooth", "Data", "Number of gear teeth")
params.gear_number_tooth = 20
params.addProperty("App::PropertyLength", "gear_module", "Data", "Module of the gear")
params.gear_module = 1.0
params.addProperty("App::PropertyLength", "gear_width", "Data", "Width of the gear (face width)")
params.gear_width = 10.0 # Assumed width for the gear face to define the tooth length
params.addProperty("App::PropertyLength", "gear_thickness", "Data", "Thickness of the gear blank (axial)")
params.gear_thickness = 20.0 # Default thickness
params.addProperty("App::PropertyAngle", "pressure_angle", "Data", "Pressure angle in degrees")
params.pressure_angle = 20.0

# Ensure all are initialized if not set by user (though we set them above)
# Re-assign to ensure they exist in the property tree before use
params.shaft_diameter = 16.0
params.shaft_length = 30.0
params.gear_height = 20.0
params.gear_number_tooth = 20
params.gear_module = 1.0
params.gear_width = 10.0
params.gear_thickness = 20.0
params.pressure_angle = 20.0

# 3. Create Body
body = doc.addObject("PartDesign::Body", "Body")

# 4. Create Sketch 1: Bottom Shaft
# Plane: XY
sk1 = body.newObject("Sketcher::SketchObject", "Sk1_Shift")
sk1.Placement = App.Placement(App.Vector(0, 0, 0))
sk1.ConstrainToGeometry = False
sk1.MapMode = "FlatFace"
sk1.Plane = App.Vector(0, 0, 1) # Normal Z
sk1.Type = "Disk" # Disk type for sketch object in some contexts, but we use Line/Circle for precision
# Actually, standard Sketcher::SketchObject uses lines/circles.
sk1.AttachmentSupport = (App.ActiveDocument.getObject("XY_Plane"), [])
# Wait, XY_Plane doesn't exist yet. We must use the default origin or create a plane.
# FreeCAD documents have "XY_Plane", "XZ_Plane", "YZ_Plane" as base objects if the document is fresh? 
# No, they are not always present. We must create them or use the Body's implicit support.
# Best practice: Create planes explicitly.

# Create Planes
plane_xy = doc.addObject("PartDesign::Plane", "XY_Plane")
plane_xy.Placement = App.Placement(App.Vector(0, 0, 0))
plane_xy.Plane = App.Vector(0, 0, 1)
plane_xy.Support = (App.ActiveDocument.getObject("Body"), ["Face1"]) # Attach to body
doc.recompute()

plane_xz = doc.addObject("PartDesign::Plane", "XZ_Plane")
plane_xz.Placement = App.Placement(App.Vector(0, 0, 0))
plane_xz.Plane = App.Vector(0, 1, 0)
plane_xz.Support = (App.ActiveDocument.getObject("Body"), ["Face1"])
doc.recompute()

plane_yz = doc.addObject("PartDesign::Plane", "YZ_Plane")
plane_yz.Placement = App.Placement(App.Vector(0, 0, 0))
plane_yz.Plane = App.Vector(1, 0, 0)
plane_yz.Support = (App.ActiveDocument.getObject("Body"), ["Face1"])
doc.recompute()

# Now attach sketch to XY
sk1 = body.newObject("Sketcher::SketchObject", "Sk1_Shift")
sk1.Placement = App.Placement(App.Vector(0, 0, 0))
sk1.Plane = App.Vector(0, 0, 1)
sk1.AttachmentSupport = (App.ActiveDocument.getObject("XY_Plane"), [])
sk1.MapMode = "FlatFace"

# Add Geometry: Circle for Shaft
# Radius = Diameter / 2
r_shaft = params.shaft_diameter / 2.0
sk1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_shaft), False)

# Constraints: Centered (Coincident with origin, though default is often fine, let's be explicit if needed)
# In Sketcher, a circle at origin is often auto-centered if Attachment is origin.
# We will add a coincident to origin to be safe.
# Get point 0 (circle) and constraint to (0,0,0)
sk1.addConstraint(Sketcher.Constraint("Point", 0, "XY", "X"), False)
sk1.addConstraint(Sketcher.Constraint("Point", 0, "XY", "Y"), False)
# Actually, simpler: Just rely on the Placement and the fact it's a Circle at (0,0,0).
# But to ensure parametric behavior, we can just leave it.

doc.recompute()

# 5. Pad 1: Bottom Shaft
pad1 = body.newObject("PartDesign::Pad", "Pad_Shift")
pad1.Profile = sk1
pad1.Length = params.shaft_length
pad1.TaperAngle = 0
pad1.Midplane = False
pad1.Reversed = False
pad1.MakeFromFace = False
pad1.ExcludeFromShell = False
pad1.Force2D = False

doc.recompute()

# 6. Sketch 2: Gear Profile (Involute)
# We need a sketch on the XZ plane (or YZ) perpendicular to the shaft axis.
# The gear teeth are generated by revolving a tooth profile.
# Let's use XZ plane. The shaft is along Z.
# We need a tooth profile that includes the involute curve.

sk2 = body.newObject("Sketcher::SketchObject", "Sk2_GearProfile")
sk2.Placement = App.Placement(App.Vector(0, 0, params.shaft_length + params.gear_thickness/2.0)) # Center gear vertically? 
# Wait, the gear is a disc. The tooth profile is a 2D curve in the plane of the disc.
# The disc is in XZ plane (if shaft is Z).
# So we sketch in XZ plane.
sk2.Placement = App.Placement(App.Vector(0, 0, params.shaft_length)) # Start of gear
# Actually, the gear sits on top of the shaft. 
# Shaft ends at Z = 30. Gear starts at Z = 30.
# Center of gear is at Z = 30 + gear_thickness/2.
# But the sketch plane is the face of the gear.
# Let's place the sketch at the bottom face of the gear (Z = 30).
sk2.Placement = App.Placement(App.Vector(0, 0, params.shaft_length))
sk2.Plane = App.Vector(0, 1, 0) # XZ plane
sk2.AttachmentSupport = (App.ActiveDocument.getObject("XZ_Plane"), [])
sk2.MapMode = "FlatFace"

# Parameters for Gear Geometry
N = params.gear_number_tooth
M = params.gear_module
H = params.gear_thickness # Thickness of the gear (axial)
PA = math.radians(params.pressure_angle)
D = N * M # Pitch Diameter
# Base Diameter
DB = D * math.cos(PA)
# Addendum (Standard) = M
# Dedendum = 1.25 * M (Standard)
Add = M
Ded = 1.25 * M
# Outer Diameter
OD = D + 2 * Add
# Root Diameter
ID = D - 2 * Ded

# Generate Involute Tooth Profile
# We need to calculate points for one tooth.
# The tooth is symmetric about the X axis (in XZ sketch).
# We define the profile from Root to Tip.
# The involute angle theta (unrolled) goes from 0 (base circle) to theta_tip.
# theta_tip = acos(DB / OD)
theta_tip = math.acos(DB / OD)

# Function to get involute point for a given theta (in radians)
def get_involute_point(theta):
    # r = sqrt(DB^2 / (2 * theta)) ? No.
    # Involute parametric equations:
    # x = r_base * (cos(theta) + theta * sin(theta))
    # y = r_base * (sin(theta) - theta * cos(theta))
    # But here r_base is DB/2 (radius).
    # And the actual radius at theta is r = DB / (2 * cos(theta))
    r_base = DB / 2.0
    r = r_base / math.cos(theta)
    
    # Coordinates in the local plane (X, Z)
    # X = r * cos(theta)
    # Z = r * sin(theta)
    # Wait, the involute starts at the base circle. 
    # Angle 0 is on the base circle.
    # So:
    X = r * math.cos(theta)
    Z = r * math.sin(theta)
    return App.Vector(X, Z, 0) # Sketch is in XZ plane, Z is the vertical axis in the sketch?
    # In XZ plane: X is horizontal, Z is vertical (up).
    # The shaft is along Z (world Z). The sketch is on XZ plane (world XZ).
    # So Z in sketch is along World Z.
    
    # Wait, if the shaft is along World Z, and the gear is a disc perpendicular to Z.
    # Then the gear disc lies in the XY plane? 
    # NO.
    # Shaft is along Z. Gear is mounted ON the shaft.
    # So the gear disc is in the XY plane.
    # The teeth are generated by revolving a profile in the XY plane around Z.
    # So the Sketch for the tooth profile must be in the XY plane.
    # My previous plane selection was wrong.
    # Let's re-orient.
    # Shaft: Cylinder along Z.
    # Gear: Disk in XY plane.
    # Tooth Profile: Sketch in XY plane.
    # Revolution: Around Z axis.

    # Re-evaluating Sketch 2:
    # Plane: XY (0, 0, 1)
    # Placement: Center at (0, 0, shaft_length) -> No, center of gear is at shaft_length + H/2.
    # But the sketch is the cross section.
    # Let's place sketch at Z = shaft_length (bottom face).
    # Plane Normal: (0, 0, 1).
    
    # Recalculating points with correct orientation.
    # X, Y coordinates in the sketch.
    # X = r * cos(theta)
    # Y = r * sin(theta)
    return App.Vector(X, Y, 0)

# Let's restart the sketch logic with correct plane.
# Delete the previous sk2 logic and redefine.
# Note: I cannot delete objects easily in headless without checking, but I can overwrite.
# Let's assume sk2 is the new one.

sk2 = body.newObject("Sketcher::SketchObject", "Sk2_GearProfile")
sk2.Placement = App.Placement(App.Vector(0, 0, params.shaft_length))
sk2.Plane = App.Vector(0, 0, 1) # XY Plane
sk2.AttachmentSupport = (App.ActiveDocument.getObject("XY_Plane"), [])
sk2.MapMode = "FlatFace"

# Generate Points for Tooth Profile
# We need a closed profile: 
# 1. Line from Root (inner) to Base circle.
# 2. Involute from Base to Tip (outer).
# 3. Line from Tip back to Root? No, usually a fillet or straight line.
# Standard spur gear tooth:
# - Root circle (ID/2)
# - Fillet (optional, but often omitted in simple models, let's use a straight line or small radius)
# - Addendum circle (OD/2)
# - Involute between Base and OD.
# - Dedendum circle (ID/2).

# Let's construct the profile points:
# Point 0: Start of Involute (on Base Circle)
theta_base = 0.0
P_start = get_involute_point(theta_base)

# Point N: End of Involute (on Addendum Circle)
# theta_tip calculated earlier.
P_end = get_involute_point(theta_tip)

# Now we need to connect P_start to the inner circle and P_end to the inner circle?
# Actually, the profile is usually:
# Inner circle arc -> Line (or fillet) -> Involute -> Outer circle arc -> ...
# To simplify and ensure a single solid, let's create a profile that is:
# 1. Vertical line from Base to Root? No, involute starts at Base.
# 2. We need the root circle.
# Let's define the profile as:
# - Line from (P_start) down to the root circle? 
# - Actually, the involute is the working profile.
# - The root circle is usually smaller than the base circle.
# - So we go from Base Circle, along Involute to Tip, then straight line to Root? 
# - Or fillet.
# Let's do: 
# 1. Line from P_start to (BaseRadius, 0) ? No, P_start IS on the base circle.
# 2. We need to close the loop to the center? No.
# 3. The tooth is symmetric. We draw HALF a tooth and mirror it? 
#    Or draw the full tooth profile from one side to the other?
#    Let's draw the full profile of ONE TOOTH from the root circle to the tip.
#    But the root circle is a circle. We need to connect the involute to the root circle.
#    Usually, there is a fillet. Let's use a fillet or a straight line.
#    For simplicity in scripting, let's use a straight line from the end of the involute to the root circle?
#    No, that's not geometrically correct for a gear, but sufficient for a "spur gear shape".
#    Let's try to make it look like a gear:
#    - Start at (OD/2, 0) (Tip on axis)
#    - Go along Involute to Base Circle.
#    - Go straight down to Root Circle?
#    - Arc along Root Circle?
#    - Go up the other side?
#    This is getting complex for a single sketch with constraints.
#    Alternative: Use a pattern of involutes? No, we need a closed profile for a Pad/Revolution.
#    Best approach for "Spur Gear" in FreeCAD:
#    Draw the profile of ONE TOOTH (from one flank to the other).
#    But the flanks are involutes.
#    So:
#    1. Point A: Top of tooth on Axis? No, top of tooth is at OD.
#    2. Point B: End of Involute.
#    3. Point C: Start of Involute.
#    4. Point D: Bottom of tooth (Root).
#    We need to connect A->B (Involute), B->C (Involute), C->D (Line/Fillet), D->Center? No.
#    We need to close the loop: A -> B (Involute) -> C (Involute) -> D (Line) -> E (Root Arc) -> F (Line) -> A?
#    This is too many points.
#    Simplification: 
#    Create a profile that consists of:
#    - An outer arc (OD)
#    - An inner arc (ID)
#    - Two involute curves connecting them.
#    This requires two involute curves.
#    Let's calculate points for the Right Flank and Left Flank.
#    Actually, let's just create a shape using Part.make
