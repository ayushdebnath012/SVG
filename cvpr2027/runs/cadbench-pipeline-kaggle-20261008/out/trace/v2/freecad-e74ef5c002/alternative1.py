import FreeCAD as App
import Part
from pathlib import Path
import os

def create_smooth_shaft(keyway_width, keyway_depth, keyway_height, num_keyways, shaft_diameter, shaft_length):
    """
    Creates a parametric smooth shaft with keyways.
    """
    doc = App.newDocument("SmoothShaft")

    # 1. Define Parameters
    params = doc.addObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Overall diameter")
    params.shaft_diameter = shaft_diameter
    params.addProperty("App::PropertyLength", "shaft_length", "Dimensions", "Overall length")
    params.shaft_length = shaft_length
    params.addProperty("App::PropertyLength", "keyway_width", "Dimensions", "Keyway width")
    params.keyway_width = keyway_width
    params.addProperty("App::PropertyLength", "keyway_depth", "Dimensions", "Keyway depth")
    params.keyway_depth = keyway_depth
    params.addProperty("App::PropertyLength", "keyway_height", "Dimensions", "Keyway height")
    params.keyway_height = keyway_height
    params.addProperty("App::PropertyInteger", "num_keyways", "Dimensions", "Number of keyways")
    params.num_keyways = num_keyways

    # 2. Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement()

    # 3. Main Shaft Profile Sketch (Front View)
    # We will define the profile on the XY plane. The Z axis will be the extrusion axis.
    main_sketch = body.newObject("Sketcher::SketchObject", "MainProfile")
    main_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    main_sketch.Support = [(doc.getObject("XY_Plane"), ["Plane0"])]
    main_sketch.ConstrainAuto = True
    main_sketch.ConstrainFixAngle = True
    main_sketch.ConstrainFixConstraint = True

    # Add Rectangle (0,0) to (Length, Diameter)
    # FreeCAD Sketcher LineSegment needs start and end points in sketcher local coordinates (usually XY plane)
    main_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(shaft_length, 0, 0)), False)
    main_sketch.addGeometry(Part.LineSegment(App.Vector(shaft_length, 0, 0), App.Vector(shaft_length, shaft_diameter, 0)), False)
    main_sketch.addGeometry(Part.LineSegment(App.Vector(shaft_length, shaft_diameter, 0), App.Vector(0, shaft_diameter, 0)), False)
    main_sketch.addGeometry(Part.LineSegment(App.Vector(0, shaft_diameter, 0), App.Vector(0, 0, 0)), False)

    # Constraints:
    # 1. Coincident origin
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 0))
    # 2. Horizontal lines
    main_sketch.addConstraint(Sketcher.Constraint("LineToValue", 0, 1, 0, 0, shaft_length))
    main_sketch.addConstraint(Sketcher.Constraint("LineToValue", 2, 0, 0, 1, 0))
    main_sketch.addConstraint(Sketcher.Constraint("LineToValue", 2, 1, 0, 1, shaft_diameter))
    # 3. Vertical lines
    main_sketch.addConstraint(Sketcher.Constraint("LineToValue", 1, 0, 0, 0, 0))
    main_sketch.addConstraint(Sketcher.Constraint("LineToValue", 1, 0, 1, 1, shaft_diameter))
    # 4. Horizontal top
    main_sketch.addConstraint(Sketcher.Constraint("LineToValue", 0, 1, 1, 0, shaft_diameter))
    # 5. Length constraint
    main_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, 0, 1, shaft_length))
    # 6. Diameter constraint
    main_sketch.addConstraint(Sketcher.Constraint("Length", 1, 0, 0, 1, shaft_diameter))
    # 7. Right angle at corner
    main_sketch.addConstraint(Sketcher.Constraint("Angle", 1, 0, 1, 1, 0, 1, 1, 0))
    # 8. Right angle at bottom left
    main_sketch.addConstraint(Sketcher.Constraint("Angle", 0, 0, 0, 1, 0, 1, 0, 0))
    # 9. Parallel sides
    main_sketch.addConstraint(Sketcher.Constraint("Parallel", 0, 0, 2, 0, 2, 1, 0, 1, 1))
    main_sketch.addConstraint(Sketcher.Constraint("Parallel", 0, 1, 1, 1, 1, 0, 1, 0, 0))

    # Pad the main shaft
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = main_sketch
    pad.Length = shaft_length
    pad.MidPlane = False
    # Drive length from parameter
    pad.setExpression("Length", "Parameters.shaft_length")

    # 4. Keyway Sketches
    # We need to create sketches for the keyways. Since we need to revolve them (or subtract them),
    # and the shaft is cylindrical, the keyways are rectangular grooves cut into the cylinder.
    # A common way to model this in PartDesign without complex 3D sketches is:
    # 1. Create a sketch on a plane parallel to the shaft axis (e.g., XZ plane at the end or middle).
    # 2. Draw the profile of one keyway.
    # 3. Use a Polar Pattern to replicate the keyway profile.
    # 4. Use a Revolution feature (Groove) to cut it all around.
    
    # However, the prompt asks for "Smooth shaft... with two keyway features".
    # Standard approach for keyways on a shaft:
    # They are usually rectangular cuts perpendicular to the surface, extending radially inwards.
    # To make them "smooth" (no sharp edges where the groove meets the cylinder wall), we should fillet the corners.
    # But the prompt defines specific Width, Depth, Height.
    # Let's model the keyway as a rectangular slot cut through the shaft.
    
    # Strategy:
    # 1. Create a sketch on the XZ plane (side view).
    # 2. Draw a rectangle representing one keyway face.
    # 3. Pattern this face around the Z axis (circular pattern of faces).
    # 4. Create a Groove feature using this patterned face? 
    #    Actually, PartDesign::Groove creates a rotational cut. If we define the profile of the cut in the XZ plane,
    #    and revolve it 360 degrees, it creates a cylindrical hole. That's not a keyway.
    #    A keyway is a linear cut around the circumference.
    
    # Correct Strategy for Keyways in PartDesign:
    # 1. Create a sketch on the XZ plane (side view).
    # 2. Draw the profile of ONE keyway (a rectangle).
    # 3. Use PartDesign::Pocket to cut this specific rectangle? No, that cuts a hole through the face.
    # 4. Use PartDesign::Groove? A groove rotates the profile. If we rotate a rectangle 360, we get a cylinder hole.
    #    
    #    Alternative: 
    #    Create a sketch on the XZ plane. Draw the profile of the keyway (rect).
    #    Use PartDesign::Pocket. Set the Reference to the face of the shaft.
    #    BUT, a pocket is usually a direct subtraction of the sketch area.
    #    If we sketch the keyway on the XZ plane, and the sketch is on the face of the cylinder...
    #    Wait, the keyway wraps around.
    #    
    #    Let's try a different feature order:
    #    1. Create the Shaft (done).
    #    2. Create a sketch on the XZ plane (perpendicular to Z axis).
    #    3. Draw a rectangle that represents the cross-section of the keyway at one location.
    #       The rectangle should be positioned such that it represents the "cutout".
    #    4. Actually, the easiest way to get a keyway (a slot around the cylinder) is:
    #       - Create a sketch on the XZ plane.
    #       - Draw a rectangle that is offset from the center.
    #       - This doesn't work directly with standard revolve/pocket unless we pattern the sketch itself.
    
    #    Let's go with the "Patterned Sketch" approach.
    #    1. Create a sketch on the XZ plane (Y=0).
    #    2. Draw a rectangle representing the keyway profile.
    #       The keyway is a slot of Width X Height.
    #       It goes from Depth to Surface.
    #       Since it's a keyway, it is open on the outer side? No, usually it's a slot.
    #       Let's assume the standard keyway: A rectangular groove cut into the side.
    #       It has a width (circumferential) and height (radial).
    #       Wait, the parameters are: width (circumferential?), depth (radial?), height (length?).
    #       Prompt: "keyway_width = 5 mm", "keyway_depth = 5 mm", "keyway_height = 20 mm".
    #       Standard Keyway:
    #       Width: Circumferential dimension.
    #       Depth: Radial dimension (into the shaft).
    #       Height: Length along the shaft.
    #       
    #    So, if we have 2 keyways, they are separated by 180 degrees.
    #    We can model one keyway, then use a Polar Pattern with 2 occurrences (angle 180).
    #    
    #    How to model ONE keyway that wraps around?
    #    We cannot model a full 360 cut in one go with a simple sketch unless we use a shell or specific groove logic.
    #    BUT, a keyway is typically a straight slot.
    #    If we define the keyway as a rectangular cut on the side, it doesn't wrap 360.
    #    UNLESS the "Keyway" here implies a keyseat (a slot).
    #    If we have 2 keyways, they are likely opposite each other.
    #    
    #    Let's assume the standard interpretation:
    #    A "Keyway" in a shaft is a slot for a key.
    #    If we have 2 keyways, they are two separate slots.
    #    Each slot is rectangular.
    #    Dimensions:
    #    - Width (circumferential length of the slot).
    #    - Depth (radial depth into the shaft).
    #    - Height (axial length of the slot).
    #    
    #    Wait, usually "Keyway Width" is the width of the key/keyseat.
    #    If the shaft is 50mm, and keyway width is 5mm.
    #    Does "width" mean the circumferential length of the cut? Yes.
    #    Does "height" mean the axial length? Yes.
    #    Does "depth" mean the radial depth? Yes.
    #    
    #    So, we need to create a slot on the surface.
    #    In FreeCAD PartDesign, creating a slot on a curved surface is tricky with simple sketches.
    #    However, we can create a sketch on the XZ plane (side view).
    #    Draw a rectangle.
    #    Extrude it (Pad) to create a block that intersects the shaft.
    #    Then use "Common" -> "Difference" (Boolean) to cut it.
    #    OR use a Pocket feature if the sketch is on the face.
    #    But the face is curved.
    #    
    #    Alternative: Use a "Groove" feature? No, that's rotational.
    #    Alternative: Use a "Pocket" feature with a sketch that is projected onto the face?
    #    Sketcher supports "Placement" on a face, but the geometry must be planar.
    #    We can't easily sketch on a curved face and get a slot that follows the curve unless we use a "Projected" constraint or a specific tool.
    #    
    #    Let's try the Boolean approach (most robust for complex shapes):
    #    1. Create the Shaft.
    #    2. Create a sketch on the XZ plane (Y=0).
    #    3. Draw a rectangle representing the "removal" volume.
    #       The rectangle should be positioned at the correct radius, length, and circumferential span.
    #       But the circumferential span is curved. A rectangle in XZ is straight.
    #       This creates a flat-sided cut, not a curved one.
    #       
    #    Is the "Keyway" actually a cylindrical hole? No, "keyway" implies a slot.
    #    Maybe the prompt implies a "Keyseat" which is a straight slot.
    #    If we cut a straight slot (flat sides) into a cylinder, it looks like a keyway but the corners are sharp and the width is linear, not arc length.
    #    Given the constraints of "PartDesign features" and "editable tree", and the specific parameters:
    #    Let's assume the keyways are straight slots cut into the side of the cylinder.
    #    The "Width" is the linear dimension along the X axis (if we align the slot with X).
    #    The "Height" is the dimension along Z.
    #    The "Depth" is the dimension along Y (radial).
    #    
    #    So, for ONE keyway:
    #    - Located at Y = shaft_diameter/2 - keyway_depth.
    #    - Extends from Y - keyway_depth to Y (the surface).
    #    - Extends in Z from 0 to keyway_height.
    #    - Extends in X from 0 to keyway_width.
    #    
    #    Then we need to position this keyway.
    #    Since we need 2 keyways, we can create the first one, then pattern it.
    #    But standard PartDesign Polar Pattern works on features (Pads/Pockets) or Sketches.
    #    If we create a Pocket feature for the first keyway, we can pattern the Pocket.
    #    
    #    How to create the first keyway?
    #    1. Create a sketch on the XZ plane (Y=0).
    #    2. Draw a rectangle.
    #       Bottom Y = (shaft_diameter/2 - keyway_depth).
    #       Top Y = shaft_diameter/2.
    #       Left X = 0.
    #       Right X = keyway_width.
    #       Bottom Z = 0.
    #       Top Z = keyway_height.
    #    3. This sketch is on the "midplane" of the keyway height, but offset radially.
    #    4. Create a Pocket? 
    #       If we attach the sketch to the XY plane, and pocket through all, we get a hole.
    #       We want to pocket only the volume defined by the sketch, subtracted from the shaft.
    #       This requires the sketch to be on the face of the object or using a boolean difference.
    #       
    #    Better approach for PartDesign:
    #    1. Create the Shaft (Pad).
    #    2. Create a sketch on the XZ plane.
    #    3. Draw the rectangle (the keyway profile).
    #    4. Create a "Pocket" feature.
    #       - Profile: The sketch.
    #       - Reference: The face of the shaft (e.g., the top face at Z=40, or the side face?).
    #       - If we reference the side face (cylinder surface), the pocket will subtract the sketch area from that face.
    #       - This creates a slot!
    #       - We must ensure the sketch is coplanar with the face? No, the sketch is on XZ, the face is curved.
    #       - We need to project the sketch onto the face.
    #       - Sketcher supports "Project" constraints? No.
    #       - We can use the "AttachmentSupport" as the face? 
    #         If we set the sketch support to the Face, it creates a sketch on the face.
    #         But the face is curved. Sketcher requires a flat plane.
    #         It will try to flatten the face.
    #         If we flatten the cylindrical face at the location of the keyway, we get a flat plane.
    #         Then we sketch the keyway rectangle.
    #         Then we Pocket "Through All" (or specific length).
    #         This creates a slot.
    
    #    Let's refine this plan:
    #    1. Shaft Body exists.
    #    2. Keyway Sketch 1:
    #       - Support: The face of the shaft (e.g., the face at Z=40? No, we want the slot to be at a specific location).
    #       - Actually, we can just create the sketch on the XZ plane (Y=0) and use a "Pocket" with a specific Length and Reference.
    #       - Wait, if we pocket from the X
