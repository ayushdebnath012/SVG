import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Base Parameters
R = {
    "rotor_outer_diameter": 250.0,
    "hub_outer_diameter": 84.9558108,
    "hub_height": 5.0,
    "disc_lower_surface_position": 3.0,
    "disc_upper_surface_position": 8.0,
    "hub_top_transition_radius": 40.0,
    "braking_band_upper_inner_radius": 55.0,
    "hat_transition_fillet_radius": 6.885713,
}

# Edit Parameters
EDIT = {
    "center_bore_diameter": 40.0,
    "hat_ventilation_window_count": 5,
    "hat_ventilation_window_sweep_angle": 32.0,
    "hat_ventilation_window_phase_angle": -90.0,
    "hub_mounting_hole_diameter": 6.0,
    "hub_mounting_hole_pitch_circle_diameter": 60.0,
    "hub_mounting_hole_count": 5,
    "peripheral_hole_diameter": 6.0,
    "peripheral_outer_ring_pitch_circle_diameter": 232.2646056,
    "peripheral_outer_ring_phase_angle": -100.4944943,
    "peripheral_middle_ring_pitch_circle_diameter": 216.1390363,
    "peripheral_middle_ring_phase_angle": -95.9477697,
    "peripheral_inner_ring_pitch_circle_diameter": 195.9364374,
    "peripheral_inner_ring_phase_angle": -92.3400124,
    "ventilation_channel_count": 8,
    "ventilation_channel_inner_boundary_radius": 62.0,
    "ventilation_channel_outer_boundary_radius": 89.0,
    "ventilation_channel_guide_arc_radius": 44.5,
    "ventilation_channel_fillet_radius": 5.0,
    "ventilation_channel_clockwise_guide_center_phase_angle": -51.4285714,
    "ventilation_channel_counterclockwise_guide_center_radius": 45.2702065,
    "ventilation_channel_counterclockwise_guide_center_phase_angle": -18.5264601,
}

# --- Helper Functions ---

def create_doc():
    """Creates a new FreeCAD document."""
    doc = App.newDocument("Rotor")
    doc.Label = "Brake Rotor"
    return doc

def get_plane(doc, name):
    """Gets a standard plane object from the document."""
    return doc.getObject(name)

def add_varset(body, name, **kwargs):
    """Adds a VarSet to the body for parameters."""
    varset = body.newObject("App::VarSet", name)
    for key, value in kwargs.items():
        varset.addProperty("App::PropertyLength", key, "Dimensions")
        varset[key] = value
    return varset

def add_sketch(body, name, plane_name="XY_Plane", offset=0.0):
    """Adds a sketch object to the body."""
    plane = get_plane(body, plane_name)
    sketch = body.newObject("Sketcher::SketchObject", name)
    sketch.Plane = plane
    sketch.MapMode = "FlatFace"
    sketch.Placement = App.Placement(App.Vector(0, 0, offset))
    return sketch

def add_pad(body, name, profile, length, **kwargs):
    """Adds a Pad feature."""
    pad = body.newObject("PartDesign::Pad", name)
    pad.Profile = profile
    pad.Length = length
    pad.Type = "Blind"
    for k, v in kwargs.items():
        setattr(pad, k, v)
    return pad

def add_pocket(body, name, profile, length, **kwargs):
    """Adds a Pocket feature."""
    pocket = body.newObject("PartDesign::Pocket", name)
    pocket.Profile = profile
    pocket.Length = length
    pocket.Type = "Blind"
    for k, v in kwargs.items():
        setattr(pocket, k, v)
    return pocket

def add_revolution(body, name, profile, axis, angle, **kwargs):
    """Adds a Revolution feature."""
    rev = body.newObject("PartDesign::Revolution", name)
    rev.Profile = profile
    rev.ReferenceAxis = axis
    rev.Angle = angle
    rev.Axis = axis[0]
    for k, v in kwargs.items():
        setattr(rev, k, v)
    return rev

