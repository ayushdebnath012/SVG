import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

def get_axis(doc, axis_name):
    """Helper to get standard axes or create them if missing."""
    obj = doc.getObject(axis_name)
    if obj:
        return (obj, [""])
    else:
        # Create if missing to ensure robustness
        plane = doc.addObject("PartDesign::Plane", axis_name)
        plane.Plane = App.Vector(0, 0, 0), App.Vector(0, 0, 1) # XZ plane default for Z axis
        doc.recompute()
        return (plane, [""])

def create_solid_body(doc):
    """Creates an empty PartDesign Body."""
    body = doc.addObject("PartDesign::Body", "Body")
    return body

def create_sketch(doc, body, name, parent_planename, orientation="XY"):
    """Creates a Sketcher::SketchObject attached to a specific plane."""
    # Identify the plane
    if parent_planename == "XY_Plane":
        support = (doc.getObject("XY_Plane"), [""])
        orientation_map = {"XY": (0, 1, 0), "XZ": (1, 0, 0), "YZ": (0, 0, 1)}
        axis_map = {"XY": "X_Axis", "XZ": "Z_Axis", "YZ": "Y_Axis"}
        ref_axis = doc.getObject(axis_map[orientation])
        support = (ref_axis, [""])
    elif parent_planename == "XZ_Plane":
        support = (doc.getObject("XZ_Plane"), [""])
        orientation_map = {"XY": (0, 1, 0), "XZ": (1, 0, 0), "YZ": (0, 0, 1)}
        axis_map = {"XY": "X_Axis", "XZ": "Z_Axis", "YZ": "Y_Axis"}
        ref_axis = doc.getObject(axis_map[orientation])
        support = (ref_axis, [""])
    elif parent_planename == "YZ_Plane":
        support = (doc.getObject("YZ_Plane"), [""])
        orientation_map = {"XY": (0, 1, 0), "XZ": (1, 0, 0), "YZ": (0, 0, 1)}
        axis_map = {"XY": "X_Axis", "XZ": "Z_Axis", "YZ": "Y_Axis"}
        ref_axis = doc.getObject(axis_map[orientation])
        support = (ref_axis, [""])
    
    # Actually, standard FreeCAD 1.1 behavior for PartDesign sketches on Planes:
    # The sketch is usually placed on a PartDesign::Plane object.
    # If we use the standard XY, XZ, YZ Planes, we attach the sketch to them.
    
    sketch = body.newObject("Sketcher::SketchObject", name)
    # Determine attachment support based on parent name
    if "XY" in parent_planename:
        sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
        sketch.Placement.Rotation = App.Rotation(App.Vector(0, 0, 1), 0) # XY plane orientation
        sketch.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 0) # Default to XY plane normal Z
        # To be safe, let's explicitly set the plane if using standard planes
        # In FreeCAD 1.1 PartDesign, usually we attach to a PartDesign::Plane
        # But for simple scripts, attaching to the XY_Plane object works if we use the correct API
        # However, the most robust way in 1.1 is often:
        sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
        # We will rely on the default behavior of the body's coordinate system or explicit plane attachment.
        # Let's use the standard approach: Attach to the plane object.
        if parent_planename == "XY_Plane":
            sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
        elif parent_planename == "XZ_Plane":
            sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 1, 0), 90)) # Rotate to XZ
        elif parent_planename == "YZ_Plane":
            sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(1, 0, 0), 90)) # Rotate to YZ
            
    sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    return sketch

def add_constraint(sketch, c_type, idx1, idx2, val1=None, val2=None, ref1=None, ref2=None):
    """Helper to add a constraint."""
    # This is a simplified helper. Real usage requires knowing object indices.
    pass

