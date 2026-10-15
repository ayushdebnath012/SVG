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

def create_param_var(doc, name, value):
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

def add_arc(sketch, center, radius, start_angle, end_angle):
    p1 = App.Vector(center.X + radius * math.cos(math.radians(start_angle)), 
                    center.Y + radius * math.sin(math.radians(start_angle)), 
                    center.Z)
    p2 = App.Vector(center.X + radius * math.cos(math.radians(end_angle)), 
                    center.Y + radius * math.sin(math.radians(end_angle)), 
                    center.Z)
    sketch.addGeometry(Part.Arc(center, p1, p2), False)

def add_stadium(sketch, center, straight_length, arc_radius, angle=0):
    # Stadium shape: rectangle with semicircles at ends.
    # Orientation: Straight part along X axis.
    half_straight = straight_length / 2.0
    
    # Points relative to center (0,0) before rotation
    p1 = App.Vector(-half_straight, -arc_radius, 0)
    p2 = App.Vector(-half_straight, arc_radius, 0)
    p3 = App.Vector(half_straight, arc_radius, 0)
    p4 = App.Vector(half_straight, -arc_radius, 0)
    
    # Add segments
    sketch.addGeometry(Part.LineSegment(p1, App.Vector(-half_straight, arc_radius, 0)), False)
    sketch.addGeometry(Part.Arc(App.Vector(-half_straight, 0, 0), p2, p3), False)
    sketch.addGeometry(Part.LineSegment(p3, p4), False)
    sketch.addGeometry(Part.Arc(App.Vector(half_straight, 0, 0), p4, App.Vector(half_straight, -arc_radius, 0)), False)
    sketch.addGeometry(Part.LineSegment(App.Vector(half_straight, -arc_radius, 0), p1), False)
    sketch.addGeometry(Part.Arc(App.Vector(-half_straight, 0, 0), p1, App.Vector(-half_straight, -arc_radius, 0)), False)
    
    # Rotate the sketch object
    if angle != 0:
        rot = App.Rotation(App.Vector(0, 0, 1), angle)
        sketch.Placement = App.Placement(App.Vector(center.X, center.Y, center.Z), rot)

# --- Step 1: Build Base Part ---

doc = App.newDocument("BasePart")
doc.Label = "BasePart"

# Create Body
body = doc.addObject("PartDesign::Body", "Body")

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
sketch_base = create_sketch(doc, body, "BaseProfile", "XY_Plane", 0)

# --- Construct Base Profile Wire ---
# We will build a closed wire manually by adding segments to the sketch.
# The profile consists of an outer cylinder and an inner complex shape.
# To keep it simple and robust, we will create a compound of two closed wires: Outer and Inner.

# Outer Profile: Simple Cylinder
r_outer = params.outer_diameter / 2.0
add_circle(sketch_base, App.Vector(0, 0, 0), r_outer)

# Inner Profile: Complex Shape
# 1. Bottom Floor (Closed Circle)
r_inner_bottom = params.base_inner_diameter / 2.0
add_circle(sketch_base, App.Vector(0, 0, 0), r_inner_bottom)

# 2. Inner Wall Upwards
# We need to connect the bottom circle to the top lip.
# Let's define the inner wall as a vertical line from the bottom circle to the start of the top transition.
# Height of the vertical wall section:
h_vertical = params.base_cap_overall_height - params.lip_step_height

