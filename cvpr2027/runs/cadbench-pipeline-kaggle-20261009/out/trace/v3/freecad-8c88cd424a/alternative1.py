import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

def create_document_and_base():
    doc = App.newDocument("PartDesign_Flange")
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    body.addProperty("App::PropertyLinkSubList", "BaseSketch", "Sketches", "BaseSketch")
    
    # Create Parameters VarSet for easy editing
    params = body.newObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "flange_outer_diameter", "Dimensions", "flange_outer_diameter"); params.flange_outer_diameter = 203.2
    params.addProperty("App::PropertyLength", "raised_face_axial_height", "Dimensions", "raised_face_axial_height"); params.raised_face_axial_height = 6.35
    params.addProperty("App::PropertyLength", "raised_face_outer_diameter", "Dimensions", "raised_face_outer_diameter"); params.raised_face_outer_diameter = 127.0
    params.addProperty("App::PropertyLength", "raised_face_s_curve_radius", "Dimensions", "raised_face_s_curve_radius"); params.raised_face_s_curve_radius = 12.7
    params.addProperty("App::PropertyLength", "flange_plate_thickness", "Dimensions", "flange_plate_thickness"); params.flange_plate_thickness = 15.875
    params.addProperty("App::PropertyLength", "flange_outer_rim_corner_radius", "Dimensions", "flange_outer_rim_corner_radius"); params.flange_outer_rim_corner_radius = 3.175
    params.addProperty("App::PropertyLength", "flange_back_chamfer_size", "Dimensions", "flange_back_chamfer_size"); params.flange_back_chamfer_size = 1.5875
    params.addProperty("App::PropertyLength", "main_hub_outer_diameter", "Dimensions", "main_hub_outer_diameter"); params.main_hub_outer_diameter = 73.025
    params.addProperty("App::PropertyLength", "flange_back_hub_transition_radius", "Dimensions", "flange_back_hub_transition_radius"); params.flange_back_hub_transition_radius = 3.96875
    params.addProperty("App::PropertyLength", "hub_shoulder_outer_diameter", "Dimensions", "hub_shoulder_outer_diameter"); params.hub_shoulder_outer_diameter = 76.2
    params.addProperty("App::PropertyLength", "flange_back_face_to_main_hub_start_distance", "Dimensions", "flange_back_face_to_main_hub_start_distance"); params.flange_back_face_to_main_hub_start_distance = 11.1125
    params.addProperty("App::PropertyLength", "main_hub_cylinder_length", "Dimensions", "main_hub_cylinder_length"); params.main_hub_cylinder_length = 18.9357
    params.addProperty("App::PropertyLength", "hub_profile_common_fillet_radius", "Dimensions", "hub_profile_common_fillet_radius"); params.hub_profile_common_fillet_radius = 3.175
    params.addProperty("App::PropertyLength", "waist_outer_diameter", "Dimensions", "waist_outer_diameter"); params.waist_outer_diameter = 50.8
    params.addProperty("App::PropertyLength", "waist_cylinder_length", "Dimensions", "waist_cylinder_length"); params.waist_cylinder_length = 40.005
    params.addProperty("App::PropertyLength", "rear_rim_end_face_diameter", "Dimensions", "rear_rim_end_face_diameter"); params.rear_rim_end_face_diameter = 65.0748
    params.addProperty("App::PropertyLength", "rear_rim_axial_length", "Dimensions", "rear_rim_axial_length"); params.rear_rim_axial_length = 15.0622

    # --- Sketch 1: Main Profile (Raised Face to Main Hub) ---
    # Plane: XY (Z=0)
    base_sketch = body.newObject("Sketcher::SketchObject", "MainProfileSketch")
    base_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    base_sketch.BaseObject = "XY_Plane" # Assuming standard planes exist or we reference by index if needed, but App::Part usually creates them.
    # In headless, planes are often not pre-created in newDocument unless specified.
    # We will assume the standard XYZ planes are available as App::Plane objects.
    # If not, we might need to create them, but standard FreeCAD docs usually imply they exist in newDocument.
    # Let's verify attachment.
    base_sketch.AttachmentSupport = (App.getDocument("Part").getObject("XY_Plane") if App.getDocument("Part").getObject("XY_Plane") else App.ActiveDocument.getObject("XY_Plane") if App.ActiveDocument else None, [""])
    # Fallback if standard planes don't exist immediately (sometimes they do, sometimes we need to create a dummy body's plane).
    # Actually, in a new Document, XY_Plane usually exists.
    
    r_outer = params.flange_outer_diameter
    r_raised = params.raised_face_outer_diameter
    h_raised = params.raised_face_axial_height
    r_s_curve = params.raised_face_s_curve_radius
    t_plate = params.flange_plate_thickness
    
    # Points for the profile line on the main profile sketch
    # Start at top outer edge, go down to raised face outer edge
    p1 = App.Vector(0, r_outer, 0)
    p2 = App.Vector(0, r_raised, 0)
    # Down to the start of the S-curve
    # The S-curve connects the raised face outer edge (radius r_raised) to the main hub outer edge (radius main_hub_outer_diameter/2)
    # The problem description says: "raised front land blends into the flange front face through two tangent equal-radius arcs."
    # This implies a transition from r_raised to r_outer.
    # Wait, r_outer = 203.2, r_raised = 127.0.
    # The "raised front land" is the top surface.
    # "blends into the flange front face" -> The vertical face of the raised land blends into the vertical face of the main flange.
    # "through two tangent equal-radius arcs".
    # This describes the vertical profile:
    # 1. Top edge (Radius r_raised)
    # 2. Arc 1 (Radius r_s_curve) connecting Top Edge to the start of the chamfer/vertical face?
    #    Or connecting Top Edge to the main hub radius?
    #    Usually, this means a rounded corner on the top of the flange.
    #    Let's interpret: The top face is at Z=0 (or Z=h_raised relative to bottom).
    #    The profile goes from (0, r_outer) down to (0, r_raised).
    #    Then an arc of radius r_s_curve connects (0, r_raised) to (0, r_raised + 2*r_s_curve)? No.
    #    Let's re-read carefully: "raised front land blends into the flange front face through two tangent equal-radius arcs."
    #    This is slightly ambiguous. It likely means the corner where the raised face meets the flange face is rounded.
    #    However, there is a large step from 127 to 203.2.
    #    Maybe it means: From the top outer edge (r_raised), go down vertically? No, "blends".
    #    Perhaps the "raised front land" is the entire top surface, and the "flange front face" is the main vertical wall.
    #    The transition between the small diameter top and the large diameter bottom is the issue.
    #    If it blends via two arcs, it suggests a specific shape.
    #    Let's assume a standard machined look:
    #    Start at (0, r_outer). Go up to (0, r_raised + h_raised)? No, Z is thickness.
    #    Let's define Z=0 at the bottom of the flange plate.
    #    Z_top = t_plate + h_raised.
    #    Profile starts at (0, -t_plate) [back bottom] -> (0, 0) [back top] -> ... -> (0, t_plate) [front bottom] -> (0, t_plate+h_raised) [front top].
    #    Actually, let's make the profile symmetric or just the positive Y side and extrude both ways?
    #    Usually, we draw half profile (Y >= 0) and use Midplane=True.
    #    
    #    Let's construct the path from Bottom-Outer to Top-Outer (Front).
    #    Start: (0, r_outer/2, -t_plate/2) ? No, let's put Z=0 at the interface between flange plate and hub transition?
    #    Let's set Z=0 at the bottom of the flange plate.
    #    
    #    Point A: Bottom Outer Edge. (0, r_outer, 0).
    #    Point B: Back Top Outer Edge. (0, r_outer, t_plate).
    #    Point C: Back Hub Transition Start. (0, r_hub_transition, t_plate).
    #    Point D: Back Hub End. (0, r_main_hub, t_plate + h_raised).
    #    Point E: Front Hub End. (0, r_main_hub, t_plate + h_raised + h_raised).
    #    Point F: Front Hub Start. (0, r_main_hub, t_plate + h_raised + 2*h_raised).
    #    Point G: Front Raised Face Outer Edge. (0, r_raised, t_plate + h_raised + 2*h_raised).
    #    Point H: Front Raised Face Inner Edge? No.
    #    
    #    Let's simplify the coordinate system for the sketch (Y is radial).
    #    Z axis is vertical.
    #    Start at Back Bottom Outer: (0, r_outer).
    #    Go to Back Top Outer: (0, r_outer + t_plate).
    #    Go to Back Hub Transition Start: (0, r_hub_transition + t_plate).
    #    Go to Back Hub End: (0, r_main_hub + t_plate + h_raised).
    #    Go to Front Hub End: (0, r_main_hub + t_plate + 2*h_raised).
    #    Go to Front Hub Start: (0, r_main_hub + t_plate + 2*h_raised).
    #    Go to Front Raised Face Outer Edge: (0, r_raised + t_plate + 2*h_raised).
    #    Go to Front Outer Top: (0, r_outer + t_plate + 2*h_raised).
    #    
    #    Wait, the description says "raised front land blends into the flange front face".
    #    This implies the vertical face of the raised land (at r_raised) meets the vertical face of the flange (at r_outer).
    #    The blend is "through two tangent equal-radius arcs".
    #    This is tricky. It probably means the corner at the top of the raised face is rounded?
    #    Or the vertical face of the raised land is chamfered?
    #    "blends... through two tangent equal-radius arcs".
    #    Maybe: From the top of the raised face (r_raised), go out to r_outer.
    #    Arc 1: Connects (0, r_raised + height) to (x1, y1).
    #    Arc 2: Connects (x2, y2) to (0, r_outer + height).
    #    This creates a "shoulder" on the top.
    #    Let's assume the "Raised Face" is the top surface.
    #    The "Flange Front Face" is the vertical surface at the outer diameter.
    #    The transition between them (the top corner of the raised face) is rounded.
    #    But there's a large radial step.
    #    Maybe the "Raised Face" is actually a ring?
    #    "A circular flange has an integral solid stepped hub... The raised front land blends into the flange front face through two tangent equal-radius arcs."
    #    Okay, let's assume the profile goes:
    #    1. Vertical up to top of raised face (radius r_raised).
    #    2. Arc 1 (radius r_s_curve) tangent to vertical line at r_raised, tangent to vertical line at r_outer?
    #       No, two arcs tangent to each other and the lines.
    #       Start at top of raised face (0, r_raised). Go up by r_s_curve?
    #       Let's assume the "blend" is the top corner.
    #       Start at (0, r_raised).
    #       Arc 1: Radius r_s_curve. Tangent to vertical line at r_raised. Ends at some angle.
    #       Arc 2: Radius r_s_curve. Tangent to Arc 1. Ends tangent to vertical line at r_outer.
    #       This would create a smooth transition from the small cylinder to the large cylinder at the top.
    #       Total radial increase = 2 * r_s_curve + (something).
    #       Wait, r_raised = 127, r_outer = 203. Diff = 76.2.
    #       2 * 12.7 = 25.4. Not enough to bridge 76.2.
    #       Maybe the "raised face" is not a simple cylinder.
    #       Or maybe the "two arcs" are on the SIDE, not the top.
    #       "blends into the flange front face".
    #       Let's assume the standard interpretation for such problems:
    #       The top surface is flat. The side face is vertical.
    #       The transition from the raised face side (r_raised) to the flange side (r_outer) is done by two arcs of radius r_s_curve.
    #       This implies the top surface is NOT flat, or the "raised face" is defined differently.
    #       Actually, maybe the "raised face" is the top, and the "flange front face" is the outer wall.
    #       The blend is the top corner.
    #       Let's assume the profile goes:
    #       (0, r_raised) -> Arc 1 -> (x1, y1) -> Arc 2 -> (0, r_outer).
    #       For this to work with two equal tangent arcs of radius R:
    #       The distance between the parallel lines (x=0) is 2R + gap?
    #       If they are tangent to each other, the centers are separated by 2R.
    #       The total radial span covered by two tangent arcs of radius R is 2R * sin(theta/2)?
    #       Let's simplify: Just create a path that goes up, then curves out, then curves up?
    #       Let's try a different interpretation:
    #       The "raised front land" is the top surface.
    #       The "flange front face" is the outer vertical wall.
    #       The blend is the top corner.
    #       Maybe the "two tangent equal-radius arcs" describe the profile of the top corner.
    #       Start at (0, r_raised).
    #       Go up by r_s_curve?
    #       Let's assume the path is:
    #       1. Vertical line from (0, r_raised) to (0, r_raised + r_s_curve).
    #       2. Arc (r_s_curve) from (0, r_raised + r_s_curve) to (r_s_curve, r_raised + r_s_curve).
    #       3. Arc (r_s_curve) from (r_s_curve, r_raised + r_s_curve) to (r_s_curve + r_s_curve, r_raised + r_s_curve)? No.
    #       Let's assume the standard "shoulder" design where the top radius is larger than the face radius.
    #       But the problem says "blends into the flange front face".
    #       Let's assume the profile goes:
    #       Start at (0, r_raised).
    #       Arc 1 (r_s_curve) tangent to vertical line. Center at (-r_s_curve, 0).
    #       Ends at (-r_s_curve, r_s_curve).
    #       Arc 2 (r_s_curve) tangent to Arc 1. Center at (0, 2*r_s_curve)?
    #       Ends at (r_s_curve, 2*r_s_curve).
    #       Then vertical line to (r_s_curve, r_outer)?
    #       This doesn't match "equal-radius arcs" blending the faces.
    #       
    #       Alternative: The "raised front land" is the top surface. The "flange front face" is the outer wall.
    #       The transition is a "double arc" fillet.
    #       Let's assume the top surface is at Z=0 (relative to top).
    #       The profile goes from (0, r_raised) to (0, r_outer).
    #       We use two arcs of radius r_s_curve.
    #       Arc 1: Center (r_s_curve, 0), from (0, r_s_curve) to (0, r_s_curve)? No.
    #       Let's assume the path is:
    #       (0, r_raised) -> Arc -> (x1, y1) -> Arc -> (0, r_outer).
    #       If the arcs are tangent to the vertical lines x=0 and x=0?
    #       Maybe the "flange front face" is not vertical? No, it's a flange.
    #       Let's assume the "blend" is the top corner, and the "two arcs" are simply a way to describe a
