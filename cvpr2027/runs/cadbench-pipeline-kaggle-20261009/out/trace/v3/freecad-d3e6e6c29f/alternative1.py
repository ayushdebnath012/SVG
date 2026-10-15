from pathlib import Path
import FreeCAD as App
import Part
from Part import Shape, Vector
from Sketcher import Constraint, ConstraintType
import math

def create_document():
    """Creates a new FreeCAD document."""
    doc = App.newDocument("SteeringKnuckle")
    return doc

def create_body_and_params(doc):
    """Creates the Body and named parameters."""
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Named Parameters
    params = body.newObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "body_depth", "Dimensions", "Thickness of the knuckle")
    params.body_depth = 15.0
    
    params.addProperty("App::PropertyLength", "spindle_bore_diameter", "Dimensions", "Diameter of spindle hole")
    params.spindle_bore_diameter = 15.0
    
    params.addProperty("App::PropertyLength", "spindle_boss_diameter", "Dimensions", "Diameter of spindle boss outer")
    params.spindle_boss_diameter = 24.0
    
    params.addProperty("App::PropertyLength", "spindle_center_offset_x", "Dimensions", "X offset of spindle boss center")
    params.spindle_center_offset_x = -100.0
    
    params.addProperty("App::PropertyLength", "hub_outer_arc_radius", "Dimensions", "Radius of main hub arc")
    params.hub_outer_arc_radius = 26.9
    
    params.addProperty("App::PropertyLength", "hub_inner_diameter", "Dimensions", "Inner diameter of hub ring")
    params.hub_inner_diameter = 41.7
    
    params.addProperty("App::PropertyLength", "bracket_arm_outer_fillet_radius", "Dimensions", "Radius of outer arm blend")
    params.bracket_arm_outer_fillet_radius = 26.9
    
    params.addProperty("App::PropertyLength", "bracket_arm_inner_fillet_radius", "Dimensions", "Radius of inner arm blend")
    params.bracket_arm_inner_fillet_radius = 24.0
    
    params.addProperty("App::PropertyLength", "bracket_arm_outer_width", "Dimensions", "Width of arm at spindle")
    params.bracket_arm_outer_width = 18.0
    
    params.addProperty("App::PropertyLength", "bracket_arm_slot_end_arc_radius", "Dimensions", "Radius of slot ends")
    params.bracket_arm_slot_end_arc_radius = 5.0
    
    params.addProperty("App::PropertyLength", "bracket_arm_slot_width", "Dimensions", "Width of the arm slot")
    params.bracket_arm_slot_width = 10.0
    
    params.addProperty("App::PropertyLength", "bracket_arm_slot_left_center_x", "Dimensions", "X center of left slot")
    params.bracket_arm_slot_left_center_x = -77.8
    
    params.addProperty("App::PropertyLength", "bracket_arm_slot_right_center_x", "Dimensions", "X center of right slot")
    params.bracket_arm_slot_right_center_x = -41.8
    
    params.addProperty("App::PropertyLength", "bracket_tab_width", "Dimensions", "Width of bracket tabs")
    params.bracket_tab_width = 16.0
    
    params.addProperty("App::PropertyLength", "bracket_tab_outer_extent_y", "Dimensions", "Max Y extent of tabs")
    params.bracket_tab_outer_extent_y = 47.0
    
    params.addProperty("App::PropertyLength", "bracket_tab_inner_extent_y", "Dimensions", "Min Y extent of tabs")
    params.bracket_tab_inner_extent_y = 25.6828737
    
    params.addProperty("App::PropertyLength", "arm_inner_fillet_center_left_x", "Dimensions", "X center of inner left fillet")
    params.arm_inner_fillet_center_left_x = -85.6125054
    
    params.addProperty("App::PropertyLength", "arm_inner_fillet_center_left_y", "Dimensions", "Y center of inner left fillet")
    params.arm_inner_fillet_center_left_y = 33.0
    
    params.addProperty("App::PropertyLength", "arm_outer_fillet_center_right_x", "Dimensions", "X center of outer right fillet")
    params.arm_outer_fillet_center_right_x = -40.0703132
    
    params.addProperty("App::PropertyLength", "arm_outer_fillet_center_right_y", "Dimensions", "Y center of outer right fillet")
    params.arm_outer_fillet_center_right_y = 35.9
    
    params.addProperty("App::PropertyLength", "center_bore_diameter", "Dimensions", "Diameter of cross-bore")
    params.center_bore_diameter = 10.0
    
    params.addProperty("App::PropertyLength", "center_bore_y_offset", "Dimensions", "Y offset for cross-bore")
    params.center_bore_y_offset = 7.5
    
    # Angles
    params.addProperty("App::PropertyAngle", "hub_outer_arc_lower_start_angle", "Angles", "Start angle for lower hub arc")
    params.hub_outer_arc_lower_start_angle = -138.1420401
    
    params.addProperty("App::PropertyAngle", "hub_outer_arc_lower_end_angle", "Angles", "End angle for lower hub arc")
    params.hub_outer_arc_lower_end_angle = -107.301374
    
    params.addProperty("App::PropertyAngle", "hub_outer_arc_upper_start_angle", "Angles", "Start angle for upper hub arc")
    params.hub_outer_arc_upper_start_angle = 107.301374
    
    params.addProperty("App::PropertyAngle", "hub_outer_arc_upper_end_angle", "Angles", "End angle for upper hub arc")
    params.hub_outer_arc_upper_end_angle = 138.1420401
    
    params.addProperty("App::PropertyAngle", "hub_outer_arc_right_start_angle", "Angles", "Start angle for right hub arc")
    params.hub_outer_arc_right_start_angle = -72.698626
    
    params.addProperty("App::PropertyAngle", "hub_outer_arc_right_end_angle", "Angles", "End angle for right hub arc")
    params.hub_outer_arc_right_end_angle = 72.698626
    
    params.addProperty("App::PropertyAngle", "arm_outer_fillet_lower_start_angle", "Angles", "Start angle for outer fillet")
    params.arm_outer_fillet_lower_start_angle = 41.8579599
    
    params.addProperty("App::PropertyAngle", "arm_outer_fillet_upper_end_angle", "Angles", "End angle for outer fillet")
    params.arm_outer_fillet_upper_end_angle = -41.8579599
    
    params.addProperty("App::PropertyAngle", "arm_inner_fillet_lower_end_angle", "Angles", "End angle for inner fillet")
    params.arm_inner_fillet_lower_end_angle = 113.5564643
    
    params.addProperty("App::PropertyAngle", "arm_inner_fillet_upper_start_angle", "Angles", "Start angle for inner fillet")
    params.arm_inner_fillet_upper_start_angle = -113.5564643
    
    params.addProperty("App::PropertyAngle", "spindle_boss_arc_start_angle", "Angles", "Start angle for spindle arc")
    params.spindle_boss_arc_start_angle = 66.4435357
    
    params.addProperty("App::PropertyAngle", "spindle_boss_arc_end_angle", "Angles", "End angle for spindle arc")
    params.spindle_boss_arc_end_angle = -66.4435357
    
    params.addProperty("App::PropertyAngle", "hub_inner_ring_split_angle_1", "Angles", "Split angle 1 for inner ring")
    params.hub_inner_ring_split_angle_1 = 67.4373731
    
    params.addProperty("App::PropertyAngle", "hub_inner_ring_split_angle_2", "Angles", "Split angle 2 for inner ring")
    params.hub_inner_ring_split_angle_2 = 112.5626269
    
    params.addProperty("App::PropertyAngle", "hub_inner_ring_split_angle_3", "Angles", "Split angle 3 for inner ring")
    params.hub_inner_ring_split_angle_3 = 247.4373731
    
    params.addProperty("App::PropertyAngle", "hub_inner_ring_split_angle_4", "Angles", "Split angle 4 for inner ring")
    params.hub_inner_ring_split_angle_4 = 292.5626269
    
    return body, params

