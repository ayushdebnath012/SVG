import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Base Parameters
params_base = {
    "circuit_board_length": 80.00,
    "circuit_board_width": 36.00,
    "circuit_board_thickness": 2.00,
    "secondary_circuit_board_length": 71.00,
    "secondary_circuit_board_width": 27.00,
    "secondary_circuit_board_thickness": 7.00,
    "secondary_circuit_board_center_x": -0.50,
    "secondary_circuit_board_center_y": -1.00,
}

# Edit Parameters (Target)
params_edit = {
    "side_interface_center_offset": -1.00,
    "side_interface_outer_edge_inset": 0.50,
    "side_interface_inboard_length": 5.00,
    "side_interface_outer_height": 3.90,
    "side_interface_inner_height": 12.00,
    "side_interface_thickness": 2.00,
    "main_recess_length": 65.00,
    "main_recess_width": 14.00,
    "main_recess_depth": 1.00,
    "header_slot_length": 65.00,
    "header_slot_width": 1.00,
    "header_slot_depth": 1.00,
    "header_slot_center_offset": 10.00,
    "mounting_hole_diameter": 3.00,
    "mounting_hole_count": 4,
    "mounting_hole_edge_inset": 2.00,
    "right_hole_stagger": 0.50,
    "header_pin_count": 16,
    "header_pin_pitch": 2.54,
    "header_pin_diameter": 1.00,
    "header_pin_length": 9.50,
    "header_pin_start_offset": 8.00,
    "header_row_left_inset": 8.00,
    "header_row_edge_inset": 2.50,
    "upper_housing_end_radius": 0.90,
    "upper_housing_straight_height": 2.50,
    "upper_housing_thickness": 0.20,
    "lower_header_height": 2.00,
    "lower_header_corner_radius": 0.30,
}

def create_document(name):
    doc = App.newDocument(name)
    # Create standard planes
    doc.addObject("PartDesign::Plane", "XY_Plane")
    doc.addObject("PartDesign::Plane", "XZ_Plane")
    doc.addObject("PartDesign::Plane", "YZ_Plane")
    doc.addObject("PartDesign::Axis", "X_Axis")
    doc.addObject("PartDesign::Axis", "Y_Axis")
    doc.addObject("PartDesign::Axis", "Z_Axis")
    return doc