def build_base_part(doc):
    body = create_solid_body(doc)
    
    # Parameters
    params = body.newObject("App::FeaturePython", "Parameters") # Using FeaturePython for code injection if needed, or simple App::Property
    # Actually, App::Property is standard. Let's use App::Property
    params = body.newObject("App::VarSet", "Parameters") # VarSet allows defining properties
    
    # Define Base Parameters
    params.addProperty("App::PropertyLength", "rotor_outer_diameter")
    params.rotor_outer_diameter = 250.0
    params.addProperty("App::PropertyLength", "hub_outer_diameter")
    params.hub_outer_diameter = 84.9558108
    params.addProperty("App::PropertyLength", "hub_height")
    params.hub_height = 5.0
    params.addProperty("App::PropertyLength", "disc_lower_surface_position")
    params.disc_lower_surface_position = 3.0
    params.addProperty("App::PropertyLength", "disc_upper_surface_position")
    params.disc_upper_surface_position = 8.0
    params.addProperty("App::PropertyLength", "hub_top_transition_radius")
    params.hub_top_transition_radius = 40.0
    params.addProperty("App::PropertyLength", "braking_band_upper_inner_radius")
    params.braking_band_upper_inner_radius = 55.0
    params.addProperty("App::PropertyLength", "hat_transition_fillet_radius")
    params.hat_transition_fillet_radius = 6.885713
    
    # --- 1. Hub Sketch (Profile in XY plane) ---
    sketch_hub = body.newObject("Sketcher::SketchObject", "Sketch_Hub_Profile")
    sketch_hub.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    sketch_hub.Layer = "0"
    
    # Outer Hub Circle
    sketch_hub.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hub_outer_diameter / 2), False)
    # Inner Pilot (Base only, small center opening)
    sketch_hub.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 2.0), False) # Small pilot
    
    # Center Constraint
    sketch_hub.addConstraint(Sketcher.Constraint("Center", 0, 1)) # Center on 0 (circle 0)
    sketch_hub.addConstraint(Sketcher.Constraint("Center", 1, 1)) # Center on 1 (circle 1)
    sketch_hub.addConstraint(Sketcher.Constraint("Horizontal", 0, 1)) # Align centers
    sketch_hub.addConstraint(Sketcher.Constraint("Radius", 0, 1, params.hub_outer_diameter / 2))
    sketch_hub.addConstraint(Sketcher.Constraint("Radius", 1, 1, 2.0))
    
    # --- 2. Braking Band & Hat Profile Sketch (in XZ plane at Z = disc_lower_surface_position + hat_height_offset?) ---
    # The description says: "hub rises to hub_height... braking band... axial faces lie at disc_lower_surface_position and disc_upper_surface_position"
    # Hub is from Z=0 to Z=hub_height.
    # Braking band is from Z=disc_lower_surface_position to Z=disc_upper_surface_position.
    # There is a transition between Hub (Z=5) and Braking Band (Z=3 to 8).
    # Wait, 3 to 8 covers 5. So they overlap? 
    # "Hub rises to hub_height (5.0). ... braking band ... axial faces lie at 3.0 and 8.0".
    # This implies the hub is the core (Z=0 to 5). The braking band is the annular ring (Z=3 to 8).
    # The "hat transition" connects the hub top (Z=5) to the braking band inner wall.
    
    # Let's define the profile for the Braking Band and Hat.
    # We need a sketch in XZ plane.
    # Let's place the sketch at Z = disc_lower_surface_position = 3.0.
    # But the hub is solid up to 5.0.
    # So the profile needs to account for the hub removal or intersection.
    # Strategy: Create a "Braking Band Block" that extends from Z=3 to Z=8.
    # Then subtract the Hub (Z=0 to 5) later? Or define the Hub separately.
    # PartDesign Body order matters.
    # Let's do:
    # 1. Pad Hub (Z=0 to 5).
    # 2. Pad Braking Band + Hat (Z=3 to 8).
    # 3. The intersection will naturally create the geometry if we Pad from Z=3.
    #    But we need the hub to exist inside.
    #    Actually, the Hub is the inner part. The Braking Band is the annulus.
    #    If we Pad Hub first (0 to 5), then Pad Braking Band (3 to 8), the result is a union.
    #    The Braking Band sketch should represent the annulus shape at Z=3.
    
    # Let's create the Braking Band Profile in XZ plane.
    # Z=0 in sketch corresponds to global Z=3.
    
    sketch_band = body.newObject("Sketcher::SketchObject", "Sketch_Band_Profile")
    sketch_band.Placement = App.Placement(App.Vector(0, 0, 3.0), App.Rotation(App.Vector(0, 1, 0), 90)) # Rotate to XZ, shift to Z=3
    
    # Inner Radius of Braking Band at the bottom (Z=3) is not given directly, but implied by the hub?
    # "hub_outer_diameter = 84.9558108". "hub_top_transition_radius = 40.0".
    # The braking band inner radius at the top (Z=8) is likely related to the hub outer diameter?
    # Or is the hub outer diameter the bottom inner radius?
    # Usually, the hub outer diameter is the inner diameter of the rotor.
    # Let's assume the braking band inner radius at the bottom is hub_outer_diameter / 2?
    # But there is a "hat transition".
    # "Equal-radius fillets and parallel sloping walls join the hub region to the inner edge of the braking band"
    # This suggests the inner wall of the braking band is slanted.
    # Inner Radius at Z=3 = Hub Outer Radius = 42.4779 mm.
    # Inner Radius at Z=8 = Hub Top Transition Radius = 40.0 mm.
    # So we need a trapezoid profile for the inner wall of the band.
    
    # Outer Radius of braking band?
    # "braking_band_upper_inner_radius = 55.0". This might be the inner radius of the band at the top?
    # Or the inner radius of the band generally?
    # Let's assume the braking band is an annulus.
    # Inner wall: Slanted from R=42.4779 (at Z=3) to R=40.0 (at Z=8).
    # Outer wall: Parallel to inner wall? "parallel sloping walls".
    # Outer Radius at Z=3? Not explicitly given.
    # Let's assume the braking band outer radius is derived from the rotor outer diameter?
    # No, rotor outer diameter is the rim.
    # Let's assume the braking band outer radius is defined by the hat transition?
    # Let's assume the braking band outer radius at the top (Z=8) is 55.0 + something?
    # Wait, "braking_band_upper_inner_radius = 55.0". This is confusing.
    # Maybe it means the inner radius of the *braking band* (the ring itself) is 55?
    # If so, Hub Outer (42.5) -> Band Inner (55)?
    # That leaves a gap.
    # Re-reading: "hub_outer_diameter = 84.9558108" (Radius ~42.5).
    # "hub_top_transition_radius = 40.0".
    # "braking_band_upper_inner_radius = 55.0".
    # This implies the hub outer diameter is NOT the braking band inner radius.
    # There is a hat transition between the hub (R=42.5) and the braking band (R=55 at top).
    # But the text says: "Equal-radius fillets and parallel sloping walls join the hub region to the inner edge of the braking band".
    # This implies the transition connects R=42.5 to R=55.
    # So the Hat Transition Radius (6.88) is used for the fillet.
    # The "parallel sloping walls" likely refers to the outer wall of the hub and inner wall of the band?
    # Or the inner wall of the band and the hub outer wall?
    # Let's assume:
    # 1. Hub: Cylindrical R=42.4779, H=5.0 (Z=0 to 5).
    # 2. Braking Band Inner Wall: Slanted from R=42.4779 (Z=3) to R=55.0 (Z=8)?
    #    Wait, the braking band is from Z=3 to Z=8.
    #    At Z=3, the inner radius is R_hub = 42.4779.
    #    At Z=8, the inner radius is R_band_inner = 55.0.
    #    So the inner wall slopes outward.
    #    Length of slope in Z = 5mm. Delta R = 55 - 42.4779 = 12.5221.
    #    Slope angle = atan(12.5221/5) = 68 deg.
    #    Fillet at the top corner (Z=8, R=55) connecting to the braking band?
    #    "hat_transition_fillet_radius = 6.885713".
    #    This fillet likely connects the Hub Top (Z=5, R=42.5) to the Braking Band Inner Wall (Z=3 to 8)?
    #    But the braking band starts at Z=3.
    #    So the Hub (0-5) and Band (3-8) overlap in Z.
    #    The Union will fill the overlap.
    #    The "Hat" is the volume added between Z=5 and Z=8 at the inner radius.
    #    So we Pad the Braking Band profile from Z=3 to Z=8.
    #    The profile at Z=3 (sketch origin): Inner Radius = 42.4779.
    #    The profile at Z=8: Inner Radius = 55.0.
    #    Wait, if we use a sketch at Z=3, we define the shape at that Z.
    #    If the shape changes, we need a swept profile or a sketch that represents the extrusion start.
    #    Since it's a "sloping wall", the cross-section changes.
    #    We can't just extrude a constant profile.
    #    We need to model the Hub and the Band separately or use a Pad with a varying profile?
    #    PartDesign Pad accepts a Sketch. If the sketch is in XZ, we can define the profile at Z=3.
    #    But the inner radius changes.
    #    Alternative: Model the Hub (0-5). Then Model the "Hat + Band" as a solid that starts at Z=5?
    #    But the Band goes down to Z=3.
    #    Okay, let's re-read carefully: "hub rises to hub_height". "braking band ... axial faces lie at disc_lower ... disc_upper".
    #    This implies the Hub is the central cylinder (0-5). The Braking Band is the annulus (3-8).
    #    The intersection is (3-5).
    #    In the intersection, the geometry is the Hub (R=42.5).
    #    Above Z=5, the geometry is the Band Inner Wall (sloping to 55) and Band Outer Wall.
    #    Below Z=3, the geometry is just the Hub.
    #    So, we can Pad the Hub (0-5).
    #    Then we need to Pad the "Hat" part (5-8) with the sloping inner wall.
    #    But the Band also has an outer wall.
    #    Let's assume the Band Outer Wall is parallel to the Inner Wall.
    #    What is the outer radius at the bottom (Z=3)?
    #    Maybe the "