def add_hole(body, name, profile, length, **kwargs):
    """Adds a Hole feature."""
    hole = body.newObject("PartDesign::Hole", name)
    hole.Profile = profile
    hole.Length = length
    hole.Type = "ThroughAll"
    for k, v in kwargs.items():
        setattr(hole, k, v)
    return hole

def add_pattern(body, name, originals, axis, angle, occurrences, **kwargs):
    """Adds a PolarPattern feature."""
    pattern = body.newObject("PartDesign::PolarPattern", name)
    pattern.Originals = originals
    pattern.Axis = axis
    pattern.Angle = angle
    pattern.Occurrences = occurrences
    for k, v in kwargs.items():
        setattr(pattern, k, v)
    return pattern

def add_fillet(body, name, edges, radius, **kwargs):
    """Adds a Fillet feature."""
    fillet = body.newObject("PartDesign::Fillet", name)
    fillet.Edges = edges
    fillet.Radius = radius
    for k, v in kwargs.items():
        setattr(fillet, k, v)
    return fillet

def add_chamfer(body, name, edges, size, **kwargs):
    """Adds a Chamfer feature."""
    chamfer = body.newObject("PartDesign::Chamfer", name)
    chamfer.Edges = edges
    chamfer.Size = size
    for k, v in kwargs.items():
        setattr(chamfer, k, v)
    return chamfer

def add_line(sketch, p1, p2):
    """Adds a line segment to a sketch."""
    sketch.addGeometry(Part.LineSegment(p1, p2), False)

def add_circle(sketch, center, radius):
    """Adds a circle to a sketch."""
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), False)

def add_arc(sketch, center, radius, start_angle, end_angle):
    """Adds an arc to a sketch."""
    # FreeCAD Sketcher arcs are defined by center, radius, and two points or angles
    # We use the angle method if available, otherwise construct points
    # Note: Sketcher.Constraint("Angle") is for constraints. 
    # To add geometry, we use Part.Arc.
    # Part.Arc(center, radius, start_angle, end_angle) works in radians.
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)
    arc = Part.Arc(center, App.Vector(0, 0, 1), start_rad, end_rad)
    sketch.addGeometry(arc, False)

def add_constraint(sketch, constraint_type, *args):
    """Adds a constraint to a sketch."""
    sketch.addConstraint(constraint_type, *args)

def recompute(doc):
    """Triggers recomputation of the document."""
    doc.recompute()

# --- Step 1: Build Base Part ---

