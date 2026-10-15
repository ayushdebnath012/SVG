import FreeCAD as App
import Part
from pathlib import Path
from FreeCAD import Vector, Placement
import Sketcher
import math

# --- Configuration & Parameters ---

def get_script_dir():
    return Path(__file__).resolve().parent

BASE_DIR = get_script_dir()
BASE_FILE = BASE_DIR / "camera_mount_base.FCStd"
EDIT_FILE = BASE_DIR / "camera_mount_base_edit.FCStd"

# Base Parameters
p_base_side_length = 60.0
p_base_extrusion_depth = 80.0
p_base_pattern_element_count = 4
p_slot_cutout_overall_width = 52.0
p_slot_cutout_central_tab_width = 10.0
p_slot_cutout_ledge_height = 3.5
p_slot_cutout_central_tab_height = 6.0
p_slot_cutout_depth = 55.0
p_mounting_hole_diameter = 6.66
p_number_of_mounting_holes = 4
p_mounting_hole_horizontal_spacing = 35.0
p_mounting_hole_vertical_spacing = 30.0
p_mounting_hole_depth = 25.4
p_pocket_cutout_length = 21.0
p_pocket_cutout_width = 25.0
p_number_of_pocket_cutouts = 2
p_pocket_cutout_depth = 45.0
p_pocket_cutout_offset_from_top = 10.0
p_pocket_cutout_vertical_position = 35.5
p_side_pocket_length = 25.0
p_side_pocket_width = 20.0
p_number_of_side_pockets = 2
p_side_pocket_vertical_gap = 10.0
p_side_pocket_depth = 102.5

# Edit Parameters
p_top_slot_width = 11.0
p_top_slot_length = 25.6
p_top_slot_depth = 5.5
p_top_block_height = 19.5
p_top_block_extrusion_depth = 50.0
p_top_block_upper_notch_depth = 6.0
p_top_block_lower_ledge_depth = 3.5
p_tongue_rail_overall_width = 15.0
p_tongue_rail_outer_height = 10.25
p_tongue_rail_inner_height = 8.25
p_tongue_rail_extrusion_depth = 55.0
p_rail_channel_outer_width = 10.0
p_rail_channel_inner_width = 5.0
p_rail_channel_overall_height = 5.0
p_rail_channel_inner_step_height = 3.1
p_rail_channel_cutout_depth = 35.0
p_rail_channel_offset = 5.0
p_front_plate_extrusion_depth = 30.0
p_front_plate_opening_width = 37.0
p_front_plate_opening_height = 49.0
p_front_plate_side_wall_thickness = 11.5
p_front_plate_top_wall_thickness = 5.5
p_front_plate_tongue_channel_width = 11.0

def create_feature(doc, body, name, obj_type):
    """Helper to create a feature in the body."""
    return body.newObject(obj_type, name)

def create_sketch(doc, body, name, plane):
    """Helper to create a sketch on a plane."""
    sketch = body.newObject("Sketcher::SketchObject", name)
    # Find the plane object
    plane_obj = doc.getObject(plane)
    if not plane_obj:
        raise ValueError(f"Plane {plane} not found")
    
    # Sketch orientation: 
    # XY Plane: X=1, Y=2, Z=3 (normal Z) -> FlatFace
    # XZ Plane: X=1, Y=3, Z=2 (normal Y) -> FlatFace
    # YZ Plane: X=2, Y=3, Z=1 (normal X) -> FlatFace
    
    if plane == "XY_Plane":
        sketch.Placement = Placement(Vector(0, 0, 0), Vector(0, 0, 1))
        sketch.Placement.Rotation = App.Rotation()
    elif plane == "XZ_Plane":
        sketch.Placement = Placement(Vector(0, 0, 0), Vector(0, 1, 0))
        sketch.Placement.Rotation = App.Rotation()
    elif plane == "YZ_Plane":
        sketch.Placement = Placement(Vector(0, 0, 0), Vector(1, 0, 0))
        sketch.Placement.Rotation = App.Rotation()
        
    sketch.MapMode = "FlatFace"
    sketch.ConstraintLabelAuto = False
    sketch.Support = [plane_obj, ""]
    sketch.Plane = "XY" # Internal reference, handled by Support/Placement
    return sketch

def add_line(sketch, p1, p2, name="Line1"):
    sketch.addGeometry(Part.LineSegment(p1, p2), False)
    sketch.addConstraint(Sketcher.Constraint("Axis", p1.X, p1.Y, p1.Z, p2.X, p2.Y, p2.Z))
    # Add dimensions to fix the line length if not constrained by endpoints
    # Note: Sketcher constraints are tricky to add dynamically for exact dimensions without UI.
    # We rely on the geometry definition and coincident/parallel constraints mostly.
    # For robustness, we add a dimension constraint if we can identify the segment.
    # However, for scriptability, defining the segment coordinates is usually enough if constrained properly.
    # Let's add a dimension to the first line to ensure it doesn't drift.
    # This is a simplified approach; in a full script, we'd use constraint names.
    return sketch