def build_base_part():
    doc = create_document("LCD_Module_Base")
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Parameters
    params = body.newObject("App::VarSet", "Parameters")
    for k, v in params_base.items():
        params.addProperty("App::PropertyLength", k, "Dimensions", k)
        params.setValue(k, v)

    # Base Sketch (Primary Board)
    sk1 = body.newObject("Sketcher::SketchObject", "BaseSketch")
    sk1.Placement = App.Placement(App.Vector(0, 0, 0))
    sk1.Constrain = True
    sk1.MapMode = "FlatFace"
    sk1.AttachmentSupport = (doc.getObject("XY_Plane"), [])
    
    # Rectangle
    sk1.addGeometry(Part.LineSegment(App.Vector(-params_base["circuit_board_length"]/2, -params_base["circuit_board_width"]/2, 0), 
                                     App.Vector(params_base["circuit_board_length"]/2, -params_base["circuit_board_width"]/2, 0)), False)
    sk1.addGeometry(Part.LineSegment(App.Vector(params_base["circuit_board_length"]/2, -params_base["circuit_board_width"]/2, 0), 
                                     App.Vector(params_base["circuit_board_length"]/2, params_base["circuit_board_width"]/2, 0)), False)
    sk1.addGeometry(Part.LineSegment(App.Vector(params_base["circuit_board_length"]/2, params_base["circuit_board_width"]/2, 0), 
                                     App.Vector(-params_base["circuit_board_length"]/2, params_base["circuit_board_width"]/2, 0)), False)
    sk1.addGeometry(Part.LineSegment(App.Vector(-params_base["circuit_board_length"]/2, params_base["circuit_board_width"]/2, 0), 
                                     App.Vector(-params_base["circuit_board_length"]/2, -params_base["circuit_board_width"]/2, 0)), False)
    
    # Constraints
    sk1.addConstraint(Sketcher.Constraint("Axis", 0, 1, "X_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Axis", 1, 2, "X_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Axis", 2, 3, "X_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Axis", 3, 0, "X_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Axis", 0, 1, "Y_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Axis", 1, 2, "Y_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Axis", 2, 3, "Y_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Axis", 3, 0, "Y_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Length", 0, 1, "Parameters.circuit_board_length"))
    sk1.addConstraint(Sketcher.Constraint("Length", 1, 2, "Parameters.circuit_board_width"))
    sk1.addConstraint(Sketcher.Constraint("Length", 2, 3, "Parameters.circuit_board_length"))
    sk1.addConstraint(Sketcher.Constraint("Length", 3, 0, "Parameters.circuit_board_width"))
    
    # Pad Primary Board
    pad1 = body.newObject("PartDesign::Pad", "PadPrimaryBoard")
    pad1.Profile = sk1
    pad1.Length = params_base["circuit_board_thickness"]
    pad1.Type = "Solid"
    pad1.Midplane = False
    pad1.Reversed = False

    # Secondary Board Sketch
    sk2 = body.newObject("Sketcher::SketchObject", "SecondarySketch")
    sk2.Placement = App.Placement(App.Vector(0, 0, params_base["circuit_board_thickness"]))
    sk2.MapMode = "FlatFace"
    sk2.AttachmentSupport = (doc.getObject("XY_Plane"), [])
    
    # Rectangle
    sk2.addGeometry(Part.LineSegment(App.Vector(-params_base["secondary_circuit_board_length"]/2, -params_base["secondary_circuit_board_width"]/2, 0), 
                                     App.Vector(params_base["secondary_circuit_board_length"]/2, -params_base["secondary_circuit_board_width"]/2, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(params_base["secondary_circuit_board_length"]/2, -params_base["secondary_circuit_board_width"]/2, 0), 
                                     App.Vector(params_base["secondary_circuit_board_length"]/2, params_base["secondary_circuit_board_width"]/2, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(params_base["secondary_circuit_board_length"]/2, params_base["secondary_circuit_board_width"]/2, 0), 
                                     App.Vector(-params_base["secondary_circuit_board_length"]/2, params_base["secondary_circuit_board_width"]/2, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(-params_base["secondary_circuit_board_length"]/2, params_base["secondary_circuit_board_width"]/2, 0), 
                                     App.Vector(-params_base["secondary_circuit_board_length"]/2, -params_base["secondary_circuit_board_width"]/2, 0)), False)
    
    # Constraints
    sk2.addConstraint(Sketcher.Constraint("Axis", 0, 1, "X_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Axis", 1, 2, "X_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Axis", 2, 3, "X_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Axis", 3, 0, "X_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Axis", 0, 1, "Y_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Axis", 1, 2, "Y_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Axis", 2, 3, "Y_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Axis", 3, 0, "Y_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Length", 0, 1, "Parameters.secondary_circuit_board_length"))
    sk2.addConstraint(Sketcher.Constraint("Length", 1, 2, "Parameters.secondary_circuit_board_width"))
    sk2.addConstraint(Sketcher.Constraint("Length", 2, 3, "Parameters.secondary_circuit_board_length"))
    sk2.addConstraint(Sketcher.Constraint("Length", 3, 0, "Parameters.secondary_circuit_board_width"))
    
    # Offset constraints for centering
    # Center X
    sk2.addConstraint(Sketcher.Constraint("PointOnObject", 0, 1, "Parameters.secondary_circuit_board_center_x", 0, 1)) # This is tricky in pure sketcher without points
    # Instead, we define the rectangle relative to the center of the primary board using a placement offset in the sketch creation or by constraining to a point.
    # Since we can't easily create a point object in the sketcher API easily for arbitrary offsets without clutter, 
    # we will use the Placement of the sketch to position the center of the rectangle.
    # The sketch geometry is centered at (0,0) in local coords. We need to shift the sketch origin.
    # Actually, the easiest way in PartDesign is to define the sketch at the correct location.
    # The sketch geometry is defined relative to the sketch's local origin.
    # We want the center of the rectangle to be at (sec_x, sec_y).
    # So we shift the sketch origin by (-sec_x, -sec_y).
    # But the sketch object's Placement moves the whole sketch.
    # Let's redefine the sketch geometry to be centered at the desired offset.
    
    # Re-defining sk2 geometry to be centered at the offset
    cx = params_base["secondary_circuit_board_center_x"]
    cy = params_base["secondary_circuit_board_center_y"]
    
    sk2.addGeometry(Part.LineSegment(App.Vector(-params_base["secondary_circuit_board_length"]/2 + cx, -params_base["secondary_circuit_board_width"]/2 + cy, 0), 
                                     App.Vector(params_base["secondary_circuit_board_length"]/2 + cx, -params_base["secondary_circuit_board_width"]/2 + cy, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(params_base["secondary_circuit_board_length"]/2 + cx, -params_base["secondary_circuit_board_width"]/2 + cy, 0), 
                                     App.Vector(params_base["secondary_circuit_board_length"]/2 + cx, params_base["secondary_circuit_board_width"]/2 + cy, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(params_base["secondary_circuit_board_length"]/2 + cx, params_base["secondary_circuit_board_width"]/2 + cy, 0), 
                                     App.Vector(-params_base["secondary_circuit_board_length"]/2 + cx, params_base["secondary_circuit_board_width"]/2 + cy, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(-params_base["secondary_circuit_board_length"]/2 + cx, params_base["secondary_circuit_board_width"]/2 + cy, 0), 
                                     App.Vector(-params_base["secondary_circuit_board_length"]/2 + cx, -params_base["secondary_circuit_board_width"]/2 + cy, 0)), False)
    
    # Re-constraints
    sk2.addConstraint(Sketcher.Constraint("Axis", 0, 1, "X_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Axis", 1, 2, "X_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Axis", 2, 3, "X_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Axis", 3, 0, "X_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Axis", 0, 1, "Y_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Axis", 1, 2, "Y_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Axis", 2, 3, "Y_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Axis", 3, 0, "Y_Axis"))
    sk2.addConstraint(Sketcher.Constraint("Length", 0, 1, "Parameters.secondary_circuit_board_length"))
    sk2.addConstraint(Sketcher.Constraint("Length", 1, 2, "Parameters.secondary_circuit_board_width"))
    sk2.addConstraint(Sketcher.Constraint("Length", 2, 3, "Parameters.secondary_circuit_board_length"))
    sk2.addConstraint(Sketcher.Constraint("Length", 3, 0, "Parameters.secondary_circuit_board_width"))
    
    # Pad Secondary Board
    pad2 = body.newObject("PartDesign::Pad", "PadSecondaryBoard")
    pad2.Profile = sk2
    pad2.Length = params_base["secondary_circuit_board_thickness"]
    pad2.Type = "Solid"
    pad2.Midplane = False
    pad2.Reversed = False

    doc.recompute()
    return doc

def build_edit_part(base_doc):
    doc = App.newDocument("LCD_Module_Edit")
    # Copy objects from base to edit doc to preserve structure but allow modification
    # We need to recreate the body and features to ensure they are editable in the new doc
    # and to apply the new parameters.
    
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Parameters
    params = body.newObject("App::VarSet", "Parameters")
    # Copy base params
    for k, v in params_base.items():
        params.addProperty("App::PropertyLength", k, "Dimensions", k)
        params.setValue(k, v)
    # Add edit params
    for k, v in params_edit.items():
        params.addProperty("App::PropertyLength", k, "Dimensions", k)
        params.setValue(k, v)

    # 1. Primary Board
    sk1 = body.newObject("Sketcher::SketchObject", "BaseSketch")
    sk1.Placement = App.Placement(App.Vector(0, 0, 0))
    sk1.MapMode = "FlatFace"
    sk1.AttachmentSupport = (doc.getObject("XY_Plane"), [])
    
    l = params_base["circuit_board_length"]
    w = params_base["circuit_board_width"]
    sk1.addGeometry(Part.LineSegment(App.Vector(-l/2, -w/2, 0), App.Vector(l/2, -w/2, 0)), False)
    sk1.addGeometry(Part.LineSegment(App.Vector(l/2, -w/2, 0), App.Vector(l/2, w/2, 0)), False)
    sk1.addGeometry(Part.LineSegment(App.Vector(l/2, w/2, 0), App.Vector(-l/2, w/2, 0)), False)
    sk1.addGeometry(Part.LineSegment(App.Vector(-l/2, w/2, 0), App.Vector(-l/2, -w/2, 0)), False)
    
    sk1.addConstraint(Sketcher.Constraint("Axis", 0, 1, "X_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Axis", 1, 2, "X_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Axis", 2, 3, "X_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Axis", 3, 0, "X_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Axis", 0, 1, "Y_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Axis", 1, 2, "Y_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Axis", 2, 3, "Y_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Axis", 3, 0, "Y_Axis"))
    sk1.addConstraint(Sketcher.Constraint("Length", 0, 1, "Parameters.circuit_board_length"))
    sk1.addConstraint(Sketcher.Constraint("Length", 1, 2, "Parameters.circuit_board_width"))
    sk1.addConstraint(Sketcher.Constraint("Length", 2, 3, "Parameters.circuit_board_length"))
    sk1.addConstraint(Sketcher.Constraint("Length", 3, 0, "Parameters.circuit_board_width"))
    
    pad1 = body.newObject("PartDesign::Pad", "PadPrimaryBoard")
    pad1.Profile = sk1
    pad1.Length = params_base["circuit_board_thickness"]
    pad1.Type = "Solid"
    pad1.Midplane = False
    pad1.Reversed = False

    # 2. Secondary Board
    sk2 = body.newObject("Sketcher::SketchObject", "Secondary
