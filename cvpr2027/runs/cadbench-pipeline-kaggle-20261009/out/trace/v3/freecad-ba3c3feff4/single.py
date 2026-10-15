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

# Base Part Parameters
params = {
    "mount_outer_diameter": 15.19,
    "mount_overall_height": 6.02,
    "outer_flange_lip_height": 0.38,
    "lower_body_top_height": 2.0825,
    "taper_transition_height": 1.51,
    "lower_body_taper_base_diameter": 10.55,
    "lower_body_top_diameter": 10.45,
    "inner_wall_base_thickness": 1.7451912,
    "top_surface_outer_diameter": 7.4335456,
    "inner_shelf_diameter": 5.8444164,
    "inner_shelf_height": 5.1305,
    "outer_tangent_blend_radius": 1.27,
    "inner_tangent_blend_radius": 0.3175,
    "upper_wall_blend_termination_angle": 175.0,
}

# Edit Parameters (Target)
edit_params = {
    "clip_slot_length": 11.43,
    "clip_slot_width": 5.08,
    "clip_slot_pocket_depth": 3.9375,
    "clip_slot_center_offset": 4.13,
}

def create_document():
    doc = App.newDocument("PartDesign_Mount")
    doc.Label = "Magnetic Mount"
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Create Parameters Object (Editable)
    params_obj = body.newObject("App::VarSet", "Parameters")
    for name, value in params.items():
        params_obj.addProperty("App::PropertyFloat", name, "Parameters", "Dimensions")
        params_obj.setValue(name, value)
    
    # Create Reference Planes
    # XY_Plane (Z=0), XZ_Plane (Y=0), YZ_Plane (X=0)
    # FreeCAD 1.1 usually has these as App::Plane objects named XY_Plane, etc.
    # If not found, we create them or assume they exist in the default document.
    # For robustness in headless, we try to get them.
    planes = ["XY_Plane", "XZ_Plane", "YZ_Plane"]
    axes = ["X_Axis", "Y_Axis", "Z_Axis"]
    
    plane_objs = {}
    axis_objs = {}
    
    for name in planes:
        obj = doc.getObject(name)
        if obj:
            plane_objs[name] = obj
        else:
            # Fallback: Create a plane if missing (though standard doc usually has them)
            # In a real headless script without GUI, we might need to create them manually,
            # but standard FreeCAD docs often include them. 
            # Let's assume they exist or create a simple workaround if needed.
            # For this script, we assume standard planes exist.
            pass
            
    for name in axes:
        obj = doc.getObject(name)
        if obj:
            axis_objs[name] = obj
            
    return doc, body, params_obj, plane_objs, axis_objs

