import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# Helper to get path
SCRIPT_PATH = Path(__file__).resolve()
BASE_FILE = SCRIPT_PATH.parent / f"{SCRIPT_PATH.stem}_base.FCStd"
EDIT_FILE = SCRIPT_PATH.parent / f"{SCRIPT_PATH.stem}_edit.FCStd"

# --- Step 1: Build Base Part ---

doc = App.newDocument("LockingJaw_Base")
doc.Label = "LockingJaw_Base"

# 1. Create Body
body = doc.addObject("PartDesign::Body", "Body")

# 2. Parameters
params = body.newObject("App::VarSet", "Dimensions")
params.addProperty("App::PropertyLength", "locking_jaw_thickness", "Dimensions", "jaw thickness")
params.locking_jaw_thickness = 46.0
params.addProperty("App::PropertyLength", "ball_contact_arc_radius", "Dimensions", "ball contact radius")
params.ball_contact_arc_radius = 25.0
params.addProperty("App::PropertyLength", "main_upper_run_length", "Dimensions", "upper run")
params.main_upper_run_length = 28.0
params.addProperty("App::PropertyLength", "upper_nose_arc_radius", "Dimensions", "nose radius")
params.upper_nose_arc_radius = 8.0
params.addProperty("App::PropertyLength", "main_nose_tip_longitudinal_offset", "Dimensions", "nose tip X")
params.main_nose_tip_longitudinal_offset = 57.46
params.addProperty("App::PropertyLength", "main_nose_tip_vertical_offset", "Dimensions", "nose tip Y")
params.main_nose_tip_vertical_offset = -9.79
params.addProperty("App::PropertyLength", "main_lower_run_length", "Dimensions", "lower run")
params.main_lower_run_length = 41.87
params.addProperty("App::PropertyLength", "side_relief_pocket_depth", "Dimensions", "side relief depth")
params.side_relief_pocket_depth = 6.0
params.addProperty("App::PropertyLength", "ball_socket_radius", "Dimensions", "ball socket radius")
params.ball_socket_radius = 25.4
params.addProperty("App::PropertyLength", "ball_socket_lateral_offset", "Dimensions", "socket lateral")
params.ball_socket_lateral_offset = -6.75
params.addProperty("App::PropertyLength", "ball_socket_longitudinal_offset", "Dimensions", "socket longitudinal")
params.ball_socket_longitudinal_offset = 3.64
params.addProperty("App::PropertyLength", "side_plate_thickness", "Dimensions", "side plate thick")
params.side_plate_thickness = 4.0
params.addProperty("App::PropertyLength", "side_plate_upper_hook_radius", "Dimensions", "hook radius")
params.side_plate_upper_hook_radius = 5.45
params.addProperty("App::PropertyLength", "side_plate_lower_fillet_radius", "Dimensions", "lower fillet")
params.side_plate_lower_fillet_radius = 3.0
params.addProperty("App::PropertyLength", "side_plate_top_edge_offset", "Dimensions", "plate top X")
params.side_plate_top_edge_offset = 33.17
params.addProperty("App::PropertyLength", "side_plate_lower_fillet_center_offset", "Dimensions", "fillet center Y offset")
params.side_plate_lower_fillet_center_offset = 9.78
params.addProperty("App::PropertyLength", "side_plate_outer_height", "Dimensions", "plate outer height")
params.side_plate_outer_height = 12.35
params.addProperty("App::PropertyLength", "side_plate_hook_sweep_angle", "Dimensions", "hook angle")
params.side_plate_hook_sweep_angle = 60.0
params.addProperty("App::PropertyLength", "main_upper_left_junction_long_offset", "Dimensions", "junction X")
params.main_upper_left_junction_long_offset = -2.29
params.addProperty("App::PropertyLength", "main_upper_left_junction_vert_offset", "Dimensions", "junction Y")
params.main_upper_left_junction_vert_offset = 3.0
params.addProperty("App::PropertyLength", "ball_contact_start_angle", "Dimensions", "start angle")
params.ball_contact_start_angle = -143.6036437

# 3. Main Profile Sketch (Front/Right View)
# We define the 2D profile of the jaw on the XZ plane.
# Origin at Ball Contact Center.
sketch_main = body.newObject("Sketcher::SketchObject", "MainProfile")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(math.radians(0), 1, 0, 0))
sketch_main.AttachmentSupport = (App.ActiveDocument.XZ_Plane, [])
sketch_main.ConstrainToPlane = False
sketch_main.LockedPlane = False
sketch_main.LockedTangent = False
sketch_main.LockedNormal = False
sketch_main.ViewObject.Locked = False

