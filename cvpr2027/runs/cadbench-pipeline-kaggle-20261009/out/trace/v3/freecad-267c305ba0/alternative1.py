from pathlib import Path
import FreeCAD as App
import Part
from math import radians, cos, sin, sqrt

# --- Configuration & Parameters ---
# Base Part Parameters
params_base = {
    "base_cap_overall_height": 420.0,
    "outer_diameter": 367.4643772,
    "base_inner_diameter": 263.8437432,
    "body_transition_arc_radius": 45.0,
    "body_transition_arc_start_angle": -90.0,
    "body_transition_arc_end_angle": -2.5,
    "top_transition_arc_start_angle": 2.5,
    "top_transition_arc_end_angle": 90.0,
    "lip_fillet_arc_radius": 12.0,
    "lip_step_diameter": 50.0,
    "lip_fillet_start_diameter": 74.0,
    "lip_step_height": 8.0,
    "lip_rim_radial_width": 25.0,
    "wall_thickness": 4.0,
    "bayonet_slot_y_position": 185.8894096
}

# Edit Part Parameters (Target)
params_edit = {
    "bayonet_slot_outer_arc_radius": 119.9218716,
    "bayonet_slot_inner_arc_radius": 116.9218716,
    "bayonet_slot_ring_central_angle": 250.0,
    "bayonet_ledge_depth": 100.0,
    "bayonet_slot_arc_radius": 25.0,
    "bayonet_slot_arc_central_angle": 180.0,
    "bayonet_slot_straight_length": 36.0,
    "cap_outer_diameter": 239.8437432,
    "cap_inner_diameter": 233.8437432,
    "cap_wall_thickness": 3.0,
    "lower_cap_ring_depth": 30.0
}

