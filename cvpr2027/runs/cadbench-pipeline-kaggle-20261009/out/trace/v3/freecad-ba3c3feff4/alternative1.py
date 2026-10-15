import FreeCAD as App
import Part
import PartDesign
import Sketcher
from pathlib import Path

def create_base():
    """
    Creates the base magnetic-back cable-tie mount.
    """
    doc = App.newDocument("Mount_Base")
    
    # --- Parameters ---
    params = doc.addObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "mount_outer_diameter", "Dimensions", "15.19")
    params.mount_outer_diameter = 15.19
    params.addProperty("App::PropertyLength", "mount_overall_height", "Dimensions", "6.02")
    params.mount_overall_height = 6.02
    params.addProperty("App::PropertyLength", "outer_flange_lip_height", "Dimensions", "0.38")
    params.outer_flange_lip_height = 0.38
    params.addProperty("App::PropertyLength", "lower_body_top_height", "Dimensions", "2.0825")
    params.lower_body_top_height = 2.0825
    params.addProperty("App::PropertyLength", "taper_transition_height", "Dimensions", "1.51")
    params.taper_transition_height = 1.51
    params.addProperty("App::PropertyLength", "lower_body_taper_base_diameter", "Dimensions", "10.55")
    params.lower_body_taper_base_diameter = 10.55
    params.addProperty("App::PropertyLength", "lower_body_top_diameter", "Dimensions", "10.45")
    params.lower_body_top_diameter = 10.45
    params.addProperty("App::PropertyLength", "inner_wall_base_thickness", "Dimensions", "1.7451912")
    params.inner_wall_base_thickness = 1.7451912
    params.addProperty("App::PropertyLength", "top_surface_outer_diameter", "Dimensions", "7.4335456")
    params.top_surface_outer_diameter = 7.4335456
    params.addProperty("App::PropertyLength", "inner_shelf_diameter", "Dimensions", "5.8444164")
    params.inner_shelf_diameter = 5.8444164
    params.addProperty("App::PropertyLength", "inner_shelf_height", "Dimensions", "5.1305")
    params.inner_shelf_height = 5.1305
    params.addProperty("App::PropertyLength", "outer_tangent_blend_radius", "Dimensions", "1.27")
    params.outer_tangent_blend_radius = 1.27
    params.addProperty("App::PropertyLength", "inner_tangent_blend_radius", "Dimensions", "0.3175")
    params.inner_tangent_blend_radius = 0.3175
    params.addProperty("App::PropertyLength", "upper_wall_blend_termination_angle", "Dimensions", "175.0")
    params.upper_wall_blend_termination_angle = 175.0

    # --- Body ---
    body = doc.addObject("PartDesign::Body", "Body")
    
    # --- Support Planes ---
    doc.addObject("PartDesign::Plane", "XY_Plane")
    doc.addObject("PartDesign::Plane", "XZ_Plane")
    doc.addObject("PartDesign::Plane", "YZ_Plane")
    doc.addObject("PartDesign::Axis", "X_Axis")
    doc.addObject("PartDesign::Axis", "Y_Axis")
    doc.addObject("PartDesign::Axis", "Z_Axis")

    # --- Base Sketch (Bottom of Taper) ---
    # Radius calculation: (base_dia + top_dia) / 2
    # Z: 0.0
    sketch_base = body.newObject("Sketcher::SketchObject", "Sketch_BaseBottom")
    sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_base.Support = [(doc.getObject("XY_Plane"), [])]
    sketch_base.MapMode = "FlatFace"
    
    r_base = (params.lower_body_taper_base_diameter / 2) + (params.inner_wall_base_thickness / 2)
    sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_base))
    sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_shelf_diameter / 2))
    
    # Constraint: Concentric
    sketch_base.addConstraint(Sketcher.Constraint("Equal", 0, 1, 1, 0))
    # Constraint: Vertical centerlines (Coincident to origin)
    sketch_base.addConstraint(Sketcher.Constraint("PointOnUnconstrained", 0, 1, 0, 1))
    sketch_base.addConstraint(Sketcher.Constraint("PointOnUnconstrained", 1, 1, 0, 1))
    doc.recompute()

    # --- Lower Body Taper ---
    # Z: params.lower_body_top_height
    # Outer Radius: (base + top) / 2
    # Inner Radius: inner_shelf_diameter / 2 (constant)
    sketch_taper = body.newObject("Sketcher::SketchObject", "Sketch_Taper")
    sketch_taper.Placement = App.Placement(App.Vector(0, 0, params.lower_body_top_height))
    sketch_taper.Support = [(doc.getObject("XY_Plane"), [])]
    sketch_taper.MapMode = "FlatFace"
    
    r_taper_outer = (params.lower_body_taper_base_diameter + params.lower_body_top_diameter) / 2
    sketch_taper.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_taper_outer))
    sketch_taper.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_shelf_diameter / 2))
    
    sketch_taper.addConstraint(Sketcher.Constraint("Equal", 0, 1, 1, 0))
    sketch_taper.addConstraint(Sketcher.Constraint("PointOnUnconstrained", 0, 1, 0, 1))
    sketch_taper.addConstraint(Sketcher.Constraint("PointOnUnconstrained", 1, 1, 0, 1))
    doc.recompute()

    # --- Upper Wall / Shelf Sketch ---
    # Z: params.inner_shelf_height
    # Outer Radius: top_surface_outer_diameter / 2
    # Inner Radius: inner_shelf_diameter / 2
    sketch_upper = body.newObject("Sketcher::SketchObject", "Sketch_Upper")
    sketch_upper.Placement = App.Placement(App.Vector(0, 0, params.inner_shelf_height))
    sketch_upper.Support = [(doc.getObject("XY_Plane"), [])]
    sketch_upper.MapMode = "FlatFace"
    
    r_upper_outer = params.top_surface_outer_diameter / 2
    sketch_upper.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_upper_outer))
    sketch_upper.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_shelf_diameter / 2))
    
    sketch_upper.addConstraint(Sketcher.Constraint("Equal", 0, 1, 1, 0))
    sketch_upper.addConstraint(Sketcher.Constraint("PointOnUnconstrained", 0, 1, 0, 1))
    sketch_upper.addConstraint(Sketcher.Constraint("PointOnUnconstrained", 1, 1, 0, 1))
    doc.recompute()

    # --- Flange Lip Sketch ---
    # Z: params.mount_overall_height
    # Outer Radius: mount_outer_diameter / 2
    # Inner Radius: top_surface_outer_diameter / 2 (Note: Description says "upper inner and outer walls continue to top_surface_outer_diameter and inner_shelf_diameter through smooth tangent blends". 
    # The lip is the thin perimeter. The inner radius of the lip usually matches the outer radius of the surface below or is slightly larger. 
    # Based on "outer_tangent_blend_radius", the lip connects to the upper wall.
    # Let's assume the inner radius of the lip is top_surface_outer_diameter / 2.
    sketch_lip = body.newObject("Sketcher::SketchObject", "Sketch_Lip")
    sketch_lip.Placement = App.Placement(App.Vector(0, 0, params.mount_overall_height))
    sketch_lip.Support = [(doc.getObject("XY_Plane"), [])]
    sketch_lip.MapMode = "FlatFace"
    
    r_lip_outer = params.mount_outer_diameter / 2
    r_lip_inner = params.top_surface_outer_diameter / 2
    sketch_lip.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_lip_outer))
    sketch_lip.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_lip_inner))
    
    sketch_lip.addConstraint(Sketcher.Constraint("Equal", 0, 1, 1, 0))
    sketch_lip.addConstraint(Sketcher.Constraint("PointOnUnconstrained", 0, 1, 0, 1))
    sketch_lip.addConstraint(Sketcher.Constraint("PointOnUnconstrained", 1, 1, 0, 1))
    doc.recompute()

    # --- Features Construction ---

    # 1. Pad Lower Body Taper
    pad_taper = body.newObject("PartDesign::Pad", "Pad_Taper")
    pad_taper.Profile = sketch_taper
    pad_taper.Length = params.lower_body_top_height
    pad_taper.FeatureSubType = "Tapered"
    # Taper angle calculation:
    # Height = 1.51mm. Delta Radius = (r_base + r_taper) / 2 - (r_taper + r_upper) / 2 ? 
    # Actually, the taper goes from base_bottom to base_top.
    # Base Bottom (Z=0): R = r_base
    # Base Top (Z=2.0825): R = r_taper
    # Delta R = (10.55 + 10.45)/2 - (10.55+10.45)/2 ?? No.
    # Z=0, R=(10.55 + 10.45)/2 = 10.5? No.
    # Let's re-read: "transitions between lower_body_taper_base_diameter and lower_body_top_diameter".
    # So at Z=0, Dia = 10.55. At Z=2.0825, Dia = 10.45.
    # Delta D = -0.1. Delta Z = 2.0825. Angle = atan(0.1 / 2.0825) * 180/pi.
    # But Pad.TaperAngle is in degrees relative to vertical.
    # tan(theta) = (R_top - R_base) / Height
    # R_base = 10.55/2 = 5.275
    # R_top = 10.45/2 = 5.225
    # tan(theta) = -0.05 / 2.0825
    pad_taper.TaperAngle = atan2(params.lower_body_top_diameter/2 - params.lower_body_taper_base_diameter/2, params.lower_body_top_height) * 180 / 3.141592653589793
    # Since it's shrinking, the angle will be negative.
    doc.recompute()

    # 2. Pad Upper Wall / Shelf
    # From Z=2.0825 to Z=5.1305
    pad_upper = body.newObject("PartDesign::Pad", "Pad_Upper")
    pad_upper.Profile = sketch_upper
    pad_upper.Length = params.inner_shelf_height - params.lower_body_top_height
    pad_upper.FeatureSubType = "Tapered"
    # Taper from r_taper_outer to r_upper_outer
    # R_top = (10.45 + 7.4335)/2 ? No, description says "upper inner and outer walls continue to top_surface_outer_diameter... through smooth tangent blends".
    # This implies the outer surface of the upper wall is defined by top_surface_outer_diameter.
    # The inner surface is inner_shelf_diameter.
    # Is there a taper on the upper wall? "continue to ... through smooth tangent blends". 
    # Usually this implies a constant diameter unless specified otherwise, but "tangent blends" suggests transitions.
    # Given the specific diameters provided (top_surface_outer_diameter), let's assume the outer radius of the upper wall is simply top_surface_outer_diameter/2.
    # R_base_for_upper = 10.45/2 = 5.225
    # R_top_for_upper = 7.4335456/2 = 3.71677
    pad_upper.TaperAngle = atan2(params.top_surface_outer_diameter/2 - params.lower_body_top_diameter/2, params.inner_shelf_height - params.lower_body_top_height) * 180 / 3.141592653589793
    doc.recompute()

    # 3. Pad Flange Lip
    # From Z=5.1305 to Z=6.02
    pad_lip = body.newObject("PartDesign::Pad", "Pad_Lip")
    pad_lip.Profile = sketch_lip
    pad_lip.Length = params.mount_overall_height - params.inner_shelf_height
    pad_lip.FeatureSubType = "Tapered"
    # R_base = 7.4335/2 = 3.7167
    # R_top = 15.19/2 = 7.595
    pad_lip.TaperAngle = atan2(params.mount_outer_diameter/2 - params.top_surface_outer_diameter/2, params.mount_overall_height - params.inner_shelf_height) * 180 / 3.141592653589793
    doc.recompute()

    # 4. Internal Shelf (Pocket)
    # Depth = inner_shelf_height. Creates a hole from top down to the shelf surface? 
    # Wait, the shelf is a solid protrusion from the bottom? Or a hole in the wall?
    # "internal shelf ... Heights are measured upward from the bottom face."
    # Usually a shelf is a step inward. 
    # My construction: Pad Taper (creates wall), Pad Upper (creates top surface area), Pad Lip (flange).
    # The "internal shelf" usually means a recessed area or a raised platform? 
    # "mount has ... an internal shelf". If I pad the top area (7.43mm) and the bottom area (10.55mm), the area between them (10.45 -> 7.43) is a tapered wall.
    # The "shelf" is likely the flat surface at Z=5.1305.
    # However, the description says "internal shelf". 
    # Let's assume the "shelf" is the feature created by the taper of the upper wall, effectively creating a step if the inner diameter was different, but here it's concentric.
    # Actually, maybe the "shelf" is the result of the inner hole not being cut all the way? 
    # No, the inner hole is open all the way up to the lip? 
    # "internal shelf" implies a raised platform inside. 
    # If I have a tapered wall (outer 10.55->7.43) and a constant inner hole (5.84), the inner surface is a cylinder.
    # The "shelf" might be the flat surface at the bottom of the inner cavity? 
    # But the inner cavity goes all the way to Z=0? 
    # If the inner hole is open at Z=0, there is no shelf.
    # Re-reading: "internal shelf ... Heights are measured upward from the bottom face."
    # Maybe the inner hole is NOT open at the bottom? 
    # "tapered lower annular body ... internal shelf".
    # This implies the bottom of the inner hole is blocked by a shelf.
    # So I need to cut a pocket at the bottom to create the cavity, but stop at the shelf height?
    # No, if I stop at shelf height, I am creating a solid shelf.
    # But the cavity needs to go down to the bottom face for the cable tie to pass through? 
    # "cable-tie mount". Cable ties go through the bottom.
    # If there is an "internal shelf", it usually means a ledge where the tie rests.
    # This suggests the inner hole is blocked at some height, or the wall thickness varies.
    # Let's assume the standard interpretation: The inner hole goes through the bottom, but the "shelf" is the flat surface at Z=5.1305 on the *inner* surface of the wall?
    # No, that's just the top surface of the tapered wall.
    # Let's reconsider the geometry:
    # Bottom: Dia 10.55 (Outer).
    # Taper to Z=2.08: Dia 10.45 (Outer).
    # Taper to Z=5.13: Dia 7.43 (Outer).
    # Inner: Constant 5.84.
    # If the inner hole is open at the bottom, the "shelf" description is confusing.
    # Unless "internal shelf" refers to the bottom of the inner cavity being *higher* than the bottom face?
    # i