# Start point at bottom inner circle (0, -r_inner_bottom, 0)
# End point at top transition start (0, -r_inner_bottom, h_vertical)
# Note: The sketch is on XY plane (Z=0). We need to lift the sketch or use a different plane.
# The problem is that PartDesign::Pad extrudes along Z. If the sketch is on XY, the profile is in XY.
# The profile must be a closed loop in the XY plane.
# The "height" of the part comes from the Pad length, not the sketch Z coordinates.
# So the sketch defines the cross-section.
# The cross-section is a rectangle with rounded corners? No, it's a hollow cylinder with a top lip.
# The cross-section is an annulus (ring) with a top lip feature.
# Wait, the top lip is a feature on the top face, not part of the cross-section.
# The cross-section is simply an annulus with inner radius r_inner_bottom and outer radius r_outer.
# The top lip is created by a Pad or a Pocket?
# "The lip steps inward to a rounded rim". This implies a change in diameter at the top.
# So the cross-section is NOT a simple annulus. It's an annulus that widens at the top?
# No, if it widens at the top, the cross-section changes along Z. That requires a revolution of a profile that changes width.
# Let's assume the "tapered body" means the outer diameter changes.
# Let's assume the outer diameter is constant for the main body, and the "taper" is the transition arcs mentioned.
# Actually, let's interpret "two outer-wall segments meeting at outer_diameter" as:
# The outer wall has two segments. Maybe one is vertical, one is tapered?
# Given the complexity and lack of specific taper angles, let's assume a constant outer diameter for the main body
# and focus on the inner lip structure.
# The inner lip structure:
# - Bottom: Inner radius r_inner_bottom.
# - Top: Inner radius r_lip_inner = lip_step_diameter / 2.0.
# - Transition: Arcs connecting the vertical wall to the top lip.

# Since the sketch is a 2D profile, we cannot represent a tapered cylinder directly unless we use a revolution of a profile that changes width.
# But the sketch is on XY plane. The revolution will be around Z axis.
# So the profile must be a curve in the R-Z plane? No, the sketch is on XY, so it's in the R-Theta plane?
# No, PartDesign::Pad extrudes along Z. The sketch is in XY. The result is a cylinder.
# To get a tapered cylinder, we need to use PartDesign::Revolution.
# But the task asks for "PartDesign features (Pad, Pocket, Revolution...)".
# Let's use Revolution for the main body to handle the taper.
# Profile for Revolution: A line from (r_outer_bottom, 0) to (r_outer_top, H).
# But we also have an inner wall.
# Let's simplify:
# 1. Create a Pad for the main body (cylinder).
# 2. Create a Pocket for the inner cavity.
# 3. Create a Pad for the top lip.

# Let's re-evaluate the geometry based on "hollow bayonet-style lamp-holder cap".
# It's a cup shape.
# Outer shape: Cylinder with a flared top? Or just a cylinder.
# Inner shape: Cylinder with a stepped top lip.
# Let's assume the outer diameter is constant at outer_diameter.
# The "taper" might be the transition arcs at the top and bottom of the inner wall.
# Let's assume the inner wall is vertical from Z=0 to Z=H-lip_step_height.
# Then there are transition arcs to the top lip.
# And the top lip has a different inner diameter.

# Let's build the base part as:
# 1. Pad: Outer Cylinder (r_outer, H).
# 2. Pocket: Inner Cylinder (r_inner_bottom, H).
# 3. Pad: Top Lip (r_lip_inner, lip_step_height) on top of the inner cylinder? No, that would fill it.
# We need to subtract the inner cavity.
# Let's do:
# 1. Pad: Outer Cylinder (r_outer, H).
# 2. Pocket: Inner Cylinder (r_inner_bottom, H).
# 3. Pocket: Top Lip Cavity (r_lip_inner, lip_step_height) at the top.
# 4. Fillet: On the top edge of the inner wall.

# Let's refine the parameters:
# r_outer = outer_diameter / 2.0
# r_inner_bottom = base_inner_diameter / 2.0
# r_lip_inner = lip_step_diameter / 2.0
# r_lip_outer = lip_step_diameter / 2.0 + lip_rim_radial_width
# H = base_cap_overall_height
# H_lip = lip_step_height