# Helper to add constrained geometry
def add_constrained_geometry(points, constraints):
    # points: list of (x, z)
    # constraints: list of strings describing constraints between indices
    # Note: Sketcher API is low level. We add geometry then constraints.
    # For a complex shape, we build it piece by piece.
    pass

# Construct the path for the main body
# Start at Ball Contact Center (0,0)
# Go along negative X (longitudinal) by main_lower_run_length
# Then turn up? No, the description says "horizontal upper and lower runs".
# Let's trace the perimeter on the XZ plane (X=longitudinal, Z=vertical).
# Ball Contact Center is at (0,0).
# Lower run: from (0,0) to (-main_lower_run_length, 0) -> (-41.87, 0)
# Upper run: from (0,0) to (-main_upper_run_length, 0) -> (-28.0, 0)
# Wait, the description says "concave ball-contact edge".
# This implies the inner curve is the ball contact.
# Let's define the profile as a closed loop.
# Start at (0,0).
# 1. Lower edge: Line from (0,0) to (-main_lower_run_length, 0).
# 2. Outer Lower Edge: Line from (-main_lower_run_length, 0) to (main_upper_run_length, side_plate_outer_height)?
#    No, "side plates project from outer faces".
#    The main body is centered across locking_jaw_thickness (Z direction).
#    So the main body extends from -thickness/2 to +thickness/2 in Z.
#    The "side plates" are likely the parts sticking out on the sides (Y direction in 3D, but here we are sketching XZ).
#    Actually, usually "side plates" in a coupler jaw are the side wings.
#    Let's assume the profile sketch is the cross section on the XZ plane (center of the jaw width).
#    The "side plates" are features added via extrusion or patterns on the Y axis?
#    Or are they part of the main profile? "Two mirrored lower side plates project from the outer faces".
#    If we sketch on XZ, "outer faces" are the top/bottom faces of the jaw (Z +/- thickness/2).
#    So the side plates are on the top/bottom faces.

# Let's refine the Main Profile (XZ plane):
# It contains the ball contact arc, upper run, nose, lower run.
# The "side plates" are separate features on the top/bottom faces.

# Main Profile Points (X, Z):
# Start: (0,0)
# Lower Run: Line to (-main_lower_run_length, 0)
# Bottom Edge: Line to (-main_lower_run_length, -locking_jaw_thickness/2)
# Side Plate Bottom: Line to (side_plate_top_edge_offset, -side_plate_outer_height - locking_jaw_thickness/2) ??
#    Description: "side_plate_outer_height_above_main_lower_run = 12.35".
#    So bottom of plate is at Z = -12.35 - thickness/2? Or is the height relative to the run?
#    "above main lower run" implies +Z direction?
#    "lower side plates". Usually side plates are the side wings.
#    Let's assume the "Main Profile" is the central web.
#    The side plates are added later.

# Let's build the central web profile:
# 1. Lower Run: (0,0) -> (-41.87, 0)
# 2. Left Vertical: (-41.87, 0) -> (-41.87, -23)
# 3. Bottom Right Corner: (-41.87, -23) -> (0, -23) ? No, that's not a jaw.
#    A jaw usually has a jaw face.
#    "concave ball-contact edge". This is on the inside.
#    So the profile is the OUTLINE.
#    Inside curve: Arc from (0,0) with radius 25.
#    Start angle: -143.6 degrees.
#    End angle: ? (Usually symmetric or defined by the nose).
#    Nose tip: (57.46, -9.79).
#    Upper run: Horizontal.
#    Lower run: Horizontal.

# Let's construct the Main Profile explicitly:
# Point A: (0, 0) - Ball Contact Center
# Point B: Start of lower run. (0,0).
# Point C: End of lower run. (-41.87, 0).
# Point D: Bottom left corner of main body. (-41.87, -23).
# Point E: Bottom right corner of main body. (0, -23).
#    Wait, the side plates are on the outer faces.
#    So the main body is a block of thickness 46 (Z -23 to 23).
#    The side plates are attached to the top/bottom faces (Z=23 and Z=-23).
#    So the main profile is just the central web?
#    "locking jaw ... has a solid main body centered across locking_jaw_thickness".
#    So the main body IS the block of thickness 46.
#    The side plates are "projecting from the outer faces".
#    This means they stick out in the Y direction (width of the jaw).
#    So the Main Profile sketch should be on the XZ plane and define the shape of the jaw in the XZ plane (including the ball contact and nose).
#    The side plates will be added as pads/pockets on the top and bottom faces (Z=23 and Z=-23).

