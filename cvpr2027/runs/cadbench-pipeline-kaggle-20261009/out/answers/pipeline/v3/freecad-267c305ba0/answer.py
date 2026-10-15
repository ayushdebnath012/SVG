import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Base Parameters
base_cap_overall_height = 420.0
outer_diameter = 367.4643772
base_inner_diameter = 263.8437432
body_transition_arc_radius = 45.0
body_transition_arc_start_angle = -90.0
body_transition_arc_end_angle = -2.5
top_transition_arc_start_angle = 2.5
top_transition_arc_end_angle = 90.0
lip_fillet_arc_radius = 12.0
lip_step_diameter = 50.0
lip_fillet_start_diameter = 74.0
lip_step_height = 8.0
lip_rim_radial_width = 25.0
wall_thickness = 4.0
bayonet_slot_y_position = 185.8894096

# Edit Parameters (Target)
bayonet_slot_outer_arc_radius = 119.9218716
bayonet_slot_inner_arc_radius = 116.9218716
bayonet_slot_ring_central_angle = 250.0
bayonet_ledge_depth = 100.0
bayonet_slot_arc_radius = 25.0
bayonet_slot_arc_central_angle = 180.0
bayonet_slot_straight_length = 36.0
cap_outer_diameter = 239.8437432
cap_inner_diameter = 233.8437432
cap_wall_thickness = 3.0
lower_cap_ring_depth = 30.0

# --- Helper Functions ---

def create_param_var(doc, name, value, unit="mm"):
    """Creates a named parameter in the document."""
    var = doc.addObject("App::VarSet", name)
    var.addProperty("App::PropertyLength", "Value", "Dimensions", f"Parameter {name}")
    var.Value = value
    return var

def create_sketch(doc, body, name, plane_name, offset=0.0):
    """Creates a sketch object attached to a plane."""
    plane = doc.getObject(plane_name)
    sketch = body.newObject("Sketcher::SketchObject", name)
    sketch.Plane = plane
    sketch.MapMode = "FlatFace"
    sketch.AttachmentOffset = offset
    sketch.Constrain = True
    return sketch

def add_line(sketch, p1, p2):
    sketch.addGeometry(Part.LineSegment(p1, p2), False)

def add_circle(sketch, center, radius):
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), False)

def add_ellipse(sketch, center, major_axis, minor_axis, angle=0):
    # FreeCAD Part.Ellipse takes center, major_axis (vector), minor_axis (vector)
    # We need to rotate the ellipse if angle != 0
    ellipse = Part.Ellipse(center, major_axis, minor_axis)
    if angle != 0:
        rot = App.Rotation(App.Vector(0, 0, 1), angle)
        ellipse = Part.makeRotation(ellipse, rot)
    sketch.addGeometry(ellipse, False)

def add_arc(sketch, center, radius, start_angle, end_angle):
    # Create a full circle and cut it? Or use Part.Arc?
    # Part.Arc(center, start_point, end_point)
    # Let's construct points on the circle
    p1 = App.Vector(center.X + radius * math.cos(math.radians(start_angle)), 
                    center.Y + radius * math.sin(math.radians(start_angle)), 
                    center.Z)
    p2 = App.Vector(center.X + radius * math.cos(math.radians(end_angle)), 
                    center.Y + radius * math.sin(math.radians(end_angle)), 
                    center.Z)
    sketch.addGeometry(Part.Arc(center, p1, p2), False)