def create_base_sketch(body, params):
    """Creates the base XY sketch defining the main outline and hub."""
    sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch.MapMode = "FlatFace"
    sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation()) # Reset to ensure FlatFace on XY
    
    # Helper to add circle
    def add_circle(center, radius):
        return Part.Circle(center, App.Vector(0, 0, 1), radius)
    
    # Helper to add line segment
    def add_line(p1, p2):
        return Part.LineSegment(p1, p2)
    
    # 1. Hub Outer Arc (Right side)
    r = params.hub_outer_arc_radius
    a1 = params.hub_outer_arc_right_start_angle
    a2 = params.hub_outer_arc_right_end_angle
    sketch.addGeometry(add_circle(App.Vector(0, 0, 0), r), False)
    
    # 2. Hub Inner Ring (Split into 4 arcs to allow chamfering/drilling if needed later, though spec says cross-drilled)
    # We will construct the inner ring as a single circle for the main pad, then maybe subtract or just rely on the pad shape.
    # The prompt says "cross-drilled hole... runs along the tab axis". This implies a hole in the solid.
    # The inner ring is defined by split angles. Let's create the main shape first.
    
    # Main Hub Ring (Inner)
    inner_r = params.hub_inner_diameter / 2
    sketch.addGeometry(add_circle(App.Vector(0, 0, 0), inner_r), False)
    
    # Main Spindle Boss (Outer)
    boss_r = params.spindle_boss_diameter / 2
    sketch.addGeometry(add_circle(App.Vector(params.spindle_center_offset_x, 0, 0), boss_r), False)
    
    # Spindle Boss Bore
    bore_r = params.spindle_bore_diameter / 2
    sketch.addGeometry(add_circle(App.Vector(params.spindle_center_offset_x, 0, 0), bore_r), False)
    
    # Arm Outer Fillet (Right side blend between Hub and Spindle)
    # Defined by center and angles.
    # Center: (arm_outer_fillet_center_right_x, arm_outer_fillet_center_right_y)
    # Angles: arm_outer_fillet_lower_start_angle to arm_outer_fillet_upper_end_angle
    # Note: Angles are counter-clockwise from +X. 
    # Lower start is positive (top quadrant?), Upper end is negative (bottom quadrant?). 
    # Let's assume standard math angles.
    c = App.Vector(params.arm_outer_fillet_center_right_x, params.arm_outer_fillet_center_right_y, 0)
    r_f = params.bracket_arm_outer_fillet_radius
    a_start = params.arm_outer_fillet_lower_start_angle
    a_end = params.arm_outer_fillet_upper_end_angle
    
    # To create an arc between two angles on a circle:
    p_start = c + App.Vector(math.cos(math.radians(a_start)), math.sin(math.radians(a_start)), 0) * r_f
    p_end = c + App.Vector(math.cos(math.radians(a_end)), math.sin(math.radians(a_end)), 0) * r_f
    
    # We need to connect the hub arc and spindle arc. 
    # The hub arc ends at hub_outer_arc_right_end_angle (72.7 deg).
    # The spindle arc starts at spindle_boss_arc_start_angle (66.4 deg).
    # The fillet connects them.
    
    sketch.addGeometry(add_circle(c, r_f), False)
    
    # 3. Arm Inner Fillet (Left side blend)
    # Center: (arm_inner_fillet_center_left_x, arm_inner_fillet_center_left_y)
    c = App.Vector(params.arm_inner_fillet_center_left_x, params.arm_inner_fillet_center_left_y, 0)
    r_f = params.bracket_arm_inner_fillet_radius
    a_end = params.arm_inner_fillet_lower_end_angle # 113.5 deg
    a_start = params.arm_inner_fillet_upper_start_angle # -113.5 deg
    
    p_start = c + App.Vector(math.cos(math.radians(a_start)), math.sin(math.radians(a_start)), 0) * r_f
    p_end = c + App.Vector(math.cos(math.radians(a_end)), math.sin(math.radians(a_end)), 0) * r_f
    
    sketch.addGeometry(add_circle(c, r_f), False)
    
    # 4. Bracket Tabs
    # "Two bracket tabs extend from the hub, one on each side of the arm axis"
    # "centered through the plate thickness" -> They are part of the main body.
    # "cross-drilled hole... runs along the tab axis" -> This means the hole goes through the tabs.
    # Tab geometry: Width, Outer extent Y, Inner extent Y.
    # They extend from the hub. Let's assume they extend in Y direction from the inner ring?
    # Or maybe they are the "arms" of the knuckle?
    # "steering knuckle with an integral bracket arm"
    # Usually, the arm is the long part (Spindle to Hub). The tabs are usually on the hub side.
    # Let's define the tab shape relative to the hub.
    # Tab width = 16.0. 
    # Outer extent Y = 47.0. Inner extent Y = 25.68.
    # This sounds like a slot or a specific profile.
    # Let's create a rectangular-ish profile for the tabs.
    # Let's place them at Y = +/- (bracket_tab_outer_extent_y) ? No, "extend from the hub".
    # Let's assume they extend from the inner ring radius outwards.
    # But the description says "cross-drilled hole... runs along the tab axis".
    # This implies the hole is perpendicular to the XY plane? No, "along the tab axis".
    # If the tab axis is Y, the hole is along Y.
    # Let's create the main pad first, then add holes.
    
    # For now, we will construct the main outer profile based on the arcs provided, 
    # and the "tabs" might be implied by the "arm" or specific cutouts. 
    # However, the prompt explicitly lists tab dimensions. 
    # Let's add the tab shapes as separate circles/arcs if they protrude, or modify the inner profile.
    # Given "integral bracket arm", maybe the "arm" is the long part, and "tabs" are the two small protrusions on the hub.
    # Let's add two circular arcs or rectangles at the hub side.
    # Let's assume they are located at Y = +/- 47.0?
    # Let's add two circles at (0, 47) and (0, -47) with radius related to width?
    # Or maybe they are the "arms" themselves?
    # Let's stick to the prompt: "Two bracket tabs extend from the hub".
    # Let's create two circular arcs at the top and bottom of the hub area.
    # Radius? Let's assume they are width/2? Or use the extents.
    # Let's create a rectangle shape for the tabs.
    # Center at (0, 47.0) and (0, -47.0)?
    # Let's add them as circles for now to define the extent, then refine.
    # Actually, let's create the main pad, then add the tabs as separate pads or modify the sketch.
    # Since the prompt asks for a "single PartDesign Body producing exactly one solid", 
    # we can use multiple pads or a complex sketch.
    # Let's add the tabs as circles in the sketch to define the outer boundary.
    
    tab_width = params.bracket_tab_width
    tab_outer_y = params.bracket_tab_outer_extent_y
    tab_inner_y = params.bracket_tab_inner_extent_y
    
    # Tab 1 (Top)
    # Let's assume it's a rectangle from Y=tab_inner_y to Y=tab_outer_y?
    # Or centered at tab_outer_y?
    # Let's assume centered at tab_outer_y.
    # Rectangle: x = +/- tab_width/2, y = tab_inner_y to tab_outer_y.
    sketch.addGeometry(add_line(App.Vector(-tab_width/2, tab_outer_y, 0), App.Vector(-tab_width/2, tab_inner_y, 0)), False)
    sketch.addGeometry(add_line(App.Vector(tab_width/2, tab_outer_y, 0), App.Vector(tab_width/2, tab_inner_y, 0)), False)
    sketch.addGeometry(add_line(App.Vector(tab_width/2, tab_inner_y, 0), App.Vector(-tab_width/2, tab_inner_y, 0)), False)
    sketch.addGeometry(add_line(App.Vector(-tab_width/2, tab_outer_y, 0), App.Vector(-tab_width/2, tab_inner_y, 0)), False)
    # Actually, let's just add the corners.
    sketch.addGeometry(add_line(App.Vector(-tab_width/2, tab_outer_y, 0), App.Vector(-tab_width/2, tab_inner_y, 0)), False)
    sketch.addGeometry(add_line(App.Vector(tab_width/2, tab_outer_y, 0), App.Vector(tab_width/2, tab_inner_y, 0)), False)
    sketch.addGeometry(add_line(App.Vector(-tab_width/2, tab_inner_y, 0), App.Vector(tab_width/2, tab_inner_y, 0)), False)