def build_base_part(doc):
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Parameters
    params = add_varset(body, "Dimensions",
        rotor_outer_diameter=R["rotor_outer_diameter"],
        hub_outer_diameter=R["hub_outer_diameter"],
        hub_height=R["hub_height"],
        disc_lower_surface_position=R["disc_lower_surface_position"],
        disc_upper_surface_position=R["disc_upper_surface_position"],
        hub_top_transition_radius=R["hub_top_transition_radius"],
        braking_band_upper_inner_radius=R["braking_band_upper_inner_radius"],
        hat_transition_fillet_radius=R["hat_transition_fillet_radius"],
    )

    # --- Main Profile Sketch (Outer Shape) ---
    # This sketch defines the outer profile of the rotor from bottom to top.
    # Z=0 is bottom.
    # 1. Hub Bottom (Z=0) to Hub Top (Z=hub_height)
    # 2. Hat Transition (Z=hub_height) to Disc Upper (Z=disc_upper_surface_position)
    # 3. Braking Band (Z=disc_upper_surface_position) to Disc Lower (Z=disc_lower_surface_position)
    
    main_sketch = add_sketch(body, "MainProfile", "XY_Plane", 0.0)
    
    # Points
    # Outer Radius
    r_outer = R["rotor_outer_diameter"] / 2.0
    # Inner Radius (Hub Outer)
    r_hub_outer = R["hub_outer_diameter"] / 2.0
    # Inner Radius (Braking Band Upper)
    r_band_inner = R["braking_band_upper_inner_radius"]
    
    # Z positions
    z_hub_top = R["hub_height"]
    z_disc_upper = R["disc_upper_surface_position"]
    z_disc_lower = R["disc_lower_surface_position"]
    
    # Segments
    # 1. Hub Bottom (Z=0) to Hub Top (Z=hub_height)
    #    Radius: r_hub_outer
    add_circle(main_sketch, App.Vector(0, 0, 0), r_hub_outer)
    add_line(main_sketch, App.Vector(r_hub_outer, 0, 0), App.Vector(r_hub_outer, 0, z_hub_top))
    add_circle(main_sketch, App.Vector(0, 0, z_hub_top), r_hub_outer)
    
    # 2. Hat Transition (Z=hub_height) to Disc Upper (Z=disc_upper_surface_position)
    #    Radius: r_outer
    #    Fillet between r_hub_outer and r_outer at Z=hub_height
    add_circle(main_sketch, App.Vector(0, 0, z_hub_top), r_outer)
    add_line(main_sketch, App.Vector(r_outer, 0, z_hub_top), App.Vector(r_outer, 0, z_disc_upper))
    add_circle(main_sketch, App.Vector(0, 0, z_disc_upper), r_outer)
    
    # 3. Braking Band (Z=disc_upper_surface_position) to Disc Lower (Z=disc_lower_surface_position)
    #    Radius: r_band_inner
    #    Fillet between r_outer and r_band_inner at Z=disc_upper_surface_position
    add_circle(main_sketch, App.Vector(0, 0, z_disc_upper), r_band_inner)
    add_line(main_sketch, App.Vector(r_band_inner, 0, z_disc_upper), App.Vector(r_band_inner, 0, z_disc_lower))
    add_circle(main_sketch, App.Vector(0, 0, z_disc_lower), r_band_inner)
    
    # Constraints
    # Coincident centers
    add_constraint(main_sketch, "Coincident", 0, 2, 1, 1) # Center of circle 0 to center of circle 1
    add_constraint(main_sketch, "Coincident", 0, 4, 1, 1) # Center of circle 0 to center of circle 2
    add_constraint(main_sketch, "Coincident", 0, 6, 1, 1) # Center of circle 0 to center of circle 3
    
    # Tangent/Vertical lines
    add_constraint(main_sketch, "Vertical", 1, 1)
    add_constraint(main_sketch, "Vertical", 3, 1)
    add_constraint(main_sketch, "Vertical", 5, 1)
    
    # Horizontal lines
    add_constraint(main_sketch, "Horizontal", 1, 2)
    add_constraint(main_sketch, "Horizontal", 3, 4)
    add_constraint(main_sketch, "Horizontal", 5, 6)
    
    # Lengths
    add_constraint(main_sketch, "Length", 1, 2, R["hub_height"])
    add_constraint(main_sketch, "Length", 3, 4, R["disc_upper_surface_position"] - R["hub_height"])
    add_constraint(main_sketch, "Length", 5, 6, R["disc_lower_surface_position"] - R["disc_upper_surface_position"])
    
    # Radii
    add_constraint(main_sketch, "Radius", 0, 2, R["hub_outer_diameter"] / 2.0)
    add_constraint(main_sketch, "Radius", 0, 4, R["rotor_outer_diameter"] / 2.0)
    add_constraint(main_sketch, "Radius", 0, 6, R["braking_band_upper_inner_radius"])
    
    # Fillets
    # Between Hub Top and Hat Start
    add_fillet(body, "Fillet_Hat_Start", (main_sketch, ["Edge1", "Edge2"]), R["hat_transition_fillet_radius"])
    # Between Hat End and Band Start
    add_fillet(body, "Fillet_Band_Start", (main_sketch, ["Edge3", "Edge4"]), R["hat_transition_fillet_radius"])
    
    # Pad the main profile
    pad_main = add_pad(body, "Pad_Main", main_sketch, R["disc_lower_surface_position"])
    pad_main.setExpression("Length", "Dimensions.disc_lower_surface_position")

    # --- Center Bore (Base) ---
    # Small central pilot opening
    bore_sketch = add_sketch(body, "BoreSketch", "XY_Plane", 0.0)
    bore_radius = 5.0 # Small pilot
    add_circle(bore_sketch, App.Vector(0, 0, 0), bore_radius)
    add_constraint(bore_sketch, "Center", 0, 1) # Center at origin
    add_constraint(bore_sketch, "Radius", 0, 1, 5.0)
    
    pocket_bore = add_pocket(body, "Pocket_Bore", bore_sketch, R["disc_lower_surface_position"])
    pocket_bore.setExpression("Length", "Dimensions.disc_lower_surface_position")

    recompute(doc)
    return doc

