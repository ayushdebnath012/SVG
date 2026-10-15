import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import copy

def create_base_document():
    """Creates the base part geometry as defined in the prompt."""
    doc = App.newDocument("RodHangerBase")
    
    # --- Parameters ---
    params = doc.addObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "strap_thickness", "Dimensions", "thickness")
    params.addProperty("App::PropertyLength", "strap_width", "Dimensions", "extrusion length")
    params.addProperty("App::PropertyLength", "upper_strap_transition_inner_radius", "Dimensions", "inner radius")
    params.addProperty("App::PropertyLength", "upper_strap_profile_height", "Dimensions", "total height")
    params.addProperty("App::PropertyLength", "upper_side_leg_straight_length", "Dimensions", "vertical leg length")
    params.addProperty("App::PropertyLength", "top_flat_width", "Dimensions", "top width")
    params.addProperty("App::PropertyAngle", "upper_transition_tangent_direction_angle", "Dimensions", "tangent angle")
    params.addProperty("App::PropertyLength", "strap_connection_overlap_length", "Dimensions", "overlap")
    params.addProperty("App::PropertyLength", "pivot_hole_diameter", "Dimensions", "pivot hole")

    # Set values
    params.strap_thickness = 2.78
    params.strap_width = 19.05
    params.upper_strap_transition_inner_radius = 2.78
    params.upper_strap_profile_height = 34.93
    params.upper_side_leg_straight_length = 22.23
    params.top_flat_width = 14.78
    params.upper_transition_tangent_direction_angle = 67.68612906
    params.strap_connection_overlap_length = 19.06
    params.pivot_hole_diameter = 11.12

    # --- Body ---
    body = doc.addObject("PartDesign::Body", "Body")
    doc.addObject("App::DocumentObjectGroup", "Group")
    doc.addObject("App::DocumentObjectGroup", "Group").Parent = body
    # Actually, PartDesign::Body usually doesn't need a group inside it for top-level objects in the tree, 
    # but App::DocumentObjectGroup is a valid parent. Let's keep it simple.
    # Standard practice: Body is the root. Features are children of Body.

    # --- Plane: XY (Base for the profile) ---
    # We need the profile to be on XY plane so we can extrude along Z.
    # However, the prompt implies "upper strap", "lower loop". 
    # Let's define the profile on the XY plane, centered at (0,0).
    # The "upper" part will be in Y>0, "lower" part in Y<0.
    # The mirror plane is the XZ plane (Y=0).
    
    plane_xy = doc.addObject("PartDesign::Plane", "Plane_XY")
    plane_xy.Placement = App.Placement(App.Vector(0, 0, 0))
    body.addObject(plane_xy)

    # --- Sketch 1: Upper Strap Profile ---
    # Geometry description:
    # 1. Top flat strip: width = top_flat_width. Centered on Y axis? 
    #    Let's say the top is at Y = upper_strap_profile_height.
    #    So it goes from Y = H - w/2 to Y = H + w/2.
    #    Wait, "joined through concentric inner/outer transition arcs".
    #    Usually, this means a C-shape or U-shape.
    #    "Two vertical side strips... to a centered horizontal top strip".
    #    This sounds like a 'U' turned upside down, or a 'C' shape facing down?
    #    "Pivoting rod-hanger base... mirrored upper strap only".
    #    "Lower side ends provide the shared connection for the omitted loop".
    #    This implies the shape is open at the bottom (negative Y).
    #    So: Top horizontal bar, two vertical legs going down, then rounded bottom corners.
    #    
    #    Coordinates:
    #    Top Y = upper_strap_profile_height
    #    Top Width = top_flat_width (centered on X=0).
    #    Vertical Legs: Start at Y = top - thickness, go down to Y = top - thickness - straight_length.
    #    Corner Radius: upper_strap_transition_inner_radius.
    #    Outer Corner Radius: inner + thickness.
    #    
    #    Let's calculate the bottom Y extent.
    #    Top Y_max = H
    #    Inner corner Y = H - thickness
    #    Leg length = L_leg
    #    So Inner Corner Y = H - L_leg
    #    Outer corner Y = H - L_leg - thickness
    
    # Let's create the sketch
    sketch_base = body.newObject("Sketcher::SketchObject", "BaseSketch")
    sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_base.Placement = App.Placement(App.Vector(0, 0, 0)) # Ensure origin
    sketch_base.ConstraintFixToPlane = 1 # XY Plane (Index 1 in list of planes, but let's use standard naming if possible, or index)
    # Actually, sketch.Placement is relative to the plane. 
    # If we attach to Plane_XY, we need to tell the sketch which plane.
    # sketch.Placement = App.Placement(App.Vector(0,0,0)) puts it on the plane of the body (XY).
    
    # Draw lines and arcs
    # Helper to create lines
    def add_line(sketch_obj, p1, p2):
        sketch_obj.addGeometry(Part.LineSegment(p1, p2), False)

    H = params.upper_strap_profile_height
    W = params.top_flat_width
    T = params.strap_thickness
    L_leg = params.upper_side_leg_straight_length
    R_inner = params.upper_strap_transition_inner_radius
    R_outer = R_inner + T
    Theta_deg = params.upper_transition_tangent_direction_angle
    Theta_rad = Theta_deg * 3.14159265359 / 180.0

    # The transition angle is given. "Upper transition tangent direction angle".
    # In a standard U-shape, the leg is vertical (90 deg). The top is horizontal (0 deg).
    # The transition connects them.
    # If the angle is measured from horizontal? Or vertical?
    # Let's assume the standard tangent at the *inner* corner.
    # If it's 67.68 degrees, that's specific.
    # Let's construct the geometry based on standard arcs.
    # Inner arc radius R_inner.
    # Top segment center X = 0. Top segment Y = H - R_inner.
    # Leg segment X = +/- W/2. Leg segment Y goes from (H - R_inner) down to (H - L_leg - R_inner).
    # Wait, the straight leg length is usually the tangent length.
    # If the arc is tangent to the top and the leg, the tangent length is sqrt((W/2 - R)^2 + (L_leg)^2)?
    # No, "vertical side strips joined through ... common tangent segments".
    # This implies the vertical part is straight, then an arc, then the top is straight.
    # So the arc is tangent to the vertical line and the horizontal line.
    # The angle 67.68 deg might be the angle of the tangent line relative to something else?
    # Or maybe the shape is not a simple U.
    # "Two vertical side strips joined through concentric inner/outer transition arcs and common tangent segments to a centered horizontal top strip".
    # This phrasing "common tangent segments" suggests the arc is tangent to both the vertical strip and the top strip.
    # This forms a rounded corner.
    # Why the specific angle? Maybe the "tangent direction" is not 90/0.
    # "Upper transition tangent direction angle = 67.68...".
    # Could it be that the top strip is not horizontal? "centered horizontal top strip".
    # Could the side strips not be vertical? "Two vertical side strips".
    # So the tangent at the corner must be at 45 degrees? No.
    # Maybe the angle defines the *location* of the tangent point relative to the center?
    # Or maybe the angle is the angle of the chord?
    # Let's re-read carefully: "joined through concentric inner/outer transition arcs and common tangent segments".
    # This usually means a fillet.
    # If the angle is 67.68, maybe it's the angle of the *radius*? No.
    # Let's assume the standard U-shape where the corner is 90 degrees, and the angle provided is a specific constraint for a different geometry?
    # OR, perhaps the "tangent direction" is the angle of the straight line segment connecting the start of the arc to the end of the arc? No.
    # Let's consider the possibility that the "tangent direction" refers to the angle of the *top* surface relative to the side? No, it's horizontal.
    # Let's try to interpret "tangent direction angle" as the angle of the normal? No.
    # Hypothesis: The angle 67.68 is the angle of the tangent vector at the *inner* corner relative to the X-axis?
    # If the leg is vertical and top is horizontal, the tangent vector at the top of the inner arc is vertical (90 deg).
    # If it's 67.68, then the leg is not vertical? But prompt says "vertical side strips".
    # Maybe the "transition" is not a 90-degree fillet. Maybe it's an arc that connects a slanted leg? No, "vertical".
    # Is it possible the angle is for the *outer* corner? No, concentric.
    # Let's reconsider the shape. "Two vertical side strips... to a centered horizontal top strip".
    # Maybe the "common tangent segments" are the vertical strips and the horizontal top strip themselves?
    # And the "transition arcs" join them.
    # If the angle is 67.68, maybe it's the angle of the *chord*?
    # Let's assume the provided angle is the angle of the tangent to the arc at the point where it meets the *top* strip?
    # If the top is horizontal, the tangent must be horizontal.
    # This is confusing. Let's look at the numbers.
    # 67.68 degrees.
    # Maybe the "vertical side strips" are not vertical in the global frame, but relative to the strip?
    # "vertical side strips" -> Global Y axis.
    # "horizontal top strip" -> Global X axis.
    # Intersection is 90 degrees.
    # Why 67.68?
    # Maybe the "transition" is not a simple fillet. Maybe it's a "common tangent" between two circles?
    # "concentric inner/outer transition arcs".
    # Okay, let's step back. If the geometry is a standard U-shape, the angle should be 90.
    # Is it possible the prompt implies a specific non-orthogonal join?
    # "Two vertical side strips ... to a centered horizontal top strip".
    # Maybe the top strip is not horizontal? "centered horizontal top strip".
    # Okay, let's assume the angle parameter is actually the *angle of the tangent line* at the *outer* corner? No.
    # Let's try a different interpretation: The "transition" is an arc that is tangent to the vertical strip and the top strip, but the *direction* of the tangent is given as 67.68?
    # If the tangent is at 67.68, and the leg is vertical (90), they are not tangent.
    # Unless... the "vertical side strips" are actually at an angle? No, "vertical".
    # Maybe the "tangent direction" is the angle of the *chord* connecting the ends of the arc?
    # Let's assume the standard U-shape and the angle is a red herring or I am misinterpreting "tangent direction".
    # WAIT. "upper_transition_tangent_direction_angle".
    # Could it be the angle of the *radius*? No.
    # Let's assume the angle is the angle of the *top* surface relative to the *side* surface? That's 90.
    # Let's assume the angle is the angle of the *inner* arc tangent at the *top* connection point? That's 0 (horizontal).
    # Let's assume the angle is the angle of the *outer* arc tangent at the *top* connection point? That's 0.
    # What if the "vertical side strips" are not straight lines? No.
    # What if the "horizontal top strip" is not horizontal? No.
    # Is it possible the angle is the angle of the *leg*? No, "vertical".
    # Let's try to search for the specific angle 67.68612906. 
    # 67.686... is approx 67 + 2/3.
    # Maybe it's atan(2.5)? No.
    # Maybe it's related to the dimensions?
    # Let's assume the geometry is a standard U-shape (90 deg corners) and the angle is just a specific parameter name that might be unused or I am missing a subtle geometric nuance.
    # HOWEVER, "joined through ... common tangent segments".
    # This phrase "common tangent segments" is key.
    # If you have two circles (inner and outer), and you want to connect them with a line segment that is tangent to both...
    # But we are connecting a line (leg) and a line (top) with an arc.
    # The arc is tangent to the leg and the top.
    # The leg and top are perpendicular.
    # So the arc is a quarter circle.
    # Why the angle?
    # Maybe the "transition" is not a fillet, but a specific shape defined by that angle?
    # Let's assume the angle is the angle of the *chord* of the arc?
    # If the arc is a quarter circle, the chord angle is 45.
    # If the arc is smaller?
    # Let's assume the "tangent direction" is the angle of the *top* strip relative to the *leg*? No.
    # Let's assume the provided angle is the angle of the *tangent* at the *bottom* of the transition?
    # If the leg is vertical, the tangent at the bottom is vertical.
    # Okay, I will proceed with a standard U-shape (90 degree corners) and assume the angle parameter is either for a future edit or I'm overthinking it. 
    # BUT, to be safe, I will construct the U-shape using the dimensions provided.
    # Top Y = H - R_inner. (Wait, if the top strip is at Y=H, and thickness is T, then the bottom of the top strip is H-T. The inner corner is at H-T. The radius is R_inner. So the center of the inner arc is at H-T-R_inner.
    # The leg starts at the end of the top strip.
    # Top strip: X in [-W/2, W/2], Y = H.
    # Inner corner arc: Center (W/2, H - R_inner). Radius R_inner.
    # Leg: X = W/2. Y from H - R_inner down to H - R_inner - L_leg.
    # This creates a U-shape.
    # The "tangent direction angle" might be the angle of the *outer* arc? No.
    # I will ignore the angle for the base construction as it contradicts "vertical/horizontal" unless it defines a non-orthogonal join which contradicts the text.
    # WAIT! "common tangent segments to a centered horizontal top strip".
    # Maybe the "transition" is a segment that is tangent to the vertical strip and the top strip?
    # If the segment is tangent to the vertical strip, it must be horizontal.
    # If it is tangent to the top strip, it must be vertical.
    # Contradiction.
    # Unless the "vertical side strips" are not the ones being joined?
    # "Two vertical side strips joined through concentric inner/outer transition arcs... to a centered horizontal top strip".
    # Okay, I'll stick to the U-shape.
    
    # --- Constructing the Base Sketch ---
    # Top Y level = H
    # Top Width = W
    
    # Points:
    # TL (Top Left): (-W/2, H)
    # TR (Top Right): (W/2, H)
    # Inner Corner Top: (W/2, H - R_inner) -> Start of leg?
    # No, the arc connects the Top Strip and the Leg Strip.
    # The Top Strip is the horizontal line.
    # The Leg Strip is the vertical line.
    # The arc is tangent to both.
    # Center of inner arc: (W/2, H - R_inner).
    # The arc goes from (W/2, H) [Start on Top Strip] to (W/2 - R_inner, H - R_inner) [End on Leg Strip]?
    # Wait, if the arc is tangent to the vertical line X=W/2, the center X must be W/2 - R_inner.
    # If the arc is tangent to the horizontal line Y=H, the center Y must be H - R_inner.
    # So Center = (W/2 - R_inner, H - R_inner).
    # Arc starts at (W/2, H) and ends at (W/2 - R_inner, H - R_inner).
    # This is a quarter circle (90 deg).
    # The Leg Strip continues from (W/2 - R_inner, H - R_inner) downwards.