# Let's define the Main Profile (XZ):
# Start at (0,0).
# 1. Lower Run: Line to (-41.87, 0).
# 2. Outer Lower Edge: Line to (-41.87, -23).
# 3. Bottom Edge: Line to (0, -23). (To close the block back to Z-axis?)
#    No, the nose tip is at X=57.46.
#    So the body extends to the right (positive X).
#    The "lower run" and "upper run" are likely the faces that touch the ball.
#    "concave ball-contact edge".
#    So the inner surface is an arc.
#    The outer surface is the main body shape.
#    Let's assume the profile is the OUTER contour of the main body.
#    Start at (0,0).
#    Go left along lower run: (-41.87, 0).
#    Go down/out to the bottom of the jaw: (-41.87, -23).
#    Go right to the nose tip X? No, the nose is at X=57.
#    So the body is wide.
#    Let's assume the profile goes from (-41.87, -23) to (57.46, -9.79) then to (-28.0, 9.79?) then to (0, 23) then to (0,0)?
#    This is getting ambiguous. Let's try to interpret "locking jaw" standard shape.
#    It's a U-shape or a block with a concave slot.
#    "concave ball-contact edge": The inside of the jaw touches the ball.
#    So the profile is the OUTSIDE of the jaw.
#    Start at (0,0) (Ball Contact Center).
#    The ball contact arc is INSIDE the profile.
#    So the profile starts at (0,0) and goes OUTWARDS.
#    Lower run: Line from (0,0) to (-41.87, 0).
#    Then down to the bottom face: (-41.87, -23).
#    Then across the bottom? Or up to the nose?
#    "rounded upper nose".
#    Nose tip at (57.46, -9.79).
#    Upper run: Horizontal.
#    So from Nose Tip, go left to Upper Run start?
#    Upper run length 28. So from (57.46, -9.79) to (29.46, -9.79)?
#    And then up to the top face (Z=23)?
#    And then left to (-41.87, 23)?

# Let's simplify:
# Profile is a closed loop in XZ.
# 1. (0,0) -> (-41.87, 0) [Lower Run]
# 2. (-41.87, 0) -> (-41.87, -23) [Outer Bottom]
# 3. (-41.87, -23) -> (0, -23) [Bottom Web? Or is it open?]
#    If it's a solid body, it must be closed.
#    Let's assume the bottom is flat from -41.87 to 0.
#    Then from (0, -23) to (57.46, -9.79) [Bottom of Nose]
#    Then Arc to (29.46, -9.79) ? No, nose tip is at 57.46.
#    Let's assume the nose tip is the outermost point.
#    Nose Arc: Center (57.46, -9.79), Radius 8.
#    End of nose arc at (29.46, -9.79)?
#    Then Upper Run: (29.46, -9.79) -> (29.46, 23)? No, upper run is horizontal.
#    So (29.46, -9.79) -> (29.46, 9.79)? No.
#    Let's assume the Upper Run is from X=29.46 to X=0?
#    "main_upper_run_length = 28.0".
#    If the nose tip is at 57.46, and the run is 28, then the run starts at 57.46 - 28 = 29.46.
#    So Upper Run: (29.46, Y_nose) -> (29.46, 23)? No, horizontal.
#    (29.46, 23) -> (57.46, 23)? No, nose tip is lower.
#    Maybe the nose tip is the lowest point of the upper run?
#    "main_nose_tip_vertical_offset = -9.79".
#    So the nose tip is below the center line.
#    Upper run is "horizontal".
#    So the upper run is at Z = -9.79?
#    Then it goes from X=29.46 to X=57.46?
#    Then the nose arc connects the upper run to the nose tip?
#    "rounded upper nose".
#    So Arc from (57.46, -9.79) to (29.46, -9.79)? That's a straight line.
#    Maybe the nose arc connects the upper run (at Z=23?) to the nose tip?
#    This is too speculative.
#    Let's try a different interpretation:
#    The profile is the shape of the jaw facing the ball.
#    It has a concave edge.
#    Start at (0,0).
#    Arc (Ball Contact) from start angle -143.6 to some end angle.
#    Then straight lines.
#    Let's define the points manually based on the description "concave ball-contact edge, horizontal upper and lower runs, a rounded upper nose".
#    Point 1: (0,0)
#    Point 2: (-41.87, 0) [End of lower run]
#    Point 3: (-41.87, -23) [Bottom of jaw]
#    Point 4: (0, -23) [Corner of main block]
#    Point 5: (57.46, -9.79) [Nose Tip]
#    Point 6: (29.46, -9.79) [Start of Upper Run]
#    Point 7: (29.46, 23) [Top of jaw]
#    Point 8: (-41.87, 23) [Top Left Corner]
#    Point 9: (0, 23) [Top Right Corner]
#    Point 10: (0,0) [Back to start]
#    This creates a block with a nose sticking out.
#    Now add the Ball Contact Arc inside.
#    Arc from (
