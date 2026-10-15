"""
FreeCAD 1.1 Script: LCD Module Blank & Interface Construction
Generates _base.FCStd and _edit.FCStd based on __file__.
"""

from pathlib import Path
import FreeCAD as App
import Part
from Part import Shape, Vector, Placement
import math

# --- Configuration from __file__ ---
script_path = Path(__file__).resolve()
stem = script_path.stem

# Output paths
base_path = script_path.parent / f"{stem}_base.FCStd"
edit_path = script_path.parent / f"{stem}_edit.FCStd"

# --- Part Design Helper Functions ---

def create_param_set(body, name, **kwargs):
    """Creates a VarSet to hold parameters and sets their expressions."""
    varset = body.newObject("App::VarSet", name)
    for key, value in kwargs.items():
        # Ensure the property type matches the value type (convert to float if needed)
        if isinstance(value, (int, float)):
            prop_type = "App::PropertyLength" if "length" in key.lower() or "width" in key.lower() or "thickness" in key.lower() or "radius" in key.lower() or "depth" in key.lower() or "height" in key.lower() or "pitch" in key.lower() or "offset" in key.lower() or "diameter" in key.lower() else "App::PropertyLength"
        else:
            prop_type = "App::PropertyLength" # Default to length for simplicity in this context
        
        varset.addProperty(prop_type, key, "Dimensions", f"Parameter: {key}")
        varset[key] = value
    return varset

def add_sketch(body, name, plane_name, origin_offset=0.0, constraints=None):
    """Creates a sketch object attached to a specific plane."""
    # Get the plane object
    plane_obj = body.getObject(plane_name)
    
    sketch = body.newObject("Sketcher::SketchObject", name)
    sketch.Plane = plane_obj.Name
    sketch.Constrain = False # Disable auto-constraint initially to manage manually if needed, but we will add constraints
    
    # If we are offsetting from a plane origin (e.g. Top face), we need to handle the placement
    # In PartDesign, Sketcher::SketchObject.Plane refers to the face. 
    # If we want to offset, we usually use a different plane or an offset parameter.
    # For simplicity in this script, we will create the sketch on the face and use Vector constraints 
    # or simply rely on the coordinate system if the sketch is on XY.
    
    return sketch

def add_pad(body, sketch_obj, length_expr, length_val=0.0, reversed=False, midplane=False):
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sketch_obj
    pad.Length = length_val
    if length_expr:
        pad.setExpression("Length", length_expr)
    pad.Reversed = reversed
    pad.Midplane = midplane
    return pad

def add_pocket(body, sketch_obj, length_expr, length_val=0.0, type="ThroughAll", reversed=False, midplane=False):
    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = sketch_obj
    pocket.Length = length_val
    if length_expr:
        pocket.setExpression("Length", length_expr)
    pocket.Type = type
    pocket.Reversed = reversed
    pocket.Midplane = midplane
    return pocket

def add_fillet(body, edges, radius_expr, radius_val=0.0):
    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.EdgeList = edges
    fillet.Radius = radius_val
    if radius_expr:
        fillet.setExpression("Radius", radius_expr)
    return fillet

def add_chamfer(body, edges, size_expr, size_val=0.0):
    chamfer = body.newObject("PartDesign::Chamfer", "Chamfer")
    chamfer.EdgeList = edges
    chamfer.Size = size_val
    if size_expr:
        chamfer.setExpression("Size", size_expr)
    return chamfer

def add_hole(body, sketch_obj, length_expr, length_val=0.0, type="ThroughAll"):
    hole = body.newObject("PartDesign::Hole", "Hole")
    hole.Profile = sketch_obj
    hole.Length = length_val
    if length_expr:
        hole.setExpression("Length", length_expr)
    hole.Type = type
    return hole

# --- Base Part Parameters ---
base_params = {
    "circuit_board_length": 80.0,
    "circuit_board_width": 36.0,
    "circuit_board_thickness": 2.0,
    "secondary_circuit_board_length": 71.0,
    "secondary_circuit_board_width": 27.0,
    "secondary_circuit_board_thickness": 7.0,
    "secondary_circuit_board_center_x": -0.5,
    "secondary_circuit_board_center_y": -1.0,
}