def create_base_document():
    """Creates the Base Part document."""
    doc = App.newDocument("BayonetCap_Base")
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Parameters Object (to drive geometry via expressions)
    params_var = body.newObject("App::Variable", "BaseParams")
    params_var.addProperty("App::PropertyBool", "visible")
    params_var.visible = False # Hide the variable object itself, just use its properties
    
    # Set Base Parameters as Variables or direct properties
    # For simplicity in this script structure, we set them as direct properties on a container 
    # or rely on the feature's direct settings. 
    # To strictly follow "named document objects whose properties drive the geometry", 
    # we will use App::Variable or just set the features directly. 
    # Given the complexity of the expression engine in headless mode without a GUI, 
    # setting values directly on the features is the most robust approach for a standalone script.
    
    # 1. Main Body Profile Sketch (XY Plane)
    sketch_main = body.newObject("PartDesign::Sketcher", "MainProfile")
    sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_main.AttachmentSupport = (doc.getObject("XY_Plane"), [])
    
    # Define Profile Points
    # We need a complex profile: 
    # Outer arc (start to end) -> Top Lip Step -> Top Lip Arc -> Inner Arc (start to end) -> Floor -> Floor Inner Arc
    # Angles are relative to the bottom (0 deg). 
    # However, the prompt defines transitions. Let's interpret:
    # Base Inner Diameter (Bottom) -> Wall Up -> Transition Arc (Start -90 to End -2.5) -> Wall Up -> Top Lip Step -> Lip Rim -> Inner Lip Arc -> Top Floor.
    
    # Let's construct the path logic:
    # 0,0 is bottom center.
    # Outer Radius at bottom: outer_diameter/2
    # Inner Radius at bottom: base_inner_diameter/2
    
    # Let's define key Y heights:
    # H_floor = 0
    # H_floor_inner = 0 (Floor is solid thickness? "lower end remains closed by a solid floor of that thickness" -> thickness is wall_thickness? 
    # Wait, "lower end remains closed by a solid floor of that thickness". Usually floor thickness = wall_thickness unless specified. 
    # Let's assume Floor Thickness = wall_thickness.
    # So Floor Inner Face is at Y = wall_thickness.
    # Floor Outer Face is at Y = wall_thickness. (Wait, floor is solid).
    # Let's re-read: "lower end remains closed by a solid floor of that thickness". 
    # So the material exists from Y=0 to Y=wall_thickness.
    # The inner bore starts at Y=wall_thickness.
    
    # Let's define the outer profile trace:
    # Start at bottom inner radius (0, -base_inner_diameter/2).
    # Go up to H_floor.
    # Transition Arc: From angle -90 to -2.5? The prompt says "body_transition_arc_start_angle = -90.0". 
    # If we start at -90 (negative Y axis), go up?
    # Let's assume standard polar coords: 0 is +X, 90 is +Y.
    # Bottom of cylinder is usually -90.
    # So Outer Profile:
    # 1. Point A: (outer_diameter/2, -base_cap_overall_height) -> Wait, height is 420. 
    # Let's set origin at the center of the bottom floor.
    # Outer Bottom: (outer_diameter/2, 0).
    # Inner Bottom: (base_inner_diameter/2, 0).
    # Floor Thickness: wall_thickness.
    # So Inner Floor Face starts at Y=wall_thickness.
    
    # Let's build the sketch on XY plane (Z=0). The object will be revolved around Z axis (which is usually the vertical axis in FreeCAD sketch context if attached to XY plane? 
    # No, if attached to XY plane, the sketch is in XZ or YZ? 
    # Standard FreeCAD: Sketch on XY plane -> Geometry in X and Y. Axis of revolution must be Z.
    # So let's use X for Radius, Y for Height.
    
    # Origin: (0,0) = Center of bottom floor.
    # X = Radius, Y = Height.
    
    # Outer Path:
    # Start: (outer_diameter/2, wall_thickness)  (Top of floor)
    # Go up to: (outer_diameter/2, top_transition_start_y)? 
    # Prompt: "body_transition_arc_start_angle = -90.0".
    # If we are building a profile, angles usually define the arc orientation.
    # Let's assume the wall goes straight up from the floor, then curves.
    # Where does the curve start? 
    # "two outer-wall segments meeting at outer_diameter". This implies a tapered section.
    # "tapered body ... with two outer-wall segments".
    # Segment 1: Floor to Transition Start.
    # Segment 2: Transition End to Top.
    # "body_transition_arc_start_angle = -90.0". This likely defines the start of the fillet relative to the vertical? Or absolute?
    # Let's assume absolute angles in the profile sketch (X=Radius, Y=Height).
    # Angle 0 = +X (Horizontal). Angle 90 = +Y (Vertical). Angle -90 = -Y (Down).
    # Start at -90? That would be the bottom.
    # So:
    # 1. Start at (outer_diameter/2, wall_thickness).
    # 2. Go up to a point where the arc begins.
    # 3. Arc from angle -90 (relative to what?) to -2.5.
    # Let's interpret: The wall is vertical (-90 deg from vertical? No, vertical is 90).
    # Let's assume the angles are absolute in the sketch coordinate system (0=East, 90=North).
    # Start of arc: -90 degrees? That is South.
    # End of arc: -2.5 degrees.
    # This suggests an arc starting near the bottom and going almost to horizontal.
    # But the cap is 420mm tall.
    # Alternative: The "base_cap_overall_height" is the total height.
    # Maybe the transition is near the top?
    # Let's try: 
    # Bottom segment: Vertical wall.
    # Middle segment: Tapered.
    # Top segment: Vertical?
    # The prompt says "two outer-wall segments meeting at outer_diameter".
    # Maybe: Bottom Vertical, then Tapered to the very top (outer_diameter).
    # And the arc is the fillet between the vertical wall and the tapered wall.
    # If the vertical wall is at X = constant.
    # The tapered wall meets at X = outer_diameter/2 at the top?
    # "meeting at outer_diameter" -> The final diameter is outer_diameter.
    
    # Let's refine the geometry construction based on typical CAD modeling of such parts:
    # 1. Bottom Floor (Y=0 to Y=wall_thickness).
    # 2. Vertical Wall (Y=wall_thickness to Y=some_h).
    # 3. Fillet (Transition Arc).
    # 4. Tapered Wall (to Top Diameter).
    # 5. Top Lip.
    
    # Given the specific angles:
    # body_transition_arc_start_angle = -90.0
    # body_transition_arc_end_angle = -2.5
    # If we use a Fillet tool in PartDesign, we select two edges.
    # If we use a Sketch with splines/arcs:
    # Let's define the profile points explicitly.
    
    # Let's assume the "Transition Arc" is the fillet between the main wall and the taper.
    # If the arc starts at -90 (vertical up? No, -90 is down. 90 is up).
    # Maybe the coordinates are (Y, X)? (Height, Radius).
    # Let's stick to (X=Radius, Y=Height).
    # Start of arc: (R_start, H_start). End of arc: (R_end, H_end).
    # If the arc starts at -90 deg from the vertical?
    # Let's assume the angles are measured from the positive X-axis (Radius) counter-clockwise.
    # -90 deg is pointing Down (towards floor).
    # -2.5 deg is pointing slightly down.
    # This implies the arc is near the bottom?
    # But we have "body_transition_arc_start_angle" and "top_transition_arc_start_angle".
    # This suggests two transitions.
    # Transition 1 (Body): -90 to -2.5.
    # Transition 2 (Top): 2.5 to 90.
    # This looks like an arc that goes from "Vertical Down" to "Vertical Up"?
    # -90 (Down) -> -2.5 (Almost Horizontal Right) -> 2.5 -> 90 (Up).
    # This describes a continuous curve from the bottom of the main wall, through a flat-ish section, to the top?
    # Or maybe it describes the angle of the tangent?
    # Let's assume the profile consists of:
    # 1. Vertical Line (Bottom Wall).
    # 2. Arc 1 (Body Transition). Tangent starts vertical (-90), ends at -2.5.
    # 3. Straight Line (Taper?).
    # 4. Arc 2 (Top Transition). Tangent starts 2.5, ends 90 (Vertical Up).
    # 5. Vertical Line (Top Lip?).
    
    # Let's calculate coordinates for the Body Transition Arc:
    # Radius = body_transition_arc_radius (45).
    # Start Angle = -90 deg. End Angle = -2.5 deg.
    # Center of arc?
    # If it connects to a vertical line (tangent -90), the center is to the Right (positive X).
    # If it connects to a line at -2.5 deg, the center is...
    # Let's try to construct the points.
    # Point A (Start of Arc): Tangent is vertical (parallel to Y axis). 
    # If the arc curves inward or outward? "tapered body". Usually tapers inward at top.
    # So the arc must connect a larger radius (bottom) to a smaller radius (top)? 
    # Or connect vertical wall to tapered wall.
    # If the wall is vertical, Radius is constant.
    # Then it tapers.
    # So the arc connects Vertical Wall to Tapered Wall.
    # Start Angle -90 (Vertical). End Angle -2.5 (Slightly Down).
    # This implies the arc curves "outward" or "inward"?
    # If tangent goes from Vertical to Down-Right, the curve is convex (bulging out).
    # If tangent goes from Vertical to Down-Left...
    # Let's assume the arc is on the side of the profile (X > 0).
    # Tangent -90 is pointing Down. Tangent -2.5 is pointing Right-Down.
    # To go from Down to Right-Down, you turn Left (Counter-Clockwise).
    # So the arc bulges to the Right (Outward).
    # This matches a "flare" or "base" widening?
    # But we are at the bottom?
    
    # Let's reconsider the "two outer-wall segments meeting at outer_diameter".
    # Maybe the "Base Inner Diameter" is the minimum, and "Outer Diameter" is the max.
    # And the transitions smooth the corners.
    
    # Let's try a different interpretation:
    # The angles define the orientation of the wall segments relative to the vertical axis?
    # No, "start_angle" usually implies absolute.
    
    # Let's try to construct the profile points using the angles as tangent directions.
    # Arc 1 (Body): Radius 45. Start Tangent: -90 (Down). End Tangent: -2.5 (Right-Down).
    # This arc creates a smooth transition from a vertical line to a line going down-right.
    # This seems to be at the bottom?
    # But we have "top_transition".
    # Let's assume the profile goes from Bottom to Top.
    # 1. Start at Bottom Inner Radius (base_inner_diameter/2).
    # 2. Go Up.
    # 3. Arc 1 (Body Transition).
    # 4. Go Up (Tapered?).
    # 5. Arc 2 (Top Transition).
    # 6. Go Up (Lip).
    
    # Wait, the prompt says "two outer-wall segments meeting at outer_diameter".
    # This implies the final shape has a diameter of outer_diameter.
    # And the transitions are "body" and "top".
    # Maybe the "Body" transition is at the bottom (connecting floor to wall)?
    # And "Top" transition is at the top (connecting wall to lip)?
    # If so:
    # Body Transition: Connects Floor (Vertical?) to Wall.
    # Top Transition: Connects Wall to Lip.
    
    # Let's assume the "Body" transition is at the bottom, smoothing the floor-to-wall corner.
    # Floor is at Y=0. Wall starts at Y=wall_thickness.
    # If the floor is flat, and wall is vertical, the corner is sharp.
    # Transition Arc Radius 45.
    # If the arc connects the horizontal floor face to the vertical wall face.
    # Tangent at start (floor face) = 0 (Horizontal). Tangent at end (wall face) = 90 (Vertical).
    # But the prompt says -90 to -2.5.
    # This doesn't match 0 to 90.
    
    # Let's try: The angles are relative to the vertical axis?
    # -90 deg from vertical = Horizontal.
    # -2.5 deg from vertical = Almost Vertical.
    # This fits! 
    # So: Start Angle = -90 (Horizontal). End Angle = -2.5 (Vertical-ish).
    # This arc connects the Horizontal Floor to the Vertical Wall.
    # And the Top Transition:
    # Start = 2.5 (Almost Vertical). End = 90 (Horizontal? 90 from vertical = Horizontal).
    # Wait, if 0 is Vertical Up.
    # Then 90 is Horizontal Right.
    # So Top Transition connects Vertical Wall to Horizontal Lip?
    # "stepped top lip".
    # So the lip steps inward.
    # So the top transition connects the main wall to the inner lip.
    # This makes sense.
    
    # Revised Geometry Plan:
    # Coordinate System: Origin at Center of Bottom Floor.
    # X = Radius, Y = Height.
    # Angles measured from Vertical Up (Y+), Counter-Clockwise? 
    # Or Clockwise? 
    # Let's assume standard math: 0 = X+, 90 = Y+.
    # If angles are from Vertical:
    # Let's assume the prompt angles are from the Vertical Up axis, Clockwise?
    # Body Transition: Start -90 (Down? or Left?), End -2.5.
    # This is getting ambiguous.
    
    # Let's try the most logical CAD interpretation for a "Bayonet Cap":
    # 1. Bottom: Floor (Solid).
    # 2. Wall: Vertical.
    # 3. Top: Flared/Lip.
    # The "Body Transition" is likely the fil
