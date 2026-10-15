import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

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
    
    sec_l = params_base["secondary_circuit_board_length"]
    sec_w = params_base["secondary_circuit_board_width"]
    sec_cx = params_base["secondary_circuit_board_center_x"]
    sec_cy = params_base["secondary_circuit_board_center_y"]
    
    sk2.addGeometry(Part.LineSegment(App.Vector(-sec_l/2 + sec_cx, -sec_w/2 + sec_cy, 0), 
                                     App.Vector(sec_l/2 + sec_cx, -sec_w/2 + sec_cy, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(sec_l/2 + sec_cx, -sec_w/2 + sec_cy, 0), 
                                     App.Vector(sec_l/2 + sec_cx, sec_w/2 + sec_cy, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(sec_l/2 + sec_cx, sec_w/2 + sec_cy, 0), 
                                     App.Vector(-sec_l/2 + sec_cx, sec_w/2 + sec_cy, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(-sec_l/2 + sec_cx, sec_w/2 + sec_cy, 0), 
                                     App.Vector(-sec_l/2 + sec_cx, -sec_w/2 + sec_cy, 0)), False)
    
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
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Parameters
    params = body.newObject("App::VarSet", "Parameters")
    for k, v in params_base.items():
        params.addProperty("App::PropertyLength", k, "Dimensions", k)
        params.setValue(k, v)
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
    sk2 = body.newObject("Sketcher::SketchObject", "SecondarySketch")
    sk2.Placement = App.Placement(App.Vector(0, 0, params_base["circuit_board_thickness"]))
    sk2.MapMode = "FlatFace"
    sk2.AttachmentSupport = (doc.getObject("XY_Plane"), [])
    
    sec_l = params_base["secondary_circuit_board_length"]
    sec_w = params_base["secondary_circuit_board_width"]
    sec_cx = params_base["secondary_circuit_board_center_x"]
    sec_cy = params_base["secondary_circuit_board_center_y"]
    
    sk2.addGeometry(Part.LineSegment(App.Vector(-sec_l/2 + sec_cx, -sec_w/2 + sec_cy, 0), 
                                     App.Vector(sec_l/2 + sec_cx, -sec_w/2 + sec_cy, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(sec_l/2 + sec_cx, -sec_w/2 + sec_cy, 0), 
                                     App.Vector(sec_l/2 + sec_cx, sec_w/2 + sec_cy, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(sec_l/2 + sec_cx, sec_w/2 + sec_cy, 0), 
                                     App.Vector(-sec_l/2 + sec_cx, sec_w/2 + sec_cy, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(-sec_l/2 + sec_cx, sec_w/2 + sec_cy, 0), 
                                     App.Vector(-sec_l/2 + sec_cx, -sec_w/2 + sec_cy, 0)), False)
    
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
    
    pad2 = body.newObject("PartDesign::Pad", "PadSecondaryBoard")
    pad2.Profile = sk2
    pad2.Length = params_base["secondary_circuit_board_thickness"]
    pad2.Type = "Solid"
    pad2.Midplane = False
    pad2.Reversed = False

    # 3. Side Interface (Tapered Wedge)
    # Outer edge inset from right board edge
    # Inboard edge inset from right board edge
    # Centered at side_interface_center_offset (transverse Y)
    # Height: outer_height to inner_height
    # Thickness: side_interface_thickness
    
    right_edge_x = l / 2
    outer_inset = params_edit["side_interface_outer_edge_inset"]
    inboard_len = params_edit["side_interface_inboard_length"]
    center_y = params_edit["side_interface_center_offset"]
    outer_h = params_edit["side_interface_outer_height"]
    inner_h = params_edit["side_interface_inner_height"]
    iface_thick = params_edit["side_interface_thickness"]
    
    # Define the profile for the wedge
    # Points: (x, y, z)
    # Outer edge (lower z): (right_edge_x - outer_inset, center_y, 0) to (right_edge_x - outer_inset - inboard_len, center_y, 0)
    # Inner edge (higher z): (right_edge_x - outer_inset, center_y, outer_h) to (right_edge_x - outer_inset - inboard_len, center_y, inner_h)
    # Wait, the description says "widens from side_interface_outer_height at its outer edge to side_interface_inner_height at its inboard edge".
    # This implies the height changes along the length of the interface.
    # Let's define the profile in the XZ plane (sketch on XZ plane, extruded along Y? No, usually sketch on XY, extruded Z).
    # The interface is a solid block. Let's sketch the cross-section in the XZ plane (Y=0) and extrude along Y.
    # But the center is offset in Y. So we sketch on a plane at Y = center_y.
    
    sk3 = body.newObject("Sketcher::SketchObject", "InterfaceSketch")
    # Attach to XZ plane at Y = center_y
    # We need to create a plane or use the existing XZ plane and offset the sketch.
    # FreeCAD Sketcher::SketchObject can be attached to a plane with an offset.
    # However, the standard planes are at Y=0. We can use the XZ plane and set AttachmentOffset.
    sk3.Placement = App.Placement(App.Vector(0, center_y, 0))
    sk3.MapMode = "FlatFace"
    sk3.AttachmentSupport = (doc.getObject("XZ_Plane"), [])
    
    # Profile points in local sketch coords (X, Z)
    # Outer edge (right side of interface): x = right_edge_x - outer_inset
    # Inboard edge (left side of interface): x = right_edge_x - outer_inset - inboard_len
    # Height at outer edge: outer_h
    # Height at inboard edge: inner_h
    
    p1 = App.Vector(right_edge_x - outer_inset, 0) # Local X, Z
    p2 = App.Vector(right_edge_x - outer_inset - inboard_len, 0)
    p3 = App.Vector(right_edge_x - outer_inset - inboard_len, inner_h)
    p4 = App.Vector(right_edge_x - outer_inset, outer_h)
    
    sk3.addGeometry(Part.LineSegment(p1, p2), False)
    sk3.addGeometry(Part.LineSegment(p2, p3), False)
    sk3.addGeometry(Part.LineSegment(p3, p4), False)
    sk3.addGeometry(Part.LineSegment(p4, p1), False)
    
    sk3.addConstraint(Sketcher.Constraint("Axis", 0, 1, "X_Axis"))
    sk3.addConstraint(Sketcher.Constraint("Axis", 1, 2, "X_Axis"))
    sk3.addConstraint(Sketcher.Constraint("Axis", 2, 3, "X_Axis"))
    sk3.addConstraint(Sketcher.Constraint("Axis", 3, 0, "X_Axis"))
    # We don't need explicit length constraints if we define the geometry directly, 
    # but let's add them for clarity if possible. Since we used absolute values, constraints might conflict or be redundant.
    # We'll rely on the geometry definition.
    
    # Extrude along Y (which is the normal of XZ plane)
    # The sketch is on XZ plane. Normal is Y.
    # We need to extrude by 'iface_thick' in Y direction.
    # But the sketch is centered at Y=center_y. The extrusion will be along Y.
    # The direction is positive Y (since we want it on the right side, and Y is transverse).
    # Wait, the board is along X. Y is transverse.
    # The interface is at the right edge (positive X). It extends inwards (negative X).
    # It is centered at Y = center_y.
    # So we extrude along Y.
    
    iface_pad = body.newObject("PartDesign::Pad", "PadInterface")
    iface_pad.Profile = sk3
    iface_pad.Length = iface_thick
    iface_pad.Type = "Solid"
    iface_pad.Midplane = False
    iface_pad.Reversed = False

    # 4. Main Recess (Blind)
    # Centered on secondary board's upper face.
    # Secondary board top is at Z = circuit_board_thickness + secondary_circuit_board_thickness
    # Recess goes down by main_recess_depth.
    
    sk4 = body.newObject("Sketcher::SketchObject", "RecessSketch")
    sk4.Placement = App.Placement(App.Vector(0, 0, params_base["circuit_board_thickness"] + params_base["secondary_circuit_board_thickness"]))
    sk4.MapMode = "FlatFace"
    sk4.AttachmentSupport = (doc.getObject("XY_Plane"), [])
    
    rec_l = params_edit["main_recess_length"]
    rec_w = params_edit["main_recess_width"]
    
    sk4.addGeometry(Part.LineSegment(App.Vector(-rec_l/2, -rec_w/2, 0), App.Vector(rec_l/2, -rec_w/2, 0)), False)
    sk4.addGeometry(Part.LineSegment(App.Vector(rec_l/2, -rec_w/2, 0), App.Vector(rec_l/2, rec_w/2, 0)), False)
    sk4.addGeometry(Part.LineSegment(App.Vector(rec_l/2, rec_w/2, 0), App.Vector(-rec_l/2, rec_w/2, 0)), False)
    sk4.addGeometry(Part.LineSegment(App.Vector(-rec_l/2, rec_w/2, 0), App.Vector(-rec_l/2, -rec_w/2, 0)), False)
    
    sk4.addConstraint(Sketcher.Constraint("Axis", 0, 1, "X_Axis"))
    sk4.addConstraint(Sketcher.Constraint("Axis", 1, 2, "X_Axis"))
    sk4.addConstraint(Sketcher.Constraint("Axis", 2, 3, "X_Axis"))
    sk4.addConstraint(Sketcher.Constraint("Axis", 3, 0, "X_Axis"))
    sk4.addConstraint(Sketcher.Constraint("Axis", 0, 1, "Y_Axis"))
    sk4.addConstraint(Sketcher.Constraint("Axis", 1, 2, "Y_Axis"))
    sk4.addConstraint(Sketcher.Constraint("Axis", 2, 3, "Y_Axis"))
    sk4.addConstraint(Sketcher.Constraint("Axis", 3, 0, "Y_Axis"))
    sk4.addConstraint(Sketcher.Constraint("Length", 0, 1, "Parameters.main_recess_length"))
    sk4.addConstraint(Sketcher.Constraint("Length", 1, 2, "Parameters.main_recess_width"))
    sk4.addConstraint(Sketcher.Constraint("Length", 2, 3, "Parameters.main_recess_length"))
    sk4.addConstraint(Sketcher.Constraint("Length", 3, 0, "Parameters.main_recess_width"))
    
    recess = body.newObject("PartDesign::Pocket", "PocketMainRecess")
    recess.Profile = sk4
    recess.Length = params_edit["main_recess_depth"]
    recess.Type = "Blind"
    recess.Midplane = False
    recess.Reversed = True # Remove material downwards

    # 5. Header Slots
    # Two rectangular slots, parallel to longitudinal (X).
    # Centers symmetrically spaced from secondary-board center by header_slot_center_offset along transverse (Y).
    # Length, width, depth.
    
    slot_l = params_edit["header_slot_length"]
    slot_w = params_edit["header_slot_width"]
    slot_d = params_edit["header_slot_depth"]
    slot_cy = params_edit["header_slot_center_offset"]
    
    # Slot 1 (Upper, positive Y)
    sk5 = body.newObject("Sketcher::SketchObject", "SlotSketch1")
    sk5.Placement = App.Placement(App.Vector(0, slot_cy, params_base["circuit_board_thickness"] + params_base["secondary_circuit_board_thickness"]))
    sk5.MapMode = "FlatFace"
    sk5.AttachmentSupport = (doc.getObject("XY_Plane"), [])
    
    sk5.addGeometry(Part.LineSegment(App.Vector(-slot_l/2, -slot_w/2, 0), App.Vector(slot_l/2, -slot_w/2, 0)), False)
    sk5.addGeometry(Part.LineSegment(App.Vector(slot_l/2, -slot_w/2, 0), App.Vector(slot_l/2, slot_w/2, 0)), False)
    sk5.addGeometry(Part.LineSegment(App.Vector(slot_l/2, slot_w/2, 0), App.Vector(-slot_l/2, slot_w/2, 0)), False)
    sk5.addGeometry(Part.LineSegment(App.Vector(-slot_l/2, slot_w/2, 0), App.Vector(-slot_l/2, -slot_w/2, 0)), False)
    
    sk5.addConstraint(Sketcher.Constraint("Axis", 0, 1, "X_Axis"))
    sk5.addConstraint(Sketcher.Constraint("Axis", 1, 2, "X_Axis"))
    sk5.addConstraint(Sketcher.Constraint("Axis", 2, 3, "X_Axis"))
    sk5.addConstraint(Sketcher.Constraint("Axis", 3, 0, "X_Axis"))
    sk5.addConstraint(Sketcher.Constraint("Axis", 0, 1, "Y_Axis"))
    sk5.addConstraint(Sketcher.Constraint("Axis", 1, 2, "Y_Axis"))
    sk5.addConstraint(Sketcher.Constraint("Axis", 2, 3, "Y_Axis"))
    sk5.addConstraint(Sketcher.Constraint("Axis", 3, 0, "Y_Axis"))
    sk5.addConstraint(Sketcher.Constraint("Length", 0, 1, "Parameters.header_slot_length"))
    sk5.addConstraint(Sketcher.Constraint("Length", 1, 2, "Parameters.header_slot_width"))
    sk5.addConstraint(Sketcher.Constraint("Length", 2, 3, "Parameters.header_slot_length"))
    sk5.addConstraint(Sketcher.Constraint("Length", 3, 0, "Parameters.header_slot_width"))
    
    slot1 = body.newObject("PartDesign::Pocket", "PocketSlot1")
    slot1.Profile = sk5
    slot1.Length = params_edit["header_slot_depth"]
    slot1.Type = "Blind"
    slot1.Midplane = False
    slot1.Reversed = True
    
    # Slot 2 (Lower, negative Y)
    sk6 = body.newObject("Sketcher::SketchObject", "SlotSketch2")
    sk6.Placement = App.Placement(App.Vector(0, -slot_cy, params_base["circuit_board_thickness"] + params_base["secondary_circuit_board_thickness"]))
    sk6.MapMode = "FlatFace"
    sk6.AttachmentSupport = (doc.getObject("XY_Plane"), [])
    
    sk6.addGeometry(Part.LineSegment(App.Vector(-slot_l/2, -slot_w/2, 0), App.Vector(slot_l/2, -slot_w/2, 0)), False)
    sk6.addGeometry(Part.LineSegment(App.Vector(slot_l/2, -slot_w/2, 0), App.Vector(slot_l/2, slot_w/2, 0)), False)
    sk6.addGeometry(Part.LineSegment(App.Vector(slot_l/2, slot_w/2, 0), App.Vector(-slot_l/2, slot_w/2, 0)), False)
    sk6.addGeometry(Part.LineSegment(App.Vector(-slot_l/2, slot_w/2, 0), App.Vector(-slot_l/2, -slot_w/2, 0)), False)
    
    sk6.addConstraint(Sketcher.Constraint("Axis", 0, 1, "X_Axis"))
    sk6.addConstraint(Sketcher.Constraint("Axis", 1, 2, "X_Axis"))
    sk6.addConstraint(Sketcher.Constraint("Axis", 2, 3, "X_Axis"))
    sk6.addConstraint(Sketcher.Constraint("Axis", 3, 0, "X_Axis"))
    sk6.addConstraint(Sketcher.Constraint("Axis", 0, 1, "Y_Axis"))
    sk6.addConstraint(Sketcher.Constraint("Axis", 1, 2, "Y_Axis"))
    sk6.addConstraint(Sketcher.Constraint("Axis", 2, 3, "Y_Axis"))
    sk6.addConstraint(Sketcher.Constraint("Axis", 3, 0, "Y_Axis"))
    sk6.addConstraint(Sketcher.Constraint("Length", 0, 1, "Parameters.header_slot_length"))
    sk6.addConstraint(Sketcher.Constraint("Length", 1, 2, "Parameters.header_slot_width"))
    sk6.addConstraint(Sketcher.Constraint("Length", 2, 3, "Parameters.header_slot_length"))
    sk6.addConstraint(Sketcher.Constraint("Length", 3, 0, "Parameters.header_slot_width"))
    
    slot2 = body.newObject("PartDesign::Pocket", "PocketSlot2")
    slot2.Profile = sk6
    slot2.Length = params_edit["header_slot_depth"]
    slot2.Type = "Blind"
    slot2.Midplane = False
    slot2.Reversed = True

    # 6. Mounting Holes
    # 4 holes. Nominal setback from each adjacent board edge is mounting_hole_edge_inset.
    # Upper-right hole: right-edge setback increased by right_hole_stagger.
    # Lower-right hole: lower-edge setback increased by right_hole_stagger.
    # "Lower-right" likely means the hole at the bottom right (positive X, negative Y).
    # "Upper-right" likely means the hole at the top right (positive X, positive Y).
    # Wait, "lower-right hole has its lower-edge setback increased". This phrasing is ambiguous.
    # Usually, holes are defined by their center.
    # Let's assume a 2x2 grid.
    # Standard inset: hole_edge_inset from all edges.
    # Hole 1 (Top-Right): Right edge setback += stagger.
    # Hole 2 (Bottom-Right): Lower edge setback += stagger.
    # This implies the holes are not in a perfect grid.
    
    # Let's define the 4 positions.
    # Board edges: X = +/- l/2, Y = +/- w/2.
    # Standard inset: x = +/- (l/2 - inset), y = +/- (w/2 - inset).
    # Hole 1 (Top-Right): x = l/2 - inset + stagger, y = w/2 - inset.
    # Hole 2 (Bottom-Right): x = l/2 - inset, y = w/2 - inset - stagger.
    # Hole 3 (Top-Left): x = -l/2 + inset, y = w/2 - inset.
    # Hole 4 (Bottom-Left): x = -l/2 + inset, y = -w/2 + inset.
    
    # Wait, "lower-right hole has its lower-edge setback increased".
    # If the hole is at the bottom right, its "lower edge" is the bottom of the hole.
    # Increasing the setback from the lower board edge means moving the hole further down (more negative Y).
    # So y = -(w/2 - inset - stagger) = -w/2 + inset + stagger.
    # Similarly for the top-right hole, "right-edge setback increased" means moving further right (more positive X).
    # x = l/2 - inset + stagger.
    
    # Let's re-read carefully: "The upper-right hole has its right-edge setback increased by right_hole_stagger"
    # "The lower-right hole has its lower-edge setback increased by right_hole_stagger"
    # This suggests only the right-side holes are staggered.
    
    # Let's define the 4 holes.
    # Hole 1 (Top-Right): x = l/2 - inset + stagger, y = w/2 - inset
    # Hole 2 (Bottom-Right): x = l/2 - inset, y = -w/2 + inset + stagger
    # Hole 3 (Top-Left): x = -l/2 + inset, y = w/2 - inset
    # Hole 4 (Bottom-Left): x = -l/2 + inset, y = -w/2 + inset
    
    # Wait, the description says "Four circular mounting holes pass completely through the assembly."
    # "The nominal setback from each adjacent board edge is mounting_hole_edge_inset."
    # This implies a standard grid first.
    # Then modifications.
    
    # Let's create 4 sketches for the holes.
    hole_dia = params_edit["mounting_hole_diameter"]
    hole_count = params_edit["mounting_hole_count"]
    hole_inset = params_edit["mounting_hole_edge_inset"]
    stagger = params_edit["right_hole_stagger"]
    
    # Hole 1: Top-Right (Staggered X)
    sk_h1 = body.newObject("Sketcher::SketchObject", "HoleSketch1")
    sk_h1.Placement = App.Placement(App.Vector(0, 0, params_base["circuit_board_thickness"] + params_base["secondary_circuit_board_thickness"]))
    sk_h1.MapMode = "FlatFace"
    sk_h1.AttachmentSupport = (doc.getObject("XY_Plane"), [])
    sk_h1.addGeometry(Part.Circle(App.Vector(l/2 - hole_inset + stagger, w/2 - hole_inset, 0), App.Vector(0, 0, 1), hole_dia/2), False)
    sk_h1.addConstraint(Sketcher.Constraint("Radius", 0, "Parameters.mounting_hole_diameter"))
    hole1 = body.newObject("PartDesign::Hole", "Hole1")
    hole1.Profile = sk_h1
    hole1.Type = "FullyDefined"
    hole1.Depth = "ThroughAll"
    hole1.Angle = 90.0
    hole1.Axis = (doc.getObject("Z_Axis"), [""])
    
    # Hole 2: Bottom-Right (Staggered Y)
    sk_h2 = body.newObject("Sketcher::SketchObject", "HoleSketch2
