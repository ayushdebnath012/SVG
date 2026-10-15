import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

def create_document_and_save(filename, doc):
    """Helper to save the current document to a specific filename."""
    doc.recompute()
    path = Path(filename)
    doc.saveAs(str(path))
    return str(path)

def build_base_part():
    """
    Builds the base 'routing clamp' part.
    Returns the document object.
    """
    doc = App.newDocument("RoutingClamp_Base")
    
    # --- Parameters (Named, Editable) ---
    # We will use a PropertyGroup to store dimensions for easy reference in expressions
    params = doc.addObject("App::PropertyGroupProxy", "Parameters")
    params.Proxy = doc.addObject("App::VarSet", "Dims")
    
    # Base Dimensions
    p = params.Dims
    p.addProperty("App::PropertyLength", "cable_channel_diameter", "Dimensions")
    p.cable_channel_diameter = 4.76
    p.addProperty("App::PropertyLength", "channel_center_spacing", "Dimensions")
    p.channel_center_spacing = 10.16
    p.addProperty("App::PropertyLength", "clamp_overall_profile_width", "Dimensions")
    p.clamp_overall_profile_width = 15.84
    p.addProperty("App::PropertyLength", "clamp_body_height", "Dimensions")
    p.clamp_body_height = 6.9
    p.addProperty("App::PropertyLength", "clamp_length", "Dimensions")
    p.clamp_length = 17.78
    p.addProperty("App::PropertyLength", "center_bridge_width", "Dimensions")
    p.center_bridge_width = 6.98
    p.addProperty("App::PropertyLength", "bridge_top_width", "Dimensions")
    p.bridge_top_width = 5.76
    p.addProperty("App::PropertyLength", "snap_ring_outer_radius", "Dimensions")
    p.snap_ring_outer_radius = 2.84
    p.addProperty("App::PropertyLength", "snap_opening_angle", "Dimensions")
    p.snap_opening_angle = 112.1598742
    p.addProperty("App::PropertyLength", "channel_arc_radius", "Dimensions")
    p.channel_arc_radius = 6.64
    p.addProperty("App::PropertyLength", "channel_arc_span", "Dimensions")
    p.channel_arc_span = 19.509833
    p.addProperty("App::PropertyLength", "channel_arc_center_spacing", "Dimensions")
    p.channel_arc_center_spacing = 11.42
    p.addProperty("App::PropertyLength", "channel_arc_vertical_center_spacing", "Dimensions")
    p.channel_arc_vertical_center_spacing = 7.18
    p.addProperty("App::PropertyLength", "channel_outer_height", "Dimensions")
    p.channel_outer_height = 6.1
    p.addProperty("App::PropertyLength", "channel_inner_height", "Dimensions")
    p.channel_inner_height = 5.34
    p.addProperty("App::PropertyLength", "channel_relief_depth", "Dimensions")
    p.channel_relief_depth = 12.74
    p.addProperty("App::PropertyLength", "side_recess_width", "Dimensions")
    p.side_recess_width = 3.81
    p.addProperty("App::PropertyLength", "side_recess_axial_length", "Dimensions")
    p.side_recess_axial_length = 5.05
    p.addProperty("App::PropertyLength", "side_recess_depth", "Dimensions")
    p.side_recess_depth = 5.21
    p.addProperty("App::PropertyLength", "side_recess_axial_center_offset", "Dimensions")
    p.side_recess_axial_center_offset = 4.775

    # --- Body ---
    body = doc.addObject("PartDesign::Body", "Body")
    doc.setActiveObject("Body")

    # --- Reference Planes ---
    # XY: Front face (Width x Height), Z is length axis
    # XZ: Top/Bottom face (Length x Width), Y is height axis
    # YZ: Side face (Length x Depth?), X is width axis
    # Standard FreeCAD planes: XY, XZ, YZ
    # We will place sketches on these standard planes within the Body context.
    
    # --- 1. Main Profile Sketch (XY Plane, Z-axis extrusion) ---
    # This defines the cross-section of the clamp.
    sketch_profile = body.newObject("Sketcher::SketchObject", "Sketch_Profile")
    sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0)) # Center of length
    sketch_profile.Placement = sketch_profile.Placement * App.Rotation(0, 0, 0) # Ensure orientation
    # Actually, better to attach to a plane. Let's use the global XY plane (Z is up) but rotate so Z becomes Length.
    # FreeCAD Default: XY plane, Z up. We want Z to be the Length axis.
    # So we sketch on XY plane, extrude along Z.
    sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Geometry Construction Strategy:
    # Symmetric about Y=0 (Width midplane) and X=0 (Bridge midplane).
    # Width spans from -W/2 to W/2.
    # Height spans from -H/2 to H/2.
    # Length spans from -L/2 to L/2.
    
    w_total = p.clamp_overall_profile_width
    h_total = p.clamp_body_height
    l_total = p.clamp_length
    w_bridge = p.center_bridge_width
    w_top = p.bridge_top_width
    
    # Coordinates
    half_w = w_total / 2
    half_h = h_total / 2
    half_l = l_total / 2
    half_bridge = w_bridge / 2
    half_top = w_top / 2
    
    # Points for the profile (X=Length, Y=Width, Z=Height is implicit as 0 in sketch)
    # We define points in the sketch plane (X, Y).
    
    # Outer Corners
    p1 = App.Vector(-half_l, -half_w)
    p2 = App.Vector(half_l, -half_w)
    p3 = App.Vector(half_l, half_w)
    p4 = App.Vector(-half_l, half_w)
    
    # Bottom Bridge (Center)
    # The bridge connects the lower channel to the upper channel? 
    # "joined by a central bridge"
    # "Straight inner links and equal-run-and-rise ramps join the finger ends to the narrower upper and lower bridge."
    # Let's interpret:
    # Lower channel (Y < 0). Upper channel (Y > 0).
    # Bridge is in the middle? Or is the "bridge" the connection between the two channels?
    # "center_bridge_width" and "bridge_top_width". 
    # Usually a clamp has a central spine.
    # Let's assume the "bridge" is the central spine connecting the two channels.
    # The profile is symmetric.
    # Let's define the "Bridge" as the central part.
    
    # Let's trace the perimeter from bottom-left (-half_l, -half_w) -> bottom-right -> top-right -> top-left -> back.
    
    # 1. Bottom Edge (Left to Right)
    # Actually, let's look at the "channels".
    # "two side-by-side cable channels".
    # This implies the profile has a gap in the middle?
    # "joined by a central bridge".
    # Okay, so there are two holes (circles) in the main body.
    # Between them is a bridge.
    # The bridge has a width.
    # The top width of the bridge is narrower.
    
    # Let's re-read carefully: "straight inner links and equal-run-and-rise ramps join the finger ends to the narrower upper and lower bridge."
    # This suggests the "Bridge" is a specific feature, possibly a raised part or a specific width zone.
    # Given "center_bridge_width" = 6.98 and "clamp_overall_profile_width" = 15.84.
    # If there are two channels, the bridge is likely the material between them?
    # Or is the bridge the top cap?
    # "narrower upper and lower bridge" -> This phrasing is tricky. "Upper and Lower Bridge" might refer to the top and bottom of the central spine.
    # Let's assume the profile is:
    # Outer bounds: Width 15.84, Height 6.9.
    # Two circular channels in the middle (Width-wise).
    # A central bridge connecting them.
    # "narrower upper and lower bridge" might mean the bridge tapers?
    # Or maybe "bridge" refers to the top and bottom horizontal segments of the central spine?
    
    # Let's try a standard interpretation:
    # The profile is a solid block with two holes.
    # The "Bridge" is the material between the holes.
    # "center_bridge_width" = 6.98 (Distance between hole centers? Or width of the bridge itself?)
    # If channel spacing is 10.16, and bridge width is 6.98...
    # If the bridge is the material, and channels are circles...
    # Let's assume the "Bridge" is the central rectangular prism connecting the two channels.
    # Its width (along X in profile) is 6.98? No, that's wider than half the channel spacing (5.08).
    # Wait, channel_center_spacing = 10.16.
    # If bridge width is 6.98, it fits between them.
    # "bridge_top_width" = 5.76. This implies the bridge narrows towards the top?
    # "equal-run-and-rise ramps join the finger ends to the narrower upper and lower bridge."
    # This suggests the bridge has a shape like a trapezoid or a stepped cylinder?
    # "Upper and Lower Bridge" -> Maybe the bridge is split?
    # "Two equal blind rectangular recesses enter from the lower broad face... centered across the width".
    # This is complex.
    
    # Let's simplify based on "Snap-in routing clamp".
    # Common shape: Two parallel slots.
    # The "Bridge" is the wall between them.
    # "narrower upper and lower bridge" -> The wall might be tapered?
    # "Straight inner links" -> The bottom of the channel.
    # "ramps" -> The side of the channel.
    
    # Let's construct the profile points manually to match the description.
    # Symmetry about Y=0.
    # We need to define the outer contour and the inner holes.
    
    # Outer Contour:
    # Bottom: (-half_l, -half_w) to (half_l, -half_w) ? 
    # "Two equal blind rectangular recesses enter from the lower broad face".
    # So the bottom face is not flat everywhere.
    
    # Let's assume the "Lower Broad Face" is the bottom of the part.
    # Recesses are holes/cuts.
    # "centered across the width".
    
    # Let's build the profile step-by-step.
    # We'll define the outer shell first, then subtract the channels and recesses.
    
    # Points (X, Y) in XY plane. Z is extrusion axis.
    # X: Length, Y: Width.
    
    # Outer Rectangle
    # Bottom-Left: (-half_l, -half_w)
    # Bottom-Right: (half_l, -half_w)
    # Top-Right: (half_l, half_w)
    # Top-Left: (-half_l, half_w)
    
    # Add Blind Recesses (Subtractive)
    # "enter from the lower broad face" -> Cut from Bottom (-half_w) upwards?
    # "centered across the width" -> Y = 0.
    # "placed at equal opposite offsets along the length".
    # Center of part X=0.
    # Offset = side_recess_axial_center_offset = 4.775.
    # Width = side_recess_width = 3.81.
    # Depth = side_recess_depth = 5.21.
    # Length = side_recess_axial_length = 5.05.
    
    # So we have two rectangular cuts on the bottom face (Y = -half_w + depth?).
    # Actually, "enter from the lower broad face" usually means a hole from the bottom.
    # But the profile is the cross section.
    # So the profile must show the outline of these recesses.
    # If they are on the bottom face, they appear as notches in the bottom edge of the profile.
    # Position: X = +/- 4.775.
    # Width: 3.81.
    # Depth: 5.21 (into the part, i.e., +Y direction).
    # So the bottom edge goes:
    # From -half_l to -(4.775 + 1.905) -> Down? No, it's a recess.
    # The profile line goes Up by 5.21 at X = -4.775 - 1.905.
    
    # Let's refine the "Bridge" geometry.
    # "joined by a central bridge"
    # "Straight inner links and equal-run-and-rise ramps join the finger ends to the narrower upper and lower bridge."
    # This sounds like the channel walls are complex.
    # "Finger" = Retaining finger around the cable.
    # "Straight inner links" = Bottom of the channel.
    # "Ramps" = The transition from the finger to the bridge?
    
    # Alternative Interpretation:
    # The "Bridge" is a central protrusion.
    # The "Channels" are the voids around it.
    # The "Finger" is the part of the wall that sticks out to hold the cable.
    # "Snap ring outer radius" -> The finger has a lip.
    
    # Let's try to map the points based on the "Snap Ring" and "Channel" logic.
    # We have a main body.
    # Two holes (circular).
    # Around each hole is a "retaining finger" (a bump).
    # The "bridge" connects the two channels.
    
    # Let's construct the profile using a series of lines and arcs.
    # Since we need a single solid, we will create a sketch with all outer boundaries, 
    # then use a Pad, then subtract the holes/recesses.
    
    # Let's define the profile vertices.
    # We will draw the outer perimeter and the inner cutouts.
    
    # Outer Perimeter (CCW)
    # Start Bottom-Left
    v1 = App.Vector(-half_l, -half_w)
    v2 = App.Vector(-half_l + side_recess_axial_length/2, -half_w + side_recess_depth) # Start of recess?
    # Wait, recesses are at X = +/- 4.775. Width 3.81.
    # Center X = 4.775. Left edge = 2.865. Right edge = 6.685.
    # Bottom edge is flat until the recess.
    
    # Let's restart the profile construction with a clear logic.
    # 1. Outer Box: X in [-8.92, 8.92], Y in [-3.45, 3.45].
    # 2. Bottom Face has two rectangular notches (recesses).
    #    Center X = +/- 4.775. Width = 3.81. Depth = 5.21 (upwards).
    #    So the bottom edge Y = -3.45 is interrupted.
    #    At X = -6.685, go up 5.21. Horizontal. At X = -2.865, go down.
    #    Same for positive X.
    
    # 3. Channels.
    #    "cable_channel_diameter = 4.76".
    #    "channel_center_spacing = 10.16".
    #    "channel_arc_radius = 6.64".
    #    "channel_arc_span = 19.509833".
    #    "channel_outer_height = 6.1".
    #    "channel_inner_height = 5.34".
    #    This implies the channel is not a simple circle. It has an arc segment and straight sides?
    #    "wrapped by an outer retaining finger".
    #    "Straight inner links".
    #    Maybe the channel profile is: Bottom straight, sides straight (or arc?), top arc?
    #    "channel_arc_radius" and "channel_arc_span" suggest an arc at the top.
    #    "channel_outer_height" vs "channel_inner_height" -> The finger has a specific height profile.
    
    #    Let's assume the channel is defined by an arc at the top and straight sides/bottom.
    #    Center of channel: Y = 0? No, "side-by-side".
    #    Centers at Y = +/- (spacing/2) = +/- 5.08.
    #    But wait, "joined by a central bridge".
    #    If the centers are 10.16 apart, the bridge is between them.
    #    Bridge width = 6.98?
    #    If centers are 5.08 from center, and bridge width is 6.98 (radius 3.49 from center), they overlap?
    #    5.08 > 3.49. So they don't overlap. There is a gap of 2*5.08 - 6.98 = 3.18?
    #    Or is the "bridge" the space between them?
    #    "