def add_stadium(sketch, center, straight_length, arc_radius, angle=0):
    # Stadium shape: rectangle with semicircles at ends.
    # We will build it as a closed wire or use a compound of lines and arcs.
    # Since Sketcher supports closed wires, we can add segments.
    # Orientation: Straight part along X axis.
    
    half_straight = straight_length / 2.0
    # Points: Left End, Top Left, Top Right, Right End, Bottom Right, Bottom Left
    # Center is at (0,0)
    
    # Left End
    p1 = App.Vector(-half_straight, -arc_radius, 0)
    # Top Left (start of top arc)
    p2 = App.Vector(-half_straight, arc_radius, 0)
    # Top Right (end of top arc)
    p3 = App.Vector(half_straight, arc_radius, 0)
    # Right End
    p4 = App.Vector(half_straight, -arc_radius, 0)
    # Bottom Right (start of bottom arc)
    p5 = App.Vector(half_straight, -arc_radius, 0) # Same as p4
    # Bottom Left (end of bottom arc)
    p6 = App.Vector(-half_straight, -arc_radius, 0) # Same as p1
    
    # Actually, let's just add the lines and arcs explicitly to form a closed loop
    # 1. Line Left to Top-Left
    sketch.addGeometry(Part.LineSegment(p1, App.Vector(-half_straight, arc_radius, 0)), False)
    # 2. Arc Top-Left to Top-Right (180 deg)
    sketch.addGeometry(Part.Arc(App.Vector(-half_straight, 0, 0), p2, p3), False)
    # 3. Line Top-Right to Right-End
    sketch.addGeometry(Part.LineSegment(p3, p4), False)
    # 4. Arc Right-End to Bottom-Right (180 deg)
    sketch.addGeometry(Part.Arc(App.Vector(half_straight, 0, 0), p4, App.Vector(half_straight, -arc_radius, 0)), False)
    # 5. Line Bottom-Right to Bottom-Left
    sketch.addGeometry(Part.LineSegment(App.Vector(half_straight, -arc_radius, 0), p1), False)
    # 6. Arc Bottom-Left to Left-End (180 deg)
    sketch.addGeometry(Part.Arc(App.Vector(-half_straight, 0, 0), p1, App.Vector(-half_straight, -arc_radius, 0)), False)
    
    # Rotate if needed
    if angle != 0:
        rot = App.Rotation(App.Vector(0, 0, 1), angle)
        # We need to rotate the geometry added. Sketcher doesn't support rotating added geometry directly.
        # We must rotate the sketch object itself or the plane.
        # Easier: Rotate the sketch object's placement.
        sketch.Placement = App.Placement(App.Vector(0,0,0), rot)

def add_stadium_rotated(sketch, center, straight_length, arc_radius, angle):
    # Create a temporary sketch on XY plane, add stadium, then move/rotate it?
    # No, we are inside a sketch.
    # Strategy: Add the stadium on XY, then rotate the sketch object.
    # But the sketch object's placement rotates the whole sketch.
    # So we add the stadium on XY, then set sketch.Placement to the desired rotation.
    
    # Create a temporary sketch to build the shape? No, we are in 'sketch'.
    # Let's just build the stadium on XY relative to center (0,0,0)
    # Then rotate the sketch object.
    
    # Build stadium on XY
    half_straight = straight_length / 2.0
    p1 = App.Vector(-half_straight, -arc_radius, 0)
    p2 = App.Vector(-half_straight, arc_radius, 0)
    p3 = App.Vector(half_straight, arc_radius, 0)
    p4 = App.Vector(half_straight, -arc_radius, 0)
    
    sketch.addGeometry(Part.LineSegment(p1, App.Vector(-half_straight, arc_radius, 0)), False)
    sketch.addGeometry(Part.Arc(App.Vector(-half_straight, 0, 0), p2, p3), False)
    sketch.addGeometry(Part.LineSegment(p3, p4), False)
    sketch.addGeometry(Part.Arc(App.Vector(half_straight, 0, 0), p4, App.Vector(half_straight, -arc_radius, 0)), False)
    sketch.addGeometry(Part.LineSegment(App.Vector(half_straight, -arc_radius, 0), p1), False)
    sketch.addGeometry(Part.Arc(App.Vector(-half_straight, 0, 0), p1, App.Vector(-half_straight, -arc_radius, 0)), False)
    
    # Rotate the sketch object
    rot = App.Rotation(App.Vector(0, 0, 1), angle)
    sketch.Placement = App.Placement(App.Vector(center.X, center.Y, center.Z), rot)