def build_base_part(doc, body, params_obj, plane_objs, axis_objs):
    # 1. Base Sketch: Outer Flange Lip (Top Face)
    # We build from bottom up.
    # Step 1: Create the bottom-most sketch for the tapered body base.
    # Actually, let's build the profile from the bottom (Z=0) upwards.
    
    # Sketch 1: Bottom of the tapered body (Z=0)
    sk1 = body.newObject("Sketcher::SketchObject", "Sketch_Bottom")
    sk1.Placement = App.Placement(App.Vector(0, 0, 0))
    sk1.Support = (plane_objs["XY_Plane"], [""])
    sk1.MapMode = "FlatFace"
    
    # Outer diameter at bottom
    d_bottom = params_obj.getValue("lower_body_taper_base_diameter")
    sk1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), d_bottom / 2.0), False)
    sk1.addConstraint(Sketcher.Constraint("Radius", 0, 1, d_bottom / 2.0))
    sk1.addConstraint(Sketcher.Constraint("Center", 0, 1))
    sk1.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
    sk1.addConstraint(Sketcher.Constraint("Vertical", 0, 1))
    
    # 2. Pad to lower_body_top_height
    pad1 = body.newObject("PartDesign::Pad", "Pad_Bottom")
    pad1.Profile = sk1
    pad1.Length = params_obj.getValue("lower_body_top_height")
    pad1.Type = "Solid"
    
    # 3. Sketch 2: Top of the tapered body (Z = lower_body_top_height)
    # This sketch defines the start of the upper wall.
    # We need to create a sketch on the face of Pad1.
    # However, PartDesign::Pad creates a face. We can attach a new sketch to that face.
    # But to keep it simple and robust, let's use a single continuous profile sketch 
    # if possible, or multiple sketches.
    # Given the complexity (taper + blends), a single sketch with a complex profile 
    # rotated or a series of pads is better.
    # Let's try a single sketch for the entire outer profile from Z=0 to Z=mount_overall_height.
    # This requires calculating the X coordinates at specific Z heights.
    
    # Re-evaluating strategy: 
    # A single sketch with a closed loop defined by lines and arcs is hard to parametrize 
    # with tangent blends easily in FreeCAD Sketcher without complex constraints.
    # Better approach: 
    # 1. Pad the bottom cylinder (taper base).
    # 2. Pad the tapered section.
    # 3. Pad the upper wall section.
    # 4. Add fillets.
    
    # Let's refine the geometry construction:
    # Z=0: D = lower_body_taper_base_diameter
    # Z=lower_body_top_height: D = lower_body_top_diameter
    # Z=mount_overall_height: D = mount_outer_diameter
    
    # We will create 3 Pads for the outer body.
    
    # --- Outer Body Construction ---
    
    # Pad 1: Bottom Cylinder (Z=0 to Z=lower_body_top_height)
    # Wait, the description says "gently tapered lower annular body".
    # So it's not a cylinder. It's a frustum.
    # We can do this with a Pad using a sketch with a line, or a Revolution.
    # Let's use a Pad with a sketch that has a line segment.
    
    # Sketch 1 (Bottom Profile): Line from (0,0) to (D_bottom/2, 0)
    sk_bottom = body.newObject("Sketcher::SketchObject", "Sketch_Bottom_Profile")
    sk_bottom.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_bottom.Support = (plane_objs["XY_Plane"], [""])
    sk_bottom.MapMode = "FlatFace"
    
    # Line from center to edge
    sk_bottom.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params_obj.getValue("lower_body_taper_base_diameter")/2, 0, 0)), False)
    sk_bottom.addConstraint(Sketcher.Constraint("Radius", 0, 1, params_obj.getValue("lower_body_taper_base_diameter")/2)) # Approximate with circle constraint then convert? No, let's use Line.
    sk_bottom.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
    sk_bottom.addConstraint(Sketcher.Constraint("Center", 0, 1))
    
    # Actually, for a taper, we need a line.
    # Let's define the profile as a line segment.
    # To make it a solid, we need to close it or use a revolution.
    # Let's use a Revolution for the tapered part? 
    # "PartDesign::Revolution" is good for tapers.
    
    # Let's switch strategy for the body:
    # 1. Pad the bottom flat part? No, it's tapered immediately.
    # 2. Revolution of a line segment from Z=0 to Z=lower_body_top_height.
    #    Radius at Z=0: lower_body_taper_base_diameter / 2
    #    Radius at Z=lower_body_top_height: lower_body_top_diameter / 2
    
    # Sketch for Revolution 1 (Bottom Taper)
    sk_rev1 = body.newObject("Sketcher::SketchObject", "Sketch_Rev1")
    sk_rev1.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_rev1.Support = (plane_objs["XY_Plane"], [""])
    sk_rev1.MapMode = "FlatFace"
    
    # Line from (0,0) to (R_bottom, 0)
    R_bottom = params_obj.getValue("lower_body_taper_base_diameter") / 2.0
    sk_rev1.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(R_bottom, 0, 0)), False)
    sk_rev1.addConstraint(Sketcher.Constraint("Radius", 0, 1, R_bottom))
    sk_rev1.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
    sk_rev1.addConstraint(Sketcher.Constraint("Center", 0, 1))
    
    # Revolution 1
    rev1 = body.newObject("PartDesign::Revolution", "Rev_Bottom")
    rev1.Profile = sk_rev1
    rev1.ReferenceAxis = (axis_objs["Z_Axis"], [""])
    rev1.Angle = 360.0
    rev1.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Now we need to taper it. A simple revolution of a line creates a cone.
    # We need a frustum. We can do this by:
    # 1. Pad a cylinder of R_bottom to height H1.
    # 2. Pad a frustum? No, PartDesign doesn't have a direct "Frustum" feature.
    #    We can use a Pad with a sketch that has a line, but the sketch must be on the face.
    #    Or, we can use a Pad with a sketch that defines the profile, and the Pad extrudes it.
    #    If we extrude a line, we get a plane.
    #    We need to use a "Pad" with a "Sketch" that is a closed loop? No.
    #    Standard way: Pad a cylinder, then Pad a frustum using a sketch on the top face.
    #    But a frustum is defined by two radii.
    #    We can create a sketch on the top face (Z=H1) and draw a line from (0,0) to (R_top, 0).
    #    Then use a Pad? No, Pad extrudes perpendicular to the face.
    #    We need to rotate the line.
    #    So: Sketch on Z=H1 face -> Line (0,0) to (R_top, 0).
    #    Then Revolution? Yes.
    #    But Revolution needs a profile in a plane. The sketch is in the XY plane of the face.
    #    If we revolve around Z axis, it works.
    
    # Let's restart the body construction logic to be precise:
    # 1. Pad Cylinder (R_bottom, H1)
    # 2. Sketch on top face: Line (0,0) to (R_top, 0).
    # 3. Revolution of that line? No, Revolution of a line creates a cone.
    #    We want to replace the top of the cylinder with a tapered section.
    #    Actually, we can just Pad the cylinder, then Pad the tapered section.
    #    How to Pad a tapered section?
    #    We can use a Pad with a sketch that is a line, but the Pad direction must be along the line? No.
    #    We can use a "Pad" with a "Sketch" that is a closed loop? No.
    #    Correct approach for Frustum in PartDesign:
    #    1. Pad Cylinder (R_bottom, H1).
    #    2. Create a sketch on the top face. Draw a line from (0,0) to (R_top, 0).
    #    3. Use a "Pad" with the sketch? No, that extrudes up.
    #    4. Use a "Pad" with the sketch, but the sketch is a line? No.
    #    5. Use a "Pad" with a "Sketch" that is a line, and set the "Midplane" or something? No.
    #    6. Use a "Pad" with a "Sketch" that is a line, and the "Length" is the height?
    #       This creates a cylinder of radius R_top.
    #    7. To get a taper, we need to subtract a cone or add a cone.
    #       We can Pad a cone (Revolution of a line) and then subtract?
    #       Or, we can use a "Pad" with a "Sketch" that is a line, and the "Length" is the height, 
    #       but the sketch is on the side? No.
    
    # Alternative: Use a single sketch for the whole profile and use a "Pad" with "Midplane" or "Reversed"? No.
    # The most robust way for a frustum in PartDesign is:
    # 1. Pad Cylinder (R_bottom, H1).
    # 2. Create a sketch on the top face. Draw a line from (0,0) to (R_top, 0).
    # 3. Use a "Pad" with the sketch? No.
    # 4. Use a "Pad" with a "Sketch" that is a line, and the "Length" is the height, 
    #    but the sketch is a line segment?
    #    If we sketch a line from (0,0) to (R_top, 0) on the top face, and then use a "Pad" 
    #    with "Length" = H2, we get a cylinder of radius R_top.
    #    To get a taper, we need to subtract a cone from the cylinder?
    #    Or add a cone to the cylinder?
    #    If we add a cone (Revolution of a line from (0,0) to (R_top, 0) with angle 180? No).
    #    We can create a cone by revolving a line from (0,0) to (R_top, 0) around Z axis? 
    #    That creates a cone with tip at (0,0,0) and base at Z=H2.
    #    We want a frustum from Z=H1 to Z=H2.
    #    So we need a cone with tip at Z=H1 - (H2-H1)*R_bottom/R_top?
    #    This is getting complicated.
    
    # Simpler approach:
    # 1. Pad Cylinder (R_bottom, H1).
    # 2. Pad Cylinder (R_top, H2-H1).
    # 3. Subtract a Cone (Revolution of a line from (0,0) to (R_bottom, 0) with tip at Z=H1)?
    #    No, we want to taper from R_bottom to R_top.
    #    We can subtract a cone with tip at Z=H1 and base radius R_bottom at Z=H1? No.
    #    We can subtract a cone with tip at Z=H1 - delta and base radius R_bottom at Z=H1?
    #    Let's calculate the tip of the cone that connects R_bottom at Z=H1 to R_top at Z=H2.
    #    Slope m = (R_top - R_bottom) / (H2 - H1).
    #    Tip Z = H1 - R_bottom / m.
    #    Then we subtract a cone with tip at (0,0,TipZ) and base radius R_bottom at Z=H1.
    #    Wait, if we subtract a cone with tip at TipZ and base radius R_bottom at Z=H1, 
    #    the radius at Z=H2 will be R_top.
    #    Yes!
    
    # So:
    # 1. Pad Cylinder (R_bottom, H1).
    # 2. Pad Cylinder (R_top, H2-H1).
    # 3. Subtract Cone (Tip at Z=TipZ, Base R_bottom at Z=H1).
    
    # Let's implement this.
    
    # --- Outer Body Construction ---
    
    # 1. Bottom Cylinder
    sk_cyl1 = body.newObject("Sketcher::SketchObject", "Sketch_Cyl1")
    sk_cyl1.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_cyl1.Support = (plane_objs["XY_Plane"], [""])
    sk_cyl1.MapMode = "FlatFace"
    R1 = params_obj.getValue("lower_body_taper_base_diameter") / 2.0
    sk_cyl1.addGeometry(Part.Circle(App.Vector
