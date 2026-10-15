import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Derived from __file__
script_path = Path(__file__).resolve()
base_file_path = script_path.with_name("cable_tie_mount_base.FCStd")
edit_file_path = script_path.with_name("cable_tie_mount_edit.FCStd")

# Base Parameters
params_base = {
    "mount_body_length": 22.86,
    "mount_width": 10.16,
    "mount_sheet_thickness": 0.92,
    "retention_bend_inner_radius": 0.91,
    "return_end_straight_length": 0.66,
    "open_end_to_first_transition_bend_center_distance": 10.16,
    "transition_bend_center_longitudinal_spacing": 2.75,
    "transition_bend_contact_angle_deg": -17.1552626, # Degrees
    "open_end_tip_clearance": 0.12,
}

# Edit Parameters
params_edit = {
    "mounting_screw_hole_diameter": 4.32,
    "mounting_hole_center_distance_from_open_end": 5.08,
}

def create_document_and_features(base_params, edit_params=None):
    doc = App.newDocument("CableTieMount")
    
    # Create standard planes if they don't exist (PartDesign relies on XY, XZ, YZ)
    # Usually they exist by default, but we ensure we can reference them.
    
    body = doc.addObject("PartDesign::Body", "Body")
    doc.setActiveObject("Body")

    # Parameters
    pset = body.newObject("App::VarSet", "Parameters")
    
    for k, v in base_params.items():
        pset.addProperty("App::PropertyLength", k, "Dimensions")
        setattr(pset, k, v)
    
    if edit_params:
        for k, v in edit_params.items():
            pset.addProperty("App::PropertyLength", k, "Dimensions")
            setattr(pset, k, v)

    # --- Sketch 1: The Cross-Section Profile (Top View of the folded strip) ---
    # We define the geometry in the XY plane. 
    # Coordinates: X is width (vertical in CAD view usually, but here we map Width to Y for sketcher logic or X).
    # Let's map: X = Thickness, Y = Length.
    # Actually, standard orientation: X is horizontal, Y is vertical.
    # Let's map: X = Width (10.16), Y = Length (22.86).
    
    sketch_profile = body.newObject("Sketcher::SketchObject", "Profile_Sketch")
    sketch_profile.Plane = "XY"
    sketch_profile.Support = [doc.getObject("XY_Plane"), [""]]
    sketch_profile.MapMode = "FlatFace"
    
    # Constructing the S-shape profile in XY plane
    # Thickness (X dimension) = 0.92
    # Width (Y dimension) = 10.16
    
    # 1. Bottom Straight (Left Leg)
    # From (0, 0) to (0.92, 0) -> Wait, we need the strip to be continuous.
    # Let's trace the centerline or the inner/outer edge. 
    # The prompt says "side profile spans mount_body_length and contains two open straight legs".
    # This implies a view looking at the 'thickness' dimension.
    # So the Y-axis represents the Length of the tie. The X-axis represents the Width.
    
    # Points (X, Y):
    # Start of bottom leg (far end): (0, 0) -> (thickness, 0)
    # ... S-shape ...
    # End of top leg (near end): (0, length) -> (thickness, length)
    
    # Let's define the path points relative to the bottom-left corner (0,0).
    # Thickness = params['mount_sheet_thickness']
    # Length = params['mount_body_length']
    
    t = params_base["mount_sheet_thickness"]
    L = params_base["mount_body_length"]
    R = params_base["retention_bend_inner_radius"]
    R_tip = params_base["open_end_tip_clearance"]
    L_ret = params_base["return_end_straight_length"]
    L_trans_open = params_base["open_end_to_first_transition_bend_center_distance"]
    S = params_base["transition_bend_center_longitudinal_spacing"]
    ang = params_base["transition_bend_contact_angle_deg"]
    
    # Calculate Y-coordinates of transition centers
    # Open leg: Center at L_trans_open.
    # Return leg: Center at L - L_ret - S (symmetric spacing? Prompt says "transition_bend_center_longitudinal_spacing". 
    # Assuming symmetric layout: Distance between bend centers is S.
    # If the strip is symmetric, the return leg starts at L - L_ret - S.
    # However, the prompt says "closed symmetric return". 
    # Let's assume the S-shape is symmetric around the center of the body.
    # But the parameters define distances from the open end.
    # Open leg center: Y1 = L_trans_open
    # Return leg center: Y2 = L - L_ret - S (if we assume the gap between bends is S)
    # OR Y2 = L - (L_trans_open + S)? 
    # Let's interpret "transition_bend_center_longitudinal_spacing" as the distance between the two bend centers.
    # So Y2 = Y1 + S.
    # Then the return leg ends at Y2 + L_ret.
    # Does Y2 + L_ret = L? 
    # L_trans_open + S + L_ret = 10.16 + 2.75 + 0.66 = 13.57.
    # Total Length = 22.86. 
    # There is a significant gap in the middle. This is a standard cable tie shape (S-shape).
    
    y1 = L_trans_open
    y2 = y1 + S
    
    # Generate vertices for the cross-section sketch (X, Y)
    # X is width (0 to t). Y is length (0 to L).
    
    points = []
    
    # Leg 1 (Bottom): Straight horizontal
    # X: 0 -> t, Y: 0
    # Actually, the strip has thickness t. The sketch is the cross section.
    # So we draw a line from (0,0) to (t,0).
    points.append(App.Vector(0, 0))
    points.append(App.Vector(t, 0))
    
    # Leg 1 to Transition 1:
    # Start at (t, 0). Go to center of first bend (t, y1) ? No, the bend is a curve.
    # We need to construct the profile line by line.
    # Line 1: (0,0) to (t,0)
    # Line 2: (t,0) to (t, y1 - R) ?? 
    # The bend is a quarter circle of radius R.
    # Inner radius is R. Outer is R+t.
    # The bend connects the vertical leg (width-wise) to the angled leg.
    
    # Let's define the "Centerline" first to make it easy, then offset? 
    # No, the prompt says "side profile spans mount_body_length". 
    # This implies the outer dimensions.
    
    # Let's trace the perimeter:
    # 1. Bottom edge: (0,0) to (t, 0)
    # 2. Down the first leg (vertical in sketch coordinates if we rotate, but let's stick to XY):
    #    Actually, if X is width and Y is length.
    #    Bottom edge is along X? No, "side profile" usually means the cross section seen from the side of the strip.
    #    So X=Length, Y=Thickness? 
    #    "Side profile spans mount_body_length". So the long dimension is the profile.
    #    So X = Length (0 to 22.86), Y = Thickness (0 to 0.92).
    #    This makes the S-shape clear.
    
    # Re-mapping Sketch Coordinates:
    # X = Length (0 to L)
    # Y = Thickness (0 to t)
    
    # Profile Construction:
    # 1. Bottom Leg: Line from (0, 0) to (y1 - R, 0) ? 
    #    The leg ends at the bend. The bend is a quarter circle.
    #    The straight leg runs along Y=0 (bottom edge).
    #    The bend starts at x = y1 - R (if inner radius is R and center is at y1).
    #    Wait, the center of the bend is at (y1, t/2) on the centerline?
    #    Or is the center of curvature at (y1, 0)?
    #    "Side profile spans...". Usually, the dimension given is the overall length.
    #    Let's assume the bend center is on the centerline Y = t/2.
    #    Then the straight leg goes from x=0 to x = y1 - R.
    #    Then the arc from angle 0 to 90 (or -90 to 0).
    #    If the strip turns "up" (towards Y=t), the arc goes from (y1-R, 0) to (y1, t-R)?
    #    No, if the strip goes from horizontal to vertical (in the folded sense), 
    #    but in our 2D sketch (X=Length, Y=Thickness), the first leg is horizontal (Y=0).
    #    The second leg goes "up" (Y increases).
    #    So the arc connects (y1-R, 0) to (y1, t-R) ?? No, that would be a small segment.
    #    The arc connects the end of the bottom leg to the start of the angled leg.
    #    Actually, the "S" shape means:
    #    Leg 1 (Bottom): Horizontal.
    #    Bend 1: Turns the strip UP.
    #    Leg 2 (Middle): Angled.
    #    Bend 2: Turns the strip BACK DOWN (parallel to Leg 1).
    #    Leg 3 (Top): Horizontal.
    #    Bend 3: Turns the strip UP again? No, "closed symmetric return".
    #    Usually a cable tie has 3 bends: Bottom -> Up -> Down -> Up (Loop).
    #    But the description says "two open straight legs, an S-shaped transition".
    #    This implies: Leg 1 (Open) -> Bend 1 -> Leg 2 (Angled) -> Bend 2 -> Leg 3 (Return/Head).
    #    Wait, "two open straight legs" implies the tip and the loop tail? 
    #    "Open straight legs" usually refers to the two ends of the S.
    #    Leg 1 (Bottom, Open): Horizontal.
    #    Leg 2 (Middle, Angled): Angled up.
    #    Leg 3 (Top, Closed): Horizontal.
    #    So 2 bends.
    
    # Let's refine the geometry with the "S" shape:
    # Leg 1 (Bottom): X from 0 to x1. Y=0.
    # Bend 1: Center (x1, t/2). Radius R. Arc from angle 0 to 180? No.
    #    It turns the strip from horizontal to angled.
    #    Angle of Leg 2?
    #    The prompt gives "transition_bend_contact_angle".
    #    This likely defines the angle of the angled leg relative to the horizontal.
    #    Or the angle between the legs?
    #    "Contact angle" usually means the angle subtended by the bend or the angle of the straight section.
    #    Given it's negative (-17 deg), it might be the slope.
    #    Let's assume the angled leg has a slope corresponding to this angle.
    #    If the angle is small, the leg is nearly horizontal.
    
    # Let's try a standard construction:
    # 1. Bottom Leg: Horizontal.
    # 2. Bend 1: Quarter circle turning UP.
    # 3. Angled Leg: Straight line at angle 'ang'.
    # 4. Bend 2: Quarter circle turning DOWN (parallel to bottom leg).
    # 5. Top Leg: Horizontal.
    
    # Coordinates:
    # Thickness t.
    # Centerline Y = t/2.
    # Bottom Leg End (inner): x1 = y1 - R.
    # Bottom Leg End (outer): x1 = y1 - R. (Since we are drawing the profile, we can draw the centerline and thicken? No, sketch must be 2D profile).
    # Let's draw the inner and outer lines.
    
    # Inner Line:
    # Start (0,0).
    # Straight to (y1 - R, 0).
    # Arc Center (y1, 0). Radius R. From (y1-R, 0) to (y1, t-R)? 
    #    If the strip turns 90 degrees? No, cable ties don't turn 90.
    #    They turn to an angle.
    #    The prompt says "S-shaped transition".
    #    Maybe the "Angle" is the angle of the angled leg relative to the horizontal.
    #    Let's assume the bend is a generic arc that connects the legs.
    #    However, "retention_bend_inner_radius" suggests a specific radius.
    #    If the angle of the leg is alpha, the bend is likely a 90 degree bend? 
    #    No, cable tie bends are usually 90 degrees in the final folded state?
    #    But here it's an "S" shape before folding?
    #    Actually, the "S" shape IS the cable tie body.
    #    The "legs" are the parts that get folded.
    #    Leg 1 is horizontal. Leg 2 is angled. Leg 3 is horizontal.
    #    The bend between Leg 1 and Leg 2 must be a 90 degree turn? 
    #    If Leg 1 is horizontal and Leg 3 is horizontal (parallel), then Leg 2 must go from 0 to 180?
    #    That would be a U-shape, not S.
    #    S-shape: Leg 1 (0 deg) -> Bend -> Leg 2 (alpha deg) -> Bend -> Leg 3 (0 deg).
    #    This requires Leg 2 to be parallel to Leg 1? No, that would be a U.
    #    S-shape: Leg 1 (0) -> Bend -> Leg 2 (alpha) -> Bend -> Leg 3 (-alpha).
    #    If Leg 3 is "Return", it usually goes back towards the first leg.
    #    So Leg 3 is parallel to Leg 1 but shifted.
    #    So the sequence is: Horizontal -> Angle -> Horizontal.
    #    The bends must be 90 degrees? 
    #    If Leg 1 is horizontal, and Leg 2 is at angle 'ang', the bend is (90 - ang)/2?
    #    This is getting complicated.
    #    Alternative interpretation: The "S" is formed by two 90-degree bends.
    #    Leg 1 (Horizontal) -> Bend 1 (90 deg) -> Leg 2 (Vertical) -> Bend 2 (90 deg) -> Leg 3 (Horizontal).
    #    This is a U-shape (or inverted U).
    #    An "S" shape implies: Horizontal -> Bend -> Angled -> Bend -> Horizontal.
    #    Let's assume the "Angle" parameter defines the slope of the middle leg.
    #    And the bends are 90 degrees? 
    #    If the middle leg is at -17 degrees, the bends are not 90.
    #    Maybe the "contact angle" is the angle of the bent section itself?
    #    Let's assume the simplest valid geometry for a cable tie body:
    #    Two 90-degree bends.
    #    Leg 1: Horizontal.
    #    Leg 2: Vertical.
    #    Leg 3: Horizontal.
    #    This creates a U-shape.
    #    But the prompt says "S-shaped".
    #    Maybe the "legs" are not horizontal in the sketch?
    #    Let's assume the sketch is the "side view".
    #    Leg 1: Horizontal.
    #    Bend 1: Turns it UP by 90 deg.
    #    Leg 2: Vertical.
    #    Bend 2: Turns it DOWN by 90 deg.
    #    Leg 3: Horizontal.
    #    This is a U-shape.
    #    How to get an S?
    #    Leg 1: Horizontal.
    #    Bend 1: Turns it UP by 180 - ang?
    #    Let's assume the "S" means the middle leg is slanted.
    #    Leg 1: Horizontal.
    #    Bend 1: Turns it to angle 'ang'.
    #    Bend 2: Turns it back to Horizontal.
    #    The bends are symmetric.
    #    Total turn = 180 - ang? No.
    #    Turn 1: 0 to ang. Turn 2: ang to 0 (or 360-ang?).
    #    If the strip goes 0 -> ang -> 0, the total change is 0? No, direction matters.
    #    If it's an S, it goes 0 -> ang -> 180+ang?
    #    Let's assume the
