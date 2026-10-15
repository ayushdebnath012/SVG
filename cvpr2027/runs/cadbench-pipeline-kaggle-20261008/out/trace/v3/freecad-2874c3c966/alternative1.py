import FreeCAD as App
import Part
import Sketcher
import math
from pathlib import Path

# ==============================================================================
# 1. CONFIGURATION & PARAMETERS
# ==============================================================================

# Base Parameters
BASE_PARAMS = {
    "pin_body_diameter": 13.94,
    "outer_diameter": 18.9,
    "snap_feature_diameter": 15.9,
    "undercut_diameter": 6.0,
    "front_section_length": 3.1,
    "front_snap_taper_length": 1.56,
    "first_snap_ridge_axial_length": 4.47,
    "second_snap_ridge_start_position": 8.5,
    "second_snap_ridge_end_position": 12.05,
    "main_shaft_section_start": 15.1,
    "snap_groove_width": 1.5,
    "snap_groove_apex_position": 16.6,
    "rear_shaft_section_start": 18.1,
    "rear_taper_start_position": 29.62,
    "connector_end_position": 40.1,
    "total_connector_length": 43.2,
    "undercut_depth_position": 3.0,
    "conical_bore_length": 9.0,
    "conical_bore_large_end_diameter": 13.94,
    "conical_bore_small_end_diameter": 6.0,
    "front_snap_taper_return_position": 4.03,
}

# Edit Parameters (applied to the target part)
EDIT_PARAMS = {
    "axial_slot_width": 2.0,
    "axial_slot_length": 9.89,
    "axial_slot_axial_length": 23.2,
    "number_of_axial_slot_features": 6,
    "axial_slot_total_sweep_angle": 60.0,
    "snap_tab_width": 3.2,
    "snap_tab_top_arc_radius": 9.45,
    "snap_tab_top_arc_central_angle": 19.495659,
    "snap_tab_axial_length": 14.0,
    "snap_tab_axial_offset": 15.1,
    "number_of_snap_tab_features": 4,
    "snap_tab_total_sweep_angle": 90.0,
    "conical_cutout_large_diameter": 13.94,
    "conical_cutout_small_diameter": 5.08,
    "conical_cutout_axial_length": 8.5,
}

# Helper to access document parameters
def get_param(doc, name, default=None):
    obj = doc.getObject(name)
    if obj and obj.exists():
        return obj[name]
    return default

# ==============================================================================
# 2. BUILD BASE PART
# ==============================================================================

