from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

# --- Configuration and Parameters ---
# Base Part Parameters
params_base = {
    "bracket_base_length": 110.3712707,
    "bracket_height": 85.0,
    "bracket_thickness": 12.0,
    "corner_fillet_arc_radius": 20.0,
    "corner_fillet_arc_central_angle": 66.7504374,
    "outer_curved_arc_radius": 77.0,
    "outer_curved_arc_center_x": 58.0,
    "bracket_overall_width": 25.0,
    "bracket_overall_height": 65.0,
    "bracket_extrusion_depth": 85.0,
    "angled_edge_top_x_offset": 17.4166975,
    "edge_slot_width": 3.2153903,
    "base_center_notch_center_offset": 45.0,
    "base_center_notch_arc_radius": 15.0,
    "base_center_notch_rectangular_width": 20.0,
    "base_center_notch_rectangular_height": 30.0,
    "base_center_notch_depth": 43.0,
    "base_mounting_hole_row_offset": 55.0,
    "base_mounting_hole_center_spacing": 55.0,
    "base_mounting_through_hole_diameter": 5.0,
    "base_mounting_counterbore_diameter": 10.0,
    "base_mounting_counterbore_depth": 5.0
}

# Edit Parameters (only used for the edit phase)
params_edit = {
    "bearing_support_arc_radius": 26.0,
    "bearing_support_flat_width": 33.0,
    "bearing_support_boss_height": 9.0,
    "bearing_boss_through_bore_diameter": 15.0,
    "bearing_boss_counterbore_diameter": 30.0,
    "bearing_boss_counterbore_depth": 12.0
}

# --- Script Execution Logic ---

def create_document(name):
    """Creates a new FreeCAD document."""
    doc = App.newDocument(name)
    # Create standard axes and planes
    x_axis = doc.addObject("App::Axis", "X_Axis")
    y_axis = doc.addObject("App::Axis", "Y_Axis")
    z_axis = doc.addObject("App::Axis", "Z_Axis")
    
    # XY, YZ, XZ planes
    xy_plane = doc.addObject("Part::Plane", "XY_Plane")
    xy_plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation())
    
    yz_plane = doc.addObject("Part::Plane", "YZ_Plane")
    yz_plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0,0,math.pi/2))
    
    xz_plane = doc.addObject("Part::Plane", "XZ_Plane")
    xz_plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(math.pi/2,0,0))
    
    # Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    return doc, body

def create_sketch(body, name, plane, offset=0.0):
    """Creates a new sketch attached to the specified plane with an offset."""
    sketch = body.newObject("Sketcher::SketchObject", name)
    sketch.Placement = App.Placement(App.Vector(0, 0, offset))
    sketch.MapMode = "FlatFace"
    # Find the plane object
    plane_obj = None
    if plane == "XY_Plane": plane_obj = doc.getObject("XY_Plane")
    elif plane == "XZ_Plane": plane_obj = doc.getObject("XZ_Plane")
    elif plane == "YZ_Plane": plane_obj = doc.getObject("YZ_Plane")
    
    if plane_obj:
        sketch.Placement = App.Placement(plane_obj.Placement.toPlacement())
        # Force FlatFace on the specific plane
        # Note: In headless, we rely on the Placement matching the plane's coordinate system
        # For XY plane at origin, default placement works.
    
    return sketch

def add_line(sketch, p1, p2, is_constraint=False):
    sketch.addGeometry(Part.LineSegment(p1, p2), is_constraint)

def add_circle(sketch, center, axis, radius, is_constraint=False):
    sketch.addGeometry(Part.Circle(center, axis, radius), is_constraint)

def add_arc(sketch, center, axis, start_angle, end_angle, radius, is_constraint=False):
    # FreeCAD arcs are defined by start and end angles in radians
    sketch.addGeometry(Part.Arc(center, axis, start_angle, end_angle, radius), is_constraint)

def add_triangle(sketch, p1, p2, p3, is_constraint=False):
    sketch.addGeometry(Part.Triangle(p1, p2, p3), is_constraint)

def add_rectangle(sketch, center, width, height, is_constraint=False):
    # Create a rectangle by adding 4 lines or using a closed wire if available.
    # Here we add 4 lines.
    # Line 1: Right
    sketch.addGeometry(Part.LineSegment(
        App.Vector(center.X + width/2, center.Y - height/2, 0),
        App.Vector(center.X + width/2, center.Y + height/2, 0)
    ), is_constraint)
    # Line 2: Top
    sketch.addGeometry(Part.LineSegment(
        App.Vector(center.X + width/2, center.Y + height/2, 0),
        App.Vector(center.X - width/2, center.Y + height/2, 0)
    ), is_constraint)
    # Line 3: Left
    sketch.addGeometry(Part.LineSegment(
        App.Vector(center.X - width/2, center.Y + height/2, 0),
        App.Vector(center.X - width/2, center.Y - height/2, 0)
    ), is_constraint)
    # Line 4: Bottom
    sketch.addGeometry(Part.LineSegment(
        App.Vector(center.X - width/2, center.Y - height/2, 0),
        App.Vector(center.X + width/2, center.Y - height/2, 0)
    ), is_constraint)