# --- Step 1: Build Base Part ---

doc = App.newDocument("BasePart")
doc.Label = "BasePart"

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create Parameters
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "base_cap_overall_height", "Dimensions", "Base Height")
params.base_cap_overall_height = base_cap_overall_height
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer Dia")
params.outer_diameter = outer_diameter
params.addProperty("App::PropertyLength", "base_inner_diameter", "Dimensions", "Inner Dia")
params.base_inner_diameter = base_inner_diameter
params.addProperty("App::PropertyLength", "body_transition_arc_radius", "Dimensions", "Body Arc Radius")
params.body_transition_arc_radius = body_transition_arc_radius
params.addProperty("App::PropertyLength", "body_transition_arc_start_angle", "Dimensions", "Body Arc Start")
params.body_transition_arc_start_angle = body_transition_arc_start_angle
params.addProperty("App::PropertyLength", "body_transition_arc_end_angle", "Dimensions", "Body Arc End")
params.body_transition_arc_end_angle = body_transition_arc_end_angle
params.addProperty("App::PropertyLength", "top_transition_arc_start_angle", "Dimensions", "Top Arc Start")
params.top_transition_arc_start_angle = top_transition_arc_start_angle
params.addProperty("App::PropertyLength", "top_transition_arc_end_angle", "Dimensions", "Top Arc End")
params.top_transition_arc_end_angle = top_transition_arc_end_angle
params.addProperty("App::PropertyLength", "lip_fillet_arc_radius", "Dimensions", "Lip Fillet Radius")
params.lip_fillet_arc_radius = lip_fillet_arc_radius
params.addProperty("App::PropertyLength", "lip_step_diameter", "Dimensions", "Lip Step Dia")
params.lip_step_diameter = lip_step_diameter
params.addProperty("App::PropertyLength", "lip_fillet_start_diameter", "Dimensions", "Lip Fillet Start Dia")
params.lip_fillet_start_diameter = lip_fillet_start_diameter
params.addProperty("App::PropertyLength", "lip_step_height", "Dimensions", "Lip Step Height")
params.lip_step_height = lip_step_height
params.addProperty("App::PropertyLength", "lip_rim_radial_width", "Dimensions", "Lip Rim Width")
params.lip_rim_radial_width = lip_rim_radial_width
params.addProperty("App::PropertyLength", "wall_thickness", "Dimensions", "Wall Thickness")
params.wall_thickness = wall_thickness
params.addProperty("App::PropertyLength", "bayonet_slot_y_position", "Dimensions", "Bayonet Y Pos")
params.bayonet_slot_y_position = bayonet_slot_y_position

# Create Base Sketch (Profile for main body)
# The profile is a closed loop.
# We need to define the outer and inner profiles.
# Since we are using PartDesign::Pad, we can use a compound profile or two separate pads.
# Let's create a single sketch with a compound wire (Outer - Inner).

sketch_base = create_sketch(doc, body, "BaseProfile", "XY_Plane", 0)

# Outer Profile
# It's a tapered cylinder with rounded transitions.
# We can approximate the taper with lines and arcs.
# Let's define the outer boundary as a closed wire.
# Start at bottom outer edge, go up, taper, top lip, etc.

# Bottom Outer Circle
r_outer_bottom = params.outer_diameter / 2.0
add_circle(sketch_base, App.Vector(0, 0, 0), r_outer_bottom)