def build_base_part():
    doc = App.newDocument("PartDesign_Base")
    doc.Name = "BasePart"
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Parameters Object
    params = body.newObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "pin_body_diameter", "Dimensions")
    params.pin_body_diameter = BASE_PARAMS["pin_body_diameter"]
    params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions")
    params.outer_diameter = BASE_PARAMS["outer_diameter"]
    params.addProperty("App::PropertyLength", "snap_feature_diameter", "Dimensions")
    params.snap_feature_diameter = BASE_PARAMS["snap_feature_diameter"]
    params.addProperty("App::PropertyLength", "undercut_diameter", "Dimensions")
    params.undercut_diameter = BASE_PARAMS["undercut_diameter"]
    params.addProperty("App::PropertyLength", "front_section_length", "Dimensions")
    params.front_section_length = BASE_PARAMS["front_section_length"]
    params.addProperty("App::PropertyLength", "front_snap_taper_length", "Dimensions")
    params.front_snap_taper_length = BASE_PARAMS["front_snap_taper_length"]
    params.addProperty("App::PropertyLength", "first_snap_ridge_axial_length", "Dimensions")
    params.first_snap_ridge_axial_length = BASE_PARAMS["first_snap_ridge_axial_length"]
    params.addProperty("App::PropertyLength", "second_snap_ridge_start_position", "Dimensions")
    params.second_snap_ridge_start_position = BASE_PARAMS["second_snap_ridge_start_position"]
    params.addProperty("App::PropertyLength", "second_snap_ridge_end_position", "Dimensions")
    params.second_snap_ridge_end_position = BASE_PARAMS["second_snap_ridge_end_position"]
    params.addProperty("App::PropertyLength", "main_shaft_section_start", "Dimensions")
    params.main_shaft_section_start = BASE_PARAMS["main_shaft_section_start"]
    params.addProperty("App::PropertyLength", "snap_groove_width", "Dimensions")
    params.snap_groove_width = BASE_PARAMS["snap_groove_width"]
    params.addProperty("App::PropertyLength", "snap_groove_apex_position", "Dimensions")
    params.snap_groove_apex_position = BASE_PARAMS["snap_groove_apex_position"]
    params.addProperty("App::PropertyLength", "rear_shaft_section_start", "Dimensions")
    params.rear_shaft_section_start = BASE_PARAMS["rear_shaft_section_start"]
    params.addProperty("App::PropertyLength", "rear_taper_start_position", "Dimensions")
    params.rear_taper_start_position = BASE_PARAMS["rear_taper_start_position"]
    params.addProperty("App::PropertyLength", "connector_end_position", "Dimensions")
    params.connector_end_position = BASE_PARAMS["connector_end_position"]
    params.addProperty("App::PropertyLength", "total_connector_length", "Dimensions")
    params.total_connector_length = BASE_PARAMS["total_connector_length"]
    params.addProperty("App::PropertyLength", "undercut_depth_position", "Dimensions")
    params.undercut_depth_position = BASE_PARAMS["undercut_depth_position"]
    params.addProperty("App::PropertyLength", "conical_bore_length", "Dimensions")
    params.conical_bore_length = BASE_PARAMS["conical_bore_length"]
    params.addProperty("App::PropertyLength", "conical_bore_large_end_diameter", "Dimensions")
    params.conical_bore_large_end_diameter = BASE_PARAMS["conical_bore_large_end_diameter"]
    params.addProperty("App::PropertyLength", "conical_bore_small_end_diameter", "Dimensions")
    params.conical_bore_small_end_diameter = BASE_PARAMS["conical_bore_small_end_diameter"]
    params.addProperty("App::PropertyLength", "front_snap_taper_return_position", "Dimensions")
    params.front_snap_taper_return_position = BASE_PARAMS["front_snap_taper_return_position"]
    
    # XY Sketch (Main Profile)
    sketch = body.newObject("Sketcher::SketchObject", "FrontSketch")
    sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch.Reference = (doc.getObject("XY_Plane"), [])
    sketch.MapMode = "Plane"
    
    # Coordinates derived from parameters
    # The profile starts at front_section_length (positive X) and extends to connector_end_position.
    # However, the prompt says "extending from x = -front_section_length". 
    # Let's assume the coordinate system origin is at the front face of the main shaft (x=0 at main_shaft_section_start relative to front face? No.)
    # Let's place the Front Face of the Part at X = 0. The connector extends in +X.
    # "extending from x = -front_section_length to connector_end_position" implies the total length is roughly sum of parts.
    # Let's define the geometry relative to the Front Face (X=0).
    # Front section length is 3.1mm.
    
    # Points for the front stepped cylinder profile
    # Start X = -front_section_length (relative to some datum, let's say Front Face is 0, so start is 0? 
    # Prompt: "extending from x = -front_section_length". Let's assume the main shaft starts at 0, 
    # and the front section goes backwards? 
    # Let's interpret: The part exists in X range [-front_section_length, connector_end_position].
    # So Front Face is at X = -front_section_length.
    
    x_start = -BASE_PARAMS["front_section_length"]
    x_front_end = 0 # Front face of the main shaft section
    
    # 1. Front Section (Pin Body Diameter)
    # Radius
    r_front = BASE_PARAMS["pin_body_diameter"] / 2.0
    # Points: (x_start, r_front) to (x_front_end, r_front)
    p1 = App.Vector(x_start, r_front)
    p2 = App.Vector(x_front_end, r_front)
    sketch.addGeometry(Part.LineSegment(p1, p2), False)
    
    # 2. Front Snap Taper
    # Extends from x_front_end to x_front_end + front_snap_taper_length
    x_taper_start = x_front_end
    x_taper_end = x_front_end + BASE_PARAMS["front_snap_taper_length"]
    # Tapers from pin_body_diameter to snap_feature_diameter
    r_taper_start = r_front
    r_taper_end = BASE_PARAMS["snap_feature_diameter"] / 2.0
    p3 = App.Vector(x_taper_end, r_taper_end)
    sketch.addGeometry(Part.LineSegment(p2, p3), False)
    
    # 3. First Snap Ridge
    # Length: first_snap_ridge_axial_length
    # Diameter: snap_feature_diameter
    x_ridge_start = x_taper_end
    x_ridge_end = x_ridge_start + BASE_PARAMS["first_snap_ridge_axial_length"]
    p4 = App.Vector(x_ridge_start, r_taper_end)
    p5 = App.Vector(x_ridge_end, r_taper_end)
    sketch.addGeometry(Part.LineSegment(p4, p5), False)
    
    # 4. Second Snap Ridge
    # Start: second_snap_ridge_start_position (relative to Front Face? No, relative to part front?)
    # Let's assume coordinates are absolute from the part front face (which is at x_start).
    # So x = 0 is the front face of the main shaft.
    # x_front_end = 0.
    # x_ridge_start = front_snap_taper_length.
    # second_snap_ridge_start_position is absolute X from front face?
    # "second_snap_ridge_start_position = 8.5 mm"
    # So we are at X = 8.5.
    x_ridge2_start = BASE_PARAMS["second_snap_ridge_start_position"]
    x_ridge2_end = BASE_PARAMS["second_snap_ridge_end_position"]
    p6 = App.Vector(x_ridge2_start, r_taper_end)
    p7 = App.Vector(x_ridge2_end, r_taper_end)
    sketch.addGeometry(Part.LineSegment(p6, p7), False)
    
    # 5. Intermediate Section (Outer Diameter)
    # From second_snap_ridge_end_position to main_shaft_section_start
    x_mid_start = x_ridge2_end
    x_mid_end = BASE_PARAMS["main_shaft_section_start"]
    r_mid = BASE_PARAMS["outer_diameter"] / 2.0
    p8 = App.Vector(x_mid_start, r_mid)
    p9 = App.Vector(x_mid_end, r_mid)
    sketch.addGeometry(Part.LineSegment(p8, p9), False)
    
    # 6. Snap Groove
    # Width: snap_groove_width
    # Apex position: snap_groove_apex_position (absolute X)
    # Narrows to snap_feature_diameter
    x_groove_start = x_mid_end
    x_groove_end = x_mid_end + BASE_PARAMS["snap_groove_width"]
    r_groove_start = r_mid
    r_groove_end = BASE_PARAMS["snap_feature_diameter"] / 2.0
    p10 = App.Vector(x_groove_start, r_groove_start)
    p11 = App.Vector(x_groove_end, r_groove_end)
    sketch.addGeometry(Part.LineSegment(p10, p11), False)
    
    # 7. Rear Cavity (Cylindrical then Tapered)
    # Rear shaft section start: rear_shaft_section_start (absolute X)
    # This implies a cylindrical section from groove end to rear_shaft_section_start?
    # Or is the groove the start of the rear section?
    # "The rear cavity remains cylindrical and then flares internally toward the rear face."
    # Let's assume cylindrical from groove end to rear_shaft_section_start.
    x_cyl_start = x_groove_end
    x_cyl_end = BASE_PARAMS["rear_shaft_section_start"]
    p12 = App.Vector(x_cyl_start, r_groove_end)
    p13 = App.Vector(x_cyl_end, r_groove_end)
    sketch.addGeometry(Part.LineSegment(p12, p13), False)
    
    # Taper from rear_shaft_section_start to connector_end_position
    x_taper2_start = x_cyl_end
    x_taper2_end = BASE_PARAMS["connector_end_position"]
    # Flares internally: from snap_feature_diameter to outer_diameter? 
    # "flares internally toward the rear face" usually means gets larger.
    # But wait, connector_end_position is the outer face.
    # Let's check the taper: "from conical_bore_large_end_diameter to conical_bore_small_end_diameter" was for the bore.
    # External taper: "flares internally" -> gets bigger.
    r_taper2_end = BASE_PARAMS["outer_diameter"] / 2.0
    p14 = App.Vector(x_taper2_end, r_taper2_end)
    sketch.addGeometry(Part.LineSegment(p13, p14), False)
    
    # Close the loop? 
    # We need to go back down the other side.
    # Undercut: "circumferential groove narrows to snap_feature_diameter before the rear cylindrical section."
    # Actually, the description says "circumferential groove narrows to snap_feature_diameter before the rear cylindrical section."
    # My sequence: Outer -> Groove -> Rear Cyl -> Taper to End.
    # Wait, "before the rear cylindrical section" implies the groove is BEFORE the rear cylinder.
    # My sequence: Main Shaft -> Ridge -> Mid -> Groove -> Rear Cyl -> Taper.
    # This matches.
    
    # Now the return path (bottom half)
    # We need to go from p14 (End, Outer) back to p1 (Start, Front)
    
    # Taper back (Reversed)
    p15 = App.Vector(x_taper2_start, r_taper2_end)
    sketch.addGeometry(Part.LineSegment(p15, p14), False) # Redundant, just closing? No, p14 is end.
    # Actually, we need to connect p14 to p13? No, p14 is the tip.
    # We are tracing the perimeter.
    # Current: ... -> p13 (Rear Cyl start) -> p14 (End Tip).
    # Now reverse: p14 -> p15 (Rear Cyl start) -> p12 (Rear Cyl end) -> p11 (Groove end) ...
    # Wait, p12 is rear_shaft_section_start.
    # p13 is same x as p12? Yes.
    # So p14 -> p13.
    sketch.addGeometry(Part.LineSegment(p14, p13), False)
    sketch.addGeometry(Part.LineSegment(p13, p12), False)
    sketch.addGeometry(Part.LineSegment(p12, p11), False)
    sketch.addGeometry(Part.LineSegment(p11, p10), False)
    sketch.addGeometry(Part.LineSegment(p10, p9), False)
    sketch.addGeometry(Part.LineSegment(p9, p8), False)
    sketch.addGeometry(Part.LineSegment(p8, p7), False)
    sketch.addGeometry(Part.LineSegment(p7, p6), False)
    sketch.addGeometry(Part.LineSegment(p6, p5), False)
    sketch.addGeometry(Part.LineSegment(p5, p4), False)
    sketch.addGeometry(Part.LineSegment(p4, p3), False)
    sketch.addGeometry(Part.LineSegment(p3, p2), False)
    sketch.addGeometry(Part.LineSegment(p2, p1), False)
    
    # Constraints
    Sketcher.addConstraint(sketch, "Coincident", 0, 1, 0, 0, 0, 0, 0) # p1 origin
    Sketcher.addConstraint(sketch, "Parallel", 0, 0, 1, 0, 0, 0, 0) # Vertical lines
    Sketcher.addConstraint(sketch, "Vertical", 0, 1, 0, 0, 0, 0, 0) # All vertical? No, x varies.
    # Standardize: Horizontal lines are radius (y), Vertical lines are x.
    # But we have slanted lines.
    # Let's just constrain coincidences and horizontal/vertical where possible.
    # Actually, for a profile, we usually constrain X and Y independently.
    # Y is constant for horizontal segments. X is constant for vertical.
    # Slanted segments are defined by points.
    # Let's add constraints to make it robust:
    Sketcher.addConstraint(sketch, "Horizontal", 0, 0, 0, 0, 0, 0, 0) # p1_y
    # ... too many manual constraints. 
    # Let's rely on the geometry being closed and the solver fixing