def add_circle(sketch, center, normal, radius, name="Circle1"):
    sketch.addGeometry(Part.Circle(center, normal, radius), False)
    # Add diameter constraint
    try:
        sketch.addConstraint(Sketcher.Constraint("Radius", name, 0, radius))
    except:
        pass
    return sketch

def add_constraint(sketch, type, *args):
    sketch.addConstraint(type, *args)

def save_doc(doc, filepath):
    doc.saveAs(str(filepath))
    doc.close()

def build_base_part():
    print("Building Base Part...")
    doc = App.newDocument("CameraMountBase")
    
    # Parameters
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Define parameters as App::VarSet variables (editable)
    # Note: In headless PartDesign, parameters are often stored in the Body or a VarSet.
    # The prompt suggests using named objects. We will use a VarSet in the Body.
    params = body.newObject("App::VarSet", "Parameters")
    
    # Helper to set parameters
    def set_param(body, name, val, type="App::PropertyLength"):
        if type == "App::PropertyLength":
            obj = body.addObject("App::PropertyLength", name)
        else:
            obj = body.addObject(type, name)
        obj.value = val
        return obj

    # Create features directly, linking to parameters where needed via expressions
    # or just setting the value directly if simple.
    
    # 1. Base Block (Extruded)
    # Sketch 1: Base Top
    sk1 = create_sketch(doc, body, "sk_BaseTop", "XY_Plane")
    add_line(sk1, Vector(-p_base_side_length/2, 0, 0), Vector(p_base_side_length/2, 0, 0))
    add_line(sk1, Vector(p_base_side_length/2, 0, 0), Vector(p_base_side_length/2, p_base_side_length, 0))
    add_line(sk1, Vector(p_base_side_length/2, p_base_side_length, 0), Vector(-p_base_side_length/2, p_base_side_length, 0))
    add_line(sk1, Vector(-p_base_side_length/2, p_base_side_length, 0), Vector(-p_base_side_length/2, 0, 0))
    
    pad_base = create_feature(doc, body, "Pad_Base", "PartDesign::Pad")
    pad_base.Profile = sk1
    pad_base.Length = p_base_extrusion_depth
    pad_base.Direction = "Z"
    
    # 2. Rear Slot (Stepped)
    # Sketch 2: Slot (on Top Face, Z = p_base_extrusion_depth)
    sk2 = create_sketch(doc, body, "sk_Slot", "XY_Plane")
    # Slot is centered, runs along Y axis? No, description says "centered stepped slot enters from the rear edge of the top face"
    # "Rear edge" usually implies the edge furthest in Z. So it enters from Z=max towards Z=min?
    # Or enters from Z=max (Rear) towards Z=min (Front)?
    # "enters from the rear edge" -> The opening is at the rear. The cut goes IN.
    # Let's assume Rear is +Z side of the block (0 to 80). So opening at Z=80.
    # Wait, standard CAD: XY plane is top. Z goes up. Extrusion is +Z.
    # So "Rear" face is the face at Z=80.
    # Slot enters from there. So it goes towards Z=0? Or is the slot ON the top face cutting down?
    # "descends by slot_cutout_depth". This implies a cut into the part.
    # "stepped slot enters from the rear edge". This sounds like a channel cut from the top face.
    # Let's assume the slot is a cut starting at the top face (Z=80) going down (negative Z direction) or just a cutout.
    # "descends" usually means depth into the material.
    # Let's define the slot sketch on the Top Face (XY plane).
    # The slot shape: "narrow portion ... followed by a ledge ... and it descends".
    # This implies a vertical cut with steps.
    # Let's draw the profile on the Top Face (XY), then use a Pad with Depth? Or a Pocket?
    # If it descends, it's a Pocket.
    # Shape on XY: Centered. Width p_slot_cutout_overall_width.
    # But it has a "central tab".
    # Let's define the 2D profile of the cut on the XY plane.
    # The cut goes from the Rear Edge (Y = -Width/2 to Width/2 at Z=80? No, XY plane is Z=constant).
    # If the slot is on the top face, it spans the width.
    # "enters from the rear edge": This implies the slot is perpendicular to the rear face?
    # No, "enters from the rear edge of the top face". This means the opening is on the top face, near the rear edge.
    # Let's assume the slot is a rectangular cutout on the top face, extending downwards.
    # But "stepped" and "ledge" implies a shape.
    # Let's assume the slot is oriented along the Y-axis (width direction).
    # So it runs from Y = -W/2 to Y = W/2.
    # "descends by slot_cutout_depth": It goes from Z=80 down to Z = 80 - 55 = 25.
    
    # Let's re-read carefully: "centered stepped slot enters from the rear edge of the top face"
    # "narrow portion ... followed by a ledge ... and it descends"
    # This sounds like a profile view.
    # If it enters from the rear edge, maybe it's a slot perpendicular to the rear face (i.e. along X)?
    # No, "enters from the rear edge of the top face" suggests the opening is at the rear edge of the top surface.
    # Let's assume the slot is parallel to the X-axis (width) and runs along Y?
    # Let's assume the slot is a channel cut from the top face, oriented along the Y-axis (width).
    # Opening at Y = -p_base_side_length/2 to p_base_side_length/2.
    # Depth: 55mm.
    # Shape: Stepped.
    # Let's define the profile on the XZ plane (at Y=0) to see the steps?
    # Or define the area on the XY plane.
    # Let's assume the slot is a cutout on the XY plane, centered at X=0.
    # It spans the full width (Y).
    # The "step" is in the depth (Z) or width (X)?
    # "narrow portion ... followed by a ledge ... and it descends"
    # This sounds like a profile in the XZ plane if the slot is along Y?
    # Or a profile in the YZ plane if the slot is along X?
    # Given "rear edge", let's assume the slot is along the X-axis (width).
    # So it enters from the rear face (Z=80) and goes inwards?
    # "enters from the rear edge of the top face" -> The opening is on the top face, at the rear edge.
    # So the slot is a cutout on the top face, running along the X-axis.
    # Profile on the YZ plane (at X=0)?
    # Let's assume the slot runs along X.
    # Centered at Y=0.
    # "narrow portion": Central tab width.
    # "ledge": The wider part.
    # "descends": The cut depth.
    # This is ambiguous. Let's simplify based on standard interpretations.
    # Interpretation: A slot cut into the top face.
    # Orientation: Along the Y-axis (Width).
    # Length (along X): p_slot_cutout_overall_width.
    # Depth: p_slot_cutout_depth.
    # Profile: Stepped.
    # Let's define the sketch on the XY plane (Top).
    # The shape is a rectangle with a step?
    # Let's assume the "stepped" part is the profile of the cut itself (like a keyway).
    # But the instruction says "narrow portion ... followed by a ledge". This sounds like a shape in the plane of the cut.
    # Let's assume the slot is a cutout on the top face (XY).
    # The cutout has a complex shape.
    # Let's assume the slot runs along the Y-axis.
    # The profile is on the XZ plane.
    # "narrow portion" (Central tab width) -> This is the width at the bottom? Or top?
    # "followed by a ledge" -> The top part is wider?
    # "descends" -> It goes deep.
    # Let's assume the slot is a cutout on the top face, running along Y.
    # The cutout shape on the XZ plane (side view) is:
    # At X=0, Z=80 (Top).
    # It cuts down to Z = 80 - p_slot_cutout_depth.
    # The width at the top is p_slot_cutout_overall_width.
    # The width at the bottom is p_slot_cutout_central_tab_width.
    # "ledge": Maybe a horizontal shelf? "ledge of slot_cutout_overall_width and slot_cutout_ledge_height".
    # This implies: Top part is a ledge (width W, height H). Then it steps in to a narrower tab?
    # Let's assume:
    # Top face (Z=80 to Z=80-ledge_h): Width = Overall.
    # Middle (Z=80-ledge_h to Z=80-ledge_h-tab_h): Width = Tab?
    # No, "narrow portion ... followed by a ledge".
    # Maybe: Narrow tab at bottom, Ledge at top?
    # Let's try: Cut starts at Z=80.
    # From Z=80 down to Z=80-ledge_h: Width = Overall (Ledge).
    # From Z=80-ledge_h down to Z=80-ledge_h-tab_h: Width = Tab (Narrow).
    # From Z=80-ledge_h-tab_h down to Z=80-ledge_h-tab_h-tab_h: Width = Tab?
    # "descends by slot_cutout_depth".
    # Let's assume the total depth is 55.
    # Ledge height 3.5. Tab height 6.0.
    # So:
    # Z=80 to 76.5: Width = 52.
    # Z=76.5 to 70.5: Width = 10.
    # Z=70.5 to 55.0: Width = 10.
    
    # This defines the shape on the XZ plane.
    # We will create a sketch on the XZ plane (at Y=0) to define the profile.
    # Then use a Revolve? No, it's a slot, so it's along Y.
    # So we need a sketch on the XZ plane, then a LinearPattern along Y?
    # Or just a sketch on the XY plane with a profile that extrudes along Z? No, it's a cut.
    # Let's do this:
    # Sketch on XZ plane (Profile).
    # Feature: Pad (additive) or Pocket (subtractive).
    # If we sketch on XZ, we can't easily extrude along Y unless we revolve or use a specific pattern.
    # Better: Sketch on XY plane (Top).
    # Draw the shape: A rectangle of width 52, length (along Y) = ?
    # Wait, if it runs along Y, the "profile" is on the XZ plane.
    # So we define the profile on the XZ plane, then use a "Pad" along the Y-axis?
    # PartDesign::Pad can extrude along