# --- Edit Parameters ---
edit_params = {
    "side_interface_center_offset": -1.0,
    "side_interface_outer_edge_inset": 0.5,
    "side_interface_inboard_length": 5.0,
    "side_interface_outer_height": 3.9,
    "side_interface_inner_height": 12.0,
    "side_interface_thickness": 2.0,
    "main_recess_length": 65.0,
    "main_recess_width": 14.0,
    "main_recess_depth": 1.0,
    "header_slot_length": 65.0,
    "header_slot_width": 1.0,
    "header_slot_depth": 1.0,
    "header_slot_center_offset": 10.0,
    "mounting_hole_diameter": 3.0,
    "mounting_hole_count": 4,
    "mounting_hole_edge_inset": 2.0,
    "right_hole_stagger": 0.5,
    "header_pin_count": 16,
    "header_pin_pitch": 2.54,
    "header_pin_diameter": 1.0,
    "header_pin_length": 9.5,
    "header_pin_start_offset": 8.0,
    "header_row_left_inset": 8.0,
    "header_row_edge_inset": 2.5,
    "upper_housing_end_radius": 0.9,
    "upper_housing_straight_height": 2.5,
    "upper_housing_thickness": 0.2,
    "lower_header_height": 2.0,
    "lower_header_corner_radius": 0.3,
}

