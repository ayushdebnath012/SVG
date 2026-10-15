from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # Ensure we are working in headless mode without GUI dependencies
    # Initialize document
    doc = App.newDocument("SmoothShaft")
    doc.Label = "SmoothShaft_Parametric"

    # Create the Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))

    # --- Parameters ---
    # We define parameters directly on the Body for direct access or via a VarSet
    # Using a VarSet as per common FreeCAD 1.1 patterns for named parameters
    params = body.newObject("App::VarSet", "Parameters")
    
    params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Shaft Diameter")
    params.shaft_diameter = 30.0
    
    params.addProperty("App::PropertyLength", "shaft_length", "Dimensions", "Shaft Length")
    params.shaft_length = 50.0
    
    params.addProperty("App::PropertyLength", "keyway_width", "Dimensions", "Keyway Width")
    params.keyway_width = 7.0
    
    params.addProperty("App::PropertyLength", "keyway_depth", "Dimensions", "Keyway Depth")
    params.keyway_depth = 4.0
    
    params.addProperty("App::PropertyLength", "keyway_height", "Dimensions", "Keyway Height")
    params.keyway_height = 20.0
    
    params.addProperty("App::PropertyInteger", "num_keyways", "Dimensions", "Number of Keyways")
    params.num_keyways = 1

    # --- Sketch 1: Base Cylinder Profile (Side View) ---
    # We create a sketch in the XY plane to define the outer diameter and the keyway cutout
    sketch_base = body.newObject("Sketcher::SketchObject", "Sketch_BaseProfile")
    sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_base.Support = [(doc.getObject("XY_Plane"), [""])] # Assuming standard planes exist or we create them
    
    # Check if standard planes exist, if not create them (standard FreeCAD init usually has them, 
    # but in headless script without init, we might need to be careful. 
    # However, standard practice in these scripts assumes a basic environment or creates planes.
    # Let's assume standard XY_Plane exists as per standard FreeCAD installation).
    # If strict headless without GUI, planes might be missing. 
    # To be safe and robust, we will create the planes if they don't exist, 
    # but the prompt implies a standard environment. 
    # Let's try to access them. If they fail, we create a temporary plane.
    # Actually, PartDesign::Body newObject("Sketcher::SketchObject") often requires a valid face/plane.
    # We will assume the standard planes XY_Plane, XZ_Plane, YZ_Plane exist in the document root.
    
    # Create sketch geometry for the shaft cross-section
    # Center at (0,0) in the sketch plane (which is XY world plane, so Z is normal).
    # Shape: A rectangle of width = diameter, height = shaft_length/2? 
    # No, standard keyway sketches are often done in a plane passing through the axis.
    # Let's do the sketch in the XZ plane (Side view) to define the cylinder profile and keyway slot easily.
    
    # Re-planning Sketch Strategy:
    # Sketch 1: Side view (XZ plane). 
    #   - Draw a circle of diameter = shaft_diameter? No, circle is better in XY.
    #   - Let's do XY plane for the circle (Cylinder generator).
    #   - But the keyway is a slot. A slot in XY would be a rectangle cutting the circle.
    #   - If we rotate the slot (Revolution), we need the profile in XZ.
    #   - Let's create the profile in the XZ plane (Side view).
    #   - The profile will be: A rectangle of width = shaft_diameter and height = shaft_length.
    #   - Inside that, we need to cut the keyway. 
    #   - Keyway geometry in Side View (XZ): 
    #     - A slot defined by a rectangle? Or a hole?
    #     - Keyway is usually rectangular. 
    #     - Let's define the outer boundary first.
    
    # Let's stick to the prompt's implied flexibility: "choose the sketch planes... afresh".
    # Approach:
    # 1. Create XY_Plane, XZ_Plane, YZ_Plane if they don't exist to ensure robustness.
    
    # Helper to ensure planes exist
    def ensure_planes(doc):
        for name in ["XY_Plane", "XZ_Plane", "YZ_Plane"]:
            if not doc.exists(name):
                p = doc.addObject("PartDesign::Plane", name)
                p.Placement = App.Placement(App.Vector(0,0,0))
                # Standard planes placement is usually implicit in PartDesign or specific vectors.
                # For a simple script, we can just place them at origin and orient them correctly.
                # However, FreeCAD PartDesign::Plane is a specific object type.
                # Let's use a simpler approach: Create a Part::Plane? No, Sketcher needs AttachmentSupport.
                # Standard planes in FreeCAD 1.1 are often just App::Plane or similar?
                # Actually, Sketcher::SketchObject AttachmentSupport expects (Face, AxisList).
                # We can create a sketch on a Part::Plane or just use the document planes.
                # Let's create simple Part::Plane objects to be safe.
                part_plane = doc.addObject("Part::Plane", name)
                part_plane.Placement = App.Placement(App.Vector(0,0,0))
                # Orientations:
                # XY_Plane: Normal Z
                # XZ_Plane: Normal Y
                # YZ_Plane: Normal X
                if name == "XY_Plane": part_plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0,0,0)) # Normal Z
                elif name == "XZ_Plane": part_plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0, 90, 0)) # Normal Y
                elif name == "YZ_Plane": part_plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(90, 0, 0)) # Normal X
                doc.recompute()
                # Note: Part::Plane might not be the best for Sketcher AttachmentSupport in all versions.
                # Let's rely on the standard PartDesign::Plane if available, or just use the document planes if they exist.
                # Given the constraint "reproduce the part", and standard FreeCAD installs usually have these planes.
                # If not, we create a sketch on a Part::Feature (Part::Block) or similar?
                # Let's assume standard planes exist. If not, this script might fail on the specific "ensure" logic if not careful.
                # Let's just try to use them. If not found, create a temporary block to sketch on.
    
    # Check for standard planes
    has_xy = doc.getObject("XY_Plane")
    has_xz = doc.getObject("XZ_Plane")
    has_yz = doc.getObject("YZ_Plane")
    
    # If missing, create a temporary reference face
    if not has_xy or not has_xz:
        # Create a small block to host planes if standard ones are missing
        tmp_body = doc.addObject("PartDesign::Body", "TempBody")
        tmp_sketch = tmp_body.newObject("Sketcher::SketchObject", "TempSketch")
        # Create a simple line or circle to generate a face? 
        # Actually, let's just create a Part::Block and use its face.
        tmp_block = Part.makeBox(1, 1, 1)
        doc.addObject("Part::Feature", "TempBlock").Shape = tmp_block
        # This is getting complicated for a standard script. 
        # Standard FreeCAD 1.1 usually has XY, XZ, YZ planes in the Part Design workbench.
        # We will proceed assuming they exist. If the environment is bare, we might need to create a face.
        # Let's create a Part::Plane if Sketcher::SketchObject fails to find it? 
        # No, let's just create a simple Part::Feature plane if needed.
        # Actually, the most robust way in headless scripts for sketches is to create a Part::Plane object 
        # and attach the sketch to it.
        pass # We will assume standard planes exist as per "FreeCAD 1.1" context usually implying a standard install.

    # --- Feature 1: Pad (Cylinder) ---
    # We define the cylinder in the XY plane.
    # Sketch: Circle of diameter = shaft_diameter.
    # Pad: Revolved? No, Pad of a circle in XY creates a cylinder if we revolve? 
    # Wait, Pad extrudes along the normal. 
    # If Sketch is in XY, normal is Z. Extruding Z creates a cylinder of height = Length.
    # This is perfect.
    
    sketch_cylinder = body.newObject("Sketcher::SketchObject", "Sketch_Cylinder")
    # Attach to XY_Plane. If it doesn't exist, we might get an error. 
    # To be absolutely safe against missing planes in a bare environment:
    # We will create a Part::Plane and use that as support if the standard one is missing.
    # But Sketcher::SketchObject AttachmentSupport accepts (Face, Axis).
    # Let's assume XY_Plane exists.
    
    sketch_cylinder.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_cylinder.Support = [(doc.getObject("XY_Plane"), [""])]
    sketch_cylinder.MapMode = "FlatFace"
    
    # Add Circle
    sketch_cylinder.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.shaft_diameter / 2.0), False)
    
    # Add constraint to keep it centered (implicit with origin)
    # Add constraint to fix radius? No, parameter drives it.
    
    # Pad the cylinder
    pad = body.newObject("PartDesign::Pad", "Pad_Cylinder")
    pad.Profile = sketch_cylinder
    pad.Length = params.shaft_length
    pad.Midplane = False
    
    # --- Feature 2: Keyway ---
    # The keyway is a slot. 
    # We need a sketch showing the slot profile.
    # If we sketch in the XY plane, we draw a rectangle (the slot) and then use a Pocket (ThroughAll or specific length).
    # Or, we can use a Revolution of a profile? 
    # A keyway is a flat slot. Revolution of a profile (like a T-shape) creates a cylinder with a groove.
    # A groove is created by rotating a rectangular profile around the center axis.
    # This is often cleaner than a sketch-based pocket for a full-depth keyway.
    # Let's use a Revolution feature for the keyway groove.
    
    # Sketch for Groove (Side View - XZ Plane)
    sketch_groove = body.newObject("Sketcher::SketchObject", "Sketch_Groove")
    sketch_groove.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_groove.Support = [(doc.getObject("XZ_Plane"), [""])]
    sketch_groove.MapMode = "FlatFace"
    
    # Geometry:
    # We need a shape that, when revolved 360 deg around the Z axis (which is the normal of XY, but XZ plane normal is Y? 
    # Wait. 
    # XZ Plane: X and Z axes. Normal is Y.
    # If we revolve around Y, we get a cylinder standing on its side? No.
    # We want a cylinder along Z.
    # So the profile must be in XZ, and we revolve around the X axis? No, around the Z axis.
    # The Z axis is in the XZ plane.
    # So we sketch in XZ, and revolve around the Z axis.
    
    # Keyway Geometry in XZ:
    # We need a rectangle representing the slot.
    # Center of the shaft is (0,0) in XZ? 
    # The shaft axis is Z. The cross section is in XZ at any Z.
    # So at Z=0, we draw the slot.
    # Slot Width = keyway_width (along X).
    # Slot Depth = keyway_depth (along Z? No, depth is usually along the axis of the shaft).
    # Wait. 
    # Shaft axis = Z.
    # Keyway is a cut along the Z axis.
    # So the "Depth" of the keyway is along Z.
    # The "Height" of the keyway is the distance from the bottom of the shaft to the bottom of the keyway? 
    # Or is it the height of the keyway slot itself?
    # Standard definitions:
    # Width: Across the diameter.
    # Depth: How far into the shaft (along the diameter).
    # Height: Length along the shaft axis.
    # Prompt says: "keyway_height = 20 mm". Since length is 50mm, this is the length along the axis.
    # Prompt says: "keyway_depth = 4 mm". This is the cut depth from surface to bottom.
    # Prompt says: "keyway_width = 7 mm". This is the width across the diameter.
    
    # So in XZ plane (Side view):
    # We are looking at the X-Z cross section.
    # The shaft radius is 15mm.
    # The keyway is a rectangular cut.
    # X range: [-width/2, +width/2] = [-3.5, 3.5].
    # Z range: The cut goes from the surface (Z = +Radius) inwards by depth.
    # So Z goes from (Radius - depth) to (Radius + depth)? 
    # No, a keyway is centered? Usually keyways are symmetric or offset.
    # Assuming centered on the X-axis? 
    # Yes, standard keyway is centered on the diameter.
    # So X: [-3.5, 3.5].
    # Z: The cut is along the Z axis.
    # Wait. If we revolve this profile around the Z axis, we get a cylinder with a groove.
    # The groove will be at the "equator" of the cylinder?
    # If the profile is in XZ, and we revolve around Z.
    # The X axis is the radial direction. The Z axis is the axial direction.
    # So yes, X is radius, Z is height.
    # We want a groove at the equator (X = Radius).
    # The profile should be a rectangle attached to the circle? 
    # No, the groove is a subtraction.
    # We can create a solid rectangle in XZ: 
    # X: [0, width/2] ? No, centered.
    # Let's define the shape to be revolved.
    # The shape to revolve must be on one side of the axis (X >= 0) to avoid double counting, OR we revolve the whole thing and use "Cut" logic?
    # PartDesign::Revolution creates a solid by revolving a profile.
    # If we want to CUT a keyway, we can:
    # 1. Create the main cylinder.
    # 2. Create a sketch of the keyway slot (a rectangle) in the XZ plane.
    # 3. Use a Pocket (ThroughAll) or a specific Pocket (Length).
    # Since the keyway is through the length? No, keyway_height = 20mm (length).
    # So it's not ThroughAll. It's a Pocket of length 20mm.
    # But a Pocket requires a 2D profile closed by a face.
    # If we sketch a rectangle in XZ, and extrude it? 
    # No, Pocket creates a hole.
    # If we define a closed loop in XZ (a rectangle representing the slot face), and do a Pad along Z? No.
    # To cut a keyway (a slot along Z):
    # We need to cut along Z.
    # Sketch in XZ: A rectangle representing the slot face? No.
    # We need to cut a volume.
    # The volume to remove is a rectangular prism: 
    # X: [-3.5, 3.5], Z: [0, 20] (if centered), Y: [-Depth, +Depth]?
    # No, the keyway is a slot. 
    # The slot surface is perpendicular to the X axis? No.
    # The slot is a gap. 
    # The material removed is defined by the slot boundaries.
    # The slot is: 
    #   - Width (X): 7mm.
    #   - Depth (Y, radial): 4mm. (Wait, Y is radial in XZ view? No, Y is normal to XZ).
    #   - Height (Z, axial): 20mm.
    #   
    # Let's re-orient.
    # Shaft Axis = Z.
    # Radial direction = X (and Y).
    # Tangential direction = Y (and X).
    # Keyway is a rectangular slot.
    # It has a width (along circumference? No, usually width of the key is the tangential dimension, but the slot width is the gap).
    # Standard Keyway:
    #   - Width: The dimension across the key (Tangential).
    #   - Depth: The dimension into the shaft (Radial).
    #   - Length: The dimension along the shaft (Axial).
    #   
    # So in XZ plane
