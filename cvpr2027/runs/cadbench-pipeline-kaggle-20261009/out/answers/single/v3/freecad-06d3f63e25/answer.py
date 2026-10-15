import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Derived from __file__
script_path = Path(__file__).resolve()
base_filename = script_path.stem + "_base.FCStd"
edit_filename = script_path.stem + "_edit.FCStd"

# Base Parameters
params_base = {
    "clip_base_length": 12.57,
    "clip_base_width": 23.34,
    "clip_base_thickness": 4.06,
    "barb_cutout_base_width": 1.01,
    "barb_cutout_height": 1.76,
    "gap_between_barb_cutouts": 2.04,
    "number_of_barb_cutouts": 2,
    "slot_top_arc_radius": 1.1684,
    "slot_top_arc_central_angle_1": 90.0,
    "slot_top_arc_central_angle_2": 270.0,
    "slot_arc_center_y_position": 9.6393,
    "slot_straight_length": 19.3194355,
    "slot_bottom_width": 1.0348006,
    "slot_bottom_taper_height": 1.1275645,
    "slot_overall_width": 2.3368,
    "trapezoid_bottom_width": 2.04,
    "trapezoid_top_width": 1.0348006,
    "trapezoid_bottom_y_position": -11.67,
    "trapezoid_top_y_position": -10.8077,
    "slot_width": 0.77,
    "slot_length": 15.72,
    "slot_spacing": 11.8,
}

# Edit Parameters
params_edit = {
    "cutout_arc_radius": 2.73,
    "cutout_arc_central_angle": 31.3008576,
    "cutout_arc_center_y": 2.12,
    "cutout_base_width": 5.48,
    "cutout_base_height": 3.3,
    "cutout_slot_width": 1.4729302,
}

def create_document_and_body():
    doc = App.newDocument("Part")
    body = doc.addObject("PartDesign::Body", "Body")
    return doc, body

def add_parameters(body, params_dict):
    # Create a VarSet to hold parameters
    varset = body.newObject("App::VarSet", "Parameters")
    for name, value in params_dict.items():
        varset.addProperty("App::PropertyLength", name, "Dimensions")
        varset[name] = value
    return varset

def create_sketch(body, name, plane="XY_Plane", offset=0.0):
    sketch = body.newObject("Sketcher::SketchObject", name)
    # Find the plane
    plane_obj = None
    for obj in doc.Objects:
        if obj.Name == plane:
            plane_obj = obj
            break
    
    if plane_obj:
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = plane_obj.Placement * sketch.Placement
        sketch.Placement = App.Placement(App.Vector(0, 0, offset)) # Reset to local origin relative to body if needed, but usually attachment handles it
        # Actually, simpler approach for PartDesign:
        # Set AttachmentSupport to the plane object
        sketch.AttachmentSupport = (plane_obj, [""])
        sketch.MapMode = "FlatFace"
    else:
        # Fallback if plane not found (shouldn't happen in standard doc)
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App.Vector(0, 0, offset))
        sketch.Placement = App.Placement(App
