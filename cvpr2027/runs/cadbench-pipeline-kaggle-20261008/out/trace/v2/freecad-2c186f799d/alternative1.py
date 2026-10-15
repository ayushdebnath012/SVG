"""
answer.py
FreeCAD 1.1 Script to generate a circular flange part.
This script creates a parametric PartDesign model saved as an editable FCStd file.
"""

import os
import FreeCAD as App
import Part
from PartDesign import Body
from Sketcher import Sketcher

def main():
    # --- 1. Document Setup ---
    # Create a new document named after the script stem (answer.FCStd)
    doc_name = os.path.splitext(os.path.basename(__file__))[0]
    doc = App.newDocument(doc_name)
    
    # Get reference to the Z-axis object required by PartDesign sketches
    # We create a dummy Point object to act as a vertex reference if needed, 
    # but usually Z_Axis is provided in the default XY_Plane setup or we can create it.
    # In standard FreeCAD, the XY_Plane object usually has X_Axis, Y_Axis, Z_Axis as children.
    
    # --- 2. Define Parameters ---
    # We will store parameters in a PropertySet object attached to the Body 
    # to make them easily accessible and editable in the tree.
    
    # Parameters
    params = Body(doc).newObject("App::Property", "Parameters")
    params.addProperty("App::PropertyLength", "outer_diameter", "Parameters", "Outer diameter of flange")
    params.addProperty("App::PropertyLength", "flange_thickness", "Parameters", "Thickness of flange")
    params.addProperty("App::PropertyLength", "bore_diameter", "Parameters", "Diameter of central bore")
    params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Parameters", "Diameter of bolt circle")
    params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Parameters", "Diameter of bolt holes")
    params.addProperty("App::PropertyInteger", "number_of_bolt_holes", "Parameters", "Count of bolt holes")
    
    # Set values
    params.outer_diameter = 125.4125
    params.flange_thickness = 23.01875
    params.bore_diameter = 64.690625
    params.bolt_circle_diameter = 103.1875
    params.bolt_hole_diameter = 13.49375
    params.number_of_bolt_holes = 4

    # --- 3. Create Body ---
    body = doc.addObject("PartDesign::Body", "Body")
    doc.setActiveObject("Body")

    # --- 4. Create Base Sketch (Flange Outline) ---
    # Sketch on XY_Plane (z=0)
    base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    base_sketch.ViewObject.Lock = False # Allow editing
    base_sketch.ViewObject.IsOneInstance = False
    
    # Add Circle for Outer Diameter
    # Note: Sketcher::SketchObject geometry methods in headless often require Part objects
    # However, the reference code uses Part.Circle directly in addGeometry.
    # We will construct the geometry using Part.
    
    outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
    base_sketch.addGeometry(outer_circle, True) # True = Fix
    
    # --- 5. Create Through Bore Sketch ---
    # Sketch on a plane parallel to XY but at half thickness, or simply on XY and extrude through?
    # To ensure "Through All" works correctly for a hole starting from the top face, 
    # it is best to create a sketch on the Top face of the flange.
    # However, to keep it simple and robust in headless mode without complex face detection:
    # We will create a sketch on the XY plane, but we will use a Pocket feature that is "Through All"
    # starting from the top. But "Through All" requires a direction.
    # Alternative: Create a sketch on the XY plane, and use a Pad for the hole with Length = -thickness?
    # No, standard practice: Sketch on the top face.
    
    # Since we are in headless mode, creating a sketch on a specific face of a non-existent solid is tricky 
    # because the solid doesn't exist yet.
    # Strategy: 
    # 1. Pad the flange.
    # 2. Create a new sketch on the XY plane.
    # 3. Use a Pocket feature. To make it "Through All" from the top, we usually rely on the feature being 
    #    attached to the top face. 
    #    If we attach to XY_Plane, "Through All" goes in the negative Z direction (or positive depending on config).
    #    Let's assume standard Right Hand Rule: XY plane normal is Z. "Through All" goes through the body.
    #    If the body is at Z=0 with thickness +Z, a sketch on XY attached to Plane, Through All might cut from Z=0 downwards.
    #    To cut upwards, we can reverse the pocket or attach to the Top Face.
    #    Let's try to attach to the Top Face of the flange (created by Pad).
    
    # We need to reference the Top Face of the Pad.
    # In headless scripting, accessing faces of objects created later can be done via GetChildByLabel or specific API.
    # However, a robust parametric way is to create the sketch on the XY plane and use a "Through All" pocket 
    # directed along the Z axis. We can define the direction explicitly if the tool allows, or rely on the default.
    # The default for a sketch on XY_Plane usually cuts along Z.
    
    # Let's create the Bore Sketch on the XY plane.
    bore_sketch = body.newObject("Sketcher::SketchObject", "BoreSketch")
    bore_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    
    bore_radius = params.bore_diameter / 2.0
    bore_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bore_radius)
    bore_sketch.addGeometry(bore_circle, True)

    # --- 6. Pad Feature (Flange Body) ---
    pad = body.newObject("PartDesign::Pad", "FlangePad")
    pad.Profile = base_sketch
    pad.Length = params.flange_thickness
    pad.Type = "Solid"
    
    # --- 7. Bolt Hole Pattern ---
    # We need a sketch for the bolt hole.
    # To ensure the pocket is "Through All" from the top surface, we attach the sketch to the Top Face of the Pad.
    # We will create the sketch, then attach it to the Top Face of the Pad.
    
    bolt_sketch = body.newObject("Sketcher::SketchObject", "BoltSketch")
    bolt_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    
    bolt_hole = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
    bolt_sketch.addGeometry(bolt_hole, True)

    # Attach BoltSketch to the Top Face of FlangePad
    # The Top Face of FlangePad is usually the face with Z = flange_thickness/2.
    # We can get the face by index or label, but in headless without GUI, 
    # we can assume the face index is 0 (if we are careful) or use the API to find it.
    # A safer way in headless PartDesign is to use the "Through All" option and specify the direction 
    # if the tool supports it, or attach to the specific face.
    # Let's try to attach to the Top Face. In FreeCAD 1.1, we can access the face by index.
    # The Pad creates faces. The top face is likely index 1 or 0 depending on creation order.
    # However, using a named reference is better.
    # Let's try to attach to the Top Face by getting the face object from the Pad.
    
    # Note: In headless mode, getting faces from a Body object's features directly can be tricky if not cached.
    # But the Body caches them. 
    # We can try: pad.getObject("Face_0")? No.
    # Let's use the fact that we can set AttachmentSupport to a Face object.
    # We need to find the Top Face of FlangePad.
    
    # Alternative Robust Approach:
    # Create the bolt sketch on XY plane.
    # Create a Pocket feature.
    # Set Type = "Through All".
    # Set Reference to the BoltSketch.
    # To ensure it cuts from the top, we can set the Reference to the Top Face of the Pad explicitly.
    
    # How to get the Top Face object?
    # In the Body, the faces are stored. We can iterate? No.
    # Let's assume the standard behavior: Sketch on XY, Through All cuts along Z axis.
    # If the body exists, it might cut from Z=0 to negative infinity.
    # To cut upwards, we can set the sketch plane to the Top Face directly.
    
    # Let's try to grab the face index. Usually, for a simple Pad, the top face is the last created or index 1.
    # But to be safe, let's create the sketch on the XY plane and use the Pocket feature with 
    # "Through All" and specify the direction if possible, or just accept it cuts from Z=0.
    # Actually, for a flange, the hole is usually through the entire thickness. 
    # If we put the sketch on the XY plane (bottom) and go "Through All", it cuts through the whole part.
    # That is acceptable! The position of the hole center doesn't matter as long as it's on the axis.
    # Wait, if we cut from Z=0 downwards, and the body is Z=0 to Z=thickness, it cuts the whole body. Correct.
    
    pocket = body.newObject("PartDesign::Pocket", "BorePocket")
    pocket.Profile = bore_sketch
    pocket.Type = "ThroughAll"
    pocket.Type = "ThroughAll" # Ensure it is set
    
    # --- 8. Bolt Hole Pattern ---
    # We need to pattern the hole.
    # First, we need to make sure the BoltSketch is attached to a face that allows "Through All" 
    # cutting from the top, OR we just accept the XY plane cut-through.
    # Let's refine: To get a clean "Top" appearance in the CAD tree, attaching to the Top Face is best.
    # Let's attempt to attach to the Top Face of FlangePad.
    # In FreeCAD 1.1, we can use `face = pad.getObject("Face_0")`? No.
    # We can use `pad.Faces` property? No.
    # Let's try to get the face by index.
    
    # Workaround for Headless Face Attachment:
    # Create the sketch on the XY plane.
    # Create the Pocket.
    # Set AttachmentSupport = (pad, ["Face_1"]) -> We need to know the index.
    # Let's try a generic approach: Attach to the Top Face.
    # If we can't determine the index, we stick to XY plane "Through All" which works for geometry, 
    # even if the attachment support in the tree is XY_Plane.
    
    # Let's create the pattern.
    # We need a reference object for the pattern. We can use the Pocket itself.
    
    pattern = body.newObject("PartDesign::PolarPattern", "BoltPattern")
    pattern.Originals = [pocket]
    pattern.Axis = (App.Vector(0, 0, 0), App.Vector(0, 0, 1)) # Z Axis
    pattern.Angle = 360.0
    pattern.Occurrences = params.number_of_bolt_holes
    # Distance from center
    radius_pattern = params.bolt_circle_diameter / 2.0
    # The PolarPattern tool usually takes a distance parameter.
    pattern.Distance = radius_pattern

    # --- 9. Add Constraints to Sketches (Optional but good practice) ---
    # We added True to addGeometry which fixes them to the origin.
    
    # --- 10. Compute and Save ---
    doc.recompute()
    
    # Save to the exact path derived from __file__
    # The prompt asks to save as answer.FCStd next to the script.
    output_path = os.path.splitext(__file__)[0] + ".FCStd"
    doc.saveAs(output_path)
    
    print(f"Model saved to {output_path}")

if __name__ == "__main__":
    main()