# --- Step 2: Apply Edits ---

def apply_edits(doc):
    # Get existing features
    body = doc.getObject("Body")
    pad_main = body.getObject("Pad_Main")
    pocket_bore = body.getObject("Pocket_Bore")
    
    # Update Parameters
    params = body.getObject("Dimensions")
    params.center_bore_diameter = EDIT["center_bore_diameter"]
    params.hat_ventilation_window_count = EDIT["hat_ventilation_window_count"]
    params.hat_ventilation_window_sweep_angle = EDIT["hat_ventilation_window_sweep_angle"]
    params.hat_ventilation_window_phase_angle = EDIT["hat_ventilation_window_phase_angle"]
    params.hub_mounting_hole_diameter = EDIT["hub_mounting_hole_diameter"]
    params.hub_mounting_hole_pitch_circle_diameter = EDIT["hub_mounting_hole_pitch_circle_diameter"]
    params.hub_mounting_hole_count = EDIT["hub_mounting_hole_count"]
    params.peripheral_hole_diameter = EDIT["peripheral_hole_diameter"]
    params.peripheral_outer_ring_pitch_circle_diameter = EDIT["peripheral_outer_ring_pitch_circle_diameter"]
    params.peripheral_outer_ring_phase_angle = EDIT["peripheral_outer_ring_phase_angle"]
    params.peripheral_middle_ring_pitch_circle_diameter = EDIT["peripheral_middle_ring_pitch_circle_diameter"]
    params.peripheral_middle_ring_phase_angle = EDIT["peripheral_middle_ring_phase_angle"]
    params.peripheral_inner_ring_pitch_circle_diameter = EDIT["peripheral_inner_ring_pitch_circle_diameter"]
    params.peripheral_inner_ring_phase_angle = EDIT["peripheral_inner_ring_phase_angle"]
    params.ventilation_channel_count = EDIT["ventilation_channel_count"]
    params.ventilation_channel_inner_boundary_radius = EDIT["ventilation_channel_inner_boundary_radius"]
    params.ventilation_channel_outer_boundary_radius = EDIT["ventilation_channel_outer_boundary_radius"]
    params.ventilation_channel_guide_arc_radius = EDIT["ventilation_channel_guide_arc_radius"]
    params.ventilation_channel_fillet_radius = EDIT["ventilation_channel_fillet_radius"]
    params.ventilation_channel_clockwise_guide_center_phase_angle = EDIT["ventilation_channel_clockwise_guide_center_phase_angle"]
    params.ventilation_channel_counterclockwise_guide_center_radius = EDIT["ventilation_channel_counterclockwise_guide_center_radius"]
    params.ventilation_channel_counterclockwise_guide_center_phase_angle = EDIT["ventilation_channel_counterclockwise_guide_center_phase_angle"]

    # 1. Expand Center Bore
    # We need to modify the bore sketch or create a new one. 
    # Since sketches are immutable in terms of geometry once added, we create a new sketch for the expanded bore.
    # However, to keep it simple and editable, we can just create a new pocket with a new sketch.
    
    bore_sketch_new = add_sketch(body, "BoreSketch_New", "XY_Plane", 0.0)
    add_circle(bore_sketch_new, App.Vector(0, 0, 0), EDIT["center_bore_diameter"] / 2.0)
    add_constraint(bore_sketch_new, "Center", 0, 1)
    add_constraint(bore_sketch_new, "Radius", 0, 1, EDIT["center_bore_diameter"] / 2.0)
    
    pocket_bore_new = add_pocket(body, "Pocket_Bore_New", bore_sketch_new, R["disc_lower_surface_position"])
    pocket_bore_new.setExpression("Length", "Dimensions.disc_lower_surface_position")
