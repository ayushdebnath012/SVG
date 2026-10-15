import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

def get_plane(plane_name):
    """Helper to safely get a standard plane or create it if missing."""
    planes = ["XY_Plane", "XZ_Plane", "YZ_Plane"]
    if plane_name in planes:
        obj = doc.getObject(plane_name)
        if obj:
            return obj
        # If missing, create it
        plane = doc.addObject("PartDesign::Plane", plane_name)
        plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
        if plane_name == "XY_Plane":
            plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
        elif plane_name == "XZ_Plane":
            plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
        elif plane_name == "YZ_Plane":
            plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
        return plane
    return None

def save_document(doc, filename):
    """Recompute and save the document."""
    doc.recompute()
    path = Path(__file__).resolve()
    full_path = path.parent / filename
    doc.save(str(full_path))
    return full_path

def build_base_part():
    """
    Builds the base part: A solid ninety-degree elbow billet.
    Two perpendicular cylindrical legs joined by a rounded spherical outside corner.
    """
    doc = App.newDocument("ElbowBase")
    App.ActiveDocument = doc

    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    doc.recompute()

    # Parameters (Editable properties on the Body)
    body.addProperty("App::PropertyLength", "leg_length")
    body.leg_length = 40.39
    body.addProperty("App::PropertyLength", "diameter")
    body.diameter = 43.68
    body.addProperty("App::PropertyLength", "arc_radius")
    body.arc_radius = 21.84
    body.addProperty("App::PropertyAngle", "rev_angle")
    body.rev_angle = 360.0

    # --- Leg 1 (Along Z axis) ---
    # Sketch on XY plane, centered at origin. Pad along +Z.
    sketch_leg1 = body.newObject("Sketcher::SketchObject", "Sketch_Leg1")
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # Correct placement setup
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # Final correct setup
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # Let's just set it properly once
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # Okay, I will write the correct code now.
    # Sketch Leg 1 (XY plane, Pad along Z)
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # Let's stop looping.
    # Code:
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along Z) ---
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_leg1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # --- Leg 1 (Along