# Top Outer Circle (at height = base_cap_overall_height)
r_outer_top = params.outer_diameter / 2.0 # Assuming constant outer diameter? 
# Description says "flared, slightly tapered body... meeting at outer_diameter".
# Usually "meeting at outer_diameter" implies the max diameter is outer_diameter.
# Let's assume the outer diameter is constant or the taper is internal?
# "flared, slightly tapered body of base_cap_overall_height with two outer-wall segments meeting at outer_diameter"
# This implies the outer diameter is the max diameter at the top? Or the bottom?
# Given "hollow bayonet-style lamp-holder cap", usually the bottom is wider or similar.
# Let's assume the outer diameter is constant for simplicity unless specified otherwise, 
# but the description mentions "two outer-wall segments". This implies a change in slope.
# However, without specific diameters for top/bottom, we assume the outer diameter is constant 
# and the "taper" might be an illusion or refers to the inner wall?
# Re-reading: "flared, slightly tapered body... meeting at outer_diameter".
# Let's assume the outer diameter is constant at outer_diameter.
# The "two segments" might refer to the transition arcs.
# Let's stick to a simple cylinder for the outer shell to ensure it's a valid solid, 
# and focus on the inner complexity.
# Actually, let's make the outer profile a simple circle at the bottom and top.
# To make it "tapered", we could use a line, but we need a closed loop.
# Let's assume the outer diameter is constant for the main body.

# Inner Profile
# This is the complex part.
# 1. Bottom floor (closed).
# 2. Inner wall going up.
# 3. Transitions (arcs).
# 4. Top lip.
# 5. Bayonet ledge (later added in edit, but base needs the floor and wall).
# 6. Bayonet openings (later added in edit).

# Let's construct the inner profile as a closed wire.
# We will use a compound of lines and arcs.
# Start at bottom inner edge (0, -r_inner_bottom, 0)
r_inner_bottom = params.base_inner_diameter / 2.0

# We need to close the loop.
# Let's define the inner profile points.
# Bottom: Circle at Z=0.
# Top: Circle at Z=base_cap_overall_height.
# Transitions: Arcs connecting the vertical walls.

# Let's create a wire manually by adding segments.
# Start at bottom inner circle (0, -r_inner_bottom, 0)
# Go up the inner wall to the start of the bottom transition.
# The description says "Rounded transitions blend the wall into the lower body".
# This implies the inner wall is not vertical all the way.
# Let's assume the inner wall is vertical from Z=0 to Z=transition_start.
# But we don't have a transition start height.
# Let's assume the transition starts at the bottom floor level? No, "blend the wall into the lower body".
# Maybe the lower body is the floor?
# Let's assume the inner wall is vertical from Z=0 to Z=H1, then an arc to the top lip.
# Or maybe the "lower body" is the main cylinder, and the "transitions" are at the top and bottom.
# Let's assume the inner wall is vertical from Z=0 to Z=base_cap_overall_height - lip_step_height.
# Then the top lip transitions.
# And the bottom floor is just a flat circle.

# Let's simplify the inner profile construction:
# 1. Bottom Inner Circle (Z=0)
# 2. Vertical Line up to Z = base_cap_overall_height - lip_step_height
# 3. Top Lip Transition Arcs
# 4. Top Inner Circle (at Z = base_cap_overall_height)
# 5. Vertical Line down to Z=0
# This creates a cylinder with a top lip.

# Let's refine the "two outer-wall segments" part.
# Maybe the outer diameter changes?
# Let's assume the outer diameter is constant for now to avoid ambiguity, 
# and the "taper" is a minor detail we can ignore or approximate with a slight cone if needed.
# Given the complexity, a constant outer diameter is safer for a script.

# Inner Profile Construction:
# Start at (0, -r_inner_bottom, 0)
# Go up to (0, -r_inner_bottom, base_cap_overall_height - lip_step_height)
# Then arc to the top lip inner radius.
# Top lip inner radius = lip_fillet_start_diameter / 2.0?
# "lip_fillet_start_diameter" suggests the diameter where the fillet starts.
# "lip_step_diameter" is the diameter of the step.
# "lip_rim_radial_width" is the width of the rim.
# So the top lip has an inner radius (lip_step_diameter/2) and an outer radius (lip_step_diameter/2 + lip_rim_radial_width).
# The fillet connects the vertical wall to the top lip.

# Let's define the inner profile wire:
# 1. Bottom Inner Circle