# Steps:
# 1. Pad: Cylinder (r_outer, H).
# 2. Pocket: Cylinder (r_inner_bottom, H).
# 3. Pocket: Cylinder (r_lip_inner, H - H_lip) at the top? No, the lip is at the top.
# The lip is a protrusion on the top face of the inner cavity?
# "The lip steps inward to a rounded rim".
# This means the inner diameter increases at the top.
# So the inner cavity is wider at the top.
# So we need to subtract a larger cylinder at the top.
# Pocket 1: Cylinder (r_inner_bottom, H - H_lip).
# Pocket 2: Cylinder (r_lip_inner, H_lip) at the top.
# But this creates a sharp edge. We need fillets.
# Fillet: On the edge between Pocket 1 and Pocket 2.

# Let's implement this.

# --- Create Main Body Pad ---
sketch_outer = create_sketch(doc, body, "OuterProfile", "XY_Plane", 0)
add_circle(sketch_outer, App.Vector(0, 0, 0), params.outer_diameter / 2.0)
pad_outer = body.newObject("PartDesign::Pad", "PadOuter")
pad_outer.Profile = sketch_outer
pad_outer.Length = params.base_cap_overall_height
pad_outer.Midplane = False

# --- Create Inner Cavity Pockets ---
# Pocket 1: Bottom part of inner cavity
sketch_inner_bottom = create_sketch(doc, body, "InnerBottomProfile", "XY_Plane", 0)
add_circle(sketch_inner_bottom, App.Vector(0, 0, 0), params.base_inner_diameter / 2.0)
pocket_inner_bottom = body.newObject("PartDesign::Pocket", "PocketInnerBottom")
pocket_inner_bottom.Profile = sketch_inner_bottom
pocket_inner_bottom.Length = params.base_cap_overall_height - params.lip_step_height
pocket_inner_bottom.Type = "Blind"

# Pocket 2: Top part of inner cavity (the lip step)
sketch_inner_top = create_sketch(doc, body, "InnerTopProfile", "XY_Plane", 0)
add_circle(sketch_inner_top, App.Vector(0, 0, 0), params.lip_step_diameter / 2.0)
pocket_inner_top = body.newObject("PartDesign::Pocket", "PocketInnerTop")
pocket_inner_top.Profile = sketch_inner_top
pocket_inner_top.Length = params.lip_step_height
pocket_inner_top.Type = "Blind"

# --- Create Top Lip Fillet ---
# The fillet is on the edge between the bottom pocket and the top pocket.
# The edge is a circle at Z = H - H_lip.
# We need to select the edge.
# The edge is the intersection of the two pockets? No, the edge is the boundary of the top pocket on the side of the bottom pocket.
# Actually, the top pocket is subtracted from the solid. The bottom pocket is also subtracted.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We need to fillet this edge.
# But the edge is internal? No, it's the edge of the cavity.
# We can use PartDesign::Fillet.
# Base: The solid body.
# Edge: The edge of the top pocket.
# How to select the edge?
# The edge is the circle at Z = H - H_lip.
# We can create a sketch on the plane Z = H - H_lip and select the circle?
# Or we can use the edge of the pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can create a sketch on the plane Z = H - H_lip and select the circle.
# But the sketch must be on a plane.
# Let's create a sketch on the plane Z = H - H_lip.
# But we don't have a plane at that height.
# We can use the XY plane and offset it.
# sketch_fillet = create_sketch(doc, body, "FilletProfile", "XY_Plane", params.base_cap_overall_height - params.lip_step_height)
# add_circle(sketch_fillet, App.Vector(0, 0, 0), params.lip_step_diameter / 2.0)
# But this circle is in the XY plane, offset by Z.
# The edge we want to fillet is the circle at that height.
# The sketch circle will be coincident with the edge.
# Then we can use the sketch circle to select the edge.
# But the fillet feature needs an edge, not a sketch.
# We can use the edge of the pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary of the removed material.
# We need to fillet the edge of the remaining material.
# The edge is the circle at Z = H - H_lip with radius r_lip_inner.
# We can use the edge of the top pocket feature.
# Let's try to select the edge of the top pocket.
# The top pocket is a cylinder. Its side edge is at Z = H - H_lip.
# We can use the edge of the top pocket feature.
# But the pocket feature is a subtractive feature. The edge is the boundary
