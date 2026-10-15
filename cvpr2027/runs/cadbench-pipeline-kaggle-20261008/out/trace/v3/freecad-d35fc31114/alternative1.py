import FreeCAD as App
import Part
from Part import Shape, Face, Edge, Wire, Vertex, Vector
import Sketcher
from math import degrees, radians, pi

def createDocument():
    doc = App.newDocument("PivotBracket")
    doc.Name = "PivotBracket"
    
    # 1. Create Reference Planes and Axes
    # XY_Plane (z=0), XZ_Plane (y=0), YZ_Plane (x=0)
    doc.addObject("PartDesign::Plane", "XY_Plane")
    doc.addObject("PartDesign::Plane", "XZ_Plane")
    doc.addObject("PartDesign::Plane", "YZ_Plane")
    
    # Axes (needed for some features, though Planes often suffice)
    doc.addObject("Part::Axis", "X_Axis")
    doc.addObject("Part::Axis", "Y_Axis")
    doc.addObject("Part::Axis", "Z_Axis")
    
    # 2. Create Parameters
    params = doc.addObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "channel_length", "Dimensions", "Length of the channel")
    params.channel_length = 55.1
    
    params.addProperty("App::PropertyLength", "opposite_channel_end", "Dimensions", "Z position of the back end")
    params.opposite_channel_end = -23.1
    
    params.addProperty("App::PropertyLength", "clear_width", "Dimensions", "Clear distance between rails")
    params.clear_width = 42.0
    
    params.addProperty("App::PropertyLength", "flange_depth", "Dimensions", "Depth of flanges")
    params.flange_depth = 10.0
    
    params.addProperty("App::PropertyLength", "web_thickness", "Dimensions", "Thickness of the web")
    params.web_thickness = 6.0
    
    params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of flange face")
    params.flange_thickness = 4.0
    
    params.addProperty("App::PropertyLength", "taper_angle_deg", "Dimensions", "Sidewall taper angle in degrees")
    params.taper_angle_deg = 45.0
    
    params.addProperty("App::PropertyLength", "jaw_thickness", "Dimensions", "Thickness of the transverse jaw")
    params.jaw_thickness = 8.9
    
    params.addProperty("App::PropertyLength", "jaw_outer_edge_len", "Dimensions", "Length of outer jaw arm edge")
    params.jaw_outer_edge_len = 40.0
    
    params.addProperty("App::PropertyLength", "jaw_inner_edge_len", "Dimensions", "Length of inner jaw arm edge")
    params.jaw_inner_edge_len = 34.0
    
    params.addProperty("App::PropertyLength", "small_hole_dia", "Dimensions", "Diameter for small holes")
    params.small_hole_dia = 3.2
    
    params.addProperty("App::PropertyLength", "pivot_hole_dia", "Dimensions", "Diameter for pivot holes")
    params.pivot_hole_dia = 4.2
    
    params.addProperty("App::PropertyLength", "pivot_pattern_radius", "Dimensions", "Radius for pivot pattern")
    params.pivot_pattern_radius = 12.0
    
    params.addProperty("App::PropertyLength", "jaw_open_hole_dist", "Dimensions", "Distance of first jaw hole pair from inner tip")
    params.jaw_open_hole_dist = 8.75
    
    params.addProperty("App::PropertyLength", "jaw_throat_hole_dist", "Dimensions", "Distance of second jaw hole pair from inner tip")
    params.jaw_throat_hole_dist = 25.25
    
    doc.recompute()

    # 3. Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # 4. Main Body Sketch (Longitudinal Channel Profile)
    # We will build this in the YZ plane (at x=0), then extrude along Z (Longitudinal).
    # Actually, the problem says "Longitudinal channel... extend for channel_length".
    # Let's place the sketch in the XZ plane (y=0) and extrude along Y (transverse)? 
    # No, standard convention: Longitudinal is usually Z.
    # Let's define the channel axis along Z.
    # Sketch in XZ plane (y=0). Extrude along Z.
    
    sketch_main = body.newObject("Sketcher::SketchObject", "Sketch_Main")
    sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_main.Placement = App.Placement(App.Rotation(), App.Vector(0, 0, 0)) # Identity
    # Attach to YZ plane (x=0) so the sketch lies on x=0.
    # Wait, if sketch is on YZ plane, we extrude along X.
    # Let's stick to: Sketch in XZ plane (y=0). Extrude along Z.
    # Plane for XZ plane is "XZ_Plane".
    sketch_main.AttachmentSupport = (doc.getObject("XZ_Plane"), [""])
    sketch_main.MapMode = "FlatFace"
    
    # Calculate dimensions
    taper_angle_rad = radians(params.taper_angle_deg.Value)
    half_clear = params.clear_width.Value / 2.0
    half_web = params.web_thickness.Value / 2.0
    
    # Profile in XZ plane:
    # Web is centered at X=0. Width = params.web_thickness.
    # Flanges extend from Web outer face by params.flange_depth.
    # Sidewalls taper from Flange inner face to Web inner face.
    # Wait, description: "web extends inward by channel_web_thickness". 
    # "Each rail projects from the common outer web face by channel_flange_depth".
    # "Clear width is distance between inner faces".
    # "Sidewall taper joins that face [inner face of rail] to the web inner face".
    
    # Geometry Construction:
    # Web: Rectangle from x = -web/2 to +web/2, z = 0 to length.
    # Flanges: Project OUTWARD from Web outer faces? 
    # "Projects from the common outer web face". Usually C-channel flanges are on the outside of the web.
    # So Web is in the middle. Flanges stick out.
    # Let's assume the "common outer web face" is the face where the flanges are attached.
    # So Web is central. Flanges are on the sides.
    # Inner faces of rails define the clear width.
    # Web inner face is the surface facing the clear width.
    # So: Web is in the center. Flanges are on the OUTSIDE of the web.
    # Inner face of rail = Inner face of web + Flange thickness? No.
    # "Clear width is the clear distance between the inner faces of those rails".
    # Rails = Flange + Web? Or Flange + Web + Taper?
    # "Each rail projects... by flange_depth".
    # "Web extends inward by web_thickness".
    # This implies the Rail is composed of Flange + Web.
    # But there is a taper. "Sidewall taper joins that face [inner face of rail] to the web inner face".
    # This implies the Flange is rectangular, and then there is a tapered section connecting the Flange inner edge to the Web inner edge.
    # Wait, if the Flange projects from the Web, the Flange is attached to the Web.
    # If the Web is in the center, the Flanges are on the outside.
    # The "inner face of the rail" is the face facing the center.
    # The taper connects this face to the "web inner face".
    # This implies the Flange has an inner face, and the Web has an inner face.
    # And they are connected by a tapered surface.
    # So the profile looks like a C, but the sides of the C are tapered towards the center.
    
    # Let's coordinate this:
    # Z axis is the longitudinal axis.
    # Profile is in XZ plane.
    # Web is centered at X=0.
    # Flanges are on the outside (negative X and positive X).
    # Let's say Web is from X = -w/2 to X = +w/2.
    # Flanges are attached to X = -w/2 and X = +w/2.
    # Flange depth = distance from Web outer face to Flange outer face? 
    # "Projects from the common outer web face by channel_flange_depth".
    # So Flange Outer Face is at X = -w/2 - depth and X = +w/2 + depth.
    # Flange Thickness = thickness of the flange face? 
    # "channel_flange_thickness". This is likely the thickness of the material in the X-direction? 
    # No, usually flange thickness is the thickness of the web part? 
    # "Each rail projects ... by flange_depth and has channel_flange_thickness".
    # This suggests the Flange is a block of size: Depth x Thickness x Length.
    # But then the taper connects the "inner face of the rail" to the "web inner face".
    # If the Flange is a block, its inner face is at X = -w/2 (if attached to left side) or X = +w/2.
    # But the taper connects "that face" to "web inner face".
    # If the Flange is on the outside, its inner face is the face adjacent to the Web.
    # The Web inner face is the face adjacent to the clear space.
    # So the taper is between the Flange inner face and the Web inner face?
    # That would mean the Flange and Web are separated by the taper.
    # This creates a gap.
    # Let's re-read carefully: "Each rail projects from the common outer web face by channel_flange_depth".
    # "channel_clear_width is the clear distance between the inner faces of those rails".
    # "channel_sidewall_taper_angle is the acute angle between each symmetric sidewall taper and the adjacent straight rail inside face; each taper joins that face to the web inner face."
    
    # Interpretation:
    # Rail = Flange + Taper + Web?
    # Or Rail = Flange + Web?
    # "joins that face [adjacent straight rail inside face] to the web inner face".
    # So there is a Straight Rail Inside Face (part of the Flange).
    # And there is a Web Inner Face (part of the Web).
    # The Taper joins them.
    # So the Flange is a straight block. The Web is a straight block.
    # They are separated by a tapered transition.
    # This means the "Clear Width" is the distance between the inner face of the Flange and the inner face of the Web.
    # Wait, "Clear width is the clear distance between the inner faces of those rails".
    # If the Rail is Flange + Taper + Web, the "inner face of the rail" is the inner face of the Flange.
    # The "web inner face" is the inner face of the Web.
    # So the Clear Width is the distance between the Flange Inner Face and the Web Inner Face.
    # But the Flange is attached to the Web.
    # If they are attached, there is no gap.
    # Unless "projects from" means the Flange is an extension of the Web, and the "inner face" is the top/bottom?
    # No, "sidewall taper".
    
    # Alternative Interpretation (Standard C-Channel with Tapered Web):
    # The "Rail" is the whole side.
    # The "Straight Rail Inside Face" is the vertical face of the Flange facing the center.
    # The "Web Inner Face" is the vertical face of the Web facing the center.
    # The Taper connects them.
    # This implies the Flange and Web are NOT directly connected. There is a tapered section.
    # But "joined flush at one end" refers to the Jaw.
    # "Longitudinal channel... extend for channel_length".
    # So the channel is a single continuous piece.
    # It has a Web, and two Flanges.
    # The Flanges are attached to the Web.
    # The "inner face of the rail" is the face of the Flange facing the center.
    # The "web inner face" is the face of the Web facing the center.
    # If the Flange is attached to the Web, the Flange inner face IS the Web inner face (if the Flange is just a thin plate on the side).
    # But here we have a "flange_depth" and "web_thickness".
    # Maybe the "Rail" is the Flange.
    # "Each rail projects from the common outer web face".
    # So Web is central. Flanges are on the outside.
    # Flange depth = distance from Web outer face to Flange outer face.
    # Flange thickness = thickness of the Flange material in the direction of the taper?
    # No, "channel_flange_thickness" is likely the thickness of the flange face (the face parallel to the taper).
    # Let's assume:
    # Web: Rectangle centered at X=0. Width = web_thickness. Height (Z) = length.
    # Flanges: Rectangles attached to the outside of the Web.
    # Flange Depth: Distance from Web outer face to Flange outer face.
    # Flange Thickness: Thickness of the Flange in the X-direction? No, that would be the width.
    # Maybe Flange Thickness is the thickness of the flange face (the face perpendicular to the Web plane)?
    # No, the sketch is a 2D profile.
    # Let's assume the profile is:
    # Central Web: X from -w/2 to +w/2.
    # Flanges: Attached to X = -w/2 and X = +w/2.
    # Flange extends from X = -w/2 to X = -w/2 - depth.
    # Flange extends from X = +w/2 to X = +w/2 + depth.
    # The "Straight Rail Inside Face" is the face at X = -w/2 (left flange) and X = +w/2 (right flange).
    # The "Web Inner Face" is the face at X = -w/2 (left web) and X = +w/2 (right web).
    # They are the same face if attached directly.
    # But there is a "taper" joining "that face" to "web inner face".
    # This implies the "Straight Rail Inside Face" is NOT the face at X = -w/2.
    # Maybe the Flange has a thickness in the X-direction?
    # "channel_flange_thickness".
    # If the Flange has a thickness, then it extends from X = -w/2 - depth to X = -w/2.
    # And the "Straight Rail Inside Face" is the face at X = -w/2 - depth? No, that's the outer face.
    # The "inside face" is the one facing the center.
    # If the Flange is a block from X = -w/2 - depth to X = -w/2, the inside face is at X = -w/2.
    # The Web is from X = -w/2 to X = w/2. The inside face is at X = -w/2.
    # They are the same.
    # So the taper must be between the Flange face and the Web face.
    # This implies the Flange and Web are separated by the taper.
    # So the Flange is from X = -w/2 - depth to X = -w/2 - taper_start.
    # The Web is from X = -w/2 + taper_end to X = w/2.
    # The Taper is from X = -w/2 - taper_start to X = -w/2 + taper_end.
    # But the problem says "joins that face [straight rail inside face] to the web inner face".
    # This implies the Straight Rail Inside Face is the face of the Flange, and the Web Inner Face is the face of the Web.
    # And they are connected by the taper.
    # So the Clear Width is the distance between the Straight Rail Inside Face and the Web Inner Face.
    # Wait, "Clear width is the clear distance between the inner faces of those rails".
    # If the Rail is Flange + Taper + Web, the "inner face of the rail" is the inner face of the Flange.
    # So Clear Width = Distance between Left Flange Inner Face and Right Flange Inner Face.
    # The Web is inside this clear width.
    # The Taper connects the Flange Inner Face to the Web Inner Face.
    # This implies the Flange is further out than the Web.
    # So the profile is:
    # Flange (Straight) -> Taper -> Web (Straight).
    # Flange Inner Face is at X = -w/2 - depth. (Assuming Flange is on the outside).
    # Web Inner Face is at X = -w/2 + taper_width/2?
    # No, the Web is centered.
    # Let's assume the Flange is on the outside.
    # Flange Outer Face: X = -w/2 - depth.
    # Flange Inner Face: X = -w/2. (This is the face of the Flange adjacent to the taper).
    # Web Inner Face: X = -w/2. (This is the face of the Web adjacent to the taper).
    # If they are the same, no taper needed.
    # Unless "channel_flange_thickness" is the thickness of the Flange in the direction of the taper?
    # No, "projects by flange_depth".
    # Maybe the "Straight Rail Inside Face" is the face of the Flange facing the center, but the Flange is THICKER than the Web.
    # No, "projects from the