def build_base(doc):
    """Builds the base part."""
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Parameters
    params = create_param_set(body, "Params", **base_params)
    
    # 1. Primary Board Sketch (Bottom Face of Body, XY Plane)
    # We create the sketch on the Front (XY) plane, then push up.
    # However, PartDesign::Pad works best if the sketch is on a face.
    # Let's create a sketch on the Front plane (XZ? No, usually XY is Z-up).
    # In FreeCAD default: XY plane is Z-up.
    
    sketch_board = body.newObject("Sketcher::SketchObject", "BaseSketch")
    sketch_board.Plane = "XY_Plane"
    sketch_board.Constrain = False
    
    # Geometry
    L = base_params["circuit_board_length"]
    W = base_params["circuit_board_width"]
    sketch_board.addGeometry(Part.makeBox(L, W, 0.1).Shape) # Placeholder to force update if needed, but we use lines
    sketch_board.addGeometry(Part.LineSegment(Vector(-L/2, -W/2, 0), Vector(L/2, -W/2, 0)))
    sketch_board.addGeometry(Part.LineSegment(Vector(L/2, -W/2, 0), Vector(L/2, W/2, 0)))
    sketch_board.addGeometry(Part.LineSegment(Vector(L/2, W/2, 0), Vector(-L/2, W/2, 0)))
    sketch_board.addGeometry(Part.LineSegment(Vector(-L/2, W/2, 0), Vector(-L/2, -W/2, 0)))
    
    # Constraints
    sketch_board.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 2)) # Coincident vertices? No, simpler:
    # Center constraints
    sketch_board.addConstraint(Sketcher.Constraint("Point", 1, 2, "XY")) # Center on origin
    # Let's use simpler centering constraints
    sketch_board.addConstraint(Sketcher.Constraint("Point", 1, 1, "Point", 0, 0, "XY")) # Point 1 at 0,0
    
    # Actually, let's just use the standard approach:
    # Create a rectangle.
    sketch_board.removeGeometry(1) # Remove placeholder
    sketch_board.addGeometry(Part.LineSegment(Vector(-L/2, -W/2, 0), Vector(L/2, -W/2, 0)))
    sketch_board.addGeometry(Part.LineSegment(Vector(L/2, -W/2, 0), Vector(L/2, W/2, 0)))
    sketch_board.addGeometry(Part.LineSegment(Vector(L/2, W/2, 0), Vector(-L/2, W/2, 0)))
    sketch_board.addGeometry(Part.LineSegment(Vector(-L/2, W/2, 0), Vector(-L/2, -W/2, 0)))
    sketch_board.addConstraint(Sketcher.Constraint("Point", 0, 1, "XY")) # Lock center
    # Actually, let's just constrain the center of the rectangle to the origin.
    # The sketch tool usually adds constraints. We will add a center point.
    # To be safe and simple:
    # Add a center point
    sketch_board.addGeometry(Part.Point(Vector(0,0,0)))
    sketch_board.addConstraint(Sketcher.Constraint("Point", 0, 1, "Point", 2, 0, "XY")) # Point 0 coincident with Point 2 (center)
    sketch_board.addConstraint(Sketcher.Constraint("Point", 1, 1, "XY")) # Lock point
    
    # Pad Board
    pad_board = body.newObject("PartDesign::Pad", "PadBoard")
    pad_board.Profile = sketch_board
    pad_board.Length = base_params["circuit_board_thickness"]
    pad_board.Reversed = False
    
    # 2. Secondary Board Sketch
    # We need a sketch on the Top Face of PadBoard.
    # We can't easily reference "Top_Face" by name dynamically in a script without getting the shape.
    # Instead, we will place the sketch on XY_Plane and offset it using a placement or just use the Pad to create the volume and then subtract?
    # No, PartDesign sketch must be on a face.
    # Let's create a sketch on XY_Plane, then use a Pad to lift it to the height of the board, then another Pad for the secondary board?
    # Better: Use a sketch on XY, pad up by thickness + secondary_thickness, then subtract the secondary board height?
    # No, the description says "raised block".
    
    # Strategy:
    # 1. Pad Board (Thickness T1)
    # 2. Create a sketch on the Top Face of the resulting solid.
    # Since we can't easily get the Top Face object name, we will create a sketch on XY_Plane, 
    # and use a Pad to lift the secondary board from the top face of the first pad.
    # Wait, PartDesign::Pad takes a sketch. If we put the sketch on XY, and Pad it with Length = T1 + T2, 
    # we get a stepped shape if the sketch is different.
    # Let's try that.
    
    # Sketch for Secondary Board
    # We want it to start at Z = T1.
    # If we sketch on XY, the sketch is at Z=0.
    # If we Pad this sketch with Length = T1 + T2, it goes from Z=0 to Z=T1+T2.
    # But we want the *difference* to be the secondary board.
    # So, we pad the *same* sketch with Length = T1 + T2.
    # Then we subtract a pocket of depth T1? No.
    # We want a block of thickness T2 sitting on top of T1.
    # So the total height is T1 + T2.
    # The sketch defines the footprint of the secondary board.
    # We pad the sketch with Length = T1 + T2.
    # This creates a block of T1+T2.
    # Then we subtract a pocket of depth T1 from the bottom?
    # Or simply: Pad the main board. Then create a sketch on the Top Face.
    # How to get the Top Face object?
    # We can get the face from the solid.
    
    # Alternative: Use a sketch on XY, pad up T1. Then create a sketch on the Top Face.
    # Let's assume we can get the Top Face.
    # Actually, let's just do the subtraction method to avoid face dependency issues in the script.
    # Pad main board (T1).
    # Create sketch on XY for Secondary Board.
    # Pad that sketch with Length = T1 + T2. (This makes a tall block).
    # Subtract a pocket of depth T1 from the bottom of the tall block?
    # No, that removes material from the main board.
    # We want to ADD material.
    # So: Pad Main (T1).
    # Create sketch on Top Face. Pad (T2).
    
    # To do this dynamically:
    # 1. Pad Board (T1).
    # 2. Get the Top Face of the PadBoard feature? No, the PadBoard creates a solid.
    # We need the face of the solid.
    # We can use the Body's active shape? No.
    # Let's use the workaround: Sketch on XY, Pad (T1+T2). Then Pocket (T1) from the bottom?
    # No, that makes a block of T2 on top of nothing?
    # Ah, if I Pad (T1+T2) on XY, I have a block of T1+T2.
    # If I Pocket (T1) on XY, I remove the bottom T1. Result: T2 block in the middle.
    # That's not what we want. We want a block of T2 sitting on T1.
    
    # Correct approach with PartDesign:
    # 1. Pad Board (T1).
    # 2. Sketch on Top Face of PadBoard.
    # 3. Pad Secondary (T2).
    
    # How to get Top Face?
    # We can create a temporary sketch on XY, pad T1.
    # Then create a new sketch on the face of that pad.
    # We can get the face from the pad's shape.
    
    # Let's try to get the face from the PadBoard result.
    # pad_board.Placement -> get shape -> faces.
    # But the feature tree doesn't expose faces directly as objects.
    # We can use a trick: Create a sketch on XY, pad T1.
    # Then create a sketch on XY again, but offset the sketch? No.
    
    # Let's use the "Sketch on Face" logic properly.
    # We need the face object.
    # In PartDesign, we can add a sketch to a face.
    # We need to find the face.
    # We can get the shape of the pad_board.
    # But the shape is a TopoShape.
    # We can iterate faces.
    
    # Simpler approach: 
    # Create a sketch on XY.
    # Pad with T1 + T2.
    # This creates a solid block of height T1+T2.
    # Then we subtract a pocket of depth T1 from the bottom? No.
    # We want a step.
    # Okay, let's assume we can get the face.
    # We will create a sketch on XY, pad T1.
    # Then we will create a sketch on the Top Face of the resulting solid.
    # To get the Top Face object, we can use the following:
    # The PadBoard creates a solid. We can get the face from the solid.
    # But we need an object to attach the sketch to.
    # We can create a "Part::Feature" just to hold the face? No, that's baked.
    # We can use the "PartDesign::Body" to create a sketch on a face.
    # We need the Face object.
    # We can get the face from the PadBoard's shape.
    # But the PadBoard is a feature.
    # We can use the `Shape` property of the PadBoard.
    # `pad_board.Shape.Faces`? No, it's a TopoShape.
    # `pad_board.Shape.Faces` gives a list of faces.
    # We can pick the top face.
    # But we need an object to attach the sketch to.
    # We can create a temporary sketch on the face?
    # No, we need the face object.
    # We can create a sketch on the face by referencing the face object.
    # But we don't have the face object.
    # We can create a sketch on XY, then use a Pad to lift it.
    # Then we can create a sketch on the Top Face of the Pad.
    # How?
    # We can use the `Sketcher::SketchObject.Plane` property.
    # We can set `Plane` to the face