def create_base_part(params):
    """Creates the base L-shaped part."""
    doc, body = create_document("BasePart")
    doc.setVariable("bracket_base_length", params["bracket_base_length"])
    doc.setVariable("bracket_height", params["bracket_height"])
    doc.setVariable("bracket_thickness", params["bracket_thickness"])
    doc.setVariable("corner_fillet_arc_radius", params["corner_fillet_arc_radius"])
    doc.setVariable("corner_fillet_arc_central_angle", params["corner_fillet_arc_central_angle"])
    doc.setVariable("outer_curved_arc_radius", params["outer_curved_arc_radius"])
    doc.setVariable("outer_curved_arc_center_x", params["outer_curved_arc_center_x"])
    doc.setVariable("bracket_overall_width", params["bracket_overall_width"])
    doc.setVariable("bracket_overall_height", params["bracket_overall_height"])
    doc.setVariable("bracket_extrusion_depth", params["bracket_extrusion_depth"])
    doc.setVariable("angled_edge_top_x_offset", params["angled_edge_top_x_offset"])
    doc.setVariable("edge_slot_width", params["edge_slot_width"])
    doc.setVariable("base_center_notch_center_offset", params["base_center_notch_center_offset"])
    doc.setVariable("base_center_notch_arc_radius", params["base_center_notch_arc_radius"])
    doc.setVariable("base_center_notch_rectangular_width", params["base_center_notch_rectangular_width"])
    doc.setVariable("base_center_notch_rectangular_height", params["base_center_notch_rectangular_height"])
    doc.setVariable("base_center_notch_depth", params["base_center_notch_depth"])
    doc.setVariable("base_mounting_hole_row_offset", params["base_mounting_hole_row_offset"])
    doc.setVariable("base_mounting_hole_center_spacing", params["base_mounting_hole_center_spacing"])
    doc.setVariable("base_mounting_through_hole_diameter", params["base_mounting_through_hole_diameter"])
    doc.setVariable("base_mounting_counterbore_diameter", params["base_mounting_counterbore_diameter"])
    doc.setVariable("base_mounting_counterbore_depth", params["base_mounting_counterbore_depth"])

    # --- Step 1: Curved Main Plate (L-shape logic) ---
    # The description says "curved main plate joined perpendicularly to a trapezoidal plate".
    # "Main plate uses two equal inner transition arcs joined tangentially by the centered outer curved transition."
    # This sounds like the side profile of the main plate.
    
    # Let's assume the L-shape is formed by extruding a profile on the XZ plane.
    # Profile:
    # 1. Outer curved transition (Arc)
    # 2. Inner transition arcs (2 arcs)
    # 3. Connection to perpendicular plate.
    
    # Let's construct the profile on the XZ plane.
    # Origin (0,0) is the start of the outer arc.
    # Radius = outer_curved_arc_radius (77mm)
    # Center = (outer_curved_arc_center_x, 0) relative to the arc start? 
    # The parameter says "center_x". Let's assume the arc is part of a circle centered at X = center_x.
    
    sketch_profile = body.newObject("Sketcher::SketchObject", "ProfileSketch")
    sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_profile.MapMode = "FlatFace"
    
    # Arc 1: Outer curved transition
    # Start at (0, 0). Radius 77. Center at (77, 0) -> Arc goes from 0 to 90 deg? 
    # Or Center at (77, 0) and arc goes from 0 to -90?
    # Let's assume standard: Start (0,0), Center (77,0), End (0, 77).
    # But the description says "centered outer curved transition".
    # Let's assume the arc starts at origin, goes to height H1.
    
    # Refined interpretation:
    # The "L" consists of a vertical section and a horizontal section.
    # The "Main Plate" is the horizontal one? Or the vertical one?
    # "joined perpendicularly to a trapezoidal plate".
    # Let's build the profile on XZ.
    # Point A: (0,0)
    # Arc 1: Radius 77, Center (77, 0). Start (0,0), End (0, 77). This is a quarter circle.
    # But we need "two equal inner transition arcs".
    
    # Alternative Interpretation:
    # The profile is defined by:
    # 1. An outer arc of radius 77.
    # 2. Two inner arcs of radius 20.
    # They are joined tangentially.
    
    # Let's try to construct a profile that matches the "L" description.
    # Let's say the "Main Plate" is the bottom part, extending to the right.
    # The "Perpendicular Plate" is the top part, extending upwards.
    
    # Let's define the vertices of the profile path:
    # V1: (0, 0)
    # V2: End of outer arc.
    # V3: Start of inner arc 1.
    # V4: End of inner arc 1.
    # V5: Start of inner arc 2.
    # V6: End of inner arc 2.
    # V7: Connection to perpendicular plate.
    
    # Given the complexity and specific parameters, let's try a specific geometric construction:
    # Outer Arc: Radius 77. Center (77, 0). Starts at (0,0), ends at (0, 77).
    # Inner Arc 1: Radius 20. Tangent to outer at (0,0)? No, that's a corner.
    # Tangent to outer at (0, 77)?
    
    # Let's assume the "L" is formed by a large radius fillet (77) connecting a horizontal bottom and a vertical left side?
    # No, "centered outer curved transition".
    
    # Let's try this:
    # Start at (0,0).
    # Outer Arc: Radius 77, Center (77, 0). From angle 180 to 90?
    # Let's assume the arc is from (0,0) to (0, 77) with center (77, 0).
    # Then we need to transition to the perpendicular plate.
    # The perpendicular plate is a "trapezoidal plate".
    
    # Let's simplify based on typical "L" bearing supports:
    # A horizontal plate (Main) and a vertical plate (Perpendicular).
    # The junction has fillets.
    
    # Profile Sketch Construction:
    # 1. Line from (0, 0) to (L, 0) ? No, curved.
    # 2. Arc from (0,0) to (0, H) with Radius 77?
    # 3. Inner arcs (R=20).
    
    # Let's assume the profile is:
    # - Start (0,0).
    # - Outer Arc (R=77) from (0,0) to (0, 77). Center (77,0).
    # - At (0,77), we need to transition.
    # - Inner Arc 1 (R=20). Tangent to previous arc? 
    #   Previous arc tangent at (0,77) is horizontal.
    #   So Inner Arc 1 starts at (0,77) with tangent horizontal?
    #   If it curves "in", center would be at (20, 77)?
    #   Then it ends at (20, 57)?
    # - Inner Arc 2 (R=20). Tangent to Inner Arc 1?
    #   Inner Arc 1 ends at (20, 57) with vertical tangent.
    #   Inner Arc 2 starts at (20, 57), curves in to (40, 57)?
    #   This creates a step.
    
    # Let's try a different interpretation of "Two equal inner transition arcs joined tangentially by the centered outer curved transition".
    # Maybe the "L" is the negative space? No, "consists of a curved main plate".
    
    # Let's try to build the profile explicitly:
    # 1. Start (0,0).
    # 2. Outer Arc (R=77, Center=77,0) from 180 deg to 90 deg. Points: (0,0) -> (0,77).
    # 3. Inner Arc 1 (R=20). Tangent to Outer at (0,77).
    #    Tangent vector at (0,77) for Outer Arc (center 77,0) is (-1, 0).
    #    So Inner Arc 1 starts at (0,77) going Left? That goes outside.
    #    Maybe the Outer Arc is the bottom curve?
    
    # Let's try:
    # Bottom curve: Outer Arc (R=77). Center (0, 77). Start (0,0) -> (77, 77).
    # Then vertical rise?
    
    # Let's stick to the most robust interpretation of "L-shaped bearing-support":
    # A horizontal leg and a vertical leg.
    # The "curved main plate" is the horizontal leg, shaped by the outer arc and inner arcs.
    # The "trapezoidal plate" is the vertical leg.
    
    # Profile:
    # 1. Start (0,0).
    # 2. Outer Arc (R=77). Center (77, 0). From 180 to 90. End (0, 77).
    # 3. Inner Arc 1 (R=20). Center (20, 77). From 90 to 180?
    #    Starts (0,77), goes to (20, 57).
    # 4. Inner Arc 2 (R=20). Center (40, 57). From 90 to 180?
    #    Starts (20, 57), goes to (40, 37).
    # 5. Line to connect to vertical plate?
    
    # This seems too arbitrary. Let's use the parameters directly to define a path.
    # Path:
    # P0 = (0, 0)
    # P1 = (0, 77) [End of Outer Arc]
    # P2 = (0, 77) [Start of Inner Arc 1]
    # P3 = (20, 57) [End of Inner Arc 1]
    # P4 = (20, 57) [Start of Inner Arc 2]
    # P5 = (40, 37) [End of Inner Arc 2]
    # P6 = (40, 37) [Start of Perpendicular Plate]
    
    # Wait, "joined tangentially".
    # Outer Arc (Center
